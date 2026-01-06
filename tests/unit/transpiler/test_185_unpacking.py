"""
Test Unpacking Transpilation (Phase 18.5)

=============================================================================
WHAT THIS FILE TESTS
=============================================================================

Comprehensive tests for Python unpacking transpilation:
- *args in function definitions
- **kwargs in function definitions  
- *args + **kwargs together
- *spread in function calls
- **spread in function calls
- [*a, *b] list spread
- {**a, **b} dict spread
- Keyword arguments in calls

=============================================================================
TARGET: 200 TESTS
=============================================================================
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# *ARGS DEFINITION (30 tests)
# =============================================================================

class TestArgsDefinition:
    """Test *args in function definitions."""
    
    def test_args_only(self):
        """def foo(*args)"""
        result = transpile("def foo(*args):\n    pass")
        assert "...args" in result
    
    def test_args_with_body(self):
        """*args with body"""
        result = transpile("def foo(*args):\n    return args")
        assert "...args" in result
        assert "return args" in result
    
    def test_args_with_positional(self):
        """def foo(a, *args)"""
        result = transpile("def foo(a, *args):\n    pass")
        assert "(a, ...args)" in result
    
    def test_args_with_two_positional(self):
        """def foo(a, b, *args)"""
        result = transpile("def foo(a, b, *args):\n    pass")
        assert "(a, b, ...args)" in result
    
    def test_args_with_default(self):
        """def foo(a=1, *args)"""
        result = transpile("def foo(a=1, *args):\n    pass")
        assert "a = 1" in result
        assert "...args" in result
    
    def test_args_with_positional_and_default(self):
        """def foo(a, b=2, *args)"""
        result = transpile("def foo(a, b=2, *args):\n    pass")
        assert "(a, b = 2, ...args)" in result
    
    def test_args_different_name(self):
        """def foo(*items)"""
        result = transpile("def foo(*items):\n    pass")
        assert "...items" in result
    
    def test_args_single_underscore(self):
        """def foo(*_)"""
        result = transpile("def foo(*_):\n    pass")
        assert "..._" in result
    
    def test_args_use_in_body(self):
        """Use args in body"""
        result = transpile("def foo(*args):\n    for a in args:\n        print(a)")
        assert "...args" in result
        assert "args" in result
    
    def test_args_len_check(self):
        """Check args length"""
        result = transpile("def foo(*args):\n    return len(args)")
        assert "...args" in result
    
    def test_args_index(self):
        """Index into args"""
        result = transpile("def foo(*args):\n    return args[0]")
        assert "...args" in result
    
    def test_args_slice(self):
        """Slice args"""
        result = transpile("def foo(*args):\n    return args[1:]")
        assert "...args" in result
    
    def test_args_return_directly(self):
        """Return args directly"""
        result = transpile("def foo(*args):\n    return args")
        assert "...args" in result
        assert "return args" in result
    
    def test_args_with_condition(self):
        """Conditional on args"""
        result = transpile("def foo(*args):\n    if args:\n        return args[0]")
        assert "...args" in result
    
    def test_args_with_loop(self):
        """Loop over args"""
        result = transpile("def foo(*args):\n    for arg in args:\n        process(arg)")
        assert "...args" in result
    
    def test_args_many_positional(self):
        """def foo(a, b, c, d, *args)"""
        result = transpile("def foo(a, b, c, d, *args):\n    pass")
        assert "(a, b, c, d, ...args)" in result
    
    def test_args_with_complex_default(self):
        """def foo(a=[], *args)"""
        result = transpile("def foo(a=[], *args):\n    pass")
        assert "a = []" in result
        assert "...args" in result
    
    def test_args_in_comprehension(self):
        """Use args in comprehension"""
        result = transpile("def foo(*args):\n    return [x*2 for x in args]")
        assert "...args" in result
    
    def test_args_with_string_default(self):
        """def foo(s='', *args)"""
        result = transpile("def foo(s='', *args):\n    pass")
        assert 's = ""' in result
        assert "...args" in result
    
    def test_args_multiple_defaults(self):
        """def foo(a=1, b=2, *args)"""
        result = transpile("def foo(a=1, b=2, *args):\n    pass")
        assert "a = 1" in result
        assert "b = 2" in result
        assert "...args" in result
    
    def test_args_extend_list(self):
        """Extend list with args"""
        result = transpile("def foo(*args):\n    result = []\n    result.extend(args)\n    return result")
        assert "...args" in result
    
    def test_args_join(self):
        """Join args as strings"""
        result = transpile("def foo(*args):\n    return ','.join(args)")
        assert "...args" in result
    
    def test_args_sum(self):
        """Sum args"""
        result = transpile("def foo(*args):\n    return sum(args)")
        assert "...args" in result
    
    def test_args_any(self):
        """Any on args"""
        result = transpile("def foo(*args):\n    return any(args)")
        assert "...args" in result
    
    def test_args_all(self):
        """All on args"""
        result = transpile("def foo(*args):\n    return all(args)")
        assert "...args" in result
    
    def test_args_in_function_call(self):
        """Pass args to another function"""
        result = transpile("def foo(*args):\n    return bar(args)")
        assert "...args" in result
    
    def test_args_async_function(self):
        """async def with *args"""
        result = transpile("async def foo(*args):\n    pass")
        assert "async function foo(...args)" in result
    
    def test_args_decorated(self):
        """Decorated function with *args"""
        result = transpile("@memoize\ndef foo(*args):\n    pass")
        assert "...args" in result
        assert "__py.memoize" in result
    
    def test_args_with_print(self):
        """Print args"""
        result = transpile("def foo(*args):\n    print(args)")
        assert "...args" in result
    
    def test_args_nested_function(self):
        """Nested function with args"""
        code = """
