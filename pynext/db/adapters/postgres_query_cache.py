"""
PostgreSQL Read-Through Query Cache.

This module provides intelligent caching for database queries with
TTL-based and smart invalidation strategies.

Why Query Caching?

Database queries are often:
1. Repeated frequently (same user profile, same product)
2. Expensive to execute (complex JOINs, aggregations)
3. Reading data that changes slowly

Without caching:
- Every request hits the database
- Identical queries execute repeatedly
- Response times are bound by DB latency

With caching:
- Hot data served from memory (sub-millisecond)
- Database load reduced dramatically
- Response times improve 10-100x

Invalidation Strategies:

1. TTL-based (simple): Cache expires after N seconds
2. Smart (tag-based): Invalidate by table or custom tags
3. Pattern-based: Invalidate by query pattern

AI-Friendly Design:
- Clear cache entries with metadata
- Observable hit/miss rates
- Multiple invalidation strategies
- Simple configuration with smart defaults
"""

from __future__ import annotations

import asyncio
import fnmatch
import hashlib
import logging
import re
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Generic, List, Optional, Set, Tuple, TypeVar, Union

logger = logging.getLogger("pynext.db.postgres.cache")

T = TypeVar("T")


class InvalidationStrategy(Enum):
    """Cache invalidation strategies.
    
    TTL: Time-based expiration only
    SMART: Tag-based invalidation with TTL fallback
    MANUAL: No automatic invalidation, only explicit
    """
    TTL = "ttl"
    SMART = "smart"
    MANUAL = "manual"


@dataclass
class QueryCacheConfig:
    """Configuration for query caching.
    
    Attributes:
        enabled: Whether caching is enabled. Default: True
        max_size: Maximum cache entries. Default: 10000
        default_ttl: Default TTL in seconds. Default: 60.0
        invalidation: Invalidation strategy. Default: "ttl"
        cache_reads: Cache SELECT queries. Default: True
        cache_writes: Cache INSERT/UPDATE results. Default: False
        auto_tag: Auto-extract tags from queries. Default: True
        stats_enabled: Track cache statistics. Default: True
    
    Example:
        # Simple TTL cache
        config = QueryCacheConfig(default_ttl=300.0)
        
        # Smart invalidation
        config = QueryCacheConfig(
            invalidation="smart",
            auto_tag=True,
        )
        
        # Large cache for heavy reads
        config = QueryCacheConfig(
            max_size=100000,
            default_ttl=600.0,
        )
    """
    enabled: bool = True
    max_size: int = 10000
    default_ttl: float = 60.0
    invalidation: str = "ttl"
    cache_reads: bool = True
    cache_writes: bool = False
    auto_tag: bool = True
    stats_enabled: bool = True
    
    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.max_size < 0:
            raise ValueError(f"max_size must be >= 0, got {self.max_size}")
        if self.default_ttl < 0:
            raise ValueError(f"default_ttl must be >= 0, got {self.default_ttl}")
        if self.invalidation not in ("ttl", "smart", "manual"):
            raise ValueError(f"invalidation must be ttl/smart/manual, got {self.invalidation}")


@dataclass
class CacheEntry:
    """A cached query result.
    
    Attributes:
        key: Cache key (hash of query + params)
        query: Original SQL query
        params: Query parameters
        result: Cached result data
        created_at: When entry was created
        expires_at: When entry expires
        tags: Tags for smart invalidation
        hit_count: Number of cache hits
    """
    key: str
    query: str
    params: Optional[tuple] = None
    result: Any = None
    created_at: float = field(default_factory=time.monotonic)
    expires_at: float = 0.0
    tags: Set[str] = field(default_factory=set)
    hit_count: int = 0
    
    @property
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        if self.expires_at == 0:
            return False  # Never expires
        return time.monotonic() > self.expires_at
    
    @property
    def age_seconds(self) -> float:
        """Time since entry was created."""
        return time.monotonic() - self.created_at
    
    @property
    def ttl_remaining(self) -> float:
        """Seconds until expiration (0 if expired)."""
        if self.expires_at == 0:
            return float("inf")
        remaining = self.expires_at - time.monotonic()
        return max(0, remaining)
    
    def touch(self) -> None:
        """Record a cache hit."""
        self.hit_count += 1


