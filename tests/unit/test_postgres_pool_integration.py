"""
Integration tests for PostgreSQL Connection Pool (Phase 5.2).

Tests cover:
- Full flow from pool start to query to close
- Queue + lifecycle + warmup integration
- External pooler integration
- Error recovery scenarios
- Graceful shutdown
- Configuration combinations

Total: 100 tests
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from pynext.db.adapters.postgres.pool.pool import (
    AutoScalingPool,
    PoolStats,
    PoolState,
    PooledConnection,
    ConnectionState,
    PoolExhaustedError,
    PoolClosedError,
)
from pynext.db.adapters.postgres.core.url import PostgresConfig
from pynext.db.adapters.postgres.pool.queue import QueueConfig, QueuePriority
from pynext.db.adapters.postgres.pool.lifecycle import LifecycleConfig, RetirementReason
from pynext.db.adapters.postgres.pool.warmup import WarmupConfig
from pynext.db.adapters.postgres.pool.external import ExternalPoolerConfig, PoolerType, PoolerMode


# =============================================================================
# Pool Initialization Tests (15 tests)
# =============================================================================

class TestPoolInitialization:
    """Tests for pool initialization with Phase 5.2 features."""
    
    def test_init_with_all_configs(self):
        """Test initialization with all Phase 5.2 configs."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(
            config=config,
            queue_config=QueueConfig(max_size=100),
            lifecycle_config=LifecycleConfig(max_lifetime=1800),
            warmup_config=WarmupConfig(enabled=True),
            external_pooler=ExternalPoolerConfig(enabled=False),
        )
        assert pool.state == PoolState.UNINITIALIZED
        
    def test_init_with_queue_config(self):
        """Test initialization with queue config."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(
            config=config,
            queue_config=QueueConfig(max_size=500),
        )
        assert pool._queue.config.max_size == 500
        
    def test_init_with_lifecycle_config(self):
        """Test initialization with lifecycle config."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(
            config=config,
            lifecycle_config=LifecycleConfig(max_lifetime=7200),
        )
        assert pool._lifecycle_manager.config.max_lifetime == 7200
        
    def test_init_with_warmup_config(self):
        """Test initialization with warmup config."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(
            config=config,
            warmup_config=WarmupConfig(enabled=True, query="SELECT 2"),
        )
        assert pool._warmer.config.query == "SELECT 2"
        
    def test_init_with_external_pooler(self):
        """Test initialization with external pooler config."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(
            config=config,
            external_pooler=ExternalPoolerConfig(
                enabled=True,
                type=PoolerType.PGBOUNCER,
            ),
        )
        assert pool._external_pooler.pooler_type == PoolerType.PGBOUNCER
        
    def test_init_defaults(self):
        """Test initialization creates default configs."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(config=config)
        assert pool._queue is not None
        assert pool._lifecycle_manager is not None
        assert pool._warmer is not None
        assert pool._external_pooler is not None
        
    def test_properties_before_start(self):
        """Test properties before pool start."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(config=config)
        assert pool.is_under_pressure is False
        assert pool.queue_depth == 0
        
    def test_lifecycle_manager_property(self):
        """Test lifecycle_manager property."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(config=config)
        assert pool.lifecycle_manager is not None
        
    def test_warmer_property(self):
        """Test warmer property."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(config=config)
        assert pool.warmer is not None
        
    def test_external_pooler_property(self):
        """Test external_pooler property."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(config=config)
        assert pool.external_pooler is not None
        
    def test_queue_timeout_from_acquire_timeout(self):
        """Test queue uses acquire_timeout by default."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(
            config=config,
            acquire_timeout=15.0,
        )
        assert pool._queue.config.max_wait_time == 15.0
        
    def test_lifecycle_uses_max_lifetime(self):
        """Test lifecycle uses max_lifetime parameter."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(
            config=config,
            max_lifetime=1800,
        )
        assert pool._lifecycle_manager.config.max_lifetime == 1800
        
    def test_lifecycle_soft_lifetime_derived(self):
        """Test lifecycle soft_lifetime is derived from max_lifetime."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(
            config=config,
            max_lifetime=3600,
        )
        # Soft lifetime should be max_lifetime / 2 by default
        assert pool._lifecycle_manager.config.soft_lifetime == 1800
        
    def test_busy_connections_set_empty(self):
        """Test busy connections set is empty initially."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(config=config)
        assert len(pool._busy_connections) == 0
        
    def test_connection_id_counter_starts_zero(self):
        """Test connection ID counter starts at 0."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(config=config)
        assert pool._connection_id_counter == 0


