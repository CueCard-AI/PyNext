"""
Comprehensive tests for PostgreSQL Connection Lifecycle (Phase 5.2).

Tests cover:
- LifecycleConfig validation and defaults
- ConnectionLifecycle state management
- Soft vs hard lifetime limits
- Use count retirement
- Health check tracking
- Graceful replacement
- Statistics tracking

Total: 80 tests
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
import time

from pynext.db.adapters.postgres_lifecycle import (
    LifecycleConfig,
    ConnectionHealth,
    RetirementReason,
    ReplacementStrategy,
    ConnectionLifecycle,
    LifecycleStats,
    LifecycleManager,
)


# =============================================================================
# LifecycleConfig Tests (15 tests)
# =============================================================================

class TestLifecycleConfig:
    """Tests for LifecycleConfig dataclass."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = LifecycleConfig()
        assert config.max_lifetime == 3600.0
        assert config.soft_lifetime == 1800.0
        assert config.max_uses == 10000
        assert config.health_check_interval == 30.0
        assert config.health_check_timeout == 5.0
        assert config.health_check_query == "SELECT 1"
        assert config.replacement_strategy == ReplacementStrategy.GRACEFUL
        assert config.grace_period == 30.0
        
    def test_custom_values(self):
        """Test custom configuration values."""
        config = LifecycleConfig(
            max_lifetime=7200.0,
            soft_lifetime=3600.0,
            max_uses=5000,
            health_check_interval=60.0,
            replacement_strategy=ReplacementStrategy.IMMEDIATE,
        )
        assert config.max_lifetime == 7200.0
        assert config.soft_lifetime == 3600.0
        
    def test_invalid_max_lifetime_raises_error(self):
        """Test negative max_lifetime raises error."""
        with pytest.raises(ValueError, match="max_lifetime must be >= 0"):
            LifecycleConfig(max_lifetime=-1)
            
    def test_invalid_soft_lifetime_raises_error(self):
        """Test negative soft_lifetime raises error."""
        with pytest.raises(ValueError, match="soft_lifetime must be >= 0"):
            LifecycleConfig(soft_lifetime=-1)
            
    def test_soft_exceeds_max_raises_error(self):
        """Test soft_lifetime > max_lifetime raises error."""
        with pytest.raises(ValueError, match="soft_lifetime.*cannot exceed"):
            LifecycleConfig(soft_lifetime=3600, max_lifetime=1800)
            
    def test_invalid_max_uses_raises_error(self):
        """Test negative max_uses raises error."""
        with pytest.raises(ValueError, match="max_uses must be >= 0"):
            LifecycleConfig(max_uses=-1)
            
    def test_invalid_health_check_interval_raises_error(self):
        """Test negative health_check_interval raises error."""
        with pytest.raises(ValueError, match="health_check_interval must be >= 0"):
            LifecycleConfig(health_check_interval=-1)
            
    def test_invalid_grace_period_raises_error(self):
        """Test negative grace_period raises error."""
        with pytest.raises(ValueError, match="grace_period must be >= 0"):
            LifecycleConfig(grace_period=-1)
            
    def test_zero_max_lifetime_allowed(self):
        """Test zero max_lifetime is allowed (no limit)."""
        config = LifecycleConfig(max_lifetime=0, soft_lifetime=0)
        assert config.max_lifetime == 0
        
    def test_zero_max_uses_allowed(self):
        """Test zero max_uses is allowed (no limit)."""
        config = LifecycleConfig(max_uses=0)
        assert config.max_uses == 0
        
    def test_immediate_replacement(self):
        """Test immediate replacement strategy."""
        config = LifecycleConfig(replacement_strategy=ReplacementStrategy.IMMEDIATE)
        assert config.replacement_strategy == ReplacementStrategy.IMMEDIATE
        
    def test_lazy_replacement(self):
        """Test lazy replacement strategy."""
        config = LifecycleConfig(replacement_strategy=ReplacementStrategy.LAZY)
        assert config.replacement_strategy == ReplacementStrategy.LAZY
        
    def test_custom_health_check_query(self):
        """Test custom health check query."""
        config = LifecycleConfig(health_check_query="SELECT NOW()")
        assert config.health_check_query == "SELECT NOW()"
        
    def test_track_metrics_default(self):
        """Test track_metrics default value."""
        config = LifecycleConfig()
        assert config.track_metrics is True
        
    def test_equal_soft_and_max_lifetime(self):
        """Test equal soft and max lifetime is valid."""
        config = LifecycleConfig(soft_lifetime=1800, max_lifetime=1800)
        assert config.soft_lifetime == config.max_lifetime


