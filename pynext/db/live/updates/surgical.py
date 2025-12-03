"""
PyNext Live Query - Surgical Update Strategy.

Efficiently adds, updates, or removes individual items from query results
without re-running the entire query.

Surgical updates are:
- Fast: O(1) for lookups, O(n) for insert in correct position
- Efficient: No database query needed
- Accurate: For simple queries without complex filters

Best for:
- Simple queries (User.live())
- Unfiltered queries
- Queries without ordering/limits

Not suitable for:
- Complex WHERE clauses (need to re-evaluate)
- LIMIT queries (may change which items are included)
- Aggregations
"""

from __future__ import annotations

from typing import Any, Dict, List, Type, TYPE_CHECKING

from pynext.db.live.updates.base import UpdateStrategy, UpdateResult
from pynext.db.live.detection.base import ChangeEvent, ChangeType

if TYPE_CHECKING:
    from pynext.db.table import Table
    from pynext.db.live.config import QuerySignature

T = type


class SurgicalUpdate(UpdateStrategy):
    """
    Surgical update strategy.
    
    Applies changes directly to the in-memory result list:
    - INSERT: Add new row to list
    - UPDATE: Replace existing row
    - DELETE: Remove row from list
    """
    
    @property
    def name(self) -> str:
        return "Surgical"
    
    def apply(
        self,
        current_data: List,
        current_by_id: Dict[int, Any],
        event: ChangeEvent,
        model: Type,
    ) -> UpdateResult:
        """Apply a surgical update."""
        if event.type == ChangeType.INSERT:
            return self._apply_insert(current_data, current_by_id, event, model)
        elif event.type == ChangeType.UPDATE:
            return self._apply_update(current_data, current_by_id, event, model)
        elif event.type == ChangeType.DELETE:
            return self._apply_delete(current_data, current_by_id, event, model)
        else:
            # Unknown change type, no change
            return UpdateResult.no_change(current_data, current_by_id)
    
    def _apply_insert(
        self,
        current_data: List,
        current_by_id: Dict[int, Any],
        event: ChangeEvent,
        model: Type,
    ) -> UpdateResult:
        """Handle INSERT by adding new row."""
        if not event.new_data:
            return UpdateResult.no_change(current_data, current_by_id)
        
        row_id = event.row_id or event.new_data.get("id")
        if row_id is None:
            return UpdateResult.no_change(current_data, current_by_id)
        
        # Skip if already exists
        if row_id in current_by_id:
            return UpdateResult.no_change(current_data, current_by_id)
        
        # Create new model instance
        new_row = model._from_row(event.new_data)
        
        # Add to list
        new_data = current_data + [new_row]
        new_by_id = {**current_by_id, row_id: new_row}
        
        return UpdateResult(
            changed=True,
            data=new_data,
            data_by_id=new_by_id,
            added=[row_id],
        )
    
    def _apply_update(
        self,
        current_data: List,
        current_by_id: Dict[int, Any],
        event: ChangeEvent,
        model: Type,
    ) -> UpdateResult:
        """Handle UPDATE by replacing existing row."""
        if not event.new_data:
            return UpdateResult.no_change(current_data, current_by_id)
        
        row_id = event.row_id or event.new_data.get("id")
        if row_id is None:
            return UpdateResult.no_change(current_data, current_by_id)
        
        # Skip if not in current results
        if row_id not in current_by_id:
            return UpdateResult.no_change(current_data, current_by_id)
        
        # Create updated model instance
        updated_row = model._from_row(event.new_data)
        
        # Replace in list
        new_data = [
            updated_row if (hasattr(r, "id") and r.id == row_id) else r
            for r in current_data
        ]
        new_by_id = {**current_by_id, row_id: updated_row}
        
        return UpdateResult(
            changed=True,
            data=new_data,
            data_by_id=new_by_id,
            updated=[row_id],
        )
    
    def _apply_delete(
        self,
        current_data: List,
        current_by_id: Dict[int, Any],
        event: ChangeEvent,
        model: Type,
    ) -> UpdateResult:
        """Handle DELETE by removing row."""
        row_id = event.row_id
        if row_id is None and event.old_data:
            row_id = event.old_data.get("id")
        
        if row_id is None:
            return UpdateResult.no_change(current_data, current_by_id)
        
        # Skip if not in current results
        if row_id not in current_by_id:
            return UpdateResult.no_change(current_data, current_by_id)
        
        # Remove from list
        new_data = [
            r for r in current_data
            if not (hasattr(r, "id") and r.id == row_id)
        ]
        new_by_id = {k: v for k, v in current_by_id.items() if k != row_id}
        
        return UpdateResult(
            changed=True,
            data=new_data,
            data_by_id=new_by_id,
            removed=[row_id],
        )
    
    def can_apply(
        self,
        event: ChangeEvent,
        signature: "QuerySignature",
    ) -> bool:
        """
        Check if surgical update is appropriate for this event.
        
        Surgical updates work well for:
        - Simple queries without filters
        - INSERTs (always can add)
        - DELETEs when row is in results
        - UPDATEs that don't affect filter criteria
        """
        # Always works for simple queries
        if signature.is_simple:
            return True
        
        # For INSERT, need to evaluate filters to know if it matches
        if event.type == ChangeType.INSERT:
            # Can't surgically add without evaluating filters
            return not signature.has_filters
        
        # For UPDATE, check if changed columns affect filters
        if event.type == ChangeType.UPDATE and event.columns_changed:
            # Get filter fields
            filter_fields = set()
            for clause in signature.where_clauses:
                for key in clause:
                    field_name = key.split("__")[0]
                    filter_fields.add(field_name)
            
            # If ordering field changed, need to re-sort
            if signature.order_by:
                order_field = signature.order_by.lstrip("-")
                if order_field in event.columns_changed:
                    return False
            
            # If filter field changed, need to re-evaluate
            if filter_fields.intersection(event.columns_changed):
                return False
            
            return True
        
        # DELETE is always surgical if row is in results
        if event.type == ChangeType.DELETE:
            return True
        
        return False

