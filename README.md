# BAZINGA - Parallel AI Development Teams for Claude Code

> **Repository:** https://github.com/mehdic/bazinga

**One request → Multiple AI developers working simultaneously → Done 3x faster.**

BAZINGA coordinates teams of AI agents to build software in parallel. While traditional AI coding assistants work sequentially, BAZINGA analyzes your request, breaks it into independent tasks, and spawns multiple developers to work simultaneously—just like a real dev team.

---

## See It In Action

```bash
@orchestrator implement JWT authentication, user registration, and password reset
```

**What happens:**

```
PM: "Analyzing request... 3 independent features detected"
PM: "Spawning 3 developers in parallel"

┌─────────────────────┬─────────────────────┬─────────────────────┐
│  Developer 1 (JWT)  │  Developer 2 (Reg)  │  Developer 3 (Pwd)  │
├─────────────────────┼─────────────────────┼─────────────────────┤
│ ✓ Implementation    │ ✓ Implementation    │ ✓ Implementation    │
│ ✓ Unit tests        │ ✓ Unit tests        │ ✓ Unit tests        │
│ ✓ Security scan     │ ✓ Security scan     │ ✓ Security scan     │
│ ✓ Lint check        │ ✓ Lint check        │ ✓ Lint check        │
│ ✓ Coverage check    │ ✓ Coverage check    │ ✓ Coverage check    │
│ ✓ Code review       │ ✓ Code review       │ ✓ Code review       │
└─────────────────────┴─────────────────────┴─────────────────────┘

PM: "BAZINGA! All features complete in 18 minutes"
    (Sequential would've taken 60 minutes)
```

**Result:** 3 features implemented, tested, security-scanned, and reviewed—all in parallel.

---

## Quick Start

```bash
# Install and initialize (one command)
uvx --from git+https://github.com/mehdic/bazinga.git bazinga init my-project

# Start building
cd my-project
@orchestrator implement user authentication with JWT
```

That's it. No configuration needed. BAZINGA automatically:
- ✅ Analyzes task complexity and independence
- ✅ Spawns 1-4 developers based on parallelization opportunities
- ✅ Runs security scans, lint checks, and test coverage
- ✅ Reviews code quality with Tech Lead
- ✅ Escalates to more powerful models (Opus) for difficult problems

---

## How It Works

### The Team

BAZINGA coordinates 5 specialized AI agents:

1. **Project Manager (PM)** - Analyzes requirements, breaks down work, decides parallelism
2. **Developers (1-4)** - Implement code in parallel, create tests, fix issues
3. **QA Expert** - Runs integration/contract/E2E tests (optional, advanced mode)
4. **Tech Lead** - Reviews code quality, security, architecture
5. **Orchestrator** - Routes messages between agents, maintains workflow

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
Tech Lead reviews all work
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
@orchestrator fix bug where users can't reset password
```

**Flow:** PM → 1 Developer → Tech Lead → BAZINGA
**Time:** ~5-10 minutes

### Multiple Features (Parallel Mode)

```bash
@orchestrator implement REST API with auth, user management, and admin endpoints
```

**Flow:** PM → 3 Developers (parallel) → Tech Lead reviews all → BAZINGA
**Time:** ~15-20 minutes (vs 45-60 sequential)

### Large Project

```bash
@orchestrator build a blog platform with posts, comments, tags, and search
```

**Flow:** PM → 4 Developers (parallel, 2 phases) → QA tests → Tech Lead → BAZINGA
**Time:** ~30-40 minutes (vs 2+ hours sequential)

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
- `security-scan` - Vulnerability detection
- `lint-check` - Code quality and style
- `test-coverage` - Coverage analysis

**Advanced Skills** (opt-in):
- `velocity-tracker` - PM metrics and velocity tracking
- `codebase-analysis` - Pattern extraction from similar code
- `test-pattern-analysis` - Test framework learning
- `api-contract-validation` - Breaking change detection
- `db-migration-check` - Migration safety analysis
- `pattern-miner` - Historical pattern analysis
- `quality-dashboard` - Unified health metrics

### CLI Options

```bash
# Default (lite profile)
bazinga init my-project

# Advanced profile (all features enabled)
bazinga init my-project --profile advanced

# Custom configuration
bazinga init my-project --testing full --skills all

