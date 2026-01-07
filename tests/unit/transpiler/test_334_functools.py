"""
Phase 33.4: functools Module Tests

Comprehensive tests for Python functools module transpilation.
Tests verify the runtime provides correct JavaScript implementations for:
- partial (argument binding)
- reduce (fold)
- lru_cache (memoization)
- cache (unbounded memoization)
- wraps (decorator helper)
"""

import pytest


# =============================================================================
# PARTIAL TESTS (8 tests)
# =============================================================================

class TestPartial:
    """Tests for partial()."""
    
    def test_partial_positional(self):
        """partial with positional args."""
        from pynext.runtime.stdlib.functools import partial
        
        def power(base, exp):
            return base ** exp
        
        square = partial(power, exp=2)
        assert square(5) == 25
    
    def test_partial_keyword(self):
        """partial with keyword args."""
        from pynext.runtime.stdlib.functools import partial
        
        def greet(name, greeting="Hello"):
            return f"{greeting}, {name}!"
        
        hi = partial(greet, greeting="Hi")
        assert hi("Alice") == "Hi, Alice!"
    
    def test_partial_multiple_args(self):
        """partial with multiple bound args."""
        from pynext.runtime.stdlib.functools import partial
        
        def add3(a, b, c):
            return a + b + c
        
        add_10_20 = partial(add3, 10, 20)
        assert add_10_20(5) == 35
    
    def test_partial_override(self):
        """partial args can be overridden."""
        from pynext.runtime.stdlib.functools import partial
        
        def power(base, exp):
            return base ** exp
        
        cube = partial(power, exp=3)
        # Override exp
        assert cube(2, exp=4) == 16
    
    def test_partial_func_attribute(self):
        """partial.func holds original function."""
        from pynext.runtime.stdlib.functools import partial
        
        def original():
            pass
        
        p = partial(original)
        assert p.func is original
    
    def test_partial_args_attribute(self):
        """partial.args holds bound positional args."""
        from pynext.runtime.stdlib.functools import partial
        
        def f(a, b, c):
            pass
        
        p = partial(f, 1, 2)
        assert p.args == (1, 2)
    
    def test_partial_keywords_attribute(self):
        """partial.keywords holds bound keyword args."""
        from pynext.runtime.stdlib.functools import partial
        
        def f(a, b=10):
            pass
        
        p = partial(f, b=20)
        assert p.keywords == {"b": 20}
    
    def test_partial_nested(self):
        """Nested partial works."""
        from pynext.runtime.stdlib.functools import partial
        
        def f(a, b, c):
            return a + b + c
        
        p1 = partial(f, 1)
        p2 = partial(p1, 2)
        assert p2(3) == 6


# =============================================================================
# REDUCE TESTS (6 tests)
# =============================================================================

class TestReduce:
    """Tests for reduce()."""
    
    def test_reduce_sum(self):
        """reduce with add function."""
        from pynext.runtime.stdlib.functools import reduce
        result = reduce(lambda a, b: a + b, [1, 2, 3, 4])
        assert result == 10
    
    def test_reduce_product(self):
        """reduce with multiply function."""
        from pynext.runtime.stdlib.functools import reduce
        result = reduce(lambda a, b: a * b, [1, 2, 3, 4])
        assert result == 24
    
    def test_reduce_max(self):
        """reduce to find max."""
        from pynext.runtime.stdlib.functools import reduce
        result = reduce(lambda a, b: a if a > b else b, [3, 1, 4, 1, 5])
        assert result == 5
    
    def test_reduce_initial(self):
        """reduce with initial value."""
        from pynext.runtime.stdlib.functools import reduce
        result = reduce(lambda a, b: a + b, [1, 2, 3], 10)
        assert result == 16
    
    def test_reduce_single_element(self):
        """reduce with single element."""
        from pynext.runtime.stdlib.functools import reduce
        result = reduce(lambda a, b: a + b, [42])
        assert result == 42
    
    def test_reduce_empty_with_initial(self):
        """reduce empty list with initial."""
        from pynext.runtime.stdlib.functools import reduce
        result = reduce(lambda a, b: a + b, [], 100)
        assert result == 100


# =============================================================================
# LRU_CACHE TESTS (6 tests)
# =============================================================================

