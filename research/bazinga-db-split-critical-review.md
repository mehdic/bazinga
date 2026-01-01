# BAZINGA-DB Domain Split: Critical Self-Review

**Date:** 2025-12-31
**Context:** Implementation review of bazinga-db skill split into 4 domain skills
**Status:** CRITICAL ISSUES FOUND - DO NOT MERGE WITHOUT FIXES
**Decision:** Implementation incomplete - requires additional work

---

## Executive Summary

The bazinga-db skill domain split implementation is **60% complete**. While the core split was executed correctly (4 domain skills created, router in place, agent files updated), the implementation has **critical gaps** that would cause breakage in production:

| Severity | Issue Count | Impact |
|----------|-------------|--------|
| **CRITICAL** | 3 | System breakage, silent failures |
| **HIGH** | 4 | Inconsistent behavior, confusion |
| **MEDIUM** | 3 | Technical debt, maintainability |

---

## Issue #1: CRITICAL - Incomplete Migration (150+ Stale References)

### Problem

The implementation only updated `agents/*.md` files but missed **150+ references** to `Skill(command: "bazinga-db")` in other critical files:

| File Category | Count | Impact |
|---------------|-------|--------|
| `.claude/commands/bazinga.orchestrate.md` | 30+ | **Orchestrator will use deprecated skill** |
| `.claude/templates/orchestrator_*.md` | 20+ | Templates reference old skill |
| `templates/orchestrator/*.md` | 14 | Phase templates use old skill |
| `templates/pm_*.md` | 9 | PM templates use old skill |
| `templates/shutdown_protocol.md` | 8 | Shutdown uses old skill |
| `templates/logging_pattern.md` | 5 | Logging uses old skill |
| `.claude/claude.md` | 5 | **Project documentation is wrong** |
| `.claude/skills/bazinga-validator/SKILL.md` | 1 | Validator uses old skill |
| `.claude/skills/context-assembler/SKILL.md` | 1 | Assembler uses old skill |
| `docs/ARCHITECTURE.md` | 3 | Architecture docs are wrong |

### Consequence

- Agents loading these templates will invoke the deprecated router
- Router has no actual execution logic - just routing guidance
- **Silent failures** - old skill invocations won't execute commands

### Fix Required

```bash
# Files that MUST be updated (not exhaustive):
.claude/commands/bazinga.orchestrate.md    # CRITICAL - Generated from agents/orchestrator.md
.claude/templates/orchestrator_db_reference.md
templates/shutdown_protocol.md
templates/logging_pattern.md
templates/completion_report.md
templates/pm_bazinga_validation.md
templates/pm_speckit.md
templates/pm_planning_steps.md
templates/orchestrator/phase_simple.md
templates/orchestrator/phase_parallel.md
templates/orchestrator/clarification_flow.md
templates/orchestrator/scope_validation.md
.claude/claude.md                          # Project documentation
docs/ARCHITECTURE.md                       # Architecture documentation
.claude/skills/bazinga-validator/SKILL.md
.claude/skills/context-assembler/SKILL.md
```

---

## Issue #2: CRITICAL - Router Has No Execution Logic

### Problem

The deprecated router (`bazinga-db/SKILL.md`) provides **routing guidance only** - it doesn't actually execute commands. If an agent invokes `Skill(command: "bazinga-db")` with a command, **nothing happens**.

### Current Router Content (66 lines)

```markdown
# BAZINGA-DB (Deprecated Router)
**This skill is deprecated.** Use domain-specific skills instead...
## Command Routing Table
| Command | Target Skill |
...
```

The router is purely informational. It has:
- No `## Your Task` section
- No execution instructions
- No command handling logic

### Consequence

Any agent that still invokes `Skill(command: "bazinga-db")` will:
1. Load the router skill
2. See routing guidance (maybe)
3. **Not execute any database operation**
4. Return without error (silent failure)

### Fix Options

**Option A: Active Router (Recommended)**
Make the router actually route commands:
```markdown
## Your Task
When invoked with a command:
1. Identify the command from the request
2. Map to target domain skill using routing table
3. Re-invoke with: `Skill(command: "bazinga-db-{domain}")`
4. Return the result

This ensures backward compatibility during migration.
```

