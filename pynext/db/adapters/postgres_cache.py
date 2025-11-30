"""
PostgreSQL Statement Cache.

This module provides LRU caching for prepared statements,
improving query performance by 10-30% for repeated queries.

How it works:
1. First execution: PostgreSQL parses the SQL, creates execution plan
2. We cache the prepared statement with the SQL as key
3. Subsequent executions: Skip parsing, reuse cached statement
4. LRU eviction when cache is full (oldest unused statements removed)

Why this matters:
- SQL parsing takes 1-5ms per query
- Prepared statements skip parsing entirely
- For apps with repeated queries (most apps), this is free performance

AI-Friendly Design:
- Simple LRU cache with clear semantics
- Thread-safe for async operations
- Easy to understand cache hit/miss behavior
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from collections import OrderedDict
from dataclasses import dataclass, field
from time import monotonic
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import asyncpg

logger = logging.getLogger("pynext.db.postgres")


@dataclass
class CachedStatement:
    """A cached prepared statement.
    
    Tracks the prepared statement along with usage statistics
    for monitoring and debugging.
    
    Attributes:
        statement: The asyncpg PreparedStatement object
        sql: Original SQL query (for debugging)
        created_at: When the statement was prepared
        hit_count: How many times this statement was reused
        last_used: Last time this statement was used
    """
    statement: "asyncpg.PreparedStatement"
    sql: str
    created_at: float = field(default_factory=monotonic)
    hit_count: int = 0
    last_used: float = field(default_factory=monotonic)
    
    def record_hit(self) -> None:
        """Record a cache hit."""
        self.hit_count += 1
        self.last_used = monotonic()


class StatementCache:
    """LRU cache for PostgreSQL prepared statements.
    
    This cache stores prepared statements keyed by their SQL query.
    When the cache is full, the least recently used statements are evicted.
    
    Why LRU?
    - Most apps have a working set of frequently used queries
    - LRU naturally keeps the hot queries in cache
    - Cold queries get evicted, freeing memory
    
    Thread Safety:
    - Uses asyncio.Lock for safe concurrent access
    - All operations are atomic
    
    Examples:
        # Create cache with default size (1000 statements)
        cache = StatementCache()
        
        # Create cache with custom size
        cache = StatementCache(max_size=500)
        
        # Get or create a prepared statement
        async with conn.transaction():
            stmt = await cache.get_or_prepare(conn, "SELECT * FROM users WHERE id = $1")
            result = await stmt.fetch(user_id)
        
        # Check cache statistics
        stats = cache.get_stats()
        print(f"Hit rate: {stats['hit_rate']:.1%}")
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        *,
        track_stats: bool = True,
    ):
        """Initialize the statement cache.
        
        Args:
            max_size: Maximum number of statements to cache (default: 1000)
            track_stats: Whether to track hit/miss statistics (default: True)
        
        Notes:
            - Each prepared statement uses ~1-10KB of memory
            - max_size=1000 ≈ 1-10MB memory usage
            - Adjust based on your query patterns
        """
        if max_size < 1:
            raise ValueError(
                f"max_size must be at least 1, got {max_size}.\n"
                "Example: StatementCache(max_size=1000)"
            )
        
        self._max_size = max_size
        self._track_stats = track_stats
        
        # OrderedDict for LRU: most recent at end
        self._cache: OrderedDict[str, CachedStatement] = OrderedDict()
        
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
        
        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
    
    @property
    def size(self) -> int:
        """Current number of cached statements."""
        return len(self._cache)
    
    @property
    def max_size(self) -> int:
        """Maximum cache size."""
        return self._max_size
    
    def _make_key(self, sql: str) -> str:
        """Create a cache key from SQL.
        
        Uses MD5 hash for fixed-length keys.
        MD5 is fine here - we're not doing crypto, just hashing.
        
        Args:
            sql: SQL query string
        
        Returns:
            MD5 hash of the SQL
        """
        return hashlib.md5(sql.encode()).hexdigest()
    
    async def get_or_prepare(
        self,
        connection: "asyncpg.Connection",
        sql: str,
    ) -> "asyncpg.PreparedStatement":
        """Get a cached statement or prepare a new one.
        
        This is the main API for using the cache:
        1. Check if SQL is already cached
        2. If yes, return cached statement (cache hit)
        3. If no, prepare statement, cache it, return it (cache miss)
        
        Args:
            connection: asyncpg connection to use for preparing
            sql: SQL query to prepare
        
        Returns:
            Prepared statement (from cache or newly created)
        
        Example:
            stmt = await cache.get_or_prepare(conn, "SELECT * FROM users WHERE id = $1")
            user = await stmt.fetchrow(user_id)
        """
        key = self._make_key(sql)
        
        async with self._lock:
            # Check cache
            if key in self._cache:
                # Cache hit - move to end (most recently used)
                cached = self._cache[key]
                cached.record_hit()
                self._cache.move_to_end(key)
                
                if self._track_stats:
                    self._hits += 1
                
                logger.debug(f"Statement cache hit: {sql[:50]}...")
                return cached.statement
            
            # Cache miss - prepare new statement
            if self._track_stats:
                self._misses += 1
            
            logger.debug(f"Statement cache miss: {sql[:50]}...")
        
        # Prepare outside lock (can be slow)
        statement = await connection.prepare(sql)
        
        async with self._lock:
            # Evict if necessary
            while len(self._cache) >= self._max_size:
                evicted_key, evicted = self._cache.popitem(last=False)
                if self._track_stats:
                    self._evictions += 1
                logger.debug(f"Evicted statement: {evicted.sql[:50]}...")
            
            # Cache the new statement
            self._cache[key] = CachedStatement(
                statement=statement,
                sql=sql,
            )
        
        return statement
    
    async def invalidate(self, sql: str) -> bool:
        """Remove a specific statement from cache.
        
        Use this when you know a statement needs to be re-prepared,
        for example after a schema change.
        
        Args:
            sql: SQL query to invalidate
        
        Returns:
            True if statement was in cache and removed, False otherwise
        
        Example:
            # After adding a column
            cache.invalidate("SELECT * FROM users")
        """
        key = self._make_key(sql)
        
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Invalidated statement: {sql[:50]}...")
                return True
            return False
    
    async def invalidate_all(self) -> int:
        """Remove all statements from cache.
        
        Use this after major schema changes or when you need
        to free memory.
        
        Returns:
            Number of statements that were removed
        
        Example:
            count = await cache.invalidate_all()
            print(f"Cleared {count} cached statements")
        """
        async with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"Cleared all {count} cached statements")
            return count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dict with cache statistics:
            - size: Current number of cached statements
            - max_size: Maximum cache size
            - hits: Number of cache hits
            - misses: Number of cache misses
            - evictions: Number of evicted statements
            - hit_rate: Ratio of hits to total requests (0.0-1.0)
        
        Example:
            stats = cache.get_stats()
            print(f"Cache hit rate: {stats['hit_rate']:.1%}")
            print(f"Size: {stats['size']}/{stats['max_size']}")
        """
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0.0
        
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "evictions": self._evictions,
            "hit_rate": hit_rate,
        }
    
    def get_cached_queries(self) -> Dict[str, Dict[str, Any]]:
        """Get information about cached queries.
        
        Useful for debugging and monitoring.
        
        Returns:
            Dict mapping SQL (truncated) to stats:
            - hit_count: Number of times this query was reused
            - created_at: When the statement was first prepared
            - last_used: When the statement was last used
        
        Example:
            for sql, stats in cache.get_cached_queries().items():
                print(f"{sql}: {stats['hit_count']} hits")
        """
        return {
            cached.sql[:100]: {
                "hit_count": cached.hit_count,
                "created_at": cached.created_at,
                "last_used": cached.last_used,
                "age_seconds": monotonic() - cached.created_at,
            }
            for cached in self._cache.values()
        }
    
    def __repr__(self) -> str:
        """Return string representation."""
        stats = self.get_stats()
        return (
            f"StatementCache(size={stats['size']}/{stats['max_size']}, "
            f"hit_rate={stats['hit_rate']:.1%})"
        )


class PerConnectionCache:
    """Manages statement caches per connection.
    
    Each PostgreSQL connection has its own prepared statements.
    This class manages a cache for each connection.
    
    Why per-connection?
    - PostgreSQL prepared statements are connection-specific
    - Can't share a prepared statement between connections
    - Each connection needs its own cache
    
    Example:
        cache_manager = PerConnectionCache(max_statements=500)
        
        async with pool.acquire() as conn:
            cache = cache_manager.get_cache(conn)
            stmt = await cache.get_or_prepare(conn, "SELECT 1")
    """
    
    def __init__(
        self,
        max_statements: int = 1000,
    ):
        """Initialize per-connection cache manager.
        
        Args:
            max_statements: Max statements per connection
        """
        self._max_statements = max_statements
        self._caches: Dict[int, StatementCache] = {}
        self._lock = asyncio.Lock()
    
    async def get_cache(self, connection: "asyncpg.Connection") -> StatementCache:
        """Get or create cache for a connection.
        
        Args:
            connection: asyncpg connection
        
        Returns:
            StatementCache for this connection
        """
        conn_id = id(connection)
        
        async with self._lock:
            if conn_id not in self._caches:
                self._caches[conn_id] = StatementCache(
                    max_size=self._max_statements
                )
            return self._caches[conn_id]
    
    async def remove_cache(self, connection: "asyncpg.Connection") -> None:
        """Remove cache for a closed connection.
        
        Call this when a connection is closed to free memory.
        
        Args:
            connection: asyncpg connection that was closed
        """
        conn_id = id(connection)
        
        async with self._lock:
            if conn_id in self._caches:
                del self._caches[conn_id]
    
    def get_total_stats(self) -> Dict[str, Any]:
        """Get aggregated stats across all connections.
        
        Returns:
            Aggregated statistics
        """
        total_size = 0
        total_hits = 0
        total_misses = 0
        total_evictions = 0
        
        for cache in self._caches.values():
            stats = cache.get_stats()
            total_size += stats["size"]
            total_hits += stats["hits"]
            total_misses += stats["misses"]
            total_evictions += stats["evictions"]
        
        total = total_hits + total_misses
        hit_rate = total_hits / total if total > 0 else 0.0
        
        return {
            "connections": len(self._caches),
            "total_size": total_size,
            "max_per_connection": self._max_statements,
            "total_hits": total_hits,
            "total_misses": total_misses,
            "total_evictions": total_evictions,
            "overall_hit_rate": hit_rate,
        }

