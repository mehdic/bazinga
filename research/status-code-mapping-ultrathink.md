# Status Code Mapping: Comprehensive Gap Analysis

**Date:** 2025-12-23
**Context:** Complete audit of all agent status codes vs transitions.json configuration
**Decision:** Align transitions.json with authoritative agent definitions
**Status:** Implemented
**Reviewed by:** OpenAI GPT-5 (Gemini skipped - ENABLE_GEMINI=false)
**Implemented:** 2025-12-23

---

## Problem Statement

Multiple gaps exist between what agents define as their output status codes and what `transitions.json` is configured to route. This creates:
1. **Broken routing** - Status codes returned by agents aren't handled
2. **Wrong destinations** - Some codes route to incorrect agents
3. **Name mismatches** - Same status with different names causes parse failures

---

## Complete Agent Status Code Inventory

### Developer (`agents/developer.md`)

| Status Code | Meaning | Intended Route |
|-------------|---------|----------------|
| `READY_FOR_QA` | Implementation complete with integration/E2E tests | QA Expert |
| `READY_FOR_REVIEW` | Implementation complete (unit tests or no tests) | Tech Lead |
| `BLOCKED` | Cannot proceed without external help | Investigator (fallback: Tech Lead) |
| `PARTIAL` | Partial work done, can continue | Respawn Developer |
| `ESCALATE_SENIOR` | Issue too complex for Developer tier | SSE |
| `NEEDS_TECH_LEAD_VALIDATION` | Uncertainty, need TL guidance | Tech Lead |

**Merge Task Status Codes (per orchestrator.md:111):**

| Status Code | Meaning | Intended Route |
|-------------|---------|----------------|
| `MERGE_SUCCESS` | Merge completed successfully | Check phase (continue workflow) |
| `MERGE_CONFLICT` | Git conflicts during merge | Developer to resolve |
| `MERGE_TEST_FAILURE` | Tests fail after merge | Developer to fix |
| `MERGE_BLOCKED` | Cannot merge (permissions, etc.) | Tech Lead |

### Senior Software Engineer (`agents/senior_software_engineer.md`)

| Status Code | Meaning | Intended Route |
|-------------|---------|----------------|
| `READY_FOR_QA` | Fix complete with tests | QA Expert |
| `READY_FOR_REVIEW` | Fix complete, minimal/no tests | Tech Lead |
| `BLOCKED` | Cannot proceed without help | Tech Lead |
| `ROOT_CAUSE_FOUND` | Identified cause, need PM decision | **Project Manager** |
| `PARTIAL` | Partial work done, can continue | Respawn SSE |
| `NEEDS_TECH_LEAD_VALIDATION` | Need TL guidance | Tech Lead |

### QA Expert (`agents/qa_expert.md`)

| Status Code | Meaning | Intended Route |
|-------------|---------|----------------|
| `PASS` | All tests pass | Tech Lead |
| `FAIL` | Tests fail (Level 1-2 challenges) | Developer |
| `FAIL_ESCALATE` | Tests fail (Level 3-5 challenges) | SSE |
| `BLOCKED` | Cannot run tests | Tech Lead |
| `FLAKY` | Intermittent test failures | Tech Lead |
| `PARTIAL` | Some tests run, some blocked | Tech Lead |

### Tech Lead (`agents/tech_lead.md`)

| Status Code | Meaning | Intended Route |
|-------------|---------|----------------|
| `APPROVED` | Code passes review | Developer (spawn_merge) → then check_phase |
| `CHANGES_REQUESTED` | Issues found | Developer (with escalation check) |
| `SPAWN_INVESTIGATOR` | Complex issue needs investigation | Investigator |
| `ESCALATE_TO_OPUS` | Need stronger model | Respawn Tech Lead (model: opus) |
| `UNBLOCKING_GUIDANCE_PROVIDED` | Helped blocked developer | Return to blocked agent |
| `ARCHITECTURAL_DECISION_MADE` | Made design decision | Developer |

### Project Manager (`agents/project_manager.md`)

