# Specialization Flow Diagnostic: Why Specializations Are Not Being Passed to Agents

**Date:** 2025-12-09
**Context:** Agent prompts (Developer, SSE, QA Expert, Tech Lead) are being spawned WITHOUT specialization content despite extensive documentation and infrastructure
**Decision:** Root cause analysis and fix implementation
**Status:** ✅ REVIEWED + USER APPROVED
**Reviewed by:** OpenAI GPT-5 (2025-12-09)

---

## Problem Statement

The BAZINGA orchestration system has:
1. A fully designed `specialization-loader` skill (`.claude/skills/specialization-loader/SKILL.md`)
2. 72+ specialization templates in `bazinga/templates/specializations/`
3. Detailed documentation in:
   - `agents/orchestrator.md` - §Specialization Loading (lines 1222-1330)
   - `bazinga/templates/prompt_building.md` - Specialization Block Section (lines 88-191)

**Yet** the actual agent prompts being spawned show NO specialization content:

```
You are a SENIOR SOFTWARE ENGINEER AGENT in a Claude Code Multi-Agent Dev Team.

Session Context
Session ID: bazinga_20251209_103316
Group ID: STUB-FDB
Mode: PARALLEL (4 concurrent SSEs)
...
```

**Missing:** The specialization block that should appear at the TOP of the prompt.

---

## Expected Flow (Per Documentation)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        EXPECTED SPECIALIZATION FLOW                              │
└─────────────────────────────────────────────────────────────────────────────────┘

                      ┌──────────────────────┐
                      │   PM Planning        │
                      │ (Step 1 of Orch)     │
                      └──────────┬───────────┘
                                 │
                    PM assigns specializations
                    per task group based on
                    project_context.json
                                 │
                                 ▼
                ┌────────────────────────────────┐
                │ bazinga-db create-task-group   │
                │ --specializations '[           │
                │   "01-languages/typescript.md",│
                │   "03-backend/express.md"      │
                │ ]'                             │
                └────────────────┬───────────────┘
                                 │
                                 ▼
              ┌──────────────────────────────────────┐
              │ ORCHESTRATOR SPAWN STEP (Phase 2A/2B)│
              │                                      │
              │  ┌────────────────────────────────┐  │
              │  │ Step 1: Check skills_config    │  │
              │  │ IF specializations.enabled     │  │
              │  └──────────────┬─────────────────┘  │
              │                 │                    │
              │                 ▼                    │
              │  ┌────────────────────────────────┐  │
              │  │ Step 2: Query DB for group     │  │
              │  │ specializations                │  │
              │  │ bazinga-db get task groups     │  │
              │  └──────────────┬─────────────────┘  │
              │                 │                    │
              │                 ▼                    │
              │  ┌────────────────────────────────┐  │
              │  │ Step 3: Validate array         │  │
              │  │ IF null/empty → skip           │  │
              │  └──────────────┬─────────────────┘  │
              │                 │                    │
              │                 ▼                    │
              │  ┌────────────────────────────────┐  │
              │  │ Step 4a: OUTPUT CONTEXT        │  │
              │  │ Session ID: {id}               │  │
              │  │ Group ID: {group}              │  │
              │  │ Agent Type: developer          │  │
              │  │ Model: haiku                   │  │
              │  │ Specialization Paths: [...]    │  │
              │  └──────────────┬─────────────────┘  │
              │                 │                    │
              │                 ▼                    │
              │  ┌────────────────────────────────┐  │
              │  │ Step 4b: Skill(command:        │  │
              │  │    "specialization-loader")    │  │
              │  └──────────────┬─────────────────┘  │
              │                 │                    │
              │                 ▼                    │
              │  ┌────────────────────────────────┐  │
              │  │ SKILL RETURNS:                 │  │
              │  │ [SPECIALIZATION_BLOCK_START]   │  │
              │  │ ## SPECIALIZATION GUIDANCE     │  │
              │  │ ...content...                  │  │
              │  │ [SPECIALIZATION_BLOCK_END]     │  │
              │  └──────────────┬─────────────────┘  │
              │                 │                    │
              │                 ▼                    │
              │  ┌────────────────────────────────┐  │
              │  │ Step 5: Extract block          │  │
              │  │ Parse between markers          │  │
              │  └──────────────┬─────────────────┘  │
              │                 │                    │
              │                 ▼                    │
              │  ┌────────────────────────────────┐  │
              │  │ Step 6: Build agent prompt     │  │
              │  │ PREPEND specialization block   │  │
              │  │ + base prompt + task           │  │
              │  └──────────────┬─────────────────┘  │
              │                 │                    │
              │                 ▼                    │
              │  ┌────────────────────────────────┐  │
              │  │ Task(subagent_type=...,        │  │
              │  │      prompt=[FULL PROMPT])     │  │
              │  └────────────────────────────────┘  │
              │                                      │
              └──────────────────────────────────────┘
