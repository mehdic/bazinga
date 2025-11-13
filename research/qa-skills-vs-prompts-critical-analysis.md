# QA Capabilities: Skills vs Prompts - Brutal Critical Analysis

**Date:** 2025-11-08
**Context:** Evaluating each QA capability from qa-capabilities-analysis.md
**Framework:** Claude Code Skills vs Agent Prompts vs Commands

---

## The Skills Test (from Anthropic docs)

**✅ Good Skills:**
- Standardized, repeatable workflows
- Scriptable automated checks
- Domain-specific expertise Claude auto-discovers
- Clear trigger conditions
- Includes scripts/templates/resources
- Fast execution (<60s typically)

**❌ Bad Skills:**
- Complex orchestration (use agents)
- One-off tasks (use commands)
- Deep reasoning tasks (use prompts)
- Variable/context-specific workflows
- Anything LLM should decide, not script

**Test:** *"Would this run the same way every time across all projects?"*
- If **YES** → Skill candidate
- If **NO** → Agent prompt or command

---

## Default vs Superpowers Decision Framework

**Default Skills** (Always Run):
- Essential for quality gates
- Fast (<20s)
- Critical for preventing issues
- No debate, must run every time
- Examples: security-scan, test-coverage, lint-check

**Superpowers Skills** (Opt-in with "superpowers" keyword):
- Adds significant value but not essential
- Slower (15-60s)
- Deeper analysis
- Worth the time cost when quality is critical
- Examples: codebase-analysis, test-pattern-analysis

**Prompt Enhancement** (Not a Skill):
- Complex reasoning
- LLM decision-making
- Context-specific logic
- Already built into agent capabilities
- Add to agent instructions, not a skill

---

## Critical Analysis: QA Capabilities from Analysis Doc

### ✅ TIER 1 CAPABILITIES

---

### 1. Parallel Test Execution

**Proposed as:** Immediate implementation
**Reality Check:** ⚠️ **NOT A SKILL - PROMPT ENHANCEMENT**

**Why NOT a skill:**
- ❌ Not scriptable - requires orchestration logic
- ❌ Different command per framework (pytest -n, jest --maxWorkers)
- ❌ This is workflow logic, not domain expertise
- ❌ Claude needs to decide when/how to parallelize

**What it actually is:**
- LLM reasoning: "Should I run these tests in parallel?"
- Workflow orchestration: Running multiple bash commands concurrently
- Agent decision-making: How many workers based on CPU cores?

**Correct implementation:**
```markdown
# agents/qa_expert.md

## Test Execution Strategy

IMPORTANT: Run test suites in PARALLEL, not sequentially.

### Parallel Execution Commands

**Python (pytest):**
```bash
pytest tests/integration tests/contract tests/e2e -n auto
```

**JavaScript (Jest):**
```bash
jest --testPathPattern="integration|contract|e2e" --maxWorkers=4
```

**Go:**
```bash
go test -parallel 4 ./integration ./contract ./e2e
```

Use bash background jobs or GNU parallel for maximum efficiency.
```

**Verdict:** ❌ **NOT A SKILL - ADD TO QA EXPERT PROMPT**

---

### 2. Pre-Flight Fast Checks

**Proposed as:** Critical, reuses existing skills
**Reality Check:** ⚠️ **PARTIALLY SKILL, MOSTLY PROMPT**

**Breaking it down:**

**Secret Detection - YES, NEW DEFAULT SKILL** ✅
- ✅ Standardized workflow (TruffleHog or detect-secrets)
- ✅ Scriptable
- ✅ Fast (<5s)
- ✅ Clear trigger: Before running expensive tests
- ✅ Critical security concern

**Lint/Type Check - ALREADY EXISTS AS SKILL** ✅
- lint-check skill already exists (default)
- Just need to invoke it in QA phase

