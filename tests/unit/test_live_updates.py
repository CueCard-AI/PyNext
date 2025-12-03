"""
Comprehensive tests for PyNext Live Query Update Strategies.

Tests the UpdateStrategy base class and implementations:
- SurgicalUpdate
- FullRefresh
- StrategySelector

Target: 80 tests
"""

import pytest
import asyncio
from datetime import datetime
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from dataclasses import dataclass

from pynext.db.live.updates.base import (
    UpdateStrategy,
    UpdateResult,
)
from pynext.db.live.updates.surgical import SurgicalUpdate
from pynext.db.live.updates.refresh import FullRefresh, RefreshDebouncer
from pynext.db.live.updates.selector import (
    StrategySelector,
    get_strategy_selector,
)
from pynext.db.live.detection.base import ChangeEvent, ChangeType
from pynext.db.live.config import UpdateGranularity, QuerySignature, LiveQueryConfig


# =============================================================================
# Mock Model for Testing
# =============================================================================

@dataclass
class MockUser:
    """Mock user model for testing."""
    id: int
    name: str
    age: int = 25
    
    @classmethod
    def _from_row(cls, data: Dict[str, Any]) -> "MockUser":
        """Create from row dict."""
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            age=data.get("age", 25),
        )
    
    def _to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "name": self.name, "age": self.age}


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def insert_event():
    """Create an INSERT change event."""
    return ChangeEvent(
        table="users",
        type=ChangeType.INSERT,
        row_id=3,
        new_data={"id": 3, "name": "Charlie", "age": 30},
    )


@pytest.fixture
def update_event():
    """Create an UPDATE change event."""
    return ChangeEvent(
        table="users",
        type=ChangeType.UPDATE,
        row_id=1,
        old_data={"id": 1, "name": "Alice", "age": 25},
        new_data={"id": 1, "name": "Alice", "age": 26},
        columns_changed=["age"],
    )


@pytest.fixture
def delete_event():
    """Create a DELETE change event."""
    return ChangeEvent(
        table="users",
        type=ChangeType.DELETE,
        row_id=2,
        old_data={"id": 2, "name": "Bob", "age": 28},
    )


@pytest.fixture
def sample_data():
    """Create sample data rows."""
    return [
        MockUser(id=1, name="Alice", age=25),
        MockUser(id=2, name="Bob", age=28),
    ]


@pytest.fixture
def sample_data_by_id(sample_data):
    """Create data lookup dict."""
    return {u.id: u for u in sample_data}


@pytest.fixture
def query_signature():
    """Create a sample query signature."""
    return QuerySignature(table="users")


@pytest.fixture
def config():
    """Create default config."""
    return LiveQueryConfig()


# =============================================================================
# UpdateResult Tests
# =============================================================================

class TestUpdateResult:
    """Tests for UpdateResult dataclass."""
    
    def test_create_result_changed(self):
        """Test creating result with changes."""
        result = UpdateResult(
            changed=True,
            data=[{"id": 1}],
            data_by_id={1: {"id": 1}},
            added=[1],
        )
        
        assert result.changed is True
        assert result.change_count == 1
        assert result.added == [1]
    
    def test_create_result_no_change(self):
        """Test creating result with no changes."""
        result = UpdateResult(
            changed=False,
            data=[],
            data_by_id={},
        )
        
        assert result.changed is False
        assert result.change_count == 0
    
    def test_change_count_all_types(self):
        """Test change count with all operation types."""
        result = UpdateResult(
            changed=True,
            data=[],
            data_by_id={},
            added=[1, 2],
            updated=[3],
            removed=[4, 5, 6],
        )
        
        assert result.change_count == 6
    
    def test_no_change_factory(self):
        """Test no_change factory method."""
        data = [{"id": 1}]
        data_by_id = {1: {"id": 1}}
        
        result = UpdateResult.no_change(data, data_by_id)
        
        assert result.changed is False
        assert result.data == data
        assert result.data_by_id == data_by_id
        assert result.added == []
        assert result.updated == []
        assert result.removed == []
    
    def test_defaults(self):
        """Test default values."""
        result = UpdateResult(
            changed=True,
            data=[],
            data_by_id={},
        )
        
        assert result.added == []
        assert result.updated == []
        assert result.removed == []


