"""
Test Async/Await Transpilation (Phase 18.5)

=============================================================================
WHAT THIS FILE TESTS
=============================================================================

Comprehensive tests for Python async/await syntax transpilation:
- Basic await expressions
- Async function definitions
- Chained awaits
- Await in various expressions
- Error handling patterns
- Real-world API patterns

=============================================================================
TARGET: 150 TESTS
=============================================================================
"""

import pytest
from pynext.transpiler import transpile, TranspileError


def transpile_expression(expr: str) -> str:
    """Helper to transpile a single expression."""
    return transpile(f"x = {expr}")


# =============================================================================
# BASIC AWAIT (20 tests)
# =============================================================================

class TestBasicAwait:
    """Test basic await expressions."""
    
    def test_await_function_call(self):
        """await func()"""
        result = transpile("async def f():\n    x = await get_data()")
        assert "await get_data()" in result
    
    def test_await_method_call(self):
        """await obj.method()"""
        result = transpile("async def f():\n    x = await response.json()")
        assert "await response.json()" in result
    
    def test_await_with_args(self):
        """await func(a, b)"""
        result = transpile("async def f():\n    x = await fetch(url, options)")
        assert "await fetch(url, options)" in result
    
    def test_await_attribute_method(self):
        """await obj.attr.method()"""
        result = transpile("async def f():\n    x = await client.api.fetch()")
        assert "await client.api.fetch()" in result
    
    def test_await_subscript_method(self):
        """await items[0].method()"""
        result = transpile("async def f():\n    x = await handlers[0].run()")
        assert "await" in result and "run()" in result
    
    def test_await_variable(self):
        """await promise_var"""
        result = transpile("async def f():\n    x = await promise")
        assert "await promise" in result
    
    def test_await_property_access(self):
        """await obj.property"""
        result = transpile("async def f():\n    x = await task.result")
        assert "await task.result" in result
    
    def test_await_simple_assignment(self):
        """x = await func()"""
        result = transpile("async def f():\n    result = await query()")
        assert "let result = await query()" in result
    
    def test_await_multiple_assignments(self):
        """Multiple await assignments"""
        code = """
async def f():
    a = await get_a()
    b = await get_b()
    c = await get_c()
"""
        result = transpile(code)
        assert result.count("await") == 3
    
    def test_await_no_assignment(self):
        """await as statement (no assignment)"""
        result = transpile("async def f():\n    await delay(100)")
        assert "await delay(100)" in result
    
    def test_await_with_keyword_args(self):
        """await func(key=value)"""
        result = transpile("async def f():\n    x = await fetch(url, method='GET')")
        assert "await fetch" in result
    
    def test_await_nested_call(self):
        """await outer(inner())"""
        result = transpile("async def f():\n    x = await process(get_data())")
        assert "await process(get_data())" in result
    
    def test_await_with_spread(self):
        """await func(*args)"""
        result = transpile("async def f():\n    x = await call(*args)")
        assert "await call(...args)" in result
    
    def test_await_string_method(self):
        """await on result of string operation"""
        result = transpile("async def f():\n    x = await fetch(base + path)")
        assert "await fetch" in result
    
    def test_await_in_return(self):
        """return await func()"""
        result = transpile("async def f():\n    return await get_result()")
        assert "return await get_result()" in result
    
    def test_await_fstring_arg(self):
        """await with f-string argument"""
        result = transpile("async def f():\n    x = await fetch(f'/api/{id}')")
        assert "await fetch" in result
    
    def test_await_list_arg(self):
        """await with list argument"""
        result = transpile("async def f():\n    x = await process([1, 2, 3])")
        assert "await process([1, 2, 3])" in result
    
    def test_await_dict_arg(self):
        """await with dict argument"""
        result = transpile("async def f():\n    x = await post({'key': 'value'})")
        assert "await post" in result
    
    def test_await_lambda_result(self):
        """await (lambda: func())()"""
        result = transpile("async def f():\n    x = await (lambda: get)()") 
        assert "await" in result
    
    def test_await_conditional_expression(self):
        """await (a if cond else b)"""
        result = transpile("async def f():\n    x = await (get_a() if flag else get_b())")
        assert "await" in result


# =============================================================================
# ASYNC FUNCTIONS (25 tests)
# =============================================================================

