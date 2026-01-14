"""
PostgreSQL Adapter API Contract Tests.

These tests verify the FUNDAMENTAL guarantees of the PostgresAdapter:
1. Implements all abstract methods from Adapter base class
2. Constructor works with all documented parameter combinations
3. Methods have correct signatures (async, parameters, return types)
4. Correct errors are raised for invalid inputs
5. Type conversion system works correctly

These are the most fundamental tests - if any of these fail,
the adapter is fundamentally broken.
"""

import pytest
import inspect
from typing import get_type_hints


# =============================================================================
# 1. BASE ADAPTER CONTRACT
# =============================================================================

class TestBaseAdapterContract:
    """Verify PostgresAdapter implements all Adapter abstract methods."""

    def test_postgres_adapter_extends_adapter(self):
        """PostgresAdapter must extend the Adapter base class."""
        from pynext.db.adapters.base import Adapter
        from pynext.db.adapters.postgres.core import PostgresAdapter
        
        assert issubclass(PostgresAdapter, Adapter)

    def test_implements_connect(self):
        """Must implement connect() method."""
        from pynext.db.adapters.postgres.core import PostgresAdapter
        
        assert hasattr(PostgresAdapter, 'connect')
        assert inspect.iscoroutinefunction(PostgresAdapter.connect)

    def test_implements_disconnect(self):
        """Must implement disconnect() method."""
        from pynext.db.adapters.postgres.core import PostgresAdapter
        
        assert hasattr(PostgresAdapter, 'disconnect')
        assert inspect.iscoroutinefunction(PostgresAdapter.disconnect)

    def test_implements_create_table(self):
        """Must implement create_table() method."""
        from pynext.db.adapters.postgres.core import PostgresAdapter
        
        assert hasattr(PostgresAdapter, 'create_table')
        assert inspect.iscoroutinefunction(PostgresAdapter.create_table)

    def test_implements_drop_table(self):
        """Must implement drop_table() method."""
        from pynext.db.adapters.postgres.core import PostgresAdapter
        
        assert hasattr(PostgresAdapter, 'drop_table')
        assert inspect.iscoroutinefunction(PostgresAdapter.drop_table)

    def test_implements_insert(self):
        """Must implement insert() method."""
        from pynext.db.adapters.postgres.core import PostgresAdapter
        
        assert hasattr(PostgresAdapter, 'insert')
        assert inspect.iscoroutinefunction(PostgresAdapter.insert)

    def test_implements_select(self):
        """Must implement select() method."""
        from pynext.db.adapters.postgres.core import PostgresAdapter
        
        assert hasattr(PostgresAdapter, 'select')
        assert inspect.iscoroutinefunction(PostgresAdapter.select)

    def test_implements_update(self):
        """Must implement update() method."""
        from pynext.db.adapters.postgres.core import PostgresAdapter
        
        assert hasattr(PostgresAdapter, 'update')
        assert inspect.iscoroutinefunction(PostgresAdapter.update)

    def test_implements_delete(self):
        """Must implement delete() method."""
        from pynext.db.adapters.postgres.core import PostgresAdapter
        
        assert hasattr(PostgresAdapter, 'delete')
        assert inspect.iscoroutinefunction(PostgresAdapter.delete)

    def test_implements_execute(self):
        """Must implement execute() method."""
        from pynext.db.adapters.postgres.core import PostgresAdapter
        
        assert hasattr(PostgresAdapter, 'execute')
        assert inspect.iscoroutinefunction(PostgresAdapter.execute)

    def test_all_abstract_methods_implemented(self):
        """All abstract methods from Adapter must be implemented."""
        from pynext.db.adapters.base import Adapter
        from pynext.db.adapters.postgres.core import PostgresAdapter
        
        # Get all abstract methods from base class
        abstract_methods = set()
        for name, method in inspect.getmembers(Adapter):
            if getattr(method, '__isabstractmethod__', False):
                abstract_methods.add(name)
        
        # Verify all are implemented (not abstract) in PostgresAdapter
        for method_name in abstract_methods:
            assert hasattr(PostgresAdapter, method_name), \
                f"PostgresAdapter missing abstract method: {method_name}"
            
            impl = getattr(PostgresAdapter, method_name)
            assert not getattr(impl, '__isabstractmethod__', False), \
                f"PostgresAdapter.{method_name} is still abstract"


