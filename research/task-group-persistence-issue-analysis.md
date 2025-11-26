# Task Group Persistence Issue: Root Cause Analysis

**Date:** 2025-11-26
**Context:** PM creates task groups but they're not found when Tech Lead tries to update them
**Decision:** Implement upsert-or-create pattern + improved error handling
**Status:** Proposed

---

## Problem Statement

When PM creates task groups during orchestration:
1. PM attempts to create task groups (A, B, etc.)
2. Sometimes gets "already exists" error (IntegrityError)
3. Create function silently fails - returns no error status
4. Later, Tech Lead tries `update-task-group`
5. Gets "Task group not found" error

**User observed behavior:** "PM has issues saving the groups in the tables, it showed some kind of 'already exists' error"

---

## Root Cause Analysis

### Issue #1: Silent Failure in create_task_group

**Location:** `.claude/skills/bazinga-db/scripts/bazinga_db.py:300-314`

```python
def create_task_group(self, group_id: str, session_id: str, name: str,
                     status: str = 'pending', assigned_to: Optional[str] = None) -> None:
    """Create a new task group."""
    conn = self._get_connection()
    try:
        conn.execute("""
            INSERT INTO task_groups (id, session_id, name, status, assigned_to)
            VALUES (?, ?, ?, ?, ?)
        """, (group_id, session_id, name, status, assigned_to))
        conn.commit()
        self._print_success(f"✓ Task group created: {group_id}")
    except sqlite3.IntegrityError:
        print(f"! Task group already exists: {group_id} in session {session_id}", file=sys.stderr)
        # ❌ BUG: No return value, no exception raised, caller thinks success
    finally:
        conn.close()
```

**Problem:** When IntegrityError occurs:
- Prints warning to stderr (agent might not see this)
- Returns None (same as success case)
- Caller has no way to know operation failed
- No upsert behavior - doesn't update existing record

### Issue #2: Inconsistent Error Handling

**Compare with create_session (lines 121-137):**
```python
except sqlite3.IntegrityError as e:
    # Session already exists - return existing session info
    existing = conn.execute("""SELECT ... FROM sessions WHERE session_id = ?""").fetchone()
    if existing:
        self._print_success(f"✓ Session already exists: {session_id}")
        return dict(existing)  # ✅ Returns existing record
```

`create_session` handles duplicates gracefully by returning existing record.
`create_task_group` does NOT - it silently fails.

### Issue #3: Race Conditions / Double Creation

**Scenario that causes "already exists":**
1. PM starts creating task groups
2. Partial failure or retry occurs
3. Some groups get created, some don't
4. PM retries, gets "already exists" for partially created groups
5. Groups that failed initially never get created
6. Database ends up in inconsistent state

### Issue #4: Empty Database Edge Case

**Current observation:** Database file is 0 bytes (empty)
```bash
$ ls -la bazinga/bazinga.db
-rw-r--r-- 1 root root 0 Nov 26 09:30 bazinga.db
```

Despite auto-initialization code in `_ensure_db_exists()` (lines 29-71), the database is empty. This suggests either:
- PM is invoking the skill incorrectly
- Skill invocation isn't triggering database operations
- State is being stored elsewhere (JSON files instead of DB)

---

## Solution: Upsert Pattern

### Recommended Fix: INSERT OR REPLACE (Upsert)

Replace the current INSERT with upsert behavior:

```python
def create_task_group(self, group_id: str, session_id: str, name: str,
                     status: str = 'pending', assigned_to: Optional[str] = None) -> Dict[str, Any]:
    """Create or update a task group (upsert)."""
    conn = self._get_connection()
    try:
        # Use INSERT OR REPLACE for upsert behavior
        conn.execute("""
            INSERT OR REPLACE INTO task_groups (id, session_id, name, status, assigned_to, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (group_id, session_id, name, status, assigned_to))
        conn.commit()

        # Fetch and return the record
        row = conn.execute("""
            SELECT * FROM task_groups WHERE id = ? AND session_id = ?
        """, (group_id, session_id)).fetchone()

        result = dict(row) if row else None
        self._print_success(f"✓ Task group saved: {group_id} (session: {session_id[:20]}...)")
        return {"success": True, "task_group": result}

    except Exception as e:
        print(f"! Failed to save task group {group_id}: {e}", file=sys.stderr)
        return {"success": False, "error": str(e)}
    finally:
        conn.close()
```

### Alternative: Explicit Upsert with ON CONFLICT