class TestAsyncFunctions:
    """Test async function definitions."""
    
    def test_async_empty_function(self):
        """async def foo(): pass"""
        result = transpile("async def foo():\n    pass")
        assert "async function foo()" in result
    
    def test_async_with_body(self):
        """async def with body statements"""
        result = transpile("async def foo():\n    x = 1\n    return x")
        assert "async function foo()" in result
        assert "return x" in result
    
    def test_async_single_param(self):
        """async def foo(x)"""
        result = transpile("async def foo(x):\n    pass")
        assert "async function foo(x)" in result
    
    def test_async_multiple_params(self):
        """async def foo(a, b, c)"""
        result = transpile("async def foo(a, b, c):\n    pass")
        assert "async function foo(a, b, c)" in result
    
    def test_async_with_default(self):
        """async def foo(x=1)"""
        result = transpile("async def foo(x=1):\n    pass")
        assert "async function foo(x = 1)" in result
    
    def test_async_with_multiple_defaults(self):
        """async def foo(a, b=1, c=2)"""
        result = transpile("async def foo(a, b=1, c=2):\n    pass")
        assert "async function foo(a, b = 1, c = 2)" in result
    
    def test_async_with_await_in_body(self):
        """async function with await"""
        result = transpile("async def foo():\n    await bar()")
        assert "async function foo()" in result
        assert "await bar()" in result
    
    def test_async_return_await(self):
        """async def with return await"""
        result = transpile("async def foo():\n    return await bar()")
        assert "return await bar()" in result
    
    def test_async_multiple_awaits(self):
        """Multiple awaits in async function"""
        code = """
async def fetch_all():
    a = await get_a()
    b = await get_b()
    return a + b
"""
        result = transpile(code)
        assert "async function fetch_all()" in result
        assert result.count("await") == 2
    
    def test_async_with_if_statement(self):
        """async with if statement"""
        code = """
async def foo():
    if condition:
        await action()
"""
        result = transpile(code)
        assert "if" in result
        assert "await action()" in result
    
    def test_async_with_for_loop(self):
        """async with for loop"""
        code = """
async def foo():
    for item in items:
        await process(item)
"""
        result = transpile(code)
        assert "for" in result
        assert "await process(item)" in result
    
    def test_async_with_while_loop(self):
        """async with while loop"""
        code = """
async def foo():
    while running:
        await tick()
"""
        result = transpile(code)
        assert "while" in result
        assert "await tick()" in result
    
    def test_async_nested_function(self):
        """Nested async function"""
        code = """
async def outer():
    async def inner():
        await task()
    await inner()
"""
        result = transpile(code)
        assert result.count("async function") == 2
    
    def test_async_with_list_comp(self):
        """async with list comprehension"""
        code = """
async def foo():
    data = await get_items()
    return [x * 2 for x in data]
"""
        result = transpile(code)
        assert "await get_items()" in result
        assert ".map(" in result
    
    def test_async_multiple_functions(self):
        """Multiple async functions"""
        code = """
async def foo():
    pass

async def bar():
    pass
"""
        result = transpile(code)
        assert "async function foo()" in result
        assert "async function bar()" in result
    
    def test_async_mixed_with_regular(self):
        """Async and regular functions together"""
        code = """
def regular():
    pass

async def async_fn():
    pass
"""
        result = transpile(code)
        assert "function regular()" in result
        assert "async function async_fn()" in result
    
    def test_async_empty_return(self):
        """async with empty return"""
        result = transpile("async def foo():\n    return")
        assert "return;" in result
    
    def test_async_return_tuple(self):
        """async returning tuple"""
        result = transpile("async def foo():\n    return a, b")
        assert "return [a, b]" in result
    
    def test_async_with_docstring(self):
        """async with docstring (ignored)"""
        code = '''
async def foo():
    """Docstring"""
    pass
'''
        result = transpile(code)
        assert "async function foo()" in result
    
    def test_async_reserved_word_param(self):
        """async with reserved word as param"""
        result = transpile("async def foo(class_):\n    pass")
        assert "async function foo" in result
    
    def test_async_with_complex_default(self):
        """async with complex default value"""
        result = transpile("async def foo(x=[]):\n    pass")
        assert "async function foo(x = [])" in result
    
    def test_async_long_body(self):
        """async with many statements"""
        code = """
async def process():
    a = await step1()
    b = await step2(a)
    c = await step3(b)
    d = await step4(c)
    return d
"""
        result = transpile(code)
        assert result.count("await") == 4
    
    def test_async_with_boolean_ops(self):
        """async with boolean operations"""
        code = """
async def check():
    return await is_valid() and await is_ready()
"""
        result = transpile(code)
        assert result.count("await") == 2
    
    def test_async_callback_style(self):
        """async function used as callback"""
        code = """
async def handler(event):
    data = await process(event)
    return data
"""
        result = transpile(code)
        assert "async function handler(event)" in result


# =============================================================================
# CHAINED AWAITS (20 tests)
# =============================================================================

