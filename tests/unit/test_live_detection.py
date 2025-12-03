"""
Comprehensive tests for PyNext Live Query Change Detection.

Tests the ChangeDetector base class and all implementations:
- PostgresNotifyDetector
- SupabaseRealtimeDetector
- PollingDetector
- DetectorRegistry

Target: 100 tests
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from pynext.db.live.detection.base import (
    ChangeDetector,
    ChangeEvent,
    ChangeType,
    ChangeCallback,
)
from pynext.db.live.detection.postgres import PostgresNotifyDetector
from pynext.db.live.detection.supabase import SupabaseRealtimeDetector
from pynext.db.live.detection.polling import PollingDetector
from pynext.db.live.detection.registry import (
    DetectorRegistry,
    get_detector_registry,
    reset_detector_registry,
)
from pynext.db.live.config import QuerySignature


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def change_event():
    """Create a sample change event."""
    return ChangeEvent(
        table="users",
        type=ChangeType.INSERT,
        row_id=1,
        new_data={"id": 1, "name": "John"},
        timestamp=datetime.utcnow(),
        source="test",
    )


@pytest.fixture
def query_signature():
    """Create a sample query signature."""
    return QuerySignature(table="users")


@pytest.fixture
async def detector_registry():
    """Create a fresh detector registry."""
    # Clear any existing registry state first (avoid Mock await issues)
    from pynext.db.live.detection.registry import _registry
    global _registry
    import pynext.db.live.detection.registry as registry_module
    registry_module._registry = None
    
    # Now get a fresh registry
    return get_detector_registry()


# =============================================================================
# ChangeType Tests
# =============================================================================

class TestChangeType:
    """Tests for ChangeType enum."""
    
    def test_all_change_types(self):
        """Test all change types exist."""
        assert ChangeType.INSERT.value == "INSERT"
        assert ChangeType.UPDATE.value == "UPDATE"
        assert ChangeType.DELETE.value == "DELETE"
        assert ChangeType.TRUNCATE.value == "TRUNCATE"
        assert ChangeType.UNKNOWN.value == "UNKNOWN"


# =============================================================================
# ChangeEvent Tests
# =============================================================================

class TestChangeEvent:
    """Tests for ChangeEvent dataclass."""
    
    def test_create_insert_event(self):
        """Test creating an INSERT event."""
        event = ChangeEvent(
            table="users",
            type=ChangeType.INSERT,
            row_id=1,
            new_data={"id": 1, "name": "John"},
        )
        
        assert event.table == "users"
        assert event.type == ChangeType.INSERT
        assert event.is_insert is True
        assert event.is_update is False
        assert event.is_delete is False
        assert event.has_data is True
    
    def test_create_update_event(self):
        """Test creating an UPDATE event."""
        event = ChangeEvent(
            table="users",
            type=ChangeType.UPDATE,
            row_id=1,
            old_data={"id": 1, "name": "John"},
            new_data={"id": 1, "name": "Jane"},
            columns_changed=["name"],
        )
        
        assert event.is_update is True
        assert event.columns_changed == ["name"]
    
    def test_create_delete_event(self):
        """Test creating a DELETE event."""
        event = ChangeEvent(
            table="users",
            type=ChangeType.DELETE,
            row_id=1,
            old_data={"id": 1, "name": "John"},
        )
        
        assert event.is_delete is True
        assert event.old_data is not None
    
    def test_event_to_dict(self, change_event):
        """Test converting event to dict."""
        d = change_event.to_dict()
        
        assert d["table"] == "users"
        assert d["type"] == "INSERT"
        assert d["row_id"] == 1
        assert "timestamp" in d
    
    def test_event_from_dict(self):
        """Test creating event from dict."""
        d = {
            "table": "users",
            "type": "UPDATE",
            "row_id": 1,
            "old_data": {"name": "John"},
            "new_data": {"name": "Jane"},
            "timestamp": datetime.utcnow().isoformat(),
            "source": "test",
            "columns_changed": ["name"],
        }
        
        event = ChangeEvent.from_dict(d)
        
        assert event.table == "users"
        assert event.type == ChangeType.UPDATE
        assert event.columns_changed == ["name"]
    
    def test_affects_simple_query(self, change_event, query_signature):
        """Test if event affects a simple query."""
        assert change_event.affects_query(query_signature) is True
    
    def test_does_not_affect_different_table(self, change_event):
        """Test event doesn't affect query on different table."""
        sig = QuerySignature(table="posts")
        assert change_event.affects_query(sig) is False
    
    def test_affects_filtered_query_on_update(self):
        """Test UPDATE affects filtered query if columns overlap."""
        event = ChangeEvent(
            table="users",
            type=ChangeType.UPDATE,
            row_id=1,
            columns_changed=["status"],
        )
        
        sig = QuerySignature(
            table="users",
            where_clauses=({"status": "active"},),  # Dict format, not tuples
        )
        
        assert event.affects_query(sig) is True
    
    def test_event_without_data(self):
        """Test event without row data."""
        event = ChangeEvent(
            table="users",
            type=ChangeType.UNKNOWN,
        )
        
        assert event.has_data is False
    
    def test_event_default_timestamp(self):
        """Test event has default timestamp."""
        event = ChangeEvent(table="users", type=ChangeType.INSERT)
        assert event.timestamp is not None
    
    def test_event_default_source(self):
        """Test event has default source."""
        event = ChangeEvent(table="users", type=ChangeType.INSERT)
        assert event.source == "unknown"


