"""
PyNext Live Query - PostgreSQL Trigger Management.

Manages NOTIFY triggers for live query change detection.

Triggers are automatically created when:
1. A table is first subscribed to
2. auto_create_triggers is enabled in config

The triggers send NOTIFY events with JSON payloads containing:
- Operation type (INSERT/UPDATE/DELETE)
- Row ID
- Old and new row data
- Changed columns (for UPDATE)

Usage:
    manager = get_trigger_manager()
    
    # Create trigger for a table
    await manager.ensure_trigger("users")
    
    # Check if trigger exists
    has_trigger = await manager.has_trigger("users")
    
    # Drop trigger
    await manager.drop_trigger("users")
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Set, TYPE_CHECKING

from pynext.db.live.config import get_server_config

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass
class NotifyChannel:
    """
    Represents a NOTIFY channel for a table.
    
    Contains metadata about the trigger.
    """
    table: str
    channel: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    trigger_exists: bool = False
    function_exists: bool = False


@dataclass
class TriggerConfig:
    """
    Configuration for trigger creation.
    """
    # Channel prefix
    prefix: str = "pynext_live_"
    
    # Include old data in payload (for UPDATE/DELETE)
    include_old_data: bool = True
    
    # Include new data in payload (for INSERT/UPDATE)
    include_new_data: bool = True
    
    # Include changed columns list
    include_changed_columns: bool = True
    
    # Maximum payload size (PostgreSQL limit is ~8000 bytes)
    max_payload_size: int = 7000


class TriggerManager:
    """
    Manages PostgreSQL NOTIFY triggers for live queries.
    
    This is a singleton - use get_trigger_manager() to access.
    
    Features:
    - Auto-creates triggers when needed
    - Tracks which tables have triggers
    - Configurable payload content
    - Safe trigger replacement
    """
    
    def __init__(self, config: Optional[TriggerConfig] = None):
        self._config = config or TriggerConfig()
        self._channels: Dict[str, NotifyChannel] = {}
        self._lock = asyncio.Lock()
    
    def get_channel_name(self, table: str) -> str:
        """Get the NOTIFY channel name for a table."""
        return f"{self._config.prefix}{table}"
    
    async def ensure_trigger(
        self,
        table: str,
        connection: Optional[Any] = None,
    ) -> NotifyChannel:
        """
        Ensure a NOTIFY trigger exists for a table.
        
        Creates the trigger if it doesn't exist.
        Uses adapter's clean API when available.
        
        Args:
            table: Table name
            connection: Optional database connection
        
        Returns:
            NotifyChannel with trigger info
        """
        async with self._lock:
            channel_name = self.get_channel_name(table)
            trigger_name = f"{channel_name}_trigger"
            
            # Check cache
            if table in self._channels and self._channels[table].trigger_exists:
                return self._channels[table]
            
            # Try to use adapter's clean API first
            from pynext.db.table import get_adapter
            adapter = get_adapter()
            
            # Check if trigger already exists using adapter API
            if hasattr(adapter, "check_trigger_exists"):
                if await adapter.check_trigger_exists(table, trigger_name):
                    channel = NotifyChannel(
                        table=table,
                        channel=channel_name,
                        trigger_exists=True,
                        function_exists=True,
                    )
                    self._channels[table] = channel
                    return channel
            
            # Create trigger using adapter API if available
            if hasattr(adapter, "execute_trigger_sql"):
                # Generate SQL
                function_sql = self._generate_function_sql(table, channel_name)
                trigger_sql = self._generate_trigger_sql(table, channel_name)
                
                # Execute with retry (via adapter)
                await adapter.execute_trigger_sql(function_sql)
                await adapter.execute_trigger_sql(trigger_sql)
                
                # Cache
                channel = NotifyChannel(
                    table=table,
                    channel=channel_name,
                    trigger_exists=True,
                    function_exists=True,
                )
                self._channels[table] = channel
                
                logger.info(f"Created NOTIFY trigger for table: {table}")
                return channel
            
            # Fallback: use direct connection
            conn = connection or await self._get_connection()
            if conn is None:
                raise RuntimeError("No database connection available")
            
            try:
                # Create function and trigger
                await self._create_trigger_function(conn, table, channel_name)
                await self._create_trigger(conn, table, channel_name)
                
                # Cache
                channel = NotifyChannel(
                    table=table,
                    channel=channel_name,
                    trigger_exists=True,
                    function_exists=True,
                )
                self._channels[table] = channel
                
                logger.info(f"Created NOTIFY trigger for table: {table}")
                
                return channel
                
            finally:
                # Release connection if we acquired it
                if connection is None and hasattr(conn, "close"):
                    await conn.close()
    
    async def has_trigger(
        self,
        table: str,
        connection: Optional[Any] = None,
    ) -> bool:
        """Check if a trigger exists for a table using adapter's clean API."""
        # Check cache first
        if table in self._channels:
            return self._channels[table].trigger_exists
        
        trigger_name = f"{self.get_channel_name(table)}_trigger"
        
        # Try adapter's clean API first
        try:
            from pynext.db.table import get_adapter
            adapter = get_adapter()
            
            if hasattr(adapter, "check_trigger_exists"):
                return await adapter.check_trigger_exists(table, trigger_name)
        except Exception:
            pass
        
        # Fallback: check database directly
        conn = connection or await self._get_connection()
        if conn is None:
            return False
        
        try:
            result = await conn.fetchval(
                """
                SELECT EXISTS(
                    SELECT 1 FROM pg_trigger
                    WHERE tgname = $1
                )
                """,
                trigger_name,
            )
            
            return bool(result)
            
        except Exception as e:
            logger.debug(f"Error checking trigger: {e}")
            return False
        finally:
            if connection is None and hasattr(conn, "close"):
                await conn.close()
    
    async def drop_trigger(
        self,
        table: str,
        connection: Optional[Any] = None,
    ) -> bool:
        """
        Drop the NOTIFY trigger for a table.
        
        Returns:
            True if dropped, False if didn't exist
        """
        async with self._lock:
            channel_name = self.get_channel_name(table)
            
            conn = connection or await self._get_connection()
            if conn is None:
                return False
            
            try:
                trigger_name = f"{channel_name}_trigger"
                function_name = f"{channel_name}_notify"
                
                # Drop trigger
                await conn.execute(
                    f"DROP TRIGGER IF EXISTS {trigger_name} ON {table}"
                )
                
                # Drop function
                await conn.execute(
                    f"DROP FUNCTION IF EXISTS {function_name}()"
                )
                
                # Update cache
                if table in self._channels:
                    self._channels[table].trigger_exists = False
                    self._channels[table].function_exists = False
                
                logger.info(f"Dropped NOTIFY trigger for table: {table}")
                
                return True
                
            except Exception as e:
                logger.error(f"Error dropping trigger: {e}")
                return False
            finally:
                if connection is None and hasattr(conn, "close"):
                    await conn.close()
    
    def _generate_function_sql(self, table: str, channel: str) -> str:
        """Generate the trigger function SQL.
        
        Returns the SQL string without executing it.
        Used by ensure_trigger when adapter's execute_trigger_sql is available.
        """
        function_name = f"{channel}_notify"
        
        # Build payload JSON
        payload_parts = ["'operation', TG_OP"]
        
        # ID
        payload_parts.append("""
            'id', CASE
                WHEN TG_OP = 'DELETE' THEN OLD.id
                ELSE NEW.id
            END
        """)
        
        # Old data (for UPDATE/DELETE)
        if self._config.include_old_data:
            payload_parts.append("""
                'old', CASE
                    WHEN TG_OP IN ('UPDATE', 'DELETE') THEN row_to_json(OLD)
                    ELSE NULL
                END
            """)
        
        # New data (for INSERT/UPDATE)
        if self._config.include_new_data:
            payload_parts.append("""
                'new', CASE
                    WHEN TG_OP IN ('INSERT', 'UPDATE') THEN row_to_json(NEW)
                    ELSE NULL
                END
            """)
        
        # Changed columns (for UPDATE)
        if self._config.include_changed_columns:
            payload_parts.append("""
                'changed_columns', CASE
                    WHEN TG_OP = 'UPDATE' THEN (
                        SELECT array_agg(key)
                        FROM jsonb_each(to_jsonb(NEW)) n
                        FULL OUTER JOIN jsonb_each(to_jsonb(OLD)) o USING (key)
                        WHERE n.value IS DISTINCT FROM o.value
                    )
                    ELSE NULL
                END
            """)
        
        payload_json = ", ".join(payload_parts)
        
        return f"""
        CREATE OR REPLACE FUNCTION {function_name}()
        RETURNS trigger AS $$
        DECLARE
            payload TEXT;
        BEGIN
            payload := json_build_object({payload_json})::text;
            
            -- Truncate if too long
            IF length(payload) > {self._config.max_payload_size} THEN
                payload := json_build_object(
                    'operation', TG_OP,
                    'id', CASE WHEN TG_OP = 'DELETE' THEN OLD.id ELSE NEW.id END,
                    'truncated', true
                )::text;
            END IF;
            
            PERFORM pg_notify('{channel}', payload);
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
        """
    
    def _generate_trigger_sql(self, table: str, channel: str) -> str:
        """Generate the trigger creation SQL.
        
        Returns the SQL string without executing it.
        """
        trigger_name = f"{channel}_trigger"
        function_name = f"{channel}_notify"
        
        return f"""
        DROP TRIGGER IF EXISTS {trigger_name} ON {table};
        CREATE TRIGGER {trigger_name}
        AFTER INSERT OR UPDATE OR DELETE ON {table}
        FOR EACH ROW EXECUTE FUNCTION {function_name}();
        """
    
    async def _create_trigger_function(
        self,
        conn: Any,
        table: str,
        channel: str,
    ) -> None:
        """Create the trigger function."""
        function_sql = self._generate_function_sql(table, channel)
        await conn.execute(function_sql)
    
    async def _create_trigger(
        self,
        conn: Any,
        table: str,
        channel: str,
    ) -> None:
        """Create the trigger."""
        trigger_sql = self._generate_trigger_sql(table, channel)
        await conn.execute(trigger_sql)
    
    async def _get_connection(self) -> Optional[Any]:
        """Get a database connection using adapter's clean API."""
        try:
            from pynext.db.table import get_adapter
            
            adapter = get_adapter()
            
            # Use adapter's pool if available
            if hasattr(adapter, "_pool") and adapter._pool:
                return await adapter._pool.acquire()
            
            if hasattr(adapter, "_connection"):
                return adapter._connection
            
            return None
        except Exception:
            return None
    
    def get_tracked_tables(self) -> Set[str]:
        """Get set of tables with tracked triggers."""
        return {
            table
            for table, channel in self._channels.items()
            if channel.trigger_exists
        }
    
    def get_channel(self, table: str) -> Optional[NotifyChannel]:
        """Get channel info for a table."""
        return self._channels.get(table)


# Global trigger manager
_manager: Optional[TriggerManager] = None


def get_trigger_manager() -> TriggerManager:
    """Get the global trigger manager."""
    global _manager
    if _manager is None:
        _manager = TriggerManager()
    return _manager


def reset_trigger_manager() -> None:
    """Reset the trigger manager. Mainly for testing."""
    global _manager
    _manager = None

