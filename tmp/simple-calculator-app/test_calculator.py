"""
Unit tests for the calculator module.

Tests cover all operations, error handling, memory functions, and history tracking.
"""

import pytest
from calculator import Calculator


class TestBasicOperations:
    """Tests for basic arithmetic operations."""

    def test_add_positive_integers(self):
        """Test adding two positive integers."""
        calc = Calculator()
        assert calc.add(2, 3) == 5

    def test_add_negative_integers(self):
        """Test adding negative integers."""
        calc = Calculator()
        assert calc.add(-2, -3) == -5

    def test_add_mixed_sign_integers(self):
        """Test adding integers with mixed signs."""
        calc = Calculator()
        assert calc.add(10, -3) == 7

    def test_add_floats(self):
        """Test adding floating-point numbers."""
        calc = Calculator()
        assert pytest.approx(calc.add(2.5, 3.7)) == 6.2

    def test_add_zero(self):
        """Test adding zero."""
        calc = Calculator()
        assert calc.add(5, 0) == 5

    def test_subtract_positive_integers(self):
        """Test subtracting two positive integers."""
        calc = Calculator()
        assert calc.subtract(10, 3) == 7

    def test_subtract_negative_result(self):
        """Test subtraction resulting in negative number."""
        calc = Calculator()
        assert calc.subtract(3, 10) == -7

    def test_subtract_negative_operands(self):
        """Test subtracting negative numbers."""
        calc = Calculator()
        assert calc.subtract(-5, -3) == -2

    def test_subtract_floats(self):
        """Test subtracting floating-point numbers."""
        calc = Calculator()
        assert pytest.approx(calc.subtract(10.5, 2.3)) == 8.2

    def test_multiply_positive_integers(self):
        """Test multiplying two positive integers."""
        calc = Calculator()
        assert calc.multiply(4, 5) == 20

    def test_multiply_negative_integers(self):
        """Test multiplying negative integers."""
        calc = Calculator()
        assert calc.multiply(-2, -3) == 6

    def test_multiply_mixed_sign(self):
        """Test multiplying numbers with mixed signs."""
        calc = Calculator()
        assert calc.multiply(-4, 5) == -20

    def test_multiply_by_zero(self):
        """Test multiplying by zero."""
        calc = Calculator()
        assert calc.multiply(100, 0) == 0

    def test_multiply_floats(self):
        """Test multiplying floating-point numbers."""
        calc = Calculator()
        assert pytest.approx(calc.multiply(2.5, 4.0)) == 10.0

    def test_divide_positive_integers(self):
        """Test dividing two positive integers."""
        calc = Calculator()
        assert calc.divide(10, 2) == 5

    def test_divide_with_remainder(self):
        """Test division resulting in float."""
        calc = Calculator()
        assert pytest.approx(calc.divide(10, 3)) == 10 / 3

    def test_divide_floats(self):
        """Test dividing floating-point numbers."""
        calc = Calculator()
        assert pytest.approx(calc.divide(7.5, 2.5)) == 3.0

    def test_divide_negative_numbers(self):
        """Test dividing negative numbers."""
        calc = Calculator()
        assert pytest.approx(calc.divide(-10, 2)) == -5

    def test_divide_by_zero_raises_error(self):
        """Test that dividing by zero raises ValueError."""
        calc = Calculator()
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            calc.divide(10, 0)

    def test_divide_negative_by_negative(self):
        """Test dividing negative by negative."""
        calc = Calculator()
        assert pytest.approx(calc.divide(-10, -2)) == 5


