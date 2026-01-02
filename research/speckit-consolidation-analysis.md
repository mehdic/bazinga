# SpecKit Consolidation Analysis: Eliminating orchestrate-from-spec

**Date:** 2026-01-02
**Context:** Analyzing whether to consolidate SpecKit integration into the main orchestrator and eliminate the separate orchestrate-from-spec command
**Decision:** Implemented ultra-minimal approach (ask user, then pass context to PM)
**Status:** COMPLETED
**Reviewed by:** OpenAI GPT-5

---

## Problem Statement

The BAZINGA orchestration system currently has two parallel execution paths:

1. **`/bazinga.orchestrate`** - Standard multi-agent orchestration where PM analyzes requirements and creates task breakdowns
2. **`/bazinga.orchestrate-from-spec`** - SpecKit-aware orchestration that reads pre-planned artifacts (spec.md, tasks.md, plan.md)

This duplication creates:
- **Maintenance burden**: 6+ files (~2000+ lines) to maintain in parallel
- **Feature drift**: Improvements to main orchestrator don't automatically apply to spec-kit mode
- **Cognitive overhead**: Users must choose between two commands
- **Testing complexity**: Two execution paths to validate

**The question:** Can we consolidate the relevant SpecKit functionality directly into the main orchestrator and eliminate the separate command?

---

## Current Architecture

### Files Involved in SpecKit Integration

| File | Lines | Purpose |
|------|-------|---------|
| `.claude/commands/bazinga.orchestrate-from-spec.md` | 640 | Entry point command |
| `agents/orchestrator_speckit.md` | 490 | SpecKit-aware orchestrator agent |
| `templates/pm_speckit.md` | 520 | PM workflow modifications |
| `templates/developer_speckit.md` | 455 | Developer workflow modifications |
| `templates/qa_speckit.md` | 214 | QA validation against spec.md |
| `templates/tech_lead_speckit.md` | 254 | TL review with plan.md compliance |

**Total: ~2,573 lines of SpecKit-specific code**

### What SpecKit Mode Actually Changes

#### 1. PM Behavior Changes

| Standard Mode | SpecKit Mode |
|---------------|--------------|
| PM analyzes requirements | PM reads spec.md for requirements |
| PM creates task breakdown | PM reads tasks.md (already exists) |
| PM decides grouping strategy | PM uses [US] and [P] markers from tasks.md |
| Free-form task descriptions | Structured T001, T002, T003 task IDs |

**Key addition:** Parsing `tasks.md` format:
```
- [ ] [T001] [P] [US1] Description (file.py)
```

#### 2. Developer Behavior Changes

| Standard Mode | SpecKit Mode |
|---------------|--------------|
| Receives PM description | Reads spec.md + plan.md for context |
| Self-defines tasks | Assigned specific task IDs |
| Reports completion | Updates tasks.md with [x] checkmarks |

**Key addition:** After each task, run:
```bash
Edit(old="- [ ] [T002]", new="- [x] [T002]")
```

#### 3. QA Expert Changes

| Standard Mode | SpecKit Mode |
|---------------|--------------|
| Tests implementation | Validates against spec.md acceptance criteria |
| Free-form test strategy | Covers ALL spec.md edge cases |
| Reports pass/fail | Also verifies tasks.md accuracy |

**Key addition:** Cross-reference test coverage with `spec.md` acceptance criteria section.

#### 4. Tech Lead Changes

| Standard Mode | SpecKit Mode |
|---------------|--------------|
| Reviews code quality | Also validates plan.md compliance |
| Subjective architecture review | Architecture defined in plan.md |
| Free-form approval | Must verify tasks.md checkmarks accurate |

**Key addition:** Check code against `plan.md` technical decisions.

---

## Consolidation Options

### Option A: Keep Separate (Status Quo)

**Pros:**
- Clean separation of concerns
- Users explicitly choose mode
- No risk of breaking existing orchestration

**Cons:**
- 2500+ lines of duplicate/parallel code
- Feature drift between modes
- Double maintenance burden
- Two test suites needed

**Verdict:** Suboptimal - high maintenance cost

---

### Option B: Full Consolidation (Single Orchestrator)

**Approach:** Merge all SpecKit logic into `bazinga.orchestrate.md` with auto-detection.

