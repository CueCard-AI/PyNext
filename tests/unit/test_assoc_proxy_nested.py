"""
Tests for nested path traversal in association proxy.

Tests cover:
- Multi-level dot notation paths
- None handling at different levels
- Complex nested structures
- Path edge cases
"""

import pytest
from typing import Optional, List
from dataclasses import dataclass


# =============================================================================
# Mock Classes for Nested Testing
# =============================================================================

@dataclass
class Address:
    """Address model."""
    street: str
    city: str
    country: str
    zip_code: Optional[str] = None


@dataclass
class Company:
    """Company model."""
    name: str
    address: Optional[Address] = None
    industry: str = "Tech"


@dataclass
class Department:
    """Department model."""
    name: str
    code: str
    company: Optional[Company] = None
    budget: float = 0.0


@dataclass
class Role:
    """Role with permissions."""
    name: str
    permissions: List[str]
    level: int = 1


@dataclass
class Employee:
    """Employee model with nested relationships."""
    id: int
    name: str
    department: Optional[Department] = None
    role: Optional[Role] = None


class MockTable:
    """Base mock table."""
    _fields = {}
    __table_name__ = "mock"


from pynext.db.relationships.association_proxy import (
    association_proxy,
    _traverse_path,
)


# =============================================================================
# Test: Two-Level Paths
# =============================================================================

class TestTwoLevelPaths:
    """Test two-level nested paths."""
    
    def test_simple_two_level(self):
        """Simple two-level path: department.name."""
        class Model(MockTable):
            def __init__(self, emp: Employee):
                self._employee = emp
            
            @property
            def employee(self):
                return self._employee
        
        Model.dept_name = association_proxy("employee", "department.name", scalar=True)
        
        dept = Department("Engineering", "ENG")
        emp = Employee(1, "Alice", department=dept)
        model = Model(emp)
        
        assert model.dept_name == "Engineering"
    
    def test_two_level_integer(self):
        """Two-level path to integer."""
        class Model(MockTable):
            def __init__(self, emp: Employee):
                self._employee = emp
            
            @property
            def employee(self):
                return self._employee
        
        Model.role_level = association_proxy("employee", "role.level", scalar=True)
        
        role = Role("Admin", ["read", "write"], level=5)
        emp = Employee(1, "Alice", role=role)
        model = Model(emp)
        
        assert model.role_level == 5
    
    def test_two_level_list(self):
        """Two-level path to list attribute."""
        class Model(MockTable):
            def __init__(self, emp: Employee):
                self._employee = emp
            
            @property
            def employee(self):
                return self._employee
        
        Model.permissions = association_proxy("employee", "role.permissions", scalar=True)
        
        role = Role("Admin", ["read", "write", "delete"])
        emp = Employee(1, "Alice", role=role)
        model = Model(emp)
        
        assert model.permissions == ["read", "write", "delete"]


# =============================================================================
# Test: Three-Level Paths
# =============================================================================

class TestThreeLevelPaths:
    """Test three-level nested paths."""
    
    def test_three_level_string(self):
        """Three-level path: department.company.name."""
        class Model(MockTable):
            def __init__(self, emp: Employee):
                self._employee = emp
            
            @property
            def employee(self):
                return self._employee
        
        Model.company_name = association_proxy("employee", "department.company.name", scalar=True)
        
        company = Company("Acme Corp")
        dept = Department("Engineering", "ENG", company=company)
        emp = Employee(1, "Alice", department=dept)
        model = Model(emp)
        
        assert model.company_name == "Acme Corp"
    
    def test_three_level_to_object(self):
        """Three-level path returning object."""
        class Model(MockTable):
            def __init__(self, emp: Employee):
                self._employee = emp
            
            @property
            def employee(self):
                return self._employee
        
        Model.address = association_proxy("employee", "department.company.address", scalar=True)
        
        addr = Address("123 Main St", "SF", "USA")
        company = Company("Acme Corp", address=addr)
        dept = Department("Engineering", "ENG", company=company)
        emp = Employee(1, "Alice", department=dept)
        model = Model(emp)
        
        assert model.address is addr
        assert model.address.city == "SF"


# =============================================================================
# Test: Four-Level Paths
# =============================================================================

