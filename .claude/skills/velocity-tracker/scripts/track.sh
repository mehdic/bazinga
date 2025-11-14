#!/usr/bin/env bash
set +e  # Don't exit on error for graceful degradation

# Velocity & Metrics Tracker
# Analyzes PM state to calculate velocity, cycle times, and trends

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

COORD_DIR="bazinga"
SKILLS_DIR="${COORD_DIR}/artifacts/${SESSION_ID}/skills"
mkdir -p "$SKILLS_DIR"

# Database paths
DB_SCRIPT=".claude/skills/bazinga-db/scripts/bazinga_db.py"
DB_PATH="${COORD_DIR}/bazinga.db"

METRICS_FILE="${SKILLS_DIR}/project_metrics.json"
HISTORICAL_FILE="${SKILLS_DIR}/historical_metrics.json"

echo "📁 Output directory: $SKILLS_DIR"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "📊 Velocity & Metrics Tracker"
echo "=================================================="

# Ensure coordination directory exists
mkdir -p "${COORD_DIR}"

# Load profile from skills_config.json for graceful degradation
PROFILE="lite"
if [ -f "${COORD_DIR}/skills_config.json" ] && command -v jq &> /dev/null; then
    PROFILE=$(jq -r '._metadata.profile // "lite"' "${COORD_DIR}/skills_config.json" 2>/dev/null || echo "lite")
fi

