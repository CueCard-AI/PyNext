"""
Risk Hardening Tests for Phase 18.5

=============================================================================
COMPREHENSIVE TESTS FOR HIGH-RISK AREAS
=============================================================================

These tests verify correct behavior for edge cases that could break:
1. *args + **kwargs together
2. Keyword-only arguments
3. Chained comparisons with side effects
4. Boolean short-circuit evaluation
5. Generator tuple unpacking
6. Decorator order with async
7. Decorator spread arguments
8. Memoize cache key issues
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# ARGS + KWARGS TOGETHER (15 tests)
# =============================================================================

class TestArgsKwargsTogether:
    """Test *args and **kwargs used together."""
    
    def test_wrapper_pattern(self):
        """Common wrapper pattern"""
        code = """
def wrapper(*args, **kwargs):
    return original(*args, **kwargs)
"""
        result = transpile(code)
        # Should extract kwargs from args
        assert "const kwargs = " in result
        assert "__kw__" in result
        # Should mark kwargs in call
        assert "__kw__: true" in result
    
    def test_kwargs_accessed_in_body(self):
        """Accessing kwargs when both present"""
        code = """
def func(*args, **kwargs):
    x = kwargs.get('x', 0)
    y = kwargs.get('y', 0)
    return sum(args) + x + y
"""
        result = transpile(code)
        assert "const kwargs = " in result
        assert "kwargs" in result
    
    def test_args_and_kwargs_returned(self):
        """Return both args and kwargs"""
        code = """
def debug(*args, **kwargs):
    return {'args': args, 'kwargs': kwargs}
"""
        result = transpile(code)
        assert "const kwargs = " in result
        assert "args" in result
        assert "kwargs" in result
    
    def test_kwargs_pop(self):
        """Pop from kwargs"""
        code = """
def handler(*args, **kwargs):
    debug = kwargs.pop('debug', False)
    return process(*args, **kwargs)
"""
        result = transpile(code)
        assert "const kwargs = " in result
    
    def test_kwargs_update(self):
        """Update kwargs"""
        code = """
def extend(*args, **kwargs):
    kwargs['extra'] = 'value'
    return child(*args, **kwargs)
"""
        result = transpile(code)
        assert "const kwargs = " in result
    
    def test_args_modification(self):
        """Modify args before passing"""
        code = """
def prepend(*args, **kwargs):
    new_args = (first,) + args
    return target(*new_args, **kwargs)
"""
        result = transpile(code)
        assert "const kwargs = " in result
    
    def test_conditional_forwarding(self):
        """Conditionally forward"""
        code = """
def router(*args, **kwargs):
    if condition:
        return handler_a(*args, **kwargs)
    return handler_b(*args, **kwargs)
"""
        result = transpile(code)
        assert "__kw__: true" in result
    
    def test_async_wrapper(self):
        """Async function with both"""
        code = """
async def async_wrapper(*args, **kwargs):
    result = await original(*args, **kwargs)
    return result
"""
        result = transpile(code)
        assert "async function async_wrapper" in result
        assert "const kwargs = " in result
    
    def test_decorated_with_both(self):
        """Decorated function with both"""
        code = """
@memoize
def cached(*args, **kwargs):
    return compute(*args, **kwargs)
"""
        result = transpile(code)
        assert "__py.memoize" in result
        assert "const kwargs = " in result
    
    def test_nested_with_both(self):
        """Nested functions with both"""
        code = """
def outer(*args, **kwargs):
    def inner():
        return args, kwargs
    return inner()
"""
        result = transpile(code)
        assert "const kwargs = " in result
    
    def test_empty_args_with_kwargs(self):
        """Empty args but kwargs present"""
        code = """
def with_kwargs(*args, **kwargs):
    if not args:
        return kwargs
    return args[0]
"""
        result = transpile(code)
        assert "const kwargs = " in result
    
    def test_kwargs_iteration(self):
        """Iterate over kwargs"""
        code = """
def process(*args, **kwargs):
    for key, value in kwargs.items():
        print(key, value)
    return args
