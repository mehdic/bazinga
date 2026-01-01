# Domain Skill Migration Phase 6: Implementation Design

**Date:** 2026-01-01
**Context:** Designing the optimal fix for Phase 5 issues
**Decision:** Pending user approval
**Status:** Design Complete - Reviewed - Awaiting User Approval
**Reviewed by:** OpenAI GPT-5 (external review completed)

---

## Problem Statement

Phase 5 review identified that the Phase 4 "centralized validation" was:
1. **Incomplete** - Only 4 of 16 functions validated
2. **Broken** - `allow_global` parameter is dead code
3. **Oversimplified** - Treats all `group_id` parameters as equivalent when they have different semantics

The core insight from OpenAI: **group_id means different things in different contexts**.

---

## Semantic Analysis

### Three Distinct Domains of group_id

| Domain | Parameter Name | Meaning | 'global' Valid? |
|--------|---------------|---------|-----------------|
| **Scope** (most functions) | `group_id` | Session vs group scope | ✅ 'global' = session-level |
| **Investigation Scope** | `group_id` | Which group being investigated | ❌ Must be specific group |
| **Task Group ID** | `id` / `group_id` | Identifier for task group | ❌ 'global' is reserved |

### Why One Validator Doesn't Work

```python
# Current broken approach:
def validate_group_id(group_id, allow_global=True):  # allow_global NEVER CHECKED!
    ...
```

The boolean flag approach has problems:
1. Easy to forget to pass `allow_global=False`
2. Not self-documenting at call site
3. Mixes two concepts (validation + scope enforcement)

---

## Proposed Solution: Three Explicit Validators

### Design Principle

**Make the call site self-documenting.** When you read:
```python
error = validate_scope_group_only(group_id)
```

You immediately understand: "This operation requires a specific group, not 'global'."

Compare to:
```python
error = validate_group_id(group_id, allow_global=False)
```

Which requires you to remember what `allow_global=False` means.

### Implementation

```python
# Shared pattern validation
GROUP_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')
# Reserved names - checked CASE-INSENSITIVELY per OpenAI review
RESERVED_GROUP_IDS = frozenset({'global', 'session', 'all', 'default'})

def _validate_group_id_base(group_id: Any) -> Optional[str]:
    """Base validation: type, format, length. Used by all three validators."""
    if group_id is None:
        return "group_id cannot be None"
    if not isinstance(group_id, str):
        return f"group_id must be a string, got {type(group_id).__name__}"
    if not group_id or not group_id.strip():
        return "group_id cannot be empty"
    if len(group_id) > 64:
        return f"group_id too long (max 64 chars, got {len(group_id)})"
    if not GROUP_ID_PATTERN.match(group_id):
        return "group_id must be alphanumeric with underscores/hyphens only"
    return None


def validate_scope_global_or_group(group_id: Any) -> Optional[str]:
    """Validate scope allowing 'global' (session-level) or any valid group ID.

    Use for: save_state (non-investigation), get_latest_state, save_event,
             save_context_package, get_context_packages, save_reasoning,
             get_reasoning, reasoning_timeline, check_mandatory_phases,
             get_consumption

    Note: Callers accepting None should coerce to 'global' BEFORE calling.
    """
    return _validate_group_id_base(group_id)


def validate_scope_group_only(group_id: Any) -> Optional[str]:
    """Validate scope that MUST be group-specific (rejects 'global').

    Use for: save_investigation_iteration, save_state (investigation type),
             save_consumption, extract_strategies

    CASE-INSENSITIVE: 'GLOBAL', 'Global', 'global' all rejected.
    """
    error = _validate_group_id_base(group_id)
    if error:
        return error
    if group_id.lower() == 'global':  # Case-insensitive per OpenAI review
        return "group_id cannot be 'global' for this operation (must be group-specific)"
    return None


def validate_task_group_id(task_group_id: Any) -> Optional[str]:
    """Validate task group identifier (rejects reserved names).

    Use for: create_task_group, update_task_group, update_context_references

    Reserved names (case-insensitive): global, session, all, default
    """
    error = _validate_group_id_base(task_group_id)
    if error:
        return error
    # Case-insensitive reserved check per OpenAI review
    if task_group_id.lower() in RESERVED_GROUP_IDS:
        return f"'{task_group_id}' is a reserved identifier and cannot be used as a task group ID"
    return None
```

