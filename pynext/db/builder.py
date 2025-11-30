"""
PyNext Type-Safe SQL Builder.

Build SQL queries with Python, not strings.
Full type safety, SQL injection prevention, and easy composition.

Design: Type-safe power when raw SQL feels risky.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Type, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from pynext.db.table import Table


class JoinType(str, Enum):
    """SQL JOIN types."""
    INNER = "INNER JOIN"
    LEFT = "LEFT JOIN"
    RIGHT = "RIGHT JOIN"
    FULL = "FULL OUTER JOIN"
    CROSS = "CROSS JOIN"


class OrderDirection(str, Enum):
    """SQL ORDER BY directions."""
    ASC = "ASC"
    DESC = "DESC"


class SQLBuilder:
    """
    Type-safe SQL query builder.
    
    Build complex SQL queries with Python methods instead of strings.
    Prevents SQL injection, provides IDE autocomplete, catches errors early.
    
    Usage:
        from pynext.db import sql
        
        # SELECT
        users = await (
            sql.select("*")
            .from_("users")
            .where("role", "=", "admin")
            .order_by("created_at", "DESC")
            .limit(10)
            .execute()
        )
        
        # INSERT
        await (
            sql.insert("users")
            .values(name="John", email="john@example.com")
            .returning("*")
            .execute()
        )
        
        # UPDATE
        await (
            sql.update("users")
            .set(active=True)
            .where("last_login", ">", datetime(2024, 1, 1))
            .execute()
        )
        
        # DELETE
        await (
            sql.delete("users")
            .where("active", "=", False)
            .execute()
        )
    """
    
    def select(self, *columns: str) -> "SelectBuilder":
        """
        Start a SELECT query.
        
        Examples:
            sql.select("*")
            sql.select("id", "name", "email")
            sql.select("users.id", "posts.title")
        """
        return SelectBuilder(list(columns) if columns else ["*"])
    
    def insert(self, table: str) -> "InsertBuilder":
        """
        Start an INSERT query.
        
        Examples:
            sql.insert("users").values(name="John")
        """
        return InsertBuilder(table)
    
    def update(self, table: str) -> "UpdateBuilder":
        """
        Start an UPDATE query.
        
        Examples:
            sql.update("users").set(active=True)
        """
        return UpdateBuilder(table)
    
    def delete(self, table: str) -> "DeleteBuilder":
        """
        Start a DELETE query.
        
        Examples:
            sql.delete("users").where("active", "=", False)
        """
        return DeleteBuilder(table)


class SelectBuilder:
    """Builder for SELECT queries."""
    
    def __init__(self, columns: List[str]):
        self._columns = columns
        self._table: Optional[str] = None
        self._joins: List[Tuple[str, str, str, str, str]] = []  # type, table, col1, op, col2
        self._where_clauses: List[Tuple[str, str, Any]] = []  # column, op, value
        self._where_or: List[List[Tuple[str, str, Any]]] = []
        self._order: List[Tuple[str, str]] = []  # column, direction
        self._group: List[str] = []
        self._having: List[Tuple[str, str, Any]] = []
        self._limit_val: Optional[int] = None
        self._offset_val: Optional[int] = None
        self._distinct: bool = False
    
    def from_(self, table: str) -> "SelectBuilder":
        """
        Set the FROM table.
        
        Examples:
            sql.select("*").from_("users")
        """
        self._table = table
        return self
    
    def distinct(self) -> "SelectBuilder":
        """
        Add DISTINCT.
        
        Examples:
            sql.select("role").from_("users").distinct()
        """
        self._distinct = True
        return self
    
    def join(
        self,
        table: str,
        column1: str,
        operator: str,
        column2: str,
        join_type: Union[JoinType, str] = JoinType.INNER,
    ) -> "SelectBuilder":
        """
        Add a JOIN clause.
        
        Examples:
            sql.select("posts.*", "users.name")
               .from_("posts")
               .join("users", "posts.author_id", "=", "users.id")
        """
        if isinstance(join_type, JoinType):
            join_type = join_type.value
        self._joins.append((join_type, table, column1, operator, column2))
        return self
    
    def left_join(
        self,
        table: str,
        column1: str,
        operator: str,
        column2: str,
    ) -> "SelectBuilder":
        """Left join shortcut."""
        return self.join(table, column1, operator, column2, JoinType.LEFT)
    
    def right_join(
        self,
        table: str,
        column1: str,
        operator: str,
        column2: str,
    ) -> "SelectBuilder":
        """Right join shortcut."""
        return self.join(table, column1, operator, column2, JoinType.RIGHT)
    
    def where(
        self,
        column: str,
        operator: str,
        value: Any,
    ) -> "SelectBuilder":
        """
        Add a WHERE condition (AND).
        
        Examples:
            .where("role", "=", "admin")
            .where("age", ">", 18)
            .where("name", "LIKE", "%john%")
        """
        self._where_clauses.append((column, operator, value))
        return self
    
    def where_in(self, column: str, values: List[Any]) -> "SelectBuilder":
        """
        Add a WHERE IN condition.
        
        Examples:
            .where_in("id", [1, 2, 3])
        """
        self._where_clauses.append((column, "IN", values))
        return self
    
    def where_not_in(self, column: str, values: List[Any]) -> "SelectBuilder":
        """
        Add a WHERE NOT IN condition.
        
        Examples:
            .where_not_in("role", ["banned", "suspended"])
        """
        self._where_clauses.append((column, "NOT IN", values))
        return self
    
    def where_null(self, column: str) -> "SelectBuilder":
        """
        Add a WHERE IS NULL condition.
        
        Examples:
            .where_null("deleted_at")
        """
        self._where_clauses.append((column, "IS", None))
        return self
    
    def where_not_null(self, column: str) -> "SelectBuilder":
        """
        Add a WHERE IS NOT NULL condition.
        
        Examples:
            .where_not_null("email")
        """
        self._where_clauses.append((column, "IS NOT", None))
        return self
    
    def where_between(
        self,
        column: str,
        low: Any,
        high: Any,
    ) -> "SelectBuilder":
        """
        Add a WHERE BETWEEN condition.
        
        Examples:
            .where_between("age", 18, 65)
        """
        self._where_clauses.append((column, "BETWEEN", (low, high)))
        return self
    
    def or_where(
        self,
        column: str,
        operator: str,
        value: Any,
    ) -> "SelectBuilder":
        """
        Add an OR WHERE condition.
        
        Examples:
            .where("role", "=", "admin")
            .or_where("role", "=", "superuser")
        """
        if not self._where_or:
            # Move last AND condition to OR group
            if self._where_clauses:
                last = self._where_clauses.pop()
                self._where_or.append([last])
        
        self._where_or[-1].append((column, operator, value))
        return self
    
    def order_by(
        self,
        column: str,
        direction: Union[OrderDirection, str] = OrderDirection.ASC,
    ) -> "SelectBuilder":
        """
        Add an ORDER BY clause.
        
        Examples:
            .order_by("created_at", "DESC")
            .order_by("name")
        """
        if isinstance(direction, OrderDirection):
            direction = direction.value
        self._order.append((column, direction))
        return self
    
    def group_by(self, *columns: str) -> "SelectBuilder":
        """
        Add a GROUP BY clause.
        
        Examples:
            sql.select("role", "COUNT(*)")
               .from_("users")
               .group_by("role")
        """
        self._group.extend(columns)
        return self
    
    def having(
        self,
        column: str,
        operator: str,
        value: Any,
    ) -> "SelectBuilder":
        """
        Add a HAVING clause.
        
        Examples:
            .group_by("role")
            .having("COUNT(*)", ">", 10)
        """
        self._having.append((column, operator, value))
        return self
    
    def limit(self, n: int) -> "SelectBuilder":
        """
        Add a LIMIT clause.
        
        Examples:
            .limit(10)
        """
        self._limit_val = n
        return self
    
    def offset(self, n: int) -> "SelectBuilder":
        """
        Add an OFFSET clause.
        
        Examples:
            .offset(20)
        """
        self._offset_val = n
        return self
    
    def page(self, page: int, per_page: int = 20) -> "SelectBuilder":
        """
        Paginate results.
        
        Examples:
            .page(2, 20)  # Results 21-40
        """
        self._limit_val = per_page
        self._offset_val = (page - 1) * per_page
        return self
    
    def build(self) -> Tuple[str, Tuple[Any, ...]]:
        """
        Build the SQL query and parameters.
        
        Returns:
            Tuple of (sql_string, parameters)
        """
        if not self._table:
            raise ValueError("No table specified. Use .from_('table')")
        
        params: List[Any] = []
        param_index = 0
        
        def add_param(value: Any) -> str:
            nonlocal param_index
            param_index += 1
            params.append(value)
            return f"${param_index}"
        
        # SELECT
        distinct = "DISTINCT " if self._distinct else ""
        sql = f"SELECT {distinct}{', '.join(self._columns)} FROM {self._table}"
        
        # JOINs
        for join_type, table, col1, op, col2 in self._joins:
            sql += f" {join_type} {table} ON {col1} {op} {col2}"
        
        # WHERE
        where_parts = []
        for column, operator, value in self._where_clauses:
            if operator == "IN":
                placeholders = ", ".join(add_param(v) for v in value)
                where_parts.append(f"{column} IN ({placeholders})")
            elif operator == "NOT IN":
                placeholders = ", ".join(add_param(v) for v in value)
                where_parts.append(f"{column} NOT IN ({placeholders})")
            elif operator == "IS" and value is None:
                where_parts.append(f"{column} IS NULL")
            elif operator == "IS NOT" and value is None:
                where_parts.append(f"{column} IS NOT NULL")
            elif operator == "BETWEEN":
                low, high = value
                where_parts.append(f"{column} BETWEEN {add_param(low)} AND {add_param(high)}")
            else:
                where_parts.append(f"{column} {operator} {add_param(value)}")
        
        # OR WHERE groups
        for or_group in self._where_or:
            or_parts = []
            for column, operator, value in or_group:
                or_parts.append(f"{column} {operator} {add_param(value)}")
            if or_parts:
                where_parts.append(f"({' OR '.join(or_parts)})")
        
        if where_parts:
            sql += f" WHERE {' AND '.join(where_parts)}"
        
        # GROUP BY
        if self._group:
            sql += f" GROUP BY {', '.join(self._group)}"
        
        # HAVING
        if self._having:
            having_parts = []
            for column, operator, value in self._having:
                having_parts.append(f"{column} {operator} {add_param(value)}")
            sql += f" HAVING {' AND '.join(having_parts)}"
        
        # ORDER BY
        if self._order:
            order_parts = [f"{col} {dir}" for col, dir in self._order]
            sql += f" ORDER BY {', '.join(order_parts)}"
        
        # LIMIT / OFFSET
        if self._limit_val is not None:
            sql += f" LIMIT {self._limit_val}"
        if self._offset_val is not None:
            sql += f" OFFSET {self._offset_val}"
        
        return sql, tuple(params)
    
    async def execute(self) -> List[Dict[str, Any]]:
        """
        Execute the query and return results.
        
        Returns:
            List of row dicts
        """
        from pynext.db.table import get_adapter
        
        sql, params = self.build()
        adapter = get_adapter()
        return await adapter.fetch_all(sql, params)
    
    async def execute_one(self) -> Optional[Dict[str, Any]]:
        """
        Execute the query and return first result.
        
        Returns:
            Row dict or None
        """
        from pynext.db.table import get_adapter
        
        # Add LIMIT 1 if not already limited
        if self._limit_val is None:
            self._limit_val = 1
        
        sql, params = self.build()
        adapter = get_adapter()
        return await adapter.fetch_one(sql, params)


class InsertBuilder:
    """Builder for INSERT queries."""
    
    def __init__(self, table: str):
        self._table = table
        self._values_data: Dict[str, Any] = {}
        self._returning: List[str] = []
        self._on_conflict: Optional[Tuple[List[str], Optional[Dict[str, Any]]]] = None
    
    def values(self, **data: Any) -> "InsertBuilder":
        """
        Set values to insert.
        
        Examples:
            sql.insert("users").values(name="John", email="john@example.com")
        """
        self._values_data.update(data)
        return self
    
    def returning(self, *columns: str) -> "InsertBuilder":
        """
        Add RETURNING clause.
        
        Examples:
            sql.insert("users").values(...).returning("*")
            sql.insert("users").values(...).returning("id")
        """
        self._returning = list(columns) if columns else ["*"]
        return self
    
    def on_conflict_do_nothing(self, *columns: str) -> "InsertBuilder":
        """
        Handle conflicts by doing nothing.
        
        Examples:
            sql.insert("users")
               .values(email="john@example.com")
               .on_conflict_do_nothing("email")
        """
        self._on_conflict = (list(columns), None)
        return self
    
    def on_conflict_do_update(
        self,
        conflict_columns: List[str],
        update_values: Dict[str, Any],
    ) -> "InsertBuilder":
        """
        Handle conflicts by updating.
        
        Examples:
            sql.insert("users")
               .values(email="john@example.com", name="John")
               .on_conflict_do_update(["email"], {"name": "John Updated"})
        """
        self._on_conflict = (conflict_columns, update_values)
        return self
    
    def build(self) -> Tuple[str, Tuple[Any, ...]]:
        """Build the SQL query and parameters."""
        if not self._values_data:
            raise ValueError("No values specified. Use .values(...)")
        
        params: List[Any] = []
        param_index = 0
        
        def add_param(value: Any) -> str:
            nonlocal param_index
            param_index += 1
            params.append(value)
            return f"${param_index}"
        
        columns = list(self._values_data.keys())
        placeholders = [add_param(v) for v in self._values_data.values()]
        
        sql = f"INSERT INTO {self._table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        
        # ON CONFLICT
        if self._on_conflict:
            conflict_cols, update_vals = self._on_conflict
            sql += f" ON CONFLICT ({', '.join(conflict_cols)})"
            
            if update_vals is None:
                sql += " DO NOTHING"
            else:
                set_parts = [f"{k} = {add_param(v)}" for k, v in update_vals.items()]
                sql += f" DO UPDATE SET {', '.join(set_parts)}"
        
        # RETURNING
        if self._returning:
            sql += f" RETURNING {', '.join(self._returning)}"
        
        return sql, tuple(params)
    
    async def execute(self) -> Optional[Dict[str, Any]]:
        """
        Execute the INSERT.
        
        Returns:
            Inserted row (if RETURNING) or None
        """
        from pynext.db.table import get_adapter
        
        sql, params = self.build()
        adapter = get_adapter()
        
        if self._returning:
            return await adapter.fetch_one(sql, params)
        
        await adapter.execute(sql, params)
        return None


class UpdateBuilder:
    """Builder for UPDATE queries."""
    
    def __init__(self, table: str):
        self._table = table
        self._set_data: Dict[str, Any] = {}
        self._where_clauses: List[Tuple[str, str, Any]] = []
        self._returning: List[str] = []
    
    def set(self, **data: Any) -> "UpdateBuilder":
        """
        Set values to update.
        
        Examples:
            sql.update("users").set(active=True, role="admin")
        """
        self._set_data.update(data)
        return self
    
    def where(
        self,
        column: str,
        operator: str,
        value: Any,
    ) -> "UpdateBuilder":
        """
        Add WHERE condition.
        
        Examples:
            .where("id", "=", 1)
            .where("role", "!=", "admin")
        """
        self._where_clauses.append((column, operator, value))
        return self
    
    def where_in(self, column: str, values: List[Any]) -> "UpdateBuilder":
        """Add WHERE IN condition."""
        self._where_clauses.append((column, "IN", values))
        return self
    
    def returning(self, *columns: str) -> "UpdateBuilder":
        """Add RETURNING clause."""
        self._returning = list(columns) if columns else ["*"]
        return self
    
    def build(self) -> Tuple[str, Tuple[Any, ...]]:
        """Build the SQL query and parameters."""
        if not self._set_data:
            raise ValueError("No values specified. Use .set(...)")
        
        params: List[Any] = []
        param_index = 0
        
        def add_param(value: Any) -> str:
            nonlocal param_index
            param_index += 1
            params.append(value)
            return f"${param_index}"
        
        set_parts = [f"{k} = {add_param(v)}" for k, v in self._set_data.items()]
        sql = f"UPDATE {self._table} SET {', '.join(set_parts)}"
        
        # WHERE
        if self._where_clauses:
            where_parts = []
            for column, operator, value in self._where_clauses:
                if operator == "IN":
                    placeholders = ", ".join(add_param(v) for v in value)
                    where_parts.append(f"{column} IN ({placeholders})")
                else:
                    where_parts.append(f"{column} {operator} {add_param(value)}")
            sql += f" WHERE {' AND '.join(where_parts)}"
        
        # RETURNING
        if self._returning:
            sql += f" RETURNING {', '.join(self._returning)}"
        
        return sql, tuple(params)
    
    async def execute(self) -> Optional[Dict[str, Any]]:
        """
        Execute the UPDATE.
        
        Returns:
            Updated row (if RETURNING) or None
        """
        from pynext.db.table import get_adapter
        
        sql, params = self.build()
        adapter = get_adapter()
        
        if self._returning:
            return await adapter.fetch_one(sql, params)
        
        result = await adapter.execute(sql, params)
        return None


class DeleteBuilder:
    """Builder for DELETE queries."""
    
    def __init__(self, table: str):
        self._table = table
        self._where_clauses: List[Tuple[str, str, Any]] = []
        self._returning: List[str] = []
    
    def where(
        self,
        column: str,
        operator: str,
        value: Any,
    ) -> "DeleteBuilder":
        """
        Add WHERE condition.
        
        Examples:
            .where("active", "=", False)
            .where("created_at", "<", datetime(2020, 1, 1))
        """
        self._where_clauses.append((column, operator, value))
        return self
    
    def where_in(self, column: str, values: List[Any]) -> "DeleteBuilder":
        """Add WHERE IN condition."""
        self._where_clauses.append((column, "IN", values))
        return self
    
    def returning(self, *columns: str) -> "DeleteBuilder":
        """Add RETURNING clause."""
        self._returning = list(columns) if columns else ["*"]
        return self
    
    def build(self) -> Tuple[str, Tuple[Any, ...]]:
        """Build the SQL query and parameters."""
        params: List[Any] = []
        param_index = 0
        
        def add_param(value: Any) -> str:
            nonlocal param_index
            param_index += 1
            params.append(value)
            return f"${param_index}"
        
        sql = f"DELETE FROM {self._table}"
        
        # WHERE
        if self._where_clauses:
            where_parts = []
            for column, operator, value in self._where_clauses:
                if operator == "IN":
                    placeholders = ", ".join(add_param(v) for v in value)
                    where_parts.append(f"{column} IN ({placeholders})")
                else:
                    where_parts.append(f"{column} {operator} {add_param(value)}")
            sql += f" WHERE {' AND '.join(where_parts)}"
        
        # RETURNING
        if self._returning:
            sql += f" RETURNING {', '.join(self._returning)}"
        
        return sql, tuple(params)
    
    async def execute(self) -> int:
        """
        Execute the DELETE.
        
        Returns:
            Number of deleted rows
        """
        from pynext.db.table import get_adapter
        
        sql, params = self.build()
        adapter = get_adapter()
        
        result = await adapter.execute(sql, params)
        
        if hasattr(result, 'rowcount'):
            return result.rowcount
        return 0


# Global SQL builder instance
sql = SQLBuilder()


__all__ = [
    "SQLBuilder",
    "SelectBuilder",
    "InsertBuilder",
    "UpdateBuilder",
    "DeleteBuilder",
    "JoinType",
    "OrderDirection",
    "sql",
]