# Check if jq is available
if ! command -v jq &> /dev/null; then
    if [ "$PROFILE" = "lite" ]; then
        # Lite mode: Skip gracefully
        echo -e "${YELLOW}⚠️  jq not installed - velocity tracking skipped in lite mode${NC}"
        echo "   Install with: apt-get install jq (or brew install jq on macOS)"
        cat > "$METRICS_FILE" <<EOF
{
  "status": "skipped",
  "reason": "jq not installed",
  "recommendation": "Install with: apt-get install jq (or brew install jq on macOS)",
  "impact": "Velocity tracking was skipped. Install jq for project metrics.",
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF
        exit 0
    else
        # Advanced mode: Fail if jq missing
        echo -e "${RED}❌ jq required but not installed${NC}"
        cat > "$METRICS_FILE" <<EOF
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

# Function: Extract JSON field (with jq fallback)
extract_json() {
    local file="$1"
    local path="$2"

    if [ "$USE_JQ" = true ]; then
        jq -r "$path" "$file" 2>/dev/null || echo "null"
    else
        # Basic grep-based extraction (less robust)
        grep -o "\"${path##*.}\"[[:space:]]*:[[:space:]]*[^,}]*" "$file" | cut -d':' -f2 | tr -d ' "' | head -1 || echo "null"
    fi
}

# Fetch PM state from database
echo "📁 Reading PM state from database..."

PM_STATE_JSON=$(python3 "$DB_SCRIPT" --db "$DB_PATH" get-state "$SESSION_ID" "pm" 2>/dev/null)

# Check if PM state exists
if [ -z "$PM_STATE_JSON" ] || [ "$PM_STATE_JSON" = "null" ] || [ "$PM_STATE_JSON" = "{}" ]; then
    echo -e "${YELLOW}⚠️  No PM state found - this is the first run${NC}"
    echo ""
    echo "Creating initial metrics structure..."

    # Create minimal metrics file
    cat > "$METRICS_FILE" <<EOF
{
  "status": "first_run",
  "message": "No historical data yet. Metrics will be available after first task completion.",
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF

    echo "✓ Metrics file created: $METRICS_FILE"
    exit 0
fi

# Create a temporary file to store PM state for jq processing
PM_STATE_TEMP=$(mktemp)
echo "$PM_STATE_JSON" > "$PM_STATE_TEMP"
PM_STATE="$PM_STATE_TEMP"

echo "✓ PM state loaded from database"

# Calculate current metrics
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
TOTAL_GROUPS=0
COMPLETED_GROUPS=0
IN_PROGRESS=0
PENDING=0
TOTAL_STORY_POINTS=0
TOTAL_ITERATIONS=0

# Use jq if available for robust parsing
if [ "$USE_JQ" = true ]; then
    TOTAL_GROUPS=$(jq -r '.task_groups | length' "$PM_STATE" 2>/dev/null || echo "0")

    # Count completed groups and calculate story points
    if [ "$TOTAL_GROUPS" -gt 0 ]; then
        COMPLETED_GROUPS=$(jq -r '[.task_groups[] | select(.status == "COMPLETED")] | length' "$PM_STATE" 2>/dev/null || echo "0")
        IN_PROGRESS=$(jq -r '[.task_groups[] | select(.status == "IN_PROGRESS")] | length' "$PM_STATE" 2>/dev/null || echo "0")

        # Sum story points from completed groups (default 3 points per group if not specified)
        TOTAL_STORY_POINTS=$(jq -r '[.task_groups[] | select(.status == "COMPLETED") | (.story_points // 3)] | add // 0' "$PM_STATE" 2>/dev/null || echo "0")

        # Average iterations (revisions)
        TOTAL_ITERATIONS=$(jq -r '[.task_groups[] | select(.status == "COMPLETED") | (.iterations // 1)] | add // 0' "$PM_STATE" 2>/dev/null || echo "0")
    fi
else
    # Fallback: basic counting
    TOTAL_GROUPS=$(grep -c '"id"' "$PM_STATE" 2>/dev/null || echo "0")
    COMPLETED_GROUPS=$(grep -c '"COMPLETED"' "$PM_STATE" 2>/dev/null || echo "0")
    TOTAL_STORY_POINTS=$((COMPLETED_GROUPS * 3))  # Default 3 points per group
    TOTAL_ITERATIONS=$COMPLETED_GROUPS
fi

PENDING=$((TOTAL_GROUPS - COMPLETED_GROUPS - IN_PROGRESS))
[ $PENDING -lt 0 ] && PENDING=0

# Calculate percentage complete
if [ "$TOTAL_GROUPS" -gt 0 ]; then
    PERCENT_COMPLETE=$((COMPLETED_GROUPS * 100 / TOTAL_GROUPS))
else
    PERCENT_COMPLETE=0
fi

# Calculate average iterations (revision rate)
if [ "$COMPLETED_GROUPS" -gt 0 ]; then
    REVISION_RATE=$(echo "scale=2; $TOTAL_ITERATIONS / $COMPLETED_GROUPS" | bc 2>/dev/null || echo "1.0")
else
    REVISION_RATE="0.0"
fi

echo "   Total groups: $TOTAL_GROUPS"
echo "   Completed: $COMPLETED_GROUPS"
echo "   In progress: $IN_PROGRESS"
echo "   Pending: $PENDING"
echo "   Velocity: $TOTAL_STORY_POINTS story points"

# Load historical metrics if available
echo ""
echo "📊 Analyzing historical trends..."

HISTORICAL_VELOCITY="0.0"
HISTORICAL_CYCLE_TIME="0"
HISTORICAL_REVISION_RATE="1.0"
TOTAL_RUNS=0
VELOCITY_TREND="stable"
QUALITY_TREND="stable"

if [ -f "$HISTORICAL_FILE" ] && [ "$USE_JQ" = true ]; then
    TOTAL_RUNS=$(jq -r '.total_runs // 0' "$HISTORICAL_FILE" 2>/dev/null || echo "0")
    HISTORICAL_VELOCITY=$(jq -r '.average_velocity // 0' "$HISTORICAL_FILE" 2>/dev/null || echo "0.0")
    HISTORICAL_REVISION_RATE=$(jq -r '.average_revision_rate // 1.0' "$HISTORICAL_FILE" 2>/dev/null || echo "1.0")

    echo "   Historical average velocity: $HISTORICAL_VELOCITY"
    echo "   Historical revision rate: $HISTORICAL_REVISION_RATE"

    # Determine trends
    if (( $(echo "$TOTAL_STORY_POINTS > $HISTORICAL_VELOCITY * 1.1" | bc -l 2>/dev/null || echo "0") )); then
        VELOCITY_TREND="improving"
    elif (( $(echo "$TOTAL_STORY_POINTS < $HISTORICAL_VELOCITY * 0.9" | bc -l 2>/dev/null || echo "0") )); then
        VELOCITY_TREND="declining"
    fi

    if (( $(echo "$REVISION_RATE < $HISTORICAL_REVISION_RATE * 0.9" | bc -l 2>/dev/null || echo "0") )); then
        QUALITY_TREND="improving"
    elif (( $(echo "$REVISION_RATE > $HISTORICAL_REVISION_RATE * 1.1" | bc -l 2>/dev/null || echo "0") )); then
        QUALITY_TREND="declining"
    fi
else
    echo "   No historical data available yet"
fi

# Generate recommendations
RECOMMENDATIONS=""
WARNINGS=""

if [ "$TOTAL_STORY_POINTS" -gt 0 ]; then
    if [ "$VELOCITY_TREND" = "improving" ]; then
        RECOMMENDATIONS="Current velocity ($TOTAL_STORY_POINTS) exceeds historical average - excellent progress"
    elif [ "$VELOCITY_TREND" = "declining" ]; then
        WARNINGS="⚠️ Velocity declining - current ($TOTAL_STORY_POINTS) below historical average ($HISTORICAL_VELOCITY)"
    fi
fi

if [ "$QUALITY_TREND" = "improving" ]; then
    RECOMMENDATIONS="${RECOMMENDATIONS}\nQuality trend improving - fewer revisions per task"
elif [ "$QUALITY_TREND" = "declining" ]; then
    WARNINGS="${WARNINGS}\n⚠️ Quality declining - more revisions required per task"
fi

# Write metrics file
echo ""
echo "💾 Writing metrics..."

cat > "$METRICS_FILE" <<EOF
{
  "timestamp": "$TIMESTAMP",
  "current_run": {
    "total_groups": $TOTAL_GROUPS,
    "completed_groups": $COMPLETED_GROUPS,
    "in_progress": $IN_PROGRESS,
    "pending": $PENDING,
    "percent_complete": $PERCENT_COMPLETE,
    "velocity": $TOTAL_STORY_POINTS,
    "revision_rate": $REVISION_RATE
  },
  "historical_metrics": {
    "total_runs": $TOTAL_RUNS,
    "average_velocity": $HISTORICAL_VELOCITY,
    "average_revision_rate": $HISTORICAL_REVISION_RATE
  },
  "trends": {
    "velocity": "$VELOCITY_TREND",
    "quality": "$QUALITY_TREND"
  },
  "recommendations": [
    $(echo -e "$RECOMMENDATIONS" | sed 's/^/    "/;s/$/",/' | head -c -2)
  ],
  "warnings": [
    $(echo -e "$WARNINGS" | sed 's/^/    "/;s/$/",/' | head -c -2)
  ]
}
EOF

echo "✓ Metrics written to: $METRICS_FILE"

# Update historical metrics
if [ "$COMPLETED_GROUPS" -gt 0 ]; then
    echo ""
    echo "📈 Updating historical data..."

    NEW_TOTAL_RUNS=$((TOTAL_RUNS + 1))

    # Calculate new averages
    if [ "$TOTAL_RUNS" -gt 0 ]; then
        NEW_AVG_VELOCITY=$(echo "scale=2; ($HISTORICAL_VELOCITY * $TOTAL_RUNS + $TOTAL_STORY_POINTS) / $NEW_TOTAL_RUNS" | bc 2>/dev/null || echo "$TOTAL_STORY_POINTS")
        NEW_AVG_REVISION=$(echo "scale=2; ($HISTORICAL_REVISION_RATE * $TOTAL_RUNS + $REVISION_RATE) / $NEW_TOTAL_RUNS" | bc 2>/dev/null || echo "$REVISION_RATE")
    else
        NEW_AVG_VELOCITY="$TOTAL_STORY_POINTS"
        NEW_AVG_REVISION="$REVISION_RATE"
    fi

    cat > "$HISTORICAL_FILE" <<EOF
{
  "total_runs": $NEW_TOTAL_RUNS,
  "average_velocity": $NEW_AVG_VELOCITY,
  "average_revision_rate": $NEW_AVG_REVISION,
  "last_updated": "$TIMESTAMP"
}
EOF

    echo "✓ Historical metrics updated"
fi

# Display summary
echo ""
echo "=================================================="
echo -e "${GREEN}✓ Metrics analysis complete!${NC}"
echo ""
echo "📊 Summary:"
echo "   Progress: $PERCENT_COMPLETE%"
echo "   Velocity: $TOTAL_STORY_POINTS story points"
echo "   Trend: $VELOCITY_TREND"

if [ -n "$WARNINGS" ]; then
    echo ""
    echo -e "${RED}Warnings:${NC}"
    echo -e "$WARNINGS"
fi

if [ -n "$RECOMMENDATIONS" ]; then
    echo ""
    echo -e "${GREEN}Recommendations:${NC}"
    echo -e "$RECOMMENDATIONS"
fi

echo ""
echo "📄 Full metrics: $METRICS_FILE"

# Clean up temporary PM state file
if [ -f "$PM_STATE_TEMP" ]; then
    rm -f "$PM_STATE_TEMP"
fi
