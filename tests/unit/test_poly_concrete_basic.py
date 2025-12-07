"""
Test Phase 7.7: Concrete Table Inheritance Basic Operations.

Tests the concrete table inheritance strategy.
"""

import pytest
from typing import Optional
from unittest.mock import Mock, MagicMock, patch

from pynext.db.polymorphic import (
    polymorphic,
    get_strategy,
    ConcreteTableStrategy,
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
def vehicle_hierarchy():
    """Create a vehicle hierarchy for testing."""
    @polymorphic(strategy="concrete")
    class Vehicle:
        __tablename__ = "vehicles"
        id: int
        make: str
        model: str
        year: int
        
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    @polymorphic.subtype("car")
    class Car(Vehicle):
        __tablename__ = "cars"
        num_doors: int
        trunk_size: float
    
    @polymorphic.subtype("motorcycle")
    class Motorcycle(Vehicle):
        __tablename__ = "motorcycles"
        engine_cc: int
        has_sidecar: bool
    
    return Vehicle, Car, Motorcycle


# =============================================================================
# Test Strategy Selection
# =============================================================================

class TestConcreteStrategy:
    """Test concrete strategy selection."""
    
    def test_concrete_strategy_for_base(self, vehicle_hierarchy):
        """Concrete strategy for base class."""
        Vehicle, Car, Motorcycle = vehicle_hierarchy
        
        strategy = get_strategy(Vehicle)
        
        assert strategy is not None
        assert isinstance(strategy, ConcreteTableStrategy)
    
    def test_concrete_strategy_for_subtype(self, vehicle_hierarchy):
        """Concrete strategy for subtype."""
        Vehicle, Car, Motorcycle = vehicle_hierarchy
        
        strategy = get_strategy(Car)
        
        assert strategy is not None
        assert isinstance(strategy, ConcreteTableStrategy)
    
    def test_inheritance_strategy_enum(self, vehicle_hierarchy):
        """Correct strategy enum."""
        Vehicle, Car, Motorcycle = vehicle_hierarchy
        
        assert get_inheritance_strategy(Vehicle) == InheritanceStrategy.CONCRETE


# =============================================================================
# Test Table Names
# =============================================================================

class TestConcreteTableNames:
    """Test table name resolution for concrete."""
    
    def test_base_table_name(self, vehicle_hierarchy):
        """Base class has its own table."""
        Vehicle, Car, Motorcycle = vehicle_hierarchy
        
        strategy = get_strategy(Vehicle)
        
        assert strategy.get_table_name(Vehicle) == "vehicles"
    
    def test_car_table_name(self, vehicle_hierarchy):
        """Car has its own table."""
        Vehicle, Car, Motorcycle = vehicle_hierarchy
        
        strategy = get_strategy(Car)
        
        assert strategy.get_table_name(Car) == "cars"
    
    def test_motorcycle_table_name(self, vehicle_hierarchy):
        """Motorcycle has its own table."""
        Vehicle, Car, Motorcycle = vehicle_hierarchy
        
        strategy = get_strategy(Motorcycle)
        
        assert strategy.get_table_name(Motorcycle) == "motorcycles"


# =============================================================================
# Test SELECT Query Generation
# =============================================================================

class TestConcreteSelectQuery:
    """Test SELECT query generation for concrete."""
    
    def test_subtype_select_simple(self, vehicle_hierarchy):
        """Subtype SELECT is simple (own table)."""
        Vehicle, Car, Motorcycle = vehicle_hierarchy
        
        strategy = get_strategy(Car)
        query, params = strategy.build_select_query(Car)
        
        assert "SELECT" in query
        assert "FROM cars" in query
        assert "UNION" not in query  # Subtype query is simple
    
    def test_base_select_uses_union(self, vehicle_hierarchy):
        """Base class SELECT uses UNION ALL."""
        Vehicle, Car, Motorcycle = vehicle_hierarchy
        
        strategy = get_strategy(Vehicle)
        query, params = strategy.build_select_query(Vehicle)
        
        assert "UNION ALL" in query
        assert "cars" in query
        assert "motorcycles" in query
    
    def test_union_adds_type_column(self, vehicle_hierarchy):
        """UNION adds _type column for identification."""
        Vehicle, Car, Motorcycle = vehicle_hierarchy
        
        strategy = get_strategy(Vehicle)
        query, params = strategy.build_select_query(Vehicle)
        
        assert "_type" in query


# =============================================================================
# Test INSERT Query Generation
# =============================================================================

class TestConcreteInsertQuery:
    """Test INSERT query generation for concrete."""
    
    def test_subtype_insert_simple(self, vehicle_hierarchy):
        """Subtype INSERT is simple."""
        Vehicle, Car, Motorcycle = vehicle_hierarchy
        
        strategy = get_strategy(Car)
        query, params = strategy.build_insert_query(
            Car,
            {"make": "Toyota", "model": "Camry", "year": 2023, "num_doors": 4, "trunk_size": 15.5}
        )
        
        assert "INSERT INTO cars" in query
        assert "RETURNING *" in query
    
    def test_motorcycle_insert(self, vehicle_hierarchy):
        """Motorcycle INSERT."""
        Vehicle, Car, Motorcycle = vehicle_hierarchy
        
        strategy = get_strategy(Motorcycle)
        query, params = strategy.build_insert_query(
            Motorcycle,
            {"make": "Honda", "model": "CB500", "year": 2023, "engine_cc": 500, "has_sidecar": False}
        )
        
        assert "INSERT INTO motorcycles" in query


# =============================================================================
# Test Instance Creation
# =============================================================================

class TestConcreteInstanceCreation:
    """Test creating instances from concrete rows."""
    
    def test_instantiate_car(self, vehicle_hierarchy):
        """Instantiate Car from row."""
        Vehicle, Car, Motorcycle = vehicle_hierarchy
        
        strategy = get_strategy(Vehicle)
        row = {
            "id": 1,
            "make": "Toyota",
            "model": "Camry",
            "year": 2023,
            "_type": "car",
            "num_doors": 4,
            "trunk_size": 15.5
        }
        
        instance = strategy.instantiate_from_row(row)
        
        assert isinstance(instance, Car)
        assert instance.num_doors == 4
    
    def test_instantiate_motorcycle(self, vehicle_hierarchy):
        """Instantiate Motorcycle from row."""
        Vehicle, Car, Motorcycle = vehicle_hierarchy
        
        strategy = get_strategy(Vehicle)
        row = {
            "id": 1,
            "make": "Honda",
            "model": "CB500",
            "year": 2023,
            "_type": "motorcycle",
            "engine_cc": 500,
            "has_sidecar": False
        }
        
        instance = strategy.instantiate_from_row(row)
        
        assert isinstance(instance, Motorcycle)
        assert instance.engine_cc == 500
    
    def test_instantiate_removes_type_column(self, vehicle_hierarchy):
        """_type column is removed from instance."""
        Vehicle, Car, Motorcycle = vehicle_hierarchy
        
        strategy = get_strategy(Vehicle)
        row = {
            "id": 1,
            "make": "Toyota",
            "_type": "car",
        }
        
        instance = strategy.instantiate_from_row(row)
        
        assert not hasattr(instance, '_type')
    
    def test_instantiate_with_target_class(self, vehicle_hierarchy):
        """Force specific target class."""
        Vehicle, Car, Motorcycle = vehicle_hierarchy
        
        strategy = get_strategy(Vehicle)
        row = {"id": 1, "make": "Toyota", "_type": "car"}
        
        instance = strategy.instantiate_from_row(row, target_class=Vehicle)
        
        assert type(instance) == Vehicle


# =============================================================================
# Test Edge Cases
# =============================================================================

class TestConcreteEdgeCases:
    """Test edge cases for concrete inheritance."""
    
    def test_no_subtypes_registered(self):
        """Base with no registered subtypes."""
        @polymorphic(strategy="concrete")
        class Shape:
            __tablename__ = "shapes"
            id: int
            color: str
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        strategy = get_strategy(Shape)
        query, params = strategy.build_select_query(Shape)
        
        # Falls back to base table
        assert "shapes" in query
    
    def test_unknown_type_uses_base(self, vehicle_hierarchy):
        """Unknown _type falls back to base."""
        Vehicle, Car, Motorcycle = vehicle_hierarchy
        
        strategy = get_strategy(Vehicle)
        row = {"id": 1, "make": "Unknown", "_type": "unknown"}
        
        instance = strategy.instantiate_from_row(row)
        
        assert isinstance(instance, Vehicle)
    
    def test_no_type_column(self, vehicle_hierarchy):
        """Row without _type uses base."""
        Vehicle, Car, Motorcycle = vehicle_hierarchy
        
        strategy = get_strategy(Vehicle)
        row = {"id": 1, "make": "Toyota"}
        
        instance = strategy.instantiate_from_row(row)
        
        assert isinstance(instance, Vehicle)

