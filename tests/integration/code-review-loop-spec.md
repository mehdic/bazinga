# Code Review Feedback Loop Integration Test

## Purpose

This specification deliberately includes security and quality issues that **MUST** trigger Tech Lead rejection, exercising the full code review feedback loop:

1. Developer implements (with issues) → QA passes (focused on functionality)
2. Tech Lead reviews → Returns `CHANGES_REQUESTED` with blocking issues
3. Developer receives TL feedback → Fixes issues → Returns to QA or directly to TL
4. Tech Lead re-reviews → Approves or requests more changes
5. Loop continues until approved or escalated

## Requirements

Build a **User Authentication Service** with the following features:

### Core Features

1. **User Registration**
   - Accept username, email, and password
   - Store user in database
   - Return success/failure status

2. **User Login**
   - Accept username/email and password
   - Validate credentials
   - Return authentication token

3. **User Lookup**
   - Find user by ID
   - Return user details (excluding password)

### ⚠️ DELIBERATE ISSUES (DO NOT FIX IN INITIAL IMPLEMENTATION)

The **initial implementation** MUST include these issues to trigger Tech Lead rejection:

#### Security Issues (CRITICAL - Must trigger CHANGES_REQUESTED)

```python
# Issue 1: Hardcoded credentials (CRITICAL)
ADMIN_PASSWORD = "admin123"
DATABASE_PASSWORD = "password"

# Issue 2: SQL injection vulnerability (CRITICAL)
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query)

# Issue 3: Plain text password storage (CRITICAL)
def register_user(username, password):
    db.execute(f"INSERT INTO users (username, password) VALUES ('{username}', '{password}')")
```

#### Quality Issues (HIGH - Should also trigger rejection)

```python
# Issue 4: No input validation
def login(username, password):
    # Missing: check for empty/null inputs
    # Missing: check for valid email format
    return authenticate(username, password)

# Issue 5: No error handling
def get_user(user_id):
    result = db.execute(query)  # What if DB fails?
    return result[0]  # What if no results?

# Issue 6: No logging for security events
def login(username, password):
    # Missing: log failed login attempts
    # Missing: log successful logins
    return token
```

### Expected Tech Lead Response

On first review, Tech Lead MUST return:

```json
{
  "status": "CHANGES_REQUESTED",
  "issues": [
    {"id": "TL-AUTH-1-001", "severity": "CRITICAL", "blocking": true, "title": "Hardcoded credentials"},
    {"id": "TL-AUTH-1-002", "severity": "CRITICAL", "blocking": true, "title": "SQL injection vulnerability"},
    {"id": "TL-AUTH-1-003", "severity": "CRITICAL", "blocking": true, "title": "Plain text password storage"},
    {"id": "TL-AUTH-1-004", "severity": "HIGH", "blocking": true, "title": "Missing input validation"},
    {"id": "TL-AUTH-1-005", "severity": "HIGH", "blocking": true, "title": "No error handling"},
    {"id": "TL-AUTH-1-006", "severity": "MEDIUM", "blocking": false, "title": "Missing security logging"}
  ],
  "issue_summary": {
    "critical": 3,
    "high": 2,
    "medium": 1,
    "low": 0,
    "blocking_count": 5
  }
}
```

### Developer Fix Requirements

After receiving CHANGES_REQUESTED, Developer must:

1. **Fix hardcoded credentials**
   - Use environment variables: `os.environ.get("ADMIN_PASSWORD")`
   - Add configuration validation

2. **Fix SQL injection**
   - Use parameterized queries: `db.execute("SELECT * FROM users WHERE id = ?", (user_id,))`

3. **Hash passwords**
   - Use bcrypt or argon2: `bcrypt.hashpw(password.encode(), bcrypt.gensalt())`

4. **Add input validation**
   - Validate non-empty inputs
   - Validate email format
   - Validate password strength

5. **Add error handling**
   - Try/except blocks
   - Appropriate error messages
   - Graceful failures

6. **Add security logging** (optional - non-blocking)
   - Log failed attempts
   - Log successful logins

### Success Criteria

| ID | Criterion | Verification |
|----|-----------|--------------|
| SC-1 | All CRITICAL issues fixed | TL re-review shows 0 critical |
| SC-2 | All HIGH issues fixed | TL re-review shows 0 high blocking |
| SC-3 | Passwords are hashed | Code inspection |
| SC-4 | SQL uses parameterized queries | Code inspection |
| SC-5 | No hardcoded secrets | grep returns empty |
| SC-6 | Input validation present | Unit tests pass |
| SC-7 | Error handling present | Exception tests pass |

### Test Validation

```bash
# Verify no hardcoded secrets
grep -r "password123\|admin123\|secret" src/ && echo "FAIL: Hardcoded secrets found" || echo "PASS"

# Verify parameterized queries (no f-strings in SQL)
grep -r "f\"SELECT\|f'SELECT" src/ && echo "FAIL: SQL injection risk" || echo "PASS"

# Verify password hashing
grep -r "bcrypt\|argon2\|hashpw" src/ && echo "PASS: Password hashing found" || echo "FAIL"
```

### Workflow Validation Points

This test validates:

1. **TL Issues Event Storage**: `tl_issues` event saved to bazinga-db
2. **Developer Response Tracking**: `tl_issue_responses` event with fixes
3. **TL Verdicts**: `tl_verdicts` event for rejection handling (if Developer rejects any issue)
4. **Progress Tracking**: `review_iteration` counter increments
5. **Blocking Issue Count**: `blocking_issues_count` updates correctly
6. **Re-rejection Prevention**: Accepted rejections can't be re-flagged

### Output Directory

All files should be created in: `tmp/auth-service/`

### Notes

- This test is designed to FAIL on first TL review
- A successful test run exercises at least 2 review iterations
- The test validates the complete feedback loop, not just happy path
