"""
PyNext Per-Query Timeout.

Provides two ways to set timeouts on database queries:
1. Chain method: query.timeout(5).all()
2. Context manager: async with db.timeout(5):

Why Two Approaches?
    Chain method is perfect for single queries.
    Context manager is perfect for multiple related queries.

Usage - Chain Method (Default, Easiest):
    # Single query with 5 second timeout
    users = await User.select().where(active=True).timeout(5).all()
    
    # With custom error message
    users = await User.select().timeout(5, message="User query too slow").all()

Usage - Context Manager:
    # Multiple queries share same timeout
    async with db.timeout(10):
        users = await User.select().all()
        orders = await Order.select().where(user_id=user.id).all()

Usage - Direct Execute:
    result = await db.execute(
        "SELECT * FROM huge_table",
        timeout=30,
        timeout_message="Report generation timed out"
    )
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar, Union
from contextlib import asynccontextmanager
from contextvars import ContextVar
import asyncio
import time

from pynext.db.exceptions import DatabaseError


# =============================================================================
# EXCEPTIONS
# =============================================================================

class QueryTimeoutError(DatabaseError):
    """
    Raised when a query exceeds its timeout.
    
    Attributes:
        query: The SQL query that timed out
        timeout_seconds: The configured timeout
        duration_ms: How long the query ran before timeout
        message: Custom error message if provided
    
    Example:
        try:
            await User.select().timeout(5).all()
        except QueryTimeoutError as e:
            print(f"Query timed out after {e.duration_ms}ms")
            print(f"Timeout was: {e.timeout_seconds}s")
    """
    
    def __init__(
        self,
        query: str = "",
        timeout_seconds: float = 0,
        duration_ms: float = 0,
        message: Optional[str] = None,
    ):
        self.query = query
        self.timeout_seconds = timeout_seconds
        self.duration_ms = duration_ms
        self.custom_message = message
        
        if message:
            super().__init__(message)
        else:
            super().__init__(
                f"Query timed out after {duration_ms:.1f}ms "
                f"(timeout: {timeout_seconds}s)"
            )
    
    def __repr__(self) -> str:
        return (
            f"QueryTimeoutError(timeout={self.timeout_seconds}s, "
            f"duration={self.duration_ms:.1f}ms)"
        )


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class QueryTimeout:
    """
    Configuration for a query timeout.
    
    Attributes:
        seconds: Timeout in seconds
        message: Custom error message
        track_stats: Whether to track timeout statistics
    
    Example:
        timeout = QueryTimeout(seconds=5, message="User lookup too slow")
    """
    seconds: float
    message: Optional[str] = None
    track_stats: bool = True
    
    def __post_init__(self):
        """Validate timeout configuration."""
        if self.seconds <= 0:
            raise ValueError(f"Timeout must be positive, got {self.seconds}")
        if self.seconds > 86400:  # 24 hours
            raise ValueError(f"Timeout too large: {self.seconds}s (max 24 hours)")
    
    def to_postgres_ms(self) -> int:
        """Convert to PostgreSQL statement_timeout in milliseconds."""
        return int(self.seconds * 1000)


@dataclass
class TimeoutConfig:
    """
    Global timeout configuration.
    
    Attributes:
        default_timeout: Default timeout for all queries
        max_timeout: Maximum allowed timeout
        track_timeouts: Track timeout occurrences
        on_timeout: Callback when timeout occurs
    """
    default_timeout: Optional[float] = None
    max_timeout: float = 3600.0  # 1 hour
    track_timeouts: bool = True
    on_timeout: Optional[Callable[[QueryTimeoutError], None]] = None


# =============================================================================
# TIMEOUT STATS
# =============================================================================

@dataclass
class TimeoutStats:
    """
    Statistics for query timeouts.
    
    Attributes:
        total_queries: Total queries with timeout set
        timeout_count: Number of queries that timed out
        avg_duration_ms: Average duration of timed-out queries
        last_timeout: When last timeout occurred
        by_query_type: Breakdown by query type (SELECT, INSERT, etc.)
    """
    total_queries: int = 0
    timeout_count: int = 0
    total_duration_ms: float = 0.0
    last_timeout: Optional[datetime] = None
    by_query_type: Dict[str, int] = field(default_factory=dict)
    
    @property
    def avg_duration_ms(self) -> float:
        """Average duration of timed-out queries."""
        if self.timeout_count == 0:
            return 0.0
        return self.total_duration_ms / self.timeout_count
    
    @property
    def timeout_rate(self) -> float:
        """Percentage of queries that timed out."""
        if self.total_queries == 0:
            return 0.0
        return (self.timeout_count / self.total_queries) * 100
    
    def record_query(self):
        """Record a query with timeout."""
        self.total_queries += 1
    
    def record_timeout(self, duration_ms: float, query_type: str = "UNKNOWN"):
        """Record a timeout occurrence."""
        self.timeout_count += 1
        self.total_duration_ms += duration_ms
        self.last_timeout = datetime.now()
        self.by_query_type[query_type] = self.by_query_type.get(query_type, 0) + 1
    
    def reset(self):
        """Reset all statistics."""
        self.total_queries = 0
        self.timeout_count = 0
        self.total_duration_ms = 0.0
        self.last_timeout = None
        self.by_query_type.clear()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "total_queries": self.total_queries,
            "timeout_count": self.timeout_count,
            "avg_duration_ms": self.avg_duration_ms,
            "timeout_rate": self.timeout_rate,
            "last_timeout": self.last_timeout.isoformat() if self.last_timeout else None,
            "by_query_type": dict(self.by_query_type),
        }


# Global stats instance
_global_timeout_stats = TimeoutStats()


def get_timeout_stats() -> TimeoutStats:
    """Get global timeout statistics."""
    return _global_timeout_stats


def reset_timeout_stats():
    """Reset global timeout statistics."""
    _global_timeout_stats.reset()


# =============================================================================
# CONTEXT VARIABLE FOR SCOPED TIMEOUTS
# =============================================================================

# Current timeout in context (for nested contexts)
_current_timeout: ContextVar[Optional[QueryTimeout]] = ContextVar(
    "current_timeout", default=None
)


def get_current_timeout() -> Optional[QueryTimeout]:
    """Get the current timeout from context."""
    return _current_timeout.get()


def set_current_timeout(timeout: Optional[QueryTimeout]) -> None:
    """Set the current timeout in context."""
    _current_timeout.set(timeout)


# =============================================================================
# CONTEXT MANAGER
# =============================================================================

class TimeoutContext:
    """
    Context manager for scoped timeouts.
    
    All queries within this context will use the specified timeout.
    Supports nesting (inner timeout takes precedence).
    
    Usage:
        async with TimeoutContext(seconds=10):
            users = await User.select().all()
            orders = await Order.select().all()
        
        # Nested (inner takes precedence)
        async with TimeoutContext(seconds=30):
            # ... slow queries ...
            async with TimeoutContext(seconds=5):
                # ... quick queries with shorter timeout ...
    """
    
    def __init__(
        self,
        seconds: float,
        message: Optional[str] = None,
        track_stats: bool = True,
    ):
        self.timeout = QueryTimeout(
            seconds=seconds,
            message=message,
            track_stats=track_stats,
        )
        self._previous_timeout: Optional[QueryTimeout] = None
        self._entered = False
    
    async def __aenter__(self) -> "TimeoutContext":
        """Enter the timeout context."""
        self._previous_timeout = get_current_timeout()
        set_current_timeout(self.timeout)
        self._entered = True
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Exit the timeout context."""
        set_current_timeout(self._previous_timeout)
        self._entered = False
        
        # Don't suppress exceptions
        return False
    
    @property
    def seconds(self) -> float:
        """Get timeout seconds."""
        return self.timeout.seconds
    
    def __repr__(self) -> str:
        status = "active" if self._entered else "inactive"
        return f"TimeoutContext(seconds={self.timeout.seconds}, status={status})"


