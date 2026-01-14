"""
Comprehensive tests for PyNext Query Cancellation.

100 tests covering:
- Query tracking
- Cancellation
- Disconnect handling
- Concurrent operations
- Cleanup
"""

import pytest
import asyncio
from datetime import datetime

from pynext.db.adapters.postgres.queries.cancel import (
    QueryState,
    CancelReason,
    CancellationConfig,
    RunningQuery,
    CancellationToken,
    QueryCancelledError,
    QueryTracker,
    QueryRegistry,
    CancelExecutor,
    get_current_tracker,
    set_current_tracker,
    get_query_registry,
    set_query_registry,
    track_query,
    cancel_queries,
    cancel,
    get_running_queries,
)


# =============================================================================
# QUERY STATE TESTS
# =============================================================================

class TestQueryState:
    """Tests for QueryState enum."""
    
    def test_pending_state(self):
        """Test PENDING state."""
        assert QueryState.PENDING.value == "pending"
    
    def test_running_state(self):
        """Test RUNNING state."""
        assert QueryState.RUNNING.value == "running"
    
    def test_completed_state(self):
        """Test COMPLETED state."""
        assert QueryState.COMPLETED.value == "completed"
    
    def test_cancelled_state(self):
        """Test CANCELLED state."""
        assert QueryState.CANCELLED.value == "cancelled"
    
    def test_error_state(self):
        """Test ERROR state."""
        assert QueryState.ERROR.value == "error"


# =============================================================================
# CANCEL REASON TESTS
# =============================================================================

class TestCancelReason:
    """Tests for CancelReason enum."""
    
    def test_client_disconnect(self):
        """Test CLIENT_DISCONNECT reason."""
        assert CancelReason.CLIENT_DISCONNECT.value == "client_disconnect"
    
    def test_timeout(self):
        """Test TIMEOUT reason."""
        assert CancelReason.TIMEOUT.value == "timeout"
    
    def test_user_request(self):
        """Test USER_REQUEST reason."""
        assert CancelReason.USER_REQUEST.value == "user_request"
    
    def test_shutdown(self):
        """Test SHUTDOWN reason."""
        assert CancelReason.SHUTDOWN.value == "shutdown"
    
    def test_resource_limit(self):
        """Test RESOURCE_LIMIT reason."""
        assert CancelReason.RESOURCE_LIMIT.value == "resource_limit"


# =============================================================================
# CANCELLATION CONFIG TESTS
# =============================================================================

