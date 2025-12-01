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
    
    # Production with Phase 5.2 Features
    from pynext.db.adapters import (
        PostgresAdapter,
        QueueConfig,
        LifecycleConfig,
        WarmupConfig,
        ExternalPoolerConfig,
        PoolerType,
        PoolerMode,
    )
    
    adapter = PostgresAdapter(
        "postgresql://...",
        queue_config=QueueConfig(max_size=1000),
        lifecycle_config=LifecycleConfig(soft_lifetime=1800),
        warmup_config=WarmupConfig(enabled=True),
        external_pooler=ExternalPoolerConfig(
            enabled=True,
            type=PoolerType.PGBOUNCER,
            mode=PoolerMode.TRANSACTION,
        ),
    )
"""

from pynext.db.adapters.base import Adapter
from pynext.db.adapters.memory import MemoryAdapter
from pynext.db.adapters.mock import MockAdapter

# PostgreSQL adapter (optional - requires asyncpg)
try:
    from pynext.db.adapters.postgres import PostgresAdapter
    from pynext.db.adapters.postgres_url import PostgresConfig, PostgresConfigError
    from pynext.db.adapters.postgres_pool import (
        AutoScalingPool,
        PoolStats,
        PoolState,
        PooledConnection,
        ConnectionState,
        PoolExhaustedError,
        PoolClosedError,
    )
    from pynext.db.adapters.postgres_cache import StatementCache, PerConnectionCache
    
    # Phase 5.2: Queue management
    from pynext.db.adapters.postgres_queue import (
        ConnectionQueue,
        QueueConfig,
        QueueStats,
        QueuedRequest,
        QueuePriority,
        QueueOverflowAction,
        QueueFullError,
        QueueTimeoutError,
    )
    
    # Phase 5.2: Lifecycle management
    from pynext.db.adapters.postgres_lifecycle import (
        LifecycleManager,
        LifecycleConfig,
        LifecycleStats,
        ConnectionLifecycle,
        ConnectionHealth,
        RetirementReason,
        ReplacementStrategy,
    )
    
    # Phase 5.2: Connection warmup
    from pynext.db.adapters.postgres_warmup import (
        ConnectionWarmer,
        WarmupConfig,
        WarmupResult,
        WarmupStats,
    )
    
    # Phase 5.2: External pooler support
    from pynext.db.adapters.postgres_external import (
        ExternalPoolerManager,
        ExternalPoolerConfig,
        PoolerType,
        PoolerMode,
        PoolerInfo,
        PoolerDetectionError,
        PoolerCompatibilityError,
        create_pooler_config_for_supabase,
        create_pooler_config_for_render,
        create_pooler_config_for_neon,
    )
    
    _HAS_POSTGRES = True
except ImportError:
    _HAS_POSTGRES = False
    PostgresAdapter = None  # type: ignore
    PostgresConfig = None  # type: ignore
    PostgresConfigError = None  # type: ignore
    AutoScalingPool = None  # type: ignore
    PoolStats = None  # type: ignore
    PoolState = None  # type: ignore
    PooledConnection = None  # type: ignore
    ConnectionState = None  # type: ignore
    PoolExhaustedError = None  # type: ignore
    PoolClosedError = None  # type: ignore
    StatementCache = None  # type: ignore
    PerConnectionCache = None  # type: ignore
    # Phase 5.2 fallbacks
    ConnectionQueue = None  # type: ignore
    QueueConfig = None  # type: ignore
    QueueStats = None  # type: ignore
    QueuedRequest = None  # type: ignore
    QueuePriority = None  # type: ignore
    QueueOverflowAction = None  # type: ignore
    QueueFullError = None  # type: ignore
    QueueTimeoutError = None  # type: ignore
    LifecycleManager = None  # type: ignore
    LifecycleConfig = None  # type: ignore
    LifecycleStats = None  # type: ignore
    ConnectionLifecycle = None  # type: ignore
    ConnectionHealth = None  # type: ignore
    RetirementReason = None  # type: ignore
    ReplacementStrategy = None  # type: ignore
    ConnectionWarmer = None  # type: ignore
    WarmupConfig = None  # type: ignore
    WarmupResult = None  # type: ignore
    WarmupStats = None  # type: ignore
    ExternalPoolerManager = None  # type: ignore
    ExternalPoolerConfig = None  # type: ignore
    PoolerType = None  # type: ignore
    PoolerMode = None  # type: ignore
    PoolerInfo = None  # type: ignore
    PoolerDetectionError = None  # type: ignore
    PoolerCompatibilityError = None  # type: ignore
    create_pooler_config_for_supabase = None  # type: ignore
    create_pooler_config_for_render = None  # type: ignore
    create_pooler_config_for_neon = None  # type: ignore

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
    "PoolState",
    "PooledConnection",
    "ConnectionState",
    "PoolExhaustedError",
    "PoolClosedError",
    "StatementCache",
    "PerConnectionCache",
    # Phase 5.2: Queue management
    "ConnectionQueue",
    "QueueConfig",
    "QueueStats",
    "QueuedRequest",
    "QueuePriority",
    "QueueOverflowAction",
    "QueueFullError",
    "QueueTimeoutError",
    # Phase 5.2: Lifecycle management
    "LifecycleManager",
    "LifecycleConfig",
    "LifecycleStats",
    "ConnectionLifecycle",
    "ConnectionHealth",
    "RetirementReason",
    "ReplacementStrategy",
    # Phase 5.2: Connection warmup
    "ConnectionWarmer",
    "WarmupConfig",
    "WarmupResult",
    "WarmupStats",
    # Phase 5.2: External pooler support
    "ExternalPoolerManager",
    "ExternalPoolerConfig",
    "PoolerType",
    "PoolerMode",
    "PoolerInfo",
    "PoolerDetectionError",
    "PoolerCompatibilityError",
    "create_pooler_config_for_supabase",
    "create_pooler_config_for_render",
    "create_pooler_config_for_neon",
]