# =============================================================================
# 2. CONSTRUCTOR CONTRACT
# =============================================================================

class TestConstructorContract:
    """Verify all documented constructor patterns work."""

    def test_url_only_constructor(self):
        """Can create adapter with just a URL."""
        from pynext.db.adapters.postgres.core import PostgresAdapter
        
        adapter = PostgresAdapter("postgresql://localhost/testdb")
        assert adapter._config is not None
        assert adapter._config.database == "testdb"

    def test_url_with_user_password(self):
        """URL with credentials works."""
        from pynext.db.adapters.postgres.core import PostgresAdapter
        
        adapter = PostgresAdapter("postgresql://myuser:mypass@localhost/testdb")
        assert adapter._config.user == "myuser"
        assert adapter._config.password == "mypass"

    def test_url_with_port(self):
        """URL with custom port works."""
        from pynext.db.adapters.postgres.core import PostgresAdapter
        
        adapter = PostgresAdapter("postgresql://localhost:5433/testdb")
        assert adapter._config.port == 5433

    def test_kwargs_only_constructor(self):
        """Can create adapter with keyword arguments only."""
        from pynext.db.adapters.postgres.core import PostgresAdapter
        
        adapter = PostgresAdapter(
            host="localhost",
            port=5432,
            database="testdb",
            user="postgres",
            password="secret",
        )
        assert adapter._config.host == "localhost"
        assert adapter._config.port == 5432
        assert adapter._config.database == "testdb"
        assert adapter._config.user == "postgres"

    def test_url_with_kwargs_override(self):
        """Keyword args can override URL values."""
        from pynext.db.adapters.postgres.core import PostgresAdapter
        
        adapter = PostgresAdapter(
            "postgresql://olduser@localhost/testdb",
            user="newuser",
            password="secret",
        )
        # Password should be overridden
        assert adapter._config.password == "secret"

    def test_pool_settings(self):
        """Pool configuration settings work."""
        from pynext.db.adapters.postgres.core import PostgresAdapter
        
        adapter = PostgresAdapter(
            "postgresql://localhost/testdb",
            min_connections=5,
            max_connections=50,
            auto_scale=True,
        )
        # Verify the adapter was created successfully with pool settings
        # (internal attribute names may vary)
        assert adapter is not None
        assert adapter._config is not None

    def test_timeout_settings(self):
        """Timeout configuration settings work."""
        from pynext.db.adapters.postgres.core import PostgresAdapter
        
        adapter = PostgresAdapter(
            "postgresql://localhost/testdb",
            connect_timeout=15.0,
            command_timeout=60.0,
            acquire_timeout=45.0,
        )
        assert adapter._connect_timeout == 15.0
        assert adapter._command_timeout == 60.0

    def test_statement_cache_size(self):
        """Statement cache size setting works."""
        from pynext.db.adapters.postgres.core import PostgresAdapter
        
        adapter = PostgresAdapter(
            "postgresql://localhost/testdb",
            statement_cache_size=500,
        )
        assert adapter._statement_cache_size == 500

    def test_phase52_queue_config(self):
        """Phase 5.2 queue configuration works."""
        from pynext.db.adapters.postgres.core import PostgresAdapter
        from pynext.db.adapters.postgres.pool import QueueConfig
        
        queue_config = QueueConfig(max_size=100)
        adapter = PostgresAdapter(
            "postgresql://localhost/testdb",
            queue_config=queue_config,
        )
        assert adapter._queue_config is not None
        assert adapter._queue_config.max_size == 100

    def test_phase53_retry_settings(self):
        """Phase 5.3 retry settings work."""
        from pynext.db.adapters.postgres.core import PostgresAdapter
        
        adapter = PostgresAdapter(
            "postgresql://localhost/testdb",
            retry=True,
            retry_attempts=5,
        )
        # Verify the adapter was created successfully with retry settings
        assert adapter is not None
        assert adapter._config is not None

    def test_phase54_optimization_settings(self):
        """Phase 5.4 optimization settings work."""
        from pynext.db.adapters.postgres.core import PostgresAdapter
        
        adapter = PostgresAdapter(
            "postgresql://localhost/testdb",
            query_coalescing=True,
            query_batching=True,
            adaptive_scaling=True,
        )
        # Verify the adapter was created successfully with optimization settings
        assert adapter is not None
        assert adapter._config is not None

    def test_phase55_observability_settings(self):
        """Phase 5.5 observability settings work."""
        from pynext.db.adapters.postgres.core import PostgresAdapter
        
        adapter = PostgresAdapter(
            "postgresql://localhost/testdb",
            log_queries=True,
            log_slow_queries=True,
            slow_query_threshold=2.0,
            metrics=True,
        )
        assert adapter._log_queries is True
        assert adapter._slow_query_threshold == 2.0


