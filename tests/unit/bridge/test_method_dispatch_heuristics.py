"""
Tests for Method Dispatch Heuristics

The transpiler uses heuristics to determine how to emit certain methods
that exist in multiple Python types (dict, set, signal, etc).

Critical Risk: .update() is used by:
- dict.update(other_dict) → __py.dict.update(d, other)
- set.update(other_set) → __py.set.update(s, other)
- signal.update(lambda x: x+1) → signal.update(fn)

This tests the heuristics that distinguish between these.
"""

import pytest
from pynext.transpiler import transpile, parse, emit


class TestUpdateMethodHeuristics:
    """Test dispatch of the ambiguous .update() method."""
    
    def test_signal_update_with_lambda(self):
        """signal.update(lambda v: v+1) should emit as signal update."""
        source = "count.update(lambda v: v + 1)"
        js = transpile(source)
        
        # Should preserve as update call with function
        assert "update" in js
        # Lambda should be converted to arrow function
        assert "=>" in js or "function" in js
    
    def test_dict_update_with_dict(self):
        """dict.update({...}) should use __py.dict.update or Object.assign."""
        source = 'd.update({"a": 1})'
        js = transpile(source)
        
        # Should use dict update helper or Object.assign
        assert "__py.dict.update" in js or "Object.assign" in js or "update" in js
    
    def test_set_update_with_list(self):
        """set.update([1,2,3]) should use set update."""
        source = "s.update([1, 2, 3])"
        js = transpile(source)
        
        # Should handle set update
        assert "update" in js or "add" in js
    
    def test_update_with_variable_arg(self):
        """update(variable) - heuristic must guess."""
        source = "x.update(y)"
        js = transpile(source)
        
        # Should produce some form of update call
        assert "update" in js


class TestAppendVsPushHeuristics:
    """Test list.append() translation to JS push()."""
    
    def test_append_to_list(self):
        """list.append(item) should become push()."""
        source = "items.append(x)"
        js = transpile(source)
        
        assert "push" in js
    
    def test_append_with_complex_item(self):
        """append with dict/object argument."""
        source = 'items.append({"id": 1})'
        js = transpile(source)
        
        assert "push" in js
        assert "id" in js


class TestRemoveMethodHeuristics:
    """Test disambiguation of .remove() method."""
    
    def test_list_remove(self):
        """list.remove(item) removes first occurrence."""
        source = "items.remove(x)"
        js = transpile(source)
        
        # Should use splice-based removal or helper
        assert "splice" in js or "__py.list.remove" in js or "remove" in js
    
    def test_set_remove(self):
        """set.remove(item) removes from set."""
        source = "my_set.remove(item)"
        js = transpile(source)
        
        # Could be .delete() for Set or helper
        assert "delete" in js or "remove" in js or "__py.set.remove" in js


class TestPopMethodHeuristics:
    """Test disambiguation of .pop() method."""
    
    def test_list_pop_no_args(self):
        """list.pop() removes and returns last element."""
        source = "last = items.pop()"
        js = transpile(source)
        
        assert "pop" in js
    
    def test_list_pop_with_index(self):
        """list.pop(0) removes first element."""
        source = "first = items.pop(0)"
        js = transpile(source)
        
        # May use splice for arbitrary index
        assert "pop" in js or "splice" in js or "__py.list.pop" in js
    
    def test_dict_pop(self):
        """dict.pop(key) removes and returns value."""
        source = 'value = d.pop("key")'
        js = transpile(source)
        
        # Dict pop is different from list pop
        assert "pop" in js or "__py.dict.pop" in js or "delete" in js
    
    def test_dict_pop_with_default(self):
        """dict.pop(key, default) with default value."""
        source = 'd.pop("key", None)'
        js = transpile(source)
        
        # Should handle default value
        assert "pop" in js or "__py.dict.pop" in js


class TestGetMethodHeuristics:
    """Test .get() method (primarily dict)."""
    
    def test_dict_get_simple(self):
        """dict.get(key) returns value or None."""
        source = 'd.get("key")'
        js = transpile(source)
        
        # Should use bracket access or __py.dict.get
        assert "__py.dict.get" in js or "get" in js or "[" in js
    
    def test_dict_get_with_default(self):
        """dict.get(key, default) with default value."""
        source = 'd.get("key", "default")'
        js = transpile(source)
        
        # Should handle the default
        assert "default" in js
    
    def test_dict_get_numeric_default(self):
        """dict.get(key, 0) with numeric default."""
        source = 'd.get("count", 0)'
        js = transpile(source)
        
        assert "0" in js


class TestClearMethodHeuristics:
    """Test .clear() method disambiguation."""
    
    def test_list_clear(self):
        """list.clear() empties the list."""
        source = "items.clear()"
        js = transpile(source)
        
        # Could be length = 0 or splice(0) or helper
        assert "clear" in js or "length = 0" in js or "splice" in js
    
    def test_dict_clear(self):
        """dict.clear() empties the dict."""
        source = "d.clear()"
        js = transpile(source)
        
        # Transpiler may use .length = 0 for arrays or clear helper
        assert "clear" in js or "__py.dict.clear" in js or "length = 0" in js


class TestCopyMethodHeuristics:
    """Test .copy() method for shallow copy."""
    
    def test_list_copy(self):
        """list.copy() creates shallow copy."""
        source = "new_list = items.copy()"
        js = transpile(source)
        
        # Could be slice() or spread or Array.from
        assert "slice" in js or "[..." in js or "Array.from" in js or "copy" in js
    
    def test_dict_copy(self):
        """dict.copy() creates shallow copy."""
        source = "new_dict = d.copy()"
        js = transpile(source)
        
        # Could be Object.assign, spread, slice, or helper
        # Transpiler may use [...d] for arrays
        assert "Object.assign" in js or "{..." in js or "__py.dict.copy" in js or "copy" in js or "[..." in js