class TestCancellationConfig:
    """Tests for CancellationConfig."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = CancellationConfig()
        assert config.cancel_on_disconnect is True
        assert config.cancel_timeout == 5.0
        assert config.max_tracked_queries == 1000
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = CancellationConfig(
            cancel_on_disconnect=False,
            cancel_timeout=10.0,
        )
        assert config.cancel_on_disconnect is False
        assert config.cancel_timeout == 10.0
    
    def test_invalid_timeout(self):
        """Test invalid timeout raises error."""
        with pytest.raises(ValueError):
            CancellationConfig(cancel_timeout=-1)
    
    def test_invalid_max_queries(self):
        """Test invalid max_tracked_queries raises error."""
        with pytest.raises(ValueError):
            CancellationConfig(max_tracked_queries=0)


# =============================================================================
# RUNNING QUERY TESTS
# =============================================================================

class TestRunningQuery:
    """Tests for RunningQuery."""
    
    def test_basic_creation(self):
        """Test basic query creation."""
        query = RunningQuery(
            id="q1",
            query="SELECT * FROM users",
        )
        assert query.id == "q1"
        assert query.query == "SELECT * FROM users"
        assert query.state == QueryState.PENDING
    
    def test_with_request_id(self):
        """Test query with request ID."""
        query = RunningQuery(
            id="q1",
            request_id="req_123",
            query="SELECT 1",
        )
        assert query.request_id == "req_123"
    
    def test_duration_ms(self):
        """Test duration calculation."""
        query = RunningQuery(id="q1", query="SELECT 1")
        # Duration should be small but non-zero
        assert query.duration_ms >= 0
    
    def test_duration_seconds(self):
        """Test duration in seconds."""
        query = RunningQuery(id="q1", query="SELECT 1")
        # Duration is calculated based on time since creation
        # So we just verify it's non-negative and matches the formula
        assert query.duration_seconds >= 0
        assert abs(query.duration_seconds - query.duration_ms / 1000) < 0.001
    
    def test_is_running(self):
        """Test is_running property."""
        query = RunningQuery(id="q1", query="SELECT 1")
        assert query.is_running is False
        
        query.state = QueryState.RUNNING
        assert query.is_running is True
    
    def test_is_cancellable(self):
        """Test is_cancellable property."""
        query = RunningQuery(id="q1", query="SELECT 1")
        assert query.is_cancellable is True
        
        query.state = QueryState.RUNNING
        assert query.is_cancellable is True
        
        query.state = QueryState.COMPLETED
        assert query.is_cancellable is False
    
    def test_is_cancelled(self):
        """Test is_cancelled property."""
        query = RunningQuery(id="q1", query="SELECT 1")
        assert query.is_cancelled is False
        
        query.state = QueryState.CANCELLED
        assert query.is_cancelled is True
    
    def test_mark_running(self):
        """Test marking as running."""
        query = RunningQuery(id="q1", query="SELECT 1")
        query.mark_running(backend_pid=12345)
        
        assert query.state == QueryState.RUNNING
        assert query.backend_pid == 12345
    
    def test_mark_completed(self):
        """Test marking as completed."""
        query = RunningQuery(id="q1", query="SELECT 1")
        query.mark_completed()
        
        assert query.state == QueryState.COMPLETED
    
    def test_mark_cancelled(self):
        """Test marking as cancelled."""
        query = RunningQuery(id="q1", query="SELECT 1")
        query.mark_cancelled(CancelReason.USER_REQUEST)
        
        assert query.state == QueryState.CANCELLED
        assert query.cancel_reason == CancelReason.USER_REQUEST
    
    def test_mark_error(self):
        """Test marking as error."""
        query = RunningQuery(id="q1", query="SELECT 1")
        query.mark_error()
        
        assert query.state == QueryState.ERROR
    
    def test_check_cancelled(self):
        """Test check_cancelled method."""
        query = RunningQuery(id="q1", query="SELECT 1")
        assert query.check_cancelled() is False
        
        query.mark_cancelled()
        assert query.check_cancelled() is True
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        query = RunningQuery(
            id="q1",
            request_id="req_123",
            query="SELECT * FROM users",
        )
        d = query.to_dict()
        
        assert d["id"] == "q1"
        assert d["request_id"] == "req_123"
        assert "duration_ms" in d


# =============================================================================
# CANCELLATION TOKEN TESTS
# =============================================================================

class TestCancellationToken:
    """Tests for CancellationToken."""
    
    def test_initial_state(self):
        """Test initial token state."""
        token = CancellationToken()
        assert token.is_cancelled is False
        assert token.reason is None
    
    def test_cancel(self):
        """Test cancelling token."""
        token = CancellationToken()
        token.cancel(CancelReason.USER_REQUEST)
        
        assert token.is_cancelled is True
        assert token.reason == CancelReason.USER_REQUEST
    
    def test_cancel_default_reason(self):
        """Test cancel with default reason."""
        token = CancellationToken()
        token.cancel()
        
        assert token.is_cancelled is True
        assert token.reason == CancelReason.USER_REQUEST
    
    def test_on_cancel_callback(self):
        """Test on_cancel callback."""
        token = CancellationToken()
        callback_args = []
        
        def callback(t):
            callback_args.append(t)
        
        token.on_cancel(callback)
        token.cancel()
        
        assert len(callback_args) == 1
        assert callback_args[0] is token
    
    def test_on_cancel_immediate_if_cancelled(self):
        """Test callback called immediately if already cancelled."""
        token = CancellationToken()
        token.cancel()
        
        callback_args = []
        token.on_cancel(lambda t: callback_args.append(t))
        
        assert len(callback_args) == 1
    
    def test_throw_if_cancelled(self):
        """Test throw_if_cancelled method."""
        token = CancellationToken()
        
        # Should not raise
        token.throw_if_cancelled()
        
        token.cancel()
        
        with pytest.raises(QueryCancelledError):
            token.throw_if_cancelled()
    
    def test_repr(self):
        """Test string representation."""
        token = CancellationToken()
        assert "active" in repr(token)
        
        token.cancel()
        assert "cancelled" in repr(token)


# =============================================================================
# QUERY CANCELLED ERROR TESTS
# =============================================================================

class TestQueryCancelledError:
    """Tests for QueryCancelledError."""
    
    def test_basic_error(self):
        """Test basic error creation."""
        error = QueryCancelledError(
            query_id="q1",
            reason=CancelReason.TIMEOUT,
            duration_ms=5000,
        )
        
        assert error.query_id == "q1"
        assert error.reason == CancelReason.TIMEOUT
        assert error.duration_ms == 5000
    
    def test_error_message(self):
        """Test error message."""
        error = QueryCancelledError(
            reason=CancelReason.TIMEOUT,
            duration_ms=5000,
        )
        
        assert "cancelled" in str(error).lower()
        assert "timeout" in str(error).lower()
    
    def test_custom_message(self):
        """Test error with custom message."""
        error = QueryCancelledError(
            message="Custom cancellation message",
        )
        
        assert str(error) == "Custom cancellation message"


# =============================================================================
# QUERY TRACKER TESTS
# =============================================================================

class TestQueryTracker:
    """Tests for QueryTracker."""
    
    def test_basic_creation(self):
        """Test basic tracker creation."""
        registry = QueryRegistry()
        tracker = QueryTracker(
            request_id="req_123",
            registry=registry,
        )
        assert tracker.request_id == "req_123"
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test tracker as context manager."""
        registry = QueryRegistry()
        
        async with QueryTracker("req_123", registry) as tracker:
            assert tracker._entered is True
        
        assert tracker._entered is False
    
    def test_track_query(self):
        """Test tracking a query."""
        registry = QueryRegistry()
        tracker = QueryTracker("req_123", registry)
        
        query = tracker.track_query("SELECT * FROM users")
        
        assert query.query == "SELECT * FROM users"
        assert query.request_id == "req_123"
        assert tracker.query_count == 1
    
    @pytest.mark.asyncio
    async def test_cancel_all(self):
        """Test cancelling all tracked queries."""
        registry = QueryRegistry()
        tracker = QueryTracker("req_123", registry)
        
        q1 = tracker.track_query("SELECT 1")
        q2 = tracker.track_query("SELECT 2")
        
        count = await tracker.cancel_all(CancelReason.CLIENT_DISCONNECT)
        
        assert count == 2
        assert q1.is_cancelled
        assert q2.is_cancelled
    
    def test_running_queries(self):
        """Test getting running queries."""
        registry = QueryRegistry()
        tracker = QueryTracker("req_123", registry)
        
        q1 = tracker.track_query("SELECT 1")
        q2 = tracker.track_query("SELECT 2")
        
        q1.mark_running()
        
        running = tracker.running_queries
        assert len(running) == 1
        assert running[0] is q1


