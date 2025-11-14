# BAZINGA - Claude Code Multi-Agent Dev Team - Usage Examples

> **Repository:** https://github.com/mehdic/bazinga

This document provides practical examples of using BAZINGA (Claude Code Multi-Agent Dev Team).

## Quick Start Examples

### Example 1: Simple Feature with Tests

**User Request:**
```
/bazinga.orchestrate implement JWT authentication with token generation and validation
```
(or: `@orchestrator implement JWT authentication with token generation and validation`)

**What Happens:**

1. **PM analyzes** (spawned by orchestrator):
   ```
   ## PM Decision: SIMPLE MODE

   ### Analysis
   - Features identified: 1 (JWT authentication)
   - File overlap: N/A (single feature)
   - Dependencies: None
   - Recommended parallelism: 1 developer

   ### Task Group Created
   **Group Main: JWT Authentication**
   - Tasks: Token generation, validation middleware, tests
   - Files: auth.py, middleware.py, test_auth.py
   - Estimated effort: 15 minutes

   ### Next Action
   **Status:** PLANNING_COMPLETE
   **Next Action:** Orchestrator should spawn 1 developer for group: Main
   ```

2. **Developer implements**:
   ```
   ## Implementation Complete

   **Summary:** Implemented JWT authentication with token generation and validation

   **Files Modified:**
   - src/auth/jwt_handler.py (created)
   - src/middleware/auth.py (created)
   - tests/integration/test_jwt_auth.py (created)

   **Key Changes:**
   - JWT token generation using HS256
   - Token validation middleware
   - Integration tests for auth flow

   **Tests:**
   - Total: 8
   - Passing: 8
   - Failing: 0

   **Tests Created/Fixed:** YES (8 integration tests)

   **Status:** READY_FOR_QA
   **Next Step:** Orchestrator, please forward to QA Expert for testing
   ```

3. **QA Expert tests**:
   ```
   ## QA Expert: Test Results - PASS ✅

   All tests passed successfully for Group Main: JWT Authentication

   ### Test Summary
   **Integration Tests**: 8/8 passed (30s)
   **Contract Tests**: 4/4 passed (10s)
   **E2E Tests**: 3/3 passed (45s)

   **Total Tests**: 15/15 passed
   **Total Duration**: 1m 25s

   **Status:** PASS
   **Next Step:** Orchestrator, please forward to Tech Lead for code quality review
   ```

4. **Tech Lead reviews**:
   ```
   ## Review: APPROVED

   **What Was Done Well:**
   - Clean JWT implementation
   - Comprehensive test coverage
   - Proper error handling

   **Code Quality:** Excellent

   **Ready for Production:** YES ✅

   **Status:** APPROVED
   **Next Step:** Orchestrator, please forward to PM for completion tracking
   ```

5. **PM completes**:
   ```
   ## PM Final Report

   ### All Tasks Complete ✅

   All task groups successfully completed:
   - Group Main: JWT Authentication ✅

   ### BAZINGA

   Project complete! All requirements met.

   **Status:** COMPLETE
   ```

**Result:** Feature implemented, tested, reviewed, and approved automatically.

---

### Example 2: Refactoring without Tests

**User Request:**
```
/bazinga.orchestrate refactor the error handling in the authentication middleware for better clarity
```

**What Happens:**

1. **PM analyzes**:
   ```
   ## PM Decision: SIMPLE MODE

   ### Task Group Created
   **Group Main: Refactor Error Handling**
   - Tasks: Improve error messages, standardize error responses
   - Files: middleware/auth.py, utils/errors.py
   - Estimated effort: 10 minutes

   **Status:** PLANNING_COMPLETE
   **Next Action:** Orchestrator should spawn 1 developer
   ```

2. **Developer refactors**:
   ```
   ## Implementation Complete

   **Summary:** Refactored error handling for better clarity

   **Files Modified:**
   - middleware/auth.py (modified)
   - utils/errors.py (modified)

   **Key Changes:**
   - Standardized error message format
   - Extracted error handling to utility
   - Improved HTTP status codes

   **Tests:** N/A (refactoring only, existing tests still pass)

   **Tests Created/Fixed:** NO (refactoring only)

   **Status:** READY_FOR_REVIEW
   **Next Step:** Orchestrator, please forward to Tech Lead for code review
   ```