| Status Code | Meaning | Intended Route |
|-------------|---------|----------------|
| `PLANNING_COMPLETE` | Initial planning done | spawn_batch Developers |
| `CONTINUE` | Phase complete, more pending | spawn_batch Developers |
| `BAZINGA` | All work complete | validate_then_end |
| `NEEDS_CLARIFICATION` | Need user input | pause_for_user |
| `INVESTIGATION_NEEDED` | Unknown blocker | Investigator |
| `INVESTIGATION_ONLY` | Questions only, no implementation | end_session |
| `IN_PROGRESS` | Work ongoing (tracking) | Internal/informal |
| `REASSIGNING_FOR_FIXES` | Issues found, spawning dev | Internal/informal |
| `ESCALATING_TO_TECH_LEAD` | Dev stuck, need TL | Internal/informal |

### Investigator (`agents/investigator.md`)

| Status Code | Meaning | Intended Route |
|-------------|---------|----------------|
| `ROOT_CAUSE_FOUND` | Investigation complete | **Tech Lead** (for validation) |
| `INVESTIGATION_INCOMPLETE` | Max iterations reached | Tech Lead (partial review) |
| `BLOCKED` | External blocker | Tech Lead |
| `EXHAUSTED` | All hypotheses eliminated | Tech Lead |
| `NEED_DEVELOPER_DIAGNOSTIC` | Need code instrumentation | Developer |
| `HYPOTHESIS_ELIMINATED` | Theory disproven | Internal loop (respawn Investigator) |
| `NEED_MORE_ANALYSIS` | Need deeper analysis | Internal loop (respawn Investigator) |

### Requirements Engineer (`agents/requirements_engineer.md`)

| Status Code | Meaning | Intended Route |
|-------------|---------|----------------|
| `READY_FOR_REVIEW` | Research complete | Tech Lead (bypass_qa: true) |
| `BLOCKED` | Need external access | Investigator |
| `PARTIAL` | Partial findings | Respawn RE |

---

## Current transitions.json Configuration

```json
{
  "developer": {
    "READY_FOR_QA": { "next_agent": "qa_expert" },
    "READY_FOR_REVIEW": { "next_agent": "tech_lead" },
    "BLOCKED": { "next_agent": "investigator", "fallback_agent": "tech_lead" },
    "PARTIAL": { "next_agent": "developer", "action": "respawn" },
    "INCOMPLETE": { "next_agent": "developer", "action": "respawn" },
    "ESCALATE_SENIOR": { "next_agent": "senior_software_engineer" },
    "NEEDS_TECH_LEAD_VALIDATION": { "next_agent": "tech_lead" }
  },
  "senior_software_engineer": {
    "READY_FOR_QA": { "next_agent": "qa_expert" },
    "READY_FOR_REVIEW": { "next_agent": "tech_lead" },
    "BLOCKED": { "next_agent": "tech_lead" },
    "NEEDS_TECH_LEAD_VALIDATION": { "next_agent": "tech_lead" }
    // ❌ MISSING: ROOT_CAUSE_FOUND
  },
  "qa_expert": {
    "PASS": { "next_agent": "tech_lead" },
    "FAIL": { "next_agent": "developer", "escalation_check": true },
    "FAIL_ESCALATE": { "next_agent": "senior_software_engineer" },
    "PARTIAL": { "next_agent": "tech_lead" },
    "BLOCKED": { "next_agent": "tech_lead" },
    "FLAKY": { "next_agent": "tech_lead" }
  },
  "tech_lead": {
    "APPROVED": { "next_agent": "developer", "action": "spawn_merge", "then": "check_phase" },
    "CHANGES_REQUESTED": { "next_agent": "developer", "escalation_check": true },
    "SPAWN_INVESTIGATOR": { "next_agent": "investigator" },
    "ESCALATE_TO_OPUS": { "next_agent": "tech_lead", "model_override": "opus" },
    "UNBLOCKING_GUIDANCE_PROVIDED": { "next_agent": "_return_to_blocked" },
    "ARCHITECTURAL_DECISION_MADE": { "next_agent": "developer" }
  },
  "project_manager": {
    "PLANNING_COMPLETE": { "next_agent": "developer", "action": "spawn_batch" },
    "CONTINUE": { "next_agent": "developer", "action": "spawn_batch" },
    "BAZINGA": { "next_agent": null, "action": "validate_then_end" },
    "NEEDS_CLARIFICATION": { "next_agent": null, "action": "pause_for_user" },
    "INVESTIGATION_NEEDED": { "next_agent": "investigator" },
    "INVESTIGATION_ONLY": { "next_agent": null, "action": "end_session" }
  },
  "investigator": {
    "ROOT_CAUSE_FOUND": { "next_agent": "developer" },  // ❌ WRONG
    "INCOMPLETE": { ... },                              // ❌ WRONG NAME
    "BLOCKED": { "next_agent": "tech_lead" },
    "EXHAUSTED": { "next_agent": "tech_lead" },
    "WAITING_FOR_RESULTS": { "next_agent": "developer" } // ❌ WRONG NAME
  },
  "requirements_engineer": {
    "READY_FOR_REVIEW": { "next_agent": "tech_lead", "bypass_qa": true },
    "BLOCKED": { "next_agent": "investigator" },
    "PARTIAL": { "next_agent": "requirements_engineer", "action": "respawn" }
  }
}
```

