# Tech Lead Capabilities & Skills Analysis

**Date:** 2025-11-07
**Topic:** Enhancing Tech Lead Agent with Automated Capabilities and Claude Code Skills
**Status:** Research & Recommendations

---

## Table of Contents

1. [Original Question](#original-question)
2. [Proposed Capabilities](#proposed-capabilities)
3. [Claude Code Skills Research](#claude-code-skills-research)
4. [Critical Analysis: Skills vs Other Approaches](#critical-analysis)
5. [Implementation Recommendations](#implementation-recommendations)
6. [Next Steps](#next-steps)

---

## Original Question

**User asked:** "What capabilities or skill could we give to the tech lead to do a better job?"

**Context:** The Tech Lead agent currently performs manual code reviews. We explored ways to enhance it with automated analysis tools and capabilities.

---

## Proposed Capabilities

### Category 1: Automated Analysis & Tooling

#### 1. Static Analysis Suite ⭐⭐⭐⭐⭐
**Purpose:** Run automated code quality and security checks

**Tools by Language:**
- **Python:** bandit, semgrep, ruff, pylint, flake8, mypy
- **JavaScript/TypeScript:** eslint, prettier, npm audit
- **Ruby:** rubocop
- **Go:** golangci-lint

**Value:** Catch 60-70% of common issues automatically (SQL injection, XSS, etc.)

---

#### 2. Code Complexity Metrics ⭐⭐⭐⭐
**Purpose:** Objectively identify code that needs refactoring

**Tools:**
- radon (Python cyclomatic complexity)
- code-complexity (multi-language)
- SonarQube metrics

**Metrics:**
- Functions with complexity > 10 (hard to test)
- Files with > 300 lines (should be split)
- Duplicate code detection

**Value:** Objective data on code maintainability

---

#### 3. Test Coverage Analysis ⭐⭐⭐⭐⭐
**Purpose:** Know exactly what's tested vs risky

**Tools:**
- coverage.py (Python)
- jest --coverage (JavaScript)
- go test -cover (Go)

**Metrics:**
- Line coverage %
- Branch coverage %
- Uncovered critical paths

**Value:** Clear visibility into testing gaps

---

#### 4. Performance Profiling ⭐⭐
**Purpose:** Catch performance issues before production

**Tools:**
- cProfile (Python)
- perf, flamegraph (system-wide)
- memory_profiler (memory leaks)
- py-spy (production profiling)

**Value:** Identify bottlenecks early

**Note:** Context-specific, expensive, not suitable for every review

---

### Category 2: Enhanced Review Intelligence

#### 5. Codebase Context Search ⭐⭐⭐
**Purpose:** Understand full impact of changes

**Capabilities:**
- Grep across entire codebase for similar patterns
- Find all usages of a function/class
- Identify files that frequently change together
- Search git history for context

**Value:** Prevent breaking changes, understand dependencies

---

#### 6. Git History Analysis ⭐⭐⭐
**Purpose:** Identify risky areas and patterns

**Analyses:**
```bash
# Hotspot detection
git log --all --format='%aN' | sort | uniq -c | sort -rn

# Files changed most frequently
git log --stat --oneline | grep "filename"

# Files with most bug fixes
git log --grep="fix\|bug" --oneline -- file.py
```

**Value:** Know which files are risky, who has expertise

---

#### 7. Dependency Impact Analysis ⭐⭐
**Purpose:** Understand downstream effects

**Capabilities:**
- What modules import this?
- What tests cover this code path?
- What APIs depend on this function?
- Breaking change detection

**Value:** Prevent accidental breakage

**Note:** Complex reasoning required, better as agent task than automated check

---

### Category 3: Knowledge & Memory

#### 8. Project-Specific Memory ⭐⭐⭐
**Purpose:** Learn from history, track patterns

**Structure:**
```json
{
  "tech_debt_register": [
    {"file": "auth.py", "issue": "needs refactoring", "priority": "high"}
  ],
  "past_issues": [
    {"pattern": "SQL injection", "occurrences": 3, "last_seen": "2024-01"}
  ],
  "architecture_decisions": [
    {"decision": "Use JWT not sessions", "reason": "scalability", "date": "..."}
  ]
}
```

**Value:** Enforce decisions consistently, learn patterns

---

#### 9. Best Practices Database ⭐⭐⭐
**Purpose:** Consistent enforcement of standards

**Example:**
```yaml
python_best_practices:
  - "Use context managers for file operations"
  - "Prefer pathlib over os.path"
  - "Use typing for public APIs"

security_patterns:
  - "Never use pickle on untrusted data"
  - "Always parameterize SQL queries"
  - "Validate all user inputs"
```

**Value:** Consistent code quality across team

---

### Category 4: Proactive Capabilities

#### 10. Automated Fix Suggestions ⭐⭐⭐
**Purpose:** Not just identify, but propose fixes

**Example:**
```python
# Before
cursor.execute(f"SELECT * FROM users WHERE id={user_id}")

# Tech Lead suggests
cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
```

**Value:** Faster iteration, educational for developers

**Note:** This is already Claude's natural strength - may not need special implementation

---

#### 11. Architectural Pattern Detection ⭐⭐⭐
**Purpose:** Elevate code quality to senior engineer level

**Detects:**
- God objects (classes doing too much)
- Circular dependencies
- Missing abstractions
- Tight coupling
- Leaky abstractions

**Suggests:**
- "Consider using Strategy pattern here"
- "This could benefit from Factory pattern"
- "Extract interface for testability"

**Value:** Better system design

---

#### 12. Comparative Analysis ⭐⭐⭐
**Purpose:** Ensure consistency across codebase

**Capabilities:**
- "Similar function in auth_v2.py handles this better"
- "Other endpoints use middleware for this"
- "Previous implementation had edge case handling"

**Value:** Learn from existing code

---

---

## Claude Code Skills Research

### What Are Skills?

**Definition:** Skills are modular capabilities that extend Claude's functionality through organized folders containing instructions, scripts, and resources.

**Key Characteristics:**
- **Model-invoked:** Claude autonomously decides when to use them (unlike commands which are user-invoked)
- **Structure:** `SKILL.md` + optional supporting files (scripts, templates, data)
- **Storage:** `.claude/skills/` (project) or `~/.claude/skills/` (personal)
- **Progressive disclosure:** Claude only reads files when needed
- **Team shareable:** Project skills shared via git

### SKILL.md Format

```yaml
---
name: security-scan
description: "Run security vulnerability scan on Python code using bandit. Use when reviewing code for security issues or before approving changes."
allowed-tools: [Bash, Read, Write]
---

# Security Scanning Skill

## When to Use

Use this skill when:
- Reviewing code changes for security vulnerabilities
- Before approving any pull request
- When suspicious code patterns are detected

## Instructions

[Detailed instructions here]
```

### When to Use Skills

**✅ Use Skills for:**
- Standardized, repeatable workflows
- Scriptable automated checks
- Team-wide consistency requirements
- Cross-project applicability
- Clear trigger conditions (when Claude should auto-invoke)

**❌ Don't Use Skills for:**
- Complex orchestration (use agents)
- One-off tasks (use commands)
- Deep reasoning tasks (use enhanced prompts)
- Variable/context-specific workflows

**The Test:** *"Would this run the same way every time across all projects?"*
- If **YES** → Skill candidate
- If **NO** → Agent/Prompt enhancement

---

## Critical Analysis

### Skills Suitability Evaluation

| Capability | Skill Score | Reasoning | Better Approach |
|------------|-------------|-----------|-----------------|
| **Static Analysis Suite** | ⭐⭐⭐⭐⭐ | Standardized, scriptable, auto-invoke, team-critical | **SKILL** |
| **Test Coverage** | ⭐⭐⭐⭐⭐ | Objective metrics, repeatable, auto-invoke | **SKILL** |
| **Linting Suite** | ⭐⭐⭐⭐⭐ | Standardized checks, auto-invoke | **SKILL** |
| **Code Complexity** | ⭐⭐⭐⭐ | Helpful metrics, scriptable, but not critical | **SKILL** (lower priority) |
| **Git History Analysis** | ⭐⭐⭐ | Scriptable, but results vary, unclear trigger | Script in `scripts/` |
| **Performance Profiling** | ⭐⭐ | Not repeatable, context-specific, expensive | Agent task (explicit) |
| **Automated Fix Suggestions** | ⭐ | Not standardized, already built-in Claude behavior | Enhanced prompt |
| **Architectural Pattern Detection** | ⭐ | Complex reasoning, LLM task not script task | Enhanced prompt |
| **Project Memory** | ⭐⭐ | State management complex, not static | YAML files Tech Lead reads |
| **Codebase Context Search** | ⭐ | Already built-in (Grep, Glob tools) | Use existing tools |
| **Dependency Impact** | ⭐⭐ | Complex graph analysis, context-specific | Agent task |
| **Best Practices DB** | ⭐⭐⭐ | Could be YAML files | Static knowledge base |

### Detailed Analysis

#### ✅ EXCELLENT Skill Candidates

**1. Static Analysis Suite (Security Scanner)** ⭐⭐⭐⭐⭐

**Why Perfect for Skills:**
- ✅ Standardized workflow: Always run same security checks
- ✅ Repeatable: Same process every code review
- ✅ Auto-invoke worthy: "When reviewing code" triggers automatically
- ✅ Can include scripts: Package bandit/ruff/eslint wrappers
- ✅ Team shareable: Everyone uses same security standards
- ✅ Cross-project: Security checks apply universally

**Implementation:**
```yaml
---
name: security-analyzer
description: "Automatically run security vulnerability scans when reviewing code. Detects SQL injection, XSS, insecure dependencies. Use before approving any code changes."
allowed-tools: [Bash, Read, Write, Grep]
---
```

**Reality Check:** **Perfect fit** - This is exactly what Skills were designed for.

---

**2. Test Coverage Reporter** ⭐⭐⭐⭐⭐

**Why Perfect:**
- ✅ Standardized: Always check coverage the same way
- ✅ Auto-invoke: "When reviewing tests" activates automatically
- ✅ Includes scripts: Coverage report parsers
- ✅ Team consistency: Everyone sees same metrics
- ✅ Output templates: Generate formatted coverage reports

**Implementation:**
```yaml
---
name: coverage-reporter
description: "Generate test coverage reports and identify untested code. Use when reviewing tests or before approving changes. Supports Python (pytest-cov), JavaScript (jest), Go (go test -cover)."
allowed-tools: [Bash, Read, Write]
---
```

**Reality Check:** **Perfect fit** - Objective, scriptable, repeatable.

---

**3. Linting Suite** ⭐⭐⭐⭐⭐

**Why Perfect:**
- ✅ Standardized: Run language-appropriate linters
- ✅ Auto-invoke: "When reviewing code quality"
- ✅ Scriptable: eslint, ruff, pylint wrappers
- ✅ Quick wins: Immediate feedback

**Implementation:**
```yaml
---
name: lint-checker
description: "Run code quality linters (Python: ruff, JS: eslint, Go: golangci-lint). Use when reviewing code for style and quality issues."
allowed-tools: [Bash, Read]
---
```

**Reality Check:** **Perfect fit** - Standard practice every review.

---

**4. Code Complexity Analyzer** ⭐⭐⭐⭐

**Why It Works:**
- ✅ Standardized: Cyclomatic complexity is algorithmic
- ✅ Repeatable: Same metrics every time
- ✅ Scriptable: radon/lizard tools
- ✅ Objective: No judgment needed

**But:**
- ⚠️ Less critical than security
- ⚠️ Might not need auto-invoke every time

**Reality Check:** **Good fit, but lower priority** - Nice to have, not must-have.

---

#### ⚠️ MARGINAL Skill Candidates

**5. Git History Analysis** ⭐⭐⭐

**Pros:**
- ✅ Can be scripted (git log parsing)
- ✅ Repeatable (hotspot detection)

**Cons:**
- ⚠️ Results vary by project/timeline
- ⚠️ Often needs manual interpretation
- ❌ Not clearly "auto-invoke worthy" - when would Claude know to check git history?

**Reality Check:** **Could work as Skill, but marginal** - Better as explicit script Tech Lead calls when needed.

**Better Approach:** Create `scripts/git-analysis.sh` that Tech Lead runs explicitly.

---

#### ❌ POOR Skill Candidates

**6. Performance Profiling** ⭐⭐

**Why NOT:**
- ❌ Not repeatable: Different code paths need different profiling
- ❌ Context-specific: Need to know what to profile
- ❌ Requires judgment: When is perf testing needed?
- ❌ Expensive: Can't auto-invoke for every review
- ❌ State management: Need to run code, collect data, analyze

**Reality Check:** **Bad fit for Skills** - Better as explicit agent task or Tech Lead instruction.

---

**7. Automated Fix Suggestions** ⭐

**Why NOT:**
- ❌ Not standardized: Each issue needs unique fix
- ❌ Complex reasoning: LLM strength, not script strength
- ❌ Already built-in: Claude already does this naturally
- ❌ State management: Needs context across conversation

**Reality Check:** **Terrible fit** - This is just normal Claude capability, doesn't need special packaging.

---

**8. Architectural Pattern Detection** ⭐

**Why NOT:**
- ❌ Requires deep code understanding (LLM task, not script)
- ❌ Not standardized (every codebase different)
- ❌ Needs orchestration with other analyses
- ❌ Complex reasoning about trade-offs

**Reality Check:** **Terrible fit** - Should stay in Tech Lead agent's main prompt as enhanced instructions.

---

**9. Project Memory / Best Practices Database** ⭐⭐

**Questionable because:**
- ⚠️ Could be Skill for querying knowledge base
- ❌ State management is complex
- ❌ Needs to evolve over time (not static)
- ❌ Context-dependent interpretation

**Reality Check:** **Marginal** - Better as YAML files that Tech Lead reads via Read tool.

**Better Approach:**
```yaml
# .claude/tech_lead/best_practices.yaml
python:
  - rule: "Use context managers for files"
    example: "with open('file.txt') as f:"

security:
  - rule: "Parameterize SQL queries"
    bad: "cursor.execute(f'SELECT * FROM users WHERE id={id}')"
    good: "cursor.execute('SELECT * FROM users WHERE id=?', (id,))"
```

---

**10. Codebase Context Search** ⭐

**Why NOT:**
- ❌ Already built-in (Grep, Glob tools)
- ❌ Not a workflow - it's a tool
- ❌ Context-dependent queries

**Reality Check:** **Not a Skill** - Just use existing Grep/Glob tools in Tech Lead instructions.

---

**11. Dependency Impact Analysis** ⭐⭐

**Why NOT:**
- ❌ Complex graph analysis (needs LLM reasoning)
- ❌ Context-specific (different for each change)
- ❌ Not repeatable workflow

**Reality Check:** **Not a good fit** - This is a Tech Lead agent reasoning task, not a scriptable workflow.

---

---

## Implementation Recommendations

### Phase 1: Core Security & Quality Skills

**Priority: CRITICAL**
**Timeline: Week 1**

Create 3 essential Skills:

#### Skill 1: Security Scanner

**Location:** `.claude/skills/security-scan/`

**Files:**
```
.claude/skills/security-scan/
├── SKILL.md
├── scan.sh          # Language detection + tool wrapper
├── scan.ps1         # PowerShell version
└── report.md        # Output template
```

**SKILL.md:**
```yaml
---
name: security-scan
description: "Run comprehensive security vulnerability scans when reviewing code. Detects SQL injection, XSS, credential leaks, insecure dependencies. Automatically use before approving any code changes or pull requests."
allowed-tools: [Bash, Read, Write, Grep]
---

# Security Scanning Skill

## When to Use

This skill automatically activates when:
- Tech Lead is reviewing code changes
- Before approving pull requests
- When security-sensitive code is modified (auth, database, API endpoints)

## Scan Process

1. **Detect project language** (Python/JavaScript/Go/Ruby)
2. **Run appropriate security scanner:**
   - Python: bandit + pip-audit
   - JavaScript: npm audit + eslint-plugin-security
   - Go: gosec
   - Ruby: brakeman
3. **Generate structured report** with severity levels
4. **Flag critical issues** that block approval

## Instructions

[See scan.sh for implementation details]

## Output Format

Security scan results are saved to: `bazinga/security_scan_results.json`
```

**scan.sh:**
```bash
#!/bin/bash
# Security scanner wrapper

set -e

echo "🔒 Security Scan Starting..."

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

# Run appropriate scanner
case $LANG in
    python)
        if ! command -v bandit &> /dev/null; then
            echo "⚠️ bandit not installed. Installing..."
            pip install bandit --quiet
        fi
        bandit -r . -f json -o bazinga/security_scan.json -ll
        ;;
    javascript)
        npm audit --json > bazinga/security_scan.json
        ;;
    go)
        if ! command -v gosec &> /dev/null; then
            echo "⚠️ gosec not installed. Installing..."
            go install github.com/securego/gosec/v2/cmd/gosec@latest
        fi
        gosec -fmt json -out bazinga/security_scan.json ./...
        ;;
esac

echo "✅ Security scan complete"
```

---

#### Skill 2: Coverage Reporter

**Location:** `.claude/skills/test-coverage/`

**SKILL.md:**
```yaml
---
name: test-coverage
description: "Generate comprehensive test coverage reports. Use when reviewing tests or before approving code changes. Identifies untested code paths and low-coverage areas. Supports Python, JavaScript, Go."
allowed-tools: [Bash, Read, Write]
---

# Test Coverage Analysis Skill

## When to Use

Auto-activate when:
- Reviewing test files
- Before approving code changes
- Developer claims "added tests"

## Coverage Process

1. Detect test framework
2. Run coverage analysis
3. Generate report with uncovered lines
4. Flag critical code with <80% coverage

## Output

Saves to: `bazinga/coverage_report.json`
```

---

#### Skill 3: Lint Checker

**Location:** `.claude/skills/lint-check/`

**SKILL.md:**
```yaml
---
name: lint-check
description: "Run code quality linters for style, complexity, and best practices. Use when reviewing any code changes. Supports Python (ruff), JavaScript (eslint), Go (golangci-lint)."
allowed-tools: [Bash, Read]
---

# Code Linting Skill

## When to Use

Auto-activate for all code reviews to check:
- Code style consistency
- Common anti-patterns
- Best practice violations
- Import organization

## Output

Saves to: `bazinga/lint_results.json`
```

---

### Phase 2: Supporting Infrastructure

**Priority: HIGH**
**Timeline: Week 1**

#### 1. Tool Installation Check

Create `scripts/check-tools.sh`:
```bash
#!/bin/bash
# Check if analysis tools are installed, offer to install

check_tool() {
    TOOL=$1
    INSTALL_CMD=$2

    if ! command -v $TOOL &> /dev/null; then
        echo "⚠️ $TOOL not installed"
        echo "Install with: $INSTALL_CMD"
        return 1
    fi
    echo "✅ $TOOL installed"
    return 0
}

check_tool "bandit" "pip install bandit"
check_tool "ruff" "pip install ruff"
check_tool "pytest" "pip install pytest pytest-cov"
```

#### 2. Results Aggregator

Create `scripts/aggregate-analysis.sh`:
```bash
#!/bin/bash
# Aggregate all analysis results into one report for Tech Lead

cat > bazinga/analysis_summary.md <<EOF
# Code Analysis Summary

## Security Scan
$(cat bazinga/security_scan.json | jq -r '.results | length') issues found

## Test Coverage
$(cat bazinga/coverage_report.json | jq -r '.totals.percent_covered')% coverage

## Linting
$(cat bazinga/lint_results.json | jq -r 'length') issues found

[Full details in bazinga/ folder]
EOF
```

---

### Phase 3: Tech Lead Integration

**Priority: HIGH**
**Timeline: Week 1**

Update `agents/techlead.md` to reference Skills:

```markdown
## Workflow

### 0. Pre-Review Automated Analysis (NEW)

**BEFORE manual review, automated Skills will run:**

The following Skills activate automatically:
- 🔒 **security-scan**: Security vulnerability detection
- 🧪 **test-coverage**: Coverage analysis
- 📋 **lint-check**: Code quality linting

**Wait for Skills to complete, then read results:**

```bash
# Read aggregated summary
cat bazinga/analysis_summary.md

# Read detailed reports if needed
cat bazinga/security_scan.json
cat bazinga/coverage_report.json
cat bazinga/lint_results.json
```

**Use automated findings to guide your manual review.**

### 1. Understand Context

**Read automated analysis results first**, then proceed with manual review...
```

---

### Phase 4: Optional Complexity Analyzer

**Priority: MEDIUM**
**Timeline: Week 2**

**Skill 4: Complexity Analyzer**

Only implement if time permits. Lower priority than security/coverage/linting.

---

---

## Implementation Approaches

### Approach 1: Pre-Review Automated Checks (Orchestrator)

**Where:** Orchestrator runs checks **before** spawning Tech Lead

**Pros:**
- ✅ Guaranteed to run every time
- ✅ Results ready when Tech Lead spawns
- ✅ Orchestrator controls timing

**Cons:**
- ❌ Orchestrator becomes more complex
- ❌ Harder to customize per-project

**Use for:** Critical checks that MUST run (security)

---

### Approach 2: Enhanced Tech Lead Instructions

**Where:** Tech Lead agent instructions include tool usage

**Pros:**
- ✅ Tech Lead decides when to run checks
- ✅ Flexible based on context
- ✅ Simpler orchestrator

**Cons:**
- ❌ Tech Lead might skip checks
- ❌ Relies on LLM judgment

**Use for:** Optional checks (complexity analysis)

---

### Approach 3: Skills (Recommended)

**Where:** `.claude/skills/` with auto-invoke descriptions

**Pros:**
- ✅ **Auto-invoked by Claude** when appropriate
- ✅ **Team shareable** via git
- ✅ **Reusable** across projects
- ✅ **Progressive disclosure** - only load when needed
- ✅ **Standardized** - same checks everywhere
- ✅ **Maintainable** - separate from agent prompts

**Cons:**
- ❌ Requires good descriptions for auto-invoke
- ❌ New feature (learning curve)

**Use for:** Security, coverage, linting (standardized workflows)

---

### Hybrid Approach (RECOMMENDED)

**Combine all three:**

1. **Skills** for: Security, Coverage, Linting (auto-invoke)
2. **Orchestrator check** for: Reading Skill results before Tech Lead spawn
3. **Tech Lead instructions** for: How to interpret results + manual review

**Workflow:**
```
Developer completes → Orchestrator spawns Tech Lead
                    ↓
                Skills auto-invoke during Tech Lead review:
                - security-scan runs
                - test-coverage runs
                - lint-check runs
                    ↓
                Tech Lead reads Skill outputs from bazinga/
                    ↓
                Tech Lead performs manual review with context
                    ↓
                Tech Lead makes APPROVED/CHANGES_REQUESTED decision
```

---

---

## Next Steps

### Immediate Actions (This Week)

**Step 1:** Create Skills infrastructure
- [ ] Create `.claude/skills/` directory
- [ ] Create `security-scan/` skill
- [ ] Create `test-coverage/` skill
- [ ] Create `lint-check/` skill

**Step 2:** Implement supporting scripts
- [ ] `scan.sh` (security scanner wrapper)
- [ ] `coverage.sh` (coverage wrapper)
- [ ] `lint.sh` (linting wrapper)
- [ ] PowerShell versions of all scripts

**Step 3:** Update Tech Lead agent
- [ ] Add "Read automated analysis results" step
- [ ] Update review workflow to use Skill outputs
- [ ] Add examples of how to interpret results

**Step 4:** Update orchestrator (optional)
- [ ] Add step to check if Skills completed
- [ ] Pass Skill results to Tech Lead in spawn prompt

**Step 5:** Documentation
- [ ] Update README with Skills section
- [ ] Create SKILLS.md guide for team
- [ ] Add examples to docs/

**Step 6:** Test
- [ ] Test on Python project
- [ ] Test on JavaScript project
- [ ] Verify auto-invoke works
- [ ] Verify results format is useful

---

### Future Enhancements (Later)

**Phase 2:** Additional Skills
- [ ] Complexity analyzer (if useful)
- [ ] Git hotspot analyzer (maybe)

**Phase 3:** Enhanced Intelligence
- [ ] Best practices YAML database
- [ ] Project memory JSON files
- [ ] Architectural pattern guidelines

**Phase 4:** Advanced Features
- [ ] Custom security rules per project
- [ ] Historical trend tracking
- [ ] Integration with CI/CD

---

---

## Key Insights

### What We Learned

1. **Skills are NOT a silver bullet**
   - Don't use for complex orchestration → Use agents
   - Don't use for one-off tasks → Use commands
   - Don't use for reasoning → Use enhanced prompts
   - ✅ **DO use for:** Repeatable, scriptable, standardized workflows

2. **The Skills Test:** *"Would this run the same way every time across all projects?"*
   - If **YES** → Skill candidate
   - If **NO** → Agent/Prompt enhancement

3. **Skills vs Agents vs Commands:**
   - **Skills:** Auto-invoked, standardized workflows, scriptable
   - **Agents:** Complex reasoning, orchestration, contextual judgment
   - **Commands:** User-triggered, one-off tasks

4. **Security/Coverage/Linting are the "Big 3"**
   - Highest value
   - Most standardized
   - Auto-invoke makes sense
   - Team consistency critical

5. **Most "capabilities" don't need special implementation**
   - Fix suggestions → Already built-in
   - Architectural analysis → LLM reasoning
   - Context search → Built-in tools (Grep/Glob)

### Critical Thinking Applied

**Be objective:** Not every idea needs implementation
**Be realistic:** Skills work for narrow use cases
**Be critical:** Many "capabilities" are already covered by Claude's base abilities

**The real wins:** Security scanning, test coverage, linting
**The waste of time:** Reimplementing Claude's natural reasoning abilities

---

---

## Conclusion

**Recommended Implementation:**

✅ **Implement as Skills:**
1. Security Scanner (CRITICAL)
2. Test Coverage Reporter (HIGH)
3. Linting Suite (HIGH)

❌ **Don't Implement:**
- Automated fix suggestions (already built-in)
- Architectural pattern detection (LLM reasoning)
- Performance profiling (too variable)
- Project memory (wrong pattern)

📁 **Implement as Files/Scripts:**
- Best practices database → YAML files
- Git history analysis → Explicit script
- Architectural guidelines → Enhanced Tech Lead prompt

**Impact:**
- Security issues caught automatically
- Test coverage visible before approval
- Code quality standardized
- Tech Lead focuses on architecture/design
- Faster review cycles
- Higher quality approvals

**Next Action:** Implement the 3 core Skills (security, coverage, linting)

---

**End of Analysis**
