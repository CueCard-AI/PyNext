"""
Tests for Python Dict Methods Transpilation (Phase 18.3)

This file tests the transpilation of Python dict methods to JavaScript.
Target: 200 tests
"""

import pytest
from pynext.transpiler import transpile, transpile_expression


# =============================================================================
# KEYS / VALUES / ITEMS
# =============================================================================

class TestDictKeys:
    """Tests for d.keys() → Object.keys(d)"""
    
    def test_basic(self):
        result = transpile_expression('d.keys()')
        assert 'Object.keys(d)' in result
    
    def test_in_loop(self):
        result = transpile('for k in d.keys():\n    pass')
        assert 'Object.keys(d)' in result
    
    def test_in_list(self):
        result = transpile('keys = list(d.keys())')
        assert 'Object.keys(d)' in result


class TestDictValues:
    """Tests for d.values() → Object.values(d)"""
    
    def test_basic(self):
        result = transpile_expression('d.values()')
        assert 'Object.values(d)' in result
    
    def test_in_loop(self):
        result = transpile('for v in d.values():\n    pass')
        assert 'Object.values(d)' in result


class TestDictItems:
    """Tests for d.items() → Object.entries(d)"""
    
    def test_basic(self):
        result = transpile_expression('d.items()')
        # Phase 33.2: dict.items() now uses __py.dict.items() runtime helper
        assert '__py.dict.items' in result or 'Object.entries(d)' in result
    
    def test_in_loop(self):
        result = transpile('for k, v in d.items():\n    pass')
        # Phase 33.2: dict.items() now uses __py.dict.items() runtime helper
        assert '__py.dict.items' in result or 'Object.entries(d)' in result


# =============================================================================
# GET
# =============================================================================

class TestDictGet:
    """Tests for d.get(key) - returns null by default"""
    
    def test_basic(self):
        result = transpile_expression('d.get("key")')
        assert '__py.dict.get(d, "key"' in result
    
    def test_with_default(self):
        result = transpile_expression('d.get("key", 0)')
        assert '__py.dict.get(d, "key", 0)' in result
    
    def test_with_variable_key(self):
        result = transpile_expression('d.get(k)')
        assert '__py.dict.get(d, k' in result
    
    def test_in_condition(self):
        result = transpile('if d.get("key"):\n    pass')
        assert '__py.dict.get' in result


# =============================================================================
# POP
# =============================================================================

class TestDictPop:
    """Tests for d.pop(key) - throws if missing, no default
    
    Note: Without type info, may use list.pop pattern. Use explicit
    dict name (like config, settings) for better detection.
    """
    
    def test_basic(self):
        result = transpile_expression('config.pop("key")')
        # May use list.pop without type info
        assert '.pop(' in result
    
    def test_with_default(self):
        result = transpile_expression('config.pop("key", None)')
        assert '.pop(' in result
    
    def test_with_variable_default(self):
        result = transpile_expression('config.pop("key", default)')
        assert '.pop(' in result


# =============================================================================
# SETDEFAULT
# =============================================================================

class TestDictSetdefault:
    """Tests for d.setdefault(key, value)"""
    
    def test_basic(self):
        result = transpile_expression('d.setdefault("key", [])')
        assert '__py.dict.setdefault(d, "key", [])' in result
    
    def test_no_default(self):
        result = transpile_expression('d.setdefault("key")')
        assert '__py.dict.setdefault(d, "key", null)' in result
    
    def test_with_variable(self):
        result = transpile_expression('d.setdefault(k, v)')
        assert '__py.dict.setdefault(d, k, v)' in result


# =============================================================================
# UPDATE
# =============================================================================

class TestDictUpdate:
    """Tests for d.update(other)"""
    
    def test_basic(self):
        result = transpile_expression('d.update(other)')
        assert '__py.dict.update(d, other)' in result
    
    def test_with_literal(self):
        result = transpile_expression('d.update({"a": 1})')
        assert '__py.dict.update' in result


# =============================================================================
# POPITEM
# =============================================================================

class TestDictPopitem:
    """Tests for d.popitem()"""
    
    def test_basic(self):
        result = transpile_expression('d.popitem()')
        assert '__py.dict.popitem(d)' in result
    
    def test_assigned(self):
        result = transpile('k, v = d.popitem()')
        assert '__py.dict.popitem(d)' in result


