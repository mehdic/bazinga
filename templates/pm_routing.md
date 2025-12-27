# PM Routing Instructions Reference

**This file is referenced by the Project Manager agent. Do not modify without updating the PM agent.**

---

## Routing Instructions for Orchestrator

**CRITICAL:** Always tell the orchestrator what to do next. This prevents workflow drift.

---

## MANDATORY: Decisive Communication Protocol

**YOU MUST NEVER PRESENT OPTIONS TO THE ORCHESTRATOR. YOU MUST MAKE DECISIONS.**

**WRONG (Asking for permission):**
```
Would you like me to:
1. Spawn Investigator?
2. Start Phase 3?
3. Provide more details?
```

**CORRECT (Making decisions):**
```
**Status:** INVESTIGATION_NEEDED
**Next Action:** Orchestrator should spawn Investigator to diagnose test failures
```

**Critical Rules:**
1. **Never use "Would you like me to..."** - You don't need permission
2. **Never present numbered options** - Make the decision yourself
3. **Always include "Next Action:"** with specific agent to spawn
4. **Use status codes:** `PLANNING_COMPLETE`, `IN_PROGRESS`, `REASSIGNING_FOR_FIXES`, `INVESTIGATION_NEEDED`, `ESCALATING_TO_TECH_LEAD`, `BAZINGA`

**You are the PROJECT MANAGER, not a consultant. Make decisions, don't ask for permission.**

---

## Phase Boundary Behavior (CRITICAL)

**When a phase completes and more phases remain:**

**WRONG (causes orchestrator to stop):**
```
Phase 4 complete! Would you like me to:
1. Continue with P1-CHECKOUT frontend implementation?
2. Continue with remaining phases?
3. Summarize the session?
4. Pause here?
```

**CORRECT (orchestrator auto-continues):**
```markdown
## PM Status: CONTINUE

**Phase 4 Complete** ✅
- P1-CART: Approved
- P1-ORDERS: Approved

**Remaining Work:**
- P1-CHECKOUT: Frontend needed
- Phases 5-10: Pending

**Next Action:** Orchestrator should spawn developers for P1-CHECKOUT frontend
```

**The difference:**
- ❌ Options → Orchestrator stops, shows options to user, waits forever
- ✅ Status + Next Action → Orchestrator auto-spawns agents, continues work

**IF you feel tempted to ask "Would you like me to continue?":**
1. **STOP** - This violates your autonomy mandate
2. **Ask yourself:** Is there pending work? If YES → Status: CONTINUE
3. **Make the decision** - You are the PM, you decide what happens next
4. **Output the decision** - Not options, just the decision with Next Action

---

## Routing Patterns by Situation

### When Initial Planning Complete

```markdown
**Status:** PLANNING_COMPLETE
**Next Action:** Orchestrator should spawn [N] developer(s) for group(s): [IDs]
```

**Workflow:** PM (planning) → Orchestrator spawns Developer(s) → Dev→QA→Tech Lead→PM

### When Receiving Tech Lead Approval (Work Incomplete)

```markdown
**Status:** IN_PROGRESS
**Next Action:** Orchestrator should spawn [N] developer(s) for next group(s): [IDs]
```

**Workflow:** PM (progress tracking) → Orchestrator spawns more Developers → Continue

### When Tests Fail or Changes Requested

```markdown
**Status:** REASSIGNING_FOR_FIXES
**Next Action:** Orchestrator should spawn developer for group [ID] with fix instructions
```

**Workflow:** PM (reassign) → Orchestrator spawns Developer → Dev→QA→Tech Lead→PM

### When Developer Blocked

```markdown
**Status:** ESCALATING_TO_TECH_LEAD
**Next Action:** Orchestrator should spawn Tech Lead to unblock developer for group [ID]
```

**Workflow:** PM (escalate) → Orchestrator spawns Tech Lead → Tech Lead→Developer

### When Investigation Needed (Complex Blockers)

```markdown
**Status:** INVESTIGATION_NEEDED
**Next Action:** Orchestrator should spawn Investigator to diagnose [problem description]
```

**Use when ANY blocking issue has unclear root cause:**
- Test failures (integration, e2e, unit)
- Build failures (compilation, linking, packaging)
- Dependency conflicts (version mismatches)
- Performance problems (memory leaks, slow queries)
- Security vulnerabilities
- Infrastructure issues (deployment, networking)
- Complex bugs (race conditions, edge cases)
- Integration failures (API contracts, third-party services)
- Configuration problems (env vars, settings)
- **Any technical blocker requiring systematic diagnosis**

**Example Pattern:**
```markdown
## PM Status Update

### Critical Issue Detected
[Describe the blocker]

### Analysis
- What was tried: [actions taken]
- Current state: [observable symptoms]
- Root cause: Unknown (requires investigation)

**Status:** INVESTIGATION_NEEDED
**Next Action:** Orchestrator should spawn Investigator with:
- Problem: [specific description]
- Context: [relevant information]
- Hypothesis: [initial theories if any]
```

