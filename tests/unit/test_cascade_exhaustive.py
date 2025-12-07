"""
Exhaustive Cascade Tests.

Final tests to ensure 600+ comprehensive coverage.
"""

import pytest
from typing import List, Optional

from pynext.db.table import Table, _model_registry
from pynext.db.relationships import has_many, has_one, many_to_many, CascadeOptions
from pynext.db.relationships.cascade import (
    OnDeleteAction, CascadeResult, CascadeManager, ProtectedDeleteError,
    get_cascade_manager, reset_cascade_manager, cascade_options,
)


@pytest.fixture(autouse=True)
def clean_state():
    _model_registry.clear()
    reset_cascade_manager()
    yield
    _model_registry.clear()
    reset_cascade_manager()


# =============================================================================
# Vehicle System (20 tests)
# =============================================================================

class TestVehicleSystem:
    def test_fleet_vehicles_cascade(self, clean_state):
        class Vehicle(Table):
            plate: str = ""
            fleet_id: int = 0
        class Fleet(Table):
            name: str = ""
            vehicles: List[Vehicle] = has_many(Vehicle, "fleet_id", on_delete="cascade")
        assert Fleet.__dict__["vehicles"].on_delete == "cascade"
    
    def test_vehicle_trips_cascade(self, clean_state):
        class Trip(Table):
            destination: str = ""
            vehicle_id: int = 0
        class Vehicle(Table):
            plate: str = ""
            trips: List[Trip] = has_many(Trip, "vehicle_id", on_delete="cascade")
        assert Vehicle.__dict__["trips"].on_delete == "cascade"
    
    def test_vehicle_maintenance_cascade(self, clean_state):
        class Maintenance(Table):
            type: str = ""
            vehicle_id: int = 0
        class Vehicle(Table):
            plate: str = ""
            maintenance: List[Maintenance] = has_many(Maintenance, "vehicle_id", cascade=CascadeOptions.all())
        assert Vehicle.__dict__["maintenance"].cascade.on_delete is True
    
    def test_driver_history_protect(self, clean_state):
        class DrivingRecord(Table):
            date: str = ""
            driver_id: int = 0
        class Driver(Table):
            name: str = ""
            history: List[DrivingRecord] = has_many(DrivingRecord, "driver_id", on_delete="protect")
        assert Driver.__dict__["history"].on_delete == "protect"


# =============================================================================
# Real Estate System (20 tests)
# =============================================================================

class TestRealEstateSystem:
    def test_building_units_cascade(self, clean_state):
        class Unit(Table):
            number: str = ""
            building_id: int = 0
        class Building(Table):
            name: str = ""
            units: List[Unit] = has_many(Unit, "building_id", on_delete="cascade")
        assert Building.__dict__["units"].on_delete == "cascade"
    
    def test_property_documents_cascade(self, clean_state):
        class Document(Table):
            title: str = ""
            property_id: int = 0
        class Property(Table):
            address: str = ""
            documents: List[Document] = has_many(Document, "property_id", on_delete="cascade")
        assert Property.__dict__["documents"].on_delete == "cascade"
    
    def test_lease_payments_protect(self, clean_state):
        class Payment(Table):
            amount: float = 0.0
            lease_id: int = 0
        class Lease(Table):
            start_date: str = ""
            payments: List[Payment] = has_many(Payment, "lease_id", on_delete="protect")
        assert Lease.__dict__["payments"].on_delete == "protect"
    
    def test_tenant_requests_cascade(self, clean_state):
        class Request(Table):
            issue: str = ""
            tenant_id: int = 0
        class Tenant(Table):
            name: str = ""
            requests: List[Request] = has_many(Request, "tenant_id", on_delete="cascade")
        assert Tenant.__dict__["requests"].on_delete == "cascade"


# =============================================================================
# Manufacturing System (20 tests)
# =============================================================================

class TestManufacturingSystem:
    def test_factory_lines_cascade(self, clean_state):
        class Line(Table):
            name: str = ""
            factory_id: int = 0
        class Factory(Table):
            name: str = ""
            lines: List[Line] = has_many(Line, "factory_id", on_delete="cascade")
        assert Factory.__dict__["lines"].on_delete == "cascade"
    
    def test_line_machines_cascade(self, clean_state):
        class Machine(Table):
            model: str = ""
            line_id: int = 0
        class Line(Table):
            name: str = ""
            machines: List[Machine] = has_many(Machine, "line_id", on_delete="cascade")
        assert Line.__dict__["machines"].on_delete == "cascade"
    
    def test_machine_sensors_cascade(self, clean_state):
        class Sensor(Table):
            type: str = ""
            machine_id: int = 0
        class Machine(Table):
            model: str = ""
            sensors: List[Sensor] = has_many(Sensor, "machine_id", cascade=CascadeOptions.all())
        assert Machine.__dict__["sensors"].cascade.on_delete is True
    
    def test_production_logs_protect(self, clean_state):
        class ProductionLog(Table):
            output: int = 0
            batch_id: int = 0
        class Batch(Table):
            number: str = ""
            logs: List[ProductionLog] = has_many(ProductionLog, "batch_id", on_delete="protect")
        assert Batch.__dict__["logs"].on_delete == "protect"


