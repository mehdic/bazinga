# Database Recovery with Data Salvaging

**Date:** 2025-12-03
**Context:** Improve database recovery to preserve user data during auto-fix
**Decision:** Implement data salvaging before database reinitialization
**Status:** Implemented

---

## Problem Statement

When BAZINGA database corruption was detected (or falsely detected), the previous recovery process:
1. Backed up the corrupted file
2. Deleted the original
3. Created fresh empty database

This caused **complete data loss** - all sessions, logs, task groups, etc. were gone. Users had to start from scratch.

## Root Cause Analysis

Database "corruption" can be triggered by:

| Cause | Real Corruption? | Data Recoverable? |
|-------|------------------|-------------------|
| Inline SQL with wrong column names | No | Yes |
| Missing schema (empty DB file) | No | N/A |
| Transient disk errors | No | Yes |
| Process killed during write | Sometimes | Usually |
| Actual file corruption | Yes | Partial |
| WAL file deleted | Yes | Partial |

Most "corruption" events are actually recoverable - the data exists but something went wrong accessing it.

## Solution: Data Salvaging

### New Recovery Flow

```
Corruption Detected
        │
        ▼
┌─────────────────────────────────────┐
│ 1. SALVAGE: Extract readable data   │
│    - Connect with short timeout     │
│    - SELECT * from each table       │
│    - Store columns + rows in memory │
└─────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────┐
│ 2. BACKUP: Create timestamped copy  │
│    bazinga.db.corrupted_YYYYMMDD_*  │
└─────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────┐
│ 3. DELETE: Remove corrupted file    │
└─────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────┐
│ 4. INIT: Create fresh database      │
│    - Run init_db.py                 │
│    - Full schema v6                 │
└─────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────┐
│ 5. RESTORE: Insert salvaged data    │
│    - Foreign key order respected    │
│    - INSERT OR IGNORE (skip fails)  │
└─────────────────────────────────────┘
        │
        ▼
    ✓ Recovery Complete
```

### Tables Salvaged (in order)

1. `sessions` - Core session records
2. `orchestration_logs` - Agent interaction history
3. `state_snapshots` - PM/Orchestrator state
4. `task_groups` - Task definitions and status
5. `token_usage` - Token consumption tracking
6. `skill_outputs` - Skill execution results
7. `development_plans` - Multi-phase plans
8. `success_criteria` - Completion criteria
9. `context_packages` - Inter-agent context
10. `context_package_consumers` - Context consumption

Order matters for foreign key constraints (sessions must exist before logs referencing them).

### Implementation Details

#### `_extract_salvageable_data()`

```python
def _extract_salvageable_data(self) -> Dict[str, Dict]:
    """Try to extract data from corrupted database."""
    salvaged = {}

    # Short timeout - don't hang on badly corrupted DB
    conn = sqlite3.connect(self.db_path, timeout=5.0)

    for table in tables_to_try:
        try:
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            if rows:
                # Get column names
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [col[1] for col in cursor.fetchall()]
                salvaged[table] = {'columns': columns, 'rows': rows}
        except sqlite3.Error:
            pass  # Table unreadable - skip

    return salvaged
```

#### `_restore_salvaged_data()`

```python
def _restore_salvaged_data(self, salvaged: Dict) -> int:
    """Restore data to new database."""
    for table in restore_order:
        if table not in salvaged:
            continue

        columns = salvaged[table]['columns']
        rows = salvaged[table]['rows']

        for row in rows:
            cursor.execute(
                f"INSERT OR IGNORE INTO {table} (...) VALUES (...)",
                row
            )

    return total_restored
```

### Example Output

```
! Database corruption detected. Attempting recovery...
! Attempting to salvage data from corrupted database...
!   Salvaged 3 rows from sessions
!   Salvaged 47 rows from orchestration_logs
!   Salvaged 5 rows from state_snapshots
!   Salvaged 12 rows from task_groups
! Corrupted database backed up to: bazinga.db.corrupted_20231203_143022.db
! Restoring salvaged data to new database...
!   Restored 3/3 rows to sessions
!   Restored 47/47 rows to orchestration_logs
!   Restored 5/5 rows to state_snapshots
!   Restored 12/12 rows to task_groups
! ✓ Database recovered with 67 rows restored
```

