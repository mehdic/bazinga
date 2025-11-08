---
name: quality-dashboard
description: Unified project health dashboard aggregating all quality metrics
category: superpowers
execution_time: 10-15s
---

# Quality Dashboard Skill

## Overview

The **quality-dashboard** Skill provides a comprehensive, unified view of project health by aggregating metrics from all quality tools (security scans, test coverage, linting) and project metrics (velocity, cycle time).

**Purpose:** Give PM and users a single health score (0-100) with trend analysis and anomaly detection.

## When to Use

- **Before major decisions** - Check overall health before proceeding
- **Before BAZINGA** - Final health check before declaring complete
- **After significant changes** - See impact of changes on quality
- **Weekly/milestone reviews** - Track quality trends over time

## What It Analyzes

| Source | Metrics Extracted |
|--------|-------------------|
| **security_scan.json** | Critical/high/medium vulnerability counts, trend |
| **coverage_report.json** | Line/branch coverage percentages, trend |
| **lint_results.json** | Issue counts by severity, trend |
| **project_metrics.json** | Velocity, cycle time, completion %, revision rate |
| **historical_metrics.json** | Historical averages for trend comparison |

## Output Format

```json
{
  "overall_health_score": 85,
  "health_level": "good",
  "timestamp": "2024-11-08T12:00:00Z",
  "metrics": {
    "security": {
      "score": 90,
      "critical_issues": 0,
      "high_issues": 1,
      "medium_issues": 5,
      "trend": "improving"
    },
    "coverage": {
      "score": 80,
      "line_coverage": 75,
      "branch_coverage": 68,
      "uncovered_files": ["payment.py", "auth.py"],
      "trend": "stable"
    },
    "lint": {
      "score": 85,
      "total_issues": 23,
      "high_severity": 2,
      "medium_severity": 8,
      "low_severity": 13,
      "trend": "improving"
    },
    "velocity": {
      "score": 95,
      "current": 12,
      "historical_avg": 10.5,
      "trend": "improving"
    },
    "quality_trend": "improving"
  },
  "anomalies": [
    "Security score dropped 15 points from last run",
    "Coverage decreased in auth module (45% -> 38%)"
  ],
  "recommendations": [
    "Address 1 high-severity security issue before deployment",
    "Add tests for auth module (coverage: 38% -> target: 70%)",
    "Fix 2 high-severity lint issues in payment.py"
  ],
  "quality_gates_status": {
    "security": "passed",
    "coverage": "failed",
    "lint": "passed"
  }
}
```

## Health Score Calculation

```
Overall Score = (security_score × 0.35) + (coverage_score × 0.30) + 
                (lint_score × 0.20) + (velocity_score × 0.15)

Where each component score is 0-100:

security_score:
  - critical_vulns = 0: 100 points
  - critical_vulns > 0: 0 points
  - Deduct 10 points per high vulnerability
  - Deduct 2 points per medium vulnerability

coverage_score:
  - line_coverage as percentage (e.g., 75% = 75 points)
  - Branch coverage bonus: if >65%, add 5 points

lint_score:
  - Start at 100
  - Deduct 10 points per high-severity issue
  - Deduct 2 points per medium-severity issue
  - Deduct 0.5 points per low-severity issue

velocity_score:
  - current > historical_avg: 100 points
  - current = historical_avg: 80 points
  - current < historical_avg: (current/historical) × 80
```

## Health Levels

| Score Range | Level | Meaning |
|-------------|-------|---------|
| 90-100 | Excellent | Production-ready, high quality |
| 75-89 | Good | Minor issues, safe to deploy with review |
| 60-74 | Fair | Multiple issues, needs improvement before deploy |
| 40-59 | Poor | Significant quality concerns, do not deploy |
| 0-39 | Critical | Severe quality issues, immediate action required |

## Trend Detection

Compares current metrics to previous run (if available):

- **Improving**: Score increased by >5 points
- **Stable**: Score changed by ≤5 points
- **Declining**: Score decreased by >5 points

## Anomaly Detection

Flags issues like:
- Security score dropped >10 points
- Coverage decreased in any file by >10%
- Lint issues increased >50%
- Velocity dropped below 50% of historical

## Usage Example

**In PM agent:**
```bash
# Before BAZINGA decision
/quality-dashboard

# Read results
cat coordination/quality_dashboard.json

# Check overall health
health_score=$(jq -r '.overall_health_score' coordination/quality_dashboard.json)

if [ "$health_score" -lt 75 ]; then
    echo "Health score too low ($health_score/100) - cannot send BAZINGA"
    echo "Recommendations:"
    jq -r '.recommendations[]' coordination/quality_dashboard.json
fi
```

## Benefits

✅ **Single unified view** - No need to check 4+ separate files  
✅ **Trend analysis** - See if quality improving or declining  
✅ **Anomaly detection** - Catch regressions automatically  
✅ **Actionable recommendations** - Know exactly what to fix  
✅ **Historical comparison** - Track progress over time

## Performance

- **Execution time:** 10-15 seconds
- **Dependencies:** jq (graceful fallback if not available)
- **Output:** `coordination/quality_dashboard.json`

## Platform Support

- ✅ Linux/macOS (bash)
- ✅ Windows (PowerShell)

## Related Skills

- **security-scan** - Provides security metrics input
- **test-coverage** - Provides coverage metrics input
- **lint-check** - Provides linting metrics input
- **velocity-tracker** - Provides project metrics input
