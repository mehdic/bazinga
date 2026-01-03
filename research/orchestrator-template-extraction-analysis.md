# Orchestrator Template Extraction: Critical Analysis

**Date:** 2026-01-03
**Context:** Extracted 3 large sections from orchestrator.md to reduce token size
**Decision:** Template extraction with stub references
**Status:** Proposed (Pending Review)
**Reviewed by:** (Pending OpenAI GPT-5, Google Gemini 3 Pro Preview)

---

## What Was Implemented

Extracted 3 sections from `agents/orchestrator.md` (2,951 → 1,885 lines, -36%):

| Template | Lines | Content |
|----------|-------|---------|
| `pm_spawn_workflow.md` | 442 | PM understanding capture, decision parsing, clarification workflow |
| `resume_workflow.md` | 358 | Scope preservation, new session creation (steps 1-8) |
| `workflow_routing_reference.md` | 359 | Workflow router usage, progress tracking, escalation |

Each extracted section replaced with stub reference:
```markdown
**🔴 MANDATORY: Read [template] before proceeding:**
```
Read(file_path: "templates/orchestrator/[template].md")
```
```

---

## Critical Analysis

### 1. PATH PREFIX BUG (CRITICAL - BREAKING)

**Status:** 🔴 BREAKING IN INSTALLED MODE

The stub references use:
```
Read(file_path: "templates/orchestrator/pm_spawn_workflow.md")
```

But per project conventions (`.claude/claude.md`), the correct path is:
```
Read(file_path: "bazinga/templates/orchestrator/pm_spawn_workflow.md")
```

**Why this matters:**
- In **dev mode**: `templates/` exists at repo root ✅
- In **installed mode**: Only `bazinga/templates/` exists ❌

**Evidence from existing templates:**
```bash
grep -r "Read(file_path:" agents/orchestrator.md | head -5
```
Shows existing references use `bazinga/templates/...` prefix.

**Impact:**
- All 3 stub references will FAIL in installed mode
- Orchestrator will be BROKEN for all client projects after `bazinga install`

**Fix Required:** Change all stub paths from `templates/...` to `bazinga/templates/...`

---

### 2. TOKEN BUDGET PARADOX (MEDIUM)

**Observation:** The extraction may not actually reduce runtime token usage.

**Before:**
- orchestrator.md: 2,951 lines loaded once

**After (worst case):**
- orchestrator.md: 1,885 lines
- + pm_spawn_workflow.md: 442 lines
- + resume_workflow.md: 358 lines
- + workflow_routing_reference.md: 359 lines
- **Total: 3,044 lines** (3% MORE than before!)

**Mitigating factors:**
1. Templates read on-demand, not all at once
2. Some templates mutually exclusive (resume OR new session, not both)
3. Context window can evict templates after processing
4. LLM summarization compresses older content

**Verdict:** Acceptable trade-off. On-demand loading is better than monolithic upfront load.

---

### 3. MISSING RUNTIME VALIDATION (MEDIUM)

**What wasn't tested:**
- [ ] Template files readable from orchestrator context
- [ ] Instructions in templates complete and self-contained
- [ ] Path resolution works in both dev/installed modes
- [ ] No dangling references to content that stayed in orchestrator.md

**Risk:** Silent failures where orchestrator can't find templates.

**Recommended test:**
```bash
# Verify template paths resolve
for f in templates/orchestrator/{pm_spawn_workflow,resume_workflow,workflow_routing_reference}.md; do
  test -f "$f" && echo "✅ $f" || echo "❌ $f MISSING"
done
```

---

### 4. CONTENT COMPLETENESS AUDIT (LOW-MEDIUM)

Need to verify extracted content is self-contained:

**pm_spawn_workflow.md should contain:**
- [ ] MANDATORY FIRST ACTION section
- [ ] PM understanding capture requirements
- [ ] Step 1.3: Receive PM Decision
- [ ] Step 1.3a: Handle PM Status (all 4 status codes)
- [ ] Clarification workflow (NEEDS_CLARIFICATION)
- [ ] Step 1.4: Verify PM State
- [ ] Step 1.5: Route Based on Mode

**resume_workflow.md should contain:**
- [ ] SCOPE PRESERVATION section (code block format)
- [ ] Path B: CREATE NEW SESSION
- [ ] Steps 1-8 for session initialization
- [ ] Capability discovery logic
- [ ] Build baseline check
- [ ] Template loading (3 required templates)
- [ ] Initialization verification checkpoint

