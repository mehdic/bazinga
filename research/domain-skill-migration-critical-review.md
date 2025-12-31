# Domain Skill Migration: Critical Self-Review

**Date:** 2025-12-31
**Context:** Phase 1 fixes for bazinga-db domain skill migration
**Status:** CRITICAL ISSUES FOUND - Requires Immediate Action

---

## Executive Summary

The domain skill migration implementation has **critical bugs** that were masked by overly permissive validation rules. While 20+ files were updated, the validation script's exclusions created blind spots that allowed domain mismatches to persist.

**Severity: HIGH** - Production templates contain incorrect domain mappings.

---

## 1. Critical Bugs Found

### 1.1 templates/investigation_loop.md - WRONG DOMAIN MAPPINGS

| Line | Current | Should Be | Impact |
|------|---------|-----------|--------|
| 156 | `bazinga-db-core, please log investigation iteration` | `bazinga-db-agents` | Logging goes to wrong skill |
| 180 | `bazinga-db-core, please get active agent count` | `bazinga-db-agents` | Agent queries fail |
| 247 | `bazinga-db-core, please increment revision` | `bazinga-db-core` | OK (state operation) |
| 300 | `bazinga-db-core, please save context package` | `bazinga-db-context` | Context never saved |

**Root Cause:** The validation script excludes `templates/*` assuming they're documentation. But `investigation_loop.md` is an **operational template** that agents use directly.

### 1.2 Validation Script Design Flaw

```bash
# Current exclusions - TOO BROAD
-not -path "$REPO_ROOT/templates/*"  # Excludes operational templates!
-not -path "$REPO_ROOT/docs/*"
-not -path "$REPO_ROOT/.claude/skills/*/references/*"
```

**Problem:** Not all templates are documentation. Some are executable agent instructions.

### 1.3 Missing Invocation Statements

The investigation_loop.md has request text but **NO corresponding `Skill(command: ...)` invocations** for many operations. This means agents will make requests but never actually invoke the skill.

---

## 2. Logical Flaws

### 2.1 False Dichotomy: Documentation vs Operational

The validation script assumes templates are either:
- **Documentation** (exclude from validation)
- **Agent files** (validate strictly)

Reality: Templates like `investigation_loop.md`, `phase_simple.md`, `phase_parallel.md` are **embedded into agent prompts** and execute as code.

### 2.2 Request/Invocation Consistency Check is Insufficient

Current check:
```bash
if file has "bazinga-db-X, please" AND NOT "Skill(command: bazinga-db-X)"
  → warning
```

Missing checks:
1. Does the request text match the correct domain for that operation?
2. Are there orphaned invocations without request text?
3. Do CLI commands use the correct domain?

### 2.3 Domain Classification is Implicit

No explicit mapping exists between operations and domains. Each file interprets the domain split differently.

---

## 3. Missing Considerations

### 3.1 CLI Script Path References

The CLI script path `.claude/skills/bazinga-db/scripts/bazinga_db.py` is referenced 20+ times. If the script moves, all references break.

**Better:** Define a constant or use a wrapper script.

### 3.2 No Runtime Verification

The validation only checks static text. It doesn't verify:
- Skills actually exist and are loadable
- CLI commands map to real functions
- Request text is parseable

### 3.3 Backward Compatibility

The deprecated `bazinga-db` skill routes to domain skills, but:
- The routing table is manually maintained
- No tests verify routing works
- No deprecation warnings at runtime

### 3.4 Cross-File Consistency

Operations like "update task group" appear in 10+ files with varying request text:
- `bazinga-db-workflow, please update task group:`
- `bazinga-db-workflow, please update task group status:`
- `update-task-group` (CLI format)

No canonical reference for correct phrasing.

---

## 4. Better Alternatives

### 4.1 Domain Registry (Recommended)

Create a single source of truth:

```python
# .claude/skills/bazinga-db/domain_registry.py
DOMAIN_MAPPING = {
    # Core operations
    "create-session": "core",
    "get-session": "core",
    "save-state": "core",

    # Workflow operations
    "create-task-group": "workflow",
    "update-task-group": "workflow",

    # Agent operations
    "log-interaction": "agents",
    "save-reasoning": "agents",

    # Context operations
    "save-context-package": "context",
    "extract-strategies": "context",
}
```

Benefits:
- Single source of truth
- Validation script can use it
- Auto-generate routing table

### 4.2 Template Categories

Classify templates explicitly:

```yaml
# templates/manifest.yaml
investigation_loop.md:
  type: operational  # Validates like agent files
  embedded_in: [investigator.md, orchestrator.md]

message_templates.md:
  type: documentation  # Skip validation
```

### 4.3 Request Text Canonicalization

Define canonical request patterns:

```markdown
## Save Context Package
**Domain:** context
**Request:** `bazinga-db-context, please save context package:`
**CLI:** `bazinga_db.py save-context-package ...`
```

Validation can then check against canonical forms.

---

## 5. Implementation Risks

### 5.1 Immediate Risk: Investigation Workflow Broken

If `investigation_loop.md` is used as-is:
- Investigation logging goes to wrong table (or fails silently)
- Context packages never saved
- Agent counts may return wrong data

**Mitigation:** Fix investigation_loop.md immediately.

### 5.2 Silent Failures

When wrong domain is invoked:
- Skill might not recognize the command
- Returns empty/error that's ignored
- Data is lost

**Mitigation:** Add explicit error handling in skill responses.

### 5.3 Validation Bypass

Developers might add new templates to excluded directories, bypassing validation entirely.

**Mitigation:** Invert the logic - validate everything by default, exclude only explicitly marked files.

