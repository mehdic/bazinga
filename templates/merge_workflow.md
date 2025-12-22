# Merge Workflow Reference

This template contains the merge task prompt and response handling for the Developer merge operation.

**Used by:** Orchestrator Steps 2A.7a and 2B.7a (Merge-on-Approval)

---

## Variable Sources

- `{session_id}` - Current session ID (from orchestrator state)
- `{initial_branch}` - From `sessions.initial_branch` in database (set at session creation, defaults to 'main')
- `{feature_branch}` - From `task_groups.feature_branch` in database (set by Developer when creating branch)
- `{group_id}` - Current group being merged (e.g., "A", "B", "main")

### Variable Hygiene

**When interpolating variables into prompts, apply these sanitization rules:**

| Variable | Max Length | Sanitization |
|----------|------------|--------------|
| `{test_failures}` | 2000 chars | Truncate with "... (truncated)" |
| `{blocker_reason}` | 500 chars | Truncate, remove control chars |
| `{conflict_files}` | 1000 chars | Truncate, one file per line |
| `{error_details}` | 1000 chars | Truncate, remove ANSI codes |

**General rules:**
- Strip leading/trailing whitespace
- Remove control characters (except newlines)
- Truncate with "... (truncated, {N} more chars)" indicator
- Never include raw stack traces > 50 lines

---

## Merge Task Prompt Template

**🔴 CRITICAL: The prompt MUST include the full Developer agent file + merge task context**

Build the Developer prompt using TWO-TURN spawn sequence:

**TURN 1: Invoke Skills**
- Invoke context-assembler (if enabled)
- Invoke specialization-loader with agent_type=developer

**TURN 2: Build Prompt & Spawn**
```
// 🔴 MANDATORY: Read the FULL Developer agent file
dev_definition = Read("agents/developer.md")  // ~1400 lines of agent instructions
IF Read fails OR dev_definition is empty:
    ⚠️ Agent file read failed | agents/developer.md | Cannot proceed - spawn aborted

// Build merge task context (this is APPENDED to the agent file, not a replacement)
task_context = """
---

## Current Task: Merge Feature Branch

**Context:**
- Session ID: {session_id}
- Initial Branch: {initial_branch}
- Feature Branch: {feature_branch}
- Group ID: {group_id}

**Instructions:**
1. Checkout initial branch: `git checkout {initial_branch}`
2. Pull latest: `git pull origin {initial_branch}`
3. Merge feature branch: `git merge {feature_branch} --no-edit`
4. IF merge conflicts: Abort with `git merge --abort` → Report MERGE_CONFLICT
5. IF merge succeeds: Run tests locally
6. IF tests pass: Push with `git push origin {initial_branch}`
7. **Monitor CI status (poll every 60 seconds, up to 5 minutes):**
   - Use `gh run list --branch {initial_branch} --limit 1` to get latest run
   - Use `gh run view <run_id>` to check status
   - Poll every 60 seconds until: completed, failed, or 5-minute timeout
8. IF CI passes (or no CI configured): Report MERGE_SUCCESS
9. IF CI fails with errors RELATED to our changes: Report MERGE_TEST_FAILURE
10. IF CI has PRE-EXISTING failures (unrelated to our changes): Report MERGE_SUCCESS with note in summary
11. IF tests fail locally (BEFORE pushing): Reset with `git reset --hard ORIG_HEAD` → Report MERGE_TEST_FAILURE

**⚠️ CRITICAL:** Never push before local tests pass. `ORIG_HEAD` undoes the merge cleanly.
**⚠️ CI POLLING:** You MUST poll CI status - do not just push and report success without checking.

**Response Format:**
Report one of:
- `MERGE_SUCCESS` - Merged and tests pass (include files changed, test summary)
- `MERGE_CONFLICT` - Conflicts found (list conflicting files)
- `MERGE_TEST_FAILURE` - Tests failed after merge (list failures)
- `MERGE_BLOCKED` - Cannot proceed (environment issue, missing deps, CI blocked)
"""

// Compose full prompt: agent file + task context
base_prompt = dev_definition + task_context
prompt = {CONTEXT_BLOCK} + {SPEC_BLOCK} + base_prompt
```

---

## Spawn Configuration

```
// Full prompt includes: CONTEXT_BLOCK + SPEC_BLOCK + dev_definition (~1400 lines) + task_context
Task(
  subagent_type: "general-purpose",
  model: MODEL_CONFIG["developer"],
  description: "Dev {group_id}: merge to {initial_branch}",
  prompt: {prompt}  // NOT a custom template - includes full agent file!
)
```

---