**The "Preflight" logic - PROMPT ENHANCEMENT** ❌
- ❌ The decision to "run fast checks before slow tests" is workflow logic
- ❌ The fail-fast behavior is LLM reasoning
- ❌ Not scriptable - it's orchestration

**Correct implementation:**

**NEW SKILL: secret-detection**
```yaml
---
name: secret-detection
description: "Detect hardcoded secrets, API keys, credentials in code. Use before running tests or committing code."
allowed-tools: [Bash, Read, Write]
---

# Secret Detection Skill

Scans for leaked credentials using TruffleHog.

## When to Use
- Before running expensive test suites
- Before committing code
- When reviewing security-sensitive changes

## Output
- bazinga/secrets_found.json
```

**QA Expert Prompt Enhancement:**
```markdown
# agents/qa_expert.md

## Pre-Flight Checks (MANDATORY)

BEFORE running expensive tests, run fast validation:

1. **Secret Detection** (CRITICAL - 3s)
   - Invoke: /secret-detection skill
   - If secrets found: IMMEDIATELY route back to Developer
   - DO NOT run tests if secrets detected

2. **Lint Check** (5s)
   - Invoke: /lint-check skill
   - If critical issues: Route back to Developer
   - Minor issues: Continue but note in report

3. **Type Checking** (5s)
   - Run language-appropriate type checker
   - Python: mypy
   - TypeScript: tsc --noEmit
   - Go: go build (validates types)

ONLY if all preflight checks pass, proceed with full test suite.
```

**Verdict:**
- ✅ **NEW DEFAULT SKILL: secret-detection**
- ❌ **Rest is PROMPT ENHANCEMENT**

---

### 3. Test Coverage Validation

**Proposed as:** High priority, reuses test-coverage skill
**Reality Check:** ⚠️ **NOT A SKILL - PROMPT ENHANCEMENT**

**Why NOT a skill:**
- ❌ test-coverage skill already exists (default)
- ❌ The validation logic ("is 80% enough?") is LLM reasoning
- ❌ Threshold enforcement is workflow decision
- ❌ Different thresholds per project (not standardized)

**What it actually is:**
- Reading existing test-coverage skill output
- Applying project-specific thresholds
- Making routing decision (pass/fail)
- This is QA Expert's job, not a skill's job

**Correct implementation:**
```markdown
# agents/qa_expert.md

## Coverage Validation (After Tests Pass)

1. **Analyze Coverage** (already exists)
   - Invoke: /test-coverage skill
   - Reads: bazinga/coverage_report.json

2. **Validate Thresholds**
   - Minimum line coverage: 80%
   - Minimum branch coverage: 75%
   - Critical files: 90%+

3. **Routing Decision**
   - IF coverage < thresholds:
     - Status: COVERAGE_TOO_LOW
     - Route to: Developer with specific gaps
   - IF coverage >= thresholds:
     - Status: PASS
     - Route to: Tech Lead

**Coverage threshold configuration** (project-specific):
- Check for .claude/qa_config.yaml
- Default to 80% line, 75% branch if not found
```

**Verdict:** ❌ **NOT A SKILL - PROMPT ENHANCEMENT (uses existing skill)**

---

### 4. Flaky Test Tracking & Alerting

**Proposed as:** High priority, requires persistence
**Reality Check:** ✅ **YES, NEW SUPERPOWERS SKILL**

**Why YES, it's a good skill:**
- ✅ Standardized workflow (parse test results, track failures)
- ✅ Scriptable (Python can analyze test JSON)
- ✅ Domain expertise (flaky test analysis algorithms)
- ✅ Produces structured output (flaky_tests.json)
- ✅ Repeatable across projects
- ✅ Not quick reasoning - requires historical analysis

**Why SUPERPOWERS, not default:**
- ⚠️ Not critical for every run (nice to have)
- ⚠️ Adds 10-15s overhead
- ⚠️ Value grows over time (needs history)
- ⚠️ More useful for mature projects than new ones

