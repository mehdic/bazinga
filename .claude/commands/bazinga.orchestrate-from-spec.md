---
description: Execute spec-kit tasks using BAZINGA multi-agent orchestration with full integration
---

# BAZINGA + Spec-Kit Integration Command

This command bridges spec-kit's planning phase with BAZINGA's execution phase, creating a seamless spec-driven development workflow.

**🆕 Enhanced Reporting**: Upon completion, you will receive:
- **Concise summary** showing quality metrics, efficiency, and any issues requiring attention
- **Detailed report** saved to `bazinga/artifacts/{SESSION_ID}/completion_report.md` with comprehensive analysis
- Links to Skills results (security-scan, test-coverage, lint-check) and token usage

## User Input

```text
$ARGUMENTS
```

**Argument Parsing**:
1. Parse feature directory path (if provided)
2. If no path → Auto-detect latest feature
3. Uses Skills configured in bazinga/skills_config.json

**Examples**:
- `/orchestrate-from-spec` → Auto-detect feature, use configured Skills
- `/orchestrate-from-spec .specify/features/001-auth` → Specific feature, use configured Skills

---

## Overview

**Integration Flow**:
```
spec-kit (planning) → /orchestrate-from-spec → BAZINGA (execution)
```

This command:
1. ✅ Loads spec-kit artifacts (spec.md, tasks.md, plan.md)
2. ✅ Validates they exist and are complete
3. ✅ Spawns BAZINGA orchestrator with spec-kit context
4. ✅ PM reads and parses spec-kit task breakdown
5. ✅ Developers implement following spec-kit structure
6. ✅ Updates tasks.md with completion checkmarks

---

## Phase 1: Validate and Load Spec-Kit Artifacts

### Step 1.0: Determine Feature Directory

**Parse Arguments for Feature Path**:
```
FEATURE_PATH = ""

# Parse feature path from arguments
FEATURE_PATH = $ARGUMENTS.strip()
```

**Output**:
```
📂 **FEATURE PATH**: {FEATURE_DIR}
```

**Priority Order**:
1. If FEATURE_PATH is not empty → Use it
2. Check for `.specify/features/` directory
3. If multiple features → Use latest (highest number)
4. If no features found → Show error and suggest workflow

**Error Handling**:
```
If no spec-kit features found:
"❌ No spec-kit features found. Please run the planning workflow first:
   1. /speckit.constitution (if first time)
   2. /speckit.specify <description>
   3. /speckit.plan
   4. /speckit.tasks
   Then run /orchestrate-from-spec again."
```

### Step 1.1: Validate Required Files

**Check for Required Files**:
```bash
FEATURE_DIR=.specify/features/XXX-feature-name

Required:
✅ $FEATURE_DIR/spec.md       (Feature specification - REQUIRED)
✅ $FEATURE_DIR/tasks.md      (Task breakdown - REQUIRED)

Recommended:
⚠️  $FEATURE_DIR/plan.md      (Technical plan - highly recommended)
ℹ️  $FEATURE_DIR/research.md  (Research notes - optional)
ℹ️  $FEATURE_DIR/data-model.md (Data structures - optional)
ℹ️  $FEATURE_DIR/contracts/   (API contracts - optional)
```

**Validation Output**:
```
🔍 **SPEC-KIT INTEGRATION**: Loading artifacts from .specify/features/001-auth-feature/

✅ spec.md found (1,234 bytes)
✅ tasks.md found (2,456 bytes)
✅ plan.md found (1,890 bytes)
ℹ️  research.md found (1,120 bytes)
ℹ️  data-model.md found (890 bytes)

📋 Artifacts loaded successfully. Proceeding with orchestration...
```

**If Missing Critical Files**:
```
❌ Missing required files:
   - spec.md: NOT FOUND
   - tasks.md: FOUND ✅

Cannot proceed. Please run:
   /speckit.tasks

Then retry /orchestrate-from-spec
```

### Step 1.2: Parse and Display Summary

**Read and Parse**:
1. `spec.md` - Extract feature title and key requirements
2. `tasks.md` - Count total tasks, identify parallel markers, story groupings
3. `plan.md` - Extract technical approach summary

