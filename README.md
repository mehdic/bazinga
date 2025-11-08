# BAZINGA - Claude Code Multi-Agent Dev Team

> **Repository:** https://github.com/mehdic/bazinga

A sophisticated multi-agent orchestration system for Claude Code that coordinates autonomous development teams including Project Manager, Developers, QA Expert, and Tech Lead agents working together to complete software projects.

## Quick Install

```bash
# One-time use (no installation required)
uvx --from git+https://github.com/mehdic/bazinga.git bazinga init my-project

# Or install the CLI
uv tool install bazinga-cli --from git+https://github.com/mehdic/bazinga.git
bazinga init my-project
```

## Overview

This system implements adaptive parallelism, intelligent workflow routing, and comprehensive role drift prevention to ensure high-quality software delivery through autonomous agent coordination.

### Built on Claude Code Skills

BAZINGA uses Claude Code Skills to provide agents with specialized tools like `/security-scan`, `/lint-check`, and `/codebase-analysis`. Skills return structured JSON output that agents can use to make decisions and validate their work.

## Features

- **🆕 Tech Debt Tracking**: Explicit logging of engineering tradeoffs with PM gate before deployment
- **🆕 Developer Superpowers Mode**: Keyword-activated enhanced capabilities (codebase analysis, test patterns, build checks)
- **🆕 Spec-Kit Integration**: Seamless integration with GitHub's spec-kit for spec-driven development (planning + execution)
- **🆕 Intelligent Model Escalation**: Automatically escalates Tech Lead to Opus after 3 failed revisions for deeper analysis
- **🆕 Claude Code Skills**: Automated security scanning, test coverage, and linting with dual-mode analysis (basic/advanced)
- **🆕 Multi-Language Support**: Full support for Python, JavaScript, Go, Java, and Ruby projects
- **🆕 Automated Tool Installation**: CLI automatically detects and offers to install analysis tools for your project
- **Adaptive Parallelism**: PM dynamically spawns 1-4 developers based on task complexity
- **Conditional Workflow**: Intelligent routing based on whether tests exist (Dev→QA→TechLead vs Dev→TechLead)
- **Role Drift Prevention**: 6-layer defense system preventing agents from forgetting their roles
- **Explicit Routing**: Each agent tells orchestrator exactly where to route next
- **Full Autonomy**: Agents work until 100% complete without asking user questions
- **Quality Gates**: QA Expert validates tests, Tech Lead reviews code quality
- **Project Completion**: PM is the only agent that sends BAZINGA signal
- **Cross-Platform Scripts**: Choose between bash or PowerShell scripts during installation
- **Modern CLI**: Easy installation via `uvx` or `uv tool install`

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

### Intelligent Model Escalation

BAZINGA automatically escalates the Tech Lead to use more powerful models when code revisions persist:

| Revision Count | Model Used | Strategy |
|----------------|------------|----------|
| **1-2 revisions** | Sonnet 4.5 | Fast, cost-effective reviews for typical issues |
| **3+ revisions** | Opus | Deep analysis for persistent, complex problems |

**How it works:**

1. **PM tracks revisions** - Updates `coordination/group_status.json` with revision count each time Tech Lead requests changes
2. **Orchestrator checks count** - Reads revision count before spawning Tech Lead
3. **Automatic escalation** - Uses `model: "opus"` parameter when revision_count >= 3
4. **Enhanced prompt** - Tech Lead receives special instructions for persistent issues:
   - Look for subtle bugs or design flaws
   - Verify edge cases are handled
   - Check for architectural issues
   - Consider if the approach itself needs rethinking

**Example:**

```
First review: Tech Lead (Sonnet) → "Add error handling"
Second review: Tech Lead (Sonnet) → "Fix edge case in validation"
Third review: Tech Lead (Opus) → "Architectural issue: authentication flow needs redesign"
```

This ensures cost-effective reviews for routine issues while providing deeper analysis when problems persist.

### Automated Code Analysis with Skills

BAZINGA includes three Claude Code Skills that provide automated security scanning, test coverage analysis, and code linting:

#### Progressive Analysis Strategy

Skills use **dual-mode analysis** that escalates alongside model escalation:

