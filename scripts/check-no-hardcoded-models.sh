#!/bin/bash
# Check for hardcoded model names in agent and template files
#
# Model assignments MUST come from bazinga/model_selection.json
# Hardcoding model names (haiku, sonnet, opus) in agent files creates
# inconsistency when configuration changes.
#
# ALLOWED exceptions:
# - YAML frontmatter (model: sonnet) - documentation only, not read at runtime
# - Variable references (MODEL_CONFIG["developer"])
# - Template placeholders ({haiku|sonnet|opus})
# - Token budget tables (| haiku | 900 |)
# - Status markers (ESCALATE_TO_OPUS)
# - Documentation showing what NOT to do (NEVER, ❌, example, etc.)

set +e

echo "🔍 Checking for hardcoded model names in agent files..."
echo ""

ERRORS_FOUND=0

# Files to check
# Note: We check agents/, templates/, and .claude/commands/
# Exclude research/ (analysis docs) and bazinga/model_selection.json (config source)
FILES_TO_CHECK=$(find agents templates .claude/commands -name '*.md' 2>/dev/null | grep -v 'research/' || true)

# Also add any .claude/agents if they exist
if [ -d ".claude/agents" ]; then
    FILES_TO_CHECK="$FILES_TO_CHECK $(find .claude/agents -name '*.md' 2>/dev/null || true)"
fi

echo "━━━ Check: Hardcoded tier/model notation ━━━"
echo ""
echo "Forbidden patterns:"
echo "  ❌ [SSE/Sonnet], [Dev/Haiku] - use [SSE/{model}] or [Dev/{model}] instead"
echo "  ❌ (Sonnet), (Haiku), (Opus) in operational context"
echo "  ❌ 'spawn with opus', 'use sonnet for' - imperative model instructions"
echo ""
echo "Allowed patterns:"
echo "  ✅ YAML frontmatter 'model: sonnet' (documentation only)"
echo "  ✅ MODEL_CONFIG[\"developer\"] (variable reference)"
echo "  ✅ {haiku|sonnet|opus} (template placeholder)"
echo "  ✅ | haiku | 900 | (token budget table)"
echo "  ✅ ESCALATE_TO_OPUS (status marker)"
echo ""

VIOLATION_COUNT=0