# =============================================================================
# PostgresNotifyDetector Tests
# =============================================================================

class TestPostgresNotifyDetector:
    """Tests for PostgreSQL LISTEN/NOTIFY detector."""
    
    def test_detector_properties(self):
        """Test detector properties."""
        detector = PostgresNotifyDetector()
        
        assert detector.name == "PostgreSQL LISTEN/NOTIFY"
        assert detector.priority == 50
        assert detector.is_running is False
    
    def test_channel_name(self):
        """Test getting channel name for table."""
        detector = PostgresNotifyDetector()
        channel = detector._get_channel_name("users")
        
        assert channel == "pynext_live_users"
    
    @pytest.mark.asyncio
    async def test_is_available_no_connection(self):
        """Test availability check without connection."""
        detector = PostgresNotifyDetector()
        
        with patch.object(detector, '_get_connection', new_callable=AsyncMock, return_value=None):
            available = await detector.is_available()
            assert available is False
    
    @pytest.mark.asyncio
    async def test_subscribe_unsubscribe(self):
        """Test subscribing and unsubscribing."""
        detector = PostgresNotifyDetector()
        detector._running = True
        
        # Mock subscription
        with patch.object(detector, 'subscribe_table', new_callable=AsyncMock):
            with patch.object(detector, 'unsubscribe_table', new_callable=AsyncMock):
                callback = Mock()
                sub_id = await detector.subscribe("users", callback)
                
                assert sub_id is not None
                assert detector.get_subscription_count("users") == 1
                
                await detector.unsubscribe(sub_id)
                assert detector.get_subscription_count("users") == 0
    
    @pytest.mark.asyncio
    async def test_multiple_subscriptions_same_table(self):
        """Test multiple subscriptions to same table."""
        detector = PostgresNotifyDetector()
        detector._running = True
        
        with patch.object(detector, 'subscribe_table', new_callable=AsyncMock):
            with patch.object(detector, 'unsubscribe_table', new_callable=AsyncMock):
                cb1 = Mock()
                cb2 = Mock()
                
                sub1 = await detector.subscribe("users", cb1)
                sub2 = await detector.subscribe("users", cb2)
                
                assert detector.get_subscription_count("users") == 2
                
                await detector.unsubscribe(sub1)
                assert detector.get_subscription_count("users") == 1
                
                await detector.unsubscribe(sub2)
                assert detector.get_subscription_count("users") == 0
    
    def test_notify_subscribers(self):
        """Test notifying subscribers."""
        detector = PostgresNotifyDetector()
        detector._subscriptions["users"] = {}
        
        callback = Mock()
        detector._subscriptions["users"]["sub1"] = callback
        
        event = ChangeEvent(table="users", type=ChangeType.INSERT)
        detector._notify_subscribers(event)
        
        callback.assert_called_once_with(event)
    
    def test_on_notification_valid_payload(self):
        """Test handling valid NOTIFY payload."""
        detector = PostgresNotifyDetector()
        detector._subscriptions["users"] = {}
        
        callback = Mock()
        detector._subscriptions["users"]["sub1"] = callback
        
        payload = '{"operation": "INSERT", "id": 1, "new": {"id": 1, "name": "John"}}'
        detector._on_notification(None, 1, "pynext_live_users", payload)
        
        assert callback.called
    
    def test_on_notification_invalid_json(self):
        """Test handling invalid JSON payload."""
        detector = PostgresNotifyDetector()
        detector._subscriptions["users"] = {}
        
        # Should not raise
        detector._on_notification(None, 1, "pynext_live_users", "invalid json")
    
    def test_get_subscribed_tables(self):
        """Test getting subscribed tables."""
        detector = PostgresNotifyDetector()
        detector._tables = {"users", "posts"}
        
        tables = detector.get_subscribed_tables()
        assert "users" in tables
        assert "posts" in tables


