"""
PostgreSQL Core Adapter Components.

This module contains the essential components for PostgreSQL connectivity:
- adapter.py: Main PostgresAdapter class
- url.py: Connection URL parsing and configuration
- types.py: Python <-> PostgreSQL type conversion
- cache.py: Statement caching for performance
"""

from .adapter import PostgresAdapter
from .url import PostgresConfig, PostgresConfigError
from .types import python_to_postgres, postgres_to_python, get_postgres_type, TypeConversionError, TypeMapping
from .cache import StatementCache, PerConnectionCache, CachedStatement

__all__ = [
    # Adapter
    "PostgresAdapter",
    # URL/Config
    "PostgresConfig",
    "PostgresConfigError",
    # Types
    "python_to_postgres",
    "postgres_to_python",
    "get_postgres_type",
    "TypeConversionError",
    "TypeMapping",
    # Cache
    "StatementCache",
    "PerConnectionCache",
    "CachedStatement",
]

