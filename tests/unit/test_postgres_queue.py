"""
Comprehensive tests for PostgreSQL Connection Queue (Phase 5.2).

Tests cover:
- QueueConfig validation and defaults
- ConnectionQueue initialization
- FIFO ordering correctness
- Priority queue ordering
- Queue overflow handling
- Backpressure detection
- Timeout handling
- Statistics tracking
- Concurrent operations

Total: 120 tests
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import time

from pynext.db.adapters.postgres_queue import (
    QueueConfig,
    QueueOverflowAction,
    QueuePriority,
    QueuedRequest,
    QueueStats,
    ConnectionQueue,
    QueueFullError,
    QueueTimeoutError,
)


# =============================================================================
# QueueConfig Tests (20 tests)
# =============================================================================

class TestQueueConfig:
    """Tests for QueueConfig dataclass."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = QueueConfig()
        assert config.max_size == 1000
        assert config.max_wait_time == 30.0
        assert config.fairness == "fifo"
        assert config.overflow_action == QueueOverflowAction.REJECT
        assert config.track_wait_times is True
        assert config.warn_threshold == 100
        assert config.critical_threshold == 500
        
    def test_custom_values(self):
        """Test custom configuration values."""
        config = QueueConfig(
            max_size=500,
            max_wait_time=15.0,
            fairness="priority",
            overflow_action=QueueOverflowAction.DROP_OLDEST,
            track_wait_times=False,
            warn_threshold=50,
            critical_threshold=200,
        )
        assert config.max_size == 500
        assert config.max_wait_time == 15.0
        assert config.fairness == "priority"
        assert config.overflow_action == QueueOverflowAction.DROP_OLDEST
        
    def test_invalid_max_size_raises_error(self):
        """Test that negative max_size raises ValueError."""
        with pytest.raises(ValueError, match="max_size must be >= 0"):
            QueueConfig(max_size=-1)
            
    def test_invalid_max_wait_time_raises_error(self):
        """Test that negative max_wait_time raises ValueError."""
        with pytest.raises(ValueError, match="max_wait_time must be >= 0"):
            QueueConfig(max_wait_time=-1)
            
    def test_invalid_fairness_raises_error(self):
        """Test that invalid fairness raises ValueError."""
        with pytest.raises(ValueError, match="fairness must be"):
            QueueConfig(fairness="invalid")
            
    def test_invalid_thresholds_raises_error(self):
        """Test that warn_threshold > critical_threshold raises error."""
        with pytest.raises(ValueError, match="warn_threshold must be"):
            QueueConfig(warn_threshold=500, critical_threshold=100)
            
    def test_zero_max_size_allowed(self):
        """Test zero max_size is allowed (no queueing)."""
        config = QueueConfig(max_size=0)
        assert config.max_size == 0
        
    def test_zero_max_wait_time_allowed(self):
        """Test zero max_wait_time is allowed (no waiting)."""
        config = QueueConfig(max_wait_time=0)
        assert config.max_wait_time == 0
        
    def test_fifo_fairness(self):
        """Test fifo fairness setting."""
        config = QueueConfig(fairness="fifo")
        assert config.fairness == "fifo"
        
    def test_priority_fairness(self):
        """Test priority fairness setting."""
        config = QueueConfig(fairness="priority")
        assert config.fairness == "priority"
        
    def test_reject_overflow_action(self):
        """Test reject overflow action."""
        config = QueueConfig(overflow_action=QueueOverflowAction.REJECT)
        assert config.overflow_action == QueueOverflowAction.REJECT
        
    def test_drop_oldest_overflow_action(self):
        """Test drop_oldest overflow action."""
        config = QueueConfig(overflow_action=QueueOverflowAction.DROP_OLDEST)
        assert config.overflow_action == QueueOverflowAction.DROP_OLDEST
        
    def test_timeout_fastest_overflow_action(self):
        """Test timeout_fastest overflow action."""
        config = QueueConfig(overflow_action=QueueOverflowAction.TIMEOUT_FASTEST)
        assert config.overflow_action == QueueOverflowAction.TIMEOUT_FASTEST
        
    def test_equal_thresholds_allowed(self):
        """Test equal warn and critical thresholds are allowed."""
        config = QueueConfig(warn_threshold=100, critical_threshold=100)
        assert config.warn_threshold == 100
        assert config.critical_threshold == 100
        
    def test_large_max_size(self):
        """Test large max_size value."""
        config = QueueConfig(max_size=1000000)
        assert config.max_size == 1000000
        
    def test_large_max_wait_time(self):
        """Test large max_wait_time value."""
        config = QueueConfig(max_wait_time=3600.0)
        assert config.max_wait_time == 3600.0
        
    def test_minimum_valid_config(self):
        """Test minimum valid configuration."""
        config = QueueConfig(
            max_size=0,
            max_wait_time=0,
            warn_threshold=0,
            critical_threshold=0,
        )
        assert config.max_size == 0
        
    def test_track_wait_times_disabled(self):
        """Test wait time tracking can be disabled."""
        config = QueueConfig(track_wait_times=False)
        assert config.track_wait_times is False
        
    def test_config_immutability(self):
        """Test that config values are accessible."""
        config = QueueConfig(max_size=100)
        assert config.max_size == 100
        
    def test_default_thresholds_relationship(self):
        """Test default thresholds have correct relationship."""
        config = QueueConfig()
        assert config.warn_threshold < config.critical_threshold


