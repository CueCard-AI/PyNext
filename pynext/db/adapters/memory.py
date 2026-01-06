"""
PyNext Memory Database Adapter.

SQLite-based in-memory adapter for accurate SQL testing.
Uses real SQL execution with connection pooling.

Perfect for:
- Integration tests
- Testing SQL compatibility
- Development without external DB
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING
import json

from pynext.db.adapters.base import Adapter
from pynext.db.exceptions import NotFoundError, QueryError
from pynext.db.fields import serialize_value, deserialize_value, SQLType

if TYPE_CHECKING:
    from pynext.db.query import Query
    from pynext.db.fields import FieldInfo


class MemoryAdapter(Adapter):
    """
    In-memory SQLite database adapter.
    
    Uses real SQL execution for accurate testing.
    Data is lost when the adapter is disconnected.
    
    Usage:
        adapter = MemoryAdapter()
        await adapter.connect()
        
        # Create table
        await adapter.create_table("users", fields)
        
        # Use it
        await adapter.insert("users", {"name": "John"}, fields)
    """
    
    def __init__(self, database: str = ":memory:"):
        """
        Initialize the adapter.
        
        Args:
            database: SQLite database path (default: in-memory)
        """
        self._database = database
        self._conn: Optional[sqlite3.Connection] = None
        self._in_transaction = False
    
    async def connect(self) -> None:
        """Connect to the SQLite database."""
        self._conn = sqlite3.connect(self._database, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        # Enable foreign keys
        self._conn.execute("PRAGMA foreign_keys = ON")
    
    async def disconnect(self) -> None:
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
    
    async def create_table(self, table: str, fields: Dict[str, "FieldInfo"]) -> None:
        """Create a table with the given fields."""
        columns = []
        for name, field in fields.items():
            col_def = self._field_to_column(field)
            columns.append(col_def)
        
        sql = f"CREATE TABLE IF NOT EXISTS {table} ({', '.join(columns)})"
        self._execute(sql)
        
        # Create indexes
        for name, field in fields.items():
            if field.index and not field.primary_key:
                idx_sql = f"CREATE INDEX IF NOT EXISTS idx_{table}_{name} ON {table} ({name})"
                self._execute(idx_sql)
    
    async def drop_table(self, table: str) -> None:
        """Drop a table."""
        self._execute(f"DROP TABLE IF EXISTS {table}")
    
    async def insert(
        self,
        table: str,
        data: Dict[str, Any],
        fields: Dict[str, "FieldInfo"],
    ) -> Dict[str, Any]:
        """Insert a row and return it with generated id."""
        # Add auto timestamps
        now = datetime.utcnow()
        data = {**data}
        if "created_at" not in data:
            data["created_at"] = now
        if "updated_at" not in data:
            data["updated_at"] = now
        
        # Serialize values
        serialized = {}
        for key, value in data.items():
            if key in fields:
                serialized[key] = serialize_value(value, fields[key])
            else:
                serialized[key] = value
        
        # Build SQL
        columns = list(serialized.keys())
        placeholders = ["?" for _ in columns]
        values = [serialized[col] for col in columns]
        
        sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        cursor = self._execute(sql, tuple(values))
        row_id = cursor.lastrowid
        
        # Fetch the inserted row
        return await self._get_by_id(table, row_id, fields)
    
    async def select(
        self,
        table: str,
        query: "Query",
        fields: Dict[str, "FieldInfo"],
    ) -> List[Dict[str, Any]]:
        """Select rows matching the query."""
        sql, params = self._build_select_sql(table, query)
        rows = self._fetch_all(sql, params)
        
        # Deserialize values
        return [self._deserialize_row(row, fields) for row in rows]
    
    async def select_one(
        self,
        table: str,
        query: "Query",
        fields: Dict[str, "FieldInfo"],
    ) -> Optional[Dict[str, Any]]:
        """Select a single row."""
        sql, params = self._build_select_sql(table, query)
        sql += " LIMIT 1"
        row = self._fetch_one(sql, params)
        
        if row is None:
            return None
        return self._deserialize_row(row, fields)
    
    async def update(
        self,
        table: str,
        id: int,
        data: Dict[str, Any],
        fields: Dict[str, "FieldInfo"],
    ) -> Dict[str, Any]:
        """Update a row by id."""
        # Add updated_at
        data = {**data, "updated_at": datetime.utcnow()}
        
        # Serialize values
        serialized = {}
        for key, value in data.items():
            if key in fields:
                serialized[key] = serialize_value(value, fields[key])
            else:
                serialized[key] = value
        
        # Build SQL
        set_clause = ", ".join(f"{col} = ?" for col in serialized.keys())
        values = list(serialized.values()) + [id]
        
        sql = f"UPDATE {table} SET {set_clause} WHERE id = ?"
        cursor = self._execute(sql, tuple(values))
        
        if cursor.rowcount == 0:
            raise NotFoundError(table, id=id)
        
        # Fetch the updated row
        return await self._get_by_id(table, id, fields)
    
    async def delete(self, table: str, id: int) -> bool:
        """Delete a row by id."""
        sql = f"DELETE FROM {table} WHERE id = ?"
        cursor = self._execute(sql, (id,))
        return cursor.rowcount > 0
    
    async def count(self, table: str, query: "Query") -> int:
        """Count matching rows."""
        where_clause, params = self._build_where_clause(query)
        sql = f"SELECT COUNT(*) FROM {table}"
        if where_clause:
            sql += f" WHERE {where_clause}"
        
        row = self._fetch_one(sql, params)
        return row[0] if row else 0
    
    async def exists(self, table: str, query: "Query") -> bool:
        """Check if any rows match."""
        where_clause, params = self._build_where_clause(query)
        sql = f"SELECT 1 FROM {table}"
        if where_clause:
            sql += f" WHERE {where_clause}"
        sql += " LIMIT 1"
        
        row = self._fetch_one(sql, params)
        return row is not None
    
    async def execute(
        self,
        sql: str,
        params: Optional[Tuple[Any, ...]] = None,
    ) -> Any:
        """Execute raw SQL."""
        # Convert $1, $2 style to ? style
        converted_sql = self._convert_placeholders(sql)
        cursor = self._execute(converted_sql, params or ())
        return cursor
    
    async def fetch_all(
        self,
        sql: str,
        params: Optional[Tuple[Any, ...]] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch all rows."""
        converted_sql = self._convert_placeholders(sql)
        rows = self._fetch_all(converted_sql, params or ())
        return [dict(row) for row in rows]
    
    async def fetch_one(
        self,
        sql: str,
        params: Optional[Tuple[Any, ...]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Fetch one row."""
        converted_sql = self._convert_placeholders(sql)
        row = self._fetch_one(converted_sql, params or ())
        return dict(row) if row else None
    
    async def begin_transaction(self) -> None:
        """Begin a transaction."""
        self._execute("BEGIN TRANSACTION")
        self._in_transaction = True
    
    async def commit_transaction(self) -> None:
        """Commit the transaction."""
        self._execute("COMMIT")
        self._in_transaction = False
    
    async def rollback_transaction(self) -> None:
        """Rollback the transaction."""
        self._execute("ROLLBACK")
        self._in_transaction = False
    
    # Private methods
    
    def _execute(self, sql: str, params: Tuple[Any, ...] = ()) -> sqlite3.Cursor:
        """Execute SQL and return cursor."""
        if not self._conn:
            raise QueryError("Database not connected")
        try:
            cursor = self._conn.execute(sql, params)
            if not self._in_transaction:
                self._conn.commit()
            return cursor
        except sqlite3.Error as e:
            raise QueryError(str(e), query=sql, params=params)
    
    def _fetch_all(self, sql: str, params: Tuple[Any, ...] = ()) -> List[sqlite3.Row]:
        """Execute SQL and fetch all rows."""
        cursor = self._execute(sql, params)
        return cursor.fetchall()
    
    def _fetch_one(self, sql: str, params: Tuple[Any, ...] = ()) -> Optional[sqlite3.Row]:
        """Execute SQL and fetch one row."""
        cursor = self._execute(sql, params)
        return cursor.fetchone()
    
    async def _get_by_id(self, table: str, id: int, fields: Dict[str, "FieldInfo"]) -> Dict[str, Any]:
        """Get a row by id."""
        sql = f"SELECT * FROM {table} WHERE id = ?"
        row = self._fetch_one(sql, (id,))
        if row is None:
            raise NotFoundError(table, id=id)
        return self._deserialize_row(row, fields)
    
    def _field_to_column(self, field: "FieldInfo") -> str:
        """Convert a FieldInfo to SQLite column definition."""
        parts = [field.name]
        
        # Type mapping for SQLite
        type_map = {
            SQLType.INTEGER: "INTEGER",
            SQLType.BIGINT: "INTEGER",
            SQLType.REAL: "REAL",
            SQLType.DOUBLE: "REAL",
            SQLType.DECIMAL: "REAL",
            SQLType.VARCHAR: "TEXT",
            SQLType.TEXT: "TEXT",
            SQLType.BOOLEAN: "INTEGER",
            SQLType.TIMESTAMP: "TEXT",
            SQLType.DATE: "TEXT",
            SQLType.TIME: "TEXT",
            SQLType.JSON: "TEXT",
            SQLType.JSONB: "TEXT",
            SQLType.UUID: "TEXT",
            SQLType.BLOB: "BLOB",
        }
        
        parts.append(type_map.get(field.sql_type, "TEXT"))
        
        if field.primary_key:
            parts.append("PRIMARY KEY")
            if field.auto_increment:
                parts.append("AUTOINCREMENT")
        
        if not field.nullable and not field.primary_key:
            parts.append("NOT NULL")
        
        if field.unique and not field.primary_key:
            parts.append("UNIQUE")
        
        return " ".join(parts)
    
    def _build_select_sql(self, table: str, query: "Query") -> Tuple[str, Tuple[Any, ...]]:
        """Build SELECT SQL from query."""
        sql = f"SELECT * FROM {table}"
        where_clause, params = self._build_where_clause(query)
        
        if where_clause:
            sql += f" WHERE {where_clause}"
        
        # Ordering
        if query._order_by:
            order_parts = []
            for order in query._order_by:
                if order.startswith("-"):
                    order_parts.append(f"{order[1:]} DESC")
                else:
                    order_parts.append(f"{order} ASC")
            sql += f" ORDER BY {', '.join(order_parts)}"
        
        # Limit and offset
        if query._limit:
            sql += f" LIMIT {query._limit}"
        if query._offset:
            sql += f" OFFSET {query._offset}"
        
        return sql, params
    
    def _build_where_clause(self, query: "Query") -> Tuple[str, Tuple[Any, ...]]:
        """Build WHERE clause from query."""
        conditions = []
        params = []
        
        # where conditions
        for field, value in query._where.items():
            conditions.append(f"{field} = ?")
            params.append(value)
        
        # where_not conditions
        for field, value in query._where_not.items():
            conditions.append(f"{field} != ?")
            params.append(value)
        
        # where_in conditions
        for field, values in query._where_in.items():
            placeholders = ", ".join("?" for _ in values)
            conditions.append(f"{field} IN ({placeholders})")
            params.extend(values)
        
        # where_like conditions
        for field, pattern in query._where_like.items():
            conditions.append(f"{field} LIKE ?")
            params.append(pattern)
        
        # where_gt conditions
        for field, value in query._where_gt.items():
            conditions.append(f"{field} > ?")
            params.append(value)
        
        # where_gte conditions
        for field, value in query._where_gte.items():
            conditions.append(f"{field} >= ?")
            params.append(value)
        
        # where_lt conditions
        for field, value in query._where_lt.items():
            conditions.append(f"{field} < ?")
            params.append(value)
        
        # where_lte conditions
        for field, value in query._where_lte.items():
            conditions.append(f"{field} <= ?")
            params.append(value)
        
        # where_null conditions
        for field in query._where_null:
            conditions.append(f"{field} IS NULL")
        
        # where_not_null conditions
        for field in query._where_not_null:
            conditions.append(f"{field} IS NOT NULL")
        
        where_clause = " AND ".join(conditions) if conditions else ""
        return where_clause, tuple(params)
    
    def _deserialize_row(self, row: sqlite3.Row, fields: Dict[str, "FieldInfo"]) -> Dict[str, Any]:
        """Deserialize a database row to Python types."""
        result = {}
        for key in row.keys():
            value = row[key]
            if key in fields:
                result[key] = deserialize_value(value, fields[key])
            else:
                result[key] = value
        return result
    
    def _convert_placeholders(self, sql: str) -> str:
        """Convert $1, $2 style placeholders to ? style.
        
        FUNDAMENTAL: Properly skips string literals to avoid corrupting
        strings like '$100' inside SQL.
        """
        result = []
        i = 0
        in_string = None
        
        while i < len(sql):
            char = sql[i]
            
            # Handle string literal boundaries (SQL uses single quotes)
            if in_string:
                result.append(char)
                # Handle escaped quotes ('')
                if char == in_string:
                    if i + 1 < len(sql) and sql[i + 1] == in_string:
                        # Escaped quote - consume both
                        result.append(sql[i + 1])
                        i += 2
                        continue
                    else:
                        in_string = None
                i += 1
                continue
            
            # Check for string start
            if char == "'":
                in_string = "'"
                result.append(char)
                i += 1
                continue
            
            # Check for $N placeholder pattern (only outside strings)
            if char == '$' and i + 1 < len(sql) and sql[i + 1].isdigit():
                # Found placeholder - replace with ?
                result.append('?')
                i += 1
                # Skip all digits
                while i < len(sql) and sql[i].isdigit():
                    i += 1
                continue
            
            result.append(char)
            i += 1
        
        return ''.join(result)
    
    # Convenience methods
    
    def reset(self) -> None:
        """Reset the database (for tests)."""
        if self._conn:
            # Get all tables
            cursor = self._conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [row[0] for row in cursor.fetchall()]
            
            # Drop all tables
            for table in tables:
                if not table.startswith("sqlite_"):
                    self._conn.execute(f"DROP TABLE IF EXISTS {table}")
            self._conn.commit()

