#!/bin/bash
# parse-speckit-tasks.sh
# Utility script to parse spec-kit tasks.md format and extract useful information
# for BAZINGA orchestration system
#
# Usage:
#   bash .claude/scripts/parse-speckit-tasks.sh <tasks.md path>
#   bash .claude/scripts/parse-speckit-tasks.sh .specify/features/001-auth/tasks.md

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    local color=$1
    shift
    echo -e "${color}$@${NC}"
}

# Function to print section header
print_section() {
    echo ""
    print_color "$CYAN" "═══════════════════════════════════════════"
    print_color "$CYAN" "$1"
    print_color "$CYAN" "═══════════════════════════════════════════"
}

# Check if file path provided
if [ $# -eq 0 ]; then
    print_color "$RED" "Error: tasks.md file path required"
    echo ""
    echo "Usage: $0 <path-to-tasks.md>"
    echo ""
    echo "Examples:"
    echo "  $0 .specify/features/001-auth/tasks.md"
    echo "  $0 tasks.md"
    exit 1
fi

TASKS_FILE="$1"

# Check if file exists
if [ ! -f "$TASKS_FILE" ]; then
    print_color "$RED" "Error: File not found: $TASKS_FILE"
    exit 1
fi

# Parse tasks
print_section "SPEC-KIT TASKS ANALYSIS"

# Count total tasks
total_tasks=$(grep -c '^\s*-\s*\[.\]\s*\[T[0-9]*\]' "$TASKS_FILE" || echo "0")
print_color "$BLUE" "📋 Total Tasks: $total_tasks"

# Count completed tasks
completed_tasks=$(grep -c '^\s*-\s*\[x\]\s*\[T[0-9]*\]' "$TASKS_FILE" || echo "0")
print_color "$GREEN" "✅ Completed: $completed_tasks"

# Count pending tasks
pending_tasks=$((total_tasks - completed_tasks))
print_color "$YELLOW" "⏳ Pending: $pending_tasks"

# Calculate progress percentage
if [ "$total_tasks" -gt 0 ]; then
    progress=$((completed_tasks * 100 / total_tasks))
    print_color "$CYAN" "📊 Progress: ${progress}%"
fi

# Find parallel tasks
print_section "PARALLEL TASKS"
parallel_count=$(grep -c '\[P\]' "$TASKS_FILE" || echo "0")
print_color "$BLUE" "🔀 Tasks marked [P]: $parallel_count"

if [ "$parallel_count" -gt 0 ]; then
    echo ""
    print_color "$CYAN" "Parallel tasks:"
    grep '\[P\]' "$TASKS_FILE" | sed 's/^/  /' || true
fi

# Find user stories
print_section "USER STORIES"
user_stories=$(grep -oE '\[US[0-9]+\]' "$TASKS_FILE" | sort -u || echo "")

if [ -n "$user_stories" ]; then
    for story in $user_stories; do
        story_count=$(grep -c "$story" "$TASKS_FILE" || echo "0")
        story_completed=$(grep "\[x\].*$story" "$TASKS_FILE" | wc -l || echo "0")
        print_color "$BLUE" "$story: $story_completed/$story_count tasks complete"

        echo ""
        print_color "$CYAN" "  Tasks in $story:"
        grep "$story" "$TASKS_FILE" | sed 's/^/    /' || true
        echo ""
    done
else
    print_color "$YELLOW" "No user story markers found"
fi

# Group tasks by status
print_section "TASKS BY STATUS"

echo ""
print_color "$GREEN" "✅ COMPLETED TASKS:"
completed_list=$(grep '^\s*-\s*\[x\]\s*\[T[0-9]*\]' "$TASKS_FILE" || echo "")
if [ -n "$completed_list" ]; then
    echo "$completed_list" | sed 's/^/  /'
else
    echo "  (none)"
fi

echo ""
print_color "$YELLOW" "⏳ PENDING TASKS:"
pending_list=$(grep '^\s*-\s*\[ \]\s*\[T[0-9]*\]' "$TASKS_FILE" || echo "")
if [ -n "$pending_list" ]; then
    echo "$pending_list" | sed 's/^/  /'
else
    echo "  (none)"
fi

# Extract task IDs
print_section "TASK IDs"

echo ""
print_color "$CYAN" "All Task IDs:"
task_ids=$(grep -oE 'T[0-9]+' "$TASKS_FILE" | sort -u || echo "")
if [ -n "$task_ids" ]; then
    echo "$task_ids" | tr '\n' ' '
    echo ""
else
    echo "  (none found)"
fi

# Extract files mentioned
print_section "FILES AFFECTED"

echo ""
print_color "$CYAN" "Files mentioned in tasks:"
files=$(grep -oE '\([a-zA-Z0-9_/.-]+\.(py|js|ts|go|rs|java|rb|php|cpp|h|md)\)' "$TASKS_FILE" | tr -d '()' | sort -u || echo "")
if [ -n "$files" ]; then
    echo "$files" | sed 's/^/  /'
else
    echo "  (none found)"
fi

# Generate JSON summary
print_section "JSON SUMMARY"

echo ""
print_color "$CYAN" "JSON output (for programmatic use):"

cat <<EOF
{
  "total_tasks": $total_tasks,
  "completed_tasks": $completed_tasks,
  "pending_tasks": $pending_tasks,
  "progress_percentage": ${progress:-0},
  "parallel_tasks": $parallel_count,
  "user_stories": [
EOF

# Print user stories JSON
if [ -n "$user_stories" ]; then
    first=true
    for story in $user_stories; do
        if [ "$first" = true ]; then
            first=false
        else
            echo ","
        fi
        story_count=$(grep -c "$story" "$TASKS_FILE" || echo "0")
        story_completed=$(grep "\[x\].*$story" "$TASKS_FILE" | wc -l || echo "0")
        echo -n "    {\"story\": \"$story\", \"total\": $story_count, \"completed\": $story_completed}"
        echo -n "}"
    done
    echo ""
fi

cat <<EOF
  ],
  "task_ids": [$(echo "$task_ids" | tr '\n' ',' | sed 's/,$//' | sed 's/T\([0-9]*\)/"T\1"/g')],
  "files": [$(echo "$files" | tr '\n' ',' | sed 's/,$//' | sed 's/\(.*\)/"\1"/g')]
}
EOF

print_section "ANALYSIS COMPLETE"

echo ""
print_color "$BLUE" "💡 Tip: Use this information to plan BAZINGA orchestration groups"
echo ""

# Exit with success if all tasks complete, otherwise exit code indicates pending tasks
if [ "$pending_tasks" -eq 0 ]; then
    print_color "$GREEN" "🎉 All tasks complete!"
    exit 0
else
    print_color "$YELLOW" "⚠️  $pending_tasks tasks remaining"
    exit 1
fi
