"""
PyNext Runtime - functools Module (Python implementation)

This module provides Python functools functionality.
The JavaScript equivalent is in functools.js.

For testing, this re-exports Python's standard functools module
to ensure tests validate expected behavior.
"""

# Re-export from Python's standard functools module
from functools import (
    partial,
    reduce,
    lru_cache,
    wraps,
    update_wrapper,
    cmp_to_key,
    total_ordering,
    singledispatch,
    cached_property,
)

# cache was added in Python 3.9
try:
    from functools import cache
except ImportError:
    # Fallback: cache is just lru_cache with maxsize=None
    cache = lru_cache(maxsize=None)

__all__ = [
    'partial',
    'reduce',
    'lru_cache',
    'cache',
    'wraps',
    'update_wrapper',
    'cmp_to_key',
    'total_ordering',
    'singledispatch',
    'cached_property',
]
