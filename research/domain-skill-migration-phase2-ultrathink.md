# Domain Skill Migration Phase 2: Ultrathink Critical Review

**Date:** 2026-01-01
**Context:** Review of all Phase 1-3 implementation from previous session
**Decision:** Pending user approval of fixes
**Status:** Reviewed
**Reviewed by:** OpenAI GPT-5 ✅, Google Gemini 3 Pro Preview (skipped)

---

## Scope

This review covers commit `8405a57` which implemented:
- Phase 1: Documentation fixes (event types, State vs Events doc, validation script)
- Phase 2: Security/reliability (--payload-file, redaction, idempotency_key column)
- Phase 3: Architectural (event registry, 5+ schemas, atomic command)

---

## Critical Analysis

### 🔴 CRITICAL Issue 1: state_type 'investigation' NOT IN CHECK CONSTRAINT

**Severity:** P0 - Data corruption / Silent failure

**Location:**
- `init_db.py:1556-1560` - state_snapshots table definition
- `bazinga_db.py:1262` - save_investigation_iteration uses 'investigation'

**Problem:**
The state_snapshots table has a CHECK constraint:
```sql
state_type CHECK(state_type IN ('pm', 'orchestrator', 'group_status'))
```

But `save_investigation_iteration` tries to INSERT with `state_type='investigation'`:
```python
conn.execute("""
    INSERT OR REPLACE INTO state_snapshots
    (session_id, state_type, state_data, timestamp)
    VALUES (?, 'investigation', ?, datetime('now'))
""", (session_id, redacted_state))
```

**Result:** Every call to `save-investigation-iteration` will FAIL with a CHECK constraint violation. The atomic save feature is **completely broken**.

**Fix Required:**
- Add 'investigation' to state_type CHECK constraint
- Add schema migration v17→v18 or fix v17 migration

---

### 🔴 CRITICAL Issue 2: No UNIQUE constraint for state replacement

**Severity:** P0 - Logic error

**Location:** `init_db.py` - state_snapshots table

**Problem:**
The `INSERT OR REPLACE` statement requires a UNIQUE constraint on the columns being checked for replacement. The state_snapshots table has:
- `id` as PRIMARY KEY (auto-increment)
- No UNIQUE constraint on (session_id, state_type)

**Result:** Every `INSERT OR REPLACE` creates a NEW ROW instead of replacing. State snapshots table grows unbounded. Session resumption may load wrong state.