# =============================================================================
# ConnectionHealth Tests (5 tests)
# =============================================================================

class TestConnectionHealth:
    """Tests for ConnectionHealth enum."""
    
    def test_healthy_status(self):
        """Test healthy status."""
        assert ConnectionHealth.HEALTHY.value == "healthy"
        
    def test_unknown_status(self):
        """Test unknown status."""
        assert ConnectionHealth.UNKNOWN.value == "unknown"
        
    def test_degraded_status(self):
        """Test degraded status."""
        assert ConnectionHealth.DEGRADED.value == "degraded"
        
    def test_unhealthy_status(self):
        """Test unhealthy status."""
        assert ConnectionHealth.UNHEALTHY.value == "unhealthy"
        
    def test_closed_status(self):
        """Test closed status."""
        assert ConnectionHealth.CLOSED.value == "closed"


# =============================================================================
# RetirementReason Tests (5 tests)
# =============================================================================

class TestRetirementReason:
    """Tests for RetirementReason enum."""
    
    def test_soft_lifetime_reason(self):
        """Test soft lifetime reason."""
        assert RetirementReason.SOFT_LIFETIME.value == "soft_lifetime"
        
    def test_hard_lifetime_reason(self):
        """Test hard lifetime reason."""
        assert RetirementReason.HARD_LIFETIME.value == "hard_lifetime"
        
    def test_max_uses_reason(self):
        """Test max uses reason."""
        assert RetirementReason.MAX_USES.value == "max_uses"
        
    def test_health_check_failed_reason(self):
        """Test health check failed reason."""
        assert RetirementReason.HEALTH_CHECK_FAILED.value == "health_check_failed"
        
    def test_manual_reason(self):
        """Test manual reason."""
        assert RetirementReason.MANUAL.value == "manual"


# =============================================================================
# ConnectionLifecycle Tests (20 tests)
# =============================================================================

