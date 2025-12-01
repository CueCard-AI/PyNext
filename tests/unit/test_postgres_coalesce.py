"""
Tests for PostgreSQL Query Coalescing.

Tests cover:
- CoalescingConfig validation and defaults
- Query deduplication
- Result broadcasting
- Error broadcasting
- Max waiters limit
- Statistics tracking
- Concurrent access
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from pynext.db.adapters.postgres_coalesce import (
    CoalescingConfig,
    PendingQuery,
    CoalescingStats,
    CoalescingLimitError,
    QueryCoalescer,
    aggressive_coalescing_config,
    conservative_coalescing_config,
    disabled_coalescing_config,
)


# =============================================================================
# CoalescingConfig Tests
# =============================================================================

class TestCoalescingConfig:
    """Tests for CoalescingConfig dataclass."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = CoalescingConfig()
        assert config.enabled is True
        assert config.window_ms == 5.0
        assert config.max_waiters == 100
        assert config.coalesce_reads is True
        assert config.coalesce_writes is False
    
    def test_custom_window(self):
        """Test custom window."""
        config = CoalescingConfig(window_ms=20.0)
        assert config.window_ms == 20.0
    
    def test_custom_max_waiters(self):
        """Test custom max_waiters."""
        config = CoalescingConfig(max_waiters=500)
        assert config.max_waiters == 500
    
    def test_coalesce_writes_enabled(self):
        """Test enabling write coalescing."""
        config = CoalescingConfig(coalesce_writes=True)
        assert config.coalesce_writes is True
    
    def test_negative_window_raises(self):
        """Test that negative window raises error."""
        with pytest.raises(ValueError, match="window_ms must be >= 0"):
            CoalescingConfig(window_ms=-1.0)
    
    def test_zero_max_waiters_raises(self):
        """Test that zero max_waiters raises error."""
        with pytest.raises(ValueError, match="max_waiters must be >= 1"):
            CoalescingConfig(max_waiters=0)
    
    def test_disabled_config(self):
        """Test disabled configuration."""
        config = CoalescingConfig(enabled=False)
        assert config.enabled is False


# =============================================================================
# PendingQuery Tests
# =============================================================================

class TestPendingQuery:
    """Tests for PendingQuery dataclass."""
    
    def test_basic_pending_query(self):
        """Test basic pending query creation."""
        pq = PendingQuery(
            key="abc123",
            query="SELECT * FROM users",
        )
        assert pq.key == "abc123"
        assert pq.query == "SELECT * FROM users"
        assert pq.waiters == 1
    
    def test_pending_query_with_params(self):
        """Test pending query with parameters."""
        pq = PendingQuery(
            key="abc123",
            query="SELECT * FROM users WHERE id = $1",
            params=(1,),
        )
        assert pq.params == (1,)
    
    def test_elapsed_time(self):
        """Test elapsed time calculation."""
        pq = PendingQuery(key="abc123", query="SELECT 1")
        # Should have some elapsed time
        assert pq.elapsed_ms >= 0


# =============================================================================
# CoalescingStats Tests
# =============================================================================

class TestCoalescingStats:
    """Tests for CoalescingStats dataclass."""
    
    def test_initial_stats(self):
        """Test initial statistics."""
        stats = CoalescingStats()
        assert stats.total_queries == 0
        assert stats.coalesced_queries == 0
        assert stats.executed_queries == 0
    
    def test_savings_percent_zero(self):
        """Test savings with no queries."""
        stats = CoalescingStats()
        assert stats.savings_percent == 0.0
    
    def test_savings_percent_calculation(self):
        """Test savings calculation."""
        stats = CoalescingStats(
            total_queries=100,
            coalesced_queries=90,
            executed_queries=10,
        )
        assert stats.savings_percent == 90.0
    
    def test_avg_waiters_calculation(self):
        """Test average waiters calculation."""
        stats = CoalescingStats(
            executed_queries=10,
            total_waiters=50,
        )
        assert stats.avg_waiters_per_query == 5.0
    
    def test_to_dict(self):
        """Test dictionary conversion."""
        stats = CoalescingStats(total_queries=10)
        d = stats.to_dict()
        assert "total_queries" in d
        assert "savings_percent" in d


# =============================================================================
# QueryCoalescer Basic Tests
# =============================================================================