class TestFourLevelPaths:
    """Test four-level nested paths."""
    
    def test_four_level_path(self):
        """Four-level path: department.company.address.city."""
        class Model(MockTable):
            def __init__(self, emp: Employee):
                self._employee = emp
            
            @property
            def employee(self):
                return self._employee
        
        Model.city = association_proxy("employee", "department.company.address.city", scalar=True)
        
        addr = Address("123 Main St", "San Francisco", "USA")
        company = Company("Acme Corp", address=addr)
        dept = Department("Engineering", "ENG", company=company)
        emp = Employee(1, "Alice", department=dept)
        model = Model(emp)
        
        assert model.city == "San Francisco"
    
    def test_four_level_optional(self):
        """Four-level path with optional value at end."""
        class Model(MockTable):
            def __init__(self, emp: Employee):
                self._employee = emp
            
            @property
            def employee(self):
                return self._employee
        
        Model.zip_code = association_proxy("employee", "department.company.address.zip_code", scalar=True)
        
        addr = Address("123 Main St", "SF", "USA", zip_code="94102")
        company = Company("Acme Corp", address=addr)
        dept = Department("Engineering", "ENG", company=company)
        emp = Employee(1, "Alice", department=dept)
        model = Model(emp)
        
        assert model.zip_code == "94102"


# =============================================================================
# Test: None at Different Levels
# =============================================================================

class TestNoneAtLevels:
    """Test None handling at different path levels."""
    
    def test_none_at_level_1(self):
        """None at first level returns None."""
        class Model(MockTable):
            def __init__(self):
                self._employee = None
            
            @property
            def employee(self):
                return self._employee
        
        Model.dept_name = association_proxy("employee", "department.name", scalar=True)
        
        assert Model().dept_name is None
    
    def test_none_at_level_2(self):
        """None at second level returns None."""
        class Model(MockTable):
            def __init__(self, emp: Employee):
                self._employee = emp
            
            @property
            def employee(self):
                return self._employee
        
        Model.dept_name = association_proxy("employee", "department.name", scalar=True)
        
        emp = Employee(1, "Alice", department=None)
        model = Model(emp)
        
        assert model.dept_name is None
    
    def test_none_at_level_3(self):
        """None at third level returns None."""
        class Model(MockTable):
            def __init__(self, emp: Employee):
                self._employee = emp
            
            @property
            def employee(self):
                return self._employee
        
        Model.company_name = association_proxy("employee", "department.company.name", scalar=True)
        
        dept = Department("Engineering", "ENG", company=None)
        emp = Employee(1, "Alice", department=dept)
        model = Model(emp)
        
        assert model.company_name is None
    
    def test_none_at_level_4(self):
        """None at fourth level returns None."""
        class Model(MockTable):
            def __init__(self, emp: Employee):
                self._employee = emp
            
            @property
            def employee(self):
                return self._employee
        
        Model.city = association_proxy("employee", "department.company.address.city", scalar=True)
        
        company = Company("Acme Corp", address=None)
        dept = Department("Engineering", "ENG", company=company)
        emp = Employee(1, "Alice", department=dept)
        model = Model(emp)
        
        assert model.city is None


# =============================================================================
# Test: Collections with Nested Paths
# =============================================================================

class TestCollectionsNestedPaths:
    """Test nested paths on collections."""
    
    def test_collection_nested_path(self):
        """Nested path on collection items."""
        class User(MockTable):
            def __init__(self, employees: List[Employee]):
                self._employees = employees
            
            @property
            def employees(self):
                return self._employees
        
        User.dept_names = association_proxy("employees", "department.name")
        
        emps = [
            Employee(1, "Alice", Department("Eng", "E")),
            Employee(2, "Bob", Department("Sales", "S")),
        ]
        user = User(emps)
        
        assert list(user.dept_names) == ["Eng", "Sales"]
    
    def test_collection_deep_nested_path(self):
        """Deep nested path on collection items."""
        class User(MockTable):
            def __init__(self, employees: List[Employee]):
                self._employees = employees
            
            @property
            def employees(self):
                return self._employees
        
        User.company_names = association_proxy("employees", "department.company.name")
        
        emps = [
            Employee(1, "Alice", Department("Eng", "E", Company("Acme"))),
            Employee(2, "Bob", Department("Sales", "S", Company("Beta"))),
        ]
        user = User(emps)
        
        assert list(user.company_names) == ["Acme", "Beta"]
    
    def test_collection_skips_none_in_path(self):
        """Collection skips items with None in path."""
        class User(MockTable):
            def __init__(self, employees: List[Employee]):
                self._employees = employees
            
            @property
            def employees(self):
                return self._employees
        
        User.company_names = association_proxy("employees", "department.company.name")
        
        emps = [
            Employee(1, "Alice", Department("Eng", "E", Company("Acme"))),
            Employee(2, "Bob", Department("Sales", "S", company=None)),  # No company
            Employee(3, "Charlie", Department("HR", "H", Company("Gamma"))),
        ]
        user = User(emps)
        
        assert list(user.company_names) == ["Acme", "Gamma"]


