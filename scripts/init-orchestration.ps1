# BAZINGA Orchestration Initialization Script (PowerShell)
#
# This script creates the required folder structure and state files
# for orchestration. Safe to run multiple times (idempotent).
#
# Usage: .\.claude\scripts\init-orchestration.ps1

$ErrorActionPreference = "Stop"

# Generate session ID with timestamp
$SESSION_ID = "bazinga_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
$TIMESTAMP = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

Write-Host "🔄 Initializing BAZINGA orchestration system..." -ForegroundColor Cyan
Write-Host "📅 Session ID: $SESSION_ID" -ForegroundColor Cyan

# Ensure all required directories exist (New-Item -Force is idempotent - safe to run multiple times)
Write-Host "📁 Ensuring directory structure exists..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path "coordination\messages" -Force | Out-Null
New-Item -ItemType Directory -Path "coordination\reports" -Force | Out-Null
New-Item -ItemType Directory -Path "docs" -Force | Out-Null

# Initialize pm_state.json
if (-not (Test-Path "coordination\pm_state.json")) {
    Write-Host "📝 Creating pm_state.json..." -ForegroundColor Yellow
    @"
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
"@ | Out-File -FilePath "coordination\pm_state.json" -Encoding UTF8
} else {
    Write-Host "✓ pm_state.json already exists" -ForegroundColor Gray
}

# Initialize group_status.json
if (-not (Test-Path "coordination\group_status.json")) {
    Write-Host "📝 Creating group_status.json..." -ForegroundColor Yellow
    @"
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
"@ | Out-File -FilePath "coordination\group_status.json" -Encoding UTF8
} else {
    Write-Host "✓ group_status.json already exists" -ForegroundColor Gray
}

# Initialize orchestrator_state.json
if (-not (Test-Path "coordination\orchestrator_state.json")) {
    Write-Host "📝 Creating orchestrator_state.json..." -ForegroundColor Yellow
    @"
{
  "session_id": "$SESSION_ID",
  "current_phase": "initialization",
  "active_agents": [],
  "iteration": 0,
  "total_spawns": 0,
  "decisions_log": [],
  "status": "running",
  "start_time": "$TIMESTAMP",
  "last_update": "$TIMESTAMP"
}
"@ | Out-File -FilePath "coordination\orchestrator_state.json" -Encoding UTF8
} else {
    Write-Host "✓ orchestrator_state.json already exists" -ForegroundColor Gray
}

# Initialize skills_config.json
if (-not (Test-Path "coordination\skills_config.json")) {
    Write-Host "📝 Creating skills_config.json..." -ForegroundColor Yellow
    @"
{
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
    "velocity-tracker": "mandatory"
  },
  "_metadata": {
    "description": "Skills configuration for BAZINGA agents",
    "last_updated": "$TIMESTAMP",
    "configuration_notes": [
      "MANDATORY: Skill will be automatically invoked by the agent",
      "DISABLED: Skill will not be invoked",
      "Use /configure-skills to modify this configuration interactively"
    ]
  }
}
"@ | Out-File -FilePath "coordination\skills_config.json" -Encoding UTF8
} else {
    Write-Host "✓ skills_config.json already exists" -ForegroundColor Gray
}

# Initialize message files
$MESSAGE_FILES = @(
    "coordination\messages\dev_to_qa.json",
    "coordination\messages\qa_to_techlead.json",
    "coordination\messages\techlead_to_dev.json"
)

foreach ($msg_file in $MESSAGE_FILES) {
    if (-not (Test-Path $msg_file)) {
        Write-Host "📝 Creating $msg_file..." -ForegroundColor Yellow
        @"
{
  "messages": []
}
"@ | Out-File -FilePath $msg_file -Encoding UTF8
    } else {
        Write-Host "✓ $msg_file already exists" -ForegroundColor Gray
    }
}

# Initialize orchestration log
if (-not (Test-Path "docs\orchestration-log.md")) {
    Write-Host "📝 Creating orchestration log..." -ForegroundColor Yellow
    @"
# BAZINGA Orchestration Log

**Session:** $SESSION_ID
**Started:** $TIMESTAMP

This file tracks all agent interactions during orchestration.

---

"@ | Out-File -FilePath "docs\orchestration-log.md" -Encoding UTF8
} else {
    Write-Host "✓ orchestration-log.md already exists" -ForegroundColor Gray
}

# Create .gitignore for coordination folder if it doesn't exist
if (-not (Test-Path "coordination\.gitignore")) {
    Write-Host "📝 Creating coordination\.gitignore..." -ForegroundColor Yellow
    @"
# Coordination state files are temporary and should not be committed
*.json

# EXCEPT skills_config.json - this is permanent configuration
!skills_config.json

# Keep the folder structure
!.gitignore
"@ | Out-File -FilePath "coordination\.gitignore" -Encoding UTF8
} else {
    Write-Host "✓ coordination\.gitignore already exists" -ForegroundColor Gray
}

Write-Host ""
Write-Host "✅ Initialization complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Created structure:" -ForegroundColor Cyan
Write-Host "   coordination\"
Write-Host "   ├── pm_state.json"
Write-Host "   ├── group_status.json"
Write-Host "   ├── orchestrator_state.json"
Write-Host "   ├── skills_config.json"
Write-Host "   └── messages\"
Write-Host "       ├── dev_to_qa.json"
Write-Host "       ├── qa_to_techlead.json"
Write-Host "       └── techlead_to_dev.json"
Write-Host ""
Write-Host "   docs\"
Write-Host "   └── orchestration-log.md"
Write-Host ""
Write-Host "🚀 Ready for orchestration!" -ForegroundColor Green