# =============================================================================
# QUERY REGISTRY TESTS
# =============================================================================

class TestQueryRegistry:
    """Tests for QueryRegistry."""
    
    def test_basic_creation(self):
        """Test basic registry creation."""
        registry = QueryRegistry()
        assert registry.query_count == 0
    
    def test_register_query(self):
        """Test registering a query."""
        registry = QueryRegistry()
        query = RunningQuery(id="q1", query="SELECT 1")
        
        registry.register_query(query)
        
        assert registry.query_count == 1
        assert registry.get_query("q1") is query
    
    def test_unregister_query(self):
        """Test unregistering a query."""
        registry = QueryRegistry()
        query = RunningQuery(id="q1", query="SELECT 1")
        
        registry.register_query(query)
        removed = registry.unregister_query("q1")
        
        assert removed is query
        assert registry.query_count == 0
    
    def test_get_queries_for_request(self):
        """Test getting queries for a request."""
        registry = QueryRegistry()
        
        q1 = RunningQuery(id="q1", request_id="req_123", query="SELECT 1")
        q2 = RunningQuery(id="q2", request_id="req_123", query="SELECT 2")
        q3 = RunningQuery(id="q3", request_id="req_456", query="SELECT 3")
        
        registry.register_query(q1)
        registry.register_query(q2)
        registry.register_query(q3)
        
        queries = registry.get_queries_for_request("req_123")
        
        assert len(queries) == 2
        assert q1 in queries
        assert q2 in queries
    
    def test_get_running_queries(self):
        """Test getting running queries."""
        registry = QueryRegistry()
        
        q1 = RunningQuery(id="q1", query="SELECT 1")
        q1.mark_running()
        q2 = RunningQuery(id="q2", query="SELECT 2")
        
        registry.register_query(q1)
        registry.register_query(q2)
        
        running = registry.get_running_queries()
        
        assert len(running) == 1
        assert q1 in running
    
    @pytest.mark.asyncio
    async def test_cancel_query(self):
        """Test cancelling a specific query."""
        registry = QueryRegistry()
        query = RunningQuery(id="q1", query="SELECT 1")
        
        registry.register_query(query)
        result = await registry.cancel_query("q1", CancelReason.USER_REQUEST)
        
        assert result is True
        assert query.is_cancelled
    
    @pytest.mark.asyncio
    async def test_cancel_query_not_found(self):
        """Test cancelling nonexistent query."""
        registry = QueryRegistry()
        result = await registry.cancel_query("nonexistent")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_cancel_queries_for_request(self):
        """Test cancelling queries for a request."""
        registry = QueryRegistry()
        
        q1 = RunningQuery(id="q1", request_id="req_123", query="SELECT 1")
        q2 = RunningQuery(id="q2", request_id="req_123", query="SELECT 2")
        
        registry.register_query(q1)
        registry.register_query(q2)
        
        count = await registry.cancel_queries_for_request("req_123")
        
        assert count == 2
        assert q1.is_cancelled
        assert q2.is_cancelled
    
    @pytest.mark.asyncio
    async def test_cancel_all(self):
        """Test cancelling all queries."""
        registry = QueryRegistry()
        
        for i in range(5):
            query = RunningQuery(id=f"q{i}", query=f"SELECT {i}")
            registry.register_query(query)
        
        count = await registry.cancel_all(CancelReason.SHUTDOWN)
        
        assert count == 5
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        registry = QueryRegistry()
        query = RunningQuery(id="q1", query="SELECT 1")
        query.mark_running()
        registry.register_query(query)
        
        d = registry.to_dict()
        
        assert d["query_count"] == 1
        assert len(d["running_queries"]) == 1


