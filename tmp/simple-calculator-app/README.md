# Simple Calculator Module

A lightweight Python calculator module with core arithmetic operations, memory functions, and operation history tracking.

## Features

- **Basic Operations**: Addition, subtraction, multiplication, and division
- **Memory Functions**: Store, recall, and clear values in memory
- **Operation History**: Track the last 10 operations performed
- **Error Handling**: Type validation and comprehensive error messages
- **Comprehensive Tests**: Full test coverage with pytest

## Installation

Simply import the `Calculator` class from the `calculator.py` module:

```python
from calculator import Calculator

calc = Calculator()
```

## Usage

### Basic Arithmetic Operations

```python
from calculator import Calculator

calc = Calculator()

# Addition
result = calc.add(10, 5)          # Returns: 15

# Subtraction
result = calc.subtract(10, 3)     # Returns: 7

# Multiplication
result = calc.multiply(4, 5)      # Returns: 20

# Division
result = calc.divide(10, 2)       # Returns: 5.0

# Division by zero raises ValueError
try:
    result = calc.divide(10, 0)
except ValueError as e:
    print(f"Error: {e}")           # Error: Cannot divide by zero
```

### Memory Functions

Store and retrieve values in the calculator's memory:

```python
from calculator import Calculator

calc = Calculator()

# Store a value in memory
calc.memory_store(42)

# Recall the stored value
value = calc.memory_recall()      # Returns: 42

# Clear memory
calc.memory_clear()
value = calc.memory_recall()      # Returns: None
```

### Operation History

Track the last 10 operations performed:

```python
from calculator import Calculator

calc = Calculator()

calc.add(2, 3)
calc.subtract(10, 4)
calc.multiply(5, 6)

# Get history of operations
history = calc.get_history()

# Each entry contains (operation_name, operands, result)
for operation_name, operands, result in history:
    print(f"{operation_name}: {operands} = {result}")
# Output:
# add: (2, 3) = 5
# subtract: (10, 4) = 6
# multiply: (5, 6) = 30

# Clear history
calc.clear_history()
```

## Error Handling

The calculator includes comprehensive error handling:

### TypeError: Non-Numeric Input

All operations validate that inputs are numeric (int or float):

```python
from calculator import Calculator

calc = Calculator()

try:
    calc.add("5", 3)
except TypeError as e:
    print(f"Error: {e}")  # Error: Operand must be a number

try:
    calc.memory_store("not a number")
except TypeError as e:
    print(f"Error: {e}")  # Error: Operand must be a number
```

### ValueError: Division by Zero

Division by zero raises a ValueError:

```python
from calculator import Calculator

calc = Calculator()

try:
    result = calc.divide(10, 0)
except ValueError as e:
    print(f"Error: {e}")  # Error: Cannot divide by zero
```

## API Reference

### Calculator Class

#### Methods

##### `add(a, b)`
- **Description**: Add two numbers
- **Parameters**: `a` (int|float), `b` (int|float)
- **Returns**: Sum of a and b
- **Raises**: `TypeError` if operands are not numeric

##### `subtract(a, b)`
- **Description**: Subtract b from a
- **Parameters**: `a` (int|float), `b` (int|float)
- **Returns**: Difference of a and b
- **Raises**: `TypeError` if operands are not numeric

##### `multiply(a, b)`
- **Description**: Multiply two numbers
- **Parameters**: `a` (int|float), `b` (int|float)
- **Returns**: Product of a and b
- **Raises**: `TypeError` if operands are not numeric

##### `divide(a, b)`
- **Description**: Divide a by b
- **Parameters**: `a` (int|float), `b` (int|float)
- **Returns**: Result of a divided by b
- **Raises**:
  - `TypeError` if operands are not numeric
  - `ValueError` if b is zero

##### `memory_store(value)`
- **Description**: Store a value in memory
- **Parameters**: `value` (int|float)
- **Returns**: None
- **Raises**: `TypeError` if value is not numeric

##### `memory_recall()`
- **Description**: Recall the value stored in memory
- **Parameters**: None
- **Returns**: Stored value or None if nothing has been stored

##### `memory_clear()`
- **Description**: Clear the memory
- **Parameters**: None
- **Returns**: None

##### `get_history()`
- **Description**: Get the operation history
- **Parameters**: None
- **Returns**: List of tuples containing (operation_name, operands, result)

##### `clear_history()`
- **Description**: Clear the operation history
- **Parameters**: None
- **Returns**: None

## Running Tests

To run the comprehensive unit tests, use pytest:

```bash
# Run all tests
pytest test_calculator.py

# Run with verbose output
pytest test_calculator.py -v

# Run tests with coverage report
pytest test_calculator.py --cov=calculator

# Run specific test class
pytest test_calculator.py::TestBasicOperations

# Run specific test function
pytest test_calculator.py::TestMemoryFunctions::test_memory_store_integer
```

## Test Coverage

The test suite includes 60+ test cases covering:

- **Basic Operations** (20 tests): All arithmetic operations with various number types
- **Error Handling** (7 tests): Type validation and error conditions
- **Memory Functions** (9 tests): Storage, recall, and clearing
- **History Tracking** (11 tests): Recording and managing operation history
- **Calculator State** (2 tests): Instance independence and clean state
- **Edge Cases** (5 tests): Very large/small numbers, floating-point precision

## Examples

### Complete Calculator Session

```python
from calculator import Calculator

# Create a calculator instance
calc = Calculator()

# Perform some calculations
print(calc.add(10, 5))           # 15
print(calc.subtract(20, 8))      # 12
print(calc.multiply(4, 7))       # 28
print(calc.divide(100, 4))       # 25.0

# Use memory
calc.memory_store(100)
print(calc.memory_recall())      # 100

# Check history
history = calc.get_history()
print(f"Total operations: {len(history)}")  # 4

# View last operation
last_op = history[-1]
print(f"Last operation: {last_op[0]}")  # divide
```

### Using Multiple Instances

```python
from calculator import Calculator

# Each instance has independent state
calc1 = Calculator()
calc2 = Calculator()

calc1.memory_store(42)
calc2.memory_store(100)

print(calc1.memory_recall())  # 42
print(calc2.memory_recall())  # 100
```

## Implementation Details

### History Tracking

- Operations are stored in a `deque` with a maximum length of 10
- When more than 10 operations are recorded, the oldest operation is automatically removed
- History includes the operation name, operands, and result
- History is not affected by operations that raise errors (failed operations are not recorded)

### Memory

- Memory starts as `None`
- Can store any numeric value (int or float)
- Values are preserved across calculations
- Memory is independent from history

### Type Validation

- All numeric inputs are validated before operations
- Boolean values are explicitly rejected (they are technically int subclass in Python)
- Type errors provide clear messages indicating what type was received

## Requirements

- Python 3.6+
- pytest (for running tests)

## License

This calculator module is provided as-is for educational and practical purposes.
