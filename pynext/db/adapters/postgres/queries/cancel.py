"""
PyNext Query Cancellation.

Provides query tracking and cancellation with:
- Request-based tracking
- Automatic cancellation on client disconnect
- Manual cancellation API
- Running query monitoring

Why Query Cancellation?
    Long-running queries consume database resources. When a client
    disconnects (user navigates away), we should cancel their queries
    to free resources for other users.

Usage - Track Queries:
    async with db.track_query(request_id="req_123") as tracker:
        result = await long_running_query()

Usage - Cancel on Disconnect (Automatic):
    @app.on_disconnect
    async def handle_disconnect(request):
        await db.cancel_queries(request_id=request.id)

Usage - Manual Cancellation:
    query_id = await db.execute_async("SELECT * FROM huge_table")
    # Later...
    await db.cancel(query_id, reason="User cancelled")

Usage - Monitor Running Queries:
    running = await db.get_running_queries()
    for q in running:
        print(f"{q.id}: {q.query[:50]}... ({q.duration_ms}ms)")
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from contextvars import ContextVar
import asyncio
import time
import uuid
import weakref


# =============================================================================
# ENUMS
# =============================================================================

class QueryState(str, Enum):
    """State of a tracked query."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


class CancelReason(str, Enum):
    """Reason for query cancellation."""
    CLIENT_DISCONNECT = "client_disconnect"
    TIMEOUT = "timeout"
    USER_REQUEST = "user_request"
    SHUTDOWN = "shutdown"
    RESOURCE_LIMIT = "resource_limit"


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class CancellationConfig:
    """
    Configuration for query cancellation.
    
    Attributes:
        cancel_on_disconnect: Auto-cancel when client disconnects
        cancel_timeout: Grace period before cancellation (seconds)
        track_all_queries: Track all queries (not just long-running)
        log_cancellations: Log when queries are cancelled
        max_tracked_queries: Maximum number of queries to track
    """
    cancel_on_disconnect: bool = True
    cancel_timeout: float = 5.0
    track_all_queries: bool = False
    log_cancellations: bool = True
    max_tracked_queries: int = 1000
    
    def __post_init__(self):
        """Validate configuration."""
        if self.cancel_timeout < 0:
            raise ValueError("cancel_timeout must be non-negative")
        if self.max_tracked_queries < 1:
            raise ValueError("max_tracked_queries must be at least 1")


# =============================================================================
# RUNNING QUERY
# =============================================================================

@dataclass
class RunningQuery:
    """
    Represents a currently running query.
    
    Attributes:
        id: Unique query ID
        request_id: Associated request ID
        query: SQL query (truncated for safety)
        params: Query parameters
        start_time: When query started
        state: Current state
        backend_pid: PostgreSQL backend PID
        connection_id: Connection ID
        cancel_reason: Why it was cancelled (if cancelled)
    """
    id: str
    request_id: Optional[str] = None
    query: str = ""
    params: tuple = ()
    start_time: Optional[datetime] = None
    state: QueryState = QueryState.PENDING
    backend_pid: Optional[int] = None
    connection_id: Optional[int] = None
    cancel_reason: Optional[CancelReason] = None
    _cancel_event: asyncio.Event = field(default_factory=asyncio.Event)
    
    def __post_init__(self):
        """Initialize defaults."""
        if self.start_time is None:
            self.start_time = datetime.now()
    
    @property
    def duration_ms(self) -> float:
        """Duration in milliseconds."""
        if self.start_time is None:
            return 0.0
        delta = datetime.now() - self.start_time
        return delta.total_seconds() * 1000
    
    @property
    def duration_seconds(self) -> float:
        """Duration in seconds."""
        return self.duration_ms / 1000
    
    @property
    def is_running(self) -> bool:
        """Check if query is currently running."""
        return self.state == QueryState.RUNNING
    
    @property
    def is_cancellable(self) -> bool:
        """Check if query can be cancelled."""
        return self.state in (QueryState.PENDING, QueryState.RUNNING)
    
    @property
    def is_cancelled(self) -> bool:
        """Check if query was cancelled."""
        return self.state == QueryState.CANCELLED
    
    def mark_running(self, backend_pid: Optional[int] = None):
        """Mark query as running."""
        self.state = QueryState.RUNNING
        self.backend_pid = backend_pid
    
    def mark_completed(self):
        """Mark query as completed."""
        self.state = QueryState.COMPLETED
    
    def mark_cancelled(self, reason: CancelReason = CancelReason.USER_REQUEST):
        """Mark query as cancelled."""
        self.state = QueryState.CANCELLED
        self.cancel_reason = reason
        self._cancel_event.set()
    
    def mark_error(self):
        """Mark query as errored."""
        self.state = QueryState.ERROR
    
    async def wait_for_cancel(self) -> bool:
        """Wait for cancellation signal."""
        return await self._cancel_event.wait()
    
    def check_cancelled(self) -> bool:
        """Check if cancelled without waiting."""
        return self._cancel_event.is_set()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "request_id": self.request_id,
            "query": self.query[:200],
            "duration_ms": self.duration_ms,
            "state": self.state.value,
            "backend_pid": self.backend_pid,
            "cancel_reason": self.cancel_reason.value if self.cancel_reason else None,
        }