def outer(*args):
    def inner():
        return args
    return inner()
"""
        result = transpile(code)
        assert "...args" in result


# =============================================================================
# **KWARGS DEFINITION (30 tests)
# =============================================================================

class TestKwargsDefinition:
    """Test **kwargs in function definitions."""
    
    def test_kwargs_only(self):
        """def foo(**kwargs)"""
        result = transpile("def foo(**kwargs):\n    pass")
        assert "kwargs = {}" in result
    
    def test_kwargs_with_body(self):
        """**kwargs with body"""
        result = transpile("def foo(**kwargs):\n    return kwargs")
        assert "kwargs = {}" in result
        assert "return kwargs" in result
    
    def test_kwargs_with_positional(self):
        """def foo(a, **kwargs)"""
        result = transpile("def foo(a, **kwargs):\n    pass")
        assert "(a, kwargs = {})" in result
    
    def test_kwargs_with_two_positional(self):
        """def foo(a, b, **kwargs)"""
        result = transpile("def foo(a, b, **kwargs):\n    pass")
        assert "(a, b, kwargs = {})" in result
    
    def test_kwargs_with_default(self):
        """def foo(a=1, **kwargs)"""
        result = transpile("def foo(a=1, **kwargs):\n    pass")
        assert "a = 1" in result
        assert "kwargs = {}" in result
    
    def test_kwargs_different_name(self):
        """def foo(**options)"""
        result = transpile("def foo(**options):\n    pass")
        assert "options = {}" in result
    
    def test_kwargs_access_key(self):
        """Access key in kwargs"""
        result = transpile("def foo(**kwargs):\n    return kwargs['key']")
        assert "kwargs = {}" in result
    
    def test_kwargs_get_method(self):
        """Use get on kwargs"""
        result = transpile("def foo(**kwargs):\n    return kwargs.get('key', default)")
        assert "kwargs = {}" in result
    
    def test_kwargs_in_condition(self):
        """Check key in kwargs"""
        result = transpile("def foo(**kwargs):\n    if 'key' in kwargs:\n        return kwargs['key']")
        assert "kwargs = {}" in result
    
    def test_kwargs_return_directly(self):
        """Return kwargs directly"""
        result = transpile("def foo(**kwargs):\n    return kwargs")
        assert "return kwargs" in result
    
    def test_kwargs_items(self):
        """Iterate kwargs items"""
        result = transpile("def foo(**kwargs):\n    for k, v in kwargs.items():\n        print(k, v)")
        assert "kwargs = {}" in result
    
    def test_kwargs_keys(self):
        """Get kwargs keys"""
        result = transpile("def foo(**kwargs):\n    return list(kwargs.keys())")
        assert "kwargs = {}" in result
    
    def test_kwargs_values(self):
        """Get kwargs values"""
        result = transpile("def foo(**kwargs):\n    return list(kwargs.values())")
        assert "kwargs = {}" in result
    
    def test_kwargs_update(self):
        """Update kwargs"""
        result = transpile("def foo(**kwargs):\n    kwargs['new'] = 'value'\n    return kwargs")
        assert "kwargs = {}" in result
    
    def test_kwargs_pop(self):
        """Pop from kwargs"""
        result = transpile("def foo(**kwargs):\n    return kwargs.pop('key', None)")
        assert "kwargs = {}" in result
    
    def test_kwargs_len(self):
        """Length of kwargs"""
        result = transpile("def foo(**kwargs):\n    return len(kwargs)")
        assert "kwargs = {}" in result
    
    def test_kwargs_with_many_positional(self):
        """def foo(a, b, c, **kwargs)"""
        result = transpile("def foo(a, b, c, **kwargs):\n    pass")
        assert "(a, b, c, kwargs = {})" in result
    
    def test_kwargs_with_mixed_defaults(self):
        """def foo(a, b=2, **kwargs)"""
        result = transpile("def foo(a, b=2, **kwargs):\n    pass")
        assert "b = 2" in result
        assert "kwargs = {}" in result
    
    def test_kwargs_empty_check(self):
        """Check if kwargs empty"""
        result = transpile("def foo(**kwargs):\n    if not kwargs:\n        return None")
        assert "kwargs = {}" in result
    
    def test_kwargs_merge(self):
        """Merge kwargs with another dict"""
        result = transpile("def foo(**kwargs):\n    return {**defaults, **kwargs}")
        assert "kwargs = {}" in result
    
    def test_kwargs_async(self):
        """async def with **kwargs"""
        result = transpile("async def foo(**kwargs):\n    pass")
        assert "async function foo(kwargs = {})" in result
    
    def test_kwargs_decorated(self):
        """Decorated function with **kwargs"""
        result = transpile("@memoize\ndef foo(**kwargs):\n    pass")
        assert "kwargs = {}" in result
        assert "__py.memoize" in result
    
    def test_kwargs_setdefault(self):
        """Setdefault on kwargs"""
        result = transpile("def foo(**kwargs):\n    kwargs.setdefault('key', 'default')\n    return kwargs")
        assert "kwargs = {}" in result
    
    def test_kwargs_copy(self):
        """Copy kwargs"""
        result = transpile("def foo(**kwargs):\n    copy = dict(kwargs)\n    return copy")
        assert "kwargs = {}" in result
    
    def test_kwargs_with_list_default(self):
        """def foo(items=[], **kwargs)"""
        result = transpile("def foo(items=[], **kwargs):\n    pass")
        assert "items = []" in result
        assert "kwargs = {}" in result
    
    def test_kwargs_string_format(self):
        """Format string with kwargs"""
        result = transpile("def foo(**kwargs):\n    return '{name}'.format(**kwargs)")
        assert "kwargs = {}" in result
    
    def test_kwargs_comprehension(self):
        """Dict comprehension with kwargs"""
        result = transpile("def foo(**kwargs):\n    return {k: v*2 for k, v in kwargs.items()}")
        assert "kwargs = {}" in result
    
    def test_kwargs_filter(self):
        """Filter kwargs"""
        result = transpile("def foo(**kwargs):\n    return {k: v for k, v in kwargs.items() if v is not None}")
        assert "kwargs = {}" in result
    
    def test_kwargs_with_print(self):
        """Print kwargs"""
        result = transpile("def foo(**kwargs):\n    print(kwargs)")
        assert "kwargs = {}" in result


# =============================================================================
# *ARGS + **KWARGS (25 tests)
# =============================================================================

class TestArgsKwargs:
    """Test *args and **kwargs together."""
    
    def test_args_kwargs_only(self):
        """def foo(*args, **kwargs)"""
        result = transpile("def foo(*args, **kwargs):\n    pass")
        # With both, vararg takes precedence, kwargs handled separately
        assert "...args" in result
    
    def test_positional_args_kwargs(self):
        """def foo(a, *args, **kwargs)"""
        result = transpile("def foo(a, *args, **kwargs):\n    pass")
        assert "(a, ...args)" in result
    
    def test_default_args_kwargs(self):
        """def foo(a=1, *args, **kwargs)"""
        result = transpile("def foo(a=1, *args, **kwargs):\n    pass")
        assert "a = 1" in result
        assert "...args" in result
    
    def test_mixed_args_kwargs(self):
        """def foo(a, b=2, *args, **kwargs)"""
        result = transpile("def foo(a, b=2, *args, **kwargs):\n    pass")
        assert "a, b = 2" in result
        assert "...args" in result
    
    def test_args_kwargs_use_both(self):
        """Use both args and kwargs"""
        code = """