| Revision Count | Security Scan Mode | Tech Lead Model |
|----------------|-------------------|-----------------|
| **0-1 revisions** | Basic (5-10s, high/medium severity) | Sonnet 4.5 |
| **2 revisions** | Advanced (30-60s, all severities) | Sonnet 4.5 |
| **3+ revisions** | Advanced (comprehensive) | Opus |

#### Available Skills

**Default Skills (Always Available):**

1. **security-scan** - Security vulnerability detection
   - Basic: Fast scan for critical/high severity issues (5-10s)
   - Advanced: Deep analysis with multiple tools (30-60s)
   - Results: `coordination/security_scan.json`

2. **test-coverage** - Test coverage analysis
   - Generates line/branch coverage reports (5-20s)
   - Identifies untested code paths
   - Results: `coordination/coverage_report.json`

3. **lint-check** - Code quality linting
   - Style, complexity, best practices (3-10s)
   - Language-specific linters (ruff, eslint, golangci-lint, Checkstyle, etc.)
   - Results: `coordination/lint_results.json`

4. **velocity-tracker** - PM metrics and progress tracking (3-5s)
   - Measures development velocity (story points per run)
   - Tracks cycle time per task group
   - Detects 99% rule violations (tasks stuck >3x estimate)
   - Identifies trends (improving/stable/declining)
   - Enables continuous learning across runs
   - Results: `coordination/project_metrics.json`

#### Language Support

| Language | Security | Coverage | Linting |
|----------|----------|----------|---------|
| **Python** | bandit + semgrep | pytest-cov | ruff/pylint |
| **JavaScript** | npm audit + eslint | jest | eslint |
| **Go** | gosec | go test -cover | golangci-lint |
| **Java** | SpotBugs + OWASP | JaCoCo | Checkstyle + PMD |
| **Ruby** | brakeman | - | rubocop |

#### Error Handling

Skills include comprehensive error tracking with explicit status reporting:

```json
{
  "status": "success|partial|error",
  "tool": "bandit+semgrep",
  "error": "Semgrep scan failed",
  "results": [...]
}
```

This prevents false confidence from empty results - the Tech Lead always knows if a scan actually succeeded.

### Developer Superpowers Mode

BAZINGA includes enhanced Developer capabilities that can be activated by including the word **"superpowers"** in your orchestration request.

#### Two-Tier Capability System

**Standard Mode** (default):
- Fast, essential checks (1 min overhead)
- Pre-commit validation (lint-check Skill)
- Unit test enforcement
- Build verification

**Superpowers Mode** (keyword-activated):
- All standard capabilities PLUS:
- Codebase analysis before implementation
- Test pattern analysis before writing tests
- App startup health checks
- Code context injection (similar code & utilities)
- Enhanced workflow with comprehensive checks

#### How to Activate

Simply include "superpowers" in your orchestration request:

```bash
# Standard mode
/bazinga.orchestrate "Implement password reset endpoint"

# Superpowers mode - all advanced capabilities active
/bazinga.orchestrate "superpowers - Implement password reset endpoint"
```

#### Developer Capabilities in Superpowers Mode

**1. Codebase Analysis Skill** (10-20 seconds)
- Finds similar features in the codebase
- Discovers reusable utilities (EmailService, TokenGenerator, etc.)
- Detects architectural patterns (service layer, repository, factory)
- Suggests implementation approach
- Output: `coordination/codebase_analysis.json`

**2. Test Pattern Analysis Skill** (5-15 seconds)
- Detects test framework (pytest, jest, go test, JUnit)
- Extracts common fixtures and test utilities
- Identifies test patterns (AAA, Given-When-Then)
- Learns naming conventions
- Suggests test cases based on similar tests
- Output: `coordination/test_patterns.json`

**3. API Contract Validation Skill** (5-15 seconds)
- Detects breaking changes in OpenAPI/Swagger specifications
- Compares current spec against baseline
- Identifies removed endpoints, changed response types, removed fields
- Suggests safe migration strategies (API versioning)
- Supports FastAPI, Flask, Django, Express auto-generation
- Output: `coordination/api_contract_validation.json`

**4. Database Migration Check Skill** (5-20 seconds)
- Analyzes database migrations for dangerous operations
- Supports PostgreSQL, MySQL, SQL Server, MongoDB (+ SQLite, Oracle)
- Detects table locks, rewrites, data loss risks
- Suggests zero-downtime alternatives
- Works with Alembic, Django, Flyway, Liquibase, Mongoose, ActiveRecord
- Output: `coordination/db_migration_check.json`

