# BAZINGA - Multi-Agent Development Team for Claude Code

> **Repository:** https://github.com/mehdic/bazinga

BAZINGA is a multi-agent orchestration system for Claude Code that automates software development using a team of AI agents: Project Manager, Developers, QA Expert, and Tech Lead.

## What Development Problems Does It Solve?

We built BAZINGA to address real pain points we experienced in software development:

- **Manual code reviews take hours** - Tech Lead agent automates quality reviews, finding issues before human review
- **Tests written inconsistently** - QA Expert ensures testing standards are followed across all work
- **Security vulnerabilities discovered late** - Automated security scanning catches issues during development, not in production
- **No idea if estimates are accurate** - PM tracks velocity and learns from history to improve future estimates
- **Developers repeat same mistakes** - Skills analyze code patterns and provide feedback based on project conventions
- **Context switching kills productivity** - Adaptive parallelism lets 1-4 developers work simultaneously on independent tasks

## Quick Install

```bash
# One-time use (no installation)
uvx --from git+https://github.com/mehdic/bazinga.git bazinga init my-project

# Or install as a tool
uv tool install bazinga-cli --from git+https://github.com/mehdic/bazinga.git
bazinga init my-project

# Or use pip
pip install git+https://github.com/mehdic/bazinga.git
bazinga init my-project
```

---

## The Problem

### Before BAZINGA

**Using Claude Code normally (even with manual multi-agent coordination):**

- **Single agent**: One agent plans, codes, tests, and reviews all in one go
- **Manual multi-agent**: You manually coordinate agents yourself, remembering each step
- **No framework**: No structured workflow following software development best practices
- **Manual quality checks**: You remember to run security scans, linting, coverage... or you don't
- **No automation**: Each quality check requires explicit manual invocation
- **Sequential work**: Can't parallelize independent tasks across multiple agents automatically
- **No learning**: No velocity tracking or historical data to improve estimates

**What this looks like:**

```
You: "Implement JWT authentication with user management"

Claude Code (single agent):
  - Plans the work
  - Writes all the code
  - Creates some tests (maybe)
  - Reviews its own code (limited self-critique)
  - No security scan unless you explicitly ask
  - No coverage analysis unless you explicitly ask
  - Pushes to completion

Result: Fast, but quality varies. No specialization, no quality gates.

--- OR ---

Claude Code (manual multi-agent - you coordinate):
  You: "@pm-agent plan this work"
  You: "now @dev-agent implement the auth module"
  You: "did I run security scan? let me check... @security run scan"
  You: "now @qa-agent test this"
  You: "wait, did the dev finish? let me check state files..."
  You: "@tech-lead-agent review the code"

Result: Better quality, but YOU manage the workflow. Easy to skip steps.
```

**Problems:**
- No separation of concerns (single agent reviews own code)
- No structured framework (manual multi-agent is ad-hoc)
- No mandatory quality gates (easy to forget steps)
- Can't parallelize automatically (you decide and coordinate manually)
- No metrics or learning over time
- No automated Skills workflow

### After BAZINGA

**Using BAZINGA: A complete framework following software development best practices:**

- **Structured workflow**: Follows industry-standard SDLC (plan → develop → test → review → deploy)
- **Automated orchestration**: Framework manages agent coordination, you don't
- **Autonomous execution**: Long task lists run for hours without interruption, maintaining best practices throughout
- **Specialized roles**: PM plans, Developers code, QA tests, Tech Lead reviews
- **Mandatory quality gates**: Security scans, test coverage, linting run automatically at each step
- **Skills automation**: 11 Skills automate code analysis, security scanning, pattern detection
- **Parallel execution**: Framework automatically spawns 1-4 developers based on task complexity
- **Automatic escalation**: Tech Lead escalates to Opus after 3 failed revisions (no manual intervention)
- **Velocity tracking**: PM learns from history and improves estimates over time
- **Separation of concerns**: Authors don't review their own code (enforced by framework)

**What this looks like:**

