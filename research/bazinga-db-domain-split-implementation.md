# Bazinga-DB Domain Split: Implementation Strategy

**Date:** 2025-12-30 (Updated after main merge)
**Context:** Splitting bazinga-db into domain-focused skills while maintaining shared Python infrastructure
**Decision:** Keep scripts in original location, create domain SKILL.md files only
**Status:** Ready for Final Approval

---

## Executive Summary

**The Python script (`bazinga_db.py`) does NOT move.** All 57+ files that reference it continue to work unchanged. We only create new SKILL.md files for each domain, all pointing to the same script.

---

## Critical Design Decision: Script Location

### The Problem

The path `.claude/skills/bazinga-db/scripts/bazinga_db.py` is referenced in **57+ files**:
- 10 agent files (developer.md, pm, qa, tech lead, etc.)
- 8 other skills (validator, context-assembler, lint-check, etc.)
- 4 templates (orchestrator phases, pm planning, tech lead)
- 35+ research/test/documentation files

### Options Evaluated

| Option | Description | Files Changed | Risk |
|--------|-------------|---------------|------|
| **A: Keep in original** | Scripts stay in `bazinga-db/scripts/` | 0 | ✅ None |
| B: Move to shared dir | Create `.claude/shared-scripts/` | 57+ | ❌ High |
| C: Move to core skill | Put in `bazinga-db-core/scripts/` | 57+ | ❌ High |

### Decision: Option A - Scripts Stay

**Zero path changes required.** The original `bazinga-db` skill directory becomes the "infrastructure" home for:
- `scripts/bazinga_db.py` - The main CLI
- `scripts/init_db.py` - Database initialization
- `scripts/init_session.py` - Session creation helper
- `references/schema.md` - Schema documentation
- `references/command_examples.md` - Full command reference

The original `SKILL.md` becomes a **deprecated routing skill** that directs agents to the appropriate domain skill.

---

## Architecture Overview

```
.claude/skills/
├── bazinga-db/                    # INFRASTRUCTURE (scripts home)
│   ├── SKILL.md                   # DEPRECATED - Router to domain skills (~50 lines)
│   ├── scripts/                   # SHARED - All domain skills use these
│   │   ├── bazinga_db.py         # Main CLI (unchanged)
│   │   ├── init_db.py            # DB init (unchanged)
│   │   └── init_session.py       # Session init (unchanged)
│   └── references/                # SHARED - Referenced by all domain skills
│       ├── schema.md             # Full schema docs
│       └── command_examples.md   # Full command examples
│
├── bazinga-db-core/               # Domain: Sessions, State, Dashboard
│   └── SKILL.md                   # ~180 lines
│
├── bazinga-db-workflow/           # Domain: Task Groups, Plans, Criteria
│   └── SKILL.md                   # ~200 lines
│
├── bazinga-db-agents/             # Domain: Logs, Reasoning, Tokens, Skill Output
│   └── SKILL.md                   # ~220 lines
│
└── bazinga-db-context/            # Domain: Context Packages, Consumption
    └── SKILL.md                   # ~150 lines
```

**Note:** `bazinga-db-learning` (error patterns, strategies) merged into `bazinga-db-context` to reduce skill count to 4.

---

## Domain Skill Specifications

### 1. bazinga-db-core (~180 lines)

**Purpose:** Session lifecycle and system operations

**Commands:**
| Command | Description |
|---------|-------------|
| `create-session` | Initialize new orchestration session |
| `get-session` | Get session details |
| `list-sessions` | List recent sessions |
| `update-session-status` | Update session status |
| `save-state` | Save PM/orchestrator state snapshot |
| `get-state` | Get latest state snapshot |
| `dashboard-snapshot` | Get complete dashboard data |
| `query` | Execute custom SELECT query |
| `integrity-check` | Check database integrity |
| `recover-db` | Attempt database recovery |
| `detect-paths` | Show auto-detected paths |

**Primary Users:** Orchestrator, Dashboard