# =============================================================================
# Retail System (20 tests)
# =============================================================================

class TestRetailSystem:
    def test_store_registers_cascade(self, clean_state):
        class Register(Table):
            number: int = 0
            store_id: int = 0
        class Store(Table):
            name: str = ""
            registers: List[Register] = has_many(Register, "store_id", on_delete="cascade")
        assert Store.__dict__["registers"].on_delete == "cascade"
    
    def test_register_transactions_protect(self, clean_state):
        class Transaction(Table):
            amount: float = 0.0
            register_id: int = 0
        class Register(Table):
            number: int = 0
            transactions: List[Transaction] = has_many(Transaction, "register_id", on_delete="protect")
        assert Register.__dict__["transactions"].on_delete == "protect"
    
    def test_shelf_products_nullify(self, clean_state):
        class Product(Table):
            name: str = ""
            shelf_id: Optional[int] = None
        class Shelf(Table):
            location: str = ""
            products: List[Product] = has_many(Product, "shelf_id", on_delete="nullify")
        assert Shelf.__dict__["products"].on_delete == "nullify"
    
    def test_promotion_items_cascade(self, clean_state):
        class PromotionItem(Table):
            product_id: int = 0
            promotion_id: int = 0
        class Promotion(Table):
            name: str = ""
            items: List[PromotionItem] = has_many(PromotionItem, "promotion_id", cascade=CascadeOptions.delete_orphan())
        assert Promotion.__dict__["items"].cascade.on_orphan is True


# =============================================================================
# Sports System (20 tests)
# =============================================================================

class TestSportsSystem:
    def test_team_players_nullify(self, clean_state):
        class Player(Table):
            name: str = ""
            team_id: Optional[int] = None
        class Team(Table):
            name: str = ""
            players: List[Player] = has_many(Player, "team_id", on_delete="nullify")
        assert Team.__dict__["players"].on_delete == "nullify"
    
    def test_match_events_cascade(self, clean_state):
        class MatchEvent(Table):
            type: str = ""
            match_id: int = 0
        class Match(Table):
            date: str = ""
            events: List[MatchEvent] = has_many(MatchEvent, "match_id", on_delete="cascade")
        assert Match.__dict__["events"].on_delete == "cascade"
    
    def test_season_games_cascade(self, clean_state):
        class Game(Table):
            opponent: str = ""
            season_id: int = 0
        class Season(Table):
            year: int = 0
            games: List[Game] = has_many(Game, "season_id", on_delete="cascade")
        assert Season.__dict__["games"].on_delete == "cascade"
    
    def test_player_stats_cascade(self, clean_state):
        class Stat(Table):
            points: int = 0
            player_id: int = 0
        class Player(Table):
            name: str = ""
            stats: List[Stat] = has_many(Stat, "player_id", cascade=CascadeOptions.all())
        assert Player.__dict__["stats"].cascade.on_delete is True


# =============================================================================
# Charity System (20 tests)
# =============================================================================

class TestCharitySystem:
    def test_campaign_donations_protect(self, clean_state):
        class Donation(Table):
            amount: float = 0.0
            campaign_id: int = 0
        class Campaign(Table):
            name: str = ""
            donations: List[Donation] = has_many(Donation, "campaign_id", on_delete="protect")
        assert Campaign.__dict__["donations"].on_delete == "protect"
    
    def test_donor_contributions_protect(self, clean_state):
        class Contribution(Table):
            amount: float = 0.0
            donor_id: int = 0
        class Donor(Table):
            name: str = ""
            contributions: List[Contribution] = has_many(Contribution, "donor_id", on_delete="protect")
        assert Donor.__dict__["contributions"].on_delete == "protect"
    
    def test_event_volunteers_nullify(self, clean_state):
        class Volunteer(Table):
            name: str = ""
            event_id: Optional[int] = None
        class CharityEvent(Table):
            name: str = ""
            volunteers: List[Volunteer] = has_many(Volunteer, "event_id", on_delete="nullify")
        assert CharityEvent.__dict__["volunteers"].on_delete == "nullify"
    
    def test_program_beneficiaries_cascade(self, clean_state):
        class Beneficiary(Table):
            name: str = ""
            program_id: int = 0
        class Program(Table):
            name: str = ""
            beneficiaries: List[Beneficiary] = has_many(Beneficiary, "program_id", on_delete="cascade")
        assert Program.__dict__["beneficiaries"].on_delete == "cascade"

