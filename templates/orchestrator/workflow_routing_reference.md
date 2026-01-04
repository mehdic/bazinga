# Workflow Routing Reference

**This file contains the detailed workflow routing logic and progress tracking.**
**Read by orchestrator when routing agent responses.**

---

## §Workflow Routing (Deterministic)

**Purpose:** After receiving an agent response, use workflow-router to determine the next action deterministically.

**The workflow-router script (`.claude/skills/workflow-router/scripts/workflow_router.py`) determines:**
- Next agent to spawn based on current agent + status code
- Whether escalation is needed (revision count threshold)
- Whether QA should be skipped (testing_mode)
- Security-sensitive task handling

---

## When to Use Workflow-Router

**AFTER receiving ANY agent response:**
1. Extract status code from response (READY_FOR_QA, PASS, APPROVED, etc.)
2. Invoke workflow-router with current state
3. Follow the returned action

---

## Invocation

**Output parameters in conversation context:**
```
Current Agent: {developer|qa_expert|tech_lead|etc.}
Response Status: {READY_FOR_QA|PASS|FAIL|APPROVED|CHANGES_REQUESTED|etc.}
Session ID: {session_id}
Group ID: {group_id}
Testing Mode: {full|minimal|disabled}
```

**Then invoke:**
```
Skill(command: "workflow-router")
```

---

## Response Format

The skill returns JSON with:
```json
{
  "success": true,
  "next_agent": "qa_expert",
  "action": "spawn",
  "model": "sonnet",
  "group_id": "AUTH",
  "include_context": ["reasoning", "packages"]
}
```

**Use the returned `next_agent` and `action` to determine what to do next:**
- `action: spawn` → Build prompt for `next_agent` and spawn
- `action: merge` → Developer performs merge to initial_branch
- `action: check_phase` → Check if more groups need work

---

## Progress-Based Iteration Tracking (MANDATORY for Feedback Loops)

**When routing CHANGES_REQUESTED or FAIL back to Developer/SSE, you MUST track progress.**

### Step 0: Save Issue Events (CRITICAL for Validator)

**⚠️ Security Best Practice:** Use `--payload-file` and `--idempotency-key` for all events.

**After receiving Tech Lead response:**
```bash
# Write payload to temp file (avoid exposing in process table)
cat > /tmp/tl_issues.json << 'EOF'
{"group_id": "{group_id}", "iteration": {N}, "issues": [...], "blocking_count": {N}}
EOF
```

```
Skill(command: "bazinga-db-agents")

Request: save-event "{session_id}" "tl_issues" \
  --payload-file /tmp/tl_issues.json \
  --idempotency-key "{session_id}|{group_id}|tl_issues|{N}"
```

**After receiving Developer/SSE response to CHANGES_REQUESTED:**
```bash
# from_agent = "developer" or "senior_software_engineer"
cat > /tmp/dev_responses.json << 'EOF'
{"group_id": "{group_id}", "iteration": {N}, "from_agent": "{developer|senior_software_engineer}", "issue_responses": [...], "blocking_summary": {...}}
EOF
```

```
Skill(command: "bazinga-db-agents")

Request: save-event "{session_id}" "tl_issue_responses" \
  --payload-file /tmp/dev_responses.json \
  --idempotency-key "{session_id}|{group_id}|tl_issue_responses|{N}"
```

**After TL re-review (iteration > 1), save TL verdicts:**

Transform TL's `iteration_tracking` into tl_verdicts event:
```python
# Get IDs from TL handoff, lookup details from tl_issues
it = tl_handoff.get("iteration_tracking", {})
issues = {i["id"]: i for e in tl_issues_events for i in e.get("issues", [])}
verdicts = [{"issue_id": id, "verdict": "ACCEPTED", **{k: issues.get(id, {}).get(k, "") for k in ["location", "title"]}} for id in it.get("rejections_accepted", [])]
verdicts += [{"issue_id": id, "verdict": "OVERRULED", **{k: issues.get(id, {}).get(k, "") for k in ["location", "title"]}} for id in it.get("rejections_overruled", [])]
# Write to temp file, then save via:
# Skill(command: "bazinga-db-agents") → save-event {session_id} tl_verdicts \
#   --payload-file /tmp/tl_verdicts.json \
#   --idempotency-key "{session_id}|{group_id}|tl_verdicts|{N}"
```

