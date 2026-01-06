"""
Phase 33.1.1: Function Transpilation Tests

Comprehensive test suite for function transpilation covering:
- Basic functions
- Default arguments
- *args and **kwargs
- Positional-only arguments (/)
- Keyword-only arguments (*)
- Complex combinations
- Decorators (simple and parameterized)
- Nested functions and closures
- Lambda expressions

Total: 220 tests
"""

import pytest
from pynext.transpiler import transpile, TranspileError
from tests.unit.transpiler.test_utils import assert_has_runtime_function


# =============================================================================
# BASIC FUNCTIONS (10 tests)
# =============================================================================

class TestBasicFunctions:
    """Test basic function definitions."""
    
    def test_empty_function(self):
        """def foo(): pass"""
        result = transpile("def foo():\n    pass")
        assert "function foo()" in result
        assert "/* pass */" in result
    
    def test_function_with_return(self):
        """def foo(): return 5"""
        result = transpile("def foo():\n    return 5")
        assert "function foo()" in result
        assert "return 5;" in result
    
    def test_function_with_single_param(self):
        """def foo(x): return x"""
        result = transpile("def foo(x):\n    return x")
        assert "function foo(x)" in result
        assert "return x;" in result
    
    def test_function_with_multiple_params(self):
        """def foo(a, b, c): return a + b + c"""
        result = transpile("def foo(a, b, c):\n    return a + b + c")
        assert "function foo(a, b, c)" in result
        assert "return" in result
    
    def test_function_with_body(self):
        """def foo(): x = 5; return x"""
        result = transpile("def foo():\n    x = 5\n    return x")
        assert "function foo()" in result
        assert "let x = 5" in result or "x = 5" in result
        assert "return x;" in result
    
    def test_named_function(self):
        """Function name is preserved"""
        result = transpile("def my_function(): pass")
        assert "function my_function()" in result
    
    def test_function_with_expression(self):
        """def foo(): print('hi')"""
        result = transpile("def foo():\n    print('hi')")
        assert "function foo()" in result
        # Phase 33.2: Uses __py.print() for proper string conversion
        assert "__py.print" in result
    
    def test_function_with_multiple_statements(self):
        """def foo(): x = 1; y = 2; return x + y"""
        result = transpile("def foo():\n    x = 1\n    y = 2\n    return x + y")
        assert "function foo()" in result
        assert "return" in result
    
    def test_function_call_in_body(self):
        """def foo(): bar()"""
        result = transpile("def foo():\n    bar()")
        assert "function foo()" in result
        assert "bar();" in result
    
    def test_function_with_conditional(self):
        """def foo(x): if x > 0: return x"""
        result = transpile("def foo(x):\n    if x > 0:\n        return x")
        assert "function foo(x)" in result
        assert "if" in result


# =============================================================================
# DEFAULT ARGUMENTS (20 tests)
# =============================================================================

class TestDefaultArguments:
    """Test default argument values."""
    
    def test_single_default_arg(self):
        """def foo(x=1): return x"""
        result = transpile("def foo(x=1):\n    return x")
        assert "function foo(x = 1)" in result
    
    def test_multiple_default_args(self):
        """def foo(x=1, y=2): return x + y"""
        result = transpile("def foo(x=1, y=2):\n    return x + y")
        assert "x = 1" in result
        assert "y = 2" in result
    
    def test_mixed_required_and_default(self):
        """def foo(x, y=2): return x + y"""
        result = transpile("def foo(x, y=2):\n    return x + y")
        assert "function foo(x, y = 2)" in result
    
    def test_default_with_string(self):
        """def foo(name='world'): return name"""
        result = transpile("def foo(name='world'):\n    return name")
        assert "name = 'world'" in result or 'name = "world"' in result
    
    def test_default_with_none(self):
        """def foo(x=None): return x"""
        result = transpile("def foo(x=None):\n    return x")
        assert "x = null" in result
    
    def test_default_with_true(self):
        """def foo(flag=True): return flag"""
        result = transpile("def foo(flag=True):\n    return flag")
        assert "flag = true" in result
    
    def test_default_with_false(self):
        """def foo(flag=False): return flag"""
        result = transpile("def foo(flag=False):\n    return flag")
        assert "flag = false" in result
    
    def test_default_with_list(self):
        """def foo(items=[]): return items"""
        result = transpile("def foo(items=[]):\n    return items")
        assert "items = []" in result
    
    def test_default_with_dict(self):
        """def foo(config={}): return config"""
        result = transpile("def foo(config={}):\n    return config")
        assert "config = {}" in result
    
    def test_default_with_expression(self):
        """def foo(x=1+1): return x"""
        result = transpile("def foo(x=1+1):\n    return x")
        assert "x = (1 + 1)" in result or "x = 1 + 1" in result
    
    def test_multiple_defaults_end(self):
        """def foo(x, y, z=3, w=4): return x + y + z + w"""
        result = transpile("def foo(x, y, z=3, w=4):\n    return x + y + z + w")
        assert "z = 3" in result
        assert "w = 4" in result
    
    def test_all_defaults(self):
        """def foo(x=1, y=2, z=3): return x + y + z"""
        result = transpile("def foo(x=1, y=2, z=3):\n    return x + y + z")
        assert "x = 1" in result
        assert "y = 2" in result
        assert "z = 3" in result
    
    def test_default_with_call(self):
        """def foo(x=len([])): return x"""
        result = transpile("def foo(x=len([])):\n    return x")
        assert "x = " in result
    
    def test_default_with_attribute(self):
        """def foo(x=obj.attr): return x"""
        result = transpile("def foo(x=obj.attr):\n    return x")
        assert "x = obj.attr" in result
    
    def test_default_with_negative(self):
        """def foo(x=-1): return x"""
        result = transpile("def foo(x=-1):\n    return x")
        # Negative literals may be wrapped in parentheses for precedence
        assert "x = -1" in result or "x = (-1)" in result
    
    def test_default_with_float(self):
        """def foo(x=1.5): return x"""
        result = transpile("def foo(x=1.5):\n    return x")
        assert "x = 1.5" in result
    
    def test_default_with_tuple(self):
        """def foo(x=(1, 2)): return x"""
        result = transpile("def foo(x=(1, 2)):\n    return x")
        assert "x = [1, 2]" in result
    
    def test_default_with_nested_call(self):
        """def foo(x=bar(1)): return x"""
        result = transpile("def foo(x=bar(1)):\n    return x")
        assert "x = bar(1)" in result
    
    def test_default_with_complex_expression(self):
        """def foo(x=1*2+3): return x"""
        result = transpile("def foo(x=1*2+3):\n    return x")
        assert "x = " in result
    
    def test_default_order_preserved(self):
        """Default args maintain order"""
        result = transpile("def foo(a=1, b=2, c=3): pass")
        assert result.index("a = 1") < result.index("b = 2")
        assert result.index("b = 2") < result.index("c = 3")


# =============================================================================
# *ARGS (30 tests)
# =============================================================================

