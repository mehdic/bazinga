"""
Unit tests for the Calculator module.

Tests cover basic operations, memory functions, history tracking,
and error handling.
"""

import pytest
from calculator import Calculator


class TestBasicOperations:
    """Test basic arithmetic operations."""

    def test_add_positive_numbers(self):
        """Test addition of positive numbers."""
        calc = Calculator()
        assert calc.add(5, 3) == 8
        assert calc.add(10.5, 2.5) == 13.0

    def test_add_negative_numbers(self):
        """Test addition with negative numbers."""
        calc = Calculator()
        assert calc.add(-5, -3) == -8
        assert calc.add(-5, 3) == -2

    def test_add_zero(self):
        """Test addition with zero."""
        calc = Calculator()
        assert calc.add(5, 0) == 5
        assert calc.add(0, 0) == 0

    def test_subtract_positive_numbers(self):
        """Test subtraction of positive numbers."""
        calc = Calculator()
        assert calc.subtract(10, 3) == 7
        assert calc.subtract(5.5, 2.5) == 3.0

    def test_subtract_negative_numbers(self):
        """Test subtraction with negative numbers."""
        calc = Calculator()
        assert calc.subtract(-5, -3) == -2
        assert calc.subtract(5, -3) == 8

    def test_multiply_positive_numbers(self):
        """Test multiplication of positive numbers."""
        calc = Calculator()
        assert calc.multiply(5, 3) == 15
        assert calc.multiply(2.5, 4) == 10.0

    def test_multiply_negative_numbers(self):
        """Test multiplication with negative numbers."""
        calc = Calculator()
        assert calc.multiply(-5, 3) == -15
        assert calc.multiply(-5, -3) == 15

    def test_multiply_by_zero(self):
        """Test multiplication by zero."""
        calc = Calculator()
        assert calc.multiply(5, 0) == 0
        assert calc.multiply(0, 0) == 0

    def test_divide_positive_numbers(self):
        """Test division of positive numbers."""
        calc = Calculator()
        assert calc.divide(10, 2) == 5.0
        assert calc.divide(7.5, 2.5) == 3.0

    def test_divide_negative_numbers(self):
        """Test division with negative numbers."""
        calc = Calculator()
        assert calc.divide(-10, 2) == -5.0
        assert calc.divide(-10, -2) == 5.0

    def test_divide_by_zero_raises_error(self):
        """Test that division by zero raises ValueError."""
        calc = Calculator()
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            calc.divide(5, 0)


class TestErrorHandling:
    """Test error handling for invalid inputs."""

    def test_add_with_string_raises_error(self):
        """Test that non-numeric input raises TypeError."""
        calc = Calculator()
        with pytest.raises(TypeError, match="must be numeric"):
            calc.add("5", 3)

    def test_subtract_with_none_raises_error(self):
        """Test that None input raises TypeError."""
        calc = Calculator()
        with pytest.raises(TypeError, match="must be numeric"):
            calc.subtract(5, None)

    def test_multiply_with_list_raises_error(self):
        """Test that list input raises TypeError."""
        calc = Calculator()
        with pytest.raises(TypeError, match="must be numeric"):
            calc.multiply([5], 3)

    def test_divide_with_boolean_raises_error(self):
        """Test that boolean input raises TypeError."""
        calc = Calculator()
        with pytest.raises(TypeError, match="must be numeric"):
            calc.divide(True, 5)


