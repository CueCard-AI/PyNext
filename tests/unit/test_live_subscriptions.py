"""
Comprehensive tests for PyNext Live Query Subscription Manager.

Tests the SubscriptionManager and related components:
- QueryGroup
- Subscription lifecycle
- Deduplication
- Orchestration

Target: 42 tests
"""

import pytest
import asyncio
from datetime import datetime
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from pynext.db.live.subscriptions import (
    SubscriptionManager,
    QueryGroup,
    Subscription,
    ClientSubscription,
    get_subscription_manager,
    reset_subscription_manager,
)
from pynext.db.live.config import (
    LiveQueryConfig,
    QuerySignature,
    TransportType,
    DetectionStrategy,
    UpdateGranularity,
    DEFAULT_CONFIG,
)
from pynext.db.live.detection.base import ChangeEvent, ChangeType


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
    return QuerySignature(
        table="users",
        where_clauses=({"status": "active"},),
    )


@pytest.fixture
def simple_signature():
    """Create a simple query signature (no filters)."""
    return QuerySignature(table="users")


@pytest.fixture
async def subscription_manager():
    """Create a fresh subscription manager."""
    import pynext.db.live.subscriptions as subs_module
    subs_module._manager = None
    return get_subscription_manager()


@pytest.fixture
def change_event():
    """Create a sample change event."""
    return ChangeEvent(
        table="users",
        type=ChangeType.INSERT,
        row_id=1,
        new_data={"id": 1, "name": "John", "status": "active"},
    )


@pytest.fixture
def mock_callback():
    """Create a mock callback function."""
    return Mock()


# =============================================================================
# Subscription Tests
# =============================================================================

class TestSubscription:
    """Tests for Subscription dataclass."""
    
    def test_create_subscription(self, query_signature, config, mock_callback):
        """Test creating a subscription."""
        sub = Subscription(
            id="sub_1",
            client_id="client_1",
            query_signature=query_signature,
            callback=mock_callback,
            config=config,
        )
        
        assert sub.id == "sub_1"
        assert sub.client_id == "client_1"
        assert sub.query_signature == query_signature
        assert sub.callback == mock_callback
    
    def test_subscription_defaults(self, query_signature, config, mock_callback):
        """Test subscription default values."""
        sub = Subscription(
            id="sub_1",
            client_id="client_1",
            query_signature=query_signature,
            callback=mock_callback,
            config=config,
        )
        
        assert sub.created_at is not None
        assert sub.last_update is None
        assert sub.update_count == 0
    
    def test_subscription_on_change(self, query_signature, config, mock_callback, change_event):
        """Test subscription on_change method."""
        sub = Subscription(
            id="sub_1",
            client_id="client_1",
            query_signature=query_signature,
            callback=mock_callback,
            config=config,
        )
        
        sub.on_change(change_event)
        
        mock_callback.assert_called_once_with(change_event)
        assert sub.update_count == 1
        assert sub.last_update is not None
    
    def test_subscription_on_change_error_handling(self, query_signature, config, change_event):
        """Test subscription handles callback errors gracefully."""
        error_callback = Mock(side_effect=Exception("Callback error"))
        
        sub = Subscription(
            id="sub_1",
            client_id="client_1",
            query_signature=query_signature,
            callback=error_callback,
            config=config,
        )
        
        # Should not raise even if callback raises
        sub.on_change(change_event)
        
        # Still records the update
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
        assert group.is_empty is True
        assert group.subscription_count == 0
    
    def test_add_subscription(self, query_signature, config, mock_callback):
        """Test adding subscription to group."""
        group = QueryGroup(signature=query_signature)
        
        sub = Subscription(
            id="sub_1",
            client_id="client_1",
            query_signature=query_signature,
            callback=mock_callback,
            config=config,
        )
        
        group.add_subscription(sub)
        
        assert group.subscription_count == 1
        assert group.is_empty is False
    
    def test_remove_subscription(self, query_signature, config, mock_callback):
        """Test removing subscription from group."""
        group = QueryGroup(signature=query_signature)
        
        sub = Subscription(
            id="sub_1",
            client_id="client_1",
            query_signature=query_signature,
            callback=mock_callback,
            config=config,
        )
        
        group.add_subscription(sub)
        removed = group.remove_subscription("sub_1")
        
        assert removed == sub
        assert group.subscription_count == 0
        assert group.is_empty is True
    
    def test_remove_nonexistent_subscription(self, query_signature):
        """Test removing nonexistent subscription returns None."""
        group = QueryGroup(signature=query_signature)
        
        removed = group.remove_subscription("nonexistent")
        
        assert removed is None
    
    def test_on_change_notifies_subscriptions(self, simple_signature, config, change_event):
        """Test on_change notifies all subscriptions."""
        group = QueryGroup(signature=simple_signature)
        
        callback1 = Mock()
        callback2 = Mock()
        
        sub1 = Subscription(
            id="sub_1",
            client_id="client_1",
            query_signature=simple_signature,
            callback=callback1,
            config=config,
        )
        sub2 = Subscription(
            id="sub_2",
            client_id="client_2",
            query_signature=simple_signature,
            callback=callback2,
            config=config,
        )
        
        group.add_subscription(sub1)
        group.add_subscription(sub2)
        
        group.on_change(change_event)
        
        callback1.assert_called_once_with(change_event)
        callback2.assert_called_once_with(change_event)
    
    def test_on_change_filters_by_query(self, query_signature, config):
        """Test on_change only notifies if event affects query."""
        group = QueryGroup(signature=query_signature)
        
        callback = Mock()
        sub = Subscription(
            id="sub_1",
            client_id="client_1",
            query_signature=query_signature,
            callback=callback,
            config=config,
        )
        group.add_subscription(sub)
        
        # Event for different table
        wrong_table_event = ChangeEvent(
            table="posts",
            type=ChangeType.INSERT,
            row_id=1,
        )
        
        group.on_change(wrong_table_event)
        
        # Should not be called - different table
        callback.assert_not_called()
    
    def test_group_created_at(self, query_signature):
        """Test group has created_at timestamp."""
        group = QueryGroup(signature=query_signature)
        
        assert group.created_at is not None
        assert isinstance(group.created_at, datetime)


