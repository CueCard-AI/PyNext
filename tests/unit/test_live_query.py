"""
Comprehensive tests for PyNext Live Query Core.

Tests the LiveQuery class, Model.live() method, and query chaining.
Target: 80 tests
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from pynext.db.live.config import (
    LiveQueryConfig,
    QuerySignature,
    TransportType,
    DetectionStrategy,
    UpdateGranularity,
    DEFAULT_CONFIG,
    ServerConfig,
    configure_live_queries,
    get_server_config,
)
from pynext.db.live.query import (
    LiveQuery,
    LiveQueryState,
    LiveQueryMetadata,
    live,
)


# =============================================================================
# Fixtures
# =============================================================================

class MockModel:
    """Mock model for testing."""
    __table_name__ = "users"
    _fields = {"id": Mock(), "name": Mock(), "email": Mock()}
    
    def __init__(self, **data):
        for k, v in data.items():
            setattr(self, k, v)
    
    @classmethod
    def _from_row(cls, row):
        return cls(**row)
    
    def _to_dict(self):
        return {"id": self.id, "name": getattr(self, "name", None)}


@pytest.fixture
def mock_model():
    return MockModel


@pytest.fixture
def live_config():
    return LiveQueryConfig()


# =============================================================================
# LiveQueryConfig Tests
# =============================================================================

class TestLiveQueryConfig:
    """Tests for LiveQueryConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = LiveQueryConfig()
        
        assert config.transport == TransportType.AUTO
        assert config.detection == DetectionStrategy.AUTO
        assert config.granularity == UpdateGranularity.AUTO
        assert config.poll_interval == 30.0
        assert config.batch_updates is True
        assert config.reconnect is True
        assert config.initial_fetch is True
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = LiveQueryConfig(
            transport=TransportType.WEBSOCKET,
            poll_interval=10.0,
            debug=True,
        )
        
        assert config.transport == TransportType.WEBSOCKET
        assert config.poll_interval == 10.0
        assert config.debug is True
    
    def test_config_merge(self):
        """Test merging configurations."""
        config = LiveQueryConfig()
        merged = config.merge(poll_interval=5.0, debug=True)
        
        assert merged.poll_interval == 5.0
        assert merged.debug is True
        assert config.poll_interval == 30.0  # Original unchanged
    
    def test_config_to_dict(self):
        """Test converting config to dict."""
        config = LiveQueryConfig()
        d = config.to_dict()
        
        assert d["transport"] == "auto"
        assert d["detection"] == "auto"
        assert d["poll_interval"] == 30.0
    
    def test_transport_types(self):
        """Test all transport types."""
        assert TransportType.AUTO.value == "auto"
        assert TransportType.SSE.value == "sse"
        assert TransportType.WEBSOCKET.value == "websocket"
    
    def test_detection_strategies(self):
        """Test all detection strategies."""
        assert DetectionStrategy.AUTO.value == "auto"
        assert DetectionStrategy.SUPABASE.value == "supabase"
        assert DetectionStrategy.POSTGRES.value == "postgres"
        assert DetectionStrategy.POLLING.value == "polling"
    
    def test_update_granularities(self):
        """Test all update granularities."""
        assert UpdateGranularity.AUTO.value == "auto"
        assert UpdateGranularity.SURGICAL.value == "surgical"
        assert UpdateGranularity.REFRESH.value == "refresh"


# =============================================================================
# QuerySignature Tests
# =============================================================================

