# Spec-Kit Template Extraction Plan: Developer, QA, SSE, and Tech Lead

**Date:** 2025-12-03
**Context:** Extract spec-kit sections from agent files into reusable templates
**Decision:** Flat layout at templates root (integrated from OpenAI review)
**Status:** Implemented
**Reviewed by:** OpenAI GPT-5

---

## Problem Statement

The spec-kit integration sections in agent files are large (~400 lines in developer.md) and duplicated between developer and senior_software_engineer (SSE inherits developer content). This:
1. Bloats agent files unnecessarily
2. Creates synchronization issues when updating spec-kit workflow
3. Makes agent files harder to maintain

**Reference pattern:** PM already extracted spec-kit section to `templates/pm_speckit.md` (~520 lines).

---

## Current State Analysis

### Spec-Kit Content in Each Agent

| Agent | Has Spec-Kit Section? | Lines | Location |
|-------|----------------------|-------|----------|
| **Developer** | YES | ~410 lines | Lines 173-582 |
| **Senior Software Engineer** | YES (inherited) | ~410 lines | Auto-generated from developer.base.md |
| **QA Expert** | NO | N/A | Only workflow references |
| **Tech Lead** | NO | N/A | Only workflow references |

### Key Findings

1. **Only Developer has a substantive spec-kit section.** SSE inherits it via build system.
2. **SSE is auto-generated** from `agents/_sources/developer.base.md` + `agents/_sources/senior.delta.md`
3. **QA and Tech Lead** don't need spec-kit templates - they follow same workflow regardless of mode.

---

## Multi-LLM Review Integration

### Critical Issues Identified (OpenAI GPT-5)

1. **CLI copy_templates doesn't copy subdirectories** ❌
   - Current code: `source_templates.glob("*.md")` - non-recursive
   - Impact: Subfolder `speckit/` would NOT be copied during `bazinga init`
   - **Resolution:** Use flat layout instead of subfolder

2. **SSE is auto-generated** - editing it directly would be overwritten ❌
   - Source: `agents/_sources/developer.base.md`
   - **Resolution:** Edit source file, then rebuild with `./scripts/build-agent-files.sh`

3. **Need fallback if template missing** ❌
   - If template not copied/available, agents lose spec-kit guidance
   - **Resolution:** Keep minimal inline instructions with template reference

### Incorporated Feedback

| Suggestion | Decision | Rationale |
|------------|----------|-----------|
| Flat template at root (no subfolder) | ✅ ADOPTED | Avoids CLI changes, consistent with pm_speckit.md |
| Update developer.base.md, not developer.md | ✅ ADOPTED | Required for build system |
| Add inline fallback with summary | ✅ ADOPTED | Prevents silent regression |
| Add acceptance verification steps | ✅ ADOPTED | Ensures template works end-to-end |

### Rejected Suggestions

| Suggestion | Reason for Rejection |
|------------|---------------------|
| Build-time partial inclusion | Over-engineering for this case; runtime Read pattern already works for PM |
| Create speckit folder anyway + fix CLI | More invasive change; flat layout is simpler |

---

## Final Solution: Flat Layout with Inline Fallback

### File Structure (Final)

```
templates/
├── pm_speckit.md               # Existing PM spec-kit template
├── developer_speckit.md        # NEW - shared by Developer + SSE
├── pm_output_format.md         # Existing
├── ...other templates...
```

**No subfolder.** This matches PM pattern and requires no CLI changes.

### Agent File Changes

#### 1. developer.base.md (SOURCE - must edit this)

**Remove:** Lines containing full spec-kit section (~410 lines)

**Add:** Short reference with inline fallback:

```markdown
## 🆕 SPEC-KIT INTEGRATION MODE

**Activation Trigger**: If PM provides task IDs (e.g., T001, T002) and mentions "SPEC-KIT INTEGRATION ACTIVE"

**REQUIRED:** Read full workflow instructions from: `templates/developer_speckit.md`

### Quick Reference (Fallback if template unavailable)

1. **Read Context**: spec.md (requirements), plan.md (architecture), tasks.md (task list)
2. **Parse Task Format**: `- [ ] [TaskID] [Markers] Description (file.py)`
3. **Implement Following Spec**: Follow plan.md technical approach, meet spec.md criteria
4. **Update tasks.md**: Mark `- [ ]` → `- [x]` as you complete each task
5. **Enhanced Report**: Include task IDs, spec compliance, plan adherence
6. **Checklist**: Read spec → Follow plan → Update tasks.md → Reference task IDs
```

#### 2. senior.delta.md (SOURCE - verify no spec-kit content)

This file contains SSE-specific additions. Verify it doesn't duplicate spec-kit content.
If it does, remove the duplicate since base already has the reference.

