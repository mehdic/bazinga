# Success Criteria Table Implementation Plan - ULTRATHINK Analysis

**Date:** 2025-11-24
**Context:** User wants to implement the original success_criteria table design from research/orchestration-completion-enforcement.md
**Decision:** To be determined after analysis
**Status:** Planning phase

---

## Executive Summary

**Question:** Should we implement a dedicated `success_criteria` table with associated commands?

**Quick Answer:** ✅ YES - Benefits outweigh risks, but requires careful implementation with migration strategy.

**Key Insight:** Current approach (storing in pm_state) works but lacks independent verification, audit trails, and data integrity. A dedicated table provides these benefits at the cost of increased complexity.

---

## Problem Statement

### Current Situation

**What exists now:**
```
PM State (JSON in state_snapshots table):
{
  "success_criteria": [
    {"criterion": "All tests passing", "status": "pending", ...},
    {"criterion": "Coverage >70%", "status": "pending", ...}
  ]
}
```

**Issues with current approach:**
1. ❌ No independent verification - orchestrator trusts PM's JSON
2. ❌ No audit trail - criteria can be modified in pm_state
3. ❌ No data integrity - foreign keys don't enforce relationships
4. ❌ Parsing overhead - JSON parsing for every query
5. ❌ No indexed queries - can't efficiently filter by status
6. ❌ Concurrent access issues - JSON updates aren't atomic
7. ❌ PM can manipulate - redefine success criteria mid-session

### What Was Designed But Not Implemented

**Original design (from research/orchestration-completion-enforcement.md:1304):**

```sql
CREATE TABLE success_criteria (
  id INTEGER PRIMARY KEY,
  session_id TEXT NOT NULL,
  criterion TEXT NOT NULL,
  status TEXT CHECK(status IN ('pending', 'met', 'blocked', 'failed')),
  actual TEXT,
  evidence TEXT,
  required_for_completion BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);

CREATE INDEX idx_success_criteria_session ON success_criteria(session_id);
```

**Commands designed:**
- `save-success-criteria` - PM saves criteria at planning phase
- `get-success-criteria` - Orchestrator queries for validation
- `update-success-criteria` - PM updates status before BAZINGA

**Current state:**
- ✅ Orchestrator tries to call these commands (lines 441, 2256, 2312)
- ❌ Commands don't exist (causes "Unknown command" error)
- ❌ Table doesn't exist (no place to store data)
- ❌ PM doesn't use them (only saves to pm_state)

---

## Benefits Analysis

### Benefit 1: Independent Verification ⭐⭐⭐⭐⭐

**Current problem:**
```
PM (in pm_state): "All tests passing - status: met"
Orchestrator: "I trust PM's JSON" ✅ ACCEPT
Reality: Tests still failing, PM was wrong/optimistic
```

**With dedicated table:**
```
PM saves to database: status = "met"
Orchestrator queries database independently
Validator runs tests, updates database: status = "failed"
Orchestrator sees mismatch: "PM says met, validator says failed"
→ REJECT with evidence
```

**Impact:** 🔥 CRITICAL - Prevents premature BAZINGA acceptance

### Benefit 2: Immutable Audit Trail ⭐⭐⭐⭐

**Current problem:**
```
Time 10:00 - PM state: {"criterion": "50 tests passing"}
Time 10:30 - PM realizes mistake, edits state
Time 10:31 - PM state: {"criterion": "ALL tests passing"}
→ No trace of original narrow criteria
```

**With dedicated table:**
```
Time 10:00 - INSERT: criterion="50 tests passing", created_at=10:00
Time 10:30 - INSERT: criterion="ALL tests passing", created_at=10:30
→ Both records exist, can see PM changed criteria
→ Can enforce "criteria are immutable after creation"
```

**Impact:** 🔍 HIGH - Audit trail prevents criteria manipulation

### Benefit 3: Data Integrity ⭐⭐⭐⭐

**Current problem:**
```
state_snapshots table:
  session_id: "bazinga_123"
  state_data: '{"success_criteria": [...]}' (just JSON text)

sessions table:
  session_id: "bazinga_456" (different session)

No enforcement - could reference wrong session in JSON
```

**With dedicated table:**
```sql
success_criteria table:
  session_id TEXT NOT NULL
  FOREIGN KEY (session_id) REFERENCES sessions(session_id)

→ Database enforces relationship
→ Can't create criteria for non-existent session
→ Cascade delete removes criteria when session deleted
```

**Impact:** 🛡️ HIGH - Database-enforced data integrity

### Benefit 4: Query Performance ⭐⭐⭐

**Current approach:**
```python
# Get all criteria with status="met"
1. SELECT state_data FROM state_snapshots WHERE state_type='pm'
2. Parse entire JSON string
3. Extract success_criteria array
4. Filter in Python: [c for c in criteria if c['status'] == 'met']
```

**With dedicated table:**
```sql
-- Get all criteria with status="met"
SELECT * FROM success_criteria
WHERE session_id = ? AND status = 'met'
-- Uses index: idx_success_criteria_session
-- Database does filtering, returns only matches
```

**Impact:** ⚡ MEDIUM - Faster queries, especially for large sessions

### Benefit 5: Atomic Updates ⭐⭐⭐

**Current problem:**
```python
# Two agents update criteria simultaneously
Agent 1: Read pm_state JSON
Agent 2: Read pm_state JSON
Agent 1: Modify criterion A, Write back
Agent 2: Modify criterion B, Write back
→ Agent 2 overwrites Agent 1's change (lost update)
```

