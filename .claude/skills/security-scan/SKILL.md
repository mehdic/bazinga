---
name: security-scan
description: "Run comprehensive security vulnerability scans when reviewing code. Automatically uses basic mode (fast, high/medium severity only) for first reviews, advanced mode (comprehensive, all severities) for iterations. Detects SQL injection, XSS, hardcoded secrets, insecure dependencies. Use before approving any code changes or pull requests."
allowed-tools: [Bash, Read, Write, Grep]
---

# Security Scanning Skill

You are the security-scan skill. When invoked, you run appropriate security scanners based on project language and provide structured security reports.

## Your Task

When invoked, you will:
1. Check the scan mode (basic or advanced) from environment variable
2. Detect the project language
3. Run appropriate security scanning tools
4. Parse scan results
5. Generate a structured security report

---

## Step 1: Determine Scan Mode

Check the environment variable `SECURITY_SCAN_MODE` via **Bash**:

```bash
echo $SECURITY_SCAN_MODE
```

If not set or equals "basic":
- Use **basic mode** (fast, high/medium severity only)
- Runtime: 5-10 seconds

If equals "advanced":
- Use **advanced mode** (all severities, comprehensive)
- Runtime: 30-60 seconds

---

## Step 2: Detect Project Language

Use the **Read** tool to check for language indicators:

**Python:**
- Check for: `requirements.txt`, `pyproject.toml`, `setup.py`, `*.py` files
- If found: language = "python"

**JavaScript/TypeScript:**
- Check for: `package.json`, `node_modules/`
- If found: language = "javascript"

**Go:**
- Check for: `go.mod`, `go.sum`, `*.go` files
- If found: language = "go"

**Ruby:**
- Check for: `Gemfile`, `Gemfile.lock`, `*.rb` files
- If found: language = "ruby"

**Java:**
- Check for: `pom.xml`, `build.gradle`, `*.java` files
- If found: language = "java"

---

## Step 3: Run Security Scan

Based on language and mode, use the **Bash** tool to run security scanners:

### Python:

**Basic Mode:**
```bash
# Check if bandit is installed
which bandit || pip install bandit

# Run with high/medium severity only
bandit -r . -ll -f json -o security_scan.json 2>&1
```

**Advanced Mode:**
```bash
# Install semgrep if needed
which semgrep || pip install semgrep

# Run bandit (all severities)
bandit -r . -f json -o bandit_results.json 2>&1

# Run semgrep with auto rules
semgrep --config=auto --json -o semgrep_results.json . 2>&1
```

### JavaScript/TypeScript:

**Basic Mode:**
```bash
# npm audit is built-in
npm audit --json --audit-level=high > security_scan.json 2>&1
```

**Advanced Mode:**
```bash
# Full npm audit
npm audit --json > npm_audit.json 2>&1

# Install and run eslint-plugin-security if available
if [ -f "package.json" ] && grep -q "eslint-plugin-security" package.json; then
    npx eslint . --format json > eslint_security.json 2>&1
fi
```

### Go:

**Basic Mode:**
```bash
# Install gosec if needed
which gosec || go install github.com/securego/gosec/v2/cmd/gosec@latest

# Run with high severity only
gosec -severity high -fmt json -out security_scan.json ./... 2>&1
```

**Advanced Mode:**
```bash
# Run with all severities
gosec -fmt json -out security_scan.json ./... 2>&1
```

### Ruby:

**Basic Mode:**
```bash
# Install brakeman if needed
which brakeman || gem install brakeman

# Run with severity level 1 (high)
brakeman --format json --output security_scan.json --severity-level 1 2>&1
```

**Advanced Mode:**
```bash
# Run with all findings
brakeman --format json --output security_scan.json 2>&1
```

### Java:

**Basic Mode:**
```bash
# Maven
if [ -f "pom.xml" ]; then
    mvn spotbugs:check -Dspotbugs.effort=Max -Dspotbugs.threshold=High 2>&1
fi

# Gradle
if [ -f "build.gradle" ]; then
    ./gradlew spotbugsMain 2>&1
fi
```

**Advanced Mode:**
```bash
# Maven with all priorities + dependency check
if [ -f "pom.xml" ]; then
    mvn spotbugs:check 2>&1
    mvn dependency-check:check 2>&1
fi

# Gradle
if [ -f "build.gradle" ]; then
    ./gradlew spotbugsMain dependencyCheckAnalyze 2>&1
fi
```

