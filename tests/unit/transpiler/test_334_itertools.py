"""
Phase 33.4: itertools Module Tests

Comprehensive tests for Python itertools module transpilation.
Tests verify the runtime provides correct JavaScript implementations for:
- Infinite: count, cycle, repeat
- Chain: chain, chain.from_iterable
- Slicing: islice
- Filtering: takewhile, dropwhile, filterfalse
- Grouping: groupby
- Accumulation: accumulate
- Combinatorics: product, permutations, combinations, combinations_with_replacement
- zip_longest, starmap, tee, pairwise
"""

import pytest


# =============================================================================
# INFINITE ITERATORS (8 tests)
# =============================================================================

class TestCount:
    """Tests for count()."""
    
    def test_count_default(self):
        """count() starts at 0."""
        from pynext.runtime.stdlib.itertools import count
        c = count()
        assert next(c) == 0
        assert next(c) == 1
        assert next(c) == 2
    
    def test_count_start(self):
        """count(start) starts at start."""
        from pynext.runtime.stdlib.itertools import count
        c = count(10)
        assert next(c) == 10
        assert next(c) == 11
    
    def test_count_step(self):
        """count(start, step) increments by step."""
        from pynext.runtime.stdlib.itertools import count
        c = count(10, 2)
        assert next(c) == 10
        assert next(c) == 12
        assert next(c) == 14


class TestCycle:
    """Tests for cycle()."""
    
    def test_cycle_list(self):
        """cycle repeats list infinitely."""
        from pynext.runtime.stdlib.itertools import cycle
        c = cycle([1, 2, 3])
        assert next(c) == 1
        assert next(c) == 2
        assert next(c) == 3
        assert next(c) == 1  # Repeats
    
    def test_cycle_string(self):
        """cycle repeats string characters."""
        from pynext.runtime.stdlib.itertools import cycle
        c = cycle("ab")
        assert next(c) == "a"
        assert next(c) == "b"
        assert next(c) == "a"


class TestRepeat:
    """Tests for repeat()."""
    
    def test_repeat_infinite(self):
        """repeat(x) repeats infinitely."""
        from pynext.runtime.stdlib.itertools import repeat
        r = repeat("hello")
        assert next(r) == "hello"
        assert next(r) == "hello"
        assert next(r) == "hello"
    
    def test_repeat_limited(self):
        """repeat(x, n) repeats n times."""
        from pynext.runtime.stdlib.itertools import repeat
        r = repeat("hello", 3)
        assert list(r) == ["hello", "hello", "hello"]
    
    def test_repeat_zero(self):
        """repeat(x, 0) is empty."""
        from pynext.runtime.stdlib.itertools import repeat
        r = repeat("hello", 0)
        assert list(r) == []


# =============================================================================
# CHAIN TESTS (4 tests)
# =============================================================================

class TestChain:
    """Tests for chain()."""
    
    def test_chain_lists(self):
        """chain chains lists."""
        from pynext.runtime.stdlib.itertools import chain
        result = list(chain([1, 2], [3, 4], [5, 6]))
        assert result == [1, 2, 3, 4, 5, 6]
    
    def test_chain_empty(self):
        """chain handles empty iterables."""
        from pynext.runtime.stdlib.itertools import chain
        result = list(chain([1, 2], [], [3]))
        assert result == [1, 2, 3]
    
    def test_chain_strings(self):
        """chain chains strings (character by character)."""
        from pynext.runtime.stdlib.itertools import chain
        result = list(chain("ab", "cd"))
        assert result == ["a", "b", "c", "d"]
    
    def test_chain_from_iterable(self):
        """chain.from_iterable flattens iterable of iterables."""
        from pynext.runtime.stdlib.itertools import chain
        result = list(chain.from_iterable([[1, 2], [3, 4]]))
        assert result == [1, 2, 3, 4]


# =============================================================================
# ISLICE TESTS (5 tests)
# =============================================================================

