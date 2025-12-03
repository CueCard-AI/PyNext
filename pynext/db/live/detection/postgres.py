"""
PyNext Live Query - PostgreSQL LISTEN/NOTIFY Detection.

Uses PostgreSQL's native LISTEN/NOTIFY mechanism for instant change detection.
This is the preferred method when using PostgreSQL directly (not Supabase).

How It Works:
1. Creates triggers on watched tables
2. Triggers send NOTIFY on INSERT/UPDATE/DELETE
3. PyNext listens for notifications and routes to subscribers

The triggers send JSON payloads with:
- Operation type (INSERT/UPDATE/DELETE)
- Row ID
- Changed columns (for UPDATE)
- Old and new row data

Usage:
    detector = PostgresNotifyDetector()
    await detector.start()
    
    # Subscribe to table changes
    sub_id = await detector.subscribe("users", lambda event: print(event))
    
    # Later
    await detector.unsubscribe(sub_id)
    await detector.stop()
"""

from __future__ import annotations

import asyncio
import json
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


class PostgresNotifyDetector(ChangeDetector):
    """
    Change detector using PostgreSQL LISTEN/NOTIFY.
    
    This is the fastest detection method for PostgreSQL:
    - No polling delay
    - Near-instant notifications
    - Low overhead
    
    Requirements:
    - PostgreSQL database
    - asyncpg connection with listen capability
    - PyNext's trigger installed on watched tables
    """
    
    CHANNEL_PREFIX = "pynext_live_"
    
    def __init__(self, connection: Optional[Any] = None):
        """
        Create a PostgreSQL NOTIFY detector.
        
        Args:
            connection: Optional asyncpg connection. If not provided,
                       uses the global adapter's connection.
        """
        super().__init__()
        self._connection = connection
        self._listen_connection = None
        self._listener_task: Optional[asyncio.Task] = None
        self._channels: Set[str] = set()
    
    @property
    def name(self) -> str:
        return "PostgreSQL LISTEN/NOTIFY"
    
    @property
    def priority(self) -> int:
        return 50  # Medium priority (Supabase RT is higher)
    
    async def is_available(self) -> bool:
        """Check if PostgreSQL is available and supports NOTIFY."""
        try:
            from pynext.db.table import get_adapter
            adapter = get_adapter()
            
            # Use adapter's clean API
            if hasattr(adapter, "supports_listen_notify"):
                return adapter.supports_listen_notify()
            
            # Fallback: try to get a connection
            conn = await self._get_connection()
            if conn is None:
                return False
            
            # Test that NOTIFY works
            await conn.execute("SELECT 1")
            return True
            
        except Exception as e:
            logger.debug(f"PostgreSQL NOTIFY not available: {e}")
            return False
    
    async def start(self) -> None:
        """Start listening for notifications."""
        if self._running:
            return
        
        self._listen_connection = await self._get_listen_connection()
        if self._listen_connection is None:
            raise RuntimeError("Could not get PostgreSQL connection for LISTEN")
        
        self._running = True
        logger.info("PostgreSQL NOTIFY detector started")
    
    async def stop(self) -> None:
        """Stop listening and clean up."""
        self._running = False
        
        # Cancel listener task
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
            self._listener_task = None
        
        # Unlisten from all channels
        if self._listen_connection:
            for channel in list(self._channels):
                try:
                    await self._listen_connection.execute(f"UNLISTEN {channel}")
                except Exception:
                    pass
            self._channels.clear()
        
        # Close dedicated listen connection
        if self._listen_connection:
            try:
                await self._listen_connection.close()
            except Exception:
                pass
            self._listen_connection = None
        
        logger.info("PostgreSQL NOTIFY detector stopped")
    
    async def subscribe_table(self, table: str) -> None:
        """Start listening for changes on a table."""
        channel = self._get_channel_name(table)
        
        if channel in self._channels:
            return
        
        conn = self._listen_connection
        if conn is None:
            raise RuntimeError("Detector not started")
        
        # Ensure trigger exists
        await self._ensure_trigger(table)
        
        # Start listening
        await conn.add_listener(channel, self._on_notification)
        self._channels.add(channel)
        
        logger.debug(f"Listening on channel: {channel}")
    
    async def unsubscribe_table(self, table: str) -> None:
        """Stop listening for changes on a table."""
        channel = self._get_channel_name(table)
        
        if channel not in self._channels:
            return
        
        conn = self._listen_connection
        if conn:
            await conn.remove_listener(channel, self._on_notification)
            self._channels.discard(channel)
        
        logger.debug(f"Stopped listening on channel: {channel}")
    
    def _on_notification(
        self,
        connection: Any,
        pid: int,
        channel: str,
        payload: str,
    ) -> None:
        """Handle a NOTIFY payload."""
        try:
            # Parse the JSON payload
            data = json.loads(payload)
            
            # Extract table name from channel
            table = channel.replace(self.CHANNEL_PREFIX, "")
            
            # Create change event
            event = ChangeEvent(
                table=table,
                type=ChangeType(data.get("operation", "UNKNOWN")),
                row_id=data.get("id"),
                old_data=data.get("old"),
                new_data=data.get("new"),
                timestamp=datetime.utcnow(),
                source="postgres_notify",
                columns_changed=data.get("changed_columns", []),
            )
            
            # Notify subscribers
            self._notify_subscribers(event)
            
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid NOTIFY payload: {payload[:100]}... - {e}")
        except Exception as e:
            logger.error(f"Error handling NOTIFY: {e}")
    
    def _get_channel_name(self, table: str) -> str:
        """Get the NOTIFY channel name for a table."""
        return f"{self.CHANNEL_PREFIX}{table}"
    
    async def _get_connection(self) -> Optional[Any]:
        """Get a database connection for regular queries."""
        if self._connection:
            return self._connection
        
        try:
            from pynext.db.table import get_adapter
            adapter = get_adapter()
            
            # Use adapter's connection context manager if available
            if hasattr(adapter, "connection"):
                # For one-off queries, we'll acquire from pool
                if hasattr(adapter, "_pool") and adapter._pool:
                    return await adapter._pool.acquire()
            
            return None
        except Exception:
            return None
    
    async def _get_listen_connection(self) -> Optional[Any]:
        """
        Get a dedicated connection for LISTEN.
        
        LISTEN requires a persistent connection that isn't returned to the pool.
        Uses adapter's clean API when available.
        """
        try:
            from pynext.db.table import get_adapter
            adapter = get_adapter()
            
            # Use adapter's dedicated method (clean API)
            if hasattr(adapter, "get_listen_connection"):
                return await adapter.get_listen_connection()
            
            # Fallback: create connection directly from config
            if hasattr(adapter, "_config"):
                import asyncpg
                
                conn = await asyncpg.connect(
                    host=adapter._config.host,
                    port=adapter._config.port,
                    user=adapter._config.user,
                    password=adapter._config.password,
                    database=adapter._config.database,
                )
                return conn
            
            return None
        except Exception as e:
            logger.error(f"Could not create listen connection: {e}")
            return None
    
    async def _ensure_trigger(self, table: str) -> None:
        """
        Ensure the NOTIFY trigger exists on a table.
        
        Creates trigger if auto_create_triggers is enabled.
        Uses adapter's clean API for trigger management.
        """
        from pynext.db.live.config import get_server_config
        from pynext.db.table import get_adapter
        
        config = get_server_config()
        if not config.auto_create_triggers:
            return
        
        channel = self._get_channel_name(table)
        trigger_name = f"{channel}_trigger"
        function_name = f"{channel}_notify"
        
        try:
            adapter = get_adapter()
            
            # Check if trigger already exists (using clean API if available)
            if hasattr(adapter, "check_trigger_exists"):
                if await adapter.check_trigger_exists(table, trigger_name):
                    logger.debug(f"Trigger already exists for table: {table}")
                    return
            
            # Create trigger function SQL
            function_sql = f"""
            CREATE OR REPLACE FUNCTION {function_name}()
            RETURNS trigger AS $$
            DECLARE
                payload JSON;
                changed_cols TEXT[];
            BEGIN
                IF TG_OP = 'INSERT' THEN
                    payload = json_build_object(
                        'operation', TG_OP,
                        'id', NEW.id,
                        'new', row_to_json(NEW)
                    );
                ELSIF TG_OP = 'UPDATE' THEN
                    -- Get changed columns
                    SELECT array_agg(key)
                    INTO changed_cols
                    FROM (
                        SELECT key
                        FROM jsonb_each(to_jsonb(NEW)) new_val
                        FULL OUTER JOIN (
                            SELECT key, value
                            FROM jsonb_each(to_jsonb(OLD))
                        ) old_val USING (key)
                        WHERE new_val.value IS DISTINCT FROM old_val.value
                    ) changed;
                    
                    payload = json_build_object(
                        'operation', TG_OP,
                        'id', NEW.id,
                        'old', row_to_json(OLD),
                        'new', row_to_json(NEW),
                        'changed_columns', changed_cols
                    );
                ELSIF TG_OP = 'DELETE' THEN
                    payload = json_build_object(
                        'operation', TG_OP,
                        'id', OLD.id,
                        'old', row_to_json(OLD)
                    );
                END IF;
                
                PERFORM pg_notify('{channel}', payload::text);
                RETURN NULL;
            END;
            $$ LANGUAGE plpgsql;
            """
            
            # Create trigger SQL
            trigger_sql = f"""
            DROP TRIGGER IF EXISTS {trigger_name} ON {table};
            CREATE TRIGGER {trigger_name}
            AFTER INSERT OR UPDATE OR DELETE ON {table}
            FOR EACH ROW EXECUTE FUNCTION {function_name}();
            """
            
            # Execute using adapter's clean API if available (includes retry!)
            if hasattr(adapter, "execute_trigger_sql"):
                await adapter.execute_trigger_sql(function_sql)
                await adapter.execute_trigger_sql(trigger_sql)
            else:
                # Fallback: execute directly
                conn = await self._get_connection()
                if conn is None:
                    return
                try:
                    await conn.execute(function_sql)
                    await conn.execute(trigger_sql)
                finally:
                    if hasattr(conn, "close") and self._connection is None:
                        await conn.close()
            
            logger.info(f"Created NOTIFY trigger for table: {table}")
            
        except Exception as e:
            logger.warning(f"Could not create trigger for {table}: {e}")