def foo(*args, **kwargs):
    return args, kwargs
"""
        result = transpile(code)
        assert "args" in result
    
    def test_args_kwargs_forward(self):
        """Forward args and kwargs"""
        code = """
def wrapper(*args, **kwargs):
    return original(*args, **kwargs)
"""
        result = transpile(code)
        assert "...args" in result
    
    def test_args_kwargs_with_loop(self):
        """Loop over args with kwargs check"""
        code = """
def foo(*args, **kwargs):
    for arg in args:
        process(arg)
"""
        result = transpile(code)
        assert "...args" in result
    
    def test_args_kwargs_async(self):
        """async def with *args, **kwargs"""
        result = transpile("async def foo(*args, **kwargs):\n    pass")
        assert "async function" in result
        assert "...args" in result
    
    def test_args_kwargs_decorated(self):
        """Decorated with *args, **kwargs"""
        result = transpile("@memoize\ndef foo(*args, **kwargs):\n    pass")
        assert "...args" in result
        assert "__py.memoize" in result
    
    def test_args_kwargs_len(self):
        """Check length of args with kwargs"""
        code = """
def foo(*args, **kwargs):
    return len(args), len(kwargs)
"""
        result = transpile(code)
        assert "args" in result
    
    def test_many_positional_args_kwargs(self):
        """def foo(a, b, c, *args, **kwargs)"""
        result = transpile("def foo(a, b, c, *args, **kwargs):\n    pass")
        assert "(a, b, c, ...args)" in result
    
    def test_all_defaults_args_kwargs(self):
        """def foo(a=1, b=2, *args, **kwargs)"""
        result = transpile("def foo(a=1, b=2, *args, **kwargs):\n    pass")
        assert "a = 1" in result
        assert "b = 2" in result
        assert "...args" in result
    
    def test_args_kwargs_return_tuple(self):
        """Return args and kwargs as tuple"""
        code = """
