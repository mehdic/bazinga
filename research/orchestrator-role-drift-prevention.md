# Orchestrator Role Drift Prevention: Deep Analysis

**Date:** 2025-12-09
**Context:** Observed orchestrator directly executing git push, CI monitoring, and log analysis instead of spawning agents
**Decision:** Pending - analyzing solutions
**Status:** Proposed
**Reviewed by:** (pending)

---

## Problem Statement

The BAZINGA orchestrator is designed as a **coordinator-only** agent that spawns specialized agents (Developer, QA Expert, Tech Lead, Investigator) to perform actual work. However, in practice, we observed significant **role drift** where the orchestrator:

1. Directly executed `git push origin main`
2. Made curl requests to GitHub API to check CI status
3. Read `.env` files for credentials
4. Downloaded and analyzed CI logs
5. Drew conclusions about whether failures were pre-existing

This violates the core principle: "I coordinate agents, I do not implement."

### Root Cause Analysis

**Why did drift occur?**

1. **Implicit workflow gap**: The merge step says "Spawn Developer (merge task)" but lacks explicit spawn template
2. **Natural extension trap**: "Verify merge worked" naturally leads to "check CI" which leads to "analyze failures"
3. **No enforcement mechanism**: Rules are instructional only - no structural barriers
4. **Missing scenario coverage**: Role drift examples don't cover merge/CI monitoring case
5. **Long conversation decay**: After many messages, the coordinator identity weakens
6. **Ambiguous boundaries**: "Bash for init only" doesn't enumerate what counts as init

### Impact