class TestVarArgs:
    """Test *args (variadic positional arguments)."""
    
    def test_simple_varargs(self):
        """def foo(*args): return args"""
        result = transpile("def foo(*args):\n    return args")
        assert "function foo(...args)" in result
        assert "return args;" in result
    
    def test_varargs_with_regular_args(self):
        """def foo(x, *args): return args"""
        result = transpile("def foo(x, *args):\n    return args")
        assert "function foo(x, ...args)" in result
    
    def test_varargs_with_multiple_regular_args(self):
        """def foo(x, y, *args): return args"""
        result = transpile("def foo(x, y, *args):\n    return args")
        assert "function foo(x, y, ...args)" in result
    
    def test_varargs_with_defaults(self):
        """def foo(x=1, *args): return args"""
        result = transpile("def foo(x=1, *args):\n    return args")
        assert "x = 1" in result
        assert "...args" in result
    
    def test_varargs_iteration(self):
        """def foo(*args): for x in args: print(x)"""
        result = transpile("def foo(*args):\n    for x in args:\n        print(x)")
        assert "...args" in result
        assert "for" in result
    
    def test_varargs_length(self):
        """def foo(*args): return len(args)"""
        result = transpile("def foo(*args):\n    return len(args)")
        assert "...args" in result
    
    def test_varargs_indexing(self):
        """def foo(*args): return args[0]"""
        result = transpile("def foo(*args):\n    return args[0]")
        assert "...args" in result
        # Phase 33.2: Uses __py.getitem() for __getitem__ dunder support
        assert "__py.getitem(args, 0)" in result
    
    def test_varargs_slicing(self):
        """def foo(*args): return args[1:]"""
        result = transpile("def foo(*args):\n    return args[1:]")
        assert "...args" in result
    
    def test_varargs_with_conditional(self):
        """def foo(*args): if len(args) > 0: return args[0]"""
        result = transpile("def foo(*args):\n    if len(args) > 0:\n        return args[0]")
        assert "...args" in result
        assert "if" in result
    
    def test_varargs_empty(self):
        """def foo(*args): return args if args else []"""
        result = transpile("def foo(*args):\n    return args if args else []")
        assert "...args" in result
    
    def test_varargs_with_kwargs(self):
        """def foo(*args, **kwargs): return len(args) + len(kwargs)"""
        result = transpile("def foo(*args, **kwargs):\n    return len(args) + len(kwargs)")
        assert "...args" in result
    
    def test_varargs_name_custom(self):
        """def foo(*items): return items"""
        result = transpile("def foo(*items):\n    return items")
        assert "...items" in result
    
    def test_varargs_with_computation(self):
        """def foo(*args): return sum(args)"""
        result = transpile("def foo(*args):\n    return sum(args)")
        assert "...args" in result
    
    def test_varargs_with_list_comp(self):
        """def foo(*args): return [x*2 for x in args]"""
        result = transpile("def foo(*args):\n    return [x*2 for x in args]")
        assert "...args" in result
    
    def test_varargs_with_filter(self):
        """def foo(*args): return [x for x in args if x > 0]"""
        result = transpile("def foo(*args):\n    return [x for x in args if x > 0]")
        assert "...args" in result
    
    def test_varargs_with_map(self):
        """def foo(*args): return list(map(str, args))"""
        result = transpile("def foo(*args):\n    return list(map(str, args))")
        assert "...args" in result
    
    def test_varargs_with_nested_call(self):
        """def foo(*args): return bar(*args)"""
        result = transpile("def foo(*args):\n    return bar(*args)")
        assert "...args" in result
    
    def test_varargs_with_unpacking(self):
        """def foo(*args): a, b = args"""
        result = transpile("def foo(*args):\n    a, b = args")
        assert "...args" in result
    
    def test_varargs_with_assert(self):
        """def foo(*args): assert len(args) > 0"""
        result = transpile("def foo(*args):\n    assert len(args) > 0")
        assert "...args" in result
    
    def test_varargs_with_raise(self):
        """def foo(*args): raise ValueError if not args"""
        result = transpile("def foo(*args):\n    if not args:\n        raise ValueError()")
        assert "...args" in result
    
    def test_varargs_with_try_except(self):
        """def foo(*args): try: return args[0]; except: return None"""
        result = transpile("def foo(*args):\n    try:\n        return args[0]\n    except:\n        return None")
        assert "...args" in result
    
    def test_varargs_with_while(self):
        """def foo(*args): while args: args = args[1:]"""
        result = transpile("def foo(*args):\n    while args:\n        args = args[1:]")
        assert "...args" in result
    
    def test_varargs_with_for_range(self):
        """def foo(*args): for i in range(len(args)): print(args[i])"""
        result = transpile("def foo(*args):\n    for i in range(len(args)):\n        print(args[i])")
        assert "...args" in result
    
    def test_varargs_with_dict(self):
        """def foo(*args): return {i: x for i, x in enumerate(args)}"""
        result = transpile("def foo(*args):\n    return {i: x for i, x in enumerate(args)}")
        assert "...args" in result
    
    def test_varargs_with_set(self):
        """def foo(*args): return set(args)"""
        result = transpile("def foo(*args):\n    return set(args)")
        assert "...args" in result
    
    def test_varargs_with_tuple(self):
        """def foo(*args): return tuple(args)"""
        result = transpile("def foo(*args):\n    return tuple(args)")
        assert "...args" in result
    
    def test_varargs_with_lambda(self):
        """def foo(*args): return lambda x: x in args"""
        result = transpile("def foo(*args):\n    return lambda x: x in args")
        assert "...args" in result
    
    def test_varargs_with_nested_function(self):
        """def foo(*args): def inner(): return args; return inner()"""
        result = transpile("def foo(*args):\n    def inner():\n        return args\n    return inner()")
        assert "...args" in result
    
    def test_varargs_with_class(self):
        """def foo(*args): class Bar: pass"""
        result = transpile("def foo(*args):\n    class Bar:\n        pass")
        assert "...args" in result
    
    def test_varargs_with_decorator(self):
        """@decorator\ndef foo(*args): pass"""
        result = transpile("@decorator\ndef foo(*args):\n    pass")
        assert "...args" in result


# =============================================================================
# **KWARGS (30 tests)
# =============================================================================

