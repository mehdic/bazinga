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
# Using -Raw for better performance with large files
$transcriptContent = Get-Content $transcriptPath -Raw -ErrorAction SilentlyContinue
if (-not $transcriptContent) {
    exit 0
}

# Check both with and without § symbol for consistency across platforms
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

# Output the FULL orchestrator file to restore complete context
# After compaction, partial context leads to role drift and workflow failures
Write-Output ""
Write-Output "================================================================================"
Write-Output "  BAZINGA POST-COMPACTION RECOVERY"
Write-Output "  Re-injecting FULL orchestrator context..."
Write-Output "================================================================================"
Write-Output ""

# Output the complete orchestrator file (using -Raw for performance and exact fidelity)
Get-Content $orchestratorFile -Raw

Write-Output ""
Write-Output "================================================================================"
Write-Output "  ORCHESTRATOR CONTEXT FULLY RESTORED"
Write-Output "  Continue orchestration from where you left off."
Write-Output "  Check bazinga/bazinga.db for current session state."
Write-Output "================================================================================"
Write-Output ""

exit 0
