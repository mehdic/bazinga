# Self-Review: Context Accumulation Fix Implementation

**Date:** 2025-12-23
**Context:** Critical review of my own implementation
**Decision:** Multiple issues identified requiring fixes
**Status:** Self-Review (Brutally Honest)

---

## Executive Summary

**My implementation has serious flaws.** Several "optimizations" will actually make context usage WORSE, not better. The core problem: I didn't fully understand how skill invocations work in the context window.

---

## Critical Issues Identified

### 🔴 Issue 1: Skill Invocations ADD Context, Not Reduce It

**What I assumed:** Calling `Skill(command: "workflow-router")` offloads logic from context.

**Reality:** Each skill invocation:
1. Expands the SKILL.md file (~100-120 lines) into context
2. The skill executes and returns output
3. Both the expansion AND output stay in context

**Impact on my implementation:**
```
Step 2B.2 calls workflow-router 4 times (once per developer):
  4 × ~500 tokens (SKILL.md expansion) = 2,000+ tokens

vs. Original inline routing:
  4 × ~75 tokens (status extraction + route) = 300 tokens

NET EFFECT: 6-7x WORSE, not better!
```

**Verdict:** 🔴 CRITICAL BUG - Implementation makes problem worse

---

### 🔴 Issue 2: Phase Tracker Counter Is Still Ephemeral

**What I wrote (Step 2B.7b, Step 3):**
```
# Increment counter from state
phase_completed[current_phase] += 1
```

**The problem:** This is a local variable increment, not a DB operation. The counter exists only in the current message. On resume/retry, it resets.

**This is EXACTLY what the LLM review warned against:**
> "Local counters not persisted: Will drift on resume/retry"

**Verdict:** 🔴 CRITICAL BUG - Didn't actually fix the persistence issue

---

### 🔴 Issue 3: Template Caching Creates Chicken-and-Egg Problem

**What I wrote:**
```
BEFORE any Read(file_path: "bazinga/templates/X.md"):
1. Check orchestrator state for templates_loaded array
2. IF template name in templates_loaded → SKIP Read
```

**The problem:** To check orchestrator state, I need to call:
```
Skill(command: "bazinga-db")
bazinga-db, please get state...
```

This skill invocation adds ~300+ tokens. If I do this before every Read, I'm adding MORE context than just reading the template.

**Math:**
- Read a 5k token template: 5,000 tokens (once)
- Check state + maybe skip: ~300 tokens per check
- If I check 10 times: 3,000 tokens (just for checking!)
- And I still need to read the template the first time

**Verdict:** 🔴 FLAWED DESIGN - Net negative on context savings

---

### 🟡 Issue 4: Context Threshold Protocol Is Unenforceable

**What I wrote:**
```
estimated_usage = (total_spawns * 600) + 25000
usage_percent = estimated_usage / 200000
```

**The problem:**
1. The orchestrator has no way to know actual context usage
2. The formula is a rough guess based on assumptions
3. `total_spawns` might not be tracked accurately
4. Context accumulates from many sources beyond spawns

**The protocol says "at 70%, switch to compact mode" but there's no reliable way to detect 70%.**

**Verdict:** 🟡 WEAK - Directionally correct but unenforceable

---

### 🟡 Issue 5: Aggregated Capsule Conflicts with Threshold Protocol

**Step 2B.2 always outputs:**
```
🔨 **{N} Developers Complete**

| Group | Status | Files | Tests | Summary |
|-------|--------|-------|-------|---------|
...
```

**But the threshold protocol says at 70%:**
```
✅ 4 devs → 3 QA + 1 retry | Phase 2: 6/8
```

**These are contradictory.** Step 2B.2 doesn't check threshold before outputting full table.

**Verdict:** 🟡 INCONSISTENT - Need conditional output format

---

### 🟡 Issue 6: Phase Tracker Initialization Location Is Wrong

**Where I put it:** `phase_parallel.md` (Step right after token tracking)

**Where it should be:** Main orchestrator.md flow, specifically after PM returns PLANNING_COMPLETE (before entering parallel mode)

**Why it matters:** The parallel template is only entered AFTER mode routing. The initialization needs to happen during mode routing, not inside the parallel template.

**Verdict:** 🟡 WRONG LOCATION - Won't execute at right time

---

### 🟡 Issue 7: bazinga-db Natural Language Format Not Verified

**What I wrote:**
```
Skill(command: "bazinga-db")

bazinga-db, please update task group:
Group ID: {group_id}
Session ID: {session_id}
Status: completed
```

**Uncertainty:** Does bazinga-db parse this format correctly? Looking at SKILL.md, it expects:
- Natural language like "update task group" ✅
- But the parameter format I used may not match what the skill expects

**Need to verify:** Does the skill correctly parse my parameter format?