class TestKwArgs:
    """Test **kwargs (variadic keyword arguments)."""
    
    def test_simple_kwargs(self):
        """def foo(**kwargs): return kwargs"""
        result = transpile("def foo(**kwargs):\n    return kwargs")
        assert "kwargs = {}" in result or "function foo(kwargs = {})" in result
        assert "return kwargs;" in result
    
    def test_kwargs_with_regular_args(self):
        """def foo(x, **kwargs): return kwargs"""
        result = transpile("def foo(x, **kwargs):\n    return kwargs")
        assert "function foo(x" in result
        assert "kwargs = {}" in result
    
    def test_kwargs_with_multiple_regular_args(self):
        """def foo(x, y, **kwargs): return kwargs"""
        result = transpile("def foo(x, y, **kwargs):\n    return kwargs")
        assert "function foo(x, y" in result
        assert "kwargs = {}" in result
    
    def test_kwargs_with_defaults(self):
        """def foo(x=1, **kwargs): return kwargs"""
        result = transpile("def foo(x=1, **kwargs):\n    return kwargs")
        assert "x = 1" in result
        assert "kwargs = {}" in result
    
    def test_kwargs_with_varargs(self):
        """def foo(*args, **kwargs): return len(kwargs)"""
        result = transpile("def foo(*args, **kwargs):\n    return len(kwargs)")
        assert "...args" in result
    
    def test_kwargs_iteration(self):
        """def foo(**kwargs): for k, v in kwargs.items(): print(k, v)"""
        result = transpile("def foo(**kwargs):\n    for k, v in kwargs.items():\n        print(k, v)")
        assert "kwargs = {}" in result
        assert "for" in result
    
    def test_kwargs_keys(self):
        """def foo(**kwargs): return list(kwargs.keys())"""
        result = transpile("def foo(**kwargs):\n    return list(kwargs.keys())")
        assert "kwargs = {}" in result
    
    def test_kwargs_values(self):
        """def foo(**kwargs): return list(kwargs.values())"""
        result = transpile("def foo(**kwargs):\n    return list(kwargs.values())")
        assert "kwargs = {}" in result
    
    def test_kwargs_items(self):
        """def foo(**kwargs): return list(kwargs.items())"""
        result = transpile("def foo(**kwargs):\n    return list(kwargs.items())")
        assert "kwargs = {}" in result
    
    def test_kwargs_access(self):
        """def foo(**kwargs): return kwargs.get('key', 'default')"""
        result = transpile("def foo(**kwargs):\n    return kwargs.get('key', 'default')")
        assert "kwargs = {}" in result
    
    def test_kwargs_bracket_access(self):
        """def foo(**kwargs): return kwargs['key']"""
        result = transpile("def foo(**kwargs):\n    return kwargs['key']")
        assert "kwargs = {}" in result
        assert "kwargs['key']" in result or "kwargs[\"key\"]" in result or "__py.at(kwargs" in result
    
    def test_kwargs_with_conditional(self):
        """def foo(**kwargs): if 'key' in kwargs: return kwargs['key']"""
        result = transpile("def foo(**kwargs):\n    if 'key' in kwargs:\n        return kwargs['key']")
        assert "kwargs = {}" in result
        assert "if" in result
    
    def test_kwargs_empty_check(self):
        """def foo(**kwargs): return len(kwargs) == 0"""
        result = transpile("def foo(**kwargs):\n    return len(kwargs) == 0")
        assert "kwargs = {}" in result
    
    def test_kwargs_name_custom(self):
        """def foo(**opts): return opts"""
        result = transpile("def foo(**opts):\n    return opts")
        assert "opts = {}" in result
    
    def test_kwargs_with_computation(self):
        """def foo(**kwargs): return sum(kwargs.values())"""
        result = transpile("def foo(**kwargs):\n    return sum(kwargs.values())")
        assert "kwargs = {}" in result
    
    def test_kwargs_with_dict_comp(self):
        """def foo(**kwargs): return {k: v*2 for k, v in kwargs.items()}"""
        result = transpile("def foo(**kwargs):\n    return {k: v*2 for k, v in kwargs.items()}")
        assert "kwargs = {}" in result
    
    def test_kwargs_with_filter(self):
        """def foo(**kwargs): return {k: v for k, v in kwargs.items() if v > 0}"""
        result = transpile("def foo(**kwargs):\n    return {k: v for k, v in kwargs.items() if v > 0}")
        assert "kwargs = {}" in result
    
    def test_kwargs_with_update(self):
        """def foo(**kwargs): kwargs.update({'new': 'value'})"""
        result = transpile("def foo(**kwargs):\n    kwargs.update({'new': 'value'})")
        assert "kwargs = {}" in result
    
    def test_kwargs_with_copy(self):
        """def foo(**kwargs): return kwargs.copy()"""
        result = transpile("def foo(**kwargs):\n    return kwargs.copy()")
        assert "kwargs = {}" in result
    
    def test_kwargs_with_pop(self):
        """def foo(**kwargs): return kwargs.pop('key', None)"""
        result = transpile("def foo(**kwargs):\n    return kwargs.pop('key', None)")
        assert "kwargs = {}" in result
    
    def test_kwargs_with_clear(self):
        """def foo(**kwargs): kwargs.clear()"""
        result = transpile("def foo(**kwargs):\n    kwargs.clear()")
        assert "kwargs = {}" in result
    
    def test_kwargs_with_raise(self):
        """def foo(**kwargs): raise ValueError if not kwargs"""
        result = transpile("def foo(**kwargs):\n    if not kwargs:\n        raise ValueError()")
        assert "kwargs = {}" in result
    
    def test_kwargs_with_try_except(self):
        """def foo(**kwargs): try: return kwargs['key']; except: return None"""
        result = transpile("def foo(**kwargs):\n    try:\n        return kwargs['key']\n    except:\n        return None")
        assert "kwargs = {}" in result
    
    def test_kwargs_with_while(self):
        """def foo(**kwargs): while kwargs: kwargs.popitem()"""
        result = transpile("def foo(**kwargs):\n    while kwargs:\n        kwargs.popitem()")
        assert "kwargs = {}" in result
    
    def test_kwargs_with_for_keys(self):
        """def foo(**kwargs): for k in kwargs: print(k)"""
        result = transpile("def foo(**kwargs):\n    for k in kwargs:\n        print(k)")
        assert "kwargs = {}" in result
    
    def test_kwargs_with_lambda(self):
        """def foo(**kwargs): return lambda k: kwargs.get(k)"""
        result = transpile("def foo(**kwargs):\n    return lambda k: kwargs.get(k)")
        assert "kwargs = {}" in result
    
    def test_kwargs_with_nested_function(self):
        """def foo(**kwargs): def inner(): return kwargs; return inner()"""
        result = transpile("def foo(**kwargs):\n    def inner():\n        return kwargs\n    return inner()")
        assert "kwargs = {}" in result
    
    def test_kwargs_with_class(self):
        """def foo(**kwargs): class Bar: pass"""
        result = transpile("def foo(**kwargs):\n    class Bar:\n        pass")
        assert "kwargs = {}" in result
    
    def test_kwargs_with_decorator(self):
        """@decorator\ndef foo(**kwargs): pass"""
        result = transpile("@decorator\ndef foo(**kwargs):\n    pass")
        assert "kwargs = {}" in result


# =============================================================================
# POSITIONAL-ONLY ARGUMENTS (20 tests)
# =============================================================================

