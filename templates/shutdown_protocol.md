## 🚨 MANDATORY SHUTDOWN PROTOCOL - NO SKIPPING ALLOWED

**⚠️ CRITICAL**: When PM sends BAZINGA, you MUST complete ALL steps IN ORDER. This is NOT optional.

---

## 🔴🔴🔴 STEP 0: VALIDATOR GATE (CANNOT BE SKIPPED) 🔴🔴🔴

**THIS STEP IS MANDATORY. THE SHUTDOWN PROTOCOL CANNOT PROCEED WITHOUT IT.**

### 0.1: Check for Validator Verdict in Database

Before ANY shutdown step, query the database for a validator verdict:

**Request to bazinga-db skill:**
```
bazinga-db, get events for session [session_id] with type "validator_verdict" limit 1
```

**Then invoke:**
```
Skill(command: "bazinga-db")
```

**Parse the response:**

- **IF verdict event exists AND verdict = "ACCEPT":**
  ```
  ✅ Validator gate passed | Verdict: ACCEPT | Proceeding to shutdown
  ```
  → Continue to Step 1 (Get dashboard snapshot)

- **IF verdict event exists AND verdict = "REJECT":**
  ```
  ❌ Validator gate BLOCKED | Verdict: REJECT | Cannot proceed to shutdown
  ```
  → This should NOT happen (PM should have been respawned)
  → STOP immediately and respawn PM with rejection details

- **IF NO verdict event exists:**
  ```
  🚨 VALIDATOR NOT INVOKED | Shutdown blocked | Must invoke validator first
  ```
  → **HARD BLOCK: DO NOT PROCEED TO STEP 1**
  → Invoke validator immediately:
  ```
  Skill(command: "bazinga-validator")
  ```
  → After validator returns, re-check this gate

### 0.2: Log Validator Gate Check

After validator gate passes, log the check:

**Request to bazinga-db skill:**
```
bazinga-db, save event for session [session_id]:
  Event type: validator_gate_check
  Payload: {"passed": true, "verdict": "ACCEPT", "timestamp": "[ISO timestamp]"}
```

**Then invoke:**
```
Skill(command: "bazinga-db")
```

### 🚨 WHY THIS GATE EXISTS

**Problem:** Orchestrators may skip validator invocation due to:
- Context loss after many messages
- Role drift (acting as PM)
- Incorrect skill invocation syntax (`skill:` vs `command:`)

**Solution:** Hard runtime check that BLOCKS shutdown until validator verdict exists.

**This gate is NON-NEGOTIABLE. No exceptions. No bypasses.**

---

**🛑 MANDATORY CHECKLIST - Execute each step sequentially:**

```
SHUTDOWN CHECKLIST:
[ ] 0. ⚠️ VALIDATOR GATE - Verify validator_verdict event exists (HARD BLOCK)
[ ] 1. Get dashboard snapshot from database
[ ] 2. Detect anomalies (gaps between goal and actual)
[ ] 2.5. Git cleanup - Check for uncommitted/unpushed work:
    [ ] 2.5.1. Check git status for uncommitted changes
    [ ] 2.5.2. Commit uncommitted changes (if any)
    [ ] 2.5.3. Get current branch name
    [ ] 2.5.4. Check for unpushed commits
    [ ] 2.5.5. Push to remote (if needed)
    [ ] 2.5.6. Record git state in database
    [ ] 2.5.7. Display git cleanup success
[ ] 3. Read completion report template
[ ] 4. Generate detailed report file: bazinga/artifacts/{SESSION_ID}/completion_report.md
[ ] 5. Invoke velocity-tracker skill
[ ] 6. Save final orchestrator state to database
[ ] 7. Update session status to 'completed' with end_time
[ ] 8. Verify database writes succeeded
[ ] 9. ONLY THEN display success message to user
```

**❌ IF ANY STEP FAILS:**
- Log the failure
- Display error message, NOT success
- Session remains 'active', NOT 'completed'
- Do NOT proceed to next step

**Validation Before Accepting BAZINGA:**

**MANDATORY: Templated Rejection Messages (Prevent Role Drift)**

When rejecting BAZINGA, orchestrator MUST use structured templates. NEVER analyze code or suggest implementation details.

**Rejection Template Structure:**
```
❌ BAZINGA rejected (attempt {count}/3) | {reason} | {directive}
```

**Examples:**
- "❌ BAZINGA rejected (attempt 1/3) | No criteria in database | PM must extract criteria"
- "❌ BAZINGA rejected (attempt 2/3) | Evidence shows 44%, criterion requires >70% | PM must achieve target coverage"