for file in $FILES_TO_CHECK; do
    [ -f "$file" ] || continue

    file_violations=""

    # Read file content, skipping YAML frontmatter (first --- to second ---)
    # We use awk to skip the frontmatter section
    content_without_frontmatter=$(awk '
        BEGIN { in_frontmatter = 0; found_first = 0 }
        /^---$/ {
            if (!found_first) { found_first = 1; in_frontmatter = 1; next }
            else if (in_frontmatter) { in_frontmatter = 0; next }
        }
        !in_frontmatter { print }
    ' "$file")

    # Pattern 1: Hardcoded tier/model notation like [SSE/Sonnet], [Dev/Haiku]
    # This catches brackets with model names that should use {model} placeholder
    pattern1_matches=$(echo "$content_without_frontmatter" | grep -n '\[.*\/\(Haiku\|Sonnet\|Opus\)\]' 2>/dev/null || true)

    # Pattern 2: Model name in parentheses in operational context
    # e.g., "Senior Software Engineer (Sonnet)" but not "(haiku=900)"
    pattern2_matches=$(echo "$content_without_frontmatter" | grep -n '([A-Za-z ]*\(Haiku\|Sonnet\|Opus\))' 2>/dev/null | grep -v '(haiku=' | grep -v '(sonnet=' | grep -v '(opus=' || true)

    # Pattern 3: Imperative instructions with model names
    # e.g., "spawn with opus", "use sonnet for", "assign haiku to"
    pattern3_matches=$(echo "$content_without_frontmatter" | grep -niE '(spawn|use|assign|run|execute) (with |using |on )?(haiku|sonnet|opus)' 2>/dev/null || true)

    # Pattern 4: Direct hardcoded model string assignments (not MODEL_CONFIG references)
    # e.g., = "haiku" or = 'sonnet' but not MODEL_CONFIG["x"] = "haiku"
    pattern4_matches=$(echo "$content_without_frontmatter" | grep -nE '[^A-Z_]= ?"(haiku|sonnet|opus)"' 2>/dev/null || true)
    pattern4_matches="$pattern4_matches$(echo "$content_without_frontmatter" | grep -nE "[^A-Z_]= ?'(haiku|sonnet|opus)'" 2>/dev/null || true)"

    # Combine all matches
    all_matches="$pattern1_matches
$pattern2_matches
$pattern3_matches
$pattern4_matches"

    # Filter out documentation/educational context and allowed patterns
    while IFS= read -r match; do
        [ -z "$match" ] && continue

        # Skip lines with documentation markers
        if echo "$match" | grep -qiE "(NEVER|DON'T|DO NOT|❌|🚫|example|prohibited|forbidden|wrong|bad|Fix:|CRITICAL|Should be|must not|Avoid|Warning)"; then
            continue
        fi

        # Skip variable references like MODEL_CONFIG["developer"]
        if echo "$match" | grep -qE 'MODEL_CONFIG\['; then
            continue
        fi

        # Skip template placeholders like {haiku|sonnet|opus}
        if echo "$match" | grep -qE '\{haiku\|sonnet\|opus\}|\{model\}'; then
            continue
        fi

        # Skip token budget table rows
        if echo "$match" | grep -qE '^\|.*haiku.*\|.*[0-9]+.*\|'; then
            continue
        fi
        if echo "$match" | grep -qE '^\|.*sonnet.*\|.*[0-9]+.*\|'; then
            continue
        fi
        if echo "$match" | grep -qE '^\|.*opus.*\|.*[0-9]+.*\|'; then
            continue
        fi

        # Skip status markers (all caps with underscore)
        if echo "$match" | grep -qE 'ESCALATE_TO_OPUS|SPAWN_OPUS'; then
            continue
        fi

        # Skip if this is inside a code block comment or description
        if echo "$match" | grep -qE '^[0-9]+:.*#.*Model:'; then
            continue
        fi

        # This is a real violation
        file_violations="$file_violations$match
"
    done <<< "$all_matches"

    # Report violations for this file
    if [ -n "$(echo "$file_violations" | tr -d '[:space:]')" ]; then
        echo "❌ $file"
        echo "   Hardcoded model names found:"
        echo "$file_violations" | while IFS= read -r line; do
            [ -n "$line" ] && echo "   → Line $line"
        done
        echo ""
        VIOLATION_COUNT=$((VIOLATION_COUNT + 1))
    fi
done

ERRORS_FOUND=$VIOLATION_COUNT

# Summary
echo "═══════════════════════════════════════════════════════════"

if [ $ERRORS_FOUND -gt 0 ]; then
    echo "❌ FAILED: Found $ERRORS_FOUND file(s) with hardcoded model names"
    echo ""
    echo "How to fix:"
    echo "  1. Replace [SSE/Sonnet] with [SSE/{model}] or remove model specification"
    echo "  2. Replace (Sonnet) with ({model}) or use tier-based language"
    echo "  3. Remove imperative model instructions"
    echo "  4. Use MODEL_CONFIG[\"agent_type\"] for model references"
    echo ""
    echo "Model assignments belong in:"
    echo "  ✅ bazinga/model_selection.json (runtime configuration)"
    echo "  ✅ YAML frontmatter (documentation only)"
    echo ""
    echo "See: bazinga/model_selection.json for configuration"
    echo "═══════════════════════════════════════════════════════════"
    exit 1
else
    echo "✅ PASSED: No hardcoded model name violations found"
    echo ""
    echo "Verified that agent files use:"
    echo "  ✅ MODEL_CONFIG[\"agent\"] for model references"
    echo "  ✅ {model} placeholders in templates"
    echo "  ✅ Tier-based language (Developer tier, SSE tier)"
    echo "═══════════════════════════════════════════════════════════"
    exit 0
fi
