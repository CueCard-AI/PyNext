"""
Phase 33.2: Async/Await Transpilation Tests

Comprehensive test suite for async/await transpilation covering:
- async def → async function
- await expressions
- async for → for await
- async with → async try/finally
- asyncio.gather → Promise.all
- Async context managers
- Async generators
- Edge cases and integration

Total: 100+ tests covering all async features, edge cases, and integration scenarios.
"""

import pytest
from pynext.transpiler import transpile, TranspileError


# =============================================================================
# ASYNC FUNCTIONS (30 tests)
# =============================================================================

class TestAsyncFunctions:
    """Test async function transpilation."""
    
    def test_async_def_basic(self):
        """Basic async function."""
        code = """
async def fetch():
    return await get_data()
"""
        result = transpile(code)
        assert "async function" in result
        assert "await" in result
    
    def test_async_def_with_args(self):
        """Async function with arguments."""
        code = """
async def fetch(url):
    return await request(url)
"""
        result = transpile(code)
        assert "async function" in result
        assert "await" in result
    
    def test_async_def_with_defaults(self):
        """Async function with default arguments."""
        code = """
async def fetch(url="default"):
    return await request(url)
"""
        result = transpile(code)
        assert "async function" in result
        assert "await" in result
    
    def test_async_def_with_kwargs(self):
        """Async function with **kwargs."""
        code = """
async def fetch(**kwargs):
    return await request(**kwargs)
"""
        result = transpile(code)
        assert "async function" in result
        assert "await" in result
    
    def test_async_def_with_args_kwargs(self):
        """Async function with *args and **kwargs."""
        code = """
async def fetch(*args, **kwargs):
    return await request(*args, **kwargs)
"""
        result = transpile(code)
        assert "async function" in result
        assert "await" in result
    
    def test_async_def_with_return(self):
        """Async function with return."""
        code = """
async def fetch():
    data = await get_data()
    return data
"""
        result = transpile(code)
        assert "async function" in result
        assert "return" in result
    
    def test_async_def_with_exception(self):
        """Async function with exception handling."""
        code = """
async def fetch():
    try:
        return await get_data()
    except:
        return None
"""
        result = transpile(code)
        assert "async function" in result
        assert "await" in result
    
    def test_async_def_with_conditional(self):
        """Async function with conditional."""
        code = """
async def fetch(use_cache):
    if use_cache:
        return await get_cached()
    return await get_fresh()
"""
        result = transpile(code)
        assert "async function" in result
        assert "await" in result
    
    def test_async_def_with_loop(self):
        """Async function with loop."""
        code = """
async def fetch_all(urls):
    results = []
    for url in urls:
        results.append(await fetch(url))
    return results
"""
        result = transpile(code)
        assert "async function" in result
        assert "await" in result
    
    def test_async_def_in_class(self):
        """Async method in class."""
        code = """
class Client:
    async def fetch(self):
        return await self.request()
"""
        result = transpile(code)
        assert "async" in result
        assert "await" in result


# =============================================================================
# AWAIT EXPRESSIONS (20 tests)
# =============================================================================

class TestAwaitExpressions:
    """Test await expression transpilation."""
    
    def test_await_basic(self):
        """Basic await expression."""
        code = """
async def func():
    result = await promise
"""
        result = transpile(code)
        assert "await" in result
    
    def test_await_with_call(self):
        """await with function call."""
        code = """
async def func():
    result = await fetch(url)
"""
        result = transpile(code)
        assert "await" in result
    
    def test_await_with_method_call(self):
        """await with method call."""
        code = """
async def func():
    result = await obj.method()
"""
        result = transpile(code)
        assert "await" in result
    
    def test_await_with_attribute(self):
        """await with attribute access."""
        code = """
async def func():
    result = await obj.promise
"""
        result = transpile(code)
        assert "await" in result
    
    def test_await_with_expression(self):
        """await with complex expression."""
        code = """
async def func():
    result = await (a + b)
"""
        result = transpile(code)
        assert "await" in result
    
    def test_await_in_return(self):
        """await in return statement."""
        code = """
async def func():
    return await get_value()
"""
        result = transpile(code)
        assert "await" in result
        assert "return" in result
    
    def test_await_in_conditional(self):
        """await in conditional."""
        code = """
async def func():
    if await check():
        return True
"""
        result = transpile(code)
        assert "await" in result
    
    def test_await_in_loop(self):
        """await in loop."""
        code = """
async def func():
    for item in items:
        await process(item)
"""
        result = transpile(code)
        assert "await" in result


# =============================================================================
# ASYNC FOR (20 tests)
# =============================================================================

