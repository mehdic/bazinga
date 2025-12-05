#!/bin/bash

# Validate and auto-fix orchestrator.md section references
# Supports: §line XXXX (keyword), §Step X.Y.Z, orphan detection, auto-fix
# Also validates references in template files (phase_simple.md, phase_parallel.md)

set -e

ORCHESTRATOR_FILE="agents/orchestrator.md"
TEMPLATE_SIMPLE="bazinga/templates/orchestrator/phase_simple.md"
TEMPLATE_PARALLEL="bazinga/templates/orchestrator/phase_parallel.md"
ERRORS=0
WARNINGS=0
FIX_MODE=false
CHECK_ORPHANS=false
VERBOSE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --fix)
            FIX_MODE=true
            shift
            ;;
        --check-orphans)
            CHECK_ORPHANS=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Validate orchestrator.md and template file references (§line XXXX, §Step X.Y.Z)"
            echo "Also checks phase_simple.md and phase_parallel.md for cross-file references"
            echo ""
            echo "Options:"
            echo "  --fix             Auto-fix broken line references (updates file)"
            echo "  --check-orphans   Find sections that nothing references"
            echo "  --verbose, -v     Show detailed validation info"
            echo "  --help, -h        Show this help message"
            echo ""
            echo "Reference formats:"
            echo "  §line 3279                     - Reference to line 3279"
            echo "  §line 3279 (task groups)       - With content keyword validation"
            echo "  §Step 2A.1                     - Reference to Step 2A.1 section"
            echo ""
            echo "Examples:"
            echo "  $0                             - Validate all references"
            echo "  $0 --fix                       - Auto-fix broken references"
            echo "  $0 --check-orphans             - Find unreferenced sections"
            echo "  $0 --fix --check-orphans -v    - Full validation + fix + orphans"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "🔍 Validating orchestrator.md references..."
[ "$FIX_MODE" = true ] && echo "   🔧 Auto-fix mode enabled"
[ "$CHECK_ORPHANS" = true ] && echo "   🔍 Orphan detection enabled"

if [ ! -f "$ORCHESTRATOR_FILE" ]; then
    echo "❌ Error: $ORCHESTRATOR_FILE not found"
    exit 1
fi

# Create temp file for fixes
TEMP_FILE="${ORCHESTRATOR_FILE}.tmp"

## Feature 1: Content Validation with Keywords
validate_line_references() {
    # Extract all §line references with optional keywords
    # Format: §line 3279 (keyword) or §line 3279
    LINE_REFS=$(grep -oE '§line [0-9]+( \([^)]+\))?' "$ORCHESTRATOR_FILE" | sort -u || true)

    if [ -z "$LINE_REFS" ]; then
        return 0
    fi

    echo "  → Found $(echo "$LINE_REFS" | wc -l) unique §line references"

    while IFS= read -r ref; do
        if [ -z "$ref" ]; then continue; fi

        # Extract line number and optional keyword
        LINE_NUM=$(echo "$ref" | grep -oE '[0-9]+')
        KEYWORD=$(echo "$ref" | grep -oP '\(\K[^)]+' || echo "")

        # Get total lines in file
        TOTAL_LINES=$(wc -l < "$ORCHESTRATOR_FILE")

        # Check if line number is valid
        if [ "$LINE_NUM" -gt "$TOTAL_LINES" ]; then
            if [ "$FIX_MODE" = true ]; then
                # Try to find content by keyword
                if [ -n "$KEYWORD" ]; then
                    NEW_LINE=$(grep -n -i "$KEYWORD" "$ORCHESTRATOR_FILE" | head -1 | cut -d: -f1 || echo "")
                    if [ -n "$NEW_LINE" ]; then
                        echo "  🔧 AUTO-FIX: §line $LINE_NUM → §line $NEW_LINE (found '$KEYWORD' at line $NEW_LINE)"
                        # Update all references in file
                        sed -i "s/§line $LINE_NUM/§line $NEW_LINE/g" "$ORCHESTRATOR_FILE"
                        continue
                    fi
                fi
                echo "  ❌ CANNOT FIX: §line $LINE_NUM (file only has $TOTAL_LINES lines, no keyword to search)"
                ERRORS=$((ERRORS + 1))
            else
                echo "  ❌ BROKEN: §line $LINE_NUM (file only has $TOTAL_LINES lines)"
                [ -n "$KEYWORD" ] && echo "      Expected keyword: '$KEYWORD'"
                echo "      Hint: Run with --fix to auto-update"
                ERRORS=$((ERRORS + 1))
            fi
            continue
        fi

        # Validate content if keyword is provided
        if [ -n "$KEYWORD" ]; then
            ACTUAL_LINE=$(sed -n "${LINE_NUM}p" "$ORCHESTRATOR_FILE")
            if ! echo "$ACTUAL_LINE" | grep -qi "$KEYWORD"; then
                if [ "$FIX_MODE" = true ]; then
                    # Try to find content by keyword
                    NEW_LINE=$(grep -n -i "$KEYWORD" "$ORCHESTRATOR_FILE" | head -1 | cut -d: -f1 || echo "")
                    if [ -n "$NEW_LINE" ] && [ "$NEW_LINE" != "$LINE_NUM" ]; then
                        echo "  🔧 AUTO-FIX: §line $LINE_NUM → §line $NEW_LINE (content mismatch, found '$KEYWORD' at line $NEW_LINE)"
                        sed -i "s/§line $LINE_NUM/§line $NEW_LINE/g" "$ORCHESTRATOR_FILE"
                        continue
                    fi
                fi
                echo "  ⚠️  CONTENT MISMATCH: §line $LINE_NUM"
                echo "      Expected keyword: '$KEYWORD'"
                echo "      Actual content: $ACTUAL_LINE"
                WARNINGS=$((WARNINGS + 1))
            elif [ "$VERBOSE" = true ]; then
                echo "  ✅ §line $LINE_NUM: '$KEYWORD' ✓"
            fi
        fi

    done <<< "$LINE_REFS"
}

