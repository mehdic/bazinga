#!/bin/bash
# discover-speckit.sh - Discover SpecKit features in .specify directory
# Usage: discover-speckit.sh
#
# Returns JSON with discovered features for orchestrator consumption
# Compliant with orchestrator §Bash Command Allowlist

set -e

SPECIFY_DIR=".specify/features"

# Check if .specify/features exists
if [ ! -d "$SPECIFY_DIR" ]; then
    echo '{"speckit_available": false, "features": [], "reason": "no .specify/features directory"}'
    exit 0
fi

# Find feature directories (those containing tasks.md)
FEATURES=()
for dir in "$SPECIFY_DIR"/*/; do
    if [ -d "$dir" ] && [ -f "${dir}tasks.md" ]; then
        # Extract just the feature name (last component of path)
        feature_name=$(basename "$dir")
        FEATURES+=("\"$feature_name\"")
    fi
done

# Count features
FEATURE_COUNT=${#FEATURES[@]}

if [ $FEATURE_COUNT -eq 0 ]; then
    echo '{"speckit_available": false, "features": [], "reason": "no valid features found (need tasks.md)"}'
    exit 0
fi

# Build JSON array
FEATURES_JSON=$(IFS=,; echo "[${FEATURES[*]}]")

# Output JSON result
cat << EOF
{
  "speckit_available": true,
  "feature_count": $FEATURE_COUNT,
  "features": $FEATURES_JSON,
  "base_dir": "$SPECIFY_DIR"
}
EOF

exit 0
