# Scope Validation Protocol

**Purpose:** Mandatory scope checks before any agent spawn decision
**When:** At START of every orchestrator turn

---

## Step 1: Query Current State

```
Skill(command: "bazinga-db") → get-session {session_id}
Skill(command: "bazinga-db") → get-task-groups {session_id}
```

---

## Step 2.4: Validate estimated_items is Set (MANDATORY)

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

---

## Step 2.5: Validate item_count is Set (MANDATORY)

**Before using scope comparison, verify all task groups have item_count:**

```python
for group in task_groups:
    if group.item_count is None or group.item_count == 0:
        # VALIDATION FAILED - item_count not set
        # This should not happen if PM followed template
```

**IF any group has item_count=0 or null:**
- **DO NOT** proceed with scope comparison (will be inaccurate)
- Respawn PM with: "Task group '{group_id}' missing item_count. Use update-task-group to set item_count."
- PM fixes via:
  ```
  Skill(command: "bazinga-db") → update-task-group {group_id} {session_id} --status in_progress --item_count 1
  ```
- **BLOCK** workflow until PM fixes this

**Note:** Database defaults item_count to 1 on INSERT, so this should rarely trigger. If it does, PM violated the mandatory field requirement.

---

## Step 3: Decision Logic

**Calculate progress:**
```python
original_items = session.Original_Scope.estimated_items
completed_items = sum(group.item_count for group in task_groups if group.status == "completed")
```

**IF `completed_items < original_items`:**
- Workflow is NOT complete
- MUST continue spawning agents
- CANNOT ask user for permission to continue
- CANNOT claim "done" or "complete"

**IF `completed_items >= original_items`:**
- May proceed to BAZINGA flow
- PM must still send BAZINGA
- Validator must still ACCEPT

---

## Enforcement Rules

This check prevents premature stops by ensuring:
1. Original scope is tracked throughout session
2. Progress is measured against original scope
3. Orchestrator cannot stop until scope is complete (or BAZINGA sent)

**Violation Detection:**
- If you're about to say "done" or "complete" → CHECK completed_items first
- If you're about to ask user "should I continue?" → CHECK completed_items first
- If completed_items < original_items → You MUST continue, not ask

---

## Quick Reference

| Condition | Action |
|-----------|--------|
| `estimated_items` missing | Derive from sum(item_count), save to state |
| `item_count = 0` on any group | BLOCK, respawn PM to fix |
| `completed_items < original_items` | MUST continue workflow |
| `completed_items >= original_items` | May proceed to BAZINGA |
