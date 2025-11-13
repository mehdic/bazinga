# BAZINGA Advanced Features

This guide covers advanced features for power users and production-critical projects.

**TL;DR:** BAZINGA defaults to "lite" mode for fast iteration. Use "advanced" mode when you need comprehensive analysis, full QA workflow, or production-critical guarantees.

---

## Table of Contents

- [Profiles Overview](#profiles-overview)
- [Advanced Skills](#advanced-skills)
- [Full Testing Mode](#full-testing-mode)
- [Configuration](#configuration)
- [Performance Considerations](#performance-considerations)
- [When to Use Advanced Mode](#when-to-use-advanced-mode)

---

## Profiles Overview

BAZINGA has three configuration profiles:

| Profile | Skills Active | Testing Mode | Use Case |
|---------|---------------|--------------|----------|
| **Lite** (default) | 3 core skills | Minimal (lint + unit tests) | Fast iteration, most projects |
| **Advanced** | All 10 skills | Full (all testing + QA Expert) | Production-critical, complex projects |
| **Custom** | User-selected | User-configured | Fine-tuned workflows |

### Switching Profiles

```bash
# Initialize with advanced profile
bazinga init my-project --profile advanced

# Configure existing project
/bazinga.configure-skills
> Type: "advanced"

# Testing mode
/bazinga.configure-testing
> Select: "full"
```

---

## Advanced Skills

Beyond the 3 core skills (security-scan, lint-check, test-coverage), BAZINGA includes 7 advanced skills for comprehensive analysis.

### Developer Skills

#### 1. Codebase Analysis
**What it does:** Finds similar features, reusable utilities, and architectural patterns before implementation.

**When it runs:** Before Developer starts coding (invoked by PM).

**Output:** `bazinga/codebase_analysis.json`

**Example output:**
```json
{
  "similar_features": [
    {
      "file": "src/auth/login.py",
      "similarity_score": 0.85,
      "patterns": ["service layer", "validation", "token generation"],
      "key_functions": ["LoginService", "validate_credentials", "generate_token"]
    }
  ],
  "reusable_utilities": [
    {"name": "EmailService", "file": "src/utils/email.py"},
    {"name": "TokenGenerator", "file": "src/auth/tokens.py"}
  ],
  "suggested_approach": "Create PasswordResetService in services/; use existing EmailService, TokenGenerator; follow patterns from src/auth/login.py"
}
```

**Dependencies:** None (pure Python pattern matching).

**Performance:** 15-30s depending on codebase size.

---

#### 2. Test Pattern Analysis
**What it does:** Analyzes existing test suite to learn patterns, fixtures, naming conventions, and utilities.

**When it runs:** After Developer writes code, before writing tests.

**Output:** `bazinga/test_patterns.json`

**Example output:**
```json
{
  "framework": "pytest",
  "version": "7.4.0",
  "common_fixtures": ["db_session", "auth_user", "mock_email"],
  "test_patterns": {
    "structure": "Arrange-Act-Assert",
    "naming": "test_<feature>_<scenario>_<expected>"
  },
  "suggested_tests": [
    "test_password_reset_valid_email_sends_token",
    "test_password_reset_invalid_email_returns_error",
    "test_password_reset_expired_token_raises_exception"
  ],
  "coverage_target": "80%"
}
```

**Dependencies:** Test framework installed (pytest, jest, go test, junit, rspec).

**Performance:** 20-40s depending on test suite size.

---

#### 3. API Contract Validation
**What it does:** Detects breaking changes in OpenAPI/Swagger specifications (endpoint removals, field type changes, required parameters).

**When it runs:** After Developer modifies API endpoints.

**Output:** `bazinga/api_contract_validation.json`

**Example output:**
```json
{
  "status": "breaking_changes_detected",
  "breaking_changes": [
    {
      "type": "endpoint_removed",
      "path": "/api/v1/users/{id}",
      "method": "DELETE",
      "severity": "critical",
      "impact": "Clients calling this endpoint will receive 404"
    },
    {
      "type": "response_field_removed",
      "path": "/api/v1/auth/login",
      "field": "refresh_token",
      "severity": "high",
      "impact": "Clients expecting refresh_token will break"
    }
  ],
  "recommendations": [
    "CRITICAL: Deploy breaking changes as new API version (/v2) to maintain backward compatibility",
    "Consider API versioning (e.g., /v2/api/users/{id}) instead of removing DELETE /api/v1/users/{id}"
  ]
}
```

**Dependencies:** OpenAPI/Swagger spec files (openapi.yaml, swagger.json) or framework with auto-generation (FastAPI, Flask-RESTX, Express).

**Performance:** 10-20s.

---

#### 4. Database Migration Check
**What it does:** Detects dangerous operations in database migrations (table locks, full-table rewrites, non-concurrent index creation).

**When it runs:** After Developer creates/modifies migrations.

**Output:** `bazinga/db_migration_check.json`

**Example output:**
```json
{
  "status": "dangerous_operations_detected",
  "database": "postgresql",
  "migration_framework": "alembic",
  "dangerous_operations": [
    {
      "migration_file": "migrations/0012_add_user_email_index.py",
      "line": 23,
      "operation": "CREATE INDEX idx_users_email ON users(email)",
      "severity": "high",
      "reason": "Non-concurrent index creation will lock table for writes",
      "estimated_downtime": "30s to 5min depending on table size"
    }
  ],
  "recommendations": [
    "PostgreSQL: Create indexes with CONCURRENTLY to avoid blocking writes",
    "Test migrations on production-sized dataset in staging environment"
  ]
}
```

**Dependencies:** Migration framework (Alembic, Django migrations, Flyway, Liquibase, golang-migrate).

**Performance:** 10-15s.

---

### QA Expert Skills

#### 5. Pattern Miner
**What it does:** Mines historical patterns from git history, issue tracker, and past test failures to predict risk areas.

**When it runs:** In QA Expert phase (full testing mode only).

**Output:** `bazinga/pattern_mining.json`

**Example output:**
```json
{
  "high_risk_files": [
    {
      "file": "src/auth/login.py",
      "risk_score": 0.85,
      "reasons": [
        "Changed 15 times in last 30 days",
        "Caused 3 production incidents",
        "High cyclomatic complexity (CC=23)"
      ]
    }
  ],
  "test_failure_patterns": [
    "Race condition in concurrent login tests (failed 8/10 runs)",
    "Flaky email sending mock (failed randomly)"
  ],
  "recommendations": [
    "Add integration test for concurrent login scenario",
    "Stabilize email mock in tests/conftest.py"
  ]
}
```

**Dependencies:** Git history, optional issue tracker API access.

**Performance:** 30-60s (git log parsing can be slow).

---

#### 6. Quality Dashboard
**What it does:** Aggregates all quality metrics (security, coverage, complexity, test health) into unified dashboard.

**When it runs:** In QA Expert phase (full testing mode only), after all tests complete.

**Output:** `bazinga/quality_dashboard.json`

**Example output:**
```json
{
  "overall_health": "GOOD",
  "health_score": 82,
  "metrics": {
    "security": {
      "status": "PASS",
      "vulnerabilities": 0,
      "last_scan": "2025-01-10T15:30:00Z"
    },
    "coverage": {
      "status": "PASS",
      "line_coverage": 85,
      "branch_coverage": 78,
      "target": 80
    },
    "code_quality": {
      "status": "PASS",
      "lint_issues": 2,
      "complexity_issues": 1
    },
    "test_health": {
      "status": "GOOD",
      "total_tests": 127,
      "passing": 127,
      "flaky_tests": 0
    }
  },
  "trends": {
    "coverage_change": "+3%",
    "security_trend": "stable",
    "quality_trend": "improving"
  }
}
```

**Dependencies:** jq (for JSON processing).

**Performance:** 15-30s.

---

### Project Manager Skills

#### 7. Velocity Tracker
**What it does:** Tracks PM metrics, developer velocity, iteration counts, and time-to-completion.

**When it runs:** Throughout orchestration lifecycle (PM phases).

**Output:** `bazinga/velocity_metrics.json`

**Example output:**
```json
{
  "session_id": "v4_20250110_153000",
  "total_tasks": 3,
  "completed_tasks": 3,
  "iterations": 2,
  "average_iterations_per_task": 1.67,
  "developer_utilization": {
    "dev_1": {
      "tasks_completed": 1,
      "revisions": 2,
      "estimated_time": "12 minutes"
    },
    "dev_2": {
      "tasks_completed": 1,
      "revisions": 1,
      "estimated_time": "8 minutes"
    },
    "dev_3": {
      "tasks_completed": 1,
      "revisions": 2,
      "estimated_time": "15 minutes"
    }
  },
  "model_escalations": 1,
  "total_estimated_time": "35 minutes",
  "parallel_efficiency": "3.1x faster than sequential"
}
```

**Dependencies:** jq (for JSON processing).

**Performance:** 5-10s.

---

## Full Testing Mode

Full testing mode enables the QA Expert agent and comprehensive test requirements.

### What Changes in Full Mode

| Aspect | Minimal Mode (Default) | Full Mode |
|--------|------------------------|-----------|
| **Developer Tests** | Unit tests only | Unit + integration tests |
| **QA Expert** | Disabled | Enabled (runs after all developers) |
| **QA Tests** | N/A | Contract tests, E2E tests |
| **QA Skills** | N/A | Pattern mining, quality dashboard |
| **Coverage Target** | 0% (advisory) | 80% (enforced) |
| **Time to Complete** | ~15-20 min (3 features) | ~30-40 min (3 features) |

### Enabling Full Mode

```bash
/bazinga.configure-testing
> Select: "full"
```

**Configuration saved to:** `bazinga/testing_config.json`

```json
{
  "_testing_framework": {
    "enabled": true,
    "mode": "full",

    "pre_commit_validation": {
      "lint_check": true,
      "unit_tests": true,
      "build_check": true
    },

    "test_requirements": {
      "require_integration_tests": true,
      "require_contract_tests": true,
      "require_e2e_tests": false,
      "coverage_threshold": 80
    },

    "qa_workflow": {
      "enable_qa_expert": true,
      "auto_route_to_qa": true,
      "qa_skills_enabled": true
    }
  }
}
```

### QA Expert Workflow

When full mode is enabled:

1. **Developers complete** → All tasks marked as done
2. **PM routes to QA Expert** → Runs comprehensive test suite
3. **QA Expert executes:**
   - Integration tests (API endpoints, service interactions)
   - Contract tests (API backward compatibility)
   - E2E tests (full user workflows)
   - Pattern mining (risk analysis)
   - Quality dashboard (unified metrics)
4. **QA Expert reports to Tech Lead** → Final approval decision
5. **Tech Lead decides:**
   - APPROVED → PM declares BAZINGA
   - CHANGES_REQUESTED → Route back to developers

### Test Types

#### Integration Tests
- Test interactions between services/modules
- Database integration, API endpoint testing
- Example: `test_user_registration_creates_db_record_and_sends_email()`

#### Contract Tests
- Verify API contracts (request/response schemas)
- Ensure backward compatibility
- Example: `test_login_endpoint_returns_expected_schema()`

#### E2E Tests
- Full user workflow from start to finish
- Browser automation (Selenium, Playwright, Cypress)
- Example: `test_user_can_complete_full_registration_flow()`

---

## Configuration

### Skills Configuration

Interactive configuration:

```bash
/bazinga.configure-skills
```

**Menu:**
```
📦 CORE SKILLS (Lite Profile - Always Active)
  1. lint-check (Developer)
  6. security-scan (Tech Lead)
  7. lint-check (Tech Lead)
  8. test-coverage (Tech Lead)

⚡ ADVANCED SKILLS (Opt-in)
  2. codebase-analysis (Developer)
  3. test-pattern-analysis (Developer)
  4. api-contract-validation (Developer)
  5. db-migration-check (Developer)
  9. pattern-miner (QA Expert)
  10. quality-dashboard (QA Expert)
  11. velocity-tracker (PM)

💡 Input: "advanced" → Enable all 10 skills
💡 Input: "2 3 9" → Enable skills #2, #3, #9
💡 Input: "lite" → Reset to core skills only
```

### Testing Configuration

Interactive configuration:

```bash
/bazinga.configure-testing
```

**Options:**
- **full** - All testing enabled (QA Expert, integration/E2E tests, 80% coverage target)
- **minimal** (default) - Lint + unit tests only, skip QA Expert
- **disabled** - Only lint checks (fastest iteration)

### CLI Configuration

```bash
# Initialize with advanced profile
bazinga init my-project --profile advanced

# Custom configuration
bazinga init my-project --testing full --skills all

# Lite profile (default)
bazinga init my-project --profile lite
```

---

## Performance Considerations

### Skill Execution Time

| Skill | Typical Time | Impact |
|-------|--------------|--------|
| Core Skills (1, 6-8) | 5-20s | Low - always worth it |
| codebase-analysis | 15-30s | Medium - valuable for complex features |
| test-pattern-analysis | 20-40s | Medium - saves time writing tests |
| api-contract-validation | 10-20s | Low - critical for APIs |
| db-migration-check | 10-15s | Low - critical for migrations |
| pattern-miner | 30-60s | High - use for production-critical code |
| quality-dashboard | 15-30s | Medium - nice for final report |
| velocity-tracker | 5-10s | Low - useful for PM metrics |

### Testing Mode Time

| Mode | Time for 3 Features | Speedup |
|------|---------------------|---------|
| Minimal (default) | ~15-20 min | 3x faster (parallel) |
| Full | ~30-40 min | 2.5x faster (parallel + QA) |
| Disabled | ~10-15 min | 3.5x faster (no tests) |

### Graceful Degradation

**Lite mode:** Skills skip gracefully if tools are missing (warns but continues).

**Advanced mode:** Skills fail if required tools are missing (user explicitly opted in for guarantees).

**Example lite mode warning:**
```
⚠️  bandit not installed - security scan skipped in lite mode
   To enable: pip install bandit
   Impact: Security vulnerabilities were not detected. Consider installing for production code.
```

**Example advanced mode error:**
```
❌ bandit required but not installed
   Command: pip install bandit
   Impact: Cannot continue - advanced profile requires security scanning.
```

---

## When to Use Advanced Mode

### Use Advanced Profile When:

✅ **Production-critical features** - Full QA workflow, comprehensive analysis
✅ **Complex refactoring** - Pattern mining, quality dashboard for safety
✅ **API changes** - API contract validation to prevent breaking changes
✅ **Database migrations** - Migration safety checks for production databases
✅ **Team collaboration** - Velocity tracking for metrics and reporting

### Use Lite Profile When:

✅ **Rapid prototyping** - Fast iteration, minimal overhead
✅ **Simple features** - Core quality gates (security, lint, coverage) sufficient
✅ **Small projects** - Advanced analysis not needed
✅ **Solo development** - Don't need velocity tracking or comprehensive reports

---

## Tool Installation

### Core Skills (Lite Profile)

**Python:**
```bash
pip install bandit ruff pytest-cov
```

**JavaScript/TypeScript:**
```bash
npm install --save-dev jest eslint
```

**Go:**
```bash
go install github.com/securego/gosec/v2/cmd/gosec@latest
go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
```

**Java:**
```bash
# Maven
mvn dependency:resolve

# Gradle
gradle build
```

**Ruby:**
```bash
gem install brakeman rubocop simplecov
```

### Advanced Skills

**System tools:**
```bash
# jq (pattern-miner, quality-dashboard, velocity-tracker)
brew install jq           # macOS
sudo apt install jq       # Ubuntu/Debian
sudo yum install jq       # RHEL/CentOS
```

**Python modules:** Advanced skills have their own module dependencies - these are included in the skills themselves. If missing, graceful degradation will handle it.

---

## Integration Examples

### CI/CD Pipeline (Advanced Profile)

```yaml
# .github/workflows/bazinga.yml
name: BAZINGA Full QA

on:
  pull_request:
    branches: [main]

jobs:
  bazinga:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install BAZINGA
        run: |
          pip install git+https://github.com/mehdic/bazinga.git

      - name: Initialize BAZINGA (Advanced)
        run: |
          bazinga init --here --profile advanced

      - name: Run Orchestration
        run: |
          # Trigger via Claude Code CLI (when available)
          # For now: manual trigger or API integration
```

### Pre-commit Hook (Lite Profile)

```bash
# .git/hooks/pre-commit
#!/bin/bash
# Run lite profile checks before commit

bazinga init --here --profile lite
# Run security-scan, lint-check, test-coverage
# Exit 1 if any issues found
```

---

## Troubleshooting

### Common Issues

**Q: Advanced skills not running**
A: Check skills_config.json profile. Run `/bazinga.configure-skills` to verify.

**Q: Skill failed with module import error**
A: Advanced profile requires all dependencies. Check error message for missing modules.

**Q: QA Expert not appearing**
A: Enable full testing mode with `/bazinga.configure-testing` → select "full".

**Q: Pattern miner is slow (>60s)**
A: Large git history. Consider using lite mode or exclude pattern-miner (disable skill #9).

**Q: Quality dashboard fails with "jq not found"**
A: Install jq: `brew install jq` (macOS) or `apt install jq` (Linux).

---

## See Also

- [README.md](../README.md) - Overview and quick start
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Common commands and workflows
- [SKILLS.md](SKILLS.md) - Complete Skills reference
- [MODEL_ESCALATION.md](MODEL_ESCALATION.md) - Opus escalation details
- [ARCHITECTURE.md](ARCHITECTURE.md) - Technical deep-dive

---

**Version:** 2.0.0
**Last Updated:** 2025-01-10
