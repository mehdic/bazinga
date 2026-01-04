# Simple Calculator Module

A Python calculator module providing basic arithmetic operations, memory functions, and operation history tracking.

## Features

### Basic Operations
- **add(a, b)** - Returns the sum of two numbers
- **subtract(a, b)** - Returns the difference of two numbers
- **multiply(a, b)** - Returns the product of two numbers
- **divide(a, b)** - Returns the quotient of two numbers (handles division by zero)

### Memory Functions
- **memory_store(value)** - Store a value in memory
- **memory_recall()** - Recall the stored value (returns None if no value stored)
- **memory_clear()** - Clear the stored memory value

### History Tracking
- **get_history()** - Returns the last 10 operations performed
- Operations are automatically tracked in chronological order
- History automatically rotates when more than 10 operations are performed

## Installation

No external dependencies required. Python 3.11+ recommended.

```bash
# For running tests
pip install pytest
```

## Usage

```python
from calculator import Calculator

# Create calculator instance
calc = Calculator()

# Basic operations
result = calc.add(5, 3)        # Returns 8
result = calc.subtract(10, 4)  # Returns 6
result = calc.multiply(3, 7)   # Returns 21
result = calc.divide(20, 4)    # Returns 5.0

# Memory functions
calc.memory_store(42)
value = calc.memory_recall()   # Returns 42
calc.memory_clear()
value = calc.memory_recall()   # Returns None

# View operation history
history = calc.get_history()
# Returns: ['add(5, 3) = 8', 'subtract(10, 4) = 6', ...]
```

## Error Handling

### Division by Zero
```python
calc.divide(10, 0)  # Raises ValueError: "Cannot divide by zero"
```

### Invalid Input Types
```python
calc.add("5", 3)    # Raises TypeError: "Invalid input type: str. Expected int or float."
```

## Running Tests

```bash
# Run all tests
pytest test_calculator.py

# Run with verbose output
pytest test_calculator.py -v

# Run with coverage
pytest test_calculator.py --cov=calculator
```

## Test Coverage

The test suite includes:
- ✓ All basic operations (positive/negative numbers, decimals, zero)
- ✓ Division by zero error handling
- ✓ Type validation for all operations
- ✓ Memory storage, recall, and clear functions
- ✓ History tracking (max 10 operations)
- ✓ Edge cases (large numbers, small decimals, boundary conditions)

## Design Notes

- Uses Python type hints for all public APIs
- Follows EAFP (Easier to Ask Forgiveness than Permission) principle
- History implemented with `collections.deque` for efficient rotation
- Immutable design - operations don't modify input values
- Comprehensive input validation with clear error messages

## License

This is a demonstration module created for testing purposes.