```

---

## Actual Flow (Current Implementation)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        ACTUAL FLOW (THE BUG)                                     │
└─────────────────────────────────────────────────────────────────────────────────┘

              ┌──────────────────────────────────────┐
              │ ORCHESTRATOR SPAWN STEP (Phase 2A/2B)│
              │                                      │
              │  ┌────────────────────────────────┐  │
              │  │ phase_simple.md / phase_parallel│  │
              │  │                                 │  │
              │  │ **Build:** Read agent file +   │  │
              │  │ prompt_building.md (testing    │  │
              │  │ + skills + **specializations**)│  │
              │  │                                 │  │
              │  │        ⚠️ VAGUE REFERENCE       │  │
              │  │    "loaded via prompt_building"│  │
              │  │                                 │  │
              │  └──────────────┬─────────────────┘  │
              │                 │                    │
              │     ❌ NO ACTUAL LOADING STEP       │
              │     ❌ NO Skill() invocation        │
              │     ❌ NO context output            │
              │     ❌ NO block extraction          │
              │                 │                    │
              │                 ▼                    │
              │  ┌────────────────────────────────┐  │
              │  │ **Show Prompt Summary:**       │  │
              │  │ Specializations: {status}      │  │
              │  │                                 │  │
              │  │  ⚠️ SHOWS STATUS BUT NO CONTENT│  │
              │  └──────────────┬─────────────────┘  │
              │                 │                    │
              │                 ▼                    │
              │  ┌────────────────────────────────┐  │
              │  │ **Spawn:**                     │  │
              │  │ Task(subagent_type=...,        │  │
              │  │      prompt=[BASE PROMPT ONLY])│  │
              │  │                                 │  │
              │  │  ❌ MISSING SPECIALIZATION BLOCK│  │
              │  └────────────────────────────────┘  │
              │                                      │
              └──────────────────────────────────────┘
```

---

## Root Cause Analysis

### The Disconnect: Documentation vs. Execution

| Component | Status | Problem |
|-----------|--------|---------|
| `orchestrator.md` §Specialization Loading | ✅ Exists (lines 1222-1330) | DESCRIPTIVE ONLY - describes what should happen |
| `prompt_building.md` specialization section | ✅ Exists (lines 88-191) | GUIDE ONLY - not executable, just instructions |
| `phase_simple.md` spawn steps | ❌ Missing implementation | References "loaded via prompt_building" but doesn't execute the steps |
| `phase_parallel.md` spawn steps | ❌ Missing implementation | Same issue - vague reference, no execution |
| `specialization-loader` skill | ✅ Fully implemented | NEVER INVOKED - skill exists but orchestrator doesn't call it |

### The Critical Gap

**In `phase_simple.md` line 100:**
```markdown
**Build:** Read agent file + `bazinga/templates/prompt_building.md`
(testing_config + skills_config + **specializations** for tier).
```

**What this assumes:** The orchestrator will "know" to:
1. Read skills_config.json
2. Query DB for specializations
3. Output context
4. Invoke Skill(command: "specialization-loader")
5. Extract the block
6. Prepend to prompt

**What actually happens:** The orchestrator reads the "Build" instruction as:
1. Read agent file ✓
2. Read prompt_building.md ✓ (but this is a guide, not executable)
3. Skip to "Spawn" instruction
4. **Never invoke the skill**