# =============================================================================
# Test: _traverse_path Helper Directly
# =============================================================================

class TestTraversePathHelper:
    """Test the _traverse_path helper function directly."""
    
    def test_single_attr(self):
        """Single attribute traversal."""
        obj = type('Obj', (), {'name': 'Test'})()
        assert _traverse_path(obj, 'name') == 'Test'
    
    def test_two_attrs(self):
        """Two attribute traversal."""
        inner = type('Inner', (), {'value': 42})()
        outer = type('Outer', (), {'inner': inner})()
        assert _traverse_path(outer, 'inner.value') == 42
    
    def test_three_attrs(self):
        """Three attribute traversal."""
        l3 = type('L3', (), {'data': 'deep'})()
        l2 = type('L2', (), {'l3': l3})()
        l1 = type('L1', (), {'l2': l2})()
        assert _traverse_path(l1, 'l2.l3.data') == 'deep'
    
    def test_none_root(self):
        """None root returns None."""
        assert _traverse_path(None, 'any.path') is None
    
    def test_none_intermediate(self):
        """None intermediate returns None."""
        outer = type('Outer', (), {'inner': None})()
        assert _traverse_path(outer, 'inner.value') is None
    
    def test_missing_attr(self):
        """Missing attribute returns None."""
        obj = type('Obj', (), {})()
        assert _traverse_path(obj, 'nonexistent') is None
    
    def test_empty_path(self):
        """Empty path returns object itself."""
        obj = type('Obj', (), {'name': 'Test'})()
        result = _traverse_path(obj, '')
        assert result is obj


# =============================================================================
# Test: Path Edge Cases
# =============================================================================

class TestPathEdgeCases:
    """Test edge cases in path traversal."""
    
    def test_single_char_attr(self):
        """Single character attribute name."""
        obj = type('Obj', (), {'x': 1, 'y': 2})()
        assert _traverse_path(obj, 'x') == 1
        assert _traverse_path(obj, 'y') == 2
    
    def test_underscore_attr(self):
        """Attribute with underscore."""
        obj = type('Obj', (), {'my_value': 'test'})()
        assert _traverse_path(obj, 'my_value') == 'test'
    
    def test_numeric_suffix_attr(self):
        """Attribute with numeric suffix."""
        obj = type('Obj', (), {'value1': 'a', 'value2': 'b'})()
        assert _traverse_path(obj, 'value1') == 'a'
        assert _traverse_path(obj, 'value2') == 'b'
    
    def test_double_underscore_attr(self):
        """Attribute with double underscore."""
        obj = type('Obj', (), {'__special__': 'val'})()
        assert _traverse_path(obj, '__special__') == 'val'
    
    def test_method_access(self):
        """Can access methods (but not call them)."""
        class Obj:
            def my_method(self):
                return 42
        
        result = _traverse_path(Obj(), 'my_method')
        assert callable(result)
    
    def test_property_access(self):
        """Can access properties."""
        class Obj:
            @property
            def computed(self):
                return "computed_value"
        
        result = _traverse_path(Obj(), 'computed')
        assert result == "computed_value"


# =============================================================================
# Test: Nested with Different Types
# =============================================================================