class TestConnectionLifecycle:
    """Tests for ConnectionLifecycle dataclass."""
    
    def test_creation(self):
        """Test lifecycle creation."""
        lifecycle = ConnectionLifecycle(connection_id="conn_1")
        assert lifecycle.connection_id == "conn_1"
        assert lifecycle.use_count == 0
        assert lifecycle.health == ConnectionHealth.UNKNOWN
        assert lifecycle.marked_for_retirement is False
        
    def test_age_calculation(self):
        """Test age calculation."""
        lifecycle = ConnectionLifecycle(
            connection_id="conn_1",
            created_at=time.monotonic() - 10.0,
        )
        assert lifecycle.age() >= 10.0
        
    def test_idle_time_calculation(self):
        """Test idle time calculation."""
        lifecycle = ConnectionLifecycle(
            connection_id="conn_1",
            last_used=time.monotonic() - 5.0,
        )
        assert lifecycle.idle_time() >= 5.0
        
    def test_mark_used(self):
        """Test marking as used."""
        lifecycle = ConnectionLifecycle(connection_id="conn_1")
        lifecycle.mark_used()
        assert lifecycle.use_count == 1
        
    def test_mark_used_multiple(self):
        """Test marking as used multiple times."""
        lifecycle = ConnectionLifecycle(connection_id="conn_1")
        for _ in range(10):
            lifecycle.mark_used()
        assert lifecycle.use_count == 10
        
    def test_mark_healthy(self):
        """Test marking as healthy."""
        lifecycle = ConnectionLifecycle(connection_id="conn_1")
        lifecycle.mark_healthy()
        assert lifecycle.health == ConnectionHealth.HEALTHY
        assert lifecycle.last_health_check > 0
        
    def test_mark_unhealthy(self):
        """Test marking as unhealthy."""
        lifecycle = ConnectionLifecycle(connection_id="conn_1")
        lifecycle.mark_unhealthy()
        assert lifecycle.health == ConnectionHealth.UNHEALTHY
        
    def test_request_retirement(self):
        """Test requesting retirement."""
        lifecycle = ConnectionLifecycle(connection_id="conn_1")
        lifecycle.request_retirement(RetirementReason.MANUAL)
        assert lifecycle.marked_for_retirement is True
        assert lifecycle.retirement_reason == RetirementReason.MANUAL
        
    def test_request_retirement_idempotent(self):
        """Test requesting retirement is idempotent."""
        lifecycle = ConnectionLifecycle(connection_id="conn_1")
        lifecycle.request_retirement(RetirementReason.MANUAL)
        lifecycle.request_retirement(RetirementReason.MAX_USES)
        # First reason should stick
        assert lifecycle.retirement_reason == RetirementReason.MANUAL
        
    def test_should_retire_not_marked(self):
        """Test should_retire when not marked."""
        lifecycle = ConnectionLifecycle(connection_id="conn_1")
        config = LifecycleConfig()
        assert lifecycle.should_retire(config) is None
        
    def test_should_retire_when_marked(self):
        """Test should_retire when marked."""
        lifecycle = ConnectionLifecycle(connection_id="conn_1")
        lifecycle.request_retirement(RetirementReason.MANUAL)
        config = LifecycleConfig()
        assert lifecycle.should_retire(config) == RetirementReason.MANUAL
        
    def test_should_retire_hard_lifetime(self):
        """Test should_retire for hard lifetime."""
        lifecycle = ConnectionLifecycle(
            connection_id="conn_1",
            created_at=time.monotonic() - 7200,
        )
        config = LifecycleConfig(max_lifetime=3600)
        assert lifecycle.should_retire(config) == RetirementReason.HARD_LIFETIME
        
    def test_should_retire_max_uses(self):
        """Test should_retire for max uses."""
        lifecycle = ConnectionLifecycle(
            connection_id="conn_1",
            use_count=10000,
        )
        config = LifecycleConfig(max_uses=10000)
        assert lifecycle.should_retire(config) == RetirementReason.MAX_USES
        
    def test_should_retire_unhealthy(self):
        """Test should_retire for unhealthy."""
        lifecycle = ConnectionLifecycle(
            connection_id="conn_1",
            health=ConnectionHealth.UNHEALTHY,
        )
        config = LifecycleConfig()
        assert lifecycle.should_retire(config) == RetirementReason.HEALTH_CHECK_FAILED
        
    def test_should_prefer_retirement_soft_lifetime(self):
        """Test should_prefer_retirement for soft lifetime."""
        lifecycle = ConnectionLifecycle(
            connection_id="conn_1",
            created_at=time.monotonic() - 2000,
        )
        config = LifecycleConfig(soft_lifetime=1800, max_lifetime=3600)
        assert lifecycle.should_prefer_retirement(config) == RetirementReason.SOFT_LIFETIME
        
    def test_needs_health_check(self):
        """Test needs_health_check."""
        lifecycle = ConnectionLifecycle(
            connection_id="conn_1",
            last_health_check=time.monotonic() - 60,
        )
        config = LifecycleConfig(health_check_interval=30)
        assert lifecycle.needs_health_check(config) is True
        
    def test_needs_health_check_disabled(self):
        """Test needs_health_check when disabled."""
        lifecycle = ConnectionLifecycle(connection_id="conn_1")
        config = LifecycleConfig(health_check_interval=0)
        assert lifecycle.needs_health_check(config) is False
        
    def test_to_dict(self):
        """Test conversion to dictionary."""
        lifecycle = ConnectionLifecycle(connection_id="conn_1")
        d = lifecycle.to_dict()
        assert "connection_id" in d
        assert "age_seconds" in d
        assert "use_count" in d
        assert "health" in d
        
    def test_time_since_health_check_never(self):
        """Test time_since_health_check when never checked."""
        lifecycle = ConnectionLifecycle(connection_id="conn_1")
        assert lifecycle.time_since_health_check() == float("inf")
        
    def test_time_since_health_check_recent(self):
        """Test time_since_health_check after recent check."""
        lifecycle = ConnectionLifecycle(connection_id="conn_1")
        lifecycle.mark_healthy()
        assert lifecycle.time_since_health_check() < 1.0


# =============================================================================
# LifecycleStats Tests (10 tests)
# =============================================================================

