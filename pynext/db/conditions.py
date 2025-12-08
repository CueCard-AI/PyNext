"""
PyNext Query Condition Functions.

Type-safe, composable condition builders for database queries.
These functions create Condition objects that get compiled into AST nodes.

Design Principles:
- Stupid simple: gt("age", 18) is obvious
- Type-safe: IDE autocomplete works
- Composable: and_(c1, c2), or_(c1, c2)
- AI-friendly: One function per operation, clear naming

Usage:
    from pynext.db import gt, eq, contains, and_, or_
    
    # Simple conditions
    users = await User.q(gt("age", 18))
    users = await User.q(eq("status", "active"))
    
    # Combined conditions (implicit AND)
    users = await User.q(gt("age", 18), eq("status", "active"))
    
    # Explicit logical operators
    users = await User.q(or_(eq("role", "admin"), eq("role", "moderator")))
    
    # Nested conditions
    users = await User.q(
        and_(
            gt("age", 18),
            or_(eq("role", "admin"), eq("role", "moderator"))
        )
    )
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional, Union


# =============================================================================
# Operator Enum
# =============================================================================

class Operator(str, Enum):
    """SQL comparison operators."""
    EQ = "="
    NE = "!="
    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="
    LIKE = "LIKE"
    ILIKE = "ILIKE"
    IN = "IN"
    NOT_IN = "NOT IN"
    IS_NULL = "IS NULL"
    IS_NOT_NULL = "IS NOT NULL"
    BETWEEN = "BETWEEN"
    CONTAINS = "@>"        # PostgreSQL array/jsonb contains
    CONTAINED_BY = "<@"    # PostgreSQL contained by
    OVERLAPS = "&&"        # PostgreSQL array overlap
    

class LogicalOp(str, Enum):
    """Logical operators for combining conditions."""
    AND = "AND"
    OR = "OR"
    NOT = "NOT"


# =============================================================================
# Condition Classes
# =============================================================================

@dataclass
class Condition:
    """
    A single field condition.
    
    Represents: field op value
    Example: age > 18, status = 'active', name LIKE '%john%'
    
    Attributes:
        field: Column name (can include table prefix: "users.age")
        op: Comparison operator
        value: Value to compare against (will become a parameter)
        value2: Second value for BETWEEN operator
    """
    field: str
    op: Operator
    value: Any
    value2: Any = None  # For BETWEEN
    
    def __repr__(self) -> str:
        if self.op == Operator.BETWEEN:
            return f"Condition({self.field!r} BETWEEN {self.value!r} AND {self.value2!r})"
        elif self.op in (Operator.IS_NULL, Operator.IS_NOT_NULL):
            return f"Condition({self.field!r} {self.op.value})"
        return f"Condition({self.field!r} {self.op.value} {self.value!r})"
    
    def to_dict(self) -> dict:
        """Convert to AST dictionary format."""
        result = {
            "type": "condition",
            "field": self.field,
            "op": self.op.value,
        }
        if self.op not in (Operator.IS_NULL, Operator.IS_NOT_NULL):
            result["value"] = self.value
        if self.op == Operator.BETWEEN:
            result["value2"] = self.value2
        return result


@dataclass
class LogicalCondition:
    """
    A logical combination of conditions.
    
    Represents: condition AND/OR condition
    Example: (age > 18) AND (status = 'active')
    
    Attributes:
        op: Logical operator (AND, OR, NOT)
        conditions: List of Condition or LogicalCondition objects
    """
    op: LogicalOp
    conditions: List[Union[Condition, "LogicalCondition"]] = field(default_factory=list)
    
    def __repr__(self) -> str:
        conds = ", ".join(repr(c) for c in self.conditions)
        return f"{self.op.value}({conds})"
    
    def to_dict(self) -> dict:
        """Convert to AST dictionary format."""
        return {
            "type": "logical",
            "op": self.op.value,
            "conditions": [c.to_dict() for c in self.conditions],
        }


@dataclass 
class RawCondition:
    """
    A raw SQL condition string.
    
    Used for escape hatches when the query builder isn't enough.
    
    Attributes:
        sql: Raw SQL string with $1, $2, ... placeholders
        params: Parameter values
    """
    sql: str
    params: List[Any] = field(default_factory=list)
    
    def __repr__(self) -> str:
        return f"RawCondition({self.sql!r}, {self.params!r})"
    
    def to_dict(self) -> dict:
        """Convert to AST dictionary format."""
        return {
            "type": "raw",
            "sql": self.sql,
            "params": self.params,
        }


# Type alias for any condition type
ConditionType = Union[Condition, LogicalCondition, RawCondition]


# =============================================================================
# Condition Factory Functions
# =============================================================================

def eq(field: str, value: Any) -> Condition:
    """
    Equal to: field = value
    
    Examples:
        eq("status", "active")     → status = 'active'
        eq("age", 18)              → age = 18
        eq("is_admin", True)       → is_admin = true
    """
    return Condition(field=field, op=Operator.EQ, value=value)


def ne(field: str, value: Any) -> Condition:
    """
    Not equal to: field != value
    
    Examples:
        ne("status", "deleted")    → status != 'deleted'
        ne("role", "guest")        → role != 'guest'
    """
    return Condition(field=field, op=Operator.NE, value=value)


def gt(field: str, value: Any) -> Condition:
    """
    Greater than: field > value
    
    Examples:
        gt("age", 18)              → age > 18
        gt("price", 100.0)         → price > 100.0
        gt("created_at", date)     → created_at > '2024-01-01'
    """
    return Condition(field=field, op=Operator.GT, value=value)


def gte(field: str, value: Any) -> Condition:
    """
    Greater than or equal: field >= value
    
    Examples:
        gte("age", 18)             → age >= 18
        gte("score", 80)           → score >= 80
    """
    return Condition(field=field, op=Operator.GTE, value=value)


def lt(field: str, value: Any) -> Condition:
    """
    Less than: field < value
    
    Examples:
        lt("age", 65)              → age < 65
        lt("stock", 10)            → stock < 10
    """
    return Condition(field=field, op=Operator.LT, value=value)


def lte(field: str, value: Any) -> Condition:
    """
    Less than or equal: field <= value
    
    Examples:
        lte("price", 100)          → price <= 100
        lte("priority", 5)         → priority <= 5
    """
    return Condition(field=field, op=Operator.LTE, value=value)


def like(field: str, pattern: str) -> Condition:
    """
    LIKE pattern match (case-sensitive): field LIKE pattern
    
    Use % for wildcards:
    - 'john%' matches 'john', 'johnny', 'johnson'
    - '%john' matches 'john', 'big john'
    - '%john%' matches anything containing 'john'
    
    Examples:
        like("name", "john%")      → name LIKE 'john%'
        like("email", "%@gmail.com") → email LIKE '%@gmail.com'
    """
    return Condition(field=field, op=Operator.LIKE, value=pattern)


def ilike(field: str, pattern: str) -> Condition:
    """
    ILIKE pattern match (case-insensitive): field ILIKE pattern
    
    Same as like() but case-insensitive.
    PostgreSQL specific.
    
    Examples:
        ilike("name", "john%")     → name ILIKE 'john%' (matches 'John', 'JOHN')
    """
    return Condition(field=field, op=Operator.ILIKE, value=pattern)


def contains(field: str, substring: str) -> Condition:
    """
    Contains substring (case-insensitive): field ILIKE '%substring%'
    
    Convenience wrapper around ilike with wildcards.
    
    Examples:
        contains("name", "john")   → name ILIKE '%john%'
        contains("bio", "python")  → bio ILIKE '%python%'
    """
    return Condition(field=field, op=Operator.ILIKE, value=f"%{substring}%")


def startswith(field: str, prefix: str) -> Condition:
    """
    Starts with prefix (case-insensitive): field ILIKE 'prefix%'
    
    Examples:
        startswith("name", "Dr.")  → name ILIKE 'Dr.%'
        startswith("url", "https") → url ILIKE 'https%'
    """
    return Condition(field=field, op=Operator.ILIKE, value=f"{prefix}%")


def endswith(field: str, suffix: str) -> Condition:
    """
    Ends with suffix (case-insensitive): field ILIKE '%suffix'
    
    Examples:
        endswith("email", "@gmail.com") → email ILIKE '%@gmail.com'
        endswith("file", ".pdf")        → file ILIKE '%.pdf'
    """
    return Condition(field=field, op=Operator.ILIKE, value=f"%{suffix}")


def in_(field: str, values: List[Any]) -> Condition:
    """
    In list: field IN (value1, value2, ...)
    
    Examples:
        in_("status", ["active", "pending"])  → status IN ('active', 'pending')
        in_("id", [1, 2, 3])                  → id IN (1, 2, 3)
    """
    return Condition(field=field, op=Operator.IN, value=values)


def not_in(field: str, values: List[Any]) -> Condition:
    """
    Not in list: field NOT IN (value1, value2, ...)
    
    Examples:
        not_in("status", ["deleted", "banned"]) → status NOT IN ('deleted', 'banned')
    """
    return Condition(field=field, op=Operator.NOT_IN, value=values)


def isnull(field: str) -> Condition:
    """
    Is null: field IS NULL
    
    Examples:
        isnull("deleted_at")       → deleted_at IS NULL
        isnull("parent_id")        → parent_id IS NULL
    """
    return Condition(field=field, op=Operator.IS_NULL, value=None)


def notnull(field: str) -> Condition:
    """
    Is not null: field IS NOT NULL
    
    Examples:
        notnull("email")           → email IS NOT NULL
        notnull("verified_at")     → verified_at IS NOT NULL
    """
    return Condition(field=field, op=Operator.IS_NOT_NULL, value=None)


# Aliases for compatibility
is_null_ = isnull
is_not_null_ = notnull
not_in_ = not_in


def between(field: str, low: Any, high: Any) -> Condition:
    """
    Between range: field BETWEEN low AND high
    
    Examples:
        between("age", 18, 65)     → age BETWEEN 18 AND 65
        between("price", 10, 100)  → price BETWEEN 10 AND 100
        between("date", start, end) → date BETWEEN '2024-01-01' AND '2024-12-31'
    """
    return Condition(field=field, op=Operator.BETWEEN, value=low, value2=high)


def json_contains(field: str, value: Any) -> Condition:
    """
    JSON/Array contains (PostgreSQL): field @> value
    
    Examples:
        json_contains("tags", ["python"])  → tags @> '["python"]'
        json_contains("data", {"key": "v"}) → data @> '{"key": "v"}'
    """
    return Condition(field=field, op=Operator.CONTAINS, value=value)


def json_contained_by(field: str, value: Any) -> Condition:
    """
    JSON/Array contained by (PostgreSQL): field <@ value
    
    Examples:
        json_contained_by("tags", ["a", "b", "c"])  → tags <@ '["a", "b", "c"]'
    """
    return Condition(field=field, op=Operator.CONTAINED_BY, value=value)


def array_overlaps(field: str, values: List[Any]) -> Condition:
    """
    Array overlaps (PostgreSQL): field && values
    
    True if arrays have any elements in common.
    
    Examples:
        array_overlaps("tags", ["python", "go"])  → tags && ARRAY['python', 'go']
    """
    return Condition(field=field, op=Operator.OVERLAPS, value=values)


# =============================================================================
# Logical Combination Functions
# =============================================================================

def and_(*conditions: ConditionType) -> LogicalCondition:
    """
    Combine conditions with AND.
    
    All conditions must be true for the row to match.
    
    Examples:
        and_(gt("age", 18), eq("status", "active"))
        → (age > 18) AND (status = 'active')
        
        and_(
            gt("age", 18),
            or_(eq("role", "admin"), eq("role", "mod"))
        )
        → (age > 18) AND ((role = 'admin') OR (role = 'mod'))
    """
    return LogicalCondition(op=LogicalOp.AND, conditions=list(conditions))


def or_(*conditions: ConditionType) -> LogicalCondition:
    """
    Combine conditions with OR.
    
    Any condition can be true for the row to match.
    
    Examples:
        or_(eq("role", "admin"), eq("role", "moderator"))
        → (role = 'admin') OR (role = 'moderator')
    """
    return LogicalCondition(op=LogicalOp.OR, conditions=list(conditions))


def not_(condition: ConditionType) -> LogicalCondition:
    """
    Negate a condition.
    
    Examples:
        not_(eq("status", "deleted"))
        → NOT (status = 'deleted')
        
        not_(in_("role", ["guest", "banned"]))
        → NOT (role IN ('guest', 'banned'))
    """
    return LogicalCondition(op=LogicalOp.NOT, conditions=[condition])


# =============================================================================
# Raw SQL Condition
# =============================================================================

def raw(sql: str, *params: Any) -> RawCondition:
    """
    Raw SQL condition for escape hatches.
    
    Use when the query builder doesn't support your use case.
    Parameters are bound safely (no SQL injection).
    
    Examples:
        raw("custom_func(data) > $1", 10)
        raw("jsonb_col @> $1", '{"key": "value"}')
        raw("ST_Distance(location, $1) < $2", point, 1000)
    """
    return RawCondition(sql=sql, params=list(params))


# =============================================================================
# Tuple Parsing
# =============================================================================

# Mapping of string operators to Operator enum
_OPERATOR_MAP = {
    "=": Operator.EQ,
    "==": Operator.EQ,
    "!=": Operator.NE,
    "<>": Operator.NE,
    ">": Operator.GT,
    ">=": Operator.GTE,
    "<": Operator.LT,
    "<=": Operator.LTE,
    "like": Operator.LIKE,
    "LIKE": Operator.LIKE,
    "ilike": Operator.ILIKE,
    "ILIKE": Operator.ILIKE,
    "in": Operator.IN,
    "IN": Operator.IN,
    "not in": Operator.NOT_IN,
    "NOT IN": Operator.NOT_IN,
    "is null": Operator.IS_NULL,
    "IS NULL": Operator.IS_NULL,
    "is not null": Operator.IS_NOT_NULL,
    "IS NOT NULL": Operator.IS_NOT_NULL,
    "between": Operator.BETWEEN,
    "BETWEEN": Operator.BETWEEN,
    "@>": Operator.CONTAINS,
    "<@": Operator.CONTAINED_BY,
    "&&": Operator.OVERLAPS,
}


def parse_tuple_condition(tup: tuple) -> Condition:
    """
    Parse a tuple condition into a Condition object.
    
    Tuple format: (field, operator, value) or (field, operator, value1, value2) for BETWEEN
    
    Examples:
        ("age", ">", 18)           → Condition(age > 18)
        ("status", "=", "active")  → Condition(status = 'active')
        ("name", "like", "%john%") → Condition(name LIKE '%john%')
        ("age", "between", 18, 65) → Condition(age BETWEEN 18 AND 65)
        ("deleted_at", "is null")  → Condition(deleted_at IS NULL)
    
    Raises:
        ValueError: If tuple format is invalid or operator unknown
    """
    if len(tup) == 2:
        # (field, "is null") or (field, "is not null")
        field, op_str = tup
        op = _OPERATOR_MAP.get(op_str.lower() if isinstance(op_str, str) else op_str)
        if op not in (Operator.IS_NULL, Operator.IS_NOT_NULL):
            raise ValueError(
                f"Two-element tuple requires 'is null' or 'is not null' operator, got: {op_str}"
            )
        return Condition(field=field, op=op, value=None)
    
    elif len(tup) == 3:
        # (field, operator, value)
        field, op_str, value = tup
        op = _OPERATOR_MAP.get(op_str)
        if op is None:
            raise ValueError(f"Unknown operator: {op_str!r}. Valid operators: {list(_OPERATOR_MAP.keys())}")
        return Condition(field=field, op=op, value=value)
    
    elif len(tup) == 4:
        # (field, "between", low, high)
        field, op_str, value1, value2 = tup
        if op_str.lower() != "between":
            raise ValueError(f"Four-element tuple requires 'between' operator, got: {op_str}")
        return Condition(field=field, op=Operator.BETWEEN, value=value1, value2=value2)
    
    else:
        raise ValueError(
            f"Invalid tuple condition: {tup}. "
            f"Expected (field, op, value) or (field, 'between', low, high)"
        )


def parse_condition(arg: Any) -> ConditionType:
    """
    Parse any condition argument into a ConditionType.
    
    Handles:
    - Tuple: ("age", ">", 18)
    - Condition: eq("status", "active")
    - LogicalCondition: and_(c1, c2)
    - RawCondition: raw("sql", params)
    
    Raises:
        TypeError: If argument type is not recognized
    """
    if isinstance(arg, (Condition, LogicalCondition, RawCondition)):
        return arg
    elif isinstance(arg, tuple):
        return parse_tuple_condition(arg)
    else:
        raise TypeError(
            f"Invalid condition type: {type(arg).__name__}. "
            f"Expected tuple, Condition, LogicalCondition, or RawCondition"
        )


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Operator enums
    "Operator",
    "LogicalOp",
    
    # Condition classes
    "Condition",
    "LogicalCondition", 
    "RawCondition",
    "ConditionType",
    
    # Comparison functions
    "eq",
    "ne",
    "gt",
    "gte",
    "lt",
    "lte",
    "like",
    "ilike",
    "contains",
    "startswith",
    "endswith",
    "in_",
    "not_in",
    "not_in_",  # Alias
    "isnull",
    "is_null_",  # Alias
    "notnull",
    "is_not_null_",  # Alias
    "between",
    
    # PostgreSQL specific
    "json_contains",
    "json_contained_by",
    "array_overlaps",
    
    # Logical operators
    "and_",
    "or_",
    "not_",
    
    # Raw SQL
    "raw",
    
    # Parsing
    "parse_tuple_condition",
    "parse_condition",
]

