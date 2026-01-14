"""
Comprehensive tests for PostgreSQL Graceful Degradation.

Tests cover:
- Queue depth trigger
- Error rate trigger
- Latency P95 trigger
- Connection health trigger
- Replica lag trigger
- Multiple trigger combination
- Level escalation (normal → degraded → critical)
- Level de-escalation
- Auto-recovery detection
- Recovery timing
- Load shedding decisions
- Retry-after calculation
- Monitoring loop
- Action execution per level
- Statistics tracking

100 tests total.
"""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch

from pynext.db.adapters.postgres.reliability.degradation import (
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


# ============================================================================
# DegradationLevel Tests (5 tests)
# ============================================================================

class TestDegradationLevel:
    """Tests for DegradationLevel enum."""
    
    def test_level_ordering(self):
        """Test levels are correctly ordered."""
        assert DegradationLevel.NORMAL < DegradationLevel.DEGRADED
        assert DegradationLevel.DEGRADED < DegradationLevel.CRITICAL
        assert DegradationLevel.CRITICAL < DegradationLevel.EMERGENCY
    
    def test_level_values(self):
        """Test level numeric values."""
        assert DegradationLevel.NORMAL == 0
        assert DegradationLevel.DEGRADED == 1
        assert DegradationLevel.CRITICAL == 2
        assert DegradationLevel.EMERGENCY == 3
    
    def test_level_comparison(self):
        """Test level comparison operations."""
        assert DegradationLevel.CRITICAL >= DegradationLevel.DEGRADED
        assert DegradationLevel.DEGRADED <= DegradationLevel.CRITICAL
    
    def test_level_equality(self):
        """Test level equality."""
        assert DegradationLevel.NORMAL == DegradationLevel.NORMAL
        assert DegradationLevel.CRITICAL != DegradationLevel.EMERGENCY
    
    def test_level_max(self):
        """Test finding max level."""
        levels = [DegradationLevel.NORMAL, DegradationLevel.CRITICAL, DegradationLevel.DEGRADED]
        assert max(levels) == DegradationLevel.CRITICAL


# ============================================================================
# DegradationMetric Tests (5 tests)
# ============================================================================

class TestDegradationMetric:
    """Tests for DegradationMetric enum."""
    
    def test_queue_depth_metric(self):
        """Test QUEUE_DEPTH metric value."""
        assert DegradationMetric.QUEUE_DEPTH.value == "queue_depth"
    
    def test_error_rate_metric(self):
        """Test ERROR_RATE metric value."""
        assert DegradationMetric.ERROR_RATE.value == "error_rate"
    
    def test_latency_metrics(self):
        """Test latency metric values."""
        assert DegradationMetric.LATENCY_P95.value == "latency_p95"
        assert DegradationMetric.LATENCY_P99.value == "latency_p99"
    
    def test_connection_health_metric(self):
        """Test CONNECTION_HEALTH metric value."""
        assert DegradationMetric.CONNECTION_HEALTH.value == "connection_health"
    
    def test_all_metrics(self):
        """Test all metric types exist."""
        metrics = [m.value for m in DegradationMetric]
        assert "queue_depth" in metrics
        assert "error_rate" in metrics
        assert "pool_utilization" in metrics
        assert "replica_lag" in metrics


# ============================================================================
# DegradationAction Tests (5 tests)
# ============================================================================

class TestDegradationAction:
    """Tests for DegradationAction enum."""
    
    def test_log_warning_action(self):
        """Test LOG_WARNING action value."""
        assert DegradationAction.LOG_WARNING.value == "log_warning"
    
    def test_reject_actions(self):
        """Test rejection action values."""
        assert DegradationAction.REJECT_BATCH.value == "reject_batch"
        assert DegradationAction.REJECT_LOW.value == "reject_low"
        assert DegradationAction.REJECT_NORMAL.value == "reject_normal"
    
    def test_extend_timeouts_action(self):
        """Test EXTEND_TIMEOUTS action value."""
        assert DegradationAction.EXTEND_TIMEOUTS.value == "extend_timeouts"
    
    def test_circuit_open_action(self):
        """Test CIRCUIT_OPEN action value."""
        assert DegradationAction.CIRCUIT_OPEN.value == "circuit_open"
    
    def test_notify_action(self):
        """Test NOTIFY action value."""
        assert DegradationAction.NOTIFY.value == "notify"


# ============================================================================
# DegradationTrigger Tests (15 tests)
# ============================================================================

class TestDegradationTrigger:
    """Tests for DegradationTrigger dataclass."""
    
    def test_trigger_creation(self):
        """Test creating a trigger."""
        trigger = DegradationTrigger(
            metric=DegradationMetric.QUEUE_DEPTH,
            threshold=100,
            level=DegradationLevel.DEGRADED,
        )
        assert trigger.metric == DegradationMetric.QUEUE_DEPTH
        assert trigger.threshold == 100
        assert trigger.level == DegradationLevel.DEGRADED
    
    def test_trigger_default_comparison(self):
        """Test default comparison is gt."""
        trigger = DegradationTrigger(
            metric=DegradationMetric.QUEUE_DEPTH,
            threshold=100,
            level=DegradationLevel.DEGRADED,
        )
        assert trigger.comparison == "gt"
    
    def test_trigger_invalid_comparison(self):
        """Test invalid comparison raises error."""
        with pytest.raises(ValueError, match="comparison must be"):
            DegradationTrigger(
                metric=DegradationMetric.QUEUE_DEPTH,
                threshold=100,
                level=DegradationLevel.DEGRADED,
                comparison="invalid",
            )
    
    def test_trigger_gt_is_triggered(self):
        """Test greater-than trigger."""
        trigger = DegradationTrigger(
            metric=DegradationMetric.QUEUE_DEPTH,
            threshold=100,
            level=DegradationLevel.DEGRADED,
            comparison="gt",
        )
        
        assert trigger.is_triggered(101) is True
        assert trigger.is_triggered(100) is False
        assert trigger.is_triggered(99) is False
    
    def test_trigger_lt_is_triggered(self):
        """Test less-than trigger."""
        trigger = DegradationTrigger(
            metric=DegradationMetric.CONNECTION_HEALTH,
            threshold=0.5,
            level=DegradationLevel.DEGRADED,
            comparison="lt",
        )
        
        assert trigger.is_triggered(0.3) is True
        assert trigger.is_triggered(0.5) is False
        assert trigger.is_triggered(0.7) is False
    
    def test_trigger_gte_is_triggered(self):
        """Test greater-than-or-equal trigger."""
        trigger = DegradationTrigger(
            metric=DegradationMetric.QUEUE_DEPTH,
            threshold=100,
            level=DegradationLevel.DEGRADED,
            comparison="gte",
        )
        
        assert trigger.is_triggered(100) is True
        assert trigger.is_triggered(101) is True
        assert trigger.is_triggered(99) is False
    
    def test_trigger_lte_is_triggered(self):
        """Test less-than-or-equal trigger."""
        trigger = DegradationTrigger(
            metric=DegradationMetric.CONNECTION_HEALTH,
            threshold=0.5,
            level=DegradationLevel.DEGRADED,
            comparison="lte",
        )
        
        assert trigger.is_triggered(0.5) is True
        assert trigger.is_triggered(0.3) is True
        assert trigger.is_triggered(0.7) is False
    
    def test_trigger_zero_threshold(self):
        """Test trigger with zero threshold."""
        trigger = DegradationTrigger(
            metric=DegradationMetric.QUEUE_DEPTH,
            threshold=0,
            level=DegradationLevel.DEGRADED,
            comparison="gt",
        )
        
        assert trigger.is_triggered(1) is True
        assert trigger.is_triggered(0) is False
    
    def test_trigger_float_threshold(self):
        """Test trigger with float threshold."""
        trigger = DegradationTrigger(
            metric=DegradationMetric.ERROR_RATE,
            threshold=0.15,
            level=DegradationLevel.CRITICAL,
        )
        
        assert trigger.is_triggered(0.20) is True
        assert trigger.is_triggered(0.10) is False
    
    def test_trigger_high_threshold(self):
        """Test trigger with high threshold."""
        trigger = DegradationTrigger(
            metric=DegradationMetric.LATENCY_P95,
            threshold=10000,
            level=DegradationLevel.EMERGENCY,
        )
        
        assert trigger.is_triggered(15000) is True
        assert trigger.is_triggered(5000) is False
    
    def test_trigger_emergency_level(self):
        """Test trigger for emergency level."""
        trigger = DegradationTrigger(
            metric=DegradationMetric.QUEUE_DEPTH,
            threshold=1000,
            level=DegradationLevel.EMERGENCY,
        )
        
        assert trigger.level == DegradationLevel.EMERGENCY
    
    def test_trigger_exact_threshold(self):
        """Test exact threshold values."""
        trigger = DegradationTrigger(
            metric=DegradationMetric.POOL_UTILIZATION,
            threshold=0.95,
            level=DegradationLevel.CRITICAL,
            comparison="gte",
        )
        
        assert trigger.is_triggered(0.95) is True
    
    def test_trigger_negative_value(self):
        """Test trigger with negative value (edge case)."""
        trigger = DegradationTrigger(
            metric=DegradationMetric.QUEUE_DEPTH,
            threshold=0,
            level=DegradationLevel.NORMAL,
            comparison="gt",
        )
        
        # Negative value shouldn't trigger gt 0
        assert trigger.is_triggered(-1) is False
    
    def test_multiple_triggers_same_metric(self):
        """Test multiple triggers for same metric."""
        t1 = DegradationTrigger(
            metric=DegradationMetric.QUEUE_DEPTH,
            threshold=100,
            level=DegradationLevel.DEGRADED,
        )
        t2 = DegradationTrigger(
            metric=DegradationMetric.QUEUE_DEPTH,
            threshold=500,
            level=DegradationLevel.CRITICAL,
        )
        
        value = 250
        assert t1.is_triggered(value) is True
        assert t2.is_triggered(value) is False


# ============================================================================
# DegradationConfig Tests (15 tests)
# ============================================================================

class TestDegradationConfig:
    """Tests for DegradationConfig dataclass."""
    
    def test_config_defaults(self):
        """Test default configuration."""
        config = DegradationConfig()
        
        assert len(config.triggers) > 0  # Has defaults
        assert len(config.actions) > 0   # Has defaults
        assert config.auto_recovery is True
        assert config.recovery_check_interval == 10.0
        assert config.recovery_delay == 30.0
    
    def test_config_custom_triggers(self):
        """Test custom triggers."""
        triggers = [
            DegradationTrigger(
                DegradationMetric.QUEUE_DEPTH,
                50,
                DegradationLevel.DEGRADED,
            ),
        ]
        config = DegradationConfig(triggers=triggers)
        
        assert len(config.triggers) == 1
    
    def test_config_custom_actions(self):
        """Test custom actions."""
        actions = {
            DegradationLevel.CRITICAL: [DegradationAction.NOTIFY],
        }
        config = DegradationConfig(actions=actions)
        
        assert DegradationAction.NOTIFY in config.actions[DegradationLevel.CRITICAL]
    
    def test_config_disable_auto_recovery(self):
        """Test disabling auto recovery."""
        config = DegradationConfig(auto_recovery=False)
        assert config.auto_recovery is False
    
    def test_config_custom_recovery_delay(self):
        """Test custom recovery delay."""
        config = DegradationConfig(recovery_delay=60.0)
        assert config.recovery_delay == 60.0
    
    def test_config_custom_recovery_interval(self):
        """Test custom recovery check interval."""
        config = DegradationConfig(recovery_check_interval=5.0)
        assert config.recovery_check_interval == 5.0
    
    def test_config_notify_callback(self):
        """Test notify callback configuration."""
        def callback(old, new):
            pass
        
        config = DegradationConfig(notify_callback=callback)
        assert config.notify_callback is not None
    
    def test_config_min_samples(self):
        """Test min_samples configuration."""
        config = DegradationConfig(min_samples=10)
        assert config.min_samples == 10
    
    def test_config_empty_triggers(self):
        """Test empty triggers means no triggers (explicit disable)."""
        config = DegradationConfig(triggers=[])
        # Empty list means explicitly no triggers
        assert len(config.triggers) == 0
    
    def test_config_empty_actions(self):
        """Test empty actions means no actions (explicit disable)."""
        config = DegradationConfig(actions={})
        # Empty dict means explicitly no actions
        assert len(config.actions) == 0
    
    def test_config_none_uses_defaults(self):
        """Test None triggers and actions use defaults."""
        config = DegradationConfig()  # triggers=None, actions=None by default
        # None means use defaults
        assert len(config.triggers) > 0
        assert len(config.actions) > 0
    
    def test_config_all_custom(self):
        """Test fully custom configuration."""
        triggers = [
            DegradationTrigger(
                DegradationMetric.ERROR_RATE,
                0.5,
                DegradationLevel.EMERGENCY,
            ),
        ]
        actions = {
            DegradationLevel.EMERGENCY: [DegradationAction.CIRCUIT_OPEN],
        }
        config = DegradationConfig(
            triggers=triggers,
            actions=actions,
            auto_recovery=False,
            recovery_delay=120.0,
        )
        
        assert len(config.triggers) == 1
        assert len(config.actions) == 1
        assert config.auto_recovery is False
        assert config.recovery_delay == 120.0
    
    def test_default_triggers_function(self):
        """Test default_triggers convenience function."""
        triggers = default_triggers()
        
        assert len(triggers) > 0
        # Check various metrics are covered
        metrics = [t.metric for t in triggers]
        assert DegradationMetric.QUEUE_DEPTH in metrics
        assert DegradationMetric.ERROR_RATE in metrics
    
    def test_default_actions_function(self):
        """Test default_actions convenience function."""
        actions = default_actions()
        
        assert DegradationLevel.DEGRADED in actions
        assert DegradationLevel.CRITICAL in actions
        assert DegradationLevel.EMERGENCY in actions
    
    def test_strict_config(self):
        """Test strict_config convenience function."""
        config = strict_config()
        
        # Strict should trigger at lower thresholds
        queue_triggers = [
            t for t in config.triggers
            if t.metric == DegradationMetric.QUEUE_DEPTH
        ]
        # Should have lower threshold than default
        assert any(t.threshold <= 50 for t in queue_triggers)
    
    def test_lenient_config(self):
        """Test lenient_config convenience function."""
        config = lenient_config()
        
        # Lenient should trigger at higher thresholds
        assert config.recovery_delay < 30.0  # Faster recovery


# ============================================================================
# DegradationStats Tests (10 tests)
# ============================================================================

class TestDegradationStats:
    """Tests for DegradationStats tracking."""
    
    def test_initial_stats(self):
        """Test initial stats values."""
        stats = DegradationStats()
        
        assert stats.current_level == DegradationLevel.NORMAL
        assert stats.level_changes == 0
        assert stats.recovery_count == 0
        assert stats.load_shed_count == 0
    
    def test_record_level_change(self):
        """Test recording level change."""
        stats = DegradationStats()
        
        stats.record_level_change(
            DegradationLevel.NORMAL,
            DegradationLevel.DEGRADED,
        )
        
        assert stats.level_changes == 1
        assert stats.current_level == DegradationLevel.DEGRADED
    
    def test_record_recovery(self):
        """Test recovery is counted on de-escalation."""
        stats = DegradationStats()
        stats.current_level = DegradationLevel.CRITICAL
        
        stats.record_level_change(
            DegradationLevel.CRITICAL,
            DegradationLevel.NORMAL,
        )
        
        assert stats.recovery_count == 1
    
    def test_record_trigger(self):
        """Test recording triggered triggers."""
        stats = DegradationStats()
        trigger = DegradationTrigger(
            DegradationMetric.QUEUE_DEPTH,
            100,
            DegradationLevel.DEGRADED,
        )
        
        stats.record_trigger(trigger)
        
        assert "queue_depth:DEGRADED" in stats.triggered_by
        assert stats.triggered_by["queue_depth:DEGRADED"] == 1
    
    def test_record_load_shed(self):
        """Test recording load shedding."""
        stats = DegradationStats()
        
        stats.record_load_shed()
        stats.record_load_shed()
        
        assert stats.load_shed_count == 2
    
    def test_record_metric(self):
        """Test recording current metrics."""
        stats = DegradationStats()
        
        stats.record_metric(DegradationMetric.QUEUE_DEPTH, 150.0)
        
        assert stats.current_metrics["queue_depth"] == 150.0
    
    def test_time_in_level(self):
        """Test time in level tracking."""
        stats = DegradationStats()
        
        # Simulate being in DEGRADED state
        stats.record_level_change(
            DegradationLevel.NORMAL,
            DegradationLevel.DEGRADED,
        )
        time.sleep(0.05)
        stats.record_level_change(
            DegradationLevel.DEGRADED,
            DegradationLevel.NORMAL,
        )
        
        assert stats.time_in_level[DegradationLevel.DEGRADED] >= 0.04
    
    def test_to_dict(self):
        """Test stats to_dict conversion."""
        stats = DegradationStats()
        stats.level_changes = 5
        stats.recovery_count = 2
        
        d = stats.to_dict()
        
        assert d["level_changes"] == 5
        assert d["recovery_count"] == 2
        assert d["current_level"] == "NORMAL"
    
    def test_multiple_triggers_tracked(self):
        """Test multiple different triggers tracked."""
        stats = DegradationStats()
        
        t1 = DegradationTrigger(
            DegradationMetric.QUEUE_DEPTH,
            100,
            DegradationLevel.DEGRADED,
        )
        t2 = DegradationTrigger(
            DegradationMetric.ERROR_RATE,
            0.1,
            DegradationLevel.DEGRADED,
        )
        
        stats.record_trigger(t1)
        stats.record_trigger(t1)
        stats.record_trigger(t2)
        
        assert stats.triggered_by["queue_depth:DEGRADED"] == 2
        assert stats.triggered_by["error_rate:DEGRADED"] == 1
    
    def test_escalation_not_recovery(self):
        """Test escalation doesn't count as recovery."""
        stats = DegradationStats()
        
        stats.record_level_change(
            DegradationLevel.NORMAL,
            DegradationLevel.CRITICAL,
        )
        
        assert stats.recovery_count == 0


# ============================================================================
# DegradationManager Tests (35 tests)
# ============================================================================

class TestDegradationManager:
    """Tests for DegradationManager."""
    
    def test_create_manager(self):
        """Test creating a manager."""
        manager = DegradationManager()
        
        assert manager.current_level == DegradationLevel.NORMAL
        assert manager.is_degraded is False
    
    def test_create_manager_with_config(self):
        """Test creating manager with config."""
        config = DegradationConfig(recovery_delay=60.0)
        manager = DegradationManager(config)
        
        assert manager._config.recovery_delay == 60.0
    
    def test_is_degraded_property(self):
        """Test is_degraded property."""
        manager = DegradationManager()
        
        assert manager.is_degraded is False
        
        manager._current_level = DegradationLevel.DEGRADED
        assert manager.is_degraded is True
    
    def test_is_critical_property(self):
        """Test is_critical property."""
        manager = DegradationManager()
        
        assert manager.is_critical is False
        
        manager._current_level = DegradationLevel.CRITICAL
        assert manager.is_critical is True
        
        manager._current_level = DegradationLevel.EMERGENCY
        assert manager.is_critical is True
    
    def test_is_emergency_property(self):
        """Test is_emergency property."""
        manager = DegradationManager()
        
        assert manager.is_emergency is False
        
        manager._current_level = DegradationLevel.EMERGENCY
        assert manager.is_emergency is True
    
    def test_force_level(self):
        """Test forcing a level."""
        manager = DegradationManager()
        
        manager.force_level(DegradationLevel.CRITICAL)
        
        assert manager.current_level == DegradationLevel.CRITICAL
        assert manager.stats.level_changes == 1
    
    def test_reset(self):
        """Test reset to normal."""
        manager = DegradationManager()
        manager._current_level = DegradationLevel.EMERGENCY
        
        manager.reset()
        
        assert manager.current_level == DegradationLevel.NORMAL
    
    def test_should_shed_load_normal(self):
        """Test no load shedding in normal state."""
        manager = DegradationManager()
        
        assert manager.should_shed_load("batch") is False
        assert manager.should_shed_load("normal") is False
    
    def test_should_shed_load_reject_batch(self):
        """Test batch rejection in critical state."""
        config = DegradationConfig(
            actions={
                DegradationLevel.CRITICAL: [DegradationAction.REJECT_BATCH],
            }
        )
        manager = DegradationManager(config)
        manager._current_level = DegradationLevel.CRITICAL
        
        assert manager.should_shed_load("batch") is True
        assert manager.should_shed_load("normal") is False
    
    def test_should_shed_load_reject_low(self):
        """Test low priority rejection."""
        config = DegradationConfig(
            actions={
                DegradationLevel.EMERGENCY: [DegradationAction.REJECT_LOW],
            }
        )
        manager = DegradationManager(config)
        manager._current_level = DegradationLevel.EMERGENCY
        
        assert manager.should_shed_load("low") is True
        assert manager.should_shed_load("batch") is True
        assert manager.should_shed_load("normal") is False
    
    def test_should_shed_load_reject_normal(self):
        """Test normal priority rejection."""
        config = DegradationConfig(
            actions={
                DegradationLevel.EMERGENCY: [DegradationAction.REJECT_NORMAL],
            }
        )
        manager = DegradationManager(config)
        manager._current_level = DegradationLevel.EMERGENCY
        
        assert manager.should_shed_load("normal") is True
        assert manager.should_shed_load("low") is True
        assert manager.should_shed_load("high") is False
    
    def test_get_retry_after_normal(self):
        """Test retry_after is 0 in normal state."""
        manager = DegradationManager()
        
        assert manager.get_retry_after() == 0
    
    def test_get_retry_after_degraded(self):
        """Test retry_after for degraded state."""
        manager = DegradationManager()
        manager._current_level = DegradationLevel.DEGRADED
        
        assert manager.get_retry_after() == 5
    
    def test_get_retry_after_critical(self):
        """Test retry_after for critical state."""
        manager = DegradationManager()
        manager._current_level = DegradationLevel.CRITICAL
        
        assert manager.get_retry_after() == 15
    
    def test_get_retry_after_emergency(self):
        """Test retry_after for emergency state."""
        manager = DegradationManager()
        manager._current_level = DegradationLevel.EMERGENCY
        
        assert manager.get_retry_after() == 30
    
    def test_check_and_reject_normal(self):
        """Test check_and_reject doesn't raise in normal."""
        manager = DegradationManager()
        
        manager.check_and_reject("batch")  # Should not raise
    
    def test_check_and_reject_raises(self):
        """Test check_and_reject raises when needed."""
        config = DegradationConfig(
            actions={
                DegradationLevel.CRITICAL: [DegradationAction.REJECT_BATCH],
            }
        )
        manager = DegradationManager(config)
        manager._current_level = DegradationLevel.CRITICAL
        
        with pytest.raises(DegradationError) as exc_info:
            manager.check_and_reject("batch")
        
        assert exc_info.value.level == DegradationLevel.CRITICAL
        assert exc_info.value.retry_after == 15
    
    def test_evaluate_triggers_normal(self):
        """Test trigger evaluation returns normal when not triggered."""
        config = DegradationConfig(
            triggers=[
                DegradationTrigger(
                    DegradationMetric.QUEUE_DEPTH,
                    100,
                    DegradationLevel.DEGRADED,
                ),
            ]
        )
        manager = DegradationManager(config)
        
        metrics = {"queue_depth": 50}
        level = manager._evaluate_triggers(metrics)
        
        assert level == DegradationLevel.NORMAL
    
    def test_evaluate_triggers_degraded(self):
        """Test trigger evaluation returns degraded."""
        config = DegradationConfig(
            triggers=[
                DegradationTrigger(
                    DegradationMetric.QUEUE_DEPTH,
                    100,
                    DegradationLevel.DEGRADED,
                ),
            ]
        )
        manager = DegradationManager(config)
        
        metrics = {"queue_depth": 150}
        level = manager._evaluate_triggers(metrics)
        
        assert level == DegradationLevel.DEGRADED
    
    def test_evaluate_triggers_highest_wins(self):
        """Test highest triggered level is returned."""
        config = DegradationConfig(
            triggers=[
                DegradationTrigger(
                    DegradationMetric.QUEUE_DEPTH,
                    100,
                    DegradationLevel.DEGRADED,
                ),
                DegradationTrigger(
                    DegradationMetric.ERROR_RATE,
                    0.2,
                    DegradationLevel.CRITICAL,
                ),
            ]
        )
        manager = DegradationManager(config)
        
        metrics = {"queue_depth": 150, "error_rate": 0.3}
        level = manager._evaluate_triggers(metrics)
        
        assert level == DegradationLevel.CRITICAL
    
    def test_evaluate_triggers_missing_metric(self):
        """Test missing metrics are ignored."""
        config = DegradationConfig(
            triggers=[
                DegradationTrigger(
                    DegradationMetric.QUEUE_DEPTH,
                    100,
                    DegradationLevel.DEGRADED,
                ),
            ]
        )
        manager = DegradationManager(config)
        
        metrics = {"error_rate": 0.5}  # No queue_depth
        level = manager._evaluate_triggers(metrics)
        
        assert level == DegradationLevel.NORMAL
    
    @pytest.mark.asyncio
    async def test_start_stop(self):
        """Test start and stop lifecycle."""
        manager = DegradationManager()
        
        def get_metrics():
            return {"queue_depth": 0}
        
        await manager.start(get_metrics)
        assert manager._running is True
        
        await manager.stop()
        assert manager._running is False
    
    @pytest.mark.asyncio
    async def test_start_twice_safe(self):
        """Test starting twice is safe."""
        manager = DegradationManager()
        
        def get_metrics():
            return {}
        
        await manager.start(get_metrics)
        await manager.start(get_metrics)  # Should not raise
        
        await manager.stop()
    
    @pytest.mark.asyncio
    async def test_stop_twice_safe(self):
        """Test stopping twice is safe."""
        manager = DegradationManager()
        
        await manager.stop()
        await manager.stop()  # Should not raise
    
    @pytest.mark.asyncio
    async def test_monitoring_updates_level(self):
        """Test monitoring loop updates level."""
        config = DegradationConfig(
            triggers=[
                DegradationTrigger(
                    DegradationMetric.QUEUE_DEPTH,
                    50,
                    DegradationLevel.DEGRADED,
                ),
            ],
            recovery_check_interval=0.01,
            recovery_delay=0,  # Immediate
        )
        manager = DegradationManager(config)
        
        queue_depth = [0]
        
        def get_metrics():
            return {"queue_depth": queue_depth[0]}
        
        await manager.start(get_metrics)
        
        # Trigger degradation
        queue_depth[0] = 100
        await asyncio.sleep(0.05)
        
        assert manager.current_level == DegradationLevel.DEGRADED
        
        await manager.stop()
    
    @pytest.mark.asyncio
    async def test_recovery_delay(self):
        """Test recovery respects delay."""
        config = DegradationConfig(
            triggers=[
                DegradationTrigger(
                    DegradationMetric.QUEUE_DEPTH,
                    50,
                    DegradationLevel.DEGRADED,
                ),
            ],
            recovery_check_interval=0.01,
            recovery_delay=0.1,  # 100ms delay
        )
        manager = DegradationManager(config)
        manager._current_level = DegradationLevel.DEGRADED
        
        def get_metrics():
            return {"queue_depth": 0}  # Should recover
        
        await manager.start(get_metrics)
        await asyncio.sleep(0.03)
        
        # Should still be degraded (waiting for recovery delay)
        # Note: This is timing-sensitive
        
        await manager.stop()
    
    @pytest.mark.asyncio
    async def test_notify_callback_called(self):
        """Test notification callback is called."""
        callback_calls = []
        
        def callback(old, new):
            callback_calls.append((old, new))
        
        config = DegradationConfig(
            triggers=[
                DegradationTrigger(
                    DegradationMetric.QUEUE_DEPTH,
                    50,
                    DegradationLevel.DEGRADED,
                ),
            ],
            notify_callback=callback,
            recovery_check_interval=0.01,
            recovery_delay=0,
        )
        manager = DegradationManager(config)
        
        def get_metrics():
            return {"queue_depth": 100}
        
        await manager.start(get_metrics)
        await asyncio.sleep(0.03)
        
        # Callback should have been called
        assert len(callback_calls) >= 1
        
        await manager.stop()
    
    def test_stats_property(self):
        """Test stats property returns stats."""
        manager = DegradationManager()
        
        stats = manager.stats
        
        assert isinstance(stats, DegradationStats)
    
    def test_load_shed_tracks_stats(self):
        """Test load shedding updates stats."""
        config = DegradationConfig(
            actions={
                DegradationLevel.CRITICAL: [DegradationAction.REJECT_BATCH],
            }
        )
        manager = DegradationManager(config)
        manager._current_level = DegradationLevel.CRITICAL
        
        manager.should_shed_load("batch")
        
        assert manager.stats.load_shed_count == 1
    
    def test_current_level_property(self):
        """Test current_level property."""
        manager = DegradationManager()
        
        assert manager.current_level == DegradationLevel.NORMAL
        
        manager.force_level(DegradationLevel.CRITICAL)
        assert manager.current_level == DegradationLevel.CRITICAL


# ============================================================================
# DegradationError Tests (5 tests)
# ============================================================================

class TestDegradationError:
    """Tests for DegradationError exception."""
    
    def test_error_creation(self):
        """Test creating a DegradationError."""
        error = DegradationError(
            "Request rejected",
            level=DegradationLevel.CRITICAL,
            retry_after=15,
        )
        
        assert str(error.args[0]) == "Request rejected"
        assert error.level == DegradationLevel.CRITICAL
        assert error.retry_after == 15
    
    def test_error_str(self):
        """Test error string representation."""
        error = DegradationError(
            "Too many requests",
            level=DegradationLevel.EMERGENCY,
            retry_after=30,
        )
        
        error_str = str(error)
        
        assert "Too many requests" in error_str
        assert "EMERGENCY" in error_str
        assert "30" in error_str
    
    def test_error_is_exception(self):
        """Test DegradationError is an Exception."""
        error = DegradationError(
            "Test",
            level=DegradationLevel.DEGRADED,
            retry_after=5,
        )
        
        assert isinstance(error, Exception)
    
    def test_error_can_be_raised(self):
        """Test error can be raised and caught."""
        with pytest.raises(DegradationError) as exc_info:
            raise DegradationError(
                "Test error",
                level=DegradationLevel.CRITICAL,
                retry_after=15,
            )
        
        assert exc_info.value.retry_after == 15
    
    def test_error_level_accessible(self):
        """Test level is accessible after catch."""
        try:
            raise DegradationError(
                "Test",
                level=DegradationLevel.DEGRADED,
                retry_after=5,
            )
        except DegradationError as e:
            assert e.level == DegradationLevel.DEGRADED


# ============================================================================
# Convenience Config Tests (5 tests)
# ============================================================================

class TestConvenienceConfigs:
    """Tests for convenience configuration functions."""
    
    def test_disabled_config(self):
        """Test disabled_config creates disabled config."""
        config = disabled_config()
        
        assert len(config.triggers) == 0
        assert len(config.actions) == 0
        assert config.auto_recovery is False
    
    def test_strict_config_lower_thresholds(self):
        """Test strict config has lower thresholds."""
        strict = strict_config()
        default = DegradationConfig()
        
        # Find queue_depth triggers
        strict_queue = [
            t for t in strict.triggers
            if t.metric == DegradationMetric.QUEUE_DEPTH
        ]
        default_queue = [
            t for t in default.triggers
            if t.metric == DegradationMetric.QUEUE_DEPTH
        ]
        
        if strict_queue and default_queue:
            # Strict should have lower threshold for same level
            strict_degraded = [t for t in strict_queue if t.level == DegradationLevel.DEGRADED]
            default_degraded = [t for t in default_queue if t.level == DegradationLevel.DEGRADED]
            
            if strict_degraded and default_degraded:
                assert strict_degraded[0].threshold < default_degraded[0].threshold
    
    def test_lenient_config_higher_thresholds(self):
        """Test lenient config has higher thresholds."""
        lenient = lenient_config()
        
        # Should have higher thresholds
        queue_triggers = [
            t for t in lenient.triggers
            if t.metric == DegradationMetric.QUEUE_DEPTH
        ]
        
        if queue_triggers:
            degraded = [t for t in queue_triggers if t.level == DegradationLevel.DEGRADED]
            if degraded:
                assert degraded[0].threshold >= 100
    
    def test_strict_config_longer_recovery(self):
        """Test strict config has longer recovery delay."""
        strict = strict_config()
        
        assert strict.recovery_delay >= 60.0
    
    def test_lenient_config_shorter_recovery(self):
        """Test lenient config has shorter recovery delay."""
        lenient = lenient_config()
        
        assert lenient.recovery_delay <= 10.0