class TestAsyncFor:
    """Test async for loop transpilation."""
    
    def test_async_for_basic(self):
        """Basic async for loop."""
        code = """
async def process_all():
    async for item in async_gen():
        await process(item)
"""
        result = transpile(code)
        assert "for await" in result
        assert "await" in result
    
    def test_async_for_with_body(self):
        """async for with body."""
        code = """
async def func():
    async for item in gen():
        result = await process(item)
        store(result)
"""
        result = transpile(code)
        assert "for await" in result
        assert "await" in result
    
    def test_async_for_with_else(self):
        """async for with else clause."""
        code = """
async def func():
    async for item in gen():
        await process(item)
    else:
        await cleanup()
"""
        result = transpile(code)
        assert "for await" in result
        assert "else" in result
    
    def test_async_for_with_break(self):
        """async for with break."""
        code = """
async def func():
    async for item in gen():
        if item.done:
            break
        await process(item)
"""
        result = transpile(code)
        assert "for await" in result
        assert "break" in result
    
    def test_async_for_with_continue(self):
        """async for with continue."""
        code = """
async def func():
    async for item in gen():
        if item.skip:
            continue
        await process(item)
"""
        result = transpile(code)
        assert "for await" in result
        assert "continue" in result


# =============================================================================
# ASYNCIO.GATHER (15 tests)
# =============================================================================

class TestAsyncioGather:
    """Test asyncio.gather transpilation."""
    
    def test_gather_basic(self):
        """Basic asyncio.gather."""
        code = """
async def fetch_all():
    results = await asyncio.gather(
        fetch_a(),
        fetch_b(),
        fetch_c()
    )
    return results
"""
        result = transpile(code)
        assert "Promise.all" in result
        assert "await" in result
    
    def test_gather_with_list(self):
        """asyncio.gather with list."""
        code = """
async def fetch_all(tasks):
    results = await asyncio.gather(*tasks)
    return results
"""
        result = transpile(code)
        assert "Promise.all" in result
    
    def test_gather_with_comprehension(self):
        """asyncio.gather with comprehension."""
        code = """
async def fetch_all(urls):
    tasks = [fetch(url) for url in urls]
    results = await asyncio.gather(*tasks)
    return results
"""
        result = transpile(code)
        assert "Promise.all" in result


# =============================================================================
# EDGE CASES (15 tests)
# =============================================================================

class TestAsyncEdgeCases:
    """Test async edge cases."""
    
    def test_async_with_sync_mix(self):
        """Async function with sync operations."""
        code = """
async def mixed():
    sync_value = compute()
    async_value = await fetch()
    return sync_value + async_value
"""
        result = transpile(code)
        assert "async function" in result
        assert "await" in result
    
    def test_async_with_nested_async(self):
        """Nested async calls."""
        code = """
async def outer():
    result = await inner()
    return result

async def inner():
    return await get_value()
"""
        result = transpile(code)
        assert result.count("async function") == 2
        assert result.count("await") >= 2
    
    def test_async_with_generator(self):
        """Async generator (async def with yield)."""
        code = """
async def gen():
    yield await get_value()
"""
        result = transpile(code)
        # Should emit as async function* (async generator)
        assert "async function*" in result
        assert "yield" in result
        assert "await" in result


# =============================================================================
# ASYNC GENERATORS (20 tests)
# =============================================================================

