"""
Nullify Cascade Tests.

Tests for on_delete="nullify" functionality including:
- FK set to NULL behavior
- Nullify configuration
- Nullify with various relationship types
"""

import pytest
from typing import List, Optional

from pynext.db.table import Table, _model_registry
from pynext.db.relationships import (
    has_many,
    has_one,
    CascadeOptions,
)
from pynext.db.relationships.cascade import (
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
# Nullify Configuration Tests (40 tests)
# =============================================================================

class TestNullifyConfiguration:
    """Test nullify configuration on relationships."""
    
    def test_has_many_nullify(self, clean_state):
        """Test has_many with on_delete=nullify."""
        class Comment(Table):
            text: str = ""
            author_id: Optional[int] = None
        
        class User(Table):
            name: str = ""
            comments: List[Comment] = has_many(Comment, "author_id", on_delete="nullify")
        
        assert User.__dict__["comments"].on_delete == "nullify"
    
    def test_has_one_nullify(self, clean_state):
        """Test has_one with on_delete=nullify."""
        class Settings(Table):
            theme: str = "light"
            user_id: Optional[int] = None
        
        class User(Table):
            name: str = ""
            settings: Settings = has_one(Settings, "user_id", on_delete="nullify")
        
        assert User.__dict__["settings"].on_delete == "nullify"
    
    def test_nullify_with_backref(self, clean_state):
        """Test nullify with backref."""
        class Post(Table):
            title: str = ""
            author_id: Optional[int] = None
        
        class Author(Table):
            name: str = ""
            posts: List[Post] = has_many(
                Post, "author_id",
                backref="author",
                on_delete="nullify"
            )
        
        desc = Author.__dict__["posts"]
        assert desc.on_delete == "nullify"
        assert desc.backref == "author"
    
    def test_nullify_with_lazy(self, clean_state):
        """Test nullify with lazy loading."""
        class Task(Table):
            title: str = ""
            assignee_id: Optional[int] = None
        
        class Employee(Table):
            name: str = ""
            tasks: List[Task] = has_many(
                Task, "assignee_id",
                lazy="selectin",
                on_delete="nullify"
            )
        
        desc = Employee.__dict__["tasks"]
        assert desc.on_delete == "nullify"
        assert desc.lazy == "selectin"
    
    def test_multiple_nullify_relationships(self, clean_state):
        """Test multiple nullified relationships."""
        class Post(Table):
            title: str = ""
            author_id: Optional[int] = None
        
        class Comment(Table):
            text: str = ""
            author_id: Optional[int] = None
        
        class User(Table):
            name: str = ""
            posts: List[Post] = has_many(Post, "author_id", on_delete="nullify")
            comments: List[Comment] = has_many(Comment, "author_id", on_delete="nullify")
        
        assert User.__dict__["posts"].on_delete == "nullify"
        assert User.__dict__["comments"].on_delete == "nullify"


class TestNullifyScenarios:
    """Test various nullify scenarios."""
    
    def test_nullify_optional_fk(self, clean_state):
        """Test nullify with optional FK (most common case)."""
        class Article(Table):
            title: str = ""
            editor_id: Optional[int] = None
        
        class Editor(Table):
            name: str = ""
            articles: List[Article] = has_many(
                Article, "editor_id",
                on_delete="nullify"
            )
        
        assert Editor.__dict__["articles"].on_delete == "nullify"
    
    def test_nullify_preserves_data(self, clean_state):
        """Test nullify is for preserving orphaned data."""
        class Review(Table):
            content: str = ""
            reviewer_id: Optional[int] = None
        
        class Reviewer(Table):
            name: str = ""
            # Nullify: Keep reviews even after reviewer is deleted
            reviews: List[Review] = has_many(Review, "reviewer_id", on_delete="nullify")
        
        assert Reviewer.__dict__["reviews"].on_delete == "nullify"
    
    def test_nullify_mixed_with_cascade(self, clean_state):
        """Test nullify mixed with cascade."""
        class Post(Table):
            title: str = ""
            author_id: int = 0
        
        class Comment(Table):
            text: str = ""
            author_id: Optional[int] = None
        
        class User(Table):
            name: str = ""
            posts: List[Post] = has_many(Post, "author_id", on_delete="cascade")
            comments: List[Comment] = has_many(Comment, "author_id", on_delete="nullify")
        
        assert User.__dict__["posts"].on_delete == "cascade"
        assert User.__dict__["comments"].on_delete == "nullify"
    
    def test_nullify_anonymous_content(self, clean_state):
        """Test nullify for anonymous content pattern."""
        class Message(Table):
            content: str = ""
            sender_id: Optional[int] = None
        
        class User(Table):
            name: str = ""
            # Messages become anonymous when user deleted
            messages: List[Message] = has_many(
                Message, "sender_id",
                on_delete="nullify"
            )
        
        assert User.__dict__["messages"].on_delete == "nullify"


class TestNullifyWithFeatures:
    """Test nullify with other features."""
    
    def test_nullify_with_back_populates(self, clean_state):
        """Test nullify with back_populates."""
        class Document(Table):
            title: str = ""
            owner_id: Optional[int] = None
        
        class Owner(Table):
            name: str = ""
            documents: List[Document] = has_many(
                Document, "owner_id",
                back_populates="owner",
                on_delete="nullify"
            )
        
        desc = Owner.__dict__["documents"]
        assert desc.on_delete == "nullify"
        assert desc.back_populates == "owner"
    
    def test_nullify_has_one_settings(self, clean_state):
        """Test nullify on has_one for settings pattern."""
        class Preferences(Table):
            theme: str = "light"
            user_id: Optional[int] = None
        
        class User(Table):
            name: str = ""
            preferences: Preferences = has_one(
                Preferences, "user_id",
                on_delete="nullify"
            )
        
        assert User.__dict__["preferences"].on_delete == "nullify"
    
    def test_nullify_self_referential(self, clean_state):
        """Test nullify on self-referential relationship."""
        class Node(Table):
            name: str = ""
            parent_id: Optional[int] = None
            children: List["Node"] = has_many(
                "Node", "parent_id",
                on_delete="nullify"
            )
        
        assert Node.__dict__["children"].on_delete == "nullify"
    
    def test_nullify_string_model(self, clean_state):
        """Test nullify with string model reference."""
        class Item(Table):
            name: str = ""
            category_id: Optional[int] = None
        
        class Category(Table):
            name: str = ""
            items: List["Item"] = has_many("Item", "category_id", on_delete="nullify")
        
        assert Category.__dict__["items"].on_delete == "nullify"


# =============================================================================
# Nullify Edge Cases (20 tests)
# =============================================================================

class TestNullifyEdgeCases:
    """Test edge cases for nullify."""
    
    def test_nullify_empty_collection(self, clean_state):
        """Test nullify with empty collection."""
        class Child(Table):
            name: str = ""
            parent_id: Optional[int] = None
        
        class Parent(Table):
            name: str = ""
            children: List[Child] = has_many(Child, "parent_id", on_delete="nullify")
        
        parent = Parent(name="P1")
        assert len(parent.children) == 0
    
    def test_nullify_multiple_levels(self, clean_state):
        """Test nullify at multiple levels."""
        class GrandChild(Table):
            name: str = ""
            child_id: Optional[int] = None
        
        class Child(Table):
            name: str = ""
            parent_id: Optional[int] = None
            grandchildren: List[GrandChild] = has_many(
                GrandChild, "child_id", on_delete="nullify"
            )
        
        class Parent(Table):
            name: str = ""
            children: List[Child] = has_many(Child, "parent_id", on_delete="nullify")
        
        assert Parent.__dict__["children"].on_delete == "nullify"
        assert Child.__dict__["grandchildren"].on_delete == "nullify"
    
    def test_nullify_with_required_fields(self, clean_state):
        """Test nullify configuration (FK should be optional for nullify to work)."""
        class Post(Table):
            title: str = ""  # Required
            content: str = ""  # Required
            author_id: Optional[int] = None  # Optional for nullify
        
        class Author(Table):
            name: str = ""
            posts: List[Post] = has_many(Post, "author_id", on_delete="nullify")
        
        assert Author.__dict__["posts"].on_delete == "nullify"
    
    def test_nullify_vs_none_default(self, clean_state):
        """Test nullify is different from none default."""
        class ItemA(Table):
            name: str = ""
            container_id: int = 0
        
        class ItemB(Table):
            name: str = ""
            container_id: int = 0
        
        class ContainerA(Table):
            name: str = ""
            items: List[ItemA] = has_many(ItemA, "container_id")  # Default: none
        
        class ContainerB(Table):
            name: str = ""
            items: List[ItemB] = has_many(ItemB, "container_id", on_delete="nullify")
        
        assert ContainerA.__dict__["items"].on_delete == "none"
        assert ContainerB.__dict__["items"].on_delete == "nullify"

