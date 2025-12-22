# Role Drift Prevention Implementation Review

**Date:** 2025-12-09
**Context:** Critical analysis of 12-layer orchestrator role drift prevention implementation
**Decision:** Pending review
**Status:** Under Review

---

## Implementation Summary

Implemented changes across 9 files to prevent two types of orchestrator role drift:
- **Type 1:** Direct implementation (orchestrator doing work instead of spawning agents)
- **Type 2:** Premature BAZINGA acceptance (accepting scope reduction without validation)

---

## Layer-by-Layer Implementation Verification

### Type 1: Direct Implementation Drift

| Layer | Plan | Implementation | Status |
|-------|------|----------------|--------|
| 1. Scenarios 3-6 | Add to orchestrator.md | ✅ Added Scenarios 3-6 | Match |
| 2. Merge Template | Enhance merge_workflow.md with 60s CI polling | ❌ **NOT IMPLEMENTED** | **MISSING** |
| 3. Bash Allowlist | Explicit allowlist + build-baseline.sh | ✅ Added §Bash Command Allowlist | Match |
| 4. Policy Gate | Single reference in orchestrator.md | ✅ Added §Policy-Gate section | Match |
| 5. Runtime Comment | Enforcement anchor at top | ✅ Added HTML comment | Match |

### Type 2: Premature BAZINGA

| Layer | Plan | Implementation | Status |
|-------|------|----------------|--------|
| 6. Scenarios 5-6 | BAZINGA validation + scope scenarios | ✅ Added in Scenarios section | Match |
| 7. Mandatory Validator | Force validator invocation | ✅ Added §Mandatory BAZINGA Validation | Match |
| 8. Scope Tracking | Store original_scope at session start | ❌ **NOT IMPLEMENTED** | **MISSING** |
| 9. Scope Immutable | PM cannot reduce scope | ✅ Added to project_manager.md | Match |
| 10. Validator Enhancement | Add scope validation to validator | ✅ Added Step 5.5 | Match |
| 11. PM BAZINGA Format | Completion Summary with counts | ✅ Added to project_manager.md | Match |
| 12. Progress Tracking | Show progress in capsules | ✅ Added to message_templates.md | Match |

---

## Critical Issues Identified

### 🔴 CRITICAL ISSUE 1: Missing Merge Workflow Enhancement (Layer 2)

**Plan stated:**
> Enhance existing `templates/merge_workflow.md` with explicit Developer spawn template with CI monitoring (60-second polling)

**Reality:**
The merge_workflow.md file was NOT modified. The Developer merge task with 60-second CI polling was not added.

**Impact:**
- Developer won't know to poll CI every 60 seconds
- No explicit merge prompt template exists
- Orchestrator may still not spawn Developer correctly for merge tasks

**Fix Required:**
Add the enhanced Developer merge prompt to `templates/merge_workflow.md`

---

### 🔴 CRITICAL ISSUE 2: Missing Scope Tracking at Session Start (Layer 8)

**Plan stated:**
> Add to orchestrator initialization (Step 0): Store original scope when creating session in database

**Reality:**
The orchestrator.md was NOT modified to include `Original_Scope` field in session creation.

**Impact:**
- Validator cannot compare completion against original scope
- Step 5.5 in validator references `original_scope` but it's never stored
- Scope validation will fail because there's no baseline to compare against

**Fix Required:**
Modify orchestrator.md Step 0 (Path B: CREATE NEW SESSION) to include Original_Scope field.

---

### 🟡 ISSUE 3: bazinga-db Schema Not Updated

**Plan stated:**
> Add `original_scope`, `completed_items_count` fields to bazinga-db schema

**Reality:**
The bazinga-db schema was not modified. The SKILL.md references querying `original_scope` but the database doesn't have this field.

**Impact:**
- `bazinga-db, get session [session_id] with original scope information` will fail
- Validator's scope check cannot work without database support

**Fix Required:**
Either:
a) Update bazinga-db schema migration (preferred)
b) Store original_scope in pm_state JSON field (workaround)

---

### 🟡 ISSUE 4: Validator Logging Command May Not Exist

**Implementation added:**
```
bazinga-db, log validator verdict:
Session ID: [session_id]
Verdict: [ACCEPT/REJECT]
Reason: [summary]
Scope_Check: [pass/fail]
```

**Problem:**
The bazinga-db skill may not have a `log validator verdict` command implemented. This could cause the validator to fail or silently skip logging.

**Fix Required:**
Verify bazinga-db supports this command, or use existing logging mechanism.

---

### 🟡 ISSUE 5: Progress Tracking Data Source Unclear

**Implementation added capsule format:**
```
✅ Group {id} complete | {summary} | Progress: {completed}/{total} ({percentage}%)
```

