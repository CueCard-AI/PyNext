"""
Tests for creator functions in association proxy.

Tests cover:
- Creator function invocation
- Append through proxy
- Extend through proxy
- Error handling without creator
"""

import pytest
from typing import List, Optional
from dataclasses import dataclass, field


# =============================================================================
# Mock Classes
# =============================================================================

@dataclass
class Tag:
    """Tag model."""
    id: int
    name: str


@dataclass
class ProductTag:
    """Junction table for Product-Tag M2M."""
    id: int
    product_id: int
    tag_id: int
    tag: Optional[Tag] = None
    
    @classmethod
    def create(cls, product_id: int, tag: Tag):
        """Factory method for tests."""
        return cls(id=0, product_id=product_id, tag_id=tag.id, tag=tag)


@dataclass
class Keyword:
    """Keyword model."""
    id: int
    word: str


@dataclass
class UserKeyword:
    """Junction for User-Keyword."""
    id: int
    user_id: int
    keyword: Optional[Keyword] = None


class MockCollection(list):
    """Mock collection that tracks appends."""
    
    def __init__(self, *args):
        super().__init__(*args)
        self.append_log = []
    
    def append(self, item):
        self.append_log.append(item)
        super().append(item)


class MockTable:
    """Base mock table."""
    _fields = {}
    __table_name__ = "mock"


from pynext.db.relationships.association_proxy import (
    association_proxy,
    ProxyCollection,
)


# =============================================================================
# Test: Creator Function Basics
# =============================================================================

class TestCreatorBasics:
    """Test basic creator function behavior."""
    
    def test_creator_stored_in_descriptor(self):
        """Creator function is stored in descriptor."""
        creator = lambda x: x
        proxy = association_proxy("items", "tag", creator=creator)
        assert proxy.creator is creator
    
    def test_creator_none_by_default(self):
        """Creator is None by default."""
        proxy = association_proxy("items", "tag")
        assert proxy.creator is None
    
    def test_append_calls_creator(self):
        """Append calls the creator function."""
        created_items = []
        
        def creator(tag: Tag):
            item = ProductTag(0, 1, tag.id, tag)
            created_items.append(item)
            return item
        
        class Product(MockTable):
            def __init__(self):
                self._product_tags = []
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tags = association_proxy("product_tags", "tag", creator=creator)
        
        product = Product()
        tag = Tag(1, "electronics")
        
        product.tags.append(tag)
        
        assert len(created_items) == 1
        assert created_items[0].tag is tag
    
    def test_append_adds_to_source(self):
        """Append adds created item to source collection."""
        class Product(MockTable):
            def __init__(self):
                self._product_tags = []
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tags = association_proxy(
            "product_tags", 
            "tag",
            creator=lambda tag: ProductTag(0, 1, tag.id, tag)
        )
        
        product = Product()
        tag = Tag(1, "sale")
        
        product.tags.append(tag)
        
        assert len(product._product_tags) == 1
        assert product._product_tags[0].tag is tag


# =============================================================================
# Test: Append Operations
# =============================================================================

class TestAppendOperations:
    """Test append through proxy."""
    
    def test_append_single_item(self):
        """Append single item works."""
        class Product(MockTable):
            def __init__(self):
                self._product_tags = []
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tags = association_proxy(
            "product_tags",
            "tag",
            creator=lambda t: ProductTag(0, 1, t.id, t)
        )
        
        product = Product()
        product.tags.append(Tag(1, "new"))
        
        assert list(product.tags) == [Tag(1, "new")]
    
    def test_append_multiple_items(self):
        """Append multiple items sequentially."""
        class Product(MockTable):
            def __init__(self):
                self._product_tags = []
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tags = association_proxy(
            "product_tags",
            "tag",
            creator=lambda t: ProductTag(0, 1, t.id, t)
        )
        
        product = Product()
        product.tags.append(Tag(1, "a"))
        product.tags.append(Tag(2, "b"))
        product.tags.append(Tag(3, "c"))
        
        names = list(product.tags)
        assert len(names) == 3
    
    def test_append_returns_none(self):
        """Append returns None (like list.append)."""
        class Product(MockTable):
            def __init__(self):
                self._product_tags = []
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tags = association_proxy(
            "product_tags",
            "tag",
            creator=lambda t: ProductTag(0, 1, t.id, t)
        )
        
        product = Product()
        result = product.tags.append(Tag(1, "test"))
        
        assert result is None


# =============================================================================
# Test: Extend Operations
# =============================================================================