### Why This is Better

| Aspect | Old Approach | New Approach |
|--------|--------------|--------------|
| Dead code | `allow_global` never used | No dead code |
| Call site clarity | Need to remember what `False` means | Function name tells you |
| Semantic correctness | One-size-fits-all | Domain-specific |
| Error messages | Generic | Context-specific |
| Extensibility | Add more booleans? | Add new validator |

---

## Function-by-Function Mapping

### Category 1: Scope - Global or Group (11 functions)

These accept both 'global' (session-level) and group-specific values:

| Function | Current Validation | New Validator |
|----------|-------------------|---------------|
| `save_state` (pm/orchestrator/group_status) | `validate_group_id()` | `validate_scope_global_or_group()` |
| `get_latest_state` | `validate_group_id()` | `validate_scope_global_or_group()` |
| `save_event` | `validate_group_id()` | `validate_scope_global_or_group()` |
| `save_context_package` | ❌ None | `validate_scope_global_or_group()` |
| `get_context_packages` | ❌ None | `validate_scope_global_or_group()` |
| `save_reasoning` | ❌ None | `validate_scope_global_or_group()` |
| `get_reasoning` | ❌ None | `validate_scope_global_or_group()` |
| `reasoning_timeline` | ❌ None | `validate_scope_global_or_group()` |
| `check_mandatory_phases` | ❌ None | `validate_scope_global_or_group()` |
| `get_consumption` | ❌ None | `validate_scope_global_or_group()` |

### Category 2: Scope - Group Only (4 functions)

These MUST be group-specific (reject 'global'):

| Function | Current Validation | New Validator |
|----------|-------------------|---------------|
| `save_state` (investigation) | `validate_group_id()` | `validate_scope_group_only()` |
| `save_investigation_iteration` | `validate_group_id()` | `validate_scope_group_only()` |
| `save_consumption` | ❌ None | `validate_scope_group_only()` |
| `extract_strategies` | ❌ None | `validate_scope_group_only()` |

### Category 3: Task Group ID (3 functions)

These validate task group identifiers (reject reserved names):

| Function | Current Validation | New Validator |
|----------|-------------------|---------------|
| `create_task_group` | ❌ None | `validate_task_group_id()` |
| `update_task_group` | ❌ None | `validate_task_group_id()` |
| `update_context_references` | ❌ None | `validate_task_group_id()` |

### Special Case: save_state

`save_state` needs conditional validation based on `state_type`:

```python
def save_state(self, session_id: str, state_type: str, state_data: Dict,
               group_id: str = 'global') -> Dict[str, Any]:
    # Validate group_id based on state_type
    if state_type == 'investigation':
        error = validate_scope_group_only(group_id)
    else:
        error = validate_scope_global_or_group(group_id)
    if error:
        raise ValueError(error)
    ...
```

### Special Case: save_context_package None Handling

Per OpenAI review, `save_context_package` currently accepts `None` as session-level scope. We must coerce `None → 'global'` before validation:

```python
def save_context_package(self, session_id: str, package_data: Dict,
                         group_id: Optional[str] = None) -> Dict[str, Any]:
    # Coerce None to 'global' for backward compatibility
    if group_id is None:
        group_id = 'global'
    error = validate_scope_global_or_group(group_id)
    if error:
        raise ValueError(error)
    ...
```

This preserves the existing semantic where `None` means session-level.

---

## Backfill Strategy

### Current State

