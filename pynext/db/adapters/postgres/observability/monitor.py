"""
PyNext Pool Monitor Module.

Provides connection pool monitoring, leak detection, exhaustion warnings,
and dead connection cleanup.

Why Pool Monitoring?
───────────────────
Connection pools can fail in silent, subtle ways:
- Connections leak (held but never released)
- Connections die (network issues, database restart)
- Pool exhausts (too many concurrent requests)

This module helps you:
1. Detect issues BEFORE they cause outages
2. Automatically clean up dead connections
3. Alert on pool exhaustion before it happens
4. Track connection lifecycle for debugging

Monitoring Flow:
    Pool State → Check Thresholds → Alert/Clean → Log/Metrics

Usage Levels:

Level 1: Basic Monitoring (Zero Config)
    adapter = PostgresAdapter("postgresql://...", monitor=True)

Level 2: Custom Thresholds
    adapter = PostgresAdapter("postgresql://...", monitor=MonitorConfig(
        exhaustion_warning_threshold=0.8,  # Warn at 80%
    ))

Level 3: Full Monitoring
    adapter = PostgresAdapter("postgresql://...", monitor=MonitorConfig(
        exhaustion_warning_threshold=0.8,
        leak_detection_timeout=300,  # 5 min
        health_check_interval=30,
        dead_connection_timeout=60,
    ))

AI-Friendly Design:
- Clear warning messages
- Structured event data
- Easy callback integration
- Comprehensive statistics
"""

from __future__ import annotations

import asyncio
import threading
import time
import uuid
import weakref
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


# ============================================================================
# Configuration
# ============================================================================

@dataclass
class MonitorConfig:
    """Configuration for pool monitoring.
    
    Attributes:
        enabled: Whether monitoring is enabled
        exhaustion_warning_threshold: Pool utilization to trigger warning (0-1)
        exhaustion_critical_threshold: Pool utilization to trigger critical (0-1)
        leak_detection_timeout: Seconds before a held connection is a leak
        dead_connection_timeout: Seconds unresponsive before connection is dead
        health_check_interval: Seconds between health checks
        max_connection_age: Maximum seconds a connection can live
        track_call_stacks: Track where connections were acquired
        
    Example:
        # Default configuration
        config = MonitorConfig()
        
        # Custom thresholds
        config = MonitorConfig(
            exhaustion_warning_threshold=0.7,
            leak_detection_timeout=60,
        )
    """
    enabled: bool = True
    exhaustion_warning_threshold: float = 0.8
    exhaustion_critical_threshold: float = 0.95
    leak_detection_timeout: float = 300.0  # 5 minutes
    dead_connection_timeout: float = 60.0
    health_check_interval: float = 30.0
    max_connection_age: float = 3600.0  # 1 hour
    track_call_stacks: bool = False
    
    # Callbacks
    on_exhaustion_warning: Optional[Callable[["PoolEvent"], None]] = None
    on_exhaustion_critical: Optional[Callable[["PoolEvent"], None]] = None
    on_leak_detected: Optional[Callable[["LeakInfo"], None]] = None
    on_dead_connection: Optional[Callable[["ConnectionInfo"], None]] = None
    
    def __post_init__(self):
        """Validate configuration."""
        if not 0 <= self.exhaustion_warning_threshold <= 1:
            raise ValueError("exhaustion_warning_threshold must be 0-1")
        if not 0 <= self.exhaustion_critical_threshold <= 1:
            raise ValueError("exhaustion_critical_threshold must be 0-1")
        if self.exhaustion_warning_threshold >= self.exhaustion_critical_threshold:
            raise ValueError("warning threshold must be less than critical")
        if self.leak_detection_timeout <= 0:
            raise ValueError("leak_detection_timeout must be positive")


# ============================================================================
# Enums
# ============================================================================

