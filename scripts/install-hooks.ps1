# Install git hooks for BAZINGA development (PowerShell)
# Run this after cloning the repository
#
# Usage: .\scripts\install-hooks.ps1

$ErrorActionPreference = "Stop"

$REPO_ROOT = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

# Save current location and change to repo root
Push-Location $REPO_ROOT
try {

Write-Host "🔧 Installing git hooks for BAZINGA development..."

# Verify we're in a git repository
if (-not (Test-Path ".git")) {
    Write-Host "  ❌ ERROR: Not a git repository. Run this from the repository root." -ForegroundColor Red
    exit 1
}

# Install pre-commit hook
$hookSource = "scripts\git-hooks\pre-commit"
$hookDest = ".git\hooks\pre-commit"

if (Test-Path $hookSource) {
    # Ensure hooks directory exists
    $hooksDir = ".git\hooks"
    if (-not (Test-Path $hooksDir)) {
        New-Item -ItemType Directory -Path $hooksDir -Force | Out-Null
    }

    # Read content and write with LF line endings (required for git hooks)
    $content = Get-Content $hookSource -Raw
    # Normalize line endings to LF only (git hooks require Unix line endings)
    $content = $content -replace "`r`n", "`n"
    # Write with UTF8 no BOM encoding
    [System.IO.File]::WriteAllText($hookDest, $content, [System.Text.UTF8Encoding]::new($false))

    # Make hook executable on Unix-like systems (required for git hooks to run)
    if ($IsLinux -or $IsMacOS -or (-not $env:OS -or $env:OS -notmatch "Windows")) {
        if (Get-Command "chmod" -ErrorAction SilentlyContinue) {
            & chmod +x $hookDest
            Write-Host "  ✅ Pre-commit hook installed (with LF line endings, executable)" -ForegroundColor Green
        }
        else {
            Write-Host "  ✅ Pre-commit hook installed (with LF line endings)" -ForegroundColor Green
            Write-Host "  ⚠️  Note: chmod not found. Manually run: chmod +x $hookDest" -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "  ✅ Pre-commit hook installed (with LF line endings)" -ForegroundColor Green
    }
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

} finally {
    # Restore original location
    Pop-Location
}
