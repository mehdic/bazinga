# BAZINGA Skills: Granular Analysis Configuration

BAZINGA uses **Claude Code Skills** to provide agents with specialized analysis tools. This document explains what each Skill does, when to use it, and how to configure which ones run during orchestration.

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Available Skills](#available-skills)
4. [Configuration Presets](#configuration-presets)
5. [Language Support](#language-support)
6. [Advanced Configuration](#advanced-configuration)

---

## Overview

### What Are Skills?

Skills are automated analysis tools that agents invoke to validate code quality, security, test coverage, and project metrics. They return structured JSON results that inform decision-making.

**Key Points:**
- Skills run automatically during agent workflows
- Each Skill focuses on a specific problem
- Results are saved to `bazinga/` for agent access
- Skills can be enabled or disabled based on your workflow

**💡 Profiles:** BAZINGA has two main modes:
- **Lite** (default) - 3 core skills, fast iteration (~1-2 min overhead)
- **Advanced** - All 10 skills, comprehensive analysis (~3-5 min overhead)

### Why Configure Skills?

**Different Workflows Need Different Tools:**

| Scenario | Lite Mode | Advanced Mode | Custom |
|----------|-----------|---------------|--------|
| **Rapid Iteration** | ✅ Perfect | ❌ Too slow | ✅ Maybe |
| **Critical Features** | ⚠️ Basic | ✅ Comprehensive | ✅ Maybe |
| **Database Work** | ⚠️ Missing | ✅ Good | ✅ db-migration-check |
| **API Changes** | ⚠️ Missing | ✅ Good | ✅ api-contract-validation |

**Time Investment:**

- **Lite Mode (default)**: 1-2 minute overhead (security, linting, coverage)
- **Advanced Mode**: 3-5 minute overhead (adds pattern analysis, deeper insights)
- **Custom Mode**: You decide what's worth the time

---

## Quick Start

### Using /bazinga.configure-skills Command

Open the interactive configuration menu:

```bash
/bazinga.configure-skills
```

This displays all 11 Skills grouped by agent with current status:

```
🎯 BAZINGA Skills Configuration

┌─────────────────────────────────────────────────────────────┐
│ 🔧 Developer Agent                                          │
├─────┬───────────────────────────────┬──────────┬────────────┤
│  1  │ lint-check                    │ 5-10s    │ ✅ ON      │
│  2  │ codebase-analysis             │ 15-30s   │ ⚪ OFF     │
│  3  │ test-pattern-analysis         │ 20-40s   │ ⚪ OFF     │
│  4  │ api-contract-validation       │ 10-20s   │ ⚪ OFF     │
│  5  │ db-migration-check            │ 10-15s   │ ⚪ OFF     │
└─────┴───────────────────────────────┴──────────┴────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 🛡️ Tech Lead Agent                                          │
├─────┬───────────────────────────────┬──────────┬────────────┤
│  6  │ security-scan                 │ 5-60s    │ ✅ ON      │
│  7  │ lint-check                    │ 5-10s    │ ✅ ON      │
│  8  │ test-coverage                 │ 10-20s   │ ✅ ON      │
└─────┴───────────────────────────────┴──────────┴────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 🧪 QA Expert Agent                                          │
├─────┬───────────────────────────────┬──────────┬────────────┤
│  9  │ pattern-miner                 │ 15-20s   │ ⚪ OFF     │
│ 10  │ quality-dashboard             │ 10-15s   │ ⚪ OFF     │
└─────┴───────────────────────────────┴──────────┴────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 📊 Project Manager Agent                                    │
├─────┬───────────────────────────────┬──────────┬────────────┤
│ 11  │ velocity-tracker              │ 5-10s    │ ✅ ON      │
└─────┴───────────────────────────────┴──────────┴────────────┘

💡 Smart Input Options:

Numbers (enable by default):
  2 3 9           → Turn on Skills #2, #3, #9
  enable 2 3 9    → Same (enable is default)
  disable 1 7     → Turn off Skills #1, #7

Presets:
  lite            → Lite profile (1,6,7,8 ON) - default, fast iteration
  advanced        → Advanced profile (all 10 skills ON)
  defaults        → Same as lite (recommended)
  none            → Disable all Skills

Examples:
  "2 3 9"                    → Enable codebase-analysis, test-pattern, pattern-miner
  "disable 6"                → Turn off security-scan
  "advanced"                 → Enable all advanced Skills
  "lite"                     → Reset to lite profile for fast iteration
```

### Configuration Examples

**For rapid iteration (1-2 min overhead):**
```bash
/bazinga.configure-skills
> lite
```

**For critical features (3-5 min overhead):**
```bash
/bazinga.configure-skills
> advanced
```

**Custom: Enable pattern analysis and quality dashboard:**
```bash
/bazinga.configure-skills
> 2 9 10
```

**Custom: Disable security scanning for trusted code:**
```bash
/bazinga.configure-skills
> disable 6
```

---

## Available Skills

### Core Skills (Lite Profile - Default)

These three Skills are enabled by default in lite mode and run automatically:

#### 1. **lint-check** (Developer & Tech Lead)
- **Problem**: Code quality issues go unnoticed
- **What it does**: Runs language-specific linters to find style violations, complexity issues, and anti-patterns
- **Time**: 5-10 seconds
- **When to use**: On every code review (enabled by default)
- **Output**: `bazinga/lint_results.json`

**Example output:**
```json
{
  "status": "success",
  "tool": "ruff",
  "issues": [
    {"file": "src/auth.py", "line": 45, "code": "E501", "message": "Line too long (120 > 88)", "severity": "warning"},
    {"file": "src/auth.py", "line": 32, "code": "F841", "message": "Unused variable 'token'", "severity": "error"}
  ],
  "summary": {"total": 2, "errors": 1, "warnings": 1}
}
```

**Language Support:**
- Python: ruff, pylint
- JavaScript: eslint
- Go: golangci-lint
- Java: Checkstyle, PMD
- Ruby: rubocop

---

#### 2. **security-scan** (Tech Lead only)
- **Problem**: Security vulnerabilities slip into production
- **What it does**: Scans code for SQL injection, XSS, hardcoded secrets, insecure dependencies
- **Time**: 5-10s (basic) or 30-60s (advanced)
- **Dual Mode**:
  - **Basic** (revision < 2): Fast scan, high/medium severity only
  - **Advanced** (revision >= 2): Comprehensive scan, all severities
- **When to use**: Before approving any code (enabled by default)
- **Output**: `bazinga/security_scan.json`

**Example output (basic mode):**
```json
{
  "status": "vulnerabilities_found",
  "mode": "basic",
  "tool": "bandit+semgrep",
  "vulnerabilities": [
    {
      "type": "hardcoded_secret",
      "severity": "high",
      "file": "config.py",
      "line": 12,
      "message": "Hardcoded password found",
      "suggestion": "Use environment variables"
    }
  ]
}
```

**Language Support:**
- Python: bandit, semgrep
- JavaScript: npm audit, eslint-plugin-security
- Go: gosec
- Ruby: brakeman
- Java: SpotBugs + OWASP Find Bugs

---

#### 3. **test-coverage** (Tech Lead only)
- **Problem**: Tests don't cover critical code paths
- **What it does**: Measures line and branch coverage, identifies untested code
- **Time**: 10-20 seconds
- **When to use**: After developers add/fix tests (enabled by default)
- **Output**: `bazinga/coverage_report.json`

**Example output:**
```json
{
  "status": "success",
  "tool": "pytest-cov",
  "summary": {
    "line_coverage": 82.5,
    "branch_coverage": 75.0,
    "files": [
      {"file": "src/auth.py", "coverage": 95, "status": "excellent"},
      {"file": "src/db.py", "coverage": 68, "status": "low", "untested_lines": "45-67"}
    ]
  },
  "coverage_trend": {"previous": 78.0, "current": 82.5, "direction": "improving"}
}
```

**Language Support:**
- Python: pytest-cov
- JavaScript: Jest
- Go: go test -cover
- Java: JaCoCo

---

### Advanced Skills (Opt-in)

These Skills are disabled by default but provide deeper analysis. Enable them for:
- Critical features
- Complex architectures
- Production deployments
- Knowledge building

#### 5. **codebase-analysis** (Developer)
- **Problem**: Developers reinvent the wheel instead of reusing existing patterns
- **What it does**: Finds similar features, reusable utilities, and architectural patterns
- **Time**: 15-30 seconds
- **When to use**: At start of complex features to understand existing solutions
- **Output**: `bazinga/codebase_patterns.json`

**Problem it solves:**
```
Developer writes: New "user registration" endpoint
Codebase has: 3 similar endpoints (login, password_reset, oauth)
Developer never looked at them

Result: Duplicated code, inconsistent patterns, extra bugs
```

**Example output:**
```json
{
  "task": "Implement password reset endpoint",
  "similar_features": [
    {
      "file": "api/user_registration.py",
      "similarity": 0.85,
      "patterns": ["email validation", "token generation", "service layer"],
      "key_functions": ["generate_token()", "send_email()"]
    }
  ],
  "reusable_utilities": [
    {"name": "EmailService", "file": "utils/email.py"},
    {"name": "TokenGenerator", "file": "utils/tokens.py"}
  ],
  "architectural_patterns": ["service layer", "repository pattern"]
}
```

**Enable when:** Starting work on feature similar to existing ones

---

#### 6. **test-pattern-analysis** (Developer)
- **Problem**: Tests are inconsistent - different fixtures, naming, styles
- **What it does**: Extracts test framework, fixtures, naming conventions, helper utilities
- **Time**: 15-30 seconds
- **When to use**: Before writing new tests
- **Output**: `bazinga/test_patterns.json`

**Problem it solves:**
```
Existing tests: Use pytest fixtures and context managers
Developer writes: Tests with manual setup/teardown

Result: Tests are harder to maintain, patterns not consistent
```

**Example output:**
```json
{
  "framework": "pytest",
  "common_fixtures": [
    {"name": "db", "scope": "session", "usage_count": 25},
    {"name": "auth_user", "scope": "function", "usage_count": 12}
  ],
  "naming_patterns": ["test_<function>_<scenario>"],
  "helper_functions": ["setup_test_db()", "create_user()"]
}
```

**Enable when:** Writing tests for new features

---

#### 7. **api-contract-validation** (Developer)
- **Problem**: API changes break clients without anyone noticing
- **What it does**: Compares OpenAPI specs, detects breaking changes (removed endpoints, changed types)
- **Time**: 10-20 seconds
- **When to use**: Before deploying API changes
- **Output**: `bazinga/contract_diff.json`

**Problem it solves:**
```
Developer removes "deprecated" field from API response
Client app expected that field → BREAKS

Result: Angry users, production incident, expensive fix
```

**Example output:**
```json
{
  "status": "breaking_changes_detected",
  "breaking_changes": [
    {
      "endpoint": "GET /users/{id}",
      "change": "Field removed",
      "field": "deprecated",
      "severity": "high",
      "impact": "Clients depending on this field will crash"
    }
  ],
  "safe_changes": [
    {
      "endpoint": "POST /users",
      "change": "Optional field added",
      "field": "metadata",
      "impact": "Backward compatible"
    }
  ]
}
```

**Enable when:** Modifying API contracts (REST, GraphQL, gRPC)

---

#### 8. **db-migration-check** (Developer)
- **Problem**: Database migrations cause downtime or data loss
- **What it does**: Detects dangerous operations (locks, rewrites) and suggests safe alternatives
- **Time**: 10-20 seconds
- **When to use**: Before deploying migrations
- **Output**: `bazinga/migration_analysis.json`

**Problem it solves:**
```
Migration: ALTER TABLE users ADD COLUMN email DEFAULT NULL
Database: 1 million rows
Result: Table locked for 30 minutes → DOWNTIME

Safe alternative: Add column without lock, then backfill
```

**Example output:**
```json
{
  "status": "dangerous_operations_detected",
  "database": "postgresql",
  "dangerous_operations": [
    {
      "operation": "ALTER COLUMN TYPE",
      "file": "migrations/001_change_email_type.sql",
      "danger": "Table rewrite on 500K rows, estimated 2 minutes lock time",
      "safe_alternative": "Use NOT VALID constraint to add during low-traffic period"
    }
  ],
  "safe_operations": [
    {
      "operation": "CREATE INDEX CONCURRENTLY",
      "status": "safe",
      "reason": "Uses CONCURRENTLY flag, no table lock"
    }
  ]
}
```

**Supported Databases:**
- PostgreSQL (most detailed checks)
- MySQL (online DDL detection)
- SQL Server (online index creation)
- MongoDB (background index creation)
- SQLite, Oracle (also supported)

**Enable when:** Adding/modifying database migrations

---

#### 9. **pattern-miner** (QA Expert)
- **Problem**: Team keeps making the same mistakes, estimates never improve
- **What it does**: Mines historical data to identify recurring patterns, predict effort, detect risks
- **Time**: 15-20 seconds
- **When to use**: For retrospectives and historical learning
- **Output**: `bazinga/pattern_insights.json`

**Problem it solves:**
```
Run 1: Database tasks estimated 4 hours, took 10 hours
Run 2: Database tasks estimated 4 hours again, took 10 hours again
Run 3: ... same thing

Better: Analyze patterns → "Database tasks always 2.5x estimate"
Next estimate: 10 hours → Set expectation correctly
```

**Example output:**
```json
{
  "patterns": [
    {
      "pattern": "Database tasks take 2.5x initial estimate",
      "confidence": 0.85,
      "samples": 8,
      "impact": "Affects 15-20% of tasks"
    }
  ],
  "risk_predictions": [
    {
      "risk": "Payment module has high revision rate (80%)",
      "probability": 0.75,
      "recommendation": "Allow extra review cycles for payment features"
    }
  ],
  "recommendations": [
    "Budget 2.5x for any database work",
    "Flag payment module changes for extra review"
  ]
}
```

**Enable when:** You want data-driven estimation and historical learning

---

#### 10. **quality-dashboard** (QA Expert) ⭐
- **Problem**: No single view of project health - security good, coverage bad, velocity declining
- **What it does**: Aggregates all quality metrics (security, coverage, lint, velocity) into one health score
- **Time**: 10-15 seconds
- **When to use**: Before major decisions, before BAZINGA, weekly reviews
- **Output**: `bazinga/quality_dashboard.json`

**Problem it solves:**
```
Tech Lead: "Security looks good"
PM: "Coverage is trending down"
Developer: "Linting is clean"
User: "Can I ship this?" → No clear answer

Better: Quality dashboard says "Health: 72/100 (yellow), declining 5% per week"
Clear signal: Fix coverage before shipping
```

**Example output:**
```json
{
  "overall_health_score": 78,
  "health_level": "good",
  "metrics": {
    "security": {"score": 95, "trend": "stable", "status": "excellent"},
    "coverage": {"score": 82, "trend": "declining", "status": "good"},
    "lint": {"score": 70, "trend": "improving", "status": "fair"},
    "velocity": {"score": 65, "trend": "declining", "status": "warning"}
  },
  "anomalies": [
    {"type": "coverage_decline", "value": -5.2, "message": "Coverage dropped 5.2% this week"}
  ],
  "recommendations": [
    "Focus on test coverage - down 5% this week",
    "Investigate velocity decline - might indicate architectural issues"
  ]
}
```

**Enable when:** You want a comprehensive health view before major decisions

---

## Configuration Presets

### Preset: "lite" or "defaults"

**When to use:** Daily development, rapid iteration, tight deadlines

**What's enabled:**
- ✅ #1 Developer lint-check (5-10s)
- ✅ #6 Tech Lead security-scan (basic mode, 5-10s)
- ✅ #7 Tech Lead lint-check (5-10s)
- ✅ #8 Tech Lead test-coverage (10-20s)

**What's disabled:**
- ⚪ All 7 advanced Skills (including velocity-tracker)

**Total time**: 1-2 minutes overhead per orchestration run

**Best for:**
- Fixing bugs
- Small features
- Rapid iteration
- Cost optimization

**Example:**
```bash
/bazinga.configure-skills
> lite
```

---

### Preset: "advanced"

**When to use:** Critical features, production work, knowledge building

**What's enabled:**
- ✅ All lite Skills (1, 6, 7, 8)
- ✅ #2 Developer codebase-analysis (15-30s)
- ✅ #3 Developer test-pattern-analysis (15-30s)
- ✅ #4 Developer api-contract-validation (10-20s)
- ✅ #5 Developer db-migration-check (10-20s)
- ✅ #9 QA Expert pattern-miner (15-20s)
- ✅ #10 QA Expert quality-dashboard (10-15s)
- ✅ #11 PM velocity-tracker (5-10s)

**Total time**: 3-5 minutes overhead per orchestration run

**Best for:**
- Critical features
- API changes
- Database work
- Large refactorings
- Before production deployment

**Example:**
```bash
/bazinga.configure-skills
> advanced
```

---

### Preset: "none"

**When to use:** Testing, debugging, emergency mode (not recommended)

**Disables all Skills** - agents run without automated analysis

**Best for:**
- Troubleshooting agent behavior
- Minimal overhead (dangerous!)
- Testing only

**Not recommended** for real work - turns off all safety checks.

---

### Custom Configuration

**When to use:** Your workflow needs specific Skills

**Examples:**

**For API-heavy work:**
```bash
/bazinga.configure-skills
> 1 4 6 7 8 11
# Enable: lint, api-contract-validation, security, lint, coverage, velocity
```

**For database work:**
```bash
/bazinga.configure-skills
> 1 5 6 7 8 11
# Enable: lint, db-migration-check, security, lint, coverage, velocity
```

**For rapid iteration with coverage focus:**
```bash
/bazinga.configure-skills
> 1 8 11
# Enable: lint (dev), test-coverage, velocity
# Fast: skip all advanced analysis
```

**For learning/knowledge building:**
```bash
/bazinga.configure-skills
> 2 3 9 10
# Enable: codebase-analysis, test-pattern-analysis, pattern-miner, quality-dashboard
# Skip: lint, security, coverage (focus on patterns and insights)
```

---

## Language Support

### Python

| Skill | Tool(s) | Detection |
|-------|---------|-----------|
| **lint-check** | ruff (fast) or pylint (comprehensive) | PEP 8, complexity, best practices |
| **security-scan** | bandit, semgrep | SQL injection, hardcoded secrets, etc. |
| **test-coverage** | pytest-cov | Line and branch coverage |
| **codebase-analysis** | AST parsing | Patterns, utilities, architecture |
| **test-pattern-analysis** | AST parsing | Fixtures, patterns, helpers |
| **db-migration-check** | SQL parsing | Alembic, raw SQL migrations |

**Project detection:** `pyproject.toml`, `setup.py`, `requirements.txt`

---

### JavaScript/TypeScript

| Skill | Tool(s) | Detection |
|-------|---------|-----------|
| **lint-check** | eslint | Style, potential bugs, best practices |
| **security-scan** | npm audit, eslint security plugin | Dependency vulnerabilities, XSS |
| **test-coverage** | Jest, Istanbul format | Line, branch, function coverage |
| **codebase-analysis** | AST parsing | Patterns, utilities, components |
| **test-pattern-analysis** | AST parsing | Test frameworks, mocks, patterns |
| **api-contract-validation** | OpenAPI/Swagger parsing | Breaking changes in specs |

**Project detection:** `package.json`, `.eslintrc`, `jest.config.js`

---

### Go

| Skill | Tool(s) | Detection |
|-------|---------|-----------|
| **lint-check** | golangci-lint | Style, complexity, best practices |
| **security-scan** | gosec | SQL injection, hardcoded secrets |
| **test-coverage** | go test -cover | Package and function coverage |
| **codebase-analysis** | AST parsing | Patterns, interfaces, packages |
| **test-pattern-analysis** | AST parsing | Test patterns, table-driven tests |
| **db-migration-check** | SQL parsing | Database/sql migrations |

**Project detection:** `go.mod`, `go.sum`

---

### Java

| Skill | Tool(s) | Detection |
|-------|---------|-----------|
| **lint-check** | Checkstyle, PMD | Style, complexity, anti-patterns |
| **security-scan** | SpotBugs, OWASP Find Bugs | Vulnerabilities, insecure patterns |
| **test-coverage** | JaCoCo | Line and branch coverage |
| **codebase-analysis** | AST parsing | Design patterns, layers, interfaces |
| **test-pattern-analysis** | AST parsing | JUnit patterns, fixtures, helpers |
| **db-migration-check** | SQL parsing | Flyway, Liquibase migrations |

**Project detection:** `pom.xml`, `build.gradle`, `build.gradle.kts`

---

### Ruby

| Skill | Tool(s) | Detection |
|-------|---------|-----------|
| **lint-check** | rubocop | Style, complexity, best practices |
| **security-scan** | brakeman | SQL injection, XSS, hardcoded secrets |
| **test-coverage** | SimpleCov | Line coverage reporting |
| **codebase-analysis** | AST parsing | Patterns, utilities, mixins |
| **test-pattern-analysis** | AST parsing | RSpec patterns, fixtures, helpers |
| **db-migration-check** | SQL parsing | Rails, raw SQL migrations |

**Project detection:** `Gemfile`, `Rakefile`, `config/rails_env.rb`

---

## Advanced Configuration

### Skills Configuration File

Configuration is persisted in `bazinga/skills_config.json`:

```json
{
  "developer": {
    "lint-check": "mandatory",
    "codebase-analysis": "disabled",
    "test-pattern-analysis": "disabled",
    "api-contract-validation": "disabled",
    "db-migration-check": "disabled"
  },
  "tech_lead": {
    "security-scan": "mandatory",
    "lint-check": "mandatory",
    "test-coverage": "mandatory"
  },
  "qa_expert": {
    "pattern-miner": "disabled",
    "quality-dashboard": "disabled"
  },
  "pm": {
    "velocity-tracker": "mandatory"
  },
  "_metadata": {
    "description": "Skills configuration for BAZINGA agents",
    "last_updated": "2025-01-08T14:30:00Z",
    "configuration_notes": [
      "MANDATORY: Skill will be automatically invoked by the agent",
      "DISABLED: Skill will not be invoked",
      "Use /bazinga.configure-skills to modify this configuration interactively"
    ]
  }
}
```

**Values:**
- `"mandatory"` - Agent will always invoke this Skill
- `"disabled"` - Agent will skip this Skill

### How Agents Use Skills Configuration

**Developer Agent:**
- Checks `skills_config.json` at start of implementation
- If Skill is "mandatory", invokes it automatically
- If Skill is "disabled", skips it
- Reports results in response

**Tech Lead Agent:**
- Checks `skills_config.json` during code review
- Invokes mandatory Skills in this order: security-scan → lint-check → test-coverage
- Uses results to inform review decisions
- Reports findings to PM

**QA Expert Agent:**
- Checks `skills_config.json` before/during testing
- Invokes mandatory Skills as needed
- Uses pattern-miner for test strategy insights
- Uses quality-dashboard for health assessment

**PM Agent:**
- Always invokes velocity-tracker (mandatory)
- Uses results for progress tracking and decision-making
- May invoke pattern-miner for retrospectives

### Skill Invocation Examples

**Example: Developer with default configuration**

```
Developer receives task: "Add JWT authentication"

1. Check skills_config.json
   - lint-check: mandatory → WILL RUN
   - codebase-analysis: disabled → SKIP
   - test-pattern-analysis: disabled → SKIP
   - etc.

2. Implement code

3. Invoke mandatory Skills:
   /lint-check
   Result: 3 issues found (complexity, unused import)

4. Fix issues

5. Report to orchestrator with Skills results attached
```

**Example: Tech Lead with advanced configuration**

```
Tech Lead receives code for review

1. Check skills_config.json
   - security-scan: mandatory → WILL RUN
   - lint-check: mandatory → WILL RUN
   - test-coverage: mandatory → WILL RUN

2. Invoke Skills in sequence:
   /security-scan
   Result: No vulnerabilities, status: success

   /lint-check
   Result: 2 style issues in new code

   /test-coverage
   Result: 85% coverage, excellent

3. Synthesize results:
   - Security: ✅ Clear
   - Style: ⚠️ Minor issues (fix before merge)
   - Coverage: ✅ Good

4. Decision: APPROVED with minor fixes
```

### Persistence Across Sessions

- Configuration is **automatically saved** to `bazinga/skills_config.json`
- Configuration **persists across all BAZINGA sessions**
- Use `/bazinga.configure-skills` anytime to adjust
- Configuration is **tracked in git** (safe to commit)

---

## Benefits of Each Mode

### Lite Mode (Default)

**Overhead:** 1-2 minutes per orchestration run

**Pros:**
- Suitable for rapid iteration and tight deadlines
- Essential quality checks without time burden
- Cost-effective (minimal compute)
- Good for small features and bug fixes

**Cons:**
- Misses architectural patterns
- No historical learning
- Can't detect breaking API changes
- Weak for database work

**Best for:**
- Bug fixes (✅)
- Small features (✅)
- Rapid iteration (✅)
- CI/CD pipelines (✅)

---

### Advanced Mode (All Skills)

**Overhead:** 3-5 minutes per orchestration run

**Pros:**
- Comprehensive analysis across all dimensions
- Detects architectural issues early
- API contract safety
- Database migration safety
- Historical learning and pattern detection
- Complete project health visibility
- PM velocity tracking

**Cons:**
- Slower (3-5 min overhead)
- More expensive (more analysis)
- Overkill for small changes

**Best for:**
- Critical features (✅)
- API changes (✅)
- Database migrations (✅)
- Production work (✅)
- Large refactorings (✅)
- Knowledge building (✅)

---

### Custom Configuration

**Overhead:** Depends on your choices (1-5 minutes)

**When to use:**
- Your workflow is somewhere between fast and advanced
- You need specific Skills but not all
- You want to optimize for your team's needs

**Examples:**

**API-heavy team:**
```
Enable: lint, security, coverage, api-contract-validation, velocity
Disable: database checks, pattern analysis
Time: 2-3 minutes
```

**Database-heavy team:**
```
Enable: lint, security, coverage, db-migration-check, velocity
Disable: api-contract, pattern analysis
Time: 2-3 minutes
```

**Knowledge-building team:**
```
Enable: codebase-analysis, test-pattern-analysis, pattern-miner, quality-dashboard
Disable: lint, security, coverage (first priority on patterns/insights)
Time: 1 minute (skip basic checks)
```

---

## Troubleshooting

### "Skill X timed out"

**Cause:** Skill took longer than expected (usually on large codebases)

**Solutions:**
- Disable Skills you don't need
- Use "fast" preset for large codebases
- Check if your codebase has performance issues (too many files, deep nesting)

### "Skill returned error status"

**Cause:** Required tool not installed or misconfigured

**Solution:** BAZINGA CLI automatically detects and offers to install missing tools:
```bash
# During init or first use
bazinga check
# Shows: "python: ruff not found. Install? (y/n)"
```

### "Configuration not applied"

**Cause:** Skills file not found or malformed

**Solution:**
```bash
# Verify configuration exists
cat bazinga/skills_config.json

# Reset to defaults
/bazinga.configure-skills
> defaults

# Re-run orchestration
```

### "I want to compare before/after"

**Enable different configurations:**

1. Run with Fast configuration
2. Note results in `bazinga/` files
3. Change to Advanced configuration
4. Run again and compare

This helps you decide what Skills are worth the time for your workflow.

---

## Next Steps

- **Quick start**: Run `/bazinga.configure-skills` and select a preset
- **Learn more**: See agent documentation (`agents/developer.md`, `agents/tech_lead.md`, etc.)
- **Integration**: See how orchestrator uses Skills in `agents/orchestrator.md`
- **Examples**: See `examples/EXAMPLES.md` for real workflow examples

---

## Development Status

**⚠️ Note:** BAZINGA Skills are currently under active development. While the Skills listed in this document are functional and tested, we are continuously improving:

- Detection accuracy and coverage
- Performance and execution speed
- Language support and tool integrations
- Output quality and actionability

We welcome feedback and bug reports as you use these Skills in your workflows. Please report issues at the project repository.

