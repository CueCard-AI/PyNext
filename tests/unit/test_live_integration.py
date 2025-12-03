"""
Comprehensive Integration Tests for PyNext Live Queries.

Tests the complete live query system end-to-end:
- Full subscription lifecycle
- Change detection to client delivery
- Error recovery and resilience
- Performance and concurrency

Target: 100 tests
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from dataclasses import dataclass

from pynext.db.live import (
    LiveQuery,
    LiveQueryState,
    live,
)
from pynext.db.live.config import (
    LiveQueryConfig,
    QuerySignature,
    TransportType,
    DetectionStrategy,
    UpdateGranularity,
)
from pynext.db.live.detection.base import ChangeEvent, ChangeType
from pynext.db.live.subscriptions import (
    SubscriptionManager,
    Subscription,
    QueryGroup,
    ClientSubscription,
    get_subscription_manager,
    reset_subscription_manager,
)
from pynext.db.live.updates.surgical import SurgicalUpdate
from pynext.db.live.updates.refresh import FullRefresh
from pynext.db.live.updates.selector import StrategySelector


# =============================================================================
# Mock Models
# =============================================================================

@dataclass
class MockUser:
    """Mock user model for testing."""
    id: int
    name: str
    status: str = "active"
    
    @classmethod
    def _from_row(cls, data: Dict[str, Any]) -> "MockUser":
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            status=data.get("status", "active"),
        )


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def config():
    """Create default live query config."""
    return LiveQueryConfig()


@pytest.fixture
def query_signature():
    """Create a sample query signature."""
    return QuerySignature(table="users")


@pytest.fixture
async def clean_state():
    """Ensure clean state before each test."""
    await reset_subscription_manager()
    yield
    await reset_subscription_manager()


# =============================================================================
# QuerySignature Tests
# =============================================================================

class TestQuerySignature:
    """Tests for QuerySignature."""
    
    def test_create_simple_signature(self):
        """Test creating a simple query signature."""
        sig = QuerySignature(table="users")
        
        assert sig.table == "users"
        assert sig.is_simple is True
    
    def test_signature_with_where(self):
        """Test signature with WHERE clause."""
        sig = QuerySignature(
            table="users",
            where_clauses=({"status": "active"},),
        )
        
        assert sig.has_filters is True
    
    def test_signature_with_limit(self):
        """Test signature with LIMIT."""
        sig = QuerySignature(table="users", limit=10)
        
        assert sig.has_limit is True
        assert sig.limit == 10
    
    def test_signature_with_order(self):
        """Test signature with ORDER BY."""
        sig = QuerySignature(table="users", order_by="name")
        
        assert sig.has_ordering is True
    
    def test_signature_hash(self):
        """Test signature hash for deduplication."""
        sig1 = QuerySignature(table="users")
        sig2 = QuerySignature(table="users")
        sig3 = QuerySignature(table="posts")
        
        assert hash(sig1) == hash(sig2)
        assert hash(sig1) != hash(sig3)
    
    def test_signature_equality(self):
        """Test signature equality."""
        sig1 = QuerySignature(table="users", limit=10)
        sig2 = QuerySignature(table="users", limit=10)
        sig3 = QuerySignature(table="users", limit=20)
        
        assert sig1 == sig2
        assert sig1 != sig3


# =============================================================================
# Subscription Tests
# =============================================================================

class TestSubscription:
    """Tests for Subscription dataclass."""
    
    def test_create_subscription(self, query_signature, config):
        """Test creating a subscription."""
        callback = Mock()
        
        sub = Subscription(
            id="sub_1",
            client_id="client_1",
            query_signature=query_signature,
            callback=callback,
            config=config,
        )
        
        assert sub.id == "sub_1"
        assert sub.client_id == "client_1"
        assert sub.update_count == 0
    
    def test_subscription_on_change(self, query_signature, config):
        """Test subscription handles change events."""
        callback = Mock()
        
        sub = Subscription(
            id="sub_1",
            client_id="client_1",
            query_signature=query_signature,
            callback=callback,
            config=config,
        )
        
        event = ChangeEvent(table="users", type=ChangeType.INSERT, row_id=1)
        sub.on_change(event)
        
        callback.assert_called_once_with(event)
        assert sub.update_count == 1
        assert sub.last_update is not None
    
    def test_subscription_callback_error_handled(self, query_signature, config):
        """Test callback errors don't crash."""
        callback = Mock(side_effect=Exception("Callback error"))
        
        sub = Subscription(
            id="sub_1",
            client_id="client_1",
            query_signature=query_signature,
            callback=callback,
            config=config,
        )
        
        event = ChangeEvent(table="users", type=ChangeType.INSERT, row_id=1)
        
        # Should not raise
        sub.on_change(event)
        
        # Still counts as update
        assert sub.update_count == 1