class TestQueryCoalescerBasic:
    """Tests for basic QueryCoalescer operations."""
    
    @pytest.fixture
    def coalescer(self):
        return QueryCoalescer()
    
    @pytest.mark.asyncio
    async def test_single_query_execution(self, coalescer):
        """Test single query executes normally."""
        async def executor(query):
            return [{"id": 1}]
        
        result = await coalescer.execute_or_join(
            "SELECT * FROM users",
            executor=executor,
        )
        
        assert result == [{"id": 1}]
    
    @pytest.mark.asyncio
    async def test_query_with_params(self, coalescer):
        """Test query with parameters."""
        async def executor(query, params):
            return [{"id": params[0]}]
        
        result = await coalescer.execute_or_join(
            "SELECT * FROM users WHERE id = $1",
            params=(1,),
            executor=executor,
        )
        
        assert result == [{"id": 1}]
    
    @pytest.mark.asyncio
    async def test_pending_count(self, coalescer):
        """Test pending count starts at zero."""
        assert coalescer.pending_count == 0
    
    @pytest.mark.asyncio
    async def test_bypass_coalescing(self, coalescer):
        """Test bypass flag skips coalescing."""
        call_count = 0
        
        async def executor(query):
            nonlocal call_count
            call_count += 1
            return call_count
        
        # Both should execute
        r1 = await coalescer.execute_or_join("SELECT 1", executor=executor, bypass=True)
        r2 = await coalescer.execute_or_join("SELECT 1", executor=executor, bypass=True)
        
        assert r1 == 1
        assert r2 == 2
    
    @pytest.mark.asyncio
    async def test_disabled_coalescing(self):
        """Test disabled coalescing executes all."""
        coalescer = QueryCoalescer(CoalescingConfig(enabled=False))
        call_count = 0
        
        async def executor(query):
            nonlocal call_count
            call_count += 1
            return call_count
        
        # Both should execute
        r1 = await coalescer.execute_or_join("SELECT 1", executor=executor)
        r2 = await coalescer.execute_or_join("SELECT 1", executor=executor)
        
        assert r1 == 1
        assert r2 == 2


# =============================================================================
# Query Deduplication Tests
# =============================================================================

class TestQueryDeduplication:
    """Tests for query deduplication."""
    
    @pytest.mark.asyncio
    async def test_identical_queries_coalesced(self):
        """Test identical concurrent queries are coalesced."""
        coalescer = QueryCoalescer()
        execution_count = 0
        
        async def slow_executor(query):
            nonlocal execution_count
            execution_count += 1
            await asyncio.sleep(0.05)  # Simulate DB call
            return {"count": execution_count}
        
        # Launch multiple identical queries concurrently
        results = await asyncio.gather(
            coalescer.execute_or_join("SELECT 1", executor=slow_executor),
            coalescer.execute_or_join("SELECT 1", executor=slow_executor),
            coalescer.execute_or_join("SELECT 1", executor=slow_executor),
        )
        
        # All should get same result
        assert all(r == results[0] for r in results)
        # Only one execution should have happened
        assert execution_count == 1
    
    @pytest.mark.asyncio
    async def test_different_queries_not_coalesced(self):
        """Test different queries are not coalesced."""
        coalescer = QueryCoalescer()
        
        async def executor(query):
            await asyncio.sleep(0.01)
            return query
        
        results = await asyncio.gather(
            coalescer.execute_or_join("SELECT 1", executor=executor),
            coalescer.execute_or_join("SELECT 2", executor=executor),
        )
        
        assert results[0] != results[1]
    
    @pytest.mark.asyncio
    async def test_different_params_not_coalesced(self):
        """Test same query with different params are not coalesced."""
        coalescer = QueryCoalescer()
        execution_count = 0
        
        async def executor(query, params):
            nonlocal execution_count
            execution_count += 1
            await asyncio.sleep(0.01)
            return params[0]
        
        results = await asyncio.gather(
            coalescer.execute_or_join("SELECT $1", params=(1,), executor=executor),
            coalescer.execute_or_join("SELECT $1", params=(2,), executor=executor),
        )
        
        assert results[0] == 1
        assert results[1] == 2
        assert execution_count == 2
    
    @pytest.mark.asyncio
    async def test_write_queries_not_coalesced_by_default(self):
        """Test write queries are not coalesced by default."""
        coalescer = QueryCoalescer()
        execution_count = 0
        
        async def executor(query):
            nonlocal execution_count
            execution_count += 1
            await asyncio.sleep(0.01)
            return execution_count
        
        results = await asyncio.gather(
            coalescer.execute_or_join("INSERT INTO users VALUES (1)", executor=executor),
            coalescer.execute_or_join("INSERT INTO users VALUES (1)", executor=executor),
        )
        
        # Both should execute
        assert execution_count == 2


# =============================================================================
# Result Broadcasting Tests
# =============================================================================

