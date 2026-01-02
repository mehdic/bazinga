# SpecKit Implementation Critical Review

**Date:** 2026-01-02
**Type:** Ultrathink Self-Review
**Context:** Brutal honest assessment of the SpecKit consolidation implementation
**Status:** IN REVIEW

---

## Executive Summary

**Verdict: INCOMPLETE IMPLEMENTATION** ⚠️

The implementation has fundamental gaps that will cause it to **fail silently** when used. The detection works, but the context is never actually passed to PM. This is a critical oversight.

---

## Critical Issues (Must Fix)

### 🔴 Issue #1: SPECKIT_CONTEXT Never Passed to PM (CRITICAL)

**Severity:** BLOCKER
**Impact:** Feature completely non-functional

**Problem:** Step 0.5e says "Include `SPECKIT_CONTEXT` section in PM spawn with file contents" but:
1. Phase 1 (Step 1.2) doesn't reference any SpecKit context
2. The PM spawn prompt template doesn't include SPECKIT_CONTEXT
3. There's no variable passing between Step 0.5e and Phase 1

**Evidence:**
```markdown
# Step 0.5e says:
5. **Pass to PM in Phase 1:**
   - Include `SPECKIT_CONTEXT` section in PM spawn with file contents

# But Phase 1 (Step 1.2) says:
Build PM prompt by reading `agents/project_manager.md` and including:
- Session ID from Step 0
- Previous PM state from Step 1.1
- User's requirements from conversation
- Task: Analyze requirements, decide mode, create task groups

# No mention of SPECKIT_CONTEXT!
```

**Result:** User says "yes" to SpecKit, orchestrator stores state, but PM never receives the context. PM creates its own task breakdown as usual. **The entire feature is a no-op.**

**Fix Required:**
1. Add explicit SPECKIT_CONTEXT section to PM spawn prompt template
2. Define exact format of SPECKIT_CONTEXT
3. Add conditional logic in Phase 1 to include context when speckit_mode=true

---

### 🔴 Issue #2: Uses `cat` Command (Forbidden)

**Severity:** HIGH
**Impact:** Violates tool usage rules

**Problem:** The implementation uses bash `cat` to read files:
```bash
TASKS_CONTENT=$(cat "$FEATURE_DIR/tasks.md" 2>/dev/null)
```

But `.claude/claude.md` explicitly forbids this:
```
- Avoid using Bash with the `find`, `grep`, `cat`, `head`, `tail`...
  Instead, always prefer using the dedicated tools for these commands:
  - Read files: Use Read (NOT cat/head/tail)
```

**Fix Required:** Use Read tool instead:
```
Read(file_path: "{FEATURE_DIR}/tasks.md")
Read(file_path: "{FEATURE_DIR}/spec.md")
Read(file_path: "{FEATURE_DIR}/plan.md")
```

---

### 🔴 Issue #3: Resume Scenario Not Handled

**Severity:** HIGH
**Impact:** SpecKit mode lost on resume

**Problem:** Step 0.5e says "NEW SESSION ONLY" but doesn't define what happens on resume:
- If session has `speckit_mode: true` in state, should we skip detection and use stored context?
- If we re-detect, we might ask the user again (confusing)
- If we don't check state, we lose SpecKit mode on resume

**Evidence:** Resume path (Path A) jumps to Step 3 → Step 4 → Step 5 (spawn PM). It never checks for stored speckit_mode.

**Fix Required:**
1. In resume path, check session state for `speckit_mode`
2. If true, load `speckit_artifacts` from state
3. Pass to PM as SPECKIT_CONTEXT

---

### 🔴 Issue #4: NEEDS_CLARIFICATION Cap Conflict

**Severity:** MEDIUM-HIGH
**Impact:** PM loses ability to ask questions

**Problem:** The orchestrator has a hard cap of 1 clarification per session:
```markdown
**Exception: NEEDS_CLARIFICATION (Hard Cap = 1 per session)**
- Check database state: `get-state "{session_id}" "orchestrator"`
- If `clarification_used: true` and PM asks again → AUTO-FALLBACK
```

If SpecKit detection uses this clarification slot, PM cannot ask any clarifying questions later.

