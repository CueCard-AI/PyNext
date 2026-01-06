"""
Tests for Python String Methods Transpilation (Phase 18.3)

This file tests the transpilation of Python string methods to JavaScript.
Categories:
1. Basic - Simple method calls, correct output
2. Edge Cases - Empty strings, None, boundaries, unicode
3. Error Handling - Exceptions, invalid inputs
4. Integration - Chained methods, nested calls, comprehensions

Target: 200 tests
"""

import pytest
from pynext.transpiler import transpile, transpile_expression


# =============================================================================
# DIRECT MAPPINGS - Same semantics
# =============================================================================

class TestStringLower:
    """Tests for s.lower() → s.toLowerCase()"""
    
    def test_basic(self):
        assert transpile_expression('s.lower()') == 's.toLowerCase()'
    
    def test_on_literal(self):
        result = transpile_expression('"HELLO".lower()')
        assert '.toLowerCase()' in result
    
    def test_chained_with_strip(self):
        result = transpile_expression('s.strip().lower()')
        assert '.trim().toLowerCase()' in result
    
    def test_in_fstring(self):
        result = transpile_expression('f"{name.lower()}"')
        assert '.toLowerCase()' in result
    
    def test_in_comprehension(self):
        result = transpile_expression('[x.lower() for x in items]')
        assert '.toLowerCase()' in result


class TestStringUpper:
    """Tests for s.upper() → s.toUpperCase()"""
    
    def test_basic(self):
        assert transpile_expression('s.upper()') == 's.toUpperCase()'
    
    def test_chained(self):
        result = transpile_expression('s.strip().upper()')
        assert '.toUpperCase()' in result
    
    def test_in_condition(self):
        result = transpile('if s.upper() == "YES":\n    pass')
        assert '.toUpperCase()' in result


class TestStringStartswith:
    """Tests for s.startswith() → s.startsWith()"""
    
    def test_basic(self):
        result = transpile_expression('s.startswith("http")')
        assert 's.startsWith("http")' in result
    
    def test_with_variable(self):
        result = transpile_expression('s.startswith(prefix)')
        assert '.startsWith(prefix)' in result


class TestStringEndswith:
    """Tests for s.endswith() → s.endsWith()"""
    
    def test_basic(self):
        result = transpile_expression('s.endswith(".py")')
        assert 's.endsWith(".py")' in result


class TestStringFind:
    """Tests for s.find() → s.indexOf()"""
    
    def test_basic(self):
        result = transpile_expression('s.find("x")')
        assert 's.indexOf("x")' in result
    
    def test_with_start(self):
        result = transpile_expression('s.find("x", 5)')
        assert 'indexOf' in result


class TestStringRfind:
    """Tests for s.rfind() → s.lastIndexOf()"""
    
    def test_basic(self):
        result = transpile_expression('s.rfind("x")')
        assert 's.lastIndexOf("x")' in result


# =============================================================================
# RUNTIME HELPERS - Different semantics
# =============================================================================

class TestStringSplit:
    """Tests for s.split() - CRITICAL semantic difference"""
    
    def test_no_args_uses_runtime(self):
        result = transpile_expression('s.split()')
        assert '__py.str.split(s)' in result
    
    def test_with_sep_uses_runtime(self):
        result = transpile_expression('s.split(",")')
        assert '__py.str.split(s, ",")' in result
    
    def test_with_maxsplit(self):
        result = transpile_expression('s.split(",", 2)')
        assert '__py.str.split(s, ",", 2)' in result
    
    def test_none_sep(self):
        result = transpile_expression('s.split(None)')
        assert '__py.str.split' in result
    
    def test_chained(self):
        result = transpile_expression('line.strip().split()')
        assert '.trim()' in result
        assert '__py.str.split' in result


class TestStringRsplit:
    """Tests for s.rsplit()"""
    
    def test_basic(self):
        result = transpile_expression('s.rsplit(",")')
        assert '__py.str.rsplit(s, ",")' in result
    
    def test_with_maxsplit(self):
        result = transpile_expression('s.rsplit(",", 1)')
        assert '__py.str.rsplit(s, ",", 1)' in result


