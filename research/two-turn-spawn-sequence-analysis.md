# Two-Turn Spawn Sequence: Will It Actually Work?

**Date:** 2025-12-11
**Context:** Analyzing whether the 2-turn spawn sequence solves the specialization loading problem
**Decision:** 2-turn is necessary but NOT sufficient - needs DB-gated enforcement
**Status:** Reviewed - Awaiting User Approval
**Reviewed by:** OpenAI GPT-5

---

## Problem Statement

We implemented a "two-turn spawn sequence" to fix specialization loading:
- **Turn 1:** Output `[SPEC_CTX_START]` block, call `Skill(command: "specialization-loader")`, end message
- **Turn 2:** Extract block from skill response, call `Task()` with block prepended

**The core question:** Will this actually solve the problem?

---

## Understanding the Tool Execution Model

### How Tool Calls Work

When Claude makes tool calls:
1. Claude composes message with tool call(s)
2. Message is sent, tools execute
3. Results return to Claude
4. Claude sees results in **next turn**

**Critical insight:** Tool calls in the SAME message cannot depend on each other's outputs.

```
Turn N: Claude calls Tool_A and Tool_B
        Both tool prompts are composed BEFORE either executes
        Tool_B cannot use Tool_A's output

Turn N+1: Claude sees Tool_A result and Tool_B result
          Can now use results to inform next action
```

### Does This Make 2-Turn Necessary?

**YES** - If Task() needs data from Skill()'s output, they MUST be in separate turns.

**The "fused action" pattern (same message) was architecturally broken:**
```
# Broken - Task() prompt composed BEFORE Skill() returns
Turn 1: [SPEC_CTX block] + Skill() + Task()
        ↓ Task prompt doesn't include specialization because Skill hasn't returned yet
```

**The 2-turn pattern is architecturally correct:**
```
Turn 1: [SPEC_CTX block] + Skill()
Turn 2: Read Skill output → Extract block → Task(prompt with block)
        ↓ Task prompt includes specialization because Skill already returned
```

---

## Critical Analysis: Does 2-Turn Solve the Root Cause?

### What Was the Original Problem?

The orchestrator was:
1. ✅ Reading the phase template
2. ✅ Seeing the MANDATORY specialization steps
3. ❌ **Skipping Skill() call entirely** (efficiency optimization)
4. ❌ Spawning Task() with generic prompt

**Root cause:** Claude's efficiency heuristic decided Skill() was "optional" and skipped it.

### Does 2-Turn Prevent Skipping?

**NO.** The 2-turn sequence changes the structure but doesn't prevent skipping:

| Failure Mode | Can Still Happen with 2-Turn? |
|--------------|------------------------------|
| Skip Skill() entirely | ✅ Yes - Claude can still skip Turn 1's Skill() |
| Output SPEC_CTX but don't call Skill() | ✅ Yes - Text output ≠ tool call |
| Skip block extraction in Turn 2 | ✅ Yes - Claude can call Task() without extracting |
| Call Task() directly without Turn 1 | ✅ Yes - Nothing enforces Turn 1 must happen |

**The 2-turn sequence doesn't FORCE anything - it just provides clearer instructions.**

### What 2-Turn Does Provide

1. **Clearer checkpoint** - Turn 1 has ONE job: call Skill()
2. **Per-turn self-checks** - Verification questions for each turn
3. **Structural separation** - Can't accidentally put both in same message
4. **More obvious skipping** - If Turn 1 has no Skill(), it's clearly wrong

---

## Potential Failure Modes

### Failure Mode 1: Skill Returns Instructions, Not Block

**Assumption in template:** Skill() returns a composed block between `[SPECIALIZATION_BLOCK_START]` and `[SPECIALIZATION_BLOCK_END]`

**Reality check:** Does specialization-loader actually return a composed block, or does it return INSTRUCTIONS for composing a block?

If skill returns instructions:
```
Turn 1: Skill() → returns "Read file X, Read file Y, compose block"
Turn 2: Orchestrator must FOLLOW instructions, then call Task()
```

But template says "extract content between markers" - implying block already exists.

**If skill returns instructions instead of block, Turn 2 logic is wrong.**

### Failure Mode 2: Orchestrator Skips Turn 1 Entirely

Claude's efficiency optimization could trigger:
```
Orchestrator thinking: "I need to spawn a developer. Let me just call Task()."
                       "Those specialization steps are nice-to-have."
```

Result: Goes directly to Task() without any Turn 1.

**The 2-turn structure doesn't prevent this.**

### Failure Mode 3: Turn 2 Doesn't Extract Block