#### 3. Run Build Script

```bash
./scripts/build-agent-files.sh
```

This regenerates:
- `agents/developer.md` (copy of developer.base.md)
- `agents/senior_software_engineer.md` (merged base + delta)

---

## Implementation Steps

### Phase 1: Create Template (5 min)

1. Extract spec-kit section from `agents/_sources/developer.base.md` lines 173-582
2. Create `templates/developer_speckit.md` with:
   - Header comment marking it as single source of truth
   - Version date
   - Full spec-kit workflow content

### Phase 2: Update Source File (10 min)

1. Edit `agents/_sources/developer.base.md`:
   - Remove full spec-kit section
   - Add short reference with inline fallback (as shown above)

2. Verify `agents/_sources/senior.delta.md` has no spec-kit duplication

### Phase 3: Rebuild Agent Files (2 min)

```bash
./scripts/build-agent-files.sh
```

Verify output:
- `developer.md` has reference, not full section
- `senior_software_engineer.md` inherits reference

### Phase 4: Verify CLI Copies Template (5 min)

```bash
# Test in clean directory
mkdir /tmp/test-bazinga
cd /tmp/test-bazinga
bazinga init

# Verify template exists
ls -la templates/developer_speckit.md
```

### Phase 5: Acceptance Testing (10 min)

1. **Template exists after init:** Check `templates/developer_speckit.md`
2. **Agent reference works:** Agent file contains reference line
3. **Fallback present:** Agent file has inline quick reference
4. **Build system verified:** Both developer.md and SSE have same reference

---

## Files to Modify

| File | Action |
|------|--------|
| `templates/developer_speckit.md` | **CREATE** - extracted spec-kit content |
| `agents/_sources/developer.base.md` | **MODIFY** - remove section, add reference |
| `agents/_sources/senior.delta.md` | **VERIFY** - no duplicate spec-kit content |
| `agents/developer.md` | **AUTO** - regenerated by build script |
| `agents/senior_software_engineer.md` | **AUTO** - regenerated by build script |

**No changes needed to:**
- `pyproject.toml` - templates already force-included
- `src/bazinga_cli/__init__.py` - flat layout works with existing code

---

## Size Impact

### Before
- `developer.base.md`: ~1634 lines
- `developer.md`: ~1634 lines
- `senior_software_engineer.md`: ~1855 lines

### After
- `developer.base.md`: ~1240 lines (-394 lines)
- `developer.md`: ~1240 lines (-394 lines)
- `senior_software_engineer.md`: ~1460 lines (-395 lines)
- `developer_speckit.md`: ~420 lines (new template)

**Net reduction:** ~770 lines removed from tracked agent files

---

## Risk Assessment

### Mitigated Risks

| Risk | Mitigation |
|------|------------|
| Template not copied | Flat layout ensures existing copy_templates works |
| SSE out of sync | Edit source file, rebuild propagates to both |
| Template missing at runtime | Inline fallback provides basic guidance |
| Build system ignored | CI check with `--check` mode catches drift |

### Remaining Low Risks

- Agent must Read template (same as PM pattern - proven to work)
- Inline fallback is abbreviated (sufficient for basic guidance)

---

## Verification Checklist

Post-implementation verification:

- [ ] `templates/developer_speckit.md` exists with full content
- [ ] `agents/_sources/developer.base.md` has reference, not full section
- [ ] `agents/developer.md` regenerated with reference
- [ ] `agents/senior_software_engineer.md` regenerated with reference
- [ ] `./scripts/build-agent-files.sh --check` passes
- [ ] `bazinga init` in test project copies template
- [ ] Template file size ~420 lines (verify full content extracted)

---

## Summary for User Validation

**Approach:** Flat layout (like pm_speckit.md), edit source file, rebuild agents

**Changes:**
1. Create `templates/developer_speckit.md` (extracted content)
2. Update `agents/_sources/developer.base.md` (remove section, add reference with fallback)
3. Run build script to regenerate agent files
4. No CLI or pyproject.toml changes needed

**Benefits:**
- ~770 lines removed from agent files
- Single source of truth for spec-kit workflow
- Consistent with PM pattern
- No infrastructure changes required

**Decisions Made:**
1. ✅ Flat layout approved (over subfolder) - consistent with pm_speckit.md pattern
2. ✅ 6-step inline fallback is sufficient - balances brevity with essential guidance
3. ✅ Implementation completed - templates extracted, agents updated

---

## References

- PM spec-kit template: `templates/pm_speckit.md`
- Build script: `scripts/build-agent-files.sh`
- Merge script: `scripts/merge_agent_delta.py`
- OpenAI review: `tmp/ultrathink-reviews/openai-review.md`
