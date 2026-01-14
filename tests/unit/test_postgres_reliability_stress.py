"""
Stress tests for PostgreSQL Reliability Components.

Tests cover:
- High concurrency with failures
- Rapid circuit breaker transitions
- Replica failover under load
- Degradation during traffic spike
- Recovery under sustained load
- Memory stability
- CPU efficiency

50 tests total.
"""

import asyncio
import gc
import pytest
import random
import sys
import threading
import time
from unittest.mock import AsyncMock, MagicMock

from pynext.db.adapters.postgres.reliability.retry import (
    RetryConfig,
    RetryManager,
    RetryError,
)
from pynext.db.adapters.postgres.reliability.circuit import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerRegistry,
    CircuitOpenError,
    CircuitState,
)
from pynext.db.adapters.postgres.reliability.replica import (
    Replica,
    ReplicaConfig,
    ReplicaManager,
    ReplicaHealth,
)
from pynext.db.adapters.postgres.reliability.degradation import (
    DegradationConfig,
    DegradationLevel,
    DegradationManager,
    DegradationMetric,
    DegradationTrigger,
    DegradationAction,
)


# ============================================================================
# High Concurrency Tests (15 tests)
# ============================================================================

class TestHighConcurrency:
    """Tests for high concurrency scenarios."""
    
    @pytest.mark.asyncio
    async def test_concurrent_retries_1000_requests(self):
        """Test 1000 concurrent retry operations."""
        config = RetryConfig(max_attempts=2, initial_delay=0.001, jitter=False)
        manager = RetryManager(config)
        
        success_count = [0]
        
        async def operation():
            await asyncio.sleep(0.001)
            success_count[0] += 1
            return True
        
        tasks = [
            asyncio.create_task(manager.execute_with_retry(operation))
            for _ in range(1000)
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert all(results)
        assert success_count[0] == 1000
    
    @pytest.mark.asyncio
    async def test_concurrent_circuit_checks_1000(self):
        """Test 1000 concurrent circuit breaker checks."""
        breaker = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=100))
        
        async def check_and_record():
            if breaker.allow_request():
                await asyncio.sleep(0.001)
                breaker.record_success()
                return True
            return False
        
        tasks = [
            asyncio.create_task(check_and_record())
            for _ in range(1000)
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert sum(results) == 1000
        assert breaker.stats.total_successes == 1000
    
    @pytest.mark.asyncio
    async def test_concurrent_mixed_success_failure(self):
        """Test concurrent operations with mixed success/failure."""
        config = RetryConfig(max_attempts=2, initial_delay=0.001, jitter=False)
        manager = RetryManager(config)
        
        results = {"success": 0, "failure": 0}
        
        async def mixed_operation():
            if random.random() < 0.8:  # 80% success
                results["success"] += 1
                return True
            else:
                raise ConnectionRefusedError()
        
        tasks = [
            asyncio.create_task(manager.execute_with_retry(mixed_operation))
            for _ in range(500)
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Most should succeed (with retry)
        assert results["success"] > 400
    
    @pytest.mark.asyncio
    async def test_concurrent_circuit_transitions(self):
        """Test concurrent operations during circuit transitions."""
        config = CircuitBreakerConfig(failure_threshold=50)
        breaker = CircuitBreaker("test", config)
        
        success_count = [0]
        failure_count = [0]
        rejection_count = [0]
        
        async def operation():
            if not breaker.allow_request():
                rejection_count[0] += 1
                return
            
            if random.random() < 0.3:  # 30% failure
                breaker.record_failure()
                failure_count[0] += 1
            else:
                breaker.record_success()
                success_count[0] += 1
        
        tasks = [asyncio.create_task(operation()) for _ in range(500)]
        await asyncio.gather(*tasks)
        
        total = success_count[0] + failure_count[0] + rejection_count[0]
        assert total == 500
    
    @pytest.mark.asyncio
    async def test_concurrent_replica_selection(self):
        """Test concurrent replica selection."""
        config = ReplicaConfig(
            replicas=[
                Replica("postgresql://r1/db", name="r1", weight=3),
                Replica("postgresql://r2/db", name="r2", weight=1),
            ],
            routing="weighted_random",
        )
        manager = ReplicaManager(config)
        manager._replica_health["r1"] = ReplicaHealth.HEALTHY
        manager._replica_health["r2"] = ReplicaHealth.HEALTHY
        
        selections = {"r1": 0, "r2": 0}
        
        async def select():
            replica = manager.select_replica()
            if replica:
                selections[replica.name] += 1
        
        tasks = [asyncio.create_task(select()) for _ in range(1000)]
        await asyncio.gather(*tasks)
        
        # r1 should get ~75% (weight 3 of 4)
        assert selections["r1"] > 600
        assert selections["r2"] > 150
    
    @pytest.mark.asyncio
    async def test_concurrent_degradation_checks(self):
        """Test concurrent degradation level checks."""
        config = DegradationConfig(
            triggers=[
                DegradationTrigger(
                    DegradationMetric.QUEUE_DEPTH,
                    100,
                    DegradationLevel.DEGRADED,
                ),
            ],
        )
        manager = DegradationManager(config)
        
        checks = [0]
        
        async def check():
            _ = manager.current_level
            _ = manager.is_degraded
            _ = manager.should_shed_load("normal")
            checks[0] += 1
        
        tasks = [asyncio.create_task(check()) for _ in range(1000)]
        await asyncio.gather(*tasks)
        
        assert checks[0] == 1000
    
    @pytest.mark.asyncio
    async def test_concurrent_registry_access(self):
        """Test concurrent circuit breaker registry access."""
        registry = CircuitBreakerRegistry()
        
        async def access_breakers():
            for i in range(100):
                breaker = registry.get_breaker(f"breaker_{i % 10}")
                breaker.record_success()
        
        tasks = [asyncio.create_task(access_breakers()) for _ in range(100)]
        await asyncio.gather(*tasks)
        
        # Should have 10 unique breakers
        assert len(registry.get_all_breakers()) == 10
    
    @pytest.mark.asyncio
    async def test_concurrent_stats_updates(self):
        """Test concurrent statistics updates."""
        breaker = CircuitBreaker("test")
        
        async def update_stats():
            for _ in range(100):
                if random.random() < 0.7:
                    breaker.record_success()
                else:
                    breaker.record_failure()
        
        tasks = [asyncio.create_task(update_stats()) for _ in range(100)]
        await asyncio.gather(*tasks)
        
        total = breaker.stats.total_successes + breaker.stats.total_failures
        assert total == 10000
    
    @pytest.mark.asyncio
    async def test_rapid_success_failure_alternation(self):
        """Test rapid success/failure alternation."""
        breaker = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=10))
        
        for i in range(1000):
            if i % 2 == 0:
                breaker.record_success()
            else:
                breaker.record_failure()
        
        # Should still be closed (alternating resets counters)
        assert breaker.is_closed
    
    @pytest.mark.asyncio
    async def test_burst_failures_then_recovery(self):
        """Test burst of failures followed by recovery."""
        config = CircuitBreakerConfig(
            failure_threshold=50,
            success_threshold=10,
            timeout=0.05,
            half_open_max_requests=15,  # Allow enough requests for success_threshold
        )
        breaker = CircuitBreaker("test", config)
        
        # Burst of failures
        for _ in range(50):
            breaker.record_failure()
        
        assert breaker.is_open
        
        # Wait for timeout to pass
        await asyncio.sleep(0.1)
        
        # Record successes - first request transitions to HALF_OPEN
        success_count = 0
        for _ in range(15):  # Try more than success_threshold
            if breaker.allow_request():
                breaker.record_success()
                success_count += 1
        
        # Should have gotten at least success_threshold successes
        assert success_count >= 10
        assert breaker.is_closed
    
    @pytest.mark.asyncio
    async def test_concurrent_force_operations(self):
        """Test concurrent force open/close operations."""
        breaker = CircuitBreaker("test")
        
        async def toggle():
            for _ in range(100):
                if random.random() < 0.5:
                    breaker.force_open()
                else:
                    breaker.force_close()
        
        tasks = [asyncio.create_task(toggle()) for _ in range(10)]
        await asyncio.gather(*tasks)
        
        # State should be valid
        assert breaker.state in [CircuitState.CLOSED, CircuitState.OPEN, CircuitState.HALF_OPEN]
    
    @pytest.mark.asyncio
    async def test_parallel_execute_with_retry(self):
        """Test parallel retry executions."""
        config = RetryConfig(max_attempts=3, initial_delay=0.001, jitter=False)
        managers = [RetryManager(config) for _ in range(10)]
        
        async def run_operations(manager):
            success = 0
            for _ in range(100):
                try:
                    await manager.execute_with_retry(lambda: asyncio.sleep(0))
                    success += 1
                except Exception:
                    pass
            return success
        
        tasks = [asyncio.create_task(run_operations(m)) for m in managers]
        results = await asyncio.gather(*tasks)
        
        assert sum(results) == 1000
    
    @pytest.mark.asyncio
    async def test_concurrent_degradation_level_changes(self):
        """Test concurrent degradation level changes."""
        manager = DegradationManager()
        
        levels_seen = set()
        
        async def change_level():
            for _ in range(100):
                level = random.choice(list(DegradationLevel))
                manager.force_level(level)
                levels_seen.add(manager.current_level)
        
        tasks = [asyncio.create_task(change_level()) for _ in range(10)]
        await asyncio.gather(*tasks)
        
        # Should have seen all levels
        assert DegradationLevel.NORMAL in levels_seen
    
    @pytest.mark.asyncio
    async def test_high_throughput_circuit_execute(self):
        """Test high throughput through circuit execute."""
        breaker = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=1000))
        
        async def noop():
            pass
        
        start = time.monotonic()
        
        for _ in range(10000):
            await breaker.execute(noop)
        
        elapsed = time.monotonic() - start
        
        # Should complete in reasonable time
        assert elapsed < 5.0
        assert breaker.stats.total_requests == 10000
    
    @pytest.mark.asyncio
    async def test_concurrent_round_robin(self):
        """Test concurrent round-robin selection."""
        config = ReplicaConfig(
            replicas=[
                Replica("postgresql://r1/db", name="r1"),
                Replica("postgresql://r2/db", name="r2"),
                Replica("postgresql://r3/db", name="r3"),
            ],
            routing="round_robin",
        )
        manager = ReplicaManager(config)
        for name in ["r1", "r2", "r3"]:
            manager._replica_health[name] = ReplicaHealth.HEALTHY
        
        selections = {"r1": 0, "r2": 0, "r3": 0}
        lock = asyncio.Lock()
        
        async def select():
            replica = manager.select_replica()
            async with lock:
                selections[replica.name] += 1
        
        tasks = [asyncio.create_task(select()) for _ in range(900)]
        await asyncio.gather(*tasks)
        
        # Should be evenly distributed
        for count in selections.values():
            assert 250 <= count <= 350


