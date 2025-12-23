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
2. 72+ specialization templates in `templates/specializations/`
3. Detailed documentation in:
   - `agents/orchestrator.md` - §Specialization Loading (lines 1222-1330)
   - `templates/prompt_building.md` - Specialization Block Section (lines 88-191)

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
**Build:** Read agent file + `templates/prompt_building.md`
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

Create `templates/orchestrator/spawn_with_specializations.md` used by ALL spawn paths:

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

1. **Create** `templates/orchestrator/spawn_with_specializations.md`
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

# DETAILED IMPLEMENTATION SPECIFICATION

## File Inventory and Line Numbers

### Files to CREATE (1 file)

| File | Purpose | Est. Lines |
|------|---------|------------|
| `templates/orchestrator/spawn_with_specializations.md` | Centralized spawn helper | ~150 lines |

### Files to MODIFY (4 files)

| File | Lines to Change | Change Type |
|------|----------------|-------------|
| `agents/project_manager.md` | 1502-1871 | DELETE ~370 lines (fallback mapping) |
| `templates/orchestrator/phase_simple.md` | 99-116, 200, 218, 234, 240, 289, 341, 410 | UPDATE spawn instructions |
| `templates/orchestrator/phase_parallel.md` | 183-209 | UPDATE parallel spawn |
| `agents/orchestrator_speckit.md` | 120-150 | UPDATE to use centralized spawn |

---

## Phase 0: PM Token Optimization - DETAILED SPEC

### File: `agents/project_manager.md`

**DELETE Lines 1502-1871** (~370 lines)

This removes:
1. **Fallback Mapping Table** (lines 1506-1529) - Human-readable table
2. **MAPPING_TABLE dictionary** (lines 1535-1558) - Code table
3. **Helper functions** (lines 1560-1669):
   - `remove_punctuation()`
   - `remove_whitespace()`
   - `file_exists()`
   - `LOG_WARNING()`
   - `normalize_key()`
   - `parse_frameworks()`
   - `dedupe_stable()`
   - `lookup_and_validate()`
4. **Fallback logic block** (lines 1671-1711)
5. **path_matches function** (lines 1746-1776)
6. **Extended fallback mapping** (lines 1797-1833)

**REPLACE WITH** (simplified version ~40 lines):

```markdown
### Step 3.5: Assign Specializations per Task Group

**Purpose:** Assign technology-specific template paths to each task group based on project_context.json.

**Step 3.5.1: Read Project Context**

```
Read(file_path: "bazinga/project_context.json")
```

**If file missing:** Skip specializations. Orchestrator will derive fallback at spawn time.

**Step 3.5.2: Map Task Groups to Components**

For each task group, determine which component(s) it targets:

```
FOR each task_group:
    specializations = []

    # Extract file paths from task description
    target_paths = extract file paths from task description

    # Match against project_context.components
    FOR each component in project_context.components:
        IF task targets files within component.path:
            specializations.extend(component.suggested_specializations)

    # Deduplicate while preserving order
    specializations = dedupe_stable(specializations)
    task_group.specializations = specializations
```

**Step 3.5.3: Include Specializations in Task Group Definition**

When creating task groups:

```markdown
**Group A:** Implement Login UI
- **Specializations:** ["templates/specializations/01-languages/typescript.md", "templates/specializations/02-frameworks-frontend/nextjs.md"]
```

**Step 3.5.4: Store via bazinga-db**

```
bazinga-db, please create task group:
Group ID: A
--specializations '["path1.md", "path2.md"]'
```

**If no specializations found:** Store empty array `--specializations '[]'`. Orchestrator derives fallback.

---
```

**Impact Analysis:**

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| PM file size | ~94KB / 2603 lines | ~82KB / ~2230 lines | -12KB / -373 lines |
| PM token count | ~23,556 tokens | ~20,500 tokens | -~3,000 tokens |
| Fallback logic owner | PM | Orchestrator | Moved responsibility |
| Truncation risk | HIGH | MEDIUM | Reduced |

