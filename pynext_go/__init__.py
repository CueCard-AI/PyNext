"""
PyNext Go Bridge - High Performance Database Layer.

This package provides a Go-powered database execution engine that delivers
true parallelism and zero-copy data transfer via Apache Arrow.

Installation:
    pip install pynext-go  # Includes pre-built Go binaries

Quick Start:
    from pynext_go import GoBridge, BridgeConfig
    
    # Initialize the bridge
    bridge = GoBridge()
    bridge.init(BridgeConfig(
        primary="postgresql://user:pass@localhost/db",
        pool_min_size=2,
        pool_max_size=10,
    ))
    
    # Execute queries
    result = bridge.execute("SELECT * FROM users WHERE age > $1", [18])
    print(result.rows)
    
    # Check health
    health = bridge.health()
    print(health.status)  # "healthy", "degraded", or "unhealthy"
    
    # Cleanup
    bridge.close()

Auto-detection:
    The bridge automatically detects if the Go library is available.
    If not, queries fall back to asyncpg with a warning.
    
    # Check availability
    from pynext_go import GO_AVAILABLE
    if GO_AVAILABLE:
        print("Go bridge loaded!")
    else:
        print("Using asyncpg fallback")

Performance:
    - 2-5x faster than asyncpg for typical queries
    - Zero-copy Arrow results for DataFrame operations
    - True parallel query execution (bypasses GIL)
    - Connection pooling managed by Go
"""

from __future__ import annotations

__version__ = "0.1.0"

# Check if Go library is available
from pynext_go.bridge import (
    GoBridge,
    GO_AVAILABLE,
    GO_LIBRARY_PATH,
    GoNotAvailableError,
    QueryBatch,
    DeferredResult,
)

from pynext_go.config import (
    BridgeConfig,
    DEFAULT_POOL_MIN,
    DEFAULT_POOL_MAX,
    DEFAULT_QUERY_TIMEOUT,
)

from pynext_go.health import (
    HealthStatus,
    ConnectionHealth,
    PoolHealth,
)

from pynext_go.result import (
    QueryResult,
    BatchResult,
)

from pynext_go.errors import (
    BridgeError,
    BridgeConfigError,
    BridgeConnectionError,
    BridgeQueryError,
    BridgeTimeoutError,
    BridgePoolError,
    BridgeArrowError,
)

# Singleton bridge instance for convenience
_default_bridge: GoBridge | None = None


def init(
    primary: str,
    *,
    replicas: list[str] | None = None,
    pool_min_size: int = DEFAULT_POOL_MIN,
    pool_max_size: int = DEFAULT_POOL_MAX,
    query_timeout: int = DEFAULT_QUERY_TIMEOUT,
    **kwargs,
) -> GoBridge:
    """
    Initialize the global Go bridge.
    
    This is a convenience function that creates a singleton bridge instance.
    For more control, create a GoBridge instance directly.
    
    Args:
        primary: Primary database connection string
        replicas: Optional list of read replica connection strings
        pool_min_size: Minimum connections in pool (default: 2)
        pool_max_size: Maximum connections in pool (default: 10)
        query_timeout: Default query timeout in ms (default: 30000)
        **kwargs: Additional config options
        
    Returns:
        The initialized GoBridge instance
        
    Raises:
        BridgeConfigError: Invalid configuration
        BridgeConnectionError: Failed to connect to database
        
    Example:
        import pynext_go
        
        pynext_go.init("postgresql://localhost/mydb")
        result = pynext_go.execute("SELECT 1")
    """
    global _default_bridge
    
    if _default_bridge is not None:
        _default_bridge.close()
    
    config = BridgeConfig(
        primary=primary,
        replicas=replicas or [],
        pool_min_size=pool_min_size,
        pool_max_size=pool_max_size,
        query_timeout=query_timeout,
        **kwargs,
    )
    
    _default_bridge = GoBridge()
    _default_bridge.init(config)
    return _default_bridge


def execute(sql: str, params: list | None = None, **kwargs) -> QueryResult:
    """
    Execute a query using the global bridge.
    
    Args:
        sql: SQL query with $1, $2, ... placeholders
        params: Query parameters
        **kwargs: Additional options (timeout_ms, use_replica, etc.)
        
    Returns:
        QueryResult with rows and metadata
        
    Raises:
        BridgeError: If bridge not initialized or query fails
        
    Example:
        result = pynext_go.execute(
            "SELECT * FROM users WHERE age > $1",
            [18]
        )
        for row in result.rows:
            print(row)
    """
    if _default_bridge is None:
        raise BridgeError("Go bridge not initialized - call pynext_go.init() first")
    return _default_bridge.execute(sql, params or [], **kwargs)


