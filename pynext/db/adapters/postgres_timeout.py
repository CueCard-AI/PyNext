"""
PostgreSQL Per-Query Timeout Management.

This module provides intelligent timeout management for database queries,
allowing different timeouts for different query types, tables, and patterns.

Why Per-Query Timeouts?

Not all queries are equal:
- Read queries should be fast (10s max)
- Write queries may take longer (60s)
- Analytics queries can run for minutes
- Health checks should be instant (1s)

Without per-query timeouts:
- One slow query can block others
- Timeout settings are one-size-fits-all
- No way to prioritize critical queries

With per-query timeouts:
- Fast queries fail fast
- Slow queries get time they need
- Critical queries are protected

How It Works:

1. TimeoutManager checks query against rules
2. Rules are checked in order: per-pattern → per-table → per-type → default
3. First match wins
4. Timeout is applied via asyncio.wait_for()

AI-Friendly Design:
- Clear configuration with dataclasses
- Predictable rule matching order
- Easy to extend with new patterns
- All timeouts are explicit
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Pattern, Tuple, TypeVar, Union

logger = logging.getLogger("pynext.db.postgres.timeout")

T = TypeVar("T")


class QueryType(Enum):
    """Standard query types for timeout classification.
    
    SELECT: Read queries
    INSERT: Create queries
    UPDATE: Modify queries
    DELETE: Remove queries
    DDL: Schema changes (CREATE TABLE, etc.)
    TRANSACTION: BEGIN, COMMIT, ROLLBACK
    OTHER: Anything else
    """
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    DDL = "ddl"
    TRANSACTION = "transaction"
    OTHER = "other"


@dataclass
class QueryTimeoutConfig:
    """Configuration for query timeouts.
    
    Attributes:
        default: Default timeout in seconds for unmatched queries.
                Default: 30.0
        per_type: Timeouts by query type (select, insert, update, delete).
                 Default: {} (use default for all types)
        per_table: Timeouts by table name.
                  Default: {} (no table-specific timeouts)
        per_pattern: Timeouts by regex pattern matching the query.
                    Default: {} (no pattern-specific timeouts)
        enabled: Whether timeout management is enabled.
                Default: True
    
    Example:
        # Simple: just a default
        config = QueryTimeoutConfig(default=30.0)
        
        # Per-type timeouts
        config = QueryTimeoutConfig(
            default=30.0,
            per_type={
                "select": 10.0,   # Fast reads
                "insert": 60.0,   # Slower writes
                "update": 60.0,
                "delete": 30.0,
            },
        )
        
        # Full control
        config = QueryTimeoutConfig(
            default=30.0,
            per_type={"select": 10.0, "insert": 60.0},
            per_table={
                "large_table": 120.0,    # Big table needs time
                "cache_table": 5.0,      # Cache should be fast
            },
            per_pattern={
                r"SELECT.*analytics": 300.0,  # Analytics queries
                r"INSERT.*bulk": 600.0,       # Bulk inserts
            },
        )
    """
    default: float = 30.0
    per_type: Dict[str, float] = field(default_factory=dict)
    per_table: Dict[str, float] = field(default_factory=dict)
    per_pattern: Dict[str, float] = field(default_factory=dict)
    enabled: bool = True
    
    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.default < 0:
            raise ValueError(f"default timeout must be >= 0, got {self.default}")
        
        for key, value in self.per_type.items():
            if value < 0:
                raise ValueError(f"per_type[{key}] timeout must be >= 0, got {value}")
        
        for key, value in self.per_table.items():
            if value < 0:
                raise ValueError(f"per_table[{key}] timeout must be >= 0, got {value}")
        
        for key, value in self.per_pattern.items():
            if value < 0:
                raise ValueError(f"per_pattern[{key}] timeout must be >= 0, got {value}")


@dataclass
class QueryWithTimeout:
    """A query bundled with its timeout.
    
    Attributes:
        query: The SQL query string
        timeout: Timeout in seconds
        query_type: Detected query type
        matched_rule: Which rule matched (for debugging)
    """
    query: str
    timeout: float
    query_type: QueryType = QueryType.OTHER
    matched_rule: str = "default"
    
    def __repr__(self) -> str:
        return (
            f"QueryWithTimeout(timeout={self.timeout}s, "
            f"type={self.query_type.value}, rule={self.matched_rule})"
        )


class QueryTimeoutError(asyncio.TimeoutError):
    """Raised when a query exceeds its timeout.
    
    Attributes:
        query: The query that timed out
        timeout: The timeout that was exceeded
        elapsed: Actual time elapsed
        query_type: Type of query
    """
    
    def __init__(
        self,
        query: str,
        timeout: float,
        elapsed: float,
        query_type: QueryType = QueryType.OTHER,
    ):
        self.query = query
        self.timeout = timeout
        self.elapsed = elapsed
        self.query_type = query_type
        
        # Truncate query for display
        display_query = query[:100] + "..." if len(query) > 100 else query
        
        super().__init__(
            f"Query timed out after {elapsed:.2f}s (limit: {timeout}s)\n"
            f"Query type: {query_type.value}\n"
            f"Query: {display_query}"
        )


@dataclass
class TimeoutStats:
    """Statistics about timeout behavior.
    
    Attributes:
        total_queries: Total queries processed
        timeouts: Number of queries that timed out
        by_type: Counts by query type
        by_rule: Counts by which rule matched
        avg_timeout_ms: Average timeout applied
    """
    total_queries: int = 0
    timeouts: int = 0
    by_type: Dict[str, int] = field(default_factory=dict)
    by_rule: Dict[str, int] = field(default_factory=dict)
    total_timeout_ms: float = 0
    
    @property
    def timeout_rate(self) -> float:
        """Fraction of queries that timed out."""
        if self.total_queries == 0:
            return 0.0
        return self.timeouts / self.total_queries
    
    @property
    def avg_timeout_ms(self) -> float:
        """Average timeout applied in milliseconds."""
        if self.total_queries == 0:
            return 0.0
        return self.total_timeout_ms / self.total_queries
    
    def record_query(self, query_type: QueryType, rule: str, timeout: float) -> None:
        """Record a query execution."""
        self.total_queries += 1
        self.total_timeout_ms += timeout * 1000
        
        type_name = query_type.value
        self.by_type[type_name] = self.by_type.get(type_name, 0) + 1
        self.by_rule[rule] = self.by_rule.get(rule, 0) + 1
    
    def record_timeout(self) -> None:
        """Record a timeout event."""
        self.timeouts += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/metrics."""
        return {
            "total_queries": self.total_queries,
            "timeouts": self.timeouts,
            "timeout_rate": self.timeout_rate,
            "avg_timeout_ms": self.avg_timeout_ms,
            "by_type": self.by_type.copy(),
            "by_rule": self.by_rule.copy(),
        }


