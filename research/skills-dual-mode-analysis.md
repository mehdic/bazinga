# Skills Dual-Mode Analysis: Basic vs Advanced

**Date:** 2025-11-07
**Question:** Should Skills have basic (default) and advanced (iteration) modes?
**Analysis Type:** Critical evaluation of time savings vs complexity

---

## Executive Summary

**Recommendation:** Implement dual-mode ONLY for Security Scanner

| Skill | Dual-Mode? | Time Savings | Complexity | Value | Priority |
|-------|-----------|--------------|------------|-------|----------|
| **Security Scanner** | ✅ **YES** | 🔥 HIGH (20-50s) | Low | High | **P0** |
| **Coverage Reporter** | ⚠️ MAYBE | Medium (10-15s) | Medium | Medium | P2 |
| **Linting Suite** | ❌ NO | Low (3-5s) | Low | Low | Skip |
| **Complexity Analyzer** | ❌ NO | Low (5-10s) | Low | Low | Skip |

**Key Insight:** Only Security Scanner has significant time savings (20-50s). Others are already fast enough that dual-mode adds complexity without meaningful benefit.

---

## Critical Analysis by Skill

### 1. Security Scanner ⭐⭐⭐⭐⭐ **IMPLEMENT DUAL-MODE**

#### Basic Mode (First Review - Default)

**What it does:**
```bash
# Fast scan focusing on critical issues
- bandit -ll (high/medium severity only)
- Common vulnerabilities: SQL injection, XSS, hardcoded secrets
- Dependency check: npm audit --audit-level=high
- Skip slow deep analysis
```

**Time:** 5-10 seconds
**Output:** High/medium severity issues only

**Example output:**
```json
{
  "critical_issues": 2,
  "high_issues": 5,
  "scan_mode": "basic",
  "message": "Found 7 high-priority security issues. Run advanced scan for comprehensive analysis."
}
```

---

#### Advanced Mode (Iteration 2+ - After Issues Found)

**What it does:**
```bash
# Comprehensive deep scan
- bandit (all severities including low/info)
- semgrep --config=auto (all security patterns)
- Deep dependency analysis (full vulnerability graph)
- Historical vulnerability patterns for this codebase
- Custom security rules (project-specific)
- Timing attack detection
- Race condition analysis
- Logic flaw patterns
```

**Time:** 30-60 seconds
**Output:** Complete security analysis with low-severity issues, patterns, trends

**Example output:**
```json
{
  "critical_issues": 2,
  "high_issues": 5,
  "medium_issues": 12,
  "low_issues": 8,
  "info_issues": 15,
  "scan_mode": "advanced",
  "patterns_detected": ["SQL injection in 3 files", "Weak cryptography"],
  "historical_context": "auth.py has had 4 security fixes in past 6 months",
  "recommendations": ["Consider using parameterized queries library-wide"]
}
```

---

#### Why Dual-Mode Makes Sense

**Time Savings:**
- ✅ **20-50 seconds saved** on first review
- ✅ 90% of issues caught in basic mode
- ✅ Fast feedback loop for developers

**Value:**
- ✅ Reduces noise (no low-severity warnings on first pass)
- ✅ Progressive disclosure (simple → complex)
- ✅ Aligns with revision tracking (basic → advanced → opus escalation)
- ✅ Teaches developers incrementally

**When to use Advanced:**
```python
if revision_count >= 2:
    security_mode = "advanced"
    # Developer has iterated twice, persistent security issues
    # Time for deep analysis
```

**Verdict:** ⭐⭐⭐⭐⭐ **Absolutely worth it** - Significant time savings, clear value

---

### 2. Test Coverage Reporter ⚠️ **MAYBE IMPLEMENT**

#### Basic Mode (First Review)

**What it does:**
```bash
# Quick coverage summary
pytest --cov=. --cov-report=term --quiet
# Show only:
- Overall coverage %
- Files with <80% coverage (simple threshold)
- Pass/fail based on threshold
```

**Time:** 10-15 seconds
**Output:** Simple percentage and problem files

**Example output:**
```
Coverage: 67%
Files below 80%:
- auth.py (45%)
- payment.py (52%)
- api/routes.py (71%)

Status: BELOW_THRESHOLD
```

---

#### Advanced Mode (Iteration 2+)