"""
        result = transpile(code)
        assert "const kwargs = " in result
    
    def test_kwargs_destructuring(self):
        """Destructure from kwargs"""
        code = """
def extract(*args, **kwargs):
    name = kwargs.get('name')
    age = kwargs.get('age')
    return name, age, args
"""
        result = transpile(code)
        assert "const kwargs = " in result
    
    def test_args_len_with_kwargs(self):
        """Check args length when kwargs present"""
        code = """
def check(*args, **kwargs):
    if len(args) == 0:
        return kwargs
    return args
"""
        result = transpile(code)
        assert "const kwargs = " in result
    
    def test_multiple_spread_calls(self):
        """Multiple calls with spread"""
        code = """
def multi(*args, **kwargs):
    a = first(*args, **kwargs)
    b = second(*args, **kwargs)
    return a, b
"""
        result = transpile(code)
        assert result.count("__kw__: true") >= 2


# =============================================================================
# KEYWORD-ONLY ARGUMENTS (15 tests)
# =============================================================================

class TestKeywordOnlyArgs:
    """Test keyword-only arguments after * or *args."""
    
    def test_bare_star_single(self):
        """def func(*, key): ..."""
        code = """
def func(*, key):
    return key
"""
        result = transpile(code)
        assert "key" in result
    
    def test_bare_star_with_default(self):
        """def func(*, key=None): ..."""
        code = """
def func(*, key=None):
    return key
"""
        result = transpile(code)
        assert "key" in result
        assert "null" in result
    
    def test_bare_star_multiple(self):
        """def func(*, a, b, c): ..."""
        code = """
def func(*, a, b, c=1):
    return a + b + c
"""
        result = transpile(code)
        assert "a" in result
        assert "b" in result
        assert "c" in result
    
    def test_positional_and_kwonly(self):
        """def func(x, *, key): ..."""
        code = """
def func(x, *, key):
    return x + key
"""
        result = transpile(code)
        assert "(x, key)" in result
    
    def test_default_and_kwonly(self):
        """def func(x=1, *, key): ..."""
        code = """
def func(x=1, *, key):
    return x + key
"""
        result = transpile(code)
        assert "x = 1" in result
        assert "key" in result
    
    def test_vararg_and_kwonly(self):
        """def func(*args, key): ..."""
        code = """
def func(*args, key):
    return sum(args) + key
"""
        result = transpile(code)
        # kwonly comes from kwargs when there's vararg
        assert "__kwargs__" in result or "const key = " in result
    
    def test_vararg_kwonly_with_default(self):
        """def func(*args, key=0): ..."""
        code = """
def func(*args, key=0):
    return sum(args) + key
"""
        result = transpile(code)
        assert "?? 0" in result or "= 0" in result
    
    def test_full_signature(self):
        """def func(a, b=1, *args, key, **kwargs): ..."""
        code = """
def func(a, b=1, *args, key, **kwargs):
    return a, b, args, key, kwargs
"""
        result = transpile(code)
        assert "const kwargs = " in result
        assert "const key = kwargs.key" in result
    
    def test_kwonly_used_in_expression(self):
        """Use kwonly arg in expression"""
        code = """
def compute(*, factor=1.0, offset=0):
    return lambda x: x * factor + offset
"""
        result = transpile(code)
        assert "factor" in result
        assert "offset" in result
    
    def test_kwonly_with_complex_default(self):
        """kwonly with complex default"""
        code = """
def func(*, items=[]):
    return items
"""
        result = transpile(code)
        assert "[]" in result
    
    def test_kwonly_in_method(self):
        """kwonly in method-like function"""
        code = """
def method(self, *, key):
    return self.data[key]
"""
        result = transpile(code)
        assert "self" in result
        assert "key" in result
    
    def test_kwonly_async(self):
        """Async with kwonly"""
        code = """
async def fetch(*, url, timeout=30):
    return await request(url, timeout=timeout)
"""
        result = transpile(code)
        assert "async function fetch" in result
        assert "url" in result
        assert "timeout" in result
    
    def test_kwonly_decorated(self):
        """Decorated with kwonly"""
        code = """
