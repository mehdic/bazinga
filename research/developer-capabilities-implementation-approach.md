# Developer Capabilities: Skills vs Other Approaches

**Status**: Implementation Guide
**Created**: 2025-11-07
**Priority**: High

## Summary

Of the 5 proposed capabilities, **2 should be Skills** and **3 should use other approaches**.

---

## ✅ SHOULD BE SKILLS (Model-Invoked Tools)

### 1. Pre-Commit Validation Skill ⚡ TIER 1 - REUSE EXISTING

**Type:** Skill (reuse existing `lint-check` Skill)

**Why it's a Skill:**
- ✅ Invokes external tools (ruff, eslint, tsc, golangci-lint, checkstyle)
- ✅ Returns structured output (JSON with issues)
- ✅ Model-invoked (Developer calls before commit)
- ✅ Already exists as `lint-check` Skill - just reuse it!

**Implementation:**
```markdown
Developer workflow:
1. Complete implementation
2. Invoke lint-check Skill: `/lint-check`
3. Read results from bazinga/lint_results.json
4. If issues found: fix them, retry
5. When clean: commit
```

**Location:** Already exists at `.claude/skills/lint-check/`

**Effort:** Zero - already implemented, just change Developer workflow

**Note:** This is NOT a new Skill - we already have it for Tech Lead. We just need Developer to use it BEFORE committing instead of Tech Lead catching issues AFTER commit.

---

### 2. Codebase Analysis Skill 📊 TIER 2 - NEW SKILL

**Type:** New Skill

**Why it's a Skill:**
- ✅ Complex analysis requiring tools (AST parsing, grep, similarity)
- ✅ Returns structured output (JSON with patterns, utilities, suggestions)
- ✅ Model-invoked (Developer calls before implementation)
- ✅ Reusable across different Developer instances
- ✅ Time-consuming (10-20 seconds) - better as background tool

**Output:** `bazinga/codebase_analysis.json`

```json
{
  "task": "Implement password reset",
  "similar_features": [
    {
      "file": "user_registration.py",
      "similarity_score": 0.85,
      "patterns": ["email validation", "token generation", "service layer"],
      "key_functions": ["generate_token()", "send_email()"]
    }
  ],
  "reusable_utilities": [
    {"name": "EmailService", "file": "utils/email.py", "functions": ["send_email()"]},
    {"name": "TokenGenerator", "file": "utils/tokens.py", "functions": ["generate_token()"]}
  ],
  "architectural_patterns": [
    "Service layer pattern (services/)",
    "Repository pattern (repositories/)",
    "Factory pattern (factories/)"
  ],
  "suggested_approach": "Create PasswordResetService in services/, use existing EmailService and TokenGenerator",
  "conventions": [
    "All business logic goes in services/",
    "Use error_response() for errors from utils/responses.py",
    "80% test coverage minimum"
  ]
}
```

**Tools/Tech:**
- Python AST parsing (`ast` module)
- Text similarity (cosine similarity, TF-IDF)
- Grep for pattern detection
- File analysis

**Skill Structure:**
```
.claude/skills/codebase-analysis/
├── SKILL.md              # Skill definition
├── analyze.py            # Main analysis script
├── similarity.py         # Text similarity functions
└── patterns.py           # Pattern detection
```

**Developer Usage:**
```bash
# Developer invokes before coding
/codebase-analysis "Implement password reset endpoint"

# Skill analyzes codebase
# Writes results to bazinga/codebase_analysis.json

# Developer reads results
cat bazinga/codebase_analysis.json

# Developer uses patterns and utilities from analysis
```

---

### 3. Test Pattern Analysis Skill 🧪 TIER 2 - NEW SKILL

**Type:** New Skill

**Why it's a Skill:**
- ✅ Complex analysis (test framework detection, fixture extraction)
- ✅ Returns structured output (JSON with test patterns)
- ✅ Model-invoked (Developer calls before writing tests)
- ✅ Reusable across projects
- ✅ Specialized logic (test-specific analysis)

**Output:** `bazinga/test_patterns.json`

```json
{
  "framework": "pytest",
  "version": "7.4.0",
  "test_directory": "tests/",
  "common_fixtures": [
    {
      "name": "test_client",
      "file": "tests/conftest.py",
      "scope": "function",
      "usage": "Provides Flask test client"
    },
    {
      "name": "mock_db",
      "file": "tests/conftest.py",
      "scope": "function",
      "usage": "Provides mocked database"
    }
  ],
  "test_patterns": {
    "structure": "AAA (Arrange-Act-Assert)",
    "naming": "test_<function>_<scenario>_<expected>",
    "example": "test_login_valid_credentials_returns_token"
  },
  "similar_tests": [
    {
      "file": "tests/test_user_registration.py",
      "test_name": "test_registration_valid_email",
      "pattern": "AAA",
      "coverage": "92%",
      "edge_cases": ["invalid email", "duplicate user", "db failure"]
    }
  ],
  "suggested_tests": [
    "test_password_reset_valid_email_sends_token",
    "test_password_reset_invalid_email_returns_error",
    "test_password_reset_expired_token_returns_error",
    "test_password_reset_db_failure_handles_gracefully"
  ],
  "coverage_target": "80%",
  "utilities": [
    {"name": "assert_email_sent", "file": "tests/helpers.py"},
    {"name": "create_test_user", "file": "tests/fixtures.py"}
  ]
}
```