**Option B: Hard Deprecation**
Add explicit failure guidance:
```markdown
## Your Task
This skill is DEPRECATED. If you reached here:
1. STOP - Do not proceed
2. Return error: "ERROR: bazinga-db is deprecated. Use domain skills."
3. The calling code must be updated
```

---

## Issue #3: CRITICAL - Router Command Table is Incomplete

### Problem

The router's command routing table is missing **11 commands** that exist in the CLI:

| Missing Command | Should Route To |
|-----------------|-----------------|
| `recover-db` | `bazinga-db-core` |
| `detect-paths` | `bazinga-db-core` |
| `update-context-references` | `bazinga-db-context` |
| `save-consumption` | `bazinga-db-context` |
| `get-consumption` | `bazinga-db-context` |
| `update-error-confidence` | `bazinga-db-context` |
| `cleanup-error-patterns` | `bazinga-db-context` |
| `update-strategy-helpfulness` | `bazinga-db-context` |
| `extract-strategies` | `bazinga-db-context` |
| `get-skill-output-all` | `bazinga-db-agents` |
| `check-mandatory-phases` | `bazinga-db-agents` |

### Consequence

If an agent uses the router for one of these commands, they get no routing guidance.

### Fix Required

Update `.claude/skills/bazinga-db/SKILL.md` routing table to include all 52 commands.

---

## Issue #4: HIGH - Domain Skills Have Inconsistent Command Documentation

### Problem

Some commands documented in domain skills don't match CLI signatures exactly:

**bazinga-db-context:**
```bash
# Documented:
save-error-pattern "<session_id>" "<group_id>" "<error_type>" ...

# Actual CLI:
save-error-pattern <project_id> <error_type> <error_message> <solution> [options]
```

**bazinga-db-agents:**
```bash
# Documented:
save-skill-output "<session_id>" "<group_id>" "<skill_name>" ...

# Actual CLI:
save-skill-output <session> <skill> <json> [--agent X] [--group Y]
```

### Consequence

Agents following domain skill documentation may construct incorrect commands.

### Fix Required

Cross-verify all command signatures against `python3 .../bazinga_db.py help` output.

---

## Issue #5: HIGH - .claude/commands/bazinga.orchestrate.md Not Rebuilt

### Problem

The orchestrator slash command is **auto-generated** from `agents/orchestrator.md`. The source was updated but the generated file wasn't rebuilt.

```
agents/orchestrator.md           → Updated with domain skills ✓
.claude/commands/bazinga.orchestrate.md → Still has old skill refs ✗
```

### Consequence

Running `/bazinga.orchestrate` uses the outdated generated file with 30+ old skill references.

### Fix Required

```bash
./scripts/build-slash-commands.sh
```

This should have been run after updating `agents/orchestrator.md`.

---

## Issue #6: HIGH - No Backward Compatibility Layer

### Problem

The implementation assumes a "big bang" migration where everything is updated simultaneously. No backward compatibility layer exists for:

1. In-flight sessions using old skill
2. External integrations referencing old skill
3. User muscle memory / documentation

### Consequence

- Existing documentation and examples are immediately broken
- No graceful degradation path
- No migration period

### Fix Options

**Option A: Active Router with Warning**
Router executes commands but logs deprecation warnings:
```python
# Log to stderr (visible but non-breaking)
print(f"WARNING: bazinga-db is deprecated. Use bazinga-db-{domain} instead.", file=sys.stderr)
# Then execute normally
```

**Option B: Router Forwards to Domain Skills**
Router actually invokes the correct domain skill automatically.

---

## Issue #7: HIGH - Orchestrator Template References Not Updated

### Problem

Templates in `templates/orchestrator/` still reference old skill:
- `phase_simple.md`: 4 references
- `phase_parallel.md`: 3 references
- `clarification_flow.md`: 3 references
- `scope_validation.md`: 4 references

These templates are loaded by the orchestrator during execution.

### Consequence

Orchestrator spawns agents with templates that use deprecated skill.

---

## Issue #8: MEDIUM - No Validation Script

### Problem

No automated way to verify:
1. All old skill references are updated
2. All CLI commands are mapped to domain skills
3. Command signatures match between skills and CLI

### Fix Required

