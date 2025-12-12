# Phase 4 Implementation Analysis: Graduated Token Management

**Date:** 2025-12-12
**Context:** Critical analysis of Phase 4 (User Story 2) implementation for context-assembler skill
**Decision:** Implemented Phase 4.1 + 4.2 fixes
**Status:** Implemented (v1.4.0)
**Reviewed by:** OpenAI GPT-5 (2025-12-12)

---

## Problem Statement

Phase 4 implements "Graduated Token Management" (FR-003, FR-004) - token budget enforcement with 5 graduated zones for graceful degradation. The goal is to prevent agents from being cut off mid-task by proactively adjusting context based on token usage.

## Implementation Summary

### What Was Implemented

1. **Token Zone Detection (Step 2c in SKILL.md)**
   - Python script that determines zone based on MODEL and CURRENT_TOKENS
   - 5 zones: Normal (0-60%), Soft Warning (60-75%), Conservative (75-85%), Wrap-up (85-95%), Emergency (95%+)
   - Uses tiktoken for encoding detection (cl100k_base)
   - 15% safety margin on model limits

2. **Zone-Aware Query Behavior (Step 3)**
   - Emergency: Skip to output
   - Wrap-up: Skip context packages
   - Conservative: Query only critical packages (LIMIT=1)
   - Soft Warning: Normal query, prefer summaries
   - Normal: Full context query

3. **Zone-Specific Output Formatting (Step 5)**
   - Different output templates for each zone
   - Zone indicators (🔶, 🚨)
   - Truncation for higher zones

4. **Token Budget Allocation Tables**
   - Per-agent type percentages documented
   - Developer: 50/20/20/10, SSE: 40/20/25/15, QA: 40/15/30/15, Tech Lead: 30/15/40/15

5. **Documentation Updates**
   - usage.md with tiktoken dependency
   - spec.md, plan.md, tasks.md with SSE additions

---

## Critical Analysis

### Issue 1: Token Counting is Not Actually Implemented

**Severity:** HIGH

**Problem:** The implementation relies on `current_tokens` being passed as a parameter, but:
- Claude Code does NOT expose token usage to skills
- The orchestrator has no mechanism to track/provide this value
- Default value of 0 means zone will ALWAYS be "Normal"

**Evidence:**
```bash
# From SKILL.md Step 1
- `current_tokens`: Current token usage in conversation (OPTIONAL, for zone detection)

# From Step 2c
CURRENT_TOKENS=0  # Current usage if known, else 0
```

**Impact:** The entire zone detection system is effectively disabled in practice because there's no way to get `current_tokens`.

**Fix Required:** Either:
1. Document this as "future capability" requiring orchestrator changes
2. Implement token estimation of the context being assembled (count tokens in packages)
3. Use heuristics (message count, conversation length) as proxy

---

### Issue 2: Budget Allocation Percentages Are Documentation Only

**Severity:** MEDIUM

**Problem:** The token budget allocation tables (Task 50%, Specialization 20%, etc.) are documented but never enforced.

**Evidence:**
```markdown
| Agent | Task | Specialization | Context Pkgs | Errors |
|-------|------|----------------|--------------|--------|
| developer | 50% | 20% | 20% | 10% |
```

There's no code that:
- Calculates what 20% of the budget means in tokens
- Limits context packages to 20% of budget
- Enforces any of these allocations

**Impact:** The percentages are aspirational documentation, not functional constraints.

**Fix Required:** Either:
1. Remove the tables as misleading (they imply enforcement)
2. Add actual budget calculation and enforcement logic
3. Clearly mark as "recommended allocation" not "enforced allocation"

---

### Issue 3: SKILL.md Step 1 Missing SSE in Agent Type List

**Severity:** LOW

**Problem:** After adding SSE to all tables, Step 1 still lists:
```
- `agent_type`: Target agent - developer/qa_expert/tech_lead (REQUIRED)
```

Should include `senior_software_engineer`.

**Fix Required:** Update to:
```
- `agent_type`: Target agent - developer/senior_software_engineer/qa_expert/tech_lead (REQUIRED)
```

---

### Issue 4: "Prefer Summaries" Logic is Vacuous

**Severity:** MEDIUM

**Problem:** Soft Warning zone says "prefer summaries over full content", but:
- The skill ALWAYS uses summaries (from `summary` column)
- There's no "full content" mode implemented
- The distinction is meaningless

**Evidence from output templates:**
```markdown
# Normal zone
**[{PRIORITY}]** {file_path}
> {summary}

# Soft Warning zone
**[{PRIORITY}]** {file_path}
> {summary}  ← Summaries only, no full content
```

Both show `{summary}`. The comment "Summaries only" is misleading since that's always the case.

**Impact:** Soft Warning zone behavior is identical to Normal zone except for the indicator text.