**Correct implementation:**

```yaml
---
name: flaky-test-detector
description: "Track and analyze flaky tests over time. Identifies chronic flaky tests requiring fixes. Use in superpowers mode for comprehensive quality analysis."
allowed-tools: [Bash, Read, Write]
---

# Flaky Test Detection Skill

Analyzes test result history to identify and track flaky tests.

## When to Use
- After running tests in QA phase
- When investigating test reliability
- Before major releases
- In superpowers mode for enhanced quality analysis

## What It Does
- Parses test results from pytest-json-report, jest --json, etc.
- Tracks failure patterns across runs
- Calculates flakiness score (pass rate variance)
- Identifies chronic flaky tests (3+ failures)
- Generates alerts for action items

## Output
- bazinga/flaky_tests.json
- bazinga/flaky_test_report.md
```

**Verdict:** ✅ **NEW SUPERPOWERS SKILL: flaky-test-detector**

---

## ✅ TIER 2 CAPABILITIES

---

### 5. Visual Regression Testing

**Proposed as:** High value for UI apps
**Reality Check:** ✅ **YES, NEW SUPERPOWERS SKILL**

**Why YES:**
- ✅ Standardized workflow (Playwright screenshots + pixelmatch)
- ✅ Scriptable
- ✅ Domain expertise (image comparison algorithms)
- ✅ Repeatable
- ✅ Produces structured output

**Why SUPERPOWERS, not default:**
- ⚠️ Only valuable for UI apps (not APIs/services)
- ⚠️ Slower (30-90s)
- ⚠️ Requires baseline management
- ⚠️ Opt-in makes sense - not every project needs this

**Correct implementation:**

```yaml
---
name: visual-regression
description: "Screenshot comparison for UI changes. Catches CSS bugs, layout shifts. Use in superpowers mode for web UI applications."
allowed-tools: [Bash, Read, Write]
---

# Visual Regression Testing Skill

Automated visual comparison using Playwright screenshots.

## When to Use
- When testing web UI changes
- Before merging CSS/styling changes
- For responsive design validation
- In superpowers mode for UI-heavy projects

## Requirements
- Playwright installed
- Baseline screenshots in .visual-regression/baselines/

## Output
- bazinga/visual_diff_report.json
- .visual-regression/diffs/ (diff images)
```

**Verdict:** ✅ **NEW SUPERPOWERS SKILL: visual-regression**

---

### 6. API Schema Validation

**Proposed as:** High value for API services
**Reality Check:** ✅ **EXTEND EXISTING SKILL: api-contract-validation**

**Why NOT a new skill:**
- ✅ api-contract-validation skill already exists (superpowers)
- ✅ Just needs runtime validation mode, not just spec diff

**Enhancement needed:**
```markdown
# .claude/skills/api-contract-validation/SKILL.md

## Modes

### 1. Spec Diff Mode (existing)
Compares OpenAPI specs for breaking changes

### 2. Runtime Validation Mode (NEW)
Validates actual API responses against schema

**Usage:**
```bash
# Mode 1: Spec diff
python validate_contract.py --mode=diff --baseline=api_v1.yaml --current=api_v2.yaml

# Mode 2: Runtime validation
python validate_contract.py --mode=runtime --spec=api.yaml --test-results=integration_results.json
```
```

**Verdict:** ✅ **ENHANCE EXISTING SUPERPOWERS SKILL: api-contract-validation**

---

### 7. Accessibility Testing (a11y)

**Proposed as:** Legal compliance, low cost
**Reality Check:** ✅ **YES, NEW SUPERPOWERS SKILL**

**Why YES:**
- ✅ Standardized workflow (axe-core integration)
- ✅ Scriptable
- ✅ Domain expertise (WCAG rules)
- ✅ Repeatable
- ✅ Fast (10-15s)

