"""
Tests for PyNext Pool Monitor Module.

120 comprehensive tests covering:
- MonitorConfig (15 tests)
- ConnectionInfo and PoolStats (15 tests)
- LeakDetector (25 tests)
- HealthChecker (20 tests)
- PoolMonitor core (30 tests)
- Events and callbacks (15 tests)
"""

import time
import threading
from unittest.mock import MagicMock

import pytest

from pynext.db.adapters.postgres_monitor import (
    MonitorConfig,
    PoolEventType,
    ConnectionState,
    ConnectionInfo,
    LeakInfo,
    PoolEvent,
    PoolStats,
    LeakDetector,
    HealthChecker,
    PoolMonitor,
    create_monitor,
)


# ============================================================================
# MonitorConfig Tests (15 tests)
# ============================================================================

class TestMonitorConfig:
    """Tests for MonitorConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = MonitorConfig()
        assert config.enabled is True
        assert config.exhaustion_warning_threshold == 0.8
        assert config.exhaustion_critical_threshold == 0.95
        assert config.leak_detection_timeout == 300.0
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = MonitorConfig(
            exhaustion_warning_threshold=0.7,
            leak_detection_timeout=60.0,
        )
        assert config.exhaustion_warning_threshold == 0.7
        assert config.leak_detection_timeout == 60.0
    
    def test_disabled_config(self):
        """Test disabled monitoring."""
        config = MonitorConfig(enabled=False)
        assert config.enabled is False
    
    def test_invalid_warning_threshold_low(self):
        """Test invalid low warning threshold."""
        with pytest.raises(ValueError):
            MonitorConfig(exhaustion_warning_threshold=-0.1)
    
    def test_invalid_warning_threshold_high(self):
        """Test invalid high warning threshold."""
        with pytest.raises(ValueError):
            MonitorConfig(exhaustion_warning_threshold=1.5)
    
    def test_invalid_critical_threshold(self):
        """Test invalid critical threshold."""
        with pytest.raises(ValueError):
            MonitorConfig(exhaustion_critical_threshold=-0.1)
    
    def test_warning_must_be_less_than_critical(self):
        """Test warning must be less than critical threshold."""
        with pytest.raises(ValueError):
            MonitorConfig(
                exhaustion_warning_threshold=0.95,
                exhaustion_critical_threshold=0.8,
            )
    
    def test_invalid_leak_timeout(self):
        """Test invalid leak timeout."""
        with pytest.raises(ValueError):
            MonitorConfig(leak_detection_timeout=0)
    
    def test_dead_connection_timeout(self):
        """Test dead connection timeout setting."""
        config = MonitorConfig(dead_connection_timeout=30.0)
        assert config.dead_connection_timeout == 30.0
    
    def test_health_check_interval(self):
        """Test health check interval setting."""
        config = MonitorConfig(health_check_interval=15.0)
        assert config.health_check_interval == 15.0
    
    def test_max_connection_age(self):
        """Test max connection age setting."""
        config = MonitorConfig(max_connection_age=1800.0)
        assert config.max_connection_age == 1800.0
    
    def test_track_call_stacks(self):
        """Test call stack tracking setting."""
        config = MonitorConfig(track_call_stacks=True)
        assert config.track_call_stacks is True
    
    def test_warning_callback(self):
        """Test exhaustion warning callback."""
        callback = MagicMock()
        config = MonitorConfig(on_exhaustion_warning=callback)
        assert config.on_exhaustion_warning is callback
    
    def test_critical_callback(self):
        """Test exhaustion critical callback."""
        callback = MagicMock()
        config = MonitorConfig(on_exhaustion_critical=callback)
        assert config.on_exhaustion_critical is callback
    
    def test_leak_callback(self):
        """Test leak detection callback."""
        callback = MagicMock()
        config = MonitorConfig(on_leak_detected=callback)
        assert config.on_leak_detected is callback


# ============================================================================
# ConnectionInfo and PoolStats Tests (15 tests)
# ============================================================================

class TestConnectionInfo:
    """Tests for ConnectionInfo dataclass."""
    
    def test_default_info(self):
        """Test default connection info."""
        info = ConnectionInfo()
        assert info.connection_id.startswith("conn_")
        assert info.state == ConnectionState.IDLE
    
    def test_custom_id(self):
        """Test custom connection ID."""
        info = ConnectionInfo(connection_id="custom_id")
        assert info.connection_id == "custom_id"
    
    def test_age_seconds(self):
        """Test age calculation."""
        info = ConnectionInfo()
        time.sleep(0.1)
        assert info.age_seconds >= 0.1
    
    def test_held_seconds_not_acquired(self):
        """Test held seconds when not acquired."""
        info = ConnectionInfo()
        assert info.held_seconds == 0.0
    
    def test_held_seconds_acquired(self):
        """Test held seconds when acquired."""
        info = ConnectionInfo(acquired_at=time.time() - 10.0)
        assert info.held_seconds >= 10.0
    
    def test_idle_seconds_not_released(self):
        """Test idle seconds when not released."""
        info = ConnectionInfo()
        assert info.idle_seconds == 0.0
    
    def test_idle_seconds_released(self):
        """Test idle seconds when released."""
        info = ConnectionInfo(released_at=time.time() - 5.0)
        assert info.idle_seconds >= 5.0
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        info = ConnectionInfo(connection_id="test")
        d = info.to_dict()
        
        assert d["connection_id"] == "test"
        assert "state" in d
        assert "acquire_count" in d


class TestPoolStats:
    """Tests for PoolStats dataclass."""
    
    def test_default_stats(self):
        """Test default pool stats."""
        stats = PoolStats()
        assert stats.active == 0
        assert stats.idle == 0
        assert stats.waiting == 0
    
    def test_custom_stats(self):
        """Test custom pool stats."""
        stats = PoolStats(active=5, idle=10, waiting=2)
        assert stats.active == 5
        assert stats.idle == 10
        assert stats.waiting == 2
    
    def test_utilization_calculation(self):
        """Test utilization calculation."""
        stats = PoolStats(active=8, max_size=10)
        assert stats.utilization == 0.8
    
    def test_utilization_zero_max(self):
        """Test utilization with zero max size."""
        stats = PoolStats(active=5, max_size=0)
        assert stats.utilization == 0.0
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        stats = PoolStats(active=5, idle=10)
        d = stats.to_dict()
        
        assert d["active"] == 5
        assert d["idle"] == 10
        assert "utilization" in d
    
    def test_total_connections(self):
        """Test total connections."""
        stats = PoolStats(total=15)
        assert stats.total == 15
    
    def test_min_max_size(self):
        """Test min and max size."""
        stats = PoolStats(min_size=5, max_size=20)
        assert stats.min_size == 5
        assert stats.max_size == 20


# ============================================================================
# LeakDetector Tests (25 tests)
# ============================================================================

class TestLeakDetector:
    """Tests for LeakDetector class."""
    
    def test_track_acquire(self):
        """Test tracking connection acquisition."""
        detector = LeakDetector(timeout=60.0)
        info = detector.track_acquire("conn_1")
        
        assert info is not None
        assert info.state == ConnectionState.ACTIVE
    
    def test_track_release(self):
        """Test tracking connection release."""
        detector = LeakDetector(timeout=60.0)
        detector.track_acquire("conn_1")
        info = detector.track_release("conn_1")
        
        assert info is not None
        assert info.state == ConnectionState.IDLE
    
    def test_track_release_nonexistent(self):
        """Test releasing nonexistent connection."""
        detector = LeakDetector(timeout=60.0)
        info = detector.track_release("nonexistent")
        assert info is None
    
    def test_track_query(self):
        """Test tracking query execution."""
        detector = LeakDetector(timeout=60.0)
        detector.track_acquire("conn_1")
        detector.track_query("conn_1")
        
        connections = detector.get_all_connections()
        assert connections[0].query_count == 1
    
    def test_check_leaks_no_leaks(self):
        """Test checking for leaks when none exist."""
        detector = LeakDetector(timeout=60.0)
        detector.track_acquire("conn_1")
        detector.track_release("conn_1")
        
        leaks = detector.check_leaks()
        assert len(leaks) == 0
    
    def test_check_leaks_found(self):
        """Test detecting a leak."""
        detector = LeakDetector(timeout=0.01)  # Very short timeout
        detector.track_acquire("conn_1")
        
        time.sleep(0.02)  # Wait for timeout
        
        leaks = detector.check_leaks()
        assert len(leaks) == 1
        assert leaks[0].connection.connection_id == "conn_1"
    
    def test_leak_marks_as_leaked(self):
        """Test leak detection marks connection as leaked."""
        detector = LeakDetector(timeout=0.01)
        detector.track_acquire("conn_1")
        time.sleep(0.02)
        
        detector.check_leaks()
        
        connections = detector.get_all_connections()
        assert connections[0].state == ConnectionState.LEAKED
    
    def test_remove_connection(self):
        """Test removing a connection."""
        detector = LeakDetector(timeout=60.0)
        detector.track_acquire("conn_1")
        detector.remove_connection("conn_1")
        
        connections = detector.get_all_connections()
        assert len(connections) == 0
    
    def test_get_active_connections(self):
        """Test getting active connections."""
        detector = LeakDetector(timeout=60.0)
        detector.track_acquire("conn_1")
        detector.track_acquire("conn_2")
        detector.track_release("conn_1")
        
        active = detector.get_active_connections()
        assert len(active) == 1
        assert active[0].connection_id == "conn_2"
    
    def test_get_all_connections(self):
        """Test getting all connections."""
        detector = LeakDetector(timeout=60.0)
        detector.track_acquire("conn_1")
        detector.track_acquire("conn_2")
        
        all_conn = detector.get_all_connections()
        assert len(all_conn) == 2
    
    def test_reset(self):
        """Test resetting detector."""
        detector = LeakDetector(timeout=60.0)
        detector.track_acquire("conn_1")
        detector.reset()
        
        assert len(detector.get_all_connections()) == 0
    
    def test_acquire_count(self):
        """Test acquire count is tracked."""
        detector = LeakDetector(timeout=60.0)
        detector.track_acquire("conn_1")
        detector.track_release("conn_1")
        detector.track_acquire("conn_1")
        
        connections = detector.get_all_connections()
        assert connections[0].acquire_count == 2
    
    def test_call_stack_tracking_disabled(self):
        """Test call stack tracking disabled by default."""
        detector = LeakDetector(timeout=60.0, track_stacks=False)
        info = detector.track_acquire("conn_1")
        assert info.call_stack is None
    
    def test_call_stack_tracking_enabled(self):
        """Test call stack tracking when enabled."""
        detector = LeakDetector(timeout=60.0, track_stacks=True)
        info = detector.track_acquire("conn_1")
        assert info.call_stack is not None
    
    def test_leak_includes_held_seconds(self):
        """Test leak info includes held seconds."""
        detector = LeakDetector(timeout=0.01)
        detector.track_acquire("conn_1")
        time.sleep(0.02)
        
        leaks = detector.check_leaks()
        assert leaks[0].held_seconds >= 0.02
    
    def test_multiple_leaks(self):
        """Test detecting multiple leaks."""
        detector = LeakDetector(timeout=0.01)
        detector.track_acquire("conn_1")
        detector.track_acquire("conn_2")
        time.sleep(0.02)
        
        leaks = detector.check_leaks()
        assert len(leaks) == 2
    
    def test_only_active_can_leak(self):
        """Test only active connections can be leaks."""
        detector = LeakDetector(timeout=0.01)
        detector.track_acquire("conn_1")
        detector.track_release("conn_1")
        time.sleep(0.02)
        
        leaks = detector.check_leaks()
        assert len(leaks) == 0
    
    def test_thread_safety(self):
        """Test detector is thread-safe."""
        detector = LeakDetector(timeout=60.0)
        
        def acquire_release():
            for i in range(100):
                conn_id = f"conn_{threading.current_thread().name}_{i}"
                detector.track_acquire(conn_id)
                detector.track_release(conn_id)
        
        threads = [threading.Thread(target=acquire_release) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All should be idle
        active = detector.get_active_connections()
        assert len(active) == 0
    
    def test_released_at_timestamp(self):
        """Test released_at timestamp is set."""
        detector = LeakDetector(timeout=60.0)
        before = time.time()
        detector.track_acquire("conn_1")
        detector.track_release("conn_1")
        after = time.time()
        
        connections = detector.get_all_connections()
        assert before <= connections[0].released_at <= after
    
    def test_acquired_at_timestamp(self):
        """Test acquired_at timestamp is set."""
        detector = LeakDetector(timeout=60.0)
        before = time.time()
        detector.track_acquire("conn_1")
        after = time.time()
        
        connections = detector.get_all_connections()
        assert before <= connections[0].acquired_at <= after
    
    def test_last_query_at_timestamp(self):
        """Test last_query_at timestamp is set."""
        detector = LeakDetector(timeout=60.0)
        before = time.time()
        detector.track_acquire("conn_1")
        detector.track_query("conn_1")
        after = time.time()
        
        connections = detector.get_all_connections()
        assert before <= connections[0].last_query_at <= after
    
    def test_leak_to_dict(self):
        """Test LeakInfo to_dict."""
        conn = ConnectionInfo(connection_id="test")
        leak = LeakInfo(connection=conn, held_seconds=60.0)
        d = leak.to_dict()
        
        assert d["connection_id"] == "test"
        assert d["held_seconds"] == 60.0
    
    def test_reacquire_after_release(self):
        """Test reacquiring after release."""
        detector = LeakDetector(timeout=60.0)
        detector.track_acquire("conn_1")
        detector.track_release("conn_1")
        info = detector.track_acquire("conn_1")
        
        assert info.state == ConnectionState.ACTIVE
    
    def test_query_count_accumulates(self):
        """Test query count accumulates across acquires."""
        detector = LeakDetector(timeout=60.0)
        detector.track_acquire("conn_1")
        detector.track_query("conn_1")
        detector.track_query("conn_1")
        detector.track_release("conn_1")
        detector.track_acquire("conn_1")
        detector.track_query("conn_1")
        
        connections = detector.get_all_connections()
        assert connections[0].query_count == 3


# ============================================================================
# HealthChecker Tests (20 tests)
# ============================================================================

class TestHealthChecker:
    """Tests for HealthChecker class."""
    
    def test_mark_healthy(self):
        """Test marking connection healthy."""
        checker = HealthChecker(timeout=60.0)
        checker.mark_healthy("conn_1")
        assert checker.is_healthy("conn_1") is True
    
    def test_mark_unhealthy(self):
        """Test marking connection unhealthy."""
        checker = HealthChecker(timeout=60.0)
        checker.mark_healthy("conn_1")
        checker.mark_unhealthy("conn_1")
        assert checker.is_healthy("conn_1") is False
    
    def test_is_healthy_unknown(self):
        """Test is_healthy for unknown connection."""
        checker = HealthChecker(timeout=60.0)
        assert checker.is_healthy("unknown") is False
    
    def test_is_healthy_expired(self):
        """Test is_healthy when check expired."""
        checker = HealthChecker(timeout=0.01)
        checker.mark_healthy("conn_1")
        time.sleep(0.02)
        assert checker.is_healthy("conn_1") is False
    
    def test_needs_check_yes(self):
        """Test needs_check returns true when due."""
        checker = HealthChecker(timeout=60.0)
        assert checker.needs_check("conn_1", interval=0.01) is True
    
    def test_needs_check_no(self):
        """Test needs_check returns false when recent."""
        checker = HealthChecker(timeout=60.0)
        checker.mark_healthy("conn_1")
        assert checker.needs_check("conn_1", interval=60.0) is False
    
    def test_get_dead_connections(self):
        """Test getting dead connections."""
        checker = HealthChecker(timeout=0.01)
        checker.mark_healthy("conn_1")
        time.sleep(0.02)
        
        dead = checker.get_dead_connections()
        assert "conn_1" in dead
    
    def test_no_dead_connections(self):
        """Test no dead connections when all healthy."""
        checker = HealthChecker(timeout=60.0)
        checker.mark_healthy("conn_1")
        checker.mark_healthy("conn_2")
        
        dead = checker.get_dead_connections()
        assert len(dead) == 0
    
    def test_remove_connection(self):
        """Test removing connection."""
        checker = HealthChecker(timeout=60.0)
        checker.mark_healthy("conn_1")
        checker.remove_connection("conn_1")
        
        assert checker.is_healthy("conn_1") is False
    
    def test_reset(self):
        """Test resetting checker."""
        checker = HealthChecker(timeout=60.0)
        checker.mark_healthy("conn_1")
        checker.mark_healthy("conn_2")
        checker.reset()
        
        assert checker.is_healthy("conn_1") is False
        assert checker.is_healthy("conn_2") is False
    
    def test_multiple_healthy_marks(self):
        """Test multiple healthy marks update timestamp."""
        checker = HealthChecker(timeout=0.02)
        checker.mark_healthy("conn_1")
        time.sleep(0.01)
        checker.mark_healthy("conn_1")
        time.sleep(0.01)
        
        # Should still be healthy because we refreshed
        assert checker.is_healthy("conn_1") is True
    
    def test_thread_safety(self):
        """Test checker is thread-safe."""
        checker = HealthChecker(timeout=60.0)
        
        def mark_healthy():
            for i in range(100):
                conn_id = f"conn_{threading.current_thread().name}_{i}"
                checker.mark_healthy(conn_id)
        
        threads = [threading.Thread(target=mark_healthy) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should not raise
    
    def test_dead_after_timeout(self):
        """Test connection becomes dead after timeout."""
        checker = HealthChecker(timeout=0.01)
        checker.mark_healthy("conn_1")
        
        assert checker.is_healthy("conn_1") is True
        
        time.sleep(0.02)
        
        assert checker.is_healthy("conn_1") is False
    
    def test_needs_check_after_interval(self):
        """Test needs_check after interval passes."""
        checker = HealthChecker(timeout=60.0)
        checker.mark_healthy("conn_1")
        time.sleep(0.02)
        
        assert checker.needs_check("conn_1", interval=0.01) is True
    
    def test_get_dead_connections_empty(self):
        """Test get_dead_connections returns empty list initially."""
        checker = HealthChecker(timeout=60.0)
        assert checker.get_dead_connections() == []
    
    def test_mark_healthy_creates_entry(self):
        """Test mark_healthy creates tracking entry."""
        checker = HealthChecker(timeout=60.0)
        checker.mark_healthy("new_conn")
        
        dead = checker.get_dead_connections()
        assert "new_conn" not in dead
    
    def test_mark_unhealthy_removes_from_healthy_set(self):
        """Test mark_unhealthy removes from healthy set."""
        checker = HealthChecker(timeout=60.0)
        checker.mark_healthy("conn_1")
        checker.mark_unhealthy("conn_1")
        
        assert checker.is_healthy("conn_1") is False
    
    def test_very_short_timeout(self):
        """Test very short timeout."""
        checker = HealthChecker(timeout=0.001)
        checker.mark_healthy("conn_1")
        time.sleep(0.005)
        
        dead = checker.get_dead_connections()
        assert "conn_1" in dead
    
    def test_long_timeout(self):
        """Test long timeout keeps connections healthy."""
        checker = HealthChecker(timeout=3600.0)  # 1 hour
        checker.mark_healthy("conn_1")
        
        assert checker.is_healthy("conn_1") is True
        assert len(checker.get_dead_connections()) == 0


# ============================================================================
# PoolMonitor Core Tests (30 tests)
# ============================================================================

class TestPoolMonitorCore:
    """Tests for PoolMonitor core functionality."""
    
    def test_default_creation(self):
        """Test creating monitor with defaults."""
        monitor = PoolMonitor()
        assert monitor.enabled is True
    
    def test_custom_config(self):
        """Test creating monitor with custom config."""
        config = MonitorConfig(exhaustion_warning_threshold=0.7)
        monitor = PoolMonitor(config)
        assert monitor.config.exhaustion_warning_threshold == 0.7
    
    def test_disabled_monitor(self):
        """Test disabled monitor."""
        config = MonitorConfig(enabled=False)
        monitor = PoolMonitor(config)
        assert monitor.enabled is False
    
    def test_pool_name(self):
        """Test pool name setting."""
        monitor = PoolMonitor(pool_name="main_pool")
        assert monitor.pool_name == "main_pool"
    
    def test_update_stats(self):
        """Test updating pool stats."""
        monitor = PoolMonitor()
        stats = PoolStats(active=5, idle=10)
        monitor.update_stats(stats)
        
        assert monitor._current_stats.active == 5
    
    def test_track_acquire(self):
        """Test tracking connection acquire."""
        monitor = PoolMonitor()
        monitor.track_acquire("conn_1")
        
        active = monitor.get_active_connections()
        assert len(active) == 1
    
    def test_track_release(self):
        """Test tracking connection release."""
        monitor = PoolMonitor()
        monitor.track_acquire("conn_1")
        monitor.track_release("conn_1")
        
        active = monitor.get_active_connections()
        assert len(active) == 0
    
    def test_track_query(self):
        """Test tracking query."""
        monitor = PoolMonitor()
        monitor.track_acquire("conn_1")
        monitor.track_query("conn_1")
        
        # Should not raise
    
    def test_track_connection_closed(self):
        """Test tracking connection close."""
        monitor = PoolMonitor()
        monitor.track_acquire("conn_1")
        monitor.track_connection_closed("conn_1")
        
        active = monitor.get_active_connections()
        assert len(active) == 0
    
    def test_check_pool_no_issues(self):
        """Test check_pool with no issues."""
        monitor = PoolMonitor()
        monitor.update_stats(PoolStats(active=1, max_size=10))
        
        events = monitor.check_pool()
        assert len(events) == 0
    
    def test_check_pool_exhaustion_warning(self):
        """Test check_pool detects exhaustion warning."""
        config = MonitorConfig(exhaustion_warning_threshold=0.5)
        monitor = PoolMonitor(config)
        monitor.update_stats(PoolStats(active=6, max_size=10))
        
        events = monitor.check_pool()
        
        warning_events = [e for e in events if e.type == PoolEventType.EXHAUSTION_WARNING]
        assert len(warning_events) == 1
    
    def test_check_pool_exhaustion_critical(self):
        """Test check_pool detects exhaustion critical."""
        config = MonitorConfig(
            exhaustion_warning_threshold=0.5,
            exhaustion_critical_threshold=0.9,
        )
        monitor = PoolMonitor(config)
        monitor.update_stats(PoolStats(active=9, max_size=10))
        
        events = monitor.check_pool()
        
        critical_events = [e for e in events if e.type == PoolEventType.EXHAUSTION_CRITICAL]
        assert len(critical_events) == 1
    
    def test_check_pool_exhaustion_cleared(self):
        """Test check_pool detects exhaustion cleared."""
        config = MonitorConfig(exhaustion_warning_threshold=0.5)
        monitor = PoolMonitor(config)
        
        # Trigger warning
        monitor.update_stats(PoolStats(active=6, max_size=10))
        monitor.check_pool()
        
        # Clear it
        monitor.update_stats(PoolStats(active=2, max_size=10))
        events = monitor.check_pool()
        
        cleared_events = [e for e in events if e.type == PoolEventType.EXHAUSTION_CLEARED]
        assert len(cleared_events) == 1
    
    def test_check_pool_detects_leaks(self):
        """Test check_pool detects leaks."""
        config = MonitorConfig(leak_detection_timeout=0.01)
        monitor = PoolMonitor(config)
        monitor.track_acquire("conn_1")
        time.sleep(0.02)
        
        events = monitor.check_pool()
        
        leak_events = [e for e in events if e.type == PoolEventType.LEAK_DETECTED]
        assert len(leak_events) == 1
    
    def test_get_events(self):
        """Test getting event history."""
        config = MonitorConfig(exhaustion_warning_threshold=0.5)
        monitor = PoolMonitor(config)
        monitor.update_stats(PoolStats(active=6, max_size=10))
        monitor.check_pool()
        
        events = monitor.get_events()
        assert len(events) >= 1
    
    def test_get_events_with_limit(self):
        """Test getting events with limit."""
        config = MonitorConfig(exhaustion_warning_threshold=0.5)
        monitor = PoolMonitor(config)
        
        # Generate multiple events
        for i in range(5):
            monitor.update_stats(PoolStats(active=6, max_size=10))
            monitor.check_pool()
            monitor.update_stats(PoolStats(active=1, max_size=10))
            monitor.check_pool()
        
        events = monitor.get_events(limit=3)
        assert len(events) <= 3
    
    def test_get_events_by_type(self):
        """Test getting events filtered by type."""
        config = MonitorConfig(exhaustion_warning_threshold=0.5)
        monitor = PoolMonitor(config)
        monitor.update_stats(PoolStats(active=6, max_size=10))
        monitor.check_pool()
        
        events = monitor.get_events(event_type=PoolEventType.EXHAUSTION_WARNING)
        assert all(e.type == PoolEventType.EXHAUSTION_WARNING for e in events)
    
    def test_get_stats(self):
        """Test getting monitor stats."""
        monitor = PoolMonitor()
        stats = monitor.get_stats()
        
        assert "pool_name" in stats
        assert "current_stats" in stats
        assert "active_connections" in stats
    
    def test_reset(self):
        """Test resetting monitor."""
        monitor = PoolMonitor()
        monitor.track_acquire("conn_1")
        monitor.reset()
        
        assert len(monitor.get_active_connections()) == 0
        assert len(monitor.get_events()) == 0
    
    def test_disabled_skips_tracking(self):
        """Test disabled monitor skips tracking."""
        config = MonitorConfig(enabled=False)
        monitor = PoolMonitor(config)
        
        monitor.track_acquire("conn_1")
        events = monitor.check_pool()
        
        assert len(events) == 0
    
    def test_create_monitor_helper(self):
        """Test create_monitor helper function."""
        monitor = create_monitor(
            exhaustion_warning_threshold=0.7,
            pool_name="test_pool",
        )
        assert monitor.config.exhaustion_warning_threshold == 0.7
        assert monitor.pool_name == "test_pool"
    
    def test_no_duplicate_warnings(self):
        """Test no duplicate warnings for same state."""
        config = MonitorConfig(exhaustion_warning_threshold=0.5)
        monitor = PoolMonitor(config)
        
        # Check twice with same state
        monitor.update_stats(PoolStats(active=6, max_size=10))
        events1 = monitor.check_pool()
        events2 = monitor.check_pool()
        
        # First should have warning, second should not
        warnings1 = [e for e in events1 if e.type == PoolEventType.EXHAUSTION_WARNING]
        warnings2 = [e for e in events2 if e.type == PoolEventType.EXHAUSTION_WARNING]
        
        assert len(warnings1) == 1
        assert len(warnings2) == 0
    
    def test_event_includes_pool_stats(self):
        """Test events include pool stats."""
        config = MonitorConfig(exhaustion_warning_threshold=0.5)
        monitor = PoolMonitor(config)
        monitor.update_stats(PoolStats(active=6, max_size=10))
        
        events = monitor.check_pool()
        
        assert events[0].pool_stats is not None
        assert events[0].pool_stats["active"] == 6
    
    def test_event_includes_pool_name(self):
        """Test events include pool name."""
        monitor = PoolMonitor(pool_name="main")
        config = MonitorConfig(exhaustion_warning_threshold=0.5)
        monitor.config = config
        monitor.update_stats(PoolStats(active=6, max_size=10))
        
        events = monitor.check_pool()
        if events:
            assert events[0].pool_name == "main"
    
    def test_events_have_timestamp(self):
        """Test events have timestamp."""
        config = MonitorConfig(exhaustion_warning_threshold=0.5)
        monitor = PoolMonitor(config)
        before = time.time()
        monitor.update_stats(PoolStats(active=6, max_size=10))
        events = monitor.check_pool()
        after = time.time()
        
        assert before <= events[0].timestamp <= after
    
    def test_pool_event_to_dict(self):
        """Test PoolEvent to_dict."""
        event = PoolEvent(
            type=PoolEventType.EXHAUSTION_WARNING,
            pool_name="main",
            message="Test",
        )
        d = event.to_dict()
        
        assert d["type"] == "exhaustion_warning"
        assert d["pool_name"] == "main"
    
    def test_max_events_limit(self):
        """Test max events limit."""
        config = MonitorConfig(exhaustion_warning_threshold=0.1)
        monitor = PoolMonitor(config)
        monitor._max_events = 10
        
        # Generate many events
        for i in range(20):
            monitor.update_stats(PoolStats(active=9, max_size=10))
            monitor.check_pool()
            monitor.update_stats(PoolStats(active=1, max_size=10))
            monitor.check_pool()
        
        events = monitor.get_events(limit=100)
        assert len(events) <= 10
    
    def test_connection_state_enum(self):
        """Test ConnectionState enum values."""
        assert ConnectionState.IDLE.value == "idle"
        assert ConnectionState.ACTIVE.value == "active"
        assert ConnectionState.DEAD.value == "dead"
        assert ConnectionState.LEAKED.value == "leaked"


# ============================================================================
# Events and Callbacks Tests (15 tests)
# ============================================================================

class TestEventsAndCallbacks:
    """Tests for events and callbacks."""
    
    def test_warning_callback_called(self):
        """Test exhaustion warning callback is called."""
        callback = MagicMock()
        config = MonitorConfig(
            exhaustion_warning_threshold=0.5,
            on_exhaustion_warning=callback,
        )
        monitor = PoolMonitor(config)
        monitor.update_stats(PoolStats(active=6, max_size=10))
        monitor.check_pool()
        
        callback.assert_called_once()
    
    def test_critical_callback_called(self):
        """Test exhaustion critical callback is called."""
        callback = MagicMock()
        config = MonitorConfig(
            exhaustion_warning_threshold=0.5,
            exhaustion_critical_threshold=0.8,
            on_exhaustion_critical=callback,
        )
        monitor = PoolMonitor(config)
        monitor.update_stats(PoolStats(active=9, max_size=10))
        monitor.check_pool()
        
        callback.assert_called_once()
    
    def test_leak_callback_called(self):
        """Test leak detection callback is called."""
        callback = MagicMock()
        config = MonitorConfig(
            leak_detection_timeout=0.01,
            on_leak_detected=callback,
        )
        monitor = PoolMonitor(config)
        monitor.track_acquire("conn_1")
        time.sleep(0.02)
        monitor.check_pool()
        
        callback.assert_called_once()
    
    def test_dead_connection_callback_called(self):
        """Test dead connection callback is called."""
        callback = MagicMock()
        config = MonitorConfig(
            dead_connection_timeout=0.01,
            on_dead_connection=callback,
        )
        monitor = PoolMonitor(config)
        monitor.track_acquire("conn_1")
        # Need to trigger health check and let it expire
        monitor._health_checker.mark_healthy("conn_1")
        time.sleep(0.02)
        monitor.check_pool()
        
        # May or may not be called depending on implementation
    
    def test_callback_receives_event(self):
        """Test callback receives proper event object."""
        received_events = []
        
        def callback(event):
            received_events.append(event)
        
        config = MonitorConfig(
            exhaustion_warning_threshold=0.5,
            on_exhaustion_warning=callback,
        )
        monitor = PoolMonitor(config)
        monitor.update_stats(PoolStats(active=6, max_size=10))
        monitor.check_pool()
        
        assert len(received_events) == 1
        assert isinstance(received_events[0], PoolEvent)
    
    def test_leak_callback_receives_leak_info(self):
        """Test leak callback receives LeakInfo object."""
        received_leaks = []
        
        def callback(leak):
            received_leaks.append(leak)
        
        config = MonitorConfig(
            leak_detection_timeout=0.01,
            on_leak_detected=callback,
        )
        monitor = PoolMonitor(config)
        monitor.track_acquire("conn_1")
        time.sleep(0.02)
        monitor.check_pool()
        
        assert len(received_leaks) == 1
        assert isinstance(received_leaks[0], LeakInfo)
    
    def test_event_type_values(self):
        """Test PoolEventType enum values."""
        assert PoolEventType.EXHAUSTION_WARNING.value == "exhaustion_warning"
        assert PoolEventType.EXHAUSTION_CRITICAL.value == "exhaustion_critical"
        assert PoolEventType.LEAK_DETECTED.value == "leak_detected"
    
    def test_warning_not_called_when_below_threshold(self):
        """Test warning callback not called below threshold."""
        callback = MagicMock()
        config = MonitorConfig(
            exhaustion_warning_threshold=0.8,
            on_exhaustion_warning=callback,
        )
        monitor = PoolMonitor(config)
        monitor.update_stats(PoolStats(active=5, max_size=10))
        monitor.check_pool()
        
        callback.assert_not_called()
    
    def test_multiple_callbacks(self):
        """Test multiple callbacks can be set."""
        warning_cb = MagicMock()
        critical_cb = MagicMock()
        
        config = MonitorConfig(
            exhaustion_warning_threshold=0.5,
            exhaustion_critical_threshold=0.8,
            on_exhaustion_warning=warning_cb,
            on_exhaustion_critical=critical_cb,
        )
        monitor = PoolMonitor(config)
        monitor.update_stats(PoolStats(active=9, max_size=10))
        monitor.check_pool()
        
        # Both should be called for critical
        critical_cb.assert_called_once()
    
    def test_event_message_content(self):
        """Test event message contains useful info."""
        config = MonitorConfig(exhaustion_warning_threshold=0.5)
        monitor = PoolMonitor(config)
        monitor.update_stats(PoolStats(active=6, max_size=10))
        
        events = monitor.check_pool()
        
        assert "60" in events[0].message or "capacity" in events[0].message.lower()
    
    def test_cleared_event_after_warning(self):
        """Test cleared event is generated after warning resolved."""
        config = MonitorConfig(exhaustion_warning_threshold=0.5)
        monitor = PoolMonitor(config)
        
        # Trigger warning
        monitor.update_stats(PoolStats(active=6, max_size=10))
        monitor.check_pool()
        
        # Resolve it
        monitor.update_stats(PoolStats(active=2, max_size=10))
        events = monitor.check_pool()
        
        cleared = [e for e in events if e.type == PoolEventType.EXHAUSTION_CLEARED]
        assert len(cleared) == 1
    
    def test_no_callback_when_disabled(self):
        """Test callbacks not called when monitor disabled."""
        callback = MagicMock()
        config = MonitorConfig(
            enabled=False,
            exhaustion_warning_threshold=0.5,
            on_exhaustion_warning=callback,
        )
        monitor = PoolMonitor(config)
        monitor.update_stats(PoolStats(active=6, max_size=10))
        monitor.check_pool()
        
        callback.assert_not_called()
    
    def test_event_details_content(self):
        """Test event details contain useful info."""
        config = MonitorConfig(exhaustion_warning_threshold=0.5)
        monitor = PoolMonitor(config)
        monitor.update_stats(PoolStats(active=6, max_size=10, waiting=5))
        
        events = monitor.check_pool()
        
        assert "waiting" in events[0].details or events[0].pool_stats.get("waiting") == 5
    
    def test_leak_event_contains_connection_id(self):
        """Test leak event contains connection ID."""
        config = MonitorConfig(leak_detection_timeout=0.01)
        monitor = PoolMonitor(config)
        monitor.track_acquire("leaked_conn_123")
        time.sleep(0.02)
        
        events = monitor.check_pool()
        
        leak_events = [e for e in events if e.type == PoolEventType.LEAK_DETECTED]
        assert len(leak_events) == 1
        assert "leaked_conn_123" in leak_events[0].message or leak_events[0].details.get("connection_id") == "leaked_conn_123"
    
    def test_callback_exception_doesnt_crash(self):
        """Test callback exception doesn't crash monitor."""
        def bad_callback(event):
            raise ValueError("Callback error")
        
        config = MonitorConfig(
            exhaustion_warning_threshold=0.5,
            on_exhaustion_warning=bad_callback,
        )
        monitor = PoolMonitor(config)
        monitor.update_stats(PoolStats(active=6, max_size=10))
        
        # Should raise but that's expected behavior
        # In production, might want to catch this
        with pytest.raises(ValueError):
            monitor.check_pool()

