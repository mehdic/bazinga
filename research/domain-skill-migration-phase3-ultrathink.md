# Domain Skill Migration Phase 3: Ultrathink Critical Review

**Date:** 2026-01-01
**Context:** Review of Schema v18 implementation (commit ec08745)
**Decision:** Pending user approval of fixes
**Status:** Reviewed - Awaiting User Approval
**Reviewed by:** OpenAI GPT-5 (Gemini skipped - ENABLE_GEMINI=false)

---

## Scope

This review covers commit `ec08745` which implemented:
- Schema v18 migration (group_id, investigation state_type, UNIQUE index)
- UPSERT for save_investigation_iteration
- JSON validation for file inputs
- Documentation updates for save-event, investigator.md, orchestrator.md

---

## Critical Analysis

### 🔴 CRITICAL Issue 1: save_state function BROKEN by UNIQUE constraint

**Severity:** P0 - Every save-state call fails on second invocation

**Location:** `bazinga_db.py:1325-1334`

**Problem:**
The existing `save_state` function uses simple INSERT without UPSERT:
```python
def save_state(self, session_id: str, state_type: str, state_data: Dict) -> None:
    conn.execute("""
        INSERT INTO state_snapshots (session_id, state_type, state_data)
        VALUES (?, ?, ?)
    """, (session_id, state_type, json.dumps(state_data)))
```

With the new `UNIQUE(session_id, state_type, group_id)` index:
1. First call: Works - INSERTs with implicit `group_id='global'` (from DEFAULT)
2. Second call: **FAILS** - UNIQUE constraint violation for same (session_id, state_type, 'global')

**Impact:**
- ALL orchestrator state saves fail after first save
- ALL PM state saves fail after first save
- Session recovery completely broken

**Fix Required:**
```python
def save_state(self, session_id: str, state_type: str, state_data: Dict,
               group_id: str = 'global') -> None:
    conn.execute("""
        INSERT INTO state_snapshots (session_id, group_id, state_type, state_data, timestamp)
        VALUES (?, ?, ?, ?, datetime('now'))
        ON CONFLICT(session_id, state_type, group_id)
        DO UPDATE SET state_data = excluded.state_data, timestamp = excluded.timestamp
    """, (session_id, group_id, state_type, json.dumps(state_data)))
```

---

### 🔴 CRITICAL Issue 2: get_latest_state doesn't filter by group_id

**Severity:** P0 - Returns wrong state for parallel investigations

**Location:** `bazinga_db.py:1336-1345`

**Problem:**
```python
def get_latest_state(self, session_id: str, state_type: str) -> Optional[Dict]:
    row = conn.execute("""
        SELECT state_data FROM state_snapshots
        WHERE session_id = ? AND state_type = ?
        ORDER BY timestamp DESC LIMIT 1
    """, (session_id, state_type)).fetchone()
```

This query doesn't filter by group_id. In parallel mode with multiple investigation states:
- Group A: investigation state with group_id='A'
- Group B: investigation state with group_id='B'
- `get_latest_state(session, 'investigation')` returns the MOST RECENT regardless of group

**Impact:**
- Parallel investigations return wrong state
- Investigation resumption loads wrong group's state

**Fix Required:**
```python
def get_latest_state(self, session_id: str, state_type: str,
                     group_id: str = 'global') -> Optional[Dict]:
    row = conn.execute("""
        SELECT state_data FROM state_snapshots
        WHERE session_id = ? AND state_type = ? AND group_id = ?
        ORDER BY timestamp DESC LIMIT 1
    """, (session_id, state_type, group_id)).fetchone()
```

---

### 🔴 CRITICAL Issue 3: CLI save-state/get-state don't support group_id

**Severity:** P0 - CLI incompatible with new schema

**Location:**
- CLI: `bazinga_db.py:3584-3589`
- Docs: `bazinga-db-core/SKILL.md:81-102`

**Problem:**
The CLI commands don't accept group_id:
```bash
# Current (broken for investigation states)
save-state <session> <type> <json_data>
get-state <session> <type>
```

**Impact:**
- Cannot save investigation state with correct group_id via CLI
- Cannot retrieve group-specific investigation state

**Fix Required:**
```bash
# Updated CLI
save-state <session> <type> <json_data> [--group-id <id>]
get-state <session> <type> [--group-id <id>]
```

---

### 🔴 CRITICAL Issue 4: investigation_loop.md uses broken save-state pattern

**Severity:** P0 - Template instructs broken usage

**Location:** `templates/investigation_loop.md:94-102` and `113-116`

**Problem:**
The template instructs:
```
bazinga-db-core, please save state:
Session ID: {session_id}
State Type: investigation
Data: {investigation_state as JSON}
```

