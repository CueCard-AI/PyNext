"""
Test Phase 7.7: Concrete Table Inheritance Query Tests.

Tests query generation for concrete table inheritance.
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
    """Create vehicle hierarchy."""
    @polymorphic(strategy="concrete")
    class Vehicle:
        __tablename__ = "vehicles"
        id: int
        make: str
        model: str
        year: int
        color: str
        
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    @polymorphic.subtype("car")
    class Car(Vehicle):
        __tablename__ = "cars"
        num_doors: int
        trunk_size: float
        fuel_type: str
    
    @polymorphic.subtype("motorcycle")
    class Motorcycle(Vehicle):
        __tablename__ = "motorcycles"
        engine_cc: int
        has_sidecar: bool
        style: str
    
    @polymorphic.subtype("truck")
    class Truck(Vehicle):
        __tablename__ = "trucks"
        bed_length: float
        towing_capacity: int
        is_4x4: bool
    
    return Vehicle, Car, Motorcycle, Truck


# =============================================================================
# Test SELECT Queries
# =============================================================================

class TestConcreteSelect:
    """Test SELECT query generation for concrete."""
    
    def test_subtype_select_simple(self, vehicle_hierarchy):
        """Subtype SELECT is simple."""
        Vehicle, Car, Motorcycle, Truck = vehicle_hierarchy
        
        strategy = get_strategy(Car)
        query, params = strategy.build_select_query(Car)
        
        assert "SELECT" in query
        assert "FROM cars" in query
        assert "UNION" not in query
    
    def test_base_select_uses_union(self, vehicle_hierarchy):
        """Base SELECT uses UNION ALL."""
        Vehicle, Car, Motorcycle, Truck = vehicle_hierarchy
        
        strategy = get_strategy(Vehicle)
        query, params = strategy.build_select_query(Vehicle)
        
        assert "UNION ALL" in query
    
    def test_union_includes_all_subtypes(self, vehicle_hierarchy):
        """UNION includes all registered subtypes."""
        Vehicle, Car, Motorcycle, Truck = vehicle_hierarchy
        
        strategy = get_strategy(Vehicle)
        query, params = strategy.build_select_query(Vehicle)
        
        assert "cars" in query
        assert "motorcycles" in query
        assert "trucks" in query
    
    def test_union_adds_type_column(self, vehicle_hierarchy):
        """UNION adds _type column."""
        Vehicle, Car, Motorcycle, Truck = vehicle_hierarchy
        
        strategy = get_strategy(Vehicle)
        query, params = strategy.build_select_query(Vehicle)
        
        assert "_type" in query
        assert "'car'" in query or "car" in query
        assert "'motorcycle'" in query or "motorcycle" in query
        assert "'truck'" in query or "truck" in query
    
    def test_motorcycle_select(self, vehicle_hierarchy):
        """Motorcycle SELECT from own table."""
        Vehicle, Car, Motorcycle, Truck = vehicle_hierarchy
        
        strategy = get_strategy(Motorcycle)
        query, params = strategy.build_select_query(Motorcycle)
        
        assert "FROM motorcycles" in query
    
    def test_truck_select(self, vehicle_hierarchy):
        """Truck SELECT from own table."""
        Vehicle, Car, Motorcycle, Truck = vehicle_hierarchy
        
        strategy = get_strategy(Truck)
        query, params = strategy.build_select_query(Truck)
        
        assert "FROM trucks" in query


# =============================================================================
# Test INSERT Queries
# =============================================================================

class TestConcreteInsert:
    """Test INSERT query generation for concrete."""
    
    def test_car_insert(self, vehicle_hierarchy):
        """Car INSERT into own table."""
        Vehicle, Car, Motorcycle, Truck = vehicle_hierarchy
        
        strategy = get_strategy(Car)
        query, params = strategy.build_insert_query(
            Car,
            {
                "make": "Toyota",
                "model": "Camry",
                "year": 2023,
                "color": "Blue",
                "num_doors": 4,
                "trunk_size": 15.5,
                "fuel_type": "Hybrid"
            }
        )
        
        assert "INSERT INTO cars" in query
        assert "RETURNING *" in query
    
    def test_motorcycle_insert(self, vehicle_hierarchy):
        """Motorcycle INSERT."""
        Vehicle, Car, Motorcycle, Truck = vehicle_hierarchy
        
        strategy = get_strategy(Motorcycle)
        query, params = strategy.build_insert_query(
            Motorcycle,
            {
                "make": "Honda",
                "model": "CB500",
                "year": 2023,
                "color": "Red",
                "engine_cc": 500,
                "has_sidecar": False,
                "style": "Sport"
            }
        )
        
        assert "INSERT INTO motorcycles" in query
    
    def test_truck_insert(self, vehicle_hierarchy):
        """Truck INSERT."""
        Vehicle, Car, Motorcycle, Truck = vehicle_hierarchy
        
        strategy = get_strategy(Truck)
        query, params = strategy.build_insert_query(
            Truck,
            {
                "make": "Ford",
                "model": "F-150",
                "year": 2023,
                "color": "Black",
                "bed_length": 6.5,
                "towing_capacity": 10000,
                "is_4x4": True
            }
        )
        
        assert "INSERT INTO trucks" in query
    
    def test_insert_includes_all_fields(self, vehicle_hierarchy):
        """INSERT includes inherited and own fields."""
        Vehicle, Car, Motorcycle, Truck = vehicle_hierarchy
        
        strategy = get_strategy(Car)
        query, params = strategy.build_insert_query(
            Car,
            {
                "make": "Toyota",
                "model": "Camry",
                "num_doors": 4
            }
        )
        
        # Both base and subtype fields
        assert "make" in query
        assert "num_doors" in query


# =============================================================================
# Test Instance Creation
# =============================================================================

class TestConcreteInstantiation:
    """Test instance creation from concrete rows."""
    
    def test_instantiate_car(self, vehicle_hierarchy):
        """Instantiate Car."""
        Vehicle, Car, Motorcycle, Truck = vehicle_hierarchy
        
        strategy = get_strategy(Vehicle)
        row = {
            "id": 1,
            "make": "Toyota",
            "model": "Camry",
            "year": 2023,
            "_type": "car",
            "num_doors": 4,
            "trunk_size": 15.5,
            "fuel_type": "Hybrid"
        }
        
        instance = strategy.instantiate_from_row(row)
        
        assert isinstance(instance, Car)
        assert instance.num_doors == 4
    
    def test_instantiate_motorcycle(self, vehicle_hierarchy):
        """Instantiate Motorcycle."""
        Vehicle, Car, Motorcycle, Truck = vehicle_hierarchy
        
        strategy = get_strategy(Vehicle)
        row = {
            "id": 2,
            "make": "Honda",
            "model": "CB500",
            "year": 2023,
            "_type": "motorcycle",
            "engine_cc": 500,
            "has_sidecar": False,
            "style": "Sport"
        }
        
        instance = strategy.instantiate_from_row(row)
        
        assert isinstance(instance, Motorcycle)
        assert instance.engine_cc == 500
    
    def test_instantiate_truck(self, vehicle_hierarchy):
        """Instantiate Truck."""
        Vehicle, Car, Motorcycle, Truck = vehicle_hierarchy
        
        strategy = get_strategy(Vehicle)
        row = {
            "id": 3,
            "make": "Ford",
            "model": "F-150",
            "year": 2023,
            "_type": "truck",
            "bed_length": 6.5,
            "towing_capacity": 10000,
            "is_4x4": True
        }
        
        instance = strategy.instantiate_from_row(row)
        
        assert isinstance(instance, Truck)
        assert instance.towing_capacity == 10000
    
    def test_type_column_removed(self, vehicle_hierarchy):
        """_type column removed from instance."""
        Vehicle, Car, Motorcycle, Truck = vehicle_hierarchy
        
        strategy = get_strategy(Vehicle)
        row = {"id": 1, "make": "Toyota", "_type": "car"}
        
        instance = strategy.instantiate_from_row(row)
        
        assert not hasattr(instance, '_type')
    
    def test_force_target_class(self, vehicle_hierarchy):
        """Force specific target class."""
        Vehicle, Car, Motorcycle, Truck = vehicle_hierarchy
        
        strategy = get_strategy(Vehicle)
        row = {"id": 1, "make": "Toyota", "_type": "car"}
        
        instance = strategy.instantiate_from_row(row, target_class=Vehicle)
        
        assert type(instance) == Vehicle


# =============================================================================
# Test Multiple Rows
# =============================================================================

class TestConcreteMultipleRows:
    """Test instantiating multiple rows."""
    
    def test_mixed_types(self, vehicle_hierarchy):
        """Instantiate mixed types from UNION result."""
        Vehicle, Car, Motorcycle, Truck = vehicle_hierarchy
        
        strategy = get_strategy(Vehicle)
        rows = [
            {"id": 1, "make": "Toyota", "_type": "car", "num_doors": 4},
            {"id": 2, "make": "Honda", "_type": "motorcycle", "engine_cc": 500},
            {"id": 3, "make": "Ford", "_type": "truck", "bed_length": 6.5},
            {"id": 4, "make": "BMW", "_type": "car", "num_doors": 2},
            {"id": 5, "make": "Harley", "_type": "motorcycle", "engine_cc": 1200},
        ]
        
        instances = [strategy.instantiate_from_row(row) for row in rows]
        
        assert isinstance(instances[0], Car)
        assert isinstance(instances[1], Motorcycle)
        assert isinstance(instances[2], Truck)
        assert isinstance(instances[3], Car)
        assert isinstance(instances[4], Motorcycle)


# =============================================================================
# Test Edge Cases
# =============================================================================

class TestConcreteEdgeCases:
    """Test edge cases for concrete inheritance."""
    
    def test_unknown_type(self, vehicle_hierarchy):
        """Unknown _type uses base class."""
        Vehicle, Car, Motorcycle, Truck = vehicle_hierarchy
        
        strategy = get_strategy(Vehicle)
        row = {"id": 1, "make": "Unknown", "_type": "unknown"}
        
        instance = strategy.instantiate_from_row(row)
        
        assert isinstance(instance, Vehicle)
    
    def test_no_type_column(self, vehicle_hierarchy):
        """No _type column uses base class."""
        Vehicle, Car, Motorcycle, Truck = vehicle_hierarchy
        
        strategy = get_strategy(Vehicle)
        row = {"id": 1, "make": "Unknown"}
        
        instance = strategy.instantiate_from_row(row)
        
        assert isinstance(instance, Vehicle)
    
    def test_empty_type_column(self, vehicle_hierarchy):
        """Empty _type uses base class."""
        Vehicle, Car, Motorcycle, Truck = vehicle_hierarchy
        
        strategy = get_strategy(Vehicle)
        row = {"id": 1, "make": "Unknown", "_type": ""}
        
        instance = strategy.instantiate_from_row(row)
        
        assert isinstance(instance, Vehicle)
    
    def test_null_type_column(self, vehicle_hierarchy):
        """Null _type uses base class."""
        Vehicle, Car, Motorcycle, Truck = vehicle_hierarchy
        
        strategy = get_strategy(Vehicle)
        row = {"id": 1, "make": "Unknown", "_type": None}
        
        instance = strategy.instantiate_from_row(row)
        
        assert isinstance(instance, Vehicle)
    
    def test_no_subtypes_registered(self):
        """Base with no subtypes."""
        @polymorphic(strategy="concrete")
        class Shape:
            __tablename__ = "shapes"
            id: int
            
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        strategy = get_strategy(Shape)
        query, params = strategy.build_select_query(Shape)
        
        # Falls back to base table
        assert "shapes" in query

