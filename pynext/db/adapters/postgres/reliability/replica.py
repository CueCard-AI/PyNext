"""
PostgreSQL Read Replica Routing.

This module provides intelligent read replica routing with lag detection,
weighted distribution, and automatic failover.

Why Read Replicas?

PostgreSQL supports streaming replication, allowing you to create read-only
copies of your database. Benefits:

1. Scale reads: Route SELECT queries to replicas
2. Reduce primary load: Primary handles writes only
3. Geographic distribution: Replicas near users
4. High availability: Failover if primary dies

How It Works:

    ┌──────────────────────────────────────────────────────────────────┐
    │                         Your Application                          │
    │                                                                   │
    │   await User.get(1)      await User.insert(name="John")          │
    │         │                         │                               │
    │         ▼                         ▼                               │
    │   ┌─────────────────────────────────────────────────────────┐    │
    │   │                   ReplicaManager                         │    │
    │   │                                                          │    │
    │   │   is_read_query? ─────► route_to_replica()              │    │
    │   │                              │                           │    │
    │   │   is_write_query? ────► route_to_primary()              │    │
    │   └──────────────────────────────────────────────────────────┘    │
    │              │                         │                          │
    └──────────────┼─────────────────────────┼──────────────────────────┘
                   │                         │
         ┌─────────┴─────────┐              │
         ▼         ▼         ▼              ▼
    ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
    │Replica 1│ │Replica 2│ │Replica 3│ │ Primary │
    │(weight 3)│ │(weight 2)│ │(weight 1)│ │(writes) │
    └─────────┘ └─────────┘ └─────────┘ └─────────┘

Routing Strategies:

1. WEIGHTED_RANDOM: Random selection weighted by replica weight
2. ROUND_ROBIN: Cycle through replicas in order
3. LEAST_CONNECTIONS: Route to replica with fewest active connections

Lag Detection:

Replicas may fall behind the primary. PyNext:
1. Periodically checks replication lag
2. Removes lagging replicas from rotation
3. Falls back to primary if all replicas lag
4. Automatically re-adds recovered replicas

AI-Friendly Design:
- Simple configuration (just URLs)
- Advanced options when needed
- Observable metrics
- Comprehensive logging
"""

from __future__ import annotations

import asyncio
import logging
import random
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, TYPE_CHECKING, Union

if TYPE_CHECKING:
    import asyncpg

logger = logging.getLogger("pynext.db.postgres.replica")


class RoutingStrategy(Enum):
    """Strategy for selecting which replica to use.
    
    WEIGHTED_RANDOM: Random selection, weighted by replica weight.
                    Higher weight = more likely to be selected.
    
    ROUND_ROBIN: Cycle through replicas in order.
                Ignores weights, fair distribution.
    
    LEAST_CONNECTIONS: Route to replica with fewest active connections.
                      Good for uneven query durations.
    """
    WEIGHTED_RANDOM = "weighted_random"
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"


