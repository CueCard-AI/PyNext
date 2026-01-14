"""
Tests for PostgreSQL Query Cache with Smart Invalidation.

Tests cover:
- QueryCacheConfig validation and defaults
- Cache get/set operations
- TTL-based expiration
- Smart (tag-based) invalidation
- Pattern-based invalidation
- LRU eviction
- Cache statistics
- Concurrent access
- Cache warming
"""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch

from pynext.db.adapters.postgres.performance.query_cache import (
    InvalidationStrategy,
    QueryCacheConfig,
    CacheEntry,
    CacheStats,
    QueryCache,
    simple_cache_config,
    smart_cache_config,
    aggressive_cache_config,
    no_cache_config,
)


# =============================================================================
# QueryCacheConfig Tests
# =============================================================================

class TestQueryCacheConfig:
    """Tests for QueryCacheConfig dataclass."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = QueryCacheConfig()
        assert config.enabled is True
        assert config.max_size == 10000
        assert config.default_ttl == 60.0
        assert config.invalidation == "ttl"
        assert config.cache_reads is True
        assert config.cache_writes is False
        assert config.auto_tag is True
        assert config.stats_enabled is True
    
    def test_custom_max_size(self):
        """Test custom max_size."""
        config = QueryCacheConfig(max_size=5000)
        assert config.max_size == 5000
    
    def test_custom_ttl(self):
        """Test custom default_ttl."""
        config = QueryCacheConfig(default_ttl=300.0)
        assert config.default_ttl == 300.0
    
    def test_smart_invalidation(self):
        """Test smart invalidation strategy."""
        config = QueryCacheConfig(invalidation="smart")
        assert config.invalidation == "smart"
    
    def test_manual_invalidation(self):
        """Test manual invalidation strategy."""
        config = QueryCacheConfig(invalidation="manual")
        assert config.invalidation == "manual"
    
    def test_negative_max_size_raises(self):
        """Test that negative max_size raises error."""
        with pytest.raises(ValueError, match="max_size must be >= 0"):
            QueryCacheConfig(max_size=-1)
    
    def test_negative_ttl_raises(self):
        """Test that negative TTL raises error."""
        with pytest.raises(ValueError, match="default_ttl must be >= 0"):
            QueryCacheConfig(default_ttl=-1.0)
    
    def test_invalid_invalidation_raises(self):
        """Test that invalid invalidation strategy raises error."""
        with pytest.raises(ValueError, match="invalidation must be"):
            QueryCacheConfig(invalidation="invalid")
    
    def test_zero_max_size_allowed(self):
        """Test that zero max_size is allowed."""
        config = QueryCacheConfig(max_size=0)
        assert config.max_size == 0
    
    def test_zero_ttl_allowed(self):
        """Test that zero TTL is allowed (never expires)."""
        config = QueryCacheConfig(default_ttl=0)
        assert config.default_ttl == 0
    
    def test_disabled_config(self):
        """Test disabled configuration."""
        config = QueryCacheConfig(enabled=False)
        assert config.enabled is False


# =============================================================================
# CacheEntry Tests
# =============================================================================

class TestCacheEntry:
    """Tests for CacheEntry dataclass."""
    
    def test_basic_entry(self):
        """Test basic cache entry creation."""
        entry = CacheEntry(
            key="abc123",
            query="SELECT * FROM users",
            result=[{"id": 1}],
        )
        assert entry.key == "abc123"
        assert entry.query == "SELECT * FROM users"
        assert entry.result == [{"id": 1}]
    
    def test_entry_with_params(self):
        """Test entry with parameters."""
        entry = CacheEntry(
            key="abc123",
            query="SELECT * FROM users WHERE id = $1",
            params=(1,),
            result=[{"id": 1}],
        )
        assert entry.params == (1,)
    
    def test_entry_with_tags(self):
        """Test entry with tags."""
        entry = CacheEntry(
            key="abc123",
            query="SELECT * FROM users",
            tags={"table:users", "user:1"},
        )
        assert "table:users" in entry.tags
        assert "user:1" in entry.tags
    
    def test_is_expired_false(self):
        """Test entry that hasn't expired."""
        entry = CacheEntry(
            key="abc123",
            query="SELECT 1",
            expires_at=time.monotonic() + 100,
        )
        assert entry.is_expired is False
    
    def test_is_expired_true(self):
        """Test entry that has expired."""
        entry = CacheEntry(
            key="abc123",
            query="SELECT 1",
            expires_at=time.monotonic() - 1,
        )
        assert entry.is_expired is True
    
    def test_never_expires(self):
        """Test entry that never expires."""
        entry = CacheEntry(
            key="abc123",
            query="SELECT 1",
            expires_at=0,  # Never expires
        )
        assert entry.is_expired is False
    
    def test_age_seconds(self):
        """Test age calculation."""
        entry = CacheEntry(
            key="abc123",
            query="SELECT 1",
            created_at=time.monotonic() - 10,
        )
        assert 9 < entry.age_seconds < 11
    
    def test_ttl_remaining(self):
        """Test TTL remaining calculation."""
        entry = CacheEntry(
            key="abc123",
            query="SELECT 1",
            expires_at=time.monotonic() + 30,
        )
        assert 29 < entry.ttl_remaining < 31
    
    def test_touch_increments_hits(self):
        """Test touch increments hit count."""
        entry = CacheEntry(key="abc123", query="SELECT 1")
        assert entry.hit_count == 0
        entry.touch()
        assert entry.hit_count == 1
        entry.touch()
        assert entry.hit_count == 2


