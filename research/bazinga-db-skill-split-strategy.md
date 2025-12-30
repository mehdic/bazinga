# Bazinga-DB Skill Split Strategy: Ultrathink Analysis

**Date:** 2025-12-30
**Context:** The bazinga-db skill SKILL.md has grown to 850 lines (~26KB), exceeding the maximum file opening size. Need to split into smaller, manageable skills without breaking the system.
**Decision:** Documentation Slimming (Option 6) - NOT Domain Split
**Status:** Reviewed
**Reviewed by:** OpenAI GPT-5

---

## Problem Statement

The `bazinga-db` skill has become too large to be loaded by Claude Code's file opening mechanism. At 850 lines (~26KB), it's double the maximum file size. This creates:

1. **Invocation failures** - Skill cannot be fully loaded
2. **Lost context** - Truncated instructions lead to incorrect behavior
3. **Maintenance burden** - Monolithic file is hard to update

### Current Skill Inventory

The skill manages **25+ database commands** across **15 operation categories**:

| Category | Commands | Usage Frequency | Agent Users |
|----------|----------|-----------------|-------------|
| SESSION | 4 | High | Orchestrator |
| LOG | 2 | High | All agents |
| STATE | 2 | Medium | PM, Orchestrator |
| TASK GROUP | 3 | High | PM, Orchestrator |
| TOKEN | 2 | Low | Orchestrator |
| SKILL OUTPUT | 4 | Medium | All agents |
| DEVELOPMENT PLAN | 3 | Low | PM |
| SUCCESS CRITERIA | 3 | Medium | PM, Orchestrator |
| CONTEXT PACKAGE | 4 | Medium | RE, Developer, SSE |
| REASONING CAPTURE | 4 | High | All agents |
| ERROR PATTERN | 4 | Low | Learning system |
| CONSUMPTION SCOPE | 2 | Low | Context engineering |
| STRATEGIES | 4 | Low | Learning system |
| QUERY | 2 | Low | Dashboard, debugging |
| MAINTENANCE | 3 | Low | System admin |

---

## Solution Options Analyzed

### Option 1: CQRS-Style Split (Read/Write Separation)

**Concept:** Apply Command Query Responsibility Segregation pattern - separate read operations from write operations.

**Structure:**
```
.claude/skills/
├── bazinga-db-read/     # All queries/gets
│   └── SKILL.md
├── bazinga-db-write/    # All creates/updates/saves
│   └── SKILL.md
└── bazinga-db/          # DEPRECATED - router only
    └── SKILL.md         # Delegates to read/write
```

**Pros:**
- Clean conceptual split (reading vs writing)
- Aligns with well-known CQRS pattern
- Each skill ~400 lines (within limits)

**Cons:**
- **Artificial grouping** - "save-reasoning" and "get-reasoning" logically belong together
- **Confusing for agents** - Which skill to invoke when you need both read AND write?
- **Double invocation overhead** - Many workflows need read-then-write
- **Breaks cohesion** - Related operations scattered across skills

**Verdict:** ⚠️ Conceptually clean but practically awkward. Most database interactions are read-write pairs.

---

### Option 2: Domain-Based Split (By Table Group)

**Concept:** Split by business domain/table groupings based on actual usage patterns.

**Structure:**
```
.claude/skills/
├── bazinga-db-core/           # Sessions, task groups, state (~300 lines)
│   └── SKILL.md
├── bazinga-db-agents/         # Logs, reasoning, tokens (~250 lines)
│   └── SKILL.md
├── bazinga-db-context/        # Context packages, consumption (~200 lines)
│   └── SKILL.md
├── bazinga-db-planning/       # Dev plans, success criteria (~200 lines)
│   └── SKILL.md
└── bazinga-db-learning/       # Error patterns, strategies (~150 lines)
    └── SKILL.md
```

**Mapping:**
| Skill | Tables/Operations | Primary Users |
|-------|-------------------|---------------|
| `bazinga-db-core` | sessions, task_groups, state_snapshots | Orchestrator, PM |
| `bazinga-db-agents` | orchestration_logs, reasoning, token_usage | All agents |
| `bazinga-db-context` | context_packages, consumption | RE, Developer |
| `bazinga-db-planning` | development_plans, success_criteria | PM |
| `bazinga-db-learning` | error_patterns, strategies | Learning system |

