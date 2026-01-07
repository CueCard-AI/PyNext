"""
Tests for Phase 33.5: Proxy-based Attribute Access

Tests the transpilation of classes with __getattr__, __setattr__, __delattr__
to JavaScript classes wrapped with Proxy.

Run with: pytest tests/unit/transpiler/test_335_attribute_proxy.py -v
"""

import pytest
from pynext.transpiler import transpile


class TestGetattr:
    """Tests for __getattr__ transpilation."""
    
    def test_basic_getattr(self):
        """Test basic __getattr__ class."""
        code = '''
class Dynamic:
    def __getattr__(self, name):
        return f"dynamic_{name}"
'''
        result = transpile(code)
        assert "class Dynamic" in result
        assert "__getattr__" in result
        assert "__py_create_Dynamic" in result
    
    def test_getattr_with_fallback(self):
        """Test __getattr__ with existing attributes."""
        code = '''
class Fallback:
    def __init__(self):
        self.known = "value"
    
    def __getattr__(self, name):
        return f"unknown_{name}"
'''
        result = transpile(code)
        assert "__py_create_Fallback" in result
    
    def test_getattr_with_dict(self):
        """Test __getattr__ accessing internal dict."""
        code = '''
class AttrDict:
    def __init__(self):
        self._data = {}
    
    def __getattr__(self, name):
        return self._data.get(name)
'''
        result = transpile(code)
        assert "__getattr__" in result
        assert "Proxy" in result
    
    def test_getattr_raises_attribute_error(self):
        """Test __getattr__ that raises AttributeError."""
        code = '''
class Strict:
    def __getattr__(self, name):
        raise AttributeError(f"No attribute {name}")
'''
        result = transpile(code)
        assert "__getattr__" in result
    
    def test_getattr_with_computed_value(self):
        """Test __getattr__ returning computed values."""
        code = '''
class Computed:
    def __getattr__(self, name):
        return len(name) * 2
'''
        result = transpile(code)
        assert "__getattr__" in result


class TestSetattr:
    """Tests for __setattr__ transpilation."""
    
    def test_basic_setattr(self):
        """Test basic __setattr__ class."""
        code = '''
class Setter:
    def __setattr__(self, name, value):
        print(f"Setting {name} to {value}")
        super().__setattr__(name, value)
'''
        result = transpile(code)
        assert "__setattr__" in result
        assert "__py_create_Setter" in result
    
    def test_setattr_validation(self):
        """Test __setattr__ with validation."""
        code = '''
class Validated:
    def __setattr__(self, name, value):
        if name == "age" and value < 0:
            raise ValueError("Age cannot be negative")
        object.__setattr__(self, name, value)
'''
        result = transpile(code)
        assert "__setattr__" in result
    
    def test_setattr_with_transform(self):
        """Test __setattr__ that transforms values."""
        code = '''
class Transform:
    def __setattr__(self, name, value):
        super().__setattr__(name, str(value).upper())
'''
        result = transpile(code)
        assert "__setattr__" in result


class TestDelattr:
    """Tests for __delattr__ transpilation."""
    
    def test_basic_delattr(self):
        """Test basic __delattr__ class."""
        code = '''
class Deletable:
    def __delattr__(self, name):
        print(f"Deleting {name}")
        super().__delattr__(name)
'''
        result = transpile(code)
        assert "__delattr__" in result
        assert "__py_create_Deletable" in result
    
    def test_delattr_prevents_deletion(self):
        """Test __delattr__ that prevents deletion."""
        code = '''
class Protected:
    def __delattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(f"Cannot delete {name}")
        super().__delattr__(name)
'''
        result = transpile(code)
        assert "__delattr__" in result


