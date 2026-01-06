"""
Test Pass, Break, Continue Statement Transpilation

=============================================================================
WHAT THIS FILE TESTS
=============================================================================

Control flow statements: pass, break, continue.

=============================================================================
EXPECTED TRANSFORMATIONS
=============================================================================

Python      → JavaScript
pass        → /* pass */
break       → break;
continue    → continue;
"""

import pytest
from pynext.transpiler import transpile, TranspileError


# =============================================================================
# PASS STATEMENT
# =============================================================================

class TestPassStatement:
    """Test pass statement."""
    
    def test_pass_alone(self):
        """pass in function body"""
        result = transpile("def foo():\n    pass")
        assert "/* pass */" in result
    
    def test_pass_in_if(self):
        """if x: pass"""
        result = transpile("if x:\n    pass")
        assert "/* pass */" in result
    
    def test_pass_in_for(self):
        """for x in items: pass"""
        result = transpile("for x in items:\n    pass")
        assert "/* pass */" in result
    
    def test_pass_in_while(self):
        """while x: pass"""
        result = transpile("while x:\n    pass")
        assert "/* pass */" in result
    
    def test_pass_in_elif(self):
        """if x: a() elif y: pass"""
        result = transpile("if x:\n    a()\nelif y:\n    pass")
        assert "/* pass */" in result
    
    def test_pass_in_else(self):
        """if x: a() else: pass"""
        result = transpile("if x:\n    a()\nelse:\n    pass")
        assert "/* pass */" in result


# =============================================================================
# BREAK STATEMENT
# =============================================================================

class TestBreakStatement:
    """Test break statement."""
    
    def test_break_in_for(self):
        """for x in items: break"""
        result = transpile("for x in items:\n    break")
        assert "break;" in result
    
    def test_break_in_while(self):
        """while True: break"""
        result = transpile("while True:\n    break")
        assert "break;" in result
    
    def test_break_in_if(self):
        """for x in items: if x > 5: break"""
        result = transpile("for x in items:\n    if x > 5:\n        break")
        assert "break;" in result
    
    def test_break_nested_loop(self):
        """Break in nested loop"""
        code = "for x in a:\n    for y in b:\n        break"
        result = transpile(code)
        assert "break;" in result
    
    def test_break_after_work(self):
        """for x in items: work(); break"""
        result = transpile("for x in items:\n    work()\n    break")
        assert "work();" in result
        assert "break;" in result


# =============================================================================
# CONTINUE STATEMENT
# =============================================================================

class TestContinueStatement:
    """Test continue statement."""
    
    def test_continue_in_for(self):
        """for x in items: continue"""
        result = transpile("for x in items:\n    continue")
        assert "continue;" in result
    
    def test_continue_in_while(self):
        """while x: continue"""
        result = transpile("while x:\n    continue")
        assert "continue;" in result
    
    def test_continue_in_if(self):
        """for x in items: if x < 0: continue"""
        result = transpile("for x in items:\n    if x < 0:\n        continue")
        assert "continue;" in result
    
    def test_continue_then_work(self):
        """for x in items: if skip: continue; work()"""
        code = "for x in items:\n    if skip:\n        continue\n    work()"
        result = transpile(code)
        assert "continue;" in result
        assert "work();" in result


# =============================================================================
# COMBINED
# =============================================================================

class TestCombinedControlFlow:
    """Test combinations of control flow statements."""
    
    def test_break_and_continue(self):
        """Loop with both break and continue"""
        code = """
for x in items:
    if x < 0:
        continue
    if x > 100:
        break
    work(x)
"""
        result = transpile(code)
        assert "continue;" in result
        assert "break;" in result
    
    def test_pass_and_work(self):
        """if with pass in one branch"""
        code = "if x:\n    pass\nelse:\n    work()"
        result = transpile(code)
        assert "/* pass */" in result
        assert "work()" in result
