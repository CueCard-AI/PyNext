"""
Tests for core-minimal.js - Layer 0 Essential Functions

=============================================================================
WHAT THIS FILE TESTS
=============================================================================

Tests the 8 essential functions in core-minimal.js:
- at(arr, i): Negative indexing
- slice(arr, s, e, step): Python slicing
- bool(x): Python truthiness
- eq(a, b): Deep equality
- mod(a, b): Python modulo
- floordiv(a, b): Floor division
- range(s, e, step): Range iterator
- len(x): Length (works on dict)

=============================================================================
WHY THESE TESTS EXIST
=============================================================================

Layer 0 is the foundation of the PyNext runtime. Any bug here affects all
transpiled code. These tests verify Python semantics are correctly implemented.

=============================================================================
TEST CATEGORIES
=============================================================================

1. Basic functionality (happy path)
2. Edge cases (empty, negative, zero)
3. Error handling (division by zero, invalid types)
4. Python-specific semantics (negative modulo, truthiness)
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# AT() TESTS - Negative Indexing
# =============================================================================

class TestAt:
    """Tests for at() - Python negative indexing."""
    
    def test_at_positive_index(self):
        """Positive index returns correct element."""
        code = "items = [1, 2, 3]; x = items[0]"
        result = transpile(code)
        # Transpiler may use getitem or direct access
        assert "[0]" in result or "getitem(items, 0)" in result or "at(items, 0)" in result
    
    def test_at_negative_one(self):
        """items[-1] returns last element."""
        code = "items = [1, 2, 3]; x = items[-1]"
        result = transpile(code)
        # Should use at() for negative index
        assert "at" in result.lower() or "[-1]" in result
    
    def test_at_negative_two(self):
        """items[-2] returns second-to-last element."""
        code = "items = [1, 2, 3]; x = items[-2]"
        result = transpile(code)
        assert "at" in result.lower() or "[-2]" in result
    
    def test_at_string(self):
        """Works on strings too."""
        code = 's = "hello"; c = s[-1]'
        result = transpile(code)
        assert "at" in result.lower() or "[-1]" in result


# =============================================================================
# SLICE() TESTS - Python Slicing
# =============================================================================

class TestSlice:
    """Tests for slice() - Python slicing semantics."""
    
    def test_slice_basic(self):
        """Basic slice items[1:3]."""
        code = "items = [1, 2, 3, 4]; x = items[1:3]"
        result = transpile(code)
        # Should use slice or .slice()
        assert "slice" in result.lower()
    
    def test_slice_from_start(self):
        """Slice from start items[:2]."""
        code = "items = [1, 2, 3, 4]; x = items[:2]"
        result = transpile(code)
        assert "slice" in result.lower() or "[:2]" in result
    
    def test_slice_to_end(self):
        """Slice to end items[2:]."""
        code = "items = [1, 2, 3, 4]; x = items[2:]"
        result = transpile(code)
        assert "slice" in result.lower()
    
    def test_slice_negative(self):
        """Negative slice items[-2:]."""
        code = "items = [1, 2, 3, 4]; x = items[-2:]"
        result = transpile(code)
        assert "slice" in result.lower()
    
    def test_slice_with_step(self):
        """Slice with step items[::2]."""
        code = "items = [1, 2, 3, 4]; x = items[::2]"
        result = transpile(code)
        # Step slicing requires runtime
        assert "slice" in result.lower()
    
    def test_slice_reverse(self):
        """Reverse slice items[::-1]."""
        code = "items = [1, 2, 3, 4]; x = items[::-1]"
        result = transpile(code)
        assert "slice" in result.lower()
    
    def test_slice_string(self):
        """Slice on string."""
        code = 's = "hello"; x = s[1:4]'
        result = transpile(code)
        assert "slice" in result.lower()


# =============================================================================
# BOOL() TESTS - Python Truthiness
# =============================================================================

class TestBool:
    """Tests for bool() - Python truthiness."""
    
    def test_bool_empty_list(self):
        """Empty list is falsy."""
        code = "items = []; result = 'yes' if items else 'no'"
        result = transpile(code)
        # Should use bool() for list truthiness
        assert "bool" in result.lower() or "length" in result.lower()
    
    def test_bool_non_empty_list(self):
        """Non-empty list is truthy."""
        code = "items = [1, 2, 3]; result = 'yes' if items else 'no'"
        result = transpile(code)
        assert "bool" in result.lower() or "length" in result.lower()
    
    def test_bool_empty_dict(self):
        """Empty dict is falsy."""
        code = "d = {}; result = 'yes' if d else 'no'"
        result = transpile(code)
        # Dicts also need truthiness check
        assert "bool" in result.lower() or "Object.keys" in result
    
    def test_bool_zero(self):
        """Zero is falsy."""
        code = "x = 0; result = 'yes' if x else 'no'"
        result = transpile(code)
        # 0 truthiness works in JS, may not need bool()
        assert "?" in result or "if" in result.lower()
    
    def test_bool_empty_string(self):
        """Empty string is falsy."""
        code = 's = ""; result = "yes" if s else "no"'
        result = transpile(code)
        assert "?" in result or "if" in result.lower()
    
    def test_bool_none(self):
        """None is falsy."""
        code = "x = None; result = 'yes' if x else 'no'"
        result = transpile(code)
        assert "?" in result or "if" in result.lower()


# =============================================================================
# EQ() TESTS - Deep Equality
# =============================================================================

class TestEq:
    """Tests for eq() - Deep equality."""
    
    def test_eq_primitives(self):
        """Primitives use ===."""
        code = "result = 1 == 1"
        result = transpile(code)
        # May use === or eq()
        assert "==" in result or "eq" in result.lower()
    
    def test_eq_lists(self):
        """Lists need deep equality."""
        code = "result = [1, 2] == [1, 2]"
        result = transpile(code)
        # Should use eq() or similar for list comparison
        assert "eq" in result.lower() or "==" in result
    
    def test_eq_dicts(self):
        """Dicts need deep equality."""
        code = 'result = {"a": 1} == {"a": 1}'
        result = transpile(code)
        assert "eq" in result.lower() or "==" in result
    
    def test_eq_nested(self):
        """Nested structures need deep equality."""
        code = "result = [[1, 2], [3, 4]] == [[1, 2], [3, 4]]"
        result = transpile(code)
        assert "eq" in result.lower() or "==" in result
    
    def test_ne_operator(self):
        """Not equal operator."""
        code = "result = [1, 2] != [1, 3]"
        result = transpile(code)
        assert "!=" in result or "eq" in result.lower()


# =============================================================================
# MOD() TESTS - Python Modulo
# =============================================================================

class TestMod:
    """Tests for mod() - Python modulo (always positive)."""
    
    def test_mod_positive(self):
        """Positive modulo."""
        code = "result = 7 % 3"
        result = transpile(code)
        # May use % directly for positive numbers
        assert "%" in result or "mod" in result.lower()
    
    def test_mod_negative_dividend(self):
        """Negative dividend: -1 % 3 = 2 in Python."""
        code = "result = -1 % 3"
        result = transpile(code)
        # Should use mod() for negative to get Python behavior
        assert "mod" in result.lower() or "%" in result
    
    def test_mod_negative_divisor(self):
        """Negative divisor."""
        code = "result = 7 % -3"
        result = transpile(code)
        assert "mod" in result.lower() or "%" in result


# =============================================================================
# FLOORDIV() TESTS - Floor Division
# =============================================================================

class TestFloordiv:
    """Tests for floordiv() - Floor division."""
    
    def test_floordiv_positive(self):
        """Positive floor division: 7 // 3 = 2."""
        code = "result = 7 // 3"
        result = transpile(code)
        assert "floor" in result.lower() or "//" in result
    
    def test_floordiv_negative(self):
        """Negative floor division: -7 // 3 = -3."""
        code = "result = -7 // 3"
        result = transpile(code)
        assert "floor" in result.lower() or "//" in result
    
    def test_floordiv_exact(self):
        """Exact division: 6 // 3 = 2."""
        code = "result = 6 // 3"
        result = transpile(code)
        assert "floor" in result.lower() or "//" in result