def execute_fast(sql: str, params: list | None = None, **kwargs) -> QueryResult:
    """
    Execute using pinned connection (2-3x faster for small queries).
    
    Best for repeated small queries (API endpoints).
    """
    if _default_bridge is None:
        raise BridgeError("Go bridge not initialized - call pynext_go.init() first")
    return _default_bridge.execute_fast(sql, params or [], **kwargs)


async def execute_fast_async(sql: str, params: list | None = None, **kwargs) -> QueryResult:
    """Async version of execute_fast."""
    if _default_bridge is None:
        raise BridgeError("Go bridge not initialized - call pynext_go.init() first")
    return await _default_bridge.execute_fast_async(sql, params or [], **kwargs)


def execute_batch(queries: list[tuple[str, list]], **kwargs) -> BatchResult:
    """
    Execute multiple queries efficiently.
    
    Args:
        queries: List of (sql, params) tuples
        **kwargs: Additional options (transaction, stop_on_error, etc.)
        
    Returns:
        BatchResult with individual results
        
    Example:
        result = pynext_go.execute_batch([
            ("INSERT INTO users (name) VALUES ($1)", ["Alice"]),
            ("INSERT INTO users (name) VALUES ($1)", ["Bob"]),
        ], transaction=True)
    """
    if _default_bridge is None:
        raise BridgeError("Go bridge not initialized - call pynext_go.init() first")
    return _default_bridge.execute_batch(queries, **kwargs)


def health() -> HealthStatus:
    """
    Get the health status of the Go bridge.
    
    Returns:
        HealthStatus with primary, replica, and pool health
        
    Example:
        health = pynext_go.health()
        if health.status != "healthy":
            print(f"Warning: {health.primary.error}")
    """
    if _default_bridge is None:
        raise BridgeError("Go bridge not initialized - call pynext_go.init() first")
    return _default_bridge.health()


def close() -> None:
    """
    Close the global Go bridge and release resources.
    
    Safe to call multiple times.
    """
    global _default_bridge
    if _default_bridge is not None:
        _default_bridge.close()
        _default_bridge = None


def warmup() -> None:
    """
    Warm up the connection pool.
    
    Creates min_size connections in advance to avoid
    cold start latency on first queries.
    
    Example:
        pynext_go.init("postgresql://localhost/mydb")
        pynext_go.warmup()  # Pre-create connections
    """
    if _default_bridge is None:
        raise BridgeError("Go bridge not initialized - call pynext_go.init() first")
    _default_bridge.warmup()


# =============================================================================
# Query Builder API (Phase 8.2)
# =============================================================================


def execute_query(ast_json: str | bytes) -> QueryResult:
    """
    Execute a query from an AST JSON.
    
    This is the main entry point for the new query builder API.
    Called internally by QueryBuilder.
    
    Args:
        ast_json: Query AST as JSON string (from QueryBuilder.to_dict())
        
    Returns:
        QueryResult with rows and metadata
        
    Example:
        import json
        ast = {
            "table": "users",
            "type": "SELECT",
            "conditions": {"type": "condition", "field": "age", "op": ">", "value": 18}
        }
        result = pynext_go.execute_query(json.dumps(ast))
    """
    if _default_bridge is None:
        raise BridgeError("Go bridge not initialized - call pynext_go.init() first")
    return _default_bridge.execute_query(ast_json)


def query_explain(ast_json: str | bytes) -> dict:
    """
    Get generated SQL without executing.
    
    Useful for debugging and testing query generation.
    
    Args:
        ast_json: Query AST as JSON string
        
    Returns:
        Dict with 'sql' and 'params' keys
        
    Example:
        result = pynext_go.query_explain(json.dumps(ast))
        print(result["sql"])    # SELECT * FROM "users" WHERE "age" > $1
        print(result["params"]) # [18]
    """
    if _default_bridge is None:
        raise BridgeError("Go bridge not initialized - call pynext_go.init() first")
    return _default_bridge.query_explain(ast_json)


