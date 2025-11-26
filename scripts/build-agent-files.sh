#!/bin/bash
#
# Build Agent Files
#
# Generates agent files from sources:
#   - developer.md = copy of _sources/developer.base.md
#   - senior_software_engineer.md = _sources/developer.base.md + _sources/senior.delta.md
#
# Usage:
#   ./scripts/build-agent-files.sh [--check]
#
# Options:
#   --check   Only verify files are up to date, don't modify (for CI)
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SOURCES_DIR="$PROJECT_ROOT/agents/_sources"
OUTPUT_DIR="$PROJECT_ROOT/agents"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse arguments
CHECK_MODE=false
if [[ "$1" == "--check" ]]; then
    CHECK_MODE=true
fi

# Verify source files exist
if [[ ! -f "$SOURCES_DIR/developer.base.md" ]]; then
    echo -e "${RED}Error: Source file not found: $SOURCES_DIR/developer.base.md${NC}"
    exit 1
fi

if [[ ! -f "$SOURCES_DIR/senior.delta.md" ]]; then
    echo -e "${RED}Error: Delta file not found: $SOURCES_DIR/senior.delta.md${NC}"
    exit 1
fi

echo "Building agent files..."
echo "  Source directory: $SOURCES_DIR"
echo "  Output directory: $OUTPUT_DIR"
echo ""

if $CHECK_MODE; then
    echo -e "${YELLOW}Running in CHECK mode (no files will be modified)${NC}"
    echo ""

    # Create temp directory for generated files
    TEMP_DIR=$(mktemp -d)
    trap "rm -rf $TEMP_DIR" EXIT

    # Generate to temp location
    cp "$SOURCES_DIR/developer.base.md" "$TEMP_DIR/developer.md"
    python3 "$SCRIPT_DIR/merge_agent_delta.py" \
        "$SOURCES_DIR/developer.base.md" \
        "$SOURCES_DIR/senior.delta.md" \
        "$TEMP_DIR/senior_software_engineer.md"

    # Compare with existing files
    FAILED=false

    echo "Checking developer.md..."
    if diff -q "$TEMP_DIR/developer.md" "$OUTPUT_DIR/developer.md" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓ developer.md is up to date${NC}"
    else
        echo -e "  ${RED}✗ developer.md is OUT OF DATE${NC}"
        echo "    Run './scripts/build-agent-files.sh' to regenerate"
        FAILED=true
    fi

    echo "Checking senior_software_engineer.md..."
    if diff -q "$TEMP_DIR/senior_software_engineer.md" "$OUTPUT_DIR/senior_software_engineer.md" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓ senior_software_engineer.md is up to date${NC}"
    else
        echo -e "  ${RED}✗ senior_software_engineer.md is OUT OF DATE${NC}"
        echo "    Run './scripts/build-agent-files.sh' to regenerate"
        FAILED=true
    fi

    echo ""
    if $FAILED; then
        echo -e "${RED}Agent files are out of sync with sources!${NC}"
        echo ""
        echo "==================== DIFF OUTPUT ===================="
        echo ""

        if ! diff -q "$TEMP_DIR/developer.md" "$OUTPUT_DIR/developer.md" > /dev/null 2>&1; then
            echo "--- developer.md diff ---"
            diff -u "$OUTPUT_DIR/developer.md" "$TEMP_DIR/developer.md" || true
            echo ""
        fi

        if ! diff -q "$TEMP_DIR/senior_software_engineer.md" "$OUTPUT_DIR/senior_software_engineer.md" > /dev/null 2>&1; then
            echo "--- senior_software_engineer.md diff ---"
            diff -u "$OUTPUT_DIR/senior_software_engineer.md" "$TEMP_DIR/senior_software_engineer.md" || true
            echo ""
        fi

        echo "==================== FIX INSTRUCTIONS ===================="
        echo ""
        echo "To fix, run locally:"
        echo "  ./scripts/build-agent-files.sh"
        echo "  git add agents/developer.md agents/senior_software_engineer.md"
        echo "  git commit --amend --no-edit"
        echo ""
        echo "Or install the pre-commit hook to auto-rebuild:"
        echo "  ./scripts/install-hooks.sh"
        echo ""
        exit 1
    else
        echo -e "${GREEN}All agent files are up to date.${NC}"
        exit 0
    fi
else
    # Generate developer.md (direct copy)
    echo "Generating developer.md..."
    cp "$SOURCES_DIR/developer.base.md" "$OUTPUT_DIR/developer.md"
    echo -e "  ${GREEN}✓ Generated developer.md${NC}"

    # Generate senior_software_engineer.md (base + delta)
    echo "Generating senior_software_engineer.md..."
    python3 "$SCRIPT_DIR/merge_agent_delta.py" \
        "$SOURCES_DIR/developer.base.md" \
        "$SOURCES_DIR/senior.delta.md" \
        "$OUTPUT_DIR/senior_software_engineer.md"
    echo -e "  ${GREEN}✓ Generated senior_software_engineer.md${NC}"

    echo ""
    echo -e "${GREEN}Agent files built successfully!${NC}"

    # Show file sizes for verification
    echo ""
    echo "File sizes:"
    echo "  developer.md:              $(wc -l < "$OUTPUT_DIR/developer.md") lines"
    echo "  senior_software_engineer.md: $(wc -l < "$OUTPUT_DIR/senior_software_engineer.md") lines"
fi
