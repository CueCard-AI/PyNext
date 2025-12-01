"""
Tests for PostgreSQL Query Pipeline.

Tests cover:
- PipelineConfig validation and defaults
- Single query pipelining
- Batch execution
- Auto-flush behavior
- Manual flush
- Error handling
- Statistics tracking
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from pynext.db.adapters.postgres_pipeline import (
    PipelineConfig,
    PipelinedQuery,
    PipelineStats,
    QueryPipeline,
    high_throughput_config,
    low_latency_config,
    disabled_pipeline_config,
)


# =============================================================================
# PipelineConfig Tests
# =============================================================================

class TestPipelineConfig:
    """Tests for PipelineConfig dataclass."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = PipelineConfig()
        assert config.enabled is True
        assert config.max_batch_size == 100
        assert config.max_wait_ms == 5.0
        assert config.auto_flush is True
    
    def test_custom_batch_size(self):
        """Test custom batch size."""
        config = PipelineConfig(max_batch_size=500)
        assert config.max_batch_size == 500
    
    def test_custom_wait_time(self):
        """Test custom wait time."""
        config = PipelineConfig(max_wait_ms=10.0)
        assert config.max_wait_ms == 10.0
    
    def test_zero_batch_size_raises(self):
        """Test that zero batch size raises error."""
        with pytest.raises(ValueError, match="max_batch_size must be >= 1"):
            PipelineConfig(max_batch_size=0)
    
    def test_negative_wait_raises(self):
        """Test that negative wait raises error."""
        with pytest.raises(ValueError, match="max_wait_ms must be >= 0"):
            PipelineConfig(max_wait_ms=-1.0)
    
    def test_disabled_auto_flush(self):
        """Test disabled auto flush."""
        config = PipelineConfig(auto_flush=False)
        assert config.auto_flush is False


# =============================================================================
# PipelinedQuery Tests
# =============================================================================

class TestPipelinedQuery:
    """Tests for PipelinedQuery dataclass."""
    
    def test_basic_pipelined_query(self):
        """Test basic pipelined query creation."""
        pq = PipelinedQuery(query="SELECT 1")
        assert pq.query == "SELECT 1"
        assert pq.params is None
    
    def test_pipelined_query_with_params(self):
        """Test pipelined query with parameters."""
        pq = PipelinedQuery(query="SELECT $1", params=(1,))
        assert pq.params == (1,)
    
    def test_wait_time(self):
        """Test wait time calculation."""
        pq = PipelinedQuery(query="SELECT 1")
        # Should have some wait time
        assert pq.wait_time_ms >= 0


# =============================================================================
# PipelineStats Tests
# =============================================================================

class TestPipelineStats:
    """Tests for PipelineStats dataclass."""
    
    def test_initial_stats(self):
        """Test initial statistics."""
        stats = PipelineStats()
        assert stats.total_queries == 0
        assert stats.batches_executed == 0
    
    def test_avg_batch_size(self):
        """Test average batch size calculation."""
        stats = PipelineStats(total_queries=100, batches_executed=10)
        assert stats.avg_batch_size == 10.0
    
    def test_avg_wait_time(self):
        """Test average wait time calculation."""
        stats = PipelineStats(total_queries=10, total_wait_time_ms=100.0)
        assert stats.avg_wait_time_ms == 10.0
    
    def test_avg_batch_time(self):
        """Test average batch time calculation."""
        stats = PipelineStats(batches_executed=10, total_batch_time_ms=500.0)
        assert stats.avg_batch_time_ms == 50.0
    
    def test_to_dict(self):
        """Test dictionary conversion."""
        stats = PipelineStats(total_queries=10)
        d = stats.to_dict()
        assert "total_queries" in d
        assert "avg_batch_size" in d


# =============================================================================
# QueryPipeline Basic Tests
# =============================================================================

