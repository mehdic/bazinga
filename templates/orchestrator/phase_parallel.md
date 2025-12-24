## Phase 2B: Parallel Mode Execution

**Before any Bash command:** See §Policy-Gate and §Bash Command Allowlist in orchestrator.md

### 🔴 FOREGROUND EXECUTION ONLY (Concurrent OK, Background NOT OK)

**All Task() calls MUST include `run_in_background: false`.** Multiple concurrent foreground spawns are fine. See orchestrator.md §FOREGROUND EXECUTION ONLY and §PRE-TASK VALIDATION.

### 🔴 POST-SPAWN TOKEN TRACKING (MANDATORY)

**After EVERY Task() call, you MUST:**

1. **Increment spawn counter:**
   ```
   bazinga-db, please update orchestrator state:

   Session ID: {session_id}
   State Type: orchestrator
   State Data: {"total_spawns": {current_total_spawns + 1}}
   ```
   Then invoke: `Skill(command: "bazinga-db")`

2. **Compute token estimate:** `estimated_token_usage = total_spawns * 15000`

**Note:** The prompt-builder script applies token budgets automatically based on model tier (haiku=900, sonnet=1800, opus=2400). The spawn counter is tracked for metrics and debugging purposes.

---

**🚨 ENFORCE MAX 4 PARALLEL AGENTS** (see §HARD LIMIT in Overview)

**Note:** Phase 2B is already announced in Step 1.5 mode routing. No additional message needed here.

**🔴 CRITICAL WORKFLOW RULE - NEVER STOP BETWEEN PHASES:**

**Multi-phase execution is common in parallel mode:**
- PM may create Phase 1 (setup groups A, B, C) and Phase 2 (feature groups D, E, F)
- When Phase 1 completes, orchestrator MUST automatically start Phase 2
- **NEVER STOP TO WAIT FOR USER INPUT between phases**
- Only stop when PM sends BAZINGA or NEEDS_CLARIFICATION

**How to detect and continue to next phase:**
- After EACH group's Tech Lead approval: Spawn Developer (merge), then check if pending groups exist (Step 2B.7b)
- IF pending groups found: Immediately spawn developers for next phase
- IF no pending groups: Then spawn PM for final assessment
- Process continuously until all phases complete

**Without this rule:** Orchestrator hangs after Phase 1, waiting indefinitely for user to say "continue"

**🔴 PHASE BOUNDARY AUTO-CONTINUATION:**

If PM asks "Would you like me to continue with Phase N?" → Auto-select CONTINUE if pending work exists.
Output: `🔄 Auto-continuing | Phase {N} complete | Starting Phase {N+1}`