# =============================================================================
# SurgicalUpdate Tests
# =============================================================================

class TestSurgicalUpdate:
    """Tests for SurgicalUpdate strategy."""
    
    def test_name(self):
        """Test strategy name."""
        strategy = SurgicalUpdate()
        assert strategy.name == "Surgical"
    
    def test_apply_insert(self, sample_data, sample_data_by_id, insert_event):
        """Test applying INSERT event."""
        strategy = SurgicalUpdate()
        
        result = strategy.apply(
            sample_data, sample_data_by_id, insert_event, MockUser
        )
        
        assert result.changed is True
        assert len(result.data) == 3
        assert 3 in result.added
        assert result.data[2].name == "Charlie"
    
    def test_apply_update(self, sample_data, sample_data_by_id, update_event):
        """Test applying UPDATE event."""
        strategy = SurgicalUpdate()
        
        result = strategy.apply(
            sample_data, sample_data_by_id, update_event, MockUser
        )
        
        assert result.changed is True
        assert len(result.data) == 2
        assert 1 in result.updated
        assert result.data[0].age == 26
    
    def test_apply_delete(self, sample_data, sample_data_by_id, delete_event):
        """Test applying DELETE event."""
        strategy = SurgicalUpdate()
        
        result = strategy.apply(
            sample_data, sample_data_by_id, delete_event, MockUser
        )
        
        assert result.changed is True
        assert len(result.data) == 1
        assert 2 in result.removed
        assert result.data[0].name == "Alice"
    
    def test_apply_insert_duplicate_ignored(self, sample_data, sample_data_by_id):
        """Test INSERT with existing ID is ignored."""
        strategy = SurgicalUpdate()
        
        event = ChangeEvent(
            table="users",
            type=ChangeType.INSERT,
            row_id=1,  # Already exists
            new_data={"id": 1, "name": "Duplicate"},
        )
        
        result = strategy.apply(
            sample_data, sample_data_by_id, event, MockUser
        )
        
        assert result.changed is False
        assert len(result.data) == 2
    
    def test_apply_update_not_found(self, sample_data, sample_data_by_id):
        """Test UPDATE for non-existent row."""
        strategy = SurgicalUpdate()
        
        event = ChangeEvent(
            table="users",
            type=ChangeType.UPDATE,
            row_id=999,
            new_data={"id": 999, "name": "Ghost"},
        )
        
        result = strategy.apply(
            sample_data, sample_data_by_id, event, MockUser
        )
        
        assert result.changed is False
        assert len(result.data) == 2
    
    def test_apply_delete_not_found(self, sample_data, sample_data_by_id):
        """Test DELETE for non-existent row."""
        strategy = SurgicalUpdate()
        
        event = ChangeEvent(
            table="users",
            type=ChangeType.DELETE,
            row_id=999,
            old_data={"id": 999},
        )
        
        result = strategy.apply(
            sample_data, sample_data_by_id, event, MockUser
        )
        
        assert result.changed is False
        assert len(result.data) == 2
    
    def test_apply_insert_no_data(self, sample_data, sample_data_by_id):
        """Test INSERT with no new_data."""
        strategy = SurgicalUpdate()
        
        event = ChangeEvent(
            table="users",
            type=ChangeType.INSERT,
            row_id=3,
            new_data=None,
        )
        
        result = strategy.apply(
            sample_data, sample_data_by_id, event, MockUser
        )
        
        assert result.changed is False
    
    def test_apply_update_no_data(self, sample_data, sample_data_by_id):
        """Test UPDATE with no new_data."""
        strategy = SurgicalUpdate()
        
        event = ChangeEvent(
            table="users",
            type=ChangeType.UPDATE,
            row_id=1,
            new_data=None,
        )
        
        result = strategy.apply(
            sample_data, sample_data_by_id, event, MockUser
        )
        
        assert result.changed is False
    
    def test_apply_unknown_event_type(self, sample_data, sample_data_by_id):
        """Test unknown event type returns no change."""
        strategy = SurgicalUpdate()
        
        event = ChangeEvent(
            table="users",
            type=ChangeType.TRUNCATE,
            row_id=None,
        )
        
        result = strategy.apply(
            sample_data, sample_data_by_id, event, MockUser
        )
        
        assert result.changed is False
    
    def test_apply_empty_data_insert(self, insert_event):
        """Test INSERT to empty list."""
        strategy = SurgicalUpdate()
        
        result = strategy.apply([], {}, insert_event, MockUser)
        
        assert result.changed is True
        assert len(result.data) == 1
        assert result.data[0].name == "Charlie"
    
    def test_apply_delete_all(self):
        """Test DELETE that empties the list."""
        strategy = SurgicalUpdate()
        
        data = [MockUser(id=1, name="Only")]
        data_by_id = {1: data[0]}
        event = ChangeEvent(
            table="users",
            type=ChangeType.DELETE,
            row_id=1,
            old_data={"id": 1},
        )
        
        result = strategy.apply(data, data_by_id, event, MockUser)
        
        assert result.changed is True
        assert len(result.data) == 0
    
    def test_can_apply_simple_query(self, insert_event):
        """Test can_apply for simple query."""
        strategy = SurgicalUpdate()
        sig = QuerySignature(table="users")
        
        assert strategy.can_apply(insert_event, sig) is True
    
    def test_can_apply_with_limit(self, insert_event):
        """Test can_apply with limit - INSERT needs filter check."""
        strategy = SurgicalUpdate()
        sig = QuerySignature(table="users", limit=10)
        
        # INSERT with filters needs re-evaluation
        assert strategy.can_apply(insert_event, sig) is True  # No filters
    
    def test_can_apply_delete_always_ok(self, delete_event):
        """Test DELETE can always use surgical."""
        strategy = SurgicalUpdate()
        sig = QuerySignature(
            table="users",
            where_clauses=({"status": "active"},),
        )
        
        assert strategy.can_apply(delete_event, sig) is True
    
    def test_can_apply_update_changed_filter_field(self):
        """Test UPDATE that changes a filtered field."""
        strategy = SurgicalUpdate()
        sig = QuerySignature(
            table="users",
            where_clauses=({"status": "active"},),
        )
        event = ChangeEvent(
            table="users",
            type=ChangeType.UPDATE,
            row_id=1,
            columns_changed=["status"],  # Changed filter field!
        )
        
        # Can't use surgical - need to re-evaluate filter
        assert strategy.can_apply(event, sig) is False
    
    def test_can_apply_update_changed_order_field(self):
        """Test UPDATE that changes order field."""
        strategy = SurgicalUpdate()
        sig = QuerySignature(
            table="users",
            order_by="name",
        )
        event = ChangeEvent(
            table="users",
            type=ChangeType.UPDATE,
            row_id=1,
            columns_changed=["name"],  # Changed order field!
        )
        
        # Can't use surgical - need to re-sort
        assert strategy.can_apply(event, sig) is False
    
    def test_update_preserves_order(self, sample_data, sample_data_by_id, update_event):
        """Test UPDATE preserves row order."""
        strategy = SurgicalUpdate()
        
        result = strategy.apply(
            sample_data, sample_data_by_id, update_event, MockUser
        )
        
        assert result.data[0].id == 1
        assert result.data[1].id == 2


