"""
Comprehensive pytest tests for the Calculator module.

Tests cover:
- Core operations (add, subtract, multiply, divide)
- Edge cases (zero, negative numbers, floats, large numbers)
- Error handling (division by zero, invalid types)
- Memory functions (store, recall, clear)
- History tracking (max 10 operations, order, content)
"""

import pytest
from calculator import Calculator


class TestBasicAddition:
    """Test cases for addition operations."""

    def test_add_two_positive_integers(self):
        """Test adding two positive integers."""
        calc = Calculator()
        assert calc.add(2, 3) == 5

    def test_add_two_negative_integers(self):
        """Test adding two negative integers."""
        calc = Calculator()
        assert calc.add(-5, -3) == -8

    def test_add_positive_and_negative(self):
        """Test adding positive and negative integers."""
        calc = Calculator()
        assert calc.add(10, -7) == 3

    def test_add_zeros(self):
        """Test adding zero to zero."""
        calc = Calculator()
        assert calc.add(0, 0) == 0

    def test_add_with_zero(self):
        """Test adding a number to zero."""
        calc = Calculator()
        assert calc.add(5, 0) == 5

    def test_add_floats(self):
        """Test adding two floats."""
        calc = Calculator()
        assert pytest.approx(calc.add(1.5, 2.5)) == 4.0

    def test_add_mixed_int_float(self):
        """Test adding integer and float."""
        calc = Calculator()
        assert pytest.approx(calc.add(5, 2.5)) == 7.5

    def test_add_large_numbers(self):
        """Test adding large numbers."""
        calc = Calculator()
        assert calc.add(1000000, 2000000) == 3000000

    def test_add_very_small_floats(self):
        """Test adding very small floats."""
        calc = Calculator()
        result = calc.add(0.0001, 0.0002)
        assert pytest.approx(result, abs=1e-6) == 0.0003


class TestBasicSubtraction:
    """Test cases for subtraction operations."""

    def test_subtract_two_positive_integers(self):
        """Test subtracting two positive integers."""
        calc = Calculator()
        assert calc.subtract(10, 3) == 7

    def test_subtract_two_negative_integers(self):
        """Test subtracting two negative integers."""
        calc = Calculator()
        assert calc.subtract(-5, -3) == -2

    def test_subtract_positive_from_smaller_positive(self):
        """Test subtracting larger from smaller (negative result)."""
        calc = Calculator()
        assert calc.subtract(3, 10) == -7

    def test_subtract_zeros(self):
        """Test subtracting zero from zero."""
        calc = Calculator()
        assert calc.subtract(0, 0) == 0

    def test_subtract_with_zero(self):
        """Test subtracting zero from a number."""
        calc = Calculator()
        assert calc.subtract(5, 0) == 5

    def test_subtract_floats(self):
        """Test subtracting two floats."""
        calc = Calculator()
        assert pytest.approx(calc.subtract(5.5, 2.3)) == 3.2

    def test_subtract_mixed_int_float(self):
        """Test subtracting float from integer."""
        calc = Calculator()
        assert pytest.approx(calc.subtract(10, 3.5)) == 6.5

    def test_subtract_large_numbers(self):
        """Test subtracting large numbers."""
        calc = Calculator()
        assert calc.subtract(2000000, 1000000) == 1000000