class PoolEventType(str, Enum):
    """Types of pool events."""
    EXHAUSTION_WARNING = "exhaustion_warning"
    EXHAUSTION_CRITICAL = "exhaustion_critical"
    EXHAUSTION_CLEARED = "exhaustion_cleared"
    HEALTH_CHECK_STARTED = "health_check_started"
    HEALTH_CHECK_COMPLETED = "health_check_completed"
    LEAK_DETECTED = "leak_detected"
    DEAD_CONNECTION = "dead_connection"
    CONNECTION_RECOVERED = "connection_recovered"


class ConnectionState(str, Enum):
    """States a connection can be in."""
    IDLE = "idle"
    ACTIVE = "active"
    DEAD = "dead"
    LEAKED = "leaked"


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class ConnectionInfo:
    """Information about a connection.
    
    Tracks the state and lifecycle of a single connection.
    
    Attributes:
        connection_id: Unique identifier
        created_at: When connection was created
        acquired_at: When connection was last acquired
        released_at: When connection was last released
        state: Current state
        acquire_count: Times this connection was acquired
        query_count: Queries executed on this connection
        last_query_at: When last query was executed
        last_health_check: When last health check passed
        call_stack: Stack trace of acquire (if tracking enabled)
    """
    connection_id: str = field(default_factory=lambda: f"conn_{uuid.uuid4().hex[:8]}")
    created_at: float = field(default_factory=time.time)
    acquired_at: Optional[float] = None
    released_at: Optional[float] = None
    state: ConnectionState = ConnectionState.IDLE
    acquire_count: int = 0
    query_count: int = 0
    last_query_at: Optional[float] = None
    last_health_check: Optional[float] = None
    call_stack: Optional[str] = None
    
    @property
    def age_seconds(self) -> float:
        """Get connection age in seconds."""
        return time.time() - self.created_at
    
    @property
    def held_seconds(self) -> float:
        """Get time held since last acquire in seconds."""
        if self.acquired_at is None:
            return 0.0
        return time.time() - self.acquired_at
    
    @property
    def idle_seconds(self) -> float:
        """Get time idle since last release in seconds."""
        if self.released_at is None:
            return 0.0
        return time.time() - self.released_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "connection_id": self.connection_id,
            "created_at": self.created_at,
            "acquired_at": self.acquired_at,
            "released_at": self.released_at,
            "state": self.state.value,
            "acquire_count": self.acquire_count,
            "query_count": self.query_count,
            "age_seconds": self.age_seconds,
            "held_seconds": self.held_seconds,
            "idle_seconds": self.idle_seconds,
        }


@dataclass
class LeakInfo:
    """Information about a detected connection leak.
    
    A leak is when a connection is acquired but never released.
    
    Attributes:
        connection: The leaked connection info
        held_seconds: How long the connection has been held
        detected_at: When the leak was detected
        call_stack: Stack trace of acquire (if available)
    """
    connection: ConnectionInfo
    held_seconds: float = 0.0
    detected_at: float = field(default_factory=time.time)
    call_stack: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "connection_id": self.connection.connection_id,
            "held_seconds": self.held_seconds,
            "detected_at": self.detected_at,
            "call_stack": self.call_stack,
        }


@dataclass
class PoolEvent:
    """A pool monitoring event.
    
    Represents a significant event in the pool's lifecycle.
    
    Attributes:
        type: Type of event
        timestamp: When event occurred
        pool_name: Name of the pool
        pool_stats: Pool statistics at event time
        message: Human-readable message
        details: Additional details
    """
    type: PoolEventType
    timestamp: float = field(default_factory=time.time)
    pool_name: str = ""
    pool_stats: Dict[str, Any] = field(default_factory=dict)
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type.value,
            "timestamp": self.timestamp,
            "pool_name": self.pool_name,
            "pool_stats": self.pool_stats,
            "message": self.message,
            "details": self.details,
        }