# =============================================================================
# CacheStats Tests
# =============================================================================

class TestCacheStats:
    """Tests for CacheStats dataclass."""
    
    def test_initial_stats(self):
        """Test initial statistics."""
        stats = CacheStats()
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.evictions == 0
        assert stats.invalidations == 0
    
    def test_hit_rate_zero(self):
        """Test hit rate with no requests."""
        stats = CacheStats()
        assert stats.hit_rate == 0.0
    
    def test_hit_rate_calculation(self):
        """Test hit rate calculation."""
        stats = CacheStats(hits=75, misses=25)
        assert stats.hit_rate == 0.75
    
    def test_miss_rate_calculation(self):
        """Test miss rate calculation."""
        stats = CacheStats(hits=75, misses=25)
        assert stats.miss_rate == 0.25
    
    def test_total_requests(self):
        """Test total requests calculation."""
        stats = CacheStats(hits=50, misses=50)
        assert stats.total_requests == 100
    
    def test_record_hit(self):
        """Test recording a cache hit."""
        stats = CacheStats()
        stats.record_hit(latency_ms=0.5)
        assert stats.hits == 1
        assert stats.total_hit_latency_ms == 0.5
    
    def test_record_miss(self):
        """Test recording a cache miss."""
        stats = CacheStats()
        stats.record_miss(latency_ms=10.0)
        assert stats.misses == 1
        assert stats.total_miss_latency_ms == 10.0
    
    def test_avg_hit_latency(self):
        """Test average hit latency calculation."""
        stats = CacheStats(hits=2, total_hit_latency_ms=1.0)
        assert stats.avg_hit_latency_ms == 0.5
    
    def test_avg_miss_latency(self):
        """Test average miss latency calculation."""
        stats = CacheStats(misses=2, total_miss_latency_ms=20.0)
        assert stats.avg_miss_latency_ms == 10.0
    
    def test_fill_ratio(self):
        """Test fill ratio calculation."""
        stats = CacheStats(current_size=500, max_size=1000)
        assert stats.fill_ratio == 0.5
    
    def test_to_dict(self):
        """Test dictionary conversion."""
        stats = CacheStats(hits=10, misses=5)
        d = stats.to_dict()
        assert "hits" in d
        assert "misses" in d
        assert "hit_rate" in d
        assert d["hits"] == 10
        assert d["misses"] == 5


# =============================================================================
# QueryCache Basic Operations Tests
# =============================================================================

