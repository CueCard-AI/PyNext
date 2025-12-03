"""
PyNext Live Query - Subscription Manager.

Server-side management of active live query subscriptions.

Responsibilities:
- Track active subscriptions
- Deduplicate identical queries
- Route changes to subscribers
- Clean up on disconnect
- Batch updates for efficiency

Architecture:
    Client → Subscription → QueryGroup → ChangeDetector
    
    Multiple clients with the same query share a QueryGroup.
    Changes flow: Database → Detector → QueryGroup → Subscriptions → Clients
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    TYPE_CHECKING,
)

from pynext.db.live.config import (
    QuerySignature,
    LiveQueryConfig,
    DEFAULT_CONFIG,
    get_server_config,
)
from pynext.db.live.detection.base import ChangeEvent, ChangeCallback

if TYPE_CHECKING:
    from pynext.db.live.detection import ChangeDetector

logger = logging.getLogger(__name__)


@dataclass
class Subscription:
    """
    A single live query subscription.
    
    Represents one client's subscription to one query.
    """
    id: str
    client_id: str
    query_signature: QuerySignature
    callback: ChangeCallback
    config: LiveQueryConfig
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_update: Optional[datetime] = None
    update_count: int = 0
    
    def on_change(self, event: ChangeEvent) -> None:
        """Handle a change event."""
        self.last_update = datetime.utcnow()
        self.update_count += 1
        
        try:
            self.callback(event)
        except Exception as e:
            logger.warning(f"Subscription callback error: {e}")


@dataclass
class QueryGroup:
    """
    A group of subscriptions to the same query.
    
    Multiple clients can subscribe to the same query.
    They share a single database listener but each gets their own callback.
    """
    signature: QuerySignature
    subscriptions: Dict[str, Subscription] = field(default_factory=dict)
    detector_subscription_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def subscription_count(self) -> int:
        return len(self.subscriptions)
    
    @property
    def is_empty(self) -> bool:
        return len(self.subscriptions) == 0
    
    def add_subscription(self, subscription: Subscription) -> None:
        """Add a subscription to this group."""
        self.subscriptions[subscription.id] = subscription
    
    def remove_subscription(self, subscription_id: str) -> Optional[Subscription]:
        """Remove a subscription from this group."""
        return self.subscriptions.pop(subscription_id, None)
    
    def on_change(self, event: ChangeEvent) -> None:
        """Route a change event to all subscriptions."""
        for subscription in self.subscriptions.values():
            # Check if this change affects the query
            if event.affects_query(self.signature):
                subscription.on_change(event)


class ClientSubscription:
    """
    Tracks all subscriptions for a single client.
    
    Used for cleanup when client disconnects.
    """
    
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.subscription_ids: Set[str] = set()
        self.created_at = datetime.utcnow()
    
    def add(self, subscription_id: str) -> None:
        self.subscription_ids.add(subscription_id)
    
    def remove(self, subscription_id: str) -> None:
        self.subscription_ids.discard(subscription_id)
    
    @property
    def count(self) -> int:
        return len(self.subscription_ids)


class SubscriptionManager:
    """
    Manages all live query subscriptions.
    
    This is a singleton - use get_subscription_manager() to access.
    
    Features:
    - Query deduplication (same query = shared listener)
    - Efficient change routing
    - Client-based cleanup
    - Memory limits
    """
    
    def __init__(self):
        # Subscription ID -> Subscription
        self._subscriptions: Dict[str, Subscription] = {}
        
        # Query signature hash -> QueryGroup
        self._query_groups: Dict[int, QueryGroup] = {}
        
        # Client ID -> ClientSubscription
        self._client_subscriptions: Dict[str, ClientSubscription] = {}
        
        # Table -> QueryGroups subscribed to it
        self._table_groups: Dict[str, Set[int]] = {}
        
        # Detector reference
        self._detector: Optional["ChangeDetector"] = None
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
    
    async def subscribe(
        self,
        query_signature: QuerySignature,
        callback: ChangeCallback,
        config: Optional[LiveQueryConfig] = None,
        client_id: Optional[str] = None,
    ) -> str:
        """
        Subscribe to changes for a query.
        
        Args:
            query_signature: The query to subscribe to
            callback: Function to call on changes
            config: Optional configuration
            client_id: Optional client ID for tracking
        
        Returns:
            Subscription ID
        """
        async with self._lock:
            config = config or DEFAULT_CONFIG
            subscription_id = f"sub_{uuid.uuid4().hex[:12]}"
            client_id = client_id or f"anonymous_{uuid.uuid4().hex[:8]}"
            
            # Check limits
            server_config = get_server_config()
            client_sub = self._client_subscriptions.get(client_id)
            if client_sub and client_sub.count >= server_config.max_subscriptions_per_client:
                raise RuntimeError(
                    f"Max subscriptions ({server_config.max_subscriptions_per_client}) "
                    f"reached for client {client_id}"
                )
            
            # Create subscription
            subscription = Subscription(
                id=subscription_id,
                client_id=client_id,
                query_signature=query_signature,
                callback=callback,
                config=config,
            )
            
            # Get or create query group
            sig_hash = hash(query_signature)
            query_group = self._query_groups.get(sig_hash)
            
            if query_group is None:
                # New query group
                query_group = QueryGroup(signature=query_signature)
                self._query_groups[sig_hash] = query_group
                
                # Start listening for changes on this table
                await self._subscribe_to_table(query_signature.table, query_group)
            
            # Add subscription to group
            query_group.add_subscription(subscription)
            
            # Track
            self._subscriptions[subscription_id] = subscription
            
            # Track client subscriptions
            if client_id not in self._client_subscriptions:
                self._client_subscriptions[client_id] = ClientSubscription(client_id)
            self._client_subscriptions[client_id].add(subscription_id)
            
            logger.debug(
                f"Subscription created: {subscription_id} for {query_signature.table}"
            )
            
            return subscription_id
    
    async def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from changes.
        
        Returns:
            True if unsubscribed, False if not found
        """
        async with self._lock:
            subscription = self._subscriptions.pop(subscription_id, None)
            if not subscription:
                return False
            
            # Remove from query group
            sig_hash = hash(subscription.query_signature)
            query_group = self._query_groups.get(sig_hash)
            
            if query_group:
                query_group.remove_subscription(subscription_id)
                
                # If group is empty, clean up
                if query_group.is_empty:
                    await self._unsubscribe_from_table(
                        subscription.query_signature.table,
                        query_group,
                    )
                    del self._query_groups[sig_hash]
            
            # Remove from client tracking
            client_sub = self._client_subscriptions.get(subscription.client_id)
            if client_sub:
                client_sub.remove(subscription_id)
                if client_sub.count == 0:
                    del self._client_subscriptions[subscription.client_id]
            
            logger.debug(f"Subscription removed: {subscription_id}")
            
            return True
    
    async def unsubscribe_client(self, client_id: str) -> int:
        """
        Unsubscribe all subscriptions for a client.
        
        Returns:
            Number of subscriptions removed
        """
        client_sub = self._client_subscriptions.get(client_id)
        if not client_sub:
            return 0
        
        count = 0
        for subscription_id in list(client_sub.subscription_ids):
            if await self.unsubscribe(subscription_id):
                count += 1
        
        return count
    
    async def _subscribe_to_table(
        self,
        table: str,
        query_group: QueryGroup,
    ) -> None:
        """Start listening for changes on a table."""
        from pynext.db.live.detection import get_detector_registry
        
        # Get detector for this table
        registry = get_detector_registry()
        detector = await registry.get_detector(table)
        
        # Subscribe to table changes
        sub_id = await detector.subscribe(
            table,
            query_group.on_change,
        )
        query_group.detector_subscription_id = sub_id
        
        # Track
        if table not in self._table_groups:
            self._table_groups[table] = set()
        self._table_groups[table].add(hash(query_group.signature))
    
    async def _unsubscribe_from_table(
        self,
        table: str,
        query_group: QueryGroup,
    ) -> None:
        """Stop listening for changes on a table."""
        from pynext.db.live.detection import get_detector_registry
        
        # Unsubscribe from detector
        if query_group.detector_subscription_id:
            registry = get_detector_registry()
            detector = await registry.get_detector(table)
            await detector.unsubscribe(query_group.detector_subscription_id)
        
        # Untrack
        if table in self._table_groups:
            sig_hash = hash(query_group.signature)
            self._table_groups[table].discard(sig_hash)
            if not self._table_groups[table]:
                del self._table_groups[table]
    
    def get_subscription(self, subscription_id: str) -> Optional[Subscription]:
        """Get a subscription by ID."""
        return self._subscriptions.get(subscription_id)
    
    def get_client_subscriptions(self, client_id: str) -> List[Subscription]:
        """Get all subscriptions for a client."""
        client_sub = self._client_subscriptions.get(client_id)
        if not client_sub:
            return []
        
        return [
            self._subscriptions[sub_id]
            for sub_id in client_sub.subscription_ids
            if sub_id in self._subscriptions
        ]
    
    def get_table_subscription_count(self, table: str) -> int:
        """Get number of subscriptions for a table."""
        sig_hashes = self._table_groups.get(table, set())
        count = 0
        for sig_hash in sig_hashes:
            group = self._query_groups.get(sig_hash)
            if group:
                count += group.subscription_count
        return count
    
    @property
    def subscription_count(self) -> int:
        """Total number of active subscriptions."""
        return len(self._subscriptions)
    
    @property
    def client_count(self) -> int:
        """Number of clients with subscriptions."""
        return len(self._client_subscriptions)
    
    @property
    def query_group_count(self) -> int:
        """Number of unique query groups."""
        return len(self._query_groups)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get subscription statistics."""
        return {
            "subscriptions": self.subscription_count,
            "clients": self.client_count,
            "query_groups": self.query_group_count,
            "tables": list(self._table_groups.keys()),
        }
    
    async def notify_change(self, event: ChangeEvent) -> int:
        """
        Notify subscriptions about a change event.
        
        Routes the change to all query groups subscribed to the table.
        
        Args:
            event: The change event to notify about
            
        Returns:
            Number of subscriptions notified
        """
        table = event.table
        sig_hashes = self._table_groups.get(table, set())
        
        notified = 0
        for sig_hash in sig_hashes:
            query_group = self._query_groups.get(sig_hash)
            if query_group:
                # Check if this event affects this query
                if event.affects_query(query_group.signature):
                    query_group.on_change(event)
                    notified += query_group.subscription_count
        
        return notified


# Global subscription manager
_manager: Optional[SubscriptionManager] = None


def get_subscription_manager() -> SubscriptionManager:
    """Get the global subscription manager."""
    global _manager
    if _manager is None:
        _manager = SubscriptionManager()
    return _manager


async def reset_subscription_manager() -> None:
    """Reset the subscription manager. Mainly for testing."""
    global _manager
    if _manager:
        # Unsubscribe all
        for sub_id in list(_manager._subscriptions.keys()):
            await _manager.unsubscribe(sub_id)
    _manager = None