**Problem:**
- Where does `{completed}` come from?
- Where does `{total}` come from?
- The orchestrator doesn't track `completed_items_count`
- PM's task groups don't have item counts

**The plan said:**
> PM sets item counts during planning - Each task_group gets `item_count` field

**But this was NOT implemented in project_manager.md.** PM doesn't know to add item counts to task groups.

**Impact:**
Progress tracking capsules will show placeholder values or fail to render.

---

### 🟡 ISSUE 6: Circular Dependency in Validator Scope Check

**Flow:**
1. Validator queries `original_scope` from database
2. Validator extracts PM's Completion Summary from BAZINGA message
3. Validator compares

**Problem:**
Step 5.5 says "Extract PM's Completion Summary from BAZINGA message" - but how does the validator get the PM's BAZINGA message? It's invoked by orchestrator, not passed the PM response.

**Current validator invocation:**
```
Skill(command: "bazinga-validator")
```

**Missing:**
The validator needs context about what PM claimed. The orchestrator should pass PM's BAZINGA response to the validator somehow.

---

### 🟢 Minor Issue 7: Response Parsing Threshold

**Implementation:**
```
Validation before accepting:
1. Completed_Items == Total_Items (or very close: >90%)
```

**Problem:**
The 90% threshold is vague. What counts as "very close"? If original scope was 100 tasks and 91 were completed, is that acceptable?

**Recommendation:**
Use explicit rule: `Completed_Items == Total_Items` (100% required) unless BLOCKED status.

---

## Functional Compatibility Analysis

### Will Existing Functionality Break?

**1. Orchestrator Core Flow:** ✅ Safe
- Added sections are additive, not modifying existing flow
- Runtime comment is HTML comment (invisible to processing)
- Scenarios are documentation, not executable

**2. PM Agent:** ✅ Safe
- Added §Scope Immutable is a behavioral directive
- PM BAZINGA Format is additive requirement
- No existing logic modified

**3. Phase Templates:** ✅ Safe
- Only added a one-line reference to §Policy-Gate
- No logic changes

**4. bazinga-validator:** ⚠️ Partially Safe
- Step 5.5 added between Step 5 and Step 6
- Step numbering is sequential and clear
- BUT: References non-existent data (original_scope)

**5. build-baseline.sh:** ✅ Safe
- New file, no conflicts
- Properly handles multiple project types
- Returns appropriate exit codes

---

## Gap Analysis: Plan vs Implementation

### Implemented Correctly ✅
1. Runtime enforcement anchor comment
2. Scenarios 3-6 in orchestrator
3. §Bash Command Allowlist with explicit patterns
4. §Policy-Gate section
5. Phase template references
6. build-baseline.sh wrapper script
7. §Mandatory BAZINGA Validation
8. §Scope Immutable in PM
9. PM BAZINGA Response Format
10. Progress tracking capsule format
11. PM BAZINGA Completion Summary parsing

### Missing ❌
1. **merge_workflow.md enhancement** - Layer 2 completely skipped
2. **Original_Scope storage in orchestrator init** - Layer 8 partially missing
3. **bazinga-db schema update** - Supporting infrastructure not added
4. **PM item_count per task group** - Progress tracking data source missing

### Partially Implemented ⚠️
1. **Validator scope check** - Logic added but depends on missing data
2. **Progress tracking** - Format defined but data flow undefined

---

## Risk Assessment

| Risk | Severity | Likelihood | Mitigation |
|------|----------|------------|------------|
| Merge workflow unchanged | HIGH | CERTAIN | Add merge prompt to merge_workflow.md |
| Scope validation fails | HIGH | CERTAIN | Add original_scope storage |
| Progress tracking broken | MEDIUM | HIGH | Add item_count to PM task groups |
| Validator logging fails | LOW | MEDIUM | Verify bazinga-db command exists |

---

## Recommendations

### Must Fix Before Deployment

1. **Add merge workflow enhancement to `templates/merge_workflow.md`:**
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