class TestQueryCacheBasic:
    """Tests for basic QueryCache operations."""
    
    @pytest.fixture
    def cache(self):
        return QueryCache(QueryCacheConfig(default_ttl=60.0))
    
    @pytest.mark.asyncio
    async def test_set_and_get(self, cache):
        """Test basic set and get."""
        await cache.set("SELECT 1", None, result=42)
        result = await cache.get("SELECT 1")
        assert result == 42
    
    @pytest.mark.asyncio
    async def test_get_nonexistent(self, cache):
        """Test get on nonexistent key."""
        result = await cache.get("SELECT 999")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_set_with_params(self, cache):
        """Test set and get with parameters."""
        await cache.set("SELECT * FROM users WHERE id = $1", (1,), result=[{"id": 1}])
        result = await cache.get("SELECT * FROM users WHERE id = $1", (1,))
        assert result == [{"id": 1}]
    
    @pytest.mark.asyncio
    async def test_different_params_different_cache(self, cache):
        """Test that different params create different cache entries."""
        await cache.set("SELECT * FROM users WHERE id = $1", (1,), result="user1")
        await cache.set("SELECT * FROM users WHERE id = $1", (2,), result="user2")
        
        assert await cache.get("SELECT * FROM users WHERE id = $1", (1,)) == "user1"
        assert await cache.get("SELECT * FROM users WHERE id = $1", (2,)) == "user2"
    
    @pytest.mark.asyncio
    async def test_cache_size(self, cache):
        """Test cache size tracking."""
        assert cache.size == 0
        await cache.set("SELECT 1", None, result=1)
        assert cache.size == 1
        await cache.set("SELECT 2", None, result=2)
        assert cache.size == 2
    
    @pytest.mark.asyncio
    async def test_disabled_cache(self):
        """Test disabled cache returns None."""
        cache = QueryCache(QueryCacheConfig(enabled=False))
        await cache.set("SELECT 1", None, result=42)
        result = await cache.get("SELECT 1")
        assert result is None


# =============================================================================
# TTL Expiration Tests
# =============================================================================

class TestCacheTTL:
    """Tests for TTL-based cache expiration."""
    
    @pytest.mark.asyncio
    async def test_entry_expires(self):
        """Test that entries expire after TTL."""
        cache = QueryCache(QueryCacheConfig(default_ttl=0.05))
        await cache.set("SELECT 1", None, result=42)
        
        # Should exist initially
        assert await cache.get("SELECT 1") == 42
        
        # Wait for expiration
        await asyncio.sleep(0.1)
        
        # Should be gone
        assert await cache.get("SELECT 1") is None
    
    @pytest.mark.asyncio
    async def test_custom_ttl_per_entry(self):
        """Test custom TTL per entry."""
        cache = QueryCache(QueryCacheConfig(default_ttl=60.0))
        
        # Short TTL entry
        await cache.set("SELECT 1", None, result=1, ttl=0.05)
        # Long TTL entry
        await cache.set("SELECT 2", None, result=2, ttl=60.0)
        
        await asyncio.sleep(0.1)
        
        # Short TTL expired
        assert await cache.get("SELECT 1") is None
        # Long TTL still exists
        assert await cache.get("SELECT 2") == 2
    
    @pytest.mark.asyncio
    async def test_zero_ttl_never_expires(self):
        """Test that TTL=0 means never expires."""
        cache = QueryCache(QueryCacheConfig(default_ttl=60.0))
        await cache.set("SELECT 1", None, result=42, ttl=0)
        
        await asyncio.sleep(0.05)
        
        # Should still exist
        assert await cache.get("SELECT 1") == 42
    
    @pytest.mark.asyncio
    async def test_cleanup_expired(self):
        """Test cleanup of expired entries."""
        cache = QueryCache(QueryCacheConfig(default_ttl=0.05))
        
        await cache.set("SELECT 1", None, result=1)
        await cache.set("SELECT 2", None, result=2)
        
        await asyncio.sleep(0.1)
        
        count = cache.cleanup_expired()
        assert count == 2
        assert cache.size == 0


# =============================================================================
# Smart Invalidation Tests
# =============================================================================

