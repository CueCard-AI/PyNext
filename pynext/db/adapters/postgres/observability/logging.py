"""
PyNext Database Logging Module.

Provides structured logging with rich context for database operations.
Supports both Python's standard logging and structlog for JSON output.

Why Structured Logging?
───────────────────────
Traditional logs are hard to search and analyze:
    "Query took 523ms: SELECT * FROM users WHERE..."

Structured logs are machine-parseable:
    {"event": "slow_query", "duration_ms": 523, "query": "SELECT...", "trace_id": "abc123"}

This module provides:
- Automatic context injection (query_id, trace_id, pool stats)
- Slow query detection and logging
- Multiple output formats (text, JSON, structlog)
- Log level filtering
- Parameter redaction for security

Usage Levels:

Level 1: Zero Config (Just Works)
    adapter = PostgresAdapter("postgresql://...", logging=True)

Level 2: Custom Threshold
    adapter = PostgresAdapter("postgresql://...", logging=LogConfig(slow_query_ms=100))

Level 3: Full Control
    adapter = PostgresAdapter("postgresql://...", logging=LogConfig(
        level="DEBUG",
        slow_query_ms=100,
        log_params=False,
        format="json",
    ))

AI-Friendly Design:
- Every class has clear docstrings
- Type hints on all parameters
- Descriptive error messages
- Examples in docstrings
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

# Logger for this module
logger = logging.getLogger("pynext.db.logging")


# ============================================================================
# Context Variables (Thread-Safe Request Context)
# ============================================================================

# These allow passing context through async call stacks
_query_context: ContextVar[Optional["QueryContext"]] = ContextVar(
    "query_context", default=None
)
_trace_id: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)
_client_ip: ContextVar[Optional[str]] = ContextVar("client_ip", default=None)


def set_trace_id(trace_id: str) -> None:
    """Set the trace ID for the current context.
    
    The trace ID propagates through all database operations in this context,
    making it easy to correlate logs across services.
    
    Args:
        trace_id: Unique identifier for the request/trace
    
    Example:
        set_trace_id("req_abc123")
        # All subsequent DB operations will include this trace_id
        users = await User.all()
    """
    _trace_id.set(trace_id)


def get_trace_id() -> Optional[str]:
    """Get the current trace ID."""
    return _trace_id.get()


def set_client_ip(ip: str) -> None:
    """Set the client IP for the current context.
    
    Useful for debugging which client caused a particular query.
    
    Args:
        ip: Client IP address
    """
    _client_ip.set(ip)


def get_client_ip() -> Optional[str]:
    """Get the current client IP."""
    return _client_ip.get()


# ============================================================================
# Enums
# ============================================================================

class LogLevel(str, Enum):
    """Log levels for database operations.
    
    DEBUG: All queries, parameters, timing
    INFO: Query summaries, connection events
    WARNING: Slow queries, pool warnings
    ERROR: Query failures, connection errors
    CRITICAL: Fatal errors, pool exhaustion
    """
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    
    def to_python_level(self) -> int:
        """Convert to Python logging level."""
        return getattr(logging, self.value)


class LogFormat(str, Enum):
    """Output format for logs.
    
    TEXT: Human-readable format
        2024-01-15 10:30:00 WARNING slow_query duration_ms=523 query="SELECT..."
    
    JSON: Machine-parseable JSON
        {"timestamp": "2024-01-15T10:30:00Z", "level": "WARNING", "event": "slow_query", ...}
    
    STRUCTLOG: For structlog integration (requires structlog package)
    """
    TEXT = "text"
    JSON = "json"
    STRUCTLOG = "structlog"


class LogEvent(str, Enum):
    """Types of loggable events."""
    QUERY_START = "query_start"
    QUERY_SUCCESS = "query_success"
    QUERY_ERROR = "query_error"
    SLOW_QUERY = "slow_query"
    
    CONNECTION_ACQUIRED = "connection_acquired"
    CONNECTION_RELEASED = "connection_released"
    CONNECTION_CREATED = "connection_created"
    CONNECTION_CLOSED = "connection_closed"
    CONNECTION_ERROR = "connection_error"
    
    POOL_EXHAUSTION_WARNING = "pool_exhaustion_warning"
    POOL_EXHAUSTED = "pool_exhausted"
    
    TRANSACTION_BEGIN = "transaction_begin"
    TRANSACTION_COMMIT = "transaction_commit"
    TRANSACTION_ROLLBACK = "transaction_rollback"
    
    RETRY_ATTEMPT = "retry_attempt"
    CIRCUIT_OPENED = "circuit_opened"
    CIRCUIT_CLOSED = "circuit_closed"


# ============================================================================
# Configuration
# ============================================================================

@dataclass
class LogConfig:
    """Configuration for database logging.
    
    This dataclass controls how database operations are logged.
    All options have sensible defaults - you can use LogConfig()
    for a reasonable starting configuration.
    
    Attributes:
        enabled: Whether logging is enabled
        level: Minimum log level to output
        format: Output format (text, json, structlog)
        slow_query_ms: Queries slower than this are logged as warnings
        log_queries: Whether to log query text
        log_params: Whether to log query parameters (security risk!)
        log_pool_stats: Whether to include pool statistics
        redact_patterns: Regex patterns to redact from queries
        max_query_length: Truncate queries longer than this
        logger_name: Name of the Python logger to use
        
    Example:
        # Default configuration
        config = LogConfig()
        
        # Custom slow query threshold
        config = LogConfig(slow_query_ms=50)
        
        # Production configuration (no params, JSON format)
        config = LogConfig(
            level=LogLevel.WARNING,
            format=LogFormat.JSON,
            log_params=False,
            slow_query_ms=100,
        )
    """
    enabled: bool = True
    level: LogLevel = LogLevel.INFO
    format: LogFormat = LogFormat.TEXT
    slow_query_ms: float = 100.0
    log_queries: bool = True
    log_params: bool = False  # Default False for security
    log_pool_stats: bool = True
    redact_patterns: List[str] = field(default_factory=list)
    max_query_length: int = 1000
    logger_name: str = "pynext.db"
    
    # Callbacks for custom handling
    on_slow_query: Optional[Callable[["LogRecord"], None]] = None
    on_error: Optional[Callable[["LogRecord"], None]] = None
    
    def __post_init__(self):
        """Validate configuration."""
        if isinstance(self.level, str):
            self.level = LogLevel(self.level.upper())
        if isinstance(self.format, str):
            self.format = LogFormat(self.format.lower())
        if self.slow_query_ms <= 0:
            raise ValueError("slow_query_ms must be positive")
        if self.max_query_length <= 0:
            raise ValueError("max_query_length must be positive")


# ============================================================================
# Query Context
# ============================================================================

@dataclass
class QueryContext:
    """Context for a database query.
    
    Holds all metadata about a query that might be useful for logging,
    debugging, or tracing. Created automatically when a query starts.
    
    Attributes:
        query_id: Unique identifier for this query
        query: The SQL query text
        params: Query parameters (if log_params enabled)
        start_time: When the query started
        end_time: When the query finished (set after completion)
        duration_ms: Query duration in milliseconds
        trace_id: Request trace ID (for distributed tracing)
        client_ip: Client IP address
        table: Detected table name (if applicable)
        query_type: Type of query (SELECT, INSERT, UPDATE, DELETE)
        error: Error message if query failed
        pool_stats: Pool statistics at query time
        
    Example:
        # Context is created automatically
        async with query_context("SELECT * FROM users") as ctx:
            # Execute query
            pass
        print(f"Query {ctx.query_id} took {ctx.duration_ms}ms")
    """
    query_id: str = field(default_factory=lambda: f"q_{uuid.uuid4().hex[:12]}")
    query: str = ""
    params: Optional[tuple] = None
    start_time: float = field(default_factory=time.monotonic)
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    trace_id: Optional[str] = None
    client_ip: Optional[str] = None
    table: Optional[str] = None
    query_type: Optional[str] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    pool_stats: Optional[Dict[str, Any]] = None
    connection_id: Optional[str] = None
    rows_affected: Optional[int] = None
    rows_returned: Optional[int] = None
    
    def __post_init__(self):
        """Initialize computed fields."""
        # Get trace context from context vars
        if self.trace_id is None:
            self.trace_id = get_trace_id()
        if self.client_ip is None:
            self.client_ip = get_client_ip()
        
        # Parse query type and table
        if self.query:
            self._parse_query()
    
    def _parse_query(self) -> None:
        """Extract query type and table from query text."""
        query_upper = self.query.strip().upper()
        
        # Detect query type
        for qt in ["SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER"]:
            if query_upper.startswith(qt):
                self.query_type = qt
                break
        
        # Extract table name (simple heuristic)
        if self.query_type == "SELECT":
            # SELECT ... FROM table_name
            if " FROM " in query_upper:
                parts = self.query.upper().split(" FROM ", 1)
                if len(parts) > 1:
                    table_part = parts[1].split()[0] if parts[1].split() else ""
                    self.table = table_part.strip('"').lower()
        elif self.query_type == "INSERT":
            # INSERT INTO table_name
            if " INTO " in query_upper:
                parts = self.query.upper().split(" INTO ", 1)
                if len(parts) > 1:
                    table_part = parts[1].split()[0] if parts[1].split() else ""
                    self.table = table_part.strip('"').lower()
        elif self.query_type in ("UPDATE", "DELETE"):
            # UPDATE table_name / DELETE FROM table_name
            parts = self.query.upper().split()
            if len(parts) > 1:
                idx = 1 if self.query_type == "UPDATE" else 2  # DELETE FROM
                if len(parts) > idx:
                    self.table = parts[idx].strip('"').lower()
    
    def finish(self, error: Optional[str] = None, error_type: Optional[str] = None) -> None:
        """Mark the query as finished.
        
        Args:
            error: Error message if query failed
            error_type: Type of error (e.g., "TimeoutError", "ConnectionError")
        """
        self.end_time = time.monotonic()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.error = error
        self.error_type = error_type
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "query_id": self.query_id,
            "query": self.query,
            "params": self.params if self.params else None,
            "duration_ms": round(self.duration_ms, 2) if self.duration_ms else None,
            "trace_id": self.trace_id,
            "client_ip": self.client_ip,
            "table": self.table,
            "query_type": self.query_type,
            "error": self.error,
            "error_type": self.error_type,
            "pool": self.pool_stats,
            "connection_id": self.connection_id,
            "rows_affected": self.rows_affected,
            "rows_returned": self.rows_returned,
        }


# ============================================================================
# Log Record
# ============================================================================

@dataclass
class LogRecord:
    """A structured log record.
    
    Contains all information about a logged event in a structured format.
    Can be serialized to text, JSON, or structlog format.
    
    Attributes:
        timestamp: When the event occurred
        level: Log level
        event: Type of event
        message: Human-readable message
        context: Query context (if applicable)
        extra: Additional fields
    """
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    level: LogLevel = LogLevel.INFO
    event: LogEvent = LogEvent.QUERY_SUCCESS
    message: str = ""
    context: Optional[QueryContext] = None
    extra: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "event": self.event.value,
            "message": self.message,
        }
        
        if self.context:
            result.update(self.context.to_dict())
        
        if self.extra:
            result.update(self.extra)
        
        return result
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), default=str)
    
    def to_text(self) -> str:
        """Convert to human-readable text."""
        parts = [
            self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            self.level.value.ljust(8),
            self.event.value,
        ]
        
        if self.message:
            parts.append(self.message)
        
        if self.context:
            if self.context.duration_ms is not None:
                parts.append(f"duration_ms={self.context.duration_ms:.2f}")
            if self.context.query_id:
                parts.append(f"query_id={self.context.query_id}")
            if self.context.trace_id:
                parts.append(f"trace_id={self.context.trace_id}")
            if self.context.table:
                parts.append(f"table={self.context.table}")
            if self.context.error:
                parts.append(f"error={self.context.error}")
        
        for key, value in self.extra.items():
            parts.append(f"{key}={value}")
        
        return " ".join(str(p) for p in parts)


# ============================================================================
# Database Logger
# ============================================================================

class DBLogger:
    """Structured logger for database operations.
    
    The main logging class that handles all database-related logging.
    Supports multiple output formats and integrates with Python's
    standard logging and optionally structlog.
    
    Features:
    - Automatic query context tracking
    - Slow query detection
    - Configurable output format (text, JSON, structlog)
    - Parameter redaction for security
    - Pool statistics inclusion
    - Custom callbacks for events
    
    Example:
        # Create logger with config
        config = LogConfig(slow_query_ms=100, format=LogFormat.JSON)
        db_logger = DBLogger(config)
        
        # Log a query
        ctx = QueryContext(query="SELECT * FROM users")
        ctx.finish()
        db_logger.log_query(ctx)
        
        # Check if slow
        if db_logger.is_slow_query(ctx):
            print("Query was slow!")
    """
    
    def __init__(self, config: Optional[LogConfig] = None):
        """Initialize the database logger.
        
        Args:
            config: Logging configuration (uses defaults if not provided)
        """
        self.config = config or LogConfig()
        self._logger = logging.getLogger(self.config.logger_name)
        self._structlog = None
        
        # Try to import structlog if requested
        if self.config.format == LogFormat.STRUCTLOG:
            try:
                import structlog
                self._structlog = structlog.get_logger(self.config.logger_name)
            except ImportError:
                logger.warning(
                    "structlog not installed, falling back to JSON format. "
                    "Install with: pip install structlog"
                )
                self.config.format = LogFormat.JSON
        
        # Statistics
        self._stats = {
            "queries_logged": 0,
            "slow_queries": 0,
            "errors": 0,
        }
    
    @property
    def enabled(self) -> bool:
        """Whether logging is enabled."""
        return self.config.enabled
    
    def is_slow_query(self, ctx: QueryContext) -> bool:
        """Check if a query is considered slow.
        
        Args:
            ctx: Query context with timing information
            
        Returns:
            True if query duration exceeds slow_query_ms threshold
        """
        if ctx.duration_ms is None:
            return False
        return ctx.duration_ms > self.config.slow_query_ms
    
    def _should_log(self, level: LogLevel) -> bool:
        """Check if we should log at this level."""
        if not self.config.enabled:
            return False
        return level.to_python_level() >= self.config.level.to_python_level()
    
    def _redact_query(self, query: str) -> str:
        """Redact sensitive information from query.
        
        Args:
            query: Original query text
            
        Returns:
            Query with sensitive patterns redacted
        """
        import re
        
        result = query
        
        # Apply custom redaction patterns
        for pattern in self.config.redact_patterns:
            result = re.sub(pattern, "[REDACTED]", result)
        
        # Truncate if too long
        if len(result) > self.config.max_query_length:
            result = result[:self.config.max_query_length] + "..."
        
        return result
    
    def _prepare_context(self, ctx: QueryContext) -> QueryContext:
        """Prepare context for logging (redaction, truncation).
        
        Args:
            ctx: Original query context
            
        Returns:
            Context with redacted/truncated fields
        """
        if not self.config.log_queries:
            ctx.query = "[QUERY LOGGING DISABLED]"
        else:
            ctx.query = self._redact_query(ctx.query)
        
        if not self.config.log_params:
            ctx.params = None
        
        return ctx
    
    def _emit(self, record: LogRecord) -> None:
        """Emit a log record.
        
        Args:
            record: The log record to emit
        """
        if self.config.format == LogFormat.STRUCTLOG and self._structlog:
            # Use structlog
            log_method = getattr(self._structlog, record.level.value.lower())
            log_method(
                record.event.value,
                **record.to_dict(),
            )
        elif self.config.format == LogFormat.JSON:
            # JSON format
            log_method = getattr(self._logger, record.level.value.lower())
            log_method(record.to_json())
        else:
            # Text format
            log_method = getattr(self._logger, record.level.value.lower())
            log_method(record.to_text())
    
    def log_query(
        self,
        ctx: QueryContext,
        level: Optional[LogLevel] = None,
        message: str = "",
    ) -> None:
        """Log a completed query.
        
        Automatically determines log level based on:
        - Error: ERROR level
        - Slow: WARNING level
        - Success: DEBUG level
        
        Args:
            ctx: Query context with timing and results
            level: Override log level (auto-detected if not provided)
            message: Optional message
        """
        if not self.config.enabled:
            return
        
        # Determine level
        if level is None:
            if ctx.error:
                level = LogLevel.ERROR
                event = LogEvent.QUERY_ERROR
            elif self.is_slow_query(ctx):
                level = LogLevel.WARNING
                event = LogEvent.SLOW_QUERY
            else:
                level = LogLevel.DEBUG
                event = LogEvent.QUERY_SUCCESS
        else:
            event = LogEvent.QUERY_SUCCESS if not ctx.error else LogEvent.QUERY_ERROR
        
        if not self._should_log(level):
            return
        
        # Prepare context
        ctx = self._prepare_context(ctx)
        
        # Create record
        record = LogRecord(
            level=level,
            event=event,
            message=message,
            context=ctx,
        )
        
        # Emit
        self._emit(record)
        
        # Update stats
        self._stats["queries_logged"] += 1
        if event == LogEvent.SLOW_QUERY:
            self._stats["slow_queries"] += 1
            if self.config.on_slow_query:
                self.config.on_slow_query(record)
        if ctx.error:
            self._stats["errors"] += 1
            if self.config.on_error:
                self.config.on_error(record)
    
    def log_event(
        self,
        event: LogEvent,
        level: LogLevel = LogLevel.INFO,
        message: str = "",
        context: Optional[QueryContext] = None,
        **extra: Any,
    ) -> None:
        """Log a database event.
        
        Args:
            event: Type of event
            level: Log level
            message: Human-readable message
            context: Optional query context
            **extra: Additional fields to include
        """
        if not self._should_log(level):
            return
        
        record = LogRecord(
            level=level,
            event=event,
            message=message,
            context=context,
            extra=extra,
        )
        
        self._emit(record)
    
    def log_connection_acquired(
        self,
        connection_id: str,
        wait_time_ms: float,
        pool_stats: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log connection acquisition from pool."""
        self.log_event(
            LogEvent.CONNECTION_ACQUIRED,
            LogLevel.DEBUG,
            f"Connection {connection_id} acquired",
            connection_id=connection_id,
            wait_time_ms=round(wait_time_ms, 2),
            pool=pool_stats,
        )
    
    def log_connection_released(
        self,
        connection_id: str,
        held_time_ms: float,
    ) -> None:
        """Log connection release back to pool."""
        self.log_event(
            LogEvent.CONNECTION_RELEASED,
            LogLevel.DEBUG,
            f"Connection {connection_id} released",
            connection_id=connection_id,
            held_time_ms=round(held_time_ms, 2),
        )
    
    def log_connection_error(
        self,
        error: str,
        error_type: str,
        connection_id: Optional[str] = None,
    ) -> None:
        """Log connection error."""
        self.log_event(
            LogEvent.CONNECTION_ERROR,
            LogLevel.ERROR,
            f"Connection error: {error}",
            connection_id=connection_id,
            error=error,
            error_type=error_type,
        )
    
    def log_pool_exhaustion_warning(
        self,
        utilization: float,
        pool_stats: Dict[str, Any],
    ) -> None:
        """Log pool exhaustion warning (before failure)."""
        self.log_event(
            LogEvent.POOL_EXHAUSTION_WARNING,
            LogLevel.WARNING,
            f"Pool at {utilization:.1%} capacity",
            utilization=utilization,
            pool=pool_stats,
        )
    
    def log_pool_exhausted(
        self,
        pool_stats: Dict[str, Any],
        waiting_count: int,
    ) -> None:
        """Log pool exhaustion (failure)."""
        self.log_event(
            LogEvent.POOL_EXHAUSTED,
            LogLevel.CRITICAL,
            f"Pool exhausted! {waiting_count} requests waiting",
            pool=pool_stats,
            waiting_count=waiting_count,
        )
    
    def log_transaction(
        self,
        event: LogEvent,
        transaction_id: Optional[str] = None,
        isolation: Optional[str] = None,
    ) -> None:
        """Log transaction event."""
        self.log_event(
            event,
            LogLevel.DEBUG,
            f"Transaction {event.value}",
            transaction_id=transaction_id,
            isolation=isolation,
        )
    
    def log_retry(
        self,
        attempt: int,
        max_attempts: int,
        error: str,
        delay_ms: float,
    ) -> None:
        """Log retry attempt."""
        self.log_event(
            LogEvent.RETRY_ATTEMPT,
            LogLevel.WARNING,
            f"Retry {attempt}/{max_attempts} after {error}",
            attempt=attempt,
            max_attempts=max_attempts,
            error=error,
            delay_ms=round(delay_ms, 2),
        )
    
    def log_circuit_breaker(
        self,
        opened: bool,
        failure_count: int,
        threshold: int,
    ) -> None:
        """Log circuit breaker state change."""
        event = LogEvent.CIRCUIT_OPENED if opened else LogEvent.CIRCUIT_CLOSED
        level = LogLevel.WARNING if opened else LogLevel.INFO
        self.log_event(
            event,
            level,
            f"Circuit breaker {'opened' if opened else 'closed'}",
            failure_count=failure_count,
            threshold=threshold,
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get logging statistics.
        
        Returns:
            Dictionary with logging stats
        """
        return {
            **self._stats,
            "config": {
                "level": self.config.level.value,
                "format": self.config.format.value,
                "slow_query_ms": self.config.slow_query_ms,
            },
        }
    
    def reset_stats(self) -> None:
        """Reset logging statistics."""
        self._stats = {
            "queries_logged": 0,
            "slow_queries": 0,
            "errors": 0,
        }


# ============================================================================
# Context Manager for Query Tracking
# ============================================================================

class QueryTracker:
    """Context manager for tracking query execution.
    
    Automatically creates and manages query context, timing,
    and logging for database operations.
    
    Example:
        logger = DBLogger(LogConfig())
        
        async with QueryTracker(logger, "SELECT * FROM users") as tracker:
            result = await execute_query(tracker.context.query)
            tracker.context.rows_returned = len(result)
        
        # Query is automatically logged when context exits
    """
    
    def __init__(
        self,
        db_logger: DBLogger,
        query: str,
        params: Optional[tuple] = None,
        pool_stats: Optional[Dict[str, Any]] = None,
    ):
        """Initialize query tracker.
        
        Args:
            db_logger: The database logger
            query: SQL query text
            params: Query parameters
            pool_stats: Current pool statistics
        """
        self.db_logger = db_logger
        self.context = QueryContext(
            query=query,
            params=params,
            pool_stats=pool_stats,
        )
        self._token = None
    
    async def __aenter__(self) -> "QueryTracker":
        """Enter async context."""
        self._token = _query_context.set(self.context)
        
        if self.db_logger.enabled:
            self.db_logger.log_event(
                LogEvent.QUERY_START,
                LogLevel.DEBUG,
                f"Starting query: {self.context.query_type or 'QUERY'}",
                context=self.context,
            )
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context."""
        # Finish timing
        if exc_val:
            self.context.finish(
                error=str(exc_val),
                error_type=type(exc_val).__name__,
            )
        else:
            self.context.finish()
        
        # Log the query
        self.db_logger.log_query(self.context)
        
        # Reset context var
        if self._token:
            _query_context.reset(self._token)
    
    def __enter__(self) -> "QueryTracker":
        """Enter sync context."""
        self._token = _query_context.set(self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit sync context."""
        if exc_val:
            self.context.finish(
                error=str(exc_val),
                error_type=type(exc_val).__name__,
            )
        else:
            self.context.finish()
        
        self.db_logger.log_query(self.context)
        
        if self._token:
            _query_context.reset(self._token)


def get_current_context() -> Optional[QueryContext]:
    """Get the current query context (if in a tracked query)."""
    return _query_context.get()


# ============================================================================
# Convenience Functions
# ============================================================================

def create_logger(
    level: Union[str, LogLevel] = LogLevel.INFO,
    format: Union[str, LogFormat] = LogFormat.TEXT,
    slow_query_ms: float = 100.0,
    **kwargs: Any,
) -> DBLogger:
    """Create a database logger with common options.
    
    Convenience function for creating a DBLogger with common settings.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format: Output format (text, json, structlog)
        slow_query_ms: Slow query threshold in milliseconds
        **kwargs: Additional LogConfig options
    
    Returns:
        Configured DBLogger instance
    
    Example:
        # Quick setup
        logger = create_logger(level="DEBUG", format="json")
        
        # With more options
        logger = create_logger(
            level="WARNING",
            format="json",
            slow_query_ms=50,
            log_params=False,
        )
    """
    if isinstance(level, str):
        level = LogLevel(level.upper())
    if isinstance(format, str):
        format = LogFormat(format.lower())
    
    config = LogConfig(
        level=level,
        format=format,
        slow_query_ms=slow_query_ms,
        **kwargs,
    )
    
    return DBLogger(config)


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # Configuration
    "LogConfig",
    "LogLevel",
    "LogFormat",
    "LogEvent",
    
    # Context
    "QueryContext",
    "QueryTracker",
    "get_current_context",
    "set_trace_id",
    "get_trace_id",
    "set_client_ip",
    "get_client_ip",
    
    # Logging
    "LogRecord",
    "DBLogger",
    "create_logger",
]

