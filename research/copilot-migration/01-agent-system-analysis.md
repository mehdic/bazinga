# BAZINGA Agent System Migration Analysis: Claude Code to GitHub Copilot

**Date:** 2026-01-23
**Status:** Draft
**Author:** Backend System Architect
**Scope:** Agent System (agents/*.md) Migration Strategy

---

## Executive Summary

This document analyzes the BAZINGA multi-agent orchestration system for migration to GitHub Copilot. BAZINGA currently implements a sophisticated 9-agent workflow with hierarchical routing, escalation tiers, and structured handoffs. Copilot offers equivalent primitives (`.agent.md` files, `#runSubagent`, handoffs, MCP) but with architectural differences that require careful mapping.

**Key Finding:** A hybrid approach (Option B) is recommended, maintaining an abstract agent definition layer that compiles to platform-specific formats. This preserves BAZINGA's sophisticated workflow patterns while enabling dual-platform support.

---

## Table of Contents

1. [Current State Analysis](#1-current-state-analysis)
2. [Copilot Mapping](#2-copilot-mapping)
3. [Migration Strategy](#3-migration-strategy)
4. [Dual-Platform Support](#4-dual-platform-support)
5. [Implementation Plan](#5-implementation-plan)
6. [Open Questions](#6-open-questions)

---

## 1. Current State Analysis

### 1.1 Agent Inventory

BAZINGA implements 9 specialized agents, each with distinct responsibilities:

| Agent | Model | Role | Spawning Context |
|-------|-------|------|------------------|
| **orchestrator** | sonnet | Coordinator (never implements) | Entry point, runs inline |
| **project_manager** | opus | Strategic planning, final quality gate | Phase 1, spawns first |
| **developer** | sonnet | Implementation, code changes | Task execution |
| **senior_software_engineer** | opus | Escalation tier for complex failures | After dev failure or Level 3+ QA failure |
| **qa_expert** | sonnet | Testing, validation, 5-level challenges | Conditional (when tests exist) |
| **tech_lead** | opus | Code review, architectural guidance | After QA pass or direct from dev |
| **investigator** | opus | Deep-dive analysis, root cause | Max 5 iterations |
| **requirements_engineer** | opus | Requirements analysis, research mode | `[R]` task groups |
| **tech_stack_scout** | sonnet | Project context detection | Step 0.5 (read-only) |

### 1.2 Agent Definition Format

Each agent is defined as a Markdown file with YAML frontmatter:

```yaml
# agents/developer.md
---
name: developer
description: "Implementation specialist for coding tasks"
model: sonnet
---

# Developer Agent

## Identity & Purpose
[Agent instructions...]

## Workflow
[Execution steps...]

## Status Codes
[Valid output codes...]
```

**Key characteristics:**
- `model` field is documentation only (runtime reads from `bazinga/model_selection.json`)
- Extensive inline instructions (1000-1500 lines per agent)
- Embedded workflow logic, routing rules, and handoff patterns

### 1.3 Agent Spawning Mechanism

Agents are spawned via the `Task()` tool with explicit parameters:

```python
Task(
    description: "Execute developer agent for task group CALC",
    prompt: "{composed_agent_prompt_from_prompt_builder}",
    run_in_background: false  # MANDATORY - foreground only
)
```

**Critical constraints:**
- `run_in_background: false` is mandatory (background causes context leaks, hangs)
- Maximum 4 parallel developers
- Agent prompts built deterministically via `prompt-builder` skill

### 1.4 Status Code System

Agents communicate via structured status codes that drive routing:

| Status Code | Source Agent(s) | Routing Action |
|-------------|-----------------|----------------|
| `READY_FOR_QA` | developer, sse | Route to qa_expert |
| `READY_FOR_REVIEW` | developer, sse | Route to tech_lead (bypasses QA) |
| `APPROVED` | tech_lead | Route to PM for next assignment |
| `CHANGES_REQUESTED` | tech_lead | Route back to developer |
| `PASS` | qa_expert | Route to tech_lead |
| `FAIL` | qa_expert | Route back to developer |
| `FAIL_ESCALATE` | qa_expert | Escalate to senior_software_engineer |
| `BAZINGA` | project_manager | Session complete |
| `BLOCKED` | any | Route to investigator or PM |
| `ESCALATE_SENIOR` | developer | Escalate to senior_software_engineer |

### 1.5 Handoff File System

Context is passed between agents via handoff JSON files:

```
bazinga/artifacts/{session_id}/{group_id}/handoff_{agent}.json
```

**Handoff file structure:**
```json
{
  "session_id": "bazinga_abc123",
  "group_id": "CALC",
  "agent_type": "developer",
  "status": "READY_FOR_QA",
  "summary": ["Implemented calculator.py", "Added unit tests", "All tests passing"],
  "files_changed": ["calculator.py", "test_calculator.py"],
  "context_for_next": {
    "test_framework": "pytest",
    "coverage": "95%"
  }
}
```

### 1.6 Key Dependencies

| Dependency | Purpose | Critical? |
|------------|---------|-----------|
| `bazinga-db` skill | State persistence (SQLite) | Yes |
| `prompt-builder` skill | Deterministic prompt composition | Yes |
| `workflow-router` skill | Routing decisions | Yes |
| `specialization-loader` skill | Tech-specific identity composition | Yes |
| `model_selection.json` | Agent model assignment | Yes |
| `project_context.json` | Tech stack context | Yes |

### 1.7 Workflow Pattern

The standard workflow follows this routing:

```
Orchestrator
    │
    ▼
Project Manager (planning)
    │
    ├─── Simple Mode ──────────────────────────────────────┐
    │    ▼                                                  │
    │    Developer → [QA Expert] → Tech Lead → PM          │
    │         ↑____________│____________│                   │
    │         (CHANGES_REQUESTED loop)                     │
    │                                                       │
    ├─── Parallel Mode ────────────────────────────────────┤
    │    ▼                                                  │
    │    Developer[1..4] → QA → TL ──┐                     │
    │    (per task group)            │                     │
    │                                ▼                     │
    │                             PM (merge)               │
    │                                                       │
    └─── Escalation Path ──────────────────────────────────┘
         Developer/QA fails → Senior Software Engineer
         Complex problems → Investigator (max 5 iter)
         Research tasks → Requirements Engineer
```

---

## 2. Copilot Mapping

### 2.1 Primitive Mapping

| BAZINGA Concept | Copilot Equivalent | Notes |
|-----------------|-------------------|-------|
| `agents/*.md` | `.github/agents/*.agent.md` | Different frontmatter schema |
| `Task()` tool | `#runSubagent` | Sub-agent spawning |
| Handoff files | `handoffs` in frontmatter | User-driven via buttons |
| `bazinga-db` skill | MCP server | External state management |
| `prompt-builder` | Custom skill or inline | No direct equivalent |
| `workflow-router` | Hardcoded or custom skill | No direct equivalent |
| Status codes | Agent output + handoff triggers | Manual mapping required |
| Model selection | VS Code settings | Different mechanism |

### 2.2 Agent File Format Translation

**BAZINGA format:**
```yaml
---
name: developer
description: "Implementation specialist"
model: sonnet
---
# Developer Agent
[1200+ lines of instructions]
```

**Copilot `.agent.md` format:**
```yaml
---
name: developer
description: "Implementation specialist"
tools:
  - filesystem
  - terminal
  - code_search
handoffs:
  - name: qa_expert
    description: "Hand off to QA for testing"
    send: false  # User confirms before sending
  - name: tech_lead
    description: "Hand off to Tech Lead for review"
    send: false
---
# Developer Agent
[Instructions - should be concise]
```

**Key differences:**
- Copilot has `tools` array (explicit tool access)
- Copilot has `handoffs` array (user-driven transitions)
- Copilot encourages shorter instructions with skill references
- No `model` field in Copilot (configured elsewhere)

### 2.3 Status Code to Handoff Mapping

BAZINGA status codes must be mapped to Copilot handoff triggers:

| Status Code | Copilot Handoff Target | `send` Value |
|-------------|----------------------|--------------|
| `READY_FOR_QA` | `qa_expert` | `false` (user confirms) |
| `READY_FOR_REVIEW` | `tech_lead` | `false` |
| `APPROVED` | `project_manager` | `true` (auto-send) |
| `CHANGES_REQUESTED` | `developer` | `false` |
| `PASS` | `tech_lead` | `true` |
| `FAIL` | `developer` | `false` |
| `FAIL_ESCALATE` | `senior_software_engineer` | `false` |
| `BAZINGA` | (none - terminal) | N/A |

**Challenge:** Copilot handoffs are user-driven (button click), while BAZINGA routes automatically via orchestrator. This requires either:
1. User intervention at each transition (less automated)
2. Custom orchestration skill that bypasses handoff buttons

### 2.4 Sub-Agent Invocation

**BAZINGA:**
```python
Task(
    description: "Execute developer for CALC",
    prompt: "{built_prompt}",
    run_in_background: false
)
```

**Copilot:**
```markdown
#runSubagent developer "Implement calculator.py with add, subtract, multiply, divide functions"
```

**Differences:**
- Copilot sub-agents are context-isolated (start fresh)
- No equivalent to BAZINGA's composed prompt injection
- Copilot relies on agent's own `.agent.md` instructions

### 2.5 Skill Mapping

BAZINGA skills map to Copilot skills with format changes:

| BAZINGA Skill | Copilot Equivalent | Migration Path |
|---------------|-------------------|----------------|
| `bazinga-db` | MCP server | Reimplement as MCP |
| `prompt-builder` | Custom skill | Rewrite for Copilot format |
| `workflow-router` | Custom skill | Rewrite for Copilot format |
| `specialization-loader` | Custom skill | Rewrite for Copilot format |
| `codebase-analysis` | Built-in `code_search` | Use native tool |
| `lint-check` | Custom skill or GitHub Action | Integration option |
| `security-scan` | Custom skill or GitHub Action | Integration option |

### 2.6 Feature Gap Analysis

| Feature | BAZINGA | Copilot | Gap |
|---------|---------|---------|-----|
| Model selection per agent | Yes (JSON config) | No (VS Code settings) | Custom implementation needed |
| Automatic routing | Yes (orchestrator) | No (user-driven) | Orchestration skill needed |
| 5-level QA challenges | Yes | No | Custom skill needed |
| Escalation tiers | Yes (automatic) | No | Custom logic needed |
| Parallel task groups | Yes (1-4 devs) | Limited | Custom orchestration needed |
| Handoff context files | Yes (JSON) | Limited (message context) | MCP or custom solution |
| State persistence | Yes (SQLite) | No | MCP server needed |
| Specialization composition | Yes (prompt-builder) | No | Custom skill needed |

---

## 3. Migration Strategy

### 3.1 Option A: Direct Translation

**Approach:** Translate each `agents/*.md` file directly to `.github/agents/*.agent.md` format.

**Pros:**
- Simplest migration path
- Maintains 1:1 agent correspondence
- Familiar agent names and roles

**Cons:**
- Loses automatic routing (requires user clicks)
- No state persistence without MCP
- Loses prompt composition sophistication
- Status code system requires reimplementation
- Escalation tiers become manual

**Effort:** Medium (2-3 weeks)
**Risk:** High (feature loss)

### 3.2 Option B: Hybrid Approach (RECOMMENDED)

**Approach:** Create an abstract agent definition layer that compiles to both Claude Code and Copilot formats.

```
agents/*.yaml (Abstract Definition)
       │
       ├──► compile-claude.py ──► .claude/agents/*.md
       │
       └──► compile-copilot.py ──► .github/agents/*.agent.md
```

**Abstract definition schema:**
```yaml
# agents/developer.yaml
name: developer
description: "Implementation specialist"
tier: standard  # standard | escalation | coordinator

platform:
  claude:
    model: sonnet
  copilot:
    tools: [filesystem, terminal, code_search]

status_codes:
  - READY_FOR_QA → qa_expert
  - READY_FOR_REVIEW → tech_lead
  - BLOCKED → investigator

handoffs:
  qa_expert:
    condition: "tests exist AND testing_mode == full"
    auto_send: true
  tech_lead:
    condition: "always"
    auto_send: true

instructions:
  identity: templates/developer/identity.md
  workflow: templates/developer/workflow.md
  routing: templates/developer/routing.md
```

**Pros:**
- Single source of truth
- Platform-specific optimizations
- Preserves BAZINGA sophistication
- Enables gradual migration
- Supports dual-platform runtime

**Cons:**
- Higher initial investment
- New abstraction layer to maintain
- Compilation step adds complexity

**Effort:** High (4-6 weeks)
**Risk:** Medium (complexity, but controlled)

### 3.3 Option C: Copilot-Native Rewrite

**Approach:** Redesign the entire agent system using Copilot-native patterns, abandoning BAZINGA conventions.

**Pros:**
- Fully leverages Copilot features
- No legacy constraints
- Potentially simpler architecture

**Cons:**
- Loses years of BAZINGA refinement
- No Claude Code support
- Steep learning curve for team
- Risk of losing nuanced workflow logic

**Effort:** Very High (8-12 weeks)
**Risk:** Very High (complete rewrite)

### 3.4 Recommendation: Option B (Hybrid Approach)

**Rationale:**
1. **Preserves investment** - BAZINGA's workflow patterns are battle-tested
2. **Enables iteration** - Can migrate incrementally
3. **Dual-platform support** - Critical for team flexibility
4. **Maintainability** - Single source of truth reduces drift
5. **Risk mitigation** - Can fall back to Claude Code if issues arise

---

## 4. Dual-Platform Support

### 4.1 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Abstract Layer                            │
│  agents/*.yaml  │  skills/*.yaml  │  workflows/*.yaml       │
└─────────────────────────────────────────────────────────────┘
         │                  │                   │
         ▼                  ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────┐
│ Claude Compiler │ │ Copilot Compiler│ │ Shared State (MCP)  │
└─────────────────┘ └─────────────────┘ └─────────────────────┘
         │                  │                   │
         ▼                  ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────┐
│ .claude/agents/ │ │ .github/agents/ │ │ bazinga-mcp-server  │
│ .claude/skills/ │ │ .github/skills/ │ │ (SQLite backend)    │
└─────────────────┘ └─────────────────┘ └─────────────────────┘
```

### 4.2 Runtime Detection

```python
# runtime/platform.py
import os

def detect_platform() -> str:
    """Detect current AI coding assistant platform."""
    if os.environ.get("CLAUDE_CODE_VERSION"):
        return "claude"
    if os.environ.get("GITHUB_COPILOT_VERSION"):
        return "copilot"
    # Fallback: check for platform-specific files
    if os.path.exists(".claude"):
        return "claude"
    if os.path.exists(".github/agents"):
        return "copilot"
    return "unknown"

def get_agent_path(agent_name: str) -> str:
    """Get platform-specific agent path."""
    platform = detect_platform()
    if platform == "claude":
        return f".claude/agents/{agent_name}.md"
    elif platform == "copilot":
        return f".github/agents/{agent_name}.agent.md"
    raise ValueError(f"Unknown platform: {platform}")
```

### 4.3 Shared Components

| Component | Sharing Strategy |
|-----------|-----------------|
| State persistence | MCP server (works with both) |
| Specialization templates | Shared `templates/` directory |
| Workflow definitions | Abstract YAML compiled to both |
| Success criteria | Shared database schema |
| Session artifacts | Shared file structure |

### 4.4 Platform-Specific Components

| Component | Claude Code | Copilot |
|-----------|-------------|---------|
| Agent spawning | `Task()` tool | `#runSubagent` |
| Routing | Orchestrator inline | Handoff buttons or skill |
| Model selection | `model_selection.json` | VS Code settings |
| Tool access | Implicit (all tools) | Explicit `tools` array |
| Prompt composition | `prompt-builder` skill | Skill or inline |

### 4.5 Build Pipeline

```bash
# build.sh
#!/bin/bash

echo "Building agent definitions for both platforms..."

# Compile for Claude Code
python scripts/compile-agents.py --platform claude --output .claude/agents/

# Compile for Copilot
python scripts/compile-agents.py --platform copilot --output .github/agents/

# Compile skills
python scripts/compile-skills.py --platform claude --output .claude/skills/
python scripts/compile-skills.py --platform copilot --output .github/skills/

echo "Build complete."
```

---

## 5. Implementation Plan

### 5.1 Phase 1: Foundation (Weeks 1-2)

**Goal:** Establish abstract definition format and basic compilation.

| Task | Effort | Owner |
|------|--------|-------|
| Design abstract agent YAML schema | 2 days | Architect |
| Implement Claude compiler (preserve current behavior) | 3 days | Developer |
| Implement Copilot compiler (basic `.agent.md` output) | 3 days | Developer |
| Convert `developer.md` to abstract format | 2 days | Developer |
| Validate Claude output matches current | 1 day | QA |

**Deliverables:**
- `scripts/compile-agents.py` with `--platform` flag
- `agents/developer.yaml` abstract definition
- Passing tests for Claude compilation

### 5.2 Phase 2: Core Agents (Weeks 3-4)

**Goal:** Convert all 9 agents to abstract format.

| Agent | Complexity | Effort |
|-------|------------|--------|
| orchestrator | High | 3 days |
| project_manager | High | 2 days |
| developer | Medium (done in Phase 1) | - |
| senior_software_engineer | Medium | 2 days |
| qa_expert | High (5-level challenges) | 3 days |
| tech_lead | High | 2 days |
| investigator | Medium | 1 day |
| requirements_engineer | Medium | 1 day |
| tech_stack_scout | Low | 0.5 day |

**Deliverables:**
- All 9 agents in abstract YAML format
- Passing compilation for both platforms
- Integration tests for workflow routing

### 5.3 Phase 3: Skills & State (Weeks 5-6)

**Goal:** Port critical skills and implement MCP state server.

| Task | Effort | Priority |
|------|--------|----------|
| Design MCP server for `bazinga-db` | 2 days | P0 |
| Implement MCP server (SQLite backend) | 4 days | P0 |
| Port `prompt-builder` skill | 3 days | P1 |
| Port `workflow-router` skill | 2 days | P1 |
| Port `specialization-loader` skill | 2 days | P1 |
| Test MCP integration with Copilot | 2 days | P0 |

**Deliverables:**
- `bazinga-mcp-server` npm package
- Copilot-compatible skill definitions
- MCP integration tests

### 5.4 Phase 4: Orchestration (Week 7)

**Goal:** Implement Copilot-compatible orchestration.

| Task | Effort |
|------|--------|
| Design Copilot orchestration pattern | 2 days |
| Implement orchestration skill | 3 days |
| Test full workflow in Copilot | 2 days |
| Document differences from Claude workflow | 1 day |

**Deliverables:**
- Copilot orchestration skill
- End-to-end workflow test
- Documentation of platform differences

### 5.5 Phase 5: Testing & Documentation (Week 8)

**Goal:** Comprehensive testing and documentation.

| Task | Effort |
|------|--------|
| Integration tests for both platforms | 2 days |
| Performance comparison (Claude vs Copilot) | 1 day |
| Migration guide documentation | 2 days |
| Team training materials | 2 days |
| Bug fixes and polish | 1 day |

**Deliverables:**
- Test suite with 95%+ coverage
- Performance benchmark report
- Migration guide
- Training materials

### 5.6 Effort Summary

| Phase | Duration | Effort |
|-------|----------|--------|
| Phase 1: Foundation | 2 weeks | 11 days |
| Phase 2: Core Agents | 2 weeks | 14.5 days |
| Phase 3: Skills & State | 2 weeks | 15 days |
| Phase 4: Orchestration | 1 week | 8 days |
| Phase 5: Testing & Docs | 1 week | 8 days |
| **Total** | **8 weeks** | **56.5 days** |

### 5.7 Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Copilot API changes | Medium | High | Abstract layer insulates from changes |
| MCP performance issues | Medium | Medium | Load testing in Phase 3 |
| Workflow routing gaps | High | High | Early spike in Phase 1 |
| Team adoption resistance | Low | Medium | Training and documentation |
| Feature parity gaps | High | Medium | Document differences, plan workarounds |

---

## 6. Open Questions

### 6.1 Technical Questions

| # | Question | Impact | Resolution Path |
|---|----------|--------|-----------------|
| 1 | How does Copilot handle parallel agent execution? | High | Spike test in Phase 1 |
| 2 | Can MCP servers maintain persistent connections? | High | Test in Phase 3 |
| 3 | What's the max context size for Copilot sub-agents? | Medium | Documentation review |
| 4 | Can handoffs include structured context (JSON)? | High | Experiment in Phase 2 |
| 5 | How does Copilot handle agent failures/crashes? | Medium | Error handling spike |
| 6 | Is there rate limiting on `#runSubagent` calls? | Medium | Test at scale |

### 6.2 Architectural Decisions Needed

| # | Decision | Options | Recommendation |
|---|----------|---------|----------------|
| 1 | Where to store abstract definitions? | `agents/` vs `abstract/` | New `abstract/agents/` directory |
| 2 | How to handle orchestration in Copilot? | Skill vs inline vs external | Custom orchestration skill |
| 3 | MCP server hosting | Local vs cloud | Local first, cloud option later |
| 4 | Handoff trigger mechanism | Buttons vs auto-send | Auto-send with confirmation |
| 5 | Specialization in Copilot | Inline vs skill | Skill (matches Claude) |

### 6.3 Process Questions

| # | Question | Owner |
|---|----------|-------|
| 1 | Who owns the abstract definition format? | Architect |
| 2 | How do we version agent definitions? | Team decision |
| 3 | CI/CD for dual compilation? | DevOps |
| 4 | Testing strategy for both platforms? | QA Lead |
| 5 | Rollback plan if Copilot adoption fails? | PM |

### 6.4 Questions for Copilot Team

1. **Handoff context:** Can structured data (JSON) be passed in handoff messages, or only plain text?
2. **Sub-agent limits:** Is there a maximum number of concurrent sub-agents?
3. **State persistence:** Are there plans for native state persistence (vs MCP)?
4. **Model routing:** Can different agents use different models (GPT-4 vs GPT-3.5)?
5. **Custom tools:** Can custom tools be defined beyond the built-in set?
6. **Workspace scope:** Do sub-agents have access to full workspace or limited scope?

---

## Appendix A: Agent Comparison Matrix

| Agent | Lines (Claude) | Status Codes | Handoffs | Escalation | Conditional |
|-------|----------------|--------------|----------|------------|-------------|
| orchestrator | 2000+ | N/A (routes others) | All agents | N/A | N/A |
| project_manager | 440 | 5 | developer, RE | N/A | N/A |
| developer | 1250 | 4 | qa_expert, tech_lead | SSE | N/A |
| senior_software_engineer | 1459 | 4 | qa_expert, tech_lead | N/A | N/A |
| qa_expert | 1556 | 5 | developer, tech_lead | SSE (L3+) | tests exist |
| tech_lead | 1557 | 4 | developer, PM | investigator | N/A |
| investigator | 1227 | 5 | developer, tech_lead | N/A | max 5 iter |
| requirements_engineer | 887 | 3 | tech_lead | N/A | `[R]` groups |
| tech_stack_scout | 475 | 1 | PM | N/A | Step 0.5 |

---

## Appendix B: Status Code Reference

### Developer Status Codes
```
READY_FOR_QA         → qa_expert (when tests exist)
READY_FOR_REVIEW     → tech_lead (bypasses QA)
BLOCKED              → investigator or PM
ESCALATE_SENIOR      → senior_software_engineer
```

### QA Expert Status Codes
```
PASS                 → tech_lead
FAIL                 → developer
FAIL_ESCALATE        → senior_software_engineer (L3+ failures)
FLAKY                → developer (with flaky test guidance)
BLOCKED              → PM
```

### Tech Lead Status Codes
```
APPROVED             → PM (next assignment)
CHANGES_REQUESTED    → developer
SPAWN_INVESTIGATOR   → investigator
UNBLOCKING_GUIDANCE  → developer (with guidance)
```

### Project Manager Status Codes
```
PLANNING_COMPLETE    → orchestrator starts execution
CONTINUE             → next task group
IN_PROGRESS          → waiting for agent completion
BAZINGA              → session complete (terminal)
NEEDS_CLARIFICATION  → user interaction required
```

---

## Appendix C: Copilot `.agent.md` Template

```yaml
---
name: {agent_name}
description: "{agent_description}"
tools:
  - filesystem
  - terminal
  - code_search
  - github_api
handoffs:
  - name: {target_agent_1}
    description: "{handoff_description}"
    send: false  # true for auto-send
  - name: {target_agent_2}
    description: "{handoff_description}"
    send: false
---

# {Agent Title}

## Purpose
{Brief agent purpose - 2-3 sentences}

## Capabilities
- {Capability 1}
- {Capability 2}
- {Capability 3}

## Workflow
1. {Step 1}
2. {Step 2}
3. {Step 3}

## Output Format
{Expected output structure}

## Handoff Triggers
- **{target_agent_1}**: When {condition}
- **{target_agent_2}**: When {condition}
```

---

## Appendix D: File Structure After Migration

```
project-root/
├── abstract/                    # NEW: Abstract definitions
│   ├── agents/
│   │   ├── developer.yaml
│   │   ├── project_manager.yaml
│   │   └── ...
│   ├── skills/
│   │   ├── bazinga-db.yaml
│   │   └── ...
│   └── workflows/
│       └── standard.yaml
│
├── .claude/                     # Claude Code (compiled)
│   ├── agents/
│   │   ├── developer.md
│   │   └── ...
│   ├── commands/
│   └── skills/
│
├── .github/                     # Copilot (compiled)
│   ├── agents/
│   │   ├── developer.agent.md
│   │   └── ...
│   └── skills/
│
├── bazinga/                     # Shared state
│   ├── bazinga.db              # SQLite (accessed via MCP)
│   └── templates/              # Shared specializations
│
└── scripts/
    ├── compile-agents.py        # Abstract → Platform
    ├── compile-skills.py
    └── build.sh
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1 | 2026-01-23 | Backend Architect | Initial draft |

---

## References

1. `research/copilot-agents-skills-implementation-deep-dive.md` - Copilot architecture analysis
2. `agents/*.md` - Current BAZINGA agent definitions
3. `bazinga/model_selection.json` - Model configuration
4. `.claude/skills/bazinga-db/` - State management skill
5. `.claude/skills/prompt-builder/` - Prompt composition skill