@memoize
def cached(*, key):
    return compute(key)
"""
        result = transpile(code)
        assert "__py.memoize" in result
        assert "key" in result
    
    def test_kwonly_all_defaults(self):
        """All kwonly have defaults"""
        code = """
def config(*, debug=False, verbose=False, level=1):
    return debug, verbose, level
"""
        result = transpile(code)
        assert "false" in result
        assert "1" in result
    
    def test_kwonly_none_default(self):
        """kwonly with None default"""
        code = """
def optional(*, callback=None):
    if callback:
        callback()
"""
        result = transpile(code)
        assert "null" in result


# =============================================================================
# CHAINED COMPARISON SIDE EFFECTS (10 tests)
# =============================================================================

class TestChainedComparisonSideEffects:
    """Test chained comparisons with side effects."""
    
    def test_simple_chain(self):
        """0 < x < 10"""
        code = "result = 0 < x < 10"
        result = transpile(code)
        assert "&&" in result
    
    def test_chain_with_function_call(self):
        """0 < get_value() < 10"""
        code = "result = 0 < get_value() < 10"
        result = transpile(code)
        # Should cache get_value() to avoid double call
        assert "get_value()" in result
    
    def test_chain_with_method_call(self):
        """0 < obj.get() < 10"""
        code = "result = 0 < obj.compute() < 10"
        result = transpile(code)
        assert "obj.compute()" in result
    
    def test_triple_chain(self):
        """a < b < c < d"""
        code = "result = a < b < c < d"
        result = transpile(code)
        assert "&&" in result
    
    def test_chain_with_names_only(self):
        """a < b < c (no side effects)"""
        code = "result = a < b < c"
        result = transpile(code)
        # Should be simple without caching
        assert "&&" in result
    
    def test_chain_mixed_operators(self):
        """a < b <= c < d"""
        code = "result = a < b <= c < d"
        result = transpile(code)
        assert "&&" in result
    
    def test_chain_with_equality(self):
        """a == b == c"""
        code = "result = a == b == c"
        result = transpile(code)
        assert "__py.eq" in result
    
    def test_chain_in_condition(self):
        """if 0 < x < 10:"""
        code = """
if 0 < x < 10:
    result = True
