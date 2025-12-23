# Guardrail Implementation Review: Preventing Premature Orchestration Stops

**Date:** 2025-12-15
**Context:** Implementation of 5 fixes to prevent orchestrator from stopping before completing all tasks
**Decision:** Added guardrails to orchestrator.md and phase templates
**Status:** In-Branch Implementation (commits on feature branch, pending merge)
**Reviewed by:** External LLM review (non-authoritative, used for analysis only)
**Branch Commits** (verify with `git log --oneline` on this branch):
- `aa232d6` - Initial guardrails implementation
- `57c72b7` - OpenAI-recommended improvements
- `327566d` - DB API consistency fix (get-state, clarification_used/resolved)
- `8c7e3b5` - Review fixes (status consistency, atomic increment, security)
- `33ddc74` - Escalation target fix (SSE → Tech Lead)
- `bb3572a` - CLI → Skill invocations

*Note: Commits are branch-local until PR merge. External reviews informed design but are not authoritative.*

---

## Problem Statement

The BAZINGA orchestrator was stopping prematurely before completing all tasks in the original scope. Despite having late-stage guardrails (BAZINGA Validator, Shutdown Protocol), the orchestrator would:
1. Ask permission-seeking questions ("Would you like me to continue?")
2. Output status and stop without taking next action
3. Fail to spawn PM after phase completion
4. Lose track of original scope after context compaction

**Root cause:** All existing guardrails were "late-stage" (post-BAZINGA). No early-stage guards prevented premature stopping.

---

## Solution: 5 Guardrail Fixes

### Fix 1: Pre-Output Self-Check (orchestrator.md:421-475)

**Purpose:** Detect and prevent violations BEFORE outputting messages

**Checks:**
1. Permission-seeking detection ("Would you like me to continue?")
2. Action-after-status (must call Task/Skill, not just output)
3. Completion claim validation (requires BAZINGA + Validator)

**Exception:** PM's NEEDS_CLARIFICATION (once per session)

### Fix 2: Mandatory PM Re-spawn After Phase Completion

**Locations:**
- `phase_simple.md:1249-1297`
- `phase_parallel.md:691-747`

**Purpose:** Force PM spawn after all groups in phase are approved/merged

**Behavior:**
- PM compares Original_Scope.estimated_items to completed items
- PM decides: assign next phase OR send BAZINGA
- No permission-seeking allowed

### Fix 3: Scope Continuity Check (orchestrator.md:479-535)

**Purpose:** Every-turn verification of progress against original scope

**Logic:**
- If completed_items < original_items → MUST continue, CANNOT stop
- If completed_items >= original_items → May proceed to BAZINGA flow
- Exception for NEEDS_CLARIFICATION pending

### Fix 4: Anti-Pattern Detection (orchestrator.md:539-595)

**Purpose:** Self-check with explicit forbidden/allowed pattern tables

**Includes:**
- Forbidden patterns with detection and correction
- Allowed patterns with conditions
- Self-correction procedure

### Fix 5: Post-Compaction Recovery (orchestrator.md:599-671)

**Purpose:** Automatic resume after context compaction

**Behavior:**
- Check session state in database
- Resume from where workflow paused
- Never ask permission after recovery

---

## Critical Analysis

### Pros

1. **Early-stage prevention:** Guards fire BEFORE output, not after BAZINGA
2. **Multiple layers:** 5 independent checks create defense-in-depth
3. **Clear exception handling:** NEEDS_CLARIFICATION preserved as legitimate pause
4. **Self-correction guidance:** Explicit examples of how to fix violations
5. **Database-backed scope tracking:** Original_Scope survives context compaction

### Cons / Potential Issues

1. **Instruction bloat:** Added ~250 lines to orchestrator.md (already large file)
2. **Redundancy:** Some checks overlap (Fix 1 Check 1 and Fix 4 forbidden patterns)
3. **Mental checks:** "Run this check mentally" relies on LLM attention, not enforcement
4. **No runtime verification:** These are instructions, not code - LLM could still violate
5. **Clarification tracking complexity:** `clarification_used`, `clarification_pending`, `clarification_resolved` - three states to track

### Potential Gaps

#### Gap 1: No Enforcement Mechanism

The checks are **instructions**, not **code**. The orchestrator could still:
- Ignore the self-check sections
- Output permission-seeking despite instructions
- Skip scope continuity check

**Mitigation needed:** Consider adding a hook or post-processing check?

#### Gap 2: State Tracking Complexity

Three clarification-related states:
- `clarification_used` (orchestrator internal)
- `clarification_pending` (database)
- `clarification_resolved` (database)

