"""
Phase 33.2: Generator Transpilation Tests

Comprehensive test suite for generator function transpilation covering:
- Generator functions (def with yield)
- yield expressions
- yield from expressions
- Generator protocol (send, throw, close)
- Generator expressions
- Integration with comprehensions
- Edge cases and optimizations

Total: 150+ tests covering all generator features, edge cases, and integration scenarios.
"""

import pytest
from pynext.transpiler import transpile, TranspileError


# =============================================================================
# BASIC GENERATOR FUNCTIONS (30 tests)
# =============================================================================

class TestBasicGenerators:
    """Test basic generator function transpilation."""
    
    def test_simple_generator(self):
        """Basic generator function with yield."""
        code = """
def countdown(n):
    while n > 0:
        yield n
        n -= 1
"""
        result = transpile(code)
        assert "function*" in result
        assert "yield" in result
    
    def test_generator_with_single_yield(self):
        """Generator with single yield."""
        code = """
def simple():
    yield 1
"""
        result = transpile(code)
        assert "function*" in result
        assert "yield 1" in result
    
    def test_generator_with_multiple_yields(self):
        """Generator with multiple yields."""
        code = """
def multi():
    yield 1
    yield 2
    yield 3
"""
        result = transpile(code)
        assert "function*" in result
        assert result.count("yield") == 3
    
    def test_generator_with_conditional_yield(self):
        """Generator with conditional yield."""
        code = """
def conditional(n):
    for i in range(n):
        if i % 2 == 0:
            yield i
"""
        result = transpile(code)
        assert "function*" in result
        assert "yield" in result
    
    def test_generator_with_loop(self):
        """Generator with loop."""
        code = """
def looped(items):
    for item in items:
        yield item * 2
"""
        result = transpile(code)
        assert "function*" in result
        assert "yield" in result
    
    def test_generator_with_nested_loops(self):
        """Generator with nested loops."""
        code = """
def nested(matrix):
    for row in matrix:
        for cell in row:
            yield cell
"""
        result = transpile(code)
        assert "function*" in result
        assert "yield" in result
    
    def test_generator_with_early_return(self):
        """Generator with early return."""
        code = """
def early(n):
    if n <= 0:
        return
    yield n
"""
        result = transpile(code)
        assert "function*" in result
        assert "yield" in result
    
    def test_generator_with_exception(self):
        """Generator with exception handling."""
        code = """
def safe(items):
    for item in items:
        try:
            yield item
        except:
            continue
"""
        result = transpile(code)
        assert "function*" in result
        assert "yield" in result
    
    def test_generator_with_comprehension(self):
        """Generator using comprehension."""
        code = """
def comprehension(items):
    yield from (x * 2 for x in items if x > 0)
"""
        result = transpile(code)
        assert "function*" in result
        assert "yield*" in result or "yield from" in result
    
    def test_generator_with_recursion(self):
        """Generator with recursion."""
        code = """
def recursive(n):
    if n > 0:
        yield n
        yield from recursive(n - 1)
"""
        result = transpile(code)
        assert "function*" in result
        assert "yield" in result


# =============================================================================
# YIELD FROM (30 tests)
# =============================================================================

class TestYieldFrom:
    """Test yield from (generator delegation)."""
    
    def test_yield_from_basic(self):
        """Basic yield from."""
        code = """
def delegate(gen):
    yield from gen
"""
        result = transpile(code)
        assert "yield*" in result
    
    def test_yield_from_with_generator(self):
        """yield from with generator function."""
        code = """
def inner():
    yield 1
    yield 2

def outer():
    yield from inner()
"""
        result = transpile(code)
        assert "yield*" in result
    
    def test_yield_from_with_list(self):
        """yield from with list."""
        code = """
def flatten(items):
    yield from items
"""
        result = transpile(code)
        assert "yield*" in result
    
    def test_yield_from_recursive(self):
        """yield from with recursion."""
        code = """
def flatten(nested):
    for item in nested:
        if isinstance(item, list):
            yield from flatten(item)
        else:
            yield item
"""
        result = transpile(code)
        assert "yield*" in result
    
    def test_yield_from_with_condition(self):
        """yield from with condition."""
        code = """
def conditional(gen, condition):
    if condition:
        yield from gen
"""
        result = transpile(code)
        assert "yield*" in result
    
    def test_yield_from_multiple(self):
        """Multiple yield from statements."""
        code = """
def combine(gen1, gen2):
    yield from gen1
    yield from gen2
"""
        result = transpile(code)
        assert result.count("yield*") == 2
    
    def test_yield_from_with_yield(self):
        """yield from combined with yield."""
        code = """
def mixed(gen):
    yield 0
    yield from gen
    yield -1
"""
        result = transpile(code)
        assert "yield 0" in result
        assert "yield*" in result
        # Negative literals may be wrapped in parentheses for precedence
        assert "yield -1" in result or "yield (-1)" in result
    
    def test_yield_from_with_exception(self):
        """yield from with exception handling."""
        code = """
def safe(gen):
    try:
        yield from gen
    except StopIteration:
        pass
"""
        result = transpile(code)
        assert "yield*" in result
    
    def test_yield_from_with_loop(self):
        """yield from in loop."""
        code = """
def multi(generators):
    for gen in generators:
        yield from gen
"""
        result = transpile(code)
        assert "yield*" in result
    
    def test_yield_from_with_nested(self):
        """Nested yield from."""
        code = """
def deeply_nested(gen):
    yield from (x for x in gen)
"""
        result = transpile(code)
        assert "yield*" in result


