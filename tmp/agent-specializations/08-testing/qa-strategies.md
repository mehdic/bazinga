---
name: qa-strategies
type: testing
priority: 2
token_estimate: 450
compatible_with: [qa_expert, tech_lead]
requires: []
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# QA Strategies & Test Planning Expertise

## Specialist Profile
QA specialist designing comprehensive test strategies. Expert in test planning, risk-based testing, and quality metrics.

## Implementation Guidelines

### Test Plan Structure

```markdown
# Test Plan: User Management Feature

## 1. Scope
### In Scope
- User registration (email/password)
- User profile management
- User search functionality
- Admin user management

### Out of Scope
- OAuth integration (separate feature)
- Password reset (existing functionality)

## 2. Test Approach

### 2.1 Test Levels
| Level | Coverage | Tools | Owner |
|-------|----------|-------|-------|
| Unit | 80%+ | Jest | Dev |
| Integration | API contracts | Supertest | Dev |
| E2E | Critical paths | Playwright | QA |
| Performance | Load testing | k6 | QA |

### 2.2 Test Types
- Functional: CRUD operations, validation
- Security: Auth, authorization, input validation
- Performance: Response times, concurrent users
- Usability: Accessibility, mobile responsiveness

## 3. Entry/Exit Criteria

### Entry Criteria
- [ ] Feature code complete
- [ ] Unit tests passing
- [ ] Test environment available
- [ ] Test data prepared

### Exit Criteria
- [ ] All critical test cases passed
- [ ] No P1/P2 defects open
- [ ] 80% code coverage
- [ ] Performance benchmarks met

## 4. Risk Assessment
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Data migration issues | Medium | High | Parallel testing |
| Performance degradation | Low | High | Load testing |
| Security vulnerabilities | Medium | Critical | Security scan |
```

### Test Case Design

```markdown
## Test Case: TC-USER-001
**Title:** Create user with valid data
**Priority:** P1
**Type:** Functional

### Preconditions
- User is logged in as admin
- No user exists with test email

### Test Data
| Field | Value |
|-------|-------|
| Email | test.user@example.com |
| Display Name | Test User |

### Steps
1. Navigate to Users page
2. Click "Create User" button
3. Enter email: test.user@example.com
4. Enter display name: Test User
5. Click Submit

### Expected Results
- Success message displayed
- User appears in user list
- User status is "pending"
- Created timestamp is current

### Actual Results
[To be filled during execution]

### Status
[ ] Pass [ ] Fail [ ] Blocked
```

### Boundary Value Analysis

```python
# Systematic boundary testing
class BoundaryTests:
    """
    For display_name: min=2, max=100 characters

    Boundaries:
    - Below min: 1 char (invalid)
    - At min: 2 chars (valid)
    - Above min: 3 chars (valid)
    - Below max: 99 chars (valid)
    - At max: 100 chars (valid)
    - Above max: 101 chars (invalid)
    """

    @pytest.mark.parametrize("length,expected_valid", [
        (1, False),   # Below minimum
        (2, True),    # At minimum boundary
        (3, True),    # Just above minimum
        (99, True),   # Just below maximum
        (100, True),  # At maximum boundary
        (101, False), # Above maximum
    ])
    def test_display_name_length(self, length, expected_valid):
        name = "a" * length
        result = validate_display_name(name)
        assert result.is_valid == expected_valid
```

### Equivalence Partitioning

```python
# Group inputs into equivalence classes
class EmailValidationTests:
    """
    Equivalence classes for email:
    - Valid: standard format (user@domain.com)
    - Invalid: missing @ symbol
    - Invalid: missing domain
    - Invalid: special characters
    - Invalid: empty string
    """

    @pytest.mark.parametrize("email,expected_valid,partition", [
        ("user@example.com", True, "valid_standard"),
        ("user.name@example.co.uk", True, "valid_subdomain"),
        ("userexample.com", False, "invalid_no_at"),
        ("user@", False, "invalid_no_domain"),
        ("user@exam ple.com", False, "invalid_space"),
        ("", False, "invalid_empty"),
    ])
    def test_email_validation(self, email, expected_valid, partition):
        result = validate_email(email)
        assert result.is_valid == expected_valid, f"Failed for partition: {partition}"
```

### Defect Severity Matrix

```markdown
## Severity Definitions

| Severity | Definition | SLA | Examples |
|----------|------------|-----|----------|
| P1-Critical | System unusable, data loss | 4 hours | Auth broken, data corruption |
| P2-High | Major feature broken, no workaround | 24 hours | Cannot create users |
| P3-Medium | Feature impaired, workaround exists | 72 hours | Search not filtering correctly |
| P4-Low | Minor issue, cosmetic | Next sprint | Typo, alignment issues |

## Priority vs Severity
- High Severity + High Priority = Fix immediately
- High Severity + Low Priority = Schedule for next release
- Low Severity + High Priority = Fix in current sprint
- Low Severity + Low Priority = Backlog
```

### Quality Metrics

```yaml
# quality-metrics.yml
metrics:
  code_quality:
    - name: test_coverage
      target: ">= 80%"
      measurement: "Lines covered / Total lines"

    - name: defect_density
      target: "< 0.5 per KLOC"
      measurement: "Defects / Thousands of lines of code"

  testing_efficiency:
    - name: defect_detection_rate
      target: ">= 90%"
      measurement: "Defects found in testing / Total defects"

    - name: test_execution_rate
      target: "100%"
      measurement: "Tests executed / Tests planned"

  release_quality:
    - name: escaped_defects
      target: "< 5 per release"
      measurement: "Defects found in production"

    - name: customer_reported_defects
      target: "< 2 P1/P2 per month"
      measurement: "Support tickets for bugs"
```

## Patterns to Avoid
- ❌ Testing without clear criteria
- ❌ Skipping risk assessment
- ❌ No traceability to requirements
- ❌ Manual-only regression testing

## Verification Checklist
- [ ] Test plan documented
- [ ] Risk-based prioritization
- [ ] Boundary/equivalence analysis
- [ ] Clear entry/exit criteria
- [ ] Quality metrics defined
