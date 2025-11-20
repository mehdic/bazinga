# Development Plan Management Strategy

**Created:** 2025-11-20
**Status:** Approved - Ready for Implementation

---

## 🎯 Problem Statement

**Issue:** When users provide multi-phase development plans and request partial execution (e.g., "do Phase 1 only"), the system loses context when they return later to continue (e.g., "now do Phase 2"). The PM agent spawns fresh and has no memory of the original plan.

**Real Example:**
```
User: "Here's my plan: Phase 1: X, Phase 2: Y, Phase 3: Z. Do Phase 1 only."
[Orchestration completes Phase 1]
User: "Now do Phase 2 and 3"
PM: "??? What plan? What phases?"
```

---

## 🎯 Solution: PM-Owned Development Plan Management

### Core Principle
**Orchestrator = Dumb Router** (just passes user prompt to PM)
**PM = Smart Planner** (detects, creates, saves, and manages plans)

### Key Insight
PM already receives:
- session_id (unique per orchestration)
- Full user prompt
- Access to bazinga-db skill

Therefore, PM can:
1. Check if plan exists for session (first action)
2. Create and save plan if first time
3. Load and continue plan if resuming

**Orchestrator needs NO changes** - it already passes everything PM needs!

---

## 📊 Database Schema

```sql
CREATE TABLE development_plans (
  id INTEGER PRIMARY KEY,
  session_id TEXT UNIQUE,        -- One plan per orchestration session
  original_prompt TEXT NOT NULL, -- User's original prompt (for reference)
  plan_text TEXT NOT NULL,       -- The structured plan (user-provided or PM-generated)
  phases TEXT NOT NULL,          -- JSON: [{phase: 1, name: "...", status: "...", ...}, ...]
  current_phase INTEGER,         -- Which phase we're executing (1-based)
  total_phases INTEGER,          -- Total number of phases in plan
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  metadata TEXT                  -- JSON: {plan_type: "user_provided"|"pm_generated", ...}
);
```

### Schema Design Rationale

**session_id as UNIQUE key:**
- One plan per orchestration session
- Natural foreign key to sessions table
- Prevents duplicate plans

**original_prompt preservation:**
- Critical for context when resuming
- Helps PM understand user's original intent
- Used when user provides vague continuation ("do the rest")

**plan_text vs phases:**
- plan_text: Human-readable structured text
- phases: Machine-readable JSON for state tracking
- Both needed: text for display, JSON for logic

**Metadata extensibility:**
- plan_type: "user_provided_partial" | "user_provided_full" | "pm_generated"
- scope_requested: What user asked for this run
- Future: priority, dependencies, estimates, etc.

---

## 🔄 Workflow

### Scenario 1: First-Time Orchestration (User-Provided Plan, Partial Scope)

```
User: "Here's my plan:
  Phase 1: Setup JWT authentication
  Phase 2: Add user registration
  Phase 3: Email verification

  Do Phase 1 only for now."

↓

Orchestrator:
  ✅ Creates session_id: bazinga_20251120_143022
  ✅ Spawns PM with session_id + full user prompt
  ❌ Does NOT analyze, detect, or parse anything

↓

PM (First Action):
  1. Invokes bazinga-db skill: get_development_plan(session_id)
  2. Response: null (no plan exists)
  3. Analyzes user prompt:
     - Detects explicit plan structure (Phase 1, 2, 3)
     - Detects partial scope ("Phase 1 only", "for now")
     - Determines plan_type: "user_provided_partial"
  4. Parses plan:
     - Phase 1: "Setup JWT authentication" (requested_now=true)
     - Phase 2: "Add user registration" (requested_now=false)
     - Phase 3: "Email verification" (requested_now=false)
  5. Saves to database via bazinga-db skill:
     - original_prompt: [full user message]
     - plan_text: "Phase 1: Setup JWT...\nPhase 2: Add user..."
     - phases: [JSON array with status tracking]
     - current_phase: 1
     - metadata: {plan_type: "user_provided_partial", scope_requested: "Phase 1 only"}
  6. Outputs to orchestrator:
     ```
     ## Development Plan Context
     Session Plan: 3-phase plan detected
     - Phase 1: JWT auth (EXECUTING NOW)
     - Phase 2: User registration (DEFERRED)
     - Phase 3: Email verification (DEFERRED)
     ```
  7. Proceeds with normal planning:
     - Creates task groups for Phase 1 only
     - Decides mode (simple/parallel)
     - Returns to orchestrator

↓

Normal orchestration flow: Dev → QA → Tech Lead → PM → BAZINGA

↓

Result: Phase 1 completed, plan saved to database
```

