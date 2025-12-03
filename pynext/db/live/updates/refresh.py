"""
PyNext Live Query - Full Refresh Strategy.

Re-runs the entire query to get fresh results.

Full refresh is:
- Always accurate: Gets exact current state
- Slower: Requires database query
- Higher load: Full query execution

Best for:
- Complex queries with filters
- Ordered queries (changes may affect order)
- Limited queries (changes may affect which items included)
- Aggregation queries
- When surgical update fails
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Type, TYPE_CHECKING

from pynext.db.live.updates.base import UpdateStrategy, UpdateResult
from pynext.db.live.detection.base import ChangeEvent

if TYPE_CHECKING:
    from pynext.db.table import Table
    from pynext.db.live.config import QuerySignature

T = type


class FullRefresh(UpdateStrategy):
    """
    Full refresh update strategy.
    
    Re-executes the query to get current results.
    
    This is the fallback strategy when surgical updates aren't possible.
    It's always accurate but slower.
    """
    
    def __init__(self, query_executor: callable = None):
        """
        Create a full refresh strategy.
        
        Args:
            query_executor: Async function to execute the query.
                           Should return List[T].
        """
        self._query_executor = query_executor
    
    @property
    def name(self) -> str:
        return "FullRefresh"
    
    def apply(
        self,
        current_data: List,
        current_by_id: Dict[int, Any],
        event: ChangeEvent,
        model: Type,
    ) -> UpdateResult:
        """
        Apply a full refresh.
        
        Note: This is a synchronous stub. The actual refresh is async
        and triggered separately by the LiveQuery.
        
        Returns a "needs refresh" signal.
        """
        # Signal that a refresh is needed
        # The actual refresh happens async in LiveQuery
        return UpdateResult(
            changed=True,
            data=current_data,  # Keep current until refresh completes
            data_by_id=current_by_id,
            added=[],
            updated=[],
            removed=[],
        )
    
    async def apply_async(
        self,
        current_data: List,
        current_by_id: Dict[int, Any],
        event: ChangeEvent,
        model: Type,
    ) -> UpdateResult:
        """
        Apply a full refresh asynchronously.
        
        This actually executes the query and returns new data.
        """
        if not self._query_executor:
            return UpdateResult.no_change(current_data, current_by_id)
        
        try:
            # Execute the query
            new_data = await self._query_executor()
            
            # Build lookup dict
            new_by_id = {
                r.id: r for r in new_data
                if hasattr(r, "id")
            }
            
            # Determine what changed
            old_ids = set(current_by_id.keys())
            new_ids = set(new_by_id.keys())
            
            added = list(new_ids - old_ids)
            removed = list(old_ids - new_ids)
            
            # Check for updates (same id, different data)
            updated = []
            for row_id in old_ids & new_ids:
                old_row = current_by_id[row_id]
                new_row = new_by_id[row_id]
                
                # Compare by updated_at if available, otherwise by dict
                if hasattr(old_row, "updated_at") and hasattr(new_row, "updated_at"):
                    if old_row.updated_at != new_row.updated_at:
                        updated.append(row_id)
                elif hasattr(old_row, "_to_dict") and hasattr(new_row, "_to_dict"):
                    if old_row._to_dict() != new_row._to_dict():
                        updated.append(row_id)
            
            changed = bool(added or removed or updated)
            
            return UpdateResult(
                changed=changed,
                data=new_data,
                data_by_id=new_by_id,
                added=added,
                updated=updated,
                removed=removed,
            )
            
        except Exception as e:
            # On error, keep current data
            return UpdateResult.no_change(current_data, current_by_id)
    
    def can_apply(
        self,
        event: ChangeEvent,
        signature: "QuerySignature",
    ) -> bool:
        """Full refresh can always be applied."""
        return True


class RefreshDebouncer:
    """
    Debounces multiple refresh requests.
    
    When many changes happen quickly, we don't want to run the query
    for each one. This debouncer waits for a quiet period before
    actually executing.
    """
    
    def __init__(self, delay_ms: int = 100):
        """
        Create a debouncer.
        
        Args:
            delay_ms: Wait this long after last change before refresh
        """
        self._delay_ms = delay_ms
        self._pending_task: Dict[str, asyncio.Task] = {}
        self._callbacks: Dict[str, callable] = {}
    
    async def request_refresh(
        self,
        query_id: str,
        callback: callable,
    ) -> None:
        """
        Request a refresh for a query.
        
        If another refresh is pending, cancels it and starts a new timer.
        """
        # Cancel existing pending refresh
        existing = self._pending_task.get(query_id)
        if existing:
            existing.cancel()
            try:
                await existing
            except asyncio.CancelledError:
                pass
        
        # Store callback
        self._callbacks[query_id] = callback
        
        # Start new timer
        self._pending_task[query_id] = asyncio.create_task(
            self._delayed_refresh(query_id)
        )
    
    async def _delayed_refresh(self, query_id: str) -> None:
        """Wait and then execute refresh."""
        try:
            await asyncio.sleep(self._delay_ms / 1000)
            
            callback = self._callbacks.pop(query_id, None)
            self._pending_task.pop(query_id, None)
            
            if callback:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
                    
        except asyncio.CancelledError:
            pass
    
    def cancel(self, query_id: str) -> None:
        """Cancel a pending refresh."""
        task = self._pending_task.pop(query_id, None)
        if task:
            task.cancel()
        self._callbacks.pop(query_id, None)
    
    def cancel_all(self) -> None:
        """Cancel all pending refreshes."""
        for task in self._pending_task.values():
            task.cancel()
        self._pending_task.clear()
        self._callbacks.clear()