class TestMemoryFunctions:
    """Test memory storage and recall functions."""

    def test_memory_store_and_recall(self):
        """Test storing and recalling a value."""
        calc = Calculator()
        calc.memory_store(42)
        assert calc.memory_recall() == 42

    def test_memory_store_updates_value(self):
        """Test that storing updates the previous value."""
        calc = Calculator()
        calc.memory_store(10)
        calc.memory_store(20)
        assert calc.memory_recall() == 20

    def test_memory_recall_empty(self):
        """Test that recalling from empty memory returns None."""
        calc = Calculator()
        assert calc.memory_recall() is None

    def test_memory_clear(self):
        """Test clearing memory."""
        calc = Calculator()
        calc.memory_store(42)
        calc.memory_clear()
        assert calc.memory_recall() is None

    def test_memory_store_float(self):
        """Test storing float values."""
        calc = Calculator()
        calc.memory_store(3.14159)
        assert calc.memory_recall() == 3.14159

    def test_memory_store_negative(self):
        """Test storing negative values."""
        calc = Calculator()
        calc.memory_store(-100)
        assert calc.memory_recall() == -100

    def test_memory_store_invalid_type_raises_error(self):
        """Test that storing non-numeric value raises TypeError."""
        calc = Calculator()
        with pytest.raises(TypeError, match="must be numeric"):
            calc.memory_store("42")


class TestHistory:
    """Test operation history tracking."""

    def test_history_records_operations(self):
        """Test that operations are recorded in history."""
        calc = Calculator()
        calc.add(5, 3)
        calc.subtract(10, 2)

        history = calc.get_history()
        assert len(history) == 2
        assert history[0] == ("add", 5, 3, 8)
        assert history[1] == ("subtract", 10, 2, 8)

    def test_history_records_all_operations(self):
        """Test that all operation types are recorded."""
        calc = Calculator()
        calc.add(5, 3)
        calc.subtract(10, 2)
        calc.multiply(4, 5)
        calc.divide(20, 4)

        history = calc.get_history()
        assert len(history) == 4
        assert history[0][0] == "add"
        assert history[1][0] == "subtract"
        assert history[2][0] == "multiply"
        assert history[3][0] == "divide"

    def test_history_max_10_operations(self):
        """Test that history keeps only last 10 operations."""
        calc = Calculator()

        # Perform 15 operations
        for i in range(15):
            calc.add(i, 1)

        history = calc.get_history()
        assert len(history) == 10

        # Verify it's the last 10 operations (5-14)
        for i, (op, a, b, result) in enumerate(history):
            assert a == i + 5

    def test_history_fifo_behavior(self):
        """Test that oldest operations are removed when limit is reached."""
        calc = Calculator()

        # Add 10 operations
        for i in range(10):
            calc.add(i, 0)

        # Add one more
        calc.add(999, 0)

        history = calc.get_history()
        # First operation (0+0) should be gone
        assert history[0][1] == 1  # Second operation's first operand
        # Last operation should be present
        assert history[-1][1] == 999

    def test_clear_history(self):
        """Test clearing the history."""
        calc = Calculator()
        calc.add(5, 3)
        calc.subtract(10, 2)

        calc.clear_history()
        assert calc.get_history() == []

    def test_history_empty_initially(self):
        """Test that history is empty for new calculator."""
        calc = Calculator()
        assert calc.get_history() == []


class TestIntegration:
    """Integration tests combining multiple features."""

    def test_calculator_workflow(self):
        """Test a typical calculator workflow."""
        calc = Calculator()

        # Perform some calculations
        result1 = calc.add(10, 5)
        assert result1 == 15

        # Store result in memory
        calc.memory_store(result1)

        # Perform another calculation
        result2 = calc.multiply(3, 4)
        assert result2 == 12

        # Recall from memory and use it
        mem_value = calc.memory_recall()
        result3 = calc.subtract(mem_value, result2)
        assert result3 == 3

        # Check history
        history = calc.get_history()
        assert len(history) == 3

    def test_edge_cases_combination(self):
        """Test edge cases in combination."""
        calc = Calculator()

        # Operations with zero
        calc.add(0, 0)
        calc.multiply(100, 0)

        # Negative numbers
        calc.subtract(-5, -10)

        # Memory with negative
        calc.memory_store(-42)
        assert calc.memory_recall() == -42

        # History should have all operations
        assert len(calc.get_history()) == 3