**Auto-detection logic:**
```python
# At initialization, before PM spawn:
if exists(".specify/features/*/tasks.md"):
    SPECKIT_MODE = True
    FEATURE_DIR = detect_latest_feature()
else:
    SPECKIT_MODE = False
```

**Changes to main orchestrator:**
1. Add Step 0.5b: Check for SpecKit artifacts
2. If found, inject SPECKIT_MODE context into PM spawn
3. PM template includes conditional section for SpecKit mode
4. Developer/QA/TL templates include conditional sections

**Estimated impact:**
- Add ~200 lines to main orchestrator (detection + context injection)
- Modify pm_speckit.md to become conditional section in main PM template
- Same for developer, QA, TL templates

**Pros:**
- Single source of truth
- All improvements automatically apply to both modes
- Simplified testing
- Users don't need to choose command

**Cons:**
- Main orchestrator grows larger (already 1300+ lines)
- Risk of regressions during merge
- Conditional logic adds complexity

**Verdict:** Optimal if executed carefully

---

### Option C: Hybrid - Auto-Detection with Modular Templates

**Approach:** Keep templates separate but auto-detect and load them dynamically.

**Changes:**
1. Remove `bazinga.orchestrate-from-spec.md` command
2. Keep `orchestrator_speckit.md` as an extension module
3. Main orchestrator detects SpecKit mode and loads extension
4. Keep separate _speckit.md templates, loaded conditionally

**Detection in main orchestrator:**
```markdown
## Step 0.5c: SpecKit Mode Detection

```bash
test -f .specify/features/*/tasks.md && echo "speckit" || echo "standard"
```

**IF "speckit" detected:**
- Read and apply: `templates/pm_speckit.md` additions to PM context
- Developers receive: standard + `templates/developer_speckit.md` additions
- QA receives: standard + `templates/qa_speckit.md` additions
- TL receives: standard + `templates/tech_lead_speckit.md` additions
```

**Pros:**
- Single entry point (one command)
- Templates stay modular (easier to maintain)
- Clear extension pattern
- Less risk than full merge

**Cons:**
- Still maintaining separate template files
- Dynamic loading adds complexity
- Template concatenation could be error-prone

**Verdict:** Good middle ground

---

### Option D: Minimal Integration (Tasks.md Only)

**Approach:** Only integrate the tasks.md parsing and checkmark updating. Remove all other SpecKit-specific features.

**What's included:**
- Auto-detect `tasks.md` in any location
- Parse task IDs and markers
- Developers update checkmarks
- BAZINGA verification includes tasks.md check

**What's dropped:**
- Feature directory convention (.specify/features/)
- spec.md context injection (PM can read if needed)
- plan.md compliance (TL can check if needed)
- QA spec.md validation
- All SpecKit slash commands

**Estimated changes:**
- ~50 lines added to main orchestrator
- ~100 lines added to developer template
- All _speckit.md files deleted

**Pros:**
- Minimal complexity added
- Keeps core value (task tracking with checkmarks)
- No new cognitive load on users

**Cons:**
- Loses structured context flow (spec → plan → tasks)
- Less traceability
- Users lose QA/TL validation against specs

**Verdict:** Too aggressive - loses valuable features

---

## Recommended Approach: Option C (Hybrid)

### Rationale

1. **Single entry point eliminates confusion** - Users just use `/bazinga.orchestrate`
2. **Modular templates preserve maintainability** - Clear separation of base vs extension
3. **Auto-detection is low-risk** - Simple file existence check
4. **Additive, not invasive** - SpecKit templates ADD to base templates, don't replace

### Implementation Plan

#### Phase 1: Add Auto-Detection to Main Orchestrator

Add to `bazinga.orchestrate.md` after Step 0.5 (Tech Stack Detection):

```markdown
### Step 0.5d: SpecKit Mode Detection

Check for SpecKit artifacts:
```bash
SPECKIT_FEATURE=$(ls -d .specify/features/*/tasks.md 2>/dev/null | head -1)
if [ -n "$SPECKIT_FEATURE" ]; then
    FEATURE_DIR=$(dirname "$SPECKIT_FEATURE")
    echo "speckit:$FEATURE_DIR"
else
    echo "standard"
fi
```

**IF SpecKit mode detected:**
- Set `SPECKIT_MODE=true`
- Set `FEATURE_DIR={detected path}`
- Display: `🔍 SpecKit artifacts detected | Feature: {FEATURE_DIR} | Enhanced context enabled`
```

**Estimated: +30 lines**

