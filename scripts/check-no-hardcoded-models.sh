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

# Use strict mode but allow grep to return non-zero (no matches)
set -Euo pipefail

echo "🔍 Checking for hardcoded model names in agent files..."
echo ""

VIOLATION_COUNT=0

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

# Build list of directories to search
SEARCH_DIRS=""
[ -d "agents" ] && SEARCH_DIRS="$SEARCH_DIRS agents"
[ -d "templates" ] && SEARCH_DIRS="$SEARCH_DIRS templates"
[ -d ".claude/commands" ] && SEARCH_DIRS="$SEARCH_DIRS .claude/commands"
[ -d ".claude/agents" ] && SEARCH_DIRS="$SEARCH_DIRS .claude/agents"

if [ -z "$SEARCH_DIRS" ]; then
    echo "⚠️  No directories to scan found"
    exit 0
fi

# Process files using find -print0 for robust filename handling
while IFS= read -r -d '' file; do
    # Skip research folder
    [[ "$file" == *"/research/"* ]] && continue
    [ -f "$file" ] || continue

    file_violations=""

    # Read file content, skipping YAML frontmatter only if file starts with ---
    # Gate on NR==1 to avoid triggering on --- appearing mid-file
    content_without_frontmatter=$(awk '
        NR == 1 && /^---$/ { in_frontmatter = 1; next }
        in_frontmatter && /^---$/ { in_frontmatter = 0; next }
        !in_frontmatter { print }
    ' "$file")

    # Collect all pattern matches into an array for proper handling
    declare -a all_matches=()

    # Pattern 1: Hardcoded tier/model notation like [SSE/Sonnet], [Dev/Haiku]
    # Case-insensitive to catch [Dev/haiku], [SSE/SONNET], etc.
    while IFS= read -r match; do
        [ -n "$match" ] && all_matches+=("$match")
    done < <(echo "$content_without_frontmatter" | grep -niE '\[.*/[[:space:]]*(haiku|sonnet|opus)[[:space:]]*\]' 2>/dev/null || true)

    # Pattern 2: Model name in parentheses in operational context
    # e.g., "Senior Software Engineer (Sonnet)" but not "(haiku=900)"
    # Case-insensitive
    while IFS= read -r match; do
        [ -n "$match" ] && all_matches+=("$match")
    done < <(echo "$content_without_frontmatter" | grep -niE '\([a-z ]*[[:space:]]*(haiku|sonnet|opus)[[:space:]]*\)' 2>/dev/null | grep -viE '\((haiku|sonnet|opus)=' || true)

    # Pattern 3: Imperative instructions with model names
    # e.g., "spawn with opus", "use sonnet for", "assign haiku to"
    while IFS= read -r match; do
        [ -n "$match" ] && all_matches+=("$match")
    done < <(echo "$content_without_frontmatter" | grep -niE '(spawn|use|assign|run|execute)[[:space:]]+(with[[:space:]]+|using[[:space:]]+|on[[:space:]]+)?(haiku|sonnet|opus)' 2>/dev/null || true)

    # Pattern 4: Direct hardcoded model string assignments
    # e.g., = "haiku" or = 'sonnet' but not MODEL_CONFIG["x"] = "haiku"
    # Handles start-of-line and case-insensitive
    while IFS= read -r match; do
        [ -n "$match" ] && all_matches+=("$match")
    done < <(echo "$content_without_frontmatter" | grep -niE '(^|[^A-Z_])[[:space:]]*=[[:space:]]*["'"'"'](haiku|sonnet|opus)["'"'"']' 2>/dev/null || true)

    # Filter out documentation/educational context and allowed patterns
    for match in "${all_matches[@]+"${all_matches[@]}"}"; do
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
        if echo "$match" | grep -qiE '\{haiku\|sonnet\|opus\}|\{model\}'; then
            continue
        fi

        # Skip token budget table rows (case-insensitive)
        if echo "$match" | grep -qiE '^[0-9]+:\|.*(haiku|sonnet|opus).*\|.*[0-9]+.*\|'; then
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
        file_violations="$file_violations$match"$'\n'
    done

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

    # Clear the array for next file
    unset all_matches

done < <(find $SEARCH_DIRS -name '*.md' -print0 2>/dev/null)

# Summary
echo "═══════════════════════════════════════════════════════════"

if [ "$VIOLATION_COUNT" -gt 0 ]; then
    echo "❌ FAILED: Found $VIOLATION_COUNT file(s) with hardcoded model names"
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