class TestIslice:
    """Tests for islice()."""
    
    def test_islice_stop(self):
        """islice(it, stop) takes first n."""
        from pynext.runtime.stdlib.itertools import islice, count
        result = list(islice(count(), 5))
        assert result == [0, 1, 2, 3, 4]
    
    def test_islice_start_stop(self):
        """islice(it, start, stop) slices range."""
        from pynext.runtime.stdlib.itertools import islice, count
        result = list(islice(count(), 2, 5))
        assert result == [2, 3, 4]
    
    def test_islice_step(self):
        """islice(it, start, stop, step) with step."""
        from pynext.runtime.stdlib.itertools import islice, count
        result = list(islice(count(), 0, 10, 2))
        assert result == [0, 2, 4, 6, 8]
    
    def test_islice_list(self):
        """islice works with lists."""
        from pynext.runtime.stdlib.itertools import islice
        result = list(islice([1, 2, 3, 4, 5], 2, 4))
        assert result == [3, 4]
    
    def test_islice_none_stop(self):
        """islice with None stop."""
        from pynext.runtime.stdlib.itertools import islice
        result = list(islice([1, 2, 3, 4, 5], 2, None))
        assert result == [3, 4, 5]


# =============================================================================
# FILTERING TESTS (6 tests)
# =============================================================================

class TestTakewhile:
    """Tests for takewhile()."""
    
    def test_takewhile_basic(self):
        """takewhile takes while predicate true."""
        from pynext.runtime.stdlib.itertools import takewhile
        result = list(takewhile(lambda x: x < 5, [1, 3, 5, 2, 4]))
        assert result == [1, 3]
    
    def test_takewhile_all_true(self):
        """takewhile with all true."""
        from pynext.runtime.stdlib.itertools import takewhile
        result = list(takewhile(lambda x: x < 10, [1, 2, 3]))
        assert result == [1, 2, 3]


class TestDropwhile:
    """Tests for dropwhile()."""
    
    def test_dropwhile_basic(self):
        """dropwhile drops while predicate true."""
        from pynext.runtime.stdlib.itertools import dropwhile
        result = list(dropwhile(lambda x: x < 5, [1, 3, 5, 2, 4]))
        assert result == [5, 2, 4]
    
    def test_dropwhile_none_true(self):
        """dropwhile with none true."""
        from pynext.runtime.stdlib.itertools import dropwhile
        result = list(dropwhile(lambda x: x > 10, [1, 2, 3]))
        assert result == [1, 2, 3]


class TestFilterfalse:
    """Tests for filterfalse()."""
    
    def test_filterfalse_basic(self):
        """filterfalse filters where predicate false."""
        from pynext.runtime.stdlib.itertools import filterfalse
        result = list(filterfalse(lambda x: x % 2, range(10)))
        assert result == [0, 2, 4, 6, 8]
    
    def test_filterfalse_all_false(self):
        """filterfalse with all false predicate."""
        from pynext.runtime.stdlib.itertools import filterfalse
        result = list(filterfalse(lambda x: False, [1, 2, 3]))
        assert result == [1, 2, 3]


# =============================================================================
# GROUPBY TESTS (4 tests)
# =============================================================================

class TestGroupby:
    """Tests for groupby()."""
    
    def test_groupby_basic(self):
        """groupby groups consecutive equal items."""
        from pynext.runtime.stdlib.itertools import groupby
        data = [1, 1, 2, 2, 2, 3, 1]
        result = [(k, list(g)) for k, g in groupby(data)]
        assert result == [(1, [1, 1]), (2, [2, 2, 2]), (3, [3]), (1, [1])]
    
    def test_groupby_key_function(self):
        """groupby with key function."""
        from pynext.runtime.stdlib.itertools import groupby
        data = ["a", "ab", "abc", "b", "bc"]
        result = [(k, list(g)) for k, g in groupby(data, key=lambda x: x[0])]
        assert result == [("a", ["a", "ab", "abc"]), ("b", ["b", "bc"])]
    
    def test_groupby_sorted(self):
        """groupby with sorted data."""
        from pynext.runtime.stdlib.itertools import groupby
        data = sorted([3, 1, 2, 1, 3, 2])
        result = [(k, list(g)) for k, g in groupby(data)]
        assert result == [(1, [1, 1]), (2, [2, 2]), (3, [3, 3])]
    
    def test_groupby_empty(self):
        """groupby handles empty iterable."""
        from pynext.runtime.stdlib.itertools import groupby
        result = list(groupby([]))
        assert result == []


# =============================================================================
# ACCUMULATE TESTS (3 tests)
# =============================================================================

class TestAccumulate:
    """Tests for accumulate()."""
    
    def test_accumulate_default(self):
        """accumulate default is running sum."""
        from pynext.runtime.stdlib.itertools import accumulate
        result = list(accumulate([1, 2, 3, 4]))
        assert result == [1, 3, 6, 10]
    
    def test_accumulate_multiply(self):
        """accumulate with multiply function."""
        from pynext.runtime.stdlib.itertools import accumulate
        result = list(accumulate([1, 2, 3, 4], lambda a, b: a * b))
        assert result == [1, 2, 6, 24]
    
    def test_accumulate_initial(self):
        """accumulate with initial value."""
        from pynext.runtime.stdlib.itertools import accumulate
        result = list(accumulate([1, 2, 3], initial=10))
        assert result == [10, 11, 13, 16]


