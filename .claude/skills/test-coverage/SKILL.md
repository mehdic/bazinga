---
name: test-coverage
description: "Generate comprehensive test coverage reports when reviewing code. Identifies untested code paths and low-coverage areas. Supports Python (pytest-cov), JavaScript (jest), Go (go test -cover), Java (JaCoCo). Use when reviewing tests or before approving code changes."
allowed-tools: [Bash, Read, Write]
---

# Test Coverage Analysis Skill

You are the test-coverage skill. When invoked, you run appropriate coverage tools based on project language and generate structured coverage reports.

## Your Task

When invoked, you will:
1. Detect the project language and test framework
2. Run coverage analysis using the appropriate tool
3. Parse coverage results
4. Identify files with low coverage (<80%)
5. Generate a structured report

---

## Step 1: Detect Project Language

Use the **Read** tool to check for language indicators:

**Python:**
- Check for: `requirements.txt`, `pyproject.toml`, `setup.py`, `pytest.ini`
- If found: language = "python"

**JavaScript/TypeScript:**
- Check for: `package.json`
- If found: language = "javascript"

**Go:**
- Check for: `go.mod`, `go.sum`
- If found: language = "go"

**Java:**
- Check for: `pom.xml` (Maven) or `build.gradle` (Gradle)
- If found: language = "java"

---

## Step 2: Run Coverage Analysis

Based on detected language, use the **Bash** tool to run coverage:

### For Python:
```bash
# Check if pytest-cov is installed
pip list | grep pytest-cov

# If not installed, install it
if not found:
    pip install pytest-cov

# Run coverage
pytest --cov=. --cov-report=json --cov-report=term-missing
```

### For JavaScript/TypeScript:
```bash
# Check if jest is configured
if package.json has "jest" in devDependencies or scripts:
    npm test -- --coverage --coverageReporters=json --coverageReporters=text

# Alternative: check for other test runners
if package.json has "vitest":
    npx vitest run --coverage
```

### For Go:
```bash
# Run tests with coverage
go test -coverprofile=coverage.out ./...

# Generate coverage report
go tool cover -func=coverage.out > coverage.txt
```

### For Java:

**Maven:**
```bash
mvn test
mvn jacoco:report
```

**Gradle:**
```bash
./gradlew test jacocoTestReport
```

---

## Step 3: Parse Coverage Results

Use the **Read** tool to read coverage output:

### Python:
- Read `coverage.json`
- Extract:
  - `totals.percent_covered` → overall coverage
  - For each file in `files`:
    - `summary.percent_covered` → file coverage
    - `missing_lines` → uncovered line numbers

### JavaScript:
- Read `coverage/coverage-summary.json`
- Extract:
  - `total.lines.pct` → overall line coverage
  - `total.branches.pct` → branch coverage
  - For each file:
    - `lines.pct`, `branches.pct`, `functions.pct`

### Go:
- Read `coverage.txt` (output from go tool cover)
- Parse lines like: `package/file.go:function    coverage%`
- Calculate overall coverage from all files

### Java:
- Read `target/site/jacoco/jacoco.xml` (Maven) or `build/reports/jacoco/test/jacocoTestReport.xml` (Gradle)
- Extract coverage percentages from XML

---

## Step 4: Identify Low Coverage Areas

For each file analyzed:

```
if file_coverage < 80:
    add to files_below_threshold:
        - file path
        - coverage percentage
        - uncovered line ranges
```

Identify critical uncovered code:
- Authentication/authorization logic
- Payment/transaction handling
- Data validation
- Error handling paths

---

## Step 5: Generate Structured Report

Use the **Write** tool to create `coordination/coverage_report.json`:

```json
{
  "timestamp": "<ISO 8601 timestamp>",
  "language": "<detected language>",
  "overall_coverage": <percentage>,
  "coverage_by_file": {
    "<file_path>": {
      "line_coverage": <percentage>,
      "branch_coverage": <percentage or null>,
      "uncovered_lines": [<line numbers or ranges>]
    }
  },
  "files_below_threshold": [
    {
      "file": "<file_path>",
      "coverage": <percentage>,
      "threshold": 80
    }
  ],
  "critical_uncovered_paths": [
    "<file>:<lines> (<description if identifiable>)"
  ]
}
```

---

## Step 6: Return Summary

Return a concise summary to the calling agent:

```
Test Coverage Report:
- Overall coverage: X%
- Files below 80% threshold: N files
- Critical areas with low coverage:
  - <file1>: X% coverage
  - <file2>: Y% coverage

Details saved to: coordination/coverage_report.json
```

---

## Error Handling

**If coverage tool not installed:**
- Try to install it automatically (pip install pytest-cov, npm install jest, etc.)
- If installation fails, return error with installation instructions

**If no tests found:**
- Return: "No tests found in project. Cannot generate coverage report."

**If tests fail:**
- Return: "Tests failed. Coverage report not generated. Please fix failing tests first."
- Include test failure summary

**If coverage report file not found:**
- Return: "Coverage tool ran but report file not generated. Check tool configuration."

---

## Coverage Thresholds

When analyzing results, use these thresholds:

- **>= 80%:** Good coverage (mention as passing)
- **60-79%:** Acceptable (mention as needing improvement)
- **< 60%:** Low coverage (flag as critical)
- **< 40%:** Very low coverage (flag as high risk)

---

## Notes

- Focus on **line coverage** as primary metric
- Report **branch coverage** if available (Python, JavaScript)
- Prioritize coverage in critical code paths (auth, payment, validation)
- Don't flag test files themselves for low coverage
- Exclude generated files, migrations, and config files from analysis