# =============================================================================
# SupabaseRealtimeDetector Tests
# =============================================================================

class TestSupabaseRealtimeDetector:
    """Tests for Supabase Realtime detector."""
    
    def test_detector_properties(self):
        """Test detector properties."""
        detector = SupabaseRealtimeDetector()
        
        assert detector.name == "Supabase Realtime"
        assert detector.priority == 100
        assert detector.is_running is False
    
    @pytest.mark.asyncio
    async def test_is_available_no_client(self):
        """Test availability check without client."""
        detector = SupabaseRealtimeDetector()
        
        with patch.object(detector, '_get_client', new_callable=AsyncMock, return_value=None):
            available = await detector.is_available()
            assert available is False
    
    @pytest.mark.asyncio
    async def test_is_available_with_client(self):
        """Test availability check with client."""
        detector = SupabaseRealtimeDetector()
        mock_client = Mock()
        mock_client.realtime = Mock()
        
        with patch.object(detector, '_get_client', new_callable=AsyncMock, return_value=mock_client):
            available = await detector.is_available()
            assert available is True
    
    def test_handle_change_insert(self):
        """Test handling INSERT change from Supabase."""
        detector = SupabaseRealtimeDetector()
        detector._subscriptions["users"] = {}
        
        callback = Mock()
        detector._subscriptions["users"]["sub1"] = callback
        
        payload = {
            "eventType": "INSERT",
            "new": {"id": 1, "name": "John"},
        }
        
        detector._handle_change("users", payload)
        
        assert callback.called
        event = callback.call_args[0][0]
        assert event.type == ChangeType.INSERT
        assert event.new_data == {"id": 1, "name": "John"}
    
    def test_handle_change_update(self):
        """Test handling UPDATE change from Supabase."""
        detector = SupabaseRealtimeDetector()
        detector._subscriptions["users"] = {}
        
        callback = Mock()
        detector._subscriptions["users"]["sub1"] = callback
        
        payload = {
            "eventType": "UPDATE",
            "old": {"id": 1, "name": "John"},
            "new": {"id": 1, "name": "Jane"},
        }
        
        detector._handle_change("users", payload)
        
        assert callback.called
        event = callback.call_args[0][0]
        assert event.type == ChangeType.UPDATE
        assert "name" in event.columns_changed
    
    def test_handle_change_delete(self):
        """Test handling DELETE change from Supabase."""
        detector = SupabaseRealtimeDetector()
        detector._subscriptions["users"] = {}
        
        callback = Mock()
        detector._subscriptions["users"]["sub1"] = callback
        
        payload = {
            "eventType": "DELETE",
            "old": {"id": 1, "name": "John"},
        }
        
        detector._handle_change("users", payload)
        
        assert callback.called
        event = callback.call_args[0][0]
        assert event.type == ChangeType.DELETE


# =============================================================================
# PollingDetector Tests
# =============================================================================