---

## Phase 1: Create Centralized Spawn Template - DETAILED SPEC

### NEW FILE: `templates/orchestrator/spawn_with_specializations.md`

**Full Content:**

```markdown
# §Spawn Agent with Specializations

**Version:** 1.0
**Purpose:** Centralized agent spawn procedure that loads and injects specializations before spawning.

**When to use:** Before EVERY agent spawn (Developer, SSE, QA Expert, Tech Lead, RE, Investigator).

---

## Input Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| session_id | Yes | Current orchestration session ID |
| group_id | Yes | Task group ID (e.g., "main", "A", "B") |
| agent_type | Yes | One of: developer, senior_software_engineer, qa_expert, tech_lead, requirements_engineer, investigator |
| model | Yes | Model from MODEL_CONFIG (haiku, sonnet, opus) |
| base_prompt | Yes | The agent's base prompt (from agent file + task details) |
| task_description | Yes | Brief task description for Task() description field |

---

## Execution Steps

### Step 1: Check Configuration

```
Read bazinga/skills_config.json

IF "specializations" section missing OR specializations.enabled == false:
    specialization_block = ""
    → SKIP to Step 6

IF agent_type NOT IN specializations.enabled_agents:
    specialization_block = ""
    → SKIP to Step 6
```

**enabled_agents from skills_config.json:**
```json
["developer", "senior_software_engineer", "qa_expert", "tech_lead", "requirements_engineer", "investigator"]
```

### Step 2: Query Specializations from Database

```
bazinga-db, please get task group:

Session ID: {session_id}
Group ID: {group_id}
```

Then invoke: `Skill(command: "bazinga-db")`

Extract: `specializations = task_group["specializations"]`

### Step 3: Fallback Derivation (if specializations empty)

```
IF specializations is null OR empty array:

    # Read project context for fallback
    Read(file_path: "bazinga/project_context.json")

    IF file exists AND has content:
        specializations = []

        # Strategy 1: Component matching (if components exist)
        IF project_context.components exists:
            FOR each component in project_context.components:
                IF component.suggested_specializations exists:
                    specializations.extend(component.suggested_specializations)

        # Strategy 2: Session-wide defaults (if still empty)
        IF len(specializations) == 0 AND project_context.suggested_specializations exists:
            specializations = project_context.suggested_specializations

        # Strategy 3: Manual mapping from primary fields (last resort)
        IF len(specializations) == 0:
            # Map primary_language
            IF project_context.primary_language:
                path = map_technology_to_template(project_context.primary_language)
                IF path: specializations.append(path)

            # Map framework
            IF project_context.framework:
                frameworks = parse_comma_separated(project_context.framework)
                FOR fw in frameworks:
                    path = map_technology_to_template(fw)
                    IF path: specializations.append(path)

        # Deduplicate
        specializations = remove_duplicates_preserve_order(specializations)

        # Persist back to DB for future spawns in this group
        IF len(specializations) > 0:
            bazinga-db, update task group:
            Group ID: {group_id}
            --specializations '{json.dumps(specializations)}'

            Skill(command: "bazinga-db")
