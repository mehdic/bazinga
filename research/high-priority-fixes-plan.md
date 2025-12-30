# High Priority Fixes Implementation Plan

**Date:** 2025-12-30
**Context:** Implementation plan for HIGH priority gaps from P0/P1 self-review
**Status:** Planning
**Depends on:** Critical fixes (completed in commit 6077341)

---

## Overview

8 HIGH priority gaps identified from self-review + OpenAI review. Organized by implementation complexity and dependency.

---

## Phase 1: Quick Wins (No Dependencies)

### Gap #5: Old Taxonomy in Other Agents

**Problem:** Other agents may still use BLOCKER/IMPORTANT/SUGGESTION/NIT instead of CRITICAL/HIGH/MEDIUM/LOW.

**Implementation:**
1. Grep all agent files for old terms
2. Replace with unified taxonomy
3. Add deprecation note where terms are mentioned

**Files to audit:**
- `agents/developer.md`
- `agents/senior_software_engineer.md`
- `agents/qa_expert.md`
- `agents/project_manager.md`
- `agents/investigator.md`

**Estimated effort:** 30 minutes

---

### Gap #10: No Fallback for Old Handoff Format

**Problem:** Agents reading old handoffs may fail if new fields are missing.

**Implementation:**
Add fallback defaults when reading handoffs:
```python
notes_for_future = handoff.get("notes_for_future", [])
blocking_summary = handoff.get("blocking_summary", {
    "total_blocking": 0,
    "fixed": 0,
    "rejected_with_reason": 0,
    "unaddressed": 0
})
iteration_tracking = handoff.get("iteration_tracking", {})
```

**Files to update:**
- `agents/orchestrator.md` - Add fallback logic in handoff reading section
- `.claude/skills/bazinga-validator/SKILL.md` - Add fallback in blocking issue check

**Estimated effort:** 20 minutes

---

## Phase 2: Moderate Complexity

### Gap #3: Progress Tracking State Not Implemented

**Problem:** Orchestrator documents progress logic but doesn't persist state to compare iterations.

**Implementation:**
1. After TL CHANGES_REQUESTED, orchestrator must:
   - Read current blocking_count from TL handoff
   - Query previous iteration's blocking_count from DB
   - Compare to determine progress
   - Update DB with new counts

2. Database already has columns (added in schema v16):
   - `review_iteration` ✅
   - `no_progress_count` ✅
   - `blocking_issues_count` ✅

3. Add orchestrator logic:
```
# After receiving Dev/SSE response to CHANGES_REQUESTED:
previous_blocking = query task_group.blocking_issues_count
current_blocking = handoff.blocking_summary.total_blocking - handoff.blocking_summary.fixed

IF current_blocking < previous_blocking:
    progress = true
    no_progress_count = 0
ELSE:
    progress = false
    no_progress_count += 1

# Update DB
update task_group SET
    blocking_issues_count = current_blocking,
    no_progress_count = no_progress_count,
    review_iteration = review_iteration + 1
```

**Files to update:**
- `agents/orchestrator.md` - Add state query/update logic

**Estimated effort:** 45 minutes

---

### Gap #8: Escalation Warning is Static

**Problem:** Developer doesn't know "this is iteration 3 of 4 before escalation."

**Implementation:**
1. Orchestrator injects context when spawning Developer for re-review
2. Add to prompt-builder params:
   - `review_iteration`
   - `no_progress_count`
   - `max_iterations_before_escalation` (default: 4)

3. Add warning template to `templates/developer_speckit.md`:
```markdown
**⚠️ Escalation Warning:**
This is review iteration {review_iteration}. No-progress count: {no_progress_count}.
{IF no_progress_count >= max - 1}: One more round without progress will escalate to SSE.
```

**Files to update:**
- `agents/orchestrator.md` - Inject iteration context in spawn
- `.claude/skills/prompt-builder/SKILL.md` - Accept iteration params
- `templates/developer_speckit.md` - Add warning template section

**Estimated effort:** 1 hour

---

### Gap #4: Re-Rejection Prevention Unenforceable

**Problem:** TL can re-flag issues that were already overruled, and there's no validation.

**Implementation:**
1. Orchestrator reads previous iteration's `rejections_overruled` from handoff
2. Before routing TL response, check if any newly-flagged blocking issues were in `rejections_overruled`
3. If violation detected:
   - Log warning
   - Auto-accept the issue (treat as non-blocking)
   - Notify PM in next handoff

**Files to update:**
- `agents/orchestrator.md` - Add validation step after TL response

**Estimated effort:** 30 minutes

---

## Phase 3: Higher Complexity

### Gap #12: Parallel File Clobbering Risk

**Problem:** Up to 4 developers writing to shared `handoff_implementation.json` in parallel mode.