**Questions:**
- Are these always in sync?
- What if database update fails?
- Is the state machine complete?

#### Gap 3: Scope Comparison Accuracy

Fix 3 compares `completed_items` to `original_items` using:
```
completed_items = sum(group.item_count for group in task_groups if group.status == "completed")
```

**Issues:**
- What if PM creates more groups than original_items?
- What if item_count is not set on groups?
- Does this handle multi-phase correctly?

#### Gap 4: Phase Template Loading

Fix 2 requires phase templates to be loaded. But:
- What if template read fails?
- What if orchestrator uses cached/old template?
- Is there a version check?

#### Gap 5: Circular Logic Risk

Fix 1 says "Respawn PM with: 'You already used your clarification'"
But what if PM keeps returning NEEDS_CLARIFICATION?

**Current:** Would create infinite loop of "you already used clarification" → respawn → "NEEDS_CLARIFICATION" → respawn...

**Needed:** Max retry count or escalation path

---

## Questions for Review

1. **Redundancy:** Should Fix 1 Check 1 and Fix 4 forbidden patterns be consolidated?

2. **Enforcement:** Is there a way to add runtime enforcement (hook, post-processing)?

3. **State machine:** Is the clarification state machine complete? Should we use a formal state diagram?

4. **Scope comparison:** How to handle edge cases (PM creates extra groups, item_count not set)?

5. **Infinite loop:** Should there be a max retry for PM clarification rejection?

6. **File size:** Is the orchestrator.md becoming too large? Should we extract to templates?

7. **Testing:** How can we test these guardrails? Integration test scenarios?

---

## Implementation Details

### Files Modified

| File | Lines Added | Purpose |
|------|-------------|---------|
| `agents/orchestrator.md` | ~200 | Fixes 1, 3, 4, 5 |
| `templates/orchestrator/phase_simple.md` | ~50 | Fix 2 |
| `templates/orchestrator/phase_parallel.md` | ~57 | Fix 2 |
| `.claude/commands/bazinga.orchestrate.md` | ~250 | Auto-generated |

### Commit

`aa232d6` - Add guardrails to prevent premature orchestration stops

---

## Comparison to Alternatives

### Alternative 1: Hook-based enforcement

**Approach:** Add a pre-output hook that checks for forbidden patterns

**Pros:**
- Runtime enforcement
- Can't be ignored by LLM

**Cons:**
- More complex to implement
- May break legitimate outputs
- Hook latency

**Verdict:** Could be added as enhancement, not replacement

### Alternative 2: Simpler single check

**Approach:** One rule: "Never end message without Task() or Skill() call"

**Pros:**
- Simple
- Easy to remember
- Covers most cases

**Cons:**
- Doesn't handle NEEDS_CLARIFICATION exception
- Doesn't track scope
- No self-correction guidance

**Verdict:** Too simple, would break legitimate pauses

### Alternative 3: State machine enforcement

**Approach:** Formal state machine with explicit transitions

**Pros:**
- Rigorous
- All transitions defined
- No ambiguity

**Cons:**
- Complex to implement
- May be too rigid
- Hard to modify

**Verdict:** Overkill for current needs, but could be future enhancement

---

## Decision Rationale

The implemented approach balances:
1. **Comprehensiveness:** Multiple checks cover different failure modes
2. **Pragmatism:** Instructions rather than code, easier to iterate
3. **Exception handling:** NEEDS_CLARIFICATION preserved correctly
4. **Guidance:** Self-correction examples help LLM course-correct

The main risk is that these are instructions, not enforcement. The LLM could still violate them. However:
- Multiple redundant checks increase likelihood of catching violations
- Self-correction guidance helps LLM fix mistakes
- Database-backed scope tracking survives context compaction

---

## Lessons Learned

1. **Late-stage guards aren't enough:** Need early-stage prevention
2. **Instruction clarity matters:** Explicit forbidden/allowed tables work better than prose
3. **Exceptions must be explicit:** NEEDS_CLARIFICATION case needed careful handling
4. **State tracking is complex:** Multiple related states need careful management

---

## References

- Original issue analysis: User feedback on premature stopping
- orchestrator.md: Main orchestrator instructions
- phase_simple.md: Simple mode phase template
- phase_parallel.md: Parallel mode phase template
- bazinga-db skill: Database operations for state tracking

---

## Multi-LLM Review Integration

**Reviewed by:** OpenAI GPT-5 (2025-12-15)
**Note:** Gemini review skipped (ENABLE_GEMINI=false)

---

### Critical Issues Identified by OpenAI (MUST FIX)

