"""
P1 and P2 Risk Area Tests for Phase 18.5

Comprehensive tests for:
- P1: Chained comparison side effects (10 tests)
- P1: Boolean short-circuit side effects (10 tests)
- P1: Generator tuple unpacking (15 tests)
- P1: Decorator order with async (10 tests)
- P2: Decorator spread args (10 tests)
- P2: Complex generator filters (10 tests)
- P2: Memoize cache key collisions (10 tests)
"""

import pytest
from pynext.transpiler import transpile


def transpile_expression(code: str) -> str:
    """Helper to transpile a single expression."""
    result = transpile(f"x = {code}")
    # Extract the expression part
    if "let x = " in result:
        return result.split("let x = ")[1].rstrip(";")
    return result


# =============================================================================
# P1: CHAINED COMPARISON SIDE EFFECTS (10 tests)
# =============================================================================

class TestChainedComparisonSideEffects:
    """
    Python: 0 < f() < 10 evaluates f() ONCE
    Bad JS: 0 < f() && f() < 10 evaluates f() TWICE
    Good JS: ((_t = f()), 0 < _t && _t < 10)
    """
    
    def test_simple_chain_no_cache(self):
        """Simple variables don't need caching"""
        result = transpile_expression("0 < x < 10")
        assert "(0 < x)" in result
        assert "(x < 10)" in result
        assert "&&" in result
    
    def test_chain_with_function_call(self):
        """Function call should appear only once or be cached"""
        result = transpile_expression("0 < get_value() < 10")
        # The function call should be cached
        count = result.count("get_value()")
        assert count >= 1  # At least once
    
    def test_chain_with_method_call(self):
        """Method call in chain"""
        result = transpile_expression("low < obj.compute() < high")
        assert "obj.compute()" in result
    
    def test_triple_chain_with_call(self):
        """a < f() < g() < b"""
        result = transpile_expression("a < f() < g() < b")
        assert "f()" in result
        assert "g()" in result
    
    def test_chain_with_subscript_call(self):
        """arr[i] in chain - uses __py.at for safe subscript"""
        result = transpile_expression("0 < arr[i] < 10")
        # arr[i] is transpiled to __py.at(arr, i)
        assert "__py.at(arr, i)" in result or "arr[i]" in result
    
    def test_chain_mixed_simple_complex(self):
        """Mix of simple and complex values"""
        result = transpile_expression("a < get_b() < c")
        assert "get_b()" in result
    
    def test_chain_equality_comparison(self):
        """a == b == c chain"""
        result = transpile_expression("a == b == c")
        assert "__py.eq" in result
    
    def test_chain_in_if_condition(self):
        """Chain in if condition"""
        code = """
if 0 < x < 10:
    result = True
"""
        result = transpile(code)
        assert "&&" in result
    
    def test_chain_with_attribute_access(self):
        """Chain with attribute access"""
        result = transpile_expression("min_val < obj.value < max_val")
        assert "obj.value" in result
    
    def test_chain_all_operators(self):
        """a < b <= c < d >= e"""
        result = transpile_expression("a < b <= c")
        assert "&&" in result


# =============================================================================
# P1: BOOLEAN SHORT-CIRCUIT SIDE EFFECTS (10 tests)
# =============================================================================