# =============================================================================
# COMBINATORICS TESTS (10 tests)
# =============================================================================

class TestProduct:
    """Tests for product()."""
    
    def test_product_two_lists(self):
        """product of two lists."""
        from pynext.runtime.stdlib.itertools import product
        result = list(product([1, 2], ["a", "b"]))
        assert result == [(1, "a"), (1, "b"), (2, "a"), (2, "b")]
    
    def test_product_repeat(self):
        """product with repeat."""
        from pynext.runtime.stdlib.itertools import product
        result = list(product([1, 2], repeat=2))
        assert result == [(1, 1), (1, 2), (2, 1), (2, 2)]
    
    def test_product_empty(self):
        """product with empty iterable."""
        from pynext.runtime.stdlib.itertools import product
        result = list(product([1, 2], []))
        assert result == []


class TestPermutations:
    """Tests for permutations()."""
    
    def test_permutations_all(self):
        """permutations of all elements."""
        from pynext.runtime.stdlib.itertools import permutations
        result = list(permutations([1, 2, 3]))
        assert len(result) == 6
        assert (1, 2, 3) in result
        assert (3, 2, 1) in result
    
    def test_permutations_r(self):
        """permutations of r elements."""
        from pynext.runtime.stdlib.itertools import permutations
        result = list(permutations([1, 2, 3], 2))
        assert len(result) == 6
        assert (1, 2) in result
        assert (2, 1) in result


class TestCombinations:
    """Tests for combinations()."""
    
    def test_combinations_basic(self):
        """combinations of r elements."""
        from pynext.runtime.stdlib.itertools import combinations
        result = list(combinations([1, 2, 3], 2))
        assert result == [(1, 2), (1, 3), (2, 3)]
    
    def test_combinations_all(self):
        """combinations of all elements."""
        from pynext.runtime.stdlib.itertools import combinations
        result = list(combinations([1, 2, 3], 3))
        assert result == [(1, 2, 3)]


class TestCombinationsWithReplacement:
    """Tests for combinations_with_replacement()."""
    
    def test_combinations_with_replacement(self):
        """combinations_with_replacement allows repeats."""
        from pynext.runtime.stdlib.itertools import combinations_with_replacement
        result = list(combinations_with_replacement([1, 2], 2))
        assert result == [(1, 1), (1, 2), (2, 2)]


# =============================================================================
# OTHER TESTS (5 tests)
# =============================================================================

class TestZipLongest:
    """Tests for zip_longest()."""
    
    def test_zip_longest_basic(self):
        """zip_longest fills with None."""
        from pynext.runtime.stdlib.itertools import zip_longest
        result = list(zip_longest([1, 2], [1, 2, 3, 4]))
        assert result == [(1, 1), (2, 2), (None, 3), (None, 4)]
    
    def test_zip_longest_fillvalue(self):
        """zip_longest with fillvalue."""
        from pynext.runtime.stdlib.itertools import zip_longest
        result = list(zip_longest([1, 2], [1, 2, 3, 4], fillvalue=0))
        assert result == [(1, 1), (2, 2), (0, 3), (0, 4)]


class TestStarmap:
    """Tests for starmap()."""
    
    def test_starmap_pow(self):
        """starmap unpacks arguments."""
        from pynext.runtime.stdlib.itertools import starmap
        result = list(starmap(pow, [(2, 3), (3, 2), (10, 2)]))
        assert result == [8, 9, 100]


class TestTee:
    """Tests for tee()."""
    
    def test_tee_basic(self):
        """tee creates independent iterators."""
        from pynext.runtime.stdlib.itertools import tee
        a, b = tee(iter([1, 2, 3]))
        assert list(a) == [1, 2, 3]
        assert list(b) == [1, 2, 3]


class TestPairwise:
    """Tests for pairwise()."""
    
    def test_pairwise_basic(self):
        """pairwise returns adjacent pairs."""
        from pynext.runtime.stdlib.itertools import pairwise
        result = list(pairwise([1, 2, 3, 4]))
        assert result == [(1, 2), (2, 3), (3, 4)]