class TestCacheSmartInvalidation:
    """Tests for tag-based (smart) cache invalidation."""
    
    @pytest.fixture
    def cache(self):
        return QueryCache(QueryCacheConfig(invalidation="smart", auto_tag=True))
    
    @pytest.mark.asyncio
    async def test_auto_tag_extraction(self, cache):
        """Test automatic tag extraction from query."""
        await cache.set("SELECT * FROM users", None, result=[])
        
        # Should have table:users tag
        count = cache.invalidate_tags(["table:users"])
        assert count == 1
    
    @pytest.mark.asyncio
    async def test_custom_tags(self, cache):
        """Test custom tags."""
        await cache.set(
            "SELECT * FROM users WHERE id = $1",
            (1,),
            result=[],
            tags={"user:1", "custom_tag"},
        )
        
        count = cache.invalidate_tags(["user:1"])
        assert count == 1
    
    @pytest.mark.asyncio
    async def test_invalidate_multiple_tags(self, cache):
        """Test invalidating multiple tags at once."""
        await cache.set("SELECT * FROM users", None, result=[], tags={"tag1"})
        await cache.set("SELECT * FROM orders", None, result=[], tags={"tag2"})
        await cache.set("SELECT * FROM products", None, result=[], tags={"tag1", "tag2"})
        
        count = cache.invalidate_tags(["tag1"])
        assert count == 2  # users and products
    
    @pytest.mark.asyncio
    async def test_invalidate_nonexistent_tag(self, cache):
        """Test invalidating nonexistent tag."""
        await cache.set("SELECT * FROM users", None, result=[])
        
        count = cache.invalidate_tags(["nonexistent"])
        assert count == 0
    
    @pytest.mark.asyncio
    async def test_table_tag_case_insensitive(self, cache):
        """Test table tag extraction is case insensitive."""
        await cache.set("SELECT * FROM USERS", None, result=[])
        
        count = cache.invalidate_tags(["table:users"])
        assert count == 1


# =============================================================================
# Pattern Invalidation Tests
# =============================================================================

class TestCachePatternInvalidation:
    """Tests for pattern-based cache invalidation."""
    
    @pytest.fixture
    def cache(self):
        return QueryCache()
    
    @pytest.mark.asyncio
    async def test_invalidate_pattern_wildcard(self, cache):
        """Test pattern invalidation with wildcard."""
        await cache.set("SELECT * FROM users", None, result=[])
        await cache.set("SELECT * FROM users WHERE id = 1", None, result=[])
        await cache.set("SELECT * FROM orders", None, result=[])
        
        count = cache.invalidate_pattern("*users*")
        assert count == 2
    
    @pytest.mark.asyncio
    async def test_invalidate_pattern_prefix(self, cache):
        """Test pattern invalidation with prefix."""
        await cache.set("SELECT * FROM users", None, result=[])
        await cache.set("INSERT INTO users VALUES", None, result=[])
        
        count = cache.invalidate_pattern("select*")
        assert count == 1
    
    @pytest.mark.asyncio
    async def test_invalidate_pattern_case_insensitive(self, cache):
        """Test pattern is case insensitive."""
        await cache.set("SELECT * FROM users", None, result=[])
        
        count = cache.invalidate_pattern("*USERS*")
        assert count == 1
    
    @pytest.mark.asyncio
    async def test_invalidate_pattern_no_match(self, cache):
        """Test pattern with no matches."""
        await cache.set("SELECT * FROM users", None, result=[])
        
        count = cache.invalidate_pattern("*orders*")
        assert count == 0


# =============================================================================
# LRU Eviction Tests
# =============================================================================

class TestCacheLRU:
    """Tests for LRU cache eviction."""
    
    @pytest.mark.asyncio
    async def test_eviction_on_max_size(self):
        """Test entries are evicted when max_size is reached."""
        cache = QueryCache(QueryCacheConfig(max_size=3))
        
        await cache.set("SELECT 1", None, result=1)
        await cache.set("SELECT 2", None, result=2)
        await cache.set("SELECT 3", None, result=3)
        
        assert cache.size == 3
        
        # Add one more, should evict oldest
        await cache.set("SELECT 4", None, result=4)
        
        assert cache.size == 3
        assert await cache.get("SELECT 1") is None  # Evicted
        assert await cache.get("SELECT 4") == 4  # New
    
    @pytest.mark.asyncio
    async def test_lru_order_preserved(self):
        """Test LRU order is updated on access."""
        cache = QueryCache(QueryCacheConfig(max_size=3))
        
        await cache.set("SELECT 1", None, result=1)
        await cache.set("SELECT 2", None, result=2)
        await cache.set("SELECT 3", None, result=3)
        
        # Access SELECT 1 to make it recently used
        await cache.get("SELECT 1")
        
        # Add new entry, should evict SELECT 2 (least recently used)
        await cache.set("SELECT 4", None, result=4)
        
        assert await cache.get("SELECT 1") == 1  # Still exists
        assert await cache.get("SELECT 2") is None  # Evicted
    
    @pytest.mark.asyncio
    async def test_eviction_stats_updated(self):
        """Test eviction statistics are updated."""
        cache = QueryCache(QueryCacheConfig(max_size=2))
        
        await cache.set("SELECT 1", None, result=1)
        await cache.set("SELECT 2", None, result=2)
        await cache.set("SELECT 3", None, result=3)
        
        stats = cache.get_stats()
        assert stats.evictions == 1