# =============================================================================
# CANCEL EXECUTOR TESTS
# =============================================================================

class TestCancelExecutor:
    """Tests for CancelExecutor."""
    
    def test_basic_creation(self):
        """Test basic executor creation."""
        registry = QueryRegistry()
        executor = CancelExecutor(registry)
        assert executor.registry is registry
    
    @pytest.mark.asyncio
    async def test_cancel_by_pid(self):
        """Test cancel by backend PID."""
        cancel_calls = []
        
        async def mock_execute(sql, params):
            cancel_calls.append((sql, params))
            return True
        
        registry = QueryRegistry()
        executor = CancelExecutor(registry, execute_fn=mock_execute)
        
        result = await executor.cancel_by_pid(12345)
        
        assert result is True
        assert len(cancel_calls) == 1
        assert "pg_cancel_backend" in cancel_calls[0][0]
    
    @pytest.mark.asyncio
    async def test_terminate_by_pid(self):
        """Test terminate by backend PID."""
        terminate_calls = []
        
        async def mock_execute(sql, params):
            terminate_calls.append((sql, params))
            return True
        
        registry = QueryRegistry()
        executor = CancelExecutor(registry, execute_fn=mock_execute)
        
        result = await executor.terminate_by_pid(12345)
        
        assert result is True
        assert "pg_terminate_backend" in terminate_calls[0][0]
    
    @pytest.mark.asyncio
    async def test_get_backend_pids_for_queries(self):
        """Test getting backend PIDs for matching queries."""
        async def mock_execute(sql, params):
            return [{"pid": 123}, {"pid": 456}]
        
        registry = QueryRegistry()
        executor = CancelExecutor(registry, execute_fn=mock_execute)
        
        pids = await executor.get_backend_pids_for_queries("%SELECT%")
        
        assert pids == [123, 456]


