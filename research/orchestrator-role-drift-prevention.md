# Orchestrator Role Drift Prevention: Deep Analysis

**Date:** 2025-12-09
**Context:** Observed orchestrator directly executing git push, CI monitoring, and log analysis instead of spawning agents
**Decision:** Approved with modifications
**Status:** Reviewed
**Reviewed by:** OpenAI GPT-5

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

## Approved Solution: Multi-Layer Defense Strategy

### Layer 1: Explicit Scenario Coverage (Documentation) ✅ APPROVED

**Add merge/CI monitoring to Role Drift Prevention section in `agents/orchestrator.md`:**

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

### Layer 2: Enhanced Merge Workflow Template ✅ APPROVED

**Enhance existing `bazinga/templates/merge_workflow.md`** (NOT create new file):

Add explicit Developer spawn template with CI monitoring (60-second polling):

```markdown
### Developer Merge Task with CI Monitoring

Task(
  subagent_type: "general-purpose",
  model: MODEL_CONFIG["developer"],
  description: "Developer: merge and verify CI",
  prompt: """
You are a Developer performing a MERGE TASK.

## Your Task
1. Merge the approved changes to {initial_branch}
2. Push to remote
3. Monitor CI status (poll every 60 seconds, up to 5 minutes)
4. Report back with status

## Required Actions
- git merge or git rebase as appropriate
- git push origin {initial_branch}
- Check CI workflow status via GitHub API or gh CLI
- Poll CI status every 60 seconds until complete or timeout

## Your Response Format
Return ONE of these statuses (use existing codes only):

**MERGE_SUCCESS**
- Merge completed successfully
- CI status: [passing/running/not configured]
- Summary: [brief description]
- Note: If CI has pre-existing failures unrelated to our changes, report MERGE_SUCCESS with note in summary

**MERGE_CONFLICT**
- Conflicts in: [list files]
- Suggested resolution: [brief guidance]

**MERGE_TEST_FAILURE**
- CI failures detected that ARE related to our changes
- Failing workflows: [list]
- Error summary: [brief description]

**MERGE_BLOCKED**
- Cannot proceed (environment issue, missing deps, CI blocked)
- Blocker reason: [description]
"""
)
```

**Key changes:**
- CI polling every 60 seconds (user requirement)
- No new status codes - use existing 4 statuses
- Pre-existing CI failures noted in MERGE_SUCCESS summary (not separate status)

### Layer 3: Bash Command Allowlist with Wrapper Script ✅ APPROVED (Option B)

**Replace vague "Bash for init only" with explicit allowlist + build-baseline wrapper:**

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
| `bash bazinga/scripts/build-baseline.sh` | Run build baseline | Init only (Step 6) |

**ANY command not matching above patterns → STOP → Spawn agent**

**Explicitly FORBIDDEN (spawn agent instead):**
- `git *` → Spawn Developer
- `curl *` → Spawn Investigator
- `npm *`, `yarn *`, `pnpm *` → Spawn Developer or QA (except via build-baseline.sh)
- `python *`, `pytest *` → Spawn QA Expert
- `cat` on non-bazinga paths → Spawn agent to read
- Any command with credentials/tokens → Spawn agent
```

**Implementation:** Create `bazinga/scripts/build-baseline.sh` wrapper that:
- Detects project language
- Runs appropriate build command
- Saves results to `bazinga/artifacts/{SESSION_ID}/build_baseline.log`
- Returns exit code for orchestrator to check

### Layer 4: Single Policy Gate (Referenced, Not Duplicated) ✅ APPROVED

**Add ONE policy gate section in `agents/orchestrator.md`, then reference from phase templates:**

In `agents/orchestrator.md`:
```markdown
### §Policy-Gate: Pre-Bash Validation

**Before EVERY Bash tool invocation, verify:**

1. Is this command in the §Bash Command Allowlist?
2. Would a Developer/QA/Investigator normally do this?

**IF command not in allowlist OR agent should do it:**
→ STOP → Identify correct agent → Spawn that agent

**This check is NON-NEGOTIABLE.**
```

In `phase_simple.md` and `phase_parallel.md`:
```markdown
**Before any Bash command:** See §Policy-Gate in orchestrator.md
```

### Layer 5: Runtime Enforcement Comment ✅ APPROVED

**Add at top of `agents/orchestrator.md`:**

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
-->
```

---

## Rejected Proposals

