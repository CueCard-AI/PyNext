"""
PyNext Mock Database Adapter.

Pure Python dict-based adapter for instant testing.
No external dependencies, predictable behavior.

Perfect for:
- Unit tests
- Quick prototyping
- Demos
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from pynext.db.adapters.base import Adapter
from pynext.db.exceptions import NotFoundError

if TYPE_CHECKING:
    from pynext.db.query import Query
    from pynext.db.fields import FieldInfo


class MockAdapter(Adapter):
    """
    In-memory dict-based database adapter.
    
    Stores data in Python dicts. No SQL, no dependencies.
    Great for testing and prototyping.
    
    Usage:
        adapter = MockAdapter()
        await adapter.connect()
        
        # Now use it
        await adapter.insert("users", {"name": "John"}, fields)
    """
    
    def __init__(self):
        self._tables: Dict[str, Dict[int, Dict[str, Any]]] = {}
        self._counters: Dict[str, int] = {}
        self._connected = False
        self._in_transaction = False
        self._transaction_backup: Optional[Dict[str, Dict[int, Dict[str, Any]]]] = None
    
    async def connect(self) -> None:
        """Initialize the mock database."""
        self._connected = True
    
    async def disconnect(self) -> None:
        """Clear all data."""
        self._tables.clear()
        self._counters.clear()
        self._connected = False
    
    async def create_table(self, table: str, fields: Dict[str, "FieldInfo"]) -> None:
        """Create a table (just initialize the dict)."""
        if table not in self._tables:
            self._tables[table] = {}
            self._counters[table] = 0
    
    async def drop_table(self, table: str) -> None:
        """Drop a table."""
        self._tables.pop(table, None)
        self._counters.pop(table, None)
    
    async def insert(
        self,
        table: str,
        data: Dict[str, Any],
        fields: Dict[str, "FieldInfo"],
    ) -> Dict[str, Any]:
        """Insert a row and return it with generated id."""
        # Ensure table exists
        if table not in self._tables:
            await self.create_table(table, fields)
        
        # Generate id
        self._counters[table] += 1
        row_id = self._counters[table]
        
        # Create row with auto-fields
        now = datetime.utcnow()
        row = {
            "id": row_id,
            "created_at": now,
            "updated_at": now,
            **deepcopy(data),
        }
        
        # Store
        self._tables[table][row_id] = row
        
        return deepcopy(row)
    
    async def select(
        self,
        table: str,
        query: "Query",
        fields: Dict[str, "FieldInfo"],
    ) -> List[Dict[str, Any]]:
        """Select rows matching the query."""
        if table not in self._tables:
            return []
        
        rows = list(self._tables[table].values())
        
        # Apply filters
        rows = self._apply_filters(rows, query)
        
        # Apply ordering
        rows = self._apply_ordering(rows, query)
        
        # Apply offset and limit
        if query._offset:
            rows = rows[query._offset:]
        if query._limit:
            rows = rows[:query._limit]
        
        return [deepcopy(row) for row in rows]
    
    async def select_one(
        self,
        table: str,
        query: "Query",
        fields: Dict[str, "FieldInfo"],
    ) -> Optional[Dict[str, Any]]:
        """Select a single row."""
        rows = await self.select(table, query, fields)
        return rows[0] if rows else None
    
    async def update(
        self,
        table: str,
        id: int,
        data: Dict[str, Any],
        fields: Dict[str, "FieldInfo"],
    ) -> Dict[str, Any]:
        """Update a row by id."""
        if table not in self._tables or id not in self._tables[table]:
            raise NotFoundError(table, id=id)
        
        row = self._tables[table][id]
        row.update(data)
        row["updated_at"] = datetime.utcnow()
        
        return deepcopy(row)
    
    async def delete(self, table: str, id: int) -> bool:
        """Delete a row by id."""
        if table not in self._tables:
            return False
        if id not in self._tables[table]:
            return False
        
        del self._tables[table][id]
        return True
    
    async def count(self, table: str, query: "Query") -> int:
        """Count matching rows."""
        if table not in self._tables:
            return 0
        
        rows = list(self._tables[table].values())
        rows = self._apply_filters(rows, query)
        return len(rows)
    
    async def exists(self, table: str, query: "Query") -> bool:
        """Check if any rows match."""
        return await self.count(table, query) > 0
    
    async def execute(
        self,
        sql: str,
        params: Optional[Tuple[Any, ...]] = None,
    ) -> Any:
        """Execute raw SQL (not supported in mock)."""
        # For mock, we just return None
        # Real adapters would execute the SQL
        return None
    
    async def fetch_all(
        self,
        sql: str,
        params: Optional[Tuple[Any, ...]] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch all rows (not supported in mock)."""
        return []
    
    async def fetch_one(
        self,
        sql: str,
        params: Optional[Tuple[Any, ...]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Fetch one row (not supported in mock)."""
        return None
    
    async def begin_transaction(self) -> None:
        """Begin a transaction (backup current state)."""
        self._in_transaction = True
        self._transaction_backup = deepcopy(self._tables)
    
    async def commit_transaction(self) -> None:
        """Commit transaction (discard backup)."""
        self._in_transaction = False
        self._transaction_backup = None
    
    async def rollback_transaction(self) -> None:
        """Rollback transaction (restore backup)."""
        if self._transaction_backup is not None:
            self._tables = self._transaction_backup
        self._in_transaction = False
        self._transaction_backup = None
    
    def _apply_filters(self, rows: List[Dict[str, Any]], query: "Query") -> List[Dict[str, Any]]:
        """Apply query filters to rows."""
        result = rows
        
        # where conditions
        for field, value in query._where.items():
            result = [r for r in result if r.get(field) == value]
        
        # where_not conditions
        for field, value in query._where_not.items():
            result = [r for r in result if r.get(field) != value]
        
        # where_in conditions
        for field, values in query._where_in.items():
            result = [r for r in result if r.get(field) in values]
        
        # where_like conditions
        for field, pattern in query._where_like.items():
            import re
            # Convert SQL LIKE to regex
            regex_pattern = pattern.replace("%", ".*").replace("_", ".")
            regex = re.compile(f"^{regex_pattern}$", re.IGNORECASE)
            result = [r for r in result if regex.match(str(r.get(field, "")))]
        
        # where_gt conditions
        for field, value in query._where_gt.items():
            result = [r for r in result if r.get(field) is not None and r.get(field) > value]
        
        # where_gte conditions
        for field, value in query._where_gte.items():
            result = [r for r in result if r.get(field) is not None and r.get(field) >= value]
        
        # where_lt conditions
        for field, value in query._where_lt.items():
            result = [r for r in result if r.get(field) is not None and r.get(field) < value]
        
        # where_lte conditions
        for field, value in query._where_lte.items():
            result = [r for r in result if r.get(field) is not None and r.get(field) <= value]
        
        # where_null conditions
        for field in query._where_null:
            result = [r for r in result if r.get(field) is None]
        
        # where_not_null conditions
        for field in query._where_not_null:
            result = [r for r in result if r.get(field) is not None]
        
        return result
    
    def _apply_ordering(self, rows: List[Dict[str, Any]], query: "Query") -> List[Dict[str, Any]]:
        """Apply query ordering to rows."""
        if not query._order_by:
            return rows
        
        result = rows.copy()
        
        # Apply orderings in reverse (last ordering is primary)
        for order in reversed(query._order_by):
            reverse = order.startswith("-")
            field = order.lstrip("-")
            result.sort(key=lambda r: (r.get(field) is None, r.get(field)), reverse=reverse)
        
        return result
    
    # Convenience methods for testing
    
    def reset(self) -> None:
        """Reset all data (for tests)."""
        self._tables.clear()
        self._counters.clear()
    
    def get_all(self, table: str) -> List[Dict[str, Any]]:
        """Get all rows from a table (for tests)."""
        if table not in self._tables:
            return []
        return list(self._tables[table].values())
    
    def get_by_id(self, table: str, id: int) -> Optional[Dict[str, Any]]:
        """Get a row by id (for tests)."""
        if table not in self._tables:
            return None
        return self._tables[table].get(id)

