"""
PyNext Live Query Change Detection - Base Classes.

Abstract base class for all change detectors.
Each detector implements a different strategy for detecting database changes.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from pynext.db.live.config import LiveQueryConfig, QuerySignature


class ChangeType(str, Enum):
    """
    Type of database change.
    
    - INSERT: New row added
    - UPDATE: Existing row modified
    - DELETE: Row removed
    - TRUNCATE: All rows removed (rare)
    - UNKNOWN: Change type not determined
    """
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    TRUNCATE = "TRUNCATE"
    UNKNOWN = "UNKNOWN"


@dataclass
class ChangeEvent:
    """
    Represents a change to a database table.
    
    Contains all information needed to update a live query.
    
    Attributes:
        table: Name of the table that changed
        type: Type of change (INSERT, UPDATE, DELETE)
        row_id: ID of the affected row (if available)
        old_data: Previous row data (for UPDATE/DELETE)
        new_data: New row data (for INSERT/UPDATE)
        timestamp: When the change occurred
        source: Where the change was detected from
        columns_changed: List of changed column names (for UPDATE)
    """
    table: str
    type: ChangeType
    row_id: Optional[int] = None
    old_data: Optional[Dict[str, Any]] = None
    new_data: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: str = "unknown"
    columns_changed: List[str] = field(default_factory=list)
    
    @property
    def has_data(self) -> bool:
        """Check if event has row data."""
        return self.old_data is not None or self.new_data is not None
    
    @property
    def is_insert(self) -> bool:
        return self.type == ChangeType.INSERT
    
    @property
    def is_update(self) -> bool:
        return self.type == ChangeType.UPDATE
    
    @property
    def is_delete(self) -> bool:
        return self.type == ChangeType.DELETE
    
    def affects_query(self, signature: "QuerySignature") -> bool:
        """
        Check if this change could affect a query.
        
        Used to filter changes before applying updates.
        A change affects a query if:
        1. Same table
        2. Inserted row might match filters
        3. Updated row's changed columns are used in filters/ordering
        4. Deleted row might have been in results
        """
        # Must be same table
        if self.table != signature.table:
            return False
        
        # Simple queries (no filters) are always affected
        if signature.is_simple:
            return True
        
        # For updates, check if changed columns overlap with query
        if self.is_update and self.columns_changed:
            # Check WHERE clause fields
            where_fields = set()
            for clause in signature.where_clauses:
                for key in clause:
                    field_name = key.split("__")[0]  # Handle __gt, __in, etc.
                    where_fields.add(field_name)
            
            # Check ORDER BY field
            if signature.order_by:
                order_field = signature.order_by.lstrip("-")
                where_fields.add(order_field)
            
            # If any changed column is in query, it's affected
            if where_fields.intersection(self.columns_changed):
                return True
            
            # If ID in results might have changed
            if self.row_id is not None:
                return True
        
        # For INSERT/DELETE, we can't know without checking filters
        # So assume it could affect the query
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization."""
        return {
            "table": self.table,
            "type": self.type.value,
            "row_id": self.row_id,
            "old_data": self.old_data,
            "new_data": self.new_data,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "columns_changed": self.columns_changed,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChangeEvent":
        """Create from dict."""
        return cls(
            table=data["table"],
            type=ChangeType(data["type"]),
            row_id=data.get("row_id"),
            old_data=data.get("old_data"),
            new_data=data.get("new_data"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.utcnow(),
            source=data.get("source", "unknown"),
            columns_changed=data.get("columns_changed", []),
        )


# Type for change callbacks
ChangeCallback = Callable[[ChangeEvent], None]


class ChangeDetector(ABC):
    """
    Abstract base class for change detection strategies.
    
    Implementations:
    - PostgresNotifyDetector: Uses PostgreSQL LISTEN/NOTIFY
    - SupabaseRealtimeDetector: Uses Supabase Realtime
    - PollingDetector: Polls for changes at intervals
    
    Usage:
        detector = PostgresNotifyDetector()
        await detector.start()
        
        subscription_id = await detector.subscribe("users", on_change)
        
        # Later
        await detector.unsubscribe(subscription_id)
        await detector.stop()
    """
    
    def __init__(self):
        self._running = False
        self._subscriptions: Dict[str, Dict[str, ChangeCallback]] = {}  # table -> {id: callback}
        self._tables: Set[str] = set()
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name for this detector."""
        pass
    
    @property
    @abstractmethod
    def priority(self) -> int:
        """
        Priority for auto-selection (higher = preferred).
        
        - 100: Supabase Realtime
        - 50: PostgreSQL LISTEN/NOTIFY
        - 10: Polling
        """
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """
        Check if this detector is available.
        
        For example, PostgresNotifyDetector checks if connected to PostgreSQL.
        """
        pass
    
    @abstractmethod
    async def start(self) -> None:
        """
        Start the detector.
        
        This should initialize any connections or listeners needed.
        """
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """
        Stop the detector.
        
        This should clean up any resources.
        """
        pass
    
    @abstractmethod
    async def subscribe_table(self, table: str) -> None:
        """
        Start listening for changes on a table.
        
        Called when the first subscription for a table is added.
        """
        pass
    
    @abstractmethod
    async def unsubscribe_table(self, table: str) -> None:
        """
        Stop listening for changes on a table.
        
        Called when the last subscription for a table is removed.
        """
        pass
    
    async def subscribe(
        self,
        table: str,
        callback: ChangeCallback,
        subscription_id: Optional[str] = None,
    ) -> str:
        """
        Subscribe to changes on a table.
        
        Args:
            table: Table name to watch
            callback: Function to call on changes
            subscription_id: Optional ID (generated if not provided)
        
        Returns:
            Subscription ID for unsubscribing
        """
        import uuid
        
        sub_id = subscription_id or f"sub_{uuid.uuid4().hex[:12]}"
        
        # Initialize table subscriptions if needed
        if table not in self._subscriptions:
            self._subscriptions[table] = {}
        
        # Add subscription
        self._subscriptions[table][sub_id] = callback
        
        # Start listening if first subscription for this table
        if table not in self._tables:
            self._tables.add(table)
            await self.subscribe_table(table)
        
        return sub_id
    
    async def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from changes.
        
        Args:
            subscription_id: ID returned from subscribe()
        
        Returns:
            True if unsubscribed, False if not found
        """
        for table, subs in self._subscriptions.items():
            if subscription_id in subs:
                del subs[subscription_id]
                
                # Stop listening if no more subscriptions for this table
                if not subs:
                    del self._subscriptions[table]
                    self._tables.discard(table)
                    await self.unsubscribe_table(table)
                
                return True
        
        return False
    
    def _notify_subscribers(self, event: ChangeEvent) -> None:
        """
        Notify all subscribers for a table about a change.
        
        Called by detector implementations when a change is detected.
        """
        table_subs = self._subscriptions.get(event.table, {})
        
        for callback in table_subs.values():
            try:
                callback(event)
            except Exception as e:
                # Log but don't stop other callbacks
                import logging
                logging.warning(f"Subscriber callback error: {e}")
    
    def get_subscription_count(self, table: Optional[str] = None) -> int:
        """Get number of subscriptions, optionally for a specific table."""
        if table:
            return len(self._subscriptions.get(table, {}))
        return sum(len(subs) for subs in self._subscriptions.values())
    
    def get_subscribed_tables(self) -> List[str]:
        """Get list of tables with active subscriptions."""
        return list(self._tables)
    
    @property
    def is_running(self) -> bool:
        """Check if detector is running."""
        return self._running

