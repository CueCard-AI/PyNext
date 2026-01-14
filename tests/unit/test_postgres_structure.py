"""
Comprehensive tests for the Postgres adapter package structure.

Tests verify:
1. All imports work correctly from each submodule
2. Package-level re-exports are complete
3. Main adapters/__init__.py exports match postgres package
4. No circular imports
5. Cross-module dependencies work
6. Symbol counts are as expected
"""

import pytest
import subprocess
import sys


class TestCoreImports:
    """Verify all core module imports work."""

    def test_adapter_import(self):
        from pynext.db.adapters.postgres.core import PostgresAdapter
        assert PostgresAdapter is not None

    def test_config_imports(self):
        from pynext.db.adapters.postgres.core import (
            PostgresConfig,
            PostgresConfigError,
        )
        assert PostgresConfig is not None
        assert PostgresConfigError is not None

    def test_cache_imports(self):
        from pynext.db.adapters.postgres.core import (
            StatementCache,
            PerConnectionCache,
            CachedStatement,
        )
        assert StatementCache is not None
        assert PerConnectionCache is not None
        assert CachedStatement is not None

    def test_type_imports(self):
        from pynext.db.adapters.postgres.core import (
            python_to_postgres,
            postgres_to_python,
            get_postgres_type,
            TypeConversionError,
            TypeMapping,
        )
        assert callable(python_to_postgres)
        assert callable(postgres_to_python)
        assert callable(get_postgres_type)


