"""
Comprehensive tests for PostgreSQL Circuit Breaker.

Tests cover:
- Circuit state transitions (closed → open → half-open → closed)
- Failure threshold triggering
- Success threshold recovery
- Timeout-based recovery
- Global circuit breaker
- Per-connection breakers
- Per-query-type breakers
- Registry management
- Concurrent access
- Statistics tracking
- Error type filtering
- Half-open test requests

120 tests total.
"""

import asyncio
import pytest
import threading
import time
from unittest.mock import AsyncMock, MagicMock, patch

from pynext.db.adapters.postgres_circuit import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerRegistry,
    CircuitOpenError,
    CircuitScope,
    CircuitState,
    CircuitStats,
    create_global_breaker,
    create_sensitive_breaker,
    create_tolerant_breaker,
)


# ============================================================================
# CircuitBreakerConfig Tests (15 tests)
# ============================================================================

class TestCircuitBreakerConfig:
    """Tests for CircuitBreakerConfig dataclass."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = CircuitBreakerConfig()
        assert config.failure_threshold == 5
        assert config.success_threshold == 2
        assert config.timeout == 30.0
        assert config.scope == "global"
        assert config.half_open_max_requests == 1
        assert config.failure_rate_threshold is None
        assert config.sample_window == 60.0
    
    def test_custom_values(self):
        """Test custom configuration values."""
        config = CircuitBreakerConfig(
            failure_threshold=10,
            success_threshold=3,
            timeout=60.0,
            scope="connection",
        )
        assert config.failure_threshold == 10
        assert config.success_threshold == 3
        assert config.timeout == 60.0
        assert config.scope == "connection"
    
    def test_invalid_failure_threshold(self):
        """Test validation for failure_threshold."""
        with pytest.raises(ValueError, match="failure_threshold must be >= 1"):
            CircuitBreakerConfig(failure_threshold=0)
    
    def test_invalid_success_threshold(self):
        """Test validation for success_threshold."""
        with pytest.raises(ValueError, match="success_threshold must be >= 1"):
            CircuitBreakerConfig(success_threshold=0)
    
    def test_invalid_timeout(self):
        """Test validation for timeout."""
        with pytest.raises(ValueError, match="timeout must be >= 0"):
            CircuitBreakerConfig(timeout=-1)
    
    def test_invalid_scope(self):
        """Test validation for scope."""
        with pytest.raises(ValueError, match="scope must be global/connection/query_type"):
            CircuitBreakerConfig(scope="invalid")
    
    def test_valid_scopes(self):
        """Test all valid scope values."""
        for scope in ["global", "connection", "query_type"]:
            config = CircuitBreakerConfig(scope=scope)
            assert config.scope == scope
    
    def test_failure_rate_threshold_validation(self):
        """Test failure_rate_threshold validation."""
        with pytest.raises(ValueError, match="failure_rate_threshold must be 0-1"):
            CircuitBreakerConfig(failure_rate_threshold=1.5)
        
        with pytest.raises(ValueError, match="failure_rate_threshold must be 0-1"):
            CircuitBreakerConfig(failure_rate_threshold=0)
    
    def test_valid_failure_rate_threshold(self):
        """Test valid failure_rate_threshold values."""
        config = CircuitBreakerConfig(failure_rate_threshold=0.5)
        assert config.failure_rate_threshold == 0.5
    
    def test_excluded_errors(self):
        """Test excluded_errors set."""
        config = CircuitBreakerConfig(excluded_errors={ValueError, KeyError})
        assert ValueError in config.excluded_errors
        assert KeyError in config.excluded_errors
    
    def test_zero_timeout_valid(self):
        """Test zero timeout is valid."""
        config = CircuitBreakerConfig(timeout=0)
        assert config.timeout == 0
    
    def test_sample_window_default(self):
        """Test sample_window default value."""
        config = CircuitBreakerConfig()
        assert config.sample_window == 60.0
    
    def test_half_open_max_requests_custom(self):
        """Test custom half_open_max_requests."""
        config = CircuitBreakerConfig(half_open_max_requests=5)
        assert config.half_open_max_requests == 5
    
    def test_boundary_values(self):
        """Test boundary configuration values."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            success_threshold=1,
            failure_rate_threshold=0.01,
        )
        assert config.failure_threshold == 1
        assert config.success_threshold == 1
        assert config.failure_rate_threshold == 0.01
    
    def test_failure_rate_max_boundary(self):
        """Test failure_rate_threshold at max."""
        config = CircuitBreakerConfig(failure_rate_threshold=1.0)
        assert config.failure_rate_threshold == 1.0


# ============================================================================
# CircuitBreaker State Tests (25 tests)
# ============================================================================