def query_validate(ast_json: str | bytes) -> bool:
    """
    Validate a query AST without executing.
    
    Args:
        ast_json: Query AST as JSON string
        
    Returns:
        True if valid
        
    Raises:
        BridgeQueryError: If validation fails (includes error message)
        
    Example:
        try:
            pynext_go.query_validate(json.dumps(ast))
            print("Query is valid!")
        except BridgeQueryError as e:
            print(f"Invalid query: {e}")
    """
    if _default_bridge is None:
        raise BridgeError("Go bridge not initialized - call pynext_go.init() first")
    return _default_bridge.query_validate(ast_json)


# =============================================================================
# Async API
# =============================================================================


async def execute_async(sql: str, params: list | None = None, **kwargs) -> QueryResult:
    """
    Execute a query asynchronously using the global bridge.
    
    This runs the query in a thread pool to avoid blocking the event loop.
    
    Args:
        sql: SQL query with $1, $2, ... placeholders
        params: Query parameters
        **kwargs: Additional options (timeout_ms, use_replica, etc.)
        
    Returns:
        QueryResult with rows and metadata
        
    Example:
        result = await pynext_go.execute_async(
            "SELECT * FROM users WHERE age > $1",
            [18]
        )
    """
    if _default_bridge is None:
        raise BridgeError("Go bridge not initialized - call pynext_go.init() first")
    return await _default_bridge.execute_async(sql, params or [], **kwargs)


async def execute_batch_async(queries: list[tuple[str, list]], **kwargs) -> BatchResult:
    """
    Execute multiple queries asynchronously.
    
    Args:
        queries: List of (sql, params) tuples
        **kwargs: Additional options (transaction, stop_on_error, etc.)
        
    Returns:
        BatchResult with individual results
        
    Example:
        result = await pynext_go.execute_batch_async([
            ("INSERT INTO users (name) VALUES ($1)", ["Alice"]),
            ("INSERT INTO users (name) VALUES ($1)", ["Bob"]),
        ], transaction=True)
    """
    if _default_bridge is None:
        raise BridgeError("Go bridge not initialized - call pynext_go.init() first")
    return await _default_bridge.execute_batch_async(queries, **kwargs)


async def health_async() -> HealthStatus:
    """
    Get the health status of the Go bridge asynchronously.
    
    Returns:
        HealthStatus with primary, replica, and pool health
    """
    if _default_bridge is None:
        raise BridgeError("Go bridge not initialized - call pynext_go.init() first")
    return await _default_bridge.health_async()


async def warmup_async() -> None:
    """
    Warm up the connection pool asynchronously.
    
    Example:
        pynext_go.init("postgresql://localhost/mydb")
        await pynext_go.warmup_async()
    """
    if _default_bridge is None:
        raise BridgeError("Go bridge not initialized - call pynext_go.init() first")
    await _default_bridge.warmup_async()


def execute_parallel(queries: list[tuple[str, list]]) -> list[QueryResult]:
    """
    Execute multiple queries in parallel using the global bridge.
    
    Each query runs in its own goroutine with its own connection.
    This is the fastest way to execute independent queries.
    
    Args:
        queries: List of (sql, params) tuples
        
    Returns:
        List of QueryResult in same order as input
        
    Example:
        results = pynext_go.execute_parallel([
            ("SELECT * FROM users", []),
            ("SELECT * FROM orders WHERE user_id = $1", [123]),
            ("SELECT COUNT(*) FROM products", []),
        ])
        users, orders, product_count = results
    """
    if _default_bridge is None:
        raise BridgeError("Go bridge not initialized - call pynext_go.init() first")
    return _default_bridge.execute_parallel(queries)


async def execute_parallel_async(queries: list[tuple[str, list]]) -> list[QueryResult]:
    """
    Execute multiple queries in parallel asynchronously.
    
    Each query runs in its own goroutine with its own connection.
    This is the fastest way to execute independent queries.
    
    Args:
        queries: List of (sql, params) tuples
        
    Returns:
        List of QueryResult in same order as input
        
    Example:
        results = await pynext_go.execute_parallel_async([
            ("SELECT * FROM users", []),
            ("SELECT * FROM orders", []),
        ])
    """
    if _default_bridge is None:
        raise BridgeError("Go bridge not initialized - call pynext_go.init() first")
    return await _default_bridge.execute_parallel_async(queries)


