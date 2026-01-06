"""
Test Decorator Transpilation (Phase 18.5)

=============================================================================
WHAT THIS FILE TESTS
=============================================================================

Comprehensive tests for Python decorator transpilation:
- @memoize
- @debounce(ms)
- @throttle(ms)
- Custom decorators
- Stacked decorators
- Async decorated functions

=============================================================================
TARGET: 100 TESTS
=============================================================================
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# @MEMOIZE (25 tests)
# =============================================================================

class TestMemoize:
    """Test @memoize decorator."""
    
    def test_memoize_simple(self):
        """@memoize on simple function"""
        code = """
@memoize
def add(a, b):
    return a + b
"""
        result = transpile(code)
        assert "__py.memoize" in result
        assert "const add = " in result
    
    def test_memoize_recursive(self):
        """@memoize on recursive function"""
        code = """
@memoize
def fib(n):
    if n <= 1:
        return n
    return fib(n-1) + fib(n-2)
"""
        result = transpile(code)
        assert "__py.memoize" in result
        assert "fib(n" in result
    
    def test_memoize_no_args(self):
        """@memoize on function with no args"""
        code = """
@memoize
def get_config():
    return load_config()
"""
        result = transpile(code)
        assert "__py.memoize" in result
        assert "function get_config()" in result
    
    def test_memoize_many_args(self):
        """@memoize on function with many args"""
        code = """
@memoize
def combine(a, b, c, d):
    return a + b + c + d
"""
        result = transpile(code)
        assert "__py.memoize" in result
        assert "(a, b, c, d)" in result
    
    def test_memoize_with_defaults(self):
        """@memoize on function with defaults"""
        code = """
@memoize
def greet(name, greeting="Hello"):
    return f"{greeting}, {name}!"
"""
        result = transpile(code)
        assert "__py.memoize" in result
        assert 'greeting = "Hello"' in result
    
    def test_memoize_preserves_body(self):
        """@memoize preserves function body"""
        code = """
@memoize
def compute():
    x = 1
    y = 2
    return x + y
"""
        result = transpile(code)
        assert "let x = 1" in result
        assert "let y = 2" in result
        assert "return" in result
    
    def test_memoize_with_loop(self):
        """@memoize with loop in body"""
        code = """
@memoize
def sum_to(n):
    total = 0
    for i in range(n):
        total += i
    return total
"""
        result = transpile(code)
        assert "__py.memoize" in result
        assert "for" in result
    
    def test_memoize_with_condition(self):
        """@memoize with condition in body"""
        code = """
@memoize
def classify(x):
    if x > 0:
        return "positive"
    return "non-positive"
"""
        result = transpile(code)
        assert "__py.memoize" in result
        assert "if" in result
    
    def test_memoize_empty_body(self):
        """@memoize with pass body"""
        code = """
@memoize
def noop():
    pass
"""
        result = transpile(code)
        assert "__py.memoize" in result
    
    def test_memoize_single_expression(self):
        """@memoize with single expression"""
        code = """
@memoize
def double(x):
    return x * 2
"""
        result = transpile(code)
        assert "__py.memoize" in result
        assert "return" in result
    
    def test_memoize_with_comprehension(self):
        """@memoize with list comprehension"""
        code = """
@memoize
def squares(n):
    return [x*x for x in range(n)]
"""
        result = transpile(code)
        assert "__py.memoize" in result
    
    def test_memoize_with_call(self):
        """@memoize calling other function"""
        code = """
@memoize
def wrapper(x):
    return process(x)
"""
        result = transpile(code)
        assert "__py.memoize" in result
        assert "process(x)" in result
    
    def test_memoize_with_method_call(self):
        """@memoize calling method"""
        code = """
@memoize
def upper(s):
    return s.upper()
"""
        result = transpile(code)
        assert "__py.memoize" in result
    
    def test_memoize_with_slice(self):
        """@memoize with slicing"""
        code = """
@memoize
def middle(items):
    return items[1:-1]
"""
        result = transpile(code)
        assert "__py.memoize" in result
    
    def test_memoize_with_dict_access(self):
        """@memoize with dict access"""
        code = """
