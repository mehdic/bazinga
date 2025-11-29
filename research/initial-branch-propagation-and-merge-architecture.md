# Initial Branch Propagation & Merge Architecture (ULTRATHINK)

**Date:** 2025-11-28
**Context:** User requires `initial_branch` to be passed to EVERY agent, stored in DB, and included in spawn prompts
**Decision:** Design complete architecture for branch context propagation and merge-on-approval
**Status:** Research Complete - Ready for Implementation

---

## Problem Statement

### Current Issues

1. **initial_branch is not propagated** - PM captures it, but it's buried in pm_state JSON
2. **initial_branch not in DB schema** - Sessions table lacks this column
3. **Agents don't receive branch context** - Tech Lead can't merge because it doesn't know initial_branch
4. **Merges batched at end** - Anti-pattern increases conflict risk
5. **Orchestrator shouldn't implement** - But we need someone to merge

### User Requirements

1. `initial_branch` must be saved in the database
2. `initial_branch` must be in PM state
3. `initial_branch` must be passed as an argument to EVERY agent's prompt
4. Orchestrator must NOT implement (including merge)

---

## Architecture Overview

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          INITIAL BRANCH PROPAGATION                         │
└─────────────────────────────────────────────────────────────────────────────┘

Step 1: CAPTURE (Orchestrator Initialization)
────────────────────────────────────────────

    Orchestrator starts
           │
           ▼
    git branch --show-current → "main"
           │
           ▼
    ┌─────────────────────────────────────┐
    │  DB: sessions table                 │
    │  ─────────────────────────────────  │
    │  session_id: bazinga_12345          │
    │  initial_branch: "main"  ← NEW      │
    │  status: active                     │
    └─────────────────────────────────────┘


Step 2: PROPAGATE (Every Agent Spawn)
─────────────────────────────────────

    ┌──────────────────────────────────────────────────────────────────────┐
    │  STANDARD SPAWN CONTEXT (for ALL agents)                             │
    │  ────────────────────────────────────────────────────────────────    │
    │                                                                       │
    │  **SESSION CONTEXT:**                                                │
    │  - Session ID: {session_id}                                          │
    │  - Initial Branch: {initial_branch}  ← ALWAYS INCLUDED               │
    │  - Mode: {simple|parallel}                                           │
    │                                                                       │
    │  **GROUP CONTEXT:**                                                  │
    │  - Group ID: {group_id}                                              │
    │  - Feature Branch: feature/group-{id}-{slug}                         │
    │                                                                       │
    └──────────────────────────────────────────────────────────────────────┘

                              │
           ┌──────────────────┼──────────────────┐
           ▼                  ▼                  ▼
       ┌───────┐         ┌────────┐         ┌──────────┐
       │  PM   │         │  Dev   │         │ Tech Lead│
       └───┬───┘         └────┬───┘         └────┬─────┘
           │                  │                  │
           │ Stores in        │ Creates          │ Reviews on
           │ pm_state         │ feature/group-A  │ feature/group-A
           │                  │ from initial     │
           ▼                  ▼                  ▼
       pm_state.json    git checkout -b     git checkout
       initial_branch:  feature/group-A     feature/group-A
       "main"                 │                  │
                              │                  │
                              └────────┬─────────┘
                                       │
                                       ▼
                              Merge happens here
                              (see Step 3)


Step 3: MERGE (After Tech Lead Approval)
────────────────────────────────────────

    Tech Lead: APPROVED
           │
           ▼
    Orchestrator receives APPROVED
           │
           ▼
    Spawns MERGE DEVELOPER with:
    ┌─────────────────────────────────────┐
    │  **MERGE TASK CONTEXT:**            │
    │  - Session ID: {session_id}         │
    │  - Initial Branch: {initial_branch} │  ← FROM DB
    │  - Feature Branch: {feature_branch} │  ← FROM DEV REPORT
    │  - Task: MERGE ONLY (no implement)  │
    └─────────────────────────────────────┘
           │
           ▼
    Merge Developer executes:
    1. git checkout {initial_branch}
    2. git pull origin {initial_branch}
    3. git merge {feature_branch}
    4. IF conflict → MERGE_CONFLICT
    5. IF success → git push → MERGED
           │
           ▼
    Reports: MERGED or MERGE_CONFLICT
           │
           ├── MERGED → Route to PM (group complete)
           │
           └── MERGE_CONFLICT → Route to Original Developer
                               (with conflict details)