class TestBasicMultiplication:
    """Test cases for multiplication operations."""

    def test_multiply_two_positive_integers(self):
        """Test multiplying two positive integers."""
        calc = Calculator()
        assert calc.multiply(3, 4) == 12

    def test_multiply_two_negative_integers(self):
        """Test multiplying two negative integers."""
        calc = Calculator()
        assert calc.multiply(-3, -4) == 12

    def test_multiply_positive_and_negative(self):
        """Test multiplying positive and negative integers."""
        calc = Calculator()
        assert calc.multiply(-3, 4) == -12

    def test_multiply_by_zero(self):
        """Test multiplying by zero."""
        calc = Calculator()
        assert calc.multiply(100, 0) == 0

    def test_multiply_by_one(self):
        """Test multiplying by one."""
        calc = Calculator()
        assert calc.multiply(5, 1) == 5

    def test_multiply_floats(self):
        """Test multiplying two floats."""
        calc = Calculator()
        assert pytest.approx(calc.multiply(2.5, 4.0)) == 10.0

    def test_multiply_mixed_int_float(self):
        """Test multiplying integer and float."""
        calc = Calculator()
        assert pytest.approx(calc.multiply(3, 2.5)) == 7.5

    def test_multiply_large_numbers(self):
        """Test multiplying large numbers."""
        calc = Calculator()
        assert calc.multiply(1000, 2000) == 2000000

    def test_multiply_small_floats(self):
        """Test multiplying small floats."""
        calc = Calculator()
        result = calc.multiply(0.1, 0.2)
        assert pytest.approx(result, abs=1e-10) == 0.02


class TestBasicDivision:
    """Test cases for division operations."""

    def test_divide_two_positive_integers(self):
        """Test dividing two positive integers."""
        calc = Calculator()
        assert calc.divide(10, 2) == 5.0

    def test_divide_two_negative_integers(self):
        """Test dividing two negative integers."""
        calc = Calculator()
        assert calc.divide(-10, -2) == 5.0

    def test_divide_positive_by_negative(self):
        """Test dividing positive by negative."""
        calc = Calculator()
        assert calc.divide(10, -2) == -5.0

    def test_divide_zero_by_number(self):
        """Test dividing zero by a number."""
        calc = Calculator()
        assert calc.divide(0, 5) == 0.0

    def test_divide_by_one(self):
        """Test dividing by one."""
        calc = Calculator()
        assert calc.divide(5, 1) == 5.0

    def test_divide_floats(self):
        """Test dividing two floats."""
        calc = Calculator()
        assert pytest.approx(calc.divide(5.0, 2.0)) == 2.5

    def test_divide_mixed_int_float(self):
        """Test dividing integer by float."""
        calc = Calculator()
        assert pytest.approx(calc.divide(10, 2.5)) == 4.0

    def test_divide_by_fractional_number(self):
        """Test dividing by fractional number."""
        calc = Calculator()
        assert pytest.approx(calc.divide(1, 0.5)) == 2.0

    def test_divide_by_zero_raises_error(self):
        """Test that dividing by zero raises ValueError."""
        calc = Calculator()
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            calc.divide(10, 0)

    def test_divide_zero_by_zero_raises_error(self):
        """Test that dividing zero by zero raises ValueError."""
        calc = Calculator()
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            calc.divide(0, 0)

    def test_divide_negative_by_zero_raises_error(self):
        """Test that dividing negative by zero raises ValueError."""
        calc = Calculator()
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            calc.divide(-10, 0)


class TestTypeErrors:
    """Test cases for type error handling."""

    def test_add_string_and_number_raises_error(self):
        """Test that adding string and number raises TypeError."""
        calc = Calculator()
        with pytest.raises(TypeError):
            calc.add("5", 3)

    def test_add_none_and_number_raises_error(self):
        """Test that adding None and number raises TypeError."""
        calc = Calculator()
        with pytest.raises(TypeError):
            calc.add(None, 3)

    def test_subtract_string_and_number_raises_error(self):
        """Test that subtracting string and number raises TypeError."""
        calc = Calculator()
        with pytest.raises(TypeError):
            calc.subtract("5", 3)


    def test_divide_string_and_number_raises_error(self):
        """Test that dividing string and number raises TypeError."""
        calc = Calculator()
        with pytest.raises(TypeError):
            calc.divide("10", 2)

    def test_divide_number_by_string_raises_error(self):
        """Test that dividing number by string raises TypeError."""
        calc = Calculator()
        with pytest.raises(TypeError):
            calc.divide(10, "2")

    def test_memory_store_string_raises_error(self):
        """Test that storing string in memory raises TypeError."""
        calc = Calculator()
        with pytest.raises(TypeError):
            calc.memory_store("value")

    def test_memory_store_none_raises_error(self):
        """Test that storing None in memory raises TypeError."""
        calc = Calculator()
        with pytest.raises(TypeError):
            calc.memory_store(None)

    def test_memory_store_list_raises_error(self):
        """Test that storing list in memory raises TypeError."""
        calc = Calculator()
        with pytest.raises(TypeError):
            calc.memory_store([1, 2, 3])


