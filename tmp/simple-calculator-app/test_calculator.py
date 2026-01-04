"""Unit tests for calculator module."""

import pytest
from calculator import Calculator


class TestBasicOperations:
    """Test basic arithmetic operations."""

    def test_add_positive_numbers(self):
        """Test addition with positive numbers."""
        calc = Calculator()
        assert calc.add(5, 3) == 8
        assert calc.add(10.5, 2.5) == 13.0

    def test_add_negative_numbers(self):
        """Test addition with negative numbers."""
        calc = Calculator()
        assert calc.add(-5, -3) == -8
        assert calc.add(-10, 5) == -5

    def test_subtract_positive_numbers(self):
        """Test subtraction with positive numbers."""
        calc = Calculator()
        assert calc.subtract(10, 3) == 7
        assert calc.subtract(5.5, 2.5) == 3.0

    def test_subtract_negative_numbers(self):
        """Test subtraction with negative numbers."""
        calc = Calculator()
        assert calc.subtract(-5, -3) == -2
        assert calc.subtract(5, 10) == -5

    def test_multiply_positive_numbers(self):
        """Test multiplication with positive numbers."""
        calc = Calculator()
        assert calc.multiply(5, 3) == 15
        assert calc.multiply(2.5, 4) == 10.0

    def test_multiply_negative_numbers(self):
        """Test multiplication with negative numbers."""
        calc = Calculator()
        assert calc.multiply(-5, 3) == -15
        assert calc.multiply(-2, -3) == 6

    def test_multiply_by_zero(self):
        """Test multiplication by zero."""
        calc = Calculator()
        assert calc.multiply(5, 0) == 0
        assert calc.multiply(0, 5) == 0

    def test_divide_positive_numbers(self):
        """Test division with positive numbers."""
        calc = Calculator()
        assert calc.divide(10, 2) == 5
        assert calc.divide(7.5, 2.5) == 3.0

    def test_divide_negative_numbers(self):
        """Test division with negative numbers."""
        calc = Calculator()
        assert calc.divide(-10, 2) == -5
        assert calc.divide(-6, -3) == 2


class TestErrorHandling:
    """Test error handling."""

    def test_divide_by_zero(self):
        """Test division by zero raises ValueError."""
        calc = Calculator()
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            calc.divide(10, 0)

    def test_add_invalid_type_first_arg(self):
        """Test addition with invalid first argument type."""
        calc = Calculator()
        with pytest.raises(TypeError, match="Invalid input type"):
            calc.add("5", 3)  # type: ignore

    def test_add_invalid_type_second_arg(self):
        """Test addition with invalid second argument type."""
        calc = Calculator()
        with pytest.raises(TypeError, match="Invalid input type"):
            calc.add(5, "3")  # type: ignore

    def test_subtract_invalid_type(self):
        """Test subtraction with invalid type."""
        calc = Calculator()
        with pytest.raises(TypeError, match="Invalid input type"):
            calc.subtract(5, None)  # type: ignore

    def test_multiply_invalid_type(self):
        """Test multiplication with invalid type."""
        calc = Calculator()
        with pytest.raises(TypeError, match="Invalid input type"):
            calc.multiply([1, 2], 3)  # type: ignore

    def test_divide_invalid_type(self):
        """Test division with invalid type."""
        calc = Calculator()
        with pytest.raises(TypeError, match="Invalid input type"):
            calc.divide(10, {"value": 2})  # type: ignore

    def test_memory_store_invalid_type(self):
        """Test memory store with invalid type."""
        calc = Calculator()
        with pytest.raises(TypeError, match="Invalid input type"):
            calc.memory_store("42")  # type: ignore


class TestMemoryFunctions:
    """Test memory storage and retrieval."""

    def test_memory_store_and_recall(self):
        """Test storing and recalling a value."""
        calc = Calculator()
        calc.memory_store(42.5)
        assert calc.memory_recall() == 42.5

    def test_memory_recall_empty(self):
        """Test recalling when no value is stored."""
        calc = Calculator()
        assert calc.memory_recall() is None

    def test_memory_store_overwrites(self):
        """Test that new store overwrites previous value."""
        calc = Calculator()
        calc.memory_store(10)
        calc.memory_store(20)
        assert calc.memory_recall() == 20

    def test_memory_clear(self):
        """Test clearing memory."""
        calc = Calculator()
        calc.memory_store(42)
        calc.memory_clear()
        assert calc.memory_recall() is None

    def test_memory_with_negative_numbers(self):
        """Test memory with negative numbers."""
        calc = Calculator()
        calc.memory_store(-15.5)
        assert calc.memory_recall() == -15.5


class TestHistory:
    """Test operation history tracking."""

    def test_history_tracks_operations(self):
        """Test that operations are added to history."""
        calc = Calculator()
        calc.add(5, 3)
        calc.subtract(10, 2)
        history = calc.get_history()
        assert len(history) == 2
        assert "add(5, 3) = 8" in history[0]
        assert "subtract(10, 2) = 8" in history[1]

    def test_history_max_10_operations(self):
        """Test that history is limited to last 10 operations."""
        calc = Calculator()
        # Perform 15 operations
        for i in range(15):
            calc.add(i, 1)
        history = calc.get_history()
        assert len(history) == 10
        # First 5 operations should be gone, last 10 should remain
        assert "add(5, 1)" in history[0]
        assert "add(14, 1)" in history[9]

    def test_history_includes_memory_operations(self):
        """Test that memory operations are tracked in history."""
        calc = Calculator()
        calc.memory_store(42)
        calc.memory_recall()
        calc.memory_clear()
        history = calc.get_history()
        assert len(history) == 3
        assert "memory_store(42)" in history[0]
        assert "memory_recall()" in history[1]
        assert "memory_clear()" in history[2]

    def test_history_empty_on_init(self):
        """Test that history is empty on initialization."""
        calc = Calculator()
        assert calc.get_history() == []

    def test_history_with_all_operations(self):
        """Test history with mix of all operation types."""
        calc = Calculator()
        calc.add(1, 2)
        calc.multiply(3, 4)
        calc.memory_store(10)
        calc.divide(20, 2)
        history = calc.get_history()
        assert len(history) == 4


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_operations(self):
        """Test operations with zero."""
        calc = Calculator()
        assert calc.add(0, 0) == 0
        assert calc.subtract(0, 0) == 0
        assert calc.multiply(0, 100) == 0

    def test_large_numbers(self):
        """Test operations with large numbers."""
        calc = Calculator()
        assert calc.add(1e10, 1e10) == 2e10
        assert calc.multiply(1e5, 1e5) == 1e10

    def test_small_decimals(self):
        """Test operations with small decimal numbers."""
        calc = Calculator()
        result = calc.add(0.1, 0.2)
        assert abs(result - 0.3) < 1e-10  # Handle floating point precision

    def test_negative_zero(self):
        """Test operations with negative zero."""
        calc = Calculator()
        assert calc.add(-0.0, 5) == 5
        assert calc.multiply(-0.0, 100) == 0

    def test_integer_inputs(self):
        """Test that integers work correctly."""
        calc = Calculator()
        assert calc.add(5, 3) == 8
        assert isinstance(calc.add(5, 3), (int, float))