# =============================================================================
# FullRefresh Tests
# =============================================================================

class TestFullRefresh:
    """Tests for FullRefresh strategy."""
    
    def test_name(self):
        """Test strategy name."""
        strategy = FullRefresh()
        assert strategy.name == "FullRefresh"
    
    def test_apply_returns_needs_refresh(self, sample_data, sample_data_by_id, insert_event):
        """Test apply signals refresh needed."""
        strategy = FullRefresh()
        
        result = strategy.apply(
            sample_data, sample_data_by_id, insert_event, MockUser
        )
        
        # Sync apply just signals refresh needed
        assert result.changed is True
        assert result.data == sample_data  # Keeps current until async completes
    
    @pytest.mark.asyncio
    async def test_apply_async_executes_query(self, sample_data, sample_data_by_id, insert_event):
        """Test async apply executes query."""
        new_data = [MockUser(id=1, name="Updated")]
        
        async def executor():
            return new_data
        
        strategy = FullRefresh(query_executor=executor)
        
        result = await strategy.apply_async(
            sample_data, sample_data_by_id, insert_event, MockUser
        )
        
        assert len(result.data) == 1
        assert result.data[0].name == "Updated"
    
    @pytest.mark.asyncio
    async def test_apply_async_tracks_changes(self, sample_data, sample_data_by_id, insert_event):
        """Test async apply correctly identifies added/removed/updated."""
        # Start with Alice(1) and Bob(2)
        # End with Alice(1 updated), Charlie(3) - so Bob removed, Charlie added
        new_data = [
            MockUser(id=1, name="AliceNew", age=30),
            MockUser(id=3, name="Charlie", age=35),
        ]
        
        async def executor():
            return new_data
        
        strategy = FullRefresh(query_executor=executor)
        
        result = await strategy.apply_async(
            sample_data, sample_data_by_id, insert_event, MockUser
        )
        
        assert result.changed is True
        assert 3 in result.added
        assert 2 in result.removed
    
    @pytest.mark.asyncio
    async def test_apply_async_no_executor(self, sample_data, sample_data_by_id, insert_event):
        """Test async apply without executor."""
        strategy = FullRefresh()  # No executor
        
        result = await strategy.apply_async(
            sample_data, sample_data_by_id, insert_event, MockUser
        )
        
        assert result.changed is False
        assert result.data == sample_data
    
    @pytest.mark.asyncio
    async def test_apply_async_executor_error(self, sample_data, sample_data_by_id, insert_event):
        """Test async apply handles executor error."""
        async def executor():
            raise Exception("DB error")
        
        strategy = FullRefresh(query_executor=executor)
        
        result = await strategy.apply_async(
            sample_data, sample_data_by_id, insert_event, MockUser
        )
        
        # Returns no change on error
        assert result.changed is False
        assert result.data == sample_data
    
    def test_can_apply_always_true(self, insert_event):
        """Test can_apply always returns True."""
        strategy = FullRefresh()
        sig = QuerySignature(
            table="users",
            where_clauses=({"status": "active"},),
            order_by="name",
            limit=10,
        )
        
        assert strategy.can_apply(insert_event, sig) is True