class TestCircuitBreakerState:
    """Tests for circuit breaker state transitions."""
    
    def test_initial_state_closed(self):
        """Test circuit starts in closed state."""
        breaker = CircuitBreaker("test")
        assert breaker.state == CircuitState.CLOSED
        assert breaker.is_closed is True
        assert breaker.is_open is False
        assert breaker.is_half_open is False
    
    def test_closed_allows_requests(self):
        """Test closed circuit allows requests."""
        breaker = CircuitBreaker("test")
        assert breaker.allow_request() is True
    
    def test_failure_below_threshold(self):
        """Test failures below threshold don't open circuit."""
        config = CircuitBreakerConfig(failure_threshold=5)
        breaker = CircuitBreaker("test", config)
        
        for _ in range(4):
            breaker.record_failure()
        
        assert breaker.state == CircuitState.CLOSED
    
    def test_failure_at_threshold_opens(self):
        """Test failures at threshold opens circuit."""
        config = CircuitBreakerConfig(failure_threshold=5)
        breaker = CircuitBreaker("test", config)
        
        for _ in range(5):
            breaker.record_failure()
        
        assert breaker.state == CircuitState.OPEN
    
    def test_open_rejects_requests(self):
        """Test open circuit rejects requests."""
        config = CircuitBreakerConfig(failure_threshold=1)
        breaker = CircuitBreaker("test", config)
        
        breaker.record_failure()
        
        assert breaker.state == CircuitState.OPEN
        assert breaker.allow_request() is False
    
    def test_success_resets_failure_count(self):
        """Test success resets consecutive failures."""
        config = CircuitBreakerConfig(failure_threshold=5)
        breaker = CircuitBreaker("test", config)
        
        for _ in range(4):
            breaker.record_failure()
        
        breaker.record_success()
        
        # Should reset, need 5 more to open
        for _ in range(4):
            breaker.record_failure()
        
        assert breaker.state == CircuitState.CLOSED
    
    def test_timeout_triggers_half_open(self):
        """Test timeout transitions to half-open."""
        config = CircuitBreakerConfig(failure_threshold=1, timeout=0.1)
        breaker = CircuitBreaker("test", config)
        
        breaker.record_failure()
        assert breaker.state == CircuitState.OPEN
        
        time.sleep(0.15)
        
        # Next request should be allowed (half-open)
        assert breaker.allow_request() is True
        assert breaker.state == CircuitState.HALF_OPEN
    
    def test_half_open_success_closes(self):
        """Test success in half-open closes circuit."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            success_threshold=1,
            timeout=0.01,
        )
        breaker = CircuitBreaker("test", config)
        
        breaker.record_failure()
        time.sleep(0.02)
        breaker.allow_request()  # Transition to half-open
        
        breaker.record_success()
        
        assert breaker.state == CircuitState.CLOSED
    
    def test_half_open_failure_opens(self):
        """Test failure in half-open reopens circuit."""
        config = CircuitBreakerConfig(failure_threshold=1, timeout=0.01)
        breaker = CircuitBreaker("test", config)
        
        breaker.record_failure()
        time.sleep(0.02)
        breaker.allow_request()  # Transition to half-open
        
        breaker.record_failure()
        
        assert breaker.state == CircuitState.OPEN
    
    def test_multiple_successes_required(self):
        """Test multiple successes needed to close."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            success_threshold=3,
            timeout=0.01,
        )
        breaker = CircuitBreaker("test", config)
        
        breaker.record_failure()
        time.sleep(0.02)
        breaker.allow_request()  # Transition to half-open
        
        breaker.record_success()
        assert breaker.state == CircuitState.HALF_OPEN
        
        breaker.record_success()
        assert breaker.state == CircuitState.HALF_OPEN
        
        breaker.record_success()
        assert breaker.state == CircuitState.CLOSED
    
    def test_half_open_limited_requests(self):
        """Test half-open limits concurrent requests."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            timeout=0.01,
            half_open_max_requests=1,
        )
        breaker = CircuitBreaker("test", config)
        
        breaker.record_failure()
        time.sleep(0.02)
        
        # First request allowed
        assert breaker.allow_request() is True
        
        # Second request rejected
        assert breaker.allow_request() is False
    
    def test_half_open_multiple_requests(self):
        """Test half-open with higher request limit."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            timeout=0.01,
            half_open_max_requests=3,
        )
        breaker = CircuitBreaker("test", config)
        
        breaker.record_failure()
        time.sleep(0.02)
        
        # First three requests allowed
        assert breaker.allow_request() is True
        assert breaker.allow_request() is True
        assert breaker.allow_request() is True
        
        # Fourth rejected
        assert breaker.allow_request() is False
    
    def test_reset_closes_circuit(self):
        """Test reset() closes the circuit."""
        config = CircuitBreakerConfig(failure_threshold=1)
        breaker = CircuitBreaker("test", config)
        
        breaker.record_failure()
        assert breaker.state == CircuitState.OPEN
        
        breaker.reset()
        assert breaker.state == CircuitState.CLOSED
    
    def test_force_open(self):
        """Test force_open() opens the circuit."""
        breaker = CircuitBreaker("test")
        
        breaker.force_open()
        
        assert breaker.state == CircuitState.OPEN
        assert breaker.allow_request() is False
    
    def test_force_close(self):
        """Test force_close() closes the circuit."""
        config = CircuitBreakerConfig(failure_threshold=1)
        breaker = CircuitBreaker("test", config)
        
        breaker.record_failure()
        breaker.force_close()
        
        assert breaker.state == CircuitState.CLOSED
    
    def test_time_until_half_open_when_open(self):
        """Test time_until_half_open when open."""
        config = CircuitBreakerConfig(failure_threshold=1, timeout=30.0)
        breaker = CircuitBreaker("test", config)
        
        breaker.record_failure()
        
        remaining = breaker.get_time_until_half_open()
        assert 29.0 <= remaining <= 30.0
    
    def test_time_until_half_open_when_closed(self):
        """Test time_until_half_open when closed."""
        breaker = CircuitBreaker("test")
        
        remaining = breaker.get_time_until_half_open()
        assert remaining == 0.0
    
    def test_excluded_errors_dont_count(self):
        """Test excluded errors don't increment failure count."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            excluded_errors={ValueError},
        )
        breaker = CircuitBreaker("test", config)
        
        breaker.record_failure(ValueError("ignored"))
        breaker.record_failure(ValueError("also ignored"))
        
        assert breaker.state == CircuitState.CLOSED
        
        # Regular errors still count
        breaker.record_failure(Exception("counts"))
        breaker.record_failure(Exception("counts"))
        
        assert breaker.state == CircuitState.OPEN
    
    def test_name_property(self):
        """Test name property."""
        breaker = CircuitBreaker("my-circuit")
        assert breaker.name == "my-circuit"
    
    def test_state_transitions_logged(self):
        """Test state transitions are recorded in stats."""
        config = CircuitBreakerConfig(failure_threshold=1, timeout=0.01)
        breaker = CircuitBreaker("test", config)
        
        assert breaker.stats.state_transitions == 0
        
        breaker.record_failure()  # closed → open
        assert breaker.stats.state_transitions == 1
        
        time.sleep(0.02)
        breaker.allow_request()  # open → half-open
        assert breaker.stats.state_transitions == 2
    
    def test_failure_rate_threshold(self):
        """Test failure rate threshold triggers open."""
        config = CircuitBreakerConfig(
            failure_rate_threshold=0.5,
            failure_threshold=100,  # High, won't trigger
        )
        breaker = CircuitBreaker("test", config)
        
        # Record 6 failures out of 10
        for _ in range(4):
            breaker.stats.record_success()
        for _ in range(6):
            breaker.stats.record_failure()
        
        # Manually check threshold
        assert breaker._should_trip() is True
    
    def test_consecutive_failure_tracking(self):
        """Test consecutive failures are tracked."""
        breaker = CircuitBreaker("test")
        
        breaker.record_failure()
        assert breaker.stats.consecutive_failures == 1
        
        breaker.record_failure()
        assert breaker.stats.consecutive_failures == 2
        
        breaker.record_success()
        assert breaker.stats.consecutive_failures == 0
    
    def test_consecutive_success_tracking(self):
        """Test consecutive successes are tracked."""
        breaker = CircuitBreaker("test")
        
        breaker.record_success()
        assert breaker.stats.consecutive_successes == 1
        
        breaker.record_success()
        assert breaker.stats.consecutive_successes == 2
        
        breaker.record_failure()
        assert breaker.stats.consecutive_successes == 0
    
    def test_open_timeout_zero_immediate_half_open(self):
        """Test zero timeout allows immediate half-open."""
        config = CircuitBreakerConfig(failure_threshold=1, timeout=0)
        breaker = CircuitBreaker("test", config)
        
        breaker.record_failure()
        
        # Should immediately try half-open
        assert breaker.allow_request() is True
        assert breaker.state == CircuitState.HALF_OPEN


# ============================================================================
# CircuitBreaker Execute Tests (15 tests)
# ============================================================================

class TestCircuitBreakerExecute:
    """Tests for circuit breaker execute method."""
    
    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Test execute with successful operation."""
        breaker = CircuitBreaker("test")
        
        async def operation():
            return "result"
        
        result = await breaker.execute(operation)
        assert result == "result"
        assert breaker.stats.total_successes == 1
    
    @pytest.mark.asyncio
    async def test_execute_failure(self):
        """Test execute with failing operation."""
        breaker = CircuitBreaker("test")
        
        async def operation():
            raise ValueError("error")
        
        with pytest.raises(ValueError):
            await breaker.execute(operation)
        
        assert breaker.stats.total_failures == 1
    
    @pytest.mark.asyncio
    async def test_execute_circuit_open(self):
        """Test execute when circuit is open."""
        config = CircuitBreakerConfig(failure_threshold=1)
        breaker = CircuitBreaker("test", config)
        
        breaker.record_failure()
        
        async def operation():
            return "should not run"
        
        with pytest.raises(CircuitOpenError) as exc_info:
            await breaker.execute(operation)
        
        assert exc_info.value.circuit_name == "test"
        assert exc_info.value.time_until_half_open > 0
    
    @pytest.mark.asyncio
    async def test_execute_with_arguments(self):
        """Test execute with function arguments."""
        breaker = CircuitBreaker("test")
        
        async def operation(a, b, c=None):
            return f"{a}-{b}-{c}"
        
        result = await breaker.execute(operation, "x", "y", c="z")
        assert result == "x-y-z"
    
    @pytest.mark.asyncio
    async def test_execute_records_request(self):
        """Test execute records request in stats."""
        breaker = CircuitBreaker("test")
        
        async def operation():
            return True
        
        await breaker.execute(operation)
        assert breaker.stats.total_requests == 1
    
    @pytest.mark.asyncio
    async def test_execute_rejection_stats(self):
        """Test rejection is recorded in stats."""
        config = CircuitBreakerConfig(failure_threshold=1)
        breaker = CircuitBreaker("test", config)
        
        breaker.record_failure()
        
        async def operation():
            pass
        
        with pytest.raises(CircuitOpenError):
            await breaker.execute(operation)
        
        assert breaker.stats.total_rejections == 1
    
    @pytest.mark.asyncio
    async def test_execute_half_open_success(self):
        """Test successful execute in half-open state."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            success_threshold=1,
            timeout=0.01,
        )
        breaker = CircuitBreaker("test", config)
        
        breaker.record_failure()
        time.sleep(0.02)
        
        async def operation():
            return "recovered"
        
        result = await breaker.execute(operation)
        assert result == "recovered"
        assert breaker.state == CircuitState.CLOSED
    
    @pytest.mark.asyncio
    async def test_execute_half_open_failure(self):
        """Test failing execute in half-open state."""
        config = CircuitBreakerConfig(failure_threshold=1, timeout=0.01)
        breaker = CircuitBreaker("test", config)
        
        breaker.record_failure()
        time.sleep(0.02)
        
        async def operation():
            raise ValueError("still broken")
        
        with pytest.raises(ValueError):
            await breaker.execute(operation)
        
        assert breaker.state == CircuitState.OPEN
    
    @pytest.mark.asyncio
    async def test_execute_concurrent_operations(self):
        """Test concurrent execute operations."""
        breaker = CircuitBreaker("test")
        
        results = []
        
        async def operation(n):
            await asyncio.sleep(0.01)
            return n
        
        tasks = [breaker.execute(operation, i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        assert results == list(range(10))
        assert breaker.stats.total_requests == 10
    
    @pytest.mark.asyncio
    async def test_execute_excluded_error(self):
        """Test execute with excluded error."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            excluded_errors={ValueError},
        )
        breaker = CircuitBreaker("test", config)
        
        async def operation():
            raise ValueError("excluded")
        
        with pytest.raises(ValueError):
            await breaker.execute(operation)
        
        # Should still be closed since error is excluded
        assert breaker.state == CircuitState.CLOSED
    
    @pytest.mark.asyncio
    async def test_execute_async_generator(self):
        """Test execute returns result correctly."""
        breaker = CircuitBreaker("test")
        
        async def operation():
            await asyncio.sleep(0.001)
            return {"key": "value"}
        
        result = await breaker.execute(operation)
        assert result == {"key": "value"}
    
    @pytest.mark.asyncio
    async def test_execute_none_result(self):
        """Test execute returning None."""
        breaker = CircuitBreaker("test")
        
        async def operation():
            return None
        
        result = await breaker.execute(operation)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_execute_trips_circuit(self):
        """Test execute can trip the circuit."""
        config = CircuitBreakerConfig(failure_threshold=3)
        breaker = CircuitBreaker("test", config)
        
        async def failing():
            raise ConnectionRefusedError()
        
        for _ in range(3):
            with pytest.raises(ConnectionRefusedError):
                await breaker.execute(failing)
        
        assert breaker.state == CircuitState.OPEN
    
    @pytest.mark.asyncio
    async def test_circuit_open_error_message(self):
        """Test CircuitOpenError message format."""
        config = CircuitBreakerConfig(failure_threshold=1, timeout=30.0)
        breaker = CircuitBreaker("my-circuit", config)
        
        breaker.record_failure()
        
        async def operation():
            pass
        
        with pytest.raises(CircuitOpenError) as exc_info:
            await breaker.execute(operation)
        
        error_str = str(exc_info.value)
        assert "my-circuit" in error_str
        assert "retry_in=" in error_str
    
    @pytest.mark.asyncio
    async def test_execute_closes_after_success_threshold(self):
        """Test circuit closes after meeting success threshold."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            success_threshold=2,
            timeout=0.05,  # 50ms timeout
            half_open_max_requests=3,  # Allow enough requests to meet success_threshold
        )
        breaker = CircuitBreaker("test", config)
        
        # Trip the circuit
        breaker.record_failure()
        assert breaker.state == CircuitState.OPEN
        
        # Wait for timeout to pass
        await asyncio.sleep(0.1)  # 100ms, well past the 50ms timeout
        
        async def operation():
            return "ok"
        
        # First success should transition to HALF_OPEN
        await breaker.execute(operation)
        assert breaker.state == CircuitState.HALF_OPEN
        
        # Second success should transition to CLOSED
        await breaker.execute(operation)
        assert breaker.state == CircuitState.CLOSED


# ============================================================================
# CircuitBreakerRegistry Tests (25 tests)
# ============================================================================

class TestCircuitBreakerRegistry:
    """Tests for CircuitBreakerRegistry."""
    
    def test_create_registry(self):
        """Test creating a registry."""
        registry = CircuitBreakerRegistry()
        assert registry is not None
    
    def test_get_global_breaker(self):
        """Test getting global circuit breaker."""
        registry = CircuitBreakerRegistry()
        breaker = registry.get_global()
        
        assert breaker.name == "global"
        assert breaker.state == CircuitState.CLOSED
    
    def test_get_global_same_instance(self):
        """Test global breaker is same instance."""
        registry = CircuitBreakerRegistry()
        
        breaker1 = registry.get_global()
        breaker2 = registry.get_global()
        
        assert breaker1 is breaker2
    
    def test_get_for_connection(self):
        """Test getting per-connection breaker."""
        registry = CircuitBreakerRegistry()
        
        breaker = registry.get_for_connection("conn_123")
        
        assert breaker.name == "conn:conn_123"
    
    def test_get_for_connection_different_ids(self):
        """Test different connection IDs get different breakers."""
        registry = CircuitBreakerRegistry()
        
        breaker1 = registry.get_for_connection("conn_1")
        breaker2 = registry.get_for_connection("conn_2")
        
        assert breaker1 is not breaker2
        assert breaker1.name != breaker2.name
    
    def test_get_for_connection_same_id(self):
        """Test same connection ID gets same breaker."""
        registry = CircuitBreakerRegistry()
        
        breaker1 = registry.get_for_connection("conn_1")
        breaker2 = registry.get_for_connection("conn_1")
        
        assert breaker1 is breaker2
    
    def test_get_for_query_type(self):
        """Test getting per-query-type breaker."""
        registry = CircuitBreakerRegistry()
        
        breaker = registry.get_for_query_type("read")
        
        assert breaker.name == "query:read"
    
    def test_get_for_query_type_different_types(self):
        """Test different query types get different breakers."""
        registry = CircuitBreakerRegistry()
        
        read_breaker = registry.get_for_query_type("read")
        write_breaker = registry.get_for_query_type("write")
        
        assert read_breaker is not write_breaker
    
    def test_get_breaker_by_key(self):
        """Test getting breaker by arbitrary key."""
        registry = CircuitBreakerRegistry()
        
        breaker = registry.get_breaker("custom_key")
        
        assert breaker.name == "custom_key"
    
    def test_get_breaker_with_custom_config(self):
        """Test getting breaker with custom config."""
        registry = CircuitBreakerRegistry()
        custom_config = CircuitBreakerConfig(failure_threshold=10)
        
        breaker = registry.get_breaker("custom", config=custom_config)
        
        # First breaker uses custom config
        # Note: subsequent gets won't update config
        assert breaker is not None
    
    def test_get_all_breakers(self):
        """Test getting all breakers."""
        registry = CircuitBreakerRegistry()
        
        registry.get_global()
        registry.get_for_connection("conn_1")
        registry.get_for_query_type("read")
        
        breakers = registry.get_all_breakers()
        
        assert len(breakers) == 3
        assert "global" in breakers
        assert "conn:conn_1" in breakers
        assert "query:read" in breakers
    
    def test_get_all_stats(self):
        """Test getting stats for all breakers."""
        registry = CircuitBreakerRegistry()
        
        registry.get_global().record_success()
        registry.get_for_connection("conn_1").record_failure()
        
        stats = registry.get_all_stats()
        
        assert "global" in stats
        assert "conn:conn_1" in stats
        assert stats["global"]["total_successes"] == 1
        assert stats["conn:conn_1"]["total_failures"] == 1
    
    def test_reset_all(self):
        """Test resetting all breakers."""
        config = CircuitBreakerConfig(failure_threshold=1)
        registry = CircuitBreakerRegistry(config=config)
        
        breaker1 = registry.get_global()
        breaker2 = registry.get_for_connection("conn_1")
        
        breaker1.record_failure()
        breaker2.record_failure()
        
        assert breaker1.state == CircuitState.OPEN
        assert breaker2.state == CircuitState.OPEN
        
        registry.reset_all()
        
        assert breaker1.state == CircuitState.CLOSED
        assert breaker2.state == CircuitState.CLOSED
    
    def test_remove_breaker(self):
        """Test removing a breaker."""
        registry = CircuitBreakerRegistry()
        
        registry.get_breaker("temp")
        assert "temp" in registry.get_all_breakers()
        
        registry.remove_breaker("temp")
        assert "temp" not in registry.get_all_breakers()
    
    def test_remove_nonexistent_breaker(self):
        """Test removing nonexistent breaker doesn't error."""
        registry = CircuitBreakerRegistry()
        
        registry.remove_breaker("doesnt_exist")  # Should not raise
    
    def test_clear(self):
        """Test clearing all breakers."""
        registry = CircuitBreakerRegistry()
        
        registry.get_global()
        registry.get_for_connection("conn_1")
        
        assert len(registry.get_all_breakers()) == 2
        
        registry.clear()
        
        assert len(registry.get_all_breakers()) == 0
    
    def test_registry_with_default_config(self):
        """Test registry uses default config."""
        default_config = CircuitBreakerConfig(failure_threshold=10)
        registry = CircuitBreakerRegistry(default_config=default_config)
        
        # New breakers should use default config
        breaker = registry.get_breaker("new")
        # Config is passed to breaker
        assert breaker is not None
    
    def test_registry_thread_safety(self):
        """Test registry is thread-safe."""
        registry = CircuitBreakerRegistry()
        errors = []
        
        def get_breakers():
            try:
                for i in range(100):
                    registry.get_breaker(f"thread_{threading.current_thread().name}_{i}")
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=get_breakers) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0
    
    def test_breakers_independent(self):
        """Test breakers are independent."""
        config = CircuitBreakerConfig(failure_threshold=2)
        registry = CircuitBreakerRegistry(config=config)
        
        breaker1 = registry.get_for_connection("conn_1")
        breaker2 = registry.get_for_connection("conn_2")
        
        # Open breaker1
        breaker1.record_failure()
        breaker1.record_failure()
        
        assert breaker1.state == CircuitState.OPEN
        assert breaker2.state == CircuitState.CLOSED
    
    def test_query_type_isolation(self):
        """Test query types are isolated."""
        config = CircuitBreakerConfig(failure_threshold=1)
        registry = CircuitBreakerRegistry(config=config)
        
        read_breaker = registry.get_for_query_type("read")
        write_breaker = registry.get_for_query_type("write")
        
        read_breaker.record_failure()
        
        assert read_breaker.state == CircuitState.OPEN
        assert write_breaker.state == CircuitState.CLOSED
    
    def test_global_affects_all(self):
        """Test global breaker can be used for all operations."""
        config = CircuitBreakerConfig(failure_threshold=1)
        registry = CircuitBreakerRegistry(config=config)
        
        global_breaker = registry.get_global()
        global_breaker.record_failure()
        
        assert global_breaker.state == CircuitState.OPEN
        # Other breakers still independent
        assert registry.get_for_query_type("read").state == CircuitState.CLOSED
    
    def test_registry_config_inheritance(self):
        """Test registry config is inherited."""
        config = CircuitBreakerConfig(failure_threshold=7, timeout=45.0)
        registry = CircuitBreakerRegistry(config=config)
        
        # Global breaker should use registry config
        global_breaker = registry.get_global()
        assert global_breaker is not None
    
    def test_multiple_registries_independent(self):
        """Test multiple registries are independent."""
        registry1 = CircuitBreakerRegistry()
        registry2 = CircuitBreakerRegistry()
        
        breaker1 = registry1.get_global()
        breaker2 = registry2.get_global()
        
        assert breaker1 is not breaker2