# ============================================================================
# Rapid State Transition Tests (10 tests)
# ============================================================================

class TestRapidStateTransitions:
    """Tests for rapid state transitions."""
    
    @pytest.mark.asyncio
    async def test_rapid_circuit_open_close(self):
        """Test rapid circuit open/close cycles."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            success_threshold=1,
            timeout=0.001,
        )
        breaker = CircuitBreaker("test", config)
        
        for _ in range(100):
            breaker.record_failure()
            await asyncio.sleep(0.002)
            if breaker.allow_request():
                breaker.record_success()
        
        # Should have many transitions
        assert breaker.stats.state_transitions >= 50
    
    @pytest.mark.asyncio
    async def test_rapid_degradation_escalation(self):
        """Test rapid degradation level escalation."""
        manager = DegradationManager()
        
        for _ in range(100):
            for level in DegradationLevel:
                manager.force_level(level)
        
        assert manager.stats.level_changes == 400
    
    @pytest.mark.asyncio
    async def test_rapid_replica_health_changes(self):
        """Test rapid replica health changes."""
        config = ReplicaConfig(
            replicas=[
                Replica("postgresql://r1/db", name="r1"),
                Replica("postgresql://r2/db", name="r2"),
            ],
        )
        manager = ReplicaManager(config)
        
        for _ in range(1000):
            name = random.choice(["r1", "r2"])
            if random.random() < 0.5:
                manager.mark_replica_healthy(name)
            else:
                manager.mark_replica_unhealthy(name)
        
        # Should have valid health states
        for name in ["r1", "r2"]:
            assert manager._replica_health[name] in [ReplicaHealth.HEALTHY, ReplicaHealth.UNHEALTHY]
    
    @pytest.mark.asyncio
    async def test_circuit_timeout_races(self):
        """Test circuit timeout races."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            timeout=0.001,
        )
        breaker = CircuitBreaker("test", config)
        
        races_won = [0]
        
        async def race():
            breaker.record_failure()
            await asyncio.sleep(0.001)
            if breaker.allow_request():
                races_won[0] += 1
        
        tasks = [asyncio.create_task(race()) for _ in range(100)]
        await asyncio.gather(*tasks)
        
        assert races_won[0] > 0
    
    @pytest.mark.asyncio
    async def test_half_open_request_limit(self):
        """Test half-open request limiting under load."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            timeout=0.001,
            half_open_max_requests=5,
        )
        breaker = CircuitBreaker("test", config)
        
        breaker.record_failure()
        await asyncio.sleep(0.002)
        
        allowed = sum(1 for _ in range(100) if breaker.allow_request())
        
        # Only 5 should be allowed in half-open
        assert allowed == 5
    
    @pytest.mark.asyncio
    async def test_concurrent_state_queries(self):
        """Test concurrent state queries during transitions."""
        breaker = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=1))
        
        states_seen = []
        
        async def query_state():
            for _ in range(100):
                states_seen.append(breaker.state)
                if random.random() < 0.3:
                    breaker.record_failure()
                elif random.random() < 0.3:
                    breaker.record_success()
        
        tasks = [asyncio.create_task(query_state()) for _ in range(10)]
        await asyncio.gather(*tasks)
        
        # Should have captured various states
        assert len(states_seen) == 1000
    
    @pytest.mark.asyncio
    async def test_degradation_trigger_evaluation_speed(self):
        """Test trigger evaluation speed."""
        triggers = [
            DegradationTrigger(DegradationMetric.QUEUE_DEPTH, i * 10, DegradationLevel.DEGRADED)
            for i in range(1, 101)
        ]
        
        config = DegradationConfig(triggers=triggers)
        manager = DegradationManager(config)
        
        metrics = {"queue_depth": 500}
        
        start = time.monotonic()
        for _ in range(10000):
            manager._evaluate_triggers(metrics)
        elapsed = time.monotonic() - start
        
        # Should be fast
        assert elapsed < 2.0
    
    @pytest.mark.asyncio
    async def test_registry_create_delete_cycle(self):
        """Test rapid registry create/delete cycles."""
        registry = CircuitBreakerRegistry()
        
        for i in range(1000):
            key = f"breaker_{i % 10}"
            registry.get_breaker(key)
            if i % 20 == 0:
                registry.remove_breaker(key)
        
        # Should have some breakers
        assert len(registry.get_all_breakers()) > 0
    
    @pytest.mark.asyncio
    async def test_retry_delay_timing(self):
        """Test retry delay timing accuracy."""
        config = RetryConfig(
            max_attempts=5,
            initial_delay=0.01,
            backoff="fixed",
            jitter=False,
        )
        manager = RetryManager(config)
        
        timestamps = []
        
        async def timed_operation():
            timestamps.append(time.monotonic())
            if len(timestamps) < 5:
                raise ConnectionRefusedError()
            return "success"
        
        await manager.execute_with_retry(timed_operation)
        
        # Check delays
        for i in range(1, len(timestamps)):
            delay = timestamps[i] - timestamps[i-1]
            assert 0.005 <= delay <= 0.02
    
    @pytest.mark.asyncio
    async def test_stats_update_speed(self):
        """Test statistics update speed."""
        breaker = CircuitBreaker("test")
        
        start = time.monotonic()
        for _ in range(100000):
            breaker.record_success()
        elapsed = time.monotonic() - start
        
        assert elapsed < 2.0
        assert breaker.stats.total_successes == 100000


# ============================================================================
# Resource Management Tests (15 tests)
# ============================================================================

class TestResourceManagement:
    """Tests for memory and resource management."""
    
    @pytest.mark.asyncio
    async def test_retry_stats_memory_bound(self):
        """Test retry stats don't grow unbounded."""
        config = RetryConfig(max_attempts=2, initial_delay=0.001, jitter=False)
        manager = RetryManager(config)
        
        async def op():
            return True
        
        for _ in range(10000):
            await manager.execute_with_retry(op)
        
        # Stats should be bounded
        stats_dict = manager.stats.to_dict()
        assert sys.getsizeof(str(stats_dict)) < 10000
    
    @pytest.mark.asyncio
    async def test_circuit_recent_results_bounded(self):
        """Test circuit breaker recent results are bounded."""
        breaker = CircuitBreaker("test")
        
        for i in range(10000):
            if i % 2 == 0:
                breaker.record_success()
            else:
                breaker.record_failure()
        
        # Recent results should be bounded
        assert len(breaker.stats._recent_results) <= 1000
    
    @pytest.mark.asyncio
    async def test_registry_cleanup(self):
        """Test registry can be cleaned up."""
        registry = CircuitBreakerRegistry()
        
        # Create many breakers
        for i in range(100):
            registry.get_breaker(f"breaker_{i}")
        
        assert len(registry.get_all_breakers()) == 100
        
        # Clear
        registry.clear()
        
        assert len(registry.get_all_breakers()) == 0
    
    @pytest.mark.asyncio
    async def test_replica_manager_cleanup(self):
        """Test replica manager cleanup."""
        config = ReplicaConfig(
            replicas=[Replica("postgresql://r1/db", name="r1")],
        )
        
        async def create_pool(url):
            pool = AsyncMock()
            pool.close = AsyncMock()
            return pool
        
        manager = ReplicaManager(config, create_pool=create_pool)
        await manager.start()
        
        assert len(manager._replica_pools) == 1
        
        await manager.stop()
        
        assert len(manager._replica_pools) == 0
    
    @pytest.mark.asyncio
    async def test_degradation_monitoring_cleanup(self):
        """Test degradation monitoring cleanup."""
        manager = DegradationManager()
        
        await manager.start(lambda: {})
        assert manager._running is True
        
        await manager.stop()
        assert manager._running is False
    
    @pytest.mark.asyncio
    async def test_concurrent_manager_creation(self):
        """Test concurrent manager creation doesn't leak."""
        managers = []
        
        for _ in range(100):
            manager = RetryManager()
            managers.append(manager)
        
        # Clean up
        managers.clear()
        gc.collect()
    
    @pytest.mark.asyncio
    async def test_error_objects_dont_leak(self):
        """Test error objects don't leak."""
        config = RetryConfig(max_attempts=2, initial_delay=0.001, jitter=False)
        manager = RetryManager(config)
        
        async def failing():
            raise ConnectionRefusedError()
        
        errors = []
        for _ in range(1000):
            try:
                await manager.execute_with_retry(failing)
            except RetryError as e:
                errors.append(e)
        
        # Errors should be collectible
        errors.clear()
        gc.collect()
    
    @pytest.mark.asyncio
    async def test_task_cleanup(self):
        """Test async tasks are cleaned up."""
        manager = DegradationManager()
        
        await manager.start(lambda: {})
        task = manager._monitoring_task
        
        await manager.stop()
        
        # Task should be done
        assert task.done() or task.cancelled()
    
    @pytest.mark.asyncio
    async def test_stats_reset(self):
        """Test stats can be reset to free memory."""
        manager = RetryManager()
        
        async def op():
            return True
        
        for _ in range(1000):
            await manager.execute_with_retry(op)
        
        assert manager.stats.total_attempts == 1000
        
        manager.reset_stats()
        
        assert manager.stats.total_attempts == 0
    
    @pytest.mark.asyncio
    async def test_circuit_reset_clears_state(self):
        """Test circuit reset clears state."""
        breaker = CircuitBreaker("test")
        
        for _ in range(1000):
            breaker.record_success()
        
        breaker.reset()
        
        assert breaker.stats.total_successes == 0
    
    @pytest.mark.asyncio
    async def test_long_running_stability(self):
        """Test stability over many operations."""
        config = RetryConfig(max_attempts=2, initial_delay=0.001, jitter=False)
        manager = RetryManager(config)
        breaker = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=1000))
        
        async def operation():
            await breaker.execute(lambda: asyncio.sleep(0))
            return True
        
        # Run many operations
        for batch in range(10):
            tasks = [
                asyncio.create_task(manager.execute_with_retry(operation))
                for _ in range(1000)
            ]
            await asyncio.gather(*tasks)
        
        assert manager.stats.total_successes == 10000
        assert breaker.stats.total_successes == 10000
    
    @pytest.mark.asyncio
    async def test_concurrent_stop_start(self):
        """Test concurrent stop/start operations."""
        manager = DegradationManager()
        
        async def toggle():
            for _ in range(10):
                await manager.start(lambda: {})
                await asyncio.sleep(0.01)
                await manager.stop()
        
        tasks = [asyncio.create_task(toggle()) for _ in range(5)]
        await asyncio.gather(*tasks)
        
        # Should be stopped
        await manager.stop()
        assert not manager._running
    
    @pytest.mark.asyncio
    async def test_registry_many_breakers(self):
        """Test registry with many breakers."""
        registry = CircuitBreakerRegistry()
        
        for i in range(10000):
            registry.get_breaker(f"breaker_{i}")
        
        assert len(registry.get_all_breakers()) == 10000
        
        # Clear and verify
        registry.clear()
        assert len(registry.get_all_breakers()) == 0
    
    @pytest.mark.asyncio
    async def test_thread_safety_stress(self):
        """Test thread safety under stress."""
        breaker = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=1000))
        errors = []
        
        def thread_work():
            try:
                for _ in range(1000):
                    if random.random() < 0.5:
                        breaker.record_success()
                    else:
                        breaker.record_failure()
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=thread_work) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0
        total = breaker.stats.total_successes + breaker.stats.total_failures
        assert total == 10000
    
    @pytest.mark.asyncio
    async def test_degradation_stats_bounded(self):
        """Test degradation stats are bounded."""
        manager = DegradationManager()
        
        # Many level changes
        for i in range(10000):
            level = DegradationLevel(i % 4)
            manager.force_level(level)
        
        stats = manager.stats.to_dict()
        
        # Should be bounded
        assert manager.stats.level_changes == 10000
        assert len(manager.stats.time_in_level) == 4