## Response Format
Return: MERGE_SUCCESS | MERGE_CONFLICT | MERGE_TEST_FAILURE | MERGE_BLOCKED
"""
)
```

2. **Add original_scope to orchestrator session creation:**
In orchestrator.md Path B step 3, add:
```
Original_Scope: {
  "raw_request": "[exact user request text]",
  "scope_type": "file|feature|task_list|description",
  "scope_reference": "[file path or feature name if applicable]",
  "estimated_items": [count if determinable, null otherwise]
}
```

3. **Add item_count to PM task group creation:**
In project_manager.md Step 3, add requirement for each task group to include item_count.

### Should Fix

4. Pass PM's BAZINGA response to validator as context
5. Clarify 90% threshold rule (recommend 100% or explicit user approval)

---

## Verdict

**Implementation Completeness:** 75% (9/12 layers fully implemented)

**Production Readiness:** ⚠️ NOT READY

**Critical Blockers:**
- merge_workflow.md not enhanced (merge tasks won't use 60s polling)
- original_scope not stored (validator scope check will fail)

**The implementation captures the spirit of the plan but has execution gaps that will cause runtime failures.** The validator's scope check (Step 5.5) will fail because it references data that's never stored.

---

## Multi-LLM Review Integration

**Reviewed by:** OpenAI GPT-5

### Consensus Points (Confirmed Issues)

1. **Layer 2 (merge_workflow.md) completely missing** - Confirmed critical
2. **Layer 8 (original_scope) not stored** - Confirmed critical
3. **bazinga-db schema mismatch** - New commands referenced but not implemented
4. **Progress tracking data source undefined** - No item_count in PM task groups
5. **Validator can't access PM's BAZINGA content** - Context gap identified

### Additional Issues Identified by LLM

6. **PM told to run git command (Step 5.1)** - Policy violation!
   - PM Step 5.1 says "git branch --show-current"
   - PM tool constraints forbid git
   - FIX: Move to orchestrator init and store as `sessions.initial_branch`

7. **Orchestrator Bash allowlist contradictions**
   - Step 6 shows inline build commands (npm, go, python)
   - Allowlist says "use build-baseline.sh wrapper"
   - FIX: Remove inline commands, use wrapper only

8. **Fallback file creation uses forbidden patterns**
   - Orchestrator uses cp/heredoc writes not in allowlist
   - FIX: Create a wrapper script for fallback generation

9. **CI provider variance**
   - CI polling assumes GitHub
   - FIX: Isolate in Developer helper for future extensibility

10. **Scope reduction absolutism may be impractical**
    - "Scope immutable" is absolute
    - FIX: Add explicit "user-approved scope change" path with DB logging

### Actionable Fixes Required (Ordered by Priority)

#### Priority 1: Critical Blockers

| Fix | File | Description |
|-----|------|-------------|
| F1 | `templates/merge_workflow.md` | Add Developer merge prompt with 60s CI polling |
| F2 | `agents/orchestrator.md` | Add Original_Scope to session creation (Path B Step 3) |
| F3 | `.claude/skills/bazinga-db/SKILL.md` | Add schema support for original_scope, validator_verdicts |

#### Priority 2: Policy Violations

| Fix | File | Description |
|-----|------|-------------|
| F4 | `agents/project_manager.md` | Remove git command, use DB lookup for initial_branch |
| F5 | `agents/orchestrator.md` | Store initial_branch in session at init |
| F6 | `agents/orchestrator.md` | Remove inline build commands from Step 6 |

#### Priority 3: Data Flow Gaps

| Fix | File | Description |
|-----|------|-------------|
| F7 | `agents/project_manager.md` | Add item_count requirement for task groups |
| F8 | `agents/orchestrator.md` | Track completed_items_count, increment on approval |
| F9 | `agents/orchestrator.md` | Log PM BAZINGA message to DB for validator access |

#### Priority 4: Robustness

| Fix | File | Description |
|-----|------|-------------|
| F10 | Various | Make validator timeouts configurable |
| F11 | Various | Add user-approved scope change path |
| F12 | `response_parsing.md` | Change 90% to 100% requirement |

### Rejected LLM Suggestions

| Suggestion | Reason |
|------------|--------|
| Create write-fallback-context.sh | Over-engineering - fallback is rare |
| Add preflight policy checker | Good idea but out of scope for this fix |
| Store PM BAZINGA as structured DB fields | Can parse from message for now |

---

## Updated Risk Assessment

| Risk | Severity | Status |
|------|----------|--------|
| Merge workflow unchanged | CRITICAL | ❌ Blocking |
| Scope validation fails (no original_scope) | CRITICAL | ❌ Blocking |
| PM policy violation (git command) | HIGH | ❌ Must fix |
| Progress tracking broken | MEDIUM | ⚠️ Should fix |
| Validator logging fails | LOW | ⚠️ Should fix |

---

## Final Verdict

**The implementation is 75% complete but has 3 critical blockers that will cause runtime failures:**

1. **merge_workflow.md** - Not enhanced with CI polling template
2. **original_scope** - Not stored at session creation
3. **PM git command** - Policy violation

**Without fixing these, the role drift prevention will NOT work as designed.**

---

## References

- Original plan: `research/orchestrator-role-drift-prevention.md`
- Commit: `5057667` - "Implement 12-layer orchestrator role drift prevention"
- LLM Review: `tmp/ultrathink-reviews/combined-review.md`