#### Phase 2: Conditional Template Loading

Modify prompt-builder skill to accept optional `speckit_mode` and `feature_dir` parameters:

```python
if params.get("speckit_mode"):
    # Load base agent template
    prompt = load_template(f"agents/{agent_type}.md")

    # Append SpecKit extensions if they exist
    speckit_template = f"templates/{agent_type}_speckit.md"
    if os.path.exists(speckit_template):
        prompt += "\n\n---\n\n## SPEC-KIT INTEGRATION MODE\n\n"
        prompt += load_template(speckit_template)

    # Inject feature context
    prompt = prompt.replace("{FEATURE_DIR}", params["feature_dir"])
```

**Estimated: +50 lines to prompt-builder**

#### Phase 3: Update PM Workflow

When spawning PM in SpecKit mode, include:

```markdown
🆕 **SPEC-KIT INTEGRATION MODE ACTIVE**

**Feature Directory**: {FEATURE_DIR}

**Available Artifacts**:
- spec.md: {exists/missing}
- tasks.md: {exists/required}
- plan.md: {exists/missing}

**Your Modified Workflow**: See §SPEC-KIT INTEGRATION MODE section below.
```

**Estimated: +20 lines to PM spawn**

#### Phase 4: Delete Redundant Files

Remove after Phase 1-3 complete:
- `.claude/commands/bazinga.orchestrate-from-spec.md` (640 lines)
- `agents/orchestrator_speckit.md` (490 lines)

**Estimated: -1130 lines removed**

#### Phase 5: Update Documentation

- Update `.claude/claude.md` to remove references to orchestrate-from-spec
- Update any SpecKit workflow docs to use `/bazinga.orchestrate`

### Net Change Summary

| Category | Lines |
|----------|-------|
| Added to orchestrate.md | +30 |
| Added to prompt-builder | +50 |
| Added to PM spawn | +20 |
| Deleted (orchestrate-from-spec.md) | -640 |
| Deleted (orchestrator_speckit.md) | -490 |
| **Net** | **-1030** |

**Result:** ~1000 lines of code removed while maintaining all functionality.

---

## Critical Analysis

### Pros

1. **Reduced maintenance burden** - One orchestrator to maintain instead of two
2. **Automatic feature parity** - All improvements apply to both modes
3. **Simplified UX** - Users just use `/bazinga.orchestrate`, mode auto-detected
4. **Preserved modularity** - SpecKit templates remain separate, easy to update
5. **Net code reduction** - ~1000 lines removed

### Cons

1. **Migration risk** - Must ensure no regressions during transition
2. **Increased prompt-builder complexity** - Now handles template merging
3. **Hidden mode switching** - Users may not realize SpecKit mode is active
4. **Testing burden** - Need to test both modes through single entry point

### Mitigations

| Risk | Mitigation |
|------|------------|
| Regressions | Add integration tests for SpecKit mode before migration |
| Hidden switching | Clear user-facing message when SpecKit detected |
| Template merge bugs | Unit test template concatenation |
| Complexity | Document the conditional flow clearly |

---

## Comparison to Alternatives

| Approach | Code Reduction | Risk | Maintainability | User Experience |
|----------|---------------|------|-----------------|-----------------|
| A: Keep Separate | 0 | Low | Poor | Confusing |
| B: Full Merge | -1500 | High | Good | Simple |
| **C: Hybrid** | **-1030** | **Medium** | **Good** | **Simple** |
| D: Minimal | -2400 | Medium | Good | Loss of features |

---

## Decision Rationale

Option C (Hybrid) is recommended because:

1. **Balance of risk vs reward** - Moderate code reduction with controlled risk
2. **Preserves the value proposition** - SpecKit templates provide real value
3. **Aligns with existing patterns** - prompt-builder already does template composition
4. **Reversible** - Can always re-separate if issues arise

---

## Questions for External Review

1. **Is auto-detection the right approach?** Or should users explicitly enable SpecKit mode?
2. **Should we keep the /speckit.* commands?** They're still useful for the planning phase.
3. **Is the hybrid approach too complex?** Would full merge (Option B) be cleaner?
4. **What testing coverage is needed?** Before vs after migration?
5. **Are there edge cases we're missing?** Multiple feature directories, partial artifacts, etc.

---

## Lessons Learned