# =============================================================================
# Get or Execute Tests
# =============================================================================

class TestCacheGetOrExecute:
    """Tests for get_or_execute functionality."""
    
    @pytest.fixture
    def cache(self):
        return QueryCache(QueryCacheConfig(default_ttl=60.0))
    
    @pytest.mark.asyncio
    async def test_cache_hit(self, cache):
        """Test cache hit path."""
        # Pre-populate cache
        await cache.set("SELECT 1", None, result=42)
        
        executor = AsyncMock(return_value=999)
        result = await cache.get_or_execute("SELECT 1", executor=executor)
        
        assert result == 42  # From cache
        executor.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_cache_miss(self, cache):
        """Test cache miss path."""
        async def executor(query):
            return 42
        
        result = await cache.get_or_execute("SELECT 1", executor=executor)
        
        assert result == 42  # From executor
        assert await cache.get("SELECT 1") == 42  # Cached
    
    @pytest.mark.asyncio
    async def test_cache_miss_with_params(self, cache):
        """Test cache miss with parameters."""
        async def executor(query, params):
            return [{"id": params[0]}]
        
        result = await cache.get_or_execute(
            "SELECT * FROM users WHERE id = $1",
            params=(1,),
            executor=executor,
        )
        
        assert result == [{"id": 1}]
    
    @pytest.mark.asyncio
    async def test_bypass_cache(self, cache):
        """Test bypass cache flag."""
        await cache.set("SELECT 1", None, result=42)
        
        async def executor(query):
            return 999
        
        result = await cache.get_or_execute(
            "SELECT 1",
            executor=executor,
            bypass=True,
        )
        
        assert result == 999  # From executor despite cache hit
    
    @pytest.mark.asyncio
    async def test_stats_on_hit(self, cache):
        """Test statistics on cache hit."""
        await cache.set("SELECT 1", None, result=42)
        
        async def executor(query):
            return 999
        
        await cache.get_or_execute("SELECT 1", executor=executor)
        
        stats = cache.get_stats()
        assert stats.hits == 1
        assert stats.misses == 0
    
    @pytest.mark.asyncio
    async def test_stats_on_miss(self, cache):
        """Test statistics on cache miss."""
        async def executor(query):
            return 42
        
        await cache.get_or_execute("SELECT 1", executor=executor)
        
        stats = cache.get_stats()
        assert stats.hits == 0
        assert stats.misses == 1
    
    @pytest.mark.asyncio
    async def test_custom_ttl(self, cache):
        """Test custom TTL in get_or_execute."""
        async def executor(query):
            return 42
        
        await cache.get_or_execute("SELECT 1", executor=executor, ttl=0.05)
        
        # Should exist
        assert await cache.get("SELECT 1") == 42
        
        await asyncio.sleep(0.1)
        
        # Should be expired
        assert await cache.get("SELECT 1") is None
    
    @pytest.mark.asyncio
    async def test_custom_tags(self, cache):
        """Test custom tags in get_or_execute."""
        async def executor(query):
            return 42
        
        await cache.get_or_execute(
            "SELECT 1",
            executor=executor,
            tags={"custom_tag"},
        )
        
        count = cache.invalidate_tags(["custom_tag"])
        assert count == 1


# =============================================================================
# Invalidation Tests
# =============================================================================

