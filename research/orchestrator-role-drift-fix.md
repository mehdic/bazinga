# Orchestrator Role Drift Fix: Deep Analysis

**Date:** 2025-12-18
**Context:** Orchestrators on multiple machines are violating coordinator role by running git operations and tests directly instead of spawning agents
**Decision:** Strengthen enforcement rules in orchestrator.md + add code-level guards
**Status:** Reviewed - Awaiting User Approval
**Reviewed by:** OpenAI GPT-5

---

## Problem Statement

The BAZINGA orchestrator is experiencing **role drift** - a pattern where it starts executing implementation-level commands instead of maintaining its coordinator role. Evidence from user reports:

### Observed Violations

```
❌ Bash(git log --oneline -10)
   → Should spawn Developer or Investigator for git state

❌ Bash(cd /Users/.../delivery-app && npm test -- --coverage)
   → Should spawn QA Expert for test execution

❌ Bash(python3 .claude/skills/prompt-builder/scripts/prompt_builder.py ...)
   → Should use Skill(command: "prompt-builder") not direct Bash execution

❌ Write(params_sse_test_fix.json)
   → Allowed for prompt params, but orchestrator made decision to spawn SSE
   → Decision should come from PM, not orchestrator
```

### Root Cause Analysis

1. **Incomplete Forbidden List**: The `§Bash Command Allowlist` explicitly forbids `git push/pull/merge/checkout` but NOT `git log/status/diff/show` - read-only git commands that still violate coordinator role

2. **Skill vs Bash Ambiguity**: Prompt-builder can technically be invoked via `python3 ...` (Bash) OR `Skill(command: "prompt-builder")`. The docs prefer Skill but don't FORBID Bash invocation.

3. **Resume Context Leakage**: When resuming sessions, orchestrator loads state and "knows" what needs to happen, tempting it to act directly rather than spawn PM to decide.

4. **Missing Role Drift Scenario**: The "Common Role Drift Scenarios" section doesn't include a git operations example.

---

## Proposed Solution

### Fix 1: Expand Forbidden Bash Commands

**Current** (lines 285-290):
```markdown
**Explicitly FORBIDDEN (spawn agent instead):**
- `git push/pull/merge/checkout` → Spawn Developer
- `curl *` → Spawn Investigator
- `npm/yarn/pnpm *` → Spawn Developer (except via build-baseline.sh)
- `python/pytest *` → Spawn QA Expert
```