def batch() -> QueryBatch:
    """
    Create a batch context for parallel query execution.
    
    Queries added to the batch are executed in parallel when
    the context exits. This provides 2-3x speedup for typical
    API endpoints that make multiple independent database calls.
    
    Example:
        with pynext_go.batch() as b:
            user = b.query("SELECT * FROM users WHERE id = $1", [user_id])
            orders = b.query("SELECT * FROM orders WHERE user_id = $1", [user_id])
            notifications = b.query("SELECT * FROM notifications WHERE user_id = $1", [user_id])
        
        # All 3 queries executed in parallel!
        return {
            "user": user.rows[0],
            "orders": orders.rows,
            "notifications": notifications.rows
        }
    
    Async usage:
        async with pynext_go.batch() as b:
            user = b.query("SELECT * FROM users WHERE id = $1", [user_id])
            orders = b.query("SELECT * FROM orders WHERE user_id = $1", [user_id])
        
        return {"user": user.rows, "orders": orders.rows}
    
    Returns:
        QueryBatch context manager
    """
    if _default_bridge is None:
        raise BridgeError("Go bridge not initialized - call pynext_go.init() first")
    return _default_bridge.batch()


def execute_arrow(sql: str, params: list | None = None):
    """
    Execute query and return results as PyArrow Table.
    
    This is the fastest path for large result sets - zero-copy
    transfer from Go to Python via Arrow IPC.
    
    Args:
        sql: SQL query string
        params: Query parameters
        
    Returns:
        PyArrow Table
        
    Example:
        table = pynext_go.execute_arrow("SELECT * FROM orders", [])
        df = table.to_pandas()  # Zero-copy!
        
        # For JSON to frontend:
        import orjson
        json_bytes = orjson.dumps(table.to_pydict())
    """
    if _default_bridge is None:
        raise BridgeError("Go bridge not initialized - call pynext_go.init() first")
    return _default_bridge.execute_arrow(sql, params)


async def execute_arrow_async(sql: str, params: list | None = None):
    """
    Execute query and return results as PyArrow Table asynchronously.
    
    Args:
        sql: SQL query string
        params: Query parameters
        
    Returns:
        PyArrow Table
        
    Example:
        table = await pynext_go.execute_arrow_async("SELECT * FROM orders", [])
        df = table.to_pandas()
    """
    if _default_bridge is None:
        raise BridgeError("Go bridge not initialized - call pynext_go.init() first")
    return await _default_bridge.execute_arrow_async(sql, params)


def execute_copy(sql: str) -> bytes:
    """
    Execute query using COPY protocol - fastest for bulk reads.
    
    Returns CSV data that can be parsed with pandas/pyarrow.
    This is 2x faster than asyncpg for large result sets (10K+ rows).
    
    Args:
        sql: SQL query string
        
    Returns:
        CSV bytes with header row
        
    Example:
        csv_data = pynext_go.execute_copy("SELECT * FROM orders LIMIT 10000")
        
        # Parse with pandas
        import pandas as pd
        import io
        df = pd.read_csv(io.BytesIO(csv_data))
        
        # Or parse with pyarrow (faster)
        import pyarrow.csv as pa_csv
        table = pa_csv.read_csv(io.BytesIO(csv_data))
    """
    if _default_bridge is None:
        raise BridgeError("Go bridge not initialized - call pynext_go.init() first")
    return _default_bridge.execute_copy(sql)


def execute_copy_df(sql: str):
    """
    Execute COPY and return as pandas DataFrame.
    
    This is the fastest way to get query results into a DataFrame.
    2-3x faster than asyncpg for large result sets.
    
    Args:
        sql: SQL query string
        
    Returns:
        pandas DataFrame
        
    Example:
        df = pynext_go.execute_copy_df("SELECT * FROM orders WHERE status = 'pending'")
        print(df.describe())
    """
    if _default_bridge is None:
        raise BridgeError("Go bridge not initialized - call pynext_go.init() first")
    return _default_bridge.execute_copy_df(sql)


def execute_copy_rows(sql: str) -> list[dict]:
    """
    Execute COPY and return as list of dictionaries.
    
    Fastest way to get bulk data as Python dicts (for JSON APIs).
    2-3x faster than asyncpg for 1000+ rows.
    
    Args:
        sql: SQL query string
        
    Returns:
        List of dictionaries (one per row)
        
    Example:
        rows = pynext_go.execute_copy_rows("SELECT * FROM orders LIMIT 5000")
        return jsonify({"orders": rows})  # Ready for API response
    """
    if _default_bridge is None:
        raise BridgeError("Go bridge not initialized - call pynext_go.init() first")
    return _default_bridge.execute_copy_rows(sql)


