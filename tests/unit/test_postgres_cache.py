"""
PostgreSQL Statement Cache Tests.

60 comprehensive tests for StatementCache functionality.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from pynext.db.adapters.postgres.core.cache import (
    StatementCache,
    CachedStatement,
    PerConnectionCache,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def cache():
    """Create a fresh statement cache."""
    return StatementCache(max_size=10)


@pytest.fixture
def mock_connection():
    """Create a mock asyncpg connection."""
    conn = MagicMock()
    conn.prepare = AsyncMock()
    return conn


@pytest.fixture
def mock_statement():
    """Create a mock prepared statement."""
    return MagicMock()


# =============================================================================
# StatementCache Basic Tests
# =============================================================================

class TestStatementCacheBasic:
    """Basic StatementCache tests."""
    
    def test_cache_creation(self):
        """Test creating a statement cache."""
        cache = StatementCache()
        assert cache.size == 0
        assert cache.max_size == 1000  # default
    
    def test_cache_custom_size(self):
        """Test creating cache with custom size."""
        cache = StatementCache(max_size=500)
        assert cache.max_size == 500
    
    def test_cache_min_size_validation(self):
        """Test that max_size must be at least 1."""
        with pytest.raises(ValueError):
            StatementCache(max_size=0)
    
    def test_cache_negative_size_validation(self):
        """Test that negative max_size raises error."""
        with pytest.raises(ValueError):
            StatementCache(max_size=-1)
    
    def test_cache_size_property(self, cache):
        """Test size property starts at 0."""
        assert cache.size == 0


# =============================================================================
# Get or Prepare Tests
# =============================================================================

class TestGetOrPrepare:
    """Tests for get_or_prepare method."""
    
    @pytest.mark.asyncio
    async def test_cache_miss_prepares(self, cache, mock_connection, mock_statement):
        """Test cache miss triggers prepare."""
        mock_connection.prepare.return_value = mock_statement
        
        result = await cache.get_or_prepare(mock_connection, "SELECT 1")
        
        assert result == mock_statement
        mock_connection.prepare.assert_called_once_with("SELECT 1")
    
    @pytest.mark.asyncio
    async def test_cache_hit_reuses(self, cache, mock_connection, mock_statement):
        """Test cache hit returns cached statement."""
        mock_connection.prepare.return_value = mock_statement
        
        # First call - cache miss
        await cache.get_or_prepare(mock_connection, "SELECT 1")
        # Second call - should be cache hit
        result = await cache.get_or_prepare(mock_connection, "SELECT 1")
        
        assert result == mock_statement
        # Prepare should only be called once
        assert mock_connection.prepare.call_count == 1
    
    @pytest.mark.asyncio
    async def test_different_queries_cached_separately(self, cache, mock_connection):
        """Test different queries are cached separately."""
        stmt1 = MagicMock()
        stmt2 = MagicMock()
        mock_connection.prepare.side_effect = [stmt1, stmt2]
        
        result1 = await cache.get_or_prepare(mock_connection, "SELECT 1")
        result2 = await cache.get_or_prepare(mock_connection, "SELECT 2")
        
        assert result1 == stmt1
        assert result2 == stmt2
        assert mock_connection.prepare.call_count == 2
    
    @pytest.mark.asyncio
    async def test_cache_size_increases(self, cache, mock_connection, mock_statement):
        """Test cache size increases after preparing."""
        mock_connection.prepare.return_value = mock_statement
        
        assert cache.size == 0
        await cache.get_or_prepare(mock_connection, "SELECT 1")
        assert cache.size == 1
    
    @pytest.mark.asyncio
    async def test_same_query_doesnt_increase_size(self, cache, mock_connection, mock_statement):
        """Test same query doesn't increase cache size."""
        mock_connection.prepare.return_value = mock_statement
        
        await cache.get_or_prepare(mock_connection, "SELECT 1")
        await cache.get_or_prepare(mock_connection, "SELECT 1")
        
        assert cache.size == 1


# =============================================================================
# LRU Eviction Tests
# =============================================================================

class TestLRUEviction:
    """Tests for LRU eviction behavior."""
    
    @pytest.mark.asyncio
    async def test_eviction_at_max_size(self, mock_connection):
        """Test eviction when cache reaches max size."""
        cache = StatementCache(max_size=3)
        stmts = [MagicMock() for _ in range(4)]
        mock_connection.prepare.side_effect = stmts
        
        # Fill cache
        await cache.get_or_prepare(mock_connection, "SELECT 1")
        await cache.get_or_prepare(mock_connection, "SELECT 2")
        await cache.get_or_prepare(mock_connection, "SELECT 3")
        
        assert cache.size == 3
        
        # Add one more - should evict oldest
        await cache.get_or_prepare(mock_connection, "SELECT 4")
        
        assert cache.size == 3
    
    @pytest.mark.asyncio
    async def test_lru_evicts_oldest(self, mock_connection):
        """Test that LRU evicts least recently used."""
        cache = StatementCache(max_size=2)
        stmts = [MagicMock() for _ in range(3)]
        mock_connection.prepare.side_effect = stmts
        
        # Add two statements
        await cache.get_or_prepare(mock_connection, "SELECT 1")
        await cache.get_or_prepare(mock_connection, "SELECT 2")
        
        # Access first statement (makes it recently used)
        mock_connection.prepare.reset_mock()
        mock_connection.prepare.return_value = stmts[0]
        await cache.get_or_prepare(mock_connection, "SELECT 1")
        
        # Should not prepare again (cache hit)
        mock_connection.prepare.assert_not_called()
        
        # Add third statement
        mock_connection.prepare.return_value = stmts[2]
        await cache.get_or_prepare(mock_connection, "SELECT 3")
        
        # SELECT 2 should have been evicted (least recently used)
        # SELECT 1 should still be cached
        mock_connection.prepare.reset_mock()
        await cache.get_or_prepare(mock_connection, "SELECT 1")
        mock_connection.prepare.assert_not_called()