### 5.4 Merge Conflicts

Multiple files have similar patterns. Merging from other branches may reintroduce old-style references.

**Mitigation:** Add pre-merge hook or CI check.

---

## 6. Improvement Suggestions

### 6.1 Immediate (Before Merge)

1. **Fix investigation_loop.md** - Correct all domain mappings
2. **Add missing invocations** - Every request needs corresponding Skill() call
3. **Refine validation exclusions** - Only exclude true documentation files
4. **Add operational template list** - Explicit list of templates that need validation

### 6.2 Short-Term (Next Sprint)

1. **Create domain_registry.py** - Single source of truth for operation→domain mapping
2. **Add runtime deprecation logging** - Log when deprecated skill routes to domain skill
3. **Add integration test** - Verify each domain skill handles its operations correctly
4. **Canonical request patterns** - Document standard phrasing for each operation

### 6.3 Long-Term (Technical Debt)

1. **Template manifest** - Classify all templates by type
2. **Auto-generation** - Generate routing table and validation from registry
3. **Schema validation** - Verify request text contains required fields
4. **Cross-reference check** - Ensure all embedded templates match their sources

---

## 7. Updated Validation Script Requirements

```bash
# validate-db-skill-migration.sh v2

# 1. Check ALL markdown files (no blanket exclusions)
# 2. Classify files:
#    - Agent files: strict validation
#    - Operational templates: strict validation
#    - Documentation: skip or warn-only
# 3. Domain correctness:
#    - Map operations to expected domains
#    - Flag mismatches
# 4. Invocation completeness:
#    - Every request needs invocation
#    - Every invocation needs request
# 5. Cross-file consistency:
#    - Same operation should use same phrasing
```

---

## 8. Specific Files Requiring Fixes

| File | Issue | Priority |
|------|-------|----------|
| `templates/investigation_loop.md` | Wrong domains for 3 operations | CRITICAL |
| `templates/investigation_loop.md` | Missing Skill() invocations | HIGH |
| `.specify/memory/constitution.md` | References old "bazinga-db skill" | LOW |
| Validation script | Exclusions too broad | HIGH |

---

## 9. Verification Checklist

Before considering migration complete:

- [ ] All files in templates/ with bazinga-db references are verified
- [ ] Each request has matching Skill() invocation
- [ ] Each operation maps to correct domain
- [ ] Validation script catches all issues when run
- [ ] Integration test passes with domain skills
- [ ] No silent failures when wrong domain invoked

---

## 10. Conclusion

**The implementation is INCOMPLETE.** While significant progress was made on Phase 1, critical bugs remain:

1. **investigation_loop.md** has wrong domain mappings that will cause runtime failures
2. **Validation script** has blind spots that mask issues
3. **No canonical reference** for correct operation→domain mapping

**Recommended Action:** Do NOT merge until investigation_loop.md is fixed and validation script is enhanced to catch these issues.

---

## Multi-LLM Review Integration

**Reviewed by:** OpenAI GPT-5 (2025-12-31)

### Consensus Points (Confirmed)

1. **Wrong domain mappings in investigation_loop.md are critical** - Must fix before merge
2. **Validation script exclusions are too broad** - Operational templates must be validated
3. **Domain registry is the right approach** - Single source of truth recommended
4. **Missing Skill() invocations are a real bug** - Request text without invocation is useless

### New Insights from Review

1. **"active agent count" domain is ambiguous** - I assumed `bazinga-db-agents` but OpenAI correctly notes this could be:
   - `bazinga-db-core` (session/orchestrator state)
   - `bazinga-db-workflow` (workflow state)
   - Need to define API contract first, not guess

2. **Other operational templates need scanning** - Beyond investigation_loop.md:
   - `templates/orchestrator/phase_simple.md`
   - `templates/orchestrator/phase_parallel.md`
   - `templates/shutdown_protocol.md`
   - `templates/clarification_flow.md`

3. **Runtime safeguards needed** - Domain skills should emit explicit errors for unknown operations, not fail silently

4. **Deprecation telemetry** - Add runtime logging when deprecated bazinga-db shim is used

### Incorporated Improvements

| Suggestion | Action |
|------------|--------|
| Fix investigation_loop.md immediately | ✅ Will fix domain mappings and add Skill() invocations |
| Define "active agent count" API first | ✅ Need to check CLI and decide domain before fixing |
| Create domain_registry.py | ✅ Added to short-term plan |
| Template manifest for classification | ✅ Added to long-term plan |
| CI gates (pre-commit + required job) | ✅ Added to immediate actions |
| Golden tests for templates | ✅ Added to short-term plan |
| Sweep other operational templates | ✅ Added to immediate verification |

### Rejected Suggestions (None)

All suggestions from the review are valid and actionable.

---

## Revised Action Plan

### Phase 1: Immediate Fixes (Before Merge)

1. **Audit CLI for "active agent count"** - Determine correct domain
2. **Fix investigation_loop.md** - All domain mappings and add Skill() invocations
3. **Scan operational templates** - phase_simple.md, phase_parallel.md, shutdown_protocol.md
4. **Update validation script** - Add operational templates to validation scope
5. **Run validation** - Verify all issues caught

### Phase 2: CI/CD (This Sprint)

1. **Pre-commit hook** - Block commits with domain mismatches
2. **Required CI job** - validate-db-skill-migration.sh must pass

### Phase 3: Infrastructure (Next Sprint)

1. **domain_registry.py** - Single source of truth
2. **Golden tests** - Parse templates, verify domain mappings
3. **Runtime error codes** - Skills emit explicit errors