**Display Summary**:
```
═══════════════════════════════════════════════════════
🎯 SPEC-KIT + BAZINGA ORCHESTRATION
═══════════════════════════════════════════════════════

**Feature**: JWT Authentication System
**Location**: .specify/features/001-jwt-auth/

**Specification Summary** (from spec.md):
- User authentication with JWT tokens
- Secure token generation and validation
- Refresh token support
- Role-based access control

**Technical Approach** (from plan.md):
- Libraries: PyJWT, bcrypt
- Database: Add users table with password_hash
- API: /login, /logout, /refresh, /verify endpoints
- Middleware: JWT validation decorator

**Task Breakdown** (from tasks.md):
- Total tasks: 12
- Parallel tasks: 6 (marked with [P])
- User stories: 3 (US1, US2, US3)
- Estimated complexity: Medium-High

**Next**: Spawning BAZINGA orchestrator to execute tasks...

═══════════════════════════════════════════════════════
```

---

## Phase 2: Spawn BAZINGA Orchestrator with Spec-Kit Context

### Step 2.1: Prepare Enhanced Orchestrator Prompt

**Key Enhancement**: Inject spec-kit context into orchestrator's initial state

```
You are now the **ORCHESTRATOR** for the Claude Code Multi-Agent Dev Team.

🆕 **SPEC-KIT INTEGRATION MODE ACTIVE**
✅ **Skills Mode**: Advanced Skills enabled per bazinga/skills_config.json

You are executing a feature that has been planned using GitHub's spec-kit methodology. All planning artifacts have been prepared, and your job is to coordinate implementation.

═══════════════════════════════════════════════════════
📂 SPEC-KIT ARTIFACTS LOADED
═══════════════════════════════════════════════════════

**Feature Directory**: {FEATURE_DIR}

**Available Artifacts**:
✅ spec.md - Feature requirements and acceptance criteria
✅ tasks.md - Pre-defined task breakdown with checklist format
✅ plan.md - Technical architecture and approach
✅ research.md - Research findings and unknowns resolved (if available)
✅ data-model.md - Data structures and schemas (if available)
✅ contracts/ - API contracts and interfaces (if available)

**User Stories Identified** (from tasks.md):
List of [US1], [US2], [US3] with descriptions

**Parallel Execution Opportunities** (from tasks.md):
List of tasks marked with [P]

═══════════════════════════════════════════════════════

## 🎯 MODIFIED ORCHESTRATION WORKFLOW

Your standard workflow applies, but with these SPEC-KIT specific modifications:

### Modified Instructions for PROJECT MANAGER

**🔴 CRITICAL CHANGE**: Do NOT create your own task breakdown.

**Available Tools:**
- `/velocity-tracker` Skill for measuring velocity, cycle time, and detecting 99% rule violations

**Your Modified Workflow**:

1. **Read Spec-Kit Artifacts** (Step 1):
   ```
   spec_content = read_file("{FEATURE_DIR}/spec.md")
   tasks_content = read_file("{FEATURE_DIR}/tasks.md")
   plan_content = read_file("{FEATURE_DIR}/plan.md")
   ```

2. **Parse tasks.md Format** (Step 2):

   Spec-kit uses this format:
   ```
   - [ ] [TaskID] [Markers] Description (file.py)

   Where:
   - TaskID: T001, T002, etc. (unique identifier)
   - Markers: [P] = parallel, [US1] = user story 1
   - Description: What needs to be done
   - (file.py): Target file/module
   ```

3. **Group Tasks by User Story** (Step 3):

   **Grouping Strategy**:
   ```
   Group by [US] marker:
   - Tasks with [US1] → Group "US1"
   - Tasks with [US2] → Group "US2"
   - Tasks without [US] → Group by phase (Setup/Core/Polish)

   Parallel Detection:
   - Groups with ALL tasks marked [P] → Can run in parallel
   - Groups with mixed or no [P] → Sequential
   ```

4. **Decide Execution Mode** (Step 4):

   Based on parallel groups:
   ```
   IF 2+ groups can run in parallel:
     → PARALLEL MODE
   ELSE:
     → SIMPLE MODE
   ```

5. **Create BAZINGA Groups from Spec-Kit Tasks** (Step 5):

   **Example Mapping**:
   ```
   tasks.md:
   - [ ] [T001] [P] Setup: Create auth module structure (auth/__init__.py)
   - [ ] [T002] [P] [US1] JWT token generation (auth/jwt.py)
   - [ ] [T003] [P] [US1] Token validation (auth/jwt.py)
   - [ ] [T004] [US2] Login endpoint (api/login.py)
   - [ ] [T005] [US2] Logout endpoint (api/logout.py)
   - [ ] [T006] [US3] Token refresh endpoint (api/refresh.py)

   BAZINGA Groups:
   Group SETUP: [T001] - Can parallel: YES
   Group US1: [T002, T003] - Can parallel: YES (both marked [P])
   Group US2: [T004, T005] - Can parallel: NO (sequential, may depend on US1)
   Group US3: [T006] - Can parallel: NO (depends on US1)

   Execution Plan:
   Phase 1: SETUP, US1 (2 developers in parallel)
   Phase 2: US2, US3 (1-2 developers based on file overlap check)
   ```

6. **Update pm_state.json** (Step 6):

   Include in state:
   ```json
   {
     "mode": "parallel",
     "spec_kit_integration": true,
     "feature_dir": "{FEATURE_DIR}",
     "task_groups": {
       "SETUP": {
         "task_ids": ["T001"],
         "files": ["auth/__init__.py"],
         "parallel": true
       },
       "US1": {
         "task_ids": ["T002", "T003"],
         "files": ["auth/jwt.py"],
         "parallel": true
       }
     }
   }
   ```

### Modified Instructions for DEVELOPERS

**🔴 CRITICAL ADDITIONS**: Use spec-kit artifacts for context and update tasks.md.

**Skills Available** (if marked as 'mandatory' in bazinga/skills_config.json):
- **/codebase-analysis** - Find similar features and reusable utilities (10-20s)
- **/test-pattern-analysis** - Learn testing patterns before writing tests (5-15s)
- **/api-contract-validation** - Validate API changes don't break contracts (5-15s)
- **/db-migration-check** - Check migration safety before applying (5-20s)

IMPORTANT: Use Skills when available to:
- Discover existing utilities (EmailService, TokenGenerator, etc.)
- Follow established patterns
- Avoid breaking changes
- Write tests consistent with project style

**Your Modified Workflow**:

1. **Read Your Assigned Tasks** (Before Implementation):
   ```
   # PM assigns you task IDs, e.g., ["T002", "T003"]

   tasks_content = read_file("{FEATURE_DIR}/tasks.md")

   # Parse out YOUR tasks:
   - [ ] [T002] [P] [US1] JWT token generation (auth/jwt.py)
   - [ ] [T003] [P] [US1] Token validation (auth/jwt.py)
   ```

2. **Read Context Documents** (Required):
   ```
   spec = read_file("{FEATURE_DIR}/spec.md")
   plan = read_file("{FEATURE_DIR}/plan.md")

   # Optional but recommended:
   if exists("{FEATURE_DIR}/data-model.md"):
     data_model = read_file("{FEATURE_DIR}/data-model.md")

   if exists("{FEATURE_DIR}/research.md"):
     research = read_file("{FEATURE_DIR}/research.md")
   ```

3. **Implement Following Spec-Kit Methodology**:

   **TDD Approach** (if tests mentioned in tasks.md):
   ```
   For each task:
   a. Write test first (if task says "write tests")
   b. Implement to pass test
   c. Refactor
   d. Move to next task
   ```

   **File Organization** (from plan.md):
   - Follow architecture specified in plan.md
   - Use libraries/dependencies from plan.md
   - Follow patterns established in plan.md

4. **Update tasks.md as You Complete Tasks** (REQUIRED):

   **After completing each task**:
   ```
   Use Edit tool to mark task complete:

   Old:
   - [ ] [T002] [P] [US1] JWT token generation (auth/jwt.py)

   New:
   - [x] [T002] [P] [US1] JWT token generation (auth/jwt.py)
   ```

   **This provides real-time progress tracking!**

5. **Report Format** (Enhanced):

   Include in your status report:
   ```
   ## Implementation Complete - Group {group_id}

   **Spec-Kit Tasks Completed**:
   - [x] T002: JWT token generation
   - [x] T003: Token validation

   **Files Modified**:
   - auth/jwt.py (created)
   - tests/test_jwt.py (created)

   **Spec.md Requirements Met**:
   - ✅ Secure token generation using HS256
   - ✅ Token expiration (1 hour access, 7 days refresh)
   - ✅ Validation with signature verification

   **Plan.md Approach Followed**:
   - ✅ Used PyJWT library as specified
   - ✅ Implemented token payload structure from plan

   **tasks.md Updated**: YES (marked T002, T003 as complete)

   **Status**: READY_FOR_QA
   ```

### Modified Instructions for QA EXPERT

**Standard workflow**, but additionally:

1. **Verify tasks.md alignment**:
   - Check that implemented features match task descriptions
   - Validate test coverage matches task requirements

2. **Cross-reference with spec.md**:
   - Ensure acceptance criteria from spec.md are met
   - Validate edge cases mentioned in spec

### Modified Instructions for TECH LEAD

**🆕 AUTOMATIC SKILLS INTEGRATION**: The orchestrator will automatically inject Claude Code Skills into Tech Lead reviews.

**Skills Used** (automatically invoked):
- **security-scan**: Scans for vulnerabilities (basic mode → advanced mode at revision 2+)
- **test-coverage**: Generates coverage reports
- **lint-check**: Checks code quality and style

**Progressive Analysis Strategy**:

| Revision Count | Security Scan Mode | Tech Lead Model | Trigger |
|----------------|-------------------|-----------------|---------|
| **0-1 revisions** | Basic (5-10s, high/medium severity) | Sonnet 4.5 | First review |
| **2 revisions** | Advanced (30-60s, all severities) | Sonnet 4.5 | After first changes requested |
| **3+ revisions** | Advanced (comprehensive) | Opus | Persistent issues detected |

**Standard workflow**, but additionally:

1. **Validate spec-kit compliance**:
   - Code follows architecture in plan.md
   - Uses libraries/patterns from plan.md
   - Meets quality standards from constitution.md (if exists)

2. **Check tasks.md accuracy**:
   - Verify marked tasks are actually complete
   - Ensure implementation matches task descriptions

3. **Review automated Skill results**:
   - Security scan findings from bazinga/security_scan.json
   - Coverage report from bazinga/coverage_report.json
   - Lint results from bazinga/lint_results.json

---

## 🚀 BEGIN ORCHESTRATION

Now proceed with your standard orchestration workflow:

1. **Initialize**: Run initialization script if first time
2. **Spawn PM**: PM reads spec-kit artifacts and creates groups
3. **Execute**: Run Simple or Parallel mode based on PM decision
4. **Route**: Follow standard routing (Dev → QA → Tech Lead → PM)
5. **Complete**: PM sends BAZINGA when all tasks in tasks.md are checked

**Remember**:
- PM does NOT create tasks (reads from tasks.md)
- Developers UPDATE tasks.md with checkmarks
- All agents REFERENCE spec.md and plan.md for context
- tasks.md serves as single source of truth for progress
- 🆕 **Tech Lead automatically uses Claude Code Skills** for security, coverage, and linting
- 🆕 **Progressive analysis**: basic → advanced scan at revision 2, Opus model at revision 3
- 🆕 **Revision tracking**: bazinga/group_status.json tracks per-group revision counts

═══════════════════════════════════════════════════════
🎯 START ORCHESTRATION NOW
═══════════════════════════════════════════════════════
```