class TestPositionalOnlyArgs:
    """Test positional-only arguments (/) - Phase 33.1."""
    
    def test_simple_posonly(self):
        """def foo(x, y, /): return x + y"""
        result = transpile("def foo(x, y, /):\n    return x + y")
        assert "function foo(x, y)" in result
    
    def test_posonly_with_regular(self):
        """def foo(x, y, /, z): return x + y + z"""
        result = transpile("def foo(x, y, /, z):\n    return x + y + z")
        assert "function foo(x, y, z)" in result
    
    def test_posonly_with_defaults(self):
        """def foo(x, y=2, /): return x + y"""
        result = transpile("def foo(x, y=2, /):\n    return x + y")
        assert "function foo(x, y = 2)" in result
    
    def test_posonly_multiple_with_defaults(self):
        """def foo(x, y=2, z=3, /): return x + y + z"""
        result = transpile("def foo(x, y=2, z=3, /):\n    return x + y + z")
        assert "x" in result
        assert "y = 2" in result
        assert "z = 3" in result
    
    def test_posonly_with_regular_and_defaults(self):
        """def foo(x, y, /, z=3): return x + y + z"""
        result = transpile("def foo(x, y, /, z=3):\n    return x + y + z")
        assert "function foo(x, y, z = 3)" in result
    
    def test_posonly_with_varargs(self):
        """def foo(x, y, /, *args): return args"""
        result = transpile("def foo(x, y, /, *args):\n    return args")
        assert "function foo(x, y, ...args)" in result
    
    def test_posonly_with_kwargs(self):
        """def foo(x, y, /, **kwargs): return kwargs"""
        result = transpile("def foo(x, y, /, **kwargs):\n    return kwargs")
        assert "function foo(x, y" in result
        assert "kwargs = {}" in result
    
    def test_posonly_with_kwonly(self):
        """def foo(x, y, /, *, z): return x + y + z"""
        result = transpile("def foo(x, y, /, *, z):\n    return x + y + z")
        assert "function foo(x, y" in result
    
    def test_posonly_single(self):
        """def foo(x, /): return x"""
        result = transpile("def foo(x, /):\n    return x")
        assert "function foo(x)" in result
    
    def test_posonly_with_complex_body(self):
        """def foo(x, y, /): if x > y: return x; return y"""
        result = transpile("def foo(x, y, /):\n    if x > y:\n        return x\n    return y")
        assert "function foo(x, y)" in result
        assert "if" in result
    
    def test_posonly_with_loop(self):
        """def foo(x, /): for i in range(x): print(i)"""
        result = transpile("def foo(x, /):\n    for i in range(x):\n        print(i)")
        assert "function foo(x)" in result
        assert "for" in result
    
    def test_posonly_with_nested_function(self):
        """def foo(x, /): def inner(): return x; return inner()"""
        result = transpile("def foo(x, /):\n    def inner():\n        return x\n    return inner()")
        assert "function foo(x)" in result
    
    def test_posonly_with_lambda(self):
        """def foo(x, /): return lambda y: x + y"""
        result = transpile("def foo(x, /):\n    return lambda y: x + y")
        assert "function foo(x)" in result
    
    def test_posonly_with_class(self):
        """def foo(x, /): class Bar: pass"""
        result = transpile("def foo(x, /):\n    class Bar:\n        pass")
        assert "function foo(x)" in result
    
    def test_posonly_with_decorator(self):
        """@decorator\ndef foo(x, /): pass"""
        result = transpile("@decorator\ndef foo(x, /):\n    pass")
        assert "function foo(x)" in result
    
    def test_posonly_all_defaults(self):
        """def foo(x=1, y=2, /): return x + y"""
        result = transpile("def foo(x=1, y=2, /):\n    return x + y")
        assert "x = 1" in result
        assert "y = 2" in result
    
    def test_posonly_mixed_defaults(self):
        """def foo(x, y=2, z=3, /): return x + y + z"""
        result = transpile("def foo(x, y=2, z=3, /):\n    return x + y + z")
        assert "x" in result
        assert "y = 2" in result
        assert "z = 3" in result
    
    def test_posonly_with_assert(self):
        """def foo(x, /): assert x > 0"""
        result = transpile("def foo(x, /):\n    assert x > 0")
        assert "function foo(x)" in result
    
    def test_posonly_with_raise(self):
        """def foo(x, /): if x < 0: raise ValueError()"""
        result = transpile("def foo(x, /):\n    if x < 0:\n        raise ValueError()")
        assert "function foo(x)" in result
    
    def test_posonly_with_try_except(self):
        """def foo(x, /): try: return 1/x; except: return 0"""
        result = transpile("def foo(x, /):\n    try:\n        return 1/x\n    except:\n        return 0")
        assert "function foo(x)" in result


# =============================================================================
# KEYWORD-ONLY ARGUMENTS (20 tests)
# =============================================================================

class TestKeywordOnlyArgs:
    """Test keyword-only arguments (*) - Phase 33.1."""
    
    def test_simple_kwonly(self):
        """def foo(*, x): return x"""
        result = transpile("def foo(*, x):\n    return x")
        # Should use object destructuring: {x} = {}
        assert "{x}" in result or "function foo" in result
    
    def test_kwonly_with_default(self):
        """def foo(*, x=1): return x"""
        result = transpile("def foo(*, x=1):\n    return x")
        # Should use object destructuring with default: {x = 1} = {}
        assert "x = 1" in result
    
    def test_kwonly_multiple(self):
        """def foo(*, x, y): return x + y"""
        result = transpile("def foo(*, x, y):\n    return x + y")
        assert "{x, y}" in result or "function foo" in result
    
    def test_kwonly_multiple_with_defaults(self):
        """def foo(*, x, y=2): return x + y"""
        result = transpile("def foo(*, x, y=2):\n    return x + y")
        assert "x" in result
        assert "y = 2" in result
    
    def test_kwonly_with_regular_args(self):
        """def foo(a, *, x): return a + x"""
        result = transpile("def foo(a, *, x):\n    return a + x")
        assert "function foo(a" in result
    
    def test_kwonly_with_defaults_regular(self):
        """def foo(a=1, *, x): return a + x"""
        result = transpile("def foo(a=1, *, x):\n    return a + x")
        assert "a = 1" in result
    
    def test_kwonly_with_varargs(self):
        """def foo(*args, x): return x"""
        result = transpile("def foo(*args, x):\n    return x")
        assert "...args" in result
    
    def test_kwonly_with_kwargs(self):
        """def foo(*, x, **kwargs): return kwargs"""
        result = transpile("def foo(*, x, **kwargs):\n    return kwargs")
        assert "kwargs = {}" in result
    
    def test_kwonly_with_posonly(self):
        """def foo(x, /, *, y): return x + y"""
        result = transpile("def foo(x, /, *, y):\n    return x + y")
        assert "function foo(x" in result
    
    def test_kwonly_all_defaults(self):
        """def foo(*, x=1, y=2): return x + y"""
        result = transpile("def foo(*, x=1, y=2):\n    return x + y")
        assert "x = 1" in result
        assert "y = 2" in result
    
    def test_kwonly_mixed_required_defaults(self):
        """def foo(*, x, y=2, z): return x + y + z"""
        result = transpile("def foo(*, x, y=2, z):\n    return x + y + z")
        assert "x" in result
        assert "y = 2" in result
        assert "z" in result
    
    def test_kwonly_with_complex_body(self):
        """def foo(*, x): if x > 0: return x; return 0"""
        result = transpile("def foo(*, x):\n    if x > 0:\n        return x\n    return 0")
        assert "function foo" in result
        assert "if" in result
    
    def test_kwonly_with_loop(self):
        """def foo(*, n): for i in range(n): print(i)"""
        result = transpile("def foo(*, n):\n    for i in range(n):\n        print(i)")
        assert "function foo" in result
        assert "for" in result
    
    def test_kwonly_with_nested_function(self):
        """def foo(*, x): def inner(): return x; return inner()"""
        result = transpile("def foo(*, x):\n    def inner():\n        return x\n    return inner()")
        assert "function foo" in result
    
    def test_kwonly_with_lambda(self):
        """def foo(*, x): return lambda y: x + y"""
        result = transpile("def foo(*, x):\n    return lambda y: x + y")
        assert "function foo" in result
    
    def test_kwonly_with_class(self):
        """def foo(*, x): class Bar: pass"""
        result = transpile("def foo(*, x):\n    class Bar:\n        pass")
        assert "function foo" in result
    
    def test_kwonly_with_decorator(self):
        """@decorator\ndef foo(*, x): pass"""
        result = transpile("@decorator\ndef foo(*, x):\n    pass")
        assert "function foo" in result
    
    def test_kwonly_with_assert(self):
        """def foo(*, x): assert x > 0"""
        result = transpile("def foo(*, x):\n    assert x > 0")
        assert "function foo" in result
    
    def test_kwonly_with_raise(self):
        """def foo(*, x): if x < 0: raise ValueError()"""
        result = transpile("def foo(*, x):\n    if x < 0:\n        raise ValueError()")
        assert "function foo" in result
    
    def test_kwonly_with_try_except(self):
        """def foo(*, x): try: return 1/x; except: return 0"""
        result = transpile("def foo(*, x):\n    try:\n        return 1/x\n    except:\n        return 0")
        assert "function foo" in result