class TimeoutManager:
    """Manages per-query timeouts.
    
    This class determines the appropriate timeout for each query based on:
    1. Pattern matching (regex against query)
    2. Table name extraction
    3. Query type detection (SELECT, INSERT, etc.)
    4. Default timeout
    
    Rules are checked in this order, first match wins.
    
    Basic Usage:
        manager = TimeoutManager(QueryTimeoutConfig(default=30.0))
        
        # Get timeout for a query
        timeout = manager.get_timeout("SELECT * FROM users")
        
        # Get query with timeout bundled
        qt = manager.with_timeout("SELECT * FROM users")
        print(f"Timeout: {qt.timeout}s, Rule: {qt.matched_rule}")
    
    With Execution:
        # Execute with automatic timeout
        result = await manager.execute_with_timeout(
            "SELECT * FROM users",
            executor=lambda q: conn.fetch(q),
        )
    
    Per-Type Configuration:
        manager = TimeoutManager(QueryTimeoutConfig(
            default=30.0,
            per_type={"select": 10.0, "insert": 60.0},
        ))
        
        manager.get_timeout("SELECT * FROM users")  # 10.0s
        manager.get_timeout("INSERT INTO users ...")  # 60.0s
    """
    
    # Patterns for detecting query type
    _TYPE_PATTERNS = [
        (re.compile(r"^\s*SELECT\b", re.IGNORECASE), QueryType.SELECT),
        (re.compile(r"^\s*INSERT\b", re.IGNORECASE), QueryType.INSERT),
        (re.compile(r"^\s*UPDATE\b", re.IGNORECASE), QueryType.UPDATE),
        (re.compile(r"^\s*DELETE\b", re.IGNORECASE), QueryType.DELETE),
        (re.compile(r"^\s*(CREATE|ALTER|DROP|TRUNCATE)\b", re.IGNORECASE), QueryType.DDL),
        (re.compile(r"^\s*(BEGIN|COMMIT|ROLLBACK|SAVEPOINT)\b", re.IGNORECASE), QueryType.TRANSACTION),
    ]
    
    # Pattern for extracting table name
    _TABLE_PATTERN = re.compile(
        r"(?:FROM|INTO|UPDATE|JOIN|TABLE)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
        re.IGNORECASE,
    )
    
    def __init__(self, config: Optional[QueryTimeoutConfig] = None):
        """Initialize the timeout manager.
        
        Args:
            config: Timeout configuration (default: QueryTimeoutConfig())
        """
        self._config = config or QueryTimeoutConfig()
        self._stats = TimeoutStats()
        
        # Compile patterns for efficiency
        self._compiled_patterns: List[Tuple[Pattern, float]] = []
        for pattern, timeout in self._config.per_pattern.items():
            try:
                compiled = re.compile(pattern, re.IGNORECASE)
                self._compiled_patterns.append((compiled, timeout))
            except re.error as e:
                logger.warning(f"Invalid pattern '{pattern}': {e}")
    
    @property
    def config(self) -> QueryTimeoutConfig:
        """Get current configuration."""
        return self._config
    
    @property
    def stats(self) -> TimeoutStats:
        """Get timeout statistics."""
        return self._stats
    
    def detect_query_type(self, query: str) -> QueryType:
        """Detect the type of a SQL query.
        
        Args:
            query: SQL query string
        
        Returns:
            QueryType enum value
        
        Example:
            manager.detect_query_type("SELECT * FROM users")
            # Returns: QueryType.SELECT
        """
        for pattern, query_type in self._TYPE_PATTERNS:
            if pattern.match(query):
                return query_type
        return QueryType.OTHER
    
    def extract_table(self, query: str) -> Optional[str]:
        """Extract the primary table name from a query.
        
        Args:
            query: SQL query string
        
        Returns:
            Table name or None if not found
        
        Example:
            manager.extract_table("SELECT * FROM users WHERE id = 1")
            # Returns: "users"
        """
        match = self._TABLE_PATTERN.search(query)
        if match:
            return match.group(1).lower()
        return None
    
    def get_timeout(
        self,
        query: str,
        query_type: Optional[QueryType] = None,
        override: Optional[float] = None,
    ) -> float:
        """Get the timeout for a query.
        
        Checks rules in order: override → pattern → table → type → default.
        
        Args:
            query: SQL query string
            query_type: Override auto-detected query type
            override: Explicit timeout override (highest priority)
        
        Returns:
            Timeout in seconds
        
        Example:
            timeout = manager.get_timeout("SELECT * FROM users")
        """
        if not self._config.enabled:
            return self._config.default
        
        # Explicit override has highest priority
        if override is not None:
            return override
        
        # Check pattern rules first
        for pattern, timeout in self._compiled_patterns:
            if pattern.search(query):
                return timeout
        
        # Check table-specific rules
        table = self.extract_table(query)
        if table and table in self._config.per_table:
            return self._config.per_table[table]
        
        # Check type-specific rules
        detected_type = query_type or self.detect_query_type(query)
        type_key = detected_type.value
        if type_key in self._config.per_type:
            return self._config.per_type[type_key]
        
        # Fall back to default
        return self._config.default
    
    def with_timeout(
        self,
        query: str,
        timeout: Optional[float] = None,
    ) -> QueryWithTimeout:
        """Bundle a query with its timeout information.
        
        Args:
            query: SQL query string
            timeout: Override timeout (optional)
        
        Returns:
            QueryWithTimeout with query, timeout, and metadata
        
        Example:
            qt = manager.with_timeout("SELECT * FROM users")
            print(f"Will wait {qt.timeout}s for this query")
        """
        query_type = self.detect_query_type(query)
        matched_rule = "override" if timeout is not None else self._determine_rule(query, query_type)
        final_timeout = timeout if timeout is not None else self.get_timeout(query, query_type)
        
        # Record for statistics
        self._stats.record_query(query_type, matched_rule, final_timeout)
        
        return QueryWithTimeout(
            query=query,
            timeout=final_timeout,
            query_type=query_type,
            matched_rule=matched_rule,
        )
    
    async def execute_with_timeout(
        self,
        query: str,
        executor: Callable[[str], Any],
        timeout: Optional[float] = None,
    ) -> Any:
        """Execute a query with automatic timeout.
        
        Args:
            query: SQL query string
            executor: Async function to execute the query
            timeout: Override timeout (optional)
        
        Returns:
            Result from executor
        
        Raises:
            QueryTimeoutError: If query exceeds timeout
        
        Example:
            result = await manager.execute_with_timeout(
                "SELECT * FROM users",
                executor=lambda q: conn.fetch(q),
            )
        """
        qt = self.with_timeout(query, timeout)
        start_time = time.monotonic()
        
        try:
            if asyncio.iscoroutinefunction(executor):
                result = await asyncio.wait_for(
                    executor(query),
                    timeout=qt.timeout,
                )
            else:
                # Handle sync executor
                result = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, executor, query),
                    timeout=qt.timeout,
                )
            return result
            
        except asyncio.TimeoutError:
            elapsed = time.monotonic() - start_time
            self._stats.record_timeout()
            
            logger.warning(
                f"Query timed out after {elapsed:.2f}s (limit: {qt.timeout}s), "
                f"type: {qt.query_type.value}, rule: {qt.matched_rule}"
            )
            
            raise QueryTimeoutError(
                query=query,
                timeout=qt.timeout,
                elapsed=elapsed,
                query_type=qt.query_type,
            )
    
    def _determine_rule(self, query: str, query_type: QueryType) -> str:
        """Determine which rule matched for a query."""
        # Check pattern rules
        for pattern, _ in self._compiled_patterns:
            if pattern.search(query):
                return f"pattern:{pattern.pattern}"
        
        # Check table rules
        table = self.extract_table(query)
        if table and table in self._config.per_table:
            return f"table:{table}"
        
        # Check type rules
        type_key = query_type.value
        if type_key in self._config.per_type:
            return f"type:{type_key}"
        
        return "default"
    
    def reset_stats(self) -> None:
        """Reset statistics."""
        self._stats = TimeoutStats()
    
    def get_stats(self) -> TimeoutStats:
        """Get current statistics."""
        return self._stats
    
    def __repr__(self) -> str:
        return (
            f"TimeoutManager(default={self._config.default}s, "
            f"types={len(self._config.per_type)}, "
            f"tables={len(self._config.per_table)}, "
            f"patterns={len(self._config.per_pattern)})"
        )