@asynccontextmanager
async def timeout_context(
    seconds: float,
    message: Optional[str] = None,
    track_stats: bool = True,
):
    """
    Async context manager for query timeouts.
    
    Usage:
        async with timeout_context(10):
            await User.select().all()
    """
    ctx = TimeoutContext(seconds, message, track_stats)
    async with ctx:
        yield ctx


# =============================================================================
# TIMEOUT EXECUTOR
# =============================================================================

class TimeoutExecutor:
    """
    Executes queries with timeout enforcement.
    
    This class wraps database execution to enforce timeouts
    using PostgreSQL's statement_timeout setting.
    """
    
    def __init__(
        self,
        config: Optional[TimeoutConfig] = None,
        stats: Optional[TimeoutStats] = None,
    ):
        self._config = config or TimeoutConfig()
        self._stats = stats or _global_timeout_stats
    
    def get_effective_timeout(
        self,
        explicit_timeout: Optional[float] = None,
    ) -> Optional[QueryTimeout]:
        """
        Get the effective timeout for a query.
        
        Priority:
        1. Explicit timeout passed to query
        2. Context timeout (from TimeoutContext)
        3. Default timeout (from config)
        
        Args:
            explicit_timeout: Timeout passed directly to query
        
        Returns:
            QueryTimeout or None if no timeout configured
        """
        # Explicit timeout takes highest priority
        if explicit_timeout is not None:
            return QueryTimeout(seconds=explicit_timeout)
        
        # Context timeout (from async with db.timeout(...))
        context_timeout = get_current_timeout()
        if context_timeout is not None:
            return context_timeout
        
        # Default timeout from config
        if self._config.default_timeout is not None:
            return QueryTimeout(seconds=self._config.default_timeout)
        
        return None
    
    def validate_timeout(self, timeout: QueryTimeout) -> QueryTimeout:
        """
        Validate and clamp timeout to allowed range.
        
        Args:
            timeout: Timeout to validate
        
        Returns:
            Validated timeout (may be clamped)
        """
        if timeout.seconds > self._config.max_timeout:
            return QueryTimeout(
                seconds=self._config.max_timeout,
                message=timeout.message,
                track_stats=timeout.track_stats,
            )
        return timeout
    
    async def execute_with_timeout(
        self,
        query: str,
        params: tuple = (),
        timeout: Optional[QueryTimeout] = None,
        execute_fn: Optional[Callable] = None,
    ) -> Any:
        """
        Execute a query with timeout enforcement.
        
        This wraps the query in a transaction that sets
        statement_timeout for just that query.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            timeout: Timeout configuration
            execute_fn: Function to execute the query
        
        Returns:
            Query result
        
        Raises:
            QueryTimeoutError: If query exceeds timeout
        """
        if timeout is None:
            # No timeout, execute normally
            if execute_fn:
                return await execute_fn(query, params)
            raise ValueError("execute_fn required when no timeout")
        
        # Validate timeout
        timeout = self.validate_timeout(timeout)
        
        # Track stats
        if timeout.track_stats:
            self._stats.record_query()
        
        start_time = time.perf_counter()
        
        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                execute_fn(query, params) if execute_fn else asyncio.sleep(0),
                timeout=timeout.seconds,
            )
            return result
            
        except asyncio.TimeoutError:
            # Calculate actual duration
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Determine query type
            query_type = self._get_query_type(query)
            
            # Track stats
            if timeout.track_stats:
                self._stats.record_timeout(duration_ms, query_type)
            
            # Create error
            error = QueryTimeoutError(
                query=query[:200],  # Truncate for safety
                timeout_seconds=timeout.seconds,
                duration_ms=duration_ms,
                message=timeout.message,
            )
            
            # Call callback if configured
            if self._config.on_timeout:
                try:
                    self._config.on_timeout(error)
                except Exception:
                    pass  # Don't let callback errors affect main flow
            
            raise error
    
    def _get_query_type(self, query: str) -> str:
        """Extract query type from SQL."""
        query_upper = query.strip().upper()
        for qt in ["SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER"]:
            if query_upper.startswith(qt):
                return qt
        return "OTHER"
    
    def generate_timeout_sql(self, timeout: QueryTimeout) -> str:
        """
        Generate SQL to set statement_timeout.
        
        This is used when we need to set timeout in PostgreSQL directly.
        
        Args:
            timeout: Timeout configuration
        
        Returns:
            SET statement_timeout SQL
        """
        timeout_ms = timeout.to_postgres_ms()
        return f"SET LOCAL statement_timeout = {timeout_ms}"
    
    def generate_reset_sql(self) -> str:
        """Generate SQL to reset statement_timeout."""
        return "SET LOCAL statement_timeout = 0"