class TestQueryPipelineBasic:
    """Tests for basic QueryPipeline operations."""
    
    @pytest.fixture
    def batch_executor(self):
        async def executor(queries):
            return [f"result_{i}" for i in range(len(queries))]
        return executor
    
    @pytest.mark.asyncio
    async def test_add_single_query(self, batch_executor):
        """Test adding a single query."""
        pipeline = QueryPipeline(
            config=PipelineConfig(auto_flush=False),
            batch_executor=batch_executor,
        )
        
        # Add query and immediately flush
        task = asyncio.create_task(pipeline.add("SELECT 1"))
        await asyncio.sleep(0.01)
        await pipeline.flush()
        
        result = await task
        assert result == "result_0"
    
    @pytest.mark.asyncio
    async def test_buffer_size(self, batch_executor):
        """Test buffer size tracking."""
        pipeline = QueryPipeline(
            config=PipelineConfig(auto_flush=False, max_batch_size=100),
            batch_executor=batch_executor,
        )
        
        assert pipeline.buffer_size == 0
        
        # Add queries without flushing
        task1 = asyncio.create_task(pipeline.add("SELECT 1"))
        task2 = asyncio.create_task(pipeline.add("SELECT 2"))
        await asyncio.sleep(0.01)
        
        assert pipeline.buffer_size == 2
        
        await pipeline.flush()
        await task1
        await task2
    
    @pytest.mark.asyncio
    async def test_is_running(self, batch_executor):
        """Test is_running property."""
        pipeline = QueryPipeline(batch_executor=batch_executor)
        
        assert pipeline.is_running is False
        await pipeline.start()
        assert pipeline.is_running is True
        await pipeline.stop()
        assert pipeline.is_running is False
    
    @pytest.mark.asyncio
    async def test_disabled_pipeline(self, batch_executor):
        """Test disabled pipeline executes immediately."""
        pipeline = QueryPipeline(
            config=PipelineConfig(enabled=False),
            batch_executor=batch_executor,
        )
        
        result = await pipeline.add("SELECT 1")
        assert result == "result_0"


# =============================================================================
# Batch Execution Tests
# =============================================================================

class TestBatchExecution:
    """Tests for batch query execution."""
    
    @pytest.mark.asyncio
    async def test_batch_on_max_size(self):
        """Test batch executes when max_size reached."""
        execution_count = 0
        
        async def batch_executor(queries):
            nonlocal execution_count
            execution_count += 1
            return [f"result_{i}" for i in range(len(queries))]
        
        pipeline = QueryPipeline(
            config=PipelineConfig(max_batch_size=3, auto_flush=False),
            batch_executor=batch_executor,
        )
        
        # Add 3 queries (should trigger batch)
        tasks = [
            asyncio.create_task(pipeline.add("SELECT 1")),
            asyncio.create_task(pipeline.add("SELECT 2")),
            asyncio.create_task(pipeline.add("SELECT 3")),
        ]
        
        # Wait for all to complete
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 3
        assert execution_count == 1
    
    @pytest.mark.asyncio
    async def test_add_many_queries(self):
        """Test adding many queries at once."""
        async def batch_executor(queries):
            return [f"result_{i}" for i in range(len(queries))]
        
        pipeline = QueryPipeline(
            config=PipelineConfig(auto_flush=False),
            batch_executor=batch_executor,
        )
        
        # Add many at once
        task = asyncio.create_task(pipeline.add_many([
            ("SELECT 1", None),
            ("SELECT 2", None),
            ("SELECT 3", None),
        ]))
        await asyncio.sleep(0.01)
        await pipeline.flush()
        
        results = await task
        assert len(results) == 3
    
    @pytest.mark.asyncio
    async def test_batch_preserves_order(self):
        """Test batch results are in correct order."""
        async def batch_executor(queries):
            return [f"result_for_{q[0]}" for q in queries]
        
        pipeline = QueryPipeline(
            config=PipelineConfig(auto_flush=False),
            batch_executor=batch_executor,
        )
        
        task = asyncio.create_task(pipeline.add_many([
            ("query_A", None),
            ("query_B", None),
            ("query_C", None),
        ]))
        await asyncio.sleep(0.01)
        await pipeline.flush()
        
        results = await task
        assert results[0] == "result_for_query_A"
        assert results[1] == "result_for_query_B"
        assert results[2] == "result_for_query_C"


# =============================================================================
# Auto-Flush Tests
# =============================================================================

class TestAutoFlush:
    """Tests for auto-flush behavior."""
    
    @pytest.mark.asyncio
    async def test_auto_flush_on_timer(self):
        """Test auto-flush triggers on timer."""
        execution_count = 0
        
        async def batch_executor(queries):
            nonlocal execution_count
            execution_count += 1
            return [f"result_{i}" for i in range(len(queries))]
        
        pipeline = QueryPipeline(
            config=PipelineConfig(max_wait_ms=50, auto_flush=True),
            batch_executor=batch_executor,
        )
        
        await pipeline.start()
        
        # Add query
        task = asyncio.create_task(pipeline.add("SELECT 1"))
        
        # Wait for auto-flush
        await asyncio.sleep(0.1)
        result = await task
        
        assert result == "result_0"
        assert execution_count >= 1
        
        await pipeline.stop()
    
    @pytest.mark.asyncio
    async def test_start_stop(self):
        """Test start and stop."""
        async def batch_executor(queries):
            return ["result"] * len(queries)
        
        pipeline = QueryPipeline(batch_executor=batch_executor)
        
        await pipeline.start()
        assert pipeline.is_running
        
        await pipeline.stop()
        assert not pipeline.is_running
    
    @pytest.mark.asyncio
    async def test_stop_flushes_remaining(self):
        """Test stop flushes remaining queries."""
        async def batch_executor(queries):
            return [f"result_{i}" for i in range(len(queries))]
        
        pipeline = QueryPipeline(
            config=PipelineConfig(auto_flush=False),
            batch_executor=batch_executor,
        )
        
        # Add query
        task = asyncio.create_task(pipeline.add("SELECT 1"))
        await asyncio.sleep(0.01)
        
        # Stop should flush
        await pipeline.stop()
        
        result = await task
        assert result == "result_0"


