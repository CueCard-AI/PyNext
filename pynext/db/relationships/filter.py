"""
PyNext Relationship Filter.

Parses and applies filter conditions to relationship queries.
Supports both Condition functions and tuple syntax.

Usage:
    from pynext.db.relationships.filter import RelationshipFilter
    from pynext.db.relationships.conditions import eq, gte
    
    # Create filter from conditions
    rf = RelationshipFilter([
        eq("is_active", True),
        gte("views", 100),
        ("created_at", ">=", days_ago(30))  # Tuple also works
    ])
    
    # Apply to a query
    query = Post.select().where(author_id=user.id)
    filtered_query = rf.apply_to_query(query)
    posts = await filtered_query
"""

from __future__ import annotations

from typing import Any, List, Optional, TYPE_CHECKING, Union

from .conditions import Condition, ConditionInput, normalize_condition

if TYPE_CHECKING:
    from pynext.db.query import Query


class RelationshipFilter:
    """
    Parses and applies filter conditions to relationship queries.
    
    This is the core class that handles filtered relationships.
    It normalizes both Condition objects and tuples into a unified
    format, then applies them to Query objects.
    
    Attributes:
        conditions: List of normalized Condition objects
    
    Example:
        filter = RelationshipFilter([
            eq("is_active", True),
            ("views", ">=", 100)
        ])
        
        query = filter.apply_to_query(Post.select())
    """
    
    def __init__(self, conditions: List[ConditionInput]):
        """
        Initialize filter with conditions.
        
        Args:
            conditions: List of Condition objects or (field, op, value) tuples
        
        Raises:
            ValueError: If any condition is invalid
        """
        if conditions is None:
            self.conditions = []
        else:
            self.conditions = [normalize_condition(c) for c in conditions]
    
    def apply_to_query(self, query: "Query") -> "Query":
        """
        Apply all filter conditions to a query.
        
        Args:
            query: Query object to filter
        
        Returns:
            Filtered query with all conditions applied
        
        Example:
            filtered_query = filter.apply_to_query(Post.select())
        """
        for condition in self.conditions:
            query = self._apply_condition(query, condition)
        return query
    
    def _apply_condition(self, query: "Query", condition: Condition) -> "Query":
        """
        Apply a single condition to a query.
        
        Maps Condition operators to Query methods.
        
        Args:
            query: Query to modify
            condition: Condition to apply
        
        Returns:
            Modified query
        """
        field = condition.field
        op = condition.operator
        value = condition.value
        
        # Map operators to Query methods
        if op == "=":
            return query.where(**{field: value})
        
        elif op in ("!=", "<>"):
            return query.where_not(**{field: value})
        
        elif op == ">":
            return query.where_gt(**{field: value})
        
        elif op == ">=":
            return query.where_gte(**{field: value})
        
        elif op == "<":
            return query.where_lt(**{field: value})
        
        elif op == "<=":
            return query.where_lte(**{field: value})
        
        elif op == "LIKE":
            return query.where_like(**{field: value})
        
        elif op == "ILIKE":
            # PostgreSQL case-insensitive LIKE
            # Fall back to LIKE for databases that don't support ILIKE
            if hasattr(query, 'where_ilike'):
                return query.where_ilike(**{field: value})
            return query.where_like(**{field: value})
        
        elif op == "NOT LIKE":
            if hasattr(query, 'where_not_like'):
                return query.where_not_like(**{field: value})
            # Fallback: use raw where if method not available
            return query.where_not(**{field: value})
        
        elif op == "IN":
            return query.where_in(**{field: value})
        
        elif op == "NOT IN":
            if hasattr(query, 'where_not_in'):
                return query.where_not_in(**{field: value})
            # Fallback for older Query implementations
            return query.where_not_in(**{field: value})
        
        elif op == "IS NULL":
            return query.where_null(field)
        
        elif op == "IS NOT NULL":
            return query.where_not_null(field)
        
        else:
            raise ValueError(f"Unsupported operator: {op}")
    
    def is_empty(self) -> bool:
        """Check if filter has no conditions."""
        return len(self.conditions) == 0
    
    def __len__(self) -> int:
        """Return number of conditions."""
        return len(self.conditions)
    
    def __bool__(self) -> bool:
        """Return True if filter has conditions."""
        return len(self.conditions) > 0
    
    def __repr__(self) -> str:
        """Human-readable representation."""
        if not self.conditions:
            return "RelationshipFilter([])"
        
        cond_strs = [repr(c) for c in self.conditions]
        return f"RelationshipFilter([{', '.join(cond_strs)}])"
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "conditions": [c.to_dict() for c in self.conditions]
        }
    
    @classmethod
    def from_list(
        cls,
        conditions: Optional[List[ConditionInput]]
    ) -> Optional["RelationshipFilter"]:
        """
        Create filter from condition list, or None if empty.
        
        Args:
            conditions: List of conditions or None
        
        Returns:
            RelationshipFilter or None if no conditions
        """
        if not conditions:
            return None
        return cls(conditions)


def parse_filter(
    filter_input: Optional[Union[List[ConditionInput], "RelationshipFilter"]]
) -> Optional[RelationshipFilter]:
    """
    Parse filter input into RelationshipFilter.
    
    Accepts:
    - None (returns None)
    - List of Condition/tuples (creates RelationshipFilter)
    - RelationshipFilter (returns as-is)
    
    Args:
        filter_input: Filter specification
    
    Returns:
        RelationshipFilter or None
    
    Example:
        # All of these work:
        parse_filter(None)
        parse_filter([eq("active", True)])
        parse_filter([("active", "=", True)])
        parse_filter(RelationshipFilter([...]))
    """
    if filter_input is None:
        return None
    
    if isinstance(filter_input, RelationshipFilter):
        return filter_input
    
    if isinstance(filter_input, list):
        if not filter_input:
            return None
        return RelationshipFilter(filter_input)
    
    raise ValueError(
        f"Invalid filter type: {type(filter_input)}. "
        f"Expected list of conditions or RelationshipFilter."
    )

