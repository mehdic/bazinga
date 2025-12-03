# PM Spec-Kit Integration Mode

**This file is loaded by the Project Manager when orchestrator signals SPEC-KIT INTEGRATION MODE.**

---

## Activation Trigger

If the orchestrator mentions "SPEC-KIT INTEGRATION MODE" or provides a feature directory path containing spec-kit artifacts.

## What is Spec-Kit Integration?

Spec-Kit (GitHub's spec-driven development toolkit) provides a structured planning workflow:
1. `/speckit.specify` - Creates feature specifications (spec.md)
2. `/speckit.plan` - Generates technical plans (plan.md)
3. `/speckit.tasks` - Breaks down into tasks (tasks.md with checklist format)

When integrated with BAZINGA, you leverage these pre-planned artifacts instead of creating your own analysis from scratch.

## Key Differences in Spec-Kit Mode

| Standard Mode | Spec-Kit Mode |
|---------------|---------------|
| You analyze requirements | Spec.md provides requirements |
| You create task breakdown | Tasks.md provides task breakdown |
| You plan architecture | Plan.md provides architecture |
| Free-form grouping | Group by spec-kit task markers |

## How to Detect Spec-Kit Mode

Orchestrator will:
1. Explicitly state "SPEC-KIT INTEGRATION MODE ACTIVE"
2. Provide feature directory path (e.g., `.specify/features/001-jwt-auth/`)
3. Include file paths for spec.md, tasks.md, plan.md
4. Include parsed summary of tasks with IDs and markers

## Modified Workflow in Spec-Kit Mode

**Step 0: Detect and Answer Investigation Questions (SAME AS STANDARD MODE)**

Even in Spec-Kit mode, if user asks investigation questions, answer them FIRST using the same process:
- Check for investigation question patterns (see Standard Mode Phase 1, Step 1)
- Apply same safeguards, timeout, and output constraints
- Include "Investigation Answers" section before Spec-Kit analysis
- Then continue with Spec-Kit workflow below

**Phase 1: Read Spec-Kit Artifacts** (instead of analyzing requirements)

```
Step 1: Read Feature Documents

feature_dir = [provided by orchestrator, e.g., ".specify/features/001-jwt-auth/"]

spec_content = read_file(f"{feature_dir}/spec.md")
tasks_content = read_file(f"{feature_dir}/tasks.md")
plan_content = read_file(f"{feature_dir}/plan.md")

# Optional but recommended:
if exists(f"{feature_dir}/research.md"):
    research_content = read_file(f"{feature_dir}/research.md")

if exists(f"{feature_dir}/data-model.md"):
    data_model = read_file(f"{feature_dir}/data-model.md")
```

**Phase 2: Parse tasks.md Format**

Spec-kit tasks.md uses this format:
```
- [ ] [TaskID] [Markers] Description (file.py)

Where:
- TaskID: T001, T002, etc. (unique identifier)
- Markers: [P] = can run in parallel
           [US1], [US2] = user story groupings
           Both: [P] [US1] = parallel task in story 1
- Description: What needs to be done
- (file.py): Target file/module
```

**Examples**:
```
- [ ] [T001] [P] Setup: Create auth module structure (auth/__init__.py)
- [ ] [T002] [P] [US1] JWT token generation (auth/jwt.py)
- [ ] [T003] [P] [US1] Token validation (auth/jwt.py)
- [ ] [T004] [US2] Login endpoint (api/login.py)
- [ ] [T005] [US2] Logout endpoint (api/logout.py)
```

**Phase 3: Group Tasks by User Story and Parallelism**

**Grouping Strategy**:

1. **Primary grouping: User Story markers**
   ```
   Tasks with [US1] → Group "US1"
   Tasks with [US2] → Group "US2"
   Tasks with [US3] → Group "US3"
   Tasks without [US] → Group by phase (Setup/Core/Polish)
   ```

2. **Parallel detection: [P] markers**
   ```
   Group with ALL tasks marked [P] → Can run in parallel
   Group with some tasks marked [P] → Sequential within group, but group can be parallel
   Group with no [P] markers → Sequential
   ```

3. **Dependency detection: Analyze file overlap**
   ```
   If Group US2 uses files from Group US1 → Sequential dependency
   If groups use completely different files → Can run in parallel
   ```

**Example Parsing**:

```
Input tasks.md:
- [ ] [T001] [P] Setup: Create auth module (auth/__init__.py)
- [ ] [T002] [P] [US1] JWT generation (auth/jwt.py)
- [ ] [T003] [P] [US1] Token validation (auth/jwt.py)
- [ ] [T004] [US2] Login endpoint (api/login.py)
- [ ] [T005] [US2] Logout endpoint (api/logout.py)
- [ ] [T006] [US2] Unit tests for endpoints (tests/test_api.py)
- [ ] [T007] [US3] Token refresh endpoint (api/refresh.py)

Your Task Groups:
{
  "SETUP": {
    "task_ids": ["T001"],
    "description": "Create auth module structure",
    "files": ["auth/__init__.py"],
    "parallel_eligible": true,
    "dependencies": []
  },
  "US1": {
    "task_ids": ["T002", "T003"],
    "description": "JWT token generation and validation",
    "files": ["auth/jwt.py"],
    "parallel_eligible": true,
    "dependencies": []
  },
  "US2": {
    "task_ids": ["T004", "T005", "T006"],
    "description": "Login/logout endpoints with tests",
    "files": ["api/login.py", "api/logout.py", "tests/test_api.py"],
    "parallel_eligible": false,
    "dependencies": ["US1"]  // Uses JWT from US1
  },
  "US3": {
    "task_ids": ["T007"],
    "description": "Token refresh endpoint",
    "files": ["api/refresh.py"],
    "parallel_eligible": false,
    "dependencies": ["US1"]  // Uses JWT from US1
  }
}
```

**Phase 4: Decide Execution Mode**

```
Analysis:
- Independent groups (no dependencies): SETUP, US1 → Can run in parallel
- Dependent groups: US2, US3 depend on US1 → Must wait for US1

Decision: PARALLEL MODE

Execution Plan:
- Phase 1: SETUP + US1 (2 developers in parallel)
- Phase 2: US2 + US3 (after US1 complete, could be parallel if no file overlap)

Recommended parallelism: 2 developers for phase 1
```

**Phase 4.5: Generate Project Context (NEW)**

After analyzing requirements and before creating task groups, generate project context to help developers understand the codebase. This context will be saved and reused across all developers.

**Check Existing Context:**
```bash
If file exists: bazinga/project_context.json
  AND created within last hour
  AND session_id matches current session
  → Reuse existing context
Else
  → Generate new context
```

**Session ID Verification:**
```python
import json
from datetime import datetime, timedelta

# Read existing context
with open('bazinga/project_context.json') as f:
    existing_context = json.load(f)

# Check conditions
# Note: Replace 'Z' with '+00:00' for Python 3.10 compatibility
generated_at = existing_context.get('generated_at', '1970-01-01T00:00:00+00:00').replace('Z', '+00:00')
file_age = datetime.now() - datetime.fromisoformat(generated_at)
session_matches = existing_context.get('session_id') == current_session_id
is_recent = file_age < timedelta(hours=1)

if session_matches and is_recent:
    # Reuse existing context
    context = existing_context
else:
    # Generate new context (session mismatch or stale)
    context = generate_new_context()
```

**Generate Project Context:**
```json
{
  "project_type": "Detected project type (REST API, CLI tool, library, microservice)",
  "primary_language": "Python/JavaScript/Go/Java (detected)",
  "framework": "Flask/Express/Django/Spring (if applicable)",
  "architecture_patterns": [
    "Service layer pattern (services/)",
    "Repository pattern (repositories/)",
    "MVC pattern (models/views/controllers/)"
  ],
  "conventions": {
    "error_handling": "How errors are typically handled",
    "authentication": "Auth approach if present",
    "validation": "Input validation approach",
    "testing": "Test framework and patterns used"
  },
  "key_directories": {
    "services": "Business logic location (e.g., services/)",
    "models": "Data models location (e.g., models/)",
    "utilities": "Shared utilities location (e.g., utils/)",
    "tests": "Test files location (e.g., tests/)"
  },
  "common_utilities": [
    {
      "name": "EmailService",
      "location": "utils/email.py",
      "purpose": "Handles email sending"
    },
    {
      "name": "TokenGenerator",
      "location": "utils/tokens.py",
      "purpose": "JWT token generation"
    }
  ],
  "test_framework": "pytest/jest/go test",
  "coverage_target": "80%",
  "generated_at": "2025-11-18T10:00:00Z",
  "session_id": "[current session_id]"
}
```

**Save Context (DB + File):**

1. **Primary: Save to Database**
```
bazinga-db, save state
  session_id: {current_session_id}
  state_type: project_context
  state_data: {context_json}
```

2. **Cache: Write to File**
Write to `bazinga/project_context.json` (overwrites template). Developers read this for fast access. DB stores history for analysis.

**VALIDATION (MANDATORY):**

After generating and saving project_context.json, verify it was created successfully:

```bash
# Step 1: Verify file exists
if [ ! -f "bazinga/project_context.json" ]; then
    echo "ERROR: Failed to create project_context.json"
    # Create minimal fallback context
fi

# Step 2: Verify JSON is valid
python3 -c "import json; json.load(open('bazinga/project_context.json'))" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "ERROR: Invalid JSON in project_context.json"
    # Create minimal fallback context
fi

# Step 3: Verify required fields
python3 -c "
import json
ctx = json.load(open('bazinga/project_context.json'))
required = ['project_type', 'primary_language', 'session_id', 'generated_at']
missing = [f for f in required if f not in ctx]
if missing:
    print(f'ERROR: Missing required fields: {missing}')
    exit(1)
" 2>/dev/null
```

**Fallback Context (if validation fails):**

If context generation or validation fails, create this minimal fallback:

```json
{
  "project_type": "unknown",
  "primary_language": "detected from file extensions",
  "framework": "none detected",
  "architecture_patterns": [],
  "conventions": {},
  "key_directories": {},
  "common_utilities": [],
  "test_framework": "none detected",
  "coverage_target": "unknown",
  "generated_at": "[current timestamp]",
  "session_id": "[current session_id]",
  "fallback": true,
  "fallback_reason": "Context generation failed - using minimal fallback"
}
```

**Error Logging:**

If context generation fails, log to `bazinga/pm_errors.log`:
```
[timestamp] ERROR: Project context generation failed
[timestamp] REASON: [error description]
[timestamp] ACTION: Created fallback context
[timestamp] IMPACT: Developers may have reduced code awareness
```

**Continue on Fallback:**
Even if context generation fails, CONTINUE with task planning. The fallback context ensures developers can still work, just with less guidance.

**Enhance Task Group Descriptions:**

When creating task groups, include relevant file hints:

Original task description:
```
Group A: User Authentication
- Implement login endpoint
- Add JWT token generation
```

Enhanced with file hints:
```
Group A: User Authentication
- Implement login endpoint
- Add JWT token generation

Relevant files to reference:
- Existing auth patterns: /auth/basic_auth.py
- User model: /models/user.py
- JWT utility: /utils/token.py (if exists)
- Similar endpoint: /api/register.py
- Error handling: /utils/responses.py

Key patterns to follow:
- Use service layer pattern (see /services/user_service.py)
- Follow error_response() pattern from /utils/responses.py
- Use validators from /utils/validators.py
```

**Phase 5: Save Your PM State with Spec-Kit Context to Database**

**Request to bazinga-db skill:**
```
bazinga-db, please save the PM state:

Session ID: [session_id from orchestrator]
State Type: pm
State Data: {
  "session_id": "[session_id]",
  "mode": "parallel",
  "spec_kit_mode": true,
  "feature_dir": ".specify/features/001-jwt-auth/",
  "task_groups": {
    "SETUP": {
      "group_id": "SETUP",
      "task_ids": ["T001"],
      "description": "Create auth module structure",
      "files": ["auth/__init__.py"],
      "spec_kit_tasks": [
        "- [ ] [T001] [P] Setup: Create auth module (auth/__init__.py)"
      ],
      "parallel": true,
      "dependencies": [],
      "status": "pending"
    },
    "US1": {
      "group_id": "US1",
      "task_ids": ["T002", "T003"],
      "description": "JWT token generation and validation",
      "files": ["auth/jwt.py"],
      "spec_kit_tasks": [
        "- [ ] [T002] [P] [US1] JWT generation (auth/jwt.py)",
        "- [ ] [T003] [P] [US1] Token validation (auth/jwt.py)"
      ],
      "parallel": true,
      "dependencies": [],
      "status": "pending"
    }
  },
  "execution_plan": {
    "phase_1": ["SETUP", "US1"],
    "phase_2": ["US2", "US3"]
  },
  "spec_artifacts": {
    "spec_md": ".specify/features/001-jwt-auth/spec.md",
    "tasks_md": ".specify/features/001-jwt-auth/tasks.md",
    "plan_md": ".specify/features/001-jwt-auth/plan.md"
  },
  "completed_groups": [],
  "current_phase": 1,
  "iteration": 1
}
```

**Then invoke the skill:**
```
Skill(command: "bazinga-db")
```

**IMPORTANT:** You MUST invoke bazinga-db skill here. Use the returned data. Simply do not echo the skill response text in your message to user.


Additionally, create task groups in the database:

**For each task group, request:**
```
bazinga-db, please create task group:

Group ID: SETUP
Session ID: [session_id]
Name: Create auth module structure
Status: pending
```

**Then invoke:**
```
Skill(command: "bazinga-db")
```

**IMPORTANT:** You MUST invoke bazinga-db skill here. Use the returned data. Simply do not echo the skill response text in your message to user.


Repeat for each task group (SETUP, US1, US2, etc.).

**Phase 6: Return Your Decision**

Format your response for the orchestrator:

```markdown
## PM Decision: PARALLEL MODE (Spec-Kit Integration)

### Spec-Kit Artifacts Analyzed
- spec.md: JWT Authentication System
- tasks.md: 7 tasks identified (T001-T007)
- plan.md: Using PyJWT, bcrypt, PostgreSQL

### Task Group Mapping

**From tasks.md task IDs to BAZINGA groups:**
[Show mapping of task IDs to your created groups]

### Developer Context in Spec-Kit Mode

When spawning developers through orchestrator, include this context:
```
**SPEC-KIT MODE ACTIVE**
**Task IDs:** [T002, T003]
**Task Descriptions:** [paste relevant lines from tasks.md]
**Read Context:** {feature_dir}/spec.md (requirements), plan.md (technical approach)
**Implementation:** Follow spec.md requirements and plan.md architecture
**Update Progress:** Mark tasks complete in tasks.md: - [ ] [T002] -> - [x] [T002]
**Report:** Completion with task IDs when done
```

### Progress Tracking in Spec-Kit Mode

**Dual tracking required:**
1. **Developers mark tasks.md:** Change `- [ ] [T002]` to `- [x] [T002]` when complete
2. **You update pm_state.json:** Move task IDs to completed_task_ids, update status
3. **Group completion criteria:** All task IDs for group have [x] marks in tasks.md

**Verification steps:**
- Read tasks.md after each developer completion
- Count completed [x] marks vs total tasks
- Update pm_state.json to reflect actual progress

### BAZINGA Condition in Spec-Kit Mode

**Additional requirements beyond standard mode:**
1. ALL task groups complete in pm_state.json (standard requirement)
2. ALL tasks in tasks.md have [x] checkmarks (spec-kit specific)
3. Tech Lead approved all groups (standard requirement)

**Verification before BAZINGA:**
```bash
# Read tasks.md
# Count completed tasks (anchor to task ID pattern):
completed=$(grep -E '^\- \[x\] \[T[0-9]+\]' tasks.md | wc -l)
total=$(grep -E '^\- \[[x ]\] \[T[0-9]+\]' tasks.md | wc -l)
# Verify: completed matches total
# Only then: Send BAZINGA
```

**CRITICAL:** Do NOT send BAZINGA if any tasks in tasks.md still show `- [ ]`

### Quick Reference: Standard vs Spec-Kit

| Aspect | Standard Mode | Spec-Kit Mode |
|--------|---------------|---------------|
| **Progress** | pm_state.json only | pm_state.json + tasks.md [x] marks |
| **Completion** | All groups complete | All groups + verify all [x] in tasks.md |
| **Dev Context** | PM requirements | spec.md + plan.md + task IDs |
| **Tracking** | Group status | Group status + individual task [x] |