class TestErrorHandling:
    """Tests for error handling and input validation."""

    def test_add_with_string_raises_typeerror(self):
        """Test that adding with string operand raises TypeError."""
        calc = Calculator()
        with pytest.raises(TypeError, match="Operand must be a number"):
            calc.add("5", 3)

    def test_add_with_none_raises_typeerror(self):
        """Test that adding with None raises TypeError."""
        calc = Calculator()
        with pytest.raises(TypeError, match="Operand must be a number"):
            calc.add(None, 3)

    def test_add_with_list_raises_typeerror(self):
        """Test that adding with list operand raises TypeError."""
        calc = Calculator()
        with pytest.raises(TypeError, match="Operand must be a number"):
            calc.add([1, 2], 3)

    def test_subtract_with_string_raises_typeerror(self):
        """Test that subtracting with string operand raises TypeError."""
        calc = Calculator()
        with pytest.raises(TypeError, match="Operand must be a number"):
            calc.subtract(10, "5")

    def test_multiply_with_boolean_raises_typeerror(self):
        """Test that boolean values raise TypeError."""
        calc = Calculator()
        with pytest.raises(TypeError, match="Operand must be a number"):
            calc.multiply(True, 5)

    def test_divide_with_dict_raises_typeerror(self):
        """Test that dividing with dict operand raises TypeError."""
        calc = Calculator()
        with pytest.raises(TypeError, match="Operand must be a number"):
            calc.divide(10, {"value": 2})

    def test_memory_store_with_string_raises_typeerror(self):
        """Test that storing string in memory raises TypeError."""
        calc = Calculator()
        with pytest.raises(TypeError, match="Operand must be a number"):
            calc.memory_store("value")


class TestMemoryFunctions:
    """Tests for memory storage and recall functionality."""

    def test_memory_store_integer(self):
        """Test storing an integer in memory."""
        calc = Calculator()
        calc.memory_store(42)
        assert calc.memory_recall() == 42

    def test_memory_store_float(self):
        """Test storing a float in memory."""
        calc = Calculator()
        calc.memory_store(3.14)
        assert pytest.approx(calc.memory_recall()) == 3.14

    def test_memory_store_zero(self):
        """Test storing zero in memory."""
        calc = Calculator()
        calc.memory_store(0)
        assert calc.memory_recall() == 0

    def test_memory_store_negative(self):
        """Test storing negative number in memory."""
        calc = Calculator()
        calc.memory_store(-100)
        assert calc.memory_recall() == -100

    def test_memory_recall_empty(self):
        """Test recalling from empty memory."""
        calc = Calculator()
        assert calc.memory_recall() is None

    def test_memory_overwrite(self):
        """Test that storing new value overwrites old value."""
        calc = Calculator()
        calc.memory_store(10)
        assert calc.memory_recall() == 10
        calc.memory_store(20)
        assert calc.memory_recall() == 20

    def test_memory_clear(self):
        """Test clearing memory."""
        calc = Calculator()
        calc.memory_store(42)
        assert calc.memory_recall() == 42
        calc.memory_clear()
        assert calc.memory_recall() is None

    def test_memory_clear_when_empty(self):
        """Test clearing memory that is already empty."""
        calc = Calculator()
        calc.memory_clear()  # Should not raise error
        assert calc.memory_recall() is None

    def test_multiple_memory_operations(self):
        """Test sequence of memory operations."""
        calc = Calculator()
        calc.memory_store(100)
        assert calc.memory_recall() == 100
        calc.memory_clear()
        assert calc.memory_recall() is None
        calc.memory_store(200)
        assert calc.memory_recall() == 200


