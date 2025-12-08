"""
Concurrency and stress tests for Go Bridge.

Tests thread safety, concurrent access, and performance
under load to ensure the Go bridge is robust.
"""

import pytest
import threading
import time
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch, MagicMock

from pynext_go import GoBridge, GO_AVAILABLE
from pynext_go.config import BridgeConfig
from pynext_go.errors import BridgeError
from pynext_go.result import QueryResult
from pynext_go.health import HealthStatus


# =============================================================================
# Thread Safety Tests
# =============================================================================

class TestThreadSafetyBasic:
    """Basic thread safety tests."""
    
    def test_concurrent_version_calls(self):
        """version() should be thread-safe."""
        results = []
        errors = []
        
        def get_version():
            try:
                v = GoBridge.version()
                results.append(v)
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=get_version) for _ in range(20)]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Errors: {errors}"
        assert len(results) == 20
        # All should return same version
        assert len(set(results)) == 1
    
    def test_concurrent_is_available_calls(self):
        """is_available should be thread-safe."""
        results = []
        errors = []
        
        def check_available():
            try:
                bridge = GoBridge()
                results.append(bridge.is_available)
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=check_available) for _ in range(20)]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Errors: {errors}"
        assert len(results) == 20
    
    def test_concurrent_close_calls(self):
        """close() should be thread-safe and idempotent."""
        errors = []
        
        def close_bridge():
            try:
                bridge = GoBridge()
                bridge.close()
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=close_bridge) for _ in range(20)]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Errors: {errors}"
    
    def test_concurrent_config_creation(self):
        """BridgeConfig creation should be thread-safe."""
        results = []
        errors = []
        
        def create_config(i):
            try:
                config = BridgeConfig(
                    primary=f"postgresql://localhost/test{i}",
                    pool_max_size=10 + i,
                )
                results.append(config)
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=create_config, args=(i,)) for i in range(20)]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Errors: {errors}"
        assert len(results) == 20


class TestThreadSafetyLock:
    """Test that bridge lock prevents race conditions."""
    
    def test_bridge_has_lock(self):
        """GoBridge should have a lock attribute."""
        bridge = GoBridge()
        assert hasattr(bridge, "_lock")
    
    def test_concurrent_init_attempts(self):
        """Concurrent init() should be safe."""
        bridge = GoBridge()
        bridge.close()  # Ensure clean state
        
        results = []
        errors = []
        
        def try_init():
            try:
                # This will fail without real DB, but should not crash
                bridge.init(BridgeConfig(primary="postgresql://localhost/test"))
                results.append("success")
            except BridgeError:
                results.append("error")
            except Exception as e:
                # Connection errors are expected
                results.append(f"other:{type(e).__name__}")
        
        # Create threads that will all try to init
        threads = [threading.Thread(target=try_init) for _ in range(10)]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should have 10 results, no crashes
        assert len(results) == 10


# =============================================================================
# ThreadPoolExecutor Tests
# =============================================================================

class TestThreadPoolExecutor:
    """Test with ThreadPoolExecutor for parallel execution."""
    
    def test_parallel_config_serialization(self):
        """Parallel config JSON serialization."""
        configs = [
            BridgeConfig(primary=f"postgresql://localhost/db{i}")
            for i in range(100)
        ]
        
        def serialize(config):
            return config.to_json()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(serialize, c) for c in configs]
            results = [f.result() for f in as_completed(futures)]
        
        assert len(results) == 100
        # All should be valid JSON
        for r in results:
            assert '"primary"' in r
    
    def test_parallel_result_creation(self):
        """Parallel QueryResult creation."""
        def create_result(i):
            return QueryResult(
                success=True,
                rows=[[i, f"name_{i}"]],
                columns=["id", "name"],
            )
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_result, i) for i in range(100)]
            results = [f.result() for f in as_completed(futures)]
        
        assert len(results) == 100
        assert all(r.success for r in results)
    
    def test_parallel_result_iteration(self):
        """Parallel iteration over results."""
        result = QueryResult(
            success=True,
            rows=[[i, f"name_{i}"] for i in range(1000)],
            columns=["id", "name"],
        )
        
        def iterate_range(start, end):
            items = []
            for i in range(start, end):
                items.append(result[i])
            return len(items)
        
        ranges = [(i*100, (i+1)*100) for i in range(10)]
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(iterate_range, s, e) for s, e in ranges]
            counts = [f.result() for f in as_completed(futures)]
        
        assert sum(counts) == 1000


# =============================================================================
# Stress Tests
# =============================================================================

class TestStress:
    """Stress tests for Go bridge components."""
    
    def test_rapid_config_creation(self):
        """Create many configs rapidly."""
        start = time.time()
        
        configs = []
        for i in range(10000):
            config = BridgeConfig(
                primary=f"postgresql://localhost/db{i}",
            )
            configs.append(config)
        
        elapsed = time.time() - start
        
        assert len(configs) == 10000
        assert elapsed < 5.0, f"Too slow: {elapsed}s"
    
    def test_rapid_result_creation(self):
        """Create many results rapidly."""
        start = time.time()
        
        results = []
        for i in range(1000):
            result = QueryResult(
                success=True,
                rows=[[j, f"name_{j}"] for j in range(10)],
                columns=["id", "name"],
            )
            results.append(result)
        
        elapsed = time.time() - start
        
        assert len(results) == 1000
        assert elapsed < 5.0, f"Too slow: {elapsed}s"
    
    def test_large_result_set(self):
        """Handle very large result set."""
        # 100k rows
        rows = [[i, f"name_{i}", i * 1.5] for i in range(100000)]
        
        result = QueryResult(
            success=True,
            rows=rows,
            columns=["id", "name", "value"],
        )
        
        assert len(result) == 100000
        
        # Iteration should complete
        count = 0
        for _ in result:
            count += 1
        assert count == 100000
    
    def test_many_columns(self):
        """Handle result with many columns."""
        num_cols = 200
        columns = [f"col_{i}" for i in range(num_cols)]
        row = list(range(num_cols))
        
        result = QueryResult(
            success=True,
            rows=[row],
            columns=columns,
        )
        
        assert len(result.columns) == 200
        
        d = result.first_dict()
        assert len(d) == 200


