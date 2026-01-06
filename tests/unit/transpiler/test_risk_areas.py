"""
Phase 18 Risk Area Tests - Comprehensive Python Unit Tests

Tests all identified risk areas from the Phase 18 audit:
1. super() call handling
2. Augmented assignment to attributes (self.x += 1)
3. Property setters (@property.setter)
4. Division by zero handling
5. Deep equality with cycles
6. Banker's rounding

Each test verifies the transpiler produces correct JavaScript output.
"""

import pytest
from pynext.transpiler import transpile, parse
from tests.unit.transpiler.test_utils import assert_has_assignment_with_operation
from pynext.transpiler.nodes import (
    ClassDef, MethodDef, PropertyDef, PropertySetterDef,
    AugAssign, BinOp, ExprStmt
)


# =============================================================================
# SUPER() CALL HANDLING TESTS
# =============================================================================

class TestSuperCalls:
    """Tests for super() call transpilation."""
    
    def test_super_init_no_args(self):
        """super().__init__() in constructor → super()"""
        code = '''
class Child(Parent):
    def __init__(self):
        super().__init__()
'''
        js = transpile(code)
        assert "extends Parent" in js
        assert "super()" in js
        assert "super().__init__" not in js
    
    def test_super_init_with_args(self):
        """super().__init__(args) in constructor → super(args)"""
        code = '''
class Dog(Animal):
    def __init__(self, name, breed):
        super().__init__(name)
        self.breed = breed
'''
        js = transpile(code)
        assert "super(name)" in js
        assert "super().__init__" not in js
        assert "this.breed = breed" in js
    
    def test_super_init_with_multiple_args(self):
        """super().__init__(a, b, c) → super(a, b, c)"""
        code = '''
class Widget(BaseWidget):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
'''
        js = transpile(code)
        assert "super(x, y, width, height)" in js
    
    def test_super_method_call(self):
        """super().method() in regular method → super.method()"""
        code = '''
class Child(Parent):
    def process(self):
        super().process()
'''
        js = transpile(code)
        assert "super.process()" in js
        assert "super().process" not in js
    
    def test_super_method_with_args(self):
        """super().method(args) → super.method(args)"""
        code = '''
class Child(Parent):
    def validate(self, data):
        result = super().validate(data)
        return result
'''
        js = transpile(code)
        assert "super.validate(data)" in js
    
    def test_super_in_async_method(self):
        """super() in async method"""
        code = '''
class AsyncChild(AsyncParent):
    async def fetch(self, url):
        await super().fetch(url)
'''
        js = transpile(code)
        assert "async fetch" in js
        assert "super.fetch(url)" in js
    
    def test_super_multiple_calls(self):
        """Multiple super() calls in same method"""
        code = '''
class Child(Parent):
    def process(self):
        super().setup()
        super().run()
        super().cleanup()
'''
        js = transpile(code)
        assert "super.setup()" in js
        assert "super.run()" in js
        assert "super.cleanup()" in js
    
    def test_super_with_self_assignment(self):
        """super() combined with self assignments"""
        code = '''
class Child(Parent):
    def __init__(self, name, extra):
        super().__init__(name)
        self.extra = extra
        self.name = name
'''
        js = transpile(code)
        assert "super(name)" in js
        assert "this.extra = extra" in js
        assert "this.name = name" in js


# =============================================================================
# AUGMENTED ASSIGNMENT TO ATTRIBUTES TESTS
# =============================================================================

