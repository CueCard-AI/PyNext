"""
PyNext Relationship Filter Conditions.

Simple, type-safe filter conditions for relationship queries.
Dramatically simpler than SQLAlchemy's string-based primaryjoin.

Two Syntaxes Supported:

1. Condition Functions (IDE autocomplete):
   filter=[eq("is_active", True), gte("views", 100)]

2. Tuple Syntax (SQL-like):
   filter=[("is_active", "=", True), ("views", ">=", 100)]

Both can be mixed in the same filter list.

SQLAlchemy Comparison:
    SQLAlchemy:
        primaryjoin="and_(User.id == Post.author_id, Post.is_active == true())"
        # String-based, no IDE help, error-prone
    
    PyNext:
        filter=[eq("is_active", True)]
        # Clear, type-safe, IDE autocomplete

Usage:
    from pynext.db import has_many, eq, gte, like, is_in
    
    class User(Table):
        # Only active posts
        active_posts: List[Post] = has_many(Post, filter=[
            eq("is_active", True)
        ])
        
        # Multiple conditions
        recent_popular: List[Post] = has_many(Post, filter=[
            eq("is_active", True),
            gte("views", 100),
            gte("created_at", days_ago(30))
        ])
        
        # Mix function and tuple syntax
        posts: List[Post] = has_many(Post, filter=[
            eq("is_active", True),           # Function
            ("views", ">=", 100)             # Tuple
        ])
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional, Union


# =============================================================================
# Condition Class
# =============================================================================

@dataclass
class Condition:
    """
    A single filter condition for a relationship.
    
    Represents a comparison like: field OPERATOR value
    
    Attributes:
        field: Column name to filter on (e.g., "is_active")
        operator: SQL operator (=, !=, >, >=, <, <=, LIKE, IN, IS NULL)
        value: Value to compare against
    
    Examples:
        Condition("is_active", "=", True)      # is_active = true
        Condition("views", ">=", 100)          # views >= 100
        Condition("title", "LIKE", "%python%") # title LIKE '%python%'
    """
    field: str
    operator: str
    value: Any
    
    def __post_init__(self):
        """Validate the condition."""
        if not self.field or not self.field.strip():
            raise ValueError("Condition field cannot be empty")
        
        valid_operators = {
            "=", "!=", "<>",
            ">", ">=", "<", "<=",
            "LIKE", "ILIKE", "NOT LIKE",
            "IN", "NOT IN",
            "IS NULL", "IS NOT NULL",
        }
        
        # Normalize operator to uppercase and strip whitespace
        self.operator = self.operator.strip().upper()
        
        if self.operator not in valid_operators:
            raise ValueError(
                f"Invalid operator: {self.operator}. "
                f"Valid: {', '.join(sorted(valid_operators))}"
            )
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "field": self.field,
            "operator": self.operator,
            "value": self.value,
        }
    
    def __repr__(self) -> str:
        """Human-readable representation."""
        return f"Condition({self.field!r}, {self.operator!r}, {self.value!r})"


# =============================================================================
# Condition Functions (IDE-Friendly)
# =============================================================================

def eq(field: str, value: Any) -> Condition:
    """
    Equality condition: field = value
    
    Args:
        field: Column name
        value: Value to match
    
    Returns:
        Condition for equality check
    
    Example:
        filter=[eq("is_active", True)]
        # SQL: is_active = true
    """
    return Condition(field, "=", value)


def ne(field: str, value: Any) -> Condition:
    """
    Not equal condition: field != value
    
    Args:
        field: Column name
        value: Value to not match
    
    Returns:
        Condition for inequality check
    
    Example:
        filter=[ne("status", "deleted")]
        # SQL: status != 'deleted'
    """
    return Condition(field, "!=", value)


def gt(field: str, value: Any) -> Condition:
    """
    Greater than condition: field > value
    
    Args:
        field: Column name
        value: Value to compare against
    
    Returns:
        Condition for greater than check
    
    Example:
        filter=[gt("views", 100)]
        # SQL: views > 100
    """
    return Condition(field, ">", value)


def gte(field: str, value: Any) -> Condition:
    """
    Greater than or equal condition: field >= value
    
    Args:
        field: Column name
        value: Value to compare against
    
    Returns:
        Condition for greater than or equal check
    
    Example:
        filter=[gte("price", 10.00)]
        # SQL: price >= 10.00
    """
    return Condition(field, ">=", value)


def lt(field: str, value: Any) -> Condition:
    """
    Less than condition: field < value
    
    Args:
        field: Column name
        value: Value to compare against
    
    Returns:
        Condition for less than check
    
    Example:
        filter=[lt("age", 18)]
        # SQL: age < 18
    """
    return Condition(field, "<", value)


def lte(field: str, value: Any) -> Condition:
    """
    Less than or equal condition: field <= value
    
    Args:
        field: Column name
        value: Value to compare against
    
    Returns:
        Condition for less than or equal check
    
    Example:
        filter=[lte("quantity", 0)]
        # SQL: quantity <= 0
    """
    return Condition(field, "<=", value)


def like(field: str, pattern: str) -> Condition:
    """
    LIKE pattern matching condition.
    
    Args:
        field: Column name
        pattern: LIKE pattern with % wildcards
    
    Returns:
        Condition for LIKE check
    
    Example:
        filter=[like("title", "%python%")]
        # SQL: title LIKE '%python%'
        
        filter=[like("email", "%@gmail.com")]
        # SQL: email LIKE '%@gmail.com'
    """
    return Condition(field, "LIKE", pattern)


def ilike(field: str, pattern: str) -> Condition:
    """
    Case-insensitive LIKE pattern matching (PostgreSQL).
    
    Args:
        field: Column name
        pattern: LIKE pattern with % wildcards
    
    Returns:
        Condition for case-insensitive LIKE check
    
    Example:
        filter=[ilike("name", "%john%")]
        # SQL: name ILIKE '%john%' (matches John, JOHN, john)
    """
    return Condition(field, "ILIKE", pattern)


def not_like(field: str, pattern: str) -> Condition:
    """
    NOT LIKE pattern matching condition.
    
    Args:
        field: Column name
        pattern: LIKE pattern to exclude
    
    Returns:
        Condition for NOT LIKE check
    
    Example:
        filter=[not_like("email", "%@test.com")]
        # SQL: email NOT LIKE '%@test.com'
    """
    return Condition(field, "NOT LIKE", pattern)


def is_in(field: str, values: List[Any]) -> Condition:
    """
    IN list condition: field IN (values)
    
    Args:
        field: Column name
        values: List of values to match
    
    Returns:
        Condition for IN check
    
    Example:
        filter=[is_in("status", ["active", "pending"])]
        # SQL: status IN ('active', 'pending')
        
        filter=[is_in("category_id", [1, 2, 3])]
        # SQL: category_id IN (1, 2, 3)
    """
    if not isinstance(values, (list, tuple, set)):
        raise ValueError(f"is_in requires a list, got: {type(values)}")
    return Condition(field, "IN", list(values))


def not_in(field: str, values: List[Any]) -> Condition:
    """
    NOT IN list condition: field NOT IN (values)
    
    Args:
        field: Column name
        values: List of values to exclude
    
    Returns:
        Condition for NOT IN check
    
    Example:
        filter=[not_in("status", ["deleted", "archived"])]
        # SQL: status NOT IN ('deleted', 'archived')
    """
    if not isinstance(values, (list, tuple, set)):
        raise ValueError(f"not_in requires a list, got: {type(values)}")
    return Condition(field, "NOT IN", list(values))


def is_null(field: str, null: bool = True) -> Condition:
    """
    NULL check condition: field IS NULL or field IS NOT NULL
    
    Args:
        field: Column name
        null: True for IS NULL, False for IS NOT NULL
    
    Returns:
        Condition for NULL check
    
    Examples:
        filter=[is_null("deleted_at")]
        # SQL: deleted_at IS NULL
        
        filter=[is_null("deleted_at", False)]
        # SQL: deleted_at IS NOT NULL
    """
    operator = "IS NULL" if null else "IS NOT NULL"
    return Condition(field, operator, None)


# =============================================================================
# Convenience Aliases
# =============================================================================

# Common aliases for better readability
equals = eq
not_equals = ne
greater_than = gt
greater_than_or_equal = gte
less_than = lt
less_than_or_equal = lte
contains = like  # Alias for string contains


# =============================================================================
# Condition Type
# =============================================================================

# Type alias for condition input (function result or tuple)
ConditionInput = Union[Condition, tuple]


def normalize_condition(c: ConditionInput) -> Condition:
    """
    Normalize a condition input to a Condition object.
    
    Accepts:
    - Condition object (returned as-is)
    - 3-tuple: (field, operator, value)
    
    Args:
        c: Condition input (Condition or tuple)
    
    Returns:
        Normalized Condition object
    
    Raises:
        ValueError: If input is invalid
    
    Examples:
        normalize_condition(eq("active", True))  # Returns as-is
        normalize_condition(("active", "=", True))  # Converts to Condition
    """
    if isinstance(c, Condition):
        return c
    
    if isinstance(c, tuple):
        if len(c) != 3:
            raise ValueError(
                f"Tuple condition must have 3 elements (field, operator, value), "
                f"got {len(c)}: {c}"
            )
        field, operator, value = c
        return Condition(field, operator, value)
    
    raise ValueError(
        f"Invalid condition type: {type(c)}. "
        f"Expected Condition or (field, operator, value) tuple."
    )


def normalize_conditions(conditions: List[ConditionInput]) -> List[Condition]:
    """
    Normalize a list of condition inputs to Condition objects.
    
    Args:
        conditions: List of Condition objects or tuples
    
    Returns:
        List of normalized Condition objects
    
    Example:
        normalize_conditions([
            eq("active", True),           # Function
            ("views", ">=", 100)          # Tuple
        ])
        # Returns: [Condition("active", "=", True), Condition("views", ">=", 100)]
    """
    return [normalize_condition(c) for c in conditions]