---

## Gap Analysis

### ❌ Gap 1: SSE Missing ROOT_CAUSE_FOUND

**Current:** `senior_software_engineer` section has no `ROOT_CAUSE_FOUND` entry

**Agent says (SSE agent:1144):**
> "ROOT_CAUSE_FOUND - Identified root cause, need PM decision"

**Correct route:** `project_manager`

**Impact:** If SSE returns ROOT_CAUSE_FOUND, workflow router has no rule → undefined behavior

### ❌ Gap 2: Investigator ROOT_CAUSE_FOUND Routes to Wrong Agent

**Current:** Routes to `developer`
**Agent says (investigator.md:689):**
> "Next Step: Routing back to Tech Lead for validation and decision"

**Correct route:** `tech_lead`

**Impact:** Developer receives unvalidated root cause → potentially implements wrong fix

### ❌ Gap 3: Investigator Status Code Name Mismatch (INCOMPLETE)

**Current:** transitions.json uses `INCOMPLETE`
**Agent uses:** `INVESTIGATION_INCOMPLETE`

**Impact:** Investigator returns `INVESTIGATION_INCOMPLETE`, workflow router doesn't recognize it

### ❌ Gap 4: Investigator Status Code Name Mismatch (WAITING_FOR_RESULTS)

**Current:** transitions.json uses `WAITING_FOR_RESULTS`
**Agent uses:** `NEED_DEVELOPER_DIAGNOSTIC`

**Impact:** Investigator returns `NEED_DEVELOPER_DIAGNOSTIC`, workflow router doesn't recognize it

### ⚠️ Gap 5: Developer Merge Status Codes Missing

**Current:** No merge status codes in transitions.json

**Orchestrator mentions (orchestrator.md:111):**
- `MERGE_SUCCESS`
- `MERGE_CONFLICT`
- `MERGE_TEST_FAILURE`
- `MERGE_BLOCKED`

**Impact:** These may be handled specially by orchestrator (via "then": "check_phase"), but should be documented in transitions.json for completeness

### ⚠️ Gap 6: SSE Missing PARTIAL Status

**Current:** SSE section has no `PARTIAL` entry
**Agent mentions:** PARTIAL as valid status (SSE agent:1176)

**Impact:** If SSE returns PARTIAL, no routing rule

### ❌ Gap 7: Tech Lead Status Name Mismatch (UNBLOCKING_GUIDANCE) [LLM-IDENTIFIED]

**Current:** transitions.json uses `UNBLOCKING_GUIDANCE_PROVIDED`
**Agent uses:** `UNBLOCKING_GUIDANCE` (per tech_lead.md:963)

**Impact:** Tech Lead returns `UNBLOCKING_GUIDANCE`, workflow router doesn't recognize it

### ❌ Gap 8: Investigator Internal Statuses Missing [LLM-IDENTIFIED]

**Current:** `HYPOTHESIS_ELIMINATED` and `NEED_MORE_ANALYSIS` not in transitions.json
**Marked as:** "Internal loop" but workflow-router expects explicit transitions

**Impact:** If these statuses aren't handled explicitly, they fall to unknown transition fallback (likely routing to Tech Lead), breaking the investigation loop