**Fix Required:**
- Add `UNIQUE(session_id, state_type)` constraint (but state_type alone isn't unique enough)
- Or use `INSERT ... ON CONFLICT` with proper conflict resolution
- Or add `group_id` to state_snapshots for investigation states

---

### 🔴 CRITICAL Issue 3: Investigation state has no group isolation

**Severity:** P0 - Race condition / Data loss

**Location:** `bazinga_db.py:1259-1263`

**Problem:**
The state is saved with only (session_id, state_type='investigation'). In parallel mode, multiple groups can have concurrent investigations. They will OVERWRITE each other's state.

Example scenario:
1. Group A starts investigation iteration 1, saves state
2. Group B starts investigation iteration 1, saves state (OVERWRITES A)
3. Group A resumes - loads GROUP B's state!

**Fix Required:**
- Add `group_id` column to state_snapshots table
- Or encode group_id into state_type: `state_type='investigation_GRPID'`
- Update UNIQUE constraint to include group_id

---

### 🟡 MEDIUM Issue 1: Event registry NOT enforced at runtime

**Severity:** P2 - Weak contract enforcement

**Location:** `bazinga/schemas/events/registry.json`

**Problem:**
The registry exists as documentation only. The `save_event` function:
- Does NOT validate event_subtype against registry
- Does NOT validate payload against JSON schema
- Allows any event type to be saved

**Impact:**
- Typos in event types go undetected
- Invalid payloads stored in database
- Registry is documentation, not enforcement

**Recommendation:**
Either:
1. Add validation to `save_event` with registry lookup
2. Or explicitly document that registry is advisory-only

---

### 🟡 MEDIUM Issue 2: Idempotency key format not validated

**Severity:** P2 - Data quality

**Location:** `bazinga_db.py:1100` and SKILL.md documentation

**Problem:**
The recommended format is `{session_id}|{group_id}|{event_type}|{iteration}` but:
- No regex validation enforces this format
- Any string is accepted as idempotency_key
- Inconsistent keys will bypass deduplication

**Impact:**
- Format drift over time
- Debugging difficulties when keys don't match expected pattern

**Recommendation:**
Add optional format validation or make format advisory-only in docs.

---

### 🟡 MEDIUM Issue 3: JSON validation missing on file reads

**Severity:** P2 - Garbage in, garbage out

**Location:** CLI argument parsing for --payload-file, --state-file, --event-file

**Problem:**
Files are read and passed directly to database. No JSON.loads() validation:
```python
with open(payload_path, 'r') as f:
    payload = f.read().strip()
```

**Impact:**
- Malformed JSON stored in database
- Query parsing may fail later
- Dashboard can't display corrupted events

**Fix Required:**
Add JSON validation after reading files.

---

### 🟢 MINOR Issue 1: Temp files not cleaned up

**Severity:** P3 - Resource leak

**Location:** `templates/investigation_loop.md` Step 4a-log

**Problem:**
Instructions write to `/tmp/inv_state.json`, `/tmp/inv_event.json` but no cleanup. Over many orchestrations, temp files accumulate.

**Recommendation:**
Add cleanup instruction or use unique temp file names with session ID.

---

### 🟢 MINOR Issue 2: Validation script doesn't test actual operations

**Severity:** P3 - False confidence

**Location:** `scripts/validate-db-skill-migration.sh`

**Problem:**
Script only greps for text patterns in markdown. Doesn't:
- Create test database
- Run actual CLI commands
- Verify save/load round-trip

**Recommendation:**
Consider adding integration test that exercises actual DB operations.

---

### 🟢 MINOR Issue 3: Schema dedup key is advisory only

**Severity:** P4 - Documentation incomplete

**Location:** `bazinga/schemas/event_investigation_iteration.schema.json:62-65`

**Problem:**
```json
"x-dedup-key": {
  "description": "Deduplication key to prevent duplicate events",
  "fields": ["session_id", "group_id", "iteration"]
}
```

This is a custom extension. Nothing reads it. The actual dedup uses idempotency_key column.

**Recommendation:**
Either implement schema-driven dedup or remove x-dedup-key to avoid confusion.

---

## Backward Compatibility Assessment

### ✅ Safe

| Change | Risk | Assessment |
|--------|------|------------|
| idempotency_key column (nullable) | Low | Existing rows work with NULL |
| Partial unique index | Low | Only on non-NULL values |
| New event types in docs | None | Additive change |
| New CLI flags | None | Optional flags |

### ⚠️ Needs Verification

| Change | Risk | Assessment |
|--------|------|------------|
| state_type CHECK constraint | **BROKEN** | 'investigation' not in allowed values |

---

## Summary

| Severity | Count | Issues |
|----------|-------|--------|
| 🔴 Critical | 3 | CHECK constraint, UNIQUE missing, group isolation |
| 🟡 Medium | 3 | Registry not enforced, key format, JSON validation |
| 🟢 Minor | 3 | Temp files, validation scope, schema extension |

### Verdict

**The atomic save-investigation-iteration feature is completely broken** due to the state_type CHECK constraint violation. This is a P0 bug that would cause every invocation to fail with a SQLite constraint error.

Additionally, even if that were fixed, the lack of group isolation means parallel investigations would corrupt each other's state.

---

## Proposed Fixes

### Fix 1: Update state_type CHECK constraint (Schema v18)

```sql
-- Migration v17 → v18
ALTER TABLE state_snapshots RENAME TO state_snapshots_old;

CREATE TABLE state_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    group_id TEXT,  -- NEW: For investigation state isolation
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    state_type TEXT CHECK(state_type IN ('pm', 'orchestrator', 'group_status', 'investigation')),
    state_data TEXT NOT NULL,
    UNIQUE(session_id, state_type, group_id),  -- NEW: Allow replacement
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);

-- Migrate data
INSERT INTO state_snapshots (id, session_id, timestamp, state_type, state_data)
SELECT id, session_id, timestamp, state_type, state_data FROM state_snapshots_old;

DROP TABLE state_snapshots_old;
```

### Fix 2: Update save_investigation_iteration

```python
# Use group_id in upsert
conn.execute("""
    INSERT INTO state_snapshots
    (session_id, group_id, state_type, state_data, timestamp)
    VALUES (?, ?, 'investigation', ?, datetime('now'))
    ON CONFLICT(session_id, state_type, group_id)
    DO UPDATE SET state_data = excluded.state_data, timestamp = excluded.timestamp
""", (session_id, group_id, redacted_state))
```

### Fix 3: Add JSON validation to file reads

```python
# In CLI parsing
try:
    with open(payload_path, 'r') as f:
        content = f.read().strip()
    json.loads(content)  # Validate JSON
    payload = content
except json.JSONDecodeError as e:
    print(f"Error: Invalid JSON in payload file: {e}", file=sys.stderr)
    sys.exit(1)
```

---

## Multi-LLM Review Integration

### OpenAI GPT-5 Validation

OpenAI **confirmed all 3 critical issues** as accurate and identified additional concerns:

#### Additional Issues Raised

| Issue | Severity | Description |
|-------|----------|-------------|
| NULL-unsafe UNIQUE | 🔴 Critical | `UNIQUE(session_id, state_type, group_id)` won't work with NULL group_id - SQLite treats NULLs as distinct |
| Event idempotency collision | 🟡 Medium | Current unique index may collapse distinct per-group events if idempotency_key is malformed |
| Missing indexes | 🟢 Minor | New access patterns need: `idx_state_session_type_group ON (session_id, state_type, group_id, timestamp DESC)` |
| Payload size/DoS | 🟢 Minor | No max size on event payloads - oversized payloads could bloat DB |
| SCHEMA_VERSION fallback | 🟢 Minor | bazinga_db.py has stale fallback `EXPECTED_SCHEMA_VERSION=7` |

### Incorporated Feedback

1. **group_id NOT NULL DEFAULT 'global'**
   - Instead of nullable group_id, use NOT NULL with sentinel value
   - Prevents NULL-unsafe uniqueness issues

2. **Use UPSERT not REPLACE**
   - Replace `INSERT OR REPLACE` with `INSERT ... ON CONFLICT ... DO UPDATE`
   - Avoids delete-insert semantics that can cascade deletes

3. **Event idempotency: include group_id in index**
   - Adjust unique index: `(session_id, event_subtype, group_id, idempotency_key)`
   - Prevents cross-group collisions

4. **Backfill migration safety**
   - Backfill existing pm/orchestrator rows with group_id='global'
   - Recreate indexes, checkpoint WAL, integrity_check, ANALYZE

5. **Add runtime JSON validation for file inputs**
   - Validate with json.loads() after reading --payload-file/--state-file
   - Clear error messages on parse failure

### Rejected Suggestions (With Reasoning)

1. **Separate investigation_state table**
   - OpenAI suggested creating a dedicated table instead of extending state_snapshots
   - **Rejected**: Would require more extensive changes to state APIs. Extending existing table with group_id is simpler and maintains consistency with other state types.

2. **Relax CHECK constraint entirely**
   - OpenAI suggested removing CHECK or using app-level validation
   - **Rejected**: CHECK constraints provide database-level data integrity. Adding new values is a one-time migration cost, but the protection is permanent.

3. **Payload truncation with artifact files**
   - OpenAI suggested storing large payloads as external files
   - **Deferred**: Not needed for current use cases. Can be added later if size becomes an issue.

---

## Revised Proposed Fixes

### Schema v18 Migration (Revised)

```sql
-- Migration v17 → v18: Investigation state isolation

-- Recreate state_snapshots with group_id support
ALTER TABLE state_snapshots RENAME TO state_snapshots_old;

CREATE TABLE state_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    group_id TEXT NOT NULL DEFAULT 'global',  -- NOT NULL with sentinel
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    state_type TEXT CHECK(state_type IN ('pm', 'orchestrator', 'group_status', 'investigation')),
    state_data TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);

-- Create UNIQUE constraint for upsert
CREATE UNIQUE INDEX idx_state_unique
ON state_snapshots(session_id, state_type, group_id);

-- Performance index for queries
CREATE INDEX idx_state_session_type_group
ON state_snapshots(session_id, state_type, group_id, timestamp DESC);

-- Migrate data with group_id backfill
INSERT INTO state_snapshots (id, session_id, group_id, timestamp, state_type, state_data)
SELECT id, session_id, 'global', timestamp, state_type, state_data
FROM state_snapshots_old;

DROP TABLE state_snapshots_old;
```

### Updated save_investigation_iteration (Revised)

```python
def save_investigation_iteration(self, session_id: str, group_id: str,
                                   iteration: int, status: str,
                                   state_data: str, event_payload: str) -> Dict[str, Any]:
    # ... validation and redaction ...

    conn.execute("BEGIN IMMEDIATE")

    # UPSERT state (not INSERT OR REPLACE)
    conn.execute("""
        INSERT INTO state_snapshots
        (session_id, group_id, state_type, state_data, timestamp)
        VALUES (?, ?, 'investigation', ?, datetime('now'))
        ON CONFLICT(session_id, state_type, group_id)
        DO UPDATE SET
            state_data = excluded.state_data,
            timestamp = excluded.timestamp
    """, (session_id, group_id, redacted_state))

    # ... event save with group_id in idempotency check ...
```

### Updated Event Idempotency Index

```sql
-- Replace current index
DROP INDEX IF EXISTS idx_logs_idempotency;

-- New index includes group_id
CREATE UNIQUE INDEX idx_logs_idempotency
ON orchestration_logs(session_id, event_subtype, group_id, idempotency_key)
WHERE idempotency_key IS NOT NULL AND log_type = 'event';
```

### JSON Validation for File Inputs (New)

```python
# In CLI parsing for --payload-file, --state-file, --event-file
try:
    with open(file_path, 'r') as f:
        content = f.read().strip()
    # Validate JSON before accepting
    json.loads(content)
    return content
except json.JSONDecodeError as e:
    print(f"Error: Invalid JSON in file '{file_path}': {e}", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"Error reading file '{file_path}': {e}", file=sys.stderr)
    sys.exit(1)
```

---

## Implementation Priority

| Priority | Issue | Fix |
|----------|-------|-----|
| P0 | state_type CHECK constraint | Schema v18 with 'investigation' |
| P0 | No UNIQUE for upsert | Add UNIQUE(session_id, state_type, group_id) |
| P0 | Group isolation | Add group_id column with NOT NULL DEFAULT 'global' |
| P1 | Event idempotency collisions | Update unique index to include group_id |
| P2 | JSON validation | Add json.loads() validation for file inputs |
| P3 | Temp file cleanup | Add cleanup instructions to investigation_loop.md |

---

## References

- Commit: 8405a57 (Implement all phases of domain skill migration improvements)
- Previous review: research/domain-skill-migration-ultrathink-review.md
- Previous plan: research/domain-skill-migration-implementation-plan.md
- OpenAI review: tmp/ultrathink-reviews/openai-review.md
