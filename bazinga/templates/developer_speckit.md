# Developer Spec-Kit Integration Mode

**Single Source of Truth** - Shared by Developer and Senior Software Engineer agents
**Version:** 1.0.0
**Last Updated:** 2025-12-03

---

## What is Spec-Kit Integration?

When BAZINGA orchestration integrates with GitHub's spec-kit workflow, you receive pre-planned tasks with:
- **Task IDs**: Unique identifiers (T001, T002, T003, etc.)
- **Feature directory**: Path to spec-kit artifacts (`.specify/features/XXX/`)
- **Context documents**: spec.md (requirements), plan.md (architecture), tasks.md (task list)

## Key Differences in Spec-Kit Mode

| Standard Mode | Spec-Kit Mode |
|---------------|---------------|
| PM gives you requirements | spec.md provides detailed requirements |
| Free-form implementation | Follow technical approach in plan.md |
| Self-defined tasks | Assigned specific task IDs from tasks.md |
| Your own testing approach | May include test specifications in tasks |
| No progress tracking file | Update tasks.md with checkmarks [x] |

## How to Detect Spec-Kit Mode

Your assignment from PM will include:
1. Explicit statement: "SPEC-KIT INTEGRATION ACTIVE"
2. Feature directory path (e.g., `.specify/features/001-jwt-auth/`)
3. Your assigned task IDs (e.g., ["T002", "T003"])
4. Your task descriptions from tasks.md
5. Paths to spec.md, plan.md, and other context documents

## Modified Workflow in Spec-Kit Mode

### Step 1: Read Your Assigned Tasks

PM assigns you specific task IDs. Example:
```
**Your Task IDs**: [T002, T003]

**Your Task Descriptions** (from tasks.md):
- [ ] [T002] [P] [US1] JWT token generation (auth/jwt.py)
- [ ] [T003] [P] [US1] Token validation (auth/jwt.py)
```

### Step 2: Read Context Documents

**REQUIRED Reading** (before implementing):
```
feature_dir = [provided by PM, e.g., ".specify/features/001-jwt-auth/"]

# MUST READ:
spec_md = read_file(f"{feature_dir}/spec.md")
plan_md = read_file(f"{feature_dir}/plan.md")
tasks_md = read_file(f"{feature_dir}/tasks.md")

# Recommended (if exists):
if file_exists(f"{feature_dir}/research.md"):
    research_md = read_file(f"{feature_dir}/research.md")

if file_exists(f"{feature_dir}/data-model.md"):
    data_model_md = read_file(f"{feature_dir}/data-model.md")

if directory_exists(f"{feature_dir}/contracts/"):
    # Read API contracts for your endpoints
    contracts = read_files_in(f"{feature_dir}/contracts/")
```