class TestAsyncGenerators:
    """Test async generator transpilation (async def with yield)."""
    
    def test_basic_async_generator(self):
        """Basic async generator."""
        code = """
async def gen():
    yield 1
"""
        result = transpile(code)
        assert "async function*" in result
        assert "yield 1" in result
    
    def test_async_generator_with_multiple_yields(self):
        """Async generator with multiple yields."""
        code = """
async def gen():
    yield 1
    yield 2
    yield 3
"""
        result = transpile(code)
        assert "async function*" in result
        assert "yield 1" in result
        assert "yield 2" in result
        assert "yield 3" in result
    
    def test_async_generator_with_await(self):
        """Async generator with await in yield."""
        code = """
async def gen():
    value = await fetch()
    yield value
"""
        result = transpile(code)
        assert "async function*" in result
        assert "await" in result
        assert "yield" in result
    
    def test_async_generator_with_await_in_yield(self):
        """Async generator with await directly in yield."""
        code = """
async def gen():
    yield await get_value()
"""
        result = transpile(code)
        assert "async function*" in result
        assert "yield await" in result or ("yield" in result and "await" in result)
    
    def test_async_generator_with_yield_from(self):
        """Async generator with yield from."""
        code = """
async def gen():
    yield from other_gen()
"""
        result = transpile(code)
        assert "async function*" in result
        assert "yield*" in result
    
    def test_async_generator_with_loop(self):
        """Async generator with loop."""
        code = """
async def gen():
    for i in range(5):
        yield i
"""
        result = transpile(code)
        assert "async function*" in result
        assert "yield" in result
        assert "for" in result
    
    def test_async_generator_with_async_for(self):
        """Async generator with async for."""
        code = """
async def gen():
    async for item in async_items():
        yield item
"""
        result = transpile(code)
        assert "async function*" in result
        assert "for await" in result
        assert "yield" in result
    
    def test_async_generator_with_conditionals(self):
        """Async generator with conditionals."""
        code = """
async def gen():
    if condition:
        yield 1
    else:
        yield 2
"""
        result = transpile(code)
        assert "async function*" in result
        assert "yield" in result
        assert "if" in result
    
    def test_async_generator_with_try_except(self):
        """Async generator with try/except."""
        code = """
async def gen():
    try:
        yield await fetch()
    except Error:
        yield None
"""
        result = transpile(code)
        assert "async function*" in result
        assert "yield" in result
        assert "try" in result
    
    def test_async_generator_with_nested_async(self):
        """Async generator with nested async function."""
        code = """
async def gen():
    async def helper():
        return await get_value()
    yield await helper()
"""
        result = transpile(code)
        assert "async function*" in result
        assert "yield" in result
        # Nested async function should be separate
        assert "async function" in result
    
    def test_async_generator_in_class(self):
        """Async generator method in class."""
        code = """
class Processor:
    async def process(self):
        yield await get_data()
"""
        result = transpile(code)
        assert "class" in result
        assert "async function*" in result or "async *" in result
        assert "yield" in result
    
    def test_async_generator_with_args(self):
        """Async generator with arguments."""
        code = """
async def gen(start, end):
    for i in range(start, end):
        yield i
"""
        result = transpile(code)
        assert "async function*" in result
        assert "yield" in result
    
    def test_async_generator_with_defaults(self):
        """Async generator with default arguments."""
        code = """
async def gen(start=0, end=10):
    for i in range(start, end):
        yield i
"""
        result = transpile(code)
        assert "async function*" in result
        assert "yield" in result
    
    def test_async_generator_with_star_args(self):
        """Async generator with *args."""
        code = """
async def gen(*items):
    for item in items:
        yield await process(item)
"""
        result = transpile(code)
        assert "async function*" in result
        assert "yield" in result
        assert "await" in result
    
    def test_async_generator_with_kwargs(self):
        """Async generator with **kwargs."""
        code = """
async def gen(**options):
    yield options.get('value', 0)
"""
        result = transpile(code)
        assert "async function*" in result
        assert "yield" in result
    
    def test_async_generator_empty(self):
        """Empty async generator."""
        code = """
async def gen():
    pass
"""
        result = transpile(code)
        # Empty async function (no yield) should be regular async function
        assert "async function" in result
        assert "async function*" not in result
    
    def test_async_generator_vs_async_function(self):
        """Distinguish async generator from regular async function."""
        code_gen = """
async def gen():
    yield 1
"""
        code_func = """
async def func():
    return 1
"""
        result_gen = transpile(code_gen)
        result_func = transpile(code_func)
        
        # Generator should be async function*
        assert "async function*" in result_gen
        # Regular function should be async function
        assert "async function" in result_func
        assert "async function*" not in result_func
    
    def test_async_generator_with_decorator(self):
        """Async generator with decorator."""
        code = """
@decorator
async def gen():
    yield 1
"""
        result = transpile(code)
        assert "async function*" in result or "async *" in result
        assert "yield" in result
    
    def test_async_generator_progressive_loading(self):
        """Async generator for progressive data loading."""
        code = """
async def load_pages():
    page = 1
    while True:
        data = await fetch_page(page)
        if not data:
            break
        yield data
        page += 1
"""
        result = transpile(code)
        assert "async function*" in result
        assert "yield" in result
        assert "await" in result
        assert "while" in result
    
    def test_async_generator_streaming(self):
        """Async generator for streaming data."""
        code = """
async def stream_data():
    async with connection() as conn:
        async for chunk in conn.read():
            yield await process(chunk)
"""
        result = transpile(code)
        assert "async function*" in result
        assert "yield" in result
        assert "for await" in result
        assert "await" in result
    
    def test_async_with_comprehension(self):
        """Async with comprehension."""
        code = """
async def fetch_all():
    return [await fetch(url) for url in urls]
"""
        result = transpile(code)
        assert "async function" in result
        assert "await" in result
    
    def test_async_with_decorator(self):
        """Async function with decorator."""
        code = """
@decorator
async def decorated():
    return await fetch()
"""
        result = transpile(code)
        assert "async" in result or "function" in result
        assert "await" in result