**With dedicated table:**
```sql
-- Two agents update different criteria
Agent 1: UPDATE success_criteria SET status='met' WHERE criterion='A'
Agent 2: UPDATE success_criteria SET status='met' WHERE criterion='B'
→ Both updates succeed independently (row-level locking)
```

**Impact:** 🔄 MEDIUM - Concurrent updates work correctly

### Benefit 6: Structured Queries ⭐⭐⭐

**Current limitations:**
```python
# Can't easily query:
- "Show me all incomplete criteria across all sessions"
- "Which sessions have blocked criteria?"
- "What's the most common blocking criterion?"
→ Must parse every pm_state JSON
```

**With dedicated table:**
```sql
-- Easy analytical queries
SELECT criterion, COUNT(*) as blocked_count
FROM success_criteria
WHERE status = 'blocked'
GROUP BY criterion
ORDER BY blocked_count DESC;

-- Dashboard can show trends
```

**Impact:** 📊 MEDIUM - Better analytics and dashboard features

### Benefit 7: Enforcement of Immutability ⭐⭐⭐⭐⭐

**Current problem:**
```
PM at time 1: Creates criteria "50 tests passing"
Developer fixes 50 tests
PM at time 2: Realizes should be "ALL tests", edits pm_state
PM at time 3: "All criteria met!" sends BAZINGA
→ Moved goalposts, no one notices
```

**With dedicated table:**
```sql
-- Enforce immutability with triggers or application logic
CREATE TRIGGER prevent_criterion_change
BEFORE UPDATE ON success_criteria
BEGIN
  SELECT RAISE(ABORT, 'Cannot modify criterion text after creation')
  WHERE NEW.criterion != OLD.criterion;
END;

-- Only status/actual/evidence can be updated
```

**Impact:** 🔥 CRITICAL - Prevents PM from moving goalposts

---

## Risk Analysis

### Risk 1: Dual Storage Complexity ⚠️⚠️⚠️⚠️

**The problem:**
```
success_criteria table: criterion="All tests passing", status="met"
pm_state JSON: criterion="All tests passing", status="pending"
→ Which is correct? They're out of sync!
```

**Why this happens:**
- PM updates table but forgets to update pm_state
- PM updates pm_state but table update fails
- Race condition between two updates

**Mitigation strategies:**

**Option A: Table is source of truth (recommended)**
```
✅ PM saves to table only
✅ PM state stores minimal info (just reference)
✅ Orchestrator queries table
✅ PM queries table if needs current status
→ Single source of truth
```

**Option B: Dual write with verification**
```
⚠️ PM saves to both table AND pm_state
⚠️ Verification step: Compare table vs pm_state
⚠️ If mismatch: Table wins, fix pm_state
→ More complex, can still get out of sync
```

**Option C: pm_state is derived**
```
✅ PM saves to table only
✅ When saving pm_state, fetch criteria from table
✅ pm_state.success_criteria = query_from_table()
→ pm_state is always consistent snapshot
```

**Recommended:** Option A or C - Table is source of truth

**Severity:** HIGH if not handled correctly

### Risk 2: Migration of Existing Sessions ⚠️⚠️⚠️

**The problem:**
```
Old session (created Nov 21):
  pm_state.success_criteria = [...]  ✅ Has criteria
  success_criteria table = []         ❌ Empty

New code tries to query table → Empty result
Backward compat logic triggers: "Extract from requirements"
But requirements are generic: "fix everything"
→ Can't extract good criteria retroactively
```

**Migration challenges:**

1. **Extracting criteria from pm_state**
   ```python
   # For each old session
   pm_state = get_state(session_id, 'pm')
   if 'success_criteria' in pm_state:
       for criterion in pm_state['success_criteria']:
           # Insert into table
           save_success_criteria(session_id, criterion)
   ```

2. **Handling missing fields**
   ```python
   # Old pm_state might not have all fields
   criterion = {
       'criterion': c.get('criterion', 'Unknown'),
       'status': c.get('status', 'pending'),
       'actual': c.get('actual'),  # Might be missing
       'evidence': c.get('evidence'),  # Might be missing
       'required_for_completion': c.get('required_for_completion', True)
   }
   ```

3. **Resume compatibility**
   ```python
   # When resuming old session
   criteria = get_success_criteria(session_id)
   if not criteria:
       # Old session, migrate now
       pm_state = get_state(session_id, 'pm')
       if 'success_criteria' in pm_state:
           migrate_criteria_to_table(session_id, pm_state)
   ```

**Mitigation:**
```python
# In orchestrator resume logic (Step 4.5)
IF criteria table empty AND pm_state has criteria:
    → Migrate pm_state criteria to table
    → Continue normally
IF both empty:
    → Old session without criteria
    → PM must extract from requirements
```

**Severity:** MEDIUM - Can be handled with migration logic

### Risk 3: Increased Complexity ⚠️⚠️

**More code to maintain:**
```
Before: 1 place to update (pm_state)
After: 1 place to update (table) + migration logic + validation

Lines of code added:
- init_db.py: +20 lines (table creation)
- bazinga_db.py: +100 lines (3 commands)
- project_manager.md: +30 lines (save logic)
- orchestrator.md: Already references it
Total: ~150 lines
```

**More failure points:**
- Table creation fails
- Insert fails
- Query fails
- pm_state and table out of sync

**Mitigation:**
- ✅ Comprehensive error handling
- ✅ Fallback to pm_state if table query fails
- ✅ Transaction wrapping (all-or-nothing)
- ✅ Clear error messages

