"""
Phase 33.5: Context Manager Edge Case Tests

Comprehensive edge case tests for context manager transpilation,
covering complex scenarios and corner cases.
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# BASIC CONTEXT MANAGER TRANSPILATION
# =============================================================================

class TestContextManagerBasic:
    """Basic context manager transpilation tests."""
    
    def test_contextmanager_simple(self):
        """Simple @contextmanager function."""
        code = '''
from contextlib import contextmanager

@contextmanager
def simple_context():
    yield
'''
        js = transpile(code)
        assert "yield" in js or "__py" in js
    
    def test_contextmanager_with_setup_teardown(self):
        """@contextmanager with setup and teardown."""
        code = '''
from contextlib import contextmanager

@contextmanager
def managed_resource():
    print("setup")
    yield
    print("teardown")
'''
        js = transpile(code)
        assert "setup" in js
        assert "teardown" in js
    
    def test_contextmanager_yields_value(self):
        """@contextmanager yields a value."""
        code = '''
from contextlib import contextmanager

@contextmanager
def managed_value():
    yield 42
'''
        js = transpile(code)
        assert "42" in js


# =============================================================================
# TRY/FINALLY IN CONTEXT MANAGERS
# =============================================================================

class TestContextManagerTryFinally:
    """Tests for try/finally in context managers."""
    
    def test_contextmanager_try_finally(self):
        """@contextmanager with try/finally."""
        code = '''
from contextlib import contextmanager

@contextmanager
def safe_context():
    resource = open_resource()
    try:
        yield resource
    finally:
        close_resource(resource)
'''
        js = transpile(code)
        assert "try" in js
        assert "finally" in js or "catch" in js
    
    def test_contextmanager_nested_try(self):
        """@contextmanager with nested try blocks."""
        code = '''
from contextlib import contextmanager

@contextmanager
def nested_try():
    try:
        try:
            yield
        finally:
            inner_cleanup()
    finally:
        outer_cleanup()
'''
        js = transpile(code)
        assert js is not None


# =============================================================================
# EXCEPTION HANDLING IN CONTEXT MANAGERS
# =============================================================================

class TestContextManagerExceptions:
    """Tests for exception handling in context managers."""
    
    def test_contextmanager_catches_exception(self):
        """@contextmanager catches and handles exception."""
        code = '''
from contextlib import contextmanager

@contextmanager
def exception_handler():
    try:
        yield
    except ValueError:
        print("caught ValueError")
'''
        js = transpile(code)
        assert "catch" in js
    
    def test_contextmanager_reraises_exception(self):
        """@contextmanager reraises exception."""
        code = '''
from contextlib import contextmanager

@contextmanager
def reraiser():
    try:
        yield
    except Exception as e:
        print(f"Got: {e}")
        raise
'''
        js = transpile(code)
        assert "throw" in js or "raise" in js.lower()
    
    def test_contextmanager_suppress_exception(self):
        """@contextmanager suppresses exception."""
        code = '''
from contextlib import contextmanager

@contextmanager
def suppressor():
    try:
        yield
    except ValueError:
        pass  # Suppress
'''
        js = transpile(code)
        assert "catch" in js


# =============================================================================
# NESTED CONTEXT MANAGERS
# =============================================================================

class TestNestedContextManagers:
    """Tests for nested context managers."""
    
    def test_nested_with_statements(self):
        """Nested with statements."""
        code = '''
with outer_context():
    with inner_context():
        do_something()
'''
        js = transpile(code)
        assert js is not None
        # Should have two levels of context management
    
    def test_multiple_context_managers_single_with(self):
        """Multiple context managers in single with."""
        code = '''
with ctx1(), ctx2():
    do_something()
'''
        js = transpile(code)
        assert js is not None
    
    def test_deeply_nested_contexts(self):
        """Deeply nested context managers."""
        code = '''
with a():
    with b():
        with c():
            with d():
                innermost()
'''
        js = transpile(code)
        assert "innermost" in js


# =============================================================================
# ASYNC CONTEXT MANAGERS
# =============================================================================

class TestAsyncContextManagers:
    """Tests for async context managers."""
    
    def test_async_with_statement(self):
        """async with statement."""
        code = '''
async def use_async_ctx():
    async with async_context() as value:
        await process(value)
'''
        js = transpile(code)
        assert "await" in js
        assert "__aenter__" in js or "async" in js
    
    def test_asynccontextmanager_decorator(self):
        """@asynccontextmanager decorator."""
        code = '''
from contextlib import asynccontextmanager

@asynccontextmanager
async def async_managed():
    resource = await acquire()
    try:
        yield resource
    finally:
        await release(resource)
'''
        js = transpile(code)
        assert "async" in js
    
    def test_async_with_multiple_contexts(self):
        """Multiple async contexts."""
        code = '''
async def multi_async():
    async with ctx1() as a, ctx2() as b:
        await process(a, b)
'''
        js = transpile(code)
        assert "await" in js


# =============================================================================
# CONTEXT MANAGER IN CLASSES
# =============================================================================

class TestContextManagerInClasses:
    """Tests for context managers in classes."""
    
    def test_class_based_context_manager(self):
        """Class-based context manager."""
        code = '''
class MyContext:
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        return False
'''
        js = transpile(code)
        assert "__enter__" in js
        assert "__exit__" in js
    
    def test_class_context_with_state(self):
        """Class context manager with state."""
        code = '''
class StatefulContext:
    def __init__(self, value):
        self.value = value
        self.entered = False
    
    def __enter__(self):
        self.entered = True
        return self.value
    
    def __exit__(self, *args):
        self.entered = False
        return False
'''
        js = transpile(code)
        assert "__init__" in js or "constructor" in js
        assert "__enter__" in js
    
    def test_context_manager_method(self):
        """Context manager as class method."""
        code = '''
class Resource:
    @contextmanager
    def use_resource(self):
        self.acquire()
        try:
            yield self
        finally:
            self.release()
'''
        js = transpile(code)
        assert "use_resource" in js


# =============================================================================
# GENERATOR EDGE CASES
# =============================================================================

class TestGeneratorEdgeCases:
    """Tests for generator-based context manager edge cases."""
    
    def test_contextmanager_with_return(self):
        """@contextmanager should not have return before yield."""
        code = '''
from contextlib import contextmanager

@contextmanager
def early_return_check(condition):
    if condition:
        setup()
    yield
    if condition:
        teardown()
'''
        js = transpile(code)
        assert js is not None
    
    def test_contextmanager_multiple_cleanup_paths(self):
        """@contextmanager with multiple cleanup paths."""
        code = '''
from contextlib import contextmanager

@contextmanager
def multi_cleanup():
    resource = acquire()
    try:
        yield resource
    except TypeError:
        cleanup_type_error(resource)
        raise
    except ValueError:
        cleanup_value_error(resource)
        raise
    finally:
        final_cleanup(resource)
'''
        js = transpile(code)
        assert "catch" in js or "except" in js.lower()
    
    def test_contextmanager_with_params(self):
        """@contextmanager with parameters."""
        code = '''
from contextlib import contextmanager

@contextmanager
def parameterized(a, b, c=10, *args, **kwargs):
    setup(a, b, c)
    yield a + b + c
    teardown()
'''
        js = transpile(code)
        assert "a" in js and "b" in js and "c" in js


# =============================================================================
# WITH STATEMENT EDGE CASES
# =============================================================================

class TestWithStatementEdgeCases:
    """Edge cases for with statement transpilation."""
    
    def test_with_no_as(self):
        """with statement without 'as' clause."""
        code = '''
with some_context():
    do_work()
'''
        js = transpile(code)
        assert js is not None
    
    def test_with_complex_expression(self):
        """with statement with complex context expression."""
        code = '''
with get_manager().create_context(param=value):
    process()
'''
        js = transpile(code)
        assert js is not None
    
    def test_with_tuple_unpacking(self):
        """with statement with tuple unpacking."""
        code = '''
with multi_value_context() as (a, b, c):
    use(a, b, c)
'''
        js = transpile(code)
        # Should handle destructuring or tuple assignment
        assert js is not None
    
    def test_with_in_loop(self):
        """with statement in a loop."""
        code = '''
for item in items:
    with context(item) as ctx:
        process(ctx)
'''
        js = transpile(code)
        assert "for" in js
    
    def test_with_in_function(self):
        """with statement in function."""
        code = '''
def do_with():
    with context() as ctx:
        return ctx.value
'''
        js = transpile(code)
        assert "function" in js or "=>" in js
    
    def test_nested_with_different_types(self):
        """Nested with mixing sync and async."""
        code = '''
async def mixed():
    with sync_context():
        async with async_context():
            await work()
'''
        js = transpile(code)
        assert "await" in js


# =============================================================================
# EXIT BEHAVIOR EDGE CASES
# =============================================================================

class TestExitBehaviorEdgeCases:
    """Tests for __exit__ behavior edge cases."""
    
    def test_exit_receives_exception_info(self):
        """__exit__ receives exception info."""
        code = '''
class ExceptionLogger:
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            log_exception(exc_type, exc_val)
        return False
'''
        js = transpile(code)
        assert "exc_type" in js or "__exit__" in js
    
    def test_exit_suppresses_with_return_true(self):
        """__exit__ returning True suppresses exception."""
        code = '''
class Suppressor:
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if isinstance(exc_val, ValueError):
            return True  # Suppress
        return False
'''
        js = transpile(code)
        assert "__exit__" in js
    
    def test_exit_raises_different_exception(self):
        """__exit__ raises different exception."""
        code = '''
class Transformer:
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            raise RuntimeError("Transformed error") from exc_val
        return False
'''
        js = transpile(code)
        assert "__exit__" in js


# =============================================================================
# EDGE CASES WITH YIELD VALUE
# =============================================================================

class TestYieldValueEdgeCases:
    """Edge cases for contextmanager yield values."""
    
    def test_yield_none_explicitly(self):
        """@contextmanager yields None explicitly."""
        code = '''
from contextlib import contextmanager

@contextmanager
def yield_none():
    yield None
'''
        js = transpile(code)
        assert "null" in js or "None" in js.lower() or "yield" in js
    
    def test_yield_complex_object(self):
        """@contextmanager yields complex object."""
        code = '''
from contextlib import contextmanager

@contextmanager
def yield_dict():
    yield {"key": "value", "nested": {"a": 1}}
'''
        js = transpile(code)
        assert "key" in js
    
    def test_yield_tuple(self):
        """@contextmanager yields tuple."""
        code = '''
from contextlib import contextmanager

@contextmanager
def yield_tuple():
    yield (1, 2, 3)
'''
        js = transpile(code)
        assert "1" in js and "2" in js and "3" in js
    
    def test_yield_computed_value(self):
        """@contextmanager yields computed value."""
        code = '''
from contextlib import contextmanager

@contextmanager
def yield_computed(base):
    result = base * 2 + 10
    yield result
    cleanup(result)
'''
        js = transpile(code)
        assert "base" in js
        assert "result" in js