**Description for frontmatter:**
```yaml
description: Session lifecycle and system operations. Use when creating sessions, saving state, or getting dashboard data.
```

---

### 2. bazinga-db-workflow (~200 lines)

**Purpose:** Task management and planning

**Commands:**
| Command | Description |
|---------|-------------|
| `create-task-group` | Create task group with specializations |
| `update-task-group` | Update task group fields |
| `get-task-groups` | Get task groups by session |
| `save-development-plan` | Save PM development plan |
| `get-development-plan` | Get development plan |
| `update-plan-progress` | Update plan phase status |
| `save-success-criteria` | Save success criteria |
| `get-success-criteria` | Get success criteria |
| `update-success-criterion` | Update criterion status |

**Primary Users:** Project Manager, Orchestrator

**Description for frontmatter:**
```yaml
description: Task groups and development planning. Use when managing task groups, plans, or success criteria.
```

---

### 3. bazinga-db-agents (~220 lines)

**Purpose:** Agent interactions and tracking

**Commands:**
| Command | Description |
|---------|-------------|
| `log-interaction` | Log agent interaction |
| `stream-logs` | Stream logs in markdown |
| `save-reasoning` | Save agent reasoning (auto-redacts secrets) |
| `get-reasoning` | Get reasoning entries |
| `reasoning-timeline` | Get chronological reasoning timeline |
| `check-mandatory-phases` | Check if mandatory phases documented |
| `log-tokens` | Log token usage |
| `token-summary` | Get token summary |
| `save-skill-output` | Save skill output |
| `get-skill-output` | Get latest skill output |
| `get-skill-output-all` | Get all skill outputs |
| `check-skill-evidence` | Check for recent skill evidence |
| `save-event` | Save generic event |
| `get-events` | Get events by session |

**Primary Users:** All agents (Developer, QA, Tech Lead, etc.)

**Description for frontmatter:**
```yaml
description: Agent logs, reasoning, and token tracking. Use when logging interactions, saving reasoning, or tracking tokens.
```

---

### 4. bazinga-db-context (~150 lines)

**Purpose:** Context engineering and learning

**Commands:**
| Command | Description |
|---------|-------------|
| `save-context-package` | Save context package |
| `get-context-packages` | Get context packages for agent spawn |
| `mark-context-consumed` | Mark package as consumed |
| `update-context-references` | Update task group context references |
| `save-consumption` | Save consumption record |
| `get-consumption` | Get consumption records |
| `save-error-pattern` | Capture error pattern |
| `get-error-patterns` | Query error patterns |
| `update-error-confidence` | Adjust pattern confidence |
| `cleanup-error-patterns` | Remove expired patterns |
| `save-strategy` | Save strategy from success |
| `get-strategies` | Get strategies |
| `update-strategy-helpfulness` | Increment helpfulness |
| `extract-strategies` | Extract strategies from reasoning |

**Primary Users:** Requirements Engineer, Developer, Learning System

**Description for frontmatter:**
```yaml
description: Context packages and learning patterns. Use when managing context packages, error patterns, or strategies.
```

---

## Deprecated Router Skill (bazinga-db)

The original `bazinga-db/SKILL.md` becomes a minimal router:

```markdown
---
name: bazinga-db
description: DEPRECATED - Use domain-specific skills instead. Routes to bazinga-db-core, bazinga-db-workflow, bazinga-db-agents, or bazinga-db-context.
version: 2.0.0
allowed-tools: [Bash, Read]
---

# BAZINGA-DB (Deprecated Router)

⚠️ **This skill is deprecated.** Use domain-specific skills instead:

| Domain | Skill | Use For |
|--------|-------|---------|
| Sessions & State | `bazinga-db-core` | Sessions, state, dashboard |
| Tasks & Plans | `bazinga-db-workflow` | Task groups, plans, criteria |
| Agent Tracking | `bazinga-db-agents` | Logs, reasoning, tokens |
| Context & Learning | `bazinga-db-context` | Context packages, patterns |

## Quick Reference

**Script location:** `.claude/skills/bazinga-db/scripts/bazinga_db.py`
**Full command help:** `python3 .../bazinga_db.py help`
**Schema docs:** `.claude/skills/bazinga-db/references/schema.md`
**Command examples:** `.claude/skills/bazinga-db/references/command_examples.md`

## If You're Here By Mistake

1. Identify what you're trying to do
2. Invoke the correct domain skill:
   - Session ops? → `Skill(command: "bazinga-db-core")`
   - Task groups? → `Skill(command: "bazinga-db-workflow")`
   - Logging/reasoning? → `Skill(command: "bazinga-db-agents")`
   - Context packages? → `Skill(command: "bazinga-db-context")`
```

