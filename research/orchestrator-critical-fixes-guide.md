# Orchestrator Critical Fixes Guide

## Status: PARTIALLY IMPLEMENTED

Optional skills support has been implemented in orchestrator. Remaining fixes address the WHILE loop architecture issue and missing workflows for the investigation system.

## Fixes Completed ✅

1. **Skills Configuration** (bazinga/skills_config.json)
   - Added "optional" status for framework-driven skills
   - Changed all previously disabled skills to "optional" by default (lite profile)
   - All 10 advanced skills are now optional and available when needed
   - Users can still disable specific skills if desired

2. **Init Script** (scripts/init-orchestration.sh)
   - Updated to match new skills config format
   - Added "optional" status documentation

3. **Tech Lead Language** (agents/techlead.md)
   - Changed all "spawn" to "request" (Tech Lead cannot spawn, only request)
   - Updated Investigation Request Format to include hypothesis matrix
   - Fixed decision tree terminology

4. **Investigator Validation** (agents/investigator.md)
   - Added hypothesis matrix validation in STEP 1
   - Handles empty, null, or malformed hypothesis matrices
   - Returns BLOCKED if cannot proceed

5. **Orchestrator Optional Skills Support** (agents/orchestrator.md) - ✅ IMPLEMENTED
   - Updated Developer prompt building (Step 2A.2) to check for "optional" status
   - Updated QA Expert prompt building (Step 2A.4) to check for "optional" status
   - Updated Tech Lead prompt building (Step 2A.6) to check for "optional" status
   - **Updated Investigator prompt building (Step 2A.6b) to check for "optional" status** ✅ NEW
   - Added "3b. For EACH optional skill" sections after mandatory skills
   - Optional skills are injected with clear "OPTIONAL SKILLS AVAILABLE" header
   - Tech Lead optional skills include framework guidance (when to use which skill)
   - Skills configuration now supports 3 states: mandatory, optional, disabled

**Implementation Details:**
- Developer optional skills: Available when workflow requires them
- QA Expert optional skills: Available when analysis requires them
- Tech Lead optional skills: Available in specific frameworks
  - codebase-analysis: Frameworks 1, 2, 3 (Root Cause, Architectural Decisions, Performance)
  - pattern-miner: Frameworks 1, 3 (Root Cause, Performance - historical patterns)
  - test-pattern-analysis: Framework 4 (Flaky Test Analysis)
- **Investigator optional skills**: Available during investigation loops ✅ NEW
  - codebase-analysis: MANDATORY (always injected)
  - pattern-miner: MANDATORY (always injected)
  - test-pattern-analysis: OPTIONAL (test-related investigations)
  - security-scan: OPTIONAL (security-related hypotheses)

