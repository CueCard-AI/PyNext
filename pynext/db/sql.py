"""
PyNext Raw SQL Module.

When the ORM isn't enough, raw SQL is always available.
Safe, parameterized, with optional model mapping.

Design: Raw power when you need it, safety always.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from pynext.db.table import Table

T = TypeVar("T", bound="Table")


class Database:
    """
    Raw SQL interface for database operations.
    
    Use this when the ORM isn't enough.
    All queries use parameterized placeholders ($1, $2, ...) for safety.
    
    Usage:
        from pynext.db import db
        
        # Simple query
        users = await db.sql("SELECT * FROM users WHERE role = $1", "admin")
        
        # With model mapping
        users = await db.sql(
            "SELECT * FROM users WHERE role = $1",
            "admin",
            model=User
        )
        
        # Execute (INSERT/UPDATE/DELETE)
        count = await db.execute(
            "UPDATE users SET active = true WHERE last_login > $1",
            datetime(2024, 1, 1)
        )
    """
    
    async def sql(
        self,
        query: str,
        *args: Any,
        model: Optional[Type[T]] = None,
    ) -> List[Any]:
        """
        Execute a SELECT query and return results.
        
        Examples:
            # Returns list of dicts
            users = await db.sql("SELECT * FROM users WHERE role = $1", "admin")
            
            # Returns list of User instances
            users = await db.sql(
                "SELECT * FROM users WHERE role = $1",
                "admin",
                model=User
            )
        
        Args:
            query: SQL query with $1, $2, ... placeholders
            *args: Parameter values
            model: Optional model class to map results to
            
        Returns:
            List of dicts or model instances
        """
        from pynext.db.table import get_adapter
        
        adapter = get_adapter()
        rows = await adapter.fetch_all(query, args if args else None)
        
        if model is not None:
            return [model._from_row(row) for row in rows]
        
        return rows
    
    async def sql_one(
        self,
        query: str,
        *args: Any,
        model: Optional[Type[T]] = None,
    ) -> Optional[Any]:
        """
        Execute a SELECT query and return first result.
        
        Examples:
            user = await db.sql_one(
                "SELECT * FROM users WHERE id = $1",
                1,
                model=User
            )
        
        Args:
            query: SQL query with $1, $2, ... placeholders
            *args: Parameter values
            model: Optional model class to map result to
            
        Returns:
            Dict, model instance, or None
        """
        from pynext.db.table import get_adapter
        
        adapter = get_adapter()
        row = await adapter.fetch_one(query, args if args else None)
        
        if row is None:
            return None
        
        if model is not None:
            return model._from_row(row)
        
        return row
    
    async def sql_val(
        self,
        query: str,
        *args: Any,
    ) -> Optional[Any]:
        """
        Execute a query and return a single value.
        
        Perfect for COUNT, SUM, MAX, etc.
        
        Examples:
            count = await db.sql_val("SELECT COUNT(*) FROM users")
            total = await db.sql_val("SELECT SUM(balance) FROM accounts")
        
        Args:
            query: SQL query
            *args: Parameter values
            
        Returns:
            The first column of the first row, or None
        """
        from pynext.db.table import get_adapter
        
        adapter = get_adapter()
        row = await adapter.fetch_one(query, args if args else None)
        
        if row is None:
            return None
        
        # Get first value from row
        if isinstance(row, dict):
            return list(row.values())[0] if row else None
        return row[0] if row else None
    
    async def execute(
        self,
        query: str,
        *args: Any,
    ) -> int:
        """
        Execute an INSERT, UPDATE, or DELETE query.
        
        Examples:
            # Update
            count = await db.execute(
                "UPDATE users SET active = true WHERE last_login > $1",
                datetime(2024, 1, 1)
            )
            
            # Delete
            count = await db.execute(
                "DELETE FROM users WHERE active = false"
            )
            
            # Insert
            await db.execute(
                "INSERT INTO logs (message, level) VALUES ($1, $2)",
                "User logged in",
                "info"
            )
        
        Args:
            query: SQL query with $1, $2, ... placeholders
            *args: Parameter values
            
        Returns:
            Number of affected rows (for UPDATE/DELETE)
        """
        from pynext.db.table import get_adapter
        
        adapter = get_adapter()
        result = await adapter.execute(query, args if args else None)
        
        # Return rowcount if available
        if hasattr(result, 'rowcount'):
            return result.rowcount
        return 0
    
    def transaction(
        self,
        isolation: Optional[str] = None,
        auto_commit: bool = True,
    ) -> "Transaction":
        """
        Start a database transaction.
        
        Examples:
            # Simple (auto-commit on success, rollback on error)
            async with db.transaction():
                await User.insert(name="John")
                await Post.insert(title="Hello", author_id=1)
            
            # With isolation level
            async with db.transaction(isolation="serializable"):
                # Strong consistency
                ...
            
            # Manual control
            async with db.transaction(auto_commit=False) as tx:
                await User.insert(name="John")
                if some_condition:
                    await tx.commit()
                else:
                    await tx.rollback()
        
        Args:
            isolation: Isolation level (read_committed, serializable, etc.)
            auto_commit: Auto-commit on success (default: True)
            
        Returns:
            Transaction context manager
        """
        from pynext.db.transaction import Transaction
        return Transaction(isolation=isolation, auto_commit=auto_commit)
    
    async def raw(self, query: str, *args: Any) -> Any:
        """
        Execute raw SQL and return the cursor/result object.
        
        Use when you need full control.
        
        Args:
            query: SQL query
            *args: Parameter values
            
        Returns:
            Raw cursor/result from adapter
        """
        from pynext.db.table import get_adapter
        
        adapter = get_adapter()
        return await adapter.execute(query, args if args else None)


# Global database instance
db = Database()


# Export
__all__ = ["Database", "db"]