### ⚠️ Gap 9: Developer Merge Statuses Not in Agent File [LLM-IDENTIFIED]

**Current:** developer.md doesn't declare MERGE_* statuses
**Orchestrator mentions:** MERGE_SUCCESS, MERGE_CONFLICT, MERGE_TEST_FAILURE, MERGE_BLOCKED

**Impact:** Without agent file declaring them, response parser may not recognize them

---

## Root Cause Analysis: Why These Gaps Exist

1. **Investigator agent was defined after transitions.json** - Status codes evolved in agent file but config wasn't updated
2. **SSE ROOT_CAUSE_FOUND is rare** - Only happens when SSE identifies root cause during complex debugging
3. **Name standardization happened later** - Agent files adopted descriptive names, config kept old names
4. **Merge workflow is special-cased** - Handled by "then": "check_phase" logic, not standard routing

---

## Complete Mapping Table (Authoritative)

| Agent | Status Code | Route To | Action | Notes |
|-------|-------------|----------|--------|-------|
| **Developer** | READY_FOR_QA | qa_expert | spawn | Testing mode: full + integration tests |
| | READY_FOR_REVIEW | tech_lead | spawn | Testing mode: disabled/minimal OR unit-only |
| | BLOCKED | investigator | spawn | fallback: tech_lead |
| | PARTIAL | developer | respawn | |
| | INCOMPLETE | developer | respawn | Alias for PARTIAL |
| | ESCALATE_SENIOR | senior_software_engineer | spawn | |
| | NEEDS_TECH_LEAD_VALIDATION | tech_lead | spawn | |
| | MERGE_SUCCESS | _check_phase | special | Post-merge continue |
| | MERGE_CONFLICT | developer | respawn | Resolve conflicts |
| | MERGE_TEST_FAILURE | developer | respawn | Fix failing tests |
| | MERGE_BLOCKED | tech_lead | spawn | Permissions/policy |
| **SSE** | READY_FOR_QA | qa_expert | spawn | |
| | READY_FOR_REVIEW | tech_lead | spawn | |
| | BLOCKED | tech_lead | spawn | |
| | NEEDS_TECH_LEAD_VALIDATION | tech_lead | spawn | |
| | **ROOT_CAUSE_FOUND** | **project_manager** | spawn | **NEW** - PM decides next |
| | PARTIAL | senior_software_engineer | respawn | **NEW** |
| **QA Expert** | PASS | tech_lead | spawn | |
| | FAIL | developer | respawn | escalation_check: true |
| | FAIL_ESCALATE | senior_software_engineer | spawn | Level 3-5 failures |
| | PARTIAL | tech_lead | spawn | |
| | BLOCKED | tech_lead | spawn | |
| | FLAKY | tech_lead | spawn | |
| **Tech Lead** | APPROVED | developer | spawn_merge | then: check_phase |
| | CHANGES_REQUESTED | developer | respawn | escalation_check: true |
| | SPAWN_INVESTIGATOR | investigator | spawn | |
| | ESCALATE_TO_OPUS | tech_lead | respawn | model_override: opus |
| | UNBLOCKING_GUIDANCE_PROVIDED | _return_to_blocked | spawn | |
| | ARCHITECTURAL_DECISION_MADE | developer | spawn | |
| **PM** | PLANNING_COMPLETE | developer | spawn_batch | max_parallel: 4 |
| | CONTINUE | developer | spawn_batch | |
| | BAZINGA | null | validate_then_end | |
| | NEEDS_CLARIFICATION | null | pause_for_user | |
| | INVESTIGATION_NEEDED | investigator | spawn | |
| | INVESTIGATION_ONLY | null | end_session | |
| **Investigator** | **ROOT_CAUSE_FOUND** | **tech_lead** | spawn | **FIX** - was developer |
| | **INVESTIGATION_INCOMPLETE** | tech_lead | spawn | **FIX** - was INCOMPLETE |
| | BLOCKED | tech_lead | spawn | |
| | EXHAUSTED | tech_lead | spawn | |
| | **NEED_DEVELOPER_DIAGNOSTIC** | developer | spawn | **FIX** - was WAITING_FOR_RESULTS |
| | **HYPOTHESIS_ELIMINATED** | investigator | respawn | **NEW** - was marked internal, needs explicit transition |
| | **NEED_MORE_ANALYSIS** | investigator | respawn | **NEW** - was marked internal, needs explicit transition |
| **RE** | READY_FOR_REVIEW | tech_lead | spawn | bypass_qa: true |
| | BLOCKED | investigator | spawn | |
| | PARTIAL | requirements_engineer | respawn | |