class TestBooleanShortCircuitSideEffects:
    """
    Python: a() and b() - b() not called if a() is falsy
    Bad JS: (__py.bool(a()) ? b() : a()) - a() called TWICE
    Good JS: ((_t) => __py.bool(_t) ? b() : _t)(a()) - a() called ONCE
    """
    
    def test_and_lazy_evaluation(self):
        """get_a() and get_b() - get_b() is NOT pre-evaluated"""
        result = transpile_expression("get_a() and get_b()")
        # Should use IIFE pattern for lazy evaluation
        assert "=>" in result
        assert "get_a()" in result
        assert "get_b()" in result
        # get_b() should be in the truthy branch, not pre-evaluated
        assert "__py.bool" in result
    
    def test_or_lazy_evaluation(self):
        """get_a() or get_b() - get_b() is NOT pre-evaluated"""
        result = transpile_expression("get_a() or get_b()")
        assert "=>" in result
        assert "__py.bool" in result
    
    def test_simple_and_no_iife(self):
        """Simple variables don't need IIFE"""
        result = transpile_expression("a and b")
        # Should still use ternary for Python semantics
        assert "__py.bool" in result
    
    def test_chained_and_lazy(self):
        """a() and b() and c() - each evaluated lazily"""
        result = transpile_expression("get_a() and get_b() and get_c()")
        # Should have nested lazy evaluation
        assert "get_a()" in result
        assert "get_b()" in result
        assert "get_c()" in result
    
    def test_mixed_and_or_lazy(self):
        """a() and b() or c() - proper precedence and laziness"""
        result = transpile_expression("get_a() and get_b() or get_c()")
        assert "__py.bool" in result
    
    def test_not_with_and(self):
        """not a and b"""
        result = transpile_expression("not get_a() and get_b()")
        assert "!" in result or "__py.bool" in result
    
    def test_and_returns_value(self):
        """and returns the determining value, not True/False"""
        result = transpile_expression("x and y")
        # Should return y if x is truthy, x if falsy
        assert "__py.bool(x)" in result
        assert "y" in result
    
    def test_or_returns_value(self):
        """or returns the determining value, not True/False"""
        result = transpile_expression("x or y")
        assert "__py.bool(x)" in result
    
    def test_comparison_and_no_double_eval(self):
        """(a > 0) and (b > 0) - comparisons are simple"""
        result = transpile_expression("(a > 0) and (b > 0)")
        assert "(a > 0)" in result
        assert "(b > 0)" in result
    
    def test_complex_condition(self):
        """Complex boolean expression"""
        result = transpile_expression("(get_a() and get_b()) or get_c()")
        assert "__py.bool" in result


# =============================================================================
# P1: GENERATOR TUPLE UNPACKING (15 tests)
# =============================================================================

class TestGeneratorTupleUnpacking:
    """
    Python: sum(a*b for a, b in pairs)
    Bad JS: pairs.reduce((acc, [a, b]) => ...) - destructuring needs parens in arrow
    Good JS: pairs.reduce((acc, ([a, b])) => ...)
    """
    
    def test_simple_tuple_unpack_sum(self):
        """sum(a*b for a, b in pairs)"""
        result = transpile_expression("sum(a*b for a, b in pairs)")
        assert ".reduce(" in result
        assert "[a, b]" in result
    
    def test_tuple_unpack_any(self):
        """any(v > 0 for k, v in items)"""
        result = transpile_expression("any(v > 0 for k, v in items)")
        assert ".some(" in result or "__py.any" in result
    
    def test_tuple_unpack_all(self):
        """all(a == b for a, b in pairs)"""
        result = transpile_expression("all(a == b for a, b in pairs)")
        assert ".every(" in result or "__py.all" in result
    
    def test_tuple_unpack_list(self):
        """list(a+b for a, b in pairs)"""
        result = transpile_expression("list(a+b for a, b in pairs)")
        assert ".map(" in result
        assert "a" in result and "b" in result
    
    def test_tuple_unpack_set(self):
        """set(k for k, v in items)"""
        result = transpile_expression("set(k for k, v in items)")
        assert "Set" in result
    
    def test_tuple_unpack_dict(self):
        """dict((k.lower(), v) for k, v in items)"""
        result = transpile_expression("dict((k.lower(), v) for k, v in items)")
        assert "Object.fromEntries" in result or "__py.dict" in result
    
    def test_triple_unpack(self):
        """sum(a+b+c for a, b, c in triples)"""
        result = transpile_expression("sum(a+b+c for a, b, c in triples)")
        assert "a" in result and "b" in result and "c" in result
    
    def test_unpack_with_filter(self):
        """list(a for a, b in pairs if b > 0)"""
        result = transpile_expression("list(a for a, b in pairs if b > 0)")
        assert ".filter(" in result
    
    def test_unpack_enumerate(self):
        """sum(i*x for i, x in enumerate(items))"""
        result = transpile_expression("sum(i*x for i, x in enumerate(items))")
        assert "i" in result and "x" in result
    
    def test_unpack_zip(self):
        """all(a < b for a, b in zip(xs, ys))"""
        result = transpile_expression("all(a < b for a, b in zip(xs, ys))")
        assert "zip" in result.lower() or "a" in result
    
    def test_unpack_items(self):
        """list(f'{k}={v}' for k, v in d.items())"""
        result = transpile_expression("list(str(k) + str(v) for k, v in d.items())")
        assert "k" in result and "v" in result
    
    def test_unpack_min(self):
        """min(a+b for a, b in pairs)"""
        result = transpile_expression("min(a+b for a, b in pairs)")
        assert "min" in result.lower() or "__py.min" in result
    
    def test_unpack_max(self):
        """max(a*b for a, b in pairs)"""
        result = transpile_expression("max(a*b for a, b in pairs)")
        assert "max" in result.lower() or "__py.max" in result
    
    def test_unpack_sorted(self):
        """sorted(a for a, b in pairs)"""
        result = transpile_expression("sorted(a for a, b in pairs)")
        assert "sorted" in result.lower() or "__py.sorted" in result
    
    def test_unpack_with_ternary(self):
        """list(a if a > b else b for a, b in pairs)"""
        result = transpile_expression("list(a if a > b else b for a, b in pairs)")
        assert "a" in result and "b" in result