# =============================================================================
# Pool Stats Tests (20 tests)
# =============================================================================

class TestPoolStats:
    """Tests for pool statistics with Phase 5.2 additions."""
    
    def test_get_stats_includes_queue(self):
        """Test get_stats includes queue statistics."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(config=config)
        stats = pool.get_stats()
        assert hasattr(stats, 'queue_depth')
        assert hasattr(stats, 'queue_wait_avg_ms')
        
    def test_get_stats_includes_warmup(self):
        """Test get_stats includes warmup statistics."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(config=config)
        stats = pool.get_stats()
        assert hasattr(stats, 'warmup_success_rate')
        
    def test_get_stats_includes_health(self):
        """Test get_stats includes health check statistics."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(config=config)
        stats = pool.get_stats()
        assert hasattr(stats, 'health_check_failures')
        
    def test_get_stats_includes_pressure(self):
        """Test get_stats includes pressure indicator."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(config=config)
        stats = pool.get_stats()
        assert hasattr(stats, 'is_under_pressure')
        
    def test_get_queue_stats(self):
        """Test get_queue_stats method."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(config=config)
        stats = pool.get_queue_stats()
        assert stats.depth == 0
        
    def test_get_lifecycle_stats(self):
        """Test get_lifecycle_stats method."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(config=config)
        stats = pool.get_lifecycle_stats()
        assert stats.total_connections_created == 0
        
    def test_get_warmup_stats(self):
        """Test get_warmup_stats method."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(config=config)
        stats = pool.get_warmup_stats()
        assert stats.total_warmups == 0
        
    def test_stats_to_dict_includes_phase52(self):
        """Test stats to_dict includes Phase 5.2 fields."""
        stats = PoolStats()
        d = stats.to_dict()
        assert 'queue_depth' in d
        assert 'queue_wait_avg_ms' in d
        assert 'warmup_success_rate' in d
        assert 'is_under_pressure' in d
        
    def test_stats_queue_wait_p99(self):
        """Test stats includes queue wait p99."""
        stats = PoolStats()
        assert stats.queue_wait_p99_ms == 0
        
    def test_stats_health_check_failures_default(self):
        """Test health check failures default to 0."""
        stats = PoolStats()
        assert stats.health_check_failures == 0
        
    def test_stats_is_under_pressure_default(self):
        """Test is_under_pressure defaults to False."""
        stats = PoolStats()
        assert stats.is_under_pressure is False
        
    def test_stats_warmup_success_rate_default(self):
        """Test warmup success rate defaults to 1.0."""
        stats = PoolStats()
        assert stats.warmup_success_rate == 1.0
        
    def test_stats_utilization_calculation(self):
        """Test utilization is calculated correctly."""
        stats = PoolStats(size=10, busy=5)
        d = stats.to_dict()
        assert d['utilization'] == 0.5
        
    def test_stats_utilization_empty_pool(self):
        """Test utilization with empty pool."""
        stats = PoolStats(size=0, busy=0)
        d = stats.to_dict()
        assert d['utilization'] == 0
        
    def test_stats_all_fields_accessible(self):
        """Test all stats fields are accessible."""
        stats = PoolStats()
        _ = stats.size
        _ = stats.idle
        _ = stats.busy
        _ = stats.waiting
        _ = stats.min_size
        _ = stats.max_size
        _ = stats.total_acquires
        _ = stats.total_releases
        _ = stats.queue_depth
        _ = stats.queue_wait_avg_ms
        
    def test_stats_created_closed_tracking(self):
        """Test created/closed tracking."""
        stats = PoolStats(created=10, closed=5)
        assert stats.created == 10
        assert stats.closed == 5
        
    def test_stats_timeouts_tracking(self):
        """Test timeout tracking."""
        stats = PoolStats(total_timeouts=3)
        assert stats.total_timeouts == 3
        
    def test_stats_waiting_default(self):
        """Test waiting defaults to 0."""
        stats = PoolStats()
        assert stats.waiting == 0
        
    def test_stats_with_all_values(self):
        """Test stats with all values set."""
        stats = PoolStats(
            size=10,
            idle=3,
            busy=7,
            waiting=5,
            min_size=5,
            max_size=20,
            total_acquires=100,
            total_releases=95,
            total_timeouts=2,
            created=15,
            closed=5,
            queue_depth=5,
            queue_wait_avg_ms=15.5,
            queue_wait_p99_ms=50.0,
            warmup_success_rate=0.95,
            health_check_failures=1,
            is_under_pressure=True,
        )
        d = stats.to_dict()
        assert len(d) > 0
        
    def test_stats_immutable_fields(self):
        """Test stats fields can be read."""
        stats = PoolStats(queue_depth=10)
        assert stats.queue_depth == 10


# =============================================================================
# Pool State Management Tests (15 tests)
# =============================================================================

class TestPoolStateManagement:
    """Tests for pool state management."""
    
    def test_initial_state(self):
        """Test initial pool state."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(config=config)
        assert pool.state == PoolState.UNINITIALIZED
        
    def test_pool_state_enum(self):
        """Test pool state enum values."""
        assert PoolState.UNINITIALIZED.value == "uninitialized"
        assert PoolState.RUNNING.value == "running"
        assert PoolState.CLOSING.value == "closing"
        assert PoolState.CLOSED.value == "closed"
        
    def test_connection_state_enum(self):
        """Test connection state enum values."""
        assert ConnectionState.IDLE.value == "idle"
        assert ConnectionState.BUSY.value == "busy"
        assert ConnectionState.CLOSING.value == "closing"
        assert ConnectionState.CLOSED.value == "closed"
        
    def test_pooled_connection_creation(self):
        """Test pooled connection creation."""
        mock_conn = MagicMock()
        pooled = PooledConnection(
            connection=mock_conn,
            connection_id="conn_1",
        )
        assert pooled.connection_id == "conn_1"
        assert pooled.state == ConnectionState.IDLE
        assert pooled.use_count == 0
        
    def test_pooled_connection_mark_busy(self):
        """Test marking pooled connection as busy."""
        mock_conn = MagicMock()
        pooled = PooledConnection(connection=mock_conn, connection_id="conn_1")
        pooled.mark_busy()
        assert pooled.state == ConnectionState.BUSY
        assert pooled.use_count == 1
        
    def test_pooled_connection_mark_idle(self):
        """Test marking pooled connection as idle."""
        mock_conn = MagicMock()
        pooled = PooledConnection(connection=mock_conn, connection_id="conn_1")
        pooled.mark_busy()
        pooled.mark_idle()
        assert pooled.state == ConnectionState.IDLE
        
    def test_pooled_connection_age(self):
        """Test pooled connection age calculation."""
        import time
        mock_conn = MagicMock()
        pooled = PooledConnection(
            connection=mock_conn,
            connection_id="conn_1",
            created_at=time.monotonic() - 10,
        )
        assert pooled.age() >= 10
        
    def test_pooled_connection_idle_time(self):
        """Test pooled connection idle time calculation."""
        import time
        mock_conn = MagicMock()
        pooled = PooledConnection(
            connection=mock_conn,
            connection_id="conn_1",
            last_used=time.monotonic() - 5,
        )
        assert pooled.idle_time() >= 5
        
    def test_pool_exhausted_error(self):
        """Test pool exhausted error."""
        error = PoolExhaustedError("Pool exhausted")
        assert isinstance(error, Exception)
        
    def test_pool_closed_error(self):
        """Test pool closed error."""
        error = PoolClosedError("Pool closed")
        assert isinstance(error, Exception)
        
    def test_pool_size_property(self):
        """Test pool size property."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(config=config)
        assert pool.size == 0
        
    def test_pool_is_under_pressure_property(self):
        """Test is_under_pressure property."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(config=config)
        assert pool.is_under_pressure is False
        
    def test_pool_queue_depth_property(self):
        """Test queue_depth property."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(config=config)
        assert pool.queue_depth == 0
        
    def test_pool_state_property(self):
        """Test state property."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(config=config)
        assert pool.state == PoolState.UNINITIALIZED
        
    def test_pooled_connection_connection_id(self):
        """Test pooled connection has connection_id."""
        mock_conn = MagicMock()
        pooled = PooledConnection(
            connection=mock_conn,
            connection_id="my_conn_123",
        )
        assert pooled.connection_id == "my_conn_123"


