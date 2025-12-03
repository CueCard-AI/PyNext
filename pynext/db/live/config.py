"""
PyNext Live Query Configuration.

Configuration options for live queries with sensible defaults.
Dead simple - just use the defaults, or customize what you need.

Usage:
    # Default config - works great for most cases
    users = User.live()
    
    # Custom config
    from pynext.db.live import LiveQueryConfig
    
    users = User.live(config=LiveQueryConfig(
        poll_interval=5.0,  # Poll every 5 seconds (fallback)
        transport="auto",   # Let PyNext choose SSE vs WebSocket
    ))
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class TransportType(str, Enum):
    """
    How updates are sent from server to client.
    
    - auto: PyNext chooses the best transport (recommended)
    - sse: Server-Sent Events (simpler, unidirectional)
    - websocket: WebSocket (bidirectional, lower latency)
    """
    AUTO = "auto"
    SSE = "sse"
    WEBSOCKET = "websocket"


class DetectionStrategy(str, Enum):
    """
    How database changes are detected.
    
    - auto: Best available (Supabase RT > LISTEN/NOTIFY > Polling)
    - supabase: Use Supabase Realtime only
    - postgres: Use PostgreSQL LISTEN/NOTIFY only
    - polling: Use polling only
    """
    AUTO = "auto"
    SUPABASE = "supabase"
    POSTGRES = "postgres"
    POLLING = "polling"


class UpdateGranularity(str, Enum):
    """
    How changes are applied to the query result.
    
    - auto: PyNext chooses based on query type
    - surgical: Add/update/remove individual items
    - refresh: Re-run entire query
    """
    AUTO = "auto"
    SURGICAL = "surgical"
    REFRESH = "refresh"


@dataclass
class LiveQueryConfig:
    """
    Configuration for a live query.
    
    Most users won't need to customize this - the defaults work great.
    
    Attributes:
        transport: How to send updates (auto, sse, websocket)
        detection: How to detect changes (auto, supabase, postgres, polling)
        granularity: How to apply changes (auto, surgical, refresh)
        poll_interval: Seconds between polls (fallback only)
        batch_updates: Batch multiple updates together
        batch_delay_ms: Delay before sending batched updates
        dedupe_queries: Share results for identical queries
        reconnect: Auto-reconnect on disconnect
        reconnect_delay_ms: Initial reconnect delay
        max_reconnect_attempts: Give up after this many attempts
        initial_fetch: Fetch data immediately on subscribe
        stale_time_ms: Data older than this is considered stale
        cache_results: Cache query results
        optimistic_updates: Apply changes before server confirms
        debug: Enable debug logging
    """
    
    # Transport
    transport: TransportType = TransportType.AUTO
    
    # Detection
    detection: DetectionStrategy = DetectionStrategy.AUTO
    
    # Update granularity
    granularity: UpdateGranularity = UpdateGranularity.AUTO
    
    # Polling (fallback)
    poll_interval: float = 30.0  # seconds
    
    # Batching
    batch_updates: bool = True
    batch_delay_ms: int = 50
    
    # Deduplication
    dedupe_queries: bool = True
    
    # Reconnection
    reconnect: bool = True
    reconnect_delay_ms: int = 1000
    max_reconnect_attempts: int = 10
    
    # Fetching
    initial_fetch: bool = True
    stale_time_ms: int = 0  # 0 = always fresh
    
    # Caching
    cache_results: bool = True
    
    # Optimistic updates
    optimistic_updates: bool = False
    
    # Debug
    debug: bool = False
    
    def merge(self, **overrides: Any) -> "LiveQueryConfig":
        """
        Create a new config with overrides.
        
        Examples:
            new_config = config.merge(poll_interval=5.0)
        """
        from dataclasses import asdict
        current = asdict(self)
        current.update(overrides)
        return LiveQueryConfig(**current)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization."""
        from dataclasses import asdict
        result = asdict(self)
        # Convert enums to strings
        result["transport"] = self.transport.value
        result["detection"] = self.detection.value
        result["granularity"] = self.granularity.value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LiveQueryConfig":
        """Create config from dict."""
        # Handle enum conversions
        if "transport" in data and isinstance(data["transport"], str):
            data["transport"] = TransportType(data["transport"])
        if "detection" in data and isinstance(data["detection"], str):
            data["detection"] = DetectionStrategy(data["detection"])
        if "granularity" in data and isinstance(data["granularity"], str):
            data["granularity"] = UpdateGranularity(data["granularity"])
        
        # Filter to only known fields
        from dataclasses import fields
        known_fields = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in data.items() if k in known_fields}
        
        return cls(**filtered)
    
    # Aliases for backwards compatibility
    @property
    def debounce_ms(self) -> int:
        """Alias for batch_delay_ms."""
        return self.batch_delay_ms
    
    @property
    def update_granularity(self) -> UpdateGranularity:
        """Alias for granularity."""
        return self.granularity