**Tools/Tech:**
- Test framework detection (pytest, jest, go test, junit)
- Test file parsing
- Fixture extraction
- Pattern analysis

**Skill Structure:**
```
.claude/skills/test-pattern-analysis/
├── SKILL.md              # Skill definition
├── analyze_tests.py      # Main analysis script
├── frameworks.py         # Framework detection
└── patterns.py           # Pattern extraction
```

**Developer Usage:**
```bash
# Developer invokes before writing tests
/test-pattern-analysis tests/

# Skill analyzes existing tests
# Writes results to bazinga/test_patterns.json

# Developer reads patterns
cat bazinga/test_patterns.json

# Developer follows patterns and uses fixtures
```

---

## ❌ SHOULD NOT BE SKILLS (Other Approaches)

### 1. Code Context Injection 🎯 TIER 1 - ORCHESTRATOR LOGIC

**Type:** Orchestrator enhancement (prompt engineering)

**Why it's NOT a Skill:**
- ❌ No tool invocation required (just file reads)
- ❌ No model invocation needed (happens BEFORE spawning Developer)
- ❌ Not reusable by model (it's orchestrator's job)
- ✅ Better as smart prompt assembly

**Implementation Approach:** Orchestrator logic

**How it works:**
```python
# In orchestrator, BEFORE spawning Developer

# Step 1: Extract keywords from task
task = "Implement password reset endpoint"
keywords = ["password", "reset", "endpoint", "email"]

# Step 2: Find similar files (simple grep)
similar_files = []
for keyword in keywords:
    files = grep_for_files(keyword)
    similar_files.extend(files)

# Limit to top 3
similar_files = similar_files[:3]

# Step 3: Read utilities
utils = ["utils/email.py", "utils/validators.py", "utils/responses.py"]

# Step 4: Build enhanced prompt
developer_prompt = base_developer_prompt + f"""

═══════════════════════════════════════════
CODEBASE CONTEXT
═══════════════════════════════════════════

## Similar Features

**File: user_registration.py**
```python
@app.route('/api/register', methods=['POST'])
def register():
    email = request.json.get('email')
    if not is_valid_email(email):
        return error_response('Invalid email')
    EmailService.send_welcome_email(email)
    return success_response()
```

## Available Utilities

- utils/email.py: EmailService class
- utils/validators.py: is_valid_email()
- utils/responses.py: error_response(), success_response()

═══════════════════════════════════════════

YOUR TASK: {task}

Use the patterns and utilities shown above.
"""

# Step 5: Spawn Developer with enhanced prompt
spawn_developer(developer_prompt)
```

**Why this approach:**
- ✅ Zero runtime cost (happens during spawn)
- ✅ No separate tool needed (just file reads)
- ✅ Orchestrator already has context
- ✅ Simpler than invoking a Skill
- ✅ Can combine with Codebase Analysis Skill for even better results

**Location:** `agents/orchestrator.md` - enhance Developer spawning logic

**Effort:** 3 hours (orchestrator enhancement)

---

### 2. Enforce Unit Test Execution ✅ TIER 1 - WORKFLOW ENFORCEMENT

**Type:** Workflow change (prompt requirements)

**Why it's NOT a Skill:**
- ❌ No tool invocation (just running `pytest` or `npm test`)
- ❌ No special logic needed (standard test commands)
- ❌ Not a capability, just proper process
- ✅ Better as mandatory workflow requirement

**Implementation Approach:** Developer prompt enhancement

**How it works:**
```markdown
# Add to agents/developer.md prompt

## ⚠️ MANDATORY: Test Execution Before Reporting

Before reporting "READY_FOR_QA", you MUST:

1. Run ALL unit tests:
   ```bash
   # Python
   pytest

   # JavaScript
   npm test

   # Go
   go test ./...

   # Java
   mvn test
   ```

2. Verify ALL tests PASS

3. If ANY test fails:
   - Analyze the failures
   - Fix the issues
   - Re-run tests
   - Repeat until ALL pass

4. ONLY when all tests pass, report: **Status: READY_FOR_QA**

5. If tests fail and you cannot fix, report: **Status: BLOCKED - Tests failing**

**Example output:**
```
Running unit tests...
pytest
======================== test session starts =========================
collected 47 items