class TestResultBroadcasting:
    """Tests for result broadcasting to waiters."""
    
    @pytest.mark.asyncio
    async def test_result_broadcast_to_all_waiters(self):
        """Test result is broadcast to all waiting queries."""
        coalescer = QueryCoalescer()
        
        async def slow_executor(query):
            await asyncio.sleep(0.05)
            return {"data": "result"}
        
        results = await asyncio.gather(
            coalescer.execute_or_join("SELECT 1", executor=slow_executor),
            coalescer.execute_or_join("SELECT 1", executor=slow_executor),
            coalescer.execute_or_join("SELECT 1", executor=slow_executor),
            coalescer.execute_or_join("SELECT 1", executor=slow_executor),
            coalescer.execute_or_join("SELECT 1", executor=slow_executor),
        )
        
        # All should get identical result
        assert all(r == {"data": "result"} for r in results)
    
    @pytest.mark.asyncio
    async def test_error_broadcast_to_all_waiters(self):
        """Test errors are broadcast to all waiters."""
        coalescer = QueryCoalescer()
        
        async def failing_executor(query):
            await asyncio.sleep(0.05)
            raise ValueError("Database error")
        
        with pytest.raises(ValueError, match="Database error"):
            await asyncio.gather(
                coalescer.execute_or_join("SELECT 1", executor=failing_executor),
                coalescer.execute_or_join("SELECT 1", executor=failing_executor),
            )


# =============================================================================
# Max Waiters Tests
# =============================================================================

class TestMaxWaiters:
    """Tests for max_waiters limit."""
    
    @pytest.mark.asyncio
    async def test_max_waiters_limit(self):
        """Test max_waiters limit is enforced."""
        coalescer = QueryCoalescer(CoalescingConfig(max_waiters=2))
        
        async def slow_executor(query):
            await asyncio.sleep(0.5)
            return "result"
        
        # Start first query
        task1 = asyncio.create_task(
            coalescer.execute_or_join("SELECT 1", executor=slow_executor)
        )
        await asyncio.sleep(0.01)
        
        # Second should join
        task2 = asyncio.create_task(
            coalescer.execute_or_join("SELECT 1", executor=slow_executor)
        )
        await asyncio.sleep(0.01)
        
        # Third should fail (max_waiters=2)
        with pytest.raises(CoalescingLimitError):
            await coalescer.execute_or_join("SELECT 1", executor=slow_executor)
        
        # Cleanup
        task1.cancel()
        task2.cancel()
        try:
            await task1
        except asyncio.CancelledError:
            pass
        try:
            await task2
        except asyncio.CancelledError:
            pass
    
    def test_coalescing_limit_error_attributes(self):
        """Test CoalescingLimitError has correct attributes."""
        error = CoalescingLimitError("SELECT 1", 100, 100)
        
        assert error.query == "SELECT 1"
        assert error.current_waiters == 100
        assert error.max_waiters == 100


# =============================================================================
# Statistics Tests
# =============================================================================

class TestCoalescingStatistics:
    """Tests for coalescing statistics."""
    
    @pytest.mark.asyncio
    async def test_stats_after_coalesced_queries(self):
        """Test statistics after coalesced queries."""
        coalescer = QueryCoalescer()
        
        async def slow_executor(query):
            await asyncio.sleep(0.02)
            return "result"
        
        await asyncio.gather(
            coalescer.execute_or_join("SELECT 1", executor=slow_executor),
            coalescer.execute_or_join("SELECT 1", executor=slow_executor),
            coalescer.execute_or_join("SELECT 1", executor=slow_executor),
        )
        
        stats = coalescer.get_stats()
        assert stats.total_queries == 3
        assert stats.executed_queries == 1
        assert stats.coalesced_queries == 2
    
    @pytest.mark.asyncio
    async def test_stats_savings_percent(self):
        """Test savings percentage calculation."""
        coalescer = QueryCoalescer()
        
        async def slow_executor(query):
            await asyncio.sleep(0.02)
            return "result"
        
        # 10 identical queries, should only execute 1
        await asyncio.gather(*[
            coalescer.execute_or_join("SELECT 1", executor=slow_executor)
            for _ in range(10)
        ])
        
        stats = coalescer.get_stats()
        assert stats.savings_percent == 90.0
    
    @pytest.mark.asyncio
    async def test_stats_reset(self):
        """Test statistics reset."""
        coalescer = QueryCoalescer()
        
        async def executor(query):
            return "result"
        
        await coalescer.execute_or_join("SELECT 1", executor=executor)
        
        coalescer.reset_stats()
        stats = coalescer.get_stats()
        
        assert stats.total_queries == 0
    
    @pytest.mark.asyncio
    async def test_get_pending(self):
        """Test getting pending queries."""
        coalescer = QueryCoalescer()
        
        async def slow_executor(query):
            await asyncio.sleep(0.5)
            return "result"
        
        task = asyncio.create_task(
            coalescer.execute_or_join("SELECT 1", executor=slow_executor)
        )
        await asyncio.sleep(0.01)
        
        pending = coalescer.get_pending()
        assert len(pending) == 1
        
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


