# parse-speckit-tasks.ps1
# Utility script to parse spec-kit tasks.md format and extract useful information
# for BAZINGA orchestration system
#
# Usage:
#   pwsh .claude/scripts/parse-speckit-tasks.ps1 <tasks.md path>
#   pwsh .claude/scripts/parse-speckit-tasks.ps1 .specify/features/001-auth/tasks.md

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$TasksFile
)

# Function to print colored output
function Write-ColorOutput {
    param(
        [string]$Color,
        [string]$Message
    )
    Write-Host $Message -ForegroundColor $Color
}

# Function to print section header
function Write-Section {
    param([string]$Title)
    Write-Host ""
    Write-ColorOutput "Cyan" "═══════════════════════════════════════════"
    Write-ColorOutput "Cyan" $Title
    Write-ColorOutput "Cyan" "═══════════════════════════════════════════"
}

# Check if file exists
if (-not (Test-Path $TasksFile)) {
    Write-ColorOutput "Red" "Error: File not found: $TasksFile"
    exit 1
}

# Read file content
$content = Get-Content $TasksFile -Raw

# Parse tasks
Write-Section "SPEC-KIT TASKS ANALYSIS"

# Count total tasks
$totalTasks = ([regex]::Matches($content, '^\s*-\s*\[.\]\s*\[T\d+\]', [System.Text.RegularExpressions.RegexOptions]::Multiline)).Count
Write-ColorOutput "Blue" "📋 Total Tasks: $totalTasks"

# Count completed tasks
$completedTasks = ([regex]::Matches($content, '^\s*-\s*\[x\]\s*\[T\d+\]', [System.Text.RegularExpressions.RegexOptions]::Multiline)).Count
Write-ColorOutput "Green" "✅ Completed: $completedTasks"

# Count pending tasks
$pendingTasks = $totalTasks - $completedTasks
Write-ColorOutput "Yellow" "⏳ Pending: $pendingTasks"

# Calculate progress percentage
if ($totalTasks -gt 0) {
    $progress = [math]::Round(($completedTasks / $totalTasks) * 100)
    Write-ColorOutput "Cyan" "📊 Progress: ${progress}%"
} else {
    $progress = 0
}

# Find parallel tasks
Write-Section "PARALLEL TASKS"
$parallelMatches = [regex]::Matches($content, '\[P\]')
$parallelCount = $parallelMatches.Count
Write-ColorOutput "Blue" "🔀 Tasks marked [P]: $parallelCount"

if ($parallelCount -gt 0) {
    Write-Host ""
    Write-ColorOutput "Cyan" "Parallel tasks:"
    $parallelLines = Get-Content $TasksFile | Select-String '\[P\]'
    foreach ($line in $parallelLines) {
        Write-Host "  $line"
    }
}

# Find user stories
Write-Section "USER STORIES"
$userStories = [regex]::Matches($content, '\[US\d+\]') | ForEach-Object { $_.Value } | Select-Object -Unique | Sort-Object

if ($userStories.Count -gt 0) {
    foreach ($story in $userStories) {
        $storyCount = ([regex]::Matches($content, [regex]::Escape($story))).Count
        $storyCompleted = ([regex]::Matches($content, "\[x\].*$([regex]::Escape($story))")).Count
        Write-ColorOutput "Blue" "${story}: $storyCompleted/$storyCount tasks complete"

        Write-Host ""
        Write-ColorOutput "Cyan" "  Tasks in ${story}:"
        $storyLines = Get-Content $TasksFile | Select-String $story
        foreach ($line in $storyLines) {
            Write-Host "    $line"
        }
        Write-Host ""
    }
} else {
    Write-ColorOutput "Yellow" "No user story markers found"
}

# Group tasks by status
Write-Section "TASKS BY STATUS"

Write-Host ""
Write-ColorOutput "Green" "✅ COMPLETED TASKS:"
$completedLines = Get-Content $TasksFile | Select-String '^\s*-\s*\[x\]\s*\[T\d+\]'
if ($completedLines.Count -gt 0) {
    foreach ($line in $completedLines) {
        Write-Host "  $line"
    }
} else {
    Write-Host "  (none)"
}

Write-Host ""
Write-ColorOutput "Yellow" "⏳ PENDING TASKS:"
$pendingLines = Get-Content $TasksFile | Select-String '^\s*-\s*\[ \]\s*\[T\d+\]'
if ($pendingLines.Count -gt 0) {
    foreach ($line in $pendingLines) {
        Write-Host "  $line"
    }
} else {
    Write-Host "  (none)"
}

# Extract task IDs
Write-Section "TASK IDs"

Write-Host ""
Write-ColorOutput "Cyan" "All Task IDs:"
$taskIds = [regex]::Matches($content, 'T\d+') | ForEach-Object { $_.Value } | Select-Object -Unique | Sort-Object
if ($taskIds.Count -gt 0) {
    Write-Host "  $($taskIds -join ' ')"
} else {
    Write-Host "  (none found)"
}

# Extract files mentioned
Write-Section "FILES AFFECTED"

Write-Host ""
Write-ColorOutput "Cyan" "Files mentioned in tasks:"
$files = [regex]::Matches($content, '\([a-zA-Z0-9_/.-]+\.(py|js|ts|go|rs|java|rb|php|cpp|h|md)\)') |
    ForEach-Object { $_.Value.Trim('()') } |
    Select-Object -Unique |
    Sort-Object
if ($files.Count -gt 0) {
    foreach ($file in $files) {
        Write-Host "  $file"
    }
} else {
    Write-Host "  (none found)"
}

# Generate JSON summary
Write-Section "JSON SUMMARY"

Write-Host ""
Write-ColorOutput "Cyan" "JSON output (for programmatic use):"

# Build user stories JSON array
$userStoriesJson = @()
foreach ($story in $userStories) {
    $storyCount = ([regex]::Matches($content, [regex]::Escape($story))).Count
    $storyCompleted = ([regex]::Matches($content, "\[x\].*$([regex]::Escape($story))")).Count
    $userStoriesJson += @{
        story = $story
        total = $storyCount
        completed = $storyCompleted
    }
}

# Build JSON object
$jsonOutput = @{
    total_tasks = $totalTasks
    completed_tasks = $completedTasks
    pending_tasks = $pendingTasks
    progress_percentage = $progress
    parallel_tasks = $parallelCount
    user_stories = $userStoriesJson
    task_ids = @($taskIds)
    files = @($files)
}

# Convert to JSON and output
$jsonOutput | ConvertTo-Json -Depth 5

Write-Section "ANALYSIS COMPLETE"

Write-Host ""
Write-ColorOutput "Blue" "💡 Tip: Use this information to plan BAZINGA orchestration groups"
Write-Host ""

# Exit with success if all tasks complete, otherwise exit code indicates pending tasks
if ($pendingTasks -eq 0) {
    Write-ColorOutput "Green" "🎉 All tasks complete!"
    exit 0
} else {
    Write-ColorOutput "Yellow" "⚠️  $pendingTasks tasks remaining"
    exit 1
}