### Step 2.2: Spawn Orchestrator Agent

Use the Task tool to spawn the orchestrator:

```
Task(
  subagent_type: "general-purpose",
  description: "BAZINGA orchestration executing spec-kit tasks",
  prompt: [Full enhanced prompt from above with actual file paths]
)
```

---

## Phase 3: Monitor and Support

### Step 3.1: Monitor Progress

While orchestration runs, you can monitor progress by invoking the bazinga-db skill:

**To check orchestration logs:**

Request to bazinga-db skill:
```
bazinga-db, please stream recent logs for session {session_id}.
Show me the last 20 log entries.
```

Then invoke:
```
Skill(command: "bazinga-db")
```

**To check PM state:**

Request to bazinga-db skill:
```
bazinga-db, please get the PM state for session {session_id}.
I need to see the current status and task groups.
```

Then invoke:
```
Skill(command: "bazinga-db")
```

**Note:** All orchestration data is stored in bazinga/bazinga.db. Use the bazinga-db skill to query it instead of direct bash commands.

### Step 3.2: Handle Completion

When orchestrator returns with BAZINGA from PM:

```
═══════════════════════════════════════════════════════
✅ SPEC-KIT + BAZINGA ORCHESTRATION COMPLETE
═══════════════════════════════════════════════════════

**Feature**: {Feature Name}
**Status**: COMPLETE ✅

**Tasks Completed**: {X}/{Y} tasks in tasks.md marked complete

**Suggested Next Steps**:

1. **Validate Consistency**:
   /speckit.analyze

   This checks consistency between spec.md, plan.md, tasks.md, and implementation.

2. **Review Checklists** (if exists):
   Review {FEATURE_DIR}/checklists/*.md
   Ensure all quality gates are satisfied.

3. **Manual Testing**:
   Follow quickstart.md or test plan from spec.

4. **Create Pull Request**:
   All work has been committed to appropriate branches.
   Review commits and create PR when ready.

═══════════════════════════════════════════════════════
```

