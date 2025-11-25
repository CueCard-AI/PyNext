"""
PyNext Incremental Static Regeneration (ISR) - Fine-Grained Invalidation.

Unlike Next.js which regenerates entire pages, PyNext ISR supports:
- Component-level invalidation (only regenerate changed parts)
- Signal/Resource-based cache keys
- Tag-based invalidation groups
- Partial page regeneration

SolidJS Principles Applied:
- Fine-grained updates (component-level, not page-level)
- Reactive cache invalidation tied to signals/resources
- Minimal work (only regenerate what changed)
"""

from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    TypeVar,
    Union,
    Awaitable,
)
import asyncio
import hashlib
import json
import time
from pathlib import Path


T = TypeVar("T")
ComponentFunc = Callable[..., Any]


class InvalidationScope(Enum):
    """Scope of cache invalidation."""
    PAGE = "page"          # Entire page (like Next.js)
    COMPONENT = "component"  # Single component
    RESOURCE = "resource"   # Tied to a Resource
    TAG = "tag"            # Tag-based group


class RevalidationTrigger(Enum):
    """What triggers revalidation."""
    TIME = "time"          # Time-based (seconds)
    ON_DEMAND = "on_demand"  # Manual trigger
    SIGNAL = "signal"      # When signal changes
    RESOURCE = "resource"  # When resource refetches


@dataclass
class RevalidateConfig:
    """Configuration for revalidation behavior."""
    # Time-based revalidation (seconds)
    seconds: Optional[int] = None
    
    # On-demand revalidation
    on_demand: bool = False
    
    # Cache tags for grouped invalidation
    tags: List[str] = field(default_factory=list)
    
    # Scope of invalidation
    scope: InvalidationScope = InvalidationScope.PAGE
    
    # Stale-while-revalidate behavior
    stale_while_revalidate: bool = True
    
    # Background regeneration
    background_regeneration: bool = True


@dataclass
class CacheEntry:
    """A single cache entry for ISR."""
    content: str
    hash: str
    created_at: float
    expires_at: Optional[float]
    tags: Set[str]
    scope: InvalidationScope
    
    # Metadata
    component_id: Optional[str] = None
    resource_id: Optional[str] = None
    
    # Regeneration state
    is_stale: bool = False
    regenerating: bool = False
    stale_while_revalidate: bool = True
    
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    def mark_stale(self) -> None:
        """Mark entry as stale (but still usable)."""
        self.is_stale = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "hash": self.hash,
            "createdAt": self.created_at,
            "expiresAt": self.expires_at,
            "tags": list(self.tags),
            "scope": self.scope.value,
            "componentId": self.component_id,
            "resourceId": self.resource_id,
            "isStale": self.is_stale,
        }