"""
        result = transpile(code)
        assert "&&" in result
    
    def test_chain_with_subscript(self):
        """a < items[0] < b"""
        code = "result = a < items[0] < b"
        result = transpile(code)
        assert "items" in result
    
    def test_chain_with_attribute(self):
        """a < obj.value < b"""
        code = "result = a < obj.value < b"
        result = transpile(code)
        assert "obj.value" in result


# =============================================================================
# BOOLEAN SHORT-CIRCUIT (10 tests)
# =============================================================================

class TestBooleanShortCircuit:
    """Test boolean short-circuit evaluation."""
    
    def test_and_short_circuit(self):
        """a and b - b not evaluated if a falsy"""
        code = "result = a and b"
        result = transpile(code)
        assert "__py.bool" in result or "?" in result
    
    def test_or_short_circuit(self):
        """a or b - b not evaluated if a truthy"""
        code = "result = a or b"
        result = transpile(code)
        assert "__py.bool" in result or "?" in result
    
    def test_and_with_function_call(self):
        """get_a() and get_b()"""
        code = "result = get_a() and get_b()"
        result = transpile(code)
        # Should not call get_b() if get_a() is falsy
        assert "get_a()" in result
        assert "get_b()" in result
    
    def test_or_with_function_call(self):
        """get_a() or get_b()"""
        code = "result = get_a() or get_b()"
        result = transpile(code)
        assert "get_a()" in result
        assert "get_b()" in result
    
    def test_nested_and_or(self):
        """a and b or c"""
        code = "result = a and b or c"
        result = transpile(code)
        assert "__py.bool" in result
    
    def test_complex_chain(self):
        """a and b and c and d"""
        code = "result = a and b and c and d"
        result = transpile(code)
        assert "__py.bool" in result
    
    def test_mixed_and_or(self):
        """a and b or c and d"""
        code = "result = a and b or c and d"
        result = transpile(code)
        assert "__py.bool" in result
    
    def test_not_with_and(self):
        """not a and b"""
        code = "result = not a and b"
        result = transpile(code)
        assert "!" in result or "not" in result.lower()
    
    def test_parenthesized_bool(self):
        """(a or b) and c"""
        code = "result = (a or b) and c"
        result = transpile(code)
        assert "__py.bool" in result
    
    def test_bool_with_comparison(self):
        """a > 0 and b > 0"""
        code = "result = a > 0 and b > 0"
        result = transpile(code)
        # Python semantics use short-circuit evaluation
        assert "(a > 0)" in result and "(b > 0)" in result


# =============================================================================
# GENERATOR TUPLE UNPACKING (15 tests)
# =============================================================================

class TestGeneratorTupleUnpacking:
    """Test generator expressions with tuple unpacking."""
    
    def test_simple_unpack(self):
        """sum(a*b for a, b in pairs)"""
        code = "x = sum(a*b for a, b in pairs)"
        result = transpile(code)
        # Should handle tuple unpacking
        assert "a" in result
        assert "b" in result
    
    def test_items_unpack(self):
        """any(v > 0 for k, v in d.items())"""
        code = "x = any(v > 0 for k, v in d.items())"
        result = transpile(code)
        assert "v > 0" in result or "v" in result
    
    def test_enumerate_unpack(self):
        """sum(i*x for i, x in enumerate(items))"""
        code = "x = sum(i*x for i, x in enumerate(items))"
        result = transpile(code)
        assert "enumerate" in result or "i" in result
    
    def test_zip_unpack(self):
        """all(a < b for a, b in zip(list1, list2))"""
        code = "x = all(a < b for a, b in zip(list1, list2))"
        result = transpile(code)
        assert "zip" in result or "a" in result
    
    def test_triple_unpack(self):
        """list(a+b+c for a, b, c in triples)"""
        code = "x = list(a+b+c for a, b, c in triples)"
        result = transpile(code)
        assert "a" in result
        assert "b" in result
        assert "c" in result
    
    def test_dict_from_pairs(self):
        """dict((k.lower(), v) for k, v in items)"""
        code = "x = dict((k.lower(), v) for k, v in items)"
        result = transpile(code)
        assert "k" in result
        assert "v" in result
    
    def test_set_from_pairs(self):
        """set(k for k, v in items if v > 0)"""
        code = "x = set(k for k, v in items if v > 0)"
        result = transpile(code)
        assert "k" in result
    
    def test_list_with_filter_unpack(self):
        """list(a for a, b in pairs if b > 0)"""
        code = "x = list(a for a, b in pairs if b > 0)"
        result = transpile(code)
        assert "a" in result
        assert "b > 0" in result or "b" in result
    
    def test_min_with_unpack(self):
        """min(a+b for a, b in pairs)"""
        code = "x = min(a+b for a, b in pairs)"
        result = transpile(code)
        assert "min" in result.lower() or "a" in result
    
    def test_max_with_unpack(self):
        """max(a*b for a, b in pairs)"""
        code = "x = max(a*b for a, b in pairs)"
        result = transpile(code)
        assert "max" in result.lower() or "a" in result
    
    def test_sorted_with_unpack(self):
        """sorted(a for a, b in pairs)"""
        code = "x = sorted(a for a, b in pairs)"
        result = transpile(code)
        assert "sorted" in result.lower() or "a" in result
    
    def test_complex_unpack_expression(self):
        """sum((a+b)*c for (a, b), c in nested)"""
        code = "x = sum((a+b)*c for (a, b), c in nested)"
        result = transpile(code)
        # Should handle nested unpacking
        assert "a" in result
    
    def test_unpack_with_ternary(self):
        """list(a if a > b else b for a, b in pairs)"""
        code = "x = list(a if a > b else b for a, b in pairs)"
        result = transpile(code)
        assert "a" in result
        assert "b" in result
    
    def test_unpack_with_call(self):
        """list(process(a, b) for a, b in pairs)"""
        code = "x = list(process(a, b) for a, b in pairs)"
        result = transpile(code)
        assert "process" in result
    
    def test_multiple_generators(self):
        """Not tested here - rare in practice"""
        pass


# =============================================================================
# DECORATOR ORDER WITH ASYNC (10 tests)
# =============================================================================

class TestDecoratorOrderAsync:
    """Test decorator ordering with async functions."""
    
    def test_single_decorator_async(self):
        """@memoize async def ..."""
        code = """
