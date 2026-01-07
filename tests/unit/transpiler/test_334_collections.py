"""
Phase 33.4: collections Module Tests

Comprehensive tests for Python collections module transpilation.
Tests verify the runtime provides correct JavaScript implementations for:
- Counter (counting, most_common, arithmetic)
- defaultdict (default factories)
- deque (append, pop, rotate, maxlen)
- OrderedDict (move_to_end, popitem)
- namedtuple (creation, _asdict, _replace)
"""

import pytest


# =============================================================================
# COUNTER TESTS (10 tests)
# =============================================================================

class TestCounterBasic:
    """Basic Counter tests."""
    
    def test_counter_from_list(self):
        """Counter from list counts items."""
        from pynext.runtime.stdlib.collections import Counter
        c = Counter(["a", "b", "a", "c", "a", "b"])
        assert c["a"] == 3
        assert c["b"] == 2
        assert c["c"] == 1
    
    def test_counter_from_string(self):
        """Counter from string counts characters."""
        from pynext.runtime.stdlib.collections import Counter
        c = Counter("abracadabra")
        assert c["a"] == 5
        assert c["b"] == 2
        assert c["r"] == 2
    
    def test_counter_from_dict(self):
        """Counter from dict."""
        from pynext.runtime.stdlib.collections import Counter
        c = Counter({"a": 3, "b": 2})
        assert c["a"] == 3
        assert c["b"] == 2
    
    def test_counter_missing_key(self):
        """Counter returns 0 for missing keys."""
        from pynext.runtime.stdlib.collections import Counter
        c = Counter(["a", "b"])
        assert c["z"] == 0


class TestCounterMethods:
    """Counter method tests."""
    
    def test_counter_most_common(self):
        """Counter.most_common returns sorted list."""
        from pynext.runtime.stdlib.collections import Counter
        c = Counter(["a", "b", "a", "c", "a", "b"])
        most = c.most_common(2)
        assert most[0] == ("a", 3)
        assert most[1] == ("b", 2)
    
    def test_counter_update(self):
        """Counter.update adds counts."""
        from pynext.runtime.stdlib.collections import Counter
        c = Counter(["a", "b"])
        c.update(["a", "d"])
        assert c["a"] == 2
        assert c["d"] == 1
    
    def test_counter_total(self):
        """Counter.total returns sum of counts."""
        from pynext.runtime.stdlib.collections import Counter
        c = Counter(["a", "b", "a", "c", "a", "b"])
        assert c.total() == 6


class TestCounterArithmetic:
    """Counter arithmetic tests."""
    
    def test_counter_add(self):
        """Counter + Counter adds counts."""
        from pynext.runtime.stdlib.collections import Counter
        c1 = Counter({"a": 3, "b": 2})
        c2 = Counter({"a": 1, "b": 3})
        result = c1 + c2
        assert result["a"] == 4
        assert result["b"] == 5
    
    def test_counter_subtract(self):
        """Counter - Counter subtracts counts."""
        from pynext.runtime.stdlib.collections import Counter
        c1 = Counter({"a": 3, "b": 2})
        c2 = Counter({"a": 1, "b": 3})
        result = c1 - c2
        assert result["a"] == 2
    
    def test_counter_intersection(self):
        """Counter & Counter is intersection."""
        from pynext.runtime.stdlib.collections import Counter
        c1 = Counter({"a": 3, "b": 2})
        c2 = Counter({"a": 1, "b": 3})
        result = c1 & c2
        assert result["a"] == 1
        assert result["b"] == 2


# =============================================================================
# DEFAULTDICT TESTS (8 tests)
# =============================================================================