# =============================================================================
# CANCELLATION TOKEN
# =============================================================================

class CancellationToken:
    """
    Token for cooperative cancellation.
    
    Queries can check this token to exit early if cancelled.
    """
    
    def __init__(self):
        """Initialize token."""
        self._cancelled = False
        self._reason: Optional[CancelReason] = None
        self._callbacks: List[Callable] = []
    
    @property
    def is_cancelled(self) -> bool:
        """Check if cancelled."""
        return self._cancelled
    
    @property
    def reason(self) -> Optional[CancelReason]:
        """Get cancellation reason."""
        return self._reason
    
    def cancel(self, reason: CancelReason = CancelReason.USER_REQUEST):
        """Cancel this token."""
        if not self._cancelled:
            self._cancelled = True
            self._reason = reason
            
            # Call callbacks
            for callback in self._callbacks:
                try:
                    callback(self)
                except Exception:
                    pass
    
    def on_cancel(self, callback: Callable) -> None:
        """Register cancellation callback."""
        self._callbacks.append(callback)
        
        # Call immediately if already cancelled
        if self._cancelled:
            try:
                callback(self)
            except Exception:
                pass
    
    def throw_if_cancelled(self) -> None:
        """Raise exception if cancelled."""
        if self._cancelled:
            raise QueryCancelledError(
                reason=self._reason or CancelReason.USER_REQUEST
            )
    
    def __repr__(self) -> str:
        status = "cancelled" if self._cancelled else "active"
        return f"CancellationToken({status})"


# =============================================================================
# EXCEPTIONS
# =============================================================================

class QueryCancelledError(Exception):
    """
    Raised when a query is cancelled.
    
    Attributes:
        query_id: ID of cancelled query
        reason: Why it was cancelled
        duration_ms: How long it ran before cancellation
    """
    
    def __init__(
        self,
        query_id: Optional[str] = None,
        reason: CancelReason = CancelReason.USER_REQUEST,
        duration_ms: float = 0.0,
        message: Optional[str] = None,
    ):
        self.query_id = query_id
        self.reason = reason
        self.duration_ms = duration_ms
        
        if message:
            super().__init__(message)
        else:
            super().__init__(
                f"Query cancelled: {reason.value} after {duration_ms:.1f}ms"
            )


# =============================================================================
# QUERY TRACKER
# =============================================================================

