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

**Fallback Mapping Table:**

| Technology | Template Path |
|------------|---------------|
| typescript, ts | `bazinga/templates/specializations/01-languages/typescript.md` |
| javascript, js | `bazinga/templates/specializations/01-languages/javascript.md` |
| python, py | `bazinga/templates/specializations/01-languages/python.md` |
| java | `bazinga/templates/specializations/01-languages/java.md` |
| go, golang | `bazinga/templates/specializations/01-languages/go.md` |
| rust | `bazinga/templates/specializations/01-languages/rust.md` |
| react | `bazinga/templates/specializations/02-frameworks-frontend/react.md` |
| nextjs, next.js | `bazinga/templates/specializations/02-frameworks-frontend/nextjs.md` |
| vue | `bazinga/templates/specializations/02-frameworks-frontend/vue.md` |
| angular | `bazinga/templates/specializations/02-frameworks-frontend/angular.md` |
| express | `bazinga/templates/specializations/03-frameworks-backend/express.md` |
| fastapi | `bazinga/templates/specializations/03-frameworks-backend/fastapi.md` |
| django | `bazinga/templates/specializations/03-frameworks-backend/django.md` |
| springboot, spring | `bazinga/templates/specializations/03-frameworks-backend/spring-boot.md` |
| postgresql, postgres | `bazinga/templates/specializations/05-databases/postgresql.md` |
| mongodb, mongo | `bazinga/templates/specializations/05-databases/mongodb.md` |
| kubernetes, k8s | `bazinga/templates/specializations/06-infrastructure/kubernetes.md` |
| docker | `bazinga/templates/specializations/06-infrastructure/docker.md` |
| jest, vitest | `bazinga/templates/specializations/08-testing/jest-vitest.md` |
| playwright, cypress | `bazinga/templates/specializations/08-testing/playwright-cypress.md` |

### Step 4: Invoke Specialization Loader Skill

**⚠️ STRICT ADJACENCY RULE:** NO output between context blob and Skill() call.

```
IF len(specializations) > 0:

    # ⚠️ TWO SEPARATE ACTIONS - skill reads context from conversation
    # CRITICAL: Do NOT output anything else between these two actions

    # Action 4a: Output context as TEXT (not tool call)
    OUTPUT:
        Session ID: {session_id}
        Group ID: {group_id}
        Agent Type: {agent_type}
        Model: {model}
        Specialization Paths: {json.dumps(specializations)}

    # Action 4b: IMMEDIATELY invoke the skill (no other output in between)
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