class TestHistoryTracking:
    """Tests for operation history tracking."""

    def test_history_records_addition(self):
        """Test that addition is recorded in history."""
        calc = Calculator()
        result = calc.add(2, 3)
        history = calc.get_history()
        assert len(history) == 1
        assert history[0] == ("add", (2, 3), 5)

    def test_history_records_subtraction(self):
        """Test that subtraction is recorded in history."""
        calc = Calculator()
        result = calc.subtract(10, 3)
        history = calc.get_history()
        assert len(history) == 1
        assert history[0] == ("subtract", (10, 3), 7)

    def test_history_records_multiplication(self):
        """Test that multiplication is recorded in history."""
        calc = Calculator()
        calc.multiply(4, 5)
        history = calc.get_history()
        assert len(history) == 1
        assert history[0] == ("multiply", (4, 5), 20)

    def test_history_records_division(self):
        """Test that division is recorded in history."""
        calc = Calculator()
        calc.divide(10, 2)
        history = calc.get_history()
        assert len(history) == 1
        assert history[0] == ("divide", (10, 2), 5.0)

    def test_history_multiple_operations(self):
        """Test that multiple operations are recorded in history."""
        calc = Calculator()
        calc.add(2, 3)
        calc.subtract(10, 4)
        calc.multiply(2, 5)
        history = calc.get_history()
        assert len(history) == 3
        assert history[0][0] == "add"
        assert history[1][0] == "subtract"
        assert history[2][0] == "multiply"

    def test_history_preserves_order(self):
        """Test that history preserves operation order."""
        calc = Calculator()
        calc.add(1, 1)
        calc.add(2, 2)
        calc.add(3, 3)
        history = calc.get_history()
        assert history[0] == ("add", (1, 1), 2)
        assert history[1] == ("add", (2, 2), 4)
        assert history[2] == ("add", (3, 3), 6)

    def test_history_max_length_10(self):
        """Test that history is limited to 10 most recent operations."""
        calc = Calculator()
        for i in range(15):
            calc.add(i, 1)
        history = calc.get_history()
        assert len(history) == 10
        # First operation should be the 6th one (index 5)
        assert history[0] == ("add", (5, 1), 6)

    def test_history_clear(self):
        """Test clearing history."""
        calc = Calculator()
        calc.add(2, 3)
        calc.subtract(10, 5)
        assert len(calc.get_history()) == 2
        calc.clear_history()
        assert len(calc.get_history()) == 0

    def test_history_not_affected_by_errors(self):
        """Test that failed operations don't appear in history."""
        calc = Calculator()
        calc.add(2, 3)
        try:
            calc.divide(10, 0)
        except ValueError:
            pass
        history = calc.get_history()
        assert len(history) == 1
        assert history[0][0] == "add"

    def test_history_not_affected_by_type_errors(self):
        """Test that operations with type errors don't appear in history."""
        calc = Calculator()
        calc.add(2, 3)
        try:
            calc.add("bad", 5)
        except TypeError:
            pass
        history = calc.get_history()
        assert len(history) == 1
        assert history[0][0] == "add"

    def test_history_returns_copy(self):
        """Test that get_history returns a copy, not reference."""
        calc = Calculator()
        calc.add(2, 3)
        history1 = calc.get_history()
        calc.add(4, 5)
        history2 = calc.get_history()
        assert len(history1) == 1
        assert len(history2) == 2


class TestCalculatorState:
    """Tests for calculator state independence."""

    def test_multiple_instances_independent(self):
        """Test that multiple calculator instances have independent state."""
        calc1 = Calculator()
        calc2 = Calculator()

        calc1.add(2, 3)
        calc1.memory_store(100)

        calc2.add(5, 5)
        calc2.memory_store(200)

        assert calc1.memory_recall() == 100
        assert calc2.memory_recall() == 200
        assert len(calc1.get_history()) == 1
        assert len(calc2.get_history()) == 1
        assert calc1.get_history()[0][0] == "add"
        assert calc2.get_history()[0][0] == "add"

    def test_calculator_fresh_state(self):
        """Test that new calculator starts with clean state."""
        calc = Calculator()
        assert calc.memory_recall() is None
        assert len(calc.get_history()) == 0


class TestEdgeCases:
    """Tests for edge cases and special values."""

    def test_very_large_numbers(self):
        """Test calculator with very large numbers."""
        calc = Calculator()
        large = 10**100
        assert calc.add(large, large) == 2 * large

    def test_very_small_numbers(self):
        """Test calculator with very small numbers."""
        calc = Calculator()
        small = 1e-100
        assert pytest.approx(calc.add(small, small)) == 2 * small

    def test_floating_point_precision(self):
        """Test that floating point calculations are handled correctly."""
        calc = Calculator()
        result = calc.add(0.1, 0.2)
        assert pytest.approx(result) == 0.3

    def test_negative_zero(self):
        """Test handling of negative zero."""
        calc = Calculator()
        result = calc.subtract(0, 0)
        assert result == 0

    def test_divide_negative_by_zero_raises_error(self):
        """Test that dividing negative number by zero raises error."""
        calc = Calculator()
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            calc.divide(-5, 0)
