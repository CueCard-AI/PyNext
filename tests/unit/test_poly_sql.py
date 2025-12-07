"""
Test Phase 7.7: SQL Generation Tests.

Detailed tests for SQL query generation across all strategies.
"""

import pytest
from typing import Optional
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch

from pynext.db.polymorphic import (
    polymorphic,
    get_strategy,
    SingleTableStrategy,
    JoinedTableStrategy,
    ConcreteTableStrategy,
    get_polymorphic_registry,
    reset_polymorphic_registry,
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


# =============================================================================
# Test STI SQL Generation
# =============================================================================

class TestSTISQL:
    """Test STI SQL generation."""
    
    def test_select_star(self):
        """SELECT * query."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            id: int
        
        strategy = get_strategy(Content)
        query, params = strategy.build_select_query(Content)
        
        assert query == "SELECT * FROM contents"
        assert params == []
    
    def test_select_columns(self):
        """SELECT with specific columns."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            id: int
            title: str
            body: str
        
        strategy = get_strategy(Content)
        query, params = strategy.build_select_query(Content, columns=["id", "title"])
        
        assert "SELECT id, title FROM contents" in query
    
    def test_subtype_where_clause(self):
        """Subtype adds WHERE clause."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            id: int
        
        @polymorphic.subtype("article")
        class Article(Content):
            pass
        
        strategy = get_strategy(Article)
        query, params = strategy.build_select_query(Article)
        
        assert "WHERE type = $1" in query
        assert params == ["article"]
    
    def test_insert_returning(self):
        """INSERT RETURNING query."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            id: int
            title: str
        
        strategy = get_strategy(Content)
        query, params = strategy.build_insert_query(Content, {"title": "Test"})
        
        assert "INSERT INTO contents" in query
        assert "RETURNING *" in query
    
    def test_insert_with_discriminator(self):
        """Subtype INSERT adds discriminator."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            id: int
        
        @polymorphic.subtype("post")
        class Post(Content):
            pass
        
        strategy = get_strategy(Post)
        query, params = strategy.build_insert_query(Post, {"id": 1})
        
        assert "type" in query
        assert "post" in params
    
    def test_insert_placeholders(self):
        """INSERT uses correct placeholders."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            id: int
            title: str
            body: str
        
        strategy = get_strategy(Content)
        query, params = strategy.build_insert_query(
            Content,
            {"title": "Test", "body": "Content"}
        )
        
        assert "$1" in query
        assert "$2" in query


# =============================================================================
# Test Joined SQL Generation
# =============================================================================

class TestJoinedSQL:
    """Test Joined Table SQL generation."""
    
    def test_base_select_no_join(self):
        """Base SELECT has no JOIN."""
        @polymorphic("type", strategy="joined")
        class Employee:
            __tablename__ = "employees"
            id: int
        
        strategy = get_strategy(Employee)
        query, params = strategy.build_select_query(Employee)
        
        assert "SELECT" in query
        assert "JOIN" not in query
    
    def test_subtype_select_with_join(self):
        """Subtype SELECT has JOIN."""
        @polymorphic("type", strategy="joined")
        class Employee:
            __tablename__ = "employees"
            id: int
        
        @polymorphic.subtype("manager")
        class Manager(Employee):
            __tablename__ = "managers"
            department: str
        
        strategy = get_strategy(Manager)
        query, params = strategy.build_select_query(Manager)
        
        assert "JOIN" in query
        assert "employees" in query
        assert "managers" in query
    
    def test_join_on_condition(self):
        """JOIN has ON condition."""
        @polymorphic("type", strategy="joined")
        class Employee:
            __tablename__ = "employees"
            id: int
        
        @polymorphic.subtype("engineer")
        class Engineer(Employee):
            __tablename__ = "engineers"
        
        strategy = get_strategy(Engineer)
        query, params = strategy.build_select_query(Engineer)
        
        assert "employees.id = engineers.id" in query
    
    def test_subtype_insert_uses_cte(self):
        """Subtype INSERT uses CTE."""
        @polymorphic("type", strategy="joined")
        class Employee:
            __tablename__ = "employees"
            id: int
            name: str
        
        @polymorphic.subtype("manager")
        class Manager(Employee):
            __tablename__ = "managers"
            department: str
        
        strategy = get_strategy(Manager)
        query, params = strategy.build_insert_query(
            Manager,
            {"name": "Jane", "department": "IT"}
        )
        
        assert "WITH" in query


# =============================================================================
# Test Concrete SQL Generation
# =============================================================================

class TestConcreteSQL:
    """Test Concrete Table SQL generation."""
    
    def test_subtype_select_simple(self):
        """Subtype SELECT is simple."""
        @polymorphic(strategy="concrete")
        class Vehicle:
            __tablename__ = "vehicles"
            id: int
        
        @polymorphic.subtype("car")
        class Car(Vehicle):
            __tablename__ = "cars"
        
        strategy = get_strategy(Car)
        query, params = strategy.build_select_query(Car)
        
        assert "SELECT * FROM cars" in query
        assert "UNION" not in query
    
    def test_base_select_uses_union(self):
        """Base SELECT uses UNION ALL."""
        @polymorphic(strategy="concrete")
        class Vehicle:
            __tablename__ = "vehicles"
            id: int
        
        @polymorphic.subtype("car")
        class Car(Vehicle):
            __tablename__ = "cars"
        
        @polymorphic.subtype("bike")
        class Bike(Vehicle):
            __tablename__ = "bikes"
        
        strategy = get_strategy(Vehicle)
        query, params = strategy.build_select_query(Vehicle)
        
        assert "UNION ALL" in query
        assert "cars" in query
        assert "bikes" in query
    
    def test_union_has_type_column(self):
        """UNION adds _type column."""
        @polymorphic(strategy="concrete")
        class Vehicle:
            __tablename__ = "vehicles"
            id: int
        
        @polymorphic.subtype("car")
        class Car(Vehicle):
            __tablename__ = "cars"
        
        @polymorphic.subtype("bike")
        class Bike(Vehicle):
            __tablename__ = "bikes"
        
        strategy = get_strategy(Vehicle)
        query, params = strategy.build_select_query(Vehicle)
        
        assert "_type" in query
    
    def test_subtype_insert_direct(self):
        """Subtype INSERT goes directly to own table."""
        @polymorphic(strategy="concrete")
        class Vehicle:
            __tablename__ = "vehicles"
            id: int
        
        @polymorphic.subtype("car")
        class Car(Vehicle):
            __tablename__ = "cars"
            doors: int
        
        strategy = get_strategy(Car)
        query, params = strategy.build_insert_query(Car, {"id": 1, "doors": 4})
        
        assert "INSERT INTO cars" in query
        assert "vehicles" not in query


# =============================================================================
# Test Parameterized Queries
# =============================================================================

class TestParameterizedQueries:
    """Test query parameterization."""
    
    def test_params_order_preserved(self):
        """Parameter order is preserved."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            id: int
            title: str
            body: str
        
        strategy = get_strategy(Content)
        
        # Use ordered data
        from collections import OrderedDict
        data = OrderedDict([
            ("title", "Test Title"),
            ("body", "Test Body"),
        ])
        
        query, params = strategy.build_insert_query(Content, data)
        
        assert params[0] == "Test Title"
        assert params[1] == "Test Body"
    
    def test_subtype_params_include_identity(self):
        """Subtype params include discriminator value."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            id: int
        
        @polymorphic.subtype("article")
        class Article(Content):
            pass
        
        strategy = get_strategy(Article)
        query, params = strategy.build_insert_query(Article, {"id": 1})
        
        assert "article" in params


# =============================================================================
# Test SQL Format Consistency
# =============================================================================

class TestSQLFormatConsistency:
    """Test SQL format is consistent."""
    
    def test_select_format(self):
        """SELECT format is consistent."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            id: int
        
        strategy = get_strategy(Content)
        query, _ = strategy.build_select_query(Content)
        
        assert query.startswith("SELECT")
        assert "FROM" in query
    
    def test_insert_format(self):
        """INSERT format is consistent."""
        @polymorphic("type")
        class Content:
            __tablename__ = "contents"
            id: int
        
        strategy = get_strategy(Content)
        query, _ = strategy.build_insert_query(Content, {"id": 1})
        
        assert "INSERT INTO" in query
        assert "VALUES" in query
        assert "RETURNING" in query

