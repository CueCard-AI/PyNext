"""
PostgreSQL Auto-Scaling Connection Pool.

This module provides a connection pool that automatically grows and shrinks
based on demand. It follows SolidJS principles:
- Fine-grained: Only creates connections when needed
- Minimal overhead: No background threads, event-driven
- No global state: Each pool is independent

How Auto-Scaling Works:

1. Pool starts with `min_size` connections
2. When all connections are busy and a request comes in:
   - If pool size < max_size: Create new connection immediately
   - If pool size = max_size: Queue the request (with timeout)
3. When connections are idle for `idle_timeout`:
   - Close them, but never go below min_size
4. Connections older than `max_lifetime` are closed and replaced

Phase 5.2 Features:
- Connection Queue: Fair FIFO queuing with backpressure
- Lifecycle Management: Soft/hard limits, graceful replacement
- Connection Warmup: Pre-warm connections for instant use
- External Pooler Support: PgBouncer, pgpool compatibility

Why This Matters:
- Small apps: Use minimal resources (1-2 connections)
- Traffic spikes: Instantly scale up to handle load
- After spike: Scale back down, free memory
- No wasted connections sitting idle
- Production-ready: Handles PgBouncer, health checks, warmup

AI-Friendly Design:
- Clear state machine (idle, busy, closed)
- Comprehensive logging for debugging
- All configuration is explicit
"""

from __future__ import annotations

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Set, TYPE_CHECKING

from .postgres_url import PostgresConfig
from .postgres_queue import (
    ConnectionQueue,
    QueueConfig,
    QueueFullError,
    QueueTimeoutError,
    QueueStats,
)
from .postgres_lifecycle import (
    LifecycleManager,
    LifecycleConfig,
    ConnectionLifecycle,
    LifecycleStats,
    RetirementReason,
    ConnectionHealth,
)
from .postgres_warmup import (
    ConnectionWarmer,
    WarmupConfig,
    WarmupResult,
    WarmupStats,
)
from .postgres_external import (
    ExternalPoolerManager,
    ExternalPoolerConfig,
    PoolerType,
    PoolerMode,
    PoolerInfo,
)

if TYPE_CHECKING:
    import asyncpg

logger = logging.getLogger("pynext.db.postgres")


class PoolState(Enum):
    """State of the connection pool."""
    UNINITIALIZED = "uninitialized"  # Pool created but not started
    RUNNING = "running"              # Pool is active and accepting requests
    CLOSING = "closing"              # Pool is shutting down
    CLOSED = "closed"                # Pool is fully closed


class ConnectionState(Enum):
    """State of a pooled connection."""
    IDLE = "idle"          # Available for use
    BUSY = "busy"          # Currently in use
    CLOSING = "closing"    # Being closed
    CLOSED = "closed"      # Fully closed


@dataclass
class PooledConnection:
    """A connection managed by the pool.
    
    Tracks connection state and statistics.
    
    Attributes:
        connection: The asyncpg connection
        connection_id: Unique identifier for this connection
        state: Current state (idle, busy, closed)
        created_at: When the connection was created
        last_used: When the connection was last used
        use_count: Number of times this connection was used
    """
    connection: "asyncpg.Connection"
    connection_id: str = ""
    state: ConnectionState = ConnectionState.IDLE
    created_at: float = field(default_factory=time.monotonic)
    last_used: float = field(default_factory=time.monotonic)
    use_count: int = 0
    
    def mark_busy(self) -> None:
        """Mark connection as in use."""
        self.state = ConnectionState.BUSY
        self.use_count += 1
        self.last_used = time.monotonic()
    
    def mark_idle(self) -> None:
        """Mark connection as available."""
        self.state = ConnectionState.IDLE
        self.last_used = time.monotonic()
    
    def age(self) -> float:
        """Get age of connection in seconds."""
        return time.monotonic() - self.created_at
    
    def idle_time(self) -> float:
        """Get time since last use in seconds."""
        return time.monotonic() - self.last_used