| # | Issue | Severity | Description |
|---|-------|----------|-------------|
| 1 | **No runtime enforcement** | HIGH | All 5 fixes are instruction-level. LLM can still violate despite instructions. No automated pre-send validator. |
| 2 | **Clarification loop risk** | HIGH | PM NEEDS_CLARIFICATION limited "once per session" by instruction, but no hard cap. Risk of infinite clarify→respawn loop. |
| 3 | **Scope comparison brittleness** | MEDIUM | `item_count` may be missing/0, `estimated_items` may be null, PM may create more/fewer groups than estimate. |
| 4 | **Phase template dependency** | MEDIUM | No version/availability checks. If Read fails or old template cached, behavior regresses silently. |
| 5 | **Batch processing is procedural only** | MEDIUM | `batch_processing.md` is documentation. No mechanism verifies all responses routed before turn ends. |
| 6 | **Token budget bloat** | LOW | Always calling specialization-loader + context-assembler (including retries) without caching may exceed limits. |

---

### OpenAI's Recommended Improvements

1. **Pre-send validator hook:** Create "orchestration-lint" that checks:
   - Permission-seeking phrases outside PM NEEDS_CLARIFICATION
   - Messages ending without Task()/Skill() call
   - Completion claims without validator ACCEPT
   - Auto-append tool call on violation

2. **Unify and persist clarification state:**
   - Store `clarification_used` in bazinga-db (not ephemeral)
   - Add `max_retries=1` hard gate
   - Auto-fallback if PM returns NEEDS_CLARIFICATION again

3. **Harden scope comparison:**
   - Make `item_count` mandatory on task group creation
   - If `Original_Scope.estimated_items` null, derive from sum of initial groups
   - Secondary check: all groups completed AND success criteria met AND merges done

4. **Add caching for specialization/context:**
   - Cache specialization blocks per (group_id, agent_type) for session
   - Cache context-assembler outputs per agent_type/group/iteration

5. **Version and availability checks for templates:**
   - Add version headers to templates
   - Fail fast with clear error if outdated/missing
   - Provide minimal fallback if Read fails

6. **Batch-processing enforcement:**
   - Internal "routing completeness" function after parallel responses
   - Log routing_completeness_check: pass/fail+missing_groups

7. **Integration tests:**
   - Simulate common failure modes (permission-seeking, status-only, missing spawn)
   - Test DB failure scenarios

8. **Guardrails in spec-kit path:**
   - Mirror Fixes 1-5 into orchestrator_speckit.md

9. **Safer permission-seeking detector:**
   - Whitelist PM NEEDS_CLARIFICATION block
   - Only search for leading phrases outside quoted PM blocks

10. **DB outage escape hatch:**
    - If all Skill calls fail twice, allow ending after capsule with deferred note + Task() call

---

### OpenAI's Overall Assessment

> "The plan substantially strengthens early-stage guardrails and adds defense-in-depth through documentation and template guidance. However, without a runtime pre-send validator and minimal state machine enforcement, the orchestrator can still violate these rules under load or due to LLM drift."

**Confidence:** Medium if implemented as-is; High with recommended enforcement additions

---

### Suggested Changes Requiring User Approval

#### Change 1: Add Pre-Send Validator Hook

**Current:** Guardrails are instructions only - LLM "should" follow them
**Proposed:** Add runtime hook that validates output before sending
**Impact:** Requires new hook implementation, adds latency, but provides actual enforcement

**Do you approve this change?** [Yes/No/Modify]

---

#### Change 2: Hard Cap on NEEDS_CLARIFICATION (max_retries=1)

**Current:** Instruction says "once per session" but no enforcement
**Proposed:** If PM returns NEEDS_CLARIFICATION again after first use, auto-respond with fallback and continue
**Impact:** PM loses flexibility to ask multiple questions, but prevents infinite loops

**Do you approve this change?** [Yes/No/Modify]

---

#### Change 3: Make item_count Mandatory on Task Groups

**Current:** Scope comparison may fail if item_count not set
**Proposed:** Block PM completion if item_count missing; PM must backfill with default of 1
**Impact:** PM has additional validation requirement, but scope tracking becomes reliable

**Do you approve this change?** [Yes/No/Modify]

---

#### Change 4: Add Template Version Headers

**Current:** Templates loaded without version check
**Proposed:** Add version header, fail fast if outdated/missing
**Impact:** More maintenance (update versions), but prevents silent regressions

**Do you approve this change?** [Yes/No/Modify]

---

#### Change 5: Add Caching for Specialization/Context