This uses the old `save-state` CLI which doesn't pass group_id. Every second save for the same session will fail.

**Fix Required:**
Update template to ALWAYS use atomic `save-investigation-iteration` command, not save-state for investigation type.

---

### 🟡 MEDIUM Issue 1: Deduplication key inconsistency in index vs idempotency

**Severity:** P2 - Potential for dedup failures

**Location:**
- Index: `idx_logs_idempotency ON (session_id, event_subtype, group_id, idempotency_key)`
- Check: `WHERE session_id = ? AND ... event_subtype = ? AND idempotency_key = ?`

**Problem:**
The idempotency check in `save_investigation_iteration` (line 1270-1276) doesn't include group_id:
```python
existing = conn.execute("""
    SELECT id FROM orchestration_logs
    WHERE session_id = ? AND log_type = 'event'
    AND event_subtype = 'investigation_iteration'
    AND idempotency_key = ?
""", (session_id, idempotency_key)).fetchone()
```

But the unique index includes group_id. This creates a semantic mismatch:
- If two groups have the same idempotency_key format, the query finds the first one
- But the insert might succeed because group_id differs in the unique index

**Impact:**
The idempotency_key already includes group_id in its format `{session}|{group}|type|{iter}`, so this is mostly cosmetic. But for consistency, the query should match the index.

---

### 🟡 MEDIUM Issue 2: No migration test for state_snapshots deduplication

**Severity:** P2 - Migration may create duplicates

**Location:** `init_db.py:1518-1525` (migration data restore)

**Problem:**
When migrating v17→v18, if there are duplicate (session_id, state_type) rows in the old table, the migration will fail when trying to INSERT into the new table with UNIQUE constraint:
```python
for row in state_data:
    cursor.execute("""
        INSERT INTO state_snapshots (id, session_id, group_id, timestamp, state_type, state_data)
        VALUES (?, ?, 'global', ?, ?, ?)
    """, ...)
```

If old table had multiple rows with same (session_id, state_type), this INSERT will hit UNIQUE violation.

**Fix Required:**
Add deduplication step before migration:
```python
# Keep only latest per (session_id, state_type)
cursor.execute("""
    SELECT id, session_id, timestamp, state_type, state_data FROM (
        SELECT *, ROW_NUMBER() OVER (PARTITION BY session_id, state_type ORDER BY timestamp DESC) as rn
        FROM state_snapshots
    ) WHERE rn = 1
""")
```

Or use INSERT OR REPLACE during restore.

---

### 🟢 MINOR Issue 1: Temp file names could collide in parallel

**Severity:** P3 - Race condition in parallel mode

**Location:** `agents/investigator.md:750-771`

**Problem:**
Temp files use fixed names:
```bash
cat > /tmp/inv_state.json << 'EOF'
cat > /tmp/inv_event.json << 'EOF'
```

In parallel mode, multiple investigators could clobber each other's temp files.

**Fix Required:**
Use unique temp file names:
```bash
cat > /tmp/inv_state_${session_id}_${group_id}.json << 'EOF'
```

---

### 🟢 MINOR Issue 2: Missing group_id in schema.md reference doc

**Severity:** P4 - Documentation incomplete

**Location:** `.claude/skills/bazinga-db/references/schema.md` (if exists)

**Problem:**
The schema reference documentation may not be updated to reflect the new group_id column in state_snapshots.

---

## Backward Compatibility Assessment

### ❌ BREAKING CHANGES

| Change | Impact | Affected Code |
|--------|--------|---------------|
| UNIQUE(session_id, state_type, group_id) | **BREAKS** save_state on second call | All orchestrator/PM state saves |
| group_id NOT NULL DEFAULT 'global' | Works on INSERT | - |
| 'investigation' in CHECK | Fixes previous bug | - |

### Risk Level: **HIGH**

The current implementation will break existing workflows that call save-state multiple times for the same session/state_type.

---

## Summary

| Severity | Count | Issues |
|----------|-------|--------|
| 🔴 Critical | 4 | save_state broken, get_state broken, CLI broken, template broken |
| 🟡 Medium | 2 | Dedup check mismatch, migration dedup |
| 🟢 Minor | 2 | Temp file collision, docs incomplete |

### Verdict

**The Schema v18 implementation is BROKEN** - the UNIQUE index breaks the existing `save_state`/`get_latest_state` functions. Every orchestration session that saves state more than once will fail with a UNIQUE constraint violation.

This is a P0 regression that must be fixed before the code can be used.

---

## Proposed Fixes

### Fix 1: Update save_state to use UPSERT with group_id