class TestLifecycleStats:
    """Tests for LifecycleStats dataclass."""
    
    def test_default_values(self):
        """Test default statistics values."""
        stats = LifecycleStats()
        assert stats.total_connections_created == 0
        assert stats.total_connections_retired == 0
        assert stats.health_checks_performed == 0
        
    def test_avg_lifetime_empty(self):
        """Test average lifetime with no data."""
        stats = LifecycleStats()
        assert stats.avg_connection_lifetime_ms == 0
        
    def test_avg_lifetime_with_data(self):
        """Test average lifetime calculation."""
        stats = LifecycleStats()
        stats.connection_lifetimes_ms = [1000.0, 2000.0, 3000.0]
        assert stats.avg_connection_lifetime_ms == 2000.0
        
    def test_avg_uses_empty(self):
        """Test average uses with no data."""
        stats = LifecycleStats()
        assert stats.avg_connection_uses == 0
        
    def test_avg_uses_with_data(self):
        """Test average uses calculation."""
        stats = LifecycleStats()
        stats.connection_use_counts = [100, 200, 300]
        assert stats.avg_connection_uses == 200.0
        
    def test_record_retirement(self):
        """Test recording retirement."""
        stats = LifecycleStats()
        lifecycle = ConnectionLifecycle(
            connection_id="conn_1",
            use_count=500,
            retirement_reason=RetirementReason.MAX_USES,
        )
        stats.record_retirement(lifecycle)
        assert stats.total_connections_retired == 1
        assert "max_uses" in stats.retirements_by_reason
        
    def test_retirements_by_reason_tracking(self):
        """Test retirements by reason tracking."""
        stats = LifecycleStats()
        for reason in [RetirementReason.MAX_USES, RetirementReason.MAX_USES, RetirementReason.MANUAL]:
            lifecycle = ConnectionLifecycle(
                connection_id="conn",
                retirement_reason=reason,
            )
            stats.record_retirement(lifecycle)
        assert stats.retirements_by_reason["max_uses"] == 2
        assert stats.retirements_by_reason["manual"] == 1
        
    def test_to_dict(self):
        """Test conversion to dictionary."""
        stats = LifecycleStats()
        d = stats.to_dict()
        assert "total_created" in d
        assert "total_retired" in d
        assert "avg_lifetime_ms" in d
        
    def test_lifetime_samples_limited(self):
        """Test lifetime samples are limited to 1000."""
        stats = LifecycleStats()
        for i in range(1100):
            lifecycle = ConnectionLifecycle(connection_id=f"conn_{i}")
            stats.record_retirement(lifecycle)
        assert len(stats.connection_lifetimes_ms) == 1000
        
    def test_health_checks_increment(self):
        """Test health check counter increment."""
        stats = LifecycleStats()
        stats.health_checks_performed += 1
        stats.health_checks_performed += 1
        assert stats.health_checks_performed == 2


# =============================================================================
# LifecycleManager Tests (25 tests)
# =============================================================================