**Implementation:**
1. Change handoff naming to include agent ID:
   - `handoff_implementation_{agent_id}.json` (e.g., `handoff_implementation_developer_1.json`)

2. Keep stable alias for simple mode:
   - `handoff_implementation.json` → symlink or copy of latest

3. Update artifact path construction in:
   - Developer/SSE agents
   - Orchestrator reading logic
   - QA Expert reading logic
   - Tech Lead reading logic

**Files to update:**
- `agents/developer.md` - Use agent_id in handoff path
- `agents/senior_software_engineer.md` - Same
- `agents/orchestrator.md` - Update reading logic
- `agents/qa_expert.md` - Update reading logic
- `agents/tech_lead.md` - Update reading logic

**Estimated effort:** 1.5 hours

---

### Gap #14: Event Payload Governance Missing

**Problem:** No schema/versioning for tl_issues/tl_issue_responses events.

**Implementation:**
1. Create event schemas in `bazinga/schemas/`:
   - `event_tl_issues.schema.json`
   - `event_tl_issue_responses.schema.json`

2. Add dedup key: `(session_id, group_id, iteration, event_type)`

3. Update bazinga-db `save-event` to:
   - Validate against schema
   - Check for duplicate by key
   - Return existing event if duplicate (idempotent)

**Files to update:**
- Create `bazinga/schemas/event_tl_issues.schema.json`
- Create `bazinga/schemas/event_tl_issue_responses.schema.json`
- `.claude/skills/bazinga-db/SKILL.md` - Add validation note
- `.claude/skills/bazinga-db/scripts/bazinga_db.py` - Add schema validation (optional)

**Estimated effort:** 1 hour

---

### Gap #15: Capability Discovery Missing

**Problem:** Orchestrator assumes skills exist, no fallback if disabled.

**Implementation:**
1. At session init, orchestrator reads `bazinga/skills_config.json`
2. Check which skills are enabled/disabled
3. For each disabled skill, use documented fallback:
   - `lint-check` disabled → Skip lint validation
   - `security-scan` disabled → Skip security check (warn)
   - `test-coverage` disabled → Skip coverage check

4. Surface warning for critical disabled skills

**Files to update:**
- `agents/orchestrator.md` - Add capability check at init
- Document fallback behavior per skill

**Estimated effort:** 45 minutes

---

## Implementation Order

| Order | Gap | Effort | Dependencies |
|-------|-----|--------|--------------|
| 1 | #5 Old taxonomy | 30m | None |
| 2 | #10 Fallback for old handoffs | 20m | None |
| 3 | #3 Progress tracking | 45m | None |
| 4 | #4 Re-rejection prevention | 30m | None |
| 5 | #8 Escalation warning | 1h | #3 (uses iteration count) |
| 6 | #15 Capability discovery | 45m | None |
| 7 | #14 Event payload governance | 1h | Schemas in place |
| 8 | #12 Parallel file clobbering | 1.5h | None (but complex) |

**Total estimated effort:** ~6.5 hours

---

## Acceptance Criteria

### Gap #3 - Progress Tracking
- [ ] Orchestrator queries previous blocking count from DB
- [ ] Compares current vs previous to determine progress
- [ ] Updates DB with new counts
- [ ] no_progress_count resets on progress, increments otherwise

### Gap #4 - Re-Rejection Prevention
- [ ] Orchestrator reads rejections_overruled from previous iteration
- [ ] Validates TL response doesn't re-flag overruled issues
- [ ] Auto-accepts violations with warning

### Gap #5 - Old Taxonomy
- [ ] No BLOCKER/IMPORTANT/SUGGESTION/NIT in any agent file
- [ ] Deprecation note added where old terms mentioned

### Gap #8 - Escalation Warning
- [ ] Developer receives iteration count in prompt
- [ ] Warning appears when near escalation threshold
- [ ] Warning is dynamic (not static text)

### Gap #10 - Old Handoff Fallback
- [ ] Agents gracefully handle missing notes_for_future
- [ ] Agents gracefully handle missing blocking_summary
- [ ] Agents gracefully handle missing iteration_tracking

### Gap #12 - Parallel File Clobbering
- [ ] Each developer writes to unique handoff file
- [ ] Orchestrator reads correct file per agent
- [ ] Simple mode still works with single file

### Gap #14 - Event Payload Governance
- [ ] Event schemas created for tl_issues and tl_issue_responses
- [ ] Dedup key prevents duplicate events
- [ ] Invalid payloads rejected or warned

### Gap #15 - Capability Discovery
- [ ] Orchestrator reads skills_config at init
- [ ] Disabled skills have documented fallbacks
- [ ] Warning surfaced for critical disabled skills

---

## Next Steps

1. Get user approval for this plan
2. Implement in order (1-8)
3. Commit after each logical group
4. Update self-review document status
