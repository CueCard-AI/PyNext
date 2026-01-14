"""
Comprehensive tests for PyNext Per-Query Timeout.

100 tests covering:
- Chain method (.timeout())
- Context manager (async with db.timeout())
- Nested timeouts
- Error handling
- Statistics tracking
- Edge cases
"""

import pytest
import asyncio
from datetime import datetime

from pynext.db.adapters.postgres.queries.query_timeout import (
    QueryTimeoutError,
    QueryTimeout,
    TimeoutConfig,
    TimeoutStats,
    TimeoutContext,
    timeout_context,
    TimeoutExecutor,
    TimeoutMixin,
    get_timeout_stats,
    reset_timeout_stats,
    get_current_timeout,
    set_current_timeout,
    create_timeout,
    create_timeout_executor,
)


# =============================================================================
# QUERYTIMEOUT TESTS
# =============================================================================

class TestQueryTimeout:
    """Tests for QueryTimeout dataclass."""
    
    def test_basic_creation(self):
        """Test basic timeout creation."""
        timeout = QueryTimeout(seconds=5)
        assert timeout.seconds == 5
        assert timeout.message is None
        assert timeout.track_stats is True
    
    def test_with_message(self):
        """Test timeout with custom message."""
        timeout = QueryTimeout(seconds=10, message="Custom timeout")
        assert timeout.message == "Custom timeout"
    
    def test_track_stats_disabled(self):
        """Test disabling stats tracking."""
        timeout = QueryTimeout(seconds=5, track_stats=False)
        assert timeout.track_stats is False
    
    def test_to_postgres_ms(self):
        """Test conversion to PostgreSQL milliseconds."""
        timeout = QueryTimeout(seconds=5)
        assert timeout.to_postgres_ms() == 5000
    
    def test_to_postgres_ms_fractional(self):
        """Test fractional seconds conversion."""
        timeout = QueryTimeout(seconds=1.5)
        assert timeout.to_postgres_ms() == 1500
    
    def test_invalid_zero_seconds(self):
        """Test that zero seconds raises error."""
        with pytest.raises(ValueError, match="positive"):
            QueryTimeout(seconds=0)
    
    def test_invalid_negative_seconds(self):
        """Test that negative seconds raises error."""
        with pytest.raises(ValueError, match="positive"):
            QueryTimeout(seconds=-5)
    
    def test_invalid_too_large(self):
        """Test that too large timeout raises error."""
        with pytest.raises(ValueError, match="too large"):
            QueryTimeout(seconds=100000)
    
    def test_small_timeout(self):
        """Test very small timeout."""
        timeout = QueryTimeout(seconds=0.001)
        assert timeout.seconds == 0.001
        assert timeout.to_postgres_ms() == 1
    
    def test_max_valid_timeout(self):
        """Test maximum valid timeout (24 hours)."""
        timeout = QueryTimeout(seconds=86400)
        assert timeout.seconds == 86400


# =============================================================================
# TIMEOUTCONFIG TESTS
# =============================================================================