## Response Handling

### Status Extraction

Parse the Developer's merge response. Extract status:
- **MERGE_SUCCESS** - Branch merged, tests pass
- **MERGE_CONFLICT** - Git merge conflicts
- **MERGE_TEST_FAILURE** - Tests fail after merge
- **MERGE_BLOCKED** - Cannot proceed (environment/CI issue)

### Status Routing

**IF status = MERGE_SUCCESS:**
- Output capsule: `✅ Group {id} merged | {feature_branch} → {initial_branch} | Tests passing → PM check`
- Update task_group in database:
  - status: "completed"
  - merge_status: "merged"
- **Proceed to spawn PM for final check** (Step 2A.8 or check for next phase in parallel mode)

**IF status = MERGE_CONFLICT:**
- Output capsule: `⚠️ Group {id} merge conflict | {conflict_files} | Developer fixing → Retry merge`
- Update task_group in database:
  - status: "in_progress"
  - merge_status: "conflict"
- **🔴 Spawn Developer with Specializations (INLINE)** - conflict resolution:

  **TURN 1: Invoke Skills**
  1. Output this context block (skill reads from conversation):
     ```
     [SPEC_CTX_START group={group_id} agent=developer]
     Session ID: {session_id}
     Group ID: {group_id}
     Agent Type: developer
     Model: {model}
     Specialization Paths: {task_group.specializations as JSON array}
     [SPEC_CTX_END group={group_id}]
     ```
  2. IMMEDIATELY invoke: `Skill(command: "specialization-loader")`
  3. Extract block between `[SPECIALIZATION_BLOCK_START]` and `[SPECIALIZATION_BLOCK_END]` → {SPEC_BLOCK}

  **TURN 2: Build Prompt & Spawn**
  ```
  // 🔴 MANDATORY: Read the FULL Developer agent file
  dev_definition = Read("agents/developer.md")
  IF Read fails OR dev_definition is empty:
      ⚠️ Agent file read failed | agents/developer.md | Cannot proceed - spawn aborted

  task_context = """
  ---

  ## Current Task: Resolve Merge Conflicts

  **Context:**
  - Session ID: {session_id}
  - Feature Branch: {feature_branch}
  - Initial Branch: {initial_branch}
  - Group ID: {group_id}

  **Instructions:**
  1. Checkout feature_branch: `git checkout {feature_branch}`
  2. Fetch and merge latest initial_branch INTO feature_branch: `git fetch origin && git merge origin/{initial_branch}`
  3. Resolve all conflicts
  4. Commit the resolution: `git commit -m "Resolve merge conflicts with {initial_branch}"`
  5. Push feature_branch: `git push origin {feature_branch}`

  **⚠️ CRITICAL:** This ensures feature_branch is up-to-date with initial_branch before retry merge.

  **Response Format:**
  Report CONFLICTS_RESOLVED when done, or CONFLICTS_FAILED if unable to resolve.
  """

  base_prompt = dev_definition + task_context
  prompt = {CONTEXT_BLOCK} + {SPEC_BLOCK} + base_prompt

  Task(
    subagent_type="general-purpose",
    model=MODEL_CONFIG["developer"],
    description="Dev {group_id}: resolve conflicts",
    prompt={prompt}
  )
  ```
  * After Developer fixes: Route back through QA → Tech Lead → Developer (merge)

**IF status = MERGE_TEST_FAILURE:**
- Output capsule: `⚠️ Group {id} merge failed tests | {test_failures} | Developer fixing → Retry merge`
- Update task_group in database:
  - status: "in_progress"
  - merge_status: "test_failure"  # NOT "conflict" - these are distinct issues
