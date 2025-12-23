# Investigation Workflow

This document describes how the investigation sub-workflow integrates with the main BAZINGA orchestration system.

---

## Where Investigation Fits in the Main Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        MAIN ORCHESTRATION WORKFLOW                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  User Request → PM (Planning) → Developer → QA Expert → Tech Lead          │
│                                                              │              │
│                                                              ▼              │
│                                              ┌──────────────────────────┐   │
│                                              │   Tech Lead Decision     │   │
│                                              └──────────────────────────┘   │
│                                                       │                     │
│                    ┌──────────────────────────────────┼─────────────────┐   │
│                    │                    │             │                 │   │
│                    ▼                    ▼             ▼                 ▼   │
│              APPROVED           CHANGES_REQ    SPAWN_INVESTIGATOR   ESCALATE│
│                 │                    │                │                 │   │
│                 ▼                    ▼                ▼                 │   │
│           Developer             Developer      ┌─────────────┐          │   │
│           (merge)               (fix)          │ INVESTIGATION│          │   │
│                                                │    LOOP      │◄─────────┘   │
│                                                └──────┬──────┘              │
│                                                       │                     │
│                                                       ▼                     │
│                                              Back to Tech Lead              │
│                                              (validate solution)            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Investigation Loop Detail (Multi-Turn)

The investigation loop spans **multiple orchestrator turns**. Each agent spawn terminates the current turn.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         INVESTIGATION LOOP (Max 5 iterations)               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ENTRY: Tech Lead returns SPAWN_INVESTIGATOR                                │
│         with: problem_summary, hypothesis_matrix, suggested_skills          │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │ ORCHESTRATOR TURN 1                                                │     │
│  ├────────────────────────────────────────────────────────────────────┤     │
│  │ Step 1: Initialize investigation_state                             │     │
│  │         Save to DB (state_type="investigation")                    │     │
│  │ Step 2: Check iteration limit (1 of 5)                             │     │
│  │ Step 3: Spawn Investigator (via prompt-builder)                    │     │
│  │         → TERMINATE (await response)                               │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                              │                                              │
│                              ▼                                              │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │ INVESTIGATOR (iteration 1)                                         │     │
│  │ - Analyzes hypothesis matrix                                       │     │
│  │ - Decides next action                                              │     │
│  │ - Returns one of:                                                  │     │
│  │   • ROOT_CAUSE_FOUND (→ exit to TL validation)                     │     │
│  │   • NEED_DEVELOPER_DIAGNOSTIC (→ spawn Developer)                  │     │
│  │   • HYPOTHESIS_ELIMINATED (→ continue loop)                        │     │
│  │   • NEED_MORE_ANALYSIS (→ continue loop)                           │     │
│  │   • BLOCKED (→ exit to PM)                                         │     │
│  │   • EXHAUSTED (→ exit to PM)                                       │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                              │                                              │
│              ┌───────────────┼───────────────┐                              │
│              ▼               ▼               ▼                              │
│    ROOT_CAUSE_FOUND    NEED_DIAGNOSTIC    HYPOTHESIS_ELIMINATED             │
│         │                    │                    │                         │
│         │                    ▼                    │                         │
│         │    ┌───────────────────────────┐        │                         │
│         │    │ ORCHESTRATOR TURN 2       │        │                         │
│         │    │ Step 4b: Capacity check   │        │                         │
│         │    │ Step 4c: Spawn Developer  │        │                         │
│         │    │ → TERMINATE               │        │                         │
│         │    └───────────────────────────┘        │                         │
│         │                    │                    │                         │
│         │                    ▼                    │                         │
│         │    ┌───────────────────────────┐        │                         │
│         │    │ DEVELOPER (diagnostics)   │        │                         │
│         │    │ - Add logging/profiling   │        │                         │
│         │    │ - Run scenario            │        │                         │
│         │    │ - Report results          │        │                         │
│         │    └───────────────────────────┘        │                         │
│         │                    │                    │                         │
│         │                    ▼                    │                         │
│         │    ┌───────────────────────────┐        │                         │
│         │    │ ORCHESTRATOR TURN 3       │        │                         │
│         │    │ Step 4d: Process results  │        │                         │
│         │    │ Step 3: Respawn Investig. │◄───────┘                         │
│         │    │ → TERMINATE               │                                  │
│         │    └───────────────────────────┘                                  │
│         │                    │                                              │
│         │                    ▼                                              │
│         │          (Loop continues...)                                      │
│         │          Max 5 iterations                                         │
│         │                    │                                              │
│         ▼                    ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                        EXIT CONDITIONS                              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Exit Routing

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EXIT ROUTING                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ROOT_CAUSE_FOUND ──────────────────────────────────────────────┐           │
│  INVESTIGATION_INCOMPLETE (max iterations) ─────────────────────┤           │
│                                                                 ▼           │
│                                                    ┌────────────────────┐   │
│                                                    │ Tech Lead          │   │
│                                                    │ (Step 2A.6c)       │   │
│                                                    │ Validates findings │   │
│                                                    └─────────┬──────────┘   │
│                                                              │              │
│                                              ┌───────────────┴────────────┐ │
│                                              ▼                            ▼ │
│                                          APPROVED                CHANGES_REQ│
│                                              │                            │ │
│                                              ▼                            │ │
│                                    ┌─────────────────┐                    │ │
│                                    │ Developer       │                    │ │
│                                    │ (implement fix) │                    │ │
│                                    └─────────────────┘                    │ │
│                                              │                            │ │
│                                              ▼                            │ │
│                                    Back to normal workflow                │ │
│                                    (QA → TL → PM → BAZINGA)               │ │
│                                                                           │ │
│                               ┌───────────────────────────────────────────┘ │
│                               ▼                                             │
│                    Resume investigation with TL feedback                    │
│                    (do NOT reset iteration counter)                         │
│                                                                             │
│                                                                             │
│  BLOCKED ──────────────────────────────────────────────────────┐            │
│  EXHAUSTED ────────────────────────────────────────────────────┤            │
│                                                                ▼            │
│                                                    ┌────────────────────┐   │
│                                                    │ PM                 │   │
│                                                    │ (NEEDS_CLARIF)     │   │
│                                                    │ Decides next step  │   │
│                                                    └─────────┬──────────┘   │
│                                                              │              │
│                                              ┌───────────────┴────────────┐ │
│                                              ▼                            ▼ │
│                                          CONTINUE              NEEDS_CLARIF │
│                                       (with resources)         (simplify)   │
│                                              │                            │ │
│                                              ▼                            ▼ │
│                                    Resume investigation          Ask user   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## State Persistence for Session Resume

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SESSION RESUME HANDLING                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Session ends mid-investigation (e.g., context limit, timeout)              │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Database (via bazinga-db save-state)                                │    │
│  │                                                                     │    │
│  │  investigation_state = {                                            │    │
│  │    session_id: "bazinga_abc123",                                    │    │
│  │    group_id: "A",                                                   │    │
│  │    status: "in_progress",        ← Key field for resume detection   │    │
│  │    current_iteration: 3,         ← Resume from iteration 4          │    │
│  │    hypothesis_matrix: [...],                                        │    │
│  │    iterations_log: [iter1, iter2, iter3],                           │    │
│  │    developer_diagnostic_results: "..." ← Preserve diagnostic data   │    │
│  │  }                                                                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│                              ▼                                              │
│                                                                             │
│  User resumes session                                                       │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Orchestrator Step 0: Check for active investigations               │    │
│  │                                                                     │    │
│  │  bazinga-db, please get state:                                      │    │
│  │  Session ID: {session_id}                                           │    │
│  │  State Type: investigation                                          │    │
│  │                                                                     │    │
│  │  IF state.status == "in_progress":                                  │    │
│  │    → Skip normal workflow                                           │    │
│  │    → Jump to Step 2A.6b (investigation loop)                        │    │
│  │    → Continue from current_iteration + 1                            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Integration Points

