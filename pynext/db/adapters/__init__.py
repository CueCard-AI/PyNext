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
    
    # Production with Phase 5.5 Observability Features
    from pynext.db.adapters import (
        PostgresAdapter,
        LogConfig,
        MetricsConfig,
        AnalyzerConfig,
        MonitorConfig,
    )
    
    adapter = PostgresAdapter(
        "postgresql://...",
        logging_config=LogConfig(
            enabled=True,
            level="INFO",
            slow_query_ms=200,
            structlog_enabled=True,  # Use structlog for JSON output
        ),
        metrics_config=MetricsConfig(
            enabled=True,
            backend="prometheus",  # or "opentelemetry"
            prefix="myapp_db",
        ),
        analyzer_config=AnalyzerConfig(
            enabled=True,
            slow_query_threshold_ms=100,
            auto_explain=True,
            suggest_indexes=True,
        ),
        monitor_config=MonitorConfig(
            enabled=True,
            exhaustion_warning_threshold=0.8,
            leak_detection_timeout=300,
            health_check_interval=30,
        ),
    )
"""

from pynext.db.adapters.base import Adapter
from pynext.db.adapters.memory import MemoryAdapter
from pynext.db.adapters.mock import MockAdapter

# Phase 8.1: Go Bridge Adapter
try:
    from pynext.db.adapters.go_adapter import (
        GoPostgresAdapter,
        is_go_available,
    )
    _HAS_GO_ADAPTER = True
except ImportError:
    _HAS_GO_ADAPTER = False
    GoPostgresAdapter = None  # type: ignore
    is_go_available = lambda: False  # type: ignore

# PostgreSQL adapter (optional - requires asyncpg)
try:
    # Core adapter and configuration
    from pynext.db.adapters.postgres.core import (
        PostgresAdapter,
        PostgresConfig,
        PostgresConfigError,
        StatementCache,
        PerConnectionCache,
    )
    
    # Pool management (Phase 5.2)
    from pynext.db.adapters.postgres.pool import (
        AutoScalingPool,
        PoolStats,
        PoolState,
        PooledConnection,
        ConnectionState,
        PoolExhaustedError,
        PoolClosedError,
        ConnectionQueue,
        QueueConfig,
        QueueStats,
        QueuedRequest,
        QueuePriority,
        QueueOverflowAction,
        QueueFullError,
        QueueTimeoutError,
        LifecycleManager,
        LifecycleConfig,
        LifecycleStats,
        ConnectionLifecycle,
        ConnectionHealth,
        RetirementReason,
        ReplacementStrategy,
        ConnectionWarmer,
        WarmupConfig,
        WarmupResult,
        WarmupStats,
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
    
    # Reliability features (Phase 5.3)
    from pynext.db.adapters.postgres.reliability import (
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
    
    # Performance optimization (Phase 5.4)
    from pynext.db.adapters.postgres.performance import (
        QueryType,
        QueryTimeoutConfig,
        QueryWithTimeout,
        QueryTimeoutError,
        TimeoutStats,
        TimeoutManager,
        quick_timeout_config,
        standard_timeout_config,
        batch_timeout_config,
        no_timeout_config,
        InvalidationStrategy,
        QueryCacheConfig,
        CacheEntry,
        CacheStats,
        QueryCache,
        simple_cache_config,
        smart_cache_config,
        aggressive_cache_config,
        no_cache_config,
        CoalescingConfig,
        PendingQuery,
        CoalescingStats,
        CoalescingLimitError,
        QueryCoalescer,
        aggressive_coalescing_config,
        conservative_coalescing_config,
        disabled_coalescing_config,
        PipelineConfig,
        PipelinedQuery,
        PipelineStats,
        QueryPipeline,
        high_throughput_config,
        low_latency_config,
        disabled_pipeline_config,
        BatchConfig,
        BatchResult,
        BatchStats,
        BatchOptimizer,
        bulk_load_config,
        transactional_config,
        disabled_batch_config,
        AdaptiveScalingConfig,
        LoadSample,
        ScaleEvent,
        ScalingStats,
        ScalingRecommendation,
        AdaptiveScaler,
        aggressive_scaling_config,
        conservative_scaling_config,
        disabled_scaling_config,
    )
    
    # Observability features (Phase 5.5)
    from pynext.db.adapters.postgres.observability import (
        LogConfig,
        QueryContext,
        DBLogger,
        LogLevel,
        LogFormat,
        LogEvent,
        LogRecord,
        set_trace_id,
        get_trace_id,
        set_client_ip,
        get_client_ip,
        MetricsConfig,
        MetricsCollector,
        MetricsBackend,
        PrometheusBackend,
        OpenTelemetryBackend,
        OTLPConfig,
        QueryAnalyzer,
        AnalyzerConfig,
        ExplainResult,
        SuggestionType,
        ScanType,
        ExplainNode,
        QuerySuggestion,
        AnalysisResult,
        PoolMonitor,
        MonitorConfig,
        LeakDetector,
        HealthChecker,
        PoolEventType,
        ConnectionInfo,
        LeakInfo,
        PoolEvent,
    )
    
    # Advanced query features (Phase 5.7)
    from pynext.db.adapters.postgres.queries import (
        ChainQueryTimeoutError,
        QueryTimeout,
        TimeoutConfig,
        ChainTimeoutStats,
        TimeoutContext,
        timeout_context,
        TimeoutExecutor,
        TimeoutMixin,
        get_timeout_stats,
        reset_timeout_stats,
        get_current_timeout,
        set_current_timeout,
        create_timeout,
        create_timeout_executor,
        ExplainFormat,
        NodeType,
        SuggestionSeverity,
        BufferStats,
        PlanNode,
        Suggestion,
        QueryPlan,
        PlanComparison,
        ExplainTextParser,
        PlanAnalyzer,
        ExplainMixin,
        ExplainExecutor,
        PaginationMethod,
        CursorDirection,
        PaginationConfig,
        Cursor,
        Page,
        OffsetPage,
        KeysetPaginator,
        OffsetPaginator,
        SmartPaginator,
        StreamingPaginator,
        PaginationMixin,
        get_pagination_config,
        set_pagination_config,
        StatementState,
        PreparedStats,
        PreparedStatement,
        PreparedCache,
        PreparedExecutor,
        prepared,
        SchemaWatcher,
        get_prepared_executor,
        set_prepared_executor,
        QueryState,
        CancelReason,
        CancellationConfig,
        RunningQuery,
        CancellationToken,
        QueryCancelledError,
        QueryTracker,
        QueryRegistry,
        CancelExecutor,
        get_current_tracker,
        set_current_tracker,
        get_query_registry,
        set_query_registry,
        track_query,
        cancel_queries,
        cancel,
        get_running_queries,
    )
    
    # Backward compatibility aliases
    query_id_var = None  # Removed - use set_trace_id/get_trace_id instead
    trace_id_var = None  # Removed - use set_trace_id/get_trace_id instead
    client_ip_var = None  # Removed - use set_client_ip/get_client_ip instead
    IndexSuggestion = None  # Removed
    QueryHint = None  # Removed
    
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
    # Phase 5.4 fallbacks
    QueryType = None  # type: ignore
    QueryTimeoutConfig = None  # type: ignore
    QueryWithTimeout = None  # type: ignore
    QueryTimeoutError = None  # type: ignore
    TimeoutStats = None  # type: ignore
    TimeoutManager = None  # type: ignore
    quick_timeout_config = None  # type: ignore
    standard_timeout_config = None  # type: ignore
    batch_timeout_config = None  # type: ignore
    no_timeout_config = None  # type: ignore
    InvalidationStrategy = None  # type: ignore
    QueryCacheConfig = None  # type: ignore
    CacheEntry = None  # type: ignore
    CacheStats = None  # type: ignore
    QueryCache = None  # type: ignore
    simple_cache_config = None  # type: ignore
    smart_cache_config = None  # type: ignore
    aggressive_cache_config = None  # type: ignore
    no_cache_config = None  # type: ignore
    CoalescingConfig = None  # type: ignore
    PendingQuery = None  # type: ignore
    CoalescingStats = None  # type: ignore
    CoalescingLimitError = None  # type: ignore
    QueryCoalescer = None  # type: ignore
    aggressive_coalescing_config = None  # type: ignore
    conservative_coalescing_config = None  # type: ignore
    disabled_coalescing_config = None  # type: ignore
    PipelineConfig = None  # type: ignore
    PipelinedQuery = None  # type: ignore
    PipelineStats = None  # type: ignore
    QueryPipeline = None  # type: ignore
    high_throughput_config = None  # type: ignore
    low_latency_config = None  # type: ignore
    disabled_pipeline_config = None  # type: ignore
    BatchConfig = None  # type: ignore
    BatchResult = None  # type: ignore
    BatchStats = None  # type: ignore
    BatchOptimizer = None  # type: ignore
    bulk_load_config = None  # type: ignore
    transactional_config = None  # type: ignore
    disabled_batch_config = None  # type: ignore
    AdaptiveScalingConfig = None  # type: ignore
    LoadSample = None  # type: ignore
    ScaleEvent = None  # type: ignore
    ScalingStats = None  # type: ignore
    ScalingRecommendation = None  # type: ignore
    AdaptiveScaler = None  # type: ignore
    aggressive_scaling_config = None  # type: ignore
    conservative_scaling_config = None  # type: ignore
    disabled_scaling_config = None  # type: ignore
    # Phase 5.5 fallbacks
    LogConfig = None  # type: ignore
    QueryContext = None  # type: ignore
    DBLogger = None  # type: ignore
    LogLevel = None  # type: ignore
    LogFormat = None  # type: ignore
    LogEvent = None  # type: ignore
    LogRecord = None  # type: ignore
    set_trace_id = None  # type: ignore
    get_trace_id = None  # type: ignore
    set_client_ip = None  # type: ignore
    get_client_ip = None  # type: ignore
    query_id_var = None  # type: ignore
    trace_id_var = None  # type: ignore
    client_ip_var = None  # type: ignore
    MetricsConfig = None  # type: ignore
    MetricsCollector = None  # type: ignore
    MetricsBackend = None  # type: ignore
    PrometheusBackend = None  # type: ignore
    OpenTelemetryBackend = None  # type: ignore
    OTLPConfig = None  # type: ignore
    QueryAnalyzer = None  # type: ignore
    AnalyzerConfig = None  # type: ignore
    ExplainResult = None  # type: ignore
    SuggestionType = None  # type: ignore
    ScanType = None  # type: ignore
    ExplainNode = None  # type: ignore
    QuerySuggestion = None  # type: ignore
    AnalysisResult = None  # type: ignore
    IndexSuggestion = None  # type: ignore
    QueryHint = None  # type: ignore
    PoolMonitor = None  # type: ignore
    MonitorConfig = None  # type: ignore
    LeakDetector = None  # type: ignore
    HealthChecker = None  # type: ignore
    PoolEventType = None  # type: ignore
    ConnectionInfo = None  # type: ignore
    LeakInfo = None  # type: ignore
    PoolEvent = None  # type: ignore
    # Phase 5.7 fallbacks
    ChainQueryTimeoutError = None  # type: ignore
    QueryTimeout = None  # type: ignore
    TimeoutConfig = None  # type: ignore
    ChainTimeoutStats = None  # type: ignore
    TimeoutContext = None  # type: ignore
    timeout_context = None  # type: ignore
    TimeoutExecutor = None  # type: ignore
    TimeoutMixin = None  # type: ignore
    get_timeout_stats = None  # type: ignore
    reset_timeout_stats = None  # type: ignore
    get_current_timeout = None  # type: ignore
    set_current_timeout = None  # type: ignore
    create_timeout = None  # type: ignore
    create_timeout_executor = None  # type: ignore
    ExplainFormat = None  # type: ignore
    NodeType = None  # type: ignore
    SuggestionSeverity = None  # type: ignore
    BufferStats = None  # type: ignore
    PlanNode = None  # type: ignore
    Suggestion = None  # type: ignore
    QueryPlan = None  # type: ignore
    PlanComparison = None  # type: ignore
    ExplainTextParser = None  # type: ignore
    PlanAnalyzer = None  # type: ignore
    ExplainMixin = None  # type: ignore
    ExplainExecutor = None  # type: ignore
    PaginationMethod = None  # type: ignore
    CursorDirection = None  # type: ignore
    PaginationConfig = None  # type: ignore
    Cursor = None  # type: ignore
    Page = None  # type: ignore
    OffsetPage = None  # type: ignore
    KeysetPaginator = None  # type: ignore
    OffsetPaginator = None  # type: ignore
    SmartPaginator = None  # type: ignore
    StreamingPaginator = None  # type: ignore
    PaginationMixin = None  # type: ignore
    get_pagination_config = None  # type: ignore
    set_pagination_config = None  # type: ignore
    StatementState = None  # type: ignore
    PreparedStats = None  # type: ignore
    PreparedStatement = None  # type: ignore
    PreparedCache = None  # type: ignore
    PreparedExecutor = None  # type: ignore
    prepared = None  # type: ignore
    SchemaWatcher = None  # type: ignore
    get_prepared_executor = None  # type: ignore
    set_prepared_executor = None  # type: ignore
    QueryState = None  # type: ignore
    CancelReason = None  # type: ignore
    CancellationConfig = None  # type: ignore
    RunningQuery = None  # type: ignore
    CancellationToken = None  # type: ignore
    QueryCancelledError = None  # type: ignore
    QueryTracker = None  # type: ignore
    QueryRegistry = None  # type: ignore
    CancelExecutor = None  # type: ignore
    get_current_tracker = None  # type: ignore
    set_current_tracker = None  # type: ignore
    get_query_registry = None  # type: ignore
    set_query_registry = None  # type: ignore
    track_query = None  # type: ignore
    cancel_queries = None  # type: ignore
    cancel = None  # type: ignore
    get_running_queries = None  # type: ignore

def get_best_adapter(
    dsn: str,
    *,
    prefer_go: bool = True,
    require_go: bool = False,
    **kwargs,
):
    """
    Get the best available PostgreSQL adapter.
    
    Auto-selects between GoPostgresAdapter (if available) and PostgresAdapter.
    
    Args:
        dsn: PostgreSQL connection string
        prefer_go: Prefer Go bridge if available (default: True)
        require_go: Raise error if Go not available (default: False)
        **kwargs: Adapter configuration options
        
    Returns:
        GoPostgresAdapter or PostgresAdapter instance
        
    Raises:
        ImportError: If require_go=True and Go unavailable
        
    Example:
        # Auto-select best adapter
        adapter = get_best_adapter("postgresql://localhost/mydb")
        
        # Require Go bridge
        adapter = get_best_adapter("postgresql://...", require_go=True)
        
        # Force asyncpg even if Go available
        adapter = get_best_adapter("postgresql://...", prefer_go=False)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Check Go availability
    go_available = _HAS_GO_ADAPTER and is_go_available()
    
    if require_go and not go_available:
        raise ImportError(
            "Go bridge required but not available. "
            "Install pynext-go: pip install pynext-go"
        )
    
    if prefer_go and go_available:
        logger.info("Using Go bridge adapter (high performance)")
        return GoPostgresAdapter(dsn, **kwargs)
    
    if go_available and not prefer_go:
        logger.info("Using asyncpg adapter (Go available but not preferred)")
    else:
        logger.warning(
            "Go bridge not available, using asyncpg. "
            "Install pynext-go for better performance."
        )
    
    # Fall back to asyncpg adapter
    if PostgresAdapter is not None:
        return PostgresAdapter(dsn, **kwargs)
    
    raise ImportError(
        "No PostgreSQL adapter available. "
        "Install asyncpg: pip install asyncpg"
    )