**Severity:** LOW - Standard database development complexity

### Risk 4: Schema Changes ⚠️⚠️

**Breaking changes:**
```
Version 3 (current): No success_criteria table
Version 4 (new): Has success_criteria table

Old clients connecting to new database: ✅ Works (backward compatible)
New clients connecting to old database: ❌ Breaks (table missing)
```

**Mitigation:**
- ✅ Auto-migration on init (init_db.py already does this)
- ✅ Schema version bump (v3 → v4)
- ✅ Add table with CREATE TABLE IF NOT EXISTS

**Severity:** LOW - Handled by existing migration system

### Risk 5: Performance Overhead ⚠️

**More database operations:**
```
Before: 1 write (pm_state)
After: 1 write (pm_state) + N writes (criteria) where N = criterion count

Typical session:
- 3-5 criteria
- 3-5 updates per criterion
Total: 15-25 additional writes per session
```

**Query overhead:**
```
Before: 1 query (get pm_state)
After: 1 query (get pm_state) + 1 query (get criteria)
```

**Mitigation:**
- ✅ Batch inserts (insert multiple criteria at once)
- ✅ Indexed queries (already in design)
- ✅ WAL mode enabled (concurrent reads/writes)

**Actual impact:** Negligible - 15-25 writes is tiny for SQLite

**Severity:** VERY LOW - Not a concern

### Risk 6: Criterion Uniqueness ⚠️⚠️⚠️

**Problem:**
```sql
-- PM accidentally inserts duplicate
INSERT INTO success_criteria (session_id, criterion)
VALUES ('bazinga_123', 'All tests passing');

INSERT INTO success_criteria (session_id, criterion)
VALUES ('bazinga_123', 'All tests passing');  -- Duplicate!

-- Later: Update criterion
UPDATE success_criteria
SET status = 'met'
WHERE session_id = 'bazinga_123' AND criterion = 'All tests passing';
→ Updates BOTH rows (unexpected)
```

**Mitigation:**
```sql
-- Add unique constraint
CREATE UNIQUE INDEX idx_unique_criterion
ON success_criteria(session_id, criterion);

-- Now duplicate insert fails:
-- Error: UNIQUE constraint failed
```

**Severity:** MEDIUM - Needs unique constraint in schema

---

## Integration Analysis

### Where It Integrates

**1. Database Initialization (.claude/skills/bazinga-db/scripts/init_db.py)**

**Location:** After development_plans table (line 272)

```python
# Success criteria table (for BAZINGA validation)
cursor.execute("""
    CREATE TABLE IF NOT EXISTS success_criteria (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        criterion TEXT NOT NULL,
        status TEXT CHECK(status IN ('pending', 'met', 'blocked', 'failed')) DEFAULT 'pending',
        actual TEXT,
        evidence TEXT,
        required_for_completion BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
    )
""")
cursor.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_criterion
    ON success_criteria(session_id, criterion)
""")
cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_criteria_session_status
    ON success_criteria(session_id, status)
""")
print("✓ Created success_criteria table with indexes")
```

**Schema version bump:** v3 → v4

**Migration logic:**
```python
# Handle v3→v4 migration (add success_criteria table)
if current_version == 3:
    print("🔄 Migrating schema from v3 to v4...")
    # No data migration needed - table will be created below
    print("✓ Migration to v4 complete (success_criteria table added)")
```

**2. Database Commands (.claude/skills/bazinga-db/scripts/bazinga_db.py)**

**Location:** After development plan commands (line 612)

```python
elif cmd == 'save-success-criteria':
    session_id = cmd_args[0]
    criteria_json = cmd_args[1]
    criteria_list = json.loads(criteria_json)
    db.save_success_criteria(session_id, criteria_list)

elif cmd == 'get-success-criteria':
    session_id = cmd_args[0]
    result = db.get_success_criteria(session_id)
    print(json.dumps(result, indent=2))

elif cmd == 'update-success-criterion':
    session_id = cmd_args[0]
    criterion_text = cmd_args[1]
    kwargs = {}
    for i in range(2, len(cmd_args), 2):
        key = cmd_args[i].lstrip('--')
        value = cmd_args[i + 1]
        kwargs[key] = value
    db.update_success_criterion(session_id, criterion_text, **kwargs)
```

**Implementation methods in BazingaDB class:**