@dataclass
class PoolStats:
    """Pool statistics snapshot.
    
    Attributes:
        active: Number of active (in-use) connections
        idle: Number of idle connections
        waiting: Number of requests waiting for connection
        total: Total connections (active + idle)
        max_size: Maximum pool size
        min_size: Minimum pool size
        utilization: Pool utilization (active / max_size)
    """
    active: int = 0
    idle: int = 0
    waiting: int = 0
    total: int = 0
    max_size: int = 10
    min_size: int = 0
    
    @property
    def utilization(self) -> float:
        """Get pool utilization (0-1)."""
        if self.max_size == 0:
            return 0.0
        return self.active / self.max_size
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "active": self.active,
            "idle": self.idle,
            "waiting": self.waiting,
            "total": self.total,
            "max_size": self.max_size,
            "min_size": self.min_size,
            "utilization": self.utilization,
        }


# ============================================================================
# Leak Detector
# ============================================================================

class LeakDetector:
    """Detects connection leaks.
    
    Tracks when connections are acquired and released, and
    reports connections that are held for too long.
    
    Example:
        detector = LeakDetector(timeout=300)  # 5 min timeout
        
        # Track connection
        detector.track_acquire("conn_123")
        
        # ... some time passes ...
        
        # Check for leaks
        leaks = detector.check_leaks()
        for leak in leaks:
            print(f"Leak: {leak.connection_id} held for {leak.held_seconds}s")
    """
    
    def __init__(
        self,
        timeout: float = 300.0,
        track_stacks: bool = False,
    ):
        """Initialize leak detector.
        
        Args:
            timeout: Seconds before connection is considered leaked
            track_stacks: Whether to track acquire call stacks
        """
        self._timeout = timeout
        self._track_stacks = track_stacks
        self._connections: Dict[str, ConnectionInfo] = {}
        self._lock = threading.Lock()
    
    def track_acquire(
        self,
        connection_id: str,
        call_stack: Optional[str] = None,
    ) -> ConnectionInfo:
        """Track a connection being acquired.
        
        Args:
            connection_id: Unique connection identifier
            call_stack: Optional stack trace
        
        Returns:
            Connection info object
        """
        with self._lock:
            if connection_id not in self._connections:
                self._connections[connection_id] = ConnectionInfo(
                    connection_id=connection_id,
                )
            
            info = self._connections[connection_id]
            info.acquired_at = time.time()
            info.state = ConnectionState.ACTIVE
            info.acquire_count += 1
            
            if self._track_stacks:
                import traceback
                info.call_stack = call_stack or "".join(traceback.format_stack())
            
            return info
    
    def track_release(self, connection_id: str) -> Optional[ConnectionInfo]:
        """Track a connection being released.
        
        Args:
            connection_id: Unique connection identifier
        
        Returns:
            Connection info object, or None if not found
        """
        with self._lock:
            info = self._connections.get(connection_id)
            if info:
                info.released_at = time.time()
                info.state = ConnectionState.IDLE
            return info
    
    def track_query(self, connection_id: str) -> None:
        """Track a query executed on a connection."""
        with self._lock:
            info = self._connections.get(connection_id)
            if info:
                info.query_count += 1
                info.last_query_at = time.time()
    
    def check_leaks(self) -> List[LeakInfo]:
        """Check for connection leaks.
        
        Returns:
            List of detected leaks
        """
        now = time.time()
        leaks = []
        
        with self._lock:
            for info in self._connections.values():
                if info.state == ConnectionState.ACTIVE:
                    held_seconds = now - (info.acquired_at or now)
                    if held_seconds > self._timeout:
                        info.state = ConnectionState.LEAKED
                        leaks.append(LeakInfo(
                            connection=info,
                            held_seconds=held_seconds,
                            call_stack=info.call_stack,
                        ))
        
        return leaks
    
    def remove_connection(self, connection_id: str) -> None:
        """Remove a connection from tracking."""
        with self._lock:
            self._connections.pop(connection_id, None)
    
    def get_active_connections(self) -> List[ConnectionInfo]:
        """Get all active (held) connections."""
        with self._lock:
            return [
                info for info in self._connections.values()
                if info.state == ConnectionState.ACTIVE
            ]
    
    def get_all_connections(self) -> List[ConnectionInfo]:
        """Get all tracked connections."""
        with self._lock:
            return list(self._connections.values())
    
    def reset(self) -> None:
        """Reset all tracking."""
        with self._lock:
            self._connections.clear()


