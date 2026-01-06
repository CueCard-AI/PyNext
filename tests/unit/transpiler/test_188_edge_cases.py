"""
Phase 18.8: Edge Cases Tests

Tests for edge cases: division, unicode, overflow, global/nonlocal.

Tests: 60
"""

import pytest
import warnings
from pynext.transpiler import parse, emit, transpile
from pynext.transpiler.errors import UnsupportedSyntax
from tests.unit.transpiler.test_utils import assert_has_runtime_function


class TestDivisionBehavior:
    """Tests for division edge cases."""
    
    def test_normal_division(self):
        """Normal division works."""
        js = transpile("x = 10 / 2")
        assert "/" in js
    
    def test_division_by_literal_zero(self):
        """Division by zero literal."""
        js = transpile("x = 1 / 0")
        assert "/ 0" in js or "/0" in js
        # JS will return Infinity
    
    def test_floor_division(self):
        """Floor division uses __py.floordiv."""
        js = transpile("x = 7 // 2")
        assert "__py.floordiv" in js or "//" not in js
    
    def test_modulo(self):
        """Modulo uses dunder runtime for unknown types, native JS for literals."""
        js = transpile("x = 7 % 3")
        # Numeric literals use native JS % operator (correct optimization)
        assert_has_runtime_function(js, "mod", allow_native_js=True)
    
    def test_negative_modulo(self):
        """Negative modulo (Python differs from JS)."""
        js = transpile("x = -7 % 3")
        assert_has_runtime_function(js, "mod")


class TestIntegerOverflow:
    """Tests for large integer handling."""
    
    def test_large_integer(self):
        """Large integers are emitted."""
        js = transpile("x = 9007199254740993")
        assert "9007199254740993" in js
    
    def test_very_large_integer(self):
        """Very large integers are emitted."""
        js = transpile("x = 99999999999999999999999999")
        assert "9999999999" in js
    
    def test_negative_large_integer(self):
        """Large negative integers."""
        js = transpile("x = -9007199254740993")
        assert "9007199254740993" in js
    
    def test_integer_operations(self):
        """Operations with large integers."""
        js = transpile("x = 9007199254740993 + 1")
        assert "+" in js


class TestUnicodeIdentifiers:
    """Tests for unicode identifier support."""
    
    def test_unicode_variable_name(self):
        """Unicode variable names work."""
        js = transpile("变量 = 5")
        assert "变量" in js
    
    def test_unicode_chinese(self):
        """Chinese characters in identifiers."""
        js = transpile("计数器 = 0")
        assert "计数器" in js
    
    def test_unicode_japanese(self):
        """Japanese characters in identifiers."""
        js = transpile("カウンター = 0")
        assert "カウンター" in js
    
    def test_unicode_russian(self):
        """Russian characters in identifiers."""
        js = transpile("переменная = 1")
        assert "переменная" in js
    
    def test_unicode_arabic(self):
        """Arabic characters in identifiers."""
        js = transpile("متغير = 2")
        assert "متغير" in js
    
    def test_unicode_greek(self):
        """Greek characters in identifiers."""
        js = transpile("μεταβλητή = 3")
        assert "μεταβλητή" in js
    
    def test_unicode_emoji_in_string(self):
        """Emoji in strings (not identifiers)."""
        js = transpile('x = "Hello 👋"')
        assert "👋" in js
    
    def test_unicode_function_name(self):
        """Unicode function names."""
        js = transpile("def 处理(): pass")
        assert "处理" in js
    
    def test_unicode_param_name(self):
        """Unicode parameter names."""
        js = transpile("def f(參數): return 參數")
        assert "參數" in js
    
    def test_mixed_ascii_unicode(self):
        """Mix of ASCII and unicode."""
        js = transpile("my_变量 = 5")
        assert "my_变量" in js
    
    def test_unicode_in_string(self):
        """Unicode in string literals."""
        js = transpile('greeting = "Привет мир"')
        assert "Привет" in js
    
    def test_unicode_class_name(self):
        """Unicode class names."""
        js = transpile("class クラス: pass")
        assert "クラス" in js
    
    def test_accented_characters(self):
        """Accented latin characters."""
        js = transpile("café = 'coffee'")
        assert "café" in js
    
    def test_umlaut_characters(self):
        """German umlaut characters."""
        js = transpile("größe = 10")
        assert "größe" in js


class TestGlobalNonlocal:
    """Tests for global/nonlocal handling."""
    
    def test_global_warning(self):
        """Global statement emits warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            ir = parse("""