---

### Step 0.5: Re-Rejection Prevention (MANDATORY for Iteration > 1)

**After TL sends CHANGES_REQUESTED (iteration > 1), validate no re-flagged accepted issues:**

**Data source: Query prior TL verdicts from DB (authoritative source)**

**Step 1: Get all TL verdicts for this session**
```
Skill(command: "bazinga-db-agents")

Request: get-events "{session_id}" "tl_verdicts"
```

**Step 2: Process the response (pseudocode)**
```python
# Parse skill output as JSON list of verdict events
all_verdicts = [...]  # From skill response

# Filter to this group's verdicts
all_prior_verdicts = [v for v in all_verdicts if v.get("group_id") == group_id]

# Step 3: Build set of previously ACCEPTED issues (closed, cannot be re-flagged)
previous_accepted = set()
for verdict_event in all_prior_verdicts:
    for verdict in verdict_event.get("verdicts", []):
        if verdict.get("verdict") == "ACCEPTED":
            # Use location|title for CROSS-ITERATION matching (issue_ids change per iteration)
            # Within same iteration: prefer issue_id matching
            # Cross-iteration: fall back to location|title as stable identifiers
            issue_key = f"{verdict.get('location', '')}|{verdict.get('title', '')}"
            previous_accepted.add(issue_key)

# Step 4: Check if TL is re-flagging any previously ACCEPTED issues
re_flagged = []
for issue in current_tl_handoff.get("issues", []):
    if issue.get("blocking"):
        issue_key = f"{issue.get('location', '')}|{issue.get('title', '')}"
        if issue_key in previous_accepted:
            re_flagged.append(issue.get("id"))
```

**IF re_flagged issues detected:**
```
⚠️ RE-REJECTION VIOLATION: {len(re_flagged)} issues re-flagged after ACCEPTED
→ Auto-accept these (cannot be re-flagged). Log warning for PM.
```

**Rationale:** Once TL accepts a rejection, it cannot be re-flagged. Prevents infinite review loops.

---

### Step 1: Read Handoff Files to Determine Progress

After receiving Developer/SSE response to CHANGES_REQUESTED:
```bash
# Simple mode: Read unified implementation handoff
cat bazinga/artifacts/{SESSION_ID}/{GROUP_ID}/handoff_implementation.json | jq '.blocking_summary'

# Parallel mode: Read agent-specific handoff
cat bazinga/artifacts/{SESSION_ID}/{GROUP_ID}/handoff_implementation_{AGENT_ID}.json | jq '.blocking_summary'
# Where AGENT_ID = task_group.assigned_to (e.g., "developer_1", "sse_1")
```

**⚠️ Backward Compatibility:** If handoff fields are missing, use these defaults:
```python
notes_for_future = handoff.get("notes_for_future", [])
blocking_summary = handoff.get("blocking_summary", {
    "total_blocking": 0, "fixed": 0, "rejected_with_reason": 0, "unaddressed": 0
})
iteration_tracking = handoff.get("iteration_tracking", {"iteration": 1})
```

**Progress is measured by "blocking_issues_remaining decreased", NOT "any fixes":**
```python
previous_blocking = db.blocking_issues_count  # From task_groups table
# Query via Skill(command: "bazinga-db-agents") → get-events, then flatten and count ACCEPTED
tl_accepted = sum(1 for e in tl_verdicts_events for v in e.get("verdicts", []) if v.get("verdict") == "ACCEPTED")
current_blocking = blocking_summary.total_blocking - blocking_summary.fixed - tl_accepted
# Progress: current_blocking < previous_blocking
```

After receiving QA FAIL response:
```bash
# Read QA's handoff
cat bazinga/artifacts/{SESSION_ID}/{GROUP_ID}/handoff_qa_expert.json | jq '.test_progression'
```

**QA progress is measured by "still_failing count decreased":**
```
previous_failing = {from prior QA handoff}
current_failing = len(test_progression.still_failing)

IF current_failing < previous_failing:
  → Progress made
ELSE:
  → No progress
```

---

### Step 2: Query Previous State from Database

