#!/bin/bash

# Validate Agent and Command File Sizes
# Ensures files don't exceed Claude Code's practical token limits

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Size limits
# Claude Code has a practical limit of ~25,000 tokens
# Using rough estimate of 4 characters per token = 100,000 characters
HARD_LIMIT_CHARS=100000  # ~25,000 tokens - will fail CI
WARN_LIMIT_CHARS=80000   # ~20,000 tokens - will show warning

# Counters
total_files=0
oversized_files=0
warning_files=0

echo "=================================================="
echo "Agent and Command File Size Validation"
echo "=================================================="
echo ""
echo "Limits:"
echo "  ⛔ Hard limit: 100,000 chars (~25,000 tokens)"
echo "  ⚠️  Warning:    80,000 chars (~20,000 tokens)"
echo ""

# Function to check a single file
check_file() {
    local file="$1"
    local char_count

    # Get character count (bytes, approximation for ASCII/UTF-8 text)
    char_count=$(wc -c < "$file")

    # Get line count for additional context
    local line_count
    line_count=$(wc -l < "$file")

    # Estimate tokens (rough: 4 chars per token)
    local estimated_tokens=$((char_count / 4))

    # Check against limits
    if [ "$char_count" -gt "$HARD_LIMIT_CHARS" ]; then
        echo -e "${RED}❌ FAIL${NC}: $file"
        echo "   Size: $char_count chars (~$estimated_tokens tokens, $line_count lines)"
        echo "   Exceeds hard limit by $((char_count - HARD_LIMIT_CHARS)) characters"
        echo ""
        oversized_files=$((oversized_files + 1))
        return 1
    elif [ "$char_count" -gt "$WARN_LIMIT_CHARS" ]; then
        echo -e "${YELLOW}⚠️  WARN${NC}: $file"
        echo "   Size: $char_count chars (~$estimated_tokens tokens, $line_count lines)"
        echo "   Approaching limit (${WARN_LIMIT_CHARS} chars)"
        echo ""
        warning_files=$((warning_files + 1))
        return 0
    else
        echo -e "${GREEN}✅ PASS${NC}: $file"
        echo "   Size: $char_count chars (~$estimated_tokens tokens, $line_count lines)"
        return 0
    fi
}

# Check all agent files
echo "Checking agents/*.md files..."
echo "--------------------------------------------------"
if [ -d "agents" ]; then
    for file in agents/*.md; do
        if [ -f "$file" ]; then
            check_file "$file" || true  # Continue even if check fails
            total_files=$((total_files + 1))
        fi
    done
else
    echo "⚠️  Warning: agents/ directory not found"
fi

echo ""
echo "Checking .claude/commands/*.md files..."
echo "--------------------------------------------------"
if [ -d ".claude/commands" ]; then
    for file in .claude/commands/*.md; do
        if [ -f "$file" ]; then
            check_file "$file" || true  # Continue even if check fails
            total_files=$((total_files + 1))
        fi
    done
else
    echo "⚠️  Warning: .claude/commands/ directory not found"
fi

# Summary
echo ""
echo "=================================================="
echo "Summary"
echo "=================================================="
echo "Total files checked: $total_files"
echo -e "${RED}Files exceeding hard limit: $oversized_files${NC}"
echo -e "${YELLOW}Files with warnings: $warning_files${NC}"
echo ""

# Exit with failure if any files exceed hard limit
if [ "$oversized_files" -gt 0 ]; then
    echo -e "${RED}❌ VALIDATION FAILED${NC}"
    echo ""
    echo "Files exceeding the hard limit (100,000 chars / ~25,000 tokens):"
    echo "These files may cause performance issues or failures in Claude Code."
    echo ""
    echo "Recommended actions:"
    echo "  1. Refactor large files to reduce size"
    echo "  2. Move templates to separate files"
    echo "  3. Remove verbose examples and duplicate content"
    echo "  4. Extract common patterns to shared documentation"
    echo ""
    echo "See research/orchestrator-bloat-analysis.md for detailed guidance."
    echo ""
    exit 1
fi

if [ "$warning_files" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  WARNING${NC}"
    echo ""
    echo "Some files are approaching the size limit."
    echo "Consider refactoring before adding more content."
    echo ""
fi

echo -e "${GREEN}✅ All files within acceptable size limits${NC}"
exit 0
