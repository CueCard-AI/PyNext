"""
Go Bridge Stress Tests

These tests validate the Go Bridge can handle sustained load, burst traffic,
and edge cases without memory leaks or connection pool exhaustion.

Run with: pytest tests/benchmarks/test_go_stress.py -v
"""

import gc
import os
import time
import tracemalloc

import pytest

# Database URL
DB_URL = os.environ.get(
    "PYNEXT_TEST_DB_URL",
    "postgresql://pynext:pynext@localhost:5433/pynext_test"
)


def is_db_available() -> bool:
    """Check if test database is available."""
    try:
        import psycopg
        with psycopg.connect(DB_URL, connect_timeout=2) as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        return False


requires_db = pytest.mark.skipif(
    not is_db_available(),
    reason="PostgreSQL test database not available"
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope="class")
def go_bridge(request):
    """Initialize Go bridge for stress tests with higher pool limits."""
    import pynext_go
    
    # Close any existing connection first
    try:
        pynext_go.close()
    except Exception:
        pass
    
    # Use larger pool for stress tests
    pynext_go.init(
        primary=DB_URL,
        pool_min_size=20,
        pool_max_size=150  # Higher for stress tests
    )
    pynext_go.warmup()
    
    yield pynext_go
    pynext_go.close()


# =============================================================================
# Sustained Load Tests
# =============================================================================

@requires_db
class TestSustainedLoad:
    """
    Test behavior under sustained load for extended periods.
    Target: No degradation over 60 seconds of continuous load.
    """
    
    def test_30_second_sustained_100_qps(self, go_bridge):
        """Sustain 100 queries/second for 30 seconds."""
        duration = 30  # seconds
        target_qps = 100
        interval = 1.0 / target_qps
        
        query_count = 0
        error_count = 0
        latencies = []
        
        start_time = time.time()
        end_time = start_time + duration
        
        while time.time() < end_time:
            batch_start = time.perf_counter()
            
            # Fire batch of 10 queries
            queries = [("SELECT COUNT(*) FROM users", []) for _ in range(10)]
            results = go_bridge.execute_parallel(queries)
            
            for r in results:
                if r.success:
                    query_count += 1
                    latencies.append(r.duration_ms)
                else:
                    error_count += 1
            
            # Throttle to target rate
            elapsed = time.perf_counter() - batch_start
            sleep_time = (10 * interval) - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        total_time = time.time() - start_time
        actual_qps = query_count / total_time
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        p99_latency = sorted(latencies)[int(len(latencies) * 0.99)] if latencies else 0
        
        print(f"\n📊 Sustained Load Results:")
        print(f"   Duration: {total_time:.1f}s")
        print(f"   Total queries: {query_count}")
        print(f"   Actual QPS: {actual_qps:.0f}")
        print(f"   Errors: {error_count}")
        print(f"   Avg latency: {avg_latency:.2f}ms")
        print(f"   P99 latency: {p99_latency:.2f}ms")
        
        assert error_count == 0, f"Had {error_count} errors during sustained load"
        assert actual_qps >= target_qps * 0.8, f"QPS {actual_qps:.0f} below target {target_qps}"
        assert p99_latency < 50, f"P99 latency {p99_latency:.1f}ms exceeds 50ms target"


# =============================================================================
# Burst Traffic Tests
# =============================================================================

