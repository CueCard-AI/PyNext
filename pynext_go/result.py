"""
PyNext Go Bridge - Query Result Types.

Defines QueryResult and BatchResult for query responses.

Design Goals:
    - Familiar API (similar to database cursors)
    - Easy conversion to dicts, DataFrames
    - Arrow support for zero-copy operations
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterator, TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd
    import polars as pl


@dataclass
class QueryResult:
    """
    Result of a single query execution.
    
    Attributes:
        success: True if query succeeded
        error: Error message if failed
        rows: List of row values (list of lists)
        columns: Column names
        rows_affected: Number of rows affected (INSERT/UPDATE/DELETE)
        duration_ms: Query execution time in milliseconds
        cached: Whether prepared statement was used
        arrow_buffer: Raw Arrow IPC buffer (for zero-copy)
    
    Usage:
        # Iterate rows as lists
        for row in result:
            print(row)
        
        # Iterate rows as dicts
        for row in result.iter_dicts():
            print(row["name"])
        
        # Convert all to dicts
        users = result.to_dicts()
        
        # Convert to DataFrame
        df = result.to_pandas()
    """
    success: bool
    error: str = ""
    rows: list[list[Any]] = field(default_factory=list)
    columns: list[str] = field(default_factory=list)
    rows_affected: int = 0
    duration_ms: float = 0.0
    cached: bool = False
    arrow_buffer: bytes | None = None
    
    def __len__(self) -> int:
        """Return number of rows."""
        return len(self.rows)
    
    def __bool__(self) -> bool:
        """True if query succeeded (even with 0 rows)."""
        return self.success
    
    def __iter__(self) -> Iterator[list[Any]]:
        """Iterate over rows as lists."""
        return iter(self.rows)
    
    def __getitem__(self, index: int) -> list[Any]:
        """Get row by index."""
        return self.rows[index]
    
    @property
    def column_count(self) -> int:
        """Number of columns."""
        return len(self.columns)
    
    @property
    def row_count(self) -> int:
        """Number of rows."""
        return len(self.rows)
    
    @property
    def is_empty(self) -> bool:
        """True if no rows returned."""
        return len(self.rows) == 0
    
    def first(self) -> list[Any] | None:
        """
        Get first row or None if empty.
        
        Returns:
            First row as list, or None
        """
        if self.rows:
            return self.rows[0]
        return None
    
    def first_dict(self) -> dict[str, Any] | None:
        """
        Get first row as dict or None if empty.
        
        Returns:
            First row as dict, or None
        """
        if self.rows:
            return dict(zip(self.columns, self.rows[0]))
        return None
    
    def one(self) -> list[Any]:
        """
        Get exactly one row, raise if not exactly one.
        
        Returns:
            The single row
            
        Raises:
            ValueError: If not exactly one row
        """
        if len(self.rows) == 0:
            raise ValueError("Expected one row, got none")
        if len(self.rows) > 1:
            raise ValueError(f"Expected one row, got {len(self.rows)}")
        return self.rows[0]
    
    def one_dict(self) -> dict[str, Any]:
        """
        Get exactly one row as dict, raise if not exactly one.
        
        Returns:
            The single row as dict
            
        Raises:
            ValueError: If not exactly one row
        """
        row = self.one()
        return dict(zip(self.columns, row))
    
    def scalar(self) -> Any:
        """
        Get single value from first row, first column.
        
        Useful for COUNT(*), MAX(), etc.
        
        Returns:
            The scalar value
            
        Raises:
            ValueError: If no rows or no columns
        """
        if not self.rows:
            raise ValueError("No rows")
        if not self.rows[0]:
            raise ValueError("No columns")
        return self.rows[0][0]
    
    def column(self, name: str) -> list[Any]:
        """
        Get all values for a column.
        
        Args:
            name: Column name
            
        Returns:
            List of values for that column
            
        Raises:
            KeyError: If column not found
        """
        try:
            idx = self.columns.index(name)
        except ValueError:
            raise KeyError(f"Column not found: {name}")
        return [row[idx] for row in self.rows]
    
    def iter_dicts(self) -> Iterator[dict[str, Any]]:
        """
        Iterate over rows as dictionaries.
        
        Yields:
            Each row as a dict
        """
        for row in self.rows:
            yield dict(zip(self.columns, row))
    
    def to_dicts(self) -> list[dict[str, Any]]:
        """
        Convert all rows to list of dicts.
        
        Returns:
            List of row dicts
        """
        return [dict(zip(self.columns, row)) for row in self.rows]
    
    def to_pandas(self) -> pd.DataFrame:
        """
        Convert to pandas DataFrame.
        
        If Arrow buffer is available, uses zero-copy conversion.
        Otherwise falls back to dict conversion.
        
        Returns:
            pandas DataFrame
            
        Raises:
            ImportError: If pandas not installed
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas is required for to_pandas()")
        
        # Try Arrow path first (zero-copy)
        if self.arrow_buffer:
            try:
                import pyarrow as pa
                reader = pa.ipc.open_stream(self.arrow_buffer)
                table = reader.read_all()
                return table.to_pandas()
            except Exception:
                pass  # Fall back to dict conversion
        
        # Fallback: create from dicts
        return pd.DataFrame(self.to_dicts())
    
    def to_polars(self) -> pl.DataFrame:
        """
        Convert to Polars DataFrame.
        
        If Arrow buffer is available, uses zero-copy conversion.
        Otherwise falls back to dict conversion.
        
        Returns:
            Polars DataFrame
            
        Raises:
            ImportError: If polars not installed
        """
        try:
            import polars as pl
        except ImportError:
            raise ImportError("polars is required for to_polars()")
        
        # Try Arrow path first (zero-copy)
        if self.arrow_buffer:
            try:
                import pyarrow as pa
                reader = pa.ipc.open_stream(self.arrow_buffer)
                table = reader.read_all()
                return pl.from_arrow(table)
            except Exception:
                pass  # Fall back to dict conversion
        
        # Fallback: create from dicts
        return pl.DataFrame(self.to_dicts())
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> QueryResult:
        """Create from dictionary (Go response)."""
        return cls(
            success=data.get("success", False),
            error=data.get("error", ""),
            rows=data.get("rows", []),
            columns=data.get("columns", []),
            rows_affected=data.get("rows_affected", 0),
            duration_ms=data.get("duration_ms", 0.0),
            cached=data.get("cached", False),
            arrow_buffer=data.get("arrow_buffer"),
        )