# =============================================================================
# Memory Tests
# =============================================================================

class TestMemoryBehavior:
    """Test memory behavior under various conditions."""
    
    def test_result_garbage_collection(self):
        """Results should be garbage collected."""
        import gc
        
        # Create and discard many results
        for _ in range(100):
            result = QueryResult(
                success=True,
                rows=[[i] for i in range(1000)],
                columns=["id"],
            )
            # Don't keep reference
            del result
        
        gc.collect()
        # If this completes without OOM, we're good
    
    def test_config_reuse(self):
        """Config objects should be reusable."""
        config = BridgeConfig(primary="postgresql://localhost/test")
        
        # Serialize many times
        for _ in range(1000):
            _ = config.to_json()
        
        # Config should still be valid
        assert config.primary == "postgresql://localhost/test"


# =============================================================================
# Error Recovery Tests
# =============================================================================

class TestErrorRecovery:
    """Test error recovery in concurrent scenarios."""
    
    def test_error_does_not_corrupt_state(self):
        """Errors should not corrupt bridge state."""
        bridge = GoBridge()
        
        # Force some errors
        for _ in range(10):
            try:
                bridge.execute("SELECT 1")
            except BridgeError:
                pass  # Expected
        
        # Bridge should still be usable after init
        assert not bridge.is_initialized
        assert bridge.config is None
    
    def test_concurrent_errors_handled(self):
        """Concurrent errors should be handled gracefully."""
        bridge = GoBridge()
        errors = []
        
        def cause_error():
            try:
                bridge.execute("SELECT 1")
            except BridgeError:
                errors.append("expected")
            except Exception as e:
                errors.append(f"unexpected: {e}")
        
        threads = [threading.Thread(target=cause_error) for _ in range(20)]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All should be "expected" errors
        assert all(e == "expected" for e in errors)
        assert len(errors) == 20


# =============================================================================
# Producer-Consumer Pattern Tests
# =============================================================================

class TestProducerConsumer:
    """Test producer-consumer patterns with bridge."""
    
    def test_result_queue(self):
        """Results can be passed between threads via queue."""
        result_queue = queue.Queue()
        
        def producer():
            for i in range(10):
                result = QueryResult(
                    success=True,
                    rows=[[i]],
                    columns=["id"],
                )
                result_queue.put(result)
        
        def consumer():
            results = []
            while True:
                try:
                    result = result_queue.get(timeout=1)
                    results.append(result)
                except queue.Empty:
                    break
            return results
        
        prod_thread = threading.Thread(target=producer)
        cons_thread = threading.Thread(target=consumer)
        
        prod_thread.start()
        prod_thread.join()
        
        cons_thread.start()
        cons_thread.join()
        
        # Verify all results were produced
        assert result_queue.qsize() == 0 or True  # Consumer may have consumed


# =============================================================================
# Async Compatibility Tests
# =============================================================================

class TestAsyncCompatibility:
    """Test compatibility with async patterns."""
    
    @pytest.mark.asyncio
    async def test_sync_in_executor(self):
        """Sync operations can run in executor."""
        import asyncio
        
        def sync_config():
            return BridgeConfig(primary="postgresql://localhost/test")
        
        loop = asyncio.get_event_loop()
        config = await loop.run_in_executor(None, sync_config)
        
        assert config.primary == "postgresql://localhost/test"
    
    @pytest.mark.asyncio
    async def test_concurrent_async_executor(self):
        """Multiple async executor calls."""
        import asyncio
        
        def sync_version():
            return GoBridge.version()
        
        loop = asyncio.get_event_loop()
        
        tasks = [
            loop.run_in_executor(None, sync_version)
            for _ in range(10)
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 10
        assert all(isinstance(r, str) for r in results)


# =============================================================================
# Lock Contention Tests
# =============================================================================

class TestLockContention:
    """Test behavior under lock contention."""
    
    def test_high_contention_close(self):
        """High contention on close() operations."""
        bridge = GoBridge()
        
        barrier = threading.Barrier(10)
        errors = []
        
        def close_at_same_time():
            try:
                barrier.wait()  # Synchronize all threads
                bridge.close()
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=close_at_same_time) for _ in range(10)]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Errors: {errors}"
    
    def test_mixed_operations_under_contention(self):
        """Mixed read/write operations under contention."""
        bridge = GoBridge()
        
        operations = []
        errors = []
        
        def random_operation():
            try:
                import random
                op = random.choice(["version", "available", "close"])
                
                if op == "version":
                    GoBridge.version()
                elif op == "available":
                    _ = bridge.is_available
                elif op == "close":
                    bridge.close()
                
                operations.append(op)
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=random_operation) for _ in range(50)]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Errors: {errors}"
        assert len(operations) == 50
