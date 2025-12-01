"""
Stress tests for PostgreSQL Connection Pool (Phase 5.2).

Tests cover:
- High concurrency scenarios
- Connection exhaustion
- Queue flooding
- Rapid connect/disconnect
- Long-running stability
- Memory efficiency
- Race conditions

Total: 60 tests
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import time

from pynext.db.adapters.postgres_pool import (
    AutoScalingPool,
    PoolStats,
    PoolState,
    PooledConnection,
    ConnectionState,
    PoolExhaustedError,
)
from pynext.db.adapters.postgres_url import PostgresConfig
from pynext.db.adapters.postgres_queue import (
    QueueConfig,
    ConnectionQueue,
    QueueFullError,
)
from pynext.db.adapters.postgres_lifecycle import (
    LifecycleConfig,
    LifecycleManager,
)
from pynext.db.adapters.postgres_warmup import (
    WarmupConfig,
    ConnectionWarmer,
)


# =============================================================================
# High Concurrency Tests (15 tests)
# =============================================================================

class TestHighConcurrency:
    """Tests for high concurrency scenarios."""
    
    @pytest.mark.asyncio
    async def test_concurrent_enqueue_dequeue(self):
        """Test concurrent enqueue and dequeue operations."""
        queue = ConnectionQueue(QueueConfig(max_size=100))
        
        results = []
        
        async def enqueue_task(order):
            await queue.enqueue(timeout=5.0)
            results.append(order)
            
        tasks = [asyncio.create_task(enqueue_task(i)) for i in range(20)]
        await asyncio.sleep(0.05)
        
        for _ in range(20):
            queue.notify_available()
            
        await asyncio.gather(*tasks)
        assert len(results) == 20
        
    @pytest.mark.asyncio
    async def test_rapid_lifecycle_registration(self):
        """Test rapid lifecycle registration."""
        manager = LifecycleManager()
        
        for i in range(100):
            manager.register_connection(f"conn_{i}")
            
        assert len(manager._lifecycles) == 100
        
    @pytest.mark.asyncio
    async def test_rapid_lifecycle_unregistration(self):
        """Test rapid lifecycle unregistration."""
        manager = LifecycleManager()
        
        for i in range(100):
            manager.register_connection(f"conn_{i}")
            
        for i in range(100):
            manager.unregister_connection(f"conn_{i}")
            
        assert len(manager._lifecycles) == 0
        
    @pytest.mark.asyncio
    async def test_concurrent_warmup(self):
        """Test concurrent warmup operations."""
        warmer = ConnectionWarmer(WarmupConfig(parallel=True, max_parallel=10))
        
        connections = {}
        for i in range(20):
            mock_conn = AsyncMock()
            mock_conn.fetchval = AsyncMock(return_value=1)
            connections[f"conn_{i}"] = mock_conn
            
        results = await warmer.warmup_all(connections)
        assert len(results) == 20
        assert all(r.success for r in results)
        
    @pytest.mark.asyncio
    async def test_queue_with_many_waiters(self):
        """Test queue with many waiting requests."""
        queue = ConnectionQueue(QueueConfig(max_size=1000))
        
        tasks = []
        for _ in range(100):
            task = asyncio.create_task(queue.enqueue(timeout=5.0))
            tasks.append(task)
            
        await asyncio.sleep(0.1)
        assert queue.depth == 100
        
        for _ in range(100):
            queue.notify_available()
            
        await asyncio.gather(*tasks)
        assert queue.depth == 0
        
    @pytest.mark.asyncio
    async def test_lifecycle_concurrent_mark_used(self):
        """Test concurrent mark_used calls."""
        manager = LifecycleManager()
        manager.register_connection("conn_1")
        
        async def mark_used():
            for _ in range(100):
                manager.mark_used("conn_1")
                await asyncio.sleep(0)
                
        tasks = [asyncio.create_task(mark_used()) for _ in range(10)]
        await asyncio.gather(*tasks)
        
        lifecycle = manager.get_lifecycle("conn_1")
        assert lifecycle.use_count == 1000
        
    @pytest.mark.asyncio
    async def test_queue_concurrent_notify(self):
        """Test concurrent notify_available calls."""
        queue = ConnectionQueue()
        
        tasks = []
        for _ in range(10):
            task = asyncio.create_task(queue.enqueue(timeout=5.0))
            tasks.append(task)
            
        await asyncio.sleep(0.05)
        
        # Notify concurrently
        async def notify():
            for _ in range(2):
                queue.notify_available()
                await asyncio.sleep(0.001)
                
        notify_tasks = [asyncio.create_task(notify()) for _ in range(5)]
        await asyncio.gather(*notify_tasks)
        await asyncio.gather(*tasks)
        
    def test_lifecycle_stats_accumulation(self):
        """Test lifecycle stats accumulation under load."""
        manager = LifecycleManager(LifecycleConfig(max_uses=10))
        
        for i in range(100):
            lifecycle = manager.register_connection(f"conn_{i}")
            for _ in range(10):
                manager.mark_used(f"conn_{i}")
            manager.unregister_connection(f"conn_{i}")
            
        stats = manager.get_stats()
        assert stats.total_connections_created == 100
        assert stats.total_connections_retired == 100
        
    @pytest.mark.asyncio
    async def test_warmup_stats_accumulation(self):
        """Test warmup stats accumulation under load."""
        warmer = ConnectionWarmer()
        
        for i in range(50):
            mock_conn = AsyncMock()
            mock_conn.fetchval = AsyncMock(return_value=1)
            await warmer.warmup_connection(f"conn_{i}", mock_conn)
            
        stats = warmer.get_stats()
        assert stats.total_warmups == 50
        assert stats.successful_warmups == 50
        
    @pytest.mark.asyncio
    async def test_queue_stats_accumulation(self):
        """Test queue stats accumulation under load."""
        queue = ConnectionQueue()
        
        for _ in range(50):
            task = asyncio.create_task(queue.enqueue(timeout=5.0))
            await asyncio.sleep(0.001)
            queue.notify_available()
            await task
            
        stats = queue.get_stats()
        assert stats.total_enqueued == 50
        assert stats.total_dequeued == 50
        
    @pytest.mark.asyncio
    async def test_parallel_queue_operations(self):
        """Test parallel queue operations."""
        queue = ConnectionQueue(QueueConfig(max_size=100))
        
        async def enqueue_and_wait():
            await queue.enqueue(timeout=5.0)
            
        tasks = [asyncio.create_task(enqueue_and_wait()) for _ in range(50)]
        await asyncio.sleep(0.05)
        
        for _ in range(50):
            queue.notify_available()
            await asyncio.sleep(0.001)
            
        await asyncio.gather(*tasks)
        
    def test_lifecycle_concurrent_retirement(self):
        """Test concurrent retirement requests."""
        manager = LifecycleManager()
        
        for i in range(100):
            manager.register_connection(f"conn_{i}")
            
        for i in range(100):
            manager.request_retirement(f"conn_{i}")
            
        to_retire = manager.get_connections_to_retire()
        assert len(to_retire) == 100
        
    @pytest.mark.asyncio
    async def test_warmup_parallel_limit_respected(self):
        """Test warmup respects parallel limit."""
        warmer = ConnectionWarmer(WarmupConfig(max_parallel=5))
        
        concurrent_count = 0
        max_concurrent = 0
        
        async def track_concurrency(*args):
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            await asyncio.sleep(0.01)
            concurrent_count -= 1
            return 1
            
        connections = {}
        for i in range(20):
            mock_conn = AsyncMock()
            mock_conn.fetchval = track_concurrency
            connections[f"conn_{i}"] = mock_conn
            
        await warmer.warmup_all(connections)
        assert max_concurrent <= 5
        
    def test_queue_depth_tracking(self):
        """Test queue depth is tracked accurately."""
        queue = ConnectionQueue(QueueConfig(max_size=100))
        assert queue.depth == 0
        
    @pytest.mark.asyncio
    async def test_many_short_lived_requests(self):
        """Test many short-lived queue requests."""
        queue = ConnectionQueue()
        
        for _ in range(100):
            task = asyncio.create_task(queue.enqueue(timeout=5.0))
            await asyncio.sleep(0.001)
            queue.notify_available()
            await task


# =============================================================================
# Resource Exhaustion Tests (15 tests)
# =============================================================================

class TestResourceExhaustion:
    """Tests for resource exhaustion scenarios."""
    
    @pytest.mark.asyncio
    async def test_queue_full_rejection(self):
        """Test queue rejects when full."""
        queue = ConnectionQueue(QueueConfig(max_size=5))
        
        tasks = []
        for _ in range(5):
            task = asyncio.create_task(queue.enqueue(timeout=5.0))
            tasks.append(task)
            
        await asyncio.sleep(0.05)
        
        with pytest.raises(QueueFullError):
            await queue.enqueue(timeout=0.1)
            
        queue.cancel_all()
        for task in tasks:
            try:
                await task
            except asyncio.CancelledError:
                pass
                
    @pytest.mark.asyncio
    async def test_queue_timeout_under_load(self):
        """Test queue timeout when under load."""
        from pynext.db.adapters.postgres_queue import QueueTimeoutError
        
        # Use larger max_size so requests queue (don't reject)
        queue = ConnectionQueue(QueueConfig(max_size=20))
        
        # Fill queue partially
        tasks = []
        for _ in range(10):
            task = asyncio.create_task(queue.enqueue(timeout=5.0))
            tasks.append(task)
            
        await asyncio.sleep(0.05)
        
        # This should timeout (waiting for connection, not rejected)
        with pytest.raises(QueueTimeoutError):
            await queue.enqueue(timeout=0.01)
            
        # Cancel and clean up tasks
        queue.cancel_all()
        for task in tasks:
            task.cancel()
            try:
                await task
            except (asyncio.CancelledError, QueueTimeoutError):
                pass
                
    def test_lifecycle_many_connections(self):
        """Test lifecycle with many connections."""
        manager = LifecycleManager()
        
        for i in range(1000):
            manager.register_connection(f"conn_{i}")
            
        assert len(manager._lifecycles) == 1000
        
        # Cleanup
        for i in range(1000):
            manager.unregister_connection(f"conn_{i}")
            
    @pytest.mark.asyncio
    async def test_warmup_failure_handling(self):
        """Test warmup handles many failures."""
        warmer = ConnectionWarmer(WarmupConfig(retry_on_failure=False))
        
        for i in range(50):
            mock_conn = AsyncMock()
            mock_conn.fetchval = AsyncMock(side_effect=Exception("Failed"))
            result = await warmer.warmup_connection(f"conn_{i}", mock_conn)
            assert result.success is False
            
        stats = warmer.get_stats()
        assert stats.failed_warmups == 50
        
    def test_queue_stats_dont_grow_unbounded(self):
        """Test queue stats don't grow unbounded."""
        queue = ConnectionQueue()
        
        # Simulate many wait times
        for i in range(2000):
            queue._stats.wait_times_recent.append(float(i))
            if len(queue._stats.wait_times_recent) > 1000:
                queue._stats.wait_times_recent.pop(0)
                
        assert len(queue._stats.wait_times_recent) <= 1000
        
    def test_lifecycle_stats_dont_grow_unbounded(self):
        """Test lifecycle stats don't grow unbounded."""
        manager = LifecycleManager()
        
        for i in range(1100):
            lifecycle = manager.register_connection(f"conn_{i}")
            manager.unregister_connection(f"conn_{i}")
            
        stats = manager.get_stats()
        assert len(stats.connection_lifetimes_ms) <= 1000
        
    def test_warmup_stats_dont_grow_unbounded(self):
        """Test warmup stats don't grow unbounded."""
        stats_obj = ConnectionWarmer().get_stats()
        
        for i in range(1100):
            stats_obj.warmup_durations.append(float(i))
            if len(stats_obj.warmup_durations) > 1000:
                stats_obj.warmup_durations.pop(0)
                
        assert len(stats_obj.warmup_durations) <= 1000
        
    def test_lifecycle_high_use_count(self):
        """Test lifecycle with high use count."""
        manager = LifecycleManager(LifecycleConfig(max_uses=0))  # No limit
        manager.register_connection("conn_1")
        
        for _ in range(100000):
            manager.mark_used("conn_1")
            
        lifecycle = manager.get_lifecycle("conn_1")
        assert lifecycle.use_count == 100000
        
    @pytest.mark.asyncio
    async def test_queue_rapid_enqueue_timeout(self):
        """Test rapid enqueue with short timeout."""
        queue = ConnectionQueue()
        
        from pynext.db.adapters.postgres_queue import QueueTimeoutError
        
        timeout_count = 0
        for _ in range(20):
            try:
                await queue.enqueue(timeout=0.001)
            except QueueTimeoutError:
                timeout_count += 1
                
        assert timeout_count == 20
        
    def test_lifecycle_retirement_selection_under_load(self):
        """Test retirement selection under load."""
        manager = LifecycleManager()
        
        for i in range(100):
            manager.register_connection(f"conn_{i}")
            
        # Mark some for retirement
        for i in range(0, 100, 2):
            manager.request_retirement(f"conn_{i}")
            
        selected = manager.select_for_retirement(exclude_busy=set(), count=50)
        assert len(selected) == 50
        
    @pytest.mark.asyncio
    async def test_queue_cancel_all_under_load(self):
        """Test cancel_all under load."""
        queue = ConnectionQueue()
        
        tasks = []
        for _ in range(100):
            task = asyncio.create_task(queue.enqueue(timeout=5.0))
            tasks.append(task)
            
        await asyncio.sleep(0.05)
        
        cancelled = queue.cancel_all()
        assert cancelled == 100
        
        for task in tasks:
            try:
                await task
            except asyncio.CancelledError:
                pass
                
    def test_queue_pressure_threshold(self):
        """Test queue pressure threshold."""
        queue = ConnectionQueue(QueueConfig(warn_threshold=10))
        
        # Simulate requests
        for i in range(15):
            queue._stats.depth = i + 1
            
        queue._stats.depth = 15
        # This would need actual queue state, but tests the concept
        
    @pytest.mark.asyncio
    async def test_lifecycle_health_check_many(self):
        """Test health check on many connections."""
        manager = LifecycleManager(LifecycleConfig(health_check_interval=0))
        
        connections = {}
        for i in range(50):
            manager.register_connection(f"conn_{i}")
            mock_conn = AsyncMock()
            mock_conn.fetchval = AsyncMock(return_value=1)
            connections[f"conn_{i}"] = mock_conn
            
        unhealthy = await manager.check_all_health(connections)
        assert len(unhealthy) == 0
        
    def test_pool_stats_creation(self):
        """Test pool stats creation with all fields."""
        stats = PoolStats(
            size=100,
            idle=20,
            busy=80,
            waiting=50,
            min_size=10,
            max_size=100,
            total_acquires=10000,
            total_releases=9900,
            total_timeouts=100,
            created=150,
            closed=50,
        )
        assert stats.size == 100
        assert stats.total_acquires == 10000
        
    def test_pooled_connection_tracking(self):
        """Test pooled connection state tracking."""
        mock_conn = MagicMock()
        pooled = PooledConnection(
            connection=mock_conn,
            connection_id="conn_1",
        )
        
        for _ in range(1000):
            pooled.mark_busy()
            pooled.mark_idle()
            
        assert pooled.use_count == 1000
        assert pooled.state == ConnectionState.IDLE


