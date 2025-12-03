"""
PyNext Live Queries - Reactive Database Queries.

Queries that automatically update when the underlying data changes.
Dead simple API, hyper-efficient under the hood.

Usage:
    # Basic - Always fresh, auto-updates!
    users = User.live()
    
    # Filtered
    active = User.live().where(status="active")
    
    # With ordering and limit
    recent = Post.live().order_by("-created_at").limit(10)
    
    # Access data
    users()           # Get current value (list)
    users.loading     # Signal[bool] - loading state
    users.error       # Signal[Optional[Exception]]
    users.refetch()   # Manual refetch
    users.stop()      # Stop subscription

How It Works:
    1. LiveQuery extends Signal to hold query results
    2. ChangeDetector monitors for database changes (LISTEN/NOTIFY, Supabase Realtime, polling)
    3. Transport layer sends updates to client (SSE for simple, WebSocket for complex)
    4. UpdateStrategy determines how to apply changes (surgical vs full refresh)
    5. SubscriptionManager coordinates everything server-side
"""

from pynext.db.live.config import (
    LiveQueryConfig,
    TransportType,
    DetectionStrategy,
    UpdateGranularity,
    DEFAULT_CONFIG,
)

from pynext.db.live.query import (
    LiveQuery,
    LiveQueryState,
    live,
)

from pynext.db.live.subscriptions import (
    SubscriptionManager,
    ClientSubscription,
    QueryGroup,
    Subscription,
    get_subscription_manager,
)

from pynext.db.live.triggers import (
    TriggerManager,
    NotifyChannel,
    TriggerConfig,
    get_trigger_manager,
)


async def enable_live_queries(table: str) -> NotifyChannel:
    """
    Enable live queries for a table by creating the NOTIFY trigger.
    
    This creates a PostgreSQL trigger that sends NOTIFY events on
    INSERT, UPDATE, and DELETE operations.
    
    Usage:
        # Enable live queries for users table
        await enable_live_queries("users")
        # Creates: pynext_live_users trigger on INSERT/UPDATE/DELETE
        
        # Now you can use live queries
        users = User.live()  # Will receive real-time updates!
    
    Args:
        table: The table name to enable live queries for
    
    Returns:
        NotifyChannel with trigger metadata
    
    Note:
        If auto_create_triggers is enabled (default), triggers are created
        automatically when you first call User.live(). This function is for
        manual trigger creation or pre-creating triggers at app startup.
    """
    manager = get_trigger_manager()
    return await manager.ensure_trigger(table)


async def disable_live_queries(table: str) -> bool:
    """
    Disable live queries for a table by removing the NOTIFY trigger.
    
    Usage:
        await disable_live_queries("users")
    
    Args:
        table: The table name to disable live queries for
    
    Returns:
        True if trigger was dropped, False if it didn't exist
    """
    manager = get_trigger_manager()
    return await manager.drop_trigger(table)

# Detection strategies
from pynext.db.live.detection import (
    ChangeDetector,
    ChangeEvent,
    ChangeType,
    DetectorRegistry,
    get_detector_registry,
)

from pynext.db.live.detection.postgres import PostgresNotifyDetector
from pynext.db.live.detection.supabase import SupabaseRealtimeDetector
from pynext.db.live.detection.polling import PollingDetector

# Transport layer
from pynext.db.live.transport import (
    Transport,
    TransportMessage,
    TransportState,
    TransportManager,
    get_transport_manager,
)

from pynext.db.live.transport.sse import SSETransport
from pynext.db.live.transport.websocket import WebSocketTransport
from pynext.db.live.transport.selector import TransportSelector

# Update strategies
from pynext.db.live.updates import (
    UpdateStrategy,
    UpdateResult,
    StrategySelector,
)

from pynext.db.live.updates.surgical import SurgicalUpdate
from pynext.db.live.updates.refresh import FullRefresh

__all__ = [
    # Config
    "LiveQueryConfig",
    "TransportType",
    "DetectionStrategy",
    "UpdateGranularity",
    "DEFAULT_CONFIG",
    
    # Core
    "LiveQuery",
    "LiveQueryState",
    "live",
    
    # Subscriptions
    "SubscriptionManager",
    "ClientSubscription",
    "QueryGroup",
    "Subscription",
    "get_subscription_manager",
    
    # Triggers
    "TriggerManager",
    "NotifyChannel",
    "TriggerConfig",
    "get_trigger_manager",
    "enable_live_queries",
    "disable_live_queries",
    
    # Detection
    "ChangeDetector",
    "ChangeEvent",
    "ChangeType",
    "DetectorRegistry",
    "get_detector_registry",
    "PostgresNotifyDetector",
    "SupabaseRealtimeDetector",
    "PollingDetector",
    
    # Transport
    "Transport",
    "TransportMessage",
    "TransportState",
    "TransportManager",
    "get_transport_manager",
    "SSETransport",
    "WebSocketTransport",
    "TransportSelector",
    
    # Updates
    "UpdateStrategy",
    "UpdateResult",
    "StrategySelector",
    "SurgicalUpdate",
    "FullRefresh",
]