**Pros:**
- **High cohesion** - Related operations stay together
- **Clear ownership** - Each skill has clear purpose
- **Matches mental model** - "I need to save reasoning" → bazinga-db-agents
- **Scalable** - Can add new domain skills without touching others
- **Independent evolution** - Planning skill can change without affecting agents

**Cons:**
- **5 skills to maintain** - More files to keep in sync
- **Agent needs to know which skill** - Requires clear documentation
- **Cross-domain operations** - Dashboard snapshot needs all domains
- **Schema coordination** - Changes may span multiple skills

**Verdict:** ✅ Best balance of cohesion and manageability. Natural boundaries.

---

### Option 3: Facade Pattern with Sub-Skills

**Concept:** Keep one entry point skill that delegates to specialized sub-skills.

**Structure:**
```
.claude/skills/
├── bazinga-db/                # Router/facade (~150 lines)
│   └── SKILL.md               # Parses request, delegates to sub-skill
├── bazinga-db-sessions/       # Session operations
├── bazinga-db-logs/           # Log operations
├── bazinga-db-tasks/          # Task group operations
└── ...
```

**Pros:**
- **Single entry point** - Agents always invoke `bazinga-db`
- **Backward compatible** - No changes to agent code
- **Implementation hidden** - Sub-skills are implementation detail

**Cons:**
- **Double invocation overhead** - Facade skill → sub-skill
- **Facade still needs smarts** - Routing logic adds complexity
- **Token waste** - Two skill loads per operation
- **Claude Code limitation** - Skills can't invoke other skills directly

**Verdict:** ❌ Claude Code skills cannot invoke other skills. Pattern doesn't apply.

---

### Option 4: Core + Extensions Pattern

**Concept:** One core skill with essential operations, multiple extension skills for advanced features.

**Structure:**
```
.claude/skills/
├── bazinga-db/                # Core: sessions, logs, task groups (~400 lines)
│   └── SKILL.md
├── bazinga-db-reasoning/      # Extension: reasoning capture (~150 lines)
│   └── SKILL.md
├── bazinga-db-context/        # Extension: context packages (~150 lines)
│   └── SKILL.md
└── bazinga-db-learning/       # Extension: error patterns, strategies (~150 lines)
    └── SKILL.md
```

**Pros:**
- **Minimal disruption** - Core operations unchanged
- **Clear hierarchy** - Core vs extensions
- **Progressive complexity** - Basic users need only core
- **Smaller core** - Most-used operations in primary skill

**Cons:**
- **Arbitrary "core" definition** - What's essential varies by workflow
- **Still need to update agent prompts** - Agents must know about extensions
- **Extensions may not be discovered** - Model might not invoke them

**Verdict:** ⚠️ Good compromise but "core" is subjective. May fragment related operations.

---

### Option 5: Agent-Centric Split

**Concept:** Split skills by which agents primarily use them.

**Structure:**
```
.claude/skills/
├── bazinga-db-orchestrator/   # Sessions, state, dashboard
├── bazinga-db-pm/             # Task groups, plans, criteria
├── bazinga-db-developer/      # Logs, reasoning, context
└── bazinga-db-system/         # Tokens, errors, strategies
```

**Pros:**
- **Clear ownership** - "I'm PM, I use bazinga-db-pm"
- **Optimized instructions** - Each skill tailored to agent needs

**Cons:**
- **Overlap** - Multiple agents log reasoning
- **Role changes** - If agent responsibilities shift, skills break
- **Not discoverable** - QA Expert doesn't have their own skill but needs logging

**Verdict:** ❌ Too rigid. Operations don't align well with agent boundaries.

---

## Recommended Solution: Domain-Based Split (Option 2)

### Why Domain-Based?

1. **Natural boundaries** - Tables cluster into logical domains
2. **High cohesion** - CRUD operations for related tables stay together
3. **Low coupling** - Domains interact through sessions/group IDs, not each other
4. **Matches usage patterns** - Most workflows operate within one domain
5. **Future-proof** - New domains (e.g., metrics) get their own skill

### Proposed Split Architecture

