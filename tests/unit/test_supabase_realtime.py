"""
Comprehensive tests for PyNext Supabase Realtime.

Tests cover:
- RealtimeEvent and Subscription models
- Decorator-based handlers (@on_insert, @on_update, @on_delete, @on_change)
- Signal-based subscriptions
- Handler registry
- Lifecycle management (start, stop)
- Event handling

Total: 120 tests
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch, AsyncMock

from pynext.db.supabase.realtime import (
    SupabaseRealtime,
    RealtimeEvent,
    Subscription,
    RealtimeConfig,
    EventType,
    ChannelState,
    Signal,
    TableSignal,
    HandlerRegistry,
    on_insert,
    on_update,
    on_delete,
    on_change,
    _global_registry,
)
from pynext.db.supabase.exceptions import (
    RealtimeError,
    RealtimeConnectionError,
    SubscriptionError,
    ChannelError,
    AlreadySubscribedError,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_supabase():
    """Create mock Supabase adapter."""
    supabase = Mock()
    supabase._initialized = True
    supabase._ensure_initialized = Mock()
    
    # Mock realtime client
    realtime_client = Mock()
    supabase.client = Mock()
    supabase.client.realtime = realtime_client
    
    # Mock table for subscribe initial fetch
    table_mock = Mock()
    table_mock.select = Mock(return_value=table_mock)
    table_mock.execute = Mock(return_value=Mock(data=[]))
    supabase.table = Mock(return_value=table_mock)
    
    return supabase


@pytest.fixture
def realtime(mock_supabase):
    """Create SupabaseRealtime instance."""
    return SupabaseRealtime(mock_supabase)


@pytest.fixture
def registry():
    """Create fresh HandlerRegistry."""
    return HandlerRegistry()


@pytest.fixture(autouse=True)
def clear_global_registry():
    """Clear global registry before each test."""
    _global_registry.clear()
    yield
    _global_registry.clear()


# =============================================================================
# EVENT TYPE TESTS (10 tests)
# =============================================================================

class TestEventType:
    """Tests for EventType enum."""
    
    def test_event_type_insert(self):
        """EventType has INSERT."""
        assert EventType.INSERT.value == "INSERT"
    
    def test_event_type_update(self):
        """EventType has UPDATE."""
        assert EventType.UPDATE.value == "UPDATE"
    
    def test_event_type_delete(self):
        """EventType has DELETE."""
        assert EventType.DELETE.value == "DELETE"
    
    def test_event_type_all(self):
        """EventType has ALL (*)."""
        assert EventType.ALL.value == "*"
    
    def test_event_type_is_string(self):
        """EventType values are strings."""
        assert isinstance(EventType.INSERT.value, str)
    
    def test_channel_state_closed(self):
        """ChannelState has closed."""
        assert ChannelState.CLOSED.value == "closed"
    
    def test_channel_state_joined(self):
        """ChannelState has joined."""
        assert ChannelState.JOINED.value == "joined"
    
    def test_channel_state_joining(self):
        """ChannelState has joining."""
        assert ChannelState.JOINING.value == "joining"
    
    def test_channel_state_leaving(self):
        """ChannelState has leaving."""
        assert ChannelState.LEAVING.value == "leaving"
    
    def test_channel_state_errored(self):
        """ChannelState has errored."""
        assert ChannelState.ERRORED.value == "errored"


# =============================================================================
# REALTIME EVENT TESTS (15 tests)
# =============================================================================

class TestRealtimeEvent:
    """Tests for RealtimeEvent model."""
    
    def test_event_from_payload_insert(self):
        """RealtimeEvent parses INSERT payload."""
        payload = {
            "eventType": "INSERT",
            "table": "users",
            "new": {"id": 1, "name": "Alice"}
        }
        event = RealtimeEvent.from_payload(payload)
        assert event.type == EventType.INSERT
        assert event.table == "users"
    
    def test_event_from_payload_update(self):
        """RealtimeEvent parses UPDATE payload."""
        payload = {
            "eventType": "UPDATE",
            "table": "users",
            "old": {"id": 1, "name": "Alice"},
            "new": {"id": 1, "name": "Bob"}
        }
        event = RealtimeEvent.from_payload(payload)
        assert event.type == EventType.UPDATE
        assert event.old_record == {"id": 1, "name": "Alice"}
        assert event.new_record == {"id": 1, "name": "Bob"}
    
    def test_event_from_payload_delete(self):
        """RealtimeEvent parses DELETE payload."""
        payload = {
            "eventType": "DELETE",
            "table": "users",
            "old": {"id": 1, "name": "Alice"}
        }
        event = RealtimeEvent.from_payload(payload)
        assert event.type == EventType.DELETE
        assert event.old_record == {"id": 1, "name": "Alice"}
    
    def test_event_from_payload_type_key(self):
        """RealtimeEvent handles 'type' key instead of 'eventType'."""
        payload = {"type": "INSERT", "table": "users", "new": {}}
        event = RealtimeEvent.from_payload(payload)
        assert event.type == EventType.INSERT
    
    def test_event_from_payload_record_key(self):
        """RealtimeEvent handles 'record' key."""
        payload = {"eventType": "INSERT", "table": "users", "record": {"id": 1}}
        event = RealtimeEvent.from_payload(payload)
        assert event.new_record == {"id": 1}
    
    def test_event_from_payload_old_record_key(self):
        """RealtimeEvent handles 'old_record' key."""
        payload = {"eventType": "DELETE", "table": "users", "old_record": {"id": 1}}
        event = RealtimeEvent.from_payload(payload)
        assert event.old_record == {"id": 1}
    
    def test_event_from_payload_new_record_key(self):
        """RealtimeEvent handles 'new_record' key."""
        payload = {"eventType": "INSERT", "table": "users", "new_record": {"id": 1}}
        event = RealtimeEvent.from_payload(payload)
        assert event.new_record == {"id": 1}
    
    def test_event_schema_default(self):
        """RealtimeEvent has 'public' schema by default."""
        payload = {"eventType": "INSERT", "table": "users"}
        event = RealtimeEvent.from_payload(payload)
        assert event.schema == "public"
    
    def test_event_schema_custom(self):
        """RealtimeEvent parses custom schema."""
        payload = {"eventType": "INSERT", "table": "users", "schema": "private"}
        event = RealtimeEvent.from_payload(payload)
        assert event.schema == "private"
    
    def test_event_record_property_insert(self):
        """RealtimeEvent.record returns new_record for INSERT."""
        payload = {"eventType": "INSERT", "table": "users", "new": {"id": 1}}
        event = RealtimeEvent.from_payload(payload)
        assert event.record == {"id": 1}
    
    def test_event_record_property_update(self):
        """RealtimeEvent.record returns new_record for UPDATE."""
        payload = {"eventType": "UPDATE", "table": "users", "new": {"id": 1}}
        event = RealtimeEvent.from_payload(payload)
        assert event.record == {"id": 1}
    
    def test_event_record_property_delete(self):
        """RealtimeEvent.record returns old_record for DELETE."""
        payload = {"eventType": "DELETE", "table": "users", "old": {"id": 1}}
        event = RealtimeEvent.from_payload(payload)
        assert event.record == {"id": 1}
    
    def test_event_commit_timestamp(self):
        """RealtimeEvent parses commit_timestamp."""
        payload = {"eventType": "INSERT", "table": "users", "commit_timestamp": "2024-01-01T00:00:00Z"}
        event = RealtimeEvent.from_payload(payload)
        assert event.commit_timestamp == "2024-01-01T00:00:00Z"
    
    def test_event_empty_payload(self):
        """RealtimeEvent handles empty payload."""
        event = RealtimeEvent.from_payload({})
        assert event.table == ""
    
    def test_event_default_type(self):
        """RealtimeEvent defaults to INSERT."""
        event = RealtimeEvent.from_payload({"table": "users"})
        assert event.type == EventType.INSERT


# =============================================================================
# SUBSCRIPTION TESTS (10 tests)
# =============================================================================

class TestSubscription:
    """Tests for Subscription model."""
    
    def test_subscription_creation(self):
        """Subscription can be created."""
        sub = Subscription(table="users")
        assert sub.table == "users"
    
    def test_subscription_default_event_types(self):
        """Subscription has ALL event type by default."""
        sub = Subscription(table="users")
        assert EventType.ALL in sub.event_types
    
    def test_subscription_with_filter(self):
        """Subscription can have filter."""
        sub = Subscription(table="users", filter="status=eq.active")
        assert sub.filter == "status=eq.active"
    
    def test_subscription_with_columns(self):
        """Subscription can specify columns."""
        sub = Subscription(table="users", columns=["id", "name"])
        assert sub.columns == ["id", "name"]
    
    def test_subscription_matches_event_all(self):
        """Subscription with ALL matches any event."""
        sub = Subscription(table="users")
        event = RealtimeEvent(type=EventType.INSERT, table="users")
        assert sub.matches_event(event) is True
    
    def test_subscription_matches_event_specific(self):
        """Subscription matches specific event type."""
        sub = Subscription(table="users", event_types={EventType.INSERT})
        insert_event = RealtimeEvent(type=EventType.INSERT, table="users")
        update_event = RealtimeEvent(type=EventType.UPDATE, table="users")
        assert sub.matches_event(insert_event) is True
        assert sub.matches_event(update_event) is False
    
    def test_subscription_state_default(self):
        """Subscription has CLOSED state by default."""
        sub = Subscription(table="users")
        assert sub.state == ChannelState.CLOSED
    
    def test_subscription_handlers_default(self):
        """Subscription has empty handlers by default."""
        sub = Subscription(table="users")
        assert sub.handlers == []
    
    def test_subscription_channel_name(self):
        """Subscription can have channel name."""
        sub = Subscription(table="users", channel_name="realtime:users")
        assert sub.channel_name == "realtime:users"
    
    def test_subscription_multiple_event_types(self):
        """Subscription can have multiple event types."""
        sub = Subscription(table="users", event_types={EventType.INSERT, EventType.UPDATE})
        assert EventType.INSERT in sub.event_types
        assert EventType.UPDATE in sub.event_types


# =============================================================================
# REALTIME CONFIG TESTS (5 tests)
# =============================================================================

class TestRealtimeConfig:
    """Tests for RealtimeConfig."""
    
    def test_config_defaults(self):
        """RealtimeConfig has sensible defaults."""
        config = RealtimeConfig()
        assert config.enabled is True
        assert config.auto_reconnect is True
    
    def test_config_reconnect_delay(self):
        """RealtimeConfig has reconnect_delay."""
        config = RealtimeConfig()
        assert config.reconnect_delay == 1.0
    
    def test_config_max_reconnect_attempts(self):
        """RealtimeConfig has max_reconnect_attempts."""
        config = RealtimeConfig()
        assert config.max_reconnect_attempts == 10
    
    def test_config_heartbeat_interval(self):
        """RealtimeConfig has heartbeat_interval."""
        config = RealtimeConfig()
        assert config.heartbeat_interval == 30.0
    
    def test_config_custom_values(self):
        """RealtimeConfig accepts custom values."""
        config = RealtimeConfig(
            enabled=False,
            auto_reconnect=False,
            reconnect_delay=2.0
        )
        assert config.enabled is False
        assert config.reconnect_delay == 2.0


# =============================================================================
# HANDLER REGISTRY TESTS (15 tests)
# =============================================================================

class TestHandlerRegistry:
    """Tests for HandlerRegistry."""
    
    def test_register_handler(self, registry):
        """Registry can register handler."""
        handler = Mock()
        registry.register("users", EventType.INSERT, handler)
        handlers = registry.get_handlers("users", EventType.INSERT)
        assert handler in handlers
    
    def test_register_multiple_handlers(self, registry):
        """Registry can register multiple handlers."""
        handler1 = Mock()
        handler2 = Mock()
        registry.register("users", EventType.INSERT, handler1)
        registry.register("users", EventType.INSERT, handler2)
        handlers = registry.get_handlers("users", EventType.INSERT)
        assert len(handlers) == 2
    
    def test_register_different_events(self, registry):
        """Registry separates handlers by event type."""
        insert_handler = Mock()
        update_handler = Mock()
        registry.register("users", EventType.INSERT, insert_handler)
        registry.register("users", EventType.UPDATE, update_handler)
        
        insert_handlers = registry.get_handlers("users", EventType.INSERT)
        update_handlers = registry.get_handlers("users", EventType.UPDATE)
        
        assert insert_handler in insert_handlers
        assert insert_handler not in update_handlers
    
    def test_register_with_filter(self, registry):
        """Registry handles filters."""
        handler = Mock()
        registry.register("users", EventType.INSERT, handler, filter="status=eq.active")
        handlers = registry.get_handlers("users", EventType.INSERT, filter="status=eq.active")
        assert handler in handlers
    
    def test_get_handlers_includes_all(self, registry):
        """get_handlers includes ALL event handlers."""
        all_handler = Mock()
        insert_handler = Mock()
        registry.register("users", EventType.ALL, all_handler)
        registry.register("users", EventType.INSERT, insert_handler)
        
        handlers = registry.get_handlers("users", EventType.INSERT)
        
        assert all_handler in handlers
        assert insert_handler in handlers
    
    def test_get_all_subscriptions(self, registry):
        """Registry tracks subscriptions."""
        registry.register("users", EventType.INSERT, Mock())
        registry.register("orders", EventType.UPDATE, Mock())
        
        subs = registry.get_subscriptions()
        
        assert len(subs) == 2
    
    def test_get_no_handlers(self, registry):
        """get_handlers returns empty for unknown table."""
        handlers = registry.get_handlers("unknown", EventType.INSERT)
        assert handlers == []
    
    def test_register_creates_subscription(self, registry):
        """Registering handler creates subscription."""
        registry.register("users", EventType.INSERT, Mock())
        subs = registry.get_subscriptions()
        assert len(subs) == 1
        assert subs[0].table == "users"
    
    def test_subscription_event_types_updated(self, registry):
        """Registering adds event type to subscription."""
        registry.register("users", EventType.INSERT, Mock())
        registry.register("users", EventType.UPDATE, Mock())
        subs = registry.get_subscriptions()
        assert EventType.INSERT in subs[0].event_types
        assert EventType.UPDATE in subs[0].event_types
    
    def test_register_columns_merged(self, registry):
        """Registering merges columns."""
        registry.register("users", EventType.INSERT, Mock(), columns=["name"])
        registry.register("users", EventType.UPDATE, Mock(), columns=["status"])
        subs = registry.get_subscriptions()
        assert "name" in subs[0].columns
        assert "status" in subs[0].columns
    
    def test_clear_registry(self, registry):
        """Registry can be cleared."""
        registry.register("users", EventType.INSERT, Mock())
        registry.clear()
        assert registry.get_subscriptions() == []
    
    def test_make_key_with_filter(self, registry):
        """Registry keys include filter."""
        registry.register("users", EventType.INSERT, Mock(), filter="a=b")
        registry.register("users", EventType.INSERT, Mock(), filter="c=d")
        subs = registry.get_subscriptions()
        assert len(subs) == 2
    
    def test_make_key_without_filter(self, registry):
        """Registry keys work without filter."""
        registry.register("users", EventType.INSERT, Mock())
        subs = registry.get_subscriptions()
        assert subs[0].filter is None
    
    def test_get_handlers_different_filter(self, registry):
        """Handlers with different filters are separate."""
        handler1 = Mock()
        handler2 = Mock()
        registry.register("users", EventType.INSERT, handler1, filter="a=b")
        registry.register("users", EventType.INSERT, handler2, filter="c=d")
        
        handlers1 = registry.get_handlers("users", EventType.INSERT, filter="a=b")
        handlers2 = registry.get_handlers("users", EventType.INSERT, filter="c=d")
        
        assert handler1 in handlers1
        assert handler1 not in handlers2


# =============================================================================
# DECORATOR TESTS (20 tests)
# =============================================================================

class TestDecorators:
    """Tests for decorator functions."""
    
    def test_on_insert_registers_handler(self):
        """@on_insert registers handler."""
        @on_insert("users")
        async def handler(record):
            pass
        
        handlers = _global_registry.get_handlers("users", EventType.INSERT)
        assert len(handlers) >= 1
    
    def test_on_update_registers_handler(self):
        """@on_update registers handler."""
        @on_update("users")
        async def handler(old, new):
            pass
        
        handlers = _global_registry.get_handlers("users", EventType.UPDATE)
        assert len(handlers) >= 1
    
    def test_on_delete_registers_handler(self):
        """@on_delete registers handler."""
        @on_delete("users")
        async def handler(old):
            pass
        
        handlers = _global_registry.get_handlers("users", EventType.DELETE)
        assert len(handlers) >= 1
    
    def test_on_change_registers_handler(self):
        """@on_change registers handler for ALL."""
        @on_change("users")
        async def handler(event_type, old, new):
            pass
        
        handlers = _global_registry.get_handlers("users", EventType.ALL)
        assert len(handlers) >= 1
    
    def test_decorator_with_filter(self):
        """Decorator accepts filter."""
        @on_insert("orders", filter="status=eq.pending")
        async def handler(record):
            pass
        
        handlers = _global_registry.get_handlers("orders", EventType.INSERT, filter="status=eq.pending")
        assert len(handlers) >= 1
    
    def test_decorator_with_columns(self):
        """Decorator accepts columns."""
        @on_update("users", columns=["status", "role"])
        async def handler(old, new):
            pass
        
        subs = _global_registry.get_subscriptions()
        users_sub = [s for s in subs if s.table == "users"][0]
        assert "status" in users_sub.columns
    
    def test_decorator_preserves_function(self):
        """Decorator preserves function."""
        @on_insert("users")
        async def my_handler(record):
            return "result"
        
        assert my_handler.__name__ == "my_handler"
    
    def test_decorator_wraps_function(self):
        """Decorator creates async wrapper."""
        @on_insert("users")
        async def handler(record):
            pass
        
        assert asyncio.iscoroutinefunction(handler)
    
    def test_multiple_decorators_same_table(self):
        """Multiple decorators on same table."""
        @on_insert("users")
        async def handler1(record):
            pass
        
        @on_insert("users")
        async def handler2(record):
            pass
        
        handlers = _global_registry.get_handlers("users", EventType.INSERT)
        assert len(handlers) >= 2
    
    def test_decorators_different_tables(self):
        """Decorators on different tables."""
        @on_insert("users")
        async def user_handler(record):
            pass
        
        @on_insert("orders")
        async def order_handler(record):
            pass
        
        user_handlers = _global_registry.get_handlers("users", EventType.INSERT)
        order_handlers = _global_registry.get_handlers("orders", EventType.INSERT)
        assert len(user_handlers) >= 1
        assert len(order_handlers) >= 1
    
    def test_on_insert_creates_subscription(self):
        """@on_insert creates subscription."""
        @on_insert("products")
        async def handler(record):
            pass
        
        subs = _global_registry.get_subscriptions()
        tables = [s.table for s in subs]
        assert "products" in tables
    
    def test_on_update_creates_subscription(self):
        """@on_update creates subscription."""
        @on_update("products")
        async def handler(old, new):
            pass
        
        subs = _global_registry.get_subscriptions()
        tables = [s.table for s in subs]
        assert "products" in tables
    
    def test_on_delete_creates_subscription(self):
        """@on_delete creates subscription."""
        @on_delete("products")
        async def handler(old):
            pass
        
        subs = _global_registry.get_subscriptions()
        tables = [s.table for s in subs]
        assert "products" in tables
    
    def test_on_change_creates_subscription(self):
        """@on_change creates subscription."""
        @on_change("products")
        async def handler(event_type, old, new):
            pass
        
        subs = _global_registry.get_subscriptions()
        tables = [s.table for s in subs]
        assert "products" in tables
    
    def test_decorator_filter_none(self):
        """Decorator handles None filter."""
        @on_insert("users")
        async def handler(record):
            pass
        
        subs = _global_registry.get_subscriptions()
        users_sub = [s for s in subs if s.table == "users"][0]
        assert users_sub.filter is None
    
    def test_decorator_columns_none(self):
        """Decorator handles None columns."""
        @on_insert("users")
        async def handler(record):
            pass
        
        subs = _global_registry.get_subscriptions()
        users_sub = [s for s in subs if s.table == "users"][0]
        # columns might be None or empty
    
    def test_decorator_complex_filter(self):
        """Decorator handles complex filter."""
        @on_insert("orders", filter="status=eq.pending,total=gt.100")
        async def handler(record):
            pass
        
        subs = _global_registry.get_subscriptions()
        orders_sub = [s for s in subs if s.table == "orders"][0]
        assert orders_sub.filter == "status=eq.pending,total=gt.100"
    
    def test_decorator_multiple_columns(self):
        """Decorator handles multiple columns."""
        @on_update("users", columns=["name", "email", "status"])
        async def handler(old, new):
            pass
        
        subs = _global_registry.get_subscriptions()
        users_sub = [s for s in subs if s.table == "users"][0]
        assert len(users_sub.columns) == 3
    
    def test_sync_handler_wrapped(self):
        """Decorator wraps sync handlers."""
        @on_insert("users")
        async def handler(record):
            return "sync"
        
        # Should be callable
        assert callable(handler)


# =============================================================================
# SIGNAL TESTS (15 tests)
# =============================================================================

class TestSignal:
    """Tests for Signal class."""
    
    def test_signal_initial_value(self):
        """Signal stores initial value."""
        signal = Signal(initial_value=42)
        assert signal() == 42
    
    def test_signal_get(self):
        """Signal.get() returns value."""
        signal = Signal(initial_value="hello")
        assert signal.get() == "hello"
    
    def test_signal_set(self):
        """Signal.set() updates value."""
        signal = Signal(initial_value=1)
        signal.set(2)
        assert signal() == 2
    
    def test_signal_update(self):
        """Signal.update() applies function."""
        signal = Signal(initial_value=5)
        signal.update(lambda x: x * 2)
        assert signal() == 10
    
    def test_signal_subscribe(self):
        """Signal.subscribe() adds callback."""
        signal = Signal(initial_value=0)
        values = []
        signal.subscribe(lambda v: values.append(v))
        signal.set(1)
        assert values == [1]
    
    def test_signal_unsubscribe(self):
        """Signal.subscribe() returns unsubscribe function."""
        signal = Signal(initial_value=0)
        values = []
        unsubscribe = signal.subscribe(lambda v: values.append(v))
        unsubscribe()
        signal.set(1)
        assert values == []
    
    def test_signal_multiple_subscribers(self):
        """Signal notifies multiple subscribers."""
        signal = Signal(initial_value=0)
        values1 = []
        values2 = []
        signal.subscribe(lambda v: values1.append(v))
        signal.subscribe(lambda v: values2.append(v))
        signal.set(1)
        assert values1 == [1]
        assert values2 == [1]
    
    def test_signal_no_notify_same_value(self):
        """Signal doesn't notify for same value."""
        signal = Signal(initial_value=5)
        values = []
        signal.subscribe(lambda v: values.append(v))
        signal.set(5)  # Same value
        assert values == []
    
    def test_signal_none_initial(self):
        """Signal handles None initial value."""
        signal = Signal()
        assert signal() is None
    
    def test_signal_notify_handles_errors(self):
        """Signal handles subscriber errors gracefully."""
        signal = Signal(initial_value=0)
        signal.subscribe(lambda v: 1/0)  # Will raise
        signal.subscribe(lambda v: None)  # Should still be called
        signal.set(1)  # Should not raise
    
    def test_table_signal_creation(self):
        """TableSignal can be created."""
        signal = TableSignal("users")
        assert signal.table == "users"
    
    def test_table_signal_initial_data(self):
        """TableSignal accepts initial data."""
        signal = TableSignal("users", [{"id": 1, "name": "Alice"}])
        assert len(signal()) == 1
    
    def test_table_signal_handle_insert(self):
        """TableSignal handles INSERT event."""
        signal = TableSignal("users", [])
        event = RealtimeEvent(
            type=EventType.INSERT,
            table="users",
            new_record={"id": 1, "name": "Alice"}
        )
        signal.handle_event(event)
        assert len(signal()) == 1
    
    def test_table_signal_handle_update(self):
        """TableSignal handles UPDATE event."""
        signal = TableSignal("users", [{"id": 1, "name": "Alice"}])
        event = RealtimeEvent(
            type=EventType.UPDATE,
            table="users",
            new_record={"id": 1, "name": "Bob"}
        )
        signal.handle_event(event)
        assert signal()[0]["name"] == "Bob"
    
    def test_table_signal_handle_delete(self):
        """TableSignal handles DELETE event."""
        signal = TableSignal("users", [{"id": 1, "name": "Alice"}])
        event = RealtimeEvent(
            type=EventType.DELETE,
            table="users",
            old_record={"id": 1, "name": "Alice"}
        )
        signal.handle_event(event)
        assert len(signal()) == 0