# =============================================================================
# DataFrame API (Phase 8.3)
# =============================================================================


def execute_polars(sql: str, params: list | None = None):
    """
    Execute query and return results as Polars DataFrame.
    
    Uses zero-copy conversion from Arrow for maximum performance.
    This is the fastest path for Polars DataFrames.
    
    Args:
        sql: SQL query string
        params: Query parameters
        
    Returns:
        Polars DataFrame
        
    Example:
        import pynext_go
        
        df = pynext_go.execute_polars("SELECT * FROM users WHERE age > $1", [18])
        
        # Polars operations
        result = (df
            .filter(pl.col("status") == "active")
            .group_by("role")
            .agg(pl.count())
        )
        
    Performance:
        - Zero-copy from Arrow (instant conversion)
        - 2-3x faster than asyncpg + manual conversion
    """
    if _default_bridge is None:
        raise BridgeError("Go bridge not initialized - call pynext_go.init() first")
    return _default_bridge.execute_polars(sql, params)


async def execute_polars_async(sql: str, params: list | None = None):
    """
    Execute query and return Polars DataFrame asynchronously.
    
    Args:
        sql: SQL query string
        params: Query parameters
        
    Returns:
        Polars DataFrame
        
    Example:
        df = await pynext_go.execute_polars_async("SELECT * FROM orders", [])
    """
    if _default_bridge is None:
        raise BridgeError("Go bridge not initialized - call pynext_go.init() first")
    return await _default_bridge.execute_polars_async(sql, params)


def execute_numpy(sql: str, params: list | None = None, zero_copy: bool = True) -> dict:
    """
    Execute query and return results as column-wise NumPy arrays.
    
    Returns a dictionary mapping column names to NumPy arrays.
    This is the best format for vectorized operations and analytics.
    
    Args:
        sql: SQL query string
        params: Query parameters
        zero_copy: Attempt zero-copy for numeric columns (default True)
        
    Returns:
        Dictionary mapping column names to NumPy arrays
        
    Example:
        import pynext_go
        import numpy as np
        
        arrays = pynext_go.execute_numpy("SELECT id, score FROM users", [])
        
        # Vectorized operations
        mean_score = np.mean(arrays["score"])
        high_scorers = arrays["id"][arrays["score"] > 90]
        
    Performance:
        - Numeric columns: Zero-copy (instant)
        - String columns: O(n) copy required
    """
    if _default_bridge is None:
        raise BridgeError("Go bridge not initialized - call pynext_go.init() first")
    return _default_bridge.execute_numpy(sql, params, zero_copy)


async def execute_numpy_async(
    sql: str, params: list | None = None, zero_copy: bool = True
) -> dict:
    """
    Execute query and return column-wise NumPy arrays asynchronously.
    
    Args:
        sql: SQL query string
        params: Query parameters
        zero_copy: Attempt zero-copy for numeric columns
        
    Returns:
        Dictionary mapping column names to NumPy arrays
        
    Example:
        arrays = await pynext_go.execute_numpy_async("SELECT * FROM data", [])
    """
    if _default_bridge is None:
        raise BridgeError("Go bridge not initialized - call pynext_go.init() first")
    return await _default_bridge.execute_numpy_async(sql, params, zero_copy)


def execute_numpy_structured(
    sql: str, params: list | None = None, max_string_length: int = 256
):
    """
    Execute query and return results as a NumPy structured array.
    
    Returns a single NumPy array where each row is a record with
    named fields. Useful for row-oriented access patterns.
    
    Args:
        sql: SQL query string
        params: Query parameters
        max_string_length: Max length for fixed-width string fields
            
    Returns:
        NumPy structured array
        
    Example:
        import pynext_go
        
        arr = pynext_go.execute_numpy_structured("SELECT id, name, score FROM users", [])
        
        # Access by field name
        print(arr["name"])    # array(['Alice', 'Bob', 'Charlie'])
        
        # Access by row index
        print(arr[0])         # (1, 'Alice', 95.5)
        
        # Iterate over rows
        for row in arr:
            print(f"{row['name']}: {row['score']}")
    """
    if _default_bridge is None:
        raise BridgeError("Go bridge not initialized - call pynext_go.init() first")
    return _default_bridge.execute_numpy_structured(sql, params, max_string_length)


