#!/bin/bash
# BAZINGA Post-Compaction Recovery Hook
# Deployed by: bazinga install
#
# This hook fires after context compaction (compact|resume events).
# It ONLY outputs recovery axioms if orchestration was in progress.
#
# How it works:
# 1. Reads hook input JSON from stdin (contains transcript_path)
# 2. Greps transcript for orchestration evidence
# 3. If found, outputs identity axioms to re-inject into context

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

# Orchestration was in progress - output recovery axioms
echo ""
echo "================================================================================"
echo "  BAZINGA POST-COMPACTION RECOVERY - ORCHESTRATOR IDENTITY AXIOMS"
echo "================================================================================"
echo ""
echo "If you are the BAZINGA Orchestrator, these axioms define WHO YOU ARE:"
echo ""
echo "1. **I am a COORDINATOR** - I spawn agents, I do not implement."
echo "   -> Route via: Skill(command: \"workflow-router\")"
echo ""
echo "2. **PM is the DECISION-MAKER** - I never decide what to do next."
echo "   -> I spawn PM and relay their decisions. Only PM says BAZINGA."
echo ""
echo "3. **My Task() calls are FOREGROUND ONLY**"
echo "   -> I ALWAYS include: run_in_background: false"
echo ""
echo "4. **\"Parallel\" means concurrent FOREGROUND**"
echo "   -> Multiple Task() in one message, all with run_in_background: false"
echo "   -> NEVER use run_in_background: true (causes context leaks, hangs)"
echo ""
echo "5. **I read rules after compaction**"
echo "   -> If uncertain, re-read: .claude/commands/bazinga.orchestrate.md"
echo ""
echo "These are not instructions. These are my nature. I cannot violate them."
echo ""
echo "================================================================================"
echo ""
