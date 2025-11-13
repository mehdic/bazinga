#!/usr/bin/env pwsh

# Directories
$COORD_DIR = "bazinga"
$SECURITY_FILE = "$COORD_DIR/security_scan.json"
$COVERAGE_FILE = "$COORD_DIR/coverage_report.json"
$LINT_FILE = "$COORD_DIR/lint_results.json"
$METRICS_FILE = "$COORD_DIR/project_metrics.json"
$HISTORICAL_FILE = "$COORD_DIR/historical_metrics.json"
$DASHBOARD_FILE = "$COORD_DIR/quality_dashboard.json"
$PREVIOUS_DASHBOARD = "$COORD_DIR/quality_dashboard_previous.json"

Write-Host "📊 Quality Dashboard" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Save previous dashboard for trend comparison
if (Test-Path $DASHBOARD_FILE) {
    Copy-Item $DASHBOARD_FILE $PREVIOUS_DASHBOARD -Force
}

# Initialize scores
$SECURITY_SCORE = 100
$COVERAGE_SCORE = 0
$LINT_SCORE = 100
$VELOCITY_SCORE = 80

$ANOMALIES = @()
$RECOMMENDATIONS = @()

# ============================================
# 1. Analyze Security Metrics
# ============================================
Write-Host "🔒 Analyzing security metrics..."

$CRITICAL_VULNS = 0
$HIGH_VULNS = 0
$MEDIUM_VULNS = 0
$SECURITY_TREND = "stable"

if (Test-Path $SECURITY_FILE) {
    try {
        $security = Get-Content $SECURITY_FILE -Raw | ConvertFrom-Json
        $CRITICAL_VULNS = if ($security.summary.critical) { $security.summary.critical } else { 0 }
        $HIGH_VULNS = if ($security.summary.high) { $security.summary.high } else { 0 }
        $MEDIUM_VULNS = if ($security.summary.medium) { $security.summary.medium } else { 0 }

        # Calculate security score
        if ($CRITICAL_VULNS -gt 0) {
            $SECURITY_SCORE = 0
            $ANOMALIES += "Critical security vulnerabilities detected ($CRITICAL_VULNS)"
            $RECOMMENDATIONS += "URGENT: Fix $CRITICAL_VULNS critical security vulnerabilities before deployment"
        } else {
            $SECURITY_SCORE = 100 - ($HIGH_VULNS * 10) - ($MEDIUM_VULNS * 2)
            if ($SECURITY_SCORE -lt 0) { $SECURITY_SCORE = 0 }
        }

        if ($HIGH_VULNS -gt 0) {
            $RECOMMENDATIONS += "Address $HIGH_VULNS high-severity security issues"
        }

        Write-Host "   Critical: $CRITICAL_VULNS | High: $HIGH_VULNS | Medium: $MEDIUM_VULNS"
        Write-Host "   Security Score: $SECURITY_SCORE/100"
    } catch {
        Write-Host "   ⚠️  Error reading security scan results" -ForegroundColor Yellow
        $SECURITY_SCORE = 50
    }
} else {
    Write-Host "   ⚠️  No security scan results found" -ForegroundColor Yellow
    $SECURITY_SCORE = 50
}

# ============================================
# 2. Analyze Coverage Metrics
# ============================================
Write-Host ""
Write-Host "📈 Analyzing test coverage..."

$LINE_COV = 0
$BRANCH_COV = 0
$COVERAGE_TREND = "stable"

if (Test-Path $COVERAGE_FILE) {
    try {
        $coverage = Get-Content $COVERAGE_FILE -Raw | ConvertFrom-Json
        $LINE_COV = if ($coverage.summary.line_coverage) { $coverage.summary.line_coverage } else { 0 }
        $BRANCH_COV = if ($coverage.summary.branch_coverage) { $coverage.summary.branch_coverage } else { 0 }

        # Calculate coverage score
        $COVERAGE_SCORE = [math]::Floor($LINE_COV)
        if ($BRANCH_COV -gt 65) {
            $COVERAGE_SCORE += 5
        }
        if ($COVERAGE_SCORE -gt 100) { $COVERAGE_SCORE = 100 }

        if ($LINE_COV -lt 70) {
            $RECOMMENDATIONS += "Increase test coverage to 70% (currently $LINE_COV%)"
        }

        Write-Host "   Line Coverage: $LINE_COV% | Branch Coverage: $BRANCH_COV%"
        Write-Host "   Coverage Score: $COVERAGE_SCORE/100"
    } catch {
        Write-Host "   ⚠️  Error reading coverage report" -ForegroundColor Yellow
        $COVERAGE_SCORE = 50
    }
} else {
    Write-Host "   ⚠️  No coverage report found" -ForegroundColor Yellow
    $COVERAGE_SCORE = 50
}