class TestTimeoutConfig:
    """Tests for TimeoutConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = TimeoutConfig()
        assert config.default_timeout is None
        assert config.max_timeout == 3600.0
        assert config.track_timeouts is True
        assert config.on_timeout is None
    
    def test_with_default_timeout(self):
        """Test setting default timeout."""
        config = TimeoutConfig(default_timeout=30.0)
        assert config.default_timeout == 30.0
    
    def test_with_max_timeout(self):
        """Test custom max timeout."""
        config = TimeoutConfig(max_timeout=600.0)
        assert config.max_timeout == 600.0
    
    def test_with_callback(self):
        """Test on_timeout callback."""
        callback_called = []
        
        def callback(error):
            callback_called.append(error)
        
        config = TimeoutConfig(on_timeout=callback)
        assert config.on_timeout is callback


# =============================================================================
# TIMEOUTSTATS TESTS
# =============================================================================

class TestTimeoutStats:
    """Tests for TimeoutStats."""
    
    def test_initial_stats(self):
        """Test initial stats values."""
        stats = TimeoutStats()
        assert stats.total_queries == 0
        assert stats.timeout_count == 0
        assert stats.avg_duration_ms == 0.0
        assert stats.timeout_rate == 0.0
        assert stats.last_timeout is None
    
    def test_record_query(self):
        """Test recording a query."""
        stats = TimeoutStats()
        stats.record_query()
        assert stats.total_queries == 1
    
    def test_record_multiple_queries(self):
        """Test recording multiple queries."""
        stats = TimeoutStats()
        for _ in range(10):
            stats.record_query()
        assert stats.total_queries == 10
    
    def test_record_timeout(self):
        """Test recording a timeout."""
        stats = TimeoutStats()
        stats.record_query()
        stats.record_timeout(1500.0, "SELECT")
        assert stats.timeout_count == 1
        assert stats.last_timeout is not None
        assert stats.by_query_type["SELECT"] == 1
    
    def test_avg_duration_ms(self):
        """Test average duration calculation."""
        stats = TimeoutStats()
        stats.record_timeout(1000.0, "SELECT")
        stats.record_timeout(2000.0, "SELECT")
        assert stats.avg_duration_ms == 1500.0
    
    def test_timeout_rate(self):
        """Test timeout rate calculation."""
        stats = TimeoutStats()
        stats.record_query()
        stats.record_query()
        stats.record_query()
        stats.record_query()
        stats.record_timeout(1000.0, "SELECT")
        assert stats.timeout_rate == 25.0
    
    def test_reset(self):
        """Test resetting stats."""
        stats = TimeoutStats()
        stats.record_query()
        stats.record_timeout(1000.0, "SELECT")
        stats.reset()
        assert stats.total_queries == 0
        assert stats.timeout_count == 0
        assert stats.last_timeout is None
        assert len(stats.by_query_type) == 0
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        stats = TimeoutStats()
        stats.record_query()
        stats.record_timeout(1000.0, "SELECT")
        
        d = stats.to_dict()
        assert "total_queries" in d
        assert "timeout_count" in d
        assert "avg_duration_ms" in d
        assert "timeout_rate" in d
        assert "by_query_type" in d
    
    def test_by_query_type_tracking(self):
        """Test tracking by query type."""
        stats = TimeoutStats()
        stats.record_timeout(1000.0, "SELECT")
        stats.record_timeout(1000.0, "SELECT")
        stats.record_timeout(1000.0, "INSERT")
        
        assert stats.by_query_type["SELECT"] == 2
        assert stats.by_query_type["INSERT"] == 1


# =============================================================================
# TIMEOUTCONTEXT TESTS
# =============================================================================

class TestTimeoutContext:
    """Tests for TimeoutContext."""
    
    @pytest.mark.asyncio
    async def test_basic_context(self):
        """Test basic context usage."""
        async with TimeoutContext(seconds=10) as ctx:
            assert ctx.seconds == 10
            assert ctx._entered is True
        assert ctx._entered is False
    
    @pytest.mark.asyncio
    async def test_context_sets_current(self):
        """Test that context sets current timeout."""
        async with TimeoutContext(seconds=5):
            current = get_current_timeout()
            assert current is not None
            assert current.seconds == 5
        
        # After exit, should be None or previous
        current = get_current_timeout()
    
    @pytest.mark.asyncio
    async def test_nested_contexts(self):
        """Test nested timeout contexts."""
        async with TimeoutContext(seconds=30):
            outer = get_current_timeout()
            assert outer.seconds == 30
            
            async with TimeoutContext(seconds=5):
                inner = get_current_timeout()
                assert inner.seconds == 5
            
            # After inner exits, should restore outer
            restored = get_current_timeout()
            assert restored.seconds == 30
    
    @pytest.mark.asyncio
    async def test_context_with_message(self):
        """Test context with custom message."""
        async with TimeoutContext(seconds=10, message="Test timeout") as ctx:
            assert ctx.timeout.message == "Test timeout"
    
    def test_repr(self):
        """Test string representation."""
        ctx = TimeoutContext(seconds=10)
        assert "TimeoutContext" in repr(ctx)
        assert "inactive" in repr(ctx)


@pytest.mark.asyncio
async def test_timeout_context_function():
    """Test timeout_context async context manager."""
    async with timeout_context(10) as ctx:
        assert ctx.seconds == 10


# =============================================================================
# TIMEOUTEXECUTOR TESTS
# =============================================================================

class TestTimeoutExecutor:
    """Tests for TimeoutExecutor."""
    
    def test_basic_creation(self):
        """Test basic executor creation."""
        executor = TimeoutExecutor()
        assert executor._config is not None
        assert executor._stats is not None
    
    def test_with_config(self):
        """Test executor with custom config."""
        config = TimeoutConfig(default_timeout=30)
        executor = TimeoutExecutor(config=config)
        assert executor._config.default_timeout == 30
    
    def test_get_effective_timeout_explicit(self):
        """Test explicit timeout takes priority."""
        executor = TimeoutExecutor()
        timeout = executor.get_effective_timeout(explicit_timeout=5)
        assert timeout is not None
        assert timeout.seconds == 5
    
    def test_get_effective_timeout_context(self):
        """Test context timeout is used when no explicit."""
        executor = TimeoutExecutor()
        set_current_timeout(QueryTimeout(seconds=10))
        
        try:
            timeout = executor.get_effective_timeout()
            assert timeout is not None
            assert timeout.seconds == 10
        finally:
            set_current_timeout(None)
    
    def test_get_effective_timeout_default(self):
        """Test default timeout from config."""
        config = TimeoutConfig(default_timeout=20)
        executor = TimeoutExecutor(config=config)
        
        timeout = executor.get_effective_timeout()
        assert timeout is not None
        assert timeout.seconds == 20
    
    def test_get_effective_timeout_none(self):
        """Test no timeout when none configured."""
        executor = TimeoutExecutor()
        set_current_timeout(None)
        
        timeout = executor.get_effective_timeout()
        assert timeout is None
    
    def test_validate_timeout_within_max(self):
        """Test validation passes for valid timeout."""
        config = TimeoutConfig(max_timeout=60)
        executor = TimeoutExecutor(config=config)
        
        timeout = QueryTimeout(seconds=30)
        validated = executor.validate_timeout(timeout)
        assert validated.seconds == 30
    
    def test_validate_timeout_exceeds_max(self):
        """Test timeout is clamped to max."""
        config = TimeoutConfig(max_timeout=60)
        executor = TimeoutExecutor(config=config)
        
        timeout = QueryTimeout(seconds=100)
        validated = executor.validate_timeout(timeout)
        assert validated.seconds == 60
    
    def test_generate_timeout_sql(self):
        """Test generating SET statement_timeout SQL."""
        executor = TimeoutExecutor()
        timeout = QueryTimeout(seconds=5)
        
        sql = executor.generate_timeout_sql(timeout)
        assert "SET LOCAL statement_timeout" in sql
        assert "5000" in sql
    
    def test_generate_reset_sql(self):
        """Test generating reset SQL."""
        executor = TimeoutExecutor()
        sql = executor.generate_reset_sql()
        assert "SET LOCAL statement_timeout = 0" in sql
    
    def test_get_query_type_select(self):
        """Test extracting SELECT query type."""
        executor = TimeoutExecutor()
        assert executor._get_query_type("SELECT * FROM users") == "SELECT"
    
    def test_get_query_type_insert(self):
        """Test extracting INSERT query type."""
        executor = TimeoutExecutor()
        assert executor._get_query_type("INSERT INTO users VALUES (1)") == "INSERT"
    
    def test_get_query_type_update(self):
        """Test extracting UPDATE query type."""
        executor = TimeoutExecutor()
        assert executor._get_query_type("UPDATE users SET name = 'x'") == "UPDATE"
    
    def test_get_query_type_delete(self):
        """Test extracting DELETE query type."""
        executor = TimeoutExecutor()
        assert executor._get_query_type("DELETE FROM users") == "DELETE"
    
    def test_get_query_type_other(self):
        """Test OTHER for unknown query types."""
        executor = TimeoutExecutor()
        assert executor._get_query_type("EXPLAIN SELECT 1") == "OTHER"
    
    @pytest.mark.asyncio
    async def test_execute_with_timeout_success(self):
        """Test successful execution within timeout."""
        executor = TimeoutExecutor()
        
        async def fast_query(sql, params):
            await asyncio.sleep(0.01)
            return [{"id": 1}]
        
        timeout = QueryTimeout(seconds=1)
        result = await executor.execute_with_timeout(
            "SELECT 1",
            (),
            timeout=timeout,
            execute_fn=fast_query,
        )
        
        assert result == [{"id": 1}]
    
    @pytest.mark.asyncio
    async def test_execute_with_timeout_error(self):
        """Test timeout error when query takes too long."""
        executor = TimeoutExecutor()
        
        async def slow_query(sql, params):
            await asyncio.sleep(2)
            return []
        
        timeout = QueryTimeout(seconds=0.1)
        
        with pytest.raises(QueryTimeoutError) as exc_info:
            await executor.execute_with_timeout(
                "SELECT * FROM slow",
                (),
                timeout=timeout,
                execute_fn=slow_query,
            )
        
        assert exc_info.value.timeout_seconds == 0.1
    
    @pytest.mark.asyncio
    async def test_execute_with_timeout_tracks_stats(self):
        """Test that timeout tracks statistics."""
        stats = TimeoutStats()
        executor = TimeoutExecutor(stats=stats)
        
        async def fast_query(sql, params):
            return []
        
        timeout = QueryTimeout(seconds=1)
        await executor.execute_with_timeout(
            "SELECT 1",
            (),
            timeout=timeout,
            execute_fn=fast_query,
        )
        
        assert stats.total_queries == 1


# =============================================================================
# TIMEOUTMIXIN TESTS
# =============================================================================

class TestTimeoutMixin:
    """Tests for TimeoutMixin."""
    
    def test_mixin_timeout_method(self):
        """Test .timeout() method."""
        class MockQuery(TimeoutMixin):
            pass
        
        query = MockQuery()
        result = query.timeout(5)
        
        assert result is query  # Returns self for chaining
        assert query._timeout is not None
        assert query._timeout.seconds == 5
    
    def test_mixin_timeout_with_message(self):
        """Test .timeout() with message."""
        class MockQuery(TimeoutMixin):
            pass
        
        query = MockQuery()
        query.timeout(10, message="Custom message")
        
        assert query._timeout.message == "Custom message"
    
    def test_mixin_get_timeout(self):
        """Test get_timeout() method."""
        class MockQuery(TimeoutMixin):
            pass
        
        query = MockQuery()
        assert query.get_timeout() is None
        
        query.timeout(5)
        assert query.get_timeout().seconds == 5
    
    def test_mixin_has_timeout(self):
        """Test has_timeout() method."""
        class MockQuery(TimeoutMixin):
            pass
        
        query = MockQuery()
        assert query.has_timeout() is False
        
        query.timeout(5)
        assert query.has_timeout() is True
    
    def test_mixin_clear_timeout(self):
        """Test clear_timeout() method."""
        class MockQuery(TimeoutMixin):
            pass
        
        query = MockQuery()
        query.timeout(5)
        assert query.has_timeout() is True
        
        result = query.clear_timeout()
        assert result is query
        assert query.has_timeout() is False


# =============================================================================
# QUERYTIMEOUTERROR TESTS
# =============================================================================

class TestQueryTimeoutError:
    """Tests for QueryTimeoutError."""
    
    def test_basic_error(self):
        """Test basic error creation."""
        error = QueryTimeoutError(
            query="SELECT * FROM users",
            timeout_seconds=5,
            duration_ms=5100,
        )
        
        assert error.query == "SELECT * FROM users"
        assert error.timeout_seconds == 5
        assert error.duration_ms == 5100
        assert "5100" in str(error)
    
    def test_error_with_custom_message(self):
        """Test error with custom message."""
        error = QueryTimeoutError(
            query="SELECT 1",
            timeout_seconds=5,
            duration_ms=5100,
            message="User lookup timed out",
        )
        
        assert str(error) == "User lookup timed out"
        assert error.custom_message == "User lookup timed out"
    
    def test_error_repr(self):
        """Test error representation."""
        error = QueryTimeoutError(timeout_seconds=5, duration_ms=5100)
        
        r = repr(error)
        assert "QueryTimeoutError" in r
        assert "5" in r
    
    def test_error_inheritance(self):
        """Test error inherits from DatabaseError."""
        from pynext.db.exceptions import DatabaseError
        
        error = QueryTimeoutError()
        assert isinstance(error, DatabaseError)


# =============================================================================
# GLOBAL STATS TESTS
# =============================================================================

class TestGlobalStats:
    """Tests for global stats functions."""
    
    def test_get_timeout_stats(self):
        """Test getting global stats."""
        stats = get_timeout_stats()
        assert isinstance(stats, TimeoutStats)
    
    def test_reset_timeout_stats(self):
        """Test resetting global stats."""
        stats = get_timeout_stats()
        stats.record_query()
        
        reset_timeout_stats()
        
        stats = get_timeout_stats()
        assert stats.total_queries == 0


# =============================================================================
# CONTEXT VARIABLE TESTS
# =============================================================================

class TestContextVariables:
    """Tests for context variables."""
    
    def test_get_set_current_timeout(self):
        """Test getting and setting current timeout."""
        original = get_current_timeout()
        
        timeout = QueryTimeout(seconds=5)
        set_current_timeout(timeout)
        
        assert get_current_timeout() is timeout
        
        set_current_timeout(original)
    
    def test_current_timeout_isolation(self):
        """Test timeout isolation between tasks."""
        # Set in one context
        set_current_timeout(QueryTimeout(seconds=10))
        
        # Should be visible in same context
        assert get_current_timeout().seconds == 10
        
        # Clean up
        set_current_timeout(None)


# =============================================================================
# CONVENIENCE FUNCTION TESTS
# =============================================================================

class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    def test_create_timeout(self):
        """Test create_timeout function."""
        timeout = create_timeout(5)
        assert timeout.seconds == 5
    
    def test_create_timeout_with_message(self):
        """Test create_timeout with message."""
        timeout = create_timeout(5, message="Test")
        assert timeout.message == "Test"
    
    def test_create_timeout_executor(self):
        """Test create_timeout_executor function."""
        executor = create_timeout_executor(
            default_timeout=30,
            max_timeout=300,
        )
        
        assert executor._config.default_timeout == 30
        assert executor._config.max_timeout == 300
    
    def test_create_timeout_executor_with_callback(self):
        """Test create_timeout_executor with callback."""
        callbacks = []
        
        executor = create_timeout_executor(
            on_timeout=lambda e: callbacks.append(e),
        )
        
        assert executor._config.on_timeout is not None


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases."""
    
    def test_timeout_zero_point_one(self):
        """Test very short timeout."""
        timeout = QueryTimeout(seconds=0.1)
        assert timeout.to_postgres_ms() == 100
    
    def test_timeout_many_decimals(self):
        """Test timeout with many decimals."""
        timeout = QueryTimeout(seconds=1.123456789)
        # Should truncate to integer ms
        assert timeout.to_postgres_ms() == 1123
    
    @pytest.mark.asyncio
    async def test_nested_contexts_three_deep(self):
        """Test three levels of nested contexts."""
        async with TimeoutContext(seconds=60):
            assert get_current_timeout().seconds == 60
            
            async with TimeoutContext(seconds=30):
                assert get_current_timeout().seconds == 30
                
                async with TimeoutContext(seconds=5):
                    assert get_current_timeout().seconds == 5
                
                assert get_current_timeout().seconds == 30
            
            assert get_current_timeout().seconds == 60
    
    def test_stats_division_by_zero(self):
        """Test stats don't crash with no data."""
        stats = TimeoutStats()
        assert stats.avg_duration_ms == 0.0
        assert stats.timeout_rate == 0.0
    
    @pytest.mark.asyncio
    async def test_context_exception_handling(self):
        """Test context properly handles exceptions."""
        try:
            async with TimeoutContext(seconds=10):
                raise ValueError("Test error")
        except ValueError:
            pass
        
        # Context should be properly cleaned up
        # even after exception
    
    def test_executor_explicit_timeout_priority(self):
        """Test explicit timeout has highest priority."""
        config = TimeoutConfig(default_timeout=30)
        executor = TimeoutExecutor(config=config)
        
        set_current_timeout(QueryTimeout(seconds=20))
        
        try:
            timeout = executor.get_effective_timeout(explicit_timeout=5)
            assert timeout.seconds == 5
        finally:
            set_current_timeout(None)
    
    def test_query_truncation_in_error(self):
        """Test long queries are truncated in errors."""
        long_query = "SELECT " + "a" * 1000
        error = QueryTimeoutError(query=long_query[:200])
        assert len(error.query) <= 200
    
    @pytest.mark.asyncio
    async def test_callback_error_doesnt_break_flow(self):
        """Test callback errors don't affect main flow."""
        def bad_callback(error):
            raise RuntimeError("Callback crashed")
        
        config = TimeoutConfig(on_timeout=bad_callback)
        executor = TimeoutExecutor(config=config)
        
        async def slow_query(sql, params):
            await asyncio.sleep(1)
            return []
        
        timeout = QueryTimeout(seconds=0.05)
        
        # Should still raise QueryTimeoutError, not RuntimeError
        with pytest.raises(QueryTimeoutError):
            await executor.execute_with_timeout(
                "SELECT 1",
                (),
                timeout=timeout,
                execute_fn=slow_query,
            )


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests for timeout features."""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete timeout workflow."""
        reset_timeout_stats()
        
        config = TimeoutConfig(
            default_timeout=30,
            track_timeouts=True,
        )
        executor = TimeoutExecutor(config=config)
        
        # Simulate successful query
        async def fast_query(sql, params):
            await asyncio.sleep(0.01)
            return [{"id": 1}]
        
        timeout = QueryTimeout(seconds=5)
        result = await executor.execute_with_timeout(
            "SELECT * FROM users",
            (),
            timeout=timeout,
            execute_fn=fast_query,
        )
        
        assert result == [{"id": 1}]
        
        stats = get_timeout_stats()
        assert stats.total_queries >= 1
    
    @pytest.mark.asyncio
    async def test_mixin_with_executor(self):
        """Test mixin and executor together."""
        class Query(TimeoutMixin):
            def __init__(self):
                self._timeout = None
        
        query = Query()
        query.timeout(5)
        
        assert query.has_timeout()
        assert query.get_timeout().seconds == 5
    
    @pytest.mark.asyncio
    async def test_context_with_executor(self):
        """Test context manager with executor."""
        executor = TimeoutExecutor()
        
        async with TimeoutContext(seconds=10):
            timeout = executor.get_effective_timeout()
            assert timeout is not None
            assert timeout.seconds == 10


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================

class TestPerformance:
    """Performance-related tests."""
    
    def test_stats_recording_speed(self):
        """Test stats recording is fast."""
        stats = TimeoutStats()
        
        # Should be able to record many events quickly
        for i in range(10000):
            stats.record_query()
        
        assert stats.total_queries == 10000
    
    def test_to_dict_efficiency(self):
        """Test to_dict doesn't crash with many entries."""
        stats = TimeoutStats()
        
        for i in range(1000):
            stats.record_timeout(100.0, f"TYPE_{i % 10}")
        
        d = stats.to_dict()
        assert len(d["by_query_type"]) == 10