@dataclass
class CacheStats:
    """Statistics about cache performance.
    
    Attributes:
        hits: Total cache hits
        misses: Total cache misses
        evictions: Entries evicted due to size limit
        expirations: Entries expired by TTL
        invalidations: Entries invalidated manually
        current_size: Current number of entries
        max_size: Maximum allowed entries
    """
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    expirations: int = 0
    invalidations: int = 0
    current_size: int = 0
    max_size: int = 0
    total_hit_latency_ms: float = 0
    total_miss_latency_ms: float = 0
    
    @property
    def total_requests(self) -> int:
        """Total cache requests."""
        return self.hits + self.misses
    
    @property
    def hit_rate(self) -> float:
        """Cache hit rate (0-1)."""
        if self.total_requests == 0:
            return 0.0
        return self.hits / self.total_requests
    
    @property
    def miss_rate(self) -> float:
        """Cache miss rate (0-1)."""
        return 1.0 - self.hit_rate
    
    @property
    def avg_hit_latency_ms(self) -> float:
        """Average latency for cache hits."""
        if self.hits == 0:
            return 0.0
        return self.total_hit_latency_ms / self.hits
    
    @property
    def avg_miss_latency_ms(self) -> float:
        """Average latency for cache misses."""
        if self.misses == 0:
            return 0.0
        return self.total_miss_latency_ms / self.misses
    
    @property
    def fill_ratio(self) -> float:
        """How full the cache is (0-1)."""
        if self.max_size == 0:
            return 0.0
        return self.current_size / self.max_size
    
    def record_hit(self, latency_ms: float = 0) -> None:
        """Record a cache hit."""
        self.hits += 1
        self.total_hit_latency_ms += latency_ms
    
    def record_miss(self, latency_ms: float = 0) -> None:
        """Record a cache miss."""
        self.misses += 1
        self.total_miss_latency_ms += latency_ms
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/metrics."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.hit_rate,
            "evictions": self.evictions,
            "expirations": self.expirations,
            "invalidations": self.invalidations,
            "current_size": self.current_size,
            "max_size": self.max_size,
            "fill_ratio": self.fill_ratio,
            "avg_hit_latency_ms": self.avg_hit_latency_ms,
            "avg_miss_latency_ms": self.avg_miss_latency_ms,
        }


