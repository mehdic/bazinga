# BAZINGA - AI Development with Enforced Engineering Practices

> **Repository:** https://github.com/mehdic/bazinga

**AI that codes like a professional engineering team—with mandatory code review, security scanning, and test coverage on every change.**

BAZINGA coordinates teams of AI agents that follow professional software engineering practices automatically. Every change gets security scanning, lint checking, test coverage analysis, and independent code review. The same rigorous process professional teams follow—enforced, not optional. Powered by [Agentic Context Engineering](#core-philosophy-agentic-context-engineering).

---

## What Makes This Different

**The problem with AI coding today:** AI generates code, you accept it, commit it—hope it's secure. No security scan. No code review. No test coverage check. We'd never accept this from a human developer.

**BAZINGA's approach:** Enforce the same engineering practices on AI that we require from humans.

Every change automatically receives:
- **Security scanning** - SQL injection, XSS, hardcoded secrets, dependency vulnerabilities
- **Lint checking** - Code style, complexity, best practices
- **Test coverage analysis** - Measured, not assumed
- **Independent code review** - Tech Lead agent reviews all code (writers don't review themselves)

The framework enforces separation of concerns: the Developer agent writes code, a separate Tech Lead agent reviews it. Same principle as professional teams. No shortcuts. No skipped reviews.

---

## Core Philosophy: Agentic Context Engineering

BAZINGA is strictly architected on the principles of **Agentic Context Engineering (ACE)**, solving the "infinite context fallacy" where larger context windows lead to signal dilution and reasoning drift.

Instead of treating memory as a simple chat log, BAZINGA implements a **Tiered Memory Model** (Working Context, Sessions, Memory, Artifacts) inspired by research from Google's ADK and Anthropic.

- **Context as a Compiled View:** Every agent prompt is dynamically compiled from the database, projecting only the minimal, relevant slice of history needed for the specific task.
- **State Offloading:** Heavy research and file contents are offloaded to **Context Packages** (Artifacts), preventing token bloat. Agents receive pointers to this data and must actively "read" it, keeping the working context clean.
- **Reasoning Capture:** We separate *what* happened (Interaction Logs) from *why* it happened (Reasoning Logs), allowing agents to evolve strategies without carrying the full weight of execution history.

### The Problem & Solution

![The Context Window Fallacy](docs/reference/TheContextWindowsFlallacy.png)
*The "Infinite Context" Fallacy vs. the Compiled View Architecture—why bigger context windows don't equal better performance.*

### BAZINGA's Implementation

![The BAZINGA Playbook](docs/reference/TheBazingaPlaybook.png)
*How BAZINGA implements the 9 scaling principles: tiered memory, state offloading, schema-driven summarization, and sub-agent isolation.*

For a detailed breakdown of the theory and our implementation, see the [Agentic Context Engineering Reference](docs/reference/agentic_context_engineering.md).

---

## See It In Action

```bash
/bazinga.orchestrate implement JWT authentication, user registration, and password reset
# (or: @orchestrator implement JWT authentication, user registration, and password reset)
```

**What happens:**

```
PM: "Analyzing request... 3 independent features detected"
PM: "Security-sensitive features - enforcing auth security guidelines"

┌─────────────────────┬─────────────────────┬─────────────────────┐
│  Developer 1 (JWT)  │  Developer 2 (Reg)  │  Developer 3 (Pwd)  │
├─────────────────────┼─────────────────────┼─────────────────────┤
│ ✓ Implementation    │ ✓ Implementation    │ ✓ Implementation    │
│ ✓ Unit tests        │ ✓ Unit tests        │ ✓ Unit tests        │
│ ✓ Security scan     │ ✓ Security scan     │ ✓ Security scan     │
│ ✓ Lint check        │ ✓ Lint check        │ ✓ Lint check        │
│ ✓ Coverage check    │ ✓ Coverage check    │ ✓ Coverage check    │
└─────────────────────┴─────────────────────┴─────────────────────┘

Tech Lead: "Reviewing all implementations for security and architecture..."
Tech Lead: "✓ Token handling secure, ✓ Password hashing correct, ✓ No secrets exposed"

PM: "BAZINGA! All features complete - all quality gates passed"
```

**Result:** 3 features implemented, tested, security-scanned, and reviewed. Every change met engineering standards before completion.

---

## Quick Start

```bash
# Option 1: Create new project
uvx --from git+https://github.com/mehdic/bazinga.git bazinga init my-project
cd my-project
/bazinga.orchestrate implement user authentication with JWT

# Option 2: Initialize in current directory
cd your-existing-project
uvx --from git+https://github.com/mehdic/bazinga.git bazinga init --here
/bazinga.orchestrate implement user authentication with JWT

# Note: You can also use @orchestrator instead of /bazinga.orchestrate if you prefer
```

That's it. No configuration needed. BAZINGA automatically:
- ✅ Analyzes task complexity and independence
- ✅ Spawns 1-4 developers based on parallelization opportunities
- ✅ Runs security scans, lint checks, and test coverage
- ✅ Reviews code quality with Tech Lead
- ✅ Escalates to more powerful models (Opus) for difficult problems

### Advanced Mode (Optional)

For complex or ambiguous requests, use the enhanced orchestration command:

```bash
/bazinga.orchestrate-advanced "improve our authentication system"
```

**What it does:**
1. **Clarifies** ambiguous requests through interactive Q&A
2. **Discovers** existing codebase infrastructure and patterns
3. **Assesses** complexity, risks, and parallelization opportunities
4. **Structures** enhanced requirements for the PM

This adds 2-4 minutes upfront but provides better decisions, fewer revisions, and prevents issues by identifying risks early. Use for complex features, new architecture, or unclear requirements.

---

## How It Works

### The Team

BAZINGA coordinates 9 specialized AI agents:

1. **Tech Stack Scout** - Auto-detects project technology stack, frameworks, and versions before development begins
2. **Project Manager (PM)** - Analyzes requirements, breaks down work, decides parallelism
3. **Requirements Engineer** - Clarifies ambiguous requests, discovers codebase patterns, assesses complexity (used with `/orchestrate-advanced`)
4. **Developers (1-4)** - Implement code in parallel, create tests, fix issues
5. **Senior Software Engineer (SSE)** - Handles medium-to-complex tasks (complexity 4-10), security-sensitive code, and architectural work; escalation target when Developers get stuck
6. **QA Expert** - Runs integration/contract/E2E tests (optional, advanced mode)
7. **Tech Lead** - Reviews code quality, security, architecture; classifies problem complexity
8. **Investigator** - Deep-dive systematic investigation for complex multi-hypothesis problems (spawned by Tech Lead)
9. **Orchestrator** - Routes messages between agents, maintains workflow, manages investigation loops

All agents are enhanced with **72 technology specializations** covering languages, frameworks, databases, and infrastructure—ensuring each agent receives context-appropriate expertise for your project's tech stack.

### The Workflow

```
Your request
    ↓
PM analyzes → Detects N independent tasks
    ↓
Spawns N developers in parallel
    ↓
Each developer:
  - Implements feature
  - Writes unit tests
  - Runs security scan
  - Runs lint check
  - Measures coverage
    ↓
Tech Lead reviews → Classifies problem complexity
    ↓
    ├─ Simple (80%) → Standard review → Approve/Request changes
    ├─ Complex (15%) → Apply framework → Approve/Request changes
    │   • Root Cause Analysis (5 Whys + Hypothesis Matrix)
    │   • Architectural Decision Analysis
    │   • Performance Investigation
    │   • Flaky Test Analysis
    │   • Security Issue Triage
    └─ Investigation Required (5%) → Spawn Investigator
        ↓
        Investigation Loop (max 5 iterations):
          1. Investigator analyzes hypothesis matrix
          2. Decides action (diagnostic code, testing, analysis)
          3. May spawn Developer for diagnostic changes
          4. Returns findings and updated hypotheses
          5. Repeat until root cause found or blocked
        ↓
        Tech Lead validates findings
    ↓
PM confirms → BAZINGA!
```

### Adaptive Parallelism

The PM automatically decides how many developers to spawn (1-4) based on:
- **Task independence** - Can features be built separately?
- **File overlap** - Do they modify the same files?
- **Dependencies** - Does Task B depend on Task A?
- **Complexity** - Is parallelism worth coordination overhead?

**Example decisions:**

| Request | PM Decision | Reasoning |
|---------|-------------|-----------|
| "Implement JWT auth" | 1 developer | Single feature, no parallelism benefit |
| "Add auth, user mgmt, admin dashboard" | 3 developers | Independent features, low file overlap |
| "Add login and password reset" | 1 developer | Password reset depends on auth |
| "Refactor database layer" | 1 developer | High file overlap, risky in parallel |

---

## Automatic Quality Gates

Every feature automatically gets:

### Security Scanning
- **Tool:** bandit (Python), npm audit (JS), gosec (Go), brakeman (Ruby), SpotBugs (Java)
- **Checks:** SQL injection, XSS, hardcoded secrets, auth bypasses, insecure dependencies
- **Escalation:** Basic scan (5-10s) → Advanced scan (30-60s) after 2 revisions

### Lint Checking
- **Tool:** ruff/pylint (Python), eslint (JS), golangci-lint (Go), rubocop (Ruby), Checkstyle (Java)
- **Checks:** Code style, complexity, best practices, common mistakes
- **Enforcement:** All issues must be fixed before approval

### Test Coverage
- **Tool:** pytest-cov (Python), jest (JS), go test (Go), simplecov (Ruby), JaCoCo (Java)
- **Checks:** Line coverage, branch coverage, untested code paths
- **Target:** 80% coverage by default

**Missing tools?** No problem. BAZINGA gracefully degrades—warns you but continues working.

---

## Advanced Problem-Solving Frameworks

Tech Lead automatically classifies every code review and applies the appropriate problem-solving approach:

### Tier 1: Standard Review (80%)
Clear implementation, no issues → Standard code review workflow

### Tier 2: Structured Frameworks (15%)
Complex but single-hypothesis problems → Apply specialized framework:

| Framework | When Used | Techniques |
|-----------|-----------|------------|
| **Root Cause Analysis** | Unclear bug origin | 5 Whys, Hypothesis Matrix (likelihood scoring) |
| **Architectural Decision** | Choosing between approaches | Decision Matrix (weighted criteria) |
| **Performance Investigation** | Slow endpoints, memory issues | Profiling, bottleneck analysis |
| **Flaky Test Analysis** | Intermittent test failures | Race condition detection, timing analysis |
| **Security Issue Triage** | Vulnerability findings | Severity assessment, exploit analysis |

### Tier 3: Deep Investigation (5%)
Multi-hypothesis problems with unclear root cause → Spawn Investigator agent:

**Investigation Loop (max 5 iterations):**
1. **Hypothesis Matrix** - Rank theories by likelihood (1-10 scale)
2. **Action Selection** - Choose diagnostic strategy (code changes, testing, analysis)
3. **Execute & Gather Evidence** - May spawn Developer for diagnostic code
4. **Update Hypotheses** - Eliminate or confirm theories based on evidence
5. **Repeat** - Until root cause found or investigation blocked

**Triggers for Investigation (≥2 criteria required):**
- Root cause unclear after initial analysis
- Requires iterative hypothesis testing
- Needs diagnostic code changes (logging, profiling)
- Multi-variable problem (A works, B works, A+B fails)
- Environmental differences (prod vs staging)
- Intermittent/non-deterministic behavior
- Performance issue without obvious hotspot
- Would take Developer >2 attempts to solve

**Investigation Actions:**
- `ROOT_CAUSE_FOUND` - Investigation complete, solution identified
- `NEED_DEVELOPER_DIAGNOSTIC` - Request diagnostic code changes
- `HYPOTHESIS_ELIMINATED` - Theory disproven, continue with next
- `NEED_MORE_ANALYSIS` - Deeper analysis required
- `BLOCKED` - Cannot proceed, escalate to PM

---

## Intelligent Model Escalation

Stuck on a hard problem? BAZINGA automatically escalates to more powerful models:

```
Revision 1-2: Claude Sonnet (fast, handles 90% of reviews)
Revision 3+:  Claude Opus (deep analysis for persistent issues)
```

**Why this matters:**
- **Cost-effective** - Use fast Sonnet for typical work
- **Automatic** - No manual model switching
- **Smart** - Opus only when truly needed

### Two-Tier Developer System

PM assigns tasks to the right tier based on complexity:

| Complexity | Tier | Model |
|------------|------|-------|
| 1-6 (standard) | Developer | Sonnet |
| 7-10 (complex) | Senior Software Engineer | Sonnet |

**Override rules:** Security-sensitive or architectural tasks always go to Senior Software Engineer, regardless of score.

**Details:** See [research/tier-and-model-decision-flow.md](research/tier-and-model-decision-flow.md)

---

## Multi-Language Support

Full support for Python, JavaScript/TypeScript, Go, Java, and Ruby projects:

| Language | Security | Coverage | Linting |
|----------|----------|----------|---------|
| Python | bandit + semgrep | pytest-cov | ruff/pylint |
| JavaScript/TypeScript | npm audit + eslint | jest | eslint |
| Go | gosec | go test -cover | golangci-lint |
| Java | SpotBugs + OWASP | JaCoCo | Checkstyle + PMD |
| Ruby | brakeman | simplecov | rubocop |

Automated tool installation during setup (optional).

---

## Examples

### Single Feature (Simple Mode)

```bash
/bazinga.orchestrate fix bug where users can't reset password
```

**Flow:** PM → Developer → Security scan → Lint → Tech Lead review → BAZINGA
**Quality gates:** Security scan for auth vulnerabilities, lint check, coverage verification

### Multiple Features (Parallel Mode)

```bash
/bazinga.orchestrate implement REST API with auth, user management, and admin endpoints
```

**Flow:** PM → 3 Developers (parallel) → Each gets security scan + lint → Tech Lead reviews all → BAZINGA
**Quality gates:** Independent security scan per feature, architecture review across all endpoints

### Large Project

```bash
/bazinga.orchestrate build a blog platform with posts, comments, tags, and search
```

**Flow:** PM → 4 Developers (parallel, 2 phases) → QA integration tests → Tech Lead → BAZINGA
**Quality gates:** Full test coverage, XSS prevention for user content, SQL injection checks

---

## Configuration

BAZINGA works out of the box with sensible defaults. Want more control?

### Testing Modes

```bash
/bazinga.configure-testing
```

- **Minimal** (default) - Lint + unit tests, fast iteration (30-40% faster)
- **Full** - All tests + QA Expert for integration/E2E tests (production quality)
- **Disabled** - Lint only, rapid prototyping (40-60% faster)

### Advanced Skills

```bash
/bazinga.configure-skills
```

**Core Skills** (always active):
- `security-scan` - Vulnerability detection (Tech Lead)
- `lint-check` - Code quality and style (Developer, Tech Lead)
- `test-coverage` - Coverage analysis (Tech Lead)
- `codebase-analysis` - Pattern extraction from similar code (Investigator)
- `pattern-miner` - Historical pattern analysis (Investigator)

**Advanced Skills** (opt-in):
- `velocity-tracker` - PM metrics and velocity tracking
- `test-pattern-analysis` - Test framework learning
- `api-contract-validation` - Breaking change detection
- `db-migration-check` - Migration safety analysis
- `quality-dashboard` - Unified health metrics

### CLI Options

```bash
# Default (lite profile)
bazinga init my-project       # Create new project directory
bazinga init --here           # Initialize in current directory
bazinga init                  # Same as --here (defaults to current directory)

# Advanced profile (all features enabled)
bazinga init my-project --profile advanced
bazinga init --here --profile advanced

# Custom configuration
bazinga init my-project --testing full --skills all

# Update existing project
bazinga update
```

---

## Key Features

- **Mandatory Security Scanning** - Every change scanned for vulnerabilities, secrets, injection attacks
- **Independent Code Review** - Tech Lead reviews all code (writers don't review themselves)
- **Enforced Test Coverage** - Coverage measured and tracked, not assumed
- **Full Audit Trail** - All decisions logged with reasoning for compliance and learning
- **3-Tier Problem Solving** - Standard review (80%), structured frameworks (15%), deep investigation (5%)
- **Coordinated Development** - 1-4 developers working together, automatically managed
- **Model Escalation** - Automatically escalates to Opus for persistent complex issues
- **Multi-language Support** - Python, JavaScript/TypeScript, Go, Java, Ruby

---

## Real Problems BAZINGA Solves

### Before BAZINGA

**AI coding without safeguards:**
```
AI: *generates authentication code*
You: "Looks good" → Commit

No security scan.
No code review.
No test coverage check.
Hope it's secure.
```

**Result:** AI-generated code bypasses all the engineering practices we've built.

### After BAZINGA

```
You: "/bazinga.orchestrate implement auth, user management, and admin dashboard"
```

**What happens automatically:**
- Security scan catches SQL injection in user query
- Lint check flags complexity issue
- Tech Lead requests better error handling
- Developer fixes issues
- Tech Lead approves
- All changes logged for audit

**Result:** Production-quality code. Same standards as human-written code.

---

## Installation

### Option 1: One-time Use (No Installation)

```bash
uvx --from git+https://github.com/mehdic/bazinga.git bazinga init my-project
```

### Option 2: Install as Tool

```bash
# Using uv (recommended)
uv tool install bazinga-cli --from git+https://github.com/mehdic/bazinga.git
bazinga init my-project

# Using pip
pip install git+https://github.com/mehdic/bazinga.git
bazinga init my-project
```

### System Requirements

- Python 3.11+
- Claude Code (with Claude agent SDK)
- Git
- Optional: Security/lint/coverage tools for your language (auto-installed during setup)

---

## Documentation

### Getting Started
- **README.md** (this file) - Overview and quick start
- **[examples/EXAMPLES.md](examples/EXAMPLES.md)** - Practical usage examples
- **[docs/QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)** - Common commands and workflows

### Advanced Features
- **[docs/ADVANCED.md](docs/ADVANCED.md)** - Advanced skills, full testing mode, integrations
- **[docs/SKILLS.md](docs/SKILLS.md)** - Complete Skills reference
- **[docs/MODEL_ESCALATION.md](docs/MODEL_ESCALATION.md)** - How and why Opus escalation works

### Architecture & Design
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Technical deep-dive
- **[docs/ROLE_DRIFT_PREVENTION.md](docs/ROLE_DRIFT_PREVENTION.md)** - How role enforcement works
- **[docs/INVESTIGATION_WORKFLOW.md](docs/INVESTIGATION_WORKFLOW.md)** - Investigation loop workflow diagrams
- **[docs/DOCS_INDEX.md](docs/DOCS_INDEX.md)** - Complete documentation index

---

## Troubleshooting

### Common Issues

**Q: Workflow seems slow**
A: Check testing mode (`/bazinga.configure-testing`). Use minimal mode for faster iteration.

**Q: Skills not running**
A: Check if tools are installed. BAZINGA will warn if tools are missing. Install with:
```bash
# Python
pip install bandit ruff pytest-cov

# JavaScript
npm install --save-dev jest eslint

# Go
go install github.com/securego/gosec/v2/cmd/gosec@latest
```

**Q: Want to disable a specific skill**
A: Run `/bazinga.configure-skills` and deselect skills you don't want.

**Q: Tasks not running in parallel**
A: PM may have detected dependencies or high file overlap. Check PM's reasoning in output.

**Q: Build failing**
A: Check `bazinga/build_baseline.log`. BAZINGA tracks baseline vs. final build status.

---

## Project Structure

```
your-project/
├── .claude/
│   ├── agents/                # Agent definitions (9 agents)
│   ├── commands/              # Slash commands
│   └── skills/                # Analysis tools (10+ Skills)
├── bazinga/
│   ├── bazinga.db            # SQLite database (sessions, tasks, logs)
│   ├── project_context.json  # Tech stack detection output
│   ├── model_selection.json  # Agent model configuration
│   ├── skills_config.json    # Agent skills configuration
│   ├── challenge_levels.json # QA test progression config
│   └── templates/            # Specialization templates
├── .claude.md                 # Global configuration
└── .git/                      # Git repository
```

---

## Quality Outcomes

**What every BAZINGA session delivers:**

| Quality Gate | What It Ensures |
|--------------|-----------------|
| Security Scan | No SQL injection, XSS, hardcoded secrets, auth vulnerabilities |
| Lint Check | Code meets style standards, no complexity violations |
| Test Coverage | 80%+ coverage target, untested paths flagged |
| Code Review | Architecture alignment, edge cases covered, security verified |
| Audit Trail | Full log of decisions, findings, and reasoning |

**Engineering principles enforced:**
- Writers don't review their own code (separation of concerns)
- Security scanning cannot be skipped
- Test coverage is measured, not assumed
- All decisions logged for traceability

---

## Contributing

We welcome contributions! Areas for improvement:
- Additional language support (Rust, C#, etc.)
- New Skills for analysis
- Performance optimizations
- Documentation improvements
- Bug fixes

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## Development Status

**Stable:**
- ✅ Core orchestration workflow
- ✅ Adaptive parallelism (1-4 developers)
- ✅ 3-tier problem-solving (standard/frameworks/investigation)
- ✅ Investigator agent with systematic root cause analysis
- ✅ 6 problem-solving frameworks (Root Cause, Architecture, Performance, Flaky Tests, Security, Investigation)
- ✅ Investigation loop management (max 5 iterations)
- ✅ Role drift prevention
- ✅ Core Skills (security, lint, coverage, codebase-analysis, pattern-miner)
- ✅ Model escalation
- ✅ Multi-language support (Python, JS, Go, Java, Ruby)

**Advanced (opt-in):**
- ⚡ Velocity tracking and PM metrics
- ⚡ Quality dashboards
- ⚡ API contract validation
- ⚡ Database migration safety checks
- ⚡ Test pattern analysis

**Experimental (early development):**
- ⚠️ Real-time Dashboard - Visual monitoring interface for orchestration sessions
  - Under active initial development and not yet reliable
  - Provides reporting/monitoring only - no impact on BAZINGA core functionality
  - Not installed by default; opt-in with `--dashboard`:
    ```bash
    bazinga init my-project --dashboard   # new project
    bazinga init --here --dashboard       # existing directory
    bazinga setup-dashboard               # install later
    ```

---

## Support & Getting Help

1. **Check documentation:** [docs/DOCS_INDEX.md](docs/DOCS_INDEX.md)
2. **Review examples:** [examples/EXAMPLES.md](examples/EXAMPLES.md)
3. **Search issues:** https://github.com/mehdic/bazinga/issues
4. **Open new issue:** Include version, language, and logs

---

## License

MIT License - Feel free to use and adapt for your projects.

See [LICENSE](LICENSE) for full details.

---

## Acknowledgments

Built for Claude Code using the Claude Agent SDK.

Special thanks to:
- Claude Code team for the Skills system and agent SDK
- Early adopters who provided feedback and bug reports
- Open source security/lint/coverage tool maintainers

---

**Version:** 1.1.0
**Last Updated:** 2025-12-30
**Created by:** [@mehdic](https://github.com/mehdic)

---

## Quick Links

- 🚀 **[Get Started](#quick-start)** - Install and run your first orchestration
- 🔒 **[Quality Gates](#automatic-quality-gates)** - Security, lint, coverage details
- 📚 **[Examples](examples/EXAMPLES.md)** - See real usage patterns
- 🏗️ **[Architecture](docs/ARCHITECTURE.md)** - How it works under the hood
- 🐛 **[Issues](https://github.com/mehdic/bazinga/issues)** - Report bugs or request features

---

**Philosophy:** AI-generated code should meet the same engineering standards as human-written code. Security scanning, code review, test coverage—these practices exist for good reasons. BAZINGA enforces them automatically, every time, no exceptions.