```
You: "Implement JWT authentication with user management"
     (single command - framework handles the rest)

BAZINGA Framework executes structured workflow:

PM Agent:
  ✓ Analyzes requirements
  ✓ Breaks into 2 independent task groups
  ✓ Decides to spawn 2 developers in parallel (automatic)
  ✓ Tracks velocity using velocity-tracker Skill

Developer-1: Auth module          Developer-2: User management
  ✓ lint-check Skill (automatic)    ✓ lint-check Skill (automatic)
  ✓ Writes code + tests              ✓ Writes code + tests
  ↓                                   ↓
QA Expert: Validates tests        QA Expert: Validates tests
  ✓ Runs integration tests          ✓ Runs integration tests
  ↓                                   ↓
Tech Lead: Reviews code (both modules)
  ✓ security-scan Skill (automatic - checks for vulnerabilities)
  ✓ test-coverage Skill (automatic - validates coverage)
  ✓ Architectural review
  ↓
PM: Confirms completion
  ✓ All quality gates passed
  ✓ No blocking tech debt
  ✓ BAZINGA! ✓

Result: High quality + parallelism + automated checks. You wrote one command.
```

**Benefits:**
- **Framework enforces best practices**: Can't skip steps (plan → dev → test → review)
- **Automated quality checks**: 11 Skills run at appropriate stages (not optional)
- **Intelligent parallelism**: Framework decides 1-4 developers based on complexity
- **Complete automation**: You manage the "what", framework manages the "how"
- **Historical learning**: Metrics improve estimates over time
- **Repeatable process**: Same workflow every time, zero manual coordination

---

## How It Works

### Simple Explanation

BAZINGA gives you a team of specialized AI agents:

- **Project Manager (PM)** - Breaks down work, tracks progress, decides parallelism, gates deployment
- **Developers (1-4)** - Write code, create tests, fix bugs based on feedback
- **QA Expert** - Runs integration/contract/E2E tests, reports results
- **Tech Lead** - Reviews code quality, security, architecture
- **Orchestrator** - Routes messages between agents, spawns team members

### Visual Workflow

```
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│  PM plans work                                                 │
│       ↓                                                        │
│  Developers code (1-4 in parallel)                             │
│       ↓                                                        │
│  QA tests (if integration/contract/E2E tests exist)            │
│       ↓                                                        │
│  Tech Lead reviews (auto-escalates to Opus after 3 revisions)  │
│       ↓                                                        │
│  PM confirms completion                                        │
│       ↓                                                        │
│  BAZINGA! ✓                                                    │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

**Example execution:**
```
User: Implement JWT authentication

PM: Creates task groups, decides parallelism
     └─> Spawns 1 developer (simple task)

Developer: Implements auth + tests
           └─> Routes to QA (tests exist)

QA Expert: Runs tests → PASS
           └─> Routes to Tech Lead

Tech Lead: Reviews code → APPROVED (or requests changes)
           └─> Routes to PM

PM: All tasks complete → BAZINGA
```

### Agent Roles

| Agent | Responsibilities | Tools | Decision Power |
|-------|-----------------|-------|----------------|
| **Orchestrator** | Routes messages, spawns agents | None (routing only) | Agent selection |
| **PM** | Plans work, tracks progress, gates deployment | Read state files | Parallelism (1-4 devs), BAZINGA signal |
| **Developer** | Writes code, creates tests, fixes bugs | Full implementation tools | Routing (QA or Tech Lead) |
| **QA Expert** | Runs integration/contract/E2E tests | Bash, Read | Test validation (PASS/FAIL) |
| **Tech Lead** | Reviews quality, security, architecture | Read, Skills | Approval (APPROVED/CHANGES_REQUESTED) |

### Two Modes of Operation

**Simple Mode (Sequential):**
```
PM → 1 Developer → QA → Tech Lead → PM
```
Used for: Single features, bug fixes, small refactorings

**Parallel Mode (Concurrent):**
```
PM → 2-4 Developers (parallel) → QA → Tech Lead → PM
```
Used for: Multiple features, large projects, independent task groups

PM decides mode based on:
- Task complexity (story points)
- Task independence (can they run in parallel?)
- Dependencies (what blocks what?)

### Conditional Routing

**If Developer creates/fixes tests:**
```
Developer → QA Expert → Tech Lead → PM
```

**If Developer doesn't touch tests:**
```
Developer → Tech Lead → PM
```

This prevents wasting time spawning QA when there's nothing to test.

---

## Key Features

### 1. Configurable Skills System

**What it is:**
BAZINGA includes 11 automated analysis tools (Skills) that provide security scanning, test coverage, linting, and more. You control which ones run.

**Why it matters:**
- **Fast iteration**: Default skills run in 1-2 minutes total
- **Deep analysis**: Advanced skills run in 3-5 minutes for critical work
- **No magic keywords**: Just enable/disable what you need

**Quick example:**
```bash
/configure-skills
> 2 3 9    # Enable skills #2, #3, #9
> advanced # Enable all advanced skills
> fast     # Only fast skills (<20s)
```

**Default Skills (always on):**
- lint-check (5-10s) - Code quality and style
- security-scan (5-60s) - Vulnerability detection
- test-coverage (5-20s) - Coverage analysis
- velocity-tracker (3-5s) - PM metrics

**Advanced Skills (configurable):**
- codebase-analysis - Pattern extraction
- test-pattern-analysis - Test strategy learning
- api-contract-validation - Breaking change detection
- db-migration-check - Migration safety
- quality-dashboard - Unified health metrics
- pattern-miner - Historical pattern analysis

**Learn more:** [docs/SKILLS.md](docs/SKILLS.md)

### 2. Adaptive Parallelism

**What it is:**
PM dynamically spawns 1-4 developers based on task complexity and independence.

**Why it matters:**
- **Faster completion**: Independent tasks run simultaneously
- **Intelligent scheduling**: PM analyzes dependencies and assigns work accordingly
- **No manual coordination**: PM handles all task routing

**Example:**
```
Task: Implement JWT auth, user registration, password reset

