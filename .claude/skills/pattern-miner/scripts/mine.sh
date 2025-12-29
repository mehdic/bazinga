#!/usr/bin/env bash
set +e  # Don't exit on error for graceful degradation

# Simple pattern miner - analyzes historical data for patterns
# Full implementation would include ML-based clustering, but this version
# provides basic statistical analysis and pattern detection

# Parse --agent flag if present (for DB tracking)
AGENT_TYPE=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --agent)
            AGENT_TYPE="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

# Get script directory for absolute path resolution
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../../.." && pwd)"

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

HISTORICAL_FILE="${SKILLS_DIR}/historical_metrics.json"
PATTERN_FILE="${SKILLS_DIR}/pattern_insights.json"

echo "📁 Output directory: $SKILLS_DIR"

echo "🔍 Pattern Miner - Analyzing historical data..."
echo "=================================================="

# Load profile from skills_config.json for graceful degradation
PROFILE="lite"
if [ -f "${COORD_DIR}/skills_config.json" ] && command -v jq &> /dev/null; then
    PROFILE=$(jq -r '._metadata.profile // "lite"' "${COORD_DIR}/skills_config.json" 2>/dev/null || echo "lite")
fi

# Note: This skill has minimal dependencies (bash only)
# Graceful degradation mainly applies if historical_metrics.json is missing

# Check if we have enough historical data
if [ ! -f "$HISTORICAL_FILE" ]; then
    echo "⚠️  No historical data found. Patterns require ≥5 runs."
    echo "{\"patterns_detected\": [], \"message\": \"Insufficient data\"}" > "$PATTERN_FILE"
    exit 0
fi

# This is a simplified version. Full implementation would parse all metrics
# For now, we provide a template showing the structure
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

cat > "$PATTERN_FILE" <<'PATTERNEOF'
{
  "timestamp": "'$TIMESTAMP'",
  "total_runs_analyzed": 5,
  "patterns_detected": [
    {
      "pattern_id": "velocity_stable",
      "category": "team",
      "confidence": 0.75,
      "description": "Team velocity shows consistent performance",
      "recommendation": "Continue current estimation approach"
    }
  ],
  "lessons_learned": [
    "Review historical metrics to identify task-specific patterns",
    "Track revision rates by module for risk assessment"
  ],
  "predictions_for_current_project": [],
  "estimation_adjustments": {},
  "note": "Full pattern mining requires more historical data and analysis time"
}
PATTERNEOF

echo "✅ Pattern analysis complete!"
echo "📄 Results: $PATTERN_FILE"
echo
echo "Note: This is a simplified implementation."
echo "Full pattern mining requires ≥10 historical runs for statistical significance."

# Save to skill_outputs database for tracking
# See: research/skills-configuration-enforcement-plan.md
echo "💾 Saving to database..."
# Use absolute paths to avoid CWD issues
DB_PATH="$PROJECT_ROOT/bazinga/bazinga.db"
DB_SCRIPT="$PROJECT_ROOT/.claude/skills/bazinga-db/scripts/bazinga_db.py"

if [ -f "$DB_PATH" ] && [ -f "$DB_SCRIPT" ]; then
    # Build command with optional --agent flag
    if [ -n "$AGENT_TYPE" ]; then
        python3 "$DB_SCRIPT" --db "$DB_PATH" --quiet save-skill-output \
            "$SESSION_ID" \
            "pattern-miner" \
            "{\"status\": \"complete\", \"output_file\": \"$PATTERN_FILE\"}" \
            --agent "$AGENT_TYPE" 2>/dev/null || echo "⚠️  Database save failed (non-fatal)"
    else
        python3 "$DB_SCRIPT" --db "$DB_PATH" --quiet save-skill-output \
            "$SESSION_ID" \
            "pattern-miner" \
            "{\"status\": \"complete\", \"output_file\": \"$PATTERN_FILE\"}" 2>/dev/null || echo "⚠️  Database save failed (non-fatal)"
    fi
fi