```

**Fallback Mapping Table (embedded):**

| Technology | Template Path |
|------------|---------------|
| typescript, ts | `templates/specializations/01-languages/typescript.md` |
| javascript, js | `templates/specializations/01-languages/javascript.md` |
| python, py | `templates/specializations/01-languages/python.md` |
| java | `templates/specializations/01-languages/java.md` |
| go, golang | `templates/specializations/01-languages/go.md` |
| rust | `templates/specializations/01-languages/rust.md` |
| react | `templates/specializations/02-frameworks-frontend/react.md` |
| nextjs, next.js | `templates/specializations/02-frameworks-frontend/nextjs.md` |
| vue | `templates/specializations/02-frameworks-frontend/vue.md` |
| angular | `templates/specializations/02-frameworks-frontend/angular.md` |
| express | `templates/specializations/03-frameworks-backend/express.md` |
| fastapi | `templates/specializations/03-frameworks-backend/fastapi.md` |
| django | `templates/specializations/03-frameworks-backend/django.md` |
| springboot, spring | `templates/specializations/03-frameworks-backend/spring-boot.md` |
| postgresql, postgres | `templates/specializations/05-databases/postgresql.md` |
| mongodb, mongo | `templates/specializations/05-databases/mongodb.md` |
| kubernetes, k8s | `templates/specializations/06-infrastructure/kubernetes.md` |
| docker | `templates/specializations/06-infrastructure/docker.md` |
| jest, vitest | `templates/specializations/08-testing/jest-vitest.md` |
| playwright, cypress | `templates/specializations/08-testing/playwright-cypress.md` |

### Step 4: Invoke Specialization Loader Skill

```
IF len(specializations) > 0:

    # ⚠️ TWO SEPARATE ACTIONS - skill reads context from conversation

    # Action 4a: Output context as TEXT (not tool call)
    OUTPUT:
        Session ID: {session_id}
        Group ID: {group_id}
        Agent Type: {agent_type}
        Model: {model}
        Specialization Paths: {json.dumps(specializations)}

    # Action 4b: Invoke the skill
    Skill(command: "specialization-loader")

    # Action 4c: Extract block from skill response
    # Parse text between markers:
    specialization_block = extract_between(
        skill_response,
        "[SPECIALIZATION_BLOCK_START]",
        "[SPECIALIZATION_BLOCK_END]"
    )

    IF specialization_block is empty:
        LOG: "Warning: specialization-loader returned empty block"
        specialization_block = ""

ELSE:
    specialization_block = ""
```

### Step 5: Log Injection Metadata

```
bazinga-db save-skill-output {session_id} "specialization-injection" '{
    "group_id": "{group_id}",
    "agent_type": "{agent_type}",
    "model": "{model}",
    "injected": {true if specialization_block else false},
    "templates_count": {len(specializations)},
    "block_tokens": {len(specialization_block) // 4}
}'

Skill(command: "bazinga-db")
```

### Step 6: Build Complete Prompt

```
IF specialization_block:
    full_prompt = specialization_block + "\n\n---\n\n" + base_prompt
ELSE:
    full_prompt = base_prompt
```

### Step 7: Spawn Agent

```
Task(
    subagent_type="general-purpose",
    model={model},
    description={task_description},
    prompt={full_prompt}
)
```

---

## Parallel Mode: Isolation Rule

**⚠️ CRITICAL:** When spawning multiple agents in one orchestrator message:

```
FOR EACH agent in batch:
    # Do context→skill→spawn as TIGHT SEQUENCE per agent
    # Do NOT interleave contexts for multiple agents

    # Agent 1:
    1. Output Agent 1's specialization context
    2. Skill(command: "specialization-loader")
    3. Extract Agent 1's block
    4. Task(...) for Agent 1

    # Agent 2:
    5. Output Agent 2's specialization context
    6. Skill(command: "specialization-loader")
    7. Extract Agent 2's block
    8. Task(...) for Agent 2

    # ... etc.
```

**Why:** The skill reads context from the conversation. If you output all contexts first, then invoke the skill multiple times, the skill will read the WRONG context for each invocation.

---

## Error Handling

| Error | Action |
|-------|--------|
| skills_config.json missing | Proceed without specializations |
| specializations.enabled = false | Proceed without specializations |
| DB query fails | Log warning, proceed without specializations |
| project_context.json missing | Proceed without specializations |
| specialization-loader returns empty | Log warning, proceed without specializations |
| skill invocation fails | Log warning, proceed without specializations |

**All errors are non-blocking.** Spawn proceeds with base_prompt only.

---

## Usage Example

**Before this template:**
```
Task(subagent_type="general-purpose", model=MODEL_CONFIG["developer"],
     description="Dev A: implement login", prompt=[base_prompt])
