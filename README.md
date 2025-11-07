# BAZINGA - Claude Code Multi-Agent Dev Team

> **Repository:** https://github.com/mehdic/bazinga

A sophisticated multi-agent orchestration system for Claude Code that coordinates autonomous development teams including Project Manager, Developers, QA Expert, and Tech Lead agents working together to complete software projects.

## Overview

This system implements adaptive parallelism, intelligent workflow routing, and comprehensive role drift prevention to ensure high-quality software delivery through autonomous agent coordination.

## Features

- **Adaptive Parallelism**: PM dynamically spawns 1-4 developers based on task complexity
- **Conditional Workflow**: Intelligent routing based on whether tests exist (Dev→QA→TechLead vs Dev→TechLead)
- **Role Drift Prevention**: 6-layer defense system preventing agents from forgetting their roles
- **Explicit Routing**: Each agent tells orchestrator exactly where to route next
- **Full Autonomy**: Agents work until 100% complete without asking user questions
- **Quality Gates**: QA Expert validates tests, Tech Lead reviews code quality
- **Project Completion**: PM is the only agent that sends BAZINGA signal

## Architecture

### Workflow Modes

**Simple Mode** (Sequential):
```
PM → 1 Developer → [QA if tests] → Tech Lead → PM → Next task or BAZINGA
```

**Parallel Mode** (Concurrent):
```
PM → 2-4 Developers (parallel) → [QA if tests] → Tech Lead → PM → BAZINGA
```

### Conditional Routing

**With Tests:**
```
Developer → QA Expert → Tech Lead → PM
```

**Without Tests:**
```
Developer → Tech Lead → PM
```

### Agent Roles

| Agent | Role | Responsibilities |
|-------|------|------------------|
| **Orchestrator** | Message Router | Routes messages between agents, spawns agents |
| **Project Manager** | Coordinator | Plans, tracks progress, decides parallelism, sends BAZINGA |
| **Developer** | Implementer | Writes code, creates/fixes tests, fixes bugs |
| **QA Expert** | Testing Specialist | Runs integration/contract/E2E tests (conditional) |
| **Tech Lead** | Quality Reviewer | Reviews code quality, unblocks developers, approves work |

## Project Structure

```
claude-code-multiagent-dev-team/
├── README.md                    # This file
├── agents/                      # Agent definitions
│   ├── orchestrator.md         # Main orchestrator agent
│   ├── developer.md            # Developer implementation specialist
│   ├── qa_expert.md            # QA testing specialist
│   ├── techlead.md             # Tech lead reviewer
│   └── project_manager.md      # Project coordinator
├── commands/                    # Slash commands
│   └── orchestrate.md          # /orchestrate command version
├── scripts/                     # Utility scripts
│   ├── init-orchestration.sh  # Initialization script
│   └── README.md               # Scripts documentation
├── config/                      # Configuration files
│   ├── claude.md               # Global constraints (.claude.md)
│   └── coordination.gitignore  # Gitignore for coordination folder
├── docs/                        # Documentation
│   ├── DOCS_INDEX.md           # Documentation navigation guide
│   ├── ARCHITECTURE.md         # Detailed architecture (NEW)
│   ├── ROLE_DRIFT_PREVENTION.md # 6-layer defense system
│   ├── SCOPE_REDUCTION_INCIDENT.md # Case study
│   └── original-v4/            # Original the development docs
│       ├── V4_ARCHITECTURE.md
│       ├── V4_IMPLEMENTATION_SUMMARY.md
│       ├── V4_STATE_SCHEMAS.md
│       └── V4_WORKFLOW_DIAGRAMS.md
└── examples/                    # Example usage
    └── EXAMPLES.md             # Practical usage examples
```

## Installation

### Complete File Mapping

Here's where each file from this package should go in your target project:

