#!/bin/bash

# Validate and auto-fix orchestrator.md section references
# Supports: §line XXXX (keyword), §Step X.Y.Z, orphan detection, auto-fix
# Also validates references in template files (phase_simple.md, phase_parallel.md)

set -e
set -o pipefail

ORCHESTRATOR_FILE="agents/orchestrator.md"

# Template paths: try bazinga/templates first (symlink in dev), fall back to templates/ (CI/no symlink)
if [ -f "bazinga/templates/orchestrator/phase_simple.md" ]; then
    TEMPLATE_SIMPLE="bazinga/templates/orchestrator/phase_simple.md"
    TEMPLATE_PARALLEL="bazinga/templates/orchestrator/phase_parallel.md"
else
    TEMPLATE_SIMPLE="templates/orchestrator/phase_simple.md"
    TEMPLATE_PARALLEL="templates/orchestrator/phase_parallel.md"
fi
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
            echo "  §Step 2A.6b                    - With lowercase suffix (a, b, c)"
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

# Portable sed -i wrapper (works on GNU, BSD/macOS, and BusyBox sed)
# Usage: portable_sed_i 's/old/new/g' file
portable_sed_i() {
    local pattern="$1"
    local file="$2"
    if sed --version 2>/dev/null | grep -q GNU; then
        # GNU sed (Linux)
        sed -i "$pattern" "$file"
    elif sed --version 2>&1 | grep -qi busybox; then
        # BusyBox sed (Alpine) - no backup suffix needed
        sed -i "$pattern" "$file"
    else
        # BSD sed (macOS) - requires empty extension argument
        sed -i '' "$pattern" "$file"
    fi
}

## Helper: Find step location across all files
# Usage: find_step_location "2A.1"
# Sets: STEP_LOCATION_FILE, STEP_LOCATION_LINE (empty if not found)
find_step_location() {
    local step_id="$1"
    # Escape dots for precise regex matching
    local step_escaped="${step_id//./\\.}"

    STEP_LOCATION_FILE=""
    STEP_LOCATION_LINE=""

    # Check all files: orchestrator, then templates
    local files=("$ORCHESTRATOR_FILE" "$TEMPLATE_SIMPLE" "$TEMPLATE_PARALLEL")
    local line
    for file in "${files[@]}"; do
        [ -f "$file" ] || continue
        # Pattern: alphanumeric boundary ([^0-9A-Za-z]|$) prevents 2A.1 matching 2A.1a or 2A.10
        line=$(grep -nE "^### Step ${step_escaped}([^0-9A-Za-z]|$)" "$file" | head -1 | cut -d: -f1 || true)
        if [ -n "$line" ]; then
            STEP_LOCATION_FILE="$file"
            STEP_LOCATION_LINE="$line"
            return 0
        fi
    done

    return 1
}

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
        # Use sed instead of grep -P for portability (macOS compatibility)
        KEYWORD=$(echo "$ref" | sed -n 's/.*(\([^)]*\)).*/\1/p')

        # Get total lines in file
        TOTAL_LINES=$(wc -l < "$ORCHESTRATOR_FILE")

        # Check if line number is valid
        if [ "$LINE_NUM" -gt "$TOTAL_LINES" ]; then
            if [ "$FIX_MODE" = true ]; then
                # Try to find content by keyword
                if [ -n "$KEYWORD" ]; then
                    # Use -F for literal match and -- to prevent option injection
                    NEW_LINE=$(grep -nFi -- "$KEYWORD" "$ORCHESTRATOR_FILE" | head -1 | cut -d: -f1 || echo "")
                    if [ -n "$NEW_LINE" ]; then
                        echo "  🔧 AUTO-FIX: §line $LINE_NUM → §line $NEW_LINE (found '$KEYWORD' at line $NEW_LINE)"
                        # Update all references in file (portable for macOS/Linux)
                        portable_sed_i "s/§line $LINE_NUM/§line $NEW_LINE/g" "$ORCHESTRATOR_FILE"
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
            # Use -F for literal match and -- to prevent option injection
            if ! echo "$ACTUAL_LINE" | grep -qFi -- "$KEYWORD"; then
                if [ "$FIX_MODE" = true ]; then
                    # Try to find content by keyword
                    NEW_LINE=$(grep -nFi -- "$KEYWORD" "$ORCHESTRATOR_FILE" | head -1 | cut -d: -f1 || echo "")
                    if [ -n "$NEW_LINE" ] && [ "$NEW_LINE" != "$LINE_NUM" ]; then
                        echo "  🔧 AUTO-FIX: §line $LINE_NUM → §line $NEW_LINE (content mismatch, found '$KEYWORD' at line $NEW_LINE)"
                        # Update all references in file (portable for macOS/Linux)
                        portable_sed_i "s/§line $LINE_NUM/§line $NEW_LINE/g" "$ORCHESTRATOR_FILE"
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
    local STEP_REFS
    STEP_REFS=$(grep -oE '§Step [0-9A-Za-z]+\.[0-9A-Za-z]+(\.[0-9A-Za-z]+)?' "$ORCHESTRATOR_FILE" | sort -u || true)

    if [ -z "$STEP_REFS" ]; then
        return 0
    fi

    echo "  → Found $(echo "$STEP_REFS" | wc -l) unique §Step references"

    while IFS= read -r ref; do
        if [ -z "$ref" ]; then continue; fi

        # Extract step identifier (e.g., "2A.1")
        local STEP_ID
        STEP_ID=$(echo "$ref" | sed 's/§Step //')

        # Use consolidated helper to find step location
        if find_step_location "$STEP_ID"; then
            if [ "$VERBOSE" = true ]; then
                echo "  ✅ §Step $STEP_ID → $STEP_LOCATION_FILE:$STEP_LOCATION_LINE"
            fi
        else
            echo "  ❌ BROKEN: §Step $STEP_ID (section not found)"
            echo "      Searching for: ### Step $STEP_ID"
            echo "      Checked: $ORCHESTRATOR_FILE, $TEMPLATE_SIMPLE, $TEMPLATE_PARALLEL"
            echo "      Available sections in orchestrator:"
            grep -nE "^### Step [0-9A-Za-z]+\.[0-9A-Za-z]+([^0-9A-Za-z]|$)" "$ORCHESTRATOR_FILE" | head -5 | sed 's/^/        /' || echo "        (none)"
            echo "      Note: §Step references cannot be auto-fixed (section structure changed)"
            ERRORS=$((ERRORS + 1))
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
    local STEP_REFS
    STEP_REFS=$(grep -oE '§Step [0-9A-Za-z]+\.[0-9A-Za-z]+(\.[0-9A-Za-z]+)?' "$TEMPLATE_FILE" | sort -u || true)

    if [ -z "$STEP_REFS" ]; then
        return 0
    fi

    echo "  → Found $(echo "$STEP_REFS" | wc -l) unique §Step references in $TEMPLATE_NAME"

    while IFS= read -r ref; do
        if [ -z "$ref" ]; then continue; fi

        local STEP_ID
        STEP_ID=$(echo "$ref" | sed 's/§Step //')

        # Use consolidated helper to find step location
        if find_step_location "$STEP_ID"; then
            if [ "$VERBOSE" = true ]; then
                echo "  ✅ §Step $STEP_ID → $STEP_LOCATION_FILE:$STEP_LOCATION_LINE"
            fi
        else
            echo "  ❌ BROKEN: §Step $STEP_ID in $TEMPLATE_NAME (section not found)"
            echo "      Checked: $ORCHESTRATOR_FILE, $TEMPLATE_SIMPLE, $TEMPLATE_PARALLEL"
            ERRORS=$((ERRORS + 1))
        fi

    done <<< "$STEP_REFS"
}