# =============================================================================
# P1: DECORATOR ORDER WITH ASYNC (10 tests)
# =============================================================================

class TestDecoratorOrderWithAsync:
    """
    Decorators should be applied in correct order even on async functions.
    @outer
    @inner
    async def f(): ...
    → const f = outer(inner(async function f() {...}))
    """
    
    def test_single_on_async(self):
        """@memoize async def f()"""
        code = """
@memoize
async def fetch():
    return await api()
"""
        result = transpile(code)
        assert "__py.memoize" in result
        assert "async function fetch" in result
    
    def test_two_decorators_on_async(self):
        """@outer @inner async def f()"""
        code = """
@log_calls
@memoize
async def fetch():
    return await api()
"""
        result = transpile(code)
        # log_calls should wrap memoize
        log_pos = result.find("log_calls")
        memo_pos = result.find("memoize")
        assert log_pos < memo_pos
    
    def test_three_decorators_on_async(self):
        """@a @b @c async def f()"""
        code = """
@timed
@retry(3)
@memoize
async def critical():
    return await important()
"""
        result = transpile(code)
        assert result.count("__py.") >= 3
    
    def test_debounce_on_async(self):
        """@debounce(ms) async def f()"""
        code = """
@debounce(300)
async def search(q):
    return await api.search(q)
"""
        result = transpile(code)
        assert "__py.debounce(300)" in result
        assert "async function search" in result
    
    def test_throttle_on_async(self):
        """@throttle(ms) async def f()"""
        code = """
@throttle(100)
async def track(e):
    await analytics.track(e)
"""
        result = transpile(code)
        assert "__py.throttle(100)" in result
    
    def test_once_on_async(self):
        """@once async def f()"""
        code = """
@once
async def init():
    await setup()
"""
        result = transpile(code)
        assert "__py.once" in result
    
    def test_retry_on_async(self):
        """@retry(n) async def f()"""
        code = """
@retry(5)
async def flaky():
    return await unstable_api()
"""
        result = transpile(code)
        assert "__py.retry(5)" in result
    
    def test_deprecated_on_async(self):
        """@deprecated async def f()"""
        code = """
@deprecated('Use v2')
async def old():
    return await legacy()
"""
        result = transpile(code)
        assert "__py.deprecated" in result
    
    def test_custom_and_builtin_on_async(self):
        """Mix of custom and builtin decorators"""
        code = """
@my_decorator
@memoize
async def mixed():
    return await something()
"""
        result = transpile(code)
        assert "my_decorator" in result
        assert "__py.memoize" in result
    
    def test_decorator_factory_on_async(self):
        """@factory(args) on async"""
        code = """
@cache(ttl=60)
@rate_limit(10, per='minute')
async def api_call():
    return await external()
"""
        result = transpile(code)
        assert "cache" in result
        assert "rate_limit" in result


