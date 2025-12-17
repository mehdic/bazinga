# PM BAZINGA Validation Reference

**This file is referenced by the Project Manager agent. Do not modify without updating the PM agent.**

---

## BAZINGA VALIDATION PROTOCOL

**MANDATORY: Verify ALL success criteria before BAZINGA**

### Pre-BAZINGA Verification (REQUIRED)

Before sending BAZINGA, you MUST complete ALL these steps:

1. **Query success criteria from database**
   - **Request:** `bazinga-db, get success criteria for session [session_id]`
   - **Command:** `get-success-criteria [session_id]`
   - **Invoke:** `Skill(command: "bazinga-db")`
   - This ensures you verify against ORIGINAL criteria (cannot be manipulated)

2. **Verify each criterion** with concrete evidence (test output, measurements)
   - Run tests, check coverage, validate requirements
   - Document actual results vs expected

3. **Update criteria status in database**
   For each criterion, update: status (met/blocked/failed), actual value, evidence
   - **Request:** `bazinga-db, update success criterion for session [id]`
   - **Command:** `update-success-criterion [session_id] "[criterion_text]" --status "met" --actual "[value]" --evidence "[proof]"`
   - **Example:** `update-success-criterion abc123 "All tests passing" --status "met" --actual "711/711 passing" --evidence "pytest output at 2025-11-24T10:30:00"`
   - **Invoke:** `Skill(command: "bazinga-db")` for EACH criterion update

4. **Calculate completion**: X/Y criteria met (%)

---

## Decision Logic

```
IF 100% criteria met:
  → Send BAZINGA (Path A)

ELSE IF <100% criteria met:
  → Check if test-related criteria exist

  # Detect test criteria
  test_criteria_exist = any(
    "test" in criterion.lower() OR
    "passing" in criterion.lower() OR
    "failure" in criterion.lower()
    for criterion in success_criteria
  )

  IF test_criteria_exist:
    → MANDATORY: Get test failure count FIRST

    Methods (in order of preference):
    1. Query bazinga-db for latest test results
    2. Spawn QA Expert: "Run full test suite NOW and report exact failure count"
    3. Read recent test output file (if < 5 min old)

    ❌ DO NOT run tests yourself via Bash
    ✅ DO get exact numeric count: "X passing, Y failing"
    ❌ DO NOT accept vague: "tests look good"

    IF any_test_failures_exist (count > 0):
      → Path B is FORBIDDEN
      → MUST use Path C: Spawn developers to fix ALL failures
      → DO NOT send BAZINGA until failure count = 0

  ELSE IF other_gaps_exist:
    → Check if fixable:
      - Fixable (coverage, config, bugs) → Path C
      - Truly external (API keys, service down) → Path B
```

---

## Path A: Full Achievement ✅

**100% of success criteria met**

- Evidence: Test output, coverage reports, measurements
- Action: Send BAZINGA immediately

---

## Path B: Partial Achievement with External Blockers ⚠️

**X/Y criteria met (X < Y) where remaining gaps blocked by external factors**

**External blockers (acceptable):**
- External API unavailable/down (not under project control)
- Third-party service rate limits or outages
- Missing backend features (explicitly out of scope)
- Cloud infrastructure limitations beyond project

**NOT external (must fix - use Path C):**
- Test failures, coverage gaps, config issues, bugs
- Missing mocks or test data (fixable infrastructure)
- Dependency version conflicts (solvable)

**Required format:**
```markdown
## Pre-BAZINGA Verification

Success Criteria Status: X/Y met (Z%)

✅ Criterion 1: [description] - ACHIEVED
   Evidence: [concrete measurement]
✅ Criterion 2: [description] - ACHIEVED
   Evidence: [concrete measurement]
❌ Criterion 3: [description] - BLOCKED
   Root cause: [external blocker]
   Attempts: [what was tried]
   Proof external: [why can't be fixed within scope]

## BAZINGA

Partial completion with documented external blockers.
```

**Update blocked criteria in database:**
```
update-success-criterion [session_id] "[criterion_text]" --status "blocked" --actual "[partial_result]" --evidence "[blocker_description]"
```

### Path B Strict Requirements

To use Path B, you MUST prove ALL of these:

1. **Clear external dependency** - Not code, tests, config within project
2. **Beyond project control** - Cannot be fixed by developers
3. **Multiple fix attempts failed** - Document 2-3 approaches tried
4. **Not a test/coverage gap** - Coverage <target is ALWAYS Path C
5. **Not a bug/failure** - Test failures are ALWAYS Path C
6. **Not a config/setup issue** - Environment/deps are ALWAYS Path C
7. **ZERO test failures** - If ANY tests failing, Path B is FORBIDDEN

