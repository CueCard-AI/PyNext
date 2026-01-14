"""
PostgreSQL Batch Optimization.

This module provides optimized batch operations for INSERT, UPDATE,
and UPSERT operations.

Why Batch Optimization?

Single-row operations:
    INSERT INTO users VALUES (1, 'Alice')
    INSERT INTO users VALUES (2, 'Bob')
    INSERT INTO users VALUES (3, 'Charlie')
    → 3 round trips

Batched operation:
    INSERT INTO users VALUES (1, 'Alice'), (2, 'Bob'), (3, 'Charlie')
    → 1 round trip

For 1000 rows with 10ms latency:
- Single: 10 seconds
- Batched: 10 milliseconds (1000x faster!)

How It Works:

1. Collect rows to insert/update
2. Build optimized SQL with multiple values
3. Execute in chunks (respecting max_batch_size)
4. Return results

Benefits:
- 100-1000x faster bulk operations
- Reduced network overhead
- Better transaction performance
- Automatic chunking

AI-Friendly Design:
- Simple insert_many/update_many/upsert_many API
- Automatic SQL generation
- Configurable batch sizes
- Clear error handling
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, TypeVar, Union

logger = logging.getLogger("pynext.db.postgres.batch")

T = TypeVar("T")


@dataclass
class BatchConfig:
    """Configuration for batch operations.
    
    Attributes:
        enabled: Whether batching is enabled. Default: True
        max_batch_size: Maximum rows per batch. Default: 1000
        max_params: Maximum parameters per query. Default: 65535
                   PostgreSQL limit is 65535.
        batch_inserts: Enable batched inserts. Default: True
        batch_updates: Enable batched updates. Default: True
        batch_upserts: Enable batched upserts. Default: True
        return_results: Return affected rows. Default: True
    
    Example:
        # Default: 1000 rows per batch
        config = BatchConfig()
        
        # Larger batches for data loading
        config = BatchConfig(max_batch_size=5000)
        
        # Smaller batches for memory-constrained systems
        config = BatchConfig(max_batch_size=100)
    """
    enabled: bool = True
    max_batch_size: int = 1000
    max_params: int = 65535  # PostgreSQL limit
    batch_inserts: bool = True
    batch_updates: bool = True
    batch_upserts: bool = True
    return_results: bool = True
    
    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.max_batch_size < 1:
            raise ValueError(f"max_batch_size must be >= 1, got {self.max_batch_size}")
        if self.max_params < 1:
            raise ValueError(f"max_params must be >= 1, got {self.max_params}")


@dataclass
class BatchResult:
    """Result of a batch operation.
    
    Attributes:
        total_rows: Total rows processed
        affected_rows: Rows actually affected
        batches: Number of batches executed
        duration_ms: Total execution time
        errors: Any errors encountered
    """
    total_rows: int = 0
    affected_rows: int = 0
    batches: int = 0
    duration_ms: float = 0
    errors: List[str] = field(default_factory=list)
    
    @property
    def success(self) -> bool:
        """Whether operation was successful."""
        return len(self.errors) == 0
    
    @property
    def rows_per_second(self) -> float:
        """Processing rate."""
        if self.duration_ms == 0:
            return 0.0
        return self.total_rows / (self.duration_ms / 1000)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "total_rows": self.total_rows,
            "affected_rows": self.affected_rows,
            "batches": self.batches,
            "duration_ms": self.duration_ms,
            "rows_per_second": self.rows_per_second,
            "success": self.success,
            "errors": self.errors,
        }


@dataclass
class BatchStats:
    """Statistics about batch operations.
    
    Attributes:
        total_operations: Total batch operations
        total_rows: Total rows processed
        total_batches: Total batches executed
        total_duration_ms: Total execution time
        inserts: Insert operations
        updates: Update operations
        upserts: Upsert operations
    """
    total_operations: int = 0
    total_rows: int = 0
    total_batches: int = 0
    total_duration_ms: float = 0
    inserts: int = 0
    updates: int = 0
    upserts: int = 0
    errors: int = 0
    
    @property
    def avg_batch_size(self) -> float:
        """Average rows per batch."""
        if self.total_batches == 0:
            return 0.0
        return self.total_rows / self.total_batches
    
    @property
    def avg_duration_ms(self) -> float:
        """Average operation duration."""
        if self.total_operations == 0:
            return 0.0
        return self.total_duration_ms / self.total_operations
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/metrics."""
        return {
            "total_operations": self.total_operations,
            "total_rows": self.total_rows,
            "total_batches": self.total_batches,
            "avg_batch_size": self.avg_batch_size,
            "avg_duration_ms": self.avg_duration_ms,
            "inserts": self.inserts,
            "updates": self.updates,
            "upserts": self.upserts,
            "errors": self.errors,
        }