Even if Turn 1 works correctly:
```
Turn 2: Orchestrator sees skill output
        Thinks "specialization step done"
        Calls Task() with base_prompt only (no extraction)
```

**Extraction step is still skippable.**

### Failure Mode 4: Parallel Mode Complexity

For 4 parallel groups:
```
Turn 1: Skill() for A, Skill() for B, Skill() for C, Skill() for D
Turn 2: Extract A's block, Extract B's block, Extract C's block, Extract D's block
        Task() for A with A's block
        Task() for B with B's block
        Task() for C with C's block
        Task() for D with D's block
```

**Potential issues:**
- How does orchestrator match skill outputs to groups?
- If outputs aren't clearly labeled, blocks could be mismatched
- 8 extraction + composition operations in Turn 2

---

## Comparison: Original Problem vs 2-Turn Solution

| Aspect | Original (Fused) | 2-Turn Sequence |
|--------|-----------------|-----------------|
| Architectural correctness | ❌ Broken (Task can't use Skill output) | ✅ Correct (Turn 2 has Skill output) |
| Prevents skipping Skill() | ❌ No | ❌ No |
| Provides skip detection | ❌ No (mixed in same message) | ✅ Yes (Turn 1 self-check) |
| Complexity | Low | Medium |
| Latency | 1 turn | 2 turns |

**Key insight:** 2-turn is necessary but not sufficient.

---

## What Would Actually Solve the Problem?

### Tier 1: Detection (Current Approach)
- Self-checks per turn
- Visible output showing specialization status
- User can see if skipped and intervene

**Confidence:** Medium - Relies on user vigilance

### Tier 2: Prompt Engineering (Harder)
- Make the ONLY path to Task() go through Skill() first
- Remove ALL examples of Task() without Skill()
- No "IF disabled, skip Skill()" escape hatches

**Confidence:** Medium-Low - Claude can still optimize

### Tier 3: Post-Hoc Validation + Retry
- After Task() is called, check if specialization was included
- If not, reject and force retry with proper sequence

**Confidence:** Medium-High - Catches failures after the fact

### Tier 4: Tool-Level Enforcement (Infrastructure Change)
- Modify Task() to require specialization_block parameter
- Parameter must come from valid Skill() call
- System-level enforcement, not prompt-level

**Confidence:** High - Cannot be bypassed

---

## Risk Assessment

### If 2-Turn Works
- ✅ Specializations load correctly
- ✅ Agents get technology-specific guidance
- ✅ Output quality improves

### If 2-Turn Fails (Same Skipping Behavior)
- ❌ We've added latency (2 turns instead of 1)
- ❌ More complex instructions to follow
- ❌ False sense of security ("we fixed it")
- ❌ Problem persists with more convoluted code

### Likelihood Assessment
Based on the failure modes:
- **High probability (60%):** Some improvement - self-checks catch obvious skips
- **Medium probability (30%):** Same problem - Claude still skips when it "optimizes"
- **Low probability (10%):** Worse - More complexity leads to more confusion

---

## Questions for External Review

1. **Skill tool behavior:** When Skill() is called, does the skill return a composed block, or does it return instructions that Claude must follow?

2. **Tool dependency in same turn:** Is it architecturally possible for Tool_B to use Tool_A's output when both are called in the same message?

3. **Efficiency optimization:** What triggers Claude to skip "optional" steps, and does 2-turn structure change that?

4. **Alternative approaches:** What would truly FORCE the Skill() call rather than just instructing it?

5. **Parallel mode viability:** Can Claude reliably track 4 skill outputs and match them to the correct Task() calls?

---

## Provisional Verdict

**The 2-turn sequence is:**
- ✅ Architecturally necessary (fixes tool dependency issue)
- ✅ An improvement (clearer checkpoints, per-turn self-checks)
- ⚠️ Not a complete solution (doesn't prevent skipping)
- ⚠️ Adds complexity and latency

**Confidence level:** Medium

**Recommendation:** Keep 2-turn as foundation, but add detection/retry mechanism as backup.

---

---

## Multi-LLM Review Integration

### OpenAI GPT-5 Review Summary

**Overall Assessment:** "The two-turn spawn sequence is architecturally necessary but not sufficient to guarantee specialization loading. As written, it still allows skipping or misapplication and is brittle in parallel scenarios."

**Confidence:** Medium-low (as-is) → Medium-high (with improvements)

### Critical Issues Identified

1. **My "Failure Mode 1" was wrong:** The skill DOES return a composed block (not instructions). The SKILL.md contract specifies it returns between `[SPECIALIZATION_BLOCK_START]` and `[SPECIALIZATION_BLOCK_END]` markers. My speculation was unnecessary.

2. **Parallel mode has CONTEXT BLEED risk:** Multiple `[SPEC_CTX_START]` blocks in one message is dangerous. The skill reads "the context above" - with multiple contexts, it's ambiguous which one each skill invocation reads. **HIGH RISK of misapplied specializations.**

3. **No hard validation:** Nothing enforces that Task() actually includes the specialization block. The extraction step can still be skipped.

4. **Fragile marker parsing:** Relying on parsing `[SPECIALIZATION_BLOCK_START]` from tool output is error-prone. Minor formatting deviations break extraction.

5. **Token budget not validated:** Final prompt (base + specialization + context packages + reasoning) can exceed model limits.

### Recommended Improvements (From Review)

#### High Priority (Should Implement)

| # | Improvement | Rationale |
|---|-------------|-----------|
| 1 | **DB-gated enforcement** | After Skill(), fetch block from DB via `bazinga-db get-skill-output` instead of parsing tool output. Deterministic, not brittle. |
| 2 | **Single-context-per-call in parallel** | Don't put multiple SPEC_CTX blocks in one message. One block + one Skill() per message. Avoids context bleed. |
| 3 | **Embed group_id in skill output** | Update skill to include "Group: {group_id}" in returned block. Ensures deterministic matching. |
| 4 | **Post-composition validator** | Before Task(), verify specialization signature present and tokens within budget. Reject and retry if not. |

#### Medium Priority (Should Consider)

| # | Improvement | Rationale |
|---|-------------|-----------|
| 5 | **Caching/reuse** | Cache blocks per (session, group, agent). Reuse on retries. Reduces latency. |
| 6 | **Fallback strategy** | If skill fails: retry once → proceed without specialization with warning + audit flag |
| 7 | **Telemetry** | Log hash of specialization block with Task spawn for audit trail |
| 8 | **Token budget gate** | Cap context packages/reasoning aggressively when specialization is present |

### What This Means for Current Implementation

**Current 2-turn sequence:**
- ✅ Architecturally correct (tool dependency)
- ❌ Still allows skipping (no enforcement)
- ❌ Parallel mode is brittle (context bleed)
- ❌ No validation that block was actually applied

**With recommended improvements:**
- ✅ DB is source of truth (not brittle parsing)
- ✅ Single-context-per-call eliminates ambiguity
- ✅ Post-validation catches failures
- ✅ Audit trail for debugging

### Rejected Suggestions (With Reasoning)

| Suggestion | Reason for Rejection |
|------------|---------------------|
| Parameterized skill input (JSON args) | Requires skill infrastructure changes; current approach works if DB-gated |

---

## Revised Verdict

**The 2-turn spawn sequence as currently implemented:**
- ✅ Solves the tool dependency issue (necessary)
- ❌ Does NOT prevent skipping (not sufficient)
- ❌ Is brittle in parallel mode (context bleed risk)
- ⚠️ Confidence: **Medium-Low**

**With DB-gated enforcement + single-context-per-call + post-validation:**
- ✅ Solves tool dependency
- ✅ Enforces specialization loading via DB check
- ✅ No context ambiguity in parallel
- ✅ Catches failures before spawn
- ⚠️ Confidence: **Medium-High**

---

## Proposed Next Steps

**If user approves, implement in this order:**

1. **DB-gated enforcement (Turn 2 change)**
   - After Skill(), query `bazinga-db get-skill-output` for (session, group, agent)
   - Use DB record instead of parsing tool output
   - Retry skill once if not found

2. **Single-context-per-call (Parallel mode change)**
   - Remove multiple SPEC_CTX blocks in same message
   - Sequential: Group A (Skill) → Group A (Task) → Group B (Skill) → Group B (Task)
   - Or: Interleaved: A Skill, B Skill → (wait) → A Task, B Task (but separate SPEC_CTX messages)

3. **Post-composition validator (Pre-Task check)**
   - Before Task(), verify prompt contains `## SPECIALIZATION GUIDANCE`
   - Verify total tokens under model hard limit
   - Reject and retry if validation fails

4. **Update skill to embed group_id**
   - Add "Group: {group_id}" to returned block header
   - Ensures parallel matching works correctly

---

## References

- `research/specialization-loading-failure-analysis.md` - Original problem analysis
- `templates/orchestrator/phase_simple.md` - 2-turn implementation
- `.claude/skills/specialization-loader/SKILL.md` - Skill definition
- `tmp/ultrathink-reviews/openai-review.md` - Full OpenAI review