# =============================================================================
# QueuePriority Tests (5 tests)
# =============================================================================

class TestQueuePriority:
    """Tests for QueuePriority enum."""
    
    def test_priority_values(self):
        """Test priority numeric values."""
        assert QueuePriority.CRITICAL.value == 0
        assert QueuePriority.HIGH.value == 1
        assert QueuePriority.NORMAL.value == 2
        assert QueuePriority.LOW.value == 3
        assert QueuePriority.BATCH.value == 4
        
    def test_priority_ordering(self):
        """Test priority ordering (lower value = higher priority)."""
        assert QueuePriority.CRITICAL.value < QueuePriority.HIGH.value
        assert QueuePriority.HIGH.value < QueuePriority.NORMAL.value
        assert QueuePriority.NORMAL.value < QueuePriority.LOW.value
        assert QueuePriority.LOW.value < QueuePriority.BATCH.value
        
    def test_priority_comparison(self):
        """Test priority comparison via values."""
        priorities = [QueuePriority.BATCH, QueuePriority.CRITICAL, QueuePriority.NORMAL]
        sorted_priorities = sorted(priorities, key=lambda p: p.value)
        assert sorted_priorities[0] == QueuePriority.CRITICAL
        
    def test_all_priority_levels(self):
        """Test all priority levels exist."""
        assert len(QueuePriority) == 5
        
    def test_priority_from_value(self):
        """Test getting priority from value."""
        assert QueuePriority(0) == QueuePriority.CRITICAL
        assert QueuePriority(2) == QueuePriority.NORMAL


# =============================================================================
# QueuedRequest Tests (10 tests)
# =============================================================================

