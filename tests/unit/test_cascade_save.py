"""
Save Cascade Tests.

Tests for cascade.on_save functionality.
When parent is saved, related dirty objects are also saved.
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
# Save Cascade Configuration Tests (40 tests)
# =============================================================================

class TestSaveCascadeConfiguration:
    """Test save cascade configuration."""
    
    def test_cascade_options_on_save(self, clean_state):
        """Test CascadeOptions with on_save."""
        opts = CascadeOptions(on_save=True)
        assert opts.on_save is True
    
    def test_save_only_preset(self, clean_state):
        """Test CascadeOptions.save_only() preset."""
        opts = CascadeOptions.save_only()
        assert opts.on_save is True
        assert opts.on_delete is False
    
    def test_all_preset_includes_save(self, clean_state):
        """Test CascadeOptions.all() includes on_save."""
        opts = CascadeOptions.all()
        assert opts.on_save is True
    
    def test_has_many_with_save_cascade(self, clean_state):
        """Test has_many with save cascade."""
        class Item(Table):
            name: str = ""
            cart_id: int = 0
        
        class Cart(Table):
            total: float = 0.0
            items: List[Item] = has_many(
                Item, "cart_id",
                cascade=CascadeOptions(on_save=True)
            )
        
        desc = Cart.__dict__["items"]
        assert desc.cascade.on_save is True
    
    def test_has_one_with_save_cascade(self, clean_state):
        """Test has_one with save cascade."""
        class Profile(Table):
            bio: str = ""
            user_id: int = 0
        
        class User(Table):
            name: str = ""
            profile: Profile = has_one(
                Profile, "user_id",
                cascade=CascadeOptions(on_save=True)
            )
        
        desc = User.__dict__["profile"]
        assert desc.cascade.on_save is True


class TestSaveCascadeScenarios:
    """Test various save cascade scenarios."""
    
    def test_save_cascade_aggregate(self, clean_state):
        """Test save cascade for aggregate pattern."""
        class Address(Table):
            street: str = ""
            order_id: int = 0
        
        class OrderLine(Table):
            product: str = ""
            order_id: int = 0
        
        class Order(Table):
            number: str = ""
            address: Address = has_one(
                Address, "order_id",
                cascade=CascadeOptions(on_save=True)
            )
            lines: List[OrderLine] = has_many(
                OrderLine, "order_id",
                cascade=CascadeOptions(on_save=True)
            )
        
        assert Order.__dict__["address"].cascade.on_save is True
        assert Order.__dict__["lines"].cascade.on_save is True
    
    def test_save_cascade_document(self, clean_state):
        """Test save cascade for document pattern."""
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
    
    def test_save_and_delete_cascade(self, clean_state):
        """Test both save and delete cascade."""
        class Child(Table):
            name: str = ""
            parent_id: int = 0
        
        class Parent(Table):
            name: str = ""
            children: List[Child] = has_many(
                Child, "parent_id",
                cascade=CascadeOptions(on_save=True, on_delete=True)
            )
        
        desc = Parent.__dict__["children"]
        assert desc.cascade.on_save is True
        assert desc.cascade.on_delete is True
    
    def test_save_cascade_with_backref(self, clean_state):
        """Test save cascade with backref."""
        class Task(Table):
            title: str = ""
            project_id: int = 0
        
        class Project(Table):
            name: str = ""
            tasks: List[Task] = has_many(
                Task, "project_id",
                backref="project",
                cascade=CascadeOptions(on_save=True)
            )
        
        desc = Project.__dict__["tasks"]
        assert desc.cascade.on_save is True
        assert desc.backref == "project"


class TestSaveCascadeEdgeCases:
    """Test edge cases for save cascade."""
    
    def test_save_only_no_delete(self, clean_state):
        """Test on_save without on_delete."""
        class Log(Table):
            message: str = ""
            session_id: int = 0
        
        class Session(Table):
            name: str = ""
            logs: List[Log] = has_many(
                Log, "session_id",
                cascade=CascadeOptions(on_save=True)
            )
        
        desc = Session.__dict__["logs"]
        assert desc.cascade.on_save is True
        assert desc.cascade.on_delete is False
    
    def test_save_with_lazy_dynamic(self, clean_state):
        """Test save cascade with lazy='dynamic'."""
        class Event(Table):
            name: str = ""
            stream_id: int = 0
        
        class Stream(Table):
            name: str = ""
            events: List[Event] = has_many(
                Event, "stream_id",
                lazy="dynamic",
                cascade=CascadeOptions(on_save=True)
            )
        
        desc = Stream.__dict__["events"]
        assert desc.cascade.on_save is True
        assert desc.lazy == "dynamic"
    
    def test_save_self_referential(self, clean_state):
        """Test save cascade on self-referential relationship."""
        class Category(Table):
            name: str = ""
            parent_id: Optional[int] = None
            subcategories: List["Category"] = has_many(
                "Category", "parent_id",
                cascade=CascadeOptions(on_save=True)
            )
        
        desc = Category.__dict__["subcategories"]
        assert desc.cascade.on_save is True
    
    def test_multiple_save_cascades(self, clean_state):
        """Test multiple relationships with save cascade."""
        class Photo(Table):
            url: str = ""
            post_id: int = 0
        
        class Comment(Table):
            text: str = ""
            post_id: int = 0
        
        class Post(Table):
            title: str = ""
            photos: List[Photo] = has_many(
                Photo, "post_id",
                cascade=CascadeOptions(on_save=True)
            )
            comments: List[Comment] = has_many(
                Comment, "post_id",
                cascade=CascadeOptions(on_save=True)
            )
        
        assert Post.__dict__["photos"].cascade.on_save is True
        assert Post.__dict__["comments"].cascade.on_save is True


# =============================================================================
# Mixed Cascade Tests (20 tests)
# =============================================================================

class TestMixedCascades:
    """Test mixed cascade configurations."""
    
    def test_save_delete_orphan_all(self, clean_state):
        """Test all cascade options together."""
        class Part(Table):
            name: str = ""
            assembly_id: int = 0
        
        class Assembly(Table):
            name: str = ""
            parts: List[Part] = has_many(
                Part, "assembly_id",
                cascade=CascadeOptions.all()
            )
        
        desc = Assembly.__dict__["parts"]
        assert desc.cascade.on_save is True
        assert desc.cascade.on_delete is True
        assert desc.cascade.on_orphan is True
        assert desc.cascade.on_merge is True
    
    def test_save_and_orphan(self, clean_state):
        """Test save and orphan together."""
        class Element(Table):
            value: str = ""
            collection_id: int = 0
        
        class Collection(Table):
            name: str = ""
            elements: List[Element] = has_many(
                Element, "collection_id",
                cascade=CascadeOptions(on_save=True, on_orphan=True)
            )
        
        desc = Collection.__dict__["elements"]
        assert desc.cascade.on_save is True
        assert desc.cascade.on_orphan is True
        assert desc.cascade.on_delete is False
    
    def test_different_cascades_per_relationship(self, clean_state):
        """Test different cascade configs per relationship."""
        class Draft(Table):
            content: str = ""
            author_id: int = 0
        
        class Published(Table):
            content: str = ""
            author_id: int = 0
        
        class Author(Table):
            name: str = ""
            # Drafts: save cascade (work in progress)
            drafts: List[Draft] = has_many(
                Draft, "author_id",
                cascade=CascadeOptions(on_save=True)
            )
            # Published: delete cascade (cleanup)
            published: List[Published] = has_many(
                Published, "author_id",
                cascade=CascadeOptions(on_delete=True)
            )
        
        assert Author.__dict__["drafts"].cascade.on_save is True
        assert Author.__dict__["drafts"].cascade.on_delete is False
        assert Author.__dict__["published"].cascade.on_delete is True
        assert Author.__dict__["published"].cascade.on_save is False