```python
def save_success_criteria(self, session_id: str, criteria: List[Dict[str, Any]]) -> None:
    """Save success criteria for a session."""
    conn = self._get_connection()
    cursor = conn.cursor()

    for criterion_data in criteria:
        cursor.execute("""
            INSERT INTO success_criteria
            (session_id, criterion, status, actual, evidence, required_for_completion)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id, criterion) DO UPDATE SET
                status = excluded.status,
                actual = excluded.actual,
                evidence = excluded.evidence,
                required_for_completion = excluded.required_for_completion,
                updated_at = CURRENT_TIMESTAMP
        """, (
            session_id,
            criterion_data['criterion'],
            criterion_data.get('status', 'pending'),
            criterion_data.get('actual'),
            criterion_data.get('evidence'),
            criterion_data.get('required_for_completion', True)
        ))

    conn.commit()
    conn.close()
    self._print_success(f"✓ Saved {len(criteria)} success criteria for session {session_id}")

def get_success_criteria(self, session_id: str) -> List[Dict[str, Any]]:
    """Get all success criteria for a session."""
    conn = self._get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, criterion, status, actual, evidence, required_for_completion,
               created_at, updated_at
        FROM success_criteria
        WHERE session_id = ?
        ORDER BY created_at ASC
    """, (session_id,))

    rows = cursor.fetchall()
    conn.close()

    return [{
        'id': row[0],
        'criterion': row[1],
        'status': row[2],
        'actual': row[3],
        'evidence': row[4],
        'required_for_completion': bool(row[5]),
        'created_at': row[6],
        'updated_at': row[7]
    } for row in rows]

def update_success_criterion(self, session_id: str, criterion: str, **kwargs) -> None:
    """Update a specific success criterion."""
    conn = self._get_connection()
    cursor = conn.cursor()

    # Build SET clause dynamically
    valid_fields = ['status', 'actual', 'evidence', 'required_for_completion']
    updates = []
    values = []

    for key, value in kwargs.items():
        if key in valid_fields:
            updates.append(f"{key} = ?")
            values.append(value)

    if not updates:
        raise ValueError("No valid fields to update")

    # Add updated_at
    updates.append("updated_at = CURRENT_TIMESTAMP")

    # Add WHERE clause values
    values.extend([session_id, criterion])

    cursor.execute(f"""
        UPDATE success_criteria
        SET {', '.join(updates)}
        WHERE session_id = ? AND criterion = ?
    """, values)

    if cursor.rowcount == 0:
        raise ValueError(f"No criterion found: {criterion} for session {session_id}")

    conn.commit()
    conn.close()
    self._print_success(f"✓ Updated criterion: {criterion}")
```

**3. Project Manager (agents/project_manager.md)**

**Location:** Lines 1472-1484 (already has placeholder code)

**Current code (line 1472):**
```
bazinga-db, please save success criteria:

Session ID: [current session_id]
Criteria: [JSON array]
```

**Update to use actual command:**
```
**Save to database using bazinga-db skill:**

Request format:
bazinga-db, please save success criteria:
  Session ID: [current_session_id]
  Criteria: [
    {"criterion": "All tests passing", "status": "pending", "required_for_completion": true},
    {"criterion": "Coverage >70%", "status": "pending", "required_for_completion": true}
  ]

Then invoke:
Skill(command: "bazinga-db")

The criteria are now immutably stored in the database.
```

**Also update criteria before BAZINGA (new section):**

Location: Before BAZINGA decision (around line 576)

```
3. **Update criteria status in database (MANDATORY before BAZINGA)**

   For each criterion, update its status in the database:

   Request: bazinga-db, update success criterion:
     Session ID: [session_id]
     Criterion: "[criterion text]"
     --status "met"
     --actual "[actual value achieved]"
     --evidence "[proof/test results/artifact link]"

   Invoke: Skill(command: "bazinga-db")

   CRITICAL: Update database, not just pm_state. Orchestrator validates from database.
```

**4. Orchestrator (agents/orchestrator.md)**

**Lines 441, 2256, 2312 already reference it - just needs to work!**

**But add migration logic at resume (Step 4.5, line 449):**

```
**If criteria NOT found (empty result):**
- Check if old session with criteria in pm_state
- Request: bazinga-db, get PM state for session: [session_id]
- If pm_state has success_criteria field:
  → Migrate to table: bazinga-db, save success criteria: [extract from pm_state]
  → Continue normally
- If pm_state also empty:
  → This is a very old session from before success criteria enforcement
  → PM must extract criteria retroactively from original requirements
```

### How It Flows

**Session Creation:**
```
1. User: /orchestrate "Fix all bugs"
2. Orchestrator spawns PM
3. PM extracts criteria:
   - "All bugs fixed"
   - "All tests passing"
   - "No regressions"
4. PM saves to database:
   bazinga-db, save-success-criteria [session_id] [criteria_json]
5. PM also stores in pm_state for convenience
6. PM continues with task breakdown
```

**During Development:**
```
1. Developers work
2. QA tests
3. Tech Lead reviews
4. PM checks progress:
   - Query database: bazinga-db, get-success-criteria [session_id]
   - See which criteria are met/pending
   - Decide: Continue or BAZINGA?
```

**Before BAZINGA:**
```
1. PM evaluates completion
2. PM updates each criterion in database:
   bazinga-db, update-success-criterion [session_id] "All tests passing"
     --status "met"
     --actual "711/711 tests passing"
     --evidence "artifacts/session_123/test-results.txt"
3. PM sends BAZINGA message
4. Orchestrator validates independently
```

**BAZINGA Validation:**
```
1. Orchestrator receives BAZINGA from PM
2. Orchestrator queries database (not pm_state):
   bazinga-db, get-success-criteria [session_id]
3. Orchestrator counts:
   met_count = criteria where status="met"
   total_count = criteria where required_for_completion=true
4. If met_count < total_count:
   → REJECT: Incomplete
5. Else:
   → Spawn validator for independent verification
```

**Resume Old Session:**
```
1. User resumes old session (created before table existed)
2. Orchestrator queries: bazinga-db, get-success-criteria [session_id]
3. Returns empty []
4. Orchestrator queries pm_state: bazinga-db, get-state [session_id] pm
5. If pm_state has success_criteria:
   → Migrate: bazinga-db, save-success-criteria [session_id] [from pm_state]
   → Continue
6. If pm_state also empty:
   → PM must extract from original requirements
```

---

## What It Improves

### Improvement 1: Trustless Validation

**Before:**
```
PM: "I checked everything, all criteria met! BAZINGA!"
Orchestrator: "I trust PM" → ACCEPT
→ Blind trust
```