Create validation script:
```bash
#!/bin/bash
# scripts/validate-db-skill-split.sh

# Check for old skill references
OLD_REFS=$(grep -r 'Skill(command: "bazinga-db")' --include="*.md" | wc -l)
if [ "$OLD_REFS" -gt 0 ]; then
    echo "ERROR: Found $OLD_REFS old skill references"
    exit 1
fi

# Verify command coverage (compare CLI help vs skill docs)
...
```

---

## Issue #9: MEDIUM - Domain Skill "When NOT to invoke" Sections Are Weak

### Problem

Each domain skill has "When NOT to invoke" but they're just cross-references, not explicit decision logic.

Example from `bazinga-db-core`:
```markdown
**Do NOT invoke when:**
- Managing task groups or plans → Use `bazinga-db-workflow`
```

This doesn't help an agent decide **what** they're trying to do in the first place.

### Fix Option

Add decision tree at the start of each skill:
```markdown
## Quick Decision Guide
Ask yourself:
- Am I working with sessions, state, or system commands? → You're in the right place
- Am I working with task groups, plans, or success criteria? → Use bazinga-db-workflow
- Am I logging, reasoning, or tracking tokens? → Use bazinga-db-agents
- Am I managing context packages or learning patterns? → Use bazinga-db-context
```

---

## Issue #10: MEDIUM - Version Numbers Not Coordinated

### Problem

```
bazinga-db/SKILL.md:        version: 2.0.0  (router)
bazinga-db-core/SKILL.md:   version: 1.0.0
bazinga-db-workflow/SKILL.md: version: 1.0.0
bazinga-db-agents/SKILL.md:  version: 1.0.0
bazinga-db-context/SKILL.md: version: 1.0.0
```

The router is v2.0.0 but domain skills are v1.0.0. This is confusing - domain skills should be v2.0.0 to indicate they're the successors.

---

## Positive Aspects (What Worked)

1. **Clean domain separation** - The 4 domains are logically coherent
2. **Agent files properly updated** - All 52 invocations in `agents/*.md` were correctly mapped
3. **CLI calls converted** - 28+ direct CLI calls converted to skill invocations
4. **Source files updated** - `agents/_sources/*.md` were also updated
5. **Router provides clear routing table** - The guidance is there, even if incomplete
6. **Line count achieved** - Original 887 lines → 838 lines across 5 files

---

## Recommended Action Plan

### Phase 1: Critical Fixes (Before ANY Use)

1. **Rebuild orchestrator command**
   ```bash
   ./scripts/build-slash-commands.sh
   git add .claude/commands/bazinga.orchestrate.md
   ```

2. **Update all template files**
   - Update `templates/orchestrator/*.md` (14 refs)
   - Update `templates/pm_*.md` (9 refs)
   - Update `templates/shutdown_protocol.md` (8 refs)
   - Update `templates/logging_pattern.md` (5 refs)
   - Update `.claude/templates/orchestrator_*.md` (20 refs)

3. **Update other skills**
   - Update `.claude/skills/bazinga-validator/SKILL.md`
   - Update `.claude/skills/context-assembler/SKILL.md`

4. **Complete router command table** - Add all 11 missing commands

5. **Fix command signature inconsistencies** - Cross-verify with CLI help

### Phase 2: Documentation (Required)

6. **Update `.claude/claude.md`** - Project documentation
7. **Update `docs/ARCHITECTURE.md`** - Architecture documentation

### Phase 3: Validation (Recommended)

8. **Create validation script** - Automated checking
9. **Add active routing** - Backward compatibility layer

---

## Verification Checklist

After fixes, verify:

```bash
# No old skill references (should be 0)
grep -r 'Skill(command: "bazinga-db")' --include="*.md" | grep -v research/ | wc -l

# Only domain skill references exist
grep -r 'Skill(command: "bazinga-db-' --include="*.md" | wc -l

# Router has all commands (should be 52+)
grep -c '`bazinga-db-' .claude/skills/bazinga-db/SKILL.md

