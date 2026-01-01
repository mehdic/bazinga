# Domain Skill Migration: Full Implementation Plan

**Date:** 2026-01-01
**Context:** Implementation plan for all phases from ultrathink review
**Decision:** Implement all phases (Phase 1-3)
**Status:** Reviewed
**Reviewed by:** OpenAI GPT-5 (2026-01-01)

---

## Executive Summary

This plan implements ALL phases from the domain skill migration ultrathink review:
- **Phase 1:** Documentation fixes (3 items)
- **Phase 2:** Security/reliability improvements (3 items)
- **Phase 3:** Architectural improvements (2 items)

**Total estimated changes:** 8 files modified, 2 files created

---

## Discovery: Existing Infrastructure

Analysis revealed existing infrastructure that simplifies implementation:

| Component | Status | Location |
|-----------|--------|----------|
| `scan_and_redact()` function | ✅ EXISTS | bazinga_db.py:59 |
| Event JSON schemas | ✅ PARTIAL | bazinga/schemas/event_*.json (3 schemas) |
| Dedup key in schemas | ✅ EXISTS | `x-dedup-key` field in schemas |
| `--content-file` pattern | ✅ EXISTS | save-reasoning command |

**Missing event schemas:**
- `investigation_iteration`
- `scope_change`
- `role_violation`
- `pm_bazinga`
- `validator_verdict`

---

## Phase 1: Documentation Fixes

### 1.1 Add `investigation_iteration` to bazinga-db-agents/SKILL.md

**File:** `.claude/skills/bazinga-db-agents/SKILL.md`

**Change:** Add to "Common event types" section (line ~189-194):

```markdown
**Common event types:**
- `scope_change` - User approved scope reduction
- `role_violation` - Detected role boundary violation
- `tl_issues` - Tech Lead issues after CHANGES_REQUESTED
- `tl_issue_responses` - Developer responses to TL issues
- `tl_verdicts` - TL verdicts on Developer rejections
+ - `investigation_iteration` - Investigator agent iteration progress
+ - `pm_bazinga` - PM sends BAZINGA completion signal
+ - `validator_verdict` - Validator ACCEPT/REJECT decision
```

**Effort:** 5 minutes

---

### 1.2 Add "State vs Events" documentation to investigation_loop.md

**File:** `templates/investigation_loop.md`

**Change:** Add section after "Prerequisites" (line ~19):

```markdown
---

## State vs Events Design

Investigation progress is tracked in TWO complementary systems:

| System | Purpose | Skill | Resumable? |
|--------|---------|-------|------------|
| **State** | Current progress, iteration count | bazinga-db-core | ✅ Yes |
| **Events** | Immutable audit trail, history | bazinga-db-agents | ❌ Append-only |

**Why both?**
- State enables session resumption after context compaction
- Events provide queryable history and dashboard timeline
- Both MUST be updated together for consistency

**Failure handling:**
- If state update fails: Retry with exponential backoff
- If event save fails: Log warning, continue (audit trail is secondary)
- Reconciliation: Dashboard queries events to verify state accuracy

---
```

**Effort:** 5 minutes

---

### 1.3 Add event type validation to validation script

**File:** `scripts/validate-db-skill-migration.sh`

**Change:** Add new validation section after deprecated skill check:

```bash
# 7. Check event types are documented
echo ""
echo "📋 Checking event types are documented..."

# Known event types (from bazinga-db-agents SKILL.md)
DOCUMENTED_EVENTS="scope_change|role_violation|tl_issues|tl_issue_responses|tl_verdicts|investigation_iteration|pm_bazinga|validator_verdict"

# Find event types used in agent files
USED_EVENTS=$(grep -roh 'Event Type: [a-z_]*' --include="*.md" "$REPO_ROOT/agents" "$REPO_ROOT/templates" 2>/dev/null | \
    sed 's/Event Type: //' | sort -u)

for event in $USED_EVENTS; do
    if ! echo "$event" | grep -qE "^($DOCUMENTED_EVENTS)$"; then
        echo -e "${YELLOW}  ⚠️  Undocumented event type: $event${NC}"
        ((WARNINGS++))
    fi
done

if [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}  ✅ All event types are documented${NC}"
fi
```

**Effort:** 10 minutes

---

## Phase 2: Security/Reliability Improvements

### 2.1 Add `--payload-file` option to save-event