class QueryTracker:
    """
    Tracks running queries for a request.
    
    Use as a context manager to track queries within a scope.
    """
    
    def __init__(
        self,
        request_id: str,
        registry: "QueryRegistry",
        token: Optional[CancellationToken] = None,
    ):
        """
        Initialize tracker.
        
        Args:
            request_id: Request ID for grouping
            registry: Query registry
            token: Optional cancellation token
        """
        self.request_id = request_id
        self.registry = registry
        self.token = token or CancellationToken()
        self._queries: List[RunningQuery] = []
        self._entered = False
    
    async def __aenter__(self) -> "QueryTracker":
        """Enter tracking context."""
        self._entered = True
        self.registry.register_tracker(self)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Exit tracking context."""
        self._entered = False
        
        # Mark all queries as completed
        for query in self._queries:
            if query.is_running:
                query.mark_completed()
        
        self.registry.unregister_tracker(self)
        return False
    
    def track_query(
        self,
        sql: str,
        params: tuple = (),
    ) -> RunningQuery:
        """
        Track a new query.
        
        Args:
            sql: SQL query
            params: Query parameters
        
        Returns:
            RunningQuery for tracking
        """
        query = RunningQuery(
            id=str(uuid.uuid4()),
            request_id=self.request_id,
            query=sql[:500],  # Truncate for safety
            params=params,
        )
        
        self._queries.append(query)
        self.registry.register_query(query)
        
        return query
    
    async def cancel_all(self, reason: CancelReason = CancelReason.USER_REQUEST) -> int:
        """Cancel all tracked queries."""
        count = 0
        for query in self._queries:
            if query.is_cancellable:
                query.mark_cancelled(reason)
                count += 1
        
        self.token.cancel(reason)
        return count
    
    @property
    def query_count(self) -> int:
        """Number of tracked queries."""
        return len(self._queries)
    
    @property
    def running_queries(self) -> List[RunningQuery]:
        """Currently running queries."""
        return [q for q in self._queries if q.is_running]


# =============================================================================
# QUERY REGISTRY
# =============================================================================

class QueryRegistry:
    """
    Global registry of running queries.
    
    Manages query tracking and cancellation across all requests.
    """
    
    def __init__(self, config: Optional[CancellationConfig] = None):
        """
        Initialize registry.
        
        Args:
            config: Cancellation configuration
        """
        self.config = config or CancellationConfig()
        self._queries: Dict[str, RunningQuery] = {}
        self._trackers: Dict[str, QueryTracker] = {}
        self._by_request: Dict[str, Set[str]] = {}
        self._lock = asyncio.Lock()
    
    @property
    def query_count(self) -> int:
        """Total tracked queries."""
        return len(self._queries)
    
    @property
    def tracker_count(self) -> int:
        """Active trackers."""
        return len(self._trackers)
    
    def register_tracker(self, tracker: QueryTracker) -> None:
        """Register a query tracker."""
        self._trackers[tracker.request_id] = tracker
    
    def unregister_tracker(self, tracker: QueryTracker) -> None:
        """Unregister a query tracker."""
        self._trackers.pop(tracker.request_id, None)
    
    def register_query(self, query: RunningQuery) -> None:
        """Register a running query."""
        # Enforce max limit
        if len(self._queries) >= self.config.max_tracked_queries:
            self._evict_completed()
        
        self._queries[query.id] = query
        
        if query.request_id:
            if query.request_id not in self._by_request:
                self._by_request[query.request_id] = set()
            self._by_request[query.request_id].add(query.id)
    
    def unregister_query(self, query_id: str) -> Optional[RunningQuery]:
        """Unregister a query."""
        query = self._queries.pop(query_id, None)
        
        if query and query.request_id:
            request_queries = self._by_request.get(query.request_id, set())
            request_queries.discard(query_id)
            if not request_queries:
                self._by_request.pop(query.request_id, None)
        
        return query
    
    def get_query(self, query_id: str) -> Optional[RunningQuery]:
        """Get a query by ID."""
        return self._queries.get(query_id)
    
    def get_queries_for_request(self, request_id: str) -> List[RunningQuery]:
        """Get all queries for a request."""
        query_ids = self._by_request.get(request_id, set())
        return [self._queries[qid] for qid in query_ids if qid in self._queries]
    
    def get_running_queries(self) -> List[RunningQuery]:
        """Get all currently running queries."""
        return [q for q in self._queries.values() if q.is_running]
    
    async def cancel_query(
        self,
        query_id: str,
        reason: CancelReason = CancelReason.USER_REQUEST,
        cancel_fn: Optional[Callable] = None,
    ) -> bool:
        """
        Cancel a specific query.
        
        Args:
            query_id: Query ID to cancel
            reason: Cancellation reason
            cancel_fn: Function to cancel in database
        
        Returns:
            True if cancelled, False if not found
        """
        query = self._queries.get(query_id)
        if not query or not query.is_cancellable:
            return False
        
        query.mark_cancelled(reason)
        
        # Cancel in database if function provided
        if cancel_fn and query.backend_pid:
            try:
                await cancel_fn(query.backend_pid)
            except Exception:
                pass
        
        return True
    
    async def cancel_queries_for_request(
        self,
        request_id: str,
        reason: CancelReason = CancelReason.CLIENT_DISCONNECT,
        cancel_fn: Optional[Callable] = None,
    ) -> int:
        """
        Cancel all queries for a request.
        
        Args:
            request_id: Request ID
            reason: Cancellation reason
            cancel_fn: Function to cancel in database
        
        Returns:
            Number of queries cancelled
        """
        query_ids = list(self._by_request.get(request_id, set()))
        count = 0
        
        for query_id in query_ids:
            if await self.cancel_query(query_id, reason, cancel_fn):
                count += 1
        
        # Also cancel via tracker
        tracker = self._trackers.get(request_id)
        if tracker:
            await tracker.cancel_all(reason)
        
        return count
    
    async def cancel_all(
        self,
        reason: CancelReason = CancelReason.SHUTDOWN,
        cancel_fn: Optional[Callable] = None,
    ) -> int:
        """Cancel all running queries."""
        count = 0
        for query_id in list(self._queries.keys()):
            if await self.cancel_query(query_id, reason, cancel_fn):
                count += 1
        return count
    
    def _evict_completed(self) -> None:
        """Remove completed queries to make room."""
        completed = [
            qid for qid, q in self._queries.items()
            if not q.is_running
        ]
        
        # Remove oldest completed first
        for qid in completed[:len(completed)//2]:
            self.unregister_query(qid)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query_count": self.query_count,
            "tracker_count": self.tracker_count,
            "running_queries": [q.to_dict() for q in self.get_running_queries()],
        }


# =============================================================================
# CANCEL EXECUTOR
# =============================================================================

class CancelExecutor:
    """
    Executes query cancellation in the database.
    
    Uses pg_cancel_backend() to cancel running queries.
    """
    
    def __init__(
        self,
        registry: QueryRegistry,
        execute_fn: Optional[Callable] = None,
    ):
        """
        Initialize executor.
        
        Args:
            registry: Query registry
            execute_fn: Function to execute SQL
        """
        self.registry = registry
        self._execute_fn = execute_fn
    
    async def cancel_by_pid(self, backend_pid: int) -> bool:
        """
        Cancel query by PostgreSQL backend PID.
        
        Args:
            backend_pid: PostgreSQL backend process ID
        
        Returns:
            True if cancel signal sent
        """
        if self._execute_fn:
            try:
                result = await self._execute_fn(
                    "SELECT pg_cancel_backend($1)",
                    (backend_pid,)
                )
                return bool(result)
            except Exception:
                return False
        return False
    
    async def terminate_by_pid(self, backend_pid: int) -> bool:
        """
        Terminate query by PostgreSQL backend PID.
        
        This is more forceful than cancel.
        
        Args:
            backend_pid: PostgreSQL backend process ID
        
        Returns:
            True if terminate signal sent
        """
        if self._execute_fn:
            try:
                result = await self._execute_fn(
                    "SELECT pg_terminate_backend($1)",
                    (backend_pid,)
                )
                return bool(result)
            except Exception:
                return False
        return False
    
    async def get_backend_pids_for_queries(
        self,
        query_pattern: str,
    ) -> List[int]:
        """
        Get backend PIDs for queries matching a pattern.
        
        Args:
            query_pattern: SQL LIKE pattern
        
        Returns:
            List of backend PIDs
        """
        if self._execute_fn:
            try:
                rows = await self._execute_fn(
                    """
                    SELECT pid 
                    FROM pg_stat_activity 
                    WHERE query LIKE $1 
                    AND state = 'active'
                    AND pid != pg_backend_pid()
                    """,
                    (query_pattern,)
                )
                return [row["pid"] for row in rows]
            except Exception:
                return []
        return []


# =============================================================================
# CONTEXT VARIABLE
# =============================================================================

_current_tracker: ContextVar[Optional[QueryTracker]] = ContextVar(
    "current_tracker", default=None
)


def get_current_tracker() -> Optional[QueryTracker]:
    """Get current query tracker from context."""
    return _current_tracker.get()


def set_current_tracker(tracker: Optional[QueryTracker]) -> None:
    """Set current query tracker in context."""
    _current_tracker.set(tracker)


# =============================================================================
# GLOBAL STATE
# =============================================================================

_global_registry: Optional[QueryRegistry] = None


def get_query_registry() -> QueryRegistry:
    """Get global query registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = QueryRegistry()
    return _global_registry