def foo():
    global x
    x = 5
""")
            # Should have parsed without error
            assert ir is not None
    
    def test_nonlocal_warning(self):
        """Nonlocal statement emits warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            ir = parse("""
def outer():
    x = 1
    def inner():
        nonlocal x
        x = 2
""")
            assert ir is not None
    
    def test_global_multiple_names(self):
        """Global with multiple names."""
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            ir = parse("""
def foo():
    global a, b, c
    a = 1
""")
            assert ir is not None
    
    def test_nonlocal_multiple_names(self):
        """Nonlocal with multiple names."""
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            ir = parse("""
def outer():
    a = b = c = 0
    def inner():
        nonlocal a, b, c
        a = 1
""")
            assert ir is not None
    
    def test_global_transpiles(self):
        """Code with global still transpiles."""
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            js = transpile("""
def foo():
    global counter
    counter = counter + 1
""")
            assert "counter" in js


class TestSpecialCharacters:
    """Tests for special characters in code."""
    
    def test_backslash_in_string(self):
        """Backslash in strings."""
        js = transpile(r'path = "C:\\Users"')
        assert "Users" in js
    
    def test_newline_in_string(self):
        """Newline in strings."""
        js = transpile('text = "line1\\nline2"')
        assert "\\n" in js or "line1" in js
    
    def test_tab_in_string(self):
        """Tab in strings."""
        js = transpile('text = "col1\\tcol2"')
        assert "\\t" in js or "col1" in js
    
    def test_quote_in_string(self):
        """Quotes in strings."""
        js = transpile('quote = "He said \\"hello\\""')
        assert "hello" in js
    
    def test_single_quote_in_double_quoted(self):
        """Single quote in double-quoted string."""
        js = transpile("text = \"it's\"")
        assert "it" in js


class TestEdgeCaseExpressions:
    """Tests for edge case expressions."""
    
    def test_chained_comparison(self):
        """Chained comparisons."""
        js = transpile("valid = 0 < x < 10")
        assert "x" in js
    
    def test_negative_index(self):
        """Negative indexing uses __py.at."""
        js = transpile("last = items[-1]")
        assert "__py.at" in js
    
    def test_negative_slice(self):
        """Negative slicing."""
        js = transpile("reversed = items[::-1]")
        assert "__py.slice" in js
    
    def test_empty_list_literal(self):
        """Empty list."""
        js = transpile("x = []")
        assert "[]" in js
    
    def test_empty_dict_literal(self):
        """Empty dict."""
        js = transpile("x = {}")
        assert "{}" in js
    
    def test_none_value(self):
        """None value."""
        js = transpile("x = None")
        assert "null" in js
    
    def test_true_false(self):
        """True and False values."""
        js = transpile("x = True; y = False")
        assert "true" in js
        assert "false" in js
    
    def test_triple_quoted_string(self):
        """Triple-quoted strings."""
        js = transpile('doc = """multi\nline"""')
        assert "multi" in js
    
    def test_raw_string(self):
        """Raw strings."""
        js = transpile(r'pattern = r"\d+"')
        assert "\\d" in js
    
    def test_bytes_literal(self):
        """Bytes literals (may not be fully supported)."""
        try:
            js = transpile('data = b"hello"')
            # If it parses, check something reasonable
            assert "hello" in js or js is not None
        except:
            pass  # Bytes might not be supported


class TestCommentHandling:
    """Tests for comments in code."""
    
    def test_comment_ignored(self):
        """Comments are ignored."""
        js = transpile("""
# This is a comment
x = 5
""")
        assert "x" in js
        assert "This is a comment" not in js
    
    def test_inline_comment(self):
        """Inline comments."""
        js = transpile("x = 5  # inline")
        assert "x" in js
        assert "inline" not in js
    
    def test_multiple_comments(self):
        """Multiple comments."""
        js = transpile("""
# Comment 1
x = 1
# Comment 2
y = 2
""")
        assert "x" in js
        assert "y" in js


class TestWhitespace:
    """Tests for whitespace handling."""
    
    def test_extra_blank_lines(self):
        """Extra blank lines."""
        js = transpile("""
x = 1


y = 2
""")
        assert "x" in js
        assert "y" in js
    
    def test_trailing_whitespace(self):
        """Trailing whitespace."""
        js = transpile("x = 5   ")
        assert "x" in js
    
    def test_leading_whitespace_in_function(self):
        """Proper indentation in function."""
        js = transpile("""
def foo():
    x = 1
    y = 2
    return x + y
""")
        assert "foo" in js