Migration only backfills `log_type = 'event'`:
```sql
UPDATE orchestration_logs SET group_id = 'global'
WHERE log_type = 'event' AND (group_id IS NULL OR group_id = '')
```

### What's Missing

| log_type | Has group_id? | Needs Backfill? |
|----------|--------------|-----------------|
| event | ✅ Yes | ✅ Currently done |
| reasoning | ✅ Yes | ❌ **MISSING** |
| interaction | ✅ Yes | ❌ **MISSING** |

### Recommended Fix

```sql
-- Backfill all log types that use group_id
UPDATE orchestration_logs
SET group_id = 'global'
WHERE group_id IS NULL OR group_id = ''
```

This is simpler and covers all cases. Since 'global' is the correct default for session-scoped logs, this is safe.

### Migration Safety

OpenAI raised concerns about long-running migrations on large tables. However:
1. This is an UPDATE with no joins - SQLite handles this efficiently
2. Typical BAZINGA databases are small (< 100K rows)
3. The UPDATE runs within the existing transaction with WAL mode

If concerned, we could add batching, but it's likely over-engineering for this use case.

### Legacy Investigation State Detection (OpenAI Critical Issue)

OpenAI correctly identified that `state_snapshots` with `state_type='investigation'` may contain `NULL` or `'global'` group_id, which would be invalid once group-only validation is enforced.

**Detection Query:**
```sql
-- Detect invalid investigation state rows BEFORE enforcing validation
SELECT COUNT(*) as invalid_count FROM state_snapshots
WHERE state_type = 'investigation'
  AND (group_id IS NULL OR LOWER(group_id) = 'global');
```

**Remediation Strategy:**

1. **Detection Phase (P1)**: Add a pre-flight check before enforcing validation
   - If invalid rows exist, log warning with count
   - Do NOT fail silently - visibility is critical

2. **Quarantine Option (P2)**: If invalid rows found:
   ```sql
   -- Quarantine invalid investigation rows with a synthetic group_id
   UPDATE state_snapshots
   SET group_id = '__invalid_investigation_' || id || '__'
   WHERE state_type = 'investigation'
     AND (group_id IS NULL OR LOWER(group_id) = 'global');
   ```

3. **Policy Decision**: Invalid investigation rows are likely:
   - Old data from before proper group scoping was enforced
   - Safe to quarantine since investigation state is ephemeral
   - Can be cleaned up manually after review

**Implementation Note:** Add detection to migration before applying the backfill. This gives visibility into the scope of the problem.

---

## CLI Output Strategy

### Current State

- `save_state` returns a dict (Fix G from Phase 4)
- CLI ignores the return value (line 3693)

### Options Considered

| Option | Pros | Cons |
|--------|------|------|
| Always output JSON | Consistent with other commands | May break scripts expecting silence |
| Add `--json` flag | Safe, opt-in | More complexity |
| Keep silent, return non-zero on error | Backward compatible | Less informative |

### Recommended: `--json` flag

Add optional `--json` flag to `save-state`. When present, output the result dict. This is the safest approach because:

1. Existing scripts continue to work (silent by default)
2. New scripts can opt-in to JSON output
3. Consistent pattern that could be applied to other commands

```python
elif cmd == 'save-state':
    # ... existing parsing ...
    json_output = '--json' in cmd_args
    result = db.save_state(cmd_args[0], cmd_args[1], state_data, group_id=group_id)
    if json_output:
        print(json.dumps(result, indent=2))
```

---

## DB-Level Guardrails (Optional P3)

### The Case For

Application-level validation can be bypassed by:
- Direct SQL access
- Future code paths that forget to validate
- Bugs in validation logic

A DB trigger provides defense-in-depth:

```sql
CREATE TRIGGER prevent_global_investigation
BEFORE INSERT ON state_snapshots
WHEN NEW.state_type = 'investigation' AND NEW.group_id = 'global'
BEGIN
    SELECT RAISE(ABORT, 'investigation state cannot use global scope');
END;

CREATE TRIGGER prevent_global_investigation_update
BEFORE UPDATE ON state_snapshots
WHEN NEW.state_type = 'investigation' AND NEW.group_id = 'global'
BEGIN
    SELECT RAISE(ABORT, 'investigation state cannot use global scope');
END;
```

### The Case Against

1. SQLite triggers add complexity
2. Error messages from triggers are less friendly
3. Application-level validation with good tests is usually sufficient
4. Triggers can be harder to debug

### Recommendation

**Skip for now (P3).** The explicit validators with good naming should prevent most issues. Add trigger later if we see violations in production.

---

## Implementation Plan

### Phase 6a: Replace Validators (P1)

1. Add three new validator functions with **case-insensitive** reserved checks
2. Add `_validate_group_id_base()` helper
3. Add expanded `RESERVED_GROUP_IDS` constant: `{'global', 'session', 'all', 'default'}`
4. Keep old `validate_group_id()` temporarily with `@deprecated` decorator

### Phase 6b: Apply Validators to All Functions (P1)

Update each function per the mapping table:
- Category 1: `validate_scope_global_or_group()`
- Category 2: `validate_scope_group_only()`
- Category 3: `validate_task_group_id()`

Special handling:
- `save_state`: Conditional validation based on `state_type`
- `save_context_package`: Coerce `None → 'global'` before validation

### Phase 6c: Legacy Data Detection & Backfill (P2)

1. **Detection first**: Query for invalid investigation state rows
2. **Log warning** if any found (with count)
3. **Quarantine** invalid rows with synthetic group_id
4. **Backfill** all orchestration_logs where group_id is NULL/empty

### Phase 6d: CLI --json Flag (P2)

Add optional `--json` flag to `save-state` command.

### Phase 6e: Add Tests (P2)

Per OpenAI recommendation, enumerate concrete test cases:
- Unit tests for all three validators (including case variants)
- Integration tests per function mapping (positive/negative)
- Migration tests for legacy data detection
- CLI tests for save-state with/without --json

### Phase 6f: Cleanup (P3)

1. Remove deprecated `validate_group_id()` function
2. Fix misleading comments
3. Update documentation
4. Consider DB CHECK constraint (simpler than trigger)

---

## Migration Path for Existing Code

### Backward Compatibility

| Change | Backward Compatible? | Notes |
|--------|---------------------|-------|
| New validators | ✅ Yes | Old function still exists |
| save_state validation | ✅ Yes | Only rejects invalid values |
| Backfill all logs | ✅ Yes | Sets NULL to 'global' |
| CLI --json flag | ✅ Yes | Opt-in, silent by default |

### Deprecation Timeline

1. **Phase 6**: Add new validators, keep old one deprecated
2. **Phase 7**: Remove old `validate_group_id()` after all call sites updated
3. **Future**: Consider DB triggers if issues arise

---

## Risk Assessment

### Low Risk

- **Type safety**: Validators only reject clearly invalid values
- **Backfill safety**: NULL → 'global' is the intended semantic
- **CLI compatibility**: --json is opt-in

### Medium Risk

- **Breaking valid 'global' uses**: Mitigated by careful function categorization
- **Missing a function**: Mitigated by comprehensive mapping table

### Mitigation

1. Run integration tests after each phase
2. Verify each function against the mapping table
3. Test both 'global' and group-specific values for each category

---

## Summary

### Key Decisions

1. **Three explicit validators** instead of boolean flag
2. **Self-documenting function names** that encode semantics
3. **Case-insensitive reserved checks** (per OpenAI review)
4. **Expanded reserved names**: 'global', 'session', 'all', 'default'
5. **Conditional validation in save_state** based on state_type
6. **None → 'global' coercion** in save_context_package
7. **Legacy data detection** before backfill (with quarantine option)
8. **Backfill all log types** not just events
9. **Opt-in --json flag** for CLI output
10. **Skip DB triggers** for now (consider CHECK constraint later)