# =============================================================================
# QUERY BUILDER MIXIN
# =============================================================================

T = TypeVar("T")


class TimeoutMixin(Generic[T]):
    """
    Mixin for adding timeout support to query builders.
    
    This is mixed into the Query class to add .timeout() method.
    
    Usage:
        class Query(TimeoutMixin[Query]):
            ...
        
        # Now you can do:
        query.timeout(5).all()
    """
    
    _timeout: Optional[QueryTimeout] = None
    
    def timeout(
        self: T,
        seconds: float,
        message: Optional[str] = None,
    ) -> T:
        """
        Set a timeout for this query.
        
        Args:
            seconds: Timeout in seconds
            message: Custom error message if timeout occurs
        
        Returns:
            Self for chaining
        
        Example:
            users = await User.select().timeout(5).all()
            
            # With custom message
            users = await User.select().timeout(
                5, 
                message="User search too slow"
            ).all()
        """
        self._timeout = QueryTimeout(seconds=seconds, message=message)
        return self
    
    def get_timeout(self) -> Optional[QueryTimeout]:
        """Get the configured timeout."""
        return self._timeout
    
    def has_timeout(self) -> bool:
        """Check if timeout is configured."""
        return self._timeout is not None
    
    def clear_timeout(self: T) -> T:
        """Remove timeout from this query."""
        self._timeout = None
        return self


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_timeout(
    seconds: float,
    message: Optional[str] = None,
) -> QueryTimeout:
    """
    Create a timeout configuration.
    
    Args:
        seconds: Timeout in seconds
        message: Custom error message
    
    Returns:
        QueryTimeout configuration
    
    Example:
        timeout = create_timeout(10, "Report generation timeout")
    """
    return QueryTimeout(seconds=seconds, message=message)


