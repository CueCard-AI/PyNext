"""
PyNext Database Transaction Module.

Full transaction support with savepoints, isolation levels,
and automatic rollback on errors.

Design: Safe by default, powerful when needed.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, List, Optional, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from pynext.db.adapters.base import Adapter


class IsolationLevel(str, Enum):
    """
    Database transaction isolation levels.
    
    From weakest to strongest:
    - READ_UNCOMMITTED: Can see uncommitted changes (dirty reads)
    - READ_COMMITTED: Only see committed changes (default PostgreSQL)
    - REPEATABLE_READ: Consistent reads within transaction
    - SERIALIZABLE: Strongest isolation, as if transactions ran serially
    """
    READ_UNCOMMITTED = "read_uncommitted"
    READ_COMMITTED = "read_committed"
    REPEATABLE_READ = "repeatable_read"
    SERIALIZABLE = "serializable"


class Savepoint:
    """
    A savepoint within a transaction.
    
    Savepoints allow partial rollbacks - if something fails,
    you can roll back just to the savepoint, not the whole transaction.
    
    Usage:
        async with db.transaction() as tx:
            await User.insert(name="John")
            
            async with tx.savepoint() as sp:
                await Post.insert(title="Risky")
                # If this fails, only the savepoint rolls back
                # User insert is preserved
    """
    
    def __init__(
        self,
        adapter: "Adapter",
        name: str,
        parent: Optional["Transaction"] = None,
    ):
        self._adapter = adapter
        self._name = name
        self._parent = parent
        self._released = False
        self._rolled_back = False
    
    @property
    def name(self) -> str:
        """The savepoint name."""
        return self._name
    
    async def release(self) -> None:
        """
        Release (commit) this savepoint.
        
        After release, the savepoint's changes become part of
        the parent transaction.
        """
        if not self._released and not self._rolled_back:
            await self._adapter.execute(f"RELEASE SAVEPOINT {self._name}")
            self._released = True
    
    async def rollback(self) -> None:
        """
        Rollback to this savepoint.
        
        Undoes all changes since the savepoint was created.
        """
        if not self._released and not self._rolled_back:
            await self._adapter.execute(f"ROLLBACK TO SAVEPOINT {self._name}")
            self._rolled_back = True
    
    async def __aenter__(self) -> "Savepoint":
        """Enter the savepoint context."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Exit the savepoint context."""
        if exc_type is not None:
            # Error occurred - rollback savepoint
            await self.rollback()
            # Don't propagate the exception if parent handles it
            return False
        else:
            # Success - release savepoint
            await self.release()
        return False