---

## Fix Plan

### Priority 1: Critical Routing Fixes

#### Fix 1.1: Add SSE ROOT_CAUSE_FOUND

```json
"senior_software_engineer": {
  // ... existing entries ...
  "ROOT_CAUSE_FOUND": {
    "next_agent": "project_manager",
    "action": "spawn",
    "include_context": ["root_cause_analysis", "recommendation", "evidence"]
  }
}
```

#### Fix 1.2: Update Investigator ROOT_CAUSE_FOUND

```json
"investigator": {
  "ROOT_CAUSE_FOUND": {
    "next_agent": "tech_lead",  // Changed from "developer"
    "action": "spawn",
    "include_context": ["root_cause", "fix_guidance", "investigation_summary", "evidence"]
  }
}
```

#### Fix 1.3: Rename INCOMPLETE → INVESTIGATION_INCOMPLETE

```json
"investigator": {
  "INVESTIGATION_INCOMPLETE": {  // Changed from "INCOMPLETE"
    "next_agent": "tech_lead",
    "action": "spawn",
    "include_context": ["partial_findings", "iterations_completed", "hypotheses_tested", "next_steps"]
  }
}
```

#### Fix 1.4: Rename WAITING_FOR_RESULTS → NEED_DEVELOPER_DIAGNOSTIC

```json
"investigator": {
  "NEED_DEVELOPER_DIAGNOSTIC": {  // Changed from "WAITING_FOR_RESULTS"
    "next_agent": "developer",
    "action": "spawn",
    "include_context": ["diagnostic_request", "hypothesis", "expected_output"]
  }
}
```

### Priority 2: Completeness Fixes

#### Fix 2.1: Add SSE PARTIAL

```json
"senior_software_engineer": {
  // ... existing entries ...
  "PARTIAL": {
    "next_agent": "senior_software_engineer",
    "action": "respawn",
    "include_context": ["partial_work", "remaining_tasks"]
  }
}
```

#### Fix 2.2: Add Developer Merge Status Codes (Optional - May Be Special-Cased)

```json
"developer": {
  // ... existing entries ...
  "MERGE_SUCCESS": {
    "next_agent": "_check_phase",
    "action": "continue",
    "include_context": ["merge_result"]
  },
  "MERGE_CONFLICT": {
    "next_agent": "developer",
    "action": "respawn",
    "include_context": ["conflict_files", "resolution_hints"]
  },
  "MERGE_TEST_FAILURE": {
    "next_agent": "developer",
    "action": "respawn",
    "include_context": ["failing_tests", "test_output"]
  },
  "MERGE_BLOCKED": {
    "next_agent": "tech_lead",
    "action": "spawn",
    "include_context": ["blocker_reason"]
  }
}
```

**Note:** Merge status codes may already be handled by orchestrator's `"then": "check_phase"` logic. Verify before adding.

### Priority 3: LLM-Identified Fixes

#### Fix 3.1: Add Tech Lead UNBLOCKING_GUIDANCE Alias

```json
"tech_lead": {
  // ... existing entries ...
  "UNBLOCKING_GUIDANCE": {
    "next_agent": "_return_to_blocked",
    "action": "spawn",
    "include_context": ["guidance", "unblocking_steps"]
  }
  // Keep UNBLOCKING_GUIDANCE_PROVIDED as alias for backward compat
}
```

**Alternative:** Standardize on one name in tech_lead.md and transitions.json (prefer shorter `UNBLOCKING_GUIDANCE`).

#### Fix 3.2: Add Investigator HYPOTHESIS_ELIMINATED and NEED_MORE_ANALYSIS