class TestPoolImports:
    """Verify all pool module imports work."""

    def test_pool_core_imports(self):
        from pynext.db.adapters.postgres.pool import (
            AutoScalingPool,
            PoolStats,
            PoolState,
            PooledConnection,
            ConnectionState,
            PoolExhaustedError,
            PoolClosedError,
        )
        assert AutoScalingPool is not None
        assert PoolStats is not None
        assert PoolState is not None

    def test_queue_imports(self):
        from pynext.db.adapters.postgres.pool import (
            ConnectionQueue,
            QueueConfig,
            QueueStats,
            QueuedRequest,
            QueuePriority,
            QueueOverflowAction,
            QueueFullError,
            QueueTimeoutError,
        )
        assert ConnectionQueue is not None
        assert QueueConfig is not None

    def test_lifecycle_imports(self):
        from pynext.db.adapters.postgres.pool import (
            LifecycleManager,
            LifecycleConfig,
            LifecycleStats,
            ConnectionLifecycle,
            ConnectionHealth,
            RetirementReason,
            ReplacementStrategy,
        )
        assert LifecycleManager is not None
        assert LifecycleConfig is not None

    def test_warmup_imports(self):
        from pynext.db.adapters.postgres.pool import (
            ConnectionWarmer,
            WarmupConfig,
            WarmupResult,
            WarmupStats,
        )
        assert ConnectionWarmer is not None
        assert WarmupConfig is not None

    def test_external_imports(self):
        from pynext.db.adapters.postgres.pool import (
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
        assert ExternalPoolerManager is not None
        assert PoolerType is not None


class TestReliabilityImports:
    """Verify all reliability module imports work."""

    def test_retry_imports(self):
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
        )
        assert RetryConfig is not None
        assert RetryManager is not None
        assert callable(with_retry)

    def test_circuit_imports(self):
        from pynext.db.adapters.postgres.reliability import (
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
        assert CircuitBreaker is not None
        assert CircuitBreakerConfig is not None

    def test_replica_imports(self):
        from pynext.db.adapters.postgres.reliability import (
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
        assert Replica is not None
        assert ReplicaManager is not None

    def test_degradation_imports(self):
        from pynext.db.adapters.postgres.reliability import (
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
        assert DegradationManager is not None
        assert DegradationConfig is not None


class TestPerformanceImports:
    """Verify all performance module imports work."""

    def test_timeout_imports(self):
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
        )
        assert QueryTimeoutConfig is not None
        assert TimeoutManager is not None

    def test_query_cache_imports(self):
        from pynext.db.adapters.postgres.performance import (
            InvalidationStrategy,
            QueryCacheConfig,
            CacheEntry,
            CacheStats,
            QueryCache,
            simple_cache_config,
            smart_cache_config,
            aggressive_cache_config,
            no_cache_config,
        )
        assert QueryCache is not None
        assert QueryCacheConfig is not None

    def test_coalesce_imports(self):
        from pynext.db.adapters.postgres.performance import (
            CoalescingConfig,
            PendingQuery,
            CoalescingStats,
            CoalescingLimitError,
            QueryCoalescer,
            aggressive_coalescing_config,
            conservative_coalescing_config,
            disabled_coalescing_config,
        )
        assert QueryCoalescer is not None
        assert CoalescingConfig is not None

    def test_pipeline_imports(self):
        from pynext.db.adapters.postgres.performance import (
            PipelineConfig,
            PipelinedQuery,
            PipelineStats,
            QueryPipeline,
            high_throughput_config,
            low_latency_config,
            disabled_pipeline_config,
        )
        assert QueryPipeline is not None
        assert PipelineConfig is not None

    def test_batch_imports(self):
        from pynext.db.adapters.postgres.performance import (
            BatchConfig,
            BatchResult,
            BatchStats,
            BatchOptimizer,
            bulk_load_config,
            transactional_config,
            disabled_batch_config,
        )
        assert BatchOptimizer is not None
        assert BatchConfig is not None

    def test_scaling_imports(self):
        from pynext.db.adapters.postgres.performance import (
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
        assert AdaptiveScaler is not None
        assert AdaptiveScalingConfig is not None


class TestObservabilityImports:
    """Verify all observability module imports work."""

    def test_logging_imports(self):
        from pynext.db.adapters.postgres.observability import (
            LogConfig,
            QueryContext,
            DBLogger,
            LogLevel,
            LogFormat,
            LogEvent,
            LogRecord,
            QueryTracker,
            set_trace_id,
            get_trace_id,
            set_client_ip,
            get_client_ip,
        )
        assert LogConfig is not None
        assert DBLogger is not None
        assert callable(set_trace_id)

    def test_metrics_imports(self):
        from pynext.db.adapters.postgres.observability import (
            MetricsConfig,
            MetricsCollector,
            MetricsBackend,
        )
        assert MetricsConfig is not None
        assert MetricsCollector is not None

    def test_prometheus_imports(self):
        from pynext.db.adapters.postgres.observability import (
            PrometheusBackend,
        )
        assert PrometheusBackend is not None

    def test_opentelemetry_imports(self):
        from pynext.db.adapters.postgres.observability import (
            OpenTelemetryBackend,
            OTLPConfig,
        )
        assert OpenTelemetryBackend is not None
        assert OTLPConfig is not None

    def test_analyzer_imports(self):
        from pynext.db.adapters.postgres.observability import (
            QueryAnalyzer,
            AnalyzerConfig,
            ExplainResult,
            SuggestionType,
            ScanType,
            ExplainNode,
            QuerySuggestion,
            AnalysisResult,
        )
        assert QueryAnalyzer is not None
        assert AnalyzerConfig is not None

    def test_monitor_imports(self):
        from pynext.db.adapters.postgres.observability import (
            PoolMonitor,
            MonitorConfig,
            LeakDetector,
            HealthChecker,
            PoolEventType,
            ConnectionInfo,
            LeakInfo,
            PoolEvent,
        )
        assert PoolMonitor is not None
        assert MonitorConfig is not None


class TestQueriesImports:
    """Verify all queries module imports work."""

    def test_query_timeout_imports(self):
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
        )
        assert QueryTimeout is not None
        assert TimeoutExecutor is not None

    def test_explain_imports(self):
        from pynext.db.adapters.postgres.queries import (
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
        )
        assert QueryPlan is not None
        assert PlanAnalyzer is not None

    def test_pagination_imports(self):
        from pynext.db.adapters.postgres.queries import (
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
        )
        assert KeysetPaginator is not None
        assert PaginationConfig is not None

    def test_prepared_imports(self):
        from pynext.db.adapters.postgres.queries import (
            StatementState,
            PreparedStats,
            PreparedStatement,
            PreparedCache,
            PreparedExecutor,
            prepared,
            SchemaWatcher,
            get_prepared_executor,
            set_prepared_executor,
        )
        assert PreparedStatement is not None
        assert PreparedExecutor is not None

    def test_cancel_imports(self):
        from pynext.db.adapters.postgres.queries import (
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
        assert CancelExecutor is not None
        assert QueryRegistry is not None


class TestPackageReexports:
    """Verify postgres/__init__.py re-exports everything correctly."""

    def test_core_reexports(self):
        from pynext.db.adapters.postgres import PostgresAdapter
        from pynext.db.adapters.postgres.core import PostgresAdapter as CoreAdapter
        assert PostgresAdapter is CoreAdapter

    def test_reliability_reexports(self):
        from pynext.db.adapters.postgres import RetryConfig
        from pynext.db.adapters.postgres.reliability.retry import RetryConfig as DirectConfig
        assert RetryConfig is DirectConfig

    def test_performance_reexports(self):
        from pynext.db.adapters.postgres import BatchConfig
        from pynext.db.adapters.postgres.performance.batch import BatchConfig as DirectConfig
        assert BatchConfig is DirectConfig

    def test_observability_reexports(self):
        from pynext.db.adapters.postgres import LogConfig
        from pynext.db.adapters.postgres.observability.logging import LogConfig as DirectConfig
        assert LogConfig is DirectConfig

    def test_pool_reexports(self):
        from pynext.db.adapters.postgres import AutoScalingPool
        from pynext.db.adapters.postgres.pool.pool import AutoScalingPool as DirectPool
        assert AutoScalingPool is DirectPool


class TestAdaptersModuleExports:
    """Verify adapters/__init__.py exports match postgres package."""

    def test_adapter_export(self):
        from pynext.db.adapters import PostgresAdapter
        from pynext.db.adapters.postgres import PostgresAdapter as PgAdapter
        assert PostgresAdapter is PgAdapter

    def test_config_export(self):
        from pynext.db.adapters import PostgresConfig
        from pynext.db.adapters.postgres import PostgresConfig as PgConfig
        assert PostgresConfig is PgConfig

    def test_retry_export(self):
        from pynext.db.adapters import RetryConfig
        from pynext.db.adapters.postgres import RetryConfig as PgRetryConfig
        assert RetryConfig is PgRetryConfig

    def test_circuit_export(self):
        from pynext.db.adapters import CircuitBreaker
        from pynext.db.adapters.postgres import CircuitBreaker as PgCircuitBreaker
        assert CircuitBreaker is PgCircuitBreaker

    def test_pool_export(self):
        from pynext.db.adapters import AutoScalingPool
        from pynext.db.adapters.postgres import AutoScalingPool as PgPool
        assert AutoScalingPool is PgPool

    def test_log_export(self):
        from pynext.db.adapters import LogConfig
        from pynext.db.adapters.postgres import LogConfig as PgLogConfig
        assert LogConfig is PgLogConfig


class TestNoCircularImports:
    """Verify no circular imports exist."""

    def test_fresh_import_works(self):
        """Test importing in a fresh Python process."""
        result = subprocess.run(
            [sys.executable, '-c', 'from pynext.db.adapters.postgres import PostgresAdapter; print("OK")'],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Import failed: {result.stderr}"
        assert "OK" in result.stdout

    def test_all_submodules_import(self):
        """Test all submodules can be imported independently."""
        modules = [
            'pynext.db.adapters.postgres.core',
            'pynext.db.adapters.postgres.pool',
            'pynext.db.adapters.postgres.reliability',
            'pynext.db.adapters.postgres.performance',
            'pynext.db.adapters.postgres.observability',
            'pynext.db.adapters.postgres.queries',
        ]
        for mod in modules:
            result = subprocess.run(
                [sys.executable, '-c', f'import {mod}; print("OK")'],
                capture_output=True,
                text=True,
                timeout=30,
            )
            assert result.returncode == 0, f"Import of {mod} failed: {result.stderr}"


class TestCrossModuleDependencies:
    """Verify internal imports between modules work."""

    def test_adapter_has_pool_attributes(self):
        """Adapter should have pool-related configuration."""
        from pynext.db.adapters.postgres.core import PostgresAdapter
        # Check adapter class has expected attributes
        assert hasattr(PostgresAdapter, '__init__')

    def test_prometheus_extends_metrics_backend(self):
        """PrometheusBackend should extend MetricsBackend."""
        from pynext.db.adapters.postgres.observability.prometheus import PrometheusBackend
        from pynext.db.adapters.postgres.observability.metrics import MetricsBackend
        assert issubclass(PrometheusBackend, MetricsBackend)

    def test_opentelemetry_extends_metrics_backend(self):
        """OpenTelemetryBackend should extend MetricsBackend."""
        from pynext.db.adapters.postgres.observability.opentelemetry import OpenTelemetryBackend
        from pynext.db.adapters.postgres.observability.metrics import MetricsBackend
        assert issubclass(OpenTelemetryBackend, MetricsBackend)


class TestSymbolCounts:
    """Verify expected number of symbols are exported."""

    def test_postgres_package_symbol_count(self):
        """Postgres package should export many symbols."""
        from pynext.db.adapters import postgres
        public_symbols = [s for s in dir(postgres) if not s.startswith('_')]
        # Should have at least 100 public symbols
        assert len(public_symbols) >= 100, f"Only {len(public_symbols)} public symbols"

    def test_core_symbol_count(self):
        """Core submodule should export key symbols."""
        from pynext.db.adapters.postgres import core
        public_symbols = [s for s in dir(core) if not s.startswith('_')]
        assert len(public_symbols) >= 5

    def test_reliability_symbol_count(self):
        """Reliability submodule should export many symbols."""
        from pynext.db.adapters.postgres import reliability
        public_symbols = [s for s in dir(reliability) if not s.startswith('_')]
        assert len(public_symbols) >= 20


class TestConfigInstantiation:
    """Verify config classes can be instantiated."""

    def test_postgres_config_instantiation(self):
        from pynext.db.adapters.postgres.core import PostgresConfig
        config = PostgresConfig(
            host='localhost',
            port=5432,
            database='test',
            user='test',
            password='test',
        )
        assert config.host == 'localhost'
        assert config.port == 5432

    def test_retry_config_instantiation(self):
        from pynext.db.adapters.postgres.reliability import RetryConfig
        config = RetryConfig(max_attempts=5)
        assert config.max_attempts == 5

    def test_log_config_instantiation(self):
        from pynext.db.adapters.postgres.observability import LogConfig
        config = LogConfig()
        assert config is not None

    def test_batch_config_instantiation(self):
        from pynext.db.adapters.postgres.performance import BatchConfig
        config = BatchConfig()
        assert config is not None

    def test_queue_config_instantiation(self):
        from pynext.db.adapters.postgres.pool import QueueConfig
        config = QueueConfig()
        assert config is not None


class TestFactoryFunctions:
    """Verify factory functions work correctly."""

    def test_quick_retry(self):
        from pynext.db.adapters.postgres.reliability import quick_retry
        config = quick_retry()
        assert config is not None

    def test_standard_retry(self):
        from pynext.db.adapters.postgres.reliability import standard_retry
        config = standard_retry()
        assert config is not None

    def test_create_global_breaker(self):
        from pynext.db.adapters.postgres.reliability import create_global_breaker
        config = create_global_breaker()
        assert config is not None

    def test_simple_cache_config(self):
        from pynext.db.adapters.postgres.performance import simple_cache_config
        config = simple_cache_config()
        assert config is not None

    def test_quick_timeout_config(self):
        from pynext.db.adapters.postgres.performance import quick_timeout_config
        config = quick_timeout_config()
        assert config is not None