# =============================================================================
# QueryGroup Tests
# =============================================================================

class TestQueryGroup:
    """Tests for QueryGroup."""
    
    def test_create_query_group(self, query_signature):
        """Test creating a query group."""
        group = QueryGroup(signature=query_signature)
        
        assert group.signature == query_signature
        assert group.subscription_count == 0
        assert group.is_empty is True
    
    def test_add_subscription(self, query_signature, config):
        """Test adding subscription to group."""
        group = QueryGroup(signature=query_signature)
        
        sub = Subscription(
            id="sub_1",
            client_id="client_1",
            query_signature=query_signature,
            callback=Mock(),
            config=config,
        )
        
        group.add_subscription(sub)
        
        assert group.subscription_count == 1
        assert group.is_empty is False
    
    def test_remove_subscription(self, query_signature, config):
        """Test removing subscription from group."""
        group = QueryGroup(signature=query_signature)
        
        sub = Subscription(
            id="sub_1",
            client_id="client_1",
            query_signature=query_signature,
            callback=Mock(),
            config=config,
        )
        
        group.add_subscription(sub)
        removed = group.remove_subscription("sub_1")
        
        assert removed == sub
        assert group.is_empty is True
    
    def test_on_change_routes_to_subscriptions(self, query_signature, config):
        """Test on_change routes to all subscriptions."""
        group = QueryGroup(signature=query_signature)
        
        callback1 = Mock()
        callback2 = Mock()
        
        sub1 = Subscription(
            id="sub_1",
            client_id="client_1",
            query_signature=query_signature,
            callback=callback1,
            config=config,
        )
        sub2 = Subscription(
            id="sub_2",
            client_id="client_2",
            query_signature=query_signature,
            callback=callback2,
            config=config,
        )
        
        group.add_subscription(sub1)
        group.add_subscription(sub2)
        
        event = ChangeEvent(table="users", type=ChangeType.INSERT, row_id=1)
        group.on_change(event)
        
        callback1.assert_called_once()
        callback2.assert_called_once()


# =============================================================================
# ClientSubscription Tests
# =============================================================================

class TestClientSubscription:
    """Tests for ClientSubscription."""
    
    def test_create_client_subscription(self):
        """Test creating client subscription."""
        client_sub = ClientSubscription("client_1")
        
        assert client_sub.client_id == "client_1"
        assert client_sub.count == 0
    
    def test_add_subscription(self):
        """Test adding subscription to client."""
        client_sub = ClientSubscription("client_1")
        
        client_sub.add("sub_1")
        client_sub.add("sub_2")
        
        assert client_sub.count == 2
    
    def test_remove_subscription(self):
        """Test removing subscription from client."""
        client_sub = ClientSubscription("client_1")
        
        client_sub.add("sub_1")
        client_sub.remove("sub_1")
        
        assert client_sub.count == 0


# =============================================================================
# SubscriptionManager Tests
# =============================================================================

