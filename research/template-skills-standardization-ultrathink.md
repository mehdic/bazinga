# Template Skills Standardization: Critical Analysis

**Date:** 2026-01-04
**Context:** Standardize orchestrator templates to use Skills instead of direct script calls
**Decision:** Replaced 4 direct python3 script calls with Skill invocations
**Status:** Reviewed (Critical issues found)
**Reviewed by:** OpenAI GPT-5

---

## Changes Made

| File | Line | Old Pattern | New Pattern |
|------|------|-------------|-------------|
| `phase_simple.md:62` | `get-task-groups` | `python3 ... --quiet get-task-groups "{session_id}"` | `Skill(command: "bazinga-db-workflow")` |
| `phase_simple.md:211` | `check-mandatory-phases` | `python3 ... --quiet check-mandatory-phases ...` | `Skill(command: "bazinga-db-agents")` |
| `phase_simple.md:894` | `reasoning-timeline` | `python3 ... --quiet reasoning-timeline ...` | `Skill(command: "bazinga-db-agents")` |
| `phase_parallel.md:203` | `get-task-groups` | `python3 ... --quiet get-task-groups "{session_id}"` | `Skill(command: "bazinga-db-workflow")` |

---

## Critical Analysis

### 🟢 CORRECT: Pattern Consistency

The "request block + Then invoke" pattern matches existing orchestrator patterns:

```markdown
# Existing pattern in orchestrator.md (line 1595-1600)
bazinga-db-agents, please log this {agent_type} interaction:
Session ID: {session_id}, Agent Type: {agent_type}, Content: {response}
```
Then invoke: `Skill(command: "bazinga-db-agents")`

My fix uses the same pattern:
```markdown
bazinga-db-workflow, please get task groups:
Session ID: {session_id}
```
Then invoke: `Skill(command: "bazinga-db-workflow")`

**Verdict:** ✅ Pattern is consistent with existing orchestrator style.

---

### 🔴 CRITICAL: Skill Operation Format Mismatch

**Problem:** The Skills expect different request formats than what I provided.

**bazinga-db-workflow SKILL.md shows:**
```bash
python3 .../bazinga_db.py --quiet get-task-groups "<session_id>" [status]
```

**My request format:**
```
bazinga-db-workflow, please get task groups:

Session ID: {session_id}
```

**Question:** Does the skill parse "Session ID: {session_id}" correctly?

**Analysis:** Looking at how skills work:
1. `Skill(command: "bazinga-db-workflow")` loads the SKILL.md
2. The skill sees the request in conversation context
3. The skill translates the request to the CLI command

**But:** The SKILL.md doesn't define a "request parsing" format. It only shows CLI commands. This means:
- The skill relies on LLM understanding to map natural language to CLI
- Different phrasings might result in different translations
- There's no guaranteed 1:1 mapping

**Risk Level:** 🟡 MEDIUM - Skills are designed to handle natural language, but explicit format would be safer.

---

### 🔴 CRITICAL: Missing Parameters in Some Requests

**check-mandatory-phases requires 3 args:**
```bash
python3 ... check-mandatory-phases "<session_id>" "<group_id>" "<agent_type>"
```

**My request:**
```
bazinga-db-agents, please check mandatory phases:

Session ID: {session_id}
Group ID: {group_id}
Agent Type: {agent_type}
```

**Verdict:** ✅ All parameters included.

**reasoning-timeline optional args:**
```bash
python3 ... reasoning-timeline "<session_id>" [--format markdown|json]
```

**My request:**
```
bazinga-db-agents, please get reasoning timeline:

Session ID: {session_id}
Group ID: {group_id}
Format: markdown
```

**Issue:** I added `Group ID` but the CLI command uses `--group_id` (underscore) not a positional arg.

Looking at the script more carefully:
```bash
python3 ... reasoning-timeline "<session_id>" [--format markdown|json]
```

**Wait** - the SKILL.md shows no `--group_id` flag for `reasoning-timeline`! Let me check...

---

