# BAZINGA Post-Compaction Recovery Hook
# Deployed by: bazinga install
#
# This hook fires after context compaction (compact|resume events).
# It checks if orchestration was in progress, then outputs the
# IDENTITY AXIOMS section (not full file to avoid token blow-up).

# Read hook input from stdin
$hookInput = $input | Out-String

# Exit silently if no input
if ([string]::IsNullOrWhiteSpace($hookInput)) {
    exit 0
}

# Parse JSON input using PowerShell's ConvertFrom-Json
try {
    $data = $hookInput | ConvertFrom-Json
    $transcriptPath = $data.transcript_path
    $projectCwd = $data.cwd
} catch {
    # Soft fail - don't break session
    exit 0
}

# Exit silently if no transcript path
if ([string]::IsNullOrWhiteSpace($transcriptPath) -or -not (Test-Path $transcriptPath)) {
    exit 0
}

# Exit silently if no cwd
if ([string]::IsNullOrWhiteSpace($projectCwd)) {
    exit 0
}

# Check if orchestration was in progress
# Look for evidence of /bazinga.orchestrate command or orchestrator activity
$transcriptContent = Get-Content $transcriptPath -Raw -ErrorAction SilentlyContinue
if (-not $transcriptContent) {
    exit 0
}

$orchestrationPattern = "bazinga\.orchestrate|ORCHESTRATOR|orchestrator\.md|ORCHESTRATOR IDENTITY AXIOMS"
if ($transcriptContent -notmatch $orchestrationPattern) {
    # No orchestration evidence - exit silently
    exit 0
}

# Build absolute paths to orchestrator files
$orchestratorCmd = Join-Path $projectCwd ".claude\commands\bazinga.orchestrate.md"
$orchestratorAgent = Join-Path $projectCwd ".claude\agents\orchestrator.md"

# Find the orchestrator file
$orchestratorFile = $null
if (Test-Path $orchestratorCmd) {
    $orchestratorFile = $orchestratorCmd
} elseif (Test-Path $orchestratorAgent) {
    $orchestratorFile = $orchestratorAgent
}

# Soft fail if file not found (don't break session)
if (-not $orchestratorFile) {
    Write-Output ""
    Write-Output "⚠️  BAZINGA: Orchestrator file not found for recovery."
    Write-Output "   If you are the orchestrator, manually read: .claude\agents\orchestrator.md"
    exit 0
}

# Output ONLY the identity axioms section (not full file to avoid token blow-up)
Write-Output ""
Write-Output "================================================================================"
Write-Output "  BAZINGA POST-COMPACTION RECOVERY"
Write-Output "  Re-injecting identity axioms (not full file to save tokens)..."
Write-Output "================================================================================"
Write-Output ""

# Output the identity axioms section (first ~60 lines containing the critical rules)
Get-Content $orchestratorFile -TotalCount 60

Write-Output ""
Write-Output "================================================================================"
Write-Output "  IDENTITY AXIOMS RESTORED"
Write-Output "  For full rules, read: .claude\agents\orchestrator.md"
Write-Output "================================================================================"
Write-Output ""

exit 0