# ============================================
# 3. Analyze Lint Metrics
# ============================================
Write-Host ""
Write-Host "🔍 Analyzing code quality (lint)..."

$HIGH_LINT = 0
$MEDIUM_LINT = 0
$LOW_LINT = 0
$LINT_TREND = "stable"

if (Test-Path $LINT_FILE) {
    try {
        $lint = Get-Content $LINT_FILE -Raw | ConvertFrom-Json

        foreach ($file in $lint.files) {
            foreach ($issue in $file.issues) {
                switch ($issue.severity) {
                    "high" { $HIGH_LINT++ }
                    "medium" { $MEDIUM_LINT++ }
                    "low" { $LOW_LINT++ }
                }
            }
        }

        # Calculate lint score
        $LINT_SCORE = 100 - ($HIGH_LINT * 10) - ($MEDIUM_LINT * 2) - [math]::Floor($LOW_LINT / 2)
        if ($LINT_SCORE -lt 0) { $LINT_SCORE = 0 }

        if ($HIGH_LINT -gt 5) {
            $RECOMMENDATIONS += "Fix $HIGH_LINT high-severity lint issues (threshold: 5)"
        }

        $TOTAL_LINT = $HIGH_LINT + $MEDIUM_LINT + $LOW_LINT
        Write-Host "   High: $HIGH_LINT | Medium: $MEDIUM_LINT | Low: $LOW_LINT (Total: $TOTAL_LINT)"
        Write-Host "   Lint Score: $LINT_SCORE/100"
    } catch {
        Write-Host "   ⚠️  Error reading lint results" -ForegroundColor Yellow
        $LINT_SCORE = 50
    }
} else {
    Write-Host "   ⚠️  No lint results found" -ForegroundColor Yellow
    $LINT_SCORE = 50
}

# ============================================
# 4. Analyze Velocity Metrics
# ============================================
Write-Host ""
Write-Host "⚡ Analyzing project velocity..."

$CURRENT_VEL = 0
$HIST_AVG_VEL = 10
$VELOCITY_TREND = "stable"

if (Test-Path $METRICS_FILE) {
    try {
        $metrics = Get-Content $METRICS_FILE -Raw | ConvertFrom-Json
        $CURRENT_VEL = if ($metrics.current_run.velocity) { $metrics.current_run.velocity } else { 0 }

        if (Test-Path $HISTORICAL_FILE) {
            $historical = Get-Content $HISTORICAL_FILE -Raw | ConvertFrom-Json
            $HIST_AVG_VEL = if ($historical.averages.velocity) { $historical.averages.velocity } else { 10 }
        }

        # Calculate velocity score
        if ($CURRENT_VEL -gt $HIST_AVG_VEL) {
            $VELOCITY_SCORE = 100
            $VELOCITY_TREND = "improving"
        } elseif ($CURRENT_VEL -eq $HIST_AVG_VEL) {
            $VELOCITY_SCORE = 80
            $VELOCITY_TREND = "stable"
        } else {
            $VELOCITY_SCORE = [math]::Floor(($CURRENT_VEL / $HIST_AVG_VEL) * 80)
            $VELOCITY_TREND = "declining"

            if ($CURRENT_VEL -lt ($HIST_AVG_VEL * 0.5)) {
                $ANOMALIES += "Velocity dropped below 50% of historical average"
                $RECOMMENDATIONS += "Investigate velocity decline (current: $CURRENT_VEL vs avg: $HIST_AVG_VEL)"
            }
        }

        Write-Host "   Current Velocity: $CURRENT_VEL | Historical Avg: $HIST_AVG_VEL"
        Write-Host "   Velocity Score: $VELOCITY_SCORE/100 ($VELOCITY_TREND)"
    } catch {
        Write-Host "   ⚠️  Error reading project metrics" -ForegroundColor Yellow
        $VELOCITY_SCORE = 50
    }
} else {
    Write-Host "   ⚠️  No project metrics found" -ForegroundColor Yellow
    $VELOCITY_SCORE = 50
}

# ============================================
# 5. Calculate Overall Health Score
# ============================================
Write-Host ""
Write-Host "🎯 Calculating overall health..."

# Weighted average: Security 35%, Coverage 30%, Lint 20%, Velocity 15%
$OVERALL_SCORE = [math]::Floor(($SECURITY_SCORE * 0.35) + ($COVERAGE_SCORE * 0.30) + ($LINT_SCORE * 0.20) + ($VELOCITY_SCORE * 0.15))