**What it does:**
```bash
# Comprehensive coverage analysis
pytest --cov=. --cov-report=html --cov-report=json
# Analyze:
- Line-by-line uncovered code
- Branch coverage (not just line coverage)
- Historical coverage trends (improving or degrading?)
- Uncovered critical paths (auth, payment, data handling)
- Test quality analysis (assertion density)
- Missing edge case coverage
```

**Time:** 20-30 seconds
**Output:** Detailed report with specific uncovered lines, branches, critical paths

**Example output:**
```
Coverage: 67%

Critical Uncovered Paths:
- auth.py:45-52 (token validation error handling)
- payment.py:89-103 (refund logic edge cases)

Branch Coverage:
- Overall: 52% (vs 67% line coverage)
- auth.py: 8 of 15 branches uncovered

Historical Trend:
- 2 weeks ago: 71%
- Today: 67%
- Status: DEGRADING ⚠️

Recommendations:
- Add tests for error handling in token validation
- Test refund logic with edge cases (partial refunds, expired orders)
```

---

#### Why Dual-Mode is Questionable

**Time Savings:**
- ⚠️ **10-15 seconds saved** - Marginal
- ⚠️ Coverage tests are already relatively fast
- ⚠️ Most projects run in <20s total

**Value:**
- ✅ Reduces noise on first pass
- ✅ Detailed analysis helps on iterations
- ⚠️ But developers need to know WHAT to test, not just percentage

**Critical Question:** Is 10-15s savings worth the complexity?

**Verdict:** ⚠️ **Marginal benefit** - Implement only if time budget critical, or if coverage is VERY slow (>30s)

---

### 3. Linting Suite ❌ **DON'T IMPLEMENT DUAL-MODE**

#### Why NOT?

**Time Savings:**
- ❌ **Only 3-5 seconds saved**
- ❌ Modern linters are already extremely fast
- ❌ Diminishing returns

**Analysis:**
```bash
# Basic mode would be:
ruff check --select=E,F  # Errors only: 2-5s

# Advanced mode would be:
ruff check  # All rules: 5-10s

# Time saved: 3-5 seconds ← NOT WORTH IT
```