# ============================================================================
# Health Checker
# ============================================================================

class HealthChecker:
    """Checks health of database connections.
    
    Periodically tests connections to ensure they're still alive.
    
    Example:
        checker = HealthChecker(timeout=60)
        
        # Check if connection is healthy
        is_healthy = await checker.check_connection(conn)
        
        # Mark connection as healthy
        checker.mark_healthy("conn_123")
    """
    
    def __init__(self, timeout: float = 60.0):
        """Initialize health checker.
        
        Args:
            timeout: Seconds before connection is considered dead
        """
        self._timeout = timeout
        self._last_check: Dict[str, float] = {}
        self._healthy: Set[str] = set()
        self._lock = threading.Lock()
    
    def mark_healthy(self, connection_id: str) -> None:
        """Mark a connection as healthy.
        
        Call this after a successful health check or query.
        """
        with self._lock:
            self._last_check[connection_id] = time.time()
            self._healthy.add(connection_id)
    
    def mark_unhealthy(self, connection_id: str) -> None:
        """Mark a connection as unhealthy."""
        with self._lock:
            self._healthy.discard(connection_id)
    
    def is_healthy(self, connection_id: str) -> bool:
        """Check if connection is considered healthy.
        
        A connection is healthy if it passed a health check recently.
        """
        with self._lock:
            if connection_id not in self._healthy:
                return False
            
            last_check = self._last_check.get(connection_id, 0)
            return (time.time() - last_check) < self._timeout
    
    def needs_check(self, connection_id: str, interval: float) -> bool:
        """Check if connection needs a health check.
        
        Args:
            connection_id: Connection to check
            interval: Check interval in seconds
        """
        with self._lock:
            last_check = self._last_check.get(connection_id, 0)
            return (time.time() - last_check) >= interval
    
    def get_dead_connections(self) -> List[str]:
        """Get connections that haven't passed health check recently."""
        now = time.time()
        dead = []
        
        with self._lock:
            for conn_id, last_check in self._last_check.items():
                if (now - last_check) > self._timeout:
                    dead.append(conn_id)
        
        return dead
    
    def remove_connection(self, connection_id: str) -> None:
        """Remove a connection from tracking."""
        with self._lock:
            self._last_check.pop(connection_id, None)
            self._healthy.discard(connection_id)
    
    def reset(self) -> None:
        """Reset all health tracking."""
        with self._lock:
            self._last_check.clear()
            self._healthy.clear()


# ============================================================================
# Pool Monitor
# ============================================================================