### Why This Happens

The templates are **declarative descriptions** masquerading as **executable instructions**:

```markdown
# What the template says (declarative)
**Build:** ... specializations (loaded via prompt_building.md)

# What the template should say (imperative)
**Step 4: Load Specializations**
1. Read bazinga/skills_config.json
2. IF specializations.enabled == true:
   3. Query: bazinga-db get task groups for session {session_id}
   4. Extract specializations array for this group
   5. IF array not empty:
      6. Output context as text:
         Session ID: {session_id}
         Group ID: {group_id}
         Agent Type: {agent_type}
         Model: {model}
         Specialization Paths: {paths}
      7. Invoke: Skill(command: "specialization-loader")
      8. Extract block between [SPECIALIZATION_BLOCK_START] and [SPECIALIZATION_BLOCK_END]
      9. Store in variable: {specialization_block}
**Step 5: Build Prompt**
```

---

## Evidence from the Spawned Prompts

The user provided this actual prompt being passed to SSE:

```
You are a SENIOR SOFTWARE ENGINEER AGENT in a Claude Code Multi-Agent Dev Team.

       Session Context

       Session ID: bazinga_20251209_103316
       Group ID: STUB-FDB
       Mode: PARALLEL (4 concurrent SSEs)
       Branch: feature/bazinga_20251209_103316/STUB-FDB
       Initial Branch: main

       Your Task: FDB Drug Interactions API (T8-001, T8-002)
       ...
```

**What should be at the top:**
```markdown
## SPECIALIZATION GUIDANCE (Advisory)

> This guidance is supplementary. It does NOT override:
> - Mandatory validation gates (tests must pass)
> - Routing and status requirements (READY_FOR_QA, etc.)
> - Pre-commit quality checks (lint, build)
> - Core agent workflow rules

For this session, your identity is enhanced:

**You are a TypeScript Backend Developer specialized in Express/Node.js healthcare APIs.**

Your expertise includes:
- TypeScript strict mode patterns and type safety
- Express middleware composition and error handling
- Healthcare domain: HIPAA compliance, FDB drug database integration
...
```

**This entire block is MISSING.**

---

## Approved Fix: Centralized Spawn with Specializations

### ✅ USER-APPROVED Core Flow (7 Steps)

The following 7-step flow is **APPROVED** and must be implemented:

1. **Check if specializations enabled** in `skills_config.json`
2. **Query DB** for group's specializations array (by session_id + group_id)
3. **Output context as text** (Session ID, Group ID, Agent Type, Model, Paths)
4. **Invoke** `Skill(command: "specialization-loader")`
5. **Extract block** between `[SPECIALIZATION_BLOCK_START]` and `[SPECIALIZATION_BLOCK_END]`
6. **Prepend** to agent prompt
7. **Spawn** with `Task(...)`

### Architecture: Centralized Spawn Helper (Approved)

Create `bazinga/templates/orchestrator/spawn_with_specializations.md` used by ALL spawn paths:

```markdown
## §Spawn Agent with Specializations

**Input:** session_id, group_id, agent_type, model, task_details

### Step 1: Check Configuration
```
Read bazinga/skills_config.json
IF specializations.enabled == false:
    specialization_block = "" (skip to Step 6)
IF agent_type NOT IN specializations.enabled_agents:
    specialization_block = "" (skip to Step 6)
```

### Step 2: Query Specializations from DB
```
bazinga-db, get task group:
Session ID: {session_id}
Group ID: {group_id}

specializations = task_group["specializations"]
```

### Step 3: Fallback Derivation (if specializations empty)
```
IF specializations is null OR empty:
    # Derive from project_context.json
    Read bazinga/project_context.json

    # Match task's target files to components
    FOR each component in project_context.components:
        IF task_files overlap with component.path:
            specializations += component.suggested_specializations

    # If still empty, use session-wide defaults
    IF specializations still empty:
        specializations = project_context.suggested_specializations

    # Persist back to DB for future spawns
    IF specializations not empty:
        bazinga-db update task group --specializations {specializations}
