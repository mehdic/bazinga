# PM Spawn Workflow

**This file contains the detailed PM spawn and response handling workflow.**
**Read by orchestrator at Phase 1 (Spawn Project Manager).**

---

## MANDATORY FIRST ACTION

Before ANY analysis, save your understanding of this request:

1. Create session-specific understanding file:
   ```bash
   # Ensure artifacts directory exists
   mkdir -p bazinga/artifacts/{session_id}

   cat > bazinga/artifacts/{session_id}/pm_understanding.md << 'UNDERSTANDING_EOF'
   ## PM Understanding Phase

   ### Raw Request Summary
   {Summarize the user's request in 2-3 sentences}

   ### Scope Assessment
   - Type: {file|feature|bug|refactor|research}
   - Complexity: {low|medium|high}
   - Estimated task groups: {1-N}

   ### Key Requirements
   - {Requirement 1}
   - {Requirement 2}
   ...

   ### Initial Constraints
   - {Any constraints identified}
   UNDERSTANDING_EOF
   ```

2. Save to database:
   ```
   Skill(command: "bazinga-db-agents") → save-reasoning {session_id} global project_manager understanding --content-file bazinga/artifacts/{session_id}/pm_understanding.md --confidence high
   ```

**Do NOT proceed with planning until understanding is saved.**
```

**Spawn:**
```
Task(
  subagent_type: "general-purpose",
  description: "PM analyzing requirements and deciding execution mode",
  prompt: [Full PM prompt from agents/project_manager.md with session_id context AND mandatory understanding capture above],
  run_in_background: false
)
```

PM returns decision with:
- Mode chosen (SIMPLE/PARALLEL)
- Task groups created
- Execution plan
- Next action for orchestrator

---

## Step 1.3: Receive PM Decision

**Step 1: Check for Investigation Answers (PRIORITY)**

Check if PM response contains investigation section. Look for these headers (fuzzy match):
- "## Investigation Answers"
- "## Investigation Results"
- "## Answers"
- "## Findings"
- "## Investigation"
- Case-insensitive matching

**IF investigation section found:**
- Extract question(s) and answer(s) from the section
- Handle multiple questions (see multi-question logic below)
- Output investigation capsule BEFORE planning capsule:
  ```
  📊 Investigation results | {findings_summary} | Details: {details}
  ```
- Example: `📊 Investigation results | Found 83 E2E tests in 5 files | 30 passing, 53 skipped`
- **Log investigation to database:**
  ```
  bazinga-db-agents, please log this investigation:
  Session ID: [session_id]
  Investigation Type: pre_orchestration_qa
  Questions: [extracted questions]
  Answers: [extracted answers]
  ```
  Then invoke: `Skill(command: "bazinga-db-agents")`
- Then continue to parse planning sections

**Multi-question capsules:** 1Q: summary+details, 2Q: both summaries, 3+Q: "Answered N questions"

**No investigation:** Skip to Step 2. **Parse fails:** Log warning, continue.

**Step 2: Parse PM response and output capsule to user**

Use the PM Response Parsing section from `bazinga/templates/response_parsing.md` (loaded at initialization) to extract:
- **Status** (PLANNING_COMPLETE, BAZINGA, CONTINUE, NEEDS_CLARIFICATION, INVESTIGATION_ONLY, INVESTIGATION_NEEDED)
- **Mode** (SIMPLE, PARALLEL)
- **Task groups** (if mode decision)
- **Assessment** (if continue/bazinga)

**Step 3: Construct and output plan summary to user**

IF status = INVESTIGATION_ONLY:
  → Display final investigation capsule (already shown)
  → Update session status to 'completed'
  → EXIT (no development)

IF status = PLANNING_COMPLETE (PM's first response with multi-phase/complex plan):
  → Use **Execution Plan Ready** format:
  ```markdown
  📋 **Execution Plan Ready**
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  **Mode:** {mode} ({N} concurrent developers)
  **Tasks:** {task_count} across {phase_count} phases

  **Phases:**
  > Phase 1: {phase_name} - Groups {group_ids}
  > Phase 2: {phase_name} - Groups {group_ids}

  **Success Criteria:**
  • {criterion_1}
  • {criterion_2}

  **Starting:** Phase 1 with Groups {ids}
  ```

  **Data sources:** Extract from PM response - mode, task_groups array, success_criteria array, execution_phases.
  **Fallback:** If phases not explicit, list all groups as single phase.

IF status = PLANNING_COMPLETE (simple single-group):
  → Use compact capsule:
  ```
  📋 Planning complete | Single-group: {task_summary} | Starting development
  ```

IF status = NEEDS_CLARIFICATION:
  → Use clarification template (§Step 1.3a)
  → SKIP planning capsule

IF status = BAZINGA or CONTINUE:
  → Use appropriate template

IF status = INVESTIGATION_NEEDED:
  → Use "Investigation Needed" template:
  ```
  🔬 Investigation needed | {problem_summary} | Spawning Investigator
  ```
  → Immediately spawn Investigator (see §Step 2A.6b for investigation loop)

**Apply fallbacks:** If data missing, scan for "parallel", "simple", group names.

**Step 4: Log PM interaction** — Use §Logging Reference pattern. Agent ID: `pm_main`.

**AFTER logging PM response: IMMEDIATELY continue to Step 1.3a (Handle PM Clarification Requests). Do NOT stop.**

**🔴 LAYER 2 SELF-CHECK (PM RESPONSE):**

Before continuing to Step 1.3a, verify:
1. ✅ Did I invoke `Skill(command: "bazinga-db-agents")` to log PM interaction?
2. ✅ Did I output a capsule to the user showing PM's analysis?
3. ✅ Am I about to continue to Step 1.3a (not ending my message)?

**IF ANY IS NO:** Complete it NOW before proceeding. This is MANDATORY.

---

## Step 1.3a: Handle PM Status and Route Accordingly

**Detection:** Check PM Status code from response

**Expected status codes from PM spawn (initial or resume):**
- `PLANNING_COMPLETE` - PM completed planning, proceed to execution
- `CONTINUE` - PM verified state and work should continue (common in RESUME scenarios)
- `BAZINGA` - PM declares completion (rare in initial spawn, common in resume/final assessment)
- `NEEDS_CLARIFICATION` - PM needs user input before planning
- `INVESTIGATION_ONLY` - Investigation-only request; no implementation needed

**🔴 INTENT WITHOUT ACTION:** If you write "spawn" → call `Skill(command: "prompt-builder")` + `Task()` NOW.

---

**IF status = PLANNING_COMPLETE:**
- PM has completed planning (created mode decision and task groups)
- **IMMEDIATELY jump to Step 1.4 (Verify PM State and Task Groups). Do NOT stop.**

**IF status = CONTINUE (CRITICAL FOR RESUME SCENARIOS):**
- PM verified state and determined work should continue
- **🔴 DO NOT STOP FOR USER INPUT** - keep making tool calls until agents are spawned
- **Step 1:** Query task groups: `Skill(command: "bazinga-db-workflow")` → get all task groups for session
- **Step 2:** Find groups with status: `in_progress` or `pending`
- **Step 3:** Read the appropriate phase template (`phase_simple.md` or `phase_parallel.md`)
- **Step 4:** Spawn appropriate agent using prompt-builder:
  - Call `Skill(command: "prompt-builder")` with agent parameters
  - Then call `Task()` with the built prompt
  - **⚠️ CAPACITY LIMIT: Respect MAX 4 PARALLEL DEVELOPERS hard limit**
  - If more than 4 groups need spawning, spawn first 4 and queue/defer remainder
- **🔴 You MUST call SOME tool in THIS turn**. Do NOT just say "let me spawn"

**Clarification:** Multi-step tool sequences (DB query → prompt-builder → spawn) within the same assistant turn are expected. The rule is: **complete all steps before your turn ends** - never stop to wait for user input between receiving PM CONTINUE and spawning agents.

**IF status = NEEDS_CLARIFICATION:** Execute clarification workflow below

**IF status = INVESTIGATION_ONLY:**
- PM only answered questions (no implementation requested)
- Display PM's investigation findings to user
- **END orchestration** (no development work needed)

**IF status = BAZINGA:**
- All work complete (if PM returns this early, likely a resume of already-complete session)
- **MANDATORY: Invoke `Skill(command: "bazinga-validator")` to verify completion**
  - IF validator returns ACCEPT → Proceed to completion
  - IF validator returns REJECT → **Execute [Validator REJECT Handling Procedure](#mandatory-validator-reject-handling-procedure)** (do NOT stop!)
- **IMMEDIATELY proceed to Completion phase ONLY after validator ACCEPTS**

**IF status is missing or unclear:**
- **DO NOT GUESS** - Status codes must be explicit in PM response
- Scan for EXPLICIT status markers only:
  - Explicit "Status: CONTINUE" or "CONTINUE" on its own line → treat as CONTINUE
  - Explicit "Status: PLANNING_COMPLETE" or "PLANNING_COMPLETE" → treat as PLANNING_COMPLETE
  - Explicit "Status: NEEDS_CLARIFICATION" or question blocks → treat as NEEDS_CLARIFICATION
- **Generic phrases like "proceed", "continue with", "Phase N" are NOT status codes**
- If truly ambiguous: Output `⚠️ PM status unclear | Cannot determine next action | Respawning PM for explicit status`
- Then respawn PM with: "Your previous response lacked an explicit status code. Please respond with one of: PLANNING_COMPLETE, CONTINUE, BAZINGA, NEEDS_CLARIFICATION"
- **IMMEDIATELY jump to appropriate phase after status determined. Do NOT stop.**

**🔴 ANTI-PATTERN - INTENT WITHOUT ACTION:**
❌ **WRONG:** "Database updated. Now let me spawn the SSE..." [STOPS - turn ends without any tool call]
✅ **CORRECT:** "Database updated. Building prompt." [Skill(command: "prompt-builder")] → then [Task() with built prompt]

Saying "let me spawn" or "I will spawn" is NOT spawning. You MUST call Skill(command: "prompt-builder") followed by Task() in the same turn.

---

## Clarification Workflow (NEEDS_CLARIFICATION)

**🔴 MANDATORY: Read full clarification protocol (includes hard cap enforcement):**
```
Read(file_path: "bazinga/templates/orchestrator/clarification_flow.md")
```

**Step 1: Log** via §Logging Reference (type: `pm_clarification`, status: `pending`)
**Step 2: Update orchestrator state** via bazinga-db (`clarification_used: true`, `clarification_resolved: false`)
**Step 3: Surface Clarification to User**

**User output (capsule format):**
```
⚠️ PM needs clarification | {blocker_type}: {question_summary} | Awaiting response (auto-proceed with fallback in 5 min)