| Integration Point | How It Works |
|-------------------|--------------|
| **Entry** | Tech Lead returns `SPAWN_INVESTIGATOR` instead of `CHANGES_REQUESTED` when problem is complex |
| **Agent Spawning** | Uses prompt-builder skill (same as all other agents) |
| **State Storage** | Uses `bazinga-db save-state` with `state_type="investigation"` |
| **Developer Diagnostics** | Spawns Developer with `task_type: "diagnostic"` - does NOT go to QA |
| **Exit to TL** | Routes back to Step 2A.6c (Tech Lead validation) in phase_simple.md |
| **Exit to PM** | Uses existing `NEEDS_CLARIFICATION` status for unblock decisions |
| **Capacity Limit** | Respects MAX 4 developers rule |
| **Escalation** | Uses revision_count for Developer → SSE escalation |

---

## Workflow Router Integration

The investigation loop uses a **hybrid routing approach**:

### Handled by workflow-router (Entry/Exit)

| Agent | Status | Next Agent | Defined In |
|-------|--------|------------|------------|
| Tech Lead | `SPAWN_INVESTIGATOR` | Investigator | transitions.json |
| PM | `INVESTIGATION_NEEDED` | Investigator | transitions.json |
| Developer | `BLOCKED` | Investigator | transitions.json |
| Investigator | `ROOT_CAUSE_FOUND` | Developer | transitions.json |

### Handled by investigation_loop.md (Internal Loop)

These statuses are **NOT** in workflow-router - they're managed by the orchestrator's investigation_loop template:

| Status | Meaning | Handled By |
|--------|---------|------------|
| `NEED_DEVELOPER_DIAGNOSTIC` | Need code instrumentation | investigation_loop.md Step 4b-4c |
| `HYPOTHESIS_ELIMINATED` | Theory disproven | investigation_loop.md → Respawn |
| `NEED_MORE_ANALYSIS` | Deeper analysis needed | investigation_loop.md → Respawn |
| `INVESTIGATION_INCOMPLETE` | Max iterations reached | investigation_loop.md Step 5b |
| `EXHAUSTED` | All hypotheses eliminated | investigation_loop.md Step 5d |

---

## Agent Knowledge Requirements

### Tech Lead Must Know

1. **When to trigger investigation** - Framework 6 criteria (≥2 checked = spawn investigator)
2. **What context to provide** - problem_summary, hypothesis_matrix, suggested_skills
3. **Status code to return** - `SPAWN_INVESTIGATOR`

**Location:** `agents/tech_lead.md` §Framework 6

### Investigator Must Know

1. **Status codes available** - ROOT_CAUSE_FOUND, NEED_DEVELOPER_DIAGNOSTIC, HYPOTHESIS_ELIMINATED, NEED_MORE_ANALYSIS, BLOCKED, EXHAUSTED
2. **Iteration awareness** - Current iteration provided in context, max 5 total
3. **Output format** - JSON response with status and summary

**Location:** `agents/investigator.md` §Status Codes

### Developer Must Know (Diagnostic Mode)

1. **Diagnostic-only tasks** - Add instrumentation, DO NOT fix bug
2. **Branch isolation** - Work on feature branch only
3. **Cleanup required** - Diagnostics must be removed before merge

**Location:** Investigation context in spawn prompt (via prompt-builder)

### PM Must Know (Unblock Mode)

1. **Investigation blocked scenarios** - Receives NEEDS_CLARIFICATION with investigation context
2. **Options available** - Provide resources, simplify task, mark external dependency
3. **Status to return** - CONTINUE (with resources) or NEEDS_CLARIFICATION (simplify)

**Location:** Standard PM workflow handles this via NEEDS_CLARIFICATION

---

## Summary

The investigation loop is a **sub-workflow** that:
1. **Enters** when Tech Lead identifies a complex problem (≥2 investigation criteria)
2. **Runs iteratively** (max 5 iterations) across multiple orchestrator turns
3. **Optionally spawns Developer** for diagnostic instrumentation
4. **Exits** back to Tech Lead for validation or PM for unblock decisions
5. **Persists state** in database for session resume
6. **Follows all existing rules** (prompt-builder, MODEL_CONFIG, capacity limits)

---

## References

- `agents/investigator.md` - Investigator agent definition
- `agents/tech_lead.md` - Tech Lead triggers (Framework 6)
- `templates/orchestrator/phase_simple.md` - Step 2A.6b reference
- `templates/investigation_loop.md` - Full loop procedure (to be created)
- `research/investigation-loop-template-ultrathink.md` - Design analysis

---

## Known Gaps (Fixed)

> **Status:** All gaps fixed in transitions.json v1.1.0 (2025-12-23)
> **Reference:** `research/status-code-mapping-ultrathink.md`

### Gap 1: ROOT_CAUSE_FOUND Routing Mismatch ✅ FIXED

| Source | Route |
|--------|-------|
| `transitions.json` (v1.1.0) | ROOT_CAUSE_FOUND → tech_lead ✅ |
| `phase_simple.md` | ROOT_CAUSE_FOUND → Tech Lead validation ✅ |
| `investigator.md` | "Routing back to Tech Lead for validation" ✅ |

### Gap 2: Status Code Name Mismatches ✅ FIXED

| Investigator Uses | transitions.json (v1.1.0) | Match? |
|-------------------|---------------------------|--------|
| `NEED_DEVELOPER_DIAGNOSTIC` | `NEED_DEVELOPER_DIAGNOSTIC` | ✅ Fixed |
| `INVESTIGATION_INCOMPLETE` | `INVESTIGATION_INCOMPLETE` | ✅ Fixed |
| `HYPOTHESIS_ELIMINATED` | `HYPOTHESIS_ELIMINATED` | ✅ Added |
| `NEED_MORE_ANALYSIS` | `NEED_MORE_ANALYSIS` | ✅ Added |

### Gap 3: Missing investigation_loop.md Template ✅ FIXED

The file `templates/investigation_loop.md` has been created from the ultrathink design.

**Status:** Template created at `templates/investigation_loop.md` (2025-12-23).

### Additional Fixes Applied

| Gap | Description | Status |
|-----|-------------|--------|
| SSE ROOT_CAUSE_FOUND | Added SSE → tech_lead routing | ✅ Fixed |
| SSE PARTIAL | Added respawn routing | ✅ Fixed |
| TL UNBLOCKING_GUIDANCE | Added alias for UNBLOCKING_GUIDANCE_PROVIDED | ✅ Fixed |
| Backward compat aliases | Added `_status_aliases` section | ✅ Added |
