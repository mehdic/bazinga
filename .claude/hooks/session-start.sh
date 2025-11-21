#!/bin/bash
set -euo pipefail

# Only run in Claude Code Web environment
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# DISABLED: Load project context file at session start
# User requested to disable claude.md loading for now (2025-11-21)
# if [ -f ".claude/claude.md" ]; then
#   echo "📋 Loading project context from .claude/claude.md..."
#   cat .claude/claude.md
#   echo ""
#   echo "✅ Project context loaded successfully!"
# else
#   echo "⚠️  Warning: .claude/claude.md not found"
# fi

# Remind about research folder
if [ -d "research" ]; then
  echo "📚 Research documents available in 'research/' folder"
  echo "   Use these for historical context and past decisions"
fi