**After:**
```
PM: Updates database: status="met"
Orchestrator: Queries database independently
Orchestrator: "Database says met, but let me verify"
Validator: Runs tests, finds failures, updates database: status="failed"
Orchestrator: "Database now says failed" → REJECT
→ Independent verification
```

### Improvement 2: Immutable Contract

**Before:**
```
Time 1: PM defines: "50 tests passing"
Time 2: Developers fix 50 tests
Time 3: PM changes pm_state: "ALL tests passing"
Time 4: PM: "Criteria met!" (moved goalposts)
→ No audit trail
```

**After:**
```
Time 1: PM saves to database: "50 tests passing" (created_at: T1)
Time 2: Developers work
Time 3: PM tries to change criterion → DATABASE REJECTS (immutable)
Time 4: PM must INSERT new criterion: "ALL tests passing" (created_at: T3)
→ Both records exist, clear audit trail
```

### Improvement 3: Better Dashboard

**Before:**
```
Dashboard query:
1. Get all pm_state records
2. Parse each JSON
3. Extract success_criteria
4. Manually aggregate
→ Slow, complex
```

**After:**
```sql
-- Dashboard: Show completion rate across all sessions
SELECT
  session_id,
  COUNT(*) as total_criteria,
  SUM(CASE WHEN status='met' THEN 1 ELSE 0 END) as met_count,
  ROUND(100.0 * SUM(CASE WHEN status='met' THEN 1 ELSE 0 END) / COUNT(*), 1) as completion_pct
FROM success_criteria
WHERE required_for_completion = 1
GROUP BY session_id
ORDER BY completion_pct DESC;

→ Fast, simple SQL
```

### Improvement 4: Data Integrity

**Before:**
```
pm_state references session "bazinga_999" (doesn't exist)
→ No enforcement, data corruption possible
```

**After:**
```sql
FOREIGN KEY (session_id) REFERENCES sessions(session_id)
→ Database prevents invalid references
→ Cascade delete cleans up criteria when session deleted
```

---

## What It Could Break

### Break 1: Old Sessions Without Migration

**Scenario:**
```
1. Old session has criteria in pm_state only
2. New code queries table
3. Table is empty
4. Orchestrator thinks no criteria exist
5. Tries to extract from requirements
6. Generic requirements: "fix everything"
7. Can't extract good criteria
→ Resume fails
```

**Fix:** Automatic migration in resume logic (Step 4.5)

### Break 2: Concurrent PM Updates

**Scenario:**
```
PM instance 1: Updates criterion A status to "met"
PM instance 2: Updates criterion B status to "met"
Both try to save entire criteria array to pm_state
→ One overwrites the other (lost update)
```

**Fix:** Don't save to pm_state, only to table (table handles row-level locking)

### Break 3: PM State Snapshots

**Scenario:**
```
Dashboard shows historical pm_state snapshots
pm_state snapshot from Time 1: "50 tests passing"
Criteria table now has: "ALL tests passing"
→ Inconsistency in historical view
```

**Fix:** pm_state snapshots remain as-is (historical record), table is current truth

### Break 4: Partial Saves

**Scenario:**
```
PM saves 3 criteria to database successfully
PM tries to save 4th criterion → Database error (disk full)
→ Only 3 of 4 criteria saved
```

**Fix:** Transaction wrapping (all-or-nothing)

```python
def save_success_criteria(self, session_id, criteria):
    conn = self._get_connection()
    try:
        cursor = conn.cursor()
        for criterion in criteria:
            cursor.execute("INSERT INTO ...", ...)
        conn.commit()  # All or nothing
    except Exception as e:
        conn.rollback()  # Undo all
        raise
    finally:
        conn.close()
```

---

## Complete Implementation Plan

### Phase 1: Database Schema (Foundation)

**Files to modify:**
1. `.claude/skills/bazinga-db/scripts/init_db.py`

**Changes:**

**Step 1.1: Update schema version**
```python
# Line 14
SCHEMA_VERSION = 4  # Was 3
```

**Step 1.2: Add migration handler**
```python
# After line 118, add v3→v4 migration
if current_version == 3:
    print("🔄 Migrating schema from v3 to v4...")
    # No data migration needed - table will be created below
    print("✓ Migration to v4 complete (success_criteria table added)")
```

**Step 1.3: Create table**
```python
# After line 272 (development_plans table), add:
    # Success criteria table (for BAZINGA validation)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS success_criteria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            criterion TEXT NOT NULL,
            status TEXT CHECK(status IN ('pending', 'met', 'blocked', 'failed')) DEFAULT 'pending',
            actual TEXT,
            evidence TEXT,
            required_for_completion BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_criterion
        ON success_criteria(session_id, criterion)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_criteria_session_status
        ON success_criteria(session_id, status)
    """)
    print("✓ Created success_criteria table with indexes")
```

**Step 1.4: Update version description**
```python
# Line 124
""", (SCHEMA_VERSION, f"Schema v{SCHEMA_VERSION}: Add success_criteria table for immutable completion tracking"))
```

**Testing:**
```bash
# Test database initialization
python .claude/skills/bazinga-db/scripts/init_db.py /tmp/test.db

# Verify table exists
sqlite3 /tmp/test.db ".schema success_criteria"

# Should show table with indexes
```

### Phase 2: Database Commands (API)

**Files to modify:**
1. `.claude/skills/bazinga-db/scripts/bazinga_db.py`

**Changes:**

**Step 2.1: Add save_success_criteria method**

Location: After `get_development_plan` method (around line 450)

