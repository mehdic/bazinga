# Domain Skill Migration: Linter Fixes Critical Review

**Date:** 2025-12-31
**Context:** Second-pass review after linter issue fixes
**Status:** REVIEW IN PROGRESS

---

## Executive Summary

This review analyzes the fixes applied to address linter-identified issues in the domain skill migration. While the immediate issues were resolved, several deeper architectural concerns remain unaddressed.

---

## 1. Fixes Applied

### 1.1 save-reasoning --content-file Documentation ✅

**Before:**
```bash
python3 ... save-reasoning "<session>" "<group>" "<agent>" "<phase>" "<content>"
```

**After:**
```bash
# Recommended: Use --content-file to avoid exposing content in process table
python3 ... save-reasoning "<session>" "<group>" "<agent>" "<phase>" \
  --content-file /tmp/reasoning.txt [--confidence N]

# Alternative: Inline content (avoid for sensitive data)
python3 ... save-reasoning ... "<content>"
```

**Assessment:** ✅ Good fix, addresses security concern

### 1.2 investigator.md Workflow Fields Mismatch ✅

**Before:**
```
bazinga-db-workflow, please update task group investigation status:
Investigation Iteration: [N]
Last Activity: [description]
```

**After:**
```
# TWO operations:
# 1. Workflow: update task group with --review_iteration
bazinga-db-workflow, please update task group:
Review Iteration: [N]

# 2. Agents: log activity details via event
bazinga-db-agents, please save event:
Event Type: investigation_status
Payload: { "activity": "[description]" }
```

**Assessment:** ✅ Correctly maps to supported CLI flags

### 1.3 Deprecated Skill Quick Reference ✅

**Before:** Listed CLI commands and script paths
**After:** Shows domain skill routing table only

**Assessment:** ✅ Properly discourages direct CLI usage

### 1.4 Lingering Narrative Fixes ✅

Updated 3 occurrences of "bazinga-db skill" → "bazinga-db-agents skill"

**Assessment:** ✅ Consistent terminology

---

## 2. Critical Issues STILL Present

### 2.1 🔴 No --payload-file for save-event

**Problem:** The linter noted that `save-event` examples pass JSON inline, which has the same security/quoting issues as save-reasoning.

**Current state:** NOT FIXED
- save-event still uses inline JSON payloads
- No --payload-file option exists in CLI

**Risk:**
- Sensitive event data visible in process table
- Complex JSON quoting failures

**Recommendation:**
1. Add `--payload-file` to bazinga_db.py save-event command
2. Update docs to recommend file-based approach

### 2.2 🔴 check-mandatory-phases Return Semantics

**Problem:** Linter noted inconsistent documentation - JSON output vs exit codes

**Current state:** PARTIALLY ADDRESSED
- SKILL.md shows JSON: `{"complete": true/false, "missing": [...]}`
- But no example JSON provided

**Risk:** Agents may parse output incorrectly

**Recommendation:** Add explicit JSON example in SKILL.md

### 2.3 🟡 orchestrator_db_reference.md Pattern Inconsistency

**Problem:** Mixes "request-then-invoke" and direct CLI patterns

**Current state:** NOT FIXED
- Some sections show natural language requests + Skill()
- Others show direct CLI commands

**Risk:** Confusion about canonical invocation pattern

**Recommendation:** Add header note clarifying the pattern

---

## 3. Logical Flaws in Implementation

### 3.1 Two-Operation Investigation Update is Redundant

**Issue:** The fix requires TWO skill invocations for one logical operation:
1. `bazinga-db-workflow` for review_iteration
2. `bazinga-db-agents` for activity logging

**Problems:**
- Atomicity: If first succeeds and second fails, state is inconsistent
- Complexity: Agents must remember to do both
- Token waste: Two skill invocations instead of one

**Better Alternative:**
- Add investigation-specific fields to task_groups table
- Or: Create single `update-investigation-status` command that does both

### 3.2 🔴 CRITICAL: review_iteration Data Corruption Risk

**Issue:** We mapped "Investigation Iteration" to `--review_iteration`

