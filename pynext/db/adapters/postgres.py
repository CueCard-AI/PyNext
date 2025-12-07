"""
PostgreSQL Adapter for PyNext.

This is the main entry point for PostgreSQL support. It provides
a dead-simple API that just works out of the box.

Usage Levels:

Level 1: One Line (Beginner)
    adapter = PostgresAdapter("postgresql://localhost/mydb")

Level 2: Explicit Config
    adapter = PostgresAdapter(
        host="localhost",
        database="mydb",
        user="postgres",
        password="secret",
    )

Level 3: Production
    adapter = PostgresAdapter(
        url="postgresql://...",
        min_connections=5,
        max_connections=100,
        statement_cache_size=1000,
    )

Level 4: Production with Phase 5.2 Features
    from pynext.db.adapters import (
        QueueConfig, LifecycleConfig, WarmupConfig,
        ExternalPoolerConfig, PoolerType, PoolerMode,
    )
    
    adapter = PostgresAdapter(
        url="postgresql://...",
        
        # Pool settings
        min_connections=10,
        max_connections=100,
        
        # Phase 5.2: Queue management
        queue_config=QueueConfig(max_size=1000),
        
        # Phase 5.2: Lifecycle management
        lifecycle_config=LifecycleConfig(soft_lifetime=1800),
        
        # Phase 5.2: Connection warmup
        warmup_config=WarmupConfig(enabled=True),
        
        # Phase 5.2: External pooler (PgBouncer)
        external_pooler=ExternalPoolerConfig(
            enabled=True,
            type=PoolerType.PGBOUNCER,
            mode=PoolerMode.TRANSACTION,
        ),
    )

Features:
- Auto-scaling connection pool
- Statement caching (10-30% faster)
- Binary protocol (not text)
- Automatic type conversion
- Full async support
- Phase 5.2: Fair queuing with backpressure
- Phase 5.2: Lifecycle management (soft/hard limits)
- Phase 5.2: Connection warmup
- Phase 5.2: External pooler support (PgBouncer, pgpool)

AI-Friendly Design:
- Every method has clear docstrings
- Type hints on all parameters
- Descriptive error messages
- Examples in docstrings
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple, Type, TYPE_CHECKING

from ..adapters.base import Adapter
from .postgres_url import PostgresConfig, PostgresConfigError
from .postgres_pool import (
    AutoScalingPool,
    PoolStats,
    PoolState,
    QueueStats,
    LifecycleStats,
    WarmupStats,
)
from .postgres_cache import StatementCache, PerConnectionCache
from .postgres_types import python_to_postgres, postgres_to_python, get_postgres_type
from .postgres_queue import QueueConfig, QueuePriority, QueueOverflowAction
from .postgres_lifecycle import LifecycleConfig, ReplacementStrategy
from .postgres_warmup import WarmupConfig
from .postgres_external import (
    ExternalPoolerConfig,
    ExternalPoolerManager,
    PoolerType,
    PoolerMode,
)

# Phase 5.3: Reliability
from .postgres_retry import (
    RetryConfig,
    RetryManager,
    RetryStats,
)
from .postgres_circuit import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerRegistry,
    CircuitState,
)
from .postgres_replica import (
    Replica,
    ReplicaConfig,
    ReplicaManager,
    ReplicaStats,
)
from .postgres_degradation import (
    DegradationConfig,
    DegradationManager,
    DegradationLevel,
)

# Phase 5.4: High-Load Optimization
from .postgres_coalesce import (
    QueryCoalescer,
    CoalescingConfig,
    CoalescingStats,
)
from .postgres_pipeline import (
    QueryPipeline,
    PipelineConfig,
    PipelineStats,
)
from .postgres_batch import (
    BatchOptimizer,
    BatchConfig,
    BatchStats,
)
from .postgres_scaling import (
    AdaptiveScaler,
    AdaptiveScalingConfig,
    ScalingStats,
)

# Phase 5.5: Observability
from .postgres_logging import (
    DBLogger,
    LogConfig,
    QueryContext,
)
from .postgres_metrics import (
    MetricsCollector,
    MetricsConfig,
)
from .postgres_analyzer import (
    QueryAnalyzer,
    AnalyzerConfig,
    QuerySuggestion,
    AnalysisResult,
)
from .postgres_monitor import (
    PoolMonitor,
    MonitorConfig,
    ConnectionInfo,
    LeakInfo,
)

# Phase 5.7: Advanced Query Features
from .postgres_query_timeout import (
    QueryTimeout,
    TimeoutContext,
    TimeoutConfig,
    TimeoutExecutor,
    TimeoutStats,
    QueryTimeoutError,
    get_timeout_stats,
    reset_timeout_stats,
)
from .postgres_explain import (
    QueryPlan,
    PlanNode,
    ExplainFormat,
    PlanAnalyzer,
    Suggestion as ExplainSuggestion,
)
from .postgres_pagination import (
    Cursor,
    Page,
    PaginationConfig,
    PaginationMethod,
    KeysetPaginator,
    OffsetPaginator,
    SmartPaginator,
)
from .postgres_prepared import (
    PreparedStatement,
    PreparedCache,
    PreparedStats,
    PreparedExecutor,
)
from .postgres_cancel import (
    QueryTracker,
    QueryRegistry,
    CancelExecutor,
    RunningQuery,
    CancellationToken,
    CancellationConfig,
    QueryCancelledError,
    CancelReason,
    get_query_registry,
    track_query,
    cancel_queries,
)

if TYPE_CHECKING:
    from ..query import Query
    from ..fields import FieldInfo
    from ..transaction import IsolationLevel
    import asyncpg

logger = logging.getLogger("pynext.db.postgres")


class PostgresAdapter(Adapter):
    """PostgreSQL adapter with asyncpg.
    
    The simplest possible API for PostgreSQL. Features:
    
    - **Auto-scaling pool**: Grows under load, shrinks when idle
    - **Statement caching**: 10-30% faster for repeated queries
    - **Binary protocol**: Maximum performance
    - **Type conversion**: Automatic Python ↔ PostgreSQL
    
    Basic Usage:
        # One line setup
        adapter = PostgresAdapter("postgresql://user:pass@localhost/mydb")
        configure_db(adapter)
        
        # Now use your models
        users = await User.all()
    
    With Options:
        adapter = PostgresAdapter(
            host="localhost",
            port=5432,
            database="myapp",
            user="postgres",
            password="secret",
            min_connections=5,
            max_connections=50,
        )
    
    Production Configuration:
        adapter = PostgresAdapter(
            url="postgresql://...",
            
            # Pool settings
            min_connections=10,       # Keep 10 connections warm
            max_connections=100,      # Scale to 100 under load
            auto_scale=True,          # Enable auto-scaling
            
            # Performance
            statement_cache_size=1000,  # Cache 1000 prepared statements
            
            # Timeouts
            connect_timeout=10.0,     # 10s to establish connection
            command_timeout=30.0,     # 30s per query
            acquire_timeout=30.0,     # 30s to get a connection
        )
    """
    
    def __init__(
        self,
        url: Optional[str] = None,
        *,
        # Connection parameters (alternative to URL)
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        ssl: Optional[bool] = None,
        
        # Pool settings
        min_connections: int = 1,
        max_connections: int = 10,
        auto_scale: bool = True,
        idle_timeout: float = 300.0,
        max_lifetime: float = 3600.0,
        acquire_timeout: float = 30.0,
        
        # Performance settings
        statement_cache_size: int = 1000,
        
        # Timeout settings
        connect_timeout: float = 10.0,
        command_timeout: Optional[float] = None,
        
        # Phase 5.2: Advanced pool configuration
        queue_config: Optional[QueueConfig] = None,
        lifecycle_config: Optional[LifecycleConfig] = None,
        warmup_config: Optional[WarmupConfig] = None,
        external_pooler: Optional[ExternalPoolerConfig] = None,
        
        # Phase 5.2: Simple warmup toggle (convenience)
        warmup: bool = False,
        warmup_query: str = "SELECT 1",
        
        # Phase 5.3: Reliability (simple toggles)
        retry: bool = True,                    # Auto-retry failed queries
        retry_attempts: int = 3,               # Max retry attempts
        circuit_breaker: bool = True,          # Enable circuit breaker
        circuit_breaker_threshold: int = 5,    # Failures before opening
        
        # Phase 5.3: Read replicas (simple list)
        replicas: Optional[List[str]] = None,  # List of replica URLs
        
        # Phase 5.4: High-load optimization (simple toggles)
        query_coalescing: bool = True,         # Dedupe identical queries
        query_batching: bool = True,           # Auto-batch small queries
        adaptive_scaling: bool = True,         # Auto-scale pool size
        
        # Phase 5.5: Observability (simple toggles)
        log_queries: bool = False,             # Log all queries
        log_slow_queries: bool = True,         # Log slow queries
        slow_query_threshold: float = 1.0,     # Seconds
        metrics: bool = False,                 # Enable metrics collection
        
        # Phase 5.7: Advanced query features
        timeout_config: Optional[TimeoutConfig] = None,
        pagination_config: Optional[PaginationConfig] = None,
        prepared_cache_size: int = 1000,
        cancellation_config: Optional[CancellationConfig] = None,
        
        # Phase 5.7: Simple toggles
        cancel_on_disconnect: bool = True,
    ):
        """Initialize the PostgreSQL adapter.
        
        You can configure the adapter using either:
        1. A URL: `PostgresAdapter("postgresql://...")`
        2. Keyword args: `PostgresAdapter(host="...", database="...")`
        3. Both: URL with keyword overrides
        
        Args:
            url: PostgreSQL connection URL (optional)
            host: Database host (default: localhost)
            port: Database port (default: 5432)
            database: Database name (default: postgres)
            user: Database user (default: postgres)
            password: Database password (optional)
            ssl: Enable SSL (default: False)
            min_connections: Minimum pool size (default: 1)
            max_connections: Maximum pool size (default: 10)
            auto_scale: Enable auto-scaling (default: True)
            idle_timeout: Close idle connections after seconds (default: 300)
            max_lifetime: Replace connections after seconds (default: 3600)
            acquire_timeout: Timeout to get connection (default: 30)
            statement_cache_size: Number of statements to cache (default: 1000)
            connect_timeout: Timeout to establish connection (default: 10)
            command_timeout: Default query timeout (default: None)
            queue_config: Phase 5.2 - Queue configuration for waiting requests
            lifecycle_config: Phase 5.2 - Lifecycle management configuration
            warmup_config: Phase 5.2 - Full warmup configuration
            external_pooler: Phase 5.2 - External pooler (PgBouncer/pgpool) config
            warmup: Phase 5.2 - Simple toggle to enable warmup (default: False)
            warmup_query: Phase 5.2 - Query for warmup (default: "SELECT 1")
            retry: Phase 5.3 - Auto-retry failed queries (default: True)
            retry_attempts: Phase 5.3 - Max retry attempts (default: 3)
            circuit_breaker: Phase 5.3 - Enable circuit breaker (default: True)
            circuit_breaker_threshold: Phase 5.3 - Failures before opening (default: 5)
            replicas: Phase 5.3 - List of replica URLs for read scaling
            query_coalescing: Phase 5.4 - Dedupe identical queries (default: True)
            query_batching: Phase 5.4 - Auto-batch small queries (default: True)
            adaptive_scaling: Phase 5.4 - Auto-scale pool size (default: True)
            log_queries: Phase 5.5 - Log all queries (default: False)
            log_slow_queries: Phase 5.5 - Log slow queries (default: True)
            slow_query_threshold: Phase 5.5 - Slow query threshold in seconds (default: 1.0)
            metrics: Phase 5.5 - Enable metrics collection (default: False)
            timeout_config: Phase 5.7 - Per-query timeout configuration
            pagination_config: Phase 5.7 - Pagination defaults
            prepared_cache_size: Phase 5.7 - Max prepared statements to cache
            cancellation_config: Phase 5.7 - Query cancellation configuration
            cancel_on_disconnect: Phase 5.7 - Auto-cancel queries on disconnect
        
        Raises:
            PostgresConfigError: If configuration is invalid
        
        Examples:
            # URL only
            adapter = PostgresAdapter("postgresql://localhost/mydb")
            
            # Keywords only
            adapter = PostgresAdapter(
                host="localhost",
                database="mydb",
                user="postgres",
            )
            
            # URL with password override (for security)
            adapter = PostgresAdapter(
                url="postgresql://user@localhost/mydb",
                password=os.environ["DB_PASSWORD"],
            )
            
            # With warmup (Phase 5.2)
            adapter = PostgresAdapter(
                url="postgresql://localhost/mydb",
                warmup=True,  # Enable connection warmup
            )
            
            # With PgBouncer (Phase 5.2)
            adapter = PostgresAdapter(
                url="postgresql://localhost:6432/mydb",
                external_pooler=ExternalPoolerConfig(
                    enabled=True,
                    mode=PoolerMode.TRANSACTION,
                ),
            )
        """
        # Build configuration
        overrides: Dict[str, Any] = {}
        if host is not None:
            overrides["host"] = host
        if port is not None:
            overrides["port"] = port
        if database is not None:
            overrides["database"] = database
        if user is not None:
            overrides["user"] = user
        if password is not None:
            overrides["password"] = password
        if ssl is not None:
            overrides["ssl"] = ssl
        
        if url:
            self._config = PostgresConfig.from_url(url, **overrides)
        elif overrides:
            self._config = PostgresConfig(**overrides)
        else:
            self._config = PostgresConfig()
        
        # Store settings
        self._min_connections = min_connections
        self._max_connections = max_connections
        self._auto_scale = auto_scale
        self._idle_timeout = idle_timeout
        self._max_lifetime = max_lifetime
        self._acquire_timeout = acquire_timeout
        self._statement_cache_size = statement_cache_size
        self._connect_timeout = connect_timeout
        self._command_timeout = command_timeout
        
        # Phase 5.2: Advanced configurations
        self._queue_config = queue_config
        self._lifecycle_config = lifecycle_config
        self._external_pooler_config = external_pooler
        
        # Phase 5.2: Handle simple warmup toggle
        if warmup_config:
            self._warmup_config = warmup_config
        elif warmup:
            self._warmup_config = WarmupConfig(
                enabled=True,
                query=warmup_query,
            )
        else:
            self._warmup_config = None
        
        # Pool (created on connect)
        self._pool: Optional[AutoScalingPool] = None
        
        # Statement cache (per-connection)
        self._cache_manager = PerConnectionCache(max_statements=statement_cache_size)
        
        # Transaction state
        self._in_transaction = False
        self._current_connection: Optional["asyncpg.Connection"] = None
        
        # Phase 5.3: Reliability
        self._retry_enabled = retry
        self._retry_manager = RetryManager(RetryConfig(
            max_attempts=retry_attempts,
        )) if retry else None
        
        self._circuit_breaker_enabled = circuit_breaker
        self._circuit_breaker_registry = CircuitBreakerRegistry(
            config=CircuitBreakerConfig(failure_threshold=circuit_breaker_threshold)
        ) if circuit_breaker else None
        
        self._replica_manager: Optional[ReplicaManager] = None
        self._replica_urls = replicas or []
        
        self._degradation_manager = DegradationManager(DegradationConfig())
        
        # Phase 5.4: High-Load Optimization
        self._query_coalescing_enabled = query_coalescing
        self._query_coalescer = QueryCoalescer(CoalescingConfig()) if query_coalescing else None
        
        self._query_batching_enabled = query_batching
        self._batch_optimizer = BatchOptimizer(BatchConfig()) if query_batching else None
        
        self._adaptive_scaling_enabled = adaptive_scaling
        self._adaptive_scaler = AdaptiveScaler(AdaptiveScalingConfig()) if adaptive_scaling else None
        
        # Phase 5.5: Observability
        self._log_queries = log_queries
        self._log_slow_queries = log_slow_queries
        self._slow_query_threshold = slow_query_threshold
        self._db_logger = DBLogger(LogConfig(
            log_queries=log_queries,
            slow_query_ms=slow_query_threshold * 1000 if slow_query_threshold else 100.0,
        ))
        
        self._metrics_enabled = metrics
        self._metrics_collector = MetricsCollector(MetricsConfig()) if metrics else None
        
        self._query_analyzer = QueryAnalyzer(AnalyzerConfig(
            slow_threshold_ms=slow_query_threshold * 1000 if slow_query_threshold else 100.0,
        ))
        
        self._pool_monitor = PoolMonitor(MonitorConfig())
        
        # Phase 5.7: Advanced query features
        self._timeout_config = timeout_config or TimeoutConfig()
        self._timeout_executor = TimeoutExecutor(self._timeout_config)
        
        self._pagination_config = pagination_config or PaginationConfig()
        self._smart_paginator = SmartPaginator(self._pagination_config)
        
        self._prepared_cache_size = prepared_cache_size
        self._prepared_cache = PreparedCache(max_size=prepared_cache_size)
        self._prepared_executor = PreparedExecutor(self._prepared_cache)
        
        self._cancellation_config = cancellation_config or CancellationConfig(
            cancel_on_disconnect=cancel_on_disconnect
        )
        self._query_registry = QueryRegistry(self._cancellation_config)
        self._cancel_executor = CancelExecutor(
            self._query_registry,
            execute_fn=self._execute_cancel,
        )
    
    # =========================================================================
    # Lifecycle
    # =========================================================================
    
    async def connect(self) -> None:
        """Connect to PostgreSQL and initialize the pool.
        
        This method:
        1. Creates the connection pool
        2. Establishes initial connections
        3. Warms connections (if warmup enabled - Phase 5.2)
        4. Validates the connection
        
        Call this before using the adapter.
        
        Example:
            adapter = PostgresAdapter("postgresql://localhost/mydb")
            await adapter.connect()
            # Now ready to use
        """
        if self._pool is not None:
            logger.warning("Adapter already connected")
            return
        
        logger.info(f"Connecting to PostgreSQL: {self._config}")
        
        self._pool = AutoScalingPool(
            config=self._config,
            min_size=self._min_connections,
            max_size=self._max_connections,
            auto_scale=self._auto_scale,
            idle_timeout=self._idle_timeout,
            max_lifetime=self._max_lifetime,
            acquire_timeout=self._acquire_timeout,
            connect_timeout=self._connect_timeout,
            command_timeout=self._command_timeout,
            # Phase 5.2: Advanced configurations
            queue_config=self._queue_config,
            lifecycle_config=self._lifecycle_config,
            warmup_config=self._warmup_config,
            external_pooler=self._external_pooler_config,
        )
        
        await self._pool.start()
        
        # Validate connection
        try:
            result = await self._pool.fetchval("SELECT 1")
            if result != 1:
                raise RuntimeError("Connection validation failed")
            logger.info("PostgreSQL connection established")
        except Exception as e:
            await self._pool.close()
            self._pool = None
            raise RuntimeError(
                f"Failed to connect to PostgreSQL: {e}\n"
                f"Config: {self._config}"
            )
    
    async def disconnect(self) -> None:
        """Disconnect from PostgreSQL.
        
        Closes all connections in the pool.
        
        Example:
            await adapter.disconnect()
        """
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
            logger.info("PostgreSQL connection closed")
    
    # =========================================================================
    # Table Operations
    # =========================================================================
    
    async def create_table(self, table: str, fields: Dict[str, "FieldInfo"]) -> None:
        """Create a table with the given fields.
        
        Includes FK constraints with ON DELETE actions from cascade configuration.
        
        Args:
            table: Table name
            fields: Field definitions
        
        Example:
            # With on_delete="cascade" set on parent relationship:
            CREATE TABLE "posts" (
                "id" SERIAL PRIMARY KEY,
                "author_id" INTEGER NOT NULL REFERENCES "users"("id") ON DELETE CASCADE
            )
        """
        columns = []
        
        for name, field_info in fields.items():
            pg_type = get_postgres_type(field_info.python_type)
            
            col_def = f'"{name}" {pg_type}'
            
            if field_info.primary_key:
                if pg_type in ("INTEGER", "BIGINT"):
                    col_def = f'"{name}" SERIAL PRIMARY KEY'
                else:
                    col_def += " PRIMARY KEY"
            else:
                if not field_info.nullable:
                    col_def += " NOT NULL"
                if field_info.unique:
                    col_def += " UNIQUE"
                if field_info.default is not None:
                    default_val = self._format_default(field_info.default)
                    col_def += f" DEFAULT {default_val}"
                
                # Add FK constraint with ON DELETE (Phase 7.4.1)
                if field_info.foreign_key:
                    col_def += f' REFERENCES "{field_info.foreign_key}"("id")'
                    # Add ON DELETE clause if not default
                    fk_on_delete = getattr(field_info, 'fk_on_delete', 'NO ACTION')
                    if fk_on_delete and fk_on_delete != "NO ACTION":
                        col_def += f" ON DELETE {fk_on_delete}"
            
            columns.append(col_def)
        
        sql = f'CREATE TABLE IF NOT EXISTS "{table}" (\n  ' + ",\n  ".join(columns) + "\n)"
        
        await self._execute(sql)
        logger.info(f"Created table: {table}")
    
    async def drop_table(self, table: str) -> None:
        """Drop a table.
        
        Args:
            table: Table name
        """
        await self._execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')
        logger.info(f"Dropped table: {table}")
    
    # =========================================================================
    # FK Constraint Operations (Phase 7.4.1)
    # =========================================================================
    
    async def get_foreign_keys(self, table: str) -> List[Dict[str, Any]]:
        """
        Get all FK constraints for a table.
        
        This is useful for introspecting the database schema.
        
        Args:
            table: Table name
        
        Returns:
            List of dicts with FK info:
            [
                {
                    "constraint_name": "posts_author_id_fkey",
                    "column_name": "author_id",
                    "foreign_table": "users",
                    "foreign_column": "id",
                    "on_delete": "CASCADE"
                }
            ]
        
        Example:
            fks = await adapter.get_foreign_keys("posts")
            for fk in fks:
                print(f"{fk['column_name']} -> {fk['foreign_table']}.{fk['foreign_column']}")
        """
        sql = """
            SELECT
                tc.constraint_name,
                kcu.column_name,
                ccu.table_name AS foreign_table,
                ccu.column_name AS foreign_column,
                rc.delete_rule AS on_delete
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            JOIN information_schema.referential_constraints rc
                ON rc.constraint_name = tc.constraint_name
                AND rc.constraint_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name = $1
        """
        
        rows = await self._fetch(sql, table)
        return [
            {
                "constraint_name": row["constraint_name"],
                "column_name": row["column_name"],
                "foreign_table": row["foreign_table"],
                "foreign_column": row["foreign_column"],
                "on_delete": row["on_delete"],
            }
            for row in rows
        ]
    
    async def has_constraint(self, table: str, constraint_name: str) -> bool:
        """
        Check if a constraint exists on a table.
        
        Args:
            table: Table name
            constraint_name: Name of the constraint to check
        
        Returns:
            True if constraint exists, False otherwise
        
        Example:
            if await adapter.has_constraint("posts", "posts_author_id_fkey"):
                print("FK constraint exists")
        """
        sql = """
            SELECT 1 FROM information_schema.table_constraints
            WHERE table_name = $1 AND constraint_name = $2
            LIMIT 1
        """
        
        result = await self._fetchrow(sql, table, constraint_name)
        return result is not None
    
    async def add_fk_constraint(
        self,
        table: str,
        column: str,
        ref_table: str,
        ref_column: str = "id",
        on_delete: str = "NO ACTION",
        constraint_name: Optional[str] = None,
    ) -> None:
        """
        Add a FK constraint to an existing table.
        
        Use this for migrations or when adding FK constraints after table creation.
        
        Args:
            table: Table with the FK column
            column: FK column name
            ref_table: Referenced table
            ref_column: Referenced column (default: "id")
            on_delete: ON DELETE action (CASCADE, SET NULL, RESTRICT, NO ACTION)
            constraint_name: Custom constraint name (auto-generated if None)
        
        Example:
            # Add FK with CASCADE
            await adapter.add_fk_constraint(
                "posts", "author_id", "users",
                on_delete="CASCADE"
            )
            
            # Add FK with custom name
            await adapter.add_fk_constraint(
                "posts", "author_id", "users",
                constraint_name="posts_author_fk"
            )
        """
        if constraint_name is None:
            constraint_name = f"{table}_{column}_fkey"
        
        sql = f"""
            ALTER TABLE "{table}"
            ADD CONSTRAINT "{constraint_name}"
            FOREIGN KEY ("{column}")
            REFERENCES "{ref_table}"("{ref_column}")
            ON DELETE {on_delete}
        """
        
        await self._execute(sql)
        logger.info(f"Added FK constraint: {constraint_name} on {table}.{column}")
    
    async def alter_fk_on_delete(
        self,
        table: str,
        column: str,
        on_delete: str,
        constraint_name: Optional[str] = None,
    ) -> None:
        """
        Change the ON DELETE action for an existing FK constraint.
        
        This drops the existing constraint and recreates it with the new action.
        
        Args:
            table: Table with the FK column
            column: FK column name
            on_delete: New ON DELETE action (CASCADE, SET NULL, RESTRICT, NO ACTION)
            constraint_name: Constraint name (auto-detected if None)
        
        Example:
            # Change from NO ACTION to CASCADE
            await adapter.alter_fk_on_delete("posts", "author_id", "CASCADE")
        """
        # Find the constraint if name not provided
        if constraint_name is None:
            fks = await self.get_foreign_keys(table)
            for fk in fks:
                if fk["column_name"] == column:
                    constraint_name = fk["constraint_name"]
                    ref_table = fk["foreign_table"]
                    ref_column = fk["foreign_column"]
                    break
            
            if constraint_name is None:
                raise ValueError(f"No FK constraint found for {table}.{column}")
        else:
            # Need to look up ref table/column
            fks = await self.get_foreign_keys(table)
            for fk in fks:
                if fk["constraint_name"] == constraint_name:
                    ref_table = fk["foreign_table"]
                    ref_column = fk["foreign_column"]
                    break
            else:
                raise ValueError(f"Constraint {constraint_name} not found on {table}")
        
        # Drop and recreate
        await self._execute(f'ALTER TABLE "{table}" DROP CONSTRAINT "{constraint_name}"')
        await self.add_fk_constraint(
            table, column, ref_table, ref_column, on_delete, constraint_name
        )
        
        logger.info(f"Altered FK constraint {constraint_name}: ON DELETE {on_delete}")
    
    async def drop_fk_constraint(
        self,
        table: str,
        constraint_name: str,
    ) -> None:
        """
        Drop a FK constraint.
        
        Args:
            table: Table with the constraint
            constraint_name: Name of the constraint to drop
        
        Example:
            await adapter.drop_fk_constraint("posts", "posts_author_id_fkey")
        """
        await self._execute(f'ALTER TABLE "{table}" DROP CONSTRAINT "{constraint_name}"')
        logger.info(f"Dropped FK constraint: {constraint_name}")
    
    # =========================================================================
    # CRUD Operations
    # =========================================================================
    
    async def insert(
        self,
        table: str,
        data: Dict[str, Any],
        fields: Dict[str, "FieldInfo"],
    ) -> Dict[str, Any]:
        """Insert a row and return the created record.
        
        Args:
            table: Table name
            data: Column values to insert
            fields: Field definitions
        
        Returns:
            The created row including generated id
        """
        # Convert values
        converted = {}
        for key, value in data.items():
            if key in fields:
                converted[key] = python_to_postgres(value)
            else:
                converted[key] = value
        
        columns = list(converted.keys())
        values = list(converted.values())
        placeholders = [f"${i+1}" for i in range(len(columns))]
        
        col_str = ", ".join(f'"{c}"' for c in columns)
        val_str = ", ".join(placeholders)
        
        sql = f'INSERT INTO "{table}" ({col_str}) VALUES ({val_str}) RETURNING *'
        
        row = await self._fetchrow(sql, *values)
        return dict(row) if row else {}
    
    async def insert_many(
        self,
        table: str,
        data: List[Dict[str, Any]],
        fields: Dict[str, "FieldInfo"],
    ) -> List[Dict[str, Any]]:
        """Insert multiple rows.
        
        Args:
            table: Table name
            data: List of row dicts
            fields: Field definitions
        
        Returns:
            List of created rows
        """
        if not data:
            return []
        
        results = []
        for row_data in data:
            result = await self.insert(table, row_data, fields)
            results.append(result)
        return results
    
    async def select(
        self,
        table: str,
        query: "Query",
        fields: Dict[str, "FieldInfo"],
    ) -> List[Dict[str, Any]]:
        """Select rows matching the query.
        
        Args:
            table: Table name
            query: Query with filters, ordering, etc.
            fields: Field definitions
        
        Returns:
            List of matching rows
        """
        sql, params = self._build_select(table, query)
        rows = await self._fetch(sql, *params)
        return [dict(row) for row in rows]
    
    async def select_one(
        self,
        table: str,
        query: "Query",
        fields: Dict[str, "FieldInfo"],
    ) -> Optional[Dict[str, Any]]:
        """Select a single row.
        
        Args:
            table: Table name
            query: Query with filters
            fields: Field definitions
        
        Returns:
            The matching row or None
        """
        sql, params = self._build_select(table, query)
        sql += " LIMIT 1"
        row = await self._fetchrow(sql, *params)
        return dict(row) if row else None
    
    async def update(
        self,
        table: str,
        id: int,
        data: Dict[str, Any],
        fields: Dict[str, "FieldInfo"],
    ) -> Dict[str, Any]:
        """Update a row by id.
        
        Args:
            table: Table name
            id: Row id
            data: Column values to update
            fields: Field definitions
        
        Returns:
            The updated row
        """
        converted = {}
        for key, value in data.items():
            if key in fields:
                converted[key] = python_to_postgres(value)
            else:
                converted[key] = value
        
        set_clauses = []
        values = []
        for i, (key, value) in enumerate(converted.items(), 1):
            set_clauses.append(f'"{key}" = ${i}')
            values.append(value)
        
        set_str = ", ".join(set_clauses)
        id_placeholder = f"${len(values) + 1}"
        values.append(id)
        
        sql = f'UPDATE "{table}" SET {set_str} WHERE "id" = {id_placeholder} RETURNING *'
        
        row = await self._fetchrow(sql, *values)
        return dict(row) if row else {}
    
    async def update_many(
        self,
        table: str,
        query: "Query",
        data: Dict[str, Any],
        fields: Dict[str, "FieldInfo"],
    ) -> int:
        """Update multiple rows.
        
        Args:
            table: Table name
            query: Query with filters
            data: Column values to update
            fields: Field definitions
        
        Returns:
            Number of updated rows
        """
        converted = {}
        for key, value in data.items():
            if key in fields:
                converted[key] = python_to_postgres(value)
            else:
                converted[key] = value
        
        set_clauses = []
        values = []
        for i, (key, value) in enumerate(converted.items(), 1):
            set_clauses.append(f'"{key}" = ${i}')
            values.append(value)
        
        set_str = ", ".join(set_clauses)
        where_clause, where_params = self._build_where(query, len(values))
        values.extend(where_params)
        
        sql = f'UPDATE "{table}" SET {set_str}'
        if where_clause:
            sql += f" WHERE {where_clause}"
        
        result = await self._execute(sql, *values)
        # Parse "UPDATE N" result
        try:
            return int(result.split()[1])
        except (IndexError, ValueError):
            return 0
    
    async def delete(self, table: str, id: int) -> bool:
        """Delete a row by id.
        
        Handles FK constraint violations by translating them to ProtectedDeleteError.
        This happens when on_delete="protect" (RESTRICT) is set on a relationship
        and there are related records.
        
        Args:
            table: Table name
            id: Row id
        
        Returns:
            True if deleted, False if not found
        
        Raises:
            ForeignKeyViolationError: When deletion violates a RESTRICT constraint
        """
        sql = f'DELETE FROM "{table}" WHERE "id" = $1'
        try:
            result = await self._execute(sql, id)
            return "DELETE 1" in result
        except Exception as e:
            # Handle FK violation (RESTRICT)
            error_str = str(e).lower()
            if "foreign" in error_str and ("violates" in error_str or "constraint" in error_str):
                from pynext.db.relationships.cascade import ProtectedDeleteError
                
                # Extract constraint info from error message
                constraint_name = self._extract_constraint_name(str(e))
                related_table = self._extract_related_table(str(e))
                
                # Create a placeholder instance for the error
                class DummyInstance:
                    def __init__(self, table_name, row_id):
                        self.id = row_id
                        self.__class__.__name__ = table_name.rstrip('s').title()
                
                raise ProtectedDeleteError(
                    instance=DummyInstance(table, id),
                    relationship=related_table or constraint_name or "related",
                    related_count=1,  # We don't know exact count from DB error
                )
            raise  # Re-raise other exceptions
    
    async def delete_many(self, table: str, query: "Query") -> int:
        """Delete multiple rows.
        
        Args:
            table: Table name
            query: Query with filters
        
        Returns:
            Number of deleted rows
        """
        where_clause, params = self._build_where(query)
        
        sql = f'DELETE FROM "{table}"'
        if where_clause:
            sql += f" WHERE {where_clause}"
        
        result = await self._execute(sql, *params)
        try:
            return int(result.split()[1])
        except (IndexError, ValueError):
            return 0
    
    async def count(self, table: str, query: "Query") -> int:
        """Count rows matching the query.
        
        Args:
            table: Table name
            query: Query with filters
        
        Returns:
            Number of matching rows
        """
        where_clause, params = self._build_where(query)
        
        sql = f'SELECT COUNT(*) FROM "{table}"'
        if where_clause:
            sql += f" WHERE {where_clause}"
        
        result = await self._fetchval(sql, *params)
        return result or 0
    
    async def exists(self, table: str, query: "Query") -> bool:
        """Check if any rows match the query.
        
        Args:
            table: Table name
            query: Query with filters
        
        Returns:
            True if any rows match
        """
        count = await self.count(table, query)
        return count > 0
    
    # =========================================================================
    # Raw SQL
    # =========================================================================
    
    async def execute(
        self,
        sql: str,
        params: Optional[Tuple[Any, ...]] = None,
    ) -> Any:
        """Execute raw SQL.
        
        Args:
            sql: SQL query with $1, $2, ... placeholders
            params: Parameter values
        
        Returns:
            Query result
        """
        if params:
            return await self._execute(sql, *params)
        return await self._execute(sql)
    
    async def fetch_all(
        self,
        sql: str,
        params: Optional[Tuple[Any, ...]] = None,
    ) -> List[Dict[str, Any]]:
        """Execute SQL and return all rows.
        
        Args:
            sql: SQL query
            params: Parameter values
        
        Returns:
            List of row dicts
        """
        if params:
            rows = await self._fetch(sql, *params)
        else:
            rows = await self._fetch(sql)
        return [dict(row) for row in rows]
    
    async def fetch_one(
        self,
        sql: str,
        params: Optional[Tuple[Any, ...]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Execute SQL and return one row.
        
        Args:
            sql: SQL query
            params: Parameter values
        
        Returns:
            Row dict or None
        """
        if params:
            row = await self._fetchrow(sql, *params)
        else:
            row = await self._fetchrow(sql)
        return dict(row) if row else None
    
    # =========================================================================
    # Transactions
    # =========================================================================
    
    async def begin_transaction(self, isolation: Optional["IsolationLevel"] = None) -> None:
        """Begin a transaction."""
        if self._pool is None:
            raise RuntimeError("Not connected")
        
        # Get a dedicated connection for the transaction
        self._current_connection = await self._pool._acquire_connection()
        self._in_transaction = True
        
        if isolation:
            await self._current_connection.connection.execute(
                f"BEGIN ISOLATION LEVEL {isolation.upper().replace('_', ' ')}"
            )
        else:
            await self._current_connection.connection.execute("BEGIN")
    
    async def commit_transaction(self) -> None:
        """Commit the current transaction."""
        if not self._in_transaction or self._current_connection is None:
            raise RuntimeError("No active transaction")
        
        await self._current_connection.connection.execute("COMMIT")
        await self._pool._release_connection(self._current_connection)
        self._current_connection = None
        self._in_transaction = False
    
    async def rollback_transaction(self) -> None:
        """Rollback the current transaction."""
        if not self._in_transaction or self._current_connection is None:
            raise RuntimeError("No active transaction")
        
        await self._current_connection.connection.execute("ROLLBACK")
        await self._pool._release_connection(self._current_connection)
        self._current_connection = None
        self._in_transaction = False
    
    async def savepoint(self, name: str) -> None:
        """Create a savepoint."""
        if not self._in_transaction:
            raise RuntimeError("Savepoint requires active transaction")
        await self._current_connection.connection.execute(f'SAVEPOINT "{name}"')
    
    async def release_savepoint(self, name: str) -> None:
        """Release a savepoint."""
        if not self._in_transaction:
            raise RuntimeError("No active transaction")
        await self._current_connection.connection.execute(f'RELEASE SAVEPOINT "{name}"')
    
    async def rollback_savepoint(self, name: str) -> None:
        """Rollback to a savepoint."""
        if not self._in_transaction:
            raise RuntimeError("No active transaction")
        await self._current_connection.connection.execute(f'ROLLBACK TO SAVEPOINT "{name}"')
    
    # =========================================================================
    # Internal Helpers
    # =========================================================================
    
    async def _execute(self, sql: str, *args: Any) -> str:
        """Execute SQL and return status."""
        if self._pool is None:
            raise RuntimeError("Not connected. Call connect() first.")
        
        if self._in_transaction and self._current_connection:
            return await self._current_connection.connection.execute(sql, *args)
        
        return await self._pool.execute(sql, *args)
    
    async def _fetch(self, sql: str, *args: Any) -> List[Any]:
        """Execute SQL and return all rows."""
        if self._pool is None:
            raise RuntimeError("Not connected. Call connect() first.")
        
        if self._in_transaction and self._current_connection:
            return await self._current_connection.connection.fetch(sql, *args)
        
        return await self._pool.fetch(sql, *args)
    
    async def _fetchrow(self, sql: str, *args: Any) -> Optional[Any]:
        """Execute SQL and return one row."""
        if self._pool is None:
            raise RuntimeError("Not connected. Call connect() first.")
        
        if self._in_transaction and self._current_connection:
            return await self._current_connection.connection.fetchrow(sql, *args)
        
        return await self._pool.fetchrow(sql, *args)
    
    async def _fetchval(self, sql: str, *args: Any) -> Any:
        """Execute SQL and return a single value."""
        if self._pool is None:
            raise RuntimeError("Not connected. Call connect() first.")
        
        if self._in_transaction and self._current_connection:
            return await self._current_connection.connection.fetchval(sql, *args)
        
        return await self._pool.fetchval(sql, *args)
    
    def _build_select(self, table: str, query: "Query") -> Tuple[str, List[Any]]:
        """Build a SELECT query."""
        sql = f'SELECT * FROM "{table}"'
        params: List[Any] = []
        
        where_clause, where_params = self._build_where(query)
        if where_clause:
            sql += f" WHERE {where_clause}"
            params.extend(where_params)
        
        if query._order_by:
            order_parts = []
            for field, direction in query._order_by:
                order_parts.append(f'"{field}" {direction}')
            sql += f" ORDER BY {', '.join(order_parts)}"
        
        if query._limit is not None:
            sql += f" LIMIT ${len(params) + 1}"
            params.append(query._limit)
        
        if query._offset is not None:
            sql += f" OFFSET ${len(params) + 1}"
            params.append(query._offset)
        
        return sql, params
    
    def _build_where(
        self,
        query: "Query",
        param_offset: int = 0,
    ) -> Tuple[str, List[Any]]:
        """Build WHERE clause from query conditions."""
        if not query._conditions:
            return "", []
        
        conditions = []
        params = []
        
        for i, (field, op, value) in enumerate(query._conditions, param_offset + 1):
            if op == "eq":
                conditions.append(f'"{field}" = ${i}')
                params.append(value)
            elif op == "ne":
                conditions.append(f'"{field}" != ${i}')
                params.append(value)
            elif op == "gt":
                conditions.append(f'"{field}" > ${i}')
                params.append(value)
            elif op == "gte":
                conditions.append(f'"{field}" >= ${i}')
                params.append(value)
            elif op == "lt":
                conditions.append(f'"{field}" < ${i}')
                params.append(value)
            elif op == "lte":
                conditions.append(f'"{field}" <= ${i}')
                params.append(value)
            elif op == "in":
                conditions.append(f'"{field}" = ANY(${i})')
                params.append(list(value))
            elif op == "like":
                conditions.append(f'"{field}" LIKE ${i}')
                params.append(value)
            elif op == "ilike":
                conditions.append(f'"{field}" ILIKE ${i}')
                params.append(value)
            elif op == "is_null":
                if value:
                    conditions.append(f'"{field}" IS NULL')
                else:
                    conditions.append(f'"{field}" IS NOT NULL')
        
        return " AND ".join(conditions), params
    
    def _format_default(self, value: Any) -> str:
        """Format a default value for SQL."""
        if value is None:
            return "NULL"
        elif isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            escaped = value.replace("'", "''")
            return f"'{escaped}'"
        else:
            escaped = str(value).replace("'", "''")
            return f"'{escaped}'"
    
    def _extract_constraint_name(self, error_msg: str) -> Optional[str]:
        """
        Extract FK constraint name from PostgreSQL error message.
        
        Args:
            error_msg: PostgreSQL error message
        
        Returns:
            Constraint name or None if not found
        
        Example:
            Error: "violates foreign key constraint 'posts_author_id_fkey'"
            Returns: "posts_author_id_fkey"
        """
        import re
        
        # Pattern: constraint "constraint_name" or constraint 'constraint_name'
        patterns = [
            r'constraint\s*["\'](\w+)["\']',
            r'constraint\s+(\w+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, error_msg, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_related_table(self, error_msg: str) -> Optional[str]:
        """
        Extract related table name from PostgreSQL FK error message.
        
        Args:
            error_msg: PostgreSQL error message
        
        Returns:
            Table name or None if not found
        
        Example:
            Error: "on table 'posts' violates foreign key constraint"
            Returns: "posts"
        """
        import re
        
        # Pattern: on table "tablename" or table 'tablename'
        patterns = [
            r'on\s+table\s*["\'](\w+)["\']',
            r'table\s*["\'](\w+)["\']',
            r'from\s+table\s*["\'](\w+)["\']',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, error_msg, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    # =========================================================================
    # Pool Stats
    # =========================================================================
    
    def get_pool_stats(self) -> Optional[PoolStats]:
        """Get connection pool statistics.
        
        Returns:
            PoolStats or None if not connected
        
        Example:
            stats = adapter.get_pool_stats()
            print(f"Connections: {stats.busy}/{stats.size}")
            # Phase 5.2 metrics
            print(f"Queue depth: {stats.queue_depth}")
            print(f"Warmup success: {stats.warmup_success_rate:.1%}")
        """
        if self._pool is None:
            return None
        return self._pool.get_stats()
    
    def get_queue_stats(self) -> Optional[QueueStats]:
        """Get detailed queue statistics (Phase 5.2).
        
        Returns:
            QueueStats or None if not connected
        
        Example:
            stats = adapter.get_queue_stats()
            print(f"Waiting: {stats.depth}")
            print(f"Avg wait: {stats.wait_time_avg_ms:.1f}ms")
        """
        if self._pool is None:
            return None
        return self._pool.get_queue_stats()
    
    def get_lifecycle_stats(self) -> Optional[LifecycleStats]:
        """Get detailed lifecycle statistics (Phase 5.2).
        
        Returns:
            LifecycleStats or None if not connected
        
        Example:
            stats = adapter.get_lifecycle_stats()
            print(f"Retired: {stats.total_connections_retired}")
            print(f"Avg lifetime: {stats.avg_connection_lifetime_ms:.0f}ms")
        """
        if self._pool is None:
            return None
        return self._pool.get_lifecycle_stats()
    
    def get_warmup_stats(self) -> Optional[WarmupStats]:
        """Get detailed warmup statistics (Phase 5.2).
        
        Returns:
            WarmupStats or None if not connected
        
        Example:
            stats = adapter.get_warmup_stats()
            print(f"Success rate: {stats.success_rate:.1%}")
            print(f"Avg warmup: {stats.avg_duration_ms:.1f}ms")
        """
        if self._pool is None:
            return None
        return self._pool.get_warmup_stats()
    
    @property
    def is_under_pressure(self) -> bool:
        """Check if pool is under pressure (Phase 5.2).
        
        Returns True if queue has waiting requests approaching capacity.
        Use for backpressure signaling in your application.
        
        Example:
            if adapter.is_under_pressure:
                return Response("System busy, try again", status=503)
        """
        if self._pool is None:
            return False
        return self._pool.is_under_pressure
    
    @property
    def queue_depth(self) -> int:
        """Current number of requests waiting for connections (Phase 5.2).
        
        Returns:
            Number of waiting requests, 0 if not connected
        """
        if self._pool is None:
            return 0
        return self._pool.queue_depth
    
    # =========================================================================
    # Phase 5.7: Per-Query Timeouts
    # =========================================================================
    
    def timeout(self, seconds: float, message: Optional[str] = None) -> TimeoutContext:
        """Create a timeout context for queries.
        
        Args:
            seconds: Maximum time for queries in this context
            message: Custom error message if timeout occurs
        
        Returns:
            Context manager that applies timeout to all queries within
        
        Example:
            async with adapter.timeout(5):
                # All queries here have a 5 second timeout
                users = await User.all()
                orders = await Order.all()
            
            # With custom message
            async with adapter.timeout(10, "Report generation timed out"):
                report = await generate_report()
        """
        return TimeoutContext(seconds, message)
    
    def get_timeout_stats(self) -> TimeoutStats:
        """Get timeout statistics.
        
        Returns:
            Statistics about query timeouts
        
        Example:
            stats = adapter.get_timeout_stats()
            print(f"Timeouts: {stats.timeout_count}/{stats.total_queries}")
        """
        return get_timeout_stats()
    
    # =========================================================================
    # Phase 5.7: EXPLAIN/ANALYZE
    # =========================================================================
    
    async def explain(
        self,
        sql: str,
        *args,
        analyze: bool = False,
        buffers: bool = False,
        format: str = "text",
    ) -> QueryPlan:
        """Get execution plan for a query.
        
        Args:
            sql: SQL query to explain
            *args: Query parameters
            analyze: Actually execute the query (measures real time)
            buffers: Include buffer usage statistics
            format: Output format (text, json, yaml, xml)
        
        Returns:
            QueryPlan with parsed execution plan
        
        Example:
            # Basic explain
            plan = await adapter.explain("SELECT * FROM users WHERE active")
            print(plan.cost)
            print(plan.rows)
            
            # With analysis
            plan = await adapter.explain(
                "SELECT * FROM users", 
                analyze=True, 
                buffers=True
            )
            print(plan.actual_time)
            print(plan.tree)  # ASCII visualization
            
            # Check suggestions
            for suggestion in plan.suggestions:
                print(f"[{suggestion.severity}] {suggestion.title}")
        """
        options = []
        if analyze:
            options.append("ANALYZE")
        if buffers:
            options.append("BUFFERS")
        options.append(f"FORMAT {format.upper()}")
        
        explain_sql = f"EXPLAIN ({', '.join(options)}) {sql}"
        
        rows = await self._fetch(explain_sql, *args)
        
        if format.lower() == "json":
            import json
            raw = json.dumps([dict(r) for r in rows])
            return QueryPlan.from_json(raw, query=sql)
        else:
            raw = "\n".join(str(r[0]) for r in rows)
            return QueryPlan.from_text(raw, query=sql)
    
    # =========================================================================
    # Phase 5.7: Pagination
    # =========================================================================
    
    async def paginate(
        self,
        sql: str,
        *args,
        page_size: int = 20,
        cursor: Optional[str] = None,
        mode: Optional[PaginationMethod] = None,
    ) -> Page:
        """Paginate query results.
        
        Uses smart pagination by default, automatically choosing between
        keyset and offset pagination based on query characteristics.
        
        Args:
            sql: SQL query (should have ORDER BY for keyset pagination)
            *args: Query parameters
            page_size: Number of items per page
            cursor: Cursor from previous page (None for first page)
            mode: Force specific pagination mode
        
        Returns:
            Page with items and next_cursor
        
        Example:
            # First page
            page = await adapter.paginate(
                "SELECT * FROM users ORDER BY id",
                page_size=20,
            )
            
            # Next page
            page = await adapter.paginate(
                "SELECT * FROM users ORDER BY id",
                page_size=20,
                cursor=page.next_cursor,
            )
            
            # Check if more pages
            if page.has_more:
                print(f"More pages available: {page.next_cursor}")
        """
        async def execute(query, params):
            return await self._fetch(query, *params)
        
        async def count(query):
            result = await self._fetchval(f"SELECT COUNT(*) FROM ({query}) AS subq")
            return result or 0
        
        paginator = self._smart_paginator
        if mode == PaginationMethod.KEYSET:
            paginator = KeysetPaginator()
        elif mode == PaginationMethod.OFFSET:
            paginator = OffsetPaginator()
        
        return await paginator.paginate(
            execute_fn=execute,
            count_fn=count,
            query=sql,
            page_size=page_size,
            cursor=cursor,
        )
    
    # =========================================================================
    # Phase 5.7: Prepared Statements
    # =========================================================================
    
    async def prepare(
        self,
        name: str,
        sql: str,
        types: Optional[List[type]] = None,
    ) -> PreparedStatement:
        """Prepare a statement for repeated execution.
        
        Prepared statements are faster for queries run many times
        because parsing and planning happen only once.
        
        Args:
            name: Unique name for the statement
            sql: SQL with $1, $2, etc. placeholders
            types: Optional list of parameter types
        
        Returns:
            PreparedStatement that can be executed multiple times
        
        Example:
            # Prepare once
            stmt = await adapter.prepare(
                "get_user",
                "SELECT * FROM users WHERE id = $1",
                types=[int],
            )
            
            # Execute many times (faster)
            user1 = await stmt.fetchone(1)
            user2 = await stmt.fetchone(2)
            user3 = await stmt.fetchone(3)
        """
        stmt = PreparedStatement(name=name, sql=sql, param_types=types)
        self._prepared_cache.put(stmt)
        return stmt
    
    async def unprepare(self, name: str) -> bool:
        """Remove a prepared statement.
        
        Args:
            name: Name of the prepared statement
        
        Returns:
            True if statement was removed, False if not found
        """
        return self._prepared_cache.remove(name)
    
    async def unprepare_all(self) -> int:
        """Remove all prepared statements.
        
        Returns:
            Number of statements removed
        """
        count = len(self._prepared_cache._cache) if hasattr(self._prepared_cache, '_cache') else 0
        self._prepared_cache.clear()
        return count
    
    def get_prepared_stats(self) -> Dict[str, PreparedStats]:
        """Get statistics for all prepared statements.
        
        Returns:
            Dict mapping statement name to stats
        
        Example:
            stats = adapter.get_prepared_stats()
            for name, stat in stats.items():
                print(f"{name}: {stat.call_count} calls, avg {stat.avg_time_ms:.1f}ms")
        """
        return self._prepared_cache.get_all_stats()
    
    # =========================================================================
    # Phase 5.7: Query Cancellation
    # =========================================================================
    
    def track_query(self, request_id: str) -> QueryTracker:
        """Track queries for a request (for cancellation).
        
        Use as a context manager to track all queries made during a request.
        If the client disconnects, you can cancel all tracked queries.
        
        Args:
            request_id: Unique request identifier
        
        Returns:
            QueryTracker context manager
        
        Example:
            async with adapter.track_query("req_123") as tracker:
                # All queries here are tracked
                users = await User.all()
                orders = await Order.all()
            
            # Later, if client disconnects:
            await adapter.cancel_queries("req_123")
        """
        return QueryTracker(request_id, self._query_registry)
    
    async def cancel_queries(
        self,
        request_id: str,
        reason: CancelReason = CancelReason.CLIENT_DISCONNECT,
    ) -> int:
        """Cancel all queries for a request.
        
        Args:
            request_id: Request ID to cancel queries for
            reason: Why the queries are being cancelled
        
        Returns:
            Number of queries cancelled
        
        Example:
            @app.on_disconnect
            async def handle_disconnect(request):
                count = await adapter.cancel_queries(request.id)
                logger.info(f"Cancelled {count} queries")
        """
        return await self._query_registry.cancel_queries_for_request(
            request_id, reason
        )
    
    async def cancel(
        self,
        query_id: str,
        reason: CancelReason = CancelReason.USER_REQUEST,
    ) -> bool:
        """Cancel a specific query.
        
        Args:
            query_id: ID of the query to cancel
            reason: Why the query is being cancelled
        
        Returns:
            True if cancelled, False if not found
        """
        return await self._query_registry.cancel_query(query_id, reason)
    
    def get_running_queries(self) -> List[RunningQuery]:
        """Get all currently running queries.
        
        Returns:
            List of running queries with metadata
        
        Example:
            for query in adapter.get_running_queries():
                print(f"{query.id}: {query.query[:50]}... ({query.duration_ms}ms)")
        """
        return self._query_registry.get_running_queries()
    
    async def _execute_cancel(self, sql: str, params: tuple) -> Any:
        """Internal method for cancellation executor."""
        return await self._execute(sql, *params)
    
    # =========================================================================
    # Phase 5.3: Reliability - Retry
    # =========================================================================
    
    async def with_retry(
        self,
        fn,
        max_attempts: Optional[int] = None,
    ):
        """Execute a function with automatic retry on failure.
        
        Args:
            fn: Async function to execute
            max_attempts: Override default max attempts
        
        Returns:
            Result of the function
        
        Example:
            result = await adapter.with_retry(
                lambda: adapter.execute("INSERT INTO users ..."),
                max_attempts=5,
            )
        """
        if not self._retry_manager:
            return await fn()
        
        return await self._retry_manager.execute(fn, max_attempts=max_attempts)
    
    def get_retry_stats(self) -> Optional[RetryStats]:
        """Get retry statistics.
        
        Returns:
            RetryStats or None if retry is disabled
        
        Example:
            stats = adapter.get_retry_stats()
            if stats:
                print(f"Retries: {stats.total_retries}")
                print(f"Success rate: {stats.success_rate:.1%}")
        """
        if self._retry_manager:
            return self._retry_manager.get_stats()
        return None
    
    # =========================================================================
    # Phase 5.3: Reliability - Circuit Breaker
    # =========================================================================
    
    @property
    def circuit_state(self) -> Optional[CircuitState]:
        """Get current circuit breaker state.
        
        Returns:
            CircuitState (CLOSED, OPEN, HALF_OPEN) or None if disabled
        
        Example:
            if adapter.circuit_state == CircuitState.OPEN:
                return Response("Database temporarily unavailable", status=503)
        """
        if self._circuit_breaker_registry:
            breaker = self._circuit_breaker_registry.get("default")
            if breaker:
                return breaker.state
        return None
    
    @property
    def is_circuit_open(self) -> bool:
        """Check if circuit breaker is open (blocking requests).
        
        Example:
            if adapter.is_circuit_open:
                return cached_response()
        """
        return self.circuit_state == CircuitState.OPEN
    
    def reset_circuit(self) -> None:
        """Manually reset the circuit breaker to closed state.
        
        Example:
            # After fixing the database issue
            adapter.reset_circuit()
        """
        if self._circuit_breaker_registry:
            breaker = self._circuit_breaker_registry.get("default")
            if breaker:
                breaker.reset()
    
    # =========================================================================
    # Phase 5.3: Reliability - Read Replicas
    # =========================================================================
    
    async def add_replica(self, url: str, weight: int = 1) -> None:
        """Add a read replica for load balancing.
        
        Args:
            url: PostgreSQL connection URL for the replica
            weight: Relative weight for load balancing (higher = more traffic)
        
        Example:
            await adapter.add_replica("postgresql://replica1/mydb")
            await adapter.add_replica("postgresql://replica2/mydb", weight=2)
        """
        if not self._replica_manager:
            self._replica_manager = ReplicaManager(ReplicaConfig())
        
        replica = Replica(url=url, weight=weight)
        await self._replica_manager.add_replica(replica)
    
    async def remove_replica(self, url: str) -> bool:
        """Remove a read replica.
        
        Args:
            url: URL of the replica to remove
        
        Returns:
            True if removed, False if not found
        """
        if self._replica_manager:
            return await self._replica_manager.remove_replica(url)
        return False
    
    def get_replica_stats(self) -> Optional[ReplicaStats]:
        """Get statistics about read replicas.
        
        Returns:
            ReplicaStats or None if no replicas configured
        
        Example:
            stats = adapter.get_replica_stats()
            if stats:
                print(f"Replicas: {stats.replica_count}")
                print(f"Reads routed: {stats.reads_routed}")
        """
        if self._replica_manager:
            return self._replica_manager.get_stats()
        return None
    
    # =========================================================================
    # Phase 5.3: Reliability - Degradation
    # =========================================================================
    
    @property
    def degradation_level(self) -> DegradationLevel:
        """Get current degradation level.
        
        Returns:
            DegradationLevel (NORMAL, DEGRADED, CRITICAL, OFFLINE)
        
        Example:
            if adapter.degradation_level == DegradationLevel.CRITICAL:
                # Serve cached content only
                return cached_response()
        """
        return self._degradation_manager.level
    
    @property
    def is_degraded(self) -> bool:
        """Check if system is in degraded mode.
        
        Example:
            if adapter.is_degraded:
                # Disable non-essential features
                pass
        """
        return self._degradation_manager.level != DegradationLevel.NORMAL
    
    # =========================================================================
    # Phase 5.4: High-Load - Query Coalescing
    # =========================================================================
    
    async def coalesce(self, sql: str, *args) -> Any:
        """Execute query with coalescing (deduplication).
        
        If the same query is already running, wait for its result
        instead of executing again. Great for hot queries.
        
        Args:
            sql: SQL query
            *args: Query parameters
        
        Returns:
            Query result
        
        Example:
            # Even if called 100 times simultaneously,
            # this only executes once
            result = await adapter.coalesce(
                "SELECT * FROM popular_items LIMIT 10"
            )
        """
        if not self._query_coalescer:
            return await self._fetch(sql, *args)
        
        return await self._query_coalescer.execute(
            sql,
            args,
            executor=lambda: self._fetch(sql, *args),
        )
    
    def get_coalesce_stats(self) -> Optional[CoalescingStats]:
        """Get query coalescing statistics.
        
        Returns:
            CoalesceStats or None if coalescing is disabled
        
        Example:
            stats = adapter.get_coalesce_stats()
            if stats:
                print(f"Queries saved: {stats.queries_saved}")
                print(f"Hit rate: {stats.hit_rate:.1%}")
        """
        if self._query_coalescer:
            return self._query_coalescer.get_stats()
        return None
    
    # =========================================================================
    # Phase 5.4: High-Load - Batch Operations
    # =========================================================================
    
    async def batch_insert(
        self,
        table: str,
        rows: List[Dict[str, Any]],
        batch_size: int = 100,
    ) -> int:
        """Insert many rows efficiently in batches.
        
        Args:
            table: Table name
            rows: List of row dictionaries
            batch_size: Rows per batch
        
        Returns:
            Number of rows inserted
        
        Example:
            count = await adapter.batch_insert(
                "users",
                [{"name": "Alice"}, {"name": "Bob"}, ...],
                batch_size=500,
            )
            print(f"Inserted {count} rows")
        """
        if not rows:
            return 0
        
        if self._batch_optimizer:
            return await self._batch_optimizer.batch_insert(
                table, rows, batch_size,
                executor=self._execute,
            )
        
        # Fallback to simple insert
        inserted = 0
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            for row in batch:
                await self.insert(table, row, {})
                inserted += 1
        return inserted
    
    def get_batch_stats(self) -> Optional[BatchStats]:
        """Get batch operation statistics.
        
        Returns:
            BatchStats or None if batching is disabled
        """
        if self._batch_optimizer:
            return self._batch_optimizer.get_stats()
        return None
    
    # =========================================================================
    # Phase 5.4: High-Load - Adaptive Scaling
    # =========================================================================
    
    def get_scaling_stats(self) -> Optional[ScalingStats]:
        """Get adaptive scaling statistics.
        
        Returns:
            ScalingStats or None if adaptive scaling is disabled
        
        Example:
            stats = adapter.get_scaling_stats()
            if stats:
                print(f"Current pool size: {stats.current_size}")
                print(f"Recommended: {stats.recommended_size}")
        """
        if self._adaptive_scaler:
            return self._adaptive_scaler.get_stats()
        return None
    
    # =========================================================================
    # Phase 5.5: Observability - Logging
    # =========================================================================
    
    def get_slow_queries(self, limit: int = 10) -> List[AnalysisResult]:
        """Get recent slow queries.
        
        Args:
            limit: Maximum number of queries to return
        
        Returns:
            List of analysis results for slow queries
        
        Example:
            for query in adapter.get_slow_queries(5):
                print(f"{query.duration_ms}ms: {query.sql[:50]}...")
                for suggestion in query.suggestions:
                    print(f"  - {suggestion}")
        """
        return self._query_analyzer.get_slow_queries(limit)
    
    async def analyze_query(self, sql: str) -> List[QuerySuggestion]:
        """Analyze a query and suggest optimizations.
        
        Args:
            sql: SQL query to analyze
        
        Returns:
            List of query suggestions
        
        Example:
            suggestions = await adapter.analyze_query(
                "SELECT * FROM orders WHERE user_id = 123"
            )
            for s in suggestions:
                print(f"Consider: {s.description}")
        """
        plan = await self.explain(sql, analyze=True)
        return self._query_analyzer.analyze_plan(plan)
    
    # =========================================================================
    # Phase 5.5: Observability - Metrics
    # =========================================================================
    
    def get_metrics(self) -> Optional[Dict[str, Any]]:
        """Get query metrics.
        
        Returns:
            Dict of metrics or None if metrics are disabled
        
        Example:
            metrics = adapter.get_metrics()
            if metrics:
                print(f"Queries/sec: {metrics['queries_per_second']}")
                print(f"Avg latency: {metrics['avg_latency_ms']}ms")
        """
        if self._metrics_collector:
            return self._metrics_collector.get_all_metrics()
        return None
    
    # =========================================================================
    # Phase 5.5: Observability - Health
    # =========================================================================
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the database connection.
        
        Returns:
            Dict with health status details
        
        Example:
            health = await adapter.health_check()
            if health["is_healthy"]:
                return {"status": "ok"}
            else:
                return {"status": "unhealthy", "reason": health["reason"]}
        """
        return await self._pool_monitor.check_health(self._pool)
    
    async def detect_leaks(self) -> Optional[List[LeakInfo]]:
        """Detect connection leaks.
        
        Returns:
            List of LeakInfo if leaks detected, None otherwise
        
        Example:
            leaks = await adapter.detect_leaks()
            if leaks:
                for leak in leaks:
                    logger.warning(f"Leak: connection held for {leak.held_duration_ms}ms")
        """
        return await self._pool_monitor.detect_leaks(self._pool)
    
    # =========================================================================
    # Phase 6: Live Query Integration
    # =========================================================================
    
    def supports_listen_notify(self) -> bool:
        """Check if this adapter supports PostgreSQL LISTEN/NOTIFY.
        
        LISTEN/NOTIFY enables instant database change detection for live queries.
        This is the preferred method for real-time updates.
        
        Returns:
            True - PostgreSQL always supports LISTEN/NOTIFY
        
        Example:
            if adapter.supports_listen_notify():
                # Use instant detection
                detector = PostgresNotifyDetector()
            else:
                # Fall back to polling
                detector = PollingDetector()
        """
        return True
    
    def supports_live_queries(self) -> bool:
        """Check if this adapter supports live queries.
        
        Live queries automatically update when database changes.
        
        Returns:
            True - PostgreSQL supports live queries via LISTEN/NOTIFY
        
        Example:
            if adapter.supports_live_queries():
                users = User.live()  # Real-time updates!
        """
        return True
    
    async def get_listen_connection(self) -> "asyncpg.Connection":
        """Get a dedicated connection for LISTEN/NOTIFY.
        
        This connection is NOT returned to the pool. It stays open for the
        lifetime of the live query subscription because LISTEN requires a
        persistent connection.
        
        Important:
            - The caller is responsible for closing this connection
            - Don't use for regular queries - use the pool instead
            - One connection can LISTEN to multiple channels
        
        Returns:
            A dedicated asyncpg connection
        
        Example:
            conn = await adapter.get_listen_connection()
            try:
                await conn.add_listener("pynext_live_users", callback)
                # Keep connection open...
            finally:
                await conn.close()  # Caller must close!
        
        Raises:
            RuntimeError: If connection cannot be established
        """
        try:
            import asyncpg
            
            return await asyncpg.connect(
                host=self._config.host,
                port=self._config.port,
                user=self._config.user,
                password=self._config.password,
                database=self._config.database,
                ssl=self._config.ssl_context,
                timeout=self._config.connect_timeout,
            )
        except Exception as e:
            logger.error(f"Failed to create LISTEN connection: {e}")
            raise RuntimeError(f"Could not create LISTEN connection: {e}") from e
    
    async def execute_trigger_sql(self, sql: str) -> None:
        """Execute SQL for trigger creation/modification.
        
        Uses retry logic for reliability. Triggers are created for
        LISTEN/NOTIFY-based live query detection.
        
        Args:
            sql: The trigger SQL to execute
        
        Example:
            await adapter.execute_trigger_sql('''
                CREATE OR REPLACE FUNCTION pynext_notify_users()
                RETURNS trigger AS $$ ... $$
            ''')
        
        Raises:
            Exception: If SQL execution fails after retries
        """
        if self._retry_manager:
            async with self._retry_manager.retry("trigger_sql"):
                async with self.connection() as conn:
                    await conn.execute(sql)
        else:
            async with self.connection() as conn:
                await conn.execute(sql)
    
    async def check_trigger_exists(self, table: str, trigger_name: str) -> bool:
        """Check if a trigger exists on a table.
        
        Used to avoid recreating triggers that already exist.
        
        Args:
            table: Table name
            trigger_name: Name of the trigger
        
        Returns:
            True if trigger exists, False otherwise
        
        Example:
            if not await adapter.check_trigger_exists("users", "pynext_live_users_trigger"):
                await adapter.execute_trigger_sql(create_sql)
        """
        result = await self.fetch_one(
            """
            SELECT 1 FROM pg_trigger 
            WHERE tgname = $1 
            AND tgrelid = $2::regclass
            """,
            trigger_name, table
        )
        return result is not None
    
    async def check_function_exists(self, function_name: str) -> bool:
        """Check if a function exists in the database.
        
        Args:
            function_name: Name of the function
        
        Returns:
            True if function exists, False otherwise
        """
        result = await self.fetch_one(
            """
            SELECT 1 FROM pg_proc 
            WHERE proname = $1
            """,
            function_name
        )
        return result is not None
    
    @property
    def live_query_config(self) -> Dict[str, Any]:
        """Get configuration for live queries.
        
        Exposes retry and circuit breaker settings so live query
        components can use consistent resilience patterns.
        
        Returns:
            Dict with retry and circuit breaker configuration
        
        Example:
            config = adapter.live_query_config
            retry_attempts = config["retry_attempts"]
        """
        return {
            "retry_attempts": self._retry_config.max_attempts if self._retry_config else 3,
            "retry_initial_delay": self._retry_config.initial_delay if self._retry_config else 1.0,
            "retry_max_delay": self._retry_config.max_delay if self._retry_config else 30.0,
            "circuit_breaker_enabled": self._circuit_registry is not None,
            "host": self._config.host,
            "port": self._config.port,
            "database": self._config.database,
        }
    
    def __repr__(self) -> str:
        """Return string representation."""
        pool_info = ""
        if self._pool:
            stats = self._pool.get_stats()
            pool_info = f", pool={stats.size}/{self._max_connections}"
            if stats.queue_depth > 0:
                pool_info += f", queue={stats.queue_depth}"
        return f"PostgresAdapter({self._config.host}:{self._config.port}/{self._config.database}{pool_info})"

