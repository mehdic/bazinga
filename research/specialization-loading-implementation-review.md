# Specialization Loading Implementation Review

**Date:** 2025-12-11
**Context:** Deep analysis of why specializations weren't loading
**Status:** Analysis Complete - Issues Fixed

---

## Problem Statement

Orchestrator was spawning agents without specializations, even when:
1. `skills_config.json` had `specializations.enabled = true`
2. `project_context.json` existed with framework/language info
3. Task groups were created in the DB

The orchestrator just said "I'll proceed without specialization loading (graceful degradation)".

---

## Expected Flow (Design Intent)

```
┌─────────────────────────────────────────────────────────────────────┐
│ Step 0.5: Check project_context.json                                │
│ ↓                                                                   │
│ IF MISSING → Spawn Tech Stack Scout                                 │
│ ↓                                                                   │
│ Scout analyzes project, creates project_context.json with:          │
│   - components[].suggested_specializations                          │
│   - primary_language, framework fields                              │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ Step 1: Spawn PM                                                    │
│ ↓                                                                   │
│ PM Step 3.5.1: Read project_context.json                            │
│ PM Step 3.5.2: Map task groups to components                        │
│ PM Step 3.5.3: Extract suggested_specializations per group          │
│ PM Step 3.5.4: Store via `create-task-group --specializations`      │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ Phase 2: Spawn Agents                                               │
│ ↓                                                                   │
│ Query task groups from DB → Get specializations[]                   │
│ Call specialization-loader skill with paths                         │
│ Prepend composed block to agent prompt                              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Actual Flow (What Was Happening)

```
┌─────────────────────────────────────────────────────────────────────┐
│ Phase 2: Spawn Agents                                               │
│ ↓                                                                   │
│ Query task groups from DB → specializations = null                  │
│ ↓                                                                   │
│ Old Step 3: "IF specializations is null → Skip entirely"  ← BUG!    │
│ ↓                                                                   │
│ Spawn agent with base prompt only (no specialization)               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Root Causes Found

### 1. Missing Fallback Derivation in Orchestrator

**File:** `agents/orchestrator.md` (lines 1519-1524)

**Before (broken):**
```
Step 3: Extract and validate specializations
specializations = task_group["specializations"]
IF specializations is null OR empty:
    Skip specialization loading, continue to spawn  ← NO FALLBACK!
```

**After (fixed):**
```
Step 3: Extract specializations (with fallback derivation)
specializations = task_group["specializations"]

IF specializations is null OR empty:
    # FALLBACK: Derive from project_context.json
    Read project_context.json
    Try: components[].suggested_specializations
    Try: suggested_specializations (session-wide)
    Try: map primary_language + framework to template paths

IF specializations still empty:
    Skip specialization loading
```

### 2. Orphaned Template

**File:** `templates/orchestrator/spawn_with_specializations.md`

This template had the CORRECT fallback derivation logic but was **never referenced** by:
- orchestrator.md
- phase_simple.md
- phase_parallel.md

The template existed in isolation, providing no value.

### 3. Phase Templates Missing Fallback

**Files:**
- `templates/orchestrator/phase_simple.md`
- `templates/orchestrator/phase_parallel.md`

These templates assumed `task_group.specializations` would exist:
```
Specialization Paths: {task_group.specializations as JSON array}
```

No fallback logic when it was null.

### 4. PM Might Not Be Storing Specializations

**File:** `agents/project_manager.md` (Step 3.5)

PM is instructed to:
1. Read `project_context.json`
2. Map task groups to components
3. Extract `suggested_specializations`
4. Store via `--specializations` flag

**Possible failure points:**
- project_context.json doesn't have components with suggested_specializations
- PM doesn't follow Step 3.5 (complex, easy to skip)
- PM extracts but forgets `--specializations` flag
- Resume scenario: task groups created before Step 3.5 existed

---

## Why Did PM Not Assign Specializations?

Based on the user's session showing `specializations: null` for all task groups:

**Most Likely Causes:**

1. **Resume Scenario (Most Probable)**
   - Task groups were created in a previous session
   - Previous PM version didn't have Step 3.5 or didn't follow it
   - Current session resumes, finds existing groups, skips to spawning