# =============================================================================
# RefreshDebouncer Tests
# =============================================================================

class TestRefreshDebouncer:
    """Tests for RefreshDebouncer."""
    
    def test_create_debouncer(self):
        """Test creating debouncer."""
        debouncer = RefreshDebouncer(delay_ms=100)
        assert debouncer._delay_ms == 100
    
    @pytest.mark.asyncio
    async def test_request_refresh_calls_callback(self):
        """Test refresh calls callback after delay."""
        debouncer = RefreshDebouncer(delay_ms=10)
        
        called = []
        async def callback():
            called.append(True)
        
        await debouncer.request_refresh("query1", callback)
        await asyncio.sleep(0.02)  # Wait for delay
        
        assert len(called) == 1
    
    @pytest.mark.asyncio
    async def test_request_refresh_debounces(self):
        """Test multiple requests are debounced."""
        debouncer = RefreshDebouncer(delay_ms=50)
        
        call_count = []
        async def callback():
            call_count.append(True)
        
        # Multiple requests in quick succession
        await debouncer.request_refresh("query1", callback)
        await asyncio.sleep(0.01)
        await debouncer.request_refresh("query1", callback)
        await asyncio.sleep(0.01)
        await debouncer.request_refresh("query1", callback)
        
        await asyncio.sleep(0.1)  # Wait for final callback
        
        # Should only be called once
        assert len(call_count) == 1
    
    @pytest.mark.asyncio
    async def test_cancel(self):
        """Test cancelling a pending refresh."""
        debouncer = RefreshDebouncer(delay_ms=100)
        
        called = []
        async def callback():
            called.append(True)
        
        await debouncer.request_refresh("query1", callback)
        debouncer.cancel("query1")
        
        await asyncio.sleep(0.15)  # Wait past delay
        
        assert len(called) == 0
    
    @pytest.mark.asyncio
    async def test_cancel_all(self):
        """Test cancelling all pending refreshes."""
        debouncer = RefreshDebouncer(delay_ms=100)
        
        called = []
        async def callback1():
            called.append(1)
        async def callback2():
            called.append(2)
        
        await debouncer.request_refresh("query1", callback1)
        await debouncer.request_refresh("query2", callback2)
        
        debouncer.cancel_all()
        
        await asyncio.sleep(0.15)
        
        assert len(called) == 0
    
    @pytest.mark.asyncio
    async def test_sync_callback(self):
        """Test with sync callback."""
        debouncer = RefreshDebouncer(delay_ms=10)
        
        called = []
        def callback():
            called.append(True)
        
        await debouncer.request_refresh("query1", callback)
        await asyncio.sleep(0.02)
        
        assert len(called) == 1