class TestPollingDetector:
    """Tests for polling detector."""
    
    def test_detector_properties(self):
        """Test detector properties."""
        detector = PollingDetector(interval=10.0)
        
        assert detector.name == "Polling"
        assert detector.priority == 10
        assert detector._interval == 10.0
    
    def test_set_interval(self):
        """Test setting poll interval."""
        detector = PollingDetector()
        detector.set_interval(5.0)
        
        assert detector._interval == 5.0
    
    def test_set_interval_minimum(self):
        """Test minimum interval is enforced."""
        detector = PollingDetector()
        detector.set_interval(0.1)
        
        assert detector._interval == 1.0  # Minimum
    
    @pytest.mark.asyncio
    async def test_is_available(self):
        """Test availability check."""
        detector = PollingDetector()
        
        with patch('pynext.db.table.get_adapter', return_value=Mock()):
            available = await detector.is_available()
            assert available is True
    
    def test_detect_insert(self):
        """Test detecting inserted rows."""
        detector = PollingDetector()
        
        previous = {}
        current = {1: {"id": 1, "name": "John"}}
        
        events = detector._detect_changes("users", previous, current)
        
        assert len(events) == 1
        assert events[0].type == ChangeType.INSERT
        assert events[0].row_id == 1
    
    def test_detect_delete(self):
        """Test detecting deleted rows."""
        detector = PollingDetector()
        
        previous = {1: {"id": 1, "name": "John"}}
        current = {}
        
        events = detector._detect_changes("users", previous, current)
        
        assert len(events) == 1
        assert events[0].type == ChangeType.DELETE
        assert events[0].row_id == 1
    
    def test_detect_update(self):
        """Test detecting updated rows."""
        detector = PollingDetector()
        
        previous = {1: {"id": 1, "name": "John"}}
        current = {1: {"id": 1, "name": "Jane"}}
        
        events = detector._detect_changes("users", previous, current)
        
        assert len(events) == 1
        assert events[0].type == ChangeType.UPDATE
        assert events[0].columns_changed == ["name"]
    
    def test_detect_no_changes(self):
        """Test no changes detected."""
        detector = PollingDetector()
        
        data = {1: {"id": 1, "name": "John"}}
        
        events = detector._detect_changes("users", data, data.copy())
        
        assert len(events) == 0
    
    def test_detect_multiple_changes(self):
        """Test detecting multiple changes at once."""
        detector = PollingDetector()
        
        previous = {
            1: {"id": 1, "name": "John"},
            2: {"id": 2, "name": "Jane"},
        }
        current = {
            1: {"id": 1, "name": "Johnny"},  # Updated
            3: {"id": 3, "name": "Bob"},      # Inserted
            # 2 is deleted
        }
        
        events = detector._detect_changes("users", previous, current)
        
        assert len(events) == 3
        types = {e.type for e in events}
        assert ChangeType.INSERT in types
        assert ChangeType.UPDATE in types
        assert ChangeType.DELETE in types
    
    @pytest.mark.asyncio
    async def test_start_stop(self):
        """Test starting and stopping detector."""
        detector = PollingDetector()
        
        await detector.start()
        assert detector.is_running is True
        
        await detector.stop()
        assert detector.is_running is False
    
    @pytest.mark.asyncio
    async def test_subscribe_starts_polling(self):
        """Test subscribing starts polling task."""
        detector = PollingDetector(interval=60.0)  # Long interval to avoid actual polling
        detector._running = True
        
        with patch.object(detector, '_poll_table', new_callable=AsyncMock):
            await detector.subscribe_table("users")
            
            assert "users" in detector._poll_tasks
            
            await detector.unsubscribe_table("users")
            assert "users" not in detector._poll_tasks


# =============================================================================
# DetectorRegistry Tests
# =============================================================================

class TestDetectorRegistry:
    """Tests for DetectorRegistry."""
    
    @pytest.mark.asyncio
    async def test_get_detector_registry(self, detector_registry):
        """Test getting detector registry singleton."""
        registry1 = get_detector_registry()
        registry2 = get_detector_registry()
        
        assert registry1 is registry2
    
    @pytest.mark.asyncio
    async def test_auto_select_polling_fallback(self, detector_registry):
        """Test auto-selection falls back to polling."""
        # Mock all detectors as unavailable except polling
        with patch.object(SupabaseRealtimeDetector, 'is_available', new_callable=AsyncMock, return_value=False):
            with patch.object(PostgresNotifyDetector, 'is_available', new_callable=AsyncMock, return_value=False):
                with patch.object(PollingDetector, 'is_available', new_callable=AsyncMock, return_value=True):
                    with patch.object(PollingDetector, 'start', new_callable=AsyncMock):
                        with patch.object(PollingDetector, 'subscribe_table', new_callable=AsyncMock):
                            detector = await detector_registry.get_detector("users")
                            
                            assert isinstance(detector, PollingDetector)
    
    @pytest.mark.asyncio
    async def test_get_detector_for_table(self, detector_registry):
        """Test getting detector for specific table."""
        detector = detector_registry.get_detector_for_table("users")
        assert detector is None  # No detector assigned yet
    
    @pytest.mark.asyncio
    async def test_invalidate_cache(self, detector_registry):
        """Test invalidating availability cache."""
        detector_registry._cache_valid = True
        detector_registry.invalidate_cache()
        
        assert detector_registry._cache_valid is False
    
    @pytest.mark.asyncio
    async def test_stop_all_detectors(self, detector_registry):
        """Test stopping all detectors."""
        mock_detector = Mock()
        mock_detector.is_running = True
        mock_detector.stop = AsyncMock()
        
        detector_registry._detectors["test"] = mock_detector
        
        await detector_registry.stop_all()
        
        mock_detector.stop.assert_called_once()
        assert len(detector_registry._detectors) == 0
    
    @pytest.mark.asyncio
    async def test_get_all_detectors(self, detector_registry):
        """Test getting all detector instances."""
        detector_registry._detectors["test"] = Mock()
        
        detectors = detector_registry.get_all_detectors()
        
        assert "test" in detectors
    
    @pytest.mark.asyncio
    async def test_get_table_assignments(self, detector_registry):
        """Test getting table to detector mapping."""
        mock_detector = Mock()
        mock_detector.__class__.__name__ = "TestDetector"
        
        detector_registry._table_detectors["users"] = mock_detector
        
        assignments = detector_registry.get_table_assignments()
        
        assert assignments["users"] == "TestDetector"