**Why Read These**:
- **spec.md**: Understand what the feature should do (requirements, acceptance criteria, edge cases)
- **plan.md**: Understand HOW to implement (libraries, patterns, architecture decisions)
- **tasks.md**: See ALL tasks (understand dependencies, see what others are working on)
- **data-model.md**: Understand data structures you'll be working with
- **contracts/**: Understand API interfaces you need to implement

### Step 3: Understand Your Task Context

From tasks.md, understand:

**Task Format**:
```
- [ ] [TaskID] [Markers] Description (file.py)

Where:
- TaskID: Your assigned ID (T002, T003, etc.)
- Markers: [P] = parallel task
           [US1], [US2] = user story grouping
- Description: What you need to do
- (file.py): File you'll be working in
```

**Dependencies**:
```
Look at OTHER tasks in tasks.md to understand:
- What was done before you (tasks with lower IDs)
- What depends on your work (tasks with higher IDs in your user story)
- What other developers are doing (different user story markers)

Example:
If you see:
- [x] [T001] Setup: Create auth module (auth/__init__.py)  ← Already done
- [ ] [T002] [US1] JWT generation (auth/jwt.py)            ← Your task
- [ ] [T003] [US1] Token validation (auth/jwt.py)          ← Your task
- [ ] [T004] [US2] Login endpoint (api/login.py)           ← Depends on your work

You know:
- auth module already exists (T001 is checked)
- You need to implement in auth/jwt.py
- Login endpoint (T004) will depend on your JWT functions
```

### Step 4: Implement Following Spec-Kit Methodology

**Follow the Plan**:
```
From plan.md, extract:
- Libraries to use (e.g., "Use PyJWT for token generation")
- Patterns to follow (e.g., "Use decorator pattern for auth middleware")
- Architecture decisions (e.g., "Store tokens in Redis with 1-hour TTL")
- Security requirements (e.g., "Use HS256 algorithm, 256-bit secrets")

Implement EXACTLY as planned.
```

**Follow the Spec**:
```
From spec.md, extract:
- Functional requirements (what it must do)
- Acceptance criteria (how to know it's complete)
- Edge cases (error handling scenarios)
- User scenarios (how it will be used)

Ensure your implementation satisfies ALL criteria.
```

**Follow TDD if Specified**:
```
If tasks.md says "write tests first":
1. Write test cases based on spec.md acceptance criteria
2. Run tests (they should fail initially)
3. Implement code to make tests pass
4. Refactor
5. Repeat for each task
```

### Step 5: Update tasks.md as You Complete Tasks

**CRITICAL**: After completing EACH task, mark it complete in tasks.md

**How to Update**:
```
Use Edit tool to mark tasks complete:

Before (when you start):
- [ ] [T002] [P] [US1] JWT token generation (auth/jwt.py)

After (when you finish T002):
- [x] [T002] [P] [US1] JWT token generation (auth/jwt.py)

Then move to next task:
- [ ] [T003] [P] [US1] Token validation (auth/jwt.py)

After (when you finish T003):
- [x] [T003] [P] [US1] Token validation (auth/jwt.py)
```

**Update Incrementally**:
- Don't wait until all tasks are done
- Mark each task as you complete it
- This provides real-time progress visibility

**Edit Tool Example**:
```
Edit(
  file_path="{feature_dir}/tasks.md",
  old_string="- [ ] [T002] [P] [US1] JWT token generation (auth/jwt.py)",
  new_string="- [x] [T002] [P] [US1] JWT token generation (auth/jwt.py)"
)
```

### Step 6: Enhanced Reporting

Include in your status report:

```markdown
## Implementation Complete - Group {group_id}

### Spec-Kit Tasks Completed
- [x] T002: JWT token generation
- [x] T003: Token validation

### Files Modified
- auth/jwt.py (created, 150 lines)
- tests/test_jwt.py (created, 80 lines)

### Spec.md Requirements Met
**From spec.md acceptance criteria:**
- Generate JWT tokens with user ID and expiration
- Support both access tokens (1 hour) and refresh tokens (7 days)
- Validate token signatures and expiration
- Handle expired tokens gracefully with appropriate error messages
- Support token refresh flow

**From spec.md edge cases:**
- Handle malformed tokens
- Handle tokens with invalid signatures
- Handle missing token payloads
- Handle clock skew (5-minute tolerance)

### Plan.md Approach Followed
**From plan.md technical decisions:**
- Used PyJWT library (version 2.8.0) as specified
- Implemented HS256 algorithm with 256-bit secret
- Token payload structure matches plan:
  ```json
  {
    "user_id": "uuid",
    "exp": "timestamp",
    "iat": "timestamp",
    "type": "access|refresh"
  }
  ```
- Secret key loaded from environment variable JWT_SECRET
- Implemented helper functions: generate_token(), validate_token(), refresh_token()

### tasks.md Updated
Updated {feature_dir}/tasks.md with checkmarks for T002, T003

### Tests Created/Fixed
**YES** - Integration tests created

**Test Coverage**:
- Unit tests: 12 tests, all passing
- Integration tests: 5 tests, all passing
- Total coverage: 95%

**Test Files**:
- tests/test_jwt.py (JWT generation and validation)
- tests/integration/test_auth_flow.py (End-to-end auth flow)

### Branch
{branch_name}

### Commits
- abc1234: Implement JWT token generation with PyJWT
- def5678: Add token validation with signature verification
- ghi9012: Add integration tests for auth flow

### Status
**READY_FOR_QA** (tests exist)

### Next Step
Orchestrator, please forward to QA Expert for integration/contract/E2E testing.
```

---

## Example: Spec-Kit Mode Development Flow

**Scenario**: You're assigned Group US1 with tasks T002, T003 for JWT authentication.

**1. Receive Assignment**:
```
From PM via Orchestrator:
**SPEC-KIT INTEGRATION ACTIVE**
**Group**: US1
**Task IDs**: [T002, T003]
**Feature Dir**: .specify/features/001-jwt-auth/
**Your Files**: auth/jwt.py
```

**2. Read Context**:
```bash
# Read requirements
Read spec.md:
- Feature: JWT authentication with access/refresh tokens
- Must support HS256 algorithm
- Access tokens expire in 1 hour
- Refresh tokens expire in 7 days
- Must validate signatures

# Read technical approach
Read plan.md:
- Use PyJWT library
- Store secrets in environment variables
- Implement three functions: generate, validate, refresh
- Use decorator pattern for protected routes
- Add middleware for automatic validation

# Read your tasks
Read tasks.md:
- [x] [T001] Setup: Create auth module (done by previous dev)
- [ ] [T002] [P] [US1] JWT token generation (auth/jwt.py) ← You
- [ ] [T003] [P] [US1] Token validation (auth/jwt.py) ← You
- [ ] [T004] [US2] Login endpoint (api/login.py) ← Depends on you
```

**3. Implement T002 (JWT Generation)**:
```python
# auth/jwt.py
import jwt
import os
from datetime import datetime, timedelta

def generate_token(user_id: str, token_type: str = "access") -> str:
    """Generate JWT token following plan.md specifications."""
    secret = os.environ.get("JWT_SECRET")
    if not secret:
        raise RuntimeError("JWT_SECRET environment variable is not set")

    # Expiration based on token type (from spec.md)
    expiry = timedelta(hours=1) if token_type == "access" else timedelta(days=7)

    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + expiry,
        "iat": datetime.utcnow(),
        "type": token_type
    }

    # Use HS256 as specified in plan.md
    return jwt.encode(payload, secret, algorithm="HS256")
```

**4. Update tasks.md**:
```
Edit tasks.md:
- [x] [T002] [P] [US1] JWT token generation (auth/jwt.py) Marked complete
```

**5. Implement T003 (Token Validation)**:
```python
# Custom exceptions (define in auth/exceptions.py)
class TokenExpiredError(Exception):
    """Raised when JWT token has expired."""
    pass

class InvalidTokenError(Exception):
    """Raised when JWT token is invalid (malformed or bad signature)."""
    pass

def validate_token(token: str) -> dict:
    """Validate JWT token following plan.md specifications."""
    secret = os.environ.get("JWT_SECRET")
    if not secret:
        raise RuntimeError("JWT_SECRET environment variable is not set")

    try:
        # Validate signature and expiration (from spec.md edge cases)
        # leeway=300 allows 5-minute clock skew tolerance between servers
        payload = jwt.decode(token, secret, algorithms=["HS256"], leeway=300)
        return payload
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError("Token has expired")
    except jwt.InvalidSignatureError:
        raise InvalidTokenError("Invalid token signature")
    except jwt.DecodeError:
        raise InvalidTokenError("Malformed token")
```

**6. Update tasks.md Again**:
```
Edit tasks.md:
- [x] [T003] [P] [US1] Token validation (auth/jwt.py) Marked complete
```

**7. Write Tests (TDD)**:
```python
# tests/test_jwt.py
from freezegun import freeze_time  # Recommended for datetime mocking

# Custom exceptions (define in auth/exceptions.py or use your framework's)
class TokenExpiredError(Exception):
    """Raised when JWT token has expired."""
    pass

class InvalidTokenError(Exception):
    """Raised when JWT token is invalid (malformed or bad signature)."""
    pass

def test_generate_access_token():
    token = generate_token("user123", "access")
    payload = validate_token(token)
    assert payload["user_id"] == "user123"
    assert payload["type"] == "access"

def test_token_expiration():
    # Use freezegun to mock time (patches datetime where it's used)
    with freeze_time("2024-01-01 12:00:00"):
        token = generate_token("user123")

    # Move time forward past expiration
    with freeze_time("2024-01-01 14:00:00"):  # 2 hours later
        with pytest.raises(TokenExpiredError):
            validate_token(token)

# Alternative without freezegun: patch where datetime is imported
def test_token_expiration_alt():
    # Patch datetime in the module where it's USED, not datetime module itself
    with patch("auth.jwt.datetime") as mock_datetime:
        mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.side_effect = lambda *a, **kw: datetime(*a, **kw)
        token = generate_token("user123")

    # Validate with real time (token will be expired)
    with pytest.raises(TokenExpiredError):
        validate_token(token)
```

**8. Run Tests**:
```bash
pytest tests/test_jwt.py -v
# All 12 tests passing
```

**9. Report Completion**:
```
Send enhanced report (as shown above) with:
- Tasks completed (T002, T003)
- Requirements met from spec.md
- Approach followed from plan.md
- tasks.md updated
- Tests passing
- Status: READY_FOR_QA
```

---

## Key Takeaways for Spec-Kit Mode

1. **Read before coding** - spec.md and plan.md are your guides
2. **Follow the plan** - Don't deviate from technical approach in plan.md
3. **Meet all criteria** - Check every acceptance criterion in spec.md
4. **Update tasks.md** - Mark each task [x] as you complete it
5. **Reference task IDs** - Always mention task IDs in commits and reports
6. **Enhanced reporting** - Show how you met spec.md and followed plan.md
7. **Understand context** - Read tasks.md to see what others are doing

## Spec-Kit Mode Checklist

Before marking "READY_FOR_QA" or "READY_FOR_REVIEW":

- [ ] Read spec.md and understand requirements
- [ ] Read plan.md and follow technical approach
- [ ] Read tasks.md to understand your tasks
- [ ] Implement all assigned task IDs
- [ ] Update tasks.md with [x] for each completed task
- [ ] Meet all acceptance criteria from spec.md
- [ ] Follow all technical decisions from plan.md
- [ ] Write and run tests (if required)
- [ ] Reference task IDs in commit messages
- [ ] Enhanced report showing spec/plan compliance
