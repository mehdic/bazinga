# Investigation Loop Template: Comprehensive Design

**Date:** 2025-12-23
**Context:** Creating the missing `investigation_loop.md` template referenced in `templates/orchestrator/phase_simple.md`
**Decision:** Implement hybrid pattern with inline routing tables + external template for detailed procedures
**Status:** Reviewed
**Reviewed by:** OpenAI GPT-5 (Gemini skipped - ENABLE_GEMINI=false)

---

## Problem Statement

The orchestrator references `bazinga/templates/investigation_loop.md` in Step 2A.6b of `phase_simple.md`, but this file was **never created**. The file was planned (as documented in `research/orchestrator-size-optimization-ultrathink-2025-11-24.md`) but the implementation was incomplete.

**Current broken reference:**
```markdown
Read(file_path: "bazinga/templates/investigation_loop.md")
```

**Impact:** When Tech Lead returns `SPAWN_INVESTIGATOR` or `INVESTIGATION_IN_PROGRESS`, the orchestrator cannot read the investigation loop procedure, leading to undefined behavior.

---

## Analysis of Existing Components

### 1. Entry Points (Who Triggers Investigation)

| Trigger Source | Status Code | Context Provided |
|---------------|-------------|------------------|
| Tech Lead | `SPAWN_INVESTIGATOR` | problem_summary, hypothesis_matrix, suggested_skills |
| Tech Lead | `INVESTIGATION_IN_PROGRESS` | Same as above (mid-review trigger) |
| PM | `INVESTIGATION_NEEDED` | investigation_request (blocked by unclear root cause) |

### 2. Investigator Status Codes (Per-Iteration Outputs)

| Status | Meaning | Orchestrator Action |
|--------|---------|---------------------|
| `ROOT_CAUSE_FOUND` | Investigation complete | → Tech Lead validation → Developer fix |
| `NEED_DEVELOPER_DIAGNOSTIC` | Needs instrumentation | → Spawn Developer for diagnostics → Continue loop |
| `HYPOTHESIS_ELIMINATED` | Current theory disproven | → Respawn Investigator (next hypothesis) |
| `NEED_MORE_ANALYSIS` | Deeper analysis needed | → Respawn Investigator (same iteration) |
| `BLOCKED` | External blocker | → Escalate to PM |

### 3. Investigation Exit Codes (Final Outcomes)

| Status | Condition | Orchestrator Route |
|--------|-----------|-------------------|
| `ROOT_CAUSE_FOUND` | High confidence root cause | → Step 2A.6c (Tech Lead validation) |
| `INVESTIGATION_INCOMPLETE` | Max 5 iterations reached | → Step 2A.6c (Tech Lead reviews partial) |
| `BLOCKED` | External dependency | → PM for unblock decision |
| `EXHAUSTED` | All hypotheses eliminated | → PM for new direction |

### 4. State Variables Required

```yaml
investigation_state:
  session_id: string          # From orchestrator context
  group_id: string            # Current task group (main, A, B, etc.)
  branch: string              # Developer's feature branch
  current_iteration: int      # 1-5 (managed by orchestrator)
  max_iterations: 5           # Hard limit
  status: enum                # in_progress | completed | blocked | exhausted
  problem_summary: string     # From Tech Lead
  hypothesis_matrix: array    # [{hypothesis, likelihood, evidence}]
  suggested_skills: array     # Skills for investigator
  iterations_log: array       # History of each iteration
  developer_diagnostic_results: string | null  # If NEED_DEVELOPER_DIAGNOSTIC was used
  root_cause: string | null   # Set when found
  confidence: string | null   # High/Medium percentage
  solution: string | null     # Recommended fix
  partial_findings: string | null  # For INVESTIGATION_INCOMPLETE
```

---

## Critical Edge Cases & Failure Modes

### Edge Case 1: Empty or Invalid Hypothesis Matrix

**Scenario:** Tech Lead provides malformed or empty hypothesis matrix.

**Detection:**
```python
if not hypothesis_matrix or len(hypothesis_matrix) == 0:
    # Invalid state
```

**Handling:**
- Investigator returns `BLOCKED` immediately
- Blocker message: "Tech Lead provided no hypotheses. Need at least 1 hypothesis to investigate."
- Route to Tech Lead for hypothesis clarification

### Edge Case 2: Developer Diagnostic Fails

**Scenario:** Investigator requests NEED_DEVELOPER_DIAGNOSTIC but Developer cannot add instrumentation.

**Detection:** Developer returns `BLOCKED` or test failures after adding diagnostics.

**Handling:**
- Increment iteration count (consumed an attempt)
- Log failure in iterations_log
- Respawn Investigator with: "Diagnostic attempt failed. Consider alternative hypothesis."
- If 3 consecutive diagnostic failures → escalate to SSE for diagnostics

### Edge Case 3: Session Resumption Mid-Investigation

**Scenario:** Orchestrator session ends after iteration 3, user resumes later.

**Required:** Investigation state must persist in database.

**Handling:**
1. Step 0 of orchestrator checks for active investigations
2. Query: `bazinga-db query-investigations WHERE session_id={sid} AND status='in_progress'`
3. If found: Load state, skip to Step 2A.6b, continue from `current_iteration`
4. If not found: Normal workflow

