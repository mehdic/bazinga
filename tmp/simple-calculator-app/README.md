# Calculator Module

A Python calculator module with basic arithmetic operations, memory management, and operation history tracking.

## Features

### Basic Operations
- **Addition**: Add two numbers
- **Subtraction**: Subtract one number from another
- **Multiplication**: Multiply two numbers
- **Division**: Divide one number by another (with zero-division protection)

### Memory Functions
- **Store**: Save a value to memory
- **Recall**: Retrieve the stored value
- **Clear**: Clear the memory

### History Tracking
- Automatically tracks the last 10 operations performed
- First-in-first-out (FIFO) behavior when limit is reached

### Error Handling
- **Division by Zero**: Raises `ValueError` with clear error message
- **Invalid Inputs**: Raises `TypeError` for non-numeric inputs

## Installation

No installation required. Simply ensure you have Python 3.10+ installed.

## Usage

### Basic Example

```python
from calculator import Calculator

# Create a calculator instance
calc = Calculator()

# Perform basic operations
result = calc.add(10, 5)        # 15
result = calc.subtract(20, 8)   # 12
result = calc.multiply(4, 7)    # 28
result = calc.divide(100, 4)    # 25.0
```

### Memory Functions

```python
calc = Calculator()

# Perform a calculation
result = calc.add(15, 10)  # 25

# Store the result in memory
calc.memory_store(result)

# Recall the stored value
stored = calc.memory_recall()  # 25

# Clear memory
calc.memory_clear()
recalled = calc.memory_recall()  # None
```

### History Tracking

```python
calc = Calculator()

# Perform operations
calc.add(5, 3)
calc.multiply(4, 2)
calc.subtract(10, 7)

# Get operation history
history = calc.get_history()
# [('add', 5, 3, 8), ('multiply', 4, 2, 8), ('subtract', 10, 7, 3)]

# Clear history
calc.clear_history()
```

### Error Handling

```python
calc = Calculator()

# Division by zero
try:
    calc.divide(10, 0)
except ValueError as e:
    print(f"Error: {e}")  # Error: Cannot divide by zero

# Invalid input type
try:
    calc.add("10", 5)
except TypeError as e:
    print(f"Error: {e}")  # Error: Parameter 'a' must be numeric...
```

## Running Tests

The module includes comprehensive unit tests using pytest.

```bash
# Install pytest if needed
pip install pytest

# Run all tests
pytest test_calculator.py

# Run with verbose output
pytest -v test_calculator.py

# Run with coverage report
pip install pytest-cov
pytest --cov=calculator test_calculator.py
```

## API Reference

### Calculator Class

#### `__init__()`
Initialize a new calculator with empty memory and history.

#### `add(a: float, b: float) -> float`
Add two numbers.
- **Parameters**: `a`, `b` - Numbers to add
- **Returns**: Sum of a and b
- **Raises**: `TypeError` if inputs are not numeric

#### `subtract(a: float, b: float) -> float`
Subtract b from a.
- **Parameters**: `a` - Number to subtract from, `b` - Number to subtract
- **Returns**: Difference of a and b
- **Raises**: `TypeError` if inputs are not numeric

#### `multiply(a: float, b: float) -> float`
Multiply two numbers.
- **Parameters**: `a`, `b` - Numbers to multiply
- **Returns**: Product of a and b
- **Raises**: `TypeError` if inputs are not numeric

#### `divide(a: float, b: float) -> float`
Divide a by b.
- **Parameters**: `a` - Dividend, `b` - Divisor
- **Returns**: Quotient of a and b
- **Raises**:
  - `TypeError` if inputs are not numeric
  - `ValueError` if b is zero

#### `memory_store(value: float) -> None`
Store a value in memory.
- **Parameters**: `value` - Value to store
- **Raises**: `TypeError` if value is not numeric

#### `memory_recall() -> float | None`
Recall the value stored in memory.
- **Returns**: The stored value, or `None` if memory is empty

#### `memory_clear() -> None`
Clear the memory.

#### `get_history() -> List[Tuple[str, float, float, float]]`
Get the operation history.
- **Returns**: List of tuples `(operation, operand1, operand2, result)` containing the last 10 operations

#### `clear_history() -> None`
Clear the operation history.

## Design Decisions

- **Class-based design**: Encapsulates state (memory and history) within the Calculator instance
- **Type hints**: Full type annotations for better IDE support and code clarity
- **Deque for history**: Uses `collections.deque` with `maxlen=10` for efficient FIFO behavior
- **Validation**: Centralized input validation in `_validate_numeric()` method
- **Boolean exclusion**: Booleans are explicitly excluded from numeric validation (common Python gotcha)

## License

MIT License