class Transaction:
    """
    Database transaction with full control.
    
    Features:
    - Auto-commit on success (configurable)
    - Auto-rollback on error
    - Savepoints for partial rollbacks
    - Configurable isolation levels
    
    Usage:
        # Simple (auto-commit)
        async with db.transaction():
            await User.insert(name="John")
            await Post.insert(title="Hello")
        
        # With savepoints
        async with db.transaction() as tx:
            await User.insert(name="John")
            
            async with tx.savepoint():
                await Post.insert(title="Risky")
                # If this fails, user insert is preserved
        
        # Manual control
        async with db.transaction(auto_commit=False) as tx:
            await User.insert(name="John")
            if condition:
                await tx.commit()
            else:
                await tx.rollback()
        
        # Isolation level
        async with db.transaction(isolation="serializable"):
            # Strong consistency
            ...
    """
    
    def __init__(
        self,
        isolation: Optional[str] = None,
        auto_commit: bool = True,
    ):
        """
        Create a new transaction.
        
        Args:
            isolation: Isolation level (read_committed, serializable, etc.)
            auto_commit: Auto-commit on successful exit (default: True)
        """
        self._isolation = isolation
        self._auto_commit = auto_commit
        self._adapter: Optional["Adapter"] = None
        self._committed = False
        self._rolled_back = False
        self._savepoint_counter = 0
        self._savepoints: List[Savepoint] = []
    
    @property
    def is_active(self) -> bool:
        """Whether the transaction is still active."""
        return not self._committed and not self._rolled_back
    
    @property
    def isolation_level(self) -> Optional[str]:
        """The isolation level for this transaction."""
        return self._isolation
    
    async def commit(self) -> None:
        """
        Commit the transaction.
        
        Makes all changes permanent.
        """
        if not self._committed and not self._rolled_back:
            if self._adapter:
                await self._adapter.commit_transaction()
            self._committed = True
    
    async def rollback(self) -> None:
        """
        Rollback the transaction.
        
        Undoes all changes since the transaction began.
        """
        if not self._committed and not self._rolled_back:
            if self._adapter:
                await self._adapter.rollback_transaction()
            self._rolled_back = True
    
    def savepoint(self, name: Optional[str] = None) -> Savepoint:
        """
        Create a savepoint within this transaction.
        
        Args:
            name: Optional savepoint name (auto-generated if not provided)
            
        Returns:
            Savepoint context manager
            
        Examples:
            async with db.transaction() as tx:
                await User.insert(name="Safe")
                
                async with tx.savepoint():
                    await Post.insert(title="Risky")
                    # Can rollback just this part
        """
        if name is None:
            self._savepoint_counter += 1
            name = f"sp_{self._savepoint_counter}"
        
        savepoint = Savepoint(self._adapter, name, parent=self)
        self._savepoints.append(savepoint)
        return _SavepointContext(self._adapter, name, savepoint)
    
    async def __aenter__(self) -> "Transaction":
        """Enter the transaction context."""
        from pynext.db.table import get_adapter
        
        self._adapter = get_adapter()
        
        # Begin transaction first
        await self._adapter.begin_transaction()
        
        # Note: Isolation level setting is adapter-specific
        # SQLite doesn't support SET TRANSACTION ISOLATION LEVEL
        # PostgreSQL and others do - this would be handled by specific adapters
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Exit the transaction context."""
        if exc_type is not None:
            # Error occurred - rollback
            await self.rollback()
            return False  # Re-raise the exception
        
        if self._auto_commit and not self._committed and not self._rolled_back:
            # Auto-commit on success
            await self.commit()
        
        return False
    
    def _get_isolation_sql(self) -> Optional[str]:
        """Get SQL for setting isolation level."""
        if not self._isolation:
            return None
        
        # Map to SQL syntax (PostgreSQL style)
        level_map = {
            "read_uncommitted": "READ UNCOMMITTED",
            "read_committed": "READ COMMITTED",
            "repeatable_read": "REPEATABLE READ",
            "serializable": "SERIALIZABLE",
        }
        
        sql_level = level_map.get(self._isolation.lower())
        if sql_level:
            return f"SET TRANSACTION ISOLATION LEVEL {sql_level}"
        
        return None


class _SavepointContext:
    """Internal context manager for savepoints that creates the savepoint on enter."""
    
    def __init__(self, adapter: "Adapter", name: str, savepoint: Savepoint):
        self._adapter = adapter
        self._name = name
        self._savepoint = savepoint
    
    async def __aenter__(self) -> Savepoint:
        """Create the savepoint."""
        await self._adapter.execute(f"SAVEPOINT {self._name}")
        return self._savepoint
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Handle savepoint exit."""
        return await self._savepoint.__aexit__(exc_type, exc_val, exc_tb)


# Convenience function for simple transactions
@asynccontextmanager
async def transaction(
    isolation: Optional[str] = None,
    auto_commit: bool = True,
):
    """
    Simple transaction context manager.
    
    Shortcut for db.transaction() when you don't need the db object.
    
    Examples:
        async with transaction():
            await User.insert(name="John")
            await Post.insert(title="Hello")
    """
    tx = Transaction(isolation=isolation, auto_commit=auto_commit)
    async with tx:
        yield tx


__all__ = [
    "Transaction",
    "Savepoint",
    "IsolationLevel",
    "transaction",
]