# Default configuration - works great for most cases
DEFAULT_CONFIG = LiveQueryConfig()


@dataclass
class QuerySignature:
    """
    Unique identifier for a query.
    
    Used to deduplicate identical queries across clients.
    """
    table: str
    where_clauses: tuple = field(default_factory=tuple)
    order_by: Optional[str] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    fields: tuple = field(default_factory=tuple)
    joins: tuple = field(default_factory=tuple)
    aggregations: tuple = field(default_factory=tuple)
    
    def __hash__(self) -> int:
        return hash((
            self.table,
            self.where_clauses,
            self.order_by,
            self.limit,
            self.offset,
            self.fields,
            self.joins,
            self.aggregations,
        ))
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, QuerySignature):
            return False
        return (
            self.table == other.table
            and self.where_clauses == other.where_clauses
            and self.order_by == other.order_by
            and self.limit == other.limit
            and self.offset == other.offset
            and self.fields == other.fields
            and self.joins == other.joins
            and self.aggregations == other.aggregations
        )
    
    @property
    def hash(self) -> int:
        """Get hash value for the signature."""
        return self.__hash__()
    
    @property
    def is_simple(self) -> bool:
        """
        Check if this is a simple query (no filters, ordering, limits, joins).
        
        Simple queries can use surgical updates more effectively.
        """
        return (
            not self.where_clauses
            and self.order_by is None
            and self.limit is None
            and self.offset is None
            and not self.joins
            and not self.aggregations
        )
    
    @property
    def has_ordering(self) -> bool:
        """Check if query has ordering."""
        return self.order_by is not None
    
    @property
    def has_limit(self) -> bool:
        """Check if query has a limit."""
        return self.limit is not None
    
    @property
    def has_filters(self) -> bool:
        """Check if query has WHERE clauses."""
        return bool(self.where_clauses)
    
    @property
    def has_joins(self) -> bool:
        """Check if query has joins."""
        return bool(self.joins)
    
    @property
    def has_aggregations(self) -> bool:
        """Check if query has aggregations."""
        return bool(self.aggregations)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization."""
        return {
            "table": self.table,
            "where_clauses": list(self.where_clauses),
            "order_by": self.order_by,
            "limit": self.limit,
            "offset": self.offset,
            "fields": list(self.fields),
            "joins": list(self.joins),
            "aggregations": list(self.aggregations),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QuerySignature":
        """Create from dict."""
        return cls(
            table=data["table"],
            where_clauses=tuple(data.get("where_clauses", [])),
            order_by=data.get("order_by"),
            limit=data.get("limit"),
            offset=data.get("offset"),
            fields=tuple(data.get("fields", [])),
            joins=tuple(data.get("joins", [])),
            aggregations=tuple(data.get("aggregations", [])),
        )


@dataclass
class ServerConfig:
    """
    Server-side configuration for live queries.
    
    Usually set once at application startup.
    """
    
    # SSE endpoint
    sse_path: str = "/_pynext/live/sse"
    
    # WebSocket endpoint
    ws_path: str = "/_pynext/live/ws"
    
    # Maximum concurrent subscriptions per client
    max_subscriptions_per_client: int = 100
    
    # Maximum clients
    max_clients: int = 10000
    
    # Heartbeat interval (ms)
    heartbeat_interval_ms: int = 30000
    
    # Enable PostgreSQL LISTEN/NOTIFY
    enable_postgres_notify: bool = True
    
    # Enable Supabase Realtime
    enable_supabase_realtime: bool = True
    
    # Auto-create triggers for live queries
    auto_create_triggers: bool = True
    
    # Trigger channel prefix
    trigger_prefix: str = "pynext_live_"
    
    # Query result batch size
    batch_size: int = 1000
    
    # Memory limit per subscription (bytes)
    memory_limit_per_sub: int = 10 * 1024 * 1024  # 10MB
    
    # Enable debug mode
    debug: bool = False


# Default server config
DEFAULT_SERVER_CONFIG = ServerConfig()


# Global server config (set at startup)
_server_config: Optional[ServerConfig] = None


def configure_live_queries(config: Optional[ServerConfig] = None) -> ServerConfig:
    """
    Configure the live query server.
    
    Call once at application startup.
    
    Examples:
        from pynext.db.live import configure_live_queries, ServerConfig
        
        configure_live_queries(ServerConfig(
            max_clients=5000,
            debug=True,
        ))
    """
    global _server_config
    _server_config = config or ServerConfig()
    return _server_config


def get_server_config() -> ServerConfig:
    """Get the current server configuration."""
    global _server_config
    if _server_config is None:
        _server_config = ServerConfig()
    return _server_config

