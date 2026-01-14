"""
PostgreSQL Connection Lifecycle Management.

This module provides intelligent lifecycle management for database connections,
including soft/hard lifetime limits, use-count retirement, and graceful replacement.
It follows SolidJS principles:
- Fine-grained: Only manages connections that need attention
- Predictable: Clear rules for when connections are retired
- No surprises: Graceful replacement doesn't drop active queries

How Connection Lifecycle Works:

1. Each connection has a creation time and use count
2. Soft lifetime: Prefer to close, but don't interrupt
3. Hard lifetime: Must close, even if busy (with grace period)
4. Use count: Close after N uses (prevents connection staleness)
5. Health checks: Validate connections before use

Why This Matters:
- Prevents stale connections (PostgreSQL has connection-specific state)
- Balances connection freshness with performance
- Graceful replacement: no dropped queries
- Observable: Know why connections are being replaced

AI-Friendly Design:
- Clear state machine (fresh, retiring, retired)
- Explicit configuration with sensible defaults
- Comprehensive logging for debugging
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    import asyncpg

logger = logging.getLogger("pynext.db.postgres.lifecycle")


class ConnectionHealth(Enum):
    """Health status of a connection.
    
    HEALTHY: Connection is working normally
    UNKNOWN: Health hasn't been checked recently
    DEGRADED: Connection is slow but working
    UNHEALTHY: Connection is not responding
    CLOSED: Connection has been closed
    """
    HEALTHY = "healthy"
    UNKNOWN = "unknown"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CLOSED = "closed"


class RetirementReason(Enum):
    """Why a connection is being retired.
    
    Used for logging and metrics to understand connection turnover.
    """
    SOFT_LIFETIME = "soft_lifetime"      # Exceeded soft lifetime, closed opportunistically
    HARD_LIFETIME = "hard_lifetime"      # Exceeded hard lifetime, forced close
    MAX_USES = "max_uses"                # Exceeded max use count
    HEALTH_CHECK_FAILED = "health_check_failed"  # Failed health check
    IDLE_TIMEOUT = "idle_timeout"        # Idle too long
    ERROR = "error"                      # Connection error occurred
    MANUAL = "manual"                    # Manually retired
    POOL_SHUTDOWN = "pool_shutdown"      # Pool is shutting down


class ReplacementStrategy(Enum):
    """Strategy for replacing connections.
    
    IMMEDIATE: Close connection immediately (may drop queries)
    GRACEFUL: Wait for connection to be released before closing
    LAZY: Mark for replacement, close on next release
    """
    IMMEDIATE = "immediate"
    GRACEFUL = "graceful"
    LAZY = "lazy"


@dataclass
class LifecycleConfig:
    """Configuration for connection lifecycle management.
    
    Attributes:
        max_lifetime: Hard limit - force close after this many seconds (default: 3600)
        soft_lifetime: Soft limit - prefer to close after this (default: 1800)
        max_uses: Close after this many uses (default: 10000, 0 = unlimited)
        health_check_interval: Seconds between health checks (default: 30)
        health_check_timeout: Timeout for health check query (default: 5.0)
        health_check_query: Query to validate connection (default: "SELECT 1")
        replacement_strategy: How to replace connections (default: GRACEFUL)
        grace_period: Seconds to wait before force-closing (default: 30.0)
        track_metrics: Whether to track lifecycle metrics (default: True)
    
    Example:
        config = LifecycleConfig(
            max_lifetime=3600,      # 1 hour hard limit
            soft_lifetime=1800,     # 30 min soft limit
            max_uses=5000,          # Refresh after 5000 queries
            replacement_strategy=ReplacementStrategy.GRACEFUL,
        )
    """
    max_lifetime: float = 3600.0
    soft_lifetime: float = 1800.0
    max_uses: int = 10000
    health_check_interval: float = 30.0
    health_check_timeout: float = 5.0
    health_check_query: str = "SELECT 1"
    replacement_strategy: ReplacementStrategy = ReplacementStrategy.GRACEFUL
    grace_period: float = 30.0
    track_metrics: bool = True
    
    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.max_lifetime < 0:
            raise ValueError(f"max_lifetime must be >= 0, got {self.max_lifetime}")
        if self.soft_lifetime < 0:
            raise ValueError(f"soft_lifetime must be >= 0, got {self.soft_lifetime}")
        if self.soft_lifetime > self.max_lifetime and self.max_lifetime > 0:
            raise ValueError(
                f"soft_lifetime ({self.soft_lifetime}) cannot exceed "
                f"max_lifetime ({self.max_lifetime})"
            )
        if self.max_uses < 0:
            raise ValueError(f"max_uses must be >= 0, got {self.max_uses}")
        if self.health_check_interval < 0:
            raise ValueError(
                f"health_check_interval must be >= 0, got {self.health_check_interval}"
            )
        if self.grace_period < 0:
            raise ValueError(f"grace_period must be >= 0, got {self.grace_period}")


@dataclass
class ConnectionLifecycle:
    """Lifecycle state for a single connection.
    
    Tracks creation time, usage, health status, and retirement state
    for a database connection.
    
    Attributes:
        connection_id: Unique identifier for this connection
        created_at: Monotonic time when connection was created
        last_used: Monotonic time when connection was last used
        last_health_check: Monotonic time of last health check
        use_count: Number of times this connection has been used
        health: Current health status
        marked_for_retirement: Whether connection should be retired
        retirement_reason: Why connection is being retired
        retirement_requested_at: When retirement was requested
    """
    connection_id: str
    created_at: float = field(default_factory=time.monotonic)
    last_used: float = field(default_factory=time.monotonic)
    last_health_check: float = 0.0
    use_count: int = 0
    health: ConnectionHealth = ConnectionHealth.UNKNOWN
    marked_for_retirement: bool = False
    retirement_reason: Optional[RetirementReason] = None
    retirement_requested_at: Optional[float] = None
    
    def age(self) -> float:
        """Get age of connection in seconds."""
        return time.monotonic() - self.created_at
    
    def idle_time(self) -> float:
        """Get time since last use in seconds."""
        return time.monotonic() - self.last_used
    
    def time_since_health_check(self) -> float:
        """Get time since last health check in seconds."""
        if self.last_health_check == 0:
            return float("inf")
        return time.monotonic() - self.last_health_check
    
    def mark_used(self) -> None:
        """Mark connection as having been used."""
        self.use_count += 1
        self.last_used = time.monotonic()
    
    def mark_healthy(self) -> None:
        """Mark connection as healthy after successful health check."""
        self.health = ConnectionHealth.HEALTHY
        self.last_health_check = time.monotonic()
    
    def mark_unhealthy(self) -> None:
        """Mark connection as unhealthy after failed health check."""
        self.health = ConnectionHealth.UNHEALTHY
        self.last_health_check = time.monotonic()
    
    def request_retirement(self, reason: RetirementReason) -> None:
        """Request that this connection be retired."""
        if not self.marked_for_retirement:
            self.marked_for_retirement = True
            self.retirement_reason = reason
            self.retirement_requested_at = time.monotonic()
            logger.debug(
                f"Connection {self.connection_id} marked for retirement: {reason.value}"
            )
    
    def should_retire(self, config: LifecycleConfig) -> Optional[RetirementReason]:
        """Check if connection should be retired.
        
        Returns the reason for retirement, or None if connection is still valid.
        """
        if self.marked_for_retirement:
            return self.retirement_reason
        
        # Check hard lifetime
        if config.max_lifetime > 0 and self.age() > config.max_lifetime:
            return RetirementReason.HARD_LIFETIME
        
        # Check max uses
        if config.max_uses > 0 and self.use_count >= config.max_uses:
            return RetirementReason.MAX_USES
        
        # Check health
        if self.health == ConnectionHealth.UNHEALTHY:
            return RetirementReason.HEALTH_CHECK_FAILED
        
        return None
    
    def should_prefer_retirement(self, config: LifecycleConfig) -> Optional[RetirementReason]:
        """Check if connection should preferably be retired (soft limit).
        
        Returns the reason if retirement is preferred, or None.
        """
        # First check hard limits
        hard_reason = self.should_retire(config)
        if hard_reason:
            return hard_reason
        
        # Check soft lifetime
        if config.soft_lifetime > 0 and self.age() > config.soft_lifetime:
            return RetirementReason.SOFT_LIFETIME
        
        return None
    
    def needs_health_check(self, config: LifecycleConfig) -> bool:
        """Check if connection needs a health check."""
        if config.health_check_interval <= 0:
            return False
        return self.time_since_health_check() > config.health_check_interval
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/metrics."""
        return {
            "connection_id": self.connection_id,
            "age_seconds": self.age(),
            "idle_seconds": self.idle_time(),
            "use_count": self.use_count,
            "health": self.health.value,
            "marked_for_retirement": self.marked_for_retirement,
            "retirement_reason": self.retirement_reason.value if self.retirement_reason else None,
        }


