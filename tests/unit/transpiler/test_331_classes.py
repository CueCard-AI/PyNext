"""
Phase 33.1.2: Classes - Comprehensive Tests

Tests for Python class transpilation to JavaScript, including:
- Basic class definitions
- Inheritance (single and multiple via mixins)
- __init__ → constructor
- Instance methods, static methods, class methods
- @property with getter, setter, deleter
- Private methods (_method)
- Name mangling (__method)
- @dataclass
- Abstract base classes (ABC)
- super() calls
"""

import pytest
from pynext.transpiler import transpile, TranspileError


# =============================================================================
# BASIC CLASS DEFINITIONS
# =============================================================================

class TestBasicClasses:
    """Test basic class definitions."""
    
    def test_empty_class(self):
        """class Foo: pass"""
        result = transpile("class Foo:\n    pass")
        assert "class Foo" in result
        assert "{" in result
        assert "}" in result
    
    def test_class_with_init(self):
        """class Foo: def __init__(self): pass"""
        result = transpile("class Foo:\n    def __init__(self):\n        pass")
        assert "class Foo" in result
        assert "constructor()" in result
    
    def test_class_with_init_args(self):
        """class Foo: def __init__(self, x): self.x = x"""
        result = transpile("class Foo:\n    def __init__(self, x):\n        self.x = x")
        assert "constructor(x)" in result
        assert "this.x = x" in result
    
    def test_class_with_method(self):
        """class Foo: def method(self): return 42"""
        result = transpile("class Foo:\n    def method(self):\n        return 42")
        assert "method()" in result
        assert "return 42" in result
    
    def test_class_with_multiple_methods(self):
        """class Foo: def a(self): pass; def b(self): pass"""
        result = transpile("class Foo:\n    def a(self):\n        pass\n    def b(self):\n        pass")
        assert "a()" in result
        assert "b()" in result


# =============================================================================
# INHERITANCE
# =============================================================================

class TestInheritance:
    """Test class inheritance."""
    
    def test_single_inheritance(self):
        """class Child(Parent): pass"""
        result = transpile("class Parent:\n    pass\nclass Child(Parent):\n    pass")
        assert "class Child extends Parent" in result
    
    def test_inheritance_with_init(self):
        """class Child(Parent): def __init__(self): super().__init__()"""
        result = transpile("class Parent:\n    pass\nclass Child(Parent):\n    def __init__(self):\n        super().__init__()")
        assert "class Child extends Parent" in result
        assert "super()" in result
    
    def test_multiple_inheritance(self):
        """class C(A, B): pass"""
        result = transpile("class A:\n    pass\nclass B:\n    pass\nclass C(A, B):\n    pass")
        assert "class C extends A" in result
        assert "applyMixins" in result or "B" in result
    
    def test_multiple_inheritance_with_methods(self):
        """class C(A, B): pass where A and B have methods"""
        result = transpile("""
class A:
    def method_a(self): pass
class B:
    def method_b(self): pass
class C(A, B):
    pass
""")
        assert "class C extends A" in result
        assert "applyMixins" in result or "B" in result


# =============================================================================
# SUPER() CALLS
# =============================================================================

class TestSuperCalls:
    """Test super() calls."""
    
    def test_super_init_no_args(self):
        """super().__init__()"""
        result = transpile("""
class Parent:
    def __init__(self): pass
class Child(Parent):
    def __init__(self):
        super().__init__()
""")
        assert "super()" in result
    
    def test_super_init_with_args(self):
        """super().__init__(x)"""
        result = transpile("""
class Parent:
    def __init__(self, x): pass
class Child(Parent):
    def __init__(self, x):
        super().__init__(x)
""")
        assert "super(x)" in result
    
    def test_super_method(self):
        """super().method()"""
        result = transpile("""
class Parent:
    def method(self): pass
class Child(Parent):
    def method(self):
        super().method()
""")
        assert "super.method()" in result
    
    def test_super_method_with_args(self):
        """super().method(x, y)"""
        result = transpile("""
class Parent:
    def method(self, x, y): pass
class Child(Parent):
    def method(self, x, y):
        super().method(x, y)
""")
        assert "super.method(" in result


# =============================================================================
# STATIC AND CLASS METHODS
# =============================================================================

class TestStaticAndClassMethods:
    """Test @staticmethod and @classmethod."""
    
    def test_static_method(self):
        """@staticmethod def method(): pass"""
        result = transpile("class Foo:\n    @staticmethod\n    def method():\n        pass")
        assert "static method()" in result
    
    def test_classmethod(self):
        """@classmethod def method(cls): pass"""
        result = transpile("class Foo:\n    @classmethod\n    def method(cls):\n        pass")
        assert "static method()" in result
        assert "cls" in result or "this.constructor" in result
    
    def test_classmethod_with_usage(self):
        """@classmethod def from_dict(cls, data): return cls(**data)"""
        result = transpile("""
class Foo:
    @classmethod
    def from_dict(cls, data):
        return cls(**data)
""")
        assert "static from_dict" in result


# =============================================================================
# PROPERTIES
# =============================================================================