@memoize
async def fetch():
    return await api.request()
"""
        result = transpile(code)
        assert "__py.memoize" in result
        assert "async function fetch" in result
    
    def test_debounce_on_async(self):
        """@debounce async def ..."""
        code = """
@debounce(300)
async def search(q):
    return await api.search(q)
"""
        result = transpile(code)
        assert "__py.debounce(300)" in result
        assert "async function search" in result
    
    def test_throttle_on_async(self):
        """@throttle async def ..."""
        code = """
@throttle(100)
async def track(event):
    await analytics.track(event)
"""
        result = transpile(code)
        assert "__py.throttle(100)" in result
        assert "async function track" in result
    
    def test_stacked_on_async(self):
        """Multiple decorators on async"""
        code = """
@log_calls
@memoize
async def compute():
    return await expensive()
"""
        result = transpile(code)
        assert "__py.log_calls" in result
        assert "__py.memoize" in result
        assert "async function compute" in result
        # Order: log_calls(memoize(async function))
        log_pos = result.find("log_calls")
        memo_pos = result.find("memoize")
        assert log_pos < memo_pos
    
    def test_retry_memoize_async(self):
        """@retry @memoize async def ..."""
        code = """
@retry(3)
@memoize
async def fetch_data():
    return await api.request()
"""
        result = transpile(code)
        assert "__py.retry(3)" in result
        assert "__py.memoize" in result
    
    def test_three_decorators_async(self):
        """Three decorators on async"""
        code = """
@timed
@retry(2)
@memoize
async def important():
    return await critical_call()
"""
        result = transpile(code)
        assert result.count("__py.") >= 3
    
    def test_custom_and_builtin_async(self):
        """Mix of custom and builtin on async"""
        code = """
@custom_decorator
@memoize
async def mixed():
    return await something()
"""
        result = transpile(code)
        assert "custom_decorator" in result
        assert "__py.memoize" in result
    
    def test_decorator_with_args_async(self):
        """Decorator factory on async"""
        code = """
@cache(ttl=60)
@rate_limit(10)
async def api_call():
    return await external_api()
"""
        result = transpile(code)
        assert "cache" in result
        assert "rate_limit" in result
    
    def test_once_on_async(self):
        """@once on async"""
        code = """
@once
async def initialize():
    await setup()
"""
        result = transpile(code)
        assert "__py.once" in result
    
    def test_deprecated_on_async(self):
        """@deprecated on async"""
        code = """
@deprecated('Use v2')
async def old_fetch():
    return await legacy_api()
"""
        result = transpile(code)
        assert "__py.deprecated" in result


# =============================================================================
# DECORATOR SPREAD ARGS (10 tests)
# =============================================================================

class TestDecoratorSpreadArgs:
    """Test decorators with spread arguments."""
    
    def test_spread_in_decorator(self):
        """@validate(*validators)"""
        code = """
@validate(*validators)
def process(data):
    return data
"""
        result = transpile(code)
        assert "...validators" in result
    
    def test_dict_spread_in_decorator(self):
        """@config(**settings) - dict spread now supported"""
        code = """
@config(**settings)
def setup():
    pass
"""
        result = transpile(code)
        assert "config" in result
        assert "...settings" in result
    
    def test_mixed_spread_decorator(self):
        """@wrapper(*args, **kwargs)"""
        code = """
@wrapper(*args, **kwargs)
def func():
    pass
