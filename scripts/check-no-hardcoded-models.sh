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
# - Fenced code blocks (``` or ~~~, including indented)
# - Inline code (`...`)

# Use strict mode but allow grep to return non-zero (no matches)
set -Euo pipefail

echo "🔍 Checking for hardcoded model names in agent and source files..."
echo ""

VIOLATION_COUNT=0

echo "━━━ Check: Hardcoded tier/model notation ━━━"
echo ""
echo "Forbidden patterns:"
echo "  ❌ [SSE/Sonnet], [Dev/Haiku] - use [SSE/{model}] or [Dev/{model}] instead"
echo "  ❌ (Sonnet), (Haiku), (Opus) in operational context"
echo "  ❌ 'spawn with opus', 'use sonnet for' - imperative model instructions"
echo "  ❌ model = \"haiku\" - direct assignments"
echo ""
echo "Allowed patterns:"
echo "  ✅ YAML frontmatter 'model: sonnet' (documentation only)"
echo "  ✅ MODEL_CONFIG[\"agent_name\"] (variable reference)"
echo "  ✅ {haiku|sonnet|opus} (template placeholder)"
echo "  ✅ | haiku | 900 | (token budget table)"
echo "  ✅ ESCALATE_TO_OPUS (status marker)"
echo "  ✅ Fenced code blocks and inline code (examples)"
echo ""

# Build array of directories to search
declare -a SEARCH_DIRS=()
[ -d "agents" ] && SEARCH_DIRS+=("agents")
[ -d "templates" ] && SEARCH_DIRS+=("templates")
[ -d ".claude/commands" ] && SEARCH_DIRS+=(".claude/commands")
[ -d ".claude/agents" ] && SEARCH_DIRS+=(".claude/agents")
[ -d ".claude/skills" ] && SEARCH_DIRS+=(".claude/skills")
[ -d "scripts" ] && SEARCH_DIRS+=("scripts")
[ -d "src" ] && SEARCH_DIRS+=("src")