PM analysis:
- 3 independent features (can parallelize)
- Each ~5 story points (medium complexity)
- No dependencies

Decision: Spawn 3 developers in parallel

Result: Complete in 45 minutes instead of 2+ hours
```

**Learn more:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#adaptive-parallelism)

### 3. Intelligent Model Escalation

**What it is:**
After 3 failed code revisions, Tech Lead automatically escalates to Opus for deeper analysis.

**Why it matters:**
- **Cost-effective**: Use fast Sonnet for 90% of reviews
- **Deep analysis when needed**: Opus catches subtle bugs after multiple revisions
- **Automatic escalation**: No manual model switching

**How it works:**
| Revision Count | Model | Strategy |
|---------------|-------|----------|
| 1-2 revisions | Sonnet 4.5 | Fast, typical issues |
| 3+ revisions | Opus | Deep analysis, architectural issues |

**Example:**
```
Review 1 (Sonnet): "Add error handling" → Dev fixes
Review 2 (Sonnet): "Fix edge case" → Dev fixes
Review 3 (Opus): "Authentication flow needs redesign - token refresh logic is flawed"
```

**Learn more:** [docs/MODEL_ESCALATION.md](docs/MODEL_ESCALATION.md)

### 4. Data-Driven PM with Velocity Tracking

**What it is:**
PM tracks development velocity, cycle time, and quality metrics to improve estimates and detect bottlenecks.

**Why it matters:**
- **Accurate estimates**: Learns from history ("DB tasks take 2.5x initial estimate")
- **Early bottleneck detection**: Catches stuck tasks (99% rule violations)
- **Progress visibility**: User gets realistic ETAs
- **Continuous improvement**: Each run improves the baseline

**Metrics tracked:**
- **Velocity**: Story points per run
- **Cycle time**: Minutes per task group
- **Revision rate**: Iterations per task (quality indicator)
- **Completion %**: Real-time progress

**Example PM decision:**
```
Checking metrics... [invokes /velocity-tracker]

Current velocity: 12 (above avg 10.5) ✓
Trend: improving
⚠️ Group G002 taking 3x longer than expected

Action: Pace is good. Escalating G002 to Tech Lead for review.
```

**Learn more:** [docs/PM_METRICS.md](docs/PM_METRICS.md)

### 5. Spec-Kit Integration (Planning + Execution)

**What it is:**
Seamless integration with GitHub's [spec-kit](https://github.com/github/spec-kit) for spec-driven development.

**Why it matters:**
- **Rigorous planning**: Use spec-kit's specification workflow
- **Powerful execution**: Use BAZINGA's multi-agent team
- **Full traceability**: Track from spec to code with task IDs
- **Progress tracking**: Real-time checkmarks in tasks.md

**Complete workflow:**
```bash
# Phase 1: Planning with Spec-Kit
/speckit.specify Add JWT authentication  # Create spec.md
/speckit.plan                            # Create plan.md
/speckit.tasks                           # Create tasks.md

# Phase 2: Execution with BAZINGA
/orchestrate-from-spec                   # Full multi-agent execution

# Phase 3: Validation
/speckit.analyze                         # Verify consistency
```

**BAZINGA reads spec-kit artifacts:**
- spec.md - Feature requirements
- tasks.md - Task breakdown with IDs (T001, T002...)
- plan.md - Technical approach
- research.md - Research findings

**PM creates groups from tasks.md:**
```
- [ ] [T001] [P] Setup auth module
- [ ] [T002] [P] [US1] JWT generation
- [ ] [T003] [P] [US1] Token validation
- [ ] [T004] [US2] Login endpoint