class TestLifecycleManager:
    """Tests for LifecycleManager class."""
    
    def test_init_default_config(self):
        """Test initialization with default config."""
        manager = LifecycleManager()
        assert manager.config.max_lifetime == 3600.0
        
    def test_init_custom_config(self):
        """Test initialization with custom config."""
        config = LifecycleConfig(max_lifetime=7200.0)
        manager = LifecycleManager(config)
        assert manager.config.max_lifetime == 7200.0
        
    def test_register_connection(self):
        """Test registering a connection."""
        manager = LifecycleManager()
        lifecycle = manager.register_connection("conn_1")
        assert lifecycle.connection_id == "conn_1"
        
    def test_register_connection_auto_id(self):
        """Test registering with auto-generated ID."""
        manager = LifecycleManager()
        lifecycle = manager.register_connection()
        assert lifecycle.connection_id.startswith("conn_")
        
    def test_register_multiple_connections(self):
        """Test registering multiple connections."""
        manager = LifecycleManager()
        for i in range(5):
            manager.register_connection(f"conn_{i}")
        assert len(manager._lifecycles) == 5
        
    def test_unregister_connection(self):
        """Test unregistering a connection."""
        manager = LifecycleManager()
        manager.register_connection("conn_1")
        lifecycle = manager.unregister_connection("conn_1")
        assert lifecycle is not None
        assert lifecycle.connection_id == "conn_1"
        
    def test_unregister_nonexistent(self):
        """Test unregistering nonexistent connection."""
        manager = LifecycleManager()
        lifecycle = manager.unregister_connection("nonexistent")
        assert lifecycle is None
        
    def test_get_lifecycle(self):
        """Test getting lifecycle by ID."""
        manager = LifecycleManager()
        manager.register_connection("conn_1")
        lifecycle = manager.get_lifecycle("conn_1")
        assert lifecycle is not None
        
    def test_get_lifecycle_nonexistent(self):
        """Test getting nonexistent lifecycle."""
        manager = LifecycleManager()
        lifecycle = manager.get_lifecycle("nonexistent")
        assert lifecycle is None
        
    def test_mark_used(self):
        """Test marking connection as used."""
        manager = LifecycleManager()
        manager.register_connection("conn_1")
        manager.mark_used("conn_1")
        lifecycle = manager.get_lifecycle("conn_1")
        assert lifecycle.use_count == 1
        
    def test_should_retire(self):
        """Test checking if connection should retire."""
        manager = LifecycleManager(LifecycleConfig(max_uses=10))
        manager.register_connection("conn_1")
        for _ in range(10):
            manager.mark_used("conn_1")
        reason = manager.should_retire("conn_1")
        assert reason == RetirementReason.MAX_USES
        
    def test_should_prefer_retirement(self):
        """Test checking if retirement is preferred."""
        manager = LifecycleManager()
        manager.register_connection("conn_1")
        reason = manager.should_prefer_retirement("conn_1")
        assert reason is None  # Fresh connection shouldn't prefer retirement
        
    def test_request_retirement(self):
        """Test requesting connection retirement."""
        manager = LifecycleManager()
        manager.register_connection("conn_1")
        result = manager.request_retirement("conn_1", RetirementReason.MANUAL)
        assert result is True
        
    def test_request_retirement_nonexistent(self):
        """Test requesting retirement of nonexistent connection."""
        manager = LifecycleManager()
        result = manager.request_retirement("nonexistent")
        assert result is False
        
    def test_get_connections_to_retire(self):
        """Test getting connections to retire."""
        manager = LifecycleManager(LifecycleConfig(max_uses=5))
        manager.register_connection("conn_1")
        for _ in range(5):
            manager.mark_used("conn_1")
        to_retire = manager.get_connections_to_retire()
        assert "conn_1" in to_retire
        
    def test_get_connections_needing_health_check(self):
        """Test getting connections needing health check."""
        manager = LifecycleManager(LifecycleConfig(health_check_interval=0.01))
        manager.register_connection("conn_1")
        time.sleep(0.02)  # Wait for interval to pass
        need_check = manager.get_connections_needing_health_check()
        assert "conn_1" in need_check
        
    @pytest.mark.asyncio
    async def test_check_health_success(self):
        """Test successful health check."""
        manager = LifecycleManager()
        manager.register_connection("conn_1")
        
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=1)
        
        health = await manager.check_health("conn_1", mock_conn)
        assert health == ConnectionHealth.HEALTHY
        
    @pytest.mark.asyncio
    async def test_check_health_failure(self):
        """Test failed health check."""
        manager = LifecycleManager()
        manager.register_connection("conn_1")
        
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(side_effect=Exception("Connection lost"))
        
        health = await manager.check_health("conn_1", mock_conn)
        assert health == ConnectionHealth.UNHEALTHY
        
    @pytest.mark.asyncio
    async def test_check_health_timeout(self):
        """Test health check timeout."""
        manager = LifecycleManager(LifecycleConfig(health_check_timeout=0.01))
        manager.register_connection("conn_1")
        
        async def slow_query(*args):
            await asyncio.sleep(1)
            return 1
            
        mock_conn = AsyncMock()
        mock_conn.fetchval = slow_query
        
        health = await manager.check_health("conn_1", mock_conn)
        assert health == ConnectionHealth.UNHEALTHY
        
    @pytest.mark.asyncio
    async def test_check_all_health(self):
        """Test checking health of multiple connections."""
        # health_check_interval=1 enables health checks (0 disables them)
        manager = LifecycleManager(LifecycleConfig(health_check_interval=1))
        manager.register_connection("conn_1")
        manager.register_connection("conn_2")
        
        mock_conn1 = AsyncMock()
        mock_conn1.fetchval = AsyncMock(return_value=1)
        mock_conn2 = AsyncMock()
        mock_conn2.fetchval = AsyncMock(side_effect=Exception("Failed"))
        
        unhealthy = await manager.check_all_health({
            "conn_1": mock_conn1,
            "conn_2": mock_conn2,
        })
        
        assert "conn_2" in unhealthy
        assert "conn_1" not in unhealthy
        
    def test_select_for_retirement(self):
        """Test selecting connections for retirement."""
        manager = LifecycleManager()
        manager.register_connection("conn_1")
        manager.register_connection("conn_2")
        manager.request_retirement("conn_1", RetirementReason.MANUAL)
        
        selected = manager.select_for_retirement(exclude_busy=set(), count=1)
        assert "conn_1" in selected
        
    def test_select_for_retirement_exclude_busy(self):
        """Test excluding busy connections from retirement."""
        manager = LifecycleManager()
        manager.register_connection("conn_1")
        manager.register_connection("conn_2")
        manager.request_retirement("conn_1", RetirementReason.MANUAL)
        
        selected = manager.select_for_retirement(exclude_busy={"conn_1"}, count=1)
        assert "conn_1" not in selected
        
    def test_get_stats(self):
        """Test getting lifecycle statistics."""
        manager = LifecycleManager()
        stats = manager.get_stats()
        assert isinstance(stats, LifecycleStats)
        
    def test_repr(self):
        """Test string representation."""
        manager = LifecycleManager()
        repr_str = repr(manager)
        assert "LifecycleManager" in repr_str

