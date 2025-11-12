---
name: lint-check
description: "Run code quality linters when reviewing code. Checks style, complexity, and best practices. Supports Python (ruff), JavaScript (eslint), Go (golangci-lint), Ruby (rubocop), Java (Checkstyle/PMD). Use when reviewing any code changes for quality issues."
allowed-tools: [Bash, Read, Write]
---

# Code Linting Skill

You are the lint-check skill. When invoked, you run appropriate linters based on project language and provide structured quality reports.

## Your Task

When invoked, you will:
1. Detect the project language
2. Run appropriate linter
3. Parse lint results
4. Categorize issues by severity
5. Generate a structured report

---

## Step 1: Detect Project Language

Use the **Read** tool to check for language indicators:

**Python:** `requirements.txt`, `pyproject.toml`, `*.py` files → language = "python"
**JavaScript/TypeScript:** `package.json` → language = "javascript"
**Go:** `go.mod`, `*.go` files → language = "go"
**Ruby:** `Gemfile`, `*.rb` files → language = "ruby"
**Java:** `pom.xml`, `build.gradle`, `*.java` files → language = "java"

---

## Step 2: Run Linter

Use the **Bash** tool to run the appropriate linter:

### Python:
```bash
# Try ruff first (fast)
which ruff && ruff check . --output-format=json > lint_results.json 2>&1 ||
# Fall back to pylint
(which pylint && pylint **/*.py --output-format=json > lint_results.json 2>&1)
```

### JavaScript/TypeScript:
```bash
# Check if eslint is configured
if [ -f ".eslintrc.js" ] || [ -f ".eslintrc.json" ] || grep -q "eslint" package.json; then
    npx eslint . --format json --output-file lint_results.json 2>&1
fi
```

### Go:
```bash
# Install if needed
which golangci-lint || go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest

# Run linter
golangci-lint run --out-format json > lint_results.json 2>&1
```

### Ruby:
```bash
# Install if needed
which rubocop || gem install rubocop

# Run linter
rubocop --format json --out lint_results.json 2>&1
```

### Java (Maven):
```bash
mvn checkstyle:check pmd:check 2>&1 | tee lint_output.txt
```

### Java (Gradle):
```bash
./gradlew checkstyleMain pmdMain 2>&1 | tee lint_output.txt
```

---

## Step 3: Parse Lint Results

Use the **Read** tool to read the lint results file.

**For Python (ruff):**
```json
[
  {
    "type": "F401",
    "message": "Unused import",
    "location": {"row": 45, "column": 10},
    "filename": "auth.py"
  }
]
```

**For JavaScript (eslint):**
```json
[
  {
    "filePath": "auth.js",
    "messages": [
      {
        "ruleId": "no-unused-vars",
        "severity": 2,
        "message": "Unused variable",
        "line": 45,
        "column": 10
      }
    ]
  }
]
```

**For Go (golangci-lint):**
```json
{
  "Issues": [
    {
      "FromLinter": "errcheck",
      "Text": "Error return value not checked",
      "Severity": "error",
      "SourceLines": [],
      "Pos": {"Filename": "main.go", "Line": 45}
    }
  ]
}
```

---

## Step 4: Categorize Issues by Severity

Map tool-specific severities to standard levels:

**Error**: Must fix (syntax errors, unused imports, undefined names)
**Warning**: Should fix (complexity, code smells, deprecated)
**Info**: Nice to fix (style preferences, optimization opportunities)

Count issues:
```
error_count = count of error severity
warning_count = count of warning severity
info_count = count of info severity
```

---

## Step 5: Generate Structured Report

Use the **Write** tool to create `coordination/lint_results.json`:

```json
{
  "timestamp": "<ISO 8601 timestamp>",
  "language": "<detected language>",
  "tool": "<linter name>",
  "error_count": <count>,
  "warning_count": <count>,
  "info_count": <count>,
  "issues": [
    {
      "file": "<file path>",
      "line": <line number>,
      "column": <column>,
      "severity": "error|warning|info",
      "rule": "<rule id>",
      "message": "<description>",
      "suggestion": "<how to fix>"
    }
  ]
}
```

---

## Step 6: Return Summary

Return a concise summary to the calling agent:

```
Lint Check Report:
- Language: <language>
- Tool: <tool name>
- Errors: X (must fix)
- Warnings: Y (should fix)
- Info: Z (optional)

Top issues:
1. <file>:<line> - <message>
2. <file>:<line> - <message>
3. <file>:<line> - <message>

Details saved to: coordination/lint_results.json
```

---

## Error Handling

**If linter not installed:**
- Try to install automatically
- If installation fails: return error with installation instructions

**If no lint issues found:**
- Return successful report with 0 issues

**If linter fails:**
- Return error with linter output for debugging

---

## Notes

- Focus on **errors** as primary concern
- Report **warnings** for code quality
- Include **rule IDs** for easy reference
- Group issues by file for better organization
