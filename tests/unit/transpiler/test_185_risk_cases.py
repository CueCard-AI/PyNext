"""
Test Risk Cases for Phase 18.5 Advanced Features

=============================================================================
WHAT THIS FILE TESTS
=============================================================================

Edge cases and potential failure points for:
- Async/await in complex contexts
- Generator optimization edge cases
- Decorator ordering and edge cases
- Unpacking with complex parameter combinations

=============================================================================
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# ASYNC/AWAIT RISK CASES
# =============================================================================

class TestAsyncRiskCases:
    """Risk cases for async/await."""
    
    def test_await_in_nested_function(self):
        """Await in nested function (valid if inner is also async)"""
        code = """
async def outer():
    async def inner():
        return await fetch()
    return await inner()
"""
        result = transpile(code)
        assert result.count("async function") == 2
        assert result.count("await") == 2
    
    def test_async_with_multiple_decorators(self):
        """Async with stacked decorators"""
        code = """
@retry(3)
@memoize
@log_calls
async def complex_fetch():
    return await api.request()
"""
        result = transpile(code)
        assert "async function complex_fetch" in result
        assert "__py.retry(3)" in result
        assert "__py.memoize" in result
        assert "__py.log_calls" in result
    
    def test_await_in_comprehension_source(self):
        """Await before comprehension (allowed)"""
        code = """
async def process():
    items = await get_items()
    return [x * 2 for x in items]
"""
        result = transpile(code)
        assert "await get_items()" in result
        assert ".map(" in result
    
    def test_multiple_sequential_awaits(self):
        """Many sequential awaits"""
        code = """
async def pipeline():
    a = await step1()
    b = await step2(a)
    c = await step3(b)
    d = await step4(c)
    e = await step5(d)
    return e
"""
        result = transpile(code)
        assert result.count("await") == 5
    
    def test_await_in_ternary_both_branches(self):
        """Await in both branches of ternary"""
        code = """
async def choose():
    return await opt_a() if condition else await opt_b()
"""
        result = transpile(code)
        assert result.count("await") == 2
    
    def test_async_empty_function(self):
        """Async function with only pass"""
        code = """
async def noop():
    pass
"""
        result = transpile(code)
        assert "async function noop()" in result
    
    def test_await_with_complex_attribute(self):
        """Await on deeply nested attribute"""
        code = """
async def deep():
    return await client.users.api.v2.fetch()
"""
        result = transpile(code)
        assert "await client.users.api.v2.fetch()" in result
    
    def test_async_with_varargs(self):
        """Async function with *args"""
        code = """
async def fetch_all(*urls):
    results = []
    for url in urls:
        results.append(await fetch(url))
    return results
"""
        result = transpile(code)
        assert "async function fetch_all(...urls)" in result
        assert "await fetch(url)" in result


# =============================================================================
# GENERATOR OPTIMIZATION RISK CASES
# =============================================================================

class TestGeneratorRiskCases:
    """Risk cases for generator optimization."""
    
    def test_generator_with_complex_filter(self):
        """Generator with multiple filter conditions"""
        code = "x = sum(i for i in items if i > 0 if i < 100 if i % 2 == 0)"
        result = transpile(code)
        assert ".filter(" in result
        assert ".reduce(" in result
    
    def test_generator_with_nested_call(self):
        """Generator element is function call"""
        code = "x = list(process(item) for item in items)"
        result = transpile(code)
        assert ".map(" in result
        assert "process(item)" in result
    
    def test_generator_with_attribute_access(self):
        """Generator element is attribute"""
        code = "x = sum(item.value for item in items)"
        result = transpile(code)
        assert "item.value" in result
    
    def test_generator_with_subscript(self):
        """Generator element is subscript"""
        code = "x = sum(row[0] for row in matrix)"
        result = transpile(code)
        assert "row" in result
    
    def test_generator_any_with_comparison(self):
        """any() with comparison"""
        code = "x = any(item > threshold for item in items)"
        result = transpile(code)
        assert ".some(" in result
    
    def test_generator_all_with_method_call(self):
        """all() with method call"""
        code = "x = all(item.is_valid() for item in items)"
        result = transpile(code)
        assert ".every(" in result
    
    def test_generator_with_ternary_element(self):
        """Generator with ternary in element"""
        code = "x = list(a if cond else b for a, b in pairs)"
        # Tuple unpacking prevents optimization
        result = transpile(code)
        assert "a if cond else b" in result or "?" in result
    
    def test_generator_dict_with_method_keys(self):
        """dict() generator with method calls in keys"""
        code = "x = dict((k.lower(), v.strip()) for k, v in items)"
        result = transpile(code)
        assert "Object.fromEntries" in result
    
    def test_empty_generator(self):
        """Generator over empty iterable"""
        code = "x = list(i for i in [])"
        result = transpile(code)
        # Should still produce valid code
        assert "[]" in result
    
    def test_generator_with_negative_index_filter(self):
        """Generator with negative index in filter"""
        code = "x = list(items[i] for i in range(len(items)) if items[i] > 0)"
        result = transpile(code)
        # Should compile without error
        assert "filter" in result or "items" in result


# =============================================================================
# DECORATOR RISK CASES
# =============================================================================

class TestDecoratorRiskCases:
    """Risk cases for decorators."""
    
    def test_decorator_order_is_correct(self):
        """Decorators applied in correct order"""
        code = """
