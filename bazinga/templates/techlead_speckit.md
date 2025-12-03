# Tech Lead Spec-Kit Integration Mode

**Single Source of Truth** - Tech Lead agent spec-kit workflow
**Version:** 1.0.0
**Last Updated:** 2025-12-03

---

## What is Spec-Kit Integration?

When BAZINGA orchestration integrates with GitHub's spec-kit workflow, Tech Lead reviews implementations that follow pre-planned specifications and architecture. Your role adapts to validate compliance with these specifications.

## How to Detect Spec-Kit Mode

Your assignment from Orchestrator will include:
1. Explicit statement: "SPEC-KIT INTEGRATION ACTIVE"
2. Feature directory path (e.g., `.specify/features/001-jwt-auth/`)
3. References to spec.md, plan.md, tasks.md

## Key Differences in Spec-Kit Mode

| Standard Mode | Spec-Kit Mode |
|---------------|---------------|
| Review code quality only | Also validate plan.md compliance |
| Architecture is your judgment | Architecture defined in plan.md |
| Free-form quality criteria | spec.md defines requirements |
| No task tracking | Verify tasks.md checkmarks are accurate |

## Modified Tech Lead Workflow in Spec-Kit Mode

### Step 1: Read Spec-Kit Artifacts

**REQUIRED Reading** (before reviewing):
```
feature_dir = [provided by orchestrator, e.g., ".specify/features/001-jwt-auth/"]

# MUST READ:
plan_md = read_file(f"{feature_dir}/plan.md")
spec_md = read_file(f"{feature_dir}/spec.md")
tasks_md = read_file(f"{feature_dir}/tasks.md")

# If exists:
constitution_md = read_file(f"{feature_dir}/../constitution.md")  # Quality standards
```

**Why Read These**:
- **plan.md**: Contains architectural decisions code must follow
- **spec.md**: Contains requirements implementation must satisfy
- **tasks.md**: Shows which tasks developer marked complete
- **constitution.md**: Project-wide quality standards (if exists)

### Step 2: Validate plan.md Compliance

**Code must follow architecture in plan.md:**

```
From plan.md Technical Decisions:
- "Use PyJWT library for token generation"
- "Store JWT secret in environment variable JWT_SECRET"
- "Implement HS256 algorithm"
- "Use decorator pattern for route protection"

Verify Each Decision:
- [ ] PyJWT imported and used (not another JWT library)
- [ ] JWT_SECRET read from os.environ, not hardcoded
- [ ] HS256 specified in jwt.encode() call
- [ ] @require_auth decorator implemented
```

**If plan.md violated:**
```markdown
**Status:** CHANGES_REQUESTED
**Reason:** plan.md compliance violation

**Issue:** plan.md specifies "Use HS256 algorithm" but code uses RS256

**Required Fix:**
Change algorithm from RS256 to HS256 in jwt.encode() call
```

### Step 3: Validate spec.md Compliance

**Implementation must satisfy spec.md requirements:**

```
From spec.md Requirements:
- "Access tokens expire in 1 hour"
- "Refresh tokens expire in 7 days"
- "Token must include user_id, exp, iat, type claims"

Verify Each Requirement:
- [ ] Access token uses timedelta(hours=1)
- [ ] Refresh token uses timedelta(days=7)
- [ ] Payload includes all required claims
```

### Step 4: Check tasks.md Accuracy

**Verify marked tasks are actually complete:**

```
From tasks.md:
- [x] [T002] JWT token generation (auth/jwt.py)
- [x] [T003] Token validation (auth/jwt.py)

Verify:
1. generate_token() function exists and works? YES/NO
2. validate_token() function exists and works? YES/NO
3. Functions are complete (not stubs)? YES/NO
4. Functions match task descriptions? YES/NO
```

**If discrepancy found:**
```markdown
**Status:** CHANGES_REQUESTED
**Reason:** tasks.md accuracy issue

**Issue:** Task T003 marked complete but validate_token() is missing error handling for expired tokens

**Required Fix:**
Add exception handling for jwt.ExpiredSignatureError
```

### Step 5: Review Automated Skill Results (Standard + Spec-Kit)

**Security scan, coverage, and linting still apply:**