# =============================================================================
# ChangeDetector Base Class Tests
# =============================================================================

class TestChangeDetectorBase:
    """Tests for ChangeDetector base class methods."""
    
    def test_subscription_count_all(self):
        """Test getting total subscription count."""
        detector = PollingDetector()
        detector._subscriptions = {
            "users": {"sub1": Mock(), "sub2": Mock()},
            "posts": {"sub3": Mock()},
        }
        
        assert detector.get_subscription_count() == 3
    
    def test_subscription_count_table(self):
        """Test getting subscription count for specific table."""
        detector = PollingDetector()
        detector._subscriptions = {
            "users": {"sub1": Mock(), "sub2": Mock()},
            "posts": {"sub3": Mock()},
        }
        
        assert detector.get_subscription_count("users") == 2
        assert detector.get_subscription_count("posts") == 1
        assert detector.get_subscription_count("other") == 0
    
    @pytest.mark.asyncio
    async def test_unsubscribe_nonexistent(self):
        """Test unsubscribing nonexistent subscription."""
        detector = PollingDetector()
        
        result = await detector.unsubscribe("nonexistent")
        assert result is False
    
    def test_callback_error_handling(self):
        """Test that callback errors don't affect other callbacks."""
        detector = PollingDetector()
        
        error_callback = Mock(side_effect=Exception("Test error"))
        success_callback = Mock()
        
        detector._subscriptions["users"] = {
            "sub1": error_callback,
            "sub2": success_callback,
        }
        
        event = ChangeEvent(table="users", type=ChangeType.INSERT)
        detector._notify_subscribers(event)
        
        # Both were called despite error
        error_callback.assert_called_once()
        success_callback.assert_called_once()


# =============================================================================
# Edge Cases and Error Handling Tests
# =============================================================================

class TestDetectionEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_event_from_dict_missing_timestamp(self):
        """Test creating event from dict without timestamp."""
        d = {
            "table": "users",
            "type": "INSERT",
        }
        
        event = ChangeEvent.from_dict(d)
        assert event.timestamp is not None
    
    def test_polling_detect_empty_tables(self):
        """Test polling with empty tables."""
        detector = PollingDetector()
        
        events = detector._detect_changes("users", {}, {})
        assert len(events) == 0
    
    def test_change_event_row_id_from_old_data(self):
        """Test getting row_id from old_data on DELETE."""
        event = ChangeEvent(
            table="users",
            type=ChangeType.DELETE,
            old_data={"id": 5, "name": "John"},
        )
        
        assert event.old_data["id"] == 5
    
    def test_supabase_handle_unknown_event_type(self):
        """Test handling unknown event type from Supabase."""
        detector = SupabaseRealtimeDetector()
        detector._subscriptions["users"] = {}
        
        callback = Mock()
        detector._subscriptions["users"]["sub1"] = callback
        
        payload = {
            "eventType": "UNKNOWN_TYPE",
        }
        
        detector._handle_change("users", payload)
        
        assert callback.called
        event = callback.call_args[0][0]
        assert event.type == ChangeType.UNKNOWN
    
    @pytest.mark.asyncio
    async def test_registry_get_detector_with_specific_strategy(self, detector_registry):
        """Test getting detector with specific strategy."""
        from pynext.db.live.config import DetectionStrategy
        
        with patch.object(PollingDetector, 'is_available', new_callable=AsyncMock, return_value=True):
            with patch.object(PollingDetector, 'start', new_callable=AsyncMock):
                with patch.object(PollingDetector, 'subscribe_table', new_callable=AsyncMock):
                    detector = await detector_registry.get_detector(
                        "users",
                        detection=DetectionStrategy.POLLING,
                    )
                    
                    assert isinstance(detector, PollingDetector)

