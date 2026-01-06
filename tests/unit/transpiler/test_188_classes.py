"""
Phase 18.8: Class Transpilation Tests

Comprehensive tests for Python class → JavaScript class transpilation.
Covers ClassDef, MethodDef, PropertyDef, inheritance, decorators.

Tests: 120
"""

import pytest
from pynext.transpiler import parse, emit, transpile
from pynext.transpiler.nodes import (
    ClassDef, MethodDef, PropertyDef, Program, Return, Constant,
    Assignment, Name, BinOp, If, Call, Attribute,
)
from pynext.transpiler.errors import UnsupportedSyntax


# =============================================================================
# CLASS PARSING TESTS
# =============================================================================

class TestClassParsing:
    """Tests for parsing Python classes into IR."""
    
    def test_simple_class(self):
        """Parse a simple class with no methods."""
        ir = parse("class Empty: pass")
        assert isinstance(ir, Program)
        assert len(ir.body) == 1
        cls = ir.body[0]
        assert isinstance(cls, ClassDef)
        assert cls.name == "Empty"
        assert cls.bases == ()
    
    def test_class_with_init(self):
        """Parse class with __init__ method."""
        code = '''
class Todo:
    def __init__(self, title):
        self.title = title
'''
        ir = parse(code)
        cls = ir.body[0]
        assert isinstance(cls, ClassDef)
        assert cls.name == "Todo"
        assert len(cls.body) >= 1
        
        init = cls.body[0]
        assert isinstance(init, MethodDef)
        assert init.name == "constructor"  # __init__ → constructor
        assert "title" in init.args
        assert "self" not in init.args  # self is stripped
    
    def test_class_with_method(self):
        """Parse class with instance method."""
        code = '''
class Counter:
    def increment(self):
        self.count = self.count + 1
'''
        ir = parse(code)
        cls = ir.body[0]
        method = cls.body[0]
        assert isinstance(method, MethodDef)
        assert method.name == "increment"
        assert method.args == ()  # self is stripped
        assert method.is_static is False
    
    def test_class_with_staticmethod(self):
        """Parse class with @staticmethod."""
        code = '''
class Utils:
    @staticmethod
    def validate(x):
        return x > 0
'''
        ir = parse(code)
        cls = ir.body[0]
        method = cls.body[0]
        assert isinstance(method, MethodDef)
        assert method.name == "validate"
        assert method.is_static is True
        assert "x" in method.args
    
    def test_class_with_property(self):
        """Parse class with @property."""
        code = '''
class Todo:
    @property
    def status(self):
        return "Done" if self.done else "Pending"
'''
        ir = parse(code)
        cls = ir.body[0]
        prop = cls.body[0]
        assert isinstance(prop, PropertyDef)
        assert prop.name == "status"
    
    def test_class_single_inheritance(self):
        """Parse class with single inheritance."""
        code = '''
class Child(Parent):
    def __init__(self):
        super().__init__()
'''
        ir = parse(code)
        cls = ir.body[0]
        assert cls.name == "Child"
        assert cls.bases == ("Parent",)
    
    def test_class_multiple_inheritance_supported(self):
        """Multiple inheritance is now supported via mixins (Phase 33.1)."""
        code = "class Child(Parent1, Parent2): pass"
        # Phase 33.1: Multiple inheritance is supported via mixin pattern
        ir = parse(code)
        assert ir is not None
        js = transpile(code)
        assert "class Child extends Parent1" in js
    
    def test_class_with_metaclass_error(self):
        """Metaclass raises UnsupportedSyntax."""
        code = "class Singleton(metaclass=Meta): pass"
        with pytest.raises(UnsupportedSyntax) as exc:
            parse(code)
        assert "Metaclass" in str(exc.value)
    
    def test_class_with_classmethod(self):
        """@classmethod is supported and transpiles to static method with cls binding."""
        code = '''
class Factory:
    @classmethod
    def create(cls):
        return cls()
'''
        ir = parse(code)
        assert len(ir.body) == 1
        class_def = ir.body[0]
        assert len(class_def.body) == 1
        method = class_def.body[0]
        assert method.name == "create"
        assert method.is_classmethod == True
        assert method.is_static == False  # is_classmethod is separate from is_static
    
    def test_class_with_slots_error(self):
        """__slots__ raises UnsupportedSyntax."""
        code = '''
class Fast:
    __slots__ = ['x', 'y']
'''
        with pytest.raises(UnsupportedSyntax) as exc:
            parse(code)
        assert "__slots__" in str(exc.value)
    
    def test_class_with_async_method(self):
        """Parse class with async method."""
        code = '''
class DataLoader:
    async def fetch(self, url):
        return await fetch(url)
'''
        ir = parse(code)
        cls = ir.body[0]
        method = cls.body[0]
        assert isinstance(method, MethodDef)
        assert method.is_async is True
    
    def test_class_with_multiple_methods(self):
        """Parse class with multiple methods."""
        code = '''
class Todo:
    def __init__(self, title):
        self.title = title
    
    def toggle(self):
        self.done = not self.done
    
    def delete(self):
        pass
'''
        ir = parse(code)
        cls = ir.body[0]
        assert len(cls.body) == 3
    
    def test_class_skips_docstring(self):
        """Class docstrings are skipped."""
        code = '''
class Documented:
    """This is a docstring."""
    def method(self):
        pass
'''
        ir = parse(code)
        cls = ir.body[0]
        # Docstring should be skipped, only method remains
        assert len(cls.body) == 1
        assert isinstance(cls.body[0], MethodDef)
    
    def test_class_method_with_defaults(self):
        """Parse method with default parameter values."""
        code = '''
class Todo:
    def __init__(self, title, done=False):
        self.title = title
        self.done = done
'''
        ir = parse(code)
        cls = ir.body[0]
        init = cls.body[0]
        assert len(init.args) == 2
        assert len(init.defaults) == 1  # done=False
    
    def test_class_method_args_only(self):
        """Method args without defaults."""
        code = '''
class Math:
    def add(self, a, b):
        return a + b
'''
        ir = parse(code)
        cls = ir.body[0]
        method = cls.body[0]
        assert method.args == ("a", "b")
        assert method.defaults == ()


