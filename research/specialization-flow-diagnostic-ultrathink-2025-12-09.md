# Specialization Flow Diagnostic: Why Specializations Are Not Being Passed to Agents

**Date:** 2025-12-09
**Context:** Agent prompts (Developer, SSE, QA Expert, Tech Lead) are being spawned WITHOUT specialization content despite extensive documentation and infrastructure
**Decision:** Root cause analysis and fix implementation
**Status:** Proposed - awaiting LLM review

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

## Proposed Fix

### Option A: Explicit Steps in Phase Templates (Recommended)

Add explicit specialization loading steps to `phase_simple.md` and `phase_parallel.md`:

```markdown
### Step 2A.1: Spawn Single Developer

**User output:** `🔨 Implementing | Spawning developer for {brief_task_description}`

**Step 1: Load Specializations (if enabled)**

```
# Check configuration
Read bazinga/skills_config.json
IF specializations.enabled == false OR agent_type NOT IN enabled_agents:
    specialization_block = "" (empty)
    SKIP to Step 2

# Query DB for group's specializations
bazinga-db, get task groups for session {session_id}
specializations = task_group["specializations"]

IF specializations is null OR empty:
    specialization_block = "" (empty)
    SKIP to Step 2

# Invoke skill (TWO ACTIONS)
OUTPUT (as text, not tool call):
    Session ID: {session_id}
    Group ID: {group_id}
    Agent Type: {developer|senior_software_engineer}
    Model: {model from MODEL_CONFIG}
    Specialization Paths: {specializations JSON array}

Skill(command: "specialization-loader")

# Extract block
Parse skill response between [SPECIALIZATION_BLOCK_START] and [SPECIALIZATION_BLOCK_END]
Store as: specialization_block
```

**Step 2: Build Prompt**

```
prompt = specialization_block + "\n---\n" + base_prompt + task_details
```

**Step 3: Spawn**
```
Task(subagent_type="general-purpose", model=MODEL_CONFIG[tier],
     description=desc, prompt=prompt)
```
```

### Option B: Centralized Spawn Function

Create `bazinga/templates/orchestrator/spawn_agent.md` with the complete spawn flow including specializations:

```markdown
## §Spawn Agent with Specializations

**Input:** agent_type, group_id, session_id, task_details, tier

**Step 1: Load Specializations**
[full implementation]

**Step 2: Load Context Packages**
[full implementation]

**Step 3: Load Reasoning Context**
[full implementation]

**Step 4: Build Prompt**
[composition of all pieces]

**Step 5: Spawn**
Task(...)
```

Then phase templates just reference: "Follow §Spawn Agent with Specializations"

---

## Comparison: Option A vs Option B

| Aspect | Option A: Explicit Steps | Option B: Centralized |
|--------|-------------------------|----------------------|
| Implementation effort | Medium (update 2 files) | High (new file + updates) |
| Token cost | Higher (duplicated in 2A and 2B) | Lower (single reference) |
| Clarity | Very clear (step by step) | Requires template lookup |
| Risk of drift | Each template may diverge | Single source of truth |
| Debugging | Easy to see what's missing | Need to read separate file |

**Recommendation:** Option A for immediate fix (explicit is better than implicit), then migrate to Option B in a future optimization pass.

---

## Implementation Plan

### Phase 1: Immediate Fix (Option A)

1. **Update `phase_simple.md`** (Step 2A.1):
   - Add explicit specialization loading steps before "Build:" instruction
   - Include the Skill() invocation pattern
   - Add block extraction and prepend logic

2. **Update `phase_parallel.md`** (Step 2B.1):
   - Same changes for parallel spawn
   - Apply to each group in the parallel spawn loop

3. **Update escalation spawns:**
   - SSE escalation (Step 2A.3)
   - QA respawn (Step 2A.5)
   - Developer respawn after TL rejection (Step 2A.7)

### Phase 2: Validation

1. Run orchestration with a project that has `project_context.json`
2. Verify specialization-loader skill is invoked
3. Verify block appears in spawned agent prompts
4. Verify agents apply the patterns

### Phase 3: Future Optimization (Option B)

Create centralized spawn template to reduce duplication.

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Breaking existing flow | LOW | HIGH | Specialization loading is additive, not replacing |
| Token budget exceeded | MEDIUM | MEDIUM | Skill has built-in token limits |
| Skill not returning valid block | LOW | MEDIUM | Fallback: proceed without specialization |
| PM not assigning specializations | MEDIUM | LOW | Tech Stack Scout creates project_context.json |

---

## Success Criteria

1. Agent prompts include `## SPECIALIZATION GUIDANCE` section at top
2. Specialization-loader skill is invoked before each agent spawn
3. Token budget respected (haiku: 600, sonnet: 1200, opus: 1600)
4. Graceful degradation when specializations disabled/empty
5. No regression in existing orchestration flow

---

## Questions for Validation

1. Should specialization loading be mandatory (always attempt) or opt-in (only if config enabled)?
   - **Current design:** Opt-in based on `skills_config.json` setting

2. Should specialization loading happen for ALL agent types or only certain ones?
   - **Current design:** Controlled by `enabled_agents` array in config

3. What if the skill invocation fails?
   - **Current design:** Log warning, proceed without specialization (non-blocking)

---

## References

- `agents/orchestrator.md` §Specialization Loading (lines 1222-1330)
- `bazinga/templates/prompt_building.md` (lines 88-191)
- `bazinga/templates/orchestrator/phase_simple.md`
- `bazinga/templates/orchestrator/phase_parallel.md`
- `.claude/skills/specialization-loader/SKILL.md`
- `research/orchestrator-specialization-integration-ultrathink-2025-12-04.md`
