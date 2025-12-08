"""
PyNext Query AST (Abstract Syntax Tree).

Defines the tree structure that represents a query before it's compiled to SQL.
The AST is serialized to JSON and sent to Go for optimization and SQL generation.

Design Principles:
- Complete: Can represent any query we support
- Serializable: Easy JSON conversion for Go bridge
- Debuggable: Clear repr() for every node
- Immutable: All operations return new AST nodes

AST Structure:
    QueryAST
    ├── table: str
    ├── type: SELECT | INSERT | UPDATE | DELETE
    ├── columns: List[str]
    ├── conditions: ConditionNode (tree of conditions)
    ├── order: List[OrderNode]
    ├── limit: int
    ├── offset: int
    ├── includes: List[str] (relationships to eager load)
    └── params: List[Any] (parameter values)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pynext.db.conditions import (
    Condition,
    LogicalCondition,
    RawCondition,
    ConditionType,
    LogicalOp,
)


# =============================================================================
# Query Type Enum
# =============================================================================

class QueryType(str, Enum):
    """Type of SQL query."""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    RAW = "RAW"  # Raw SQL execution


# =============================================================================
# Order Node
# =============================================================================

@dataclass
class OrderNode:
    """
    Represents an ORDER BY clause element.
    
    Attributes:
        field: Column name to order by
        direction: ASC or DESC
    """
    field: str
    direction: str = "ASC"  # ASC or DESC
    
    def __repr__(self) -> str:
        return f"Order({self.field} {self.direction})"
    
    def to_dict(self) -> dict:
        return {
            "field": self.field,
            "direction": self.direction,
        }
    
    @classmethod
    def parse(cls, order_str: str) -> "OrderNode":
        """
        Parse an order string like "-created_at" or "name".
        
        Prefix with - for descending order.
        
        Examples:
            "name"         → OrderNode("name", "ASC")
            "-created_at"  → OrderNode("created_at", "DESC")
            "+score"       → OrderNode("score", "ASC")
        """
        if order_str.startswith("-"):
            return cls(field=order_str[1:], direction="DESC")
        elif order_str.startswith("+"):
            return cls(field=order_str[1:], direction="ASC")
        return cls(field=order_str, direction="ASC")


# =============================================================================
# Join Node
# =============================================================================

@dataclass
class JoinNode:
    """
    Represents a JOIN clause.
    
    Attributes:
        table: Table to join
        alias: Optional alias for the joined table
        join_type: INNER, LEFT, RIGHT, FULL
        on_field: Field in main table
        to_field: Field in joined table
    """
    table: str
    alias: Optional[str] = None
    join_type: str = "INNER"  # INNER, LEFT, RIGHT, FULL
    on_field: str = ""
    to_field: str = ""
    
    def __repr__(self) -> str:
        alias_str = f" AS {self.alias}" if self.alias else ""
        return f"Join({self.join_type} {self.table}{alias_str} ON {self.on_field} = {self.to_field})"
    
    def to_dict(self) -> dict:
        return {
            "table": self.table,
            "alias": self.alias,
            "join_type": self.join_type,
            "on_field": self.on_field,
            "to_field": self.to_field,
        }


# =============================================================================
# Condition Node (Tree Structure)
# =============================================================================

@dataclass
class ConditionNode:
    """
    Tree node for conditions.
    
    This wraps Condition, LogicalCondition, or RawCondition into a
    uniform tree structure for the AST.
    """
    condition: ConditionType
    
    def to_dict(self) -> dict:
        return self.condition.to_dict()
    
    def __repr__(self) -> str:
        return repr(self.condition)


# =============================================================================
# Query AST
# =============================================================================

@dataclass
class QueryAST:
    """
    Complete Abstract Syntax Tree for a query.
    
    This is the final representation that gets serialized to JSON
    and sent to the Go layer for optimization and SQL generation.
    
    Attributes:
        table: Main table name
        query_type: SELECT, INSERT, UPDATE, DELETE, or RAW
        columns: Columns to select (None = all, empty = *)
        conditions: Root condition node (can be tree of AND/OR)
        order: List of order clauses
        limit: Maximum rows to return
        offset: Rows to skip
        includes: Relationships to eager load
        joins: Explicit join clauses
        group_by: Group by columns
        having: Having conditions
        distinct: Whether to use DISTINCT
        for_update: Whether to use FOR UPDATE (row locking)
        params: All parameter values in order
        raw_sql: For RAW query type, the raw SQL string
        
    Immutability:
        All methods return new QueryAST instances, never modify self.
    """
    table: str
    query_type: QueryType = QueryType.SELECT
    columns: Optional[List[str]] = None
    conditions: Optional[ConditionNode] = None
    order: List[OrderNode] = field(default_factory=list)
    limit: Optional[int] = None
    offset: Optional[int] = None
    includes: List[str] = field(default_factory=list)
    joins: List[JoinNode] = field(default_factory=list)
    group_by: List[str] = field(default_factory=list)
    having: Optional[ConditionNode] = None
    distinct: bool = False
    for_update: bool = False
    params: List[Any] = field(default_factory=list)
    raw_sql: Optional[str] = None
    
    # Schema information (for validation)
    _schema_fields: Optional[Dict[str, Any]] = field(default=None, repr=False)
    
    def __repr__(self) -> str:
        parts = [f"QueryAST({self.query_type.value} FROM {self.table}"]
        if self.columns:
            parts.append(f"columns={self.columns}")
        if self.conditions:
            parts.append(f"where={self.conditions}")
        if self.order:
            parts.append(f"order={self.order}")
        if self.limit is not None:
            parts.append(f"limit={self.limit}")
        if self.offset is not None:
            parts.append(f"offset={self.offset}")
        if self.includes:
            parts.append(f"includes={self.includes}")
        return " ".join(parts) + ")"
    
    def to_dict(self) -> dict:
        """
        Convert AST to dictionary for JSON serialization.
        
        This is sent to the Go bridge for SQL generation.
        """
        result = {
            "table": self.table,
            "type": self.query_type.value,
        }
        
        if self.columns is not None:
            result["columns"] = self.columns
        
        if self.conditions is not None:
            result["conditions"] = self.conditions.to_dict()
        
        if self.order:
            result["order"] = [o.to_dict() for o in self.order]
        
        if self.limit is not None:
            result["limit"] = self.limit
        
        if self.offset is not None:
            result["offset"] = self.offset
        
        if self.includes:
            result["includes"] = self.includes
        
        if self.joins:
            result["joins"] = [j.to_dict() for j in self.joins]
        
        if self.group_by:
            result["group_by"] = self.group_by
        
        if self.having is not None:
            result["having"] = self.having.to_dict()
        
        if self.distinct:
            result["distinct"] = True
        
        if self.for_update:
            result["for_update"] = True
        
        if self.params:
            result["params"] = self.params
        
        if self.raw_sql:
            result["raw_sql"] = self.raw_sql
        
        return result
    
    # =========================================================================
    # Immutable Builder Methods
    # =========================================================================
    
    def with_columns(self, *columns: str) -> "QueryAST":
        """Return new AST with specified columns."""
        return QueryAST(
            table=self.table,
            query_type=self.query_type,
            columns=list(columns) if columns else None,
            conditions=self.conditions,
            order=self.order.copy(),
            limit=self.limit,
            offset=self.offset,
            includes=self.includes.copy(),
            joins=self.joins.copy(),
            group_by=self.group_by.copy(),
            having=self.having,
            distinct=self.distinct,
            for_update=self.for_update,
            params=self.params.copy(),
            raw_sql=self.raw_sql,
            _schema_fields=self._schema_fields,
        )
    
    def with_conditions(self, conditions: ConditionNode) -> "QueryAST":
        """Return new AST with specified conditions."""
        return QueryAST(
            table=self.table,
            query_type=self.query_type,
            columns=self.columns.copy() if self.columns else None,
            conditions=conditions,
            order=self.order.copy(),
            limit=self.limit,
            offset=self.offset,
            includes=self.includes.copy(),
            joins=self.joins.copy(),
            group_by=self.group_by.copy(),
            having=self.having,
            distinct=self.distinct,
            for_update=self.for_update,
            params=self.params.copy(),
            raw_sql=self.raw_sql,
            _schema_fields=self._schema_fields,
        )
    
    def with_order(self, *orders: OrderNode) -> "QueryAST":
        """Return new AST with specified order."""
        return QueryAST(
            table=self.table,
            query_type=self.query_type,
            columns=self.columns.copy() if self.columns else None,
            conditions=self.conditions,
            order=list(orders),
            limit=self.limit,
            offset=self.offset,
            includes=self.includes.copy(),
            joins=self.joins.copy(),
            group_by=self.group_by.copy(),
            having=self.having,
            distinct=self.distinct,
            for_update=self.for_update,
            params=self.params.copy(),
            raw_sql=self.raw_sql,
            _schema_fields=self._schema_fields,
        )
    
    def with_limit(self, limit: int) -> "QueryAST":
        """Return new AST with specified limit."""
        return QueryAST(
            table=self.table,
            query_type=self.query_type,
            columns=self.columns.copy() if self.columns else None,
            conditions=self.conditions,
            order=self.order.copy(),
            limit=limit,
            offset=self.offset,
            includes=self.includes.copy(),
            joins=self.joins.copy(),
            group_by=self.group_by.copy(),
            having=self.having,
            distinct=self.distinct,
            for_update=self.for_update,
            params=self.params.copy(),
            raw_sql=self.raw_sql,
            _schema_fields=self._schema_fields,
        )
    
    def with_offset(self, offset: int) -> "QueryAST":
        """Return new AST with specified offset."""
        return QueryAST(
            table=self.table,
            query_type=self.query_type,
            columns=self.columns.copy() if self.columns else None,
            conditions=self.conditions,
            order=self.order.copy(),
            limit=self.limit,
            offset=offset,
            includes=self.includes.copy(),
            joins=self.joins.copy(),
            group_by=self.group_by.copy(),
            having=self.having,
            distinct=self.distinct,
            for_update=self.for_update,
            params=self.params.copy(),
            raw_sql=self.raw_sql,
            _schema_fields=self._schema_fields,
        )
    
    def with_includes(self, *includes: str) -> "QueryAST":
        """Return new AST with relationships to eager load."""
        return QueryAST(
            table=self.table,
            query_type=self.query_type,
            columns=self.columns.copy() if self.columns else None,
            conditions=self.conditions,
            order=self.order.copy(),
            limit=self.limit,
            offset=self.offset,
            includes=list(includes),
            joins=self.joins.copy(),
            group_by=self.group_by.copy(),
            having=self.having,
            distinct=self.distinct,
            for_update=self.for_update,
            params=self.params.copy(),
            raw_sql=self.raw_sql,
            _schema_fields=self._schema_fields,
        )
    
    def with_params(self, params: List[Any]) -> "QueryAST":
        """Return new AST with specified parameters."""
        return QueryAST(
            table=self.table,
            query_type=self.query_type,
            columns=self.columns.copy() if self.columns else None,
            conditions=self.conditions,
            order=self.order.copy(),
            limit=self.limit,
            offset=self.offset,
            includes=self.includes.copy(),
            joins=self.joins.copy(),
            group_by=self.group_by.copy(),
            having=self.having,
            distinct=self.distinct,
            for_update=self.for_update,
            params=params,
            raw_sql=self.raw_sql,
            _schema_fields=self._schema_fields,
        )
    
    # =========================================================================
    # Query Inspection Methods
    # =========================================================================
    
    def HasConditions(self) -> bool:
        """Check if query has any conditions."""
        return self.conditions is not None
    
    def HasOrder(self) -> bool:
        """Check if query has any ordering."""
        return len(self.order) > 0
    
    def ColumnList(self) -> str:
        """Get column list as string (for SQL generation)."""
        if not self.columns:
            return "*"
        return ", ".join(self.columns)
    
    def IsRawQuery(self) -> bool:
        """Check if this is a raw SQL query."""
        return self.query_type == QueryType.RAW or self.raw_sql is not None


# =============================================================================
# AST Builder Helpers
# =============================================================================

def build_condition_node(conditions: List[ConditionType]) -> Optional[ConditionNode]:
    """
    Build a ConditionNode from a list of conditions.
    
    If multiple conditions, wraps them in AND.
    If single condition, returns it directly.
    If empty, returns None.
    """
    if not conditions:
        return None
    
    if len(conditions) == 1:
        return ConditionNode(conditions[0])
    
    # Multiple conditions → AND them together
    return ConditionNode(
        LogicalCondition(op=LogicalOp.AND, conditions=list(conditions))
    )


def merge_conditions(
    existing: Optional[ConditionNode],
    new_conditions: List[ConditionType]
) -> Optional[ConditionNode]:
    """
    Merge new conditions with existing ones using AND.
    
    Used when chaining .where() calls.
    """
    if not new_conditions:
        return existing
    
    new_node = build_condition_node(new_conditions)
    
    if existing is None:
        return new_node
    
    # AND the existing and new together
    return ConditionNode(
        LogicalCondition(
            op=LogicalOp.AND,
            conditions=[existing.condition, new_node.condition]
        )
    )


# =============================================================================
# Parameter Extraction
# =============================================================================

def extract_params(condition: ConditionType) -> List[Any]:
    """
    Extract all parameter values from a condition tree.
    
    Returns values in order they appear (left to right, depth first).
    """
    params = []
    _extract_params_recursive(condition, params)
    return params


def _extract_params_recursive(condition: ConditionType, params: List[Any]) -> None:
    """Recursive helper for parameter extraction."""
    if isinstance(condition, Condition):
        if condition.value is not None:
            if isinstance(condition.value, list):
                params.extend(condition.value)
            else:
                params.append(condition.value)
        if condition.value2 is not None:
            params.append(condition.value2)
    
    elif isinstance(condition, LogicalCondition):
        for child in condition.conditions:
            _extract_params_recursive(child, params)
    
    elif isinstance(condition, RawCondition):
        params.extend(condition.params)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "QueryType",
    "OrderNode",
    "JoinNode",
    "ConditionNode",
    "QueryAST",
    "build_condition_node",
    "merge_conditions",
    "extract_params",
]

