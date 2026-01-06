"""
Test Assignment Statement Transpilation

=============================================================================
WHAT THIS FILE TESTS
=============================================================================

Assignment statements: x = value

Covers:
- Simple variable assignment
- Different value types (int, float, str, bool, None)
- List, dict, tuple literals
- Nested data structures
- Expression assignments
- Chained assignments (a = b = 5)

=============================================================================
EXPECTED TRANSFORMATIONS
=============================================================================

Python                  → JavaScript
x = 5                   → let x = 5;
x = "hello"             → let x = "hello";
x = True                → let x = true;
x = None                → let x = null;
x = [1, 2, 3]           → let x = [1, 2, 3];
x = {"a": 1}            → let x = {"a": 1};
"""

import pytest
from pynext.transpiler import transpile, TranspileError


# =============================================================================
# BASIC INTEGER ASSIGNMENT
# =============================================================================

class TestIntegerAssignment:
    """Test assignment of integer values."""
    
    def test_assign_zero(self):
        """x = 0"""
        assert transpile("x = 0") == "let x = 0;"
    
    def test_assign_positive_int(self):
        """x = 5"""
        assert transpile("x = 5") == "let x = 5;"
    
    def test_assign_negative_int(self):
        """x = -5"""
        result = transpile("x = -5")
        assert result == "let x = (-5);" or result == "let x = -5;"
    
    def test_assign_large_int(self):
        """x = 1000000"""
        assert transpile("x = 1000000") == "let x = 1000000;"
    
    def test_assign_negative_large_int(self):
        """x = -999999"""
        result = transpile("x = -999999")
        assert result == "let x = (-999999);" or result == "let x = -999999;"
    
    def test_assign_binary_literal(self):
        """x = 0b1010"""
        # Python converts to int
        assert transpile("x = 0b1010") == "let x = 10;"
    
    def test_assign_hex_literal(self):
        """x = 0xff"""
        assert transpile("x = 0xff") == "let x = 255;"
    
    def test_assign_octal_literal(self):
        """x = 0o17"""
        assert transpile("x = 0o17") == "let x = 15;"


# =============================================================================
# FLOAT ASSIGNMENT
# =============================================================================

class TestFloatAssignment:
    """Test assignment of float values."""
    
    def test_assign_float(self):
        """x = 3.14"""
        assert transpile("x = 3.14") == "let x = 3.14;"
    
    def test_assign_negative_float(self):
        """x = -2.5"""
        result = transpile("x = -2.5")
        assert result == "let x = (-2.5);" or result == "let x = -2.5;"
    
    def test_assign_float_without_fraction(self):
        """x = 5.0"""
        assert transpile("x = 5.0") == "let x = 5.0;"
    
    def test_assign_small_float(self):
        """x = 0.001"""
        assert transpile("x = 0.001") == "let x = 0.001;"
    
    def test_assign_scientific_notation(self):
        """x = 1e10"""
        result = transpile("x = 1e10")
        assert "10000000000" in result or "1e" in result.lower()


# =============================================================================
# STRING ASSIGNMENT
# =============================================================================

class TestStringAssignment:
    """Test assignment of string values."""
    
    def test_assign_empty_string(self):
        """x = '' """
        assert transpile("x = ''") == 'let x = "";'
    
    def test_assign_simple_string(self):
        """x = "hello" """
        assert transpile('x = "hello"') == 'let x = "hello";'
    
    def test_assign_string_with_spaces(self):
        """x = "hello world" """
        assert transpile('x = "hello world"') == 'let x = "hello world";'
    
    def test_assign_string_with_numbers(self):
        """x = "abc123" """
        assert transpile('x = "abc123"') == 'let x = "abc123";'
    
    def test_assign_string_with_newline(self):
        """x = "line1\\nline2" """
        result = transpile('x = "line1\\nline2"')
        assert "\\n" in result
    
    def test_assign_string_with_tab(self):
        """x = "col1\\tcol2" """
        result = transpile('x = "col1\\tcol2"')
        assert "\\t" in result
    
    def test_assign_string_with_quotes(self):
        """x = 'he said "hi"' """
        result = transpile("x = 'he said \"hi\"'")
        assert "hi" in result


# =============================================================================
# BOOLEAN ASSIGNMENT
# =============================================================================

class TestBooleanAssignment:
    """Test assignment of boolean values."""
    
    def test_assign_true(self):
        """x = True"""
        assert transpile("x = True") == "let x = true;"
    
    def test_assign_false(self):
        """x = False"""
        assert transpile("x = False") == "let x = false;"


# =============================================================================
# NONE ASSIGNMENT
# =============================================================================

class TestNoneAssignment:
    """Test assignment of None."""
    
    def test_assign_none(self):
        """x = None"""
        assert transpile("x = None") == "let x = null;"


# =============================================================================
# LIST ASSIGNMENT
# =============================================================================

