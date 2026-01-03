"""
Simple Calculator Module

Provides basic arithmetic operations, memory functions, and history tracking.
"""
from typing import Any, List, Tuple


class Calculator:
    """A simple calculator with memory and history tracking capabilities.

    Features:
    - Basic arithmetic operations (add, subtract, multiply, divide)
    - Memory storage (store, recall, clear)
    - Operation history (last 10 operations)

    Attributes:
        _memory: Stored value in memory (None if empty)
        _history: List of last 10 operations as tuples (operation, operands, result)
    """

    def __init__(self) -> None:
        """Initialize calculator with empty memory and history."""
        self._memory: float | None = None
        self._history: List[Tuple[str, Tuple[float, ...], float]] = []

    def _validate_numeric(self, *values: Any) -> None:
        """Validate that all values are numeric (int or float).

        Args:
            *values: Values to validate

        Raises:
            TypeError: If any value is not numeric
        """
        for value in values:
            if not isinstance(value, (int, float)):
                raise TypeError(f"Invalid input type: expected int or float, got {type(value).__name__}")

    def _add_to_history(self, operation: str, operands: Tuple[float, ...], result: float) -> None:
        """Add an operation to history, maintaining max 10 entries (FIFO).

        Args:
            operation: Name of the operation (e.g., 'add', 'divide')
            operands: Tuple of operands used
            result: Result of the operation
        """
        self._history.append((operation, operands, result))
        # Keep only last 10 operations
        if len(self._history) > 10:
            self._history.pop(0)

    def add(self, a: float, b: float) -> float:
        """Add two numbers.

        Args:
            a: First number
            b: Second number

        Returns:
            Sum of a and b

        Raises:
            TypeError: If inputs are not numeric
        """
        self._validate_numeric(a, b)
        result = a + b
        self._add_to_history('add', (a, b), result)
        return result

    def subtract(self, a: float, b: float) -> float:
        """Subtract b from a.

        Args:
            a: Number to subtract from
            b: Number to subtract

        Returns:
            Difference a - b

        Raises:
            TypeError: If inputs are not numeric
        """
        self._validate_numeric(a, b)
        result = a - b
        self._add_to_history('subtract', (a, b), result)
        return result

    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers.

        Args:
            a: First number
            b: Second number

        Returns:
            Product of a and b

        Raises:
            TypeError: If inputs are not numeric
        """
        self._validate_numeric(a, b)
        result = a * b
        self._add_to_history('multiply', (a, b), result)
        return result

    def divide(self, a: float, b: float) -> float:
        """Divide a by b.

        Args:
            a: Dividend
            b: Divisor

        Returns:
            Quotient a / b

        Raises:
            TypeError: If inputs are not numeric
            ValueError: If b is zero (division by zero)
        """
        self._validate_numeric(a, b)
        if b == 0:
            raise ValueError("Division by zero is not allowed")
        result = a / b
        self._add_to_history('divide', (a, b), result)
        return result

    def memory_store(self, value: float) -> None:
        """Store a value in memory.

        Args:
            value: Value to store

        Raises:
            TypeError: If value is not numeric
        """
        self._validate_numeric(value)
        self._memory = value

    def memory_recall(self) -> float | None:
        """Recall the value stored in memory.

        Returns:
            Stored value, or None if memory is empty
        """
        return self._memory

    def memory_clear(self) -> None:
        """Clear the memory."""
        self._memory = None

    def get_history(self) -> List[Tuple[str, Tuple[float, ...], float]]:
        """Get the operation history.

        Returns:
            List of tuples (operation, operands, result) for last 10 operations
        """
        return self._history.copy()

    def clear_history(self) -> None:
        """Clear the operation history."""
        self._history.clear()