```python
def save_state(self, session_id: str, state_type: str, state_data: Dict,
               group_id: str = 'global') -> None:
    """Save state snapshot with group isolation."""
    conn = self._get_connection()
    conn.execute("""
        INSERT INTO state_snapshots (session_id, group_id, state_type, state_data, timestamp)
        VALUES (?, ?, ?, ?, datetime('now'))
        ON CONFLICT(session_id, state_type, group_id)
        DO UPDATE SET
            state_data = excluded.state_data,
            timestamp = excluded.timestamp
    """, (session_id, group_id, state_type, json.dumps(state_data)))
    conn.commit()
    conn.close()
    self._print_success(f"✓ Saved {state_type} state (group={group_id})")
```

### Fix 2: Update get_latest_state with group_id

```python
def get_latest_state(self, session_id: str, state_type: str,
                     group_id: str = 'global') -> Optional[Dict]:
    """Get latest state snapshot for specific group."""
    conn = self._get_connection()
    row = conn.execute("""
        SELECT state_data FROM state_snapshots
        WHERE session_id = ? AND state_type = ? AND group_id = ?
        ORDER BY timestamp DESC LIMIT 1
    """, (session_id, state_type, group_id)).fetchone()
    conn.close()
    return json.loads(row['state_data']) if row else None
```

### Fix 3: Update CLI commands

```python
# save-state with optional group_id
elif cmd == 'save-state':
    session_id = cmd_args[0]
    state_type = cmd_args[1]
    state_data = json.loads(cmd_args[2])
    group_id = 'global'
    # Check for --group-id flag
    if len(cmd_args) > 3 and cmd_args[3] == '--group-id':
        group_id = cmd_args[4] if len(cmd_args) > 4 else 'global'
    db.save_state(session_id, state_type, state_data, group_id=group_id)

# get-state with optional group_id
elif cmd == 'get-state':
    session_id = cmd_args[0]
    state_type = cmd_args[1]
    group_id = 'global'
    if len(cmd_args) > 2 and cmd_args[2] == '--group-id':
        group_id = cmd_args[3] if len(cmd_args) > 3 else 'global'
    result = db.get_latest_state(session_id, state_type, group_id=group_id)
    print(json.dumps(result, indent=2))
```

### Fix 4: Update investigation_loop.md

Replace all `save-state` calls for investigation type with atomic command:
```markdown
**ALWAYS use atomic save-investigation-iteration instead of save-state for investigation states.**

The save-state command does NOT support group isolation for investigation states.
Use save-investigation-iteration for all investigation state updates.
```

### Fix 5: Add migration deduplication

```python
# Before restoring, deduplicate by keeping latest per (session_id, state_type)
if state_data:
    seen = {}
    for row in sorted(state_data, key=lambda r: r[2], reverse=True):  # sort by timestamp DESC
        key = (row[1], row[3])  # (session_id, state_type)
        if key not in seen:
            seen[key] = row
    state_data = list(seen.values())
    print(f"   - Deduplicated to {len(state_data)} unique entries")
```

---

## Implementation Priority

| Priority | Issue | Fix |
|----------|-------|-----|
| P0 | save_state broken | Add UPSERT with group_id parameter |
| P0 | get_latest_state broken | Add group_id parameter |
| P0 | CLI doesn't support group_id | Add --group-id flag |
| P0 | investigation_loop.md broken | Update to use atomic command only |
| P2 | Dedup check mismatch | Add group_id to idempotency query |
| P2 | Migration may fail on duplicates | Add deduplication step |
| P3 | Temp file collision | Use unique temp file names |

---

## Multi-LLM Review Integration

### Reviewer: OpenAI GPT-5

**Overall Assessment:** Confirmed all 4 critical issues. Raised additional concerns.

### Consensus Points (Confirmed by OpenAI)

1. **save_state UPSERT is P0** - "The analysis correctly identifies that save_state uses a bare INSERT and will violate the new UNIQUE constraint on the second call."

2. **get_latest_state needs group isolation** - "Current query ignores group_id and can return the wrong state in parallel investigations."

3. **CLI must support group_id** - "The CLI wrappers don't accept group-id which makes it impossible to persist per-group investigation state via skills."

4. **Migration order is understated** - OpenAI elevated severity: "The new UNIQUE index is created before data restore, and old tables can contain multiple rows per (session_id, state_type). Inserts into the new table will raise UNIQUE violations during restore and abort the migration transaction."

### Additional Issues Raised by OpenAI (NEW)

#### 🟡 NEW Issue: save_event does not populate group_id

**Severity:** P2 - Index/query semantic mismatch

**Problem:**
The unique idempotency index is `(session_id, event_subtype, group_id, idempotency_key)` but save_event doesn't set group_id, leaving it NULL. While the idempotency_key happens to include the group ID string, this defeats the DB's intended grouping.