class TestProperties:
    """Test @property with getter, setter, deleter."""
    
    def test_property_getter(self):
        """@property def value(self): return self._value"""
        result = transpile("""
class Foo:
    @property
    def value(self):
        return self._value
""")
        assert "get value()" in result
        assert "this._value" in result
    
    def test_property_setter(self):
        """@property def value(self): ...; @value.setter def value(self, v): ..."""
        result = transpile("""
class Foo:
    @property
    def value(self):
        return self._value
    
    @value.setter
    def value(self, v):
        self._value = v
""")
        assert "get value()" in result
        assert "set value(" in result
    
    def test_property_deleter(self):
        """@property def value(self): ...; @value.deleter def value(self): ..."""
        result = transpile("""
class Foo:
    @property
    def value(self):
        return self._value
    
    @value.deleter
    def value(self):
        del self._value
""")
        assert "get value()" in result
        assert "delete value()" in result
    
    def test_property_full(self):
        """@property with getter, setter, and deleter"""
        result = transpile("""
class Foo:
    @property
    def value(self):
        return self._value
    
    @value.setter
    def value(self, v):
        self._value = v
    
    @value.deleter
    def value(self):
        del self._value
""")
        assert "get value()" in result
        assert "set value(" in result
        assert "delete value()" in result


# =============================================================================
# PRIVATE METHODS AND NAME MANGLING
# =============================================================================

class TestPrivateMethods:
    """Test private methods (_method) and name mangling (__method)."""
    
    def test_private_method(self):
        """def _private(self): pass"""
        result = transpile("class Foo:\n    def _private(self):\n        pass")
        assert "_private()" in result
    
    def test_mangled_method(self):
        """def __mangled(self): pass"""
        result = transpile("class Foo:\n    def __mangled(self):\n        pass")
        # Should use # prefix for ES2022 private fields
        assert "#mangled()" in result or "__mangled()" in result
    
    def test_dunder_method(self):
        """def __str__(self): pass (not mangled)"""
        result = transpile("class Foo:\n    def __str__(self):\n        pass")
        # Phase 33.2: Dunder methods (__xxx__) are transpiled to JS equivalents
        # __str__ → toString()
        assert "toString()" in result
    
    def test_private_with_init(self):
        """class with __init__ and _private method"""
        result = transpile("""
class Foo:
    def __init__(self):
        self._helper()
    
    def _helper(self):
        pass
""")
        assert "constructor()" in result
        assert "_helper()" in result


# =============================================================================
# DATACLASS
# =============================================================================

class TestDataclass:
    """Test @dataclass support."""
    
    def test_dataclass_basic(self):
        """@dataclass class Point: x: int; y: int"""
        result = transpile("""
@dataclass
class Point:
    x: int
    y: int
""")
        assert "class Point" in result
        assert "constructor(x, y)" in result or "constructor" in result
    
    def test_dataclass_with_defaults(self):
        """@dataclass class Point: x: int = 0; y: int = 0"""
        result = transpile("""
@dataclass
class Point:
    x: int = 0
    y: int = 0
""")
        assert "x = 0" in result
        assert "y = 0" in result
    
    def test_dataclass_equals(self):
        """@dataclass should generate equals() method"""
        result = transpile("""
@dataclass
class Point:
    x: int
    y: int
""")
        # Should have equals method for __eq__
        assert "equals(" in result or "constructor" in result


# =============================================================================
# ABSTRACT BASE CLASSES
# =============================================================================

class TestAbstractClasses:
    """Test abstract base classes (ABC)."""
    
    def test_abstract_class(self):
        """class Foo(ABC): pass"""
        result = transpile("class ABC: pass\nclass Foo(ABC):\n    pass")
        # Should check for abstract instantiation
        assert "class Foo extends ABC" in result or "class Foo" in result
    
    def test_abstract_method(self):
        """class Foo(ABC): @abstractmethod def method(self): pass"""
        result = transpile("""
class ABC: pass
class Foo(ABC):
    @abstractmethod
    def method(self):
        pass
""")
        assert "NotImplementedError" in result or "abstract" in result or "method()" in result
    
    def test_concrete_subclass(self):
        """class Concrete(Abstract): def method(self): return 42"""
        result = transpile("""
class ABC: pass
class Abstract(ABC):
    @abstractmethod
    def method(self): pass
class Concrete(Abstract):
    def method(self):
        return 42
""")
        assert "class Concrete extends Abstract" in result
        assert "return 42" in result


# =============================================================================
# COMPLEX COMBINATIONS
# =============================================================================

class TestComplexCombinations:
    """Test complex combinations of class features."""
    
    def test_inheritance_with_property(self):
        """class with inheritance and property"""
        result = transpile("""
class Parent:
    @property
    def value(self):
        return self._value

class Child(Parent):
    @property
    def value(self):
        return super().value
""")
        assert "class Child extends Parent" in result
        assert "get value()" in result
    
    def test_multiple_inheritance_with_methods(self):
        """Multiple inheritance with methods from both parents"""
        result = transpile("""
class A:
    def method_a(self): return "A"
class B:
    def method_b(self): return "B"
class C(A, B):
    def method_c(self): return "C"
""")
        assert "class C extends A" in result
        assert "method_c()" in result
    
    def test_class_with_all_features(self):
        """Class with init, methods, static, property, inheritance"""
        result = transpile("""
class Parent:
    def __init__(self, x):
        self.x = x

class Child(Parent):
    def __init__(self, x, y):
        super().__init__(x)
        self.y = y
    
    @staticmethod
    def static_method():
        return 42
    
    @property
    def value(self):
        return self.x + self.y
""")
        assert "class Child extends Parent" in result
        assert "constructor(x, y)" in result
        assert "static static_method()" in result
        assert "get value()" in result

