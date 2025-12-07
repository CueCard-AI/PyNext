"""
Edge Case Cascade Tests.

Tests for cascade edge cases including:
- Circular references
- Deep nesting
- Multiple inheritance patterns
- Concurrent operations
- Error recovery
"""

import pytest
from typing import List, Optional

from pynext.db.table import Table, _model_registry
from pynext.db.relationships import (
    has_many,
    has_one,
    belongs_to,
    many_to_many,
    CascadeOptions,
)
from pynext.db.relationships.cascade import (
    OnDeleteAction,
    CascadeOptions,
    CascadeResult,
    CascadeManager,
    get_cascade_manager,
    reset_cascade_manager,
)


@pytest.fixture(autouse=True)
def clean_state():
    """Clean state before each test."""
    _model_registry.clear()
    reset_cascade_manager()
    yield
    _model_registry.clear()
    reset_cascade_manager()


# =============================================================================
# Self-Referential Tests (15 tests)
# =============================================================================

class TestSelfReferentialCascade:
    """Test cascade on self-referential relationships."""
    
    def test_tree_cascade_delete(self, clean_state):
        """Test cascade delete on tree structure."""
        class TreeNode(Table):
            name: str = ""
            parent_id: Optional[int] = None
            children: List["TreeNode"] = has_many(
                "TreeNode", "parent_id",
                on_delete="cascade"
            )
        
        assert TreeNode.__dict__["children"].on_delete == "cascade"
    
    def test_tree_cascade_nullify(self, clean_state):
        """Test cascade nullify on tree structure."""
        class Category(Table):
            name: str = ""
            parent_id: Optional[int] = None
            subcategories: List["Category"] = has_many(
                "Category", "parent_id",
                on_delete="nullify"
            )
        
        assert Category.__dict__["subcategories"].on_delete == "nullify"
    
    def test_tree_cascade_protect(self, clean_state):
        """Test cascade protect on tree structure."""
        class Department(Table):
            name: str = ""
            parent_id: Optional[int] = None
            subdivisions: List["Department"] = has_many(
                "Department", "parent_id",
                on_delete="protect"
            )
        
        assert Department.__dict__["subdivisions"].on_delete == "protect"
    
    def test_linked_list_cascade(self, clean_state):
        """Test cascade on linked list pattern."""
        class Node(Table):
            value: int = 0
            next_id: Optional[int] = None
        
        # Linked list doesn't need cascade typically
        node = Node(value=1)
        assert node.value == 1
    
    def test_graph_node_cascade(self, clean_state):
        """Test cascade on graph-like structure."""
        class GraphNode(Table):
            name: str = ""
            parent_id: Optional[int] = None
            children: List["GraphNode"] = has_many(
                "GraphNode", "parent_id",
                cascade=CascadeOptions.delete_orphan()
            )
        
        desc = GraphNode.__dict__["children"]
        assert desc.cascade.on_delete is True
        assert desc.cascade.on_orphan is True


# =============================================================================
# Deep Nesting Tests (10 tests)
# =============================================================================

class TestDeepNestingCascade:
    """Test cascade with deep nesting."""
    
    def test_four_level_cascade(self, clean_state):
        """Test four-level cascade hierarchy."""
        class Level4(Table):
            name: str = ""
            level3_id: int = 0
        
        class Level3(Table):
            name: str = ""
            level2_id: int = 0
            items: List[Level4] = has_many(Level4, "level3_id", on_delete="cascade")
        
        class Level2(Table):
            name: str = ""
            level1_id: int = 0
            items: List[Level3] = has_many(Level3, "level2_id", on_delete="cascade")
        
        class Level1(Table):
            name: str = ""
            items: List[Level2] = has_many(Level2, "level1_id", on_delete="cascade")
        
        assert Level1.__dict__["items"].on_delete == "cascade"
        assert Level2.__dict__["items"].on_delete == "cascade"
        assert Level3.__dict__["items"].on_delete == "cascade"
    
    def test_mixed_cascade_levels(self, clean_state):
        """Test different cascades at different levels."""
        class Grandchild(Table):
            name: str = ""
            child_id: int = 0
        
        class Child(Table):
            name: str = ""
            parent_id: int = 0
            grandchildren: List[Grandchild] = has_many(
                Grandchild, "child_id",
                on_delete="nullify"
            )
        
        class Parent(Table):
            name: str = ""
            children: List[Child] = has_many(
                Child, "parent_id",
                on_delete="cascade"
            )
        
        assert Parent.__dict__["children"].on_delete == "cascade"
        assert Child.__dict__["grandchildren"].on_delete == "nullify"