class TestSubscriptionManager:
    """Tests for SubscriptionManager."""
    
    @pytest.mark.asyncio
    async def test_subscribe(self, query_signature, config, clean_state):
        """Test subscribing to a query."""
        manager = get_subscription_manager()
        
        # Mock the detector - patch where it's imported
        with patch("pynext.db.live.detection.get_detector_registry") as mock_registry:
            mock_detector = AsyncMock()
            mock_detector.subscribe = AsyncMock(return_value="det_sub_1")
            mock_registry.return_value.get_detector = AsyncMock(return_value=mock_detector)
            
            sub_id = await manager.subscribe(
                query_signature=query_signature,
                callback=Mock(),
                config=config,
            )
        
        assert sub_id is not None
        assert sub_id.startswith("sub_")
        assert manager.subscription_count == 1
    
    @pytest.mark.asyncio
    async def test_unsubscribe(self, query_signature, config, clean_state):
        """Test unsubscribing from a query."""
        manager = get_subscription_manager()
        
        with patch("pynext.db.live.detection.get_detector_registry") as mock_registry:
            mock_detector = AsyncMock()
            mock_detector.subscribe = AsyncMock(return_value="det_sub_1")
            mock_detector.unsubscribe = AsyncMock()
            mock_registry.return_value.get_detector = AsyncMock(return_value=mock_detector)
            
            sub_id = await manager.subscribe(
                query_signature=query_signature,
                callback=Mock(),
                config=config,
            )
            
            result = await manager.unsubscribe(sub_id)
        
        assert result is True
        assert manager.subscription_count == 0
    
    @pytest.mark.asyncio
    async def test_unsubscribe_not_found(self, clean_state):
        """Test unsubscribing from non-existent subscription."""
        manager = get_subscription_manager()
        
        result = await manager.unsubscribe("nonexistent")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_query_deduplication(self, query_signature, config, clean_state):
        """Test multiple subscriptions to same query share group."""
        manager = get_subscription_manager()
        
        with patch("pynext.db.live.detection.get_detector_registry") as mock_registry:
            mock_detector = AsyncMock()
            mock_detector.subscribe = AsyncMock(return_value="det_sub_1")
            mock_registry.return_value.get_detector = AsyncMock(return_value=mock_detector)
            
            # Two subscriptions to same query
            await manager.subscribe(
                query_signature=query_signature,
                callback=Mock(),
                config=config,
            )
            await manager.subscribe(
                query_signature=query_signature,
                callback=Mock(),
                config=config,
            )
        
        assert manager.subscription_count == 2
        assert manager.query_group_count == 1  # Same query = one group
    
    @pytest.mark.asyncio
    async def test_get_stats(self, query_signature, config, clean_state):
        """Test getting subscription stats."""
        manager = get_subscription_manager()
        
        with patch("pynext.db.live.detection.get_detector_registry") as mock_registry:
            mock_detector = AsyncMock()
            mock_detector.subscribe = AsyncMock(return_value="det_sub_1")
            mock_registry.return_value.get_detector = AsyncMock(return_value=mock_detector)
            
            await manager.subscribe(
                query_signature=query_signature,
                callback=Mock(),
                config=config,
            )
        
        stats = manager.get_stats()
        
        assert stats["subscriptions"] == 1
        assert stats["query_groups"] == 1
        assert "users" in stats["tables"]
    
    @pytest.mark.asyncio
    async def test_notify_change(self, query_signature, config, clean_state):
        """Test notifying subscriptions of changes."""
        manager = get_subscription_manager()
        callback = Mock()
        
        with patch("pynext.db.live.detection.get_detector_registry") as mock_registry:
            mock_detector = AsyncMock()
            mock_detector.subscribe = AsyncMock(return_value="det_sub_1")
            mock_registry.return_value.get_detector = AsyncMock(return_value=mock_detector)
            
            await manager.subscribe(
                query_signature=query_signature,
                callback=callback,
                config=config,
            )
        
        event = ChangeEvent(table="users", type=ChangeType.INSERT, row_id=1)
        notified = await manager.notify_change(event)
        
        assert notified == 1
        callback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_notify_change_wrong_table(self, query_signature, config, clean_state):
        """Test notifying ignores wrong table."""
        manager = get_subscription_manager()
        callback = Mock()
        
        with patch("pynext.db.live.detection.get_detector_registry") as mock_registry:
            mock_detector = AsyncMock()
            mock_detector.subscribe = AsyncMock(return_value="det_sub_1")
            mock_registry.return_value.get_detector = AsyncMock(return_value=mock_detector)
            
            await manager.subscribe(
                query_signature=query_signature,  # users table
                callback=callback,
                config=config,
            )
        
        event = ChangeEvent(table="posts", type=ChangeType.INSERT, row_id=1)
        notified = await manager.notify_change(event)
        
        assert notified == 0
        callback.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_unsubscribe_client(self, query_signature, config, clean_state):
        """Test unsubscribing all of a client's subscriptions."""
        manager = get_subscription_manager()
        
        with patch("pynext.db.live.detection.get_detector_registry") as mock_registry:
            mock_detector = AsyncMock()
            mock_detector.subscribe = AsyncMock(return_value="det_sub_1")
            mock_detector.unsubscribe = AsyncMock()
            mock_registry.return_value.get_detector = AsyncMock(return_value=mock_detector)
            
            await manager.subscribe(
                query_signature=query_signature,
                callback=Mock(),
                config=config,
                client_id="client_1",
            )
            await manager.subscribe(
                query_signature=QuerySignature(table="posts"),
                callback=Mock(),
                config=config,
                client_id="client_1",
            )
        
        assert manager.subscription_count == 2
        
        with patch("pynext.db.live.detection.get_detector_registry") as mock_registry:
            mock_detector = AsyncMock()
            mock_detector.unsubscribe = AsyncMock()
            mock_registry.return_value.get_detector = AsyncMock(return_value=mock_detector)
            
            removed = await manager.unsubscribe_client("client_1")
        
        assert removed == 2
        assert manager.subscription_count == 0