if [ ${#SEARCH_DIRS[@]} -eq 0 ]; then
    echo "⚠️  No directories to scan found"
    exit 0
fi

# File extensions to scan
FILE_PATTERNS=(-name '*.md' -o -name '*.mdx' -o -name '*.py' -o -name '*.ts' -o -name '*.js' -o -name '*.sh' -o -name '*.yml' -o -name '*.yaml')

# Process files using find -print0 for robust filename handling
while IFS= read -r -d '' file; do
    # Skip research folder, node_modules, and this script itself
    [[ "$file" == *"/research/"* ]] && continue
    [[ "$file" == *"/node_modules/"* ]] && continue
    [[ "$file" == *"/.git/"* ]] && continue
    [[ "$file" == *"check-no-hardcoded-models.sh" ]] && continue
    [ -f "$file" ] || continue

    file_violations=""

    # Process file content with awk:
    # 1. Skip YAML frontmatter (only if file starts with ---)
    # 2. Skip fenced code blocks (``` or ~~~, with up to 3 leading spaces)
    # 3. Skip inline code (`...`)
    # 4. Preserve original line numbers (prefixed as "LINENUM:")
    processed_content=$(awk '
        BEGIN { in_frontmatter = 0; in_fenced = 0; fence_char = "" }
        NR == 1 && /^---[[:space:]]*$/ { in_frontmatter = 1; next }
        in_frontmatter && /^---[[:space:]]*$/ { in_frontmatter = 0; next }
        in_frontmatter { next }
        # Match fenced code blocks: up to 3 spaces, then 3+ backticks or tildes
        /^[[:space:]]{0,3}```/ || /^[[:space:]]{0,3}~~~/ {
            if (!in_fenced) {
                in_fenced = 1
                fence_char = (index($0, "```") > 0) ? "`" : "~"
            } else {
                # Only close if matching fence type
                if ((fence_char == "`" && /```/) || (fence_char == "~" && /~~~/)) {
                    in_fenced = 0
                    fence_char = ""
                }
            }
            next
        }
        in_fenced { next }
        # Remove inline code before printing (replace `...` with empty)
        {
            line = $0
            gsub(/`[^`]+`/, "", line)
            print NR ":" line
        }
    ' "$file")

    # Collect all pattern matches into an array for proper handling
    declare -a all_matches=()

    # Word boundary pattern for model names (avoid matching substrings like "sonnet-3.5")
    # Using [^[:alnum:]_-] as boundary since model names are standalone words

    # Pattern 1: Hardcoded tier/model notation like [SSE/Sonnet], [Dev/Haiku]
    # Case-insensitive to catch [Dev/haiku], [SSE/SONNET], etc.
    while IFS= read -r match; do
        [ -n "$match" ] && all_matches+=("$match")
    done < <(printf '%s\n' "$processed_content" | grep -iE '^[0-9]+:.*\[.*/[[:space:]]*(haiku|sonnet|opus)[[:space:]]*\]' 2>/dev/null || true)

    # Pattern 2: Model name in parentheses in operational context
    # e.g., "Senior Software Engineer (Sonnet)" but not "(haiku=900)"
    while IFS= read -r match; do
        [ -n "$match" ] && all_matches+=("$match")
    done < <(printf '%s\n' "$processed_content" | grep -iE '^[0-9]+:.*\([a-z ]*[[:space:]]*(haiku|sonnet|opus)[[:space:]]*\)' 2>/dev/null | grep -viE '\((haiku|sonnet|opus)=' || true)

    # Pattern 3: Imperative instructions with model names
    # e.g., "spawn with opus", "use sonnet for", "assign haiku to"
    # Word boundary: model name followed by space, punctuation, or end of line
    while IFS= read -r match; do
        [ -n "$match" ] && all_matches+=("$match")
    done < <(printf '%s\n' "$processed_content" | grep -iE '^[0-9]+:.*(spawn|use|assign|run|execute)[[:space:]]+(with[[:space:]]+|using[[:space:]]+|on[[:space:]]+)?(haiku|sonnet|opus)([[:space:]]|[,.]|$)' 2>/dev/null || true)

    # Pattern 4: Direct hardcoded model string assignments
    # e.g., model = "haiku", model="sonnet", x = 'opus'
    # Match: identifier followed by = and quoted model name
    while IFS= read -r match; do
        [ -n "$match" ] && all_matches+=("$match")
    done < <(printf '%s\n' "$processed_content" | grep -iE '^[0-9]+:.*[[:alnum:]_]+[[:space:]]*=[[:space:]]*["'"'"'](haiku|sonnet|opus)["'"'"']' 2>/dev/null || true)

    # Filter out documentation/educational context and allowed patterns
    for match in "${all_matches[@]+"${all_matches[@]}"}"; do
        [ -z "$match" ] && continue

        # Skip lines with documentation markers
        if printf '%s\n' "$match" | grep -qiE "(NEVER|DON'T|DO NOT|❌|🚫|example|prohibited|forbidden|wrong|bad|Fix:|CRITICAL|Should be|must not|Avoid|Warning)"; then
            continue
        fi

        # Skip variable references like MODEL_CONFIG["developer"]
        if printf '%s\n' "$match" | grep -qE 'MODEL_CONFIG\['; then
            continue
        fi

        # Skip template placeholders like {haiku|sonnet|opus}
        if printf '%s\n' "$match" | grep -qiE '\{haiku\|sonnet\|opus\}|\{model\}'; then
            continue
        fi

        # Skip token budget table rows (case-insensitive)
        # Allow optional whitespace after colon and before pipe
        if printf '%s\n' "$match" | grep -qiE '^[0-9]+:[[:space:]]*\|.*(haiku|sonnet|opus).*\|.*[0-9]+.*\|'; then
            continue
        fi

        # Skip status markers (all caps with underscore)
        if printf '%s\n' "$match" | grep -qE 'ESCALATE_TO_OPUS|SPAWN_OPUS'; then
            continue
        fi

        # Skip if this is inside a code block comment or description
        if printf '%s\n' "$match" | grep -qE '^[0-9]+:.*#.*Model:'; then
            continue
        fi

        # Skip test assertions and mock data
        if printf '%s\n' "$match" | grep -qiE '(assert|expect|mock|test_|_test|spec\.)'; then
            continue
        fi

        # Skip Python function parameter defaults: def func(..., model="sonnet"):
        if printf '%s\n' "$match" | grep -qE 'def [[:alnum:]_]+\(.*=[[:space:]]*["'"'"'](haiku|sonnet|opus)["'"'"']'; then
            continue
        fi

        # Skip argparse/CLI defaults: default="sonnet", default='haiku'
        if printf '%s\n' "$match" | grep -qiE 'default[[:space:]]*=[[:space:]]*["'"'"'](haiku|sonnet|opus)["'"'"']'; then
            continue
        fi

        # This is a real violation
        file_violations="$file_violations$match"$'\n'
    done

    # Report violations for this file
    if [ -n "$(printf '%s\n' "$file_violations" | tr -d '[:space:]')" ]; then
        echo "❌ $file"
        echo "   Hardcoded model names found:"
        printf '%s\n' "$file_violations" | while IFS= read -r line; do
            [ -n "$line" ] && echo "   → Line $line"
        done
        echo ""
        VIOLATION_COUNT=$((VIOLATION_COUNT + 1))
    fi

    # Clear the array for next file
    unset all_matches

done < <(find "${SEARCH_DIRS[@]}" \( "${FILE_PATTERNS[@]}" \) -print0 2>/dev/null)

# Summary
echo "═══════════════════════════════════════════════════════════"

if [ "$VIOLATION_COUNT" -gt 0 ]; then
    echo "❌ FAILED: Found $VIOLATION_COUNT file(s) with hardcoded model names"
    echo ""
    echo "How to fix:"
    echo "  1. Replace [SSE/Sonnet] with [SSE/{model}] or remove model specification"
    echo "  2. Replace (Sonnet) with ({model}) or use tier-based language"
    echo "  3. Remove imperative model instructions"
    echo "  4. Use MODEL_CONFIG[\"agent_name\"] for model references"
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
    echo "Verified that agent and source files use:"
    echo "  ✅ MODEL_CONFIG[\"agent_name\"] for model references"
    echo "  ✅ {model} placeholders in templates"
    echo "  ✅ Tier-based language (Developer tier, SSE tier)"
    echo "═══════════════════════════════════════════════════════════"
    exit 0
fi
