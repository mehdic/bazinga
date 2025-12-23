# Orchestrator Role Drift Prevention: Deep Analysis

**Date:** 2025-12-09
**Updated:** 2025-12-09 (finalized with all approvals)
**Context:** Two types of orchestrator role drift observed
**Decision:** Approved - 12 layers across Type 1 and Type 2
**Status:** Ready for Implementation
**Reviewed by:** OpenAI GPT-5

---

## Problem Statement

The BAZINGA orchestrator is designed as a **coordinator-only** agent that spawns specialized agents (Developer, QA Expert, Tech Lead, Investigator) to perform actual work. We have observed **two distinct types of role drift**:

### Drift Type 1: Direct Implementation (Previously Analyzed)

The orchestrator directly executed work instead of spawning agents:

1. Directly executed `git push origin main`
2. Made curl requests to GitHub API to check CI status
3. Read `.env` files for credentials
4. Downloaded and analyzed CI logs
5. Drew conclusions about whether failures were pre-existing

**Violation:** "I coordinate agents, I do not implement."

### Drift Type 2: Premature BAZINGA Acceptance (NEW)

The orchestrator accepted PM's scope reduction without validation:

**Observed Failure:**
- User requested: "implement the tasks left in tasks8.md" (69 tasks across 4 releases)
- PM narrowed scope to Release 1 only (~18 tasks) without authorization
- PM sent BAZINGA after Release 1
- Orchestrator accepted BAZINGA without invoking validator
- Result: 51 tasks (Releases 2-4) left unimplemented

**Transcript excerpt:**
```
PM: "Release 1: Stabilize Core Foundation is complete"
PM: "T8-011 deferred to Release 2+"
PM: "Status: BAZINGA"

Orchestrator: [Accepted BAZINGA without validation] ← WRONG!
```

**Violation:** "Orchestrator is the FINAL CHECKPOINT - don't trust PM blindly"

**The safeguard existed but wasn't used:**
```
bazinga-validator skill:
"Validates BAZINGA completion claims with independent verification.
Spawned ONLY when PM sends BAZINGA. Acts as final quality gate."
```

### Root Cause Analysis

**Type 1 - Why direct implementation occurred:**

1. **Implicit workflow gap**: The merge step says "Spawn Developer (merge task)" but lacks explicit spawn template
2. **Natural extension trap**: "Verify merge worked" naturally leads to "check CI" which leads to "analyze failures"
3. **No enforcement mechanism**: Rules are instructional only - no structural barriers
4. **Missing scenario coverage**: Role drift examples don't cover merge/CI monitoring case
5. **Long conversation decay**: After many messages, the coordinator identity weakens
6. **Ambiguous boundaries**: "Bash for init only" doesn't enumerate what counts as init

**Type 2 - Why premature BAZINGA was accepted:**

1. **Over-deference to PM**: Orchestrator follows "PM decides everything" without questioning scope changes
2. **Missing scope validation**: No mechanism to compare PM's completion claim against original user request
3. **Validator not invoked**: bazinga-validator skill exists but orchestrator didn't invoke it
4. **Scope narrowing not flagged**: PM reduced scope from 69 tasks to 18 without user approval
5. **Release boundary confusion**: PM optimized for "clean stopping point" rather than full task completion

### Impact

**Type 1 Impact:**
- Orchestrator consumes tokens doing work agents should do
- Loses architectural benefits of specialized agents
- Breaks the audit trail (work not logged as agent interactions)

**Type 2 Impact:**
- **User request not fulfilled** - Only 26% of tasks completed (18/69)
- **Silent scope reduction** - User not informed of PM's decision to defer
- **Trust violation** - System appeared to complete but left 51 tasks undone
- **No recovery mechanism** - User had to manually discover the gap

---

## Approved Solution: Multi-Layer Defense Strategy

### Layer 1: Explicit Scenario Coverage (Documentation) ✅ APPROVED

**Add merge/CI monitoring to Role Drift Prevention section in `agents/orchestrator.md`:**