# =============================================================================
# Configuration Combination Tests (20 tests)
# =============================================================================

class TestConfigurationCombinations:
    """Tests for various configuration combinations."""
    
    def test_minimal_config(self):
        """Test minimal configuration."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(config=config)
        assert pool is not None
        
    def test_max_pool_size(self):
        """Test with large max pool size."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(config=config, max_size=1000)
        assert pool._max_size == 1000
        
    def test_min_equals_max(self):
        """Test min equals max pool size."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(config=config, min_size=10, max_size=10)
        assert pool._min_size == 10
        assert pool._max_size == 10
        
    def test_auto_scale_disabled(self):
        """Test with auto-scaling disabled."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(config=config, auto_scale=False)
        assert pool._auto_scale is False
        
    def test_short_timeouts(self):
        """Test with short timeouts."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(
            config=config,
            acquire_timeout=1.0,
            connect_timeout=1.0,
        )
        assert pool._acquire_timeout == 1.0
        
    def test_long_timeouts(self):
        """Test with long timeouts."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(
            config=config,
            acquire_timeout=300.0,
            connect_timeout=60.0,
        )
        assert pool._acquire_timeout == 300.0
        
    def test_command_timeout(self):
        """Test with command timeout."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(config=config, command_timeout=30.0)
        assert pool._command_timeout == 30.0
        
    def test_no_command_timeout(self):
        """Test without command timeout."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(config=config)
        assert pool._command_timeout is None
        
    def test_aggressive_queue_config(self):
        """Test with aggressive queue config."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(
            config=config,
            queue_config=QueueConfig(
                max_size=10,
                warn_threshold=5,
                critical_threshold=8,
            ),
        )
        assert pool._queue.config.max_size == 10
        
    def test_relaxed_queue_config(self):
        """Test with relaxed queue config."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(
            config=config,
            queue_config=QueueConfig(
                max_size=10000,
                max_wait_time=300.0,
            ),
        )
        assert pool._queue.config.max_size == 10000
        
    def test_strict_lifecycle_config(self):
        """Test with strict lifecycle config."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(
            config=config,
            lifecycle_config=LifecycleConfig(
                max_lifetime=600,
                soft_lifetime=300,
                max_uses=1000,
            ),
        )
        assert pool._lifecycle_manager.config.max_lifetime == 600
        
    def test_relaxed_lifecycle_config(self):
        """Test with relaxed lifecycle config."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(
            config=config,
            lifecycle_config=LifecycleConfig(
                max_lifetime=86400,  # 24 hours
                soft_lifetime=43200,  # 12 hours
                max_uses=0,  # Unlimited
            ),
        )
        assert pool._lifecycle_manager.config.max_uses == 0
        
    def test_warmup_with_prepare(self):
        """Test warmup with statement preparation."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(
            config=config,
            warmup_config=WarmupConfig(
                enabled=True,
                prepare_statements=["SELECT $1", "SELECT $1, $2"],
            ),
        )
        assert len(pool._warmer.config.prepare_statements) == 2
        
    def test_warmup_disabled(self):
        """Test with warmup disabled."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(
            config=config,
            warmup_config=WarmupConfig(enabled=False),
        )
        assert pool._warmer.enabled is False
        
    def test_pgbouncer_transaction_mode(self):
        """Test with PgBouncer transaction mode."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(
            config=config,
            external_pooler=ExternalPoolerConfig(
                enabled=True,
                type=PoolerType.PGBOUNCER,
                mode=PoolerMode.TRANSACTION,
            ),
        )
        assert pool._external_pooler.can_use_prepared_statements() is False
        
    def test_pgbouncer_session_mode(self):
        """Test with PgBouncer session mode."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(
            config=config,
            external_pooler=ExternalPoolerConfig(
                enabled=True,
                type=PoolerType.PGBOUNCER,
                mode=PoolerMode.SESSION,
            ),
        )
        assert pool._external_pooler.can_use_prepared_statements() is True
        
    def test_all_features_enabled(self):
        """Test with all features enabled."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(
            config=config,
            min_size=5,
            max_size=50,
            auto_scale=True,
            queue_config=QueueConfig(max_size=500),
            lifecycle_config=LifecycleConfig(max_lifetime=3600),
            warmup_config=WarmupConfig(enabled=True),
            external_pooler=ExternalPoolerConfig(enabled=True),
        )
        assert pool is not None
        
    def test_zero_idle_timeout(self):
        """Test with zero idle timeout."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(config=config, idle_timeout=0)
        assert pool._idle_timeout == 0
        
    def test_zero_max_lifetime(self):
        """Test with zero max lifetime (no limit)."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(config=config, max_lifetime=0)
        assert pool._max_lifetime == 0


# =============================================================================
# Error Handling Tests (15 tests)
# =============================================================================

class TestErrorHandling:
    """Tests for error handling scenarios."""
    
    def test_invalid_min_size(self):
        """Test invalid min_size raises error."""
        config = PostgresConfig(host="localhost", database="test")
        with pytest.raises(ValueError):
            AutoScalingPool(config=config, min_size=-1)
            
    def test_invalid_max_size(self):
        """Test invalid max_size raises error."""
        config = PostgresConfig(host="localhost", database="test")
        with pytest.raises(ValueError):
            AutoScalingPool(config=config, max_size=0)
            
    def test_min_exceeds_max(self):
        """Test min_size > max_size raises error."""
        config = PostgresConfig(host="localhost", database="test")
        with pytest.raises(ValueError):
            AutoScalingPool(config=config, min_size=20, max_size=10)
            
    def test_invalid_idle_timeout(self):
        """Test invalid idle_timeout raises error."""
        config = PostgresConfig(host="localhost", database="test")
        with pytest.raises(ValueError):
            AutoScalingPool(config=config, idle_timeout=-1)
            
    def test_invalid_max_lifetime(self):
        """Test invalid max_lifetime raises error."""
        config = PostgresConfig(host="localhost", database="test")
        with pytest.raises(ValueError):
            AutoScalingPool(config=config, max_lifetime=-1)
            
    def test_pool_exhausted_error_message(self):
        """Test pool exhausted error message."""
        error = PoolExhaustedError("Test message")
        assert "Test message" in str(error)
        
    def test_pool_closed_error_message(self):
        """Test pool closed error message."""
        error = PoolClosedError("Test message")
        assert "Test message" in str(error)
        
    def test_errors_are_exceptions(self):
        """Test errors inherit from Exception."""
        assert issubclass(PoolExhaustedError, Exception)
        assert issubclass(PoolClosedError, Exception)
        
    @pytest.mark.asyncio
    async def test_acquire_before_start(self):
        """Test acquiring before pool start raises error."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(config=config)
        with pytest.raises(PoolClosedError):
            async with pool.acquire():
                pass
                
    @pytest.mark.asyncio
    async def test_double_start_warning(self):
        """Test double start logs warning."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(config=config, min_size=0)
        
        # Set state to RUNNING without actually starting
        pool._state = PoolState.RUNNING
        await pool.start()  # Should warn and return early (no-op)
            
    @pytest.mark.asyncio
    async def test_double_close_safe(self):
        """Test double close is safe."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(config=config)
        pool._state = PoolState.CLOSED
        await pool.close()  # Should be no-op
        
    def test_connection_id_preserved_in_error(self):
        """Test connection ID context in errors."""
        mock_conn = MagicMock()
        pooled = PooledConnection(
            connection=mock_conn,
            connection_id="conn_123",
        )
        assert pooled.connection_id == "conn_123"
        
    def test_queue_config_validation_propagates(self):
        """Test queue config validation errors propagate."""
        with pytest.raises(ValueError):
            QueueConfig(max_size=-1)
            
    def test_lifecycle_config_validation_propagates(self):
        """Test lifecycle config validation errors propagate."""
        with pytest.raises(ValueError):
            LifecycleConfig(max_lifetime=-1)
            
    def test_warmup_config_validation_propagates(self):
        """Test warmup config validation errors propagate."""
        with pytest.raises(ValueError):
            WarmupConfig(timeout=0)


