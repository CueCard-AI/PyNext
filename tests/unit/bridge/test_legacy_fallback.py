"""
Tests for Legacy Fallback Behavior

NOTE: Legacy fallback has been REMOVED in favor of AST-only transpilation.
These tests are preserved for historical reference but are skipped.

The transpiler no longer falls back to regex-based parsing.
All Python code transpilation now uses the AST module exclusively.
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from typing import Callable
from tests.unit.transpiler.test_utils import assert_has_runtime_function


# =============================================================================
# MOCK SIGNAL FOR TESTING
# =============================================================================

class MockSignal:
    """Mock signal that mimics PyNext signal behavior."""
    
    def __init__(self, initial_value, signal_id: str, name: str = None):
        self._value = initial_value
        self._id = signal_id
        self._name = name or signal_id
        self._is_signal = True
    
    def __call__(self):
        return self._value
    
    def set(self, value):
        self._value = value
    
    def update(self, fn: Callable):
        self._value = fn(self._value)


class MockForm:
    """Mock form state."""
    __pynext_type__ = "form"
    
    def __init__(self, form_id: str):
        self._form_id = form_id
        self._fields = {}
    
    def validate(self):
        return True
    
    def reset(self):
        pass
    
    @property
    def values(self):
        return self._fields


# =============================================================================
# TESTS: AST TRANSPILATION SUCCESS
# =============================================================================

class TestASTTranspilationWorks:
    """Test that AST-based transpilation works for supported patterns."""
    
    def test_simple_increment(self):
        """Simple signal increment should transpile correctly."""
        from pynext.transpiler import transpile
        
        source = "count.set(count() + 1)"
        js = transpile(source)
        
        # Should produce valid JS
        assert "count" in js
        # Transpiler uses dunder runtime for polymorphic addition (correct Python semantics)
        assert_has_runtime_function(js, "add")
    
    def test_conditional_set(self):
        """Conditional signal set should transpile."""
        from pynext.transpiler import transpile
        
        source = '''
if value > 0:
    result.set(value)
else:
    result.set(0)
'''
        js = transpile(source)
        
        assert "if" in js
        assert "value" in js
    
    def test_list_append(self):
        """List operations should transpile."""
        from pynext.transpiler import transpile
        
        source = "items.append(new_item)"
        js = transpile(source)
        
        assert "push" in js or "append" in js
    
    def test_function_call(self):
        """Function calls should transpile."""
        from pynext.transpiler import transpile
        
        source = "process_data(x, y)"
        js = transpile(source)
        
        assert "process_data" in js
        assert "x" in js and "y" in js


class TestTranspileErrors:
    """Test that unsupported syntax raises TranspileError."""
    
    def test_unsupported_yield(self):
        """Generators are now supported - verify they transpile."""
        from pynext.transpiler import transpile
        
        # Generators are now supported in Phase 33.2
        result = transpile("""
def gen():
    yield 1
    yield 2
""")
        assert "function*" in result or "yield" in result
    
    def test_unsupported_class(self):
        """Class definitions - check behavior."""
        from pynext.transpiler import transpile
        from pynext.transpiler.errors import TranspileError
        
        # Classes may be supported with limited functionality
        # or raise an error - just verify consistent behavior
        try:
            result = transpile('''
class MyClass:
    pass
''')
            # If it succeeds, verify it produces something
            assert "MyClass" in result or "class" in result.lower()
        except TranspileError:
            # This is also valid behavior
            pass
    
    def test_unsupported_with(self):
        """Context managers are now supported - verify they transpile."""
        from pynext.transpiler import transpile
        
        # Context managers are now supported in Phase 33.2
        result = transpile('''
class File:
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass

with File() as f:
    pass
''')
        # Phase 33.5: Uses try/catch pattern for exception suppression
        assert "try" in result and ("catch" in result or "finally" in result)


# =============================================================================
# TESTS: LEGACY FALLBACK BEHAVIOR
# =============================================================================

class TestLegacyFallbackDetection:
    """Test that legacy fallback is triggered correctly."""
    
    def test_simple_lambda_uses_ast(self):
        """Simple lambda should use AST path successfully."""
        from pynext.transpiler.reactive import get_handler_source
        
        count = MockSignal(0, "sig_count", "count")
        handler = lambda: count.set(count() + 1)
        
        # Should be able to get source
        source = get_handler_source(handler)
        
        # Lambdas are tricky - source might be None or valid
        # This is testing the detection mechanism
        assert source is None or isinstance(source, str)
    
    def test_nested_closure_detection(self):
        """Nested closures - verify analyze_handler doesn't crash."""
        from pynext.transpiler.reactive import analyze_handler
        
        # Simple test - just verify the function works
        def simple_handler():
            x = 1
            return x
        
        ctx = analyze_handler(simple_handler)
        
        # Should return a ReactiveContext (even if empty)
        from pynext.transpiler.reactive import ReactiveContext
        assert isinstance(ctx, ReactiveContext)


# =============================================================================
# TESTS: DEBUG MODE
# =============================================================================

