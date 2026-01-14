"""
PyNext Cursor-Based Pagination.

Provides three pagination strategies:
1. Keyset (cursor-based): Fastest for large datasets
2. Offset: Traditional page numbers, good for small datasets
3. Smart: Automatically chooses best method

Why Keyset Pagination?
    Traditional offset pagination (OFFSET 10000) requires scanning
    all 10,000 rows before returning results. Keyset pagination
    uses WHERE clauses (id > last_id) which uses indexes efficiently.

Usage - Smart Pagination (Auto-Selects Best Method):
    page = await User.select().paginate(
        page_size=20,
        cursor=request.query.get("cursor"),
    )
    print(page.items)        # List of users
    print(page.next_cursor)  # Pass to next request
    print(page.has_more)     # Boolean

Usage - Explicit Keyset (Fastest):
    page = await User.select().order_by("created_at").cursor(
        after="2024-01-15T10:30:00",
        limit=20,
    )

Usage - Offset (When Needed):
    page = await User.select().offset_paginate(
        page=3,
        page_size=20,
    )
    print(page.total_count)
    print(page.total_pages)

Usage - Streaming (For Large Datasets):
    async for batch in User.select().stream(batch_size=100):
        for user in batch:
            process(user)
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import (
    Any, AsyncIterator, Callable, Dict, Generic, List, 
    Optional, Tuple, TypeVar, Union
)
import base64
import json
import hashlib


# =============================================================================
# TYPE VARIABLES
# =============================================================================

T = TypeVar("T")


# =============================================================================
# ENUMS
# =============================================================================

class PaginationMethod(str, Enum):
    """Pagination method to use."""
    KEYSET = "keyset"
    OFFSET = "offset"
    AUTO = "auto"


class CursorDirection(str, Enum):
    """Direction for cursor-based pagination."""
    FORWARD = "forward"
    BACKWARD = "backward"


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class PaginationConfig:
    """
    Global pagination configuration.
    
    Attributes:
        default_page_size: Default items per page
        max_page_size: Maximum allowed page size
        default_method: Default pagination method
        keyset_threshold: Row count threshold for keyset vs offset
        include_total_count: Whether to include total by default
        cursor_secret: Secret for cursor signing (optional)
    """
    default_page_size: int = 20
    max_page_size: int = 100
    default_method: PaginationMethod = PaginationMethod.AUTO
    keyset_threshold: int = 10_000
    include_total_count: bool = False
    cursor_secret: Optional[str] = None
    
    def __post_init__(self):
        """Validate configuration."""
        if self.default_page_size < 1:
            raise ValueError("default_page_size must be at least 1")
        if self.max_page_size < self.default_page_size:
            raise ValueError("max_page_size must be >= default_page_size")
        if self.keyset_threshold < 1:
            raise ValueError("keyset_threshold must be at least 1")
    
    def clamp_page_size(self, page_size: int) -> int:
        """Clamp page size to allowed range."""
        return max(1, min(page_size, self.max_page_size))


# Global config
_global_config = PaginationConfig()


def get_pagination_config() -> PaginationConfig:
    """Get global pagination config."""
    return _global_config


def set_pagination_config(config: PaginationConfig) -> None:
    """Set global pagination config."""
    global _global_config
    _global_config = config


# =============================================================================
# CURSOR
# =============================================================================

@dataclass
class Cursor:
    """
    Encoded pagination cursor.
    
    Contains position information for resuming pagination.
    Cursors are base64-encoded JSON and optionally signed.
    
    Attributes:
        values: Column values at cursor position
        direction: Pagination direction
        columns: Column names for the values
        method: Pagination method used
        checksum: Optional integrity checksum
    """
    values: Dict[str, Any]
    direction: CursorDirection = CursorDirection.FORWARD
    columns: List[str] = field(default_factory=list)
    method: PaginationMethod = PaginationMethod.KEYSET
    checksum: Optional[str] = None
    
    def encode(self, secret: Optional[str] = None) -> str:
        """
        Encode cursor to string.
        
        Args:
            secret: Optional secret for signing
        
        Returns:
            Base64-encoded cursor string
        """
        data = {
            "v": self.values,
            "d": self.direction.value,
            "c": self.columns,
            "m": self.method.value,
        }
        
        # Add checksum if secret provided
        if secret:
            payload = json.dumps(data, sort_keys=True)
            checksum = hashlib.sha256(f"{payload}{secret}".encode()).hexdigest()[:16]
            data["cs"] = checksum
        
        json_str = json.dumps(data, default=str)
        return base64.urlsafe_b64encode(json_str.encode()).decode()
    
    @classmethod
    def decode(cls, cursor_str: str, secret: Optional[str] = None) -> "Cursor":
        """
        Decode cursor from string.
        
        Args:
            cursor_str: Base64-encoded cursor
            secret: Optional secret for verification
        
        Returns:
            Decoded Cursor
        
        Raises:
            ValueError: If cursor is invalid
        """
        try:
            json_str = base64.urlsafe_b64decode(cursor_str.encode()).decode()
            data = json.loads(json_str)
            
            # Verify checksum if secret provided
            if secret:
                provided_checksum = data.pop("cs", None)
                if provided_checksum:
                    payload = json.dumps(data, sort_keys=True)
                    expected = hashlib.sha256(f"{payload}{secret}".encode()).hexdigest()[:16]
                    if provided_checksum != expected:
                        raise ValueError("Invalid cursor checksum")
            
            return cls(
                values=data.get("v", {}),
                direction=CursorDirection(data.get("d", "forward")),
                columns=data.get("c", []),
                method=PaginationMethod(data.get("m", "keyset")),
            )
            
        except (json.JSONDecodeError, UnicodeDecodeError, KeyError) as e:
            raise ValueError(f"Invalid cursor: {e}")
    
    @classmethod
    def from_record(
        cls,
        record: Dict[str, Any],
        columns: List[str],
        direction: CursorDirection = CursorDirection.FORWARD,
    ) -> "Cursor":
        """Create cursor from a record."""
        values = {col: record.get(col) for col in columns}
        return cls(
            values=values,
            direction=direction,
            columns=columns,
        )
    
    def __str__(self) -> str:
        return self.encode()


# =============================================================================
# PAGE RESULTS
# =============================================================================

@dataclass
class Page(Generic[T]):
    """
    A page of results from pagination.
    
    Attributes:
        items: List of items in this page
        page_size: Number of items per page
        has_more: Whether there are more items
        has_previous: Whether there are previous items
        next_cursor: Cursor to get next page
        previous_cursor: Cursor to get previous page
        total_count: Total items (if available)
        total_pages: Total pages (if available)
        current_page: Current page number (offset only)
        method: Pagination method used
    """
    items: List[T]
    page_size: int
    has_more: bool = False
    has_previous: bool = False
    next_cursor: Optional[str] = None
    previous_cursor: Optional[str] = None
    total_count: Optional[int] = None
    total_pages: Optional[int] = None
    current_page: Optional[int] = None
    method: PaginationMethod = PaginationMethod.KEYSET
    
    def __len__(self) -> int:
        return len(self.items)
    
    def __iter__(self):
        return iter(self.items)
    
    def __getitem__(self, index: int) -> T:
        return self.items[index]
    
    @property
    def count(self) -> int:
        """Number of items in this page."""
        return len(self.items)
    
    @property
    def is_empty(self) -> bool:
        """Check if page is empty."""
        return len(self.items) == 0
    
    @property
    def first(self) -> Optional[T]:
        """Get first item."""
        return self.items[0] if self.items else None
    
    @property
    def last(self) -> Optional[T]:
        """Get last item."""
        return self.items[-1] if self.items else None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        result = {
            "items": self.items,
            "page_size": self.page_size,
            "has_more": self.has_more,
            "has_previous": self.has_previous,
            "count": self.count,
            "method": self.method.value,
        }
        
        if self.next_cursor:
            result["next_cursor"] = self.next_cursor
        if self.previous_cursor:
            result["previous_cursor"] = self.previous_cursor
        if self.total_count is not None:
            result["total_count"] = self.total_count
        if self.total_pages is not None:
            result["total_pages"] = self.total_pages
        if self.current_page is not None:
            result["current_page"] = self.current_page
        
        return result


@dataclass
class OffsetPage(Page[T]):
    """Page with offset-specific information."""
    offset: int = 0
    
    @property
    def start_index(self) -> int:
        """1-based start index."""
        return self.offset + 1
    
    @property
    def end_index(self) -> int:
        """1-based end index."""
        return self.offset + len(self.items)


# =============================================================================
# PAGINATORS
# =============================================================================

class KeysetPaginator:
    """
    Keyset (cursor-based) pagination strategy.
    
    Uses WHERE clauses with comparison operators to paginate.
    Much faster than OFFSET for large datasets.
    """
    
    def __init__(
        self,
        order_columns: List[str],
        order_directions: Optional[List[str]] = None,
        config: Optional[PaginationConfig] = None,
    ):
        """
        Initialize keyset paginator.
        
        Args:
            order_columns: Columns to order by
            order_directions: Direction for each column (ASC/DESC)
            config: Pagination configuration
        """
        self.order_columns = order_columns
        self.order_directions = order_directions or ["ASC"] * len(order_columns)
        self.config = config or get_pagination_config()
        
        if len(self.order_columns) != len(self.order_directions):
            raise ValueError("order_columns and order_directions must have same length")
    
    def build_where_clause(
        self,
        cursor: Optional[Cursor],
        direction: CursorDirection = CursorDirection.FORWARD,
    ) -> Tuple[str, List[Any]]:
        """
        Build WHERE clause for cursor position.
        
        Args:
            cursor: Current cursor position
            direction: Pagination direction
        
        Returns:
            Tuple of (WHERE clause, parameters)
        """
        if cursor is None:
            return "", []
        
        # Build comparison based on direction
        conditions = []
        params = []
        
        for i, col in enumerate(self.order_columns):
            value = cursor.values.get(col)
            if value is None:
                continue
            
            order_dir = self.order_directions[i].upper()
            
            # Determine comparison operator
            if direction == CursorDirection.FORWARD:
                op = ">" if order_dir == "ASC" else "<"
            else:
                op = "<" if order_dir == "ASC" else ">"
            
            # Build row value comparison for multiple columns
            if i == 0:
                conditions.append(f"{col} {op} ${len(params) + 1}")
            else:
                # For multi-column, use tuple comparison
                cols = ", ".join(self.order_columns[:i+1])
                placeholders = ", ".join(f"${j+1}" for j in range(i+1))
                conditions.append(f"({cols}) {op} ({placeholders})")
            
            params.append(value)
        
        if not conditions:
            return "", []
        
        # Use the most specific condition (last one covers all columns)
        where_clause = conditions[-1]
        return f"WHERE {where_clause}", params
    
    def create_cursor_from_row(
        self,
        row: Dict[str, Any],
        direction: CursorDirection = CursorDirection.FORWARD,
    ) -> Cursor:
        """Create cursor from a result row."""
        return Cursor.from_record(row, self.order_columns, direction)
    
    async def paginate(
        self,
        execute_fn: Callable,
        query: str,
        cursor: Optional[str] = None,
        page_size: int = 20,
        direction: CursorDirection = CursorDirection.FORWARD,
    ) -> Page[Dict[str, Any]]:
        """
        Execute paginated query.
        
        Args:
            execute_fn: Function to execute SQL
            query: Base SQL query (without LIMIT)
            cursor: Encoded cursor string
            page_size: Items per page
            direction: Pagination direction
        
        Returns:
            Page of results
        """
        page_size = self.config.clamp_page_size(page_size)
        
        # Decode cursor
        decoded_cursor = None
        if cursor:
            decoded_cursor = Cursor.decode(cursor, self.config.cursor_secret)
        
        # Build WHERE clause
        where_clause, params = self.build_where_clause(decoded_cursor, direction)
        
        # Build ORDER BY
        order_parts = [
            f"{col} {dir}" 
            for col, dir in zip(self.order_columns, self.order_directions)
        ]
        order_clause = f"ORDER BY {', '.join(order_parts)}"
        
        # Fetch one extra to check if there's more
        limit_clause = f"LIMIT {page_size + 1}"
        
        # Combine query
        full_query = f"{query} {where_clause} {order_clause} {limit_clause}"
        
        # Execute
        rows = await execute_fn(full_query, params)
        
        # Check if there's more
        has_more = len(rows) > page_size
        if has_more:
            rows = rows[:page_size]
        
        # Create cursors
        next_cursor = None
        if has_more and rows:
            next_cursor = self.create_cursor_from_row(
                rows[-1], CursorDirection.FORWARD
            ).encode(self.config.cursor_secret)
        
        previous_cursor = None
        if decoded_cursor and rows:
            previous_cursor = self.create_cursor_from_row(
                rows[0], CursorDirection.BACKWARD
            ).encode(self.config.cursor_secret)
        
        return Page(
            items=rows,
            page_size=page_size,
            has_more=has_more,
            has_previous=decoded_cursor is not None,
            next_cursor=next_cursor,
            previous_cursor=previous_cursor,
            method=PaginationMethod.KEYSET,
        )


class OffsetPaginator:
    """
    Offset-based pagination strategy.
    
    Traditional pagination with page numbers.
    Simpler but slower for large datasets.
    """
    
    def __init__(self, config: Optional[PaginationConfig] = None):
        """
        Initialize offset paginator.
        
        Args:
            config: Pagination configuration
        """
        self.config = config or get_pagination_config()
    
    async def paginate(
        self,
        execute_fn: Callable,
        count_fn: Callable,
        query: str,
        page: int = 1,
        page_size: int = 20,
        include_total: bool = True,
    ) -> OffsetPage[Dict[str, Any]]:
        """
        Execute paginated query with offset.
        
        Args:
            execute_fn: Function to execute SQL
            count_fn: Function to count total rows
            query: Base SQL query
            page: Page number (1-based)
            page_size: Items per page
            include_total: Whether to count total rows
        
        Returns:
            OffsetPage of results
        """
        page = max(1, page)
        page_size = self.config.clamp_page_size(page_size)
        offset = (page - 1) * page_size
        
        # Get total count if requested
        total_count = None
        total_pages = None
        if include_total:
            total_count = await count_fn(query)
            total_pages = (total_count + page_size - 1) // page_size if total_count else 0
        
        # Build paginated query
        full_query = f"{query} LIMIT {page_size} OFFSET {offset}"
        
        # Execute
        rows = await execute_fn(full_query, ())
        
        # Determine has_more
        has_more = False
        if total_count is not None:
            has_more = offset + len(rows) < total_count
        else:
            # Fetch one extra to check
            extra_query = f"{query} LIMIT {page_size + 1} OFFSET {offset}"
            extra_rows = await execute_fn(extra_query, ())
            has_more = len(extra_rows) > page_size
        
        return OffsetPage(
            items=rows,
            page_size=page_size,
            has_more=has_more,
            has_previous=page > 1,
            total_count=total_count,
            total_pages=total_pages,
            current_page=page,
            offset=offset,
            method=PaginationMethod.OFFSET,
        )


class SmartPaginator:
    """
    Smart pagination that auto-selects best method.
    
    Chooses keyset for large tables with indexed ORDER BY,
    offset for small tables or when total count is needed.
    """
    
    def __init__(
        self,
        config: Optional[PaginationConfig] = None,
    ):
        """
        Initialize smart paginator.
        
        Args:
            config: Pagination configuration
        """
        self.config = config or get_pagination_config()
    
    def select_method(
        self,
        estimated_rows: int,
        has_indexed_order: bool,
        needs_total_count: bool,
        has_complex_order: bool,
    ) -> PaginationMethod:
        """
        Select best pagination method.
        
        Args:
            estimated_rows: Estimated total rows
            has_indexed_order: Whether ORDER BY uses indexes
            needs_total_count: Whether total count is needed
            has_complex_order: Whether ORDER BY is complex
        
        Returns:
            Recommended pagination method
        """
        # If needs total count, offset is required
        if needs_total_count:
            return PaginationMethod.OFFSET
        
        # If complex ORDER BY, use offset
        if has_complex_order:
            return PaginationMethod.OFFSET
        
        # For large tables with indexed order, use keyset
        if estimated_rows > self.config.keyset_threshold and has_indexed_order:
            return PaginationMethod.KEYSET
        
        # For small tables, offset is fine
        if estimated_rows <= self.config.keyset_threshold:
            return PaginationMethod.OFFSET
        
        # Default to keyset (faster)
        return PaginationMethod.KEYSET
    
    async def paginate(
        self,
        execute_fn: Callable,
        count_fn: Callable,
        query: str,
        order_columns: List[str],
        cursor: Optional[str] = None,
        page: Optional[int] = None,
        page_size: int = 20,
        estimated_rows: int = 0,
        has_indexed_order: bool = True,
        needs_total_count: bool = False,
    ) -> Page[Dict[str, Any]]:
        """
        Execute with auto-selected pagination.
        
        Args:
            execute_fn: Function to execute SQL
            count_fn: Function to count rows
            query: Base SQL query
            order_columns: Columns for ORDER BY
            cursor: Cursor for keyset pagination
            page: Page number for offset pagination
            page_size: Items per page
            estimated_rows: Estimated row count
            has_indexed_order: Whether order uses indexes
            needs_total_count: Whether to include total
        
        Returns:
            Paginated results
        """
        method = self.select_method(
            estimated_rows=estimated_rows,
            has_indexed_order=has_indexed_order,
            needs_total_count=needs_total_count,
            has_complex_order=len(order_columns) > 2,
        )
        
        if method == PaginationMethod.KEYSET:
            paginator = KeysetPaginator(order_columns, config=self.config)
            return await paginator.paginate(
                execute_fn, query, cursor, page_size
            )
        else:
            paginator = OffsetPaginator(config=self.config)
            return await paginator.paginate(
                execute_fn, count_fn, query, page or 1, page_size, needs_total_count
            )


# =============================================================================
# STREAMING
# =============================================================================

class StreamingPaginator:
    """
    Stream large datasets in batches.
    
    Uses server-side cursors for memory efficiency.
    """
    
    def __init__(
        self,
        batch_size: int = 100,
        config: Optional[PaginationConfig] = None,
    ):
        """
        Initialize streaming paginator.
        
        Args:
            batch_size: Number of rows per batch
            config: Pagination configuration
        """
        self.batch_size = batch_size
        self.config = config or get_pagination_config()
    
    async def stream(
        self,
        execute_fn: Callable,
        query: str,
        params: tuple = (),
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """
        Stream query results in batches.
        
        Args:
            execute_fn: Function to execute SQL
            query: SQL query
            params: Query parameters
        
        Yields:
            Batches of rows
        
        Example:
            async for batch in paginator.stream(execute, query):
                for row in batch:
                    process(row)
        """
        offset = 0
        
        while True:
            # Fetch batch
            batch_query = f"{query} LIMIT {self.batch_size} OFFSET {offset}"
            rows = await execute_fn(batch_query, params)
            
            if not rows:
                break
            
            yield rows
            
            if len(rows) < self.batch_size:
                break
            
            offset += self.batch_size
    
    async def stream_all(
        self,
        execute_fn: Callable,
        query: str,
        params: tuple = (),
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream individual rows.
        
        Args:
            execute_fn: Function to execute SQL
            query: SQL query
            params: Query parameters
        
        Yields:
            Individual rows
        """
        async for batch in self.stream(execute_fn, query, params):
            for row in batch:
                yield row