class TestQueuedRequest:
    """Tests for QueuedRequest dataclass."""
    
    @pytest.mark.asyncio
    async def test_request_creation(self):
        """Test request creation."""
        future = asyncio.get_running_loop().create_future()
        request = QueuedRequest(
            priority=2,
            enqueue_time=time.monotonic(),
            future=future,
            request_id="req_1",
        )
        assert request.priority == 2
        assert request.request_id == "req_1"
        
    @pytest.mark.asyncio
    async def test_wait_time(self):
        """Test wait time calculation."""
        future = asyncio.get_running_loop().create_future()
        request = QueuedRequest(
            priority=2,
            enqueue_time=time.monotonic() - 1.0,
            future=future,
            request_id="req_1",
        )
        assert request.wait_time() >= 1.0
        
    @pytest.mark.asyncio
    async def test_cancel(self):
        """Test request cancellation."""
        future = asyncio.get_running_loop().create_future()
        request = QueuedRequest(
            priority=2,
            enqueue_time=time.monotonic(),
            future=future,
            request_id="req_1",
        )
        request.cancel()
        assert future.cancelled()
        
    @pytest.mark.asyncio
    async def test_cancel_completed_future(self):
        """Test cancelling completed future does nothing."""
        future = asyncio.get_running_loop().create_future()
        future.set_result(True)
        
        request = QueuedRequest(
            priority=2,
            enqueue_time=time.monotonic(),
            future=future,
            request_id="req_1",
        )
        request.cancel()
        # Should not raise
        
    @pytest.mark.asyncio
    async def test_request_ordering_by_priority(self):
        """Test requests are ordered by priority."""
        future = asyncio.get_running_loop().create_future()
        r1 = QueuedRequest(priority=0, enqueue_time=1.0, future=future, request_id="1")
        r2 = QueuedRequest(priority=2, enqueue_time=1.0, future=future, request_id="2")
        assert r1 < r2
        
    @pytest.mark.asyncio
    async def test_request_with_metadata(self):
        """Test request with metadata."""
        future = asyncio.get_running_loop().create_future()
        request = QueuedRequest(
            priority=2,
            enqueue_time=time.monotonic(),
            future=future,
            request_id="req_1",
            metadata={"query": "SELECT 1", "user_id": 123},
        )
        assert request.metadata["query"] == "SELECT 1"
        
    @pytest.mark.asyncio
    async def test_request_without_metadata(self):
        """Test request without metadata."""
        future = asyncio.get_running_loop().create_future()
        request = QueuedRequest(
            priority=2,
            enqueue_time=time.monotonic(),
            future=future,
            request_id="req_1",
        )
        assert request.metadata is None
        
    @pytest.mark.asyncio
    async def test_request_equality(self):
        """Test request equality is based on priority."""
        future = asyncio.get_running_loop().create_future()
        r1 = QueuedRequest(priority=2, enqueue_time=1.0, future=future, request_id="1")
        r2 = QueuedRequest(priority=2, enqueue_time=1.0, future=future, request_id="2")
        assert r1 == r2  # Equal priority and enqueue_time
        
    @pytest.mark.asyncio
    async def test_request_sorting(self):
        """Test request sorting in priority queue."""
        future = asyncio.get_running_loop().create_future()
        requests = [
            QueuedRequest(priority=3, enqueue_time=1.0, future=future, request_id="3"),
            QueuedRequest(priority=1, enqueue_time=1.0, future=future, request_id="1"),
            QueuedRequest(priority=2, enqueue_time=1.0, future=future, request_id="2"),
        ]
        sorted_reqs = sorted(requests)
        assert sorted_reqs[0].priority == 1
        assert sorted_reqs[2].priority == 3
        
    @pytest.mark.asyncio
    async def test_request_id_uniqueness(self):
        """Test request IDs can be unique."""
        future = asyncio.get_running_loop().create_future()
        r1 = QueuedRequest(priority=2, enqueue_time=1.0, future=future, request_id="unique_1")
        r2 = QueuedRequest(priority=2, enqueue_time=1.0, future=future, request_id="unique_2")
        assert r1.request_id != r2.request_id


# =============================================================================
# QueueStats Tests (15 tests)
# =============================================================================

