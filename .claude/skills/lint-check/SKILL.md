---
name: lint-check
description: "Run code quality linters when reviewing code. Checks style, complexity, and best practices. Supports Python (ruff), JavaScript (eslint), Go (golangci-lint), Ruby (rubocop), Java (Checkstyle/PMD). Use when reviewing any code changes for quality issues."
version: 1.0.0
allowed-tools: [Bash, Read]
---

# Code Linting Skill

You are the lint-check skill. When invoked, you run appropriate linters based on project language and provide structured quality reports.

## When to Invoke This Skill

**Invoke this skill when:**
- Tech Lead is reviewing code changes
- Before approving pull requests
- Code quality issues suspected
- Before merge to main branch
- Style compliance check needed

**Do NOT invoke when:**
- Generated code (migrations, protobuf, auto-generated files)
- Third-party code (vendor/, node_modules/)
- Work-in-progress drafts not ready for review
- Emergency hotfixes (skip linting to save time)

---

## Your Task

When invoked:
1. Execute the lint checking script
2. Read the generated lint report
3. Return a summary to the calling agent

---

## Step 1: Execute Lint Check Script

Use the **Bash** tool to run the pre-built linting script.

**On Unix/macOS:**
```bash
bash .claude/skills/lint-check/scripts/lint.sh
```

**On Windows (PowerShell):**
```powershell
pwsh .claude/skills/lint-check/scripts/lint.ps1
```

> **Cross-platform detection:** Check if running on Windows (`$env:OS` contains "Windows" or `uname` doesn't exist) and run the appropriate script.

This script will:
- Detect project language (Python, JavaScript, Go, Ruby, Java)
- Run appropriate linter (ruff/pylint, eslint, golangci-lint, rubocop, checkstyle/pmd)
- Parse results and categorize by severity
- Generate `bazinga/artifacts/{SESSION_ID}/skills/lint_results.json`

---

## Step 2: Read Generated Report

Use the **Read** tool to read:

```bash
bazinga/artifacts/{SESSION_ID}/skills/lint_results.json
```

Extract key information:
- `tool` - Linter used
- `error_count` - Must-fix issues
- `warning_count` - Should-fix issues
- `info_count` - Optional improvements
- `issues` - Array of findings with file/line/rule/message

---

## Step 3: Return Summary

Return a concise summary to the calling agent:

```
Lint Check Report:
- Language: {language}
- Tool: {tool_name}
- Errors: {count} (must fix)
- Warnings: {count} (should fix)
- Info: {count} (optional)

Top issues:
1. {file}:{line} - {message}
2. {file}:{line} - {message}
3. {file}:{line} - {message}

Details saved to: bazinga/artifacts/{SESSION_ID}/skills/lint_results.json
```

---

## Example Invocation

**Scenario: Code Quality Check Before Merge**

Input: Tech Lead reviewing Python code style compliance

Expected output:
```
Lint Check Report:
- Language: python
- Tool: ruff
- Errors: 3 (must fix)
- Warnings: 12 (should fix)
- Info: 5 (optional)

Top issues:
1. auth.py:45 - Unused import 'os' (F401)
2. payment.py:89 - Function too complex (complexity: 15) (C901)
3. user.py:23 - Line too long (102 > 88 characters) (E501)

Details saved to: bazinga/artifacts/{SESSION_ID}/skills/lint_results.json
```

**Scenario: Clean Code**

Input: Tech Lead final review

Expected output:
```
Lint Check Report:
- Language: javascript
- Tool: eslint
- Errors: 0 (must fix)
- Warnings: 0 (should fix)
- Info: 2 (optional)

Code quality: Excellent! No errors or warnings.

Details saved to: bazinga/artifacts/{SESSION_ID}/skills/lint_results.json
```

---

## Error Handling

**If linter not installed:**
- Script attempts auto-installation
- Falls back gracefully if installation fails
- Returns error with installation instructions

**If no lint issues found:**
- Return successful report with 0 issues

**If linter fails:**
- Return error with linter output for debugging

---

## Notes

- The script (291+ lines) handles all language detection and linter execution
- Supports both bash (Linux/Mac) and PowerShell (Windows)
- Focuses on **errors** as primary concern (blocking issues)
- Reports **warnings** for code quality improvements
- Includes **rule IDs** for easy reference and suppression
- Groups issues by file for better organization