class TestDefaultdict:
    """Tests for defaultdict."""
    
    def test_defaultdict_list(self):
        """defaultdict(list) creates empty list for missing keys."""
        from pynext.runtime.stdlib.collections import defaultdict
        dd = defaultdict(list)
        dd["key"].append(1)
        dd["key"].append(2)
        assert dd["key"] == [1, 2]
    
    def test_defaultdict_int(self):
        """defaultdict(int) creates 0 for missing keys."""
        from pynext.runtime.stdlib.collections import defaultdict
        dd = defaultdict(int)
        dd["count"] += 1
        assert dd["count"] == 1
    
    def test_defaultdict_set(self):
        """defaultdict(set) creates empty set for missing keys."""
        from pynext.runtime.stdlib.collections import defaultdict
        dd = defaultdict(set)
        dd["items"].add("a")
        dd["items"].add("b")
        assert "a" in dd["items"]
        assert "b" in dd["items"]
    
    def test_defaultdict_lambda(self):
        """defaultdict with lambda factory."""
        from pynext.runtime.stdlib.collections import defaultdict
        dd = defaultdict(lambda: "default")
        assert dd["missing"] == "default"
    
    def test_defaultdict_no_factory(self):
        """defaultdict without factory raises KeyError."""
        from pynext.runtime.stdlib.collections import defaultdict
        dd = defaultdict()
        with pytest.raises(KeyError):
            _ = dd["missing"]
    
    def test_defaultdict_get_existing(self):
        """defaultdict returns existing values."""
        from pynext.runtime.stdlib.collections import defaultdict
        dd = defaultdict(int)
        dd["x"] = 42
        assert dd["x"] == 42
    
    def test_defaultdict_keys_values(self):
        """defaultdict supports keys/values."""
        from pynext.runtime.stdlib.collections import defaultdict
        dd = defaultdict(int)
        dd["a"] = 1
        dd["b"] = 2
        assert set(dd.keys()) == {"a", "b"}
        assert set(dd.values()) == {1, 2}
    
    def test_defaultdict_items(self):
        """defaultdict supports items."""
        from pynext.runtime.stdlib.collections import defaultdict
        dd = defaultdict(int)
        dd["a"] = 1
        items = list(dd.items())
        assert ("a", 1) in items


# =============================================================================
# DEQUE TESTS (10 tests)
# =============================================================================

class TestDeque:
    """Tests for deque."""
    
    def test_deque_append(self):
        """deque.append adds to right."""
        from pynext.runtime.stdlib.collections import deque
        dq = deque([1, 2, 3])
        dq.append(4)
        assert list(dq) == [1, 2, 3, 4]
    
    def test_deque_appendleft(self):
        """deque.appendleft adds to left."""
        from pynext.runtime.stdlib.collections import deque
        dq = deque([1, 2, 3])
        dq.appendleft(0)
        assert list(dq) == [0, 1, 2, 3]
    
    def test_deque_pop(self):
        """deque.pop removes from right."""
        from pynext.runtime.stdlib.collections import deque
        dq = deque([1, 2, 3])
        val = dq.pop()
        assert val == 3
        assert list(dq) == [1, 2]
    
    def test_deque_popleft(self):
        """deque.popleft removes from left."""
        from pynext.runtime.stdlib.collections import deque
        dq = deque([1, 2, 3])
        val = dq.popleft()
        assert val == 1
        assert list(dq) == [2, 3]
    
    def test_deque_extend(self):
        """deque.extend adds multiple to right."""
        from pynext.runtime.stdlib.collections import deque
        dq = deque([1, 2])
        dq.extend([3, 4])
        assert list(dq) == [1, 2, 3, 4]
    
    def test_deque_rotate_right(self):
        """deque.rotate(n) rotates right."""
        from pynext.runtime.stdlib.collections import deque
        dq = deque([1, 2, 3, 4, 5])
        dq.rotate(2)
        assert list(dq) == [4, 5, 1, 2, 3]
    
    def test_deque_rotate_left(self):
        """deque.rotate(-n) rotates left."""
        from pynext.runtime.stdlib.collections import deque
        dq = deque([1, 2, 3, 4, 5])
        dq.rotate(-2)
        assert list(dq) == [3, 4, 5, 1, 2]
    
    def test_deque_maxlen(self):
        """deque with maxlen discards old items."""
        from pynext.runtime.stdlib.collections import deque
        dq = deque(maxlen=3)
        dq.extend([1, 2, 3, 4, 5])
        assert list(dq) == [3, 4, 5]
    
    def test_deque_len(self):
        """len(deque) returns length."""
        from pynext.runtime.stdlib.collections import deque
        dq = deque([1, 2, 3])
        assert len(dq) == 3
    
    def test_deque_clear(self):
        """deque.clear removes all items."""
        from pynext.runtime.stdlib.collections import deque
        dq = deque([1, 2, 3])
        dq.clear()
        assert len(dq) == 0


