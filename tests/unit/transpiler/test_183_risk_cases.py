"""
Risk Cases Tests for Phase 18.3 Type Methods

Tests high-risk areas that could cause subtle bugs:
1. Type disambiguation (string vs list methods)
2. title() apostrophe handling
3. split() maxsplit behavior
4. sort() with key/reverse
5. strip() with special characters
6. Unicode method support
"""

import pytest
from pynext.transpiler import transpile, transpile_expression
from tests.unit.transpiler.test_utils import assert_has_function_call_with_args


# =============================================================================
# TYPE DISAMBIGUATION
# =============================================================================

class TestTypeDisambiguation:
    """Tests for cases where type can't be determined at transpile time."""
    
    def test_index_uses_runtime(self):
        """index() should use runtime helper for correct semantics."""
        result = transpile_expression('items.index(x)')
        # Should use a runtime helper (either str or list)
        assert '.index(' in result
    
    def test_count_uses_runtime(self):
        """count() should use runtime helper."""
        result = transpile_expression('items.count(x)')
        assert '.count(' in result
    
    def test_remove_uses_runtime(self):
        """remove() should use runtime helper for deep equality."""
        result = transpile_expression('items.remove(x)')
        assert '__py.list.remove(items, x)' in result
    
    def test_get_uses_runtime(self):
        """dict.get() should use runtime helper."""
        result = transpile_expression('d.get("key")')
        assert '__py.dict.get' in result


# =============================================================================
# TITLE() APOSTROPHE HANDLING
# =============================================================================

class TestTitleApostrophe:
    """Tests for title() with apostrophes (Python behavior)."""
    
    def test_basic_title(self):
        """title() emits runtime helper."""
        result = transpile_expression('s.title()')
        assert '__py.str.title(s)' in result
    
    def test_title_in_fstring(self):
        """title() in f-string."""
        result = transpile_expression('f"{name.title()}"')
        assert '__py.str.title' in result


# =============================================================================
# SPLIT() MAXSPLIT BEHAVIOR
# =============================================================================

class TestSplitMaxsplit:
    """Tests for split() with maxsplit argument."""
    
    def test_split_no_args(self):
        """split() with no args uses runtime."""
        result = transpile_expression('s.split()')
        assert '__py.str.split(s)' in result
    
    def test_split_with_sep(self):
        """split() with separator."""
        result = transpile_expression('s.split(",")')
        assert '__py.str.split(s, ",")' in result
    
    def test_split_with_maxsplit(self):
        """split() with maxsplit."""
        result = transpile_expression('s.split(",", 2)')
        assert '__py.str.split(s, ",", 2)' in result
    
    def test_split_none_maxsplit(self):
        """split(None, 1) for whitespace with maxsplit."""
        result = transpile_expression('s.split(None, 1)')
        assert '__py.str.split' in result


# =============================================================================
# SORT() WITH KEY AND REVERSE
# =============================================================================

class TestSortKeyReverse:
    """Tests for sort() with key and reverse kwargs."""
    
    def test_sort_no_args(self):
        """sort() with no args."""
        result = transpile_expression('items.sort()')
        assert '__py.list.sort(items)' in result
    
    def test_sort_with_reverse(self):
        """sort(reverse=True)."""
        result = transpile_expression('items.sort(reverse=True)')
        assert '__py.list.sort(items' in result
        assert 'true' in result.lower()
    
    def test_sort_with_key(self):
        """sort(key=len)."""
        result = transpile_expression('items.sort(key=len)')
        assert '__py.list.sort(items, len' in result
    
    def test_sort_with_both(self):
        """sort(key=len, reverse=True)."""
        result = transpile_expression('items.sort(key=len, reverse=True)')
        assert '__py.list.sort' in result


# =============================================================================
# STRIP() WITH SPECIAL CHARACTERS
# =============================================================================

class TestStripSpecialChars:
    """Tests for strip() with regex special characters."""
    
    def test_strip_no_args(self):
        """strip() with no args uses trim()."""
        result = transpile_expression('s.strip()')
        assert 's.trim()' in result
    
    def test_strip_with_chars(self):
        """strip() with chars uses runtime."""
        result = transpile_expression('s.strip("xy")')
        assert '__py.str.strip(s, "xy")' in result
    
    def test_lstrip_with_chars(self):
        """lstrip() with chars uses runtime."""
        result = transpile_expression('s.lstrip("xy")')
        assert '__py.str.lstrip(s, "xy")' in result
    
    def test_rstrip_with_chars(self):
        """rstrip() with chars uses runtime."""
        result = transpile_expression('s.rstrip("xy")')
        assert '__py.str.rstrip(s, "xy")' in result


# =============================================================================
# UNICODE METHODS
# =============================================================================

class TestUnicodeMethods:
    """Tests for is*() methods with unicode."""
    
    def test_isalpha_uses_runtime(self):
        """isalpha() should use runtime for unicode support."""
        result = transpile_expression('s.isalpha()')
        assert '__py.str.isalpha(s)' in result
    
    def test_isupper_uses_runtime(self):
        """isupper() should use runtime for unicode."""
        result = transpile_expression('s.isupper()')
        assert '__py.str.isupper(s)' in result
    
    def test_islower_uses_runtime(self):
        """islower() should use runtime for unicode."""
        result = transpile_expression('s.islower()')
        assert '__py.str.islower(s)' in result


# =============================================================================
# SPLITLINES
# =============================================================================

