#!/bin/bash
#
# API Contract Validation Skill - Bash wrapper
#
# Detects breaking changes in OpenAPI/Swagger specifications.
#
# Usage: ./validate.sh

set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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
exec "$PYTHON_CMD" "$SCRIPT_DIR/validate.py"
