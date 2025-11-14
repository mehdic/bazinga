# BAZINGA Quick Reference

Quick command reference for BAZINGA orchestration.

---

## Installation

```bash
# One-time use (no installation)
uvx --from git+https://github.com/mehdic/bazinga.git bazinga init my-project

# Install as tool
uv tool install bazinga-cli --from git+https://github.com/mehdic/bazinga.git

# Or with pip
pip install git+https://github.com/mehdic/bazinga.git
```

---

## Initialization

```bash
# Create new project
bazinga init my-project

# Initialize in current directory
bazinga init --here
# or simply:
bazinga init

# With advanced profile
bazinga init my-project --profile advanced

# Custom configuration
bazinga init my-project --testing full --skills all
```

---

## Basic Workflow

### 1. Start Orchestration

```bash
/bazinga.orchestrate implement user authentication with JWT
# (or: @orchestrator implement user authentication with JWT)
```

### 2. What Happens

```
PM: Analyzes request → Spawns N developers (1-4) → Parallel implementation
                                                    ↓
                         Security scan + Lint check + Coverage (each dev)
                                                    ↓
                         Tech Lead reviews all work
                                                    ↓
                         PM confirms → BAZINGA!
```

### 3. Check Status

Project state is tracked in `bazinga/*.json` files:
- `pm_state.json` - Task groups, progress, iteration count
- `group_status.json` - Per-task status, revision counts
- `orchestrator_state.json` - Active agents, routing state

---

## Common Tasks

### Single Feature (Simple)

```bash
/bazinga.orchestrate fix password reset bug
```

**Flow:** PM → 1 Developer → Tech Lead → BAZINGA
**Time:** ~5-10 minutes

---

### Multiple Features (Parallel)

```bash
/bazinga.orchestrate implement JWT auth, user registration, and password reset
```

**Flow:** PM → 3 Developers (parallel) → Tech Lead → BAZINGA
**Time:** ~15-20 minutes (vs 45-60 sequential)

---

### Large Project

```bash
/bazinga.orchestrate build blog platform with posts, comments, tags, and search
```

**Flow:** PM → 4 Developers (parallel, 2 phases) → Tech Lead → BAZINGA
**Time:** ~30-40 minutes

---

## Configuration Commands

### Configure Skills

```bash
/bazinga.configure-skills
```

**Quick inputs:**
- `lite` - Core skills only (default)
- `advanced` - All 10 skills enabled
- `2 3 9` - Enable specific skills by number
- `enable 2, disable 7` - Mixed operations

---

### Configure Testing

```bash
/bazinga.configure-testing
```

**Options:**
- `minimal` - Lint + unit tests (default, 30-40% faster)
- `full` - All tests + QA Expert (production quality)
- `disabled` - Lint only (rapid prototyping, 40-60% faster)

---

## Profiles

| Profile | Skills | Testing | Use Case |
|---------|--------|---------|----------|
| **Lite** (default) | 3 core | Minimal | Fast iteration, most projects |
| **Advanced** | 10 skills | Full | Production-critical code |
| **Custom** | User-selected | User-configured | Fine-tuned workflows |

**Switch profiles:**
```bash
# During init
bazinga init --profile advanced

# Existing project
/bazinga.configure-skills
> Type: "advanced"
```

---

## Skills Reference

### Core Skills (Lite Profile)

| # | Skill | Agent | Time | Purpose |
|---|-------|-------|------|---------|
| 1 | lint-check | Developer | 5-10s | Code style and quality |
| 6 | security-scan | Tech Lead | 5-60s | Vulnerability detection |
| 7 | lint-check | Tech Lead | 5-10s | Final quality check |
| 8 | test-coverage | Tech Lead | 10-20s | Coverage analysis |

### Advanced Skills (Opt-in)

| # | Skill | Agent | Time | Purpose |
|---|-------|-------|------|---------|
| 2 | codebase-analysis | Developer | 15-30s | Find similar features |
| 3 | test-pattern-analysis | Developer | 20-40s | Learn test patterns |
| 4 | api-contract-validation | Developer | 10-20s | Detect API breaking changes |
| 5 | db-migration-check | Developer | 10-15s | Detect dangerous migrations |
| 9 | pattern-miner | QA Expert | 30-60s | Historical pattern analysis |
| 10 | quality-dashboard | QA Expert | 15-30s | Unified metrics |
| 11 | velocity-tracker | PM | 5-10s | PM metrics |

---

## Testing Modes

### Minimal (Default)

```json
{
  "mode": "minimal",
  "pre_commit_validation": {
    "lint_check": true,
    "unit_tests": true,
    "build_check": true
  },
  "qa_workflow": {
    "enable_qa_expert": false
  }
}
```

**Time:** ~15-20 min (3 features)
**What runs:** Lint + unit tests per developer, security scan, coverage check

---

### Full

```json
{
  "mode": "full",
  "test_requirements": {
    "require_integration_tests": true,
    "require_contract_tests": true,
    "coverage_threshold": 80
  },
  "qa_workflow": {
    "enable_qa_expert": true
  }
}
```

**Time:** ~30-40 min (3 features)
**What runs:** All of minimal + integration tests + E2E tests + QA Expert with pattern mining + quality dashboard

---

### Disabled

```json
{
  "mode": "disabled",
  "pre_commit_validation": {
    "lint_check": true,
    "unit_tests": false
  }
}
```

**Time:** ~10-15 min (3 features)
**What runs:** Lint checks only

---

## Agent Interactions

### The Team