**File:** `.claude/skills/bazinga-db/scripts/bazinga_db.py`

**Change:** Modify `save_event` CLI handler (around line 4288):

```python
elif cmd == 'save-event':
    # save-event <session_id> <event_subtype> <payload> [--payload-file <path>]
    if len(cmd_args) < 2:
        print("Error: save-event requires: <session_id> <event_subtype> [payload|--payload-file <path>]", file=sys.stderr)
        sys.exit(1)

    session_id = cmd_args[0]
    event_subtype = cmd_args[1]

    # Check for --payload-file option
    payload = None
    i = 2
    while i < len(cmd_args):
        if cmd_args[i] == '--payload-file':
            if i + 1 >= len(cmd_args):
                print("Error: --payload-file requires a path", file=sys.stderr)
                sys.exit(1)
            payload_path = cmd_args[i + 1]
            try:
                with open(payload_path, 'r') as f:
                    payload = f.read().strip()
            except Exception as e:
                print(f"Error reading payload file: {e}", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif payload is None:
            payload = cmd_args[i]
            i += 1
        else:
            print(f"Error: Unexpected argument: {cmd_args[i]}", file=sys.stderr)
            sys.exit(1)

    if payload is None:
        print("Error: No payload provided", file=sys.stderr)
        sys.exit(1)

    result = db.save_event(session_id, event_subtype, payload)
    print(json.dumps(result, indent=2))
```

**Also update:** bazinga-db-agents/SKILL.md to document new option

**Effort:** 20 minutes

---

### 2.2 Add secret redaction to save-event

**File:** `.claude/skills/bazinga-db/scripts/bazinga_db.py`

**Change:** Modify `save_event` method (line ~1086):

```python
def save_event(self, session_id: str, event_subtype: str, payload: str,
               _retry_count: int = 0) -> Dict[str, Any]:
    """Save an event to orchestration_logs with log_type='event'.

    SECURITY: Payload is scanned for secrets and redacted before storage.
    """
    # ... existing validation ...

    # NEW: Scan and redact secrets from payload
    redacted_payload, was_redacted = scan_and_redact(payload)
    if was_redacted:
        self._print_error("Warning: Secrets detected and redacted from event payload")

    conn = None
    try:
        conn = self._get_connection()
        cursor = conn.execute("""
            INSERT INTO orchestration_logs
            (session_id, agent_type, content, log_type, event_subtype, event_payload, redacted)
            VALUES (?, 'system', ?, 'event', ?, ?, ?)
        """, (session_id, f"Event: {event_subtype}", event_subtype,
              redacted_payload, 1 if was_redacted else 0))
        # ... rest unchanged ...
```

**Note:** Schema already has `redacted` column, just not used by save_event.

**Effort:** 15 minutes

---

### 2.3 Add idempotency enforcement to save-event

**File:** `.claude/skills/bazinga-db/scripts/bazinga_db.py`

**Change:** Add idempotency check before insert:

```python
def save_event(self, session_id: str, event_subtype: str, payload: str,
               idempotency_key: Optional[str] = None,
               _retry_count: int = 0) -> Dict[str, Any]:
    """Save an event with optional idempotency protection.

    Args:
        idempotency_key: If provided, prevents duplicate events with same key.
                        Recommended format: {session_id}|{group_id}|{event_type}|{iteration}
    """
    # ... existing validation ...

    conn = None
    try:
        conn = self._get_connection()

        # Check idempotency if key provided
        if idempotency_key:
            existing = conn.execute("""
                SELECT id FROM orchestration_logs
                WHERE session_id = ? AND log_type = 'event'
                AND event_payload LIKE ?
            """, (session_id, f'%"idempotency_key":"{idempotency_key}"%')).fetchone()

            if existing:
                self._print_success(f"✓ Event already exists (idempotent, id={existing[0]})")
                return {
                    'success': True,
                    'event_id': existing[0],
                    'idempotent': True,
                    'message': 'Event already exists'
                }

        # Inject idempotency key into payload if provided
        if idempotency_key:
            try:
                payload_dict = json.loads(payload)
                payload_dict['idempotency_key'] = idempotency_key
                payload = json.dumps(payload_dict)
            except json.JSONDecodeError:
                pass  # Leave payload as-is if not valid JSON

        # ... rest of insert logic ...
```

**CLI change:** Add `--idempotency-key` option