[Display PM's full NEEDS_CLARIFICATION section, including:]
- Blocker Type
- Evidence of Exhaustion
- Question
- Options
- Safe Fallback
```

**Step 4: Wait for User Response**

- Set 5-minute timeout
- User can respond with their choice (option a, b, or c)
- Or specify custom answer

**Step 5: Process Response**

**If user responds within 5 minutes:**

Process internally (no verbose routing messages needed).

Log user response:
```
bazinga-db-core, please update clarification request:

Session ID: [current session_id]
Status: resolved
User Response: [user's answer]
Resolved At: [ISO timestamp]
```

**Then invoke:**
```
Skill(command: "bazinga-db-core")
```

**If timeout (5 minutes, no response):**

```
⏱️ Clarification timeout | No response after 5min | Proceeding with PM's safe fallback option
```

Log timeout:
```
bazinga-db-core, please update clarification request:

Session ID: [current session_id]
Status: timeout
User Response: timeout_assumed
Resolved At: [ISO timestamp]
```

**Then invoke:**
```
Skill(command: "bazinga-db-core")
```

**Step 6: Re-spawn PM with Answer**

Process internally (no verbose status message needed - PM will proceed with planning).

**Spawn PM again with:**

```
Task(
  subagent_type="general-purpose",
  description="PM planning with clarification",
  prompt=f"""
You are the Project Manager. You previously requested clarification and received this response:

**Your Clarification Request:**
[PM's original NEEDS_CLARIFICATION section]

**User Response:**
[user's answer OR "timeout - proceed with your safe fallback option"]

**Your Task:**
- Document this clarification in assumptions_made array
- Proceed with planning based on the clarified requirements
- Continue your normal planning workflow
- Return your PM Decision (mode, task groups, execution plan)

**Context:**
{user_requirements}

**Session Info:**
- Session ID: {session_id}
- Previous PM state: [if any]
""",
  run_in_background: false
)
```

**Step 7: Receive PM Decision (Again)**

- PM should now return normal decision (SIMPLE MODE or PARALLEL MODE)
- Log this interaction to database (same as Step 1.3)
- Update orchestrator state to mark clarification resolved:

```
bazinga-db-core, please update orchestrator state:

Session ID: [current session_id]
State Data: {
  "clarification_used": true,
  "clarification_resolved": true,
  "phase": "planning_complete"
}
```

**Then invoke:**
```
Skill(command: "bazinga-db-core")
```

**Step 8: Continue to Step 1.4**

- Proceed with normal workflow (verify PM state and task groups)
- PM should have completed planning with clarification resolved

---

## Step 1.4: Verify PM State and Task Groups in Database

**⚠️ CRITICAL VERIFICATION: Ensure PM saved state and task groups**

The PM agent should have saved PM state and created task groups in the database. Verify this now:

### 🔴 OPTIONAL: Check PM Handoff File (Non-Blocking)

**Check if PM created handoff file:**
```bash
test -f "bazinga/artifacts/{SESSION_ID}/handoff_project_manager.json" && echo "exists" || echo "missing"
```

**IF handoff file is MISSING:**
- **DO NOT block workflow** - This is common (PM may not have reached Write step)
- **Log warning:** `⚠️ PM handoff file missing | Using CRP response + database state`
- **Continue with database verification below** - DB state is the authoritative source

**IF handoff file EXISTS:**
- Good - PM completed full workflow including Write step
- Continue with database verification below

**Query task groups:**
```
bazinga-db-workflow, please get all task groups for session [current session_id]
```

**Then invoke:**
```
Skill(command: "bazinga-db-workflow")
```

**Check the response and validate:**
- If task groups returned with N > 0: ✅ Proceed to Step 1.5
- If task groups empty OR no records: ⚠️ Proceed to Step 1.4b (fallback)
- If parallel mode AND N > 4: ⚠️ Enforce MAX 4 limit (see §HARD LIMIT above) — defer groups 5+ to next phase

### Step 1.4b: Fallback - Create Task Groups from PM Response

**If PM did not create task groups in database, you must create them now:**

Parse the PM's response to extract task group information. Look for sections like:
- "Task Groups Created"
- "Group [ID]: [Name]"
- Task group IDs (like SETUP, US1, US2, etc.)

For each task group found, invoke bazinga-db-workflow:

```
bazinga-db-workflow, please create task group:

Group ID: [extracted group_id]
Session ID: [current session_id]
Name: [extracted group name]
Status: pending
```

**Then invoke:**
```
Skill(command: "bazinga-db-workflow")
```

Repeat for each task group found in the PM's response.

Process internally (creating task groups from PM response - no user output needed for database sync).

Use the PM response format examples from `bazinga/templates/message_templates.md` (loaded at initialization).

---

## Step 1.5: Route Based on Mode

**UI Message:**
```
IF PM chose "simple":
    Output (capsule format): "📋 Planning complete | Single-group execution: {task_summary} | Starting development"
    → Go to Phase 2A

ELSE IF PM chose "parallel":
    Output (capsule format): "📋 Planning complete | {N} parallel groups: {group_summaries} | Starting development → Groups {list}"
    → Go to Phase 2B
```
