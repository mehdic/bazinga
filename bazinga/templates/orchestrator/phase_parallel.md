## Phase 2B: Parallel Mode Execution

**Before any Bash command:** See §Policy-Gate and §Bash Command Allowlist in orchestrator.md

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
• {group_id}: {tier_name} ({model}) - {task[:90]}
[repeat for each group]

💡 For ≥3 developers, consider `/compact` first.
⏳ Continuing immediately... (Ctrl+C to pause. Resume via `/bazinga.orchestrate` after `/compact`)
```

**Example output (4 developers):**
```
🔨 **Phase 1 starting** | Spawning 4 developers in parallel

📋 **Developer Assignments:**
• P0-NURSE-FE: Senior Software Engineer (Sonnet) - Nurse App Frontend with auth integration
• P0-NURSE-BE: Senior Software Engineer (Sonnet) - Nurse Backend Services with API endpoints
• P0-MSG-BE: Senior Software Engineer (Sonnet) - Messaging Backend with WhatsApp channel
• P1-DOCTOR-FE: Developer (Haiku) - Doctor Frontend basic components

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

**🔴 Context Package Query (PER GROUP before spawn):**

For each group, query context packages:
```
bazinga-db, please get context packages:

Session ID: {session_id}
Group ID: {group_id}
Agent Type: {agent_type}
Limit: 3
```
Then invoke: `Skill(command: "bazinga-db")`. Include returned packages in that group's prompt (see Simple Mode §Context Package Routing Rules for format). Query errors are non-blocking.

**🔴 Reasoning Context Query (PER GROUP, AFTER context packages):**

For each group, query prior agent reasoning:
```
bazinga-db, please get reasoning:

Session ID: {session_id}
Group ID: {group_id}
Limit: 5
```
Then invoke: `Skill(command: "bazinga-db")`
Include returned reasoning in prompt (see Simple Mode §Reasoning Context Routing Rules for format). Query errors are non-blocking (proceed without reasoning if query fails).

## SPAWN DEVELOPERS - PARALLEL (ATOMIC SEQUENCE PER GROUP)

**To spawn developers in parallel, you MUST produce specializations THEN spawns for EACH group.**

**There is no Task() without the Skill() first. They are ONE action per group.**

---

### PART A: Build Base Prompts (internal, all groups, DO NOT OUTPUT)

**🔴 You MUST build a prompt string for EACH group. Do NOT skip this step.**

**For EACH group (A, B, C, D):**

**Step A.1: Gather data from task_groups[group_id]:**
```
task_title = task_groups[group_id]["title"]
task_requirements = task_groups[group_id]["requirements"]  # The actual work to do
branch = task_groups[group_id]["branch"] or session_branch
initial_tier = task_groups[group_id]["initial_tier"]
```

**Step A.2: Build base_prompt string using this template:**
```
You are a Developer in a Claude Code Multi-Agent Dev Team.

**SESSION:** {session_id}
**GROUP:** {group_id}
**MODE:** Parallel
**BRANCH:** {branch}

**TASK:** {task_title}

**REQUIREMENTS:**
{task_requirements}

**MANDATORY WORKFLOW:**
1. Implement the complete solution
2. Write unit tests for new code
3. Run lint check (must pass)
4. Run build check (must pass)
5. Commit to branch: {branch}
6. Report status: READY_FOR_QA or BLOCKED

**OUTPUT FORMAT:**
Use standard Developer response format with STATUS, FILES, TESTS, COVERAGE sections.
```

**Step A.3: Store as `base_prompts[group_id]`. DO NOT output to user.**

---

### PART B: Load Specializations → Then Spawn (FUSED ACTION PER GROUP)

**Check `bazinga/skills_config.json` once:** Is `specializations.enabled == true` AND agent_type in `enabled_agents`?

**IF YES (specializations enabled for this agent type):**

**Step B.1: Get specializations per group (with fallback derivation)**
```
FOR each group_id in groups:
    specializations = task_groups[group_id]["specializations"]  # May be null/empty

    IF specializations is null OR empty:
        # FALLBACK: Derive from project_context.json (read once, reuse)
        IF project_context not loaded:
            Read(file_path: "bazinga/project_context.json")

        IF components exists with suggested_specializations:
            specializations = merge all component.suggested_specializations
        ELSE IF suggested_specializations exists (session-wide):
            specializations = suggested_specializations
        ELSE IF primary_language or framework exists:
            specializations = map_to_template_paths(primary_language, framework)
            # See spawn_with_specializations.md for mapping table

    group_specializations[group_id] = specializations  # May still be empty
```

**Step B.2: For EACH group with non-empty specializations**, output context and invoke skill:

```
🔧 Loading specializations for Group {group_id} ({agent_type})...

[SPEC_CTX_START group={group_id} agent={agent_type}]
Session ID: {session_id}
Group ID: {group_id}
Agent Type: {agent_type}
Model: {MODEL_CONFIG[task_groups[group_id].initial_tier]}
Specialization Paths: {group_specializations[group_id] as JSON array}
[SPEC_CTX_END]
```

Then IMMEDIATELY call:
```
Skill(command: "specialization-loader")
```

Then extract block from response. Store as `specialization_blocks[group_id]`.

**Repeat for EACH group (A, B, C, D - MAX 4) before spawning any Task.**

**After ALL specializations loaded, output summary and spawn ALL:**
```
🔧 Specializations loaded: A ({N} templates), B ({N} templates), C ({N} templates)

📝 Spawning {count} developers in parallel:
• Group A: {task_groups["A"].initial_tier} | {task_groups["A"].title}
• Group B: {task_groups["B"].initial_tier} | {task_groups["B"].title}
...

Task(subagent_type="general-purpose", model=MODEL_CONFIG[task_groups["A"].initial_tier], description=f"{task_groups['A'].initial_tier} A: {task_groups['A'].title[:90]}", prompt={spec_block_A + base_A})
Task(subagent_type="general-purpose", model=MODEL_CONFIG[task_groups["B"].initial_tier], description=f"{task_groups['B'].initial_tier} B: {task_groups['B'].title[:90]}", prompt={spec_block_B + base_B})
...
```

**IF any group's skill fails:** Use base_prompt for that group, note in summary:
```
🔧 Specializations: A (loaded), B (⚠️ failed), C (loaded)
```

**IF NO (specializations disabled or agent not in enabled_agents):** Skip all Skill() calls, spawn directly:
```
📝 Spawning {count} developers in parallel | Specializations: disabled
• Group A: {task_groups["A"].initial_tier} | {task_groups["A"].title}
...

Task(subagent_type="general-purpose", model=MODEL_CONFIG[task_groups["A"].initial_tier], description=f"{task_groups['A'].initial_tier} A: {task_groups['A'].title[:90]}", prompt={base_A})
Task(subagent_type="general-purpose", model=MODEL_CONFIG[task_groups["B"].initial_tier], description=f"{task_groups['B'].initial_tier} B: {task_groups['B'].title[:90]}", prompt={base_B})
...
```

**🔴 MAX 4 groups.** If >4, spawn first 4, defer rest.

---

### TWO-TURN SPAWN SEQUENCE (Parallel Mode)

**IMPORTANT:** Skill() and Task() CANNOT be in the same message because Task() needs the specialization_block from each Skill()'s response.

**Turn 1 (this message):**
1. For EACH group, output the `[SPEC_CTX_START group=X]...[SPEC_CTX_END]` block
2. Call `Skill(command: "specialization-loader")` for EACH group (all in this message)
3. END this message (wait for all skill responses)

**Turn 2 (after skill responses):**
1. Read each skill response (internally - DO NOT echo to user)
2. Extract content between `[SPECIALIZATION_BLOCK_START]` and `[SPECIALIZATION_BLOCK_END]` for each group → store as `spec_blocks[group_id]`
3. Build `FULL_PROMPT_X = spec_blocks[X] + "\n\n---\n\n" + base_prompts[X]` for each group
4. **🔴 IMMEDIATELY output capsule and call ALL `Task()` spawns in THIS message**

**🔴🔴🔴 CRITICAL - TURN 2 MUST CALL TASK() 🔴🔴🔴**

After extracting ALL specialization blocks (silently), you MUST:
1. Output ONLY the spawn summary capsule (not the spec blocks)
2. **Call Task() for EACH group in THIS SAME MESSAGE**
3. DO NOT end the message without Task() calls

**WRONG (Bug Pattern - echoing spec blocks):**
```
[SPECIALIZATION_BLOCK_START]
...
[SPECIALIZATION_BLOCK_END]  ← WRONG! Don't echo this to user

📝 Spawning 4 developers...

[MESSAGE ENDS - NO TASK() CALLS]  ← BUG! Workflow hangs
```

**CORRECT (silent extraction, capsule only):**
```
🔧 Specializations loaded: A (3 templates), B (3 templates), C (3 templates)

📝 Spawning 3 developers in parallel:
• Group A: Developer | Initialize Delivery App Structure | Specializations: ✓
• Group B: Developer | Delivery Request List & Detail | Specializations: ✓
• Group C: Developer | Order Tracking Dashboard | Specializations: ✓

Task(subagent_type="general-purpose", model="haiku", description="Developer A: Initialize Delivery App Structure", prompt=FULL_PROMPT_A)
Task(subagent_type="general-purpose", model="haiku", description="Developer B: Delivery Request List & Detail", prompt=FULL_PROMPT_B)
Task(subagent_type="general-purpose", model="haiku", description="Developer C: Order Tracking Dashboard", prompt=FULL_PROMPT_C)
```