**Effort:** 30 minutes

---

## Phase 3: Architectural Improvements

### 3.1 Central Event Registry

**Files to create:**
- `bazinga/schemas/events/registry.json` - Event type registry
- `scripts/validate-event-schemas.py` - CI validation script

**registry.json:**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "BAZINGA Event Type Registry",
  "description": "Central registry of all valid event types and their schemas",
  "version": "1.0.0",
  "event_types": {
    "scope_change": {
      "schema": "event_scope_change.schema.json",
      "description": "User approved scope reduction",
      "producers": ["orchestrator"],
      "consumers": ["dashboard", "pm"]
    },
    "role_violation": {
      "schema": "event_role_violation.schema.json",
      "description": "Detected role boundary violation",
      "producers": ["orchestrator"],
      "consumers": ["dashboard"]
    },
    "tl_issues": {
      "schema": "event_tl_issues.schema.json",
      "description": "Tech Lead issues after CHANGES_REQUESTED",
      "producers": ["orchestrator"],
      "consumers": ["developer", "validator", "dashboard"]
    },
    "tl_issue_responses": {
      "schema": "event_tl_issue_responses.schema.json",
      "description": "Developer responses to TL issues",
      "producers": ["orchestrator"],
      "consumers": ["tech_lead", "validator", "dashboard"]
    },
    "tl_verdicts": {
      "schema": "event_tl_verdicts.schema.json",
      "description": "TL verdicts on Developer rejections",
      "producers": ["orchestrator"],
      "consumers": ["developer", "validator", "dashboard"]
    },
    "investigation_iteration": {
      "schema": "event_investigation_iteration.schema.json",
      "description": "Investigator agent iteration progress",
      "producers": ["investigator", "orchestrator"],
      "consumers": ["dashboard", "tech_lead"]
    },
    "pm_bazinga": {
      "schema": "event_pm_bazinga.schema.json",
      "description": "PM sends BAZINGA completion signal",
      "producers": ["orchestrator"],
      "consumers": ["validator", "dashboard"]
    },
    "validator_verdict": {
      "schema": "event_validator_verdict.schema.json",
      "description": "Validator ACCEPT/REJECT decision",
      "producers": ["validator"],
      "consumers": ["orchestrator", "dashboard"]
    }
  }
}
```

**Missing schemas to create:**
- `event_investigation_iteration.schema.json`
- `event_scope_change.schema.json`
- `event_role_violation.schema.json`
- `event_pm_bazinga.schema.json`
- `event_validator_verdict.schema.json`

**Effort:** 2 hours

---

### 3.2 Atomic Dual-Write for Investigation

**Approach:** Add combined command rather than transaction wrapper (simpler)

**File:** `.claude/skills/bazinga-db/scripts/bazinga_db.py`

**New command:** `save-investigation-iteration`

```python
def save_investigation_iteration(self, session_id: str, group_id: str,
                                  iteration: int, status: str,
                                  state_data: str, event_payload: str) -> Dict[str, Any]:
    """Atomically save investigation state AND event together.

    This ensures consistency between state (for resumption) and events (for audit).
    Uses single transaction - both succeed or both fail.
    """
    conn = None
    try:
        conn = self._get_connection()

        # Start transaction
        conn.execute("BEGIN IMMEDIATE")

        # 1. Save state
        conn.execute("""
            INSERT OR REPLACE INTO state_snapshots
            (session_id, state_type, state_data, updated_at)
            VALUES (?, 'investigation', ?, datetime('now'))
        """, (session_id, state_data))

        # 2. Save event (with redaction)
        redacted_payload, was_redacted = scan_and_redact(event_payload)
        idempotency_key = f"{session_id}|{group_id}|investigation_iteration|{iteration}"

        # Check idempotency
        existing = conn.execute("""
            SELECT id FROM orchestration_logs
            WHERE session_id = ? AND log_type = 'event'
            AND event_subtype = 'investigation_iteration'
            AND event_payload LIKE ?
        """, (session_id, f'%"iteration":{iteration}%')).fetchone()

        if not existing:
            conn.execute("""
                INSERT INTO orchestration_logs
                (session_id, agent_type, content, log_type, event_subtype,
                 event_payload, redacted, group_id)
                VALUES (?, 'investigator', ?, 'event', 'investigation_iteration',
                        ?, ?, ?)
            """, (session_id, f"Investigation iteration {iteration}: {status}",
                  redacted_payload, 1 if was_redacted else 0, group_id))

        conn.commit()

        return {
            'success': True,
            'atomic': True,
            'state_saved': True,
            'event_saved': not existing,
            'iteration': iteration
        }

    except Exception as e:
        if conn:
            conn.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        if conn:
            conn.close()