3. **Tech Lead reviews** (QA skipped - no tests):
   ```
   ## Review: APPROVED

   **What Was Done Well:**
   - Improved code clarity
   - Better error messages
   - Consistent error handling

   **Status:** APPROVED
   **Next Step:** Orchestrator, please forward to PM for completion tracking
   ```

4. **PM completes**:
   ```
   ### BAZINGA

   **Status:** COMPLETE
   ```

**Result:** Refactoring done and approved, QA skipped (no new tests to run).

---

### Example 3: Parallel Development

**User Request:**
```
/bazinga.orchestrate implement three features: JWT authentication, user registration, and password reset
```

**What Happens:**

1. **PM analyzes**:
   ```
   ## PM Decision: PARALLEL MODE

   ### Analysis
   - Features identified: 3
   - File overlap: LOW (different modules)
   - Dependencies: Password reset depends on auth
   - Recommended parallelism: 2 developers initially

   ### Task Groups Created
   **Group A: JWT Authentication**
   - Files: auth.py, test_auth.py
   - Can parallel: YES

   **Group B: User Registration**
   - Files: users.py, test_users.py
   - Can parallel: YES

   **Group C: Password Reset**
   - Files: password_reset.py, test_reset.py
   - Can parallel: NO (depends on A)

   ### Execution Plan
   Phase 1: Groups A, B (parallel with 2 developers)
   Phase 2: Group C (after A complete)

   **Status:** PLANNING_COMPLETE
   **Next Action:** Orchestrator should spawn 2 developers for groups: A, B
   ```

2. **Developer 1 (Group A)** and **Developer 2 (Group B)** work in parallel:
   ```
   [Both implement simultaneously]
   Both: Status READY_FOR_QA
   ```

3. **QA Expert tests both groups** (may be sequential or parallel based on orchestrator):
   ```
   Group A: PASS
   Group B: PASS
   ```

4. **Tech Lead reviews both**:
   ```
   Group A: APPROVED
   Group B: APPROVED
   ```

5. **PM receives both approvals**:
   ```
   ## PM Status Update

   ### Progress
   - Completed: A ✅, B ✅
   - Pending: C

   ### Next Assignment
   Group C can now proceed (depends on A which is complete)

   **Status:** IN_PROGRESS
   **Next Action:** Orchestrator should spawn 1 developer for group: C
   ```

6. **Developer 3 (Group C)** implements:
   ```
   [Implements → QA → Tech Lead → Approved]
   ```

7. **PM completes**:
   ```
   ### All Tasks Complete ✅
   - Group A: JWT Authentication ✅
   - Group B: User Registration ✅
   - Group C: Password Reset ✅

   ### BAZINGA

   **Status:** COMPLETE
   ```

**Result:** 3 features implemented, 2 in parallel (1.5-2x speedup), all tested and approved.

---

### Example 4: Test Failures and Recovery

**User Request:**
```
/bazinga.orchestrate implement rate limiting on the authentication endpoint
```

**What Happens:**

1. **Developer implements** with tests:
   ```
   **Status:** READY_FOR_QA
   ```

2. **QA Expert tests - FAIL**:
   ```
   ## QA Expert: Test Results - FAIL ❌

   **Integration Tests**: 3/5 passed (FAILED)

   ### Detailed Failures

   #### Integration Failure 1: Rate Limiting Not Working
   **Test**: test_rate_limiting_enforcement
   **Error**: 11th request succeeded, should be rate limited
   **Impact**: CRITICAL - security vulnerability

   ### Recommendation
   **Send back to Developer** to fix rate limiting logic

   **Status:** FAIL
   **Next Step:** Orchestrator, please send back to Developer to fix test failures
   ```

3. **Developer fixes**:
   ```
   ## Feedback Addressed

   **Issue 1:** Rate limiting not working
   - **Fixed:** ✅ Applied rate limiting middleware to auth endpoint

   **All tests passing:** 5/5

   **Tests Created/Fixed:** YES (fixed rate limiting test)

   **Status:** READY_FOR_QA
   **Next Step:** Orchestrator, please forward to QA Expert for re-testing
   ```

4. **QA Expert retests**:
   ```
   ## QA Expert: Test Results - PASS ✅

   All tests now passing: 5/5

   **Status:** PASS
   **Next Step:** Orchestrator, please forward to Tech Lead
   ```

5. **Tech Lead reviews and approves**, PM sends BAZINGA.

**Result:** Automatic failure detection, developer fix, retest, and approval.

---

## Common Scenarios

### Scenario: Developer Gets Blocked

