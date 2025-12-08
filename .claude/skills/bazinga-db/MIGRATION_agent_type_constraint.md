# Migration Guide: Remove agent_type CHECK Constraint

**Date:** 2025-11-20
**Issue:** CHECK constraint on `orchestration_logs.agent_type` was too restrictive
**Impact:** New agent types (investigator, requirements_engineer, orchestrator_speckit) could not log interactions

## What Changed

**Before:**
```sql
agent_type TEXT CHECK(agent_type IN ('pm', 'developer', 'qa_expert', 'tech_lead', 'orchestrator'))
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
.output bazinga/orchestration_logs_backup.csv
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
.import bazinga/orchestration_logs_backup.csv orchestration_logs_temp

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
rm bazinga/orchestration_logs_backup.csv
```

### Option 3: No Action Required (For New Installations)

If you're initializing a new database, the updated schema will be used automatically.

**⚠️ Note:** As of schema v2, automatic migration is built into `init_db.py`. Simply run:
```bash
python .claude/skills/bazinga-db/scripts/init_db.py bazinga/bazinga.db
```

The script will detect old schema and migrate automatically while preserving data.

---

## PowerShell Migration (Windows Users)

If you're on Windows without WSL/bash, use these PowerShell alternatives:

### PowerShell Option 1: Fresh Start

```powershell
# Backup existing database (optional)
Copy-Item bazinga/bazinga.db bazinga/bazinga.db.backup -ErrorAction SilentlyContinue

# Remove old database
Remove-Item bazinga/bazinga.db -ErrorAction SilentlyContinue

# Reinitialize with new schema
python .claude/skills/bazinga-db/scripts/init_db.py bazinga/bazinga.db
```

### PowerShell Option 2: Automatic Migration (Recommended)

**Since schema v2, migration is automatic:**

```powershell
# Just run init_db.py - it detects and migrates automatically
python .claude/skills/bazinga-db/scripts/init_db.py bazinga/bazinga.db
```

Output will show:
```
Current schema version: 1
Schema upgrade required: v1 -> v2
🔄 Migrating schema from v1 to v2...
   - Backing up N orchestration log entries
   - Restored N orchestration log entries
✓ Migration to v2 complete
```

### PowerShell Option 3: Manual Migration (Advanced)

If you need manual control:

```powershell
# 1. Backup database
Copy-Item bazinga/bazinga.db bazinga/bazinga.db.backup

# 2. Use Python to run SQL commands
$dbPath = "bazinga/bazinga.db"

python -c @"
import sqlite3
conn = sqlite3.connect('$dbPath')
cursor = conn.cursor()

# Export data
cursor.execute('SELECT * FROM orchestration_logs')
logs = cursor.fetchall()
print(f'Backing up {len(logs)} logs')

# Drop old table
cursor.execute('DROP TABLE IF EXISTS orchestration_logs')

# Create new table
cursor.execute('''
CREATE TABLE orchestration_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    iteration INTEGER,
    agent_type TEXT NOT NULL,
    agent_id TEXT,
    content TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
)
''')

# Recreate indexes
cursor.execute('CREATE INDEX idx_logs_session ON orchestration_logs(session_id, timestamp DESC)')
cursor.execute('CREATE INDEX idx_logs_agent_type ON orchestration_logs(session_id, agent_type)')

# Restore data
cursor.executemany('INSERT INTO orchestration_logs VALUES (?,?,?,?,?,?,?)', logs)
print(f'Restored {len(logs)} logs')

conn.commit()
conn.close()
"@

# 3. Verify
python -c "import sqlite3; conn = sqlite3.connect('$dbPath'); print(f'Total logs: {conn.execute(\"SELECT COUNT(*) FROM orchestration_logs\").fetchone()[0]}'); conn.close()"
```

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
- `senior_software_engineer`
- `qa_expert`
- `tech_lead`
- `orchestrator`
- `investigator`
- `requirements_engineer`

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
- Verify export: `bazinga/orchestration_logs_backup.csv`
- Restore: `cp bazinga/bazinga.db.backup bazinga/bazinga.db`

---

## Related Files Changed

- `.claude/skills/bazinga-db/scripts/init_db.py` (line 47)
- `.claude/skills/bazinga-db/references/schema.md` (line 75)

---

**Migration Status:** Required for existing databases
**Breaking Change:** Yes (requires database migration)
**Backward Compatible:** No (old schema will reject new agent types)
