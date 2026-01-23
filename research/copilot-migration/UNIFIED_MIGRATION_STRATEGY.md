# BAZINGA → GitHub Copilot: Unified Migration Strategy

**Version:** 2.2 (Final Correction)
**Date:** 2026-01-23
**Status:** APPROVED - Ready for Implementation
**Authors:** Multi-Agent Analysis Team (Claude, Gemini)
**Final Review:** APPROVE WITH CHANGES - All changes incorporated
**Revision v2.1:** Corrected agent spawning - `#runSubagent` enables programmatic spawning
**Revision v2.2:** Corrected parallelism - Parallel execution NOW SUPPORTED (PR #2839 merged Jan 15, 2026)

---

## Executive Summary

This document synthesizes 10 individual migration analyses into a unified strategy for adding GitHub Copilot support to BAZINGA while maintaining full Claude Code compatibility. All analyses received **APPROVE** or **APPROVE WITH CHANGES** verdicts from multi-model debate.

### Key Findings

| Finding | Impact | Decision |
|---------|--------|----------|
| Copilot supports `#runSubagent` for programmatic spawning | **Low** | Use `#runSubagent` tool in agent prompts - full parity with Task() |
| ~~Copilot runs subagents sequentially only~~ | ~~Medium~~ | **RESOLVED**: Parallel execution merged Jan 15, 2026 (PR #2839) |
| **Parallel execution supported** (same block = parallel) | **None** | TRUE feature parity with Claude Code |
| Copilot has no per-agent model selection | **Medium** | Accept limitation - escalation provides workflow benefits only |
| Copilot Cloud agents have no local filesystem | **High** | SQLite for Local, defer MCP for Cloud to post-MVP |
| Skills format is 95% compatible | **Low** | Minor adaptations required |
| Database schema is platform-agnostic | **Low** | Shared bazinga.db works for both platforms |

### Recommended Approach

**Dual-Platform Architecture** with platform abstraction layer:
- Claude Code: Full autonomous orchestration with parallel agents (current behavior)
- Copilot Local: **Full autonomous orchestration with parallel agents** (same capability!)
- Copilot Cloud: Deferred to post-MVP (requires MCP infrastructure)

### Timeline Summary (Revised per Final Debate)

| Phase | Duration | Focus |
|-------|----------|-------|
| **Phase 0** | Week 0-1 | **Tech Spike with Go/No-Go Decision** |
| Phase 1 | Weeks 2-3 | Core abstraction layer |
| Phase 2 | Weeks 4-5 | Agent & Skill migration |
| Phase 3 | Weeks 6-7 | CLI dual-platform support |
| Phase 4 | Weeks 8-10 | Template system + Prompt-builder refactor |
| Phase 5 | Weeks 11-12 | Integration testing |
| Phase 6 | Weeks 13-14 | Documentation & hardening |

**Total: 14-15 weeks** (revised from 12 weeks based on final debate feedback)

---

## Table of Contents

1. [Platform Comparison](#1-platform-comparison)
2. [Architecture Design](#2-architecture-design)
3. [Component Migration Summary](#3-component-migration-summary)
4. [Cross-Feature Dependencies](#4-cross-feature-dependencies)
5. [Critical Blockers & Mitigations](#5-critical-blockers--mitigations)
6. [Implementation Roadmap](#6-implementation-roadmap)
7. [Risk Assessment](#7-risk-assessment)
8. [Acceptance Criteria](#8-acceptance-criteria)

---

## 1. Platform Comparison

### 1.1 Feature Parity Matrix (UPDATED Jan 23, 2026)

| Capability | Claude Code | Copilot Local | Copilot Cloud |
|------------|-------------|---------------|---------------|
| Agent spawning | Task() - programmatic | `#runSubagent` - programmatic | `#runSubagent` - programmatic |
| Parallel agents | Up to 4 concurrent | **Up to N concurrent** (same block) | **Up to N concurrent** (same block) |
| Model selection | Per-agent (haiku/sonnet/opus) | Platform-controlled | Platform-controlled |
| Skill invocation | Skill(command: "x") explicit | Auto-activation + `#tool:runSubagent` | Auto-activation |
| State persistence | SQLite via skill | SQLite (local) | No local storage |
| Hooks | .claude/hooks/ | N/A | N/A |
| Slash commands | 14 commands | Custom Agents + Skills | Custom Agents + Skills |

**Note:** Parallel subagent execution added in [PR #2839](https://github.com/microsoft/vscode-copilot-chat/pull/2839), merged January 15, 2026.

### 1.2 Agent Spawning Mechanism Comparison

**Claude Code:**
```
Task(subagent_type="developer", prompt="Implement JWT auth")
// Spawns agent in parallel, returns when complete
```

**Copilot (via `#runSubagent`):**
```yaml
# In agent frontmatter:
tools:
  - runSubagent
```
```
# In agent prompt/output:
"Use the @developer subagent to implement JWT authentication #runSubagent"
// OR: Direct tool invocation in prompt
"Evaluate #file:auth.py using #runSubagent with @developer"
```

**Key Difference:** Claude supports parallel spawning; Copilot executes sequentially.

### 1.3 Workflow Comparison

**Claude Code (Parallel):**
```
User: /orchestrate implement JWT auth
     ↓ (automatic)
Orchestrator spawns PM
     ↓ (automatic)
PM spawns Dev1, Dev2, Dev3, Dev4 (parallel)
     ↓ (automatic, parallel execution)
All Devs complete → QA spawned
     ↓ (automatic)
BAZINGA complete
```

**Copilot (Sequential via #runSubagent):**
```
User: @bazinga-orchestrator implement JWT auth
     ↓ (automatic via #runSubagent)
Orchestrator spawns PM via #runSubagent
     ↓ (automatic via #runSubagent)
PM spawns Dev1 → waits → Dev2 → waits → Dev3 → waits → Dev4 (sequential)
     ↓ (automatic via #runSubagent)
All Devs complete → QA spawned
     ↓ (automatic)
BAZINGA complete
```

**Trade-off:** Copilot is **slower** (sequential) but **equally autonomous**.

---

## 2. Architecture Design

### 2.1 Dual-Platform Abstraction Layer

```
┌─────────────────────────────────────────────────────────────────┐
│                    BAZINGA APPLICATION LAYER                     │
│  (Agents, Skills, Orchestration Logic, Templates)               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PLATFORM ABSTRACTION LAYER                    │
│                                                                  │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐  │
│  │ AgentSpawner    │  │ SkillInvoker     │  │ StateBackend   │  │
│  │ Interface       │  │ Interface        │  │ Interface      │  │
│  └────────┬────────┘  └────────┬─────────┘  └───────┬────────┘  │
│           │                    │                    │            │
└───────────┼────────────────────┼────────────────────┼────────────┘
            │                    │                    │
    ┌───────┴───────┐    ┌───────┴───────┐    ┌───────┴───────┐
    │               │    │               │    │               │
┌───┴───┐       ┌───┴───┐│           ┌───┴───┐│           ┌───┴───┐
│Claude │       │Copilot││           │Claude ││           │SQLite │
│Spawner│       │Spawner││           │Skill  ││           │Backend│
└───────┘       └───────┘│           │Invoker││           └───────┘
                         │           └───────┘│
                     ┌───┴───┐            ┌───┴───┐
                     │Copilot│            │File   │
                     │Skill  │            │Backend│
                     │Invoker│            └───────┘
                     └───────┘
```

### 2.2 Platform Detection Strategy

```python
class PlatformDetector:
    @staticmethod
    def detect() -> Platform:
        # Priority 1: Explicit environment variable
        if os.environ.get("BAZINGA_PLATFORM"):
            return Platform(os.environ["BAZINGA_PLATFORM"])

        # Priority 2: Platform-specific indicators
        if os.environ.get("CLAUDE_CODE_SESSION"):
            return Platform.CLAUDE_CODE
        if os.environ.get("GITHUB_COPILOT_AGENT_ID"):
            return Platform.COPILOT

        # Priority 3: Directory structure (less reliable)
        if Path(".github/agents").exists():
            return Platform.COPILOT
        if Path(".claude/agents").exists():
            return Platform.CLAUDE_CODE

        # Default
        return Platform.CLAUDE_CODE
```

### 2.3 File Structure (Dual-Platform)

```
project/
├── .claude/                      # Claude Code specific
│   ├── agents/                   # Agent definitions
│   ├── commands/                 # Slash commands
│   ├── skills/                   # Skills (also read by Copilot)
│   ├── hooks/                    # Hooks (Claude only)
│   └── CLAUDE.md                 # Instructions
│
├── .github/                      # Copilot specific
│   ├── agents/                   # Custom agents (*.agent.md)
│   ├── copilot-instructions.md   # Copilot global instructions
│   └── skills -> ../.claude/skills  # Symlink (or copy on Windows)
│
├── bazinga/                      # Shared runtime
│   ├── bazinga.db                # SQLite database
│   ├── templates/                # Specialization templates
│   ├── config/                   # Workflow configuration
│   ├── model_selection.json      # Model assignments (Claude only)
│   ├── skills_config.json        # Skills configuration
│   └── challenge_levels.json     # QA challenge levels
│
└── shared/                       # Source templates (build-time)
    ├── agent-prompts/            # Shared agent logic
    └── templates/                # Shared templates
```

---

## 3. Component Migration Summary

### 3.1 Agents (M1)

| Component | Migration Approach | Effort |
|-----------|-------------------|--------|
| 10 agent definitions | Hybrid: agents/*.md + .github/agents/*.agent.md | Medium |
| Agent frontmatter | Transform: remove `model`, add `tools` | Low |
| Task() spawning | Replace with `#runSubagent` tool | Medium |

**Key Changes:**
- Filename: `developer.md` → `developer.agent.md`
- Frontmatter: Remove `model` field, add `tools` array
- Body: Replace `Task()` references with `#runSubagent`

### 3.2 Skills (M2)

| Tier | Skills | Migration Approach | Effort |
|------|--------|-------------------|--------|
| Tier 1 (Direct) | lint-check, security-scan, test-coverage | Copy to .github/skills/ | Low |
| Tier 2 (Moderate) | codebase-analysis, pattern-miner | Adapt invocation patterns | Medium |
| Tier 3 (Significant) | prompt-builder, specialization-loader | Platform abstraction | High |
| Tier 4 (Do Not Migrate) | bazinga-db, workflow-router, bazinga-validator | Keep Claude-only | N/A |

**Debate Feedback Applied:**
- Auto-activation reliability is a concern - add explicit trigger phrases in descriptions
- Python script execution needs verification on Copilot

### 3.3 Orchestration (M3)

| Approach | Description | Feasibility |
|----------|-------------|-------------|
| **Option A: `#runSubagent`** | Use built-in tool for agent spawning | **Recommended** - near-parity with Task() |
| Option B: VS Code Extension | Programmatic via extension API | Overkill now that #runSubagent exists |
| Option C: Handoffs only | User-driven buttons | Fallback if #runSubagent unreliable |

**Key Discovery:** Copilot's `#runSubagent` tool allows agents to programmatically spawn sub-agents:
```
# Enable in agent frontmatter:
tools:
  - runSubagent

# Use in agent output:
"Use @project-manager to analyze requirements #runSubagent"
```

**Remaining Limitation:** Sequential execution only (no parallel spawning like Claude's Task())

**Tech Spike Focus (Updated):**
- Verify `#runSubagent` reliability in orchestration chains
- Test state preservation across sub-agent calls
- Measure latency of sequential vs parallel execution

### 3.4 Commands (M4)

| Command Type | Copilot Implementation |
|--------------|----------------------|
| Orchestration (3) | Custom Agents with `#runSubagent` chains |
| Configuration (2) | Auto-activating Skills |
| Spec-Kit (9) | Auto-activating Skills |

**Total: 14 commands → 7 agents + 11 skills**

### 3.5 Configuration (M5)

| Config File | Copilot Handling |
|-------------|-----------------|
| model_selection.json | Ignored (platform limitation) |
| skills_config.json | Shared, accessed via ConfigProvider |
| challenge_levels.json | Shared, embedded in QA agent body |

**Debate Feedback Applied:**
- Add JSON Schema validation
- Complete ConfigProvider interface with all required methods

### 3.6 Templates (M6)

| Category | Files | Migration |
|----------|-------|-----------|
| Agent workflow | 23 | Shared, platform-specific paths |
| Orchestration | 4 | Shared, platform-specific paths |
| Specializations | 72 | Shared via Python processing |

**Debate Feedback Applied:**
- Extend timeline to 6 weeks (from 4 weeks)
- Add verification marker for version guard application
- Reframe token budgets as tier-based (not model-specific)

### 3.7 Database (M7)

| Backend | Platform | Priority |
|---------|----------|----------|
| SQLiteBackend | Claude Code, Copilot Local | MVP |
| FileBackend | Fallback | MVP |
| InMemoryBackend | Degraded mode | MVP |
| MCPBackend | Copilot Cloud | Post-MVP |

**Debate Feedback Applied:**
- Defer MCPBackend to post-MVP
- Add capability probing before backend selection
- Add atomic writes and locking to FileBackend

### 3.8 CLI (M8)

| Feature | Implementation |
|---------|---------------|
| --platform flag | CLAUDE, COPILOT, BOTH, AUTO |
| Auto-detection | Based on .claude/agents/ and .github/agents/ |
| Agent transformation | Automatic during install |
| Skills strategy | Symlink on Unix, copy on Windows |

**Debate Feedback Applied:**
- Extend timeline to 12-14 days (from 9 days)
- Add Windows symlink fallback logic
- Improve auto-detection to avoid false positives

### 3.9 Dashboard (M9)

| Phase | Action | Effort |
|-------|--------|--------|
| Immediate | Use existing dashboards unchanged | None |
| Short-term | Add platform column to sessions | Low |
| Optional | VS Code webview (if requested) | High |

**Debate Verdict:** APPROVE (no changes required)

### 3.10 Abstraction Layer (M10)

| Interface | Purpose |
|-----------|---------|
| PlatformAdapter | Entry point for platform-specific operations |
| AgentSpawner | Spawn agents (Task vs #runSubagent) |
| SkillInvoker | Invoke skills (explicit vs auto) |
| StateBackend | Persist state (SQLite vs File vs MCP) |
| ConfigProvider | Load configuration |
| TemplateLoader | Load and process templates |

---

## 4. Cross-Feature Dependencies

### 4.1 Dependency Graph

```
                    ┌──────────────────┐
                    │ M10: Abstraction │
                    │     Layer        │
                    └────────┬─────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│ M1: Agents     │  │ M7: Database   │  │ M6: Templates  │
└───────┬────────┘  └───────┬────────┘  └───────┬────────┘
        │                   │                   │
        ▼                   ▼                   ▼
┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│ M2: Skills     │  │ M3: Orchestr.  │  │ M5: Config     │
└───────┬────────┘  └───────┬────────┘  └───────┬────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                            ▼
                    ┌────────────────┐
                    │ M4: Commands   │
                    └───────┬────────┘
                            │
                            ▼
                    ┌────────────────┐
                    │ M8: CLI        │
                    └───────┬────────┘
                            │
                            ▼
                    ┌────────────────┐
                    │ M9: Dashboard  │
                    └────────────────┘
```

### 4.2 Critical Path

1. **M10 (Abstraction Layer)** must be implemented first - all other components depend on it
2. **M7 (Database)** must be ready before M3 (Orchestration) can work
3. **M1 (Agents) + M2 (Skills)** can proceed in parallel once M10 is done
4. **M8 (CLI)** is the integration point - must wait for M1, M2, M6, M7
5. **M9 (Dashboard)** has no blockers - can proceed independently

### 4.3 Conflict Resolution

| Conflict | Resolution |
|----------|------------|
| M3 timeline (11-15 weeks) vs M4 timeline (8 weeks) | Use M3's longer estimate for realistic planning |
| M5 suggests embedding config in agents vs M10's abstraction | Use abstraction for runtime, embed for fallback only |
| M2 skill auto-activation vs M4 command explicit invocation | Skills for utilities, Agents for orchestration |

---

## 5. Critical Blockers & Mitigations

### 5.1 ~~BLOCKER~~ RESOLVED: Copilot Agent Spawning via `#runSubagent`

**Original Concern:** Core BAZINGA automation would be lost without programmatic spawning

**Resolution:** Copilot's `#runSubagent` tool provides programmatic agent spawning:
- Agents can include `runSubagent` in their `tools` frontmatter
- Output like `"Use @project-manager to analyze #runSubagent"` spawns the sub-agent
- Works automatically without user intervention

**Remaining Limitations:**
1. **Sequential only** - Multiple `#runSubagent` calls execute one at a time (no parallel)
2. **Single model** - Cannot specify model per sub-agent
3. **Reliability TBD** - Need to validate in tech spike

**Decision:** Use `#runSubagent` as primary approach; handoffs as fallback only

**Required Action:** Technical spike to validate `#runSubagent` chain reliability

### 5.2 ~~LIMITATION~~ RESOLVED: Parallel Execution Now Supported

**Original Concern:** BAZINGA's parallel developer spawning would run sequentially on Copilot

**Resolution (Jan 15, 2026):** [PR #2839](https://github.com/microsoft/vscode-copilot-chat/pull/2839) merged parallel subagent support

**How it works:**
- Multiple `#runSubagent` calls in **same response block** → **parallel execution**
- Separate response blocks → sequential execution

**Decision:** TRUE feature parity achieved - no mitigation needed

### 5.3 BLOCKER: No Per-Agent Model Selection on Copilot

**Impact:** Escalation from Developer→SSE loses capability upgrade

**Mitigation:**
- Document that escalation provides workflow benefits (fresh context, different instructions) not capability upgrades
- Consider simplifying escalation path on Copilot

**Decision:** Accept limitation with clear documentation

### 5.3 BLOCKER: Copilot Cloud Has No Local Filesystem

**Impact:** SQLite-based state persistence doesn't work

**Mitigation:**
- **MVP:** Copilot Cloud uses InMemoryBackend (degraded mode with warnings)
- **Post-MVP:** Implement MCPBackend with remote state server

**Decision:** Defer Copilot Cloud full support to post-MVP

### 5.4 BLOCKER: Windows Symlinks Unreliable

**Impact:** Skills sharing strategy breaks on Windows

**Mitigation:**
```python
if platform.system() == "Windows":
    shutil.copytree(source, dest)  # Copy instead of symlink
else:
    os.symlink(source, dest)
```

**Decision:** Always copy on Windows, symlink on Unix

---

## 6. Implementation Roadmap

### Phase 0: Tech Spike with Go/No-Go Decision (Week 0-1) - UPDATED

| Task | Owner | Effort | Deliverable |
|------|-------|--------|-------------|
| `#runSubagent` Chain Test | - | 2 days | Orchestrator→PM→Dev chain working |
| `#runSubagent` State Preservation | - | 1 day | Verify context/state across spawns |
| Python Script Execution Test | - | 1 day | prompt_builder.py on Copilot |
| SQLite Write Test | - | 1 day | Verify writes in Copilot Local |
| Skill Auto-Activation Test | - | 1 day | Test 3 skills activate correctly |
| Go/No-Go Report | - | 1 day | Decision document |

**Go Criteria (ALL must pass):**
- [ ] `#runSubagent` successfully chains 3+ agents (Orchestrator→PM→Dev)
- [ ] State preserved across `#runSubagent` calls (session_id visible to all)
- [ ] Python script execution works reliably on Copilot
- [ ] SQLite writes work in Copilot Local context
- [ ] At least 2/3 test skills activate correctly

**No-Go Impact:**
- Fall back to user-driven handoffs
- Reduced automation (manual clicks between agents)
- Timeline unchanged but UX significantly degraded
- Post-MVP reassessment for parallel execution

---

### Phase 1: Core Abstraction (Weeks 2-3)

| Task | Owner | Effort | Deliverable |
|------|-------|--------|-------------|
| Platform detection module | - | 2 days | `bazinga/platform.py` |
| StateBackend abstraction | - | 3 days | `bazinga/state/backend.py` |
| SQLiteBackend implementation | - | 2 days | Port existing bazinga-db |
| FileBackend implementation | - | 2 days | JSON fallback |
| ConfigProvider abstraction | - | 2 days | `bazinga/config/provider.py` |
| Testing config handling | - | 1 day | testing_config.json support |

**Exit Criteria:**
- [ ] Platform detection works reliably
- [ ] SQLiteBackend passes all existing tests
- [ ] FileBackend handles concurrent access
- [ ] Testing configuration loads on both platforms

### Phase 2: Agent & Skill Migration (Weeks 3-4)

| Task | Owner | Effort | Deliverable |
|------|-------|--------|-------------|
| Agent file transformer | - | 2 days | `scripts/transform_agents.py` |
| Generate .github/agents/*.agent.md | - | 2 days | 10 Copilot agent files |
| Tier 1 skill migration | - | 1 day | 3 skills in .github/skills/ |
| Tier 2 skill adaptation | - | 2 days | 2 skills adapted |
| Skill invocation abstraction | - | 2 days | `bazinga/skills/invoker.py` |

**Exit Criteria:**
- [ ] All agents have Copilot equivalents
- [ ] Tier 1-2 skills work on Copilot
- [ ] `#runSubagent` chain: Orchestrator → PM → Dev → QA → TL tested

### Phase 3: CLI Dual-Platform (Weeks 5-6)

| Task | Owner | Effort | Deliverable |
|------|-------|--------|-------------|
| Add --platform flag | - | 1 day | CLI enum and parsing |
| Auto-detection logic | - | 1 day | Reliable detection |
| copy_agents_for_copilot() | - | 2 days | Agent transformation |
| copy_skills_for_copilot() | - | 1 day | Symlink/copy logic |
| Windows compatibility | - | 2 days | Full Windows testing |
| generate_copilot_instructions() | - | 1 day | From CLAUDE.md |

**Exit Criteria:**
- [ ] `bazinga install --platform=both` works
- [ ] Auto-detection passes all test cases
- [ ] Windows installation works without errors

### Phase 4: Template System (Weeks 7-8)

| Task | Owner | Effort | Deliverable |
|------|-------|--------|-------------|
| Template path abstraction | - | 2 days | Platform-specific paths |
| Version guard verification | - | 2 days | Copilot verification marker |
| Token budget tier mapping | - | 1 day | Tier-based budgets |
| Prompt builder refactor | - | 3 days | Platform-agnostic |
| Specialization loader refactor | - | 2 days | Platform-agnostic |

**Exit Criteria:**
- [ ] 72 specialization templates work on both platforms
- [ ] Version guards verified in Copilot context
- [ ] Token budgets applied correctly

### Phase 5: Integration Testing (Weeks 9-10)

| Task | Owner | Effort | Deliverable |
|------|-------|--------|-------------|
| Simple calculator test (Claude) | - | 1 day | Existing test passes |
| Simple calculator test (Copilot) | - | 2 days | Copilot equivalent |
| Parallel mode test | - | 2 days | Both platforms |
| Cross-platform session | - | 2 days | Start on Claude, view on Copilot |
| Degraded mode testing | - | 1 day | InMemoryBackend |
| CI/CD matrix | - | 2 days | GitHub Actions for both |

**Exit Criteria:**
- [ ] Integration tests pass on both platforms
- [ ] Cross-platform state visibility works
- [ ] CI runs tests on both platforms

### Phase 6: Documentation & Hardening (Weeks 11-12)

| Task | Owner | Effort | Deliverable |
|------|-------|--------|-------------|
| Update CLAUDE.md | - | 2 days | Dual-platform section |
| Create COPILOT.md | - | 2 days | Copilot-specific guide |
| Installation guide | - | 1 day | Quick start for both |
| Migration guide | - | 2 days | Claude→Copilot→Both |
| Bug fixes | - | 3 days | Issues from testing |

**Exit Criteria:**
- [ ] Documentation complete for both platforms
- [ ] No P0/P1 bugs open
- [ ] Ready for user beta

---

## 7. Risk Assessment

### 7.1 Risk Matrix (Updated per Final Debate)

| Risk | Likelihood | Impact | Mitigation | Owner |
|------|------------|--------|------------|-------|
| `#runSubagent` chain unreliable | Medium | High | Fall back to user handoffs | - |
| **Prompt-builder fails on Copilot** | Medium | **Critical** | **Early validation in Phase 0** | - |
| Copilot skill activation unreliable | Medium | Medium | Add explicit trigger phrases | - |
| Timeline slippage | High | **High** | Buffer in Weeks 13-14 | - |
| Cross-platform state inconsistency | Low | High | Schema versioning | - |
| User confusion about dual modes | Medium | **High** | Clear documentation + UX comparison | - |
| Windows installation failures | Medium | Medium | CI testing on Windows | - |
| **Python script execution differs** | Medium | High | **Test in Phase 0 tech spike** | - |
| Sequential execution too slow | Medium | Medium | Accept as Claude advantage; optimize critical paths | - |

### 7.2 Go/No-Go Criteria

**Go Criteria (all must be true):**
- [ ] `#runSubagent` successfully chains 3+ agents
- [ ] SQLiteBackend works in Copilot Local
- [ ] At least Tier 1 skills work on Copilot
- [ ] Simple orchestration flow works with `#runSubagent`

**No-Go Criteria (any triggers re-evaluation):**
- [ ] SQLite cannot write in any Copilot context
- [ ] Copilot skill activation is completely unreliable
- [ ] `#runSubagent` does not pass state between agents
- [ ] Timeline exceeds 16 weeks

---

## 8. Acceptance Criteria

### 8.1 MVP Acceptance (End of Week 12)

**Functional Requirements:**

| # | Requirement | Verification |
|---|-------------|--------------|
| 1 | `bazinga install --platform=both` works | CLI test |
| 2 | All 10 agents available in Copilot | Manual verification |
| 3 | Tier 1-2 skills work in Copilot | Skill invocation test |
| 4 | `#runSubagent`-based orchestration works | End-to-end test |
| 5 | State visible in shared dashboard | Dashboard test |
| 6 | Claude Code functionality unchanged | Regression test |
| 7 | Windows installation works | CI/CD matrix |

**Non-Functional Requirements:**

| # | Requirement | Metric |
|---|-------------|--------|
| 1 | No feature regression on Claude | 100% existing tests pass |
| 2 | Documentation complete | All user guides updated |
| 3 | Cross-platform session viewable | Dashboard shows both platforms |
| 4 | Degraded mode works | InMemoryBackend warning displayed |

### 8.2 Post-MVP Enhancements

| Enhancement | Priority | Effort | Trigger |
|-------------|----------|--------|---------|
| VS Code extension for automation | P1 | 4 weeks | Tech spike success |
| MCPBackend for Copilot Cloud | P2 | 3 weeks | Cloud agent demand |
| Full skills migration (Tier 3) | P2 | 2 weeks | User request |
| VS Code dashboard webview | P3 | 2 weeks | User request |

---

## Appendix A: Debate Summary

| Analysis | Verdict | Key Feedback |
|----------|---------|--------------|
| M1: Agents | APPROVE WITH CHANGES | Add `#runSubagent` chain documentation |
| M2: Skills | APPROVE WITH CHANGES | Concerns about auto-activation reliability |
| M3: Orchestration | APPROVE WITH CHANGES | **Requires tech spike before committing** |
| M4: Commands | APPROVE WITH CHANGES | Reconcile timeline with M3 |
| M5: Configuration | APPROVE WITH CHANGES | Complete ConfigProvider interface |
| M6: Templates | APPROVE WITH CHANGES | Extend timeline to 6 weeks |
| M7: Database | APPROVE WITH CHANGES | Defer MCP to post-MVP |
| M8: CLI | APPROVE WITH CHANGES | Windows symlink fallback required |
| M9: Dashboard | APPROVE | No changes required |
| M10: Abstraction | APPROVE WITH CHANGES | Validate parallelism gap |

---

## Appendix B: Individual Analysis Documents

| ID | Document | Status |
|----|----------|--------|
| M1 | `01-agent-system-analysis.md` | Complete, Debated |
| M2 | `02-skills-system-analysis.md` | Complete, Debated |
| M3 | `03-orchestration-analysis.md` | Complete, Debated |
| M4 | `04-commands-analysis.md` | Complete, Debated |
| M5 | `05-configuration-analysis.md` | Complete, Debated |
| M6 | `06-templates-analysis.md` | Complete, Debated |
| M7 | `07-database-analysis.md` | Complete, Debated |
| M8 | `08-cli-installation-analysis.md` | Complete, Debated |
| M9 | `09-dashboard-analysis.md` | Complete, Debated |
| M10 | `10-abstraction-layer-analysis.md` | Complete, Debated |

---

## Appendix C: Reference Documents

| Document | Purpose |
|----------|---------|
| `research/copilot-agents-skills-implementation-deep-dive.md` | Copilot architecture reference |
| `.claude/CLAUDE.md` | Current BAZINGA architecture |
| `workflow/transitions.json` | State machine rules |
| `bazinga/model_selection.json` | Agent model assignments |
| `bazinga/skills_config.json` | Skill availability rules |

---

---

## Appendix D: User Experience Comparison (FINAL - Jan 23, 2026)

### Workflow Comparison

| Scenario | Claude Code | Copilot (via #runSubagent) |
|----------|-------------|----------------------------|
| Start orchestration | `/orchestrate implement JWT auth` | `@bazinga-orchestrator implement JWT auth` |
| Agent transitions | Automatic (parallel possible) | **Automatic (parallel possible)** |
| Parallel development | Up to 4 concurrent agents | **Up to N concurrent agents** (same block) |
| Error recovery | Automatic escalation to SSE | Automatic escalation to SSE |
| QA testing | Automatic 5-level progression | Automatic 5-level progression |
| Completion | Automatic BAZINGA | Automatic BAZINGA |

### Estimated Time Overhead

| Workflow Complexity | Claude Code | Copilot | Overhead |
|---------------------|-------------|---------|----------|
| Simple (1 task group) | ~5 min | ~5 min | **None** |
| Medium (2-3 task groups) | ~10 min | ~10 min | **None** |
| Complex (4+ task groups, parallel) | ~15 min | ~15 min | **None** |

**Note:** With parallel execution support (PR #2839), there is NO performance overhead.

### User Expectation Setting

**Must communicate to users:**
1. Copilot mode is **functionally identical** to Claude Code for orchestration
2. Parallel execution works (multiple agents in same response block)
3. **Only difference:** Model selection is platform-controlled - no opus/sonnet/haiku choice
4. Same autonomous workflow, same speed, same quality gates

---

## Appendix E: Skill Verification Test Suite (Added per Final Debate)

### Tier 1 Skills (Must Pass for MVP)

| Skill | Test Input | Expected Output | Pass Criteria |
|-------|------------|-----------------|---------------|
| lint-check | Python file with style issues | JSON with findings | At least 1 finding detected |
| security-scan | File with hardcoded secret | Security warning | Secret detected |
| test-coverage | Project with tests | Coverage percentage | Number returned |

### Tier 2 Skills (Should Pass for MVP)

| Skill | Test Input | Expected Output | Pass Criteria |
|-------|------------|-----------------|---------------|
| codebase-analysis | Repository root | Pattern summary | 3+ patterns identified |
| pattern-miner | Git history | Trend insights | Historical data returned |

### Verification Process

```bash
# Run skill verification suite
python3 scripts/verify_copilot_skills.py --tier=1 --platform=copilot
python3 scripts/verify_copilot_skills.py --tier=2 --platform=copilot

# Expected output
Tier 1 Skills: 3/3 passed
Tier 2 Skills: 2/2 passed
```

---

**Document Status:** APPROVED - Ready for Implementation

**Final Debate Verdict:** APPROVE WITH CHANGES (7 changes incorporated)

**Major Revision (2026-01-23):** Corrected agent spawning mechanism
- Original: Assumed user-driven handoffs only
- Corrected v2.1: Copilot's `#runSubagent` enables programmatic spawning
- Corrected v2.2: Parallel execution NOW SUPPORTED (PR #2839 merged Jan 15, 2026)
- Impact: **TRUE feature parity** with Claude Code's Task() - only model selection differs

**Next Steps:**
1. Begin Phase 0: Tech Spike (Week 0-1)
2. Validate `#runSubagent` chain reliability
3. Go/No-Go decision at end of Week 1
4. If GO: Proceed with Phase 1-6 using `#runSubagent`
5. If NO-GO: Fall back to user-driven handoffs (degraded UX)