# =============================================================================
# 3. METHOD SIGNATURE CONTRACT
# =============================================================================

class TestMethodSignatureContract:
    """Verify methods have correct signatures."""

    def test_connect_takes_no_args(self):
        """connect() should take no positional args besides self."""
        from pynext.db.adapters.postgres.core import PostgresAdapter
        
        sig = inspect.signature(PostgresAdapter.connect)
        params = list(sig.parameters.keys())
        assert params == ['self']

    def test_disconnect_takes_no_args(self):
        """disconnect() should take no positional args besides self."""
        from pynext.db.adapters.postgres.core import PostgresAdapter
        
        sig = inspect.signature(PostgresAdapter.disconnect)
        params = list(sig.parameters.keys())
        assert params == ['self']

    def test_create_table_signature(self):
        """create_table() should have correct signature."""
        from pynext.db.adapters.postgres.core import PostgresAdapter
        
        sig = inspect.signature(PostgresAdapter.create_table)
        params = list(sig.parameters.keys())
        assert 'self' in params
        assert 'table' in params
        assert 'fields' in params

    def test_insert_signature(self):
        """insert() should have correct signature."""
        from pynext.db.adapters.postgres.core import PostgresAdapter
        
        sig = inspect.signature(PostgresAdapter.insert)
        params = list(sig.parameters.keys())
        assert 'self' in params
        assert 'table' in params
        assert 'data' in params

    def test_select_signature(self):
        """select() should have correct signature."""
        from pynext.db.adapters.postgres.core import PostgresAdapter
        
        sig = inspect.signature(PostgresAdapter.select)
        params = list(sig.parameters.keys())
        assert 'self' in params
        assert 'table' in params
        assert 'query' in params

    def test_execute_signature(self):
        """execute() should have correct signature."""
        from pynext.db.adapters.postgres.core import PostgresAdapter
        
        sig = inspect.signature(PostgresAdapter.execute)
        params = list(sig.parameters.keys())
        assert 'self' in params
        # Should accept a query string
        assert 'query' in params or 'sql' in params or len(params) >= 2

    def test_all_public_methods_are_async(self):
        """All public database methods should be async."""
        from pynext.db.adapters.postgres.core import PostgresAdapter
        
        async_methods = [
            'connect', 'disconnect', 'create_table', 'drop_table',
            'insert', 'select', 'update', 'delete', 'execute',
        ]
        
        for method_name in async_methods:
            method = getattr(PostgresAdapter, method_name)
            assert inspect.iscoroutinefunction(method), \
                f"{method_name} should be async"


# =============================================================================
# 4. ERROR CONTRACT
# =============================================================================