PM analysis:
- Tasks T001-T003 can run in parallel ([P] markers)
- User stories US1, US2 identified
- US2 depends on US1
```

**Learn more:** [.claude/commands/configure-skills.md](.claude/commands/configure-skills.md)

### 6. Role Drift Prevention (6-Layer Defense)

**What it is:**
Multi-layered system preventing agents from forgetting their roles during long conversations.

**Why it matters:**
- **Prevents scope creep**: Orchestrator won't suddenly start implementing
- **Maintains quality**: PM can't skip QA/Tech Lead reviews
- **Reliable workflows**: Each agent stays in their lane

**6 Layers:**
1. **Pre-response role check** - Agent reminds itself before every response
2. **Explicit routing table** - Mandatory lookup for orchestrator
3. **Anti-pattern detection** - WRONG vs CORRECT examples
4. **Strategic checkpoints** - Role checks at critical routing points
5. **Global constraints** - .claude.md enforces roles permanently
6. **Mandatory workflow chain** - Never skip steps

**Example prevention:**
```
❌ WRONG: Orchestrator implements feature itself
✓ CORRECT: Orchestrator spawns Developer

❌ WRONG: PM sends BAZINGA without Tech Lead approval
✓ CORRECT: PM waits for Tech Lead → APPROVED before BAZINGA
```

**Learn more:** [docs/ROLE_DRIFT_PREVENTION.md](docs/ROLE_DRIFT_PREVENTION.md)

### 7. Tech Debt Tracking

**What it is:**
Explicit logging of engineering tradeoffs with PM quality gate before deployment.

**Why it matters:**
- **Transparency**: All shortcuts documented
- **Quality gate**: PM blocks BAZINGA if critical debt exists
- **Future planning**: Logged debt guides next iterations
- **No lazy shortcuts**: Must attempt to fix before logging (30+ min)

**PM Tech Debt Gate:**
| Condition | PM Action | Result |
|-----------|-----------|--------|
| Blocking items exist | ❌ Report to user | NO BAZINGA |
| HIGH severity > 2 | ⚠️ Ask user approval | WAIT |
| Only MEDIUM/LOW | ✅ Include summary | BAZINGA with note |

**Learn more:** [docs/TECH_DEBT_GUIDE.md](docs/TECH_DEBT_GUIDE.md)

### 8. Multi-Language Support

**What it is:**
Full support for Python, JavaScript, Go, Java, and Ruby projects with language-specific tooling.

**Language coverage:**
| Language | Security | Coverage | Linting |
|----------|----------|----------|---------|
| Python | bandit + semgrep | pytest-cov | ruff/pylint |
| JavaScript | npm audit + eslint | jest | eslint |
| Go | gosec | go test -cover | golangci-lint |
| Java | SpotBugs + OWASP | JaCoCo | Checkstyle + PMD |
| Ruby | brakeman | simplecov | rubocop |

**Automated tool installation:**
CLI detects project language and offers to install missing tools during setup.

---

## Quick Start

### Three Steps to Start

**1. Install BAZINGA**
```bash
# One-time use
uvx --from git+https://github.com/mehdic/bazinga.git bazinga init my-project

# Or install as tool
uv tool install bazinga-cli --from git+https://github.com/mehdic/bazinga.git
bazinga init my-project
```

**2. Configure Skills (optional)**

Choose which analysis tools run:
```bash
/configure-skills
```

Default configuration is already optimized for most workflows (fast + essential).

**3. Run your first orchestration**

```bash
# Standard orchestration
@orchestrator implement JWT authentication

# Or with spec-kit
/speckit.specify Add JWT authentication
/speckit.plan
/speckit.tasks
/orchestrate-from-spec
```

### Simple Examples

**Example 1: Add a feature**
```bash
@orchestrator implement user registration with email verification

# BAZINGA will:
# - PM creates task breakdown
# - Developer implements feature + tests
# - QA validates tests
# - Tech Lead reviews code
# - PM sends BAZINGA when complete
```

**Example 2: Fix a bug**
```bash
@orchestrator fix bug where users can't reset password

# BAZINGA will:
# - PM creates single task
# - Developer fixes bug
# - Tech Lead reviews (no QA - no new tests)
# - PM sends BAZINGA
```

**Example 3: Large project with parallelism**
```bash
@orchestrator implement REST API with authentication, user management, and admin dashboard