### Scenario 2: Continuation (User Returns)

```
User: "Now do Phase 2 and 3"

↓

Orchestrator:
  ✅ Uses SAME session_id: bazinga_20251120_143022
  ✅ Spawns PM with session_id + new prompt

↓

PM (First Action):
  1. Invokes bazinga-db skill: get_development_plan(session_id)
  2. Response: Plan found!
     {
       original_prompt: "Here's my plan: Phase 1: JWT, Phase 2: Reg, Phase 3: Email. Do Phase 1 only.",
       phases: [
         {phase: 1, name: "JWT auth", status: "completed"},
         {phase: 2, name: "User registration", status: "not_started"},
         {phase: 3, name: "Email verification", status: "not_started"}
       ],
       current_phase: 1,
       ...
     }
  3. Analyzes new prompt: "do Phase 2 and 3"
  4. Maps to plan: Execute phases 2 and 3
  5. Updates plan in database:
     - current_phase: 2
     - phases[1].status: "in_progress"
     - phases[2].status: "pending"
  6. Outputs to orchestrator:
     ```
     ## Development Plan Context
     Continuing 3-phase plan
     - Phase 1: JWT auth ✓ COMPLETED
     - Phase 2: User registration (EXECUTING NOW)
     - Phase 3: Email verification (NEXT)

     Original request: [shows original_prompt for context]
     ```
  7. Creates task groups for Phases 2 and 3
  8. Proceeds normally

↓

Result: Phases 2 and 3 completed, full plan done
```

### Scenario 3: PM-Generated Plan

```
User: "Add authentication system with JWT and user management"

↓

PM (First Action):
  1. Queries database: No plan exists
  2. Analyzes prompt:
     - No explicit phases detected
     - Requirements: auth system, JWT, user management
     - Determines plan_type: "pm_generated"
  3. Creates plan:
     - Phase 1: Core JWT implementation
     - Phase 2: User CRUD operations
     - Phase 3: Password reset flow
     - Phase 4: Session management
  4. Saves to database
  5. Executes all phases (user didn't request partial)

↓

Result: Complete feature implemented with structured plan saved
```

### Scenario 4: Vague Continuation

```
User: "Continue" or "Do the rest"

↓

PM (First Action):
  1. Loads plan from database
  2. Sees Phase 1 completed
  3. Infers: Execute remaining phases (2, 3)
  4. Proceeds with continuation

↓

Result: Seamless continuation without explicit phase numbers
```

---

## 🛠️ Implementation Details

### 1. Extend bazinga-db Skill

**Location:** `.claude/skills/bazinga-db/SKILL.md`

**New Operations to Add:**

#### save_development_plan
```
bazinga-db, please save this development plan:

Session ID: <session_id>
Original Prompt: <user's full prompt text>
Plan Text: <structured plan as multi-line text>
Phases: <JSON array of phase objects>
Current Phase: <integer>
Total Phases: <integer>
Metadata: <JSON object>
```

**Phase Object Schema:**
```json
{
  "phase": 1,
  "name": "Phase name",
  "status": "pending|in_progress|completed|blocked",
  "description": "Detailed description",
  "requested_now": true,
  "completed_at": "ISO timestamp or null"
}
```

#### get_development_plan
```
bazinga-db, please get the development plan:

Session ID: <session_id>
```

**Returns:**
- Full plan object if exists
- null if no plan found
- Includes all fields: original_prompt, plan_text, phases array, metadata

#### update_plan_progress
```
bazinga-db, please update plan progress:

Session ID: <session_id>
Phase Number: <integer>
Status: <pending|in_progress|completed|blocked>
```