class TestStringIndex:
    """Tests for s.index() - THROWS on not found"""
    
    def test_basic(self):
        result = transpile_expression('s.index("x")')
        assert '__py.str.index(s, "x")' in result
    
    def test_with_start(self):
        result = transpile_expression('s.index("x", 5)')
        assert '__py.str.index(s, "x", 5)' in result
    
    def test_with_start_end(self):
        result = transpile_expression('s.index("x", 1, 10)')
        assert '__py.str.index' in result


class TestStringRindex:
    """Tests for s.rindex()"""
    
    def test_basic(self):
        result = transpile_expression('s.rindex("x")')
        assert '__py.str.rindex(s, "x")' in result


class TestStringCount:
    """Tests for s.count()"""
    
    def test_basic(self):
        result = transpile_expression('s.count("x")')
        assert '__py.str.count(s, "x")' in result
    
    def test_with_start_end(self):
        result = transpile_expression('s.count("x", 1, 10)')
        assert '__py.str.count' in result


class TestStringTitle:
    """Tests for s.title()"""
    
    def test_basic(self):
        result = transpile_expression('s.title()')
        assert '__py.str.title(s)' in result


class TestStringCapitalize:
    """Tests for s.capitalize()"""
    
    def test_basic(self):
        result = transpile_expression('s.capitalize()')
        assert '__py.str.capitalize(s)' in result


class TestStringSwapcase:
    """Tests for s.swapcase()"""
    
    def test_basic(self):
        result = transpile_expression('s.swapcase()')
        assert '__py.str.swapcase(s)' in result


class TestStringCenter:
    """Tests for s.center()"""
    
    def test_basic(self):
        result = transpile_expression('s.center(10)')
        assert '__py.str.center(s, 10)' in result
    
    def test_with_fillchar(self):
        result = transpile_expression('s.center(10, "-")')
        assert '__py.str.center(s, 10, "-")' in result


class TestStringLjust:
    """Tests for s.ljust()"""
    
    def test_basic(self):
        result = transpile_expression('s.ljust(10)')
        assert '__py.str.ljust(s, 10)' in result


class TestStringRjust:
    """Tests for s.rjust()"""
    
    def test_basic(self):
        result = transpile_expression('s.rjust(10)')
        assert '__py.str.rjust(s, 10)' in result


class TestStringZfill:
    """Tests for s.zfill()"""
    
    def test_basic(self):
        result = transpile_expression('s.zfill(5)')
        assert '__py.str.zfill(s, 5)' in result


# =============================================================================
# STRIP VARIANTS - With custom characters
# =============================================================================

class TestStringStrip:
    """Tests for s.strip() - with optional chars"""
    
    def test_no_args(self):
        result = transpile_expression('s.strip()')
        assert 's.trim()' in result
    
    def test_with_chars(self):
        result = transpile_expression('s.strip("xy")')
        assert '__py.str.strip(s, "xy")' in result


class TestStringLstrip:
    """Tests for s.lstrip()"""
    
    def test_no_args(self):
        result = transpile_expression('s.lstrip()')
        assert 's.trimStart()' in result
    
    def test_with_chars(self):
        result = transpile_expression('s.lstrip("xy")')
        assert '__py.str.lstrip(s, "xy")' in result


class TestStringRstrip:
    """Tests for s.rstrip()"""
    
    def test_no_args(self):
        result = transpile_expression('s.rstrip()')
        assert 's.trimEnd()' in result
    
    def test_with_chars(self):
        result = transpile_expression('s.rstrip("xy")')
        assert '__py.str.rstrip(s, "xy")' in result


# =============================================================================
# REPLACE / JOIN
# =============================================================================

class TestStringReplace:
    """Tests for s.replace()"""
    
    def test_no_count(self):
        result = transpile_expression('s.replace("a", "b")')
        assert 's.replaceAll("a", "b")' in result
    
    def test_with_count(self):
        result = transpile_expression('s.replace("a", "b", 1)')
        assert '__py.str.replace(s, "a", "b", 1)' in result