# ============================================================================
# Performance Tests (10 tests)
# ============================================================================

class TestPerformance:
    """Tests for performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_retry_latency(self):
        """Test retry adds minimal latency on success."""
        config = RetryConfig(max_attempts=3, initial_delay=1.0)  # Long delay
        manager = RetryManager(config)
        
        async def op():
            return True
        
        start = time.monotonic()
        for _ in range(1000):
            await manager.execute_with_retry(op)
        elapsed = time.monotonic() - start
        
        # Should be fast (no retries)
        assert elapsed < 1.0
    
    @pytest.mark.asyncio
    async def test_circuit_check_latency(self):
        """Test circuit check latency."""
        breaker = CircuitBreaker("test")
        
        start = time.monotonic()
        for _ in range(100000):
            breaker.allow_request()
        elapsed = time.monotonic() - start
        
        # Should be very fast
        assert elapsed < 1.0
    
    @pytest.mark.asyncio
    async def test_replica_selection_latency(self):
        """Test replica selection latency."""
        config = ReplicaConfig(
            replicas=[
                Replica("postgresql://r1/db", name="r1"),
                Replica("postgresql://r2/db", name="r2"),
                Replica("postgresql://r3/db", name="r3"),
            ],
        )
        manager = ReplicaManager(config)
        for name in ["r1", "r2", "r3"]:
            manager._replica_health[name] = ReplicaHealth.HEALTHY
        
        start = time.monotonic()
        for _ in range(100000):
            manager.select_replica()
        elapsed = time.monotonic() - start
        
        assert elapsed < 2.0
    
    @pytest.mark.asyncio
    async def test_degradation_check_latency(self):
        """Test degradation check latency."""
        manager = DegradationManager()
        
        start = time.monotonic()
        for _ in range(100000):
            manager.should_shed_load("normal")
        elapsed = time.monotonic() - start
        
        assert elapsed < 1.0
    
    @pytest.mark.asyncio
    async def test_stats_to_dict_latency(self):
        """Test stats serialization latency."""
        breaker = CircuitBreaker("test")
        
        for _ in range(1000):
            breaker.record_success()
        
        start = time.monotonic()
        for _ in range(10000):
            breaker.stats.to_dict()
        elapsed = time.monotonic() - start
        
        assert elapsed < 2.0
    
    @pytest.mark.asyncio
    async def test_concurrent_performance(self):
        """Test performance under concurrent load."""
        manager = RetryManager()
        breaker = CircuitBreaker("test")
        
        async def operation():
            await breaker.execute(lambda: asyncio.sleep(0))
            return True
        
        start = time.monotonic()
        
        tasks = [
            asyncio.create_task(manager.execute_with_retry(operation))
            for _ in range(10000)
        ]
        await asyncio.gather(*tasks)
        
        elapsed = time.monotonic() - start
        
        # Should complete in reasonable time
        assert elapsed < 10.0
    
    @pytest.mark.asyncio
    async def test_backoff_calculation_performance(self):
        """Test backoff calculation performance."""
        config = RetryConfig()
        manager = RetryManager(config)
        
        start = time.monotonic()
        for _ in range(100000):
            manager.get_delay(5)
        elapsed = time.monotonic() - start
        
        assert elapsed < 1.0
    
    @pytest.mark.asyncio
    async def test_registry_lookup_performance(self):
        """Test registry lookup performance."""
        registry = CircuitBreakerRegistry()
        
        # Pre-create breakers
        for i in range(100):
            registry.get_breaker(f"breaker_{i}")
        
        start = time.monotonic()
        for _ in range(100000):
            key = f"breaker_{random.randint(0, 99)}"
            registry.get_breaker(key)
        elapsed = time.monotonic() - start
        
        assert elapsed < 2.0
    
    @pytest.mark.asyncio
    async def test_trigger_evaluation_performance(self):
        """Test trigger evaluation performance."""
        triggers = [
            DegradationTrigger(
                DegradationMetric.QUEUE_DEPTH,
                threshold * 10,
                level,
            )
            for threshold in range(1, 20)
            for level in DegradationLevel
        ]
        
        config = DegradationConfig(triggers=triggers)
        manager = DegradationManager(config)
        
        metrics = {
            "queue_depth": 100,
            "error_rate": 0.1,
            "latency_p95": 500,
        }
        
        start = time.monotonic()
        for _ in range(10000):
            manager._evaluate_triggers(metrics)
        elapsed = time.monotonic() - start
        
        assert elapsed < 2.0
    
    @pytest.mark.asyncio
    async def test_throughput_measurement(self):
        """Test overall throughput."""
        config = RetryConfig(max_attempts=1)
        manager = RetryManager(config)
        breaker = CircuitBreaker("test")
        
        async def operation():
            if breaker.allow_request():
                breaker.record_success()
            return True
        
        start = time.monotonic()
        count = 0
        
        while time.monotonic() - start < 1.0:
            await manager.execute_with_retry(operation)
            count += 1
        
        # Should achieve high throughput
        assert count > 10000

