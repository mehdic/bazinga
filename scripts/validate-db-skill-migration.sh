#!/bin/bash
# Validate bazinga-db domain skill migration
# Ensures all references use domain-specific skills and request text is consistent

# Note: Not using set -e because arithmetic operations can return non-zero

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0
WARNINGS=0

echo "🔍 Validating bazinga-db domain skill migration..."
echo ""

# 1. Check for stale "bazinga-db, please" text (should be domain-specific)
echo "📋 Checking for stale request phrasings..."
STALE_PHRASINGS=$(grep -rn 'bazinga-db, please' --include="*.md" "$REPO_ROOT" 2>/dev/null | grep -v research/ | grep -v '.claude/skills/bazinga-db/SKILL.md' || true)
if [ -n "$STALE_PHRASINGS" ]; then
    echo -e "${RED}❌ Found stale 'bazinga-db, please' phrasings:${NC}"
    echo "$STALE_PHRASINGS"
    ((ERRORS++))
else
    echo -e "${GREEN}  ✅ No stale request phrasings found${NC}"
fi

# 2. Check for old-style skill invocations (should use domain-specific skills)
echo ""
echo "📋 Checking for old-style skill invocations..."
OLD_INVOCATIONS=$(grep -rn 'Skill(command: "bazinga-db")' --include="*.md" "$REPO_ROOT" 2>/dev/null | grep -v research/ | grep -v '.claude/skills/bazinga-db/SKILL.md' || true)
if [ -n "$OLD_INVOCATIONS" ]; then
    echo -e "${RED}❌ Found old-style skill invocations:${NC}"
    echo "$OLD_INVOCATIONS"
    ((ERRORS++))
else
    echo -e "${GREEN}  ✅ No old-style skill invocations found${NC}"
fi

# 3. Check domain-specific skills exist
echo ""
echo "📋 Checking domain-specific skills exist..."
DOMAINS=("core" "workflow" "agents" "context")
for domain in "${DOMAINS[@]}"; do
    SKILL_DIR="$REPO_ROOT/.claude/skills/bazinga-db-$domain"
    if [ -d "$SKILL_DIR" ] && [ -f "$SKILL_DIR/SKILL.md" ]; then
        echo -e "${GREEN}  ✅ bazinga-db-$domain skill exists${NC}"
    else
        echo -e "${RED}  ❌ bazinga-db-$domain skill missing${NC}"
        ((ERRORS++))
    fi
done

# 4. Check for mismatched request/invocation pairs
echo ""
echo "📋 Checking for request/invocation consistency..."

# Pattern: request text should match skill being invoked
# e.g., "bazinga-db-core, please..." followed by Skill(command: "bazinga-db-core")
check_consistency() {
    local file="$1"
    local domain="$2"
    local other_domains=("${@:3}")

    # Find lines with domain-specific request text
    local requests=$(grep -n "bazinga-db-$domain, please" "$file" 2>/dev/null || true)
    if [ -n "$requests" ]; then
        # Check that the file also has the matching skill invocation
        if ! grep -q "Skill(command: \"bazinga-db-$domain\")" "$file" 2>/dev/null; then
            echo -e "${YELLOW}  ⚠️  $file has 'bazinga-db-$domain, please' but no matching invocation${NC}"
            ((WARNINGS++))
        fi
    fi
}

# Define operational templates that MUST be validated (not documentation)
OPERATIONAL_TEMPLATES=(
    "templates/orchestrator/phase_simple.md"
    "templates/orchestrator/phase_parallel.md"
    "templates/orchestrator/clarification_flow.md"
    "templates/orchestrator/scope_validation.md"
    "templates/shutdown_protocol.md"
    "templates/investigation_loop.md"
    "templates/logging_pattern.md"
    "templates/pm_planning_steps.md"
    "templates/pm_speckit.md"
    "templates/pm_bazinga_validation.md"
    "templates/completion_report.md"
)

# Check operational templates explicitly
echo ""
echo "📋 Checking operational templates..."
for template in "${OPERATIONAL_TEMPLATES[@]}"; do
    if [ -f "$REPO_ROOT/$template" ]; then
        for domain in "${DOMAINS[@]}"; do
            check_consistency "$REPO_ROOT/$template" "$domain"
        done
    fi
done

# Check all other markdown files (excluding documentation directories and templates)
while IFS= read -r -d '' file; do
    for domain in "${DOMAINS[@]}"; do
        check_consistency "$file" "$domain"
    done
done < <(find "$REPO_ROOT" -name "*.md" \
    -not -path "$REPO_ROOT/research/*" \
    -not -path "$REPO_ROOT/templates/*" \
    -not -path "$REPO_ROOT/docs/*" \
    -not -path "$REPO_ROOT/.claude/skills/*/references/*" \
    -not -name "INTEGRATION_GUIDE.md" \
    -print0)

# 5. Check deprecated skill has deprecation notice
echo ""
echo "📋 Checking deprecated skill has deprecation notice..."
DEPRECATED_SKILL="$REPO_ROOT/.claude/skills/bazinga-db/SKILL.md"
if [ -f "$DEPRECATED_SKILL" ]; then
    if grep -q "DEPRECATED" "$DEPRECATED_SKILL" 2>/dev/null; then
        echo -e "${GREEN}  ✅ Deprecated skill has DEPRECATED notice${NC}"
    else
        echo -e "${YELLOW}  ⚠️  Deprecated skill missing DEPRECATED notice${NC}"
        ((WARNINGS++))
    fi
else
    echo -e "${RED}  ❌ Deprecated skill file not found${NC}"
    ((ERRORS++))
fi

# 6. Check event types are documented
echo ""
echo "📋 Checking event types are documented..."

# Known event types (from bazinga-db-agents SKILL.md)
DOCUMENTED_EVENTS="scope_change|role_violation|tl_issues|tl_issue_responses|tl_verdicts|investigation_iteration|pm_bazinga|validator_verdict"

# Find event types used in agent files and templates
USED_EVENTS=$(grep -roh 'Event Type: [a-z_]*' --include="*.md" "$REPO_ROOT/agents" "$REPO_ROOT/templates" 2>/dev/null | \
    sed 's/Event Type: //' | sort -u || true)

EVENT_WARNINGS=0
for event in $USED_EVENTS; do
    if ! echo "$event" | grep -qE "^($DOCUMENTED_EVENTS)$"; then
        echo -e "${YELLOW}  ⚠️  Undocumented event type: $event${NC}"
        ((EVENT_WARNINGS++))
        ((WARNINGS++))
    fi
done

if [ $EVENT_WARNINGS -eq 0 ]; then
    echo -e "${GREEN}  ✅ All event types are documented${NC}"
fi

# 7. Count domain-specific usages
echo ""
echo "📊 Domain-specific skill usage counts:"
for domain in "${DOMAINS[@]}"; do
    COUNT=$(grep -r "Skill(command: \"bazinga-db-$domain\")" --include="*.md" "$REPO_ROOT" 2>/dev/null | grep -v research/ | wc -l)
    echo "  bazinga-db-$domain: $COUNT invocations"
done

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ All validation checks passed!${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  Validation passed with $WARNINGS warning(s)${NC}"
    exit 0
else
    echo -e "${RED}❌ Validation failed with $ERRORS error(s) and $WARNINGS warning(s)${NC}"
    exit 1
fi