**BEFORE comparing, query current state:**
```
Skill(command: "bazinga-db-workflow")

Request: get-task-groups "{session_id}"
```
Then filter to `{group_id}` and extract `{review_iteration, no_progress_count, blocking_issues_count}`.

**Extract values:**
```python
# Default to 1 (not 0) to match DB DEFAULT and avoid false first-iteration penalty
previous_iteration = db_result.get("review_iteration", 1)
previous_no_progress = db_result.get("no_progress_count", 0)
previous_blocking = db_result.get("blocking_issues_count", 0)
```

---

### Step 3: Calculate Progress and Update Database

**Calculate new values:**
```python
# Current blocking = total - fixed - TL-accepted rejections
# Query tl_verdicts events via Skill(command: "bazinga-db-agents") → get-events
# Then flatten verdicts from all events and count ACCEPTED
tl_verdicts_events = get_events(session_id, "tl_verdicts", group_id)
tl_accepted = sum(1 for e in tl_verdicts_events for v in e.get("verdicts", []) if v.get("verdict") == "ACCEPTED")
current_blocking = blocking_summary.total_blocking - blocking_summary.fixed - tl_accepted

# First-iteration exception (DB default=1)
if previous_iteration == 1:
    progress = True
    new_no_progress = 0
elif current_blocking == 0:
    # Zero blocking = progress
    progress = True
    new_no_progress = 0
elif current_blocking < previous_blocking:
    progress = True
    new_no_progress = 0  # Reset
else:
    progress = False
    new_no_progress = previous_no_progress + 1  # Increment

new_iteration = previous_iteration + 1
```

**Update via bazinga-db:**
```
Skill(command: "bazinga-db-workflow")

Request: update-task-group "{group_id}" "{session_id}" \
  --review_iteration {new_iteration} \
  --no_progress_count {new_no_progress} \
  --blocking_issues_count {current_blocking}
```

**Progress summary:**
- If `current_blocking < previous_blocking`: Reset `no_progress_count` to 0
- If `current_blocking >= previous_blocking`: Increment `no_progress_count` by 1
- Always increment `review_iteration` by 1

---

### Step 4: Check Escalation Rules

**Before spawning next agent, check if escalation is needed:**

```
IF no_progress_count >= 2 AND current_agent == "developer":
  → Spawn SSE instead (Developer stuck, escalate)

IF no_progress_count >= 2 AND current_agent == "senior_software_engineer":
  → Route to PM (SSE stuck, need PM decision)

IF review_iteration >= 5:
  → Escalate to next tier regardless (hard cap)

ELSE:
  → Continue normal feedback loop
```

---

### Step 5: Include Context in Re-spawn

**Config constant:** `MAX_ITERATIONS_BEFORE_ESCALATION = 4`

When spawning Developer/SSE for re-review (after CHANGES_REQUESTED), include escalation context:
```
Review Iteration: {review_iteration}
No-Progress Count: {no_progress_count}
Max Iterations Before Escalation: 4
Prior Issues: {list from prior handoff}
Developer Responses: {from implementation handoff}
```

**Dynamic warning injection:**
```
IF no_progress_count >= 2:
  Add to context: "⚠️ HIGH RISK: Next non-progress iteration escalates to SSE"

IF review_iteration >= 3:
  Add to context: "⚠️ FINAL ITERATION: Must resolve all blocking issues"
```

This allows:
- Developer to know urgency level
- See what was fixed vs what's pending
- Understand escalation risk
- Avoid raising new MEDIUM/LOW issues (prevents nitpick loops)

---

## Example Flow

```
1. TL sends CHANGES_REQUESTED with 3 blocking issues
2. Orchestrator updates DB: review_iteration=1, blocking_issues=3
3. Developer fixes 2, rejects 1
4. Orchestrator reads handoff: blocking_summary.fixed=2
5. Orchestrator updates DB: no_progress_count=0 (reset - progress made!), review_iteration=2
6. Orchestrator spawns TL for re-review with iteration context
7. TL validates: 2 fixed, 1 rejection accepted → APPROVED
```

---

## Fallback

If workflow-router returns an error or unknown transition:
- Log warning: `⚠️ Unknown transition: {agent} + {status}`
- Route to Tech Lead for manual handling (escalation fallback)