```

**After this template:**
```
# Follow §Spawn Agent with Specializations
# With inputs: session_id, group_id="A", agent_type="developer",
#              model=MODEL_CONFIG["developer"], base_prompt=[...],
#              task_description="Dev A: implement login"
```
```

---

## Phase 2: Update Phase Templates - DETAILED SPEC

### File: `templates/orchestrator/phase_simple.md`

#### Change 1: Initial Developer Spawn (Lines 99-116)

**BEFORE (line 99-116):**
```markdown
**Build:** Read agent file + `templates/prompt_building.md` (testing_config + skills_config + **specializations** for tier). **Include:** Agent, Group=main, Mode=Simple, Session, Branch, Skills/Testing, Task from PM, **Context Packages (if any)**, **Reasoning Context (if any)**, **Specializations (loaded via prompt_building.md)**. **Validate:** ✓ Skills, ✓ Workflow, ✓ Testing, ✓ Report format, ✓ Specializations. **Show Prompt Summary:** Output structured summary (NOT full prompt):
```text
📝 **{agent_type} Prompt** | Group: {group_id} | Model: {model}
...
```
**Spawn:** `Task(subagent_type="general-purpose", model=MODEL_CONFIG[tier], description=desc, prompt=[prompt])`
```

**AFTER:**
```markdown
**Build Base Prompt:** Read agent file + `templates/prompt_building.md` (testing_config + skills_config). **Include:** Agent, Group=main, Mode=Simple, Session, Branch, Skills/Testing, Task from PM, **Context Packages (if any)**, **Reasoning Context (if any)**. **Validate:** ✓ Skills, ✓ Workflow, ✓ Testing, ✓ Report format.

**Show Prompt Summary:** Output structured summary (NOT full prompt):
```text
📝 **{agent_type} Prompt** | Group: {group_id} | Model: {model}
...
```

**🔴 Spawn with Specializations:**

Read and follow `templates/orchestrator/spawn_with_specializations.md` with:
- session_id: {session_id}
- group_id: {group_id}
- agent_type: {developer|senior_software_engineer|requirements_engineer}
- model: MODEL_CONFIG[tier]
- base_prompt: [prompt built above]
- task_description: desc
```

#### Change 2: SSE Explicit Escalation (Line 200)

**BEFORE:**
```markdown
- Task(subagent_type="general-purpose", model=MODEL_CONFIG["senior_software_engineer"], description="SeniorEng: explicit escalation", prompt=[senior engineer prompt])
```

**AFTER:**
```markdown
- **🔴 Follow §Spawn Agent with Specializations** (spawn_with_specializations.md) with agent_type="senior_software_engineer", then spawn
```

#### Change 3: Developer Continue Work (Lines 218, 234)

**BEFORE (line 218):**
```markdown
2. Add configuration from `templates/prompt_building.md` (testing_config + skills_config + **specializations**)
```

**AFTER:**
```markdown
2. Add configuration from `templates/prompt_building.md` (testing_config + skills_config)
3. **🔴 Follow §Spawn Agent with Specializations** before spawning
```

**BEFORE (line 234):**
```markdown
Task(subagent_type="general-purpose", model=MODEL_CONFIG["developer"], description="Dev {id}: continue work", prompt=[new prompt])
```

**AFTER:**
```markdown
**🔴 Follow §Spawn Agent with Specializations** with agent_type="developer", base_prompt=[new prompt], task_description="Dev {id}: continue work"
```

#### Change 4: SSE Escalation on Failure (Line 240)

**BEFORE:**
```markdown
- Task(subagent_type="general-purpose", model=MODEL_CONFIG["senior_software_engineer"], description="SeniorEng: escalated task", prompt=[senior engineer prompt])
```

**AFTER:**
```markdown
- **🔴 Follow §Spawn Agent with Specializations** with agent_type="senior_software_engineer", then spawn
```

#### Change 5: QA Expert Spawn (Lines 289-302)