# =============================================================================
# ClientSubscription Tests
# =============================================================================

class TestClientSubscription:
    """Tests for ClientSubscription."""
    
    def test_create_client_subscription(self):
        """Test creating a client subscription tracker."""
        cs = ClientSubscription("client_1")
        
        assert cs.client_id == "client_1"
        assert cs.count == 0
    
    def test_add_subscription_id(self):
        """Test adding subscription ID."""
        cs = ClientSubscription("client_1")
        
        cs.add("sub_1")
        cs.add("sub_2")
        
        assert cs.count == 2
        assert "sub_1" in cs.subscription_ids
        assert "sub_2" in cs.subscription_ids
    
    def test_remove_subscription_id(self):
        """Test removing subscription ID."""
        cs = ClientSubscription("client_1")
        cs.add("sub_1")
        cs.add("sub_2")
        
        cs.remove("sub_1")
        
        assert cs.count == 1
        assert "sub_1" not in cs.subscription_ids
    
    def test_remove_nonexistent_id(self):
        """Test removing nonexistent ID doesn't error."""
        cs = ClientSubscription("client_1")
        
        # Should not raise
        cs.remove("nonexistent")
        
        assert cs.count == 0


# =============================================================================
# SubscriptionManager Tests
# =============================================================================

class TestSubscriptionManager:
    """Tests for SubscriptionManager."""
    
    @pytest.mark.asyncio
    async def test_subscribe(self, subscription_manager, simple_signature, config):
        """Test subscribing to a query."""
        callback = Mock()
        
        sub_id = await subscription_manager.subscribe(
            query_signature=simple_signature,
            callback=callback,
            config=config,
            client_id="client_1",
        )
        
        assert sub_id is not None
        assert subscription_manager.subscription_count == 1
    
    @pytest.mark.asyncio
    async def test_unsubscribe(self, subscription_manager, simple_signature, config):
        """Test unsubscribing from a query."""
        callback = Mock()
        
        sub_id = await subscription_manager.subscribe(
            query_signature=simple_signature,
            callback=callback,
            config=config,
            client_id="client_1",
        )
        
        result = await subscription_manager.unsubscribe(sub_id)
        
        assert result is True
        assert subscription_manager.subscription_count == 0
    
    @pytest.mark.asyncio
    async def test_unsubscribe_nonexistent(self, subscription_manager):
        """Test unsubscribing nonexistent subscription."""
        result = await subscription_manager.unsubscribe("nonexistent")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_query_deduplication(self, subscription_manager, simple_signature, config):
        """Test that identical queries share a QueryGroup."""
        callback1 = Mock()
        callback2 = Mock()
        
        await subscription_manager.subscribe(
            query_signature=simple_signature,
            callback=callback1,
            config=config,
            client_id="client_1",
        )
        await subscription_manager.subscribe(
            query_signature=simple_signature,
            callback=callback2,
            config=config,
            client_id="client_2",
        )
        
        assert subscription_manager.subscription_count == 2
        assert subscription_manager.query_group_count == 1  # Deduplicated!
    
    @pytest.mark.asyncio
    async def test_client_disconnect(self, subscription_manager, simple_signature, config):
        """Test cleaning up subscriptions when client disconnects."""
        callback = Mock()
        
        await subscription_manager.subscribe(
            query_signature=simple_signature,
            callback=callback,
            config=config,
            client_id="client_1",
        )
        
        await subscription_manager.unsubscribe_client("client_1")
        
        assert subscription_manager.subscription_count == 0
    
    @pytest.mark.asyncio
    async def test_get_stats(self, subscription_manager, simple_signature, config):
        """Test getting manager stats."""
        callback = Mock()
        
        await subscription_manager.subscribe(
            query_signature=simple_signature,
            callback=callback,
            config=config,
            client_id="client_1",
        )
        
        stats = subscription_manager.get_stats()
        
        assert "subscriptions" in stats
        assert "query_groups" in stats
        assert "clients" in stats