```

**Effort:** 45 minutes

---

## Implementation Order (Dependencies)

```
Phase 1.1 (SKILL.md docs) ─────────────────────────────┐
                                                        ├─► Phase 2.1 (--payload-file)
Phase 1.2 (State vs Events doc) ───────────────────────┤
                                                        │
Phase 1.3 (validation script) ◄── Phase 3.1 (registry) ┤
                                                        │
Phase 2.2 (redaction) ─────────────────────────────────┤
                                                        │
Phase 2.3 (idempotency) ───────────────────────────────┘

Phase 3.2 (atomic write) ◄── Phase 2.2, Phase 2.3
```

**Critical path:** 1.1 → 2.1 → 2.2 → 3.2

---

## Risk Analysis

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking existing save-event calls | LOW | HIGH | New params are optional |
| Redaction too aggressive | MEDIUM | MEDIUM | Use same patterns as save-reasoning |
| Idempotency false positives | LOW | MEDIUM | Use precise key format |
| Atomic write deadlocks | LOW | HIGH | Use IMMEDIATE transaction mode |
| Schema validation too strict | MEDIUM | MEDIUM | Start with warning mode |

---

## Testing Plan

### Unit Tests

```python
# tests/test_domain_skill_migration_phase2.py

def test_save_event_with_payload_file():
    """Phase 2.1: --payload-file option works"""

def test_save_event_redacts_secrets():
    """Phase 2.2: Secrets are redacted from event payloads"""

def test_save_event_idempotency():
    """Phase 2.3: Duplicate events with same key are prevented"""

def test_save_investigation_iteration_atomic():
    """Phase 3.2: State and event are saved atomically"""

def test_save_investigation_iteration_rollback():
    """Phase 3.2: Both rollback on failure"""
```

### Integration Tests

1. Run full orchestration with investigation loop
2. Verify dashboard shows correct investigation history
3. Test session resumption after context compaction

---

## Rollback Plan

Each phase can be rolled back independently:

| Phase | Rollback Action |
|-------|-----------------|
| 1.x | Revert documentation changes |
| 2.1 | Remove --payload-file parsing (optional param) |
| 2.2 | Remove scan_and_redact call (still saves unredacted) |
| 2.3 | Remove idempotency check (still saves all events) |
| 3.1 | Delete registry files (validation becomes no-op) |
| 3.2 | Remove new command (callers use separate calls) |

---

## Estimated Total Effort

| Phase | Items | Time |
|-------|-------|------|
| Phase 1 | 3 | 20 minutes |
| Phase 2 | 3 | 65 minutes |
| Phase 3 | 2 | 2.75 hours |
| Testing | - | 1 hour |
| **Total** | **8** | **~5 hours** |

---

## Files Modified Summary

| File | Changes |
|------|---------|
| `.claude/skills/bazinga-db-agents/SKILL.md` | Add event types |
| `templates/investigation_loop.md` | Add State vs Events section |
| `scripts/validate-db-skill-migration.sh` | Add event type validation |
| `.claude/skills/bazinga-db/scripts/bazinga_db.py` | payload-file, redaction, idempotency, atomic write |

**Files Created:**
| File | Purpose |
|------|---------|
| `bazinga/schemas/events/registry.json` | Event type registry |
| `bazinga/schemas/event_investigation_iteration.schema.json` | Schema |
| `bazinga/schemas/event_scope_change.schema.json` | Schema |
| `bazinga/schemas/event_role_violation.schema.json` | Schema |
| `bazinga/schemas/event_pm_bazinga.schema.json` | Schema |
| `bazinga/schemas/event_validator_verdict.schema.json` | Schema |
| `scripts/validate-event-schemas.py` | CI validation |

---

## Multi-LLM Review Integration

**Reviewed by:** OpenAI GPT-5 (2026-01-01)

### Critical Issues Identified by OpenAI

| Issue | Severity | My Response |
|-------|----------|-------------|
| Missing CLI command for atomic write | 🔴 CRITICAL | ✅ ACCEPT - Will add CLI command + skill wiring |
| Payload LIKE-based dedup is fragile | 🔴 CRITICAL | ✅ ACCEPT - Will add idempotency_key column |
| No runtime schema validation | 🟡 HIGH | ✅ ACCEPT - Will add optional runtime validation |
| Redaction on events not skill-wired | 🟡 HIGH | ✅ ACCEPT - Will ensure both skills use same code |
| No DB schema migration for new column | 🟡 MEDIUM | ✅ ACCEPT - Will add migration in init_db.py |

### Plan Modifications Based on Review

#### 1. Add CLI Command for Atomic Write

**Original:** Only Python method, no CLI
**Updated:** Add `save-investigation-iteration` CLI command:

```bash
python3 bazinga_db.py --quiet save-investigation-iteration \
  "<session_id>" "<group_id>" <iteration> "<status>" \
  --state-file /tmp/state.json --event-file /tmp/event.json
