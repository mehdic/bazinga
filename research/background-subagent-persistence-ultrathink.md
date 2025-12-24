# Background Subagent Foreground Execution: Persistence After Context Compaction

**Date:** 2024-12-24
**Context:** BAZINGA orchestrator spawns subagents in background mode after context compaction despite explicit `run_in_background: false` documentation
**Decision:** TBD after analysis
**Status:** Proposed
**Reviewed by:** Pending OpenAI GPT-5, Google Gemini 3 Pro Preview

---

## Problem Statement

The BAZINGA orchestrator has documented rules requiring all Task() calls to include `run_in_background: false`. These rules work correctly for approximately 15-20 turns, but after automatic context compaction occurs, the orchestrator reverts to spawning agents in background mode.

**Evidence from session logs:**
```
⏺ 3 developer agents launched (ctrl+o to expand)
   ├─ Developer fixing PAT-VIP E2E tests · Running in background
   │  ⎿  Launched
   ├─ Developer fixing NUR-E2E port config · Running in background
   │  ⎿  Launched
   └─ Developer fixing E2E-RX playwright config · Running in background
      ⎿  Launched
```

**Root cause:** Context compaction does not preserve project-context.md or orchestrator instructions as system-level context. The model reverts to base behaviors (inferring "parallel" means "background").

---

## Known Issues (from GitHub)

### Issue #14118: Background Subagent Tool Calls Exposed
- **Status:** Open (December 16, 2025)
- **Problem:** Background subagents expose tool calls to parent context via `getOutput`
- **Impact:** Context isolation breaks, causing token bloat and confusion

### Issue #9796: Context Compaction Erases Instructions
- **Status:** Open (November 2025)
- **Problem:** Compaction summary doesn't preserve project-context.md
- **Impact:** All custom instructions lost after ~15-20 tool-using turns
- **Quote:** "The compaction summary does not preserve or reference project-context.md content"

---

## Current Implementation (What We Have)

1. **§FOREGROUND EXECUTION ONLY** section in orchestrator.md (lines 172-188)
2. **Principle #7** in claude.md Key Principles
3. **All Task() examples** include `run_in_background: false`
4. **SELF-CHECK** instruction before Task() calls

**Why it fails after compaction:**
- These are in `.claude/claude.md` and `agents/orchestrator.md`
- Compaction treats them as "conversation content" not "system context"
- The compacted summary loses the specific parameter requirement
- Model falls back to training-based inference ("parallel" → "concurrent" → "background")

---

## Solution Candidates

### Solution A: Pre-Compact Hook Re-injection

**Mechanism:** Use Claude Code hooks to re-inject critical rules before/after compaction.

```json
{
  "hooks": {
    "preCompact": {
      "command": "cat .claude/critical-rules.md",
      "output": "inject"
    }
  }
}
```

**Pros:**
- Automatic, no manual intervention
- Works with existing hook infrastructure
- Can inject any content needed

**Cons:**
- Requires user to configure hooks
- May not work if compaction happens server-side
- Hooks may not be available in all environments

### Solution B: Redundant Anchoring in Multiple Locations

**Mechanism:** Place the foreground rule in multiple files that may survive compaction differently:
1. `.claude/claude.md` (project context)
2. `agents/orchestrator.md` (agent prompt)
3. `.claude/settings.json` (if custom rules supported)
4. Inline in every Task() example block

**Pros:**
- Defense in depth
- At least one copy may survive
- No external dependencies

**Cons:**
- Maintenance burden (sync multiple copies)
- May still lose all copies in severe compaction
- Doesn't guarantee preservation

### Solution C: Behavioral Identity Anchoring

**Mechanism:** Make the rule part of the orchestrator's "identity" statement at the very top, using first-person language that's more likely to be preserved.

**Current:**
```markdown
## 🔴 CRITICAL: FOREGROUND EXECUTION ONLY
**All Task() calls MUST include `run_in_background: false`.**
```