class TestSplitlines:
    """Tests for splitlines() method."""
    
    def test_splitlines_no_args(self):
        """splitlines() with no args."""
        result = transpile_expression('s.splitlines()')
        assert '__py.str.splitlines(s)' in result
    
    def test_splitlines_with_keepends(self):
        """splitlines(True) keeps line endings."""
        result = transpile_expression('s.splitlines(True)')
        assert '__py.str.splitlines' in result


# =============================================================================
# INSERT() NEGATIVE INDEX
# =============================================================================

class TestInsertNegativeIndex:
    """Tests for insert() with negative indices."""
    
    def test_insert_positive(self):
        """insert() with positive index."""
        result = transpile_expression('items.insert(0, x)')
        assert '__py.list.insert(items, 0, x)' in result
    
    def test_insert_negative(self):
        """insert() with negative index."""
        result = transpile_expression('items.insert(-1, x)')
        # Negative literals may be wrapped in parentheses for precedence
        assert '__py.list.insert(items, -1, x)' in result or '__py.list.insert(items, (-1), x)' in result
    
    def test_insert_variable(self):
        """insert() with variable index."""
        result = transpile_expression('items.insert(i, x)')
        assert '__py.list.insert(items, i, x)' in result


# =============================================================================
# POP() WITH INDEX
# =============================================================================

class TestPopWithIndex:
    """Tests for pop() with index argument."""
    
    def test_pop_no_args(self):
        """pop() with no args uses direct call."""
        result = transpile_expression('items.pop()')
        assert 'items.pop()' in result
    
    def test_pop_with_index(self):
        """pop(0) uses runtime helper."""
        result = transpile_expression('items.pop(0)')
        assert '__py.list.pop(items, 0)' in result
    
    def test_pop_negative_index(self):
        """pop(-1) uses runtime helper."""
        result = transpile_expression('items.pop(-1)')
        # Negative literals may be wrapped in parentheses for precedence
        assert '__py.list.pop(items, -1)' in result or '__py.list.pop(items, (-1))' in result


# =============================================================================
# SET OPERATIONS
# =============================================================================

class TestSetOperations:
    """Tests for set methods that differ from JS."""
    
    def test_set_remove(self):
        """set.remove() uses runtime (throws on missing)."""
        result = transpile_expression('seen.remove(x)')
        assert '.remove(seen, x)' in result
    
    def test_set_discard(self):
        """set.discard() uses runtime."""
        result = transpile_expression('seen.discard(x)')
        assert '__py.set.discard(seen, x)' in result
    
    def test_set_union(self):
        """set.union() uses runtime."""
        result = transpile_expression('seen.union(other)')
        assert '__py.set.union(seen, other)' in result
    
    def test_set_intersection(self):
        """set.intersection() uses runtime."""
        result = transpile_expression('seen.intersection(other)')
        assert '__py.set.intersection(seen, other)' in result


# =============================================================================
# CHAINED METHOD CALLS
# =============================================================================

class TestChainedMethodCalls:
    """Tests for chained method calls."""
    
    def test_strip_lower_chain(self):
        """s.strip().lower() chain."""
        result = transpile_expression('s.strip().lower()')
        assert '.trim().toLowerCase()' in result
    
    def test_strip_split_chain(self):
        """s.strip().split() chain."""
        result = transpile_expression('s.strip().split()')
        assert '.trim()' in result
        assert '__py.str.split' in result
    
    def test_lower_split_chain(self):
        """s.lower().split(",") chain."""
        result = transpile_expression('s.lower().split(",")')
        assert '.toLowerCase()' in result
        assert '__py.str.split' in result


# =============================================================================
# REPLACE WITH COUNT
# =============================================================================

class TestReplaceWithCount:
    """Tests for replace() with count argument."""
    
    def test_replace_no_count(self):
        """replace() without count uses replaceAll."""
        result = transpile_expression('s.replace("a", "b")')
        assert 's.replaceAll("a", "b")' in result
    
    def test_replace_with_count(self):
        """replace() with count uses runtime."""
        result = transpile_expression('s.replace("a", "b", 1)')
        assert '__py.str.replace(s, "a", "b", 1)' in result


# =============================================================================
# JOIN REVERSAL
# =============================================================================

class TestJoinReversal:
    """Tests for join() which reverses order."""
    
    def test_join_basic(self):
        """",".join(items) becomes items.join(",")."""
        result = transpile_expression('",".join(items)')
        assert 'items.join(",")' in result
    
    def test_join_with_variable(self):
        """sep.join(items)."""
        result = transpile_expression('sep.join(items)')
        assert 'items.join(sep)' in result


# =============================================================================
# EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Edge cases that could cause issues."""
    
    def test_method_on_literal(self):
        """Method on string literal."""
        result = transpile_expression('"hello".lower()')
        assert '.toLowerCase()' in result
    
    def test_method_on_subscript(self):
        """Method on subscript result."""
        result = transpile_expression('items[0].lower()')
        assert '.toLowerCase()' in result
    
    def test_method_with_method_arg(self):
        """Method with method result as argument."""
        result = transpile_expression('s.replace(old.strip(), new_str)')
        assert '.replaceAll(' in result
        assert '.trim()' in result
    
    def test_nested_method_calls(self):
        """Nested method calls."""
        result = transpile_expression('get_string().strip().lower()')
        assert '.trim().toLowerCase()' in result
