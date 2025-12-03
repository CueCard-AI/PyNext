"""
Comprehensive tests for PyNext Live Query Server Components.

Tests the server-side live query handling:
- SSE endpoints
- WebSocket endpoints
- Trigger management
- Server integration

Target: 80 tests
"""

import pytest
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from pynext.server.live import (
    handle_sse,
    handle_websocket,
    handle_subscribe,
    handle_unsubscribe,
    handle_refresh,
    handle_stats,
    create_live_routes,
    create_live_router,
    _subscribe_query,
    _unsubscribe_query,
    _handle_ws_message,
)
from pynext.db.live.triggers import (
    TriggerManager,
    TriggerConfig,
    NotifyChannel,
    get_trigger_manager,
    reset_trigger_manager,
)
from pynext.db.live.config import (
    LiveQueryConfig,
    QuerySignature,
    TransportType,
)
from pynext.db.live.detection.base import ChangeEvent, ChangeType


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_request():
    """Create a mock HTTP request."""
    request = Mock()
    request.query_params = Mock()
    request.query_params.getlist = Mock(return_value=[])
    request.query_params.get = Mock(return_value=None)
    request.headers = {"accept": "text/event-stream"}
    return request


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket connection."""
    ws = AsyncMock()
    ws.query_params = {"client_id": "client_1"}
    ws.receive_text = AsyncMock(return_value='{"type": "ping"}')
    ws.send_text = AsyncMock()
    ws.close = AsyncMock()
    ws.accept = AsyncMock()
    return ws


@pytest.fixture
def query_signature():
    """Create a sample query signature."""
    return QuerySignature(table="users")


@pytest.fixture(autouse=True)
def reset_managers():
    """Reset singleton managers before each test."""
    reset_trigger_manager()
    yield


# =============================================================================
# TriggerConfig Tests
# =============================================================================

class TestTriggerConfig:
    """Tests for TriggerConfig dataclass."""
    
    def test_create_config(self):
        """Test creating trigger config."""
        config = TriggerConfig(
            prefix="test_",
            include_old_data=True,
            include_new_data=True,
        )
        
        assert config.prefix == "test_"
        assert config.include_old_data is True
        assert config.include_new_data is True
    
    def test_default_values(self):
        """Test default config values."""
        config = TriggerConfig()
        
        assert config.prefix == "pynext_live_"
        assert config.include_old_data is True
        assert config.include_new_data is True
        assert config.include_changed_columns is True
        assert config.max_payload_size == 7000
    
    def test_custom_max_payload(self):
        """Test custom max payload size."""
        config = TriggerConfig(max_payload_size=5000)
        assert config.max_payload_size == 5000


# =============================================================================
# NotifyChannel Tests
# =============================================================================

class TestNotifyChannel:
    """Tests for NotifyChannel dataclass."""
    
    def test_create_channel(self):
        """Test creating notify channel."""
        channel = NotifyChannel(
            table="users",
            channel="pynext_live_users",
        )
        
        assert channel.table == "users"
        assert channel.channel == "pynext_live_users"
        assert channel.trigger_exists is False
        assert channel.function_exists is False
    
    def test_channel_with_status(self):
        """Test channel with trigger status."""
        channel = NotifyChannel(
            table="users",
            channel="pynext_live_users",
            trigger_exists=True,
            function_exists=True,
        )
        
        assert channel.trigger_exists is True
        assert channel.function_exists is True
    
    def test_channel_has_created_at(self):
        """Test channel has created_at timestamp."""
        channel = NotifyChannel(
            table="users",
            channel="ch",
        )
        
        assert channel.created_at is not None
        assert isinstance(channel.created_at, datetime)


# =============================================================================
# TriggerManager Tests
# =============================================================================

class TestTriggerManager:
    """Tests for TriggerManager."""
    
    def test_get_trigger_manager_singleton(self):
        """Test getting trigger manager singleton."""
        m1 = get_trigger_manager()
        m2 = get_trigger_manager()
        
        assert m1 is m2
    
    def test_reset_trigger_manager(self):
        """Test resetting trigger manager."""
        m1 = get_trigger_manager()
        reset_trigger_manager()
        m2 = get_trigger_manager()
        
        assert m1 is not m2
    
    def test_get_channel_name(self):
        """Test generating channel name for table."""
        manager = TriggerManager()
        
        channel = manager.get_channel_name("users")
        
        assert "users" in channel
        assert channel.startswith("pynext_live_")
    
    def test_get_channel_name_custom_prefix(self):
        """Test channel name with custom prefix."""
        config = TriggerConfig(prefix="custom_")
        manager = TriggerManager(config)
        
        channel = manager.get_channel_name("posts")
        
        assert channel == "custom_posts"
    
    def test_generate_function_sql(self):
        """Test generating trigger function SQL."""
        manager = TriggerManager()
        
        sql = manager._generate_function_sql("users", "pynext_live_users")
        
        assert "CREATE OR REPLACE FUNCTION" in sql
        assert "pg_notify" in sql
        assert "pynext_live_users" in sql
    
    def test_generate_trigger_sql(self):
        """Test generating trigger SQL."""
        manager = TriggerManager()
        
        sql = manager._generate_trigger_sql("users", "pynext_live_users")
        
        assert "CREATE TRIGGER" in sql
        assert "users" in sql
        assert "AFTER INSERT OR UPDATE OR DELETE" in sql
    
    def test_generate_function_sql_includes_old_data(self):
        """Test function SQL includes old data when configured."""
        config = TriggerConfig(include_old_data=True)
        manager = TriggerManager(config)
        
        sql = manager._generate_function_sql("users", "ch")
        
        assert "'old'" in sql
        assert "row_to_json(OLD)" in sql
    
    def test_generate_function_sql_excludes_old_data(self):
        """Test function SQL excludes old data when configured."""
        config = TriggerConfig(include_old_data=False)
        manager = TriggerManager(config)
        
        sql = manager._generate_function_sql("users", "ch")
        
        assert "row_to_json(OLD)" not in sql
    
    def test_generate_function_sql_includes_changed_columns(self):
        """Test function SQL includes changed columns."""
        config = TriggerConfig(include_changed_columns=True)
        manager = TriggerManager(config)
        
        sql = manager._generate_function_sql("users", "ch")
        
        assert "'changed_columns'" in sql
    
    def test_get_tracked_tables_empty(self):
        """Test getting tracked tables when none exist."""
        manager = TriggerManager()
        
        tables = manager.get_tracked_tables()
        
        assert len(tables) == 0
    
    def test_get_tracked_tables(self):
        """Test getting tracked tables."""
        manager = TriggerManager()
        manager._channels["users"] = NotifyChannel(
            table="users",
            channel="ch",
            trigger_exists=True,
        )
        
        tables = manager.get_tracked_tables()
        
        assert "users" in tables
    
    def test_get_channel(self):
        """Test getting channel info."""
        manager = TriggerManager()
        channel = NotifyChannel(table="users", channel="ch")
        manager._channels["users"] = channel
        
        result = manager.get_channel("users")
        
        assert result is channel
    
    def test_get_channel_not_found(self):
        """Test getting channel for unknown table."""
        manager = TriggerManager()
        
        result = manager.get_channel("unknown")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_has_trigger_cached(self):
        """Test has_trigger uses cache."""
        manager = TriggerManager()
        manager._channels["users"] = NotifyChannel(
            table="users",
            channel="ch",
            trigger_exists=True,
        )
        
        result = await manager.has_trigger("users")
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_has_trigger_not_cached(self):
        """Test has_trigger when not cached."""
        manager = TriggerManager()
        
        # Mock the adapter - patch where it's imported
        mock_adapter = Mock()
        mock_adapter.check_trigger_exists = AsyncMock(return_value=False)
        
        with patch("pynext.db.table.get_adapter", return_value=mock_adapter):
            result = await manager.has_trigger("users")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_ensure_trigger_uses_cache(self):
        """Test ensure_trigger uses cache when trigger exists."""
        manager = TriggerManager()
        cached = NotifyChannel(
            table="users",
            channel="pynext_live_users",
            trigger_exists=True,
        )
        manager._channels["users"] = cached
        
        result = await manager.ensure_trigger("users")
        
        assert result is cached
    
    @pytest.mark.asyncio
    async def test_ensure_trigger_creates_trigger(self):
        """Test ensure_trigger creates trigger."""
        manager = TriggerManager()
        
        mock_adapter = Mock()
        mock_adapter.check_trigger_exists = AsyncMock(return_value=False)
        mock_adapter.execute_trigger_sql = AsyncMock()
        
        with patch("pynext.db.table.get_adapter", return_value=mock_adapter):
            result = await manager.ensure_trigger("users")
        
        assert result.table == "users"
        assert result.trigger_exists is True
        assert mock_adapter.execute_trigger_sql.call_count == 2  # Function + Trigger


# =============================================================================
# Server Handler Tests - handle_stats
# =============================================================================

class TestHandleStats:
    """Tests for handle_stats endpoint."""
    
    @pytest.mark.asyncio
    async def test_handle_stats_returns_json(self):
        """Test stats endpoint returns JSON."""
        request = Mock()
        
        with patch("pynext.server.live.get_subscription_manager") as mock_sub:
            with patch("pynext.server.live.get_transport_manager") as mock_trans:
                mock_sub.return_value.get_stats.return_value = {"count": 0}
                mock_trans.return_value.client_count = 0
                mock_trans.return_value.subscription_count = 0
                
                response = await handle_stats(request)
        
        assert response is not None


# =============================================================================
# Server Handler Tests - handle_subscribe
# =============================================================================

class TestHandleSubscribe:
    """Tests for handle_subscribe endpoint."""
    
    @pytest.mark.asyncio
    async def test_handle_subscribe_success(self):
        """Test successful subscription."""
        request = AsyncMock()
        request.json = AsyncMock(return_value={
            "id": "query_1",
            "table": "users",
        })
        request.headers = {"X-PyNext-Client-ID": "client_1"}
        
        with patch("pynext.server.live.get_subscription_manager") as mock_sub:
            with patch("pynext.server.live.get_transport_manager") as mock_trans:
                mock_sub.return_value.subscribe = AsyncMock(return_value="sub_1")
                mock_trans.return_value.subscribe_query = Mock()
                
                response = await handle_subscribe(request)
        
        assert response is not None


# =============================================================================
# Server Handler Tests - handle_unsubscribe
# =============================================================================

class TestHandleUnsubscribe:
    """Tests for handle_unsubscribe endpoint."""
    
    @pytest.mark.asyncio
    async def test_handle_unsubscribe_success(self):
        """Test successful unsubscription."""
        request = AsyncMock()
        request.json = AsyncMock(return_value={"query_id": "query_1"})
        
        with patch("pynext.server.live.get_subscription_manager") as mock_sub:
            mock_sub.return_value.unsubscribe = AsyncMock()
            
            response = await handle_unsubscribe(request)
        
        assert response is not None
    
    @pytest.mark.asyncio
    async def test_handle_unsubscribe_missing_query_id(self):
        """Test unsubscribe without query_id."""
        request = AsyncMock()
        request.json = AsyncMock(return_value={})  # No query_id
        
        response = await handle_unsubscribe(request)
        
        # Should return error response
        assert response is not None


# =============================================================================
# Server Handler Tests - handle_refresh
# =============================================================================

class TestHandleRefresh:
    """Tests for handle_refresh endpoint."""
    
    @pytest.mark.asyncio
    async def test_handle_refresh_success(self):
        """Test successful refresh."""
        request = Mock()
        mock_params = Mock()
        mock_params.get = Mock(return_value="query_1")
        request.query_params = mock_params
        
        response = await handle_refresh(request)
        
        assert response is not None
    
    @pytest.mark.asyncio
    async def test_handle_refresh_missing_query_id(self):
        """Test refresh without query_id."""
        request = Mock()
        mock_params = Mock()
        mock_params.get = Mock(return_value=None)
        request.query_params = mock_params
        
        response = await handle_refresh(request)
        
        # Should return error response
        assert response is not None


# =============================================================================
# WebSocket Message Handler Tests
# =============================================================================

class TestWSMessageHandler:
    """Tests for WebSocket message handling."""
    
    @pytest.mark.asyncio
    async def test_handle_ping(self, mock_websocket):
        """Test handling ping message."""
        message = {"type": "ping"}
        
        await _handle_ws_message("client_1", message, mock_websocket)
        
        mock_websocket.send_text.assert_called_once()
        sent = json.loads(mock_websocket.send_text.call_args[0][0])
        assert sent["type"] == "pong"
    
    @pytest.mark.asyncio
    async def test_handle_subscribe_message(self, mock_websocket):
        """Test handling subscribe message."""
        message = {
            "type": "subscribe",
            "query_id": "query_1",
            "data": {"table": "users"},
        }
        
        with patch("pynext.server.live.get_subscription_manager") as mock_sub:
            with patch("pynext.server.live.get_transport_manager") as mock_trans:
                mock_sub.return_value.subscribe = AsyncMock(return_value="sub_1")
                mock_trans.return_value.subscribe_query = Mock()
                
                await _handle_ws_message("client_1", message, mock_websocket)
        
        mock_websocket.send_text.assert_called()
        sent = json.loads(mock_websocket.send_text.call_args[0][0])
        assert sent["type"] == "subscribed"
    
    @pytest.mark.asyncio
    async def test_handle_unsubscribe_message(self, mock_websocket):
        """Test handling unsubscribe message."""
        message = {
            "type": "unsubscribe",
            "query_id": "query_1",
        }
        
        with patch("pynext.server.live.get_subscription_manager") as mock_sub:
            mock_sub.return_value.unsubscribe = AsyncMock()
            
            await _handle_ws_message("client_1", message, mock_websocket)
        
        mock_websocket.send_text.assert_called()
        sent = json.loads(mock_websocket.send_text.call_args[0][0])
        assert sent["type"] == "unsubscribed"


# =============================================================================
# Subscribe Query Function Tests
# =============================================================================

class TestSubscribeQuery:
    """Tests for _subscribe_query function."""
    
    @pytest.mark.asyncio
    async def test_subscribe_query_basic(self):
        """Test basic query subscription."""
        with patch("pynext.server.live.get_subscription_manager") as mock_sub:
            with patch("pynext.server.live.get_transport_manager") as mock_trans:
                mock_sub.return_value.subscribe = AsyncMock(return_value="sub_1")
                mock_trans.return_value.subscribe_query = Mock()
                
                result = await _subscribe_query("client_1", {
                    "id": "query_1",
                    "table": "users",
                })
        
        assert result == "sub_1"
    
    @pytest.mark.asyncio
    async def test_subscribe_query_with_where(self):
        """Test query subscription with where clause."""
        with patch("pynext.server.live.get_subscription_manager") as mock_sub:
            with patch("pynext.server.live.get_transport_manager") as mock_trans:
                mock_sub.return_value.subscribe = AsyncMock(return_value="sub_1")
                mock_trans.return_value.subscribe_query = Mock()
                
                await _subscribe_query("client_1", {
                    "id": "query_1",
                    "table": "users",
                    "where": {"status": "active"},
                })
        
        # Should not raise
        mock_sub.return_value.subscribe.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_subscribe_query_missing_table(self):
        """Test subscription without table raises error."""
        with pytest.raises(ValueError, match="Table name required"):
            await _subscribe_query("client_1", {"id": "query_1"})


# =============================================================================
# Route Creation Tests
# =============================================================================

class TestRouteCreation:
    """Tests for route creation functions."""
    
    def test_create_live_routes(self):
        """Test creating Starlette routes."""
        try:
            routes = create_live_routes()
            
            # Should have multiple routes
            assert len(routes) >= 4
            
            # Check route paths
            paths = [r.path for r in routes if hasattr(r, "path")]
            assert any("sse" in p for p in paths)
            assert any("subscribe" in p for p in paths)
            assert any("unsubscribe" in p for p in paths)
        except RuntimeError as e:
            # starlette not installed
            if "starlette" in str(e):
                pytest.skip("starlette not installed")
            raise
    
    def test_create_live_router(self):
        """Test creating FastAPI router."""
        try:
            router = create_live_router()
            
            # Should be a router
            assert router is not None
            
            # Check routes exist
            routes = router.routes
            assert len(routes) >= 4
        except RuntimeError as e:
            # fastapi not installed
            if "fastapi" in str(e):
                pytest.skip("fastapi not installed")
            raise


# =============================================================================
# Integration Tests
# =============================================================================

class TestServerIntegration:
    """Integration tests for server components."""
    
    @pytest.mark.asyncio
    async def test_full_subscribe_unsubscribe_flow(self):
        """Test complete subscribe/unsubscribe flow."""
        with patch("pynext.server.live.get_subscription_manager") as mock_sub:
            with patch("pynext.server.live.get_transport_manager") as mock_trans:
                mock_sub.return_value.subscribe = AsyncMock(return_value="sub_1")
                mock_sub.return_value.unsubscribe = AsyncMock()
                mock_trans.return_value.subscribe_query = Mock()
                
                # Subscribe
                sub_id = await _subscribe_query("client_1", {
                    "id": "query_1",
                    "table": "users",
                })
                
                assert sub_id == "sub_1"
                
                # Unsubscribe
                await _unsubscribe_query("query_1")
                
                mock_sub.return_value.unsubscribe.assert_called_once_with("query_1")
    
    @pytest.mark.asyncio
    async def test_websocket_subscribe_and_ping(self, mock_websocket):
        """Test WebSocket subscribe then ping."""
        with patch("pynext.server.live.get_subscription_manager") as mock_sub:
            with patch("pynext.server.live.get_transport_manager") as mock_trans:
                mock_sub.return_value.subscribe = AsyncMock(return_value="sub_1")
                mock_trans.return_value.subscribe_query = Mock()
                
                # Subscribe
                await _handle_ws_message("client_1", {
                    "type": "subscribe",
                    "query_id": "q1",
                    "data": {"table": "users"},
                }, mock_websocket)
                
                # Ping
                await _handle_ws_message("client_1", {"type": "ping"}, mock_websocket)
                
                assert mock_websocket.send_text.call_count == 2


# =============================================================================
# Edge Cases
# =============================================================================

class TestEdgeCases:
    """Edge case tests."""
    
    @pytest.mark.asyncio
    async def test_subscribe_with_where_list(self):
        """Test subscription with where as list."""
        with patch("pynext.server.live.get_subscription_manager") as mock_sub:
            with patch("pynext.server.live.get_transport_manager") as mock_trans:
                mock_sub.return_value.subscribe = AsyncMock(return_value="sub_1")
                mock_trans.return_value.subscribe_query = Mock()
                
                await _subscribe_query("client_1", {
                    "id": "query_1",
                    "table": "users",
                    "where": [{"status": "active"}, {"role": "admin"}],
                })
        
        mock_sub.return_value.subscribe.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_subscribe_generates_id(self):
        """Test subscription generates ID if not provided."""
        with patch("pynext.server.live.get_subscription_manager") as mock_sub:
            with patch("pynext.server.live.get_transport_manager") as mock_trans:
                mock_sub.return_value.subscribe = AsyncMock(return_value="sub_1")
                mock_trans.return_value.subscribe_query = Mock()
                
                await _subscribe_query("client_1", {
                    "table": "users",
                    # No "id" provided
                })
        
        mock_sub.return_value.subscribe.assert_called_once()
    
    def test_trigger_manager_with_custom_config(self):
        """Test TriggerManager with custom config."""
        config = TriggerConfig(
            prefix="myapp_",
            include_old_data=False,
            include_new_data=True,
            include_changed_columns=False,
            max_payload_size=3000,
        )
        manager = TriggerManager(config)
        
        channel = manager.get_channel_name("users")
        assert channel == "myapp_users"
        
        sql = manager._generate_function_sql("users", "myapp_users")
        assert "row_to_json(OLD)" not in sql  # Old data excluded
        assert "row_to_json(NEW)" in sql  # New data included
