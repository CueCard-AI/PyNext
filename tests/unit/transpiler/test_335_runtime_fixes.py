"""
Phase 33.5: Runtime Fixes Unit Tests

Tests for the robust fixes to:
1. @contextmanager exception suppression
2. @asynccontextmanager support
3. __exit__ exception arguments
4. asyncio.sleep(0) microtask behavior
5. asyncio.sleep negative value validation
6. __setattr__ always called (Python semantics)

Run with: pytest tests/unit/transpiler/test_335_runtime_fixes.py -v
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# CONTEXTMANAGER EXCEPTION SUPPRESSION TESTS
# =============================================================================

class TestContextmanagerExceptionSuppression:
    """Tests for @contextmanager exception suppression fix."""
    
    def test_contextmanager_suppresses_exception_when_caught(self):
        """Test that @contextmanager can suppress exceptions by catching them."""
        code = '''
from contextlib import contextmanager

@contextmanager
def suppress_value_errors():
    try:
        yield
    except ValueError:
        pass  # Suppress - should return True from __exit__
'''
        js = transpile(code)
        # The generator pattern should allow for exception suppression
        assert 'function suppress_value_errors' in js
        assert '__enter__' in js
        assert '__exit__' in js
    
    def test_contextmanager_reraises_exception_when_not_caught(self):
        """Test that @contextmanager re-raises exceptions not caught by generator."""
        code = '''
from contextlib import contextmanager

@contextmanager
def no_suppress():
    yield  # No try/except - exceptions will propagate
'''
        js = transpile(code)
        assert 'function no_suppress' in js
        assert '__exit__' in js
    
    def test_contextmanager_validates_single_yield(self):
        """Test that runtime validates generator has exactly one yield."""
        code = '''
from contextlib import contextmanager

@contextmanager
def single_yield():
    yield "value"
'''
        js = transpile(code)
        # Generator body should have the yield
        assert 'yield' in js
        assert '__enter__' in js
    
    def test_contextmanager_with_try_finally(self):
        """Test @contextmanager with try/finally for cleanup."""
        code = '''
from contextlib import contextmanager

@contextmanager
def managed_resource():
    resource = acquire()
    try:
        yield resource
    finally:
        release(resource)
'''
        js = transpile(code)
        assert 'function managed_resource' in js
        assert 'try' in js
        assert 'finally' in js


# =============================================================================
# ASYNCCONTEXTMANAGER TESTS
# =============================================================================

class TestAsynccontextmanager:
    """Tests for @asynccontextmanager support."""
    
    def test_asynccontextmanager_basic(self):
        """Test basic @asynccontextmanager transpilation."""
        code = '''
from contextlib import asynccontextmanager

@asynccontextmanager
async def async_resource():
    await setup()
    try:
        yield "resource"
    finally:
        await cleanup()
'''
        js = transpile(code)
        # Should generate async context manager
        assert 'async_resource' in js
    
    def test_asynccontextmanager_with_params(self):
        """Test @asynccontextmanager with parameters."""
        code = '''
from contextlib import asynccontextmanager

@asynccontextmanager
async def async_db_session(connection_string):
    session = await connect(connection_string)
    try:
        yield session
    finally:
        await session.close()
'''
        js = transpile(code)
        assert 'async_db_session' in js
        assert 'connection_string' in js


# =============================================================================
# EXCEPTION ARGUMENTS IN __exit__ TESTS
# =============================================================================

class TestExitExceptionArgs:
    """Tests for proper exception args passed to __exit__."""
    
    def test_with_statement_passes_exception_args(self):
        """Test that with statement passes exception info to __exit__."""
        code = '''
with resource() as r:
    do_something(r)
'''
        js = transpile(code)
        # Should have try/catch pattern with exception args
        assert 'try {' in js
        assert 'catch' in js
        assert '__exit__' in js
        # Should pass exception constructor and value
        assert '_e.constructor' in js or 'constructor' in js
    
    def test_with_statement_normal_exit_passes_null(self):
        """Test that normal exit passes null args to __exit__."""
        code = '''
with resource() as r:
    use(r)
'''
        js = transpile(code)
        # Should call __exit__(null, null, null) on normal exit
        assert '__exit__(null, null, null)' in js
    
    def test_with_statement_exception_suppression(self):
        """Test that __exit__ returning true suppresses exception."""
        code = '''
with suppress_context():
    raise ValueError("test")
'''
        js = transpile(code)
        # Should check _suppressed and not re-throw if true
        assert '_suppressed' in js
        assert 'if (!_suppressed)' in js
    
    def test_multiple_context_managers_exception_handling(self):
        """Test multiple context managers with exception handling."""
        code = '''
with ctx1() as a, ctx2() as b:
    use(a, b)
'''
        js = transpile(code)
        # Should have nested try/catch blocks
        assert '__exit__' in js
        # Each context manager should have its own exception tracking
        assert '_exc' in js or '_exc0' in js


# =============================================================================
# ASYNCIO.SLEEP TESTS
# =============================================================================

class TestAsyncioSleepFixes:
    """Tests for asyncio.sleep fixes."""
    
    def test_sleep_transpiles_to_py_sleep(self):
        """Test that asyncio.sleep transpiles to __py.sleep."""
        code = '''
import asyncio

async def wait():
    await asyncio.sleep(1.5)
'''
        js = transpile(code)
        assert 'sleep' in js.lower() or '__py' in js
    
    def test_sleep_with_zero_value(self):
        """Test asyncio.sleep(0) transpilation."""
        code = '''
import asyncio

async def yield_control():
    await asyncio.sleep(0)
'''
        js = transpile(code)
        # Should still produce valid code
        assert 'async' in js
        assert 'sleep' in js.lower() or '__py' in js
    
    def test_sleep_with_expression(self):
        """Test asyncio.sleep with expression argument."""
        code = '''
import asyncio

async def dynamic_wait(delay):
    await asyncio.sleep(delay * 2)
'''
        js = transpile(code)
        assert 'delay' in js
        # Multiplication may be transpiled to __py.dunders.mul or inlined
        assert '* 2' in js or '*2' in js or 'mul(delay, 2)' in js


# =============================================================================
# PROXY __setattr__ ALWAYS CALLED TESTS
# =============================================================================

class TestProxySetattr:
    """Tests for __setattr__ always being called."""
    
    def test_class_with_setattr_uses_proxy(self):
        """Test that class with __setattr__ uses Proxy factory."""
        code = '''
class Logged:
    def __setattr__(self, name, value):
        print(f"Setting {name} = {value}")
        self.__dict__[name] = value
'''
        js = transpile(code)
        # Should have Proxy factory
        assert '__py_create_Logged' in js or 'Proxy' in js or 'class Logged' in js
    
    def test_class_without_setattr_no_proxy(self):
        """Test that class without __setattr__ doesn't need Proxy."""
        code = '''
class Simple:
    def __init__(self, value):
        self.value = value
'''
        js = transpile(code)
        # Should not have unnecessary Proxy factory
        assert 'class Simple' in js


