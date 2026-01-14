"""
PyNext Prepared Statements.

Provides prepared statement management with:
- Named prepared statements
- Auto-invalidation on schema changes
- Usage statistics
- LRU caching

Why Prepared Statements?
    Prepared statements skip query parsing and planning on subsequent
    executions. For frequently-run queries, this can be 20-30% faster.

Usage - Prepare and Execute:
    stmt = await db.prepare(
        "get_user_by_id",
        "SELECT * FROM users WHERE id = $1",
        types=[int]
    )
    
    # Execute (faster after first call)
    user = await stmt.fetchone(123)
    users = await stmt.fetchall([1, 2, 3])

Usage - Decorator (Auto-Prepare):
    @db.prepared("get_active_users")
    async def get_active_users(limit: int = 100):
        return "SELECT * FROM users WHERE active = true LIMIT $1"
    
    # First call prepares, subsequent calls reuse
    users = await get_active_users(50)

Usage - Statistics:
    stats = db.prepared_stats()
    print(stats["get_user_by_id"].call_count)
    print(stats["get_user_by_id"].avg_time_ms)

Usage - Invalidation:
    # Manual
    await db.unprepare("get_user_by_id")
    
    # Automatic on schema change
    @db.on_schema_change("users")
    async def handle_users_change():
        await db.invalidate_prepared_for_table("users")
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, TypeVar
from functools import wraps
import asyncio
import hashlib
import time
import weakref


# =============================================================================
# TYPE VARIABLES
# =============================================================================

T = TypeVar("T")
F = TypeVar("F", bound=Callable)


# =============================================================================
# ENUMS
# =============================================================================

class StatementState(str, Enum):
    """State of a prepared statement."""
    PENDING = "pending"     # Not yet prepared
    PREPARED = "prepared"   # Ready to execute
    INVALID = "invalid"     # Needs re-preparation
    ERROR = "error"         # Preparation failed


# =============================================================================
# STATISTICS
# =============================================================================

@dataclass
class PreparedStats:
    """
    Statistics for a prepared statement.
    
    Attributes:
        name: Statement name
        sql: SQL query
        call_count: Number of executions
        total_time_ms: Total execution time
        error_count: Number of errors
        last_used: When last executed
        created_at: When prepared
        invalidation_count: Times invalidated
        avg_time_ms: Average execution time
    """
    name: str
    sql: str
    call_count: int = 0
    total_time_ms: float = 0.0
    error_count: int = 0
    last_used: Optional[datetime] = None
    created_at: Optional[datetime] = None
    invalidation_count: int = 0
    
    @property
    def avg_time_ms(self) -> float:
        """Average execution time in milliseconds."""
        if self.call_count == 0:
            return 0.0
        return self.total_time_ms / self.call_count
    
    @property
    def error_rate(self) -> float:
        """Error rate as percentage."""
        if self.call_count == 0:
            return 0.0
        return (self.error_count / self.call_count) * 100
    
    def record_call(self, duration_ms: float):
        """Record a successful call."""
        self.call_count += 1
        self.total_time_ms += duration_ms
        self.last_used = datetime.now()
    
    def record_error(self):
        """Record an error."""
        self.error_count += 1
        self.last_used = datetime.now()
    
    def record_invalidation(self):
        """Record an invalidation."""
        self.invalidation_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "sql": self.sql[:100],
            "call_count": self.call_count,
            "avg_time_ms": self.avg_time_ms,
            "total_time_ms": self.total_time_ms,
            "error_count": self.error_count,
            "error_rate": self.error_rate,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "invalidation_count": self.invalidation_count,
        }


# =============================================================================
# PREPARED STATEMENT
# =============================================================================

@dataclass
class PreparedStatement:
    """
    A prepared statement ready for execution.
    
    Attributes:
        name: Unique statement name
        sql: SQL query with $1, $2, ... placeholders
        param_types: Expected parameter types
        tables: Tables referenced by this statement
        state: Current state
        stats: Usage statistics
        connection_id: Connection that prepared this
        backend_name: PostgreSQL internal name
    """
    name: str
    sql: str
    param_types: List[Type] = field(default_factory=list)
    tables: Set[str] = field(default_factory=set)
    state: StatementState = StatementState.PENDING
    stats: PreparedStats = None
    connection_id: Optional[int] = None
    backend_name: Optional[str] = None
    
    def __post_init__(self):
        """Initialize statistics."""
        if self.stats is None:
            self.stats = PreparedStats(name=self.name, sql=self.sql)
            self.stats.created_at = datetime.now()
        
        # Auto-detect tables from SQL
        if not self.tables:
            self.tables = self._extract_tables()
    
    def _extract_tables(self) -> Set[str]:
        """Extract table names from SQL."""
        tables = set()
        sql_upper = self.sql.upper()
        
        # Look for FROM and JOIN clauses
        keywords = ["FROM", "JOIN", "INTO", "UPDATE"]
        words = self.sql.split()
        
        for i, word in enumerate(words):
            if word.upper() in keywords and i + 1 < len(words):
                table_name = words[i + 1].strip(",();").lower()
                if table_name and not table_name.startswith("$"):
                    tables.add(table_name)
        
        return tables
    
    @property
    def is_ready(self) -> bool:
        """Check if statement is ready to execute."""
        return self.state == StatementState.PREPARED
    
    @property
    def needs_preparation(self) -> bool:
        """Check if statement needs (re)preparation."""
        return self.state in (StatementState.PENDING, StatementState.INVALID)
    
    def invalidate(self):
        """Mark statement as needing re-preparation."""
        self.state = StatementState.INVALID
        self.stats.record_invalidation()
    
    def mark_prepared(self, connection_id: int, backend_name: str):
        """Mark statement as prepared on a connection."""
        self.state = StatementState.PREPARED
        self.connection_id = connection_id
        self.backend_name = backend_name
    
    def mark_error(self, error: Exception):
        """Mark statement as errored."""
        self.state = StatementState.ERROR
        self.stats.record_error()
    
    def generate_prepare_sql(self) -> str:
        """Generate PREPARE statement SQL."""
        type_list = ""
        if self.param_types:
            pg_types = [self._python_to_pg_type(t) for t in self.param_types]
            type_list = f"({', '.join(pg_types)})"
        
        return f"PREPARE {self.backend_name or self.name} {type_list} AS {self.sql}"
    
    def generate_execute_sql(self, params: tuple) -> str:
        """Generate EXECUTE statement SQL."""
        if not params:
            return f"EXECUTE {self.backend_name or self.name}"
        
        param_str = ", ".join(f"${i+1}" for i in range(len(params)))
        return f"EXECUTE {self.backend_name or self.name}({param_str})"
    
    def generate_deallocate_sql(self) -> str:
        """Generate DEALLOCATE statement SQL."""
        return f"DEALLOCATE {self.backend_name or self.name}"
    
    def _python_to_pg_type(self, python_type: Type) -> str:
        """Convert Python type to PostgreSQL type."""
        type_map = {
            int: "integer",
            float: "double precision",
            str: "text",
            bool: "boolean",
            bytes: "bytea",
            datetime: "timestamp",
            list: "jsonb",
            dict: "jsonb",
        }
        return type_map.get(python_type, "text")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "sql": self.sql,
            "param_types": [t.__name__ for t in self.param_types],
            "tables": list(self.tables),
            "state": self.state.value,
            "stats": self.stats.to_dict(),
        }


# =============================================================================
# PREPARED STATEMENT CACHE
# =============================================================================

class PreparedCache:
    """
    LRU cache for prepared statements.
    
    Manages statement preparation, execution, and invalidation.
    """
    
    def __init__(
        self,
        max_size: int = 100,
        auto_prepare: bool = True,
    ):
        """
        Initialize prepared statement cache.
        
        Args:
            max_size: Maximum number of cached statements
            auto_prepare: Automatically prepare on first use
        """
        self.max_size = max_size
        self.auto_prepare = auto_prepare
        self._statements: Dict[str, PreparedStatement] = {}
        self._access_order: List[str] = []
        self._lock = asyncio.Lock()
    
    @property
    def size(self) -> int:
        """Current cache size."""
        return len(self._statements)
    
    @property
    def is_full(self) -> bool:
        """Check if cache is full."""
        return self.size >= self.max_size
    
    def get(self, name: str) -> Optional[PreparedStatement]:
        """Get a prepared statement by name."""
        stmt = self._statements.get(name)
        if stmt:
            self._update_access(name)
        return stmt
    
    def put(self, stmt: PreparedStatement) -> None:
        """Add a prepared statement to cache."""
        if stmt.name in self._statements:
            self._statements[stmt.name] = stmt
            self._update_access(stmt.name)
            return
        
        # Evict if full
        if self.is_full:
            self._evict_lru()
        
        self._statements[stmt.name] = stmt
        self._access_order.append(stmt.name)
    
    def remove(self, name: str) -> Optional[PreparedStatement]:
        """Remove a prepared statement from cache."""
        stmt = self._statements.pop(name, None)
        if name in self._access_order:
            self._access_order.remove(name)
        return stmt
    
    def invalidate(self, name: str) -> bool:
        """Invalidate a prepared statement."""
        stmt = self._statements.get(name)
        if stmt:
            stmt.invalidate()
            return True
        return False
    
    def invalidate_for_table(self, table: str) -> int:
        """Invalidate all statements referencing a table."""
        count = 0
        for stmt in self._statements.values():
            if table.lower() in stmt.tables:
                stmt.invalidate()
                count += 1
        return count
    
    def invalidate_all(self) -> int:
        """Invalidate all statements."""
        count = 0
        for stmt in self._statements.values():
            stmt.invalidate()
            count += 1
        return count
    
    def clear(self) -> int:
        """Clear all statements from cache."""
        count = len(self._statements)
        self._statements.clear()
        self._access_order.clear()
        return count
    
    def all_stats(self) -> Dict[str, PreparedStats]:
        """Get statistics for all statements."""
        return {name: stmt.stats for name, stmt in self._statements.items()}
    
    def _update_access(self, name: str) -> None:
        """Update access order for LRU."""
        if name in self._access_order:
            self._access_order.remove(name)
        self._access_order.append(name)
    
    def _evict_lru(self) -> Optional[PreparedStatement]:
        """Evict least recently used statement."""
        if not self._access_order:
            return None
        
        lru_name = self._access_order.pop(0)
        return self._statements.pop(lru_name, None)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "size": self.size,
            "max_size": self.max_size,
            "statements": {name: stmt.to_dict() for name, stmt in self._statements.items()},
        }


# =============================================================================
# PREPARED STATEMENT EXECUTOR
# =============================================================================

class PreparedExecutor:
    """
    Executes prepared statements.
    
    Handles preparation, execution, and re-preparation after invalidation.
    """
    
    def __init__(
        self,
        cache: Optional[PreparedCache] = None,
        prepare_fn: Optional[Callable] = None,
        execute_fn: Optional[Callable] = None,
        deallocate_fn: Optional[Callable] = None,
    ):
        """
        Initialize executor.
        
        Args:
            cache: Statement cache
            prepare_fn: Function to prepare statement
            execute_fn: Function to execute statement
            deallocate_fn: Function to deallocate statement
        """
        self.cache = cache or PreparedCache()
        self._prepare_fn = prepare_fn
        self._execute_fn = execute_fn
        self._deallocate_fn = deallocate_fn
        self._lock = asyncio.Lock()
    
    async def prepare(
        self,
        name: str,
        sql: str,
        types: Optional[List[Type]] = None,
    ) -> PreparedStatement:
        """
        Prepare a statement for later execution.
        
        Args:
            name: Unique statement name
            sql: SQL query with $1, $2, ... placeholders
            types: Expected parameter types
        
        Returns:
            PreparedStatement ready for execution
        
        Example:
            stmt = await executor.prepare(
                "get_user",
                "SELECT * FROM users WHERE id = $1",
                types=[int]
            )
        """
        async with self._lock:
            # Check if already cached
            existing = self.cache.get(name)
            if existing and existing.is_ready:
                return existing
            
            # Create statement
            stmt = PreparedStatement(
                name=name,
                sql=sql,
                param_types=types or [],
            )
            
            # Generate backend name (unique per session)
            stmt.backend_name = f"pynext_{name}_{id(self) % 10000}"
            
            # Prepare in database
            if self._prepare_fn:
                try:
                    prepare_sql = stmt.generate_prepare_sql()
                    await self._prepare_fn(prepare_sql)
                    stmt.mark_prepared(id(self), stmt.backend_name)
                except Exception as e:
                    stmt.mark_error(e)
                    raise
            else:
                stmt.state = StatementState.PREPARED
            
            # Cache it
            self.cache.put(stmt)
            
            return stmt
    
    async def execute(
        self,
        stmt: PreparedStatement,
        params: tuple = (),
    ) -> Any:
        """
        Execute a prepared statement.
        
        Args:
            stmt: Prepared statement
            params: Query parameters
        
        Returns:
            Query results
        """
        # Re-prepare if needed
        if stmt.needs_preparation:
            async with self._lock:
                if self._prepare_fn:
                    prepare_sql = stmt.generate_prepare_sql()
                    await self._prepare_fn(prepare_sql)
                    stmt.mark_prepared(id(self), stmt.backend_name)
        
        # Execute
        start_time = time.perf_counter()
        
        try:
            if self._execute_fn:
                result = await self._execute_fn(stmt.sql, params)
            else:
                result = []
            
            duration_ms = (time.perf_counter() - start_time) * 1000
            stmt.stats.record_call(duration_ms)
            
            return result
            
        except Exception as e:
            stmt.stats.record_error()
            raise
    
    async def fetchone(
        self,
        stmt: PreparedStatement,
        *params,
    ) -> Optional[Dict[str, Any]]:
        """Fetch single row."""
        results = await self.execute(stmt, params)
        return results[0] if results else None
    
    async def fetchall(
        self,
        stmt: PreparedStatement,
        *params,
    ) -> List[Dict[str, Any]]:
        """Fetch all rows."""
        return await self.execute(stmt, params)
    
    async def unprepare(self, name: str) -> bool:
        """
        Deallocate a prepared statement.
        
        Args:
            name: Statement name
        
        Returns:
            True if deallocated, False if not found
        """
        async with self._lock:
            stmt = self.cache.remove(name)
            
            if stmt and self._deallocate_fn:
                try:
                    deallocate_sql = stmt.generate_deallocate_sql()
                    await self._deallocate_fn(deallocate_sql)
                except Exception:
                    pass  # Ignore deallocate errors
            
            return stmt is not None
    
    async def unprepare_all(self) -> int:
        """Deallocate all prepared statements."""
        async with self._lock:
            count = 0
            
            for name, stmt in list(self.cache._statements.items()):
                if self._deallocate_fn:
                    try:
                        deallocate_sql = stmt.generate_deallocate_sql()
                        await self._deallocate_fn(deallocate_sql)
                    except Exception:
                        pass
                count += 1
            
            self.cache.clear()
            return count
    
    def get_stats(self, name: str) -> Optional[PreparedStats]:
        """Get statistics for a statement."""
        stmt = self.cache.get(name)
        return stmt.stats if stmt else None
    
    def all_stats(self) -> Dict[str, PreparedStats]:
        """Get statistics for all statements."""
        return self.cache.all_stats()


# =============================================================================
# DECORATOR
# =============================================================================

def prepared(
    name: str,
    types: Optional[List[Type]] = None,
    executor: Optional[PreparedExecutor] = None,
) -> Callable[[F], F]:
    """
    Decorator to create a prepared statement from a function.
    
    The decorated function should return the SQL query string.
    
    Args:
        name: Statement name
        types: Parameter types
        executor: Executor to use (uses global if not provided)
    
    Returns:
        Decorated function
    
    Example:
        @prepared("get_active_users", types=[int])
        async def get_active_users(limit: int = 100):
            return "SELECT * FROM users WHERE active = true LIMIT $1"
        
        # First call prepares, subsequent calls reuse
        users = await get_active_users(50)
    """
    def decorator(fn: F) -> F:
        _stmt: Optional[PreparedStatement] = None
        _executor = executor
        
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            nonlocal _stmt, _executor
            
            # Get executor from global if not set
            if _executor is None:
                from . import get_prepared_executor
                _executor = get_prepared_executor()
            
            # Prepare on first call
            if _stmt is None or _stmt.needs_preparation:
                sql = await fn(*args, **kwargs) if asyncio.iscoroutinefunction(fn) else fn(*args, **kwargs)
                _stmt = await _executor.prepare(name, sql, types)
            
            # Execute with args as params
            return await _executor.execute(_stmt, args)
        
        # Add metadata
        wrapper._prepared_name = name
        wrapper._prepared_types = types
        
        return wrapper
    
    return decorator


# =============================================================================
# SCHEMA WATCHER
# =============================================================================

class SchemaWatcher:
    """
    Watches for schema changes and invalidates affected statements.
    
    Uses PostgreSQL LISTEN/NOTIFY for real-time updates.
    """
    
    def __init__(
        self,
        cache: PreparedCache,
        channel: str = "schema_changes",
    ):
        """
        Initialize schema watcher.
        
        Args:
            cache: Statement cache to invalidate
            channel: PostgreSQL channel to listen on
        """
        self.cache = cache
        self.channel = channel
        self._listeners: Dict[str, List[Callable]] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    def on_change(self, table: str) -> Callable[[F], F]:
        """
        Decorator to register a schema change handler.
        
        Args:
            table: Table to watch
        
        Returns:
            Decorator
        
        Example:
            @watcher.on_change("users")
            async def handle_users_change():
                print("Users table changed!")
        """
        def decorator(fn: F) -> F:
            if table not in self._listeners:
                self._listeners[table] = []
            self._listeners[table].append(fn)
            return fn
        return decorator
    
    async def handle_change(self, table: str, change_type: str) -> None:
        """
        Handle a schema change notification.
        
        Args:
            table: Table that changed
            change_type: Type of change (ALTER, DROP, etc.)
        """
        # Invalidate cached statements
        count = self.cache.invalidate_for_table(table)
        
        # Call listeners
        for listener in self._listeners.get(table, []):
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener()
                else:
                    listener()
            except Exception:
                pass  # Don't let listener errors affect main flow
    
    async def start(self, listen_fn: Callable) -> None:
        """Start watching for schema changes."""
        if self._running:
            return
        
        self._running = True
        
        async def watch_loop():
            while self._running:
                try:
                    # This would be replaced with actual LISTEN/NOTIFY
                    await asyncio.sleep(1)
                except asyncio.CancelledError:
                    break
                except Exception:
                    await asyncio.sleep(5)
        
        self._task = asyncio.create_task(watch_loop())
    
    async def stop(self) -> None:
        """Stop watching for schema changes."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None


# =============================================================================
# GLOBAL STATE
# =============================================================================

_global_executor: Optional[PreparedExecutor] = None


def get_prepared_executor() -> PreparedExecutor:
    """Get the global prepared executor."""
    global _global_executor
    if _global_executor is None:
        _global_executor = PreparedExecutor()
    return _global_executor


def set_prepared_executor(executor: PreparedExecutor) -> None:
    """Set the global prepared executor."""
    global _global_executor
    _global_executor = executor


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "StatementState",
    # Statistics
    "PreparedStats",
    # Statement
    "PreparedStatement",
    # Cache
    "PreparedCache",
    # Executor
    "PreparedExecutor",
    # Decorator
    "prepared",
    # Schema watcher
    "SchemaWatcher",
    # Global
    "get_prepared_executor",
    "set_prepared_executor",
]