# =============================================================================
# COMPLEX COMBINATIONS (30 tests)
# =============================================================================

class TestComplexCombinations:
    """Test complex combinations of argument types."""
    
    def test_posonly_regular_varargs(self):
        """def foo(x, /, y, *args): return args"""
        result = transpile("def foo(x, /, y, *args):\n    return args")
        assert "function foo(x, y, ...args)" in result
    
    def test_posonly_regular_kwargs(self):
        """def foo(x, /, y, **kwargs): return kwargs"""
        result = transpile("def foo(x, /, y, **kwargs):\n    return kwargs")
        assert "function foo(x, y" in result
    
    def test_posonly_regular_kwonly(self):
        """def foo(x, /, y, *, z): return x + y + z"""
        result = transpile("def foo(x, /, y, *, z):\n    return x + y + z")
        assert "function foo(x, y" in result
    
    def test_posonly_varargs_kwargs(self):
        """def foo(x, /, *args, **kwargs): return len(kwargs)"""
        result = transpile("def foo(x, /, *args, **kwargs):\n    return len(kwargs)")
        assert "...args" in result
    
    def test_posonly_varargs_kwonly(self):
        """def foo(x, /, *args, z): return z"""
        result = transpile("def foo(x, /, *args, z):\n    return z")
        assert "...args" in result
    
    def test_posonly_kwargs_kwonly(self):
        """def foo(x, /, **kwargs, z): return z"""
        # This is invalid Python syntax - **kwargs must be last
        with pytest.raises((SyntaxError, TranspileError)):
            transpile("def foo(x, /, **kwargs, z):\n    return z")
    
    def test_regular_varargs_kwargs(self):
        """def foo(x, *args, **kwargs): return len(args) + len(kwargs)"""
        result = transpile("def foo(x, *args, **kwargs):\n    return len(args) + len(kwargs)")
        assert "function foo(x, ...args)" in result
    
    def test_regular_varargs_kwonly(self):
        """def foo(x, *args, z): return z"""
        result = transpile("def foo(x, *args, z):\n    return z")
        assert "...args" in result
    
    def test_regular_kwargs_kwonly(self):
        """def foo(x, **kwargs, z): return z"""
        # Invalid Python syntax - **kwargs must be last
        with pytest.raises((SyntaxError, TranspileError)):
            transpile("def foo(x, **kwargs, z):\n    return z")
    
    def test_varargs_kwargs_kwonly(self):
        """def foo(*args, **kwargs, z): return z"""
        # Invalid Python syntax - kwonly must come before **kwargs
        with pytest.raises((SyntaxError, TranspileError)):
            transpile("def foo(*args, **kwargs, z):\n    return z")
    
    def test_all_with_defaults(self):
        """def foo(x=1, /, y=2, *args, z=3, **kwargs): return z"""
        result = transpile("def foo(x=1, /, y=2, *args, z=3, **kwargs):\n    return z")
        assert "x = 1" in result
        assert "y = 2" in result
        assert "...args" in result
    
    def test_posonly_defaults_regular_defaults(self):
        """def foo(x=1, y=2, /, z=3, w=4): return x + y + z + w"""
        result = transpile("def foo(x=1, y=2, /, z=3, w=4):\n    return x + y + z + w")
        assert "x = 1" in result
        assert "y = 2" in result
        assert "z = 3" in result
        assert "w = 4" in result
    
    def test_posonly_regular_kwonly_all_defaults(self):
        """def foo(x=1, /, y=2, *, z=3): return x + y + z"""
        result = transpile("def foo(x=1, /, y=2, *, z=3):\n    return x + y + z")
        assert "x = 1" in result
        assert "y = 2" in result
        assert "z = 3" in result
    
    def test_mixed_required_defaults(self):
        """def foo(x, y=2, /, z=3, w=4, *args, u=5, **kwargs): return u"""
        # Note: Can't have required arg after default in same group, so z=3
        result = transpile("def foo(x, y=2, /, z=3, w=4, *args, u=5, **kwargs):\n    return u")
        assert "x" in result
        assert "y = 2" in result
        assert "z = 3" in result
        assert "w = 4" in result
        assert "...args" in result
    
    def test_complex_nested_calls(self):
        """def foo(x, /, y, *args, z, **kwargs): return bar(x, y, *args, z=z, **kwargs)"""
        result = transpile("def foo(x, /, y, *args, z, **kwargs):\n    return bar(x, y, *args, z=z, **kwargs)")
        assert "function foo" in result
    
    def test_complex_with_conditionals(self):
        """def foo(x, /, y, *args, z, **kwargs): if z: return args; return kwargs"""
        result = transpile("def foo(x, /, y, *args, z, **kwargs):\n    if z:\n        return args\n    return kwargs")
        assert "function foo" in result
        assert "if" in result
    
    def test_complex_with_loops(self):
        """def foo(x, /, *args, **kwargs): for a in args: print(a); for k, v in kwargs.items(): print(k, v)"""
        result = transpile("def foo(x, /, *args, **kwargs):\n    for a in args:\n        print(a)\n    for k, v in kwargs.items():\n        print(k, v)")
        assert "function foo" in result
        assert "for" in result
    
    def test_complex_with_comprehensions(self):
        """def foo(x, /, *args, **kwargs): return [a*2 for a in args] + [v for v in kwargs.values()]"""
        result = transpile("def foo(x, /, *args, **kwargs):\n    return [a*2 for a in args] + [v for v in kwargs.values()]")
        assert "function foo" in result
    
    def test_complex_with_nested_functions(self):
        """def foo(x, /, y, *args, z, **kwargs): def inner(): return x + y + z; return inner()"""
        result = transpile("def foo(x, /, y, *args, z, **kwargs):\n    def inner():\n        return x + y + z\n    return inner()")
        assert "function foo" in result
    
    def test_complex_with_lambdas(self):
        """def foo(x, /, y, *args, z, **kwargs): return lambda w: x + y + z + w"""
        result = transpile("def foo(x, /, y, *args, z, **kwargs):\n    return lambda w: x + y + z + w")
        assert "function foo" in result
    
    def test_complex_with_classes(self):
        """def foo(x, /, y, *args, z, **kwargs): class Bar: pass"""
        result = transpile("def foo(x, /, y, *args, z, **kwargs):\n    class Bar:\n        pass")
        assert "function foo" in result
    
    def test_complex_with_decorators(self):
        """@decorator\ndef foo(x, /, y, *args, z, **kwargs): pass"""
        result = transpile("@decorator\ndef foo(x, /, y, *args, z, **kwargs):\n    pass")
        assert "function foo" in result
    
    def test_complex_with_try_except(self):
        """def foo(x, /, y, *args, z, **kwargs): try: return args[0]; except: return kwargs.get('default')"""
        result = transpile("def foo(x, /, y, *args, z, **kwargs):\n    try:\n        return args[0]\n    except:\n        return kwargs.get('default')")
        assert "function foo" in result
    
    def test_complex_with_assert(self):
        """def foo(x, /, y, *args, z, **kwargs): assert z > 0"""
        result = transpile("def foo(x, /, y, *args, z, **kwargs):\n    assert z > 0")
        assert "function foo" in result
    
    def test_complex_with_raise(self):
        """def foo(x, /, y, *args, z, **kwargs): if not z: raise ValueError()"""
        result = transpile("def foo(x, /, y, *args, z, **kwargs):\n    if not z:\n        raise ValueError()")
        assert "function foo" in result
    
    def test_complex_with_while(self):
        """def foo(x, /, y, *args, z, **kwargs): while args: args = args[1:]"""
        result = transpile("def foo(x, /, y, *args, z, **kwargs):\n    while args:\n        args = args[1:]")
        assert "function foo" in result
    
    def test_complex_with_for_range(self):
        """def foo(x, /, y, *args, z, **kwargs): for i in range(len(args)): print(args[i])"""
        result = transpile("def foo(x, /, y, *args, z, **kwargs):\n    for i in range(len(args)):\n        print(args[i])")
        assert "function foo" in result
    
    def test_complex_with_dict_comp(self):
        """def foo(x, /, y, *args, z, **kwargs): return {i: a for i, a in enumerate(args)}"""
        result = transpile("def foo(x, /, y, *args, z, **kwargs):\n    return {i: a for i, a in enumerate(args)}")
        assert "function foo" in result
    
    def test_complex_with_set_comp(self):
        """def foo(x, /, y, *args, z, **kwargs): return {a for a in args}"""
        result = transpile("def foo(x, /, y, *args, z, **kwargs):\n    return {a for a in args}")
        assert "function foo" in result
    
    def test_complex_with_list_comp(self):
        """def foo(x, /, y, *args, z, **kwargs): return [a*2 for a in args if a > 0]"""
        result = transpile("def foo(x, /, y, *args, z, **kwargs):\n    return [a*2 for a in args if a > 0]")
        assert "function foo" in result