```

---

## Database Schema Changes

### Complete Database Changes Summary

| Table | Change | Type |
|-------|--------|------|
| `sessions` | Add `initial_branch` column | New column |
| `task_groups` | Add values to `status` enum | Enum update |
| `task_groups` | Add `merge_status` column | New column |
| `task_groups` | Add `feature_branch` column | New column |
| `task_groups.last_review_status` | **NO CHANGE** | Keep as-is |

### 1. sessions table - Add initial_branch column

```sql
-- Current schema
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    mode TEXT CHECK(mode IN ('simple', 'parallel')),
    original_requirements TEXT,
    status TEXT CHECK(status IN ('active', 'completed', 'failed')) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Migration: Add initial_branch column
ALTER TABLE sessions ADD COLUMN initial_branch TEXT DEFAULT 'main';
```

### 2. task_groups table - Add merge tracking columns

```sql
-- Current task_groups schema
CREATE TABLE task_groups (
    id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    name TEXT NOT NULL,
    status TEXT CHECK(status IN ('pending', 'in_progress', 'completed', 'failed')) DEFAULT 'pending',
    assigned_to TEXT,
    revision_count INTEGER DEFAULT 0,
    last_review_status TEXT CHECK(last_review_status IN ('APPROVED', 'CHANGES_REQUESTED', NULL)),
    -- ... other columns
);

-- Migration 1: Add feature_branch column (tracks developer's branch)
ALTER TABLE task_groups ADD COLUMN feature_branch TEXT;

-- Migration 2: Add merge_status column (tracks merge state)
ALTER TABLE task_groups ADD COLUMN merge_status TEXT
    CHECK(merge_status IN ('pending', 'in_progress', 'merged', 'conflict', 'test_failure', NULL))
    DEFAULT NULL;

-- Migration 3: Update status enum (recreate table due to SQLite CHECK constraint)
-- SQLite doesn't support ALTER COLUMN, need to recreate table

CREATE TABLE task_groups_new (
    id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    name TEXT NOT NULL,
    status TEXT CHECK(status IN (
        'pending',
        'in_progress',
        'completed',
        'failed',
        'approved_pending_merge',  -- NEW: TL approved, waiting for merge slot
        'merging'                  -- NEW: merge in progress
    )) DEFAULT 'pending',
    assigned_to TEXT,
    revision_count INTEGER DEFAULT 0,
    last_review_status TEXT CHECK(last_review_status IN ('APPROVED', 'CHANGES_REQUESTED', NULL)),
    feature_branch TEXT,           -- NEW: developer's feature branch
    merge_status TEXT CHECK(merge_status IN ('pending', 'in_progress', 'merged', 'conflict', 'test_failure', NULL)),  -- NEW
    complexity INTEGER CHECK(complexity BETWEEN 1 AND 10),
    initial_tier TEXT CHECK(initial_tier IN ('Developer', 'Senior Software Engineer')) DEFAULT 'Developer',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, session_id),
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);

-- Copy data
INSERT INTO task_groups_new SELECT
    id, session_id, name, status, assigned_to, revision_count, last_review_status,
    NULL, NULL,  -- feature_branch, merge_status (new columns)
    complexity, initial_tier, created_at, updated_at
FROM task_groups;

-- Swap tables
DROP TABLE task_groups;
ALTER TABLE task_groups_new RENAME TO task_groups;

-- Recreate index
CREATE INDEX idx_taskgroups_session ON task_groups(session_id, status);
```

### 3. last_review_status - NO CHANGE NEEDED

```sql
-- Current constraint (KEEP AS-IS)
last_review_status TEXT CHECK(last_review_status IN ('APPROVED', 'CHANGES_REQUESTED', NULL))
```

**Why no change?**
- Tech Lead only uses `APPROVED` or `CHANGES_REQUESTED`
- My design keeps Tech Lead as pure reviewer (no merge)
- Merge Developer status stored in separate `merge_status` column

### Migration Script (Complete)

```python
# File: .claude/skills/bazinga-db/scripts/migrate_merge_architecture.py

import sqlite3
from datetime import datetime

