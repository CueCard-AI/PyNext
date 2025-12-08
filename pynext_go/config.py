"""
PyNext Go Bridge - Configuration.

Defines BridgeConfig and related settings for the Go bridge.

Design Principles:
    - Sensible defaults that work out of the box
    - Every option has clear documentation
    - Validation happens at config creation time
    - JSON-serializable for Go bridge communication
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any
import json

# =============================================================================
# Default Values
# =============================================================================

DEFAULT_POOL_MIN = 2
DEFAULT_POOL_MAX = 10
DEFAULT_POOL_IDLE_TIME = 300  # 5 minutes
DEFAULT_POOL_LIFETIME = 3600  # 1 hour
DEFAULT_HEALTH_INTERVAL = 30  # seconds
DEFAULT_QUERY_TIMEOUT = 30000  # 30 seconds in ms
DEFAULT_STATEMENT_CACHE = 256
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_BACKOFF = 100  # ms


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class BridgeConfig:
    """
    Configuration for the Go bridge.
    
    All settings have sensible defaults for production use.
    
    Attributes:
        primary: Primary database connection string (required)
        replicas: List of read replica connection strings
        pool_min_size: Minimum connections to maintain
        pool_max_size: Maximum connections allowed
        pool_max_idle_time: Seconds before idle connection is closed
        pool_max_lifetime: Maximum lifetime of any connection in seconds
        pool_health_interval: Seconds between health checks
        query_timeout: Default query timeout in milliseconds
        statement_cache: Size of prepared statement cache
        max_retries: Maximum retry attempts for failed queries
        retry_backoff_ms: Initial backoff delay in milliseconds
        enable_arrow: Use Arrow format for results (faster)
        enable_prepared: Use prepared statements (faster)
        enable_batch: Enable batch optimizations
        debug: Enable debug logging in Go
        
    Example:
        config = BridgeConfig(
            primary="postgresql://user:pass@localhost:5432/mydb",
            pool_max_size=20,
            query_timeout=10000,  # 10 seconds
        )
    """
    # Required
    primary: str
    
    # Optional - replicas
    replicas: list[str] = field(default_factory=list)
    
    # Pool settings
    pool_min_size: int = DEFAULT_POOL_MIN
    pool_max_size: int = DEFAULT_POOL_MAX
    pool_max_idle_time: int = DEFAULT_POOL_IDLE_TIME
    pool_max_lifetime: int = DEFAULT_POOL_LIFETIME
    pool_health_interval: int = DEFAULT_HEALTH_INTERVAL
    
    # Query settings
    query_timeout: int = DEFAULT_QUERY_TIMEOUT
    statement_cache: int = DEFAULT_STATEMENT_CACHE
    max_retries: int = DEFAULT_MAX_RETRIES
    retry_backoff_ms: int = DEFAULT_RETRY_BACKOFF
    
    # Feature flags
    enable_arrow: bool = True
    enable_prepared: bool = True
    enable_batch: bool = True
    debug: bool = False
    
    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """
        Validate the configuration.
        
        Raises:
            ValueError: If any setting is invalid
        """
        if not self.primary:
            raise ValueError("primary connection string is required")
        
        if not self.primary.startswith(("postgresql://", "postgres://")):
            raise ValueError(
                f"primary must be a PostgreSQL connection string, got: {self.primary[:20]}..."
            )
        
        if self.pool_min_size < 0:
            raise ValueError(f"pool_min_size must be >= 0, got {self.pool_min_size}")
        
        if self.pool_max_size < 1:
            raise ValueError(f"pool_max_size must be >= 1, got {self.pool_max_size}")
        
        if self.pool_min_size > self.pool_max_size:
            raise ValueError(
                f"pool_min_size ({self.pool_min_size}) cannot exceed "
                f"pool_max_size ({self.pool_max_size})"
            )
        
        if self.query_timeout < 0:
            raise ValueError(f"query_timeout must be >= 0, got {self.query_timeout}")
        
        if self.statement_cache < 0:
            raise ValueError(f"statement_cache must be >= 0, got {self.statement_cache}")
        
        if self.max_retries < 0:
            raise ValueError(f"max_retries must be >= 0, got {self.max_retries}")
        
        for i, replica in enumerate(self.replicas):
            if not replica.startswith(("postgresql://", "postgres://")):
                raise ValueError(
                    f"replica[{i}] must be a PostgreSQL connection string"
                )
    
    def to_json(self) -> str:
        """
        Serialize to JSON for Go bridge.
        
        Returns:
            JSON string with Go-compatible field names
        """
        return json.dumps(self.to_dict())
    
    def to_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary with Go-compatible field names.
        
        The Go bridge expects snake_case field names matching
        the JSON tags in pkg/bridge/types.go.
        """
        return {
            "primary": self.primary,
            "replicas": self.replicas,
            "pool_min_size": self.pool_min_size,
            "pool_max_size": self.pool_max_size,
            "pool_max_idle_time": self.pool_max_idle_time,
            "pool_max_lifetime": self.pool_max_lifetime,
            "pool_health_interval": self.pool_health_interval,
            "query_timeout": self.query_timeout,
            "statement_cache": self.statement_cache,
            "max_retries": self.max_retries,
            "retry_backoff_ms": self.retry_backoff_ms,
            "enable_arrow": self.enable_arrow,
            "enable_prepared": self.enable_prepared,
            "enable_batch": self.enable_batch,
            "debug": self.debug,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BridgeConfig:
        """
        Create config from dictionary.
        
        Args:
            data: Dictionary with config values
            
        Returns:
            BridgeConfig instance
        """
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> BridgeConfig:
        """
        Create config from JSON string.
        
        Args:
            json_str: JSON-encoded config
            
        Returns:
            BridgeConfig instance
        """
        return cls.from_dict(json.loads(json_str))
    
    def with_pool(
        self,
        min_size: int | None = None,
        max_size: int | None = None,
        max_idle_time: int | None = None,
        max_lifetime: int | None = None,
    ) -> BridgeConfig:
        """
        Create a copy with modified pool settings.
        
        Args:
            min_size: New minimum pool size
            max_size: New maximum pool size
            max_idle_time: New idle timeout in seconds
            max_lifetime: New max lifetime in seconds
            
        Returns:
            New BridgeConfig with updated settings
        """
        return BridgeConfig(
            primary=self.primary,
            replicas=self.replicas.copy(),
            pool_min_size=min_size if min_size is not None else self.pool_min_size,
            pool_max_size=max_size if max_size is not None else self.pool_max_size,
            pool_max_idle_time=max_idle_time if max_idle_time is not None else self.pool_max_idle_time,
            pool_max_lifetime=max_lifetime if max_lifetime is not None else self.pool_max_lifetime,
            pool_health_interval=self.pool_health_interval,
            query_timeout=self.query_timeout,
            statement_cache=self.statement_cache,
            max_retries=self.max_retries,
            retry_backoff_ms=self.retry_backoff_ms,
            enable_arrow=self.enable_arrow,
            enable_prepared=self.enable_prepared,
            enable_batch=self.enable_batch,
            debug=self.debug,
        )
    
    def with_timeout(self, timeout_ms: int) -> BridgeConfig:
        """
        Create a copy with modified timeout.
        
        Args:
            timeout_ms: New query timeout in milliseconds
            
        Returns:
            New BridgeConfig with updated timeout
        """
        return BridgeConfig(
            primary=self.primary,
            replicas=self.replicas.copy(),
            pool_min_size=self.pool_min_size,
            pool_max_size=self.pool_max_size,
            pool_max_idle_time=self.pool_max_idle_time,
            pool_max_lifetime=self.pool_max_lifetime,
            pool_health_interval=self.pool_health_interval,
            query_timeout=timeout_ms,
            statement_cache=self.statement_cache,
            max_retries=self.max_retries,
            retry_backoff_ms=self.retry_backoff_ms,
            enable_arrow=self.enable_arrow,
            enable_prepared=self.enable_prepared,
            enable_batch=self.enable_batch,
            debug=self.debug,
        )


# =============================================================================
# Preset Configurations
# =============================================================================

def development_config(primary: str) -> BridgeConfig:
    """
    Configuration optimized for development.
    
    - Small pool (faster startup)
    - Debug logging enabled
    - Shorter timeouts
    """
    return BridgeConfig(
        primary=primary,
        pool_min_size=1,
        pool_max_size=5,
        query_timeout=5000,  # 5 seconds
        debug=True,
    )


def production_config(primary: str, replicas: list[str] | None = None) -> BridgeConfig:
    """
    Configuration optimized for production.
    
    - Larger pool
    - Read replicas for scaling
    - Longer timeouts
    """
    return BridgeConfig(
        primary=primary,
        replicas=replicas or [],
        pool_min_size=5,
        pool_max_size=20,
        query_timeout=30000,  # 30 seconds
        debug=False,
    )


def high_throughput_config(primary: str, replicas: list[str] | None = None) -> BridgeConfig:
    """
    Configuration for high-throughput workloads.
    
    - Large pool
    - Aggressive prepared statement caching
    - Batch optimizations
    """
    return BridgeConfig(
        primary=primary,
        replicas=replicas or [],
        pool_min_size=10,
        pool_max_size=50,
        statement_cache=1024,
        enable_batch=True,
        debug=False,
    )