class TestMemoryFunctions:
    """Test cases for memory functions."""

    def test_memory_store_and_recall_integer(self):
        """Test storing and recalling an integer."""
        calc = Calculator()
        calc.memory_store(42)
        assert calc.memory_recall() == 42

    def test_memory_store_and_recall_float(self):
        """Test storing and recalling a float."""
        calc = Calculator()
        calc.memory_store(3.14)
        assert pytest.approx(calc.memory_recall()) == 3.14

    def test_memory_store_zero(self):
        """Test storing zero in memory."""
        calc = Calculator()
        calc.memory_store(0)
        assert calc.memory_recall() == 0

    def test_memory_store_negative(self):
        """Test storing negative value in memory."""
        calc = Calculator()
        calc.memory_store(-99)
        assert calc.memory_recall() == -99

    def test_memory_recall_when_empty(self):
        """Test that recalling from empty memory returns None."""
        calc = Calculator()
        assert calc.memory_recall() is None

    def test_memory_overwrite(self):
        """Test that storing a new value overwrites the previous one."""
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

    def test_memory_clear_when_empty(self):
        """Test clearing memory when it's already empty."""
        calc = Calculator()
        calc.memory_clear()
        assert calc.memory_recall() is None


class TestHistoryTracking:
    """Test cases for operation history tracking."""

    def test_history_empty_on_initialization(self):
        """Test that history is empty when calculator is created."""
        calc = Calculator()
        assert calc.get_history() == []

    def test_history_records_single_operation(self):
        """Test that a single operation is recorded in history."""
        calc = Calculator()
        calc.add(2, 3)
        history = calc.get_history()
        assert len(history) == 1
        assert history[0]["operation"] == "add"
        assert history[0]["operand_a"] == 2
        assert history[0]["operand_b"] == 3
        assert history[0]["result"] == 5

    def test_history_records_multiple_operations(self):
        """Test that multiple operations are recorded in order."""
        calc = Calculator()
        calc.add(2, 3)
        calc.subtract(5, 1)
        calc.multiply(4, 2)
        history = calc.get_history()
        assert len(history) == 3
        assert history[0]["operation"] == "add"
        assert history[1]["operation"] == "subtract"
        assert history[2]["operation"] == "multiply"

    def test_history_max_length_ten(self):
        """Test that history only keeps the last 10 operations."""
        calc = Calculator()
        for i in range(15):
            calc.add(i, 1)
        history = calc.get_history()
        assert len(history) == 10

    def test_history_oldest_operations_removed(self):
        """Test that oldest operations are removed when history exceeds 10."""
        calc = Calculator()
        for i in range(15):
            calc.add(i, 0)
        history = calc.get_history()
        # First operation should be add(5, 0)=5, not add(0, 0)=0
        assert history[0]["operand_a"] == 5

    def test_history_records_all_operation_types(self):
        """Test that history records all operation types."""
        calc = Calculator()
        calc.add(1, 2)
        calc.subtract(5, 3)
        calc.multiply(2, 4)
        calc.divide(10, 2)
        history = calc.get_history()
        operations = [h["operation"] for h in history]
        assert operations == ["add", "subtract", "multiply", "divide"]

    def test_history_with_floats(self):
        """Test that history correctly records float operations."""
        calc = Calculator()
        calc.add(1.5, 2.5)
        history = calc.get_history()
        assert history[0]["operand_a"] == 1.5
        assert history[0]["operand_b"] == 2.5
        assert pytest.approx(history[0]["result"]) == 4.0

    def test_history_clear(self):
        """Test clearing history."""
        calc = Calculator()
        calc.add(1, 2)
        calc.subtract(5, 3)
        calc.clear_history()
        assert calc.get_history() == []

    def test_history_after_division_by_zero(self):
        """Test that failed operations don't get recorded in history."""
        calc = Calculator()
        calc.add(1, 2)
        with pytest.raises(ValueError):
            calc.divide(10, 0)
        history = calc.get_history()
        assert len(history) == 1
        assert history[0]["operation"] == "add"

    def test_history_after_type_error(self):
        """Test that type errors don't get recorded in history."""
        calc = Calculator()
        calc.add(1, 2)
        with pytest.raises(TypeError):
            calc.add("string", 3)
        history = calc.get_history()
        assert len(history) == 1
        assert history[0]["operation"] == "add"

    def test_history_integration_with_all_operations(self):
        """Test history with mixed successful operations."""
        calc = Calculator()
        calc.add(10, 20)
        calc.subtract(30, 5)
        calc.multiply(4, 5)
        calc.divide(100, 4)
        history = calc.get_history()
        assert len(history) == 4
        assert history[0]["result"] == 30
        assert history[1]["result"] == 25
        assert history[2]["result"] == 20
        assert pytest.approx(history[3]["result"]) == 25.0