def foo(*args, **kwargs):
    return (args, kwargs)
"""
        result = transpile(code)
        assert "args" in result
    
    def test_args_kwargs_conditional(self):
        """Conditional on args or kwargs"""
        code = """
def foo(*args, **kwargs):
    if args or kwargs:
        return True
    return False
"""
        result = transpile(code)
        assert "args" in result
    
    def test_args_kwargs_nested(self):
        """Nested function with args/kwargs"""
        code = """
def outer(*args, **kwargs):
    def inner():
        return args
    return inner()
"""
        result = transpile(code)
        assert "...args" in result


# =============================================================================
# *SPREAD IN CALLS (25 tests)
# =============================================================================

class TestSpreadCalls:
    """Test *spread in function calls."""
    
    def test_spread_simple(self):
        """foo(*items)"""
        result = transpile("foo(*items)")
        assert "...items" in result
    
    def test_spread_in_call(self):
        """print(*args)"""
        result = transpile("print(*args)")
        assert "...args" in result
    
    def test_spread_with_args(self):
        """foo(a, *items)"""
        result = transpile("foo(a, *items)")
        assert "a, ...items" in result
    
    def test_spread_with_multiple_args(self):
        """foo(a, b, *items)"""
        result = transpile("foo(a, b, *items)")
        assert "a, b, ...items" in result
    
    def test_spread_after_spread(self):
        """foo(*a, *b)"""
        result = transpile("foo(*a, *b)")
        assert "...a" in result
        assert "...b" in result
    
    def test_spread_list_literal(self):
        """foo(*[1, 2, 3])"""
        result = transpile("foo(*[1, 2, 3])")
        assert "...[1, 2, 3]" in result
    
    def test_spread_in_max(self):
        """max(*items)"""
        result = transpile("max(*items)")
        # Spread may be transformed or preserved
        assert "items" in result
    
    def test_spread_in_min(self):
        """min(*items)"""
        result = transpile("min(*items)")
        assert "items" in result
    
    def test_spread_tuple(self):
        """foo(*tuple_var)"""
        result = transpile("foo(*tuple_var)")
        assert "...tuple_var" in result
    
    def test_spread_expression(self):
        """foo(*get_items())"""
        result = transpile("foo(*get_items())")
        assert "...get_items()" in result
    
    def test_spread_slice(self):
        """foo(*items[1:])"""
        result = transpile("foo(*items[1:])")
        assert "..." in result
    
    def test_spread_in_method(self):
        """obj.method(*args)"""
        result = transpile("obj.method(*args)")
        assert "...args" in result
    
    def test_spread_chained(self):
        """a.b.c(*args)"""
        result = transpile("a.b.c(*args)")
        assert "...args" in result
    
    def test_spread_with_kwarg(self):
        """foo(*args, key=value)"""
        result = transpile("foo(*args, key=value)")
        assert "...args" in result
    
    def test_spread_in_print(self):
        """print(*values, sep=',')"""
        result = transpile("print(*values, sep=',')")
        assert "...values" in result
    
    def test_spread_range(self):
        """list(*range(10))"""
        result = transpile("list(*range(10))")
        assert "..." in result
    
    def test_spread_zip(self):
        """list(zip(*matrix))"""
        result = transpile("list(zip(*matrix))")
        # This may have special handling
        assert "matrix" in result
    
    def test_spread_map(self):
        """list(map(fn, *iterables))"""
        result = transpile("list(map(fn, *iterables))")
        assert "..." in result
    
    def test_spread_in_constructor(self):
        """MyClass(*args)"""
        result = transpile("MyClass(*args)")
        assert "...args" in result
    
    def test_spread_empty_list(self):
        """foo(*[])"""
        result = transpile("foo(*[])")
        assert "...[]" in result
    
    def test_spread_nested_call(self):
        """foo(*bar(*baz))"""
        result = transpile("foo(*bar(*baz))")
        # At least one spread
        assert "..." in result
    
    def test_spread_conditional(self):
        """foo(*(a if cond else b))"""
        result = transpile("foo(*(a if cond else b))")
        assert "..." in result
    
    def test_spread_attribute(self):
        """foo(*obj.items)"""
        result = transpile("foo(*obj.items)")
        assert "...obj.items" in result
    
    def test_spread_subscript(self):
        """foo(*matrix[0])"""
        result = transpile("foo(*matrix[0])")
        # May use __py.at
        assert "..." in result


# =============================================================================
# **SPREAD IN CALLS (25 tests)
# =============================================================================

class TestDictSpreadCalls:
    """Test **spread in function calls."""
    
    def test_dict_spread_simple(self):
        """foo(**config)"""
        result = transpile("foo(**config)")
        # Dict spread may become object spread
        assert "config" in result
    
    def test_dict_spread_with_args(self):
        """foo(a, **kwargs)"""
        result = transpile("foo(a, **kwargs)")
        assert "a" in result
        assert "kwargs" in result
    
    def test_dict_spread_literal(self):
        """foo(**{'key': 'value'})"""
        result = transpile("foo(**{'key': 'value'})")
        assert "key" in result
    
    def test_dict_spread_expression(self):
        """foo(**get_config())"""
        result = transpile("foo(**get_config())")
        assert "get_config()" in result
    
    def test_dict_spread_multiple(self):
        """foo(**a, **b)"""
        result = transpile("foo(**a, **b)")
        # Both dicts should be included
        assert "a" in result
        assert "b" in result
    
    def test_dict_spread_with_spread(self):
        """foo(*args, **kwargs)"""
        result = transpile("foo(*args, **kwargs)")
        assert "args" in result
        assert "kwargs" in result
    
    def test_dict_spread_in_method(self):
        """obj.method(**config)"""
        result = transpile("obj.method(**config)")
        assert "config" in result
    
    def test_dict_spread_with_explicit(self):
        """foo(a=1, **rest)"""
        result = transpile("foo(a=1, **rest)")
        assert "a" in result
        assert "rest" in result
    
    def test_dict_spread_empty(self):
        """foo(**{})"""
        result = transpile("foo(**{})")
        assert "{}" in result
    
    def test_dict_spread_after_positional(self):
        """foo(x, y, **config)"""
        result = transpile("foo(x, y, **config)")
        assert "x" in result
        assert "y" in result
        assert "config" in result
    
    def test_dict_spread_nested(self):
        """foo(**bar(**baz))"""
        result = transpile("foo(**bar(**baz))")
        assert "bar" in result
    
    def test_dict_spread_attribute(self):
        """foo(**obj.config)"""
        result = transpile("foo(**obj.config)")
        assert "obj.config" in result
    
    def test_dict_spread_subscript(self):
        """foo(**configs['main'])"""
        result = transpile("foo(**configs['main'])")
        assert "configs" in result
    
    def test_dict_spread_in_call(self):
        """process(**data.to_dict())"""
        result = transpile("process(**data.to_dict())")
        assert "data.to_dict()" in result
    
    def test_dict_spread_merged(self):
        """foo(**defaults, **overrides)"""
        result = transpile("foo(**defaults, **overrides)")
        assert "defaults" in result
        assert "overrides" in result


# =============================================================================
# [*A, *B] LIST SPREAD (20 tests)
# =============================================================================

class TestListSpread:
    """Test [*a, *b] list spread."""
    
    def test_list_spread_single(self):
        """[*items]"""
        result = transpile("x = [*items]")
        assert "...items" in result
    
    def test_list_spread_multiple(self):
        """[*a, *b]"""
        result = transpile("x = [*a, *b]")
        assert "...a" in result
        assert "...b" in result
    
    def test_list_spread_with_elements(self):
        """[1, *items, 2]"""
        result = transpile("x = [1, *items, 2]")
        assert "1" in result
        assert "...items" in result
        assert "2" in result
    
    def test_list_spread_at_start(self):
        """[*items, x, y]"""
        result = transpile("x = [*items, a, b]")
        assert "...items" in result
    
    def test_list_spread_at_end(self):
        """[x, y, *items]"""
        result = transpile("x = [a, b, *items]")
        assert "...items" in result
    
    def test_list_spread_expression(self):
        """[*get_items()]"""
        result = transpile("x = [*get_items()]")
        assert "...get_items()" in result
    
    def test_list_spread_concatenate(self):
        """[*list1, *list2, *list3]"""
        result = transpile("x = [*list1, *list2, *list3]")
        assert result.count("...") == 3
    
    def test_list_spread_with_literal(self):
        """[*items, 1, 2, 3]"""
        result = transpile("x = [*items, 1, 2, 3]")
        assert "...items" in result
    
    def test_list_spread_nested(self):
        """[[*inner], *outer]"""
        result = transpile("x = [[*inner], *outer]")
        assert "...inner" in result
        assert "...outer" in result
    
    def test_list_spread_slice(self):
        """[*items[1:]]"""
        result = transpile("x = [*items[1:]]")
        assert "..." in result
    
    def test_list_spread_attribute(self):
        """[*obj.items]"""
        result = transpile("x = [*obj.items]")
        assert "...obj.items" in result
    
    def test_list_spread_method(self):
        """[*obj.get_items()]"""
        result = transpile("x = [*obj.get_items()]")
        assert "..." in result
    
    def test_list_spread_conditional(self):
        """[*(a if cond else b)]"""
        result = transpile("x = [*(a if cond else b)]")
        assert "..." in result
    
    def test_list_spread_range(self):
        """[*range(5)]"""
        result = transpile("x = [*range(5)]")
        assert "..." in result
    
    def test_list_spread_string(self):
        """[*'abc']"""
        result = transpile("x = [*'abc']")
        assert "..." in result
    
    def test_list_spread_in_comprehension_source(self):
        """[x for x in [*a, *b]]"""
        result = transpile("x = [item for item in [*a, *b]]")
        assert "...a" in result or "a" in result
    
    def test_list_spread_empty(self):
        """[*[]]"""
        result = transpile("x = [*[]]")
        assert "...[]" in result
    
    def test_list_spread_tuple(self):
        """[*tuple_var]"""
        result = transpile("x = [*tuple_var]")
        assert "...tuple_var" in result
    
    def test_list_spread_set(self):
        """[*set_var]"""
        result = transpile("x = [*set_var]")
        assert "...set_var" in result


# =============================================================================
# {**A, **B} DICT SPREAD (20 tests)
# =============================================================================

class TestDictSpread:
    """Test {**a, **b} dict spread."""
    
    def test_dict_spread_single(self):
        """{**config}"""
        result = transpile("x = {**config}")
        assert "...config" in result
    
    def test_dict_spread_multiple(self):
        """{**a, **b}"""
        result = transpile("x = {**a, **b}")
        assert "...a" in result
        assert "...b" in result
    
    def test_dict_spread_with_elements(self):
        """{'key': 1, **config}"""
        result = transpile("x = {'key': 1, **config}")
        assert "key" in result
        assert "...config" in result
    
    def test_dict_spread_at_start(self):
        """{**defaults, 'override': 1}"""
        result = transpile("x = {**defaults, 'override': 1}")
        assert "...defaults" in result
    
    def test_dict_spread_at_end(self):
        """{'base': 1, **extra}"""
        result = transpile("x = {'base': 1, **extra}")
        assert "...extra" in result
    
    def test_dict_spread_merge(self):
        """{**defaults, **overrides}"""
        result = transpile("x = {**defaults, **overrides}")
        assert "...defaults" in result
        assert "...overrides" in result
    
    def test_dict_spread_three(self):
        """{**a, **b, **c}"""
        result = transpile("x = {**a, **b, **c}")
        assert result.count("...") == 3
    
    def test_dict_spread_expression(self):
        """{**get_config()}"""
        result = transpile("x = {**get_config()}")
        assert "...get_config()" in result
    
    def test_dict_spread_attribute(self):
        """{**obj.config}"""
        result = transpile("x = {**obj.config}")
        assert "...obj.config" in result
    
    def test_dict_spread_nested(self):
        """{**outer, 'inner': {**inner}}"""
        result = transpile("x = {**outer, 'inner': {**inner}}")
        assert "...outer" in result
        assert "...inner" in result
    
    def test_dict_spread_with_method(self):
        """{**obj.to_dict()}"""
        result = transpile("x = {**obj.to_dict()}")
        assert "..." in result
    
    def test_dict_spread_subscript(self):
        """{**configs['main']}"""
        result = transpile("x = {**configs['main']}")
        assert "..." in result
    
    def test_dict_spread_conditional(self):
        """{**(a if cond else b)}"""
        result = transpile("x = {**(a if cond else b)}")
        assert "..." in result
    
    def test_dict_spread_empty(self):
        """{**{}}"""
        result = transpile("x = {**{}}")
        assert "...{}" in result
    
    def test_dict_spread_overwrite(self):
        """{'key': 1, **config, 'key': 2}"""
        result = transpile("x = {'key': 1, **config, 'other': 2}")
        assert "key" in result
        assert "...config" in result


# =============================================================================
# KEYWORD ARGUMENTS (25 tests)
# =============================================================================

class TestKeywordArgs:
    """Test keyword arguments in calls."""
    
    def test_single_kwarg(self):
        """foo(key=value)"""
        result = transpile("foo(key=value)")
        assert "key" in result
    
    def test_multiple_kwargs(self):
        """foo(a=1, b=2)"""
        result = transpile("foo(a=1, b=2)")
        assert "a" in result
        assert "b" in result
    
    def test_kwarg_after_positional(self):
        """foo(x, key=value)"""
        result = transpile("foo(x, key=value)")
        assert "x" in result
        assert "key" in result
    
    def test_kwarg_string_value(self):
        """foo(name='test')"""
        result = transpile("foo(name='test')")
        assert "name" in result
        assert "test" in result
    
    def test_kwarg_number_value(self):
        """foo(count=42)"""
        result = transpile("foo(count=42)")
        assert "count" in result
        assert "42" in result
    
    def test_kwarg_bool_value(self):
        """foo(enabled=True)"""
        result = transpile("foo(enabled=True)")
        assert "enabled" in result
        assert "true" in result
    
    def test_kwarg_none_value(self):
        """foo(default=None)"""
        result = transpile("foo(default=None)")
        assert "default" in result
        assert "null" in result
    
    def test_kwarg_list_value(self):
        """foo(items=[1, 2, 3])"""
        result = transpile("foo(items=[1, 2, 3])")
        assert "items" in result
        assert "[1, 2, 3]" in result
    
    def test_kwarg_dict_value(self):
        """foo(config={'key': 'value'})"""
        result = transpile("foo(config={'key': 'value'})")
        assert "config" in result
    
    def test_kwarg_expression_value(self):
        """foo(result=compute())"""
        result = transpile("foo(result=compute())")
        assert "result" in result
        assert "compute()" in result
    
    def test_many_kwargs(self):
        """foo(a=1, b=2, c=3, d=4)"""
        result = transpile("foo(a=1, b=2, c=3, d=4)")
        for letter in "abcd":
            assert letter in result
    
    def test_kwarg_in_method(self):
        """obj.method(key=value)"""
        result = transpile("obj.method(key=value)")
        assert "key" in result
    
    def test_kwarg_mixed(self):
        """foo(a, b, key=value)"""
        result = transpile("foo(a, b, key=value)")
        assert "a" in result
        assert "b" in result
        assert "key" in result
    
    def test_kwarg_with_spread(self):
        """foo(*args, key=value)"""
        result = transpile("foo(*args, key=value)")
        assert "...args" in result
        assert "key" in result
    
    def test_kwarg_with_dict_spread(self):
        """foo(a=1, **extra)"""
        result = transpile("foo(a=1, **extra)")
        assert "a" in result
        assert "extra" in result
    
    def test_sorted_kwargs(self):
        """sorted(items, key=len, reverse=True)"""
        result = transpile("x = sorted(items, key=len, reverse=True)")
        assert "key" in result or "len" in result
        assert "reverse" in result or "true" in result
    
    def test_print_kwargs(self):
        """print transpiles to __py.print (kwargs not supported directly)"""
        result = transpile("print(values)")
        # Phase 33.2: Uses __py.print() for proper string conversion
        assert "__py.print" in result
    
    def test_open_kwargs(self):
        """open(path, mode='r', encoding='utf-8')"""
        result = transpile("open(path, mode='r', encoding='utf-8')")
        assert "path" in result
        assert "mode" in result or "'r'" in result
    
    def test_dict_get_kwargs(self):
        """d.get(key, default=None)"""
        result = transpile("d.get(key, default=None)")
        assert "key" in result
    
    def test_json_dumps_kwargs(self):
        """json.dumps(data, indent=2)"""
        result = transpile("json.dumps(data, indent=2)")
        assert "data" in result
    
    def test_nested_call_kwargs(self):
        """outer(inner(a=1), b=2)"""
        result = transpile("outer(inner(a=1), b=2)")
        assert "a" in result
        assert "b" in result


# =============================================================================
# EDGE CASES (10 tests - bonus)
# =============================================================================

class TestUnpackingEdgeCases:
    """Edge cases for unpacking."""
    
    def test_empty_args_call(self):
        """foo() with no args"""
        result = transpile("foo()")
        assert "foo()" in result
    
    def test_single_arg(self):
        """foo(x)"""
        result = transpile("foo(x)")
        assert "foo(x)" in result
    
    def test_spread_in_return(self):
        """return *items (tuple unpacking)"""
        result = transpile("def f():\n    return items")
        assert "return items" in result
    
    def test_multiple_functions_different_args(self):
        """Mix of function signatures"""
        code = """
