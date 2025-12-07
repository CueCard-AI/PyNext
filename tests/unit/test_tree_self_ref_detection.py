"""
Test Phase 7.6: Self-Referential Relationship Detection.

These tests verify the auto-detection of self-referential relationships
in the relationship core module.
"""

import pytest
from typing import Optional, List, Dict, Any
from unittest.mock import Mock, MagicMock, patch

from pynext.db.relationships.core import (
    detect_relationships,
    detect_reverse_relationships,
    RelationshipInfo,
    RelationshipType,
    _is_self_referential_field,
)


# =============================================================================
# Mock Classes for Testing
# =============================================================================

class MockFieldInfo:
    """Mock field info for testing."""
    
    def __init__(self, name: str, type_hint: type = int):
        self.name = name
        self.type_hint = type_hint


class MockTable:
    """Mock table class for testing."""
    __table_name__ = "mock_tables"
    _fields = {}
    
    def __init__(self):
        pass


# =============================================================================
# Test _is_self_referential_field
# =============================================================================

class TestIsSelfReferentialField:
    """Test the _is_self_referential_field helper."""
    
    def test_parent_id_is_self_ref(self):
        """parent_id is always self-referential."""
        class Category:
            __table_name__ = "categories"
        
        assert _is_self_referential_field("parent_id", Category, "categories") is True
    
    def test_parent_is_self_ref(self):
        """parent is self-referential."""
        class Node:
            __table_name__ = "nodes"
        
        assert _is_self_referential_field("parent", Node, "nodes") is True
    
    def test_reply_to_id_is_self_ref(self):
        """reply_to_id is self-referential (for comments)."""
        class Comment:
            __table_name__ = "comments"
        
        assert _is_self_referential_field("reply_to_id", Comment, "comments") is True
    
    def test_reports_to_id_is_self_ref(self):
        """reports_to_id is self-referential (for employees)."""
        class Employee:
            __table_name__ = "employees"
        
        assert _is_self_referential_field("reports_to_id", Employee, "employees") is True
    
    def test_category_id_on_category(self):
        """category_id on Category is self-referential."""
        class Category:
            __table_name__ = "categories"
        
        assert _is_self_referential_field("category_id", Category, "categories") is True
    
    def test_user_id_on_post_not_self_ref(self):
        """user_id on Post is not self-referential."""
        class Post:
            __table_name__ = "posts"
        
        assert _is_self_referential_field("user_id", Post, "posts") is False
    
    def test_author_id_not_self_ref(self):
        """author_id on Article is not self-referential."""
        class Article:
            __table_name__ = "articles"
        
        assert _is_self_referential_field("author_id", Article, "articles") is False
    
    def test_comment_id_on_comment(self):
        """comment_id on Comment is self-referential."""
        class Comment:
            __table_name__ = "comments"
        
        assert _is_self_referential_field("comment_id", Comment, "comments") is True
    
    def test_node_id_on_node(self):
        """node_id on Node is self-referential."""
        class Node:
            __table_name__ = "nodes"
        
        assert _is_self_referential_field("node_id", Node, "nodes") is True
    
    def test_folder_id_on_folder(self):
        """folder_id on Folder is self-referential."""
        class Folder:
            __table_name__ = "folders"
        
        assert _is_self_referential_field("folder_id", Folder, "folders") is True


# =============================================================================
# Test detect_relationships for Self-Ref
# =============================================================================