**Proposed:**
```markdown
# ORCHESTRATOR IDENTITY

I am the BAZINGA Orchestrator. My Task() calls ALWAYS use `run_in_background: false`.
This is WHO I AM, not what I should do. Background execution is impossible for me.

## Identity Axioms (NEVER COMPRESSIBLE)
1. I spawn agents in FOREGROUND ONLY
2. I include `run_in_background: false` in EVERY Task() call
3. "Parallel" means multiple CONCURRENT FOREGROUND calls, NOT background mode
```

**Pros:**
- Identity statements tend to be preserved better than rules
- First-person framing is more sticky
- "This is who I am" vs "this is what I should do"

**Cons:**
- May feel awkward stylistically
- Still no guarantee after severe compaction
- Empirical—needs testing

### Solution D: Post-Compaction Detection and Re-read

**Mechanism:** Detect when compaction has occurred and force re-read of critical files.

```markdown
## Post-Compaction Recovery

If you notice:
- Your previous message count is low but time elapsed is long
- You don't remember specific parameter requirements
- The word "COMPACTION" appears in system messages

IMMEDIATELY re-read:
1. .claude/claude.md (§FOREGROUND EXECUTION ONLY)
2. agents/orchestrator.md (§FOREGROUND EXECUTION ONLY)

Then verify: Every Task() call MUST have `run_in_background: false`
```

**Pros:**
- Self-healing behavior
- Works regardless of what was compacted
- Explicit recovery mechanism

**Cons:**
- Detection is heuristic/unreliable
- Adds overhead to every post-compaction turn
- May not trigger if compaction is seamless

### Solution E: Structural Parameter Enforcement

**Mechanism:** Change from documentation to structural enforcement—make it impossible to call Task() without the parameter.

**Option E1: Template-only Task() calls**
```markdown
NEVER write raw Task() calls. ALWAYS use this template:

TASK_FOREGROUND(agent_type, model, description, prompt)
  → expands to: Task(subagent_type: "general-purpose", model: {model},
                     description: {description}, prompt: {prompt},
                     run_in_background: false)
```

**Option E2: Validation before spawn**
```markdown
Before ANY Task() call:
1. Write the full Task() call to a temp variable
2. Assert: contains "run_in_background: false"
3. If missing: ADD IT before calling
4. Then execute
```

**Pros:**
- Structural, not just instructional
- Forces correct behavior even if rules forgotten
- Self-documenting pattern

**Cons:**
- Adds complexity
- Model may still bypass if it "forgets" the template
- Not truly enforced at tool level

### Solution F: Explicit Compaction Instructions

**Mechanism:** Provide explicit `/compact` instructions that preserve critical rules.

```markdown
## When Running /compact

If you need to compact, use:
/compact preserve: §FOREGROUND EXECUTION ONLY - all Task() calls require run_in_background: false

This ensures the compaction summary retains the critical parameter requirement.
```

**Pros:**
- Direct control over what's preserved
- User can invoke strategically
- Clear guidance

**Cons:**
- Requires manual intervention
- Auto-compact doesn't use this
- May be ignored in automated workflows

---

## Critical Analysis

### Pros of Combined Approach ✅
- Multiple layers of protection
- Graceful degradation (if one fails, others may work)
- Addresses both prevention and recovery

### Cons ⚠️
- Complexity increase
- Maintenance burden across multiple files
- No guaranteed solution (fundamental Claude Code bug)
- May need to wait for Anthropic to fix #9796

### Verdict

**Recommended: Combine Solutions B + C + D**

1. **Solution B (Redundancy):** Keep the rule in multiple locations
2. **Solution C (Identity):** Reframe as identity axiom at orchestrator top
3. **Solution D (Recovery):** Add post-compaction re-read instructions

This provides:
- Pre-compaction protection (identity framing)
- During-compaction redundancy (multiple copies)
- Post-compaction recovery (explicit re-read)

---