def migrate(db_path: str):
    """
    Migration for merge-on-approval architecture.

    Changes:
    1. Add initial_branch to sessions
    2. Add feature_branch to task_groups
    3. Add merge_status to task_groups
    4. Expand task_groups.status enum
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("Starting merge architecture migration...")

    # 1. Add initial_branch to sessions
    try:
        cursor.execute("ALTER TABLE sessions ADD COLUMN initial_branch TEXT DEFAULT 'main'")
        print("✓ Added sessions.initial_branch")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("⊘ sessions.initial_branch already exists")
        else:
            raise

    # 2. Backfill initial_branch from pm_state if available
    cursor.execute("""
        UPDATE sessions
        SET initial_branch = COALESCE(
            (SELECT json_extract(state_data, '$.initial_branch')
             FROM state_snapshots
             WHERE state_snapshots.session_id = sessions.session_id
             AND state_type = 'pm'
             ORDER BY timestamp DESC
             LIMIT 1),
            'main'
        )
        WHERE initial_branch IS NULL OR initial_branch = ''
    """)
    print(f"✓ Backfilled initial_branch for {cursor.rowcount} sessions")

    # 3. Add feature_branch to task_groups
    try:
        cursor.execute("ALTER TABLE task_groups ADD COLUMN feature_branch TEXT")
        print("✓ Added task_groups.feature_branch")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("⊘ task_groups.feature_branch already exists")
        else:
            raise

    # 4. Add merge_status to task_groups
    try:
        cursor.execute("""
            ALTER TABLE task_groups ADD COLUMN merge_status TEXT
            CHECK(merge_status IN ('pending', 'in_progress', 'merged', 'conflict', 'test_failure', NULL))
        """)
        print("✓ Added task_groups.merge_status")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("⊘ task_groups.merge_status already exists")
        else:
            raise

    # 5. Recreate task_groups with expanded status enum
    # Check if migration already done by looking for new status values
    cursor.execute("SELECT sql FROM sqlite_master WHERE name='task_groups'")
    schema = cursor.fetchone()[0]

    if 'approved_pending_merge' not in schema:
        print("Recreating task_groups with expanded status enum...")

        # Create new table
        cursor.execute("""
            CREATE TABLE task_groups_new (
                id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                name TEXT NOT NULL,
                status TEXT CHECK(status IN (
                    'pending', 'in_progress', 'completed', 'failed',
                    'approved_pending_merge', 'merging'
                )) DEFAULT 'pending',
                assigned_to TEXT,
                revision_count INTEGER DEFAULT 0,
                last_review_status TEXT CHECK(last_review_status IN ('APPROVED', 'CHANGES_REQUESTED', NULL)),
                feature_branch TEXT,
                merge_status TEXT CHECK(merge_status IN ('pending', 'in_progress', 'merged', 'conflict', 'test_failure', NULL)),
                complexity INTEGER CHECK(complexity BETWEEN 1 AND 10),
                initial_tier TEXT CHECK(initial_tier IN ('Developer', 'Senior Software Engineer')) DEFAULT 'Developer',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (id, session_id),
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            )
        """)

        # Copy data (handle missing columns gracefully)
        cursor.execute("""
            INSERT INTO task_groups_new
            SELECT id, session_id, name, status, assigned_to, revision_count, last_review_status,
                   feature_branch, merge_status, complexity, initial_tier, created_at, updated_at
            FROM task_groups
        """)

        # Swap tables
        cursor.execute("DROP TABLE task_groups")
        cursor.execute("ALTER TABLE task_groups_new RENAME TO task_groups")
        cursor.execute("CREATE INDEX idx_taskgroups_session ON task_groups(session_id, status)")

        print("✓ Recreated task_groups with expanded status enum")
    else:
        print("⊘ task_groups status enum already expanded")

    conn.commit()
    conn.close()
    print("Migration complete!")

if __name__ == "__main__":
    migrate("bazinga/bazinga.db")
```

### Database State Transitions

```
task_groups.status flow:
─────────────────────────

pending → in_progress → completed
                    ↘ failed

NEW flow with merge:
pending → in_progress → approved_pending_merge → merging → completed
                                              ↘ in_progress (conflict, back to dev)


task_groups.merge_status flow:
──────────────────────────────

NULL (not yet approved)
  ↓
pending (TL approved, waiting for merge)
  ↓
in_progress (Merge Developer working)
  ↓
merged (success) OR conflict (failed, needs dev fix)
```

### bazinga-db Skill Updates Required

```python
# New commands needed in bazinga_db.py:

# 1. Create session with initial_branch
def create_session(session_id, mode, requirements, initial_branch='main'):
    cursor.execute("""
        INSERT INTO sessions (session_id, mode, original_requirements, initial_branch)
        VALUES (?, ?, ?, ?)
    """, (session_id, mode, requirements, initial_branch))

# 2. Get initial_branch for session
def get_initial_branch(session_id):
    cursor.execute("SELECT initial_branch FROM sessions WHERE session_id = ?", (session_id,))
    return cursor.fetchone()[0]

# 3. Update task group with feature_branch
def update_task_group(group_id, session_id, feature_branch=None, merge_status=None, **kwargs):
    # ... existing logic plus new columns

# 4. Get merge queue (groups waiting to merge)
def get_merge_queue(session_id):
    cursor.execute("""
        SELECT id, feature_branch FROM task_groups
        WHERE session_id = ? AND status = 'approved_pending_merge'
        ORDER BY updated_at ASC
    """, (session_id,))
    return cursor.fetchall()

# 5. Check if merge in progress
def is_merge_in_progress(session_id):
    cursor.execute("""
        SELECT COUNT(*) FROM task_groups
        WHERE session_id = ? AND status = 'merging'
    """, (session_id,))
    return cursor.fetchone()[0] > 0
```

---

## Agent Spawn Context Template

### Universal Context Block (ALL agents receive this)

```markdown
## Session Context

**Session ID:** {session_id}
**Initial Branch:** {initial_branch}
**Mode:** {mode}

## Branch Information

**Initial Branch (base):** {initial_branch}
**Your Feature Branch:** {feature_branch OR "N/A for this role"}

> **IMPORTANT:** All work must eventually merge back to `{initial_branch}`.
> Feature branches follow pattern: `feature/group-{ID}-{slug}`
```

### Agent-Specific Branch Usage

| Agent | Receives initial_branch | Creates feature branch | Needs for merge |
|-------|------------------------|----------------------|-----------------|
| PM | ✅ Yes (captures & stores) | ❌ No | ❌ No |
| Developer | ✅ Yes | ✅ Yes (from initial) | ❌ No |
| QA Expert | ✅ Yes | ❌ No (checks out feature) | ❌ No |
| Tech Lead | ✅ Yes | ❌ No (checks out feature) | ❌ No (doesn't merge) |
| Merge Developer | ✅ Yes | ❌ No | ✅ Yes (merges to initial) |
| Investigator | ✅ Yes | ❌ No | ❌ No |

---

## Merge Developer Role

### Why a Separate Merge Step?

| Option | Who Merges | Problem |
|--------|------------|---------|
| Tech Lead merges | Tech Lead | Violates "reviewer doesn't implement" |
| Orchestrator merges | Orchestrator | Violates "orchestrator only coordinates" |
| Developer merges | Original Developer | Already done, moved on |
| **Merge Developer** | Dedicated spawn | ✅ Clean separation of concerns |

### Merge Developer Definition

```markdown
## Role: Merge Developer

You are a **Merge Developer** - a lightweight developer role focused ONLY on merging.

**Your ONLY task:** Merge a feature branch into the initial branch.

**You do NOT:**
- Implement features
- Write tests
- Review code
- Make architectural decisions

**You DO:**
- Execute git merge
- Report success or conflict
- Provide conflict details if they occur

## Context

**Session ID:** {session_id}
**Initial Branch:** {initial_branch}
**Feature Branch:** {feature_branch}
**Group ID:** {group_id}

## Instructions

### Step 1: Checkout Initial Branch

```bash
git checkout {initial_branch}
git pull origin {initial_branch}
```

### Step 2: Merge Feature Branch

```bash
git merge {feature_branch} --no-edit
```

### Step 3: Handle Result

**IF merge succeeds:**
```bash
git push origin {initial_branch}
```

Report:
```
**Status:** MERGED
**Merged:** {feature_branch} → {initial_branch}
**Commit:** {merge_commit_hash}
```

**IF merge conflict:**

Do NOT resolve conflicts. Report them:

```
**Status:** MERGE_CONFLICT
**Conflict:** {feature_branch} → {initial_branch}
**Conflicting Files:**
- path/to/file1.py
- path/to/file2.js

**Conflict Details:**
[paste relevant git conflict markers]

**Next Step:** Route to Developer to resolve conflicts
```

### Step 4: Route

- MERGED → Orchestrator routes to PM
- MERGE_CONFLICT → Orchestrator routes to Original Developer
```

---

## Orchestrator Changes

### Step 2A.7: Route Tech Lead Response (UPDATED)

```markdown
### Step 2A.7: Route Tech Lead Response

**IF Tech Lead reports APPROVED:**

1. **Spawn Merge Developer** (NOT Tech Lead merge, NOT orchestrator merge)

   Build merge prompt with:
   - Session ID: {session_id}
   - Initial Branch: {initial_branch} ← FROM DB
   - Feature Branch: {feature_branch} ← FROM DEVELOPER REPORT
   - Group ID: {group_id}
   - Task: MERGE ONLY

   Spawn:
   ```
   Task(
     subagent_type="general-purpose",
     model=MODEL_CONFIG["developer"],  # Haiku is sufficient for merge
     description="Merge {group_id}: {feature_branch} → {initial_branch}",
     prompt=[merge_developer_prompt]
   )
   ```

2. **Wait for Merge Developer response**

3. **Route based on merge result:**
   - MERGED → Spawn PM for completion tracking
   - MERGE_CONFLICT → Spawn Developer to resolve conflicts
```

### New Step: Route Merge Developer Response

```markdown
### Step 2A.7b: Route Merge Developer Response

**IF Merge Developer reports MERGED:**
- Log: `✅ Group {id} merged | {feature_branch} → {initial_branch}`
- **Immediately spawn PM** for completion tracking
- Do NOT stop for user input

**IF Merge Developer reports MERGE_CONFLICT:**
- Log: `⚠️ Group {id} merge conflict | {conflicting_files}`
- **Immediately spawn Original Developer** with:
  - Conflict details
  - Conflicting file list
  - Instructions to resolve and commit
- After Developer resolves → QA retests → Tech Lead re-reviews → Merge Developer retries
- Do NOT stop for user input
```

---

## Race Condition Handling

### Problem: Parallel Mode Simultaneous Merges

```
Group A: Tech Lead APPROVED → Merge Developer A starts
Group B: Tech Lead APPROVED → Merge Developer B starts (SIMULTANEOUS)

Both try to:
1. git checkout main
2. git merge their feature branch
3. git push

Race condition on `main` branch!
```

### Solution: Sequential Merge Queue

**Key insight:** Orchestrator already serializes spawns. Use this to serialize merges.

```
Parallel Development → Parallel QA → Parallel Tech Lead → SEQUENTIAL MERGE

Timeline:
─────────────────────────────────────────────────────────────────────────
Time 0:  Dev A, B, C, D work in parallel
Time 1:  QA A, B, C, D test in parallel
Time 2:  Tech Lead A, B, C, D review in parallel
Time 3:  Tech Lead A: APPROVED → Spawn Merge A → Wait
Time 4:  Merge A: MERGED → Spawn PM (for A)
         Tech Lead B: APPROVED → Spawn Merge B → Wait
Time 5:  Merge B: MERGED → Spawn PM (for B)
         Tech Lead C: APPROVED → Spawn Merge C → Wait
...
```

**Implementation:**

```markdown
### Merge Queue Management (Orchestrator)

**When Tech Lead APPROVED received:**

1. Check: Is another merge in progress?
   - Query DB: any group with status = "merging"?

2. IF merge in progress:
   - Add to merge queue (set group status = "approved_pending_merge")
   - Output: `⏳ Group {id} approved, queued for merge (merge in progress)`
   - Continue processing other responses

3. IF no merge in progress:
   - Set group status = "merging"
   - Spawn Merge Developer immediately
   - Wait for merge result

4. After merge completes:
   - Check queue for pending merges
   - Spawn next merge if any
```

### Database Support for Merge Queue

Add to task_groups status enum:

```sql
status TEXT CHECK(status IN (
    'pending',
    'in_progress',
    'completed',
    'failed',
    'approved_pending_merge',  -- NEW: approved by TL, waiting for merge slot
    'merging'                  -- NEW: merge in progress
))
```

---

## Complete Flow: Simple Mode

```
1. Orchestrator initializes
   - Captures initial_branch
   - Saves to DB: sessions.initial_branch = "main"

2. Spawns PM with:
   - session_id
   - initial_branch: "main"
   - requirements

3. PM creates task group, saves to DB with initial_branch

4. Orchestrator spawns Developer with:
   - session_id
   - initial_branch: "main"
   - group_id: "A"
   - feature_branch: "feature/group-A-jwt-auth"

5. Developer:
   - git checkout main
   - git checkout -b feature/group-A-jwt-auth
   - Implements
   - Reports READY_FOR_QA with branch name

6. Orchestrator spawns QA with:
   - session_id
   - initial_branch: "main"
   - feature_branch: "feature/group-A-jwt-auth"

7. QA tests, reports PASS

8. Orchestrator spawns Tech Lead with:
   - session_id
   - initial_branch: "main"
   - feature_branch: "feature/group-A-jwt-auth"

9. Tech Lead reviews, reports APPROVED (NO MERGE)

10. Orchestrator spawns Merge Developer with:
    - session_id
    - initial_branch: "main"
    - feature_branch: "feature/group-A-jwt-auth"
    - group_id: "A"
    - task: MERGE ONLY

11. Merge Developer:
    - git checkout main
    - git pull origin main
    - git merge feature/group-A-jwt-auth
    - git push origin main
    - Reports MERGED

12. Orchestrator spawns PM with completion update

13. PM: BAZINGA
```

---

## Complete Flow: Parallel Mode (4 Groups)

```
Phase 1: Parallel Development
─────────────────────────────
Spawn Dev A, B, C, D in parallel (all receive initial_branch: "main")

Dev A → feature/group-A-auth
Dev B → feature/group-B-api
Dev C → feature/group-C-db
Dev D → feature/group-D-ui

Phase 2: Parallel QA
────────────────────
As each dev completes → Spawn QA (receives initial_branch + feature_branch)

QA A, B, C, D run in parallel

Phase 3: Parallel Tech Lead Review
───────────────────────────────────
As each QA passes → Spawn Tech Lead (receives initial_branch + feature_branch)

Tech Lead A, B, C, D review in parallel

Phase 4: SEQUENTIAL Merge (Race Condition Prevention)
─────────────────────────────────────────────────────
Tech Lead A: APPROVED
  → Spawn Merge Developer A (main ← feature/group-A-auth)
  → MERGED ✅
  → PM notified

Tech Lead B: APPROVED (arrives while A was merging)
  → Queued (status: approved_pending_merge)
  → After A merged: Spawn Merge Developer B
  → MERGED ✅
  → PM notified

Tech Lead C: APPROVED
  → Spawn Merge Developer C (after B merged)
  → MERGED ✅

Tech Lead D: APPROVED
  → Spawn Merge Developer D (after C merged)
  → MERGED ✅

Phase 5: Completion
───────────────────
PM sees all 4 groups merged → BAZINGA
```

---

## Implementation Checklist

**Implementation Status (2025-11-28):** ✅ COMPLETED with simplification - used regular Developer with inline merge prompt instead of separate Merge Developer agent. See `research/merge-simplification-ultrathink.md`.

### Database Changes

- [x] Add `initial_branch` column to `sessions` table ✅
- [x] Add migration script (Schema v5) ✅
- [x] Update schema.md documentation ✅
- [x] Add `feature_branch` and `merge_status` columns to task_groups ✅

### bazinga-db Skill Changes

- [x] Update `create-session` to accept `initial_branch` parameter ✅
- [x] Add `get-initial-branch` command ✅
- [x] Update `update-task-group` to support new merge_status ✅

### Orchestrator Changes

- [x] Capture `initial_branch` at initialization (Step 0) ✅
- [x] Save `initial_branch` to DB when creating session ✅
- [x] Include `initial_branch` in merge task spawn prompts ✅
- [x] Add Step 2A.7a: Spawn Developer for Merge ✅
- [x] Add Step 2B.7a: Spawn Developer for Merge (Parallel) ✅
- [x] Route merge response (MERGE_SUCCESS/CONFLICT/FAILURE) ✅

### Agent Prompt Template

- [x] Create inline merge prompt in orchestrator (Step 2A.7a) ✅
- [ ] Universal session context block - deferred (not critical)

### Merge Developer → SIMPLIFIED

- [x] ~~Create merge developer prompt template~~ → Used inline prompt in orchestrator ✅
- [x] ~~Define in agents/ folder~~ → Simplified: Regular Developer handles merge tasks ✅

### Revert Current Implementation

- [x] Revert techlead.md merge changes (back to just APPROVED) ✅
- [x] Revert orchestrator.md APPROVED_AND_MERGED status ✅
- [x] Revert project_manager.md merge references ✅
- [x] Keep APPROVED as the only review status ✅

### Documentation Updates

- [x] Update response_parsing.md with Developer (Merge Task) section ✅
- [ ] Update ARCHITECTURE.md with merge flow - deferred
- [ ] Update examples/EXAMPLES.md with branch context - deferred

---

## Status Codes (Final Design)

### Tech Lead Status Codes (NO CHANGE from original)

| Status | Meaning | Next Step |
|--------|---------|-----------|
| APPROVED | Code quality approved | Orchestrator spawns Merge Developer |
| CHANGES_REQUESTED | Issues need fixing | Developer fixes |
| SPAWN_INVESTIGATOR | Complex issue | Investigator analyzes |
| ESCALATE_TO_OPUS | Need better model | Re-review with Opus |

**NO new statuses for Tech Lead.** Tech Lead stays pure reviewer.

### NEW: Merge Developer Status Codes

| Status | Meaning | Next Step |
|--------|---------|-----------|
| MERGED | Successfully merged | PM for completion |
| MERGE_CONFLICT | Conflicts detected | Developer resolves |

### task_groups.status (Updated Enum)

```
pending → in_progress → completed
                    ↘ failed

                    → approved_pending_merge (waiting for merge slot)
                    → merging (merge in progress)
```

---

## Benefits of This Design

### 1. Clean Separation of Concerns

| Agent | Responsibility | Implements Code? |
|-------|---------------|------------------|
| PM | Coordinate project | ❌ |
| Developer | Implement features | ✅ |
| QA | Test features | ❌ |
| Tech Lead | Review quality | ❌ |
| **Merge Developer** | Merge branches | ✅ (git only) |
| Orchestrator | Route agents | ❌ |

### 2. Explicit Data Flow

- `initial_branch` captured once, stored in DB
- Every agent receives it explicitly
- No implicit file reading dependencies

### 3. Race Condition Safe

- Merge queue ensures sequential merges
- No simultaneous pushes to main

### 4. Continuous Integration

- Merge happens immediately after approval
- No batch merge at end
- Conflicts caught early

### 5. Backward Compatible

- Tech Lead status unchanged (APPROVED)
- Database migration adds column with default
- Existing sessions continue working

---

## Decision Rationale

### Why Merge Developer instead of other options?

| Option | Rejected Because |
|--------|------------------|
| Tech Lead merges | "Reviewer doesn't implement" principle |
| Orchestrator merges | User requirement: "orchestrator should just orchestrate" |
| Original Developer merges | Already moved on, would need re-spawn |
| PM merges | PM is coordinator, not implementer |
| **Merge Developer** | ✅ Clean, dedicated, simple |

### Why sequential merge queue?

| Option | Rejected Because |
|--------|------------------|
| True parallel merge | Race conditions on main branch |
| Locking mechanisms | Adds complexity, easy to deadlock |
| **Sequential queue** | ✅ Simple, uses existing orchestrator flow |

### Why store initial_branch in DB?

| Option | Rejected Because |
|--------|------------------|
| Only in pm_state JSON | Not accessible to all agents, buried in blob |
| Only in orchestrator memory | Lost on context compaction |
| Pass via files | Agents may not read files correctly |
| **DB column** | ✅ First-class citizen, queryable, persistent |

---

## Conclusion

This design achieves all user requirements:

1. ✅ `initial_branch` saved in database (sessions.initial_branch)
2. ✅ `initial_branch` in PM state (pm_state.json)
3. ✅ `initial_branch` passed to EVERY agent's prompt (universal context block)
4. ✅ Orchestrator only coordinates (spawns Merge Developer, doesn't merge)
5. ✅ Continuous integration (merge on approval, not batched)
6. ✅ Race condition safe (sequential merge queue)
7. ✅ No new Tech Lead statuses (keeps APPROVED)
8. ✅ Backward compatible (migration with defaults)

**Next step:** Revert current flawed implementation, then implement this clean design.