## Feature 2: Step Reference Validation
validate_step_references() {
    # Extract all §Step references (e.g., §Step 2A.1, §Step 2A.6b)
    # Note: [0-9A-Za-z]+ includes lowercase for step suffixes like 'a', 'b', 'c'
    STEP_REFS=$(grep -oE '§Step [0-9A-Za-z]+\.[0-9A-Za-z]+(\.[0-9]+)?' "$ORCHESTRATOR_FILE" | sort -u || true)

    if [ -z "$STEP_REFS" ]; then
        return 0
    fi

    echo "  → Found $(echo "$STEP_REFS" | wc -l) unique §Step references"

    while IFS= read -r ref; do
        if [ -z "$ref" ]; then continue; fi

        # Extract step identifier (e.g., "2A.1")
        STEP_ID=$(echo "$ref" | sed 's/§Step //')

        # Look for section header with this step
        # Check main orchestrator file first
        SECTION_LINE=$(grep -n "### Step $STEP_ID" "$ORCHESTRATOR_FILE" | head -1 | cut -d: -f1 || true)
        FOUND_IN=""

        # If not found in main file, check template files
        if [ -z "$SECTION_LINE" ]; then
            # Step 2A.x sections are in phase_simple.md
            if [[ "$STEP_ID" == 2A.* ]]; then
                TEMPLATE_FILE="bazinga/templates/orchestrator/phase_simple.md"
                if [ -f "$TEMPLATE_FILE" ]; then
                    SECTION_LINE=$(grep -n "### Step $STEP_ID" "$TEMPLATE_FILE" | head -1 | cut -d: -f1 || true)
                    [ -n "$SECTION_LINE" ] && FOUND_IN="$TEMPLATE_FILE"
                fi
            fi
            # Step 2B.x sections are in phase_parallel.md
            if [[ "$STEP_ID" == 2B.* ]]; then
                TEMPLATE_FILE="bazinga/templates/orchestrator/phase_parallel.md"
                if [ -f "$TEMPLATE_FILE" ]; then
                    SECTION_LINE=$(grep -n "### Step $STEP_ID" "$TEMPLATE_FILE" | head -1 | cut -d: -f1 || true)
                    [ -n "$SECTION_LINE" ] && FOUND_IN="$TEMPLATE_FILE"
                fi
            fi
        fi

        if [ -z "$SECTION_LINE" ]; then
            echo "  ❌ BROKEN: §Step $STEP_ID (section not found)"
            echo "      Searching for: ### Step $STEP_ID"
            echo "      Checked: $ORCHESTRATOR_FILE"
            [[ "$STEP_ID" == 2A.* ]] && echo "      Checked: bazinga/templates/orchestrator/phase_simple.md"
            [[ "$STEP_ID" == 2B.* ]] && echo "      Checked: bazinga/templates/orchestrator/phase_parallel.md"
            echo "      Available sections in orchestrator:"
            grep -n "### Step" "$ORCHESTRATOR_FILE" | grep -E "Step [0-9A-Za-z]+\.[0-9A-Za-z]+" | head -5 | sed 's/^/        /' || echo "        (none)"
            echo "      Note: §Step references cannot be auto-fixed (section structure changed)"
            ERRORS=$((ERRORS + 1))
        elif [ "$VERBOSE" = true ]; then
            if [ -n "$FOUND_IN" ]; then
                echo "  ✅ §Step $STEP_ID → $FOUND_IN:$SECTION_LINE"
            else
                SECTION_TITLE=$(sed -n "${SECTION_LINE}p" "$ORCHESTRATOR_FILE")
                echo "  ✅ §Step $STEP_ID → line $SECTION_LINE"
            fi
        fi

    done <<< "$STEP_REFS"
}