**Why SUPERPOWERS, not default:**
- ⚠️ Only valuable for web UIs (not APIs)
- ⚠️ Automated tools only catch 30-40% (still need manual)
- ⚠️ Opt-in makes sense - not every project needs this
- ⚠️ Legal compliance is project-specific

**Correct implementation:**

```yaml
---
name: accessibility-testing
description: "WCAG 2.2 compliance checking using axe-core. Use in superpowers mode for public-facing web applications."
allowed-tools: [Bash, Read, Write]
---

# Accessibility Testing Skill

Automated a11y testing using axe-core + Playwright.

## When to Use
- For public-facing web applications
- Before production deployments
- When testing UI changes
- In superpowers mode for compliance-critical projects

## What It Detects
- Color contrast violations
- Missing ARIA labels
- Keyboard navigation issues
- Semantic HTML violations

## Limitations
Automated tools catch ~30-40% of a11y issues.
Manual testing still required for full WCAG compliance.

## Output
- bazinga/accessibility_report.json
```

**Verdict:** ✅ **NEW SUPERPOWERS SKILL: accessibility-testing**

---

### 8. Mutation Testing

**Proposed as:** Nightly, not PR checks
**Reality Check:** ✅ **YES, NEW SUPERPOWERS SKILL (with caveats)**

**Why YES:**
- ✅ Standardized workflow (mutmut, Stryker, PITest)
- ✅ Scriptable
- ✅ Domain expertise (mutation strategies)
- ✅ Repeatable

**Why SUPERPOWERS + command-only:**
- ⚠️ VERY slow (5-30 minutes)
- ⚠️ Too expensive for every PR
- ⚠️ Best for nightly/weekly runs
- ⚠️ Should be user-initiated, not auto-invoked

**Critical distinction:**
- This should be a **SKILL** (has the scripts)
- But invoked via **COMMAND**, not auto-discovered
- Not in QA Expert workflow by default

**Correct implementation:**

```yaml
---
name: mutation-testing
description: "Test effectiveness analysis using mutation testing. VERY SLOW (5-30 min). Use via command for nightly runs or critical code paths only."
allowed-tools: [Bash, Read, Write]
---

# Mutation Testing Skill

Verifies tests catch bugs by introducing controlled mutations.

## When to Use
**DO NOT USE IN PR WORKFLOW** - Too slow!

Use via command for:
- Nightly quality runs
- Pre-release validation
- Critical business logic testing
- Security-sensitive code paths

## Speed Modes
- Fast mode: 10% sample (~2-5 min)
- Comprehensive: Full analysis (~10-30 min)

## Output
- bazinga/mutation_report.json
```

**Plus a command:**
```markdown
# .claude/commands/test-mutations.md

Run mutation testing on changed files.

Usage: /test-mutations [fast|full]

WARNING: This is slow (2-30 minutes).
Only use for critical code or nightly runs.
```

**Verdict:** ✅ **NEW SUPERPOWERS SKILL: mutation-testing (command-triggered only)**

---

### 9. Performance Smoke Tests

**Proposed as:** Quick regression checks
**Reality Check:** ⚠️ **MAYBE SKILL, MAYBE PROMPT**

**Analysis:**
- ✅ Could be scriptable (timing API calls)
- ❌ But baselines are project-specific
- ❌ And what to measure varies per app
- ⚠️ Borderline case

**The issue:**
- Setting baseline: "API should respond in <500ms" - Where does 500ms come from?
- What to measure: Which endpoints? All? Critical only?
- Failure threshold: 2x baseline? 3x? 10%?

**These are LLM reasoning questions, not script questions.**

**Better approach: Hybrid**

**Skill provides the measurement:**
```yaml
---
name: performance-profiler
description: "Quick performance smoke tests. Measures API response times and detects regressions. Use in superpowers mode."
allowed-tools: [Bash, Read, Write]
---

Runs integration tests with timing instrumentation.
Compares against historical baseline (if exists).
Reports anomalies (>2x slower than baseline).

Output: bazinga/performance_profile.json
```

