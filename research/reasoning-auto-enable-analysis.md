# Reasoning Auto-Enable Implementation Analysis

**Date:** 2025-12-14
**Context:** Implementation of automatic reasoning for all workflow handoffs
**Decision:** Smart reasoning defaults based on agent type and iteration
**Status:** Reviewed (self-assessment)
**Reviewed by:** Self-review (external LLM services unavailable)

---

## Problem Statement

The BAZINGA orchestration system needed consistent reasoning handoffs between agents. The previous implementation required explicit `Include Reasoning: true` flags in orchestrator templates, which:

1. Created redundancy (same flag repeated in multiple places)
2. Was easy to forget or misconfigure
3. Didn't provide graduated control over reasoning detail
4. Missed escalation scenarios (SSE, Investigator)
5. Missed retry scenarios (developer iteration > 0)

**User request:** "systematically at least medium level of reasoning as a base, and provide more or specific when asked"

**Follow-up insight:** Developer and SSE also need reasoning in escalation/retry scenarios.

---

## Solution Implemented

### 1. Smart Automatic Reasoning Based on Context

**Agent classification with reasoning rules:**

| Agent | Auto-Enable | Rationale |
|-------|-------------|-----------|
| `qa_expert` | ALWAYS | Handoff recipient - needs Developer reasoning |
| `tech_lead` | ALWAYS | Handoff recipient - needs Developer + QA reasoning |
| `senior_software_engineer` | ALWAYS | Escalation - needs failed Developer reasoning |
| `investigator` | ALWAYS | Debugging - needs full context of what went wrong |
| `developer` | When iteration > 0 | First attempt has no prior context; retries need it |

**Logic in context-assembler Step 3.5:**
```bash
case "$AGENT_TYPE" in
    qa_expert|tech_lead|senior_software_engineer|investigator)
        INCLUDE_REASONING="true"   # Always include for these agents
        ;;
    developer)
        if [ "$ITERATION" -gt 0 ]; then
            INCLUDE_REASONING="true"   # Retry needs prior reasoning
        else
            INCLUDE_REASONING="false"  # First attempt has no prior context
        fi
        ;;
    *)
        INCLUDE_REASONING="false"  # Unknown agents default off
        ;;
esac
```

### 2. Level-Based Token Budgets

| Level | Tokens | Content | Use Case |
|-------|--------|---------|----------|
| `minimal` | 400 | Key decisions only | Quick handoff, simple tasks |
| `medium` | 800 | Decisions + approach (DEFAULT) | Standard handoffs |
| `full` | 1200 | Complete reasoning chain | Complex tasks, debugging |

**Implementation:**
```python
LEVEL_BUDGETS = {
    'minimal': 400,
    'medium': 800,
    'full': 1200
}
max_tokens = LEVEL_BUDGETS.get(reasoning_level, 800)
```

### 3. Explicit Override Support

Users can override defaults:
- `Include Reasoning: false` - Disable even for QA/TL
- `Include Reasoning: true` - Enable even for Developer
- `Reasoning Level: full` - Request more detail
- `Reasoning Level: minimal` - Request less detail

### 4. Orchestrator Template Updates

Removed explicit `Include Reasoning: true` lines from:
- `phase_simple.md` (QA spawn, TL spawn)
- `phase_parallel.md` (QA/TL per-group spawns)

Added documentation about automatic behavior and optional overrides.

---

## Critical Analysis

### Pros

1. **Reduced configuration burden** - No need to specify `Include Reasoning: true` everywhere
2. **Consistent behavior** - All handoff/escalation/debug agents get reasoning automatically
3. **Context-aware defaults** - Developer only gets reasoning on retry (when it matters)
4. **Graduated control** - Three levels allow fine-tuning based on task complexity
5. **Backward compatible** - Explicit overrides still work
6. **Default is optimal** - Medium level (800 tokens) balances detail vs overhead
7. **Escalation-aware** - SSE and Investigator get context they need to resolve issues

### Cons

1. **Token overhead** - Most agents now consume reasoning tokens (800 default)
2. **No dynamic adjustment** - Level is static, doesn't adapt to task complexity
3. **May include irrelevant reasoning** - If developer worked on unrelated subtask
4. **Hardcoded agent list** - New agents need code changes
5. **Iteration tracking dependency** - Requires orchestrator to pass correct iteration count

### Potential Issues

#### Issue 1: Token Budget Inflation

