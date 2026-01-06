"""
Test Lambda Expression Transpilation

=============================================================================
WHAT THIS FILE TESTS
=============================================================================

Lambda expressions.

Covers:
- Simple lambdas
- Lambdas with multiple parameters
- Lambdas with default values
- Lambdas in various contexts (assignment, call arguments, etc.)

=============================================================================
EXPECTED TRANSFORMATIONS
=============================================================================

Python                          → JavaScript
lambda: 42                      → () => 42
lambda x: x                     → (x) => x
lambda x: x * 2                 → (x) => x * 2
lambda x, y: x + y              → (x, y) => x + y
lambda x=1: x                   → (x = 1) => x
"""

import pytest
from pynext.transpiler import transpile, TranspileError
from tests.unit.transpiler.test_utils import assert_has_runtime_function


# =============================================================================
# SIMPLE LAMBDAS
# =============================================================================

class TestSimpleLambdas:
    """Test simple lambda expressions."""
    
    def test_lambda_no_params(self):
        """lambda: 42"""
        result = transpile("f = lambda: 42")
        assert "() => 42" in result
    
    def test_lambda_identity(self):
        """lambda x: x"""
        result = transpile("f = lambda x: x")
        assert "(x) => x" in result
    
    def test_lambda_constant(self):
        """lambda x: 5"""
        result = transpile("f = lambda x: 5")
        assert "(x) => 5" in result


# =============================================================================
# LAMBDA OPERATIONS
# =============================================================================

class TestLambdaOperations:
    """Test lambdas with various operations."""
    
    def test_lambda_double(self):
        """lambda x: x * 2 → uses dunder runtime"""
        result = transpile("f = lambda x: x * 2")
        assert "(x) =>" in result
        assert_has_runtime_function(result, "mul")
    
    def test_lambda_add(self):
        """lambda x: x + 1 → uses dunder runtime"""
        result = transpile("f = lambda x: x + 1")
        assert "(x) =>" in result
        assert_has_runtime_function(result, "add")
    
    def test_lambda_subtract(self):
        """lambda x: x - 1 → uses dunder runtime"""
        result = transpile("f = lambda x: x - 1")
        assert "(x) =>" in result
        assert_has_runtime_function(result, "sub")
    
    def test_lambda_negate(self):
        """lambda x: -x → uses dunder runtime"""
        result = transpile("f = lambda x: -x")
        assert "(x) =>" in result
        assert_has_runtime_function(result, "neg")
    
    def test_lambda_comparison(self):
        """lambda x: x > 0"""
        result = transpile("f = lambda x: x > 0")
        assert "(x) => " in result and "> 0" in result


# =============================================================================
# MULTIPLE PARAMETERS
# =============================================================================

class TestLambdaMultipleParams:
    """Test lambdas with multiple parameters."""
    
    def test_lambda_two_params(self):
        """lambda x, y: x + y"""
        result = transpile("f = lambda x, y: x + y")
        assert "(x, y) =>" in result
    
    def test_lambda_three_params(self):
        """lambda a, b, c: a + b + c"""
        result = transpile("f = lambda a, b, c: a + b + c")
        assert "(a, b, c) =>" in result
    
    def test_lambda_many_params(self):
        """lambda a, b, c, d, e: a"""
        result = transpile("f = lambda a, b, c, d, e: a")
        assert "(a, b, c, d, e) =>" in result


# =============================================================================
# DEFAULT VALUES
# =============================================================================

class TestLambdaDefaults:
    """Test lambdas with default parameter values."""
    
    def test_lambda_default_int(self):
        """lambda x=1: x"""
        result = transpile("f = lambda x=1: x")
        assert "(x = 1) =>" in result
    
    def test_lambda_default_string(self):
        """lambda x="hi": x"""
        result = transpile('f = lambda x="hi": x')
        assert 'x = "hi"' in result
    
    def test_lambda_default_none(self):
        """lambda x=None: x"""
        result = transpile("f = lambda x=None: x")
        assert "x = null" in result
    
    def test_lambda_mixed_defaults(self):
        """lambda a, b=2: a + b"""
        result = transpile("f = lambda a, b=2: a + b")
        assert "(a, b = 2) =>" in result


# =============================================================================
# LAMBDA IN CONTEXT
# =============================================================================

class TestLambdaInContext:
    """Test lambdas used in various contexts."""
    
    def test_lambda_in_map(self):
        """map(lambda x: x * 2, items)"""
        result = transpile("result = map(lambda x: x * 2, items)")
        assert "=>" in result
        assert "map" in result.lower() or "Array" in result
    
    def test_lambda_in_filter(self):
        """filter(lambda x: x > 0, items)"""
        result = transpile("result = filter(lambda x: x > 0, items)")
        assert "=>" in result
        assert "filter" in result.lower()
    
    def test_lambda_in_sorted(self):
        """sorted(items, key=lambda x: x.name)"""
        result = transpile("result = sorted(items, key=lambda x: x.name)")
        # Sorted with key may simplify or use lambda
        assert "sort" in result or "=>" in result
    
    def test_lambda_as_callback(self):
        """callback(lambda: done.set(True))"""
        result = transpile("callback(lambda: done.set(True))")
        assert "() =>" in result


# =============================================================================
# COMPLEX LAMBDA BODIES
# =============================================================================

class TestComplexLambdaBodies:
    """Test lambdas with complex body expressions."""
    
    def test_lambda_ternary(self):
        """lambda x: "even" if x % 2 == 0 else "odd" """
        result = transpile('f = lambda x: "even" if x % 2 == 0 else "odd"')
        assert "?" in result and ":" in result
    
    def test_lambda_method_call(self):
        """lambda s: s.lower()"""
        result = transpile("f = lambda s: s.lower()")
        assert "toLowerCase" in result
    
    def test_lambda_function_call(self):
        """lambda x: len(x)"""
        result = transpile("f = lambda x: len(x)")
        assert ".length" in result or "__py.len" in result
    
    def test_lambda_attribute(self):
        """lambda x: x.value"""
        result = transpile("f = lambda x: x.value")
        assert "(x) => x.value" in result
    
    def test_lambda_subscript(self):
        """lambda x: x[0]"""
        result = transpile("f = lambda x: x[0]")
        # Phase 33.2: Uses __py.getitem() for __getitem__ dunder support
        assert "__py.getitem(x, 0)" in result


# =============================================================================
# EDGE CASES
# =============================================================================

class TestLambdaEdgeCases:
    """Test edge cases for lambda expressions."""
    
    def test_lambda_bool_return(self):
        """lambda: True"""
        result = transpile("f = lambda: True")
        assert "() => true" in result
    
    def test_lambda_none_return(self):
        """lambda: None"""
        result = transpile("f = lambda: None")
        assert "() => null" in result
    
    def test_lambda_list_return(self):
        """lambda: [1, 2, 3]"""
        result = transpile("f = lambda: [1, 2, 3]")
        assert "() => [1, 2, 3]" in result
    
    def test_lambda_dict_return(self):
        """lambda: {"a": 1}"""
        result = transpile('f = lambda: {"a": 1}')
        assert "() =>" in result and '"a"' in result
    
    def test_lambda_underscore_param(self):
        """lambda _: 42"""
        result = transpile("f = lambda _: 42")
        assert "(_) => 42" in result