class TestIntegration:
    """Integration tests combining multiple features."""

    def test_operations_independent_of_memory(self):
        """Test that operations work independently of memory."""
        calc = Calculator()
        calc.memory_store(100)
        result = calc.add(5, 3)
        assert result == 8
        assert calc.memory_recall() == 100

    def test_calculator_state_independence(self):
        """Test that multiple calculator instances are independent."""
        calc1 = Calculator()
        calc2 = Calculator()
        calc1.memory_store(10)
        calc2.memory_store(20)
        assert calc1.memory_recall() == 10
        assert calc2.memory_recall() == 20

    def test_sequential_operations_with_memory(self):
        """Test sequential operations while using memory."""
        calc = Calculator()
        result1 = calc.add(5, 3)
        calc.memory_store(result1)
        result2 = calc.multiply(result1, 2)
        assert calc.memory_recall() == 8
        assert result2 == 16

    def test_full_workflow(self):
        """Test a complete workflow using all features."""
        calc = Calculator()
        # Perform operations
        calc.add(10, 5)
        calc.subtract(20, 3)
        calc.multiply(4, 5)
        calc.divide(100, 4)
        # Store result in memory
        calc.memory_store(25.0)
        # Check memory
        assert calc.memory_recall() == 25.0
        # Check history
        history = calc.get_history()
        assert len(history) == 4
        # Clear memory
        calc.memory_clear()
        assert calc.memory_recall() is None
        # History should be unchanged
        assert len(history) == len(calc.get_history())

    def test_complex_calculation_sequence(self):
        """Test a complex sequence of calculations."""
        calc = Calculator()
        # (10 + 5) * 2 - 10 / 5
        result1 = calc.add(10, 5)  # 15
        result2 = calc.multiply(result1, 2)  # 30
        result3 = calc.divide(10, 5)  # 2.0
        result4 = calc.subtract(result2, result3)  # 28.0
        assert pytest.approx(result4) == 28.0
        # Verify history
        assert len(calc.get_history()) == 4

    def test_error_recovery(self):
        """Test that calculator can recover after an error."""
        calc = Calculator()
        calc.add(5, 3)
        with pytest.raises(ValueError):
            calc.divide(10, 0)
        # Should still work after error
        result = calc.add(2, 2)
        assert result == 4
        assert len(calc.get_history()) == 2
