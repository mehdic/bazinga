# Merge Simplification: Using Regular Developer Instead of Merge Developer Agent

**Date:** 2025-11-28
**Context:** User correctly identified that creating a separate "Merge Developer" agent type was over-engineering
**Decision:** Use regular Developer agent with inline merge task instructions
**Status:** Proposed → To Be Implemented

---

## Problem Statement

The initial merge-on-approval implementation created a new agent type (`merge_developer.md`) for a task that any Developer can perform. This adds unnecessary complexity:
- New agent file to maintain
- New agent type in routing logic
- Conceptual overhead (7 agent types instead of 6)
- Duplicate patterns already handled by Developer

## Solution: Inline Merge Task for Developer

Instead of a separate agent, spawn a regular **Developer** with a merge-specific task prompt. The merge task is just a specialized development task.

### Key Insight

A "merge" is fundamentally:
1. `git checkout {initial_branch}`
2. `git pull`
3. `git merge {feature_branch}`
4. Run tests
5. Push or rollback

This is well within a Developer's capabilities. No special agent needed.

---

## Critical Analysis

### Pros ✅

1. **Simpler architecture** - 6 agent types instead of 7
2. **Reuses existing patterns** - Developer spawning is already well-documented
3. **Less code to maintain** - No separate agent file
4. **Consistent model usage** - Developer already uses Haiku
5. **Existing escalation paths** - Developer failures already route to Senior Engineer

### Cons ⚠️

1. **Inline prompt length** - Merge instructions add ~20 lines to orchestrator
2. **Semantic ambiguity** - "Developer" spawned for implementation vs merge
3. **Description clarity** - Task descriptions need to differentiate merge vs dev work

### Verdict

**Pros strongly outweigh cons.** The inline prompt length is negligible, and task descriptions (`Dev {group}: merge to {branch}` vs `Dev {group}: implement {task}`) clearly differentiate the purpose.

---

## Decision Path Analysis

### Simple Mode (Step 2A)

```
Dev implements → QA tests → TL reviews → APPROVED
                                              ↓
                          [Step 2A.7a] Spawn Developer (merge task)
                                              ↓
                          Developer merges feature → initial_branch
                                              ↓
                          MERGE_SUCCESS → Step 2A.8 (PM check)
                          MERGE_CONFLICT → Spawn Developer (fix conflicts)
                          MERGE_TEST_FAILURE → Spawn Developer (fix tests)
```

**Verification:**
- ✅ Flow is linear, no race conditions
- ✅ Developer handles both merge and conflict resolution (same agent type)
- ✅ After conflict fix: back to QA → TL → Developer(merge) loop
- ✅ PM is spawned only after MERGE_SUCCESS

### Parallel Mode (Step 2B)

```
[Phase 1] Dev A, B, C, D (parallel, max 4)
              ↓
         Each completes independently
              ↓
[Per Group] QA → TL → APPROVED → Developer(merge)
              ↓
         MERGE_SUCCESS → mark complete, check phase
              ↓
[Phase Continuation] If pending groups exist → spawn next batch
                     If all complete → Step 2B.9 (PM check)
```

**Verification:**
- ✅ Each group merges independently after TL approval
- ✅ Sequential merging per group (no parallel merges to same branch)
- ✅ Phase continuation triggers correctly after MERGE_SUCCESS
- ✅ Conflict handling spawns Developer (same as simple mode)

### Edge Cases

| Scenario | Expected Behavior | Verified? |
|----------|------------------|-----------|
| Single group, merge succeeds | Dev→QA→TL→Dev(merge)→PM→BAZINGA | ✅ |
| Single group, merge conflicts | Dev→QA→TL→Dev(merge)→Dev(fix)→QA→TL→Dev(merge)→PM | ✅ |
| Parallel groups, all succeed | Groups merge independently, PM spawned when all complete | ✅ |
| Parallel groups, one conflicts | Conflicting group loops, others continue, PM waits for all | ✅ |
| Tests fail after merge | Rollback, spawn Dev(fix), re-run through QA→TL→merge | ✅ |

---

## Implementation Details

### Changes to orchestrator.md

1. **Agent List (line ~25):** Remove "Merge Developer" entry

2. **Status Table (line ~105):** Change row from:
   ```
   | Merge Developer | MERGE_SUCCESS, MERGE_CONFLICT, MERGE_TEST_FAILURE |
   ```
   To:
   ```
   | Developer (Merge) | MERGE_SUCCESS, MERGE_CONFLICT, MERGE_TEST_FAILURE |
   ```

3. **Workflow Chain (lines ~237-239):** Update references from "Merge Developer" to "Developer (merge task)"

4. **Step 2A.7a (lines ~1693-1768):**
   - Remove "Read `agents/merge_developer.md`"
   - Include inline merge instructions in prompt
   - Description: `Dev {group_id}: merge to {initial_branch}`

5. **Step 2B.7a (lines ~2209-2233):**
   - Same changes as Step 2A.7a for parallel mode

### Inline Merge Prompt Template

```markdown
## Your Task: Merge Feature Branch

You are a Developer performing a merge task.

**Context:**
- Session ID: {session_id}
- Initial Branch: {initial_branch}
- Feature Branch: {feature_branch}
- Group ID: {group_id}

**Instructions:**
1. Checkout initial branch: `git checkout {initial_branch}`
2. Pull latest: `git pull origin {initial_branch}`
3. Merge feature branch: `git merge {feature_branch} --no-edit`
4. IF merge succeeds: Run tests, then push
5. IF merge conflicts: Abort with `git merge --abort`
6. IF tests fail: Reset with `git reset --hard HEAD~1`

**Response Format:**
Report one of:
- `MERGE_SUCCESS` - Merged and tests pass
- `MERGE_CONFLICT` - Conflicts found (list files)
- `MERGE_TEST_FAILURE` - Tests failed (list failures)
```

### Files to Delete

- `agents/merge_developer.md` - No longer needed

### Database Schema

**No changes needed** - The schema already has:
- `sessions.initial_branch`
- `task_groups.feature_branch`
- `task_groups.merge_status`

These columns work regardless of which agent performs the merge.

---

## Comparison to Alternatives

| Approach | Complexity | Maintainability | Verdict |
|----------|-----------|-----------------|---------|
| Separate Merge Developer agent | High | Harder (7 agents) | ❌ Over-engineered |
| Orchestrator does merge | Violates role | N/A | ❌ Rule violation |
| **Developer with inline task** | Low | Easy (6 agents) | ✅ Recommended |
| Tech Lead does merge | Wrong role | Confusing | ❌ Role mismatch |

---

## Decision Rationale

1. **KISS principle** - Simplest solution that works
2. **Role clarity** - Developer implements, QA tests, TL reviews, PM coordinates
3. **Existing patterns** - Developer spawning already handles complex tasks
4. **Status codes preserved** - MERGE_SUCCESS/CONFLICT/FAILURE still work with regular Developer

---

## Migration Path

1. Delete `agents/merge_developer.md`
2. Update orchestrator.md with inline merge prompt
3. Update workflow chain comments
4. No database changes needed
5. No PM/TL changes needed

---

## References

- Previous research: `research/initial-branch-propagation-and-merge-architecture.md`
- Database schema: `.claude/skills/bazinga-db/references/schema.md`
- Orchestrator agent: `agents/orchestrator.md`
