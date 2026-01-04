"""Simple Calculator Module

Provides basic arithmetic operations, memory functions, and operation history.
"""

from collections import deque
from typing import Deque


class Calculator:
    """Calculator with basic operations, memory, and history tracking."""

    def __init__(self) -> None:
        """Initialize calculator with empty memory and history."""
        self._memory: float | None = None
        self._history: Deque[str] = deque(maxlen=10)

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
        self._add_to_history(f"add({a}, {b}) = {result}")
        return result

    def subtract(self, a: float, b: float) -> float:
        """Subtract second number from first.

        Args:
            a: First number
            b: Second number to subtract

        Returns:
            Difference of a and b

        Raises:
            TypeError: If inputs are not numeric
        """
        self._validate_numeric(a, b)
        result = a - b
        self._add_to_history(f"subtract({a}, {b}) = {result}")
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
        self._add_to_history(f"multiply({a}, {b}) = {result}")
        return result

    def divide(self, a: float, b: float) -> float:
        """Divide first number by second.

        Args:
            a: Numerator
            b: Denominator

        Returns:
            Quotient of a and b

        Raises:
            TypeError: If inputs are not numeric
            ValueError: If b is zero
        """
        self._validate_numeric(a, b)
        if b == 0:
            raise ValueError("Cannot divide by zero")
        result = a / b
        self._add_to_history(f"divide({a}, {b}) = {result}")
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
        self._add_to_history(f"memory_store({value})")

    def memory_recall(self) -> float | None:
        """Recall the stored memory value.

        Returns:
            The stored value, or None if no value is stored
        """
        self._add_to_history(f"memory_recall() = {self._memory}")
        return self._memory

    def memory_clear(self) -> None:
        """Clear the stored memory value."""
        self._memory = None
        self._add_to_history("memory_clear()")

    def get_history(self) -> list[str]:
        """Get the operation history.

        Returns:
            List of the last 10 operations (most recent last)
        """
        return list(self._history)

    def _validate_numeric(self, *values: float) -> None:
        """Validate that all values are numeric.

        Args:
            *values: Values to validate

        Raises:
            TypeError: If any value is not numeric (int or float)
        """
        for value in values:
            if not isinstance(value, (int, float)):
                raise TypeError(
                    f"Invalid input type: {type(value).__name__}. "
                    f"Expected int or float."
                )

    def _add_to_history(self, entry: str) -> None:
        """Add an entry to the operation history.

        Args:
            entry: Operation description to add
        """
        self._history.append(entry)
