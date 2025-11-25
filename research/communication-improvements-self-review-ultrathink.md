# Communication Improvements Implementation: Critical Self-Review

**Date:** 2025-11-25
**Context:** Self-review of PR #117 changes to orchestration communication
**Decision:** Several issues identified that need fixing
**Status:** Issues Found - Corrections Required

---

## Problem Statement

Review my own implementation for logic errors, contradictions, missing pieces, or broken workflows.

---

## Critical Issues Found

### 🔴 Issue 1: INVESTIGATION_NEEDED Missing from Parsing Lists

**Severity:** HIGH - Could cause routing failures

**Problem:**
- PM can output `INVESTIGATION_NEEDED` (project_manager.md:108)
- Orchestrator routes `INVESTIGATION_NEEDED` correctly (lines 1792, 2262)
- BUT `INVESTIGATION_NEEDED` is NOT in the parsing status lists:
  - orchestrator.md:831 lists: `PLANNING_COMPLETE, BAZINGA, CONTINUE, NEEDS_CLARIFICATION, INVESTIGATION_ONLY`
  - response_parsing.md:319-324 lists same (missing INVESTIGATION_NEEDED)

**Impact:**
- When PM sends `INVESTIGATION_NEEDED`, orchestrator may not recognize it as a valid status
- Could fall through to "infer intent" logic which is less reliable

**Fix Required:**
- Add `INVESTIGATION_NEEDED` to orchestrator.md line 831
- Add `INVESTIGATION_NEEDED` to response_parsing.md line 319-324 with parsing pattern

---

### 🟡 Issue 2: Step 2A.8 Status List Incomplete

**Severity:** MEDIUM - Incomplete but has fallback

**Problem:**
- orchestrator.md line 1694 (PM final check parsing) lists only: `BAZINGA, CONTINUE, NEEDS_CLARIFICATION`
- Missing from this list: `INVESTIGATION_NEEDED`, `PLANNING_COMPLETE`, `INVESTIGATION_ONLY`

**Impact:**
- If PM sends INVESTIGATION_NEEDED during final assessment, it's not in the explicit list
- Relies on "infer intent" fallback (line 1740-1744) which works but is less explicit

**Fix Required:**
- Add `INVESTIGATION_NEEDED` to line 1694

---

### 🟢 Issue 3: Template Format Inconsistency (Minor)

**Severity:** LOW - Cosmetic, not functional

**Problem:**
- response_parsing.md BAZINGA template (lines 389-393) is simpler:
  ```
  ✅ BAZINGA - Orchestration Complete!
  [Show final report]
  ```
- orchestrator.md BAZINGA template (lines 1703-1713) is richer with summary

**Impact:**
- Minor confusion about which template to use
- Both have fallbacks so not critical

**Fix Optional:**
- Align templates or document that orchestrator.md is the authoritative source

---

## Logic Verification (No Issues Found)

### ✅ PLANNING_COMPLETE Flow
- PM outputs `## PM Status: PLANNING_COMPLETE` ✓
- Orchestrator parses PLANNING_COMPLETE (line 831) ✓
- Routes to Step 1.4 (line 912) ✓
- Displays Execution Plan Ready (lines 843-861) ✓

### ✅ Rich Context Block Exceptions
- Exception list (lines 69-74) covers all enhanced templates ✓
- Doesn't conflict with capsule rules ✓

### ✅ PM Database Error Handling
- Retry logic defined (project_manager.md:341-350) ✓
- Temp file fallback whitelisted (line 308, 352-354) ✓
- Doesn't conflict with "NEVER write code files" (code ≠ JSON state) ✓

### ✅ Template Data Sources
- Each template has "Data sources" and "Fallback" ✓
- No hallucination risk for required fields ✓

---

## Recommendations

### Immediate Fixes (Should Do)

1. **Add INVESTIGATION_NEEDED to status parsing lists**
   - orchestrator.md line 831
   - response_parsing.md line 319-324

2. **Add INVESTIGATION_NEEDED to Step 2A.8 parsing**
   - orchestrator.md line 1694

### Optional Improvements

3. **Align BAZINGA template formats** between response_parsing.md and orchestrator.md

4. **Add parsing pattern for INVESTIGATION_NEEDED** in response_parsing.md (how to detect it in PM output)

---

## Verdict

**Overall Assessment:** Implementation is 85% correct. The core communication improvements work, but there's a gap in status code recognition that could cause issues when PM needs to spawn an investigator.

**Risk Level:** Medium - The "infer intent" fallback should catch most cases, but explicit parsing is more reliable.

**Action:** Fix Issue 1 and 2 before considering PR complete.

---

## Lessons Learned

1. When adding a new status code, audit ALL places it needs to be recognized
2. PM's status codes (project_manager.md:108) are the source of truth - orchestrator must handle all of them
3. Self-review with ultrathink catches integration issues that single-file reviews miss
