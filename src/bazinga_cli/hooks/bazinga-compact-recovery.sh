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

# Extract transcript path from JSON input
# Use python as jq may not be installed on all systems
TRANSCRIPT_PATH=$(echo "$HOOK_INPUT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('transcript_path', ''))" 2>/dev/null || echo "")

# Exit silently if no transcript path
if [ -z "$TRANSCRIPT_PATH" ] || [ ! -f "$TRANSCRIPT_PATH" ]; then
  exit 0
fi

# Check if orchestration was in progress
# Look for evidence of /bazinga.orchestrate command or orchestrator activity
if ! grep -q -E "bazinga\.orchestrate|ORCHESTRATOR|orchestrator\.md|§ORCHESTRATOR IDENTITY AXIOMS" "$TRANSCRIPT_PATH" 2>/dev/null; then
  # No orchestration evidence - exit silently
  exit 0
fi

# Orchestration was in progress - output the FULL orchestrator command
echo ""
echo "================================================================================"
echo "  BAZINGA POST-COMPACTION RECOVERY"
echo "  Reloading FULL orchestrator command..."
echo "================================================================================"
echo ""

# Output the entire orchestrator command file
if [ -f ".claude/commands/bazinga.orchestrate.md" ]; then
  cat ".claude/commands/bazinga.orchestrate.md"
elif [ -f ".claude/agents/orchestrator.md" ]; then
  cat ".claude/agents/orchestrator.md"
else
  echo "ERROR: Orchestrator file not found!"
  echo "Expected: .claude/commands/bazinga.orchestrate.md"
  exit 1
fi

echo ""
echo "================================================================================"
echo "  END OF ORCHESTRATOR COMMAND - RULES RESTORED"
echo "================================================================================"
echo ""