# =============================================================================
# CLASS EMITTING TESTS
# =============================================================================

class TestClassEmitting:
    """Tests for emitting JavaScript classes."""
    
    def test_emit_empty_class(self):
        """Emit empty class."""
        ir = parse("class Empty: pass")
        js = emit(ir)
        assert "class Empty {" in js
        assert "}" in js
    
    def test_emit_class_with_constructor(self):
        """Emit class with constructor."""
        code = '''
class Todo:
    def __init__(self, title):
        self.title = title
'''
        js = transpile(code)
        assert "class Todo {" in js
        assert "constructor(title)" in js
        assert "this.title = title" in js
    
    def test_emit_class_with_method(self):
        """Emit class with instance method."""
        code = '''
class Counter:
    def increment(self):
        self.count = self.count + 1
'''
        js = transpile(code)
        assert "increment() {" in js
        assert "this.count" in js
    
    def test_emit_static_method(self):
        """Emit @staticmethod as static."""
        code = '''
class Utils:
    @staticmethod
    def validate(x):
        return x > 0
'''
        js = transpile(code)
        assert "static validate(x)" in js
    
    def test_emit_property(self):
        """Emit @property as getter."""
        code = '''
class Todo:
    @property
    def status(self):
        return "Done"
'''
        js = transpile(code)
        assert "get status()" in js
    
    def test_emit_inheritance(self):
        """Emit class with extends."""
        code = '''
class Child(Parent):
    def __init__(self):
        pass
'''
        js = transpile(code)
        assert "class Child extends Parent {" in js
    
    def test_emit_async_method(self):
        """Emit async method."""
        code = '''
class Loader:
    async def fetch(self, url):
        return await fetch(url)
'''
        js = transpile(code)
        assert "async fetch(url)" in js
    
    def test_emit_method_with_defaults(self):
        """Emit method with default parameters."""
        code = '''
class Todo:
    def __init__(self, title, done=False):
        self.title = title
'''
        js = transpile(code)
        assert "done = false" in js
    
    def test_emit_self_to_this(self):
        """self is replaced with this."""
        code = '''
class Counter:
    def increment(self):
        self.count = self.count + 1
'''
        js = transpile(code)
        assert "this.count" in js
        assert "self.count" not in js
    
    def test_emit_super_call(self):
        """super().__init__() emits correctly."""
        code = '''
class Child(Parent):
    def __init__(self):
        super().__init__()
'''
        js = transpile(code)
        # super() is transpiled - may be super() or super_() depending on context
        assert "super" in js


# =============================================================================
# FULL CLASS TRANSPILATION TESTS
# =============================================================================