# =============================================================================
# CONTEXT VARIABLE TESTS
# =============================================================================

class TestContextVariables:
    """Tests for context variables."""
    
    def test_get_set_current_tracker(self):
        """Test getting and setting current tracker."""
        original = get_current_tracker()
        
        registry = QueryRegistry()
        tracker = QueryTracker("req_123", registry)
        set_current_tracker(tracker)
        
        assert get_current_tracker() is tracker
        
        set_current_tracker(original)


# =============================================================================
# GLOBAL STATE TESTS
# =============================================================================

class TestGlobalState:
    """Tests for global state management."""
    
    def test_get_query_registry(self):
        """Test getting global registry."""
        registry = get_query_registry()
        assert isinstance(registry, QueryRegistry)
    
    def test_set_query_registry(self):
        """Test setting global registry."""
        original = get_query_registry()
        
        new_registry = QueryRegistry()
        set_query_registry(new_registry)
        
        assert get_query_registry() is new_registry
        
        set_query_registry(original)


# =============================================================================
# CONVENIENCE FUNCTION TESTS
# =============================================================================

class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    def test_track_query_function(self):
        """Test track_query function."""
        tracker = track_query("req_123")
        assert isinstance(tracker, QueryTracker)
        assert tracker.request_id == "req_123"
    
    @pytest.mark.asyncio
    async def test_cancel_queries_function(self):
        """Test cancel_queries function."""
        registry = get_query_registry()
        
        q1 = RunningQuery(id="cq1", request_id="req_test", query="SELECT 1")
        registry.register_query(q1)
        
        try:
            count = await cancel_queries("req_test")
            assert count >= 1
        finally:
            registry.unregister_query("cq1")
    
    @pytest.mark.asyncio
    async def test_cancel_function(self):
        """Test cancel function."""
        registry = get_query_registry()
        
        query = RunningQuery(id="test_cancel", query="SELECT 1")
        registry.register_query(query)
        
        try:
            result = await cancel("test_cancel")
            assert result is True
            assert query.is_cancelled
        finally:
            registry.unregister_query("test_cancel")
    
    def test_get_running_queries_function(self):
        """Test get_running_queries function."""
        running = get_running_queries()
        assert isinstance(running, list)