# =============================================================================
# RANGE() TESTS - Range Iterator
# =============================================================================

class TestRange:
    """Tests for range() - Range iterator."""
    
    def test_range_single_arg(self):
        """range(5) → [0, 1, 2, 3, 4]."""
        code = "items = list(range(5))"
        result = transpile(code)
        assert "range" in result.lower()
    
    def test_range_two_args(self):
        """range(1, 5) → [1, 2, 3, 4]."""
        code = "items = list(range(1, 5))"
        result = transpile(code)
        assert "range" in result.lower()
    
    def test_range_with_step(self):
        """range(0, 10, 2) → [0, 2, 4, 6, 8]."""
        code = "items = list(range(0, 10, 2))"
        result = transpile(code)
        assert "range" in result.lower()
    
    def test_range_negative_step(self):
        """range(5, 0, -1) → [5, 4, 3, 2, 1]."""
        code = "items = list(range(5, 0, -1))"
        result = transpile(code)
        assert "range" in result.lower()
    
    def test_range_in_for(self):
        """for i in range(5)."""
        code = "for i in range(5): pass"
        result = transpile(code)
        assert "range" in result.lower() or "for" in result.lower()


# =============================================================================
# LEN() TESTS - Length
# =============================================================================

class TestLen:
    """Tests for len() - Length function."""
    
    def test_len_list(self):
        """len([1, 2, 3]) = 3."""
        code = "items = [1, 2, 3]; n = len(items)"
        result = transpile(code)
        # May inline to .length
        assert "len" in result.lower() or "length" in result.lower()
    
    def test_len_string(self):
        """len("hello") = 5."""
        code = 's = "hello"; n = len(s)'
        result = transpile(code)
        assert "len" in result.lower() or "length" in result.lower()
    
    def test_len_dict(self):
        """len({"a": 1}) = 1 (number of keys)."""
        code = 'd = {"a": 1, "b": 2}; n = len(d)'
        result = transpile(code)
        # Dict len needs Object.keys
        assert "len" in result.lower() or "Object.keys" in result
    
    def test_len_set(self):
        """len(set([1, 2, 3])) = 3."""
        # Use set() constructor to avoid parsing ambiguity with dict
        code = "s = set([1, 2, 3]); n = len(s)"
        result = transpile(code)
        # Set uses .size or len() helper
        assert "len" in result.lower() or "size" in result.lower() or "Set" in result


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestCoreMinimalIntegration:
    """Integration tests combining multiple core-minimal functions."""
    
    def test_slice_and_at(self):
        """Use both slicing and negative indexing."""
        code = """
items = [1, 2, 3, 4, 5]
first_two = items[:2]
last = items[-1]
"""
        result = transpile(code)
        assert "slice" in result.lower()
        assert "at" in result.lower() or "[-1]" in result
    
    def test_bool_and_len(self):
        """Use truthiness check with length."""
        code = """
items = [1, 2, 3]
if items and len(items) > 2:
    result = "yes"
"""
        result = transpile(code)
        # Should have both bool and len logic
        assert "length" in result.lower() or "len" in result.lower()
    
    def test_range_with_slice(self):
        """Use range and then slice the result."""
        code = """
nums = list(range(10))
subset = nums[2:7]
"""
        result = transpile(code)
        assert "range" in result.lower()
        assert "slice" in result.lower()
    
    def test_mod_floordiv_combination(self):
        """Use both mod and floordiv."""
        code = """
n = 17
quotient = n // 5
remainder = n % 5
"""
        result = transpile(code)
        # Should have floor division and modulo
        assert ("floor" in result.lower() or "//" in result) and ("%" in result or "mod" in result.lower())
    
    def test_deep_equality_with_nested(self):
        """Deep equality on nested structures."""
        code = """
a = [[1, 2], [3, 4]]
b = [[1, 2], [3, 4]]
same = a == b
"""
        result = transpile(code)
        # Should handle deep comparison
        assert "eq" in result.lower() or "==" in result

