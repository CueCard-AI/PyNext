"""
PyNext Live Query - Supabase Realtime Detection.

Uses Supabase's built-in Realtime feature for instant change detection.
This is the highest priority detector when using Supabase.

How It Works:
1. Connects to Supabase Realtime using the existing integration
2. Subscribes to table changes via postgres_changes
3. Routes changes to live query subscribers

This integrates with Phase 5.6's Supabase Realtime module.

Usage:
    detector = SupabaseRealtimeDetector()
    await detector.start()
    
    sub_id = await detector.subscribe("users", lambda event: print(event))
    
    await detector.unsubscribe(sub_id)
    await detector.stop()
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional, Set, TYPE_CHECKING

from pynext.db.live.detection.base import (
    ChangeDetector,
    ChangeEvent,
    ChangeType,
    ChangeCallback,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class SupabaseRealtimeDetector(ChangeDetector):
    """
    Change detector using Supabase Realtime.
    
    This is the preferred detection method when using Supabase:
    - Instant notifications
    - No trigger setup required
    - Built-in RLS support
    - Works through Supabase's managed infrastructure
    
    Requirements:
    - Supabase project
    - Table must have Realtime enabled
    - pynext.db.supabase configured
    """
    
    def __init__(self, supabase_client: Optional[Any] = None):
        """
        Create a Supabase Realtime detector.
        
        Args:
            supabase_client: Optional Supabase client. If not provided,
                            uses the global Supabase adapter.
        """
        super().__init__()
        self._client = supabase_client
        self._channels: Dict[str, Any] = {}  # table -> channel
        self._event_handlers: Dict[str, Any] = {}  # table -> handler
    
    @property
    def name(self) -> str:
        return "Supabase Realtime"
    
    @property
    def priority(self) -> int:
        return 100  # Highest priority
    
    async def is_available(self) -> bool:
        """Check if Supabase Realtime is available."""
        try:
            client = await self._get_client()
            if client is None:
                return False
            
            # Check that realtime is accessible
            # This is a lightweight check
            return hasattr(client, "realtime") or hasattr(client, "channel")
            
        except Exception as e:
            logger.debug(f"Supabase Realtime not available: {e}")
            return False
    
    async def start(self) -> None:
        """Start the Supabase Realtime connection."""
        if self._running:
            return
        
        self._client = await self._get_client()
        if self._client is None:
            raise RuntimeError("Supabase client not available")
        
        self._running = True
        logger.info("Supabase Realtime detector started")
    
    async def stop(self) -> None:
        """Stop and clean up Supabase Realtime subscriptions."""
        self._running = False
        
        # Unsubscribe from all channels
        for table, channel in list(self._channels.items()):
            try:
                await self._unsubscribe_channel(channel)
            except Exception as e:
                logger.warning(f"Error unsubscribing from {table}: {e}")
        
        self._channels.clear()
        self._event_handlers.clear()
        
        logger.info("Supabase Realtime detector stopped")
    
    async def subscribe_table(self, table: str) -> None:
        """Start listening for changes on a table via Supabase Realtime."""
        if table in self._channels:
            return
        
        if self._client is None:
            raise RuntimeError("Detector not started")
        
        try:
            # Create a channel for this table
            channel = self._client.channel(f"live_{table}")
            
            # Handler for postgres changes
            def on_change(payload: Dict[str, Any]) -> None:
                self._handle_change(table, payload)
            
            # Subscribe to all change types
            channel.on_postgres_changes(
                event="*",
                schema="public",
                table=table,
                callback=on_change,
            )
            
            # Connect the channel
            await channel.subscribe()
            
            self._channels[table] = channel
            self._event_handlers[table] = on_change
            
            logger.debug(f"Subscribed to Supabase Realtime: {table}")
            
        except Exception as e:
            logger.error(f"Failed to subscribe to {table}: {e}")
            raise
    
    async def unsubscribe_table(self, table: str) -> None:
        """Stop listening for changes on a table."""
        channel = self._channels.pop(table, None)
        self._event_handlers.pop(table, None)
        
        if channel:
            await self._unsubscribe_channel(channel)
            logger.debug(f"Unsubscribed from Supabase Realtime: {table}")
    
    def _handle_change(self, table: str, payload: Dict[str, Any]) -> None:
        """Handle a Supabase Realtime change event."""
        try:
            # Map Supabase event types to our ChangeType
            event_type = payload.get("eventType", "").upper()
            change_type = ChangeType.UNKNOWN
            
            if event_type == "INSERT":
                change_type = ChangeType.INSERT
            elif event_type == "UPDATE":
                change_type = ChangeType.UPDATE
            elif event_type == "DELETE":
                change_type = ChangeType.DELETE
            
            # Extract row data
            new_data = payload.get("new")
            old_data = payload.get("old")
            
            # Get row ID
            row_id = None
            if new_data and "id" in new_data:
                row_id = new_data["id"]
            elif old_data and "id" in old_data:
                row_id = old_data["id"]
            
            # Determine changed columns for updates
            columns_changed = []
            if change_type == ChangeType.UPDATE and old_data and new_data:
                for key in set(old_data.keys()) | set(new_data.keys()):
                    old_val = old_data.get(key)
                    new_val = new_data.get(key)
                    if old_val != new_val:
                        columns_changed.append(key)
            
            # Create change event
            event = ChangeEvent(
                table=table,
                type=change_type,
                row_id=row_id,
                old_data=old_data,
                new_data=new_data,
                timestamp=datetime.utcnow(),
                source="supabase_realtime",
                columns_changed=columns_changed,
            )
            
            # Notify subscribers
            self._notify_subscribers(event)
            
        except Exception as e:
            logger.error(f"Error handling Supabase change: {e}")
    
    async def _get_client(self) -> Optional[Any]:
        """Get the Supabase client."""
        if self._client:
            return self._client
        
        try:
            # Try to get from the Supabase adapter
            from pynext.db.supabase import Supabase
            return Supabase._client
        except Exception:
            pass
        
        try:
            # Try to get from environment
            import os
            from supabase import create_client
            
            url = os.environ.get("SUPABASE_URL")
            key = os.environ.get("SUPABASE_KEY")
            
            if url and key:
                return create_client(url, key)
        except Exception:
            pass
        
        return None
    
    async def _unsubscribe_channel(self, channel: Any) -> None:
        """Unsubscribe and close a channel."""
        try:
            if hasattr(channel, "unsubscribe"):
                await channel.unsubscribe()
            elif hasattr(channel, "remove"):
                channel.remove()
        except Exception as e:
            logger.warning(f"Error closing channel: {e}")