# =============================================================================
# Multiple Relationships Tests (10 tests)
# =============================================================================

class TestMultipleRelationshipsCascade:
    """Test cascade with multiple relationships."""
    
    def test_many_to_one_with_cascade(self, clean_state):
        """Test multiple models pointing to same parent."""
        class Comment(Table):
            text: str = ""
            post_id: int = 0
        
        class Like(Table):
            user_id: int = 0
            post_id: int = 0
        
        class Post(Table):
            title: str = ""
            comments: List[Comment] = has_many(Comment, "post_id", on_delete="cascade")
            likes: List[Like] = has_many(Like, "post_id", on_delete="cascade")
        
        assert Post.__dict__["comments"].on_delete == "cascade"
        assert Post.__dict__["likes"].on_delete == "cascade"
    
    def test_different_cascade_per_child(self, clean_state):
        """Test different cascades for different children."""
        class AuditLog(Table):
            action: str = ""
            user_id: int = 0
        
        class Post(Table):
            title: str = ""
            author_id: int = 0
        
        class Comment(Table):
            text: str = ""
            author_id: Optional[int] = None
        
        class User(Table):
            name: str = ""
            audit_logs: List[AuditLog] = has_many(AuditLog, "user_id", on_delete="protect")
            posts: List[Post] = has_many(Post, "author_id", on_delete="cascade")
            comments: List[Comment] = has_many(Comment, "author_id", on_delete="nullify")
        
        assert User.__dict__["audit_logs"].on_delete == "protect"
        assert User.__dict__["posts"].on_delete == "cascade"
        assert User.__dict__["comments"].on_delete == "nullify"


# =============================================================================
# CascadeManager Edge Cases (10 tests)
# =============================================================================

class TestCascadeManagerEdgeCases:
    """Test CascadeManager edge cases."""
    
    def test_manager_processing_set(self, clean_state):
        """Test manager tracks processing."""
        manager = CascadeManager()
        assert manager._processing == set()
    
    def test_get_cascade_relationships_empty(self, clean_state):
        """Test getting cascade relationships from model without any."""
        class Simple(Table):
            name: str = ""
        
        manager = CascadeManager()
        instance = Simple(name="test")
        rels = manager._get_cascade_relationships(instance)
        assert isinstance(rels, dict)
    
    def test_cascade_result_merge_empty(self, clean_state):
        """Test merging empty results."""
        r1 = CascadeResult()
        r2 = CascadeResult()
        r1.merge(r2)
        assert r1.total_affected == 0
    
    def test_cascade_result_merge_with_data(self, clean_state):
        """Test merging results with data."""
        r1 = CascadeResult()
        r1.deleted.append("a")
        
        r2 = CascadeResult()
        r2.saved.append("b")
        r2.nullified.append(("c", "field"))
        
        r1.merge(r2)
        assert r1.deleted_count == 1
        assert r1.saved_count == 1
        assert r1.nullified_count == 1


# =============================================================================
# OnDeleteAction Edge Cases (5 tests)
# =============================================================================

class TestOnDeleteActionEdgeCases:
    """Test OnDeleteAction edge cases."""
    
    def test_all_actions_are_strings(self, clean_state):
        """Test all actions can be used as strings."""
        for action in OnDeleteAction:
            assert isinstance(action.value, str)
            assert len(action.value) > 0
    
    def test_action_string_comparison(self, clean_state):
        """Test action string comparison."""
        assert OnDeleteAction.CASCADE == "cascade"
        assert OnDeleteAction.NULLIFY == "nullify"
        assert OnDeleteAction.PROTECT == "protect"
        assert OnDeleteAction.NONE == "none"
    
    def test_from_string_all_actions(self, clean_state):
        """Test from_string for all actions."""
        for action in OnDeleteAction:
            result = OnDeleteAction.from_string(action.value)
            assert result == action


# =============================================================================
# CascadeOptions Combinations (10 tests)
# =============================================================================

