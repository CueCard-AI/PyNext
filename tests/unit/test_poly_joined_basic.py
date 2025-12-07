"""
Test Phase 7.7: Joined Table Inheritance Basic Operations.

Tests the joined table inheritance strategy.
"""

import pytest
from typing import Optional
from unittest.mock import Mock, MagicMock, patch

from pynext.db.polymorphic import (
    polymorphic,
    get_strategy,
    JoinedTableStrategy,
    get_polymorphic_registry,
    reset_polymorphic_registry,
    InheritanceStrategy,
    get_inheritance_strategy,
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
    """Create an employee hierarchy for testing."""
    @polymorphic("type", strategy="joined")
    class Employee:
        __tablename__ = "employees"
        id: int
        name: str
        email: str
        type: str
        
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    @polymorphic.subtype("manager")
    class Manager(Employee):
        __tablename__ = "managers"
        department: str
        budget: float
    
    @polymorphic.subtype("engineer")
    class Engineer(Employee):
        __tablename__ = "engineers"
        language: str
        level: int
    
    return Employee, Manager, Engineer


# =============================================================================
# Test Strategy Selection
# =============================================================================

class TestJoinedStrategy:
    """Test joined strategy selection."""
    
    def test_joined_strategy_for_base(self, employee_hierarchy):
        """Joined strategy for base class."""
        Employee, Manager, Engineer = employee_hierarchy
        
        strategy = get_strategy(Employee)
        
        assert strategy is not None
        assert isinstance(strategy, JoinedTableStrategy)
    
    def test_joined_strategy_for_subtype(self, employee_hierarchy):
        """Joined strategy for subtype."""
        Employee, Manager, Engineer = employee_hierarchy
        
        strategy = get_strategy(Manager)
        
        assert strategy is not None
        assert isinstance(strategy, JoinedTableStrategy)
    
    def test_inheritance_strategy_enum(self, employee_hierarchy):
        """Correct strategy enum."""
        Employee, Manager, Engineer = employee_hierarchy
        
        assert get_inheritance_strategy(Employee) == InheritanceStrategy.JOINED


# =============================================================================
# Test Table Names
# =============================================================================

class TestJoinedTableNames:
    """Test table name resolution for joined."""
    
    def test_base_table_name(self, employee_hierarchy):
        """Base class has its own table."""
        Employee, Manager, Engineer = employee_hierarchy
        
        strategy = get_strategy(Employee)
        
        assert strategy.get_table_name(Employee) == "employees"
    
    def test_subtype_table_name(self, employee_hierarchy):
        """Subtype has its own table."""
        Employee, Manager, Engineer = employee_hierarchy
        
        strategy = get_strategy(Manager)
        
        assert strategy.get_table_name(Manager) == "managers"
    
    def test_each_subtype_different_table(self, employee_hierarchy):
        """Each subtype has different table."""
        Employee, Manager, Engineer = employee_hierarchy
        
        strategy = get_strategy(Employee)
        
        assert strategy.get_table_name(Manager) == "managers"
        assert strategy.get_table_name(Engineer) == "engineers"


# =============================================================================
# Test SELECT Query Generation
# =============================================================================

class TestJoinedSelectQuery:
    """Test SELECT query generation for joined."""
    
    def test_base_class_select(self, employee_hierarchy):
        """Base class SELECT is simple."""
        Employee, Manager, Engineer = employee_hierarchy
        
        strategy = get_strategy(Employee)
        query, params = strategy.build_select_query(Employee)
        
        assert "SELECT" in query
        assert "FROM employees" in query
        # Base query should not have JOIN
        assert "JOIN" not in query
    
    def test_subtype_select_with_join(self, employee_hierarchy):
        """Subtype SELECT includes JOIN."""
        Employee, Manager, Engineer = employee_hierarchy
        
        strategy = get_strategy(Manager)
        query, params = strategy.build_select_query(Manager)
        
        assert "SELECT" in query
        assert "employees" in query
        assert "managers" in query
        assert "JOIN" in query
        assert "WHERE" in query
        assert "manager" in params
    
    def test_engineer_select_join(self, employee_hierarchy):
        """Engineer SELECT with correct JOIN."""
        Employee, Manager, Engineer = employee_hierarchy
        
        strategy = get_strategy(Engineer)
        query, params = strategy.build_select_query(Engineer)
        
        assert "engineers" in query
        assert "engineer" in params


# =============================================================================
# Test INSERT Query Generation
# =============================================================================

class TestJoinedInsertQuery:
    """Test INSERT query generation for joined."""
    
    def test_base_insert(self, employee_hierarchy):
        """Base class INSERT is simple."""
        Employee, Manager, Engineer = employee_hierarchy
        
        strategy = get_strategy(Employee)
        query, params = strategy.build_insert_query(
            Employee,
            {"name": "John", "email": "john@example.com"}
        )
        
        assert "INSERT INTO employees" in query
        assert "RETURNING *" in query
    
    def test_subtype_insert_uses_cte(self, employee_hierarchy):
        """Subtype INSERT uses CTE for two tables."""
        Employee, Manager, Engineer = employee_hierarchy
        
        strategy = get_strategy(Manager)
        query, params = strategy.build_insert_query(
            Manager,
            {"name": "Jane", "email": "jane@example.com", "department": "IT", "budget": 100000}
        )
        
        assert "WITH" in query  # CTE
        assert "employees" in query
        assert "managers" in query
    
    def test_insert_separates_base_and_subtype_fields(self, employee_hierarchy):
        """INSERT separates fields correctly."""
        Employee, Manager, Engineer = employee_hierarchy
        
        strategy = get_strategy(Engineer)
        data = {
            "name": "Bob",
            "email": "bob@example.com",
            "language": "Python",
            "level": 3
        }
        query, params = strategy.build_insert_query(Engineer, data)
        
        # Should have both tables mentioned
        assert "employees" in query
        assert "engineers" in query


# =============================================================================
# Test Instance Creation
# =============================================================================

class TestJoinedInstanceCreation:
    """Test creating instances from joined rows."""
    
    def test_instantiate_manager(self, employee_hierarchy):
        """Instantiate Manager from row."""
        Employee, Manager, Engineer = employee_hierarchy
        
        strategy = get_strategy(Employee)
        row = {
            "id": 1,
            "name": "Jane",
            "email": "jane@example.com",
            "type": "manager",
            "department": "IT",
            "budget": 100000
        }
        
        instance = strategy.instantiate_from_row(row)
        
        assert isinstance(instance, Manager)
        assert instance.department == "IT"
    
    def test_instantiate_engineer(self, employee_hierarchy):
        """Instantiate Engineer from row."""
        Employee, Manager, Engineer = employee_hierarchy
        
        strategy = get_strategy(Employee)
        row = {
            "id": 1,
            "name": "Bob",
            "email": "bob@example.com",
            "type": "engineer",
            "language": "Python",
            "level": 3
        }
        
        instance = strategy.instantiate_from_row(row)
        
        assert isinstance(instance, Engineer)
        assert instance.language == "Python"
    
    def test_instantiate_base(self, employee_hierarchy):
        """Instantiate base Employee from row."""
        Employee, Manager, Engineer = employee_hierarchy
        
        strategy = get_strategy(Employee)
        row = {"id": 1, "name": "Test", "email": "test@example.com"}
        
        instance = strategy.instantiate_from_row(row)
        
        assert isinstance(instance, Employee)


# =============================================================================
# Test Edge Cases
# =============================================================================

class TestJoinedEdgeCases:
    """Test edge cases for joined inheritance."""
    
    def test_empty_subtype_fields(self, employee_hierarchy):
        """Subtype with no additional fields."""
        Employee, Manager, Engineer = employee_hierarchy
        
        strategy = get_strategy(Manager)
        # Only base fields
        query, params = strategy.build_insert_query(
            Manager,
            {"name": "Jane", "email": "jane@example.com"}
        )
        
        assert "INSERT" in query
    
    def test_unknown_type_uses_base(self, employee_hierarchy):
        """Unknown type falls back to base."""
        Employee, Manager, Engineer = employee_hierarchy
        
        strategy = get_strategy(Employee)
        row = {"id": 1, "name": "Test", "type": "unknown"}
        
        instance = strategy.instantiate_from_row(row)
        
        assert isinstance(instance, Employee)
        assert not isinstance(instance, Manager)