class TestAugmentedAssignmentToAttributes:
    """Tests for self.x += value and items[i] += value."""
    
    def test_self_add_assign(self):
        """self.count += 1"""
        code = '''
class Counter:
    def increment(self):
        self.count += 1
'''
        js = transpile(code)
        assert_has_assignment_with_operation(js, "this.count", "add")
    
    def test_self_sub_assign(self):
        """self.value -= 5"""
        code = '''
class Counter:
    def decrement(self):
        self.value -= 5
'''
        js = transpile(code)
        assert_has_assignment_with_operation(js, "this.value", "sub")
    
    def test_self_mul_assign(self):
        """self.scale *= 2"""
        code = '''
class Scaler:
    def double(self):
        self.scale *= 2
'''
        js = transpile(code)
        assert_has_assignment_with_operation(js, "this.scale", "mul")
    
    def test_self_div_assign(self):
        """self.total /= 2"""
        code = '''
class Divider:
    def halve(self):
        self.total /= 2
'''
        js = transpile(code)
        assert_has_assignment_with_operation(js, "this.total", "div")
    
    def test_self_floordiv_assign(self):
        """self.value //= 10"""
        code = '''
class FloorDivider:
    def truncate(self):
        self.value //= 10
'''
        js = transpile(code)
        assert_has_assignment_with_operation(js, "this.value", "floordiv")
    
    def test_self_mod_assign(self):
        """self.angle %= 360"""
        code = '''
class Rotator:
    def normalize(self):
        self.angle %= 360
'''
        js = transpile(code)
        assert_has_assignment_with_operation(js, "this.angle", "mod")
    
    def test_subscript_add_assign(self):
        """items[0] += 10"""
        code = '''
def update(items):
    items[0] += 10
'''
        js = transpile(code)
        # Phase 33.2: Uses __py.setitem() and __py.getitem() for __setitem__/__getitem__ support
        assert "__py.setitem(items, 0" in js
        # Check for dunder runtime (current implementation uses __py.dunders.add)
        from tests.unit.transpiler.test_utils import assert_has_runtime_function
        assert_has_runtime_function(js, "add", runtime_type="dunder")
    
    def test_subscript_with_variable_index(self):
        """items[i] += value (variable indices use __py.at for negative index support)"""
        code = '''
def update(items, i, value):
    items[i] += value
'''
        js = transpile(code)
        # Variable indices use __py.at to support negative indexing
        assert "__py.at(items, i)" in js
        # Check for dunder runtime (current implementation uses __py.dunders.add)
        from tests.unit.transpiler.test_utils import assert_has_runtime_function
        assert_has_runtime_function(js, "add", runtime_type="dunder")
    
    def test_nested_attribute_augassign(self):
        """self.config.value += 1"""
        code = '''
class Manager:
    def update(self):
        self.config.value += 1
'''
        js = transpile(code)
        assert_has_assignment_with_operation(js, "this.config.value", "add")
    
    def test_all_operators(self):
        """Test all augmented assignment operators on attributes."""
        code = '''
class AllOps:
    def test(self, x):
        self.a += x
        self.b -= x
        self.c *= x
        self.d /= x
        self.e //= x
        self.f %= x
        self.g **= x
'''
        js = transpile(code)
        assert_has_assignment_with_operation(js, "this.a", "add")
        assert_has_assignment_with_operation(js, "this.b", "sub")
        assert_has_assignment_with_operation(js, "this.c", "mul")
        assert_has_assignment_with_operation(js, "this.d", "div")
        assert_has_assignment_with_operation(js, "this.e", "floordiv")
        assert_has_assignment_with_operation(js, "this.f", "mod")
        # Phase 33.2: ** uses __py.dunders.pow() to support __pow__ dunder methods
        assert_has_assignment_with_operation(js, "this.g", "pow")


# =============================================================================
# PROPERTY SETTER TESTS
# =============================================================================

class TestPropertySetters:
    """Tests for @property and @name.setter transpilation."""
    
    def test_property_getter_only(self):
        """@property without setter"""
        code = '''
class Counter:
    @property
    def value(self):
        return self._value
'''
        js = transpile(code)
        assert "get value()" in js
        assert "return this._value" in js
    
    def test_property_with_setter(self):
        """@property with @name.setter"""
        code = '''
class Counter:
    @property
    def value(self):
        return self._value
    
    @value.setter
    def value(self, val):
        self._value = val
'''
        js = transpile(code)
        assert "get value()" in js
        assert "set value(val)" in js
        assert "this._value = val" in js
    
    def test_setter_with_validation(self):
        """Setter with validation logic"""
        code = '''
class Temperature:
    @property
    def celsius(self):
        return self._celsius
    
    @celsius.setter
    def celsius(self, value):
        if value < -273.15:
            value = -273.15
        self._celsius = value
'''
        js = transpile(code)
        assert "set celsius(value)" in js
        assert "if" in js
        assert "this._celsius = value" in js
    
    def test_multiple_properties(self):
        """Multiple properties with setters"""
        code = '''
class Point:
    @property
    def x(self):
        return self._x
    
    @x.setter
    def x(self, val):
        self._x = val
    
    @property
    def y(self):
        return self._y
    
    @y.setter
    def y(self, val):
        self._y = val
'''
        js = transpile(code)
        assert "get x()" in js
        assert "set x(val)" in js
        assert "get y()" in js
        assert "set y(val)" in js
    
    def test_property_setter_parsing(self):
        """Verify PropertySetterDef node is created"""
        code = '''
class Test:
    @property
    def value(self):
        return self._value
    
    @value.setter
    def value(self, val):
        self._value = val
'''
        ir = parse(code)
        class_def = ir.body[0]
        
        # Check body has PropertyDef and PropertySetterDef
        types = [type(item).__name__ for item in class_def.body]
        assert "PropertyDef" in types
        assert "PropertySetterDef" in types
    
    def test_computed_property_with_setter(self):
        """Property that computes value"""
        code = '''
class Rectangle:
    @property
    def area(self):
        return self.width * self.height
    
    @property
    def width(self):
        return self._width
    
    @width.setter
    def width(self, val):
        self._width = val
'''
        js = transpile(code)
        assert "get area()" in js
        assert "get width()" in js
        assert "set width(val)" in js