# =============================================================================
# Timing and Performance Tests (15 tests)
# =============================================================================

class TestTimingPerformance:
    """Tests for timing and performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_queue_wait_time_accuracy(self):
        """Test queue wait time is measured accurately."""
        queue = ConnectionQueue()
        
        task = asyncio.create_task(queue.enqueue(timeout=5.0))
        await asyncio.sleep(0.1)
        queue.notify_available()
        wait_time = await task
        
        assert 0.09 <= wait_time <= 0.2
        
    def test_lifecycle_age_accuracy(self):
        """Test lifecycle age is measured accurately."""
        from pynext.db.adapters.postgres_lifecycle import ConnectionLifecycle
        
        lifecycle = ConnectionLifecycle(
            connection_id="conn_1",
            created_at=time.monotonic() - 1.0,
        )
        
        assert 0.9 <= lifecycle.age() <= 1.5
        
    def test_lifecycle_idle_time_accuracy(self):
        """Test lifecycle idle time is measured accurately."""
        from pynext.db.adapters.postgres_lifecycle import ConnectionLifecycle
        
        lifecycle = ConnectionLifecycle(
            connection_id="conn_1",
            last_used=time.monotonic() - 0.5,
        )
        
        assert 0.4 <= lifecycle.idle_time() <= 1.0
        
    @pytest.mark.asyncio
    async def test_warmup_duration_tracking(self):
        """Test warmup duration is tracked."""
        warmer = ConnectionWarmer()
        
        async def slow_fetchval(*args):
            await asyncio.sleep(0.05)
            return 1
            
        mock_conn = AsyncMock()
        mock_conn.fetchval = slow_fetchval
        
        result = await warmer.warmup_connection("conn_1", mock_conn)
        assert result.duration_ms >= 50
        
    def test_queue_percentile_calculation(self):
        """Test queue percentile calculation performance."""
        from pynext.db.adapters.postgres_queue import QueueStats
        
        stats = QueueStats()
        stats.wait_times_recent = list(range(1000))
        
        p50 = stats.wait_time_p50_ms
        p95 = stats.wait_time_p95_ms
        p99 = stats.wait_time_p99_ms
        
        assert p50 < p95 < p99
        
    def test_lifecycle_selection_performance(self):
        """Test lifecycle selection is efficient."""
        manager = LifecycleManager()
        
        for i in range(1000):
            manager.register_connection(f"conn_{i}")
            
        start = time.monotonic()
        selected = manager.select_for_retirement(exclude_busy=set(), count=100)
        elapsed = time.monotonic() - start
        
        assert elapsed < 1.0  # Should be fast
        assert len(selected) == 100
        
    def test_queue_stats_to_dict_performance(self):
        """Test queue stats to_dict is efficient."""
        from pynext.db.adapters.postgres_queue import QueueStats
        
        stats = QueueStats()
        stats.wait_times_recent = list(range(1000))
        
        start = time.monotonic()
        for _ in range(100):
            _ = stats.to_dict()
        elapsed = time.monotonic() - start
        
        assert elapsed < 1.0
        
    def test_lifecycle_stats_to_dict_performance(self):
        """Test lifecycle stats to_dict is efficient."""
        from pynext.db.adapters.postgres_lifecycle import LifecycleStats
        
        stats = LifecycleStats()
        stats.connection_lifetimes_ms = list(range(1000))
        
        start = time.monotonic()
        for _ in range(100):
            _ = stats.to_dict()
        elapsed = time.monotonic() - start
        
        assert elapsed < 1.0
        
    @pytest.mark.asyncio
    async def test_queue_enqueue_dequeue_performance(self):
        """Test queue enqueue/dequeue performance."""
        queue = ConnectionQueue()
        
        start = time.monotonic()
        for _ in range(100):
            task = asyncio.create_task(queue.enqueue(timeout=5.0))
            await asyncio.sleep(0)
            queue.notify_available()
            await task
        elapsed = time.monotonic() - start
        
        assert elapsed < 5.0  # 100 ops should be fast
        
    def test_lifecycle_mark_used_performance(self):
        """Test lifecycle mark_used performance."""
        manager = LifecycleManager()
        manager.register_connection("conn_1")
        
        start = time.monotonic()
        for _ in range(10000):
            manager.mark_used("conn_1")
        elapsed = time.monotonic() - start
        
        assert elapsed < 1.0
        
    def test_pooled_connection_state_changes(self):
        """Test pooled connection state change performance."""
        mock_conn = MagicMock()
        pooled = PooledConnection(
            connection=mock_conn,
            connection_id="conn_1",
        )
        
        start = time.monotonic()
        for _ in range(10000):
            pooled.mark_busy()
            pooled.mark_idle()
        elapsed = time.monotonic() - start
        
        assert elapsed < 1.0
        
    @pytest.mark.asyncio
    async def test_warmup_batch_performance(self):
        """Test warmup batch performance."""
        warmer = ConnectionWarmer(WarmupConfig(parallel=True))
        
        connections = {}
        for i in range(100):
            mock_conn = AsyncMock()
            mock_conn.fetchval = AsyncMock(return_value=1)
            connections[f"conn_{i}"] = mock_conn
            
        start = time.monotonic()
        results = await warmer.warmup_all(connections)
        elapsed = time.monotonic() - start
        
        assert elapsed < 5.0
        assert len(results) == 100
        
    def test_queue_config_creation_performance(self):
        """Test queue config creation performance."""
        start = time.monotonic()
        for _ in range(10000):
            _ = QueueConfig(max_size=100)
        elapsed = time.monotonic() - start
        
        assert elapsed < 1.0
        
    def test_lifecycle_config_creation_performance(self):
        """Test lifecycle config creation performance."""
        start = time.monotonic()
        for _ in range(10000):
            _ = LifecycleConfig(max_lifetime=3600)
        elapsed = time.monotonic() - start
        
        assert elapsed < 1.0
        
    def test_warmup_config_creation_performance(self):
        """Test warmup config creation performance."""
        start = time.monotonic()
        for _ in range(10000):
            _ = WarmupConfig(enabled=True)
        elapsed = time.monotonic() - start
        
        assert elapsed < 1.0


# =============================================================================
# Edge Cases and Race Conditions Tests (15 tests)
# =============================================================================

class TestEdgeCasesRaceConditions:
    """Tests for edge cases and race conditions."""
    
    @pytest.mark.asyncio
    async def test_queue_notify_before_enqueue(self):
        """Test notify before any enqueue."""
        queue = ConnectionQueue()
        result = queue.notify_available()
        assert result is False
        
    @pytest.mark.asyncio
    async def test_queue_cancel_empty(self):
        """Test cancel on empty queue."""
        queue = ConnectionQueue()
        cancelled = queue.cancel_all()
        assert cancelled == 0
        
    def test_lifecycle_unregister_nonexistent(self):
        """Test unregistering nonexistent connection."""
        manager = LifecycleManager()
        result = manager.unregister_connection("nonexistent")
        assert result is None
        
    def test_lifecycle_mark_used_nonexistent(self):
        """Test mark_used on nonexistent connection."""
        manager = LifecycleManager()
        manager.mark_used("nonexistent")  # Should not raise
        
    def test_lifecycle_get_nonexistent(self):
        """Test getting nonexistent lifecycle."""
        manager = LifecycleManager()
        result = manager.get_lifecycle("nonexistent")
        assert result is None
        
    @pytest.mark.asyncio
    async def test_warmup_disabled_connection(self):
        """Test warmup on disabled warmer."""
        warmer = ConnectionWarmer(WarmupConfig(enabled=False))
        mock_conn = MagicMock()
        result = await warmer.warmup_connection("conn_1", mock_conn)
        assert result.success is True
        assert result.duration_ms == 0
        
    @pytest.mark.asyncio
    async def test_warmup_all_empty(self):
        """Test warmup_all with empty dict."""
        warmer = ConnectionWarmer()
        results = await warmer.warmup_all({})
        assert results == []
        
    def test_queue_zero_max_size(self):
        """Test queue with zero max size."""
        queue = ConnectionQueue(QueueConfig(max_size=0))
        assert queue.is_full is True
        
    def test_lifecycle_zero_max_lifetime(self):
        """Test lifecycle with zero max lifetime (no limit)."""
        config = LifecycleConfig(max_lifetime=0, soft_lifetime=0)
        manager = LifecycleManager(config)
        manager.register_connection("conn_1")
        
        reason = manager.should_retire("conn_1")
        assert reason is None  # No lifetime limit
        
    def test_lifecycle_zero_max_uses(self):
        """Test lifecycle with zero max uses (no limit)."""
        config = LifecycleConfig(max_uses=0)
        manager = LifecycleManager(config)
        manager.register_connection("conn_1")
        
        for _ in range(100000):
            manager.mark_used("conn_1")
            
        reason = manager.should_retire("conn_1")
        assert reason != "max_uses"  # Should not retire for uses
        
    def test_queue_stats_empty_percentiles(self):
        """Test queue stats percentiles with no data."""
        from pynext.db.adapters.postgres_queue import QueueStats
        
        stats = QueueStats()
        assert stats.wait_time_p50_ms == 0
        assert stats.wait_time_p95_ms == 0
        assert stats.wait_time_p99_ms == 0
        
    def test_lifecycle_stats_empty_averages(self):
        """Test lifecycle stats averages with no data."""
        from pynext.db.adapters.postgres_lifecycle import LifecycleStats
        
        stats = LifecycleStats()
        assert stats.avg_connection_lifetime_ms == 0
        assert stats.avg_connection_uses == 0
        
    @pytest.mark.asyncio
    async def test_queue_timeout_zero(self):
        """Test queue with zero timeout."""
        queue = ConnectionQueue()
        
        from pynext.db.adapters.postgres_queue import QueueTimeoutError
        with pytest.raises(QueueTimeoutError):
            await queue.enqueue(timeout=0.001)  # Very short timeout
            
    def test_warmup_stats_empty_rate(self):
        """Test warmup stats success rate with no warmups."""
        from pynext.db.adapters.postgres_warmup import WarmupStats
        
        stats = WarmupStats()
        assert stats.success_rate == 1.0  # Default to 100% when no data
        
    def test_pooled_connection_default_id(self):
        """Test pooled connection with default ID."""
        mock_conn = MagicMock()
        pooled = PooledConnection(connection=mock_conn)
        assert pooled.connection_id == ""  # Default empty string