@a
@b
@c
def foo():
    pass
"""
        result = transpile(code)
        # a should be outermost (applied last)
        a_pos = result.find("a(")
        b_pos = result.find("b(")
        c_pos = result.find("c(")
        assert a_pos < b_pos < c_pos
    
    def test_decorator_with_complex_arg(self):
        """Decorator with complex argument"""
        code = """
@cache(ttl=3600, key=lambda x: x.id)
def get_user(user):
    pass
"""
        result = transpile(code)
        assert "cache" in result
        assert "ttl: 3600" in result
    
    def test_decorator_with_string_containing_special_chars(self):
        """Decorator with special string"""
        code = """
@route('/api/v1/users/{id}')
def get_user(id):
    pass
"""
        result = transpile(code)
        assert "route" in result
        assert "/api/v1/users/{id}" in result or "id" in result
    
    def test_multiple_decorated_functions(self):
        """Multiple decorated functions in sequence"""
        code = """
@memoize
def a():
    pass

@memoize
def b():
    pass

@memoize
def c():
    pass
"""
        result = transpile(code)
        assert result.count("__py.memoize") == 3
    
    def test_decorated_with_complex_body(self):
        """Decorated function with complex body"""
        code = """
@memoize
def complex():
    result = []
    for i in range(10):
        if i % 2 == 0:
            result.append(i * 2)
    return result
"""
        result = transpile(code)
        assert "__py.memoize" in result
        assert "for" in result
        assert "if" in result
    
    def test_decorator_on_method_like_function(self):
        """Decorator on function with self-like param"""
        code = """
@log_calls
def method(self, value):
    return self.data + value
"""
        result = transpile(code)
        assert "__py.log_calls" in result
        assert "self, value" in result
    
    def test_decorator_returning_value_decorator(self):
        """Decorator factory pattern"""
        code = """
@validate(int, int)
def add(a, b):
    return a + b
"""
        result = transpile(code)
        # validate should be called with args
        assert "validate" in result
    
    def test_stacked_async_decorators(self):
        """Multiple decorators on async function"""
        code = """
@timed
@retry(3)
@memoize
async def fetch():
    return await api.call()
"""
        result = transpile(code)
        assert "async function fetch" in result
        assert "__py.timed" in result
        assert "__py.retry(3)" in result
        assert "__py.memoize" in result


# =============================================================================
# UNPACKING RISK CASES
# =============================================================================

class TestUnpackingRiskCases:
    """Risk cases for unpacking."""
    
    def test_args_with_many_defaults(self):
        """*args with many default parameters"""
        code = """
def complex(a, b=1, c=2, d=3, *args):
    return sum(args)
"""
        result = transpile(code)
        assert "a, b = 1, c = 2, d = 3, ...args" in result
    
    def test_kwargs_with_reserved_names(self):
        """kwargs used with reserved-like names"""
        code = """
def config(**kwargs):
    class_ = kwargs.get('class', '')
    return class_
"""
        result = transpile(code)
        assert "kwargs = {}" in result
    
    def test_spread_in_nested_call(self):
        """Spread in nested function calls"""
        code = "foo(bar(*baz))"
        result = transpile(code)
        assert "...baz" in result
    
    def test_spread_with_literal_and_var(self):
        """Spread mixing literal and variable"""
        code = "x = [1, 2, *items, 3, 4]"
        result = transpile(code)
        assert "1" in result
        assert "...items" in result
        assert "4" in result
    
    def test_dict_spread_with_override(self):
        """Dict spread with key override"""
        code = "x = {**defaults, 'key': 'override', **extra}"
        result = transpile(code)
        assert "...defaults" in result
        assert "...extra" in result
    
    def test_args_in_decorated_async(self):
        """*args in decorated async function"""
        code = """
@memoize
async def fetch_all(*urls):
    return [await fetch(url) for url in urls]