class TestDetectRelationshipsSelfRef:
    """Test detect_relationships detects self-referential."""
    
    def test_detect_parent_id(self):
        """Detects parent_id as self-referential."""
        class Category:
            __table_name__ = "categories"
        
        fields = {"parent_id": MockFieldInfo("parent_id")}
        registry = {"categories": Category}
        
        rels = detect_relationships(Category, fields, registry)
        
        assert "parent" in rels
        assert rels["parent"].is_self_referential is True
        assert rels["parent"].model == Category
    
    def test_detect_category_id_on_category(self):
        """Detects category_id on Category as self-referential."""
        class Category:
            __table_name__ = "categories"
        
        fields = {"category_id": MockFieldInfo("category_id")}
        registry = {"categories": Category}
        
        rels = detect_relationships(Category, fields, registry)
        
        assert "category" in rels
        assert rels["category"].is_self_referential is True
    
    def test_non_self_ref_not_marked(self):
        """Non-self-referential relationships not marked."""
        class Post:
            __table_name__ = "posts"
        
        class User:
            __table_name__ = "users"
        
        fields = {"author_id": MockFieldInfo("author_id")}
        registry = {"posts": Post, "authors": User}
        
        rels = detect_relationships(Post, fields, registry)
        
        assert "author" in rels
        assert rels["author"].is_self_referential is False
    
    def test_mixed_self_ref_and_normal(self):
        """Model with both self-ref and normal relationships."""
        class Comment:
            __table_name__ = "comments"
        
        class User:
            __table_name__ = "users"
        
        fields = {
            "parent_id": MockFieldInfo("parent_id"),  # self-ref
            "author_id": MockFieldInfo("author_id"),  # normal
        }
        registry = {"comments": Comment, "authors": User}
        
        rels = detect_relationships(Comment, fields, registry)
        
        assert rels["parent"].is_self_referential is True
        assert rels["author"].is_self_referential is False


# =============================================================================
# Test detect_reverse_relationships for Self-Ref
# =============================================================================

class TestDetectReverseRelationshipsSelfRef:
    """Test detect_reverse_relationships creates children relationship."""
    
    def test_creates_children_for_parent_id(self):
        """Creates children relationship when parent_id exists."""
        class Category:
            __table_name__ = "categories"
            _fields = {"parent_id": MockFieldInfo("parent_id")}
        
        registry = {"categories": Category}
        
        rels = detect_reverse_relationships(Category, registry)
        
        assert "children" in rels
        assert rels["children"].is_self_referential is True
        assert rels["children"].foreign_key == "parent_id"
        assert rels["children"].type == RelationshipType.HAS_MANY
    
    def test_no_children_without_parent_id(self):
        """No children relationship when parent_id doesn't exist."""
        class Post:
            __table_name__ = "posts"
            _fields = {"author_id": MockFieldInfo("author_id")}
        
        registry = {"posts": Post}
        
        rels = detect_reverse_relationships(Post, registry)
        
        assert "children" not in rels
    
    def test_children_model_is_self(self):
        """Children relationship model is the same class."""
        class Node:
            __table_name__ = "nodes"
            _fields = {"parent_id": MockFieldInfo("parent_id")}
        
        registry = {"nodes": Node}
        
        rels = detect_reverse_relationships(Node, registry)
        
        assert rels["children"].model == Node


# =============================================================================
# Test RelationshipInfo with is_self_referential
# =============================================================================

class TestRelationshipInfoSelfRef:
    """Test RelationshipInfo.is_self_referential flag."""
    
    def test_default_is_false(self):
        """is_self_referential defaults to False."""
        info = RelationshipInfo(
            name="author",
            rel_type=RelationshipType.BELONGS_TO,
            model="User",
        )
        assert info.is_self_referential is False
    
    def test_explicit_true(self):
        """Can set is_self_referential to True."""
        info = RelationshipInfo(
            name="parent",
            rel_type=RelationshipType.BELONGS_TO,
            model="Category",
            is_self_referential=True,
        )
        assert info.is_self_referential is True
    
    def test_has_many_self_ref(self):
        """HAS_MANY can be self-referential."""
        info = RelationshipInfo(
            name="children",
            rel_type=RelationshipType.HAS_MANY,
            model="Category",
            foreign_key="parent_id",
            is_self_referential=True,
        )
        assert info.is_self_referential is True
        assert info.type == RelationshipType.HAS_MANY


# =============================================================================
# Test Common Self-Ref Patterns
# =============================================================================