class BatchOptimizer:
    """Optimizes bulk database operations.
    
    Provides efficient batch INSERT, UPDATE, and UPSERT operations
    with automatic chunking and SQL generation.
    
    Basic Usage:
        optimizer = BatchOptimizer(executor=my_executor)
        
        # Insert many rows
        result = await optimizer.insert_many(
            table="users",
            rows=[
                {"name": "Alice", "email": "alice@example.com"},
                {"name": "Bob", "email": "bob@example.com"},
            ],
        )
        print(f"Inserted {result.affected_rows} rows")
    
    With Custom Executor:
        async def my_executor(sql: str, params: tuple) -> int:
            return await conn.execute(sql, *params)
        
        optimizer = BatchOptimizer(executor=my_executor)
    
    Upsert (Insert or Update):
        result = await optimizer.upsert_many(
            table="users",
            rows=[...],
            conflict_columns=["email"],  # Unique constraint
            update_columns=["name", "updated_at"],
        )
    """
    
    def __init__(
        self,
        config: Optional[BatchConfig] = None,
        executor: Optional[Callable] = None,
    ):
        """Initialize the batch optimizer.
        
        Args:
            config: Batch configuration
            executor: Async function to execute SQL (sql, params) -> affected_rows
        """
        self._config = config or BatchConfig()
        self._executor = executor
        self._stats = BatchStats()
    
    @property
    def config(self) -> BatchConfig:
        """Get current configuration."""
        return self._config
    
    def _calculate_batch_size(self, columns: int) -> int:
        """Calculate optimal batch size based on parameter limit.
        
        Args:
            columns: Number of columns per row
        
        Returns:
            Maximum rows per batch
        """
        if columns == 0:
            return self._config.max_batch_size
        
        # PostgreSQL limit is 65535 parameters
        max_by_params = self._config.max_params // columns
        return min(self._config.max_batch_size, max_by_params)
    
    def _build_insert_sql(
        self,
        table: str,
        columns: List[str],
        row_count: int,
    ) -> Tuple[str, int]:
        """Build INSERT SQL statement.
        
        Args:
            table: Table name
            columns: Column names
            row_count: Number of rows
        
        Returns:
            (SQL string, parameter count)
        """
        cols = ", ".join(columns)
        
        # Build value placeholders
        # ($1, $2, $3), ($4, $5, $6), ...
        values = []
        param_num = 1
        for _ in range(row_count):
            placeholders = ", ".join(f"${param_num + i}" for i in range(len(columns)))
            values.append(f"({placeholders})")
            param_num += len(columns)
        
        values_str = ", ".join(values)
        sql = f"INSERT INTO {table} ({cols}) VALUES {values_str}"
        
        if self._config.return_results:
            sql += " RETURNING *"
        
        return sql, param_num - 1
    
    def _build_update_sql(
        self,
        table: str,
        set_columns: List[str],
        where_columns: List[str],
    ) -> str:
        """Build UPDATE SQL statement.
        
        Args:
            table: Table name
            set_columns: Columns to update
            where_columns: Columns for WHERE clause
        
        Returns:
            SQL string
        """
        # SET col1 = $1, col2 = $2
        set_parts = []
        param_num = 1
        for col in set_columns:
            set_parts.append(f"{col} = ${param_num}")
            param_num += 1
        
        # WHERE id = $3 AND other = $4
        where_parts = []
        for col in where_columns:
            where_parts.append(f"{col} = ${param_num}")
            param_num += 1
        
        set_str = ", ".join(set_parts)
        where_str = " AND ".join(where_parts)
        
        sql = f"UPDATE {table} SET {set_str} WHERE {where_str}"
        
        if self._config.return_results:
            sql += " RETURNING *"
        
        return sql
    
    def _build_upsert_sql(
        self,
        table: str,
        columns: List[str],
        row_count: int,
        conflict_columns: List[str],
        update_columns: List[str],
    ) -> Tuple[str, int]:
        """Build UPSERT (INSERT ON CONFLICT UPDATE) SQL.
        
        Args:
            table: Table name
            columns: All column names
            row_count: Number of rows
            conflict_columns: Columns that define uniqueness
            update_columns: Columns to update on conflict
        
        Returns:
            (SQL string, parameter count)
        """
        # Start with INSERT
        insert_sql, param_count = self._build_insert_sql(table, columns, row_count)
        
        # Remove RETURNING if present (we'll add it back)
        insert_sql = insert_sql.replace(" RETURNING *", "")
        
        # ON CONFLICT (email, tenant_id)
        conflict_str = ", ".join(conflict_columns)
        
        # DO UPDATE SET name = EXCLUDED.name, updated_at = EXCLUDED.updated_at
        update_parts = [f"{col} = EXCLUDED.{col}" for col in update_columns]
        update_str = ", ".join(update_parts)
        
        sql = f"{insert_sql} ON CONFLICT ({conflict_str}) DO UPDATE SET {update_str}"
        
        if self._config.return_results:
            sql += " RETURNING *"
        
        return sql, param_count
    
    def _extract_params(
        self,
        rows: List[Dict[str, Any]],
        columns: List[str],
    ) -> tuple:
        """Extract parameters from rows in column order.
        
        Args:
            rows: List of row dictionaries
            columns: Column order
        
        Returns:
            Flat tuple of parameters
        """
        params = []
        for row in rows:
            for col in columns:
                params.append(row.get(col))
        return tuple(params)
    
    async def insert_many(
        self,
        table: str,
        rows: List[Dict[str, Any]],
        columns: Optional[List[str]] = None,
    ) -> BatchResult:
        """Insert multiple rows efficiently.
        
        Args:
            table: Table name
            rows: List of row dictionaries
            columns: Column order (default: inferred from first row)
        
        Returns:
            BatchResult with operation statistics
        
        Example:
            result = await optimizer.insert_many(
                table="users",
                rows=[
                    {"name": "Alice", "email": "alice@example.com"},
                    {"name": "Bob", "email": "bob@example.com"},
                ],
            )
        """
        if not rows:
            return BatchResult()
        
        start_time = time.monotonic()
        result = BatchResult(total_rows=len(rows))
        
        # Infer columns from first row
        if columns is None:
            columns = list(rows[0].keys())
        
        # Calculate batch size
        batch_size = self._calculate_batch_size(len(columns))
        
        # Process in batches
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            
            try:
                sql, _ = self._build_insert_sql(table, columns, len(batch))
                params = self._extract_params(batch, columns)
                
                affected = await self._execute(sql, params)
                result.affected_rows += affected if isinstance(affected, int) else len(batch)
                result.batches += 1
                
            except Exception as e:
                result.errors.append(f"Batch {result.batches + 1}: {str(e)}")
                self._stats.errors += 1
        
        result.duration_ms = (time.monotonic() - start_time) * 1000
        
        # Update stats
        self._stats.total_operations += 1
        self._stats.total_rows += result.total_rows
        self._stats.total_batches += result.batches
        self._stats.total_duration_ms += result.duration_ms
        self._stats.inserts += 1
        
        logger.debug(
            f"Inserted {result.affected_rows} rows in {result.batches} batches "
            f"({result.duration_ms:.1f}ms)"
        )
        
        return result
    
    async def update_many(
        self,
        table: str,
        updates: List[Dict[str, Any]],
        set_columns: List[str],
        where_columns: List[str],
    ) -> BatchResult:
        """Update multiple rows efficiently.
        
        Each update is a dictionary containing both SET and WHERE values.
        
        Args:
            table: Table name
            updates: List of update dictionaries
            set_columns: Columns to update
            where_columns: Columns for WHERE clause
        
        Returns:
            BatchResult with operation statistics
        
        Example:
            result = await optimizer.update_many(
                table="users",
                updates=[
                    {"id": 1, "name": "Alice Updated"},
                    {"id": 2, "name": "Bob Updated"},
                ],
                set_columns=["name"],
                where_columns=["id"],
            )
        """
        if not updates:
            return BatchResult()
        
        start_time = time.monotonic()
        result = BatchResult(total_rows=len(updates))
        
        # For updates, we execute one statement per row
        # (PostgreSQL doesn't support multi-row UPDATE efficiently)
        all_columns = set_columns + where_columns
        
        for update in updates:
            try:
                sql = self._build_update_sql(table, set_columns, where_columns)
                params = tuple(update.get(col) for col in all_columns)
                
                affected = await self._execute(sql, params)
                result.affected_rows += affected if isinstance(affected, int) else 1
                result.batches += 1
                
            except Exception as e:
                result.errors.append(f"Row {result.batches + 1}: {str(e)}")
                self._stats.errors += 1
        
        result.duration_ms = (time.monotonic() - start_time) * 1000
        
        # Update stats
        self._stats.total_operations += 1
        self._stats.total_rows += result.total_rows
        self._stats.total_batches += result.batches
        self._stats.total_duration_ms += result.duration_ms
        self._stats.updates += 1
        
        return result
    
    async def upsert_many(
        self,
        table: str,
        rows: List[Dict[str, Any]],
        conflict_columns: List[str],
        update_columns: List[str],
        columns: Optional[List[str]] = None,
    ) -> BatchResult:
        """Insert or update multiple rows.
        
        Uses PostgreSQL's INSERT ... ON CONFLICT ... DO UPDATE.
        
        Args:
            table: Table name
            rows: List of row dictionaries
            conflict_columns: Columns that define uniqueness (must have index)
            update_columns: Columns to update on conflict
            columns: Column order (default: inferred from first row)
        
        Returns:
            BatchResult with operation statistics
        
        Example:
            result = await optimizer.upsert_many(
                table="users",
                rows=[
                    {"email": "alice@example.com", "name": "Alice", "updated_at": now()},
                ],
                conflict_columns=["email"],
                update_columns=["name", "updated_at"],
            )
        """
        if not rows:
            return BatchResult()
        
        start_time = time.monotonic()
        result = BatchResult(total_rows=len(rows))
        
        # Infer columns from first row
        if columns is None:
            columns = list(rows[0].keys())
        
        # Calculate batch size
        batch_size = self._calculate_batch_size(len(columns))
        
        # Process in batches
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            
            try:
                sql, _ = self._build_upsert_sql(
                    table, columns, len(batch),
                    conflict_columns, update_columns
                )
                params = self._extract_params(batch, columns)
                
                affected = await self._execute(sql, params)
                result.affected_rows += affected if isinstance(affected, int) else len(batch)
                result.batches += 1
                
            except Exception as e:
                result.errors.append(f"Batch {result.batches + 1}: {str(e)}")
                self._stats.errors += 1
        
        result.duration_ms = (time.monotonic() - start_time) * 1000
        
        # Update stats
        self._stats.total_operations += 1
        self._stats.total_rows += result.total_rows
        self._stats.total_batches += result.batches
        self._stats.total_duration_ms += result.duration_ms
        self._stats.upserts += 1
        
        return result
    
    async def delete_many(
        self,
        table: str,
        ids: List[Any],
        id_column: str = "id",
    ) -> BatchResult:
        """Delete multiple rows by ID.
        
        Args:
            table: Table name
            ids: List of IDs to delete
            id_column: Name of ID column (default: "id")
        
        Returns:
            BatchResult with operation statistics
        
        Example:
            result = await optimizer.delete_many(
                table="users",
                ids=[1, 2, 3],
            )
        """
        if not ids:
            return BatchResult()
        
        start_time = time.monotonic()
        result = BatchResult(total_rows=len(ids))
        
        # Use ANY for efficient batch delete
        placeholders = ", ".join(f"${i+1}" for i in range(len(ids)))
        sql = f"DELETE FROM {table} WHERE {id_column} IN ({placeholders})"
        
        if self._config.return_results:
            sql += " RETURNING *"
        
        try:
            affected = await self._execute(sql, tuple(ids))
            result.affected_rows = affected if isinstance(affected, int) else len(ids)
            result.batches = 1
            
        except Exception as e:
            result.errors.append(str(e))
            self._stats.errors += 1
        
        result.duration_ms = (time.monotonic() - start_time) * 1000
        
        self._stats.total_operations += 1
        self._stats.total_rows += result.total_rows
        self._stats.total_batches += result.batches
        self._stats.total_duration_ms += result.duration_ms
        
        return result
    
    async def _execute(self, sql: str, params: tuple) -> Any:
        """Execute SQL with executor."""
        if self._executor is None:
            raise ValueError("No executor configured")
        
        if asyncio.iscoroutinefunction(self._executor):
            return await self._executor(sql, params)
        else:
            return self._executor(sql, params)
    
    def get_stats(self) -> BatchStats:
        """Get batch operation statistics."""
        return self._stats
    
    def reset_stats(self) -> None:
        """Reset statistics."""
        self._stats = BatchStats()
    
    def __repr__(self) -> str:
        return (
            f"BatchOptimizer(max_batch={self._config.max_batch_size}, "
            f"operations={self._stats.total_operations})"
        )


# =============================================================================
# Convenience Functions
# =============================================================================

def bulk_load_config() -> BatchConfig:
    """Create a configuration optimized for bulk data loading.
    
    - Large batches (5000)
    - No result return (faster)
    
    Returns:
        BatchConfig for bulk loading
    """
    return BatchConfig(
        max_batch_size=5000,
        return_results=False,
    )


def transactional_config() -> BatchConfig:
    """Create a configuration for transactional updates.
    
    - Smaller batches (100)
    - Return results
    
    Returns:
        BatchConfig for transactions
    """
    return BatchConfig(
        max_batch_size=100,
        return_results=True,
    )


def disabled_batch_config() -> BatchConfig:
    """Create a disabled batch configuration.
    
    Returns:
        BatchConfig with batching disabled
    """
    return BatchConfig(enabled=False)