class TestQuerySignature:
    """Tests for QuerySignature."""
    
    def test_simple_signature(self):
        """Test simple query signature."""
        sig = QuerySignature(table="users")
        
        assert sig.table == "users"
        assert sig.is_simple is True
        assert sig.has_filters is False
        assert sig.has_ordering is False
        assert sig.has_limit is False
    
    def test_signature_with_filters(self):
        """Test signature with WHERE clauses."""
        sig = QuerySignature(
            table="users",
            where_clauses=(("status", "active"),),
        )
        
        assert sig.is_simple is False
        assert sig.has_filters is True
    
    def test_signature_with_ordering(self):
        """Test signature with ORDER BY."""
        sig = QuerySignature(
            table="users",
            order_by="-created_at",
        )
        
        assert sig.has_ordering is True
    
    def test_signature_with_limit(self):
        """Test signature with LIMIT."""
        sig = QuerySignature(
            table="users",
            limit=10,
        )
        
        assert sig.has_limit is True
    
    def test_signature_hash(self):
        """Test signature hashing for deduplication."""
        sig1 = QuerySignature(table="users", limit=10)
        sig2 = QuerySignature(table="users", limit=10)
        sig3 = QuerySignature(table="users", limit=20)
        
        assert hash(sig1) == hash(sig2)
        assert hash(sig1) != hash(sig3)
    
    def test_signature_equality(self):
        """Test signature equality."""
        sig1 = QuerySignature(table="users")
        sig2 = QuerySignature(table="users")
        sig3 = QuerySignature(table="posts")
        
        assert sig1 == sig2
        assert sig1 != sig3
    
    def test_signature_with_fields(self):
        """Test signature with specific fields."""
        sig = QuerySignature(
            table="users",
            fields=("id", "name"),
        )
        
        assert sig.fields == ("id", "name")


# =============================================================================
# ServerConfig Tests
# =============================================================================

class TestServerConfig:
    """Tests for ServerConfig."""
    
    def test_default_server_config(self):
        """Test default server configuration."""
        config = ServerConfig()
        
        assert config.sse_path == "/_pynext/live/sse"
        assert config.ws_path == "/_pynext/live/ws"
        assert config.max_subscriptions_per_client == 100
        assert config.max_clients == 10000
    
    def test_configure_live_queries(self):
        """Test configuring live queries."""
        config = configure_live_queries(ServerConfig(debug=True))
        
        assert config.debug is True
        assert get_server_config().debug is True
    
    def test_get_server_config_default(self):
        """Test getting default server config."""
        config = get_server_config()
        assert isinstance(config, ServerConfig)


# =============================================================================
# LiveQuery Tests
# =============================================================================