# =============================================================================
# QuerySignature Tests
# =============================================================================

class TestQuerySignature:
    """Tests for QuerySignature."""
    
    def test_signature_equality(self):
        """Test signature equality comparison."""
        sig1 = QuerySignature(table="users", where_clauses=({"status": "active"},))
        sig2 = QuerySignature(table="users", where_clauses=({"status": "active"},))
        
        assert sig1 == sig2
    
    def test_signature_hash_equality(self):
        """Test that equal signatures have equal hashes."""
        # Use simple signatures (no dicts in where_clauses) for hashing
        sig1 = QuerySignature(table="users", limit=10)
        sig2 = QuerySignature(table="users", limit=10)
        
        assert hash(sig1) == hash(sig2)
    
    def test_signature_inequality(self):
        """Test signature inequality."""
        sig1 = QuerySignature(table="users")
        sig2 = QuerySignature(table="posts")
        
        assert sig1 != sig2
        assert hash(sig1) != hash(sig2)
    
    def test_is_simple(self):
        """Test is_simple property."""
        simple = QuerySignature(table="users")
        complex_sig = QuerySignature(table="users", where_clauses=({"status": "active"},))
        
        assert simple.is_simple is True
        assert complex_sig.is_simple is False
    
    def test_has_limit(self):
        """Test has_limit property."""
        no_limit = QuerySignature(table="users")
        with_limit = QuerySignature(table="users", limit=10)
        
        assert no_limit.has_limit is False
        assert with_limit.has_limit is True
    
    def test_has_filters(self):
        """Test has_filters property."""
        no_filter = QuerySignature(table="users")
        with_filter = QuerySignature(table="users", where_clauses=({"status": "active"},))
        
        assert no_filter.has_filters is False
        assert with_filter.has_filters is True


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
        assert config.reconnect is True
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = LiveQueryConfig(
            transport=TransportType.WEBSOCKET,
            detection=DetectionStrategy.POSTGRES,
            poll_interval=10.0,
        )
        
        assert config.transport == TransportType.WEBSOCKET
        assert config.detection == DetectionStrategy.POSTGRES
        assert config.poll_interval == 10.0
    
    def test_config_merge(self):
        """Test merging configs."""
        base = LiveQueryConfig(poll_interval=30.0)
        merged = base.merge(poll_interval=5.0, debug=True)
        
        assert merged.poll_interval == 5.0
        assert merged.debug is True
        # Original unchanged
        assert base.poll_interval == 30.0
    
    def test_config_to_dict(self):
        """Test converting config to dict."""
        config = LiveQueryConfig()
        
        d = config.to_dict()
        
        assert d["transport"] == "auto"
        assert d["detection"] == "auto"
        assert d["poll_interval"] == 30.0
    
    def test_default_config_constant(self):
        """Test DEFAULT_CONFIG exists and has expected values."""
        assert DEFAULT_CONFIG is not None
        assert DEFAULT_CONFIG.transport == TransportType.AUTO


# =============================================================================
# Edge Cases
# =============================================================================

class TestSubscriptionEdgeCases:
    """Tests for edge cases and error handling."""
    
    @pytest.mark.asyncio
    async def test_multiple_clients_same_query(self, subscription_manager, simple_signature, config):
        """Test multiple clients subscribing to same query."""
        callbacks = [Mock() for _ in range(5)]
        
        for i, callback in enumerate(callbacks):
            await subscription_manager.subscribe(
                query_signature=simple_signature,
                callback=callback,
                config=config,
                client_id=f"client_{i}",
            )
        
        assert subscription_manager.subscription_count == 5
        assert subscription_manager.query_group_count == 1
        assert subscription_manager.client_count == 5
    
    @pytest.mark.asyncio
    async def test_subscribe_multiple_queries(self, subscription_manager, config):
        """Test subscribing to multiple different queries."""
        callback1 = Mock()
        callback2 = Mock()
        
        sig1 = QuerySignature(table="users")
        sig2 = QuerySignature(table="posts")
        
        await subscription_manager.subscribe(
            query_signature=sig1,
            callback=callback1,
            config=config,
            client_id="client_1",
        )
        await subscription_manager.subscribe(
            query_signature=sig2,
            callback=callback2,
            config=config,
            client_id="client_1",
        )
        
        assert subscription_manager.subscription_count == 2
        assert subscription_manager.query_group_count == 2  # Different queries
    
    def test_query_signature_with_all_options(self):
        """Test query signature with all options."""
        sig = QuerySignature(
            table="users",
            where_clauses=({"status": "active"}, {"role": "admin"}),
            order_by="-created_at",
            limit=10,
            offset=5,
            fields=("id", "name", "email"),
        )
        
        assert sig.table == "users"
        assert sig.has_filters is True
        assert sig.has_limit is True
        assert sig.is_simple is False