**Fix Required:**
- SpecKit detection should NOT count as NEEDS_CLARIFICATION
- It's a different type of user interaction (mode selection, not blocking clarification)
- Add separate tracking: `speckit_prompt_shown: true`

---

### 🔴 Issue #5: User Response Parsing Undefined

**Severity:** MEDIUM
**Impact:** Edge cases cause confusion

**Problem:** The implementation says "Wait for user response" but doesn't define:
1. How to detect user response (what triggers continuation?)
2. What counts as "yes"? ("yes", "y", "yeah", "sure", "ok", "Yes", "YES")
3. What counts as "no"? ("no", "n", "nope", "skip", "No")
4. What if user says something else entirely?
5. What if user just provides new requirements without answering?

**Fix Required:**
- Define explicit response patterns
- Define fallback behavior (default to "no" if unclear?)
- Handle the case where user ignores the question

---

### 🔴 Issue #6: PM Step 1.0 Says "Skip to Step 3.5"

**Severity:** MEDIUM
**Impact:** Steps skipped incorrectly

**Problem:** In pm_planning_steps.md, if NO SPECKIT_CONTEXT:
```markdown
### IF NO SPECKIT_CONTEXT

- Proceed with normal planning (create your own task breakdown)
- Skip to Step 3.5
```

But Step 3.5 is "Assign Specializations". What about Steps 1, 2, 3 (Development Plan Management, Backfill Fields, etc.)? These shouldn't be skipped!

**Fix Required:** Change to "Continue with normal planning (Step 0, Step 0.9, etc.)" or remove the skip instruction.

---

### 🟡 Issue #7: Backward Compatibility - No Deprecation Period

**Severity:** MEDIUM
**Impact:** Existing workflows break

**Problem:** We deleted `/bazinga.orchestrate-from-spec.md` without any deprecation notice. Users who have:
- Scripts referencing this command
- Documentation referencing this command
- Muscle memory for this command

Will get errors with no guidance on what to do instead.

**Mitigation Done:** Added to deprecated_commands list in installer, so `bazinga update` will clean up old files.

**Still Missing:**
- Users who haven't run `bazinga update` won't know the command is gone
- No migration guide

---

### 🟡 Issue #8: SpecKit Slash Commands Still Reference Old Templates

**Severity:** MEDIUM
**Impact:** Inconsistent behavior

**Problem:** The `/speckit.*` commands still exist and may reference old patterns:
- `/speckit.implement` - Does this still work without the _speckit templates?
- `/speckit.specify` - Creates spec.md, still fine
- `/speckit.tasks` - Creates tasks.md, still fine
- `/speckit.plan` - Creates plan.md, still fine

**Fix Required:** Audit all /speckit.* commands to ensure they don't reference deleted templates.

---

### 🟡 Issue #9: No Validation of SpecKit Artifact Format

**Severity:** LOW-MEDIUM
**Impact:** Garbage in, garbage out

**Problem:** We detect that `tasks.md` exists, but we don't validate:
1. Is it in SpecKit format? (Could be any random tasks.md)
2. Are task IDs present? ([T001], [T002])
3. Are markers valid? ([P], [US1])
4. Is the format parseable?

**Current behavior:** If tasks.md is malformed, PM will get garbage context and produce unpredictable results.

**Fix Required:** Add format validation:
```bash
# Check for at least one SpecKit task line
grep -q '^\- \[ \] \[T[0-9]' "$FEATURE_DIR/tasks.md"
```

---

### 🟡 Issue #10: Agent Inline Instructions Too Minimal

**Severity:** LOW
**Impact:** Agents may not know what to do

**Problem:** The simplified 5-point inline instructions are minimal:
```markdown
1. **Read Context Files**: spec.md (requirements), plan.md (architecture), tasks.md (task list)
2. **Parse Task Format**: `- [ ] [TaskID] [Markers] Description (file.py)`
3. **Implement Following Spec**: Follow plan.md technical approach, meet spec.md criteria
4. **Update tasks.md**: Mark `- [ ]` → `- [x]` as you complete each task
5. **Enhanced Report**: Include task IDs, spec compliance, plan adherence
```

