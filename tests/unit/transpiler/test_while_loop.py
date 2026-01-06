"""
Test While Loop Transpilation

=============================================================================
WHAT THIS FILE TESTS
=============================================================================

While loops.

Covers:
- Simple while loops
- While with break
- While with continue
- While True loops
- Nested while loops

=============================================================================
EXPECTED TRANSFORMATIONS
=============================================================================

Python                      → JavaScript
while x > 0:                → while (x > 0) {
    x -= 1                  →     x -= 1;
                            → }

while True:                 → while (true) {
    if done:                →     if (done) {
        break               →         break;
                            →     }
                            → }
"""

import pytest
from pynext.transpiler import transpile, TranspileError


# =============================================================================
# SIMPLE WHILE
# =============================================================================

class TestSimpleWhile:
    """Test simple while loops."""
    
    def test_while_true(self):
        """while True: pass"""
        result = transpile("while True:\n    pass")
        assert "while (true)" in result
    
    def test_while_false(self):
        """while False: pass"""
        result = transpile("while False:\n    pass")
        assert "while (false)" in result
    
    def test_while_condition(self):
        """while x > 0: pass"""
        result = transpile("while x > 0:\n    pass")
        assert "while" in result and "x > 0" in result
    
    def test_while_with_body(self):
        """while x > 0: x -= 1"""
        result = transpile("while x > 0:\n    x -= 1")
        assert "while" in result and "x > 0" in result
        assert "x -= 1" in result
    
    def test_while_variable(self):
        """while running: pass - uses __py.bool for Python truthiness"""
        result = transpile("while running:\n    pass")
        assert "__py.bool(running)" in result


# =============================================================================
# WHILE WITH BREAK
# =============================================================================

class TestWhileBreak:
    """Test while loops with break."""
    
    def test_while_break(self):
        """while True: break"""
        result = transpile("while True:\n    break")
        assert "while (true)" in result
        assert "break;" in result
    
    def test_while_conditional_break(self):
        """while True: if done: break"""
        result = transpile("while True:\n    if done:\n        break")
        assert "break;" in result
    
    def test_while_break_after_work(self):
        """while True: work(); if done: break"""
        result = transpile("while True:\n    work()\n    if done:\n        break")
        assert "work()" in result
        assert "break;" in result


# =============================================================================
# WHILE WITH CONTINUE
# =============================================================================

class TestWhileContinue:
    """Test while loops with continue."""
    
    def test_while_continue(self):
        """while x: if skip: continue"""
        result = transpile("while x:\n    if skip:\n        continue")
        assert "continue;" in result
    
    def test_while_continue_and_work(self):
        """while x: if skip: continue; work()"""
        result = transpile("while x:\n    if skip:\n        continue\n    work()")
        assert "continue;" in result
        assert "work()" in result


# =============================================================================
# NESTED WHILE
# =============================================================================

class TestNestedWhile:
    """Test nested while loops."""
    
    def test_nested_while(self):
        """while a: while b: pass"""
        result = transpile("while a:\n    while b:\n        pass")
        assert result.count("while (") == 2
    
    def test_deeply_nested_while(self):
        """Three levels of nesting"""
        code = "while a:\n    while b:\n        while c:\n            pass"
        result = transpile(code)
        assert result.count("while (") == 3


# =============================================================================
# COMPLEX CONDITIONS
# =============================================================================

class TestWhileComplexConditions:
    """Test while loops with complex conditions."""
    
    def test_while_and(self):
        """while x and y: pass"""
        result = transpile("while x and y:\n    pass")
        assert "x" in result and "y" in result
    
    def test_while_or(self):
        """while x or y: pass"""
        result = transpile("while x or y:\n    pass")
        assert "x" in result and "y" in result
    
    def test_while_not(self):
        """while not done: pass"""
        result = transpile("while not done:\n    pass")
        assert "__py.bool" in result or "!" in result
    
    def test_while_comparison(self):
        """while x < len(items): pass"""
        result = transpile("while x < len(items):\n    pass")
        assert "items.length" in result or "__py.len(items)" in result


# =============================================================================
# EDGE CASES
# =============================================================================

class TestWhileEdgeCases:
    """Test edge cases for while loops."""
    
    def test_while_with_pass(self):
        """while x: pass"""
        result = transpile("while x:\n    pass")
        assert "/* pass */" in result
    
    def test_while_zero(self):
        """while 0: pass - uses __py.bool for consistency"""
        result = transpile("while 0:\n    pass")
        assert "__py.bool(0)" in result
    
    def test_while_empty_string(self):
        """while "": pass - uses __py.bool for consistency"""
        result = transpile('while "":\n    pass')
        assert '__py.bool("")' in result
    
    def test_while_function_call(self):
        """while has_more(): pass - uses __py.bool because result could be []"""
        result = transpile("while has_more():\n    pass")
        assert "__py.bool(has_more())" in result
