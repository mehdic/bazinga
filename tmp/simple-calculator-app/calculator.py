"""
Simple Calculator Module

A calculator module providing basic arithmetic operations, memory functions,
and operation history tracking.
"""

from collections import deque
from typing import Union, List, Tuple


class Calculator:
    """A simple calculator with memory and history functionality."""

    def __init__(self):
        """Initialize the calculator with empty memory and history."""
        self.memory = None
        self.history = deque(maxlen=10)  # Stores last 10 operations

    def _validate_operands(self, *operands) -> None:
        """
        Validate that all operands are numeric types.

        Args:
            *operands: Variable number of operands to validate

        Raises:
            TypeError: If any operand is not a number (int or float)
        """
        for operand in operands:
            if not isinstance(operand, (int, float)) or isinstance(operand, bool):
                raise TypeError(
                    f"Operand must be a number (int or float), got {type(operand).__name__}"
                )

    def _record_operation(self, operation: str, operands: Tuple, result: Union[int, float]) -> None:
        """
        Record an operation to the history.

        Args:
            operation: Name of the operation (e.g., 'add', 'divide')
            operands: Tuple of operands
            result: Result of the operation
        """
        self.history.append((operation, operands, result))

    def add(self, a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
        """
        Add two numbers.

        Args:
            a: First operand
            b: Second operand

        Returns:
            Sum of a and b

        Raises:
            TypeError: If either operand is not a number
        """
        self._validate_operands(a, b)
        result = a + b
        self._record_operation("add", (a, b), result)
        return result

    def subtract(self, a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
        """
        Subtract b from a.

        Args:
            a: First operand (minuend)
            b: Second operand (subtrahend)

        Returns:
            Difference of a and b

        Raises:
            TypeError: If either operand is not a number
        """
        self._validate_operands(a, b)
        result = a - b
        self._record_operation("subtract", (a, b), result)
        return result

    def multiply(self, a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
        """
        Multiply two numbers.

        Args:
            a: First operand
            b: Second operand

        Returns:
            Product of a and b

        Raises:
            TypeError: If either operand is not a number
        """
        self._validate_operands(a, b)
        result = a * b
        self._record_operation("multiply", (a, b), result)
        return result

    def divide(self, a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
        """
        Divide a by b.

        Args:
            a: Dividend
            b: Divisor

        Returns:
            Result of a divided by b

        Raises:
            TypeError: If either operand is not a number
            ValueError: If divisor (b) is zero
        """
        self._validate_operands(a, b)
        if b == 0:
            raise ValueError("Cannot divide by zero")
        result = a / b
        self._record_operation("divide", (a, b), result)
        return result

    def memory_store(self, value: Union[int, float]) -> None:
        """
        Store a value in memory.

        Args:
            value: The value to store

        Raises:
            TypeError: If value is not a number
        """
        self._validate_operands(value)
        self.memory = value

    def memory_recall(self) -> Union[int, float, None]:
        """
        Recall the value stored in memory.

        Returns:
            The value stored in memory, or None if nothing has been stored
        """
        return self.memory

    def memory_clear(self) -> None:
        """Clear the memory."""
        self.memory = None

    def get_history(self) -> List[Tuple]:
        """
        Get the operation history.

        Returns:
            List of tuples containing (operation_name, operands, result)
        """
        return list(self.history)

    def clear_history(self) -> None:
        """Clear the operation history."""
        self.history.clear()
