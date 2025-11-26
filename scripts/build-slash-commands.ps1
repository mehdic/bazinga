# Build script for generating slash commands from agent source files (PowerShell)
# This maintains single-source-of-truth while allowing inline execution
#
# Usage: .\scripts\build-slash-commands.ps1

$ErrorActionPreference = "Stop"

$REPO_ROOT = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

# Save current location and change to repo root
Push-Location $REPO_ROOT
try {

Write-Host "🔨 Building slash commands from agent sources..."

# -----------------------------------------------------------------------------
# 1. Build bazinga.orchestrate.md from agents/orchestrator.md
# -----------------------------------------------------------------------------

Write-Host "  → Building .claude\commands\bazinga.orchestrate.md"

$SOURCE_FILE = "agents\orchestrator.md"
$TARGET_FILE = ".claude\commands\bazinga.orchestrate.md"

# Validate source file exists
if (-not (Test-Path $SOURCE_FILE)) {
    Write-Host "  ❌ ERROR: Source file not found: $SOURCE_FILE" -ForegroundColor Red
    exit 1
}

$content = Get-Content $SOURCE_FILE -Raw
$lines = Get-Content $SOURCE_FILE

# Find frontmatter boundaries
$fmStart = -1
$fmEnd = -1
for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -eq "---") {
        if ($fmStart -eq -1) {
            $fmStart = $i
        }
        elseif ($fmEnd -eq -1) {
            $fmEnd = $i
            break
        }
    }
}

if ($fmStart -eq -1 -or $fmEnd -eq -1) {
    Write-Host "  ❌ ERROR: Could not find frontmatter in $SOURCE_FILE" -ForegroundColor Red
    exit 1
}

# Extract frontmatter values
$NAME = ""
$DESCRIPTION = ""
for ($i = $fmStart + 1; $i -lt $fmEnd; $i++) {
    if ($lines[$i] -match "^name:\s*(.+)$") {
        $NAME = $matches[1].Trim()
    }
    if ($lines[$i] -match "^description:\s*(.+)$") {
        $DESCRIPTION = $matches[1].Trim()
    }
}

if ([string]::IsNullOrEmpty($NAME)) {
    Write-Host "  ❌ ERROR: Could not extract 'name' from frontmatter in $SOURCE_FILE" -ForegroundColor Red
    exit 1
}

if ([string]::IsNullOrEmpty($DESCRIPTION)) {
    Write-Host "  ❌ ERROR: Could not extract 'description' from frontmatter in $SOURCE_FILE" -ForegroundColor Red
    exit 1
}

# Extract body (everything after second --- marker)
$ORCHESTRATOR_BODY = ($lines[($fmEnd + 1)..($lines.Count - 1)]) -join "`n"

if ([string]::IsNullOrEmpty($ORCHESTRATOR_BODY)) {
    Write-Host "  ❌ ERROR: Could not extract body content from $SOURCE_FILE" -ForegroundColor Red
    exit 1
}

# Generate the slash command file
$output = @"
---
name: $NAME
description: $DESCRIPTION
---

$ORCHESTRATOR_BODY
"@

# Write to temp file first
$TEMP_FILE = [System.IO.Path]::GetTempFileName()
Set-Content -Path $TEMP_FILE -Value $output -Encoding UTF8

# -----------------------------------------------------------------------------
# Validation checks
# -----------------------------------------------------------------------------

Write-Host "  → Validating generated file..."

$tempContent = Get-Content $TEMP_FILE -Raw

# Check 1: File was created and is not empty
if ([string]::IsNullOrEmpty($tempContent)) {
    Write-Host "  ❌ ERROR: Generated file is empty" -ForegroundColor Red
    Remove-Item $TEMP_FILE -ErrorAction SilentlyContinue
    exit 1
}

# Check 2: File contains required frontmatter (relaxed - just check name field exists)
if ($tempContent -notmatch "(?m)^name:") {
    Write-Host "  ❌ ERROR: Generated file missing 'name' in frontmatter" -ForegroundColor Red
    Remove-Item $TEMP_FILE -ErrorAction SilentlyContinue
    exit 1
}

if ($tempContent -notmatch "description:") {
    Write-Host "  ❌ ERROR: Generated file missing description in frontmatter" -ForegroundColor Red
    Remove-Item $TEMP_FILE -ErrorAction SilentlyContinue
    exit 1
}

# Check 3: File contains orchestrator content
if ($tempContent -notmatch "ORCHESTRATOR") {
    Write-Host "  ❌ ERROR: Generated file missing ORCHESTRATOR content" -ForegroundColor Red
    Remove-Item $TEMP_FILE -ErrorAction SilentlyContinue
    exit 1
}

# Check 4: File is reasonably sized (orchestrator should be ~2600+ lines)
$LINE_COUNT = (Get-Content $TEMP_FILE).Count
if ($LINE_COUNT -lt 2000) {
    Write-Host "  ❌ ERROR: Generated file too small ($LINE_COUNT lines, expected 2600+)" -ForegroundColor Red
    Write-Host "  This suggests content was not properly extracted"
    Remove-Item $TEMP_FILE -ErrorAction SilentlyContinue
    exit 1
}

Write-Host "  ✅ Validation passed ($LINE_COUNT lines)" -ForegroundColor Green

# Move to final location
Move-Item -Path $TEMP_FILE -Destination $TARGET_FILE -Force

Write-Host "  ✅ bazinga.orchestrate.md built successfully" -ForegroundColor Green

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------

Write-Host ""
Write-Host "✅ Slash commands built successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Generated files:"
Write-Host "  - .claude\commands\bazinga.orchestrate.md (from agents\orchestrator.md)"
Write-Host ""
Write-Host "Note: orchestrate-advanced uses embedded prompts and doesn't need building"

} finally {
    # Restore original location
    Pop-Location
}