# =============================================================================
# Convenience Config Tests
# =============================================================================

class TestConvenienceConfigs:
    """Tests for convenience configuration functions."""
    
    def test_aggressive_config(self):
        """Test aggressive coalescing configuration."""
        config = aggressive_coalescing_config()
        assert config.window_ms == 20.0
        assert config.max_waiters == 500
    
    def test_conservative_config(self):
        """Test conservative coalescing configuration."""
        config = conservative_coalescing_config()
        assert config.window_ms == 2.0
        assert config.max_waiters == 50
    
    def test_disabled_config(self):
        """Test disabled coalescing configuration."""
        config = disabled_coalescing_config()
        assert config.enabled is False


# =============================================================================
# Repr Tests
# =============================================================================

class TestCoalescerRepr:
    """Tests for coalescer string representation."""
    
    def test_repr(self):
        """Test coalescer repr."""
        coalescer = QueryCoalescer()
        repr_str = repr(coalescer)
        assert "QueryCoalescer" in repr_str


# =============================================================================
# Edge Cases Tests
# =============================================================================

class TestCoalescerEdgeCases:
    """Tests for coalescer edge cases."""
    
    @pytest.mark.asyncio
    async def test_empty_query(self):
        """Test coalescing empty query."""
        coalescer = QueryCoalescer()
        
        async def executor(query):
            return "empty"
        
        result = await coalescer.execute_or_join("", executor=executor)
        assert result == "empty"
    
    @pytest.mark.asyncio
    async def test_sync_executor(self):
        """Test with synchronous executor."""
        coalescer = QueryCoalescer()
        
        def sync_executor(query):
            return "sync_result"
        
        result = await coalescer.execute_or_join("SELECT 1", executor=sync_executor)
        assert result == "sync_result"
    
    @pytest.mark.asyncio
    async def test_none_result(self):
        """Test coalescing query that returns None."""
        coalescer = QueryCoalescer()
        
        async def executor(query):
            return None
        
        result = await coalescer.execute_or_join("SELECT NULL", executor=executor)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_large_result(self):
        """Test coalescing query with large result."""
        coalescer = QueryCoalescer()
        large_result = [{"id": i, "data": "x" * 1000} for i in range(1000)]
        
        async def executor(query):
            return large_result
        
        result = await coalescer.execute_or_join("SELECT *", executor=executor)
        assert result == large_result


# =============================================================================
# Concurrent Access Tests
# =============================================================================

class TestCoalescerConcurrency:
    """Tests for concurrent coalescer access."""
    
    @pytest.mark.asyncio
    async def test_many_concurrent_identical_queries(self):
        """Test many concurrent identical queries."""
        coalescer = QueryCoalescer(CoalescingConfig(max_waiters=1000))
        execution_count = 0
        
        async def slow_executor(query):
            nonlocal execution_count
            execution_count += 1
            await asyncio.sleep(0.05)
            return "result"
        
        # 100 concurrent identical queries
        results = await asyncio.gather(*[
            coalescer.execute_or_join("SELECT 1", executor=slow_executor)
            for _ in range(100)
        ])
        
        assert all(r == "result" for r in results)
        assert execution_count == 1  # Only one execution
    
    @pytest.mark.asyncio
    async def test_mixed_queries_concurrent(self):
        """Test mixed queries executing concurrently."""
        coalescer = QueryCoalescer()
        
        async def executor(query):
            await asyncio.sleep(0.01)
            return query
        
        # Mix of identical and different queries
        results = await asyncio.gather(
            coalescer.execute_or_join("SELECT 1", executor=executor),
            coalescer.execute_or_join("SELECT 1", executor=executor),
            coalescer.execute_or_join("SELECT 2", executor=executor),
            coalescer.execute_or_join("SELECT 2", executor=executor),
            coalescer.execute_or_join("SELECT 3", executor=executor),
        )
        
        assert results[0] == results[1] == "SELECT 1"
        assert results[2] == results[3] == "SELECT 2"
        assert results[4] == "SELECT 3"