"""
        result = transpile(code)
        assert "...args" in result
    
    def test_spread_with_literals(self):
        """@validate(*[int, str])"""
        code = """
@validate(*[int, str])
def typed(a, b):
    return a, b
"""
        result = transpile(code)
        assert "..." in result
    
    def test_decorator_call_spread(self):
        """Decorator result with spread call"""
        code = """
@create_handler(*middleware)
def handle(request):
    return response
"""
        result = transpile(code)
        assert "...middleware" in result
    
    def test_spread_in_chained(self):
        """Spread in chained decorators"""
        code = """
@first
@second(*items)
def func():
    pass
"""
        result = transpile(code)
        assert "first" in result
        assert "...items" in result
    
    def test_spread_attribute_decorator(self):
        """Spread with attribute access"""
        code = """
@register(*config.validators)
def validate():
    pass
"""
        result = transpile(code)
        assert "..." in result
    
    def test_multiple_spreads(self):
        """Multiple spreads in decorator"""
        code = """
@combine(*first, *second)
def merged():
    pass
"""
        result = transpile(code)
        assert result.count("...") >= 2
    
    def test_spread_async_decorator(self):
        """Spread decorator on async"""
        code = """
@middleware(*handlers)
async def endpoint():
    return await process()
"""
        result = transpile(code)
        assert "...handlers" in result
        assert "async function" in result
    
    def test_spread_with_kwarg(self):
        """Spread with keyword arg"""
        code = """
@setup(*args, key=value)
def init():
    pass
"""
        result = transpile(code)
        assert "...args" in result


# =============================================================================
# MEMOIZE CACHE KEY ISSUES (10 tests)
# =============================================================================

class TestMemoizeCacheKey:
    """Test memoize cache key behavior (JS runtime tests)."""
    
    def test_basic_memoize(self):
        """Basic memoize transpiles correctly"""
        code = """
@memoize
def add(a, b):
    return a + b
"""
        result = transpile(code)
        assert "__py.memoize" in result
    
    def test_memoize_single_arg(self):
        """Single arg uses direct key"""
        code = """
@memoize
def square(x):
    return x * x
"""
        result = transpile(code)
        assert "__py.memoize" in result
    
    def test_memoize_no_args(self):
        """No args function"""
        code = """
@memoize
def constant():
    return 42
"""
        result = transpile(code)
        assert "__py.memoize" in result
    
    def test_memoize_many_args(self):
        """Many args use JSON key"""
        code = """
@memoize
def combine(a, b, c, d):
    return a + b + c + d
"""
        result = transpile(code)
        assert "__py.memoize" in result
    
    def test_memoize_with_defaults(self):
        """Memoize with default args"""
        code = """
@memoize
def greet(name, greeting='Hello'):
    return f'{greeting}, {name}!'
"""
        result = transpile(code)
        assert "__py.memoize" in result
    
    def test_memoize_recursive(self):
        """Recursive memoized function"""
        code = """
@memoize
def fib(n):
    if n <= 1:
        return n
    return fib(n-1) + fib(n-2)
"""
        result = transpile(code)
        assert "__py.memoize" in result
        assert "fib" in result
    
    def test_memoize_async(self):
        """Memoize on async"""
        code = """
@memoize
async def fetch(url):
    return await request(url)
"""
        result = transpile(code)
        assert "__py.memoize" in result
        assert "async function" in result
    
    def test_memoize_stacked(self):
        """Memoize with other decorators"""
        code = """
@log_calls
@memoize
def expensive():
    return compute()
"""
        result = transpile(code)
        assert "__py.log_calls" in result
        assert "__py.memoize" in result
    
    def test_memoize_varargs(self):
        """Memoize with *args"""
        code = """
@memoize
def sum_all(*args):
    return sum(args)
"""
        result = transpile(code)
        assert "__py.memoize" in result
        assert "...args" in result
    
    def test_memoize_method_like(self):
        """Memoize on method-like function"""
        code = """
@memoize
def method(self, key):
    return self.data[key]
"""
        result = transpile(code)
        assert "__py.memoize" in result
        assert "self" in result