class ReplicaHealth(Enum):
    """Health status of a replica.
    
    HEALTHY: Replica is responding and within lag threshold
    LAGGING: Replica is responding but behind primary
    UNHEALTHY: Replica is not responding
    UNKNOWN: Health hasn't been checked yet
    """
    HEALTHY = "healthy"
    LAGGING = "lagging"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class Replica:
    """Configuration for a read replica.
    
    Supports two configuration styles:
    1. URL string (simple)
    2. Keyword arguments (explicit)
    
    Attributes:
        url: PostgreSQL connection URL for the replica (optional if using kwargs)
        host: Database host (alternative to URL)
        port: Database port (default: 5432)
        database: Database name
        user: Database user
        password: Database password
        ssl: Enable SSL (default: False)
        weight: Selection weight (higher = more traffic).
               Default: 1
        max_lag: Maximum acceptable replication lag in seconds.
                Default: 10.0
        name: Human-readable name for logging.
             Default: auto-generated from host/URL
        enabled: Whether this replica is enabled.
                Default: True
    
    Example:
        # Style 1: URL (simple)
        replica = Replica("postgresql://replica1/mydb")
        
        # Style 2: Keyword arguments (explicit)
        replica = Replica(
            host="replica1.example.com",
            port=5432,
            database="mydb",
            user="postgres",
            password="secret",
            ssl=True,
            weight=3,
        )
        
        # Weighted replica (gets 3x traffic)
        replica = Replica(
            "postgresql://replica1/mydb",
            weight=3,
            name="us-east-replica",
        )
        
        # Low-latency replica (strict lag requirement)
        replica = Replica(
            host="replica2.example.com",
            database="mydb",
            user="postgres",
            password="secret",
            max_lag=2.0,  # Max 2 seconds behind
        )
    """
    # URL-based configuration
    url: Optional[str] = None
    
    # Keyword argument configuration
    host: Optional[str] = None
    port: int = 5432
    database: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None
    ssl: bool = False
    
    # Replica-specific settings
    weight: int = 1
    max_lag: float = 10.0
    name: Optional[str] = None
    enabled: bool = True
    
    def __post_init__(self) -> None:
        """Validate and build URL if needed."""
        # Validation
        if self.weight < 1:
            raise ValueError(f"weight must be >= 1, got {self.weight}")
        if self.max_lag < 0:
            raise ValueError(f"max_lag must be >= 0, got {self.max_lag}")
        
        # Build URL from keyword args if not provided
        if self.url is None and self.host is not None:
            self.url = self._build_url()
        elif self.url is None and self.host is None:
            raise ValueError("Either 'url' or 'host' must be provided")
        
        # Auto-generate name
        if self.name is None:
            if self.host:
                self.name = f"{self.host}:{self.port}"
            else:
                self.name = self._extract_name_from_url()
    
    def _build_url(self) -> str:
        """Build a PostgreSQL URL from keyword arguments."""
        # Start with protocol
        url = "postgresql://"
        
        # Add credentials
        if self.user:
            url += self.user
            if self.password:
                # URL-encode the password
                from urllib.parse import quote
                url += f":{quote(self.password, safe='')}"
            url += "@"
        
        # Add host and port
        url += f"{self.host}:{self.port}"
        
        # Add database
        if self.database:
            url += f"/{self.database}"
        
        # Add SSL parameter
        if self.ssl:
            url += "?sslmode=require"
        
        return url
    
    def _extract_name_from_url(self) -> str:
        """Extract a readable name from the URL."""
        # Remove protocol
        url = self.url.replace("postgresql://", "").replace("postgres://", "")
        # Get host part
        host = url.split("@")[-1].split("/")[0].split(":")[0]
        return f"replica-{host}"


@dataclass
class ReplicaConfig:
    """Configuration for replica routing.
    
    Attributes:
        replicas: List of Replica configurations
        routing: Routing strategy (weighted_random, round_robin, least_connections)
        lag_check_interval: Seconds between lag checks.
                           Default: 5.0
        lag_check_query: SQL query to check replication lag.
                        Default: PostgreSQL-specific lag query
        failover_timeout: Seconds to wait before failover to primary.
                         Default: 10.0
        read_from_primary_on_lag: Fall back to primary if all replicas lag.
                                 Default: True
        min_healthy_replicas: Minimum healthy replicas before alerting.
                             Default: 1
        health_check_timeout: Timeout for health check queries.
                             Default: 5.0
    
    Example:
        config = ReplicaConfig(
            replicas=[
                Replica("postgresql://replica1/mydb", weight=3),
                Replica("postgresql://replica2/mydb", weight=1),
            ],
            routing="weighted_random",
            lag_check_interval=10.0,
        )
    """
    replicas: List[Replica] = field(default_factory=list)
    routing: str = "weighted_random"
    lag_check_interval: float = 5.0
    lag_check_query: str = "SELECT EXTRACT(EPOCH FROM (NOW() - pg_last_xact_replay_timestamp()))::float"
    failover_timeout: float = 10.0
    read_from_primary_on_lag: bool = True
    min_healthy_replicas: int = 1
    health_check_timeout: float = 5.0
    
    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.routing not in ("weighted_random", "round_robin", "least_connections"):
            raise ValueError(f"routing must be weighted_random/round_robin/least_connections, got {self.routing}")
        if self.lag_check_interval < 0:
            raise ValueError(f"lag_check_interval must be >= 0, got {self.lag_check_interval}")


