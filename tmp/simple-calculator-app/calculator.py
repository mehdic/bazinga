"""
Calculator module with basic operations, memory, and history tracking.

This module provides a Calculator class with arithmetic operations,
memory management, and operation history.
"""

from typing import List, Tuple, Union
from collections import deque


class Calculator:
    """A calculator with basic operations, memory, and history tracking."""

    def __init__(self) -> None:
        """Initialize the calculator with empty memory and history."""
        self._memory: float | None = None
        self._history: deque = deque(maxlen=10)

    def add(self, a: float, b: float) -> float:
        """
        Add two numbers.

        Args:
            a: First number
            b: Second number

        Returns:
            Sum of a and b

        Raises:
            TypeError: If inputs are not numeric
        """
        self._validate_numeric(a, "a")
        self._validate_numeric(b, "b")
        result = a + b
        self._record_operation("add", a, b, result)
        return result

    def subtract(self, a: float, b: float) -> float:
        """
        Subtract b from a.

        Args:
            a: Number to subtract from
            b: Number to subtract

        Returns:
            Difference of a and b

        Raises:
            TypeError: If inputs are not numeric
        """
        self._validate_numeric(a, "a")
        self._validate_numeric(b, "b")
        result = a - b
        self._record_operation("subtract", a, b, result)
        return result

    def multiply(self, a: float, b: float) -> float:
        """
        Multiply two numbers.

        Args:
            a: First number
            b: Second number

        Returns:
            Product of a and b

        Raises:
            TypeError: If inputs are not numeric
        """
        self._validate_numeric(a, "a")
        self._validate_numeric(b, "b")
        result = a * b
        self._record_operation("multiply", a, b, result)
        return result

    def divide(self, a: float, b: float) -> float:
        """
        Divide a by b.

        Args:
            a: Dividend
            b: Divisor

        Returns:
            Quotient of a and b

        Raises:
            TypeError: If inputs are not numeric
            ValueError: If b is zero
        """
        self._validate_numeric(a, "a")
        self._validate_numeric(b, "b")

        if b == 0:
            raise ValueError("Cannot divide by zero")

        result = a / b
        self._record_operation("divide", a, b, result)
        return result

    def memory_store(self, value: float) -> None:
        """
        Store a value in memory.

        Args:
            value: Value to store

        Raises:
            TypeError: If value is not numeric
        """
        self._validate_numeric(value, "value")
        self._memory = value

    def memory_recall(self) -> float | None:
        """
        Recall the value stored in memory.

        Returns:
            The stored value, or None if memory is empty
        """
        return self._memory

    def memory_clear(self) -> None:
        """Clear the memory."""
        self._memory = None

    def get_history(self) -> List[Tuple[str, float, float, float]]:
        """
        Get the operation history.

        Returns:
            List of tuples (operation, operand1, operand2, result)
            containing the last 10 operations
        """
        return list(self._history)

    def clear_history(self) -> None:
        """Clear the operation history."""
        self._history.clear()

    def _validate_numeric(self, value: Union[int, float], name: str) -> None:
        """
        Validate that a value is numeric.

        Args:
            value: Value to validate
            name: Name of the parameter (for error message)

        Raises:
            TypeError: If value is not numeric
        """
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise TypeError(f"Parameter '{name}' must be numeric, got {type(value).__name__}")

    def _record_operation(
        self, operation: str, a: float, b: float, result: float
    ) -> None:
        """
        Record an operation in the history.

        Args:
            operation: Name of the operation
            a: First operand
            b: Second operand
            result: Result of the operation
        """
        self._history.append((operation, a, b, result))
