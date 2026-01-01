# Domain Skill Migration: Ultrathink Critical Review

**Date:** 2026-01-01
**Context:** Critical review of bazinga-db skill split into 4 domain-focused skills
**Decision:** Evaluate implementation quality and identify gaps
**Status:** Proposed
**Reviewed by:** (Pending OpenAI GPT-5, Google Gemini 3 Pro Preview)

---

## Executive Summary

The domain skill migration split the 887-line monolithic `bazinga-db` skill into 4 domain-focused skills:
- **bazinga-db-core** - Session lifecycle, state, dashboard (65 invocations)
- **bazinga-db-workflow** - Task groups, plans, success criteria (45 invocations)
- **bazinga-db-agents** - Logs, reasoning, tokens, events (76 invocations)
- **bazinga-db-context** - Context packages, error patterns, strategies (15 invocations)

This review identifies **3 critical issues**, **2 medium issues**, and **4 minor issues**.

---

## Critical Issues 🔴

### Issue 1: Undocumented Event Type - `investigation_iteration`

**Severity:** HIGH
**Risk:** Agent confusion, silent failures

**Problem:**
The `bazinga-db-agents` SKILL.md documents these event types:
```
- scope_change
- role_violation
- tl_issues
- tl_issue_responses
- tl_verdicts
```

But `investigator.md` and `investigation_loop.md` use a NEW event type:
```
Event Type: investigation_iteration
```

This event type is **NOT documented** in the skill file. Agents using the skill won't know this is a valid event type.

**Impact:**
- Investigator agent may fail silently or get confused
- No documentation for other agents to query investigation history
- Inconsistent with documented event types

**Fix Required:**
Add `investigation_iteration` to the Common event types section in `bazinga-db-agents/SKILL.md`

---

### Issue 2: Dual Investigation Tracking Systems

**Severity:** MEDIUM-HIGH
**Risk:** State confusion, inconsistent data

**Problem:**
Investigation progress is tracked in TWO places with different mechanisms:

| System | Location | Skill | Data Stored |
|--------|----------|-------|-------------|
| State-based | `save-state` | bazinga-db-core | `investigation_state` with current_iteration, status |
| Event-based | `save-event` | bazinga-db-agents | `investigation_iteration` events with iteration logs |

The orchestrator uses **BOTH**:
1. `investigation_loop.md` saves state via `bazinga-db-core` (line 79)
2. `investigation_loop.md` saves events via `bazinga-db-agents` (line 171)

**Impact:**
- If one update fails, state is inconsistent
- No single source of truth for investigation progress
- Dashboard may show stale data if only one system is updated

**Mitigation:**
This is actually by design (state = current progress, events = audit trail), but should be documented explicitly.

---

### Issue 3: No Validation Script for Event Type Consistency

**Severity:** MEDIUM
**Risk:** Drift between documented and used event types

**Problem:**
The `validate-db-skill-migration.sh` script checks:
- Stale request phrasings
- Old-style skill invocations
- Domain skills exist
- Deprecated skill has notice

But it does **NOT** check:
- Event types used in agent files match documented types
- New event types are documented

**Impact:**
- Issue 1 (undocumented `investigation_iteration`) was not caught by validation
- Future event types could be added without documentation

**Fix Required:**
Add event type consistency check to validation script

---

## Medium Issues 🟡

### Issue 4: Missing `--payload-file` for save-event

**Severity:** MEDIUM
**Risk:** Security exposure of sensitive data

**Problem:**
The `save-reasoning` command has `--content-file` option to avoid exposing content in process table (`ps aux`). But `save-event` only supports inline JSON payload.

For `tl_issues` events with code snippets or `investigation_iteration` with sensitive findings, this could expose data.

**Current:**
```bash
save-event "{session_id}" "investigation_iteration" '{"findings": "SQL injection in auth.py"}'
```

This exposes the payload in process listings.

**Recommended:**
Add `--payload-file` option to `save-event` command for security parity with `save-reasoning`.

---

### Issue 5: Incomplete Domain Routing Documentation

**Severity:** MEDIUM
**Risk:** Agent confusion on which skill to use