# =============================================================================
# StrategySelector Tests
# =============================================================================

class TestStrategySelector:
    """Tests for StrategySelector."""
    
    def test_select_explicit_surgical(self, query_signature, insert_event):
        """Test explicit surgical selection."""
        selector = StrategySelector()
        config = LiveQueryConfig(granularity=UpdateGranularity.SURGICAL)
        
        strategy = selector.select(query_signature, insert_event, config)
        
        assert isinstance(strategy, SurgicalUpdate)
    
    def test_select_explicit_refresh(self, query_signature, insert_event):
        """Test explicit refresh selection."""
        selector = StrategySelector()
        config = LiveQueryConfig(granularity=UpdateGranularity.REFRESH)
        
        strategy = selector.select(query_signature, insert_event, config)
        
        assert isinstance(strategy, FullRefresh)
    
    def test_auto_select_simple_query(self, query_signature, insert_event, config):
        """Test auto-selection for simple query."""
        selector = StrategySelector()
        
        strategy = selector.select(query_signature, insert_event, config)
        
        # Simple query -> Surgical
        assert isinstance(strategy, SurgicalUpdate)
    
    def test_auto_select_limited_query(self, insert_event, config):
        """Test auto-selection for limited query."""
        selector = StrategySelector()
        sig = QuerySignature(table="users", limit=10)
        
        strategy = selector.select(sig, insert_event, config)
        
        # Limited -> Full refresh
        assert isinstance(strategy, FullRefresh)
    
    def test_auto_select_complex_query(self, insert_event, config):
        """Test auto-selection for complex query that surgical can't handle."""
        selector = StrategySelector()
        sig = QuerySignature(
            table="users",
            where_clauses=({"status": "active"},),
        )
        # INSERT with filters needs re-evaluation
        
        strategy = selector.select(sig, insert_event, config)
        
        # With filters, INSERT goes to refresh
        assert isinstance(strategy, FullRefresh)
    
    def test_get_strategy_by_name(self):
        """Test getting strategy by name."""
        selector = StrategySelector()
        
        assert isinstance(selector.get_strategy("surgical"), SurgicalUpdate)
        assert isinstance(selector.get_strategy("refresh"), FullRefresh)
        assert isinstance(selector.get_strategy("fullrefresh"), FullRefresh)
        assert selector.get_strategy("invalid") is None
    
    def test_singleton(self):
        """Test get_strategy_selector returns same instance."""
        s1 = get_strategy_selector()
        s2 = get_strategy_selector()
        
        assert s1 is s2


# =============================================================================
# Edge Cases
# =============================================================================

