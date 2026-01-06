"""
Test For Loop Transpilation

=============================================================================
WHAT THIS FILE TESTS
=============================================================================

For loops including range-based iteration.

Covers:
- Simple for-in loops
- For loops with range()
- Range with start, stop, step
- Nested for loops
- Break and continue in loops
- Iterating over lists, dicts, strings

=============================================================================
EXPECTED TRANSFORMATIONS
=============================================================================

Python                          → JavaScript
for x in items:                 → for (const x of items) {
    print(x)                    →     console.log(x);
                                → }

for i in range(10):             → for (let i = 0; i < 10; i++) {
    print(i)                    →     console.log(i);
                                → }

for i in range(1, 10):          → for (let i = 1; i < 10; i++) {
    print(i)                    →     console.log(i);
                                → }

for i in range(0, 10, 2):       → for (let i = 0; i < 10; i += 2) {
    print(i)                    →     console.log(i);
                                → }
"""

import pytest
from pynext.transpiler import transpile, TranspileError


# =============================================================================
# SIMPLE FOR-IN
# =============================================================================

class TestSimpleForIn:
    """Test basic for-in loops."""
    
    def test_for_in_list(self):
        """for x in items: pass → uses __py.iter for dict support"""
        result = transpile("for x in items:\n    pass")
        assert "for (const x of __py.iter(items))" in result
    
    def test_for_in_with_body(self):
        """for x in items: print(x) → uses __py.iter and __py.print"""
        result = transpile("for x in items:\n    print(x)")
        assert "for (const x of __py.iter(items))" in result
        assert "__py.print(x)" in result
    
    def test_for_in_multiple_statements(self):
        """for x in items: a(); b()"""
        result = transpile("for x in items:\n    a()\n    b()")
        assert "a()" in result
        assert "b()" in result
    
    def test_for_in_string(self):
        """for char in "hello": pass"""
        result = transpile('for char in "hello":\n    pass')
        assert "for (const char of" in result


# =============================================================================
# FOR WITH RANGE
# =============================================================================

class TestForRange:
    """Test for loops with range()."""
    
    def test_range_single_arg(self):
        """for i in range(10): pass"""
        result = transpile("for i in range(10):\n    pass")
        assert "for (let i = 0; i < 10; i++)" in result
    
    def test_range_two_args(self):
        """for i in range(5, 10): pass"""
        result = transpile("for i in range(5, 10):\n    pass")
        assert "for (let i = 5; i < 10; i++)" in result
    
    def test_range_three_args(self):
        """for i in range(0, 10, 2): pass"""
        result = transpile("for i in range(0, 10, 2):\n    pass")
        assert "i += 2" in result
    
    def test_range_negative_step(self):
        """for i in range(10, 0, -1): pass"""
        result = transpile("for i in range(10, 0, -1):\n    pass")
        assert "i > 0" in result or "i > " in result
    
    def test_range_with_variable(self):
        """for i in range(n): pass"""
        result = transpile("for i in range(n):\n    pass")
        assert "i < n" in result
    
    def test_range_zero(self):
        """for i in range(0): pass (empty loop)"""
        result = transpile("for i in range(0):\n    pass")
        assert "i < 0" in result


# =============================================================================
# FOR WITH DICT
# =============================================================================

class TestForDict:
    """Test for loops iterating over dictionaries."""
    
    def test_for_in_dict_keys(self):
        """for k in d.keys(): pass"""
        result = transpile("for k in d.keys():\n    pass")
        assert "Object.keys(d)" in result
    
    def test_for_in_dict_values(self):
        """for v in d.values(): pass"""
        result = transpile("for v in d.values():\n    pass")
        assert "Object.values(d)" in result
    
    def test_for_in_dict_items(self):
        """for k, v in d.items(): pass - handled as tuple unpack"""
        # This would need tuple unpacking support
        pass


# =============================================================================
# NESTED FOR
# =============================================================================

