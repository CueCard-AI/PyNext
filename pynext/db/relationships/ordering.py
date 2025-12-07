"""
PyNext Relationship Ordering.

Dead simple ordering for relationships with SQL-like string syntax.

Design Philosophy:
- Natural SQL syntax: "created_at desc" - anyone who knows SQL gets it
- Default ascending: "name" means "name asc" (like SQL)
- List for multiple: ["a desc", "b"] - obvious and simple
- Applied at SQL level: Efficient ORDER BY clause, not Python sorting
- Works everywhere: has_many, many_to_many, eager loading

SQLAlchemy Comparison:
    # SQLAlchemy - Verbose, requires imports
    from sqlalchemy import desc
    posts = relationship("Post", order_by=desc(Post.created_at))
    
    # PyNext - Dead simple string syntax
    posts: List[Post] = has_many(Post, order_by="created_at desc")

Django Comparison:
    # Django - Model-level only or verbose Prefetch
    class Post(models.Model):
        class Meta:
            ordering = ['-created_at']  # Affects ALL queries!
    
    # PyNext - Per-relationship, clean syntax
    posts: List[Post] = has_many(Post, order_by="created_at desc")

Usage:
    from pynext.db import Table, has_many, many_to_many
    
    class User(Table):
        # Single column ordering
        posts: List[Post] = has_many(Post, order_by="created_at desc")
        
        # Multiple column ordering
        comments: List[Comment] = has_many(
            Comment,
            order_by=["pinned desc", "created_at desc"]
        )
        
        # Ascending is default
        friends: List[User] = many_to_many(User, order_by="name")
        
        # NULLS FIRST/LAST support
        tasks: List[Task] = has_many(
            Task,
            order_by=["priority desc", "due_date nulls last"]
        )
    
    # Results are automatically ordered
    user.posts     # Ordered by created_at DESC
    user.comments  # Ordered by pinned DESC, then created_at DESC
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, List, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    pass


# =============================================================================
# OrderSpec - Represents a Single Order Clause
# =============================================================================

@dataclass
class OrderSpec:
    """
    Represents a single ORDER BY clause specification.
    
    This is the internal representation of ordering instructions.
    Users don't create these directly - they use string syntax.
    
    Attributes:
        column: Column name to order by (e.g., "created_at")
        direction: Sort direction ("asc" or "desc")
        nulls: NULL handling ("first", "last", or None)
    
    Examples:
        OrderSpec("created_at", "desc")       # ORDER BY created_at DESC
        OrderSpec("name", "asc")              # ORDER BY name ASC
        OrderSpec("due_date", "asc", "last")  # ORDER BY due_date ASC NULLS LAST
    """
    
    column: str
    direction: str = "asc"
    nulls: Optional[str] = None
    
    def __post_init__(self):
        """Validate and normalize values."""
        # Normalize direction
        self.direction = self.direction.lower()
        if self.direction not in ("asc", "desc"):
            raise ValueError(
                f"Invalid direction '{self.direction}'. "
                f"Must be 'asc' or 'desc'."
            )
        
        # Normalize nulls
        if self.nulls is not None:
            self.nulls = self.nulls.lower()
            if self.nulls not in ("first", "last"):
                raise ValueError(
                    f"Invalid nulls '{self.nulls}'. "
                    f"Must be 'first' or 'last'."
                )
        
        # Validate column name
        if not self.column:
            raise ValueError("Column name cannot be empty.")
        
        # Check for SQL injection patterns (basic check)
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', self.column):
            raise ValueError(
                f"Invalid column name '{self.column}'. "
                f"Column names must be valid identifiers."
            )
    
    def to_sql(self, table_alias: Optional[str] = None) -> str:
        """
        Convert to SQL ORDER BY clause fragment.
        
        Args:
            table_alias: Optional table alias to prefix column
        
        Returns:
            SQL string like "created_at DESC" or "t.name ASC NULLS LAST"
        
        Examples:
            OrderSpec("name", "asc").to_sql()
            # Returns: "name ASC"
            
            OrderSpec("created_at", "desc").to_sql("posts")
            # Returns: "posts.created_at DESC"
            
            OrderSpec("due_date", "asc", "last").to_sql()
            # Returns: "due_date ASC NULLS LAST"
        """
        parts = []
        
        # Column (with optional alias)
        if table_alias:
            parts.append(f"{table_alias}.{self.column}")
        else:
            parts.append(self.column)
        
        # Direction
        parts.append(self.direction.upper())
        
        # NULLS handling
        if self.nulls:
            parts.append(f"NULLS {self.nulls.upper()}")
        
        return " ".join(parts)
    
    def __str__(self) -> str:
        """String representation matching input syntax."""
        result = f"{self.column} {self.direction}"
        if self.nulls:
            result += f" nulls {self.nulls}"
        return result
    
    def __repr__(self) -> str:
        """Detailed representation."""
        nulls_str = f", nulls='{self.nulls}'" if self.nulls else ""
        return f"OrderSpec('{self.column}', '{self.direction}'{nulls_str})"


# =============================================================================
# Parsing Functions
# =============================================================================

def parse_order_spec(spec_str: str) -> OrderSpec:
    """
    Parse a single order specification string.
    
    Supports these formats:
        "column"                    -> OrderSpec("column", "asc")
        "column asc"                -> OrderSpec("column", "asc")
        "column desc"               -> OrderSpec("column", "desc")
        "column nulls first"        -> OrderSpec("column", "asc", "first")
        "column desc nulls last"    -> OrderSpec("column", "desc", "last")
    
    Args:
        spec_str: Order specification string
    
    Returns:
        OrderSpec instance
    
    Raises:
        ValueError: If the specification is invalid
    
    Examples:
        parse_order_spec("created_at desc")
        # Returns: OrderSpec("created_at", "desc")
        
        parse_order_spec("name")
        # Returns: OrderSpec("name", "asc")
        
        parse_order_spec("priority desc nulls last")
        # Returns: OrderSpec("priority", "desc", "last")
    """
    if not spec_str or not spec_str.strip():
        raise ValueError("Order specification cannot be empty.")
    
    # Normalize whitespace
    spec_str = " ".join(spec_str.lower().split())
    
    # Parse with regex
    # Pattern: column [asc|desc] [nulls first|last]
    pattern = r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*(asc|desc)?\s*(nulls\s+(first|last))?$'
    match = re.match(pattern, spec_str, re.IGNORECASE)
    
    if not match:
        raise ValueError(
            f"Invalid order specification: '{spec_str}'. "
            f"Expected format: 'column [asc|desc] [nulls first|last]'"
        )
    
    column = match.group(1)
    direction = match.group(2) or "asc"
    nulls = match.group(4)  # Group 4 is the actual nulls value (first/last)
    
    return OrderSpec(column=column, direction=direction, nulls=nulls)


def parse_order_by(
    order_by: Optional[Union[str, List[str]]]
) -> List[OrderSpec]:
    """
    Parse order_by parameter into list of OrderSpec.
    
    This is the main entry point for parsing user-provided ordering.
    Handles:
        - None (returns empty list)
        - Single string
        - List of strings
    
    Args:
        order_by: User-provided order_by value
    
    Returns:
        List of OrderSpec instances (empty if None)
    
    Raises:
        ValueError: If any specification is invalid
    
    Examples:
        parse_order_by(None)
        # Returns: []
        
        parse_order_by("created_at desc")
        # Returns: [OrderSpec("created_at", "desc")]
        
        parse_order_by(["pinned desc", "created_at desc"])
        # Returns: [OrderSpec("pinned", "desc"), OrderSpec("created_at", "desc")]
    """
    if order_by is None:
        return []
    
    if isinstance(order_by, str):
        return [parse_order_spec(order_by)]
    
    if isinstance(order_by, (list, tuple)):
        return [parse_order_spec(spec) for spec in order_by]
    
    raise TypeError(
        f"order_by must be str, list of str, or None. Got: {type(order_by).__name__}"
    )


# =============================================================================
# SQL Generation
# =============================================================================

def build_order_clause(
    specs: List[OrderSpec],
    table_alias: Optional[str] = None,
    include_keyword: bool = True,
) -> str:
    """
    Build SQL ORDER BY clause from OrderSpec list.
    
    Args:
        specs: List of OrderSpec instances
        table_alias: Optional table alias for column prefixing
        include_keyword: Whether to include "ORDER BY" keyword
    
    Returns:
        SQL ORDER BY clause (empty string if no specs)
    
    Examples:
        specs = [OrderSpec("created_at", "desc")]
        build_order_clause(specs)
        # Returns: "ORDER BY created_at DESC"
        
        specs = [OrderSpec("pinned", "desc"), OrderSpec("name", "asc")]
        build_order_clause(specs, table_alias="t")
        # Returns: "ORDER BY t.pinned DESC, t.name ASC"
        
        build_order_clause(specs, include_keyword=False)
        # Returns: "t.pinned DESC, t.name ASC"
    """
    if not specs:
        return ""
    
    columns = [spec.to_sql(table_alias) for spec in specs]
    clause = ", ".join(columns)
    
    if include_keyword:
        return f"ORDER BY {clause}"
    else:
        return clause


def build_order_columns(
    specs: List[OrderSpec],
    table_alias: Optional[str] = None,
) -> List[str]:
    """
    Build list of SQL order column expressions.
    
    Useful when you need the individual column expressions
    without the ORDER BY keyword.
    
    Args:
        specs: List of OrderSpec instances
        table_alias: Optional table alias
    
    Returns:
        List of SQL expressions
    
    Example:
        specs = [OrderSpec("a", "desc"), OrderSpec("b", "asc")]
        build_order_columns(specs)
        # Returns: ["a DESC", "b ASC"]
    """
    return [spec.to_sql(table_alias) for spec in specs]


# =============================================================================
# Validation Helpers
# =============================================================================

def validate_order_by(
    order_by: Optional[Union[str, List[str]]],
    allowed_columns: Optional[List[str]] = None,
) -> List[OrderSpec]:
    """
    Parse and validate order_by, optionally checking column names.
    
    Args:
        order_by: User-provided order_by value
        allowed_columns: Optional list of allowed column names
    
    Returns:
        List of validated OrderSpec instances
    
    Raises:
        ValueError: If validation fails
    
    Example:
        validate_order_by("name desc", allowed_columns=["name", "created_at"])
        # Returns: [OrderSpec("name", "desc")]
        
        validate_order_by("invalid_col", allowed_columns=["name"])
        # Raises: ValueError("Column 'invalid_col' not in allowed columns")
    """
    specs = parse_order_by(order_by)
    
    if allowed_columns is not None:
        allowed_set = set(allowed_columns)
        for spec in specs:
            if spec.column not in allowed_set:
                raise ValueError(
                    f"Column '{spec.column}' not in allowed columns: "
                    f"{sorted(allowed_columns)}"
                )
    
    return specs


def normalize_order_by(
    order_by: Optional[Union[str, List[str]]]
) -> Optional[List[str]]:
    """
    Normalize order_by to consistent list format.
    
    This is useful for storing order_by in a consistent format.
    
    Args:
        order_by: User-provided order_by value
    
    Returns:
        List of normalized strings, or None if input is None
    
    Examples:
        normalize_order_by("created_at DESC")
        # Returns: ["created_at desc"]
        
        normalize_order_by(["PINNED desc", "name ASC"])
        # Returns: ["pinned desc", "name asc"]
        
        normalize_order_by(None)
        # Returns: None
    """
    if order_by is None:
        return None
    
    specs = parse_order_by(order_by)
    return [str(spec) for spec in specs]


# =============================================================================
# Ordering Configuration for Relationships
# =============================================================================

@dataclass
class OrderingConfig:
    """
    Configuration for relationship ordering.
    
    Stores the parsed ordering specifications for a relationship.
    Created automatically when order_by is specified on has_many/many_to_many.
    
    Attributes:
        specs: List of OrderSpec instances
        raw: Original raw order_by value (for serialization)
    """
    
    specs: List[OrderSpec] = field(default_factory=list)
    raw: Optional[Union[str, List[str]]] = None
    
    @classmethod
    def from_order_by(
        cls,
        order_by: Optional[Union[str, List[str]]]
    ) -> "OrderingConfig":
        """
        Create OrderingConfig from order_by parameter.
        
        Args:
            order_by: User-provided order_by value
        
        Returns:
            OrderingConfig instance
        """
        specs = parse_order_by(order_by)
        return cls(specs=specs, raw=order_by)
    
    @property
    def has_ordering(self) -> bool:
        """Return True if ordering is configured."""
        return len(self.specs) > 0
    
    def to_sql(
        self,
        table_alias: Optional[str] = None,
        include_keyword: bool = True,
    ) -> str:
        """Build SQL ORDER BY clause."""
        return build_order_clause(self.specs, table_alias, include_keyword)
    
    def get_columns(self, table_alias: Optional[str] = None) -> List[str]:
        """Get list of SQL order column expressions."""
        return build_order_columns(self.specs, table_alias)
    
    def merge_with(self, other: "OrderingConfig") -> "OrderingConfig":
        """
        Merge with another OrderingConfig.
        
        The other config's specs are appended after this config's specs.
        Useful for combining relationship-level and query-level ordering.
        
        Args:
            other: OrderingConfig to merge with
        
        Returns:
            New merged OrderingConfig
        """
        merged_specs = self.specs + other.specs
        return OrderingConfig(specs=merged_specs, raw=None)
    
    def override_with(self, other: "OrderingConfig") -> "OrderingConfig":
        """
        Override this config with another.
        
        If other has ordering, it completely replaces this config.
        If other is empty, this config is kept.
        
        Args:
            other: OrderingConfig to potentially override with
        
        Returns:
            The overriding config if it has ordering, else this config
        """
        if other.has_ordering:
            return other
        return self
    
    def __bool__(self) -> bool:
        """Return True if ordering is configured."""
        return self.has_ordering
    
    def __len__(self) -> int:
        """Return number of order specs."""
        return len(self.specs)
    
    def __repr__(self) -> str:
        """Detailed representation."""
        if not self.specs:
            return "OrderingConfig()"
        specs_str = ", ".join(repr(s) for s in self.specs)
        return f"OrderingConfig([{specs_str}])"


# =============================================================================
# Convenience Functions
# =============================================================================

def asc(column: str, nulls: Optional[str] = None) -> OrderSpec:
    """
    Create ascending OrderSpec.
    
    This is an alternative to string syntax for those who prefer functions.
    
    Args:
        column: Column name
        nulls: Optional NULLS handling ("first" or "last")
    
    Returns:
        OrderSpec with ascending direction
    
    Example:
        asc("name")           # Same as "name asc"
        asc("due_date", "last")  # Same as "due_date asc nulls last"
    """
    return OrderSpec(column=column, direction="asc", nulls=nulls)


def desc(column: str, nulls: Optional[str] = None) -> OrderSpec:
    """
    Create descending OrderSpec.
    
    This is an alternative to string syntax for those who prefer functions.
    
    Args:
        column: Column name
        nulls: Optional NULLS handling ("first" or "last")
    
    Returns:
        OrderSpec with descending direction
    
    Example:
        desc("created_at")         # Same as "created_at desc"
        desc("priority", "first")  # Same as "priority desc nulls first"
    """
    return OrderSpec(column=column, direction="desc", nulls=nulls)


# =============================================================================
# Sorting Helper for In-Memory Sorting
# =============================================================================

def sort_items(
    items: List[Any],
    specs: List[OrderSpec],
    key_func: Optional[callable] = None,
) -> List[Any]:
    """
    Sort a list of items according to OrderSpec.
    
    This is used for in-memory sorting when items are already loaded.
    For database queries, use build_order_clause instead.
    
    Args:
        items: List of items to sort
        specs: List of OrderSpec instances
        key_func: Optional function to extract sortable value from item
                  Default: getattr(item, column)
    
    Returns:
        New sorted list (original is not modified)
    
    Example:
        posts = [Post(created_at=date1), Post(created_at=date2)]
        specs = [OrderSpec("created_at", "desc")]
        sorted_posts = sort_items(posts, specs)
    """
    if not specs or not items:
        return list(items)
    
    def make_sort_key(item):
        """Create sort key tuple from item."""
        keys = []
        for spec in specs:
            if key_func:
                value = key_func(item, spec.column)
            else:
                value = getattr(item, spec.column, None)
            
            # Handle None values for NULLS FIRST/LAST
            if value is None:
                if spec.nulls == "first":
                    # Use a value that sorts first
                    null_key = (0,)
                else:
                    # Default: NULLS LAST (use a value that sorts last)
                    null_key = (2,)
                keys.append((null_key, None))
            else:
                keys.append(((1,), value))
        
        return keys
    
    # Determine reverse flags per column
    # Python's sort is stable, so we sort multiple times in reverse order
    result = list(items)
    
    for spec in reversed(specs):
        reverse = spec.direction == "desc"
        
        def single_key(item, s=spec):
            if key_func:
                value = key_func(item, s.column)
            else:
                value = getattr(item, s.column, None)
            
            if value is None:
                if s.nulls == "first":
                    return (0, None)
                else:
                    return (2, None)
            return (1, value)
        
        result.sort(key=single_key, reverse=reverse)
    
    return result