class TestEdgeCases:
    """Edge case tests."""
    
    def test_surgical_insert_uses_row_id_from_data(self):
        """Test INSERT uses ID from new_data if row_id is None."""
        strategy = SurgicalUpdate()
        
        event = ChangeEvent(
            table="users",
            type=ChangeType.INSERT,
            row_id=None,  # No row_id
            new_data={"id": 5, "name": "FromData"},
        )
        
        result = strategy.apply([], {}, event, MockUser)
        
        assert result.changed is True
        assert len(result.data) == 1
        assert result.data[0].id == 5
    
    def test_surgical_delete_uses_id_from_old_data(self):
        """Test DELETE uses ID from old_data if row_id is None."""
        strategy = SurgicalUpdate()
        
        data = [MockUser(id=1, name="Test")]
        data_by_id = {1: data[0]}
        
        event = ChangeEvent(
            table="users",
            type=ChangeType.DELETE,
            row_id=None,
            old_data={"id": 1, "name": "Test"},
        )
        
        result = strategy.apply(data, data_by_id, event, MockUser)
        
        assert result.changed is True
        assert len(result.data) == 0
    
    def test_surgical_insert_no_id(self):
        """Test INSERT with no ID anywhere."""
        strategy = SurgicalUpdate()
        
        event = ChangeEvent(
            table="users",
            type=ChangeType.INSERT,
            row_id=None,
            new_data={"name": "NoId"},  # No id field
        )
        
        result = strategy.apply([], {}, event, MockUser)
        
        # Can't add without ID
        assert result.changed is False
    
    def test_surgical_delete_no_id(self):
        """Test DELETE with no ID anywhere."""
        strategy = SurgicalUpdate()
        
        data = [MockUser(id=1, name="Test")]
        data_by_id = {1: data[0]}
        
        event = ChangeEvent(
            table="users",
            type=ChangeType.DELETE,
            row_id=None,
            old_data={"name": "NoId"},  # No id field
        )
        
        result = strategy.apply(data, data_by_id, event, MockUser)
        
        # Can't delete without ID
        assert result.changed is False


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests combining components."""
    
    def test_surgical_then_refresh(self, sample_data, sample_data_by_id):
        """Test using surgical then falling back to refresh."""
        surgical = SurgicalUpdate()
        refresh = FullRefresh()
        
        # First, a surgical insert
        insert = ChangeEvent(
            table="users",
            type=ChangeType.INSERT,
            row_id=3,
            new_data={"id": 3, "name": "Charlie", "age": 30},
        )
        
        result1 = surgical.apply(sample_data, sample_data_by_id, insert, MockUser)
        assert len(result1.data) == 3
        
        # Then a refresh (simulated)
        result2 = refresh.apply(
            result1.data, result1.data_by_id, insert, MockUser
        )
        assert result2.changed is True  # Signals refresh needed
    
    def test_selector_chooses_correctly(self, config):
        """Test selector makes correct choices for different queries."""
        selector = StrategySelector()
        
        insert = ChangeEvent(table="users", type=ChangeType.INSERT, row_id=1)
        
        # Simple query -> Surgical
        simple = QuerySignature(table="users")
        assert isinstance(
            selector.select(simple, insert, config), SurgicalUpdate
        )
        
        # Limited query -> Refresh
        limited = QuerySignature(table="users", limit=10)
        assert isinstance(
            selector.select(limited, insert, config), FullRefresh
        )
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test full update workflow."""
        # Start with data
        data = [MockUser(id=1, name="Alice", age=25)]
        data_by_id = {1: data[0]}
        
        selector = StrategySelector()
        config = LiveQueryConfig()
        sig = QuerySignature(table="users")
        
        # INSERT event
        insert = ChangeEvent(
            table="users",
            type=ChangeType.INSERT,
            row_id=2,
            new_data={"id": 2, "name": "Bob", "age": 28},
        )
        
        strategy = selector.select(sig, insert, config)
        result = strategy.apply(data, data_by_id, insert, MockUser)
        
        assert result.changed is True
        assert len(result.data) == 2
        assert result.data[1].name == "Bob"