---

## Files to Create/Modify

### Files to CREATE (4 new skills)

| File | Lines | Description |
|------|-------|-------------|
| `.claude/skills/bazinga-db-core/SKILL.md` | ~180 | Core domain skill |
| `.claude/skills/bazinga-db-workflow/SKILL.md` | ~200 | Workflow domain skill |
| `.claude/skills/bazinga-db-agents/SKILL.md` | ~220 | Agents domain skill |
| `.claude/skills/bazinga-db-context/SKILL.md` | ~150 | Context domain skill |

### Files to MODIFY

| File | Skill Invocations | CLI Calls | Change | Risk |
|------|-------------------|-----------|--------|------|
| `.claude/skills/bazinga-db/SKILL.md` | - | - | Replace 887-line monolith with ~50-line router | Low |
| `.claude/claude.md` | - | - | Update skill references in "NEVER Use Inline SQL" section | Low |
| `agents/orchestrator.md` | 34 | 5 | Update skill invocations + convert CLI calls | Medium |
| `agents/investigator.md` | 10 | 2 | Update skill invocations + convert CLI calls | Medium |
| `agents/orchestrator_speckit.md` | 5 | 0 | Update skill invocations | Low |
| `agents/tech_lead.md` | 1 | 4 | Update skill invocations + convert CLI calls | Low |
| `agents/qa_expert.md` | 1 | 2 | Update skill invocations + convert CLI calls | Low |
| `agents/requirements_engineer.md` | 1 | 2 | Update skill invocations + convert CLI calls | Low |
| `agents/developer.md` | 0 | 3 | Convert CLI calls to skill invocations | Low |
| `agents/senior_software_engineer.md` | 0 | 3 | Convert CLI calls to skill invocations | Low |
| `agents/project_manager.md` | 0 | 1 | Convert CLI calls to skill invocations | Low |
| `agents/_sources/developer.base.md` | 0 | 3 | Convert CLI calls to skill invocations | Low |
| `agents/_sources/senior.delta.md` | 0 | 3 | Convert CLI calls to skill invocations | Low |

**Post-Merge Totals:**
- **52 skill invocations** to update (across 6 agent files)
- **28 CLI calls** to convert to skill invocations (across 10 agent files)

### CLI Script Calls to Convert to Skill Invocations

These direct CLI calls must be replaced with skill invocations:

| Agent File | CLI Calls | Commands | Target Skill |
|------------|-----------|----------|--------------|
| `orchestrator.md` | 5 | `get-session`, `list-sessions` | `bazinga-db-core` |
| `tech_lead.md` | 4 | `save-reasoning`, `get-skill-output` | `bazinga-db-agents` |
| `developer.md` | 3 | `save-reasoning` | `bazinga-db-agents` |
| `senior_software_engineer.md` | 3 | `save-reasoning` | `bazinga-db-agents` |
| `_sources/developer.base.md` | 3 | `save-reasoning` | `bazinga-db-agents` |
| `_sources/senior.delta.md` | 3 | `save-reasoning` | `bazinga-db-agents` |
| `qa_expert.md` | 2 | `save-reasoning` | `bazinga-db-agents` |
| `investigator.md` | 2 | `save-reasoning` | `bazinga-db-agents` |
| `requirements_engineer.md` | 2 | `save-reasoning` | `bazinga-db-agents` |
| `project_manager.md` | 1 | `save-reasoning` | `bazinga-db-agents` |