```markdown
**Scenario 3: Post-merge CI monitoring**

❌ **WRONG (Role Drift):**
```
Tech Lead: APPROVED
Orchestrator: Let me push to main and check CI...
[runs git push, curl to GitHub API, analyzes logs]
```

✅ **CORRECT (Coordinator):**
```
Tech Lead: APPROVED
[Spawns Developer with merge task]
Developer: MERGE_SUCCESS, CI status: 2 workflows running
[If detailed CI analysis needed]
[Spawns Investigator for CI analysis]
Investigator: CI failures pre-existing (babel-plugin-istanbul issue)
[Routes findings to PM]
```

**Scenario 4: External API interaction**

❌ **WRONG:** Orchestrator runs `curl` to GitHub/external APIs
✅ **CORRECT:** Spawn Investigator for any external data gathering

**Scenario 5: PM sends BAZINGA (NEW - Type 2 Drift)**

❌ **WRONG (Premature Acceptance):**
```
PM: "Release 1 complete. Status: BAZINGA"
Orchestrator: ✅ BAZINGA received! Orchestration complete.  ← WRONG! No validation
```

✅ **CORRECT (Mandatory Validation):**
```
PM: "Release 1 complete. Status: BAZINGA"
Orchestrator: 🔍 BAZINGA received - invoking validator...
[Invokes Skill(command: "bazinga-validator")]
Validator: REJECT - Original scope was 69 tasks, only 18 completed
Orchestrator: ⚠️ Validation failed - spawning PM with rejection details
[Spawns PM with validator feedback]
```

**Scenario 6: PM considers scope reduction (NEW - Type 2 Drift)**

❌ **WRONG (Any Scope Reduction):**
```
PM: "This is too large. I'll do Release 1 now, defer rest to later."
PM: [Proceeds with Release 1 only]  ← WRONG! Scope reduction forbidden
```

❌ **ALSO WRONG (Asking to Reduce):**
```
PM: "Can we reduce scope to Release 1 only?"  ← WRONG! Don't even ask
```

✅ **CORRECT (Complete Full Scope):**
```
PM: "User requested tasks8.md - 69 tasks across 4 releases"
PM: "Planning for FULL scope execution"
PM: [Creates task groups for ALL 69 tasks]
PM: [Continues until ALL 69 tasks complete]
PM: "Status: BAZINGA" [only after 100% completion]
```
```

### Layer 2: Enhanced Merge Workflow Template ✅ APPROVED

**Enhance existing `templates/merge_workflow.md`** (NOT create new file):

Add explicit Developer spawn template with CI monitoring (60-second polling):

```markdown
### Developer Merge Task with CI Monitoring

Task(
  subagent_type: "general-purpose",
  model: MODEL_CONFIG["developer"],
  description: "Developer: merge and verify CI",
  prompt: """
You are a Developer performing a MERGE TASK.

## Your Task
1. Merge the approved changes to {initial_branch}
2. Push to remote
3. Monitor CI status (poll every 60 seconds, up to 5 minutes)
4. Report back with status

## Required Actions
- git merge or git rebase as appropriate
- git push origin {initial_branch}
- Check CI workflow status via GitHub API or gh CLI
- Poll CI status every 60 seconds until complete or timeout

## Your Response Format
Return ONE of these statuses (use existing codes only):

**MERGE_SUCCESS**
- Merge completed successfully
- CI status: [passing/running/not configured]
- Summary: [brief description]
- Note: If CI has pre-existing failures unrelated to our changes, report MERGE_SUCCESS with note in summary

**MERGE_CONFLICT**
- Conflicts in: [list files]
- Suggested resolution: [brief guidance]

**MERGE_TEST_FAILURE**
- CI failures detected that ARE related to our changes
- Failing workflows: [list]
- Error summary: [brief description]

**MERGE_BLOCKED**
- Cannot proceed (environment issue, missing deps, CI blocked)
- Blocker reason: [description]
"""
)
```

**Key changes:**
- CI polling every 60 seconds (user requirement)
- No new status codes - use existing 4 statuses
- Pre-existing CI failures noted in MERGE_SUCCESS summary (not separate status)

### Layer 3: Bash Command Allowlist with Wrapper Script ✅ APPROVED (Option B)

**Replace vague "Bash for init only" with explicit allowlist + build-baseline wrapper:**