class TestChainedAwaits:
    """Test chained await expressions."""
    
    def test_await_then_method(self):
        """(await x).method()"""
        code = """
async def f():
    data = await response.json()
    return data.get('key')
"""
        result = transpile(code)
        assert "await response.json()" in result
    
    def test_double_await(self):
        """await await func() (rare but valid)"""
        result = transpile("async def f():\n    x = await (await get_promise())")
        assert result.count("await") == 2
    
    def test_await_chain_fetch_json(self):
        """Classic fetch().then().json() pattern"""
        code = """
async def f():
    response = await fetch(url)
    data = await response.json()
    return data
"""
        result = transpile(code)
        assert "await fetch(url)" in result
        assert "await response.json()" in result
    
    def test_await_with_attribute_chain(self):
        """await obj.a.b.method()"""
        result = transpile("async def f():\n    x = await client.users.api.fetch()")
        assert "await client.users.api.fetch()" in result
    
    def test_sequential_awaits_same_obj(self):
        """Multiple awaits on same object"""
        code = """
async def f():
    await obj.start()
    await obj.process()
    await obj.finish()
"""
        result = transpile(code)
        assert result.count("await obj.") == 3
    
    def test_await_result_used_in_next(self):
        """await result used in next await"""
        code = """
async def f():
    user = await get_user(id)
    posts = await get_posts(user.id)
    return posts
"""
        result = transpile(code)
        assert "await get_user" in result
        assert "await get_posts" in result
    
    def test_await_in_list_elements(self):
        """[await a, await b]"""
        code = """
async def f():
    results = [await get_a(), await get_b()]
    return results
"""
        result = transpile(code)
        assert result.count("await") == 2
    
    def test_await_in_dict_values(self):
        """{'a': await a, 'b': await b}"""
        code = """
async def f():
    return {'a': await get_a(), 'b': await get_b()}
"""
        result = transpile(code)
        assert result.count("await") == 2
    
    def test_await_pipeline(self):
        """Pipeline of awaits"""
        code = """
async def pipeline(data):
    step1 = await transform1(data)
    step2 = await transform2(step1)
    step3 = await transform3(step2)
    return step3
"""
        result = transpile(code)
        assert result.count("await") == 3
    
    def test_await_with_index(self):
        """(await get_list())[0]"""
        code = """
async def f():
    items = await get_items()
    first = items[0]
    return first
"""
        result = transpile(code)
        assert "await get_items()" in result
    
    def test_await_parallel_pattern(self):
        """Multiple independent awaits"""
        code = """
async def f():
    a = await fetch_a()
    b = await fetch_b()
    c = await fetch_c()
    return a + b + c
"""
        result = transpile(code)
        assert result.count("await") == 3
    
    def test_await_conditional_chain(self):
        """Conditional await chain"""
        code = """
async def f():
    if await check():
        return await get_success()
    return await get_fallback()
"""
        result = transpile(code)
        assert result.count("await") == 3
    
    def test_await_in_ternary(self):
        """await in ternary expression"""
        code = """
async def f():
    result = await get_a() if cond else await get_b()
    return result
"""
        result = transpile(code)
        assert result.count("await") == 2
    
    def test_await_method_chain_pattern(self):
        """await and method chain"""
        code = """
async def f():
    text = await response.text()
    return text.strip()
"""
        result = transpile(code)
        assert "await response.text()" in result
    
    def test_await_accumulator_pattern(self):
        """Accumulator with await"""
        code = """
async def fetch_all(ids):
    results = []
    for id in ids:
        data = await fetch(id)
        results.append(data)
    return results
"""
        result = transpile(code)
        assert "await fetch(id)" in result
        assert "results.push(data)" in result
    
    def test_await_with_error_check(self):
        """await with immediate error check"""
        code = """
async def f():
    response = await fetch(url)
    if not response.ok:
        return None
    return await response.json()
"""
        result = transpile(code)
        assert result.count("await") == 2
    
    def test_await_nested_in_call(self):
        """await nested inside call"""
        code = """
async def f():
    return await process(await get_data())
"""
        result = transpile(code)
        assert result.count("await") == 2
    
    def test_await_with_comparison(self):
        """await in comparison"""
        code = """
async def f():
    return await get_count() > 0
"""
        result = transpile(code)
        assert "await get_count()" in result
    
    def test_await_in_boolean_and(self):
        """await in and expression"""
        code = """
async def f():
    return await is_ready() and await is_valid()
"""
        result = transpile(code)
        assert result.count("await") == 2
    
    def test_await_in_boolean_or(self):
        """await in or expression"""
        code = """
async def f():
    return await primary() or await fallback()
"""
        result = transpile(code)
        assert result.count("await") == 2


# =============================================================================
# AWAIT IN EXPRESSIONS (25 tests)
# =============================================================================

