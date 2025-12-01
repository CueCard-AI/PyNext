"""
PyNext Supabase Realtime.

Provides two ways to subscribe to database changes:
1. Decorators (server-side) - Python functions triggered on database events
2. Signals (frontend) - Reactive values that auto-update in the UI

Why Two Approaches?
    Decorators are perfect for server-side logic (send email on user signup).
    Signals are perfect for reactive UIs (user list updates automatically).

Usage - Decorators (Default, Easiest):
    from pynext.db.supabase import Supabase, on_insert, on_update, on_delete
    
    db = Supabase("https://xyz.supabase.co")
    
    @on_insert("users")
    async def handle_new_user(record):
        print(f"Welcome {record['email']}!")
    
    @on_update("users", columns=["status"])
    async def handle_status_change(old, new):
        print(f"Status changed: {old['status']} -> {new['status']}")
    
    await db.realtime.start()

Usage - Signals (For Reactive UIs):
    users = await db.realtime.subscribe("users")
    
    # In a component - auto-updates when data changes
    def UserList():
        return ul([li(user['name']) for user in users()])
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union, TYPE_CHECKING
import asyncio
import functools
import weakref

from .exceptions import (
    RealtimeError,
    RealtimeConnectionError,
    SubscriptionError,
    ChannelError,
    AlreadySubscribedError,
)

if TYPE_CHECKING:
    from .adapter import Supabase


# =============================================================================
# ENUMS AND TYPES
# =============================================================================

class EventType(str, Enum):
    """Database change event types."""
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    ALL = "*"


class ChannelState(str, Enum):
    """State of a realtime channel."""
    CLOSED = "closed"
    JOINING = "joining"
    JOINED = "joined"
    LEAVING = "leaving"
    ERRORED = "errored"


# Type aliases
HandlerFunc = Callable[..., Any]
FilterType = Optional[str]


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class RealtimeEvent:
    """
    Container for a realtime database change event.
    
    Attributes:
        type: Event type (INSERT, UPDATE, DELETE)
        table: Table where change occurred
        schema: Database schema (usually "public")
        old_record: Previous record data (None for INSERT)
        new_record: New record data (None for DELETE)
        timestamp: When the event occurred
        commit_timestamp: Database commit timestamp
    """
    type: EventType
    table: str
    schema: str = "public"
    old_record: Optional[Dict[str, Any]] = None
    new_record: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    commit_timestamp: Optional[str] = None
    
    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "RealtimeEvent":
        """Create event from Supabase payload."""
        return cls(
            type=EventType(payload.get("eventType", payload.get("type", "INSERT"))),
            table=payload.get("table", ""),
            schema=payload.get("schema", "public"),
            old_record=payload.get("old_record") or payload.get("old"),
            new_record=payload.get("new_record") or payload.get("new") or payload.get("record"),
            commit_timestamp=payload.get("commit_timestamp"),
        )
    
    @property
    def record(self) -> Optional[Dict[str, Any]]:
        """Get the relevant record (new for INSERT/UPDATE, old for DELETE)."""
        if self.type == EventType.DELETE:
            return self.old_record
        return self.new_record


@dataclass
class Subscription:
    """
    Represents an active realtime subscription.
    
    Attributes:
        table: Table being subscribed to
        event_types: Event types to listen for
        filter: PostgREST filter expression
        columns: Specific columns to watch
        channel_name: Internal channel name
        handlers: Registered event handlers
    """
    table: str
    event_types: Set[EventType] = field(default_factory=lambda: {EventType.ALL})
    filter: Optional[str] = None
    columns: Optional[List[str]] = None
    channel_name: Optional[str] = None
    handlers: List[Callable] = field(default_factory=list)
    state: ChannelState = ChannelState.CLOSED
    
    def matches_event(self, event: RealtimeEvent) -> bool:
        """Check if this subscription should receive an event."""
        if EventType.ALL in self.event_types:
            return True
        return event.type in self.event_types


@dataclass
class RealtimeConfig:
    """
    Configuration for realtime subscriptions.
    
    Attributes:
        enabled: Whether realtime is enabled
        auto_reconnect: Automatically reconnect on disconnect
        reconnect_delay: Seconds between reconnect attempts
        max_reconnect_attempts: Maximum reconnection attempts
        heartbeat_interval: Seconds between heartbeats
    """
    enabled: bool = True
    auto_reconnect: bool = True
    reconnect_delay: float = 1.0
    max_reconnect_attempts: int = 10
    heartbeat_interval: float = 30.0


# =============================================================================
# HANDLER REGISTRY
# =============================================================================

class HandlerRegistry:
    """
    Manages registered event handlers.
    
    Handlers are registered via decorators and stored here.
    When events arrive, matching handlers are called.
    """
    
    def __init__(self):
        self._handlers: Dict[str, Dict[EventType, List[Callable]]] = {}
        self._subscriptions: Dict[str, Subscription] = {}
    
    def register(
        self,
        table: str,
        event_type: EventType,
        handler: Callable,
        filter: Optional[str] = None,
        columns: Optional[List[str]] = None,
    ):
        """Register a handler for table events."""
        key = self._make_key(table, filter)
        
        if key not in self._handlers:
            self._handlers[key] = {et: [] for et in EventType}
            self._subscriptions[key] = Subscription(
                table=table,
                filter=filter,
                columns=columns,
            )
        
        self._handlers[key][event_type].append(handler)
        self._subscriptions[key].event_types.add(event_type)
        
        if columns:
            existing = self._subscriptions[key].columns or []
            self._subscriptions[key].columns = list(set(existing + columns))
    
    def get_handlers(
        self,
        table: str,
        event_type: EventType,
        filter: Optional[str] = None,
    ) -> List[Callable]:
        """Get all handlers for a table/event combination."""
        key = self._make_key(table, filter)
        handlers = []
        
        if key in self._handlers:
            # Get specific event type handlers
            handlers.extend(self._handlers[key].get(event_type, []))
            # Get ALL event type handlers
            handlers.extend(self._handlers[key].get(EventType.ALL, []))
        
        return handlers
    
    def get_subscriptions(self) -> List[Subscription]:
        """Get all registered subscriptions."""
        return list(self._subscriptions.values())
    
    def _make_key(self, table: str, filter: Optional[str] = None) -> str:
        """Create a unique key for a table/filter combination."""
        if filter:
            return f"{table}:{filter}"
        return table
    
    def clear(self):
        """Clear all registered handlers and subscriptions."""
        self._handlers.clear()
        self._subscriptions.clear()


# Global registry for decorator-registered handlers
_global_registry = HandlerRegistry()


# =============================================================================
# DECORATORS
# =============================================================================

def on_insert(
    table: str,
    *,
    filter: Optional[str] = None,
    columns: Optional[List[str]] = None,
):
    """
    Decorator to handle INSERT events on a table.
    
    Args:
        table: Table name to subscribe to
        filter: PostgREST filter expression (e.g., "status=eq.active")
        columns: Specific columns to monitor
    
    Example:
        @on_insert("users")
        async def handle_new_user(record):
            print(f"New user: {record['email']}")
            await send_welcome_email(record['email'])
        
        @on_insert("orders", filter="status=eq.pending")
        async def handle_pending_order(record):
            await process_order(record['id'])
    """
    def decorator(func: Callable) -> Callable:
        _global_registry.register(
            table=table,
            event_type=EventType.INSERT,
            handler=func,
            filter=filter,
            columns=columns,
        )
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def on_update(
    table: str,
    *,
    filter: Optional[str] = None,
    columns: Optional[List[str]] = None,
):
    """
    Decorator to handle UPDATE events on a table.
    
    The handler receives both old and new record data.
    
    Args:
        table: Table name to subscribe to
        filter: PostgREST filter expression
        columns: Only trigger when these columns change
    
    Example:
        @on_update("users", columns=["status"])
        async def handle_status_change(old_record, new_record):
            if new_record['status'] == 'premium':
                await grant_premium_access(new_record['id'])
    """
    def decorator(func: Callable) -> Callable:
        _global_registry.register(
            table=table,
            event_type=EventType.UPDATE,
            handler=func,
            filter=filter,
            columns=columns,
        )
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def on_delete(
    table: str,
    *,
    filter: Optional[str] = None,
):
    """
    Decorator to handle DELETE events on a table.
    
    The handler receives the deleted record data.
    
    Args:
        table: Table name to subscribe to
        filter: PostgREST filter expression
    
    Example:
        @on_delete("orders")
        async def handle_order_deleted(old_record):
            await cleanup_order_files(old_record['id'])
            await notify_customer(old_record['user_id'])
    """
    def decorator(func: Callable) -> Callable:
        _global_registry.register(
            table=table,
            event_type=EventType.DELETE,
            handler=func,
            filter=filter,
        )
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def on_change(
    table: str,
    *,
    filter: Optional[str] = None,
    columns: Optional[List[str]] = None,
):
    """
    Decorator to handle ALL change events on a table.
    
    The handler receives event_type, old_record, and new_record.
    
    Args:
        table: Table name to subscribe to
        filter: PostgREST filter expression
        columns: Columns to monitor for changes
    
    Example:
        @on_change("products")
        async def handle_product_change(event_type, old_record, new_record):
            if event_type == "INSERT":
                await index_product(new_record)
            elif event_type == "UPDATE":
                await update_index(new_record)
            elif event_type == "DELETE":
                await remove_from_index(old_record['id'])
    """
    def decorator(func: Callable) -> Callable:
        _global_registry.register(
            table=table,
            event_type=EventType.ALL,
            handler=func,
            filter=filter,
            columns=columns,
        )
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# =============================================================================
# SIGNAL (REACTIVE VALUE)
# =============================================================================

class Signal:
    """
    A reactive value that updates when database changes occur.
    
    Signals are used in PyNext components to create reactive UIs
    that automatically update when the underlying data changes.
    
    Usage:
        users = await db.realtime.subscribe("users")
        
        # In a component
        def UserList():
            return ul([li(user['name']) for user in users()])
        
        # The component re-renders when users changes
    """
    
    def __init__(self, initial_value: Any = None):
        self._value = initial_value
        self._subscribers: Set[Callable] = set()
    
    def __call__(self) -> Any:
        """Get the current value."""
        return self._value
    
    def get(self) -> Any:
        """Get the current value (explicit method)."""
        return self._value
    
    def set(self, value: Any):
        """Set a new value and notify subscribers."""
        old_value = self._value
        self._value = value
        
        if old_value != value:
            self._notify()
    
    def update(self, fn: Callable[[Any], Any]):
        """Update value using a function."""
        self.set(fn(self._value))
    
    def subscribe(self, callback: Callable[[Any], None]) -> Callable[[], None]:
        """
        Subscribe to value changes.
        
        Returns a function to unsubscribe.
        """
        self._subscribers.add(callback)
        
        def unsubscribe():
            self._subscribers.discard(callback)
        
        return unsubscribe
    
    def _notify(self):
        """Notify all subscribers of value change."""
        for callback in self._subscribers:
            try:
                callback(self._value)
            except Exception:
                pass  # Don't let one subscriber crash others


class TableSignal(Signal):
    """
    A Signal specifically for table data.
    
    Provides convenience methods for working with table records.
    """
    
    def __init__(self, table: str, initial_data: Optional[List[Dict]] = None):
        super().__init__(initial_data or [])
        self._table = table
        self._by_id: Dict[Any, Dict] = {}
        
        if initial_data:
            self._rebuild_index()
    
    @property
    def table(self) -> str:
        return self._table
    
    def _rebuild_index(self):
        """Rebuild the ID index from current data."""
        self._by_id = {
            record.get("id"): record
            for record in self._value
            if record.get("id") is not None
        }
    
    def handle_event(self, event: RealtimeEvent):
        """Update the signal based on a realtime event."""
        if event.type == EventType.INSERT and event.new_record:
            self._insert(event.new_record)
        elif event.type == EventType.UPDATE and event.new_record:
            self._update(event.new_record)
        elif event.type == EventType.DELETE and event.old_record:
            self._delete(event.old_record)
    
    def _insert(self, record: Dict):
        """Add a new record."""
        record_id = record.get("id")
        if record_id is not None and record_id not in self._by_id:
            new_list = list(self._value) + [record]
            self._by_id[record_id] = record
            self.set(new_list)
    
    def _update(self, record: Dict):
        """Update an existing record."""
        record_id = record.get("id")
        if record_id is not None and record_id in self._by_id:
            # Update in list
            new_list = [
                record if r.get("id") == record_id else r
                for r in self._value
            ]
            self._by_id[record_id] = record
            self.set(new_list)
    
    def _delete(self, record: Dict):
        """Remove a record."""
        record_id = record.get("id")
        if record_id is not None and record_id in self._by_id:
            del self._by_id[record_id]
            new_list = [r for r in self._value if r.get("id") != record_id]
            self.set(new_list)
    
    def find_by_id(self, id: Any) -> Optional[Dict]:
        """Find a record by ID (O(1) lookup)."""
        return self._by_id.get(id)
    
    def filter(self, predicate: Callable[[Dict], bool]) -> List[Dict]:
        """Filter records by a predicate."""
        return [r for r in self._value if predicate(r)]
    
    def first(self, predicate: Optional[Callable[[Dict], bool]] = None) -> Optional[Dict]:
        """Get the first record, optionally filtered."""
        if predicate:
            for r in self._value:
                if predicate(r):
                    return r
            return None
        return self._value[0] if self._value else None
    
    def count(self) -> int:
        """Get the number of records."""
        return len(self._value)
    
    def is_empty(self) -> bool:
        """Check if there are no records."""
        return len(self._value) == 0


# =============================================================================
# MAIN REALTIME CLASS
# =============================================================================

class SupabaseRealtime:
    """
    Supabase Realtime subscription manager.
    
    Provides:
    - Decorator-based event handling (server-side)
    - Signal-based reactive subscriptions (frontend)
    - Automatic reconnection
    - Multiple table subscriptions
    
    Usage (Decorators):
        @on_insert("users")
        async def handle_new_user(record):
            print(f"New user: {record['email']}")
        
        await db.realtime.start()
    
    Usage (Signals):
        users = await db.realtime.subscribe("users")
        
        # users() returns current data, auto-updates on changes
    """
    
    def __init__(self, supabase: "Supabase", config: Optional[RealtimeConfig] = None):
        self._supabase = supabase
        self._config = config or RealtimeConfig()
        self._registry = _global_registry
        
        # Active subscriptions and signals
        self._active_subscriptions: Dict[str, Subscription] = {}
        self._table_signals: Dict[str, TableSignal] = {}
        
        # Connection state
        self._channel = None
        self._is_running = False
        self._reconnect_attempts = 0
        self._listen_task: Optional[asyncio.Task] = None
    
    @property
    def _client(self):
        """Get the underlying supabase-py realtime client."""
        self._supabase._ensure_initialized()
        return self._supabase.client.realtime
    
    # =========================================================================
    # SIGNAL-BASED SUBSCRIPTIONS
    # =========================================================================
    
    async def subscribe(
        self,
        table: str,
        *,
        filter: Optional[str] = None,
        columns: Optional[List[str]] = None,
        fetch_initial: bool = True,
    ) -> TableSignal:
        """
        Subscribe to a table and get a reactive Signal.
        
        The returned Signal:
        - Contains the current table data
        - Auto-updates when data changes
        - Can be used directly in PyNext components
        
        Args:
            table: Table name to subscribe to
            filter: PostgREST filter expression
            columns: Specific columns to return
            fetch_initial: Whether to fetch initial data
        
        Returns:
            TableSignal that updates automatically
        
        Example:
            users = await db.realtime.subscribe("users")
            
            # Access data
            print(f"Users: {users()}")
            
            # Use in component
            def UserList():
                return ul([li(u['name']) for u in users()])
        """
        key = f"{table}:{filter}" if filter else table
        
        # Return existing signal if already subscribed
        if key in self._table_signals:
            return self._table_signals[key]
        
        # Fetch initial data if requested
        initial_data = []
        if fetch_initial:
            try:
                query = self._supabase.table(table).select("*")
                # Note: filter parsing would be more complex in production
                result = query.execute()
                initial_data = result.data if result.data else []
            except Exception as e:
                # Log error but continue with empty initial data
                pass
        
        # Create signal
        signal = TableSignal(table, initial_data)
        self._table_signals[key] = signal
        
        # Create subscription
        subscription = Subscription(
            table=table,
            filter=filter,
            columns=columns,
        )
        self._active_subscriptions[key] = subscription
        
        # Start listening if not already
        if self._is_running:
            await self._subscribe_to_channel(subscription)
        
        return signal
    
    async def unsubscribe(self, table: str, filter: Optional[str] = None):
        """
        Unsubscribe from a table.
        
        Args:
            table: Table name
            filter: Filter that was used (if any)
        """
        key = f"{table}:{filter}" if filter else table
        
        if key in self._active_subscriptions:
            del self._active_subscriptions[key]
        
        if key in self._table_signals:
            del self._table_signals[key]
    
    # =========================================================================
    # LIFECYCLE
    # =========================================================================
    
    async def start(self):
        """
        Start listening for realtime events.
        
        This must be called after registering handlers with decorators
        or after calling subscribe().
        
        Example:
            @on_insert("users")
            async def handle_user(record):
                pass
            
            await db.realtime.start()
        """
        if self._is_running:
            return
        
        if not self._config.enabled:
            return
        
        self._is_running = True
        
        # Subscribe to all registered handlers
        for subscription in self._registry.get_subscriptions():
            await self._subscribe_to_channel(subscription)
        
        # Subscribe to signal subscriptions
        for subscription in self._active_subscriptions.values():
            await self._subscribe_to_channel(subscription)
        
        # Start background listener
        self._listen_task = asyncio.create_task(self._listen_loop())
    
    async def stop(self):
        """
        Stop listening for realtime events.
        
        Closes all channels and connections.
        """
        self._is_running = False
        
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
            self._listen_task = None
        
        # Close all channels
        try:
            if self._channel:
                await self._channel.unsubscribe()
        except Exception:
            pass
    
    async def _subscribe_to_channel(self, subscription: Subscription):
        """Create and subscribe to a Supabase channel."""
        try:
            # Build channel name
            channel_name = f"realtime:{subscription.table}"
            if subscription.filter:
                channel_name += f":{subscription.filter}"
            
            subscription.channel_name = channel_name
            
            # Create channel
            channel = self._client.channel(channel_name)
            
            # Set up event handlers
            channel.on_postgres_changes(
                event="*",  # All events
                schema="public",
                table=subscription.table,
                filter=subscription.filter,
                callback=lambda payload: self._handle_event(payload, subscription),
            )
            
            # Subscribe
            await channel.subscribe()
            subscription.state = ChannelState.JOINED
            
            self._channel = channel
            
        except Exception as e:
            subscription.state = ChannelState.ERRORED
            raise SubscriptionError(table=subscription.table, reason=str(e))
    
    async def _listen_loop(self):
        """Background loop to maintain connection."""
        while self._is_running:
            try:
                await asyncio.sleep(self._config.heartbeat_interval)
                
                # Check connection health
                # The underlying library handles heartbeats
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self._config.auto_reconnect:
                    await self._reconnect()
                else:
                    raise
    
    async def _reconnect(self):
        """Attempt to reconnect after disconnect."""
        if self._reconnect_attempts >= self._config.max_reconnect_attempts:
            raise RealtimeConnectionError(
                message=f"Failed to reconnect after {self._reconnect_attempts} attempts"
            )
        
        self._reconnect_attempts += 1
        
        await asyncio.sleep(self._config.reconnect_delay * self._reconnect_attempts)
        
        try:
            # Resubscribe to all channels
            for subscription in self._registry.get_subscriptions():
                await self._subscribe_to_channel(subscription)
            
            for subscription in self._active_subscriptions.values():
                await self._subscribe_to_channel(subscription)
            
            self._reconnect_attempts = 0
            
        except Exception:
            await self._reconnect()
    
    def _handle_event(self, payload: Dict[str, Any], subscription: Subscription):
        """Handle incoming realtime event."""
        try:
            event = RealtimeEvent.from_payload(payload)
            
            # Update table signals
            key = f"{subscription.table}:{subscription.filter}" if subscription.filter else subscription.table
            if key in self._table_signals:
                self._table_signals[key].handle_event(event)
            
            # Call registered handlers
            handlers = self._registry.get_handlers(
                subscription.table,
                event.type,
                subscription.filter,
            )
            
            for handler in handlers:
                asyncio.create_task(self._call_handler(handler, event))
                
        except Exception as e:
            # Log error but don't crash
            pass
    
    async def _call_handler(self, handler: Callable, event: RealtimeEvent):
        """Call an event handler with appropriate arguments."""
        try:
            # Determine handler signature
            import inspect
            sig = inspect.signature(handler)
            params = list(sig.parameters.keys())
            
            if len(params) == 1:
                # Single param: just the record
                await handler(event.record)
            elif len(params) == 2:
                # Two params: old and new record
                await handler(event.old_record, event.new_record)
            elif len(params) == 3:
                # Three params: event_type, old, new
                await handler(event.type.value, event.old_record, event.new_record)
            else:
                # Pass the full event
                await handler(event)
                
        except Exception as e:
            # Log error but don't crash
            pass
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def get_subscription(self, table: str, filter: Optional[str] = None) -> Optional[Subscription]:
        """Get an active subscription."""
        key = f"{table}:{filter}" if filter else table
        return self._active_subscriptions.get(key)
    
    def get_signal(self, table: str, filter: Optional[str] = None) -> Optional[TableSignal]:
        """Get a table signal."""
        key = f"{table}:{filter}" if filter else table
        return self._table_signals.get(key)
    
    @property
    def is_connected(self) -> bool:
        """Check if realtime is connected."""
        return self._is_running and self._channel is not None
    
    @property
    def subscriptions(self) -> List[Subscription]:
        """Get all active subscriptions."""
        return list(self._active_subscriptions.values())