# =============================================================================
# Manual Flush Tests
# =============================================================================

class TestManualFlush:
    """Tests for manual flush."""
    
    @pytest.mark.asyncio
    async def test_manual_flush(self):
        """Test manual flush executes pending."""
        async def batch_executor(queries):
            return [f"result_{i}" for i in range(len(queries))]
        
        pipeline = QueryPipeline(
            config=PipelineConfig(auto_flush=False),
            batch_executor=batch_executor,
        )
        
        task1 = asyncio.create_task(pipeline.add("SELECT 1"))
        task2 = asyncio.create_task(pipeline.add("SELECT 2"))
        await asyncio.sleep(0.01)
        
        count = await pipeline.flush()
        
        assert count == 2
        r1 = await task1
        r2 = await task2
        assert r1 == "result_0"
        assert r2 == "result_1"
    
    @pytest.mark.asyncio
    async def test_flush_empty_buffer(self):
        """Test flushing empty buffer."""
        async def batch_executor(queries):
            return []
        
        pipeline = QueryPipeline(batch_executor=batch_executor)
        
        count = await pipeline.flush()
        assert count == 0


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestPipelineErrors:
    """Tests for pipeline error handling."""
    
    @pytest.mark.asyncio
    async def test_batch_executor_error(self):
        """Test error in batch executor."""
        async def failing_executor(queries):
            raise ValueError("Batch failed")
        
        pipeline = QueryPipeline(
            config=PipelineConfig(auto_flush=False),
            batch_executor=failing_executor,
        )
        
        task = asyncio.create_task(pipeline.add("SELECT 1"))
        await asyncio.sleep(0.01)
        
        with pytest.raises(ValueError, match="Batch failed"):
            await pipeline.flush()
            await task
    
    @pytest.mark.asyncio
    async def test_error_propagates_to_all_queries(self):
        """Test error propagates to all waiting queries."""
        async def failing_executor(queries):
            raise RuntimeError("Database error")
        
        pipeline = QueryPipeline(
            config=PipelineConfig(auto_flush=False),
            batch_executor=failing_executor,
        )
        
        tasks = [
            asyncio.create_task(pipeline.add("SELECT 1")),
            asyncio.create_task(pipeline.add("SELECT 2")),
        ]
        await asyncio.sleep(0.01)
        
        with pytest.raises(RuntimeError):
            await pipeline.flush()
        
        # All tasks should raise
        for task in tasks:
            with pytest.raises(RuntimeError):
                await task
    
    @pytest.mark.asyncio
    async def test_error_stats_updated(self):
        """Test error statistics are updated."""
        async def failing_executor(queries):
            raise ValueError("Failed")
        
        pipeline = QueryPipeline(
            config=PipelineConfig(auto_flush=False),
            batch_executor=failing_executor,
        )
        
        task = asyncio.create_task(pipeline.add("SELECT 1"))
        await asyncio.sleep(0.01)
        
        try:
            await pipeline.flush()
        except ValueError:
            pass
        
        try:
            await task
        except ValueError:
            pass
        
        stats = pipeline.get_stats()
        assert stats.errors == 1


# =============================================================================
# Statistics Tests
# =============================================================================

