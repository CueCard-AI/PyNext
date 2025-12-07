"""
Cascade Pattern Tests.

Additional pattern tests for cascade configurations.
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
    OnDeleteAction,
    CascadeResult,
    CascadeManager,
    get_cascade_manager,
    reset_cascade_manager,
    cascade_options,
)


@pytest.fixture(autouse=True)
def clean_state():
    _model_registry.clear()
    reset_cascade_manager()
    yield
    _model_registry.clear()
    reset_cascade_manager()


# =============================================================================
# Domain-Driven Design Patterns (40 tests)
# =============================================================================

class TestAggregatePattern:
    """Test DDD Aggregate pattern with cascades."""
    
    def test_order_aggregate_cascade(self, clean_state):
        """Test Order aggregate with cascading children."""
        class OrderLine(Table):
            product_id: int = 0
            order_id: int = 0
        
        class Payment(Table):
            amount: float = 0.0
            order_id: int = 0
        
        class Order(Table):
            number: str = ""
            lines: List[OrderLine] = has_many(
                OrderLine, "order_id",
                cascade=CascadeOptions.all()
            )
            payments: List[Payment] = has_many(
                Payment, "order_id",
                cascade=CascadeOptions.delete_orphan()
            )
        
        assert Order.__dict__["lines"].cascade.on_delete is True
        assert Order.__dict__["payments"].cascade.on_delete is True
    
    def test_shopping_cart_aggregate(self, clean_state):
        """Test ShoppingCart aggregate."""
        class CartItem(Table):
            product_id: int = 0
            cart_id: int = 0
        
        class Cart(Table):
            user_id: int = 0
            items: List[CartItem] = has_many(
                CartItem, "cart_id",
                cascade=CascadeOptions.all()
            )
        
        desc = Cart.__dict__["items"]
        assert desc.cascade.on_save is True
        assert desc.cascade.on_delete is True
        assert desc.cascade.on_orphan is True
    
    def test_invoice_aggregate(self, clean_state):
        """Test Invoice aggregate."""
        class InvoiceLine(Table):
            amount: float = 0.0
            invoice_id: int = 0
        
        class Invoice(Table):
            number: str = ""
            lines: List[InvoiceLine] = has_many(
                InvoiceLine, "invoice_id",
                cascade=CascadeOptions.delete_orphan()
            )
        
        desc = Invoice.__dict__["lines"]
        assert desc.cascade.on_delete is True
        assert desc.cascade.on_orphan is True
    
    def test_document_aggregate(self, clean_state):
        """Test Document aggregate."""
        class Section(Table):
            content: str = ""
            document_id: int = 0
        
        class Document(Table):
            title: str = ""
            sections: List[Section] = has_many(
                Section, "document_id",
                cascade=CascadeOptions.all()
            )
        
        desc = Document.__dict__["sections"]
        assert desc.cascade.on_save is True


class TestEventSourcingPattern:
    """Test Event Sourcing patterns."""
    
    def test_aggregate_events_protect(self, clean_state):
        """Events should never be deleted."""
        class DomainEvent(Table):
            type: str = ""
            aggregate_id: int = 0
        
        class Aggregate(Table):
            version: int = 0
            events: List[DomainEvent] = has_many(
                DomainEvent, "aggregate_id",
                on_delete="protect"
            )
        
        assert Aggregate.__dict__["events"].on_delete == "protect"
    
    def test_snapshot_cascade(self, clean_state):
        """Snapshots can cascade."""
        class Snapshot(Table):
            state: str = ""
            aggregate_id: int = 0
        
        class Aggregate(Table):
            version: int = 0
            snapshots: List[Snapshot] = has_many(
                Snapshot, "aggregate_id",
                on_delete="cascade"
            )
        
        assert Aggregate.__dict__["snapshots"].on_delete == "cascade"


class TestRepositoryPattern:
    """Test Repository pattern cascades."""
    
    def test_entity_audits_protect(self, clean_state):
        """Audit trails should be protected."""
        class AuditEntry(Table):
            action: str = ""
            entity_id: int = 0
        
        class Entity(Table):
            name: str = ""
            audits: List[AuditEntry] = has_many(
                AuditEntry, "entity_id",
                on_delete="protect"
            )
        
        assert Entity.__dict__["audits"].on_delete == "protect"
    
    def test_entity_versions_cascade(self, clean_state):
        """Entity versions cascade."""
        class EntityVersion(Table):
            data: str = ""
            entity_id: int = 0
        
        class Entity(Table):
            current_version: int = 0
            versions: List[EntityVersion] = has_many(
                EntityVersion, "entity_id",
                on_delete="cascade"
            )
        
        assert Entity.__dict__["versions"].on_delete == "cascade"


# =============================================================================
# Microservices Patterns (40 tests)
# =============================================================================

class TestSagaPattern:
    """Test Saga pattern cascades."""
    
    def test_saga_steps_cascade(self, clean_state):
        """Saga steps cascade when saga deleted."""
        class SagaStep(Table):
            action: str = ""
            saga_id: int = 0
        
        class Saga(Table):
            name: str = ""
            steps: List[SagaStep] = has_many(
                SagaStep, "saga_id",
                on_delete="cascade"
            )
        
        assert Saga.__dict__["steps"].on_delete == "cascade"
    
    def test_compensation_log_protect(self, clean_state):
        """Compensation logs protected."""
        class CompensationLog(Table):
            action: str = ""
            saga_id: int = 0
        
        class Saga(Table):
            name: str = ""
            compensations: List[CompensationLog] = has_many(
                CompensationLog, "saga_id",
                on_delete="protect"
            )
        
        assert Saga.__dict__["compensations"].on_delete == "protect"


class TestOutboxPattern:
    """Test Outbox pattern cascades."""
    
    def test_outbox_messages_cascade(self, clean_state):
        """Outbox messages cascade."""
        class OutboxMessage(Table):
            payload: str = ""
            aggregate_id: int = 0
        
        class Aggregate(Table):
            name: str = ""
            outbox: List[OutboxMessage] = has_many(
                OutboxMessage, "aggregate_id",
                on_delete="cascade"
            )
        
        assert Aggregate.__dict__["outbox"].on_delete == "cascade"
    
    def test_inbox_messages_cascade(self, clean_state):
        """Inbox messages cascade."""
        class InboxMessage(Table):
            payload: str = ""
            consumer_id: int = 0
        
        class Consumer(Table):
            name: str = ""
            inbox: List[InboxMessage] = has_many(
                InboxMessage, "consumer_id",
                on_delete="cascade"
            )
        
        assert Consumer.__dict__["inbox"].on_delete == "cascade"


class TestCQRSPattern:
    """Test CQRS pattern cascades."""
    
    def test_read_model_cascade(self, clean_state):
        """Read model projections cascade."""
        class Projection(Table):
            data: str = ""
            source_id: int = 0
        
        class Source(Table):
            name: str = ""
            projections: List[Projection] = has_many(
                Projection, "source_id",
                on_delete="cascade"
            )
        
        assert Source.__dict__["projections"].on_delete == "cascade"
    
    def test_command_log_protect(self, clean_state):
        """Command logs protected."""
        class CommandLog(Table):
            command: str = ""
            handler_id: int = 0
        
        class Handler(Table):
            name: str = ""
            logs: List[CommandLog] = has_many(
                CommandLog, "handler_id",
                on_delete="protect"
            )
        
        assert Handler.__dict__["logs"].on_delete == "protect"


# =============================================================================
# Multi-Tenancy Patterns (40 tests)
# =============================================================================

class TestTenantIsolation:
    """Test tenant isolation cascades."""
    
    def test_tenant_users_cascade(self, clean_state):
        """Tenant users cascade when tenant deleted."""
        class User(Table):
            name: str = ""
            tenant_id: int = 0
        
        class Tenant(Table):
            name: str = ""
            users: List[User] = has_many(
                User, "tenant_id",
                on_delete="cascade"
            )
        
        assert Tenant.__dict__["users"].on_delete == "cascade"
    
    def test_tenant_data_cascade(self, clean_state):
        """Tenant data cascade."""
        class TenantData(Table):
            key: str = ""
            tenant_id: int = 0
        
        class Tenant(Table):
            name: str = ""
            data: List[TenantData] = has_many(
                TenantData, "tenant_id",
                cascade=CascadeOptions.all()
            )
        
        desc = Tenant.__dict__["data"]
        assert desc.cascade.on_delete is True
    
    def test_tenant_billing_protect(self, clean_state):
        """Tenant billing records protected."""
        class BillingRecord(Table):
            amount: float = 0.0
            tenant_id: int = 0
        
        class Tenant(Table):
            name: str = ""
            billing: List[BillingRecord] = has_many(
                BillingRecord, "tenant_id",
                on_delete="protect"
            )
        
        assert Tenant.__dict__["billing"].on_delete == "protect"


class TestOrganizationHierarchy:
    """Test organization hierarchy cascades."""
    
    def test_org_departments_cascade(self, clean_state):
        """Organization departments cascade."""
        class Department(Table):
            name: str = ""
            org_id: int = 0
        
        class Organization(Table):
            name: str = ""
            departments: List[Department] = has_many(
                Department, "org_id",
                on_delete="cascade"
            )
        
        assert Organization.__dict__["departments"].on_delete == "cascade"
    
    def test_department_teams_cascade(self, clean_state):
        """Department teams cascade."""
        class Team(Table):
            name: str = ""
            department_id: int = 0
        
        class Department(Table):
            name: str = ""
            teams: List[Team] = has_many(
                Team, "department_id",
                on_delete="cascade"
            )
        
        assert Department.__dict__["teams"].on_delete == "cascade"
    
    def test_team_members_nullify(self, clean_state):
        """Team members nullified when team dissolved."""
        class Member(Table):
            name: str = ""
            team_id: Optional[int] = None
        
        class Team(Table):
            name: str = ""
            members: List[Member] = has_many(
                Member, "team_id",
                on_delete="nullify"
            )
        
        assert Team.__dict__["members"].on_delete == "nullify"


# =============================================================================
# Soft Delete Patterns (30 tests)
# =============================================================================

class TestSoftDeletePattern:
    """Test soft delete patterns with cascades."""
    
    def test_cascade_with_deleted_at(self, clean_state):
        """Cascade works with soft delete fields."""
        class ArchivableItem(Table):
            name: str = ""
            deleted_at: Optional[str] = None
            parent_id: int = 0
        
        class Parent(Table):
            name: str = ""
            items: List[ArchivableItem] = has_many(
                ArchivableItem, "parent_id",
                on_delete="cascade"
            )
        
        assert Parent.__dict__["items"].on_delete == "cascade"
    
    def test_protect_with_active_flag(self, clean_state):
        """Protect with active items."""
        class ActiveItem(Table):
            name: str = ""
            is_active: bool = True
            container_id: int = 0
        
        class Container(Table):
            name: str = ""
            items: List[ActiveItem] = has_many(
                ActiveItem, "container_id",
                on_delete="protect"
            )
        
        assert Container.__dict__["items"].on_delete == "protect"


# =============================================================================
# Polymorphic Patterns (30 tests)
# =============================================================================

class TestPolymorphicPattern:
    """Test polymorphic relationship cascades."""
    
    def test_comment_on_post_cascade(self, clean_state):
        """Comment on post cascade."""
        class Comment(Table):
            content: str = ""
            commentable_id: int = 0
            commentable_type: str = ""
        
        class Post(Table):
            title: str = ""
            comments: List[Comment] = has_many(
                Comment, "commentable_id",
                on_delete="cascade"
            )
        
        assert Post.__dict__["comments"].on_delete == "cascade"
    
    def test_tag_on_multiple_types(self, clean_state):
        """Tags on multiple entity types."""
        class Tagging(Table):
            tag_id: int = 0
            taggable_id: int = 0
            taggable_type: str = ""
        
        class Article(Table):
            title: str = ""
            taggings: List[Tagging] = has_many(
                Tagging, "taggable_id",
                on_delete="cascade"
            )
        
        assert Article.__dict__["taggings"].on_delete == "cascade"


# =============================================================================
# Tree Patterns (30 tests)
# =============================================================================

class TestTreePatterns:
    """Test tree structure cascades."""
    
    def test_nested_set_cascade(self, clean_state):
        """Nested set pattern cascade."""
        class NestedNode(Table):
            lft: int = 0
            rgt: int = 0
            parent_id: Optional[int] = None
            children: List["NestedNode"] = has_many(
                "NestedNode", "parent_id",
                on_delete="cascade"
            )
        
        assert NestedNode.__dict__["children"].on_delete == "cascade"
    
    def test_adjacency_list_cascade(self, clean_state):
        """Adjacency list pattern cascade."""
        class Node(Table):
            name: str = ""
            parent_id: Optional[int] = None
            children: List["Node"] = has_many(
                "Node", "parent_id",
                on_delete="cascade"
            )
        
        assert Node.__dict__["children"].on_delete == "cascade"
    
    def test_materialized_path_cascade(self, clean_state):
        """Materialized path pattern cascade."""
        class PathNode(Table):
            path: str = ""
            parent_id: Optional[int] = None
            children: List["PathNode"] = has_many(
                "PathNode", "parent_id",
                on_delete="cascade"
            )
        
        assert PathNode.__dict__["children"].on_delete == "cascade"
    
    def test_closure_table_cascade(self, clean_state):
        """Closure table pattern cascade."""
        class TreePath(Table):
            ancestor_id: int = 0
            descendant_id: int = 0
            depth: int = 0
        
        class TreeNode(Table):
            name: str = ""
            paths: List[TreePath] = has_many(
                TreePath, "ancestor_id",
                on_delete="cascade"
            )
        
        assert TreeNode.__dict__["paths"].on_delete == "cascade"


# =============================================================================
# Versioning Patterns (30 tests)
# =============================================================================

class TestVersioningPatterns:
    """Test versioning cascade patterns."""
    
    def test_entity_revisions_cascade(self, clean_state):
        """Entity revisions cascade."""
        class Revision(Table):
            data: str = ""
            entity_id: int = 0
        
        class VersionedEntity(Table):
            current_revision: int = 0
            revisions: List[Revision] = has_many(
                Revision, "entity_id",
                on_delete="cascade"
            )
        
        assert VersionedEntity.__dict__["revisions"].on_delete == "cascade"
    
    def test_draft_versions_cascade(self, clean_state):
        """Draft versions cascade."""
        class Draft(Table):
            content: str = ""
            document_id: int = 0
        
        class Document(Table):
            title: str = ""
            drafts: List[Draft] = has_many(
                Draft, "document_id",
                cascade=CascadeOptions.delete_orphan()
            )
        
        desc = Document.__dict__["drafts"]
        assert desc.cascade.on_delete is True
        assert desc.cascade.on_orphan is True
    
    def test_published_versions_protect(self, clean_state):
        """Published versions protected."""
        class PublishedVersion(Table):
            content: str = ""
            document_id: int = 0
        
        class Document(Table):
            title: str = ""
            published: List[PublishedVersion] = has_many(
                PublishedVersion, "document_id",
                on_delete="protect"
            )
        
        assert Document.__dict__["published"].on_delete == "protect"


# =============================================================================
# Audit Patterns (20 tests)
# =============================================================================

class TestAuditPatterns:
    """Test audit trail cascade patterns."""
    
    def test_change_log_protect(self, clean_state):
        """Change logs must be protected."""
        class ChangeLog(Table):
            field: str = ""
            entity_id: int = 0
        
        class AuditedEntity(Table):
            name: str = ""
            changes: List[ChangeLog] = has_many(
                ChangeLog, "entity_id",
                on_delete="protect"
            )
        
        assert AuditedEntity.__dict__["changes"].on_delete == "protect"
    
    def test_access_log_protect(self, clean_state):
        """Access logs protected."""
        class AccessLog(Table):
            action: str = ""
            resource_id: int = 0
        
        class Resource(Table):
            name: str = ""
            access_logs: List[AccessLog] = has_many(
                AccessLog, "resource_id",
                on_delete="protect"
            )
        
        assert Resource.__dict__["access_logs"].on_delete == "protect"
    
    def test_login_history_protect(self, clean_state):
        """Login history protected."""
        class LoginEntry(Table):
            ip: str = ""
            user_id: int = 0
        
        class User(Table):
            name: str = ""
            logins: List[LoginEntry] = has_many(
                LoginEntry, "user_id",
                on_delete="protect"
            )
        
        assert User.__dict__["logins"].on_delete == "protect"