class TestLiveQuery:
    """Tests for LiveQuery class."""
    
    def test_create_live_query(self, mock_model):
        """Test creating a live query."""
        with patch('asyncio.create_task'):
            query = LiveQuery(mock_model, config=LiveQueryConfig(initial_fetch=False))
            
            assert query._model == mock_model
            assert query._data == []
            assert query._loading() is True
            assert query._state() == LiveQueryState.IDLE
    
    def test_live_query_call(self, mock_model):
        """Test calling live query to get data."""
        with patch.object(LiveQuery, '_start', new_callable=AsyncMock):
            query = LiveQuery(mock_model, config=LiveQueryConfig(initial_fetch=False))
            query._data = [{"id": 1}]
            
            assert query() == [{"id": 1}]
    
    def test_live_query_where(self, mock_model):
        """Test adding WHERE clause."""
        with patch.object(LiveQuery, '_start', new_callable=AsyncMock):
            query = LiveQuery(mock_model, config=LiveQueryConfig(initial_fetch=False))
            query = query.where(status="active")
            
            assert {"status": "active"} in query._where_clauses
    
    def test_live_query_where_chaining(self, mock_model):
        """Test chaining multiple WHERE clauses."""
        with patch.object(LiveQuery, '_start', new_callable=AsyncMock):
            query = LiveQuery(mock_model, config=LiveQueryConfig(initial_fetch=False))
            query = query.where(status="active").where(role="admin")
            
            assert len(query._where_clauses) == 2
    
    def test_live_query_where_in(self, mock_model):
        """Test WHERE IN clause."""
        with patch.object(LiveQuery, '_start', new_callable=AsyncMock):
            query = LiveQuery(mock_model, config=LiveQueryConfig(initial_fetch=False))
            query = query.where_in("id", [1, 2, 3])
            
            assert {"id__in": [1, 2, 3]} in query._where_clauses
    
    def test_live_query_where_not(self, mock_model):
        """Test WHERE NOT clause."""
        with patch.object(LiveQuery, '_start', new_callable=AsyncMock):
            query = LiveQuery(mock_model, config=LiveQueryConfig(initial_fetch=False))
            query = query.where_not(status="deleted")
            
            assert {"status__ne": "deleted"} in query._where_clauses
    
    def test_live_query_where_gt(self, mock_model):
        """Test WHERE > clause."""
        with patch.object(LiveQuery, '_start', new_callable=AsyncMock):
            query = LiveQuery(mock_model, config=LiveQueryConfig(initial_fetch=False))
            query = query.where_gt("age", 18)
            
            assert {"age__gt": 18} in query._where_clauses
    
    def test_live_query_where_gte(self, mock_model):
        """Test WHERE >= clause."""
        with patch.object(LiveQuery, '_start', new_callable=AsyncMock):
            query = LiveQuery(mock_model, config=LiveQueryConfig(initial_fetch=False))
            query = query.where_gte("age", 18)
            
            assert {"age__gte": 18} in query._where_clauses
    
    def test_live_query_where_lt(self, mock_model):
        """Test WHERE < clause."""
        with patch.object(LiveQuery, '_start', new_callable=AsyncMock):
            query = LiveQuery(mock_model, config=LiveQueryConfig(initial_fetch=False))
            query = query.where_lt("age", 65)
            
            assert {"age__lt": 65} in query._where_clauses
    
    def test_live_query_where_lte(self, mock_model):
        """Test WHERE <= clause."""
        with patch.object(LiveQuery, '_start', new_callable=AsyncMock):
            query = LiveQuery(mock_model, config=LiveQueryConfig(initial_fetch=False))
            query = query.where_lte("age", 65)
            
            assert {"age__lte": 65} in query._where_clauses
    
    def test_live_query_where_like(self, mock_model):
        """Test WHERE LIKE clause."""
        with patch.object(LiveQuery, '_start', new_callable=AsyncMock):
            query = LiveQuery(mock_model, config=LiveQueryConfig(initial_fetch=False))
            query = query.where_like("email", "%@gmail.com")
            
            assert {"email__like": "%@gmail.com"} in query._where_clauses
    
    def test_live_query_where_null(self, mock_model):
        """Test WHERE NULL clause."""
        with patch.object(LiveQuery, '_start', new_callable=AsyncMock):
            query = LiveQuery(mock_model, config=LiveQueryConfig(initial_fetch=False))
            query = query.where_null("deleted_at")
            
            assert {"deleted_at__null": True} in query._where_clauses
    
    def test_live_query_where_not_null(self, mock_model):
        """Test WHERE NOT NULL clause."""
        with patch.object(LiveQuery, '_start', new_callable=AsyncMock):
            query = LiveQuery(mock_model, config=LiveQueryConfig(initial_fetch=False))
            query = query.where_not_null("email")
            
            assert {"email__null": False} in query._where_clauses
    
    def test_live_query_order_by(self, mock_model):
        """Test ORDER BY clause."""
        with patch.object(LiveQuery, '_start', new_callable=AsyncMock):
            query = LiveQuery(mock_model, config=LiveQueryConfig(initial_fetch=False))
            query = query.order_by("-created_at")
            
            assert query._order_by == "-created_at"
    
    def test_live_query_limit(self, mock_model):
        """Test LIMIT clause."""
        with patch.object(LiveQuery, '_start', new_callable=AsyncMock):
            query = LiveQuery(mock_model, config=LiveQueryConfig(initial_fetch=False))
            query = query.limit(10)
            
            assert query._limit == 10
    
    def test_live_query_offset(self, mock_model):
        """Test OFFSET clause."""
        with patch.object(LiveQuery, '_start', new_callable=AsyncMock):
            query = LiveQuery(mock_model, config=LiveQueryConfig(initial_fetch=False))
            query = query.offset(5)
            
            assert query._offset == 5
    
    def test_live_query_select_fields(self, mock_model):
        """Test selecting specific fields."""
        with patch.object(LiveQuery, '_start', new_callable=AsyncMock):
            query = LiveQuery(mock_model, config=LiveQueryConfig(initial_fetch=False))
            query = query.select("id", "name")
            
            assert query._fields == ["id", "name"]
    
    def test_live_query_loading_signal(self, mock_model):
        """Test loading signal."""
        with patch.object(LiveQuery, '_start', new_callable=AsyncMock):
            query = LiveQuery(mock_model, config=LiveQueryConfig(initial_fetch=False))
            
            assert query.loading() is True
            query._loading.set(False)
            assert query.loading() is False
    
    def test_live_query_error_signal(self, mock_model):
        """Test error signal."""
        with patch.object(LiveQuery, '_start', new_callable=AsyncMock):
            query = LiveQuery(mock_model, config=LiveQueryConfig(initial_fetch=False))
            
            assert query.error() is None
            query._error.set(Exception("Test error"))
            assert query.error() is not None
    
    def test_live_query_state_signal(self, mock_model):
        """Test state signal."""
        with patch.object(LiveQuery, '_start', new_callable=AsyncMock):
            query = LiveQuery(mock_model, config=LiveQueryConfig(initial_fetch=False))
            
            assert query.state() == LiveQueryState.IDLE
            query._state.set(LiveQueryState.ACTIVE)
            assert query.state() == LiveQueryState.ACTIVE
    
    def test_live_query_is_empty(self, mock_model):
        """Test is_empty property."""
        with patch.object(LiveQuery, '_start', new_callable=AsyncMock):
            query = LiveQuery(mock_model, config=LiveQueryConfig(initial_fetch=False))
            
            assert query.is_empty is True
            query._data = [{"id": 1}]
            assert query.is_empty is False
    
    def test_live_query_count(self, mock_model):
        """Test count property."""
        with patch.object(LiveQuery, '_start', new_callable=AsyncMock):
            query = LiveQuery(mock_model, config=LiveQueryConfig(initial_fetch=False))
            
            assert query.count == 0
            query._data = [{"id": 1}, {"id": 2}]
            assert query.count == 2
    
    def test_live_query_metadata(self, mock_model):
        """Test metadata property."""
        with patch.object(LiveQuery, '_start', new_callable=AsyncMock):
            query = LiveQuery(mock_model, config=LiveQueryConfig(initial_fetch=False))
            
            assert query.metadata.table == "users"
            assert isinstance(query.metadata.created_at, datetime)
    
    def test_live_query_stop(self, mock_model):
        """Test stopping a live query."""
        with patch('asyncio.create_task'):
            query = LiveQuery(mock_model, config=LiveQueryConfig(initial_fetch=False))
            mock_unsub = Mock()
            query._unsubscribe = mock_unsub
            
            query.stop()
            
            assert query.state() == LiveQueryState.STOPPED
            mock_unsub.assert_called_once()
    
    def test_live_query_subscribe(self, mock_model):
        """Test subscribing to data changes."""
        with patch.object(LiveQuery, '_start', new_callable=AsyncMock):
            query = LiveQuery(mock_model, config=LiveQueryConfig(initial_fetch=False))
            
            callback = Mock()
            unsubscribe = query.subscribe(callback)
            
            assert callback in query._subscribers
            
            unsubscribe()
            assert callback not in query._subscribers
    
    def test_live_query_notify_subscribers(self, mock_model):
        """Test notifying subscribers."""
        with patch.object(LiveQuery, '_start', new_callable=AsyncMock):
            query = LiveQuery(mock_model, config=LiveQueryConfig(initial_fetch=False))
            query._data = [{"id": 1}]
            
            callback = Mock()
            query.subscribe(callback)
            query._notify_subscribers()
            
            callback.assert_called_once_with([{"id": 1}])
    
    def test_live_query_build_signature(self, mock_model):
        """Test building query signature."""
        with patch.object(LiveQuery, '_start', new_callable=AsyncMock):
            query = LiveQuery(mock_model, config=LiveQueryConfig(initial_fetch=False))
            query = query.where(status="active").order_by("name").limit(10)
            
            sig = query._build_signature()
            
            assert sig.table == "users"
            assert sig.has_filters is True
            assert sig.has_ordering is True
            assert sig.has_limit is True
    
    def test_live_query_repr(self, mock_model):
        """Test string representation."""
        with patch.object(LiveQuery, '_start', new_callable=AsyncMock):
            query = LiveQuery(mock_model, config=LiveQueryConfig(initial_fetch=False))
            
            repr_str = repr(query)
            assert "LiveQuery" in repr_str
            assert "MockModel" in repr_str
    
    def test_live_query_to_hydration_data(self, mock_model):
        """Test getting hydration data."""
        with patch.object(LiveQuery, '_start', new_callable=AsyncMock):
            query = LiveQuery(mock_model, config=LiveQueryConfig(initial_fetch=False))
            
            data = query.to_hydration_data()
            
            assert "id" in data
            assert data["table"] == "users"
            assert data["loading"] is True