```json
"investigator": {
  // ... existing entries ...
  "HYPOTHESIS_ELIMINATED": {
    "next_agent": "investigator",
    "action": "respawn",
    "include_context": ["eliminated_hypothesis", "next_hypothesis", "iteration", "evidence"],
    "iteration_budget_check": true
  },
  "NEED_MORE_ANALYSIS": {
    "next_agent": "investigator",
    "action": "respawn",
    "include_context": ["analysis_needed", "current_hypothesis", "iteration"],
    "iteration_budget_check": true
  }
}
```

#### Fix 3.3: Route SSE ROOT_CAUSE_FOUND via Tech Lead (LLM Recommendation)

**Original proposal:** SSE ROOT_CAUSE_FOUND → project_manager
**LLM recommendation:** SSE ROOT_CAUSE_FOUND → tech_lead (with mandatory_review: true)

**Rationale:** Consistent with Investigator ROOT_CAUSE_FOUND → tech_lead pattern. TL validates technical findings before PM makes project decisions.

```json
"senior_software_engineer": {
  "ROOT_CAUSE_FOUND": {
    "next_agent": "tech_lead",  // Changed from project_manager
    "action": "spawn",
    "mandatory_review": true,
    "include_context": ["root_cause_analysis", "recommendation", "evidence"]
  }
}
```

**User Decision Required:** Accept LLM recommendation (SSE → TL → PM) or keep original (SSE → PM)?

---