@dataclass
class BatchResult:
    """
    Result of batch query execution.
    
    Attributes:
        success: True if all queries succeeded
        error: First error message if any failed
        results: Individual QueryResult for each query
        duration_ms: Total execution time
    
    Usage:
        batch = bridge.execute_batch([
            ("INSERT INTO users (name) VALUES ($1)", ["Alice"]),
            ("INSERT INTO users (name) VALUES ($1)", ["Bob"]),
        ])
        
        if batch.success:
            print(f"Inserted {batch.total_rows_affected} rows")
        else:
            print(f"Failed: {batch.error}")
            for i, result in enumerate(batch.results):
                if not result.success:
                    print(f"Query {i} failed: {result.error}")
    """
    success: bool
    error: str = ""
    results: list[QueryResult] = field(default_factory=list)
    duration_ms: float = 0.0
    
    def __len__(self) -> int:
        """Return number of queries."""
        return len(self.results)
    
    def __bool__(self) -> bool:
        """True if all queries succeeded."""
        return self.success
    
    def __iter__(self) -> Iterator[QueryResult]:
        """Iterate over individual results."""
        return iter(self.results)
    
    def __getitem__(self, index: int) -> QueryResult:
        """Get result by index."""
        return self.results[index]
    
    @property
    def total_rows_affected(self) -> int:
        """Total rows affected across all queries."""
        return sum(r.rows_affected for r in self.results)
    
    @property
    def failed_count(self) -> int:
        """Number of failed queries."""
        return sum(1 for r in self.results if not r.success)
    
    @property
    def succeeded_count(self) -> int:
        """Number of succeeded queries."""
        return sum(1 for r in self.results if r.success)
    
    def failed_queries(self) -> list[tuple[int, QueryResult]]:
        """
        Get list of failed queries with their indices.
        
        Returns:
            List of (index, result) tuples for failed queries
        """
        return [(i, r) for i, r in enumerate(self.results) if not r.success]
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BatchResult:
        """Create from dictionary (Go response)."""
        results = [
            QueryResult.from_dict(r)
            for r in data.get("results", [])
        ]
        return cls(
            success=data.get("success", False),
            error=data.get("error", ""),
            results=results,
            duration_ms=data.get("duration_ms", 0.0),
        )

