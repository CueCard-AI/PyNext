"""
Tests for PyNext Incremental Static Regeneration (ISR).
"""

import pytest
import asyncio
import time
from pathlib import Path
from pynext.core.isr import (
    ISRCache,
    CacheEntry,
    RevalidateConfig,
    InvalidationScope,
    RevalidationTrigger,
    revalidate,
    revalidate_path,
    revalidate_tag,
    revalidate_component,
    get_isr_cache,
    init_isr_cache,
    RegenerationWorker,
)


class TestRevalidateConfig:
    """Tests for RevalidateConfig."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = RevalidateConfig()
        
        assert config.seconds is None
        assert config.on_demand is False
        assert config.tags == []
        assert config.scope == InvalidationScope.PAGE
        assert config.stale_while_revalidate is True
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = RevalidateConfig(
            seconds=60,
            tags=["products", "featured"],
            scope=InvalidationScope.COMPONENT,
        )
        
        assert config.seconds == 60
        assert "products" in config.tags
        assert config.scope == InvalidationScope.COMPONENT


class TestCacheEntry:
    """Tests for CacheEntry."""
    
    def test_entry_creation(self):
        """Test cache entry creation."""
        entry = CacheEntry(
            content="<div>Test</div>",
            hash="abc123",
            created_at=time.time(),
            expires_at=time.time() + 60,
            tags={"test", "demo"},
            scope=InvalidationScope.PAGE,
        )
        
        assert entry.content == "<div>Test</div>"
        assert "test" in entry.tags
        assert entry.is_stale is False
    
    def test_entry_expiration(self):
        """Test cache entry expiration check."""
        # Create expired entry
        entry = CacheEntry(
            content="<div>Test</div>",
            hash="abc123",
            created_at=time.time() - 120,
            expires_at=time.time() - 60,
            tags=set(),
            scope=InvalidationScope.PAGE,
        )
        
        assert entry.is_expired() is True
    
    def test_entry_not_expired(self):
        """Test non-expired entry."""
        entry = CacheEntry(
            content="<div>Test</div>",
            hash="abc123",
            created_at=time.time(),
            expires_at=time.time() + 3600,
            tags=set(),
            scope=InvalidationScope.PAGE,
        )
        
        assert entry.is_expired() is False
    
    def test_entry_no_expiration(self):
        """Test entry with no expiration."""
        entry = CacheEntry(
            content="<div>Test</div>",
            hash="abc123",
            created_at=time.time(),
            expires_at=None,
            tags=set(),
            scope=InvalidationScope.PAGE,
        )
        
        assert entry.is_expired() is False
    
    def test_mark_stale(self):
        """Test marking entry as stale."""
        entry = CacheEntry(
            content="test",
            hash="abc",
            created_at=time.time(),
            expires_at=None,
            tags=set(),
            scope=InvalidationScope.PAGE,
        )
        
        assert entry.is_stale is False
        entry.mark_stale()
        assert entry.is_stale is True
    
    def test_entry_serialization(self):
        """Test entry to_dict serialization."""
        entry = CacheEntry(
            content="test",
            hash="abc123",
            created_at=1000.0,
            expires_at=2000.0,
            tags={"tag1", "tag2"},
            scope=InvalidationScope.COMPONENT,
            component_id="ProductCard",
        )
        
        data = entry.to_dict()
        
        assert data["hash"] == "abc123"
        assert data["createdAt"] == 1000.0
        assert data["expiresAt"] == 2000.0
        assert "tag1" in data["tags"]
        assert data["scope"] == "component"
        assert data["componentId"] == "ProductCard"


class TestISRCache:
    """Tests for ISRCache."""
    
    def test_cache_creation(self):
        """Test cache creation."""
        cache = ISRCache()
        
        assert cache._cache == {}
        assert cache._tags == {}
    
    def test_set_and_get(self):
        """Test setting and getting cache entries."""
        cache = ISRCache()
        config = RevalidateConfig(seconds=60)
        
        entry = cache.set("/products", "<div>Products</div>", config)
        result = cache.get("/products")
        
        assert result is not None
        assert result.content == "<div>Products</div>"
    
    def test_get_nonexistent(self):
        """Test getting nonexistent entry."""
        cache = ISRCache()
        result = cache.get("/nonexistent")
        
        assert result is None
    
    def test_delete(self):
        """Test deleting cache entry."""
        cache = ISRCache()
        config = RevalidateConfig()
        
        cache.set("/test", "content", config)
        assert cache.get("/test") is not None
        
        deleted = cache.delete("/test")
        
        assert deleted is True
        assert cache.get("/test") is None
    
    def test_delete_nonexistent(self):
        """Test deleting nonexistent entry."""
        cache = ISRCache()
        deleted = cache.delete("/nonexistent")
        
        assert deleted is False
    
    def test_invalidate_by_tag(self):
        """Test tag-based invalidation."""
        cache = ISRCache()
        
        cache.set("/product/1", "P1", RevalidateConfig(tags=["products"]))
        cache.set("/product/2", "P2", RevalidateConfig(tags=["products"]))
        cache.set("/about", "About", RevalidateConfig(tags=["static"]))
        
        count = cache.invalidate_by_tag("products")
        
        assert count == 2
        assert cache.get("/product/1") is None
        assert cache.get("/product/2") is None
        assert cache.get("/about") is not None
    
    def test_invalidate_by_path(self):
        """Test path-based invalidation."""
        cache = ISRCache()
        
        cache.set("/products/1", "P1", RevalidateConfig())
        cache.set("/products/2", "P2", RevalidateConfig())
        cache.set("/about", "About", RevalidateConfig())
        
        count = cache.invalidate_by_path("/products")
        
        assert count == 2
        assert cache.get("/products/1") is None
        assert cache.get("/about") is not None
    
    def test_invalidate_by_component(self):
        """Test component-based invalidation."""
        cache = ISRCache()
        
        cache.set(
            "/page1:card",
            "Card1",
            RevalidateConfig(scope=InvalidationScope.COMPONENT),
            component_id="ProductCard"
        )
        cache.set(
            "/page2:card",
            "Card2",
            RevalidateConfig(scope=InvalidationScope.COMPONENT),
            component_id="ProductCard"
        )
        cache.set(
            "/page1:header",
            "Header",
            RevalidateConfig(scope=InvalidationScope.COMPONENT),
            component_id="Header"
        )
        
        count = cache.invalidate_by_component("ProductCard")
        
        assert count == 2
        assert cache.get("/page1:card") is None
        assert cache.get("/page1:header") is not None
    
    def test_cache_stats(self):
        """Test cache statistics."""
        cache = ISRCache()
        
        cache.set("/p1", "c1", RevalidateConfig(seconds=3600, tags=["a"]))
        cache.set("/p2", "c2", RevalidateConfig(seconds=3600, tags=["b"]))
        
        stats = cache.get_stats()
        
        assert stats["total_entries"] == 2
        assert "a" in stats["tags"]
        assert "b" in stats["tags"]


class TestRevalidateDecorator:
    """Tests for @revalidate decorator."""
    
    def test_basic_revalidate(self):
        """Test basic revalidate decorator."""
        @revalidate(seconds=60)
        def get_products():
            return "<div>Products</div>"
        
        assert hasattr(get_products, '_is_isr')
        assert get_products._is_isr is True
        assert get_products._revalidate_config.seconds == 60
    
    def test_revalidate_with_tags(self):
        """Test revalidate with tags."""
        @revalidate(tags=["products", "featured"])
        def get_featured():
            return "<div>Featured</div>"
        
        config = get_featured._revalidate_config
        assert "products" in config.tags
        assert "featured" in config.tags
    
    def test_revalidate_component_scope(self):
        """Test revalidate with component scope."""
        @revalidate(scope=InvalidationScope.COMPONENT)
        def product_card(id):
            return f"<div>Product {id}</div>"
        
        config = product_card._revalidate_config
        assert config.scope == InvalidationScope.COMPONENT
    
    def test_decorated_function_works(self):
        """Test decorated function still works."""
        call_count = 0
        
        @revalidate(seconds=60)
        def counter():
            nonlocal call_count
            call_count += 1
            return f"<div>Count: {call_count}</div>"
        
        result = counter()
        assert "Count:" in result


class TestRevalidationFunctions:
    """Tests for revalidation functions."""
    
    @pytest.mark.asyncio
    async def test_revalidate_path(self):
        """Test revalidate_path function."""
        # Initialize fresh cache
        cache = init_isr_cache()
        cache.set("/test", "content", RevalidateConfig())
        
        result = await revalidate_path("/test")
        
        assert result["revalidated"] is True
        assert result["path"] == "/test"
        assert result["invalidated_entries"] >= 0
    
    @pytest.mark.asyncio
    async def test_revalidate_tag(self):
        """Test revalidate_tag function."""
        cache = init_isr_cache()
        cache.set("/p1", "c1", RevalidateConfig(tags=["test-tag"]))
        
        result = await revalidate_tag("test-tag")
        
        assert result["revalidated"] is True
        assert result["tag"] == "test-tag"
    
    @pytest.mark.asyncio
    async def test_revalidate_component(self):
        """Test revalidate_component function."""
        cache = init_isr_cache()
        cache.set(
            "/test:comp",
            "content",
            RevalidateConfig(scope=InvalidationScope.COMPONENT),
            component_id="TestComponent"
        )
        
        result = await revalidate_component("TestComponent")
        
        assert result["revalidated"] is True
        assert result["component"] == "TestComponent"


class TestInvalidationScope:
    """Tests for InvalidationScope enum."""
    
    def test_all_scopes_exist(self):
        """Test all invalidation scopes are defined."""
        assert InvalidationScope.PAGE.value == "page"
        assert InvalidationScope.COMPONENT.value == "component"
        assert InvalidationScope.RESOURCE.value == "resource"
        assert InvalidationScope.TAG.value == "tag"


class TestRegenerationWorker:
    """Tests for RegenerationWorker."""
    
    @pytest.mark.asyncio
    async def test_worker_start_stop(self):
        """Test worker start and stop."""
        cache = ISRCache()
        worker = RegenerationWorker(cache)
        
        await worker.start()
        assert worker._running is True
        
        await worker.stop()
        assert worker._running is False
    
    def test_register_regenerator(self):
        """Test registering regenerator function."""
        cache = ISRCache()
        worker = RegenerationWorker(cache)
        
        def regenerate_test():
            return "new content"
        
        worker.register_regenerator("test_key", regenerate_test)
        
        assert "test_key" in worker._regenerators


class TestCachePersistence:
    """Tests for cache persistence."""
    
    def test_cache_with_directory(self, tmp_path):
        """Test cache with disk persistence."""
        cache_dir = tmp_path / "cache"
        cache = ISRCache(cache_dir)
        
        cache.set("/test", "content", RevalidateConfig())
        
        # Check file was created
        files = list(cache_dir.glob("*.json"))
        assert len(files) > 0
    
    def test_load_from_disk(self, tmp_path):
        """Test loading cache from disk."""
        cache_dir = tmp_path / "cache"
        
        # Create cache and add entry
        cache1 = ISRCache(cache_dir)
        cache1.set("/test", "content", RevalidateConfig(tags=["tag1"]))
        
        # Create new cache and load
        cache2 = ISRCache(cache_dir)
        count = cache2.load_from_disk()
        
        assert count == 1
        entry = cache2.get("/test")
        assert entry is not None
        assert entry.content == "content"