| Source File | Destination in Your Project | Required? | Purpose |
|-------------|----------------------------|-----------|---------|
| `agents/*.md` | `.claude/agents/*.md` | ✅ Yes | Agent definitions (orchestrator, PM, developer, QA, tech lead) |
| `commands/orchestrate.md` | `.claude/commands/orchestrate.md` | ⚠️ Optional | Slash command version (use if you prefer `/orchestrate`) |
| `config/claude.md` | `.claude.md` | ✅ Yes | Global orchestrator role enforcement |
| `scripts/init-orchestration.sh` | `.claude/scripts/init-orchestration.sh` | ✅ Yes | Creates coordination/ folder and state files |
| `scripts/README.md` | `.claude/scripts/README.md` | 📖 Docs | Script documentation |
| `config/coordination.gitignore` | `coordination/.gitignore` | ⚠️ Optional | Excludes state files from git (created by init script) |
| `docs/` | `docs/bazinga/` or keep local | 📖 Docs | Architecture, guides, historical docs |
| `examples/` | `docs/bazinga/examples/` or keep local | 📖 Docs | Usage examples |
| `README.md` | Keep as reference | 📖 Docs | This file |

### Option 1: Quick Install (Essentials Only)

Install just the files needed to run BAZINGA:

```bash
# From the bazinga directory, run in your target project:
cd /path/to/your/project

# 1. Copy agents (required)
mkdir -p .claude/agents
cp /path/to/bazinga/agents/*.md .claude/agents/

# 2. Copy initialization script (required)
mkdir -p .claude/scripts
cp /path/to/bazinga/scripts/init-orchestration.sh .claude/scripts/
chmod +x .claude/scripts/init-orchestration.sh

# 3. Copy global config (required)
cp /path/to/bazinga/config/claude.md .claude.md

# 4. Optional: Add slash command
cp /path/to/bazinga/commands/orchestrate.md .claude/commands/

# 5. Run initialization
bash .claude/scripts/init-orchestration.sh
```

### Option 2: Full Install (Including Documentation)

Install everything including documentation:

```bash
cd /path/to/your/project

# Copy essentials (same as Option 1)
mkdir -p .claude/agents .claude/scripts .claude/commands
cp /path/to/bazinga/agents/*.md .claude/agents/
cp /path/to/bazinga/scripts/* .claude/scripts/
cp /path/to/bazinga/commands/orchestrate.md .claude/commands/
cp /path/to/bazinga/config/claude.md .claude.md
chmod +x .claude/scripts/init-orchestration.sh

# Copy documentation (optional but recommended)
mkdir -p docs/bazinga
cp -r /path/to/bazinga/docs/* docs/bazinga/
cp -r /path/to/bazinga/examples docs/bazinga/
cp /path/to/bazinga/README.md docs/bazinga/

# Run initialization
bash .claude/scripts/init-orchestration.sh
```

### Option 3: New Standalone Project

Start a fresh project with BAZINGA:

```bash
# Clone or copy the entire bazinga directory
cp -r /path/to/bazinga /path/to/new-project
cd /path/to/new-project

# Restructure to standard layout
mkdir -p .claude/agents .claude/commands .claude/scripts
mv agents/* .claude/agents/
mv commands/* .claude/commands/
mv scripts/* .claude/scripts/
mv config/claude.md .claude.md
rm -rf agents commands config

# Initialize
bash .claude/scripts/init-orchestration.sh

# Initialize git
git init
```

## Usage

### Using the Orchestrator Agent

```
@orchestrator implement user authentication with JWT
```

The orchestrator will:
1. Spawn PM to analyze and plan
2. PM spawns developer(s) based on complexity
3. Developers implement and route appropriately
4. QA tests (if tests exist)
5. Tech Lead reviews quality
6. PM tracks completion and sends BAZINGA

### Using the Slash Command

```
/orchestrate implement user authentication with JWT
```

Same workflow as agent but invoked as command.

### Understanding Routing

Developers explicitly tell orchestrator where to route:

**With Tests:**
```
**Tests Created/Fixed:** YES
**Status:** READY_FOR_QA
**Next Step:** Orchestrator, please forward to QA Expert for testing
```