- Feature drift between parallel implementations is a real maintenance cost
- Auto-detection can simplify UX but needs clear feedback to users
- Modular templates are easier to maintain than monolithic files
- The 80/20 rule applies: most of SpecKit value comes from tasks.md parsing

---

## References

- `.claude/commands/bazinga.orchestrate-from-spec.md` - Current SpecKit entry point
- `agents/orchestrator_speckit.md` - Current SpecKit orchestrator
- `templates/*_speckit.md` - Agent extension templates
- `.specify/` - SpecKit artifact directory structure

---

## Multi-LLM Review Integration

**Review Date:** 2026-01-02
**Reviewers:** OpenAI GPT-5

### Critical Issues Identified

The external review identified 8 critical issues that must be addressed before implementation:

| # | Issue | Severity | Status |
|---|-------|----------|--------|
| 1 | Validator integration gap | Critical | **Must address** |
| 2 | Concurrency on tasks.md | Critical | **Must address** |
| 3 | Mode persistence missing | High | **Must address** |
| 4 | Prompt-builder token bloat | High | **Adopt alternative** |
| 5 | Multiple-feature ambiguity | Medium | **Must address** |
| 6 | Backward compatibility | Medium | **Must address** |
| 7 | Success criteria capture | High | **Must address** |
| 8 | Branch/source of truth | Medium | **Must address** |

### Incorporated Feedback

#### 1. Validator Must Be Updated (Critical)

**Issue:** Plan adds BAZINGA gate "all tasks.md have [x]" but doesn't update bazinga-validator.

**Incorporated Solution:**
- Update `bazinga-validator` skill to:
  - Accept `speckit_mode` and `feature_dir` from session state
  - Locate and parse tasks.md from canonical branch
  - Cross-check task_ids against DB success criteria
  - Return REJECT if any task not marked complete

**Implementation Note:** Add new validation step to `.claude/skills/bazinga-validator/SKILL.md`:
```python
if session.speckit_mode:
    tasks_complete = validate_tasks_md(session.feature_dir)
    if not tasks_complete:
        return REJECT("tasks.md has unchecked items")
```

#### 2. DB as Source of Truth for Task Completion (Critical)

**Issue:** Multiple developers editing tasks.md creates race conditions and merge conflicts.

**Incorporated Solution:**
- **DB becomes single source of truth** for task completion
- Add `task_progress` table: `{session_id, group_id, task_id, status, updated_by, updated_at}`
- Developers report completion via handoff JSON, orchestrator writes to DB
- PM/orchestrator updates tasks.md as a **single atomic operation** at phase boundaries
- Validator reads from DB, optionally verifies tasks.md mirrors DB (warning, not hard fail)

**Implementation Note:** Add to bazinga-db schema:
```sql
CREATE TABLE IF NOT EXISTS task_progress (
    session_id TEXT,
    group_id TEXT,
    task_id TEXT,
    status TEXT DEFAULT 'open',  -- open, done
    updated_by TEXT,
    updated_at TEXT,
    PRIMARY KEY (session_id, group_id, task_id)
);
```

#### 3. Mode Persistence in Session State (High)

**Issue:** Auto-detection at init but no persistence prevents mode flip mid-session.

**Incorporated Solution:**
- Detect SpecKit mode **once** at session creation
- Store in session state: `speckit_mode: boolean`, `feature_dir: string`, `speckit_artifacts: {spec, plan, tasks}`
- All subsequent operations read from session state, not re-detect
- No mode switching allowed mid-session

**Implementation Note:** Update session creation in bazinga-db-core:
```json
{
  "speckit_mode": true,
  "feature_dir": ".specify/features/001-jwt-auth/",
  "speckit_artifacts": {
    "spec_md": ".specify/features/001-jwt-auth/spec.md",
    "plan_md": ".specify/features/001-jwt-auth/plan.md",
    "tasks_md": ".specify/features/001-jwt-auth/tasks.md"
  }
}
```

#### 4. File-Reference Over Prompt Concatenation (High)

**Issue:** Merging SpecKit templates into prompts risks token overflow and content duplication.

**Adopted Alternative:**
- **DO NOT** concatenate templates in prompt-builder
- Instead, pass `"SPEC-KIT INTEGRATION ACTIVE"` flag + `FEATURE_DIR` in spawn params
- Agents already have sections to read templates by path (this is the existing pattern)
- Let agents load SpecKit context files themselves
- This keeps prompts small and respects existing guidance