**Alternative:** Always run full linting (it's already fast), just **filter the output**:

```bash
# Always scan everything
ruff check . --output-format=json > lint_results.json

# On first review (revision_count < 2):
jq 'select(.severity == "error")' lint_results.json

# On iteration (revision_count >= 2):
cat lint_results.json  # Show all
```

**Verdict:** ❌ **Not worth complexity** - Linters are already fast, just filter reporting

---

### 4. Complexity Analyzer ❌ **DON'T IMPLEMENT DUAL-MODE**

#### Why NOT?

**Reasoning:**
- ❌ Optional feature (lower priority)
- ❌ Time savings minimal (5-10s)
- ❌ Keep optional features simple

**If implemented, keep single mode:**
```bash
# Just run with reasonable threshold
radon cc . --min C  # Functions with complexity >10
```

**Verdict:** ❌ **Keep simple** - Don't add complexity to optional feature

---

---

## Trigger Mechanisms

### Option 1: Based on Revision Count (RECOMMENDED)

**Logic:**
```python
if revision_count >= 2:
    scan_mode = "advanced"
else:
    scan_mode = "basic"
```

**Pros:**
- ✅ Simple, clean logic
- ✅ Aligns with opus escalation (revision 3)
- ✅ Uses existing tracking
- ✅ Progressive: basic → advanced → opus

**Cons:**
- ⚠️ Always triggers at revision 2 (might be too early/late for some cases)

**Verdict:** ⭐⭐⭐⭐⭐ **Best approach** - Simple, predictable, aligns with system

---

### Option 2: Based on Previous Scan Results

**Logic:**
```python
if previous_security_scan.critical_issues > 0:
    scan_mode = "advanced"
else:
    scan_mode = "basic"
```

**Pros:**
- ✅ Intelligent - only go deep if problems found
- ✅ Saves time when code is clean

**Cons:**
- ❌ More complex state tracking
- ❌ Risk: might miss issues if basic scan not thorough enough
- ❌ Unpredictable behavior

**Verdict:** ⭐⭐⭐ **Too complex** - Added intelligence not worth the complexity

---

### Option 3: Always Basic, Then Advanced If Issues Found

**Logic:**
```python
run_basic_scan()
if basic_scan.has_critical_issues:
    run_advanced_scan()
```

**Pros:**
- ✅ Progressive - start fast, go deep if needed
- ✅ Best of both worlds

**Cons:**
- ❌ Two scans = MORE time if issues found
- ❌ More complex workflow
- ❌ Wastes time re-scanning

**Verdict:** ⭐⭐ **Counterproductive** - Defeats purpose of saving time

---

---

## Implementation Recommendations

### Recommended: Implement ONLY for Security Scanner

**Mode Selection Logic:**

```markdown
## In orchestrator.md (before spawning Tech Lead):

```python
# Read revision count
group_status = read_file("bazinga/group_status.json")
revision_count = group_status.get(group_id, {}).get("revision_count", 0)

# Determine security scan mode
if revision_count >= 2:
    security_scan_mode = "advanced"
else:
    security_scan_mode = "basic"

# Pass mode to Skill (via environment or parameter)
export SECURITY_SCAN_MODE=$security_scan_mode
```

---

**Skill Implementation:**

`.claude/skills/security-scan/SKILL.md`:

```yaml
---
name: security-scan
description: "Run security vulnerability scans. Automatically uses basic mode (fast) for first review, advanced mode (comprehensive) for iterations. Use when reviewing code changes or before approval."
allowed-tools: [Bash, Read, Write]
---

# Security Scanning Skill

## Mode Selection

**Mode is automatically selected based on revision count:**

- **Basic Mode** (revision_count < 2): Fast scan, high/medium severity only (5-10s)
- **Advanced Mode** (revision_count >= 2): Comprehensive scan, all severities, deep analysis (30-60s)

## Basic Mode

**What runs:**
- Security vulnerabilities: High and medium severity only
- Tools: bandit -ll, npm audit --audit-level=high
- Patterns: SQL injection, XSS, hardcoded secrets, auth bypasses
- Output: Critical issues only

**Time:** 5-10 seconds

**Use case:** First code review, quick feedback

---

## Advanced Mode

**What runs:**
- Security vulnerabilities: ALL severities (high, medium, low, info)
- Tools: bandit (full), semgrep --config=auto, npm audit (full)
- Patterns: All security patterns + timing attacks + race conditions
- Historical analysis: Past vulnerabilities in changed files
- Custom rules: Project-specific security requirements
- Output: Complete security report with context

**Time:** 30-60 seconds

**Use case:** Code has been revised 2+ times, persistent security issues, need deep analysis

---

## Implementation

See `scan.sh` for full implementation.
```

---

**scan.sh Script:**

`.claude/skills/security-scan/scan.sh`:

```bash
#!/bin/bash
set -e

# Get mode from environment (default: basic)
MODE="${SECURITY_SCAN_MODE:-basic}"

echo "🔒 Security Scan Starting (Mode: $MODE)..."

# Detect language
if [ -f "pyproject.toml" ] || [ -f "setup.py" ]; then
    LANG="python"
elif [ -f "package.json" ]; then
    LANG="javascript"
elif [ -f "go.mod" ]; then
    LANG="go"
else
    LANG="unknown"
fi

echo "📋 Detected language: $LANG"

# Run scan based on mode
case $MODE in
    basic)
        echo "⚡ Running BASIC scan (fast, high/medium severity only)..."

        case $LANG in
            python)
                # Basic: High/medium severity only
                if ! command -v bandit &> /dev/null; then
                    pip install bandit --quiet
                fi
                bandit -r . -f json -o bazinga/security_scan.json -ll
                ;;
            javascript)
                # Basic: High severity only
                npm audit --audit-level=high --json > bazinga/security_scan.json
                ;;
            go)
                if ! command -v gosec &> /dev/null; then
                    go install github.com/securego/gosec/v2/cmd/gosec@latest
                fi
                gosec -severity high -fmt json -out bazinga/security_scan.json ./...
                ;;
        esac

        echo "✅ Basic security scan complete (5-10s)"
        ;;

    advanced)
        echo "🔍 Running ADVANCED scan (comprehensive, all severities)..."

        case $LANG in
            python)
                # Advanced: All severities + semgrep
                if ! command -v bandit &> /dev/null; then
                    pip install bandit --quiet
                fi
                if ! command -v semgrep &> /dev/null; then
                    pip install semgrep --quiet
                fi

                # Run bandit (all severities)
                bandit -r . -f json -o bazinga/bandit_full.json

                # Run semgrep (comprehensive patterns)
                semgrep --config=auto --json -o bazinga/semgrep.json

                # Combine results
                jq -s '.[0] + .[1]' bazinga/bandit_full.json bazinga/semgrep.json > bazinga/security_scan.json
                ;;

            javascript)
                # Advanced: Full npm audit + eslint security
                npm audit --json > bazinga/npm_audit.json

                if npm list | grep -q eslint-plugin-security; then
                    npx eslint . --plugin security --format json > bazinga/eslint_security.json
                fi

                # Combine
                jq -s '.[0] + .[1]' bazinga/npm_audit.json bazinga/eslint_security.json > bazinga/security_scan.json
                ;;

            go)
                if ! command -v gosec &> /dev/null; then
                    go install github.com/securego/gosec/v2/cmd/gosec@latest
                fi
                # All severities
                gosec -fmt json -out bazinga/security_scan.json ./...
                ;;
        esac

        echo "✅ Advanced security scan complete (30-60s)"
        ;;

    *)
        echo "❌ Invalid mode: $MODE (use 'basic' or 'advanced')"
        exit 1
        ;;