---

## Troubleshooting

### Issue: Tasks.md not getting updated with checkmarks

**Cause**: Developers not using Edit tool to update tasks.md

**Solution**: Orchestrator should remind developers in next iteration

### Issue: PM creating its own tasks instead of using tasks.md

**Cause**: PM prompt not emphasizing spec-kit mode

**Solution**: Check that FEATURE_DIR is correctly passed to PM

### Issue: Developers not following plan.md

**Cause**: Developers not reading plan.md

**Solution**: Tech Lead should flag in review, send back to developer

### Issue: Orchestration starts but spec-kit files not found

**Cause**: Incorrect FEATURE_DIR path

**Solution**: Verify path and rerun with correct argument:
```
/orchestrate-from-spec .specify/features/001-feature-name
```

---

## Integration Benefits

✅ **Structured Planning**: Spec-kit's rigorous planning phase
✅ **Parallel Execution**: BAZINGA's adaptive parallelism
✅ **Progress Tracking**: Real-time updates to tasks.md
✅ **Quality Gates**: Both systems' quality checks apply
✅ **Audit Trail**: Complete log in orchestration-log.md
✅ **Traceability**: Task IDs link planning to execution

---

## Example Usage

**Complete Workflow**:

```bash
# Step 1: Constitution (first time only)
/speckit.constitution

# Step 2: Specify feature
/speckit.specify Add user authentication with JWT tokens

# Step 3: Generate technical plan
/speckit.plan

# Step 4: Break down into tasks
/speckit.tasks

# Step 5: Execute with BAZINGA (THIS COMMAND)
/orchestrate-from-spec

# Step 6: Validate consistency (after completion)
/speckit.analyze
```

**Result**: Feature fully implemented with complete traceability from spec to code.

---

## Notes

- This command requires both BAZINGA and spec-kit to be installed
- Spec-kit artifacts must be created before running this command
- tasks.md serves as shared state between spec-kit and BAZINGA
- All standard BAZINGA features work (parallel mode, role drift prevention, etc.)
- All standard spec-kit features work (analyze, checklist validation, etc.)

---

**Created**: 2025-11-07
**Version**: 1.0.0
**Integration**: BAZINGA v1.0 + Spec-Kit compatible
