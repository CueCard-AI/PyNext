"""
PyNext Go Bridge - Health Status Types.

Defines data classes for health check responses from the Go bridge.

Usage:
    health = bridge.health()
    
    if health.status == "healthy":
        print("All good!")
    elif health.status == "degraded":
        print(f"Warning: {health.primary.error}")
    else:
        print("Database is down!")
    
    # Pool statistics
    print(f"Active connections: {health.pool.active_conns}")
    print(f"Idle connections: {health.pool.idle_conns}")
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class ConnectionHealth:
    """
    Health status of a single database connection.
    
    Attributes:
        url: Connection URL (masked for security)
        status: "ok", "degraded", or "down"
        latency_ms: Last ping latency in milliseconds
        error: Error message if not ok
    """
    url: str
    status: str
    latency_ms: float
    error: str = ""
    
    @property
    def is_ok(self) -> bool:
        """True if connection is healthy."""
        return self.status == "ok"
    
    @property
    def is_degraded(self) -> bool:
        """True if connection is degraded but working."""
        return self.status == "degraded"
    
    @property
    def is_down(self) -> bool:
        """True if connection is down."""
        return self.status == "down"
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConnectionHealth:
        """Create from dictionary (Go response)."""
        return cls(
            url=data.get("url", ""),
            status=data.get("status", "unknown"),
            latency_ms=data.get("latency_ms", 0.0),
            error=data.get("error", ""),
        )


@dataclass
class PoolHealth:
    """
    Connection pool statistics.
    
    Attributes:
        total_conns: Total connections in pool
        idle_conns: Idle (available) connections
        active_conns: Currently in-use connections
        waiting_reqs: Requests waiting for a connection
        avg_wait_ms: Average wait time for a connection
        max_wait_ms: Maximum wait time observed
    """
    total_conns: int
    idle_conns: int
    active_conns: int
    waiting_reqs: int = 0
    avg_wait_ms: float = 0.0
    max_wait_ms: float = 0.0
    
    @property
    def utilization(self) -> float:
        """Pool utilization as a percentage (0-100)."""
        if self.total_conns == 0:
            return 0.0
        return (self.active_conns / self.total_conns) * 100
    
    @property
    def is_exhausted(self) -> bool:
        """True if pool is at capacity with waiters."""
        return self.idle_conns == 0 and self.waiting_reqs > 0
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PoolHealth:
        """Create from dictionary (Go response)."""
        return cls(
            total_conns=data.get("total_conns", 0),
            idle_conns=data.get("idle_conns", 0),
            active_conns=data.get("active_conns", 0),
            waiting_reqs=data.get("waiting_reqs", 0),
            avg_wait_ms=data.get("avg_wait_ms", 0.0),
            max_wait_ms=data.get("max_wait_ms", 0.0),
        )


@dataclass
class HealthStatus:
    """
    Overall health status of the Go bridge.
    
    Attributes:
        status: "healthy", "degraded", or "unhealthy"
        primary: Primary connection health
        replicas: List of replica health (if configured)
        pool: Connection pool statistics
        timestamp: When this health check was performed
    """
    status: str
    primary: ConnectionHealth | None
    replicas: list[ConnectionHealth]
    pool: PoolHealth
    timestamp: datetime
    
    @property
    def is_healthy(self) -> bool:
        """True if overall status is healthy."""
        return self.status == "healthy"
    
    @property
    def is_degraded(self) -> bool:
        """True if overall status is degraded."""
        return self.status == "degraded"
    
    @property
    def is_unhealthy(self) -> bool:
        """True if overall status is unhealthy."""
        return self.status == "unhealthy"
    
    @property
    def has_replicas(self) -> bool:
        """True if replicas are configured."""
        return len(self.replicas) > 0
    
    @property
    def healthy_replicas(self) -> list[ConnectionHealth]:
        """List of healthy replicas."""
        return [r for r in self.replicas if r.is_ok]
    
    def summary(self) -> str:
        """
        Get a human-readable summary.
        
        Returns:
            Status summary string
        """
        parts = [f"Status: {self.status}"]
        
        if self.primary:
            parts.append(f"Primary: {self.primary.status} ({self.primary.latency_ms:.1f}ms)")
        
        if self.replicas:
            healthy = len(self.healthy_replicas)
            total = len(self.replicas)
            parts.append(f"Replicas: {healthy}/{total} healthy")
        
        parts.append(
            f"Pool: {self.pool.active_conns}/{self.pool.total_conns} active"
        )
        
        return " | ".join(parts)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HealthStatus:
        """Create from dictionary (Go response)."""
        primary = None
        if data.get("primary"):
            primary = ConnectionHealth.from_dict(data["primary"])
        
        replicas = []
        for r in data.get("replicas", []):
            replicas.append(ConnectionHealth.from_dict(r))
        
        pool = PoolHealth.from_dict(data.get("pool", {}))
        
        # Parse timestamp
        timestamp_str = data.get("timestamp", "")
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            timestamp = datetime.now()
        
        return cls(
            status=data.get("status", "unknown"),
            primary=primary,
            replicas=replicas,
            pool=pool,
            timestamp=timestamp,
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        result: dict[str, Any] = {
            "status": self.status,
            "timestamp": self.timestamp.isoformat(),
            "pool": {
                "total_conns": self.pool.total_conns,
                "idle_conns": self.pool.idle_conns,
                "active_conns": self.pool.active_conns,
                "waiting_reqs": self.pool.waiting_reqs,
                "avg_wait_ms": self.pool.avg_wait_ms,
                "max_wait_ms": self.pool.max_wait_ms,
            },
        }
        
        if self.primary:
            result["primary"] = {
                "url": self.primary.url,
                "status": self.primary.status,
                "latency_ms": self.primary.latency_ms,
                "error": self.primary.error,
            }
        
        if self.replicas:
            result["replicas"] = [
                {
                    "url": r.url,
                    "status": r.status,
                    "latency_ms": r.latency_ms,
                    "error": r.error,
                }
                for r in self.replicas
            ]
        
        return result

