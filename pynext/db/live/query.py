"""
PyNext LiveQuery - Reactive Database Queries.

The core of live queries: a Signal that holds query results
and automatically updates when the underlying data changes.

Usage:
    # Simple - just add .live()
    users = User.live()           # All users, always fresh
    
    # Filtered
    active = User.live().where(status="active")
    
    # Chained
    recent = Post.live().where(published=True).order_by("-created_at").limit(10)
    
    # Access data
    users()           # Get current value (list of users)
    users.loading     # Signal[bool] - is loading?
    users.error       # Signal[Optional[Exception]]
    
    # Control
    users.refetch()   # Force refresh
    users.stop()      # Stop subscription
"""

from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Set,
    Type,
    TypeVar,
    TYPE_CHECKING,
)

from pynext.reactive import Signal
from pynext.db.live.config import (
    LiveQueryConfig,
    QuerySignature,
    DEFAULT_CONFIG,
    UpdateGranularity,
)

if TYPE_CHECKING:
    from pynext.db.table import Table
    from pynext.db.query import Query


T = TypeVar("T", bound="Table")


class LiveQueryState(str, Enum):
    """
    State of a live query.
    
    - idle: Not started
    - connecting: Establishing subscription
    - loading: Fetching initial data
    - active: Subscribed and receiving updates
    - error: Error occurred
    - stopped: Manually stopped
    """
    IDLE = "idle"
    CONNECTING = "connecting"
    LOADING = "loading"
    ACTIVE = "active"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class LiveQueryMetadata:
    """
    Metadata about a live query.
    
    Useful for debugging and monitoring.
    """
    id: str
    table: str
    created_at: datetime
    last_update: Optional[datetime] = None
    update_count: int = 0
    error_count: int = 0
    signature: Optional[QuerySignature] = None