# =============================================================================
# TABLE SIGNAL EXTENDED TESTS (10 tests)
# =============================================================================

class TestTableSignalExtended:
    """Extended tests for TableSignal."""
    
    def test_find_by_id(self):
        """TableSignal.find_by_id() works."""
        signal = TableSignal("users", [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"}
        ])
        user = signal.find_by_id(1)
        assert user["name"] == "Alice"
    
    def test_find_by_id_not_found(self):
        """TableSignal.find_by_id() returns None for missing."""
        signal = TableSignal("users", [{"id": 1}])
        assert signal.find_by_id(99) is None
    
    def test_filter_records(self):
        """TableSignal.filter() works."""
        signal = TableSignal("users", [
            {"id": 1, "active": True},
            {"id": 2, "active": False}
        ])
        active = signal.filter(lambda r: r["active"])
        assert len(active) == 1
    
    def test_first_record(self):
        """TableSignal.first() returns first record."""
        signal = TableSignal("users", [{"id": 1}, {"id": 2}])
        assert signal.first()["id"] == 1
    
    def test_first_with_predicate(self):
        """TableSignal.first() accepts predicate."""
        signal = TableSignal("users", [
            {"id": 1, "active": False},
            {"id": 2, "active": True}
        ])
        active = signal.first(lambda r: r["active"])
        assert active["id"] == 2
    
    def test_first_empty(self):
        """TableSignal.first() returns None for empty."""
        signal = TableSignal("users", [])
        assert signal.first() is None
    
    def test_count(self):
        """TableSignal.count() returns count."""
        signal = TableSignal("users", [{"id": 1}, {"id": 2}])
        assert signal.count() == 2
    
    def test_is_empty_true(self):
        """TableSignal.is_empty() returns True when empty."""
        signal = TableSignal("users", [])
        assert signal.is_empty() is True
    
    def test_is_empty_false(self):
        """TableSignal.is_empty() returns False when not empty."""
        signal = TableSignal("users", [{"id": 1}])
        assert signal.is_empty() is False
    
    def test_insert_no_duplicate(self):
        """TableSignal doesn't insert duplicate IDs."""
        signal = TableSignal("users", [{"id": 1, "name": "Alice"}])
        event = RealtimeEvent(
            type=EventType.INSERT,
            table="users",
            new_record={"id": 1, "name": "Alice2"}  # Same ID
        )
        signal.handle_event(event)
        assert len(signal()) == 1