**Fix Required:** Either:
1. Implement actual full content loading for Normal zone
2. Remove the "prefer summaries" language as it's not a real distinction
3. Make Soft Warning reduce package count instead

---

### Issue 5: FR-003 Requirements Not Fully Met

**Severity:** HIGH

**Problem:** FR-003 states:
> "System MUST enforce per-agent token budgets with model-aware tokenization"

Current implementation:
- ❌ Does NOT enforce budgets (just detects zones if given current_tokens)
- ✅ Has model-aware token estimation code (but unused for enforcement)
- ❌ No tokenization of actual content occurs

**Fix Required:** To meet FR-003, need to:
1. Count tokens in context packages before including them
2. Enforce budget limits based on agent type allocation
3. Truncate/exclude packages that exceed budget

---

### Issue 6: Safety Margin Applied Inconsistently

**Severity:** LOW

**Problem:** The 15% safety margin is:
- Applied to effective_limit calculation ✅
- Not configurable from skills_config.json (hardcoded as 0.15)
- Documented as configurable via `token_safety_margin` but not read from config

**Evidence:**
```python
# Hardcoded in SKILL.md
SAFETY_MARGIN = 0.15

# But documented in config reference as:
"token_safety_margin": 0.15
```

**Fix Required:** Read safety margin from skills_config.json or remove the config option from documentation.

---

### Issue 7: No Integration Tests or Validation

**Severity:** MEDIUM

**Problem:** The spec says:
> "Independent Test: Simulate different token usage levels (60%, 75%, 85%, 95%) and verify appropriate behavior at each zone"

No tests were created. The implementation cannot be validated against these scenarios.

**Fix Required:** Create test scenarios or at least document how to manually test.

---

### Issue 8: Quickstart Scenario 3 is Misleading

**Severity:** MEDIUM

**Problem:** quickstart.md shows:
```
### Scenario 3: Token Budget Exceeded
**Given** agent is at 70% token usage (Soft Warning zone)
**When** context-assembler is invoked
The system:
1. Detects current token usage via model-aware estimation
```

This implies automatic detection, but the implementation requires `current_tokens` to be passed in. There's no "detection" - it's just a parameter.

**Fix Required:** Update quickstart to reflect actual behavior (parameter-based, not auto-detected).

---

## Comparison to Alternatives

### Alternative A: Full Token Enforcement
- Count tokens in all packages
- Enforce strict budget limits
- **Pros:** Meets FR-003 fully
- **Cons:** Requires significant implementation effort, may be slow

### Alternative B: Heuristic Proxy (Implemented with fixes)
- Use message count or character count as proxy for tokens
- Detect zones based on proxy
- **Pros:** Works without Claude Code API changes
- **Cons:** Less accurate, still doesn't enforce budgets

### Alternative C: Documentation-Only (Current State)
- Document the architecture for future implementation
- Mark as "Phase 4.5" feature
- **Pros:** Honest about limitations
- **Cons:** Doesn't deliver functional value

---

## Recommendations

### Must Fix (Before merge)