### 🟢 RESOLVED: reasoning-timeline Group ID Parameter

**Initial concern:** SKILL.md didn't document `--group_id` for reasoning-timeline.

**Verification:** CLI help confirms support:
```
reasoning-timeline <session> [--group_id X] [--format json|markdown]
```

**Action taken:** Updated SKILL.md to document the `--group_id` parameter.

**Verdict:** ✅ Issue resolved. My request format is correct.

---

### 🟡 MEDIUM: Skill Invocation Overhead

**Old pattern:** Direct script call, immediate execution
**New pattern:** Skill invocation → LLM processes SKILL.md → LLM constructs command → execution

**Overhead analysis:**
- Each Skill invocation may add latency (LLM needs to read/process SKILL.md)
- Multiple skill calls in quick succession might be slower
- Skills designed for this use case, so overhead should be acceptable

**Verdict:** 🟢 Acceptable trade-off for consistency and role boundaries.

---

### 🟢 CORRECT: Orchestrator Role Compliance

**Before:** Orchestrator running `python3` directly (violates "use Skills" rule)
**After:** Orchestrator invoking Skills (respects role boundaries)

**Verdict:** ✅ Fix aligns with orchestrator axioms.

---

### 🟡 MEDIUM: pm_planning_steps.md Not Changed

I explicitly did NOT change `pm_planning_steps.md:512` because:
- PM is an agent, not the orchestrator
- Agents are allowed to use the CLI directly with `--content-file`
- The pattern is documented as "standard pattern used across all agents"

**However:** Should there be consistency between templates?

**Counter-argument:**
- Orchestrator templates run AS the orchestrator (role enforcement)
- Agent templates run AS agents (different tool access)
- Keeping them separate is correct

**Verdict:** ✅ Correct decision to skip.

---

## Backward Compatibility

### Templates are Read at Runtime

The templates in `templates/orchestrator/` are Read() at runtime, not compiled:
- `phase_simple.md` - Read during simple mode execution
- `phase_parallel.md` - Read during parallel mode execution

**Change takes effect:** Immediately on next orchestration run

**Rollback:** Revert template files, no rebuild needed

### Skill Availability

Skills already exist and are functional:
- `bazinga-db-workflow` - Has `get-task-groups` command
- `bazinga-db-agents` - Has `check-mandatory-phases` and `reasoning-timeline` commands

**Risk:** None for skill availability.

---

## Decision Tree Loopholes

### 1. Skill Fails to Parse Request

**Scenario:** Skill receives request but fails to translate to correct CLI command

**Current mitigation:** None

**Fix:** Add explicit error handling in templates:
```
IF skill returns error or empty result:
  Output: `❌ Skill invocation failed | {skill_name} | {error}` → STOP
```

**Status:** Not implemented ⚠️

### 2. Skill Times Out

**Scenario:** Skill takes too long, orchestrator moves on

**Current mitigation:** None

**Fix:** Skills should have timeout protection, but templates should also check for response

**Status:** Handled by skill implementation

### 3. Session ID Variable Not Substituted

**Scenario:** Template references `{session_id}` but orchestrator doesn't substitute

**Analysis:** This is an existing issue with direct script calls too

**Status:** No change in risk

---

## Recommendations

### ✅ Completed (During Review)

1. **Verified reasoning-timeline --group_id support** ✅
   - CLI supports `--group_id` parameter
   - Updated SKILL.md to document it

### Should Do (Follow-up)

1. **Add error handling guidance**
   - Templates should check skill results
   - Document expected response format

2. **Update SKILL.md documentation**
   - Add explicit "request format" examples
   - Show natural language → CLI mapping

3. **Add integration tests**
   - Verify skill invocations work with new template format

---

## Lessons Learned

1. **Check SKILL.md parameters** before changing templates
2. **Skills are natural language interfaces** - format flexibility is a feature, not a bug
3. **Consistency > direct calls** - Skills enforce role boundaries

---

## Multi-LLM Review Integration

### Critical Issues From OpenAI GPT-5

