#!/bin/bash

# Validate Skills Structure and Invocation
# Ensures skills follow the skill-implementation-guide.md requirements

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
total_skills=0
failed_skills=0
warning_skills=0

# Size guidelines (lines)
IDEAL_MAX_LINES=250
WARNING_LINES=150

echo "=================================================="
echo "Skills Structure Validation"
echo "=================================================="
echo ""
echo "Validating against: research/skill-implementation-guide.md"
echo ""

# Function to check a single skill
check_skill() {
    local skill_dir="$1"
    local skill_name
    skill_name=$(basename "$skill_dir")
    local has_errors=false
    local has_warnings=false

    echo "📦 Checking skill: $skill_name"
    echo "--------------------------------------------------"

    # Check 1: SKILL.md exists
    if [ ! -f "$skill_dir/SKILL.md" ]; then
        echo -e "${RED}  ❌ FAIL: SKILL.md not found${NC}"
        has_errors=true
    else
        echo -e "${GREEN}  ✅ SKILL.md exists${NC}"

        # Check 2: Frontmatter fields
        local has_version has_name has_description
        has_version=$(grep -c "^version:" "$skill_dir/SKILL.md" || echo "0")
        has_name=$(grep -c "^name:" "$skill_dir/SKILL.md" || echo "0")
        has_description=$(grep -c "^description:" "$skill_dir/SKILL.md" || echo "0")

        if [ "$has_version" -eq 0 ]; then
            echo -e "${RED}  ❌ FAIL: Missing 'version' in frontmatter${NC}"
            has_errors=true
        else
            echo -e "${GREEN}  ✅ Has 'version' field${NC}"
        fi

        if [ "$has_name" -eq 0 ]; then
            echo -e "${RED}  ❌ FAIL: Missing 'name' in frontmatter${NC}"
            has_errors=true
        else
            # Check if name matches directory
            local frontmatter_name
            frontmatter_name=$(grep "^name:" "$skill_dir/SKILL.md" | head -1 | sed 's/name: *//' | tr -d '\r')
            if [ "$frontmatter_name" != "$skill_name" ]; then
                echo -e "${RED}  ❌ FAIL: Name mismatch (frontmatter: '$frontmatter_name', directory: '$skill_name')${NC}"
                has_errors=true
            else
                echo -e "${GREEN}  ✅ Name matches directory: $frontmatter_name${NC}"
            fi
        fi

        if [ "$has_description" -eq 0 ]; then
            echo -e "${RED}  ❌ FAIL: Missing 'description' in frontmatter${NC}"
            has_errors=true
        else
            echo -e "${GREEN}  ✅ Has 'description' field${NC}"
        fi

        # Check 3: Required sections
        local has_when_to_invoke has_your_task
        has_when_to_invoke=$(grep -c "## When to Invoke" "$skill_dir/SKILL.md" || echo "0")
        has_your_task=$(grep -c "## Your Task" "$skill_dir/SKILL.md" || echo "0")

        if [ "$has_when_to_invoke" -eq 0 ]; then
            echo -e "${YELLOW}  ⚠️  WARN: Missing '## When to Invoke' section${NC}"
            has_warnings=true
        else
            echo -e "${GREEN}  ✅ Has 'When to Invoke' section${NC}"
        fi

        if [ "$has_your_task" -eq 0 ]; then
            echo -e "${YELLOW}  ⚠️  WARN: Missing '## Your Task' section${NC}"
            has_warnings=true
        else
            echo -e "${GREEN}  ✅ Has 'Your Task' section${NC}"
        fi

        # Check 4: File size
        local line_count
        line_count=$(wc -l < "$skill_dir/SKILL.md")

        if [ "$line_count" -gt "$IDEAL_MAX_LINES" ]; then
            echo -e "${YELLOW}  ⚠️  WARN: SKILL.md has $line_count lines (ideal: <$IDEAL_MAX_LINES)${NC}"
            echo -e "${YELLOW}      Consider moving verbose content to references/usage.md${NC}"
            has_warnings=true
        elif [ "$line_count" -gt "$WARNING_LINES" ]; then
            echo -e "${GREEN}  ✅ Size acceptable: $line_count lines${NC}"
        else
            echo -e "${GREEN}  ✅ Size good: $line_count lines${NC}"
        fi
    fi

    echo ""

    if [ "$has_errors" = true ]; then
        failed_skills=$((failed_skills + 1))
        return 1
    elif [ "$has_warnings" = true ]; then
        warning_skills=$((warning_skills + 1))
    fi

    return 0
}