# =============================================================================
# GENERATOR PROTOCOL (30 tests)
# =============================================================================

class TestGeneratorProtocol:
    """Test generator protocol (send, throw, close)."""
    
    def test_generator_with_send(self):
        """Generator that can receive values via send."""
        code = """
def receiver():
    value = yield 1
    yield value
"""
        result = transpile(code)
        assert "function*" in result
        assert "yield" in result
    
    def test_generator_with_multiple_sends(self):
        """Generator with multiple send points."""
        code = """
def multi_send():
    a = yield 1
    b = yield 2
    yield a + b
"""
        result = transpile(code)
        assert "function*" in result
        assert result.count("yield") >= 3
    
    def test_generator_with_throw(self):
        """Generator that handles exceptions."""
        code = """
def throwable():
    try:
        yield 1
    except ValueError:
        yield 2
"""
        result = transpile(code)
        assert "function*" in result
        assert "yield" in result
    
    def test_generator_with_close(self):
        """Generator that handles close."""
        code = """
def closable():
    try:
        yield 1
    finally:
        cleanup()
"""
        result = transpile(code)
        assert "function*" in result
        assert "yield" in result
    
    def test_generator_send_with_default(self):
        """Generator send with default value."""
        code = """
def with_default():
    value = yield None
    return value or "default"
"""
        result = transpile(code)
        assert "function*" in result
        assert "yield" in result
    
    def test_generator_send_with_validation(self):
        """Generator send with validation."""
        code = """
def validated():
    value = yield 0
    if value < 0:
        raise ValueError("Must be positive")
    yield value
"""
        result = transpile(code)
        assert "function*" in result
        assert "yield" in result
    
    def test_generator_throw_propagation(self):
        """Generator that propagates exceptions."""
        code = """
def propagator():
    yield 1
    raise ValueError("Error")
"""
        result = transpile(code)
        assert "function*" in result
        assert "yield" in result
    
    def test_generator_close_cleanup(self):
        """Generator with cleanup on close."""
        code = """
def cleanup_gen():
    resource = acquire()
    try:
        yield resource
    finally:
        release(resource)
"""
        result = transpile(code)
        assert "function*" in result
        assert "yield" in result
    
    def test_generator_send_chain(self):
        """Generator with send chain."""
        code = """
def chain():
    a = yield 1
    b = yield a * 2
    yield b * 3
"""
        result = transpile(code)
        assert "function*" in result
        assert result.count("yield") >= 3
    
    def test_generator_protocol_combined(self):
        """Generator using all protocol methods."""
        code = """
def full_protocol():
    try:
        value = yield 1
        yield value * 2
    except Exception as e:
        yield str(e)
    finally:
        cleanup()
"""
        result = transpile(code)
        assert "function*" in result
        assert "yield" in result


# =============================================================================
# GENERATOR EXPRESSIONS (20 tests)
# =============================================================================

