"""
Test If Statement Transpilation

=============================================================================
WHAT THIS FILE TESTS
=============================================================================

If/elif/else statements.

Covers:
- Simple if statements
- If-else statements
- If-elif-else chains
- Nested if statements
- Various condition types
- Truthiness testing with __py.bool()

=============================================================================
EXPECTED TRANSFORMATIONS
=============================================================================

Python                      → JavaScript
if x:                       → if (__py.bool(x)) {      # Variable needs bool
    pass                    →     /* pass */
                            → }

if True:                    → if (true) {              # Literal - no bool needed
    pass                    →     /* pass */
                            → }

if x > 0:                   → if (x > 0) {             # Comparison - no bool needed
    foo()                   →     foo();
elif x < 0:                 → } else if (x < 0) {
    bar()                   →     bar();
else:                       → } else {
    baz()                   →     baz();
                            → }

Note: Variables and function calls use __py.bool() because:
- Python: [] is falsy, JS: [] is truthy
- Python: {} is falsy, JS: {} is truthy
"""

import pytest
from pynext.transpiler import transpile, TranspileError


# =============================================================================
# SIMPLE IF
# =============================================================================

class TestSimpleIf:
    """Test simple if statements without else."""
    
    def test_if_true(self):
        """if True: pass"""
        result = transpile("if True:\n    pass")
        assert "if (true)" in result
    
    def test_if_false(self):
        """if False: pass"""
        result = transpile("if False:\n    pass")
        assert "if (false)" in result
    
    def test_if_variable(self):
        """if x: pass - uses __py.bool for Python truthiness"""
        result = transpile("if x:\n    pass")
        assert "__py.bool(x)" in result
    
    def test_if_with_body(self):
        """if x: foo() - uses __py.bool for Python truthiness"""
        result = transpile("if x:\n    foo()")
        assert "__py.bool(x)" in result
        assert "foo()" in result
    
    def test_if_with_multiple_statements(self):
        """if x: foo(); bar()"""
        result = transpile("if x:\n    foo()\n    bar()")
        assert "foo()" in result
        assert "bar()" in result


# =============================================================================
# IF-ELSE
# =============================================================================

class TestIfElse:
    """Test if-else statements."""
    
    def test_if_else_simple(self):
        """if x: foo() else: bar() - uses __py.bool for variable"""
        result = transpile("if x:\n    foo()\nelse:\n    bar()")
        assert "__py.bool(x)" in result
        assert "} else {" in result
        assert "foo()" in result
        assert "bar()" in result
    
    def test_if_else_with_multiple_statements(self):
        """if x: a(); b() else: c(); d()"""
        result = transpile("if x:\n    a()\n    b()\nelse:\n    c()\n    d()")
        assert "a()" in result
        assert "b()" in result
        assert "c()" in result
        assert "d()" in result


# =============================================================================
# IF-ELIF-ELSE
# =============================================================================

class TestIfElifElse:
    """Test if-elif-else chains."""
    
    def test_if_elif(self):
        """if x: a() elif y: b() - uses __py.bool for variables"""
        result = transpile("if x:\n    a()\nelif y:\n    b()")
        assert "__py.bool(x)" in result
        assert "__py.bool(y)" in result
    
    def test_if_elif_else(self):
        """if x: a() elif y: b() else: c() - uses __py.bool for variables"""
        result = transpile("if x:\n    a()\nelif y:\n    b()\nelse:\n    c()")
        assert "__py.bool(x)" in result
        assert "__py.bool(y)" in result
        assert "} else {" in result
    
    def test_multiple_elif(self):
        """if a: x() elif b: y() elif c: z()"""
        result = transpile("if a:\n    x()\nelif b:\n    y()\nelif c:\n    z()")
        assert result.count("else if") == 2
    
    def test_many_elif(self):
        """if with 5 elif clauses"""
        code = "if a:\n    x()\n"
        for i in range(5):
            code += f"elif c{i}:\n    f{i}()\n"
        code += "else:\n    final()"
        result = transpile(code)
        assert result.count("else if") == 5


# =============================================================================
# COMPARISON CONDITIONS
# =============================================================================