**Without Tests:**
```
**Tests Created/Fixed:** NO
**Status:** READY_FOR_REVIEW
**Next Step:** Orchestrator, please forward to Tech Lead for code review
```

## Key Principles

### 1. Orchestrator Never Implements
Orchestrator only routes messages and spawns agents. It never writes code, runs tests, or does implementation work.

### 2. PM Never Implements
PM only coordinates, plans, and tracks. PM spawns developers through orchestrator but never uses Edit/Write tools.

### 3. Only PM Sends BAZINGA
Tech Lead approves individual task groups. Only PM decides when entire project is complete.

### 4. Explicit Routing Prevents Drift
Every agent response includes "Next Step: Orchestrator, please forward to..." to prevent workflow memory drift.

### 5. Conditional QA Involvement
QA Expert is only spawned when Developer has created/fixed integration/contract/E2E tests.

### 6. Full Autonomy
Agents never ask user questions. They work autonomously until 100% complete or BAZINGA.

## Role Drift Prevention

### 6-Layer Defense System

1. **Pre-Response Role Check**: Agent reminds itself of role before every response
2. **Explicit Routing Decision Table**: Mandatory lookup table for orchestrator
3. **Anti-Pattern Detection**: WRONG vs CORRECT examples
4. **Strategic Reinforcement Checkpoints**: Role checks at critical routing points
5. **Global Constitutional Constraints**: .claude.md enforces roles permanently
6. **Mandatory Workflow Chain**: Never skip steps in workflow

## State Management

The system uses JSON state files for coordination:

- `coordination/pm_state.json` - PM planning and progress tracking
- `coordination/group_status.json` - Individual task group statuses
- `coordination/orchestrator_state.json` - Orchestrator routing state
- `coordination/messages/*.json` - Inter-agent message exchange

Run the initialization script to set up state files:

```bash
./.claude/scripts/init-orchestration.sh
```

## Configuration

### Global Constraints (.claude.md)

The `config/claude.md` file should be copied to your project root as `.claude.md`. It enforces:
- Orchestrator role enforcement
- Role drift prevention
- Mandatory workflow adherence

### Tool Restrictions

Each agent has specific tool permissions:
- **PM**: Read state files only, never Edit
- **Developer**: Full implementation tools
- **QA Expert**: Bash for tests, Read for code
- **Tech Lead**: Read for review, no Write/Edit
- **Orchestrator**: No implementation tools

## Comparison with Other Frameworks

| Feature | Claude Code Multi-Agent Dev Team | ChatDev | MetaGPT | AutoGen | CrewAI |
|---------|-----------|---------|---------|---------|--------|
| Adaptive Parallelism | ✅ (1-4) | ❌ | ❌ | ❌ | ❌ |
| Conditional Routing | ✅ | ❌ | ❌ | ❌ | ❌ |
| Role Drift Prevention | ✅ (6-layer) | ⚠️ Basic | ⚠️ Basic | ⚠️ Basic | ⚠️ Basic |
| Claude Code Native | ✅ | ❌ | ❌ | ❌ | ❌ |
| Explicit Routing | ✅ | ❌ | ❌ | ❌ | ❌ |
| Tool Restrictions | ✅ | ❌ | ❌ | ⚠️ Partial | ⚠️ Partial |

## Examples

### Example 1: Feature with Tests
```
User: Implement JWT authentication

PM: Creates 1 task group (simple mode)
Developer: Implements auth + tests → READY_FOR_QA → Routes to QA
QA: Runs tests → PASS → Routes to Tech Lead
Tech Lead: Reviews code → APPROVED → Routes to PM
PM: All complete → BAZINGA
```

### Example 2: Refactoring without Tests
```
User: Refactor error handling in middleware

PM: Creates 1 task group (simple mode)
Developer: Refactors code → READY_FOR_REVIEW → Routes to Tech Lead (skips QA)
Tech Lead: Reviews code → APPROVED → Routes to PM
PM: All complete → BAZINGA
```