```

**Also:** Update `bazinga-db-agents/SKILL.md` to document this command.

#### 2. Add idempotency_key Column (Schema v17)

**Original:** LIKE-based payload search
**Updated:** Add column with unique index:

```sql
-- Add to orchestration_logs table
ALTER TABLE orchestration_logs ADD COLUMN idempotency_key TEXT;

-- Add partial unique index
CREATE UNIQUE INDEX idx_logs_idempotency
ON orchestration_logs(session_id, event_subtype, idempotency_key)
WHERE idempotency_key IS NOT NULL AND log_type = 'event';
```

**Migration:** Add to init_db.py with SCHEMA_VERSION = 17

#### 3. Add Runtime Schema Validation (Soft Mode)

**Original:** CI-only validation
**Updated:** Add optional runtime validation:

```python
def save_event(self, session_id: str, event_subtype: str, payload: str,
               validate_schema: bool = True, ...):
    """
    Args:
        validate_schema: If True, validate payload against JSON Schema (warns on mismatch)
    """
    if validate_schema:
        schema_path = f"bazinga/schemas/event_{event_subtype}.schema.json"
        if os.path.exists(schema_path):
            # Validate and warn (don't fail) on mismatch
            self._validate_event_schema(payload, schema_path)
```

#### 4. Update Orchestrator to Use Atomic Command

**Original:** Two separate saves in investigation_loop.md
**Updated:** Add decision logic:

```markdown
## Atomic Save (Preferred)

If `save-investigation-iteration` command is available:
```
bazinga-db-agents, please save investigation iteration atomically:
Session: {session_id}, Group: {group_id}, Iteration: {N}
State: {state_json}, Event: {event_json}
```

**Fallback:** If atomic command fails or unavailable, use two separate saves.
```

### Rejected Suggestions

| Suggestion | Reason for Rejection |
|------------|---------------------|
| Single skill façade | Already have deprecated bazinga-db as router; adds confusion |
| Content-addressable dedup (SHA256) | Column-based idempotency is simpler and standard |
| Disable redaction in test environments | Security should be consistent; use allow-list instead |

### Updated Effort Estimate

| Phase | Original | Updated |
|-------|----------|---------|
| Phase 1 | 20 min | 20 min (unchanged) |
| Phase 2 | 65 min | 90 min (+25 min for column migration) |
| Phase 3 | 2.75 hrs | 3.5 hrs (+45 min for CLI wiring + runtime validation) |
| Testing | 1 hr | 1.5 hrs (+30 min for new tests) |
| **Total** | **~5 hrs** | **~6.5 hrs** |

### Updated Risk Matrix

| Risk | Original | Updated | Mitigation |
|------|----------|---------|------------|
| Breaking save-event calls | LOW | LOW | Optional params, backward compatible |
| Idempotency false positives | LOW | VERY LOW | Column-based, not LIKE-based |
| Atomic write deadlocks | LOW | LOW | IMMEDIATE mode + retry on BUSY |
| Schema validation too strict | MEDIUM | LOW | Warn mode by default |
| **NEW: Migration fails** | - | LOW | Wrapped in try/except, graceful degrade |

---

## Final Checklist

Before implementation, verify:

- [ ] User approves all phases (1, 2, 3)
- [ ] User approves schema version bump (v16 → v17)
- [ ] User approves new CLI command addition
- [ ] User approves runtime validation (soft mode)
- [ ] Confirm no other PRs modifying bazinga_db.py