**Total: 28 CLI calls to convert**

**Conversion pattern:**

```markdown
# ❌ BEFORE (direct CLI call)
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet save-reasoning \
  "{session_id}" "{group_id}" "developer" "understanding" "content..."

# ✅ AFTER (skill invocation)
Skill(command: "bazinga-db-agents")

Request: save-reasoning "{session_id}" "{group_id}" "developer" "understanding" "content..."
```

### Command-to-Skill Mapping for Agent Updates

When updating agent files, use this mapping:

| Command Pattern | Target Skill |
|-----------------|--------------|
| `create-session`, `get-session`, `list-sessions`, `update-session-status` | `bazinga-db-core` |
| `save-state`, `get-state`, `dashboard-snapshot` | `bazinga-db-core` |
| `query`, `integrity-check`, `recover-db`, `detect-paths` | `bazinga-db-core` |
| `create-task-group`, `update-task-group`, `get-task-groups` | `bazinga-db-workflow` |
| `save-development-plan`, `get-development-plan`, `update-plan-progress` | `bazinga-db-workflow` |
| `save-success-criteria`, `get-success-criteria`, `update-success-criterion` | `bazinga-db-workflow` |
| `log-interaction`, `stream-logs` | `bazinga-db-agents` |
| `save-reasoning`, `get-reasoning`, `reasoning-timeline`, `check-mandatory-phases` | `bazinga-db-agents` |
| `log-tokens`, `token-summary` | `bazinga-db-agents` |
| `save-skill-output`, `get-skill-output`, `get-skill-output-all`, `check-skill-evidence` | `bazinga-db-agents` |
| `save-event`, `get-events` | `bazinga-db-agents` |
| `save-context-package`, `get-context-packages`, `mark-context-consumed`, `update-context-references` | `bazinga-db-context` |
| `save-consumption`, `get-consumption` | `bazinga-db-context` |
| `save-error-pattern`, `get-error-patterns`, `update-error-confidence`, `cleanup-error-patterns` | `bazinga-db-context` |
| `save-strategy`, `get-strategies`, `update-strategy-helpfulness`, `extract-strategies` | `bazinga-db-context` |

### Files with NO CHANGE

| File | Reason |
|------|--------|
| `bazinga/skills_config.json` | Infrastructure skills, not configurable tools |
| Agent files (`agents/*.md`) | Skills auto-discovered, no explicit references needed |
| Installer (`src/bazinga_cli/__init__.py`) | Auto-copies all skill directories |

### Files to VERIFY (No Changes, Just Confirm)

These files reference the script path - verify they still work:

| Category | Files | Expected Impact |
|----------|-------|-----------------|
| Agent files | 10 files | None - path unchanged |
| Other skills | 8 files | None - path unchanged |
| Templates | 4 files | None - path unchanged |
| Tests | 5 files | None - path unchanged |

---

## Implementation Order

### Phase 1: Create Infrastructure (No Breaking Changes)

1. **Create 4 new skill directories** with SKILL.md files
   - Each references same script path
   - Each has focused documentation for its domain
   - All coexist with original bazinga-db

2. **Test new skills work**
   - Invoke each skill manually
   - Verify commands execute correctly

### Phase 2: Update Configuration

3. **Update skills_config.json**
   - Add entries for 4 new skills
   - Keep bazinga-db entry (for backward compatibility)

4. **Update .claude/claude.md**
   - Add domain skills to skill references
   - Note deprecation of original

### Phase 3: Deprecate Original

5. **Replace bazinga-db SKILL.md**
   - Slim to ~50 line router
   - Point to domain skills
   - Keep scripts and references unchanged

### Phase 4: Verify

6. **Integration test**
   - Run full orchestration
   - Verify all database operations work
   - Check logs for any skill invocation errors

