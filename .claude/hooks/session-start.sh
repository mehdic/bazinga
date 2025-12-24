#!/bin/bash
set -euo pipefail

# === DEV MODE SETUP (runs in both local and remote) ===
# In dev mode (bazinga repo), templates are at root templates/
# but agent files reference bazinga/templates/ (for installed mode compatibility)
# Create symlink so both paths work
if [ -d "templates" ] && [ -d "bazinga" ] && [ ! -e "bazinga/templates" ]; then
  # We're in dev mode (bazinga repo) - create symlink
  ln -s ../templates bazinga/templates 2>/dev/null || true
  echo "🔗 Dev mode: Created bazinga/templates -> ../templates symlink"
fi

# Similarly, workflow configs are at root workflow/ in dev mode
# but code references bazinga/config/ (for installed mode compatibility)
if [ -d "workflow" ] && [ -d "bazinga" ] && [ ! -e "bazinga/config" ]; then
  # We're in dev mode (bazinga repo) - create symlink
  ln -s ../workflow bazinga/config 2>/dev/null || true
  echo "🔗 Dev mode: Created bazinga/config -> ../workflow symlink"
fi

# Only run remaining setup in Claude Code Web environment
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Load project context file at session start
if [ -f ".claude/claude.md" ]; then
  echo "📋 Loading project context from .claude/claude.md..."
  cat .claude/claude.md
  echo ""
  echo "✅ Project context loaded successfully!"
else
  echo "⚠️  Warning: .claude/claude.md not found"
fi

# Check config file sync (pyproject.toml vs ALLOWED_CONFIG_FILES)
if [ -f "pyproject.toml" ] && [ -f "src/bazinga_cli/__init__.py" ]; then
  # Quick sync check using Python
  python3 -c '
import tomllib
import re
from pathlib import Path

# Get force-include configs from pyproject.toml
with open("pyproject.toml", "rb") as f:
    pyproject = tomllib.load(f)
force_include = pyproject.get("tool", {}).get("hatch", {}).get("build", {}).get("targets", {}).get("wheel", {}).get("force-include", {})
pyproject_configs = {Path(k).name for k in force_include.keys() if k.startswith("bazinga/") and "templates" not in k}

# Get ALLOWED_CONFIG_FILES from __init__.py
init_content = Path("src/bazinga_cli/__init__.py").read_text()
match = re.search(r"ALLOWED_CONFIG_FILES\s*=\s*\[(.*?)\]", init_content, re.DOTALL)
if match:
    allowed_configs = set(re.findall(r"\"([^\"]+)\"", match.group(1)))
else:
    allowed_configs = set()

# Compare
if pyproject_configs != allowed_configs:
    missing_py = pyproject_configs - allowed_configs
    missing_toml = allowed_configs - pyproject_configs
    print("⚠️  CONFIG SYNC WARNING:")
    if missing_py:
        print(f"   Missing from ALLOWED_CONFIG_FILES: {missing_py}")
    if missing_toml:
        print(f"   Missing from pyproject.toml force-include: {missing_toml}")
    print("   Run: python -m pytest tests/test_config_sync.py -v")
' 2>/dev/null || true
fi

# Remind about research folder
if [ -d "research" ]; then
  echo ""
  echo "📚 Research documents available in 'research/' folder"
  echo "   Use these for historical context and past decisions"
fi

# 🔴 CRITICAL: Force orchestrator re-read after session resume/compaction
# If there's an active BAZINGA session, remind to re-read orchestrator rules
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
    echo "🔴 ACTIVE BAZINGA SESSION DETECTED: $active_session"
    echo ""
    echo "If resuming orchestration after context compaction, you MUST:"
    echo "1. Re-read: agents/orchestrator.md (or .claude/commands/bazinga.orchestrate.md)"
    echo "2. Verify identity axioms - especially:"
    echo "   - PM is the DECISION-MAKER (not you)"
    echo "   - All Task() calls use run_in_background: false"
    echo "   - Route via Skill(command: \"workflow-router\")"
    echo ""
    cat agents/orchestrator.md 2>/dev/null | head -40 || true
    echo ""
    echo "--- END OF ORCHESTRATOR IDENTITY AXIOMS ---"
  fi
fi