**REAL-WORLD BUG EXAMPLE (THE BUG WE'RE FIXING):**

❌ **FORBIDDEN - What caused the bug:**
```
Received responses:
- Developer B: PARTIAL (69 test failures remain)
- Tech Lead C: APPROVED

Orchestrator output:
"Group C is approved. Group B still has failures. Let me route C first, then respawn B."

[Spawns Tech Lead C only]
[STOPS - Never spawns Developer B]
```
→ WRONG: Serialization ("first... then..."), partial spawning, premature stop

✅ **REQUIRED - Correct handling with three-layer enforcement:**
```
Received responses:
- Developer B: PARTIAL (69 test failures remain)
- Tech Lead C: APPROVED

LAYER 1 (Batch Processing):
Parse all: B=PARTIAL, C=APPROVED
Build queue: Developer B continuation + Phase check for C
Spawn all in ONE message

LAYER 2 (Step-Level Check):
Group B PARTIAL → Verify Developer B Task spawned ✓
Group C APPROVED → Run Phase Continuation Check ✓

LAYER 3 (Pre-Stop Verification):
Q1: All responses processed? B ✓, C ✓ = YES
Q2: Any INCOMPLETE groups? B needs continuation = YES → Developer B spawned ✓
Q3: All Tasks spawned? Developer B ✓ = YES
PASS - Safe to end message

Orchestrator output:
"Groups B (PARTIAL) and C (APPROVED) received. Spawning Developer B continuation + running phase check:"

[Task: Developer B continuation with test failure context]
[Executes: Phase Continuation Check for Group C]
```
→ CORRECT: All groups handled, no serialization, verified complete

**FAILED FLOW - How Defense-in-Depth Works:**

❌ **Violation:** Orchestrator bypasses Layer 1, spawns only Tech Lead C, forgets Developer B (PARTIAL)

🔴 **Layer 2 catch:** Self-check at Group B: "Did I spawn Task? NO" → Force spawn Developer B
🔴 **Layer 3 catch:** Pre-stop verification: "Q2: PARTIAL groups? YES (B)" + "Q3: Spawned for B? YES (Layer 2 fixed)" = PASS

**Result:** Layers 2+3 auto-fixed Layer 1 bypass. All groups handled, no stop.

**This three-layer approach prevents the bug at multiple levels.**

### Step 2B.0: Context Optimization Checkpoint (≥3 Developers)

**Trigger:** Execute this step ONLY when `parallel_count >= 3`

**Purpose:** Large parallel spawns consume significant context. This checkpoint gives users the option to compact first.

**🔴 GUARD:** Only emit this multi-line summary when `parallel_count >= 3`. For 1-2 developers, use a single capsule and continue.

**Output to user (when parallel_count >= 3):**
```
🔨 **Phase {N} starting** | Spawning {parallel_count} developers in parallel

📋 **Developer Assignments:**
• {group_id}: {tier_name} ({model}) [C:{complexity}] - {task[:90]}
[repeat for each group]

💡 For ≥3 developers, consider `/compact` first.
⏳ Continuing immediately... (Ctrl+C to pause. Resume via `/bazinga.orchestrate` after `/compact`)
```

**Complexity notation:** `[C:N]` where N is 1-10. Levels: 1-3=Low (Dev), 4-6=Medium (SSE), 7-10=High (SSE)

**Model source:** Read from `MODEL_CONFIG[agent_type]` (loaded from `bazinga/model_selection.json`)

**Example output (4 developers):**
```
🔨 **Phase 1 starting** | Spawning 4 developers in parallel

📋 **Developer Assignments:**
• P0-NURSE-FE: Senior Software Engineer ({MODEL_CONFIG["senior_software_engineer"]}) [C:7] - Nurse App Frontend with auth integration
• P0-NURSE-BE: Senior Software Engineer ({MODEL_CONFIG["senior_software_engineer"]}) [C:6] - Nurse Backend Services with API endpoints
• P0-MSG-BE: Senior Software Engineer ({MODEL_CONFIG["senior_software_engineer"]}) [C:8] - Messaging Backend with WhatsApp channel
• P1-DOCTOR-FE: Developer ({MODEL_CONFIG["developer"]}) [C:3] - Doctor Frontend basic components

💡 For ≥3 developers, consider `/compact` first.
⏳ Continuing immediately... (Ctrl+C to pause. Resume via `/bazinga.orchestrate` after `/compact`)
```

**Then IMMEDIATELY continue to Step 2B.1** - do NOT wait for user input.

**State Persistence:** PM's plan and task groups are already saved to database (Step 1.3). If user interrupts:
1. Press Ctrl+C
2. Run `/compact`
3. Run `/bazinga.orchestrate` - orchestrator auto-detects existing session and resumes

**Rationale:** User can:
- Let it proceed (context is fine)
- Press Ctrl+C, compact, and resume (state is preserved in database)

### Step 2B.1: Spawn Multiple Developers in Parallel

**🔴 CRITICAL:** Spawn ALL developers in ONE message (parallel). **ENFORCE MAX 4** (see §HARD LIMIT) — if >4 groups, use first 4, defer rest.

**Per-group tier selection (from PM's Initial Tier per group):**
| PM Tier Decision | Agent File | Model | Description |
|------------------|------------|-------|-------------|
| Developer (default) | `agents/developer.md` | `MODEL_CONFIG["developer"]` | `Dev {group}: {task[:90]}` |
| Senior Software Engineer | `agents/senior_software_engineer.md` | `MODEL_CONFIG["senior_software_engineer"]` | `SSE {group}: {task[:90]}` |
| Requirements Engineer | `agents/requirements_engineer.md` | `MODEL_CONFIG["requirements_engineer"]` | `Research {group}: {task[:90]}` |

**🔴 Research Task Override:** If PM sets `type: research`, spawn Requirements Engineer. Research groups run in Phase 1 (MAX 2 parallel), implementation groups in Phase 2+ (MAX 4 parallel).

**Parallelism Enforcement:** PM enforces MAX 2 research groups during planning. Orchestrator enforces MAX 4 implementation groups. Do NOT schedule >2 research groups concurrently.

**🔴 Enforcement Rule (before spawning):**
```
# Parse type from PM's markdown description (e.g., "**Type:** research")
# NOT from database column (DB only stores initial_tier: developer/senior_software_engineer)
def get_task_type(pm_markdown):
    # Look for "**Type:** X" pattern in PM's description (case-insensitive)
    # Note: search string MUST be lowercase since we call .lower() on input
    if "**type:** research" in pm_markdown.lower():
        return "research"
    return "implementation"  # default

research_groups = [g for g in groups if get_task_type(g.pm_markdown) == "research"]
impl_groups = [g for g in groups if get_task_type(g.pm_markdown) != "research"]
IF len(research_groups) > 2: defer_excess_research()  # graceful deferral, not error
IF len(impl_groups) > 4: defer_excess_impl()  # spawn in batches
```

### SPAWN IMPLEMENTATION AGENTS - PARALLEL (SKILL-BASED PROMPT)

**🔴 SINGLE-STEP PROMPT BUILDING (PER GROUP)**

This section handles spawning Developer, SSE, or RE for each group based on PM's `initial_tier` decision.

**🔴🔴🔴 MANDATORY Step 0: Query Task Groups and Map Tiers to Agent Types 🔴🔴🔴**

**BEFORE creating ANY params files, you MUST:**

1. **Query task groups from database:**
   ```bash
   python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet get-task-groups "{session_id}"
   ```

   **Response format:** JSON array of task groups, each with `id`, `name`, `initial_tier`, `complexity`, etc.

   **If query fails:** Output `❌ Failed to query task groups | {error}` → STOP

2. **For EACH group, extract and map initial_tier to agent_type:**

   | DB `initial_tier` Value | Maps To `agent_type` | Model Key |
   |-------------------------|---------------------|-----------|
   | `"Developer"` | `"developer"` | `MODEL_CONFIG["developer"]` |
   | `"Senior Software Engineer"` | `"senior_software_engineer"` | `MODEL_CONFIG["senior_software_engineer"]` |
   | `"Requirements Engineer"` | `"requirements_engineer"` | `MODEL_CONFIG["requirements_engineer"]` |
   | `null` or missing | `"developer"` (default) | `MODEL_CONFIG["developer"]` |

   **Also check task type:** If PM's description contains `**Type:** research`, use `requirements_engineer` regardless of initial_tier.

3. **Build agent_type map keyed by group_id:**
   ```python
   # Pseudocode - build explicit map for Step 1
   TIER_TO_AGENT = {
       "Developer": "developer",
       "Senior Software Engineer": "senior_software_engineer",
       "Requirements Engineer": "requirements_engineer"
   }

   agent_type_map = {}  # group_id → agent_type
   for group in task_groups:
       # Normalize: strip whitespace, handle case variations
       tier = (group.get("initial_tier") or "").strip()

       # Research type override
       if "**type:** research" in group.get("description", "").lower():
           agent_type_map[group["id"]] = "requirements_engineer"
       elif tier in TIER_TO_AGENT:
           agent_type_map[group["id"]] = TIER_TO_AGENT[tier]
       else:
           # Unknown tier - warn and default
           print(f"⚠️ Unknown tier '{tier}' for {group['id']}, defaulting to developer")
           agent_type_map[group["id"]] = "developer"
   ```

**🔴 CRITICAL: If you skip this step, ALL groups will spawn as Developer regardless of PM's tier decision!**

**🔴 SELF-CHECK before proceeding:**
- ✅ Did I query task_groups from database successfully?
- ✅ Did I read initial_tier for EACH group?
- ✅ Did I check for research type override?
- ✅ Did I build agent_type_map with correct mappings?
- ✅ For security tasks, is agent_type = "senior_software_engineer"?
- ✅ For research tasks, is agent_type = "requirements_engineer"?

**Step 1: Write params files for EACH group**

For EACH group, write a params JSON file using `agent_type_map[group_id]` from Step 0:

Write to `bazinga/prompts/{session_id}/params_{agent_type}_{group_id}.json`:

**⚠️ Path safety:** Ensure session_id and group_id contain only alphanumeric chars and underscores. Reject if they contain `../` or special characters.

```json
{
  "agent_type": "{agent_type_map[group_id]}",
  "session_id": "{session_id}",
  "group_id": "{group_id}",
  "task_title": "{task_groups[group_id][\"title\"]}",
  "task_requirements": "{task_groups[group_id][\"requirements\"]}",
  "branch": "{task_groups[group_id][\"branch\"] or session_branch}",
  "mode": "parallel",
  "testing_mode": "{testing_mode}",
  "model": "{MODEL_CONFIG[agent_type]}",
  "output_file": "bazinga/prompts/{session_id}/{agent_type}_{group_id}.md"
}
```

**Step 2: Invoke prompt-builder skill for EACH group**

→ `Skill(command: "prompt-builder")`

**Step 3: Verify JSON results**

For EACH group, check skill response:
- `success` is `true`
- `prompt_file` is non-empty
- `markers_ok` is `true`

**IF any check fails for a group:**
→ Output: `❌ Prompt build failed for {group_id} | {error}` → Skip that group, continue with others

**Step 2: Spawn ALL agents in ONE message with file-based instructions**

```
📝 Spawning {count} agents in parallel:
• Group A: {agent_type} | {task_title} | Prompt: bazinga/prompts/{session_id}/{agent_type}_A.md
• Group B: {agent_type} | {task_title} | Prompt: bazinga/prompts/{session_id}/{agent_type}_B.md
...

Task(subagent_type="general-purpose", model=MODEL_CONFIG[agent_type_A], description="{agent_type}: {task_A[:90]}", prompt="FIRST: Read bazinga/prompts/{session_id}/{agent_type}_A.md which contains your complete instructions.\nTHEN: Execute ALL instructions in that file.\n\nDo NOT proceed without reading the file first.", run_in_background: false)

Task(subagent_type="general-purpose", model=MODEL_CONFIG[agent_type_B], description="{agent_type}: {task_B[:90]}", prompt="FIRST: Read bazinga/prompts/{session_id}/{agent_type}_B.md which contains your complete instructions.\nTHEN: Execute ALL instructions in that file.\n\nDo NOT proceed without reading the file first.", run_in_background: false)
...
```

**🔴 SELF-CHECK:**
- ✅ Did prompt-builder create files for each group?
- ✅ Did I call Task() for EACH group with file-based instructions?

**🔴 MAX 4 groups.** If >4, spawn first 4, defer rest.

---

### Specialization Derivation (Fallback)

If `specializations` not in task_group, derive from `project_context.json`:
```
IF project_context.components with suggested_specializations:
    specializations = merge all component.suggested_specializations
ELSE IF project_context.suggested_specializations:
    specializations = suggested_specializations
ELSE IF primary_language or framework:
    specializations = map_to_template_paths(primary_language, framework)
```

### Example: FULL_PROMPT composition

The prompt-builder combines internally:
```
FULL_PROMPT[group_id] =
  CONTEXT_BLOCK     // From DB: context_packages, prior reasoning, error patterns
  +
  SPEC_BLOCK        // From DB: task_groups.specializations → template files
  +
  base_prompt       // Task details (session, group, requirements)
```

**Count your Task() calls:** Should match number of groups (max 4).

---

**AFTER receiving ALL developer responses:**

### Step 2B.2: Receive All Developer Responses

**For EACH developer response:**

**Step 1: Parse response and output capsule to user**

Use the Developer Response Parsing section from `bazinga/templates/response_parsing.md` (loaded at initialization) to extract status, files, tests, coverage, summary.

**Step 2: Construct and output capsule** (same templates as Step 2A.2):
- READY_FOR_QA/REVIEW: `🔨 Group {id} [{tier}/{model}] [C:{complexity}] complete | {summary}, {files}, {tests}, {coverage} | {status} → {next}`
- PARTIAL: `🔨 Group {id} [{tier}/{model}] [C:{complexity}] implementing | {what's done} | {current_status}`
- BLOCKED: `⚠️ Group {id} [{tier}/{model}] [C:{complexity}] blocked | {blocker} | Investigating`

**Step 3: Output capsule to user**

**Step 4: Log to database** — Use §Logging Reference pattern. Agent ID: `dev_group_{X}`.

### Step 2B.2a: Mandatory Batch Processing (LAYER 1 - ROOT CAUSE FIX)

**🔴 CRITICAL: YOU MUST READ AND FOLLOW the batch processing template. This is NOT optional.**

```
Read(file_path: "bazinga/templates/batch_processing.md")
```

**If Read fails:** Output `❌ Template load failed | batch_processing.md` and STOP.

**After reading the template, you MUST:**
1. Parse ALL responses FIRST (no spawning yet)
2. Build spawn queue for ALL groups
3. Spawn ALL Tasks in ONE message block
4. Verify enforcement checklist

**This prevents the orchestrator stopping bug. DO NOT proceed without reading and applying `bazinga/templates/batch_processing.md`.**

**Quick Reference (full rules in template):**
- ✅ Parse all → Build queue → Spawn all in ONE message
- ❌ NEVER serialize: "first A, then B"
- ❌ NEVER partial spawn: handle ALL groups NOW

### Step 2B.2b: Developer/SSE Spawn on Failure or Escalation (Per Group)

**When a Developer reports PARTIAL, INCOMPLETE, or ESCALATE_SENIOR, use this section.**

**Escalation Rules:**
- 1st failure → Re-spawn Developer
- 2nd failure → Escalate to SSE
- 3rd+ failure → Route to Tech Lead

**Determine agent_type based on revision_count:**
- revision_count < 2 → developer
- revision_count >= 2 AND < 3 → senior_software_engineer
- revision_count >= 3 → tech_lead (for architectural guidance)

**Step 1: Write params file**

Write to `bazinga/prompts/{session_id}/params_{agent_type}_{group_id}_retry.json`:
```json
{
  "agent_type": "{determined based on revision_count above}",
  "session_id": "{session_id}",
  "group_id": "{group_id}",
  "task_title": "Continuation: {original_task[:60]}",
  "task_requirements": "PREVIOUS ATTEMPT: {previous_attempt_summary}\nREMAINING ISSUES: {remaining_issues}",
  "branch": "{branch}",
  "mode": "parallel",
  "testing_mode": "{testing_mode}",
  "model": "{MODEL_CONFIG[agent_type]}",
  "output_file": "bazinga/prompts/{session_id}/{agent_type}_{group_id}_retry.md"
}
```

**Step 2: Invoke prompt-builder skill**

→ `Skill(command: "prompt-builder")`

**Step 3: Verify JSON result** - Check `success`, `prompt_file`, `markers_ok`

**IF any check fails:** Output `❌ Prompt build failed | {error}` → STOP

**Step 4: Spawn Agent with file-based instructions**

→ `Task(subagent_type="general-purpose", model=MODEL_CONFIG[agent_type], description="{agent_type} {group_id}: continuation", prompt="FIRST: Read bazinga/prompts/{session_id}/{agent_type}_{group_id}_retry.md which contains your complete instructions.\nTHEN: Execute ALL instructions in that file.\n\nDo NOT proceed without reading the file first.", run_in_background: false)`

**🔴 SELF-CHECK:**
- ✅ Did prompt-builder create the file successfully?
- ✅ Did I call Task() with file-based instructions?

---

### Step 2B.3-2B.7: Route Each Group Independently

**Critical difference from Simple Mode:** Each group flows through the workflow INDEPENDENTLY and CONCURRENTLY.

**For EACH group, execute the SAME workflow as Phase 2A (Steps 2A.3 through 2A.7):**

| Phase 2A Step | Phase 2B Equivalent | Notes |
|---------------|---------------------|-------|
| 2A.3: Route Developer Response | 2B.3 | Check this group's developer status |
| 2A.4: Spawn QA Expert | 2B.4 | Use this group's files only |
| 2A.5: Route QA Response | 2B.5 | Check this group's QA status |
| 2A.6: Spawn Tech Lead | 2B.6 | Use this group's context only |
| 2A.6b: Investigation Loop | 2B.6b | Same investigation process |
| 2A.6c: Tech Lead Validation | 2B.6c | Validate this group's investigation |
| 2A.7: Route Tech Lead Response | 2B.7 | Check this group's approval |

**Group-specific adaptations:**
- Replace "main" with group ID (A, B, C, D)
- Use group-specific branch name
- Use group-specific files list
- Track group status independently in database
- Log with agent_id: `{role}_group_{X}`

**Workflow execution:** Process groups concurrently but track each independently.

**Prompt building:** Use the same process as Step 2A.4 (QA), 2A.6 (Tech Lead), but substitute group-specific files and context.

**🔴 PRE-SPAWN CHECKLIST (QA/TL Per Group) - SKILL-BASED PROMPT**

When spawning QA or Tech Lead for a group:

**Step 1: Write params file**

Write to `bazinga/prompts/{session_id}/params_{agent_type}_{group_id}.json`:
```json
{
  "agent_type": "{qa_expert|tech_lead}",
  "session_id": "{session_id}",
  "group_id": "{group_id}",
  "task_title": "{task_description}",
  "task_requirements": "FILES: {files_changed}",
  "branch": "{branch}",
  "mode": "parallel",
  "testing_mode": "{testing_mode}",
  "model": "{MODEL_CONFIG[agent_type]}",
  "output_file": "bazinga/prompts/{session_id}/{agent_type}_{group_id}.md",
  "prior_handoff_file": "bazinga/artifacts/{session_id}/{group_id}/handoff_{prior_agent}.json"
}
```
**CRP:** `prior_handoff_file` - For QA: `handoff_implementation.json` (alias written by Developer OR SSE), For TL: `handoff_qa_expert.json`

**Step 2: Invoke prompt-builder skill**

→ `Skill(command: "prompt-builder")`

**Step 3: Verify JSON result** - Check `success`, `prompt_file`, `markers_ok`

**IF any check fails:** Output `❌ Prompt build failed | {error}` → STOP

**Step 4: Spawn Agent with file-based instructions**

```
Task(subagent_type="general-purpose", model={model}, description="{agent_type} {group_id}", prompt="FIRST: Read bazinga/prompts/{session_id}/{agent_type}_{group_id}.md which contains your complete instructions.\nTHEN: Execute ALL instructions in that file.\n\nDo NOT proceed without reading the file first.", run_in_background: false)
```

**🔴 SELF-CHECK:**
- ✅ Did prompt-builder skill return success?
- ✅ Did I call Task() with file-based instructions?

### Step 2B.7: Route Tech Lead Response (Per Group)

**IF Tech Lead approves this group:**
- **Trigger strategy extraction** (capture successful patterns for future context):
  ```
  bazinga-db, please extract strategies:

  Session ID: {session_id}
  Group ID: {group_id}
  Project ID: {project_id}
  Lang: {detected_lang}
  Framework: {detected_framework}
  ```
  Then invoke: `Skill(command: "bazinga-db")`
  *Note: This is non-blocking - proceed even if extraction fails*
- **Immediately proceed to Step 2B.7a** (Spawn Developer for merge)

**IF Tech Lead requests changes:** Route back to Developer/SSE for this group using Step 2B.2b (Developer/SSE Spawn on Failure or Escalation).

### Step 2B.7a: Spawn Developer for Merge (Parallel Mode - Per Group)

**🔴 CRITICAL: In Parallel Mode, after Tech Lead approval, spawn Developer (merge) BEFORE phase continuation check**

**User output (capsule format):**
```
🔀 Merging | Group {id} approved → Merging {feature_branch} to {initial_branch}
```

**🔴 MANDATORY: Load and use merge workflow template:**

```
Read(file_path: "bazinga/templates/merge_workflow.md")
```

**If Read fails:** Output `❌ Template load failed | merge_workflow.md` and STOP.

Use the template for merge prompt and response handling. Apply to this group's context.

**Route Developer merge response:** (Same status handling as Step 2A.7a)

| Status | Action |
|--------|--------|
| `MERGE_SUCCESS` | Update group + progress (see below) → Step 2B.7b |
| `MERGE_CONFLICT` | Spawn Developer with conflict context → Retry: Dev→QA→TL→Dev(merge) |
| `MERGE_TEST_FAILURE` | Spawn Developer with test failures → Retry: Dev→QA→TL→Dev(merge) |
| `MERGE_BLOCKED` | Spawn Tech Lead to assess blockage |
| *(Unknown status)* | Route to Tech Lead with "UNKNOWN_STATUS" reason |

**MERGE_SUCCESS Progress Tracking:**
1. Update task_group: status="completed", merge_status="merged"
2. Query completed progress from task_groups using bazinga-db skill:
   ```
   bazinga-db, please get task groups:

   Session ID: [session_id]
   Status: completed
   ```
   Then invoke: `Skill(command: "bazinga-db")`
   Sum item_count from the returned JSON to get completed items.
3. Output capsule with progress: `✅ Group {id} merged | Progress: {completed_sum}/{total_sum}`

**Escalation:** 2nd fail → SSE, 3rd fail → TL, 4th+ → PM

### Step 2B.7b: Phase Continuation Check (CRITICAL - PREVENTS HANG)

**🔴 MANDATORY: After MERGE_SUCCESS, check for next phase BEFORE spawning PM**

**Actions:** 1) Update group status=completed, merge_status=merged (bazinga-db update task group), 2) Query ALL groups (bazinga-db get all task groups), 3) Load PM state for execution_phases (bazinga-db get PM state), 4) Count: completed_count, in_progress_count, pending_count (include "deferred" status as pending), total_count.

