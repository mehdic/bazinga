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
mkdir -p coordination/messages
mkdir -p coordination/reports
mkdir -p docs

# Check if this is an existing session or new session
if [ "$FORCE_NEW" = true ]; then
    # Force new session - archive old one first
    if [ -f "coordination/orchestrator_state.json" ]; then
        OLD_SESSION=$(python3 -c "import json; print(json.load(open('coordination/orchestrator_state.json')).get('session_id', 'unknown'))" 2>/dev/null || echo "unknown")
        echo "🗂️  Archiving old session: $OLD_SESSION"
        ARCHIVE_DIR="coordination/archive/$OLD_SESSION"
        mkdir -p "$ARCHIVE_DIR"

        # Archive coordination state files
        mv coordination/*.json "$ARCHIVE_DIR/" 2>/dev/null || true
        mv coordination/messages/*.json "$ARCHIVE_DIR/" 2>/dev/null || true

        # Archive old log file
        if [ -f "docs/orchestration-log.md" ]; then
            mv docs/orchestration-log.md "$ARCHIVE_DIR/orchestration-log.md"
            echo "   Archived old log file"
        fi
    fi
    SESSION_ID="bazinga_$(date +%Y%m%d_%H%M%S)"
    echo "📅 Starting new session: $SESSION_ID"
elif [ -f "coordination/orchestrator_state.json" ]; then
    # Existing session - read the session ID from existing file
    SESSION_ID=$(python3 -c "import json; print(json.load(open('coordination/orchestrator_state.json')).get('session_id', 'unknown'))" 2>/dev/null || echo "unknown")
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
if [ ! -f "coordination/pm_state.json" ]; then
    echo "📝 Creating pm_state.json..."
    cat > coordination/pm_state.json <<EOF
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
if [ ! -f "coordination/group_status.json" ]; then
    echo "📝 Creating group_status.json..."
    cat > coordination/group_status.json <<EOF
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
if [ ! -f "coordination/orchestrator_state.json" ]; then
    echo "📝 Creating orchestrator_state.json..."
    cat > coordination/orchestrator_state.json <<EOF
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
if [ ! -f "coordination/skills_config.json" ]; then
    echo "📝 Creating skills_config.json (lite profile)..."
    cat > coordination/skills_config.json <<EOF
{
  "_metadata": {
    "profile": "lite",
    "version": "2.0",
    "description": "Lite profile - core skills only for fast development",
    "created": "$TIMESTAMP",
    "last_updated": "$TIMESTAMP",
    "configuration_notes": [
      "MANDATORY: Skill will be automatically invoked by the agent",
      "DISABLED: Skill will not be invoked",
      "Use /bazinga.configure-skills to modify this configuration interactively",
      "LITE PROFILE: 3 core skills (security-scan, lint-check, test-coverage)",
      "ADVANCED PROFILE: All 10 skills enabled - use --profile advanced during init"
    ]
  },
  "developer": {
    "lint-check": "mandatory",
    "codebase-analysis": "disabled",
    "test-pattern-analysis": "disabled",
    "api-contract-validation": "disabled",
    "db-migration-check": "disabled"
  },
  "tech_lead": {
    "security-scan": "mandatory",
    "lint-check": "mandatory",
    "test-coverage": "mandatory"
  },
  "qa_expert": {
    "pattern-miner": "disabled",
    "quality-dashboard": "disabled"
  },
  "pm": {
    "velocity-tracker": "disabled"
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
if [ ! -f "coordination/testing_config.json" ]; then
    echo "📝 Creating testing_config.json..."
    cat > coordination/testing_config.json <<EOF
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

# Initialize message files
MESSAGE_FILES=(
    "coordination/messages/dev_to_qa.json"
    "coordination/messages/qa_to_techlead.json"
    "coordination/messages/techlead_to_dev.json"
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
SESSIONS_HISTORY="coordination/sessions_history.json"

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
if [ ! -f "coordination/.gitignore" ]; then
    echo "📝 Creating coordination/.gitignore..."
    cat > coordination/.gitignore <<EOF
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
    echo "✓ coordination/.gitignore already exists"
fi

echo ""
echo "✅ Initialization complete!"
echo ""
echo "📊 Created structure:"
echo "   coordination/"
echo "   ├── pm_state.json"
echo "   ├── group_status.json"
echo "   ├── orchestrator_state.json"
echo "   ├── skills_config.json"
echo "   ├── messages/"
echo "   │   ├── dev_to_qa.json"
echo "   │   ├── qa_to_techlead.json"
echo "   │   └── techlead_to_dev.json"
echo "   └── reports/              (detailed session reports)"
echo ""
echo "   docs/"
echo "   └── orchestration-log.md"
echo ""
echo "🚀 Ready for orchestration!"
echo ""

# Check if dashboard server is running and start if needed
echo "🖥️  Checking dashboard server status..."
DASHBOARD_PORT="${DASHBOARD_PORT:-53124}"
DASHBOARD_PID_FILE="/tmp/bazinga-dashboard.pid"

# Check if server is already running
if [ -f "$DASHBOARD_PID_FILE" ] && kill -0 $(cat "$DASHBOARD_PID_FILE") 2>/dev/null; then
    echo "✓ Dashboard server already running (PID: $(cat $DASHBOARD_PID_FILE))"
    echo "🌐 Dashboard: http://localhost:$DASHBOARD_PORT"
else
    # Check if port is in use by another process
    if lsof -Pi :$DASHBOARD_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "⚠️  Port $DASHBOARD_PORT is already in use by another process"
        echo "   Dashboard server not started. You can manually start it with:"
        echo "   cd dashboard && python3 server.py"
    else
        # Launch dashboard startup script in background
        # This script handles dependency installation and server startup asynchronously
        echo "🚀 Starting dashboard server (background process)..."
        bash .claude/scripts/start-dashboard.sh &
        echo "   Dashboard will be available at http://localhost:$DASHBOARD_PORT"
        echo "   (Installation may take a moment if dependencies need to be installed)"
        echo "   View logs: tail -f /tmp/bazinga-dashboard.log"
    fi
fi
echo ""