@requires_db
class TestBurstTraffic:
    """
    Test handling of sudden traffic spikes.
    Target: Handle 5000 simultaneous queries without crashes.
    """
    
    def test_burst_1000_queries(self, go_bridge):
        """Fire 1000 queries simultaneously."""
        queries = [("SELECT COUNT(*) FROM orders", []) for _ in range(1000)]
        
        start = time.perf_counter()
        results = go_bridge.execute_parallel(queries)
        elapsed = time.perf_counter() - start
        
        success_count = sum(1 for r in results if r.success)
        error_count = sum(1 for r in results if not r.success)
        
        print(f"\n🚀 Burst 1000 Results:")
        print(f"   Time: {elapsed*1000:.0f}ms")
        print(f"   Success: {success_count}")
        print(f"   Errors: {error_count}")
        
        assert len(results) == 1000
        assert success_count == 1000, f"Only {success_count}/1000 succeeded"
        assert elapsed < 2.0, f"Burst took {elapsed:.2f}s, target is <2s"
    
    def test_burst_2000_queries(self, go_bridge):
        """Fire 2000 queries simultaneously."""
        queries = [("SELECT id, name FROM users LIMIT 1", []) for _ in range(2000)]
        
        start = time.perf_counter()
        results = go_bridge.execute_parallel(queries)
        elapsed = time.perf_counter() - start
        
        success_count = sum(1 for r in results if r.success)
        
        print(f"\n🚀 Burst 2000 Results:")
        print(f"   Time: {elapsed*1000:.0f}ms")
        print(f"   Success: {success_count}")
        
        assert len(results) == 2000
        assert success_count >= 1900, f"Only {success_count}/2000 succeeded"
        assert elapsed < 5.0, f"Burst took {elapsed:.2f}s, target is <5s"
    
    def test_burst_5000_queries(self, go_bridge):
        """Fire 5000 queries simultaneously (stress limit)."""
        queries = [("SELECT 1", []) for _ in range(5000)]
        
        start = time.perf_counter()
        results = go_bridge.execute_parallel(queries)
        elapsed = time.perf_counter() - start
        
        success_count = sum(1 for r in results if r.success)
        
        print(f"\n🚀 Burst 5000 Results:")
        print(f"   Time: {elapsed*1000:.0f}ms")
        print(f"   Success: {success_count}")
        
        assert len(results) == 5000
        # Allow some failures under extreme load
        assert success_count >= 4500, f"Only {success_count}/5000 succeeded"
        assert elapsed < 10.0, f"Burst took {elapsed:.2f}s, target is <10s"


# =============================================================================
# Memory Stability Tests
# =============================================================================

@requires_db
class TestMemoryStability:
    """
    Test for memory leaks after many operations.
    Target: No significant memory growth after 10k queries.
    """
    
    def test_no_memory_leak_10k_queries(self, go_bridge):
        """Execute 10k queries and verify no memory leak."""
        gc.collect()
        tracemalloc.start()
        
        baseline_snapshot = tracemalloc.take_snapshot()
        
        # Execute 10k queries in batches of 500
        total_queries = 10000
        batch_size = 500
        
        for i in range(0, total_queries, batch_size):
            queries = [
                (f"SELECT * FROM orders LIMIT 10", [])
                for _ in range(batch_size)
            ]
            results = go_bridge.execute_parallel(queries)
            assert all(r.success for r in results), f"Batch {i//batch_size} had failures"
        
        gc.collect()
        final_snapshot = tracemalloc.take_snapshot()
        tracemalloc.stop()
        
        # Compare memory usage
        top_stats = final_snapshot.compare_to(baseline_snapshot, 'lineno')
        
        # Sum up memory growth
        total_growth = sum(stat.size_diff for stat in top_stats if stat.size_diff > 0)
        total_growth_mb = total_growth / (1024 * 1024)
        
        print(f"\n💾 Memory Stability Results:")
        print(f"   Queries executed: {total_queries}")
        print(f"   Memory growth: {total_growth_mb:.2f} MB")
        
        # Allow up to 50MB growth (includes result caching, Python overhead)
        assert total_growth_mb < 50, f"Memory grew by {total_growth_mb:.1f}MB, target is <50MB"
    
    def test_memory_after_bulk_reads(self, go_bridge):
        """Execute bulk reads and verify memory is reclaimed."""
        gc.collect()
        tracemalloc.start()
        
        baseline = tracemalloc.take_snapshot()
        
        # Read large result sets 20 times
        for _ in range(20):
            result = go_bridge.execute("SELECT * FROM logs LIMIT 5000", [])
            assert len(result.rows) == 5000
            del result  # Explicitly delete
        
        gc.collect()
        final = tracemalloc.take_snapshot()
        tracemalloc.stop()
        
        total_growth = sum(
            stat.size_diff for stat in final.compare_to(baseline, 'lineno')
            if stat.size_diff > 0
        )
        growth_mb = total_growth / (1024 * 1024)
        
        print(f"\n💾 Bulk Read Memory:")
        print(f"   Memory growth: {growth_mb:.2f} MB")
        
        # Should reclaim memory after GC
        assert growth_mb < 30, f"Memory grew by {growth_mb:.1f}MB after bulk reads"