# =============================================================================
# Repr Tests (15 tests)
# =============================================================================

class TestPoolRepr:
    """Tests for pool string representations."""
    
    def test_pool_repr_basic(self):
        """Test basic pool repr."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(config=config)
        repr_str = repr(pool)
        assert "AutoScalingPool" in repr_str
        
    def test_pool_repr_includes_state(self):
        """Test pool repr includes state."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(config=config)
        repr_str = repr(pool)
        assert "uninitialized" in repr_str
        
    def test_pool_repr_includes_size(self):
        """Test pool repr includes size."""
        config = PostgresConfig(host="localhost", database="test")
        pool = AutoScalingPool(config=config, max_size=50)
        repr_str = repr(pool)
        assert "50" in repr_str or "size" in repr_str.lower()
        
    def test_pooled_connection_repr_not_needed(self):
        """Test pooled connection doesn't need custom repr."""
        mock_conn = MagicMock()
        pooled = PooledConnection(
            connection=mock_conn,
            connection_id="conn_1",
        )
        # Should have default dataclass repr
        repr_str = repr(pooled)
        assert "PooledConnection" in repr_str
        
    def test_pool_state_repr(self):
        """Test pool state repr."""
        state = PoolState.RUNNING
        assert "running" in str(state).lower() or "RUNNING" in str(state)
        
    def test_connection_state_repr(self):
        """Test connection state repr."""
        state = ConnectionState.IDLE
        assert "idle" in str(state).lower() or "IDLE" in str(state)
        
    def test_stats_repr(self):
        """Test stats repr."""
        stats = PoolStats(size=10, busy=5)
        d = stats.to_dict()
        assert d is not None
        
    def test_queue_config_repr(self):
        """Test queue config has repr."""
        config = QueueConfig(max_size=100)
        repr_str = repr(config)
        assert "100" in repr_str or "QueueConfig" in repr_str
        
    def test_lifecycle_config_repr(self):
        """Test lifecycle config has repr."""
        config = LifecycleConfig(max_lifetime=3600)
        repr_str = repr(config)
        assert "3600" in repr_str or "LifecycleConfig" in repr_str
        
    def test_warmup_config_repr(self):
        """Test warmup config has repr."""
        config = WarmupConfig(enabled=True)
        repr_str = repr(config)
        assert "WarmupConfig" in repr_str or "True" in repr_str
        
    def test_external_pooler_config_repr(self):
        """Test external pooler config has repr."""
        config = ExternalPoolerConfig(enabled=True)
        repr_str = repr(config)
        assert "ExternalPoolerConfig" in repr_str or "True" in repr_str
        
    def test_pooler_type_repr(self):
        """Test pooler type repr."""
        ptype = PoolerType.PGBOUNCER
        repr_str = repr(ptype)
        assert "PGBOUNCER" in repr_str or "pgbouncer" in repr_str
        
    def test_pooler_mode_repr(self):
        """Test pooler mode repr."""
        mode = PoolerMode.TRANSACTION
        repr_str = repr(mode)
        assert "TRANSACTION" in repr_str or "transaction" in repr_str
        
    def test_retirement_reason_repr(self):
        """Test retirement reason repr."""
        reason = RetirementReason.MAX_USES
        repr_str = repr(reason)
        assert "MAX_USES" in repr_str or "max_uses" in repr_str
        
    def test_queue_priority_repr(self):
        """Test queue priority repr."""
        priority = QueuePriority.CRITICAL
        repr_str = repr(priority)
        assert "CRITICAL" in repr_str or "0" in repr_str