---

## SKILL.md Template Structure

Each domain skill follows this template:

```markdown
---
name: bazinga-db-{domain}
description: {Domain purpose}. Use when {trigger conditions}.
version: 1.0.0
allowed-tools: [Bash, Read]
---

# BAZINGA-DB {Domain} Skill

You are the bazinga-db-{domain} skill. {Role description}.

## When to Invoke This Skill

**Invoke when:**
- {Condition 1}
- {Condition 2}

**Do NOT invoke when:**
- {Exclusion 1} → Use bazinga-db-{other} instead

## Script Location

**Path:** `.claude/skills/bazinga-db/scripts/bazinga_db.py`

All commands use this script with `--quiet` flag:
```bash
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet <command> [args...]
```

## Commands

### {Command 1}
```bash
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet {command} {args}
```

{Brief description and key parameters}

### {Command 2}
...

## Output Format

Return ONLY raw JSON output. No formatting or commentary.

## Error Handling

{Brief error handling guidance}

## References

- Full schema: `.claude/skills/bazinga-db/references/schema.md`
- All commands: `.claude/skills/bazinga-db/references/command_examples.md`
- CLI help: `python3 .../bazinga_db.py help`
```

---

## Installer Impact

**Good news:** The CLI installer (`copy_skills` function) automatically copies all directories in `.claude/skills/`.

**No installer changes needed.** New skill directories will be picked up automatically:
- `bazinga-db-core/` → automatically copied
- `bazinga-db-workflow/` → automatically copied
- `bazinga-db-agents/` → automatically copied
- `bazinga-db-context/` → automatically copied

The installer iterates over `source_skills.iterdir()` and copies each skill directory, so new directories are included without code changes.

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Wrong skill invoked | Medium | Low | Clear descriptions + router skill |
| Missing command in domain | Low | Medium | Cross-reference all commands before writing |
| Path reference breaks | None | N/A | Script path unchanged |
| Agent confusion | Medium | Low | Good skill descriptions |
| skills_config.json error | Low | Medium | Test after config update |
| Installer missing skills | None | N/A | Auto-copies all skill dirs |

---

## Comprehensive Testing Plan

### Phase 1: Unit Tests (After Creating Skills)

**Test each domain skill in isolation:**

```bash
# Test bazinga-db-core
Skill(command: "bazinga-db-core") → create-session "test_123" "simple" "Test"
Skill(command: "bazinga-db-core") → get-session "test_123"
Skill(command: "bazinga-db-core") → save-state "test_123" "orchestrator" '{"test": true}'
Skill(command: "bazinga-db-core") → get-state "test_123" "orchestrator"
Skill(command: "bazinga-db-core") → dashboard-snapshot "test_123"

# Test bazinga-db-workflow
Skill(command: "bazinga-db-workflow") → create-task-group "GRP1" "test_123" "Test Group"
Skill(command: "bazinga-db-workflow") → get-task-groups "test_123"
Skill(command: "bazinga-db-workflow") → save-success-criteria "test_123" '[{"criterion":"Test","status":"pending"}]'
Skill(command: "bazinga-db-workflow") → get-success-criteria "test_123"

# Test bazinga-db-agents
Skill(command: "bazinga-db-agents") → log-interaction "test_123" "developer" "Test log" 1
Skill(command: "bazinga-db-agents") → save-reasoning "test_123" "GRP1" "developer" "understanding" "Test reasoning"
Skill(command: "bazinga-db-agents") → get-reasoning "test_123"
Skill(command: "bazinga-db-agents") → log-tokens "test_123" "developer" 1000

# Test bazinga-db-context
Skill(command: "bazinga-db-context") → save-context-package "test_123" "GRP1" "research" "/tmp/test.md" "developer" '["qa_expert"]' "high" "Test package"
Skill(command: "bazinga-db-context") → get-context-packages "test_123" "GRP1" "qa_expert"
```

**Success criteria:** All commands execute without errors, return expected JSON.