**Problem:**
The deprecated `bazinga-db` skill has a routing table, but some edge cases are unclear:

| Command | Documented Domain | Potential Confusion |
|---------|-------------------|---------------------|
| `save-event` | bazinga-db-agents | Events about workflow (scope_change) could logically go to workflow |
| `update-context-references` | bazinga-db-context | Updates task_group table, could logically go to workflow |

**Impact:**
- Agents might invoke wrong skill for edge cases
- Current routing works but logic isn't intuitive

**Mitigation:**
Add "Why this domain?" explanations to routing table

---

## Minor Issues 🟢

### Issue 6: Validation Script Excludes Templates Directory

**Severity:** LOW

The validation script excludes `templates/` from consistency checks (line 113), but templates like `investigation_loop.md` are operational and should be validated.

**Current behavior:**
Templates in `OPERATIONAL_TEMPLATES` list ARE checked (explicit list), but new templates could be missed.

---

### Issue 7: No CLI Help for Domain-Specific Skills

**Severity:** LOW

`bazinga_db.py help` doesn't mention the domain skill split or suggest which domain skill to use for each command.

---

### Issue 8: Inconsistent Invocation Syntax Documentation

**Severity:** LOW

Some places show:
```
Skill(command: "bazinga-db-agents")
```

Others show:
```
Then invoke: `Skill(command: "bazinga-db-agents")`
```

The format is consistent, but surrounding text varies (request text vs. inline).

---

### Issue 9: Research Files Have Stale Patterns

**Severity:** INFO (expected)

Old `bazinga-db, please` patterns exist in `research/` folder. This is intentional (historical documents) and excluded by validation script.

---

## Backward Compatibility Assessment

### ✅ PRESERVED

1. **CLI Script Unchanged** - `bazinga_db.py` accepts all original commands
2. **Deprecated Skill Routes** - Old `bazinga-db` skill provides routing table
3. **Database Schema Unchanged** - No migrations needed
4. **Invocation Syntax Same** - `Skill(command: "skill-name")` format preserved

### ⚠️ POTENTIAL RISKS

1. **Stale Documentation** - If agent files still have old patterns, they may invoke deprecated skill
2. **Skill Discovery** - New agents might not know about domain split

### ✅ MITIGATIONS IN PLACE

1. Validation script catches stale patterns
2. Deprecated skill has DEPRECATED notice
3. All operational templates updated

---

## Token Impact Analysis

| Skill | Lines | Est. Tokens | Change |
|-------|-------|-------------|--------|
| bazinga-db-core | 169 | ~600 | NEW |
| bazinga-db-workflow | 170 | ~600 | NEW |
| bazinga-db-agents | 241 | ~850 | NEW |
| bazinga-db-context | 209 | ~750 | NEW |
| bazinga-db (deprecated) | 81 | ~300 | REDUCED from 887 |

**Net impact:** Instead of loading 887-line monolith, agents now load ~150-250 lines per domain. Significant token savings.

---

## Recommendations

### Critical (Must Fix)

1. **Add `investigation_iteration` to documented event types** in `bazinga-db-agents/SKILL.md`
   ```markdown
   - `investigation_iteration` - Investigator agent iteration progress
   ```

2. **Document dual tracking design** in investigation_loop.md header
   ```markdown
   ## State vs Events
   - State (save-state): Current investigation progress, resumable
   - Events (save-event): Immutable audit trail, queryable history
   ```

### Medium (Should Fix)

3. **Add event type validation** to `validate-db-skill-migration.sh`

4. **Add `--payload-file` option** to `save-event` for security parity

### Nice to Have

5. Update CLI help to mention domain split
6. Add "Why this domain?" to routing table

---

## Multi-LLM Review Integration

**Reviewed by:** OpenAI GPT-5 (2026-01-01)
**Gemini:** Skipped (ENABLE_GEMINI=false)

### OpenAI Key Findings

The OpenAI review identified these additional concerns:

#### Elevated to CRITICAL

1. **No Event Type Registry** - The root problem is broader than `investigation_iteration`: there's no central registry of event types with JSON schemas. This causes recurring drift.

