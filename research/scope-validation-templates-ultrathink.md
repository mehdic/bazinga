# Scope Validation Templates: Restoration Analysis

**Date:** 2024-12-23
**Context:** Orchestrator was compacted to fit under 25k token limit, removing detailed scope validation logic
**Decision:** How to restore this logic via external templates
**Status:** Proposed

---

## Problem Statement

When the orchestrator was compacted, important scope validation logic was removed:

1. **Step 2.4: Validate estimated_items is Set** - Mandatory check before scope comparison
2. **Step 2.5: Validate item_count is Set** - Mandatory check for all task groups
3. **Step 3: Decision Logic** - When to continue vs proceed to BAZINGA
4. **Exception: NEEDS_CLARIFICATION Pending** - Clarification state machine

Without this logic:
- Orchestrator may proceed with inaccurate scope comparisons
- Missing `item_count` or `estimated_items` causes silent failures
- Clarification hard cap not enforced
- Premature stops possible

## Solution: External Templates

### Proposed Template Structure

```
templates/orchestrator/
├── phase_simple.md          # Existing
├── phase_parallel.md        # Existing
├── scope_validation.md      # NEW - Detailed scope checks
└── clarification_flow.md    # NEW - Clarification state machine
```

### Template 1: `scope_validation.md`

**Contents:**
- Step 2.4: Validate estimated_items
- Step 2.5: Validate item_count
- Step 3: Decision Logic (completed_items < original_items)
- Enforcement rules

**When to Read:**
- At START of every orchestrator turn
- Before any agent spawn decision

### Template 2: `clarification_flow.md`

**Contents:**
- NEEDS_CLARIFICATION state machine
- clarification_used / clarification_resolved logic
- Hard cap enforcement
- Auto-fallback behavior

**When to Read:**
- When PM returns NEEDS_CLARIFICATION
- When checking if clarification is pending

## Orchestrator Integration

Add to orchestrator.md Step 2 (Scope Progress Check):

```markdown
**🔴 MANDATORY: Before proceeding, read and apply:**
Read(file_path: "bazinga/templates/orchestrator/scope_validation.md")

This template contains:
- Validation of estimated_items (Step 2.4)
- Validation of item_count (Step 2.5)
- Decision logic for continue vs BAZINGA (Step 3)
```

Add to PM Response Handling:

```markdown
**IF PM returns NEEDS_CLARIFICATION:**
Read(file_path: "bazinga/templates/orchestrator/clarification_flow.md")
```

## Trade-offs

### Pros ✅
1. Restores critical validation logic
2. Keeps orchestrator under size limit
3. Templates can be updated independently
4. Clear separation of concerns

### Cons ⚠️
1. Extra Read operations (adds latency)
2. More files to maintain
3. Logic split across files (harder to trace)

### Verdict
The pros outweigh cons. Scope validation is critical and cannot be skipped. Template approach maintains size constraints while restoring functionality.

## Implementation Plan

1. Create `templates/orchestrator/scope_validation.md` with Steps 2.4, 2.5, 3
2. Create `templates/orchestrator/clarification_flow.md` with clarification state machine
3. Update orchestrator.md Step 2 to require reading scope_validation.md
4. Update PM response handling to read clarification_flow.md when needed
5. Rebuild slash command

## Scope Validation Content (To Be Extracted)

### Step 2.4: Validate estimated_items is Set (MANDATORY)

**Before using scope comparison, verify Original_Scope has estimated_items:**

**IF `session.Original_Scope` is null OR `estimated_items` is null/0:**
- **DO NOT** proceed with scope comparison (will be inaccurate)
- **DERIVE from task groups:** `estimated_items = sum(group.item_count for group in task_groups)`
- Update session with derived value:
  ```
  Skill(command: "bazinga-db") → save-state {session_id} orchestrator {"derived_estimated_items": N, "derivation_source": "task_groups"}
  ```
- Log warning: "Original_Scope.estimated_items missing - derived from task groups"

**Note:** PM should set this during planning. If missing, deriving from task groups is the safe fallback.

### Step 2.5: Validate item_count is Set (MANDATORY)

**Before using scope comparison, verify all task groups have item_count:**

```python
for group in task_groups:
    if group.item_count is None or group.item_count == 0:
        # VALIDATION FAILED - item_count not set
```

**IF any group has item_count=0 or null:**
- **DO NOT** proceed with scope comparison (will be inaccurate)
- Respawn PM with: "Task group '{group_id}' missing item_count. Use update-task-group to set item_count."
- PM fixes via:
  ```
  Skill(command: "bazinga-db") → update-task-group {group_id} {session_id} --status in_progress --item_count 1
  ```
- **BLOCK** workflow until PM fixes this

### Step 3: Decision Logic

**IF `completed_items < original_items`:**
- Workflow is NOT complete
- MUST continue spawning agents
- CANNOT ask user for permission to continue
- CANNOT claim "done" or "complete"

**IF `completed_items >= original_items`:**
- May proceed to BAZINGA flow
- PM must still send BAZINGA
- Validator must still ACCEPT

## Clarification Flow Content (To Be Extracted)

### Exception: NEEDS_CLARIFICATION Pending

**Check orchestrator state in database:**

```
Skill(command: "bazinga-db") → get-state {session_id} orchestrator
```

**IF `clarification_used = true` AND `clarification_resolved = false`:**
- Scope check is PAUSED
- User response still needed
- Surface PM's stored question from `clarification_question` field
- Wait for response (this is the ONE allowed pause)
- After response: Update state with `clarification_resolved: true`, resume scope check

**IF `clarification_resolved = true` AND PM returns NEEDS_CLARIFICATION again:**
- **HARD CAP EXCEEDED** - PM already used their one clarification
- **AUTO-FALLBACK:** Respawn PM with fallback message

---

## Next Steps

1. Get user approval for this approach
2. Create the two template files
3. Update orchestrator.md with Read instructions
4. Rebuild slash command
5. Test with integration test
