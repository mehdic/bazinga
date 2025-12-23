# PM Planning Steps Reference

**This file is referenced by the Project Manager agent. Do not modify without updating the PM agent.**

---

## Step 0: Development Plan Management (FIRST ACTION)

**Query current session's plan:**

Invoke skill: `Skill(command: "bazinga-db")`

Provide request:
```
bazinga-db, please get the development plan:

Session ID: {session_id}
```

**Handle response:**

**IF plan found → CONTINUATION MODE:**
- Parse: original_prompt, phases[], current_phase, metadata
- Map user request to phases (e.g., "Phase 2" → phases[1])
- Output: `📋 Plan: {total}-phase | Phase 1✓ Phase 2→ Phase 3⏸`
- Jump to Step 1 with plan context

**IF no plan found → CHECK FOR ORPHANED PLANS:**

User request contains phase references ("Phase", "phase", "Step")? If yes:

*New sessions may lose plan context. Search recent sessions:*

Invoke: `Skill(command: "bazinga-db")`
```
bazinga-db, please list the most recent sessions (limit 5).
```

For each recent session (last 24h), query its plan. If plan found with matching phase names:
- Show user: `📋 Found plan from {prev_session} | Continue it? (assuming yes)`
- Load plan, update session_id to current
- Continue in CONTINUATION MODE

**IF still no plan → PLAN CREATION MODE:**

Detect plan type:
1. **User-provided plan:** Explicit "Phase 1:", "Step 1:", numbered items + scope keywords ("only", "for now", "start with")
2. **PM-generated plan:** Complex work (will need >2 task groups) → break into phases

**Save plan:**

Invoke: `Skill(command: "bazinga-db")`
```
bazinga-db, please save this development plan:

Session ID: {session_id}
Original Prompt: {user's exact message, escape quotes}
Plan Text: Phase 1: JWT auth
Phase 2: User registration
Phase 3: Email verification
Phases: [{"phase":1,"name":"JWT auth","status":"pending","description":"Implement JWT tokens","requested_now":true},...]
Current Phase: 1
Total Phases: 3
Metadata: {"plan_type":"user_provided_partial","scope_requested":"Phase 1 only"}
```

**JSON Construction:**
- Use compact JSON (no newlines inside array)
- Escape quotes in descriptions
- Required fields: phase (int), name, status, description, requested_now (bool)
- Keep descriptions short (<50 chars)

**Error Handling:**
- IF bazinga-db fails → Log warning, continue without persistence
- IF JSON construction fails → Skip plan save, proceed as simple orchestration

Output: `📋 Plan: {total}-phase detected | Phase 1→ Others⏸`

---

## Step 0.9: Backfill Missing Fields (ON RESUME)

**When PM is spawned with existing task groups:**

1. **Query existing task groups:**
   ```
   bazinga-db, get task groups for session [session_id]
   ```

2. **Check each group for missing fields:**
   ```
   FOR each task_group:
     needs_specializations = task_group.specializations is null OR empty
     needs_item_count = task_group.item_count is null OR 0
     needs_complexity = task_group.complexity is null
   ```

3. **Backfill missing fields:**
   - **Specializations:** Read `bazinga/project_context.json`, derive using mapping table in task classification reference.
   - **Complexity:** Derive from initial_tier:
     - If initial_tier = "Senior Software Engineer" → set complexity = 4 (minimum SSE threshold)
     - If initial_tier = "Developer" → set complexity = 2 (default low)
     - Log: `📋 Backfilled complexity={N} based on initial_tier`

