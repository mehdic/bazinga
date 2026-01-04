#!/bin/bash
# update-checkmarks.sh - Update SpecKit task checkmarks portably
# Usage: update-checkmarks.sh <feature_dir> <task_id1> [task_id2] ...
#
# Marks tasks as complete in tasks.md: - [ ] [T001] → - [x] [T001]
# Works on Linux (GNU sed), macOS (BSD sed), and Windows (via Git Bash)

set -e

FEATURE_DIR="$1"
shift

if [ -z "$FEATURE_DIR" ] || [ ! -d "$FEATURE_DIR" ]; then
    echo "Error: Feature directory not found: $FEATURE_DIR" >&2
    exit 1
fi

TASKS_FILE="$FEATURE_DIR/tasks.md"

if [ ! -f "$TASKS_FILE" ]; then
    echo "Error: tasks.md not found: $TASKS_FILE" >&2
    exit 1
fi

if [ $# -eq 0 ]; then
    echo "Error: No task IDs provided" >&2
    exit 1
fi

# Create temp file for atomic update
TEMP_FILE=$(mktemp)
trap 'rm -f "$TEMP_FILE"' EXIT

# Read original file
cp "$TASKS_FILE" "$TEMP_FILE"

# Update each task ID
UPDATED=0
for task_id in "$@"; do
    # Escape special regex characters in task_id (just in case)
    escaped_id=$(printf '%s\n' "$task_id" | sed 's/[[\.*^$()+?{|]/\\&/g')

    # Check if task exists as unchecked
    if grep -q "^- \[ \] \[${escaped_id}\]" "$TEMP_FILE"; then
        # Use sed with temp file approach (portable)
        sed "s/^- \[ \] \[${escaped_id}\]/- [x] [${escaped_id}]/" "$TEMP_FILE" > "${TEMP_FILE}.new"
        mv "${TEMP_FILE}.new" "$TEMP_FILE"
        UPDATED=$((UPDATED + 1))
    fi
done

# Atomic replace
mv "$TEMP_FILE" "$TASKS_FILE"
trap - EXIT

echo "Updated $UPDATED task(s) in $TASKS_FILE"
exit 0