## Feature 2b: Template File Step Reference Validation
validate_template_step_references() {
    local TEMPLATE_FILE="$1"
    local TEMPLATE_NAME="$2"

    if [ ! -f "$TEMPLATE_FILE" ]; then
        return 0
    fi

    # Extract all §Step references from template file
    STEP_REFS=$(grep -oE '§Step [0-9A-Za-z]+\.[0-9A-Za-z]+(\.[0-9]+)?' "$TEMPLATE_FILE" | sort -u || true)

    if [ -z "$STEP_REFS" ]; then
        return 0
    fi

    echo "  → Found $(echo "$STEP_REFS" | wc -l) unique §Step references in $TEMPLATE_NAME"

    while IFS= read -r ref; do
        if [ -z "$ref" ]; then continue; fi

        STEP_ID=$(echo "$ref" | sed 's/§Step //')
        SECTION_LINE=""
        FOUND_IN=""

        # Check main orchestrator file first (for Step 0.x, 1.x references)
        SECTION_LINE=$(grep -n "### Step $STEP_ID" "$ORCHESTRATOR_FILE" | head -1 | cut -d: -f1 || true)
        [ -n "$SECTION_LINE" ] && FOUND_IN="$ORCHESTRATOR_FILE"

        # Check phase_simple.md for Step 2A.x references
        if [ -z "$SECTION_LINE" ]; then
            if [ -f "$TEMPLATE_SIMPLE" ]; then
                SECTION_LINE=$(grep -n "### Step $STEP_ID" "$TEMPLATE_SIMPLE" | head -1 | cut -d: -f1 || true)
                [ -n "$SECTION_LINE" ] && FOUND_IN="$TEMPLATE_SIMPLE"
            fi
        fi

        # Check phase_parallel.md for Step 2B.x references
        if [ -z "$SECTION_LINE" ]; then
            if [ -f "$TEMPLATE_PARALLEL" ]; then
                SECTION_LINE=$(grep -n "### Step $STEP_ID" "$TEMPLATE_PARALLEL" | head -1 | cut -d: -f1 || true)
                [ -n "$SECTION_LINE" ] && FOUND_IN="$TEMPLATE_PARALLEL"
            fi
        fi

        if [ -z "$SECTION_LINE" ]; then
            echo "  ❌ BROKEN: §Step $STEP_ID in $TEMPLATE_NAME (section not found)"
            echo "      Checked: $ORCHESTRATOR_FILE, $TEMPLATE_SIMPLE, $TEMPLATE_PARALLEL"
            ERRORS=$((ERRORS + 1))
        elif [ "$VERBOSE" = true ]; then
            echo "  ✅ §Step $STEP_ID → $FOUND_IN:$SECTION_LINE"
        fi

    done <<< "$STEP_REFS"
}

