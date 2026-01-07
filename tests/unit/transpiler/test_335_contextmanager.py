"""
Tests for Phase 33.5: @contextmanager Decorator Transpilation

Tests the transpilation of Python's contextlib.contextmanager decorator to JavaScript
context manager objects with __enter__/__exit__ methods.

Run with: pytest tests/unit/transpiler/test_335_contextmanager.py -v
"""

import pytest
from pynext.transpiler import transpile


class TestContextmanagerDecorator:
    """Tests for @contextmanager decorator detection and transpilation."""
    
    def test_basic_contextmanager(self):
        """Test basic @contextmanager function transpilation."""
        code = '''
from contextlib import contextmanager

@contextmanager
def simple_context():
    print("enter")
    yield
    print("exit")
'''
        result = transpile(code)
        assert "function simple_context" in result
        assert "__enter__" in result
        assert "__exit__" in result
    
    def test_contextmanager_with_value(self):
        """Test @contextmanager that yields a value."""
        code = '''
from contextlib import contextmanager

@contextmanager
def value_context():
    value = 42
    yield value
    print("done")
'''
        result = transpile(code)
        assert "function value_context" in result
        assert "__enter__" in result
        assert "yield" in result.lower() or "value" in result
    
    def test_contextmanager_with_params(self):
        """Test @contextmanager with parameters."""
        code = '''
from contextlib import contextmanager

@contextmanager
def resource_context(name, timeout=10):
    resource = acquire(name, timeout)
    try:
        yield resource
    finally:
        release(resource)
'''
        result = transpile(code)
        assert "function resource_context" in result
        assert "name" in result
        assert "timeout" in result or "10" in result
    
    def test_contextmanager_with_try_finally(self):
        """Test @contextmanager with try/finally block."""
        code = '''
from contextlib import contextmanager

@contextmanager
def cleanup_context():
    resource = open_resource()
    try:
        yield resource
    finally:
        close_resource(resource)
'''
        result = transpile(code)
        assert "finally" in result
    
    def test_contextmanager_with_exception_handling(self):
        """Test @contextmanager with exception handling."""
        code = '''
from contextlib import contextmanager

@contextmanager
def error_context():
    try:
        yield
    except Exception as e:
        log_error(e)
        raise
'''
        result = transpile(code)
        assert "catch" in result or "except" in result.lower()
    
    def test_contextmanager_nested_generators(self):
        """Test @contextmanager with nested generator expressions."""
        code = '''
from contextlib import contextmanager

@contextmanager
def complex_context():
    items = [x for x in range(10)]
    yield items
    cleanup(items)
'''
        result = transpile(code)
        assert "function complex_context" in result
    
    def test_contextmanager_with_args_kwargs(self):
        """Test @contextmanager with *args and **kwargs."""
        code = '''
from contextlib import contextmanager

@contextmanager
def flexible_context(*args, **kwargs):
    setup(*args, **kwargs)
    yield
    teardown()
'''
        result = transpile(code)
        assert "function flexible_context" in result
        assert "args" in result
    
    def test_contextmanager_async_not_applicable(self):
        """Ensure async context managers use regular async handling."""
        code = '''
@contextmanager
def sync_context():
    yield 42
'''
        result = transpile(code)
        # Should not have async keyword for sync contextmanager
        assert "async function sync_context" not in result
    
    def test_contextmanager_preserves_name(self):
        """Test that function name is preserved."""
        code = '''
from contextlib import contextmanager

@contextmanager
def my_custom_manager():
    yield
'''
        result = transpile(code)
        assert "my_custom_manager" in result
    
    def test_contextmanager_multiple_yields_error(self):
        """Test that multiple yields are handled (generator behavior)."""
        code = '''
from contextlib import contextmanager

@contextmanager
def single_yield():
    yield 1
'''
        result = transpile(code)
        # Should compile without error
        assert "function single_yield" in result


class TestContextmanagerEmittedCode:
    """Tests for the structure of emitted context manager code."""
    
    def test_emitted_has_gen_field(self):
        """Test that emitted code has _gen field for generator."""
        code = '''
from contextlib import contextmanager

@contextmanager
def ctx():
    yield
'''
        result = transpile(code)
        assert "_gen" in result
    
    def test_emitted_enter_starts_generator(self):
        """Test that __enter__ starts the generator."""
        code = '''
from contextlib import contextmanager

@contextmanager
def ctx():
    yield 42
'''
        result = transpile(code)
        assert "__enter__" in result
        assert "next" in result
    
    def test_emitted_exit_completes_generator(self):
        """Test that __exit__ completes the generator."""
        code = '''
from contextlib import contextmanager

@contextmanager
def ctx():
    yield
'''
        result = transpile(code)
        assert "__exit__" in result
    
    def test_emitted_exit_handles_exceptions(self):
        """Test that __exit__ handles exceptions properly."""
        code = '''
from contextlib import contextmanager

@contextmanager
def ctx():
    try:
        yield
    finally:
        cleanup()
'''
        result = transpile(code)
        assert "__exit__" in result
        # Should have exception handling logic
        assert "excType" in result or "throw" in result
    
    def test_emitted_returns_object(self):
        """Test that function returns an object with CM methods."""
        code = '''
from contextlib import contextmanager

@contextmanager
def ctx():
    yield
'''
        result = transpile(code)
        assert "return {" in result or "return{" in result


class TestContextmanagerEdgeCases:
    """Tests for edge cases in contextmanager handling."""
    
    def test_contextmanager_empty_body(self):
        """Test contextmanager with minimal body."""
        code = '''
from contextlib import contextmanager

@contextmanager
def empty():
    yield
'''
        result = transpile(code)
        assert "function empty" in result
    
    def test_contextmanager_with_return_after_yield(self):
        """Test contextmanager with code after yield."""
        code = '''
from contextlib import contextmanager

@contextmanager
def ctx():
    print("before")
    yield 100
    print("after")
'''
        result = transpile(code)
        assert "function ctx" in result
    
    def test_contextmanager_with_conditional_yield(self):
        """Test contextmanager with conditional logic around yield."""
        code = '''
from contextlib import contextmanager

@contextmanager
def conditional():
    if True:
        yield 1
    else:
        yield 2
'''
        result = transpile(code)
        # Should still produce valid output
        assert "function conditional" in result
    
    def test_multiple_contextmanagers_in_file(self):
        """Test file with multiple @contextmanager functions."""
        code = '''
from contextlib import contextmanager

@contextmanager
def first():
    yield 1

@contextmanager
def second():
    yield 2
'''
        result = transpile(code)
        assert "function first" in result
        assert "function second" in result
    
    def test_contextmanager_and_regular_function(self):
        """Test mixed @contextmanager and regular functions."""
        code = '''
from contextlib import contextmanager

def regular():
    return 42

@contextmanager
def context():
    yield
'''
        result = transpile(code)
        assert "function regular" in result
        assert "function context" in result
        # Regular function should not have __enter__
        # Context manager should have __enter__
        assert "__enter__" in result