**Updates:**
- Sets phases[N].status to new status
- Updates current_phase pointer if appropriate
- Sets completed_at timestamp if status=completed
- Updates updated_at timestamp

---

### 2. Update Project Manager Agent

**Location:** `agents/project_manager.md`

**Changes Required:**

#### Add "STEP 0: Development Plan Management" (Before Requirement Analysis)

**Insert as FIRST step in PM's task workflow:**

```markdown
## STEP 0: Development Plan Management (FIRST ACTION)

**ALWAYS do this BEFORE analyzing requirements:**

### Query for Existing Plan

Invoke bazinga-db skill to check for existing plan:

```
bazinga-db, please get the development plan:

Session ID: {session_id}
```

Then invoke: `Skill(command: "bazinga-db")`

### Handle Response

**IF plan exists (continuing orchestration):**

You are continuing an existing orchestration. You have:
- **Original prompt:** [see plan.original_prompt]
- **Plan structure:** [see plan.phases array]
- **Current progress:** [see phase statuses]
- **User's new request:** [current user message]

**Your task:**
1. Analyze user's new request
2. Map request to plan phases (which phases to execute?)
3. Update phase statuses in database
4. Continue with task group creation for requested phases

**IF plan does NOT exist (first-time orchestration):**

This is the first orchestration for this session.

**Analyze user prompt to determine plan type:**

**Option A: User Provided Explicit Plan**

Indicators:
- Numbered phases: "Phase 1", "Phase 2", "Step 1", "Step 2"
- Structured list with clear breakdown
- Explicit partial scope: "do X only", "just Y for now", "start with Z"

Actions:
1. Parse their plan structure
2. Extract phases and descriptions
3. Determine scope: What do they want NOW vs LATER?
4. Set plan_type: "user_provided_partial" or "user_provided_full"

**Option B: User Gave Requirements, PM Must Create Plan**

Indicators:
- No explicit phases mentioned
- Requirements and goals described
- No structural breakdown

Actions:
1. Analyze requirements
2. Break into logical phases (typically 2-5 phases)
3. Create structured plan with clear phase boundaries
4. Set plan_type: "pm_generated"

**After determining plan type, save to database:**

```
bazinga-db, please save this development plan:

Session ID: {session_id}
Original Prompt: {user's exact prompt text}
Plan Text: {multi-line structured plan text}
Phases: {JSON array - see schema in research/development-plan-management-strategy.md}
Current Phase: {which phase to start with}
Total Phases: {total number of phases}
Metadata: {"plan_type": "...", "scope_requested": "...", ...}
```

Then invoke: `Skill(command: "bazinga-db")`

### Output Plan Context

After handling plan (load or create), output to orchestrator:

```
## Development Plan Context

**Session Plan:** {X}-phase plan {detected|loaded}
{List phases with status indicators: ✓ COMPLETED, (EXECUTING NOW), (DEFERRED), (NEXT)}

{IF continuing} **Original request:** {show original_prompt for context}
```

This helps orchestrator and user understand the plan context.

**AFTER handling plan: Continue to normal requirement analysis and task group creation.**
```

**Key Implementation Notes:**

1. **Surgical insertion point:** Add Step 0 before existing "## Your Task" or requirement analysis section
2. **Preserve existing PM logic:** All current PM functionality remains unchanged, just add plan management first
3. **Size optimization:** Use compact examples, reference external docs for verbose details
4. **Error handling:** If database operations fail, PM should continue with degraded functionality (log warning, proceed without plan persistence)

---

### 3. No Orchestrator Changes Needed

**Critical point:** Orchestrator already provides everything PM needs:
- ✅ session_id passed in spawn prompt
- ✅ Full user prompt passed to PM
- ✅ PM has access to bazinga-db skill

**No new orchestrator logic required!**

---

## ✅ Benefits

1. **Zero orchestrator changes** - Orchestrator stays dumb router
2. **PM-centric** - Natural extension of PM's planning responsibility
3. **Session-scoped** - Automatic linking via session_id
4. **Context preservation** - Original prompt always available for reference
5. **Flexible** - Handles both user-provided and PM-generated plans
6. **Resumable** - Seamless continuation across orchestration runs
7. **Traceable** - Full plan history in database
8. **Minimal code changes** - Surgical additions only

---

## 🚨 Potential Issues & Mitigations

### Issue 1: PM File Size Limit

**Problem:** Adding Step 0 increases PM file size, may exceed limit

**Mitigation:**
- Keep Step 0 instructions ultra-compact
- Reference external docs for details (this document)
- Use concise examples inline
- Consider extracting verbose sections to separate template files

### Issue 2: Plan Parsing Complexity

**Problem:** Detecting and parsing user-provided plans can be complex

**Mitigation:**
- Simple heuristics: Look for "Phase", "Step", numbered lists
- Fuzzy matching: Don't require exact format
- Fallback: If parsing fails, treat as PM-generated plan
- Start conservative: Support common patterns, expand later

### Issue 3: Vague Continuations

**Problem:** User says "continue" without context

**Mitigation:**
- PM loads plan and infers: execute next incomplete phases
- Show plan context in output so user understands what's happening
- If ambiguous, PM can ask for clarification

### Issue 4: Session Resumption

**Problem:** What if orchestration crashes mid-phase?

**Mitigation:**
- Phase statuses track progress (pending/in_progress/completed)
- PM can detect in_progress and resume or restart
- Future: Add checkpoint support within phases

### Issue 5: Plan Conflicts

**Problem:** User provides conflicting requests (e.g., "do Phase 2" but Phase 1 not done)

**Mitigation:**
- PM validates requests against plan state
- Can warn user about dependencies
- Can auto-include prerequisite phases if needed

---

## 📊 Success Metrics

**How to measure success:**

1. **Context retention:** User can return days later and continue with "do Phase 2"
2. **Plan accuracy:** PM correctly parses user-provided plans
3. **Seamless continuation:** No manual re-explanation needed
4. **Database integrity:** All plans properly saved and retrieved
5. **User satisfaction:** Reduced frustration from context loss

---

## 🚀 Implementation Phases

### Phase 1: Core Functionality (MVP)
**Goal:** Basic plan detection, storage, and retrieval

1. Extend bazinga-db skill with 3 operations
2. Add Step 0 to PM agent (plan management)
3. Test with explicit user-provided plans (Phase 1, Phase 2, etc.)
4. Verify database operations work correctly
5. Test continuation scenario

**Success criteria:** User can provide multi-phase plan, execute Phase 1, return and execute Phase 2

### Phase 2: Enhancement
**Goal:** Better parsing and user experience

1. Improve plan parsing (handle more formats)
2. Add plan summary to user-facing orchestrator capsules
3. Handle edge cases (conflicting requests, missing phases)
4. Add plan validation (dependencies, prerequisites)

**Success criteria:** System handles 90% of real-world plan formats

### Phase 3: Advanced Features
**Goal:** Cross-session and analytics

1. Cross-session plan queries (find related plans)
2. Plan templates (common patterns)
3. Plan analytics (most common phases, success rates)
4. Plan visualization (progress bars, timelines)

**Success criteria:** Plans become strategic asset, not just context preservation

---

## 📚 References

- **Database Schema:** See "Database Schema" section above
- **Skill Operations:** See "Implementation Details" section above
- **PM Changes:** See "Update Project Manager Agent" section above
- **bazinga-db skill docs:** `.claude/skills/bazinga-db/SKILL.md`
- **PM agent definition:** `agents/project_manager.md`
- **Orchestrator workflow:** `agents/orchestrator.md`

---

## 🎯 Key Takeaways

1. **Orchestrator does nothing** - This is a PM-only change
2. **Session-scoped plans** - One plan per orchestration session
3. **First action is plan check** - PM always queries database first
4. **Original prompt preservation** - Critical for context
5. **Surgical implementation** - Minimal code changes, maximum impact

---

**Status:** Ready for implementation - Phase 1
**Owner:** PM Agent + bazinga-db skill
**Estimated effort:** Small (2-3 surgical changes)
**Risk:** Low (isolated changes, no orchestrator impact)