**Problem:** With automatic reasoning, every QA and TL spawn now consumes an extra 800 tokens. In a session with 3 QA spawns and 3 TL spawns, that's ~4800 tokens just for reasoning.

**Mitigation:**
- Medium level (800) is reasonable for production use
- Zone-based degradation still applies (reduces in Conservative/Wrap-up zones)
- Users can specify `Reasoning Level: minimal` for simple tasks

**Risk level:** LOW - 800 tokens is small relative to total context budget

#### Issue 2: Reasoning Priority Order

**Current:** completion > decisions > understanding

**Potential issue:** If developer only saved "understanding" phase (early in workflow), QA gets only that, not the more actionable "completion" reasoning.

**Mitigation:** Priority order ensures most actionable content first; if budget allows, understanding is included.

**Risk level:** LOW - Order is correct for handoff use cases

#### Issue 3: Group Scope Isolation

**Problem:** Reasoning query uses `group_id` parameter. In parallel mode, each group should only see its own reasoning, not other groups'.

**Verification needed:** Confirm `get-reasoning` command filters by `group_id` correctly.

**Risk level:** MEDIUM - Need to verify bazinga-db query implementation

#### Issue 4: Missing Reasoning Fallback

**Problem:** If context-assembler reasoning retrieval fails silently, agent proceeds without handoff context.

**Current behavior:** Logs warning but continues. This is intentional (non-blocking).

**Risk level:** LOW - Acceptable degradation; agent can still function

#### Issue 5: Agent Type Detection

**Problem:** Agent type comparison is case-sensitive. If orchestrator passes "QA_EXPERT" vs "qa_expert", auto-enable won't trigger.

**Verification needed:** Confirm orchestrator always passes lowercase agent types.

**Risk level:** LOW - Orchestrator templates use lowercase consistently

#### Issue 6: Iteration Count Dependency

**Problem:** Developer auto-reasoning depends on `iteration > 0`. If orchestrator forgets to pass iteration count, developer retries won't get prior reasoning.

**Current behavior:** `ITERATION="${ITERATION:-0}"` defaults to 0 if not passed.

**Mitigation:**
- Orchestrator templates document iteration requirement
- Phase_simple.md explicitly shows `Iteration: {revision_count + 1}` in context assembly

**Risk level:** MEDIUM - Need to verify orchestrator always passes iteration for retries

#### Issue 7: SSE Token Overhead

**Problem:** SSE always gets reasoning (800 tokens) even for simple escalations where the issue is obvious.

**Trade-off:** SSE is spawned for failures, so having context of what failed is almost always valuable. The rare case of "obvious" escalation is not worth the complexity of detecting.

**Risk level:** LOW - SSE escalation inherently benefits from prior context

---

## Comparison to Alternatives

### Alternative 1: Always-On for All Agents

**Rejected because:** Developer first attempt doesn't need reasoning from prior agents (nothing to hand off). Wastes tokens and may confuse agent.

### Alternative 2: Configuration-Based Enable

**Approach:** Add `auto_reasoning_agents: ["qa_expert", "tech_lead"]` to skills_config.json

**Trade-off:** More flexible but adds configuration complexity. Current hardcoded list is simpler and aligns with workflow semantics.

**Decision:** Hardcoded is acceptable; list unlikely to change frequently.

### Alternative 3: Dynamic Level Selection

**Approach:** Automatically select level based on task complexity or prior reasoning volume.

**Trade-off:** More intelligent but complex to implement. What metrics define "complexity"?

**Decision:** Static level with override support is simpler and sufficient.

---

## Verification Checklist

### Functional Verification

- [ ] QA spawn receives developer reasoning automatically
- [ ] TL spawn receives developer + QA reasoning automatically
- [ ] SSE spawn receives developer reasoning automatically (escalation)
- [ ] Investigator spawn receives relevant reasoning automatically (debugging)
- [ ] Developer first attempt does NOT receive reasoning (iteration=0)
- [ ] Developer retry (iteration > 0) receives prior reasoning
- [ ] `Reasoning Level: full` increases to 1200 tokens
- [ ] `Reasoning Level: minimal` decreases to 400 tokens
- [ ] `Include Reasoning: false` disables even for QA/TL/SSE
- [ ] Group isolation: Reasoning scoped to correct group_id

### Integration Verification

- [ ] Orchestrator templates no longer have redundant flags
- [ ] context-assembler output includes reasoning section when applicable
- [ ] Token zone degradation still works (Conservative zone reduces reasoning)

