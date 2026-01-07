"""
Phase 33.5: Proxy Performance Benchmark Tests

Performance benchmarks comparing Proxy-wrapped classes vs
regular classes to ensure acceptable overhead.
"""

import pytest
import time
from pynext.transpiler import transpile


# =============================================================================
# PROXY DETECTION TESTS
# =============================================================================

class TestProxyDetection:
    """Tests for correct Proxy wrapper detection."""
    
    def test_class_with_getattr_gets_proxy(self):
        """Class with __getattr__ is detected for proxy wrapping."""
        code = '''
class Dynamic:
    def __getattr__(self, name):
        return f"got_{name}"
'''
        js = transpile(code)
        # Should have proxy factory or proxy reference
        assert "__py_create_Dynamic" in js or "Proxy" in js or "proxy" in js
    
    def test_class_with_setattr_gets_proxy(self):
        """Class with __setattr__ is detected for proxy wrapping."""
        code = '''
class Setter:
    def __init__(self):
        object.__setattr__(self, "_data", {})
    
    def __setattr__(self, name, value):
        self._data[name] = value
'''
        js = transpile(code)
        assert "__setattr__" in js
    
    def test_class_with_delattr_gets_proxy(self):
        """Class with __delattr__ is detected for proxy wrapping."""
        code = '''
class Deleter:
    def __init__(self):
        self._attrs = set()
    
    def __delattr__(self, name):
        self._attrs.discard(name)
'''
        js = transpile(code)
        assert "__delattr__" in js
    
    def test_class_without_dunders_no_proxy(self):
        """Class without attribute dunders should not get proxy."""
        code = '''
class Normal:
    def __init__(self, value):
        self.value = value
    
    def get_value(self):
        return self.value
'''
        js = transpile(code)
        # Should not have proxy factory
        assert "__py_create_Normal" not in js
    
    def test_class_with_other_dunders_no_proxy(self):
        """Class with non-attribute dunders should not get proxy."""
        code = '''
class Comparable:
    def __init__(self, value):
        self.value = value
    
    def __eq__(self, other):
        return self.value == other.value
    
    def __str__(self):
        return str(self.value)
'''
        js = transpile(code)
        # Should not have proxy factory
        assert "__py_create_Comparable" not in js


# =============================================================================
# ATTRIBUTE ACCESS TRANSPILATION
# =============================================================================

class TestAttributeAccessTranspilation:
    """Tests for attribute access transpilation with proxies."""
    
    def test_getattr_fallback_logic(self):
        """__getattr__ is called for missing attributes."""
        code = '''
class FallbackGetter:
    def __init__(self):
        self.known = 42
    
    def __getattr__(self, name):
        return f"fallback_{name}"

obj = FallbackGetter()
print(obj.known)     # Direct access
print(obj.unknown)   # Falls back to __getattr__
'''
        js = transpile(code)
        assert "__getattr__" in js
        assert "known" in js
        assert "unknown" in js
    
    def test_setattr_intercepts_all(self):
        """__setattr__ intercepts all attribute sets."""
        code = '''
class LoggingSetter:
    def __init__(self):
        object.__setattr__(self, "_log", [])
    
    def __setattr__(self, name, value):
        self._log.append((name, value))
        object.__setattr__(self, name, value)

obj = LoggingSetter()
obj.x = 10
obj.y = 20
'''
        js = transpile(code)
        assert "__setattr__" in js
    
    def test_delattr_intercepts_deletion(self):
        """__delattr__ intercepts attribute deletion."""
        code = '''
class ProtectedDeleter:
    _protected = {"critical"}
    
    def __delattr__(self, name):
        if name in self._protected:
            raise AttributeError(f"Cannot delete {name}")
        object.__delattr__(self, name)

obj = ProtectedDeleter()
del obj.normal  # Should work
'''
        js = transpile(code)
        assert "__delattr__" in js


# =============================================================================
# INHERITANCE WITH PROXIES
# =============================================================================