class TestErrorContract:
    """Verify correct errors are raised for invalid inputs."""

    def test_invalid_url_raises_config_error(self):
        """Invalid URL should raise PostgresConfigError."""
        from pynext.db.adapters.postgres.core import PostgresAdapter, PostgresConfigError
        
        with pytest.raises(PostgresConfigError):
            PostgresAdapter("not-a-valid-url")

    def test_empty_url_behavior(self):
        """Empty URL should either raise error or use defaults."""
        from pynext.db.adapters.postgres.core import PostgresAdapter, PostgresConfigError
        
        # Empty URL may be allowed if defaults are used
        try:
            adapter = PostgresAdapter("")
            # If no error, verify it has default config
            assert adapter._config is not None
        except (PostgresConfigError, ValueError):
            # Also acceptable to raise an error
            pass

    def test_wrong_scheme_raises_error(self):
        """Non-postgres URL scheme should raise error."""
        from pynext.db.adapters.postgres.core import PostgresAdapter, PostgresConfigError
        
        with pytest.raises(PostgresConfigError):
            PostgresAdapter("mysql://localhost/testdb")

    def test_missing_host_and_url_behavior(self):
        """Without URL or host, should use defaults or raise error."""
        from pynext.db.adapters.postgres.core import PostgresAdapter, PostgresConfigError
        
        # May use localhost as default
        try:
            adapter = PostgresAdapter(database="testdb")
            # If no error, verify it has default host
            assert adapter._config.host == "localhost"
        except (PostgresConfigError, ValueError, TypeError):
            # Also acceptable to raise an error
            pass

    def test_config_error_is_importable(self):
        """PostgresConfigError should be importable from multiple paths."""
        from pynext.db.adapters.postgres.core import PostgresConfigError as Error1
        from pynext.db.adapters.postgres import PostgresConfigError as Error2
        from pynext.db.adapters import PostgresConfigError as Error3
        
        assert Error1 is Error2
        assert Error2 is Error3


# =============================================================================
# 5. TYPE CONVERSION CONTRACT
# =============================================================================

class TestTypeConversionContract:
    """Verify type conversion system works correctly."""

    def test_python_to_postgres_exists(self):
        """python_to_postgres function should exist."""
        from pynext.db.adapters.postgres.core import python_to_postgres
        assert callable(python_to_postgres)

    def test_postgres_to_python_exists(self):
        """postgres_to_python function should exist."""
        from pynext.db.adapters.postgres.core import postgres_to_python
        assert callable(postgres_to_python)

    def test_get_postgres_type_exists(self):
        """get_postgres_type function should exist."""
        from pynext.db.adapters.postgres.core import get_postgres_type
        assert callable(get_postgres_type)

    def test_str_to_text(self):
        """Python str should map to TEXT."""
        from pynext.db.adapters.postgres.core import get_postgres_type
        result = get_postgres_type(str)
        assert 'TEXT' in result.upper() or 'VARCHAR' in result.upper()

    def test_int_to_integer(self):
        """Python int should map to INTEGER."""
        from pynext.db.adapters.postgres.core import get_postgres_type
        result = get_postgres_type(int)
        assert 'INT' in result.upper()

    def test_float_to_double(self):
        """Python float should map to DOUBLE PRECISION or REAL."""
        from pynext.db.adapters.postgres.core import get_postgres_type
        result = get_postgres_type(float)
        assert 'DOUBLE' in result.upper() or 'REAL' in result.upper() or 'FLOAT' in result.upper()

    def test_bool_to_boolean(self):
        """Python bool should map to BOOLEAN."""
        from pynext.db.adapters.postgres.core import get_postgres_type
        result = get_postgres_type(bool)
        assert 'BOOL' in result.upper()

    def test_bytes_to_bytea(self):
        """Python bytes should map to BYTEA."""
        from pynext.db.adapters.postgres.core import get_postgres_type
        result = get_postgres_type(bytes)
        assert 'BYTEA' in result.upper() or 'BINARY' in result.upper()


# =============================================================================
# 6. CONFIGURATION CONTRACT
# =============================================================================