class TestLruCache:
    """Tests for lru_cache()."""
    
    def test_lru_cache_basic(self):
        """lru_cache caches results."""
        from pynext.runtime.stdlib.functools import lru_cache
        
        call_count = [0]
        
        @lru_cache(maxsize=128)
        def fib(n):
            call_count[0] += 1
            if n < 2:
                return n
            return fib(n - 1) + fib(n - 2)
        
        result = fib(10)
        assert result == 55
        # Without cache, would be much more calls
        assert call_count[0] == 11
    
    def test_lru_cache_maxsize(self):
        """lru_cache respects maxsize."""
        from pynext.runtime.stdlib.functools import lru_cache
        
        @lru_cache(maxsize=2)
        def double(x):
            return x * 2
        
        double(1)
        double(2)
        double(3)  # Evicts 1
        
        info = double.cache_info()
        assert info.currsize <= 2
    
    def test_lru_cache_cache_info(self):
        """lru_cache.cache_info() returns stats."""
        from pynext.runtime.stdlib.functools import lru_cache
        
        @lru_cache(maxsize=128)
        def square(x):
            return x * x
        
        square(2)
        square(3)
        square(2)  # Hit
        
        info = square.cache_info()
        assert info.hits >= 1
        assert info.misses >= 2
    
    def test_lru_cache_cache_clear(self):
        """lru_cache.cache_clear() clears cache."""
        from pynext.runtime.stdlib.functools import lru_cache
        
        @lru_cache(maxsize=128)
        def cube(x):
            return x ** 3
        
        cube(2)
        cube(3)
        cube.cache_clear()
        
        info = cube.cache_info()
        assert info.currsize == 0
    
    def test_lru_cache_none_maxsize(self):
        """lru_cache with maxsize=None is unbounded."""
        from pynext.runtime.stdlib.functools import lru_cache
        
        @lru_cache(maxsize=None)
        def identity(x):
            return x
        
        for i in range(1000):
            identity(i)
        
        info = identity.cache_info()
        assert info.maxsize is None
        assert info.currsize == 1000
    
    def test_lru_cache_typed(self):
        """lru_cache with typed=True distinguishes types."""
        from pynext.runtime.stdlib.functools import lru_cache
        
        @lru_cache(maxsize=128, typed=True)
        def type_sensitive(x):
            return type(x).__name__
        
        type_sensitive(1)
        type_sensitive(1.0)
        
        info = type_sensitive.cache_info()
        # Both should be cached separately
        assert info.misses == 2


# =============================================================================
# CACHE TESTS (2 tests)
# =============================================================================

class TestCache:
    """Tests for cache()."""
    
    def test_cache_basic(self):
        """cache is unbounded lru_cache."""
        from pynext.runtime.stdlib.functools import cache
        
        call_count = [0]
        
        @cache
        def expensive(x, y):
            call_count[0] += 1
            return x ** y
        
        expensive(2, 3)
        expensive(2, 3)  # Cached
        expensive(3, 2)
        
        assert call_count[0] == 2
    
    def test_cache_different_args(self):
        """cache distinguishes different arguments."""
        from pynext.runtime.stdlib.functools import cache
        
        @cache
        def add(a, b):
            return a + b
        
        assert add(1, 2) == 3
        assert add(2, 1) == 3
        assert add(1, 2) == 3  # Same as first call


# =============================================================================
# WRAPS TESTS (3 tests)
# =============================================================================

class TestWraps:
    """Tests for wraps()."""
    
    def test_wraps_name(self):
        """wraps preserves __name__."""
        from pynext.runtime.stdlib.functools import wraps
        
        def my_decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        
        @my_decorator
        def greet():
            """Say hello."""
            return "hello"
        
        assert greet.__name__ == "greet"
    
    def test_wraps_doc(self):
        """wraps preserves __doc__."""
        from pynext.runtime.stdlib.functools import wraps
        
        def my_decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        
        @my_decorator
        def greet():
            """Say hello."""
            return "hello"
        
        assert greet.__doc__ == "Say hello."
    
    def test_wraps_wrapped(self):
        """wraps sets __wrapped__."""
        from pynext.runtime.stdlib.functools import wraps
        
        def my_decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        
        def original():
            pass
        
        decorated = my_decorator(original)
        assert decorated.__wrapped__ is original
