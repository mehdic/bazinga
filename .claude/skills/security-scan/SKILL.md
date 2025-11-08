---
name: security-scan
description: "Run comprehensive security vulnerability scans when reviewing code. Automatically uses basic mode (fast, high/medium severity only) for first reviews, advanced mode (comprehensive, all severities) for iterations. Detects SQL injection, XSS, hardcoded secrets, insecure dependencies. Use before approving any code changes or pull requests."
allowed-tools: [Bash, Read, Write, Grep]
---

# Security Scanning Skill

## Purpose

Automated security vulnerability detection for code reviews. This Skill runs appropriate security scanners based on project language and provides structured security reports.

## Mode Selection

**Mode is automatically determined by revision count:**

- **Basic Mode** (revision_count < 2): Fast scan focusing on high/medium severity issues (5-10 seconds)
- **Advanced Mode** (revision_count >= 2): Comprehensive scan with all severities and deep analysis (30-60 seconds)

**The mode is passed via environment variable `SECURITY_SCAN_MODE` set by the Tech Lead agent.**

---

## Basic Mode

**What it scans:**
- High and medium severity vulnerabilities only
- Common patterns: SQL injection, XSS, hardcoded secrets, authentication bypasses
- Dependency vulnerabilities (high severity only)
- Fast execution optimized for first-pass review

**Time:** 5-10 seconds

**Tools by language:**
- **Python:** `bandit -ll` (high/medium only)
- **JavaScript:** `npm audit --audit-level=high`
- **Go:** `gosec -severity high`
- **Ruby:** `brakeman --severity-level 1`
- **Java:** `spotbugs` with Find Security Bugs (high priority only)

**Output:** `coordination/security_scan.json`

**Use case:** First code review, quick feedback loop

---

## Advanced Mode

**What it scans:**
- ALL severity levels (critical, high, medium, low, info)
- Deep pattern analysis with semgrep
- Comprehensive dependency vulnerability graph
- Timing attack detection
- Race condition patterns
- Custom project-specific security rules (if configured)
- Historical vulnerability context

**Time:** 30-60 seconds

**Tools by language:**
- **Python:** `bandit` (all severities) + `semgrep --config=auto`
- **JavaScript:** `npm audit` (full) + `eslint-plugin-security`
- **Go:** `gosec` (all severities)
- **Ruby:** `brakeman` (all findings)
- **Java:** `spotbugs` (all priorities) + `semgrep` + OWASP Dependency Check

**Output:** `coordination/security_scan.json` with extended analysis

**Use case:** Code revised 2+ times, persistent security issues, need comprehensive analysis

---

## How to Use

### Automatic Invocation

This Skill is **automatically invoked** by Claude when:
- Tech Lead is reviewing code changes
- Before approving pull requests
- Security-sensitive code is modified (auth, database, API endpoints)

### Manual Test

```bash
# Test basic mode
export SECURITY_SCAN_MODE=basic
bash .claude/skills/security-scan/scan.sh

# Test advanced mode
export SECURITY_SCAN_MODE=advanced
bash .claude/skills/security-scan/scan.sh
```

---

## Output Format

Results are saved to `coordination/security_scan.json`:

```json
{
  "scan_mode": "basic|advanced",
  "timestamp": "2025-11-07T20:00:00Z",
  "language": "python",
  "status": "success|partial|error",
  "tool": "bandit",
  "error": "",
  "critical_issues": 2,
  "high_issues": 5,
  "medium_issues": 12,
  "low_issues": 8,
  "info_issues": 4,
  "issues": [
    {
      "severity": "HIGH",
      "title": "SQL Injection",
      "file": "auth.py",
      "line": 45,
      "description": "String interpolation in SQL query",
      "recommendation": "Use parameterized queries"
    }
  ]
}
```

### Status Field Values

- **success**: Scan completed without errors
- **partial**: Scan completed but some tools failed (results may be incomplete)
- **error**: Scan failed completely (tool installation failed or critical error)

**⚠️ IMPORTANT**: Always check the `status` field before interpreting results. An empty issues array with `status: "error"` means the scan failed, NOT that the code is secure.

---

## Installation Requirements

### Python Projects

```bash
pip install bandit
pip install semgrep  # Advanced mode only
```

### JavaScript Projects