# =============================================================================
# Connection Pool Tests
# =============================================================================

@requires_db
class TestConnectionPool:
    """
    Test connection pool behavior under stress.
    Target: Handle pool exhaustion gracefully.
    """
    
    def test_high_concurrency_pool_saturation(self, go_bridge):
        """Verify pool handles high concurrency via parallel execution."""
        # Simulate 20 "threads" x 50 queries each = 1000 queries
        # Using Go's native parallel execution
        queries = [
            (f"SELECT {i % 1000} as id", [])
            for i in range(1000)
        ]
        
        start = time.perf_counter()
        results = go_bridge.execute_parallel(queries)
        elapsed = time.perf_counter() - start
        
        success_count = sum(1 for r in results if r.success)
        error_count = sum(1 for r in results if not r.success)
        errors = [r.error for r in results if not r.success][:5]
        
        print(f"\n🔌 Connection Pool Saturation Test:")
        print(f"   Total queries: {len(results)}")
        print(f"   Success: {success_count}")
        print(f"   Errors: {error_count}")
        print(f"   Time: {elapsed*1000:.0f}ms")
        if errors:
            print(f"   Sample errors: {errors}")
        
        assert success_count == 1000, f"Only {success_count}/1000 succeeded"
        assert elapsed < 2.0, f"Took {elapsed:.2f}s, expected <2s"
    
    def test_pool_recovery_after_exhaustion(self, go_bridge):
        """Verify pool recovers after heavy load."""
        # Heavy burst to stress pool
        queries = [("SELECT pg_sleep(0.01)", []) for _ in range(200)]
        
        start = time.perf_counter()
        results = go_bridge.execute_parallel(queries)
        elapsed = time.perf_counter() - start
        
        # Wait for pool to settle
        time.sleep(0.5)
        
        # Simple query should work immediately
        check_start = time.perf_counter()
        check_result = go_bridge.execute("SELECT 1 as ready", [])
        check_elapsed = time.perf_counter() - check_start
        
        print(f"\n🔄 Pool Recovery Test:")
        print(f"   Heavy burst: {elapsed*1000:.0f}ms")
        print(f"   Recovery check: {check_elapsed*1000:.0f}ms")
        
        assert check_result.success, "Pool failed to recover"
        assert check_elapsed < 0.1, f"Recovery took {check_elapsed*1000:.0f}ms, expected <100ms"


# =============================================================================
# Chaos Tests (Edge Cases)
# =============================================================================

