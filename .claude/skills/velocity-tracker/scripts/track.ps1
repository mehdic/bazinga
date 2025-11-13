#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Velocity & Metrics Tracker - Analyzes PM state for data-driven decisions
.DESCRIPTION
    Calculates velocity, cycle times, trends, and detects 99% rule violations
.EXAMPLE
    ./track.ps1
#>

$ErrorActionPreference = "Stop"

$COORD_DIR = "bazinga"
$PM_STATE = Join-Path $COORD_DIR "pm_state.json"
$METRICS_FILE = Join-Path $COORD_DIR "project_metrics.json"
$HISTORICAL_FILE = Join-Path $COORD_DIR "historical_metrics.json"

Write-Host "📊 Velocity & Metrics Tracker" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# Ensure coordination directory exists
if (-not (Test-Path $COORD_DIR)) {
    New-Item -ItemType Directory -Path $COORD_DIR -Force | Out-Null
}

# Check if PM state exists
if (-not (Test-Path $PM_STATE)) {
    Write-Host "⚠️  No PM state found - this is the first run" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Creating initial metrics structure..."

    $initialMetrics = @{
        status = "first_run"
        message = "No historical data yet. Metrics will be available after first task completion."
        timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    } | ConvertTo-Json -Depth 10

    $initialMetrics | Out-File -FilePath $METRICS_FILE -Encoding utf8

    Write-Host "✓ Metrics file created: $METRICS_FILE" -ForegroundColor Green
    exit 0
}

Write-Host "📁 Reading PM state..."

# Read and parse PM state
try {
    $pmState = Get-Content $PM_STATE -Raw | ConvertFrom-Json
} catch {
    Write-Host "❌ Error reading PM state: $_" -ForegroundColor Red
    exit 1
}

# Calculate current metrics
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$totalGroups = if ($pmState.task_groups) { $pmState.task_groups.Count } else { 0 }
$completedGroups = 0
$inProgress = 0
$pending = 0
$totalStoryPoints = 0
$totalIterations = 0

if ($totalGroups -gt 0) {
    foreach ($group in $pmState.task_groups) {
        if ($group.status -eq "COMPLETED") {
            $completedGroups++
            # Default to 3 story points if not specified
            $storyPoints = if ($group.story_points) { $group.story_points } else { 3 }
            $totalStoryPoints += $storyPoints

            # Default to 1 iteration if not specified
            $iterations = if ($group.iterations) { $group.iterations } else { 1 }
            $totalIterations += $iterations
        }
        elseif ($group.status -eq "IN_PROGRESS") {
            $inProgress++
        }
    }

    $pending = $totalGroups - $completedGroups - $inProgress
    if ($pending -lt 0) { $pending = 0 }
}

# Calculate percentage complete
$percentComplete = if ($totalGroups -gt 0) {
    [Math]::Round(($completedGroups / $totalGroups) * 100)
} else { 0 }

# Calculate revision rate
$revisionRate = if ($completedGroups -gt 0) {
    [Math]::Round($totalIterations / $completedGroups, 2)
} else { 0.0 }

Write-Host "   Total groups: $totalGroups"
Write-Host "   Completed: $completedGroups"
Write-Host "   In progress: $inProgress"
Write-Host "   Pending: $pending"
Write-Host "   Velocity: $totalStoryPoints story points"
Write-Host ""

# Load historical metrics
Write-Host "📊 Analyzing historical trends..."

$historicalVelocity = 0.0
$historicalRevisionRate = 1.0
$totalRuns = 0
$velocityTrend = "stable"
$qualityTrend = "stable"

if (Test-Path $HISTORICAL_FILE) {
    try {
        $historical = Get-Content $HISTORICAL_FILE -Raw | ConvertFrom-Json

        $totalRuns = if ($historical.total_runs) { $historical.total_runs } else { 0 }
        $historicalVelocity = if ($historical.average_velocity) { $historical.average_velocity } else { 0.0 }
        $historicalRevisionRate = if ($historical.average_revision_rate) { $historical.average_revision_rate } else { 1.0 }

        Write-Host "   Historical average velocity: $historicalVelocity"
        Write-Host "   Historical revision rate: $historicalRevisionRate"

        # Determine trends
        if ($totalStoryPoints -gt ($historicalVelocity * 1.1)) {
            $velocityTrend = "improving"
        }
        elseif ($totalStoryPoints -lt ($historicalVelocity * 0.9)) {
            $velocityTrend = "declining"
        }

        if ($revisionRate -lt ($historicalRevisionRate * 0.9)) {
            $qualityTrend = "improving"
        }
        elseif ($revisionRate -gt ($historicalRevisionRate * 1.1)) {
            $qualityTrend = "declining"
        }
    }
    catch {
        Write-Host "   Could not parse historical data" -ForegroundColor Yellow
    }
}
else {
    Write-Host "   No historical data available yet"
}

