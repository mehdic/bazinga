---
name: lint-check
description: "Run code quality linters when reviewing code. Checks style, complexity, and best practices. Supports Python (ruff), JavaScript (eslint), Go (golangci-lint), Ruby (rubocop), Java (Checkstyle/PMD). Use when reviewing any code changes for quality issues."
allowed-tools: [Bash, Read]
---

# Code Linting Skill

## Purpose

Automated code quality and style checking for code reviews. This Skill runs appropriate linters based on project language and provides structured quality reports.

## What It Does

- Detects project language
- Runs language-appropriate linter
- Reports style violations and anti-patterns
- Checks best practice compliance
- Identifies code smells

---

## Supported Languages

### Python
- **Tool:** ruff (modern, fast) or pylint (comprehensive)
- **Checks:** PEP 8 style, code complexity, common mistakes
- **Speed:** Very fast (ruff < 1s, pylint 3-5s)

### JavaScript/TypeScript
- **Tool:** eslint
- **Checks:** Code style, potential bugs, best practices
- **Speed:** Fast (2-5s)

### Go
- **Tool:** golangci-lint
- **Checks:** Multiple linters (gofmt, govet, staticcheck, etc.)
- **Speed:** Moderate (5-10s)

### Ruby
- **Tool:** rubocop
- **Checks:** Ruby style guide, best practices
- **Speed:** Moderate (5-10s)

### Java
- **Tool:** Checkstyle (style) + PMD (code quality)
- **Checks:** Code style, complexity, best practices, bug patterns
- **Speed:** Moderate (10-15s)
- **Integration:** Via Maven/Gradle plugins

---

## Output Format

Results are saved to `coordination/lint_results.json`:

```json
{
  "timestamp": "2025-11-07T20:00:00Z",
  "language": "python",
  "tool": "ruff",
  "error_count": 5,
  "warning_count": 12,
  "issues": [
    {
      "file": "auth.py",
      "line": 45,
      "column": 10,
      "severity": "error",
      "rule": "F401",
      "message": "Unused import: 'os'",
      "suggestion": "Remove unused import"
    },
    {
      "file": "payment.py",
      "line": 89,
      "column": 5,
      "severity": "warning",
      "rule": "C901",
      "message": "Function too complex (complexity: 15)",
      "suggestion": "Refactor into smaller functions"
    }
  ]
}
```

---

## How to Use

### Automatic Invocation

This Skill is **automatically invoked** by Claude when:
- Tech Lead is reviewing code changes
- Before approving pull requests
- Code quality issues are suspected

### Manual Test

```bash
# Run linting
bash .claude/skills/lint-check/lint.sh

# Or PowerShell
.\.claude\skills\lint-check\lint.ps1
```

---

## Installation Requirements

### Python Projects

```bash
# Recommended: ruff (fast)
pip install ruff

# Or: pylint (comprehensive)
pip install pylint
```

### JavaScript Projects

```bash
npm install --save-dev eslint
npx eslint --init
```

### Go Projects

```bash
go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
```

### Ruby Projects

```bash
gem install rubocop
```

### Java Projects

**Maven** (`pom.xml`):
```xml
<!-- Checkstyle for style checking -->
<plugin>
  <groupId>org.apache.maven.plugins</groupId>
  <artifactId>maven-checkstyle-plugin</artifactId>
  <version>3.3.1</version>
  <configuration>
    <configLocation>google_checks.xml</configLocation>
  </configuration>
</plugin>

<!-- PMD for code quality -->
<plugin>
  <groupId>org.apache.maven.plugins</groupId>
  <artifactId>maven-pmd-plugin</artifactId>
  <version>3.21.2</version>
</plugin>
```

**Gradle** (`build.gradle`):
```gradle
plugins {
  id 'checkstyle'
  id 'pmd'
}

checkstyle {
  toolVersion = '10.12.5'
  configFile = file('config/checkstyle/google_checks.xml')
}

pmd {
  toolVersion = '6.55.0'
  ruleSets = ['category/java/bestpractices.xml', 'category/java/errorprone.xml']
}
```

---

## Interpreting Results

### Severity Levels

**Errors (Must Fix):**
- Syntax errors
- Unused imports/variables
- Undefined names
- Breaking style violations

**Warnings (Should Fix):**
- High complexity functions
- Code smells
- Deprecated patterns
- Style inconsistencies

**Info (Nice to Fix):**
- Minor style preferences
- Optimization opportunities
- Documentation suggestions

### Common Issues

**Python:**
- F401: Unused import
- E501: Line too long (>88 chars for ruff, >79 for PEP 8)
- C901: Function too complex
- N803: Argument name should be lowercase

**JavaScript:**
- no-unused-vars: Unused variables
- eqeqeq: Use === instead of ==
- no-console: Console statements in production code
- complexity: Function too complex

**Go:**
- gofmt: Code not formatted
- govet: Suspicious constructs
- staticcheck: Static analysis issues
- errcheck: Unchecked errors

---

## Configuration

### Python: pyproject.toml (ruff)

```toml
[tool.ruff]
line-length = 100
select = ["E", "F", "W", "C", "N"]
ignore = ["E501"]  # Ignore line too long

[tool.ruff.per-file-ignores]
"tests/*" = ["F401"]  # Allow unused imports in tests
```

### JavaScript: .eslintrc.json

```json
{
  "extends": "eslint:recommended",
  "rules": {
    "no-console": "warn",
    "eqeqeq": "error",
    "complexity": ["warn", 10]
  }
}
```

### Go: .golangci.yml

```yaml
linters:
  enable:
    - gofmt
    - govet
    - staticcheck
    - errcheck
```

---

## Troubleshooting

**Issue:** Linter not found

**Solution:** Install the appropriate linter for your language (see Installation Requirements)

**Issue:** Too many warnings

**Solution:** Configure linter to ignore certain rules or directories. Create config file (.ruff.toml, .eslintrc, etc.)

**Issue:** False positives

**Solution:** Use inline comments to suppress specific warnings:
- Python: `# noqa: F401`
- JavaScript: `// eslint-disable-next-line no-console`
- Go: `//nolint:errcheck`

---

## Implementation

See `lint.sh` (bash) or `lint.ps1` (PowerShell) for full implementation details.

---

## Credits

This Skill uses industry-standard linting tools:
- **ruff**: Fast Python linter (Astral)
- **pylint**: Python code analyzer (PyCQA)
- **eslint**: JavaScript/TypeScript linter (OpenJS Foundation)
- **golangci-lint**: Go linters aggregator
- **rubocop**: Ruby static analyzer (RuboCop)
- **Checkstyle**: Java style checker (Checkstyle)
- **PMD**: Java code quality analyzer (PMD)