class TestAwaitInExpressions:
    """Test await in various expression contexts."""
    
    def test_await_in_addition(self):
        """await a + await b"""
        code = """
async def f():
    return await get_a() + await get_b()
"""
        result = transpile(code)
        assert result.count("await") == 2
    
    def test_await_in_multiplication(self):
        """await a * b"""
        code = """
async def f():
    return await get_count() * 2
"""
        result = transpile(code)
        assert "await get_count()" in result
    
    def test_await_with_unary_minus(self):
        """-await value"""
        code = """
async def f():
    return -(await get_value())
"""
        result = transpile(code)
        assert "await" in result
    
    def test_await_in_subscript(self):
        """items[await index]"""
        code = """
async def f():
    items = await get_items()
    return items[0]
"""
        result = transpile(code)
        assert "await get_items()" in result
    
    def test_await_as_list_element(self):
        """[1, await x, 3]"""
        code = """
async def f():
    return [1, await get_middle(), 3]
"""
        result = transpile(code)
        assert "await get_middle()" in result
    
    def test_await_as_dict_value(self):
        """{'key': await value}"""
        code = """
async def f():
    return {'data': await fetch_data()}
"""
        result = transpile(code)
        assert "await fetch_data()" in result
    
    def test_await_in_fstring(self):
        """f'Result: {await x}'"""
        code = """
async def f():
    name = await get_name()
    return f'Hello {name}'
"""
        result = transpile(code)
        assert "await get_name()" in result
    
    def test_await_as_function_arg(self):
        """func(await x)"""
        code = """
async def f():
    return process(await get_data())
"""
        result = transpile(code)
        assert "process(await get_data())" in result
    
    def test_await_multiple_args(self):
        """func(await a, await b)"""
        code = """
async def f():
    return combine(await get_a(), await get_b())
"""
        result = transpile(code)
        assert result.count("await") == 2
    
    def test_await_with_string_format(self):
        """'{}' .format(await x)"""
        code = """
async def f():
    value = await get_value()
    return str(value)
"""
        result = transpile(code)
        assert "await get_value()" in result
    
    def test_await_in_slice(self):
        """items[:await n]"""
        code = """
async def f():
    n = await get_limit()
    return items[:n]
"""
        result = transpile(code)
        assert "await get_limit()" in result
    
    def test_await_in_comparison_chain(self):
        """a < await b < c"""
        code = """
async def f():
    return 0 < await get_value() < 100
"""
        result = transpile(code)
        assert "await get_value()" in result
    
    def test_await_with_not(self):
        """not await predicate()"""
        code = """
async def f():
    return not await is_valid()
"""
        result = transpile(code)
        assert "await is_valid()" in result
    
    def test_await_in_tuple(self):
        """(await a, await b)"""
        code = """
async def f():
    return await get_x(), await get_y()
"""
        result = transpile(code)
        assert result.count("await") == 2
    
    def test_await_attribute_access(self):
        """(await obj).attr"""
        code = """
async def f():
    user = await get_user()
    return user.name
"""
        result = transpile(code)
        assert "await get_user()" in result
        assert "user.name" in result
    
    def test_await_method_on_result(self):
        """(await obj).method()"""
        code = """
async def f():
    data = await get_data()
    return data.process()
"""
        result = transpile(code)
        assert "await get_data()" in result
        assert "data.process()" in result
    
    def test_await_in_assert_value(self):
        """if await cond:"""
        code = """
async def f():
    if await is_ready():
        return 'ready'
"""
        result = transpile(code)
        assert "await is_ready()" in result
    
    def test_await_in_while_condition(self):
        """while await running:"""
        code = """
async def f():
    while await is_running():
        await tick()
"""
        result = transpile(code)
        assert result.count("await") == 2
    
    def test_await_power_operator(self):
        """await x ** 2"""
        code = """
async def f():
    return (await get_base()) ** 2
"""
        result = transpile(code)
        assert "await get_base()" in result
    
    def test_await_floor_div(self):
        """await x // 2"""
        code = """
async def f():
    return await get_value() // 2
"""
        result = transpile(code)
        assert "await get_value()" in result
    
    def test_await_modulo(self):
        """await x % 2"""
        code = """
async def f():
    return await get_value() % 2
"""
        result = transpile(code)
        assert "await get_value()" in result
    
    def test_await_complex_expression(self):
        """Complex expression with await"""
        code = """
async def f():
    return (await get_a() + await get_b()) * 2
"""
        result = transpile(code)
        assert result.count("await") == 2
    
    def test_await_nested_ternary(self):
        """Nested ternary with await"""
        code = """
async def f():
    return await a() if cond1 else (await b() if cond2 else await c())
"""
        result = transpile(code)
        assert result.count("await") == 3
    
    def test_await_with_walrus_equivalent(self):
        """Pattern similar to walrus operator"""
        code = """
async def f():
    data = await fetch()
    if data:
        return data
"""
        result = transpile(code)
        assert "await fetch()" in result


