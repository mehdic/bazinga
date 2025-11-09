# BAZINGA CLI Test Suite

Comprehensive tests for security, state management, and CLI functionality.

## Running Tests

### Install Test Dependencies

```bash
# Using pip
pip install -e ".[dev]"

# Using uv
uv pip install -e ".[dev]"
```

### Run All Tests

```bash
pytest
```

### Run Specific Test Files

```bash
# Security tests only
pytest tests/test_security.py

# State management tests only
pytest tests/test_state_manager.py

# CLI tests only
pytest tests/test_cli.py
```

### Run with Coverage

```bash
pytest --cov=src/bazinga_cli --cov-report=html
```

Then open `htmlcov/index.html` in a browser.

### Run Specific Test Classes or Functions

```bash
# Run a specific test class
pytest tests/test_security.py::TestPathValidator

# Run a specific test function
pytest tests/test_security.py::TestPathValidator::test_validate_project_name_path_traversal
```

## Test Categories

### Security Tests (`test_security.py`)

Tests security utilities including:
- Path validation and sanitization
- Filename validation
- Path traversal prevention
- Safe subprocess execution
- Command whitelisting
- Input validation

**Key test cases:**
- Path traversal attempts (../, ../../, etc.)
- Absolute path injection (/etc/passwd, C:\Windows)
- Null byte injection
- Command injection attempts
- Reserved Windows filenames
- Invalid characters in names

### State Management Tests (`test_state_manager.py`)

Tests thread-safe state management with file locking:
- Atomic read-modify-write operations
- Race condition prevention
- Concurrent access from multiple threads
- Revision count management
- State persistence

**Key test cases:**
- Concurrent writes don't corrupt state
- File locking prevents race conditions
- Revision counts increment atomically
- Corrupted JSON recovery

### CLI Tests (`test_cli.py`)

Tests command-line interface:
- Version command
- Check command
- Init command with validation
- Security integration tests

**Key test cases:**
- Project name validation
- Directory creation
- Malicious input rejection
- Existing directory handling

## Writing New Tests

### Test Structure

```python
class TestFeatureName:
    """Test description."""

    def test_specific_behavior(self):
        """Test that specific behavior works."""
        # Arrange
        setup_data = ...

        # Act
        result = function_under_test(setup_data)

        # Assert
        assert result == expected_value
```

### Using Fixtures

Tests use pytest fixtures like `tmp_path` for temporary directories:

```python
def test_file_operations(tmp_path):
    """Test file operations in isolated directory."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    assert test_file.read_text() == "content"
```

### Testing Exceptions

```python
def test_invalid_input_raises_error():
    """Test that invalid input raises appropriate error."""
    with pytest.raises(SecurityError, match="error message"):
        validate_input("invalid")
```

### Testing Concurrent Operations

```python
def test_thread_safety(tmp_path):
    """Test that operations are thread-safe."""
    def worker():
        # perform operations
        pass

    threads = [threading.Thread(target=worker) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Verify final state is correct
```

## Coverage Goals

Target coverage: **70%+**

Current coverage by module:
- `security.py`: Aim for 95%+ (critical security code)
- `state_manager.py`: Aim for 90%+ (critical concurrency code)
- `__init__.py` (CLI): Aim for 60%+ (harder to test, lots of I/O)

## Continuous Integration

Tests should be run on:
- Every commit
- Every pull request
- Before release

Add to your CI pipeline:

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -e ".[dev]"
      - run: pytest --cov=src/bazinga_cli
```

## Troubleshooting

### Tests fail with import errors

Ensure you've installed the package in development mode:
```bash
pip install -e ".[dev]"
```

### Tests hang

Check for:
- Infinite loops in code
- Deadlocks in concurrent tests
- Missing timeouts in subprocess calls

Use pytest timeout:
```bash
pytest --timeout=10  # Fail any test taking >10 seconds
```

### Coverage not generated

Ensure pytest-cov is installed:
```bash
pip install pytest-cov
```

Run with coverage explicitly:
```bash
pytest --cov=src/bazinga_cli
```
