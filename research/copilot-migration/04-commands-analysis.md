# BAZINGA Slash Commands Migration to GitHub Copilot

**Date:** 2026-01-23
**Context:** Analysis of slash command migration strategy for BAZINGA multi-agent orchestration system
**Status:** Proposed
**Depends On:** `01-capabilities-analysis.md`, `02-agents-analysis.md`, `03-skills-analysis.md`

---

## Executive Summary

This document analyzes the migration strategy for BAZINGA's 14 slash commands from Claude Code to GitHub Copilot. The key insight is that **Claude Code slash commands serve two fundamentally different purposes** that require different migration approaches:

1. **Orchestration Commands** (5) - Complex, stateful workflows that coordinate multiple agents
2. **Utility Commands** (9) - Simpler, single-purpose workflows for planning and configuration

**Recommendation:** Hybrid approach using Copilot Custom Agents for orchestration commands (preserving inline execution) and Skills for utility commands (leveraging automatic activation).

---

## Table of Contents

1. [Current State Analysis](#1-current-state-analysis)
2. [Copilot Architecture Constraints](#2-copilot-architecture-constraints)
3. [Command-by-Command Mapping](#3-command-by-command-mapping)
4. [Migration Options](#4-migration-options)
5. [Recommended Strategy](#5-recommended-strategy)
6. [Dual-Platform Support](#6-dual-platform-support)
7. [Implementation Plan](#7-implementation-plan)
8. [Risk Assessment](#8-risk-assessment)

---

## 1. Current State Analysis

### 1.1 Complete Command Inventory

BAZINGA has **14 slash commands** organized into two families:

#### BAZINGA Family (5 commands)

| Command | File Size | Purpose | Complexity |
|---------|-----------|---------|------------|
| `/bazinga.orchestrate` | 89KB | Main multi-agent orchestration entry point | **CRITICAL** |
| `/bazinga.orchestrate-advanced` | 8KB | Enhanced orchestration with Requirements Engineer | HIGH |
| `/bazinga.orchestrate-from-spec` | 20KB | Spec-kit integration for spec-driven orchestration | HIGH |
| `/bazinga.configure-skills` | 11KB | Interactive skill configuration UI | MEDIUM |
| `/bazinga.configure-testing` | 11KB | Interactive testing configuration UI | MEDIUM |

#### Spec-Kit Family (9 commands)

| Command | File Size | Purpose | Complexity |
|---------|-----------|---------|------------|
| `/speckit.specify` | 13KB | Create feature specifications from natural language | MEDIUM |
| `/speckit.plan` | 3KB | Generate technical implementation plans | MEDIUM |
| `/speckit.tasks` | 6KB | Generate actionable task breakdowns | MEDIUM |
| `/speckit.implement` | 8KB | Execute implementation with progress tracking | HIGH |
| `/speckit.analyze` | 7KB | Cross-artifact consistency analysis | MEDIUM |
| `/speckit.clarify` | 11KB | Interactive specification clarification | MEDIUM |
| `/speckit.checklist` | 17KB | Generate requirements quality checklists | MEDIUM |
| `/speckit.constitution` | 5KB | Project constitution management | LOW |
| `/speckit.taskstoissues` | 1KB | Convert tasks to GitHub Issues | LOW |

### 1.2 Command Architecture Patterns

**Pattern 1: Inline Execution (Critical)**
```
User → /command → Command executes in SAME context as user
       ↓
       Spawns agents via Task() tool
       ↓
       Real-time visibility to user
```

The orchestrator (`/bazinga.orchestrate`) MUST run inline to provide real-time visibility. This is the most critical architectural requirement.

**Pattern 2: Agent Spawning**
```
Command → Task(model, prompt) → Sub-agent executes
                              ↓
                              Returns to command
                              ↓
                              Command routes to next agent
```

**Pattern 3: Interactive Configuration**
```
Command → Display menu → Wait for user input → Apply changes
```

**Pattern 4: Chained Commands (Handoffs)**
```yaml
handoffs:
  - label: Build Technical Plan
    agent: speckit.plan
    prompt: Create a plan for the spec...
```

### 1.3 Dependencies

```
┌─────────────────────────────────────────────────────────────┐
│                    DEPENDENCY GRAPH                          │
└─────────────────────────────────────────────────────────────┘

                    /bazinga.orchestrate
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
    bazinga-db     prompt-builder     workflow-router
    (skill)        (skill)            (skill)
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
      agents/*.md              bazinga/templates/
      (agent definitions)      (specializations)

                    /bazinga.orchestrate-advanced
                           │
                           ▼
                    /bazinga.orchestrate
                    (chains to main)

                    /bazinga.orchestrate-from-spec
                           │
        ┌──────────────────┴──────────────────┐
        ▼                                     ▼
    .specify/                         /bazinga.orchestrate
    (spec-kit artifacts)              (chains to main)

                    /speckit.* commands
                           │
                           ▼
                    .specify/scripts/
                    (bash/PowerShell helpers)
```

### 1.4 Invocation Patterns

**Claude Code:**
- Direct invocation: `/command-name arguments`
- Runs inline (same context as user)
- Can invoke other commands: `SlashCommand(command: "/speckit.plan")`
- Can spawn agents: `Task(subagent_type, model, prompt)`

**Key Behavior:**
- Commands are NOT spawned agents - they run in the main context
- This enables real-time progress visibility
- The orchestrator can coordinate multiple agents across many turns

---

## 2. Copilot Architecture Constraints

### 2.1 No Direct Slash Command Equivalent

GitHub Copilot does NOT have a direct equivalent to Claude Code's slash commands:

| Feature | Claude Code | GitHub Copilot |
|---------|-------------|----------------|
| Slash Commands | `/command` runs inline | No equivalent |
| Custom Agents | N/A | `@agent-name` via `.agent.md` |
| Chat Participants | N/A | VS Code extension API (complex) |
| Skills | `Skill(command: "name")` | Auto-activate via SKILL.md |

### 2.2 Custom Agents (.agent.md)

**Location:** `.github/agents/*.agent.md`

**Invocation:** `@agent-name prompt`

**Format:**
```yaml
---
name: orchestrator
description: Multi-agent orchestration coordinator
model: claude-sonnet-4
tools: ["read", "edit", "execute", "github/*"]
handoffs:
  - label: Start Planning
    agent: project-manager
    prompt: Analyze these requirements...
---

# Agent Instructions

You are the orchestrator...
```

**Key Properties:**
- Runs in **isolated context** (like Claude Code's Task())
- Context is separate from main chat session
- Can define **handoffs** for agent-to-agent routing
- Can specify **tools** available to agent

**Limitation for BAZINGA:**
- Handoffs are **user-driven** (buttons), not programmatic
- No equivalent to `Task()` for spawning sub-agents programmatically
- Cannot run inline like Claude Code commands

### 2.3 Skills (SKILL.md)

**Location:** `.github/skills/skill-name/SKILL.md`

**Activation:** Automatic based on prompt matching

**Format:**
```yaml
---
name: bazinga-orchestration
description: |
  Orchestrates multi-agent development workflows.
  Activates when user mentions "orchestrate", "implement feature",
  "build", or describes a multi-step development task.
---

# Orchestration Skill

## When to Use
- User requests feature implementation
- User asks for multi-agent coordination
...
```

**Key Properties:**
- **Automatic activation** based on semantic matching
- **Progressive loading** (frontmatter only until needed)
- No explicit invocation required
- Can include supporting files (scripts, templates)

**Limitation for BAZINGA:**
- Skills can't spawn sub-agents or coordinate workflows
- They only inject instructions into the current context
- Designed for knowledge injection, not orchestration

### 2.4 Sub-Agent Spawning

Copilot's sub-agent system (`#runSubagent`) has key differences:

| Feature | Claude Code Task() | Copilot Sub-Agent |
|---------|-------------------|-------------------|
| Invocation | Programmatic | User-driven or via handoffs |
| Context | Isolated | Isolated |
| Nesting | Multi-level | Single-level only |
| Return | Agent returns to parent | Session ends or button click |
| Parallelism | Concurrent foreground | Sequential only |

**Critical Limitation:** Copilot cannot programmatically spawn multiple concurrent sub-agents like BAZINGA's parallel developer workflow.

---

## 3. Command-by-Command Mapping

### 3.1 Orchestration Commands

#### `/bazinga.orchestrate` - Main Orchestrator

**Current Behavior:**
- Runs inline for real-time visibility
- Spawns PM, Developers, QA, Tech Lead via `Task()`
- Coordinates via database and skills
- Manages state across many turns

**Copilot Options:**

| Option | Implementation | Feasibility | Limitations |
|--------|---------------|-------------|-------------|
| Custom Agent | `.github/agents/orchestrator.agent.md` | PARTIAL | No programmatic Task(), handoffs only |
| Skill | Auto-inject orchestration logic | POOR | Can't coordinate agents |
| Chat Participant | VS Code extension | FULL | Requires extension development |

**Recommended:** Custom Agent with handoffs, accepting reduced automation

**Mapping:**
```yaml
---
name: bazinga-orchestrator
description: |
  Coordinates multi-agent development team.
  Use @bazinga-orchestrator to start orchestration.
model: claude-sonnet-4
tools: ["read", "edit", "execute", "github/*"]
handoffs:
  - label: Plan with PM
    agent: project-manager
    prompt: Analyze requirements and create task breakdown
  - label: Assign Developer
    agent: developer
    prompt: Implement the assigned tasks
  - label: Run QA Tests
    agent: qa-expert
    prompt: Test the implementation
  - label: Code Review
    agent: tech-lead
    prompt: Review the implementation
---
```

**Workflow Change:**
- Claude Code: Automatic agent routing
- Copilot: User clicks handoff buttons

#### `/bazinga.orchestrate-advanced`

**Current:** Spawns Requirements Engineer first, then chains to main orchestrator

**Copilot Mapping:**
```yaml
---
name: bazinga-orchestrator-advanced
handoffs:
  - label: Discover Requirements
    agent: requirements-engineer
    prompt: Analyze and discover requirements
  - label: Start Orchestration
    agent: bazinga-orchestrator
    prompt: Execute with enhanced requirements
---
```

#### `/bazinga.orchestrate-from-spec`

**Current:** Integrates spec-kit artifacts, chains to main orchestrator

**Copilot Mapping:** Custom Agent that reads `.specify/` artifacts, then hands off

#### `/bazinga.configure-skills` & `/bazinga.configure-testing`

**Current:** Interactive menu for JSON configuration

**Copilot Mapping:** Skill (auto-activates on "configure skills/testing")
- Skill injects instructions for interactive configuration
- User provides choices in chat
- Agent updates `bazinga/*.json` files

### 3.2 Spec-Kit Commands

These are simpler and map well to Skills:

| Command | Copilot Implementation | Activation Trigger |
|---------|----------------------|-------------------|
| `/speckit.specify` | Skill | "create spec", "specify feature" |
| `/speckit.plan` | Skill | "create plan", "technical plan" |
| `/speckit.tasks` | Skill | "generate tasks", "break down" |
| `/speckit.implement` | Skill | "implement tasks", "execute plan" |
| `/speckit.analyze` | Skill | "analyze spec", "check consistency" |
| `/speckit.clarify` | Skill | "clarify spec", "resolve ambiguity" |
| `/speckit.checklist` | Skill | "generate checklist", "requirements quality" |
| `/speckit.constitution` | Skill | "update constitution", "project principles" |
| `/speckit.taskstoissues` | Skill | "create issues", "tasks to github" |

**Example Skill:**
```yaml
---
name: speckit-specify
description: |
  Creates feature specifications from natural language descriptions.
  Activates for: "create a spec", "specify feature", "write specification"
---

# Specify Feature Skill

## When to Use
- User wants to create a new feature specification
- User has a feature description to formalize

## Instructions
1. Generate short name for branch
2. Run `.specify/scripts/bash/create-new-feature.sh`
3. Load spec template from `.specify/templates/spec-template.md`
4. Fill template based on user's description
...
```

### 3.3 Handoffs Configuration

Current Claude Code handoffs:
```yaml
handoffs:
  - label: Build Technical Plan
    agent: speckit.plan
    prompt: Create a plan for the spec
```

Copilot equivalent:
```yaml
handoffs:
  - label: Build Technical Plan
    agent: speckit-plan  # References .github/agents/speckit-plan.agent.md
    prompt: Create a plan for the spec
    send: true  # Auto-submit (no user edit)
```

---

## 4. Migration Options

### Option A: All Custom Agents

**Approach:** Convert all 14 commands to Custom Agents

**Structure:**
```
.github/
└── agents/
    ├── bazinga-orchestrator.agent.md
    ├── bazinga-orchestrator-advanced.agent.md
    ├── bazinga-orchestrator-from-spec.agent.md
    ├── bazinga-configure-skills.agent.md
    ├── bazinga-configure-testing.agent.md
    ├── speckit-specify.agent.md
    ├── speckit-plan.agent.md
    ├── speckit-tasks.agent.md
    ├── speckit-implement.agent.md
    ├── speckit-analyze.agent.md
    ├── speckit-clarify.agent.md
    ├── speckit-checklist.agent.md
    ├── speckit-constitution.agent.md
    └── speckit-taskstoissues.agent.md
```

**Pros:**
- Explicit invocation (`@agent-name`)
- Clear mental model for users
- Handoffs for chaining

**Cons:**
- No automatic activation
- User must know agent names
- Orchestration agents can't spawn sub-agents programmatically

### Option B: All Skills

**Approach:** Convert all 14 commands to Skills

**Structure:**
```
.github/
└── skills/
    ├── bazinga-orchestrate/SKILL.md
    ├── bazinga-configure/SKILL.md
    ├── speckit-specify/SKILL.md
    ├── speckit-plan/SKILL.md
    └── ... (9 more)
```

**Pros:**
- Automatic activation
- No explicit invocation needed
- Progressive loading (efficient)

**Cons:**
- Skills can't coordinate agents
- Orchestration commands don't fit skill model
- No programmatic sub-agent spawning

### Option C: Hybrid (Recommended)

**Approach:**
- **Custom Agents** for orchestration (requires coordination)
- **Skills** for utility commands (knowledge injection)

**Structure:**
```
.github/
├── agents/
│   ├── bazinga-orchestrator.agent.md      # Main orchestration
│   ├── bazinga-orchestrator-advanced.agent.md
│   ├── bazinga-orchestrator-from-spec.agent.md
│   ├── project-manager.agent.md           # PM agent
│   ├── developer.agent.md                 # Developer agent
│   ├── qa-expert.agent.md                 # QA agent
│   └── tech-lead.agent.md                 # Tech Lead agent
│
└── skills/
    ├── speckit-specify/SKILL.md
    ├── speckit-plan/SKILL.md
    ├── speckit-tasks/SKILL.md
    ├── speckit-implement/SKILL.md
    ├── speckit-analyze/SKILL.md
    ├── speckit-clarify/SKILL.md
    ├── speckit-checklist/SKILL.md
    ├── speckit-constitution/SKILL.md
    ├── speckit-taskstoissues/SKILL.md
    ├── bazinga-configure-skills/SKILL.md  # Config as skills
    └── bazinga-configure-testing/SKILL.md
```

**Pros:**
- Best fit for each command type
- Orchestration uses handoffs for agent routing
- Utility commands auto-activate
- Configuration is conversational

**Cons:**
- Two different invocation patterns
- Orchestration workflow is semi-automated (user clicks handoffs)

---

## 5. Recommended Strategy

### 5.1 Strategy Overview

**Adopt Hybrid Approach (Option C)** with these mappings:

| Command Type | Claude Code | Copilot | Why |
|-------------|-------------|---------|-----|
| Orchestration | Inline command | Custom Agent | Needs handoffs for agent routing |
| Configuration | Interactive menu | Skill | Conversational, auto-activates |
| Spec-kit utilities | Command | Skill | Knowledge injection, auto-activates |
| Agent definitions | `agents/*.md` | `.github/agents/*.agent.md` | Different format, same purpose |
| Skills | `.claude/skills/` | `.github/skills/` | Same format, different location |

### 5.2 Orchestration Workflow Change

**Claude Code (Current):**
```
User: /orchestrate implement JWT auth
       │
       ▼ (automatic)
[Orchestrator spawns PM via Task()]
       │
       ▼ (automatic)
[PM returns plan, orchestrator spawns Developer]
       │
       ▼ (automatic)
[Developer returns, orchestrator spawns QA]
       │
       ▼ (automatic)
[QA returns, orchestrator spawns Tech Lead]
       │
       ▼ (automatic)
[Tech Lead approves, PM sends BAZINGA]
```

**Copilot (Proposed):**
```
User: @bazinga-orchestrator implement JWT auth
       │
       ▼
[Orchestrator analyzes, presents handoff buttons]
       │
       ▼ (user clicks "Plan with PM")
[@project-manager creates plan]
       │
       ▼ (user clicks "Assign Developer")
[@developer implements]
       │
       ▼ (user clicks "Run QA Tests")
[@qa-expert tests]
       │
       ▼ (user clicks "Code Review")
[@tech-lead reviews]
       │
       ▼
[Complete or iterate]
```

**Trade-off:** Less automation, more user control. This may be acceptable for Copilot's user model (developers prefer control).

### 5.3 Spec-Kit Workflow Preservation

Spec-kit commands become auto-activating skills:

```
User: "I want to create a spec for user authentication"
       │
       ▼ (automatic skill activation)
[speckit-specify skill injects instructions]
       │
       ▼
[Copilot follows spec creation workflow]
       │
       ▼
[Presents handoff: "Build Technical Plan"]
       │
       ▼ (user clicks or says "yes")
[speckit-plan skill activates]
```

---

## 6. Dual-Platform Support

### 6.1 Architecture for Dual Support

To support both Claude Code and Copilot from the same codebase:

```
project/
├── .claude/
│   └── commands/
│       ├── bazinga.orchestrate.md      # Claude Code commands
│       └── speckit.*.md
│
├── .github/
│   ├── agents/
│   │   ├── bazinga-orchestrator.agent.md  # Copilot agents
│   │   └── *.agent.md
│   └── skills/
│       ├── speckit-*/SKILL.md            # Copilot skills
│       └── */SKILL.md
│
└── shared/
    ├── orchestration-logic.md            # Shared orchestration rules
    ├── agent-prompts/                    # Shared agent prompts
    │   ├── project-manager.md
    │   ├── developer.md
    │   └── *.md
    └── templates/                        # Shared templates
```

### 6.2 Shared Content Strategy

**Agent Prompts:**
- Core agent logic (PM, Developer, QA, Tech Lead) is shared
- Platform-specific wrappers handle invocation

**Claude Code Agent:**
```markdown
# Developer Agent (Claude Code)

{{include shared/agent-prompts/developer.md}}

## Claude Code Specific
- Use Task() to return to orchestrator
- Format output as CRP JSON
```

**Copilot Agent:**
```markdown
---
name: developer
model: claude-sonnet-4
tools: ["read", "edit", "execute"]
handoffs:
  - label: Ready for QA
    agent: qa-expert
---

# Developer Agent (Copilot)

{{include shared/agent-prompts/developer.md}}
```

### 6.3 Build Process

Create a build script that generates platform-specific files from shared sources:

```bash
#!/bin/bash
# scripts/build-platform-commands.sh

# Generate Claude Code commands
for agent in shared/agent-prompts/*.md; do
  name=$(basename $agent .md)
  cat templates/claude-wrapper.md shared/agent-prompts/$name.md > .claude/agents/$name.md
done

# Generate Copilot agents
for agent in shared/agent-prompts/*.md; do
  name=$(basename $agent .md)
  cat templates/copilot-agent-header.yaml shared/agent-prompts/$name.md > .github/agents/$name.agent.md
done
```

---

## 7. Implementation Plan

### Phase 1: Foundation (Week 1-2)

**Priority: Critical**

1. **Create Copilot directory structure**
   ```bash
   mkdir -p .github/agents .github/skills
   ```

2. **Migrate orchestration agents**
   - `bazinga-orchestrator.agent.md`
   - `project-manager.agent.md`
   - `developer.agent.md`
   - `qa-expert.agent.md`
   - `tech-lead.agent.md`

3. **Define handoff chain**
   - Orchestrator → PM → Developer → QA → Tech Lead → PM

4. **Test basic workflow**
   - Verify handoffs work
   - Verify agent isolation

**Effort:** 3-5 days

### Phase 2: Spec-Kit Skills (Week 3)

**Priority: High**

1. **Create spec-kit skills**
   - `speckit-specify/SKILL.md`
   - `speckit-plan/SKILL.md`
   - `speckit-tasks/SKILL.md`
   - `speckit-implement/SKILL.md`

2. **Configure auto-activation triggers**
   - Write clear descriptions
   - Test semantic matching

3. **Preserve script dependencies**
   - Ensure `.specify/scripts/` are accessible
   - Test bash script execution

**Effort:** 2-3 days

### Phase 3: Utility Skills (Week 4)

**Priority: Medium**

1. **Create remaining skills**
   - `speckit-analyze/SKILL.md`
   - `speckit-clarify/SKILL.md`
   - `speckit-checklist/SKILL.md`
   - `speckit-constitution/SKILL.md`
   - `speckit-taskstoissues/SKILL.md`
   - `bazinga-configure-skills/SKILL.md`
   - `bazinga-configure-testing/SKILL.md`

2. **Test cross-references**
   - Skills can reference agents via handoffs
   - Verify chaining works

**Effort:** 2-3 days

### Phase 4: Advanced Orchestration (Week 5)

**Priority: Medium**

1. **Create advanced orchestrator variants**
   - `bazinga-orchestrator-advanced.agent.md`
   - `bazinga-orchestrator-from-spec.agent.md`

2. **Integrate database operations**
   - Port bazinga-db skill to Copilot
   - Ensure state persistence

**Effort:** 2-3 days

### Phase 5: Dual-Platform Build (Week 6)

**Priority: Low**

1. **Create shared content structure**
   - Extract common agent prompts
   - Create templates

2. **Build automation**
   - Script to generate platform files
   - CI integration

**Effort:** 2-3 days

### Phase 6: Testing & Documentation (Week 7-8)

**Priority: High**

1. **End-to-end testing**
   - Full orchestration workflow
   - All spec-kit commands
   - Configuration commands

2. **Documentation**
   - User guide for Copilot invocation
   - Migration guide for existing users

**Effort:** 3-5 days

---

## 8. Risk Assessment

### 8.1 High Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **No programmatic sub-agent spawning** | Orchestration is semi-automated | Accept user-driven handoffs; educate users |
| **No parallel agent execution** | Sequential only on Copilot | Redesign workflow for sequential execution |
| **Skill activation conflicts** | Multiple skills may activate | Carefully tune descriptions; use disambiguation |

### 8.2 Medium Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Database access differences** | bazinga-db may not work | Port to MCP server or file-based fallback |
| **Template path differences** | File references break | Use relative paths; document conventions |
| **Handoff latency** | Slower workflow | Optimize agent prompts; reduce handoff count |

### 8.3 Low Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Different tool names** | Minor API differences | Create alias layer |
| **Model availability** | Some models may differ | Configure model selection per platform |

---

## Appendix A: Complete Mapping Table

| Claude Code Command | Copilot Implementation | Type | Invocation |
|---------------------|----------------------|------|------------|
| `/bazinga.orchestrate` | `@bazinga-orchestrator` | Agent | Explicit |
| `/bazinga.orchestrate-advanced` | `@bazinga-orchestrator-advanced` | Agent | Explicit |
| `/bazinga.orchestrate-from-spec` | `@bazinga-orchestrator-from-spec` | Agent | Explicit |
| `/bazinga.configure-skills` | `bazinga-configure-skills` | Skill | Auto |
| `/bazinga.configure-testing` | `bazinga-configure-testing` | Skill | Auto |
| `/speckit.specify` | `speckit-specify` | Skill | Auto |
| `/speckit.plan` | `speckit-plan` | Skill | Auto |
| `/speckit.tasks` | `speckit-tasks` | Skill | Auto |
| `/speckit.implement` | `speckit-implement` | Skill | Auto |
| `/speckit.analyze` | `speckit-analyze` | Skill | Auto |
| `/speckit.clarify` | `speckit-clarify` | Skill | Auto |
| `/speckit.checklist` | `speckit-checklist` | Skill | Auto |
| `/speckit.constitution` | `speckit-constitution` | Skill | Auto |
| `/speckit.taskstoissues` | `speckit-taskstoissues` | Skill | Auto |

---

## Appendix B: Copilot Agent Template

```yaml
---
name: agent-name
description: |
  Clear description of what this agent does.
  Include trigger phrases for disambiguation.
model: claude-sonnet-4
tools: ["read", "edit", "execute", "github/*"]
handoffs:
  - label: Button Label
    agent: target-agent-name
    prompt: Pre-filled prompt for handoff
    send: false  # true = auto-submit
---

# Agent Title

## Identity
You are [role] in the BAZINGA multi-agent orchestration system.

## Responsibilities
- [Responsibility 1]
- [Responsibility 2]

## Workflow
1. Step 1
2. Step 2
3. Step 3

## Output Format
[Describe expected output format]

## Handoff Conditions
- Condition for handoff 1 → use "Button Label"
- Condition for handoff 2 → use other button
```

---

## Appendix C: Copilot Skill Template

```yaml
---
name: skill-name
description: |
  Brief description of skill purpose.
  Include natural language triggers:
  - "create a spec"
  - "specify feature"
  - "write specification"
---

# Skill Title

## When to Use
- User scenario 1
- User scenario 2

## Instructions

### Step 1: [Action]
[Detailed instructions]

### Step 2: [Action]
[Detailed instructions]

## Output Format
[Expected output]

## Examples

### Example 1: [Title]
**Input:** "..."
**Output:** "..."
```

---

## Conclusion

Migrating BAZINGA's slash commands to GitHub Copilot requires accepting a fundamental trade-off: **automated orchestration becomes user-driven orchestration**. The recommended hybrid approach preserves the multi-agent workflow semantics while adapting to Copilot's interaction model.

**Key Decisions:**
1. Use Custom Agents for orchestration (handoff-based routing)
2. Use Skills for utility commands (automatic activation)
3. Accept user-driven handoffs for agent transitions
4. Build dual-platform support through shared content

**Next Steps:**
1. Review this analysis with team
2. Prototype `bazinga-orchestrator.agent.md`
3. Test handoff chain in Copilot
4. Iterate based on findings