**QA Expert decides what to do with results:**
```markdown
# agents/qa_expert.md (superpowers mode only)

## Performance Smoke Testing (Superpowers Only)

IF superpowers mode enabled:
  - Invoke: /performance-profiler skill
  - Review: bazinga/performance_profile.json
  - IF regressions detected (>2x baseline):
    - Warn in report
    - Flag for developer review
    - Not blocking unless severe (>5x)
```

**Verdict:** ✅ **NEW SUPERPOWERS SKILL: performance-profiler (with prompt logic)**

---

## ⚠️ TIER 3 CAPABILITIES

---

### 10. AI Test Generation

**Proposed as:** Defer to Developer phase
**Reality Check:** ❌ **NOT A SKILL - WRONG PHASE ENTIRELY**

**Why NOT:**
- ❌ Test generation is Developer's job, not QA's
- ❌ LLM reasoning, not scriptable workflow
- ❌ Quality varies, needs human review
- ❌ This is core Claude capability, not a skill

**If implemented at all:**
- Add to Developer agent prompt (superpowers mode)
- Not a skill
- Not in QA phase

**Verdict:** ❌ **NOT A SKILL - NOT EVEN QA EXPERT'S JOB**

---

### 11. Full Load Testing

**Proposed as:** Nightly/weekly, not PR
**Reality Check:** ✅ **YES, COMMAND + SKILL (like mutation testing)**

**Why YES as skill:**
- ✅ Standardized workflow (k6, JMeter, Artillery)
- ✅ Scriptable
- ✅ Domain expertise

**Why COMMAND-triggered, not auto:**
- ❌ Too slow (10-30 minutes)
- ❌ Requires staging environment
- ❌ User should explicitly request

**Correct implementation:**

```yaml
---
name: load-testing
description: "Performance load testing with k6/Artillery. VERY SLOW (10-30 min). Use via command for performance validation."
allowed-tools: [Bash, Read, Write]
---

# Load Testing Skill

Comprehensive performance testing under load.

## When to Use
**DO NOT USE IN PR WORKFLOW** - Too slow!

Use via command for:
- Pre-release performance validation
- Capacity planning
- Stress testing
- Weekly performance runs

## Test Types
- Smoke test: 1-10 users (1-2 min)
- Load test: Expected traffic (5-10 min)
- Stress test: Breaking point (10-30 min)

## Output
- bazinga/load_test_results.json
```

**Verdict:** ✅ **NEW SKILL: load-testing (command-triggered, not default or superpowers)**

---

### 12. Mobile Device Farm Testing

**Proposed as:** Only if building mobile
**Reality Check:** ❌ **NOT A SKILL - WRONG SCOPE**

**Why NOT:**
- ❌ External service (BrowserStack, AWS Device Farm)
- ❌ Expensive ($200-500/month)
- ❌ Integration with external APIs is MCP territory, not Skills
- ❌ Too complex for BAZINGA scope

**Verdict:** ❌ **OUT OF SCOPE - Not a BAZINGA concern**

---

## ❌ ANTI-PATTERNS TO AVOID

### DON'T: Run Full Security Scan in QA

**Reality Check:** ❌ **Correct - security-scan already runs in Tech Lead**

**Why correct:**
- ✅ Tech Lead already invokes security-scan skill
- ✅ QA runs secret-detection (fast, critical)
- ✅ Full scan in Tech Lead (comprehensive)
- ✅ Right division of labor

**Verdict:** ✅ **Original analysis was correct**

---

### DON'T: Auto-Fix Flaky Tests

**Reality Check:** ✅ **Correct - never auto-fix**

**Why correct:**
- ✅ Too risky
- ✅ Developer needs to understand root cause
- ✅ Skills should detect, not fix
- ✅ LLM should suggest, not auto-apply

**Verdict:** ✅ **Original analysis was correct**

