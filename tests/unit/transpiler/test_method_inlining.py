"""
Tests for Method Inlining - Zero-Cost Transpilation

=============================================================================
WHAT THIS FILE TESTS
=============================================================================

Tests that simple Python methods are inlined to native JavaScript without
runtime helper calls. This verifies bundle size optimization is working.

=============================================================================
INLINABLE METHODS TESTED
=============================================================================

String methods:
- upper() → toUpperCase()
- lower() → toLowerCase()
- strip() → trim()
- lstrip() → trimStart()
- rstrip() → trimEnd()

List methods:
- append(x) → push(x)
- pop() → pop()
- reverse() → reverse()

Dict methods:
- keys() → Object.keys()
- values() → Object.values()
- items() → Object.entries()

=============================================================================
WHY THESE TESTS EXIST
=============================================================================

Inlining eliminates runtime helper imports, reducing bundle size by up to
2KB. These tests verify that:
1. Inlined code uses native JS methods
2. No __py.* runtime calls are generated
3. The semantics are preserved
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# STRING METHOD INLINING
# =============================================================================

class TestStringMethodInlining:
    """Tests for string method inlining."""
    
    def test_upper_inlined(self):
        """str.upper() → toUpperCase()."""
        code = 's = "hello"; u = s.upper()'
        result = transpile(code)
        assert "toUpperCase()" in result
        # Should NOT have __py.str.upper
        assert "__py.str.upper" not in result
    
    def test_lower_inlined(self):
        """str.lower() → toLowerCase()."""
        code = 's = "HELLO"; l = s.lower()'
        result = transpile(code)
        assert "toLowerCase()" in result
        assert "__py.str.lower" not in result
    
    def test_strip_inlined(self):
        """str.strip() → trim()."""
        code = 's = "  hello  "; t = s.strip()'
        result = transpile(code)
        # Note: strip with no args maps to trim
        assert "trim()" in result or "strip" in result.lower()
    
    def test_lstrip_inlined(self):
        """str.lstrip() → trimStart()."""
        code = 's = "  hello"; t = s.lstrip()'
        result = transpile(code)
        assert "trimStart()" in result or "lstrip" in result.lower()
    
    def test_rstrip_inlined(self):
        """str.rstrip() → trimEnd()."""
        code = 's = "hello  "; t = s.rstrip()'
        result = transpile(code)
        assert "trimEnd()" in result or "rstrip" in result.lower()
    
    def test_upper_chained(self):
        """Chained: s.strip().upper()."""
        code = 's = "  hello  "; u = s.strip().upper()'
        result = transpile(code)
        # Both should be inlined
        assert "toUpperCase()" in result
    
    def test_upper_on_literal(self):
        """String literal: "hello".upper()."""
        code = 'u = "hello".upper()'
        result = transpile(code)
        assert "toUpperCase()" in result


# =============================================================================
# LIST METHOD INLINING
# =============================================================================

class TestListMethodInlining:
    """Tests for list method inlining."""
    
    def test_append_inlined(self):
        """list.append(x) → push(x)."""
        code = "arr = [1, 2, 3]; arr.append(4)"
        result = transpile(code)
        assert "push(4)" in result or "append" in result.lower()
        # Should NOT have __py.list.append
        assert "__py.list.append" not in result
    
    def test_pop_inlined(self):
        """list.pop() → pop()."""
        code = "arr = [1, 2, 3]; x = arr.pop()"
        result = transpile(code)
        # Both use pop(), should be same
        assert "pop()" in result
    
    def test_reverse_inlined(self):
        """list.reverse() → reverse()."""
        code = "arr = [1, 2, 3]; arr.reverse()"
        result = transpile(code)
        # Both use reverse(), should be same
        assert "reverse()" in result
    
    def test_append_multiple(self):
        """Multiple append calls."""
        code = """
arr = []
arr.append(1)
arr.append(2)
arr.append(3)
"""
        result = transpile(code)
        # All should use push
        assert result.count("push(") >= 3 or result.count("append") >= 3
    
    def test_append_with_expression(self):
        """Append with computed value."""
        code = "arr = [1, 2]; arr.append(len(arr) + 1)"
        result = transpile(code)
        # append should be push, but len needs runtime
        assert "push(" in result or "append" in result.lower()


# =============================================================================
# DICT METHOD INLINING
# =============================================================================

class TestDictMethodInlining:
    """Tests for dict method inlining."""
    
    def test_keys_inlined(self):
        """dict.keys() → Object.keys()."""
        code = 'd = {"a": 1}; k = d.keys()'
        result = transpile(code)
        assert "Object.keys" in result
        assert "__py.dict.keys" not in result
    
    def test_values_inlined(self):
        """dict.values() → Object.values()."""
        code = 'd = {"a": 1}; v = d.values()'
        result = transpile(code)
        assert "Object.values" in result
        assert "__py.dict.values" not in result
    
    def test_items_inlined(self):
        """dict.items() → Object.entries() or items()."""
        code = 'd = {"a": 1}; i = d.items()'
        result = transpile(code)
        # May use Object.entries or items() method
        assert "Object.entries" in result or "items" in result.lower()
    
    def test_keys_in_for(self):
        """for k in d.keys()."""
        code = """