@dataclass
class ReplicaStats:
    """Statistics for a single replica.
    
    Tracks lag, request counts, errors, and health.
    """
    name: str = ""
    current_lag_ms: float = 0.0
    last_lag_check: float = 0.0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    active_connections: int = 0
    health: ReplicaHealth = ReplicaHealth.UNKNOWN
    last_error: Optional[str] = None
    last_error_time: float = 0.0
    
    @property
    def success_rate(self) -> float:
        """Success rate as fraction (0-1)."""
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests
    
    @property
    def error_rate(self) -> float:
        """Error rate as fraction (0-1)."""
        if self.total_requests == 0:
            return 0.0
        return self.failed_requests / self.total_requests
    
    def record_request(self) -> None:
        """Record a request to this replica."""
        self.total_requests += 1
    
    def record_success(self) -> None:
        """Record a successful request."""
        self.successful_requests += 1
    
    def record_failure(self, error: str) -> None:
        """Record a failed request."""
        self.failed_requests += 1
        self.last_error = error
        self.last_error_time = time.monotonic()
    
    def record_lag(self, lag_ms: float) -> None:
        """Record replication lag."""
        self.current_lag_ms = lag_ms
        self.last_lag_check = time.monotonic()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/metrics."""
        return {
            "name": self.name,
            "health": self.health.value,
            "lag_ms": self.current_lag_ms,
            "total_requests": self.total_requests,
            "success_rate": self.success_rate,
            "active_connections": self.active_connections,
            "last_error": self.last_error,
        }


@dataclass
class ReplicaSetStats:
    """Aggregate statistics for all replicas."""
    primary_requests: int = 0
    replica_requests: int = 0
    failovers_to_primary: int = 0
    total_lag_checks: int = 0
    replicas: Dict[str, ReplicaStats] = field(default_factory=dict)
    
    @property
    def read_distribution(self) -> Dict[str, float]:
        """Distribution of reads across replicas."""
        total = sum(s.total_requests for s in self.replicas.values())
        if total == 0:
            return {}
        return {
            name: stats.total_requests / total
            for name, stats in self.replicas.items()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/metrics."""
        return {
            "primary_requests": self.primary_requests,
            "replica_requests": self.replica_requests,
            "failovers_to_primary": self.failovers_to_primary,
            "healthy_replicas": sum(
                1 for s in self.replicas.values()
                if s.health == ReplicaHealth.HEALTHY
            ),
            "total_replicas": len(self.replicas),
            "replicas": {
                name: stats.to_dict()
                for name, stats in self.replicas.items()
            },
        }


class ReplicaUnavailableError(Exception):
    """Raised when no replicas are available.
    
    Attributes:
        replica_states: Current state of each replica
    """
    
    def __init__(self, message: str, replica_states: Dict[str, str]):
        super().__init__(message)
        self.replica_states = replica_states