tests/test_auth.py ✓✓✓✓✓✓✓✓✓✓✓ (11 passed)
tests/test_users.py ✓✓✓✓✓✓✓✓✓✓ (10 passed)
...

======================== 47 passed in 2.31s ==========================

All tests passing ✅

Status: READY_FOR_QA
```

**NEVER report READY_FOR_QA with failing tests.**
```

**Why this approach:**
- ✅ Simple workflow enforcement
- ✅ No new tool needed (uses existing test runners)
- ✅ Just proper engineering practice
- ✅ Orchestrator can verify (check for test results in Developer report)

**Location:** `agents/developer.md` - add mandatory requirement

**Effort:** 1 hour (prompt update + orchestrator verification)

---

### 3. Dependency Resolver ⚠️ TIER 3 - POTENTIALLY A SKILL (LOW PRIORITY)

**Type:** Could be a Skill, but low priority

**Why it could be a Skill:**
- ✅ Tool invocation (pip list, npm list, go mod verify)
- ✅ Structured output (missing dependencies)

**Why it's not worth it:**
- ❌ Low frequency issue (mostly using containers)
- ❌ Low ROI (3x vs 20x for pre-commit)
- ❌ Not a bottleneck in current workflow

**Recommendation:** Skip for now, revisit if becomes a problem

---

## Summary Matrix

| Capability | Type | Tier | Priority | Effort | ROI |
|-----------|------|------|----------|--------|-----|
| **Pre-Commit Validation** | ✅ Skill (reuse lint-check) | 1 | Critical | 0 hours (exists) | 20x |
| **Code Context Injection** | ❌ Orchestrator logic | 1 | High | 3 hours | 15x |
| **Enforce Unit Tests** | ❌ Workflow enforcement | 1 | Critical | 1 hour | 10x |
| **Codebase Analysis** | ✅ Skill (new) | 2 | Medium | 4-6 hours | 8x |
| **Test Pattern Analysis** | ✅ Skill (new) | 2 | Medium | 3-4 hours | 5x |

---

## Implementation Sequence

### Phase 1: This Week (No New Skills)

**1. Enforce Unit Test Execution** (1 hour)
- Update `agents/developer.md`
- Add mandatory requirement
- Update orchestrator to verify

**2. Code Context Injection** (3 hours)
- Enhance `agents/orchestrator.md`
- Add similar code finding logic
- Inject context before spawning Developer

**3. Enable Pre-Commit Validation** (0 hours)
- Update Developer workflow to use existing `lint-check` Skill
- Add to Developer prompt: "Before commit, run /lint-check"
- No new Skill needed!

**Total:** 4 hours, **15x ROI**, **0 new Skills**

### Phase 2: Next Sprint (New Skills)

**4. Codebase Analysis Skill** (4-6 hours)
- Create new Skill at `.claude/skills/codebase-analysis/`
- Implement analysis logic
- Test with various codebases

**5. Test Pattern Analysis Skill** (3-4 hours)
- Create new Skill at `.claude/skills/test-pattern-analysis/`
- Implement test framework detection
- Test with various projects

**Total:** 7-10 hours, **6x ROI**, **2 new Skills**

---

## Skills vs Non-Skills Decision Framework

**Use a Skill when:**
- ✅ Requires external tool invocation
- ✅ Returns structured output (JSON)
- ✅ Model-invoked (agent calls it)
- ✅ Reusable across instances
- ✅ Time-consuming (>5 seconds)
- ✅ Specialized logic

**Don't use a Skill when:**
- ❌ Just prompt engineering
- ❌ Simple file reads/writes
- ❌ Workflow enforcement
- ❌ Orchestrator logic
- ❌ One-time use

**Examples:**
- ✅ `security-scan` - Invokes bandit/semgrep, returns JSON → **Skill**
- ✅ `lint-check` - Invokes ruff/eslint, returns JSON → **Skill**
- ✅ `codebase-analysis` - Complex analysis, returns JSON → **Skill**
- ❌ Context injection - Just file reads + prompt → **Not a Skill**
- ❌ Test enforcement - Workflow rule → **Not a Skill**

---

## Final Recommendations

### Immediate (Phase 1):
1. ✅ Reuse `lint-check` Skill for pre-commit (0 hours)
2. ✅ Add code context injection to orchestrator (3 hours)
3. ✅ Enforce test execution in Developer prompt (1 hour)

**Result:** 40% reduction in revision cycles, 0 new Skills

### Soon (Phase 2):
4. ✅ Create `codebase-analysis` Skill (4-6 hours)
5. ✅ Create `test-pattern-analysis` Skill (3-4 hours)

**Result:** Additional 10% reduction in revision cycles, 2 new Skills

---

**Status:** Implementation guide ready
**Priority:** Critical for Phase 1, High for Phase 2