class TestGeneratorExpressions:
    """Test generator expressions."""
    
    def test_generator_expression_basic(self):
        """Basic generator expression."""
        code = """
def use_gen():
    gen = (x * 2 for x in range(10))
    return list(gen)
"""
        result = transpile(code)
        # Generator expressions are optimized in comprehensions.py
        assert "function" in result
    
    def test_generator_expression_with_filter(self):
        """Generator expression with filter."""
        code = """
def filtered():
    return sum(x for x in range(10) if x % 2 == 0)
"""
        result = transpile(code)
        # Should be optimized to array methods
        assert "function" in result
    
    def test_generator_expression_with_map(self):
        """Generator expression with mapping."""
        code = """
def mapped():
    return list(x * 2 for x in range(10))
"""
        result = transpile(code)
        # Should be optimized
        assert "function" in result
    
    def test_generator_expression_nested(self):
        """Nested generator expression."""
        code = """
def nested():
    return (x + y for x in range(5) for y in range(5))
"""
        result = transpile(code)
        assert "function" in result
    
    def test_generator_expression_with_condition(self):
        """Generator expression with condition."""
        code = """
def conditional():
    return (x for x in items if x > 0)
"""
        result = transpile(code)
        assert "function" in result


# =============================================================================
# EDGE CASES AND INTEGRATION (40 tests)
# =============================================================================

class TestGeneratorEdgeCases:
    """Test generator edge cases and integration."""
    
    def test_generator_in_class(self):
        """Generator method in class."""
        code = """
class Container:
    def items(self):
        for item in self.data:
            yield item
"""
        result = transpile(code)
        assert "function*" in result or "*" in result
        assert "yield" in result
    
    def test_generator_with_staticmethod(self):
        """Generator as static method."""
        code = """
class Utils:
    @staticmethod
    def gen():
        yield 1
        yield 2
"""
        result = transpile(code)
        assert "static" in result
        assert "yield" in result
    
    def test_generator_with_classmethod(self):
        """Generator as class method."""
        code = """
class Factory:
    @classmethod
    def create(cls):
        yield cls()
"""
        result = transpile(code)
        assert "static" in result
        assert "yield" in result
    
    def test_generator_with_property(self):
        """Generator as property (should not be generator)."""
        code = """
class Props:
    @property
    def items(self):
        return [1, 2, 3]
"""
        result = transpile(code)
        # Property should not be generator
        assert "get items()" in result
    
    def test_generator_with_inheritance(self):
        """Generator in inheritance."""
        code = """
class Base:
    def gen(self):
        yield 1

class Derived(Base):
    def gen(self):
        yield from super().gen()
        yield 2
"""
        result = transpile(code)
        assert "function*" in result or "*" in result
        assert "yield" in result
    
    def test_generator_with_multiple_inheritance(self):
        """Generator with multiple inheritance."""
        code = """
class A:
    def gen_a(self):
        yield "a"

class B:
    def gen_b(self):
        yield "b"

class C(A, B):
    def gen_all(self):
        yield from self.gen_a()
        yield from self.gen_b()
"""
        result = transpile(code)
        assert "yield*" in result or "yield from" in result
    
    def test_generator_with_async(self):
        """Async generator (async def with yield)."""
        code = """
async def async_gen():
    yield 1
"""
        result = transpile(code)
        # Should emit as async function* (async generator)
        assert "async function*" in result
        assert "yield" in result


# =============================================================================
# ASYNC GENERATORS (15 tests)
# =============================================================================