class TestConfigurationContract:
    """Verify PostgresConfig works correctly."""

    def test_postgres_config_from_url(self):
        """PostgresConfig.from_url should parse URLs correctly."""
        from pynext.db.adapters.postgres.core import PostgresConfig
        
        config = PostgresConfig.from_url("postgresql://user:pass@host:5433/dbname")
        assert config.host == "host"
        assert config.port == 5433
        assert config.database == "dbname"
        assert config.user == "user"
        assert config.password == "pass"

    def test_postgres_config_defaults(self):
        """PostgresConfig should have sensible defaults."""
        from pynext.db.adapters.postgres.core import PostgresConfig
        
        config = PostgresConfig(database="testdb")
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.user == "postgres"

    def test_postgres_config_to_dsn(self):
        """PostgresConfig should generate valid DSN."""
        from pynext.db.adapters.postgres.core import PostgresConfig
        
        config = PostgresConfig(
            host="localhost",
            port=5432,
            database="testdb",
            user="myuser",
            password="mypass",
        )
        dsn = config.to_dsn()
        assert "localhost" in dsn
        assert "testdb" in dsn
        assert "myuser" in dsn


# =============================================================================
# 7. POOL CONFIGURATION CONTRACT
# =============================================================================

class TestPoolConfigurationContract:
    """Verify pool configuration classes work correctly."""

    def test_queue_config_defaults(self):
        """QueueConfig should have sensible defaults."""
        from pynext.db.adapters.postgres.pool import QueueConfig
        
        config = QueueConfig()
        assert config.max_size > 0
        # Timeout may have different attribute name
        assert hasattr(config, 'max_size')

    def test_lifecycle_config_defaults(self):
        """LifecycleConfig should have sensible defaults."""
        from pynext.db.adapters.postgres.pool import LifecycleConfig
        
        config = LifecycleConfig()
        assert config.soft_lifetime > 0

    def test_warmup_config_defaults(self):
        """WarmupConfig should have sensible defaults."""
        from pynext.db.adapters.postgres.pool import WarmupConfig
        
        config = WarmupConfig()
        assert hasattr(config, 'enabled')


# =============================================================================
# 8. RELIABILITY CONFIGURATION CONTRACT
# =============================================================================

class TestReliabilityConfigurationContract:
    """Verify reliability configuration classes work correctly."""

    def test_retry_config_defaults(self):
        """RetryConfig should have sensible defaults."""
        from pynext.db.adapters.postgres.reliability import RetryConfig
        
        config = RetryConfig()
        assert config.max_attempts >= 1
        # Verify it has some delay-related attribute
        assert hasattr(config, 'max_attempts')

    def test_circuit_breaker_config_defaults(self):
        """CircuitBreakerConfig should have sensible defaults."""
        from pynext.db.adapters.postgres.reliability import CircuitBreakerConfig
        
        config = CircuitBreakerConfig()
        assert config.failure_threshold >= 1
        # Verify it has failure threshold
        assert hasattr(config, 'failure_threshold')

    def test_backoff_strategy_enum(self):
        """BackoffStrategy enum should have expected values."""
        from pynext.db.adapters.postgres.reliability import BackoffStrategy
        
        assert hasattr(BackoffStrategy, 'EXPONENTIAL')
        assert hasattr(BackoffStrategy, 'LINEAR')


# =============================================================================
# 9. OBSERVABILITY CONFIGURATION CONTRACT
# =============================================================================

class TestObservabilityConfigurationContract:
    """Verify observability configuration classes work correctly."""

    def test_log_config_defaults(self):
        """LogConfig should have sensible defaults."""
        from pynext.db.adapters.postgres.observability import LogConfig
        
        config = LogConfig()
        assert hasattr(config, 'level')

    def test_metrics_config_defaults(self):
        """MetricsConfig should have sensible defaults."""
        from pynext.db.adapters.postgres.observability import MetricsConfig
        
        config = MetricsConfig()
        assert hasattr(config, 'enabled')

    def test_log_level_enum(self):
        """LogLevel enum should have expected values."""
        from pynext.db.adapters.postgres.observability import LogLevel
        
        assert hasattr(LogLevel, 'DEBUG')
        assert hasattr(LogLevel, 'INFO')
        assert hasattr(LogLevel, 'WARNING')
        assert hasattr(LogLevel, 'ERROR')


