# Test Pattern Analysis Skill

**Type:** Model-invoked test analysis tool
**Purpose:** Analyze existing tests to identify patterns, fixtures, and conventions
**Complexity:** Medium (5-15 seconds runtime)

## What This Skill Does

Before writing tests, this Skill analyzes existing test files to help developers:

1. **Identify Test Framework**: Detect pytest, jest, go test, JUnit, etc.
2. **Find Common Fixtures**: Extract reusable fixtures and their usage
3. **Understand Test Patterns**: Detect AAA, Given-When-Then, etc.
4. **Learn Naming Conventions**: Extract test naming patterns
5. **Discover Test Utilities**: Find helper functions for testing
6. **Suggest Test Cases**: Recommend test scenarios based on similar tests

## Usage

```bash
/test-pattern-analysis tests/
```

Or for specific test file:

```bash
/test-pattern-analysis tests/test_auth.py
```

## Output

**File:** `coordination/test_patterns.json`

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

## How It Works

### Step 1: Detect Test Framework

Scan for test framework indicators:
- **pytest**: `pytest.ini`, `conftest.py`, `@pytest.fixture`
- **jest**: `jest.config.js`, `*.test.js`, `describe()`
- **go test**: `*_test.go`, `func Test*(t *testing.T)`
- **JUnit**: `@Test`, `@Before`, `junit` in pom.xml

### Step 2: Find Common Fixtures

For pytest:
- Parse `conftest.py` for `@pytest.fixture`
- Extract fixture names, scopes, and docstrings

For jest:
- Find `beforeEach()`, `beforeAll()` setups
- Extract mock objects and test data

For go:
- Find setup/teardown functions
- Extract test helpers

### Step 3: Analyze Test Structure

Identify patterns:
- **AAA (Arrange-Act-Assert)**: Setup, execute, verify
- **Given-When-Then**: BDD style
- **Four-Phase Test**: Setup, exercise, verify, teardown

Detect by analyzing comment patterns and code structure.

### Step 4: Extract Naming Conventions

Analyze test names to find patterns:
- `test_<function>_<scenario>_<expected>`
- `test_<feature>_<condition>`
- `should_<expected>_when_<scenario>`

### Step 5: Find Similar Tests

Search for tests similar to current task:
- Match keywords from task to test names
- Find tests for similar features
- Extract edge cases and scenarios

### Step 6: Find Test Utilities

Scan for helper functions:
- Assertion helpers: `assert_*`, `expect_*`
- Mock builders: `create_mock_*`, `mock_*`
- Test data factories: `create_test_*`, `build_*`

### Step 7: Generate Test Suggestions

Based on analysis, suggest test cases:
- Happy path test
- Error condition tests
- Edge case tests
- Boundary tests

## Implementation

The Skill is implemented in Python and runs as an external tool invoked by the model.

**Files:**
- `analyze_tests.py`: Main test analysis orchestrator
- `frameworks.py`: Test framework detection
- `patterns.py`: Pattern extraction and analysis

**Runtime:** 5-15 seconds depending on test suite size

**Languages Supported:** Python (pytest), JavaScript (jest), Go (testing), Java (JUnit)

## When to Use

✅ **Use this Skill when:**
- Writing tests for a new feature
- Unfamiliar with project's test conventions
- Want to follow existing test patterns
- Need to match existing test coverage standards

❌ **Don't use when:**
- No existing tests in project
- Task is trivial (e.g., single unit test)
- Already familiar with test patterns
- Time is critical and tests are simple

## Example Workflow

```bash
# Developer implements feature
# Developer ready to write tests

# Developer invokes Skill
/test-pattern-analysis tests/

# Skill analyzes existing tests (5-15 seconds)
# Writes results to coordination/test_patterns.json

# Developer reads patterns
cat coordination/test_patterns.json

# Developer sees:
# - Framework: pytest
# - Fixtures: test_client, mock_db
# - Pattern: AAA (Arrange-Act-Assert)
# - Naming: test_<function>_<scenario>_<expected>
# - Suggested tests: list of test cases

# Developer writes tests following patterns
# Uses existing fixtures
# Follows naming convention
# Implements suggested test cases
# Tests pass review first time
```

## Benefits

**Without Skill:**
- Developer guesses at test patterns → inconsistent tests
- Misses common fixtures → duplicates setup code
- Wrong naming convention → gets changes requested
- Misses edge cases → insufficient coverage
- **Total:** 30-45 minutes + revision cycle

**With Skill:**
- Skill provides patterns → consistent tests
- Uses existing fixtures → clean tests
- Follows naming convention → passes review
- Suggests edge cases → complete coverage
- **Total:** 20-30 minutes, no revisions

**ROI:** 5x (30% time savings, 80% fewer revisions)

## Technical Details

**Dependencies:**
- Python 3.8+
- Standard library (ast, re, json, pathlib)
- No external dependencies

**Performance:**
- Small test suite (<50 tests): 5 seconds
- Medium test suite (50-200 tests): 8-12 seconds
- Large test suite (200+ tests): 12-20 seconds

**Limitations:**
- Text-based analysis (doesn't execute tests)
- Best for projects with existing test suite
- May miss implicit patterns

## Integration

This Skill is automatically available in:
- **Superpowers Mode**: Developer must invoke before writing tests
- **Standard Mode**: Not available (time-sensitive)

Orchestrator injects this Skill into Developer prompt when superpowers mode is active.

## Coverage Integration

The Skill also checks for coverage requirements:
- pytest: `pytest.ini` `--cov-fail-under`
- jest: `jest.config.js` `coverageThreshold`
- go: Coverage comments in tests
- JUnit: JaCoCo configuration

Reports coverage target so developer knows the standard to meet.