class TestCommonSelfRefPatterns:
    """Test common self-referential patterns."""
    
    def test_category_hierarchy(self):
        """Category > Subcategory pattern."""
        class Category:
            __table_name__ = "categories"
            _fields = {"parent_id": MockFieldInfo("parent_id")}
        
        fields = Category._fields
        registry = {"categories": Category}
        
        rels = detect_relationships(Category, fields, registry)
        rev_rels = detect_reverse_relationships(Category, registry)
        
        assert "parent" in rels
        assert "children" in rev_rels
    
    def test_org_chart(self):
        """Employee > Manager pattern."""
        class Employee:
            __table_name__ = "employees"
        
        fields = {"reports_to_id": MockFieldInfo("reports_to_id")}
        registry = {"employees": Employee}
        
        rels = detect_relationships(Employee, fields, registry)
        
        assert "reports_to" in rels
        assert rels["reports_to"].is_self_referential is True
    
    def test_comment_replies(self):
        """Comment > Reply pattern."""
        class Comment:
            __table_name__ = "comments"
        
        fields = {"reply_to_id": MockFieldInfo("reply_to_id")}
        registry = {"comments": Comment}
        
        rels = detect_relationships(Comment, fields, registry)
        
        assert "reply_to" in rels
        assert rels["reply_to"].is_self_referential is True
    
    def test_folder_structure(self):
        """Folder > Subfolder pattern."""
        class Folder:
            __table_name__ = "folders"
            _fields = {"parent_id": MockFieldInfo("parent_id")}
        
        fields = Folder._fields
        registry = {"folders": Folder}
        
        rels = detect_relationships(Folder, fields, registry)
        
        assert "parent" in rels
        assert rels["parent"].is_self_referential is True
    
    def test_menu_items(self):
        """MenuItem > SubMenuItem pattern."""
        class MenuItem:
            __table_name__ = "menu_items"
            _fields = {"parent_id": MockFieldInfo("parent_id")}
        
        fields = MenuItem._fields
        registry = {"menu_items": MenuItem}
        
        rels = detect_relationships(MenuItem, fields, registry)
        
        assert "parent" in rels


# =============================================================================
# Test Edge Cases
# =============================================================================

class TestSelfRefEdgeCases:
    """Test edge cases in self-ref detection."""
    
    def test_multiple_self_ref_fields(self):
        """Model with multiple self-ref fields."""
        class Node:
            __table_name__ = "nodes"
        
        fields = {
            "parent_id": MockFieldInfo("parent_id"),
            "node_id": MockFieldInfo("node_id"),
        }
        registry = {"nodes": Node}
        
        rels = detect_relationships(Node, fields, registry)
        
        assert len(rels) == 2
        assert all(r.is_self_referential for r in rels.values())
    
    def test_custom_table_name(self):
        """Self-ref with custom table name."""
        class TreeNode:
            __table_name__ = "tree_nodes"  # Not 'treenodes'
            _fields = {"parent_id": MockFieldInfo("parent_id")}
        
        fields = TreeNode._fields
        registry = {"tree_nodes": TreeNode}
        
        rels = detect_relationships(TreeNode, fields, registry)
        
        # parent_id is always detected as self-ref
        assert "parent" in rels
        assert rels["parent"].is_self_referential is True
    
    def test_no_fields(self):
        """Model with no fields."""
        class Empty:
            __table_name__ = "empties"
        
        rels = detect_relationships(Empty, {}, {})
        assert rels == {}
    
    def test_id_field_not_self_ref(self):
        """'id' field is not self-referential."""
        class Model:
            __table_name__ = "models"
        
        fields = {"id": MockFieldInfo("id")}
        registry = {"models": Model}
        
        rels = detect_relationships(Model, fields, registry)
        
        # 'id' doesn't end with '_id' pattern for FK detection
        # So no relationship detected
        assert len(rels) == 0


# =============================================================================
# Test Relationship Type Assignment
# =============================================================================

class TestSelfRefRelationshipTypes:
    """Test correct relationship types for self-ref."""
    
    def test_parent_is_belongs_to(self):
        """Parent relationship is BELONGS_TO."""
        class Category:
            __table_name__ = "categories"
        
        fields = {"parent_id": MockFieldInfo("parent_id")}
        registry = {"categories": Category}
        
        rels = detect_relationships(Category, fields, registry)
        
        assert rels["parent"].type == RelationshipType.BELONGS_TO
    
    def test_children_is_has_many(self):
        """Children relationship is HAS_MANY."""
        class Category:
            __table_name__ = "categories"
            _fields = {"parent_id": MockFieldInfo("parent_id")}
        
        registry = {"categories": Category}
        
        rels = detect_reverse_relationships(Category, registry)
        
        assert rels["children"].type == RelationshipType.HAS_MANY

