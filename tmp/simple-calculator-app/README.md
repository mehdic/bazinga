# Simple Calculator App

A Python calculator module with core arithmetic operations, memory management, and operation history tracking.

## Features

- **Core Operations**: Add, subtract, multiply, divide
- **Memory Functions**: Store, recall, and clear values
- **History Tracking**: Automatically tracks the last 10 operations
- **Error Handling**: Comprehensive error handling with descriptive messages
- **Type Safety**: Full type hints for all public APIs

## Installation

No external dependencies required beyond Python 3.7+.

```bash
cd simple-calculator-app
```

## Usage

```python
from calculator import Calculator

# Create a calculator instance
calc = Calculator()

# Basic operations
calc.add(10, 5)        # 15
calc.subtract(20, 3)   # 17
calc.multiply(4, 5)    # 20
calc.divide(100, 4)    # 25.0

# Memory operations
calc.memory_store(42)
value = calc.memory_recall()  # 42
calc.memory_clear()

# View operation history
history = calc.get_history()  # List of last 10 operations
calc.clear_history()
```

## API Reference

### Core Operations

- `add(a, b)` - Returns the sum of a and b
- `subtract(a, b)` - Returns a minus b
- `multiply(a, b)` - Returns a multiplied by b
- `divide(a, b)` - Returns a divided by b (raises ValueError if b is 0)

### Memory Functions

- `memory_store(value)` - Stores a numeric value in memory
- `memory_recall()` - Returns the stored value (or None if empty)
- `memory_clear()` - Clears the memory

### History Functions

- `get_history()` - Returns a list of the last 10 operations
- `clear_history()` - Clears all operation history

## Error Handling

- **ValueError**: Raised when dividing by zero
- **TypeError**: Raised when operands are not numeric types or invalid values are passed to memory_store

## Testing

Run the comprehensive test suite with pytest:

```bash
pytest test_calculator.py -v
```

The test suite includes 70+ tests covering:
- All core operations
- Edge cases and boundary conditions
- Type error handling
- Memory functions
- History tracking
- Integration scenarios

## Design Patterns

- **EAFP (Easier to Ask for Forgiveness than Permission)**: Uses try/except for type validation
- **Type Hints**: All public APIs include type hints
- **Collections.deque**: Fixed-size history using deque with maxlen=10
- **Immutable API**: Memory and history operations are clean and side-effect aware