### Implementation Order

| Priority | Fix | Effort |
|----------|-----|--------|
| P1 | Add three validator functions (case-insensitive) | Small |
| P1 | Apply to all 18 functions | Medium |
| P2 | Legacy data detection & quarantine | Small |
| P2 | Extend backfill to all log types | Small |
| P2 | Add CLI --json flag | Small |
| P2 | Add comprehensive tests | Medium |
| P3 | Remove deprecated validator | Small |
| P3 | Fix comments/docs, consider CHECK constraint | Small |

### Expected Outcome

- **All functions validated** with appropriate semantics
- **No dead code** (allow_global removed)
- **Case-insensitive protection** against reserved name variants
- **Legacy data handled** (detected and quarantined)
- **Self-documenting call sites**
- **Complete backfill** for legacy data
- **Safe CLI changes** via opt-in flag
- **Comprehensive test coverage**

---

## Questions for Review

1. Is the three-validator approach cleaner than fixing the boolean flag?
2. Should `save_consumption` be group-only or allow global?
3. Is the backfill-all-log-types approach safe?
4. Is --json flag the right CLI approach?

---

## Multi-LLM Review Integration

**Review Date:** 2026-01-01
**Reviewer:** OpenAI GPT-5 (Gemini skipped - ENABLE_GEMINI=false)

### Incorporated Feedback ✅

| Feedback | Integration |
|----------|-------------|
| **Case sensitivity of reserved identifier** | Made all reserved checks case-insensitive (`group_id.lower() == 'global'`) |
| **Expanded reserved names** | Added 'session', 'all', 'default' to `RESERVED_GROUP_IDS` |
| **save_context_package None handling** | Added explicit `None → 'global'` coercion before validation |
| **Legacy investigation state detection** | Added detection query and quarantine strategy |
| **Deprecation discipline** | Added `@deprecated` decorator requirement for old validator |
| **Add tests** | Added Phase 6e with comprehensive test requirements |
| **Consider CHECK constraint** | Added to Phase 6f as alternative to triggers |

### Rejected Suggestions (With Reasoning)

| Suggestion | Reason for Rejection |
|------------|---------------------|
| **Backfill batching** | Over-engineering for our use case (< 100K rows typical, WAL mode handles well) |
| **Single validator with domain enum** | Three explicit validators are more self-documenting at call sites; domain enum adds indirection |
| **COALESCE in read paths during transition** | Unnecessary complexity - backfill runs before validation enforcement, so no transition period with missing data |
| **CLI consistency for other commands** | Out of scope for Phase 6; can be addressed later if needed |
| **Transitional soft-enforcement (log warnings first)** | BAZINGA is internal tooling with controlled deployment; hard enforcement is acceptable |

### Addressed But Deferred

| Item | Deferral Reason |
|------|-----------------|
| **extract_strategies queries non-existent table** | Requires deeper investigation - may be dead code. Flagged for Phase 7. |
| **Audit save_consumption semantics** | Marked as group-only based on semantic analysis; will verify during implementation. |

### Risk Assessment Update

OpenAI's overall assessment: "Confidence: medium-high with the suggested adjustments."

After integrating the feedback:
- **Case sensitivity gap**: ✅ Fixed with lowercase comparison
- **None handling**: ✅ Fixed with explicit coercion
- **Legacy data**: ✅ Detection and quarantine strategy added
- **Test coverage**: ✅ Comprehensive test plan added

Remaining risks are low: primarily "did we miss any functions" (mitigated by mapping table) and "extract_strategies table mismatch" (deferred to Phase 7).

---

## References

- Phase 5 review: research/domain-skill-migration-phase5-ultrathink.md
- OpenAI feedback on semantics: tmp/ultrathink-reviews/openai-review.md
- Current validators: bazinga_db.py:96-121
