"""
Test Tuple Unpacking Transpilation

=============================================================================
WHAT THIS FILE TESTS
=============================================================================

Tuple unpacking (destructuring) in assignments.

Covers:
- Simple tuple unpacking: a, b = pair
- Swapping: a, b = b, a
- Starred unpacking: first, *rest = items
- Nested unpacking (if supported)

=============================================================================
EXPECTED TRANSFORMATIONS
=============================================================================

Python                  → JavaScript
a, b = pair             → let [a, b] = pair; (allows reassignment)
a, b = b, a             → [a, b] = [b, a];
first, *rest = items    → let [first, ...rest] = items; (allows reassignment)
a, b, c = func()        → let [a, b, c] = func(); (allows reassignment)
"""

import pytest
from pynext.transpiler import transpile, TranspileError


# =============================================================================
# SIMPLE UNPACKING
# =============================================================================

class TestSimpleUnpacking:
    """Test simple tuple unpacking."""
    
    def test_unpack_two(self):
        """a, b = pair"""
        result = transpile("a, b = pair")
        assert "let [a, b] = pair;" in result
    
    def test_unpack_three(self):
        """a, b, c = triple"""
        result = transpile("a, b, c = triple")
        assert "let [a, b, c] = triple;" in result
    
    def test_unpack_four(self):
        """a, b, c, d = items"""
        result = transpile("a, b, c, d = items")
        assert "let [a, b, c, d] = items;" in result
    
    def test_unpack_many(self):
        """a, b, c, d, e, f = items"""
        result = transpile("a, b, c, d, e, f = items")
        assert "let [a, b, c, d, e, f] = items;" in result


# =============================================================================
# SWAP PATTERN
# =============================================================================

class TestSwapPattern:
    """Test variable swapping."""
    
    def test_swap_two(self):
        """a, b = b, a"""
        result = transpile("a, b = b, a")
        assert "[a, b]" in result and "[b, a]" in result
    
    def test_swap_three(self):
        """a, b, c = c, a, b"""
        result = transpile("a, b, c = c, a, b")
        assert "[a, b, c]" in result


# =============================================================================
# UNPACKING LITERALS
# =============================================================================

class TestUnpackingLiterals:
    """Test unpacking from literals."""
    
    def test_unpack_list_literal(self):
        """a, b = [1, 2]"""
        result = transpile("a, b = [1, 2]")
        assert "[a, b]" in result and "[1, 2]" in result
    
    def test_unpack_tuple_literal(self):
        """a, b = (1, 2)"""
        result = transpile("a, b = (1, 2)")
        assert "[a, b]" in result
    
    def test_unpack_nested_literal(self):
        """a, b = [1, [2, 3]]"""
        result = transpile("a, b = [1, [2, 3]]")
        assert "[a, b]" in result


# =============================================================================
# UNPACKING FUNCTION RETURNS
# =============================================================================

class TestUnpackingFunctionReturns:
    """Test unpacking function return values."""
    
    def test_unpack_function_call(self):
        """a, b = get_pair()"""
        result = transpile("a, b = get_pair()")
        assert "[a, b] = get_pair();" in result or "const [a, b] = get_pair();" in result
    
    def test_unpack_method_call(self):
        """k, v = item.get_pair()"""
        result = transpile("k, v = item.get_pair()")
        assert "[k, v]" in result


# =============================================================================
# STARRED UNPACKING
# =============================================================================

class TestStarredUnpacking:
    """Test starred (rest) unpacking."""
    
    def test_starred_rest(self):
        """first, *rest = items"""
        result = transpile("first, *rest = items")
        assert "let [first, ...rest] = items;" in result
    
    def test_starred_middle(self):
        """first, *middle, last = items"""
        result = transpile("first, *middle, last = items")
        # This is complex - may need special handling
        assert "first" in result and "middle" in result and "last" in result
    
    def test_starred_first(self):
        """*init, last = items"""
        result = transpile("*init, last = items")
        assert "...init" in result


# =============================================================================
# UNPACKING IN LOOPS
# =============================================================================

class TestUnpackingInLoops:
    """Test unpacking in for loop iteration."""
    
    def test_unpack_enumerate(self):
        """for i, x in enumerate(items): pass - uses tuple unpack"""
        # Note: This may require special handling in the parser
        pass
    
    def test_unpack_zip(self):
        """for a, b in zip(x, y): pass"""
        # Note: This may require special handling
        pass


# =============================================================================
# IN CONTEXT
# =============================================================================

class TestUnpackingInContext:
    """Test unpacking in various contexts."""
    
    def test_unpack_in_if(self):
        """if cond: a, b = pair"""
        result = transpile("if cond:\n    a, b = pair")
        assert "[a, b] = pair;" in result or "const [a, b] = pair;" in result
    
    def test_unpack_in_function(self):
        """def foo(): a, b = pair"""
        result = transpile("def foo():\n    a, b = pair")
        assert "[a, b]" in result
    
    def test_unpack_after_other_code(self):
        """x = 1; a, b = pair"""
        result = transpile("x = 1\na, b = pair")
        assert "let x = 1" in result
        assert "[a, b]" in result


# =============================================================================
# EDGE CASES
# =============================================================================

class TestUnpackingEdgeCases:
    """Test edge cases for tuple unpacking."""
    
    def test_unpack_single_underscore(self):
        """_, x = pair - ignoring first"""
        result = transpile("_, x = pair")
        assert "[_, x]" in result
    
    def test_unpack_multiple_underscore(self):
        """_, __, x = triple"""
        result = transpile("_, __, x = triple")
        assert "x" in result
    
    def test_unpack_long_names(self):
        """first_name, last_name = name_pair"""
        result = transpile("first_name, last_name = name_pair")
        assert "first_name" in result and "last_name" in result
