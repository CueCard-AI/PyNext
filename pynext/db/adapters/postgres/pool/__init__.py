"""
PostgreSQL Connection Pool Management (Phase 5.2).

This module contains connection pooling components:
- pool.py: Auto-scaling connection pool
- queue.py: Fair request queuing with backpressure
- lifecycle.py: Connection lifecycle management
- warmup.py: Connection warming for cold starts
- external.py: External pooler support (PgBouncer, pgpool)
"""

from .pool import (
    AutoScalingPool,
    PoolStats,
    PoolState,
    PooledConnection,
    ConnectionState,
    PoolExhaustedError,
    PoolClosedError,
)
from .queue import (
    ConnectionQueue,
    QueueConfig,
    QueueStats,
    QueuedRequest,
    QueuePriority,
    QueueOverflowAction,
    QueueFullError,
    QueueTimeoutError,
)
from .lifecycle import (
    LifecycleManager,
    LifecycleConfig,
    LifecycleStats,
    ConnectionLifecycle,
    ConnectionHealth,
    RetirementReason,
    ReplacementStrategy,
)
from .warmup import (
    ConnectionWarmer,
    WarmupConfig,
    WarmupResult,
    WarmupStats,
)
from .external import (
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

__all__ = [
    # Pool
    "AutoScalingPool",
    "PoolStats",
    "PoolState",
    "PooledConnection",
    "ConnectionState",
    "PoolExhaustedError",
    "PoolClosedError",
    # Queue
    "ConnectionQueue",
    "QueueConfig",
    "QueueStats",
    "QueuedRequest",
    "QueuePriority",
    "QueueOverflowAction",
    "QueueFullError",
    "QueueTimeoutError",
    # Lifecycle
    "LifecycleManager",
    "LifecycleConfig",
    "LifecycleStats",
    "ConnectionLifecycle",
    "ConnectionHealth",
    "RetirementReason",
    "ReplacementStrategy",
    # Warmup
    "ConnectionWarmer",
    "WarmupConfig",
    "WarmupResult",
    "WarmupStats",
    # External
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