## Edge Cases

| Scenario | Behavior |
|----------|----------|
| Can't connect to old DB | Skip salvage, proceed with fresh DB |
| Some tables unreadable | Salvage what we can, skip broken tables |
| Row violates new schema | Skip that row (INSERT OR IGNORE) |
| Column mismatch (schema changed) | May fail to restore that table |
| Timeout during salvage | Return partial data, continue recovery |

## Limitations

1. **Schema changes**: If the new schema has different columns, old data may not restore
2. **Large databases**: Salvaging loads all data into memory
3. **Truly corrupted files**: SQLite may not be able to read anything
4. **Foreign key violations**: Orphaned rows are skipped

## Alternative Approaches Considered

### 1. SQLite `.recover` command
- Pros: Built-in, handles more corruption cases
- Cons: Requires sqlite3 CLI, complex output parsing
- Decision: Too fragile for automated recovery

### 2. Copy entire file and run VACUUM
- Pros: Simple
- Cons: Doesn't fix actual corruption
- Decision: Only works for minor issues

### 3. Manual intervention required
- Pros: Safest - no accidental data loss
- Cons: Blocks user workflow, requires technical knowledge
- Decision: User preferred auto-fix

## Related Changes

1. **Prevent inline SQL** - Added rule to orchestrator forbidding `python3 -c "import sqlite3..."` - addresses root cause
2. **Auto-fix preference** - User explicitly requested auto-recovery over manual intervention
3. **Backup preserved** - Even with auto-fix, backup file allows manual recovery if needed

## Query Error Protection

A critical safeguard was added to prevent database deletion when agents write bad SQL queries.

### Problem
If an agent writes inline SQL with wrong column/table names (e.g., `group_id` instead of `id`, `agent_interactions` instead of `orchestration_logs`), the error might be misidentified as "database corruption" and trigger data loss.

### Solution: QUERY_ERRORS Allowlist

```python
# Errors that indicate BAD QUERIES, NOT corruption
QUERY_ERRORS = [
    "no such column",
    "no such table",
    "syntax error",
    "near \"",           # Syntax errors
    "unrecognized token",
    "no such function",
    "ambiguous column name",
    "constraint failed",
    "unique constraint",
    "foreign key constraint",
]
```

### Behavior

| Error Type | Contains | Action |
|-----------|----------|--------|
| Query Error | "no such column" | Raise error, **DO NOT** delete database |
| Query Error | "no such table" | Raise error, **DO NOT** delete database |
| Syntax Error | "near \"SELECT\"" | Raise error, **DO NOT** delete database |
| Real Corruption | "database disk image is malformed" | Backup + salvage + recover |
| Real Corruption | "file is not a database" | Backup + salvage + recover |

### Why This Matters

Without this protection:
1. Agent writes `SELECT * FROM agent_interactions` (wrong table name)
2. SQLite throws `OperationalError: no such table: agent_interactions`
3. System might detect this as "corruption"
4. System deletes database → **ALL DATA LOST**

With this protection:
1. Agent writes bad SQL
2. SQLite throws error
3. System recognizes it as a query error, not corruption
4. Error is raised to caller without modifying the database
5. **Data is preserved**

## Files Modified

- `.claude/skills/bazinga-db/scripts/bazinga_db.py`
  - Added `QUERY_ERRORS` list to identify bad SQL vs corruption
  - Added `_is_query_error()` method
  - Updated `_is_corruption_error()` to exclude query errors
  - Updated `_ensure_db_exists()` to distinguish query errors from corruption
  - Added `_extract_salvageable_data()`
  - Added `_restore_salvaged_data()`
  - Updated `_recover_from_corruption()` to use salvaging

## Testing

To test recovery:
```bash
# Simulate corruption by truncating DB
truncate -s 100 bazinga/bazinga.db

# Any DB operation will trigger recovery
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py \
  --db bazinga/bazinga.db list-sessions
```

## Conclusion

Data salvaging significantly improves the user experience during database recovery:
- **Before**: All data lost on any "corruption"
- **After**: Most/all data preserved in typical recovery scenarios

The backup file still exists for manual recovery if the automated salvaging fails or misses data.
