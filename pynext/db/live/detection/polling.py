"""
PyNext Live Query - Polling Detection (Fallback).

Polls the database at configurable intervals to detect changes.
This is the fallback when PostgreSQL NOTIFY and Supabase Realtime aren't available.

How It Works:
1. Periodically queries the table for changes
2. Compares with previous results
3. Generates change events for any differences

Optimizations:
- Uses updated_at column if available for efficient change detection
- Tracks row IDs to detect inserts/deletes
- Configurable poll interval (default 30s)
- Batches changes to reduce notification overhead

Usage:
    detector = PollingDetector(interval=10.0)  # Poll every 10 seconds
    await detector.start()
    
    sub_id = await detector.subscribe("users", lambda event: print(event))
    
    await detector.stop()
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING

from pynext.db.live.detection.base import (
    ChangeDetector,
    ChangeEvent,
    ChangeType,
    ChangeCallback,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class PollingDetector(ChangeDetector):
    """
    Change detector using polling.
    
    This is the fallback detection method:
    - Works with any database
    - No special setup required
    - Configurable poll interval
    - Higher latency than event-based detection
    
    The polling is smart:
    - Uses updated_at column if available
    - Only fetches changed rows when possible
    - Batches changes before notification
    """
    
    def __init__(self, interval: float = 30.0):
        """
        Create a polling detector.
        
        Args:
            interval: Seconds between polls (default 30.0)
        """
        super().__init__()
        self._interval = interval
        self._poll_tasks: Dict[str, asyncio.Task] = {}
        self._last_data: Dict[str, Dict[int, Dict[str, Any]]] = {}  # table -> {id: row}
        self._last_poll: Dict[str, datetime] = {}
    
    @property
    def name(self) -> str:
        return "Polling"
    
    @property
    def priority(self) -> int:
        return 10  # Lowest priority (fallback only)
    
    async def is_available(self) -> bool:
        """Polling is always available if we have a database connection."""
        try:
            from pynext.db.table import get_adapter
            adapter = get_adapter()
            return adapter is not None
        except Exception:
            return False
    
    async def start(self) -> None:
        """Start the polling detector."""
        if self._running:
            return
        
        self._running = True
        logger.info(f"Polling detector started (interval: {self._interval}s)")
    
    async def stop(self) -> None:
        """Stop all polling tasks."""
        self._running = False
        
        # Cancel all poll tasks
        for table, task in list(self._poll_tasks.items()):
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        self._poll_tasks.clear()
        self._last_data.clear()
        self._last_poll.clear()
        
        logger.info("Polling detector stopped")
    
    async def subscribe_table(self, table: str) -> None:
        """Start polling a table for changes."""
        if table in self._poll_tasks:
            return
        
        # Initialize state
        self._last_data[table] = {}
        self._last_poll[table] = datetime.min
        
        # Start poll task
        task = asyncio.create_task(self._poll_loop(table))
        self._poll_tasks[table] = task
        
        logger.debug(f"Started polling: {table}")
    
    async def unsubscribe_table(self, table: str) -> None:
        """Stop polling a table."""
        task = self._poll_tasks.pop(table, None)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        self._last_data.pop(table, None)
        self._last_poll.pop(table, None)
        
        logger.debug(f"Stopped polling: {table}")
    
    async def _poll_loop(self, table: str) -> None:
        """Main polling loop for a table."""
        # Initial poll
        await self._poll_table(table)
        
        while self._running and table in self._poll_tasks:
            try:
                await asyncio.sleep(self._interval)
                
                if not self._running or table not in self._poll_tasks:
                    break
                
                await self._poll_table(table)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error polling {table}: {e}")
                await asyncio.sleep(5)  # Wait before retry
    
    async def _poll_table(self, table: str) -> None:
        """Poll a table for changes."""
        try:
            from pynext.db.table import get_adapter
            
            adapter = get_adapter()
            
            # Fetch current data
            # Try to use updated_at for efficient polling
            last_poll = self._last_poll.get(table, datetime.min)
            
            query_sql = f"SELECT * FROM {table}"
            
            # Check if table has updated_at column
            has_updated_at = await self._table_has_column(adapter, table, "updated_at")
            
            if has_updated_at and last_poll != datetime.min:
                # Only fetch recently updated rows
                query_sql += f" WHERE updated_at >= $1"
                rows = await adapter.execute(query_sql, last_poll)
            else:
                # Fetch all rows
                rows = await adapter.execute(query_sql)
            
            # Convert to dict by ID
            current_data: Dict[int, Dict[str, Any]] = {}
            for row in rows:
                row_dict = dict(row) if hasattr(row, "items") else row
                if "id" in row_dict:
                    current_data[row_dict["id"]] = row_dict
            
            # Get previous data
            previous_data = self._last_data.get(table, {})
            
            # Detect changes
            events = self._detect_changes(table, previous_data, current_data)
            
            # Update state
            if has_updated_at and last_poll != datetime.min:
                # Merge with existing data
                for row_id, row_data in current_data.items():
                    self._last_data[table][row_id] = row_data
            else:
                # Replace all data
                self._last_data[table] = current_data
            
            self._last_poll[table] = datetime.utcnow()
            
            # Notify subscribers
            for event in events:
                self._notify_subscribers(event)
                
        except Exception as e:
            logger.error(f"Error polling {table}: {e}")
    
    def _detect_changes(
        self,
        table: str,
        previous: Dict[int, Dict[str, Any]],
        current: Dict[int, Dict[str, Any]],
    ) -> List[ChangeEvent]:
        """Detect changes between previous and current data."""
        events = []
        now = datetime.utcnow()
        
        previous_ids = set(previous.keys())
        current_ids = set(current.keys())
        
        # Detect inserts (new IDs)
        for row_id in current_ids - previous_ids:
            events.append(ChangeEvent(
                table=table,
                type=ChangeType.INSERT,
                row_id=row_id,
                new_data=current[row_id],
                timestamp=now,
                source="polling",
            ))
        
        # Detect deletes (missing IDs)
        for row_id in previous_ids - current_ids:
            events.append(ChangeEvent(
                table=table,
                type=ChangeType.DELETE,
                row_id=row_id,
                old_data=previous[row_id],
                timestamp=now,
                source="polling",
            ))
        
        # Detect updates (same ID, different data)
        for row_id in previous_ids & current_ids:
            old_row = previous[row_id]
            new_row = current[row_id]
            
            # Check if any values changed
            changed_columns = []
            for key in set(old_row.keys()) | set(new_row.keys()):
                old_val = old_row.get(key)
                new_val = new_row.get(key)
                if old_val != new_val:
                    changed_columns.append(key)
            
            if changed_columns:
                events.append(ChangeEvent(
                    table=table,
                    type=ChangeType.UPDATE,
                    row_id=row_id,
                    old_data=old_row,
                    new_data=new_row,
                    timestamp=now,
                    source="polling",
                    columns_changed=changed_columns,
                ))
        
        return events
    
    async def _table_has_column(
        self,
        adapter: Any,
        table: str,
        column: str,
    ) -> bool:
        """Check if a table has a specific column."""
        try:
            # PostgreSQL
            result = await adapter.execute(
                """
                SELECT 1 FROM information_schema.columns
                WHERE table_name = $1 AND column_name = $2
                """,
                table, column
            )
            return len(result) > 0
        except Exception:
            # Assume it doesn't have the column
            return False
    
    def set_interval(self, interval: float) -> None:
        """
        Change the poll interval.
        
        Takes effect on the next poll cycle.
        """
        self._interval = max(1.0, interval)  # Minimum 1 second
        logger.debug(f"Poll interval set to {self._interval}s")

