"""
Test Phase 7.5: Self-Referential Relationships with Filters.

These tests verify that filters work correctly with self-referential relationships.
"""

import pytest
from datetime import datetime, timedelta
from typing import List, Optional

from pynext.db.relationships.conditions import (
    eq, ne, gt, gte, lt, lte,
    like, is_in, is_null,
)
from pynext.db.relationships.filter import RelationshipFilter
from pynext.db.relationships.core import (
    has_many,
    has_one,
    belongs_to,
)


# =============================================================================
# Test Self-Referential has_many with Filter
# =============================================================================

class TestSelfRefHasManyFilter:
    """Test self-referential has_many with filters."""
    
    def test_self_ref_has_many_active_children(self):
        """Self-referential has_many with active filter."""
        # Category with active subcategories
        hm = has_many(
            "Category",  # Same model (self-ref)
            foreign_key="parent_id",
            filter=[eq("is_active", True)],
        )
        assert hm._model == "Category"
        assert hm.filter is not None
        assert hm.filter.conditions[0].field == "is_active"
    
    def test_self_ref_has_many_visible_children(self):
        """Self-referential with non-deleted filter."""
        hm = has_many(
            "Category",
            foreign_key="parent_id",
            filter=[is_null("deleted_at")],
        )
        assert hm.filter.conditions[0].operator == "IS NULL"
    
    def test_self_ref_has_many_sorted_children(self):
        """Self-referential with ordering filter (position > 0)."""
        hm = has_many(
            "MenuItem",
            foreign_key="parent_id",
            filter=[gt("position", 0)],
        )
        assert hm.filter.conditions[0].field == "position"
    
    def test_self_ref_has_many_multiple_filters(self):
        """Self-referential with multiple filters."""
        hm = has_many(
            "Comment",
            foreign_key="parent_id",
            filter=[
                eq("is_approved", True),
                is_null("deleted_at"),
                gte("upvotes", 0),
            ],
        )
        assert len(hm.filter.conditions) == 3
    
    def test_self_ref_has_many_type_filter(self):
        """Self-referential with type filter."""
        hm = has_many(
            "Node",
            foreign_key="parent_id",
            filter=[is_in("type", ["folder", "document"])],
        )
        assert hm.filter.conditions[0].value == ["folder", "document"]


# =============================================================================
# Test Self-Referential belongs_to with Filter
# =============================================================================

class TestSelfRefBelongsToFilter:
    """Test self-referential belongs_to with filters."""
    
    def test_self_ref_belongs_to_active_parent(self):
        """Self-referential belongs_to with active parent."""
        bt = belongs_to(
            "Category",  # Same model
            foreign_key="parent_id",
            filter=[eq("is_active", True)],
        )
        assert bt._model == "Category"
        assert bt.filter is not None
    
    def test_self_ref_belongs_to_verified_parent(self):
        """Self-referential with verified parent."""
        bt = belongs_to(
            "User",
            foreign_key="manager_id",
            filter=[eq("verified", True)],
        )
        assert bt.filter.conditions[0].field == "verified"
    
    def test_self_ref_belongs_to_non_deleted(self):
        """Self-referential with non-deleted parent."""
        bt = belongs_to(
            "Page",
            foreign_key="parent_page_id",
            filter=[is_null("deleted_at")],
        )
        assert bt.filter.conditions[0].operator == "IS NULL"


# =============================================================================
# Test Self-Referential has_one with Filter
# =============================================================================

class TestSelfRefHasOneFilter:
    """Test self-referential has_one with filters."""
    
    def test_self_ref_has_one_primary_child(self):
        """Self-referential has_one with primary filter."""
        ho = has_one(
            "Node",
            foreign_key="parent_id",
            filter=[eq("is_primary", True)],
        )
        assert ho.filter is not None
    
    def test_self_ref_has_one_featured_child(self):
        """Self-referential has_one for featured child."""
        ho = has_one(
            "Product",
            foreign_key="parent_id",
            filter=[eq("featured", True)],
        )
        assert ho.filter.conditions[0].field == "featured"


# =============================================================================
# Test Parent-Child Hierarchy Patterns
# =============================================================================

class TestHierarchyPatterns:
    """Test common parent-child hierarchy patterns with filters."""
    
    def test_category_active_subcategories(self):
        """Category with active subcategories."""
        # Simulates: class Category(Table):
        #     subcategories = has_many("Category", filter=[eq("active", True)])
        hm = has_many(
            "Category",
            foreign_key="parent_id",
            filter=[eq("is_active", True)],
        )
        assert hm._model == "Category"
    
    def test_employee_direct_reports(self):
        """Employee with active direct reports."""
        hm = has_many(
            "Employee",
            foreign_key="manager_id",
            filter=[
                eq("is_active", True),
                ne("status", "terminated"),
            ],
        )
        assert len(hm.filter.conditions) == 2
    
    def test_org_visible_children(self):
        """Organization unit with visible children."""
        hm = has_many(
            "OrgUnit",
            foreign_key="parent_id",
            filter=[
                eq("is_visible", True),
                is_null("deleted_at"),
            ],
        )
        assert len(hm.filter.conditions) == 2
    
    def test_comment_approved_replies(self):
        """Comment with approved replies."""
        hm = has_many(
            "Comment",
            foreign_key="parent_id",
            filter=[eq("is_approved", True)],
        )
        assert hm.filter.conditions[0].value is True
    
    def test_folder_non_archived_items(self):
        """Folder with non-archived items."""
        hm = has_many(
            "Item",
            foreign_key="folder_id",
            filter=[ne("status", "archived")],
        )
        assert hm.filter.conditions[0].operator == "!="