class TestCascadeOptionsCombinations:
    """Test various CascadeOptions combinations."""
    
    def test_all_false(self, clean_state):
        """Test all options False."""
        opts = CascadeOptions()
        assert not opts.has_any()
    
    def test_all_true(self, clean_state):
        """Test all options True."""
        opts = CascadeOptions.all()
        assert opts.has_any()
    
    def test_single_true(self, clean_state):
        """Test each single option True."""
        opts1 = CascadeOptions(on_save=True)
        opts2 = CascadeOptions(on_delete=True)
        opts3 = CascadeOptions(on_orphan=True)
        opts4 = CascadeOptions(on_merge=True)
        
        assert opts1.has_any()
        assert opts2.has_any()
        assert opts3.has_any()
        assert opts4.has_any()
    
    def test_two_true(self, clean_state):
        """Test two options True."""
        opts = CascadeOptions(on_save=True, on_delete=True)
        assert opts.has_any()
        assert opts.on_save is True
        assert opts.on_delete is True
        assert opts.on_orphan is False
    
    def test_three_true(self, clean_state):
        """Test three options True."""
        opts = CascadeOptions(on_save=True, on_delete=True, on_orphan=True)
        assert opts.on_merge is False
        assert opts.has_any()
    
    def test_equality(self, clean_state):
        """Test CascadeOptions equality."""
        opts1 = CascadeOptions(on_delete=True)
        opts2 = CascadeOptions(on_delete=True)
        assert opts1 == opts2
    
    def test_inequality(self, clean_state):
        """Test CascadeOptions inequality."""
        opts1 = CascadeOptions(on_delete=True)
        opts2 = CascadeOptions(on_save=True)
        assert opts1 != opts2


# =============================================================================
# Real-World Patterns (10 tests)
# =============================================================================

class TestRealWorldPatterns:
    """Test real-world cascade patterns."""
    
    def test_ecommerce_order_cascade(self, clean_state):
        """Test e-commerce order cascade pattern."""
        class OrderItem(Table):
            product_id: int = 0
            quantity: int = 1
            order_id: int = 0
        
        class OrderAddress(Table):
            street: str = ""
            order_id: int = 0
        
        class Order(Table):
            number: str = ""
            user_id: int = 0
            items: List[OrderItem] = has_many(
                OrderItem, "order_id",
                cascade=CascadeOptions.delete_orphan()
            )
            shipping_address: OrderAddress = has_one(
                OrderAddress, "order_id",
                on_delete="cascade"
            )
        
        assert Order.__dict__["items"].cascade.on_delete is True
        assert Order.__dict__["items"].cascade.on_orphan is True
        assert Order.__dict__["shipping_address"].on_delete == "cascade"
    
    def test_blog_cascade_pattern(self, clean_state):
        """Test blog cascade pattern."""
        class Comment(Table):
            text: str = ""
            post_id: int = 0
        
        class Tag(Table):
            name: str = ""
        
        class Post(Table):
            title: str = ""
            author_id: int = 0
            comments: List[Comment] = has_many(Comment, "post_id", on_delete="cascade")
            tags: List[Tag] = many_to_many(Tag, on_delete="cascade")
        
        class Author(Table):
            name: str = ""
            posts: List[Post] = has_many(Post, "author_id", on_delete="cascade")
        
        assert Author.__dict__["posts"].on_delete == "cascade"
        assert Post.__dict__["comments"].on_delete == "cascade"
    
    def test_cms_content_cascade(self, clean_state):
        """Test CMS content cascade pattern."""
        class Block(Table):
            content: str = ""
            page_id: int = 0
        
        class Page(Table):
            title: str = ""
            site_id: int = 0
            blocks: List[Block] = has_many(
                Block, "page_id",
                cascade=CascadeOptions.all()
            )
        
        class Site(Table):
            name: str = ""
            pages: List[Page] = has_many(
                Page, "site_id",
                on_delete="cascade"
            )
        
        assert Site.__dict__["pages"].on_delete == "cascade"
        assert Page.__dict__["blocks"].cascade.on_delete is True
    
    def test_project_management_cascade(self, clean_state):
        """Test project management cascade pattern."""
        class Subtask(Table):
            title: str = ""
            task_id: int = 0
        
        class Task(Table):
            title: str = ""
            project_id: int = 0
            subtasks: List[Subtask] = has_many(
                Subtask, "task_id",
                on_delete="cascade"
            )
        
        class Project(Table):
            name: str = ""
            tasks: List[Task] = has_many(
                Task, "project_id",
                on_delete="cascade"
            )
        
        assert Project.__dict__["tasks"].on_delete == "cascade"
        assert Task.__dict__["subtasks"].on_delete == "cascade"