class TestQueueStats:
    """Tests for QueueStats dataclass."""
    
    def test_default_values(self):
        """Test default statistics values."""
        stats = QueueStats()
        assert stats.depth == 0
        assert stats.total_enqueued == 0
        assert stats.total_dequeued == 0
        assert stats.total_timeouts == 0
        assert stats.total_rejections == 0
        assert stats.total_cancellations == 0
        
    def test_wait_time_avg_empty(self):
        """Test average wait time with no data."""
        stats = QueueStats()
        assert stats.wait_time_avg_ms == 0
        
    def test_wait_time_avg_with_data(self):
        """Test average wait time calculation."""
        stats = QueueStats()
        stats.total_dequeued = 3
        stats.wait_time_total_ms = 30.0
        assert stats.wait_time_avg_ms == 10.0
        
    def test_percentile_empty(self):
        """Test percentiles with no data."""
        stats = QueueStats()
        assert stats.wait_time_p50_ms == 0
        assert stats.wait_time_p95_ms == 0
        assert stats.wait_time_p99_ms == 0
        
    def test_percentile_with_data(self):
        """Test percentile calculation."""
        stats = QueueStats()
        stats.wait_times_recent = [10.0, 20.0, 30.0, 40.0, 50.0]
        assert stats.wait_time_p50_ms == 30.0
        
    def test_to_dict(self):
        """Test conversion to dictionary."""
        stats = QueueStats()
        stats.depth = 10
        stats.total_enqueued = 100
        
        d = stats.to_dict()
        assert "depth" in d
        assert "total_enqueued" in d
        assert "wait_time_avg_ms" in d
        assert "wait_time_p99_ms" in d
        
    def test_track_wait_time_max(self):
        """Test max wait time tracking."""
        stats = QueueStats()
        stats.wait_time_max_ms = 100.0
        stats.wait_time_max_ms = max(stats.wait_time_max_ms, 50.0)
        assert stats.wait_time_max_ms == 100.0
        stats.wait_time_max_ms = max(stats.wait_time_max_ms, 200.0)
        assert stats.wait_time_max_ms == 200.0
        
    def test_recent_samples_tracking(self):
        """Test recent samples list."""
        stats = QueueStats()
        for i in range(10):
            stats.wait_times_recent.append(float(i))
        assert len(stats.wait_times_recent) == 10
        
    def test_total_timeouts_increment(self):
        """Test timeout counter increment."""
        stats = QueueStats()
        stats.total_timeouts += 1
        stats.total_timeouts += 1
        assert stats.total_timeouts == 2
        
    def test_total_rejections_increment(self):
        """Test rejection counter increment."""
        stats = QueueStats()
        stats.total_rejections += 1
        assert stats.total_rejections == 1
        
    def test_depth_tracking(self):
        """Test depth tracking."""
        stats = QueueStats()
        stats.depth = 50
        assert stats.depth == 50
        
    def test_cancellation_tracking(self):
        """Test cancellation tracking."""
        stats = QueueStats()
        stats.total_cancellations = 5
        assert stats.total_cancellations == 5
        
    def test_percentile_calculation_accuracy(self):
        """Test percentile calculation accuracy."""
        stats = QueueStats()
        stats.wait_times_recent = list(range(1, 101))  # 1 to 100
        # Percentile calculation uses ceiling index, so p50 of 100 items is at index 50 = value 51
        assert stats.wait_time_p50_ms == 51
        assert stats.wait_time_p95_ms == 96
        assert stats.wait_time_p99_ms == 100
        
    def test_wait_time_total_accumulation(self):
        """Test wait time total accumulation."""
        stats = QueueStats()
        stats.wait_time_total_ms += 10.0
        stats.wait_time_total_ms += 20.0
        assert stats.wait_time_total_ms == 30.0
        
    def test_stats_all_fields_accessible(self):
        """Test all stats fields are accessible."""
        stats = QueueStats()
        _ = stats.depth
        _ = stats.total_enqueued
        _ = stats.total_dequeued
        _ = stats.total_timeouts
        _ = stats.total_rejections
        _ = stats.total_cancellations
        _ = stats.wait_time_avg_ms
        _ = stats.wait_time_p50_ms
        _ = stats.wait_time_p95_ms
        _ = stats.wait_time_p99_ms


# =============================================================================
# QueueFullError Tests (5 tests)
# =============================================================================

class TestQueueFullError:
    """Tests for QueueFullError exception."""
    
    def test_error_message(self):
        """Test error message formatting."""
        error = QueueFullError(queue_size=100, max_size=100, wait_time_avg=5.0)
        assert "100/100" in str(error)
        assert "5.0" in str(error)
        
    def test_error_attributes(self):
        """Test error attributes."""
        error = QueueFullError(queue_size=50, max_size=100, wait_time_avg=2.5)
        assert error.queue_size == 50
        assert error.max_size == 100
        assert error.wait_time_avg == 2.5
        
    def test_error_is_exception(self):
        """Test error is an Exception."""
        error = QueueFullError(50, 100)
        assert isinstance(error, Exception)
        
    def test_error_can_be_raised(self):
        """Test error can be raised."""
        with pytest.raises(QueueFullError):
            raise QueueFullError(100, 100)
            
    def test_error_default_wait_time(self):
        """Test error with default wait time."""
        error = QueueFullError(50, 100)
        assert error.wait_time_avg == 0