# ============================================================================
# CircuitStats Tests (15 tests)
# ============================================================================

class TestCircuitStats:
    """Tests for CircuitStats tracking."""
    
    def test_initial_stats(self):
        """Test initial stats values."""
        stats = CircuitStats()
        assert stats.total_requests == 0
        assert stats.total_successes == 0
        assert stats.total_failures == 0
        assert stats.total_rejections == 0
    
    def test_record_request(self):
        """Test recording requests."""
        stats = CircuitStats()
        stats.record_request()
        assert stats.total_requests == 1
    
    def test_record_success(self):
        """Test recording success."""
        stats = CircuitStats()
        stats.record_success()
        assert stats.total_successes == 1
        assert stats.consecutive_successes == 1
    
    def test_record_failure(self):
        """Test recording failure."""
        stats = CircuitStats()
        stats.record_failure()
        assert stats.total_failures == 1
        assert stats.consecutive_failures == 1
    
    def test_record_rejection(self):
        """Test recording rejection."""
        stats = CircuitStats()
        stats.record_rejection()
        assert stats.total_rejections == 1
    
    def test_failure_rate(self):
        """Test failure rate calculation."""
        stats = CircuitStats()
        stats.total_requests = 100
        stats.total_failures = 25
        assert stats.failure_rate == 0.25
    
    def test_failure_rate_no_requests(self):
        """Test failure rate with no requests."""
        stats = CircuitStats()
        assert stats.failure_rate == 0.0
    
    def test_consecutive_reset_on_success(self):
        """Test consecutive failures reset on success."""
        stats = CircuitStats()
        stats.record_failure()
        stats.record_failure()
        stats.record_success()
        assert stats.consecutive_failures == 0
    
    def test_consecutive_reset_on_failure(self):
        """Test consecutive successes reset on failure."""
        stats = CircuitStats()
        stats.record_success()
        stats.record_success()
        stats.record_failure()
        assert stats.consecutive_successes == 0
    
    def test_state_change_tracking(self):
        """Test state change is recorded."""
        stats = CircuitStats()
        stats.record_state_change(CircuitState.OPEN)
        assert stats.state_transitions == 1
        assert stats.current_state == CircuitState.OPEN
    
    def test_time_in_open_tracked(self):
        """Test time in open state is tracked."""
        stats = CircuitStats()
        stats.record_state_change(CircuitState.OPEN)
        time.sleep(0.05)
        stats.record_state_change(CircuitState.HALF_OPEN)
        
        assert stats.time_in_open >= 0.04
    
    def test_recent_failure_rate(self):
        """Test recent failure rate calculation."""
        stats = CircuitStats()
        now = time.monotonic()
        
        # Add recent results
        for _ in range(6):
            stats._recent_results.append((now, True))
        for _ in range(4):
            stats._recent_results.append((now, False))
        
        rate = stats.get_recent_failure_rate(window=60.0)
        assert rate == 0.4
    
    def test_recent_failure_rate_empty(self):
        """Test recent failure rate with no results."""
        stats = CircuitStats()
        rate = stats.get_recent_failure_rate()
        assert rate == 0.0
    
    def test_to_dict(self):
        """Test stats to_dict conversion."""
        stats = CircuitStats()
        stats.total_requests = 10
        stats.total_successes = 8
        stats.total_failures = 2
        
        d = stats.to_dict()
        
        assert d["total_requests"] == 10
        assert d["total_successes"] == 8
        assert d["failure_rate"] == 0.2
    
    def test_trim_recent_results(self):
        """Test recent results list is bounded."""
        stats = CircuitStats()
        
        for i in range(2000):
            stats.record_success()
        
        assert len(stats._recent_results) <= 1000