```

### Step 4: Invoke Specialization Loader
```
IF specializations not empty:
    # TWO SEPARATE ACTIONS (skill reads context from conversation)

    OUTPUT (as text, not tool call):
        Session ID: {session_id}
        Group ID: {group_id}
        Agent Type: {agent_type}
        Model: {model}
        Specialization Paths: {specializations JSON array}

    Skill(command: "specialization-loader")

    # Extract block
    Parse response between [SPECIALIZATION_BLOCK_START] and [SPECIALIZATION_BLOCK_END]
    Store as: specialization_block
ELSE:
    specialization_block = ""
```

### Step 5: Log Injection Metadata
```
bazinga-db save-skill-output {session_id} "specialization-injection" '{
    "group_id": "{group_id}",
    "agent_type": "{agent_type}",
    "injected": {true|false},
    "templates_count": {N},
    "block_tokens": {estimated_tokens}
}'
```

### Step 6: Build Complete Prompt
```
prompt = specialization_block + "\n---\n" + base_prompt + task_details
```

### Step 7: Spawn Agent
```
Task(subagent_type="general-purpose", model={model},
     description={desc}, prompt={prompt})
```

### Parallel Mode: Isolation Rule
```
FOR EACH agent in batch:
    # Do context→skill→spawn as TIGHT SEQUENCE per agent
    # Do NOT interleave contexts for multiple agents

    1. Output THIS agent's context
    2. Invoke skill
    3. Extract block
    4. Spawn THIS agent immediately
    5. THEN proceed to next agent
```
```

---

## Implementation Plan (Approved)

### Phase 0: PM Token Optimization (Option C) ✅ APPROVED

**Problem:** PM agent is ~23,556 tokens with ~200 lines of duplicate fallback mapping tables.

**Solution:** Move fallback derivation responsibility from PM to orchestrator.

**Changes to `agents/project_manager.md`:**

1. **Remove** the fallback mapping table (lines ~1500-1700):
   - Delete the `MAPPING_TABLE` dictionary
   - Delete the `lookup_and_validate()` helper
   - Delete the `normalize_technology_name()` helper
   - Delete the fallback logic block

2. **Keep** PM's primary responsibility:
   - PM still reads `project_context.json`
   - PM still assigns `specializations` array per task group
   - PM still stores via `bazinga-db create-task-group --specializations`

3. **Simplify** PM's specialization section to:
   ```markdown
   ### Step 3.5: Assign Specializations per Task Group

   Read bazinga/project_context.json and assign specializations:

   FOR each task_group:
       target_component = identify which component(s) this group targets
       specializations = project_context.components[target].suggested_specializations

       IF specializations found:
           Store with task group: --specializations '{specializations}'
       ELSE:
           Store empty array: --specializations '[]'
           (Orchestrator will derive fallback at spawn time)
   ```

**Token savings:** ~500 tokens (removes ~200 lines of mapping tables)

**Workflow impact:** None - PM still assigns, orchestrator handles fallback if PM misses.

---

### Phase 1: Create Centralized Spawn Template

1. **Create** `bazinga/templates/orchestrator/spawn_with_specializations.md`
   - Full implementation of 7-step flow above
   - Include fallback derivation logic (moved from PM)
   - Include parallel mode isolation rule
   - Include injection verification logging

### Phase 2: Update Phase Templates

2. **Update `phase_simple.md`**:
   - Replace inline spawn instructions with: "Follow §Spawn Agent with Specializations"
   - Apply to: Step 2A.1 (Developer), 2A.3 (SSE escalation), 2A.4 (QA), 2A.5 (QA respawn), 2A.6 (Tech Lead), 2A.7 (Developer fix)

3. **Update `phase_parallel.md`**:
   - Same changes
   - **CRITICAL:** In Step 2B.1, process each agent sequentially per isolation rule
   - Apply to all spawn points

4. **Update `merge_workflow.md`**:
   - Apply same pattern for Developer merge spawns

### Phase 3: Cover All Orchestrators

5. **Update `orchestrator_speckit.md`**:
   - Same centralized spawn reference
   - Ensure spec-kit agents get specializations too