**Proposed**:
```markdown
**Explicitly FORBIDDEN (spawn agent instead):**
- `git *` → ALL git commands (log, status, diff, show, push, pull, merge, checkout, etc.) → Spawn Developer or Investigator
- `curl *` → Spawn Investigator
- `npm/yarn/pnpm *` → ALL npm commands → Spawn Developer (except via build-baseline.sh)
- `python/pytest *` → Spawn QA Expert
- `.claude/skills/*/scripts/*.py` → NEVER run skill scripts via Bash → Use Skill tool
```

### Fix 2: Add Explicit Skill-Only Rule

Add new subsection after §Bash Command Allowlist:

```markdown
### §Skill Invocation Rule (MANDATORY)

**NEVER invoke skill scripts via Bash. ALWAYS use Skill tool.**

| ❌ FORBIDDEN | ✅ REQUIRED |
|--------------|-------------|
| `Bash: python3 .claude/skills/prompt-builder/scripts/prompt_builder.py` | `Skill(command: "prompt-builder")` |
| `Bash: python3 .claude/skills/bazinga-db/scripts/bazinga_db.py` | `Skill(command: "bazinga-db")` |
| `Bash: python3 .claude/skills/workflow-router/scripts/workflow_router.py` | `Skill(command: "workflow-router")` |

**Why:**
1. Skill tool handles context properly (params file, output parsing)
2. Bash invocation bypasses skill framework and may use wrong paths
3. Direct script execution fails when running from different working directories
```

### Fix 3: Add Role Drift Scenario for Git Operations

Add to "Common Role Drift Scenarios to AVOID":

```markdown
**Scenario 7: Checking Git State**

❌ **WRONG (Role Drift):**
```
Orchestrator: Let me check the commit history to understand current state...
[runs git log --oneline -10]
[runs git status]
[analyzes output directly]
```
Directly reading repository state instead of spawning agent.

✅ **CORRECT (Coordinator):**
```
📋 Resuming session | Need current git state | Spawning PM to assess
[Spawns PM - PM will read git state if needed]
```
```

### Fix 4: Add Role Drift Scenario for Test Execution

```markdown
**Scenario 8: Running Tests Directly**

❌ **WRONG (Role Drift):**
```
Orchestrator: Let me verify the test status before spawning QA...
[runs npm test -- --coverage]
[analyzes 47 failed tests]
Orchestrator: I see we have test failures. Let me spawn SSE to fix...
```
Running tests AND making spawn decisions - double violation!

✅ **CORRECT (Coordinator):**
```
📋 Developer complete | Status: READY_FOR_QA | Spawning QA Expert
[Spawns QA Expert - QA runs tests, reports results]
```
```

### Fix 5: Strengthen Resume Workflow

In the "Path A: RESUME" section, add warning:

```markdown
**🚨 RESUME DOES NOT MEAN INVESTIGATE**

When resuming a session:
- ❌ DO NOT run git commands to "see what changed"
- ❌ DO NOT run tests to "check current state"
- ❌ DO NOT read code files to "understand context"
- ✅ DO query database for session state (via bazinga-db skill)
- ✅ DO spawn PM to assess and decide next action
- ✅ Let PM/agents do ALL investigation

**The orchestrator resumes by spawning PM, not by investigating itself.**
```

### Fix 6: Add Runtime Anchor at Top of File

The orchestrator already has an anchor at the top, but strengthen it:

```markdown
<!--
🚨 RUNTIME ENFORCEMENT ANCHOR 🚨

If you find yourself about to:
- Run ANY git command → STOP → Spawn Developer/Investigator
- Run ANY npm/yarn/pnpm command → STOP → Spawn Developer/QA
- Run ANY python script directly → STOP → Use Skill tool
- Run ANY test framework → STOP → Spawn QA Expert
- Read ANY code file → STOP → Spawn agent to read
- Call ANY external API → STOP → Spawn Investigator
- Analyze ANY output yourself → STOP → Spawn appropriate agent

The ONLY Bash commands allowed are in §Bash Command Allowlist.
When in doubt: SPAWN AN AGENT.

This comment exists because role drift is the #1 orchestrator failure mode.
-->
```

---

## Critical Analysis

### Pros ✅

1. **Explicit Prohibition**: Changing `git push/pull/merge/checkout` to `git *` removes all ambiguity about which git commands are allowed (none)

2. **Skill-First Enforcement**: Making Skill tool mandatory for skill scripts prevents path resolution issues when running from different directories

3. **Role Drift Examples**: Adding concrete scenarios for git/test operations provides clear patterns to avoid

4. **Resume Workflow Clarity**: Explicit prohibition of investigation during resume prevents the most common drift pattern

### Cons ⚠️

1. **Anchor Relies on LLM Reading Comments**: The HTML comment anchor is not enforced by code - it relies on the LLM actually reading and following it

2. **No Runtime Enforcement**: These are all documentation changes. A determined role drift can still occur because there's no code-level enforcement

3. **Increased Prompt Size**: Adding more rules increases the orchestrator prompt size (already ~2450 lines)

4. **Edge Case: build-baseline.sh**: The script legitimately runs npm commands - need to ensure exception is clear

### Verdict

The proposed fixes are **necessary but not sufficient**. They will reduce role drift by:
- Making forbidden actions explicit (git *, npm *, etc.)
- Providing concrete examples of violations
- Reinforcing the coordinator-only role

However, true prevention would require code-level enforcement (e.g., a pre-Bash hook that validates commands against allowlist). The documentation approach is the pragmatic solution given current architecture.

---

## Implementation Details

### Files to Modify

| File | Section | Change |
|------|---------|--------|
| `agents/orchestrator.md` | §Bash Command Allowlist | Expand forbidden list |
| `agents/orchestrator.md` | (new) §Skill Invocation Rule | Add mandatory Skill usage |
| `agents/orchestrator.md` | Role Drift Scenarios | Add scenarios 7-8 |
| `agents/orchestrator.md` | Path A Resume | Add investigation warning |
| `agents/orchestrator.md` | Runtime Anchor | Strengthen top comment |

### Line Count Impact

- Current: ~2450 lines
- After changes: ~2520 lines (+70 lines)
- Acceptable increase for improved enforcement

### Backwards Compatibility

No breaking changes. All additions are additive enforcement rules.

---

## Comparison to Alternatives

### Alternative 1: Code-Level Enforcement (Hook)

**Approach:** Create a pre-Bash hook that validates commands against allowlist

**Pros:**
- True enforcement (commands get blocked)
- No reliance on LLM following instructions

**Cons:**
- Requires hook infrastructure changes
- Complex to maintain allowlist in code
- May break legitimate edge cases

**Verdict:** Better long-term, but higher implementation cost. Documentation fix is faster.

### Alternative 2: Remove Bash Tool Entirely

**Approach:** Remove Bash from orchestrator's allowed tools

**Pros:**
- Complete prevention of bash-based drift

**Cons:**
- Breaks session ID generation (`date` command)
- Breaks directory creation (`mkdir`)
- Breaks dashboard startup
- Requires refactoring initialization

**Verdict:** Too disruptive. The allowlist approach is more surgical.

### Alternative 3: Separate Orchestrator Context

**Approach:** Run orchestrator with stripped-down tool access

**Pros:**
- Structural enforcement
- Can't drift if tools aren't available

**Cons:**
- Requires Task tool changes
- Complex tool filtering logic
- May break legitimate operations

**Verdict:** Over-engineered for this problem.

---

## Decision Rationale

The documentation-based approach is chosen because:

1. **Immediate Impact**: Can be deployed now without code changes
2. **Clear Communication**: Explicit rules are easier to follow than implicit assumptions
3. **Pattern Matching**: LLMs are good at following explicit patterns/examples
4. **Low Risk**: No risk of breaking existing functionality
5. **Incremental**: Can add code enforcement later if drift persists

---

## Multi-LLM Review Integration

**Reviewed by:** OpenAI GPT-5 (2025-12-18)

### 🔴 Critical Issues Identified (Must Fix)

| Issue | Impact | Resolution |
|-------|--------|------------|
| **Blanket "git *" breaks init** | `git branch --show-current` is ALREADY ALLOWED in allowlist. Blanket ban would break Step 0 initialization | Change from "git * forbidden" to ALLOWLIST approach: only `git branch --show-current` allowed, all others forbidden |
| **Documentation-only is insufficient** | Prior drift happened despite existing docs | Add code-level enforcement (hooks, validators) - see Implementation Plan |
| **orchestrator_speckit.md not updated** | Drift will recur in spec-kit mode | Must mirror changes in both orchestrator variants |
| **Resume always-PM is suboptimal** | Database may already know next agent | Use workflow-router for resume routing, not always PM |

### Incorporated Feedback

1. **✅ ACCEPT: Precise git allowlist (not blanket ban)**
   - My original: `git * → ALL git commands forbidden`
   - Corrected: `git branch --show-current` ALLOWED (init only), all others FORBIDDEN
   - Reason: Critical bug - would have broken initialization

2. **✅ ACCEPT: Code-level enforcement**
   - Add pre-Bash validator hook
   - Add Skill-only enforcement for skill scripts
   - This addresses root cause, not just symptoms

3. **✅ ACCEPT: Update orchestrator_speckit.md**
   - Mirror all guardrail changes
   - Without this, drift will happen in spec-kit orchestrations

4. **✅ ACCEPT: Workflow-router for resume**
   - Change resume logic from "always spawn PM" to "consult workflow-router"
   - More efficient, respects deterministic routing

5. **✅ ACCEPT: Extract guardrails to template**
   - Move new sections to `templates/orchestrator/guardrails.md`
   - Reduces prompt bloat, single source of truth

### Rejected Suggestions (With Reasoning)

1. **❌ DEFER: Full Bash removal from orchestrator**
   - Reason: Requires new "orchestrator-init" skill
   - Too much scope creep for this fix
   - Can revisit later if drift persists

2. **❌ DEFER: Behavior validator scanning logs**
   - Good idea but adds complexity
   - Focus on prevention (blocking) vs detection
   - Can add later for telemetry

3. **❌ DEFER: Auto-correct violations**
   - Risky - could mask problems
   - Better to fail fast and fix root cause

---

## 📋 Revised Implementation Plan (Post-Review)

### Phase 1: Documentation Fixes (Immediate)

| File | Change | Priority |
|------|--------|----------|
| `agents/orchestrator.md` | Fix git allowlist (not blanket ban) | P0 |
| `agents/orchestrator.md` | Add Skill-only rule section | P0 |
| `agents/orchestrator.md` | Add role drift scenarios 7-8 | P1 |
| `agents/orchestrator.md` | Strengthen Runtime Anchor | P1 |
| `agents/orchestrator_speckit.md` | Mirror ALL changes | P0 |
| `templates/orchestrator/guardrails.md` | Extract reusable guardrails | P2 |

### Phase 2: Code-Level Enforcement (Follow-up)

| Component | Purpose | Files |
|-----------|---------|-------|
| Pre-Bash validator hook | Block forbidden commands at runtime | New hook script |
| Skill-only gate | Block `.claude/skills/*` via Bash | Hook or wrapper |
| Read-path validator | Restrict orchestrator Read paths | Hook or wrapper |

### Specific Changes (Corrected)

**1. Git Allowlist (NOT blanket ban)**

```markdown
### §Bash Command Allowlist (EXHAUSTIVE)

**ALLOWED Git Commands (init only):**
| Pattern | Purpose |
|---------|---------|
| `git branch --show-current` | Get current branch during initialization |

**FORBIDDEN Git Commands (ALL others):**
| Pattern | Why Forbidden | Instead |
|---------|---------------|---------|
| `git log *` | Reading history | Spawn Developer/Investigator |
| `git status` | Checking state | Spawn Developer |
| `git diff *` | Viewing changes | Spawn Developer |
| `git show *` | Viewing commits | Spawn Developer/Investigator |
| `git push/pull/merge/checkout` | Modifying repo | Spawn Developer |

**If it's a git command and NOT `git branch --show-current` → FORBIDDEN**
```

**2. Skill-Only Rule (New Section)**

```markdown
### §Skill Invocation Rule (MANDATORY)

**NEVER invoke skill scripts via Bash. ALWAYS use Skill tool.**

| ❌ FORBIDDEN | ✅ REQUIRED |
|--------------|-------------|
| `python3 .claude/skills/prompt-builder/scripts/prompt_builder.py` | `Skill(command: "prompt-builder")` |
| `python3 .claude/skills/bazinga-db/scripts/bazinga_db.py` | `Skill(command: "bazinga-db")` |
| `python3 .claude/skills/workflow-router/scripts/workflow_router.py` | `Skill(command: "workflow-router")` |

**Any command matching `.claude/skills/**/scripts/*.py` → FORBIDDEN**

**Why:**
1. Skill tool handles context properly (params file, output parsing)
2. Bash invocation bypasses skill framework and may use wrong paths
3. Direct script execution fails when running from different working directories
```

**3. Role Drift Scenario 7 (Git Operations)**

```markdown
**Scenario 7: Checking Git State**

❌ **WRONG (Role Drift):**
```
Orchestrator: Let me check the commit history to understand current state...
[runs git log --oneline -10]
[runs git status]
[analyzes output directly]
```
Directly reading repository state instead of spawning agent.

✅ **CORRECT (Coordinator):**
```
📋 Resuming session | Querying database for state
[Skill(command: "bazinga-db") → get task groups]
[Skill(command: "workflow-router") → determine next action]
[Spawns appropriate agent based on router decision]
```
```

**4. Role Drift Scenario 8 (Running Tests)**

```markdown
**Scenario 8: Running Tests Directly**

❌ **WRONG (Role Drift):**
```
Orchestrator: Let me verify the test status before spawning QA...
[runs npm test -- --coverage]
[analyzes 47 failed tests]
Orchestrator: I see we have test failures. Let me spawn SSE to fix...
```
Running tests AND making spawn decisions - double violation!

✅ **CORRECT (Coordinator):**
```
📋 Developer complete | Status: READY_FOR_QA | Spawning QA Expert
[Spawns QA Expert - QA runs tests, reports results]
[QA returns FAIL → Workflow-router decides next agent]
```
```

**5. Resume Workflow (Use Workflow-Router)**

```markdown
**🚨 RESUME DOES NOT MEAN INVESTIGATE**

When resuming a session:
- ❌ DO NOT run git commands to "see what changed"
- ❌ DO NOT run tests to "check current state"
- ❌ DO NOT read code files to "understand context"
- ✅ DO query database for session state (via bazinga-db skill)
- ✅ DO invoke workflow-router to determine next agent
- ✅ Let workflow-router decide: PM, Developer, QA, or Tech Lead

**Resume Flow:**
1. `Skill(command: "bazinga-db")` → get session state
2. `Skill(command: "bazinga-db")` → get task groups
3. `Skill(command: "workflow-router")` → determine next action
4. Spawn agent based on router decision (NOT always PM)
```

---

## Lessons Learned

1. **Explicit > Implicit**: `git push/pull/merge/checkout` implied other git commands were OK. Explicit `git *` leaves no room for interpretation.

2. **Examples Prevent Drift**: Role drift scenarios with concrete violations are more effective than abstract rules.

3. **Resume is Dangerous**: The resume workflow is when drift is most likely because the orchestrator "knows" context and is tempted to act on it.

---

## References

- User report showing git log/npm test violations
- agents/orchestrator.md (source of truth)
- .claude/commands/bazinga.orchestrate.md (generated from source)