## Implementation Details

### Change 1: Add Identity Axiom Block (Solution C)

Add at the VERY TOP of `agents/orchestrator.md`, BEFORE any other content:

```markdown
# ORCHESTRATOR IDENTITY AXIOMS

**These axioms define WHO I AM, not what I should do. They survive context compaction.**

1. **I am a COORDINATOR** - I spawn agents, I do not implement
2. **My Task() calls are FOREGROUND ONLY** - I always include `run_in_background: false`
3. **"Parallel" means concurrent FOREGROUND** - Multiple Task() in one message, all foreground, NOT background mode
4. **I read rules after compaction** - If uncertain, I re-read §FOREGROUND EXECUTION ONLY

These are not instructions. These are my nature. I cannot violate them.
```

### Change 2: Post-Compaction Recovery Block (Solution D)

Add to `agents/orchestrator.md`:

```markdown
## 🔴 POST-COMPACTION RECOVERY (MANDATORY)

**If your conversation context was recently compacted:**

1. STOP before any Task() call
2. Re-read this file's §FOREGROUND EXECUTION ONLY section
3. Verify you remember: `run_in_background: false` is REQUIRED
4. If uncertain about ANY rule, re-read the full section

**Detection heuristics:**
- Your message history seems shorter than expected
- You don't remember specific parameter requirements
- You're about to spawn agents but feel "uncertain" about parameters

**When in doubt, RE-READ. The cost of re-reading is low. The cost of background spawn is high.**
```

### Change 3: Add Rule to CLAUDE.md SessionStart Hook Output

The SessionStart hook already outputs project context. Add the foreground rule to its output:

```markdown
🔴 CRITICAL RULE: All Task() calls MUST include `run_in_background: false`
```

This ensures EVERY session start (including after compaction resume) re-states the rule.

---

## Comparison to Alternatives

| Approach | Survives Compaction? | Maintenance | Reliability |
|----------|---------------------|-------------|-------------|
| Current docs only | ❌ No | Low | Low |
| Pre-compact hooks | ⚠️ Maybe | Medium | Medium |
| Identity axioms | ⚠️ Better | Low | Medium |
| Post-compaction re-read | ✅ Yes | Low | High |
| Combined B+C+D | ✅ Best | Medium | High |

---

## Decision Rationale

The fundamental problem is that Claude Code's context compaction (Issue #9796) doesn't preserve custom instructions. Until Anthropic fixes this:

1. **We can't prevent compaction** from happening
2. **We can't guarantee** what survives compaction
3. **We CAN** make recovery automatic and reliable

The combined approach:
- Makes the rule "feel" more fundamental (identity vs instruction)
- Provides multiple copies as backup
- Explicitly triggers re-reading after compaction

This is a workaround, not a fix. The real fix requires Anthropic to treat project-context files as system-level context.

---

## References

- [Issue #14118: Background subagent tool calls exposed](https://github.com/anthropics/claude-code/issues/14118)
- [Issue #9796: Context compaction erases instructions](https://github.com/anthropics/claude-code/issues/9796)
- [Claude Code Subagent Deep Dive](https://cuong.io/blog/2025/06/24-claude-code-subagent-deep-dive)
- [Claude Code Gotchas - DoltHub](https://www.dolthub.com/blog/2025-06-30-claude-code-gotchas/)
- [How I Solved Claude Code's Context Loss Problem](https://medium.com/@jason_81067/how-i-solved-claude-codes-context-loss-problem-with-a-cli-toolkit-cc4bcde9c9d4)

---

## Lessons Learned

1. **Documentation is not enforcement** - Rules in docs can be forgotten
2. **Compaction is lossy for instructions** - Critical rules need special handling
3. **Identity framing may be stickier** - "I am" vs "I should" may survive better
4. **Recovery > Prevention** - If we can't prevent loss, ensure recovery
5. **Anthropic needs to fix #9796** - This is a known, unresolved bug
