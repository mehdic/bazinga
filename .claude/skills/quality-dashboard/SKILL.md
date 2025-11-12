---
name: quality-dashboard
description: Unified project health dashboard aggregating all quality metrics
allowed-tools: [Bash, Read, Write]
---

# Quality Dashboard Skill

You are the quality-dashboard skill. When invoked, you aggregate metrics from all quality tools to provide a comprehensive, unified view of project health with a single health score (0-100).

## Your Task

When invoked, you will:
1. Load metrics from security, coverage, lint, and velocity tools
2. Calculate individual component scores
3. Compute overall health score (weighted average)
4. Detect trends by comparing to previous run
5. Identify anomalies
6. Generate actionable recommendations

---

## Step 1: Load Quality Metrics

Use the **Read** tool to load these files (if they exist):

1. `coordination/security_scan.json` - Security vulnerabilities
2. `coordination/coverage_report.json` - Test coverage
3. `coordination/lint_results.json` - Linting issues
4. `coordination/project_metrics.json` - Velocity and project metrics
5. `coordination/historical_metrics.json` - Historical data for trends
6. `coordination/quality_dashboard_previous.json` - Previous run for comparison

If a file doesn't exist, set that metric to null and note it in the report.

---

## Step 2: Calculate Security Score (0-100)

Based on `security_scan.json`:

```
security_score = 100

# Deduct points for vulnerabilities
security_score -= (critical_issues × 50)  # Critical = -50 points each
security_score -= (high_issues × 10)      # High = -10 points each
security_score -= (medium_issues × 2)     # Medium = -2 points each
security_score -= (low_issues × 0.5)      # Low = -0.5 points each

# Floor at 0
security_score = max(0, security_score)
```

**Special case**: If `security_scan.json` has `status: "error"`, set security_score = null

**Trend**: Compare to previous run's security_score
- If increased by >5: trend = "improving"
- If decreased by >5: trend = "declining"
- Otherwise: trend = "stable"

---

## Step 3: Calculate Coverage Score (0-100)

Based on `coverage_report.json`:

```
coverage_score = overall_coverage  # Use line coverage percentage

# Bonus for branch coverage
if branch_coverage > 65:
    coverage_score += 5

# Cap at 100
coverage_score = min(100, coverage_score)
```

**Trend**: Compare to previous run's overall_coverage
- If increased by >5: trend = "improving"
- If decreased by >5: trend = "declining"
- Otherwise: trend = "stable"

---

## Step 4: Calculate Lint Score (0-100)

Based on `lint_results.json`:

```
lint_score = 100

# Deduct points for issues
lint_score -= (error_count × 10)      # Errors = -10 points each
lint_score -= (warning_count × 2)     # Warnings = -2 points each
lint_score -= (info_count × 0.5)      # Info = -0.5 points each

# Floor at 0
lint_score = max(0, lint_score)
```

**Trend**: Compare to previous run's lint_score
- If increased by >5: trend = "improving"
- If decreased by >5: trend = "declining"
- Otherwise: trend = "stable"

---

## Step 5: Calculate Velocity Score (0-100)

Based on `project_metrics.json` and `historical_metrics.json`:

```
current_velocity = current_run.velocity
historical_avg = historical_metrics.average_velocity

if historical_avg == 0:
    velocity_score = 80  # No baseline, assume good

else if current_velocity >= historical_avg:
    velocity_score = 100

else:
    ratio = current_velocity / historical_avg
    velocity_score = ratio × 80  # Max 80 if at average, less if below
```

**Trend**:
- If current_velocity > historical_avg: trend = "improving"
- If current_velocity < historical_avg × 0.9: trend = "declining"
- Otherwise: trend = "stable"

---

## Step 6: Calculate Overall Health Score

Weighted average of component scores:

```
overall_health_score = (
    (security_score × 0.35) +
    (coverage_score × 0.30) +
    (lint_score × 0.20) +
    (velocity_score × 0.15)
)

# Round to integer
overall_health_score = round(overall_health_score)
```

**If any component is null** (due to missing data):
- Redistribute weights among available components
- Note in report: "Incomplete data: {component} not available"

---

## Step 7: Determine Health Level

Based on overall_health_score:

```
if score >= 90:
    health_level = "excellent"
elif score >= 75:
    health_level = "good"
elif score >= 60:
    health_level = "fair"
elif score >= 40:
    health_level = "poor"
else:
    health_level = "critical"
```

---

## Step 8: Detect Anomalies

Compare current metrics to previous run (if available):

**Anomaly conditions:**
1. Security score dropped >10 points
2. Coverage decreased in any file by >10%
3. Lint issues increased >50%
4. Velocity dropped below 50% of historical average
5. Any component score < 40