**MANDATORY PRE-PATH-B CHECK:**
```bash
# Verify zero failures before considering Path B
IF failure_count > 0:
  → Path B is FORBIDDEN
  → Use Path C to fix ALL failures
  → ALL test failures are fixable by definition
```

**Examples NOT Path B (must use Path C):**
- ❌ "Coverage only 44%, mocking too complex"
- ❌ "Tests failing due to edge cases"
- ❌ "Performance target not met"
- ❌ "Integration tests need backend"
- ❌ "Pre-existing test failures unrelated to my task"

**Examples ARE Path B (legitimate):**
- ✅ "Cannot integrate with Stripe: API keys not provided"
- ✅ "Cannot deploy to AWS: no AWS credentials, out of scope"
- ✅ "Cannot test email: SendGrid is down (checked status page)"

---

## Path C: Work Incomplete ❌

**<100% criteria met AND gaps are fixable**

- Examples: Test failures, low coverage, config issues, bugs
- Action: Spawn Developer, DO NOT send BAZINGA

**CRITICAL:** You CANNOT redefine success criteria mid-flight. If original requirement was ">70% coverage", achieving 44% is NOT success.

---

## Self-Adversarial BAZINGA Completion

**MANDATORY**: Before sending BAZINGA, challenge your own completion assessment.

### The 5-Point BAZINGA Challenge

**1. "What would the user's boss say?"**
- Would this pass a stakeholder demo?
- Are there visible rough edges?

**2. "What will break in 30 days?"**
- Are there edge cases not covered?
- Will this scale with growth?

**3. "Am I rationalizing incomplete work?"**
- Am I accepting "good enough" when 100% is achievable?
- Am I marking failures as "pre-existing" to avoid work?

**4. "Did I verify or assume?"**
- Did I RUN the tests or assume they pass?
- Did I CHECK the evidence or trust the developer?

**5. "Would I bet my job on this?"**
- Am I confident this is truly complete?
- Is there anything I'm hoping nobody notices?

### Self-Adversarial Report (Required in BAZINGA)

```markdown
## Self-Adversarial Check ✅

**1. Stakeholder Demo Ready:** YES/NO + reason
**2. 30-Day Stability:** YES/NO + potential issues
**3. Rationalization Check:** NO rationalizations detected
**4. Verification Method:** [Tests run, evidence collected]
**5. Confidence Level:** HIGH (would bet job on it)

**Red Flags Found:** [None / List any concerns]
**Concerns Addressed:** [How each was resolved]

**Conclusion:** Passed self-adversarial check. Sending BAZINGA.
```

### If ANY Answer is "NO"

```
IF stakeholder_demo_ready == NO:
    → DO NOT send BAZINGA
    → Spawn Developer to fix visible issues

IF 30_day_stability == NO:
    → Log tech debt OR fix if critical
    → Only send BAZINGA if issues are LOW severity

IF rationalization_check == YES (found rationalization):
    → STOP. Re-evaluate. Fix the issue.
    → DO NOT send BAZINGA until honest assessment

IF verification_method == "assumed":
    → RUN the verification NOW
    → DO NOT send BAZINGA until actual evidence

IF confidence_level < HIGH:
    → DO NOT send BAZINGA
    → Investigate what's causing doubt
```

---

## Tech Debt Gate (Before BAZINGA)

**MANDATORY:** Check bazinga/tech_debt.json before BAZINGA

**Decision Logic:**
- Blocking items (blocks_deployment=true) → Report to user, NO BAZINGA
- HIGH severity >2 → Ask user approval
- Only MEDIUM/LOW → Include summary in BAZINGA
- No tech debt → Send BAZINGA

---

## Development Plan Check (Before BAZINGA)

IF development plan exists:
- Query: `Skill(command: "bazinga-db")` → get development plan
- Count completed vs total phases
- IF incomplete phases remain → **DO NOT send BAZINGA**
- Output: `📋 Plan: Phase {N} complete | Phase {M} pending`
- **Status:** PARTIAL_PLAN_COMPLETE (not BAZINGA)

IF all plan phases completed:
- Mark current phase as completed
- Proceed to BAZINGA validation

---

## PM BAZINGA Response Format (MANDATORY)

```markdown
## PM Status: BAZINGA

### Completion Summary
- Completed_Items: [count]
- Total_Items: [count from original request]
- Completion_Percentage: [X]%
- Deferred_Items: [] (MUST be empty unless BLOCKED)

### Final Report
[Report content]

### Self-Adversarial Check ✅
[5-point check results]

### Branch Merge Status
[Merge verification]

### BAZINGA
Project complete! All requirements met.
```
