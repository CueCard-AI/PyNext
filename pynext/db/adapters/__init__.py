"""
PyNext Database Adapters.

Adapters provide a consistent interface to different database backends.

Available Adapters:
- MockAdapter: Pure Python dict storage (for testing)
- MemoryAdapter: SQLite in-memory (for development)
- PostgresAdapter: PostgreSQL with asyncpg (for production)

Usage:
    # Simple (testing)
    from pynext.db import MockAdapter
    adapter = MockAdapter()
    
    # Development
    from pynext.db import MemoryAdapter
    adapter = MemoryAdapter()
    
    # Production (PostgreSQL)
    from pynext.db import PostgresAdapter
    adapter = PostgresAdapter("postgresql://user:pass@localhost/mydb")
"""

from pynext.db.adapters.base import Adapter
from pynext.db.adapters.memory import MemoryAdapter
from pynext.db.adapters.mock import MockAdapter

# PostgreSQL adapter (optional - requires asyncpg)
try:
    from pynext.db.adapters.postgres import PostgresAdapter
    from pynext.db.adapters.postgres_url import PostgresConfig, PostgresConfigError
    from pynext.db.adapters.postgres_pool import AutoScalingPool, PoolStats
    from pynext.db.adapters.postgres_cache import StatementCache
    _HAS_POSTGRES = True
except ImportError:
    _HAS_POSTGRES = False
    PostgresAdapter = None  # type: ignore
    PostgresConfig = None  # type: ignore
    PostgresConfigError = None  # type: ignore
    AutoScalingPool = None  # type: ignore
    PoolStats = None  # type: ignore
    StatementCache = None  # type: ignore

__all__ = [
    "Adapter",
    "MemoryAdapter", 
    "MockAdapter",
    # PostgreSQL (optional)
    "PostgresAdapter",
    "PostgresConfig",
    "PostgresConfigError",
    "AutoScalingPool",
    "PoolStats",
    "StatementCache",
]

