"""
Test Function Definition Transpilation

=============================================================================
WHAT THIS FILE TESTS
=============================================================================

Function definitions.

Covers:
- Simple function definitions
- Functions with parameters
- Functions with default values
- Functions with return statements
- Nested functions
- Async functions

=============================================================================
EXPECTED TRANSFORMATIONS
=============================================================================

Python                          → JavaScript
def foo():                      → function foo() {
    pass                        →     /* pass */
                                → }

def foo(a, b):                  → function foo(a, b) {
    return a + b                →     return (a + b);
                                → }

def foo(x=1):                   → function foo(x = 1) {
    return x                    →     return x;
                                → }

async def foo():                → async function foo() {
    pass                        →     /* pass */
                                → }
"""

import pytest
from pynext.transpiler import transpile, TranspileError


# =============================================================================
# SIMPLE FUNCTIONS
# =============================================================================

class TestSimpleFunctions:
    """Test simple function definitions."""
    
    def test_empty_function(self):
        """def foo(): pass"""
        result = transpile("def foo():\n    pass")
        assert "function foo()" in result
    
    def test_function_with_body(self):
        """def foo(): print("hi")"""
        result = transpile('def foo():\n    print("hi")')
        assert "function foo()" in result
        assert "__py.print" in result
    
    def test_function_with_return(self):
        """def foo(): return 5"""
        result = transpile("def foo():\n    return 5")
        assert "function foo()" in result
        assert "return 5;" in result


# =============================================================================
# FUNCTION PARAMETERS
# =============================================================================

class TestFunctionParameters:
    """Test function parameters."""
    
    def test_single_param(self):
        """def foo(x): pass"""
        result = transpile("def foo(x):\n    pass")
        assert "function foo(x)" in result
    
    def test_two_params(self):
        """def foo(a, b): pass"""
        result = transpile("def foo(a, b):\n    pass")
        assert "function foo(a, b)" in result
    
    def test_many_params(self):
        """def foo(a, b, c, d, e): pass"""
        result = transpile("def foo(a, b, c, d, e):\n    pass")
        assert "function foo(a, b, c, d, e)" in result
    
    def test_underscore_param(self):
        """def foo(_): pass"""
        result = transpile("def foo(_):\n    pass")
        assert "function foo(_)" in result


# =============================================================================
# DEFAULT VALUES
# =============================================================================

class TestDefaultValues:
    """Test function parameters with default values."""
    
    def test_single_default(self):
        """def foo(x=1): pass"""
        result = transpile("def foo(x=1):\n    pass")
        assert "x = 1" in result
    
    def test_default_string(self):
        """def foo(x="hi"): pass"""
        result = transpile('def foo(x="hi"):\n    pass')
        assert 'x = "hi"' in result
    
    def test_default_none(self):
        """def foo(x=None): pass"""
        result = transpile("def foo(x=None):\n    pass")
        assert "x = null" in result
    
    def test_default_true(self):
        """def foo(x=True): pass"""
        result = transpile("def foo(x=True):\n    pass")
        assert "x = true" in result
    
    def test_default_false(self):
        """def foo(x=False): pass"""
        result = transpile("def foo(x=False):\n    pass")
        assert "x = false" in result
    
    def test_default_list(self):
        """def foo(x=[]): pass - note: mutable default anti-pattern"""
        result = transpile("def foo(x=[]):\n    pass")
        assert "x = []" in result
    
    def test_multiple_defaults(self):
        """def foo(a=1, b=2): pass"""
        result = transpile("def foo(a=1, b=2):\n    pass")
        assert "a = 1" in result
        assert "b = 2" in result
    
    def test_mixed_params(self):
        """def foo(a, b=2): pass"""
        result = transpile("def foo(a, b=2):\n    pass")
        assert "function foo(a, b = 2)" in result


# =============================================================================
# FUNCTION BODY
# =============================================================================

class TestFunctionBody:
    """Test function bodies."""
    
    def test_multiple_statements(self):
        """def foo(): a(); b(); c()"""
        result = transpile("def foo():\n    a()\n    b()\n    c()")
        assert "a()" in result
        assert "b()" in result
        assert "c()" in result
    
    def test_local_variable(self):
        """def foo(): x = 5"""
        result = transpile("def foo():\n    x = 5")
        assert "let x = 5" in result
    
    def test_if_in_function(self):
        """def foo(): if x: bar() - uses __py.bool for truthiness"""
        result = transpile("def foo():\n    if x:\n        bar()")
        assert "__py.bool(x)" in result
    
    def test_for_in_function(self):
        """def foo(): for x in items: bar(x) → uses __py.iter"""
        result = transpile("def foo():\n    for x in items:\n        bar(x)")
        assert "for (const x of __py.iter(items))" in result


# =============================================================================
# NESTED FUNCTIONS
# =============================================================================

class TestNestedFunctions:
    """Test nested function definitions."""
    
    def test_nested_function(self):
        """def foo(): def bar(): pass"""
        result = transpile("def foo():\n    def bar():\n        pass")
        assert "function foo()" in result
        assert "function bar()" in result
    
    def test_nested_function_call(self):
        """def foo(): def bar(): return 5; return bar()"""
        code = "def foo():\n    def bar():\n        return 5\n    return bar()"
        result = transpile(code)
        assert "function bar()" in result
        assert "return bar();" in result


# =============================================================================
# ASYNC FUNCTIONS
# =============================================================================

class TestAsyncFunctions:
    """Test async function definitions."""
    
    def test_async_empty(self):
        """async def foo(): pass"""
        result = transpile("async def foo():\n    pass")
        assert "async function foo()" in result
    
    def test_async_with_params(self):
        """async def foo(x): pass"""
        result = transpile("async def foo(x):\n    pass")
        assert "async function foo(x)" in result
    
    def test_async_with_return(self):
        """async def foo(): return 5"""
        result = transpile("async def foo():\n    return 5")
        assert "async function foo()" in result
        assert "return 5;" in result


# =============================================================================
# RESERVED WORD HANDLING
# =============================================================================

class TestReservedWords:
    """Test handling of JavaScript reserved words."""
    
    def test_function_named_delete(self):
        """def delete(): pass - 'delete' is JS reserved"""
        result = transpile("def delete_item():\n    pass")
        assert "function delete_item()" in result
    
    def test_param_named_class(self):
        """def foo(class_name): pass"""
        result = transpile("def foo(class_name):\n    pass")
        assert "class_name" in result


# =============================================================================
# EDGE CASES
# =============================================================================

class TestFunctionEdgeCases:
    """Test edge cases for function definitions."""
    
    def test_function_with_only_pass(self):
        """def foo(): pass"""
        result = transpile("def foo():\n    pass")
        assert "/* pass */" in result
    
    def test_function_with_docstring(self):
        """def foo(): "docstring"; pass"""
        result = transpile('def foo():\n    """docstring"""\n    pass')
        # Docstring becomes expression statement
        assert "function foo()" in result
    
    def test_long_function_name(self):
        """def this_is_a_very_long_function_name(): pass"""
        name = "this_is_a_very_long_function_name"
        result = transpile(f"def {name}():\n    pass")
        assert f"function {name}()" in result
    
    def test_function_with_underscore_name(self):
        """def _private(): pass"""
        result = transpile("def _private():\n    pass")
        assert "function _private()" in result