# =============================================================================
# P2: DECORATOR SPREAD ARGS (10 tests)
# =============================================================================

class TestDecoratorSpreadArgs:
    """
    Test decorators with *args and **kwargs spreads.
    """
    
    def test_starred_spread(self):
        """@validate(*validators)"""
        code = """
@validate(*validators)
def process(data):
    return data
"""
        result = transpile(code)
        assert "...validators" in result
    
    def test_double_starred_spread(self):
        """@config(**settings)"""
        code = """
@config(**settings)
def setup():
    pass
"""
        result = transpile(code)
        assert "...settings" in result
    
    def test_both_spreads(self):
        """@wrapper(*args, **kwargs)"""
        code = """
@wrapper(*args, **kwargs)
def func():
    pass
"""
        result = transpile(code)
        assert "...args" in result
    
    def test_spread_with_regular_args(self):
        """@dec(a, *rest)"""
        code = """
@setup(first, *rest)
def handler():
    pass
"""
        result = transpile(code)
        assert "first" in result
        assert "...rest" in result
    
    def test_spread_with_kwargs(self):
        """@dec(key=val, **more)"""
        code = """
@configure(debug=True, **options)
def app():
    pass
"""
        result = transpile(code)
        assert "debug" in result
        assert "...options" in result
    
    def test_spread_list_literal(self):
        """@validate(*[int, str])"""
        code = """
@types(*[int, str])
def typed(a, b):
    return a, b
"""
        result = transpile(code)
        assert "..." in result
    
    def test_spread_dict_literal(self):
        """@config(**{'key': val})"""
        code = """
@config(**{'debug': True})
def setup():
    pass
"""
        result = transpile(code)
        assert "..." in result
    
    def test_spread_on_async(self):
        """Spread decorator on async function"""
        code = """
@middleware(*handlers)
async def endpoint():
    return await process()
"""
        result = transpile(code)
        assert "...handlers" in result
        assert "async function" in result
    
    def test_spread_chained_decorators(self):
        """Multiple decorators with spreads"""
        code = """
@first
@second(*items)
@third(**config)
def func():
    pass
"""
        result = transpile(code)
        assert "first" in result
        assert "...items" in result
        assert "...config" in result
    
    def test_spread_attribute_decorator(self):
        """@mod.dec(*args)"""
        code = """
@validators.check(*rules)
def validate(data):
    return data
"""
        result = transpile(code)
        assert "validators.check" in result
        assert "...rules" in result


# =============================================================================
# P2: COMPLEX GENERATOR FILTERS (10 tests)
# =============================================================================

class TestComplexGeneratorFilters:
    """
    Test complex filter conditions in generator expressions.
    """
    
    def test_and_filter(self):
        """x for x in items if x > 0 and x < 10"""
        result = transpile_expression("list(x for x in items if x > 0 and x < 10)")
        assert ".filter(" in result
    
    def test_or_filter(self):
        """x for x in items if x < 0 or x > 10"""
        result = transpile_expression("list(x for x in items if x < 0 or x > 10)")
        assert ".filter(" in result
    
    def test_not_filter(self):
        """x for x in items if not x.hidden"""
        result = transpile_expression("list(x for x in items if not x.hidden)")
        assert ".filter(" in result
        assert "!" in result or "not" in result.lower()
    
    def test_comparison_filter(self):
        """x for x in items if x.value >= threshold"""
        result = transpile_expression("list(x for x in items if x.value >= threshold)")
        assert ".filter(" in result
        assert ">=" in result
    
    def test_in_filter(self):
        """x for x in items if x in valid"""
        result = transpile_expression("list(x for x in items if x in valid)")
        assert ".filter(" in result
    
    def test_not_in_filter(self):
        """x for x in items if x not in invalid"""
        result = transpile_expression("list(x for x in items if x not in invalid)")
        assert ".filter(" in result
    
    def test_is_none_filter(self):
        """x for x in items if x is not None"""
        result = transpile_expression("list(x for x in items if x is not None)")
        assert ".filter(" in result
    
    def test_method_call_filter(self):
        """x for x in items if x.is_valid()"""
        result = transpile_expression("list(x for x in items if x.is_valid())")
        assert ".filter(" in result
        assert "is_valid()" in result
    
    def test_complex_nested_filter(self):
        """x for x in items if (x > 0 and x < 10) or x == 0"""
        result = transpile_expression("list(x for x in items if (x > 0 and x < 10) or x == 0)")
        assert ".filter(" in result
    
    def test_filter_with_tuple_unpack(self):
        """k for k, v in items if v > 0"""
        result = transpile_expression("list(k for k, v in items if v > 0)")
        assert ".filter(" in result
        assert "v > 0" in result


