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
    # Cross-platform Python detection (handles py -3 launcher on Windows)
    $pythonCmd = $null
    if (Get-Command "python3" -ErrorAction SilentlyContinue) {
        $pythonCmd = @("python3")
    } elseif (Get-Command "python" -ErrorAction SilentlyContinue) {
        $version = & python --version 2>&1
        if ($version -match "Python 3") { $pythonCmd = @("python") }
    } elseif (Get-Command "py" -ErrorAction SilentlyContinue) {
        $pythonCmd = @("py", "-3")
    }

    if ($pythonCmd) {
        try {
            & $pythonCmd[0] @($pythonCmd[1..99] | Where-Object { $_ }) -c @'
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
    allowed_configs = set(re.findall(r"['\"]([^'\"]+)['\"]", match.group(1)))
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

# Setup GitHub token for PR automation (if env var is set)
$tokenFile = Join-Path $HOME ".bazinga-github-token"
if (-not (Test-Path $tokenFile)) {
    if ($env:BAZINGA_GITHUB_TOKEN) {
        # Create token file from environment variable
        $env:BAZINGA_GITHUB_TOKEN | Out-File -FilePath $tokenFile -Encoding ASCII -NoNewline
        # Set permissions (Unix only)
        if (Get-Command "chmod" -ErrorAction SilentlyContinue) {
            & chmod 600 $tokenFile
        }
        Write-Host "🔑 GitHub token configured from environment variable"
    }
    else {
        Write-Host ""
        Write-Host "⚠️  GitHub PR automation not configured" -ForegroundColor Yellow
        Write-Host "   Set BAZINGA_GITHUB_TOKEN env var or create ~/.bazinga-github-token"
    }
}

# Remind about research folder
if (Test-Path "research") {
    Write-Host ""
    Write-Host "📚 Research documents available in 'research/' folder"
    Write-Host "   Use these for historical context and past decisions"
}