# =============================================================================
# LiveQueryMetadata Tests
# =============================================================================

class TestLiveQueryMetadata:
    """Tests for LiveQueryMetadata."""
    
    def test_metadata_creation(self):
        """Test creating metadata."""
        meta = LiveQueryMetadata(
            id="test_id",
            table="users",
            created_at=datetime.utcnow(),
        )
        
        assert meta.id == "test_id"
        assert meta.table == "users"
        assert meta.update_count == 0
        assert meta.error_count == 0
    
    def test_metadata_update_tracking(self):
        """Test tracking updates."""
        meta = LiveQueryMetadata(
            id="test_id",
            table="users",
            created_at=datetime.utcnow(),
        )
        
        meta.update_count = 5
        meta.last_update = datetime.utcnow()
        
        assert meta.update_count == 5
        assert meta.last_update is not None


# =============================================================================
# LiveQueryState Tests
# =============================================================================

class TestLiveQueryState:
    """Tests for LiveQueryState enum."""
    
    def test_all_states(self):
        """Test all query states exist."""
        assert LiveQueryState.IDLE.value == "idle"
        assert LiveQueryState.CONNECTING.value == "connecting"
        assert LiveQueryState.LOADING.value == "loading"
        assert LiveQueryState.ACTIVE.value == "active"
        assert LiveQueryState.ERROR.value == "error"
        assert LiveQueryState.STOPPED.value == "stopped"