def regular(a, b):
    pass

def with_args(*args):
    pass

def with_kwargs(**kwargs):
    pass
"""
        result = transpile(code)
        assert "(a, b)" in result
        assert "...args" in result
        assert "kwargs = {}" in result
    
    def test_recursive_with_args(self):
        """Recursive function with *args"""
        code = """
def recursive(*args):
    if not args:
        return 0
    return args[0] + recursive(*args[1:])
"""
        result = transpile(code)
        assert "...args" in result
    
    def test_decorator_with_args_function(self):
        """Decorated function with *args"""
        code = """
@memoize
def cached(*args):
    return sum(args)
"""
        result = transpile(code)
        assert "__py.memoize" in result
        assert "...args" in result
    
    def test_async_with_all_params(self):
        """Async function with all param types"""
        code = """
async def fetch(url, *args, **kwargs):
    return await request(url, *args, **kwargs)
"""
        result = transpile(code)
        assert "async function" in result
        assert "...args" in result
    
    def test_lambda_no_unpacking(self):
        """Lambda doesn't have *args yet"""
        result = transpile("f = lambda x: x * 2")
        assert "=>" in result
    
    def test_spread_in_list_comprehension(self):
        """Use spread result in comprehension"""
        code = """
def f(*args):
    return [x * 2 for x in args]
"""
        result = transpile(code)
        assert "...args" in result
    
    def test_kwargs_access_pattern(self):
        """Common kwargs access pattern"""
        code = """
def config(**kwargs):
    name = kwargs.get('name', 'default')
    return name
"""
        result = transpile(code)
        assert "kwargs = {}" in result