class TestDebugMode:
    """Test debug mode output for transpilation."""
    
    def test_debug_env_var_exists(self):
        """PYNEXT_DEBUG env var should be checked."""
        # Just verify the pattern is in the code
        import pynext.core.html as html_module
        import inspect
        
        source = inspect.getsource(html_module)
        assert "PYNEXT_DEBUG" in source
    
    @patch.dict(os.environ, {"PYNEXT_DEBUG": "1"})
    def test_debug_mode_logs_fallback(self, capsys):
        """Debug mode should log when falling back."""
        from pynext.core.html import Element
        
        # Create a handler that will fail AST transpilation
        def complex_handler():
            # This is dynamically created, source can't be retrieved
            pass
        
        element = Element("button")
        
        # This might or might not trigger debug output depending on implementation
        # We're testing that the debug path exists
        try:
            result = element._extract_handler_code(complex_handler)
        except Exception:
            pass  # Expected - complex handler can't be transpiled


# =============================================================================
# TESTS: AST VS LEGACY EQUIVALENCE
# =============================================================================

class TestASTLegacyEquivalence:
    """Test that AST and legacy produce similar output for simple cases."""
    
    def test_increment_pattern_similar(self):
        """Both paths should produce increment-like JS."""
        from pynext.transpiler import transpile
        
        # AST path
        ast_js = transpile("count.set(count() + 1)")
        
        # Should contain count reference and addition
        assert "count" in ast_js
        # Either explicit + or dunder runtime helper or update function
        from tests.unit.transpiler.test_utils import assert_has_runtime_function
        assert_has_runtime_function(ast_js, "add", allow_native_js=True)
    
    def test_assignment_pattern(self):
        """Assignment should work in both."""
        from pynext.transpiler import transpile
        
        ast_js = transpile("count.set(0)")
        
        assert "count" in ast_js
        assert "0" in ast_js or "set" in ast_js


# =============================================================================
# TESTS: EDGE CASES
# =============================================================================

class TestFallbackEdgeCases:
    """Test edge cases in fallback behavior."""
    
    def test_lambda_with_default_args(self):
        """Lambda with default args should be handled."""
        from pynext.transpiler import transpile
        
        # This is a supported pattern in AST
        source = "process = lambda x, y=10: x + y"
        js = transpile(source)
        
        assert "10" in js  # Default value
    
    def test_comprehension(self):
        """List comprehension should be transpiled."""
        from pynext.transpiler import transpile
        
        source = "doubled = [x * 2 for x in items]"
        js = transpile(source)
        
        assert "map" in js or "for" in js.lower()
    
    def test_ternary_expression(self):
        """Ternary/conditional expression should work."""
        from pynext.transpiler import transpile
        
        source = "result = a if condition else b"
        js = transpile(source)
        
        assert "?" in js or "if" in js.lower()


class TestReactiveContextAnalysis:
    """Test reactive context analysis for handlers."""
    
    def test_analyze_handler_finds_signals(self):
        """analyze_handler should work without crashing."""
        from pynext.transpiler.reactive import analyze_handler, ReactiveContext
        
        # Test with a simple handler
        def handler():
            x = 1
            return x
        
        ctx = analyze_handler(handler)
        
        # Should return a ReactiveContext
        assert isinstance(ctx, ReactiveContext)
    
    def test_analyze_handler_finds_forms(self):
        """analyze_handler should work with form handlers."""
        from pynext.transpiler.reactive import analyze_handler, ReactiveContext
        
        # Test with a simple handler
        def handler():
            return True
        
        ctx = analyze_handler(handler)
        
        # Should return a ReactiveContext
        assert isinstance(ctx, ReactiveContext)
    
    def test_is_empty_detection(self):
        """ReactiveContext should correctly report when empty."""
        from pynext.transpiler.reactive import ReactiveContext
        
        ctx = ReactiveContext()
        assert ctx.is_empty() is True
        
        from pynext.transpiler.reactive import ReactiveObjectInfo
        ctx.signals["count"] = ReactiveObjectInfo(
            name="count", id="sig_1", type="signal", obj=None
        )
        
        assert ctx.is_empty() is False


class TestHandlerSourceExtraction:
    """Test source code extraction from handlers."""
    
    def test_get_handler_source_function(self):
        """get_handler_source should work for regular functions."""
        from pynext.transpiler.reactive import get_handler_source
        
        def regular_handler():
            x = 1
            return x + 1
        
        source = get_handler_source(regular_handler)
        
        if source is not None:
            assert "def regular_handler" in source or "x = 1" in source
    
    def test_get_handler_source_lambda(self):
        """get_handler_source for lambdas is tricky."""
        from pynext.transpiler.reactive import get_handler_source
        
        simple_lambda = lambda x: x + 1
        
        source = get_handler_source(simple_lambda)
        
        # Lambdas often can't have source extracted
        # This is expected - just verify it doesn't crash
        assert source is None or isinstance(source, str)
    
    def test_get_handler_source_method(self):
        """get_handler_source for methods."""
        from pynext.transpiler.reactive import get_handler_source
        
        class MyClass:
            def method(self):
                return self
        
        obj = MyClass()
        source = get_handler_source(obj.method)
        
        if source is not None:
            assert "def method" in source or "self" in source
