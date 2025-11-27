#!/bin/bash
#
# Test Pattern Analysis Skill - Bash wrapper
#
# Analyzes test suite to find patterns, fixtures, naming conventions, and utilities.
#
# Usage:
#   ./analyze_tests.sh "tests/"
#   ./analyze_tests.sh "tests/" "Implement password reset"

set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check for required argument
if [ -z "$1" ]; then
    echo "Error: Test path required" >&2
    echo "Usage: $0 \"test_path\" [\"task_description\"]" >&2
    exit 1
fi

TEST_PATH="$1"
TASK_DESCRIPTION="${2:-}"

# Check if Python is available
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: Python is not installed or not in PATH" >&2
    exit 1
fi

# Run the Python script
if [ -n "$TASK_DESCRIPTION" ]; then
    exec "$PYTHON_CMD" "$SCRIPT_DIR/analyze_tests.py" "$TEST_PATH" "$TASK_DESCRIPTION"
else
    exec "$PYTHON_CMD" "$SCRIPT_DIR/analyze_tests.py" "$TEST_PATH"
fi