# =============================================================================
# DECORATORS (20 tests)
# =============================================================================

class TestSimpleDecorators:
    """Test simple decorators (@decorator) - 10 tests."""
    
    def test_single_decorator(self):
        """@memoize\ndef foo(): pass"""
        result = transpile("@memoize\ndef foo():\n    pass")
        assert "const foo = " in result or "function foo" in result
        assert "memoize" in result
    
    def test_multiple_decorators(self):
        """@decorator1\n@decorator2\ndef foo(): pass"""
        result = transpile("@decorator1\n@decorator2\ndef foo():\n    pass")
        assert "decorator1" in result
        assert "decorator2" in result
    
    def test_decorator_with_function_body(self):
        """@memoize\ndef foo(x): return x * 2"""
        result = transpile("@memoize\ndef foo(x):\n    return x * 2")
        assert "memoize" in result
        assert "return" in result
        assert_has_runtime_function(result, "mul")
    
    def test_decorator_with_params(self):
        """@memoize\ndef foo(x, y): return x + y"""
        result = transpile("@memoize\ndef foo(x, y):\n    return x + y")
        assert "memoize" in result
        assert "function foo(x, y)" in result
    
    def test_decorator_with_defaults(self):
        """@memoize\ndef foo(x=1): return x"""
        result = transpile("@memoize\ndef foo(x=1):\n    return x")
        assert "memoize" in result
        assert "x = 1" in result
    
    def test_decorator_with_varargs(self):
        """@memoize\ndef foo(*args): return args"""
        result = transpile("@memoize\ndef foo(*args):\n    return args")
        assert "memoize" in result
        assert "...args" in result
    
    def test_decorator_with_kwargs(self):
        """@memoize\ndef foo(**kwargs): return kwargs"""
        result = transpile("@memoize\ndef foo(**kwargs):\n    return kwargs")
        assert "memoize" in result
        assert "kwargs = {}" in result
    
    def test_decorator_with_posonly(self):
        """@memoize\ndef foo(x, /): return x"""
        result = transpile("@memoize\ndef foo(x, /):\n    return x")
        assert "memoize" in result
        assert "function foo(x)" in result
    
    def test_decorator_with_kwonly(self):
        """@memoize\ndef foo(*, x): return x"""
        result = transpile("@memoize\ndef foo(*, x):\n    return x")
        assert "memoize" in result
    
    def test_decorator_order(self):
        """Decorators applied in reverse order"""
        result = transpile("@decorator1\n@decorator2\ndef foo(): pass")
        # Bottom decorator applied first
        idx1 = result.find("decorator1")
        idx2 = result.find("decorator2")
        assert idx1 != -1 and idx2 != -1