```markdown
### 🚨 BASH COMMAND ALLOWLIST (EXHAUSTIVE)

**You may ONLY execute these Bash patterns:**

| Pattern | Purpose | Example |
|---------|---------|---------|
| `SESSION_ID=bazinga_$(date...)` | Generate session ID | Init only |
| `mkdir -p bazinga/artifacts/...` | Create directories | Init only |
| `mkdir -p bazinga/...` | Create bazinga subdirs | Init only |
| `test -f bazinga/...` | Check file existence | Config checks |
| `cat bazinga/*.json` | Read config files | Use Read tool instead when possible |
| `kill -0 $(cat bazinga/dashboard.pid)` | Dashboard check | Init only |
| `bash bazinga/scripts/start-dashboard.sh` | Start dashboard | Init only |
| `bash bazinga/scripts/build-baseline.sh` | Run build baseline | Init only (Step 6) |

**ANY command not matching above patterns → STOP → Spawn agent**

**Explicitly FORBIDDEN (spawn agent instead):**
- `git *` → Spawn Developer
- `curl *` → Spawn Investigator
- `npm *`, `yarn *`, `pnpm *` → Spawn Developer or QA (except via build-baseline.sh)
- `python *`, `pytest *` → Spawn QA Expert
- `cat` on non-bazinga paths → Spawn agent to read
- Any command with credentials/tokens → Spawn agent
```

**Implementation:** Create `bazinga/scripts/build-baseline.sh` wrapper that:
- Detects project language
- Runs appropriate build command
- Saves results to `bazinga/artifacts/{SESSION_ID}/build_baseline.log`
- Returns exit code for orchestrator to check

### Layer 4: Single Policy Gate (Referenced, Not Duplicated) ✅ APPROVED

**Add ONE policy gate section in `agents/orchestrator.md`, then reference from phase templates:**

In `agents/orchestrator.md`:
```markdown
### §Policy-Gate: Pre-Bash Validation

**Before EVERY Bash tool invocation, verify:**

1. Is this command in the §Bash Command Allowlist?
2. Would a Developer/QA/Investigator normally do this?

**IF command not in allowlist OR agent should do it:**
→ STOP → Identify correct agent → Spawn that agent

**This check is NON-NEGOTIABLE.**
```

In `phase_simple.md` and `phase_parallel.md`:
```markdown
**Before any Bash command:** See §Policy-Gate in orchestrator.md
```

### Layer 5: Runtime Enforcement Comment ✅ APPROVED

**Add at top of `agents/orchestrator.md`:**

```markdown
<!--
🚨 RUNTIME ENFORCEMENT ANCHOR 🚨

If you find yourself about to:
- Run a git command → STOP → Spawn Developer
- Call an external API → STOP → Spawn Investigator
- Analyze logs/output → STOP → Spawn appropriate agent
- Read code files → STOP → Spawn agent to read

The ONLY exception is the explicit ALLOWLIST in §Bash Command Allowlist.

This comment exists because role drift is the #1 orchestrator failure mode.
-->
```

---

## NEW: Type 2 Drift Prevention (Premature BAZINGA)

### Layer 6: Mandatory Validator Invocation ⏳ PROPOSED

**Problem:** Orchestrator accepted PM's BAZINGA without validation

**Solution:** Make bazinga-validator invocation MANDATORY and AUTOMATIC when PM sends BAZINGA.

**Add to `agents/orchestrator.md` in the BAZINGA handling section:**

```markdown
### 🚨 MANDATORY BAZINGA VALIDATION (NON-NEGOTIABLE)

When PM sends BAZINGA:

**Step 1: IMMEDIATELY invoke validator (before ANY completion output)**
```
Skill(command: "bazinga-validator")
```

**Step 2: Wait for validator verdict**
- IF ACCEPT → Proceed to completion
- IF REJECT → Spawn PM with validator's failure details

**⚠️ CRITICAL: You MUST NOT:**
- ❌ Accept BAZINGA without invoking validator
- ❌ Output completion messages before validator returns
- ❌ Trust PM's completion claims without independent verification

**The validator checks:**
1. Original user request scope vs completed scope
2. All task groups marked complete
3. Test evidence exists and passes
4. No deferred items without user approval
```

### Layer 7: Scope Tracking at Session Start ⏳ PROPOSED

**Problem:** No mechanism to compare PM's completion against original request

**Solution:** Store original scope at session initialization and validate against it.

**Add to orchestrator initialization (Step 0):**

```markdown
### Step 0.1: Store Original Scope

**MANDATORY: Extract and store the user's original request scope**

When creating session in database, include:
```
bazinga-db, please create a new orchestration session:

Session ID: $SESSION_ID
Mode: simple
Requirements: [User's requirements from input]
Original_Scope: {
  "raw_request": "[exact user request text]",
  "scope_type": "file|feature|task_list|description",
  "scope_reference": "[file path or feature name if applicable]",
  "estimated_items": [count if determinable, null otherwise]
}
```

**The validator uses this to verify:**
- Did PM complete the original scope?
- Were any items deferred without user approval?
- Does completion % match expectations?
```

### Layer 8: Scope Reduction FORBIDDEN ⏳ PROPOSED

**Problem:** PM reduced scope from 69 tasks to 18 without authorization

**Solution:** PM CANNOT reduce scope. Period. No asking, no deferring, no "clean stopping points".

**Add to PM agent definition (`agents/project_manager.md`):**

```markdown
### 🚨 SCOPE IS IMMUTABLE (NON-NEGOTIABLE)

**You CANNOT reduce the scope of the user's request.**

**FORBIDDEN actions:**
- ❌ Deferring tasks to "later releases"
- ❌ Prioritizing a subset and ignoring the rest
- ❌ Optimizing for "clean stopping points"
- ❌ Asking user if they want to reduce scope
- ❌ Assuming large requests should be broken into phases

**REQUIRED behavior:**
- ✅ Complete ALL tasks in the original request
- ✅ If request references a file (tasks8.md), complete ALL items in that file
- ✅ If request is "implement feature X", implement the COMPLETE feature
- ✅ Plan for full scope, execute full scope, report full scope completion

**Examples of VIOLATIONS:**
- User requests "implement tasks8.md" (69 tasks) → PM does Release 1 only (18 tasks) ❌
- User requests "add authentication" → PM skips 2FA "for later" ❌
- User requests "fix all bugs in backlog" → PM does P0 only ❌

**If the scope is genuinely impossible:**
- Return status: BLOCKED with detailed explanation
- DO NOT proceed with partial scope
- Let user decide how to proceed

**The user defines scope. You execute it. You don't negotiate it.**
```

### Layer 9: Validator Scope Check Enhancement ⏳ PROPOSED

**Problem:** bazinga-validator may not check scope alignment

**Solution:** Enhance validator to explicitly check original vs completed scope.

**Add to bazinga-validator skill (`/.claude/skills/bazinga-validator/SKILL.md`):**

```markdown
### Scope Validation (MANDATORY)

**Step 1: Retrieve original scope**
```
bazinga-db, get session [session_id] original_scope
```

**Step 2: Compare against completion**
- If scope_type = "file": Did PM complete all items in the file?
- If scope_type = "task_list": What % of tasks completed?
- If scope_type = "feature": Is the feature fully implemented?

**Step 3: Flag scope reduction**
- If completed < 90% of original scope → REJECT with reason
- If items were deferred without user approval → REJECT with reason

**Rejection message format:**
```
REJECT: Scope mismatch

Original request: [user's exact request]
Completed: [what was actually done]
Missing: [what was not done]
Completion %: [X]%

PM deferred the following without user approval:
- [list of deferred items]

Recommendation: Return to PM for full scope completion or explicit user approval for reduced scope.
```
```

---

## Rejected Proposals

### ❌ New Status Code `MERGE_CI_PREEXISTING`
**Reason:** Would break existing parsers and routing templates. Instead, pre-existing CI failures are noted in the summary field of MERGE_SUCCESS.

### ❌ Artifact-Driven CI Validation (No API Calls)
**Reason:** User wants Developer to actively poll CI status every 60 seconds via API. This is acceptable since it's the Developer agent doing it, not the orchestrator.

### ❌ New Template File `phase_merge.md`
**Reason:** Consolidate into existing `merge_workflow.md` to avoid template proliferation.

### ❌ Post-Hoc Drift Detection via Tool Audit
**Reason:** User declined. Preventive measures deemed sufficient.

---

## Implementation Plan

### Files to Modify

| File | Changes | Drift Type |
|------|---------|------------|
| `agents/orchestrator.md` | Add Scenario 3-6, §Bash Command Allowlist, §Policy-Gate, Runtime Comment, §Mandatory BAZINGA Validation | Type 1 + 2 |
| `agents/project_manager.md` | Add §Scope Immutable, §PM BAZINGA Format | Type 2 |
| `templates/merge_workflow.md` | Add enhanced Developer merge prompt with 60s CI polling | Type 1 |
| `templates/orchestrator/phase_simple.md` | Add reference to §Policy-Gate | Type 1 |
| `templates/orchestrator/phase_parallel.md` | Add reference to §Policy-Gate | Type 1 |
| `templates/response_parsing.md` | Add PM BAZINGA Completion Summary parsing | Type 2 |
| `templates/message_templates.md` | Add progress tracking to capsule format | Type 2 |
| `.claude/skills/bazinga-validator/SKILL.md` | Add §Scope Validation, log verdicts to DB | Type 2 |
| `bazinga-db schema` | Add `original_scope`, `completed_items_count` fields | Type 2 |
| **NEW:** `bazinga/scripts/build-baseline.sh` | Wrapper script for build baseline check | Type 1 |

### Implementation Order

**Phase A: Type 1 Drift Prevention (Approved)**
1. **Scenario 3 & 4** → `agents/orchestrator.md` (immediate)
2. **Enhanced merge prompt** → `merge_workflow.md` (immediate)
3. **§Policy-Gate section** → `agents/orchestrator.md` (immediate)
4. **§Bash Command Allowlist** → `agents/orchestrator.md` (immediate)
5. **Runtime comment** → `agents/orchestrator.md` (immediate)
6. **Phase template references** → phase_simple.md, phase_parallel.md
7. **Build baseline wrapper** → `bazinga/scripts/build-baseline.sh`

**Phase B: Type 2 Drift Prevention (Approved)**
8. **Scenario 5 & 6** → `agents/orchestrator.md`
9. **§Mandatory BAZINGA Validation** → `agents/orchestrator.md` (uses `Skill(command: "bazinga-validator")`)
10. **§Scope Immutable** → `agents/project_manager.md` (scope reduction FORBIDDEN)
11. **original_scope field** → bazinga-db schema migration
12. **§Scope Validation** → bazinga-validator skill
13. **PM BAZINGA Format** → `agents/project_manager.md` + `templates/response_parsing.md`
14. **Progress Tracking** → `templates/message_templates.md` + orchestrator state

### Estimated Changes

| File | Lines Added | Lines Modified | Priority |
|------|-------------|----------------|----------|
| orchestrator.md | ~100 | ~10 | High |
| project_manager.md | ~30 | ~5 | High |
| merge_workflow.md | ~30 | ~5 | Medium |
| phase_simple.md | ~3 | 0 | Low |
| phase_parallel.md | ~3 | 0 | Low |
| bazinga-validator SKILL.md | ~40 | ~10 | High |
| build-baseline.sh (new) | ~40 | N/A | Medium |

---

## Multi-LLM Review Integration

### Reviewer
- OpenAI GPT-5 (Gemini skipped)

### Consensus Points Incorporated

1. **Consolidate on existing merge_workflow.md** - Avoid template proliferation
2. **Don't introduce new status codes** - Keep parser compatibility
3. **Reconcile Bash allowlist with build baseline** - Use wrapper script (Option B)
4. **Single policy gate referenced everywhere** - Reduce duplication and token usage

### User Modifications

1. **CI monitoring via API polling** - Developer polls every 60 seconds (user preference over artifact-driven)
2. **No post-hoc drift detection** - User declined this layer
3. **Scope reduction FORBIDDEN** - PM cannot reduce scope, not even ask (stricter than LLM suggested)

### LLM Suggestions - User Decisions (Type 2)

| Suggestion | Decision | Reason |
|------------|----------|--------|
| Replace build-baseline.sh with skill | ❌ NO | Keep wrapper script approach |
| Create ci-status-skill for multi-provider | ❌ NO | GitHub-only is acceptable |
| PM saves scope_universe during planning | 📋 LATER | Too complex for now, revisit later |
| Validator always runs tests if files exist | ❌ NO | Keep current behavior |
| Log validator verdicts to bazinga-db | ✅ YES | Add audit trail |
| Pre-existing CI failures require baseline diff | ✅ YES | Objective classification |

### Rejected LLM Suggestions

1. **Delegate build baseline to QA Expert** - User chose wrapper script approach instead
2. **Post-hoc tool audit** - User declined
3. **Replace Bash with skills** - Keep build-baseline.sh wrapper
4. **Multi-provider CI skill** - GitHub-only sufficient
5. **Auto-run tests if files exist** - Keep explicit criteria

---

## Additional Proposals (Non-LLM)

### Proposal A: PM BAZINGA Format Enforcement ✅ APPROVED

**Problem:** PM's BAZINGA message was vague - no explicit completion counts

**Solution:** Require PM to include explicit completion statistics:

**Add to PM agent definition (`agents/project_manager.md`):**

```markdown
### PM BAZINGA Response Format (MANDATORY)

When sending BAZINGA, you MUST include a Completion Summary section:

## PM Status: BAZINGA

### Completion Summary
- Completed_Items: [count]
- Total_Items: [count from original request]
- Completion_Percentage: [X]%
- Deferred_Items: [] (MUST be empty unless BLOCKED)

### Final Report
[existing report content]
```

**Update `templates/response_parsing.md`:**

```markdown
### PM BAZINGA Parsing

When PM sends BAZINGA, extract Completion Summary:
- Look for "### Completion Summary" section
- Extract Completed_Items, Total_Items, Completion_Percentage
- Verify Deferred_Items is empty (if not empty → validation fails)
```

**Impact:** Makes scope visible in BAZINGA claim, validator can verify counts

### Proposal B: Pre-Validator Sanity Check ❌ REJECTED

**Reason:** User declined. Validator invocation is sufficient.

### Proposal C: Progress Tracking in Status Messages ✅ APPROVED

**Problem:** User had no visibility into scope completion during execution

**Solution:** Include progress in orchestrator capsules throughout execution.

**Implementation:**

**Step 1: Store total_items at session start (in original_scope)**
```json
{
  "raw_request": "implement tasks8.md",
  "scope_type": "file",
  "scope_reference": "docs/tasks8.md",
  "total_items": 69
}
```

**Step 2: Track completed_items in orchestrator state**
- Add `completed_items_count` field to orchestrator state
- Increment as groups complete

**Step 3: Update capsule format in `templates/message_templates.md`**

```markdown
### Group Completion Capsule (with progress)

**Format:**
✅ Group {id} complete | {summary} | Progress: {completed}/{total} ({percentage}%) | → {next_step}

**Examples:**
✅ Group A complete | JWT auth | Progress: 5/69 (7%) | → QA review
✅ Group B complete | Database schema | Progress: 12/69 (17%) | → QA review
✅ Group Z complete | Final cleanup | Progress: 69/69 (100%) | → PM check
```

**Step 4: PM sets item counts during planning**
- Each task_group gets `item_count` field
- PM calculates based on scope_type:
  - file: count items in referenced file
  - feature: estimate during planning
  - task_list: count from provided list

**Impact:** User sees progress throughout, can catch scope issues early

---

## Success Metrics

After implementation, monitor for:

**Type 1 Metrics:**
1. **Zero direct git/curl commands** from orchestrator in next 10 sessions
2. **Merge tasks always spawn Developer** agent
3. **CI monitoring done by Developer** with 60-second polling

**Type 2 Metrics:**
4. **Validator invoked on every BAZINGA** - 100% compliance
5. **Zero silent scope reductions** - PM always requests approval for scope changes
6. **Original scope tracked** - Every session has original_scope in database
7. **Full scope completion** - No partial completions accepted without user approval

---

## Summary

### Type 1: Direct Implementation Drift

| Layer | Description | Status |
|-------|-------------|--------|
| 1. Scenarios | Add Scenario 3 & 4 to orchestrator.md | ✅ Approved |
| 2. Merge Template | Enhance merge_workflow.md with 60s CI polling | ✅ Approved |
| 3. Bash Allowlist | Explicit allowlist + build-baseline.sh wrapper | ✅ Approved |
| 4. Policy Gate | Single reference in orchestrator.md | ✅ Approved |
| 5. Runtime Comment | Enforcement anchor at top of file | ✅ Approved |

### Type 2: Premature BAZINGA Acceptance Drift (NEW)

| Layer | Description | Status |
|-------|-------------|--------|
| 6. Scenario 5 & 6 | Add BAZINGA validation and scope scenarios | ✅ Approved |
| 7. Mandatory Validator | Force `Skill(command: "bazinga-validator")` on every BAZINGA | ✅ Approved |
| 8. Scope Tracking | Store original_scope at session start | ✅ Approved |
| 9. Scope Immutable | PM CANNOT reduce scope - forbidden, not negotiable | ✅ Approved |
| 10. Validator Enhancement | Add scope validation to bazinga-validator | ✅ Approved |
| 11. PM BAZINGA Format | Include Completion Summary with counts | ✅ Approved |
| 12. Progress Tracking | Show progress in status capsules | ✅ Approved |

### Rejected

| Layer | Description | Status |
|-------|-------------|--------|
| New phase_merge.md | Separate merge template | ❌ Rejected |
| Post-hoc Audit | Tool log scanning | ❌ Rejected |
| Pre-Validator Sanity Check | Quick check before validator | ❌ Rejected |

---

## Post-Implementation Critical Review (2025-12-09)

### Implementation Status: INCOMPLETE

**Initial F1-F12 implementation was documentation-only. Backend code was NOT modified.**

| Fix | Documentation | Python Code | Schema | Actual Status |
|-----|---------------|-------------|--------|---------------|
| F1: CI polling | ✅ | N/A | N/A | Working |
| F2: Original_Scope | ✅ | ❌ | ❌ | BROKEN |
| F3: bazinga-db commands | ✅ | ❌ | ❌ | BROKEN |
| F4: PM git removal | ✅ | N/A | N/A | Partial |
| F5: initial_branch | ✅ | ❌ | Exists unused | BROKEN |
| F6: build-baseline.sh | ✅ | ✅ | N/A | Working |
| F7: item_count | ✅ | ❌ | ❌ | BROKEN |
| F8: progress tracking | ✅ | ❌ | ❌ | BROKEN |
| F9: PM BAZINGA logging | ✅ | ❌ | ❌ | BROKEN |
| F10: config timeout | ✅ | N/A | ❌ | Partial |
| F11: scope change | ✅ | ❌ | ❌ | BROKEN |
| F12: 100% threshold | ✅ | N/A | N/A | Working |

### Critical Issue: Fake Commands Documented

10+ bazinga-db commands were documented in SKILL.md but never implemented in Python:
- `log-pm-bazinga`, `get-pm-bazinga`
- `increment-session-progress`
- `log-scope-change`, `get-scope-change`
- `log-validator-verdict`
- `--original_scope`, `--initial_branch`, `--item_count` params

### LLM-Recommended Fix (GPT-5)

**Simpler approach using event logging instead of new tables:**

1. Schema v9 migration:
   - `orchestration_logs.event_subtype TEXT`
   - `orchestration_logs.event_payload TEXT`
   - `sessions.metadata TEXT` (for original_scope)
   - `task_groups.item_count INTEGER`

2. Generic commands:
   - `save-event <session> <subtype> <json_payload>`
   - `get-events <session> [subtype] [limit]`

3. Extend existing functions:
   - `create_session` → add `--initial_branch`, `--metadata`
   - `create_task_group` → add `--item_count`

### Implementation Priority (Revised)

**Phase 1: Backend Implementation**
1. Schema v9 migration in `init_db.py`
2. `save-event`/`get-events` in `bazinga_db.py`
3. Extend `create_session` signature
4. Extend `create_task_group` signature
5. Create `validator_config.json`

**Phase 2: Documentation Alignment**
6. Update SKILL.md to match actual CLI
7. Update agent docs to use correct commands

**Phase 3: Testing**
8. Unit tests for new commands
9. Integration test for scope validation

**Full analysis:** `research/f1-f12-implementation-critical-review.md`

---

## References

- Observed failure transcript (user-provided)
- `agents/orchestrator.md` - Current orchestrator definition
- `templates/merge_workflow.md` - Existing merge workflow template
- `templates/orchestrator/phase_simple.md` - Simple mode template
- `templates/orchestrator/phase_parallel.md` - Parallel mode template
- OpenAI GPT-5 review feedback
- Post-implementation critical review (2025-12-09)