1. **Update SKILL.md Step 1** to include `senior_software_engineer` in agent_type list
2. **Remove or clarify misleading language** about "prefer summaries" (it's always summaries)
3. **Add prominent warning** that token zone detection requires `current_tokens` parameter which is not automatically available

### Should Fix (Technical debt)

4. **Read safety margin from config** instead of hardcoding
5. **Clarify budget allocation tables** as "recommended" not "enforced"
6. **Update quickstart.md** to reflect parameter-based (not auto-detected) behavior

### Consider for Future

7. **Implement actual token counting** of context packages using tiktoken
8. **Add heuristic fallback** (character count / 4) for zone detection when current_tokens not provided
9. **Create integration tests** for zone behavior validation

---

## Decision Rationale

The implementation provides the **architectural foundation** for graduated token management but is **not functionally complete**. The zone detection logic is correct but unusable in practice because:

1. Claude Code doesn't expose token usage
2. No automatic detection mechanism exists
3. Default of 0 means always Normal zone

This should either be:
- **Marked as "architecture only"** with honest documentation
- **Extended with heuristic detection** to provide some value
- **Deferred** until Claude Code exposes token metrics

---

## Lessons Learned

1. **Verify API capabilities before designing** - Assumed token usage would be available
2. **Test the happy path manually** - Would have caught zone always being Normal
3. **Implementation vs documentation gap** - Tables implying enforcement without code
4. **Consistency checks after additions** - SSE missed in Step 1 after adding everywhere else

---

## References

- `specs/1-context-engineering/spec.md` - FR-003, FR-004 requirements
- `specs/1-context-engineering/plan.md` - Token budget allocation tables
- `.claude/skills/context-assembler/SKILL.md` - Implementation
- `research/skill-implementation-guide.md` - Skill patterns

---

## Multi-LLM Review Integration

**Reviewed by:** OpenAI GPT-5 (2025-12-12)

### Critical Issues Identified by OpenAI (Must Address)

| Issue | Severity | OpenAI Finding | Action Required |
|-------|----------|----------------|-----------------|
| Token budgeting CAN work without current_tokens | HIGH | Can enforce by estimating outgoing block size (summary tokens) and packing until budget met | Implement bottom-up packing |
| Conservative zone starvation | HIGH | If no "critical" packages exist, returns nothing. Need fallback ladder: critical→high→medium | Add priority fallback |
| Soft Warning needs concrete degradation | MEDIUM | Currently identical to Normal. Propose: reduce count by 25% AND truncate summaries to 200 chars | Implement micro-summaries |
| Safety margin hardcoded | MEDIUM | skills_config.json already read elsewhere; integrate token_safety_margin now | Read from config |
| Recency formula problematic | LOW | `1/(days+1)` collapses older items too aggressively | Use exponential decay |

### Missing Considerations (From OpenAI)

1. **Consumption tracking not implemented** - Skill doesn't mark consumed packages via consumption_scope table, causing repeated token waste
2. **Package size awareness missing** - No estimation of token size per package for smart packing
3. **DB retry/backoff missing** - No handling of SQLITE_BUSY/locked errors
4. **Summary redaction missing** - Error patterns are redacted but summaries could contain secrets too
5. **Performance risk** - Multiple Python processes + DB calls may breach 500ms goal under load
6. **Orchestrator integration undefined** - No contract for how orchestrator passes/receives token info

### Incorporated Feedback (PENDING USER APPROVAL)

| # | OpenAI Suggestion | Incorporation Decision | Rationale |
|---|-------------------|------------------------|-----------|
| 1 | Implement real enforcement via bottom-up packing | **ACCEPT** | Enables functional token budgeting without waiting for Claude Code API |
| 2 | Fix zone behavior with micro-summaries | **ACCEPT** | Provides actual degradation: 400→200→100→60 char summaries |
| 3 | Read safety margin from config | **ACCEPT** | Simple fix, already reading config elsewhere |
| 4 | Add priority fallback ladder | **ACCEPT** | Prevents silent starvation in Conservative zone |
| 5 | Mark consumed packages | **ACCEPT** | Prevents token waste from repeated delivery |
| 6 | Add DB retry/backoff | **ACCEPT** | Required for reliability under concurrent load |
| 7 | Two-stage return (metadata + expansion) | **DEFER** | Adds complexity; reassess after basic enforcement works |
| 8 | Session-level caching | **DEFER** | Performance optimization; implement if 500ms breached |
| 9 | Summary redaction | **ACCEPT** | Security consistency with error pattern handling |
| 10 | Exponential decay for recency | **ACCEPT** | Better distribution than current formula |

### Rejected Suggestions (With Reasoning)

| Suggestion | Rejection Reason |
|------------|------------------|
| Accept prompt_estimate_tokens from orchestrator | Requires orchestrator changes; focus on skill-local enforcement first |
| Cache ranked list for 30-60s | Premature optimization; test performance first |
| Return est_tokens per item | Nice-to-have but not blocking; add in Phase 4.5 |

### Updated Severity Assessment

**Original analysis identified 8 issues. OpenAI review adds 6 more critical findings:**

| Category | Original Count | After Review | New Issues |
|----------|----------------|--------------|------------|
| Must Fix | 3 | 6 | +Conservative starvation, +Bottom-up packing, +DB retry |
| Should Fix | 3 | 6 | +Consumption tracking, +Summary redaction, +Recency decay |
| Consider Later | 2 | 4 | +Two-stage return, +Performance caching |

---

## Revised Recommendations

### Phase 4.1: Critical Fixes (Must complete before merge)

1. **Add priority fallback ladder** - Conservative zone should try critical→high→medium
2. **Read safety_margin from config** - Replace hardcoded 0.15
3. **Update Step 1 agent_type list** - Add senior_software_engineer
4. **Add DB retry/backoff** - 3 retries with 100/250/500ms exponential backoff

### Phase 4.2: Functional Token Enforcement (Should complete)

5. **Implement bottom-up packing** - Estimate tokens per summary, pack until budget
6. **Implement micro-summaries per zone** - Normal: 400, Soft: 200, Conservative: 100, Wrap-up: 60
7. **Mark consumed packages** - Call bazinga-db after delivery
8. **Apply summary redaction** - Same patterns as error_patterns

### Phase 4.3: Polish (Can defer)

9. **Improve recency formula** - Exponential decay instead of 1/(days+1)
10. **Add est_tokens to output** - For orchestrator visibility
11. **Performance testing** - Validate <500ms under load
12. **Integration tests** - Zone transitions, fallback scenarios