```bash
npm install  # npm audit built-in
npm install --save-dev eslint-plugin-security  # Advanced mode only
```

### Go Projects

```bash
go install github.com/securego/gosec/v2/cmd/gosec@latest
```

### Ruby Projects

```bash
gem install brakeman
```

### Java Projects

**Maven** (`pom.xml`):
```xml
<plugin>
  <groupId>com.github.spotbugs</groupId>
  <artifactId>spotbugs-maven-plugin</artifactId>
  <version>4.8.0</version>
  <dependencies>
    <dependency>
      <groupId>com.h3xstream.findsecbugs</groupId>
      <artifactId>findsecbugs-plugin</artifactId>
      <version>1.12.0</version>
    </dependency>
  </dependencies>
</plugin>

<!-- Advanced mode: OWASP Dependency Check -->
<plugin>
  <groupId>org.owasp</groupId>
  <artifactId>dependency-check-maven</artifactId>
  <version>9.0.0</version>
</plugin>
```

**Gradle** (`build.gradle`):
```gradle
plugins {
  id 'com.github.spotbugs' version '6.0.0'
}

dependencies {
  spotbugsPlugins 'com.h3xstream.findsecbugs:findsecbugs-plugin:1.12.0'
}

// Advanced mode: OWASP Dependency Check
apply plugin: 'org.owasp.dependencycheck'
```

**Semgrep** (Advanced mode):
```bash
pip install semgrep  # For Java static analysis
```

---

## Implementation

See `scan.sh` (bash) or `scan.ps1` (PowerShell) for full implementation details.

---

## Interpreting Results

### Critical Issues (MUST FIX)
- SQL injection
- Authentication bypasses
- Hardcoded secrets/credentials
- Remote code execution vulnerabilities

### High Issues (SHOULD FIX)
- XSS vulnerabilities
- Insecure cryptography
- Path traversal
- Missing authentication checks

### Medium Issues (GOOD TO FIX)
- Weak random number generation
- Missing CSRF protection
- Insecure file permissions

### Low/Info Issues (OPTIONAL - Advanced mode only)
- Code smells with security implications
- Deprecated functions
- Best practice recommendations

---

## Progressive Analysis

This Skill works in concert with the Tech Lead model escalation:

```
Revision 0-1: Basic scan (fast) + Tech Lead (Sonnet)
Revision 2:   Advanced scan (comprehensive) + Tech Lead (Sonnet)
Revision 3+:  Advanced scan + Tech Lead (Opus)
```

Progressive intelligence as issues persist.

---

## Troubleshooting

**Issue:** Tool not found (bandit, semgrep, etc.)

**Solution:** The script will attempt to install missing tools automatically. If it fails, manually install:
```bash
# Python
pip install bandit semgrep

# JavaScript
# npm audit is built-in, no installation needed

# Go
go install github.com/securego/gosec/v2/cmd/gosec@latest
```

**Issue:** Scan hangs or takes too long

**Solution:**
- Basic mode should complete in <10s. If it hangs, check for large codebases.
- Advanced mode can take 30-60s, which is normal.
- For very large projects, consider excluding vendor/node_modules directories.

**Issue:** False positives

**Solution:**
- Create `.bandit` config file to exclude false positives
- Use inline comments: `# nosec` (bandit) or `// nosemgrep` (semgrep)
- Configure tool-specific ignore files

---

## Configuration

### Custom Security Rules

Create `.claude/skills/security-scan/custom-rules/` directory with project-specific rules:

**Example: custom-sql-check.yaml (semgrep)**
```yaml
rules:
  - id: custom-sql-injection
    pattern: execute($SQL)
    message: Potential SQL injection
    severity: ERROR
```

### Exclude Paths

Create `.claude/skills/security-scan/exclude-paths.txt`:
```
vendor/
node_modules/
test/
```

---

## Credits

This Skill uses industry-standard security tools:
- **bandit**: Python security scanner (PyCQA)
- **semgrep**: Multi-language static analysis (r2c/Semgrep)
- **gosec**: Go security checker
- **npm audit**: JavaScript dependency auditor (npm)
- **brakeman**: Ruby on Rails security scanner
- **SpotBugs**: Java bytecode analyzer with Find Security Bugs plugin
- **OWASP Dependency Check**: Dependency vulnerability scanner (Java, JS, Python)
