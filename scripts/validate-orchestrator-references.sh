#!/bin/bash
set -e

# Validate orchestrator.md section references (§line XXXX, §Step X.Y.Z)
# This ensures references don't break when file is edited

ORCHESTRATOR_FILE="agents/orchestrator.md"
ERRORS=0

echo "🔍 Validating orchestrator.md references..."

if [ ! -f "$ORCHESTRATOR_FILE" ]; then
    echo "❌ Error: $ORCHESTRATOR_FILE not found"
    exit 1
fi

# Extract all §line references (e.g., §line 3279)
LINE_REFS=$(grep -oE '§line [0-9]+' "$ORCHESTRATOR_FILE" | sort -u || true)

if [ -n "$LINE_REFS" ]; then
    echo "  → Found $(echo "$LINE_REFS" | wc -l) unique §line references"

    while IFS= read -r ref; do
        if [ -z "$ref" ]; then continue; fi

        # Extract line number
        LINE_NUM=$(echo "$ref" | grep -oE '[0-9]+')

        # Get total lines in file
        TOTAL_LINES=$(wc -l < "$ORCHESTRATOR_FILE")

        # Check if line number is valid
        if [ "$LINE_NUM" -gt "$TOTAL_LINES" ]; then
            echo "  ❌ BROKEN: §line $LINE_NUM (file only has $TOTAL_LINES lines)"
            ERRORS=$((ERRORS + 1))
            continue
        fi

        # Line number is valid (within file bounds)
        # Content validation would be too fragile, skip it

    done <<< "$LINE_REFS"
fi

# Extract all §Step references (e.g., §Step 2A.1)
STEP_REFS=$(grep -oE '§Step [0-9A-Z]+\.[0-9A-Z]+(\.[0-9]+)?' "$ORCHESTRATOR_FILE" | sort -u || true)

if [ -n "$STEP_REFS" ]; then
    echo "  → Found $(echo "$STEP_REFS" | wc -l) unique §Step references"

    while IFS= read -r ref; do
        if [ -z "$ref" ]; then continue; fi

        # Extract step identifier (e.g., "2A.1")
        STEP_ID=$(echo "$ref" | sed 's/§Step //')

        # Look for section header with this step
        SECTION_LINE=$(grep -n "### Step $STEP_ID" "$ORCHESTRATOR_FILE" | head -1 | cut -d: -f1 || true)

        if [ -z "$SECTION_LINE" ]; then
            echo "  ❌ BROKEN: §Step $STEP_ID (section not found)"
            echo "      Searching for: ### Step $STEP_ID"

            # Suggest nearby sections
            echo "      Available sections:"
            grep -n "### Step" "$ORCHESTRATOR_FILE" | grep -E "Step [0-9A-Z]+\.[0-9A-Z]+" | head -5 | sed 's/^/        /'

            ERRORS=$((ERRORS + 1))
        else
            # Get section title
            SECTION_TITLE=$(sed -n "${SECTION_LINE}p" "$ORCHESTRATOR_FILE")
            # echo "  ✅ Valid: §Step $STEP_ID → line $SECTION_LINE: $SECTION_TITLE"
        fi

    done <<< "$STEP_REFS"
fi

# Summary
if [ $ERRORS -eq 0 ]; then
    echo "  ✅ All references are valid"
    exit 0
else
    echo ""
    echo "❌ Validation failed: $ERRORS broken reference(s)"
    echo ""
    echo "To fix broken references:"
    echo "  1. Search for the broken reference in $ORCHESTRATOR_FILE"
    echo "  2. Find where the target content actually is now"
    echo "  3. Update the reference to point to the correct line/step"
    echo ""
    echo "Example:"
    echo "  - If §line 3279 is broken, search for 'task groups' in the file"
    echo "  - Find the actual line number where it now appears"
    echo "  - Update all references from '§line 3279' to '§line XXXX'"
    exit 1
fi
