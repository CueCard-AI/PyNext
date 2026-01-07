"""
Phase 33.4: operator Module Tests

Comprehensive tests for Python operator module transpilation.
Tests verify the runtime provides correct JavaScript implementations for:
- itemgetter, attrgetter, methodcaller
- Arithmetic: add, sub, mul, truediv, floordiv, mod, pow, neg, pos, abs
- Comparison: eq, ne, lt, le, gt, ge
- Boolean: and_, or_, not_
"""

import pytest


# =============================================================================
# GETTER TESTS (10 tests)
# =============================================================================

class TestItemgetter:
    """Tests for itemgetter()."""
    
    def test_itemgetter_single(self):
        """itemgetter(key) gets single item."""
        from pynext.runtime.stdlib.operator import itemgetter
        get_name = itemgetter("name")
        result = get_name({"name": "Alice", "age": 30})
        assert result == "Alice"
    
    def test_itemgetter_index(self):
        """itemgetter(index) gets by index."""
        from pynext.runtime.stdlib.operator import itemgetter
        get_first = itemgetter(0)
        assert get_first([1, 2, 3]) == 1
    
    def test_itemgetter_multiple(self):
        """itemgetter(k1, k2) gets tuple."""
        from pynext.runtime.stdlib.operator import itemgetter
        get_name_age = itemgetter("name", "age")
        result = get_name_age({"name": "Alice", "age": 30})
        assert result == ("Alice", 30)
    
    def test_itemgetter_negative_index(self):
        """itemgetter(-1) gets last item."""
        from pynext.runtime.stdlib.operator import itemgetter
        get_last = itemgetter(-1)
        assert get_last([1, 2, 3]) == 3
    
    def test_itemgetter_sort_key(self):
        """itemgetter as sort key."""
        from pynext.runtime.stdlib.operator import itemgetter
        users = [{"name": "Bob", "age": 25}, {"name": "Alice", "age": 30}]
        sorted_users = sorted(users, key=itemgetter("name"))
        assert sorted_users[0]["name"] == "Alice"


class TestAttrgetter:
    """Tests for attrgetter()."""
    
    def test_attrgetter_single(self):
        """attrgetter(attr) gets single attribute."""
        from pynext.runtime.stdlib.operator import attrgetter
        
        class Point:
            def __init__(self, x, y):
                self.x = x
                self.y = y
        
        get_x = attrgetter("x")
        p = Point(10, 20)
        assert get_x(p) == 10
    
    def test_attrgetter_multiple(self):
        """attrgetter(a1, a2) gets tuple."""
        from pynext.runtime.stdlib.operator import attrgetter
        
        class Point:
            def __init__(self, x, y):
                self.x = x
                self.y = y
        
        get_coords = attrgetter("x", "y")
        p = Point(10, 20)
        assert get_coords(p) == (10, 20)
    
    def test_attrgetter_nested(self):
        """attrgetter(a.b) gets nested attribute."""
        from pynext.runtime.stdlib.operator import attrgetter
        
        class Address:
            def __init__(self, city):
                self.city = city
        
        class Person:
            def __init__(self, address):
                self.address = address
        
        get_city = attrgetter("address.city")
        p = Person(Address("NYC"))
        assert get_city(p) == "NYC"


class TestMethodcaller:
    """Tests for methodcaller()."""
    
    def test_methodcaller_no_args(self):
        """methodcaller(method) calls method."""
        from pynext.runtime.stdlib.operator import methodcaller
        upper = methodcaller("upper")
        assert upper("hello") == "HELLO"
    
    def test_methodcaller_with_args(self):
        """methodcaller(method, args) passes args."""
        from pynext.runtime.stdlib.operator import methodcaller
        split_comma = methodcaller("split", ",")
        assert split_comma("a,b,c") == ["a", "b", "c"]


# =============================================================================
# ARITHMETIC OPERATOR TESTS (6 tests)
# =============================================================================

class TestArithmeticOperators:
    """Tests for arithmetic operators."""
    
    def test_add(self):
        """add(a, b) returns a + b."""
        from pynext.runtime.stdlib.operator import add
        assert add(1, 2) == 3
    
    def test_sub(self):
        """sub(a, b) returns a - b."""
        from pynext.runtime.stdlib.operator import sub
        assert sub(5, 3) == 2
    
    def test_mul(self):
        """mul(a, b) returns a * b."""
        from pynext.runtime.stdlib.operator import mul
        assert mul(3, 4) == 12
    
    def test_truediv(self):
        """truediv(a, b) returns a / b."""
        from pynext.runtime.stdlib.operator import truediv
        assert truediv(10, 4) == 2.5
    
    def test_floordiv(self):
        """floordiv(a, b) returns a // b."""
        from pynext.runtime.stdlib.operator import floordiv
        assert floordiv(10, 3) == 3
    
    def test_mod(self):
        """mod(a, b) returns a % b."""
        from pynext.runtime.stdlib.operator import mod
        assert mod(10, 3) == 1


class TestUnaryOperators:
    """Tests for unary operators."""
    
    def test_neg(self):
        """neg(a) returns -a."""
        from pynext.runtime.stdlib.operator import neg
        assert neg(5) == -5
        assert neg(-5) == 5
    
    def test_pos(self):
        """pos(a) returns +a."""
        from pynext.runtime.stdlib.operator import pos
        assert pos(5) == 5
    
    def test_abs(self):
        """abs_(a) returns abs(a)."""
        from pynext.runtime.stdlib.operator import abs_
        assert abs_(-5) == 5
        assert abs_(5) == 5


# =============================================================================
# COMPARISON OPERATOR TESTS (6 tests)
# =============================================================================

class TestComparisonOperators:
    """Tests for comparison operators."""
    
    def test_eq(self):
        """eq(a, b) returns a == b."""
        from pynext.runtime.stdlib.operator import eq
        assert eq(1, 1) is True
        assert eq(1, 2) is False
    
    def test_ne(self):
        """ne(a, b) returns a != b."""
        from pynext.runtime.stdlib.operator import ne
        assert ne(1, 2) is True
        assert ne(1, 1) is False
    
    def test_lt(self):
        """lt(a, b) returns a < b."""
        from pynext.runtime.stdlib.operator import lt
        assert lt(1, 2) is True
        assert lt(2, 1) is False
    
    def test_le(self):
        """le(a, b) returns a <= b."""
        from pynext.runtime.stdlib.operator import le
        assert le(1, 2) is True
        assert le(2, 2) is True
    
    def test_gt(self):
        """gt(a, b) returns a > b."""
        from pynext.runtime.stdlib.operator import gt
        assert gt(2, 1) is True
        assert gt(1, 2) is False
    
    def test_ge(self):
        """ge(a, b) returns a >= b."""
        from pynext.runtime.stdlib.operator import ge
        assert ge(2, 1) is True
        assert ge(2, 2) is True


# =============================================================================
# BOOLEAN OPERATOR TESTS (3 tests)
# =============================================================================

class TestBooleanOperators:
    """Tests for boolean operators."""
    
    def test_and_(self):
        """and_(a, b) returns a and b."""
        from pynext.runtime.stdlib.operator import and_
        assert and_(True, False) is False
        assert and_(True, True) is True
    
    def test_or_(self):
        """or_(a, b) returns a or b."""
        from pynext.runtime.stdlib.operator import or_
        assert or_(True, False) is True
        assert or_(False, False) is False
    
    def test_not_(self):
        """not_(a) returns not a."""
        from pynext.runtime.stdlib.operator import not_
        assert not_(True) is False
        assert not_(False) is True