**Decision Logic (Phase-Aware):** IF execution_phases null/empty → simple: pending_count>0 → output `✅ Group {id} merged | {done}/{total} groups | Starting {pending_ids}` → jump Step 2B.1, ELSE → proceed Step 2B.8. IF execution_phases exists → find current_phase (lowest incomplete) → IF current_phase complete AND next_phase exists → output `✅ Phase {N} complete | Starting Phase {N+1}` → jump Step 2B.1, ELSE IF current_phase complete AND no next_phase → proceed Step 2B.8, ELSE IF current_phase in_progress → output `✅ Group {id} merged | Phase {N}: {done}/{total} | Waiting {in_progress}` → exit (re-run on next completion). **All complete → Step 2B.8**

### Step 2B.7c: Pre-Stop Verification Gate (LAYER 3 - FINAL SAFETY NET)

**🔴 CRITICAL: RUN THIS CHECK BEFORE ENDING ANY ORCHESTRATOR MESSAGE IN STEP 2B**

**MANDATORY THREE-QUESTION CHECKLIST:**

| # | Question | Check | FAIL Action |
|---|----------|-------|-------------|
| 1 | Did I process ALL responses received? | Count responses, verify each routed | Auto-fix below |
| 2 | Any INCOMPLETE/PARTIAL/FAILED groups? | Query: `bazinga-db get all task groups` | Auto-fix below |
| 3 | Did I spawn Tasks for ALL incomplete groups? | Verify Task spawn per incomplete group | Auto-fix below |