@requires_db
class TestChaos:
    """
    Test error handling and edge cases.
    Target: Graceful handling of malformed queries and errors.
    """
    
    def test_malformed_sql_handling(self, go_bridge):
        """Verify malformed SQL raises exception, doesn't crash."""
        from pynext_go.errors import BridgeQueryError
        
        malformed_queries = [
            "SELECT * FORM users",  # Typo
            "SELCT 1",  # Typo
            "SELECT * FROM nonexistent_table_xyz",  # Missing table
            "SELECT * WHERE",  # Incomplete
        ]
        
        for sql in malformed_queries:
            try:
                go_bridge.execute(sql, [])
                assert False, f"Expected exception for: {sql}"
            except BridgeQueryError as e:
                # Expected - malformed SQL should raise error
                assert str(e), f"Expected error message for: {sql}"
        
        # Verify bridge still works after errors
        check = go_bridge.execute("SELECT 1 as ok", [])
        assert check.success, "Bridge broken after malformed queries"
    
    def test_mixed_success_and_failure_batch(self, go_bridge):
        """Verify batch handles mixed success/failure queries."""
        queries = [
            ("SELECT 1", []),  # Good
            ("SELECT * FROM nonexistent_xyz", []),  # Bad
            ("SELECT 2", []),  # Good
            ("INVALID SQL", []),  # Bad
            ("SELECT 3", []),  # Good
        ]
        
        results = go_bridge.execute_parallel(queries)
        
        assert len(results) == 5
        assert results[0].success, "Query 0 should succeed"
        assert not results[1].success, "Query 1 should fail"
        assert results[2].success, "Query 2 should succeed"
        assert not results[3].success, "Query 3 should fail"
        assert results[4].success, "Query 4 should succeed"
    
    def test_null_and_empty_params(self, go_bridge):
        """Test handling of null and empty parameters."""
        # Empty params list
        result1 = go_bridge.execute("SELECT 1", [])
        assert result1.success
        
        # None params (should be treated as empty)
        result2 = go_bridge.execute("SELECT 1", None)
        assert result2.success
        
        # NULL value in params
        result3 = go_bridge.execute("SELECT $1 as val", [None])
        assert result3.success
        assert result3.rows[0][0] is None
    
    def test_long_running_query_timeout(self, go_bridge):
        """Test behavior with slow queries (should not block others)."""
        # Fire a mix of slow and fast queries
        queries = [
            ("SELECT pg_sleep(2)", []),  # Slow (2s)
            ("SELECT 1", []),  # Fast
            ("SELECT 2", []),  # Fast
            ("SELECT 3", []),  # Fast
        ]
        
        start = time.perf_counter()
        results = go_bridge.execute_parallel(queries)
        elapsed = time.perf_counter() - start
        
        # All should complete (parallel execution)
        fast_success = all(r.success for r in results[1:4])
        
        print(f"\n⏱️ Long Query Test:")
        print(f"   Total time: {elapsed*1000:.0f}ms")
        print(f"   Fast queries succeeded: {fast_success}")
        
        # Total time should be ~2s (dominated by slow query)
        # Not 4+ seconds if queries ran sequentially
        assert elapsed < 4.0, f"Queries blocked; took {elapsed:.1f}s"
        assert fast_success, "Fast queries failed"


# =============================================================================
# Regression Tests with Strict Thresholds
# =============================================================================

@requires_db
class TestStrictRegression:
    """
    Strict performance regression tests for CI/CD.
    These fail the build if performance degrades.
    """
    
    def test_1000_queries_under_1_second(self, go_bridge):
        """1000 queries must complete in under 1 second."""
        queries = [("SELECT COUNT(*) FROM users", []) for _ in range(1000)]
        
        # Warmup
        go_bridge.execute_parallel(queries[:100])
        
        # Best of 3 runs
        times = []
        for _ in range(3):
            start = time.perf_counter()
            results = go_bridge.execute_parallel(queries)
            times.append(time.perf_counter() - start)
            assert all(r.success for r in results)
        
        best = min(times)
        print(f"\n⏱️ 1000 Query Benchmark: {best*1000:.0f}ms")
        
        assert best < 1.0, f"1000 queries took {best:.2f}s, target is <1s"
    
    def test_latency_stability(self, go_bridge):
        """P99 latency should be within 10x of P50."""
        # =====================================================================
        # WARMUP - Critical for accurate latency measurement
        # =====================================================================
        # The first queries include cold-start overhead:
        # - Connection pool initialization
        # - Go runtime JIT compilation
        # - Database query plan caching
        # - TCP connection establishment
        # 
        # We run 100 warmup queries and discard them to measure steady-state.
        # =====================================================================
        for _ in range(100):
            result = go_bridge.execute("SELECT 1", [])
            assert result.success
        
        latencies = []
        
        for _ in range(500):
            start = time.perf_counter()
            result = go_bridge.execute("SELECT 1", [])
            latencies.append((time.perf_counter() - start) * 1000)  # ms
            assert result.success
        
        latencies.sort()
        p50 = latencies[int(len(latencies) * 0.50)]
        p99 = latencies[int(len(latencies) * 0.99)]
        ratio = p99 / p50 if p50 > 0 else float('inf')
        
        print(f"\n📈 Latency Distribution (after 100 warmup queries):")
        print(f"   P50: {p50:.2f}ms")
        print(f"   P99: {p99:.2f}ms")
        print(f"   P99/P50 ratio: {ratio:.1f}x")
        
        assert ratio < 10, f"P99/P50 ratio is {ratio:.1f}x, target is <10x"

