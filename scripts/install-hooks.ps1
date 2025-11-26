# Install git hooks for BAZINGA development (PowerShell)
# Run this after cloning the repository
#
# Usage: .\scripts\install-hooks.ps1

$ErrorActionPreference = "Stop"

$REPO_ROOT = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $REPO_ROOT

Write-Host "🔧 Installing git hooks for BAZINGA development..."

# Install pre-commit hook
$hookSource = "scripts\git-hooks\pre-commit"
$hookDest = ".git\hooks\pre-commit"

if (Test-Path $hookSource) {
    # Ensure hooks directory exists
    $hooksDir = ".git\hooks"
    if (-not (Test-Path $hooksDir)) {
        New-Item -ItemType Directory -Path $hooksDir -Force | Out-Null
    }

    Copy-Item $hookSource $hookDest -Force
    Write-Host "  ✅ Pre-commit hook installed" -ForegroundColor Green
}
else {
    Write-Host "  ❌ ERROR: Hook template not found at $hookSource" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ Git hooks installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "The pre-commit hook will automatically:"
Write-Host ""
Write-Host "  1. Orchestrator changes (agents\orchestrator.md):"
Write-Host "     - Validate §line and §Step references"
Write-Host "     - Rebuild .claude\commands\bazinga.orchestrate.md"
Write-Host "     - Stage the generated file"
Write-Host ""
Write-Host "  2. Agent source changes (agents\_sources\):"
Write-Host "     - Rebuild agents\developer.md (from developer.base.md)"
Write-Host "     - Rebuild agents\senior_software_engineer.md (base + delta)"
Write-Host "     - Stage the generated files"
Write-Host ""

# Note: On Windows, the pre-commit hook will be executed via Git Bash
# which is typically installed with Git for Windows