## Complete Updated transitions.json (Investigator Section)

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
  },
  "HYPOTHESIS_ELIMINATED": {
    "next_agent": "investigator",
    "action": "respawn",
    "include_context": ["eliminated_hypothesis", "next_hypothesis", "iteration", "evidence"],
    "iteration_budget_check": true
  },
  "NEED_MORE_ANALYSIS": {
    "next_agent": "investigator",
    "action": "respawn",
    "include_context": ["analysis_needed", "current_hypothesis", "iteration"],
    "iteration_budget_check": true
  }
}
```

## Complete Updated transitions.json (SSE Section)

```json
"senior_software_engineer": {
  "READY_FOR_QA": {
    "next_agent": "qa_expert",
    "action": "spawn",
    "include_context": ["dev_output", "files_changed", "test_results"]
  },
  "READY_FOR_REVIEW": {
    "next_agent": "tech_lead",
    "action": "spawn",
    "include_context": ["dev_output", "files_changed"]
  },
  "BLOCKED": {
    "next_agent": "tech_lead",
    "action": "spawn",
    "include_context": ["blocker_details"]
  },
  "NEEDS_TECH_LEAD_VALIDATION": {
    "next_agent": "tech_lead",
    "action": "spawn",
    "include_context": ["validation_request"]
  },
  "ROOT_CAUSE_FOUND": {
    "next_agent": "project_manager",
    "action": "spawn",
    "include_context": ["root_cause_analysis", "recommendation", "evidence"]
  },
  "PARTIAL": {
    "next_agent": "senior_software_engineer",
    "action": "respawn",
    "include_context": ["partial_work", "remaining_tasks"]
  }
}
```

---

## Validation Checklist

After implementation:

- [ ] Investigator ROOT_CAUSE_FOUND → tech_lead (not developer)
- [ ] Investigator uses INVESTIGATION_INCOMPLETE (not INCOMPLETE)
- [ ] Investigator uses NEED_DEVELOPER_DIAGNOSTIC (not WAITING_FOR_RESULTS)
- [ ] SSE has ROOT_CAUSE_FOUND → project_manager
- [ ] SSE has PARTIAL → respawn SSE
- [ ] Grep for old status names shows 0 matches in transitions.json
- [ ] Config-seeder re-run (if using database-backed routing)
- [ ] Manual test: Investigator returning ROOT_CAUSE_FOUND routes correctly

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking existing sessions | Low | Medium | Old status codes never worked anyway |
| Merge status routing conflicts | Medium | Low | Verify orchestrator handles separately |
| Config-seeder not picking up changes | Low | Medium | Verify seeding script path |
| SSE ROOT_CAUSE_FOUND unexpected behavior | Low | Low | Rare path, PM handles gracefully |

---

## Implementation Order

1. **Update transitions.json** - Apply all 6 fixes
2. **Create investigation_loop.md** - Template for orchestrator (separate task)
3. **Update INVESTIGATION_WORKFLOW.md** - Mark gaps as fixed
4. **Re-seed database** - If using config-seeder
5. **Test routing** - Manual verification of critical paths

---

## Questions for LLM Review

1. **SSE ROOT_CAUSE_FOUND → PM**: Is this the correct destination? SSE says "need PM decision" but should it go through Tech Lead first for validation?

2. **Merge status codes in transitions.json**: The orchestrator uses `"then": "check_phase"` for APPROVED. Are merge statuses handled separately and don't need explicit transitions.json entries?

3. **Internal investigator statuses**: HYPOTHESIS_ELIMINATED and NEED_MORE_ANALYSIS are internal loop statuses. Should they have transitions.json entries as fallback, or is omission correct?

4. **PM informal statuses**: IN_PROGRESS, REASSIGNING_FOR_FIXES, ESCALATING_TO_TECH_LEAD appear in PM agent but not transitions.json. Are these intentionally informal/internal?

5. **Investigator → Tech Lead (all exits)**: All investigator exit statuses go to tech_lead. Is this correct, or should some (like EXHAUSTED) go to PM?

---

## Multi-LLM Review Integration

### Critical Issues Identified (OpenAI GPT-5)

The OpenAI review identified **5 critical issues** and **6 missing considerations**:

#### Critical Issues (Must Fix)

1. **Tech Lead status name mismatch** - `UNBLOCKING_GUIDANCE` vs `UNBLOCKING_GUIDANCE_PROVIDED`
   - **Action:** Add Gap 7, create Fix 3.1 with alias

2. **Investigator iterative statuses missing** - `HYPOTHESIS_ELIMINATED` and `NEED_MORE_ANALYSIS` excluded as "internal"
   - **Action:** Add Gap 8, create Fix 3.2 with explicit transitions

3. **SSE ROOT_CAUSE_FOUND routing inconsistency** - Direct to PM bypasses TL validation
   - **Action:** Create Fix 3.3 to route via tech_lead first (matches Investigator pattern)
   - **User Decision Required:** Accept this change or keep original?

4. **Developer merge statuses not declared in developer.md**
   - **Action:** Add Gap 9, note in implementation order

5. **Workflow-router/config-seeder coupling not addressed**
   - **Action:** Added to implementation order

#### Missing Considerations (Should Address)

1. **response_parsing.md alignment** - Parser must recognize new/renamed statuses
   - **Action:** Added to implementation order

2. **Backward compatibility/migration** - Existing sessions may have old status names
   - **Action:** Add alias layer recommendation

3. **include_context payload contracts** - Verify receiving agents can read proposed keys
   - **Action:** Note for implementation verification

4. **PM informal statuses** - IN_PROGRESS, REASSIGNING_FOR_FIXES, ESCALATING_TO_TECH_LEAD
   - **Action:** Document as intentionally informal (no transition needed)

5. **security_sensitive override interplay** - Ensure applies to SSE ROOT_CAUSE_FOUND
   - **Action:** Add note to SSE section

6. **Automated consistency checks** - Suggest CI validation
   - **Action:** Add to future improvements

### Incorporated Feedback

| Issue | Original | Correction |
|-------|----------|------------|
| TL status mismatch | Not identified | Added Gap 7, Fix 3.1 |
| Investigator internal statuses | Marked as "internal" | Added to transitions.json (Fix 3.2) |
| SSE ROOT_CAUSE_FOUND route | → project_manager | → tech_lead (pending user decision) |
| Merge status in agent | Not in developer.md | Added Gap 9, implementation note |
| response_parsing.md | Not mentioned | Added to implementation order |
| Backward compat | Not mentioned | Added alias layer recommendation |

### Rejected Suggestions (With Reasoning)

1. **FSM schema with generator** - Good idea but out of scope for this fix
   - Reason: Adds complexity, recommend as follow-up enhancement

2. **Soft-deprecate old status names** - Unnecessary complexity
   - Reason: Old statuses never worked; no sessions depend on them

3. **Gate all ROOT_CAUSE via TL** - Partially accepted
   - Accept: SSE ROOT_CAUSE_FOUND → TL (consistent with Investigator)
   - Reject: Already the case for Investigator, no change needed there

### Backward Compatibility: Alias Layer

To support any existing sessions with old status names, add aliases in workflow-router:

```python
STATUS_ALIASES = {
    "INCOMPLETE": "INVESTIGATION_INCOMPLETE",
    "WAITING_FOR_RESULTS": "NEED_DEVELOPER_DIAGNOSTIC",
    "UNBLOCKING_GUIDANCE_PROVIDED": "UNBLOCKING_GUIDANCE",
}