### Example 3: Parallel Development
```
User: Implement JWT auth, user registration, and password reset

PM: Creates 3 task groups, spawns 2 developers (parallel mode)
Developer 1: JWT auth with tests → QA → Tech Lead → PM
Developer 2: User registration with tests → QA → Tech Lead → PM
PM: 2 complete, spawns Developer 3
Developer 3: Password reset with tests → QA → Tech Lead → PM
PM: All complete → BAZINGA
```

## Troubleshooting

### Orchestrator Skipping Workflow Steps
- Check: Is pre-response role check present?
- Solution: Orchestrator should output `🔄 **ORCHESTRATOR ROLE CHECK**: I am a coordinator`

### PM Asking User Questions
- Check: Is PM using forbidden "Do you want to continue?" language?
- Solution: PM should autonomously assign work without asking

### QA Spawned When No Tests
- Check: Did Developer set `Tests Created/Fixed: NO`?
- Solution: Developer should explicitly state test status

### Tech Lead Sending BAZINGA
- Check: Only PM can send BAZINGA
- Solution: Tech Lead sends APPROVED, PM sends BAZINGA

## Contributing

This system was developed iteratively with focus on:
- Preventing role drift during long conversations
- Explicit routing to prevent workflow confusion
- Adaptive parallelism for efficiency
- Conditional workflows for flexibility

## License

MIT License - Feel free to use and adapt for your projects.

## Version History

- **Version 1.0**: Current version with conditional routing and 6-layer role drift prevention
- **Version 0.3**: Previous version (not included)
- **Version 0.2**: Initial multi-agent system (not included)
- **Version 0.1**: Single agent baseline (not included)

## Documentation

Comprehensive documentation is available in the `docs/` directory:

### Main Documentation
- **[DOCS_INDEX.md](docs/DOCS_INDEX.md)** - Navigation guide to all documentation
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Technical deep-dive (1,100 lines)
- **[ROLE_DRIFT_PREVENTION.md](docs/ROLE_DRIFT_PREVENTION.md)** - 6-layer defense system explained
- **[SCOPE_REDUCTION_INCIDENT.md](docs/SCOPE_REDUCTION_INCIDENT.md)** - Case study of orchestrator role drift
- **[EXAMPLES.md](examples/EXAMPLES.md)** - Practical usage examples

### Original Development Documentation (Historical)
Located in `docs/original-v4/` - Historical documentation from the development:
- **V4_ARCHITECTURE.md** - Original architecture specification (580 lines)
- **V4_IMPLEMENTATION_SUMMARY.md** - Development history and decisions (350 lines)
- **V4_STATE_SCHEMAS.md** - Complete JSON schema definitions (710 lines)
- **V4_WORKFLOW_DIAGRAMS.md** - Visual workflow representations (2,100 lines)

**Total**: Over 10,500 lines of comprehensive documentation

### Quick Links
- New users → Start with README.md (this file) and EXAMPLES.md
- Technical details → ARCHITECTURE.md
- Understanding design → original-v4/V4_IMPLEMENTATION_SUMMARY.md
- State files → original-v4/V4_STATE_SCHEMAS.md
- Troubleshooting → SCOPE_REDUCTION_INCIDENT.md

## Support

For issues or questions:
- Review **[docs/DOCS_INDEX.md](docs/DOCS_INDEX.md)** for navigation
- Check **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** for technical details
- Review **[examples/EXAMPLES.md](examples/EXAMPLES.md)** for usage patterns
- Examine agent definitions in `agents/` for specific behaviors
- See **[docs/SCOPE_REDUCTION_INCIDENT.md](docs/SCOPE_REDUCTION_INCIDENT.md)** for common issues

## Acknowledgments

Built for Claude Code using the Claude Agent SDK. Inspired by ChatDev, MetaGPT, and other multi-agent frameworks but optimized specifically for Claude Code's capabilities and constraints.

---

**Created**: 2025-01-07
**Last Updated**: 2025-01-07
**Version**: 1.0 (Conditional Workflow + 6-Layer Role Drift Prevention)