class TestPipelineStatistics:
    """Tests for pipeline statistics."""
    
    @pytest.mark.asyncio
    async def test_stats_after_batches(self):
        """Test statistics after batch execution."""
        async def batch_executor(queries):
            await asyncio.sleep(0.01)
            return [f"result_{i}" for i in range(len(queries))]
        
        pipeline = QueryPipeline(
            config=PipelineConfig(max_batch_size=2, auto_flush=False),
            batch_executor=batch_executor,
        )
        
        # Add 4 queries (2 batches)
        tasks = [asyncio.create_task(pipeline.add(f"SELECT {i}")) for i in range(4)]
        await asyncio.sleep(0.01)
        await pipeline.flush()
        await asyncio.gather(*tasks)
        
        stats = pipeline.get_stats()
        assert stats.total_queries == 4
        assert stats.batches_executed >= 1
    
    @pytest.mark.asyncio
    async def test_stats_reset(self):
        """Test statistics reset."""
        async def batch_executor(queries):
            return ["result"] * len(queries)
        
        pipeline = QueryPipeline(
            config=PipelineConfig(auto_flush=False),
            batch_executor=batch_executor,
        )
        
        task = asyncio.create_task(pipeline.add("SELECT 1"))
        await asyncio.sleep(0.01)
        await pipeline.flush()
        await task
        
        pipeline.reset_stats()
        stats = pipeline.get_stats()
        
        assert stats.total_queries == 0
        assert stats.batches_executed == 0


# =============================================================================
# Convenience Config Tests
# =============================================================================

class TestConvenienceConfigs:
    """Tests for convenience configuration functions."""
    
    def test_high_throughput_config(self):
        """Test high throughput configuration."""
        config = high_throughput_config()
        assert config.max_batch_size == 500
        assert config.max_wait_ms == 10.0
    
    def test_low_latency_config(self):
        """Test low latency configuration."""
        config = low_latency_config()
        assert config.max_batch_size == 20
        assert config.max_wait_ms == 1.0
    
    def test_disabled_config(self):
        """Test disabled configuration."""
        config = disabled_pipeline_config()
        assert config.enabled is False


# =============================================================================
# Repr Tests
# =============================================================================

class TestPipelineRepr:
    """Tests for pipeline string representation."""
    
    def test_repr(self):
        """Test pipeline repr."""
        async def batch_executor(queries):
            return []
        
        pipeline = QueryPipeline(batch_executor=batch_executor)
        repr_str = repr(pipeline)
        assert "QueryPipeline" in repr_str


# =============================================================================
# Edge Cases Tests
# =============================================================================

class TestPipelineEdgeCases:
    """Tests for pipeline edge cases."""
    
    @pytest.mark.asyncio
    async def test_empty_query(self):
        """Test pipelining empty query."""
        async def batch_executor(queries):
            return ["empty"] * len(queries)
        
        pipeline = QueryPipeline(
            config=PipelineConfig(auto_flush=False),
            batch_executor=batch_executor,
        )
        
        task = asyncio.create_task(pipeline.add(""))
        await asyncio.sleep(0.01)
        await pipeline.flush()
        
        result = await task
        assert result == "empty"
    
    @pytest.mark.asyncio
    async def test_query_with_params(self):
        """Test query with parameters in pipeline."""
        async def batch_executor(queries):
            return [f"result_{q[1]}" for q in queries]
        
        pipeline = QueryPipeline(
            config=PipelineConfig(auto_flush=False),
            batch_executor=batch_executor,
        )
        
        task = asyncio.create_task(pipeline.add("SELECT $1", params=(42,)))
        await asyncio.sleep(0.01)
        await pipeline.flush()
        
        result = await task
        assert result == "result_(42,)"
    
    @pytest.mark.asyncio
    async def test_double_start(self):
        """Test starting already running pipeline."""
        async def batch_executor(queries):
            return []
        
        pipeline = QueryPipeline(batch_executor=batch_executor)
        
        await pipeline.start()
        await pipeline.start()  # Should be no-op
        
        assert pipeline.is_running
        await pipeline.stop()
    
    @pytest.mark.asyncio
    async def test_double_stop(self):
        """Test stopping already stopped pipeline."""
        async def batch_executor(queries):
            return []
        
        pipeline = QueryPipeline(batch_executor=batch_executor)
        
        await pipeline.stop()  # Already stopped
        await pipeline.stop()  # Should be no-op
        
        assert not pipeline.is_running


# =============================================================================
# Concurrent Access Tests
# =============================================================================

class TestPipelineConcurrency:
    """Tests for concurrent pipeline access."""
    
    @pytest.mark.asyncio
    async def test_many_concurrent_adds(self):
        """Test many concurrent adds."""
        async def batch_executor(queries):
            return [f"result_{i}" for i in range(len(queries))]
        
        pipeline = QueryPipeline(
            config=PipelineConfig(max_batch_size=1000, auto_flush=False),
            batch_executor=batch_executor,
        )
        
        # Add 100 queries concurrently
        tasks = [asyncio.create_task(pipeline.add(f"SELECT {i}")) for i in range(100)]
        await asyncio.sleep(0.01)
        await pipeline.flush()
        
        results = await asyncio.gather(*tasks)
        assert len(results) == 100

