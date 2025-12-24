#!/bin/bash
# BAZINGA Post-Compaction Recovery Hook
# Deployed by: bazinga install
#
# This hook fires after context compaction (compact|resume events).
# It checks if orchestration was in progress, then outputs the
# IDENTITY AXIOMS section (not full file to avoid token blow-up).

set -uo pipefail
# Note: No -e flag - we want soft failures (exit 0) to not break sessions

# Read hook input from stdin
HOOK_INPUT=$(cat)

# Extract fields from JSON input using python (jq may not be installed)
read -r TRANSCRIPT_PATH PROJECT_CWD < <(echo "$HOOK_INPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data.get('transcript_path', ''), data.get('cwd', ''))
" 2>/dev/null || echo "")

# Exit silently if no transcript path (soft fail)
if [ -z "$TRANSCRIPT_PATH" ] || [ ! -f "$TRANSCRIPT_PATH" ]; then
  exit 0
fi

# Exit silently if no cwd (soft fail)
if [ -z "$PROJECT_CWD" ]; then
  exit 0
fi

# Check if orchestration was in progress
# Look for evidence of /bazinga.orchestrate command or orchestrator activity
if ! grep -q -E "bazinga\.orchestrate|ORCHESTRATOR|orchestrator\.md|§ORCHESTRATOR IDENTITY AXIOMS" "$TRANSCRIPT_PATH" 2>/dev/null; then
  # No orchestration evidence - exit silently
  exit 0
fi

# Build absolute paths to orchestrator files
ORCHESTRATOR_CMD="$PROJECT_CWD/.claude/commands/bazinga.orchestrate.md"
ORCHESTRATOR_AGENT="$PROJECT_CWD/.claude/agents/orchestrator.md"

# Find the orchestrator file
ORCHESTRATOR_FILE=""
if [ -f "$ORCHESTRATOR_CMD" ]; then
  ORCHESTRATOR_FILE="$ORCHESTRATOR_CMD"
elif [ -f "$ORCHESTRATOR_AGENT" ]; then
  ORCHESTRATOR_FILE="$ORCHESTRATOR_AGENT"
fi

# Soft fail if file not found (don't break session)
if [ -z "$ORCHESTRATOR_FILE" ]; then
  echo ""
  echo "⚠️  BAZINGA: Orchestrator file not found for recovery."
  echo "   If you are the orchestrator, manually read: .claude/agents/orchestrator.md"
  exit 0  # Soft fail - don't break session
fi

# Output ONLY the identity axioms section (not full file to avoid token blow-up)
# Extract first ~50 lines which contain the axioms, or up to the first major section
echo ""
echo "================================================================================"
echo "  BAZINGA POST-COMPACTION RECOVERY"
echo "  Re-injecting identity axioms (not full file to save tokens)..."
echo "================================================================================"
echo ""

# Output the identity axioms section (first ~50 lines containing the critical rules)
head -60 "$ORCHESTRATOR_FILE"

echo ""
echo "================================================================================"
echo "  IDENTITY AXIOMS RESTORED"
echo "  For full rules, read: .claude/agents/orchestrator.md"
echo "================================================================================"
echo ""

exit 0
