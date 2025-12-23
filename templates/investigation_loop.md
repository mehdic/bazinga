# Investigation Loop Management

**Purpose:** Orchestrator procedure for managing Investigator agent iterations
**When:** Tech Lead returns SPAWN_INVESTIGATOR
**Version:** 1.1 (post-review corrections applied)
**Source:** research/investigation-loop-template-ultrathink.md

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
    Log: "Resuming investigation | Iteration {current_iteration + 1} of 5"
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
Log: "MAX 4 developers active - queuing diagnostic"
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

**Route to Tech Lead validation** (per transitions.json: ROOT_CAUSE_FOUND → tech_lead)

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

**Route to Tech Lead partial review** (per transitions.json: INVESTIGATION_INCOMPLETE → tech_lead)

**TERMINATE orchestrator turn**

### Step 5c: BLOCKED

**Update state:**
```
investigation_state.status = "blocked"
investigation_state.blocker = {from investigator}
bazinga-db, please save state: ...
```

**Route to Tech Lead** (per transitions.json: BLOCKED → tech_lead)

Tech Lead will decide whether to:
- Provide resources/context to unblock
- Simplify task and close investigation
- Mark as external dependency (park task)

**TERMINATE orchestrator turn**

### Step 5d: EXHAUSTED

**Update state:**
```
investigation_state.status = "exhausted"
bazinga-db, please save state: ...
```

**Route to Tech Lead** (per transitions.json: EXHAUSTED → tech_lead)

Tech Lead will decide next steps for "all hypotheses eliminated" scenario.

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
| All hypotheses eliminated | All in matrix = eliminated | EXHAUSTED → Tech Lead |
| Session resumption | Active investigation in DB | Load state, continue from current iteration |

---

## Quick Reference: Status → Action

| From | Status | → To | Action |
|------|--------|------|--------|
| Tech Lead | SPAWN_INVESTIGATOR | Investigator | Initialize loop |
| Investigator | ROOT_CAUSE_FOUND | Tech Lead | Validate solution |
| Investigator | NEED_DEVELOPER_DIAGNOSTIC | Developer | Add instrumentation |
| Investigator | HYPOTHESIS_ELIMINATED | Investigator | Respawn (next iteration) |
| Investigator | NEED_MORE_ANALYSIS | Investigator | Respawn (next iteration) |
| Investigator | BLOCKED | Tech Lead | Handle blocker |
| Investigator | EXHAUSTED | Tech Lead | All hypotheses eliminated |
| Investigator | INVESTIGATION_INCOMPLETE | Tech Lead | Max iterations reached |
| Tech Lead (validation) | APPROVED | Developer | Implement fix |
| Tech Lead (validation) | CHANGES_REQUESTED | Investigator | Resume with feedback |

---

## References

- `agents/investigator.md` - Investigator agent definition
- `agents/tech_lead.md` - Tech Lead triggers and validation
- `workflow/transitions.json` - Status code routing (v1.1.0)
- `research/investigation-loop-template-ultrathink.md` - Design analysis
- `docs/INVESTIGATION_WORKFLOW.md` - Workflow diagrams