**Developer:**
```
## Blocked

**Blocker:** Migration conflict - user_id column already exists

**What I Tried:**
1. DROP and re-ADD column → Error
2. ALTER instead of ADD → Still conflicts

**Status:** BLOCKED
**Next Step:** Orchestrator, please forward to Tech Lead for unblocking guidance
```

**Tech Lead:**
```
## Unblocking Guidance

**Solution:** Make migration idempotent

**Steps:**
1. Check if column exists before adding
2. Use conditional SQL: `IF NOT EXISTS`

**Status:** UNBLOCKING_GUIDANCE_PROVIDED
**Next Step:** Orchestrator, please forward to Developer to continue
```

**Developer continues with solution.**

---

### Scenario: Tech Lead Requests Changes

**Tech Lead:**
```
## Review: CHANGES REQUESTED

**Issues Found:**

### 1. [CRITICAL] SQL Injection Vulnerability
**Location:** auth.py:45
**Problem:** User input in SQL query

**Current:** `cursor.execute(f'SELECT * FROM users WHERE email={email}')`
**Should be:** `cursor.execute('SELECT * FROM users WHERE email=?', (email,))`

**Status:** CHANGES_REQUESTED
**Next Step:** Orchestrator, please send back to Developer
```

**Developer fixes, routes back through QA and Tech Lead.**

---

### Scenario: PM Autonomy (Never Asks User)

**WRONG (Old Behavior):**
```
PM: Some tests are failing. Do you want me to continue fixing them?
```

**CORRECT (Current Behavior):**
```
## PM Status Update

Test failures detected in Group A. Assigning developer to fix issues.

### Next Assignment
Orchestrator should spawn developer for group A with QA feedback.

**Status:** REASSIGNING_FOR_FIXES
**Next Action:** Orchestrator should spawn developer for group A
```

PM continues autonomously until BAZINGA.

---

## Tips for Users

### Get Better Results

1. **Be specific in requests**: "Implement JWT auth with refresh tokens" vs "Add auth"
2. **Mention test requirements**: "with comprehensive tests" ensures developer creates tests
3. **Specify constraints**: "Must be backward compatible" guides decisions
4. **Trust the process**: Let agents work through failures autonomously

### Understanding Status Messages

- `PLANNING_COMPLETE`: PM finished planning, ready to spawn developers
- `READY_FOR_QA`: Developer has tests, needs QA validation
- `READY_FOR_REVIEW`: Developer has no tests, skip to Tech Lead
- `PASS/FAIL`: QA test results
- `APPROVED/CHANGES_REQUESTED`: Tech Lead review results
- `BAZINGA`: Project 100% complete

### When to Intervene

**Let it work autonomously for:**
- Test failures (will auto-fix)
- Code review feedback (will auto-address)
- Simple blockers (Tech Lead will unblock)

**Consider intervening for:**
- Fundamental requirement changes
- External blockers (API keys, permissions)
- Direction changes mid-project

---

## Advanced Usage

### Custom Task Groups

You can guide PM by being specific:

```
/bazinga.orchestrate implement these as separate task groups:
1. JWT authentication (auth.py)
2. User registration (users.py)
3. Password reset (password_reset.py)

Groups 1 and 2 can be parallel. Group 3 depends on 1.
```

PM will respect your guidance while applying its decision logic.

### Forcing Simple Mode

```
/bazinga.orchestrate implement JWT auth (please use simple sequential mode)
```

PM will likely honor this request.

### Requesting More Tests

```
/bazinga.orchestrate implement JWT auth with comprehensive integration, contract, and E2E tests
```

Developer will create all test types, ensuring QA involvement.

---

## Debugging

### Check Orchestrator Role

If orchestrator seems to be implementing instead of routing, look for:
```
🔄 **ORCHESTRATOR ROLE CHECK**: I am a coordinator. I spawn agents, I do not implement.
```

If missing, orchestrator has role drift. Remind it of its role.

### Check PM Autonomy

If PM asks "Should I continue?", PM has lost autonomy. Remind it:
- PM is fully autonomous
- Never ask user questions
- Continue until BAZINGA

### Check Routing

If workflow skips agents (e.g., Dev → PM directly), check:
- Developer should output explicit routing: "Next Step: Orchestrator, please forward to..."
- QA should only be skipped if "Tests Created/Fixed: NO"

---

**For more examples and patterns, see the ARCHITECTURE.md documentation.**