```
.claude/skills/
├── bazinga-db-core/           # 300 lines - Session lifecycle
│   ├── SKILL.md
│   └── scripts/ → symlink to shared scripts
│
├── bazinga-db-workflow/       # 250 lines - Task management
│   ├── SKILL.md
│   └── scripts/ → symlink
│
├── bazinga-db-agents/         # 250 lines - Agent interactions
│   ├── SKILL.md
│   └── scripts/ → symlink
│
├── bazinga-db-context/        # 200 lines - Context engineering
│   ├── SKILL.md
│   └── scripts/ → symlink
│
└── bazinga-db-learning/       # 150 lines - Pattern learning
    ├── SKILL.md
    └── scripts/ → symlink

# Shared infrastructure (unchanged)
bazinga-db-scripts/            # Shared Python scripts
├── bazinga_db.py              # All commands (unchanged)
├── init_db.py
└── ...
```

### Domain Mapping

#### 1. `bazinga-db-core` - Session Lifecycle (~300 lines)

**Purpose:** Create and manage orchestration sessions.

**Commands:**
- `create-session`
- `get-session`
- `list-sessions`
- `update-session-status`
- `save-state`
- `get-state`
- `dashboard-snapshot`
- `query` (custom SQL)
- `integrity-check`
- `recover-db`
- `detect-paths`

**Primary Users:** Orchestrator

---

#### 2. `bazinga-db-workflow` - Task Management (~250 lines)

**Purpose:** Manage task groups and development planning.

**Commands:**
- `create-task-group`
- `update-task-group`
- `get-task-groups`
- `save-development-plan`
- `get-development-plan`
- `update-plan-progress`
- `save-success-criteria`
- `get-success-criteria`
- `update-success-criterion`

**Primary Users:** Project Manager, Orchestrator

---

#### 3. `bazinga-db-agents` - Agent Interactions (~250 lines)

**Purpose:** Track agent logs, reasoning, and tokens.

**Commands:**
- `log-interaction`
- `stream-logs`
- `save-reasoning`
- `get-reasoning`
- `reasoning-timeline`
- `check-mandatory-phases`
- `log-tokens`
- `token-summary`
- `save-skill-output`
- `get-skill-output`
- `get-skill-output-all`
- `check-skill-evidence`
- `save-event`
- `get-events`

**Primary Users:** All agents (Developer, QA, Tech Lead, etc.)

---

#### 4. `bazinga-db-context` - Context Engineering (~200 lines)

**Purpose:** Manage context packages for inter-agent communication.

**Commands:**
- `save-context-package`
- `get-context-packages`
- `mark-context-consumed`
- `update-context-references`
- `save-consumption`
- `get-consumption`

**Primary Users:** Requirements Engineer, Developer, SSE

---

#### 5. `bazinga-db-learning` - Pattern Learning (~150 lines)

**Purpose:** Capture and query learned patterns and strategies.

**Commands:**
- `save-error-pattern`
- `get-error-patterns`
- `update-error-confidence`
- `cleanup-error-patterns`
- `save-strategy`
- `get-strategies`
- `update-strategy-helpfulness`
- `extract-strategies`

**Primary Users:** Learning system (automated)

---

## Implementation Plan

### Phase 1: Create New Skills (No Breaking Changes)

1. Create 5 new skill directories with SKILL.md files
2. Each references the same `bazinga_db.py` script
3. All skills coexist with original `bazinga-db`

### Phase 2: Update Agent Prompts

1. Update agent prompts to reference specific skills
2. Add skill selection guidance to orchestrator
3. Update integration guide

### Phase 3: Deprecate Original Skill

1. Mark `bazinga-db` as deprecated in description
2. Add migration notice pointing to new skills
3. Keep for backward compatibility (6 months)

### Phase 4: Remove Deprecated Skill

1. Remove `bazinga-db` directory
2. Update all documentation

---

## Migration Impact Analysis

### Files to Modify

| File | Change | Risk |
|------|--------|------|
| `.claude/skills/bazinga-db-*/SKILL.md` | CREATE | None (new) |
| `agents/orchestrator.md` | Update skill references | Low |
| `agents/project_manager.md` | Update skill references | Low |
| `agents/developer.md` | Update skill references | Low |
| `agents/qa_expert.md` | Update skill references | Low |
| `agents/tech_lead.md` | Update skill references | Low |
| `.claude/claude.md` | Update documentation | Low |
| `research/skill-implementation-guide.md` | Add guidance | Low |

### Agent Prompt Updates Required

Each agent prompt needs to reference the correct domain skill:

| Agent | Skills Used |
|-------|-------------|
| Orchestrator | `bazinga-db-core`, `bazinga-db-workflow`, `bazinga-db-agents` |
| Project Manager | `bazinga-db-workflow`, `bazinga-db-agents` |
| Developer | `bazinga-db-agents`, `bazinga-db-context` |
| QA Expert | `bazinga-db-agents` |
| Tech Lead | `bazinga-db-agents` |
| Requirements Engineer | `bazinga-db-context`, `bazinga-db-agents` |

### Backward Compatibility

- Original `bazinga-db` skill remains functional during transition
- All commands continue to work (Python script unchanged)
- Only SKILL.md is split (documentation, not implementation)

---

## Critical Analysis

### Pros

1. **Solves immediate problem** - Each skill within size limits
2. **Clean domain boundaries** - High cohesion within skills
3. **Matches mental model** - "Reasoning" → agents skill, "Context" → context skill
4. **Minimal code changes** - Only SKILL.md files split, Python unchanged
5. **Progressive migration** - Can adopt incrementally
6. **Future extensibility** - New domains get their own skill

### Cons

1. **More skills to maintain** - 5 instead of 1
2. **Agent learning curve** - Must know which skill to invoke
3. **Cross-domain queries** - `dashboard-snapshot` spans domains
4. **Documentation sync** - Schema changes need updates in all relevant skills
5. **Discovery burden** - Model must know 5 skills instead of 1

### Mitigations

| Risk | Mitigation |
|------|------------|
| Learning curve | Clear naming convention (bazinga-db-X) |
| Cross-domain | Keep `dashboard-snapshot` in core |
| Doc sync | Single schema.md, referenced by all skills |
| Discovery | Comprehensive skill descriptions |

---

## Comparison to Alternatives

| Criteria | Domain Split | CQRS | Facade | Core+Ext | Agent-Centric |
|----------|--------------|------|--------|----------|---------------|
| Cohesion | ✅ High | ❌ Low | ✅ High | ⚠️ Medium | ❌ Low |
| Discoverability | ⚠️ Medium | ✅ High | ✅ High | ⚠️ Medium | ⚠️ Medium |
| Migration ease | ✅ Easy | ⚠️ Medium | ❌ Hard | ✅ Easy | ❌ Hard |
| Future-proof | ✅ Yes | ⚠️ Maybe | ✅ Yes | ⚠️ Maybe | ❌ No |
| Agent confusion | ⚠️ Medium | ✅ Low | ✅ Low | ⚠️ Medium | ❌ High |

---

## Decision Rationale

Domain-based split wins because:

1. **Cohesion trumps simplicity** - Better to have 5 focused skills than 1 confusing mega-skill or 2 artificial read/write skills
2. **Natural boundaries exist** - The 5 domains already have minimal interaction
3. **Aligns with usage** - Most workflows stay within one domain
4. **Non-breaking migration** - Can run old and new skills in parallel

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Each SKILL.md size | < 350 lines |
| Agent invocation accuracy | > 95% correct skill selection |
| Migration duration | < 1 week |
| Breaking changes | 0 |

---

## References

