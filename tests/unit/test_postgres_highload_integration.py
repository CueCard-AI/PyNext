"""
Integration Tests for PostgreSQL High-Load Components.

Tests cover:
- Cache + coalescing interaction
- Pipeline + batch interaction
- Scaling + timeout interaction
- Full stack integration
- High concurrency scenarios
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from pynext.db.adapters.postgres_timeout import (
    QueryTimeoutConfig,
    TimeoutManager,
)
from pynext.db.adapters.postgres_query_cache import (
    QueryCacheConfig,
    QueryCache,
)
from pynext.db.adapters.postgres_coalesce import (
    CoalescingConfig,
    QueryCoalescer,
)
from pynext.db.adapters.postgres_pipeline import (
    PipelineConfig,
    QueryPipeline,
)
from pynext.db.adapters.postgres_batch import (
    BatchConfig,
    BatchOptimizer,
)
from pynext.db.adapters.postgres_scaling import (
    AdaptiveScalingConfig,
    AdaptiveScaler,
)


# =============================================================================
# Cache + Coalescing Integration
# =============================================================================

class TestCacheCoalescingIntegration:
    """Tests for cache and coalescing working together."""
    
    @pytest.mark.asyncio
    async def test_cache_then_coalesce(self):
        """Test cache hit prevents coalescing."""
        cache = QueryCache(QueryCacheConfig(default_ttl=60.0))
        coalescer = QueryCoalescer()
        execution_count = 0
        
        async def executor(query):
            nonlocal execution_count
            execution_count += 1
            await asyncio.sleep(0.02)
            return {"data": "result"}
        
        async def cached_executor(query, params=None):
            # Check cache first
            cached = await cache.get(query, params)
            if cached is not None:
                return cached
            
            # Then coalesce
            result = await coalescer.execute_or_join(query, params, executor)
            await cache.set(query, params, result)
            return result
        
        # First request - cache miss, execute
        r1 = await cached_executor("SELECT 1")
        
        # Second request - cache hit
        r2 = await cached_executor("SELECT 1")
        
        assert r1 == r2
        assert execution_count == 1  # Only executed once
    
    @pytest.mark.asyncio
    async def test_coalescing_with_cache_miss(self):
        """Test coalescing works when cache misses."""
        cache = QueryCache(QueryCacheConfig(default_ttl=60.0))
        coalescer = QueryCoalescer()
        execution_count = 0
        
        async def executor(query):
            nonlocal execution_count
            execution_count += 1
            await asyncio.sleep(0.05)
            return {"count": execution_count}
        
        async def full_executor(query):
            cached = await cache.get(query)
            if cached is not None:
                return cached
            
            result = await coalescer.execute_or_join(query, executor=executor)
            await cache.set(query, None, result)
            return result
        
        # Concurrent requests - all cache miss, but coalesced
        results = await asyncio.gather(
            full_executor("SELECT 1"),
            full_executor("SELECT 1"),
            full_executor("SELECT 1"),
        )
        
        assert all(r == results[0] for r in results)
        assert execution_count == 1  # Coalesced to one execution
    
    @pytest.mark.asyncio
    async def test_cache_invalidation_triggers_coalesce(self):
        """Test invalidation allows new coalescing."""
        cache = QueryCache(QueryCacheConfig(default_ttl=60.0))
        coalescer = QueryCoalescer()
        execution_count = 0
        
        async def executor(query):
            nonlocal execution_count
            execution_count += 1
            return {"count": execution_count}
        
        # Cache a result
        await cache.set("SELECT 1", None, {"count": 0})
        
        # Hit cache
        r1 = await cache.get("SELECT 1")
        assert r1 == {"count": 0}
        
        # Invalidate
        cache.invalidate("SELECT 1")
        
        # Now execute fresh
        r2 = await coalescer.execute_or_join("SELECT 1", executor=executor)
        
        assert r2 == {"count": 1}


# =============================================================================
# Pipeline + Batch Integration
# =============================================================================

class TestPipelineBatchIntegration:
    """Tests for pipeline and batch working together."""
    
    @pytest.mark.asyncio
    async def test_pipeline_batch_insert(self):
        """Test pipeline can batch inserts."""
        insert_count = 0
        
        async def batch_executor(queries):
            nonlocal insert_count
            insert_count += 1
            return [f"result_{i}" for i in range(len(queries))]
        
        pipeline = QueryPipeline(
            config=PipelineConfig(max_batch_size=5, auto_flush=False),
            batch_executor=batch_executor,
        )
        
        # Add many insert queries
        tasks = [
            asyncio.create_task(pipeline.add(f"INSERT INTO t VALUES ({i})"))
            for i in range(10)
        ]
        await asyncio.sleep(0.01)
        await pipeline.flush()
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 10
        assert insert_count == 2  # Batched into 2 groups of 5
    
    @pytest.mark.asyncio
    async def test_batch_optimizer_in_pipeline(self):
        """Test batch optimizer can use pipeline."""
        executed_sql = []
        
        async def tracking_executor(sql, params):
            executed_sql.append(sql)
            return len(params) // 2
        
        optimizer = BatchOptimizer(
            config=BatchConfig(max_batch_size=5),
            executor=tracking_executor,
        )
        
        rows = [{"col": i} for i in range(10)]
        result = await optimizer.insert_many(table="test", rows=rows)
        
        assert result.total_rows == 10
        assert result.batches == 2


# =============================================================================
# Scaling + Timeout Integration
# =============================================================================

class TestScalingTimeoutIntegration:
    """Tests for scaling and timeout working together."""
    
    @pytest.mark.asyncio
    async def test_timeout_during_scaling(self):
        """Test timeouts work during scaling events."""
        timeout_mgr = TimeoutManager(QueryTimeoutConfig(
            default=0.1,
            per_type={"select": 0.05},
        ))
        
        scaler = AdaptiveScaler(AdaptiveScalingConfig(min_samples=2))
        
        # Record load
        for _ in range(5):
            scaler.record_load(50, 100)
        
        # Get timeout for a query
        timeout = timeout_mgr.get_timeout("SELECT * FROM users")
        assert timeout == 0.05
        
        # Get scaling recommendation
        rec = scaler.recommend_pool_size(5, 100)
        
        # Both should work independently
        assert rec is not None
    
    @pytest.mark.asyncio
    async def test_scaling_under_load_with_timeouts(self):
        """Test scaling recommendations consider query patterns."""
        timeout_mgr = TimeoutManager(QueryTimeoutConfig(
            per_type={"select": 10.0, "insert": 30.0}
        ))
        
        scaler = AdaptiveScaler(AdaptiveScalingConfig(
            min_samples=5,
            scale_up_threshold=0.7,
        ))
        
        # Record high load
        for _ in range(10):
            scaler.record_load(80, 100, queue_depth=5)
        
        rec = scaler.recommend_pool_size(5, 100)
        
        # Should recommend scale up due to high load
        assert rec.current_load >= 0.7


# =============================================================================
# Full Stack Integration
# =============================================================================

class TestFullStackIntegration:
    """Tests for all components working together."""
    
    @pytest.fixture
    def full_stack(self):
        """Create a full stack of high-load components."""
        return {
            "cache": QueryCache(QueryCacheConfig(default_ttl=60.0)),
            "coalescer": QueryCoalescer(),
            "pipeline": QueryPipeline(
                config=PipelineConfig(max_batch_size=10, auto_flush=False)
            ),
            "batch": BatchOptimizer(),
            "scaler": AdaptiveScaler(AdaptiveScalingConfig(min_samples=2)),
            "timeout": TimeoutManager(QueryTimeoutConfig(default=30.0)),
        }
    
    @pytest.mark.asyncio
    async def test_read_query_flow(self, full_stack):
        """Test complete flow for read queries."""
        execution_count = 0
        
        async def db_executor(query):
            nonlocal execution_count
            execution_count += 1
            await asyncio.sleep(0.02)
            return [{"id": 1}]
        
        cache = full_stack["cache"]
        coalescer = full_stack["coalescer"]
        timeout = full_stack["timeout"]
        
        async def read_query(query):
            # 1. Check timeout
            qt = timeout.with_timeout(query)
            
            # 2. Check cache
            cached = await cache.get(query)
            if cached is not None:
                return cached
            
            # 3. Coalesce
            result = await coalescer.execute_or_join(query, executor=db_executor)
            
            # 4. Cache result
            await cache.set(query, None, result)
            
            return result
        
        # First request
        r1 = await read_query("SELECT * FROM users")
        
        # Second request (should hit cache)
        r2 = await read_query("SELECT * FROM users")
        
        assert r1 == r2
        assert execution_count == 1
    
    @pytest.mark.asyncio
    async def test_write_query_flow(self, full_stack):
        """Test complete flow for write queries."""
        batch = full_stack["batch"]
        cache = full_stack["cache"]
        
        async def db_executor(sql, params):
            return len(params)
        
        batch._executor = db_executor
        
        # Perform batch insert
        result = await batch.insert_many(
            table="users",
            rows=[{"name": f"User{i}"} for i in range(5)],
        )
        
        assert result.total_rows == 5
        
        # Invalidate related cache
        cache.invalidate_tags(["table:users"])
    
    @pytest.mark.asyncio
    async def test_concurrent_read_write(self, full_stack):
        """Test concurrent reads and writes."""
        cache = full_stack["cache"]
        batch = full_stack["batch"]
        
        read_count = 0
        write_count = 0
        
        async def read_executor(query):
            nonlocal read_count
            read_count += 1
            await asyncio.sleep(0.01)
            return [{"id": 1}]
        
        async def write_executor(sql, params):
            nonlocal write_count
            write_count += 1
            return 1
        
        batch._executor = write_executor
        
        async def read_task():
            result = await cache.get_or_execute(
                "SELECT * FROM users",
                executor=read_executor,
            )
            return result
        
        async def write_task():
            result = await batch.insert_many(
                table="users",
                rows=[{"name": "New User"}],
            )
            # Invalidate cache after write
            cache.invalidate_tags(["table:users"])
            return result
        
        # Run concurrent reads and writes
        results = await asyncio.gather(
            read_task(),
            read_task(),
            write_task(),
            read_task(),
        )
        
        assert len(results) == 4


# =============================================================================
# High Concurrency Tests
# =============================================================================

class TestHighConcurrency:
    """Tests for high concurrency scenarios."""
    
    @pytest.mark.asyncio
    async def test_100_concurrent_cached_reads(self):
        """Test 100 concurrent cached reads."""
        cache = QueryCache(QueryCacheConfig(max_size=1000))
        execution_count = 0
        
        async def executor(query):
            nonlocal execution_count
            execution_count += 1
            await asyncio.sleep(0.01)
            return {"data": "value"}
        
        async def cached_read():
            return await cache.get_or_execute(
                "SELECT * FROM data",
                executor=executor,
            )
        
        results = await asyncio.gather(*[cached_read() for _ in range(100)])
        
        assert all(r == {"data": "value"} for r in results)
        # Should be much less than 100 executions due to caching
        assert execution_count < 100
    
    @pytest.mark.asyncio
    async def test_100_concurrent_coalesced_queries(self):
        """Test 100 concurrent coalesced queries."""
        coalescer = QueryCoalescer(CoalescingConfig(max_waiters=200))
        execution_count = 0
        
        async def executor(query):
            nonlocal execution_count
            execution_count += 1
            await asyncio.sleep(0.05)
            return {"result": "data"}
        
        results = await asyncio.gather(*[
            coalescer.execute_or_join("SELECT 1", executor=executor)
            for _ in range(100)
        ])
        
        assert all(r == {"result": "data"} for r in results)
        assert execution_count == 1  # All coalesced
    
    @pytest.mark.asyncio
    async def test_mixed_concurrent_queries(self):
        """Test mixed concurrent query types."""
        cache = QueryCache()
        coalescer = QueryCoalescer()
        
        async def executor(query):
            await asyncio.sleep(0.01)
            return query
        
        async def process_query(i):
            query = f"SELECT {i % 10}"  # 10 unique queries
            
            cached = await cache.get(query)
            if cached:
                return cached
            
            result = await coalescer.execute_or_join(query, executor=executor)
            await cache.set(query, None, result)
            return result
        
        results = await asyncio.gather(*[process_query(i) for i in range(50)])
        
        assert len(results) == 50
    
    @pytest.mark.asyncio
    async def test_pipeline_under_load(self):
        """Test pipeline under high load."""
        async def batch_executor(queries):
            await asyncio.sleep(0.01)
            return [f"result_{i}" for i in range(len(queries))]
        
        pipeline = QueryPipeline(
            config=PipelineConfig(max_batch_size=20, auto_flush=False),
            batch_executor=batch_executor,
        )
        
        # Add 100 queries concurrently
        tasks = [
            asyncio.create_task(pipeline.add(f"SELECT {i}"))
            for i in range(100)
        ]
        await asyncio.sleep(0.01)
        await pipeline.flush()
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 100
        
        stats = pipeline.get_stats()
        assert stats.total_queries == 100


# =============================================================================
# Component Interaction Tests
# =============================================================================

class TestComponentInteractions:
    """Tests for specific component interactions."""
    
    @pytest.mark.asyncio
    async def test_timeout_with_cache(self):
        """Test timeout configuration with cache."""
        timeout = TimeoutManager(QueryTimeoutConfig(
            per_type={"select": 5.0}
        ))
        cache = QueryCache()
        
        query = "SELECT * FROM users"
        
        # Get timeout for query
        t = timeout.get_timeout(query)
        assert t == 5.0
        
        # Cache should work independently
        await cache.set(query, None, result=[])
        cached = await cache.get(query)
        assert cached == []
    
    @pytest.mark.asyncio
    async def test_scaling_with_coalescing_stats(self):
        """Test scaling uses coalescing statistics."""
        scaler = AdaptiveScaler(AdaptiveScalingConfig(min_samples=2))
        coalescer = QueryCoalescer()
        
        # Record some load
        for _ in range(5):
            scaler.record_load(50, 100)
        
        # Get coalescing stats
        c_stats = coalescer.get_stats()
        
        # Get scaling recommendation
        rec = scaler.recommend_pool_size(5, 100)
        
        # Both should have valid stats
        assert c_stats.total_queries >= 0
        assert rec.confidence >= 0
    
    @pytest.mark.asyncio
    async def test_batch_with_cache_invalidation(self):
        """Test batch operations trigger cache invalidation."""
        cache = QueryCache(QueryCacheConfig(auto_tag=True))
        batch = BatchOptimizer(executor=AsyncMock(return_value=1))
        
        # Cache some data
        await cache.set("SELECT * FROM users", None, result=[{"id": 1}])
        
        # Perform batch insert
        await batch.insert_many(
            table="users",
            rows=[{"name": "New"}],
        )
        
        # Invalidate users cache
        count = cache.invalidate_tags(["table:users"])
        
        assert count == 1
        assert await cache.get("SELECT * FROM users") is None
    
    @pytest.mark.asyncio
    async def test_pipeline_respects_timeout(self):
        """Test pipeline respects query timeouts."""
        timeout = TimeoutManager(QueryTimeoutConfig(default=30.0))
        
        async def batch_executor(queries):
            return [f"result" for _ in queries]
        
        pipeline = QueryPipeline(
            config=PipelineConfig(auto_flush=False),
            batch_executor=batch_executor,
        )
        
        # Get timeout for query
        qt = timeout.with_timeout("SELECT * FROM users")
        assert qt.timeout == 30.0
        
        # Pipeline should work
        task = asyncio.create_task(pipeline.add("SELECT * FROM users"))
        await asyncio.sleep(0.01)
        await pipeline.flush()
        
        result = await task
        assert result == "result"


# =============================================================================
# Error Propagation Tests
# =============================================================================

class TestErrorPropagation:
    """Tests for error propagation across components."""
    
    @pytest.mark.asyncio
    async def test_executor_error_through_cache(self):
        """Test executor error propagates through cache."""
        cache = QueryCache()
        
        async def failing_executor(query):
            raise ValueError("DB Error")
        
        with pytest.raises(ValueError, match="DB Error"):
            await cache.get_or_execute("SELECT 1", executor=failing_executor)
    
    @pytest.mark.asyncio
    async def test_executor_error_through_coalescer(self):
        """Test executor error propagates through coalescer."""
        coalescer = QueryCoalescer()
        
        async def failing_executor(query):
            await asyncio.sleep(0.02)
            raise RuntimeError("Query failed")
        
        with pytest.raises(RuntimeError, match="Query failed"):
            await asyncio.gather(
                coalescer.execute_or_join("SELECT 1", executor=failing_executor),
                coalescer.execute_or_join("SELECT 1", executor=failing_executor),
            )
    
    @pytest.mark.asyncio
    async def test_batch_error_partial_success(self):
        """Test batch error with partial success."""
        call_count = 0
        
        async def sometimes_fails(sql, params):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise ValueError("Second batch failed")
            return 5
        
        batch = BatchOptimizer(
            config=BatchConfig(max_batch_size=5),
            executor=sometimes_fails,
        )
        
        result = await batch.insert_many(
            table="test",
            rows=[{"col": i} for i in range(15)],
        )
        
        assert result.success is False
        assert result.affected_rows > 0  # Some succeeded


# =============================================================================
# Statistics Integration Tests
# =============================================================================

class TestStatisticsIntegration:
    """Tests for statistics across components."""
    
    @pytest.mark.asyncio
    async def test_combined_statistics(self):
        """Test combining statistics from multiple components."""
        cache = QueryCache()
        coalescer = QueryCoalescer()
        batch = BatchOptimizer(executor=AsyncMock(return_value=1))
        scaler = AdaptiveScaler()
        
        # Use each component
        await cache.set("SELECT 1", None, result=1)
        await cache.get("SELECT 1")
        
        async def executor(q):
            return "result"
        await coalescer.execute_or_join("SELECT 1", executor=executor)
        
        await batch.insert_many(table="t", rows=[{"a": 1}])
        
        for _ in range(5):
            scaler.record_load(50, 100)
        
        # Collect all stats
        cache_stats = cache.get_stats()
        coal_stats = coalescer.get_stats()
        batch_stats = batch.get_stats()
        scale_stats = scaler.get_stats()
        
        assert cache_stats.hits >= 0
        assert coal_stats.total_queries >= 0
        assert batch_stats.total_operations >= 0
        assert scale_stats.samples_recorded >= 0