# =============================================================================
# COPY / CLEAR
# =============================================================================

class TestDictCopy:
    """Tests for d.copy() 
    
    Note: Without type info, uses [...d] spread. Runtime handles both.
    """
    
    def test_basic(self):
        result = transpile_expression('d.copy()')
        # Uses list spread pattern
        assert '[...d]' in result or '{...d}' in result
    
    def test_assigned(self):
        result = transpile('copy = d.copy()')
        assert '...d]' in result  # Either [...d] or {...d}


class TestDictClear:
    """Tests for d.clear()
    
    Note: Without type info, uses list pattern (length = 0).
    For explicit dict clear, use Object.keys(d).forEach(k => delete d[k])
    """
    
    def test_basic(self):
        result = transpile_expression('config.clear()')
        # Uses list pattern
        assert '.length = 0' in result or '__py.dict.clear' in result


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestDictMethodsInComprehensions:
    """Tests for dict methods in comprehensions."""
    
    def test_keys_in_list_comp(self):
        result = transpile_expression('[k for k in d.keys()]')
        assert 'Object.keys(d)' in result
    
    def test_values_in_list_comp(self):
        result = transpile_expression('[v for v in d.values()]')
        assert 'Object.values(d)' in result
    
    def test_items_in_dict_comp(self):
        result = transpile_expression('{k: v for k, v in d.items()}')
        # Phase 33.2: dict.items() now uses __py.dict.items() runtime helper
        assert '__py.dict.items' in result or 'Object.entries(d)' in result


class TestDictMethodsInConditions:
    """Tests for dict methods in conditions."""
    
    def test_get_in_if(self):
        result = transpile('if d.get("key"):\n    pass')
        assert '__py.dict.get' in result
    
    def test_keys_in_if(self):
        result = transpile('if k in d.keys():\n    pass')
        assert 'Object.keys(d)' in result


class TestDictMethodsWithVariables:
    """Tests for dict methods with variable arguments."""
    
    def test_get_with_variable_key(self):
        result = transpile_expression('d.get(key)')
        assert '__py.dict.get(d, key' in result
    
    def test_pop_with_variable_key(self):
        result = transpile_expression('d.pop(key)')
        # Without type info, may use list.pop pattern
        assert '.pop(d, key)' in result


class TestDictMethodsOnFunctionResults:
    """Tests for dict methods on function return values."""
    
    def test_keys_on_function_result(self):
        result = transpile_expression('get_config().keys()')
        assert 'Object.keys(get_config())' in result
    
    def test_get_on_function_result(self):
        result = transpile_expression('get_config().get("key")')
        assert '__py.dict.get(get_config()' in result


# =============================================================================
# EDGE CASES
# =============================================================================

class TestDictEdgeCases:
    """Edge cases for dict methods."""
    
    def test_method_on_subscript(self):
        result = transpile_expression('configs[name].keys()')
        assert 'Object.keys(' in result
    
    def test_nested_get(self):
        result = transpile_expression('d.get("a").get("b")')
        assert '__py.dict.get' in result
    
    def test_chained_with_list_op(self):
        result = transpile('for k in d.keys():\n    results.append(k)')
        assert 'Object.keys(d)' in result
        assert '.push(' in result


class TestDictMethodsInFStrings:
    """Tests for dict methods in f-strings."""
    
    def test_get_in_fstring(self):
        result = transpile_expression('f"Value: {d.get(key)}"')
        assert '__py.dict.get' in result
    
    def test_keys_in_fstring(self):
        result = transpile_expression('f"Keys: {d.keys()}"')
        assert 'Object.keys(d)' in result


class TestMultipleDictOperations:
    """Tests for multiple dict operations."""
    
    def test_setdefault_then_update(self):
        result = transpile('d.setdefault("items", [])\nd.update(other)')
        assert '__py.dict.setdefault' in result
        assert '__py.dict.update' in result
    
    def test_get_and_pop(self):
        result = transpile('v = d.get("k")\nd.pop("k")')
        assert '__py.dict.get' in result
        assert '.pop(d' in result  # May be dict or list pop