**AUTO-FIX (IF ANY question fails):**
1. DO NOT end message without spawning
2. Build spawn queue using Step 2B.2b for agent selection:
   - INCOMPLETE/PARTIAL: Developer (1st fail) OR SSE (2nd+ fail) - check revision_count
   - FAILED → Investigator
   - READY_FOR_QA → QA
   - READY_FOR_REVIEW → Tech Lead
3. For Developer/SSE spawns, use Step 2B.2b (full agent file + CONTEXT_BLOCK + SPEC_BLOCK)
4. Spawn ALL missing Tasks in ONE message
5. Output: `🔄 Auto-fix: Found {N} incomplete → Spawning {agents} in parallel`
6. Re-run checklist

**PASS CRITERIA (ALL THREE must pass):** ✅ All responses processed ✅ No incomplete groups unhandled ✅ All required Tasks spawned

**FORBIDDEN:** ❌ Serialization ("first... then...") ❌ Partial spawning ❌ Ending with INCOMPLETE groups

**This verification gate is your final responsibility check. DO NOT bypass it.**

### Step 2B.8: Spawn PM When All Groups Complete



**User output (capsule format):**
```
✅ All groups complete | {N}/{N} groups approved, all quality gates passed | Final PM check → BAZINGA
```

**Build PM prompt using prompt-builder skill:**

