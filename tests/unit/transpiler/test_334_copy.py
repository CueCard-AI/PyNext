"""
Phase 33.4: copy Module Tests

Comprehensive tests for Python copy module transpilation.
Tests verify the runtime provides correct JavaScript implementations for:
- copy (shallow copy)
- deepcopy (deep copy)
- Custom __copy__ and __deepcopy__
"""

import pytest


# =============================================================================
# SHALLOW COPY TESTS (7 tests)
# =============================================================================

class TestShallowCopy:
    """Tests for copy()."""
    
    def test_copy_list(self):
        """copy creates new list."""
        from pynext.runtime.stdlib.copy import copy
        original = [1, 2, 3]
        copied = copy(original)
        assert copied == original
        assert copied is not original
    
    def test_copy_dict(self):
        """copy creates new dict."""
        from pynext.runtime.stdlib.copy import copy
        original = {"a": 1, "b": 2}
        copied = copy(original)
        assert copied == original
        assert copied is not original
    
    def test_copy_nested_shares_refs(self):
        """copy does not copy nested objects."""
        from pynext.runtime.stdlib.copy import copy
        inner = [1, 2, 3]
        original = {"inner": inner}
        copied = copy(original)
        assert copied["inner"] is inner
    
    def test_copy_modifying_nested_affects_original(self):
        """Modifying nested in copy affects original."""
        from pynext.runtime.stdlib.copy import copy
        original = {"inner": [1, 2, 3]}
        copied = copy(original)
        copied["inner"].append(4)
        assert original["inner"] == [1, 2, 3, 4]
    
    def test_copy_set(self):
        """copy creates new set."""
        from pynext.runtime.stdlib.copy import copy
        original = {1, 2, 3}
        copied = copy(original)
        assert copied == original
        assert copied is not original
    
    def test_copy_tuple(self):
        """copy returns same tuple (immutable)."""
        from pynext.runtime.stdlib.copy import copy
        original = (1, 2, 3)
        copied = copy(original)
        # Tuples are immutable, copy may return same object
        assert copied == original
    
    def test_copy_string(self):
        """copy returns same string (immutable)."""
        from pynext.runtime.stdlib.copy import copy
        original = "hello"
        copied = copy(original)
        assert copied == original


# =============================================================================
# DEEP COPY TESTS (8 tests)
# =============================================================================

class TestDeepCopy:
    """Tests for deepcopy()."""
    
    def test_deepcopy_list(self):
        """deepcopy creates new list."""
        from pynext.runtime.stdlib.copy import deepcopy
        original = [1, 2, 3]
        copied = deepcopy(original)
        assert copied == original
        assert copied is not original
    
    def test_deepcopy_nested(self):
        """deepcopy copies nested objects."""
        from pynext.runtime.stdlib.copy import deepcopy
        inner = [1, 2, 3]
        original = {"inner": inner}
        copied = deepcopy(original)
        assert copied["inner"] == inner
        assert copied["inner"] is not inner
    
    def test_deepcopy_modifying_nested(self):
        """Modifying nested in deepcopy does not affect original."""
        from pynext.runtime.stdlib.copy import deepcopy
        original = {"inner": [1, 2, 3]}
        copied = deepcopy(original)
        copied["inner"].append(4)
        assert original["inner"] == [1, 2, 3]
        assert copied["inner"] == [1, 2, 3, 4]
    
    def test_deepcopy_deeply_nested(self):
        """deepcopy handles deeply nested structures."""
        from pynext.runtime.stdlib.copy import deepcopy
        original = {"a": {"b": {"c": [1, 2, 3]}}}
        copied = deepcopy(original)
        copied["a"]["b"]["c"].append(4)
        assert original["a"]["b"]["c"] == [1, 2, 3]
    
    def test_deepcopy_list_of_dicts(self):
        """deepcopy handles list of dicts."""
        from pynext.runtime.stdlib.copy import deepcopy
        original = [{"a": 1}, {"b": 2}]
        copied = deepcopy(original)
        copied[0]["a"] = 100
        assert original[0]["a"] == 1
    
    def test_deepcopy_circular_reference(self):
        """deepcopy handles circular references."""
        from pynext.runtime.stdlib.copy import deepcopy
        original = {"self": None}
        original["self"] = original
        copied = deepcopy(original)
        assert copied["self"] is copied
        assert copied is not original
    
    def test_deepcopy_preserves_types(self):
        """deepcopy preserves object types."""
        from pynext.runtime.stdlib.copy import deepcopy
        original = {"list": [1, 2], "set": {1, 2}, "dict": {"a": 1}}
        copied = deepcopy(original)
        assert type(copied["list"]) == list
        assert type(copied["set"]) == set
        assert type(copied["dict"]) == dict
    
    def test_deepcopy_none(self):
        """deepcopy handles None."""
        from pynext.runtime.stdlib.copy import deepcopy
        assert deepcopy(None) is None


# =============================================================================
# CUSTOM COPY TESTS (5 tests)
# =============================================================================

class TestCustomCopy:
    """Tests for custom __copy__ and __deepcopy__."""
    
    def test_custom_copy(self):
        """Objects can define __copy__."""
        from pynext.runtime.stdlib.copy import copy
        
        class MyClass:
            def __init__(self, value):
                self.value = value
                self.copies = 0
            
            def __copy__(self):
                new = MyClass(self.value)
                new.copies = self.copies + 1
                return new
        
        obj = MyClass(42)
        copied = copy(obj)
        assert copied.value == 42
        assert copied.copies == 1
    
    def test_custom_deepcopy(self):
        """Objects can define __deepcopy__."""
        from pynext.runtime.stdlib.copy import deepcopy
        
        class MyClass:
            def __init__(self, value, data):
                self.value = value
                self.data = data
            
            def __deepcopy__(self, memo):
                new_data = deepcopy(self.data, memo)
                return MyClass(self.value, new_data)
        
        obj = MyClass(42, [1, 2, 3])
        copied = deepcopy(obj)
        assert copied.value == 42
        assert copied.data == [1, 2, 3]
        assert copied.data is not obj.data
    
    def test_copy_without_custom(self):
        """copy works without __copy__."""
        from pynext.runtime.stdlib.copy import copy
        
        class Simple:
            def __init__(self, x):
                self.x = x
        
        obj = Simple(42)
        copied = copy(obj)
        assert copied.x == 42
    
    def test_deepcopy_without_custom(self):
        """deepcopy works without __deepcopy__."""
        from pynext.runtime.stdlib.copy import deepcopy
        
        class Simple:
            def __init__(self, x, nested):
                self.x = x
                self.nested = nested
        
        obj = Simple(42, [1, 2, 3])
        copied = deepcopy(obj)
        assert copied.x == 42
        assert copied.nested == [1, 2, 3]
    
    def test_deepcopy_memo(self):
        """deepcopy memo prevents infinite loops."""
        from pynext.runtime.stdlib.copy import deepcopy
        
        # Create object that references itself
        obj = {"name": "self-ref"}
        obj["self"] = obj
        
        copied = deepcopy(obj)
        assert copied["self"] is copied