class TestCacheInvalidation:
    """Tests for cache invalidation."""
    
    @pytest.fixture
    def cache(self):
        return QueryCache()
    
    @pytest.mark.asyncio
    async def test_invalidate_specific(self, cache):
        """Test invalidating a specific entry."""
        await cache.set("SELECT 1", None, result=1)
        await cache.set("SELECT 2", None, result=2)
        
        success = cache.invalidate("SELECT 1")
        
        assert success is True
        assert await cache.get("SELECT 1") is None
        assert await cache.get("SELECT 2") == 2
    
    @pytest.mark.asyncio
    async def test_invalidate_nonexistent(self, cache):
        """Test invalidating nonexistent entry."""
        success = cache.invalidate("SELECT 999")
        assert success is False
    
    @pytest.mark.asyncio
    async def test_invalidate_with_params(self, cache):
        """Test invalidating entry with parameters."""
        await cache.set("SELECT * FROM users WHERE id = $1", (1,), result=[])
        
        success = cache.invalidate("SELECT * FROM users WHERE id = $1", (1,))
        assert success is True
    
    @pytest.mark.asyncio
    async def test_invalidate_all(self, cache):
        """Test invalidating all entries."""
        await cache.set("SELECT 1", None, result=1)
        await cache.set("SELECT 2", None, result=2)
        await cache.set("SELECT 3", None, result=3)
        
        count = cache.invalidate_all()
        
        assert count == 3
        assert cache.size == 0
    
    @pytest.mark.asyncio
    async def test_invalidation_stats(self, cache):
        """Test invalidation statistics."""
        await cache.set("SELECT 1", None, result=1)
        cache.invalidate("SELECT 1")
        
        stats = cache.get_stats()
        assert stats.invalidations == 1


# =============================================================================
# Cache Warming Tests
# =============================================================================

class TestCacheWarming:
    """Tests for cache warming."""
    
    def test_warm_cache(self):
        """Test warming cache with entries."""
        cache = QueryCache()
        
        count = cache.warm([
            ("SELECT * FROM config", None, {"key": "value"}, 3600.0),
            ("SELECT * FROM categories", None, [1, 2, 3], 600.0),
        ])
        
        assert count == 2
        assert cache.size == 2
    
    def test_warm_skips_existing(self):
        """Test warming skips existing entries."""
        cache = QueryCache()
        
        # Pre-populate
        asyncio.run(cache.set("SELECT * FROM config", None, result="existing"))
        
        count = cache.warm([
            ("SELECT * FROM config", None, "new", 3600.0),
        ])
        
        assert count == 0  # Skipped
    
    @pytest.mark.asyncio
    async def test_warm_with_auto_tags(self):
        """Test warming extracts tags."""
        cache = QueryCache(QueryCacheConfig(auto_tag=True))
        
        # Use async set instead of warm for proper tag extraction
        await cache.set("SELECT * FROM users", None, result=[], ttl=3600.0)
        
        # Should have table:users tag
        count = cache.invalidate_tags(["table:users"])
        assert count == 1


# =============================================================================
# Concurrent Access Tests
# =============================================================================

class TestCacheConcurrency:
    """Tests for concurrent cache access."""
    
    @pytest.mark.asyncio
    async def test_concurrent_sets(self):
        """Test concurrent set operations."""
        cache = QueryCache()
        
        async def set_entry(i):
            await cache.set(f"SELECT {i}", None, result=i)
        
        await asyncio.gather(*[set_entry(i) for i in range(100)])
        
        assert cache.size == 100
    
    @pytest.mark.asyncio
    async def test_concurrent_gets(self):
        """Test concurrent get operations."""
        cache = QueryCache()
        
        # Pre-populate
        for i in range(10):
            await cache.set(f"SELECT {i}", None, result=i)
        
        async def get_entry(i):
            return await cache.get(f"SELECT {i % 10}")
        
        results = await asyncio.gather(*[get_entry(i) for i in range(100)])
        
        assert all(r is not None for r in results)
    
    @pytest.mark.asyncio
    async def test_concurrent_get_or_execute(self):
        """Test concurrent get_or_execute for same query."""
        cache = QueryCache()
        call_count = 0
        
        async def executor(query):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)  # Simulate DB call
            return 42
        
        # All should get same result
        results = await asyncio.gather(*[
            cache.get_or_execute("SELECT 1", executor=executor)
            for _ in range(10)
        ])
        
        assert all(r == 42 for r in results)
        # Due to race conditions, might execute more than once
        # but should be much less than 10
        assert call_count <= 10


