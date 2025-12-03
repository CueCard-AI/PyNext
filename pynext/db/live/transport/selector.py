"""
PyNext Live Query - Transport Selector.

Automatically selects the best transport for a query.

Selection Logic:
┌─────────────────────────────────────────────┐
│ Query Characteristics    │ Transport       │
├─────────────────────────┼─────────────────┤
│ Simple read, 1 table    │ SSE (simpler)   │
│ Multiple tables/joins   │ WebSocket       │
│ High-frequency updates  │ WebSocket       │
│ Already have WS open    │ Reuse WebSocket │
│ Need client messages    │ WebSocket       │
└─────────────────────────────────────────────┘
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Set, TYPE_CHECKING

from pynext.db.live.config import TransportType, QuerySignature

if TYPE_CHECKING:
    from pynext.db.live.transport.base import Transport


@dataclass
class TransportSelection:
    """Result of transport selection."""
    transport_type: TransportType
    reason: str


class TransportSelector:
    """
    Selects the optimal transport for a query.
    
    The selector considers:
    - Query complexity (filters, joins, ordering)
    - Expected update frequency
    - Client capabilities
    - Existing connections
    """
    
    # Tables with high update frequency (customize per app)
    HIGH_FREQUENCY_TABLES: Set[str] = set()
    
    def __init__(self):
        # Track active WebSocket connections
        self._active_websockets: Set[str] = set()  # client_ids
    
    def select(
        self,
        signature: QuerySignature,
        client_id: str,
        preferred: TransportType = TransportType.AUTO,
    ) -> TransportSelection:
        """
        Select the best transport for a query.
        
        Args:
            signature: The query signature
            client_id: The client making the query
            preferred: Client's preferred transport (default: AUTO)
        
        Returns:
            TransportSelection with type and reason
        """
        # If client has a preference, honor it
        if preferred != TransportType.AUTO:
            return TransportSelection(
                transport_type=preferred,
                reason=f"Client requested {preferred.value}",
            )
        
        # Check if client already has WebSocket
        if client_id in self._active_websockets:
            return TransportSelection(
                transport_type=TransportType.WEBSOCKET,
                reason="Reusing existing WebSocket connection",
            )
        
        # Check for high-frequency tables
        if signature.table in self.HIGH_FREQUENCY_TABLES:
            return TransportSelection(
                transport_type=TransportType.WEBSOCKET,
                reason=f"Table {signature.table} has high update frequency",
            )
        
        # Complex queries (joins, multiple conditions) prefer WebSocket
        if len(signature.where_clauses) > 3:
            return TransportSelection(
                transport_type=TransportType.WEBSOCKET,
                reason="Complex query with many conditions",
            )
        
        # Simple queries use SSE
        if signature.is_simple:
            return TransportSelection(
                transport_type=TransportType.SSE,
                reason="Simple query - SSE is sufficient",
            )
        
        # Default to SSE for simpler setup
        return TransportSelection(
            transport_type=TransportType.SSE,
            reason="Default transport for standard queries",
        )
    
    def register_websocket(self, client_id: str) -> None:
        """Register an active WebSocket connection."""
        self._active_websockets.add(client_id)
    
    def unregister_websocket(self, client_id: str) -> None:
        """Unregister a WebSocket connection."""
        self._active_websockets.discard(client_id)
    
    def has_websocket(self, client_id: str) -> bool:
        """Check if client has an active WebSocket."""
        return client_id in self._active_websockets
    
    def register_high_frequency_table(self, table: str) -> None:
        """Mark a table as having high update frequency."""
        self.HIGH_FREQUENCY_TABLES.add(table)
    
    def unregister_high_frequency_table(self, table: str) -> None:
        """Unmark a table as high frequency."""
        self.HIGH_FREQUENCY_TABLES.discard(table)


# Global selector instance
_selector: Optional[TransportSelector] = None


def get_transport_selector() -> TransportSelector:
    """Get the global transport selector."""
    global _selector
    if _selector is None:
        _selector = TransportSelector()
    return _selector