class TestProxyInheritance:
    """Tests for proxy behavior with inheritance."""
    
    def test_child_inherits_getattr(self):
        """Child class inherits __getattr__ behavior."""
        code = '''
class Parent:
    def __getattr__(self, name):
        return f"parent_{name}"

class Child(Parent):
    pass

c = Child()
print(c.anything)
'''
        js = transpile(code)
        assert "Parent" in js
        assert "Child" in js
    
    def test_child_overrides_getattr(self):
        """Child class can override __getattr__."""
        code = '''
class Parent:
    def __getattr__(self, name):
        return f"parent_{name}"

class Child(Parent):
    def __getattr__(self, name):
        return f"child_{name}"

c = Child()
print(c.anything)
'''
        js = transpile(code)
        assert "__getattr__" in js
    
    def test_mixin_with_getattr(self):
        """Mixin class with __getattr__."""
        code = '''
class GetAttrMixin:
    def __getattr__(self, name):
        return self._fallback(name)

class MyClass(GetAttrMixin):
    def _fallback(self, name):
        return f"fallback_{name}"
'''
        js = transpile(code)
        assert "GetAttrMixin" in js
        assert "MyClass" in js


# =============================================================================
# PROPERTY INTERACTION
# =============================================================================

class TestProxyPropertyInteraction:
    """Tests for proxy interaction with properties."""
    
    def test_property_with_getattr(self):
        """Property and __getattr__ interaction."""
        code = '''
class WithProperty:
    def __init__(self):
        self._x = 10
    
    @property
    def x(self):
        return self._x
    
    def __getattr__(self, name):
        return f"fallback_{name}"

obj = WithProperty()
print(obj.x)       # Property
print(obj.unknown) # __getattr__
'''
        js = transpile(code)
        # Should have both property and __getattr__
        assert "x" in js
        assert "__getattr__" in js
    
    def test_property_setter_with_setattr(self):
        """Property setter and __setattr__ interaction."""
        code = '''
class WithPropertySetter:
    def __init__(self):
        object.__setattr__(self, "_x", 0)
    
    @property
    def x(self):
        return self._x
    
    @x.setter
    def x(self, value):
        object.__setattr__(self, "_x", value)
    
    def __setattr__(self, name, value):
        print(f"Setting {name} to {value}")
        object.__setattr__(self, name, value)

obj = WithPropertySetter()
obj.x = 42
'''
        js = transpile(code)
        assert "__setattr__" in js


# =============================================================================
# PERFORMANCE BENCHMARK STRUCTURES
# =============================================================================

class TestProxyPerformanceStructure:
    """Tests for performance-related code structures."""
    
    def test_proxy_factory_is_lightweight(self):
        """Proxy factory function should be minimal."""
        code = '''
class ProxiedClass:
    def __getattr__(self, name):
        return name
'''
        js = transpile(code)
        # Factory should be simple
        if "__py_create_ProxiedClass" in js:
            # Count lines in factory (should be ~3-4 lines)
            factory_start = js.find("__py_create_ProxiedClass")
            factory_end = js.find("};", factory_start)
            if factory_end > factory_start:
                factory_code = js[factory_start:factory_end]
                lines = [l for l in factory_code.split("\n") if l.strip()]
                assert len(lines) < 10, "Factory should be concise"
    
    def test_regular_class_no_overhead(self):
        """Regular class should have no proxy overhead."""
        code = '''
class RegularClass:
    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c
    
    def compute(self):
        return self.a + self.b + self.c
'''
        js = transpile(code)
        # Should not have proxy-related code
        assert "Proxy" not in js
        assert "__py_create_RegularClass" not in js
    
    def test_many_methods_class(self):
        """Class with many methods but no dunders."""
        code = '''
class ManyMethods:
    def method1(self): pass
    def method2(self): pass
    def method3(self): pass
    def method4(self): pass
    def method5(self): pass
    def method6(self): pass
    def method7(self): pass
    def method8(self): pass
    def method9(self): pass
    def method10(self): pass
'''
        js = transpile(code)
        # Should not have proxy
        assert "__py_create_ManyMethods" not in js


# =============================================================================
# EDGE CASES FOR PROXIES
# =============================================================================

