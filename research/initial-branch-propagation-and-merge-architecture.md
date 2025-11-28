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

### sessions table - Add initial_branch column

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

-- NEW schema (add column)
ALTER TABLE sessions ADD COLUMN initial_branch TEXT DEFAULT 'main';
```

### Migration Script

```python
# File: .claude/skills/bazinga-db/scripts/migrate_initial_branch.py

def migrate():
    """Add initial_branch column to sessions table."""
    cursor.execute("""
        ALTER TABLE sessions
        ADD COLUMN initial_branch TEXT DEFAULT 'main'
    """)

    # Backfill existing sessions from pm_state if available
    cursor.execute("""
        UPDATE sessions
        SET initial_branch = (
            SELECT json_extract(state_data, '$.initial_branch')
            FROM state_snapshots
            WHERE state_snapshots.session_id = sessions.session_id
            AND state_type = 'pm'
            ORDER BY timestamp DESC
            LIMIT 1
        )
        WHERE initial_branch IS NULL
    """)
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

### Database Changes

- [ ] Add `initial_branch` column to `sessions` table
- [ ] Add migration script
- [ ] Update schema.md documentation
- [ ] Add `approved_pending_merge` and `merging` to task_groups status enum

### bazinga-db Skill Changes

- [ ] Update `create-session` to accept `initial_branch` parameter
- [ ] Add `get-initial-branch` command
- [ ] Update `update-task-group` to support new statuses

### Orchestrator Changes

- [ ] Capture `initial_branch` at initialization (Step 0)
- [ ] Save `initial_branch` to DB when creating session
- [ ] Include `initial_branch` in ALL agent spawn prompts
- [ ] Add Step 2A.7b: Route Merge Developer Response
- [ ] Implement merge queue logic for parallel mode
- [ ] Update Step 2A.7 to spawn Merge Developer instead of expecting TL merge

### Agent Prompt Template

- [ ] Create universal "Session Context" block
- [ ] Add to prompt_building.md

### Merge Developer

- [ ] Create merge developer prompt template
- [ ] Define in agents/ folder OR as inline prompt in orchestrator

### Revert Current Implementation

- [ ] Revert techlead.md merge changes (back to just APPROVED)
- [ ] Revert orchestrator.md APPROVED_AND_MERGED status
- [ ] Revert project_manager.md merge references
- [ ] Keep APPROVED as the only approval status

### Documentation Updates

- [ ] Update ARCHITECTURE.md with merge flow
- [ ] Update examples/EXAMPLES.md with branch context
- [ ] Update agents' workflow diagrams

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