def normalize_status(status: str) -> str:
    return STATUS_ALIASES.get(status, status)
```

### Confidence Assessment

**Before review:** Medium - Comprehensive but untested against full system
**After review:** High - With LLM-identified fixes, design is robust

---

## Updated Implementation Order (Post-Review)

1. **Update transitions.json** - Apply all 9 fixes:
   - Fix 1.1: SSE ROOT_CAUSE_FOUND → tech_lead (updated per LLM)
   - Fix 1.2: Investigator ROOT_CAUSE_FOUND → tech_lead
   - Fix 1.3: Rename INCOMPLETE → INVESTIGATION_INCOMPLETE
   - Fix 1.4: Rename WAITING_FOR_RESULTS → NEED_DEVELOPER_DIAGNOSTIC
   - Fix 2.1: Add SSE PARTIAL
   - Fix 2.2: Add Developer merge statuses (optional)
   - Fix 3.1: Add Tech Lead UNBLOCKING_GUIDANCE alias
   - Fix 3.2: Add Investigator HYPOTHESIS_ELIMINATED and NEED_MORE_ANALYSIS
   - Fix 3.3: (Depends on user decision for SSE route)

2. **Update response_parsing.md** - Add new/renamed status codes to parser

3. **Add status alias layer to workflow-router** - Backward compatibility

4. **Update developer.md** - Declare merge status codes (optional)

5. **Create investigation_loop.md** - Template for orchestrator (separate task from investigation-loop-template-ultrathink.md)

6. **Update INVESTIGATION_WORKFLOW.md** - Mark gaps as fixed

7. **Bump transitions.json version** - From 1.0.0 to 1.1.0

8. **Re-seed database** - If using config-seeder

9. **Test routing** - Manual verification of critical paths

---

## Updated Validation Checklist (Post-Review)

**Implementation completed:** 2025-12-23

- [x] Investigator ROOT_CAUSE_FOUND → tech_lead (not developer)
- [x] Investigator uses INVESTIGATION_INCOMPLETE (not INCOMPLETE)
- [x] Investigator uses NEED_DEVELOPER_DIAGNOSTIC (not WAITING_FOR_RESULTS)
- [x] Investigator has HYPOTHESIS_ELIMINATED → respawn investigator
- [x] Investigator has NEED_MORE_ANALYSIS → respawn investigator
- [x] SSE has ROOT_CAUSE_FOUND → tech_lead (per LLM recommendation)
- [x] SSE has PARTIAL → respawn SSE
- [x] Tech Lead has UNBLOCKING_GUIDANCE (alias for UNBLOCKING_GUIDANCE_PROVIDED)
- [x] response_parsing.md updated with all renamed statuses
- [x] transitions.json version bumped to 1.1.0
- [x] orchestrator.md status routing table updated
- [x] INVESTIGATION_WORKFLOW.md Known Gaps section updated
- [x] Backward compat aliases added to transitions.json (`_status_aliases` section)
- [ ] Config-seeder re-run (if using database-backed routing) - N/A for now
- [ ] Manual test: Each new/fixed status routes correctly - Pending integration test

---

## References

- `agents/developer.md` - Developer status codes (lines 1028-1032)
- `agents/senior_software_engineer.md` - SSE status codes (lines 1140-1144)
- `agents/qa_expert.md` - QA status codes (lines 1173-1184)
- `agents/tech_lead.md` - Tech Lead status codes (lines 1024-1028)
- `agents/project_manager.md` - PM status codes (lines 86-94)
- `agents/investigator.md` - Investigator status codes (lines 931-935)
- `agents/requirements_engineer.md` - RE status codes (lines 741-744)
- `agents/orchestrator.md` - Status routing table (lines 107-124)
- `bazinga/config/transitions.json` - Current configuration
- `templates/response_parsing.md` - Response parser templates