class PoolExhaustedError(Exception):
    """Raised when pool is at max capacity and timeout is reached.
    
    This happens when:
    1. All connections are busy
    2. Pool is at max_size (can't create more)
    3. acquire_timeout has elapsed
    
    How to fix:
    1. Increase max_connections
    2. Increase acquire_timeout
    3. Reduce query time
    4. Use connection more efficiently (return faster)
    """
    pass


class PoolClosedError(Exception):
    """Raised when trying to use a closed pool."""
    pass


@dataclass
class PoolStats:
    """Pool statistics for monitoring.
    
    Attributes:
        size: Current number of connections
        idle: Number of idle connections
        busy: Number of busy connections
        waiting: Number of requests waiting for a connection
        min_size: Minimum pool size
        max_size: Maximum pool size
        total_acquires: Total number of successful acquires
        total_releases: Total number of releases
        total_timeouts: Number of acquire timeouts
        created: Total connections created
        closed: Total connections closed
        queue_depth: Current queue depth (Phase 5.2)
        queue_wait_avg_ms: Average queue wait time (Phase 5.2)
        queue_wait_p99_ms: 99th percentile queue wait time (Phase 5.2)
        warmup_success_rate: Warmup success rate (Phase 5.2)
        health_check_failures: Number of health check failures (Phase 5.2)
    """
    size: int = 0
    idle: int = 0
    busy: int = 0
    waiting: int = 0
    min_size: int = 1
    max_size: int = 10
    total_acquires: int = 0
    total_releases: int = 0
    total_timeouts: int = 0
    created: int = 0
    closed: int = 0
    # Phase 5.2 additions
    queue_depth: int = 0
    queue_wait_avg_ms: float = 0
    queue_wait_p99_ms: float = 0
    warmup_success_rate: float = 1.0
    health_check_failures: int = 0
    is_under_pressure: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/metrics."""
        return {
            "size": self.size,
            "idle": self.idle,
            "busy": self.busy,
            "waiting": self.waiting,
            "min_size": self.min_size,
            "max_size": self.max_size,
            "total_acquires": self.total_acquires,
            "total_releases": self.total_releases,
            "total_timeouts": self.total_timeouts,
            "utilization": self.busy / self.size if self.size > 0 else 0,
            # Phase 5.2 additions
            "queue_depth": self.queue_depth,
            "queue_wait_avg_ms": self.queue_wait_avg_ms,
            "queue_wait_p99_ms": self.queue_wait_p99_ms,
            "warmup_success_rate": self.warmup_success_rate,
            "health_check_failures": self.health_check_failures,
            "is_under_pressure": self.is_under_pressure,
        }


class AutoScalingPool:
    """Connection pool that automatically scales based on demand.
    
    This pool implements the following behaviors:
    
    1. **Lazy Initialization**: Connections are created on-demand
    2. **Auto-Scaling Up**: When all connections are busy, create more (up to max)
    3. **Auto-Scaling Down**: Close idle connections after timeout (down to min)
    4. **Connection Lifetime**: Replace old connections to prevent staleness
    
    Phase 5.2 Features:
    5. **Fair Queuing**: FIFO queue with backpressure when pool is exhausted
    6. **Lifecycle Management**: Soft/hard limits, graceful replacement
    7. **Connection Warmup**: Pre-warm connections for instant use
    8. **External Pooler Support**: PgBouncer, pgpool compatibility
    
    Basic Usage:
        pool = AutoScalingPool(
            config=PostgresConfig.from_url("postgresql://localhost/mydb"),
            min_size=1,
            max_size=10,
        )
        
        await pool.start()
        
        async with pool.acquire() as conn:
            result = await conn.fetch("SELECT 1")
        
        await pool.close()
    
    Production Usage:
        pool = AutoScalingPool(
            config=config,
            min_size=5,          # Keep 5 connections warm
            max_size=100,        # Can scale to 100 under load
            auto_scale=True,     # Enable auto-scaling
            idle_timeout=300,    # Close idle connections after 5 min
            max_lifetime=3600,   # Replace connections after 1 hour
            acquire_timeout=30,  # Wait up to 30s for a connection
            # Phase 5.2 features
            queue_config=QueueConfig(max_size=1000),
            lifecycle_config=LifecycleConfig(soft_lifetime=1800),
            warmup_config=WarmupConfig(enabled=True),
        )
    
    With External Pooler (PgBouncer):
        pool = AutoScalingPool(
            config=config,
            external_pooler=ExternalPoolerConfig(
                enabled=True,
                type=PoolerType.PGBOUNCER,
                mode=PoolerMode.TRANSACTION,
            ),
        )
    """
    
    def __init__(
        self,
        config: PostgresConfig,
        *,
        min_size: int = 1,
        max_size: int = 10,
        auto_scale: bool = True,
        idle_timeout: float = 300.0,
        max_lifetime: float = 3600.0,
        acquire_timeout: float = 30.0,
        connect_timeout: float = 10.0,
        command_timeout: Optional[float] = None,
        # Phase 5.2: Queue configuration
        queue_config: Optional[QueueConfig] = None,
        # Phase 5.2: Lifecycle configuration
        lifecycle_config: Optional[LifecycleConfig] = None,
        # Phase 5.2: Warmup configuration
        warmup_config: Optional[WarmupConfig] = None,
        # Phase 5.2: External pooler configuration
        external_pooler: Optional[ExternalPoolerConfig] = None,
    ):
        """Initialize the pool.
        
        Args:
            config: PostgreSQL connection configuration
            min_size: Minimum number of connections (default: 1)
            max_size: Maximum number of connections (default: 10)
            auto_scale: Enable automatic scaling (default: True)
            idle_timeout: Close idle connections after this many seconds (default: 300)
            max_lifetime: Replace connections older than this (default: 3600)
            acquire_timeout: Max time to wait for a connection (default: 30)
            connect_timeout: Timeout for creating new connections (default: 10)
            command_timeout: Default command timeout (default: None = no timeout)
            queue_config: Queue configuration for waiting requests (Phase 5.2)
            lifecycle_config: Lifecycle management configuration (Phase 5.2)
            warmup_config: Connection warmup configuration (Phase 5.2)
            external_pooler: External pooler (PgBouncer/pgpool) config (Phase 5.2)
        
        Raises:
            ValueError: If min_size > max_size or invalid values
        """
        # Validate
        if min_size < 0:
            raise ValueError(f"min_size must be >= 0, got {min_size}")
        if max_size < 1:
            raise ValueError(f"max_size must be >= 1, got {max_size}")
        if min_size > max_size:
            raise ValueError(
                f"min_size ({min_size}) cannot be greater than max_size ({max_size})"
            )
        if idle_timeout < 0:
            raise ValueError(f"idle_timeout must be >= 0, got {idle_timeout}")
        if max_lifetime < 0:
            raise ValueError(f"max_lifetime must be >= 0, got {max_lifetime}")
        
        self._config = config
        self._min_size = min_size
        self._max_size = max_size
        self._auto_scale = auto_scale
        self._idle_timeout = idle_timeout
        self._max_lifetime = max_lifetime
        self._acquire_timeout = acquire_timeout
        self._connect_timeout = connect_timeout
        self._command_timeout = command_timeout
        
        # State
        self._state = PoolState.UNINITIALIZED
        self._connections: List[PooledConnection] = []
        self._busy_connections: Set[str] = set()  # Track which connections are busy
        self._waiters: asyncio.Queue[asyncio.Future] = asyncio.Queue()
        
        # Synchronization
        self._lock = asyncio.Lock()
        
        # Statistics
        self._stats = PoolStats(min_size=min_size, max_size=max_size)
        
        # Background tasks
        self._maintenance_task: Optional[asyncio.Task] = None
        
        # Phase 5.2: Advanced queue management
        self._queue = ConnectionQueue(queue_config or QueueConfig(
            max_wait_time=acquire_timeout,
        ))
        
        # Phase 5.2: Lifecycle management
        lifecycle_cfg = lifecycle_config or LifecycleConfig(
            max_lifetime=max_lifetime,
            soft_lifetime=max_lifetime / 2,
        )
        self._lifecycle_manager = LifecycleManager(lifecycle_cfg)
        
        # Phase 5.2: Connection warmup
        self._warmer = ConnectionWarmer(warmup_config or WarmupConfig())
        
        # Phase 5.2: External pooler support
        self._external_pooler = ExternalPoolerManager(
            external_pooler or ExternalPoolerConfig()
        )
        
        # Connection ID counter
        self._connection_id_counter = 0
    
    @property
    def size(self) -> int:
        """Current number of connections in the pool."""
        return len(self._connections)
    
    @property
    def state(self) -> PoolState:
        """Current pool state."""
        return self._state
    
    @property
    def is_under_pressure(self) -> bool:
        """Check if pool is under pressure (queue has waiting requests)."""
        return self._queue.is_under_pressure
    
    @property
    def queue_depth(self) -> int:
        """Current number of requests waiting in queue."""
        return self._queue.depth
    
    @property
    def lifecycle_manager(self) -> LifecycleManager:
        """Get the lifecycle manager for advanced control."""
        return self._lifecycle_manager
    
    @property
    def warmer(self) -> ConnectionWarmer:
        """Get the connection warmer for advanced control."""
        return self._warmer
    
    @property
    def external_pooler(self) -> ExternalPoolerManager:
        """Get the external pooler manager."""
        return self._external_pooler
    
    async def start(self) -> None:
        """Start the pool and create initial connections.
        
        This method:
        1. Creates min_size initial connections
        2. Warms up connections (if warmup enabled)
        3. Detects external pooler (if enabled)
        4. Starts the maintenance task (for cleanup)
        5. Sets pool state to RUNNING
        
        Example:
            pool = AutoScalingPool(config)
            await pool.start()
            # Pool is now ready to use
        """
        if self._state != PoolState.UNINITIALIZED:
            logger.warning(f"Pool already in state {self._state}")
            return
        
        logger.info(f"Starting pool (min={self._min_size}, max={self._max_size})")
        
        # Create initial connections
        connections_to_warm = {}
        async with self._lock:
            for _ in range(self._min_size):
                try:
                    pooled = await self._create_connection()
                    self._connections.append(pooled)
                    connections_to_warm[pooled.connection_id] = pooled.connection
                except Exception as e:
                    logger.error(f"Failed to create initial connection: {e}")
        
        # Phase 5.2: Detect external pooler on first connection
        if self._external_pooler.is_enabled and self._connections:
            try:
                await self._external_pooler.detect_pooler(
                    self._connections[0].connection
                )
            except Exception as e:
                logger.warning(f"Failed to detect external pooler: {e}")
        
        # Phase 5.2: Warm up connections
        if self._warmer.enabled and connections_to_warm:
            warmup_results = await self._warmer.warmup_all(connections_to_warm)
            successful = sum(1 for r in warmup_results if r.success)
            logger.info(f"Warmed {successful}/{len(warmup_results)} connections")
        
        self._state = PoolState.RUNNING
        
        # Start maintenance task
        self._maintenance_task = asyncio.create_task(self._maintenance_loop())
        
        logger.info(f"Pool started with {self.size} connections")
    
    async def close(self) -> None:
        """Close the pool and all connections.
        
        This method:
        1. Stops accepting new requests
        2. Cancels all queued requests
        3. Waits for busy connections to be released
        4. Closes all connections
        5. Cancels maintenance task
        
        Example:
            await pool.close()
            # Pool is now closed
        """
        if self._state == PoolState.CLOSED:
            return
        
        logger.info("Closing pool...")
        self._state = PoolState.CLOSING
        
        # Phase 5.2: Cancel all queued requests
        cancelled = self._queue.cancel_all()
        if cancelled:
            logger.info(f"Cancelled {cancelled} queued requests")
        
        # Cancel maintenance
        if self._maintenance_task:
            self._maintenance_task.cancel()
            try:
                await self._maintenance_task
            except asyncio.CancelledError:
                pass
        
        # Close all connections
        async with self._lock:
            for pooled in self._connections:
                await self._close_connection(pooled)
            self._connections.clear()
            self._busy_connections.clear()
        
        self._state = PoolState.CLOSED
        logger.info("Pool closed")
    
    @asynccontextmanager
    async def acquire(self) -> AsyncIterator["asyncpg.Connection"]:
        """Acquire a connection from the pool.
        
        This is the main API for using the pool. It:
        1. Gets an idle connection (or creates one if needed)
        2. Marks it as busy
        3. Returns it for use
        4. On exit, marks it idle again
        
        Yields:
            asyncpg.Connection that can be used for queries
        
        Raises:
            PoolExhaustedError: If no connection available within timeout
            PoolClosedError: If pool is closed
        
        Example:
            async with pool.acquire() as conn:
                result = await conn.fetch("SELECT * FROM users")
        """
        if self._state != PoolState.RUNNING:
            raise PoolClosedError(
                f"Cannot acquire from pool in state {self._state}.\n"
                "Make sure to call pool.start() first."
            )
        
        connection = await self._acquire_connection()
        
        try:
            yield connection.connection
        finally:
            await self._release_connection(connection)
    
    async def _acquire_connection(self) -> PooledConnection:
        """Internal: Get a connection from the pool.
        
        Phase 5.2 enhancements:
        - Uses advanced queue with fair FIFO ordering
        - Respects lifecycle manager for connection health
        - Warm new connections if warmup is enabled
        """
        start_time = time.monotonic()
        
        while True:
            # Check timeout
            elapsed = time.monotonic() - start_time
            if elapsed >= self._acquire_timeout:
                self._stats.total_timeouts += 1
                raise PoolExhaustedError(
                    f"Timeout waiting for connection after {elapsed:.1f}s.\n"
                    f"Pool stats: {self.get_stats().to_dict()}\n"
                    "Consider increasing max_connections or acquire_timeout."
                )
            
            async with self._lock:
                # Try to get an idle connection
                for pooled in self._connections:
                    if pooled.state == ConnectionState.IDLE:
                        # Phase 5.2: Check lifecycle - should we retire this connection?
                        reason = self._lifecycle_manager.should_retire(pooled.connection_id)
                        if reason:
                            logger.debug(
                                f"Retiring connection {pooled.connection_id}: {reason.value}"
                            )
                            await self._close_connection(pooled)
                            self._connections.remove(pooled)
                            continue
                        
                        # Legacy check: connection too old (for backward compat)
                        if self._max_lifetime > 0 and pooled.age() > self._max_lifetime:
                            await self._close_connection(pooled)
                            self._connections.remove(pooled)
                            continue
                        
                        # Use this connection
                        pooled.mark_busy()
                        self._busy_connections.add(pooled.connection_id)
                        self._lifecycle_manager.mark_used(pooled.connection_id)
                        self._stats.total_acquires += 1
                        self._update_stats()
                        logger.debug(f"Acquired connection {pooled.connection_id}")
                        return pooled
                
                # No idle connections - can we create one?
                if self._auto_scale and len(self._connections) < self._max_size:
                    try:
                        pooled = await self._create_connection()
                        
                        # Phase 5.2: Warm new connection if enabled
                        if self._warmer.enabled:
                            result = await self._warmer.warmup_connection(
                                pooled.connection_id,
                                pooled.connection,
                            )
                            if not result.success:
                                logger.warning(
                                    f"Warmup failed for {pooled.connection_id}"
                                )
                        
                        pooled.mark_busy()
                        self._busy_connections.add(pooled.connection_id)
                        self._lifecycle_manager.mark_used(pooled.connection_id)
                        self._connections.append(pooled)
                        self._stats.total_acquires += 1
                        self._update_stats()
                        logger.info(f"Scaled up pool to {self.size} connections")
                        return pooled
                    except Exception as e:
                        logger.error(f"Failed to create connection: {e}")
            
            # Phase 5.2: Pool exhausted - enter queue
            if self._queue.depth < self._queue.config.max_size:
                try:
                    remaining_timeout = self._acquire_timeout - elapsed
                    await self._queue.enqueue(timeout=remaining_timeout)
                    # Queue returned - a connection should now be available
                    continue
                except QueueTimeoutError:
                    self._stats.total_timeouts += 1
                    raise PoolExhaustedError(
                        f"Queue timeout after {elapsed:.1f}s.\n"
                        f"Pool stats: {self.get_stats().to_dict()}\n"
                        "Consider increasing pool size or queue timeout."
                    )
                except QueueFullError as e:
                    raise PoolExhaustedError(
                        f"Queue full with {e.queue_size} waiting.\n"
                        f"Pool stats: {self.get_stats().to_dict()}\n"
                        "System is overloaded."
                    )
            else:
                # Wait a bit before retrying
                await asyncio.sleep(0.01)
    
    async def _release_connection(self, pooled: PooledConnection) -> None:
        """Internal: Return a connection to the pool.
        
        Phase 5.2 enhancements:
        - Notify queue when connection is available
        - Check if connection should be retired
        """
        async with self._lock:
            if pooled.state == ConnectionState.BUSY:
                self._busy_connections.discard(pooled.connection_id)
                
                # Phase 5.2: Check if connection should be retired on release
                reason = self._lifecycle_manager.should_prefer_retirement(
                    pooled.connection_id
                )
                if reason:
                    logger.debug(
                        f"Retiring connection {pooled.connection_id} on release: "
                        f"{reason.value}"
                    )
                    await self._close_connection(pooled)
                    self._connections.remove(pooled)
                    
                    # Notify queue that capacity freed up
                    self._queue.notify_available()
                    return
                
                pooled.mark_idle()
                self._stats.total_releases += 1
                self._update_stats()
                logger.debug(f"Released connection {pooled.connection_id}")
                
                # Phase 5.2: Notify queue that connection is available
                self._queue.notify_available()
    
    async def _create_connection(self) -> PooledConnection:
        """Internal: Create a new database connection."""
        try:
            import asyncpg
        except ImportError:
            raise ImportError(
                "asyncpg is required for PostgreSQL support.\n"
                "Install it with: pip install asyncpg"
            )
        
        kwargs = self._config.to_asyncpg_kwargs()
        kwargs["timeout"] = self._connect_timeout
        if self._command_timeout:
            kwargs["command_timeout"] = self._command_timeout
        
        # Phase 5.2: Apply external pooler connection options
        if self._external_pooler.is_enabled:
            pooler_opts = self._external_pooler.get_connection_options()
            kwargs.update(pooler_opts)
        
        connection = await asyncpg.connect(**kwargs)
        
        # Generate unique connection ID
        self._connection_id_counter += 1
        connection_id = f"conn_{self._connection_id_counter}"
        
        # Phase 5.2: Register with lifecycle manager
        self._lifecycle_manager.register_connection(connection_id)
        
        self._stats.created += 1
        logger.debug(f"Created connection {connection_id} (total: {self._stats.created})")
        
        return PooledConnection(
            connection=connection,
            connection_id=connection_id,
        )
    
    async def _close_connection(self, pooled: PooledConnection) -> None:
        """Internal: Close a connection."""
        if pooled.state != ConnectionState.CLOSED:
            pooled.state = ConnectionState.CLOSING
            try:
                await pooled.connection.close()
            except Exception as e:
                logger.warning(f"Error closing connection {pooled.connection_id}: {e}")
            pooled.state = ConnectionState.CLOSED
            
            # Phase 5.2: Unregister from lifecycle manager
            self._lifecycle_manager.unregister_connection(pooled.connection_id)
            self._busy_connections.discard(pooled.connection_id)
            
            self._stats.closed += 1
            logger.debug(f"Closed connection {pooled.connection_id}")
    
    async def _maintenance_loop(self) -> None:
        """Background task to clean up idle connections and run health checks.
        
        Phase 5.2 enhancements:
        - Run health checks on connections needing them
        - Retire connections based on lifecycle rules
        """
        while self._state == PoolState.RUNNING:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                await self._cleanup_idle_connections()
                
                # Phase 5.2: Run health checks
                await self._run_health_checks()
                
                # Phase 5.2: Retire connections that should be retired
                await self._retire_old_connections()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in maintenance loop: {e}")
    
    async def _run_health_checks(self) -> None:
        """Phase 5.2: Run health checks on connections that need them."""
        connections_to_check = self._lifecycle_manager.get_connections_needing_health_check()
        
        if not connections_to_check:
            return
        
        # Build mapping of connection_id to actual connection
        conn_map = {}
        for pooled in self._connections:
            if (
                pooled.connection_id in connections_to_check
                and pooled.state == ConnectionState.IDLE
            ):
                conn_map[pooled.connection_id] = pooled.connection
        
        if conn_map:
            unhealthy = await self._lifecycle_manager.check_all_health(conn_map)
            self._stats.health_check_failures += len(unhealthy)
    
    async def _retire_old_connections(self) -> None:
        """Phase 5.2: Retire connections that should be retired."""
        to_retire = self._lifecycle_manager.get_connections_to_retire()
        
        async with self._lock:
            for conn_id in to_retire:
                for pooled in self._connections[:]:  # Copy list to allow modification
                    if (
                        pooled.connection_id == conn_id
                        and pooled.state == ConnectionState.IDLE
                    ):
                        await self._close_connection(pooled)
                        self._connections.remove(pooled)
                        logger.info(f"Retired connection {conn_id}")
                        break
    
    async def _cleanup_idle_connections(self) -> None:
        """Close connections that have been idle too long."""
        async with self._lock:
            to_close = []
            
            for pooled in self._connections:
                # Don't go below min_size
                if len(self._connections) - len(to_close) <= self._min_size:
                    break
                
                # Check if idle too long
                if (
                    pooled.state == ConnectionState.IDLE
                    and self._idle_timeout > 0
                    and pooled.idle_time() > self._idle_timeout
                ):
                    to_close.append(pooled)
            
            for pooled in to_close:
                await self._close_connection(pooled)
                self._connections.remove(pooled)
                logger.info(f"Closed idle connection (pool size: {self.size})")
    
    def _update_stats(self) -> None:
        """Update pool statistics."""
        self._stats.size = len(self._connections)
        self._stats.idle = sum(
            1 for c in self._connections if c.state == ConnectionState.IDLE
        )
        self._stats.busy = sum(
            1 for c in self._connections if c.state == ConnectionState.BUSY
        )
    
    def get_stats(self) -> PoolStats:
        """Get current pool statistics.
        
        Returns:
            PoolStats with current values including Phase 5.2 metrics
        
        Example:
            stats = pool.get_stats()
            print(f"Pool: {stats.busy}/{stats.size} connections busy")
            print(f"Queue: {stats.queue_depth} waiting")
        """
        self._update_stats()
        
        # Phase 5.2: Add queue statistics
        queue_stats = self._queue.get_stats()
        self._stats.queue_depth = queue_stats.depth
        self._stats.queue_wait_avg_ms = queue_stats.wait_time_avg_ms
        self._stats.queue_wait_p99_ms = queue_stats.wait_time_p99_ms
        
        # Phase 5.2: Add warmup statistics
        warmup_stats = self._warmer.get_stats()
        self._stats.warmup_success_rate = warmup_stats.success_rate
        
        # Phase 5.2: Add lifecycle statistics
        lifecycle_stats = self._lifecycle_manager.get_stats()
        self._stats.health_check_failures = lifecycle_stats.health_checks_failed
        
        # Phase 5.2: Pressure indicator
        self._stats.is_under_pressure = self._queue.is_under_pressure
        
        return self._stats
    
    def get_queue_stats(self) -> QueueStats:
        """Get detailed queue statistics.
        
        Returns:
            QueueStats with queue-specific metrics
        """
        return self._queue.get_stats()
    
    def get_lifecycle_stats(self) -> LifecycleStats:
        """Get detailed lifecycle statistics.
        
        Returns:
            LifecycleStats with lifecycle-specific metrics
        """
        return self._lifecycle_manager.get_stats()
    
    def get_warmup_stats(self) -> WarmupStats:
        """Get detailed warmup statistics.
        
        Returns:
            WarmupStats with warmup-specific metrics
        """
        return self._warmer.get_stats()
    
    async def execute(
        self,
        query: str,
        *args: Any,
        timeout: Optional[float] = None,
    ) -> str:
        """Execute a query and return status.
        
        Convenience method for executing queries without managing connections.
        
        Args:
            query: SQL query to execute
            *args: Query parameters
            timeout: Query timeout (default: command_timeout)
        
        Returns:
            Status string from PostgreSQL
        
        Example:
            await pool.execute("INSERT INTO users (name) VALUES ($1)", "John")
        """
        async with self.acquire() as conn:
            return await conn.execute(query, *args, timeout=timeout)
    
    async def fetch(
        self,
        query: str,
        *args: Any,
        timeout: Optional[float] = None,
    ) -> List[Any]:
        """Execute a query and return all rows.
        
        Args:
            query: SQL query to execute
            *args: Query parameters
            timeout: Query timeout
        
        Returns:
            List of rows
        
        Example:
            users = await pool.fetch("SELECT * FROM users WHERE age > $1", 18)
        """
        async with self.acquire() as conn:
            return await conn.fetch(query, *args, timeout=timeout)
    
    async def fetchrow(
        self,
        query: str,
        *args: Any,
        timeout: Optional[float] = None,
    ) -> Optional[Any]:
        """Execute a query and return one row.
        
        Args:
            query: SQL query to execute
            *args: Query parameters
            timeout: Query timeout
        
        Returns:
            Single row or None
        
        Example:
            user = await pool.fetchrow("SELECT * FROM users WHERE id = $1", 1)
        """
        async with self.acquire() as conn:
            return await conn.fetchrow(query, *args, timeout=timeout)
    
    async def fetchval(
        self,
        query: str,
        *args: Any,
        column: int = 0,
        timeout: Optional[float] = None,
    ) -> Any:
        """Execute a query and return a single value.
        
        Args:
            query: SQL query to execute
            *args: Query parameters
            column: Column index to return (default: 0)
            timeout: Query timeout
        
        Returns:
            Single value or None
        
        Example:
            count = await pool.fetchval("SELECT COUNT(*) FROM users")
        """
        async with self.acquire() as conn:
            return await conn.fetchval(query, *args, column=column, timeout=timeout)
    
    def __repr__(self) -> str:
        """Return string representation."""
        stats = self.get_stats()
        return (
            f"AutoScalingPool("
            f"state={self._state.value}, "
            f"size={stats.size}/{self._max_size}, "
            f"busy={stats.busy}, "
            f"idle={stats.idle})"
        )

