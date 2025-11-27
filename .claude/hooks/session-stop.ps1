#!/usr/bin/env pwsh
# Session Stop Hook (PowerShell)
# AI-powered orchestrator reference validation
# Runs when Claude Code session ends
# Uses AI to intelligently check if references are broken or stale

$ErrorActionPreference = "Continue"

# Use forward slashes for git compatibility (git always outputs forward slashes)
$ORCHESTRATOR_FILE = "agents/orchestrator.md"
$ORCHESTRATOR_FILE_WIN = "agents\orchestrator.md"

# Only run if orchestrator file exists (check both path formats)
if (-not (Test-Path $ORCHESTRATOR_FILE) -and -not (Test-Path $ORCHESTRATOR_FILE_WIN)) {
    exit 0
}

Write-Host ""
Write-Host "🔍 Session Stop: Checking if orchestrator was modified..."

# Check if orchestrator was modified during this session
$MODIFIED = $false

# Check for uncommitted changes (staged or unstaged)
# Git outputs forward slashes, so match against that
$diffOutput = & git diff --name-only HEAD -- $ORCHESTRATOR_FILE 2>$null
if ($diffOutput -and ($diffOutput -match "agents/orchestrator\.md")) {
    $MODIFIED = $true
    Write-Host "  → Detected uncommitted changes to $ORCHESTRATOR_FILE"
}

if (-not $MODIFIED) {
    $cachedDiff = & git diff --name-only --cached -- $ORCHESTRATOR_FILE 2>$null
    if ($cachedDiff -and ($cachedDiff -match "agents/orchestrator\.md")) {
        $MODIFIED = $true
        Write-Host "  → Detected staged changes to $ORCHESTRATOR_FILE"
    }
}

# Check recent commits on current branch (last 5 commits)
if (-not $MODIFIED) {
    $recentChanges = & git log -5 --name-only --pretty=format: 2>$null | Select-String -Pattern "agents/orchestrator\.md" -Quiet
    if ($recentChanges) {
        $MODIFIED = $true
        Write-Host "  → Detected recent commit(s) modifying $ORCHESTRATOR_FILE"
    }
}

if (-not $MODIFIED) {
    Write-Host "  ✅ No modifications to orchestrator detected - skipping validation"
    exit 0
}

# Orchestrator was modified - trigger AI validation
Write-Host ""
Write-Host "⚠️  Orchestrator was modified during this session!" -ForegroundColor Yellow
Write-Host "🤖 Triggering AI-powered reference validation..."
Write-Host ""
Write-Host "The AI will:"
Write-Host "  1. Read agents/orchestrator.md completely"
Write-Host "  2. Extract all §line and §Step references"
Write-Host "  3. Verify each reference points to correct content"
Write-Host "  4. Detect stale references (technically valid but semantically wrong)"
Write-Host "  5. Report any issues found"
Write-Host ""
Write-Host "---"
Write-Host ""

# Create a marker file to signal that AI validation should run
$markerDir = ".claude\session-stop-checks"
if (-not (Test-Path $markerDir)) {
    New-Item -ItemType Directory -Path $markerDir -Force | Out-Null
}
"orchestrator-references" | Out-File -FilePath "$markerDir\validate-orchestrator.txt" -Encoding UTF8

# Output a clear message for the AI to see
@'
🤖 AI VALIDATION REQUIRED:

Please perform intelligent validation of orchestrator references:

**Your task:**
1. Read `agents/orchestrator.md` in full
2. Find ALL references in these formats:
   - `§line XXXX` or `§line XXXX (keyword)`
   - `§Step X.Y` or `§Step X.Y.Z`
3. For EACH reference found:
   - Verify the line number exists and points to correct content
   - Check if the keyword (if present) matches the actual content
   - Verify §Step references point to actual section headers
   - Detect if reference is STALE (points to wrong content even if line exists)
4. Report findings:
   - ✅ Valid references (only if all pass)
   - ⚠️ Stale references (technically valid but semantically wrong)
   - ❌ Broken references (line doesn't exist or completely wrong)

**Example of stale reference:**
- Reference says: `§line 146 (Query task groups)`
- Line 146 contains: `- Increment iteration counter`
- This is STALE (wrong content) even though line exists

**Do NOT just run the validation script - that already failed to detect issues.**
**You must READ the file and CHECK each reference intelligently.**

After validation, delete the marker file:
`Remove-Item -Recurse -Force .claude\session-stop-checks`

'@

exit 0