@memoize
def lookup(d, key):
    return d[key]
"""
        result = transpile(code)
        assert "__py.memoize" in result
    
    def test_memoize_with_attribute(self):
        """@memoize with attribute access"""
        code = """
@memoize
def get_name(obj):
    return obj.name
"""
        result = transpile(code)
        assert "__py.memoize" in result
        assert "obj.name" in result
    
    def test_memoize_complex_default(self):
        """@memoize with complex default"""
        code = """
@memoize
def merge(items, default=[]):
    return items + default
"""
        result = transpile(code)
        assert "__py.memoize" in result
    
    def test_memoize_nested_calls(self):
        """@memoize with nested calls"""
        code = """
@memoize
def transform(x):
    return process(normalize(x))
"""
        result = transpile(code)
        assert "__py.memoize" in result
        assert "process(normalize(x))" in result
    
    def test_memoize_fstring(self):
        """@memoize with f-string"""
        code = """
@memoize
def format_name(first, last):
    return f"{first} {last}"
"""
        result = transpile(code)
        assert "__py.memoize" in result
    
    def test_memoize_ternary(self):
        """@memoize with ternary"""
        code = """
@memoize
def sign(x):
    return 1 if x > 0 else -1
"""
        result = transpile(code)
        assert "__py.memoize" in result
    
    def test_memoize_with_return_tuple(self):
        """@memoize returning tuple"""
        code = """
@memoize
def coords():
    return 1, 2
"""
        result = transpile(code)
        assert "__py.memoize" in result
        assert "[1, 2]" in result  # Tuple becomes array
    
    def test_memoize_with_dict_return(self):
        """@memoize returning dict"""
        code = """
@memoize
def config():
    return {'key': 'value'}
"""
        result = transpile(code)
        assert "__py.memoize" in result
    
    def test_memoize_with_list_return(self):
        """@memoize returning list"""
        code = """
@memoize
def items():
    return [1, 2, 3]
"""
        result = transpile(code)
        assert "__py.memoize" in result
        assert "[1, 2, 3]" in result
    
    def test_memoize_multiple_returns(self):
        """@memoize with multiple returns"""
        code = """
@memoize
def check(x):
    if x < 0:
        return "negative"
    if x > 0:
        return "positive"
    return "zero"
"""
        result = transpile(code)
        assert "__py.memoize" in result
        assert result.count("return") == 3


# =============================================================================
# @DEBOUNCE(ms) (20 tests)
# =============================================================================

class TestDebounce:
    """Test @debounce(ms) decorator."""
    
    def test_debounce_simple(self):
        """@debounce(300) on simple function"""
        code = """
@debounce(300)
def search(query):
    return fetch(query)
"""
        result = transpile(code)
        assert "__py.debounce(300)" in result
        assert "const search = " in result
    
    def test_debounce_different_times(self):
        """@debounce with various times"""
        for ms in [100, 500, 1000]:
            code = f"""
@debounce({ms})
def handler():
    pass
"""
            result = transpile(code)
            assert f"__py.debounce({ms})" in result
    
    def test_debounce_zero(self):
        """@debounce(0)"""
        code = """
@debounce(0)
def immediate():
    pass
"""
        result = transpile(code)
        assert "__py.debounce(0)" in result
    
    def test_debounce_large_value(self):
        """@debounce with large value"""
        code = """
@debounce(5000)
def slow_handler():
    pass
"""
        result = transpile(code)
        assert "__py.debounce(5000)" in result
    
    def test_debounce_with_args(self):
        """@debounce on function with args"""
        code = """
@debounce(300)
def search(query, limit):
    return fetch(query, limit)
"""
        result = transpile(code)
        assert "__py.debounce(300)" in result
        assert "(query, limit)" in result
    
    def test_debounce_with_defaults(self):
        """@debounce on function with defaults"""
        code = """
@debounce(200)
def search(query, limit=10):
    return fetch(query, limit)
"""
        result = transpile(code)
        assert "__py.debounce(200)" in result
        assert "limit = 10" in result
    
    def test_debounce_event_handler(self):
        """@debounce on event handler pattern"""
        code = """