**Verdict:** 🟡 UNVERIFIED - May or may not work

---

### 🟢 Issue 8: Aggregated Routing Logic Is Sound (Concept)

**The concept is correct:**
- Parse all responses first
- Build spawn queue
- Output single capsule
- Spawn all at once

**But the implementation via multiple skill calls defeats the purpose.**

**Verdict:** 🟢 CONCEPT OK, IMPLEMENTATION WRONG

---

## Root Cause Analysis

**Why did I make these mistakes?**

1. **Didn't understand skill invocation overhead:** I assumed skills were "free" calls that don't consume context. They're not - the SKILL.md expands into context.

2. **Mixed ephemeral and persistent state:** I wrote pseudocode that looked like DB operations but was actually local variable manipulation.

3. **Didn't trace the full execution path:** Template caching sounds good in theory but doesn't work when checking requires DB calls.

4. **Cargo-culted patterns:** I used `Skill(command: "...")` without understanding when it's beneficial vs. harmful.

---

## What Actually Saves Context?

Based on this analysis, here's what genuinely works:

### ✅ Actually Effective:
1. **Aggregated capsule output** - ONE summary instead of N separate ones
2. **Deferred full DB queries** - Query once per phase, not per group
3. **Minimal status capsules** - `✅ {group} merged | Phase 1: 3/4` instead of full details

### ❌ Not Effective (Or Makes It Worse):
1. **Multiple skill invocations** - Each adds SKILL.md to context
2. **State checking before reads** - Checking costs more than reading
3. **Complex routing via skills** - Inline logic is cheaper

### 🔄 Needs Redesign:
1. **workflow-router integration** - Call ONCE per batch, not per response
2. **Phase tracker persistence** - Use DB properly, not local variables
3. **Template caching** - Remove or implement differently

---

## Recommended Fixes

### Fix 1: Remove Multiple workflow-router Calls

**Before (my implementation):**
```
For each response:
  Skill(command: "workflow-router")  // 4 calls = 2000+ tokens
```

**After (correct approach):**
```
# Parse all responses inline (cheap)
# Build spawn queue inline (cheap)
# Optionally call workflow-router ONCE for complex decisions
```

### Fix 2: Fix Phase Tracker to Actually Use DB

**Before (broken):**
```
phase_completed[current_phase] += 1  // local variable!
```

**After (correct):**
```
# Get current state from DB (already fetched in Step 2)
current_completed = state["phase_tracker"]["phase_completed"][current_phase]
new_completed = current_completed + 1

# Save updated state to DB
Skill(command: "bazinga-db")
bazinga-db, please save state:
Session ID: {session_id}
State Type: orchestrator
State Data: {"phase_tracker": {"phase_completed": {current_phase: new_completed}}}
```

### Fix 3: Remove Template Caching Protocol

**The protocol is counterproductive. Remove it entirely.**

Templates are read once per orchestration session anyway. The "caching" overhead exceeds any benefit.

### Fix 4: Simplify Context Threshold Protocol

**Before:** Complex threshold checks that can't be measured

**After:** Simple heuristic:
```
After Phase N completes (all groups merged):
  IF total_groups_completed >= 8:
    Switch to ultra-compact mode for remaining phases
```

This is enforceable without context measurement.

### Fix 5: Move Phase Tracker Initialization

Move from `phase_parallel.md` to `orchestrator.md` in the mode routing section (after PM returns PLANNING_COMPLETE, before entering parallel execution).

---

## Severity Assessment

| Issue | Severity | Fix Effort | Priority |
|-------|----------|------------|----------|
| Multiple skill invocations | 🔴 CRITICAL | Medium | P0 |
| Ephemeral phase counter | 🔴 CRITICAL | Low | P0 |
| Template caching overhead | 🔴 CRITICAL | Low (remove) | P0 |
| Unenforceable thresholds | 🟡 MEDIUM | Low | P1 |
| Capsule format conflict | 🟡 MEDIUM | Low | P1 |
| Wrong initialization location | 🟡 MEDIUM | Low | P1 |
| Unverified DB format | 🟡 MEDIUM | Low | P2 |

---

## Conclusion

**My implementation is fundamentally flawed.** The core insight - reduce context accumulation - is correct, but the execution is wrong.

**Key lesson learned:** Skill invocations are NOT free. They expand SKILL.md content into context. Use skills sparingly, not as a replacement for inline logic.

**Recommended action:** Revert/rewrite the changes with proper understanding of context costs.

---

## References

- `bazinga/templates/orchestrator/phase_parallel.md` - My flawed changes
- `agents/orchestrator.md` - My flawed changes
- `.claude/skills/workflow-router/SKILL.md` - Shows ~120 lines that expand into context
- `.claude/skills/bazinga-db/SKILL.md` - Shows ~800+ lines that expand into context
