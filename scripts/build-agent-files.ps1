# Build Agent Files (PowerShell)
#
# Generates agent files from sources:
#   - developer.md = copy of _sources/developer.base.md
#   - senior_software_engineer.md = _sources/developer.base.md + _sources/senior.delta.md
#
# Usage:
#   .\scripts\build-agent-files.ps1 [--check]
#
# Options:
#   --check   Only verify files are up to date, don't modify (for CI)

param(
    [switch]$Check
)

$ErrorActionPreference = "Stop"

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_ROOT = Split-Path -Parent $SCRIPT_DIR
$SOURCES_DIR = Join-Path $PROJECT_ROOT "agents\_sources"
$OUTPUT_DIR = Join-Path $PROJECT_ROOT "agents"

# Cross-platform Python detection
# Returns array: first element is executable, rest are arguments
function Get-PythonCommand {
    # Try python3 first (Unix/macOS, some Windows)
    if (Get-Command "python3" -ErrorAction SilentlyContinue) {
        return @("python3")
    }
    # Try python (Windows default)
    if (Get-Command "python" -ErrorAction SilentlyContinue) {
        # Verify it's Python 3
        $version = & python --version 2>&1
        if ($version -match "Python 3") {
            return @("python")
        }
    }
    # Try py launcher (Windows Python launcher)
    # Note: py and -3 must be separate to work with call operator
    if (Get-Command "py" -ErrorAction SilentlyContinue) {
        return @("py", "-3")
    }
    return $null
}

# Helper to invoke Python with correct arguments
function Invoke-Python {
    param([Parameter(ValueFromRemainingArguments)]$Arguments)
    & $script:PYTHON_CMD[0] @($script:PYTHON_CMD[1..99]) @Arguments
}

$script:PYTHON_CMD = Get-PythonCommand
if (-not $script:PYTHON_CMD) {
    Write-Host "Error: Python 3 not found. Install Python 3 and ensure it's in PATH." -ForegroundColor Red
    exit 1
}

# Verify source files exist
if (-not (Test-Path (Join-Path $SOURCES_DIR "developer.base.md"))) {
    Write-Host "Error: Source file not found: $SOURCES_DIR\developer.base.md" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path (Join-Path $SOURCES_DIR "senior.delta.md"))) {
    Write-Host "Error: Delta file not found: $SOURCES_DIR\senior.delta.md" -ForegroundColor Red
    exit 1
}

Write-Host "Building agent files..."
Write-Host "  Source directory: $SOURCES_DIR"
Write-Host "  Output directory: $OUTPUT_DIR"
Write-Host ""

if ($Check) {
    Write-Host "Running in CHECK mode (no files will be modified)" -ForegroundColor Yellow
    Write-Host ""

    # Create temp directory for generated files
    $TEMP_DIR = Join-Path ([System.IO.Path]::GetTempPath()) "bazinga-build-$(Get-Date -Format 'yyyyMMddHHmmss')"
    New-Item -ItemType Directory -Path $TEMP_DIR -Force | Out-Null

    try {
        # Generate to temp location
        Copy-Item (Join-Path $SOURCES_DIR "developer.base.md") (Join-Path $TEMP_DIR "developer.md")

        $mergeScript = Join-Path $SCRIPT_DIR "merge_agent_delta.py"
        Invoke-Python $mergeScript `
            (Join-Path $SOURCES_DIR "developer.base.md") `
            (Join-Path $SOURCES_DIR "senior.delta.md") `
            (Join-Path $TEMP_DIR "senior_software_engineer.md")

        # Compare with existing files
        $Failed = $false

        Write-Host "Checking developer.md..."
        $tempDev = Get-Content (Join-Path $TEMP_DIR "developer.md") -Raw
        $existingDev = Get-Content (Join-Path $OUTPUT_DIR "developer.md") -Raw -ErrorAction SilentlyContinue
        if ($tempDev -eq $existingDev) {
            Write-Host "  ✓ developer.md is up to date" -ForegroundColor Green
        }
        else {
            Write-Host "  ✗ developer.md is OUT OF DATE" -ForegroundColor Red
            Write-Host "    Run '.\scripts\build-agent-files.ps1' to regenerate"
            $Failed = $true
        }

        Write-Host "Checking senior_software_engineer.md..."
        $tempSenior = Get-Content (Join-Path $TEMP_DIR "senior_software_engineer.md") -Raw
        $existingSenior = Get-Content (Join-Path $OUTPUT_DIR "senior_software_engineer.md") -Raw -ErrorAction SilentlyContinue
        if ($tempSenior -eq $existingSenior) {
            Write-Host "  ✓ senior_software_engineer.md is up to date" -ForegroundColor Green
        }
        else {
            Write-Host "  ✗ senior_software_engineer.md is OUT OF DATE" -ForegroundColor Red
            Write-Host "    Run '.\scripts\build-agent-files.ps1' to regenerate"
            $Failed = $true
        }

        Write-Host ""
        if ($Failed) {
            Write-Host "Agent files are out of sync with sources!" -ForegroundColor Red
            Write-Host ""
            Write-Host "==================== FIX INSTRUCTIONS ====================" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "To fix, run locally:"
            Write-Host "  .\scripts\build-agent-files.ps1"
            Write-Host "  git add agents\developer.md agents\senior_software_engineer.md"
            Write-Host "  git commit --amend --no-edit"
            Write-Host ""
            Write-Host "Or install the pre-commit hook to auto-rebuild:"
            Write-Host "  .\scripts\install-hooks.ps1"
            Write-Host ""
            exit 1
        }
        else {
            Write-Host "All agent files are up to date." -ForegroundColor Green
            exit 0
        }
    }
    finally {
        Remove-Item -Path $TEMP_DIR -Recurse -Force -ErrorAction SilentlyContinue
    }
}
else {
    # Generate developer.md (direct copy)
    Write-Host "Generating developer.md..."
    Copy-Item (Join-Path $SOURCES_DIR "developer.base.md") (Join-Path $OUTPUT_DIR "developer.md") -Force
    Write-Host "  ✓ Generated developer.md" -ForegroundColor Green

    # Generate senior_software_engineer.md (base + delta)
    Write-Host "Generating senior_software_engineer.md..."
    $mergeScript = Join-Path $SCRIPT_DIR "merge_agent_delta.py"
    Invoke-Python $mergeScript `
        (Join-Path $SOURCES_DIR "developer.base.md") `
        (Join-Path $SOURCES_DIR "senior.delta.md") `
        (Join-Path $OUTPUT_DIR "senior_software_engineer.md")
    Write-Host "  ✓ Generated senior_software_engineer.md" -ForegroundColor Green

    Write-Host ""
    Write-Host "Agent files built successfully!" -ForegroundColor Green

    # Show file sizes for verification
    Write-Host ""
    Write-Host "File sizes:"
    $devLines = (Get-Content (Join-Path $OUTPUT_DIR "developer.md")).Count
    $seniorLines = (Get-Content (Join-Path $OUTPUT_DIR "senior_software_engineer.md")).Count
    Write-Host "  developer.md:              $devLines lines"
    Write-Host "  senior_software_engineer.md: $seniorLines lines"
}