### Phase 4: Add Verification Gate

6. **Extend bazinga-validator** (optional):
   - Check that spawned prompts contain `[SPECIALIZATION_BLOCK_START]` when:
     - `specializations.enabled == true`
     - Templates exist for the project's stack
   - Report violations as warnings (not blockers initially)

### Phase 5: Validation

7. **Test scenarios:**
   - Simple mode: Dev with specializations
   - Parallel mode: 4 devs with different specializations per group
   - Fallback: PM doesn't assign → derived from project_context.json
   - Escalation: Developer fails → SSE gets specializations
   - Disabled: specializations.enabled=false → graceful skip

---

## Multi-LLM Review Integration

### Reviewer
- **OpenAI GPT-5** (2025-12-09)

### Incorporated Feedback (User Approved)

| Change | Description | Status |
|--------|-------------|--------|
| Centralized Spawn Helper | Single "Spawn Agent with Specializations" procedure used by ALL paths | ✅ APPROVED |
| Parallel Mode Isolation | context→skill→spawn as tight sequence PER agent (no interleaving) | ✅ APPROVED |
| Fallback Derivation | If PM misses specializations, derive from project_context.json | ✅ APPROVED |
| Injection Verification | Log {injected, templates_count, block_tokens} per spawn | ✅ APPROVED |
| Spec-Kit Coverage | Update orchestrator_speckit.md to use same pattern | ✅ APPROVED |
| **PM Token Optimization (Option C)** | Move fallback mapping tables from PM to orchestrator, saves ~500 tokens | ✅ APPROVED |

### Rejected Suggestions (With Reasoning)

| Suggestion | Reason for Rejection |
|------------|---------------------|
| **Caching composed blocks** | Each task group should have targeted specializations. While cache key includes (session_id, group_id, agent_type, model), caching adds complexity without clear benefit. Specialization-loader already runs quickly. Can add later if latency becomes an issue. |

### Additional LLM Suggestions (Noted for Future)

1. **Orchestration-level token budgeting** - Define priority order for prompt sections. Defer to future optimization.
2. **Validator hook for BAZINGA** - Extend bazinga-validator to assert specialization blocks present. Added as optional Phase 4.

---

## Risk Assessment (Updated)

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Breaking existing flow | LOW | HIGH | Specialization loading is additive, not replacing |
| Token budget exceeded | MEDIUM | MEDIUM | Skill has built-in token limits |
| Skill not returning valid block | LOW | MEDIUM | Fallback: proceed without specialization |
| PM not assigning specializations | MEDIUM | LOW | **NEW:** Fallback derivation from project_context.json |
| Parallel mode context collision | MEDIUM | HIGH | **NEW:** Isolation rule - tight sequence per agent |
| Silent injection failures | MEDIUM | MEDIUM | **NEW:** Injection verification logging |

---

## Success Criteria (Updated)

1. ✅ Agent prompts include `## SPECIALIZATION GUIDANCE` section at top
2. ✅ Specialization-loader skill is invoked before each agent spawn
3. ✅ Token budget respected (haiku: 600, sonnet: 1200, opus: 1600)
4. ✅ Graceful degradation when specializations disabled/empty
5. ✅ No regression in existing orchestration flow
6. ✅ **NEW:** Parallel mode spawns have correct per-agent specializations
7. ✅ **NEW:** Injection metadata logged for audit trail
8. ✅ **NEW:** Fallback derivation works when PM doesn't assign
9. ✅ **NEW:** Spec-kit orchestrator also injects specializations

---

## References

- `agents/orchestrator.md` §Specialization Loading (lines 1222-1330)
- `bazinga/templates/prompt_building.md` (lines 88-191)
- `bazinga/templates/orchestrator/phase_simple.md`
- `bazinga/templates/orchestrator/phase_parallel.md`
- `.claude/skills/specialization-loader/SKILL.md`
- `research/orchestrator-specialization-integration-ultrathink-2025-12-04.md`
- `tmp/ultrathink-reviews/combined-review.md` (OpenAI GPT-5 review)