# =============================================================================
# Test Self-Referential with Loading Strategies
# =============================================================================

class TestSelfRefWithLoading:
    """Test self-referential relationships with filters and loading."""
    
    def test_self_ref_selectin_with_filter(self):
        """Self-referential with selectin loading and filter."""
        hm = has_many(
            "Category",
            foreign_key="parent_id",
            lazy="selectin",
            filter=[eq("is_active", True)],
        )
        assert hm.lazy == "selectin"
        assert hm.filter is not None
    
    def test_self_ref_dynamic_with_filter(self):
        """Self-referential with dynamic loading and filter."""
        hm = has_many(
            "Comment",
            foreign_key="parent_id",
            lazy="dynamic",
            filter=[eq("is_approved", True)],
        )
        assert hm.lazy == "dynamic"
    
    def test_self_ref_raise_with_filter(self):
        """Self-referential with raise loading and filter."""
        hm = has_many(
            "Node",
            foreign_key="parent_id",
            lazy="raise",
            filter=[eq("is_visible", True)],
        )
        assert hm.lazy == "raise"
    
    def test_self_ref_belongs_to_joined_with_filter(self):
        """Self-referential belongs_to with joined loading and filter."""
        bt = belongs_to(
            "Category",
            foreign_key="parent_id",
            lazy="joined",
            filter=[eq("is_active", True)],
        )
        assert bt.lazy == "joined"


# =============================================================================
# Test Self-Referential with Backref and Filter
# =============================================================================

class TestSelfRefWithBackrefFilter:
    """Test self-referential with backref and filter."""
    
    def test_self_ref_with_backref_and_filter(self):
        """Self-referential has_many with backref and filter."""
        hm = has_many(
            "Category",
            foreign_key="parent_id",
            backref="parent",
            filter=[eq("is_active", True)],
        )
        assert hm.backref == "parent"
        assert hm.filter is not None
    
    def test_self_ref_with_back_populates_and_filter(self):
        """Self-referential with back_populates and filter."""
        hm = has_many(
            "Comment",
            foreign_key="parent_id",
            back_populates="parent",
            filter=[eq("is_approved", True)],
        )
        assert hm.back_populates == "parent"


# =============================================================================
# Test Real-World Self-Referential Scenarios
# =============================================================================

class TestRealWorldSelfRef:
    """Test real-world self-referential scenarios."""
    
    def test_menu_item_visible_children(self):
        """Menu item with visible children."""
        hm = has_many(
            "MenuItem",
            foreign_key="parent_id",
            filter=[
                eq("is_visible", True),
                gte("position", 0),
            ],
        )
        assert len(hm.filter.conditions) == 2
    
    def test_category_published_subcategories(self):
        """Category with published subcategories."""
        hm = has_many(
            "Category",
            foreign_key="parent_id",
            filter=[
                eq("status", "published"),
                is_null("deleted_at"),
            ],
        )
        assert hm.filter.conditions[0].value == "published"
    
    def test_page_visible_subpages(self):
        """Page with visible subpages."""
        hm = has_many(
            "Page",
            foreign_key="parent_id",
            filter=[
                eq("is_published", True),
                is_null("archived_at"),
            ],
        )
        assert len(hm.filter.conditions) == 2
    
    def test_thread_not_spam_replies(self):
        """Thread with non-spam replies."""
        hm = has_many(
            "Message",
            foreign_key="thread_id",
            filter=[
                eq("is_spam", False),
                is_null("deleted_at"),
            ],
        )
        assert hm.filter.conditions[0].value is False
    
    def test_task_incomplete_subtasks(self):
        """Task with incomplete subtasks."""
        hm = has_many(
            "Task",
            foreign_key="parent_task_id",
            filter=[
                ne("status", "completed"),
                ne("status", "cancelled"),
            ],
        )
        assert len(hm.filter.conditions) == 2


# =============================================================================
# Test Mutual Self-References
# =============================================================================

class TestMutualSelfRef:
    """Test mutual self-referential patterns."""
    
    def test_user_active_friends(self):
        """User's active friends (mutual relationship)."""
        # user.friends would be many_to_many with self
        # but for simplicity, testing has_many pattern
        hm = has_many(
            "Friendship",
            foreign_key="user_id",
            filter=[eq("is_active", True)],
        )
        assert hm.filter is not None
    
    def test_node_connected_nodes(self):
        """Node with connected active nodes."""
        hm = has_many(
            "NodeConnection",
            foreign_key="from_node_id",
            filter=[
                eq("is_active", True),
                gte("weight", 0),
            ],
        )
        assert len(hm.filter.conditions) == 2