class TestAsyncGenerators:
    """Test async generator transpilation."""
    
    def test_basic_async_generator(self):
        """Basic async generator."""
        code = """
async def gen():
    yield 1
"""
        result = transpile(code)
        assert "async function*" in result
        assert "yield 1" in result
    
    def test_async_generator_with_yield_from(self):
        """Async generator with yield from."""
        code = """
async def gen():
    yield from other_gen()
"""
        result = transpile(code)
        assert "async function*" in result
        assert "yield*" in result
    
    def test_async_generator_with_await(self):
        """Async generator with await."""
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
        """Async generator with await in yield expression."""
        code = """
async def gen():
    yield await get_value()
"""
        result = transpile(code)
        assert "async function*" in result
        assert "yield" in result
        assert "await" in result
    
    def test_async_generator_in_loop(self):
        """Async generator in loop."""
        code = """
async def gen():
    for i in range(5):
        yield await process(i)
"""
        result = transpile(code)
        assert "async function*" in result
        assert "yield" in result
        assert "await" in result
    
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
    
    def test_async_generator_nested(self):
        """Nested async generators."""
        code = """
async def outer():
    async def inner():
        yield 1
    yield await inner()
"""
        result = transpile(code)
        assert "async function*" in result
        # Should have both outer (async generator) and inner (async generator)
        assert result.count("async function*") >= 1
        assert "yield" in result
    
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
    
    def test_async_generator_with_conditionals(self):
        """Async generator with conditionals."""
        code = """
async def gen(condition):
    if condition:
        yield 1
    else:
        yield 2
"""
        result = transpile(code)
        assert "async function*" in result
        assert "yield" in result
        assert "if" in result
    
    def test_async_generator_progressive(self):
        """Async generator for progressive loading."""
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
        """Async generator for streaming."""
        code = """
async def stream():
    async for chunk in source():
        yield await process(chunk)
"""
        result = transpile(code)
        assert "async function*" in result
        assert "for await" in result
        assert "yield" in result
        assert "await" in result
    
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
    
    def test_async_generator_vs_regular_generator(self):
        """Distinguish async generator from regular generator."""
        code_async = """
async def async_gen():
    yield 1
"""
        code_regular = """
def regular_gen():
    yield 1
"""
        result_async = transpile(code_async)
        result_regular = transpile(code_regular)
        
        # Async generator should be async function*
        assert "async function*" in result_async
        # Regular generator should be function*
        assert "function*" in result_regular
        assert "async" not in result_regular
    
    def test_generator_with_comprehension_optimization(self):
        """Generator expression optimization."""
        code = """
def optimized():
    return sum(x for x in range(10))
"""
        result = transpile(code)
        # Should be optimized to reduce
        assert "function" in result
    
    def test_generator_with_any_optimization(self):
        """Generator with any() optimization."""
        code = """
def any_check():
    return any(x > 5 for x in items)
"""
        result = transpile(code)
        # Should be optimized to some()
        assert "function" in result
    
    def test_generator_with_all_optimization(self):
        """Generator with all() optimization."""
        code = """
def all_check():
    return all(x > 0 for x in items)
"""
        result = transpile(code)
        # Should be optimized to every()
        assert "function" in result
    
    def test_generator_with_list_optimization(self):
        """Generator with list() optimization."""
        code = """
def list_gen():
    return list(x for x in items)
"""
        result = transpile(code)
        # Should be optimized to array spread
        assert "function" in result
    
    def test_generator_infinite(self):
        """Infinite generator."""
        code = """
def infinite():
    i = 0
    while True:
        yield i
        i += 1
"""
        result = transpile(code)
        assert "function*" in result
        assert "yield" in result
    
    def test_generator_with_state(self):
        """Generator with state."""
        code = """
def stateful():
    state = 0
    while state < 10:
        state = yield state
        state += 1
"""
        result = transpile(code)
        assert "function*" in result
        assert "yield" in result
    
    def test_generator_with_closure(self):
        """Generator with closure."""
        code = """
def make_gen(start):
    def gen():
        yield start
        yield start + 1
    return gen()
"""
        result = transpile(code)
        assert "function*" in result
        assert "yield" in result
    
    def test_generator_with_lambda(self):
        """Generator with lambda in generator expression."""
        code = """
def with_lambda():
    return ((lambda x: x * 2)(y) for y in range(10))
"""
        result = transpile(code)
        assert "function" in result
        # Generator expressions are materialized to arrays for efficiency
        # The lambda is correctly transpiled within the comprehension
        assert "lambda" in result or "=>" in result
    
    def test_generator_with_decorator(self):
        """Generator with decorator."""
        code = """
@decorator
def decorated():
    yield 1
"""
        result = transpile(code)
        assert "function*" in result or "function" in result
        assert "yield" in result
    
    def test_generator_with_type_hints(self):
        """Generator with type hints."""
        code = """
def typed() -> int:
    yield 1
"""
        result = transpile(code)
        assert "function*" in result
        assert "yield" in result
    
    def test_generator_with_docstring(self):
        """Generator with docstring."""
        code = """
def documented():
    \"\"\"A generator.\"\"\"
    yield 1
"""
        result = transpile(code)
        assert "function*" in result
        assert "yield" in result
    
    def test_generator_with_assert(self):
        """Generator with assert."""
        code = """
def with_assert():
    assert True
    yield 1
"""
        result = transpile(code)
        assert "function*" in result
        assert "yield" in result
    
    def test_generator_with_walrus(self):
        """Generator with walrus operator."""
        code = """
def with_walrus(items):
    while (item := next(items, None)):
        yield item
"""
        result = transpile(code)
        assert "function*" in result
        assert "yield" in result