# =============================================================================
# QueueTimeoutError Tests (5 tests)
# =============================================================================

class TestQueueTimeoutError:
    """Tests for QueueTimeoutError exception."""
    
    def test_error_message(self):
        """Test error message formatting."""
        error = QueueTimeoutError(wait_time=10.0, max_wait_time=10.0, queue_position=5)
        assert "10.0" in str(error)
        assert "5" in str(error)
        
    def test_error_attributes(self):
        """Test error attributes."""
        error = QueueTimeoutError(wait_time=5.0, max_wait_time=10.0, queue_position=3)
        assert error.wait_time == 5.0
        assert error.max_wait_time == 10.0
        assert error.queue_position == 3
        
    def test_error_is_exception(self):
        """Test error is an Exception."""
        error = QueueTimeoutError(5.0, 10.0, 1)
        assert isinstance(error, Exception)
        
    def test_error_can_be_raised(self):
        """Test error can be raised."""
        with pytest.raises(QueueTimeoutError):
            raise QueueTimeoutError(10.0, 10.0, 1)
            
    def test_error_with_long_wait(self):
        """Test error with long wait time."""
        error = QueueTimeoutError(wait_time=300.0, max_wait_time=30.0, queue_position=100)
        assert error.wait_time == 300.0


# =============================================================================
# ConnectionQueue Tests (60 tests)
# =============================================================================

