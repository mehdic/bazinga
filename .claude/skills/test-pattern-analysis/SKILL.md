---
name: test-pattern-analysis
description: Analyze existing tests to identify patterns, fixtures, and conventions before writing new tests
allowed-tools: [Bash, Read, Write, Grep]
---

# Test Pattern Analysis Skill

You are the test-pattern-analysis skill. When invoked, you analyze existing test files to help developers follow established patterns, fixtures, and conventions.

## Your Task

When invoked, you will:
1. Detect the test framework being used
2. Find and analyze existing test files
3. Identify common fixtures and test utilities
4. Extract test naming conventions and patterns
5. Suggest test cases based on similar tests
6. Generate a structured report

---

## Step 1: Detect Test Framework

Use the **Read** tool to check for framework indicators:

**Python (pytest):**
- Check for: `pytest.ini`, `pyproject.toml` with `[tool.pytest]`, `conftest.py`
- If found: framework = "pytest"

**Python (unittest):**
- Check for files starting with `test_` importing `unittest`
- If found: framework = "unittest"

**JavaScript (Jest):**
- Check `package.json` for "jest" in devDependencies or scripts
- Check for: `jest.config.js`, `jest.config.json`
- If found: framework = "jest"

**Go:**
- Check for files ending in `_test.go`
- If found: framework = "testing"

**Java (JUnit):**
- Check for: `pom.xml` or `build.gradle` with junit dependencies
- If found: framework = "junit"

---

## Step 2: Find Test Files

Use the **Bash** tool to find test files:

**Python:**
```bash
find . -name "test_*.py" -o -name "*_test.py" | head -20
```

**JavaScript:**
```bash
find . -name "*.test.js" -o -name "*.test.ts" -o -name "*.spec.js" | head -20
```

**Go:**
```bash
find . -name "*_test.go" | head -20
```

**Java:**
```bash
find . -name "*Test.java" -o -name "*Tests.java" | head -20
```

---

## Step 3: Find Common Fixtures

### For pytest:

Use the **Read** tool to read `conftest.py` files (if they exist).

Look for `@pytest.fixture` decorators:
```python
@pytest.fixture
def test_client():
    # fixture code
```

Extract:
- Fixture name
- Scope (function, class, module, session)
- Docstring (if present)

### For Jest:

Use the **Grep** tool to search for `beforeEach`, `beforeAll`, `afterEach`, `afterAll`:
```bash
grep -r "beforeEach\|beforeAll" tests/ --include="*.test.js" --include="*.test.ts"
```

Extract common setup patterns.

### For Go:

Look for setup/teardown functions in test files:
```go
func TestMain(m *testing.M) {
    // setup
}
```

### For Java:

Use **Grep** to find `@Before`, `@BeforeEach`, `@BeforeAll` annotations:
```bash
grep -r "@Before\|@BeforeEach\|@BeforeAll" src/test/java/
```

---

## Step 4: Analyze Test Structure Patterns

Use the **Read** tool to read 3-5 representative test files.

Identify patterns:

**AAA (Arrange-Act-Assert):**
Look for three distinct sections in tests:
```python
def test_example():
    # Arrange
    user = create_user()

    # Act
    result = user.login()

    # Assert
    assert result.success
```

**Given-When-Then:**
Look for comments or structure like:
```javascript
test('user login', () => {
    // Given
    const user = createUser();

    // When
    const result = user.login();

    // Then
    expect(result).toBeSuccess();
});
```

---

## Step 5: Extract Naming Conventions

Analyze test function names to find patterns:

Use **Grep** to get all test function names:
```bash
# Python
grep -h "def test_" tests/**/*.py | head -20

# JavaScript
grep -h "test(\|it(" tests/**/*.test.js | head -20

# Go
grep -h "func Test" **/*_test.go | head -20
```

Identify naming patterns:
- `test_<function>_<scenario>_<expected>` (Python)
- `test_<feature>_<condition>` (Python)
- `should_<expected>_when_<scenario>` (JavaScript)
- `Test<Function><Scenario>` (Go, Java)

---

## Step 6: Find Test Utilities