## Feature 3: Reverse Lookup - Find Orphaned Sections
check_orphaned_sections() {
    if [ "$CHECK_ORPHANS" != true ]; then
        return 0
    fi

    echo ""
    echo "🔍 Checking for orphaned sections (not referenced anywhere)..."

    # Find all important sections that could be referenced
    # Pattern: Look for sections with specific markers or important content

    # Check for sections with ### Step headers
    ORPHAN_STEPS=0
    while IFS= read -r line; do
        LINE_NUM=$(echo "$line" | cut -d: -f1)
        STEP_ID=$(echo "$line" | grep -oE 'Step [0-9A-Z]+\.[0-9A-Z]+(\.[0-9]+)?' | sed 's/Step //')

        if [ -n "$STEP_ID" ]; then
            # Check if this step is referenced anywhere
            if ! grep -q "§Step $STEP_ID" "$ORCHESTRATOR_FILE"; then
                echo "  ⚠️  ORPHAN: ### Step $STEP_ID (line $LINE_NUM) - not referenced"
                ORPHAN_STEPS=$((ORPHAN_STEPS + 1))
            fi
        fi
    done < <(grep -n "^### Step" "$ORCHESTRATOR_FILE" || true)

    # Check for sections with <!-- ANCHOR: --> markers (future use)
    ORPHAN_ANCHORS=0
    while IFS= read -r line; do
        LINE_NUM=$(echo "$line" | cut -d: -f1)
        ANCHOR_NAME=$(echo "$line" | grep -oP '<!-- ANCHOR: \K[^-]+(?= -->)' || echo "")

        if [ -n "$ANCHOR_NAME" ]; then
            # Check if this anchor is referenced anywhere
            if ! grep -q "§anchor $ANCHOR_NAME" "$ORCHESTRATOR_FILE"; then
                echo "  ⚠️  ORPHAN ANCHOR: $ANCHOR_NAME (line $LINE_NUM) - not referenced"
                ORPHAN_ANCHORS=$((ORPHAN_ANCHORS + 1))
            fi
        fi
    done < <(grep -n "<!-- ANCHOR:" "$ORCHESTRATOR_FILE" || true)

    if [ $ORPHAN_STEPS -eq 0 ] && [ $ORPHAN_ANCHORS -eq 0 ]; then
        echo "  ✅ No orphaned sections found"
    else
        echo ""
        echo "  Found $ORPHAN_STEPS orphaned step(s) and $ORPHAN_ANCHORS orphaned anchor(s)"
        echo "  Note: Orphans are not errors, but may indicate unused sections"
    fi
}

# Run validations
echo ""
echo "📄 Validating: $ORCHESTRATOR_FILE"
validate_line_references
validate_step_references

echo ""
echo "📄 Validating: $TEMPLATE_SIMPLE"
validate_template_step_references "$TEMPLATE_SIMPLE" "phase_simple.md"

echo ""
echo "📄 Validating: $TEMPLATE_PARALLEL"
validate_template_step_references "$TEMPLATE_PARALLEL" "phase_parallel.md"

check_orphaned_sections

# Summary
echo ""
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "✅ All references are valid"
    [ "$FIX_MODE" = true ] && echo "   No fixes were needed"
    exit 0
elif [ $ERRORS -eq 0 ] && [ $WARNINGS -gt 0 ]; then
    echo "⚠️  Validation passed with $WARNINGS warning(s)"
    echo "   Warnings indicate content mismatches but won't block commits"
    exit 0
else
    echo "❌ Validation failed: $ERRORS error(s), $WARNINGS warning(s)"
    echo ""
    if [ "$FIX_MODE" = true ]; then
        echo "Some references could not be auto-fixed."
        echo "Manual intervention required:"
        echo "  1. Review the errors above"
        echo "  2. Update references manually"
        echo "  3. Run validation again"
    else
        echo "To auto-fix broken references:"
        echo "  ./scripts/validate-orchestrator-references.sh --fix"
        echo ""
        echo "To manually fix:"
        echo "  1. Search for the broken reference in $ORCHESTRATOR_FILE"
        echo "  2. Find where the target content actually is now"
        echo "  3. Update the reference to point to the correct line/step"
    fi
    exit 1
fi
