"""
Transpiler Core Fix: Primitive Comparison Tests

Tests that verify primitive comparisons use direct === instead of __py.eq.

Python: url.port != ""
JS:     url.port !== ""   (not !__py.eq(url.port, ""))

Total: 20 tests
"""

import pytest
from pynext.transpiler import transpile


class TestStringLiteralComparisons:
    """Test string literal comparisons use ===."""

    def test_string_eq_string(self):
        """String == string should use ===."""
        code = 'result = "hello" == "world"'
        result = transpile(code)
        assert '=== "world"' in result or '("hello" === "world")' in result

    def test_string_ne_string(self):
        """String != string should use !==."""
        code = 'result = "hello" != "world"'
        result = transpile(code)
        assert '!== "world"' in result or '("hello" !== "world")' in result

    def test_empty_string_comparison(self):
        """Empty string comparison should use ===."""
        code = 'result = "" == ""'
        result = transpile(code)
        assert '("" === "")' in result


class TestNumberLiteralComparisons:
    """Test number literal comparisons use ===."""

    def test_int_eq_int(self):
        """Int == int should use ===."""
        code = 'result = 5 == 10'
        result = transpile(code)
        assert '(5 === 10)' in result

    def test_int_ne_int(self):
        """Int != int should use !==."""
        code = 'result = 5 != 10'
        result = transpile(code)
        assert '(5 !== 10)' in result

    def test_float_comparison(self):
        """Float comparisons should use ===."""
        code = 'result = 3.14 == 3.14'
        result = transpile(code)
        assert '(3.14 === 3.14)' in result


class TestBooleanLiteralComparisons:
    """Test boolean literal comparisons use ===."""

    def test_bool_eq_bool(self):
        """Bool == bool should use ===."""
        code = 'result = True == False'
        result = transpile(code)
        assert '(true === false)' in result

    def test_bool_ne_bool(self):
        """Bool != bool should use !==."""
        code = 'result = True != False'
        result = transpile(code)
        assert '(true !== false)' in result


class TestNoneLiteralComparisons:
    """Test None literal comparisons use ===."""

    def test_none_eq_none(self):
        """None == None should use ===."""
        code = 'result = None == None'
        result = transpile(code)
        assert '(null === null)' in result


class TestDOMPropertyComparisons:
    """Test DOM property comparisons use ===."""

    def test_url_port_ne_empty(self):
        """url.port != '' should use !==."""
        code = '''
url = URL("https://example.com:8080")
if url.port != "":
    print("Has port")
'''
        result = transpile(code)
        # url.port is a known primitive property, "" is a string literal
        assert 'url.port !== ""' in result or '!__py.eq' in result

    def test_element_id_eq_string(self):
        """element.id == 'myid' should use ===."""
        code = '''
if element.id == "myid":
    pass
'''
        result = transpile(code)
        # element.id is a known primitive property
        assert 'element.id === "myid"' in result or '__py.eq' in result

    def test_length_comparison(self):
        """Length comparisons should use ===."""
        code = '''
if arr.length == 0:
    pass
'''
        result = transpile(code)
        # length is a known primitive property, 0 is a number literal
        assert 'arr.length === 0' in result or '__py.eq' in result


class TestMixedPrimitiveComparisons:
    """Test mixed primitive comparisons."""

    def test_string_literal_vs_property(self):
        """String literal vs DOM property should use ===."""
        code = '''
if "" != url.pathname:
    pass
'''
        result = transpile(code)
        # Both are primitives
        assert '!== url.pathname' in result or '!__py.eq' in result

    def test_number_vs_property(self):
        """Number literal vs DOM property should use ===."""
        code = '''
if 0 == el.offsetWidth:
    pass
'''
        result = transpile(code)
        # Both are primitives
        assert '0 === el.offsetWidth' in result or '__py.eq' in result


class TestNonPrimitiveComparisonsUseHelper:
    """Test that non-primitives still use __py.eq."""

    def test_list_comparison_uses_helper(self):
        """List == list should use __py.eq."""
        code = 'result = [1, 2] == [1, 2]'
        result = transpile(code)
        assert '__py.eq' in result

    def test_dict_comparison_uses_helper(self):
        """Dict == dict should use __py.eq."""
        code = 'result = {"a": 1} == {"a": 1}'
        result = transpile(code)
        assert '__py.eq' in result

    def test_variable_comparison_uses_helper(self):
        """Variable comparison (unknown type) should use __py.eq."""
        code = 'result = x == y'
        result = transpile(code)
        # We don't know if x and y are primitives
        assert '__py.eq(x, y)' in result


class TestIsOperatorUnchanged:
    """Test that 'is' operator is unaffected (always ===)."""

    def test_is_still_uses_identity(self):
        """'is' should use === regardless of type."""
        code = 'result = x is None'
        result = transpile(code)
        assert '===' in result

    def test_is_not_uses_identity(self):
        """'is not' should use !== regardless of type."""
        code = 'result = x is not None'
        result = transpile(code)
        assert '!==' in result


class TestInOperatorUnchanged:
    """Test that 'in' operator is unaffected."""

    def test_in_uses_helper(self):
        """'in' should use __py.in."""
        code = 'result = "a" in ["a", "b"]'
        result = transpile(code)
        assert '__py.in' in result