# Update existing project
bazinga update
```

---

## What Makes BAZINGA Different

| Feature | BAZINGA | Claude Code (Default) | Other Frameworks |
|---------|---------|----------------------|------------------|
| **Parallel Developers** | ✅ 1-4 developers automatically | ❌ Single agent | ❌ Sequential only |
| **Adaptive Workflow** | ✅ PM decides parallelism | ❌ User coordinates | ❌ Fixed workflow |
| **Automatic Quality Gates** | ✅ Security, lint, coverage built-in | ❌ Manual invocation | ⚠️ Basic only |
| **Model Escalation** | ✅ Sonnet → Opus at revision 3 | ❌ Manual model selection | ❌ Single model |
| **Graceful Degradation** | ✅ Works with missing tools | ❌ N/A | ❌ Requires all tools |
| **Multi-language** | ✅ Python, JS, Go, Java, Ruby | ✅ Yes | ⚠️ Limited |

---

## Real Problems BAZINGA Solves

### Before BAZINGA

**Manual coordination:**
```
You: "@dev-agent implement auth"
You: "now @dev-agent implement user management"
You: "did I run security scan? let me check..."
You: "@security-agent run scan"
You: "@qa-agent test this"
You: "@review-agent review code"
You: "wait, did dev finish? let me check state files..."
```

**Result:** You're the project manager. Lots of context switching.

### After BAZINGA

```
You: "@orchestrator implement auth, user management, and admin dashboard"
```

**Result:** Done. PM handled everything. You stay in flow.

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
A: Check `coordination/build_baseline.log`. BAZINGA tracks baseline vs. final build status.

---

## Project Structure

```
your-project/
├── .claude/
│   ├── agents/                # Agent definitions (5 agents)
│   ├── commands/              # Slash commands
│   ├── scripts/               # Utility scripts
│   └── skills/                # Analysis tools (10 Skills)
├── coordination/              # State files (auto-generated, gitignored)
│   ├── pm_state.json         # PM planning and progress
│   ├── group_status.json     # Individual task status
│   ├── orchestrator_state.json # Routing state
│   ├── security_scan.json    # Security findings
│   ├── coverage_report.json  # Test coverage
│   ├── lint_results.json     # Code quality issues
│   └── testing_config.json   # Testing mode configuration
├── .claude.md                 # Global configuration
└── .git/                      # Git repository
```

---

## Performance

**Typical speedups with parallel mode:**

| Task Type | Sequential | BAZINGA Parallel | Speedup |
|-----------|-----------|------------------|---------|
| 2 independent features | 40 min | 15 min | 2.7x faster |
| 3 independent features | 60 min | 20 min | 3x faster |
| 4 independent modules | 90 min | 30 min | 3x faster |

**Limitations:**
- Max 4 developers (coordination overhead beyond 4)
- Features must be truly independent (low file overlap)
- Dependencies force sequential execution

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
- ✅ Role drift prevention
- ✅ Core Skills (security, lint, coverage)
- ✅ Model escalation
- ✅ Multi-language support (Python, JS, Go, Java, Ruby)

**Advanced (opt-in):**
- ⚡ Velocity tracking and PM metrics
- ⚡ Pattern mining and quality dashboards
- ⚡ API contract validation
- ⚡ Database migration safety checks

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

Built for Claude Code using the Claude Agent SDK. Inspired by ChatDev, MetaGPT, and other multi-agent frameworks but optimized specifically for Claude Code's capabilities.

Special thanks to:
- Claude Code team for the Skills system and agent SDK
- Early adopters who provided feedback and bug reports
- Open source security/lint/coverage tool maintainers

---

**Version:** 2.0.0
**Last Updated:** 2025-01-10
**Created by:** [@mehdic](https://github.com/mehdic)

---

## Quick Links

- 🚀 **[Get Started](# quick-start)** - Install and run your first orchestration
- 📚 **[Examples](examples/EXAMPLES.md)** - See real usage patterns
- ⚙️ **[Advanced Features](docs/ADVANCED.md)** - Unlock more power
- 🏗️ **[Architecture](docs/ARCHITECTURE.md)** - How it works under the hood
- 🐛 **[Issues](https://github.com/mehdic/bazinga/issues)** - Report bugs or request features

---

**Philosophy:** We built this to solve real problems we had. Parallel development with AI agents shouldn't require manual coordination. It should just work. If it helps you ship better software faster, we've succeeded.