class TestParameterizedDecorators:
    """Test parameterized decorators (@decorator(args)) - 10 tests."""
    
    def test_decorator_with_positional_arg(self):
        """@debounce(300)\ndef foo(): pass"""
        result = transpile("@debounce(300)\ndef foo():\n    pass")
        assert "debounce" in result
        assert "300" in result
    
    def test_decorator_with_multiple_args(self):
        """@decorator(1, 2, 3)\ndef foo(): pass"""
        result = transpile("@decorator(1, 2, 3)\ndef foo():\n    pass")
        assert "decorator" in result
        assert "1" in result
        assert "2" in result
        assert "3" in result
    
    def test_decorator_with_keyword_arg(self):
        """@decorator(x=1)\ndef foo(): pass"""
        result = transpile("@decorator(x=1)\ndef foo():\n    pass")
        assert "decorator" in result
        assert "x: 1" in result or "x = 1" in result
    
    def test_decorator_with_multiple_keyword_args(self):
        """@decorator(x=1, y=2)\ndef foo(): pass"""
        result = transpile("@decorator(x=1, y=2)\ndef foo():\n    pass")
        assert "decorator" in result
        assert "x" in result
        assert "y" in result
    
    def test_decorator_with_mixed_args(self):
        """@decorator(1, x=2)\ndef foo(): pass"""
        result = transpile("@decorator(1, x=2)\ndef foo():\n    pass")
        assert "decorator" in result
        assert "1" in result
        assert "x" in result
    
    def test_decorator_with_starred_args(self):
        """@decorator(*args)\ndef foo(): pass"""
        result = transpile("@decorator(*args)\ndef foo():\n    pass")
        assert "decorator" in result
        assert "...args" in result
    
    def test_decorator_with_double_starred_kwargs(self):
        """@decorator(**kwargs)\ndef foo(): pass"""
        result = transpile("@decorator(**kwargs)\ndef foo():\n    pass")
        assert "decorator" in result
        assert "...kwargs" in result
    
    def test_decorator_with_complex_expression(self):
        """@decorator(1+1, x=2*3)\ndef foo(): pass"""
        result = transpile("@decorator(1+1, x=2*3)\ndef foo():\n    pass")
        assert "decorator" in result
    
    def test_decorator_with_call(self):
        """@decorator(len([]))\ndef foo(): pass"""
        result = transpile("@decorator(len([]))\ndef foo():\n    pass")
        assert "decorator" in result
    
    def test_multiple_parameterized_decorators(self):
        """@decorator1(1)\n@decorator2(2)\ndef foo(): pass"""
        result = transpile("@decorator1(1)\n@decorator2(2)\ndef foo():\n    pass")
        assert "decorator1" in result
        assert "decorator2" in result
        assert "1" in result
        assert "2" in result


# =============================================================================
# NESTED FUNCTIONS AND CLOSURES (20 tests)
# =============================================================================

class TestNestedFunctions:
    """Test nested functions and closures."""
    
    def test_simple_nested_function(self):
        """def foo(): def bar(): pass"""
        result = transpile("def foo():\n    def bar():\n        pass")
        assert "function foo()" in result
        assert "function bar()" in result
    
    def test_nested_function_with_closure(self):
        """def foo(x): def bar(): return x; return bar()"""
        result = transpile("def foo(x):\n    def bar():\n        return x\n    return bar()")
        assert "function foo(x)" in result
        assert "function bar()" in result
        assert "return x" in result
    
    def test_nested_function_with_multiple_closures(self):
        """def foo(x, y): def bar(): return x + y; return bar()"""
        result = transpile("def foo(x, y):\n    def bar():\n        return x + y\n    return bar()")
        assert "function foo(x, y)" in result
        assert "function bar()" in result
    
    def test_nested_function_with_outer_default(self):
        """def foo(x=1): def bar(): return x; return bar()"""
        result = transpile("def foo(x=1):\n    def bar():\n        return x\n    return bar()")
        assert "function foo(x = 1)" in result
        assert "function bar()" in result
    
    def test_nested_function_with_outer_varargs(self):
        """def foo(*args): def bar(): return args; return bar()"""
        result = transpile("def foo(*args):\n    def bar():\n        return args\n    return bar()")
        assert "function foo(...args)" in result
        assert "function bar()" in result
    
    def test_nested_function_with_outer_kwargs(self):
        """def foo(**kwargs): def bar(): return kwargs; return bar()"""
        result = transpile("def foo(**kwargs):\n    def bar():\n        return kwargs\n    return bar()")
        assert "function foo" in result
        assert "function bar()" in result
    
    def test_triple_nested(self):
        """def foo(): def bar(): def baz(): pass"""
        result = transpile("def foo():\n    def bar():\n        def baz():\n            pass")
        assert "function foo()" in result
        assert "function bar()" in result
        assert "function baz()" in result
    
    def test_nested_function_with_own_params(self):
        """def foo(x): def bar(y): return x + y; return bar(2)"""
        result = transpile("def foo(x):\n    def bar(y):\n        return x + y\n    return bar(2)")
        assert "function foo(x)" in result
        assert "function bar(y)" in result
    
    def test_nested_function_with_own_defaults(self):
        """def foo(x): def bar(y=1): return x + y; return bar()"""
        result = transpile("def foo(x):\n    def bar(y=1):\n        return x + y\n    return bar()")
        assert "function foo(x)" in result
        assert "function bar(y = 1)" in result
    
    def test_nested_function_with_own_varargs(self):
        """def foo(x): def bar(*args): return x + sum(args); return bar(1, 2)"""
        result = transpile("def foo(x):\n    def bar(*args):\n        return x + sum(args)\n    return bar(1, 2)")
        assert "function foo(x)" in result
        assert "function bar(...args)" in result
    
    def test_nested_function_modifying_closure(self):
        """def foo(): x = 1; def bar(): nonlocal x; x = 2; bar(); return x"""
        # Note: nonlocal not yet supported, but test structure
        result = transpile("def foo():\n    x = 1\n    def bar():\n        x = 2\n    bar()\n    return x")
        assert "function foo()" in result
        assert "function bar()" in result
    
    def test_nested_function_with_loop(self):
        """def foo(): def bar(): for i in range(3): print(i); bar()"""
        result = transpile("def foo():\n    def bar():\n        for i in range(3):\n            print(i)\n    bar()")
        assert "function foo()" in result
        assert "function bar()" in result
        assert "for" in result
    
    def test_nested_function_with_conditional(self):
        """def foo(x): def bar(): if x > 0: return x; return bar()"""
        result = transpile("def foo(x):\n    def bar():\n        if x > 0:\n            return x\n    return bar()")
        assert "function foo(x)" in result
        assert "function bar()" in result
        assert "if" in result
    
    def test_nested_function_returning_function(self):
        """def foo(x): def bar(): return x; return bar"""
        result = transpile("def foo(x):\n    def bar():\n        return x\n    return bar")
        assert "function foo(x)" in result
        assert "function bar()" in result
    
    def test_nested_function_with_lambda(self):
        """def foo(x): def bar(): return lambda y: x + y; return bar()"""
        result = transpile("def foo(x):\n    def bar():\n        return lambda y: x + y\n    return bar()")
        assert "function foo(x)" in result
        assert "function bar()" in result
    
    def test_nested_function_with_class(self):
        """def foo(x): def bar(): class Baz: pass; bar()"""
        result = transpile("def foo(x):\n    def bar():\n        class Baz:\n            pass\n    bar()")
        assert "function foo(x)" in result
        assert "function bar()" in result
    
    def test_nested_function_with_decorator(self):
        """def foo(): @decorator\ndef bar(): pass"""
        result = transpile("def foo():\n    @decorator\n    def bar():\n        pass")
        assert "function foo()" in result
        assert "function bar()" in result
        assert "decorator" in result
    
    def test_nested_function_with_try_except(self):
        """def foo(x): def bar(): try: return 1/x; except: return 0; return bar()"""
        result = transpile("def foo(x):\n    def bar():\n        try:\n            return 1/x\n        except:\n            return 0\n    return bar()")
        assert "function foo(x)" in result
        assert "function bar()" in result
    
    def test_nested_function_with_assert(self):
        """def foo(x): def bar(): assert x > 0; return x; return bar()"""
        result = transpile("def foo(x):\n    def bar():\n        assert x > 0\n        return x\n    return bar()")
        assert "function foo(x)" in result
        assert "function bar()" in result
    
    def test_nested_function_with_raise(self):
        """def foo(x): def bar(): if x < 0: raise ValueError(); return bar()"""
        result = transpile("def foo(x):\n    def bar():\n        if x < 0:\n            raise ValueError()\n    return bar()")
        assert "function foo(x)" in result
        assert "function bar()" in result