# Determine health level
if ($OVERALL_SCORE -ge 90) {
    $HEALTH_LEVEL = "excellent"
    $HEALTH_EMOJI = "🟢"
} elseif ($OVERALL_SCORE -ge 75) {
    $HEALTH_LEVEL = "good"
    $HEALTH_EMOJI = "🟡"
} elseif ($OVERALL_SCORE -ge 60) {
    $HEALTH_LEVEL = "fair"
    $HEALTH_EMOJI = "🟠"
} elseif ($OVERALL_SCORE -ge 40) {
    $HEALTH_LEVEL = "poor"
    $HEALTH_EMOJI = "🔴"
} else {
    $HEALTH_LEVEL = "critical"
    $HEALTH_EMOJI = "❌"
}

Write-Host "   Overall Health Score: $HEALTH_EMOJI $OVERALL_SCORE/100 ($HEALTH_LEVEL)"

# ============================================
# 6. Detect Overall Trend
# ============================================
$OVERALL_TREND = "stable"
if (Test-Path $PREVIOUS_DASHBOARD) {
    try {
        $prevDash = Get-Content $PREVIOUS_DASHBOARD -Raw | ConvertFrom-Json
        $PREV_SCORE = if ($prevDash.overall_health_score) { $prevDash.overall_health_score } else { 0 }
        $SCORE_DIFF = $OVERALL_SCORE - $PREV_SCORE

        if ($SCORE_DIFF -gt 5) {
            $OVERALL_TREND = "improving"
        } elseif ($SCORE_DIFF -lt -5) {
            $OVERALL_TREND = "declining"
            $ANOMALIES += "Overall health score dropped by $([math]::Abs($SCORE_DIFF)) points"
        }
    } catch {
        # Ignore errors reading previous dashboard
    }
}

# ============================================
# 7. Check Quality Gates
# ============================================
$GATE_SECURITY = if ($CRITICAL_VULNS -gt 0) { "failed" } else { "passed" }
$GATE_COVERAGE = if ($LINE_COV -lt 70) { "failed" } else { "passed" }
$GATE_LINT = if ($HIGH_LINT -gt 5) { "failed" } else { "passed" }

# ============================================
# 8. Generate JSON Output
# ============================================
Write-Host ""
Write-Host "💾 Saving dashboard to $DASHBOARD_FILE..."

$TIMESTAMP = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

$dashboard = @{
    overall_health_score = $OVERALL_SCORE
    health_level = $HEALTH_LEVEL
    timestamp = $TIMESTAMP
    metrics = @{
        security = @{
            score = $SECURITY_SCORE
            critical_issues = $CRITICAL_VULNS
            high_issues = $HIGH_VULNS
            medium_issues = $MEDIUM_VULNS
            trend = $SECURITY_TREND
        }
        coverage = @{
            score = $COVERAGE_SCORE
            line_coverage = $LINE_COV
            branch_coverage = $BRANCH_COV
            trend = $COVERAGE_TREND
        }
        lint = @{
            score = $LINT_SCORE
            total_issues = ($HIGH_LINT + $MEDIUM_LINT + $LOW_LINT)
            high_severity = $HIGH_LINT
            medium_severity = $MEDIUM_LINT
            low_severity = $LOW_LINT
            trend = $LINT_TREND
        }
        velocity = @{
            score = $VELOCITY_SCORE
            current = $CURRENT_VEL
            historical_avg = $HIST_AVG_VEL
            trend = $VELOCITY_TREND
        }
        quality_trend = $OVERALL_TREND
    }
    anomalies = $ANOMALIES
    recommendations = $RECOMMENDATIONS
    quality_gates_status = @{
        security = $GATE_SECURITY
        coverage = $GATE_COVERAGE
        lint = $GATE_LINT
    }
}

$dashboard | ConvertTo-Json -Depth 10 | Set-Content $DASHBOARD_FILE

Write-Host "✅ Dashboard generated successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "$HEALTH_EMOJI Overall Health: $OVERALL_SCORE/100 ($HEALTH_LEVEL, $OVERALL_TREND)" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

if ($ANOMALIES.Count -gt 0) {
    Write-Host ""
    Write-Host "⚠️  Anomalies Detected:" -ForegroundColor Yellow
    foreach ($anomaly in $ANOMALIES) {
        Write-Host "   - $anomaly"
    }
}

if ($RECOMMENDATIONS.Count -gt 0) {
    Write-Host ""
    Write-Host "💡 Recommendations:" -ForegroundColor Cyan
    foreach ($rec in $RECOMMENDATIONS) {
        Write-Host "   - $rec"
    }
}

Write-Host ""
Write-Host "📄 Full dashboard: bazinga/quality_dashboard.json"