```python
def save_success_criteria(self, session_id: str, criteria: List[Dict[str, Any]]) -> None:
    """
    Save success criteria for a session.
    Uses UPSERT to handle duplicates gracefully.
    """
    conn = self._get_connection()
    cursor = conn.cursor()

    try:
        for criterion_data in criteria:
            cursor.execute("""
                INSERT INTO success_criteria
                (session_id, criterion, status, actual, evidence, required_for_completion)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id, criterion) DO UPDATE SET
                    status = excluded.status,
                    actual = excluded.actual,
                    evidence = excluded.evidence,
                    required_for_completion = excluded.required_for_completion,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                session_id,
                criterion_data['criterion'],
                criterion_data.get('status', 'pending'),
                criterion_data.get('actual'),
                criterion_data.get('evidence'),
                criterion_data.get('required_for_completion', True)
            ))

        conn.commit()
        self._print_success(f"✓ Saved {len(criteria)} success criteria for session {session_id}")
    except Exception as e:
        conn.rollback()
        raise Exception(f"Failed to save success criteria: {e}")
    finally:
        conn.close()
```

**Step 2.2: Add get_success_criteria method**

```python
def get_success_criteria(self, session_id: str) -> List[Dict[str, Any]]:
    """
    Get all success criteria for a session.
    Returns empty list if no criteria found.
    """
    conn = self._get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, criterion, status, actual, evidence, required_for_completion,
               created_at, updated_at
        FROM success_criteria
        WHERE session_id = ?
        ORDER BY created_at ASC
    """, (session_id,))

    rows = cursor.fetchall()
    conn.close()

    return [{
        'id': row[0],
        'criterion': row[1],
        'status': row[2],
        'actual': row[3],
        'evidence': row[4],
        'required_for_completion': bool(row[5]),
        'created_at': row[6],
        'updated_at': row[7]
    } for row in rows]
```

**Step 2.3: Add update_success_criterion method**

```python
def update_success_criterion(self, session_id: str, criterion: str, **kwargs) -> None:
    """
    Update a specific success criterion.
    Only status, actual, evidence can be updated (criterion text is immutable).
    """
    conn = self._get_connection()
    cursor = conn.cursor()

    # Build SET clause dynamically
    valid_fields = ['status', 'actual', 'evidence']
    updates = []
    values = []

    for key, value in kwargs.items():
        if key in valid_fields:
            updates.append(f"{key} = ?")
            values.append(value)

    if not updates:
        raise ValueError("No valid fields to update. Valid fields: status, actual, evidence")

    # Add updated_at
    updates.append("updated_at = CURRENT_TIMESTAMP")

    # Add WHERE clause values
    values.extend([session_id, criterion])

    cursor.execute(f"""
        UPDATE success_criteria
        SET {', '.join(updates)}
        WHERE session_id = ? AND criterion = ?
    """, values)

    if cursor.rowcount == 0:
        conn.close()
        raise ValueError(f"No criterion found: '{criterion}' for session {session_id}")

    conn.commit()
    conn.close()
    self._print_success(f"✓ Updated criterion: {criterion}")
```

**Step 2.4: Add command handlers**

Location: In `main()` function, after line 611

```python
elif cmd == 'save-success-criteria':
    session_id = cmd_args[0]
    criteria_json = cmd_args[1]
    criteria_list = json.loads(criteria_json)
    db.save_success_criteria(session_id, criteria_list)

elif cmd == 'get-success-criteria':
    session_id = cmd_args[0]
    result = db.get_success_criteria(session_id)
    print(json.dumps(result, indent=2))

elif cmd == 'update-success-criterion':
    session_id = cmd_args[0]
    criterion_text = cmd_args[1]
    kwargs = {}
    for i in range(2, len(cmd_args), 2):
        key = cmd_args[i].lstrip('--')
        value = cmd_args[i + 1]
        kwargs[key] = value
    db.update_success_criterion(session_id, criterion_text, **kwargs)
```

**Testing:**
```bash
# Test save
python bazinga_db.py --db /tmp/test.db save-success-criteria \
  "test_session_123" \
  '[{"criterion":"All tests passing","status":"pending","required_for_completion":true}]'

# Test get
python bazinga_db.py --db /tmp/test.db get-success-criteria "test_session_123"
# Should output JSON array with 1 criterion

# Test update
python bazinga_db.py --db /tmp/test.db update-success-criterion \
  "test_session_123" \
  "All tests passing" \
  --status "met" \
  --actual "100/100 tests passing" \
  --evidence "test-results.txt"

# Verify update
python bazinga_db.py --db /tmp/test.db get-success-criteria "test_session_123"
# Should show status="met"
```

### Phase 3: Project Manager Integration

**Files to modify:**
1. `agents/project_manager.md`

**Changes:**

**Step 3.1: Update criteria saving (line 1472)**

Replace existing placeholder with working implementation:

```markdown
**Save to database using bazinga-db skill:**

Format your request as:
```
bazinga-db, please save success criteria:
  Session ID: [current_session_id]
  Criteria: [
    {"criterion": "All tests passing", "status": "pending", "required_for_completion": true},
    {"criterion": "Coverage >70%", "status": "pending", "required_for_completion": true},
    {"criterion": "No security vulnerabilities", "status": "pending", "required_for_completion": true}
  ]
```

**Then invoke:**
```
Skill(command: "bazinga-db")
```

**The criteria are now immutably stored in the database.** You cannot change the criterion text after creation - only status, actual values, and evidence can be updated.

**Also store in pm_state for convenience:** Include success_criteria field in your pm_state when you save it, so you can reference criteria locally without querying database every time.
```