**BEFORE (line 289):**
```markdown
**Build:** 1) Read `agents/qa_expert.md`, 2) Add config from `templates/prompt_building.md` (testing_config.json + skills_config.json qa_expert section + **specializations**), 3) Include: Agent=QA Expert, Group={group_id}, Mode, Session, Skills/Testing source, Context (dev changes), **Specializations (loaded via prompt_building.md)**. **Validate:** ✓ Skills, ✓ Testing workflow, ✓ Framework, ✓ Report format, ✓ Specializations. **Description:** `f"QA {group_id}: tests"`.
```

**AFTER:**
```markdown
**Build Base Prompt:** 1) Read `agents/qa_expert.md`, 2) Add config from `templates/prompt_building.md` (testing_config.json + skills_config.json qa_expert section), 3) Include: Agent=QA Expert, Group={group_id}, Mode, Session, Skills/Testing source, Context (dev changes). **Validate:** ✓ Skills, ✓ Testing workflow, ✓ Framework, ✓ Report format. **Description:** `f"QA {group_id}: tests"`.
```

**BEFORE (line 302):**
```markdown
**Spawn:** `Task(subagent_type="general-purpose", model=MODEL_CONFIG["qa_expert"], description=desc, prompt=[prompt])`
```

**AFTER:**
```markdown
**🔴 Spawn with Specializations:** Follow `spawn_with_specializations.md` with agent_type="qa_expert", base_prompt=[prompt], task_description=desc
```

#### Change 6: Developer Fix QA Issues (Lines 341, 347)

**BEFORE (line 341):**
```markdown
2. Add configuration from `templates/prompt_building.md` (testing_config + skills_config + **specializations**)
```

**AFTER:**
```markdown
2. Add configuration from `templates/prompt_building.md` (testing_config + skills_config)
3. **🔴 Follow §Spawn Agent with Specializations** before spawning
```

**BEFORE (line 347):**
```markdown
Task(subagent_type="general-purpose", model=MODEL_CONFIG["developer"], description="Dev {id}: fix QA issues", prompt=[prompt with QA feedback])
```

**AFTER:**
```markdown
**🔴 Follow §Spawn Agent with Specializations** with agent_type="developer", base_prompt=[prompt with QA feedback], task_description="Dev {id}: fix QA issues"
```

#### Change 7: SSE QA Challenge Escalation (Line 356)

**BEFORE:**
```markdown
- Task(subagent_type="general-purpose", model=MODEL_CONFIG["senior_software_engineer"], description="SeniorEng: QA challenge escalation", prompt=[senior engineer prompt with challenge failures])
```

**AFTER:**
```markdown
- **🔴 Follow §Spawn Agent with Specializations** with agent_type="senior_software_engineer", then spawn
```

#### Change 8: Tech Lead Spawn (Lines 410, 423)

**BEFORE (line 410):**
```markdown
**Build:** 1) Read `agents/techlead.md`, 2) Add config from `templates/prompt_building.md` (testing_config.json + skills_config.json tech_lead section + **specializations**), 3) Include: Agent=Tech Lead, Group={group_id}, Mode, Session, Skills/Testing source, Context (impl+QA summary), **Implementation Reasoning (if any, max 5 entries, 300 chars each)**, **Specializations (loaded via prompt_building.md)**. **Validate:** ✓ Skills, ✓ Review workflow, ✓ Decision format, ✓ Frameworks, ✓ Specializations.
```

**AFTER:**
```markdown
**Build Base Prompt:** 1) Read `agents/techlead.md`, 2) Add config from `templates/prompt_building.md` (testing_config.json + skills_config.json tech_lead section), 3) Include: Agent=Tech Lead, Group={group_id}, Mode, Session, Skills/Testing source, Context (impl+QA summary), **Implementation Reasoning (if any, max 5 entries, 300 chars each)**. **Validate:** ✓ Skills, ✓ Review workflow, ✓ Decision format, ✓ Frameworks.
```

**BEFORE (line 423):**
```markdown
**Spawn:** `Task(subagent_type="general-purpose", model=MODEL_CONFIG["tech_lead"], description=desc, prompt=[prompt])`
```

