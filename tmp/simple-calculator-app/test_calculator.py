"""
Unit tests for the Calculator module.

Tests cover:
- Basic arithmetic operations
- Memory functions
- History tracking
- Error handling
- Edge cases
"""
import pytest
from calculator import Calculator


class TestBasicOperations:
    """Test basic arithmetic operations."""

    def test_add_positive_numbers(self):
        """Test adding two positive numbers."""
        calc = Calculator()
        assert calc.add(5, 3) == 8
        assert calc.add(10.5, 2.5) == 13.0

    def test_add_negative_numbers(self):
        """Test adding negative numbers."""
        calc = Calculator()
        assert calc.add(-5, -3) == -8
        assert calc.add(-5, 3) == -2

    def test_subtract_positive_numbers(self):
        """Test subtracting positive numbers."""
        calc = Calculator()
        assert calc.subtract(10, 3) == 7
        assert calc.subtract(5.5, 2.5) == 3.0

    def test_subtract_negative_numbers(self):
        """Test subtracting with negative numbers."""
        calc = Calculator()
        assert calc.subtract(-5, -3) == -2
        assert calc.subtract(5, -3) == 8

    def test_multiply_positive_numbers(self):
        """Test multiplying positive numbers."""
        calc = Calculator()
        assert calc.multiply(5, 3) == 15
        assert calc.multiply(2.5, 4) == 10.0

    def test_multiply_negative_numbers(self):
        """Test multiplying with negative numbers."""
        calc = Calculator()
        assert calc.multiply(-5, 3) == -15
        assert calc.multiply(-5, -3) == 15

    def test_multiply_by_zero(self):
        """Test multiplying by zero."""
        calc = Calculator()
        assert calc.multiply(5, 0) == 0
        assert calc.multiply(0, 10) == 0

    def test_divide_positive_numbers(self):
        """Test dividing positive numbers."""
        calc = Calculator()
        assert calc.divide(10, 2) == 5
        assert calc.divide(7.5, 2.5) == 3.0

    def test_divide_negative_numbers(self):
        """Test dividing with negative numbers."""
        calc = Calculator()
        assert calc.divide(-10, 2) == -5
        assert calc.divide(10, -2) == -5
        assert calc.divide(-10, -2) == 5

    def test_divide_by_zero_raises_value_error(self):
        """Test that dividing by zero raises ValueError."""
        calc = Calculator()
        with pytest.raises(ValueError, match="Division by zero is not allowed"):
            calc.divide(10, 0)

    def test_divide_zero_by_number(self):
        """Test dividing zero by a number."""
        calc = Calculator()
        assert calc.divide(0, 5) == 0


class TestMemoryFunctions:
    """Test memory storage functions."""

    def test_memory_store_and_recall(self):
        """Test storing and recalling a value."""
        calc = Calculator()
        calc.memory_store(42)
        assert calc.memory_recall() == 42

    def test_memory_store_float(self):
        """Test storing a float value."""
        calc = Calculator()
        calc.memory_store(3.14159)
        assert calc.memory_recall() == 3.14159

    def test_memory_recall_empty(self):
        """Test recalling from empty memory."""
        calc = Calculator()
        assert calc.memory_recall() is None

    def test_memory_clear(self):
        """Test clearing memory."""
        calc = Calculator()
        calc.memory_store(100)
        calc.memory_clear()
        assert calc.memory_recall() is None

    def test_memory_overwrite(self):
        """Test overwriting memory value."""
        calc = Calculator()
        calc.memory_store(10)
        calc.memory_store(20)
        assert calc.memory_recall() == 20

    def test_memory_store_negative(self):
        """Test storing negative value."""
        calc = Calculator()
        calc.memory_store(-99)
        assert calc.memory_recall() == -99

    def test_memory_store_zero(self):
        """Test storing zero."""
        calc = Calculator()
        calc.memory_store(0)
        assert calc.memory_recall() == 0