class TestCombinedDunders:
    """Tests for classes with multiple attribute dunders."""
    
    def test_getattr_and_setattr(self):
        """Test class with both __getattr__ and __setattr__."""
        code = '''
class Combined:
    def __getattr__(self, name):
        return self._data.get(name)
    
    def __setattr__(self, name, value):
        if name == "_data":
            super().__setattr__(name, value)
        else:
            self._data[name] = value
'''
        result = transpile(code)
        assert "__getattr__" in result
        assert "__setattr__" in result
        assert "__py_create_Combined" in result
    
    def test_all_three_dunders(self):
        """Test class with all three attribute dunders."""
        code = '''
class Full:
    def __getattr__(self, name):
        return f"got {name}"
    
    def __setattr__(self, name, value):
        print(f"set {name}")
    
    def __delattr__(self, name):
        print(f"del {name}")
'''
        result = transpile(code)
        assert "__getattr__" in result
        assert "__setattr__" in result
        assert "__delattr__" in result
        assert "__py_create_Full" in result


class TestProxyFactory:
    """Tests for the Proxy factory function emission."""
    
    def test_factory_function_emitted(self):
        """Test that factory function is emitted."""
        code = '''
class Proxied:
    def __getattr__(self, name):
        return name
'''
        result = transpile(code)
        assert "__py_create_Proxied" in result
        assert "new Proxy" in result
    
    def test_factory_passes_args(self):
        """Test that factory passes constructor arguments."""
        code = '''
class WithArgs:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def __getattr__(self, name):
        return f"{name}_{self.x}_{self.y}"
'''
        result = transpile(code)
        assert "__py_create_WithArgs" in result
        assert "...args" in result
    
    def test_instantiation_uses_factory(self):
        """Test that instantiation uses factory function."""
        code = '''
class Dynamic:
    def __getattr__(self, name):
        return name

obj = Dynamic()
'''
        result = transpile(code)
        assert "__py_create_Dynamic()" in result


class TestNoProxyNeeded:
    """Tests for classes that don't need Proxy wrapping."""
    
    def test_class_without_dunders(self):
        """Test regular class without attribute dunders."""
        code = '''
class Regular:
    def __init__(self):
        self.value = 42
'''
        result = transpile(code)
        assert "__py_create_Regular" not in result
    
    def test_class_with_other_dunders(self):
        """Test class with other dunders (not attribute-related)."""
        code = '''
class Other:
    def __str__(self):
        return "Other"
    
    def __len__(self):
        return 0
'''
        result = transpile(code)
        assert "__py_create_Other" not in result
    
    def test_class_with_getitem_not_getattr(self):
        """Test that __getitem__ doesn't trigger attribute Proxy."""
        code = '''
class Subscriptable:
    def __getitem__(self, key):
        return self._data[key]
'''
        result = transpile(code)
        # __getitem__ uses subscript proxy, not attribute proxy
        # The attribute proxy factory should not be emitted
        assert "__py_create_Subscriptable" not in result or "Proxy" not in result


class TestEdgeCases:
    """Tests for edge cases in attribute proxy handling."""
    
    def test_inherited_getattr(self):
        """Test class inheriting from another with __getattr__."""
        code = '''
class Base:
    def __getattr__(self, name):
        return name

class Child(Base):
    pass
'''
        result = transpile(code)
        # Base should have factory, Child might or might not depending on implementation
        assert "__py_create_Base" in result
    
    def test_multiple_classes_with_getattr(self):
        """Test multiple classes with __getattr__ in same file."""
        code = '''
class First:
    def __getattr__(self, name):
        return 1

class Second:
    def __getattr__(self, name):
        return 2
'''
        result = transpile(code)
        assert "__py_create_First" in result
        assert "__py_create_Second" in result
    
    def test_getattr_with_super_call(self):
        """Test __getattr__ that calls super()."""
        code = '''
class Extended:
    def __getattr__(self, name):
        if name.startswith("x_"):
            return f"extended_{name}"
        return super().__getattr__(name)
'''
        result = transpile(code)
        assert "__getattr__" in result
    
    def test_class_method_instantiation(self):
        """Test instantiation in class method."""
        code = '''
class Factory:
    def __getattr__(self, name):
        return name
    
    @classmethod
    def create(cls):
        return cls()
'''
        result = transpile(code)
        assert "__py_create_Factory" in result