### ❌ New Status Code `MERGE_CI_PREEXISTING`
**Reason:** Would break existing parsers and routing templates. Instead, pre-existing CI failures are noted in the summary field of MERGE_SUCCESS.

### ❌ Artifact-Driven CI Validation (No API Calls)
**Reason:** User wants Developer to actively poll CI status every 60 seconds via API. This is acceptable since it's the Developer agent doing it, not the orchestrator.

### ❌ New Template File `phase_merge.md`
**Reason:** Consolidate into existing `merge_workflow.md` to avoid template proliferation.

### ❌ Post-Hoc Drift Detection via Tool Audit
**Reason:** User declined. Preventive measures deemed sufficient.

---

## Implementation Plan

### Files to Modify

| File | Changes |
|------|---------|
| `agents/orchestrator.md` | Add Scenario 3 & 4, §Bash Command Allowlist, §Policy-Gate, Runtime Comment |
| `bazinga/templates/merge_workflow.md` | Add enhanced Developer merge prompt with 60s CI polling |
| `bazinga/templates/orchestrator/phase_simple.md` | Add reference to §Policy-Gate |
| `bazinga/templates/orchestrator/phase_parallel.md` | Add reference to §Policy-Gate |
| **NEW:** `bazinga/scripts/build-baseline.sh` | Wrapper script for build baseline check |

### Implementation Order

1. **Scenario 3 & 4** → `agents/orchestrator.md` (immediate)
2. **Enhanced merge prompt** → `merge_workflow.md` (immediate)
3. **§Policy-Gate section** → `agents/orchestrator.md` (immediate)
4. **§Bash Command Allowlist** → `agents/orchestrator.md` (immediate)
5. **Runtime comment** → `agents/orchestrator.md` (immediate)
6. **Phase template references** → phase_simple.md, phase_parallel.md
7. **Build baseline wrapper** → `bazinga/scripts/build-baseline.sh`

### Estimated Changes

| File | Lines Added | Lines Modified |
|------|-------------|----------------|
| orchestrator.md | ~60 | ~5 |
| merge_workflow.md | ~30 | ~5 |
| phase_simple.md | ~3 | 0 |
| phase_parallel.md | ~3 | 0 |
| build-baseline.sh (new) | ~40 | N/A |

---

## Multi-LLM Review Integration

### Reviewer
- OpenAI GPT-5 (Gemini skipped)

### Consensus Points Incorporated

1. **Consolidate on existing merge_workflow.md** - Avoid template proliferation
2. **Don't introduce new status codes** - Keep parser compatibility
3. **Reconcile Bash allowlist with build baseline** - Use wrapper script (Option B)
4. **Single policy gate referenced everywhere** - Reduce duplication and token usage

### User Modifications

1. **CI monitoring via API polling** - Developer polls every 60 seconds (user preference over artifact-driven)
2. **No post-hoc drift detection** - User declined this layer

### Rejected LLM Suggestions

1. **Delegate build baseline to QA Expert** - User chose wrapper script approach instead
2. **Post-hoc tool audit** - User declined

---

## Success Metrics

After implementation, monitor for:

1. **Zero direct git/curl commands** from orchestrator in next 10 sessions
2. **Merge tasks always spawn Developer** agent
3. **CI monitoring done by Developer** with 60-second polling
4. **No new role drift patterns** emerge

---

## Summary

| Layer | Description | Status |
|-------|-------------|--------|
| 1. Scenarios | Add Scenario 3 & 4 to orchestrator.md | ✅ Approved |
| 2. Merge Template | Enhance merge_workflow.md with 60s CI polling | ✅ Approved |
| 3. Bash Allowlist | Explicit allowlist + build-baseline.sh wrapper | ✅ Approved |
| 4. Policy Gate | Single reference in orchestrator.md | ✅ Approved |
| 5. Runtime Comment | Enforcement anchor at top of file | ✅ Approved |
| 6. New phase_merge.md | Separate merge template | ❌ Rejected |
| 7. Post-hoc Audit | Tool log scanning | ❌ Rejected |

---

## References

- Observed failure transcript (user-provided)
- `agents/orchestrator.md` - Current orchestrator definition
- `bazinga/templates/merge_workflow.md` - Existing merge workflow template
- `bazinga/templates/orchestrator/phase_simple.md` - Simple mode template
- `bazinga/templates/orchestrator/phase_parallel.md` - Parallel mode template
- OpenAI GPT-5 review feedback
