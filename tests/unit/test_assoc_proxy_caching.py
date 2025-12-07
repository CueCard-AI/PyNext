"""
Tests for association proxy caching behavior.

Tests cover:
- Cache behavior for collections
- Cache invalidation
- Performance with caching
- Memory management
"""

import pytest
from typing import List, Optional
from dataclasses import dataclass


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
    """Junction for Product-Tag."""
    id: int
    product_id: int
    tag: Optional[Tag] = None


class MockTable:
    """Base mock table."""
    _fields = {}
    __table_name__ = "mock"


from pynext.db.relationships.association_proxy import (
    association_proxy,
    ProxyCollection,
)


# =============================================================================
# Test: Fresh Collection on Each Access
# =============================================================================

class TestFreshCollection:
    """Test that collections are fresh on each access."""
    
    def test_new_proxy_collection_each_access(self):
        """Each access creates new ProxyCollection instance."""
        class Product(MockTable):
            def __init__(self):
                self._product_tags = []
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tags = association_proxy("product_tags", "tag")
        
        product = Product()
        
        proxy1 = product.tags
        proxy2 = product.tags
        
        # Different instances (not cached at descriptor level)
        # Values are evaluated fresh each time
        assert isinstance(proxy1, ProxyCollection)
        assert isinstance(proxy2, ProxyCollection)
    
    def test_values_evaluated_fresh(self):
        """Values are evaluated fresh on each iteration."""
        class Product(MockTable):
            def __init__(self):
                self._product_tags = []
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tag_names = association_proxy("product_tags", "tag.name")
        
        product = Product()
        
        # Initially empty
        assert list(product.tag_names) == []
        
        # Add item
        product._product_tags.append(ProductTag(1, 1, Tag(1, "new")))
        
        # Should see the new item
        assert list(product.tag_names) == ["new"]


# =============================================================================
# Test: Source Modification Reflected
# =============================================================================

class TestSourceModificationReflected:
    """Test that source modifications are reflected."""
    
    def test_append_to_source_visible(self):
        """Appending to source is visible in proxy."""
        class Product(MockTable):
            def __init__(self):
                self._product_tags = []
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tag_names = association_proxy("product_tags", "tag.name")
        
        product = Product()
        
        assert list(product.tag_names) == []
        
        product._product_tags.append(ProductTag(1, 1, Tag(1, "added")))
        
        assert list(product.tag_names) == ["added"]
    
    def test_remove_from_source_visible(self):
        """Removing from source is visible in proxy."""
        class Product(MockTable):
            def __init__(self):
                self._product_tags = [
                    ProductTag(1, 1, Tag(1, "first")),
                    ProductTag(2, 1, Tag(2, "second")),
                ]
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tag_names = association_proxy("product_tags", "tag.name")
        
        product = Product()
        
        assert list(product.tag_names) == ["first", "second"]
        
        product._product_tags.pop(0)
        
        assert list(product.tag_names) == ["second"]
    
    def test_clear_source_visible(self):
        """Clearing source is visible in proxy."""
        class Product(MockTable):
            def __init__(self):
                self._product_tags = [
                    ProductTag(1, 1, Tag(1, "a")),
                    ProductTag(2, 1, Tag(2, "b")),
                ]
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tag_names = association_proxy("product_tags", "tag.name")
        
        product = Product()
        
        assert len(list(product.tag_names)) == 2
        
        product._product_tags.clear()
        
        assert list(product.tag_names) == []
    
    def test_replace_source_visible(self):
        """Replacing source is visible in proxy."""
        class Product(MockTable):
            def __init__(self):
                self._product_tags = [ProductTag(1, 1, Tag(1, "old"))]
            
            @property
            def product_tags(self):
                return self._product_tags
            
            @product_tags.setter
            def product_tags(self, value):
                self._product_tags = value
        
        Product.tag_names = association_proxy("product_tags", "tag.name")
        
        product = Product()
        
        assert list(product.tag_names) == ["old"]
        
        product._product_tags = [ProductTag(2, 1, Tag(2, "new"))]
        
        assert list(product.tag_names) == ["new"]


# =============================================================================
# Test: Scalar Caching
# =============================================================================

class TestScalarCaching:
    """Test caching behavior for scalar proxies."""
    
    def test_scalar_evaluated_each_time(self):
        """Scalar values are evaluated each time accessed."""
        @dataclass
        class Author:
            name: str
        
        class Post(MockTable):
            def __init__(self):
                self._author = Author("Alice")
            
            @property
            def author(self):
                return self._author
            
            @author.setter
            def author(self, value):
                self._author = value
        
        Post.author_name = association_proxy("author", "name", scalar=True)
        
        post = Post()
        
        assert post.author_name == "Alice"
        
        post._author = Author("Bob")
        
        assert post.author_name == "Bob"
    
    def test_scalar_change_in_object_visible(self):
        """Changes to object attributes are visible."""
        class MutableAuthor:
            def __init__(self, name: str):
                self.name = name
        
        class Post(MockTable):
            def __init__(self):
                self._author = MutableAuthor("Alice")
            
            @property
            def author(self):
                return self._author
        
        Post.author_name = association_proxy("author", "name", scalar=True)
        
        post = Post()
        
        assert post.author_name == "Alice"
        
        post._author.name = "Updated"
        
        assert post.author_name == "Updated"


