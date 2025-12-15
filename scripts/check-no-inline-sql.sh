#!/bin/bash
# Check for inline SQL in agent files
# All database operations must use Skill(command: "bazinga-db")
#
# ALLOWED exceptions:
# - .claude/skills/bazinga-db/ (the DB skill itself)
# - Documentation/examples explaining what NOT to do (marked with NEVER/❌/🚫)

# Don't use set -e as it interferes with loops and grep
set +e

echo "🔍 Checking for prohibited inline SQL in agent files..."
echo ""

ERRORS_FOUND=0

# Paths ALLOWED to contain SQL (ONLY the DB skill itself)
ALLOWED_PATHS=(
    ".claude/skills/bazinga-db/"
)

# No educational exceptions - agents should NOT know SQL implementation details
# They should only use Skill(command: "bazinga-db")
EDUCATIONAL_FILES=()

# Build find exclusion arguments
EXCLUDE_ARGS=""
for path in "${ALLOWED_PATHS[@]}"; do
    EXCLUDE_ARGS="$EXCLUDE_ARGS ! -path \"$path*\""
done

# Files to check (excluding research folder - contains analysis docs)
# Use ./ prefix for consistent path matching with find
FILES_TO_CHECK=$(eval "find agents .claude/commands .claude/skills bazinga/templates -name '*.md' $EXCLUDE_ARGS ! -path '*/resources/*' ! -path './research/*' 2>/dev/null" || true)

# Check 1: Inline SQL statements (the real danger)
# These are hardcoded SQL strings that bypass the bazinga-db skill entirely
echo "━━━ Check 1: Inline SQL statements ━━━"
echo ""

SQL_STMT_ERRORS=0
for file in $FILES_TO_CHECK; do
    [ -f "$file" ] || continue

    # Skip educational files that contain SQL for teaching purposes
    skip_file=false
    for edu_file in "${EDUCATIONAL_FILES[@]}"; do
        if [[ "$file" == *"$edu_file"* ]]; then
            skip_file=true
            break
        fi
    done
    if [ "$skip_file" = true ]; then
        continue
    fi

    # Look for actual SQL statements in code (not documentation)
    # Pattern: SQL keywords followed by table-like patterns (case-insensitive)
    matches=$(grep -niE "cursor\.execute\(|\.execute\(['\"]?(SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER)" "$file" 2>/dev/null || true)

    if [ -n "$matches" ]; then
        # Filter out documentation/educational context
        # These patterns indicate the SQL is an example, not real code
        real_violations=""
        while IFS= read -r match; do
            # Skip lines that are clearly documentation/examples/educational content
            # These patterns indicate SQL shown for teaching, not for execution
            if echo "$match" | grep -qiE "(NEVER|DON'T|❌|🚫|example|prohibited|forbidden|wrong|bad|Fix:|Change|Review:|sql injection|vulnerability|parameterized|payload|CRITICAL|Should be|Current code|Solution|migration|idempotent|\*\*Location|\*\*Problem|\*\*Why)"; then
                continue
            fi
            real_violations="$real_violations$match
"
        done <<< "$matches"

        if [ -n "$(echo "$real_violations" | tr -d '[:space:]')" ]; then
            echo "❌ $file"
            echo "   Inline SQL statements found:"
            echo "$real_violations" | while IFS= read -r line; do
                [ -n "$line" ] && echo "   → $line"
            done
            echo ""
            SQL_STMT_ERRORS=$((SQL_STMT_ERRORS + 1))
        fi
    fi
done

if [ $SQL_STMT_ERRORS -eq 0 ]; then
    echo "✅ No inline SQL statements found"
else
    ERRORS_FOUND=$((ERRORS_FOUND + SQL_STMT_ERRORS))
fi
echo ""

# Check 2: Direct sqlite3 usage in code blocks
echo "━━━ Check 2: Direct sqlite3 usage ━━━"
echo ""

SQLITE_ERRORS=0
for file in $FILES_TO_CHECK; do
    [ -f "$file" ] || continue

    # Skip educational files
    skip_file=false
    for edu_file in "${EDUCATIONAL_FILES[@]}"; do
        if [[ "$file" == *"$edu_file"* ]]; then
            skip_file=true
            break
        fi
    done
    if [ "$skip_file" = true ]; then
        continue
    fi

    # Look for sqlite3.connect which indicates actual DB connection code
    # Note: -E flag required for alternation with |
    matches=$(grep -nE "sqlite3\.connect|conn = sqlite3|import sqlite3" "$file" 2>/dev/null || true)

    if [ -n "$matches" ]; then
        # Filter out documentation/educational context
        real_violations=""
        while IFS= read -r match; do
            # Skip lines that are clearly documentation/examples
            if echo "$match" | grep -qiE "(NEVER|DON'T|❌|🚫|example|prohibited|forbidden|wrong|#.*comment|Review:|vulnerability|payload)"; then
                continue
            fi
            real_violations="$real_violations$match
"
        done <<< "$matches"

        if [ -n "$real_violations" ]; then
            echo "❌ $file"
            echo "   Direct sqlite3 usage found:"
            echo "$real_violations" | while IFS= read -r line; do
                [ -n "$line" ] && echo "   → $line"
            done
            echo ""
            SQLITE_ERRORS=$((SQLITE_ERRORS + 1))
        fi
    fi
done

if [ $SQLITE_ERRORS -eq 0 ]; then
    echo "✅ No direct sqlite3 usage found"
else
    ERRORS_FOUND=$((ERRORS_FOUND + SQLITE_ERRORS))
fi
echo ""

# Summary
echo "═══════════════════════════════════════════════════════════"

if [ $ERRORS_FOUND -gt 0 ]; then
    echo "❌ FAILED: Found $ERRORS_FOUND inline SQL violation(s)"
    echo ""
    echo "Prohibited patterns found:"
    echo "  ❌ cursor.execute('SELECT...') - inline SQL execution"
    echo "  ❌ sqlite3.connect() - direct DB connection"
    echo "  ❌ import sqlite3 - direct sqlite imports"
    echo ""
    echo "Use the bazinga-db skill instead:"
    echo "  ✅ Skill(command: \"bazinga-db\")"
    echo "  ✅ python3 bazinga_db.py (CLI wrapper is OK)"
    echo ""
    echo "Allowed exceptions:"
    echo "  ✅ .claude/skills/bazinga-db/ (the skill itself)"
    echo "  ✅ Documentation examples marked with NEVER/❌/🚫/example"
    echo ""
    echo "See: .claude/skills/bazinga-db/SKILL.md for correct usage"
    echo "═══════════════════════════════════════════════════════════"
    exit 1
else
    echo "✅ PASSED: No inline SQL violations found"
    echo ""
    echo "Scanned files correctly avoid hardcoded SQL"
    echo ""
    echo "Excluded (allowed SQL):"
    for path in "${ALLOWED_PATHS[@]}"; do
        echo "  ✅ $path (internal implementation)"
    done
    for edu in "${EDUCATIONAL_FILES[@]}"; do
        echo "  ✅ $edu (educational examples)"
    done
    echo "═══════════════════════════════════════════════════════════"
    exit 0
fi