- **🔴 Spawn Developer with Specializations (INLINE)** - test failure:

  **TURN 1: Invoke Skills**
  1. Output this context block (skill reads from conversation):
     ```
     [SPEC_CTX_START group={group_id} agent=developer]
     Session ID: {session_id}
     Group ID: {group_id}
     Agent Type: developer
     Model: {model}
     Specialization Paths: {task_group.specializations as JSON array}
     [SPEC_CTX_END group={group_id}]
     ```
  2. IMMEDIATELY invoke: `Skill(command: "specialization-loader")`
  3. Extract block between `[SPECIALIZATION_BLOCK_START]` and `[SPECIALIZATION_BLOCK_END]` → {SPEC_BLOCK}

  **TURN 2: Build Prompt & Spawn**
  ```
  // 🔴 MANDATORY: Read the FULL Developer agent file
  dev_definition = Read("agents/developer.md")
  IF Read fails OR dev_definition is empty:
      ⚠️ Agent file read failed | agents/developer.md | Cannot proceed - spawn aborted

  task_context = """
  ---

  ## Current Task: Fix Integration Test Failures

  **Context:**
  - Session ID: {session_id}
  - Feature Branch: {feature_branch}
  - Initial Branch: {initial_branch}
  - Group ID: {group_id}
  - Test Failures: {test_failures}

  **Instructions:**
  1. Checkout feature_branch: `git checkout {feature_branch}`
  2. Fetch and merge latest initial_branch INTO feature_branch: `git fetch origin && git merge origin/{initial_branch}`
  3. Fix the integration test failures
  4. Run tests locally to verify fixes
  5. Commit and push: `git add . && git commit -m "Fix integration test failures" && git push origin {feature_branch}`

  **⚠️ CRITICAL:** This ensures feature_branch incorporates latest initial_branch changes before retry.

  **Response Format:**
  Report TESTS_FIXED when done, or TESTS_STILL_FAILING if unable to fix.
  """

  base_prompt = dev_definition + task_context
  prompt = {CONTEXT_BLOCK} + {SPEC_BLOCK} + base_prompt

  Task(
    subagent_type="general-purpose",
    model=MODEL_CONFIG["developer"],
    description="Dev {group_id}: fix test failures",
    prompt={prompt}
  )
  ```
  * After Developer fixes: Route back through QA → Tech Lead → Developer (merge)

**IF status = MERGE_BLOCKED:**
- Output capsule: `⚠️ Group {id} merge blocked | {blocker_reason} | Tech Lead assessing`
- Update task_group in database:
  - status: "in_progress"
  - merge_status: "blocked"
- **🔴 Spawn Tech Lead with Specializations (INLINE)** - assess blockage:

  **TURN 1: Invoke Skills**
  1. Output this context block (skill reads from conversation):
     ```
     [SPEC_CTX_START group={group_id} agent=tech_lead]
     Session ID: {session_id}
     Group ID: {group_id}
     Agent Type: tech_lead
     Model: {model}
     Specialization Paths: {task_group.specializations as JSON array}
     [SPEC_CTX_END group={group_id}]
     ```
  2. IMMEDIATELY invoke: `Skill(command: "specialization-loader")`
  3. Extract block between `[SPECIALIZATION_BLOCK_START]` and `[SPECIALIZATION_BLOCK_END]` → {SPEC_BLOCK}

  **TURN 2: Build Prompt & Spawn**
  ```
  // 🔴 MANDATORY: Read the FULL Tech Lead agent file
  // NOTE: File is techlead.md (no underscore)
  tl_definition = Read("agents/techlead.md")
  IF Read fails OR tl_definition is empty:
      ⚠️ Agent file read failed | agents/techlead.md | Cannot proceed - spawn aborted

  task_context = """
  ---

  ## Current Task: Assess Merge Blockage

  **Context:**
  - Session ID: {session_id}
  - Feature Branch: {feature_branch}
  - Initial Branch: {initial_branch}
  - Group ID: {group_id}
  - Blocker Reason: {blocker_reason}

  **Instructions:**
  1. Analyze the merge blocker cause
  2. Determine if it's an environment issue, CI configuration problem, or dependency conflict
  3. Recommend resolution path:
     - If fixable: Provide specific fix steps for Developer
     - If infrastructure: Flag for manual intervention
     - If fundamental: Recommend task redesign

  **Response Format:**
  Report one of:
  - BLOCKER_RESOLVABLE - Provide fix instructions for Developer
  - BLOCKER_INFRASTRUCTURE - Requires manual ops intervention
  - BLOCKER_FUNDAMENTAL - Task needs PM reassessment
  """

  base_prompt = tl_definition + task_context
  prompt = {CONTEXT_BLOCK} + {SPEC_BLOCK} + base_prompt

  Task(
    subagent_type="general-purpose",
    model=MODEL_CONFIG["tech_lead"],
    description="TechLead {group_id}: assess blockage",
    prompt={prompt}
  )
  ```

---

## Logging

Log Developer merge interaction using §Logging Reference pattern. Agent ID: `dev_merge_group_{X}`.

---

## Escalation for Repeated Merge Failures

Track merge retry count in task_group metadata. If a group fails merge 2+ times:
- On 2nd failure: Escalate to **Senior Software Engineer** for conflict/test analysis
- On 3rd failure: Escalate to **Tech Lead** for architectural guidance
- On 4th+ failure: Escalate to **PM** to evaluate if task should be simplified or deprioritized

This prevents infinite merge retry loops and brings in higher-tier expertise when merges are persistently problematic.