class TestListAssignment:
    """Test assignment of list literals."""
    
    def test_assign_empty_list(self):
        """x = []"""
        assert transpile("x = []") == "let x = [];"
    
    def test_assign_int_list(self):
        """x = [1, 2, 3]"""
        assert transpile("x = [1, 2, 3]") == "let x = [1, 2, 3];"
    
    def test_assign_string_list(self):
        """x = ["a", "b", "c"]"""
        assert transpile('x = ["a", "b", "c"]') == 'let x = ["a", "b", "c"];'
    
    def test_assign_mixed_list(self):
        """x = [1, "two", True]"""
        assert transpile('x = [1, "two", True]') == 'let x = [1, "two", true];'
    
    def test_assign_nested_list(self):
        """x = [[1, 2], [3, 4]]"""
        assert transpile("x = [[1, 2], [3, 4]]") == "let x = [[1, 2], [3, 4]];"
    
    def test_assign_list_with_none(self):
        """x = [None, None]"""
        assert transpile("x = [None, None]") == "let x = [null, null];"


# =============================================================================
# DICT ASSIGNMENT
# =============================================================================

class TestDictAssignment:
    """Test assignment of dict literals."""
    
    def test_assign_empty_dict(self):
        """x = {}"""
        assert transpile("x = {}") == "let x = {};"
    
    def test_assign_simple_dict(self):
        """x = {"a": 1}"""
        result = transpile('x = {"a": 1}')
        assert "a" in result and "1" in result
    
    def test_assign_multi_key_dict(self):
        """x = {"a": 1, "b": 2}"""
        result = transpile('x = {"a": 1, "b": 2}')
        assert "a" in result and "b" in result
    
    def test_assign_nested_dict(self):
        """x = {"outer": {"inner": 1}}"""
        result = transpile('x = {"outer": {"inner": 1}}')
        assert "outer" in result and "inner" in result
    
    def test_assign_dict_with_list_value(self):
        """x = {"items": [1, 2, 3]}"""
        result = transpile('x = {"items": [1, 2, 3]}')
        assert "items" in result and "[1, 2, 3]" in result


# =============================================================================
# TUPLE ASSIGNMENT
# =============================================================================

class TestTupleAssignment:
    """Test assignment of tuple literals."""
    
    def test_assign_empty_tuple(self):
        """x = ()"""
        assert transpile("x = ()") == "let x = [];"
    
    def test_assign_single_element_tuple(self):
        """x = (1,)"""
        assert transpile("x = (1,)") == "let x = [1];"
    
    def test_assign_tuple(self):
        """x = (1, 2, 3)"""
        assert transpile("x = (1, 2, 3)") == "let x = [1, 2, 3];"


# =============================================================================
# EXPRESSION ASSIGNMENT
# =============================================================================

class TestExpressionAssignment:
    """Test assignment of expression results."""
    
    def test_assign_addition(self):
        """x = 1 + 2"""
        result = transpile("x = 1 + 2")
        assert "1" in result and "2" in result and "+" in result
    
    def test_assign_multiplication(self):
        """x = 3 * 4"""
        result = transpile("x = 3 * 4")
        assert "3" in result and "4" in result and "*" in result
    
    def test_assign_function_call(self):
        """x = len(items)"""
        result = transpile("x = len(items)")
        assert "items.length" in result or "__py.len(items)" in result
    
    def test_assign_method_call(self):
        """x = s.lower()"""
        result = transpile("x = s.lower()")
        assert "toLowerCase" in result
    
    def test_assign_ternary(self):
        """x = a if cond else b"""
        result = transpile("x = a if cond else b")
        assert "?" in result and ":" in result


# =============================================================================
# VARIABLE NAMES
# =============================================================================

class TestVariableNames:
    """Test various variable naming patterns."""
    
    def test_single_letter(self):
        """x = 1"""
        assert transpile("x = 1") == "let x = 1;"
    
    def test_multi_letter(self):
        """count = 1"""
        assert transpile("count = 1") == "let count = 1;"
    
    def test_snake_case(self):
        """my_var = 1"""
        assert transpile("my_var = 1") == "let my_var = 1;"
    
    def test_camel_case(self):
        """myVar = 1"""
        assert transpile("myVar = 1") == "let myVar = 1;"
    
    def test_with_numbers(self):
        """var1 = 1"""
        assert transpile("var1 = 1") == "let var1 = 1;"
    
    def test_underscore_prefix(self):
        """_private = 1"""
        assert transpile("_private = 1") == "let _private = 1;"
    
    def test_double_underscore_prefix(self):
        """__dunder = 1"""
        assert transpile("__dunder = 1") == "let __dunder = 1;"


# =============================================================================
# EDGE CASES
# =============================================================================

class TestAssignmentEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_reassignment_to_same_variable(self):
        """Multiple assignments to same variable."""
        result = transpile("x = 1\nx = 2")
        assert result.count("let x") == 1  # Only first is let
        assert "x = 2" in result  # Second is reassignment
    
    def test_assign_variable_to_variable(self):
        """y = x"""
        assert transpile("y = x") == "let y = x;"
    
    def test_very_long_variable_name(self):
        """this_is_a_very_long_variable_name = 1"""
        name = "this_is_a_very_long_variable_name"
        assert transpile(f"{name} = 1") == f"let {name} = 1;"
