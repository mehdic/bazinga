# Coordination Folder Structure Analysis

## Current File Writes by Component

### Skills (12 total)
1. **security-scan**: `coordination/security_scan.json`
2. **test-coverage**: `coordination/coverage_report.json`
3. **lint-check**: `coordination/lint_results.json`
4. **quality-dashboard**: `coordination/quality_dashboard.json`
5. **velocity-tracker**: `coordination/project_metrics.json` + `coordination/historical_metrics.json`
6. **codebase-analysis**: `coordination/codebase_analysis.json`
7. **test-pattern-analysis**: `coordination/test_patterns.json`
8. **api-contract-validation**: `coordination/api_contract_validation.json`
9. **db-migration-check**: `coordination/db_migration_check.json`
10. **pattern-miner**: `coordination/pattern_insights.json`
11. **bazinga-db**: `coordination/bazinga.db` (+ .shm, .wal)
12. **skill-creator**: No files (just creates skill folders)

### Orchestrator
- `coordination/build_baseline.log` (during initialization)
- `coordination/build_baseline_status.txt` (during initialization)
- `coordination/reports/session_{TIMESTAMP}.md` (at completion)

### Agents
- **project_manager**: Uses database only (no file writes)
- **developer**: Uses database only (no file writes)
- **qa_expert**: Uses database only (no file writes)
- **techlead**: Uses database only (no file writes)

### Configuration (User-managed)
- `coordination/skills_config.json` (via /bazinga.configure-skills)
- `coordination/testing_config.json` (via /bazinga.configure-testing)

### Templates (Static, git-tracked)
- `coordination/templates/prompt_building.md`
- `coordination/templates/completion_report.md`
- `coordination/templates/message_templates.md`
- `coordination/templates/logging_pattern.md`

### Deprecated Files (Should be deleted)
- `sessions_history.json` → now in sessions table
- `pm_final_assessment.json` → now in state_snapshots table
- `current_requirements.txt` → now in sessions.original_requirements
- `pm_prompt.txt` → temporary, shouldn't persist
- `messages/` folder → now in orchestration_logs table
- `orchestration-final-log.md` → now in orchestration_logs table
- Various ad-hoc QA reports → should be in session artifacts

## Proposed New Structure

```
coordination/
├── bazinga.db                    # Database (all state/logs)
├── bazinga.db-shm                # SQLite temp
├── bazinga.db-wal                # SQLite temp
├── skills_config.json            # Config (git-tracked)
├── testing_config.json           # Config (git-tracked)
├── artifacts/                    # All session outputs (gitignored)
│   └── {session_id}/             # One folder per session
│       ├── completion_report.md
│       ├── build_baseline.log
│       ├── build_baseline_status.txt
│       └── skills/               # All skill outputs
│           ├── security_scan.json
│           ├── coverage_report.json
│           ├── lint_results.json
│           ├── quality_dashboard.json
│           ├── project_metrics.json
│           ├── historical_metrics.json
│           ├── codebase_analysis.json
│           ├── test_patterns.json
│           ├── api_contract_validation.json
│           ├── db_migration_check.json
│           └── pattern_insights.json
└── templates/                    # Prompt templates (git-tracked)
    ├── prompt_building.md
    ├── completion_report.md
    ├── message_templates.md
    └── logging_pattern.md
```

## Path Rules (To be enforced)

### For Skills
```python
# OLD: coordination/{skill_output}.json
# NEW: coordination/artifacts/{session_id}/skills/{skill_output}.json

SKILL_OUTPUT_PATH = "coordination/artifacts/{session_id}/skills/{filename}"
```

### For Orchestrator
```python
# Build baselines
BUILD_BASELINE_LOG = "coordination/artifacts/{session_id}/build_baseline.log"
BUILD_BASELINE_STATUS = "coordination/artifacts/{session_id}/build_baseline_status.txt"

# Completion report
COMPLETION_REPORT = "coordination/artifacts/{session_id}/completion_report.md"
```

### For Configuration
```python
# These stay at root (git-tracked)
SKILLS_CONFIG = "coordination/skills_config.json"
TESTING_CONFIG = "coordination/testing_config.json"
```

### For Templates
```python
# These stay in templates/ (git-tracked)
TEMPLATES_DIR = "coordination/templates/"
```

## Migration Strategy

1. **Create artifacts structure**: Create `artifacts/{session_id}/skills/` for current session
2. **Move current session files**: Move all skill outputs to new location
3. **Update all skills**: Change output paths to use new structure
4. **Update orchestrator**: Change report/baseline paths
5. **Clean up deprecated files**: Delete old JSON/MD files
6. **Update .gitignore**: Add `coordination/artifacts/` to gitignore

## Benefits

1. **Session Isolation**: Each session in its own folder
2. **Easy Cleanup**: Delete `artifacts/{old_session_id}/` when done
3. **Clear Organization**: `skills/` subfolder for all skill outputs
4. **No Conflicts**: Multiple sessions can't overwrite each other
5. **Simple Rules**: All artifacts → `artifacts/{session_id}/`