**Step 1: Write params file**

Write to `bazinga/prompts/{session_id}/params_project_manager_parallel_final.json`:
```json
{
  "agent_type": "project_manager",
  "session_id": "{session_id}",
  "group_id": "global",
  "task_title": "Final Assessment (Parallel Mode)",
  "task_requirements": "GROUPS: {N} groups completed\n\nGroup Results:\n{all_group_results_and_commit_summaries}\n\nAssess if all success criteria are met across ALL groups and decide: BAZINGA or CONTINUE",
  "branch": "{branch}",
  "mode": "parallel",
  "testing_mode": "{testing_mode}",
  "model": "{MODEL_CONFIG[\"project_manager\"]}",
  "output_file": "bazinga/prompts/{session_id}/project_manager_parallel_final.md"
}
```

**Step 2: Invoke prompt-builder skill**

→ `Skill(command: "prompt-builder")`

**Step 3: Verify JSON result** - Check `success`, `prompt_file`, `markers_ok`

**IF any check fails:** Output `❌ Prompt build failed | {error}` → STOP

**Step 4: Spawn PM with file-based instructions**

→ `Task(subagent_type="general-purpose", model=MODEL_CONFIG["project_manager"], description="PM overall assessment", prompt="FIRST: Read bazinga/prompts/{session_id}/project_manager_parallel_final.md which contains your complete instructions.\nTHEN: Execute ALL instructions in that file.\n\nDo NOT proceed without reading the file first.", run_in_background: false)`