class TestExtendOperations:
    """Test extend through proxy."""
    
    def test_extend_empty_list(self):
        """Extend with empty list does nothing."""
        class Product(MockTable):
            def __init__(self):
                self._product_tags = []
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tags = association_proxy(
            "product_tags",
            "tag",
            creator=lambda t: ProductTag(0, 1, t.id, t)
        )
        
        product = Product()
        product.tags.extend([])
        
        assert len(product._product_tags) == 0
    
    def test_extend_single_item(self):
        """Extend with single item."""
        class Product(MockTable):
            def __init__(self):
                self._product_tags = []
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tags = association_proxy(
            "product_tags",
            "tag",
            creator=lambda t: ProductTag(0, 1, t.id, t)
        )
        
        product = Product()
        product.tags.extend([Tag(1, "single")])
        
        assert len(product._product_tags) == 1
    
    def test_extend_multiple_items(self):
        """Extend with multiple items."""
        class Product(MockTable):
            def __init__(self):
                self._product_tags = []
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tags = association_proxy(
            "product_tags",
            "tag",
            creator=lambda t: ProductTag(0, 1, t.id, t)
        )
        
        product = Product()
        tags = [Tag(i, f"tag{i}") for i in range(5)]
        product.tags.extend(tags)
        
        assert len(product._product_tags) == 5
    
    def test_extend_with_generator(self):
        """Extend works with generator."""
        class Product(MockTable):
            def __init__(self):
                self._product_tags = []
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tags = association_proxy(
            "product_tags",
            "tag",
            creator=lambda t: ProductTag(0, 1, t.id, t)
        )
        
        product = Product()
        product.tags.extend(Tag(i, f"gen{i}") for i in range(3))
        
        assert len(product._product_tags) == 3


# =============================================================================
# Test: Insert Operations
# =============================================================================

class TestInsertOperations:
    """Test insert through proxy."""
    
    def test_insert_at_beginning(self):
        """Insert at beginning (adds to end of source)."""
        class Product(MockTable):
            def __init__(self):
                self._product_tags = []
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tags = association_proxy(
            "product_tags",
            "tag",
            creator=lambda t: ProductTag(0, 1, t.id, t)
        )
        
        product = Product()
        product.tags.insert(0, Tag(1, "first"))
        
        assert len(product._product_tags) == 1
    
    def test_insert_without_creator_raises(self):
        """Insert without creator raises ValueError."""
        class Product(MockTable):
            def __init__(self):
                self._product_tags = []
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tags = association_proxy("product_tags", "tag")  # No creator
        
        product = Product()
        
        with pytest.raises(ValueError) as exc_info:
            product.tags.insert(0, Tag(1, "test"))
        
        assert "creator function" in str(exc_info.value)


# =============================================================================
# Test: Error Handling
# =============================================================================

class TestCreatorErrors:
    """Test error handling for creator operations."""
    
    def test_append_without_creator_raises(self):
        """Append without creator raises ValueError."""
        class Product(MockTable):
            def __init__(self):
                self._product_tags = []
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tags = association_proxy("product_tags", "tag")  # No creator!
        
        product = Product()
        
        with pytest.raises(ValueError) as exc_info:
            product.tags.append(Tag(1, "test"))
        
        assert "creator function" in str(exc_info.value)
        assert "association_proxy" in str(exc_info.value)
    
    def test_extend_without_creator_raises(self):
        """Extend without creator raises ValueError."""
        class Product(MockTable):
            def __init__(self):
                self._product_tags = []
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tags = association_proxy("product_tags", "tag")
        
        product = Product()
        
        with pytest.raises(ValueError):
            product.tags.extend([Tag(1, "test")])
    
    def test_creator_exception_propagates(self):
        """Exception in creator propagates."""
        def bad_creator(tag):
            raise RuntimeError("Creator failed!")
        
        class Product(MockTable):
            def __init__(self):
                self._product_tags = []
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tags = association_proxy(
            "product_tags",
            "tag",
            creator=bad_creator
        )
        
        product = Product()
        
        with pytest.raises(RuntimeError) as exc_info:
            product.tags.append(Tag(1, "test"))
        
        assert "Creator failed!" in str(exc_info.value)


# =============================================================================
# Test: Creator with Different Signatures
# =============================================================================

class TestCreatorSignatures:
    """Test creator functions with different signatures."""
    
    def test_lambda_creator(self):
        """Lambda creator works."""
        class Product(MockTable):
            def __init__(self):
                self._product_tags = []
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tags = association_proxy(
            "product_tags",
            "tag",
            creator=lambda t: ProductTag(0, 1, t.id, t)
        )
        
        product = Product()
        product.tags.append(Tag(1, "test"))
        
        assert len(product._product_tags) == 1
    
    def test_function_creator(self):
        """Regular function creator works."""
        def create_product_tag(tag: Tag) -> ProductTag:
            return ProductTag(id=0, product_id=1, tag_id=tag.id, tag=tag)
        
        class Product(MockTable):
            def __init__(self):
                self._product_tags = []
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tags = association_proxy(
            "product_tags",
            "tag",
            creator=create_product_tag
        )
        
        product = Product()
        product.tags.append(Tag(1, "test"))
        
        assert len(product._product_tags) == 1
    
    def test_classmethod_creator(self):
        """Class method as creator works."""
        class Product(MockTable):
            def __init__(self):
                self._product_tags = []
                self.id = 42
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tags = association_proxy(
            "product_tags",
            "tag",
            creator=lambda t: ProductTag.create(42, t)
        )
        
        product = Product()
        product.tags.append(Tag(1, "test"))
        
        assert len(product._product_tags) == 1