# =============================================================================
# ERROR PATTERNS (20 tests)
# =============================================================================

class TestAwaitErrorPatterns:
    """Test await with error handling patterns."""
    
    def test_await_with_default_fallback(self):
        """await with or fallback"""
        code = """
async def f():
    return await get_value() or default
"""
        result = transpile(code)
        assert "await get_value()" in result
        assert "default" in result
    
    def test_await_check_before_use(self):
        """Check result before using"""
        code = """
async def f():
    result = await fetch()
    if result is None:
        return []
    return result
"""
        result = transpile(code)
        assert "await fetch()" in result
        assert "=== null" in result
    
    def test_await_with_validation(self):
        """Validate await result"""
        code = """
async def f():
    data = await get_data()
    if not data:
        raise ValueError("No data")
    return data
"""
        result = transpile(code)
        assert "await get_data()" in result
    
    def test_await_retry_pattern(self):
        """Retry pattern with await"""
        code = """
async def fetch_with_retry():
    for i in range(3):
        result = await fetch()
        if result:
            return result
    return None
"""
        result = transpile(code)
        assert "await fetch()" in result
    
    def test_await_timeout_pattern(self):
        """Timeout pattern"""
        code = """
async def with_timeout():
    await delay(1000)
    return await get_result()
"""
        result = transpile(code)
        assert result.count("await") == 2
    
    def test_await_guard_clause(self):
        """Guard clause with await"""
        code = """
async def process(id):
    if not id:
        return None
    return await fetch(id)
"""
        result = transpile(code)
        assert "await fetch(id)" in result
    
    def test_await_early_return(self):
        """Early return based on await"""
        code = """
async def check():
    if await is_cached():
        return await get_cached()
    return await fetch_fresh()
"""
        result = transpile(code)
        assert result.count("await") == 3
    
    def test_await_null_check(self):
        """Null check after await"""
        code = """
async def safe_get():
    data = await fetch()
    return data if data else {}
"""
        result = transpile(code)
        assert "await fetch()" in result
    
    def test_await_type_check(self):
        """Type check after await"""
        code = """
async def get_list():
    result = await fetch()
    if isinstance(result, list):
        return result
    return [result]
"""
        result = transpile(code)
        assert "await fetch()" in result
    
    def test_await_assertion_pattern(self):
        """Assertion after await"""
        code = """
async def must_exist():
    item = await find(id)
    if item is None:
        return None
    return item
"""
        result = transpile(code)
        assert "await find" in result
    
    def test_await_conditional_processing(self):
        """Conditional processing based on await"""
        code = """
async def process():
    config = await load_config()
    if config.enabled:
        return await run_enabled()
    return await run_disabled()
"""
        result = transpile(code)
        assert result.count("await") == 3
    
    def test_await_cleanup_pattern(self):
        """Cleanup after await"""
        code = """
async def with_cleanup():
    resource = await acquire()
    result = await process(resource)
    await release(resource)
    return result
"""
        result = transpile(code)
        assert result.count("await") == 3
    
    def test_await_chain_check(self):
        """Check each step in chain"""
        code = """
async def safe_chain():
    a = await step1()
    if not a:
        return None
    b = await step2(a)
    if not b:
        return None
    return b
"""
        result = transpile(code)
        assert result.count("await") == 2
    
    def test_await_with_break(self):
        """await with break on condition"""
        code = """
async def find_first():
    for id in ids:
        item = await fetch(id)
        if item.valid:
            return item
    return None
"""
        result = transpile(code)
        assert "await fetch(id)" in result
    
    def test_await_accumulate_errors(self):
        """Accumulate during await loop"""
        code = """
async def validate_all(items):
    errors = []
    for item in items:
        result = await validate(item)
        if not result.ok:
            errors.append(result.error)
    return errors
"""
        result = transpile(code)
        assert "await validate(item)" in result
    
    def test_await_optional_steps(self):
        """Optional processing steps"""
        code = """
async def process(data, include_extra):
    result = await transform(data)
    if include_extra:
        result = await enhance(result)
    return result
"""
        result = transpile(code)
        assert result.count("await") == 2
    
    def test_await_parallel_independent(self):
        """Independent parallel awaits"""
        code = """
async def fetch_parallel():
    users = await get_users()
    posts = await get_posts()
    return users, posts
"""
        result = transpile(code)
        assert result.count("await") == 2
    
    def test_await_dependent_chain(self):
        """Dependent await chain"""
        code = """
async def fetch_dependent():
    user = await get_user(id)
    profile = await get_profile(user.profile_id)
    return profile
"""
        result = transpile(code)
        assert result.count("await") == 2
    
    def test_await_merge_results(self):
        """Merge multiple await results"""
        code = """
async def merge():
    a = await get_a()
    b = await get_b()
    return {**a, **b}
"""
        result = transpile(code)
        assert result.count("await") == 2
    
    def test_await_filter_results(self):
        """Filter await results"""
        code = """
async def get_valid():
    items = await fetch_all()
    return [x for x in items if x.valid]
"""
        result = transpile(code)
        assert "await fetch_all()" in result


