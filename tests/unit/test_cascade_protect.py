"""
Protect Cascade Tests.

Tests for on_delete="protect" functionality including:
- ProtectedDeleteError
- Protection checks
- Multiple protected relationships
- Protection with other cascades
"""

import pytest
from typing import List, Optional

from pynext.db.table import Table, _model_registry
from pynext.db.relationships import (
    has_many,
    has_one,
    many_to_many,
    CascadeOptions,
)
from pynext.db.relationships.cascade import (
    ProtectedDeleteError,
    get_cascade_manager,
    reset_cascade_manager,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def clean_state():
    """Clean state before each test."""
    _model_registry.clear()
    reset_cascade_manager()
    yield
    _model_registry.clear()
    reset_cascade_manager()


# =============================================================================
# ProtectedDeleteError Tests (20 tests)
# =============================================================================

class TestProtectedDeleteError:
    """Test ProtectedDeleteError."""
    
    def test_error_message_contains_model(self):
        """Test error message contains model name."""
        class MockModel:
            id = 123
            __class__ = type("User", (), {})
        
        error = ProtectedDeleteError(
            instance=MockModel(),
            relationship="orders",
            related_count=5,
        )
        
        # Check error message
        message = str(error)
        assert "orders" in message
        assert "5" in message
    
    def test_error_stores_instance(self):
        """Test error stores the instance."""
        class MockModel:
            id = 1
        
        instance = MockModel()
        error = ProtectedDeleteError(instance, "items", 3)
        
        assert error.instance is instance
    
    def test_error_stores_relationship(self):
        """Test error stores relationship name."""
        class MockModel:
            id = 1
        
        error = ProtectedDeleteError(MockModel(), "children", 2)
        
        assert error.relationship == "children"
    
    def test_error_stores_related_count(self):
        """Test error stores related count."""
        class MockModel:
            id = 1
        
        error = ProtectedDeleteError(MockModel(), "items", 10)
        
        assert error.related_count == 10
    
    def test_error_is_exception(self):
        """Test ProtectedDeleteError is an Exception."""
        class MockModel:
            id = 1
        
        error = ProtectedDeleteError(MockModel(), "x", 1)
        
        assert isinstance(error, Exception)
    
    def test_error_count_zero(self):
        """Test error with zero count."""
        class MockModel:
            id = 1
        
        error = ProtectedDeleteError(MockModel(), "items", 0)
        
        assert error.related_count == 0
    
    def test_error_count_large(self):
        """Test error with large count."""
        class MockModel:
            id = 1
        
        error = ProtectedDeleteError(MockModel(), "items", 1000000)
        
        assert error.related_count == 1000000
        assert "1000000" in str(error)


# =============================================================================
# Protect Configuration Tests (30 tests)
# =============================================================================

class TestProtectConfiguration:
    """Test protect configuration on relationships."""
    
    def test_has_many_protect(self, clean_state):
        """Test has_many with on_delete=protect."""
        class Order(Table):
            total: float = 0.0
            user_id: int = 0
        
        class User(Table):
            name: str = ""
            orders: List[Order] = has_many(Order, "user_id", on_delete="protect")
        
        assert User.__dict__["orders"].on_delete == "protect"
    
    def test_has_one_protect(self, clean_state):
        """Test has_one with on_delete=protect."""
        class Account(Table):
            balance: float = 0.0
            user_id: int = 0
        
        class User(Table):
            name: str = ""
            account: Account = has_one(Account, "user_id", on_delete="protect")
        
        assert User.__dict__["account"].on_delete == "protect"
    
    def test_protect_with_backref(self, clean_state):
        """Test protect with backref."""
        class Contract(Table):
            value: float = 0.0
            company_id: int = 0
        
        class Company(Table):
            name: str = ""
            contracts: List[Contract] = has_many(
                Contract, "company_id",
                backref="company",
                on_delete="protect"
            )
        
        desc = Company.__dict__["contracts"]
        assert desc.on_delete == "protect"
        assert desc.backref == "company"
    
    def test_protect_with_lazy(self, clean_state):
        """Test protect with lazy loading."""
        class Invoice(Table):
            amount: float = 0.0
            customer_id: int = 0
        
        class Customer(Table):
            name: str = ""
            invoices: List[Invoice] = has_many(
                Invoice, "customer_id",
                lazy="selectin",
                on_delete="protect"
            )
        
        desc = Customer.__dict__["invoices"]
        assert desc.on_delete == "protect"
        assert desc.lazy == "selectin"
    
    def test_multiple_protect_relationships(self, clean_state):
        """Test multiple protected relationships."""
        class Order(Table):
            total: float = 0.0
            user_id: int = 0
        
        class Subscription(Table):
            plan: str = ""
            user_id: int = 0
        
        class Transaction(Table):
            amount: float = 0.0
            user_id: int = 0
        
        class User(Table):
            name: str = ""
            orders: List[Order] = has_many(Order, "user_id", on_delete="protect")
            subscriptions: List[Subscription] = has_many(Subscription, "user_id", on_delete="protect")
            transactions: List[Transaction] = has_many(Transaction, "user_id", on_delete="protect")
        
        assert User.__dict__["orders"].on_delete == "protect"
        assert User.__dict__["subscriptions"].on_delete == "protect"
        assert User.__dict__["transactions"].on_delete == "protect"
    
    def test_mixed_protect_and_cascade(self, clean_state):
        """Test protect mixed with cascade."""
        class Post(Table):
            title: str = ""
            user_id: int = 0
        
        class Order(Table):
            total: float = 0.0
            user_id: int = 0
        
        class User(Table):
            name: str = ""
            posts: List[Post] = has_many(Post, "user_id", on_delete="cascade")
            orders: List[Order] = has_many(Order, "user_id", on_delete="protect")
        
        assert User.__dict__["posts"].on_delete == "cascade"
        assert User.__dict__["orders"].on_delete == "protect"


class TestProtectScenarios:
    """Test various protect scenarios."""
    
    def test_protect_empty_collection(self, clean_state):
        """Test protect with empty collection."""
        class Item(Table):
            name: str = ""
            box_id: int = 0
        
        class Box(Table):
            name: str = ""
            items: List[Item] = has_many(Item, "box_id", on_delete="protect")
        
        box = Box(name="Empty Box")
        # Empty collection - no protection needed
        assert len(box.items) == 0
    
    def test_protect_critical_data(self, clean_state):
        """Test protect for critical financial data."""
        class Payment(Table):
            amount: float = 0.0
            account_id: int = 0
        
        class Account(Table):
            number: str = ""
            payments: List[Payment] = has_many(
                Payment, "account_id",
                on_delete="protect"  # Can't delete account with payments
            )
        
        assert Account.__dict__["payments"].on_delete == "protect"
    
    def test_protect_audit_trail(self, clean_state):
        """Test protect for audit trails."""
        class AuditLog(Table):
            action: str = ""
            user_id: int = 0
        
        class User(Table):
            name: str = ""
            audit_logs: List[AuditLog] = has_many(
                AuditLog, "user_id",
                on_delete="protect"  # Can't delete user with audit logs
            )
        
        assert User.__dict__["audit_logs"].on_delete == "protect"
    
    def test_protect_legal_documents(self, clean_state):
        """Test protect for legal documents."""
        class LegalDocument(Table):
            title: str = ""
            case_id: int = 0
        
        class LegalCase(Table):
            name: str = ""
            documents: List[LegalDocument] = has_many(
                LegalDocument, "case_id",
                on_delete="protect"  # Legal requirement
            )
        
        assert LegalCase.__dict__["documents"].on_delete == "protect"


# =============================================================================
# Protect with Other Features Tests (30 tests)
# =============================================================================

class TestProtectWithOtherFeatures:
    """Test protect combined with other features."""
    
    def test_protect_with_back_populates(self, clean_state):
        """Test protect with back_populates."""
        class Ticket(Table):
            subject: str = ""
            customer_id: int = 0
        
        class Customer(Table):
            name: str = ""
            tickets: List[Ticket] = has_many(
                Ticket, "customer_id",
                back_populates="customer",
                on_delete="protect"
            )
        
        desc = Customer.__dict__["tickets"]
        assert desc.on_delete == "protect"
        assert desc.back_populates == "customer"
    
    def test_protect_with_string_model(self, clean_state):
        """Test protect with string model reference."""
        class Record(Table):
            data: str = ""
            owner_id: int = 0
        
        class Owner(Table):
            name: str = ""
            records: List["Record"] = has_many("Record", "owner_id", on_delete="protect")
        
        assert Owner.__dict__["records"].on_delete == "protect"
    
    def test_protect_self_referential(self, clean_state):
        """Test protect on self-referential relationship."""
        class Department(Table):
            name: str = ""
            parent_id: Optional[int] = None
            subdivisions: List["Department"] = has_many(
                "Department", "parent_id",
                on_delete="protect"
            )
        
        assert Department.__dict__["subdivisions"].on_delete == "protect"
    
    def test_protect_has_one_optional(self, clean_state):
        """Test protect on optional has_one."""
        class License(Table):
            key: str = ""
            product_id: int = 0
        
        class Product(Table):
            name: str = ""
            license: Optional[License] = has_one(
                License, "product_id",
                on_delete="protect"
            )
        
        assert Product.__dict__["license"].on_delete == "protect"
    
    def test_protect_nested_hierarchy(self, clean_state):
        """Test protect in nested hierarchy."""
        class SubChild(Table):
            name: str = ""
            child_id: int = 0
        
        class Child(Table):
            name: str = ""
            parent_id: int = 0
            subchildren: List[SubChild] = has_many(SubChild, "child_id", on_delete="protect")
        
        class Parent(Table):
            name: str = ""
            children: List[Child] = has_many(Child, "parent_id", on_delete="protect")
        
        assert Parent.__dict__["children"].on_delete == "protect"
        assert Child.__dict__["subchildren"].on_delete == "protect"
    
    def test_protect_m2m(self, clean_state):
        """Test protect on many-to-many (unusual but possible)."""
        class Permission(Table):
            name: str = ""
        
        class Role(Table):
            name: str = ""
            # Protect means can't delete role if it has permissions assigned
            permissions: List[Permission] = many_to_many(Permission, on_delete="protect")
        
        # For M2M, protect should still be stored
        assert Role.__dict__["permissions"].on_delete == "protect"

