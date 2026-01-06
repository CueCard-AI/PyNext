"""
Test Expression Transpilation

=============================================================================
WHAT THIS FILE TESTS
=============================================================================

Various expression types.

Covers:
- Binary operations (+, -, *, /, //, %, **)
- Unary operations (-, +, not, ~)
- Comparisons (==, !=, <, >, <=, >=, is, in)
- Boolean operations (and, or)
- Conditional expressions (ternary)
- Function calls
- Method calls
- Attribute access

=============================================================================
EXPECTED TRANSFORMATIONS
=============================================================================

Python                  → JavaScript
a + b                   → (a + b)
a // b                  → __py.floordiv(a, b)
a % b                   → __py.mod(a, b)
not x                   → !__py.bool(x)
a == b                  → __py.eq(a, b)
x in items              → __py.in(x, items)
a if cond else b        → (cond ? a : b)
"""

import pytest
from pynext.transpiler import transpile, transpile_expression, TranspileError
from tests.unit.transpiler.test_utils import assert_has_runtime_function


# =============================================================================
# BINARY OPERATORS
# =============================================================================

class TestBinaryOperators:
    """Test binary operators."""
    
    def test_add(self):
        """a + b → __py.dunders.add for potential list/string concat"""
        result = transpile("x = a + b")
        assert_has_runtime_function(result, "add")
    
    def test_subtract(self):
        """a - b → __py.dunders.sub"""
        result = transpile("x = a - b")
        assert_has_runtime_function(result, "sub")
    
    def test_multiply(self):
        """a * b → __py.dunders.mul for potential string/list repeat"""
        result = transpile("x = a * b")
        assert_has_runtime_function(result, "mul")
    
    def test_divide(self):
        """a / b → __py.dunders.truediv"""
        result = transpile("x = a / b")
        assert_has_runtime_function(result, "truediv")
    
    def test_floor_divide(self):
        """a // b → __py.floordiv"""
        result = transpile("x = a // b")
        assert_has_runtime_function(result, "floordiv")
    
    def test_modulo(self):
        """a % b → __py.mod"""
        result = transpile("x = a % b")
        assert_has_runtime_function(result, "mod")
    
    def test_power(self):
        """a ** b → __py.pow for Phase 33.2 dunder support"""
        result = transpile("x = a ** b")
        assert_has_runtime_function(result, "pow")
    
    def test_bitwise_and(self):
        """a & b → __py.dunders.bitand"""
        result = transpile("x = a & b")
        assert_has_runtime_function(result, "bitand")
    
    def test_bitwise_or(self):
        """a | b → __py.dunders.bitor"""
        result = transpile("x = a | b")
        assert_has_runtime_function(result, "bitor")
    
    def test_bitwise_xor(self):
        """a ^ b → __py.dunders.bitxor"""
        result = transpile("x = a ^ b")
        assert_has_runtime_function(result, "bitxor")
    
    def test_left_shift(self):
        """a << b → __py.dunders.lshift"""
        result = transpile("x = a << b")
        assert_has_runtime_function(result, "lshift")
    
    def test_right_shift(self):
        """a >> b → __py.dunders.rshift"""
        result = transpile("x = a >> b")
        assert_has_runtime_function(result, "rshift")


# =============================================================================
# STRING OPERATIONS
# =============================================================================

class TestStringOperations:
    """Test string-specific operations."""
    
    def test_string_repeat(self):
        """"a" * 3 → "a".repeat(3)"""
        result = transpile('x = "a" * 3')
        assert ".repeat(3)" in result
    
    def test_string_concatenation(self):
        """"hello" + "world" → __py.dunders.add for string concat"""
        result = transpile('x = "hello" + "world"')
        assert '"hello"' in result and '"world"' in result
        assert_has_runtime_function(result, "add")


# =============================================================================
# UNARY OPERATORS
# =============================================================================

class TestUnaryOperators:
    """Test unary operators."""
    
    def test_negate(self):
        """-x → __py.dunders.neg"""
        result = transpile("x = -y")
        assert_has_runtime_function(result, "neg")
    
    def test_positive(self):
        """+x → __py.dunders.pos"""
        result = transpile("x = +y")
        assert_has_runtime_function(result, "pos")
    
    def test_not(self):
        """not x → !__py.bool(x)"""
        result = transpile("x = not y")
        assert_has_runtime_function(result, "bool")
    
    def test_bitwise_not(self):
        """~x"""
        result = transpile("x = ~y")
        assert "~y" in result


# =============================================================================
# COMPARISON OPERATORS
# =============================================================================

class TestComparisonOperators:
    """Test comparison operators."""
    
    def test_equal(self):
        """a == b → __py.eq for deep equality"""
        result = transpile("x = a == b")
        assert "__py.eq" in result
    
    def test_not_equal(self):
        """a != b → !__py.eq for deep equality"""
        result = transpile("x = a != b")
        assert_has_runtime_function(result, "eq")
    
    def test_less_than(self):
        """a < b"""
        result = transpile("x = a < b")
        assert "<" in result
    
    def test_less_equal(self):
        """a <= b"""
        result = transpile("x = a <= b")
        assert "<=" in result
    
    def test_greater_than(self):
        """a > b"""
        result = transpile("x = a > b")
        assert ">" in result
    
    def test_greater_equal(self):
        """a >= b"""
        result = transpile("x = a >= b")
        assert ">=" in result
    
    def test_is_none(self):
        """x is None → x === null"""
        result = transpile("x = y is None")
        assert "=== null" in result
    
    def test_is_not_none(self):
        """x is not None → x !== null"""
        result = transpile("x = y is not None")
        assert "!== null" in result
    
    def test_in_list(self):
        """x in items → __py.in"""
        result = transpile("x = y in items")
        assert_has_runtime_function(result, "in")
    
    def test_not_in_list(self):
        """x not in items → !__py.in"""
        result = transpile("x = y not in items")
        assert_has_runtime_function(result, "in")