# =============================================================================
# Update Strategy Tests
# =============================================================================

class TestUpdateStrategies:
    """Tests for update strategies integration."""
    
    def test_surgical_update_insert(self):
        """Test surgical update handles INSERT."""
        strategy = SurgicalUpdate()
        
        data = [MockUser(id=1, name="Alice")]
        data_by_id = {1: data[0]}
        
        event = ChangeEvent(
            table="users",
            type=ChangeType.INSERT,
            row_id=2,
            new_data={"id": 2, "name": "Bob"},
        )
        
        result = strategy.apply(data, data_by_id, event, MockUser)
        
        assert result.changed is True
        assert len(result.data) == 2
        assert 2 in result.added
    
    def test_surgical_update_delete(self):
        """Test surgical update handles DELETE."""
        strategy = SurgicalUpdate()
        
        data = [MockUser(id=1, name="Alice"), MockUser(id=2, name="Bob")]
        data_by_id = {1: data[0], 2: data[1]}
        
        event = ChangeEvent(
            table="users",
            type=ChangeType.DELETE,
            row_id=2,
            old_data={"id": 2, "name": "Bob"},
        )
        
        result = strategy.apply(data, data_by_id, event, MockUser)
        
        assert result.changed is True
        assert len(result.data) == 1
        assert 2 in result.removed
    
    def test_strategy_selector_simple_query(self):
        """Test selector chooses surgical for simple queries."""
        selector = StrategySelector()
        config = LiveQueryConfig()
        sig = QuerySignature(table="users")
        event = ChangeEvent(table="users", type=ChangeType.INSERT, row_id=1)
        
        strategy = selector.select(sig, event, config)
        
        assert isinstance(strategy, SurgicalUpdate)
    
    def test_strategy_selector_limited_query(self):
        """Test selector chooses refresh for limited queries."""
        selector = StrategySelector()
        config = LiveQueryConfig()
        sig = QuerySignature(table="users", limit=10)
        event = ChangeEvent(table="users", type=ChangeType.INSERT, row_id=1)
        
        strategy = selector.select(sig, event, config)
        
        assert isinstance(strategy, FullRefresh)


# =============================================================================
# Concurrency Tests
# =============================================================================

class TestConcurrency:
    """Tests for concurrent operations."""
    
    @pytest.mark.asyncio
    async def test_concurrent_subscriptions(self, query_signature, config, clean_state):
        """Test concurrent subscription creation."""
        manager = get_subscription_manager()
        
        with patch("pynext.db.live.detection.get_detector_registry") as mock_registry:
            mock_detector = AsyncMock()
            mock_detector.subscribe = AsyncMock(return_value="det_sub_1")
            mock_registry.return_value.get_detector = AsyncMock(return_value=mock_detector)
            
            async def subscribe_client(n):
                return await manager.subscribe(
                    query_signature=query_signature,
                    callback=Mock(),
                    config=config,
                    client_id=f"client_{n}",
                )
            
            # Create 10 concurrent subscriptions
            sub_ids = await asyncio.gather(*[subscribe_client(i) for i in range(10)])
        
        assert len(sub_ids) == 10
        assert len(set(sub_ids)) == 10  # All unique
        assert manager.subscription_count == 10
    
    @pytest.mark.asyncio
    async def test_concurrent_notifications(self, query_signature, config, clean_state):
        """Test concurrent change notifications."""
        manager = get_subscription_manager()
        callback = Mock()
        
        with patch("pynext.db.live.detection.get_detector_registry") as mock_registry:
            mock_detector = AsyncMock()
            mock_detector.subscribe = AsyncMock(return_value="det_sub_1")
            mock_registry.return_value.get_detector = AsyncMock(return_value=mock_detector)
            
            await manager.subscribe(
                query_signature=query_signature,
                callback=callback,
                config=config,
            )
        
        # Send 10 concurrent notifications
        events = [
            ChangeEvent(table="users", type=ChangeType.INSERT, row_id=i)
            for i in range(10)
        ]
        
        await asyncio.gather(*[manager.notify_change(e) for e in events])
        
        assert callback.call_count == 10


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestErrorHandling:
    """Tests for error handling and recovery."""
    
    @pytest.mark.asyncio
    async def test_callback_error_doesnt_crash(self, query_signature, config, clean_state):
        """Test callback error doesn't crash the system."""
        manager = get_subscription_manager()
        error_callback = Mock(side_effect=Exception("Callback error"))
        
        with patch("pynext.db.live.detection.get_detector_registry") as mock_registry:
            mock_detector = AsyncMock()
            mock_detector.subscribe = AsyncMock(return_value="det_sub_1")
            mock_registry.return_value.get_detector = AsyncMock(return_value=mock_detector)
            
            await manager.subscribe(
                query_signature=query_signature,
                callback=error_callback,
                config=config,
            )
        
        event = ChangeEvent(table="users", type=ChangeType.INSERT, row_id=1)
        
        # Should not raise
        await manager.notify_change(event)
        
        error_callback.assert_called_once()