class TestComparisonConditions:
    """Test various comparison operators in conditions."""
    
    def test_greater_than(self):
        """if x > 0: pass"""
        result = transpile("if x > 0:\n    pass")
        assert "x > 0" in result
    
    def test_less_than(self):
        """if x < 0: pass"""
        result = transpile("if x < 0:\n    pass")
        assert "x < 0" in result
    
    def test_greater_equal(self):
        """if x >= 0: pass"""
        result = transpile("if x >= 0:\n    pass")
        assert "x >= 0" in result
    
    def test_less_equal(self):
        """if x <= 0: pass"""
        result = transpile("if x <= 0:\n    pass")
        assert "x <= 0" in result
    
    def test_equal(self):
        """if x == 5: pass → uses __py.eq for deep equality"""
        result = transpile("if x == 5:\n    pass")
        assert "__py.eq" in result or "===" in result
    
    def test_not_equal(self):
        """if x != 5: pass"""
        result = transpile("if x != 5:\n    pass")
        assert "__py.eq" in result or "!==" in result


# =============================================================================
# BOOLEAN CONDITIONS
# =============================================================================

class TestBooleanConditions:
    """Test boolean operators in conditions."""
    
    def test_and(self):
        """if x and y: pass"""
        result = transpile("if x and y:\n    pass")
        assert "__py.bool" in result or ("x" in result and "y" in result)
    
    def test_or(self):
        """if x or y: pass"""
        result = transpile("if x or y:\n    pass")
        assert "x" in result and "y" in result
    
    def test_not(self):
        """if not x: pass"""
        result = transpile("if not x:\n    pass")
        assert "__py.bool" in result or "!" in result
    
    def test_complex_boolean(self):
        """if (x and y) or z: pass"""
        result = transpile("if (x and y) or z:\n    pass")
        assert "x" in result and "y" in result and "z" in result


# =============================================================================
# IDENTITY CONDITIONS
# =============================================================================

class TestIdentityConditions:
    """Test identity comparisons."""
    
    def test_is_none(self):
        """if x is None: pass"""
        result = transpile("if x is None:\n    pass")
        assert "===" in result and "null" in result
    
    def test_is_not_none(self):
        """if x is not None: pass"""
        result = transpile("if x is not None:\n    pass")
        assert "!==" in result and "null" in result


# =============================================================================
# MEMBERSHIP CONDITIONS
# =============================================================================

class TestMembershipConditions:
    """Test membership operators in conditions."""
    
    def test_in(self):
        """if x in items: pass"""
        result = transpile("if x in items:\n    pass")
        assert "__py.in" in result
    
    def test_not_in(self):
        """if x not in items: pass"""
        result = transpile("if x not in items:\n    pass")
        assert "__py.in" in result


# =============================================================================
# NESTED IF
# =============================================================================

class TestNestedIf:
    """Test nested if statements."""
    
    def test_nested_if(self):
        """if x: if y: foo()"""
        result = transpile("if x:\n    if y:\n        foo()")
        assert result.count("if (") == 2
    
    def test_deeply_nested_if(self):
        """Three levels of nesting"""
        code = "if a:\n    if b:\n        if c:\n            foo()"
        result = transpile(code)
        assert result.count("if (") == 3
    
    def test_nested_if_else(self):
        """if x: if y: a() else: b() - uses __py.bool for variables"""
        code = "if x:\n    if y:\n        a()\n    else:\n        b()"
        result = transpile(code)
        assert "__py.bool(x)" in result
        assert "__py.bool(y)" in result


# =============================================================================
# EDGE CASES
# =============================================================================

class TestIfEdgeCases:
    """Test edge cases for if statements."""
    
    def test_empty_body_pass(self):
        """if x: pass"""
        result = transpile("if x:\n    pass")
        assert "/* pass */" in result
    
    def test_chained_comparison(self):
        """if 0 < x < 10: pass"""
        result = transpile("if 0 < x < 10:\n    pass")
        assert "0 < x" in result or "x" in result
    
    def test_ternary_in_condition(self):
        """if (a if cond else b): pass"""
        result = transpile("if (a if cond else b):\n    pass")
        assert "?" in result and ":" in result
    
    def test_function_call_in_condition(self):
        """if foo(): pass - uses __py.bool because function could return []"""
        result = transpile("if foo():\n    pass")
        assert "__py.bool(foo())" in result