**workflow_routing_reference.md should contain:**
- [ ] When to use workflow-router
- [ ] Invocation format
- [ ] Response format parsing
- [ ] Progress-based iteration tracking (Steps 0-5)
- [ ] Re-rejection prevention logic
- [ ] Escalation rules
- [ ] Fallback handling

---

### 5. DECISION TREE ANALYSIS (MEDIUM)

**Question:** Are there any code paths that need content from BOTH the stub location AND the extracted template?

**Analysis:**

The orchestrator flow is:
1. Phase 0 (Session Detection) → reads stub for resume/new session
2. Phase 1 (PM Spawn) → reads stub for PM workflow
3. Phase 2+ (Agent Spawns) → reads routing reference

Each phase is sequential, so template reads are naturally serialized. No overlapping content needed.

**However:** The PM spawn workflow stub appears at line ~1731 in orchestrator.md, but the context BEFORE it (lines 1-1730) contains setup instructions. Does pm_spawn_workflow.md assume that context exists?

**Risk:** Template instructions may assume prior orchestrator context was read, creating implicit dependencies.

**Mitigation:** Templates should be self-contained with explicit context requirements at the top.

---

### 6. BACKWARD COMPATIBILITY (MEDIUM)

**Existing sessions (started before this change):**
- ✅ No impact - they already loaded full orchestrator.md
- ✅ Database schema unchanged
- ✅ Handoff file formats unchanged

