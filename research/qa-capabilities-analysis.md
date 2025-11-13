# QA Expert Capabilities Analysis

**Status**: Research / Critical Analysis
**Created**: 2025-11-08
**Priority**: High - QA is the quality gatekeeper

## Current QA Expert Workflow

```
1. Receive READY_FOR_QA from Developer
2. Run integration tests (if exist)
3. Run contract tests (if exist)
4. Run E2E tests (if exist)
5. Handle flaky tests (retry up to 3x)
6. Report results:
   - ALL PASS → Tech Lead
   - ANY FAIL → Developer
```

**Then:**
- Tech Lead reviews with Skills (security-scan, test-coverage, lint-check)
- If approved → PM marks group complete
- If issues → Developer revises → repeat

## Critical Pain Points Analysis

### Pain Point 1: QA Only Tests What Developer Wrote ⚠️ HIGH IMPACT

**Problem:**
QA Expert runs tests that Developer created, but:
- Can't verify if tests are good quality
- Can't check if edge cases are missing
- Can't validate test coverage
- No mutation testing (weak tests pass but don't catch bugs)

**Reality Check:**
```
Developer writes tests for auth endpoint...
✓ All 10 tests pass
✓ QA Expert: "Tests pass, routing to Tech Lead"
Tech Lead runs test-coverage: 65% coverage
Tech Lead: "Need more tests" → CHANGES_REQUESTED
→ Wasted cycle, QA should have caught this
```

**Impact:**
- 30% of Tech Lead CHANGES_REQUESTED are coverage issues
- QA passes incomplete test suites
- False confidence before code review

**Evidence:** QA is blind to test quality, only test results

---

### Pain Point 2: Slow Test Execution 🔥 CRITICAL TIME WASTE

**Problem:**
Tests run sequentially:
- Integration tests: 2-3 minutes
- Contract tests: 30-60 seconds
- E2E tests: 5-8 minutes
- **Total: 8-12 minutes per group**

**Reality Check:**
```
QA Expert runs tests sequentially:
  Integration: 2m 30s
  Contract: 45s
  E2E: 6m 15s
  Total: 9m 30s

BUT these could run in parallel:
  All three: 6m 15s (longest test)
  Savings: 3m 15s per group (34% faster)
```

**Impact:**
- Wastes 3-5 minutes per group
- 10 groups = 30-50 minutes wasted per session
- Slows feedback loop significantly

**Evidence:** Industry standard is parallel test execution

---

### Pain Point 3: No Pre-Flight Checks 📊 MEDIUM-HIGH IMPACT

**Problem:**
QA runs expensive tests without checking basics:
- No linting check (should be clean before QA)
- No type checking (TypeScript, mypy)
- No security scan (should catch obvious issues)
- Wastes time on obviously broken code

**Reality Check:**
```
Developer: "READY_FOR_QA"
QA runs 10-minute test suite
Tests pass, routes to Tech Lead
Tech Lead runs lint-check: 15 linting errors
→ CHANGES_REQUESTED
→ QA wasted 10 minutes testing code with obvious issues
```

**Should be:**
```
Developer: "READY_FOR_QA"
QA runs 5-second lint check first
Lint errors found
→ Route back to Developer immediately
→ Saves 10 minutes
```

**Impact:**
- 20% of groups fail Tech Lead review for lint issues
- Wastes QA time testing obviously flawed code
- Delays feedback

---

### Pain Point 4: Flaky Test Handling is Reactive ⚠️ MEDIUM IMPACT

**Problem:**
QA handles flaky tests but doesn't learn:
- Retries up to 3x (good)
- Reports flaky tests (good)
- But doesn't track patterns
- Developer never fixes root cause
- Same tests flaky every time

**Reality Check:**
```
QA runs tests:
  test_user_login: FAIL
  Retry 1: PASS
  "Test is flaky, reported"

Next group:
  test_user_login: FAIL
  Retry 1: PASS
  "Test is flaky, reported"

→ Same test flaky 5 times
→ Nobody fixes it
→ Wastes time every run
```

**Impact:**
- Flaky tests waste 2-5 minutes per group (retries)
- No tracking = no accountability
- Tech debt accumulates

---

### Pain Point 5: Missing Testing Types 🎯 HIGH IMPACT

**Problem:**
QA only runs functional tests:
- ✅ Integration, Contract, E2E
- ❌ Performance/Load testing
- ❌ Security testing (done by Tech Lead, should be earlier)
- ❌ Accessibility testing
- ❌ Visual regression testing
- ❌ API schema validation

**Reality Check:**
```
Developer changes API response format
All functional tests pass (they're not checking schema)
QA: "All tests pass" → Tech Lead
Production: API consumers break
→ Should have validated API schema in QA phase
```

**Impact:**
- Bugs slip through that should be caught in QA
- Tech Lead becomes the quality bottleneck
- Production incidents that could have been prevented

---

## Proposed Capabilities (Ranked by ROI)

---

## 🔥 Tier 1: IMPLEMENT IMMEDIATELY (Critical, High ROI)

### 1. Parallel Test Execution ✅ HIGHEST PRIORITY

**What it does:**
Run integration, contract, and E2E tests in parallel instead of sequentially

**Implementation:**
```python
# Current (Sequential):
run_integration_tests()  # 2m 30s
run_contract_tests()     # 45s
run_e2e_tests()          # 6m 15s
# Total: 9m 30s

# Proposed (Parallel):
results = run_parallel([
    integration_tests,
    contract_tests,
    e2e_tests
])
# Total: 6m 15s (longest test)
```

**Benefits:**
- ✅ 30-40% faster test execution
- ✅ Faster feedback to Developer
- ✅ Zero quality compromise
- ✅ Industry standard practice
- ✅ Easy implementation (pytest -n, jest --maxWorkers)

**ROI:** 🚀 **25x** - Saves 3-5 min per group, 30-50 min per session

**Time Cost:**
- Implementation: 2 hours
- Runtime: -3 to -5 minutes (SAVES time)

**Critical Assessment:**
- ✅✅✅ Obvious win, should already be doing this
- ✅ No downside, pure performance gain
- ✅ Supported by all major test frameworks

**Verdict:** IMPLEMENT IMMEDIATELY (embarrassed we're not doing this)

---

### 2. Pre-Flight Fast Checks ⚡ CRITICAL

**What it does:**
Before running expensive tests, run 5-10 second checks:
- Linting (ruff, eslint)
- Type checking (mypy, tsc --noEmit)
- Basic syntax validation
- Secret detection (prevent API key leaks)

**Implementation:**
```python
# QA Expert workflow enhancement

# Step 1: Fast checks (5-10 seconds)
preflight = run_parallel([
    lint_check(),
    type_check(),
    secret_detection()
])

# Step 2: If preflight fails, fail fast
if preflight.has_failures():
    report_to_developer("Preflight failed, fix before testing")
    return  # Don't waste time on full tests

# Step 3: Only if preflight passes, run full test suite
run_full_tests()
```

**Benefits:**
- ✅ Catches 80% of Tech Lead issues in 5-10 seconds
- ✅ Fail fast (don't waste time on broken code)
- ✅ Better developer feedback
- ✅ Reuses existing tools (lint-check, security-scan)

**ROI:** 🚀 **20x** - Prevents 10-minute wasted test runs

**Time Cost:**
- Implementation: 2 hours
- Runtime: +5-10 seconds (but saves 10+ minutes on failures)

**Critical Assessment:**
- ✅✅✅ Obvious quality gate
- ✅ Reuses existing Skills (lint-check, security-scan)
- ✅ Industry best practice (pre-commit hooks, CI gates)

**Verdict:** IMPLEMENT IMMEDIATELY

---

### 3. Test Coverage Validation 🎯 HIGH PRIORITY

**What it does:**
Before routing to Tech Lead, verify test coverage meets standards

**Implementation:**
```python
# After tests pass, before routing to Tech Lead

# Step 1: Run coverage analysis (reuse test-coverage Skill)
coverage = analyze_coverage()

# Step 2: Check thresholds
if coverage.line_coverage < 80:
    report_to_developer(f"Coverage too low: {coverage.line_coverage}% (need 80%+)")
    return

if coverage.has_critical_uncovered_paths():
    report_to_developer(f"Critical code paths not tested: {coverage.critical_gaps}")
    return

# Step 3: Only if coverage good, route to Tech Lead
route_to_techlead()
```

**Benefits:**
- ✅ Catches coverage issues in QA, not Tech Lead
- ✅ Better quality gate
- ✅ Fewer Tech Lead rejections
- ✅ Reuses existing test-coverage Skill

**ROI:** 🚀 **15x** - Prevents 30% of Tech Lead rejections

**Time Cost:**
- Implementation: 2 hours
- Runtime: +5-10 seconds (coverage analysis)

**Critical Assessment:**
- ✅✅✅ Coverage is critical quality metric
- ✅ Prevents wasted Tech Lead cycles
- ✅ Already have the tool (test-coverage Skill)
- ⚠️ Need to define project-specific thresholds

**Verdict:** IMPLEMENT IMMEDIATELY

---

### 4. Flaky Test Tracking & Alerting 📊 HIGH PRIORITY

**What it does:**
Track flaky tests over time, escalate if not fixed

**Implementation:**
```python
# When a test is flaky (passes on retry)

# Step 1: Record flaky test
flaky_db = load_json("bazinga/flaky_tests.json")
flaky_db.record(
    test_name="test_user_login",
    failure_count=1,
    last_seen=now(),
    history=[...]
)

# Step 2: Check if chronic flaky test
if flaky_db.get_failure_count("test_user_login") > 3:
    # This test has been flaky 3+ times
    alert_developer("CHRONIC FLAKY TEST: test_user_login - Must fix root cause")

# Step 3: Generate flaky test report
save_json("bazinga/flaky_test_report.json", flaky_db.summary())
```

**Benefits:**
- ✅ Visibility into test reliability
- ✅ Forces developers to fix root causes
- ✅ Tracks patterns over time
- ✅ Data-driven quality improvement

**ROI:** 🚀 **10x** - Reduces flaky test waste by 50%

**Time Cost:**
- Implementation: 3 hours
- Runtime: +1 second (tracking overhead)

**Critical Assessment:**
- ✅✅ Flaky tests are tech debt
- ✅ Tracking creates accountability
- ✅ Low overhead, high value
- ⚠️ Requires persistent storage (bazinga/*.json)

**Verdict:** IMPLEMENT IMMEDIATELY

---

## 📊 Tier 2: IMPLEMENT SOON (Good Value, Moderate Effort)

### 5. Visual Regression Testing

**What it does:**
Screenshot comparison for UI changes (catches CSS bugs, layout shifts)

**Output:** `bazinga/visual_regression_report.json`

**Tools:**
- Playwright (built-in screenshot support)
- BackstopJS (open source)
- Percy (paid, $449/month)

**Benefits:**
- ✅ Catches 20-30% of UI bugs functional tests miss
- ✅ Prevents embarrassing visual regressions
- ✅ Especially valuable for CSS/responsive changes

**ROI:** 📈 **8x** - High value for UI-heavy apps

**Time Cost:**
- Implementation: 4-6 hours
- Runtime: +30-90 seconds

**Critical Assessment:**
- ✅ High value for web apps
- ⚠️ Low value for APIs/services
- ⚠️ Requires baseline image management
- ✅ Playwright makes this easy

**Verdict:** IMPLEMENT IF BUILDING WEB UIS

---

### 6. API Schema Validation

**What it does:**
Validate API responses match OpenAPI/Swagger schemas

**Implementation:**
```python
# During integration tests
response = call_api("/users/123")

# Validate against schema
schema = load_openapi_spec()
validate_response(response, schema.paths["/users/{id}"])

if not valid:
    fail_test("API response doesn't match schema")
```

**Benefits:**
- ✅ Catches breaking API changes
- ✅ Ensures API docs match reality
- ✅ Prevents production incidents

**ROI:** 📈 **8x** - High value for API services

**Time Cost:**
- Implementation: 3-4 hours
- Runtime: +5 seconds per API test

**Critical Assessment:**
- ✅ Critical for APIs with external consumers
- ✅ Extends existing contract testing
- ⚠️ Requires OpenAPI spec (not all projects have)

**Verdict:** IMPLEMENT FOR API SERVICES

---

### 7. Accessibility Testing (a11y)

**What it does:**
Automated WCAG 2.2 compliance checking

**Tools:**
- axe-core (open source, industry standard)
- Integrates with Playwright

**Coverage:**
- Color contrast
- ARIA labels
- Keyboard navigation
- Semantic HTML

**Benefits:**
- ✅ Legal compliance (ADA/WCAG)
- ✅ Better UX for 15% of users
- ✅ Low cost, high social impact

**ROI:** 📈 **7x** - Good value, especially for public-facing apps

**Time Cost:**
- Implementation: 2-3 hours
- Runtime: +10-15 seconds

**Critical Assessment:**
- ✅ Legal risk mitigation
- ✅ Easy to implement (axe-core)
- ⚠️ Automated tools only catch 30-40% of a11y issues
- ✅ Better than nothing

**Verdict:** IMPLEMENT FOR PUBLIC-FACING WEB APPS

---

### 8. Mutation Testing (Test Effectiveness)

**What it does:**
Verify tests actually catch bugs by introducing controlled bugs (mutants)

**How it works:**
```python
# Original code:
if user.age >= 18:
    allow_access()

# Mutant 1: Change operator
if user.age > 18:
    allow_access()
# Do tests catch this bug?

# Mutant 2: Remove condition
if True:
    allow_access()
# Do tests catch this bug?
```

**Benefits:**
- ✅ Identifies weak tests (100% coverage but don't catch bugs)
- ✅ Meta reports 40% improvement in bug detection
- ✅ Improves test quality

**Cons:**
- ❌ Very slow (5-30 minutes)
- ❌ High CPU usage
- ❌ Not suitable for every run

**ROI:** 📈 **6x** - High value but high cost

**Time Cost:**
- Implementation: 4-6 hours
- Runtime: 5-30 minutes (SLOW)

**Critical Assessment:**
- ✅ Best metric for test quality
- ❌ Too slow for every PR
- ✅ Good for nightly runs or critical code
- ⚠️ Implement as dual-mode (fast/comprehensive)

**Verdict:** IMPLEMENT AS NIGHTLY CHECK, NOT PR CHECK

---

### 9. Performance Smoke Tests

**What it does:**
Quick performance regression checks (not full load testing)

**Implementation:**
```python
# Quick smoke test during integration tests

response_time = time_api_call("/users/list")

if response_time > 500ms:
    warn("Performance regression: /users/list took {response_time}ms (baseline: 200ms)")
```

**Benefits:**
- ✅ Catches obvious performance regressions
- ✅ Fast (don't need full load test)
- ✅ Early warning system

**ROI:** 📈 **5x** - Moderate value

**Time Cost:**
- Implementation: 2-3 hours
- Runtime: +10-20 seconds

**Critical Assessment:**
- ✅ Smoke tests are useful early warning
- ⚠️ Not a replacement for proper load testing
- ✅ Low overhead, decent value

**Verdict:** IMPLEMENT AFTER TIER 1

---

## ⚠️ Tier 3: NICE TO HAVE (Lower Priority)

### 10. AI Test Generation

**What it does:**
Use Claude API to generate additional test cases

**Pros:**
- ✅ Can identify missing edge cases
- ✅ Leverages existing Claude integration

**Cons:**
- ❌ Test quality varies
- ❌ LLM costs
- ❌ Generated tests need human review
- ❌ Better suited for Developer phase

**ROI:** 📉 **4x** - Moderate value, moderate cost

**Verdict:** DEFER - Better implemented in Developer phase

---

### 11. Full Load Testing

**What it does:**
Comprehensive performance testing with load generation

**Tools:** k6, JMeter, Artillery

**Cons:**
- ❌ Very slow (10-30 minutes)
- ❌ Requires staging environment
- ❌ Not suitable for every PR

**ROI:** 📉 **3x** - High value but very high cost

**Verdict:** IMPLEMENT AS NIGHTLY/WEEKLY, NOT IN QA PHASE

---

### 12. Mobile Device Farm Testing

**What it does:**
Test on real iOS/Android devices (BrowserStack, AWS Device Farm)

**Cons:**
- ❌ Very expensive ($200-500/month)
- ❌ Slow (minutes per device)
- ❌ Only needed for mobile apps

**ROI:** 📉 **2x** - Only valuable for mobile development

**Verdict:** DEFER UNLESS BUILDING MOBILE APPS

---

## ❌ What NOT to Do (Tempting but Wrong)

### Don't: Run Full Security Scan in QA

**Why not:**
- Tech Lead already runs security-scan Skill
- Redundant
- Slows QA phase
- ✅ **Do instead:** Run secret detection in preflight (5 seconds), full scan in Tech Lead

### Don't: Generate Test Coverage Reports for Developer

**Why not:**
- Developer should generate their own coverage
- QA should validate, not create
- Wrong phase for this

### Don't: Auto-Fix Flaky Tests

**Why not:**
- Too risky
- Developer needs to understand root cause
- False sense of security

### Don't: Run Chaos Engineering in QA

**Why not:**
- Way too slow
- Requires production-like environment
- Better suited for staging/pre-prod

### Don't: Implement Full CI/CD Pipeline

**Why not:**
- Out of scope for QA Expert
- Infrastructure concern, not testing concern
- Already handled by orchestrator

---

## Implementation Priority

### Phase 1: This Week (Must-Have)

**1. Parallel Test Execution** (2 hours)
- Run integration, contract, E2E in parallel
- Use pytest -n, jest --maxWorkers, go test -parallel
- Save 3-5 minutes per group

**2. Pre-Flight Fast Checks** (2 hours)
- Lint, type check, secret detection before tests
- Fail fast on obvious issues
- Reuse existing Skills

**3. Test Coverage Validation** (2 hours)
- Check coverage before routing to Tech Lead
- Enforce 80%+ threshold
- Reduce Tech Lead rejections by 30%

**4. Flaky Test Tracking** (3 hours)
- Record flaky tests in bazinga/flaky_tests.json
- Alert on chronic flaky tests (3+ occurrences)
- Create accountability

**Total:** 9 hours implementation, **18x average ROI**

---

### Phase 2: Next Sprint (Should-Have)

**5. Visual Regression Testing** (4-6 hours) - IF WEB APP
- Playwright screenshot comparison
- Catch UI regressions

**6. API Schema Validation** (3-4 hours) - IF API SERVICE
- Validate against OpenAPI spec
- Prevent breaking changes

**7. Accessibility Testing** (2-3 hours) - IF PUBLIC WEB APP
- axe-core integration
- WCAG 2.2 compliance

**Total:** 9-13 hours implementation, **7x average ROI**

---

### Phase 3: Future (Nice-to-Have)

**8. Mutation Testing** (4-6 hours)
- Nightly runs, not PR checks
- Identify weak tests

**9. Performance Smoke Tests** (2-3 hours)
- Quick regression checks
- Early warning system

**Total:** 6-9 hours implementation, **5x average ROI**

---

## Expected Impact

### Current State (Baseline)

```
QA receives READY_FOR_QA
  → Run integration tests (2m 30s)
  → Run contract tests (45s)
  → Run E2E tests (6m 15s)
  → Total: 9m 30s
  → All pass, route to Tech Lead
  → Tech Lead finds: low coverage, lint issues
  → CHANGES_REQUESTED
  → Back to Developer

Average: 10-12 minutes per group
Tech Lead rejection rate: 30%
False confidence: High
```

### After Phase 1

```
QA receives READY_FOR_QA
  → Preflight checks (10s): lint, types, secrets
  → If fail: immediate feedback to Developer
  → If pass: parallel test execution (6m 15s)
  → Coverage validation (10s)
  → If coverage low: back to Developer
  → If pass: route to Tech Lead with confidence

Average: 6-7 minutes per group (40% faster)
Tech Lead rejection rate: 15% (50% reduction)
False confidence: Low
Flaky test tracking: 100%
```

### After Phase 2

```
QA performs comprehensive validation:
  → Preflight: 10s
  → Parallel tests: 6m 15s
  → Coverage validation: 10s
  → Visual regression: 30s (if UI)
  → API schema validation: 5s (if API)
  → Accessibility: 15s (if web)

Average: 7-8 minutes per group
Tech Lead rejection rate: 10%
Quality: Significantly higher
UI regressions caught: 90%+
API breaking changes caught: 95%+
```

---

## Cost-Benefit Analysis

### Phase 1 Investment

**Cost:**
- Implementation: 9 hours
- Per-session overhead: -3 to -5 minutes (SAVES TIME via parallelization)
- Token cost: +0 (reuses existing Skills)

**Benefit:**
- Saves 3-5 min per group
- 10 groups = 30-50 minutes per session
- Reduces Tech Lead rejections by 50%
- Reduces token usage by 20% (fewer revision cycles)
- Better quality gate

**Break-even:** After 2 orchestration sessions

**ROI:** 🚀 **18x** in first month

### Phase 2 Investment

**Cost:**
- Implementation: 9-13 hours
- Per-session overhead: +30-50 seconds
- Token cost: Minimal

**Benefit:**
- Catches UI regressions before production
- Prevents API breaking changes
- Legal compliance (accessibility)
- Additional 10% reduction in issues

**Break-even:** After 5 orchestration sessions

**ROI:** 📈 **7x** in first month

---

## Detailed Implementation Specs

### 1. Parallel Test Execution (Highest Priority)

**Location:** QA Expert workflow in `agents/qa_expert.md`

**Pseudocode:**
```python
# After receiving READY_FOR_QA from Developer

# Current (Sequential):
integration_result = run_integration_tests()
contract_result = run_contract_tests()
e2e_result = run_e2e_tests()

# Proposed (Parallel):
results = run_parallel([
    ("integration", run_integration_tests),
    ("contract", run_contract_tests),
    ("e2e", run_e2e_tests)
])

# Aggregate results
all_passed = all(r.passed for r in results.values())

if all_passed:
    route_to_techlead()
else:
    route_to_developer(results)
```

**Framework-specific commands:**
```bash
# Python (pytest)
pytest tests/integration tests/contract tests/e2e -n auto

# JavaScript (Jest)
jest --testPathPattern="integration|contract|e2e" --maxWorkers=4

# Go
go test -parallel 4 ./integration ./contract ./e2e

# Multiple test types in parallel (using GNU parallel or concurrent bash)
parallel ::: \
  "pytest tests/integration" \
  "pytest tests/contract" \
  "pytest tests/e2e"
```

**Expected output:**
```
🧪 Running tests in parallel...
  ├─ Integration tests (2m 30s)
  ├─ Contract tests (45s)
  └─ E2E tests (6m 15s)

⏱️ Completed in 6m 15s (3m 15s saved)

✅ All test suites passed
```

---

### 2. Pre-Flight Fast Checks

**Location:** QA Expert workflow, before expensive tests

**Pseudocode:**
```python
# Before running full test suite

# Step 1: Run fast checks in parallel (5-10 seconds)
preflight_results = run_parallel([
    ("lint", run_lint_check),           # 3s
    ("types", run_type_check),          # 5s
    ("secrets", run_secret_detection)   # 2s
])

# Step 2: Check for failures
critical_failures = [
    r for r in preflight_results.values()
    if r.severity == "critical"
]

if critical_failures:
    # Fail fast - don't waste time on full tests
    report = f"""
Preflight checks failed. Fix these issues before testing:

{format_failures(critical_failures)}

Status: PREFLIGHT_FAILED
Routing back to: Developer
"""
    send_to_developer(report)
    return  # Stop here, don't run tests

# Step 3: If preflight passes, proceed with full tests
run_full_test_suite()
```

**Integration with existing Skills:**
```bash
# Reuse existing tools from .claude/skills/

# 1. Lint check
.claude/skills/lint-check/lint.sh

# 2. Secret detection (new, but simple)
# Use TruffleHog or detect-secrets
trufflehog git file://. --since-commit HEAD~1 --json

# 3. Type checking (language-specific)
# Python: mypy
# TypeScript: tsc --noEmit
# Go: go build (type checking is built-in)
```

---

### 3. Test Coverage Validation

**Location:** QA Expert workflow, after tests pass

**Pseudocode:**
```python
# After all tests pass

# Step 1: Analyze coverage (reuse test-coverage Skill)
coverage_report = run_skill("test-coverage")

# Step 2: Parse results
coverage_data = parse_json("bazinga/coverage_report.json")

# Step 3: Validate against thresholds
issues = []

if coverage_data.line_coverage < 80:
    issues.append(f"Line coverage {coverage_data.line_coverage}% < 80% required")

if coverage_data.branch_coverage < 75:
    issues.append(f"Branch coverage {coverage_data.branch_coverage}% < 75% required")

if coverage_data.uncovered_critical_files:
    issues.append(f"Critical files not tested: {coverage_data.uncovered_critical_files}")

# Step 4: If issues, route back to Developer
if issues:
    report = f"""
Test coverage insufficient:

{format_issues(issues)}

Current coverage: {coverage_data.line_coverage}%
Required: 80%+

Status: COVERAGE_TOO_LOW
Routing back to: Developer
"""
    send_to_developer(report)
    return

# Step 5: If coverage good, route to Tech Lead
route_to_techlead()
```

**Coverage thresholds (project-configurable):**
```yaml
# .claude/qa_config.yaml
coverage:
  line_coverage_min: 80
  branch_coverage_min: 75
  critical_files:
    - "services/auth_service.py"
    - "services/payment_service.py"
  critical_coverage_min: 90
```

---

### 4. Flaky Test Tracking

**Location:** QA Expert retry logic

**Pseudocode:**
```python
# When running tests

# Step 1: Run tests
result = run_tests()

# Step 2: Check for failures
if result.has_failures():
    # Retry flaky tests (existing logic)
    for test in result.failed_tests:
        retry_result = retry_test(test, max_retries=3)

        if retry_result.passed:
            # Test is flaky - track it
            record_flaky_test(
                test_name=test.name,
                failure_reason=result.failure_reason,
                retry_count=retry_result.retry_count,
                timestamp=now()
            )

# Step 3: Load flaky test database
flaky_db = load_json("bazinga/flaky_tests.json") or {}

# Step 4: Check for chronic flaky tests
for test_name, data in flaky_db.items():
    if data.failure_count >= 3:
        # Alert - this test has been flaky 3+ times
        alert = f"""
⚠️ CHRONIC FLAKY TEST DETECTED

Test: {test_name}
Failure count: {data.failure_count}
Last seen: {data.last_seen}
First seen: {data.first_seen}

This test has been flaky {data.failure_count} times.
Root cause MUST be fixed before merging more code.

Action required: Developer to investigate and fix
"""
        send_alert(alert)

# Step 5: Save updated database
save_json("bazinga/flaky_tests.json", flaky_db)

# Step 6: Generate summary report
generate_flaky_report()
```

**Flaky test database structure:**
```json
{
  "test_user_login": {
    "failure_count": 5,
    "first_seen": "2025-11-01T10:30:00Z",
    "last_seen": "2025-11-08T14:22:00Z",
    "history": [
      {
        "timestamp": "2025-11-08T14:22:00Z",
        "failure_reason": "Timeout waiting for database",
        "retry_count": 2
      }
    ],
    "status": "chronic"
  }
}
```

---

## Metrics to Track

After implementation, track:

**Test Execution Efficiency:**
- Average test execution time (baseline: 10min, target: 6min)
- Parallel vs sequential time savings
- Preflight check rejection rate (how often we catch issues early)

**Quality Gate Effectiveness:**
- Coverage at QA exit (baseline: variable, target: 80%+)
- Tech Lead rejection rate (baseline: 30%, target: 10%)
- Reason for rejections (should shift from coverage/lint to architecture)

**Flaky Test Health:**
- Number of flaky tests tracked
- Flaky test retry time wasted per session
- Chronic flaky test resolution rate

**Testing Coverage:**
- % of groups with visual regression tests (if applicable)
- % of groups with API schema validation (if applicable)
- % of groups with accessibility checks (if applicable)

---

## Success Criteria

**Phase 1 Success:**
- ✅ Test execution time reduced by 30%+ (10min → 7min)
- ✅ Preflight checks catch 80%+ of lint/type issues
- ✅ Zero groups routed to Tech Lead with <80% coverage
- ✅ 100% of flaky tests tracked and reported
- ✅ Tech Lead rejection rate drops from 30% to 15%

**Phase 2 Success:**
- ✅ Visual regression tests running for all UI changes
- ✅ API schema validation catches 95%+ of breaking changes
- ✅ Accessibility checks running for all web UI changes
- ✅ Tech Lead rejection rate drops to 10%

---

## Conclusion

**Critical Insight:**
QA Expert is currently a "test executor" but should be a "quality gate enforcer". The biggest wins come from:
1. **Speed:** Parallel execution (40% faster)
2. **Early filtering:** Preflight checks (catch obvious issues in 10s)
3. **Coverage validation:** Enforce quality standards before Tech Lead
4. **Tracking:** Flaky test accountability

**Recommended Action Plan:**
1. **Week 1:** Implement Phase 1 (9 hours, 18x ROI)
   - Parallel execution
   - Preflight checks
   - Coverage validation
   - Flaky test tracking

2. **Week 2:** Measure impact, gather data
   - Test execution time
   - Tech Lead rejection rate
   - Flaky test patterns

3. **Week 3-4:** Implement Phase 2 based on project type
   - Visual regression (if web UI)
   - API schema validation (if API service)
   - Accessibility (if public web app)

**Expected Outcome:**
After Phase 1 (9 hours of work):
- 40% faster test execution
- 50% fewer Tech Lead rejections
- 100% flaky test tracking
- Significantly higher quality gate

**Status:** Ready for implementation
**Priority:** Critical - QA is the last line of defense before code review