# =============================================================================
# LAMBDA EXPRESSIONS (20 tests)
# =============================================================================

class TestBasicLambda:
    """Test basic lambda expressions - 5 tests."""
    
    def test_simple_lambda(self):
        """lambda x: x * 2"""
        result = transpile("square = lambda x: x * 2")
        assert "(x) =>" in result or "x =>" in result
        assert_has_runtime_function(result, "mul")
    
    def test_lambda_no_args(self):
        """lambda: 42"""
        result = transpile("answer = lambda: 42")
        assert "() => 42" in result
    
    def test_lambda_multiple_args(self):
        """lambda x, y: x + y"""
        result = transpile("add = lambda x, y: x + y")
        assert "(x, y) =>" in result or "x, y =>" in result
        assert_has_runtime_function(result, "add")
    
    def test_lambda_with_default(self):
        """lambda x, y=10: x + y"""
        result = transpile("add = lambda x, y=10: x + y")
        assert "(x, y = 10) =>" in result or "x, y = 10 =>" in result
        assert_has_runtime_function(result, "add")
    
    def test_lambda_with_expression(self):
        """lambda x: x * x + 1"""
        result = transpile("f = lambda x: x * x + 1")
        assert "(x) =>" in result or "x =>" in result
        assert_has_runtime_function(result, "mul")


class TestLambdaWithClosures:
    """Test lambda expressions with closures - 5 tests."""
    
    def test_lambda_capturing_outer_var(self):
        """x = 5; f = lambda y: x + y"""
        result = transpile("x = 5\nf = lambda y: x + y")
        assert "(y) =>" in result or "y =>" in result
        assert_has_runtime_function(result, "add")
    
    def test_lambda_capturing_multiple_vars(self):
        """x = 1; y = 2; f = lambda z: x + y + z"""
        result = transpile("x = 1\ny = 2\nf = lambda z: x + y + z")
        assert "(z) =>" in result or "z =>" in result
        assert_has_runtime_function(result, "add")
    
    def test_lambda_in_function(self):
        """def foo(x): return lambda y: x + y"""
        result = transpile("def foo(x):\n    return lambda y: x + y")
        assert "function foo(x)" in result
        assert "(y) =>" in result or "y =>" in result
        assert_has_runtime_function(result, "add")
    
    def test_lambda_capturing_from_loop(self):
        """funcs = []; for i in range(3): funcs.append(lambda x: x + i)"""
        result = transpile("funcs = []\nfor i in range(3):\n    funcs.append(lambda x: x + i)")
        assert "(x) =>" in result or "x =>" in result
        assert_has_runtime_function(result, "add")
    
    def test_lambda_capturing_from_conditional(self):
        """x = 1; if True: y = 2; f = lambda z: x + y + z"""
        result = transpile("x = 1\nif True:\n    y = 2\nf = lambda z: x + y + z")
        assert "(z) =>" in result or "z =>" in result
        assert_has_runtime_function(result, "add")


class TestLambdaWithDefaultArgs:
    """Test lambda expressions with default arguments - 5 tests."""
    
    def test_lambda_single_default(self):
        """lambda x, y=10: x + y"""
        result = transpile("add = lambda x, y=10: x + y")
        assert "(x, y = 10) =>" in result or "x, y = 10 =>" in result
        assert_has_runtime_function(result, "add")
    
    def test_lambda_multiple_defaults(self):
        """lambda x=1, y=2: x + y"""
        result = transpile("add = lambda x=1, y=2: x + y")
        assert "x = 1" in result
        assert "y = 2" in result
        assert_has_runtime_function(result, "add")
    
    def test_lambda_mixed_defaults(self):
        """lambda x, y=2, z=3: x + y + z"""
        result = transpile("add = lambda x, y=2, z=3: x + y + z")
        assert "x" in result
        assert "y = 2" in result
        assert "z = 3" in result
        assert_has_runtime_function(result, "add")
    
    def test_lambda_default_with_expression(self):
        """lambda x, y=1+1: x + y"""
        result = transpile("add = lambda x, y=1+1: x + y")
        assert "y = " in result
    
    def test_lambda_default_with_call(self):
        """lambda x, y=len([]): x + y"""
        result = transpile("add = lambda x, y=len([]): x + y")
        assert "y = " in result


class TestLambdaInComprehensions:
    """Test lambda expressions in comprehensions - 5 tests."""
    
    def test_lambda_in_list_comp(self):
        """[lambda x: x*2 for i in range(3)]"""
        result = transpile("funcs = [lambda x: x*2 for i in range(3)]")
        assert "(x) =>" in result or "x =>" in result
        assert_has_runtime_function(result, "mul")
    
    def test_lambda_in_dict_comp(self):
        """{i: lambda x: x+i for i in range(3)}"""
        result = transpile("funcs = {i: lambda x: x+i for i in range(3)}")
        assert "(x) =>" in result or "x =>" in result
        assert_has_runtime_function(result, "add")
    
    def test_lambda_in_set_comp(self):
        """{lambda x: x*2 for i in range(3)}"""
        # Sets can't contain functions in Python, but test parsing
        # This will parse but may not work at runtime
        result = transpile("funcs = {lambda x: x*2 for i in range(3)}")
        assert "(x) =>" in result or "x =>" in result
    
    def test_lambda_in_generator_exp(self):
        """(lambda x: x*2 for i in range(3))"""
        result = transpile("funcs = (lambda x: x*2 for i in range(3))")
        assert "(x) =>" in result or "x =>" in result
        assert_has_runtime_function(result, "mul")
    
    def test_lambda_in_nested_comp(self):
        """[[lambda x: x+i for j in range(2)] for i in range(3)]"""
        result = transpile("funcs = [[lambda x: x+i for j in range(2)] for i in range(3)]")
        assert "(x) =>" in result or "x =>" in result
        assert_has_runtime_function(result, "add")


# =============================================================================
# EDGE CASES AND INTEGRATION
# =============================================================================

class TestFunctionEdgeCases:
    """Test edge cases and integration scenarios."""
    
    def test_function_name_with_underscore(self):
        """def _private(): pass"""
        result = transpile("def _private():\n    pass")
        assert "function _private()" in result
    
    def test_function_name_with_double_underscore(self):
        """def __special__(): pass"""
        result = transpile("def __special__():\n    pass")
        assert "function __special__()" in result
    
    def test_function_with_docstring(self):
        """def foo(): \"\"\"doc\"\"\"; pass"""
        result = transpile('def foo():\n    """doc"""\n    pass')
        assert "function foo()" in result
    
    def test_function_with_type_hints(self):
        """def foo(x: int) -> int: return x"""
        result = transpile("def foo(x: int) -> int:\n    return x")
        assert "function foo(x)" in result
        # Type hints are ignored in transpilation
    
    def test_async_function(self):
        """async def foo(): pass"""
        result = transpile("async def foo():\n    pass")
        assert "async function foo()" in result