Compared to the 450+ line `developer_speckit.md` template that included:
- Detailed examples
- Error handling
- Edge cases
- Reporting format

**Risk:** Agents may not have enough context to properly follow SpecKit patterns.

**Mitigation:** The core value (task IDs, checkmarks) is preserved. Advanced features (detailed reporting) are optional.

---

## Decision Tree Analysis

### Happy Path (Works with fixes)
```
User: /bazinga.orchestrate
  ↓
Step 0.5e: Detect .specify/features/*/tasks.md
  ↓ (found)
Ask user: "Use SpecKit?"
  ↓ (user says "yes")
Read artifacts, store in session state
  ↓
Phase 1: PM spawn WITH SPECKIT_CONTEXT
  ↓
PM reads context, creates groups from tasks.md
  ↓
Normal workflow continues
```

### Broken Paths (Currently)

**Path A: Context Lost**
```
User says "yes" → Context stored but never passed to PM → PM ignores SpecKit → FAIL
```

**Path B: Resume**
```
Session resumes → Step 0.5e skipped (NEW SESSION ONLY) → speckit_mode in state ignored → FAIL
```

**Path C: Clarification Cap**
```
SpecKit prompt uses cap → PM needs clarification later → AUTO-FALLBACK instead of asking → FAIL
```

**Path D: Invalid Format**
```
tasks.md exists but not SpecKit format → Garbage passed to PM → Unpredictable results → FAIL
```

---

## Comparison: What Was Promised vs What Was Delivered

| Promised | Delivered | Gap |
|----------|-----------|-----|
| "Ask user, pass to PM" | Ask user | ❌ Pass to PM missing |
| "PM uses pre-planned tasks" | PM doesn't receive tasks | ❌ Not implemented |
| "Inline instructions work" | Instructions exist | ⚠️ May be insufficient |
| "Resume preserves mode" | Resume ignores mode | ❌ Not implemented |
| "Backward compatible" | Command deleted | ⚠️ No deprecation |

---

## Recommended Fixes

### Priority 1: Make It Work (Blockers)

1. **Add SPECKIT_CONTEXT to PM spawn** in Step 1.2:
```markdown
**IF speckit_mode from session state or Step 0.5e:**
Include SPECKIT_CONTEXT section in PM prompt:

## SPECKIT_CONTEXT (Pre-Planned Tasks)

**Feature Directory:** {FEATURE_DIR}

**tasks.md:**
{TASKS_CONTENT from Read tool}

**spec.md:**
{SPEC_CONTENT from Read tool}

**plan.md:**
{PLAN_CONTENT from Read tool}

**Instructions:** Use tasks.md as your task breakdown. See pm_planning_steps.md Step 1.0.
```

2. **Use Read tool instead of cat** in Step 0.5e

3. **Handle resume scenario** - Check session state for speckit_mode before PM spawn

### Priority 2: Polish (Important)

4. **Define user response patterns** - Accept "yes", "y", "yeah", "ok", "sure" as affirmative
5. **Fix PM Step 1.0 skip instruction** - Don't skip to Step 3.5
6. **Separate SpecKit prompt from clarification cap**

### Priority 3: Hardening (Nice to Have)

7. **Validate tasks.md format** before using
8. **Audit /speckit.* commands** for consistency
9. **Add migration guide** for users of old command

---

## Implementation Checklist

- [ ] Add SPECKIT_CONTEXT to PM spawn template (Step 1.2)
- [ ] Replace `cat` with Read tool in Step 0.5e
- [ ] Add speckit_mode check in resume path
- [ ] Define user response parsing (yes/no patterns)
- [ ] Fix PM Step 1.0 skip instruction
- [ ] Separate speckit_prompt_shown from clarification_used
- [ ] Add tasks.md format validation
- [ ] Audit /speckit.* commands
- [ ] Create migration documentation

---

## Conclusion

**The current implementation is incomplete and will fail silently.** The detection works, the user sees the prompt, they say "yes", the context is stored... but PM never receives it. This is a critical oversight that makes the entire feature non-functional.

The fixes are straightforward but essential. Without them, we've deleted 2,500 lines of working code and replaced it with 155 lines of non-working code.

**Recommendation:** Implement Priority 1 fixes before considering this work complete.