---

## Step 4: Parse Scan Results

Use the **Read** tool to read the scan results file(s).

### For Python (bandit):
Read `security_scan.json` or `bandit_results.json`:
```json
{
  "results": [
    {
      "issue_severity": "HIGH",
      "issue_text": "SQL injection risk",
      "filename": "auth.py",
      "line_number": 45
    }
  ]
}
```

### For JavaScript (npm audit):
Read `security_scan.json`:
```json
{
  "vulnerabilities": {
    "package-name": {
      "severity": "high",
      "title": "Vulnerability description"
    }
  }
}
```

### For Go (gosec):
Read `security_scan.json`:
```json
{
  "Issues": [
    {
      "severity": "HIGH",
      "what": "Issue description",
      "file": "main.go",
      "line": "45"
    }
  ]
}
```

---

## Step 5: Categorize Issues by Severity

Count issues by severity level:

```
critical_issues = count of CRITICAL severity
high_issues = count of HIGH severity
medium_issues = count of MEDIUM severity
low_issues = count of LOW severity (advanced mode only)
info_issues = count of INFO severity (advanced mode only)
```

---

## Step 6: Generate Structured Report

Use the **Write** tool to create `coordination/security_scan.json`:

```json
{
  "scan_mode": "basic|advanced",
  "timestamp": "<ISO 8601 timestamp>",
  "language": "<detected language>",
  "status": "success|partial|error",
  "tool": "<tool name used>",
  "error": "<error message if status != success>",
  "critical_issues": <count>,
  "high_issues": <count>,
  "medium_issues": <count>,
  "low_issues": <count>,
  "info_issues": <count>,
  "issues": [
    {
      "severity": "CRITICAL|HIGH|MEDIUM|LOW|INFO",
      "title": "<issue title>",
      "file": "<file path>",
      "line": <line number>,
      "description": "<detailed description>",
      "recommendation": "<how to fix>"
    }
  ]
}
```

**Status field values:**
- `"success"`: Scan completed without errors
- `"partial"`: Scan completed but some tools failed
- `"error"`: Scan failed completely

---

## Step 7: Return Summary

Return a concise summary to the calling agent:

```
Security Scan Report (MODE mode):
- Tool: <tool name>
- Critical issues: X
- High issues: Y
- Medium issues: Z
[In advanced mode also show: Low issues, Info issues]

Top issues:
1. <severity>: <issue title> (<file>:<line>)
2. <severity>: <issue title> (<file>:<line>)
3. <severity>: <issue title> (<file>:<line>)

Details saved to: coordination/security_scan.json
```

---

## Error Handling

**If security tool not installed:**
```bash
# Try to install automatically
# For bandit:
pip install bandit

# For gosec:
go install github.com/securego/gosec/v2/cmd/gosec@latest

# For brakeman:
gem install brakeman
```

If auto-installation fails:
- Set status to "error"
- Include installation instructions in error message

**If scan fails:**
- Set status to "partial" or "error"
- Save whatever results were obtained
- Include error details in report

**If no security issues found:**
- Return successful report with 0 issues
- Status: "success"

---

## Severity Prioritization

When summarizing results, prioritize by severity:

1. **CRITICAL** - Must fix immediately (SQL injection, auth bypass, hardcoded secrets)
2. **HIGH** - Should fix before deployment (XSS, insecure crypto, path traversal)
3. **MEDIUM** - Good to fix (weak RNG, missing CSRF, insecure permissions)
4. **LOW** - Optional (code smells, deprecated functions) - advanced mode only
5. **INFO** - Best practices - advanced mode only

---

## Mode Comparison

**Basic Mode (default):**
- Fast execution (5-10 seconds)
- High/medium severity only
- Single tool per language
- Good for first-pass review

**Advanced Mode (revision_count >= 2):**
- Comprehensive (30-60 seconds)
- All severity levels
- Multiple tools per language
- Deep analysis
- Good for persistent issues

---

## Notes

- Always check the **status** field before interpreting results
- Empty issues array with status="error" means scan FAILED, not that code is secure
- In basic mode, low/info severities are not scanned
- Tools may produce false positives - include recommendation to review findings