# BAZINGA will:
# - PM creates 3 task groups
# - Spawns 3 developers in parallel
# - Each dev → QA → Tech Lead
# - PM coordinates and sends BAZINGA
```

### What Happens During Orchestration

**You'll see:**

1. **PM Planning** (30 seconds)
   ```
   Analyzing request...
   Created 2 task groups (8 story points total)
   Decision: Parallel mode (2 developers)
   ```

2. **Developer Work** (5-30 minutes per task)
   ```
   Developer-1: Implementing authentication... [running skills]
   Developer-2: Implementing user management... [running skills]
   ```

3. **Quality Gates** (1-5 minutes per task)
   ```
   QA Expert: Running tests... PASS
   Tech Lead: Reviewing code... [security scan, lint check] APPROVED
   ```

4. **PM Completion** (10 seconds)
   ```
   All task groups complete
   No blocking tech debt
   BAZINGA! ✓
   ```

### Understanding Output Files

After orchestration, you'll see these files:

```
coordination/
├── pm_state.json              # PM planning and progress
├── group_status.json          # Individual task status
├── orchestrator_state.json    # Routing state
├── security_scan.json         # Security findings
├── coverage_report.json       # Test coverage
├── lint_results.json          # Code quality issues
├── project_metrics.json       # Velocity and trends
└── tech_debt.json             # Engineering tradeoffs
```

These files help you understand what happened and track quality metrics over time.

---

## Project Structure

When you run `bazinga init`, this structure is created:

```
your-project/
├── .claude/
│   ├── agents/                # Agent definitions (5 agents)
│   ├── commands/              # Slash commands (/orchestrate, /configure-skills)
│   ├── scripts/               # Utility scripts (init, parsing)
│   └── skills/                # Analysis tools (11 Skills)
├── coordination/              # State files (auto-generated, gitignored)
├── .claude.md                 # Global constraints
└── .git/                      # Git repository
```

**Key directories:**

- **agents/** - PM, Developer, QA, Tech Lead, Orchestrator definitions
- **.claude/skills/** - Security, coverage, linting, metrics tools
- **coordination/** - JSON state files for tracking progress
- **docs/** - Comprehensive documentation (see below)

---

## Documentation

### Getting Started
- **README.md** (this file) - Overview and quick start
- **[examples/EXAMPLES.md](examples/EXAMPLES.md)** - Practical usage examples
- **[docs/DOCS_INDEX.md](docs/DOCS_INDEX.md)** - Navigation guide

### Configuration & Features
- **[docs/SKILLS.md](docs/SKILLS.md)** - Complete Skills reference (11 tools, configuration, language support)
- **[docs/MODEL_ESCALATION.md](docs/MODEL_ESCALATION.md)** - How and why Tech Lead escalates to Opus
- **[docs/PM_METRICS.md](docs/PM_METRICS.md)** - Velocity tracking, 99% rule detection, historical learning
- **[docs/TECH_DEBT_GUIDE.md](docs/TECH_DEBT_GUIDE.md)** - Tech debt workflow, gates, examples

### Architecture & Design
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Technical deep-dive (workflow, state management, decisions)
- **[docs/ROLE_DRIFT_PREVENTION.md](docs/ROLE_DRIFT_PREVENTION.md)** - 6-layer defense system explained
- **[docs/SCOPE_REDUCTION_INCIDENT.md](docs/SCOPE_REDUCTION_INCIDENT.md)** - Case study of role drift prevention

### Troubleshooting

**Common Issues:**

1. **Orchestrator skipping workflow steps**
   - Solution: Check pre-response role check output
   - See: [docs/ROLE_DRIFT_PREVENTION.md](docs/ROLE_DRIFT_PREVENTION.md)

2. **PM asking user questions**
   - Solution: PM should work autonomously without asking
   - See: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#pm-autonomy)

3. **QA spawned when no tests exist**
   - Solution: Developer should set "Tests Created/Fixed: NO"
   - See: [examples/EXAMPLES.md](examples/EXAMPLES.md)

4. **Skills not running**
   - Solution: Check `coordination/skills_config.json` or run `/configure-skills`
   - See: [docs/SKILLS.md](docs/SKILLS.md#configuration)

---

## Configuration & CLI

### CLI Commands

**Initialize new project:**
```bash
bazinga init my-project          # Create new directory
bazinga init --here              # Initialize in current directory
bazinga init my-project --no-git # Skip git initialization
```

**Update existing project:**
```bash
bazinga update                   # Update agents, scripts, commands
bazinga update --force           # Skip confirmation
```

Preserves:
- Coordination state files
- Ongoing orchestration sessions
- Custom project configuration

**Check system:**
```bash
bazinga check                    # Verify installation
bazinga --version                # Show version
```

### Configuration Files

**Skills configuration:**
```bash
/configure-skills                # Interactive menu
```

Saved to: `coordination/skills_config.json`

**Global constraints:**
- `.claude.md` - Role enforcement, workflow rules
- Auto-generated during `bazinga init`

**State files (auto-generated):**
- `coordination/pm_state.json` - PM planning
- `coordination/group_status.json` - Task status
- `coordination/orchestrator_state.json` - Routing
- `coordination/messages/` - Inter-agent messages

**Learn more:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#state-management)

---

## Comparison with Other Frameworks

| Feature | BAZINGA | ChatDev | MetaGPT | AutoGen | CrewAI |
|---------|---------|---------|---------|---------|--------|
| **Adaptive Parallelism** | ✅ 1-4 devs | ❌ | ❌ | ❌ | ❌ |
| **Conditional Routing** | ✅ QA optional | ❌ | ❌ | ❌ | ❌ |
| **Role Drift Prevention** | ✅ 6-layer | ⚠️ Basic | ⚠️ Basic | ⚠️ Basic | ⚠️ Basic |
| **Claude Code Native** | ✅ Skills | ❌ | ❌ | ❌ | ❌ |
| **Intelligent Escalation** | ✅ Auto Opus | ❌ | ❌ | ❌ | ❌ |
| **Velocity Tracking** | ✅ Built-in | ❌ | ❌ | ❌ | ❌ |
| **Configurable Depth** | ✅ Fast/Advanced | ❌ | ❌ | ❌ | ❌ |

**Why we built BAZINGA:**

We tried existing frameworks but found they:
- Didn't leverage Claude Code's unique capabilities (Skills, native agent system)
- Couldn't parallelize work intelligently
- Had role drift issues in long conversations
- Lacked quality gates (security, coverage, linting)
- Didn't learn from history to improve estimates

BAZINGA is purpose-built for Claude Code and focuses on **reliable, high-quality software delivery** through multi-agent coordination.

---

## Support & Contributing

### Getting Help

1. **Check documentation:** [docs/DOCS_INDEX.md](docs/DOCS_INDEX.md)
2. **Review examples:** [examples/EXAMPLES.md](examples/EXAMPLES.md)
3. **Search issues:** https://github.com/mehdic/bazinga/issues
4. **Open new issue:** Describe your use case and include relevant logs

### Reporting Issues

Include:
- BAZINGA version (`bazinga --version`)
- Project language (Python, JavaScript, etc.)
- Coordination files (`coordination/*.json`)
- Steps to reproduce

### Contributing

We welcome contributions! This system was developed iteratively with focus on:
- Preventing role drift during long conversations
- Explicit routing to prevent workflow confusion
- Adaptive parallelism for efficiency
- Data-driven decision making

**Areas for contribution:**
- Additional language support
- New Skills for analysis
- Performance optimizations
- Documentation improvements
- Bug fixes

### Development Status

**Stable:**
- Core orchestration workflow
- Adaptive parallelism (1-4 developers)
- Role drift prevention (6-layer system)
- Skills system (11 tools)
- Model escalation
- PM velocity tracking

**In Development:**
- Additional language support beyond Python/JS/Go/Java/Ruby
- Advanced pattern-miner capabilities (Tier 3)
- Quality dashboard aggregation improvements
- Integration with more CI/CD systems

### Acknowledgments

Built for Claude Code using the Claude Agent SDK. Inspired by ChatDev, MetaGPT, and other multi-agent frameworks but optimized specifically for Claude Code's capabilities.

Special thanks to:
- GitHub's spec-kit team for the planning framework integration
- Claude Code team for the Skills system
- Early adopters who provided feedback and bug reports

---

## License

MIT License - Feel free to use and adapt for your projects.

See [LICENSE](LICENSE) for full details.

---

**Version:** 1.0
**Last Updated:** 2025-01-07
**Created by:** [@mehdic](https://github.com/mehdic)

**Philosophy:** We built this to solve real problems we had. It's not perfect, but it works. If it helps you ship better software faster, we've succeeded.
