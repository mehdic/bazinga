#!/usr/bin/env bash
set +e  # Don't exit on error for graceful degradation

# Colors
RED=$'\033[0;31m'
GREEN=$'\033[0;32m'
YELLOW=$'\033[1;33m'
BLUE=$'\033[0;34m'
CYAN=$'\033[0;36m'
NC=$'\033[0m'  # No Color

# Get current session ID from database
get_current_session_id() {
    local db_path="bazinga/bazinga.db"
    if [ ! -f "$db_path" ]; then
        echo "bazinga_default"
        return
    fi

    local session_id=$(python3 -c "
import sqlite3
try:
    conn = sqlite3.connect('$db_path')
    cursor = conn.execute('SELECT session_id FROM sessions ORDER BY created_at DESC LIMIT 1')
    row = cursor.fetchone()
    if row:
        print(row[0])
    else:
        print('bazinga_default')
    conn.close()
except:
    print('bazinga_default')
" 2>/dev/null || echo "bazinga_default")

    echo "$session_id"
}

SESSION_ID=$(get_current_session_id)

# Directories
COORD_DIR="bazinga"
SKILLS_DIR="${COORD_DIR}/artifacts/${SESSION_ID}/skills"
SECURITY_FILE="${SKILLS_DIR}/security_scan.json"
COVERAGE_FILE="${SKILLS_DIR}/coverage_report.json"
LINT_FILE="${SKILLS_DIR}/lint_results.json"
METRICS_FILE="${SKILLS_DIR}/project_metrics.json"
HISTORICAL_FILE="${SKILLS_DIR}/historical_metrics.json"
DASHBOARD_FILE="${SKILLS_DIR}/quality_dashboard.json"
PREVIOUS_DASHBOARD="${SKILLS_DIR}/quality_dashboard_previous.json"

mkdir -p "$SKILLS_DIR"
echo "📁 Output directory: $SKILLS_DIR"

echo "📊 Quality Dashboard"
echo "=================================================="
echo

# Load profile from skills_config.json for graceful degradation
PROFILE="lite"
if [ -f "${COORD_DIR}/skills_config.json" ]; then
    if command -v jq &> /dev/null; then
        PROFILE=$(jq -r '._metadata.profile // "lite"' "${COORD_DIR}/skills_config.json" 2>/dev/null || echo "lite")
    fi
fi

# Check if jq is available - graceful fallback
if ! command -v jq &> /dev/null; then
    if [ "$PROFILE" = "lite" ]; then
        # Lite mode: Skip gracefully
        echo -e "${YELLOW}⚠️  jq not installed - quality dashboard skipped in lite mode${NC}"
        echo "   Install with: apt-get install jq (or brew install jq on macOS)"
        cat > "$DASHBOARD_FILE" <<EOF
{
  "status": "skipped",
  "reason": "jq not installed",
  "recommendation": "Install with: apt-get install jq (or brew install jq on macOS)",
  "impact": "Quality dashboard was skipped. Install jq for unified health metrics.",
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF
        exit 0
    else
        # Advanced mode: Fail if jq missing
        echo -e "${RED}❌ jq required but not installed${NC}"
        cat > "$DASHBOARD_FILE" <<EOF
{
  "status": "error",
  "reason": "jq required but not installed",
  "recommendation": "Install with: apt-get install jq (or brew install jq on macOS)",
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF
        exit 1
    fi
    USE_JQ=false
else
    USE_JQ=true
fi

# Save previous dashboard for trend comparison
if [ -f "$DASHBOARD_FILE" ]; then
    cp "$DASHBOARD_FILE" "$PREVIOUS_DASHBOARD"
fi

# Initialize scores
SECURITY_SCORE=100
COVERAGE_SCORE=0
LINT_SCORE=100
VELOCITY_SCORE=80

declare -a ANOMALIES
declare -a RECOMMENDATIONS

# ============================================
# 1. Analyze Security Metrics
# ============================================
echo "🔒 Analyzing security metrics..."

if [ -f "$SECURITY_FILE" ]; then
    if [ "$USE_JQ" = true ]; then
        CRITICAL_VULNS=$(jq -r '.summary.critical // 0' "$SECURITY_FILE" 2>/dev/null || echo "0")
        HIGH_VULNS=$(jq -r '.summary.high // 0' "$SECURITY_FILE" 2>/dev/null || echo "0")
        MEDIUM_VULNS=$(jq -r '.summary.medium // 0' "$SECURITY_FILE" 2>/dev/null || echo "0")
    else
        # Basic parsing without jq
        CRITICAL_VULNS=$(grep -o '"critical"[[:space:]]*:[[:space:]]*[0-9]*' "$SECURITY_FILE" 2>/dev/null | grep -o '[0-9]*$' || echo "0")
        HIGH_VULNS=$(grep -o '"high"[[:space:]]*:[[:space:]]*[0-9]*' "$SECURITY_FILE" 2>/dev/null | grep -o '[0-9]*$' || echo "0")
        MEDIUM_VULNS=$(grep -o '"medium"[[:space:]]*:[[:space:]]*[0-9]*' "$SECURITY_FILE" 2>/dev/null | grep -o '[0-9]*$' || echo "0")
    fi

    # Calculate security score
    if [ "$CRITICAL_VULNS" -gt 0 ]; then
        SECURITY_SCORE=0
        ANOMALIES+=("Critical security vulnerabilities detected ($CRITICAL_VULNS)")
        RECOMMENDATIONS+=("URGENT: Fix $CRITICAL_VULNS critical security vulnerabilities before deployment")
    else
        SECURITY_SCORE=$((100 - (HIGH_VULNS * 10) - (MEDIUM_VULNS * 2)))
        [ "$SECURITY_SCORE" -lt 0 ] && SECURITY_SCORE=0
    fi

    if [ "$HIGH_VULNS" -gt 0 ]; then
        RECOMMENDATIONS+=("Address $HIGH_VULNS high-severity security issues")
    fi

    echo "   Critical: $CRITICAL_VULNS | High: $HIGH_VULNS | Medium: $MEDIUM_VULNS"
    echo "   Security Score: $SECURITY_SCORE/100"
else
    echo "   ${YELLOW}⚠️  No security scan results found${NC}"
    SECURITY_SCORE=50  # Neutral score if no data
fi

SECURITY_TREND="stable"

# ============================================
# 2. Analyze Coverage Metrics
# ============================================
echo
echo "📈 Analyzing test coverage..."

if [ -f "$COVERAGE_FILE" ]; then
    if [ "$USE_JQ" = true ]; then
        LINE_COV=$(jq -r '.summary.line_coverage // 0' "$COVERAGE_FILE" 2>/dev/null || echo "0")
        BRANCH_COV=$(jq -r '.summary.branch_coverage // 0' "$COVERAGE_FILE" 2>/dev/null || echo "0")

        # Get uncovered files (coverage < 70%)
        UNCOVERED_FILES=$(jq -r '.files[] | select(.coverage < 70) | .name' "$COVERAGE_FILE" 2>/dev/null || echo "")
    else
        # Basic parsing
        LINE_COV=$(grep -o '"line_coverage"[[:space:]]*:[[:space:]]*[0-9.]*' "$COVERAGE_FILE" 2>/dev/null | grep -o '[0-9.]*$' || echo "0")
        BRANCH_COV=$(grep -o '"branch_coverage"[[:space:]]*:[[:space:]]*[0-9.]*' "$COVERAGE_FILE" 2>/dev/null | grep -o '[0-9.]*$' || echo "0")
        UNCOVERED_FILES=""
    fi

    # Calculate coverage score
    COVERAGE_SCORE=${LINE_COV%.*}  # Remove decimals
    if (( $(echo "$BRANCH_COV > 65" | bc -l 2>/dev/null || echo "0") )); then
        COVERAGE_SCORE=$((COVERAGE_SCORE + 5))
    fi
    [ "$COVERAGE_SCORE" -gt 100 ] && COVERAGE_SCORE=100

    if (( $(echo "$LINE_COV < 70" | bc -l 2>/dev/null || echo "1") )); then
        RECOMMENDATIONS+=("Increase test coverage to 70% (currently ${LINE_COV}%)")
    fi

    if [ -n "$UNCOVERED_FILES" ]; then
        UNCOVERED_COUNT=$(echo "$UNCOVERED_FILES" | wc -l)
        RECOMMENDATIONS+=("Add tests for $UNCOVERED_COUNT files with low coverage")
    fi

    echo "   Line Coverage: ${LINE_COV}% | Branch Coverage: ${BRANCH_COV}%"
    echo "   Coverage Score: $COVERAGE_SCORE/100"
else
    echo "   ${YELLOW}⚠️  No coverage report found${NC}"
    COVERAGE_SCORE=50  # Neutral score if no data
fi

COVERAGE_TREND="stable"

# ============================================
# 3. Analyze Lint Metrics
# ============================================
echo
echo "🔍 Analyzing code quality (lint)..."

if [ -f "$LINT_FILE" ]; then
    if [ "$USE_JQ" = true ]; then
        HIGH_LINT=$(jq -r '[.files[].issues[] | select(.severity == "high")] | length' "$LINT_FILE" 2>/dev/null || echo "0")
        MEDIUM_LINT=$(jq -r '[.files[].issues[] | select(.severity == "medium")] | length' "$LINT_FILE" 2>/dev/null || echo "0")
        LOW_LINT=$(jq -r '[.files[].issues[] | select(.severity == "low")] | length' "$LINT_FILE" 2>/dev/null || echo "0")
    else
        # Basic parsing
        HIGH_LINT=$(grep -o '"severity"[[:space:]]*:[[:space:]]*"high"' "$LINT_FILE" 2>/dev/null | wc -l || echo "0")
        MEDIUM_LINT=$(grep -o '"severity"[[:space:]]*:[[:space:]]*"medium"' "$LINT_FILE" 2>/dev/null | wc -l || echo "0")
        LOW_LINT=$(grep -o '"severity"[[:space:]]*:[[:space:]]*"low"' "$LINT_FILE" 2>/dev/null | wc -l || echo "0")
    fi

    # Calculate lint score
    LINT_SCORE=$((100 - (HIGH_LINT * 10) - (MEDIUM_LINT * 2) - (LOW_LINT / 2)))
    [ "$LINT_SCORE" -lt 0 ] && LINT_SCORE=0

    if [ "$HIGH_LINT" -gt 5 ]; then
        RECOMMENDATIONS+=("Fix $HIGH_LINT high-severity lint issues (threshold: 5)")
    fi

    TOTAL_LINT=$((HIGH_LINT + MEDIUM_LINT + LOW_LINT))
    echo "   High: $HIGH_LINT | Medium: $MEDIUM_LINT | Low: $LOW_LINT (Total: $TOTAL_LINT)"
    echo "   Lint Score: $LINT_SCORE/100"
else
    echo "   ${YELLOW}⚠️  No lint results found${NC}"
    LINT_SCORE=50  # Neutral score if no data
fi

LINT_TREND="stable"

# ============================================
# 4. Analyze Velocity Metrics
# ============================================
echo
echo "⚡ Analyzing project velocity..."

if [ -f "$METRICS_FILE" ]; then
    if [ "$USE_JQ" = true ]; then
        CURRENT_VEL=$(jq -r '.current_run.velocity // 0' "$METRICS_FILE" 2>/dev/null || echo "0")
    else
        CURRENT_VEL=$(grep -o '"velocity"[[:space:]]*:[[:space:]]*[0-9.]*' "$METRICS_FILE" 2>/dev/null | head -1 | grep -o '[0-9.]*$' || echo "0")
    fi

    if [ -f "$HISTORICAL_FILE" ]; then
        if [ "$USE_JQ" = true ]; then
            HIST_AVG_VEL=$(jq -r '.averages.velocity // 10' "$HISTORICAL_FILE" 2>/dev/null || echo "10")
        else
            HIST_AVG_VEL=$(grep -o '"velocity"[[:space:]]*:[[:space:]]*[0-9.]*' "$HISTORICAL_FILE" 2>/dev/null | head -1 | grep -o '[0-9.]*$' || echo "10")
        fi
    else
        HIST_AVG_VEL=10  # Default
    fi

    # Calculate velocity score
    if (( $(echo "$CURRENT_VEL > $HIST_AVG_VEL" | bc -l 2>/dev/null || echo "0") )); then
        VELOCITY_SCORE=100
        VELOCITY_TREND="improving"
    elif (( $(echo "$CURRENT_VEL == $HIST_AVG_VEL" | bc -l 2>/dev/null || echo "0") )); then
        VELOCITY_SCORE=80
        VELOCITY_TREND="stable"
    else
        VELOCITY_SCORE=$(echo "scale=0; ($CURRENT_VEL / $HIST_AVG_VEL) * 80" | bc 2>/dev/null || echo "60")
        VELOCITY_TREND="declining"

        if (( $(echo "$CURRENT_VEL < ($HIST_AVG_VEL * 0.5)" | bc -l 2>/dev/null || echo "0") )); then
            ANOMALIES+=("Velocity dropped below 50% of historical average")
            RECOMMENDATIONS+=("Investigate velocity decline (current: $CURRENT_VEL vs avg: $HIST_AVG_VEL)")
        fi
    fi

    echo "   Current Velocity: $CURRENT_VEL | Historical Avg: $HIST_AVG_VEL"
    echo "   Velocity Score: $VELOCITY_SCORE/100 (${VELOCITY_TREND})"
else
    echo "   ${YELLOW}⚠️  No project metrics found${NC}"
    VELOCITY_SCORE=50
fi

# ============================================
# 5. Calculate Overall Health Score
# ============================================
echo
echo "🎯 Calculating overall health..."

# Weighted average: Security 35%, Coverage 30%, Lint 20%, Velocity 15%
OVERALL_SCORE=$(echo "scale=0; ($SECURITY_SCORE * 0.35) + ($COVERAGE_SCORE * 0.30) + ($LINT_SCORE * 0.20) + ($VELOCITY_SCORE * 0.15)" | bc 2>/dev/null || echo "50")

# Determine health level
if [ "$OVERALL_SCORE" -ge 90 ]; then
    HEALTH_LEVEL="excellent"
    HEALTH_EMOJI="🟢"
elif [ "$OVERALL_SCORE" -ge 75 ]; then
    HEALTH_LEVEL="good"
    HEALTH_EMOJI="🟡"
elif [ "$OVERALL_SCORE" -ge 60 ]; then
    HEALTH_LEVEL="fair"
    HEALTH_EMOJI="🟠"
elif [ "$OVERALL_SCORE" -ge 40 ]; then
    HEALTH_LEVEL="poor"
    HEALTH_EMOJI="🔴"
else
    HEALTH_LEVEL="critical"
    HEALTH_EMOJI="❌"
fi

echo "   Overall Health Score: ${HEALTH_EMOJI} ${OVERALL_SCORE}/100 ($HEALTH_LEVEL)"

# ============================================
# 6. Detect Overall Trend
# ============================================
OVERALL_TREND="stable"
if [ -f "$PREVIOUS_DASHBOARD" ] && [ "$USE_JQ" = true ]; then
    PREV_SCORE=$(jq -r '.overall_health_score // 0' "$PREVIOUS_DASHBOARD" 2>/dev/null || echo "0")
    SCORE_DIFF=$((OVERALL_SCORE - PREV_SCORE))

    if [ "$SCORE_DIFF" -gt 5 ]; then
        OVERALL_TREND="improving"
    elif [ "$SCORE_DIFF" -lt -5 ]; then
        OVERALL_TREND="declining"
        ANOMALIES+=("Overall health score dropped by ${SCORE_DIFF#-} points")
    fi
fi

# ============================================
# 7. Check Quality Gates
# ============================================
GATE_SECURITY="passed"
GATE_COVERAGE="passed"
GATE_LINT="passed"

if [ "$CRITICAL_VULNS" -gt 0 ]; then
    GATE_SECURITY="failed"
fi

if (( $(echo "$LINE_COV < 70" | bc -l 2>/dev/null || echo "1") )); then
    GATE_COVERAGE="failed"
fi

if [ "$HIGH_LINT" -gt 5 ]; then
    GATE_LINT="failed"
fi

# ============================================
# 8. Generate JSON Output
# ============================================
echo
echo "💾 Saving dashboard to $DASHBOARD_FILE..."

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Build anomalies JSON array
ANOMALIES_JSON="[]"
if [ ${#ANOMALIES[@]} -gt 0 ]; then
    ANOMALIES_JSON=$(printf '%s\n' "${ANOMALIES[@]}" | jq -R . | jq -s . 2>/dev/null || echo '[]')
fi

# Build recommendations JSON array
REC_JSON="[]"
if [ ${#RECOMMENDATIONS[@]} -gt 0 ]; then
    REC_JSON=$(printf '%s\n' "${RECOMMENDATIONS[@]}" | jq -R . | jq -s . 2>/dev/null || echo '[]')
fi

# Create JSON output
cat > "$DASHBOARD_FILE" <<JSON
{
  "overall_health_score": $OVERALL_SCORE,
  "health_level": "$HEALTH_LEVEL",
  "timestamp": "$TIMESTAMP",
  "metrics": {
    "security": {
      "score": $SECURITY_SCORE,
      "critical_issues": ${CRITICAL_VULNS:-0},
      "high_issues": ${HIGH_VULNS:-0},
      "medium_issues": ${MEDIUM_VULNS:-0},
      "trend": "$SECURITY_TREND"
    },
    "coverage": {
      "score": $COVERAGE_SCORE,
      "line_coverage": ${LINE_COV:-0},
      "branch_coverage": ${BRANCH_COV:-0},
      "trend": "$COVERAGE_TREND"
    },
    "lint": {
      "score": $LINT_SCORE,
      "total_issues": $((${HIGH_LINT:-0} + ${MEDIUM_LINT:-0} + ${LOW_LINT:-0})),
      "high_severity": ${HIGH_LINT:-0},
      "medium_severity": ${MEDIUM_LINT:-0},
      "low_severity": ${LOW_LINT:-0},
      "trend": "$LINT_TREND"
    },
    "velocity": {
      "score": $VELOCITY_SCORE,
      "current": ${CURRENT_VEL:-0},
      "historical_avg": ${HIST_AVG_VEL:-10},
      "trend": "$VELOCITY_TREND"
    },
    "quality_trend": "$OVERALL_TREND"
  },
  "anomalies": $ANOMALIES_JSON,
  "recommendations": $REC_JSON,
  "quality_gates_status": {
    "security": "$GATE_SECURITY",
    "coverage": "$GATE_COVERAGE",
    "lint": "$GATE_LINT"
  }
}
JSON

echo "✅ Dashboard generated successfully!"
echo
echo "=================================================="
echo "${HEALTH_EMOJI} Overall Health: $OVERALL_SCORE/100 ($HEALTH_LEVEL, $OVERALL_TREND)"
echo "=================================================="

if [ ${#ANOMALIES[@]} -gt 0 ]; then
    echo
    echo "⚠️  Anomalies Detected:"
    for anomaly in "${ANOMALIES[@]}"; do
        echo "   - $anomaly"
    done
fi

if [ ${#RECOMMENDATIONS[@]} -gt 0 ]; then
    echo
    echo "💡 Recommendations:"
    for rec in "${RECOMMENDATIONS[@]}"; do
        echo "   - $rec"
    done
fi

echo
echo "📄 Full dashboard: bazinga/quality_dashboard.json"
