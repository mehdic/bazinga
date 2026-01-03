# Simple Calculator App

A Python calculator module with basic arithmetic operations, memory functions, and operation history tracking.

## Features

- **Basic Operations**: Addition, subtraction, multiplication, and division
- **Memory Functions**: Store, recall, and clear values in memory
- **History Tracking**: Automatically tracks the last 10 operations
- **Error Handling**: Proper validation and error messages for invalid inputs
- **Type Safety**: Full type hints for better code quality

## Installation

No external dependencies required. Simply ensure you have Python 3.10+ installed.

```bash
# Clone or copy the calculator.py file to your project
# No pip install needed - uses only Python standard library
```

## Usage

### Basic Operations

```python
from calculator import Calculator

# Create a calculator instance
calc = Calculator()

# Addition
result = calc.add(10, 5)  # Returns 15

# Subtraction
result = calc.subtract(10, 3)  # Returns 7

# Multiplication
result = calc.multiply(4, 5)  # Returns 20

# Division
result = calc.divide(20, 4)  # Returns 5.0
```

### Memory Functions

```python
calc = Calculator()

# Store a value in memory
calc.memory_store(42)

# Recall the stored value
value = calc.memory_recall()  # Returns 42

# Clear memory
calc.memory_clear()
value = calc.memory_recall()  # Returns None
```

### History Tracking

```python
calc = Calculator()

# Perform some operations
calc.add(5, 3)
calc.multiply(10, 2)
calc.divide(20, 4)

# Get operation history
history = calc.get_history()
# Returns: [
#   ('add', (5, 3), 8),
#   ('multiply', (10, 2), 20),
#   ('divide', (20, 4), 5.0)
# ]

# Clear history
calc.clear_history()
```

### Error Handling

The calculator properly handles errors:

```python
calc = Calculator()

# Division by zero raises ValueError
try:
    calc.divide(10, 0)
except ValueError as e:
    print(e)  # "Division by zero is not allowed"

# Invalid input types raise TypeError
try:
    calc.add("5", 3)
except TypeError as e:
    print(e)  # "Invalid input type: expected int or float, got str"
```

## API Reference

### Calculator Class

#### Methods

**Basic Operations:**

- `add(a: float, b: float) -> float`: Add two numbers
- `subtract(a: float, b: float) -> float`: Subtract b from a
- `multiply(a: float, b: float) -> float`: Multiply two numbers
- `divide(a: float, b: float) -> float`: Divide a by b

**Memory Functions:**

- `memory_store(value: float) -> None`: Store a value in memory
- `memory_recall() -> float | None`: Recall stored value (None if empty)
- `memory_clear() -> None`: Clear memory

**History Functions:**

- `get_history() -> List[Tuple[str, Tuple[float, ...], float]]`: Get last 10 operations
- `clear_history() -> None`: Clear operation history

### Error Handling

**ValueError:**
- Raised when dividing by zero

**TypeError:**
- Raised when inputs are not numeric (int or float)

## Running Tests

The project includes comprehensive pytest tests covering all functionality:

```bash
# Install pytest if not already installed
pip install pytest

# Run all tests
pytest test_calculator.py

# Run with verbose output
pytest test_calculator.py -v

# Run with coverage
pip install pytest-cov
pytest test_calculator.py --cov=calculator --cov-report=term-missing
```

### Test Coverage

The test suite includes:
- 40+ test cases
- All basic operations (positive, negative, zero)
- All memory functions
- History tracking and FIFO behavior
- Error handling (TypeError, ValueError)
- Edge cases (floats, large numbers, mixed types)
- State isolation between instances

## Examples

### Simple Calculator Session

```python
from calculator import Calculator

calc = Calculator()

# Calculate: (10 + 5) * 2 / 3
step1 = calc.add(10, 5)      # 15
calc.memory_store(step1)     # Store 15
step2 = calc.multiply(step1, 2)  # 30
result = calc.divide(step2, 3)   # 10.0

print(f"Result: {result}")   # Result: 10.0
print(f"Memory: {calc.memory_recall()}")  # Memory: 15

# View calculation history
for operation, operands, result in calc.get_history():
    print(f"{operation}{operands} = {result}")
# Output:
# add(10, 5) = 15
# multiply(15, 2) = 30
# divide(30, 3) = 10.0
```

### History Management

```python
calc = Calculator()

# Perform more than 10 operations
for i in range(15):
    calc.add(i, 1)

# History keeps only last 10
history = calc.get_history()
print(f"History length: {len(history)}")  # 10

# Oldest operations are dropped (FIFO)
print(history[0])   # ('add', (5, 1), 6) - operation 6
print(history[-1])  # ('add', (14, 1), 15) - operation 15
```

## Technical Details

### History Tracking

- History stores tuples of `(operation_name, operands, result)`
- Maximum 10 operations maintained using FIFO (First In, First Out)
- Older operations automatically removed when limit exceeded
- `get_history()` returns a copy to prevent external modification

### Type System

- All methods use type hints for clarity
- Accepts both `int` and `float` inputs
- Returns `float` for most operations (Python division always returns float)
- Memory can store any numeric value or `None` (empty state)

### Design Principles

- **EAFP (Easier to Ask Forgiveness than Permission)**: Uses try/except for validation
- **Single Responsibility**: Each method has one clear purpose
- **Encapsulation**: Internal state (`_memory`, `_history`) is protected
- **Immutability**: History returned as copy, not reference

## License

This is a sample project for demonstration purposes.

## Author

Created as part of the BAZINGA development framework.