**AFTER:**
```markdown
**🔴 Spawn with Specializations:** Follow `spawn_with_specializations.md` with agent_type="tech_lead", base_prompt=[prompt], task_description=desc
```

---

### File: `templates/orchestrator/phase_parallel.md`

#### Change 1: Parallel Developer Spawns (Lines 183-209)

**BEFORE (lines 183-184):**
```markdown
**Build PER GROUP:** Read agent file + `templates/prompt_building.md` (testing_config + skills_config + **specializations**). **Include:** Agent, Group=[A/B/C/D], Mode=Parallel, Session, Branch (group branch), Skills/Testing, Task from PM, **Context Packages (if any)**, **Reasoning Context (if any)**, **Specializations (loaded via prompt_building.md)**. **Validate EACH:** ✓ Skills, ✓ Workflow, ✓ Group branch, ✓ Testing, ✓ Report format, ✓ Specializations.
```

**AFTER:**
```markdown
**Build Base Prompt PER GROUP:** Read agent file + `templates/prompt_building.md` (testing_config + skills_config). **Include:** Agent, Group=[A/B/C/D], Mode=Parallel, Session, Branch (group branch), Skills/Testing, Task from PM, **Context Packages (if any)**, **Reasoning Context (if any)**. **Validate EACH:** ✓ Skills, ✓ Workflow, ✓ Group branch, ✓ Testing, ✓ Report format.
```

**BEFORE (lines 200-209):**
```markdown
**Spawn ALL in ONE message (MAX 4 groups):**
```
Task(subagent_type="general-purpose", model=models["A"], description="Dev A: {task[:90]}", prompt=[Group A prompt])
Task(subagent_type="general-purpose", model=models["B"], description="SSE B: {task[:90]}", prompt=[Group B prompt])
... # MAX 4 Task() calls in ONE message
```

**🔴 CRITICAL:** Always include `subagent_type="general-purpose"` - without it, agents spawn with 0 tool uses.

**🔴 DO NOT spawn in separate messages** (sequential). **🔴 DO NOT spawn >4** (breaks system).
```

**AFTER:**
```markdown
**🔴 Spawn ALL with Specializations (MAX 4 groups) - SEQUENTIAL PER AGENT:**

Per §Spawn Agent with Specializations **Parallel Mode: Isolation Rule**:

```
# Group A:
1. Follow spawn_with_specializations.md Steps 1-4 for Group A
   (output context → Skill → extract block)
2. Task(subagent_type="general-purpose", model=models["A"], description="Dev A: {task[:90]}", prompt=[Group A prompt WITH specialization])

# Group B:
3. Follow spawn_with_specializations.md Steps 1-4 for Group B
   (output context → Skill → extract block)
4. Task(subagent_type="general-purpose", model=models["B"], description="SSE B: {task[:90]}", prompt=[Group B prompt WITH specialization])

# ... repeat for Groups C, D (MAX 4)
```

**⚠️ ISOLATION RULE:** Complete context→skill→spawn for each agent BEFORE starting the next. Do NOT interleave contexts.

**🔴 CRITICAL:** Always include `subagent_type="general-purpose"` - without it, agents spawn with 0 tool uses.

**🔴 DO NOT spawn >4** (breaks system).
```

---

### File: `agents/orchestrator_speckit.md`

#### Change 1: PM Spawn with Spec-Kit Context (Lines 120-150)

The spec-kit orchestrator spawns PM differently (with spec-kit artifacts). Specializations should still be loaded.

**AFTER Step 5 (Spawn PM), add:**

```markdown
### Step 5b: Spawn Developers with Specializations (After PM Planning)

When PM returns with task groups, spawn developers using the centralized spawn procedure:

**🔴 For each developer spawn:**
1. Read `templates/orchestrator/spawn_with_specializations.md`
2. Follow Steps 1-7 with appropriate parameters
3. Ensure specializations from task_group are loaded
```

---

## Phase 3: Spec-Kit Orchestrator - DETAILED SPEC