def set_query_registry(registry: QueryRegistry) -> None:
    """Set global query registry."""
    global _global_registry
    _global_registry = registry


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def track_query(
    request_id: str,
    registry: Optional[QueryRegistry] = None,
) -> QueryTracker:
    """
    Create a query tracker for a request.
    
    Args:
        request_id: Unique request ID
        registry: Query registry (uses global if not provided)
    
    Returns:
        QueryTracker context manager
    
    Example:
        async with track_query("req_123") as tracker:
            result = await execute_query()
    """
    reg = registry or get_query_registry()
    return QueryTracker(request_id, reg)


async def cancel_queries(
    request_id: str,
    reason: CancelReason = CancelReason.CLIENT_DISCONNECT,
    registry: Optional[QueryRegistry] = None,
) -> int:
    """
    Cancel all queries for a request.
    
    Args:
        request_id: Request ID
        reason: Cancellation reason
        registry: Query registry
    
    Returns:
        Number of queries cancelled
    """
    reg = registry or get_query_registry()
    return await reg.cancel_queries_for_request(request_id, reason)


async def cancel(
    query_id: str,
    reason: CancelReason = CancelReason.USER_REQUEST,
    registry: Optional[QueryRegistry] = None,
) -> bool:
    """
    Cancel a specific query.
    
    Args:
        query_id: Query ID
        reason: Cancellation reason
        registry: Query registry
    
    Returns:
        True if cancelled
    """
    reg = registry or get_query_registry()
    return await reg.cancel_query(query_id, reason)


def get_running_queries(
    registry: Optional[QueryRegistry] = None,
) -> List[RunningQuery]:
    """
    Get all currently running queries.
    
    Args:
        registry: Query registry
    
    Returns:
        List of running queries
    """
    reg = registry or get_query_registry()
    return reg.get_running_queries()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "QueryState",
    "CancelReason",
    # Configuration
    "CancellationConfig",
    # Running query
    "RunningQuery",
    # Cancellation token
    "CancellationToken",
    # Exceptions
    "QueryCancelledError",
    # Tracker
    "QueryTracker",
    # Registry
    "QueryRegistry",
    # Executor
    "CancelExecutor",
    # Context
    "get_current_tracker",
    "set_current_tracker",
    # Global
    "get_query_registry",
    "set_query_registry",
    # Convenience
    "track_query",
    "cancel_queries",
    "cancel",
    "get_running_queries",
]