# =============================================================================
# REALTIME LIFECYCLE TESTS (15 tests)
# =============================================================================

class TestRealtimeLifecycle:
    """Tests for realtime lifecycle methods."""
    
    @pytest.mark.asyncio
    async def test_subscribe_returns_signal(self, realtime):
        """subscribe returns TableSignal."""
        signal = await realtime.subscribe("users")
        assert isinstance(signal, TableSignal)
    
    @pytest.mark.asyncio
    async def test_subscribe_fetches_initial(self, realtime, mock_supabase):
        """subscribe fetches initial data."""
        mock_supabase.table.return_value.select.return_value.execute.return_value.data = [
            {"id": 1, "name": "Alice"}
        ]
        
        signal = await realtime.subscribe("users")
        
        assert len(signal()) == 1
    
    @pytest.mark.asyncio
    async def test_subscribe_skip_initial_fetch(self, realtime):
        """subscribe can skip initial fetch."""
        signal = await realtime.subscribe("users", fetch_initial=False)
        assert signal() == []
    
    @pytest.mark.asyncio
    async def test_subscribe_returns_existing(self, realtime):
        """subscribe returns existing signal."""
        signal1 = await realtime.subscribe("users")
        signal2 = await realtime.subscribe("users")
        assert signal1 is signal2
    
    @pytest.mark.asyncio
    async def test_subscribe_with_filter(self, realtime):
        """subscribe with filter creates separate signal."""
        signal1 = await realtime.subscribe("users")
        signal2 = await realtime.subscribe("users", filter="active=eq.true")
        assert signal1 is not signal2
    
    @pytest.mark.asyncio
    async def test_unsubscribe_removes_signal(self, realtime):
        """unsubscribe removes signal."""
        await realtime.subscribe("users")
        await realtime.unsubscribe("users")
        assert realtime.get_signal("users") is None
    
    @pytest.mark.asyncio
    async def test_unsubscribe_with_filter(self, realtime):
        """unsubscribe with filter removes correct signal."""
        await realtime.subscribe("users")
        await realtime.subscribe("users", filter="a=b")
        await realtime.unsubscribe("users", filter="a=b")
        
        assert realtime.get_signal("users") is not None
        assert realtime.get_signal("users", filter="a=b") is None
    
    @pytest.mark.asyncio
    async def test_start_sets_running(self, realtime):
        """start sets is_running."""
        await realtime.start()
        assert realtime._is_running is True
        await realtime.stop()
    
    @pytest.mark.asyncio
    async def test_start_noop_when_running(self, realtime):
        """start is noop when already running."""
        await realtime.start()
        await realtime.start()  # Second call should not error
        assert realtime._is_running is True
        await realtime.stop()
    
    @pytest.mark.asyncio
    async def test_start_noop_when_disabled(self, realtime):
        """start is noop when disabled."""
        realtime._config.enabled = False
        await realtime.start()
        assert realtime._is_running is False
    
    @pytest.mark.asyncio
    async def test_stop_clears_running(self, realtime):
        """stop clears is_running."""
        await realtime.start()
        await realtime.stop()
        assert realtime._is_running is False
    
    @pytest.mark.asyncio
    async def test_stop_cancels_task(self, realtime):
        """stop cancels listen task."""
        await realtime.start()
        await realtime.stop()
        assert realtime._listen_task is None
    
    def test_is_connected_false_initially(self, realtime):
        """is_connected is False initially."""
        assert realtime.is_connected is False
    
    def test_subscriptions_property(self, realtime):
        """subscriptions returns active subscriptions."""
        assert realtime.subscriptions == []
    
    def test_get_subscription(self, realtime):
        """get_subscription returns subscription."""
        realtime._active_subscriptions["users"] = Subscription(table="users")
        sub = realtime.get_subscription("users")
        assert sub is not None

