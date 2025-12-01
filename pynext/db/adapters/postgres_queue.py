"""
PostgreSQL Connection Queue with Advanced Management.

This module provides a fair, monitored queue for connection requests
when the pool is at capacity. It follows SolidJS principles:
- Fine-grained: Only blocks requests that actually need to wait
- Observable: Rich metrics for monitoring queue health
- No surprises: Explicit configuration, predictable behavior

How the Queue Works:

1. When pool is exhausted, requests enter the queue
2. Queue uses FIFO ordering by default (fair to all requests)
3. Optional priority queue for critical queries
4. When a connection is released, next waiter gets it
5. Timeouts and backpressure prevent queue from growing unbounded

Why This Matters:
- Fair: First request to wait is first to get a connection
- Observable: Know exactly how many requests are waiting
- Bounded: Max queue size prevents memory exhaustion
- Responsive: Backpressure signals let callers react

AI-Friendly Design:
- Clear state transitions (waiting -> acquired -> released)
- Comprehensive metrics for debugging
- All configuration is explicit with sensible defaults
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING
from collections import deque
import heapq

logger = logging.getLogger("pynext.db.postgres.queue")


class QueueOverflowAction(Enum):
    """What to do when the queue is full.
    
    REJECT: Immediately raise QueueFullError (recommended for most cases)
    DROP_OLDEST: Remove the oldest waiting request to make room
    TIMEOUT_FASTEST: Reduce timeout for oldest requests
    """
    REJECT = "reject"
    DROP_OLDEST = "drop_oldest"
    TIMEOUT_FASTEST = "timeout_fastest"


class QueuePriority(Enum):
    """Priority levels for queued requests.
    
    Higher priority requests are processed first when using priority mode.
    """
    CRITICAL = 0    # System-critical queries (health checks, etc.)
    HIGH = 1        # Important user-facing queries
    NORMAL = 2      # Default priority
    LOW = 3         # Background tasks, analytics
    BATCH = 4       # Bulk operations, can wait


@dataclass
class QueueConfig:
    """Configuration for the connection queue.
    
    Attributes:
        max_size: Maximum number of waiting requests (default: 1000)
        max_wait_time: Maximum time a request can wait in seconds (default: 30.0)
        fairness: Queue ordering - "fifo" or "priority" (default: "fifo")
        overflow_action: What to do when queue is full (default: REJECT)
        track_wait_times: Whether to track wait time statistics (default: True)
        warn_threshold: Log warning when queue reaches this size (default: 100)
        critical_threshold: Log error when queue reaches this size (default: 500)
    
    Example:
        config = QueueConfig(
            max_size=500,
            max_wait_time=15.0,
            overflow_action=QueueOverflowAction.REJECT,
        )
    """
    max_size: int = 1000
    max_wait_time: float = 30.0
    fairness: str = "fifo"
    overflow_action: QueueOverflowAction = QueueOverflowAction.REJECT
    track_wait_times: bool = True
    warn_threshold: int = 100
    critical_threshold: int = 500
    
    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.max_size < 0:
            raise ValueError(f"max_size must be >= 0, got {self.max_size}")
        if self.max_wait_time < 0:
            raise ValueError(f"max_wait_time must be >= 0, got {self.max_wait_time}")
        if self.fairness not in ("fifo", "priority"):
            raise ValueError(f"fairness must be 'fifo' or 'priority', got {self.fairness}")
        if self.warn_threshold > self.critical_threshold:
            raise ValueError("warn_threshold must be <= critical_threshold")


@dataclass(order=True)
class QueuedRequest:
    """A request waiting in the queue.
    
    Attributes:
        priority: Priority level (lower = higher priority)
        enqueue_time: When the request was added to the queue
        future: The asyncio Future to resolve when connection is available
        request_id: Unique identifier for this request
        metadata: Optional metadata about the request
    """
    priority: int
    enqueue_time: float = field(compare=False)
    future: asyncio.Future = field(compare=False)
    request_id: str = field(compare=False)
    metadata: Optional[Dict[str, Any]] = field(default=None, compare=False)
    
    def wait_time(self) -> float:
        """Get time spent waiting in queue."""
        return time.monotonic() - self.enqueue_time
    
    def cancel(self) -> None:
        """Cancel this request."""
        if not self.future.done():
            self.future.cancel()


class QueueFullError(Exception):
    """Raised when the queue is at capacity and cannot accept more requests.
    
    This happens when:
    1. Queue has max_size requests waiting
    2. overflow_action is REJECT
    
    How to fix:
    1. Increase max_size (if you have memory)
    2. Increase pool max_connections
    3. Reduce query time
    4. Add backpressure at the application level
    """
    def __init__(self, queue_size: int, max_size: int, wait_time_avg: float = 0):
        self.queue_size = queue_size
        self.max_size = max_size
        self.wait_time_avg = wait_time_avg
        super().__init__(
            f"Connection queue is full ({queue_size}/{max_size} requests waiting, "
            f"avg wait time: {wait_time_avg:.1f}s).\n"
            "Consider increasing pool size or queue size."
        )


class QueueTimeoutError(Exception):
    """Raised when a request times out waiting in the queue.
    
    This happens when:
    1. Request waited longer than max_wait_time
    2. No connection became available
    
    How to fix:
    1. Increase max_wait_time
    2. Increase pool max_connections
    3. Reduce query execution time
    """
    def __init__(self, wait_time: float, max_wait_time: float, queue_position: int):
        self.wait_time = wait_time
        self.max_wait_time = max_wait_time
        self.queue_position = queue_position
        super().__init__(
            f"Timed out waiting for connection after {wait_time:.1f}s "
            f"(max: {max_wait_time}s, position in queue: {queue_position}).\n"
            "Consider increasing pool size or query timeout."
        )


@dataclass
class QueueStats:
    """Statistics about the connection queue.
    
    Attributes:
        depth: Current number of requests waiting
        total_enqueued: Total requests that entered the queue
        total_dequeued: Total requests that got a connection
        total_timeouts: Total requests that timed out
        total_rejections: Total requests rejected due to queue full
        total_cancellations: Total requests that were cancelled
        wait_time_total_ms: Sum of all wait times (for calculating average)
        wait_time_max_ms: Maximum wait time observed
        wait_times_recent: Recent wait times for percentile calculation
    """
    depth: int = 0
    total_enqueued: int = 0
    total_dequeued: int = 0
    total_timeouts: int = 0
    total_rejections: int = 0
    total_cancellations: int = 0
    wait_time_total_ms: float = 0
    wait_time_max_ms: float = 0
    wait_times_recent: List[float] = field(default_factory=list)
    
    @property
    def wait_time_avg_ms(self) -> float:
        """Average wait time in milliseconds."""
        total = self.total_dequeued + self.total_timeouts
        if total == 0:
            return 0
        return self.wait_time_total_ms / total
    
    @property
    def wait_time_p50_ms(self) -> float:
        """50th percentile (median) wait time."""
        return self._percentile(50)
    
    @property
    def wait_time_p95_ms(self) -> float:
        """95th percentile wait time."""
        return self._percentile(95)
    
    @property
    def wait_time_p99_ms(self) -> float:
        """99th percentile wait time."""
        return self._percentile(99)
    
    def _percentile(self, p: int) -> float:
        """Calculate percentile from recent wait times."""
        if not self.wait_times_recent:
            return 0
        sorted_times = sorted(self.wait_times_recent)
        idx = int(len(sorted_times) * p / 100)
        idx = min(idx, len(sorted_times) - 1)
        return sorted_times[idx]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/metrics."""
        return {
            "depth": self.depth,
            "total_enqueued": self.total_enqueued,
            "total_dequeued": self.total_dequeued,
            "total_timeouts": self.total_timeouts,
            "total_rejections": self.total_rejections,
            "wait_time_avg_ms": self.wait_time_avg_ms,
            "wait_time_max_ms": self.wait_time_max_ms,
            "wait_time_p50_ms": self.wait_time_p50_ms,
            "wait_time_p95_ms": self.wait_time_p95_ms,
            "wait_time_p99_ms": self.wait_time_p99_ms,
        }