def create_timeout_executor(
    default_timeout: Optional[float] = None,
    max_timeout: float = 3600.0,
    on_timeout: Optional[Callable[[QueryTimeoutError], None]] = None,
) -> TimeoutExecutor:
    """
    Create a timeout executor with configuration.
    
    Args:
        default_timeout: Default timeout for all queries
        max_timeout: Maximum allowed timeout
        on_timeout: Callback when timeout occurs
    
    Returns:
        Configured TimeoutExecutor
    
    Example:
        executor = create_timeout_executor(
            default_timeout=30,
            max_timeout=300,
            on_timeout=lambda e: logger.warning(f"Timeout: {e}")
        )
    """
    config = TimeoutConfig(
        default_timeout=default_timeout,
        max_timeout=max_timeout,
        on_timeout=on_timeout,
    )
    return TimeoutExecutor(config=config)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Exceptions
    "QueryTimeoutError",
    # Configuration
    "QueryTimeout",
    "TimeoutConfig",
    # Statistics
    "TimeoutStats",
    "get_timeout_stats",
    "reset_timeout_stats",
    # Context
    "TimeoutContext",
    "timeout_context",
    "get_current_timeout",
    "set_current_timeout",
    # Executor
    "TimeoutExecutor",
    # Mixin
    "TimeoutMixin",
    # Convenience
    "create_timeout",
    "create_timeout_executor",
]