class QueryCache:
    """Read-through cache for database queries.
    
    This cache stores query results and returns cached data on subsequent
    identical queries. It supports:
    
    1. **TTL-based expiration**: Entries expire after a configurable time
    2. **Smart invalidation**: Tag-based invalidation by table or custom tags
    3. **LRU eviction**: Oldest entries evicted when cache is full
    4. **Observable metrics**: Track hit rate, latency, size
    
    Basic Usage:
        cache = QueryCache(QueryCacheConfig(default_ttl=60.0))
        
        # Get or execute
        result = await cache.get_or_execute(
            "SELECT * FROM users WHERE id = $1",
            params=(1,),
            executor=lambda q, p: conn.fetch(q, *p),
        )
    
    With Smart Invalidation:
        cache = QueryCache(QueryCacheConfig(invalidation="smart"))
        
        # Cache a query with tags
        result = await cache.get_or_execute(
            "SELECT * FROM users WHERE id = $1",
            params=(1,),
            executor=executor,
            tags={"users", "user:1"},
        )
        
        # Invalidate by tag
        cache.invalidate_tags(["users"])  # All user queries
        cache.invalidate_tags(["user:1"])  # Just user 1
    
    With Pattern Invalidation:
        # Invalidate all queries matching pattern
        cache.invalidate_pattern("*users*")
    """
    
    # Pattern for extracting table names
    _TABLE_PATTERN = re.compile(
        r"(?:FROM|INTO|UPDATE|JOIN|TABLE)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
        re.IGNORECASE,
    )
    
    def __init__(self, config: Optional[QueryCacheConfig] = None):
        """Initialize the query cache.
        
        Args:
            config: Cache configuration (default: QueryCacheConfig())
        """
        self._config = config or QueryCacheConfig()
        
        # LRU cache storage (OrderedDict maintains insertion order)
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        
        # Tag index for smart invalidation
        self._tag_index: Dict[str, Set[str]] = {}  # tag -> set of cache keys
        
        # Statistics
        self._stats = CacheStats(max_size=self._config.max_size)
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
    
    @property
    def config(self) -> QueryCacheConfig:
        """Get current configuration."""
        return self._config
    
    @property
    def size(self) -> int:
        """Current number of cached entries."""
        return len(self._cache)
    
    @property
    def stats(self) -> CacheStats:
        """Get cache statistics."""
        self._stats.current_size = self.size
        return self._stats
    
    def _make_key(self, query: str, params: Optional[tuple] = None) -> str:
        """Create a cache key from query and parameters.
        
        Args:
            query: SQL query string
            params: Query parameters
        
        Returns:
            Hash-based cache key
        """
        # Normalize query (strip whitespace, lowercase)
        normalized = " ".join(query.split()).lower()
        
        # Include params in key
        key_data = normalized
        if params:
            key_data += str(params)
        
        # Create hash
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _extract_tags(self, query: str) -> Set[str]:
        """Auto-extract tags from query.
        
        Extracts table names to use as tags for smart invalidation.
        
        Args:
            query: SQL query string
        
        Returns:
            Set of extracted tags
        """
        tags = set()
        
        for match in self._TABLE_PATTERN.finditer(query):
            table = match.group(1).lower()
            tags.add(f"table:{table}")
        
        return tags
    
    async def get(
        self,
        query: str,
        params: Optional[tuple] = None,
    ) -> Optional[Any]:
        """Get a cached result if available.
        
        Args:
            query: SQL query string
            params: Query parameters
        
        Returns:
            Cached result or None if not found/expired
        """
        if not self._config.enabled:
            return None
        
        key = self._make_key(query, params)
        
        async with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                return None
            
            if entry.is_expired:
                self._remove_entry(key)
                self._stats.expirations += 1
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            entry.touch()
            
            return entry.result
    
    async def set(
        self,
        query: str,
        params: Optional[tuple],
        result: Any,
        ttl: Optional[float] = None,
        tags: Optional[Set[str]] = None,
    ) -> None:
        """Set a cache entry.
        
        Args:
            query: SQL query string
            params: Query parameters
            result: Result to cache
            ttl: Time-to-live in seconds (default: config.default_ttl)
            tags: Tags for smart invalidation
        """
        if not self._config.enabled:
            return
        
        key = self._make_key(query, params)
        ttl = ttl if ttl is not None else self._config.default_ttl
        
        # Build tags
        entry_tags = tags or set()
        if self._config.auto_tag:
            entry_tags = entry_tags.union(self._extract_tags(query))
        
        # Create entry
        entry = CacheEntry(
            key=key,
            query=query,
            params=params,
            result=result,
            created_at=time.monotonic(),
            expires_at=time.monotonic() + ttl if ttl > 0 else 0,
            tags=entry_tags,
        )
        
        async with self._lock:
            # Evict if at capacity
            while len(self._cache) >= self._config.max_size:
                self._evict_oldest()
            
            # Add entry
            self._cache[key] = entry
            
            # Update tag index
            for tag in entry_tags:
                if tag not in self._tag_index:
                    self._tag_index[tag] = set()
                self._tag_index[tag].add(key)
    
    async def get_or_execute(
        self,
        query: str,
        params: Optional[tuple] = None,
        executor: Optional[Callable] = None,
        ttl: Optional[float] = None,
        tags: Optional[Set[str]] = None,
        bypass: bool = False,
    ) -> Any:
        """Get cached result or execute query.
        
        This is the main API for read-through caching.
        
        Args:
            query: SQL query string
            params: Query parameters
            executor: Async function to execute query if not cached
            ttl: Time-to-live for cache entry
            tags: Tags for smart invalidation
            bypass: Skip cache lookup (force execute)
        
        Returns:
            Query result (cached or fresh)
        
        Example:
            result = await cache.get_or_execute(
                "SELECT * FROM users WHERE id = $1",
                params=(user_id,),
                executor=lambda q, p: conn.fetch(q, *p),
                ttl=300.0,
                tags={"users", f"user:{user_id}"},
            )
        """
        start_time = time.monotonic()
        
        # Try cache first (unless bypass)
        if not bypass:
            cached = await self.get(query, params)
            if cached is not None:
                latency_ms = (time.monotonic() - start_time) * 1000
                self._stats.record_hit(latency_ms)
                logger.debug(f"Cache hit: {query[:50]}...")
                return cached
        
        # Execute query
        if executor is None:
            raise ValueError("executor required when cache miss")
        
        if asyncio.iscoroutinefunction(executor):
            if params:
                result = await executor(query, params)
            else:
                result = await executor(query)
        else:
            if params:
                result = executor(query, params)
            else:
                result = executor(query)
        
        # Cache result
        await self.set(query, params, result, ttl=ttl, tags=tags)
        
        latency_ms = (time.monotonic() - start_time) * 1000
        self._stats.record_miss(latency_ms)
        logger.debug(f"Cache miss: {query[:50]}...")
        
        return result
    
    def invalidate(self, query: str, params: Optional[tuple] = None) -> bool:
        """Invalidate a specific cache entry.
        
        Args:
            query: SQL query string
            params: Query parameters
        
        Returns:
            True if entry was invalidated, False if not found
        """
        key = self._make_key(query, params)
        
        if key in self._cache:
            self._remove_entry(key)
            self._stats.invalidations += 1
            return True
        
        return False
    
    def invalidate_tags(self, tags: List[str]) -> int:
        """Invalidate all entries with any of the given tags.
        
        Args:
            tags: List of tags to invalidate
        
        Returns:
            Number of entries invalidated
        
        Example:
            # Invalidate all user-related cache
            cache.invalidate_tags(["table:users"])
            
            # Invalidate specific user
            cache.invalidate_tags(["user:123"])
        """
        count = 0
        keys_to_remove = set()
        
        for tag in tags:
            if tag in self._tag_index:
                keys_to_remove.update(self._tag_index[tag])
        
        for key in keys_to_remove:
            if key in self._cache:
                self._remove_entry(key)
                count += 1
        
        self._stats.invalidations += count
        logger.debug(f"Invalidated {count} entries by tags: {tags}")
        
        return count
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate entries matching a query pattern.
        
        Args:
            pattern: Glob pattern to match against queries
        
        Returns:
            Number of entries invalidated
        
        Example:
            # Invalidate all user queries
            cache.invalidate_pattern("*FROM users*")
        """
        count = 0
        keys_to_remove = []
        
        for key, entry in self._cache.items():
            if fnmatch.fnmatch(entry.query.lower(), pattern.lower()):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            self._remove_entry(key)
            count += 1
        
        self._stats.invalidations += count
        logger.debug(f"Invalidated {count} entries by pattern: {pattern}")
        
        return count
    
    def invalidate_all(self) -> int:
        """Invalidate all cache entries.
        
        Returns:
            Number of entries invalidated
        """
        count = len(self._cache)
        self._cache.clear()
        self._tag_index.clear()
        self._stats.invalidations += count
        logger.info(f"Invalidated all {count} cache entries")
        return count
    
    def cleanup_expired(self) -> int:
        """Remove all expired entries.
        
        Returns:
            Number of entries removed
        """
        count = 0
        keys_to_remove = []
        
        for key, entry in self._cache.items():
            if entry.is_expired:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            self._remove_entry(key)
            count += 1
        
        self._stats.expirations += count
        return count
    
    def _remove_entry(self, key: str) -> None:
        """Remove an entry and update tag index."""
        if key not in self._cache:
            return
        
        entry = self._cache[key]
        
        # Remove from tag index
        for tag in entry.tags:
            if tag in self._tag_index:
                self._tag_index[tag].discard(key)
                if not self._tag_index[tag]:
                    del self._tag_index[tag]
        
        # Remove from cache
        del self._cache[key]
    
    def _evict_oldest(self) -> None:
        """Evict the oldest (least recently used) entry."""
        if not self._cache:
            return
        
        # OrderedDict maintains insertion order, first item is oldest
        key = next(iter(self._cache))
        self._remove_entry(key)
        self._stats.evictions += 1
    
    def get_stats(self) -> CacheStats:
        """Get current cache statistics."""
        self._stats.current_size = self.size
        return self._stats
    
    def reset_stats(self) -> None:
        """Reset cache statistics."""
        self._stats = CacheStats(max_size=self._config.max_size)
        self._stats.current_size = self.size
    
    def warm(self, entries: List[Tuple[str, Optional[tuple], Any, Optional[float]]]) -> int:
        """Warm the cache with pre-computed entries.
        
        Args:
            entries: List of (query, params, result, ttl) tuples
        
        Returns:
            Number of entries added
        
        Example:
            cache.warm([
                ("SELECT * FROM config", None, config_data, 3600.0),
                ("SELECT * FROM categories", None, categories, 600.0),
            ])
        """
        count = 0
        
        for entry in entries:
            query, params, result, ttl = entry
            key = self._make_key(query, params)
            
            if key not in self._cache:
                # Use asyncio.run to call async method from sync context
                # In practice, use async version
                cache_entry = CacheEntry(
                    key=key,
                    query=query,
                    params=params,
                    result=result,
                    created_at=time.monotonic(),
                    expires_at=time.monotonic() + (ttl or self._config.default_ttl),
                    tags=self._extract_tags(query) if self._config.auto_tag else set(),
                )
                self._cache[key] = cache_entry
                count += 1
        
        logger.info(f"Warmed cache with {count} entries")
        return count
    
    def __repr__(self) -> str:
        return (
            f"QueryCache(size={self.size}/{self._config.max_size}, "
            f"hit_rate={self._stats.hit_rate:.1%}, "
            f"strategy={self._config.invalidation})"
        )


# =============================================================================
# Convenience Functions
# =============================================================================

def simple_cache_config(ttl: float = 60.0) -> QueryCacheConfig:
    """Create a simple TTL-based cache configuration.
    
    Args:
        ttl: Time-to-live in seconds
    
    Returns:
        QueryCacheConfig with TTL invalidation
    """
    return QueryCacheConfig(
        default_ttl=ttl,
        invalidation="ttl",
    )


def smart_cache_config(ttl: float = 300.0) -> QueryCacheConfig:
    """Create a smart cache configuration with tag-based invalidation.
    
    Args:
        ttl: Default TTL in seconds
    
    Returns:
        QueryCacheConfig with smart invalidation
    """
    return QueryCacheConfig(
        default_ttl=ttl,
        invalidation="smart",
        auto_tag=True,
    )


def aggressive_cache_config() -> QueryCacheConfig:
    """Create an aggressive cache configuration for read-heavy workloads.
    
    - Large cache size (100k entries)
    - Long TTL (10 minutes)
    - Smart invalidation
    
    Returns:
        QueryCacheConfig for aggressive caching
    """
    return QueryCacheConfig(
        max_size=100000,
        default_ttl=600.0,
        invalidation="smart",
        auto_tag=True,
    )


def no_cache_config() -> QueryCacheConfig:
    """Create a disabled cache configuration.
    
    Returns:
        QueryCacheConfig with caching disabled
    """
    return QueryCacheConfig(enabled=False)