**AFTER PM response:** Follow §Step 2A.8 process (parse, construct capsule, apply auto-route rules).
**Log:** §Logging Reference with ID: `pm_parallel_final`
**Track:** Invoke `Skill(command: "velocity-tracker")` with session + groups + duration

### Step 2B.9: Route PM Response

Follow §Step 2A.9 routing rules with parallel-mode adaptations:
- **CONTINUE:** Spawn ALL groups in ONE message (not sequential)
- **INVESTIGATION_NEEDED:** Include all affected group IDs and branches; Investigator→TL→Dev(s)→QA→TL→PM
- **NEEDS_CLARIFICATION:** §Step 1.3a (only stop point)

---

## 🔴 PHASE COMPLETION - MANDATORY PM RE-SPAWN (Parallel Mode)

**When ALL groups in the CURRENT PHASE are APPROVED and MERGED:**

### What You MUST Do:

1. **DO NOT** summarize to user and stop
2. **DO NOT** ask user what to do next
3. **DO NOT** ask "Would you like me to continue?"
4. **MUST** spawn PM immediately (after phase continuation check in Step 2B.7b finds no more phases)

### Mandatory PM Spawn (SKILL-BASED PROMPT):

**Step 1: Write params file**

Write to `bazinga/prompts/{session_id}/params_project_manager_all_phases.json`:
```json
{
  "agent_type": "project_manager",
  "session_id": "{session_id}",
  "group_id": "global",
  "task_title": "All Phases Assessment",
  "task_requirements": "All phases complete. All groups approved and merged: {group_list}.\n\nQuery database for Original_Scope and compare to completed work:\n- Original estimated items: {Original_Scope.estimated_items}\n- Completed items: {sum of completed group item_counts}\n\nBased on this comparison, you MUST either:\n- Identify additional work items missed (if any remain from Original_Scope), OR\n- Send BAZINGA (if ALL original tasks from scope are complete)\n\nDO NOT ask for permission. Make the decision based on scope comparison.",
  "branch": "{branch}",
  "mode": "parallel",
  "testing_mode": "{testing_mode}",
  "model": "{MODEL_CONFIG[\"project_manager\"]}",
  "output_file": "bazinga/prompts/{session_id}/project_manager_all_phases.md"
}
```