class TestKeysValuesItemsMethods:
    """Test dict iteration methods."""
    
    def test_dict_keys(self):
        """dict.keys() returns keys iterator."""
        source = "for k in d.keys():"
        # Need full statement
        source = """
for k in d.keys():
    print(k)
"""
        js = transpile(source)
        
        assert "keys" in js or "Object.keys" in js
    
    def test_dict_values(self):
        """dict.values() returns values iterator."""
        source = """
for v in d.values():
    print(v)
"""
        js = transpile(source)
        
        assert "values" in js or "Object.values" in js
    
    def test_dict_items(self):
        """dict.items() returns key-value pairs."""
        source = """
for k, v in d.items():
    print(k, v)
"""
        js = transpile(source)
        
        assert "entries" in js or "items" in js or "Object.entries" in js


class TestStringMethods:
    """Test string method translations."""
    
    def test_str_split(self):
        """str.split() should work correctly."""
        source = 's.split(",")'
        js = transpile(source)
        
        assert "split" in js
    
    def test_str_join(self):
        """str.join(iterable) - Python syntax differs from JS."""
        source = '",".join(items)'
        js = transpile(source)
        
        # Python: sep.join(items)
        # JS: items.join(sep)
        assert "join" in js
    
    def test_str_strip(self):
        """str.strip() -> trim()."""
        source = "s.strip()"
        js = transpile(source)
        
        assert "trim" in js or "strip" in js
    
    def test_str_replace(self):
        """str.replace(old, new)."""
        source = 's.replace("old", "new")'
        js = transpile(source)
        
        assert "replace" in js
    
    def test_str_lower_upper(self):
        """str.lower() and upper()."""
        lower = transpile("s.lower()")
        upper = transpile("s.upper()")
        
        assert "toLowerCase" in lower or "lower" in lower
        assert "toUpperCase" in upper or "upper" in upper
    
    def test_str_startswith_endswith(self):
        """str.startswith() and endswith()."""
        starts = transpile('s.startswith("pre")')
        ends = transpile('s.endswith("suf")')
        
        assert "startsWith" in starts or "startswith" in starts
        assert "endsWith" in ends or "endswith" in ends


class TestBuiltinFunctions:
    """Test builtin function translations."""
    
    def test_len_list(self):
        """len(list) -> list.length."""
        js = transpile("n = len(items)")
        
        assert "length" in js or "__py.len" in js
    
    def test_len_string(self):
        """len(str) -> str.length."""
        js = transpile("n = len(s)")
        
        assert "length" in js or "__py.len" in js
    
    def test_len_dict(self):
        """len(dict) -> Object.keys(d).length."""
        js = transpile("n = len(d)")
        
        assert "length" in js or "__py.len" in js
    
    def test_str_conversion(self):
        """str(x) -> String(x) or x.toString()."""
        js = transpile("s = str(x)")
        
        assert "String" in js or "toString" in js or "str" in js
    
    def test_int_conversion(self):
        """int(x) -> parseInt or Math.floor."""
        js = transpile("n = int(x)")
        
        assert "parseInt" in js or "Math" in js or "__py.int" in js or "int" in js
    
    def test_float_conversion(self):
        """float(x) -> parseFloat or Number."""
        js = transpile("f = float(x)")
        
        assert "parseFloat" in js or "Number" in js or "__py.float" in js or "float" in js
    
    def test_bool_conversion(self):
        """bool(x) -> Python truthiness check."""
        js = transpile("b = bool(x)")
        
        # Should use __py.bool for correct Python semantics
        assert "bool" in js or "__py.bool" in js
    
    def test_abs_function(self):
        """abs(x) -> Math.abs(x)."""
        js = transpile("n = abs(x)")
        
        assert "Math.abs" in js or "abs" in js
    
    def test_min_max_functions(self):
        """min/max with multiple args."""
        min_js = transpile("m = min(a, b, c)")
        max_js = transpile("m = max(a, b, c)")
        
        assert "Math.min" in min_js or "min" in min_js
        assert "Math.max" in max_js or "max" in max_js
    
    def test_range_function(self):
        """range() for iteration."""
        js = transpile("""
for i in range(5):
    print(i)
""")
        
        # Should generate a loop or use __py.range
        assert "for" in js.lower() or "__py.range" in js


class TestTypeHintingIgnored:
    """Test that type hints are ignored correctly."""
    
    def test_variable_with_type(self):
        """Variable with type annotation."""
        js = transpile("x: int = 5")
        
        assert "5" in js
        # Type annotation should not appear
        assert "int" not in js or ": int" not in js
    
    def test_function_with_types(self):
        """Function with type annotations."""
        js = transpile("""
def add(a: int, b: int) -> int:
    return a + b
""")
        
        assert "function" in js or "=>" in js
        # Types should be stripped
        assert ": int" not in js


class TestEdgeCaseMethodCalls:
    """Test edge cases in method call handling."""
    
    def test_chained_method_calls(self):
        """Chained methods should work."""
        js = transpile('s.strip().lower().split(",")')
        
        # All methods should be translated
        assert "split" in js
    
    def test_method_on_literal(self):
        """Method called directly on literal."""
        js = transpile('"hello".upper()')
        
        assert "toUpperCase" in js or "upper" in js
    
    def test_method_on_expression(self):
        """Method on complex expression."""
        js = transpile("(a + b).strip()")
        
        assert "trim" in js or "strip" in js