**OpenAI Recommendation:**
Add optional group_id to save_event and include it in both the idempotency check and the INSERT row for all event types.

**Proposed Fix:**
```python
def save_event(self, session_id: str, event_subtype: str, payload: Dict,
               idempotency_key: str = None, group_id: str = 'global') -> None:
    # Include group_id in idempotency check
    existing = conn.execute("""
        SELECT id FROM orchestration_logs
        WHERE session_id = ? AND log_type = 'event'
        AND event_subtype = ? AND group_id = ? AND idempotency_key = ?
    """, (session_id, event_subtype, group_id, idempotency_key)).fetchone()

    # Include group_id in INSERT
    conn.execute("""
        INSERT INTO orchestration_logs
        (session_id, group_id, log_type, event_subtype, payload, idempotency_key)
        VALUES (?, ?, 'event', ?, ?, ?)
    """, (session_id, group_id, event_subtype, json.dumps(payload), idempotency_key))
```

#### 🟢 Clarification: Template vs Root Cause

OpenAI noted: "The 'template instructs broken usage' conclusion is a bit overstated. The real problem is that save_state is not an UPSERT. If you fix save_state, the template's initial save is fine."

**Action:** After fixing save_state with UPSERT, the template will work. However, for investigation states specifically, preferring the atomic save-investigation-iteration command everywhere is still more robust and consistent.

### Better Alternatives Suggested by OpenAI

1. **Unified state upsert API** - Instead of special-casing investigation, provide a single `save_state(session_id, state_type, state_data, group_id='global')` UPSERT and encourage all flows to use it.

2. **SQL-window dedup in migration** - Use ROW_NUMBER() window function:
```sql
SELECT id, session_id, timestamp, state_type, state_data
FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY session_id, state_type ORDER BY timestamp DESC) rn
  FROM old_state_snapshots
) WHERE rn = 1;
```

3. **Event API normalization** - Normalize save_event to always accept optional group_id and enforce uniqueness consistently.

### Implementation Risks Noted by OpenAI

1. **Migration failure under real-world data** - If older DBs have many state snapshots for the same type, the current migration order will likely fail.

2. **Silent behavior drift if defaults change** - Introducing group_id defaults must be carefully coordinated so existing flows (orchestrator/PM) remain stable.

3. **Partial index reliance with NULL group_id** - Keeping group_id NULL in events while the index includes group_id can lead to surprising uniqueness semantics.

4. **Tooling/docs skew** - Updating code without updating SKILL.md and orchestrator templates will cause runtime agent errors.

### Incorporated into Plan

| OpenAI Finding | Incorporated? | Notes |
|----------------|---------------|-------|
| save_state UPSERT | ✅ Yes | Already in Fix 1 |
| get_latest_state group filter | ✅ Yes | Already in Fix 2 |
| CLI --group-id | ✅ Yes | Already in Fix 3 |
| Migration dedup | ✅ Yes | Enhanced Fix 5 with SQL window approach |
| save_event group_id | ✅ Yes | Added as new Fix 6 |
| Backward compat testing | ✅ Yes | Added to regression tests |
| Temp file unique names | ✅ Yes | Already in Minor Issue 1 |

### Rejected Suggestions

| Suggestion | Reason for Rejection |
|------------|---------------------|
| None | All OpenAI suggestions were valid and incorporated |

---

## Updated Implementation Priority

| Priority | Issue | Fix |
|----------|-------|-----|
| P0 | save_state broken | Fix 1: Add UPSERT with group_id parameter |
| P0 | get_latest_state broken | Fix 2: Add group_id parameter |
| P0 | CLI doesn't support group_id | Fix 3: Add --group-id flag |
| P0 | investigation_loop.md broken | Fix 4: Update to use atomic command only |
| P2 | Migration may fail on duplicates | Fix 5: Add SQL window deduplication |
| P2 | save_event missing group_id | Fix 6: Add optional group_id to save_event |
| P2 | Dedup check mismatch | Fix 7: Add group_id to idempotency query |
| P3 | Temp file collision | Fix 8: Use unique temp file names |

---

## Regression Tests Required

Per OpenAI recommendation, add tests for:
- save_state UPSERT across multiple calls (with/without group_id)
- get_latest_state returning correct per-group data
- save_event with group_id uniqueness
- Migration dedup success on seeded duplicates
- CLI --group-id flag parsing
- Backward compatibility: existing orchestrator/PM flows still work with default 'global'

---

## References

- Previous commit: ec08745 (Fix critical bugs in domain skill migration)
- Previous review: research/domain-skill-migration-phase2-ultrathink.md
- Schema v18 migration: init_db.py:1464-1564
- OpenAI review: tmp/ultrathink-reviews/openai-review.md