@debounce(150)
def on_input(event):
    value = event.target.value
    update(value)
"""
        result = transpile(code)
        assert "__py.debounce(150)" in result
        assert "event.target.value" in result
    
    def test_debounce_api_call(self):
        """@debounce on API call pattern"""
        code = """
@debounce(500)
def fetch_suggestions(text):
    response = api.get(text)
    return response.data
"""
        result = transpile(code)
        assert "__py.debounce(500)" in result
    
    def test_debounce_with_loop(self):
        """@debounce with loop in body"""
        code = """
@debounce(100)
def process_items(items):
    for item in items:
        handle(item)
"""
        result = transpile(code)
        assert "__py.debounce(100)" in result
        assert "for" in result
    
    def test_debounce_with_condition(self):
        """@debounce with condition"""
        code = """
@debounce(250)
def validate(value):
    if len(value) < 3:
        return None
    return check(value)
"""
        result = transpile(code)
        assert "__py.debounce(250)" in result
    
    def test_debounce_expression(self):
        """@debounce value as expression (just number for now)"""
        code = """
@debounce(300)
def handler():
    pass
"""
        result = transpile(code)
        assert "__py.debounce(300)" in result
    
    def test_debounce_no_args_function(self):
        """@debounce on function with no args"""
        code = """
@debounce(1000)
def auto_save():
    save()
"""
        result = transpile(code)
        assert "__py.debounce(1000)" in result
        assert "function auto_save()" in result
    
    def test_debounce_many_args(self):
        """@debounce on function with many args"""
        code = """
@debounce(200)
def update(a, b, c, d):
    pass
"""
        result = transpile(code)
        assert "__py.debounce(200)" in result
        assert "(a, b, c, d)" in result
    
    def test_debounce_with_return(self):
        """@debounce with return value"""
        code = """
@debounce(100)
def compute(x):
    return x * 2
"""
        result = transpile(code)
        assert "__py.debounce(100)" in result
        assert "return" in result
    
    def test_debounce_preserves_body(self):
        """@debounce preserves all body statements"""
        code = """
@debounce(300)
def handler():
    a = 1
    b = 2
    c = a + b
    return c
"""
        result = transpile(code)
        assert "__py.debounce(300)" in result
        assert "let a = 1" in result
        assert "let b = 2" in result


# =============================================================================
# @THROTTLE(ms) (20 tests)
# =============================================================================

class TestThrottle:
    """Test @throttle(ms) decorator."""
    
    def test_throttle_simple(self):
        """@throttle(100) on simple function"""
        code = """
@throttle(100)
def on_scroll(event):
    update_position()
"""
        result = transpile(code)
        assert "__py.throttle(100)" in result
        assert "const on_scroll = " in result
    
    def test_throttle_different_times(self):
        """@throttle with various times"""
        for ms in [50, 200, 500]:
            code = f"""
@throttle({ms})
def handler():
    pass
"""
            result = transpile(code)
            assert f"__py.throttle({ms})" in result
    
    def test_throttle_zero(self):
        """@throttle(0)"""
        code = """
@throttle(0)
def immediate():
    pass
"""
        result = transpile(code)
        assert "__py.throttle(0)" in result
    
    def test_throttle_with_args(self):
        """@throttle on function with args"""
        code = """
@throttle(100)
def track(event, metadata):
    log(event, metadata)
"""
        result = transpile(code)
        assert "__py.throttle(100)" in result
        assert "(event, metadata)" in result
    
    def test_throttle_with_defaults(self):
        """@throttle on function with defaults"""
        code = """
@throttle(50)
def animate(frame, speed=1):
    render(frame, speed)
"""
        result = transpile(code)
        assert "__py.throttle(50)" in result
        assert "speed = 1" in result
    
    def test_throttle_mouse_move(self):
        """@throttle for mouse move handler"""
        code = """
@throttle(16)
def on_mouse_move(event):
    x = event.clientX
    y = event.clientY
    update_cursor(x, y)
"""
        result = transpile(code)
        assert "__py.throttle(16)" in result
    
    def test_throttle_resize(self):
        """@throttle for resize handler"""
        code = """