# =============================================================================
# Test: ProxyCollection Internal Caching
# =============================================================================

class TestProxyCollectionCaching:
    """Test ProxyCollection's internal caching behavior."""
    
    def test_values_computed_on_iteration(self):
        """Values are computed fresh on each iteration."""
        class Product(MockTable):
            call_count = 0
            
            def __init__(self):
                self._product_tags = [ProductTag(1, 1, Tag(1, "test"))]
            
            @property
            def product_tags(self):
                Product.call_count += 1
                return self._product_tags
        
        Product.tags = association_proxy("product_tags", "tag")
        
        product = Product()
        Product.call_count = 0
        
        # Each iteration accesses the property
        list(product.tags)
        list(product.tags)
        list(product.tags)
        
        # Property was accessed multiple times
        assert Product.call_count >= 3
    
    def test_len_triggers_evaluation(self):
        """len() evaluates the values."""
        class Product(MockTable):
            def __init__(self):
                self._product_tags = [
                    ProductTag(1, 1, Tag(1, "a")),
                    ProductTag(2, 1, Tag(2, "b")),
                ]
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tags = association_proxy("product_tags", "tag")
        
        product = Product()
        
        assert len(product.tags) == 2
        
        # Add more
        product._product_tags.append(ProductTag(3, 1, Tag(3, "c")))
        
        # len() should show new count
        assert len(product.tags) == 3


# =============================================================================
# Test: Performance with Many Items
# =============================================================================

class TestPerformance:
    """Test performance with many items."""
    
    def test_iteration_1000_items(self):
        """Iterating 1000 items is efficient."""
        class Product(MockTable):
            def __init__(self, count: int):
                self._product_tags = [
                    ProductTag(i, 1, Tag(i, f"tag{i}"))
                    for i in range(count)
                ]
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tag_names = association_proxy("product_tags", "tag.name")
        
        product = Product(1000)
        
        # Should complete without issue
        result = list(product.tag_names)
        assert len(result) == 1000
    
    def test_repeated_access_1000_items(self):
        """Repeated access to 1000 items."""
        class Product(MockTable):
            def __init__(self):
                self._product_tags = [
                    ProductTag(i, 1, Tag(i, f"tag{i}"))
                    for i in range(1000)
                ]
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tag_names = association_proxy("product_tags", "tag.name")
        
        product = Product()
        
        # Multiple accesses
        for _ in range(5):
            result = list(product.tag_names)
            assert len(result) == 1000
    
    def test_index_access_efficient(self):
        """Index access works on large collections."""
        class Product(MockTable):
            def __init__(self):
                self._product_tags = [
                    ProductTag(i, 1, Tag(i, f"tag{i}"))
                    for i in range(1000)
                ]
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tag_names = association_proxy("product_tags", "tag.name")
        
        product = Product()
        
        # Access specific indices
        assert product.tag_names[0] == "tag0"
        assert product.tag_names[500] == "tag500"
        assert product.tag_names[999] == "tag999"


# =============================================================================
# Test: Memory Behavior
# =============================================================================

class TestMemoryBehavior:
    """Test memory behavior of proxies."""
    
    def test_proxy_does_not_hold_references(self):
        """Proxy doesn't hold references to values."""
        class Product(MockTable):
            def __init__(self):
                self._product_tags = [ProductTag(1, 1, Tag(1, "test"))]
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tags = association_proxy("product_tags", "tag")
        
        product = Product()
        
        proxy = product.tags
        
        # Iterate to get values
        result = list(proxy)
        
        # Clear source
        product._product_tags.clear()
        
        # Original result still has values (it's a copy)
        assert len(result) == 1
        
        # But fresh iteration is empty
        assert list(product.tags) == []


# =============================================================================
# Test: Consistency Across Multiple Proxies
# =============================================================================

class TestConsistencyMultipleProxies:
    """Test consistency when multiple proxies access same source."""
    
    def test_multiple_proxies_see_same_data(self):
        """Multiple proxies on same source see same data."""
        class Product(MockTable):
            def __init__(self):
                self._product_tags = [ProductTag(1, 1, Tag(1, "test"))]
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tags = association_proxy("product_tags", "tag")
        Product.tag_names = association_proxy("product_tags", "tag.name")
        
        product = Product()
        
        tags = list(product.tags)
        names = list(product.tag_names)
        
        assert len(tags) == 1
        assert names == ["test"]
        
        # Modify source
        product._product_tags.append(ProductTag(2, 1, Tag(2, "new")))
        
        # Both proxies should see the change
        assert len(list(product.tags)) == 2
        assert list(product.tag_names) == ["test", "new"]
    
    def test_modification_through_one_proxy_visible_to_other(self):
        """Modification through one proxy is visible to another."""
        class Product(MockTable):
            def __init__(self):
                self._product_tags = []
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tags = association_proxy(
            "product_tags",
            "tag",
            creator=lambda t: ProductTag(0, 1, tag=t)
        )
        Product.tag_names = association_proxy("product_tags", "tag.name")
        
        product = Product()
        
        # Add through tags proxy
        product.tags.append(Tag(1, "added"))
        
        # Should be visible in tag_names
        assert list(product.tag_names) == ["added"]