# =============================================================================
# Test: Creator with Extra Data
# =============================================================================

class TestCreatorExtraData:
    """Test creator functions that add extra data."""
    
    def test_creator_with_timestamp(self):
        """Creator can add timestamp."""
        from datetime import datetime
        
        @dataclass
        class TagWithTimestamp:
            tag: Tag
            created_at: datetime
        
        class Product(MockTable):
            def __init__(self):
                self._tags = []
            
            @property
            def tags(self):
                return self._tags
        
        Product.tag_names = association_proxy(
            "tags",
            "tag.name",
            creator=lambda t: TagWithTimestamp(t, datetime.now())
        )
        
        product = Product()
        product.tag_names.append(Tag(1, "timestamped"))
        
        assert len(product._tags) == 1
        assert hasattr(product._tags[0], 'created_at')
    
    def test_creator_with_default_values(self):
        """Creator can set default values."""
        @dataclass
        class TagAssignment:
            tag: Tag
            priority: int = 0
            visible: bool = True
        
        class Product(MockTable):
            def __init__(self):
                self._assignments = []
            
            @property
            def assignments(self):
                return self._assignments
        
        Product.tags = association_proxy(
            "assignments",
            "tag",
            creator=lambda t: TagAssignment(tag=t, priority=5)
        )
        
        product = Product()
        product.tags.append(Tag(1, "test"))
        
        assert product._assignments[0].priority == 5
        assert product._assignments[0].visible is True


# =============================================================================
# Test: Remove Operations with Creator
# =============================================================================

class TestRemoveOperations:
    """Test remove operations through proxy."""
    
    def test_remove_existing(self):
        """Remove existing item works."""
        class Product(MockTable):
            def __init__(self):
                tag1 = Tag(1, "first")
                tag2 = Tag(2, "second")
                self._product_tags = [
                    ProductTag(1, 1, 1, tag1),
                    ProductTag(2, 1, 2, tag2),
                ]
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tags = association_proxy("product_tags", "tag")
        
        product = Product()
        assert len(list(product.tags)) == 2
        
        product.tags.remove(Tag(1, "first"))
        
        assert len(list(product.tags)) == 1
    
    def test_remove_nonexistent_raises(self):
        """Remove nonexistent item raises ValueError."""
        class Product(MockTable):
            def __init__(self):
                self._product_tags = []
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tags = association_proxy("product_tags", "tag")
        
        product = Product()
        
        with pytest.raises(ValueError):
            product.tags.remove(Tag(999, "nonexistent"))


# =============================================================================
# Test: Pop Operations
# =============================================================================

class TestPopOperations:
    """Test pop operations through proxy."""
    
    def test_pop_last(self):
        """Pop last item."""
        class Product(MockTable):
            def __init__(self):
                self._product_tags = [
                    ProductTag(1, 1, 1, Tag(1, "first")),
                    ProductTag(2, 1, 2, Tag(2, "second")),
                ]
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tags = association_proxy("product_tags", "tag")
        
        product = Product()
        popped = product.tags.pop()
        
        assert popped == Tag(2, "second")
        assert len(list(product.tags)) == 1
    
    def test_pop_empty_raises(self):
        """Pop from empty raises IndexError."""
        class Product(MockTable):
            def __init__(self):
                self._product_tags = []
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tags = association_proxy("product_tags", "tag")
        
        product = Product()
        
        with pytest.raises(IndexError):
            product.tags.pop()


# =============================================================================
# Test: Clear Operations
# =============================================================================

class TestClearOperations:
    """Test clear operations through proxy."""
    
    def test_clear_removes_all(self):
        """Clear removes all items."""
        class Product(MockTable):
            def __init__(self):
                self._product_tags = [
                    ProductTag(1, 1, 1, Tag(1, "a")),
                    ProductTag(2, 1, 2, Tag(2, "b")),
                    ProductTag(3, 1, 3, Tag(3, "c")),
                ]
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tags = association_proxy("product_tags", "tag")
        
        product = Product()
        assert len(list(product.tags)) == 3
        
        product.tags.clear()
        
        assert len(list(product.tags)) == 0
        assert len(product._product_tags) == 0
    
    def test_clear_empty_is_noop(self):
        """Clear on empty is no-op."""
        class Product(MockTable):
            def __init__(self):
                self._product_tags = []
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tags = association_proxy("product_tags", "tag")
        
        product = Product()
        product.tags.clear()  # Should not raise
        
        assert len(product._product_tags) == 0