1. **Orchestrator** - Routes messages, maintains workflow
2. **Project Manager** - Analyzes requirements, spawns developers, confirms completion
3. **Developer (1-4)** - Implements code, writes tests, fixes issues (parallel execution)
4. **QA Expert** - Runs integration/E2E tests (full mode only)
5. **Tech Lead** - Reviews code quality, security, architecture

### Routing

```
User → Orchestrator → PM
                      ↓
                PM spawns Developers (1-4 in parallel)
                      ↓
                Each Developer implements + tests
                      ↓
                Developer → Tech Lead (via Orchestrator)
                      ↓
                Tech Lead reviews all work
                      ↓
                If issues: Tech Lead → Developer (iteration)
                If approved: Tech Lead → PM
                      ↓
                PM confirms → BAZINGA!
```

**With QA Expert (full mode):**
```
Developers → QA Expert → Tech Lead → PM
```

---

## Model Escalation

BAZINGA automatically escalates to more powerful models when stuck:

| Revision | Model | Use Case |
|----------|-------|----------|
| 1-2 | Claude Sonnet | Fast, handles 90% of reviews |
| 3+ | Claude Opus | Deep analysis for persistent issues |

**Why:** Cost-effective (Sonnet for typical work), automatic (no manual switching), smart (Opus only when needed).

---

## File Structure

```
your-project/
├── .claude/
│   ├── agents/                # 5 agent definitions
│   ├── commands/              # Slash commands
│   ├── scripts/               # Utility scripts
│   └── skills/                # 10 Skills (analysis tools)
├── bazinga/              # State files (auto-generated)
│   ├── pm_state.json         # PM planning
│   ├── group_status.json     # Task status
│   ├── orchestrator_state.json # Routing state
│   ├── skills_config.json    # Skills configuration
│   ├── testing_config.json   # Testing mode
│   ├── security_scan.json    # Security findings
│   ├── coverage_report.json  # Coverage data
│   └── lint_results.json     # Lint issues
├── .claude.md                 # Global configuration
└── .git/                      # Git repository
```

**Note:** All `bazinga/*.json` files are gitignored except `skills_config.json` and `testing_config.json`.

---

## Examples

### Example 1: Authentication System

```bash
/bazinga.orchestrate implement authentication with JWT tokens, refresh tokens, and password reset
```

**PM Decision:** 3 independent tasks → 3 developers in parallel

**Result:**
- Developer 1: JWT authentication
- Developer 2: Refresh token logic
- Developer 3: Password reset flow

**Time:** ~18 minutes (vs ~60 sequential)

---

### Example 2: Bug Fix

```bash
/bazinga.orchestrate fix bug where users can't upload files larger than 10MB
```

**PM Decision:** 1 task → 1 developer

**Result:** Bug fixed, tests added, security scan passed

**Time:** ~8 minutes

---

### Example 3: Refactoring

```bash
/bazinga.orchestrate refactor database layer to use repository pattern
```

**PM Decision:** High file overlap → 1 developer (parallel risky)

**Result:** Refactored safely, all tests passing

**Time:** ~25 minutes

---

## Performance

### Typical Speedups (Parallel Mode)

| Task Type | Sequential | BAZINGA | Speedup |
|-----------|-----------|---------|---------|
| 2 independent features | 40 min | 15 min | 2.7x faster |
| 3 independent features | 60 min | 20 min | 3x faster |
| 4 independent modules | 90 min | 30 min | 3x faster |

**Limitations:**
- Max 4 developers (coordination overhead beyond 4)
- Features must be independent (low file overlap)
- Dependencies force sequential execution

---

## Troubleshooting

### Workflow Slow

**Check testing mode:**
```bash
/bazinga.configure-testing
> Select: "minimal"
```

### Skills Not Running

**Check skills config:**
```bash
/bazinga.configure-skills
```

### Tool Missing Warning

**Lite mode:** Warns but continues
**Advanced mode:** Fails (requires all tools)

**Install tools:**
```bash
# Python
pip install bandit ruff pytest-cov

# JavaScript
npm install --save-dev jest eslint

# Go
go install github.com/securego/gosec/v2/cmd/gosec@latest
```

### Tasks Not Running in Parallel

PM may have detected:
- Dependencies between tasks
- High file overlap
- Complexity makes parallel risky

Check PM's reasoning in `bazinga/pm_state.json`.

---

## CLI Options

```bash
# Initialize
bazinga init [PROJECT_NAME] [OPTIONS]

Options:
  --here                  Initialize in current directory
  --profile TEXT          Profile: lite (default), advanced, custom
  --testing TEXT          Testing mode: minimal (default), full, disabled
  --skills TEXT           Skills: lite, advanced, all
  --help                  Show help

# Update existing project
bazinga update
```

---

## Tips

### For Fast Iteration
- Use lite profile (default)
- Use minimal testing (default)
- Disable advanced skills

### For Production Code
- Use advanced profile
- Use full testing mode
- Enable all skills

### For Parallel Speedup
- Ensure tasks are independent
- Minimize file overlap
- Break large tasks into smaller independent units

---

## Support

- **Documentation:** [docs/DOCS_INDEX.md](DOCS_INDEX.md)
- **Advanced Features:** [docs/ADVANCED.md](ADVANCED.md)
- **Examples:** [examples/EXAMPLES.md](../examples/EXAMPLES.md)
- **Issues:** https://github.com/mehdic/bazinga/issues

---

**Version:** 2.0.0
**Last Updated:** 2025-01-10