class TestNestedDifferentTypes:
    """Test nested paths with different value types."""
    
    def test_nested_to_list(self):
        """Nested path ending in list."""
        @dataclass
        class Container:
            items: List[str]
        
        @dataclass
        class Wrapper:
            container: Container
        
        class Model(MockTable):
            def __init__(self, wrapper: Wrapper):
                self._wrapper = wrapper
            
            @property
            def wrapper(self):
                return self._wrapper
        
        Model.items = association_proxy("wrapper", "container.items", scalar=True)
        
        model = Model(Wrapper(Container(['a', 'b', 'c'])))
        assert model.items == ['a', 'b', 'c']
    
    def test_nested_to_dict(self):
        """Nested path ending in dict."""
        @dataclass
        class Config:
            settings: dict
        
        @dataclass
        class App:
            config: Config
        
        class Model(MockTable):
            def __init__(self, app: App):
                self._app = app
            
            @property
            def app(self):
                return self._app
        
        Model.settings = association_proxy("app", "config.settings", scalar=True)
        
        model = Model(App(Config({'key': 'value'})))
        assert model.settings == {'key': 'value'}
    
    def test_nested_to_nested_object(self):
        """Nested path ending in nested object."""
        class Model(MockTable):
            def __init__(self, emp: Employee):
                self._employee = emp
            
            @property
            def employee(self):
                return self._employee
        
        Model.company = association_proxy("employee", "department.company", scalar=True)
        
        company = Company("Acme")
        emp = Employee(1, "Alice", Department("Eng", "E", company))
        model = Model(emp)
        
        assert model.company is company
        assert model.company.name == "Acme"


# =============================================================================
# Test: Multiple Nested Proxies
# =============================================================================

class TestMultipleNestedProxies:
    """Test multiple nested proxies on same class."""
    
    def test_multiple_same_root(self):
        """Multiple proxies with same root path."""
        class Model(MockTable):
            def __init__(self, emp: Employee):
                self._employee = emp
            
            @property
            def employee(self):
                return self._employee
        
        Model.dept_name = association_proxy("employee", "department.name", scalar=True)
        Model.dept_code = association_proxy("employee", "department.code", scalar=True)
        Model.dept_budget = association_proxy("employee", "department.budget", scalar=True)
        
        emp = Employee(1, "Alice", Department("Engineering", "ENG", budget=100000.0))
        model = Model(emp)
        
        assert model.dept_name == "Engineering"
        assert model.dept_code == "ENG"
        assert model.dept_budget == 100000.0
    
    def test_multiple_different_depths(self):
        """Multiple proxies at different nesting depths."""
        class Model(MockTable):
            def __init__(self, emp: Employee):
                self._employee = emp
            
            @property
            def employee(self):
                return self._employee
        
        # Depth 1
        Model.emp_name = association_proxy("employee", "name", scalar=True)
        # Depth 2
        Model.dept_name = association_proxy("employee", "department.name", scalar=True)
        # Depth 3
        Model.company_name = association_proxy("employee", "department.company.name", scalar=True)
        # Depth 4
        Model.city = association_proxy("employee", "department.company.address.city", scalar=True)
        
        addr = Address("123 Main", "NYC", "USA")
        company = Company("Acme", addr)
        dept = Department("Eng", "E", company)
        emp = Employee(1, "Alice", dept)
        model = Model(emp)
        
        assert model.emp_name == "Alice"
        assert model.dept_name == "Eng"
        assert model.company_name == "Acme"
        assert model.city == "NYC"


# =============================================================================
# Test: Path Consistency
# =============================================================================

class TestPathConsistency:
    """Test that paths return consistent results."""
    
    def test_repeated_access_consistent(self):
        """Repeated access returns same value."""
        class Model(MockTable):
            def __init__(self, emp: Employee):
                self._employee = emp
            
            @property
            def employee(self):
                return self._employee
        
        Model.city = association_proxy("employee", "department.company.address.city", scalar=True)
        
        addr = Address("123 Main", "SF", "USA")
        emp = Employee(1, "Alice", Department("E", "E", Company("A", addr)))
        model = Model(emp)
        
        r1 = model.city
        r2 = model.city
        r3 = model.city
        
        assert r1 == r2 == r3 == "SF"
    
    def test_source_change_reflected(self):
        """Changes to source object are reflected."""
        class Model(MockTable):
            def __init__(self, emp: Employee):
                self._employee = emp
            
            @property
            def employee(self):
                return self._employee
            
            @employee.setter
            def employee(self, val):
                self._employee = val
        
        Model.dept_name = association_proxy("employee", "department.name", scalar=True)
        
        emp1 = Employee(1, "Alice", Department("Engineering", "E"))
        model = Model(emp1)
        
        assert model.dept_name == "Engineering"
        
        # Change employee
        emp2 = Employee(2, "Bob", Department("Sales", "S"))
        model.employee = emp2
        
        assert model.dept_name == "Sales"