**Rejected Original Approach:** The original plan to have prompt-builder merge templates is abandoned in favor of the file-reference pattern that already works.

#### 5. Explicit Feature Selection (Medium)

**Issue:** Auto-selecting "latest feature" when multiple exist is unsafe.

**Incorporated Solution:**
- If multiple `.specify/features/*/tasks.md` exist:
  - Deterministic selection: highest numeric prefix (e.g., 005 > 004)
  - Log the selection: `🔍 Multiple features found | Selected: {FEATURE_DIR} (highest prefix)`
  - Allow explicit override: user can specify `FEATURE_DIR=.specify/features/002-auth` in request
- Pin selected `feature_dir` in session state (see #3)

**Implementation Note:** Add to orchestrator detection:
```bash
# Select highest-numbered feature (deterministic)
FEATURE_DIR=$(ls -d .specify/features/*/tasks.md 2>/dev/null | sort -V | tail -1 | xargs dirname)
```

#### 6. Deprecation Path for /orchestrate-from-spec (Medium)

**Issue:** Removing command without deprecation breaks existing workflows.

**Incorporated Solution:**
- **Keep `/bazinga.orchestrate-from-spec` as thin alias** for 2 releases
- Alias emits deprecation warning and calls main orchestrator with `speckit_mode=true`
- Update docs to recommend `/bazinga.orchestrate`
- Remove alias and `orchestrator_speckit.md` after deprecation period

**Implementation Note:** Modify orchestrate-from-spec.md:
```markdown
⚠️ **DEPRECATION NOTICE**: This command will be removed in a future release.
Use `/bazinga.orchestrate` instead - SpecKit mode is auto-detected.

[Thin wrapper that invokes main orchestrator with speckit_mode=true]
```

#### 7. Success Criteria Capture (High)

**Issue:** No plan to write success criteria (from tasks.md) to DB for validator.

**Incorporated Solution:**
- At planning phase, PM extracts success criteria from tasks.md:
  - "All N task_ids completed" (list task IDs explicitly)
  - "All groups APPROVED by Tech Lead"
  - Testing mode conditions
- PM calls `save-success-criteria` with explicit task list
- Validator reads these criteria and enforces them

**Implementation Note:** PM must call bazinga-db-workflow:
```json
{
  "criteria": [
    {"type": "tasks_complete", "task_ids": ["T001", "T002", "T003"]},
    {"type": "groups_approved", "groups": ["US1", "US2"]},
    {"type": "testing_mode", "mode": "full"}
  ]
}
```

#### 8. Branch Discipline (Medium)

**Issue:** PM/validator steps grep tasks.md but don't define which branch.

**Incorporated Solution:**
- Define `validation_branch` in PM state (e.g., integration branch or main)
- Developers push to feature branches; PM merges to validation_branch for QA/TL
- Validator always reads tasks.md from `validation_branch`
- Document this clearly in orchestrator and PM templates

**Implementation Note:** Add to PM state:
```json
{
  "validation_branch": "main",
  "developer_branches": ["feature/group-us1", "feature/group-us2"]
}
```

### Rejected Suggestions (With Reasoning)

| Suggestion | Reason for Rejection |
|------------|---------------------|
| "Context package registration for SpecKit artifacts" | Over-engineering for v1; agents can read files directly. Consider for v2. |
| "One session per feature enforcement" | Too restrictive; current single-feature-at-a-time is pragmatic default. Document limitation instead. |
| "CI impact analysis" | Out of scope for this consolidation. CI is user-configured. Document that tasks.md updates create PR noise. |

### Revised Implementation Plan

Based on review feedback, the implementation plan is revised:

#### Phase 0: Pre-Migration (NEW)

1. **Add `task_progress` table to DB schema**
2. **Update bazinga-validator** to:
   - Accept SpecKit mode from session
   - Read task completion from DB
   - Optionally verify tasks.md mirrors DB
3. **Add integration tests** for SpecKit mode through main orchestrator
4. **Test: multi-feature selection, partial artifacts, validator rejection**

#### Phase 1: Auto-Detection + Session Persistence

1. Add detection to `bazinga.orchestrate.md` after Step 0.5
2. Store `speckit_mode`, `feature_dir`, `speckit_artifacts` in session state
3. Display clear message when SpecKit detected
4. Handle multi-feature selection (highest prefix, allow override)

#### Phase 2: Agent Spawning with File-Reference

1. Pass `SPEC-KIT INTEGRATION ACTIVE` flag + `FEATURE_DIR` to agents
2. **DO NOT** concatenate templates in prompt-builder
3. Agents read SpecKit templates themselves (existing pattern)
4. Track task completion in DB, not just tasks.md

#### Phase 3: Deprecation Alias

1. Convert `/bazinga.orchestrate-from-spec` to thin alias
2. Add deprecation warning
3. Update docs

#### Phase 4: Cleanup (After Deprecation Period)

1. Remove `/bazinga.orchestrate-from-spec.md`
2. Remove `agents/orchestrator_speckit.md`
3. Keep `templates/*_speckit.md` (still used by agents)

### Overall Assessment

The external review validated that **Option C (Hybrid)** is the right approach but identified critical gaps in the original plan. The key insight is:

> **"DB as source of truth for task completion with tasks.md as mirror"** solves the concurrency problem while preserving the human-readable checkmark format.

With the incorporated changes, confidence level is **medium-high** for a safe migration.

### Next Steps (Pending User Approval)

1. Implement Phase 0 (DB schema, validator update, tests)
2. Implement Phase 1-3 incrementally
3. Monitor for regressions
4. Complete Phase 4 after deprecation period

---

## Final Implementation: Ultra-Minimal Approach

**Date Implemented:** 2026-01-02
**Status:** COMPLETED

After reviewing the complex hybrid approach, we chose a simpler solution: **Just ask the user**.

### What Was Implemented

1. **Detection + User Prompt in Orchestrator** (Step 0.5e)
   - Check for `.specify/features/*/tasks.md`
   - If found, list available features and ask user: "Would you like to use these?"
   - Wait for user response (yes/no)
   - If yes → read artifacts, pass to PM
   - If no → normal orchestration

2. **Pre-Planned Context Handling in PM** (Step 1.0 in pm_planning_steps.md)
   - If PM receives `SPECKIT_CONTEXT` section, use tasks.md as task breakdown
   - Parse task IDs and markers ([T001], [P], [US1])
   - Group by [US] markers
   - Use spec.md for requirements, plan.md for technical approach

3. **Simplified Agent References**
   - Developer, SSE, QA, Tech Lead: Inline 5-point reference instead of external template
   - Activation trigger: SPECKIT_CONTEXT section in spawn context

### What Was Deleted

| File | Lines | Status |
|------|-------|--------|
| `.claude/commands/bazinga.orchestrate-from-spec.md` | 640 | ✅ Deleted |
| `agents/orchestrator_speckit.md` | 490 | ✅ Deleted |
| `templates/pm_speckit.md` | 520 | ✅ Deleted |
| `templates/developer_speckit.md` | 455 | ✅ Deleted |
| `templates/qa_speckit.md` | 214 | ✅ Deleted |
| `templates/tech_lead_speckit.md` | 254 | ✅ Deleted |
| **Total Deleted** | **~2,573** | |

### Net Changes

| Category | Lines |
|----------|-------|
| Added to orchestrator.md | +90 |
| Added to pm_planning_steps.md | +65 |
| Simplified agent SpecKit sections | -30 |
| Deleted SpecKit files | -2,573 |
| **Net** | **~-2,450** |

### Why This Approach

1. **User is in control** - No auto-magic, no hidden behavior
2. **No mode persistence needed** - User decides each time
3. **No multi-feature ambiguity** - User picks explicitly
4. **No validator changes needed** - Standard workflow applies
5. **No DB changes needed** - Existing task groups work fine
6. **Minimal code** - ~155 lines added vs 2,573 deleted

### What's Preserved

- All `/speckit.*` planning commands (specify, plan, tasks, etc.)
- The `.specify/features/` directory structure
- Task ID format ([T001], [T002])
- Marker format ([P], [US1])
- Checkmark tracking in tasks.md
- Context flow: spec.md → plan.md → tasks.md

### Trade-offs

| Kept | Dropped |
|------|---------|
| User-driven activation | Auto-detection |
| Inline agent instructions | External template files |
| Standard orchestration flow | Parallel SpecKit orchestrator |
| tasks.md checkmarks (manual) | Enforced checkmark updates |

### Conclusion

The ultra-minimal approach delivers 95% of the SpecKit value with 5% of the complexity. The key insight: **"Just ask the user"** eliminates most edge cases and complexity around auto-detection, mode switching, and feature selection.