- Orchestrator consumes tokens doing work agents should do
- Loses architectural benefits of specialized agents (e.g., Investigator's deep analysis capabilities)
- Breaks the audit trail (work not logged as agent interactions)
- Sets precedent for further drift

---

## Solution: Multi-Layer Defense Strategy

### Layer 1: Explicit Scenario Coverage (Documentation)

**Add merge/CI monitoring to Role Drift Prevention section:**

```markdown
**Scenario 3: Post-merge CI monitoring**

❌ **WRONG (Role Drift):**
```
Tech Lead: APPROVED
Orchestrator: Let me push to main and check CI...
[runs git push, curl to GitHub API, analyzes logs]
```

✅ **CORRECT (Coordinator):**
```
Tech Lead: APPROVED
[Spawns Developer with merge task]
Developer: MERGE_SUCCESS, CI status: 2 workflows running
[If detailed CI analysis needed]
[Spawns Investigator for CI analysis]
Investigator: CI failures pre-existing (babel-plugin-istanbul issue)
[Routes findings to PM]
```

**Scenario 4: External API interaction**

❌ **WRONG:** Orchestrator runs `curl` to GitHub/external APIs
✅ **CORRECT:** Spawn Investigator for any external data gathering
```

### Layer 2: Explicit Merge Developer Prompt Template

**Add to phase_simple.md and phase_parallel.md:**

```markdown
### Step 2A.7a: Spawn Developer for Merge (MANDATORY TEMPLATE)

**YOU MUST spawn a Developer agent. DO NOT execute merge yourself.**

Task(
  subagent_type: "general-purpose",
  model: MODEL_CONFIG["developer"],
  description: "Developer: merge and verify CI",
  prompt: """
You are a Developer performing a MERGE TASK.

## Your Task
1. Merge the approved changes to {initial_branch}
2. Push to remote
3. Check CI status (wait up to 3 minutes for initial results)
4. Report back with status

## Required Actions
- git merge or git rebase as appropriate
- git push origin {initial_branch}
- Check CI workflow status via GitHub API or gh CLI

## Your Response Format
Return ONE of these statuses:

**MERGE_SUCCESS**
- Merge completed successfully
- CI status: [passing/running/not configured]
- Summary: [brief description]

**MERGE_CONFLICT**
- Conflicts in: [list files]
- Suggested resolution: [brief guidance]

**MERGE_TEST_FAILURE**
- CI failures detected
- Failing workflows: [list]
- Error summary: [brief description]
- Assessment: [new failures vs pre-existing]

**MERGE_CI_PREEXISTING**
- Merge successful
- CI failures detected BUT pre-existing (not caused by our changes)
- Evidence: [how you determined this]
"""
)
```

### Layer 3: Command Allowlist Enforcement

**Replace vague "Bash for init only" with explicit allowlist:**

```markdown
### 🚨 BASH COMMAND ALLOWLIST (EXHAUSTIVE)

**You may ONLY execute these Bash patterns:**

| Pattern | Purpose | Example |
|---------|---------|---------|
| `SESSION_ID=bazinga_$(date...)` | Generate session ID | Init only |
| `mkdir -p bazinga/artifacts/...` | Create directories | Init only |
| `mkdir -p bazinga/...` | Create bazinga subdirs | Init only |
| `test -f bazinga/...` | Check file existence | Config checks |
| `cat bazinga/*.json` | Read config files | Use Read tool instead when possible |
| `kill -0 $(cat bazinga/dashboard.pid)` | Dashboard check | Init only |
| `bash bazinga/scripts/start-dashboard.sh` | Start dashboard | Init only |

**ANY command not matching above patterns → STOP → Spawn agent**

**Explicitly FORBIDDEN (spawn agent instead):**
- `git *` → Spawn Developer
- `curl *` → Spawn Investigator
- `npm *`, `yarn *`, `pnpm *` → Spawn Developer or QA
- `python *`, `pytest *` → Spawn QA Expert
- `cat` on non-bazinga paths → Spawn agent to read
- Any command with credentials/tokens → Spawn agent
```

### Layer 4: Pre-Command Self-Check Gate

**Add mandatory validation before any Bash execution:**

```markdown
### 🔒 PRE-BASH VALIDATION (MANDATORY)

Before EVERY Bash tool invocation, execute this internal check:

```
INTERNAL CHECK (do not output to user):
1. Is this command in the ALLOWLIST above?
2. Am I doing this because an agent should do it?
3. Would a Developer/QA/Investigator normally do this?

IF any answer is "no" or "yes" to #2/#3:
  → STOP
  → Identify correct agent
  → Spawn that agent instead
```

**This check is NON-NEGOTIABLE. Role drift often starts with "just one quick command."**
```

### Layer 5: Structural Isolation (Template Separation)

**Create dedicated merge phase template:**

File: `bazinga/templates/orchestrator/phase_merge.md`

Purpose: Isolate the post-approval workflow into a separate template that:
1. ONLY contains spawn instructions
2. Has no Bash commands at all
3. Forces the orchestrator to read and follow agent-spawn-only instructions

```markdown
# Phase: Post-Approval Merge

**⚠️ THIS PHASE CONTAINS NO BASH COMMANDS**
**ALL WORK IS DONE BY SPAWNING AGENTS**

## When Tech Lead Returns APPROVED

### Step M.1: Spawn Developer for Merge
[Explicit spawn template - no shortcuts]

### Step M.2: Handle Developer Response
- MERGE_SUCCESS → Step M.3
- MERGE_CONFLICT → Respawn Developer with conflict details
- MERGE_TEST_FAILURE → Step M.2a
- MERGE_CI_PREEXISTING → Step M.3 (proceed, log pre-existing issues)

### Step M.2a: CI Failure Investigation
**DO NOT analyze CI yourself. Spawn Investigator:**
[Explicit Investigator spawn template]

### Step M.3: Route to PM
[Spawn PM for final assessment]
```

### Layer 6: Runtime Enforcement Comment

**Add at top of orchestrator.md:**

```markdown
<!--
🚨 RUNTIME ENFORCEMENT ANCHOR 🚨

If you find yourself about to:
- Run a git command → STOP → Spawn Developer
- Call an external API → STOP → Spawn Investigator
- Analyze logs/output → STOP → Spawn appropriate agent
- Read code files → STOP → Spawn agent to read

The ONLY exception is the explicit ALLOWLIST in §Bash Command Allowlist.

This comment exists because role drift is the #1 orchestrator failure mode.
Seeing this comment should trigger immediate self-correction.
-->
```

---

## Critical Analysis

### Pros ✅

1. **Multi-layered defense**: No single point of failure
2. **Explicit over implicit**: Allowlist removes ambiguity
3. **Scenario-based learning**: Concrete examples prevent the observed failure
4. **Structural barriers**: Separate template physically isolates danger zone
5. **Self-correction triggers**: Runtime comment catches drift in progress
6. **Backwards compatible**: No changes to agent definitions or database schema

### Cons ⚠️

1. **Increased orchestrator size**: Adding ~100 lines to already large file
2. **Maintenance burden**: Allowlist needs updating if new init commands added
3. **Not foolproof**: LLM can still ignore instructions under pressure
4. **Template proliferation**: Another template file to maintain
5. **Doesn't address root cause**: LLMs naturally want to "help" by doing work

### Alternative Approaches Considered

**A. Tool-level enforcement (rejected)**
- Modify Task tool to reject certain Bash commands
- Rejected: Requires code changes outside our control

**B. Separate orchestrator identity per phase (rejected)**
- Spawn a "Merge Coordinator" sub-orchestrator
- Rejected: Adds complexity, coordination overhead

**C. Shorter orchestrator context (rejected)**
- Compress orchestrator.md to reduce drift
- Rejected: Already near minimum for required logic

**D. Post-hoc validation agent (considered)**
- Spawn validator after each orchestrator action
- Considered: Could catch drift but adds latency

---

## Implementation Details

### Files to Modify

1. **`agents/orchestrator.md`**
   - Add Scenario 3 & 4 to Role Drift Prevention (§Layer 1)
   - Add Bash Command Allowlist section (§Layer 3)
   - Add Pre-Bash Validation gate (§Layer 4)
   - Add Runtime Enforcement Comment at top (§Layer 6)

2. **`bazinga/templates/orchestrator/phase_simple.md`**
   - Add explicit merge developer spawn template (§Layer 2)
   - Add CI failure investigation spawn template

3. **`bazinga/templates/orchestrator/phase_parallel.md`**
   - Same changes as phase_simple.md

4. **NEW: `bazinga/templates/orchestrator/phase_merge.md`** (§Layer 5)
   - Dedicated merge phase template
   - Zero Bash commands
   - Agent-spawn-only instructions

### Implementation Order

1. Layer 1 (scenarios) - Immediate, low risk
2. Layer 2 (merge template) - Immediate, addresses observed failure
3. Layer 3 (allowlist) - High impact, requires careful enumeration
4. Layer 6 (runtime comment) - Quick win
5. Layer 4 (pre-bash gate) - After allowlist is stable
6. Layer 5 (structural) - Optional, for persistent drift issues

### Estimated Changes

| File | Lines Added | Lines Modified |
|------|-------------|----------------|
| orchestrator.md | ~80 | ~10 |
| phase_simple.md | ~40 | ~5 |
| phase_parallel.md | ~40 | ~5 |
| phase_merge.md (new) | ~60 | N/A |

---

## Comparison to Alternatives

| Approach | Effectiveness | Complexity | Maintenance |
|----------|--------------|------------|-------------|
| **This proposal** | High | Medium | Medium |
| Tool-level enforcement | Very High | High (code changes) | Low |
| Sub-orchestrator | Medium | High | High |
| Shorter context | Low | Low | Low |
| Post-hoc validator | Medium | Medium | Medium |

---

## Decision Rationale

This multi-layer approach is recommended because:

1. **Addresses observed failure directly**: Merge/CI scenario coverage
2. **Defense in depth**: Multiple independent barriers
3. **Implementable now**: No external dependencies
4. **Reversible**: Can remove layers if they cause issues
5. **Educational**: Scenarios teach correct behavior, not just rules

The key insight is that role drift isn't a single failure - it's a cascade. Each layer interrupts the cascade at a different point:
- Layer 1: Prevents starting the cascade (recognition)
- Layer 2: Provides correct alternative (replacement behavior)
- Layer 3: Hard boundary (allowlist)
- Layer 4: Self-check (metacognition)
- Layer 5: Structural isolation (physical barrier)
- Layer 6: Runtime trigger (emergency brake)

---

## Success Metrics

After implementation, monitor for:

1. **Zero direct git/curl commands** from orchestrator in next 10 sessions
2. **Merge tasks always spawn Developer** agent
3. **CI analysis always spawns Investigator** when needed
4. **No new role drift patterns** emerge

---

## Open Questions

1. Should we add a "role drift detected" self-reporting mechanism?
2. Should the allowlist be in a separate config file for easier updates?
3. Is Layer 5 (structural separation) worth the template proliferation?
4. Should we add automated testing for orchestrator behavior?

---

## References

- Observed failure transcript (user-provided)
- `agents/orchestrator.md` - Current orchestrator definition
- `bazinga/templates/orchestrator/phase_simple.md` - Simple mode template
- `bazinga/templates/orchestrator/phase_parallel.md` - Parallel mode template
- `.claude/claude.md` - Project context and orchestrator rules