**VERIFIED PROBLEM:** The orchestrator ACTIVELY USES `review_iteration` for Tech Lead reviews:
- `agents/orchestrator.md:2328` - Extracts review_iteration from DB
- `agents/orchestrator.md:2333` - Uses `previous_iteration = db_result.get("review_iteration", 1)`
- `agents/orchestrator.md:2372` - Updates `--review_iteration {new_iteration}`
- `agents/orchestrator.md:2393` - Escalation check: `IF review_iteration >= 5`
- `agents/orchestrator.md:2432-2435` - TL workflow increments review_iteration

**Data Corruption Scenario:**
1. TL reviews, sets review_iteration = 1
2. Issue found, spawns Investigator
3. Investigator runs 3 iterations, sets review_iteration = 3
4. Orchestrator sees review_iteration = 3, thinks TL reviewed 3 times
5. May trigger escalation incorrectly!

**SEVERITY:** HIGH - Can trigger wrong escalation paths

**Immediate Fix Required:**
1. Remove `Review Iteration` from investigator.md workflow update
2. Use events-only for investigation iteration tracking
3. OR add `--investigation_iteration` flag to CLI

### 3.3 Validation Script Doesn't Check CLI Flag Existence

**Issue:** Script checks request text matches skill domain, but not whether the CLI flags actually exist

**Example:** If someone writes:
```
bazinga-db-workflow, please update task group:
Foo Bar: [value]
```

The validation passes (workflow domain matches), but `--foo-bar` isn't a real flag.

**Recommendation:** Add flag validation step to script

---

## 4. Missing Considerations

### 4.1 Agent Prompt Size Impact

The investigator.md fix added ~15 lines of new content. With file already near size limits, this matters.

**Current file size:** Need to check
**Risk:** May push file over Claude context limits

### 4.2 Cross-File Consistency

The investigation status update pattern now exists in:
- `agents/investigator.md` (updated)
- `templates/investigation_loop.md` (updated earlier)

**Question:** Are they consistent?

### 4.3 Backward Compatibility

**Issue:** Old orchestration sessions may have:
- `review_iteration` values from TL reviews
- No `investigation_status` events

New code expects investigation data in these locations.

**Risk:** Reading old sessions may misinterpret TL review data as investigation data.

---

## 5. Better Alternatives Not Considered

### 5.1 Single Investigation Table

Instead of overloading task_groups and events, create:

```sql
CREATE TABLE investigation_sessions (
    id INTEGER PRIMARY KEY,
    session_id TEXT NOT NULL,
    group_id TEXT NOT NULL,
    iteration INTEGER DEFAULT 0,
    status TEXT DEFAULT 'in_progress',
    last_activity TEXT,
    root_cause TEXT,
    confidence REAL,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Benefits:**
- Clean separation of concerns
- Single operation to update
- Query history easily

### 5.2 Domain Skill for Investigations

Create `bazinga-db-investigation` skill:
- `start-investigation`
- `update-investigation`
- `complete-investigation`

**Benefits:**
- Semantic clarity
- Single invocation
- Clear ownership

### 5.3 Event-Only Approach

Use ONLY events for investigation state:
- No task_group field overloading
- Query latest event for current state
- Full audit trail

**Benefits:**
- No schema changes
- Immutable history
- Simpler logic

---

## 6. Implementation Risks

### 6.1 Immediate Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| review_iteration data corruption | Medium | High | Add investigation_iteration flag |
| Two-operation atomicity failure | Low | Medium | Add transaction wrapper |
| Agent prompt size overflow | Low | High | Audit file sizes |

### 6.2 Long-term Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Pattern drift (different files diverge) | High | Medium | Golden tests |
| New templates miss validation | High | Medium | Add to OPERATIONAL_TEMPLATES |
| CLI flags change, docs stale | Medium | Medium | Schema-driven docs |

---

## 7. Specific Improvements Needed

### 7.1 Immediate (Before Merge)

1. **Verify review_iteration semantic correctness**
   - Check if TL uses this field
   - If yes, add separate investigation_iteration flag

2. **Add --payload-file to save-event**
   - Modify bazinga_db.py
   - Update SKILL.md examples

3. **Check investigator.md file size**
   - Must stay under context limits

### 7.2 Short-term (This Sprint)

1. **Add check-mandatory-phases JSON example**
2. **Add pattern note to orchestrator_db_reference.md**
3. **Create golden tests for CLI flag existence**

### 7.3 Long-term (Next Sprint)

1. **Consider investigation table or skill**
2. **Add transaction wrapper for multi-operation updates**
3. **Schema-driven documentation generation**

---

## 8. Verification Checklist

Before considering these fixes complete:

- [ ] Verify `review_iteration` is not used by Tech Lead
- [ ] Check investigator.md file size
- [ ] Confirm investigation_loop.md and investigator.md are consistent
- [ ] Test two-operation flow end-to-end
- [ ] Run validation script passes
- [ ] CI passes (agent sync check)

---

## 9. Conclusion

**The fixes address the linter's immediate concerns but introduce new issues:**

1. **Semantic mismatch** - review_iteration ≠ investigation_iteration
2. **Atomicity gap** - Two operations can partially fail
3. **Missing features** - No --payload-file for save-event
4. **Documentation gaps** - No JSON examples for check-mandatory-phases

**Recommended Action:**
1. Verify review_iteration is safe to overload (or add new flag)
2. Add --payload-file to save-event
3. Consider event-only approach for investigations
4. Add golden tests to prevent regression

---

## Multi-LLM Review Integration

**Reviewed by:** OpenAI GPT-5 (2026-01-01)

### Consensus Points (Confirmed)

1. **review_iteration corruption is HIGH severity** - Must revert immediately
2. **Event-sourced investigation state is the right approach** - Store as events, derive iteration from count
3. **--payload-file needed for save-event** - Same security pattern as save-reasoning
4. **Two-step operation lacks atomicity** - Can leave inconsistent state

### New Insights from Review

1. **Concurrency risk** - What if Investigator and TL both write review_iteration simultaneously? Need idempotent keys.

2. **Backward compatibility** - Old sessions may have review_iteration data that would be misinterpreted under new semantics.

3. **Observability gap** - No dashboard counters distinguish review vs investigation iterations.

4. **Schema validation** - Validation script checks domain match but not whether CLI flags exist.

### Incorporated Improvements

| Suggestion | Action |
|------------|--------|
| Revert review_iteration usage in investigator | ✅ **CRITICAL** - Must do before merge |
| Use events-only for investigation tracking | ✅ Best approach - no schema changes |
| Add --payload-file to save-event | ✅ Add to CLI and update docs |
| Unified update-investigation-status skill | 🟡 Consider for long-term |
| Add golden tests for router behavior | ✅ Added to short-term plan |
| Schema-driven flag validation | ✅ Added to long-term plan |

### Rejected Suggestions

| Suggestion | Reason for Rejection |
|------------|---------------------|
| Duplicate agent files concern | False positive - only one copy of each agent file exists in `agents/` |
| Migration script for existing data | Not needed - using events-only approach doesn't change existing data |

---

## Revised Action Plan

### 🔴 CRITICAL: Immediate Fix (Before Merge)

**Must revert the review_iteration fix in investigator.md:**

```diff
- **1. Update task group status (workflow skill):**
- bazinga-db-workflow, please update task group:
- Review Iteration: [current iteration number]

+ **1. Log investigation iteration (agents skill ONLY):**
+ bazinga-db-agents, please save event:
+ Event Type: investigation_iteration
+ Payload: { "iteration": N, "status": "...", "activity": "..." }
```

**Rationale:** review_iteration is actively used for TL escalation logic. Overloading it will cause incorrect escalations.

### Phase 1: Immediate (Before Merge)

1. ✅ Fix investigator.md - Remove review_iteration, use events-only
2. ✅ Fix investigation_loop.md - Same change for consistency
3. Add --payload-file to save-event CLI
4. Update all save-event examples to use file-based approach

### Phase 2: Short-term (This Sprint)

1. Add golden tests for router behavior
2. Add dashboard counters for investigation iterations
3. Add check-mandatory-phases JSON example

### Phase 3: Long-term (Next Sprint)

1. Consider bazinga-db-investigation skill for atomic operations
2. Add schema-driven flag validation
3. Add concurrency/idempotency handling

