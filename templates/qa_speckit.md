# QA Expert Spec-Kit Integration Mode

**Single Source of Truth** - QA Expert agent spec-kit workflow
**Version:** 1.0.0
**Last Updated:** 2025-12-03

---

## What is Spec-Kit Integration?

When BAZINGA orchestration integrates with GitHub's spec-kit workflow, QA receives implementations that follow pre-planned specifications. Your role adapts to validate against these specifications.

## How to Detect Spec-Kit Mode

Your assignment from Orchestrator will include:
1. Explicit statement: "SPEC-KIT INTEGRATION ACTIVE"
2. Feature directory path (e.g., `.specify/features/001-jwt-auth/`)
3. References to spec.md, plan.md, tasks.md

## Key Differences in Spec-Kit Mode

| Standard Mode | Spec-Kit Mode |
|---------------|---------------|
| Test what developer implemented | Validate against spec.md requirements |
| Free-form test strategy | Tests must cover spec.md acceptance criteria |
| Developer's description guides testing | spec.md provides authoritative requirements |
| No task tracking file | Verify tasks.md checkmarks match reality |

## Modified QA Workflow in Spec-Kit Mode

### Step 1: Read Spec-Kit Artifacts

**REQUIRED Reading** (before testing):
```
feature_dir = [provided by orchestrator, e.g., ".specify/features/001-jwt-auth/"]

# MUST READ:
spec_md = read_file(f"{feature_dir}/spec.md")
tasks_md = read_file(f"{feature_dir}/tasks.md")

# Recommended:
plan_md = read_file(f"{feature_dir}/plan.md")
```

**Why Read These**:
- **spec.md**: Contains authoritative acceptance criteria to test against
- **tasks.md**: Shows which tasks developer marked complete - verify these
- **plan.md**: Understand technical approach to design appropriate tests

### Step 2: Verify tasks.md Alignment

**Check that implemented features match task descriptions:**

```
From tasks.md:
- [x] [T002] [P] [US1] JWT token generation (auth/jwt.py)
- [x] [T003] [P] [US1] Token validation (auth/jwt.py)

Verify:
1. auth/jwt.py exists and contains generate_token function? YES/NO
2. auth/jwt.py contains validate_token function? YES/NO
3. Functions match task descriptions? YES/NO
```

**If mismatch found:**
- Report as test failure
- Developer marked task complete but implementation is missing/incorrect

### Step 3: Cross-Reference with spec.md

**Ensure acceptance criteria from spec.md are met:**

```
From spec.md Acceptance Criteria:
1. "Generate JWT tokens with user ID and expiration"
2. "Support both access tokens (1 hour) and refresh tokens (7 days)"
3. "Validate token signatures and expiration"
4. "Handle expired tokens gracefully"

Test Each Criterion:
- [ ] Test 1: Token generation includes user_id and exp claims
- [ ] Test 2: Access token expires in 1 hour, refresh in 7 days
- [ ] Test 3: Invalid signatures are rejected
- [ ] Test 4: Expired tokens return appropriate error
```

### Step 4: Validate Edge Cases from spec.md

**spec.md typically includes edge cases - test ALL of them:**

```
From spec.md Edge Cases:
- "Handle malformed tokens"
- "Handle tokens with invalid signatures"
- "Handle missing token payloads"
- "Handle clock skew (5-minute tolerance)"

Edge Case Tests:
- [ ] Malformed token returns InvalidTokenError
- [ ] Invalid signature returns InvalidTokenError
- [ ] Missing payload fields handled gracefully
- [ ] Token 4 minutes in future is accepted (clock skew)
```

### Step 5: Enhanced Reporting for Spec-Kit Mode

Include in your QA report:

```markdown
## QA Report - Spec-Kit Validation

### Spec-Kit Context
- **Feature Directory**: {feature_dir}
- **Tasks Validated**: T002, T003
- **spec.md Version**: [if versioned]

### tasks.md Verification
| Task ID | Description | Marked Complete | Actually Complete | Match |
|---------|-------------|-----------------|-------------------|-------|
| T002 | JWT generation | [x] | YES | ✅ |
| T003 | Token validation | [x] | YES | ✅ |

### spec.md Acceptance Criteria Coverage
| Criterion | Test | Result |
|-----------|------|--------|
| Generate JWT with user_id | test_token_has_user_id | ✅ PASS |
| Access token 1hr expiry | test_access_expiry | ✅ PASS |
| Refresh token 7d expiry | test_refresh_expiry | ✅ PASS |
| Validate signatures | test_signature_validation | ✅ PASS |
| Handle expired tokens | test_expired_rejection | ✅ PASS |

### spec.md Edge Cases Coverage
| Edge Case | Test | Result |
|-----------|------|--------|
| Malformed tokens | test_malformed_token | ✅ PASS |
| Invalid signatures | test_invalid_signature | ✅ PASS |
| Missing payload | test_missing_payload | ✅ PASS |
| Clock skew tolerance | test_clock_skew | ✅ PASS |

### plan.md Compliance (if architectural tests needed)
- ✅ Uses PyJWT library (verified in requirements.txt)
- ✅ HS256 algorithm (verified in code)
- ✅ JWT_SECRET from environment (verified)

### Test Summary
- **Total Tests**: 15
- **Passing**: 15
- **Failing**: 0
- **Coverage**: 95%

### Status
**QA_PASSED** - All spec.md criteria verified

### Next Step
Orchestrator, please forward to Tech Lead for code review.
```

---

## Spec-Kit QA Checklist

Before reporting QA_PASSED:

- [ ] Read spec.md acceptance criteria
- [ ] Read tasks.md to see what was marked complete
- [ ] Verify each marked task is actually implemented
- [ ] Test EVERY acceptance criterion from spec.md
- [ ] Test EVERY edge case from spec.md
- [ ] Verify implementation follows plan.md (if applicable)
- [ ] Report coverage of spec.md requirements
- [ ] Include task ID references in report

## When to Report QA_FAILED in Spec-Kit Mode

**Task-spec mismatch:**
```
Developer marked [T002] complete but:
- Function doesn't exist
- Function doesn't match task description
- Function doesn't meet spec.md criteria

Report: QA_FAILED
Reason: Task T002 marked complete but implementation missing/incorrect
```

**Spec.md criteria not met:**
```
spec.md requires "Support refresh tokens with 7-day expiry"
But: refresh_token() not implemented or uses wrong expiry

Report: QA_FAILED
Reason: spec.md criterion "refresh token support" not satisfied
```

**Edge case not handled:**
```
spec.md requires "Handle malformed tokens gracefully"
But: Malformed tokens cause unhandled exception

Report: QA_FAILED
Reason: spec.md edge case "malformed tokens" not handled
```

---

## Key Takeaways for Spec-Kit QA

1. **spec.md is authoritative** - Test against spec, not just developer's description
2. **Verify tasks.md accuracy** - Marked tasks must actually be complete
3. **Cover all acceptance criteria** - Every criterion in spec.md needs a test
4. **Test all edge cases** - spec.md edge cases are requirements, not suggestions
5. **Reference task IDs** - Link test failures to specific task IDs
6. **Enhanced reporting** - Show spec.md coverage explicitly