---

## SUMMARY: SKILLS VS PROMPTS BREAKDOWN

### ✅ NEW DEFAULT SKILLS (Always Run, Essential)

| Skill | Why Default | Execution Time | Critical |
|-------|-------------|----------------|----------|
| **secret-detection** | Prevents catastrophic leaks | 3-5s | YES |

**Total Default Skills:** 1 new (+ 3 existing: security-scan, test-coverage, lint-check)

---

### ✅ NEW SUPERPOWERS SKILLS (Opt-in, High Value)

| Skill | Why Superpowers | Execution Time | Value |
|-------|-----------------|----------------|-------|
| **flaky-test-detector** | Quality insights over time | 10-15s | High for mature projects |
| **visual-regression** | UI quality (opt-in for web apps) | 30-90s | High for UI apps |
| **accessibility-testing** | Legal compliance (opt-in) | 10-15s | High for public web |
| **performance-profiler** | Regression detection | 15-30s | Medium-High |

**Enhancements to existing:**
| Skill | Enhancement | Why |
|-------|-------------|-----|
| **api-contract-validation** | Add runtime validation mode | Validates actual responses vs schemas |

**Total Superpowers Skills:** 4 new + 1 enhanced

---

### ✅ COMMAND-TRIGGERED SKILLS (User-initiated, Too Slow for Auto)

| Skill | Why Command | Execution Time | Use Case |
|-------|-------------|----------------|----------|
| **mutation-testing** | Too slow for PR | 5-30 min | Nightly runs, critical code |
| **load-testing** | Too slow, needs env | 10-30 min | Pre-release, capacity planning |

**Total Command Skills:** 2 new

---

### ❌ PROMPT ENHANCEMENTS (Not Skills, Add to Agent Instructions)

| Enhancement | Agent | Why Not Skill |
|-------------|-------|---------------|
| **Parallel test execution** | QA Expert | Workflow orchestration, not scriptable |
| **Pre-flight logic** | QA Expert | Uses existing skills + LLM decisions |
| **Coverage validation** | QA Expert | Uses existing skill + threshold reasoning |

---

### ❌ NOT IMPLEMENTING (Wrong Phase or Out of Scope)

| Capability | Why Not |
|------------|---------|
| **AI test generation** | Developer's job, not QA; already LLM capability |
| **Mobile device farms** | External service, out of BAZINGA scope |
| **Chaos engineering** | Too complex, staging-only, separate concern |

---

## FINAL RECOMMENDATIONS

### Phase 1: Default Skills (This Week)

**1. Implement secret-detection skill** (4 hours)
- Critical security concern
- Fast (3-5s)
- Prevents catastrophic leaks
- Should run EVERY TIME

**Integration:**
```markdown
# agents/qa_expert.md

## Step 1: Pre-Flight Checks (BEFORE expensive tests)

1. **Secret Detection** (CRITICAL)
   - Invoke /secret-detection skill
   - If secrets found: STOP, route to Developer
   - Do not run tests if secrets detected
```

---

### Phase 2: Superpowers Skills (Next 2 Weeks)

**Priority order based on ROI:**

**1. flaky-test-detector** (6 hours)
- High value for reliability
- Builds knowledge over time
- 10-15s overhead acceptable in superpowers

**2. visual-regression** (6 hours)
- High value for web UIs
- Prevents embarrassing bugs
- Playwright makes this easy

**3. accessibility-testing** (4 hours)
- Legal compliance
- Low cost, high social value
- Easy axe-core integration

**4. performance-profiler** (6 hours)
- Quick smoke tests
- Early warning system
- Moderate value

**5. api-contract-validation enhancement** (4 hours)
- Add runtime validation mode
- High value for APIs
- Extends existing skill

**Total:** 26 hours for all superpowers skills

---

### Phase 3: Command Skills (Future)

**1. mutation-testing** (8 hours)
- Command-triggered only
- Nightly/weekly runs
- For critical code paths