**FORBIDDEN in rejection messages:**
- ❌ Code analysis ("The issue is in line 42...")
- ❌ Implementation suggestions ("Try using pytest-cov...")
- ❌ Debugging guidance ("Check if the config is...")

**ALLOWED in rejection messages:**
- ✅ What failed (criterion name, expected vs actual)
- ✅ What to fix (directive to PM, not implementation details)
- ✅ Rejection count (for escalation tracking)

**MANDATORY: Database-Verified Success Criteria Check**

When PM sends BAZINGA, orchestrator MUST independently verify via database (not trust PM's message):

```
if pm_message contains "BAZINGA":
    # Step 1: Initialize rejection tracking (if not exists)
    if "bazinga_rejection_count" not in orchestrator_state:
        orchestrator_state["bazinga_rejection_count"] = 0

    # Step 1.5: Token-aware safety valve (prevent session truncation)
    # Check if conversation is approaching token limit
    if estimated_token_usage() > 0.95:  # >95% token usage
        # Accept BAZINGA with warning, bypass strict verification
        → Display: "⚠️ BAZINGA accepted (token limit reached) | Strict validation bypassed to prevent session truncation | ⚠️ WARNING: Success criteria were not fully verified due to token exhaustion"
        → Log warning to database: "BAZINGA accepted under degraded mode (token exhaustion)"
        → Continue to shutdown protocol
        # Note: This prevents catastrophic failure where session ends before saving work

    # Step 2: Query database for success criteria (ground truth) with retry
    criteria = None
    for attempt in range(3):
        try:
            Request: "bazinga-db, get success criteria for session [session_id]"
            Command: get-success-criteria [session_id]
            Invoke: Skill(command: "bazinga-db")
            criteria = parse_database_response()
            break  # Success, exit retry loop
        except Exception as e:
            if attempt < 2:
                # Retry with exponential backoff
                wait_seconds = 2 ** attempt  # 1s, 2s
                → Log: "Database query failed (attempt {attempt+1}/3), retrying in {wait_seconds}s..."
                wait(wait_seconds)
                continue
            else:
                # All retries exhausted
                → ESCALATE: Display "❌ Database unavailable after 3 attempts | Cannot verify criteria | Options: 1) Wait and retry, 2) Manual verification"
                → Wait for user decision
                → DO NOT execute shutdown protocol

    # Check A: Criteria exist in database?
    if not criteria or len(criteria) == 0:
        # PM never saved criteria (skipped extraction)
        orchestrator_state["bazinga_rejection_count"] += 1
        count = orchestrator_state["bazinga_rejection_count"]

        if count > 2:
            → ESCALATE: Display "❌ Orchestration stuck | PM repeatedly failed to extract criteria | User intervention required"
            → Show user current state and options
            → Wait for user decision (exception to autonomy)
        else:
            → REJECT: Display "❌ BAZINGA rejected (attempt {count}/3) | No criteria in database | PM must extract criteria"
            → Spawn PM: "Extract success criteria from requirements, save to database, restart Phase 1"
        → DO NOT execute shutdown protocol

    # Check A.5: Validate criteria are specific and measurable
    for c in criteria:
        is_vague = (
            # Vague patterns that lack specific targets
            "improve" in c.criterion.lower() and ">" not in c.criterion and "<" not in c.criterion and "%" not in c.criterion
            or "make" in c.criterion.lower() and "progress" in c.criterion.lower()
            or "fix" in c.criterion.lower() and "all" not in c.criterion.lower() and "%" not in c.criterion.lower()
            or c.criterion.lower() in ["done", "complete", "working", "better"]
            or len(c.criterion.split()) < 3  # Too short to be specific
        )

        if is_vague:
            orchestrator_state["bazinga_rejection_count"] += 1
            count = orchestrator_state["bazinga_rejection_count"]

            if count > 2:
                → ESCALATE: Display "❌ Orchestration stuck | Vague criteria '{c.criterion}' | User intervention required"
            else:
                → REJECT: Display "❌ BAZINGA rejected (attempt {count}/3) | Criterion '{c.criterion}' is not measurable | Must include specific targets (e.g., 'Coverage >70%', 'All tests passing', 'Response time <200ms')"
                → Spawn PM: "Redefine criterion '{c.criterion}' with specific measurable target, update in database"
            → DO NOT execute shutdown protocol

    # Check B: Query database (ground truth), then validate

    Request: "bazinga-db, get success criteria for session [session_id]"
    Command: get-success-criteria [session_id]
    Invoke: Skill(command: "bazinga-db")

    criteria = parse_criteria_from_database_response()
    met_count = count(criteria where status="met")
    total_count = count(criteria where required_for_completion=true)

    IF met_count < total_count:
        orchestrator_state["bazinga_rejection_count"] += 1
        count = orchestrator_state["bazinga_rejection_count"]
        incomplete_criteria = [c for c in criteria if c.status != "met"]

        if count > 2:
            → ESCALATE: Display "❌ Orchestration stuck | Only {met_count}/{total_count} criteria met"
        else:
            → REJECT: Display "❌ BAZINGA rejected ({count}/3) | Incomplete: {met_count}/{total_count}"
            → Spawn PM: "Continue work. Incomplete: {list incomplete_criteria}"
        → DO NOT execute shutdown protocol, skip validator spawn

    try:
        # Invoke validator skill for independent verification
        # The validator returns a structured response with verdict
        Skill(command: "bazinga-validator")
        # In same message: "bazinga-validator, validate BAZINGA for session: {session_id}"

        # After skill completes, you receive validator_response containing:
        # "## BAZINGA Validation Result\n**Verdict:** ACCEPT|REJECT|CLARIFY"
        # Parse this response to determine next action:

        if "Verdict: ACCEPT" in validator_response or "**Verdict:** ACCEPT" in validator_response:
            orchestrator_state["bazinga_rejection_count"] = 0
            → Display: Extract completion message from validator_response
            → Continue to shutdown protocol

        elif "Verdict: REJECT" in validator_response or "**Verdict:** REJECT" in validator_response:
            orchestrator_state["bazinga_rejection_count"] += 1
            count = orchestrator_state["bazinga_rejection_count"]
            reason = parse_section(validator_response, "### Reason")
            action = parse_section(validator_response, "### Recommended Action")

            if count > 2:
                → ESCALATE: Display "❌ Orchestration stuck | BAZINGA rejected {count} times"
                → Show user: validator reason, criteria status
            else:
                → REJECT: Display "❌ BAZINGA rejected (attempt {count}/3) | {reason}"
                → Spawn PM: action
            → DO NOT execute shutdown protocol

        else:
            orchestrator_state["bazinga_rejection_count"] += 1
            → Display: "⚠️ Validator needs clarification"
            → Spawn PM: Extract clarification request from validator_response
            → DO NOT execute shutdown protocol

    except (ValidatorTimeout, ValidatorError, SkillInvocationError):
        # FALLBACK: Validator failed - trust PM's database state (lenient)
        → Display: "⚠️ Validator unavailable - trusting PM's database state"

        IF met_count == total_count:
            orchestrator_state["bazinga_rejection_count"] = 0
            → Display: "✅ BAZINGA ACCEPTED (database state, validator unavailable)"
            → Continue to shutdown protocol
        ELSE:
            orchestrator_state["bazinga_rejection_count"] += 1
            → REJECT: Display "❌ BAZINGA rejected | Incomplete: {met_count}/{total_count}"
            → Spawn PM: "Continue work. Validator unavailable, database shows incomplete."
            → DO NOT execute shutdown protocol
```

**The Rule**: Orchestrator verifies DATABASE (ground truth), not PM's message. Tracks rejection count to prevent infinite loops. Escalates to user after 3 rejections.

### Step 1: Get Dashboard Snapshot

Query complete metrics from database:

**Request to bazinga-db skill:**
```
bazinga-db, please provide dashboard snapshot:

Session ID: [current session_id]
```

**Then invoke:**
```
Skill(command: "bazinga-db")
```

**IMPORTANT:** You MUST invoke bazinga-db skill here. Use the returned data. Simply do not echo the skill response text in your message to user.


The dashboard snapshot returns:
- pm_state, orch_state, task_groups
- token_usage, recent_logs
- All skill outputs (security_scan, test_coverage, lint_check, velocity_tracker, etc.)

### Step 2: Detect Anomalies

Check for issues requiring attention:
- High revision counts (> 2)
- Coverage gaps (< 80%)
- Unresolved security issues
- Build health regressions
- Excessive token usage

Flag any anomalies for inclusion in reports.

### Step 2.5: Git Cleanup - Commit and Push Uncommitted Work

**⚠️ MANDATORY: Ensure all code is committed and pushed before completion**

Before generating the final report, verify all work is saved to the remote repository.

#### Sub-step 2.5.1: Check Git Status

**Check for uncommitted changes:**
```bash
git status --porcelain
```

**Parse the output:**
- If empty: No uncommitted changes, proceed to Step 2.5.4 (push check)
- If not empty: Uncommitted changes detected, proceed to Step 2.5.2

#### Sub-step 2.5.2: Commit Uncommitted Changes

**If uncommitted changes found:**

Display to user (capsule format):
```
💾 Git cleanup | Uncommitted changes detected | Committing work to feature branch
```

**Analyze changes and create commit message:**
```bash
# Get list of modified/new files
git status --short

# Create descriptive commit message based on PM's final assessment
# Format: "feat: [brief description from PM summary]"
# Example: "feat: Implement JWT authentication with test coverage"
```

**Commit the changes:**
```bash
git add .
git commit -m "$(cat <<'EOF'
[Commit message from PM summary]

Orchestration session: [SESSION_ID]
Completed by: Claude Code Multi-Agent Dev Team
Mode: [SIMPLE/PARALLEL]
Groups: [N] completed
EOF
)"
```

**Error handling:**
- If commit fails: Output error capsule and STOP (cannot complete without saving work)
- Error message: `❌ Git commit failed | [error_details] | Cannot proceed - work not saved`

#### Sub-step 2.5.3: Get Current Branch Name

**Extract the branch name:**
```bash
CURRENT_BRANCH=$(git branch --show-current)
echo "Current branch: $CURRENT_BRANCH"
```

**Verify it matches the session branch pattern:**
- Branch should start with `claude/`
- Branch should end with session ID or follow required pattern
- If mismatch: Log warning but continue (may be intentional)

#### Sub-step 2.5.4: Check for Unpushed Commits

**Check if local branch is ahead of remote:**
```bash
# Fetch remote to get latest state
git fetch origin $CURRENT_BRANCH 2>/dev/null || true

# Check if there are unpushed commits
git rev-list @{u}..HEAD --count 2>/dev/null || echo "0"
```

**Parse the result:**
- If count > 0: Unpushed commits exist, proceed to Step 2.5.5
- If count = 0 AND no uncommitted changes from Step 2.5.1: All work already pushed, proceed to Step 3
- If error (no remote tracking): Branch needs initial push, proceed to Step 2.5.5

#### Sub-step 2.5.5: Push to Remote

**Display to user (capsule format):**
```
📤 Pushing to remote | Branch: [branch_name] | Saving work to remote repository
```

**Push the branch:**
```bash
git push -u origin $CURRENT_BRANCH
```

**Retry logic (network resilience):**
- If push fails due to network errors: Retry up to 4 times with exponential backoff (2s, 4s, 8s, 16s)
- Example: `sleep 2 && git push -u origin $CURRENT_BRANCH`
- If push fails due to 403/permission: Output specific error and STOP

**Error handling:**
- If push fails after retries: Output error capsule and STOP
- Error message: `❌ Git push failed | [error_details] | Cannot proceed - work not saved to remote`
- Common 403 error: `❌ Git push failed | HTTP 403 - branch name doesn't match session pattern | Check branch name starts with 'claude/' and ends with session ID`

#### Sub-step 2.5.6: Record Git State in Database

**After successful commit/push, record final state:**

**Request to bazinga-db skill:**
```
bazinga-db, please save git state:

Session ID: [current session_id]
State Type: git_final
State Data: {
  "branch": "[CURRENT_BRANCH]",
  "commit_sha": "[git rev-parse HEAD]",
  "commit_message": "[last commit message]",
  "pushed_to_remote": true,
  "push_timestamp": "[ISO timestamp]",
  "uncommitted_changes": false
}
```

**Then invoke:**
```
Skill(command: "bazinga-db")
```

**Verification:**
- ✅ Git state saved to database
- ✅ Branch name recorded for user reference
- ✅ Commit SHA available for traceability

#### Sub-step 2.5.7: Display Git Cleanup Success

**Display to user (capsule format):**
```
✅ Git cleanup complete | All changes committed and pushed to [branch_name] | Work saved to remote
```

**This message confirms:**
- All uncommitted work has been committed
- All commits have been pushed to remote
- Branch name is available for merging to main
- Work is safely stored and won't be lost

**AFTER successful git cleanup: IMMEDIATELY continue to Step 3 (Generate Detailed Report). Do NOT stop.**

### Step 3: Generate Detailed Report

Create comprehensive report file:

```
bazinga/artifacts/{SESSION_ID}/completion_report.md
```

See `bazinga/templates/completion_report.md` for full report structure.

Report includes:
- Session summary (mode, duration, groups)
- Git state (branch, commit SHA, push status)
- Quality metrics (security, coverage, lint, build)
- Efficiency metrics (approval rate, escalations)
- Task groups breakdown
- Skills usage summary
- Anomalies detected
- Token usage & cost estimate

### Step 4: Update Database

**⚠️ MANDATORY: Save final orchestrator state and update session**

This step has TWO required sub-steps that MUST both be completed:

#### Sub-step 4.1: Save Final Orchestrator State

**Request to bazinga-db skill:**
```
bazinga-db, please save the orchestrator state:

Session ID: [current session_id]
State Type: orchestrator
State Data: {
  "status": "completed",
  "end_time": [timestamp],
  "duration_minutes": [duration],
  "completion_report": [report_filename],
  "current_phase": "completion",
  "iteration": [final iteration count],
  "total_spawns": [total agent spawns]
}
```

**Then invoke:**
```
Skill(command: "bazinga-db")
```


#### Sub-step 4.2: Update Session Status to Completed

**Request to bazinga-db skill:**
```
bazinga-db, please update session status:

Session ID: [current session_id]
Status: completed
End Time: [timestamp]
```

**Then invoke:**
```
Skill(command: "bazinga-db")
```


**Verification Checkpoint:**
- ✅ Orchestrator final state saved (1 invocation)
- ✅ Session status updated to 'completed' (1 invocation)
- ✅ Both invocations returned success responses

**CRITICAL:** You MUST complete both database operations before proceeding to Step 5. The dashboard and metrics depend on this final state being persisted.


### Step 5: Display Concise Report

Output to user (keep under 30 lines):

See `bazinga/templates/completion_report.md` for Tier 1 report format.

Display includes:
- Mode, duration, groups completed
- Quality overview (security, coverage, lint, build)
- Skills used summary
- Efficiency metrics (approval rate, escalations)
- Anomalies (if any)
- Link to detailed report file

Example output:
```
═══════════════════════════════════════════════════════════
✅ BAZINGA - Orchestration Complete!
═══════════════════════════════════════════════════════════

**Mode**: SIMPLE (1 developer)
**Duration**: 12 minutes
**Groups**: 1/1 completed ✅

**Git Status**: All changes committed and pushed ✅
**Branch**: claude/auto-commit-merge-trigger-01SmpxrBC61DeJU7PAEthhTh
**Latest Commit**: a3f9b21 - feat: Implement JWT authentication with test coverage

**Quality**: All checks passed ✅
**Skills Used**: 6 of 11 available
**Detailed Report**: bazinga/artifacts/bazinga_20250113_143530/completion_report.md

**Next Steps**: Merge branch to main when ready
═══════════════════════════════════════════════════════════
```

---
## Summary

**Mode**: {mode} ({num_developers} developer(s))
**Duration**: {duration_minutes} minutes
**Groups**: {total_groups}/{total_groups} completed ✅
**Token Usage**: ~{total_tokens/1000}K tokens (~${estimated_cost})

## Quality Overview

**Security**: {security_status} ({security_summary})
**Coverage**: {coverage_status} {coverage_avg}% average (target: 80%)
**Lint**: {lint_status} ({lint_summary})
**Build**: {build_health["final"]}

## Skills Used

{Query bazinga-db skill for skill outputs from this session}
{Get skill results from skill_outputs table in database}

**Skills Invoked**: {count} of 11 available
{FOR each Skill that ran}:
- **{skill_name}**: {status_emoji} {status} - {brief_summary}
{END FOR}

{Examples of status display}:
- **security-scan**: ✅ Success - 0 vulnerabilities found
- **lint-check**: ✅ Success - 12 issues fixed
- **test-coverage**: ✅ Success - 87.5% average coverage
- **velocity-tracker**: ✅ Success - 12 points completed
- **codebase-analysis**: ✅ Success - Found 3 similar patterns
- **pattern-miner**: ⚠️ Partial - Limited historical data

📁 **Detailed results**: See `bazinga/` folder for full JSON outputs

## Efficiency

**First-time approval**: {approval_rate}% ({first_time_approvals}/{total_groups} groups)
**Model escalations**: {groups_escalated_opus} group(s) → Opus at revision 3+
**Scan escalations**: {groups_escalated_scan} group(s) → advanced at revision 2+

{IF anomalies exist}:
## Attention Required

{FOR each anomaly}:
⚠️ **{anomaly.title}**: {anomaly.message}
   - {anomaly.details}
   - Recommendation: {anomaly.recommendation}

## Detailed Report

📊 **Full metrics and analysis**: `{report_filename}`

═══════════════════════════════════════════════════════════
```

---
