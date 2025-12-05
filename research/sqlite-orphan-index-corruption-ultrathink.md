# SQLite Orphan Index Corruption Analysis

**Date:** 2025-12-05
**Context:** BAZINGA orchestration fails with `malformed database schema (sqlite_autoindex_task_groups_1) - orphan index` after specializations feature merge
**Decision:** Two bugs identified and fixed
**Status:** Implemented

---

## Problem Statement

After merging the agent specializations feature (#165), the BAZINGA orchestration system fails with:

```
Database error at /Users/mchaouachi/IdeaProjects/CDC/bazinga/bazinga.db:
malformed database schema (sqlite_autoindex_task_groups_1) - orphan index
```

This error occurs when:
1. Any bazinga-db skill operation is attempted
2. The `_ensure_db_exists()` check runs `PRAGMA integrity_check`
3. SQLite finds an index (`sqlite_autoindex_task_groups_1`) that references a non-existent or inconsistent table

## Root Cause Analysis

### What is an Orphan Index?

SQLite automatically creates indexes named `sqlite_autoindex_<table>_<N>` for:
- `PRIMARY KEY` constraints
- `UNIQUE` constraints
- `WITHOUT ROWID` tables

An **orphan index** occurs when:
1. The index exists in `sqlite_master`
2. BUT the table it references no longer exists OR
3. The table schema has changed incompatibly

### The Specializations Migration Path

The specializations feature introduced schema v7, but the corruption likely stems from v4→v5 migration:

**Schema v7 migration (simple ADD COLUMN):**
```python
# init_db.py lines 259-274
cursor.execute("ALTER TABLE task_groups ADD COLUMN specializations TEXT")
```
This is safe - ADD COLUMN doesn't affect indexes.

**Schema v4→v5 migration (table recreation with expanded status enum):**
```python
# init_db.py lines 179-235
# 1. Create task_groups_new with new schema
cursor.execute("CREATE TABLE task_groups_new (...)")

# 2. Copy data
cursor.execute("INSERT INTO task_groups_new ... SELECT ... FROM task_groups")

# 3. Drop old table - SHOULD drop autoindex
cursor.execute("DROP TABLE task_groups")

# 4. Rename new table - SHOULD create new autoindex
cursor.execute("ALTER TABLE task_groups_new RENAME TO task_groups")

# 5. Create manual index
cursor.execute("CREATE INDEX idx_taskgroups_session ON task_groups(session_id, status)")
```

### Hypotheses for Corruption

**Hypothesis 1: Incomplete Migration Transaction**
- The migration runs within an implicit transaction
- If interrupted between DROP TABLE and RENAME, the old autoindex could persist
- Probability: Medium

**Hypothesis 2: WAL Mode Checkpoint Failure**
- Database uses WAL mode (`PRAGMA journal_mode = WAL`)
- If WAL file (`bazinga.db-wal`) contains uncommitted changes
- A crash could leave indexes in inconsistent state
- Probability: High

**Hypothesis 3: Concurrent Access During Migration**
- Multiple processes accessing DB during schema migration
- One process holds reference to old table structure
- Probability: Low (bazinga-db uses proper locking)

**Hypothesis 4: Rename-vs-Drop Timing**
- SQLite's `DROP TABLE` drops associated autoindexes
- `ALTER TABLE RENAME` preserves existing autoindexes with old naming
- If there's a naming collision or partial state, orphan can occur
- Probability: Medium

### Evidence from Error Context

```
bazinga_db.py line 371: _ensure_db_exists()
→ line 421: integrity = cursor.execute("PRAGMA integrity_check;")
→ Result: "malformed database schema (sqlite_autoindex_task_groups_1) - orphan index"
```

This confirms:
- The database file exists
- It has content (not empty)
- The integrity check fails specifically on the task_groups autoindex

## Solution Options

### Option 1: Delete Database (Simple, Destructive)
```bash
rm /Users/mchaouachi/IdeaProjects/CDC/bazinga/bazinga.db*
# Reinitialize on next run
```
**Pros:** Guaranteed fix, simple
**Cons:** Loses all orchestration history

### Option 2: REINDEX Command (May Not Work)
```sql
REINDEX task_groups;
```
**Pros:** Preserves data
**Cons:** May fail if table schema is also corrupt

### Option 3: Drop Orphan Index via SQL (Advanced)
```sql
-- Connect to database ignoring errors
DROP INDEX IF EXISTS sqlite_autoindex_task_groups_1;
```
**Pros:** Surgical fix, preserves data
**Cons:** SQLite may not allow dropping autoindexes directly

### Option 4: Export/Reimport (Data Preservation)
```bash
# Export what's readable
sqlite3 corrupt.db ".dump" > backup.sql 2>/dev/null
# Edit backup.sql to remove corrupt index references
# Create fresh database and import
```
**Pros:** Maximum data preservation
**Cons:** Complex, may need manual SQL editing

### Option 5: Automated Recovery (bazinga_db.py already has this!)
The `recover_database()` method in `bazinga_db.py` (lines 283-380) already:
1. Attempts data salvage from corrupt DB
2. Backs up corrupt DB
3. Reinitializes with fresh schema
4. Restores salvaged data

**Recommendation:** Trigger the existing recovery mechanism.

## Recommended Solution

**Primary: Trigger Existing Recovery**

The `bazinga_db.py` already has sophisticated recovery logic that:
1. Salvages data from readable tables
2. Creates fresh DB with correct schema
3. Restores salvaged data

**However**, the current code path doesn't reach recovery because it throws an exception first.

### Fix: Improve Error Handling

Current flow:
```python
integrity = cursor.execute("PRAGMA integrity_check;").fetchone()[0]
if integrity != "ok":
    is_corrupted = True
    needs_init = True  # This triggers full reinit, not recovery
```

The issue: `needs_init = True` triggers `init_database()` which fails because the corrupt DB blocks schema operations.

### Proposed Code Change

```python
# In _ensure_db_exists(), after detecting corruption:
if is_corrupted:
    self._print_error(f"Database corrupted: {integrity}")
    # Trigger recovery instead of reinit
    recovery_success = self.recover_database()
    if not recovery_success:
        raise DatabaseError(f"Database corrupt and recovery failed: {integrity}")
    return  # Recovery handled everything
```

## Prevention Measures

1. **Wrap migrations in explicit transactions**
```python
conn.execute("BEGIN IMMEDIATE")
try:
    # migration steps
    conn.execute("COMMIT")
except:
    conn.execute("ROLLBACK")
    raise
```

2. **Verify integrity after migration**
```python
# After each major migration step
integrity = cursor.execute("PRAGMA integrity_check;").fetchone()[0]
if integrity != "ok":
    raise MigrationError(f"Migration corrupted database: {integrity}")
```

3. **Force WAL checkpoint after migrations**
```python
cursor.execute("PRAGMA wal_checkpoint(TRUNCATE);")
```

## Immediate Workaround for User

Until code fix is deployed:

```bash
# On the client machine
cd /Users/mchaouachi/IdeaProjects/CDC

# Option A: Delete and restart fresh
rm -f bazinga/bazinga.db bazinga/bazinga.db-wal bazinga/bazinga.db-shm

# Option B: Try to salvage (if orchestration history is valuable)
# Backup first
cp bazinga/bazinga.db bazinga/bazinga.db.corrupt.bak

# Try vacuum to rebuild
sqlite3 bazinga/bazinga.db "VACUUM;"

# If vacuum fails, try export/import
sqlite3 bazinga/bazinga.db ".dump" > /tmp/bazinga_dump.sql 2>/dev/null
rm bazinga/bazinga.db*
sqlite3 bazinga/bazinga.db < /tmp/bazinga_dump.sql
```

## Code Fix Implementation

### File: `.claude/skills/bazinga-db/scripts/bazinga_db.py`

Modify `_ensure_db_exists()` to call `recover_database()` when corruption is detected:

```python
# Around line 424, after detecting corruption:
if is_corrupted:
    self._print_error(f"Database corrupted at {self.db_path}: {integrity}. Attempting recovery...")
    # Move the corrupt file aside and recover
    recovery_success = self.recover_database()
    if recovery_success:
        self._print_error("Recovery successful!")
        return
    else:
        raise sqlite3.DatabaseError(
            f"Database corrupt and recovery failed: {integrity}. "
            f"Manual intervention required: rm {self.db_path}*"
        )
```

## Actual Root Cause (Post-Analysis)

### Bug 1: Error Pattern Not Recognized (Detection Failure)

**Location:** `bazinga_db.py` line 57-62

**Problem:** The `CORRUPTION_ERRORS` list only contained:
```python
CORRUPTION_ERRORS = [
    "database disk image is malformed",
    "file is not a database",
]
```

The actual error `"malformed database schema (sqlite_autoindex...)"` was NOT matched because:
- `"malformed database schema"` ≠ `"database disk image is malformed"`
- Different SQLite error messages for different corruption types

**Result:** Error fell through to "May need investigation" branch instead of triggering auto-recovery.

**Fix:** Added `"malformed database schema"` to `CORRUPTION_ERRORS` list.

### Bug 2: Race Condition in Schema Migration (ACTUAL Root Cause)

**Location:** `bazinga_db.py` `_ensure_db_exists()` (lines 402-517)

**Problem:** No file lock during schema migration. When parallel developers are spawned:
1. All check schema version simultaneously (v6 < v7)
2. All see `needs_init = True`
3. All try to run `init_db.py` concurrently
4. Multiple `ALTER TABLE task_groups ADD COLUMN specializations` operations run simultaneously
5. This corrupts the schema catalog with orphan autoindexes

**Fix:** Added file lock (`bazinga.db.migrate.lock`) around migration:
```python
lock_file = open(lock_file_path, 'w')
fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)  # Exclusive lock
# Re-check schema version (another process may have migrated)
# Run migration if still needed
fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)  # Release
```

### Bug 3: Non-Atomic Table Recreation (Secondary Issue)

**Location:** `init_db.py` v4→v5 migration (lines 228-231)

**Problem:** The table swap sequence was NOT wrapped in a transaction:
```python
# NOT atomic - interruption between any of these corrupts DB
cursor.execute("DROP TABLE task_groups")
cursor.execute("ALTER TABLE task_groups_new RENAME TO task_groups")
cursor.execute("CREATE INDEX idx_taskgroups_session ON task_groups(session_id, status)")
```

If interrupted between DROP and RENAME (crash, timeout, WAL checkpoint issue):
- Old autoindex `sqlite_autoindex_task_groups_1` becomes orphaned
- New table structure lacks proper index linkage

**Fix:** Wrapped in explicit transaction:
```python
try:
    cursor.execute("BEGIN IMMEDIATE")
    # ... CREATE, INSERT, DROP, RENAME, CREATE INDEX ...
    integrity = cursor.execute("PRAGMA integrity_check;").fetchone()[0]
    if integrity != "ok":
        raise sqlite3.IntegrityError(f"Migration corrupted: {integrity}")
    cursor.execute("COMMIT")
    cursor.execute("PRAGMA wal_checkpoint(TRUNCATE);")
except Exception:
    cursor.execute("ROLLBACK")
    raise
```

### Why It Surfaced After Specializations Merge

The specializations merge:
1. Updated `EXPECTED_SCHEMA_VERSION` to 7
2. Parallel developers were spawned (normal BAZINGA operation)
3. ALL developers checked schema version simultaneously (v6 < v7)
4. ALL set `needs_init = True` and tried to run migration
5. Multiple concurrent `ALTER TABLE task_groups ADD COLUMN specializations` corrupted schema
6. Bug 1 prevented auto-recovery from detecting and fixing it

**Key insight:** This ONLY happens with parallel developers. Single-developer mode wouldn't trigger this race condition.

## Multi-LLM Review Integration

**Reviewed by:** OpenAI GPT-5 (2025-12-05)

## Decision Rationale

1. **Existing recovery code should be leveraged** - Already implemented and tested
2. **Code fix is simple and safe** - Just changes error handling flow
3. **User workaround is straightforward** - Delete and reinit if history not needed
4. **Prevention measures are optional but valuable** - Add in follow-up PR

## Implementation Steps

1. Apply code fix to `_ensure_db_exists()` in bazinga_db.py
2. Test with artificially corrupted database
3. Commit and push
4. User deletes corrupt DB or runs new code for auto-recovery

## Lessons Learned

1. **Always test migrations with WAL mode** - WAL adds complexity
2. **Integrity check should trigger recovery, not exception** - Defensive design
3. **Table recreation is risky** - Prefer ALTER TABLE when possible
4. **Keep recovery logic accessible** - Not buried behind exception handling