**New sessions (started after this change):**
- ⚠️ Must be able to read new templates
- ⚠️ Path resolution must work (see Issue #1)

**Installed clients (after `bazinga update`):**
- ❌ Will get new orchestrator.md with stub references
- ❌ Will get new templates in `bazinga/templates/orchestrator/`
- ❌ BUT stub paths say `templates/...` which won't resolve

---

### 7. INSTALLER VERIFICATION (CRITICAL)

**Question:** Are the new templates included in `bazinga install`?

Per `.claude/claude.md`:
> `templates/` → force-include

The templates directory is configured in pyproject.toml. Need to verify:
```bash
grep -A5 "templates" pyproject.toml | grep -i force
```

**If templates NOT in force-include:** New templates won't be installed to clients, causing orchestrator to fail.

---

### 8. CROSS-REFERENCE CHECK (LOW)

**Do other files reference the extracted sections?**

Files to check:
- `templates/orchestrator/phase_simple.md`
- `templates/orchestrator/phase_parallel.md`
- `.claude/commands/bazinga.orchestrate.md`

If these files reference line numbers or section headers that moved, they may be broken.

---

## Pros and Cons

### Pros ✅

1. **36% line reduction** in main orchestrator file
2. **Improved modularity** - each workflow is self-contained
3. **Easier maintenance** - can update templates independently
4. **On-demand loading** - only read what's needed for current phase
5. **Consistent with existing pattern** - phase_simple/parallel already work this way

### Cons ⚠️

1. **Path bug** - Wrong prefix will break installed mode
2. **More files to track** - 4 files instead of 1
3. **Implicit dependencies** - Templates assume prior context
4. **No runtime validation** - Untested in actual orchestration
5. **Potential installer gap** - Need to verify templates are packaged

---

## Verdict

**Implementation Status:** ⚠️ INCOMPLETE - CRITICAL BUG EXISTS

The extraction logic is sound, but the implementation has a **critical path prefix bug** that will break orchestrator in installed mode.

**Required fixes before merge:**
1. Change all 3 stub paths from `templates/...` to `bazinga/templates/...`
2. Verify templates are included in installer
3. Add runtime test for template resolution

**Risk Level:** HIGH if unfixed, LOW after fixes

---

## Recommended Fixes

### Fix 1: Path Prefix Correction
```bash
# In agents/orchestrator.md, change:
Read(file_path: "templates/orchestrator/pm_spawn_workflow.md")
# To:
Read(file_path: "bazinga/templates/orchestrator/pm_spawn_workflow.md")
```

### Fix 2: Installer Verification
```bash
# Verify templates in pyproject.toml
grep -B2 -A2 "templates" pyproject.toml
```

### Fix 3: Runtime Test
Add to integration test:
```bash
# Verify template resolution
for template in pm_spawn_workflow resume_workflow workflow_routing_reference; do
  test -f "bazinga/templates/orchestrator/${template}.md" || echo "MISSING: ${template}"
done
```

---

## Multi-LLM Review Integration

**Reviewed by:** OpenAI GPT-5
**Date:** 2026-01-03

### Consensus Points

1. **Path prefix bug is critical** - Must fix before merge
2. **No runtime validation exists** - Silent failures possible
3. **Version compatibility gap** - Templates and skills could drift

### Incorporated Feedback

| Suggestion | Status | Implementation |
|------------|--------|----------------|
| Fix all paths to `bazinga/templates/...` | ✅ MUST FIX | Edit orchestrator.md stub references |
| Add CI check for Read paths | ✅ ADOPT | Add pytest to verify all Read targets exist |
| Audit nested references | ✅ VERIFIED | Nested refs already use correct `bazinga/templates/...` |
| Add template version markers | ✅ ADOPT | Add frontmatter with version to each template |
| Update packaging manifest | ✅ VERIFY | Confirm templates in pyproject.toml |

### Rejected Suggestions (With Reasoning)

| Suggestion | Reason for Rejection |
|------------|---------------------|
| **Skill-based template retrieval** | Over-engineering for current scope. Read(file_path) is sufficient and follows existing patterns (phase_simple.md, phase_parallel.md). Adding a new skill increases complexity without proportional benefit. |
| **Session-level caching** | Not needed. Templates are read on-demand per phase, and LLM context management already handles deduplication. Adding state tracking for "templates_loaded" adds complexity. |
| **Move progress tracking to workflow-router** | Would require significant refactoring of workflow-router skill. Current template approach is functional and matches established patterns. Future consideration. |
| **Fallback if template fails** | Orchestrator correctly fails-fast on missing templates. Silent fallback would mask configuration errors and cause harder-to-debug issues. |
| **"Duplicate orchestrator" claim** | CLARIFICATION: There is ONE orchestrator file. The reviewer misinterpreted mixed paths within the same file as "duplicates". No file duplication exists. |

### Additional Issues Discovered in Review

1. **Nested references verified OK**: Templates I created use correct `bazinga/templates/...` paths internally
2. **OpenAI overestimated scope**: Suggested architectural changes beyond scope of this extraction

---

## Issues Summary (Post-Review)

| Issue | Severity | Status | Fix Required |
|-------|----------|--------|--------------|
| Wrong path prefix in stubs | 🔴 CRITICAL | CONFIRMED | Yes - 3 lines to change |
| No CI check for Read paths | 🟡 MEDIUM | NEW | Yes - add pytest |
| No template versioning | 🟡 MEDIUM | NEW | Yes - add frontmatter |
| Installer verification | 🟢 LOW | VERIFIED | Templates already in force-include |
| Token overhead | 🟢 LOW | ACCEPTABLE | On-demand loading is fine |

---

## Recommended Action Plan

### Phase 1: Critical Fix (MUST DO BEFORE MERGE)

```bash
# Fix the 3 stub references in orchestrator.md
sed -i 's|Read(file_path: "templates/orchestrator/|Read(file_path: "bazinga/templates/orchestrator/|g' agents/orchestrator.md
```

### Phase 2: Validation (SHOULD DO)

1. Add pytest test verifying all `Read(file_path:` targets exist:
```python
# tests/test_template_paths.py
def test_orchestrator_read_paths_exist():
    """Verify all Read(file_path: ...) targets in orchestrator exist."""
    orchestrator = Path("agents/orchestrator.md").read_text()
    pattern = r'Read\(file_path:\s*"([^"]+)"\)'
    for match in re.finditer(pattern, orchestrator):
        path = match.group(1)
        assert Path(path).exists(), f"Missing: {path}"
```

2. Add version markers to templates (optional, future improvement)

### Phase 3: Documentation

Update commit message to note the path fix was required post-review.

---

## References

- Commit: 14f4c94 "Extract large sections from orchestrator.md into templates"
- Files modified: `agents/orchestrator.md`
- Files created: `templates/orchestrator/{pm_spawn_workflow,resume_workflow,workflow_routing_reference}.md`
- Project conventions: `.claude/claude.md` (Path Layout section)