esac

# Parse results and add metadata
jq ". + {\"scan_mode\": \"$MODE\", \"timestamp\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\"}" \
    bazinga/security_scan.json > bazinga/security_scan_final.json

mv bazinga/security_scan_final.json bazinga/security_scan.json

echo "📊 Scan mode: $MODE"
```

---

---

## Time Analysis: Is It Worth It?

### Security Scanner Time Breakdown

**Scenario 1: Clean Code (No Issues)**

| Review | Mode | Time | Total Time |
|--------|------|------|------------|
| First review | Basic | 5s | **5s** |
| - | - | - | **DONE** |

**vs without dual-mode:**
| Review | Mode | Time | Total Time |
|--------|------|------|------------|
| First review | Full | 40s | **40s** |

**Time saved: 35 seconds** ✅

---

**Scenario 2: Issues Found, 3 Revisions**

| Review | Mode | Time | Total Time |
|--------|------|------|------------|
| First review | Basic | 5s | 5s |
| Revision 1 | Basic | 5s | 10s |
| Revision 2 | Advanced | 40s | 50s |
| Revision 3 | Advanced | 40s | **90s** |

**vs without dual-mode:**
| Review | Mode | Time | Total Time |
|--------|------|------|------------|
| First review | Full | 40s | 40s |
| Revision 1 | Full | 40s | 80s |
| Revision 2 | Full | 40s | 120s |
| Revision 3 | Full | 40s | **160s** |

**Time saved: 70 seconds** ✅

---

**Reality Check:**
- Average case: Save 20-35s per review cycle
- Worst case (many iterations): Save 60-100s total
- Best case (clean code): Save 35s

**Verdict:** ⭐⭐⭐⭐⭐ **Significant savings** - Absolutely worth implementing

---

### Coverage Reporter Time Breakdown

**Scenario: 3 Revisions**

| Review | Mode | Time | Total Time |
|--------|------|------|------------|
| First review | Basic | 10s | 10s |
| Revision 1 | Basic | 10s | 20s |
| Revision 2 | Advanced | 25s | 45s |
| Revision 3 | Advanced | 25s | **70s** |

**vs without dual-mode:**
| Review | Mode | Time | Total Time |
|--------|------|------|------------|
| First review | Full | 25s | 25s |
| Revision 1 | Full | 25s | 50s |
| Revision 2 | Full | 25s | 75s |
| Revision 3 | Full | 25s | **100s** |

**Time saved: 30 seconds over 4 reviews** = 7.5s per review

**Verdict:** ⚠️ **Marginal savings** - Only implement if team is very time-sensitive

---

---

## Critical Insights

### What Makes a Good Dual-Mode Candidate?

**Required:**
- ✅ **Significant time difference** (>20s between modes)
- ✅ **Basic mode catches 80%+ of issues**
- ✅ **Advanced mode provides genuinely different analysis** (not just "more of the same")

**Nice to have:**
- ✅ Progressive disclosure (simple → complex)
- ✅ Aligns with iteration count
- ✅ Low implementation complexity

**Disqualifiers:**
- ❌ Time savings <10s
- ❌ Basic mode might miss critical issues
- ❌ High implementation complexity

---

### Alternative: Smart Output Filtering

**Instead of running different scans, run FULL scan but filter OUTPUT:**

```bash
# ALWAYS run comprehensive scan
bandit -r . -f json -o full_results.json