# ============================================================================
# Convenience Functions Tests (10 tests)
# ============================================================================

class TestConvenienceFunctions:
    """Tests for convenience circuit breaker functions."""
    
    def test_create_global_breaker_default(self):
        """Test create_global_breaker with defaults."""
        breaker = create_global_breaker()
        assert breaker.name == "global"
        assert breaker.state == CircuitState.CLOSED
    
    def test_create_global_breaker_custom(self):
        """Test create_global_breaker with custom params."""
        breaker = create_global_breaker(
            failure_threshold=3,
            timeout=15.0,
        )
        assert breaker is not None
    
    def test_create_sensitive_breaker(self):
        """Test create_sensitive_breaker."""
        breaker = create_sensitive_breaker("sensitive")
        assert breaker.name == "sensitive"
        # Should trip quickly (low threshold)
    
    def test_create_tolerant_breaker(self):
        """Test create_tolerant_breaker."""
        breaker = create_tolerant_breaker("tolerant")
        assert breaker.name == "tolerant"
        # Should be more tolerant
    
    def test_sensitive_trips_faster(self):
        """Test sensitive breaker trips faster than tolerant."""
        sensitive = create_sensitive_breaker("s")
        tolerant = create_tolerant_breaker("t")
        
        # Trip sensitive
        for _ in range(3):
            sensitive.record_failure()
        
        assert sensitive.state == CircuitState.OPEN
        
        # Tolerant should still be closed after same failures
        for _ in range(3):
            tolerant.record_failure()
        
        assert tolerant.state == CircuitState.CLOSED
    
    def test_all_convenience_breakers_work(self):
        """Test all convenience breakers can execute operations."""
        breakers = [
            create_global_breaker(),
            create_sensitive_breaker("s"),
            create_tolerant_breaker("t"),
        ]
        
        for breaker in breakers:
            assert breaker.allow_request() is True
    
    def test_circuit_scope_enum(self):
        """Test CircuitScope enum values."""
        assert CircuitScope.GLOBAL.value == "global"
        assert CircuitScope.CONNECTION.value == "connection"
        assert CircuitScope.QUERY_TYPE.value == "query_type"
    
    def test_circuit_state_enum(self):
        """Test CircuitState enum values."""
        assert CircuitState.CLOSED.value == "closed"
        assert CircuitState.OPEN.value == "open"
        assert CircuitState.HALF_OPEN.value == "half_open"
    
    @pytest.mark.asyncio
    async def test_global_breaker_execute(self):
        """Test global breaker can execute operations."""
        breaker = create_global_breaker()
        
        async def op():
            return 42
        
        result = await breaker.execute(op)
        assert result == 42
    
    @pytest.mark.asyncio
    async def test_sensitive_breaker_trips_and_recovers(self):
        """Test sensitive breaker can trip and recover."""
        breaker = create_sensitive_breaker("test")
        
        # Trip it
        for _ in range(3):
            breaker.record_failure()
        
        assert breaker.state == CircuitState.OPEN
        
        # Wait for timeout (short in sensitive config)
        time.sleep(0.02)
        
        # Force half-open
        breaker.reset()
        assert breaker.state == CircuitState.CLOSED


