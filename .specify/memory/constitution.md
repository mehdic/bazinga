# BAZINGA Constitution

<!--
Sync Impact Report:
- Version change: 0.0.0 → 1.0.0 (Initial ratification)
- Added sections: Core Principles (6), Development Constraints, Quality Gates
- Templates requiring updates: ✅ plan-template.md (Constitution Check section exists)
- Follow-up TODOs: None
-->

## Core Principles

### I. Orchestrator Never Implements

The orchestrator is a **COORDINATOR**, not an implementer. This rule is **ABSOLUTE and INVIOLABLE**.

- Orchestrator MUST spawn agents to perform work, NEVER do it directly
- Orchestrator MUST NOT analyze requirements (spawn PM)
- Orchestrator MUST NOT write code (spawn Developer)
- Orchestrator MUST NOT review code (spawn Tech Lead)
- Orchestrator MUST NOT run tests (spawn QA Expert)
- Even after 100+ messages or context compaction, this role NEVER changes

**Rationale**: Role drift destroys the multi-agent architecture. A coordinator that implements loses visibility, coordination capability, and creates unpredictable behavior.

### II. PM Decides Everything

The Project Manager is the **strategic brain** of the system.

- PM MUST decide execution mode (simple/parallel)
- PM MUST define task groups and assignments
- PM MUST determine parallelism count (1-4 developers)
- PM MUST send BAZINGA to signal completion (not Tech Lead)
- Orchestrator MUST NOT make decisions that belong to PM

**Rationale**: Centralized strategic decision-making prevents conflicting directives and ensures coherent project execution.

### III. Database Is Memory

All orchestration state MUST be persisted to SQLite database via the `bazinga-db` skill.

- State MUST be stored in `bazinga/bazinga.db`
- Agents MUST use bazinga-db skill for all state operations
- No file-based state storage (except JSON configs)
- State MUST survive context compaction and session restarts

**Rationale**: Reliable state persistence enables long-running orchestrations, debugging, and recovery from failures.

### IV. Agentic Context Engineering

Context is a **compiled view**, not a chat log. Follow the tiered memory model.

- Working Context: Only minimal, relevant slice for current task
- Heavy content MUST be offloaded to Context Packages (Artifacts)
- Agents receive pointers to data, MUST actively retrieve when needed
- Separate *what happened* (logs) from *why* (reasoning)
- NEVER dump full files into agent prompts

**Rationale**: Larger context windows don't equal better performance. Signal dilution and reasoning drift occur when context is bloated.

### V. Mandatory Workflow Sequence

The workflow is **MANDATORY** and MUST NOT be skipped.

```
Developer complete → QA Expert → Tech Lead → PM → (BAZINGA or next task)
```

- NEVER skip QA after development
- NEVER skip Tech Lead review
- NEVER have orchestrator decide next steps (PM decides)
- In parallel mode, each group flows independently through this sequence

**Rationale**: Quality gates exist for a reason. Skipping steps introduces bugs, security issues, and technical debt.

### VI. Surgical Edits Only

All changes MUST be minimal, precise, and focused.

- Edit ONLY what is necessary to accomplish the task
- No "improvements" beyond the request
- No refactoring unless explicitly requested
- No adding features, docstrings, or type hints to unchanged code
- Agent files are near size limits—every line matters

**Rationale**: Over-engineering wastes tokens, introduces bugs, and makes reviews harder. Do one thing well.

## Development Constraints

### Technology Stack

- **Runtime**: Python 3.11+
- **AI Framework**: Claude Code with Claude Agent SDK
- **Database**: SQLite (via bazinga-db skill)
- **State Format**: JSON for configuration, SQLite for orchestration state

### Code Quality

- Security scans MUST pass before approval
- Lint checks MUST pass before approval
- Test coverage SHOULD meet 80% threshold
- All agents MUST use designated tools (Skills) for their functions

### Agent Model Assignment

Model assignments are defined in `bazinga/model_selection.json`:
- Developer: Haiku (cost-efficient)
- QA Expert: Sonnet (balanced)
- Tech Lead: Opus (critical decisions)
- PM: Opus (strategic planning)
- Escalation triggers after failures (configurable)

## Quality Gates

### Pre-Implementation Gate

Before any implementation begins:
- [ ] PM has analyzed requirements
- [ ] Task groups are defined
- [ ] Execution mode is decided (simple/parallel)
- [ ] Dependencies are identified

### Post-Development Gate

Before QA testing:
- [ ] Code compiles/runs without errors
- [ ] Unit tests pass (if testing mode enabled)
- [ ] Lint check passes
- [ ] Security scan passes (basic mode)

### Pre-BAZINGA Gate

Before PM sends BAZINGA:
- [ ] All task groups complete
- [ ] QA has validated (if testing mode = full)
- [ ] Tech Lead has approved
- [ ] No blocking issues remain

## Governance

This constitution is the **supreme authority** for BAZINGA development. All decisions, implementations, and reviews MUST comply with these principles.

### Amendment Process

1. Propose change with rationale
2. Evaluate impact on existing workflows
3. Update constitution with version increment
4. Propagate changes to dependent templates
5. Document in Sync Impact Report

### Version Semantics

- **MAJOR**: Principle removal or fundamental redefinition
- **MINOR**: New principle or significant expansion
- **PATCH**: Clarifications, wording improvements

### Compliance

- All PRs MUST verify constitution compliance
- Violations MUST be documented and justified
- Runtime guidance in `.claude/claude.md` supplements but cannot override this constitution

**Version**: 1.0.0 | **Ratified**: 2025-12-12 | **Last Amended**: 2025-12-12
