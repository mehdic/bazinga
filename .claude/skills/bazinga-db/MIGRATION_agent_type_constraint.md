# Migration Guide: Remove agent_type CHECK Constraint

**Date:** 2025-11-20
**Issue:** CHECK constraint on `orchestration_logs.agent_type` was too restrictive
**Impact:** New agent types (investigator, requirements_engineer, orchestrator_speckit) could not log interactions

## What Changed

**Before:**
```sql
agent_type TEXT CHECK(agent_type IN ('pm', 'developer', 'qa_expert', 'techlead', 'orchestrator'))
```

**After:**
```sql
agent_type TEXT NOT NULL
```

**Reason:** BAZINGA is designed to be extensible. New agents can be added without schema changes.

---

## Migration Steps

### Option 1: Fresh Start (Recommended for Development)

If you don't need to preserve existing orchestration logs:

```bash
# Backup existing database (optional)
cp bazinga/bazinga.db bazinga/bazinga.db.backup

# Remove old database
rm bazinga/bazinga.db

# Reinitialize with new schema
python .claude/skills/bazinga-db/scripts/init_db.py bazinga/bazinga.db
```

### Option 2: Preserve Existing Data

If you need to keep existing orchestration logs:

```bash
# 1. Backup database
cp bazinga/bazinga.db bazinga/bazinga.db.backup

# 2. Export orchestration_logs data
sqlite3 bazinga/bazinga.db <<EOF
.headers on
.mode csv
.output /tmp/orchestration_logs_backup.csv
SELECT * FROM orchestration_logs;
.quit
EOF

# 3. Drop and recreate table
sqlite3 bazinga/bazinga.db <<EOF
DROP TABLE IF EXISTS orchestration_logs;

CREATE TABLE orchestration_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    iteration INTEGER,
    agent_type TEXT NOT NULL,
    agent_id TEXT,
    content TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);

CREATE INDEX idx_logs_session ON orchestration_logs(session_id, timestamp DESC);
CREATE INDEX idx_logs_agent_type ON orchestration_logs(session_id, agent_type);
.quit
EOF

# 4. Reimport data
sqlite3 bazinga/bazinga.db <<EOF
.mode csv
.import /tmp/orchestration_logs_backup.csv orchestration_logs_temp

-- Skip header row and reinsert
INSERT INTO orchestration_logs (id, session_id, timestamp, iteration, agent_type, agent_id, content)
SELECT id, session_id, timestamp, iteration, agent_type, agent_id, content
FROM orchestration_logs_temp
WHERE id != 'id'; -- Skip CSV header

DROP TABLE orchestration_logs_temp;
.quit
EOF

# 5. Verify data
sqlite3 bazinga/bazinga.db "SELECT COUNT(*) FROM orchestration_logs;"

# 6. Clean up
rm /tmp/orchestration_logs_backup.csv
```

### Option 3: No Action Required (For New Installations)

If you're initializing a new database, the updated schema will be used automatically.

---

## Verification

After migration, verify the new schema:

```bash
sqlite3 bazinga/bazinga.db "PRAGMA table_info(orchestration_logs);"
```

Expected output should show `agent_type TEXT NOT NULL` without CHECK constraint.

Test with new agent types:

```bash
sqlite3 bazinga/bazinga.db <<EOF
INSERT INTO sessions (session_id, mode, status)
VALUES ('test_session', 'simple', 'active');

INSERT INTO orchestration_logs (session_id, agent_type, content)
VALUES ('test_session', 'investigator', 'Test log from investigator');

INSERT INTO orchestration_logs (session_id, agent_type, content)
VALUES ('test_session', 'requirements_engineer', 'Test log from requirements engineer');

SELECT agent_type, content FROM orchestration_logs WHERE session_id = 'test_session';

DELETE FROM orchestration_logs WHERE session_id = 'test_session';
DELETE FROM sessions WHERE session_id = 'test_session';
.quit
EOF
```

Should succeed without CHECK constraint errors.

---

## Current Agent Types

The system now supports all current and future agent types:

**Current agents:**
- `pm` (project_manager)
- `developer`
- `qa_expert`
- `techlead`
- `orchestrator`
- `investigator`
- `requirements_engineer`
- `orchestrator_speckit`

**Future agents:** Any new agent type can be added without schema changes.

---

## Troubleshooting

**Error: "CHECK constraint failed"**
- You're using an old database with the old schema
- Follow Option 1 or Option 2 above to migrate

**Error: "table orchestration_logs already exists"**
- You're trying to run init_db.py on an existing database
- Use Option 2 (Preserve Data) or delete the old database first

**Data loss after migration:**
- Check backup: `bazinga/bazinga.db.backup`
- Verify export: `/tmp/orchestration_logs_backup.csv`
- Restore: `cp bazinga/bazinga.db.backup bazinga/bazinga.db`

---

## Related Files Changed

- `.claude/skills/bazinga-db/scripts/init_db.py` (line 47)
- `.claude/skills/bazinga-db/references/schema.md` (line 75)

---

**Migration Status:** Required for existing databases
**Breaking Change:** Yes (requires database migration)
**Backward Compatible:** No (old schema will reject new agent types)