class PoolMonitor:
    """Monitor for connection pool health.
    
    Combines leak detection, health checking, and exhaustion
    monitoring into a single comprehensive monitor.
    
    Example:
        config = MonitorConfig(
            exhaustion_warning_threshold=0.8,
            leak_detection_timeout=300,
        )
        monitor = PoolMonitor(config)
        
        # Update with pool stats
        monitor.update_stats(PoolStats(active=8, idle=2, max_size=10))
        
        # Check for issues
        events = monitor.check_pool()
    """
    
    def __init__(
        self,
        config: Optional[MonitorConfig] = None,
        pool_name: str = "default",
    ):
        """Initialize pool monitor.
        
        Args:
            config: Monitor configuration
            pool_name: Name of the pool being monitored
        """
        self.config = config or MonitorConfig()
        self.pool_name = pool_name
        
        # Sub-monitors
        self._leak_detector = LeakDetector(
            timeout=self.config.leak_detection_timeout,
            track_stacks=self.config.track_call_stacks,
        )
        self._health_checker = HealthChecker(
            timeout=self.config.dead_connection_timeout,
        )
        
        # State
        self._current_stats = PoolStats()
        self._events: List[PoolEvent] = []
        self._max_events = 1000
        self._in_exhaustion_warning = False
        self._in_exhaustion_critical = False
        self._lock = threading.Lock()
    
    @property
    def enabled(self) -> bool:
        """Whether monitoring is enabled."""
        return self.config.enabled
    
    def update_stats(self, stats: PoolStats) -> None:
        """Update pool statistics.
        
        Call this periodically with current pool state.
        
        Args:
            stats: Current pool statistics
        """
        with self._lock:
            self._current_stats = stats
    
    def track_acquire(
        self,
        connection_id: str,
        call_stack: Optional[str] = None,
    ) -> None:
        """Track connection acquisition."""
        if not self.config.enabled:
            return
        self._leak_detector.track_acquire(connection_id, call_stack)
    
    def track_release(self, connection_id: str) -> None:
        """Track connection release."""
        if not self.config.enabled:
            return
        self._leak_detector.track_release(connection_id)
    
    def track_query(self, connection_id: str) -> None:
        """Track query execution (also marks as healthy)."""
        if not self.config.enabled:
            return
        self._leak_detector.track_query(connection_id)
        self._health_checker.mark_healthy(connection_id)
    
    def track_connection_closed(self, connection_id: str) -> None:
        """Track connection being closed."""
        if not self.config.enabled:
            return
        self._leak_detector.remove_connection(connection_id)
        self._health_checker.remove_connection(connection_id)
    
    def check_pool(self) -> List[PoolEvent]:
        """Check pool for issues.
        
        Call this periodically to check for:
        - Exhaustion warnings/critical
        - Connection leaks
        - Dead connections
        
        Returns:
            List of events detected
        """
        if not self.config.enabled:
            return []
        
        events = []
        
        # Check exhaustion
        events.extend(self._check_exhaustion())
        
        # Check leaks
        events.extend(self._check_leaks())
        
        # Check dead connections
        events.extend(self._check_dead_connections())
        
        # Store events
        self._store_events(events)
        
        return events
    
    def _check_exhaustion(self) -> List[PoolEvent]:
        """Check for pool exhaustion."""
        events = []
        utilization = self._current_stats.utilization
        
        # Critical
        if utilization >= self.config.exhaustion_critical_threshold:
            if not self._in_exhaustion_critical:
                self._in_exhaustion_critical = True
                event = PoolEvent(
                    type=PoolEventType.EXHAUSTION_CRITICAL,
                    pool_name=self.pool_name,
                    pool_stats=self._current_stats.to_dict(),
                    message=f"Pool is at {utilization:.1%} capacity (CRITICAL)",
                    details={"waiting": self._current_stats.waiting},
                )
                events.append(event)
                if self.config.on_exhaustion_critical:
                    self.config.on_exhaustion_critical(event)
        
        # Warning
        elif utilization >= self.config.exhaustion_warning_threshold:
            if not self._in_exhaustion_warning:
                self._in_exhaustion_warning = True
                event = PoolEvent(
                    type=PoolEventType.EXHAUSTION_WARNING,
                    pool_name=self.pool_name,
                    pool_stats=self._current_stats.to_dict(),
                    message=f"Pool is at {utilization:.1%} capacity",
                    details={"waiting": self._current_stats.waiting},
                )
                events.append(event)
                if self.config.on_exhaustion_warning:
                    self.config.on_exhaustion_warning(event)
        
        # Cleared
        else:
            if self._in_exhaustion_warning or self._in_exhaustion_critical:
                self._in_exhaustion_warning = False
                self._in_exhaustion_critical = False
                events.append(PoolEvent(
                    type=PoolEventType.EXHAUSTION_CLEARED,
                    pool_name=self.pool_name,
                    pool_stats=self._current_stats.to_dict(),
                    message=f"Pool utilization returned to normal ({utilization:.1%})",
                ))
        
        return events
    
    def _check_leaks(self) -> List[PoolEvent]:
        """Check for connection leaks."""
        events = []
        
        leaks = self._leak_detector.check_leaks()
        for leak in leaks:
            event = PoolEvent(
                type=PoolEventType.LEAK_DETECTED,
                pool_name=self.pool_name,
                pool_stats=self._current_stats.to_dict(),
                message=f"Connection leak detected: {leak.connection.connection_id}",
                details=leak.to_dict(),
            )
            events.append(event)
            
            if self.config.on_leak_detected:
                self.config.on_leak_detected(leak)
        
        return events
    
    def _check_dead_connections(self) -> List[PoolEvent]:
        """Check for dead connections."""
        events = []
        
        dead = self._health_checker.get_dead_connections()
        for conn_id in dead:
            # Get connection info
            connections = self._leak_detector.get_all_connections()
            info = next((c for c in connections if c.connection_id == conn_id), None)
            
            if info:
                info.state = ConnectionState.DEAD
                event = PoolEvent(
                    type=PoolEventType.DEAD_CONNECTION,
                    pool_name=self.pool_name,
                    pool_stats=self._current_stats.to_dict(),
                    message=f"Dead connection detected: {conn_id}",
                    details=info.to_dict(),
                )
                events.append(event)
                
                if self.config.on_dead_connection:
                    self.config.on_dead_connection(info)
        
        return events
    
    def _store_events(self, events: List[PoolEvent]) -> None:
        """Store events in history."""
        with self._lock:
            self._events.extend(events)
            if len(self._events) > self._max_events:
                self._events = self._events[-self._max_events:]
    
    def get_events(
        self,
        limit: int = 100,
        event_type: Optional[PoolEventType] = None,
    ) -> List[PoolEvent]:
        """Get event history.
        
        Args:
            limit: Maximum events to return
            event_type: Filter by event type
        
        Returns:
            List of events
        """
        with self._lock:
            events = self._events
            if event_type:
                events = [e for e in events if e.type == event_type]
            return events[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics.
        
        Returns:
            Dictionary with stats
        """
        leaks = self._leak_detector.check_leaks()
        dead = self._health_checker.get_dead_connections()
        active = self._leak_detector.get_active_connections()
        
        return {
            "pool_name": self.pool_name,
            "current_stats": self._current_stats.to_dict(),
            "active_connections": len(active),
            "leaked_connections": len(leaks),
            "dead_connections": len(dead),
            "in_exhaustion_warning": self._in_exhaustion_warning,
            "in_exhaustion_critical": self._in_exhaustion_critical,
            "total_events": len(self._events),
        }
    
    def get_active_connections(self) -> List[ConnectionInfo]:
        """Get all active (held) connections."""
        return self._leak_detector.get_active_connections()
    
    def reset(self) -> None:
        """Reset all monitoring state."""
        with self._lock:
            self._leak_detector.reset()
            self._health_checker.reset()
            self._events.clear()
            self._in_exhaustion_warning = False
            self._in_exhaustion_critical = False


# ============================================================================
# Convenience Functions
# ============================================================================

def create_monitor(
    exhaustion_warning_threshold: float = 0.8,
    leak_detection_timeout: float = 300.0,
    pool_name: str = "default",
    **kwargs: Any,
) -> PoolMonitor:
    """Create a pool monitor with common options.
    
    Args:
        exhaustion_warning_threshold: Utilization for warning (0-1)
        leak_detection_timeout: Seconds before leak detection
        pool_name: Name of the pool
        **kwargs: Additional MonitorConfig options
    
    Returns:
        Configured PoolMonitor instance
    """
    config = MonitorConfig(
        exhaustion_warning_threshold=exhaustion_warning_threshold,
        leak_detection_timeout=leak_detection_timeout,
        **kwargs,
    )
    return PoolMonitor(config, pool_name)


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # Configuration
    "MonitorConfig",
    "PoolEventType",
    "ConnectionState",
    
    # Data classes
    "ConnectionInfo",
    "LeakInfo",
    "PoolEvent",
    "PoolStats",
    
    # Components
    "LeakDetector",
    "HealthChecker",
    "PoolMonitor",
    
    # Convenience
    "create_monitor",
]

