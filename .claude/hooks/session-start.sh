#!/bin/bash
set -euo pipefail

# Only run in Claude Code Web environment
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
pyproject_configs = {Path(k).name for k in force_include.keys() if k.startswith("bazinga/") and k.endswith(".json")}

# Get ALLOWED_CONFIG_FILES from __init__.py
init_content = Path("src/bazinga_cli/__init__.py").read_text()
match = re.search(r"ALLOWED_CONFIG_FILES\s*=\s*\[(.*?)\]", init_content, re.DOTALL)
if match:
    allowed_configs = set(re.findall(r"\"([^\"]+\.json)\"", match.group(1)))
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
