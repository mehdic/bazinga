# Implementation Plan: Context Engineering System

**Branch**: `1-context-engineering` | **Date**: 2025-12-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/1-context-engineering/spec.md`

## Summary

Implement a tiered context engineering system for Orchestrix that intelligently assembles, prioritizes, and manages context passed to agents. The core component is a `context-assembler` skill that ranks packages by relevance, enforces token budgets with graduated zones, captures error patterns for learning, and supports configurable per-agent retrieval limits.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: SQLite (via orchestrix-db skill), tiktoken (token estimation)
**Storage**: SQLite (`orchestrix/orchestrix.db`) - extends existing schema
**Testing**: pytest with existing Orchestrix test infrastructure
**Target Platform**: Claude Code environment (Linux/macOS/Windows)
**Project Type**: Skill extension to existing Orchestrix orchestration system
**Performance Goals**: <500ms context assembly latency (SC-005)
**Constraints**: 15% token safety margin, graceful degradation on failures
**Scale/Scope**: Per-session context (100s of packages), cross-session patterns (1000s)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Orchestrator Never Implements | ✅ PASS | Skill invoked by orchestrator, not implementation in orchestrator |
| II. PM Decides Everything | ✅ PASS | No changes to PM decision authority |
| III. Database Is Memory | ✅ PASS | All state stored in orchestrix.db via orchestrix-db skill |
| IV. Agentic Context Engineering | ✅ PASS | **This feature implements this principle** |
| V. Mandatory Workflow Sequence | ✅ PASS | No workflow changes |
| VI. Surgical Edits Only | ✅ PASS | New skill + schema extensions, minimal changes to existing code |

**Gate Status**: ✅ PASSED - No constitution violations

## Project Structure

### Documentation (this feature)

```text
specs/1-context-engineering/
├── spec.md              # Feature specification (complete)
├── plan.md              # This file
├── data-model.md        # Entity schemas and relationships
├── quickstart.md        # Usage examples and integration guide
└── checklists/
    └── requirements.md  # Quality checklist (complete)
```

### Source Code (repository structure)

```text
.claude/skills/context-assembler/
├── SKILL.md             # Skill definition and instructions
└── references/
    └── usage.md         # Detailed usage documentation

orchestrix/
├── orchestrix.db           # Extended with new tables
└── skills_config.json   # Updated with context-assembler config
```

**Structure Decision**: This is a new skill added to the existing `.claude/skills/` directory. Database schema extensions are applied to the existing `orchestrix/orchestrix.db` via the orchestrix-db skill. No new top-level directories required.

## Phase 0: Research Summary

Research was completed prior to spec creation. Key decisions documented in `research/context-engineering-strategy.md`:

| Decision | Chosen | Rationale | Alternatives Rejected |
|----------|--------|-----------|----------------------|
| Relevance Ranking | Heuristic (no FTS5 in MVP) | Deterministic, low-latency, no embedding dependencies | FTS5 (deferred to Phase 2), Embeddings (too complex) |
| Token Estimation | tiktoken with 15% safety margin | Model-aware, proven accuracy | Character counting (inaccurate), No estimation (risky) |
| Error Pattern Storage | SQLite table with TTL | Aligns with constitution (DB is memory) | File-based (rejected by constitution) |
| Redaction Strategy | Regex + entropy detection | Catches secrets, configurable allow-lists | No redaction (security risk), LLM-based (too slow) |

## Phase 1: Design Artifacts

### Data Model

See: [data-model.md](./data-model.md)

**New Tables:**
- `error_patterns` - Captured error signatures with solutions
- `strategies` - Successful approaches extracted from completions
- `consumption_scope` - Iteration-aware package consumption tracking

**Schema Extensions:**
- Add `priority` and `summary` columns to existing `context_packages` table

### Skill Interface

**Inputs:**
```
session_id: str      # Current orchestration session
group_id: str        # Task group being processed
agent_type: str      # developer/senior_software_engineer/qa_expert/tech_lead
model: str           # haiku/sonnet/opus (for token budgeting)
```

**Output:**
```markdown
## Context for {agent_type}

### Relevant Packages ({count}/{available})
{ranked package summaries}

### Error Patterns ({count} matches)
{relevant error hints if any}

📦 +{overflow_count} more packages available (use context-fetch skill to expand)
```

### Token Budget Allocation

| Agent | Task | Specialization | Context Pkgs | Errors | Total |
|-------|------|----------------|--------------|--------|-------|
| Developer | 50% | 20% | 20% | 10% | 100% |
| Senior Software Engineer | 40% | 20% | 25% | 15% | 100% |
| QA Expert | 40% | 15% | 30% | 15% | 100% |
| Tech Lead | 30% | 15% | 40% | 15% | 100% |

**Note:** SSE handles escalations from failed developer attempts, so it receives more context and error budget.

### Retrieval Limits (Configurable)

| Agent Type | Default Limit | Override via |
|------------|---------------|--------------|
| developer | 3 | `skills_config.json` |
| senior_software_engineer | 5 | `skills_config.json` |
| qa_expert | 5 | `skills_config.json` |
| tech_lead | 5 | `skills_config.json` |

### Graduated Token Zones

| Usage % | Zone | Behavior |
|---------|------|----------|
| 0-60% | Normal | Full context, all packages |
| 60-75% | Soft Warning | Prefer summarized context |
| 75-85% | Conservative | Minimal context, no new large operations |
| 85-95% | Wrap-up | Complete current operation only |
| 95%+ | Emergency | Checkpoint and break |

## Complexity Tracking

No constitution violations requiring justification.

## Implementation Phases (Summary)

| Phase | Focus | Key Deliverables |
|-------|-------|------------------|
| P1 (MVP) | Context-assembler skill | SKILL.md, heuristic ranking, token budgeting |
| P2 | Error pattern capture | Schema, capture logic, injection |
| P3 | Configurable limits | skills_config.json integration |
| P4 | Polish | Documentation, edge case handling |

## Next Steps

1. Run `/speckit.tasks` to generate detailed task breakdown
2. Tasks will be organized by user story (P1 → P4)
3. Implementation follows Orchestrix workflow: dev → QA → tech lead → PM