**Step 2: Invoke prompt-builder skill**

→ `Skill(command: "prompt-builder")`

**Step 3: Verify JSON result** - Check `success`, `prompt_file`, `markers_ok`

**IF any check fails:** Output `❌ Prompt build failed | {error}` → STOP

### Integration with Step 2B.7b:

The Phase Continuation Check (Step 2B.7b) handles phase-to-phase transitions automatically.
This rule applies when:
- Step 2B.7b finds NO more pending phases
- All execution_phases are complete
- PM needs to assess final completion

**Step 2: Spawn PM with file-based instructions**

```
Task(
  subagent_type: "general-purpose",
  model: MODEL_CONFIG["project_manager"],
  description: "PM: All phases complete - final assessment",
  prompt: "FIRST: Read bazinga/prompts/{session_id}/project_manager_all_phases.md which contains your complete instructions.\nTHEN: Execute ALL instructions in that file.\n\nDo NOT proceed without reading the file first.",
  run_in_background: false
)
```

### Why This Rule Exists:

Without this mandatory re-spawn:
- Orchestrator may stop after final phase
- Original scope may not be fully verified
- BAZINGA decision is skipped
- User has to manually trigger completion

**NEVER stop after phases complete. ALWAYS spawn PM to verify scope and send BAZINGA.**

---