@dataclass
class LifecycleStats:
    """Statistics about connection lifecycle.
    
    Attributes:
        total_connections_created: Total connections created over pool lifetime
        total_connections_retired: Total connections retired
        retirements_by_reason: Count of retirements by reason
        health_checks_performed: Total health checks run
        health_checks_failed: Total health checks that failed
        avg_connection_lifetime_ms: Average connection lifetime in milliseconds
        avg_connection_uses: Average uses per connection
    """
    total_connections_created: int = 0
    total_connections_retired: int = 0
    retirements_by_reason: Dict[str, int] = field(default_factory=dict)
    health_checks_performed: int = 0
    health_checks_failed: int = 0
    connection_lifetimes_ms: List[float] = field(default_factory=list)
    connection_use_counts: List[int] = field(default_factory=list)
    
    @property
    def avg_connection_lifetime_ms(self) -> float:
        """Average connection lifetime in milliseconds."""
        if not self.connection_lifetimes_ms:
            return 0
        return sum(self.connection_lifetimes_ms) / len(self.connection_lifetimes_ms)
    
    @property
    def avg_connection_uses(self) -> float:
        """Average uses per connection."""
        if not self.connection_use_counts:
            return 0
        return sum(self.connection_use_counts) / len(self.connection_use_counts)
    
    def record_retirement(self, lifecycle: ConnectionLifecycle) -> None:
        """Record a connection retirement."""
        self.total_connections_retired += 1
        
        if lifecycle.retirement_reason:
            reason = lifecycle.retirement_reason.value
            self.retirements_by_reason[reason] = (
                self.retirements_by_reason.get(reason, 0) + 1
            )
        
        # Track lifetime and uses (keep last 1000)
        self.connection_lifetimes_ms.append(lifecycle.age() * 1000)
        self.connection_use_counts.append(lifecycle.use_count)
        
        if len(self.connection_lifetimes_ms) > 1000:
            self.connection_lifetimes_ms.pop(0)
        if len(self.connection_use_counts) > 1000:
            self.connection_use_counts.pop(0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/metrics."""
        return {
            "total_created": self.total_connections_created,
            "total_retired": self.total_connections_retired,
            "retirements_by_reason": self.retirements_by_reason,
            "health_checks_performed": self.health_checks_performed,
            "health_checks_failed": self.health_checks_failed,
            "avg_lifetime_ms": self.avg_connection_lifetime_ms,
            "avg_uses": self.avg_connection_uses,
        }


class LifecycleManager:
    """Manages connection lifecycle for a pool.
    
    This class handles:
    1. Tracking lifecycle state for all connections
    2. Health checking connections
    3. Determining which connections should be retired
    4. Coordinating graceful retirement
    
    Basic Usage:
        manager = LifecycleManager(LifecycleConfig())
        
        # Register a new connection
        lifecycle = manager.register_connection("conn_1")
        
        # Mark connection as used
        manager.mark_used("conn_1")
        
        # Check if connection should be retired
        if manager.should_retire("conn_1"):
            await manager.retire_connection("conn_1")
    
    With Health Checks:
        # Run health check on all connections
        unhealthy = await manager.check_all_health(connections)
        
        # Retire unhealthy connections
        for conn_id in unhealthy:
            await manager.retire_connection(conn_id)
    """
    
    def __init__(self, config: Optional[LifecycleConfig] = None):
        """Initialize the lifecycle manager.
        
        Args:
            config: Lifecycle configuration (default: LifecycleConfig())
        """
        self._config = config or LifecycleConfig()
        self._lifecycles: Dict[str, ConnectionLifecycle] = {}
        self._stats = LifecycleStats()
        self._lock = asyncio.Lock()
        self._connection_counter = 0
    
    @property
    def config(self) -> LifecycleConfig:
        """Get lifecycle configuration."""
        return self._config
    
    def register_connection(self, connection_id: Optional[str] = None) -> ConnectionLifecycle:
        """Register a new connection with the manager.
        
        Args:
            connection_id: Optional ID for the connection (auto-generated if not provided)
        
        Returns:
            ConnectionLifecycle for the new connection
        
        Example:
            lifecycle = manager.register_connection()
            print(f"Registered connection {lifecycle.connection_id}")
        """
        if connection_id is None:
            self._connection_counter += 1
            connection_id = f"conn_{self._connection_counter}"
        
        lifecycle = ConnectionLifecycle(connection_id=connection_id)
        self._lifecycles[connection_id] = lifecycle
        self._stats.total_connections_created += 1
        
        logger.debug(f"Registered connection {connection_id}")
        return lifecycle
    
    def unregister_connection(self, connection_id: str) -> Optional[ConnectionLifecycle]:
        """Unregister a connection from the manager.
        
        Args:
            connection_id: ID of the connection to unregister
        
        Returns:
            The ConnectionLifecycle that was removed, or None if not found
        """
        lifecycle = self._lifecycles.pop(connection_id, None)
        if lifecycle:
            self._stats.record_retirement(lifecycle)
            logger.debug(
                f"Unregistered connection {connection_id} "
                f"(age: {lifecycle.age():.1f}s, uses: {lifecycle.use_count})"
            )
        return lifecycle
    
    def get_lifecycle(self, connection_id: str) -> Optional[ConnectionLifecycle]:
        """Get lifecycle state for a connection.
        
        Args:
            connection_id: ID of the connection
        
        Returns:
            ConnectionLifecycle or None if not found
        """
        return self._lifecycles.get(connection_id)
    
    def mark_used(self, connection_id: str) -> None:
        """Mark a connection as having been used.
        
        Args:
            connection_id: ID of the connection
        """
        lifecycle = self._lifecycles.get(connection_id)
        if lifecycle:
            lifecycle.mark_used()
    
    def should_retire(self, connection_id: str) -> Optional[RetirementReason]:
        """Check if a connection should be retired.
        
        Args:
            connection_id: ID of the connection
        
        Returns:
            RetirementReason if connection should be retired, None otherwise
        """
        lifecycle = self._lifecycles.get(connection_id)
        if not lifecycle:
            return None
        return lifecycle.should_retire(self._config)
    
    def should_prefer_retirement(self, connection_id: str) -> Optional[RetirementReason]:
        """Check if a connection should preferably be retired (soft limit).
        
        Args:
            connection_id: ID of the connection
        
        Returns:
            RetirementReason if retirement is preferred, None otherwise
        """
        lifecycle = self._lifecycles.get(connection_id)
        if not lifecycle:
            return None
        return lifecycle.should_prefer_retirement(self._config)
    
    def request_retirement(
        self,
        connection_id: str,
        reason: RetirementReason = RetirementReason.MANUAL,
    ) -> bool:
        """Request that a connection be retired.
        
        The connection will be retired on its next release (graceful) or
        immediately (if configured).
        
        Args:
            connection_id: ID of the connection
            reason: Why the connection is being retired
        
        Returns:
            True if the connection was marked for retirement, False if not found
        """
        lifecycle = self._lifecycles.get(connection_id)
        if not lifecycle:
            return False
        lifecycle.request_retirement(reason)
        return True
    
    def get_connections_to_retire(self) -> List[str]:
        """Get list of connections that should be retired.
        
        Returns:
            List of connection IDs that should be retired
        """
        to_retire = []
        for conn_id, lifecycle in self._lifecycles.items():
            if lifecycle.should_retire(self._config):
                to_retire.append(conn_id)
        return to_retire
    
    def get_connections_preferring_retirement(self) -> List[str]:
        """Get list of connections that prefer retirement (soft limit).
        
        Returns:
            List of connection IDs that prefer retirement
        """
        prefer_retire = []
        for conn_id, lifecycle in self._lifecycles.items():
            if lifecycle.should_prefer_retirement(self._config):
                prefer_retire.append(conn_id)
        return prefer_retire
    
    def get_connections_needing_health_check(self) -> List[str]:
        """Get list of connections that need a health check.
        
        Returns:
            List of connection IDs that need health checks
        """
        need_check = []
        for conn_id, lifecycle in self._lifecycles.items():
            if lifecycle.needs_health_check(self._config):
                need_check.append(conn_id)
        return need_check
    
    async def check_health(
        self,
        connection_id: str,
        connection: "asyncpg.Connection",
    ) -> ConnectionHealth:
        """Run a health check on a connection.
        
        Args:
            connection_id: ID of the connection
            connection: The actual asyncpg connection
        
        Returns:
            Health status after the check
        """
        lifecycle = self._lifecycles.get(connection_id)
        if not lifecycle:
            return ConnectionHealth.UNKNOWN
        
        self._stats.health_checks_performed += 1
        
        try:
            start = time.monotonic()
            await asyncio.wait_for(
                connection.fetchval(self._config.health_check_query),
                timeout=self._config.health_check_timeout,
            )
            duration = time.monotonic() - start
            
            # Check if response was slow
            if duration > self._config.health_check_timeout / 2:
                lifecycle.health = ConnectionHealth.DEGRADED
                logger.warning(
                    f"Connection {connection_id} health check slow: {duration:.2f}s"
                )
            else:
                lifecycle.mark_healthy()
            
            return lifecycle.health
            
        except asyncio.TimeoutError:
            lifecycle.mark_unhealthy()
            lifecycle.request_retirement(RetirementReason.HEALTH_CHECK_FAILED)
            self._stats.health_checks_failed += 1
            logger.warning(f"Connection {connection_id} health check timed out")
            return ConnectionHealth.UNHEALTHY
            
        except Exception as e:
            lifecycle.mark_unhealthy()
            lifecycle.request_retirement(RetirementReason.HEALTH_CHECK_FAILED)
            self._stats.health_checks_failed += 1
            logger.warning(f"Connection {connection_id} health check failed: {e}")
            return ConnectionHealth.UNHEALTHY
    
    async def check_all_health(
        self,
        connections: Dict[str, "asyncpg.Connection"],
    ) -> List[str]:
        """Run health checks on all connections that need it.
        
        Args:
            connections: Mapping of connection ID to asyncpg connection
        
        Returns:
            List of connection IDs that failed health checks
        """
        need_check = self.get_connections_needing_health_check()
        unhealthy = []
        
        for conn_id in need_check:
            if conn_id in connections:
                health = await self.check_health(conn_id, connections[conn_id])
                if health == ConnectionHealth.UNHEALTHY:
                    unhealthy.append(conn_id)
        
        if unhealthy:
            logger.warning(f"Health checks failed for {len(unhealthy)} connections")
        
        return unhealthy
    
    def select_for_retirement(
        self,
        exclude_busy: Set[str],
        count: int = 1,
    ) -> List[str]:
        """Select connections for retirement, avoiding busy ones.
        
        This is used when the pool needs to shrink or refresh connections.
        Prefers connections that:
        1. Are already marked for retirement
        2. Have exceeded soft lifetime
        3. Have high use counts
        
        Args:
            exclude_busy: Set of connection IDs that are currently busy
            count: Number of connections to select
        
        Returns:
            List of connection IDs to retire
        """
        candidates = []
        
        for conn_id, lifecycle in self._lifecycles.items():
            if conn_id in exclude_busy:
                continue
            
            # Score based on retirement preference
            score = 0
            
            # Already marked for retirement
            if lifecycle.marked_for_retirement:
                score += 1000
            
            # Hard limit exceeded
            if lifecycle.should_retire(self._config):
                score += 500
            
            # Soft limit exceeded
            if lifecycle.should_prefer_retirement(self._config):
                score += 200
            
            # Age-based scoring
            score += lifecycle.age() / 60  # 1 point per minute of age
            
            # Use count scoring
            score += lifecycle.use_count / 100  # 1 point per 100 uses
            
            candidates.append((score, conn_id))
        
        # Sort by score (highest first)
        candidates.sort(reverse=True)
        
        return [conn_id for _, conn_id in candidates[:count]]
    
    def get_stats(self) -> LifecycleStats:
        """Get lifecycle statistics.
        
        Returns:
            LifecycleStats with current values
        """
        return self._stats
    
    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"LifecycleManager("
            f"connections={len(self._lifecycles)}, "
            f"retired={self._stats.total_connections_retired})"
        )

