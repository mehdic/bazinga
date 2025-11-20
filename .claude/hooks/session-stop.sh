#!/bin/bash
set -euo pipefail

# Session Stop Hook: AI-powered orchestrator reference validation
# Runs when Claude Code session ends
# Uses AI to intelligently check if references are broken or stale

ORCHESTRATOR_FILE="agents/orchestrator.md"

# Only run if orchestrator file exists
if [ ! -f "$ORCHESTRATOR_FILE" ]; then
  exit 0
fi

echo ""
echo "🔍 Session Stop: Checking if orchestrator was modified..."

# Check if orchestrator was modified during this session
MODIFIED=false

# Check for uncommitted changes (staged or unstaged)
if git diff --name-only HEAD "$ORCHESTRATOR_FILE" 2>/dev/null | grep -q "$ORCHESTRATOR_FILE"; then
  MODIFIED=true
  echo "  → Detected uncommitted changes to $ORCHESTRATOR_FILE"
elif git diff --name-only --cached "$ORCHESTRATOR_FILE" 2>/dev/null | grep -q "$ORCHESTRATOR_FILE"; then
  MODIFIED=true
  echo "  → Detected staged changes to $ORCHESTRATOR_FILE"
fi

# Check recent commits on current branch (last 5 commits)
if [ "$MODIFIED" = false ]; then
  RECENT_CHANGES=$(git log -5 --name-only --pretty=format: 2>/dev/null | grep -c "$ORCHESTRATOR_FILE" || true)
  if [ "$RECENT_CHANGES" -gt 0 ]; then
    MODIFIED=true
    echo "  → Detected $RECENT_CHANGES commit(s) modifying $ORCHESTRATOR_FILE in recent history"
  fi
fi

if [ "$MODIFIED" = false ]; then
  echo "  ✅ No modifications to orchestrator detected - skipping validation"
  exit 0
fi

# Orchestrator was modified - trigger AI validation
echo ""
echo "⚠️  Orchestrator was modified during this session!"
echo "🤖 Triggering AI-powered reference validation..."
echo ""
echo "The AI will:"
echo "  1. Read agents/orchestrator.md completely"
echo "  2. Extract all §line and §Step references"
echo "  3. Verify each reference points to correct content"
echo "  4. Detect stale references (technically valid but semantically wrong)"
echo "  5. Report any issues found"
echo ""
echo "---"
echo ""

# Create a marker file to signal that AI validation should run
# The AI assistant will detect this and perform validation
mkdir -p .claude/session-stop-checks
echo "orchestrator-references" > .claude/session-stop-checks/validate-orchestrator.txt

# Output a clear message for the AI to see
cat << 'EOF'
🤖 AI VALIDATION REQUIRED:

Please perform intelligent validation of orchestrator references:

**Your task:**
1. Read `agents/orchestrator.md` in full
2. Find ALL references in these formats:
   - `§line XXXX` or `§line XXXX (keyword)`
   - `§Step X.Y` or `§Step X.Y.Z`
3. For EACH reference found:
   - Verify the line number exists and points to correct content
   - Check if the keyword (if present) matches the actual content
   - Verify §Step references point to actual section headers
   - Detect if reference is STALE (points to wrong content even if line exists)
4. Report findings:
   - ✅ Valid references (only if all pass)
   - ⚠️ Stale references (technically valid but semantically wrong)
   - ❌ Broken references (line doesn't exist or completely wrong)

**Example of stale reference:**
- Reference says: `§line 146 (Query task groups)`
- Line 146 contains: `- Increment iteration counter`
- This is STALE (wrong content) even though line exists

**Do NOT just run the validation script - that already failed to detect issues.**
**You must READ the file and CHECK each reference intelligently.**

After validation, delete the marker file:
`rm -rf .claude/session-stop-checks`

EOF

exit 0