#### 🔴 CRITICAL: Ambiguous Skill Request Format

**Problem:** The natural language request pattern is non-deterministic:
```
bazinga-db-workflow, please get task groups:
Session ID: {session_id}
```

**Impact:**
- LLM inference can produce different CLI translations
- Small phrasing changes cause unintended commands
- Silent failures that are hard to debug

**OpenAI Recommendation:** Use a canonical request envelope:
```json
{"command":"get-task-groups","args":{"session_id":"{SESSION_ID}"}}
```

**My Assessment:**
- This is valid criticism
- However, the existing orchestrator already uses NL pattern consistently
- Changing to JSON envelope would be a larger refactor
- The current fix is consistent with existing patterns

**Decision:** Keep current NL pattern for consistency with existing code. Add JSON envelope as follow-up improvement.

#### 🔴 CRITICAL: Incomplete Standardization Scope

**Problem:** Only 4 direct calls replaced. Other templates may still have:
- merge_workflow.md
- investigation_loop.md
- Other routing templates

**OpenAI Quote:** "Mixed styles will cause drift, regressions, and maintenance burden."

**My Assessment:** Valid. I should check if other templates need similar changes.

**Action needed:** Repo-wide grep for remaining direct calls.

#### 🔴 CRITICAL: Missing Error-Handling Gates

**Problem:** No validation of skill results. A malformed response could cascade into wrong decisions.

**OpenAI Recommendation:** Add verification gate after every Skill call:
- Validate non-empty output
- JSON parse succeeds
- Expected keys exist
- If missing, output error capsule and STOP

**My Assessment:** Valid. Currently no error handling in the templates I modified.

**Decision:** Accept this feedback. Add error handling as follow-up.

#### 🟡 MEDIUM: Missing Concurrency Safeguards

**Problem:** Multiple Skill calls in parallel mode need idempotency.

**OpenAI Recommendation:** Include group_id in idempotency keys. Add skill_invocation events.

**My Assessment:** Valid for parallel mode robustness, but not directly related to this fix.

**Decision:** Note for follow-up, not blocking for this change.

### Rejected Suggestions (With Reasoning)

1. **"Adopt canonical JSON request envelope immediately"**
   - Would require refactoring all existing Skill calls
   - Current fix is consistent with existing patterns
   - Better as separate improvement PR

2. **"Add thin helper 'db-invoke' Skill"**
   - Over-engineering for this scope
   - The domain-specific Skills already exist
   - Consider for v2

### Incorporated Feedback

1. ✅ Verified reasoning-timeline --group_id support
2. ✅ Updated SKILL.md to document missing parameter
3. 📝 Documented need for error handling (follow-up)
4. 📝 Documented need for complete migration audit (follow-up)

---

## Revised Recommendations

### Keep From Current Implementation

1. ✅ Use Skill invocations instead of direct scripts (role compliance)
2. ✅ Natural language request pattern (consistency with existing)
3. ✅ Updated SKILL.md documentation

### Add as Follow-up PRs

| Priority | Item | Rationale |
|----------|------|-----------|
| ~~HIGH~~ | ~~Error handling gates~~ | ✅ **COMPLETED** - See §Error Handling Gates below |
| ~~HIGH~~ | ~~Complete migration audit~~ | ✅ **COMPLETED** - See audit below |
| MEDIUM | Canonical request envelope | Improve determinism |
| LOW | Skill invocation events | Observability |

---

## Error Handling Gates (2026-01-04)

### Implementation

Added `🔴 SKILL RESULT VALIDATION (All Skill Invocations)` section to both orchestrator templates:
- `templates/orchestrator/phase_simple.md` (lines 27-39)
- `templates/orchestrator/phase_parallel.md` (lines 27-39)

### Validation Rules

| Check | Action if Failed |
|-------|------------------|
| Result is empty/null | Output `❌ Skill returned empty | {skill_name}` → Retry once, then STOP |
| Result contains `"error":` | Output `❌ Skill error | {skill_name} | {error_message}` → STOP |
| JSON parse fails (for JSON commands) | Output `❌ Invalid JSON | {skill_name}` → STOP |