# =============================================================================
# ChangeEvent Tests
# =============================================================================

class TestChangeEvent:
    """Tests for ChangeEvent."""
    
    def test_create_insert_event(self):
        """Test creating an INSERT event."""
        event = ChangeEvent(
            table="users",
            type=ChangeType.INSERT,
            row_id=1,
            new_data={"id": 1, "name": "Alice"},
        )
        
        assert event.table == "users"
        assert event.type == ChangeType.INSERT
        assert event.row_id == 1
        assert event.new_data["name"] == "Alice"
    
    def test_create_update_event(self):
        """Test creating an UPDATE event."""
        event = ChangeEvent(
            table="users",
            type=ChangeType.UPDATE,
            row_id=1,
            old_data={"id": 1, "name": "Alice"},
            new_data={"id": 1, "name": "Alice Smith"},
            columns_changed=["name"],
        )
        
        assert event.type == ChangeType.UPDATE
        assert event.columns_changed == ["name"]
    
    def test_create_delete_event(self):
        """Test creating a DELETE event."""
        event = ChangeEvent(
            table="users",
            type=ChangeType.DELETE,
            row_id=1,
            old_data={"id": 1, "name": "Alice"},
        )
        
        assert event.type == ChangeType.DELETE
        assert event.new_data is None
    
    def test_affects_query_same_table(self):
        """Test affects_query with same table."""
        event = ChangeEvent(table="users", type=ChangeType.INSERT, row_id=1)
        sig = QuerySignature(table="users")
        
        assert event.affects_query(sig) is True
    
    def test_affects_query_different_table(self):
        """Test affects_query with different table."""
        event = ChangeEvent(table="posts", type=ChangeType.INSERT, row_id=1)
        sig = QuerySignature(table="users")
        
        assert event.affects_query(sig) is False
    
    def test_to_dict(self):
        """Test converting event to dict."""
        event = ChangeEvent(
            table="users",
            type=ChangeType.INSERT,
            row_id=1,
            new_data={"id": 1, "name": "Alice"},
        )
        
        d = event.to_dict()
        
        assert d["table"] == "users"
        assert d["type"] == "INSERT"
        assert d["row_id"] == 1


# =============================================================================
# LiveQueryConfig Tests
# =============================================================================

class TestLiveQueryConfig:
    """Tests for LiveQueryConfig."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = LiveQueryConfig()
        
        assert config.transport == TransportType.AUTO
        assert config.detection == DetectionStrategy.AUTO
        assert config.granularity == UpdateGranularity.AUTO
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = LiveQueryConfig(
            transport=TransportType.WEBSOCKET,
            detection=DetectionStrategy.POSTGRES,
            poll_interval=60.0,
        )
        
        assert config.transport == TransportType.WEBSOCKET
        assert config.detection == DetectionStrategy.POSTGRES
        assert config.poll_interval == 60.0
    
    def test_config_merge(self):
        """Test config merge."""
        config = LiveQueryConfig()
        merged = config.merge(transport=TransportType.SSE)
        
        assert merged.transport == TransportType.SSE
        assert merged.detection == config.detection  # Not changed
    
    def test_config_to_dict(self):
        """Test config to dict."""
        config = LiveQueryConfig()
        d = config.to_dict()
        
        assert "transport" in d
        assert "detection" in d
        assert "granularity" in d
