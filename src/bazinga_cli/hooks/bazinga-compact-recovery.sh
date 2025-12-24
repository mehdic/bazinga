#!/bin/bash
# BAZINGA Post-Compaction Recovery Hook
# Deployed by: bazinga install
#
# This hook fires after context compaction (compact|resume events).
# It checks if orchestration was in progress, then outputs the FULL
# orchestrator command file to restore all rules.

set -euo pipefail

# Read hook input from stdin
HOOK_INPUT=$(cat)

# Extract fields from JSON input using python (jq may not be installed)
read -r TRANSCRIPT_PATH PROJECT_CWD < <(echo "$HOOK_INPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data.get('transcript_path', ''), data.get('cwd', ''))
" 2>/dev/null || echo "")

# Exit silently if no transcript path
if [ -z "$TRANSCRIPT_PATH" ] || [ ! -f "$TRANSCRIPT_PATH" ]; then
  exit 0
fi

# Exit silently if no cwd (can't find orchestrator file)
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

# Orchestration was in progress - output the FULL orchestrator command
echo ""
echo "================================================================================"
echo "  BAZINGA POST-COMPACTION RECOVERY"
echo "  Reloading FULL orchestrator command..."
echo "  Project: $PROJECT_CWD"
echo "================================================================================"
echo ""

# Output the entire orchestrator command file
if [ -f "$ORCHESTRATOR_CMD" ]; then
  cat "$ORCHESTRATOR_CMD"
elif [ -f "$ORCHESTRATOR_AGENT" ]; then
  cat "$ORCHESTRATOR_AGENT"
else
  echo "ERROR: Orchestrator file not found!"
  echo "Checked: $ORCHESTRATOR_CMD"
  echo "Checked: $ORCHESTRATOR_AGENT"
  exit 1
fi

echo ""
echo "================================================================================"
echo "  END OF ORCHESTRATOR COMMAND - RULES RESTORED"
echo "================================================================================"
echo ""