class TestHistoryTracking:
    """Test operation history tracking."""

    def test_history_records_operations(self):
        """Test that operations are recorded in history."""
        calc = Calculator()
        calc.add(5, 3)
        calc.subtract(10, 2)

        history = calc.get_history()
        assert len(history) == 2
        assert history[0] == ('add', (5, 3), 8)
        assert history[1] == ('subtract', (10, 2), 8)

    def test_history_all_operations(self):
        """Test that all operation types are recorded."""
        calc = Calculator()
        calc.add(10, 5)
        calc.subtract(20, 8)
        calc.multiply(4, 3)
        calc.divide(15, 3)

        history = calc.get_history()
        assert len(history) == 4
        assert history[0][0] == 'add'
        assert history[1][0] == 'subtract'
        assert history[2][0] == 'multiply'
        assert history[3][0] == 'divide'

    def test_history_max_ten_operations(self):
        """Test that history maintains maximum 10 operations (FIFO)."""
        calc = Calculator()
        # Perform 15 operations
        for i in range(15):
            calc.add(i, 1)

        history = calc.get_history()
        assert len(history) == 10
        # First 5 should be dropped, so history should start with add(5, 1)
        assert history[0] == ('add', (5, 1), 6)
        assert history[9] == ('add', (14, 1), 15)

    def test_history_fifo_behavior(self):
        """Test FIFO behavior when history exceeds 10 operations."""
        calc = Calculator()
        # Add 12 operations
        for i in range(12):
            calc.add(i, 0)

        history = calc.get_history()
        # Should only contain last 10 (operations 2-11)
        assert len(history) == 10
        assert history[0] == ('add', (2, 0), 2)
        assert history[-1] == ('add', (11, 0), 11)

    def test_get_history_returns_copy(self):
        """Test that get_history returns a copy, not reference."""
        calc = Calculator()
        calc.add(5, 3)

        history1 = calc.get_history()
        calc.add(10, 2)
        history2 = calc.get_history()

        # Original history should not be modified
        assert len(history1) == 1
        assert len(history2) == 2

    def test_clear_history(self):
        """Test clearing history."""
        calc = Calculator()
        calc.add(5, 3)
        calc.multiply(2, 4)
        calc.clear_history()

        assert len(calc.get_history()) == 0

    def test_history_empty_initially(self):
        """Test that history is empty on initialization."""
        calc = Calculator()
        assert len(calc.get_history()) == 0


class TestErrorHandling:
    """Test error handling for invalid inputs."""

    def test_add_with_string_raises_type_error(self):
        """Test that adding with string raises TypeError."""
        calc = Calculator()
        with pytest.raises(TypeError, match="Invalid input type"):
            calc.add("5", 3)
        with pytest.raises(TypeError, match="Invalid input type"):
            calc.add(5, "3")

    def test_subtract_with_none_raises_type_error(self):
        """Test that subtracting with None raises TypeError."""
        calc = Calculator()
        with pytest.raises(TypeError, match="Invalid input type"):
            calc.subtract(None, 5)

    def test_multiply_with_list_raises_type_error(self):
        """Test that multiplying with list raises TypeError."""
        calc = Calculator()
        with pytest.raises(TypeError, match="Invalid input type"):
            calc.multiply([1, 2], 5)

    def test_divide_with_dict_raises_type_error(self):
        """Test that dividing with dict raises TypeError."""
        calc = Calculator()
        with pytest.raises(TypeError, match="Invalid input type"):
            calc.divide(10, {"value": 2})

    def test_memory_store_with_string_raises_type_error(self):
        """Test that storing string in memory raises TypeError."""
        calc = Calculator()
        with pytest.raises(TypeError, match="Invalid input type"):
            calc.memory_store("100")

    def test_division_by_zero_exact_message(self):
        """Test division by zero error message."""
        calc = Calculator()
        with pytest.raises(ValueError) as exc_info:
            calc.divide(100, 0)
        assert str(exc_info.value) == "Division by zero is not allowed"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_operations_with_floats(self):
        """Test operations work with floats."""
        calc = Calculator()
        assert calc.add(0.1, 0.2) == pytest.approx(0.3)
        assert calc.multiply(0.5, 0.5) == 0.25

    def test_operations_with_integers(self):
        """Test operations work with integers."""
        calc = Calculator()
        assert calc.add(1, 2) == 3
        assert isinstance(calc.add(1, 2), (int, float))

    def test_large_numbers(self):
        """Test operations with large numbers."""
        calc = Calculator()
        large = 10**15
        assert calc.add(large, 1) == large + 1
        assert calc.multiply(large, 2) == large * 2

    def test_very_small_numbers(self):
        """Test operations with very small numbers."""
        calc = Calculator()
        small = 1e-10
        result = calc.add(small, small)
        assert result == pytest.approx(2e-10)

    def test_mixed_int_float_operations(self):
        """Test operations mixing int and float."""
        calc = Calculator()
        assert calc.add(5, 2.5) == 7.5
        assert calc.multiply(3, 1.5) == 4.5

    def test_calculator_state_isolation(self):
        """Test that multiple calculator instances are isolated."""
        calc1 = Calculator()
        calc2 = Calculator()

        calc1.memory_store(100)
        calc1.add(1, 2)

        assert calc2.memory_recall() is None
        assert len(calc2.get_history()) == 0

    def test_operations_dont_affect_memory(self):
        """Test that operations don't modify memory."""
        calc = Calculator()
        calc.memory_store(42)
        calc.add(5, 3)
        calc.multiply(10, 2)

        assert calc.memory_recall() == 42

    def test_history_survives_memory_operations(self):
        """Test that memory operations don't affect history."""
        calc = Calculator()
        calc.add(5, 3)
        calc.memory_store(100)
        calc.memory_clear()

        history = calc.get_history()
        assert len(history) == 1
        assert history[0] == ('add', (5, 3), 8)