@throttle(100)
def on_resize(event):
    width = window.innerWidth
    recalculate(width)
"""
        result = transpile(code)
        assert "__py.throttle(100)" in result
    
    def test_throttle_with_condition(self):
        """@throttle with condition"""
        code = """
@throttle(50)
def process(value):
    if value > threshold:
        handle(value)
"""
        result = transpile(code)
        assert "__py.throttle(50)" in result
    
    def test_throttle_no_args_function(self):
        """@throttle on function with no args"""
        code = """
@throttle(1000)
def heartbeat():
    ping()
"""
        result = transpile(code)
        assert "__py.throttle(1000)" in result
    
    def test_throttle_with_return(self):
        """@throttle with return value"""
        code = """
@throttle(100)
def get_position():
    return current_position
"""
        result = transpile(code)
        assert "__py.throttle(100)" in result
        assert "return" in result


# =============================================================================
# CUSTOM DECORATORS (15 tests)
# =============================================================================

class TestCustomDecorators:
    """Test custom/user decorators."""
    
    def test_custom_simple(self):
        """Custom simple decorator"""
        code = """
@my_decorator
def foo():
    pass
"""
        result = transpile(code)
        assert "my_decorator" in result
        assert "__py." not in result or "my_decorator" in result.split("__py.")[0]
    
    def test_custom_with_args(self):
        """Custom decorator with args"""
        code = """
@my_wrapper(1, 2)
def foo():
    pass
"""
        result = transpile(code)
        assert "my_wrapper(1, 2)" in result
    
    def test_custom_with_string_arg(self):
        """Custom decorator with string arg"""
        code = """
@route('/api/users')
def get_users():
    pass
"""
        result = transpile(code)
        assert 'route("/api/users")' in result
    
    def test_custom_with_kwargs(self):
        """Custom decorator with kwargs"""
        code = """
@cache(ttl=3600)
def fetch_data():
    pass
"""
        result = transpile(code)
        assert "cache" in result
        assert "ttl: 3600" in result
    
    def test_custom_with_mixed_args(self):
        """Custom decorator with positional and keyword args"""
        code = """
@api('/users', method='GET')
def get_users():
    pass
"""
        result = transpile(code)
        assert "api" in result
        assert '"/users"' in result
        assert 'method: "GET"' in result
    
    def test_custom_module_decorator(self):
        """Decorator from module"""
        code = """
@functools.wraps
def wrapper():
    pass
"""
        result = transpile(code)
        assert "functools.wraps" in result
    
    def test_custom_nested_module(self):
        """Decorator from nested module"""
        code = """
@module.submodule.decorator
def foo():
    pass
"""
        result = transpile(code)
        assert "module.submodule.decorator" in result
    
    def test_custom_decorator_function_args(self):
        """Custom decorator on function with args"""
        code = """
@validate
def process(data, options):
    return transform(data, options)
"""
        result = transpile(code)
        assert "validate" in result or "__py.validate" in result
        assert "(data, options)" in result
    
    def test_custom_decorator_with_defaults(self):
        """Custom decorator on function with defaults"""
        code = """
@authenticate
def get_profile(user_id, include_details=True):
    pass
"""
        result = transpile(code)
        assert "authenticate" in result
        assert "include_details = true" in result
    
    def test_custom_no_parentheses(self):
        """Custom decorator without parentheses"""
        code = """
@singleton
def get_instance():
    pass
"""
        result = transpile(code)
        assert "singleton" in result
    
    def test_custom_lambda_style_arg(self):
        """Custom decorator with complex arg (not lambda)"""
        code = """
@cache(100)
def fetch():
    pass
"""
        result = transpile(code)
        assert "cache(100)" in result


# =============================================================================
# STACKED DECORATORS (10 tests)
# =============================================================================

class TestStackedDecorators:
    """Test multiple stacked decorators."""
    
    def test_two_decorators(self):
        """Two stacked decorators"""
        code = """
@log_calls
@memoize
def compute(x):
    return x * 2