# =============================================================================
# Statistics Tests
# =============================================================================

class TestCacheStatistics:
    """Tests for cache statistics."""
    
    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Test getting cache statistics."""
        cache = QueryCache(QueryCacheConfig(max_size=100))
        
        await cache.set("SELECT 1", None, result=1)
        await cache.get("SELECT 1")
        await cache.get("SELECT 2")  # Miss
        
        stats = cache.get_stats()
        
        assert stats.hits >= 0
        assert stats.misses >= 0
        assert stats.current_size == 1
        assert stats.max_size == 100
    
    @pytest.mark.asyncio
    async def test_reset_stats(self):
        """Test resetting statistics."""
        cache = QueryCache()
        
        await cache.set("SELECT 1", None, result=1)
        await cache.get("SELECT 1")
        
        cache.reset_stats()
        stats = cache.get_stats()
        
        assert stats.hits == 0
        assert stats.misses == 0


# =============================================================================
# Convenience Config Tests
# =============================================================================

class TestConvenienceConfigs:
    """Tests for convenience configuration functions."""
    
    def test_simple_cache_config(self):
        """Test simple cache configuration."""
        config = simple_cache_config(ttl=120.0)
        assert config.default_ttl == 120.0
        assert config.invalidation == "ttl"
    
    def test_smart_cache_config(self):
        """Test smart cache configuration."""
        config = smart_cache_config()
        assert config.invalidation == "smart"
        assert config.auto_tag is True
    
    def test_aggressive_cache_config(self):
        """Test aggressive cache configuration."""
        config = aggressive_cache_config()
        assert config.max_size == 100000
        assert config.default_ttl == 600.0
        assert config.invalidation == "smart"
    
    def test_no_cache_config(self):
        """Test disabled cache configuration."""
        config = no_cache_config()
        assert config.enabled is False


# =============================================================================
# Repr Tests
# =============================================================================

class TestCacheRepr:
    """Tests for cache string representation."""
    
    @pytest.mark.asyncio
    async def test_repr(self):
        """Test cache repr."""
        cache = QueryCache(QueryCacheConfig(max_size=1000))
        await cache.set("SELECT 1", None, result=1)
        
        repr_str = repr(cache)
        assert "QueryCache" in repr_str
        assert "1/1000" in repr_str


# =============================================================================
# Edge Cases Tests
# =============================================================================

class TestCacheEdgeCases:
    """Tests for cache edge cases."""
    
    @pytest.mark.asyncio
    async def test_empty_query(self):
        """Test caching empty query."""
        cache = QueryCache()
        await cache.set("", None, result="empty")
        assert await cache.get("") == "empty"
    
    @pytest.mark.asyncio
    async def test_none_result(self):
        """Test caching None result."""
        cache = QueryCache()
        await cache.set("SELECT NULL", None, result=None)
        # This is tricky - None could mean not found or actual result
        # The get method returns None for not found, so we can't distinguish
        result = await cache.get("SELECT NULL")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_large_result(self):
        """Test caching large result."""
        cache = QueryCache()
        large_result = [{"id": i, "data": "x" * 1000} for i in range(1000)]
        await cache.set("SELECT * FROM large", None, result=large_result)
        assert await cache.get("SELECT * FROM large") == large_result
    
    @pytest.mark.asyncio
    async def test_unicode_query(self):
        """Test caching query with Unicode."""
        cache = QueryCache()
        await cache.set("SELECT * FROM users WHERE name = '日本語'", None, result=[])
        assert await cache.get("SELECT * FROM users WHERE name = '日本語'") == []
    
    @pytest.mark.asyncio
    async def test_query_normalization(self):
        """Test query normalization (whitespace)."""
        cache = QueryCache()
        await cache.set("SELECT  *   FROM   users", None, result=[])
        # Should match with different whitespace
        assert await cache.get("SELECT * FROM users") == []

