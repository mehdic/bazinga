#!/bin/bash
#
# Build script for generating slash commands from agent source files
# This maintains single-source-of-truth while allowing inline execution
#
# Usage: ./scripts/build-slash-commands.sh

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "🔨 Building slash commands from agent sources..."

# -----------------------------------------------------------------------------
# 1. Build bazinga.orchestrate.md from agents/orchestrator.md
# -----------------------------------------------------------------------------

echo "  → Building .claude/commands/bazinga.orchestrate.md"

# Read the orchestrator agent file
ORCHESTRATOR_CONTENT=$(cat agents/orchestrator.md)

# Extract frontmatter from orchestrator
DESCRIPTION=$(echo "$ORCHESTRATOR_CONTENT" | awk '/^description:/ {$1=""; print substr($0,2); exit}')
NAME=$(echo "$ORCHESTRATOR_CONTENT" | awk '/^name:/ {print $2; exit}')

# Remove frontmatter from content (everything between --- markers)
ORCHESTRATOR_BODY=$(echo "$ORCHESTRATOR_CONTENT" | awk '
  BEGIN { in_frontmatter=0; found_first=0 }
  /^---$/ {
    if (!found_first) {
      in_frontmatter=1; found_first=1; next
    } else if (in_frontmatter) {
      in_frontmatter=0; next
    }
  }
  !in_frontmatter { print }
')

# Generate the slash command file
cat > .claude/commands/bazinga.orchestrate.md <<EOF
---
name: $NAME
description: $DESCRIPTION
---

$ORCHESTRATOR_BODY
EOF

echo "  ✅ bazinga.orchestrate.md built successfully"

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------

echo ""
echo "✅ Slash commands built successfully!"
echo ""
echo "Generated files:"
echo "  - .claude/commands/bazinga.orchestrate.md (from agents/orchestrator.md)"
echo ""
echo "Note: orchestrate-advanced uses embedded prompts and doesn't need building"