class TestNestedFor:
    """Test nested for loops."""
    
    def test_nested_for_in(self):
        """for x in a: for y in b: pass"""
        result = transpile("for x in a:\n    for y in b:\n        pass")
        assert result.count("for (const") == 2
    
    def test_nested_range(self):
        """for i in range(3): for j in range(3): pass"""
        result = transpile("for i in range(3):\n    for j in range(3):\n        pass")
        assert "for (let i" in result
        assert "for (let j" in result
    
    def test_deeply_nested(self):
        """Three levels of nesting"""
        code = "for a in x:\n    for b in y:\n        for c in z:\n            pass"
        result = transpile(code)
        assert result.count("for (const") == 3


# =============================================================================
# BREAK AND CONTINUE
# =============================================================================

class TestForBreakContinue:
    """Test break and continue in for loops."""
    
    def test_break_in_for(self):
        """for x in items: if x > 5: break"""
        result = transpile("for x in items:\n    if x > 5:\n        break")
        assert "break;" in result
    
    def test_continue_in_for(self):
        """for x in items: if x < 0: continue"""
        result = transpile("for x in items:\n    if x < 0:\n        continue")
        assert "continue;" in result
    
    def test_break_in_nested(self):
        """Break in nested loop"""
        code = "for x in a:\n    for y in b:\n        if y > 5:\n            break"
        result = transpile(code)
        assert "break;" in result


# =============================================================================
# ENUMERATE AND ZIP
# =============================================================================

class TestEnumerateZip:
    """Test enumerate and zip in for loops."""
    
    def test_enumerate(self):
        """for i, x in enumerate(items): pass"""
        result = transpile("for pair in enumerate(items):\n    pass")
        assert "__py.enumerate(items)" in result
    
    def test_zip(self):
        """for x, y in zip(a, b): pass"""
        result = transpile("for pair in zip(a, b):\n    pass")
        assert "__py.zip(a, b)" in result


# =============================================================================
# EDGE CASES
# =============================================================================

class TestForEdgeCases:
    """Test edge cases for for loops."""
    
    def test_for_with_pass(self):
        """for x in items: pass"""
        result = transpile("for x in items:\n    pass")
        assert "/* pass */" in result
    
    def test_for_empty_list(self):
        """for x in []: pass → uses __py.iter"""
        result = transpile("for x in []:\n    pass")
        assert "for (const x of __py.iter([]))" in result
    
    def test_for_in_literal_list(self):
        """for x in [1, 2, 3]: pass"""
        result = transpile("for x in [1, 2, 3]:\n    pass")
        assert "[1, 2, 3]" in result
    
    def test_range_with_expression(self):
        """for i in range(len(items)): pass"""
        result = transpile("for i in range(len(items)):\n    pass")
        assert "items.length" in result or "__py.len(items)" in result


# =============================================================================
# FOR RANGE COMPREHENSIVE
# =============================================================================

class TestForRangeComprehensive:
    """Comprehensive tests for range-based for loops."""
    
    def test_range_0(self):
        """range(0) produces empty loop"""
        result = transpile("for i in range(0):\n    print(i)")
        assert "i < 0" in result
    
    def test_range_1(self):
        """range(1) iterates once"""
        result = transpile("for i in range(1):\n    print(i)")
        assert "i < 1" in result
    
    def test_range_100(self):
        """range(100)"""
        result = transpile("for i in range(100):\n    pass")
        assert "i < 100" in result
    
    def test_range_negative_start(self):
        """range(-5, 5)"""
        result = transpile("for i in range(-5, 5):\n    pass")
        # Negative literals may be wrapped in parentheses for precedence
        assert ("i = -5" in result or "i = (-5)" in result)
        assert "i < 5" in result
    
    def test_range_step_2(self):
        """range(0, 10, 2)"""
        result = transpile("for i in range(0, 10, 2):\n    pass")
        assert "i += 2" in result
    
    def test_range_step_3(self):
        """range(0, 15, 3)"""
        result = transpile("for i in range(0, 15, 3):\n    pass")
        assert "i += 3" in result
    
    def test_range_countdown(self):
        """range(10, 0, -1) countdown"""
        result = transpile("for i in range(10, 0, -1):\n    pass")
        assert "-1" in result
