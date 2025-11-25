"""
PyNext Cache Module.

Provides caching primitives for:
- ISR (Incremental Static Regeneration)
- Component-level caching
- Resource caching
"""

from pynext.core.isr import (
    ISRCache,
    CacheEntry,
    RevalidateConfig,
    InvalidationScope,
    RevalidationTrigger,
    get_isr_cache,
    init_isr_cache,
    revalidate,
    revalidate_path,
    revalidate_tag,
    revalidate_component,
    RegenerationWorker,
)

__all__ = [
    "ISRCache",
    "CacheEntry",
    "RevalidateConfig",
    "InvalidationScope",
    "RevalidationTrigger",
    "get_isr_cache",
    "init_isr_cache",
    "revalidate",
    "revalidate_path",
    "revalidate_tag",
    "revalidate_component",
    "RegenerationWorker",
]

