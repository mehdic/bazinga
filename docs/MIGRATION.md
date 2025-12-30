# Migration Guide: BAZINGA v1.0 to v1.1

This guide helps users migrating from earlier versions of BAZINGA (v1.0.x or documentation referencing v2.0.0) to the current v1.1.0 release.

---

## What Changed

### State Management: JSON Files → SQLite Database

**Before (v1.0):**
```
bazinga/
├── pm_state.json           # PM planning
├── group_status.json       # Task status
├── orchestrator_state.json # Routing state
├── security_scan.json      # Results
├── coverage_report.json    # Results
└── lint_results.json       # Results
```

**After (v1.1):**
```
bazinga/
├── bazinga.db             # SQLite database (all state)
├── project_context.json   # Tech stack detection
├── model_selection.json   # Agent model config
├── skills_config.json     # Skills config
└── challenge_levels.json  # QA progression
```

### Why This Changed

1. **Concurrent access** - SQLite handles multiple agent writes without file corruption
2. **Structured queries** - Complex state lookups are now efficient
3. **Transaction support** - Atomic updates prevent partial writes
4. **Better audit trail** - Complete history in one place

### How to Access State

**Before:**
```bash
cat bazinga/pm_state.json | jq '.task_groups'
```

**After:**
```bash
# Use the bazinga-db skill
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet get-task-groups <SESSION_ID>

# Or query directly (for debugging only)
sqlite3 bazinga/bazinga.db "SELECT * FROM task_groups WHERE session_id='<SESSION_ID>';"
```

---

## Agent Count: 5-8 → 9

Documentation previously mentioned varying agent counts. The actual agent roster is:

| Agent | Role | New in v1.1? |
|-------|------|--------------|
| Orchestrator | Routes messages | No |
| Tech Stack Scout | Detects project tech | **Yes** |
| Project Manager | Plans and coordinates | No |
| Requirements Engineer | Clarifies requirements | No |
| Developer | Implements code | No |
| Senior Software Engineer | Complex tasks | No |
| QA Expert | Testing | No |
| Tech Lead | Code review | No |
| Investigator | Deep investigation | No |

**Total: 9 agents**

---

## Skills Count: 10-11 → 18

The system now has 18 skills total:

### User-Configurable Skills (10)

These can be enabled/disabled via `/bazinga.configure-skills`:

1. lint-check
2. security-scan
3. test-coverage
4. codebase-analysis
5. test-pattern-analysis
6. api-contract-validation
7. db-migration-check
8. pattern-miner
9. quality-dashboard
10. velocity-tracker

### Internal Orchestration Skills (8)

These run automatically and cannot be disabled:

1. **bazinga-db** - Database operations
2. **prompt-builder** - Dynamic prompt composition
3. **specialization-loader** - Tech-specific expertise loading
4. **context-assembler** - Context management
5. **workflow-router** - State machine routing
6. **config-seeder** - Configuration initialization
7. **bazinga-validator** - Completion validation
8. **skill-creator** - Skill development guide

---

## Project Structure Changes

### New Files

| File | Purpose |
|------|---------|
| `bazinga/bazinga.db` | SQLite database |
| `bazinga/project_context.json` | Tech stack detection output |
| `bazinga/model_selection.json` | Agent model assignments |
| `bazinga/challenge_levels.json` | QA test progression |
| `bazinga/templates/` | Specialization templates |

### Removed Files

These JSON state files are no longer used:

| File | Replacement |
|------|-------------|
| `pm_state.json` | `bazinga.db` → `sessions` + `task_groups` tables |
| `group_status.json` | `bazinga.db` → `task_groups` table |
| `orchestrator_state.json` | `bazinga.db` → `orchestration_logs` table |
| `security_scan.json` | Stored in skill output (temporary) |
| `coverage_report.json` | Stored in skill output (temporary) |
| `lint_results.json` | Stored in skill output (temporary) |

---

## Upgrade Steps

### For Existing Projects

If you have a project initialized with an earlier version:

```bash
# 1. Update BAZINGA CLI
pip install --upgrade git+https://github.com/mehdic/bazinga.git

# 2. Update project files
bazinga update

# 3. (Optional) Remove old state files
rm -f bazinga/pm_state.json bazinga/group_status.json bazinga/orchestrator_state.json
```

### Fresh Start (Recommended)

For a clean migration:

```bash
# 1. Back up any custom configuration
cp bazinga/skills_config.json ~/skills_backup.json

# 2. Remove old bazinga folder
rm -rf bazinga/

# 3. Re-initialize
bazinga init --here

# 4. Restore custom configuration
cp ~/skills_backup.json bazinga/skills_config.json
```

---

## Breaking Changes

### 1. Direct State File Access

**Before:**
```python
import json
with open('bazinga/pm_state.json') as f:
    state = json.load(f)
```

**After:**
```python
# Use bazinga-db skill instead
# Inline SQL is forbidden
```

### 2. State File Watching

If you had scripts watching JSON files for changes, update them to:
- Query the SQLite database
- Or use the dashboard for visual monitoring

### 3. Custom Integrations

Any custom tooling that read/wrote to JSON state files must be updated to use the `bazinga-db` skill or direct SQLite queries (for read-only access).

---

## Version Number Clarification

Some documentation referenced "v2.0.0" as the version. The actual versioning is:

| CLI Version | Documentation Version | Notes |
|-------------|----------------------|-------|
| 1.0.x | Various | Initial releases |
| 1.1.0 | 1.1.0 | Current stable - SQLite, 9 agents, 18 skills |

The version is now synchronized across:
- `src/bazinga_cli/__init__.py`
- `README.md`
- All documentation files

---

## FAQ

### Q: Will my old orchestration history be preserved?

No. The migration to SQLite creates a fresh database. Old JSON state files are not automatically imported.

### Q: Can I still use JSON files?

JSON files are only used for **configuration** (skills_config, model_selection, etc.), not runtime state. All orchestration state is in SQLite.

### Q: What if I need to debug state?

Use the dashboard or direct SQLite queries:

```bash
# List recent sessions
sqlite3 bazinga/bazinga.db "SELECT id, status, created_at FROM sessions ORDER BY created_at DESC LIMIT 5;"

# View task groups for a session
sqlite3 bazinga/bazinga.db "SELECT * FROM task_groups WHERE session_id='bazinga_XXXXX';"
```

### Q: How do I check the database schema?

```bash
sqlite3 bazinga/bazinga.db ".schema"
```

---

## See Also

- [ARCHITECTURE.md](ARCHITECTURE.md) - Updated state management section
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Updated project structure
- [DASHBOARD.md](DASHBOARD.md) - Visual state monitoring

---

**Version:** 1.1.0
**Last Updated:** 2025-12-30