class ReplicaManager:
    """Manages read replica routing and health.
    
    This class handles:
    - Selecting replicas for read queries
    - Monitoring replication lag
    - Failing over to primary when needed
    - Health checking replicas
    
    Usage:
        # Create manager
        manager = ReplicaManager(
            config=ReplicaConfig(
                replicas=[
                    Replica("postgresql://replica1/db"),
                    Replica("postgresql://replica2/db"),
                ],
            ),
            primary_pool=primary_pool,
        )
        
        # Start monitoring
        await manager.start()
        
        # Route reads
        conn = await manager.get_read_connection()
        
        # Route writes (always primary)
        conn = await manager.get_write_connection()
    """
    
    def __init__(
        self,
        config: ReplicaConfig,
        primary_pool: Any = None,  # AutoScalingPool
        create_pool: Optional[Callable] = None,
    ):
        """Initialize the replica manager.
        
        Args:
            config: Replica configuration
            primary_pool: Connection pool for primary
            create_pool: Factory function to create replica pools
        """
        self._config = config
        self._primary_pool = primary_pool
        self._create_pool = create_pool
        
        # Replica pools and stats
        self._replica_pools: Dict[str, Any] = {}
        self._replica_stats: Dict[str, ReplicaStats] = {}
        self._replica_health: Dict[str, ReplicaHealth] = {}
        
        # Routing state
        self._round_robin_index = 0
        self._lock = threading.Lock()
        
        # Monitoring
        self._monitoring_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Aggregate stats
        self._stats = ReplicaSetStats()
        
        # Initialize replica stats
        for replica in config.replicas:
            name = replica.name or replica.url
            self._replica_stats[name] = ReplicaStats(name=name)
            self._replica_health[name] = ReplicaHealth.UNKNOWN
            self._stats.replicas[name] = self._replica_stats[name]
    
    @property
    def config(self) -> ReplicaConfig:
        """Get the replica configuration."""
        return self._config
    
    @property
    def stats(self) -> ReplicaSetStats:
        """Get aggregate statistics."""
        return self._stats
    
    def get_replica_stats(self, name: str) -> Optional[ReplicaStats]:
        """Get statistics for a specific replica."""
        return self._replica_stats.get(name)
    
    def get_healthy_replicas(self) -> List[Replica]:
        """Get list of currently healthy replicas."""
        healthy = []
        for replica in self._config.replicas:
            if not replica.enabled:
                continue
            name = replica.name or replica.url
            if self._replica_health.get(name) == ReplicaHealth.HEALTHY:
                healthy.append(replica)
        return healthy
    
    def get_all_replica_health(self) -> Dict[str, ReplicaHealth]:
        """Get health status of all replicas."""
        return dict(self._replica_health)
    
    async def start(self) -> None:
        """Start the replica manager.
        
        Creates connection pools for each replica and starts
        the monitoring task.
        """
        if self._running:
            return
        
        logger.info(f"Starting replica manager with {len(self._config.replicas)} replicas")
        
        # Create pools for each replica
        for replica in self._config.replicas:
            if not replica.enabled:
                continue
            
            name = replica.name or replica.url
            try:
                if self._create_pool:
                    pool = await self._create_pool(replica.url)
                    self._replica_pools[name] = pool
                    self._replica_health[name] = ReplicaHealth.HEALTHY
                    logger.info(f"Created pool for replica '{name}'")
            except Exception as e:
                logger.error(f"Failed to create pool for replica '{name}': {e}")
                self._replica_health[name] = ReplicaHealth.UNHEALTHY
        
        # Start monitoring
        self._running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info(f"Replica manager started with {len(self._replica_pools)} active pools")
    
    async def stop(self) -> None:
        """Stop the replica manager.
        
        Stops monitoring and closes all replica pools.
        """
        if not self._running:
            return
        
        logger.info("Stopping replica manager")
        
        self._running = False
        
        # Cancel monitoring task
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        # Close replica pools
        for name, pool in self._replica_pools.items():
            try:
                if hasattr(pool, "close"):
                    await pool.close()
                logger.info(f"Closed pool for replica '{name}'")
            except Exception as e:
                logger.error(f"Error closing pool for replica '{name}': {e}")
        
        self._replica_pools.clear()
        logger.info("Replica manager stopped")
    
    async def _monitoring_loop(self) -> None:
        """Background task that monitors replica health and lag."""
        while self._running:
            try:
                await self._check_all_replicas()
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
            
            await asyncio.sleep(self._config.lag_check_interval)
    
    async def _check_all_replicas(self) -> None:
        """Check health and lag for all replicas."""
        for replica in self._config.replicas:
            if not replica.enabled:
                continue
            
            name = replica.name or replica.url
            pool = self._replica_pools.get(name)
            
            if pool is None:
                continue
            
            try:
                lag_seconds = await self._check_replica_lag(name, pool)
                self._stats.total_lag_checks += 1
                
                stats = self._replica_stats[name]
                stats.record_lag(lag_seconds * 1000)  # Convert to ms
                
                # Update health based on lag
                if lag_seconds is None:
                    self._replica_health[name] = ReplicaHealth.UNHEALTHY
                    stats.health = ReplicaHealth.UNHEALTHY
                elif lag_seconds > replica.max_lag:
                    self._replica_health[name] = ReplicaHealth.LAGGING
                    stats.health = ReplicaHealth.LAGGING
                    logger.warning(
                        f"Replica '{name}' is lagging: {lag_seconds:.1f}s "
                        f"(max: {replica.max_lag}s)"
                    )
                else:
                    self._replica_health[name] = ReplicaHealth.HEALTHY
                    stats.health = ReplicaHealth.HEALTHY
                    
            except Exception as e:
                logger.error(f"Error checking replica '{name}': {e}")
                self._replica_health[name] = ReplicaHealth.UNHEALTHY
                self._replica_stats[name].health = ReplicaHealth.UNHEALTHY
                self._replica_stats[name].record_failure(str(e))
    
    async def _check_replica_lag(self, name: str, pool: Any) -> Optional[float]:
        """Check replication lag for a replica.
        
        Args:
            name: Replica name
            pool: Connection pool for the replica
        
        Returns:
            Lag in seconds, or None if check failed
        """
        try:
            async with asyncio.timeout(self._config.health_check_timeout):
                if hasattr(pool, "acquire"):
                    async with pool.acquire() as conn:
                        result = await conn.fetchval(self._config.lag_check_query)
                        return float(result) if result is not None else 0.0
                return None
        except asyncio.TimeoutError:
            logger.warning(f"Lag check timed out for replica '{name}'")
            return None
        except Exception as e:
            logger.error(f"Lag check failed for replica '{name}': {e}")
            return None
    
    def _select_replica_weighted_random(self, replicas: List[Replica]) -> Replica:
        """Select a replica using weighted random selection."""
        total_weight = sum(r.weight for r in replicas)
        if total_weight == 0:
            return random.choice(replicas)
        
        threshold = random.uniform(0, total_weight)
        cumulative = 0
        
        for replica in replicas:
            cumulative += replica.weight
            if cumulative >= threshold:
                return replica
        
        return replicas[-1]
    
    def _select_replica_round_robin(self, replicas: List[Replica]) -> Replica:
        """Select a replica using round-robin."""
        with self._lock:
            replica = replicas[self._round_robin_index % len(replicas)]
            self._round_robin_index += 1
            return replica
    
    def _select_replica_least_connections(self, replicas: List[Replica]) -> Replica:
        """Select the replica with fewest active connections."""
        min_connections = float("inf")
        selected = replicas[0]
        
        for replica in replicas:
            name = replica.name or replica.url
            stats = self._replica_stats.get(name)
            if stats and stats.active_connections < min_connections:
                min_connections = stats.active_connections
                selected = replica
        
        return selected
    
    def select_replica(self) -> Optional[Replica]:
        """Select a replica for a read query.
        
        Returns:
            Selected Replica, or None if no healthy replicas
        """
        healthy = self.get_healthy_replicas()
        
        if not healthy:
            return None
        
        strategy = self._config.routing
        
        if strategy == "weighted_random":
            return self._select_replica_weighted_random(healthy)
        elif strategy == "round_robin":
            return self._select_replica_round_robin(healthy)
        elif strategy == "least_connections":
            return self._select_replica_least_connections(healthy)
        else:
            return random.choice(healthy)
    
    async def get_read_connection(self) -> Any:
        """Get a connection for read queries.
        
        Selects a healthy replica and returns a connection.
        Falls back to primary if no replicas available.
        
        Returns:
            Database connection (from replica or primary)
        
        Raises:
            ReplicaUnavailableError: If no replicas or primary available
        """
        replica = self.select_replica()
        
        if replica:
            name = replica.name or replica.url
            pool = self._replica_pools.get(name)
            
            if pool:
                self._stats.replica_requests += 1
                self._replica_stats[name].record_request()
                
                try:
                    if hasattr(pool, "acquire"):
                        return await pool.acquire()
                except Exception as e:
                    logger.error(f"Failed to get connection from replica '{name}': {e}")
                    self._replica_stats[name].record_failure(str(e))
        
        # Fall back to primary
        if self._config.read_from_primary_on_lag and self._primary_pool:
            self._stats.failovers_to_primary += 1
            logger.warning("Failing over reads to primary (no healthy replicas)")
            
            if hasattr(self._primary_pool, "acquire"):
                return await self._primary_pool.acquire()
        
        # No connections available
        raise ReplicaUnavailableError(
            "No replicas available for read query",
            {name: health.value for name, health in self._replica_health.items()},
        )
    
    async def get_write_connection(self) -> Any:
        """Get a connection for write queries.
        
        Always returns a connection from the primary.
        
        Returns:
            Database connection from primary
        
        Raises:
            Exception: If primary pool not available
        """
        if not self._primary_pool:
            raise ValueError("Primary pool not configured")
        
        self._stats.primary_requests += 1
        
        if hasattr(self._primary_pool, "acquire"):
            return await self._primary_pool.acquire()
        
        raise ValueError("Primary pool does not support acquire()")
    
    def mark_replica_unhealthy(self, name: str) -> None:
        """Manually mark a replica as unhealthy.
        
        Useful when you detect failures at a higher level.
        """
        with self._lock:
            self._replica_health[name] = ReplicaHealth.UNHEALTHY
            if name in self._replica_stats:
                self._replica_stats[name].health = ReplicaHealth.UNHEALTHY
            logger.warning(f"Replica '{name}' manually marked unhealthy")
    
    def mark_replica_healthy(self, name: str) -> None:
        """Manually mark a replica as healthy.
        
        Useful for manual recovery scenarios.
        """
        with self._lock:
            self._replica_health[name] = ReplicaHealth.HEALTHY
            if name in self._replica_stats:
                self._replica_stats[name].health = ReplicaHealth.HEALTHY
            logger.info(f"Replica '{name}' manually marked healthy")
    
    async def add_replica(self, replica: Replica) -> None:
        """Add a new replica at runtime.
        
        Args:
            replica: Replica configuration
        """
        name = replica.name or replica.url
        
        if name in self._replica_pools:
            logger.warning(f"Replica '{name}' already exists")
            return
        
        try:
            if self._create_pool:
                pool = await self._create_pool(replica.url)
                self._replica_pools[name] = pool
                self._replica_health[name] = ReplicaHealth.UNKNOWN
                self._replica_stats[name] = ReplicaStats(name=name)
                self._stats.replicas[name] = self._replica_stats[name]
                self._config.replicas.append(replica)
                logger.info(f"Added replica '{name}'")
        except Exception as e:
            logger.error(f"Failed to add replica '{name}': {e}")
            raise
    
    async def remove_replica(self, name: str) -> None:
        """Remove a replica at runtime.
        
        Args:
            name: Replica name to remove
        """
        pool = self._replica_pools.pop(name, None)
        
        if pool:
            try:
                if hasattr(pool, "close"):
                    await pool.close()
            except Exception as e:
                logger.error(f"Error closing pool for replica '{name}': {e}")
        
        self._replica_health.pop(name, None)
        self._replica_stats.pop(name, None)
        self._stats.replicas.pop(name, None)
        
        # Remove from config
        self._config.replicas = [
            r for r in self._config.replicas
            if (r.name or r.url) != name
        ]
        
        logger.info(f"Removed replica '{name}'")


# Convenience functions

def simple_replicas(*urls: str) -> ReplicaConfig:
    """Create a simple replica configuration from URLs.
    
    Args:
        *urls: Replica URLs
    
    Returns:
        ReplicaConfig with equal weights
    
    Example:
        config = simple_replicas(
            "postgresql://replica1/db",
            "postgresql://replica2/db",
        )
    """
    return ReplicaConfig(
        replicas=[Replica(url) for url in urls],
    )


def weighted_replicas(url_weights: Dict[str, int]) -> ReplicaConfig:
    """Create a weighted replica configuration.
    
    Args:
        url_weights: Dict of URL to weight
    
    Returns:
        ReplicaConfig with specified weights
    
    Example:
        config = weighted_replicas({
            "postgresql://primary-replica/db": 3,
            "postgresql://backup-replica/db": 1,
        })
    """
    return ReplicaConfig(
        replicas=[
            Replica(url, weight=weight)
            for url, weight in url_weights.items()
        ],
    )