### Edge Case 4: Investigator Returns Unknown Status

**Scenario:** Investigator response doesn't match known status codes.

**Detection:** Parse failure or unrecognized status.

**Handling:**
- Log warning: `⚠️ Unknown investigator status: {status}`
- Treat as `NEED_MORE_ANALYSIS` (conservative - continue investigation)
- Cap at 2 unknown statuses before `BLOCKED` escalation

### Edge Case 5: Tech Lead Rejects Root Cause (Validation Failure)

**Scenario:** Investigator finds root cause, but Tech Lead disagrees during validation (Step 2A.6c).

**Handling:**
- IF Tech Lead returns `CHANGES_REQUESTED`:
  - DO NOT close investigation
  - Add Tech Lead feedback to `iterations_log`
  - Respawn Investigator with: "Tech Lead rejected solution. Feedback: {feedback}"
  - Resume from current iteration (doesn't consume new iteration)

### Edge Case 6: PM Provides Resources After BLOCKED

**Scenario:** Investigator hits `BLOCKED`, PM provides missing resources.

**PM Decision Options:**
| PM Response | Action |
|-------------|--------|
| `PROVIDE_RESOURCES` | Resume investigation with new context |
| `REPRIORITIZE` | Close investigation, simplify task |
| `ESCALATE_EXTERNALLY` | Mark as external dependency, park task |

**Handling:**
- If `PROVIDE_RESOURCES`: Reset iteration counter? (DECISION NEEDED)
- My recommendation: **Do NOT reset** - investigations have 5 total iterations regardless of blocks

### Edge Case 7: Parallel Investigations (Multiple Groups)

**Scenario:** Multiple task groups have concurrent investigations.

**Handling:**
- Each investigation is scoped to `group_id`
- Database queries must filter by `group_id`
- Orchestrator can only manage ONE investigation per turn
- If multiple: Process oldest (by `started_at`) first

### Edge Case 8: Hypothesis Matrix Exhausted Before Iteration Limit

**Scenario:** 3 hypotheses, all eliminated by iteration 3.

**Detection:** `iterations_log` shows all hypotheses in matrix have status `eliminated`.

**Handling:**
- Return `EXHAUSTED` status (distinct from `INVESTIGATION_INCOMPLETE`)
- Route to PM with: "All hypotheses eliminated. Need new theories or task reassessment."
- PM can: Provide new hypotheses, simplify task, or close as unresolvable

### Edge Case 9: Confidence Level Ambiguity

**Scenario:** Investigator says "Medium confidence (60%)" - is this enough for ROOT_CAUSE_FOUND?

**Threshold Rules:**
| Confidence | Status | Action |
|------------|--------|--------|
| High (80%+) | `ROOT_CAUSE_FOUND` | Proceed to validation |
| Medium (50-79%) | `ROOT_CAUSE_FOUND` | Proceed but flag for extra scrutiny |
| Low (<50%) | Continue investigation | Need more evidence |

**Handling:** Tech Lead validation (Step 2A.6c) is the safety net - catches weak root causes.

### Edge Case 10: Developer Diagnostic Creates Regression

**Scenario:** Developer adds logging code that breaks tests.

**Detection:** QA fails after diagnostic code merge.

**Handling:**
- This is a Developer workflow issue, not investigation issue
- Developer should add diagnostics on feature branch
- Investigation continues with whatever output was gathered
- If no output: Treat as diagnostic failure (Edge Case 2)

---

## Template Design Decision

### Hybrid Pattern (Recommended)

Based on `research/template-extraction-routing-reliability.md`, use the **Hybrid Pattern**:

1. **phase_simple.md** keeps:
   - Entry conditions
   - Exit code routing table
   - Quick reference for status codes

2. **investigation_loop.md** contains:
   - Full loop management procedure
   - State initialization details
   - Developer diagnostic spawn procedure
   - Edge case handling
   - Database logging requirements

**Rationale:**
- Inline routing prevents missed statuses (primary concern)
- External template keeps orchestrator size manageable
- Matches investigation_loop pattern already referenced in research docs

---

## Proposed Template Structure

### Section 1: Purpose and Prerequisites
- What this template does
- Required context variables
- Entry conditions

### Section 2: State Initialization
- Create investigation_state object
- Validate hypothesis matrix
- Save initial state to database

### Section 3: Loop Iteration Logic (Single Iteration Per Orchestrator Turn)
- Increment iteration counter
- Check max iterations
- Build investigator prompt
- Spawn investigator
- Parse response
- Route based on status

### Section 4: Developer Diagnostic Procedure
- When: NEED_DEVELOPER_DIAGNOSTIC received
- Build developer diagnostic prompt
- Spawn developer (sonnet, not haiku)
- Handle diagnostic results
- Feed back to investigator

### Section 5: Exit Procedures
- ROOT_CAUSE_FOUND → Tech Lead validation spawn
- BLOCKED → PM escalation spawn
- INVESTIGATION_INCOMPLETE → Tech Lead partial review
- EXHAUSTED → PM new direction

### Section 6: Database Logging Requirements
- Log iteration start
- Log iteration result
- Log final outcome
- Update task group status

### Section 7: Edge Case Reference Table
- Quick lookup for all edge cases
- One-line handling instructions

---

## Critical Analysis

### Pros ✅

1. **Completes missing implementation** - Fixes the broken reference
2. **Comprehensive edge case handling** - 10 identified scenarios covered
3. **Hybrid pattern** - Balances size reduction with routing reliability
4. **Database persistence** - Enables session resumption
5. **Clear routing tables** - Deterministic status → action mapping

### Cons ⚠️

1. **Adds complexity** - Investigation loop is already complex; more rules add cognitive load
2. **Single-iteration-per-turn** - Investigations span multiple orchestrator invocations; may feel slow
3. **Database dependency** - Requires bazinga-db skill to work correctly
4. **Edge case overhead** - 10 edge cases may be over-engineered for rare scenarios

### Verdict

**PROCEED** - The template is necessary (reference exists but file doesn't). The hybrid pattern is proven by other templates (merge_workflow.md). Edge cases are real scenarios from existing research docs.

---

## Implementation Plan

### Phase 1: Create Base Template
1. Create `templates/investigation_loop.md` with sections 1-6
2. Include all status codes and routing
3. Add database logging requirements

### Phase 2: Add Edge Case Handling
1. Add Section 7 (edge case reference table)
2. Add specific handling for each identified edge case
3. Include validation rules (e.g., hypothesis matrix check)

### Phase 3: Update Phase_Simple.md
1. Verify Read instruction points to correct path
2. Ensure inline routing table matches template
3. Add any missing status code references

### Phase 4: Verify Integration
1. Check orchestrator.md references
2. Ensure investigator.md status codes align
3. Validate database schema supports investigation state

---

## Questions for External Review

1. **Iteration reset after BLOCKED?** Should PM's PROVIDE_RESOURCES reset the 5-iteration counter, or are blocks counted against the limit?

2. **Parallel investigation limit?** Should we cap concurrent investigations (e.g., max 2 groups under investigation)?

3. **Confidence threshold for ROOT_CAUSE_FOUND?** Is 50% (Medium) too low? Should we require 70%+?

4. **Developer diagnostic model?** Should diagnostic Developer spawns use sonnet (current plan) or haiku (cost savings)?

5. **Unknown status handling?** Is treating unknown as NEED_MORE_ANALYSIS too permissive? Should it immediately escalate?

---

## Appendix A: Complete Status Code Matrix

### Investigator → Orchestrator (Per-Iteration)

| Status | Meaning | Next Action | Database Log |
|--------|---------|-------------|--------------|
| `ROOT_CAUSE_FOUND` | High confidence root cause | → TL validation | `investigation_complete` |
| `NEED_DEVELOPER_DIAGNOSTIC` | Needs code instrumentation | → Dev diagnostic spawn | `diagnostic_requested` |
| `HYPOTHESIS_ELIMINATED` | Theory disproven | → Respawn investigator | `hypothesis_eliminated` |
| `NEED_MORE_ANALYSIS` | Need deeper analysis | → Respawn investigator | `continuing_analysis` |
| `BLOCKED` | External blocker | → PM escalation | `investigation_blocked` |

### Investigator → Orchestrator (Final Exit)

| Status | Meaning | Next Action | Database Log |
|--------|---------|-------------|--------------|
| `ROOT_CAUSE_FOUND` | Investigation success | → TL validation | `investigation_complete` |
| `INVESTIGATION_INCOMPLETE` | Max iterations reached | → TL partial review | `investigation_incomplete` |
| `BLOCKED` | Cannot proceed | → PM decision | `investigation_blocked` |
| `EXHAUSTED` | All hypotheses eliminated | → PM new direction | `hypotheses_exhausted` |

### Tech Lead Validation → Orchestrator

| Status | Meaning | Next Action |
|--------|---------|-------------|
| `APPROVED` | Root cause valid | → Close investigation → Developer fix |
| `CHANGES_REQUESTED` | Root cause rejected | → Resume investigation with feedback |

---

## Appendix B: Database State API Usage (Corrected - No Inline SQL)

**Per review feedback: Use existing bazinga-db `save-state`/`get-state` APIs, not new SQL tables.**

### Save Investigation State
```
bazinga-db, please save state:
Session ID: {session_id}
State Type: investigation
Data: {
  "group_id": "{group_id}",
  "branch": "{branch}",
  "status": "in_progress",
  "current_iteration": 0,
  "max_iterations": 5,
  "problem_summary": "{text}",
  "hypothesis_matrix": [{hypothesis, likelihood, evidence}],
  "suggested_skills": ["skill1", "skill2"],
  "iterations_log": [],
  "developer_diagnostic_results": null,
  "root_cause": null,
  "confidence": null,
  "solution": null,
  "partial_findings": null
}
```

### Get Investigation State
```
bazinga-db, please get state:
Session ID: {session_id}
State Type: investigation
```

### Update Investigation State
```
bazinga-db, please save state:
Session ID: {session_id}
State Type: investigation
Data: {updated investigation_state object}
```

### Query for Active Investigations (Session Resume)
```
bazinga-db, please get state:
Session ID: {session_id}
State Type: investigation

Then check: IF state.status == "in_progress" → Resume
```

### Log Investigation Iteration
```
bazinga-db, please log interaction:
Session ID: {session_id}
Agent Type: investigator
Content: {
  "iteration": N,
  "hypothesis_tested": "{hypothesis}",
  "status": "{status}",
  "summary": "{summary}"
}
Iteration: {N}
Agent ID: investigator_{group_id}_iter{N}
```

**Note:** This uses existing bazinga-db APIs. No new tables or inline SQL required.

---

## Appendix C: Proposed Template Content (POST-REVIEW CORRECTED)

```markdown
# Investigation Loop Management

**Purpose:** Orchestrator procedure for managing Investigator agent iterations
**When:** Tech Lead returns SPAWN_INVESTIGATOR
**Version:** 1.1 (post-review corrections applied)

---

## Prerequisites

Before starting investigation loop, verify:
- `session_id` - Current session (from Step 0)
- `group_id` - Current task group ("main", "A", "B", etc.)
- `branch` - Developer's feature branch
- `problem_summary` - From Tech Lead
- `hypothesis_matrix` - From Tech Lead (MUST be non-empty)
- `suggested_skills` - Optional list of skills

---

## Step 1: Initialize or Resume Investigation State

**Query database for existing investigation:**
```
bazinga-db, please get state:
Session ID: {session_id}
State Type: investigation
```

**IF existing investigation found:**
```
investigation_state = parse(state_data)
IF investigation_state.group_id == {current_group_id} AND investigation_state.status == "in_progress":
    Log: "🔬 Resuming investigation | Iteration {current_iteration + 1} of 5"
    → Continue to Step 2
```

**IF no existing investigation:**

**1a. Validate hypothesis matrix:**
```
IF hypothesis_matrix is empty OR null:
    status = BLOCKED
    blocker = "Tech Lead provided no hypotheses. Cannot investigate."
    → Route to Tech Lead for hypothesis clarification
    TERMINATE orchestrator turn
```

**1b. Initialize new state:**
```yaml
investigation_state:
  session_id: {session_id}
  group_id: {group_id}
  branch: {branch}
  current_iteration: 0
  max_iterations: 5
  status: "in_progress"
  problem_summary: {from Tech Lead}
  hypothesis_matrix: {from Tech Lead}
  suggested_skills: {from Tech Lead or []}
  iterations_log: []
  developer_diagnostic_results: null
  root_cause: null
  confidence: null
  solution: null
```

**1c. Save to database (using bazinga-db state APIs):**
```
bazinga-db, please save state:
Session ID: {session_id}
State Type: investigation
Data: {investigation_state as JSON}
```

---

## Step 2: Check Iteration Limit

```
investigation_state.current_iteration += 1

IF current_iteration > max_iterations:
    investigation_state.status = "incomplete"
    bazinga-db, please save state:
    Session ID: {session_id}
    State Type: investigation
    Data: {investigation_state}

    → Route to Step 5b (INVESTIGATION_INCOMPLETE exit)
    TERMINATE orchestrator turn
```

---

## Step 3: Spawn Investigator (Using prompt-builder)

**Step 3a: Write parameters file:**
```
Write params_investigator_{group_id}.json:
{
  "agent_type": "investigator",
  "session_id": "{session_id}",
  "group_id": "{group_id}",
  "branch": "{branch}",
  "current_iteration": {current_iteration},
  "max_iterations": 5,
  "problem_summary": "{investigation_state.problem_summary}",
  "hypothesis_matrix": {investigation_state.hypothesis_matrix},
  "previous_results": {iterations_log[-1] or null},
  "developer_diagnostic_results": {developer_diagnostic_results or null},
  "suggested_skills": {suggested_skills}
}
```

**Step 3b: Invoke prompt-builder skill:**
```
Skill(command: "prompt-builder")
→ Reads params file, builds complete prompt
→ Returns built_prompt
```

**Step 3c: Spawn Investigator:**
```
Task(
  subagent_type: "general-purpose",
  model: MODEL_CONFIG["investigator"],
  description: "Investigator iteration {current_iteration}",
  prompt: {built_prompt from prompt-builder}
)
```

**TERMINATE orchestrator turn** (await Investigator response)

---

## Step 4: Parse and Route Investigator Response

**When Investigator response received:**

**Step 4a: Extract status** (look for JSON response or `**STATUS:**` line):

| Status | Action |
|--------|--------|
| `ROOT_CAUSE_FOUND` | → Step 5a |
| `NEED_DEVELOPER_DIAGNOSTIC` | → Step 4b (capacity check) → Step 4c (Developer spawn) |
| `HYPOTHESIS_ELIMINATED` | → Log → Step 3 (next orchestrator turn) |
| `NEED_MORE_ANALYSIS` | → Log → Step 3 (next orchestrator turn) |
| `BLOCKED` | → Step 5c |
| `EXHAUSTED` | → Step 5d |
| Unknown/Parse Error | → Treat as NEED_MORE_ANALYSIS (max 2 times) → then BLOCKED |

**Step 4a-log: Log iteration result:**
```
bazinga-db, please log investigation iteration:
Session ID: {session_id}
Group ID: {group_id}
Iteration: {current_iteration}
Status: {status}
Summary: {extracted summary}
```

**Update investigation_state.iterations_log and save:**
```
iterations_log.append({
  "iteration": current_iteration,
  "status": status,
  "summary": extracted_summary
})
bazinga-db, please save state: ...
```

---

## Step 4b: Capacity Check (Before Diagnostic Developer Spawn)

**Check active developer count:**
```
bazinga-db, please get active agent count:
Session ID: {session_id}
Agent Type: developer
```

**IF active_developers >= 4:**
```
Log: "⚠️ MAX 4 developers active - queuing diagnostic"
investigation_state.developer_diagnostic_results = "DIAGNOSTIC_DEFERRED: Capacity limit"
→ Step 3 (continue investigation without diagnostics, next turn)
TERMINATE orchestrator turn
```

**IF active_developers < 4:**
→ Proceed to Step 4c

---

## Step 4c: Developer Diagnostic Spawn (Using prompt-builder)

**Step 4c-1: Write parameters file:**
```
Write params_developer_{group_id}_diagnostic.json:
{
  "agent_type": "developer",
  "session_id": "{session_id}",
  "group_id": "{group_id}",
  "branch": "{branch}",
  "task_type": "diagnostic",
  "diagnostic_request": {
    "hypothesis": "{investigator.hypothesis}",
    "request": "{investigator.diagnostic_request}",
    "expected_output": "{investigator.expected_output}"
  },
  "instructions": "DO NOT fix bug. ONLY add diagnostics. Report results."
}
```

**Step 4c-2: Invoke prompt-builder skill:**
```
Skill(command: "prompt-builder")
```

**Step 4c-3: Check escalation (respect revision count):**
```
bazinga-db, please get revision count:
Session ID: {session_id}
Group ID: {group_id}

IF revision_count >= 1:
    model = MODEL_CONFIG["senior_software_engineer"]
ELSE:
    model = MODEL_CONFIG["developer"]
```

**Step 4c-4: Spawn Developer/SSE:**
```
Task(
  subagent_type: "general-purpose",
  model: {model from step 4c-3},
  description: "Developer diagnostics for investigation",
  prompt: {built_prompt from prompt-builder}
)
```

**Increment revision count:**
```
bazinga-db, please increment revision:
Session ID: {session_id}
Group ID: {group_id}
```

**TERMINATE orchestrator turn** (await Developer response)

---

## Step 4d: Process Developer Diagnostic Response

**When Developer response received:**

**IF Developer returns READY_FOR_QA or similar success:**
```
investigation_state.developer_diagnostic_results = developer_output
Save to database
→ Step 3 (respawn Investigator with results, next turn)
TERMINATE orchestrator turn
```

**IF Developer returns BLOCKED:**
```
Log: "Diagnostic attempt failed"
investigation_state.developer_diagnostic_results = "DIAGNOSTIC_FAILED: {reason}"
iterations_log.append({iteration: N, diagnostic_failed: true})
Save to database
→ Step 3 (Investigator decides next action, next turn)
TERMINATE orchestrator turn
```

**Instrumentation Hygiene Reminder:**
- Diagnostic code MUST be on feature branch only
- Diagnostic code MUST be removed before QA/TL/merge
- DO NOT route diagnostic Developer to QA (diagnostic_only task)

---

## Step 5: Exit Procedures

### Step 5a: ROOT_CAUSE_FOUND

**Update state:**
```
investigation_state.status = "root_cause_found"
investigation_state.root_cause = {from investigator}
investigation_state.confidence = {from investigator}
investigation_state.solution = {from investigator}
bazinga-db, please save state: ...
```

**Register context package:**
```
bazinga-db, please save context package:
Session ID: {session_id}
Group ID: {group_id}
Package Type: investigation
File Path: bazinga/artifacts/{session_id}/investigation_{group_id}.md
Producer Agent: investigator
Consumer Agents: ["developer", "senior_software_engineer"]
Priority: high
Summary: {1-sentence root cause + fix}
```

**Route to Tech Lead validation (Step 2A.6c in phase_simple.md)**

**TERMINATE orchestrator turn**

### Step 5b: INVESTIGATION_INCOMPLETE

**State already set in Step 2 (max iterations)**

**Build partial findings:**
```
investigation_state.partial_findings = {
  "iterations_completed": current_iteration,
  "hypotheses_tested": [list from iterations_log],
  "progress": {summary of what was learned}
}
bazinga-db, please save state: ...
```

**Route to Tech Lead partial review (Step 2A.6c with incomplete flag)**

**TERMINATE orchestrator turn**

### Step 5c: BLOCKED

**Update state:**
```
investigation_state.status = "blocked"
investigation_state.blocker = {from investigator}
bazinga-db, please save state: ...
```

**Spawn PM with NEEDS_CLARIFICATION (using existing PM status):**

**Write PM params file:**
```
Write params_pm_{session_id}_unblock.json:
{
  "agent_type": "project_manager",
  "session_id": "{session_id}",
  "clarification_type": "investigation_blocked",
  "blocker": "{blocker}",
  "progress": "{iterations_log summary}",
  "iterations_used": {current_iteration},
  "options": [
    "Provide resources/context to unblock",
    "Simplify task and close investigation",
    "Mark as external dependency (park task)"
  ]
}
```

**Invoke prompt-builder and spawn PM:**
```
Skill(command: "prompt-builder")
Task(model: MODEL_CONFIG["project_manager"], prompt: {built_prompt})
```

**TERMINATE orchestrator turn**

### Step 5c-response: PM Unblock Response

**When PM responds:**

**IF PM status = CONTINUE with resources:**
```
investigation_state.status = "in_progress"
Add PM resources to investigation context
Save to database
→ Step 3 (continue investigation, next turn)
NOTE: Do NOT reset iteration counter
```

**IF PM status = NEEDS_CLARIFICATION (task simplification):**
```
investigation_state.status = "closed_simplified"
Save to database
→ Follow standard clarification flow
```

### Step 5d: EXHAUSTED

**Update state:**
```
investigation_state.status = "exhausted"
bazinga-db, please save state: ...
```

**Route to PM for new direction** (same as BLOCKED but with "all hypotheses eliminated" context)

**TERMINATE orchestrator turn**

---

## Edge Case Reference

| Scenario | Detection | Action |
|----------|-----------|--------|
| Empty hypothesis matrix | `len(matrix) == 0` | BLOCKED → Tech Lead |
| Developer diagnostic fails | Developer BLOCKED | Log failure, continue investigation |
| Capacity limit hit | `active_developers >= 4` | Defer diagnostic, continue without |
| Unknown investigator status | Parse failure | Treat as NEED_MORE_ANALYSIS (max 2x) |
| Tech Lead rejects root cause | TL CHANGES_REQUESTED | Resume investigation with feedback |
| PM provides resources | PM CONTINUE | Resume (do NOT reset iteration counter) |
| All hypotheses eliminated | All in matrix = eliminated | EXHAUSTED → PM |
| Session resumption | Active investigation in DB | Load state, continue from current iteration |

---

## Quick Reference: Status → Action (Valid Status Codes Only)

| From | Status | → To | Action |
|------|--------|------|--------|
| Tech Lead | SPAWN_INVESTIGATOR | Investigator | Initialize loop |
| Investigator | ROOT_CAUSE_FOUND | Tech Lead | Validate solution |
| Investigator | NEED_DEVELOPER_DIAGNOSTIC | Developer | Add instrumentation |
| Investigator | HYPOTHESIS_ELIMINATED | Investigator | Test next hypothesis |
| Investigator | NEED_MORE_ANALYSIS | Investigator | Deeper analysis |
| Investigator | BLOCKED | PM | Via NEEDS_CLARIFICATION |
| Investigator | EXHAUSTED | PM | Via NEEDS_CLARIFICATION |
| Tech Lead (validation) | APPROVED | Developer | Implement fix |
| Tech Lead (validation) | CHANGES_REQUESTED | Investigator | Resume with feedback |
| PM (unblock) | CONTINUE | Investigator | Resume investigation |
| PM (unblock) | NEEDS_CLARIFICATION | User | Request input |
```

---

## References

- `agents/investigator.md` - Investigator agent definition
- `agents/tech_lead.md` - Tech Lead triggers and validation
- `templates/orchestrator/phase_simple.md` - Step 2A.6b reference
- `research/orchestrator-critical-fixes-guide.md` - Single-iteration-per-turn pattern
- `research/template-extraction-routing-reliability.md` - Hybrid pattern justification
- `research/deterministic-orchestration-system.md` - Status code transitions

---

## Multi-LLM Review Integration

### Critical Issues Identified (OpenAI GPT-5)

The OpenAI review identified **7 critical issues** that would break the template at runtime:

#### 1. Prompt-Builder Violation (MUST FIX)
**Issue:** Template spawns Investigator/Developer with inline prompts.
**Current:** Inline prompt building in Step 3
**Required:** Write params file → Skill(prompt-builder) → Task with file reference
**Fix:** Replace all inline prompts with prompt-builder invocation pattern

#### 2. Invalid DB Schema (MUST FIX)
**Issue:** Proposed new `investigation_states` table violates "no inline SQL" rule and isn't supported by bazinga-db skill.
**Current:** SQL DDL in Appendix B
**Required:** Use existing `save-state`/`get-state` APIs with `state_type="investigation"`
**Fix:** Remove SQL DDL, use bazinga-db state APIs with JSON payload

#### 3. Invalid Status Codes (MUST FIX)
**Issue:** Several status codes don't exist in agent definitions:
- `INVESTIGATION_IN_PROGRESS` - Not defined in tech_lead.md
- `PROVIDE_RESOURCES`, `REPRIORITIZE`, `ESCALATE_EXTERNALLY` - Not defined in project_manager.md

**Fix:**
- Use `SPAWN_INVESTIGATOR` instead of `INVESTIGATION_IN_PROGRESS`
- Use existing PM statuses: `NEEDS_CLARIFICATION` for unblock decisions, `CONTINUE` for resume

#### 4. Hardcoded Model Selection (MUST FIX)
**Issue:** "use sonnet for diagnostics" violates MODEL_CONFIG requirement
**Fix:** Use `MODEL_CONFIG["developer"]` initially, escalate per revision count/challenge level

#### 5. File Path Mismatch (MUST FIX)
**Issue:** References `agents/techlead.md` (should be `agents/tech_lead.md`)
**Fix:** Correct all file paths

#### 6. Loop Timing Ambiguity (MUST FIX)
**Issue:** "Loop to Step 3" implies same-turn execution; orchestrator cannot wait for responses
**Fix:** Change to "After receiving Developer response in the next turn, resume at Step 3"

#### 7. Capacity/Parallelism Omission (MUST FIX)
**Issue:** Diagnostic Developer spawns ignore MAX 4 limit
**Fix:** Add capacity check before spawning

### Missing Considerations Identified

1. **Workflow-router integration** - Should use workflow-router skill for deterministic routing
2. **Context packages** - Should register investigation artifacts via context package mechanism
3. **Instrumentation hygiene** - Diagnostics must be isolated to feature branch, cleaned before merge
4. **Revision tracking** - Diagnostic spawns must increment revision counters
5. **QA gating** - Clarify diagnostic code doesn't trigger QA routing
6. **Spec-kit mode** - Explicitly state orthogonal to spec-kit mode

### Incorporated Feedback

| Issue | Original | Correction |
|-------|----------|------------|
| Status codes | INVESTIGATION_IN_PROGRESS | SPAWN_INVESTIGATOR |
| PM statuses | PROVIDE_RESOURCES/REPRIORITIZE/ESCALATE_EXTERNALLY | NEEDS_CLARIFICATION (with options) |
| Model selection | Hardcoded "sonnet" | MODEL_CONFIG["developer"] + escalation |
| Prompts | Inline prompts | prompt-builder skill |
| DB state | New SQL table | bazinga-db save-state/get-state |
| Loop timing | "Loop to Step 3" | "After next turn, resume at Step 3" |
| File paths | techlead.md | tech_lead.md |
| Capacity | None | Check active_developers < 4 |

### Rejected Suggestions (With Reasoning)

1. **Lean entirely on workflow-router** - Rejected because:
   - Hybrid pattern (inline + template) is established in other templates
   - Investigation has unique edge cases not in workflow-router
   - Keep manual routing as fallback if router fails

2. **"diagnostic_only" flag in prompt-builder** - Deferred because:
   - Adds complexity to prompt-builder skill
   - Can be achieved with task_requirements field instead
   - Consider for future enhancement

### Revised Template Design

After integrating feedback, the template must:

1. **Use prompt-builder for ALL spawns:**
   ```
   Write params_{agent_type}_{group_id}.json
   Skill(command: "prompt-builder")
   Task(prompt: {from prompt-builder output})
   ```

2. **Use bazinga-db state APIs:**
   ```
   bazinga-db, please save state:
   Session ID: {session_id}
   State Type: investigation
   Data: {investigation_state JSON}
   ```

3. **Respect MODEL_CONFIG:**
   - Investigator: `MODEL_CONFIG["investigator"]`
   - Developer (diagnostics): `MODEL_CONFIG["developer"]` with escalation
   - SSE (if escalated): `MODEL_CONFIG["senior_software_engineer"]`

4. **Use valid status codes only:**
   - Entry: Tech Lead → `SPAWN_INVESTIGATOR`
   - Exit: Investigator → `ROOT_CAUSE_FOUND`, `INVESTIGATION_INCOMPLETE`, `BLOCKED`, `EXHAUSTED`
   - PM unblock: Use `NEEDS_CLARIFICATION` with explicit options in PM's narrative

5. **Clarify turn boundaries:**
   - Each step that spawns an agent ends with "TERMINATE orchestrator turn"
   - Next step begins with "When response received from {agent}"

6. **Add capacity check:**
   ```
   Check: active_developers_count < 4
   IF >= 4: Queue diagnostic, continue investigation without diagnostics
   ```

7. **Add instrumentation hygiene rules:**
   - Diagnostics on feature branch only
   - Must be removed/guarded before QA/TL/merge
   - Include cleanup checklist in template

### Confidence Assessment

**Before review:** Medium - Template addressed the gap but untested against guardrails
**After review:** High - With fixes, design aligns with orchestrator policies

### Implementation Priority

1. **P0 (Blocking):** Fix status codes, prompt-builder usage, DB schema
2. **P1 (Important):** Add capacity checks, turn boundaries, file path corrections
3. **P2 (Enhancement):** Instrumentation hygiene, context package registration

---

## Gap Analysis: transitions.json vs investigator.md Alignment

### Gap 1: ROOT_CAUSE_FOUND Routing Error

**Current (WRONG):**
```json
// bazinga/config/transitions.json lines 173-177
"ROOT_CAUSE_FOUND": {
  "next_agent": "developer",  // ❌ WRONG
  "action": "spawn",
  "include_context": ["root_cause", "fix_guidance"]
}
```

**Correct (Per investigator.md line 689):**
```json
"ROOT_CAUSE_FOUND": {
  "next_agent": "tech_lead",  // ✅ CORRECT - Tech Lead validates first
  "action": "spawn",
  "include_context": ["root_cause", "fix_guidance", "investigation_summary"]
}
```

**Evidence:**
- `investigator.md:689`: "Routing back to Tech Lead for validation and decision"
- `INVESTIGATION_WORKFLOW.md` Exit Routing diagram shows ROOT_CAUSE_FOUND → Tech Lead
- Tech Lead validation is a safety net - catches weak root causes before Developer implements

**Impact if not fixed:**
- Developer receives root cause without Tech Lead validation
- Potentially wrong root causes get implemented as fixes
- Wastes development cycles on incorrect solutions

### Gap 2: Status Code Name Mismatches

**Current Status Code Comparison:**

| Investigator Returns | transitions.json Has | Match? | Decision |
|---------------------|---------------------|--------|----------|
| `ROOT_CAUSE_FOUND` | `ROOT_CAUSE_FOUND` | ✅ | Keep |
| `INVESTIGATION_INCOMPLETE` | `INCOMPLETE` | ❌ | Update transitions.json |
| `NEED_DEVELOPER_DIAGNOSTIC` | `WAITING_FOR_RESULTS` | ❌ | Update transitions.json |
| `BLOCKED` | `BLOCKED` | ✅ | Keep |
| `EXHAUSTED` | `EXHAUSTED` | ✅ | Keep |

**Rationale for Updating transitions.json (NOT investigator.md):**

1. **Agent files are authoritative** - Agent definitions specify what status codes they return
2. **Descriptive names are better** - `INVESTIGATION_INCOMPLETE` is more descriptive than `INCOMPLETE`
3. **NEED_DEVELOPER_DIAGNOSTIC is action-oriented** - Better than passive `WAITING_FOR_RESULTS`
4. **Config follows behavior** - transitions.json is configuration that matches agent behavior

### Fix Plan

#### Fix 1: Update ROOT_CAUSE_FOUND routing in transitions.json

```json
// Change line 174 from:
"next_agent": "developer"
// To:
"next_agent": "tech_lead"
```

#### Fix 2: Rename INCOMPLETE to INVESTIGATION_INCOMPLETE in transitions.json

```json
// Change line 178 key from:
"INCOMPLETE": {
// To:
"INVESTIGATION_INCOMPLETE": {
```

#### Fix 3: Rename WAITING_FOR_RESULTS to NEED_DEVELOPER_DIAGNOSTIC in transitions.json

```json
// Change line 193 key from:
"WAITING_FOR_RESULTS": {
// To:
"NEED_DEVELOPER_DIAGNOSTIC": {
```

Additionally, `NEED_DEVELOPER_DIAGNOSTIC` is an **internal loop status** handled by the investigation_loop.md template (not workflow-router). The transitions.json entry exists as fallback only. The include_context should reflect diagnostic request:

```json
"NEED_DEVELOPER_DIAGNOSTIC": {
  "next_agent": "developer",
  "action": "spawn",
  "include_context": ["diagnostic_request", "hypothesis", "expected_output"]
}
```

### workflow_router.py Impact

The `workflow_router.py` script reads from database (seeded from transitions.json). Changes:
1. Update transitions.json
2. Re-seed database using config-seeder skill (or re-init)

No code changes needed to workflow_router.py itself.

### Complete Updated investigator Section for transitions.json

```json
"investigator": {
  "ROOT_CAUSE_FOUND": {
    "next_agent": "tech_lead",
    "action": "spawn",
    "include_context": ["root_cause", "fix_guidance", "investigation_summary", "evidence"]
  },
  "INVESTIGATION_INCOMPLETE": {
    "next_agent": "tech_lead",
    "action": "spawn",
    "include_context": ["partial_findings", "iterations_completed", "hypotheses_tested", "next_steps"]
  },
  "BLOCKED": {
    "next_agent": "tech_lead",
    "action": "spawn",
    "include_context": ["blocker_details", "progress_summary"]
  },
  "EXHAUSTED": {
    "next_agent": "tech_lead",
    "action": "spawn",
    "include_context": ["hypotheses_tested", "elimination_reasons", "recommendations"]
  },
  "NEED_DEVELOPER_DIAGNOSTIC": {
    "next_agent": "developer",
    "action": "spawn",
    "include_context": ["diagnostic_request", "hypothesis", "expected_output"]
  }
}
```

### Validation Checklist

After fix implementation:
- [ ] transitions.json has correct `ROOT_CAUSE_FOUND` → `tech_lead` routing
- [ ] transitions.json uses `INVESTIGATION_INCOMPLETE` (not `INCOMPLETE`)
- [ ] transitions.json uses `NEED_DEVELOPER_DIAGNOSTIC` (not `WAITING_FOR_RESULTS`)
- [ ] Database re-seeded with updated config
- [ ] workflow_router.py tests pass (if any)
- [ ] investigator.md status codes align with transitions.json

### Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking existing investigations | Low | High | Gap exists in code that was never working |
| Config-seeder doesn't pick up changes | Low | Medium | Verify seeding script reads from correct path |
| Other agents reference old status codes | Low | Low | Grep for WAITING_FOR_RESULTS and INCOMPLETE |

### Implementation Order

1. **Update transitions.json** (3 changes)
2. **Create investigation_loop.md template** (Gap 3)
3. **Re-seed database** (verify changes applied)
4. **Update INVESTIGATION_WORKFLOW.md** Known Gaps section (mark as fixed)
5. **Run tests** (if any exist for workflow routing)