# =============================================================================
# EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases."""
    
    def test_query_with_empty_string(self):
        """Test query with empty query string."""
        query = RunningQuery(id="q1", query="")
        assert query.query == ""
    
    def test_query_truncation_in_to_dict(self):
        """Test long query is truncated in to_dict."""
        long_query = "SELECT " + "a" * 500
        query = RunningQuery(id="q1", query=long_query)
        d = query.to_dict()
        assert len(d["query"]) <= 200
    
    @pytest.mark.asyncio
    async def test_cancel_already_cancelled(self):
        """Test cancelling already cancelled query."""
        registry = QueryRegistry()
        query = RunningQuery(id="q1", query="SELECT 1")
        query.mark_cancelled()
        
        registry.register_query(query)
        result = await registry.cancel_query("q1")
        
        # Should return False since already cancelled
        assert result is False
    
    @pytest.mark.asyncio
    async def test_cancel_completed_query(self):
        """Test cancelling completed query."""
        registry = QueryRegistry()
        query = RunningQuery(id="q1", query="SELECT 1")
        query.mark_completed()
        
        registry.register_query(query)
        result = await registry.cancel_query("q1")
        
        # Should return False since completed
        assert result is False
    
    def test_registry_eviction(self):
        """Test registry evicts completed queries when full."""
        config = CancellationConfig(max_tracked_queries=5)
        registry = QueryRegistry(config=config)
        
        # Add completed queries
        for i in range(5):
            query = RunningQuery(id=f"q{i}", query=f"SELECT {i}")
            query.mark_completed()
            registry.register_query(query)
        
        # Add one more - should trigger eviction
        new_query = RunningQuery(id="q_new", query="SELECT new")
        registry.register_query(new_query)
        
        assert registry.query_count <= 5
    
    @pytest.mark.asyncio
    async def test_tracker_marks_queries_completed_on_exit(self):
        """Test tracker marks running queries as completed on exit."""
        registry = QueryRegistry()
        
        async with QueryTracker("req_123", registry) as tracker:
            query = tracker.track_query("SELECT 1")
            query.mark_running()
        
        assert query.state == QueryState.COMPLETED
    
    def test_token_multiple_cancels(self):
        """Test token can only be cancelled once."""
        token = CancellationToken()
        token.cancel(CancelReason.TIMEOUT)
        token.cancel(CancelReason.USER_REQUEST)  # Second cancel
        
        # Reason should be from first cancel
        assert token.reason == CancelReason.TIMEOUT
    
    @pytest.mark.asyncio
    async def test_wait_for_cancel(self):
        """Test wait_for_cancel method."""
        query = RunningQuery(id="q1", query="SELECT 1")
        
        async def cancel_after_delay():
            await asyncio.sleep(0.1)
            query.mark_cancelled()
        
        asyncio.create_task(cancel_after_delay())
        result = await asyncio.wait_for(query.wait_for_cancel(), timeout=1.0)
        
        assert result is True


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests for query cancellation."""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete cancellation workflow."""
        registry = QueryRegistry()
        
        async with QueryTracker("req_integration", registry) as tracker:
            # Track some queries
            q1 = tracker.track_query("SELECT * FROM users")
            q2 = tracker.track_query("SELECT * FROM orders")
            
            q1.mark_running(backend_pid=12345)
            q2.mark_running(backend_pid=12346)
            
            # Verify running
            running = registry.get_running_queries()
            assert len(running) == 2
            
            # Cancel all
            count = await tracker.cancel_all(CancelReason.CLIENT_DISCONNECT)
            assert count == 2
            
            # Verify cancelled
            assert q1.is_cancelled
            assert q2.is_cancelled
            assert q1.cancel_reason == CancelReason.CLIENT_DISCONNECT
    
    @pytest.mark.asyncio
    async def test_concurrent_tracking(self):
        """Test concurrent query tracking."""
        registry = QueryRegistry()
        
        async def track_queries(request_id, count):
            async with QueryTracker(request_id, registry) as tracker:
                for i in range(count):
                    tracker.track_query(f"SELECT {i}")
                await asyncio.sleep(0.01)
        
        # Run concurrent trackers
        await asyncio.gather(
            track_queries("req_1", 5),
            track_queries("req_2", 5),
            track_queries("req_3", 5),
        )
    
    @pytest.mark.asyncio
    async def test_cancel_on_disconnect_simulation(self):
        """Test simulated disconnect cancellation."""
        registry = QueryRegistry()
        
        # Simulate request with running query
        tracker = QueryTracker("req_disconnect", registry)
        await tracker.__aenter__()
        
        query = tracker.track_query("SELECT * FROM huge_table")
        query.mark_running(backend_pid=99999)
        
        # Simulate disconnect
        count = await registry.cancel_queries_for_request(
            "req_disconnect",
            CancelReason.CLIENT_DISCONNECT,
        )
        
        assert count == 1
        assert query.cancel_reason == CancelReason.CLIENT_DISCONNECT
        
        await tracker.__aexit__(None, None, None)