__all__ = [
    "Adapter",
    "MemoryAdapter", 
    "MockAdapter",
    # Phase 8.1: Go Bridge
    "GoPostgresAdapter",
    "is_go_available",
    "get_best_adapter",
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
    # Phase 5.4: Per-query timeouts
    "QueryType",
    "QueryTimeoutConfig",
    "QueryWithTimeout",
    "QueryTimeoutError",
    "TimeoutStats",
    "TimeoutManager",
    "quick_timeout_config",
    "standard_timeout_config",
    "batch_timeout_config",
    "no_timeout_config",
    # Phase 5.4: Query cache with smart invalidation
    "InvalidationStrategy",
    "QueryCacheConfig",
    "CacheEntry",
    "CacheStats",
    "QueryCache",
    "simple_cache_config",
    "smart_cache_config",
    "aggressive_cache_config",
    "no_cache_config",
    # Phase 5.4: Query coalescing
    "CoalescingConfig",
    "PendingQuery",
    "CoalescingStats",
    "CoalescingLimitError",
    "QueryCoalescer",
    "aggressive_coalescing_config",
    "conservative_coalescing_config",
    "disabled_coalescing_config",
    # Phase 5.4: Query pipelining
    "PipelineConfig",
    "PipelinedQuery",
    "PipelineStats",
    "QueryPipeline",
    "high_throughput_config",
    "low_latency_config",
    "disabled_pipeline_config",
    # Phase 5.4: Batch optimization
    "BatchConfig",
    "BatchResult",
    "BatchStats",
    "BatchOptimizer",
    "bulk_load_config",
    "transactional_config",
    "disabled_batch_config",
    # Phase 5.4: Adaptive scaling
    "AdaptiveScalingConfig",
    "LoadSample",
    "ScaleEvent",
    "ScalingStats",
    "ScalingRecommendation",
    "AdaptiveScaler",
    "aggressive_scaling_config",
    "conservative_scaling_config",
    "disabled_scaling_config",
    # Phase 5.5: Structured logging
    "LogConfig",
    "QueryContext",
    "DBLogger",
    "query_id_var",
    "trace_id_var",
    "client_ip_var",
    # Phase 5.5: Metrics collection
    "MetricsConfig",
    "MetricsCollector",
    "MetricsBackend",
    # Phase 5.5: Prometheus backend
    "PrometheusBackend",
    # Phase 5.5: OpenTelemetry backend
    "OpenTelemetryBackend",
    "OTLPConfig",
    # Phase 5.5: Query analyzer
    "QueryAnalyzer",
    "AnalyzerConfig",
    "ExplainResult",
    "IndexSuggestion",
    "QueryHint",
    # Phase 5.5: Pool monitor
    "PoolMonitor",
    "MonitorConfig",
    "LeakDetector",
    "HealthChecker",
    # Phase 5.7: Per-query timeout (chain + context manager)
    "ChainQueryTimeoutError",
    "QueryTimeout",
    "TimeoutConfig",
    "ChainTimeoutStats",
    "TimeoutContext",
    "timeout_context",
    "TimeoutExecutor",
    "TimeoutMixin",
    "get_timeout_stats",
    "reset_timeout_stats",
    "get_current_timeout",
    "set_current_timeout",
    "create_timeout",
    "create_timeout_executor",
    # Phase 5.7: EXPLAIN/ANALYZE with parsing
    "ExplainFormat",
    "NodeType",
    "SuggestionSeverity",
    "BufferStats",
    "PlanNode",
    "Suggestion",
    "QueryPlan",
    "PlanComparison",
    "ExplainTextParser",
    "PlanAnalyzer",
    "ExplainMixin",
    "ExplainExecutor",
    # Phase 5.7: Cursor-based pagination
    "PaginationMethod",
    "CursorDirection",
    "PaginationConfig",
    "Cursor",
    "Page",
    "OffsetPage",
    "KeysetPaginator",
    "OffsetPaginator",
    "SmartPaginator",
    "StreamingPaginator",
    "PaginationMixin",
    "get_pagination_config",
    "set_pagination_config",
    # Phase 5.7: Prepared statements
    "StatementState",
    "PreparedStats",
    "PreparedStatement",
    "PreparedCache",
    "PreparedExecutor",
    "prepared",
    "SchemaWatcher",
    "get_prepared_executor",
    "set_prepared_executor",
    # Phase 5.7: Query cancellation
    "QueryState",
    "CancelReason",
    "CancellationConfig",
    "RunningQuery",
    "CancellationToken",
    "QueryCancelledError",
    "QueryTracker",
    "QueryRegistry",
    "CancelExecutor",
    "get_current_tracker",
    "set_current_tracker",
    "get_query_registry",
    "set_query_registry",
    "track_query",
    "cancel_queries",
    "cancel",
    "get_running_queries",
]