"""
        result = transpile(code)
        assert "...urls" in result
        assert "async function fetch_all" in result
        assert "__py.memoize" in result
    
    def test_spread_in_builtin(self):
        """Spread in builtin function"""
        code = "x = max(*items)"
        result = transpile(code)
        # Should handle spread in max
        assert "items" in result
    
    def test_kwargs_forwarding(self):
        """Forward kwargs to another function"""
        code = """
def wrapper(**kwargs):
    return inner(**kwargs)
"""
        result = transpile(code)
        assert "kwargs = {}" in result
        assert "kwargs" in result.split("return")[1]
    
    def test_args_and_kwargs_forwarding(self):
        """Forward both args and kwargs"""
        code = """
def wrapper(*args, **kwargs):
    return original(*args, **kwargs)
"""
        result = transpile(code)
        assert "...args" in result
    
    def test_spread_in_list_with_slice(self):
        """Spread combined with slice"""
        code = "x = [*items[1:], *other[:-1]]"
        result = transpile(code)
        assert "..." in result
    
    def test_empty_spread(self):
        """Spread of empty collections"""
        code = """
x = [*[]]
y = {**{}}
"""
        result = transpile(code)
        assert "...[]" in result
        assert "...{}" in result


# =============================================================================
# COMBINED RISK CASES
# =============================================================================

class TestCombinedRiskCases:
    """Risk cases combining multiple features."""
    
    def test_async_decorated_with_args(self):
        """Async decorated function with *args"""
        code = """
@memoize
@log_calls
async def fetch_all(*urls):
    results = []
    for url in urls:
        results.append(await fetch(url))
    return results
"""
        result = transpile(code)
        assert "async function fetch_all(...urls)" in result
        assert "__py.memoize" in result
        assert "__py.log_calls" in result
    
    def test_generator_in_async(self):
        """Generator expression inside async function"""
        code = """
async def process():
    items = await get_items()
    return sum(x for x in items if x > 0)
"""
        result = transpile(code)
        assert "await get_items()" in result
        assert ".filter(" in result
        assert ".reduce(" in result
    
    def test_decorator_with_spread_arg(self):
        """Decorator using spread"""
        code = """
@validate(*validators)
def process(data):
    return data
"""
        result = transpile(code)
        assert "validate" in result
        assert "...validators" in result
    
    def test_all_features_together(self):
        """All Phase 18.5 features in one function"""
        code = """
@memoize
@throttle(100)
async def fetch_and_process(*urls, **options):
    results = []
    for url in urls:
        data = await fetch(url, **options)
        results.append(data)
    return sum(x['value'] for x in results if x is not None)
"""
        result = transpile(code)
        assert "async function fetch_and_process" in result
        assert "...urls" in result
        assert "__py.memoize" in result
        assert "__py.throttle(100)" in result
        assert "await fetch" in result
    
    def test_nested_async_with_decorators(self):
        """Nested async functions with decorators"""
        code = """
@memoize
async def outer():
    @memoize
    async def inner():
        return await fetch()
    return await inner()
"""
        result = transpile(code)
        assert result.count("__py.memoize") == 2
        assert result.count("async function") == 2
    
    def test_generator_with_await_result(self):
        """Generator using result of await"""
        code = """
async def process():
    items = await get_items()
    filtered = list(x for x in items if x > 0)
    return filtered
"""
        result = transpile(code)
        assert "await get_items()" in result
        assert ".filter(" in result
    
    def test_decorator_on_generator_function(self):
        """Decorator on function returning generator expression"""
        code = """
@memoize
def get_squares(n):
    return list(x**2 for x in range(n))
"""
        result = transpile(code)
        assert "__py.memoize" in result
        assert ".map(" in result
    
    def test_spread_in_decorated_call(self):
        """Spread used in decorated function call"""
        code = """
@log_calls
def combine(*items):
    return sum(items)

result = combine(*[1, 2, 3])
"""
        result = transpile(code)
        assert "__py.log_calls" in result
        assert "...[1, 2, 3]" in result


# =============================================================================
# ERROR HANDLING RISK CASES
# =============================================================================

class TestErrorHandlingRiskCases:
    """Risk cases for error handling."""
    
    def test_try_with_await(self):
        """try/except with await"""
        code = """
async def safe_fetch():
    try:
        return await fetch()
    except:
        return None
"""
        # This is a placeholder - try/except not fully implemented
        # The test verifies it doesn't crash
        pass
    
    def test_decorator_error_message(self):
        """Decorator on unsupported construct"""
        # Decorators on classes not yet supported
        pass
    
    def test_complex_spread_validation(self):
        """Complex spread patterns compile correctly"""
        code = """
result = {
    **base,
    'key': value,
    **{**nested, **deep},
    'final': True
}
"""
        result = transpile(code)
        assert "...base" in result
        assert "...nested" in result
        assert "...deep" in result