**5. Code Context Injection**
- Orchestrator finds similar code before spawning Developer
- Injects relevant examples and utilities into Developer prompt
- Zero runtime cost (happens during spawn)

**6. Baseline Health Checks**
- Build check: Compiles project before/after development
- App startup check (superpowers only): Verifies app starts successfully
- Catches regressions immediately

**7. Mandatory Workflow**
- Pre-implementation: Review codebase context, run analysis Skills
- During implementation: Follow existing patterns
- Pre-commit: Run all unit tests (100% pass), lint-check, build verification, API/migration checks
- Only report READY_FOR_QA when all checks pass

#### Benefits

**Without Superpowers:**
- Developer implements from scratch → 45 minutes
- Misses existing utilities → duplicates code
- Uses wrong patterns → gets changes requested in review
- **Total:** 60-90 minutes with revision

**With Superpowers:**
- Skills find utilities → saves 15 minutes
- Follows existing patterns → passes review first time
- Reuses code → cleaner implementation
- **Total:** 30-40 minutes

**ROI:** 40% time savings, 90% fewer revisions

#### Time Overhead

- **Standard Mode:** ~1 minute (lint + build checks)
- **Superpowers Mode:** ~2-3 minutes (+ codebase analysis + test pattern analysis)

The 2-3 minute investment in superpowers mode typically saves 20-30 minutes during implementation.

### Tech Debt Tracking

BAZINGA includes explicit tech debt tracking to manage engineering tradeoffs transparently.

#### Core Principle: Try First, Log Later

⚠️ **Tech debt is for CONSCIOUS TRADEOFFS, not lazy shortcuts!**

Agents must attempt to solve issues properly before logging them as tech debt.

#### What Gets Logged

**✅ Valid Tech Debt (after 30+ min attempting to fix):**
- Architectural changes beyond current scope
- External dependency limitations
- Performance optimizations requiring data not yet available
- Features requiring infrastructure not in scope

**❌ Not Valid (fix these instead):**
- Missing error handling → Add it (10 min)
- No input validation → Add it (5 min)
- Hardcoded values → Use env vars (5 min)
- Skipped tests → Write them (your job)

#### Workflow

1. **Developer** encounters issue → attempts to fix (30+ min) → documents attempts → logs tech debt if out of scope
2. **Tech Lead** reviews tech debt → validates tradeoffs → may request fixes for "lazy" items
3. **PM** reviews before BAZINGA → checks for blocking items → gates deployment

#### PM Tech Debt Gate

Before sending BAZINGA, PM evaluates accumulated debt:

| Condition | PM Action | Result |
|-----------|-----------|--------|
| **Blocking items** (blocks_deployment=true) | ❌ Report to user | NO BAZINGA |
| **HIGH severity > 2** | ⚠️ Ask user approval | WAIT |
| **Only MEDIUM/LOW** | ✅ Include summary | BAZINGA with note |

#### Output

```json
// coordination/tech_debt.json
{
  "project_tech_debt": [
    {
      "id": "TD001",
      "added_by": "Developer-1",
      "severity": "high",
      "category": "performance",
      "description": "User search uses table scan, won't scale past 10K users",
      "location": "src/users/search.py:45",
      "impact": "Slow queries (>5s) at 10K+ users",
      "suggested_fix": "Implement Elasticsearch",
      "blocks_deployment": false,
      "attempts_to_fix": "1. Added DB indexes (helped but not enough)\n2. Tried query optimization\n3. Implemented pagination\nConclusion: Need search infrastructure"
    }
  ],
  "summary": {
    "total": 3,
    "by_severity": {"high": 1, "medium": 2},
    "blocking_items": 0
  }
}
```

#### Benefits

- **Transparency**: All shortcuts explicitly documented
- **Quality Gate**: PM prevents shipping with critical issues
- **User Control**: User decides acceptable tradeoffs
- **Future Planning**: Logged debt guides next iterations

**See `docs/TECH_DEBT_GUIDE.md` for complete guidelines**

### Data-Driven Project Management

BAZINGA PM uses metrics and retrospectives for continuous improvement.