# On first review (revision < 2): Filter to high/medium
if [ $revision_count -lt 2 ]; then
    jq 'select(.issue_severity=="HIGH" or .issue_severity=="MEDIUM")' \
        full_results.json > bazinga/security_scan.json
else
    # Show all
    cp full_results.json bazinga/security_scan.json
fi
```

**Pros:**
- ✅ No risk of missing issues
- ✅ Simpler logic
- ✅ Just changes REPORTING, not SCANNING

**Cons:**
- ❌ **NO TIME SAVINGS** (still runs full scan)
- ❌ Defeats the purpose

**Verdict:** ❌ **Not recommended** - If we're going to run full scan anyway, might as well report everything

---

---

## Final Recommendations

### Implement Dual-Mode: Security Scanner ONLY

**Configuration:**

1. **Trigger:** revision_count >= 2
2. **Basic Mode:** High/medium severity, common patterns, 5-10s
3. **Advanced Mode:** All severities, deep analysis, semgrep, 30-60s
4. **Pass mode via:** Environment variable `SECURITY_SCAN_MODE`

**Implementation Priority:** **P0** (High value, clear benefit)

---

### Skip Dual-Mode: Coverage, Linting, Complexity

**Reasoning:**
- Time savings too small (<15s)
- Added complexity not justified
- Alternative: Filter output if needed

**Implementation:** Keep single-mode (simple, fast)

---

### Progressive Analysis Ladder

**Complete system progression:**

```
Code Review Workflow:

First Review (revision_count = 0):
├─ Security: BASIC mode (5s)
├─ Coverage: Standard (15s)
├─ Linting: Standard (5s)
└─ Tech Lead: SONNET model

Revision 1 (revision_count = 1):
├─ Security: BASIC mode (5s)
├─ Coverage: Standard (15s)
├─ Linting: Standard (5s)
└─ Tech Lead: SONNET model

Revision 2 (revision_count = 2):
├─ Security: ADVANCED mode (40s) ← Escalates
├─ Coverage: Standard (15s)
├─ Linting: Standard (5s)
└─ Tech Lead: SONNET model

Revision 3 (revision_count = 3):
├─ Security: ADVANCED mode (40s)
├─ Coverage: Standard (15s)
├─ Linting: Standard (5s)
└─ Tech Lead: OPUS model ← Escalates
```

**Progressive intelligence:** As issues persist, both Skills AND model escalate

---

---

## Implementation Checklist

### Phase 1: Security Scanner Dual-Mode

- [ ] Update `security-scan/SKILL.md` with mode documentation
- [ ] Modify `scan.sh` to accept MODE parameter
- [ ] Add basic mode logic (high/medium only)
- [ ] Add advanced mode logic (full semgrep)
- [ ] Create PowerShell version `scan.ps1`
- [ ] Update orchestrator to set `SECURITY_SCAN_MODE` based on revision_count
- [ ] Test basic mode (should run in 5-10s)
- [ ] Test advanced mode (should run in 30-60s)
- [ ] Verify mode selection logic (revision_count >= 2)
- [ ] Document in README

### Phase 2: Validation

- [ ] Test on Python project
- [ ] Test on JavaScript project
- [ ] Measure actual time savings
- [ ] Verify basic mode catches critical issues
- [ ] Verify advanced mode provides value
- [ ] User acceptance testing

---

---

## Conclusion

**Critical Analysis Summary:**

✅ **DO implement dual-mode for Security Scanner**
- Time savings: 20-50s per review cycle
- Value: High (security is critical)
- Complexity: Low (just different flags)
- ROI: Excellent

❌ **DON'T implement dual-mode for others**
- Coverage: Only 10-15s savings, not worth complexity
- Linting: Only 3-5s savings, negligible
- Complexity: Optional feature, keep simple

**The principle:** Only add complexity when time savings are **significant** (>20s) and implementation is **simple**.

Security Scanner meets both criteria. Others don't.

---

**Next Action:** Implement dual-mode for Security Scanner only, skip for others.

