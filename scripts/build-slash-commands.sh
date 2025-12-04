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

SOURCE_FILE="agents/orchestrator.md"
TARGET_FILE=".claude/commands/bazinga.orchestrate.md"
TEMP_FILE=$(mktemp)

# Cleanup temp file on exit
trap "rm -f $TEMP_FILE" EXIT

# Validate source file exists
if [ ! -f "$SOURCE_FILE" ]; then
    echo "  ❌ ERROR: Source file not found: $SOURCE_FILE"
    exit 1
fi

# Extract frontmatter values using more robust AWK
# Only processes the FIRST frontmatter block (between first two --- markers)
# NOTE: We only extract 'description' for slash commands
# The 'name' field is for agent definitions, NOT slash commands
DESCRIPTION=$(awk '
  BEGIN { fm_count=0; in_fm=0 }
  /^---$/ {
    fm_count++
    if (fm_count == 1) { in_fm=1; next }
    if (fm_count == 2) { exit }
  }
  in_fm && /^description:/ {
    sub(/^description:[ \t]*/, "")
    print
    exit
  }
' "$SOURCE_FILE")

# Validate frontmatter was extracted
if [ -z "$DESCRIPTION" ]; then
    echo "  ❌ ERROR: Could not extract 'description' from frontmatter in $SOURCE_FILE"
    exit 1
fi

# Extract body (everything after second --- marker)
# More robust: counts --- markers and only takes content after second one
ORCHESTRATOR_BODY=$(awk '
  BEGIN { fm_count=0; in_fm=0; body_started=0 }
  /^---$/ {
    fm_count++
    if (fm_count == 1) { in_fm=1; next }
    if (fm_count == 2) { in_fm=0; body_started=1; next }
  }
  body_started { print }
' "$SOURCE_FILE")

# Validate body was extracted
if [ -z "$ORCHESTRATOR_BODY" ]; then
    echo "  ❌ ERROR: Could not extract body content from $SOURCE_FILE"
    echo "  Make sure file has proper frontmatter structure:"
    echo "  ---"
    echo "  name: orchestrator"
    echo "  description: ..."
    echo "  ---"
    echo "  <body content>"
    exit 1
fi

# Generate the slash command file to temp location (atomic write)
# NOTE: Slash commands only need 'description' in frontmatter
# DO NOT include 'name' - that's for agent definitions only
cat > "$TEMP_FILE" <<EOF
---
description: $DESCRIPTION
---

$ORCHESTRATOR_BODY
EOF

# -----------------------------------------------------------------------------
# Validation checks
# -----------------------------------------------------------------------------

echo "  → Validating generated file..."

# Check 1: File was created and is not empty
if [ ! -s "$TEMP_FILE" ]; then
    echo "  ❌ ERROR: Generated file is empty"
    exit 1
fi

# Check 2: Validate frontmatter structure
# Extract only the frontmatter section (between first two --- markers)
FRONTMATTER=$(awk '
  BEGIN { fm_count=0; in_fm=0 }
  /^---$/ {
    fm_count++
    if (fm_count == 1) { in_fm=1; next }
    if (fm_count == 2) { exit }
  }
  in_fm { print }
' "$TEMP_FILE")

# Check 2a: Frontmatter must contain description
if ! echo "$FRONTMATTER" | grep -q "^description:"; then
    echo "  ❌ ERROR: Generated file missing description in frontmatter"
    exit 1
fi

# Check 2b: Frontmatter must NOT contain 'name:' (that's for agents, not commands)
# NOTE: Only checks frontmatter section to avoid false positives from body content
if echo "$FRONTMATTER" | grep -q "^name:"; then
    echo "  ❌ ERROR: Generated slash command should NOT have 'name:' in frontmatter"
    echo "  'name:' is for agent definitions, not slash commands"
    exit 1
fi

# Check 3: File contains orchestrator content
if ! grep -q "ORCHESTRATOR" "$TEMP_FILE"; then
    echo "  ❌ ERROR: Generated file missing ORCHESTRATOR content"
    exit 1
fi

# Check 4: File is reasonably sized (orchestrator core should be ~1400+ lines)
# Note: Phase 2A/2B extracted to templates, reducing core from ~2600 to ~1500
LINE_COUNT=$(wc -l < "$TEMP_FILE")
if [ "$LINE_COUNT" -lt 1400 ]; then
    echo "  ❌ ERROR: Generated file too small ($LINE_COUNT lines, expected 1400+)"
    echo "  This suggests content was not properly extracted"
    exit 1
fi

echo "  ✅ Validation passed ($LINE_COUNT lines)"

# Only move to final location if all validations passed
mv "$TEMP_FILE" "$TARGET_FILE"

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