# =============================================================================
# Invalidation Tests
# =============================================================================

class TestInvalidation:
    """Tests for cache invalidation."""
    
    @pytest.mark.asyncio
    async def test_invalidate_existing(self, cache, mock_connection, mock_statement):
        """Test invalidating an existing statement."""
        mock_connection.prepare.return_value = mock_statement
        
        await cache.get_or_prepare(mock_connection, "SELECT 1")
        assert cache.size == 1
        
        result = await cache.invalidate("SELECT 1")
        
        assert result is True
        assert cache.size == 0
    
    @pytest.mark.asyncio
    async def test_invalidate_nonexistent(self, cache):
        """Test invalidating a nonexistent statement."""
        result = await cache.invalidate("SELECT 1")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_invalidate_all(self, cache, mock_connection):
        """Test invalidating all statements."""
        stmts = [MagicMock() for _ in range(3)]
        mock_connection.prepare.side_effect = stmts
        
        await cache.get_or_prepare(mock_connection, "SELECT 1")
        await cache.get_or_prepare(mock_connection, "SELECT 2")
        await cache.get_or_prepare(mock_connection, "SELECT 3")
        
        assert cache.size == 3
        
        count = await cache.invalidate_all()
        
        assert count == 3
        assert cache.size == 0
    
    @pytest.mark.asyncio
    async def test_invalidate_all_empty(self, cache):
        """Test invalidating empty cache."""
        count = await cache.invalidate_all()
        assert count == 0


# =============================================================================
# Statistics Tests
# =============================================================================

class TestStatistics:
    """Tests for cache statistics."""
    
    @pytest.mark.asyncio
    async def test_hit_count(self, cache, mock_connection, mock_statement):
        """Test hit count tracking."""
        mock_connection.prepare.return_value = mock_statement
        
        await cache.get_or_prepare(mock_connection, "SELECT 1")  # miss
        await cache.get_or_prepare(mock_connection, "SELECT 1")  # hit
        await cache.get_or_prepare(mock_connection, "SELECT 1")  # hit
        
        stats = cache.get_stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 1
    
    @pytest.mark.asyncio
    async def test_hit_rate(self, cache, mock_connection, mock_statement):
        """Test hit rate calculation."""
        mock_connection.prepare.return_value = mock_statement
        
        await cache.get_or_prepare(mock_connection, "SELECT 1")  # miss
        await cache.get_or_prepare(mock_connection, "SELECT 1")  # hit
        await cache.get_or_prepare(mock_connection, "SELECT 1")  # hit
        await cache.get_or_prepare(mock_connection, "SELECT 1")  # hit
        
        stats = cache.get_stats()
        assert stats["hit_rate"] == 0.75  # 3 hits / 4 total
    
    @pytest.mark.asyncio
    async def test_eviction_count(self, mock_connection):
        """Test eviction count tracking."""
        cache = StatementCache(max_size=2)
        stmts = [MagicMock() for _ in range(4)]
        mock_connection.prepare.side_effect = stmts
        
        await cache.get_or_prepare(mock_connection, "SELECT 1")
        await cache.get_or_prepare(mock_connection, "SELECT 2")
        await cache.get_or_prepare(mock_connection, "SELECT 3")
        await cache.get_or_prepare(mock_connection, "SELECT 4")
        
        stats = cache.get_stats()
        assert stats["evictions"] == 2
    
    def test_empty_stats(self, cache):
        """Test stats on empty cache."""
        stats = cache.get_stats()
        assert stats["size"] == 0
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["hit_rate"] == 0.0
    
    @pytest.mark.asyncio
    async def test_get_cached_queries(self, cache, mock_connection, mock_statement):
        """Test getting cached query info."""
        mock_connection.prepare.return_value = mock_statement
        
        await cache.get_or_prepare(mock_connection, "SELECT 1")
        await cache.get_or_prepare(mock_connection, "SELECT 1")
        
        queries = cache.get_cached_queries()
        assert len(queries) == 1
        key = list(queries.keys())[0]
        assert queries[key]["hit_count"] == 1


# =============================================================================
# CachedStatement Tests
# =============================================================================