```python
conn.execute("""
    INSERT INTO task_groups (id, session_id, name, status, assigned_to)
    VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(id, session_id) DO UPDATE SET
        name = excluded.name,
        status = COALESCE(excluded.status, status),
        assigned_to = COALESCE(excluded.assigned_to, assigned_to),
        updated_at = CURRENT_TIMESTAMP
""", (group_id, session_id, name, status, assigned_to))
```

This is more explicit and preserves existing values when new ones are NULL.

---

## Critical Analysis

### Pros ✅

1. **Idempotent Operations** - Calling create multiple times is safe
2. **No Silent Failures** - Always returns success/failure status
3. **Consistent State** - Database always reflects latest PM intent
4. **Retry-Safe** - Network issues or partial failures won't corrupt state
5. **Backward Compatible** - Same function signature, just smarter behavior

### Cons ⚠️

1. **Overwrites Existing Data** - If group exists with status "completed", create would reset to "pending"
   - **Mitigation:** Use ON CONFLICT with COALESCE to preserve non-null values
2. **Schema Change Required** - Need to ensure composite key exists
   - **Status:** Already fixed in Nov 2025 migration

### Verdict

**Strongly Recommended.** The upsert pattern is industry standard for this exact scenario. It solves the race condition and silent failure issues without breaking existing functionality.

---

## Implementation Plan

### Phase 1: Fix create_task_group (Primary)

1. Change INSERT to INSERT OR REPLACE (or ON CONFLICT)
2. Return dict with success status
3. Always fetch and return the saved record

### Phase 2: Add get_or_create_task_group (Optional)

For cases where you want to check existence first:

```python
def get_or_create_task_group(self, group_id: str, session_id: str, name: str, **kwargs) -> Dict[str, Any]:
    """Get existing task group or create new one."""
    existing = self.get_task_group(group_id, session_id)
    if existing:
        return {"success": True, "task_group": existing, "created": False}

    result = self.create_task_group(group_id, session_id, name, **kwargs)
    result["created"] = True
    return result
```

### Phase 3: Add CLI Return Codes

Ensure CLI commands return proper exit codes:
- 0 = success
- 1 = failure

```python
if __name__ == "__main__":
    result = main()
    if isinstance(result, dict) and result.get("success") == False:
        sys.exit(1)
```

---

## Workaround Options (If Not Implementing Fix)

### Option A: Use Unique Group IDs

Instead of generic "A", "B", "C", use session-prefixed IDs:
```
{session_id}_A
{session_id}_B
```

**Problem:** Requires PM instruction changes, not a real fix.

### Option B: Delete Before Create

```bash
# Delete existing group first
python3 bazinga_db.py delete-task-group "A" "<session_id>"
# Then create
python3 bazinga_db.py create-task-group "A" "<session_id>" "Task Name"
```

**Problem:** Race conditions, data loss if delete succeeds but create fails.

### Option C: Check Existence First (Current Workaround)

```bash
# Check if exists
python3 bazinga_db.py get-task-group "A" "<session_id>"
# Only create if not found
```

**Problem:** Race conditions, extra round-trip, still can fail.

**Verdict:** None of these workarounds are reliable. Implement the upsert fix.

---

## Root Cause of Empty Database

The database being 0 bytes suggests a deeper issue:

1. **Skill Not Being Invoked Correctly** - PM may be using wrong invocation syntax
2. **Database Path Issue** - Might be writing to wrong location
3. **State in JSON Not DB** - PM state might only go to JSON files

**Investigation needed:** Check if PM is actually invoking bazinga-db skill correctly.

---

## Recommended Changes Summary

| File | Change |
|------|--------|
| `bazinga_db.py` | Replace INSERT with INSERT OR REPLACE in `create_task_group` |
| `bazinga_db.py` | Return `{"success": bool, "task_group": dict}` from `create_task_group` |
| `bazinga_db.py` | Add `get_or_create_task_group` method |
| `SKILL.md` | Update documentation to reflect upsert behavior |
| `project_manager.md` | No changes needed (upsert is transparent) |

---

## Lessons Learned

1. **Never Silently Fail** - Always return status, especially in database operations
2. **Upsert > Insert** - For operations that may be retried
3. **Consistent Error Handling** - All similar operations should handle errors the same way
4. **Return Values Matter** - Functions should always indicate success/failure

---

## References

- Database schema: `.claude/skills/bazinga-db/scripts/init_db.py`
- Current implementation: `.claude/skills/bazinga-db/scripts/bazinga_db.py:300-314`
- Previous fix: `research/pm-task-groups-fix-2025-11-21.md`
- SQLite upsert docs: https://www.sqlite.org/lang_upsert.html
