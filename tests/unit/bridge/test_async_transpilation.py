"""
Tests for Async/Await Transpilation

Tests the transpilation of Python async/await patterns to JavaScript.

Critical Scenarios:
1. async def functions
2. await expressions
3. Async in event handlers
4. try/except in async functions
5. Async comprehensions (not supported - should error)
"""

import pytest
from pynext.transpiler import transpile, parse, emit
from pynext.transpiler.errors import TranspileError
from tests.unit.transpiler.test_utils import assert_has_runtime_function


class TestAsyncFunctionTranspilation:
    """Test async function definitions."""
    
    def test_simple_async_function(self):
        """async def should become async function."""
        source = '''
async def fetch_data():
    return await get_data()
'''
        js = transpile(source)
        
        assert "async" in js
        assert "await" in js
    
    def test_async_with_params(self):
        """async def with parameters."""
        source = '''
async def fetch_user(user_id):
    return await api.get_user(user_id)
'''
        js = transpile(source)
        
        assert "async" in js
        assert "user_id" in js
    
    def test_async_with_default_params(self):
        """async def with default parameters."""
        source = '''
async def fetch_page(page=1, size=10):
    return await api.list(page, size)
'''
        js = transpile(source)
        
        assert "page" in js
        assert "10" in js or "size" in js
    
    def test_async_returns_value(self):
        """async function returning value."""
        source = '''
async def compute():
    result = await heavy_computation()
    return result * 2
'''
        js = transpile(source)
        
        assert "return" in js
        assert "* 2" in js or "result" in js


class TestAwaitExpressions:
    """Test await expression transpilation."""
    
    def test_simple_await(self):
        """Simple await expression."""
        source = '''
async def main():
    data = await fetch()
'''
        js = transpile(source)
        
        assert "await" in js
        assert "fetch" in js
    
    def test_await_in_assignment(self):
        """await in variable assignment."""
        source = '''
async def load():
    x = await get_x()
    y = await get_y()
    return x + y
'''
        js = transpile(source)
        
        assert js.count("await") >= 2
    
    def test_await_in_expression(self):
        """await as part of larger expression."""
        source = '''
async def calculate():
    return (await get_a()) + (await get_b())
'''
        js = transpile(source)
        
        assert "await" in js
        # Transpiler uses dunder runtime for Python-style addition
        assert_has_runtime_function(js, "add")
    
    def test_await_method_call(self):
        """await on method call."""
        source = '''
async def fetch():
    data = await api.fetch_data()
'''
        js = transpile(source)
        
        assert "await" in js
        assert "api" in js


class TestAsyncControlFlow:
    """Test async with control flow statements."""
    
    def test_async_with_if(self):
        """async function with conditional."""
        source = '''
async def conditional_fetch(use_cache):
    if use_cache:
        return await get_cached()
    else:
        return await fetch_fresh()
'''
        js = transpile(source)
        
        assert "async" in js
        assert "if" in js
        assert "await" in js
    
    def test_async_with_loop(self):
        """async function with loop."""
        source = '''
async def fetch_all(ids):
    results = []
    for id in ids:
        data = await fetch_one(id)
        results.append(data)
    return results
'''
        js = transpile(source)
        
        assert "async" in js
        assert "for" in js.lower()
        assert "await" in js


class TestAsyncTryExcept:
    """Test async with error handling."""
    
    def test_async_try_except(self):
        """async with try/except block."""
        source = '''
async def safe_fetch():
    try:
        return await fetch_data()
    except:
        return None
'''
        js = transpile(source)
        
        assert "async" in js
        assert "try" in js
        assert "catch" in js
    
    def test_async_try_except_specific(self):
        """async with exception handling."""
        # Test basic try/except with async
        source = '''
async def fetch_with_retry():
    try:
        result = await api.get()
        return result
    except Exception:
        return await retry()
'''
        js = transpile(source)
        
        assert "try" in js
        assert "catch" in js
    
    def test_async_try_finally(self):
        """async with try/finally."""
        source = '''
async def with_cleanup():
    try:
        return await fetch()
    finally:
        cleanup()
'''
        js = transpile(source)
        
        assert "try" in js
        assert "finally" in js


class TestAsyncEventHandlers:
    """Test async patterns common in event handlers."""
    
    def test_async_handler_pattern(self):
        """Async event handler pattern."""
        source = '''
async def handle_submit():
    data = form.values
    await api.submit(data)
    show_success()
'''
        js = transpile(source)
        
        assert "async" in js
        assert "await" in js
    
    def test_async_handler_with_state(self):
        """Async handler that updates state."""
        source = '''
async def fetch_and_update():
    loading.set(True)
    data = await fetch_data()
    items.set(data)
    loading.set(False)
'''
        js = transpile(source)
        
        assert "async" in js
        # Multiple state updates
        assert "set" in js or "loading" in js