class TestFullClassTranspilation:
    """Full end-to-end class transpilation tests."""
    
    def test_complete_todo_class(self):
        """Full Todo class example from plan."""
        code = '''
class Todo:
    def __init__(self, title, done=False):
        self.title = title
        self.done = done
    
    def toggle(self):
        self.done = not self.done
'''
        js = transpile(code)
        
        # Class structure
        assert "class Todo {" in js
        
        # Constructor
        assert "constructor(title, done = false)" in js
        assert "this.title = title" in js
        assert "this.done = done" in js
        
        # Method
        assert "toggle() {" in js
        # not is transpiled to !__py.bool() or just !
        assert "this.done" in js
        assert "!" in js  # Negation is present
    
    def test_class_with_property_and_static(self):
        """Class with both property and staticmethod."""
        code = '''
class Todo:
    @property
    def status(self):
        return "Done"
    
    @staticmethod
    def validate(title):
        return len(title) > 0
'''
        js = transpile(code)
        assert "get status()" in js
        assert "static validate(title)" in js
    
    def test_nested_class_body(self):
        """Class with complex method bodies."""
        code = '''
class Calculator:
    def compute(self, x, y):
        if x > y:
            return x - y
        else:
            return y - x
'''
        js = transpile(code)
        assert "compute(x, y)" in js
        assert "if" in js
        assert "return" in js
    
    def test_class_with_list_operations(self):
        """Class using list operations."""
        code = '''
class TodoList:
    def __init__(self):
        self.items = []
    
    def add(self, item):
        self.items.append(item)
'''
        js = transpile(code)
        assert "this.items = []" in js
        assert "this.items" in js
    
    def test_class_with_dict_operations(self):
        """Class using dict operations."""
        code = '''
class Config:
    def __init__(self):
        self.data = {}
    
    def set(self, key, value):
        self.data[key] = value
'''
        js = transpile(code)
        assert "this.data = {}" in js


# =============================================================================
# METHOD VARIATION TESTS
# =============================================================================

class TestMethodVariations:
    """Tests for various method signatures."""
    
    def test_method_no_params(self):
        """Method with no parameters."""
        code = '''
class Counter:
    def reset(self):
        self.count = 0
'''
        js = transpile(code)
        assert "reset() {" in js
    
    def test_method_multiple_params(self):
        """Method with multiple parameters."""
        code = '''
class Math:
    def add(self, a, b, c):
        return a + b + c
'''
        js = transpile(code)
        assert "add(a, b, c)" in js
    
    def test_method_all_defaults(self):
        """Method where all params have defaults."""
        code = '''
class Builder:
    def build(self, x=1, y=2, z=3):
        return x + y + z
'''
        js = transpile(code)
        assert "x = 1" in js
        assert "y = 2" in js
        assert "z = 3" in js
    
    def test_method_mixed_defaults(self):
        """Method with mix of required and default params."""
        code = '''
class Todo:
    def update(self, title, done=False, priority=0):
        self.title = title
'''
        js = transpile(code)
        assert "update(title, done = false, priority = 0)" in js
    
    def test_static_method_multiple_params(self):
        """Static method with multiple parameters."""
        code = '''
class Utils:
    @staticmethod
    def clamp(value, min_val, max_val):
        return max(min_val, min(max_val, value))
'''
        js = transpile(code)
        assert "static clamp(value, min_val, max_val)" in js


# =============================================================================
# PROPERTY TESTS
# =============================================================================

class TestPropertyTranspilation:
    """Tests for @property transpilation."""
    
    def test_simple_property(self):
        """Simple property getter."""
        code = '''
class Box:
    @property
    def width(self):
        return self._width
'''
        js = transpile(code)
        assert "get width()" in js
        assert "this._width" in js
    
    def test_property_with_computation(self):
        """Property with computed value."""
        code = '''
class Rectangle:
    @property
    def area(self):
        return self.width * self.height
'''
        js = transpile(code)
        assert "get area()" in js
    
    def test_property_with_condition(self):
        """Property with conditional logic."""
        code = '''
class Todo:
    @property
    def status(self):
        if self.done:
            return "Done"
        return "Pending"
'''
        js = transpile(code)
        assert "get status()" in js
        assert "if" in js
    
    def test_multiple_properties(self):
        """Class with multiple properties."""
        code = '''
class Person:
    @property
    def full_name(self):
        return self.first + " " + self.last
    
    @property
    def age(self):
        return self._age
'''
        js = transpile(code)
        assert "get full_name()" in js
        assert "get age()" in js


# =============================================================================
# INHERITANCE TESTS  
# =============================================================================

class TestInheritance:
    """Tests for class inheritance."""
    
    def test_simple_inheritance(self):
        """Simple single inheritance."""
        code = "class Dog(Animal): pass"
        js = transpile(code)
        assert "class Dog extends Animal" in js
    
    def test_inheritance_with_super_init(self):
        """Inheritance with super().__init__()."""
        code = '''
class Dog(Animal):
    def __init__(self, name):
        super().__init__(name)
        self.breed = "Unknown"
'''
        js = transpile(code)
        assert "extends Animal" in js
        assert "super" in js  # super() call is present
    
    def test_inheritance_override_method(self):
        """Override parent method."""
        code = '''
class Dog(Animal):
    def speak(self):
        return "Woof!"
'''
        js = transpile(code)
        assert "speak()" in js
    
    def test_no_inheritance(self):
        """Class without inheritance."""
        code = "class Standalone: pass"
        js = transpile(code)
        assert "class Standalone {" in js
        assert "extends" not in js


