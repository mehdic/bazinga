#!/bin/bash
#
# V4 Orchestration Initialization Script
#
# This script creates the required folder structure and state files
# for V4 orchestration. Safe to run multiple times (idempotent).
#
# Usage: ./.claude/scripts/init-orchestration.sh

set -e  # Exit on error

# Generate session ID with timestamp
SESSION_ID="v4_$(date +%Y%m%d_%H%M%S)"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

echo "🔄 Initializing V4 orchestration system..."
echo "📅 Session ID: $SESSION_ID"

# Ensure all required directories exist (mkdir -p is idempotent - safe to run multiple times)
echo "📁 Ensuring directory structure exists..."
mkdir -p coordination/messages
mkdir -p coordination/reports
mkdir -p docs

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
# V4 Orchestration Log

**Session:** $SESSION_ID
**Started:** $TIMESTAMP

This file tracks all agent interactions during V4 orchestration.

---

EOF
else
    echo "✓ orchestration-log.md already exists"
fi

# Create .gitignore for coordination folder if it doesn't exist
if [ ! -f "coordination/.gitignore" ]; then
    echo "📝 Creating coordination/.gitignore..."
    cat > coordination/.gitignore <<EOF
# Coordination state files are temporary and should not be committed
*.json
orchestration-log.md

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