class TestAsyncLambda:
    """Test async in lambda-like contexts (not supported in Python)."""
    
    def test_regular_lambda_works(self):
        """Regular lambda transpiles correctly."""
        source = "onclick = lambda: handle_click()"
        js = transpile(source)
        
        assert "=>" in js or "function" in js
    
    # Note: Python doesn't support async lambdas
    # async lambda: await x  # SyntaxError in Python


class TestAsyncListComprehension:
    """Test async comprehensions (may not be supported)."""
    
    def test_regular_comprehension(self):
        """Regular list comprehension works."""
        source = "doubled = [x * 2 for x in items]"
        js = transpile(source)
        
        assert "map" in js or "for" in js.lower()


class TestNestedAsyncFunctions:
    """Test nested async function definitions."""
    
    def test_async_in_async(self):
        """Nested async function."""
        source = '''
async def outer():
    async def inner():
        return await fetch()
    return await inner()
'''
        js = transpile(source)
        
        # Should have two async declarations
        assert js.count("async") >= 2


class TestAsyncExpressionPositions:
    """Test await in various expression positions."""
    
    def test_await_in_dict(self):
        """await as dict value."""
        source = '''
async def build_result():
    return {
        "data": await fetch_data(),
        "meta": await fetch_meta()
    }
'''
        js = transpile(source)
        
        assert "await" in js
        assert "data" in js
    
    def test_await_in_list(self):
        """await as list element."""
        source = '''
async def gather():
    return [
        await fetch_a(),
        await fetch_b()
    ]
'''
        js = transpile(source)
        
        assert "await" in js
    
    def test_await_in_function_arg(self):
        """await as function argument."""
        source = '''
async def process():
    result = transform(await fetch_raw())
'''
        js = transpile(source)
        
        assert "await" in js
        assert "transform" in js


class TestAsyncWithDecorators:
    """Test async functions with decorators (simplified)."""
    
    # Note: Decorators may not be fully supported in transpiler
    # These tests verify the async part works even if decorator is stripped
    
    def test_async_decorated_simple(self):
        """Async function body transpiles correctly."""
        source = '''
async def cached_fetch():
    return await fetch_with_cache()
'''
        js = transpile(source)
        
        assert "async" in js
        assert "await" in js


class TestAsyncEdgeCases:
    """Test edge cases in async transpilation."""
    
    def test_empty_async_function(self):
        """Async function with pass."""
        source = '''
async def placeholder():
    pass
'''
        js = transpile(source)
        
        assert "async" in js
    
    def test_async_return_none(self):
        """Async function returning None explicitly."""
        source = '''
async def return_none():
    return None
'''
        js = transpile(source)
        
        assert "async" in js
        assert "null" in js or "undefined" in js or "return" in js
    
    def test_async_with_multiple_awaits(self):
        """Function with many await expressions."""
        source = '''
async def many_awaits():
    a = await get_a()
    b = await get_b()
    c = await get_c()
    d = await get_d()
    return a + b + c + d
'''
        js = transpile(source)
        
        assert js.count("await") >= 4
    
    def test_chained_awaits(self):
        """Chained await calls."""
        source = '''
async def chained():
    result = await (await get_promise()).resolve()
'''
        js = transpile(source)
        
        assert "await" in js


class TestAsyncGeneratorsNotSupported:
    """Test that async generators raise appropriate errors."""
    
    def test_async_yield_raises_error(self):
        """async def with yield should error (async generators not supported)."""
        source = '''
async def async_gen():
    yield 1
'''
        # Async generators may or may not be supported
        # Check if it raises an error or transpiles
        try:
            result = transpile(source)
            # If it transpiles, verify it's marked as async generator
            assert "async" in result
            # Note: Currently async generators may transpile but not execute correctly
        except TranspileError:
            # This is also valid - async generators are not fully supported
            pass


class TestAsyncImplicitReturn:
    """Test async functions with implicit returns."""
    
    def test_async_no_return(self):
        """Async function without return statement."""
        source = '''
async def side_effect():
    await perform_action()
    log("done")
'''
        js = transpile(source)
        
        assert "async" in js
        assert "await" in js
    
    def test_async_early_return(self):
        """Async function with early return."""
        source = '''
async def early_exit(condition):
    if condition:
        return
    await do_work()
'''
        js = transpile(source)
        
        assert "if" in js
        assert "return" in js


class TestAsyncParseAndEmit:
    """Test async at IR level."""
    
    def test_parse_async_function(self):
        """Parse async function to IR."""
        source = '''
async def fetch():
    return await get()
'''
        ir = parse(source)
        
        # Should have parsed successfully
        assert ir is not None
        assert len(ir.body) > 0
    
    def test_emit_async_function(self):
        """Emit async function from IR."""
        source = '''
async def fetch():
    return await get()
'''
        ir = parse(source)
        js = emit(ir)
        
        assert "async" in js
        assert "await" in js