### Phase 2: Agent Invocation Tests (After Updating Agents)

**Verify each agent file has correct skill references:**

```bash
# Check no remaining old skill references
grep -l 'Skill(command: "bazinga-db")' agents/*.md
# Expected: No output (all references updated)

# Check no remaining direct CLI calls
grep -l 'python3.*bazinga_db\.py' agents/*.md
# Expected: No output (all CLI calls converted to skill invocations)

# Verify new references are valid
grep -oh 'Skill(command: "bazinga-db-[^"]*")' agents/*.md | sort | uniq -c
# Expected: bazinga-db-core, bazinga-db-workflow, bazinga-db-agents, bazinga-db-context
```

### Phase 3: Integration Test (Full Orchestration)

**Run the full BAZINGA integration test:**

```bash
# 1. Clear previous test data
rm -rf tmp/simple-calculator-app bazinga/bazinga.db bazinga/project_context.json

# 2. Run orchestration
/bazinga.orchestrate Implement the Simple Calculator App as specified in tests/integration/simple-calculator-spec.md
```

**Verification points during test:**
- [ ] Session created via `bazinga-db-core`
- [ ] Task groups created via `bazinga-db-workflow`
- [ ] Interactions logged via `bazinga-db-agents`
- [ ] Reasoning saved via `bazinga-db-agents`
- [ ] Success criteria saved via `bazinga-db-workflow`
- [ ] Context packages work via `bazinga-db-context`

### Phase 4: Post-Integration Verification

**Run ALL verification commands from project context:**

```bash
SESSION_ID=$(python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet list-sessions 1 | jq -r '.[0].session_id')

# Core operations
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet get-session "$SESSION_ID"

# Workflow operations
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet get-task-groups "$SESSION_ID"
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet get-success-criteria "$SESSION_ID"

# Agent operations
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet get-reasoning "$SESSION_ID"
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet reasoning-timeline "$SESSION_ID" --format markdown

# Full dashboard
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet dashboard-snapshot "$SESSION_ID"
```

**Success criteria:**
| Check | Expected |
|-------|----------|
| Session status | `completed` |
| Task groups | 1+ groups, all `completed` |
| Success criteria | 7 entries, all met |
| Reasoning entries | 8+ entries (2 per agent × 4 agents) |
| Files created | calculator.py, test_calculator.py, README.md |
| Tests passing | All pass |

### Phase 5: Cross-Domain Operation Tests

**Test operations that span multiple domains (common orchestrator patterns):**

```bash
# Simulate orchestrator session init flow
Skill(command: "bazinga-db-core") → create-session "flow_test" "parallel" "Test flow"
Skill(command: "bazinga-db-core") → save-state "flow_test" "orchestrator" '{"phase": "init"}'
Skill(command: "bazinga-db-workflow") → create-task-group "AUTH" "flow_test" "Authentication"
Skill(command: "bazinga-db-workflow") → save-success-criteria "flow_test" '[{"criterion":"Tests pass","status":"pending"}]'
Skill(command: "bazinga-db-agents") → log-interaction "flow_test" "pm" "Created task breakdown" 1

# Verify all operations succeeded
Skill(command: "bazinga-db-core") → dashboard-snapshot "flow_test"
```

### Phase 6: Error Handling Tests

**Test graceful failures:**

```bash
# Invalid session
Skill(command: "bazinga-db-core") → get-session "nonexistent"
# Expected: Error message, not crash

# Wrong domain skill for command (deprecated router should guide)
Skill(command: "bazinga-db") → save-reasoning ...
# Expected: Router message pointing to bazinga-db-agents

# Missing required args
Skill(command: "bazinga-db-workflow") → create-task-group
# Expected: Usage error, not crash
```

### Testing Checklist

- [ ] All 4 domain skills can be invoked
- [ ] Each skill's commands execute correctly
- [ ] No `Skill(command: "bazinga-db")` remains in agent files
- [ ] No `python3 .../bazinga_db.py` CLI calls remain in agent files
- [ ] Full integration test passes
- [ ] All 10 verification commands pass
- [ ] Cross-domain flows work
- [ ] Error handling is graceful
- [ ] Dashboard snapshot shows all data

