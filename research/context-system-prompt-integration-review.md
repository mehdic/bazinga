# Context System Prompt Integration: Critical Review

**Date:** 2025-12-11
**Context:** Fix specializations, context packages, and reasoning to be properly included in developer prompts
**Decision:** Template-based instruction approach (no DB enforcement)
**Status:** Reviewed
**Reviewed by:** External LLM review (ultrathink process)

---

## Problem Statement

The orchestrator was failing to include critical context in developer prompts:

1. **Specializations** - Technology-specific patterns (HOW to code)
2. **Context Packages** - Research from RE, prior failures (RESEARCH)
3. **Reasoning Context** - Prior agent decisions (WHY)

All three had the same bug pattern:
- Query mechanisms existed and worked ✅
- Templates for sections existed ✅
- **Instructions on WHERE to include them were missing** ❌

## Solution Implemented

### Changes Made

**1. Explicit base_prompt Template (PART A)**

Before:
```
**Step A.2: Build base_prompt string using this template:**
You are a Developer...
**REQUIREMENTS:** {task_requirements}
```

After:
```
**Step A.2: Retrieve context packages and reasoning (queried earlier):**
context_packages = result from query
reasoning_entries = result from query

**Step A.3: Build base_prompt string using this template:**

{IF context_packages is NOT empty}
## Context Packages Available
[table with packages]
{ENDIF}

{IF reasoning_entries is NOT empty}
## Previous Agent Reasoning
[table with reasoning]
{ENDIF}

---

You are a Developer...
**REQUIREMENTS:** {task_requirements}
```

**2. FULL_PROMPT Example Updated**

Before:
```
## SPECIALIZATION GUIDANCE
[spec_block content]
---
You are a Developer...
**REQUIREMENTS:**...
```

After:
```
## SPECIALIZATION GUIDANCE
[spec_block content]
---
## Context Packages Available
[table with research]
## Previous Agent Reasoning
[table with decisions]
---
You are a Developer...
**REQUIREMENTS:**...
```

**3. Self-Checks Added**

```markdown
**🔴 SELF-CHECK (PART A):**
- ✅ Did I query context packages?
- ✅ Did I query reasoning?
- ✅ Does my base_prompt include "Context Packages Available" section?
- ✅ Does my base_prompt include "Previous Agent Reasoning" section?
- ✅ Is the task/requirements section AFTER the context sections?

**SELF-CHECK (Turn 2):**
- ✅ Does base_prompt include context packages (if any)?
- ✅ Does base_prompt include reasoning (if any)?
```

## Critical Analysis

### Pros ✅

1. **Explicit Structure** - The base_prompt template now shows exactly WHERE to put context
2. **Concrete Examples** - FULL_PROMPT example demonstrates complete prompt with all 4 parts
3. **Self-Checks** - Orchestrator has validation points before proceeding
4. **Consistent Pattern** - Same fix applied to specializations, context packages, and reasoning
5. **No DB Changes** - Pure template/instruction approach, no schema modifications
6. **Silent Extraction** - Specialization blocks no longer echoed to user (cleaner output)

### Cons ⚠️

1. **LLM Interpretation** - Relies on orchestrator correctly parsing pseudo-code templates
2. **No Runtime Validation** - No mechanism to verify context was actually included
3. **Complex Conditional Logic** - `{IF...}{ENDIF}` blocks require correct interpretation
4. **Query Result Handling** - Orchestrator must correctly store query results across steps
5. **Turn Sequence Dependency** - Context queries in Turn 1, inclusion in base_prompt, specializations in separate turn
6. **Size Growth** - Prompts now longer with context sections (token usage)

### Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Orchestrator skips context sections | Medium | High | Self-checks at each step |
| Query results not stored correctly | Low | High | Explicit variable naming |
| Wrong section order | Low | Medium | Template shows exact order |
| Empty checks fail | Low | Low | Default to empty array |
| Prompt too long | Low | Medium | Limits already in template (3 packages, 5 reasoning) |

### Verdict

**LIKELY TO WORK** with caveats:

The fix follows the same pattern that worked for specializations:
1. Show explicit template with placeholders
2. Show concrete FULL_PROMPT example
3. Add self-checks

The orchestrator successfully followed similar instructions for specializations. The context package fix uses identical patterns.

## What to Look For in Output

### Signs Implementation is Working

**Turn 1 output:**
```
🔧 Loading specializations for developer...
[SPEC_CTX_START group=main agent=developer]
...
[SPEC_CTX_END]
```

**Turn 2 output (capsule only, no spec block echoed):**
```
🔧 Specializations loaded (3 templates) | React/TypeScript Frontend Developer

📝 **Developer Prompt** | Group: main | Model: haiku
   Task: Implement delivery list page
   Specializations: ✓ loaded
   Context Packages: 1 available    ← NEW INDICATOR
   Reasoning: 2 entries             ← NEW INDICATOR

Task(subagent_type="general-purpose", ...)
```

**Developer output:**
```
Reading context package from RE: research-oauth.md
...
bazinga-db mark-context-consumed 1 developer 1   ← CONFIRMS PACKAGE WAS READ
```

### Signs Implementation is NOT Working