class LiveQuery(Generic[T]):
    """
    A reactive query that automatically updates when data changes.
    
    LiveQuery extends the concept of a Signal to hold database query results.
    When the underlying data changes, the query automatically re-runs and
    subscribers are notified.
    
    Core Properties:
        - data(): Get current results (list of models)
        - loading: Signal[bool] - is currently loading
        - error: Signal[Optional[Exception]] - last error
        - state: Signal[LiveQueryState] - current state
    
    Methods:
        - refetch(): Manually refresh data
        - stop(): Stop the subscription
        - where(**conditions): Add filter conditions
        - order_by(field): Set ordering
        - limit(n): Set result limit
    
    Usage:
        users = User.live()
        
        # In a component
        if users.loading():
            return Loading()
        
        if users.error():
            return Error(users.error())
        
        return UserList(users=users())
    """
    
    _is_signal = True  # For compatibility with Signal-based systems
    
    def __init__(
        self,
        model: Type[T],
        config: Optional[LiveQueryConfig] = None,
    ):
        """
        Create a new live query.
        
        Usually called via Model.live() instead of directly.
        
        Args:
            model: The model class to query
            config: Optional configuration overrides
        """
        self._id = f"live_{uuid.uuid4().hex[:12]}"
        self._model = model
        self._config = config or DEFAULT_CONFIG
        
        # Internal state
        self._data: List[T] = []
        self._data_by_id: Dict[int, T] = {}  # For surgical updates
        
        # Reactive signals
        self._loading = Signal(True, name=f"{self._id}_loading")
        self._error: Signal[Optional[Exception]] = Signal(None, name=f"{self._id}_error")
        self._state: Signal[LiveQueryState] = Signal(LiveQueryState.IDLE, name=f"{self._id}_state")
        
        # Query parameters
        self._where_clauses: List[Dict[str, Any]] = []
        self._order_by: Optional[str] = None
        self._limit: Optional[int] = None
        self._offset: Optional[int] = None
        self._fields: Optional[List[str]] = None
        
        # Subscription
        self._subscription_id: Optional[str] = None
        self._subscribers: List[Callable[[List[T]], None]] = []
        self._unsubscribe: Optional[Callable[[], None]] = None
        
        # Metadata
        self._metadata = LiveQueryMetadata(
            id=self._id,
            table=model.__table_name__,
            created_at=datetime.utcnow(),
        )
        
        # Start subscription if initial_fetch is enabled
        if self._config.initial_fetch:
            asyncio.create_task(self._start())
    
    def __call__(self) -> List[T]:
        """
        Get the current query results.
        
        Returns an empty list while loading.
        
        Usage:
            users = User.live()
            for user in users():
                print(user.name)
        """
        return self._data
    
    # ==========================================================================
    # Query Builder Methods (chainable)
    # ==========================================================================
    
    def where(self, **conditions: Any) -> "LiveQuery[T]":
        """
        Filter results by conditions.
        
        All conditions are AND'd together.
        
        Examples:
            User.live().where(status="active")
            User.live().where(role="admin", active=True)
        """
        self._where_clauses.append(conditions)
        return self
    
    def where_in(self, field: str, values: List[Any]) -> "LiveQuery[T]":
        """
        Filter by field in list of values.
        
        Examples:
            User.live().where_in("id", [1, 2, 3])
        """
        self._where_clauses.append({f"{field}__in": values})
        return self
    
    def where_not(self, **conditions: Any) -> "LiveQuery[T]":
        """
        Filter results by NOT conditions.
        
        Examples:
            User.live().where_not(status="deleted")
        """
        for field, value in conditions.items():
            self._where_clauses.append({f"{field}__ne": value})
        return self
    
    def where_gt(self, field: str, value: Any) -> "LiveQuery[T]":
        """
        Filter by field greater than value.
        
        Examples:
            User.live().where_gt("age", 18)
        """
        self._where_clauses.append({f"{field}__gt": value})
        return self
    
    def where_gte(self, field: str, value: Any) -> "LiveQuery[T]":
        """
        Filter by field greater than or equal to value.
        """
        self._where_clauses.append({f"{field}__gte": value})
        return self
    
    def where_lt(self, field: str, value: Any) -> "LiveQuery[T]":
        """
        Filter by field less than value.
        """
        self._where_clauses.append({f"{field}__lt": value})
        return self
    
    def where_lte(self, field: str, value: Any) -> "LiveQuery[T]":
        """
        Filter by field less than or equal to value.
        """
        self._where_clauses.append({f"{field}__lte": value})
        return self
    
    def where_like(self, field: str, pattern: str) -> "LiveQuery[T]":
        """
        Filter by LIKE pattern.
        
        Examples:
            User.live().where_like("email", "%@gmail.com")
        """
        self._where_clauses.append({f"{field}__like": pattern})
        return self
    
    def where_null(self, field: str) -> "LiveQuery[T]":
        """
        Filter by NULL values.
        """
        self._where_clauses.append({f"{field}__null": True})
        return self
    
    def where_not_null(self, field: str) -> "LiveQuery[T]":
        """
        Filter by NOT NULL values.
        """
        self._where_clauses.append({f"{field}__null": False})
        return self
    
    def order_by(self, field: str) -> "LiveQuery[T]":
        """
        Order results by field.
        
        Prefix with "-" for descending order.
        
        Examples:
            User.live().order_by("name")        # Ascending
            User.live().order_by("-created_at") # Descending
        """
        self._order_by = field
        return self
    
    def limit(self, n: int) -> "LiveQuery[T]":
        """
        Limit number of results.
        
        Examples:
            Post.live().order_by("-created_at").limit(10)  # Latest 10 posts
        """
        self._limit = n
        return self
    
    def offset(self, n: int) -> "LiveQuery[T]":
        """
        Skip first n results.
        
        Examples:
            Post.live().offset(10).limit(10)  # Posts 11-20
        """
        self._offset = n
        return self
    
    def select(self, *fields: str) -> "LiveQuery[T]":
        """
        Select specific fields only.
        
        Examples:
            User.live().select("id", "name", "email")
        """
        self._fields = list(fields)
        return self
    
    # ==========================================================================
    # Reactive Properties
    # ==========================================================================
    
    @property
    def loading(self) -> Signal[bool]:
        """
        Signal that is True while loading.
        
        Usage:
            if users.loading():
                return LoadingSpinner()
        """
        return self._loading
    
    @property
    def error(self) -> Signal[Optional[Exception]]:
        """
        Signal containing the last error, or None.
        
        Usage:
            if users.error():
                return ErrorMessage(users.error().args[0])
        """
        return self._error
    
    @property
    def state(self) -> Signal[LiveQueryState]:
        """
        Signal containing the current state.
        
        Usage:
            match users.state():
                case LiveQueryState.LOADING:
                    return LoadingSpinner()
                case LiveQueryState.ERROR:
                    return ErrorMessage()
                case LiveQueryState.ACTIVE:
                    return UserList(users())
        """
        return self._state
    
    @property
    def is_empty(self) -> bool:
        """Check if results are empty."""
        return len(self._data) == 0
    
    @property
    def count(self) -> int:
        """Get number of results."""
        return len(self._data)
    
    @property
    def metadata(self) -> LiveQueryMetadata:
        """Get query metadata."""
        return self._metadata
    
    # ==========================================================================
    # Control Methods
    # ==========================================================================
    
    async def refetch(self) -> List[T]:
        """
        Force a refresh of the data.
        
        Useful when you know data has changed and want to update immediately.
        
        Returns:
            The fresh data
        """
        await self._fetch_data()
        return self._data
    
    def stop(self) -> None:
        """
        Stop the live query subscription.
        
        Call this when you no longer need updates.
        The query can be restarted with .start().
        """
        if self._unsubscribe:
            self._unsubscribe()
            self._unsubscribe = None
        
        self._state.set(LiveQueryState.STOPPED)
        self._subscription_id = None
    
    async def start(self) -> None:
        """
        Start or restart the live query.
        
        Called automatically on creation if initial_fetch is True.
        """
        await self._start()
    
    def subscribe(self, callback: Callable[[List[T]], None]) -> Callable[[], None]:
        """
        Subscribe to data changes.
        
        Returns an unsubscribe function.
        
        Examples:
            unsubscribe = users.subscribe(lambda data: print(f"Got {len(data)} users"))
            # Later:
            unsubscribe()
        """
        self._subscribers.append(callback)
        return lambda: self._subscribers.remove(callback) if callback in self._subscribers else None
    
    # ==========================================================================
    # Internal Methods
    # ==========================================================================
    
    async def _start(self) -> None:
        """Initialize the subscription and fetch initial data."""
        try:
            self._state.set(LiveQueryState.CONNECTING)
            
            # Build query signature
            self._metadata.signature = self._build_signature()
            
            # Fetch initial data
            await self._fetch_data()
            
            # Subscribe to changes
            await self._subscribe_to_changes()
            
            self._state.set(LiveQueryState.ACTIVE)
            
        except Exception as e:
            self._error.set(e)
            self._state.set(LiveQueryState.ERROR)
            self._metadata.error_count += 1
    
    async def _fetch_data(self) -> None:
        """Fetch data from the database."""
        self._loading.set(True)
        self._state.set(LiveQueryState.LOADING)
        
        try:
            from pynext.db.table import get_adapter
            from pynext.db.query import Query
            
            adapter = get_adapter()
            query = Query(self._model, adapter, self._model._fields)
            
            # Apply filters
            for clause in self._where_clauses:
                query = query.where(**clause)
            
            # Apply ordering
            if self._order_by:
                query = query.order_by(self._order_by)
            
            # Apply limit/offset
            if self._limit:
                query = query.limit(self._limit)
            if self._offset:
                query = query.offset(self._offset)
            
            # Execute
            results = await query
            
            # Update internal state
            self._data = results
            self._data_by_id = {r.id: r for r in results if hasattr(r, "id")}
            
            # Update metadata
            self._metadata.last_update = datetime.utcnow()
            self._metadata.update_count += 1
            
            # Notify subscribers
            self._notify_subscribers()
            
        except Exception as e:
            self._error.set(e)
            self._state.set(LiveQueryState.ERROR)
            self._metadata.error_count += 1
            raise
        finally:
            self._loading.set(False)
    
    async def _subscribe_to_changes(self) -> None:
        """Subscribe to database changes."""
        from pynext.db.live.subscriptions import get_subscription_manager
        
        manager = get_subscription_manager()
        
        self._subscription_id = await manager.subscribe(
            query_signature=self._metadata.signature,
            callback=self._on_change,
            config=self._config,
        )
        
        self._unsubscribe = lambda: asyncio.create_task(
            manager.unsubscribe(self._subscription_id)
        )
    
    def _on_change(self, event: "ChangeEvent") -> None:
        """Handle a change event from the subscription."""
        from pynext.db.live.detection import ChangeType
        from pynext.db.live.updates import get_strategy_selector
        
        # Determine update strategy
        selector = get_strategy_selector()
        strategy = selector.select(
            signature=self._metadata.signature,
            event=event,
            config=self._config,
        )
        
        # Apply the update
        try:
            result = strategy.apply(
                current_data=self._data,
                current_by_id=self._data_by_id,
                event=event,
                model=self._model,
            )
            
            if result.changed:
                self._data = result.data
                self._data_by_id = result.data_by_id
                self._metadata.last_update = datetime.utcnow()
                self._metadata.update_count += 1
                self._notify_subscribers()
                
        except Exception as e:
            # If surgical update fails, fall back to full refresh
            if self._config.granularity != UpdateGranularity.REFRESH:
                asyncio.create_task(self._fetch_data())
            else:
                self._error.set(e)
                self._metadata.error_count += 1
    
    def _notify_subscribers(self) -> None:
        """Notify all subscribers of data changes."""
        for callback in self._subscribers:
            try:
                callback(self._data)
            except Exception:
                pass  # Don't let subscriber errors affect others
    
    def _build_signature(self) -> QuerySignature:
        """Build a unique signature for this query."""
        # Convert where clauses to hashable tuple
        where_tuple = tuple(
            tuple(sorted(clause.items()))
            for clause in self._where_clauses
        )
        
        # Convert fields to tuple
        fields_tuple = tuple(self._fields) if self._fields else tuple()
        
        return QuerySignature(
            table=self._model.__table_name__,
            where_clauses=where_tuple,
            order_by=self._order_by,
            limit=self._limit,
            offset=self._offset,
            fields=fields_tuple,
        )
    
    # ==========================================================================
    # Serialization
    # ==========================================================================
    
    def get_js_init(self) -> str:
        """Generate JavaScript initialization code."""
        config = {
            "id": self._id,
            "table": self._model.__table_name__,
            "where": self._where_clauses,
            "orderBy": self._order_by,
            "limit": self._limit,
            "offset": self._offset,
            "transport": self._config.transport.value,
        }
        return f"__pynext__.live.subscribe({json.dumps(config)})"
    
    def to_hydration_data(self) -> Dict[str, Any]:
        """Get data for hydration on client."""
        return {
            "id": self._id,
            "table": self._model.__table_name__,
            "data": [r._to_dict() if hasattr(r, "_to_dict") else r for r in self._data],
            "loading": self._loading(),
            "error": str(self._error()) if self._error() else None,
            "state": self._state().value,
            "config": self._config.to_dict(),
        }
    
    def __repr__(self) -> str:
        return (
            f"LiveQuery({self._model.__name__}, "
            f"state={self._state().value}, "
            f"count={len(self._data)})"
        )


# =============================================================================
# Factory Function
# =============================================================================

def live(model: Type[T], config: Optional[LiveQueryConfig] = None) -> LiveQuery[T]:
    """
    Create a live query for a model.
    
    This is the factory function used by Table.live().
    
    Examples:
        users = live(User)
        active = live(User, config=LiveQueryConfig(poll_interval=5.0))
    """
    return LiveQuery(model, config)


# =============================================================================
# Table Extension
# =============================================================================

def _add_live_to_table() -> None:
    """
    Add the .live() method to the Table class.
    
    Called on module import.
    """
    try:
        from pynext.db.table import Table
        
        @classmethod
        def table_live(
            cls: Type[T],
            config: Optional[LiveQueryConfig] = None,
        ) -> LiveQuery[T]:
            """
            Create a live query for this model.
            
            Returns a LiveQuery that automatically updates when data changes.
            
            Examples:
                users = User.live()
                active = User.live().where(status="active")
                recent = Post.live().order_by("-created_at").limit(10)
            """
            return LiveQuery(cls, config)
        
        Table.live = table_live
        
    except ImportError:
        pass  # Table not available yet


# Add .live() to Table when this module is imported
_add_live_to_table()