# =============================================================================
# live() Factory Function Tests
# =============================================================================

class TestLiveFactory:
    """Tests for live() factory function."""
    
    def test_live_factory(self, mock_model):
        """Test live() factory function."""
        with patch('asyncio.create_task'):
            query = live(mock_model, config=LiveQueryConfig(initial_fetch=False))
            
            assert isinstance(query, LiveQuery)
            assert query._model == mock_model
    
    def test_live_factory_with_config(self, mock_model):
        """Test live() with custom config."""
        with patch('asyncio.create_task'):
            config = LiveQueryConfig(poll_interval=5.0, initial_fetch=False)
            query = live(mock_model, config=config)
            
            assert query._config.poll_interval == 5.0


# =============================================================================
# Complex Query Chaining Tests
# =============================================================================

class TestComplexQueryChaining:
    """Tests for complex query chaining."""
    
    def test_complex_where_chain(self, mock_model):
        """Test complex WHERE chain."""
        with patch.object(LiveQuery, '_start', new_callable=AsyncMock):
            query = (
                LiveQuery(mock_model, config=LiveQueryConfig(initial_fetch=False))
                .where(status="active")
                .where(role="admin")
                .where_not(deleted=True)
                .where_gt("age", 18)
                .where_like("email", "%@company.com")
            )
            
            assert len(query._where_clauses) == 5
    
    def test_full_query_chain(self, mock_model):
        """Test full query chain with all options."""
        with patch.object(LiveQuery, '_start', new_callable=AsyncMock):
            query = (
                LiveQuery(mock_model, config=LiveQueryConfig(initial_fetch=False))
                .where(status="active")
                .where_in("role", ["admin", "moderator"])
                .order_by("-created_at")
                .select("id", "name", "email")
                .limit(10)
                .offset(20)
            )
            
            assert len(query._where_clauses) == 2
            assert query._order_by == "-created_at"
            assert query._fields == ["id", "name", "email"]
            assert query._limit == 10
            assert query._offset == 20