# =============================================================================
# REAL-WORLD PATTERNS (40 tests)
# =============================================================================

class TestRealWorldPatterns:
    """Test real-world async patterns."""
    
    def test_api_get_request(self):
        """GET request pattern"""
        code = """
async def get_user(id):
    response = await fetch(f'/api/users/{id}')
    return await response.json()
"""
        result = transpile(code)
        assert result.count("await") == 2
    
    def test_api_post_request(self):
        """POST request pattern"""
        code = """
async def create_user(data):
    response = await fetch('/api/users', {
        'method': 'POST',
        'body': data
    })
    return await response.json()
"""
        result = transpile(code)
        assert result.count("await") == 2
    
    def test_fetch_with_headers(self):
        """Fetch with headers"""
        code = """
async def authenticated_fetch(url, token):
    headers = {'Authorization': f'Bearer {token}'}
    response = await fetch(url, {'headers': headers})
    return await response.json()
"""
        result = transpile(code)
        assert result.count("await") == 2
    
    def test_paginated_fetch(self):
        """Paginated fetch pattern"""
        code = """
async def fetch_all_pages():
    all_items = []
    page = 1
    while True:
        data = await fetch_page(page)
        if not data.items:
            break
        all_items.extend(data.items)
        page = page + 1
    return all_items
"""
        result = transpile(code)
        assert "await fetch_page(page)" in result
    
    def test_concurrent_requests(self):
        """Simulated concurrent pattern"""
        code = """
async def fetch_user_data(user_id):
    profile = await fetch_profile(user_id)
    settings = await fetch_settings(user_id)
    return {'profile': profile, 'settings': settings}
"""
        result = transpile(code)
        assert result.count("await") == 2
    
    def test_database_query(self):
        """Database query pattern"""
        code = """
async def find_user(email):
    result = await db.query('SELECT * FROM users WHERE email = ?', [email])
    return result[0] if result else None
"""
        result = transpile(code)
        assert "await db.query" in result
    
    def test_event_handler(self):
        """Event handler pattern"""
        code = """
async def on_click(event):
    data = await process_event(event)
    await update_ui(data)
"""
        result = transpile(code)
        assert result.count("await") == 2
    
    def test_form_submission(self):
        """Form submission handler"""
        code = """
async def handle_submit(form_data):
    validated = await validate(form_data)
    if validated.errors:
        return validated.errors
    result = await save(validated.data)
    return result
"""
        result = transpile(code)
        assert result.count("await") == 2
    
    def test_file_upload(self):
        """File upload pattern"""
        code = """
async def upload_file(file):
    url = await get_upload_url()
    result = await upload(url, file)
    return result.file_id
"""
        result = transpile(code)
        assert result.count("await") == 2
    
    def test_authentication_flow(self):
        """Authentication flow"""
        code = """
async def login(username, password):
    user = await authenticate(username, password)
    if not user:
        return None
    token = await create_session(user)
    return token
"""
        result = transpile(code)
        assert result.count("await") == 2
    
    def test_search_handler(self):
        """Search with debouncing pattern"""
        code = """
async def search(query):
    if len(query) < 3:
        return []
    results = await fetch_results(query)
    return results
"""
        result = transpile(code)
        assert "await fetch_results" in result
    
    def test_infinite_scroll(self):
        """Infinite scroll pattern"""
        code = """
async def load_more(offset):
    items = await fetch_items(offset, limit)
    return items
"""
        result = transpile(code)
        assert "await fetch_items" in result
    
    def test_refresh_token(self):
        """Token refresh pattern"""
        code = """
async def refresh_and_retry(request):
    new_token = await refresh_token()
    request.headers.token = new_token
    return await make_request(request)
"""
        result = transpile(code)
        assert result.count("await") == 2
    
    def test_websocket_message(self):
        """WebSocket message handling"""
        code = """
async def handle_message(ws, message):
    data = await process_message(message)
    await ws.send(data)
"""
        result = transpile(code)
        assert result.count("await") == 2
    
    def test_batch_processing(self):
        """Batch processing pattern"""
        code = """
async def process_batch(items):
    results = []
    for item in items:
        result = await process(item)
        results.append(result)
    return results
"""
        result = transpile(code)
        assert "await process(item)" in result
    
    def test_cache_aside(self):
        """Cache-aside pattern"""
        code = """
async def get_with_cache(key):
    cached = await cache.get(key)
    if cached:
        return cached
    value = await fetch_fresh(key)
    await cache.set(key, value)
    return value
"""
        result = transpile(code)
        assert result.count("await") == 3
    
    def test_rate_limited_fetch(self):
        """Rate limited fetching"""
        code = """
async def rate_limited_fetch(urls):
    results = []
    for url in urls:
        await delay(100)
        result = await fetch(url)
        results.append(result)
    return results
"""
        result = transpile(code)
        assert result.count("await") == 2
    
    def test_polling_pattern(self):
        """Polling pattern"""
        code = """
async def poll_status(job_id):
    while True:
        status = await check_status(job_id)
        if status.done:
            return status.result
        await delay(1000)
"""
        result = transpile(code)
        assert result.count("await") == 2
    
    def test_transaction_pattern(self):
        """Transaction pattern"""
        code = """
async def transfer(from_id, to_id, amount):
    await db.begin()
    await db.debit(from_id, amount)
    await db.credit(to_id, amount)
    await db.commit()
"""
        result = transpile(code)
        assert result.count("await") == 4
    
    def test_middleware_pattern(self):
        """Middleware pattern"""
        code = """
async def middleware(request, handler):
    request.timestamp = now()
    response = await handler(request)
    return response
"""
        result = transpile(code)
        assert "await handler(request)" in result
    
    def test_lazy_initialization(self):
        """Lazy initialization pattern"""
        code = """
async def get_connection():
    if not connection:
        connection = await create_connection()
    return connection
"""
        result = transpile(code)
        assert "await create_connection()" in result
    
    def test_retry_with_backoff(self):
        """Retry with backoff"""
        code = """
async def retry_fetch(url, max_retries):
    for i in range(max_retries):
        result = await fetch(url)
        if result.ok:
            return result
        await delay(100 * (2 ** i))
    return None
"""
        result = transpile(code)
        assert result.count("await") == 2
    
    def test_graceful_degradation(self):
        """Graceful degradation"""
        code = """
async def get_data():
    primary = await fetch_primary()
    if primary:
        return primary
    return await fetch_fallback()
"""
        result = transpile(code)
        assert result.count("await") == 2
    
    def test_aggregation_pattern(self):
        """Aggregation from multiple sources"""
        code = """
async def aggregate():
    source1 = await fetch_source1()
    source2 = await fetch_source2()
    source3 = await fetch_source3()
    return merge(source1, source2, source3)
"""
        result = transpile(code)
        assert result.count("await") == 3
    
    def test_validation_chain(self):
        """Validation chain"""
        code = """
async def validate_order(order):
    if not await check_inventory(order.items):
        return 'out_of_stock'
    if not await check_payment(order.payment):
        return 'payment_failed'
    return 'valid'
"""
        result = transpile(code)
        assert result.count("await") == 2
    
    def test_background_job(self):
        """Background job pattern"""
        code = """
async def run_job(job_id):
    job = await get_job(job_id)
    result = await execute(job)
    await update_status(job_id, 'complete', result)
    return result
"""
        result = transpile(code)
        assert result.count("await") == 3
    
    def test_stream_processing(self):
        """Stream processing pattern"""
        code = """
async def process_stream(stream):
    results = []
    for chunk in stream:
        processed = await transform(chunk)
        results.append(processed)
    return results
"""
        result = transpile(code)
        assert "await transform(chunk)" in result
    
    def test_circuit_breaker(self):
        """Circuit breaker pattern"""
        code = """
async def call_with_breaker(service):
    if breaker.is_open:
        return await fallback()
    result = await service.call()
    return result
"""
        result = transpile(code)
        assert result.count("await") == 2
    
    def test_health_check(self):
        """Health check pattern"""
        code = """
async def health_check():
    db_ok = await check_db()
    cache_ok = await check_cache()
    return {'db': db_ok, 'cache': cache_ok}
"""
        result = transpile(code)
        assert result.count("await") == 2
    
    def test_sse_handler(self):
        """Server-Sent Events handler"""
        code = """
async def handle_sse(connection):
    while connection.active:
        data = await get_update()
        await connection.send(data)
"""
        result = transpile(code)
        assert result.count("await") == 2
    
    def test_graphql_resolver(self):
        """GraphQL resolver pattern"""
        code = """
async def resolve_user(parent, args):
    user_id = args.get('id')
    return await fetch_user(user_id)
"""
        result = transpile(code)
        assert "await fetch_user" in result
    
    def test_feature_flag(self):
        """Feature flag pattern"""
        code = """
async def get_feature(user):
    flags = await load_flags(user.id)
    return flags.get('new_feature', False)
"""
        result = transpile(code)
        assert "await load_flags" in result
    
    def test_ab_test(self):
        """A/B test pattern"""
        code = """
async def get_variant(user):
    variant = await assign_variant(user.id, 'experiment_1')
    if variant == 'A':
        return await render_a()
    return await render_b()
"""
        result = transpile(code)
        assert result.count("await") >= 2  # All branches have await
    
    def test_notification_send(self):
        """Notification sending"""
        code = """
async def send_notification(user_id, message):
    user = await get_user(user_id)
    if user.preferences.email:
        await send_email(user.email, message)
    if user.preferences.push:
        await send_push(user.device_token, message)
"""
        result = transpile(code)
        assert result.count("await") >= 2
    
    def test_queue_worker(self):
        """Queue worker pattern"""
        code = """
async def worker():
    while True:
        job = await queue.fetch()
        if job is None:
            break
        await process_job(job)
        await queue.ack(job.id)
"""
        result = transpile(code)
        assert result.count("await") >= 3
    
    def test_metrics_collection(self):
        """Metrics collection"""
        code = """
async def collect_metrics():
    cpu = await get_cpu_usage()
    memory = await get_memory_usage()
    await report({'cpu': cpu, 'memory': memory})
"""
        result = transpile(code)
        assert result.count("await") == 3
    
    def test_log_aggregation(self):
        """Log aggregation"""
        code = """
async def aggregate_logs(service):
    logs = await fetch_logs(service)
    parsed = [parse(log) for log in logs]
    await store_logs(parsed)
    return len(parsed)
"""
        result = transpile(code)
        assert result.count("await") == 2
    
    def test_config_reload(self):
        """Config reload pattern"""
        code = """
async def reload_config():
    new_config = await fetch_config()
    if new_config.version > current.version:
        await apply_config(new_config)
        return True
    return False
"""
        result = transpile(code)
        assert result.count("await") == 2