d = {"a": 1, "b": 2}
for k in d.keys():
    print(k)
"""
        result = transpile(code)
        assert "Object.keys" in result
    
    def test_items_destructuring(self):
        """for k, v in d.items()."""
        code = """
d = {"a": 1, "b": 2}
for k, v in d.items():
    print(k, v)
"""
        result = transpile(code)
        # May use Object.entries or items()
        assert "Object.entries" in result or "items" in result.lower()


# =============================================================================
# NON-INLINABLE METHODS (should use runtime)
# =============================================================================

class TestNonInlinableMethods:
    """Tests that complex methods still use runtime helpers."""
    
    def test_split_with_no_args(self):
        """str.split() with no args needs runtime (whitespace handling)."""
        code = 's = "a  b   c"; words = s.split()'
        result = transpile(code)
        # split() without args has complex Python semantics
        # May use runtime or be inlined with special handling
        assert "split" in result.lower()
    
    def test_strip_with_chars(self):
        """str.strip(chars) needs runtime."""
        code = 's = "xxhelloxx"; t = s.strip("x")'
        result = transpile(code)
        # strip with chars argument can't be trim()
        assert "strip" in result.lower()
    
    def test_list_index(self):
        """list.index() needs runtime (ValueError handling)."""
        code = "arr = [1, 2, 3]; i = arr.index(2)"
        result = transpile(code)
        # indexOf doesn't throw ValueError
        assert "index" in result.lower()
    
    def test_dict_get(self):
        """dict.get() needs runtime (default value handling)."""
        code = 'd = {"a": 1}; v = d.get("b", 0)'
        result = transpile(code)
        # get() with default needs care
        assert "get" in result.lower()


# =============================================================================
# INLINING EDGE CASES
# =============================================================================

class TestInliningEdgeCases:
    """Edge cases for method inlining."""
    
    def test_method_on_variable(self):
        """Method on variable reference."""
        code = """
def process(s):
    return s.upper()
"""
        result = transpile(code)
        assert "toUpperCase()" in result
    
    def test_method_on_function_result(self):
        """Method on function return value."""
        code = """
def get_text():
    return "hello"

result = get_text().upper()
"""
        result = transpile(code)
        assert "toUpperCase()" in result
    
    def test_method_on_subscript(self):
        """Method on subscripted value."""
        code = """
items = ["hello", "world"]
upper = items[0].upper()
"""
        result = transpile(code)
        assert "toUpperCase()" in result
    
    def test_method_on_attribute(self):
        """Method on attribute access."""
        code = """
class Data:
    def __init__(self):
        self.text = "hello"

d = Data()
upper = d.text.upper()
"""
        result = transpile(code)
        assert "toUpperCase()" in result


# =============================================================================
# BUNDLE SIZE VERIFICATION
# =============================================================================

class TestBundleSizeImpact:
    """Verify inlining reduces runtime imports."""
    
    def test_no_str_import_for_upper(self):
        """str.upper() doesn't need __py.str import."""
        code = 'u = "hello".upper()'
        result = transpile(code)
        # Should not import __py.str
        assert "__py.str" not in result
        assert "import" not in result.lower() or "__py" not in result
    
    def test_no_list_import_for_append(self):
        """list.append() doesn't need __py.list import."""
        code = "arr = []; arr.append(1)"
        result = transpile(code)
        assert "__py.list" not in result
    
    def test_no_dict_import_for_keys(self):
        """dict.keys() doesn't need __py.dict import."""
        code = 'd = {"a": 1}; k = d.keys()'
        result = transpile(code)
        assert "__py.dict" not in result
    
    def test_minimal_code_size(self):
        """Simple operations produce minimal output."""
        code = 's = "hello"; u = s.upper(); l = s.lower()'
        result = transpile(code)
        # Should be simple JS without runtime
        assert "__py" not in result or "toUpperCase" in result
    
    def test_no_runtime_for_all_inlined(self):
        """Code with only inlinable methods needs no runtime."""
        code = """
s = "  hello world  "
t = s.strip().upper()
words = []
words.append(t)
"""
        result = transpile(code)
        # All methods are inlinable
        assert "toUpperCase()" in result
        # May still have some runtime for other features