- [vFunction: Modular Software Best Practices](https://vfunction.com/blog/modular-software/)
- [Microsoft: CQRS Pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/cqrs)
- [Refactoring Guru: Facade Pattern](https://refactoring.guru/design-patterns/facade)
- [ArjanCodes: Decoupling with Plugins](https://arjancodes.com/blog/best-practices-for-decoupling-software-using-plugins/)
- [Java Code Geeks: CQRS for Scalable Architectures](https://www.javacodegeeks.com/2025/12/the-cqrs-pattern-separating-reads-from-writes-for-scalable-architectures.html)

---

## Lessons Learned

1. **Skills grow faster than expected** - Need size monitoring
2. **Domain boundaries are cleaner than operation boundaries** - CQRS doesn't fit skills
3. **Python script can stay monolithic** - Only docs need splitting
4. **Agent prompts are the coupling point** - Must update when skills change

---

## Multi-LLM Review Integration

### OpenAI GPT-5 Review Summary

**Core Critique:** The domain-based split is operationally risky and unnecessary. The problem is SKILL.md prompt size, not Python command organization.

### Critical Issues Raised

1. **No evidence of actual limit** - The analysis assumed SKILL.md length causes failures but didn't quantify the actual limit (bytes vs tokens, model-specific ceilings)

2. **Backward compatibility conflict** - Keeping original `bazinga-db` during transition doesn't solve the problem since agents still call the old skill

3. **Overly invasive scope** - Splitting into 5 skills breaks the current invariant that all agents invoke `Skill(command: "bazinga-db")`. Would require synchronized updates across:
   - skills_config.json
   - prompt-builder
   - config-seeder
   - All agent definitions
   - Workflow templates

4. **Symlinks are brittle** - Platform incompatibilities (Windows, sandboxed FS) and path resolution issues

5. **Cross-domain patterns underestimated** - Orchestrator frequently chains commands across proposed domains in one flow

### Consensus Points (Accepted)

| Point | Verdict |
|-------|---------|
| SKILL.md is too verbose for actual usage needs | ✅ Agree |
| Reference files already exist but are underutilized | ✅ Agree |
| CLI --help provides detailed command documentation | ✅ Agree |
| Splitting skills multiplies maintenance burden | ✅ Agree |
| Zero-change solution preferable to multi-file migration | ✅ Agree |

### Rejected Suggestions (With Reasoning)

None - all feedback was valid and actionable.

---

## REVISED RECOMMENDATION: Option 6 - Documentation Slimming

### Why Documentation Slimming Instead of Splitting?

1. **Zero breaking changes** - No agent or orchestrator modifications needed
2. **Immediate fix** - Can be done in one PR
3. **Lower risk** - No multi-skill coordination complexity
4. **Reference files already exist** - `references/schema.md` and `references/command_examples.md` can absorb content
5. **CLI help available** - `bazinga_db.py --help` provides detailed usage

### Target Structure for SKILL.md

**Current:** 850 lines (~26KB)
**Target:** 150-250 lines (~6-8KB)

```
SKILL.md (Slimmed - ~200 lines)
├── Frontmatter (10 lines)
├── Purpose & When to Invoke (30 lines)
├── Quick Start Examples (50 lines)
│   └── Top 10 most-used commands with minimal examples
├── Command Index Table (40 lines)
│   └── Command | Description | Primary Users
├── Error Handling Playbook (30 lines)
├── "For Full Details" References (20 lines)
│   └── Links to references/schema.md
│   └── Links to references/command_examples.md
│   └── "Run bazinga_db.py --help for all options"
└── Notes & Caveats (20 lines)
```

### Content Migration Plan

| Current Location | Move To | Size Impact |
|-----------------|---------|-------------|
| Detailed command examples | `references/command_examples.md` | -300 lines |
| Schema documentation | `references/schema.md` | Already exists |
| Error scenarios | `references/error_handling.md` | -100 lines |
| Context package examples | `references/command_examples.md` | -50 lines |
| Reasoning capture examples | `references/command_examples.md` | -50 lines |

### Implementation Steps

1. **Measure actual limit** (15 min)
   - Determine exact byte/token threshold causing issues
   - Document in this file

2. **Enhance reference files** (30 min)
   - Expand `references/command_examples.md` with moved examples
   - Create `references/error_handling.md` if needed

3. **Slim SKILL.md** (1 hour)
   - Keep essential guidance only
   - Add "For full usage: `python3 .../bazinga_db.py --help`"
   - Link to reference files

4. **Test invocation** (15 min)
   - Verify skill loads successfully
   - Test common commands work

5. **Commit and push** (5 min)

### Success Metrics (Revised)

| Metric | Target |
|--------|--------|
| SKILL.md line count | < 250 lines |
| SKILL.md byte size | < 10KB |
| Breaking changes | 0 |
| Agent prompt changes | 0 |
| Implementation time | < 2 hours |

---

## Final Decision

**Implement Option 6: Documentation Slimming**

The domain-based split (Option 2) was conceptually clean but operationally risky. The OpenAI review correctly identified that:

1. The problem is **prompt size**, not **code organization**
2. Reference files and CLI help already exist but are underutilized
3. Splitting skills requires invasive changes across the entire system
4. A zero-change solution exists and should be tried first

If documentation slimming proves insufficient (unlikely), we can revisit the domain split later with the groundwork already laid out in this document.

---

## Action Items

- [ ] Measure actual token/byte limit in skill loading
- [ ] Expand `references/command_examples.md` with detailed examples
- [ ] Create `references/error_handling.md` for error scenarios
- [ ] Slim `SKILL.md` to <250 lines with quick reference only
- [ ] Add CLI help reference to SKILL.md
- [ ] Test skill invocation after changes
- [ ] Commit with message: "Slim bazinga-db SKILL.md to resolve size limit"
