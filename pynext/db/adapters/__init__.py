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
    
    # Production with Phase 5.3 Reliability Features
    from pynext.db.adapters import (
        PostgresAdapter,
        RetryConfig,
        CircuitBreakerConfig,
        Replica,
        DegradationConfig,
        DegradationTrigger,
        DegradationLevel,
        DegradationMetric,
    )
    
    adapter = PostgresAdapter(
        primary="postgresql://primary/mydb",
        replicas=[
            Replica("postgresql://replica1/mydb", weight=3),
            Replica("postgresql://replica2/mydb", weight=1),
        ],
        reliability=True,  # Enable all reliability features
        retry_config=RetryConfig(max_attempts=3),
        circuit_breaker=CircuitBreakerConfig(failure_threshold=5),
        degradation=DegradationConfig(
            triggers=[
                DegradationTrigger(DegradationMetric.QUEUE_DEPTH, 100, DegradationLevel.DEGRADED),
            ],
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
    
    # Phase 5.3: Retry logic
    from pynext.db.adapters.postgres_retry import (
        RetryConfig,
        RetryManager,
        RetryError,
        RetryStats,
        BackoffStrategy,
        with_retry,
        quick_retry,
        standard_retry,
        aggressive_retry,
        no_retry,
    )
    
    # Phase 5.3: Circuit breaker
    from pynext.db.adapters.postgres_circuit import (
        CircuitBreaker,
        CircuitBreakerConfig,
        CircuitBreakerRegistry,
        CircuitOpenError,
        CircuitScope,
        CircuitState,
        CircuitStats,
        create_global_breaker,
        create_sensitive_breaker,
        create_tolerant_breaker,
    )
    
    # Phase 5.3: Read replica routing
    from pynext.db.adapters.postgres_replica import (
        Replica,
        ReplicaConfig,
        ReplicaHealth,
        ReplicaManager,
        ReplicaStats,
        ReplicaSetStats,
        ReplicaUnavailableError,
        RoutingStrategy,
        simple_replicas,
        weighted_replicas,
    )
    
    # Phase 5.3: Graceful degradation
    from pynext.db.adapters.postgres_degradation import (
        DegradationAction,
        DegradationConfig,
        DegradationError,
        DegradationLevel,
        DegradationManager,
        DegradationMetric,
        DegradationStats,
        DegradationTrigger,
        default_actions,
        default_triggers,
        disabled_config,
        lenient_config,
        strict_config,
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
    # Phase 5.3 fallbacks
    RetryConfig = None  # type: ignore
    RetryManager = None  # type: ignore
    RetryError = None  # type: ignore
    RetryStats = None  # type: ignore
    BackoffStrategy = None  # type: ignore
    with_retry = None  # type: ignore
    quick_retry = None  # type: ignore
    standard_retry = None  # type: ignore
    aggressive_retry = None  # type: ignore
    no_retry = None  # type: ignore
    CircuitBreaker = None  # type: ignore
    CircuitBreakerConfig = None  # type: ignore
    CircuitBreakerRegistry = None  # type: ignore
    CircuitOpenError = None  # type: ignore
    CircuitScope = None  # type: ignore
    CircuitState = None  # type: ignore
    CircuitStats = None  # type: ignore
    create_global_breaker = None  # type: ignore
    create_sensitive_breaker = None  # type: ignore
    create_tolerant_breaker = None  # type: ignore
    Replica = None  # type: ignore
    ReplicaConfig = None  # type: ignore
    ReplicaHealth = None  # type: ignore
    ReplicaManager = None  # type: ignore
    ReplicaStats = None  # type: ignore
    ReplicaSetStats = None  # type: ignore
    ReplicaUnavailableError = None  # type: ignore
    RoutingStrategy = None  # type: ignore
    simple_replicas = None  # type: ignore
    weighted_replicas = None  # type: ignore
    DegradationAction = None  # type: ignore
    DegradationConfig = None  # type: ignore
    DegradationError = None  # type: ignore
    DegradationLevel = None  # type: ignore
    DegradationManager = None  # type: ignore
    DegradationMetric = None  # type: ignore
    DegradationStats = None  # type: ignore
    DegradationTrigger = None  # type: ignore
    default_actions = None  # type: ignore
    default_triggers = None  # type: ignore
    disabled_config = None  # type: ignore
    lenient_config = None  # type: ignore
    strict_config = None  # type: ignore

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
    # Phase 5.3: Retry logic
    "RetryConfig",
    "RetryManager",
    "RetryError",
    "RetryStats",
    "BackoffStrategy",
    "with_retry",
    "quick_retry",
    "standard_retry",
    "aggressive_retry",
    "no_retry",
    # Phase 5.3: Circuit breaker
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerRegistry",
    "CircuitOpenError",
    "CircuitScope",
    "CircuitState",
    "CircuitStats",
    "create_global_breaker",
    "create_sensitive_breaker",
    "create_tolerant_breaker",
    # Phase 5.3: Read replica routing
    "Replica",
    "ReplicaConfig",
    "ReplicaHealth",
    "ReplicaManager",
    "ReplicaStats",
    "ReplicaSetStats",
    "ReplicaUnavailableError",
    "RoutingStrategy",
    "simple_replicas",
    "weighted_replicas",
    # Phase 5.3: Graceful degradation
    "DegradationAction",
    "DegradationConfig",
    "DegradationError",
    "DegradationLevel",
    "DegradationManager",
    "DegradationMetric",
    "DegradationStats",
    "DegradationTrigger",
    "default_actions",
    "default_triggers",
    "disabled_config",
    "lenient_config",
    "strict_config",
]