Use the **Grep** tool to find helper functions:

**Assertion helpers:**
```bash
grep -r "def assert_\|def expect_" tests/ --include="*.py"
grep -r "function assert\|const assert" tests/ --include="*.js"
```

**Mock builders:**
```bash
grep -r "def create_mock\|def mock_" tests/ --include="*.py"
grep -r "function createMock\|function mock" tests/ --include="*.js"
```

**Test data factories:**
```bash
grep -r "def create_test_\|def build_" tests/ --include="*.py"
grep -r "function createTest\|function build" tests/ --include="*.js"
```

---

## Step 7: Find Similar Tests

If the invoking agent provided a task description (e.g., "write tests for password reset"), search for similar tests:

Use **Grep** to search for related keywords:
```bash
grep -r "password\|reset\|email" tests/ --include="test_*.py" -l
```

Use the **Read** tool to read the most relevant test files found.

Extract:
- Test structure and patterns used
- Edge cases covered
- Common assertions

---

## Step 8: Determine Coverage Target

Look for coverage configuration:

**pytest:**
Use **Read** tool to check `pytest.ini` or `pyproject.toml` for:
```ini
[tool:pytest]
addopts = --cov-fail-under=80
```

**jest:**
Use **Read** tool to check `jest.config.js` for:
```javascript
coverageThreshold: {
  global: {
    lines: 80
  }
}
```

If not found, assume default: 80%

---

## Step 9: Generate Test Suggestions

Based on similar tests found, suggest test cases:

**For a feature like "password reset":**
- Happy path: `test_password_reset_valid_email_sends_token`
- Error cases: `test_password_reset_invalid_email_returns_error`
- Edge cases: `test_password_reset_expired_token_returns_error`
- Security: `test_password_reset_rate_limiting_prevents_abuse`

---

## Step 10: Write Structured Report

Use the **Write** tool to create `coordination/test_patterns.json`:

```json
{
  "framework": "<detected framework>",
  "test_directory": "<main test directory>",
  "common_fixtures": [
    {
      "name": "<fixture_name>",
      "file": "<file_path>",
      "scope": "<scope>",
      "usage": "<description>"
    }
  ],
  "test_patterns": {
    "structure": "AAA|Given-When-Then|Four-Phase",
    "naming": "<extracted pattern>",
    "example": "<example test name>"
  },
  "similar_tests": [
    {
      "file": "<file_path>",
      "test_name": "<name>",
      "pattern": "<pattern used>",
      "edge_cases": ["<case1>", "<case2>"]
    }
  ],
  "suggested_tests": [
    "<suggested test name 1>",
    "<suggested test name 2>",
    "<suggested test name 3>"
  ],
  "coverage_target": "<percentage>",
  "utilities": [
    {"name": "<utility_name>", "file": "<file_path>"}
  ]
}
```

---

## Step 11: Return Summary

Return a concise summary to the calling agent:

```
Test Pattern Analysis:
- Framework: <framework>
- Pattern: <AAA|Given-When-Then>
- Naming convention: <pattern>
- Common fixtures: <fixture1>, <fixture2>
- Coverage target: X%

Suggested test cases:
1. <test case 1>
2. <test case 2>
3. <test case 3>

Similar tests to reference:
- <file1>: <test_name>
- <file2>: <test_name>

Details saved to: coordination/test_patterns.json
```

---

## Error Handling

**If no test files found:**
- Return: "No existing tests found. Cannot extract patterns. Developer should create tests from scratch."

**If no fixtures found:**
- Return: "No common fixtures found. Developer may need to create setup functions."

**If framework detection fails:**
- Try to infer from file patterns
- If still unclear, return: "Could not detect test framework. Please specify framework."

**If no similar tests found:**
- Return: "No similar tests found. Suggest generic test patterns (happy path, error cases, edge cases)."

---

## Notes

- Focus on extracting **reusable patterns** that save developer time
- Prioritize **fixtures** and **utilities** that can be reused
- Suggest **comprehensive test cases** including edge cases and error paths
- Ensure naming conventions are followed for consistency