For each anomaly, add to anomalies array:
```
"Security score dropped 15 points from last run"
"Coverage decreased in auth module (45% -> 38%)"
```

---

## Step 9: Generate Recommendations

Based on metrics, generate actionable recommendations:

**Security recommendations:**
- If critical_issues > 0: "Address {count} critical security issues before deployment"
- If high_issues > 3: "Fix {count} high-severity security issues"

**Coverage recommendations:**
- If overall_coverage < 80: "Increase test coverage to 80% (currently {current}%)"
- For each file with coverage < 70: "Add tests for {file} (coverage: {percentage}%)"

**Lint recommendations:**
- If error_count > 5: "Fix {count} linting errors"
- If warning_count > 20: "Address {count} linting warnings"

**Velocity recommendations:**
- If velocity declining: "Velocity below average - consider task breakdown or additional resources"

---

## Step 10: Determine Quality Gate Status

Check if each component meets minimum thresholds:

```
quality_gates_status = {
    "security": "passed" if (critical_issues == 0 AND high_issues < 3) else "failed",
    "coverage": "passed" if overall_coverage >= 70 else "failed",
    "lint": "passed" if error_count == 0 else "failed"
}
```

---

## Step 11: Determine Overall Quality Trend

Based on individual component trends:

```
improving_count = count of components with "improving" trend
declining_count = count of components with "declining" trend

if improving_count > declining_count:
    overall_trend = "improving"
elif declining_count > improving_count:
    overall_trend = "declining"
else:
    overall_trend = "stable"
```

---

## Step 12: Write Output

Use the **Write** tool to create `coordination/quality_dashboard.json`:

```json
{
  "overall_health_score": <0-100>,
  "health_level": "excellent|good|fair|poor|critical",
  "timestamp": "<ISO 8601 timestamp>",
  "metrics": {
    "security": {
      "score": <0-100>,
      "critical_issues": <count>,
      "high_issues": <count>,
      "medium_issues": <count>,
      "trend": "improving|stable|declining"
    },
    "coverage": {
      "score": <0-100>,
      "line_coverage": <percentage>,
      "branch_coverage": <percentage or null>,
      "uncovered_files": ["<file1>", "<file2>"],
      "trend": "improving|stable|declining"
    },
    "lint": {
      "score": <0-100>,
      "total_issues": <count>,
      "high_severity": <count>,
      "medium_severity": <count>,
      "low_severity": <count>,
      "trend": "improving|stable|declining"
    },
    "velocity": {
      "score": <0-100>,
      "current": <value>,
      "historical_avg": <value>,
      "trend": "improving|stable|declining"
    },
    "quality_trend": "improving|stable|declining"
  },
  "anomalies": [
    "<anomaly description 1>",
    "<anomaly description 2>"
  ],
  "recommendations": [
    "<recommendation 1>",
    "<recommendation 2>",
    "<recommendation 3>"
  ],
  "quality_gates_status": {
    "security": "passed|failed",
    "coverage": "passed|failed",
    "lint": "passed|failed"
  }
}
```

Also save a copy as `coordination/quality_dashboard_previous.json` for next run's comparison.

---

## Step 13: Return Summary

Return a concise summary to the calling agent:

```
Quality Dashboard Summary:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Overall Health: {score}/100 ({level})
Trend: {overall_trend}

Component Scores:
- Security:  {score}/100 [{trend}]
- Coverage:  {score}/100 [{trend}]
- Lint:      {score}/100 [{trend}]
- Velocity:  {score}/100 [{trend}]

Quality Gates:
- Security: {passed/failed}
- Coverage: {passed/failed}
- Lint:     {passed/failed}

{If anomalies exist:}
⚠️  Anomalies Detected:
- {anomaly 1}
- {anomaly 2}

Top Recommendations:
1. {recommendation 1}
2. {recommendation 2}
3. {recommendation 3}

Details saved to: coordination/quality_dashboard.json
```

---

## Error Handling

**If all metric files missing:**
- Return: "Cannot generate dashboard - no quality metrics found. Run security-scan, test-coverage, and lint-check first."

**If only some metrics missing:**
- Calculate health score with available metrics
- Note in report: "Incomplete data: {missing components}"
- Adjust weights accordingly

**If previous dashboard not found:**
- Skip trend detection
- Note: "No baseline for trend comparison (first run)"

---

## Notes

- Health score is **weighted** - security and coverage are most important
- Trends require at least 2 runs to detect
- Anomaly detection is aggressive to catch regressions early
- Recommendations are prioritized by impact
- Quality gates are minimum standards for deployment readiness
