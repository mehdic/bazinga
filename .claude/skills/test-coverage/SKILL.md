---
name: test-coverage
description: "Generate comprehensive test coverage reports when reviewing code. Identifies untested code paths and low-coverage areas. Supports Python (pytest-cov), JavaScript (jest), Go (go test -cover), Java (JaCoCo). Use when reviewing tests or before approving code changes."
allowed-tools: [Bash, Read, Write]
---

# Test Coverage Analysis Skill

## Purpose

Automated test coverage analysis for code reviews. This Skill runs appropriate coverage tools based on project language and generates structured coverage reports.

## What It Does

- Detects project language and test framework
- Runs coverage analysis
- Generates detailed reports with uncovered lines
- Flags critical code with <80% coverage
- Provides historical trend analysis (if data available)

---

## Supported Languages

### Python
- **Tool:** pytest with pytest-cov
- **Coverage types:** Line and branch coverage
- **Output:** Detailed per-file breakdown

### JavaScript/TypeScript
- **Tool:** Jest with coverage
- **Coverage types:** Line, branch, function, statement
- **Output:** Istanbul format reports

### Go
- **Tool:** go test -cover
- **Coverage types:** Package and function coverage
- **Output:** Coverage percentage per package

### Java
- **Tool:** JaCoCo via Maven/Gradle
- **Coverage types:** Line, branch, method, class coverage
- **Output:** XML/HTML reports with per-package breakdown
- **Integration:** Seamlessly integrates with Maven Surefire and Gradle test tasks

---

## Output Format

Results are saved to `coordination/coverage_report.json`:

```json
{
  "timestamp": "2025-11-07T20:00:00Z",
  "language": "python",
  "overall_coverage": 67.5,
  "coverage_by_file": {
    "auth.py": {
      "line_coverage": 45.2,
      "branch_coverage": 38.0,
      "uncovered_lines": [45, 46, 47, 52, 89-103]
    },
    "payment.py": {
      "line_coverage": 52.1,
      "branch_coverage": 48.5,
      "uncovered_lines": [23, 45-52, 78]
    }
  },
  "files_below_threshold": [
    {
      "file": "auth.py",
      "coverage": 45.2,
      "threshold": 80
    }
  ],
  "critical_uncovered_paths": [
    "auth.py:45-52 (token validation error handling)",
    "payment.py:89-103 (refund logic edge cases)"
  ]
}
```

---

## How to Use

### Automatic Invocation

This Skill is **automatically invoked** by Claude when:
- Tech Lead is reviewing test files
- Before approving code changes
- Developer claims "added tests"

### Manual Test

```bash
# Run coverage analysis
bash .claude/skills/test-coverage/coverage.sh

# Or PowerShell
.\.claude\skills\test-coverage\coverage.ps1
```

---

## Installation Requirements

### Python Projects

```bash
pip install pytest pytest-cov
```

### JavaScript Projects

```bash
npm install --save-dev jest
# Or if using existing test setup
npm install --save-dev @jest/globals
```

### Go Projects

No additional installation needed (built-in to go test).

### Java Projects

**Maven** (`pom.xml`):
```xml
<plugin>
  <groupId>org.jacoco</groupId>
  <artifactId>jacoco-maven-plugin</artifactId>
  <version>0.8.11</version>
  <executions>
    <execution>
      <goals>
        <goal>prepare-agent</goal>
      </goals>
    </execution>
    <execution>
      <id>report</id>
      <phase>test</phase>
      <goals>
        <goal>report</goal>
      </goals>
    </execution>
  </executions>
</plugin>
```

**Gradle** (`build.gradle`):
```gradle
plugins {
  id 'jacoco'
}

jacoco {
  toolVersion = '0.8.11'
}

jacocoTestReport {
  reports {
    xml.required = true
    html.required = true
  }
}

test {
  finalizedBy jacocoTestReport
}
```

---

## Interpreting Results

### Coverage Thresholds

- **>= 80%:** Good coverage
- **60-79%:** Acceptable, but could improve
- **< 60%:** Low coverage, needs attention
- **< 40%:** Critical, high risk

### Focus Areas

**Critical uncovered code:**
- Authentication logic
- Payment/transaction handling
- Data validation
- Error handling paths
- Edge cases

**Less critical:**
- Logging statements
- Simple getters/setters
- Configuration loading

---

## Configuration

### Python: pytest.ini or pyproject.toml

```ini
[tool:pytest]
addopts = --cov=. --cov-report=json --cov-report=term-missing
```

### JavaScript: jest.config.js

```javascript
module.exports = {
  collectCoverage: true,
  coverageReporters: ['json', 'text'],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  }
};
```

### Go: No configuration needed

Go coverage is built-in to the test command.

---

## Troubleshooting

**Issue:** pytest-cov not found

**Solution:**
```bash
pip install pytest-cov
```

**Issue:** No tests found

**Solution:** Ensure tests follow naming convention (test_*.py, *.test.js, *_test.go)

**Issue:** Coverage report not generated

**Solution:** Check that tests actually run and pass. Coverage isn't generated if tests fail.

---

## Implementation

See `coverage.sh` (bash) or `coverage.ps1` (PowerShell) for full implementation details.

---

## Credits

This Skill uses standard coverage tools:
- **pytest-cov**: Python coverage (pytest-dev)
- **Jest**: JavaScript testing framework (Facebook)
- **go test -cover**: Go built-in coverage
- **JaCoCo**: Java Code Coverage (EclEmma)