#### The Problem (Before Metrics)

Traditional PM operated blind:
- ❌ No velocity measurement → Can't predict capacity
- ❌ No cycle time tracking → Can't detect bottlenecks
- ❌ No historical learning → Each run starts from zero
- ❌ No 99% rule detection → Tasks stuck at "almost done" forever
- ❌ No trend analysis → Can't tell if improving or declining

**Result:** PM was reactive firefighter, not proactive manager.

#### The Solution (Velocity Tracker + Retrospective)

**1. Velocity Tracker Skill**

Runs in 3-5 seconds (faster than lint-check):

```json
{
  "current_run": {
    "velocity": 12,
    "percent_complete": 60,
    "revision_rate": 1.2
  },
  "trends": {
    "velocity": "improving",
    "quality": "improving"
  },
  "warnings": [
    "G002 taking 3x longer than expected - escalate to Tech Lead"
  ],
  "recommendations": [
    "Current velocity (12) exceeds historical average (10.5)"
  ]
}
```

**2. Iteration Retrospective**

PM reflects after each run:

```json
{
  "what_worked": [
    "Parallel execution saved 2 hours",
    "Velocity tracker predicted delay early"
  ],
  "what_didnt_work": [
    "DB migrations took 3x estimate - complexity underestimated"
  ],
  "lessons_learned": [
    "Budget 2.5x for database tasks",
    "Check metrics after each task group"
  ],
  "improvements_for_next_time": [
    "Escalate stuck tasks sooner",
    "Emphasize unit test coverage"
  ]
}
```

**3. 99% Rule Detection**

Industry anti-pattern: underestimating final 1% that takes 99% of time.

PM automatically detects:
- Tasks in progress >2x average cycle time
- Multiple revisions (>3) with no resolution
- Developer-group pairs stuck >1 hour

**Action:** Escalate to Tech Lead, break into smaller tasks, or update estimates.

#### Benefits

**Before (Blind PM):**
- Reactive firefighting
- No learning between runs
- Tasks stuck forever
- No user visibility
- Estimation never improves

**After (Data-Driven PM):**
- Proactive bottleneck detection
- Continuous improvement
- Stuck tasks caught early (99% rule)
- User gets progress % and ETAs
- Estimates improve with data

**Example PM Decision:**
```markdown
Checking metrics... [invokes /velocity-tracker]

Current velocity: 12 (above avg 10.5) ✓
Trend: improving
⚠️  G002 taking 3x longer than expected

Action: Pace is good. Escalating G002 to Tech Lead for review.
```

#### Metrics Tracked

| Metric | Purpose | Good | Bad |
|--------|---------|------|-----|
| **Velocity** | Story points/run | Increasing | Decreasing |
| **Cycle Time** | Minutes/task group | Decreasing | Increasing |
| **Revision Rate** | Iterations/task | <1.5 | >3 |
| **Completion %** | Progress tracking | On track | Stuck |

**Historical Learning:**

Every run improves the baseline. After 5 runs, PM knows:
- "Database tasks take 2.5x initial estimate"
- "Parallel execution saves ~40%"
- "Current team velocity averages 11 points"

This knowledge makes future estimates accurate and planning realistic.

## Project Structure