class TestStringJoin:
    """Tests for sep.join(items)"""
    
    def test_basic(self):
        result = transpile_expression('",".join(items)')
        assert 'items.join(",")' in result
    
    def test_with_variable_sep(self):
        result = transpile_expression('sep.join(items)')
        assert 'items.join(sep)' in result
    
    def test_in_comprehension(self):
        result = transpile_expression('[sep.join(parts) for parts in items]')
        assert '.join(' in result


# =============================================================================
# PARTITION
# =============================================================================

class TestStringPartition:
    """Tests for s.partition()"""
    
    def test_basic(self):
        result = transpile_expression('s.partition(":")')
        assert '__py.str.partition(s, ":")' in result


class TestStringRpartition:
    """Tests for s.rpartition()"""
    
    def test_basic(self):
        result = transpile_expression('s.rpartition(":")')
        assert '__py.str.rpartition(s, ":")' in result


# =============================================================================
# SPLITLINES
# =============================================================================

class TestStringSplitlines:
    """Tests for s.splitlines()"""
    
    def test_basic(self):
        result = transpile_expression('s.splitlines()')
        assert '__py.str.splitlines(s)' in result
    
    def test_with_keepends(self):
        result = transpile_expression('s.splitlines(True)')
        assert '__py.str.splitlines(s, true)' in result.lower()


# =============================================================================
# IS* METHODS
# =============================================================================

class TestStringIsdigit:
    """Tests for s.isdigit()"""
    
    def test_basic(self):
        result = transpile_expression('s.isdigit()')
        assert '__py.str.isdigit(s)' in result


class TestStringIsalpha:
    """Tests for s.isalpha()"""
    
    def test_basic(self):
        result = transpile_expression('s.isalpha()')
        assert '__py.str.isalpha(s)' in result


class TestStringIsalnum:
    """Tests for s.isalnum()"""
    
    def test_basic(self):
        result = transpile_expression('s.isalnum()')
        assert '__py.str.isalnum(s)' in result


class TestStringIsspace:
    """Tests for s.isspace()"""
    
    def test_basic(self):
        result = transpile_expression('s.isspace()')
        assert '__py.str.isspace(s)' in result


class TestStringIsupper:
    """Tests for s.isupper()"""
    
    def test_basic(self):
        result = transpile_expression('s.isupper()')
        assert '__py.str.isupper(s)' in result


class TestStringIslower:
    """Tests for s.islower()"""
    
    def test_basic(self):
        result = transpile_expression('s.islower()')
        assert '__py.str.islower(s)' in result


class TestStringIstitle:
    """Tests for s.istitle()"""
    
    def test_basic(self):
        result = transpile_expression('s.istitle()')
        assert '__py.str.istitle(s)' in result


class TestStringIsnumeric:
    """Tests for s.isnumeric()"""
    
    def test_basic(self):
        result = transpile_expression('s.isnumeric()')
        assert '__py.str.isnumeric(s)' in result


class TestStringIsdecimal:
    """Tests for s.isdecimal()"""
    
    def test_basic(self):
        result = transpile_expression('s.isdecimal()')
        assert '__py.str.isdecimal(s)' in result


class TestStringIsidentifier:
    """Tests for s.isidentifier()"""
    
    def test_basic(self):
        result = transpile_expression('s.isidentifier()')
        assert '__py.str.isidentifier(s)' in result


# =============================================================================
# EXPANDTABS
# =============================================================================

class TestStringExpandtabs:
    """Tests for s.expandtabs()"""
    
    def test_basic(self):
        result = transpile_expression('s.expandtabs()')
        assert '__py.str.expandtabs(s)' in result
    
    def test_with_tabsize(self):
        result = transpile_expression('s.expandtabs(4)')
        assert '__py.str.expandtabs(s, 4)' in result


# =============================================================================
# ENCODE
# =============================================================================