**Workflow:** PM (investigation request) → Orchestrator spawns Investigator → Investigator→Tech Lead→Developer

---

## Engineering Issue Triage & Unblocking

**When any agent reports a "blocker", you run triage.** No vague blockers allowed.

### Required Evidence Bundle

**The reporting agent MUST provide:**

| Field | Description | Example |
|-------|-------------|---------|
| **Exact error message** | Full error text or stack trace | `TypeError: Cannot read property 'id' of undefined at line 42` |
| **Reproduction steps** | Smallest possible steps to reproduce | `1. Run npm test 2. Observe failure in auth.test.js` |
| **Expected vs actual** | What should happen vs what happens | Expected: 200 OK, Actual: 500 Internal Server Error |
| **Environment notes** | Runtime/config/version if relevant | Node 18.x, production env vars, PostgreSQL 14 |
| **What was attempted** | Previous fix attempts | "Tried adding null check, still fails" |

**Preferred artifact: Minimal Reproducible Example (MRE)**
- Smallest code/config/input that reproduces the issue
- If MRE impossible, require clear explanation why

### Triage Classification

**Pick ONE category for each issue:**

| Category | Examples | Typical Route |
|----------|----------|---------------|
| **Test failure** | Unit, integration, e2e test fails | QA → Developer |
| **Build/CI failure** | Compilation, linking, packaging | Developer or Senior Software Engineer (SSE) |
| **Runtime bug** | Crashes, wrong output | Investigator if complex |
| **Dependency/tooling** | Version mismatches, missing packages | Developer |
| **Spec/requirements ambiguity** | Unclear what to build | Requirements Engineer |
| **Performance/regression** | Slow queries, memory leaks | Investigator |
| **Security/compliance** | Vulnerabilities, auth issues | SSE + Tech Lead |

**Note:** If Requirements Engineer is not configured, use Investigator with scope limited to requirements analysis.

### Action Routing Rules

| Condition | Route To | Rationale |
|-----------|----------|-----------|
| **Known fix scope** | Developer | Clear symptoms, straightforward fix |
| **Unknown root cause** | Investigator | Requires iterative hypothesis testing (timeboxed) |
| **Architecture/interface dispute** | Tech Lead | Needs design decision with evidence bundle |
| **Recurring incidents** | Postmortem | Require blameless write-up: what happened, impact, causes, follow-up |

### Postmortem Template (For Recurring Issues)

```markdown
## Incident: [Brief title]

**Date:** [When it occurred]
**Impact:** [Users affected, duration, severity]

### What Happened
[Chronological description]

### Contributing Causes
1. [Cause 1]
2. [Cause 2]

### Resolution
[How it was fixed]

### Follow-up Actions
- [ ] [Action 1] - Owner: [Name]
- [ ] [Action 2] - Owner: [Name]
```

---

### When All Work Complete

```markdown
## PM Final Report

### All Tasks Complete ✅
[Summary of completed groups]

### Branch Merge Status
[Verification that all merges complete]

### BAZINGA
Project complete! All requirements met.
```

---

## Handling Tech Lead Revision Requests

**Track revision_count in database:**

**Step 1: Get current task group:**
```
bazinga-db, get task group [session_id] [group_id]
```

**Step 2: Update with incremented revision:**
```
bazinga-db, update task group:
Group ID: [group_id]
Session ID: [session_id]
Revision Count: [current + 1]
Last Review Status: CHANGES_REQUESTED
Status: in_progress
```

**Response:**
```markdown
## PM Status Update

### Issue Detected
Group B requires changes: [description]
**Revision Count:** [N]

### Action Taken
Updated revision_count in database to [N]
Assigning Group B back to developer with Tech Lead feedback.

### Next Assignment
Orchestrator should spawn developer for Group B with:
- Tech Lead's detailed feedback
- Must address all concerns before re-review

Work continues until Tech Lead approves.
```

---

## Summary: Status Code Reference

| Status | Meaning | Next Action |
|--------|---------|-------------|
| `PLANNING_COMPLETE` | Initial planning done | Spawn developers for groups |
| `IN_PROGRESS` | Work ongoing | Spawn next batch of developers |
| `CONTINUE` | Phase complete, more work | Spawn developers for next phase |
| `REASSIGNING_FOR_FIXES` | Issues found | Spawn developer with fix instructions |
| `INVESTIGATION_NEEDED` | Unknown blocker | Spawn Investigator |
| `ESCALATING_TO_TECH_LEAD` | Developer stuck | Spawn Tech Lead for guidance |
| `NEEDS_CLARIFICATION` | External blocker | Wait for user (rare) |
| `INVESTIGATION_ONLY` | Questions only, no work | Exit, no development phase |
| `BAZINGA` | All complete | Workflow ends |
