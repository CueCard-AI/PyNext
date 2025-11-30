"""
PyNext Database Adapter Base.

Abstract interface that all database adapters must implement.
This ensures consistent behavior across SQLite, PostgreSQL, Supabase, etc.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from pynext.db.query import Query
    from pynext.db.fields import FieldInfo


class Adapter(ABC):
    """
    Abstract base class for database adapters.
    
    All adapters must implement these methods to provide
    a consistent interface for database operations.
    
    Example implementation:
        class PostgresAdapter(Adapter):
            async def insert(self, table, data, fields):
                # Execute INSERT and return created row
                ...
    """
    
    @abstractmethod
    async def connect(self) -> None:
        """
        Establish connection to the database.
        
        Called once when the adapter is initialized.
        Should set up connection pools, etc.
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """
        Close database connection.
        
        Called when shutting down.
        Should clean up resources.
        """
        pass
    
    @abstractmethod
    async def create_table(self, table: str, fields: Dict[str, "FieldInfo"]) -> None:
        """
        Create a table with the given fields.
        
        Args:
            table: Table name
            fields: Field definitions
            
        Should be idempotent (CREATE TABLE IF NOT EXISTS).
        """
        pass
    
    @abstractmethod
    async def drop_table(self, table: str) -> None:
        """
        Drop a table.
        
        Args:
            table: Table name
        """
        pass
    
    @abstractmethod
    async def insert(
        self,
        table: str,
        data: Dict[str, Any],
        fields: Dict[str, "FieldInfo"],
    ) -> Dict[str, Any]:
        """
        Insert a row and return the created record.
        
        Args:
            table: Table name
            data: Column values to insert
            fields: Field definitions (for serialization)
            
        Returns:
            The created row including generated id
        """
        pass
    
    @abstractmethod
    async def select(
        self,
        table: str,
        query: "Query",
        fields: Dict[str, "FieldInfo"],
    ) -> List[Dict[str, Any]]:
        """
        Select rows matching the query.
        
        Args:
            table: Table name
            query: Query with filters, ordering, etc.
            fields: Field definitions (for deserialization)
            
        Returns:
            List of matching rows
        """
        pass
    
    @abstractmethod
    async def select_one(
        self,
        table: str,
        query: "Query",
        fields: Dict[str, "FieldInfo"],
    ) -> Optional[Dict[str, Any]]:
        """
        Select a single row matching the query.
        
        Args:
            table: Table name
            query: Query with filters
            fields: Field definitions
            
        Returns:
            The matching row or None
        """
        pass
    
    @abstractmethod
    async def update(
        self,
        table: str,
        id: int,
        data: Dict[str, Any],
        fields: Dict[str, "FieldInfo"],
    ) -> Dict[str, Any]:
        """
        Update a row by id and return the updated record.
        
        Args:
            table: Table name
            id: Row id
            data: Column values to update
            fields: Field definitions
            
        Returns:
            The updated row
        """
        pass
    
    @abstractmethod
    async def delete(self, table: str, id: int) -> bool:
        """
        Delete a row by id.
        
        Args:
            table: Table name
            id: Row id
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    async def count(self, table: str, query: "Query") -> int:
        """
        Count rows matching the query.
        
        Args:
            table: Table name
            query: Query with filters
            
        Returns:
            Number of matching rows
        """
        pass
    
    @abstractmethod
    async def exists(self, table: str, query: "Query") -> bool:
        """
        Check if any rows match the query.
        
        Args:
            table: Table name
            query: Query with filters
            
        Returns:
            True if any rows match
        """
        pass
    
    @abstractmethod
    async def execute(
        self,
        sql: str,
        params: Optional[Tuple[Any, ...]] = None,
    ) -> Any:
        """
        Execute raw SQL.
        
        Args:
            sql: SQL query with $1, $2, ... placeholders
            params: Parameter values
            
        Returns:
            Query result (varies by query type)
        """
        pass
    
    @abstractmethod
    async def fetch_all(
        self,
        sql: str,
        params: Optional[Tuple[Any, ...]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute raw SQL and return all rows.
        
        Args:
            sql: SQL query
            params: Parameter values
            
        Returns:
            List of row dicts
        """
        pass
    
    @abstractmethod
    async def fetch_one(
        self,
        sql: str,
        params: Optional[Tuple[Any, ...]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Execute raw SQL and return one row.
        
        Args:
            sql: SQL query
            params: Parameter values
            
        Returns:
            Row dict or None
        """
        pass
    
    # Transaction support
    
    @abstractmethod
    async def begin_transaction(self) -> None:
        """Begin a transaction."""
        pass
    
    @abstractmethod
    async def commit_transaction(self) -> None:
        """Commit the current transaction."""
        pass
    
    @abstractmethod
    async def rollback_transaction(self) -> None:
        """Rollback the current transaction."""
        pass
    
    def transaction(self):
        """
        Context manager for transactions.
        
        Usage:
            async with adapter.transaction():
                await adapter.insert(...)
                await adapter.update(...)
        """
        return TransactionContext(self)
    
    # Batch operations
    
    async def insert_many(
        self,
        table: str,
        records: List[Dict[str, Any]],
        fields: Dict[str, "FieldInfo"],
    ) -> List[Dict[str, Any]]:
        """
        Insert multiple rows.
        
        Default implementation loops through records.
        Subclasses can override for bulk insert optimization.
        
        Args:
            table: Table name
            records: List of row data
            fields: Field definitions
            
        Returns:
            List of created rows
        """
        results = []
        for data in records:
            row = await self.insert(table, data, fields)
            results.append(row)
        return results
    
    async def update_many(
        self,
        table: str,
        query: "Query",
        data: Dict[str, Any],
        fields: Dict[str, "FieldInfo"],
    ) -> int:
        """
        Update multiple rows matching query.
        
        Args:
            table: Table name
            query: Query with filters
            data: Values to update
            fields: Field definitions
            
        Returns:
            Number of updated rows
        """
        rows = await self.select(table, query, fields)
        count = 0
        for row in rows:
            await self.update(table, row["id"], data, fields)
            count += 1
        return count
    
    async def delete_many(
        self,
        table: str,
        query: "Query",
    ) -> int:
        """
        Delete multiple rows matching query.
        
        Args:
            table: Table name
            query: Query with filters
            
        Returns:
            Number of deleted rows
        """
        # Get matching row IDs first
        from pynext.db.fields import FieldInfo, SQLType
        
        # Minimal fields for ID lookup
        fields = {"id": FieldInfo("id", int, SQLType.INTEGER)}
        rows = await self.select(table, query, fields)
        
        count = 0
        for row in rows:
            if await self.delete(table, row["id"]):
                count += 1
        return count
    
    # Savepoint support (for advanced transaction control)
    
    async def create_savepoint(self, name: str) -> None:
        """Create a savepoint."""
        await self.execute(f"SAVEPOINT {name}")
    
    async def release_savepoint(self, name: str) -> None:
        """Release (commit) a savepoint."""
        await self.execute(f"RELEASE SAVEPOINT {name}")
    
    async def rollback_to_savepoint(self, name: str) -> None:
        """Rollback to a savepoint."""
        await self.execute(f"ROLLBACK TO SAVEPOINT {name}")


class TransactionContext:
    """Context manager for database transactions."""
    
    def __init__(self, adapter: Adapter):
        self.adapter = adapter
        self._savepoint_counter = 0
    
    async def __aenter__(self):
        await self.adapter.begin_transaction()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.adapter.rollback_transaction()
            return False
        await self.adapter.commit_transaction()
        return False
    
    async def commit(self) -> None:
        """Manually commit the transaction."""
        await self.adapter.commit_transaction()
    
    async def rollback(self) -> None:
        """Manually rollback the transaction."""
        await self.adapter.rollback_transaction()
    
    def savepoint(self, name: Optional[str] = None) -> "SavepointContext":
        """
        Create a savepoint within this transaction.
        
        Args:
            name: Optional savepoint name
            
        Returns:
            Savepoint context manager
        """
        if name is None:
            self._savepoint_counter += 1
            name = f"sp_{self._savepoint_counter}"
        return SavepointContext(self.adapter, name)


class SavepointContext:
    """Context manager for savepoints."""
    
    def __init__(self, adapter: Adapter, name: str):
        self.adapter = adapter
        self.name = name
    
    async def __aenter__(self):
        await self.adapter.create_savepoint(self.name)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.adapter.rollback_to_savepoint(self.name)
            return False
        await self.adapter.release_savepoint(self.name)
        return False
    
    async def release(self) -> None:
        """Release (commit) this savepoint."""
        await self.adapter.release_savepoint(self.name)
    
    async def rollback(self) -> None:
        """Rollback to this savepoint."""
        await self.adapter.rollback_to_savepoint(self.name)