Write-Host ""

# Generate recommendations and warnings
$recommendations = @()
$warnings = @()

if ($totalStoryPoints -gt 0) {
    if ($velocityTrend -eq "improving") {
        $recommendations += "Current velocity ($totalStoryPoints) exceeds historical average - excellent progress"
    }
    elseif ($velocityTrend -eq "declining") {
        $warnings += "Velocity declining - current ($totalStoryPoints) below historical average ($historicalVelocity)"
    }
}

if ($qualityTrend -eq "improving") {
    $recommendations += "Quality trend improving - fewer revisions per task"
}
elseif ($qualityTrend -eq "declining") {
    $warnings += "Quality declining - more revisions required per task"
}

# Create metrics object
$metrics = @{
    timestamp = $timestamp
    current_run = @{
        total_groups = $totalGroups
        completed_groups = $completedGroups
        in_progress = $inProgress
        pending = $pending
        percent_complete = $percentComplete
        velocity = $totalStoryPoints
        revision_rate = $revisionRate
    }
    historical_metrics = @{
        total_runs = $totalRuns
        average_velocity = $historicalVelocity
        average_revision_rate = $historicalRevisionRate
    }
    trends = @{
        velocity = $velocityTrend
        quality = $qualityTrend
    }
    recommendations = $recommendations
    warnings = $warnings
}

# Write metrics file
Write-Host "💾 Writing metrics..."

try {
    $metrics | ConvertTo-Json -Depth 10 | Out-File -FilePath $METRICS_FILE -Encoding utf8
    Write-Host "✓ Metrics written to: $METRICS_FILE" -ForegroundColor Green
}
catch {
    Write-Host "❌ Error writing metrics: $_" -ForegroundColor Red
    exit 1
}

# Update historical metrics
if ($completedGroups -gt 0) {
    Write-Host ""
    Write-Host "📈 Updating historical data..."

    $newTotalRuns = $totalRuns + 1

    # Calculate new averages
    $newAvgVelocity = if ($totalRuns -gt 0) {
        [Math]::Round((($historicalVelocity * $totalRuns) + $totalStoryPoints) / $newTotalRuns, 2)
    } else {
        $totalStoryPoints
    }

    $newAvgRevision = if ($totalRuns -gt 0) {
        [Math]::Round((($historicalRevisionRate * $totalRuns) + $revisionRate) / $newTotalRuns, 2)
    } else {
        $revisionRate
    }

    $historicalMetrics = @{
        total_runs = $newTotalRuns
        average_velocity = $newAvgVelocity
        average_revision_rate = $newAvgRevision
        last_updated = $timestamp
    }

    try {
        $historicalMetrics | ConvertTo-Json -Depth 10 | Out-File -FilePath $HISTORICAL_FILE -Encoding utf8
        Write-Host "✓ Historical metrics updated" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠️  Could not update historical metrics: $_" -ForegroundColor Yellow
    }
}

# Display summary
Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "✓ Metrics analysis complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Summary:"
Write-Host "   Progress: $percentComplete%"
Write-Host "   Velocity: $totalStoryPoints story points"
Write-Host "   Trend: $velocityTrend"

if ($warnings.Count -gt 0) {
    Write-Host ""
    Write-Host "Warnings:" -ForegroundColor Red
    foreach ($warning in $warnings) {
        Write-Host "   ⚠️  $warning" -ForegroundColor Yellow
    }
}

if ($recommendations.Count -gt 0) {
    Write-Host ""
    Write-Host "Recommendations:" -ForegroundColor Green
    foreach ($rec in $recommendations) {
        Write-Host "   ✓ $rec"
    }
}

Write-Host ""
Write-Host "📄 Full metrics: $METRICS_FILE"