## Helper function to check if step is referenced in any file
# Must be defined at top level (not inside another function)
is_step_referenced() {
    local step_id="$1"
    # Escape dots and use alphanumeric boundary ([^0-9A-Za-z]|$) to prevent false matches (2A.1 vs 2A.1a or 2A.10)
    local step_escaped="${step_id//./\\.}"
    local files=("$ORCHESTRATOR_FILE" "$TEMPLATE_SIMPLE" "$TEMPLATE_PARALLEL")
    for file in "${files[@]}"; do
        [ -f "$file" ] || continue
        grep -qE "§Step ${step_escaped}([^0-9A-Za-z]|$)" "$file" 2>/dev/null && return 0
    done
    return 1
}

## Helper: Check orphaned steps in a single file
# Usage: check_file_orphans "/path/to/file.md"
# Increments global ORPHAN_STEPS counter
check_file_orphans() {
    local file="$1"

    if [ ! -f "$file" ]; then
        return 0
    fi

    while IFS= read -r line; do
        local line_num
        local step_id
        line_num=$(echo "$line" | cut -d: -f1)
        # Use || true to handle grep returning 1 when no match (pipefail safe)
        step_id=$(echo "$line" | grep -oE 'Step [0-9A-Za-z]+\.[0-9A-Za-z]+(\.[0-9A-Za-z]+)?' | sed 's/Step //' || true)

        if [ -n "$step_id" ]; then
            # Check if this step is referenced anywhere (orchestrator + templates)
            if ! is_step_referenced "$step_id"; then
                echo "  ⚠️  ORPHAN: ### Step $step_id ($file:$line_num) - not referenced"
                ORPHAN_STEPS=$((ORPHAN_STEPS + 1))
            fi
        fi
    done < <(grep -n "^### Step" "$file" || true)
}

## Feature 3: Reverse Lookup - Find Orphaned Sections
check_orphaned_sections() {
    if [ "$CHECK_ORPHANS" != true ]; then
        return 0
    fi

    echo ""
    echo "🔍 Checking for orphaned sections (not referenced anywhere)..."

    # Check for orphaned ### Step headers in all files
    ORPHAN_STEPS=0
    check_file_orphans "$ORCHESTRATOR_FILE"
    check_file_orphans "$TEMPLATE_SIMPLE"
    check_file_orphans "$TEMPLATE_PARALLEL"

    # Check for sections with <!-- ANCHOR: --> markers (future use)
    ORPHAN_ANCHORS=0
    while IFS= read -r line; do
        LINE_NUM=$(echo "$line" | cut -d: -f1)
        # Use sed instead of grep -P for portability; [^ ]* matches non-space chars (including hyphens)
        ANCHOR_NAME=$(echo "$line" | sed -n 's/.*<!-- ANCHOR: \([^ ]*\) -->.*/\1/p')

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

# Only show template validation banners if files exist
if [ -f "$TEMPLATE_SIMPLE" ]; then
    echo ""
    echo "📄 Validating: $TEMPLATE_SIMPLE"
    validate_template_step_references "$TEMPLATE_SIMPLE" "phase_simple.md"
fi

if [ -f "$TEMPLATE_PARALLEL" ]; then
    echo ""
    echo "📄 Validating: $TEMPLATE_PARALLEL"
    validate_template_step_references "$TEMPLATE_PARALLEL" "phase_parallel.md"
fi

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