# =============================================================================
# QUERY BUILDER MIXIN
# =============================================================================

class PaginationMixin(Generic[T]):
    """
    Mixin for adding pagination to query builders.
    """
    
    async def paginate(
        self: T,
        page_size: int = 20,
        cursor: Optional[str] = None,
        page: Optional[int] = None,
        include_total: bool = False,
    ) -> Page[Dict[str, Any]]:
        """
        Paginate query results.
        
        Uses smart pagination to auto-select best method.
        
        Args:
            page_size: Items per page
            cursor: Cursor for keyset pagination
            page: Page number for offset pagination
            include_total: Include total count
        
        Returns:
            Page of results
        
        Example:
            # First page
            page = await User.select().paginate(page_size=20)
            
            # Next page using cursor
            next_page = await User.select().paginate(
                page_size=20,
                cursor=page.next_cursor
            )
        """
        # Template - actual implementation depends on query builder
        raise NotImplementedError("Query builder must implement paginate")
    
    async def cursor(
        self: T,
        after: Optional[Any] = None,
        before: Optional[Any] = None,
        limit: int = 20,
    ) -> Page[Dict[str, Any]]:
        """
        Keyset pagination with explicit cursor values.
        
        Args:
            after: Get items after this value
            before: Get items before this value
            limit: Number of items
        
        Returns:
            Page of results
        
        Example:
            # Get users created after a specific time
            page = await User.select().order_by("created_at").cursor(
                after="2024-01-15T10:30:00",
                limit=20
            )
        """
        raise NotImplementedError("Query builder must implement cursor")
    
    async def offset_paginate(
        self: T,
        page: int = 1,
        page_size: int = 20,
        include_total: bool = True,
    ) -> OffsetPage[Dict[str, Any]]:
        """
        Traditional offset pagination.
        
        Args:
            page: Page number (1-based)
            page_size: Items per page
            include_total: Include total count
        
        Returns:
            OffsetPage with page numbers
        
        Example:
            page = await User.select().offset_paginate(page=3, page_size=20)
            print(f"Page {page.current_page} of {page.total_pages}")
        """
        raise NotImplementedError("Query builder must implement offset_paginate")
    
    def stream(
        self: T,
        batch_size: int = 100,
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """
        Stream results in batches.
        
        Args:
            batch_size: Rows per batch
        
        Yields:
            Batches of rows
        
        Example:
            async for batch in User.select().stream(batch_size=100):
                for user in batch:
                    process(user)
        """
        raise NotImplementedError("Query builder must implement stream")


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "PaginationMethod",
    "CursorDirection",
    # Configuration
    "PaginationConfig",
    "get_pagination_config",
    "set_pagination_config",
    # Cursor
    "Cursor",
    # Page
    "Page",
    "OffsetPage",
    # Paginators
    "KeysetPaginator",
    "OffsetPaginator",
    "SmartPaginator",
    "StreamingPaginator",
    # Mixin
    "PaginationMixin",
]