---

## Rollback Plan

If issues occur after implementation:

1. **Quick rollback:** `git checkout HEAD~1 -- agents/ .claude/skills/bazinga-db/`
2. **Restore all agent files** to previous state
3. **Keep domain skills:** They don't break anything on their own
4. **Domain skills can coexist** with original bazinga-db during debugging

---

## Success Criteria

| Metric | Target |
|--------|--------|
| Each domain SKILL.md | < 250 lines |
| Original SKILL.md | < 60 lines (router) |
| Path changes | 0 files |
| Breaking changes | 0 |
| Skill invocation success | 100% |
| Integration test | Pass |

---

## Detailed File-by-File Changes

### NEW: `.claude/skills/bazinga-db-core/SKILL.md`

**Content outline:**
1. Frontmatter (name, description, version, allowed-tools)
2. Role description
3. When to invoke / when not to
4. Script location
5. Commands: create-session, get-session, list-sessions, update-session-status, save-state, get-state, dashboard-snapshot, query, integrity-check, recover-db, detect-paths
6. Output format
7. Error handling
8. References

### NEW: `.claude/skills/bazinga-db-workflow/SKILL.md`

**Content outline:**
1. Frontmatter
2. Role description
3. When to invoke / when not to
4. Script location
5. Commands: create-task-group, update-task-group, get-task-groups, save-development-plan, get-development-plan, update-plan-progress, save-success-criteria, get-success-criteria, update-success-criterion
6. Critical note: Argument order for task groups (`<group_id> <session_id>`)
7. Output format
8. Error handling
9. References

### NEW: `.claude/skills/bazinga-db-agents/SKILL.md`

**Content outline:**
1. Frontmatter
2. Role description
3. When to invoke / when not to
4. Script location
5. Commands: log-interaction, stream-logs, save-reasoning, get-reasoning, reasoning-timeline, check-mandatory-phases, log-tokens, token-summary, save-skill-output, get-skill-output, get-skill-output-all, check-skill-evidence, save-event, get-events
6. Reasoning phases reference (understanding, approach, decisions, risks, blockers, pivot, completion)
7. Output format
8. Error handling
9. References

### NEW: `.claude/skills/bazinga-db-context/SKILL.md`

**Content outline:**
1. Frontmatter
2. Role description
3. When to invoke / when not to
4. Script location
5. Commands: save-context-package, get-context-packages, mark-context-consumed, update-context-references, save-consumption, get-consumption, save-error-pattern, get-error-patterns, update-error-confidence, cleanup-error-patterns, save-strategy, get-strategies, update-strategy-helpfulness, extract-strategies
6. Context package types (research, failures, decisions, handoff, investigation)
7. Output format
8. Error handling
9. References

### MODIFY: `.claude/skills/bazinga-db/SKILL.md`

**Change:** Replace 887-line monolith with ~50-line deprecated router
**Content:** Deprecation notice + routing table + quick reference

### NO CHANGE: `bazinga/skills_config.json`

**These are INFRASTRUCTURE skills, NOT configurable tools.**

The bazinga-db domain skills work like the current `bazinga-db`:
- **NOT in skills_config.json** - That file is for optional/configurable skills
- **Always available** - Any agent can invoke them anytime
- **Never disabled** - Core system functionality
- **No permissions needed** - Skill exists = available to all

**Why this is correct:**
- `skills_config.json` controls optional tools like `lint-check`, `security-scan`
- Current `bazinga-db` is NOT in skills_config.json - it's just always there
- Domain skills are the same: infrastructure, not optional features
- Agents invoke whichever domain skill they need based on the task

**Result:** No changes to skills_config.json required!

### MODIFY: `.claude/claude.md`

**Section:** "🔴 CRITICAL: NEVER Use Inline SQL"
**Change:** Add note about domain skills:

```markdown
# ✅ ALWAYS Use bazinga-db Skills (Domain-Specific)

For sessions/state:     Skill(command: "bazinga-db-core")
For task groups/plans:  Skill(command: "bazinga-db-workflow")
For logs/reasoning:     Skill(command: "bazinga-db-agents")
For context packages:   Skill(command: "bazinga-db-context")

# Or use the CLI script directly:
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --quiet <command>
```

---

## Verification Checklist

After implementation, verify:

- [ ] All 4 domain skills can be invoked via `Skill(command: "bazinga-db-*")`
- [ ] Each skill's commands execute successfully
- [ ] Original script path still works in all 57+ files
- [ ] skills_config.json is valid JSON
- [ ] Integration test passes
- [ ] No orphaned commands (all 25+ commands covered by exactly one domain)

---

## Command Distribution Verification

Ensuring no commands are missed or duplicated:

| Command | Domain |
|---------|--------|
| create-session | core |
| get-session | core |
| list-sessions | core |
| update-session-status | core |
| save-state | core |
| get-state | core |
| dashboard-snapshot | core |
| query | core |
| integrity-check | core |
| recover-db | core |
| detect-paths | core |
| create-task-group | workflow |
| update-task-group | workflow |
| get-task-groups | workflow |
| save-development-plan | workflow |
| get-development-plan | workflow |
| update-plan-progress | workflow |
| save-success-criteria | workflow |
| get-success-criteria | workflow |
| update-success-criterion | workflow |
| log-interaction | agents |
| stream-logs | agents |
| save-reasoning | agents |
| get-reasoning | agents |
| reasoning-timeline | agents |
| check-mandatory-phases | agents |
| log-tokens | agents |
| token-summary | agents |
| save-skill-output | agents |
| get-skill-output | agents |
| get-skill-output-all | agents |
| check-skill-evidence | agents |
| save-event | agents |
| get-events | agents |
| save-context-package | context |
| get-context-packages | context |
| mark-context-consumed | context |
| update-context-references | context |
| save-consumption | context |
| get-consumption | context |
| save-error-pattern | context |
| get-error-patterns | context |
| update-error-confidence | context |
| cleanup-error-patterns | context |
| save-strategy | context |
| get-strategies | context |
| update-strategy-helpfulness | context |
| extract-strategies | context |

**Total: 45 commands across 4 domains**

---

## Timeline Estimate

| Phase | Tasks | Estimated Effort |
|-------|-------|------------------|
| Phase 1 | Create 4 SKILL.md files | ~2 hours |
| Phase 2 | Update configs | ~30 min |
| Phase 3 | Replace original SKILL.md | ~15 min |
| Phase 4 | Testing & verification | ~1 hour |

**Total: ~4 hours**

---

## User Decisions (Confirmed)

1. ✅ **Domain count:** 4 domains (core, workflow, agents, context) - approved
2. ✅ **Deprecation approach:** Keep original as router (not remove entirely)
3. ✅ **Learning commands:** Merged into context domain - approved
4. ✅ **skills_config.json:** No changes needed - these are infrastructure skills
5. ✅ **Agent file updates:** Update all 52 skill invocations + 28 CLI calls

---

## Post-Merge Analysis Notes

**Changes from main merge (2025-12-30):**

1. **SKILL.md grew from 850 → 887 lines** (+37 lines)
   - New TL review iteration tracking features
   - New event schemas for `tl_issues`, `tl_issue_responses`, `tl_verdicts`

2. **Skill invocations:** 52 (slightly lower than initial estimate of 58)
   - Most are in `orchestrator.md` (34) and `investigator.md` (10)

3. **CLI calls:** 28 (higher than initial estimate of 23)
   - `orchestrator.md` gained 5 CLI calls (session verification)
   - All need conversion to skill invocations per project standards

4. **New commands to distribute:**
   - TL review events → `bazinga-db-agents` (save-event, get-events already covered)