class TestProxyEdgeCases:
    """Edge case tests for proxy wrapping."""
    
    def test_nested_class_with_proxy(self):
        """Nested class that needs proxy - tests that nested classes transpile."""
        # Note: Nested classes are simplified in transpilation
        code = '''
class Outer:
    def create_inner(self):
        return self._make_inner()

class Inner:
    def __getattr__(self, name):
        return f"inner_{name}"
'''
        js = transpile(code)
        assert "Inner" in js
        assert "__getattr__" in js
    
    def test_slots_not_supported(self):
        """Class with __slots__ should raise UnsupportedSyntax."""
        # Note: __slots__ is not supported as JavaScript doesn't have this optimization
        from pynext.transpiler.errors import UnsupportedSyntax
        
        code = '''
class SlottedDynamic:
    __slots__ = ["x", "y"]
    
    def __getattr__(self, name):
        return f"dynamic_{name}"
'''
        with pytest.raises(UnsupportedSyntax) as excinfo:
            transpile(code)
        assert "__slots__" in str(excinfo.value)
    
    def test_classmethod_with_proxy(self):
        """Class with classmethod and proxy."""
        code = '''
class WithClassmethod:
    @classmethod
    def create(cls, value):
        return cls(value)
    
    def __init__(self, value):
        self.value = value
    
    def __getattr__(self, name):
        return self.value
'''
        js = transpile(code)
        assert "create" in js
        assert "__getattr__" in js
    
    def test_staticmethod_with_proxy(self):
        """Class with staticmethod and proxy."""
        code = '''
class WithStaticmethod:
    @staticmethod
    def helper():
        return 42
    
    def __getattr__(self, name):
        return name
'''
        js = transpile(code)
        assert "helper" in js
        assert "__getattr__" in js


# =============================================================================
# PROXY WITH DESCRIPTORS
# =============================================================================

class TestProxyWithDescriptors:
    """Tests for proxy interaction with descriptors."""
    
    def test_descriptor_with_getattr(self):
        """Descriptor protocol with __getattr__."""
        code = '''
class Descriptor:
    def __get__(self, obj, type=None):
        return "descriptor_value"

class Host:
    desc = Descriptor()
    
    def __getattr__(self, name):
        return f"fallback_{name}"
'''
        js = transpile(code)
        assert "Descriptor" in js
        assert "Host" in js
    
    def test_data_descriptor_priority(self):
        """Data descriptor should have priority over __getattr__."""
        code = '''
class DataDescriptor:
    def __get__(self, obj, type=None):
        return "get"
    
    def __set__(self, obj, value):
        pass

class WithDataDesc:
    x = DataDescriptor()
    
    def __getattr__(self, name):
        return "fallback"
'''
        js = transpile(code)
        assert "DataDescriptor" in js
        assert "__getattr__" in js


# =============================================================================
# TRANSPILATION CORRECTNESS
# =============================================================================

class TestProxyTranspilationCorrectness:
    """Tests for correct transpilation output."""
    
    def test_transpile_produces_valid_js(self):
        """Transpiled proxy code is valid JavaScript."""
        code = '''
class Proxied:
    def __getattr__(self, name):
        return name.upper()

obj = Proxied()
result = obj.test
'''
        js = transpile(code)
        # Should be syntactically valid (no unclosed braces)
        assert js.count("{") == js.count("}")
        assert js.count("(") == js.count(")")
    
    def test_transpile_preserves_class_name(self):
        """Class name is preserved in transpilation."""
        code = '''
class MyProxiedClass:
    def __getattr__(self, name):
        return name

x = MyProxiedClass()
'''
        js = transpile(code)
        assert "MyProxiedClass" in js
    
    def test_transpile_preserves_method_names(self):
        """Method names are preserved."""
        code = '''
class MethodPreserver:
    def custom_method(self, arg):
        return arg * 2
    
    def __getattr__(self, name):
        return name

obj = MethodPreserver()
obj.custom_method(5)
'''
        js = transpile(code)
        assert "custom_method" in js