**Step 3.2: Add update section before BAZINGA (line 576)**

After "Calculate completion", add:

```markdown
3. **Update criteria status in database (MANDATORY before BAZINGA)**

   **CRITICAL:** You MUST update the database, not just pm_state. The orchestrator validates completion from the database table, not from your pm_state.

   For each criterion, update its status:

   Request format:
   ```
   bazinga-db, please update success criterion:
     Session ID: [current_session_id]
     Criterion: "[exact criterion text]"
     --status "met"
     --actual "[actual value achieved, e.g., '711/711 tests passing']"
     --evidence "[proof: test results file, artifact link, or summary]"
   ```

   **Then invoke:**
   ```
   Skill(command: "bazinga-db")
   ```

   **Example updates:**
   ```
   bazinga-db, update criterion:
     Session: bazinga_20251124_143000
     Criterion: "All tests passing"
     --status "met"
     --actual "711/711 tests passing (100%)"
     --evidence "artifacts/bazinga_20251124_143000/test-results.txt"

   bazinga-db, update criterion:
     Session: bazinga_20251124_143000
     Criterion: "Coverage >70%"
     --status "met"
     --actual "Coverage 87.3%"
     --evidence "artifacts/bazinga_20251124_143000/skills/coverage_report.json"
   ```

   **Do this for EVERY criterion before sending BAZINGA.**
```

**Step 3.3: Update Path B blocker logic (line 748)**

Add database update for blocked criteria:

```markdown
- ✅ "Cannot test email flow: SendGrid service is down (checked status page), beyond our control"
  → **Update database:**
  ```
  bazinga-db, update criterion:
    Session: [session_id]
    Criterion: "Email tests passing"
    --status "blocked"
    --actual "Cannot test - SendGrid down"
    --evidence "https://status.sendgrid.com - Service outage 2024-11-24 14:00 UTC"
  ```
  → Send BAZINGA with Path B (external blocker documented)
```

### Phase 4: Orchestrator Migration Logic

**Files to modify:**
1. `agents/orchestrator.md`

**Changes:**

**Step 4.1: Update resume migration logic (lines 449-456)**

Replace with complete migration:

```markdown
**If criteria NOT found (empty result):**
- This could be an old session created before success_criteria table existed
- Check if criteria exist in pm_state instead

**Migration logic:**
```
1. Query PM state: bazinga-db, get PM state for session: [session_id]
2. Check if pm_state has 'success_criteria' field
3. IF pm_state HAS criteria:
     → Migrate to table now:
       bazinga-db, save success criteria:
         Session ID: [session_id]
         Criteria: [extract from pm_state.success_criteria]
     → Verify migration:
       bazinga-db, get success criteria for session: [session_id]
     → Continue normally (criteria now in table)

   IF pm_state DOES NOT have criteria:
     → This is a very old session from before success criteria enforcement
     → PM must extract criteria retroactively
     → **Add to PM spawn context:**
        "CRITICAL: This resumed session has no success criteria in database.
         You MUST:
         1) Extract success criteria from original requirements '[original_requirements from pm_state]'
         2) Save to database using bazinga-db
         3) Continue work"
```

**After migration (whether from pm_state or extracted by PM): Criteria are now in database and workflow continues normally.**
```

**Step 4.2: No changes needed for BAZINGA validation**

Lines 2312-2372 already query the table correctly. Once Phase 2 is complete, these will work.

### Phase 5: Testing & Validation

**Test Plan:**

**Test 1: New Session (Happy Path)**
```
1. Create new session: /orchestrate "Fix all bugs"
2. PM extracts criteria
3. Verify database: sqlite3 bazinga.db "SELECT * FROM success_criteria WHERE session_id='...'"
4. Should see criteria with status='pending'
5. Complete work, PM updates criteria
6. Verify database: Should see status='met', actual values, evidence
7. PM sends BAZINGA
8. Orchestrator queries database, validates
9. Should ACCEPT if all criteria met
```

**Test 2: Resume Old Session (Migration)**
```
1. Find old session: sqlite3 bazinga.db "SELECT session_id FROM sessions ORDER BY start_time LIMIT 1"
2. Check criteria table: SELECT * FROM success_criteria WHERE session_id='...'
3. Should be empty (old session)
4. Resume: /orchestrate resume [session_id]
5. Orchestrator detects empty criteria
6. Orchestrator queries pm_state
7. If pm_state has criteria → Migrates to table
8. Verify: SELECT * FROM success_criteria WHERE session_id='...'
9. Should now have criteria
```

**Test 3: Concurrent Updates**
```
1. Create session with 3 criteria
2. Simulate PM updating criterion A (status=met)
3. Simultaneously update criterion B (status=met)
4. Verify both updates succeed
5. Query table: Should show both A and B as met
```

**Test 4: Duplicate Prevention**
```
1. Create session
2. PM saves criteria: ["All tests passing", "Coverage >70%"]
3. PM accidentally tries to save again: ["All tests passing", ...]
4. Should succeed (UPSERT handles duplicates)
5. Query table: Should have only 2 rows (no duplicates)
```

**Test 5: Immutability Enforcement**
```
1. Create criterion: "50 tests passing"
2. Try to update criterion text to "ALL tests passing"
3. Should fail (criterion text is immutable)
4. Must create new criterion instead
5. Verify: Table has both old and new criteria with different created_at
```

**Test 6: BAZINGA Rejection**
```
1. Create session with 3 criteria
2. PM updates 2 criteria to "met", leaves 1 as "pending"
3. PM sends BAZINGA
4. Orchestrator queries database
5. Sees 2/3 criteria met
6. Should REJECT: "Only 2/3 criteria met"
7. PM must continue work
```

