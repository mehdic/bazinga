#!/bin/bash
#
# BAZINGA Orchestration Initialization Script
#
# This script creates the required folder structure and state files
# for orchestration. Safe to run multiple times (idempotent).
#
# Usage:
#   ./.claude/scripts/init-orchestration.sh           # Resume existing or create new
#   ./.claude/scripts/init-orchestration.sh --new     # Force new session
#

set -e  # Exit on error

# Check for --new flag to force new session
FORCE_NEW=false
if [ "$1" = "--new" ]; then
    FORCE_NEW=true
fi

# Ensure all required directories exist (mkdir -p is idempotent - safe to run multiple times)
echo "🔄 Initializing BAZINGA Claude Code Multi-Agent Development Team..."
mkdir -p bazinga/messages
mkdir -p bazinga/reports
mkdir -p docs

# Check if this is an existing session or new session
if [ "$FORCE_NEW" = true ]; then
    # Force new session - archive old one first
    if [ -f "bazinga/orchestrator_state.json" ]; then
        OLD_SESSION=$(python3 -c "import json; print(json.load(open('bazinga/orchestrator_state.json')).get('session_id', 'unknown'))" 2>/dev/null || echo "unknown")
        echo "🗂️  Archiving old session: $OLD_SESSION"
        ARCHIVE_DIR="bazinga/archive/$OLD_SESSION"
        mkdir -p "$ARCHIVE_DIR"

        # Archive coordination state files
        mv bazinga/*.json "$ARCHIVE_DIR/" 2>/dev/null || true
        mv bazinga/messages/*.json "$ARCHIVE_DIR/" 2>/dev/null || true

        # Archive old log file
        if [ -f "docs/orchestration-log.md" ]; then
            mv docs/orchestration-log.md "$ARCHIVE_DIR/orchestration-log.md"
            echo "   Archived old log file"
        fi
    fi
    SESSION_ID="bazinga_$(date +%Y%m%d_%H%M%S)"
    echo "📅 Starting new session: $SESSION_ID"
elif [ -f "bazinga/orchestrator_state.json" ]; then
    # Existing session - read the session ID from existing file
    SESSION_ID=$(python3 -c "import json; print(json.load(open('bazinga/orchestrator_state.json')).get('session_id', 'unknown'))" 2>/dev/null || echo "unknown")
    if [ "$SESSION_ID" = "unknown" ]; then
        # File exists but no session_id, generate one
        SESSION_ID="bazinga_$(date +%Y%m%d_%H%M%S)"
        echo "📅 Creating new session ID: $SESSION_ID"
    else
        echo "📂 Resuming existing session: $SESSION_ID"
    fi
else
    # New session - generate fresh session ID
    SESSION_ID="bazinga_$(date +%Y%m%d_%H%M%S)"
    echo "📅 Creating new session: $SESSION_ID"
fi

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Initialize pm_state.json
if [ ! -f "bazinga/pm_state.json" ]; then
    echo "📝 Creating pm_state.json..."
    cat > bazinga/pm_state.json <<EOF
{
  "session_id": "$SESSION_ID",
  "mode": null,
  "original_requirements": "",
  "task_groups": [],
  "completed_groups": [],
  "in_progress_groups": [],
  "pending_groups": [],
  "iteration": 0,
  "last_update": "$TIMESTAMP"
}
EOF
else
    echo "✓ pm_state.json already exists"
fi

# Initialize group_status.json
if [ ! -f "bazinga/group_status.json" ]; then
    echo "📝 Creating group_status.json..."
    cat > bazinga/group_status.json <<EOF
{
  "_comment": "Tracks per-group status including revision counts for opus escalation",
  "_format": {
    "group_id": {
      "status": "pending|in_progress|completed",
      "revision_count": 0,
      "last_review_status": "APPROVED|CHANGES_REQUESTED|null"
    }
  }
}
EOF
else
    echo "✓ group_status.json already exists"
fi

# Initialize orchestrator_state.json
if [ ! -f "bazinga/orchestrator_state.json" ]; then
    echo "📝 Creating orchestrator_state.json..."
    cat > bazinga/orchestrator_state.json <<EOF
{
  "session_id": "$SESSION_ID",
  "current_phase": "initialization",
  "active_agents": [],
  "iteration": 0,
  "total_spawns": 0,
  "decisions_log": [],
  "token_usage": {
    "total_estimated": 0,
    "by_agent_type": {
      "pm": 0,
      "developer": 0,
      "qa": 0,
      "tech_lead": 0
    },
    "by_group": {},
    "method": "character_count_estimate"
  },
  "status": "running",
  "start_time": "$TIMESTAMP",
  "last_update": "$TIMESTAMP"
}
EOF
else
    echo "✓ orchestrator_state.json already exists"
fi

# Initialize skills_config.json (Lite Profile by default)
if [ ! -f "bazinga/skills_config.json" ]; then
    echo "📝 Creating skills_config.json (lite profile)..."
    cat > bazinga/skills_config.json <<EOF
{
  "_metadata": {
    "profile": "lite",
    "version": "2.0",
    "description": "Lite profile - core skills only for fast development",
    "created": "$TIMESTAMP",
    "last_updated": "$TIMESTAMP",
    "configuration_notes": [
      "MANDATORY: Skill will be automatically invoked by the agent (always runs)",
      "OPTIONAL: Skill can be invoked by agent if needed (framework-driven, not automatic)",
      "DISABLED: Skill will not be invoked (not available to agent)",
      "Use /bazinga.configure-skills to modify this configuration interactively",
      "LITE PROFILE: 3 mandatory core skills + optional framework skills",
      "ADVANCED PROFILE: All 10 skills enabled - use --profile advanced during init"
    ]
  },
  "developer": {
    "lint-check": "mandatory",
    "codebase-analysis": "optional",
    "test-pattern-analysis": "optional",
    "api-contract-validation": "optional",
    "db-migration-check": "optional"
  },
  "tech_lead": {
    "security-scan": "mandatory",
    "lint-check": "mandatory",
    "test-coverage": "mandatory",
    "codebase-analysis": "optional",
    "pattern-miner": "optional",
    "test-pattern-analysis": "optional"
  },
  "qa_expert": {
    "pattern-miner": "optional",
    "quality-dashboard": "optional"
  },
  "pm": {
    "velocity-tracker": "optional"
  },
  "investigator": {
    "codebase-analysis": "mandatory",
    "pattern-miner": "mandatory",
    "test-pattern-analysis": "optional",
    "security-scan": "optional"
  },
  "dashboard": {
    "dashboard_ai_diagram_enabled": false
  }
}
EOF
else
    echo "✓ skills_config.json already exists"
fi

# Initialize testing_config.json
if [ ! -f "bazinga/testing_config.json" ]; then
    echo "📝 Creating testing_config.json..."
    cat > bazinga/testing_config.json <<EOF
{
  "_testing_framework": {
    "enabled": true,
    "mode": "minimal",
    "_mode_options": ["full", "minimal", "disabled"],

    "pre_commit_validation": {
      "lint_check": true,
      "unit_tests": true,
      "build_check": true,
      "_note": "lint_check should always be true for code quality"
    },

    "test_requirements": {
      "require_integration_tests": false,
      "require_contract_tests": false,
      "require_e2e_tests": false,
      "coverage_threshold": 0,
      "_note": "These only apply when mode=full"
    },

    "qa_workflow": {
      "enable_qa_expert": false,
      "auto_route_to_qa": false,
      "qa_skills_enabled": false,
      "_note": "Disable enable_qa_expert to skip QA workflow entirely"
    }
  },

  "_metadata": {
    "description": "Testing framework configuration for BAZINGA",
    "created": "$TIMESTAMP",
    "last_updated": "$TIMESTAMP",
    "version": "1.0",
    "presets": {
      "full": "All testing enabled - complete QA workflow",
      "minimal": "Lint + unit tests only, skip QA Expert (DEFAULT)",
      "disabled": "Only lint checks - fastest iteration"
    },
    "notes": [
      "Use /bazinga.configure-testing to modify this configuration interactively",
      "Mode 'minimal' is the default - balances speed and quality (current BAZINGA default)",
      "Mode 'full' enables complete QA workflow for production-critical code",
      "Mode 'disabled' is for rapid prototyping only (lint checks still run)"
    ]
  }
}
EOF
else
    echo "✓ testing_config.json already exists"
fi

# Migrate legacy message files (renamed in tech_lead consistency fix)
declare -A LEGACY_MESSAGE_FILES=(
    ["bazinga/messages/qa_to_techlead.json"]="bazinga/messages/qa_to_tech_lead.json"
    ["bazinga/messages/techlead_to_dev.json"]="bazinga/messages/tech_lead_to_dev.json"
)

for legacy_file in "${!LEGACY_MESSAGE_FILES[@]}"; do
    new_file="${LEGACY_MESSAGE_FILES[$legacy_file]}"
    if [ -f "$legacy_file" ] && [ ! -f "$new_file" ]; then
        echo "⚠️  Migrating legacy file: $legacy_file → $new_file"
        mv "$legacy_file" "$new_file"
    fi
done

# Initialize message files
MESSAGE_FILES=(
    "bazinga/messages/dev_to_qa.json"
    "bazinga/messages/qa_to_tech_lead.json"
    "bazinga/messages/tech_lead_to_dev.json"
)

for msg_file in "${MESSAGE_FILES[@]}"; do
    if [ ! -f "$msg_file" ]; then
        echo "📝 Creating $msg_file..."
        cat > "$msg_file" <<EOF
{
  "messages": []
}
EOF
    else
        echo "✓ $msg_file already exists"
    fi
done

# Initialize orchestration log
if [ ! -f "docs/orchestration-log.md" ]; then
    echo "📝 Creating orchestration log..."
    cat > docs/orchestration-log.md <<EOF
# BAZINGA Orchestration Log

**Session:** $SESSION_ID
**Started:** $TIMESTAMP

This file tracks all agent interactions during orchestration.

---

EOF
else
    echo "✓ orchestration-log.md already exists"
fi

# Update sessions history
echo "📝 Updating sessions history..."
SESSIONS_HISTORY="bazinga/sessions_history.json"

# Initialize history file if it doesn't exist
if [ ! -f "$SESSIONS_HISTORY" ]; then
    cat > "$SESSIONS_HISTORY" <<EOF
{
  "_metadata": {
    "description": "Historical record of all orchestration sessions",
    "version": "1.0"
  },
  "sessions": []
}
EOF
fi

# Add current session to history (using Python for JSON manipulation)
python3 - <<PYTHON_SCRIPT
import json
from pathlib import Path
from datetime import datetime

history_file = Path("$SESSIONS_HISTORY")
session_id = "$SESSION_ID"
timestamp = "$TIMESTAMP"

# Load existing history
with open(history_file, 'r') as f:
    history = json.load(f)

# Check if this session already exists
session_exists = any(s.get('session_id') == session_id for s in history.get('sessions', []))

if not session_exists:
    # Add new session
    history['sessions'].append({
        'session_id': session_id,
        'start_time': timestamp,
        'status': 'started',
        'end_time': None
    })

    # Keep only last 50 sessions to prevent file from growing too large
    if len(history['sessions']) > 50:
        history['sessions'] = history['sessions'][-50:]

    # Save updated history
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=2)

    print(f"✅ Session {session_id} added to history")
else:
    print(f"✓ Session {session_id} already in history")
PYTHON_SCRIPT

# Create .gitignore for coordination folder if it doesn't exist
if [ ! -f "bazinga/.gitignore" ]; then
    echo "📝 Creating bazinga/.gitignore..."
    cat > bazinga/.gitignore <<EOF
# Coordination state files are temporary and should not be committed
*.json

# EXCEPT these files - they are permanent configuration or historical data
!skills_config.json
!testing_config.json
!sessions_history.json

# Reports are ephemeral - generated per session
reports/

# Keep the folder structure
!.gitignore
EOF
else
    echo "✓ bazinga/.gitignore already exists"
fi

# Initialize database
echo ""
echo "🗄️  Initializing BAZINGA database..."
DB_PATH="bazinga/bazinga.db"
DB_INIT_SCRIPT=".claude/skills/bazinga-db/scripts/init_db.py"
DB_CLI_SCRIPT=".claude/skills/bazinga-db/scripts/bazinga_db.py"
DB_MIGRATION_SCRIPT=".claude/skills/bazinga-db/scripts/migrate_task_groups_schema.py"

if [ -f "$DB_PATH" ]; then
    echo "✓ Database already exists"

    # Run migration if needed
    if [ -f "$DB_MIGRATION_SCRIPT" ]; then
        echo "🔄 Checking for required database migrations..."

        # Check if task_groups table has old schema (id as single PRIMARY KEY)
        # Use Python sqlite3 module instead of sqlite3 command (not always available)
        SCHEMA_CHECK=$(python3 -c "
import sqlite3
import sys
try:
    conn = sqlite3.connect('$DB_PATH')
    cursor = conn.execute(\"SELECT sql FROM sqlite_master WHERE type='table' AND name='task_groups'\")
    row = cursor.fetchone()
    if row:
        print(row[0])
    conn.close()
except Exception as e:
    print(f'Error: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null)

        if echo "$SCHEMA_CHECK" | grep -q "id TEXT PRIMARY KEY"; then
            echo "⚠️  Detected old task_groups schema - migration required"
            echo "📝 Running database migration..."
            python3 "$DB_MIGRATION_SCRIPT" --db "$DB_PATH"

            if [ $? -eq 0 ]; then
                echo "✅ Database migration completed successfully"
            else
                echo "❌ Warning: Database migration failed"
                echo "   Please run manually: python3 $DB_MIGRATION_SCRIPT --db $DB_PATH"
            fi
        else
            echo "✓ Database schema is up to date"
        fi
    fi
else
    if [ -f "$DB_INIT_SCRIPT" ]; then
        echo "📝 Creating database schema..."
        python3 "$DB_INIT_SCRIPT" "$DB_PATH"

        if [ $? -eq 0 ]; then
            echo "✅ Database initialized successfully"

            # Create session in database
            echo "📝 Creating session in database..."
            python3 "$DB_CLI_SCRIPT" --db "$DB_PATH" create-session "$SESSION_ID" "simple" "Orchestration session" 2>/dev/null

            if [ $? -eq 0 ]; then
                echo "✅ Session created in database: $SESSION_ID"
            else
                echo "⚠️  Warning: Could not create session in database"
            fi
        else
            echo "⚠️  Warning: Database initialization failed"
        fi
    else
        echo "⚠️  Warning: Database initialization script not found"
        echo "   Database will be auto-initialized on first use"
    fi
fi

# Check templates exist at bazinga/templates (installed by bazinga CLI)
if [ ! -d "bazinga/templates" ]; then
    echo ""
    echo "⚠️  Warning: bazinga/templates not found"
    echo "   Run 'bazinga update' to install templates"
else
    echo "✓ bazinga/templates exists"
fi

echo ""
echo "✅ Initialization complete!"
echo ""
echo "📊 Created structure:"
echo "   bazinga/"
echo "   ├── bazinga.db            (SQLite database - primary storage)"
echo "   ├── pm_state.json"
echo "   ├── group_status.json"
echo "   ├── orchestrator_state.json"
echo "   ├── skills_config.json"
echo "   ├── messages/"
echo "   │   ├── dev_to_qa.json"
echo "   │   ├── qa_to_tech_lead.json"
echo "   │   └── tech_lead_to_dev.json"
echo "   └── reports/              (detailed session reports)"
echo ""
echo "   docs/"
echo "   └── orchestration-log.md"
echo ""
echo "🚀 Ready for orchestration!"
echo "📊 Session ID: $SESSION_ID"
echo "🗄️  Database: bazinga/bazinga.db"
echo ""

# Check if dashboard server is running and start if needed
echo "🖥️  Checking dashboard v2 server status..."
DASHBOARD_PORT="${DASHBOARD_PORT:-3000}"
DASHBOARD_PID_FILE="bazinga/dashboard.pid"

# Check if server is already running
if [ -f "$DASHBOARD_PID_FILE" ] && kill -0 $(cat "$DASHBOARD_PID_FILE") 2>/dev/null; then
    echo "✓ Dashboard v2 server already running (PID: $(cat $DASHBOARD_PID_FILE))"
    echo "🌐 Dashboard: http://localhost:$DASHBOARD_PORT"
else
    # Check if port is in use by another process
    if lsof -Pi :$DASHBOARD_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "⚠️  Port $DASHBOARD_PORT is already in use by another process"
        echo "   Dashboard server not started. You can manually start it with:"
        echo "   cd bazinga/dashboard-v2 && npm run dev"
    else
        # Launch dashboard startup script in background
        # This script handles dependency installation and server startup asynchronously
        echo "🚀 Starting dashboard v2 server (background process)..."
        bash bazinga/scripts/start-dashboard.sh &
        echo "   Dashboard will be available at http://localhost:$DASHBOARD_PORT"
        echo "   (Installation may take a moment if dependencies need to be installed)"
        echo "   View logs: tail -f bazinga/dashboard.log"
    fi
fi
echo ""