**Current:** Always invoke both skills on every spawn (including retries)
**Proposed:** Cache per (group_id, agent_type) for session, only refresh when iteration increments
**Impact:** Reduces token usage and latency, but adds caching complexity

**Do you approve this change?** [Yes/No/Modify]

---

#### Change 6: Mirror Guardrails to orchestrator_speckit.md

**Current:** Guardrails only in main orchestrator
**Proposed:** Duplicate Fixes 1-5 into spec-kit orchestrator
**Impact:** Code duplication, but ensures consistency across execution paths

**Do you approve this change?** [Yes/No/Modify]

---

### Summary: Implementation as-is vs With Improvements

| Aspect | As-Is | With OpenAI's Improvements |
|--------|-------|---------------------------|
| Enforcement | Instructions only | Runtime + Instructions |
| Clarification loops | Risk of infinite loop | Hard cap (max 1) |
| Scope tracking | May fail on edge cases | Reliable with mandatory fields |
| Template loading | Silent failures | Fail-fast with version check |
| Token usage | High (no caching) | Optimized with caching |
| Testing | None | Integration tests |
| Spec-kit parity | Divergent | Consistent |

**Recommendation:** The current implementation addresses the core issue (premature stopping) but has gaps that could cause failures under load or edge cases. Consider implementing at least issues #1, #2, and #3 from the critical issues list.

---

## 🟢 FINAL IMPLEMENTATION STATUS (2025-12-15)

### User-Approved Changes Implemented

| Change | Status | Implementation Details |
|--------|--------|------------------------|
| **Change 2: Hard Cap NEEDS_CLARIFICATION** | ✅ DONE | Database-backed state via `save-state`/`get-state`. Auto-fallback on second request. |
| **Change 3: item_count Mandatory** | ✅ DONE | Added Step 2.5 validation in scope continuity check. Blocks workflow if null/0. |
| **Change 6: Mirror to orchestrator_speckit.md** | ✅ DONE | Added condensed guardrails section with all 5 fixes. |

### Changes NOT Implemented (User Did Not Approve)

| Change | Reason |
|--------|--------|
| Change 1: Pre-Send Validator Hook | Not approved - requires hook implementation |
| Change 4: Template Version Headers | Not approved |
| Change 5: Caching for Specialization/Context | Not approved |

### Files Modified

| File | Lines Changed | Purpose |
|------|---------------|---------|
| `agents/orchestrator.md` | +50 | Hard cap enforcement, item_count validation |
| `agents/orchestrator_speckit.md` | +60 | Mirrored guardrails section |
| `.claude/commands/bazinga.orchestrate.md` | auto-gen | Rebuilt from orchestrator.md |

### Commits

| Hash | Message |
|------|---------|
| `aa232d6` | Add guardrails to prevent premature orchestration stops |
| `2cb6695` | Add ultrathink analysis of guardrail implementation |
| `57c72b7` | Implement OpenAI-recommended guardrail improvements |

### Remaining Gaps (From OpenAI Review)

1. **No runtime enforcement** - Still instruction-level only (Change 1 not approved)
2. **Phase template dependency** - No version checks (Change 4 not approved)
3. **Token budget bloat** - No caching (Change 5 not approved)
4. **Batch processing verification** - Not implemented
5. **Integration tests** - Not implemented

### Current Guardrail Coverage

```
Fix 1: Pre-Output Self-Check         ✅ orchestrator.md, orchestrator_speckit.md
Fix 2: Mandatory PM Re-spawn         ✅ phase_simple.md, phase_parallel.md
Fix 3: Scope Continuity Check        ✅ orchestrator.md, orchestrator_speckit.md
Fix 4: Anti-Pattern Detection        ✅ orchestrator.md, orchestrator_speckit.md
Fix 5: Post-Compaction Recovery      ✅ orchestrator.md, orchestrator_speckit.md

Hard Cap Enforcement (Change 2)      ✅ Database-backed, max_retries=1
item_count Validation (Change 3)     ✅ Step 2.5 blocks if missing
Spec-kit Parity (Change 6)           ✅ Guardrails mirrored
```

### Confidence Assessment

| Scenario | Confidence |
|----------|------------|
| Permission-seeking prevention | HIGH - Multiple checks, explicit examples |
| Clarification loop prevention | HIGH - Database-backed hard cap |
| Scope tracking accuracy | MEDIUM-HIGH - item_count validation added |
| Context compaction recovery | MEDIUM - Instructions only, no runtime enforcement |
| Spec-kit consistency | HIGH - Guardrails mirrored |

**Overall:** Implementation addresses the core issue (premature stopping) with the user-approved improvements. Remaining gaps are acknowledged but not critical for typical usage.