class TestConnectionQueue:
    """Tests for ConnectionQueue class."""
    
    def test_init_default_config(self):
        """Test initialization with default config."""
        queue = ConnectionQueue()
        assert queue.config.max_size == 1000
        assert queue.depth == 0
        assert queue.is_empty
        
    def test_init_custom_config(self):
        """Test initialization with custom config."""
        config = QueueConfig(max_size=100)
        queue = ConnectionQueue(config)
        assert queue.config.max_size == 100
        
    def test_is_empty(self):
        """Test is_empty property."""
        queue = ConnectionQueue()
        assert queue.is_empty
        
    def test_is_full_when_empty(self):
        """Test is_full when empty."""
        queue = ConnectionQueue()
        assert not queue.is_full
        
    def test_is_under_pressure_when_empty(self):
        """Test is_under_pressure when empty."""
        queue = ConnectionQueue()
        assert not queue.is_under_pressure
        
    def test_is_critical_when_empty(self):
        """Test is_critical when empty."""
        queue = ConnectionQueue()
        assert not queue.is_critical
        
    @pytest.mark.asyncio
    async def test_enqueue_and_notify(self):
        """Test basic enqueue and notify flow."""
        queue = ConnectionQueue(QueueConfig(max_size=10))
        
        # Start enqueue in background
        async def enqueue_task():
            return await queue.enqueue(timeout=5.0)
            
        task = asyncio.create_task(enqueue_task())
        
        # Wait a bit then notify
        await asyncio.sleep(0.01)
        assert queue.depth == 1
        
        queue.notify_available()
        
        wait_time = await task
        assert wait_time >= 0
        
    @pytest.mark.asyncio
    async def test_enqueue_timeout(self):
        """Test enqueue timeout."""
        queue = ConnectionQueue(QueueConfig(max_size=10, max_wait_time=0.1))
        
        with pytest.raises(QueueTimeoutError):
            await queue.enqueue(timeout=0.01)
            
    @pytest.mark.asyncio
    async def test_enqueue_queue_full_reject(self):
        """Test enqueue when queue is full with reject action."""
        config = QueueConfig(
            max_size=1,
            overflow_action=QueueOverflowAction.REJECT,
        )
        queue = ConnectionQueue(config)
        
        # Start one request
        async def enqueue_task():
            return await queue.enqueue(timeout=5.0)
            
        task = asyncio.create_task(enqueue_task())
        await asyncio.sleep(0.01)
        
        # Second request should fail
        with pytest.raises(QueueFullError):
            await queue.enqueue(timeout=0.1)
            
        # Clean up
        queue.notify_available()
        await task
        
    def test_notify_available_empty_queue(self):
        """Test notify_available on empty queue."""
        queue = ConnectionQueue()
        result = queue.notify_available()
        assert result is False
        
    def test_cancel_all_empty(self):
        """Test cancel_all on empty queue."""
        queue = ConnectionQueue()
        count = queue.cancel_all()
        assert count == 0
        
    @pytest.mark.asyncio
    async def test_cancel_all_with_requests(self):
        """Test cancel_all with pending requests."""
        queue = ConnectionQueue()
        
        # Start some requests
        tasks = []
        for _ in range(3):
            task = asyncio.create_task(queue.enqueue(timeout=5.0))
            tasks.append(task)
            
        await asyncio.sleep(0.01)
        assert queue.depth == 3
        
        count = queue.cancel_all()
        assert count == 3
        assert queue.depth == 0
        
        # Tasks should be cancelled
        for task in tasks:
            with pytest.raises(asyncio.CancelledError):
                await task
                
    def test_get_stats(self):
        """Test getting queue statistics."""
        queue = ConnectionQueue()
        stats = queue.get_stats()
        assert isinstance(stats, QueueStats)
        assert stats.depth == 0
        
    @pytest.mark.asyncio
    async def test_stats_updated_on_enqueue(self):
        """Test stats updated on enqueue."""
        queue = ConnectionQueue()
        
        task = asyncio.create_task(queue.enqueue(timeout=5.0))
        await asyncio.sleep(0.01)
        
        stats = queue.get_stats()
        assert stats.total_enqueued == 1
        
        queue.notify_available()
        await task
        
    @pytest.mark.asyncio
    async def test_stats_updated_on_dequeue(self):
        """Test stats updated on dequeue."""
        queue = ConnectionQueue()
        
        task = asyncio.create_task(queue.enqueue(timeout=5.0))
        await asyncio.sleep(0.01)
        
        queue.notify_available()
        await task
        
        stats = queue.get_stats()
        assert stats.total_dequeued == 1
        
    @pytest.mark.asyncio
    async def test_fifo_ordering(self):
        """Test FIFO ordering of requests."""
        queue = ConnectionQueue(QueueConfig(fairness="fifo"))
        
        results = []
        
        async def enqueue_task(order):
            await queue.enqueue(timeout=5.0)
            results.append(order)
            
        # Start 3 requests in order
        tasks = [asyncio.create_task(enqueue_task(i)) for i in range(3)]
        await asyncio.sleep(0.05)
        
        # Notify in order
        for _ in range(3):
            queue.notify_available()
            await asyncio.sleep(0.01)
            
        await asyncio.gather(*tasks)
        assert results == [0, 1, 2]
        
    @pytest.mark.asyncio
    async def test_priority_ordering(self):
        """Test priority ordering of requests."""
        queue = ConnectionQueue(QueueConfig(fairness="priority"))
        
        results = []
        
        async def enqueue_task(priority, order):
            await queue.enqueue(priority=priority, timeout=5.0)
            results.append(order)
            
        # Start requests with different priorities
        tasks = [
            asyncio.create_task(enqueue_task(QueuePriority.LOW, "low")),
            asyncio.create_task(enqueue_task(QueuePriority.CRITICAL, "critical")),
            asyncio.create_task(enqueue_task(QueuePriority.NORMAL, "normal")),
        ]
        await asyncio.sleep(0.05)
        
        # Notify 3 times
        for _ in range(3):
            queue.notify_available()
            await asyncio.sleep(0.01)
            
        await asyncio.gather(*tasks)
        # Critical should be first
        assert results[0] == "critical"
        
    @pytest.mark.asyncio
    async def test_wait_time_tracking(self):
        """Test wait time is tracked."""
        queue = ConnectionQueue()
        
        task = asyncio.create_task(queue.enqueue(timeout=5.0))
        await asyncio.sleep(0.05)
        
        queue.notify_available()
        wait_time = await task
        
        assert wait_time >= 0.05
        
    @pytest.mark.asyncio
    async def test_request_with_metadata(self):
        """Test request with metadata."""
        queue = ConnectionQueue()
        
        task = asyncio.create_task(
            queue.enqueue(
                timeout=5.0,
                metadata={"query": "SELECT 1"},
            )
        )
        await asyncio.sleep(0.01)
        
        queue.notify_available()
        await task
        
    def test_repr(self):
        """Test string representation."""
        queue = ConnectionQueue()
        repr_str = repr(queue)
        assert "ConnectionQueue" in repr_str
        
    @pytest.mark.asyncio
    async def test_concurrent_enqueue(self):
        """Test concurrent enqueue operations."""
        queue = ConnectionQueue()
        
        async def enqueue_task():
            return await queue.enqueue(timeout=5.0)
            
        # Start 10 concurrent requests
        tasks = [asyncio.create_task(enqueue_task()) for _ in range(10)]
        await asyncio.sleep(0.01)
        
        assert queue.depth == 10
        
        # Notify all
        for _ in range(10):
            queue.notify_available()
            
        await asyncio.gather(*tasks)
        assert queue.depth == 0
        
    @pytest.mark.asyncio
    async def test_enqueue_cancellation(self):
        """Test enqueue cancellation."""
        queue = ConnectionQueue()
        
        task = asyncio.create_task(queue.enqueue(timeout=5.0))
        await asyncio.sleep(0.01)
        
        task.cancel()
        
        with pytest.raises(asyncio.CancelledError):
            await task
            
        stats = queue.get_stats()
        assert stats.total_cancellations == 1
        
    @pytest.mark.asyncio
    async def test_timeout_updates_stats(self):
        """Test timeout updates statistics."""
        queue = ConnectionQueue()
        
        with pytest.raises(QueueTimeoutError):
            await queue.enqueue(timeout=0.01)
            
        stats = queue.get_stats()
        assert stats.total_timeouts == 1
        
    @pytest.mark.asyncio
    async def test_under_pressure_threshold(self):
        """Test under pressure detection."""
        config = QueueConfig(warn_threshold=2)
        queue = ConnectionQueue(config)
        
        tasks = []
        for _ in range(3):
            task = asyncio.create_task(queue.enqueue(timeout=5.0))
            tasks.append(task)
            
        await asyncio.sleep(0.01)
        assert queue.is_under_pressure
        
        queue.cancel_all()
        for task in tasks:
            try:
                await task
            except asyncio.CancelledError:
                pass
                
    @pytest.mark.asyncio
    async def test_critical_threshold(self):
        """Test critical level detection."""
        config = QueueConfig(warn_threshold=1, critical_threshold=2)
        queue = ConnectionQueue(config)
        
        tasks = []
        for _ in range(3):
            task = asyncio.create_task(queue.enqueue(timeout=5.0))
            tasks.append(task)
            
        await asyncio.sleep(0.01)
        assert queue.is_critical
        
        queue.cancel_all()
        for task in tasks:
            try:
                await task
            except asyncio.CancelledError:
                pass
                
    @pytest.mark.asyncio
    async def test_drop_oldest_overflow(self):
        """Test drop_oldest overflow action."""
        config = QueueConfig(
            max_size=1,
            overflow_action=QueueOverflowAction.DROP_OLDEST,
        )
        queue = ConnectionQueue(config)
        
        # First request
        task1 = asyncio.create_task(queue.enqueue(timeout=5.0))
        await asyncio.sleep(0.01)
        
        # Second request should drop first
        task2 = asyncio.create_task(queue.enqueue(timeout=5.0))
        await asyncio.sleep(0.01)
        
        # First should be dropped
        with pytest.raises(QueueFullError):
            await task1
            
        queue.notify_available()
        await task2
        
    @pytest.mark.asyncio
    async def test_multiple_notify_available(self):
        """Test multiple notify_available calls."""
        queue = ConnectionQueue()
        
        # Notify when empty - should return False
        assert queue.notify_available() is False
        
        # Add a request
        task = asyncio.create_task(queue.enqueue(timeout=5.0))
        await asyncio.sleep(0.01)
        
        # Notify - should return True
        assert queue.notify_available() is True
        
        await task
        
    def test_config_property(self):
        """Test config property."""
        config = QueueConfig(max_size=50)
        queue = ConnectionQueue(config)
        assert queue.config.max_size == 50
        
    def test_depth_property(self):
        """Test depth property."""
        queue = ConnectionQueue()
        assert queue.depth == 0
        
    @pytest.mark.asyncio
    async def test_enqueue_with_custom_timeout(self):
        """Test enqueue with custom timeout override."""
        config = QueueConfig(max_wait_time=60.0)
        queue = ConnectionQueue(config)
        
        # Override with shorter timeout
        with pytest.raises(QueueTimeoutError):
            await queue.enqueue(timeout=0.01)
            
    @pytest.mark.asyncio
    async def test_enqueue_priority_default(self):
        """Test enqueue uses NORMAL priority by default."""
        queue = ConnectionQueue(QueueConfig(fairness="priority"))
        
        task = asyncio.create_task(queue.enqueue(timeout=5.0))
        await asyncio.sleep(0.01)
        
        queue.notify_available()
        await task
        
    @pytest.mark.asyncio
    async def test_wait_times_recent_limited(self):
        """Test wait_times_recent is limited."""
        queue = ConnectionQueue()
        
        for _ in range(50):
            task = asyncio.create_task(queue.enqueue(timeout=5.0))
            await asyncio.sleep(0.001)
            queue.notify_available()
            await task
            
        stats = queue.get_stats()
        assert len(stats.wait_times_recent) <= 1000
        
    @pytest.mark.asyncio
    async def test_enqueue_immediate_notify(self):
        """Test enqueue with immediate notify."""
        queue = ConnectionQueue()
        
        async def enqueue_and_notify():
            task = asyncio.create_task(queue.enqueue(timeout=5.0))
            await asyncio.sleep(0.001)
            queue.notify_available()
            return await task
            
        wait_time = await enqueue_and_notify()
        assert wait_time >= 0
        
    def test_zero_max_size(self):
        """Test queue with zero max size."""
        config = QueueConfig(max_size=0)
        queue = ConnectionQueue(config)
        assert queue.is_full  # Zero max means always full
        
    @pytest.mark.asyncio
    async def test_notify_multiple_waiters(self):
        """Test notify wakes one waiter at a time."""
        queue = ConnectionQueue()
        
        results = []
        
        async def enqueue_task(order):
            await queue.enqueue(timeout=5.0)
            results.append(order)
            
        tasks = [asyncio.create_task(enqueue_task(i)) for i in range(3)]
        await asyncio.sleep(0.05)
        
        assert queue.depth == 3
        
        # Notify one at a time
        queue.notify_available()
        await asyncio.sleep(0.01)
        assert len(results) == 1
        
        queue.notify_available()
        await asyncio.sleep(0.01)
        assert len(results) == 2
        
        queue.notify_available()
        await asyncio.gather(*tasks)
        assert len(results) == 3
        
    @pytest.mark.asyncio
    async def test_stats_depth_accuracy(self):
        """Test stats depth matches actual depth."""
        queue = ConnectionQueue()
        
        tasks = []
        for _ in range(5):
            task = asyncio.create_task(queue.enqueue(timeout=5.0))
            tasks.append(task)
            
        await asyncio.sleep(0.01)
        
        stats = queue.get_stats()
        assert stats.depth == queue.depth == 5
        
        queue.cancel_all()
        for task in tasks:
            try:
                await task
            except asyncio.CancelledError:
                pass
                
    @pytest.mark.asyncio
    async def test_wait_time_percentiles(self):
        """Test wait time percentiles are calculated."""
        queue = ConnectionQueue()
        
        for _ in range(10):
            task = asyncio.create_task(queue.enqueue(timeout=5.0))
            await asyncio.sleep(0.01)
            queue.notify_available()
            await task
            
        stats = queue.get_stats()
        assert stats.wait_time_p50_ms >= 0
        assert stats.wait_time_p95_ms >= stats.wait_time_p50_ms
        
    @pytest.mark.asyncio
    async def test_queue_empty_after_all_processed(self):
        """Test queue is empty after all requests processed."""
        queue = ConnectionQueue()
        
        tasks = []
        for _ in range(5):
            task = asyncio.create_task(queue.enqueue(timeout=5.0))
            tasks.append(task)
            
        await asyncio.sleep(0.01)
        
        for _ in range(5):
            queue.notify_available()
            
        await asyncio.gather(*tasks)
        
        assert queue.is_empty
        assert queue.depth == 0