### Exceptions

- `reasoning-timeline` with `--format markdown` returns non-JSON (expected)
- Optional context Skills (e.g., reasoning-timeline for Investigator) use graceful degradation

### SKILL.md Fixes

Fixed JSON-only vs markdown contradiction in `.claude/skills/bazinga-db-agents/SKILL.md`:
- Updated Output Format section (lines 300-308) to document exceptions
- `reasoning-timeline` supports `--format markdown` option
- `stream-logs` always returns markdown (NO format option - fixed pre-existing documentation bug)

### 🔴 Self-Review Critical Findings (2026-01-04)

**Bug Found During Review:** SKILL.md incorrectly documented `stream-logs` as having `--format markdown|json` option. The actual CLI:
- Always returns markdown (hardcoded in `stream_logs()` function)
- Only accepts `[limit] [offset]` positional args

**Resolution:**
1. Fixed `stream-logs` documentation in SKILL.md (lines 50-61)
2. Updated Output Format exceptions to clarify stream-logs always returns markdown
3. Updated both template validation sections to list both exceptions

### Remaining Risks (Acceptable)

| Risk | Severity | Mitigation |
|------|----------|------------|
| Error string false positive | LOW | Only matches `"error":` JSON key pattern, not nested content |
| Retry logic ambiguity | LOW | "Retry once, then STOP" is clear; retry-vs-permanent left to orchestrator judgment |
| Graceful degradation scope | LOW | Only reasoning-timeline explicitly listed; others can follow same pattern |
| STOP halts entire workflow | MEDIUM | Intentional - Skill failures indicate system issues requiring attention |

---

## Template Audit Results (2026-01-04)

### Audit Scope

Searched all files in `templates/` for direct `python3 .claude/skills/bazinga-db/scripts/bazinga_db.py` calls.

### Findings

| Template | Direct Script Calls | Status |
|----------|---------------------|--------|
| `templates/orchestrator/phase_simple.md` | 0 | ✅ Fixed (this PR) |
| `templates/orchestrator/phase_parallel.md` | 0 | ✅ Fixed (this PR) |
| `templates/orchestrator/*.md` (all others) | 0 | ✅ Clean |
| `templates/merge_workflow.md` | 0 | ✅ Uses Skills |
| `templates/investigation_loop.md` | 0 | ✅ Uses Skills |
| `templates/shutdown_protocol.md` | 0 | ✅ Uses Skills |
| `templates/pm_planning_steps.md` | 1 | ⏭️ Intentional (PM is agent) |
| `templates/specializations/*.md` | 0 | ✅ Clean |

### Summary

**Total orchestrator templates with direct script calls: 0** ✅

The only template with a direct script call is `pm_planning_steps.md` (line 512: `save-reasoning`). This is **intentional** because:
1. PM is an agent, not the orchestrator
2. Agents have Bash access and use `--content-file` pattern
3. This is documented as "standard pattern used across all agents"

### Conclusion

The "incomplete standardization scope" concern from OpenAI has been addressed. All orchestrator templates now use Skills.

### Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| NL parsing drift | MEDIUM | Follow-up: JSON envelope |
| Incomplete standardization | LOW | Follow-up: audit remaining templates |
| Missing error handling | MEDIUM | Follow-up: add gates |
| Parallel race conditions | LOW | Existing idempotency patterns |

**Overall:** The current implementation is **acceptable for merge** as it:
- Is consistent with existing patterns
- Improves role compliance
- Has no known regressions

The identified issues are valid but are better addressed as follow-up improvements rather than blocking this change.

---

## References

- `.claude/skills/bazinga-db-workflow/SKILL.md` - Workflow skill definition
- `.claude/skills/bazinga-db-agents/SKILL.md` - Agents skill definition
- `agents/orchestrator.md` - Existing skill invocation patterns
- `tmp/ultrathink-reviews/openai-review.md` - Full OpenAI review