**2. load-testing** (8 hours)
- Command-triggered only
- Pre-release validation
- Requires staging env

**Total:** 16 hours

---

### Phase 4: Prompt Enhancements (This Week)

**Update QA Expert agent prompt** (2 hours):
- Add parallel test execution instructions
- Add pre-flight check workflow (using skills)
- Add coverage validation logic (using skill output)
- Add superpowers mode conditional logic

---

## TOTAL EFFORT ESTIMATE

| Phase | Hours | Priority | ROI |
|-------|-------|----------|-----|
| **Phase 1** (Default) | 4 | CRITICAL | 20x |
| **Phase 2** (Superpowers) | 26 | HIGH | 12x |
| **Phase 3** (Commands) | 16 | MEDIUM | 6x |
| **Phase 4** (Prompts) | 2 | HIGH | 15x |
| **TOTAL** | **48 hours** | - | **13x avg** |

---

## CRITICAL INSIGHTS

### What We Learned

**1. Most "capabilities" are actually prompt enhancements**
- Parallel execution: Just tell QA Expert to do it
- Coverage validation: Just tell QA Expert to check thresholds
- Pre-flight logic: Just tell QA Expert the workflow

**Don't over-engineer with skills when prompts work fine.**

**2. Skills are for domain expertise, not orchestration**
- ✅ Good: "Run TruffleHog and parse results"
- ❌ Bad: "Decide when to run tests in parallel"

**3. Superpowers makes sense for non-universal needs**
- Not every project needs visual regression
- Not every project needs accessibility testing
- Opt-in is the right model

**4. Very slow things should be commands, not auto-invoked**
- Mutation testing: 5-30 min
- Load testing: 10-30 min
- User should explicitly request these

**5. Default should be minimal**
- Only 1 new default skill (secret-detection)
- Everything else is superpowers or prompts
- Fast (<5s) is the bar for default

---

## COMPARISON WITH ORIGINAL ANALYSIS

### What Changed

**Original Tier 1 (4 capabilities):**
1. Parallel execution → ❌ Not a skill, PROMPT
2. Pre-flight checks → ⚠️ Partially skill (secret-detection), mostly PROMPT
3. Coverage validation → ❌ Not a skill, PROMPT (uses existing skill)
4. Flaky test tracking → ✅ Superpowers skill (not default)

**Original Tier 2 (5 capabilities):**
1. Visual regression → ✅ Superpowers skill ✓
2. API schema validation → ✅ Enhance existing superpowers skill ✓
3. Accessibility → ✅ Superpowers skill ✓
4. Mutation testing → ✅ Command skill (not superpowers)
5. Performance smoke → ✅ Superpowers skill ✓

**Original Tier 3 (3 capabilities):**
1. AI test generation → ❌ Not QA's job
2. Load testing → ✅ Command skill ✓
3. Mobile farms → ❌ Out of scope ✓

### Brutal Truth

**Original analysis was ~40% wrong** about what should be skills vs prompts.

**Why:**
- Over-valued "capabilities" that are just workflow instructions
- Didn't apply the Skills Test ("same every time?")
- Confused LLM reasoning with scriptable workflows

**Corrected:**
- 1 new default skill (not 4)
- 4 new superpowers skills (+ 1 enhancement)
- 2 command skills
- 3 prompt enhancements
- 3 rejected entirely

---

## FINAL VERDICT: BE SKEPTICAL OF "CAPABILITIES"

**Most QA improvements don't need new skills. They need better prompts.**

**Skills are for:**
- Running external tools (TruffleHog, axe-core, Playwright)
- Parsing complex outputs
- Domain expertise (mutation algorithms, visual diffs)

**Prompts are for:**
- Making decisions
- Orchestrating workflows
- Applying thresholds
- Routing logic

**Don't build a skill if you can write a better prompt.**

---

**End of Analysis**