async def execute_numpy_structured_async(
    sql: str, params: list | None = None, max_string_length: int = 256
):
    """
    Execute query and return structured NumPy array asynchronously.
    
    Args:
        sql: SQL query string
        params: Query parameters
        max_string_length: Max length for fixed-width string fields
        
    Returns:
        NumPy structured array
        
    Example:
        arr = await pynext_go.execute_numpy_structured_async("SELECT * FROM users", [])
    """
    if _default_bridge is None:
        raise BridgeError("Go bridge not initialized - call pynext_go.init() first")
    return await _default_bridge.execute_numpy_structured_async(sql, params, max_string_length)


def execute_pandas(sql: str, params: list | None = None):
    """
    Execute query and return results as pandas DataFrame.
    
    Uses Arrow for efficient conversion. Faster than asyncpg + manual
    DataFrame creation.
    
    Args:
        sql: SQL query string
        params: Query parameters
        
    Returns:
        pandas DataFrame
        
    Example:
        import pynext_go
        
        df = pynext_go.execute_pandas("SELECT * FROM users WHERE active = $1", [True])
        print(df.describe())
        print(df.groupby("role").count())
        
    Performance:
        - Uses Arrow's optimized to_pandas() conversion
        - 1.5-2x faster than asyncpg for large results
        
    Note:
        For maximum performance, consider execute_polars() if you can
        use Polars instead of pandas.
    """
    if _default_bridge is None:
        raise BridgeError("Go bridge not initialized - call pynext_go.init() first")
    return _default_bridge.execute_pandas(sql, params)


async def execute_pandas_async(sql: str, params: list | None = None):
    """
    Execute query and return pandas DataFrame asynchronously.
    
    Args:
        sql: SQL query string
        params: Query parameters
        
    Returns:
        pandas DataFrame
        
    Example:
        df = await pynext_go.execute_pandas_async("SELECT * FROM orders", [])
    """
    if _default_bridge is None:
        raise BridgeError("Go bridge not initialized - call pynext_go.init() first")
    return await _default_bridge.execute_pandas_async(sql, params)


__all__ = [
    # Version
    "__version__",
    
    # Availability
    "GO_AVAILABLE",
    "GO_LIBRARY_PATH",
    
    # Main classes
    "GoBridge",
    "BridgeConfig",
    "QueryResult",
    "BatchResult",
    "HealthStatus",
    "ConnectionHealth",
    "PoolHealth",
    
    # Errors
    "BridgeError",
    "BridgeConfigError",
    "BridgeConnectionError",
    "BridgeQueryError",
    "BridgeTimeoutError",
    "BridgePoolError",
    "BridgeArrowError",
    "GoNotAvailableError",
    
    # Global functions (sync)
    "init",
    "execute",
    "execute_batch",
    "health",
    "close",
    "warmup",
    
    # Global functions (async)
    "execute_async",
    "execute_batch_async",
    "health_async",
    "warmup_async",
    
    # Parallel execution
    "execute_parallel",
    "execute_parallel_async",
    
    # Arrow execution (zero-copy for large results)
    "execute_arrow",
    "execute_arrow_async",
    
    # COPY execution (fastest for bulk reads - 2x faster)
    "execute_copy",
    "execute_copy_df",
    "execute_copy_rows",
    
    # Query Builder API (Phase 8.2)
    "execute_query",
    "query_explain",
    "query_validate",
    
    # DataFrame API (Phase 8.3) - Polars
    "execute_polars",
    "execute_polars_async",
    
    # DataFrame API (Phase 8.3) - NumPy
    "execute_numpy",
    "execute_numpy_async",
    "execute_numpy_structured",
    "execute_numpy_structured_async",
    
    # DataFrame API (Phase 8.3) - pandas
    "execute_pandas",
    "execute_pandas_async",
    
    # Batch execution
    "batch",
    "QueryBatch",
    "DeferredResult",
    
    # Fast execution
    "execute_fast",
    "execute_fast_async",
    
    # Constants
    "DEFAULT_POOL_MIN",
    "DEFAULT_POOL_MAX",
    "DEFAULT_QUERY_TIMEOUT",
]