# =============================================================================
# Edge Case Tests
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases."""
    
    def test_empty_where_chain(self, mock_model):
        """Test query with no WHERE clauses."""
        with patch.object(LiveQuery, '_start', new_callable=AsyncMock):
            query = LiveQuery(mock_model, config=LiveQueryConfig(initial_fetch=False))
            sig = query._build_signature()
            
            assert sig.is_simple is True
    
    def test_subscriber_error_handling(self, mock_model):
        """Test that subscriber errors don't affect other subscribers."""
        with patch.object(LiveQuery, '_start', new_callable=AsyncMock):
            query = LiveQuery(mock_model, config=LiveQueryConfig(initial_fetch=False))
            
            error_callback = Mock(side_effect=Exception("Subscriber error"))
            success_callback = Mock()
            
            query.subscribe(error_callback)
            query.subscribe(success_callback)
            
            # Should not raise
            query._notify_subscribers()
            
            # Success callback still called
            success_callback.assert_called_once()
    
    def test_double_stop(self, mock_model):
        """Test stopping an already stopped query."""
        with patch.object(LiveQuery, '_start', new_callable=AsyncMock):
            query = LiveQuery(mock_model, config=LiveQueryConfig(initial_fetch=False))
            
            query.stop()
            query.stop()  # Should not raise
            
            assert query.state() == LiveQueryState.STOPPED
    
    def test_unsubscribe_nonexistent(self, mock_model):
        """Test unsubscribing a callback that doesn't exist."""
        with patch.object(LiveQuery, '_start', new_callable=AsyncMock):
            query = LiveQuery(mock_model, config=LiveQueryConfig(initial_fetch=False))
            
            callback = Mock()
            unsubscribe = query.subscribe(callback)
            unsubscribe()
            unsubscribe()  # Double unsubscribe should not raise
    
    def test_config_with_all_options(self):
        """Test config with all options specified."""
        config = LiveQueryConfig(
            transport=TransportType.WEBSOCKET,
            detection=DetectionStrategy.POSTGRES,
            granularity=UpdateGranularity.SURGICAL,
            poll_interval=5.0,
            batch_updates=False,
            batch_delay_ms=100,
            dedupe_queries=False,
            reconnect=False,
            reconnect_delay_ms=2000,
            max_reconnect_attempts=5,
            initial_fetch=False,
            stale_time_ms=1000,
            cache_results=False,
            optimistic_updates=True,
            debug=True,
        )
        
        assert config.transport == TransportType.WEBSOCKET
        assert config.detection == DetectionStrategy.POSTGRES
        assert config.granularity == UpdateGranularity.SURGICAL
        assert config.poll_interval == 5.0
        assert config.batch_updates is False
        assert config.reconnect is False
        assert config.initial_fetch is False
        assert config.optimistic_updates is True
        assert config.debug is True