# =============================================================================
# Convenience Functions
# =============================================================================

def quick_timeout_config() -> QueryTimeoutConfig:
    """Create a quick timeout configuration for real-time apps.
    
    - Default: 10s
    - Selects: 5s
    - Everything else: 10s
    
    Returns:
        QueryTimeoutConfig for real-time apps
    """
    return QueryTimeoutConfig(
        default=10.0,
        per_type={
            "select": 5.0,
            "insert": 10.0,
            "update": 10.0,
            "delete": 10.0,
        },
    )


def standard_timeout_config() -> QueryTimeoutConfig:
    """Create a standard timeout configuration.
    
    - Default: 30s
    - Selects: 15s
    - Writes: 30s
    - DDL: 60s
    
    Returns:
        QueryTimeoutConfig for standard apps
    """
    return QueryTimeoutConfig(
        default=30.0,
        per_type={
            "select": 15.0,
            "insert": 30.0,
            "update": 30.0,
            "delete": 30.0,
            "ddl": 60.0,
        },
    )


def batch_timeout_config() -> QueryTimeoutConfig:
    """Create a timeout configuration for batch processing.
    
    - Default: 120s
    - Selects: 60s
    - Writes: 120s
    - DDL: 300s
    
    Returns:
        QueryTimeoutConfig for batch processing
    """
    return QueryTimeoutConfig(
        default=120.0,
        per_type={
            "select": 60.0,
            "insert": 120.0,
            "update": 120.0,
            "delete": 120.0,
            "ddl": 300.0,
        },
    )


def no_timeout_config() -> QueryTimeoutConfig:
    """Create a configuration that effectively disables timeouts.
    
    Uses a very large default (1 hour).
    
    Returns:
        QueryTimeoutConfig with disabled timeouts
    """
    return QueryTimeoutConfig(
        default=3600.0,
        enabled=False,
    )