class ISRCache:
    """
    Incremental Static Regeneration cache with component-level granularity.
    
    Unlike page-level caching, this cache can store and invalidate
    individual components, enabling partial page regeneration.
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self._cache: Dict[str, CacheEntry] = {}
        self._tags: Dict[str, Set[str]] = {}  # tag -> cache keys
        self._regeneration_queue: asyncio.Queue = asyncio.Queue()
        self._cache_dir = cache_dir
        
        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get(self, key: str) -> Optional[CacheEntry]:
        """Get cache entry if valid."""
        entry = self._cache.get(key)
        
        if entry is None:
            return None
        
        if entry.is_expired():
            if entry.stale_while_revalidate:
                entry.mark_stale()
                self._queue_regeneration(key)
                return entry
            else:
                self.delete(key)
                return None
        
        return entry
    
    def set(
        self,
        key: str,
        content: str,
        config: RevalidateConfig,
        component_id: Optional[str] = None,
        resource_id: Optional[str] = None
    ) -> CacheEntry:
        """Store content in cache."""
        now = time.time()
        expires_at = None
        if config.seconds:
            expires_at = now + config.seconds
        
        entry = CacheEntry(
            content=content,
            hash=hashlib.md5(content.encode()).hexdigest()[:12],
            created_at=now,
            expires_at=expires_at,
            tags=set(config.tags),
            scope=config.scope,
            component_id=component_id,
            resource_id=resource_id,
            stale_while_revalidate=config.stale_while_revalidate,
        )
        
        self._cache[key] = entry
        
        # Update tag index
        for tag in config.tags:
            if tag not in self._tags:
                self._tags[tag] = set()
            self._tags[tag].add(key)
        
        # Persist if cache dir configured
        if self._cache_dir:
            self._persist_entry(key, entry)
        
        return entry
    
    def delete(self, key: str) -> bool:
        """Delete a cache entry."""
        entry = self._cache.pop(key, None)
        
        if entry:
            # Remove from tag index
            for tag in entry.tags:
                if tag in self._tags:
                    self._tags[tag].discard(key)
            
            # Remove persisted file
            if self._cache_dir:
                self._delete_persisted(key)
            
            return True
        
        return False
    
    def invalidate_by_tag(self, tag: str) -> int:
        """Invalidate all entries with a specific tag."""
        keys = self._tags.get(tag, set()).copy()
        count = 0
        
        for key in keys:
            if self.delete(key):
                count += 1
        
        return count
    
    def invalidate_by_path(self, path: str) -> int:
        """Invalidate all entries for a path (page-level)."""
        count = 0
        keys_to_delete = []
        
        for key in self._cache:
            if key.startswith(path):
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            if self.delete(key):
                count += 1
        
        return count
    
    def invalidate_by_component(self, component_id: str) -> int:
        """Invalidate all entries for a specific component."""
        count = 0
        keys_to_delete = []
        
        for key, entry in self._cache.items():
            if entry.component_id == component_id:
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            if self.delete(key):
                count += 1
        
        return count
    
    def invalidate_by_resource(self, resource_id: str) -> int:
        """Invalidate all entries tied to a specific resource."""
        count = 0
        keys_to_delete = []
        
        for key, entry in self._cache.items():
            if entry.resource_id == resource_id:
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            if self.delete(key):
                count += 1
        
        return count
    
    def _queue_regeneration(self, key: str) -> None:
        """Queue a key for background regeneration."""
        try:
            self._regeneration_queue.put_nowait(key)
        except asyncio.QueueFull:
            pass  # Skip if queue full
    
    def _persist_entry(self, key: str, entry: CacheEntry) -> None:
        """Persist cache entry to disk."""
        if not self._cache_dir:
            return
        
        safe_key = hashlib.md5(key.encode()).hexdigest()
        file_path = self._cache_dir / f"{safe_key}.json"
        
        data = {
            "key": key,
            "content": entry.content,
            "meta": entry.to_dict(),
        }
        
        file_path.write_text(json.dumps(data))
    
    def _delete_persisted(self, key: str) -> None:
        """Delete persisted cache entry."""
        if not self._cache_dir:
            return
        
        safe_key = hashlib.md5(key.encode()).hexdigest()
        file_path = self._cache_dir / f"{safe_key}.json"
        
        if file_path.exists():
            file_path.unlink()
    
    def load_from_disk(self) -> int:
        """Load cache entries from disk."""
        if not self._cache_dir or not self._cache_dir.exists():
            return 0
        
        count = 0
        for file_path in self._cache_dir.glob("*.json"):
            try:
                data = json.loads(file_path.read_text())
                key = data["key"]
                meta = data["meta"]
                
                entry = CacheEntry(
                    content=data["content"],
                    hash=meta["hash"],
                    created_at=meta["createdAt"],
                    expires_at=meta.get("expiresAt"),
                    tags=set(meta.get("tags", [])),
                    scope=InvalidationScope(meta.get("scope", "page")),
                    component_id=meta.get("componentId"),
                    resource_id=meta.get("resourceId"),
                    is_stale=meta.get("isStale", False),
                )
                
                self._cache[key] = entry
                
                # Rebuild tag index
                for tag in entry.tags:
                    if tag not in self._tags:
                        self._tags[tag] = set()
                    self._tags[tag].add(key)
                
                count += 1
            except (json.JSONDecodeError, KeyError):
                continue
        
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = len(self._cache)
        stale = sum(1 for e in self._cache.values() if e.is_stale)
        expired = sum(1 for e in self._cache.values() if e.is_expired())
        
        return {
            "total_entries": total,
            "stale_entries": stale,
            "expired_entries": expired,
            "tags": list(self._tags.keys()),
            "pending_regeneration": self._regeneration_queue.qsize(),
        }


# Global cache instance
_isr_cache: Optional[ISRCache] = None


def get_isr_cache() -> ISRCache:
    """Get the global ISR cache."""
    global _isr_cache
    if _isr_cache is None:
        _isr_cache = ISRCache()
    return _isr_cache


def init_isr_cache(cache_dir: Optional[Path] = None) -> ISRCache:
    """Initialize ISR cache with optional disk persistence."""
    global _isr_cache
    _isr_cache = ISRCache(cache_dir)
    if cache_dir:
        _isr_cache.load_from_disk()
    return _isr_cache


# Decorators

def revalidate(
    seconds: Optional[int] = None,
    tags: Optional[List[str]] = None,
    scope: InvalidationScope = InvalidationScope.PAGE,
    on_demand: bool = False
) -> Callable[[ComponentFunc], ComponentFunc]:
    """
    Decorator to enable ISR for a component or page.
    
    Example:
        @revalidate(seconds=60)
        def product_list():
            products = fetch_products()
            return div([product_card(p) for p in products])
        
        @revalidate(tags=["products"], scope=InvalidationScope.COMPONENT)
        def product_card(product):
            return div(h2(product.name), p(product.price))
    """
    config = RevalidateConfig(
        seconds=seconds,
        tags=tags or [],
        scope=scope,
        on_demand=on_demand,
    )
    
    def decorator(func: ComponentFunc) -> ComponentFunc:
        func._revalidate_config = config
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_isr_cache()
            
            # Generate cache key
            cache_key = _generate_cache_key(func, args, kwargs)
            
            # Check cache
            entry = cache.get(cache_key)
            if entry and not entry.is_stale:
                return entry.content
            
            # Render component
            result = func(*args, **kwargs)
            
            # Convert to string if needed
            content = result
            if hasattr(result, "render"):
                content = result.render()
            elif not isinstance(result, str):
                content = str(result)
            
            # Cache result
            cache.set(
                cache_key,
                content,
                config,
                component_id=func.__name__,
            )
            
            return result
        
        wrapper._is_isr = True
        wrapper._revalidate_config = config
        
        return wrapper
    
    return decorator


def _generate_cache_key(func: Callable, args: tuple, kwargs: dict) -> str:
    """Generate cache key from function and arguments."""
    parts = [func.__module__, func.__name__]
    
    # Add serializable args
    for arg in args:
        try:
            parts.append(json.dumps(arg, sort_keys=True, default=str))
        except (TypeError, ValueError):
            parts.append(str(id(arg)))
    
    for key, value in sorted(kwargs.items()):
        try:
            parts.append(f"{key}={json.dumps(value, sort_keys=True, default=str)}")
        except (TypeError, ValueError):
            parts.append(f"{key}={id(value)}")
    
    key_string = ":".join(parts)
    return hashlib.md5(key_string.encode()).hexdigest()


# Revalidation API functions

async def revalidate_path(path: str) -> Dict[str, Any]:
    """
    Revalidate all cached content for a path.
    
    Example:
        await revalidate_path("/products")
        await revalidate_path("/blog/post-1")
    """
    cache = get_isr_cache()
    count = cache.invalidate_by_path(path)
    
    return {
        "revalidated": True,
        "path": path,
        "invalidated_entries": count,
    }


async def revalidate_tag(tag: str) -> Dict[str, Any]:
    """
    Revalidate all content with a specific tag.
    
    Example:
        await revalidate_tag("products")
        await revalidate_tag("user-123")
    """
    cache = get_isr_cache()
    count = cache.invalidate_by_tag(tag)
    
    return {
        "revalidated": True,
        "tag": tag,
        "invalidated_entries": count,
    }


async def revalidate_component(component_id: str) -> Dict[str, Any]:
    """
    Revalidate all cached instances of a component.
    
    Example:
        await revalidate_component("ProductCard")
    """
    cache = get_isr_cache()
    count = cache.invalidate_by_component(component_id)
    
    return {
        "revalidated": True,
        "component": component_id,
        "invalidated_entries": count,
    }


# Background regeneration worker

class RegenerationWorker:
    """
    Background worker for stale-while-revalidate regeneration.
    
    Processes the regeneration queue in the background,
    updating stale entries without blocking requests.
    """
    
    def __init__(self, cache: ISRCache):
        self.cache = cache
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._regenerators: Dict[str, Callable] = {}
    
    def register_regenerator(self, key: str, func: Callable) -> None:
        """Register a function to regenerate a cache key."""
        self._regenerators[key] = func
    
    async def start(self) -> None:
        """Start the background worker."""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._run())
    
    async def stop(self) -> None:
        """Stop the background worker."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
    
    async def _run(self) -> None:
        """Main worker loop."""
        while self._running:
            try:
                key = await asyncio.wait_for(
                    self.cache._regeneration_queue.get(),
                    timeout=1.0
                )
                
                await self._regenerate(key)
                
            except asyncio.TimeoutError:
                continue
            except Exception:
                continue
    
    async def _regenerate(self, key: str) -> None:
        """Regenerate a single cache entry."""
        entry = self.cache._cache.get(key)
        if not entry:
            return
        
        # Mark as regenerating
        entry.regenerating = True
        
        try:
            # Find regenerator function
            regenerator = self._regenerators.get(key)
            if regenerator:
                if asyncio.iscoroutinefunction(regenerator):
                    new_content = await regenerator()
                else:
                    new_content = regenerator()
                
                # Update cache entry
                entry.content = new_content
                entry.hash = hashlib.md5(new_content.encode()).hexdigest()[:12]
                entry.created_at = time.time()
                entry.is_stale = False
                
                if entry.expires_at and entry.scope == InvalidationScope.PAGE:
                    config = RevalidateConfig(seconds=60)  # Default 60s
                    entry.expires_at = time.time() + 60
        finally:
            entry.regenerating = False

