"""
Calculator module with core operations, memory functions, and history tracking.

This module provides a Calculator class that implements basic arithmetic operations
with memory management and operation history tracking (last 10 operations).
"""

from collections import deque
from typing import Union, List, Dict, Any


class Calculator:
    """A simple calculator with memory and history tracking."""

    def __init__(self) -> None:
        """Initialize the calculator with empty memory and history."""
        self.memory: Union[int, float, None] = None
        self.history: deque = deque(maxlen=10)

    def add(self, a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
        """
        Add two numbers.

        Args:
            a: First operand (int or float)
            b: Second operand (int or float)

        Returns:
            The sum of a and b

        Raises:
            TypeError: If operands are not numeric types
        """
        try:
            result = a + b
        except TypeError:
            raise TypeError(
                f"unsupported operand type(s) for +: "
                f"'{type(a).__name__}' and '{type(b).__name__}'"
            )
        self._record_operation("add", a, b, result)
        return result

    def subtract(
        self, a: Union[int, float], b: Union[int, float]
    ) -> Union[int, float]:
        """
        Subtract two numbers.

        Args:
            a: First operand (int or float)
            b: Second operand (int or float)

        Returns:
            The difference of a and b (a - b)

        Raises:
            TypeError: If operands are not numeric types
        """
        try:
            result = a - b
        except TypeError:
            raise TypeError(
                f"unsupported operand type(s) for -: "
                f"'{type(a).__name__}' and '{type(b).__name__}'"
            )
        self._record_operation("subtract", a, b, result)
        return result

    def multiply(
        self, a: Union[int, float], b: Union[int, float]
    ) -> Union[int, float]:
        """
        Multiply two numbers.

        Args:
            a: First operand (int or float)
            b: Second operand (int or float)

        Returns:
            The product of a and b

        Raises:
            TypeError: If operands are not numeric types
        """
        try:
            result = a * b
        except TypeError:
            raise TypeError(
                f"unsupported operand type(s) for *: "
                f"'{type(a).__name__}' and '{type(b).__name__}'"
            )
        self._record_operation("multiply", a, b, result)
        return result

    def divide(self, a: Union[int, float], b: Union[int, float]) -> float:
        """
        Divide two numbers.

        Args:
            a: Numerator (int or float)
            b: Denominator (int or float)

        Returns:
            The quotient of a and b

        Raises:
            ValueError: If b is zero
            TypeError: If operands are not numeric types
        """
        if b == 0:
            raise ValueError("Cannot divide by zero")
        try:
            result = a / b
        except TypeError:
            raise TypeError(
                f"unsupported operand type(s) for /: "
                f"'{type(a).__name__}' and '{type(b).__name__}'"
            )
        self._record_operation("divide", a, b, result)
        return result

    def memory_store(self, value: Union[int, float]) -> None:
        """
        Store a value in memory.

        Args:
            value: The value to store (int or float)

        Raises:
            TypeError: If value is not numeric
        """
        if not isinstance(value, (int, float)):
            raise TypeError(
                f"Cannot store non-numeric value of type '{type(value).__name__}'"
            )
        self.memory = value

    def memory_recall(self) -> Union[int, float, None]:
        """
        Recall the value stored in memory.

        Returns:
            The stored value, or None if memory is empty
        """
        return self.memory

    def memory_clear(self) -> None:
        """Clear the memory."""
        self.memory = None

    def get_history(self) -> List[Dict[str, Any]]:
        """
        Get the operation history.

        Returns:
            A list of dictionaries representing the last operations (up to 10)
        """
        return list(self.history)

    def clear_history(self) -> None:
        """Clear all operation history."""
        self.history.clear()

    def _record_operation(
        self, operation: str, a: Union[int, float], b: Union[int, float],
        result: Union[int, float]
    ) -> None:
        """
        Record an operation in history.

        Args:
            operation: The operation name (add, subtract, multiply, divide)
            a: First operand
            b: Second operand
            result: The result of the operation
        """
        self.history.append(
            {
                "operation": operation,
                "operand_a": a,
                "operand_b": b,
                "result": result,
            }
        )