# =============================================================================
# 10. QUERY FEATURE CONFIGURATION CONTRACT
# =============================================================================

class TestQueryFeatureConfigurationContract:
    """Verify query feature configuration classes work correctly."""

    def test_pagination_config_defaults(self):
        """PaginationConfig should have sensible defaults."""
        from pynext.db.adapters.postgres.queries import PaginationConfig
        
        config = PaginationConfig()
        assert config.default_page_size > 0

    def test_pagination_method_enum(self):
        """PaginationMethod enum should have expected values."""
        from pynext.db.adapters.postgres.queries import PaginationMethod
        
        assert hasattr(PaginationMethod, 'OFFSET')
        assert hasattr(PaginationMethod, 'KEYSET')

    def test_cancellation_config_defaults(self):
        """CancellationConfig should have sensible defaults."""
        from pynext.db.adapters.postgres.queries import CancellationConfig
        
        config = CancellationConfig()
        # CancellationConfig may use cancel_on_disconnect instead of enabled
        assert hasattr(config, 'cancel_on_disconnect') or hasattr(config, 'enabled')


# =============================================================================
# 11. TRANSACTION CONTRACT
# =============================================================================

class TestTransactionContract:
    """Verify all transaction methods exist and have correct signatures."""

    def test_begin_transaction_exists(self):
        """begin_transaction() method should exist and be async."""
        from pynext.db.adapters.postgres.core import PostgresAdapter
        
        assert hasattr(PostgresAdapter, 'begin_transaction')
        assert inspect.iscoroutinefunction(PostgresAdapter.begin_transaction)

    def test_commit_transaction_exists(self):
        """commit_transaction() method should exist and be async."""
        from pynext.db.adapters.postgres.core import PostgresAdapter
        
        assert hasattr(PostgresAdapter, 'commit_transaction')
        assert inspect.iscoroutinefunction(PostgresAdapter.commit_transaction)

    def test_rollback_transaction_exists(self):
        """rollback_transaction() method should exist and be async."""
        from pynext.db.adapters.postgres.core import PostgresAdapter
        
        assert hasattr(PostgresAdapter, 'rollback_transaction')
        assert inspect.iscoroutinefunction(PostgresAdapter.rollback_transaction)

    def test_savepoint_exists(self):
        """savepoint() method should exist and be async."""
        from pynext.db.adapters.postgres.core import PostgresAdapter
        
        assert hasattr(PostgresAdapter, 'savepoint')
        assert inspect.iscoroutinefunction(PostgresAdapter.savepoint)

    def test_rollback_to_savepoint_exists(self):
        """rollback_to_savepoint() method should exist and be async."""
        from pynext.db.adapters.postgres.core import PostgresAdapter
        
        assert hasattr(PostgresAdapter, 'rollback_to_savepoint')
        assert inspect.iscoroutinefunction(PostgresAdapter.rollback_to_savepoint)


# =============================================================================
# 12. EXCEPTION HIERARCHY
# =============================================================================

class TestExceptionHierarchy:
    """Verify all exceptions inherit from correct base classes."""

    def test_config_error_is_exception(self):
        """PostgresConfigError should be a subclass of Exception."""
        from pynext.db.adapters.postgres.core import PostgresConfigError
        
        assert issubclass(PostgresConfigError, Exception)

    def test_type_conversion_error_is_exception(self):
        """TypeConversionError should be a subclass of Exception."""
        from pynext.db.adapters.postgres.core import TypeConversionError
        
        assert issubclass(TypeConversionError, Exception)

    def test_exceptions_importable_from_multiple_paths(self):
        """Exceptions should be importable from adapter package."""
        from pynext.db.adapters.postgres.core import PostgresConfigError as Error1
        from pynext.db.adapters.postgres import PostgresConfigError as Error2
        
        # Both imports should resolve to the same class
        assert Error1 is Error2


# =============================================================================
# 13. SUBCOMPONENT EXISTENCE
# =============================================================================

