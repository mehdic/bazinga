#!/usr/bin/env pwsh
# Session Start Hook (PowerShell)
# Only run in Claude Code Web environment

$ErrorActionPreference = "Continue"

# Only run in Claude Code Web environment
if ($env:CLAUDE_CODE_REMOTE -ne "true") {
    exit 0
}

# Load project context file at session start
if (Test-Path ".claude\claude.md") {
    Write-Host "📋 Loading project context from .claude\claude.md..."
    Get-Content ".claude\claude.md"
    Write-Host ""
    Write-Host "✅ Project context loaded successfully!"
}
else {
    Write-Host "⚠️  Warning: .claude\claude.md not found" -ForegroundColor Yellow
}

# Check config file sync (pyproject.toml vs ALLOWED_CONFIG_FILES)
if ((Test-Path "pyproject.toml") -and (Test-Path "src\bazinga_cli\__init__.py")) {
    # Quick sync check using Python (with tomllib/tomli fallback for Python 3.9/3.10)
    # Detect Python command
    $pythonCmd = if (Get-Command "python3" -ErrorAction SilentlyContinue) { "python3" }
                 elseif (Get-Command "python" -ErrorAction SilentlyContinue) { "python" }
                 else { $null }

    if ($pythonCmd) {
        try {
            & $pythonCmd -c @'
import re
from pathlib import Path

# Try tomllib (Python 3.11+), fall back to tomli (Python 3.9/3.10)
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        # Neither available, skip sync check
        exit(0)

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
'@ 2>$null
        }
        catch {
            # Ignore errors silently
        }
    }
}

# Remind about research folder
if (Test-Path "research") {
    Write-Host ""
    Write-Host "📚 Research documents available in 'research/' folder"
    Write-Host "   Use these for historical context and past decisions"
}