"""
        result = transpile(code)
        assert "__py.log_calls" in result
        assert "__py.memoize" in result
        # log_calls should wrap memoize
        assert result.find("log_calls") < result.find("memoize")
    
    def test_three_decorators(self):
        """Three stacked decorators"""
        code = """
@timed
@log_calls
@memoize
def process(data):
    return transform(data)
"""
        result = transpile(code)
        assert "__py.timed" in result
        assert "__py.log_calls" in result
        assert "__py.memoize" in result
    
    def test_mixed_builtin_custom(self):
        """Mix of builtin and custom decorators"""
        code = """
@memoize
@custom
def foo():
    pass
"""
        result = transpile(code)
        assert "__py.memoize" in result
        assert "custom" in result
    
    def test_decorators_with_args(self):
        """Stacked decorators with args"""
        code = """
@throttle(100)
@debounce(200)
def handler():
    pass
"""
        result = transpile(code)
        assert "__py.throttle(100)" in result
        assert "__py.debounce(200)" in result
    
    def test_decorator_order_preserved(self):
        """Decorator application order is preserved"""
        code = """
@a
@b
@c
def foo():
    pass
"""
        result = transpile(code)
        # a wraps b wraps c wraps function
        a_pos = result.find("a(")
        b_pos = result.find("b(")
        c_pos = result.find("c(")
        assert a_pos < b_pos < c_pos
    
    def test_many_decorators(self):
        """Many stacked decorators"""
        code = """
@d1
@d2
@d3
@d4
def foo():
    pass
"""
        result = transpile(code)
        assert result.count("(function foo") == 1
    
    def test_stacked_with_args_and_no_args(self):
        """Mix of decorators with and without args"""
        code = """
@retry(3)
@memoize
@deprecated('use new_func')
def old_func():
    pass
"""
        result = transpile(code)
        assert "__py.retry(3)" in result
        assert "__py.memoize" in result
        assert "__py.deprecated" in result
    
    def test_stacked_async(self):
        """Stacked decorators on async function"""
        code = """
@memoize
@timed
async def fetch_data():
    return await get_data()
"""
        result = transpile(code)
        assert "__py.memoize" in result
        assert "__py.timed" in result
        assert "async function fetch_data" in result
    
    def test_stacked_preserves_function(self):
        """Stacked decorators preserve function body"""
        code = """
@a
@b
def foo(x):
    return x * 2
"""
        result = transpile(code)
        assert "return" in result
        assert "x" in result
    
    def test_stacked_complex_body(self):
        """Stacked decorators with complex function body"""
        code = """
@log_calls
@memoize
def process(items):
    result = []
    for item in items:
        if item.active:
            result.append(item)
    return result
"""
        result = transpile(code)
        assert "__py.log_calls" in result
        assert "__py.memoize" in result
        assert "for" in result
        assert "if" in result


# =============================================================================
# ASYNC DECORATED (10 tests)
# =============================================================================

class TestAsyncDecorated:
    """Test decorators on async functions."""
    
    def test_async_memoize(self):
        """@memoize on async function"""
        code = """
@memoize
async def fetch_user(id):
    return await get_user(id)
"""
        result = transpile(code)
        assert "__py.memoize" in result
        assert "async function fetch_user" in result
    
    def test_async_throttle(self):
        """@throttle on async function"""
        code = """
@throttle(100)
async def handle_request(req):
    return await process(req)
"""
        result = transpile(code)
        assert "__py.throttle(100)" in result
        assert "async function handle_request" in result
    
    def test_async_debounce(self):
        """@debounce on async function"""
        code = """
@debounce(300)
async def search(query):
    return await api.search(query)
"""
        result = transpile(code)
        assert "__py.debounce(300)" in result
        assert "async function search" in result
    
    def test_async_custom_decorator(self):
        """Custom decorator on async function"""
        code = """
@authenticated
async def get_profile():
    return await fetch_profile()
"""
        result = transpile(code)
        assert "authenticated" in result
        assert "async function get_profile" in result
    
    def test_async_stacked(self):
        """Stacked decorators on async function"""
        code = """
@retry(3)
@memoize
async def fetch_data():
    return await api.fetch()