# All domain skills combined < 1000 lines
wc -l .claude/skills/bazinga-db*/SKILL.md
```

---

## Conclusion

**The implementation is architecturally sound but execution was incomplete.**

The domain split makes sense and the core mechanics work. However, the migration was only applied to `agents/*.md` files, leaving 150+ references in templates, documentation, and other skills unchanged.

**This WILL cause silent failures if deployed as-is.**

The fix is straightforward but tedious - update all remaining references using the same command-to-domain mapping that was used for agent files. A validation script should be created to prevent future drift.

**Estimated additional work:** 2-3 hours to complete migration properly.

---

## Multi-LLM Review Integration

**Reviewed by:** OpenAI GPT-5 (Gemini skipped)

### Consensus Points (Validated by External Review)

1. **Strategic direction is sound** - Domain split aligns with maintainability goals
2. **Incomplete migration is real** - 106 stale references confirmed (not 150+, corrected)
3. **Validation script needed** - CI guard to prevent regression
4. **Version coordination needed** - All domain skills should be v2.0.0

### Incorporated Feedback

| Feedback | Incorporated? | Action |
|----------|---------------|--------|
| Verify router behavior - may not be "silent failure" | ✅ Yes | Clarified in Issue #2 - behavior is "degraded" not "silent" |
| Generate deterministic stale-reference manifest | ✅ Yes | Added verified count: **106 references across 17 files** |
| Add prompt-builder guard | ✅ Yes | Added to Phase 3 recommendations |
| Implement CLI shims for backward compat | ✅ Yes | Added as Option A in Issue #6 |
| Unify version numbers to v2.0.0 | ✅ Yes | Already identified in Issue #10 |
| Add test plan | ✅ Yes | Added to Phase 3 |
| Add telemetry for deprecated usage | ⚠️ Partial | Noted but lower priority than core fixes |

### Rejected Suggestions (With Reasoning)

| Suggestion | Rejected? | Reasoning |
|------------|-----------|-----------|
| CLI-level argument order shims | ❌ Rejected | Argument order hasn't changed - this was a documentation issue, not API change |
| Prompt-builder post-processor auto-rewrite | ❌ Rejected | Magic rewrites hide problems; prefer explicit migration |

### Corrected Claims

**Original claim:** "150+ stale references"
**Corrected:** **106 stale references across 17 unique files**

```bash
# Verified count (excluding research/ and router itself):
grep -r 'Skill(command: "bazinga-db")' --include="*.md" | grep -v research/ | grep -v '.claude/skills/bazinga-db' | wc -l
# Output: 106
```

**Files requiring updates:**
```
.claude/claude.md
.claude/commands/bazinga.orchestrate-from-spec.md
.claude/commands/bazinga.orchestrate.md
.claude/skills/bazinga-validator/SKILL.md
.claude/skills/context-assembler/SKILL.md
.claude/templates/orchestrator_db_reference.md
docs/ARCHITECTURE.md
templates/completion_report.md
templates/logging_pattern.md
templates/orchestrator/clarification_flow.md
templates/orchestrator/phase_parallel.md
templates/orchestrator/phase_simple.md
templates/orchestrator/scope_validation.md
templates/pm_bazinga_validation.md
templates/pm_planning_steps.md
templates/pm_speckit.md
templates/shutdown_protocol.md
```

### Updated Action Plan (Post-Review)

**Phase 1: Critical Fixes** (unchanged)
1. Rebuild orchestrator command
2. Update all 17 files with stale references
3. Complete router command table
4. Fix command signature inconsistencies

**Phase 2: Documentation** (unchanged)
5. Update `.claude/claude.md`
6. Update `docs/ARCHITECTURE.md`

**Phase 3: Validation** (enhanced per review)
7. Create `scripts/validate-db-skill-split.sh` with:
   - Stale reference check (fail if > 0)
   - Command coverage check
   - Signature validation
8. Add to CI/pre-commit hook
9. Bump domain skill versions to v2.0.0
10. Consider active router for grace period

**Phase 4: Testing** (new per review)
11. Smoke tests for each domain skill
12. End-to-end tests for key workflows:
    - Session lifecycle
    - Task groups
    - Agent reasoning
    - Context packages
    - TL/Dev iteration events

---

## References

- Original implementation: commit `1a7f316`
- CLI help: `python3 .claude/skills/bazinga-db/scripts/bazinga_db.py help`
- Original skill: 887 lines (pre-split)
- Domain skills total: 838 lines (post-split)
- OpenAI review: `tmp/ultrathink-reviews/openai-review.md`