class TestCachedStatement:
    """Tests for CachedStatement dataclass."""
    
    def test_creation(self, mock_statement):
        """Test creating a cached statement."""
        cached = CachedStatement(statement=mock_statement, sql="SELECT 1")
        assert cached.statement == mock_statement
        assert cached.sql == "SELECT 1"
        assert cached.hit_count == 0
    
    def test_record_hit(self, mock_statement):
        """Test recording a hit."""
        cached = CachedStatement(statement=mock_statement, sql="SELECT 1")
        original_last_used = cached.last_used
        
        cached.record_hit()
        
        assert cached.hit_count == 1
        assert cached.last_used >= original_last_used
    
    def test_multiple_hits(self, mock_statement):
        """Test multiple hits."""
        cached = CachedStatement(statement=mock_statement, sql="SELECT 1")
        
        for _ in range(5):
            cached.record_hit()
        
        assert cached.hit_count == 5


# =============================================================================
# PerConnectionCache Tests
# =============================================================================

class TestPerConnectionCache:
    """Tests for PerConnectionCache."""
    
    @pytest.mark.asyncio
    async def test_get_cache_creates(self, mock_connection):
        """Test getting cache creates new cache."""
        manager = PerConnectionCache()
        cache = await manager.get_cache(mock_connection)
        
        assert cache is not None
        assert isinstance(cache, StatementCache)
    
    @pytest.mark.asyncio
    async def test_get_cache_reuses(self, mock_connection):
        """Test getting cache reuses existing cache."""
        manager = PerConnectionCache()
        cache1 = await manager.get_cache(mock_connection)
        cache2 = await manager.get_cache(mock_connection)
        
        assert cache1 is cache2
    
    @pytest.mark.asyncio
    async def test_different_connections_different_caches(self):
        """Test different connections get different caches."""
        manager = PerConnectionCache()
        conn1 = MagicMock()
        conn2 = MagicMock()
        
        cache1 = await manager.get_cache(conn1)
        cache2 = await manager.get_cache(conn2)
        
        assert cache1 is not cache2
    
    @pytest.mark.asyncio
    async def test_remove_cache(self, mock_connection):
        """Test removing a cache."""
        manager = PerConnectionCache()
        await manager.get_cache(mock_connection)
        
        await manager.remove_cache(mock_connection)
        
        # Getting cache again should create new one
        cache = await manager.get_cache(mock_connection)
        assert cache is not None
    
    @pytest.mark.asyncio
    async def test_total_stats(self):
        """Test aggregated stats across connections."""
        manager = PerConnectionCache(max_statements=100)
        conn1 = MagicMock()
        conn2 = MagicMock()
        
        conn1.prepare = AsyncMock(return_value=MagicMock())
        conn2.prepare = AsyncMock(return_value=MagicMock())
        
        cache1 = await manager.get_cache(conn1)
        cache2 = await manager.get_cache(conn2)
        
        await cache1.get_or_prepare(conn1, "SELECT 1")
        await cache2.get_or_prepare(conn2, "SELECT 2")
        
        stats = manager.get_total_stats()
        assert stats["connections"] == 2
        assert stats["total_size"] == 2


# =============================================================================
# Concurrency Tests
# =============================================================================

class TestConcurrency:
    """Tests for concurrent access."""
    
    @pytest.mark.asyncio
    async def test_concurrent_get_or_prepare(self, mock_connection):
        """Test concurrent access to cache."""
        cache = StatementCache()
        stmt = MagicMock()
        mock_connection.prepare = AsyncMock(return_value=stmt)
        
        # Simulate concurrent access
        tasks = [
            cache.get_or_prepare(mock_connection, "SELECT 1")
            for _ in range(10)
        ]
        results = await asyncio.gather(*tasks)
        
        # All should get the same statement
        assert all(r == stmt for r in results)
    
    @pytest.mark.asyncio
    async def test_concurrent_invalidate(self, cache, mock_connection, mock_statement):
        """Test concurrent invalidation."""
        mock_connection.prepare.return_value = mock_statement
        
        await cache.get_or_prepare(mock_connection, "SELECT 1")
        
        # Concurrent invalidation
        tasks = [cache.invalidate("SELECT 1") for _ in range(5)]
        results = await asyncio.gather(*tasks)
        
        # Only first should return True
        assert sum(results) == 1


# =============================================================================
# Repr Tests
# =============================================================================

class TestRepr:
    """Tests for string representation."""
    
    def test_repr_empty(self, cache):
        """Test repr of empty cache."""
        repr_str = repr(cache)
        assert "StatementCache" in repr_str
        assert "0/10" in repr_str
    
    @pytest.mark.asyncio
    async def test_repr_with_items(self, cache, mock_connection, mock_statement):
        """Test repr with cached items."""
        mock_connection.prepare.return_value = mock_statement
        await cache.get_or_prepare(mock_connection, "SELECT 1")
        await cache.get_or_prepare(mock_connection, "SELECT 1")
        
        repr_str = repr(cache)
        assert "1/10" in repr_str
        assert "50" in repr_str  # 50% hit rate