class TestStringEncode:
    """Tests for s.encode()"""
    
    def test_basic(self):
        result = transpile_expression('s.encode()')
        assert '__py.str.encode(s)' in result
    
    def test_with_encoding(self):
        result = transpile_expression('s.encode("utf-8")')
        assert '__py.str.encode(s, "utf-8")' in result


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestStringMethodChaining:
    """Tests for chained string method calls."""
    
    def test_strip_lower(self):
        result = transpile_expression('s.strip().lower()')
        assert '.trim().toLowerCase()' in result
    
    def test_strip_split(self):
        result = transpile_expression('s.strip().split()')
        assert '.trim()' in result
        assert '__py.str.split' in result
    
    def test_upper_replace(self):
        result = transpile_expression('s.upper().replace("A", "B")')
        assert '.toUpperCase()' in result
        assert '.replaceAll(' in result
    
    def test_triple_chain(self):
        result = transpile_expression('s.strip().lower().split(":")')
        assert '.trim()' in result
        assert '.toLowerCase()' in result


class TestStringMethodsInComprehensions:
    """Tests for string methods in comprehensions."""
    
    def test_lower_in_list_comp(self):
        result = transpile_expression('[s.lower() for s in items]')
        assert '.toLowerCase()' in result
    
    def test_split_in_list_comp(self):
        result = transpile_expression('[s.split() for s in lines]')
        assert '__py.str.split' in result
    
    def test_strip_in_dict_comp(self):
        result = transpile_expression('{k.strip(): v for k, v in items}')
        assert '.trim()' in result


class TestStringMethodsInConditions:
    """Tests for string methods in if conditions."""
    
    def test_startswith_in_if(self):
        result = transpile('if s.startswith("http"):\n    pass')
        assert '.startsWith(' in result
    
    def test_isdigit_in_if(self):
        result = transpile('if s.isdigit():\n    pass')
        assert '__py.str.isdigit' in result
    
    def test_chained_in_if(self):
        result = transpile('if s.strip().lower() == "yes":\n    pass')
        assert '.trim().toLowerCase()' in result


class TestStringMethodsWithVariables:
    """Tests for string methods with variable arguments."""
    
    def test_split_with_variable_sep(self):
        result = transpile_expression('s.split(sep)')
        assert '__py.str.split(s, sep)' in result
    
    def test_replace_with_variables(self):
        result = transpile_expression('s.replace(old_str, new_str)')
        assert 's.replaceAll(old_str, new_str)' in result
    
    def test_center_with_variable_width(self):
        result = transpile_expression('s.center(width)')
        assert '__py.str.center(s, width)' in result


class TestStringMethodsOnFunctionResults:
    """Tests for string methods on function return values."""
    
    def test_lower_on_function_result(self):
        result = transpile_expression('get_name().lower()')
        assert 'get_name().toLowerCase()' in result
    
    def test_split_on_function_result(self):
        result = transpile_expression('get_line().split()')
        assert '__py.str.split(get_line())' in result
    
    def test_method_on_method_result(self):
        result = transpile_expression('get_text().strip().lower()')
        assert 'get_text().trim().toLowerCase()' in result


# =============================================================================
# EDGE CASES
# =============================================================================

class TestStringEdgeCases:
    """Edge cases for string methods."""
    
    def test_empty_string_literal_lower(self):
        result = transpile_expression('"".lower()')
        assert '.toLowerCase()' in result
    
    def test_method_on_subscript(self):
        result = transpile_expression('items[0].lower()')
        assert '.toLowerCase()' in result
    
    def test_method_on_dict_access(self):
        result = transpile_expression('d["key"].lower()')
        assert '.toLowerCase()' in result
    
    def test_method_with_method_arg(self):
        result = transpile_expression('s.replace(old.strip(), new.strip())')
        assert '.replaceAll(' in result
        assert '.trim()' in result
    
    def test_nested_join(self):
        result = transpile_expression('sep.join([x.strip() for x in items])')
        assert '.join(' in result
        assert '.trim()' in result


class TestStringMethodsInFStrings:
    """Tests for string methods in f-strings."""
    
    def test_lower_in_fstring(self):
        result = transpile_expression('f"Hello {name.lower()}"')
        assert '.toLowerCase()' in result
    
    def test_strip_in_fstring(self):
        result = transpile_expression('f"Value: {s.strip()}"')
        assert '.trim()' in result
    
    def test_join_in_fstring(self):
        result = transpile_expression('f"Items: {sep.join(items)}"')
        assert '.join(' in result
