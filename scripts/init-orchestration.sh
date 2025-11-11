#!/bin/bash
#
# BAZINGA Orchestration Initialization Script
#
# This script creates the required folder structure and state files
# for orchestration. Safe to run multiple times (idempotent).
#
# Usage: ./.claude/scripts/init-orchestration.sh

set -e  # Exit on error

# Generate session ID with timestamp
SESSION_ID="bazinga_$(date +%Y%m%d_%H%M%S)"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

echo "🔄 Initializing BAZINGA orchestration system..."
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

# Create .gitignore for coordination folder if it doesn't exist
if [ ! -f "coordination/.gitignore" ]; then
    echo "📝 Creating coordination/.gitignore..."
    cat > coordination/.gitignore <<EOF
# Coordination state files are temporary and should not be committed
*.json

# EXCEPT these files - they are permanent configuration
!skills_config.json
!testing_config.json

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