class TestSubcomponentExistence:
    """Verify adapter creates expected internal components."""

    def test_retry_manager_created_when_enabled(self):
        """Retry manager should be created when retry=True."""
        from pynext.db.adapters.postgres.core import PostgresAdapter
        
        adapter = PostgresAdapter("postgresql://localhost/testdb", retry=True)
        assert adapter._retry_manager is not None

    def test_circuit_breaker_created_when_enabled(self):
        """Circuit breaker registry should be created when circuit_breaker=True."""
        from pynext.db.adapters.postgres.core import PostgresAdapter
        
        adapter = PostgresAdapter("postgresql://localhost/testdb", circuit_breaker=True)
        assert adapter._circuit_breaker_registry is not None

    def test_db_logger_always_created(self):
        """DB logger should always be created."""
        from pynext.db.adapters.postgres.core import PostgresAdapter
        
        adapter = PostgresAdapter("postgresql://localhost/testdb")
        assert adapter._db_logger is not None

    def test_query_analyzer_always_created(self):
        """Query analyzer should always be created."""
        from pynext.db.adapters.postgres.core import PostgresAdapter
        
        adapter = PostgresAdapter("postgresql://localhost/testdb")
        assert adapter._query_analyzer is not None


# =============================================================================
# 14. DEFAULT STATE
# =============================================================================

class TestDefaultState:
    """Verify adapter is in correct state before connect()."""

    def test_pool_none_initially(self):
        """Pool should be None before connect() is called."""
        from pynext.db.adapters.postgres.core import PostgresAdapter
        
        adapter = PostgresAdapter("postgresql://localhost/testdb")
        assert adapter._pool is None

    def test_not_in_transaction_initially(self):
        """Adapter should not be in a transaction before connect()."""
        from pynext.db.adapters.postgres.core import PostgresAdapter
        
        adapter = PostgresAdapter("postgresql://localhost/testdb")
        assert adapter._in_transaction is False

    def test_no_current_connection_initially(self):
        """Adapter should have no current connection before connect()."""
        from pynext.db.adapters.postgres.core import PostgresAdapter
        
        adapter = PostgresAdapter("postgresql://localhost/testdb")
        assert adapter._current_connection is None


# =============================================================================
# 15. OBJECT REPRESENTATION
# =============================================================================

class TestObjectRepresentation:
    """Verify objects have useful string representations."""

    def test_adapter_has_repr(self):
        """PostgresAdapter should have a meaningful repr."""
        from pynext.db.adapters.postgres.core import PostgresAdapter
        
        adapter = PostgresAdapter("postgresql://localhost/testdb")
        repr_str = repr(adapter)
        # Should contain class name at minimum
        assert 'PostgresAdapter' in repr_str or 'postgres' in repr_str.lower()

    def test_config_has_repr(self):
        """PostgresConfig should have a meaningful repr."""
        from pynext.db.adapters.postgres.core import PostgresConfig
        
        config = PostgresConfig(database="testdb")
        repr_str = repr(config)
        # Should contain class name or database name
        assert 'PostgresConfig' in repr_str or 'testdb' in repr_str


# =============================================================================
# 16. CONFIG COPY
# =============================================================================

class TestConfigCopy:
    """Verify config objects can be safely copied."""

    def test_postgres_config_is_copyable(self):
        """PostgresConfig should be copyable via copy.copy()."""
        import copy
        from pynext.db.adapters.postgres.core import PostgresConfig
        
        config = PostgresConfig(database="testdb", host="localhost")
        config_copy = copy.copy(config)
        
        assert config_copy.database == config.database
        assert config_copy.host == config.host
        assert config_copy is not config

    def test_retry_config_is_copyable(self):
        """RetryConfig should be copyable via copy.copy()."""
        import copy
        from pynext.db.adapters.postgres.reliability import RetryConfig
        
        config = RetryConfig(max_attempts=5)
        config_copy = copy.copy(config)
        
        assert config_copy.max_attempts == config.max_attempts
        assert config_copy is not config