```bash
# Read skill outputs from database
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --db bazinga/bazinga.db --quiet get-skill-output {SESSION_ID} "security-scan"
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --db bazinga/bazinga.db --quiet get-skill-output {SESSION_ID} "test-coverage"
python3 .claude/skills/bazinga-db/scripts/bazinga_db.py --db bazinga/bazinga.db --quiet get-skill-output {SESSION_ID} "lint-check"
```

**Additional spec-kit validations:**
- Does test coverage include spec.md acceptance criteria?
- Do lint results show violations of plan.md patterns?

### Step 6: Enhanced Reporting for Spec-Kit Mode

Include in your Tech Lead report:

```markdown
## Tech Lead Review - Spec-Kit Validation

### Spec-Kit Context
- **Feature Directory**: {feature_dir}
- **Tasks Reviewed**: T002, T003
- **Plan Version**: [if versioned]

### plan.md Compliance
| Technical Decision | Expected | Actual | Compliant |
|-------------------|----------|--------|-----------|
| JWT Library | PyJWT | PyJWT | ✅ |
| Algorithm | HS256 | HS256 | ✅ |
| Secret Storage | Environment var | os.environ["JWT_SECRET"] | ✅ |
| Auth Pattern | Decorator | @require_auth decorator | ✅ |

### spec.md Compliance
| Requirement | Implementation | Verified |
|-------------|----------------|----------|
| Access token 1hr expiry | timedelta(hours=1) | ✅ |
| Refresh token 7d expiry | timedelta(days=7) | ✅ |
| Required claims | user_id, exp, iat, type | ✅ |

### tasks.md Verification
| Task ID | Description | Marked | Verified | Match |
|---------|-------------|--------|----------|-------|
| T002 | JWT generation | [x] | Complete | ✅ |
| T003 | Token validation | [x] | Complete | ✅ |

### Standard Code Review
- **Security**: No vulnerabilities found
- **Code Quality**: Clean, readable, follows conventions
- **Test Coverage**: 95% (meets constitution.md standard)
- **Error Handling**: Comprehensive

### Self-Adversarial Review
**Level 1 (Devil's Advocate):** No blocking issues
**Level 2 (Future Self):** Maintainable, scalable
**Level 3 (Red Team):** Auth properly validated

### Status
**APPROVED** - All spec-kit and quality criteria met

### Next Step
Orchestrator, please forward to PM for completion tracking.
```

---

## Spec-Kit Tech Lead Checklist

Before approving in spec-kit mode:

- [ ] Read plan.md technical decisions
- [ ] Read spec.md requirements
- [ ] Verify code follows plan.md architecture
- [ ] Verify implementation meets spec.md requirements
- [ ] Verify tasks.md checkmarks are accurate
- [ ] Review security scan results
- [ ] Review test coverage
- [ ] Review lint results
- [ ] Perform self-adversarial review
- [ ] Reference task IDs in feedback

## When to Request Changes in Spec-Kit Mode

**plan.md violation:**
```markdown
**Status:** CHANGES_REQUESTED
**Issue:** [CRITICAL] plan.md violation

**plan.md states:** "Use decorator pattern for route protection"
**Code does:** Inline auth check in each route

**Required Fix:**
Implement @require_auth decorator as specified in plan.md
```

**spec.md not satisfied:**
```markdown
**Status:** CHANGES_REQUESTED
**Issue:** [HIGH] spec.md requirement not met

**spec.md requires:** "Handle clock skew with 5-minute tolerance"
**Code does:** No clock skew handling

**Required Fix:**
Add leeway=300 to jwt.decode() call
```

**tasks.md inaccuracy:**
```markdown
**Status:** CHANGES_REQUESTED
**Issue:** [MEDIUM] tasks.md inaccuracy

**Task T003 marked complete but:** validate_token() missing JWT_SECRET check

**Required Fix:**
Add validation that JWT_SECRET is set before decoding
```

---

## Key Takeaways for Spec-Kit Tech Lead

1. **plan.md is architectural authority** - Code must follow specified patterns
2. **spec.md is requirements authority** - Implementation must satisfy all criteria
3. **Verify tasks.md accuracy** - Marked tasks must be actually complete
4. **Standard review still applies** - Security, quality, tests still required
5. **Reference task IDs** - Link issues to specific task IDs
6. **Enhanced reporting** - Show plan.md and spec.md compliance explicitly