# =============================================================================
# ORDEREDDICT TESTS (4 tests)
# =============================================================================

class TestOrderedDict:
    """Tests for OrderedDict."""
    
    def test_ordereddict_order(self):
        """OrderedDict maintains insertion order."""
        from pynext.runtime.stdlib.collections import OrderedDict
        od = OrderedDict()
        od["first"] = 1
        od["second"] = 2
        od["third"] = 3
        assert list(od.keys()) == ["first", "second", "third"]
    
    def test_ordereddict_move_to_end(self):
        """OrderedDict.move_to_end moves item."""
        from pynext.runtime.stdlib.collections import OrderedDict
        od = OrderedDict([("a", 1), ("b", 2), ("c", 3)])
        od.move_to_end("a")
        assert list(od.keys()) == ["b", "c", "a"]
    
    def test_ordereddict_move_to_beginning(self):
        """OrderedDict.move_to_end(last=False) moves to beginning."""
        from pynext.runtime.stdlib.collections import OrderedDict
        od = OrderedDict([("a", 1), ("b", 2), ("c", 3)])
        od.move_to_end("c", last=False)
        assert list(od.keys()) == ["c", "a", "b"]
    
    def test_ordereddict_popitem(self):
        """OrderedDict.popitem removes last item."""
        from pynext.runtime.stdlib.collections import OrderedDict
        od = OrderedDict([("a", 1), ("b", 2)])
        key, val = od.popitem()
        assert key == "b"
        assert val == 2


# =============================================================================
# NAMEDTUPLE TESTS (5 tests)
# =============================================================================

class TestNamedtuple:
    """Tests for namedtuple."""
    
    def test_namedtuple_basic(self):
        """namedtuple creates class with named fields."""
        from pynext.runtime.stdlib.collections import namedtuple
        Point = namedtuple("Point", ["x", "y"])
        p = Point(10, 20)
        assert p.x == 10
        assert p.y == 20
    
    def test_namedtuple_index_access(self):
        """namedtuple supports index access."""
        from pynext.runtime.stdlib.collections import namedtuple
        Point = namedtuple("Point", ["x", "y"])
        p = Point(10, 20)
        assert p[0] == 10
        assert p[1] == 20
    
    def test_namedtuple_unpacking(self):
        """namedtuple supports unpacking."""
        from pynext.runtime.stdlib.collections import namedtuple
        Point = namedtuple("Point", ["x", "y"])
        p = Point(10, 20)
        x, y = p
        assert x == 10
        assert y == 20
    
    def test_namedtuple_asdict(self):
        """namedtuple._asdict returns dict."""
        from pynext.runtime.stdlib.collections import namedtuple
        Point = namedtuple("Point", ["x", "y"])
        p = Point(10, 20)
        d = p._asdict()
        assert d == {"x": 10, "y": 20}
    
    def test_namedtuple_replace(self):
        """namedtuple._replace creates new instance."""
        from pynext.runtime.stdlib.collections import namedtuple
        Point = namedtuple("Point", ["x", "y"])
        p = Point(10, 20)
        p2 = p._replace(x=100)
        assert p2.x == 100
        assert p2.y == 20
        assert p.x == 10  # Original unchanged