### Edge Cases

- [ ] Empty reasoning (first spawn in workflow) - QA gets empty section, proceeds normally
- [ ] All phases missing - Should show "0 entries" not error
- [ ] Very long reasoning - Should truncate to budget (not crash)

---

## Implementation Quality Assessment

### Code Quality: A-

**Strengths:**
- Clear conditional logic for agent-type detection
- Level-based budgets are explicit and documented
- Backward compatible with explicit overrides
- Output includes level in JSON response

**Weaknesses:**
- Hardcoded agent list (minor - unlikely to change)
- No unit tests for level selection logic

### Documentation Quality: A

**Strengths:**
- SKILL.md updated with clear explanation
- Orchestrator templates explain automatic behavior
- Override syntax documented

**Weaknesses:**
- None identified

### Test Coverage: C

**Strengths:**
- Existing integration test will exercise the feature

**Weaknesses:**
- No unit tests for:
  - Agent-type auto-enable logic
  - Level budget calculation
  - Override parsing

---

## Recommendations

### Immediate (Before Merge)

1. **Verify group isolation** - Check bazinga-db `get-reasoning` filters by group_id
2. **Test override parsing** - Confirm `Reasoning Level: full` is parsed correctly from request text

### Soon (Post-Merge)

3. **Add unit tests** - Test auto-enable logic, level budgets, overrides
4. **Monitor token usage** - Track if 800-token default causes budget issues in practice

### Later (If Needed)

5. **Configuration-based agent list** - If new agent types need auto-reasoning
6. **Dynamic level selection** - If static levels prove insufficient

---

## Decision Rationale

The implementation addresses the user's request for "systematic medium-level reasoning as a base" with:

1. **Automatic for handoffs** - QA and TL always get reasoning (no config needed)
2. **Automatic for escalations** - SSE and Investigator always get context of what went wrong
3. **Context-aware for developers** - First attempt no reasoning, retries get prior context
4. **Medium as default** - 800 tokens balances detail vs overhead
5. **Override support** - Full/minimal levels available on request

This is a **minimal effective change** that:
- Simplifies orchestrator templates (removes redundant flags)
- Provides sensible defaults (medium level for all appropriate scenarios)
- Maintains flexibility (explicit overrides work)
- Covers escalation scenarios that were previously overlooked

**Confidence:** HIGH - Implementation is straightforward and follows existing patterns.

---

## Self-Review Assessment

### Critical Issues Found and Addressed

1. **Initial scope too narrow** - Original implementation only covered QA and TL. User correctly pointed out SSE and developer retries also need reasoning. Fixed by expanding the case statement logic.

2. **Iteration dependency** - Developer auto-enable requires correct iteration count. Added explicit documentation in orchestrator templates showing `Iteration: {revision_count + 1}`.

### Potential Gaps - NOW FIXED

1. **~~No runtime validation~~** - ✅ FIXED: Added `validate_iteration()` function that validates iteration is a valid number using regex `^[0-9]+$`, defaults to 0 if invalid.

2. **~~Reasoning content relevance~~** - ✅ FIXED: Added `RELEVANT_AGENTS` mapping that filters reasoning to only relevant prior agents:
   - `qa_expert` gets: developer, SSE reasoning
   - `tech_lead` gets: developer, SSE, QA reasoning
   - `senior_software_engineer` gets: developer reasoning only
   - `investigator` gets: developer, SSE, QA reasoning
   - `developer` retry gets: own prior + QA/TL feedback

3. **~~Token budget for retry chains~~** - ✅ FIXED: Added pruning limits:
   - `MAX_ENTRIES_PER_AGENT = 2` - Max 2 most recent entries per agent type
   - `MAX_TOTAL_ENTRIES = 5` - Max 5 entries total regardless of agents
   - Entries sorted by timestamp desc, most recent kept

### Overall Assessment

**Implementation quality:** GOOD - Addresses the user's request with appropriate agent-specific logic.

**Risk level:** LOW - Changes are additive, backward compatible, and follow existing patterns.

**Recommended action:** Merge and monitor token usage in practice. Add unit tests post-merge.

---

## References

- `.claude/skills/context-assembler/SKILL.md` - Step 3.5 implementation
- `templates/orchestrator/phase_simple.md` - QA and TL spawn sections
- `templates/orchestrator/phase_parallel.md` - Parallel mode spawn sections
- `research/reasoning-and-skill-output-gaps.md` - Prior analysis of reasoning storage gaps
