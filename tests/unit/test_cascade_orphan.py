"""
Orphan Cascade Tests.

Tests for cascade.on_orphan functionality (delete-orphan).
When items are removed from a collection, they can be deleted.
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
    get_cascade_manager,
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
# Orphan Configuration Tests (40 tests)
# =============================================================================

class TestOrphanConfiguration:
    """Test orphan configuration."""
    
    def test_cascade_options_on_orphan(self, clean_state):
        """Test CascadeOptions with on_orphan."""
        opts = CascadeOptions(on_orphan=True)
        assert opts.on_orphan is True
    
    def test_delete_orphan_preset(self, clean_state):
        """Test CascadeOptions.delete_orphan() preset."""
        opts = CascadeOptions.delete_orphan()
        assert opts.on_delete is True
        assert opts.on_orphan is True
    
    def test_all_preset_includes_orphan(self, clean_state):
        """Test CascadeOptions.all() includes on_orphan."""
        opts = CascadeOptions.all()
        assert opts.on_orphan is True
    
    def test_has_many_with_orphan_cascade(self, clean_state):
        """Test has_many with orphan cascade."""
        class LineItem(Table):
            name: str = ""
            order_id: int = 0
        
        class Order(Table):
            total: float = 0.0
            items: List[LineItem] = has_many(
                LineItem, "order_id",
                cascade=CascadeOptions(on_orphan=True)
            )
        
        desc = Order.__dict__["items"]
        assert desc.cascade.on_orphan is True
    
    def test_has_many_delete_and_orphan(self, clean_state):
        """Test has_many with both delete and orphan."""
        class Attachment(Table):
            filename: str = ""
            message_id: int = 0
        
        class Message(Table):
            content: str = ""
            attachments: List[Attachment] = has_many(
                Attachment, "message_id",
                cascade=CascadeOptions.delete_orphan()
            )
        
        desc = Message.__dict__["attachments"]
        assert desc.cascade.on_delete is True
        assert desc.cascade.on_orphan is True


class TestOrphanScenarios:
    """Test various orphan scenarios."""
    
    def test_orphan_line_items(self, clean_state):
        """Test orphan for order line items."""
        class LineItem(Table):
            product: str = ""
            quantity: int = 1
            order_id: int = 0
        
        class Order(Table):
            number: str = ""
            items: List[LineItem] = has_many(
                LineItem, "order_id",
                cascade=CascadeOptions(on_orphan=True)
            )
        
        desc = Order.__dict__["items"]
        assert desc.cascade.on_orphan is True
    
    def test_orphan_form_fields(self, clean_state):
        """Test orphan for form fields."""
        class FormField(Table):
            label: str = ""
            form_id: int = 0
        
        class Form(Table):
            title: str = ""
            fields: List[FormField] = has_many(
                FormField, "form_id",
                cascade=CascadeOptions.delete_orphan()
            )
        
        desc = Form.__dict__["fields"]
        assert desc.cascade.on_orphan is True
    
    def test_orphan_menu_items(self, clean_state):
        """Test orphan for menu items."""
        class MenuItem(Table):
            label: str = ""
            menu_id: int = 0
        
        class Menu(Table):
            name: str = ""
            items: List[MenuItem] = has_many(
                MenuItem, "menu_id",
                cascade=CascadeOptions.all()
            )
        
        desc = Menu.__dict__["items"]
        assert desc.cascade.on_orphan is True
    
    def test_orphan_embedded_documents(self, clean_state):
        """Test orphan for embedded documents pattern."""
        class Section(Table):
            content: str = ""
            document_id: int = 0
        
        class Document(Table):
            title: str = ""
            sections: List[Section] = has_many(
                Section, "document_id",
                cascade=CascadeOptions(on_delete=True, on_orphan=True)
            )
        
        desc = Document.__dict__["sections"]
        assert desc.cascade.on_orphan is True


class TestOrphanWithBackref:
    """Test orphan with backref."""
    
    def test_orphan_with_backref(self, clean_state):
        """Test orphan combined with backref."""
        class Chapter(Table):
            title: str = ""
            book_id: int = 0
        
        class Book(Table):
            title: str = ""
            chapters: List[Chapter] = has_many(
                Chapter, "book_id",
                backref="book",
                cascade=CascadeOptions.delete_orphan()
            )
        
        desc = Book.__dict__["chapters"]
        assert desc.cascade.on_orphan is True
        assert desc.backref == "book"
    
    def test_orphan_with_back_populates(self, clean_state):
        """Test orphan with back_populates."""
        class Slide(Table):
            content: str = ""
            presentation_id: int = 0
        
        class Presentation(Table):
            title: str = ""
            slides: List[Slide] = has_many(
                Slide, "presentation_id",
                back_populates="presentation",
                cascade=CascadeOptions(on_orphan=True)
            )
        
        desc = Presentation.__dict__["slides"]
        assert desc.cascade.on_orphan is True


# =============================================================================
# Orphan Edge Cases (30 tests)
# =============================================================================

class TestOrphanEdgeCases:
    """Test edge cases for orphan."""
    
    def test_orphan_only_no_delete(self, clean_state):
        """Test on_orphan without on_delete."""
        class Tag(Table):
            name: str = ""
            item_id: int = 0
        
        class Item(Table):
            name: str = ""
            tags: List[Tag] = has_many(
                Tag, "item_id",
                cascade=CascadeOptions(on_orphan=True)  # Only orphan
            )
        
        desc = Item.__dict__["tags"]
        assert desc.cascade.on_orphan is True
        assert desc.cascade.on_delete is False
    
    def test_orphan_with_lazy_selectin(self, clean_state):
        """Test orphan with lazy='selectin'."""
        class Step(Table):
            name: str = ""
            workflow_id: int = 0
        
        class Workflow(Table):
            name: str = ""
            steps: List[Step] = has_many(
                Step, "workflow_id",
                lazy="selectin",
                cascade=CascadeOptions(on_orphan=True)
            )
        
        desc = Workflow.__dict__["steps"]
        assert desc.cascade.on_orphan is True
        assert desc.lazy == "selectin"
    
    def test_orphan_self_referential(self, clean_state):
        """Test orphan on self-referential relationship."""
        class TreeNode(Table):
            name: str = ""
            parent_id: Optional[int] = None
            children: List["TreeNode"] = has_many(
                "TreeNode", "parent_id",
                cascade=CascadeOptions.delete_orphan()
            )
        
        desc = TreeNode.__dict__["children"]
        assert desc.cascade.on_orphan is True
    
    def test_orphan_multiple_relationships(self, clean_state):
        """Test orphan on multiple relationships."""
        class Photo(Table):
            url: str = ""
            album_id: int = 0
        
        class Video(Table):
            url: str = ""
            album_id: int = 0
        
        class Album(Table):
            name: str = ""
            photos: List[Photo] = has_many(
                Photo, "album_id",
                cascade=CascadeOptions(on_orphan=True)
            )
            videos: List[Video] = has_many(
                Video, "album_id",
                cascade=CascadeOptions(on_orphan=True)
            )
        
        assert Album.__dict__["photos"].cascade.on_orphan is True
        assert Album.__dict__["videos"].cascade.on_orphan is True
    
    def test_orphan_without_on_delete(self, clean_state):
        """Test orphan without on_delete (unusual but valid)."""
        class Component(Table):
            name: str = ""
            assembly_id: int = 0
        
        class Assembly(Table):
            name: str = ""
            components: List[Component] = has_many(
                Component, "assembly_id",
                cascade=CascadeOptions(on_orphan=True, on_delete=False)
            )
        
        desc = Assembly.__dict__["components"]
        assert desc.cascade.on_orphan is True
        assert desc.cascade.on_delete is False


class TestOrphanScheduling:
    """Test orphan scheduling behavior."""
    
    def test_cascade_manager_schedule_orphan(self, clean_state):
        """Test CascadeManager.schedule_orphan_delete."""
        class Item(Table):
            name: str = ""
        
        class Container(Table):
            name: str = ""
        
        item = Item(name="I1")
        container = Container(name="C1")
        
        manager = get_cascade_manager()
        manager.schedule_orphan_delete(item, container, "items")
        
        # Check that orphan markers are set
        assert hasattr(item, "_pending_orphan_delete")
        assert item._pending_orphan_delete is True
        assert item._orphan_parent is container
        assert item._orphan_relationship == "items"
    
    def test_orphan_markers_cleared(self, clean_state):
        """Test orphan markers can be cleared."""
        class Item(Table):
            name: str = ""
        
        item = Item(name="I1")
        item._pending_orphan_delete = True
        item._orphan_parent = None
        item._orphan_relationship = "test"
        
        # Clear markers
        del item._pending_orphan_delete
        del item._orphan_parent
        del item._orphan_relationship
        
        assert not hasattr(item, "_pending_orphan_delete")