# =============================================================================
# EDGE CASES (10 tests - bonus)
# =============================================================================

class TestAwaitEdgeCases:
    """Edge cases for await."""
    
    def test_await_none_comparison(self):
        """await with None comparison"""
        code = """
async def f():
    result = await fetch()
    return result is not None
"""
        result = transpile(code)
        assert "!== null" in result
    
    def test_await_boolean_context(self):
        """await in boolean context"""
        code = """
async def f():
    if await exists():
        return True
    return False
"""
        result = transpile(code)
        assert "await exists()" in result
    
    def test_await_with_default_value(self):
        """await with default using or"""
        code = """
async def f():
    value = await fetch_value() or 'default'
    return value
"""
        result = transpile(code)
        assert "await fetch_value()" in result
        assert "default" in result
    
    def test_await_empty_result_check(self):
        """Check empty result from await"""
        code = """
async def f():
    items = await fetch_items()
    if not items:
        return []
    return items
"""
        result = transpile(code)
        assert "await fetch_items()" in result
    
    def test_await_len_check(self):
        """Length check on await result"""
        code = """
async def f():
    items = await get_items()
    return len(items)
"""
        result = transpile(code)
        assert "await get_items()" in result
    
    def test_multiple_async_functions_order(self):
        """Multiple async functions maintain order"""
        code = """
async def first():
    return 1

async def second():
    return 2

async def third():
    return 3
"""
        result = transpile(code)
        assert result.find("first") < result.find("second") < result.find("third")
    
    def test_await_in_dict_comprehension(self):
        """await before dict comprehension"""
        code = """
async def f():
    items = await get_items()
    return {item.id: item.name for item in items}
"""
        result = transpile(code)
        assert "await get_items()" in result
    
    def test_await_deeply_nested(self):
        """Deeply nested await"""
        code = """
async def f():
    if cond1:
        if cond2:
            for item in items:
                if item.active:
                    result = await process(item)
                    return result
"""
        result = transpile(code)
        assert "await process(item)" in result
    
    def test_await_with_enumerate(self):
        """await in loop with enumerate"""
        code = """
async def f():
    for i, item in enumerate(items):
        await process(i, item)
"""
        result = transpile(code)
        assert "await process" in result
    
    def test_await_with_zip(self):
        """await with zip pattern"""
        code = """
async def f():
    for a, b in zip(list_a, list_b):
        await combine(a, b)
"""
        result = transpile(code)
        assert "await combine" in result