The spec-kit orchestrator at `agents/orchestrator_speckit.md` is a separate entry point. It needs to reference the centralized spawn template.

**Add section after line 402:**

```markdown
## Specialization Loading for Spec-Kit Tasks

When spawning any agent (Developer, SSE, QA, Tech Lead), follow the centralized spawn procedure:

**🔴 Required:** Read and follow `templates/orchestrator/spawn_with_specializations.md` before every agent spawn.

This ensures spec-kit tasks get the same technology-specific patterns as regular orchestration.
```

---

## Impact Analysis Summary

### Token Impact

| File | Before | After | Change |
|------|--------|-------|--------|
| `agents/project_manager.md` | ~23,556 tokens | ~20,500 tokens | **-3,056 tokens** |
| `templates/orchestrator/phase_simple.md` | ~4,200 tokens | ~4,400 tokens | +200 tokens |
| `templates/orchestrator/phase_parallel.md` | ~1,800 tokens | ~2,000 tokens | +200 tokens |
| `spawn_with_specializations.md` (NEW) | 0 | ~1,200 tokens | +1,200 tokens |
| **NET CHANGE** | - | - | **-1,456 tokens** |

### Behavior Changes

| Scenario | Before | After |
|----------|--------|-------|
| Developer spawn | No specialization block | Specialization block prepended |
| SSE spawn | No specialization block | Specialization block prepended |
| QA spawn | No specialization block | Specialization block prepended |
| Tech Lead spawn | No specialization block | Specialization block prepended |
| PM doesn't assign specializations | Nothing happens | Orchestrator derives fallback |
| Parallel mode (4 agents) | All spawn with base prompt | Each gets own specialization |
| specializations.enabled=false | Nothing happens | Skip gracefully |
| skill invocation fails | N/A | Skip gracefully, log warning |

### Risk Matrix

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| PM truncation (token limit) | MEDIUM → LOW | HIGH | -3,056 tokens reduces risk |
| Breaking existing flow | LOW | HIGH | All changes additive, skill errors non-blocking |
| Parallel context collision | HIGH → LOW | HIGH | Isolation rule prevents |
| Wrong specializations loaded | LOW | MEDIUM | DB query + fallback derivation |
| Skill returns malformed output | LOW | LOW | Graceful fallback to base prompt |
| orchestrator_speckit drift | MEDIUM | MEDIUM | Explicit documentation added |

---

## Testing Checklist

### Unit Tests

- [ ] Orchestrator loads skills_config.json correctly
- [ ] Orchestrator queries task_group.specializations from DB
- [ ] Orchestrator invokes specialization-loader skill
- [ ] Orchestrator extracts block between markers
- [ ] Orchestrator prepends block to base_prompt
- [ ] Fallback derivation works when specializations empty
- [ ] Parallel mode isolation rule followed

### Integration Tests

- [ ] Simple mode: Developer spawn includes specialization block
- [ ] Simple mode: QA spawn includes specialization block
- [ ] Simple mode: Tech Lead spawn includes specialization block
- [ ] Parallel mode: 4 agents each get correct specialization
- [ ] Escalation: SSE gets specialization after Developer fails
- [ ] Spec-kit: Developers get specialization

### Edge Cases

- [ ] skills_config.json missing → graceful skip
- [ ] specializations.enabled = false → graceful skip
- [ ] task_group.specializations = null → fallback derivation
- [ ] project_context.json missing → graceful skip
- [ ] specialization-loader returns empty → graceful skip
- [ ] specialization-loader times out → graceful skip

---

## References

- `agents/orchestrator.md` §Specialization Loading (lines 1222-1330)
- `templates/prompt_building.md` (lines 88-191)
- `templates/orchestrator/phase_simple.md`
- `templates/orchestrator/phase_parallel.md`
- `.claude/skills/specialization-loader/SKILL.md`
- `research/orchestrator-specialization-integration-ultrathink-2025-12-04.md`
- `tmp/ultrathink-reviews/combined-review.md` (OpenAI GPT-5 review)