# Function to check skill invocations in agent files
check_invocations() {
    echo "🔍 Checking skill invocations in agent files..."
    echo "--------------------------------------------------"

    local bad_invocations=0

    if [ -d "agents" ]; then
        for agent_file in agents/*.md; do
            if [ -f "$agent_file" ]; then
                # Check for wrong parameter name (skill: instead of command:)
                local wrong_invocations
                wrong_invocations=$(grep -n "Skill(skill:" "$agent_file" || echo "")

                if [ -n "$wrong_invocations" ]; then
                    echo -e "${RED}❌ FAIL: $agent_file has incorrect invocation syntax${NC}"
                    echo "$wrong_invocations" | while read -r line; do
                        echo -e "${RED}  Line: $line${NC}"
                    done
                    echo -e "${YELLOW}  Should use: Skill(command: \"skill-name\")${NC}"
                    echo -e "${YELLOW}  Not:        Skill(skill: \"skill-name\")${NC}"
                    echo ""
                    bad_invocations=$((bad_invocations + 1))
                fi
            fi
        done
    fi

    # Check in .claude/commands/ as well
    if [ -d ".claude/commands" ]; then
        for cmd_file in .claude/commands/*.md; do
            if [ -f "$cmd_file" ]; then
                local wrong_invocations
                wrong_invocations=$(grep -n "Skill(skill:" "$cmd_file" || echo "")

                if [ -n "$wrong_invocations" ]; then
                    echo -e "${RED}❌ FAIL: $cmd_file has incorrect invocation syntax${NC}"
                    echo "$wrong_invocations" | while read -r line; do
                        echo -e "${RED}  Line: $line${NC}"
                    done
                    echo -e "${YELLOW}  Should use: Skill(command: \"skill-name\")${NC}"
                    echo -e "${YELLOW}  Not:        Skill(skill: \"skill-name\")${NC}"
                    echo ""
                    bad_invocations=$((bad_invocations + 1))
                fi
            fi
        done
    fi

    if [ "$bad_invocations" -eq 0 ]; then
        echo -e "${GREEN}✅ All skill invocations use correct syntax${NC}"
    else
        echo -e "${RED}❌ Found $bad_invocations file(s) with incorrect invocation syntax${NC}"
        return 1
    fi

    echo ""
    return 0
}

# Main validation
echo "Checking all skills in .claude/skills/..."
echo ""

if [ ! -d ".claude/skills" ]; then
    echo -e "${RED}❌ ERROR: .claude/skills/ directory not found${NC}"
    exit 1
fi

# Check each skill
for skill_dir in .claude/skills/*/; do
    if [ -d "$skill_dir" ]; then
        skill_name=$(basename "$skill_dir")
        # Skip internal directories (starting with _)
        if [[ "$skill_name" == _* ]]; then
            echo "⏭️  Skipping internal directory: $skill_name"
            echo ""
            continue
        fi
        check_skill "$skill_dir" || true  # Continue checking other skills
        total_skills=$((total_skills + 1))
    fi
done

# Check invocations
invocation_check_failed=false
check_invocations || invocation_check_failed=true

# Summary
echo "=================================================="
echo "Summary"
echo "=================================================="
echo "Total skills checked: $total_skills"
echo -e "${RED}Skills with errors: $failed_skills${NC}"
echo -e "${YELLOW}Skills with warnings: $warning_skills${NC}"
echo ""

# Exit with failure if any skills have errors or bad invocations
if [ "$failed_skills" -gt 0 ] || [ "$invocation_check_failed" = true ]; then
    echo -e "${RED}❌ VALIDATION FAILED${NC}"
    echo ""
    echo "Errors found in skill structure or invocation syntax."
    echo ""
    echo "To fix:"
    echo "  1. Review the errors flagged above"
    echo "  2. See research/skill-implementation-guide.md for requirements"
    echo "  3. See research/skill-fix-manual.md for step-by-step fixing"
    echo ""
    echo "Common fixes:"
    echo "  - Add missing frontmatter fields (version, name, description)"
    echo "  - Ensure name in frontmatter matches directory name"
    echo "  - Add missing sections (When to Invoke, Your Task)"
    echo "  - Fix invocation syntax: Skill(command:) not Skill(skill:)"
    echo ""
    exit 1
fi

if [ "$warning_skills" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  WARNING${NC}"
    echo ""
    echo "Some skills have warnings (non-critical)."
    echo "Consider addressing these to improve skill quality."
    echo ""
fi

echo -e "${GREEN}✅ All skills properly structured${NC}"
exit 0