**How It Works:**
1. Orchestrator reads skills_config.json during initialization
2. For each agent spawn, checks skills with `status = "mandatory"` and `status = "optional"`
3. Mandatory skills: Injected with "USE THESE SKILLS - They are MANDATORY!"
4. Optional skills: Injected with "These are OPTIONAL - invoke only when [condition]"
5. Agent receives both sets in prompt, knows which are mandatory and which are optional
6. **Investigator receives skills dynamically from config (not from Tech Lead's suggested_skills)** ✅ NEW

## Fixes Needed in Orchestrator 🚧

### Fix #1: Remove WHILE Loop (CRITICAL)

**Problem:** Lines 1314-1627 use a WHILE loop which is impossible in agent architecture

**Current Code:**
```markdown
### Step 2A.6b: Investigation Loop Management (NEW - CRITICAL)

**IF Tech Lead reports: INVESTIGATION_IN_PROGRESS**

**WHILE investigation_state.status == "in_progress" AND investigation_state.current_iteration < investigation_state.max_iterations:**
  [Process investigation iteration]
```

**Required Fix:**
```markdown
### Step 2A.6b: Investigation Iteration (ONE Per Turn)

**IF Tech Lead reports: INVESTIGATION_IN_PROGRESS**

**IMPORTANT:** Orchestrator processes ONE investigation iteration per turn, then terminates.
The investigation continues across multiple orchestrator invocations.

#### Check for Existing Investigation

**Query database for existing investigation:**
```
bazinga-db, please query investigation states WHERE group_id = [current_group_id] AND status = 'in_progress'
```

**IF investigation already exists:**
  - RESUME existing investigation (don't create duplicate)
  - Load investigation_state from database
  - Increment current_iteration
  - Continue from where it left off

**IF no investigation exists:**
  - Initialize new investigation_state:
    ```yaml
    investigation_state:
      group_id: [current_group_id]
      session_id: [current_session_id]
      branch: [developer's_feature_branch]
      current_iteration: 0
      max_iterations: 5
      status: "in_progress"
      problem_summary: [from Tech Lead]
      hypothesis_matrix: [from Tech Lead]
      suggested_skills: [from Tech Lead]
      iterations_log: []
      developer_results: null
    ```
  - Save to database

#### Process ONE Iteration

**Increment iteration:**
```
investigation_state.current_iteration += 1
```

**IF current_iteration > max_iterations:**
  - investigation_state.status = "max_iterations_reached"
  - Save state to database
  - Spawn Tech Lead with investigation findings (partial/incomplete)
  - EXIT investigation
  - RETURN (end orchestrator turn)

**Spawn Investigator for this iteration:**
[... existing spawn logic ...]

**After Investigator responds:**
[... existing routing logic ...]

**Save updated investigation_state to database**

**TERMINATE orchestrator turn** (investigation will continue on next turn if status still "in_progress")
```

---

### Fix #2: Add Step 0 - Active Investigation Detection

**Location:** Before Step 1 (around line 250)

**Add New Section:**
```markdown
## Step 0: Check for Active Investigations (BEFORE Step 1)

**⚠️ CRITICAL: Check this BEFORE normal workflow**

**Query database for active investigations:**
```
bazinga-db, please query investigation states WHERE status = 'in_progress'
```

**IF active investigation found:**
  - Display message:
    ```
    🔬 **ORCHESTRATOR**: Resuming active investigation for Group [group_id]...
    ```
  - Load investigation_state from database
  - SKIP Steps 1-2A (normal workflow)
  - JUMP TO Step 2A.6b (Investigation Iteration)
  - Process one more iteration
  - RETURN (end turn)

**IF no active investigation:**
  - Proceed to Step 1 (normal workflow)

**Why This Matters:**
- Investigation loops span multiple orchestrator turns
- Each turn must check if investigation is in progress
- Without this, investigations would be abandoned after first iteration
```

---

### Fix #3: Add Solution Handoff Workflow

**Location:** After Step 2A.6c (Tech Lead validation of investigation findings)

**Current Code (lines 1628-1727):**
```markdown
**IF Tech Lead validates ROOT_CAUSE_FOUND:**
- If APPROVED: Route based on Tech Lead decision (continue to Step 2A.7)
```

**Required Fix:**
```markdown
**IF Tech Lead validates ROOT_CAUSE_FOUND:**

**If APPROVED:**
  1. **Close Investigation:**
     ```
     investigation_state.status = "completed"
     investigation_state.validated = true
     Save to database
     ```

  2. **Spawn Developer with Solution:**
     ```
     Task(
       subagent_type: "general-purpose",
       description: "Developer: Implement investigation solution",
       prompt: """
       You are the DEVELOPER for Group [group_id].

       INVESTIGATION COMPLETE - Implement Solution:

       **Root Cause Found:** [from investigation]
       **Recommended Solution:** [from investigation]
       **Evidence:** [from investigation]
       **Branch:** [feature_branch]

       Please implement this solution, update tests, and report when complete.

       [Include original task context and developer agent prompt]
       """
     )
     ```

  3. **Route Developer Response:**
     - If Developer reports completion → QA → Tech Lead review → PM
     - If Developer has questions → Tech Lead assists → back to Developer

**If CHANGES_REQUESTED (Tech Lead disagrees with findings):**
  1. **Restart Investigation or Close:**
     - Option A: Reset investigation, start from iteration 1 with new hypotheses
     - Option B: Close as INCOMPLETE, provide partial findings to Developer
     - PM decides which option

  2. **Update investigation_state status** accordingly
```

---

### Fix #4: Add BLOCKED Resolution Workflow

**Location:** In Step 2A.6b action routing (around line 1569-1597)

**Current Code:**
```markdown
**ACTION 5: Investigator reports "BLOCKED"**
...
Spawn PM to resolve blocker:
"PM, investigation is blocked..."
```

**Required Fix:**
```markdown
**ACTION 5: Investigator reports "BLOCKED"**

```markdown
## 🚫 Investigation Blocked

**Blocker Type:** [description]
**Current Iteration:** [N]
**Hypotheses State:** [how many tested/eliminated]
```

**Spawn PM with blocker details:**
```
Task(
  subagent_type: "general-purpose",
  description: "PM: Resolve investigation blocker",
  prompt: """
  Investigation is BLOCKED for Group [group_id]:

  **Blocker:** [blocker description]
  **Context:** [problem summary]
  **Progress So Far:** [iterations completed, hypotheses tested]

  **Decision Required:**

  1. **PROVIDE_RESOURCES:**
     - What can you provide to unblock? (access, info, permissions)
     - Investigation will resume with new context

  2. **REPRIORITIZE:**
     - Investigation not worth continuing
     - Accept partial findings and have Developer implement best guess

  3. **ESCALATE_EXTERNALLY:**
     - Requires human intervention
     - Pause orchestration, notify user

  Please decide how to proceed.
  """
)
```

**After PM responds, route based on decision:**

**IF PM says PROVIDE_RESOURCES:**
  ```
  - Update investigation_state:
      additional_context: [from PM]
      blocker_resolved: true
  - Save to database
  - Continue investigation (next turn will resume)
  ```

**IF PM says REPRIORITIZE:**
  ```
  - investigation_state.status = "closed_incomplete"
  - investigation_state.resolution = "reprioritized"
  - Save to database
  - Spawn Developer with partial findings:
      "Investigation incomplete but here's what we learned: [summary]
       Please implement best solution based on this info."
  ```

**IF PM says ESCALATE_EXTERNALLY:**
  ```
  - investigation_state.status = "needs_human"
  - Save to database
  - Display to user:
      "🚨 **ORCHESTRATOR**: Investigation requires human intervention.
       **Issue:** [blocker]
       **Context:** [summary]
       Please provide guidance or resolve blocker manually."
  - PAUSE orchestration (wait for user input)
  ```
```

---

### Fix #5: Add Investigation Deduplication

**Location:** In Step 2A.6b, before initializing new investigation (around line 1285)

**Add Before Creating New Investigation:**
```markdown
#### Check for Duplicate Investigation

**BEFORE initializing new investigation_state:**

**Query database:**
```
bazinga-db, query investigation states WHERE group_id = [current_group_id]
```

**IF investigation exists AND status = "in_progress":**
  - **DO NOT create new investigation**
  - Display message:
    ```
    ℹ️  **ORCHESTRATOR**: Investigation already active for this group. Resuming...
    ```
  - Load existing investigation_state
  - Continue from current iteration
  - RETURN

**IF investigation exists AND status = "completed":**
  - **DO NOT reinvestigate**
  - Display message:
    ```
    ℹ️  **ORCHESTRATOR**: Investigation already completed for this group.
    **Findings:** [root_cause]
    **Solution:** [solution]
    ```
  - Tech Lead should review the SOLUTION, not request new investigation
  - RETURN (don't create duplicate)

**IF investigation exists AND status IN ["closed_incomplete", "max_iterations_reached", "needs_human"]:**
  - Display message:
    ```
    ⚠️  **ORCHESTRATOR**: Previous investigation ended without resolution.
    **Status:** [status]
    **Reason:** [resolution]

    Create new investigation? (This will restart from iteration 1)
    ```
  - User/PM decides whether to restart

**IF no investigation exists:**
  - Proceed to create new investigation_state
```

---

## Testing Plan After Fixes

1. **Simple Investigation (Happy Path):**
   - Tech Lead requests investigation
   - Investigator finds root cause in 2 iterations
   - Tech Lead validates
   - Developer implements solution

2. **Max Iterations:**
   - Investigation reaches 5 iterations without resolution
   - System handles max_iterations_reached status
   - Partial findings forwarded to Developer

3. **BLOCKED Scenario:**
   - Investigator gets blocked
   - PM provides resources → investigation resumes
   - PM reprioritizes → closes with partial findings

4. **Duplicate Prevention:**
   - Tech Lead requests investigation for same group twice
   - System detects existing investigation and resumes it

5. **Session Resume:**
   - Investigation in progress
   - Orchestrator terminates/crashes
   - Next orchestrator turn detects active investigation (Step 0)
   - Investigation resumes from correct iteration

6. **Parallel Mode:**
   - 2 groups both need investigation
   - Each has independent investigation_state
   - Both can run simultaneously without conflicts

## Files Modified Summary

- ✅ bazinga/skills_config.json - optional status added
- ✅ scripts/init-orchestration.sh - updated skills config template
- ✅ agents/techlead.md - spawn → request, hypothesis matrix format
- ✅ agents/investigator.md - input validation
- 🚧 agents/orchestrator.md - Step 0, remove WHILE loop, add workflows (PENDING)

## Estimated Impact

**Lines Changed in Orchestrator:** ~200 lines
**New Sections:** 3 (Step 0, Solution Handoff, Deduplication)
**Modified Sections:** 2 (Step 2A.6b, Step 2A.6c)
**Risk Level:** HIGH (core workflow changes)
**Testing Required:** EXTENSIVE

## Recommendation

These fixes are CRITICAL for the investigation system to function, but they require careful implementation and testing. The orchestrator is the heart of the system - any errors here will break the entire workflow.

**Suggested Approach:**
1. Review this guide thoroughly
2. Implement fixes in a test branch
3. Test each scenario in Testing Plan
4. Merge only after all tests pass

**DO NOT implement these changes without testing** - the orchestrator is too critical.