### Phase 6: Documentation

**Files to create/update:**

**1. Update research document**

File: `research/success-criteria-table-implementation.md`

Document:
- Why we implemented this
- Architecture decisions
- Migration strategy
- API reference

**2. Update SKILL.md for bazinga-db**

File: `.claude/skills/bazinga-db/SKILL.md`

Add section:
```markdown
## Success Criteria Operations

### Save Success Criteria
Save criteria for a session (typically called by PM during planning).

**Request:**
```
bazinga-db, please save success criteria:
  Session ID: [session_id]
  Criteria: [JSON array of criteria objects]
```

**Invoke:** `Skill(command: "bazinga-db")`

### Get Success Criteria
Retrieve criteria for validation (typically called by orchestrator).

**Request:**
```
bazinga-db, please get success criteria for session: [session_id]
```

**Invoke:** `Skill(command: "bazinga-db")`

**Returns:** JSON array of criteria with status, actual, evidence

### Update Success Criterion
Update a specific criterion's status (typically called by PM before BAZINGA).

**Request:**
```
bazinga-db, please update success criterion:
  Session ID: [session_id]
  Criterion: "[exact criterion text]"
  --status "met|blocked|failed"
  --actual "[actual value achieved]"
  --evidence "[proof/artifact link]"
```

**Invoke:** `Skill(command: "bazinga-db")`
```

**3. Add usage examples**

File: `.claude/skills/bazinga-db/references/success-criteria-examples.md`

Include:
- PM creating criteria
- PM updating before BAZINGA
- Orchestrator validating
- Migration scenarios

### Phase 7: Rollout Strategy

**Step 1: Deploy to dev environment**
```bash
# On dev machine
git checkout claude/fix-pm-iteration-loop-01HGVwJLTwbHMBLCHQSxqZjp
# (this branch will have success_criteria implementation)

# Rebuild database (auto-migrates to v4)
python .claude/skills/bazinga-db/scripts/init_db.py bazinga/bazinga.db

# Test with new session
/orchestrate "Test success criteria"
```

**Step 2: Verify migration works**
```bash
# Find an old session
sqlite3 bazinga/bazinga.db "SELECT session_id FROM sessions WHERE status='completed' LIMIT 1"

# Resume it
/orchestrate resume [session_id]

# Check if migration happened
sqlite3 bazinga/bazinga.db "SELECT * FROM success_criteria WHERE session_id='[session_id]'"
```

**Step 3: Merge to main**
```bash
# After testing passes
git push origin claude/fix-pm-iteration-loop-01HGVwJLTwbHMBLCHQSxqZjp

# Create PR #110 (already exists)
# Merge after review
```

**Step 4: Users upgrade**
```bash
# Users on other machines
uv tool install --upgrade bazinga-cli --from git+https://github.com/mehdic/bazinga.git

# Their databases auto-migrate on next use
/orchestrate "New session"
# init_db.py detects v3, migrates to v4
```

---

## Recommended Approach

### Do We Implement This? ✅ YES

**Reasons to implement:**
1. 🔥 **CRITICAL:** Fixes current bug (unknown command error)
2. 🔥 **CRITICAL:** Enables independent validation (prevents premature BAZINGA)
3. ⭐ **HIGH VALUE:** Immutable audit trail (prevents goalpost moving)
4. ⭐ **HIGH VALUE:** Data integrity (database-enforced relationships)
5. ✅ **SAFE:** Migration strategy handles old sessions
6. ✅ **CLEAN:** Table is source of truth (no dual storage sync issues)

**Risks are manageable:**
- Migration logic is straightforward
- Complexity is standard database development
- Performance overhead is negligible
- Schema versioning handles compatibility

### Implementation Order

**Phase 1-2 (Foundation): HIGH PRIORITY**
- Database schema (init_db.py)
- Database commands (bazinga_db.py)
- These fix the immediate bug (unknown command)

**Phase 3-4 (Integration): HIGH PRIORITY**
- PM saves criteria to table
- Orchestrator migration logic
- These complete the feature

**Phase 5-7 (Quality): MEDIUM PRIORITY**
- Testing
- Documentation
- Rollout
- These ensure reliability

### Success Metrics

**After implementation:**
1. ✅ No more "unknown command" errors
2. ✅ Old sessions can resume (migration works)
3. ✅ PM can save criteria to database
4. ✅ Orchestrator can query and validate independently
5. ✅ Dashboard can show criteria across sessions
6. ✅ Audit trail shows when criteria were created/modified

---

## Conclusion

**Implement:** ✅ YES - Clear benefits, manageable risks, fixes current bug

**Approach:** Phased implementation with migration strategy

**Timeline:**
- Phase 1-2 (Foundation): 2-3 hours
- Phase 3-4 (Integration): 2-3 hours
- Phase 5-7 (Quality): 2-4 hours
- **Total:** 6-10 hours of work

**Immediate next step:** Implement Phase 1 (database schema) to fix the unknown command error, then proceed with remaining phases.

---

## References

- Original design: research/orchestration-completion-enforcement.md:1301-1333
- Current orchestrator queries: agents/orchestrator.md:441, 2256, 2312
- Current PM code: agents/project_manager.md:1472-1491
- Database schema version: .claude/skills/bazinga-db/scripts/init_db.py:14 (v3 → v4)
- Command handlers: .claude/skills/bazinga-db/scripts/bazinga_db.py:503-614