"""
        result = transpile(code)
        assert "__py.retry(3)" in result
        assert "__py.memoize" in result
        assert "async function fetch_data" in result
    
    def test_async_preserves_await(self):
        """Decorators preserve await expressions"""
        code = """
@memoize
async def fetch_all():
    a = await get_a()
    b = await get_b()
    return a, b
"""
        result = transpile(code)
        assert result.count("await") == 2
    
    def test_async_with_args(self):
        """Async decorated with args"""
        code = """
@cache(ttl=60)
async def fetch_user(user_id):
    return await db.get(user_id)
"""
        result = transpile(code)
        assert "ttl: 60" in result
        assert "async function fetch_user" in result
    
    def test_async_with_defaults(self):
        """Async decorated with defaults"""
        code = """
@memoize
async def search(query, limit=10):
    return await api.search(query, limit)
"""
        result = transpile(code)
        assert "__py.memoize" in result
        assert "limit = 10" in result
    
    def test_async_multiple_awaits(self):
        """Async decorated with multiple awaits"""
        code = """
@timed
async def fetch_parallel():
    user = await get_user()
    posts = await get_posts()
    comments = await get_comments()
    return user, posts, comments
"""
        result = transpile(code)
        assert "__py.timed" in result
        assert result.count("await") == 3
    
    def test_async_loop_await(self):
        """Async decorated with await in loop"""
        code = """
@memoize
async def fetch_all(ids):
    results = []
    for id in ids:
        data = await fetch(id)
        results.append(data)
    return results
"""
        result = transpile(code)
        assert "__py.memoize" in result
        assert "await fetch(id)" in result


# =============================================================================
# EDGE CASES (10 tests - bonus)
# =============================================================================

class TestDecoratorEdgeCases:
    """Edge cases for decorators."""
    
    def test_decorator_multiple_functions(self):
        """Multiple decorated functions"""
        code = """
@memoize
def foo():
    pass

@memoize
def bar():
    pass
"""
        result = transpile(code)
        assert result.count("__py.memoize") == 2
    
    def test_decorator_then_regular(self):
        """Decorated followed by regular function"""
        code = """
@memoize
def cached():
    pass

def regular():
    pass
"""
        result = transpile(code)
        assert "__py.memoize" in result
        assert "function regular()" in result
    
    def test_decorator_function_name_preserved(self):
        """Function name is in output"""
        code = """
@memoize
def my_special_function():
    pass
"""
        result = transpile(code)
        assert "my_special_function" in result
    
    def test_decorator_empty_args(self):
        """Decorator with empty args tuple"""
        code = """
@setup()
def init():
    pass
"""
        result = transpile(code)
        # setup() with empty args becomes setup(function) 
        assert "setup" in result
    
    def test_decorator_numeric_arg(self):
        """Decorator with various numeric args"""
        code = """
@limit(1.5)
def foo():
    pass
"""
        result = transpile(code)
        assert "limit(1.5)" in result
    
    def test_decorator_boolean_arg(self):
        """Decorator with boolean arg"""
        code = """
@config(enabled=True)
def foo():
    pass
"""
        result = transpile(code)
        assert "enabled: true" in result
    
    def test_decorator_none_arg(self):
        """Decorator with None arg"""
        code = """
@config(default=None)
def foo():
    pass
"""
        result = transpile(code)
        assert "default: null" in result
    
    def test_decorator_list_arg(self):
        """Decorator with list arg"""
        code = """
@accept([1, 2, 3])
def foo():
    pass
"""
        result = transpile(code)
        assert "[1, 2, 3]" in result
    
    def test_decorator_dict_arg(self):
        """Decorator with dict arg"""
        code = """
@config({'key': 'value'})
def foo():
    pass
"""
        result = transpile(code)
        assert '"key"' in result or "'key'" in result
    
    def test_mixed_decorated_and_regular(self):
        """Mix of decorated and regular functions"""
        code = """
@memoize
def a():
    pass

def b():
    pass

@throttle(100)
def c():
    pass

def d():
    pass
"""
        result = transpile(code)
        assert "__py.memoize" in result
        assert "__py.throttle(100)" in result
        assert "function b()" in result
        assert "function d()" in result
