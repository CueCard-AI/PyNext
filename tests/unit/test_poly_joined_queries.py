"""
Test Phase 7.7: Joined Table Inheritance Query Tests.

Tests query generation for joined table inheritance.
"""

import pytest
from typing import Optional
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch

from pynext.db.polymorphic import (
    polymorphic,
    get_strategy,
    JoinedTableStrategy,
    get_polymorphic_registry,
    reset_polymorphic_registry,
    InheritanceStrategy,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def reset_registry():
    """Reset registry before each test."""
    reset_polymorphic_registry()
    yield
    reset_polymorphic_registry()


@pytest.fixture
def employee_hierarchy():
    """Create employee hierarchy."""
    @polymorphic("employee_type", strategy="joined")
    class Employee:
        __tablename__ = "employees"
        id: int
        name: str
        email: str
        salary: Decimal
        
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    @polymorphic.subtype("manager")
    class Manager(Employee):
        __tablename__ = "managers"
        department: str
        budget: Decimal
        team_size: int
    
    @polymorphic.subtype("engineer")
    class Engineer(Employee):
        __tablename__ = "engineers"
        language: str
        level: int
        github_username: str
    
    @polymorphic.subtype("designer")
    class Designer(Employee):
        __tablename__ = "designers"
        specialty: str
        tools: str
    
    return Employee, Manager, Engineer, Designer


# =============================================================================
# Test SELECT Queries
# =============================================================================

class TestJoinedSelect:
    """Test SELECT query generation for joined."""
    
    def test_base_select_no_join(self, employee_hierarchy):
        """Base SELECT doesn't JOIN."""
        Employee, Manager, Engineer, Designer = employee_hierarchy
        
        strategy = get_strategy(Employee)
        query, params = strategy.build_select_query(Employee)
        
        assert "JOIN" not in query
        assert "FROM employees" in query
    
    def test_subtype_select_with_join(self, employee_hierarchy):
        """Subtype SELECT includes JOIN."""
        Employee, Manager, Engineer, Designer = employee_hierarchy
        
        strategy = get_strategy(Manager)
        query, params = strategy.build_select_query(Manager)
        
        assert "JOIN" in query
        assert "employees" in query
        assert "managers" in query
    
    def test_join_condition(self, employee_hierarchy):
        """JOIN condition is on ID."""
        Employee, Manager, Engineer, Designer = employee_hierarchy
        
        strategy = get_strategy(Engineer)
        query, params = strategy.build_select_query(Engineer)
        
        assert "employees.id = engineers.id" in query
    
    def test_where_clause_for_type(self, employee_hierarchy):
        """WHERE clause filters by type."""
        Employee, Manager, Engineer, Designer = employee_hierarchy
        
        strategy = get_strategy(Designer)
        query, params = strategy.build_select_query(Designer)
        
        assert "WHERE" in query
        assert "employee_type" in query
        assert params == ["designer"]
    
    def test_select_both_tables(self, employee_hierarchy):
        """SELECT includes columns from both tables."""
        Employee, Manager, Engineer, Designer = employee_hierarchy
        
        strategy = get_strategy(Manager)
        query, params = strategy.build_select_query(Manager)
        
        assert "employees.*" in query
        assert "managers.*" in query


# =============================================================================
# Test INSERT Queries
# =============================================================================

class TestJoinedInsert:
    """Test INSERT query generation for joined."""
    
    def test_base_insert_simple(self, employee_hierarchy):
        """Base INSERT is simple."""
        Employee, Manager, Engineer, Designer = employee_hierarchy
        
        strategy = get_strategy(Employee)
        query, params = strategy.build_insert_query(
            Employee,
            {"name": "John", "email": "john@example.com", "salary": 50000}
        )
        
        assert "INSERT INTO employees" in query
        assert "WITH" not in query  # No CTE for base
    
    def test_subtype_insert_uses_cte(self, employee_hierarchy):
        """Subtype INSERT uses CTE."""
        Employee, Manager, Engineer, Designer = employee_hierarchy
        
        strategy = get_strategy(Manager)
        query, params = strategy.build_insert_query(
            Manager,
            {
                "name": "Jane",
                "email": "jane@example.com",
                "salary": 80000,
                "department": "Engineering",
                "budget": 500000,
                "team_size": 10
            }
        )
        
        assert "WITH" in query
        assert "new_row" in query or "INSERT" in query
    
    def test_cte_inserts_into_base(self, employee_hierarchy):
        """CTE first inserts into base table."""
        Employee, Manager, Engineer, Designer = employee_hierarchy
        
        strategy = get_strategy(Engineer)
        query, params = strategy.build_insert_query(
            Engineer,
            {
                "name": "Bob",
                "email": "bob@example.com",
                "salary": 70000,
                "language": "Python",
                "level": 3,
                "github_username": "bob123"
            }
        )
        
        assert "INSERT INTO employees" in query
        assert "INSERT INTO engineers" in query
    
    def test_discriminator_added_to_base(self, employee_hierarchy):
        """Discriminator value added to base insert."""
        Employee, Manager, Engineer, Designer = employee_hierarchy
        
        strategy = get_strategy(Designer)
        query, params = strategy.build_insert_query(
            Designer,
            {
                "name": "Alice",
                "email": "alice@example.com",
                "salary": 65000,
                "specialty": "UX",
                "tools": "Figma"
            }
        )
        
        assert "employee_type" in query
        assert "designer" in params


# =============================================================================
# Test Instance Creation
# =============================================================================

class TestJoinedInstantiation:
    """Test instance creation from joined rows."""
    
    def test_instantiate_manager(self, employee_hierarchy):
        """Instantiate Manager."""
        Employee, Manager, Engineer, Designer = employee_hierarchy
        
        strategy = get_strategy(Employee)
        row = {
            "id": 1,
            "name": "Jane",
            "email": "jane@example.com",
            "salary": 80000,
            "employee_type": "manager",
            "department": "Engineering",
            "budget": 500000,
            "team_size": 10
        }
        
        instance = strategy.instantiate_from_row(row)
        
        assert isinstance(instance, Manager)
        assert instance.department == "Engineering"
    
    def test_instantiate_engineer(self, employee_hierarchy):
        """Instantiate Engineer."""
        Employee, Manager, Engineer, Designer = employee_hierarchy
        
        strategy = get_strategy(Employee)
        row = {
            "id": 2,
            "name": "Bob",
            "email": "bob@example.com",
            "salary": 70000,
            "employee_type": "engineer",
            "language": "Python",
            "level": 3,
            "github_username": "bob123"
        }
        
        instance = strategy.instantiate_from_row(row)
        
        assert isinstance(instance, Engineer)
        assert instance.language == "Python"
    
    def test_instantiate_designer(self, employee_hierarchy):
        """Instantiate Designer."""
        Employee, Manager, Engineer, Designer = employee_hierarchy
        
        strategy = get_strategy(Employee)
        row = {
            "id": 3,
            "name": "Alice",
            "email": "alice@example.com",
            "salary": 65000,
            "employee_type": "designer",
            "specialty": "UX",
            "tools": "Figma"
        }
        
        instance = strategy.instantiate_from_row(row)
        
        assert isinstance(instance, Designer)
        assert instance.specialty == "UX"
    
    def test_unknown_type_uses_base(self, employee_hierarchy):
        """Unknown type uses base class."""
        Employee, Manager, Engineer, Designer = employee_hierarchy
        
        strategy = get_strategy(Employee)
        row = {
            "id": 4,
            "name": "Unknown",
            "email": "unknown@example.com",
            "employee_type": "unknown"
        }
        
        instance = strategy.instantiate_from_row(row)
        
        assert isinstance(instance, Employee)
        assert type(instance).__name__ == "Employee"


# =============================================================================
# Test Multiple Rows
# =============================================================================

class TestJoinedMultipleRows:
    """Test instantiating multiple rows."""
    
    def test_mixed_types(self, employee_hierarchy):
        """Instantiate mixed types from rows."""
        Employee, Manager, Engineer, Designer = employee_hierarchy
        
        strategy = get_strategy(Employee)
        rows = [
            {"id": 1, "name": "Jane", "employee_type": "manager", 
             "department": "Eng", "budget": 100, "team_size": 5},
            {"id": 2, "name": "Bob", "employee_type": "engineer",
             "language": "Go", "level": 2, "github_username": "bob"},
            {"id": 3, "name": "Alice", "employee_type": "designer",
             "specialty": "UI", "tools": "Sketch"},
            {"id": 4, "name": "John", "employee_type": "manager",
             "department": "HR", "budget": 50, "team_size": 3},
        ]
        
        instances = [strategy.instantiate_from_row(row) for row in rows]
        
        assert isinstance(instances[0], Manager)
        assert isinstance(instances[1], Engineer)
        assert isinstance(instances[2], Designer)
        assert isinstance(instances[3], Manager)


# =============================================================================
# Test Edge Cases
# =============================================================================

class TestJoinedEdgeCases:
    """Test edge cases for joined inheritance."""
    
    def test_empty_subtype_data(self, employee_hierarchy):
        """Subtype with no additional data."""
        Employee, Manager, Engineer, Designer = employee_hierarchy
        
        strategy = get_strategy(Manager)
        # Only base fields
        query, params = strategy.build_insert_query(
            Manager,
            {"name": "Jane", "email": "jane@example.com"}
        )
        
        # Should still work
        assert "INSERT" in query
    
    def test_null_subtype_fields(self, employee_hierarchy):
        """Null values in subtype fields."""
        Employee, Manager, Engineer, Designer = employee_hierarchy
        
        strategy = get_strategy(Engineer)
        row = {
            "id": 1,
            "name": "Bob",
            "employee_type": "engineer",
            "language": None,
            "level": None,
            "github_username": None
        }
        
        instance = strategy.instantiate_from_row(row)
        
        assert isinstance(instance, Engineer)
        assert instance.language is None