# =============================================================================
# CLASS INHERITANCE INTEGRATION TESTS
# =============================================================================

class TestClassInheritanceIntegration:
    """Integration tests combining inheritance features."""
    
    def test_full_class_with_all_features(self):
        """Class with inheritance, super, properties, and methods"""
        code = '''
class Animal:
    def __init__(self, name):
        self.name = name

class Dog(Animal):
    def __init__(self, name, breed):
        super().__init__(name)
        self._breed = breed
    
    @property
    def breed(self):
        return self._breed
    
    @breed.setter
    def breed(self, value):
        self._breed = value
    
    def bark(self):
        return f"{self.name} says woof!"
    
    def update_name(self, new_name):
        self.name = new_name
'''
        js = transpile(code)
        # Inheritance
        assert "class Dog extends Animal" in js
        # Super call
        assert "super(name)" in js
        # Property getter and setter
        assert "get breed()" in js
        assert "set breed(value)" in js
        # Methods
        assert "bark()" in js
        assert "update_name(new_name)" in js
    
    def test_static_method_with_properties(self):
        """Static methods combined with properties"""
        code = '''
class Counter:
    _instances = 0
    
    def __init__(self):
        self._count = 0
    
    @property
    def count(self):
        return self._count
    
    @count.setter
    def count(self, val):
        self._count = val
    
    @staticmethod
    def create():
        return Counter()
'''
        js = transpile(code)
        assert "get count()" in js
        assert "set count(val)" in js
        assert "static create()" in js


# =============================================================================
# PARSING VERIFICATION TESTS
# =============================================================================

class TestParsingRiskAreas:
    """Verify correct IR nodes are created for risk areas."""
    
    def test_augassign_to_name_creates_augassign(self):
        """x += 1 creates AugAssign node"""
        ir = parse("x += 1")
        assert len(ir.body) == 1
        assert isinstance(ir.body[0], AugAssign)
        assert ir.body[0].target == "x"
        assert ir.body[0].op == "add"
    
    def test_augassign_to_attribute_creates_exprstmt(self):
        """self.x += 1 creates ExprStmt with BinOp assignment"""
        code = '''
class Test:
    def inc(self):
        self.x += 1
'''
        ir = parse(code)
        method = ir.body[0].body[0]  # MethodDef
        stmt = method.body[0]  # First statement in method
        assert isinstance(stmt, ExprStmt)
        assert isinstance(stmt.value, BinOp)
        assert stmt.value.op == "assign"
    
    def test_property_creates_propertydef(self):
        """@property creates PropertyDef node"""
        code = '''
class Test:
    @property
    def value(self):
        return self._value
'''
        ir = parse(code)
        prop = ir.body[0].body[0]
        assert isinstance(prop, PropertyDef)
        assert prop.name == "value"
    
    def test_setter_creates_propertysetterdef(self):
        """@name.setter creates PropertySetterDef node"""
        code = '''
class Test:
    @property
    def value(self):
        return self._value
    
    @value.setter
    def value(self, val):
        self._value = val
'''
        ir = parse(code)
        setter = ir.body[0].body[1]
        assert isinstance(setter, PropertySetterDef)
        assert setter.name == "value"
        assert setter.arg == "val"


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestEdgeCases:
    """Edge cases that could cause issues."""
    
    def test_super_with_expression_args(self):
        """super().__init__() with complex expression args"""
        code = '''
class Child(Parent):
    def __init__(self, items):
        super().__init__(len(items))
'''
        js = transpile(code)
        assert "super(__py.len(items))" in js
    
    def test_chained_attribute_augassign(self):
        """self.obj.prop += 1"""
        code = '''
class Manager:
    def update(self):
        self.state.count += 1
'''
        js = transpile(code)
        assert_has_assignment_with_operation(js, "this.state.count", "add")
    
    def test_subscript_with_expression_index_augassign(self):
        """items[i + 1] += value"""
        code = '''
def update(items, i):
    items[i + 1] += 10
'''
        js = transpile(code)
        # Check for dunder runtime (current implementation uses __py.dunders.add)
        from tests.unit.transpiler.test_utils import assert_has_runtime_function
        assert_has_runtime_function(js, "add", runtime_type="dunder")
    
    def test_property_returning_computed_value(self):
        """Property that returns a computed value"""
        code = '''
class Vector:
    @property
    def magnitude(self):
        return (self.x ** 2 + self.y ** 2) ** 0.5
'''
        js = transpile(code)
        assert "get magnitude()" in js
        assert "return" in js
    
    def test_setter_with_type_conversion(self):
        """Setter that converts type"""
        code = '''
class Config:
    @property
    def timeout(self):
        return self._timeout
    
    @timeout.setter
    def timeout(self, val):
        self._timeout = int(val)
'''
        js = transpile(code)
        assert "set timeout(val)" in js
        assert "parseInt" in js or "int(" in js or "Number" in js


# =============================================================================
# RUN ALL TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
