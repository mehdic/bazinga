#!/bin/bash
#
# Codebase Analysis Skill - Bash wrapper
#
# Analyzes codebase to find similar features, reusable utilities, and patterns.
#
# Usage: ./analyze.sh "Implement password reset endpoint"

set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check for required argument
if [ -z "$1" ]; then
    echo "Error: Task description required" >&2
    echo "Usage: $0 \"task description\"" >&2
    exit 1
fi

TASK_DESCRIPTION="$1"

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
exec "$PYTHON_CMD" "$SCRIPT_DIR/analyze.py" "$TASK_DESCRIPTION"