4. **Update with ONLY missing fields** (don't overwrite good values)

5. **Log:** `📋 Backfilled {N} task groups: {fields_updated}`

**Skip if:** This is a NEW session (no existing task groups).

---

## Step 3.5: Assign Specializations (MANDATORY - BLOCKER)

**Purpose:** Provide technology-specific patterns to agents.

**THIS STEP BLOCKS PROCEEDING** - You MUST assign specializations to EVERY task group.

### Step 3.5.1: Read Project Context

```
Read(file_path: "bazinga/project_context.json")
```

**If file exists:** Extract from `components[].suggested_specializations`
**If file MISSING:** Derive using fallback mapping table (see pm_task_classification.md)

### Step 3.5.2: Map Task Groups to Components

```
FOR each task_group:
  specializations = []
  target_paths = extract file paths from task description
  matched_component_path = null  # Track matched component for version lookup

  FOR each component in project_context.components:
    IF target_path starts with component.path:
      # Longest prefix match - prefer "backend/api/" over "backend/"
      IF matched_component_path is null OR len(component.path) > len(matched_component_path):
        matched_component_path = component.path
      specializations.extend(component.suggested_specializations)

  # Store matched component path for version context in prompt builder
  task_group.component_path = matched_component_path
  # Deduplicate preserving order
  task_group.specializations = list(dict.fromkeys(specializations))
```

**Why component_path matters:** The prompt builder uses this to look up language/framework versions from `project_context.json`, enabling version-specific guidance (e.g., Python 3.11 patterns, not 2.7).

### Step 3.5.3: Include in Task Group Definition

```markdown
**Group A:** Implement Login UI
- **Type:** implementation
- **Complexity:** 5 (MEDIUM)
- **Initial Tier:** Developer
- **Target Path:** frontend/src/pages/login.tsx
- **Component Path:** frontend/
- **Specializations:** ["bazinga/templates/specializations/01-languages/typescript.md", ...]
```

**Component Path:** The monorepo component this task group belongs to (for version lookup).

### Step 3.5.4: Store via bazinga-db (CANONICAL TEMPLATE)

```
bazinga-db, please create task group:

Group ID: A
Session ID: [session_id]
Name: Implement Login UI
Status: pending
--complexity 5
--initial_tier "Developer"
--item_count [number of tasks]
--component-path 'frontend/'
--specializations '["path/to/template1.md", "path/to/template2.md"]'
```

**Required fields:**
- `--complexity` - Task complexity score (1-10). 1-3=Low (Developer), 4-6=Medium (SSE), 7-10=High (SSE)
- `--initial_tier` - Starting agent tier (`"Developer"` or `"Senior Software Engineer"`)
- `--item_count` - Number of discrete tasks (for progress tracking)
- `--component-path` - Monorepo component path for version lookup (use `./` for simple projects)
- `--specializations` - Technology paths (NEVER empty)

**VALIDATION GATE:**
```
IMMEDIATE SELF-CHECK after creating each task group:
1. Does it include --complexity (1-10)?
2. Does it include --initial_tier?
3. Does it include --item_count?
4. Does it include --component-path?
5. Does it include --specializations with non-empty array?
6. TIER-COMPLEXITY CONSISTENCY (BIDIRECTIONAL):
   a. If complexity >= 4 → initial_tier MUST be "Senior Software Engineer"
   b. If complexity <= 3 → initial_tier MUST be "Developer"
   c. If mismatch → FIX the initial_tier to match complexity score

IF any missing OR consistency violated → IMMEDIATELY invoke bazinga-db update-task-group
```

**Policy reminder (STRICT MAPPING):**
| Complexity | Required Tier |
|------------|---------------|
| 1-3 | Developer |
| 4-6 | Senior Software Engineer |
| 7-10 | Senior Software Engineer |

**The complexity score DETERMINES the tier. Do not override.**

**DO NOT proceed to Step 5 until ALL task groups have complexity, initial_tier, item_count, component_path, and non-empty specializations.**

---

## Step 5: Save PM State to Database

### Sub-step 5.1: Get Initial Branch

Query session for initial_branch (set by orchestrator at init):
```
bazinga-db, get session [session_id] with initial_branch
```

**DO NOT run git commands** - PM tool constraints forbid git.

### Sub-step 5.2: Save PM State

```
bazinga-db, please save the PM state:

Session ID: [session_id]
State Type: pm
State Data: {
  "session_id": "[session_id]",
  "initial_branch": "[from session data]",
  "mode": "simple" or "parallel",
  "mode_reasoning": "Explanation",
  "original_requirements": "Full user requirements",
  "success_criteria": [...],
  "investigation_findings": "[summary or null]",
  "parallel_count": [number],
  "all_tasks": [...],
  "task_groups": [...],
  "execution_phases": [...],
  "completed_groups": [],
  "in_progress_groups": [],
  "pending_groups": [...],
  "iteration": 1,
  "last_update": "[ISO timestamp]",
  "completion_percentage": 0,
  "assumptions_made": [...]
}
```

Then invoke: `Skill(command: "bazinga-db")`

### Sub-step 5.3: Verify Task Groups Were Persisted

**DO NOT CREATE TASK GROUPS HERE.** Task groups are created in Step 3.5.4.

This step is VERIFICATION ONLY:
1. All task groups were created in Step 3.5.4
2. Each group has ALL required fields (Item_Count, --specializations)

**If any missing:** Go back to Step 3.5.4 and create/update them.

### Verification Checkpoint

Before proceeding:
- ✅ Captured initial branch
- ✅ Invoked bazinga-db to save PM state
- ✅ Created task groups in Step 3.5.4 (N times)
- ✅ Each group has Item_Count AND --specializations
- ✅ Each invocation returned success

---

## Step 6: Return Decision

**Use exact structure for orchestrator parsing:**

```markdown
## PM Decision: [SIMPLE MODE / PARALLEL MODE]

### Analysis
- Features identified: N
- File overlap: [LOW/MEDIUM/HIGH]
- Dependencies: [description]
- Recommended parallelism: N developers

### Reasoning
[Explain why you chose this mode]

### Task Groups Created

**Group [ID]: [Name]**
- Tasks: [list]
- Files: [list]
- Estimated effort: N minutes
- Can parallel: [YES/NO]
- **Complexity:** [1-10]
- **Initial Tier:** [Developer | Senior Software Engineer]
- **Tier Rationale:** [Why this tier]
- **Item_Count:** [N]

[Repeat for each group]

### Execution Plan

[SIMPLE MODE]:
Execute single task group sequentially through dev → QA → tech lead pipeline.

[PARALLEL MODE]:
Execute N groups in parallel (N = [parallel_count]):
- Phase 1: Groups [list] (parallel)
- Phase 2: Groups [list] (if any, depends on phase 1)

### Next Action
Orchestrator should spawn [N] developer(s) for group(s): [IDs]

**Branch Information:**
- Initial branch: [from initial_branch field]
```

---

## Initial Tier Assignment Rules

| Complexity | Initial Tier | Rationale |
|------------|--------------|-----------|
| 1-3 (Low) | Developer (Dev tier) | Standard tasks, cost-efficient |
| 4-6 (Medium) | Senior Software Engineer | Medium complexity benefits from SSE |
| 7-10 (High) | Senior Software Engineer | Complex, skip Dev tier to save time |

**Override rules (regardless of complexity):**
- Security-sensitive code → **Senior Software Engineer**
- Architectural decisions → **Senior Software Engineer**
- Bug fix with clear symptoms → **Developer** (even if complexity 7+)
- Integration with external systems → **Senior Software Engineer**
- Performance-critical paths → **Senior Software Engineer**

**NOTE:** You decide the tier, NOT the model. Orchestrator loads model assignments from database.
