#!/bin/bash
set -e

# BAZINGA Coordination Folder Migration Script
# Migrates from flat structure to session-based artifacts structure

COORD_DIR="coordination"
ARTIFACTS_DIR="$COORD_DIR/artifacts"

echo "🔄 BAZINGA Coordination Structure Migration"
echo "==========================================="
echo ""

# Step 1: Detect current session ID from database
echo "📊 Step 1: Detecting current session..."
if [ -f "$COORD_DIR/bazinga.db" ]; then
    # Get most recent session ID from database
    SESSION_ID=$(python3 -c "
import sqlite3, sys
try:
    conn = sqlite3.connect('$COORD_DIR/bazinga.db')
    cursor = conn.execute('SELECT session_id FROM sessions ORDER BY created_at DESC LIMIT 1')
    row = cursor.fetchone()
    if row:
        print(row[0])
    else:
        print('bazinga_migration_' + __import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S'))
    conn.close()
except Exception as e:
    print('bazinga_migration_' + __import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S'), file=sys.stderr)
" 2>/dev/null || echo "bazinga_migration_$(date +%Y%m%d_%H%M%S)")

    echo "✓ Session ID: $SESSION_ID"
else
    echo "⚠️  No database found, using migration session ID"
    SESSION_ID="bazinga_migration_$(date +%Y%m%d_%H%M%S)"
fi

# Step 2: Create new directory structure
echo ""
echo "📁 Step 2: Creating new directory structure..."
mkdir -p "$ARTIFACTS_DIR/$SESSION_ID/skills"
mkdir -p "$COORD_DIR/templates"
echo "✓ Created artifacts/$SESSION_ID/skills/"
echo "✓ Created templates/"

# Step 3: Move skill outputs to new location
echo ""
echo "📦 Step 3: Moving skill output files..."

SKILL_FILES=(
    "security_scan.json"
    "coverage_report.json"
    "lint_results.json"
    "quality_dashboard.json"
    "project_metrics.json"
    "historical_metrics.json"
    "codebase_analysis.json"
    "test_patterns.json"
    "api_contract_validation.json"
    "db_migration_check.json"
    "pattern_insights.json"
)

for file in "${SKILL_FILES[@]}"; do
    if [ -f "$COORD_DIR/$file" ]; then
        mv "$COORD_DIR/$file" "$ARTIFACTS_DIR/$SESSION_ID/skills/$file"
        echo "✓ Moved $file → artifacts/$SESSION_ID/skills/"
    fi
done

# Step 4: Move build baselines
echo ""
echo "🔨 Step 4: Moving build baseline files..."
if [ -f "$COORD_DIR/build_baseline.log" ]; then
    mv "$COORD_DIR/build_baseline.log" "$ARTIFACTS_DIR/$SESSION_ID/"
    echo "✓ Moved build_baseline.log"
fi
if [ -f "$COORD_DIR/build_baseline_status.txt" ]; then
    mv "$COORD_DIR/build_baseline_status.txt" "$ARTIFACTS_DIR/$SESSION_ID/"
    echo "✓ Moved build_baseline_status.txt"
fi

# Step 5: Move reports
echo ""
echo "📄 Step 5: Moving reports..."
if [ -d "$COORD_DIR/reports" ]; then
    for report in "$COORD_DIR/reports"/*.md; do
        if [ -f "$report" ]; then
            filename=$(basename "$report")
            # If it's a session report, move to that session's folder
            if [[ $filename =~ session_([0-9_]+)\.md ]]; then
                report_session="${BASH_REMATCH[1]}"
                mkdir -p "$ARTIFACTS_DIR/bazinga_$report_session"
                mv "$report" "$ARTIFACTS_DIR/bazinga_$report_session/completion_report.md"
                echo "✓ Moved $filename → artifacts/bazinga_$report_session/completion_report.md"
            else
                # Other reports go to current session
                mv "$report" "$ARTIFACTS_DIR/$SESSION_ID/"
                echo "✓ Moved $filename → artifacts/$SESSION_ID/"
            fi
        fi
    done
    rmdir "$COORD_DIR/reports" 2>/dev/null && echo "✓ Removed empty reports/ folder"
fi

# Move any ad-hoc MD reports to current session
for report in "$COORD_DIR"/*.md; do
    if [ -f "$report" ] && [ "$(basename $report)" != "README.md" ]; then
        mv "$report" "$ARTIFACTS_DIR/$SESSION_ID/"
        echo "✓ Moved $(basename $report) → artifacts/$SESSION_ID/"
    fi
done

# Step 6: Clean up deprecated files
echo ""
echo "🗑️  Step 6: Cleaning up deprecated files..."

DEPRECATED_FILES=(
    "sessions_history.json"
    "pm_final_assessment.json"
    "current_requirements.txt"
    "pm_prompt.txt"
    "orchestration-final-log.md"
)

for file in "${DEPRECATED_FILES[@]}"; do
    if [ -f "$COORD_DIR/$file" ]; then
        rm "$COORD_DIR/$file"
        echo "✓ Deleted $file (now in database)"
    fi
done

# Remove messages folder
if [ -d "$COORD_DIR/messages" ]; then
    rm -rf "$COORD_DIR/messages"
    echo "✓ Deleted messages/ folder (now in database)"
fi

# Remove any other directories that aren't the new structure
for dir in "$COORD_DIR"/*/; do
    dirname=$(basename "$dir")
    if [ "$dirname" != "artifacts" ] && [ "$dirname" != "templates" ]; then
        if [ -d "$dir" ]; then
            echo "⚠️  Found unexpected directory: $dirname"
            echo "   Moving to artifacts/$SESSION_ID/$dirname/"
            mv "$dir" "$ARTIFACTS_DIR/$SESSION_ID/"
        fi
    fi
done

# Step 7: Move templates if they exist in wrong location
echo ""
echo "📝 Step 7: Organizing templates..."
if [ -f "$COORD_DIR/prompt_building.md" ]; then
    mv "$COORD_DIR/prompt_building.md" "$COORD_DIR/templates/"
    echo "✓ Moved prompt_building.md → templates/"
fi
if [ -f "$COORD_DIR/completion_report.md" ]; then
    mv "$COORD_DIR/completion_report.md" "$COORD_DIR/templates/"
    echo "✓ Moved completion_report.md → templates/"
fi
if [ -f "$COORD_DIR/message_templates.md" ]; then
    mv "$COORD_DIR/message_templates.md" "$COORD_DIR/templates/"
    echo "✓ Moved message_templates.md → templates/"
fi
if [ -f "$COORD_DIR/logging_pattern.md" ]; then
    mv "$COORD_DIR/logging_pattern.md" "$COORD_DIR/templates/"
    echo "✓ Moved logging_pattern.md → templates/"
fi

# Step 8: Summary
echo ""
echo "✅ Migration Complete!"
echo "====================="
echo ""
echo "Final structure:"
echo "coordination/"
echo "├── bazinga.db (database)"
echo "├── skills_config.json (config)"
echo "├── testing_config.json (config)"
echo "├── artifacts/"
echo "│   └── $SESSION_ID/"
echo "│       ├── skills/ ($(ls -1 $ARTIFACTS_DIR/$SESSION_ID/skills 2>/dev/null | wc -l) files)"
echo "│       └── $(ls -1 $ARTIFACTS_DIR/$SESSION_ID/*.{md,log,txt} 2>/dev/null | wc -l) other files"
echo "└── templates/ ($(ls -1 $COORD_DIR/templates 2>/dev/null | wc -l) files)"
echo ""
echo "📋 Next steps:"
echo "1. Review artifacts/$SESSION_ID/ for correctness"
echo "2. Add 'coordination/artifacts/' to .gitignore"
echo "3. Test orchestration with new structure"
echo "4. Commit changes"