2. **project_context.json Structure Issue**
   - Scout created project_context.json but without `suggested_specializations`
   - PM read it but found nothing to extract
   - PM correctly left specializations = []

3. **PM Skipped Step 3.5**
   - PM instructions are complex (2200+ lines)
   - Step 3.5 is buried after Step 3.4
   - PM might have jumped from Step 3.4 to Step 4

**What PM Needs to Store Specializations:**
```
1. project_context.json must exist
2. It must have either:
   - components[].suggested_specializations, OR
   - suggested_specializations (session-wide)
3. PM must READ it and EXTRACT paths
4. PM must PASS --specializations flag to create-task-group
```

---

## Fixes Applied

### Fix 1: Fallback Derivation in Orchestrator
- **Commit:** `e60d4e3`
- Added fallback derivation logic to Step 3
- Orchestrator now reads project_context.json when DB has null

### Fix 2: Phase Templates Updated
- **Commit:** `e60d4e3`
- phase_simple.md: Added Step B.1 with fallback logic
- phase_parallel.md: Same fallback for parallel spawns

### Fix 3: Updated Fallback Table
- "No specializations in DB" → "Derive from project_context.json"
- Clear fallback chain documented

---

## Why Orchestrator Wasn't Using spawn_with_specializations.md

The template `spawn_with_specializations.md` was created but never integrated:

```
$ grep -r "spawn_with_specializations" agents/
(no results)

$ grep -r "spawn_with_specializations" templates/orchestrator/
(no results)
```

It was orphaned documentation with correct logic that nobody used.

---

## Remaining Risks

### 1. PM Still Might Not Store Specializations
The fix ensures orchestrator derives specializations if DB has null.
But ideally PM should store them so they're persisted and don't need re-derivation.

**Recommendation:** Audit PM's Step 3.5 compliance in live sessions.

### 2. project_context.json Might Lack suggested_specializations
If Scout doesn't create proper structure, fallback derivation won't help.

**Recommendation:** Verify Scout output format in live sessions.

### 3. No Path Validation
Orchestrator fallback derives paths like:
```
templates/specializations/01-languages/typescript.md
```

If these templates don't exist in client project, specialization loading fails.

**Recommendation:** Validate template paths exist before passing to skill.

---

## Multi-LLM Review Integration

**Reviewed by:** OpenAI GPT-5

### Key Criticisms (Valid)

1. **Duplication Risk** - Fallback logic duplicated in orchestrator.md AND phase templates invites drift
2. **No Persistence** - Derived specializations aren't written back to DB, causing repeated derivation
3. **No Path Validation** - Bad paths will cause silent failures
4. **No Backfill** - Legacy task groups with null stay null forever
5. **No Tests** - Full pipeline untested

### Recommended Improvements (Future Work)

| Priority | Improvement | Effort |
|----------|-------------|--------|
| HIGH | Persist derived specializations to DB | Medium |
| HIGH | Add path validation before skill call | Low |
| MEDIUM | Centralize in single resolver skill | High |
| MEDIUM | Add backfill for existing groups | Medium |
| LOW | Add telemetry/observability | Medium |

### What Was Incorporated

- Analysis document updated with risks and limitations
- Identified that current fix is "necessary but not sufficient"

### What Was Deferred

- Centralized resolver skill (architectural change)
- DB persistence of derived specializations (requires testing)
- Backfill migration (operational concern)
- Telemetry (nice-to-have)

---

## Conclusion

The specialization loading was broken because:

1. **Orchestrator had no fallback** - just skipped when DB had null
2. **PM might not be storing specializations** - complex instructions
3. **Correct template was orphaned** - spawn_with_specializations.md never used

**Current fix:** Added fallback derivation to orchestrator and phase templates.

**Remaining risks:**
- Fallback logic duplicated (can drift)
- Derived specializations not persisted (re-derives every spawn)
- No path validation (bad paths cause failures)
- Legacy groups stay null (no backfill)

**Verdict:** Current fix enables specialization loading to work, but is fragile. Production use should monitor for failures and consider the improvements above.