1. **Developer doesn't mention context packages** - Didn't see them
2. **No mark-context-consumed calls** - Package section missing
3. **Developer repeats prior failures** - Didn't see failures package
4. **Developer doesn't reference RE research** - Research package missing
5. **Orchestrator echoes [SPECIALIZATION_BLOCK_START]** - Silent extraction failed

### Debug Checklist

If issues occur:

1. **Check base_prompt content:**
   - Does it start with "## Context Packages Available"?
   - Does it include "## Previous Agent Reasoning"?
   - Is task section AFTER context sections?

2. **Check query results:**
   - Were context packages queried?
   - What did the query return?
   - Were results stored correctly?

3. **Check FULL_PROMPT:**
   - Does it have all 4 parts? (spec + context + reasoning + task)
   - Is the separator "---" between sections?

## Comparison to Alternatives

### Alternative 1: DB-Enforced Validation
- **Rejected** - User requested no DB enforcement
- Would require schema changes, migration

### Alternative 2: Skill-Based Prompt Building
- Build prompt via skill call instead of template
- **Rejected** - Would require new skill, more complexity
- Template approach is simpler and already working for specializations

### Alternative 3: Hardcoded Prompt Structure
- Generate complete prompt string in one place
- **Rejected** - Less flexible, harder to maintain
- Template approach allows conditional inclusion

## Files Changed

| File | Changes |
|------|---------|
| `templates/orchestrator/phase_simple.md` | PART A template, FULL_PROMPT example, self-checks |
| `templates/orchestrator/phase_parallel.md` | Same changes for parallel mode |

## Commits in This Fix

1. `440069d` - Explicit base_prompt building and silent specialization extraction
2. `6269e85` - FULL_PROMPT examples showing spec_block + base_prompt combination
3. `45535d3` - Turn 2 must call Task() instructions
4. `7b2898c` - Context packages and reasoning included in developer prompts
5. `7ad344a` - Merge main (conflict resolution)

## Lessons Learned

1. **Pseudo-code templates need concrete examples** - `{X + Y}` notation is ambiguous
2. **Query and inclusion are separate steps** - Must show WHERE to include query results
3. **Self-checks prevent drift** - Explicit validation points catch skipped steps
4. **Same bug can affect multiple systems** - Specializations, context packages, reasoning all had identical issue

## References

- `research/specialization-loading-implementation-review.md` - Prior ultrathink on specializations
- `research/context-package-final-review.md` - Context package system design
- `templates/orchestrator/phase_simple.md` - Simple mode template
- `templates/orchestrator/phase_parallel.md` - Parallel mode template

---

## Testing Recommendations

To verify the fix works:

1. **Run orchestration with RE task first** - Creates context package
2. **Run developer task in same session** - Should see context package
3. **Check developer output** - Should reference RE research
4. **Check for mark-context-consumed call** - Confirms package was in prompt

Expected output pattern:
```
RE: Analyzed OAuth requirements, saved context package
Orchestrator: Spawning developer with context package
Developer: Reading context package research-oauth.md...
Developer: bazinga-db mark-context-consumed 1 developer 1
Developer: Implementing OAuth using PKCE flow as recommended...
```

---

## Multi-LLM Review Integration

### OpenAI GPT-5 Critical Issues

| Issue | Assessment | Action |
|-------|------------|--------|
| No runtime verification | Valid - template-based only | ACCEPT - per user constraint (no DB enforcement) |
| Volatile cross-turn state | Valid for parallel mode | NOTED - monitor in testing |
| Only Developer fixed, not QA/TL | Valid gap | DEFER - can be addressed in follow-up |
| Count indicators ambiguous | Minor - cosmetic | SKIP - not critical |
| mark-context-consumed advisory | Valid | ACCEPT - no enforcement per user request |

### Suggestions Evaluated

| Suggestion | Decision | Reasoning |
|------------|----------|-----------|
| Prompt Auditor skill | REJECT | Adds complexity; template approach should work first |
| Persist per-group state in DB | REJECT | User requested no DB enforcement |
| Dynamic token budget | DEFER | Low risk with existing limits (3 packages, 5 reasoning) |
| Mirror fix for QA/TL | DEFER | Follow-up task if Developer works |
| Record inclusion metadata in DB | REJECT | User requested no DB enforcement |
| Enforce mark-context-consumed | REJECT | User requested no enforcement |
| Spec-kit parity | DEFER | Can be done in follow-up |
| Unit playbook test | ACCEPT | Good idea for future |

### Key Takeaways from Review

**What OpenAI confirmed:**
- Direction is solid
- Explicit templates + concrete examples is correct approach
- Self-checks are helpful but not sufficient alone

**What we're accepting as risk:**
- No runtime validation (template-based instruction only)
- Cross-turn state volatility (LLM must track variables)
- QA/TL prompts not updated (Developer-focused fix)

**Confidence assessment:**
- OpenAI: Medium confidence
- My assessment: **Should work for Developer prompts** based on specialization precedent

### Rejected Due to User Constraints

The following suggestions were rejected because user requested no DB enforcement:
- DB-side prompt trace
- Persist per-group assembly state in DB
- Record inclusion metadata
- Enforce mark-context-consumed at next gate

These would require schema changes or validation logic that goes against the "no DB enforcement" directive.

### Follow-up Tasks (Not in This PR)

1. Apply same pattern to QA Expert prompts
2. Apply same pattern to Tech Lead prompts
3. Spec-kit orchestrator parity
4. Create integration test playbook
