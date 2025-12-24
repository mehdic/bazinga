#!/bin/bash
# BAZINGA Post-Compaction Recovery Hook
# Deployed by: bazinga install
#
# This hook fires after context compaction (compact|resume events).
# It checks if BAZINGA orchestration was in progress via database,
# then outputs the ENTIRE orchestrator file to restore all rules.
#
# Why database check (not transcript grep):
# - After compaction, transcript may be summarized and lose original content
# - Database session state persists across compaction
# - More reliable detection of active orchestration

# Don't use set -e because we want graceful fallback
set -uo pipefail

# Check if bazinga database exists with an active session
# This is more reliable than grepping transcript (which may be compacted)
if [ -f "bazinga/bazinga.db" ]; then
  active_session=$(python3 -c '
import sqlite3
try:
    conn = sqlite3.connect("bazinga/bazinga.db")
    cursor = conn.execute("SELECT session_id, status FROM sessions ORDER BY created_at DESC LIMIT 1")
    row = cursor.fetchone()
    if row and row[1] in ("active", "in_progress"):
        print(row[0])
    conn.close()
except:
    pass
' 2>/dev/null || echo "")

  if [ -n "$active_session" ]; then
    echo ""
    echo "================================================================================"
    echo "  BAZINGA POST-COMPACTION RECOVERY"
    echo "  Active session: $active_session"
    echo "================================================================================"
    echo ""
    echo "Context was compacted. Re-loading FULL orchestrator rules..."
    echo ""

    # Try to output the ENTIRE orchestrator file
    # This ensures ALL rules are restored, not just a summary
    if [ -f ".claude/commands/bazinga.orchestrate.md" ]; then
      echo "--- BEGIN ORCHESTRATOR RULES (from .claude/commands/bazinga.orchestrate.md) ---"
      echo ""
      cat ".claude/commands/bazinga.orchestrate.md"
      echo ""
      echo "--- END ORCHESTRATOR RULES ---"
    elif [ -f ".claude/agents/orchestrator.md" ]; then
      echo "--- BEGIN ORCHESTRATOR RULES (from .claude/agents/orchestrator.md) ---"
      echo ""
      cat ".claude/agents/orchestrator.md"
      echo ""
      echo "--- END ORCHESTRATOR RULES ---"
    else
      # Fallback: output critical axioms if files not found
      echo "WARNING: Orchestrator file not found. Critical axioms:"
      echo ""
      echo "1. I am a COORDINATOR - I spawn agents, I do not implement"
      echo "2. PM is the DECISION-MAKER - I never decide, only PM says BAZINGA"
      echo "3. Task() calls FOREGROUND ONLY - always run_in_background: false"
      echo "4. Parallel = concurrent FOREGROUND, NOT background mode"
      echo "5. Route via Skill(command: \"workflow-router\")"
    fi
    echo ""
    echo "================================================================================"
    echo ""
  fi
fi