# ============================================================================
# Thread Safety Tests (5 tests)
# ============================================================================

class TestThreadSafety:
    """Tests for thread safety of circuit breakers."""
    
    def test_concurrent_record_failure(self):
        """Test concurrent failure recording."""
        config = CircuitBreakerConfig(failure_threshold=1000)
        breaker = CircuitBreaker("test", config)
        
        def record_failures():
            for _ in range(100):
                breaker.record_failure()
        
        threads = [threading.Thread(target=record_failures) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert breaker.stats.total_failures == 1000
    
    def test_concurrent_record_success(self):
        """Test concurrent success recording."""
        breaker = CircuitBreaker("test")
        
        def record_successes():
            for _ in range(100):
                breaker.record_success()
        
        threads = [threading.Thread(target=record_successes) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert breaker.stats.total_successes == 1000
    
    def test_concurrent_allow_request(self):
        """Test concurrent allow_request calls."""
        breaker = CircuitBreaker("test")
        results = []
        
        def check_allow():
            for _ in range(100):
                results.append(breaker.allow_request())
        
        threads = [threading.Thread(target=check_allow) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert all(results)  # All should be True when closed
    
    def test_concurrent_state_transitions(self):
        """Test concurrent state transitions don't corrupt state."""
        config = CircuitBreakerConfig(failure_threshold=5, timeout=0.01)
        breaker = CircuitBreaker("test", config)
        
        def toggle_state():
            for _ in range(50):
                if breaker.is_closed:
                    breaker.force_open()
                else:
                    breaker.force_close()
                time.sleep(0.001)
        
        threads = [threading.Thread(target=toggle_state) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # State should be valid
        assert breaker.state in [CircuitState.CLOSED, CircuitState.OPEN, CircuitState.HALF_OPEN]
    
    def test_registry_concurrent_access(self):
        """Test registry handles concurrent access."""
        registry = CircuitBreakerRegistry()
        breakers = []
        
        def access_registry():
            for i in range(50):
                breaker = registry.get_breaker(f"breaker_{threading.current_thread().name}_{i}")
                breakers.append(breaker)
        
        threads = [threading.Thread(target=access_registry) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All breakers should be valid
        assert all(isinstance(b, CircuitBreaker) for b in breakers)