**🔴🔴🔴 CRITICAL - FULL_PROMPT MUST COMBINE BOTH PARTS 🔴🔴🔴**

Each group's `prompt` parameter MUST be the **concatenation** of:
1. **spec_block** - The specialization content from the skill (HOW to code)
2. **base_prompt_X** - That group's task assignment from PM built in PART A (WHAT to code)

**Example of FULL_PROMPT_A (what you pass to Task for group A):**
```
## SPECIALIZATION GUIDANCE (Advisory)
You are a React/TypeScript Frontend Developer specialized in Next.js 14...
[patterns, anti-patterns from spec_block]

---

You are a Developer in a Claude Code Multi-Agent Dev Team.

**SESSION:** abc123
**GROUP:** A (R2-INIT)
**MODE:** Parallel
**BRANCH:** feature/delivery-app

**REQUIREMENTS:**
Initialize the delivery app structure:
- Set up Next.js 14 project with App Router
- Configure TypeScript, ESLint, Prettier
- Create base layout and navigation components

**MANDATORY WORKFLOW:**
1. Run codebase-analysis skill
2. Implement the solution
3. Write unit tests
4. Run lint + build
5. Commit and report READY_FOR_QA
```

**WRONG (spec_block only - missing task assignment):**
```
prompt="## SPECIALIZATION GUIDANCE\nYou are a React/TypeScript..."
```
↑ Developer knows HOW to code but NOT WHAT to build!

**CORRECT (both parts combined for each group):**
```
prompt_A = spec_block + "\n\n---\n\n" + base_prompt_A
prompt_B = spec_block + "\n\n---\n\n" + base_prompt_B
```
↑ Each developer knows BOTH the patterns AND their specific requirements!

**SELF-CHECK (Turn 2):** Did I extract ALL specialization blocks? Does this message contain `Task()` for EACH group? Does EACH prompt include BOTH spec_block AND that group's base_prompt (with the actual requirements)?

**Count your Task() calls:** Should match number of groups (max 4).

---

**AFTER receiving ALL developer responses:**

### Step 2B.2: Receive All Developer Responses

**For EACH developer response:**

**Step 1: Parse response and output capsule to user**

Use the Developer Response Parsing section from `bazinga/templates/response_parsing.md` (loaded at initialization) to extract status, files, tests, coverage, summary.

**Step 2: Construct and output capsule** (same templates as Step 2A.2):
- READY_FOR_QA/REVIEW: `🔨 Group {id} [{tier}/{model}] complete | {summary}, {files}, {tests}, {coverage} | {status} → {next}`
- PARTIAL: `🔨 Group {id} [{tier}/{model}] implementing | {what's done} | {current_status}`
- BLOCKED: `⚠️ Group {id} [{tier}/{model}] blocked | {blocker} | Investigating`

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
2. Build spawn queue: INCOMPLETE/PARTIAL → Developer, FAILED → Investigator, READY_FOR_QA → QA, READY_FOR_REVIEW → Tech Lead
3. Spawn ALL missing Tasks in ONE message
4. Output: `🔄 Auto-fix: Found {N} incomplete → Spawning {agents} in parallel`
5. Re-run checklist

**PASS CRITERIA (ALL THREE must pass):** ✅ All responses processed ✅ No incomplete groups unhandled ✅ All required Tasks spawned

**FORBIDDEN:** ❌ Serialization ("first... then...") ❌ Partial spawning ❌ Ending with INCOMPLETE groups

**This verification gate is your final responsibility check. DO NOT bypass it.**

### Step 2B.8: Spawn PM When All Groups Complete



**User output (capsule format):**
```
✅ All groups complete | {N}/{N} groups approved, all quality gates passed | Final PM check → BAZINGA
```

Build PM prompt with:
- Session context
- All group results and commit summaries
- Overall status check request

Spawn: `Task(subagent_type="general-purpose", model=MODEL_CONFIG["project_manager"], description="PM overall assessment", prompt=[PM prompt])`


**AFTER PM response:** Follow §Step 2A.8 process (parse, construct capsule, apply auto-route rules).
**Log:** §Logging Reference with ID: `pm_parallel_final`
**Track:** Invoke `Skill(command: "velocity-tracker")` with session + groups + duration

### Step 2B.9: Route PM Response

Follow §Step 2A.9 routing rules with parallel-mode adaptations:
- **CONTINUE:** Spawn ALL groups in ONE message (not sequential)
- **INVESTIGATION_NEEDED:** Include all affected group IDs and branches; Investigator→TL→Dev(s)→QA→TL→PM
- **NEEDS_CLARIFICATION:** §Step 1.3a (only stop point)

---