```
bazinga/
├── README.md                    # This file
├── LICENSE                      # MIT License
├── pyproject.toml              # Python package configuration
├── src/                         # Python CLI source code
│   └── bazinga_cli/            # Main CLI package
│       └── __init__.py         # CLI implementation (init, check commands)
├── agents/                      # Agent definitions
│   ├── orchestrator.md         # Main orchestrator agent
│   ├── developer.md            # Developer implementation specialist
│   ├── qa_expert.md            # QA testing specialist
│   ├── techlead.md             # Tech lead reviewer
│   └── project_manager.md      # Project coordinator
├── commands/                    # Slash commands
│   ├── bazinga.orchestrate.md          # /bazinga.orchestrate command
│   └── bazinga.orchestrate-from-spec.md # /bazinga.orchestrate-from-spec command
├── scripts/                     # Utility scripts
│   ├── init-orchestration.sh   # Initialization script (bash)
│   ├── init-orchestration.ps1  # Initialization script (PowerShell)
│   ├── tech_debt.py            # 🆕 Tech debt management utility
│   └── README.md                # Scripts documentation
├── docs/                        # Documentation
│   └── TECH_DEBT_GUIDE.md      # 🆕 Complete tech debt guidelines
├── .claude/                     # Claude Code configuration (copied to projects)
│   └── skills/                 # Automated analysis Skills
│       ├── security-scan/      # Security vulnerability scanning
│       ├── test-coverage/      # Test coverage analysis
│       ├── lint-check/         # Code quality linting
│       ├── velocity-tracker/   # 🆕 PM metrics & velocity tracking (default)
│       ├── codebase-analysis/  # 🆕 Codebase pattern analysis (superpowers)
│       ├── test-pattern-analysis/ # 🆕 Test pattern extraction (superpowers)
│       ├── api-contract-validation/ # 🆕 API breaking change detection (superpowers)
│       └── db-migration-check/ # 🆕 Database migration safety (superpowers)
├── config/                      # Configuration files
│   ├── claude.md               # Global constraints (.claude.md)
│   └── coordination.gitignore  # Gitignore for coordination folder
├── docs/                        # Documentation
│   ├── DOCS_INDEX.md           # Documentation navigation guide
│   ├── ARCHITECTURE.md         # Detailed architecture
│   ├── ROLE_DRIFT_PREVENTION.md # 6-layer defense system
│   ├── SCOPE_REDUCTION_INCIDENT.md # Case study
│   └── original-v4/            # Original development docs
│       ├── V4_ARCHITECTURE.md
│       ├── V4_IMPLEMENTATION_SUMMARY.md
│       ├── V4_STATE_SCHEMAS.md
│       └── V4_WORKFLOW_DIAGRAMS.md
└── examples/                    # Example usage
    └── EXAMPLES.md             # Practical usage examples
```

## Installation

BAZINGA can be installed using the modern Python package manager `uv` or traditional methods.

### Prerequisites