# =============================================================================
# IR NODE TESTS
# =============================================================================

class TestClassIRNodes:
    """Tests for ClassDef, MethodDef, PropertyDef nodes."""
    
    def test_classdef_node_creation(self):
        """Create ClassDef node directly."""
        cls = ClassDef(
            name="Test",
            bases=("Parent",),
            body=(MethodDef(name="method", args=(), body=()),),
        )
        assert cls.name == "Test"
        assert cls.bases == ("Parent",)
        assert len(cls.body) == 1
    
    def test_methoddef_node_creation(self):
        """Create MethodDef node directly."""
        method = MethodDef(
            name="calculate",
            args=("x", "y"),
            defaults=(Constant(0),),
            body=(Return(value=Constant(42)),),
            is_static=False,
            is_async=True,
        )
        assert method.name == "calculate"
        assert method.args == ("x", "y")
        assert method.is_async is True
    
    def test_propertydef_node_creation(self):
        """Create PropertyDef node directly."""
        prop = PropertyDef(
            name="value",
            body=(Return(value=Name(id="self._value")),),
        )
        assert prop.name == "value"
        assert len(prop.body) == 1
    
    def test_classdef_emit(self):
        """Emit ClassDef node directly."""
        method = MethodDef(
            name="test",
            args=(),
            body=(Return(value=Constant(42)),),
        )
        cls = ClassDef(
            name="TestClass",
            body=(method,),
        )
        prog = Program(body=(cls,))
        js = emit(prog)
        assert "class TestClass" in js
    
    def test_nested_class_structure(self):
        """Complex nested class structure."""
        cls = ClassDef(
            name="Complex",
            bases=("Base",),
            body=(
                MethodDef(name="constructor", args=("x",), body=()),
                MethodDef(name="process", args=("data",), body=()),
                PropertyDef(name="result", body=()),
            ),
        )
        assert len(cls.body) == 3


# =============================================================================
# EDGE CASES
# =============================================================================

class TestClassEdgeCases:
    """Edge cases in class transpilation."""
    
    def test_class_with_pass_only(self):
        """Class with only pass statement."""
        code = "class Empty: pass"
        js = transpile(code)
        assert "class Empty" in js
    
    def test_class_name_with_underscore(self):
        """Class name with underscores."""
        code = "class My_Class: pass"
        js = transpile(code)
        assert "class My_Class" in js
    
    def test_class_name_camelcase(self):
        """CamelCase class name."""
        code = "class MyClassName: pass"
        js = transpile(code)
        assert "class MyClassName" in js
    
    def test_method_name_with_underscore(self):
        """Method name with underscores."""
        code = '''
class Test:
    def my_method(self):
        pass
'''
        js = transpile(code)
        assert "my_method()" in js
    
    def test_private_method(self):
        """Private method (underscore prefix)."""
        code = '''
class Test:
    def _private(self):
        pass
'''
        js = transpile(code)
        assert "_private()" in js
    
    def test_dunder_method_other_than_init(self):
        """Dunder method other than __init__."""
        code = '''
class Test:
    def __str__(self):
        return "Test"
'''
        js = transpile(code)
        # Phase 33.2: __str__ → toString()
        assert "toString()" in js
    
    def test_class_with_class_variable_skipped(self):
        """Class variables are skipped (for now)."""
        code = '''
class Config:
    VERSION = "1.0"
    def method(self):
        pass
'''
        ir = parse(code)
        cls = ir.body[0]
        # Only method should be in body, class var is skipped
        assert len([x for x in cls.body if isinstance(x, MethodDef)]) == 1
    
    def test_empty_method_body(self):
        """Method with empty body (pass)."""
        code = '''
class Test:
    def empty(self):
        pass
'''
        js = transpile(code)
        assert "empty()" in js


# =============================================================================
# UNICODE TESTS
# =============================================================================

class TestClassUnicode:
    """Tests for unicode in class names and identifiers."""
    
    def test_unicode_class_name(self):
        """Unicode class name."""
        code = "class 咖啡: pass"
        js = transpile(code)
        assert "class 咖啡" in js
    
    def test_unicode_method_name(self):
        """Unicode method name."""
        code = '''
class Test:
    def метод(self):
        pass
'''
        js = transpile(code)
        assert "метод()" in js
    
    def test_unicode_param_name(self):
        """Unicode parameter name."""
        code = '''
class Test:
    def method(self, 参数):
        return 参数
'''
        js = transpile(code)
        assert "参数" in js
    
    def test_ascii_identifiers(self):
        """Standard ASCII identifiers still work."""
        code = '''
class NormalClass:
    def normal_method(self, normal_param):
        return normal_param
'''
        js = transpile(code)
        assert "NormalClass" in js
        assert "normal_method" in js
        assert "normal_param" in js