# =============================================================================
# CHAINED COMPARISONS
# =============================================================================

class TestChainedComparisons:
    """Test chained comparisons."""
    
    def test_range_check(self):
        """0 < x < 10"""
        result = transpile("x = 0 < y < 10")
        assert "&&" in result or "0 < y" in result
    
    def test_triple_check(self):
        """a < b < c < d"""
        result = transpile("x = a < b < c < d")
        assert "&&" in result


# =============================================================================
# BOOLEAN OPERATORS
# =============================================================================

class TestBooleanOperators:
    """Test boolean operators."""
    
    def test_and(self):
        """a and b"""
        result = transpile("x = a and b")
        assert "__py.bool" in result or ("a" in result and "b" in result)
    
    def test_or(self):
        """a or b"""
        result = transpile("x = a or b")
        assert "__py.bool" in result or ("a" in result and "b" in result)
    
    def test_and_chain(self):
        """a and b and c"""
        result = transpile("x = a and b and c")
        assert "a" in result and "b" in result and "c" in result
    
    def test_or_chain(self):
        """a or b or c"""
        result = transpile("x = a or b or c")
        assert "a" in result and "b" in result and "c" in result


# =============================================================================
# CONDITIONAL EXPRESSION
# =============================================================================

class TestConditionalExpression:
    """Test conditional (ternary) expressions."""
    
    def test_simple_ternary(self):
        """a if cond else b → cond ? a : b"""
        result = transpile("x = a if cond else b")
        assert "?" in result and ":" in result
    
    def test_ternary_with_values(self):
        """1 if x else 0"""
        result = transpile("x = 1 if cond else 0")
        assert "1" in result and "0" in result
    
    def test_nested_ternary(self):
        """a if x else (b if y else c)"""
        result = transpile("x = a if p else (b if q else c)")
        assert result.count("?") == 2


# =============================================================================
# FUNCTION CALLS
# =============================================================================

class TestFunctionCalls:
    """Test function call transpilation."""
    
    def test_no_args(self):
        """foo()"""
        result = transpile("foo()")
        assert "foo()" in result
    
    def test_single_arg(self):
        """foo(x)"""
        result = transpile("foo(x)")
        assert "foo(x)" in result
    
    def test_multiple_args(self):
        """foo(a, b, c)"""
        result = transpile("foo(a, b, c)")
        assert "foo(a, b, c)" in result


# =============================================================================
# BUILTIN FUNCTIONS
# =============================================================================

class TestBuiltinFunctions:
    """Test Python builtin function transpilation."""
    
    def test_len(self):
        """len(items) → items.length"""
        result = transpile("x = len(items)")
        assert "items.length" in result or "__py.len(items)" in result
    
    def test_str(self):
        """str(x) → __py.str(x) for dunder method support"""
        result = transpile("x = str(y)")
        assert "__py.str(y)" in result
    
    def test_int(self):
        """int(x) → parseInt(x)"""
        result = transpile("x = int(y)")
        assert "parseInt(y)" in result
    
    def test_float(self):
        """float(x) → parseFloat(x)"""
        result = transpile("x = float(y)")
        assert "parseFloat(y)" in result
    
    def test_abs(self):
        """abs(x) → __py.abs(x)"""
        result = transpile("x = abs(y)")
        assert "__py.abs(y)" in result
    
    def test_min(self):
        """min(a, b) → __py.min([a, b], null) for type checking"""
        result = transpile("x = min(a, b)")
        assert "__py.min" in result
    
    def test_max(self):
        """max(a, b) → __py.max([a, b], null) for type checking"""
        result = transpile("x = max(a, b)")
        assert "__py.max" in result
    
    def test_print(self):
        """print(x) → __py.print(x) for proper string conversion"""
        result = transpile("print(x)")
        assert "__py.print(x)" in result


# =============================================================================
# METHOD CALLS
# =============================================================================

class TestMethodCalls:
    """Test method call transpilation."""
    
    def test_string_lower(self):
        """s.lower() → s.toLowerCase()"""
        result = transpile("x = s.lower()")
        assert "toLowerCase()" in result
    
    def test_string_upper(self):
        """s.upper() → s.toUpperCase()"""
        result = transpile("x = s.upper()")
        assert "toUpperCase()" in result
    
    def test_string_strip(self):
        """s.strip() → s.trim()"""
        result = transpile("x = s.strip()")
        assert "trim()" in result
    
    def test_list_append(self):
        """items.append(x) → items.push(x)"""
        result = transpile("items.append(x)")
        assert "push(x)" in result
    
    def test_dict_keys(self):
        """d.keys() → Object.keys(d)"""
        result = transpile("x = d.keys()")
        assert "Object.keys(d)" in result
    
    def test_dict_values(self):
        """d.values() → Object.values(d)"""
        result = transpile("x = d.values()")
        assert "Object.values(d)" in result
    
    def test_dict_items(self):
        """d.items() → __py.dict.items(d)"""
        result = transpile("x = d.items()")
        assert "__py.dict.items(d)" in result


# =============================================================================
# ATTRIBUTE ACCESS
# =============================================================================

class TestAttributeAccess:
    """Test attribute access transpilation."""
    
    def test_simple_attribute(self):
        """obj.attr"""
        result = transpile("x = obj.attr")
        assert "obj.attr" in result
    
    def test_nested_attribute(self):
        """obj.inner.attr"""
        result = transpile("x = obj.inner.attr")
        assert "obj.inner.attr" in result
    
    def test_attribute_of_call(self):
        """func().attr"""
        result = transpile("x = func().attr")
        assert "func().attr" in result