2. **State+Event Dual-Write Has No Atomicity** - If `save-state` succeeds but `save-event` fails (or vice versa), UI and downstream logic will diverge. No compensating logic exists.

3. **No Redaction for save-event** - Reasoning paths are redacted, but events are not. Events can carry stack traces, PII, or secrets.

#### Additional Issues Identified

| Issue | Severity | Description |
|-------|----------|-------------|
| No schema validation | HIGH | Event payloads have no JSON Schema validation |
| No idempotency keys | MEDIUM | save-event dedup is implied but not enforced |
| No concurrency ordering | MEDIUM | Multiple agents can log events concurrently without sequence numbers |
| No data lifecycle/TTL | MEDIUM | No retention policy; DB growth will degrade performance |
| No observability/SLOs | LOW | No metrics on event/state latencies |

### Incorporated Feedback (REQUIRING USER APPROVAL)

**🔴 CHANGES REQUIRING USER APPROVAL:**

The following suggestions from OpenAI represent architectural changes that need explicit user approval before incorporating:

#### Change 1: Central Event Registry + Codegen
**Current:** Event types scattered across skill docs and agent files
**Proposed:** Create `bazinga/schemas/events/{event_type}.schema.json` for each event type, generate SKILL.md docs from registry
**Impact:** Requires new infrastructure, build scripts, and CI validation
**Do you approve?** [Yes/No/Modify]

#### Change 2: Atomic Dual-Write or Compensating Logic
**Current:** State and events written separately, no atomicity guarantees
**Proposed:** Either transaction wrapper OR combined "save-investigation-iteration" meta-command
**Impact:** Changes to bazinga_db.py, orchestrator templates
**Do you approve?** [Yes/No/Modify]

#### Change 3: Add Secret Redaction to save-event
**Current:** Only save-reasoning has redaction
**Proposed:** Apply same secret redaction pipeline to save-event payloads
**Impact:** Changes to bazinga_db.py save_event function
**Do you approve?** [Yes/No/Modify]

#### Change 4: Event Idempotency and Ordering
**Current:** No idempotency keys enforced
**Proposed:** Require idempotency_key (e.g., session|group|event_type|iteration), add sequence_no per group
**Impact:** Schema changes, API changes
**Do you approve?** [Yes/No/Modify]

### Rejected Suggestions (With Reasoning)

| Suggestion | Rejection Reason |
|------------|------------------|
| Single gateway skill with internal routing | Already deprecated bazinga-db serves this role; adds confusion |
| Typed SDK wrapper for agents | Over-engineering for current scale |
| Role-based access control for events | Not needed yet; adds complexity |

### Accepted Without Changes Required

These are documentation/minor fixes that can proceed:

1. ✅ Add `investigation_iteration` to documented event types
2. ✅ Document State vs Events design in investigation_loop.md
3. ✅ Add event type validation to validation script
4. ✅ Add `--payload-file` to save-event
5. ✅ Improve CLI help discoverability

---

## Updated Recommendations (Post-Review)

### Phase 1: Immediate Documentation Fixes (No User Approval Needed)

1. **Add `investigation_iteration` to bazinga-db-agents/SKILL.md**
2. **Add "State vs Events" documentation to investigation_loop.md**
3. **Update validation script to check event types**

### Phase 2: Security/Reliability Improvements (User Approval Pending)

4. **Add `--payload-file` to save-event** (security parity)
5. **Add secret redaction to save-event** (if approved)
6. **Add idempotency keys** (if approved)

### Phase 3: Architectural Improvements (User Approval Required)

7. **Central event registry** (if approved)
8. **Atomic dual-write** (if approved)

---

## Files Analyzed

- `.claude/skills/bazinga-db-core/SKILL.md`
- `.claude/skills/bazinga-db-workflow/SKILL.md`
- `.claude/skills/bazinga-db-agents/SKILL.md`
- `.claude/skills/bazinga-db-context/SKILL.md`
- `.claude/skills/bazinga-db/SKILL.md` (deprecated)
- `agents/investigator.md`
- `agents/orchestrator.md`
- `templates/investigation_loop.md`
- `scripts/validate-db-skill-migration.sh`