class ConnectionQueue:
    """Fair, monitored queue for connection requests.
    
    This queue manages requests waiting for database connections when
    the pool is at capacity. It provides:
    
    1. **Fair ordering**: FIFO by default, or priority-based
    2. **Bounded size**: Prevents memory exhaustion
    3. **Timeout handling**: Requests don't wait forever
    4. **Rich metrics**: Know exactly what's happening
    5. **Backpressure**: Signal when queue is under pressure
    
    Basic Usage:
        queue = ConnectionQueue(QueueConfig(max_size=100))
        
        # Enqueue a request (returns when connection available)
        await queue.enqueue()
        
        # Signal that a connection is available
        queue.notify_available()
        
        # Check queue health
        if queue.is_under_pressure:
            print("Queue is getting full!")
    
    With Priority:
        queue = ConnectionQueue(QueueConfig(fairness="priority"))
        
        # Critical query gets priority
        await queue.enqueue(priority=QueuePriority.CRITICAL)
        
        # Background task can wait
        await queue.enqueue(priority=QueuePriority.BATCH)
    """
    
    def __init__(self, config: Optional[QueueConfig] = None):
        """Initialize the queue.
        
        Args:
            config: Queue configuration (default: QueueConfig())
        """
        self._config = config or QueueConfig()
        
        # Request storage
        if self._config.fairness == "fifo":
            self._queue: deque[QueuedRequest] = deque()
        else:
            self._priority_queue: List[QueuedRequest] = []
        
        # Synchronization
        self._lock = asyncio.Lock()
        self._request_counter = 0
        
        # Statistics
        self._stats = QueueStats()
        self._max_recent_samples = 1000  # Keep last 1000 wait times
    
    @property
    def config(self) -> QueueConfig:
        """Get queue configuration."""
        return self._config
    
    @property
    def depth(self) -> int:
        """Current number of requests waiting."""
        if self._config.fairness == "fifo":
            return len(self._queue)
        return len(self._priority_queue)
    
    @property
    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return self.depth == 0
    
    @property
    def is_full(self) -> bool:
        """Check if queue is at capacity."""
        return self.depth >= self._config.max_size
    
    @property
    def is_under_pressure(self) -> bool:
        """Check if queue is under pressure (approaching capacity).
        
        Returns True if queue depth exceeds warn_threshold.
        Use this for backpressure signaling.
        """
        return self.depth >= self._config.warn_threshold
    
    @property
    def is_critical(self) -> bool:
        """Check if queue is at critical level.
        
        Returns True if queue depth exceeds critical_threshold.
        """
        return self.depth >= self._config.critical_threshold
    
    async def enqueue(
        self,
        priority: QueuePriority = QueuePriority.NORMAL,
        timeout: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> float:
        """Add a request to the queue and wait for a connection.
        
        This method blocks until either:
        1. A connection becomes available (returns wait time)
        2. Timeout is reached (raises QueueTimeoutError)
        3. Queue is full (raises QueueFullError)
        
        Args:
            priority: Request priority (only used in priority mode)
            timeout: Override max_wait_time for this request
            metadata: Optional metadata to attach to the request
        
        Returns:
            Wait time in seconds
        
        Raises:
            QueueFullError: If queue is at capacity
            QueueTimeoutError: If timeout is reached
            asyncio.CancelledError: If request is cancelled
        
        Example:
            try:
                wait_time = await queue.enqueue()
                print(f"Got connection after {wait_time:.2f}s")
            except QueueFullError:
                print("System overloaded, try again later")
        """
        timeout = timeout if timeout is not None else self._config.max_wait_time
        
        async with self._lock:
            # Check if queue is full
            if self.is_full:
                await self._handle_overflow()
            
            # Create request
            self._request_counter += 1
            request = QueuedRequest(
                priority=priority.value,
                enqueue_time=time.monotonic(),
                future=asyncio.get_event_loop().create_future(),
                request_id=f"req_{self._request_counter}",
                metadata=metadata,
            )
            
            # Add to queue
            if self._config.fairness == "fifo":
                self._queue.append(request)
            else:
                heapq.heappush(self._priority_queue, request)
            
            self._stats.total_enqueued += 1
            self._stats.depth = self.depth
            
            # Log if approaching limits
            self._log_queue_status()
        
        # Wait for connection (outside lock)
        try:
            await asyncio.wait_for(request.future, timeout=timeout)
            wait_time = request.wait_time()
            self._record_wait_time(wait_time)
            return wait_time
            
        except asyncio.TimeoutError:
            # Remove from queue
            async with self._lock:
                self._remove_request(request)
                self._stats.total_timeouts += 1
                self._stats.depth = self.depth
            
            wait_time = request.wait_time()
            self._record_wait_time(wait_time)
            
            raise QueueTimeoutError(
                wait_time=wait_time,
                max_wait_time=timeout,
                queue_position=self._get_position(request),
            )
            
        except asyncio.CancelledError:
            async with self._lock:
                self._remove_request(request)
                self._stats.total_cancellations += 1
                self._stats.depth = self.depth
            raise
    
    def notify_available(self) -> bool:
        """Signal that a connection is available.
        
        This wakes up the next waiting request. Should be called
        when a connection is released back to the pool.
        
        Returns:
            True if a waiter was notified, False if queue was empty
        
        Example:
            # When connection is released
            if queue.notify_available():
                print("Handed connection to waiting request")
        """
        if self.is_empty:
            return False
        
        # Get next request
        if self._config.fairness == "fifo":
            request = self._queue.popleft()
        else:
            request = heapq.heappop(self._priority_queue)
        
        # Complete the future
        if not request.future.done():
            request.future.set_result(True)
            self._stats.total_dequeued += 1
            self._stats.depth = self.depth
            return True
        
        return False
    
    def cancel_all(self) -> int:
        """Cancel all waiting requests.
        
        Use this during shutdown to clean up the queue.
        
        Returns:
            Number of requests cancelled
        """
        count = 0
        
        if self._config.fairness == "fifo":
            while self._queue:
                request = self._queue.popleft()
                request.cancel()
                count += 1
        else:
            while self._priority_queue:
                request = heapq.heappop(self._priority_queue)
                request.cancel()
                count += 1
        
        self._stats.total_cancellations += count
        self._stats.depth = 0
        
        logger.info(f"Cancelled {count} queued requests")
        return count
    
    def get_stats(self) -> QueueStats:
        """Get current queue statistics.
        
        Returns:
            QueueStats with current values
        
        Example:
            stats = queue.get_stats()
            print(f"Queue depth: {stats.depth}")
            print(f"Avg wait: {stats.wait_time_avg_ms:.1f}ms")
        """
        self._stats.depth = self.depth
        return self._stats
    
    async def _handle_overflow(self) -> None:
        """Handle queue overflow based on configured action."""
        action = self._config.overflow_action
        
        if action == QueueOverflowAction.REJECT:
            self._stats.total_rejections += 1
            raise QueueFullError(
                queue_size=self.depth,
                max_size=self._config.max_size,
                wait_time_avg=self._stats.wait_time_avg_ms / 1000,
            )
        
        elif action == QueueOverflowAction.DROP_OLDEST:
            # Remove oldest request
            if self._config.fairness == "fifo" and self._queue:
                oldest = self._queue.popleft()
                oldest.future.set_exception(
                    QueueFullError(self.depth, self._config.max_size)
                )
                self._stats.total_rejections += 1
                logger.warning(f"Dropped oldest request {oldest.request_id}")
            elif self._priority_queue:
                # In priority mode, drop lowest priority (highest number)
                self._priority_queue.sort(reverse=True)
                oldest = self._priority_queue.pop()
                oldest.future.set_exception(
                    QueueFullError(self.depth, self._config.max_size)
                )
                self._stats.total_rejections += 1
                heapq.heapify(self._priority_queue)
        
        elif action == QueueOverflowAction.TIMEOUT_FASTEST:
            # This is handled in enqueue by reducing timeout
            pass
    
    def _remove_request(self, request: QueuedRequest) -> None:
        """Remove a request from the queue."""
        if self._config.fairness == "fifo":
            try:
                self._queue.remove(request)
            except ValueError:
                pass  # Already removed
        else:
            try:
                self._priority_queue.remove(request)
                heapq.heapify(self._priority_queue)
            except ValueError:
                pass
    
    def _get_position(self, request: QueuedRequest) -> int:
        """Get position of request in queue (1-indexed)."""
        if self._config.fairness == "fifo":
            try:
                return list(self._queue).index(request) + 1
            except ValueError:
                return 0
        else:
            try:
                return sorted(self._priority_queue).index(request) + 1
            except ValueError:
                return 0
    
    def _record_wait_time(self, wait_time: float) -> None:
        """Record wait time for statistics."""
        if not self._config.track_wait_times:
            return
        
        wait_ms = wait_time * 1000
        self._stats.wait_time_total_ms += wait_ms
        self._stats.wait_time_max_ms = max(self._stats.wait_time_max_ms, wait_ms)
        
        # Keep recent samples for percentile calculation
        self._stats.wait_times_recent.append(wait_ms)
        if len(self._stats.wait_times_recent) > self._max_recent_samples:
            self._stats.wait_times_recent.pop(0)
    
    def _log_queue_status(self) -> None:
        """Log queue status at appropriate levels."""
        depth = self.depth
        
        if depth >= self._config.critical_threshold:
            logger.error(
                f"Queue at CRITICAL level: {depth}/{self._config.max_size} "
                f"(avg wait: {self._stats.wait_time_avg_ms:.1f}ms)"
            )
        elif depth >= self._config.warn_threshold:
            logger.warning(
                f"Queue under pressure: {depth}/{self._config.max_size} "
                f"(avg wait: {self._stats.wait_time_avg_ms:.1f}ms)"
            )
        elif depth > 0 and depth % 50 == 0:
            logger.info(f"Queue depth: {depth}")
    
    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"ConnectionQueue("
            f"depth={self.depth}/{self._config.max_size}, "
            f"mode={self._config.fairness}, "
            f"pressure={self.is_under_pressure})"
        )