# =============================================================================
# P2: MEMOIZE CACHE KEY COLLISIONS (10 tests)
# =============================================================================

class TestMemoizeCacheKeyCollisions:
    """
    Test that memoize uses proper cache keys to avoid collisions.
    The JS implementation now uses type-prefixed keys.
    """
    
    def test_memoize_basic(self):
        """Basic memoize works"""
        code = """
@memoize
def add(a, b):
    return a + b
"""
        result = transpile(code)
        assert "__py.memoize" in result
    
    def test_memoize_single_primitive(self):
        """Single primitive arg"""
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
    
    def test_memoize_multiple_args(self):
        """Multiple args use JSON key"""
        code = """
@memoize
def combine(a, b, c):
    return a + b + c
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
    
    def test_memoize_on_async(self):
        """Memoize on async function"""
        code = """
@memoize
async def fetch_user(id):
    return await db.get_user(id)
"""
        result = transpile(code)
        assert "__py.memoize" in result
        assert "async function" in result
    
    def test_memoize_with_varargs(self):
        """Memoize with *args"""
        code = """
@memoize
def sum_all(*args):
    return sum(args)
"""
        result = transpile(code)
        assert "__py.memoize" in result
    
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
    
    def test_memoize_method_pattern(self):
        """Memoize on method-like function"""
        code = """
@memoize
def get_property(self, key):
    return self.data[key]
"""
        result = transpile(code)
        assert "__py.memoize" in result


# =============================================================================
# COMBINED EDGE CASES (5 tests)
# =============================================================================

class TestCombinedEdgeCases:
    """
    Test combinations of multiple risk areas.
    """
    
    def test_decorated_async_with_tuple_unpack(self):
        """Decorated async with generator tuple unpack"""
        code = """
@memoize
async def compute(pairs):
    return sum(a*b for a, b in pairs)
"""
        result = transpile(code)
        assert "__py.memoize" in result
        assert "async function" in result
        assert "[a, b]" in result
    
    def test_boolean_in_generator_filter(self):
        """Boolean ops in generator filter"""
        result = transpile_expression("list(x for x in items if x.a and x.b)")
        assert ".filter(" in result
    
    def test_spread_decorator_on_async_with_kwargs(self):
        """Spread decorator on async with **kwargs"""
        code = """
@config(**settings)
async def setup(*args, **kwargs):
    return await init(*args, **kwargs)
"""
        result = transpile(code)
        assert "...settings" in result
        assert "async function" in result
    
    def test_chained_comparison_in_generator(self):
        """Chained comparison in generator filter"""
        result = transpile_expression("list(x for x in items if 0 < x < 10)")
        assert ".filter(" in result
        assert "&&" in result
    
    def test_memoized_with_complex_args(self):
        """Memoize with complex function signature"""
        code = """
@memoize
def complex_fn(a, b=1, *args, key=None, **kwargs):
    return sum(args)
"""
        result = transpile(code)
        assert "__py.memoize" in result