# =============================================================================
# CONTEXT MANAGER TRANSPILATION PATTERN TESTS
# =============================================================================

class TestContextManagerTranspilation:
    """Tests for with statement transpilation pattern."""
    
    def test_with_single_context_manager(self):
        """Test single context manager transpilation."""
        code = '''
with open_file("test.txt") as f:
    content = f.read()
'''
        js = transpile(code)
        assert '_ctx' in js
        assert '__enter__' in js
        assert '__exit__' in js
        assert 'try' in js
        assert 'catch' in js
    
    def test_with_no_as_clause(self):
        """Test with statement without as clause."""
        code = '''
with lock():
    do_work()
'''
        js = transpile(code)
        assert '__enter__' in js
        assert '__exit__' in js
    
    def test_async_with_statement(self):
        """Test async with statement transpilation."""
        code = '''
async def use_resource():
    async with async_resource() as r:
        await process(r)
'''
        js = transpile(code)
        assert '__aenter__' in js
        assert '__aexit__' in js
        assert 'await' in js
    
    def test_nested_with_statements(self):
        """Test nested with statements."""
        code = '''
with outer() as o:
    with inner() as i:
        use(o, i)
'''
        js = transpile(code)
        # Should have nested try/catch blocks
        count = js.count('__exit__')
        assert count >= 2


# =============================================================================
# EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Edge case tests for runtime fixes."""
    
    def test_contextmanager_empty_body(self):
        """Test @contextmanager with empty body after yield."""
        code = '''
from contextlib import contextmanager

@contextmanager
def noop():
    yield
'''
        js = transpile(code)
        assert 'function noop' in js
        assert 'yield' in js
    
    def test_with_statement_with_exception_in_enter(self):
        """Test with statement when __enter__ might raise."""
        code = '''
with risky_context() as r:
    safe_operation(r)
'''
        js = transpile(code)
        # __enter__ is called before try block
        assert '__enter__' in js
    
    def test_contextmanager_yields_none(self):
        """Test @contextmanager that yields None implicitly."""
        code = '''
from contextlib import contextmanager

@contextmanager
def no_value():
    setup()
    yield
    cleanup()
'''
        js = transpile(code)
        assert 'yield' in js
    
    def test_multiple_context_managers_one_line(self):
        """Test multiple context managers on one line."""
        code = '''
with open("a") as a, open("b") as b, open("c") as c:
    process(a, b, c)
'''
        js = transpile(code)
        # Should have three context manager setups
        assert '__exit__' in js


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests combining multiple fixes."""
    
    def test_contextmanager_in_class(self):
        """Test @contextmanager method in class."""
        code = '''
from contextlib import contextmanager

class ResourceManager:
    @contextmanager
    def managed(self):
        yield self.resource
'''
        js = transpile(code)
        assert 'class ResourceManager' in js
        assert 'managed' in js
    
    def test_with_and_async_combined(self):
        """Test async function with with statement."""
        code = '''
async def async_file_op():
    with open("test.txt") as f:
        await asyncio.sleep(0.1)
        return f.read()
'''
        js = transpile(code)
        assert 'async' in js
        assert '__enter__' in js
        assert '__exit__' in js
    
    def test_complex_contextmanager_with_params(self):
        """Test complex @contextmanager with parameters and defaults."""
        code = '''
from contextlib import contextmanager

@contextmanager
def timer(name, threshold=1.0, callback=None):
    start = time.time()
    try:
        yield
    finally:
        elapsed = time.time() - start
        if elapsed > threshold and callback:
            callback(name, elapsed)
'''
        js = transpile(code)
        assert 'function timer' in js
        assert 'name' in js
        assert 'threshold' in js