- Python 3.11 or higher
- Git (optional, for repository initialization)
- [uv](https://github.com/astral-sh/uv) package manager (recommended)

### Quick Start (Recommended)

**Option 1: One-Time Use with uvx**

Initialize BAZINGA in a new project without installing:

```bash
# Create a new project with BAZINGA
uvx --from git+https://github.com/mehdic/bazinga.git bazinga init my-project

# Or initialize in current directory
uvx --from git+https://github.com/mehdic/bazinga.git bazinga init --here
```

**During initialization, you'll be prompted to choose your script type:**
```
Select script type:
  1. POSIX Shell (bash/zsh) - Linux/macOS
  2. PowerShell - Windows/Cross-platform

Default for your platform: POSIX Shell (bash/zsh) - Linux/macOS
Enter choice (1 or 2, or press Enter for default):
```

Choose the script type that matches your environment and workflow preferences.

**Option 2: Install CLI Tool**

Install the BAZINGA CLI for repeated use:

```bash
# Install using uv
uv tool install bazinga-cli --from git+https://github.com/mehdic/bazinga.git

# Now use it anywhere
bazinga init my-project
```

**Option 3: Traditional pip install**

```bash
# Install from git
pip install git+https://github.com/mehdic/bazinga.git

# Use it
bazinga init my-project
```

### CLI Commands

**Initialize a new project:**
```bash
# Create a new project directory
bazinga init my-project

# Initialize in current directory
bazinga init --here

# Skip git initialization
bazinga init my-project --no-git

# Skip confirmation prompts
bazinga init my-project --force
```

**Update to latest version:**
```bash
# Update BAZINGA components in current project
bazinga update

# Skip confirmation prompt
bazinga update --force
```

This updates:
- Agent definitions (`.claude/agents/`)
- Scripts (`.claude/scripts/`) - preserves your script type choice
- Commands (`.claude/commands/`)
- Configuration (`.claude.md` - merged if needed)

**Preserved during update:**
- Coordination state files (`coordination/`)
- Your ongoing orchestration sessions
- Custom project configuration in `.claude.md`
- Your script type preference (bash or PowerShell)

**Check system requirements:**
```bash
# Verify installation and setup
bazinga check
```

**Show version:**
```bash
bazinga --version
```

### What Gets Installed

When you run `bazinga init`, the following structure is created:

```
your-project/
├── .claude/
│   ├── agents/                 # 5 agent definitions
│   │   ├── orchestrator.md    # Main message router
│   │   ├── project_manager.md # Project coordinator
│   │   ├── developer.md       # Code implementer
│   │   ├── qa_expert.md       # Testing specialist
│   │   └── techlead.md        # Quality reviewer
│   ├── commands/              # Slash commands
│   │   └── orchestrate.md     # /orchestrate command
│   └── scripts/               # Utility scripts (your choice)
│       └── init-orchestration.sh   # (if you chose bash)
│       └── init-orchestration.ps1  # (if you chose PowerShell)
├── coordination/              # State files (auto-generated)
│   ├── pm_state.json
│   ├── group_status.json
│   ├── orchestrator_state.json
│   └── messages/
├── .claude.md                 # Global configuration
└── .git/                      # Git repository (optional)
```

**Script Type Selection:**
- **POSIX Shell (bash/zsh)** - Best for Linux/macOS environments
- **PowerShell** - Best for Windows or cross-platform teams using PowerShell Core (pwsh)
- Only the scripts for your selected type are installed (not both)
- Your choice is preserved during updates

### Manual Installation (Alternative)

If you prefer to install manually or don't have uv installed:

<details>
<summary>Click to expand manual installation steps</summary>

```bash
# Clone the repository
git clone https://github.com/mehdic/bazinga.git
cd bazinga

# Install using pip
pip install -e .

# Or copy files manually to your project
cd /path/to/your/project
mkdir -p .claude/agents .claude/scripts .claude/commands
cp /path/to/bazinga/agents/*.md .claude/agents/
cp /path/to/bazinga/scripts/* .claude/scripts/
cp /path/to/bazinga/commands/orchestrate.md .claude/commands/
cp /path/to/bazinga/config/claude.md .claude.md
chmod +x .claude/scripts/init-orchestration.sh

# Run initialization
bash .claude/scripts/init-orchestration.sh
```

</details>

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

## 🆕 Spec-Kit Integration

**NEW**: BAZINGA now integrates seamlessly with GitHub's [spec-kit](https://github.com/github/spec-kit) for spec-driven development! This combines spec-kit's rigorous planning with BAZINGA's powerful execution.

### What is Spec-Kit Integration?

Spec-kit provides a structured planning workflow:
1. `/speckit.constitution` - Define project principles
2. `/speckit.specify` - Create feature specifications
3. `/speckit.plan` - Generate technical plans
4. `/speckit.tasks` - Break down into executable tasks

BAZINGA integration allows you to:
- ✅ Use spec-kit for planning (specification, architecture, task breakdown)
- ✅ Use BAZINGA for execution (adaptive parallelism, multi-agent coordination)
- ✅ Maintain traceability from spec to code
- ✅ Track progress in real-time with tasks.md checkmarks

### Complete Workflow

```bash
# Phase 1: Planning with Spec-Kit
/speckit.constitution                    # First time only
/speckit.specify Add JWT authentication  # Create spec.md
/speckit.plan                            # Create plan.md, research.md
/speckit.tasks                           # Create tasks.md with task breakdown

# Phase 2: Execution with BAZINGA
/orchestrate-from-spec                   # Execute using BAZINGA orchestration

# Phase 3: Validation
/speckit.analyze                         # Validate consistency (optional)
```

### How It Works

The `/orchestrate-from-spec` command uses the **full BAZINGA multi-agent team**:

**Team Members Involved**:
- 🎯 **Orchestrator** - Routes messages between all agents
- 📋 **Project Manager (PM)** - Coordinates execution, tracks progress
- 👨‍💻 **Developers** (1-4) - Implement code based on spec-kit tasks
- 🧪 **QA Expert** - Tests integration/contract/E2E tests (if tests exist)
- 👔 **Tech Lead** - Reviews code quality and security

**Workflow**:

1. **Loads spec-kit artifacts**:
   ```
   ✅ spec.md - Feature requirements
   ✅ tasks.md - Task breakdown with IDs (T001, T002, T003...)
   ✅ plan.md - Technical approach
   ✅ research.md - Research findings (optional)
   ✅ data-model.md - Data structures (optional)
   ```

2. **PM reads and parses tasks.md**:
   ```
   Task format: - [ ] [T001] [P] [US1] Description (file.py)

   Where:
   - T001 = Task ID
   - [P] = Parallel execution marker
   - [US1] = User story grouping
   - file.py = Target file
   ```

3. **PM creates BAZINGA groups**:
   ```
   Groups tasks by [US] markers:
   - Tasks with [US1] → Group US1
   - Tasks with [US2] → Group US2
   - Uses [P] markers to determine parallelism
   - Spawns 1-4 developers based on analysis
   ```

4. **Developers implement with context**:
   ```
   Each developer receives:
   - Assigned task IDs (e.g., T002, T003)
   - spec.md for requirements
   - plan.md for technical approach
   - tasks.md for full context

   Updates tasks.md with checkmarks as they complete each task
   ```

5. **QA Expert tests** (conditional):
   ```
   If developer created/fixed integration/contract/E2E tests:
   - Runs all test suites
   - Reports PASS/FAIL to Tech Lead
   - Developer fixes if FAIL, loops back to QA
   ```

6. **Tech Lead reviews**:
   ```
   Reviews code quality, security, best practices
   - Decision: APPROVED → forwards to PM
   - Decision: CHANGES_REQUESTED → back to Developer
   ```

7. **PM tracks completion**:
   ```
   Verifies all tasks marked [x] in tasks.md
   When all groups approved: sends BAZINGA 🎉
   ```

### Example: JWT Authentication

```bash
# Step 1: Specify feature
/speckit.specify Implement JWT authentication with access and refresh tokens

# Spec-kit creates:
# - .specify/features/001-jwt-auth/spec.md
# - Feature requirements and acceptance criteria

# Step 2: Generate plan
/speckit.plan

# Spec-kit creates:
# - .specify/features/001-jwt-auth/plan.md (technical approach)
# - .specify/features/001-jwt-auth/research.md (unknowns resolved)
# - .specify/features/001-jwt-auth/data-model.md (token structure)

# Step 3: Break down into tasks
/speckit.tasks

# Spec-kit creates tasks.md:
# - [ ] [T001] [P] Setup: Create auth module (auth/__init__.py)
# - [ ] [T002] [P] [US1] JWT generation (auth/jwt.py)
# - [ ] [T003] [P] [US1] Token validation (auth/jwt.py)
# - [ ] [T004] [US2] Login endpoint (api/login.py)
# - [ ] [T005] [US2] Logout endpoint (api/logout.py)
# - [ ] [T006] [US3] Token refresh endpoint (api/refresh.py)

# Step 4: Execute with BAZINGA
/orchestrate-from-spec

# BAZINGA orchestration (FULL TEAM):
#
# 📋 PM analyzes tasks.md:
#    - 3 user stories identified (US1, US2, US3)
#    - Tasks T001-T003 can run in parallel ([P] markers)
#    - US2 depends on US1, US3 depends on US1
#    - Decision: PARALLEL MODE
#
# Phase 1 (2 developers in parallel):
#
#   👨‍💻 Developer 1 → Group SETUP + US1 (T001, T002, T003)
#      - Reads spec.md for JWT requirements
#      - Reads plan.md for PyJWT library approach
#      - Implements JWT generation + validation
#      - Creates integration tests
#      - Updates tasks.md: [x] T001, [x] T002, [x] T003
#      - Status: READY_FOR_QA
#
#   🧪 QA Expert tests Developer 1's work:
#      - Runs integration tests (JWT flow)
#      - All tests passing
#      - Status: PASS → forwards to Tech Lead
#
#   👔 Tech Lead reviews Developer 1's work:
#      - Code quality: Good (clean, documented)
#      - Security: Good (HS256, secrets in env)
#      - Decision: APPROVED → forwards to PM
#
#   👨‍💻 Developer 2 → Group US2 (T004, T005)
#      - Implements login/logout endpoints
#      - Creates integration tests
#      - Updates tasks.md: [x] T004, [x] T005
#      - Status: READY_FOR_QA
#
#   🧪 QA Expert tests Developer 2's work:
#      - Runs endpoint integration tests
#      - All tests passing
#      - Status: PASS → forwards to Tech Lead
#
#   👔 Tech Lead reviews Developer 2's work:
#      - Code quality: Good
#      - Uses JWT from US1 correctly
#      - Decision: APPROVED → forwards to PM
#
# 📋 PM checks progress:
#    - US1: APPROVED ✓
#    - US2: APPROVED ✓
#    - US3: Still pending
#    - Spawns next phase...
#
# Phase 2 (after US1 complete):
#
#   👨‍💻 Developer 3 → Group US3 (T006)
#      - Implements token refresh endpoint
#      - Creates integration tests
#      - Updates tasks.md: [x] T006
#      - Status: READY_FOR_QA
#
#   🧪 QA Expert → PASS
#   👔 Tech Lead → APPROVED
#
# 📋 PM final check:
#    - All tasks in tasks.md marked [x]
#    - All groups approved by Tech Lead
#    - Result: BAZINGA 🎉
#
# ✅ Feature complete with full quality gates!
```

### Benefits of Integration

| Aspect | Spec-Kit Only | BAZINGA Only | **Integrated** |
|--------|--------------|--------------|----------------|
| **Planning** | ✅ Structured | ⚠️ Basic | ✅ Structured |
| **Execution** | ⚠️ Manual | ✅ Automated | ✅ Automated |
| **Parallelism** | ❌ No | ✅ Yes | ✅ Yes (spec-guided) |
| **Progress Tracking** | ✅ tasks.md | ⚠️ Logs only | ✅ Both |
| **Quality Gates** | ✅ Analyze | ✅ QA/Tech Lead | ✅ Both |
| **Traceability** | ✅ Task IDs | ❌ No | ✅ Full |

### Helper Script

Analyze spec-kit tasks.md:

```bash
# Bash
bash .claude/scripts/parse-speckit-tasks.sh .specify/features/001-auth/tasks.md

# PowerShell
pwsh .claude/scripts/parse-speckit-tasks.ps1 .specify/features/001-auth/tasks.md

# Output:
# ═══════════════════════════════════════════
# SPEC-KIT TASKS ANALYSIS
# ═══════════════════════════════════════════
# 📋 Total Tasks: 6
# ✅ Completed: 3
# ⏳ Pending: 3
# 📊 Progress: 50%
#
# 🔀 Tasks marked [P]: 3
# [User stories breakdown...]
# [JSON summary...]
```

### Automatic Agent Selection

BAZINGA intelligently chooses the right orchestrator based on context:

**🤖 Automatic Detection:**

| Your Request | Context | Agent Used | Workflow |
|--------------|---------|------------|----------|
| "Implement JWT auth" | No tasks.md | `@orchestrator` | Standard BAZINGA |
| "Execute JWT feature" | tasks.md exists | `@orchestrator_speckit` | Spec-kit integration |
| "Build API endpoints" | No tasks.md | `@orchestrator` | Standard BAZINGA |
| "Run the auth spec" | tasks.md exists | `@orchestrator_speckit` | Spec-kit integration |

**How It Works:**
- Claude automatically detects if `.specify/features/*/tasks.md` exists
- If tasks.md found → Uses spec-kit orchestrator (reads artifacts)
- If no tasks.md → Uses regular orchestrator (PM creates breakdown)
- No manual agent selection needed!

**Explicit Invocation (Optional):**
```bash
# Force standard orchestrator
@orchestrator implement feature X

# Force spec-kit orchestrator
@orchestrator_speckit execute feature

# Or use commands
/orchestrate implement feature X
/orchestrate-from-spec
```

### Requirements

- BAZINGA v1.0+ (this version)
- Spec-kit installed and initialized (`/speckit.constitution`) - for spec-kit mode only
- Feature planned with spec-kit (`/speckit.specify`, `/speckit.plan`, `/speckit.tasks`) - for spec-kit mode only

### Documentation

See:
- [`agents/orchestrator.md`](agents/orchestrator.md) - Standard orchestrator (proactive)
- [`agents/orchestrator_speckit.md`](agents/orchestrator_speckit.md) - Spec-kit orchestrator (proactive when tasks.md exists)
- [`commands/orchestrate-from-spec.md`](commands/orchestrate-from-spec.md) - Full command documentation
- [`agents/project_manager.md`](agents/project_manager.md) - PM spec-kit mode section
- [`agents/developer.md`](agents/developer.md) - Developer spec-kit mode section
- [`scripts/parse-speckit-tasks.sh`](scripts/parse-speckit-tasks.sh) - Task parser utility

---

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
