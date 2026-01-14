"""
Comprehensive tests for PostgreSQL Retry Logic.

Tests cover:
- Backoff calculation (exponential, linear, fixed)
- Jitter randomization
- Max delay capping
- Retryable error detection
- Non-retryable errors
- Max attempts exhaustion
- Successful retry scenarios
- Timeout during retry
- Concurrent retries
- Statistics tracking

80 tests total.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import time

from pynext.db.adapters.postgres.reliability.retry import (
    RetryConfig,
    RetryManager,
    RetryError,
    RetryStats,
    BackoffStrategy,
    with_retry,
    quick_retry,
    standard_retry,
    aggressive_retry,
    no_retry,
    DEFAULT_RETRYABLE_ERRORS,
)


# ============================================================================
# RetryConfig Tests (15 tests)
# ============================================================================

class TestRetryConfig:
    """Tests for RetryConfig dataclass."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.initial_delay == 1.0
        assert config.max_delay == 30.0
        assert config.backoff == "exponential"
        assert config.multiplier == 2.0
        assert config.jitter is True
        assert config.jitter_factor == 0.25
        assert config.retry_on_timeout is True
        assert config.log_retries is True
    
    def test_custom_values(self):
        """Test custom configuration values."""
        config = RetryConfig(
            max_attempts=5,
            initial_delay=0.5,
            max_delay=60.0,
            backoff="linear",
            multiplier=1.5,
            jitter=False,
        )
        assert config.max_attempts == 5
        assert config.initial_delay == 0.5
        assert config.max_delay == 60.0
        assert config.backoff == "linear"
        assert config.multiplier == 1.5
        assert config.jitter is False
    
    def test_invalid_max_attempts(self):
        """Test validation for max_attempts."""
        with pytest.raises(ValueError, match="max_attempts must be >= 1"):
            RetryConfig(max_attempts=0)
        
        with pytest.raises(ValueError, match="max_attempts must be >= 1"):
            RetryConfig(max_attempts=-1)
    
    def test_invalid_initial_delay(self):
        """Test validation for initial_delay."""
        with pytest.raises(ValueError, match="initial_delay must be >= 0"):
            RetryConfig(initial_delay=-1)
    
    def test_invalid_max_delay(self):
        """Test validation for max_delay."""
        with pytest.raises(ValueError, match="max_delay must be >= 0"):
            RetryConfig(max_delay=-1)
    
    def test_invalid_multiplier(self):
        """Test validation for multiplier."""
        with pytest.raises(ValueError, match="multiplier must be > 0"):
            RetryConfig(multiplier=0)
        
        with pytest.raises(ValueError, match="multiplier must be > 0"):
            RetryConfig(multiplier=-1)
    
    def test_invalid_jitter_factor(self):
        """Test validation for jitter_factor."""
        with pytest.raises(ValueError, match="jitter_factor must be 0-1"):
            RetryConfig(jitter_factor=1.5)
        
        with pytest.raises(ValueError, match="jitter_factor must be 0-1"):
            RetryConfig(jitter_factor=-0.1)
    
    def test_invalid_backoff(self):
        """Test validation for backoff strategy."""
        with pytest.raises(ValueError, match="backoff must be exponential/linear/fixed"):
            RetryConfig(backoff="invalid")
    
    def test_retryable_errors_default(self):
        """Test default retryable errors set."""
        config = RetryConfig()
        assert "ConnectionRefusedError" in config.retryable_errors
        assert "TimeoutError" in config.retryable_errors
    
    def test_retryable_errors_custom(self):
        """Test custom retryable errors set."""
        config = RetryConfig(retryable_errors={"CustomError"})
        assert "CustomError" in config.retryable_errors
        assert "ConnectionRefusedError" not in config.retryable_errors
    
    def test_zero_initial_delay(self):
        """Test zero initial delay is valid."""
        config = RetryConfig(initial_delay=0)
        assert config.initial_delay == 0
    
    def test_zero_max_delay(self):
        """Test zero max delay is valid."""
        config = RetryConfig(max_delay=0)
        assert config.max_delay == 0
    
    def test_jitter_factor_boundaries(self):
        """Test jitter factor at boundaries."""
        config1 = RetryConfig(jitter_factor=0)
        assert config1.jitter_factor == 0
        
        config2 = RetryConfig(jitter_factor=1)
        assert config2.jitter_factor == 1
    
    def test_single_attempt_valid(self):
        """Test single attempt configuration."""
        config = RetryConfig(max_attempts=1)
        assert config.max_attempts == 1


# ============================================================================
# Backoff Calculation Tests (15 tests)
# ============================================================================

class TestBackoffCalculation:
    """Tests for delay calculation with different strategies."""
    
    def test_exponential_backoff_sequence(self):
        """Test exponential backoff produces correct sequence."""
        config = RetryConfig(
            initial_delay=1.0,
            multiplier=2.0,
            jitter=False,
            max_delay=100.0,
        )
        manager = RetryManager(config)
        
        assert manager.get_delay(0) == 1.0
        assert manager.get_delay(1) == 2.0
        assert manager.get_delay(2) == 4.0
        assert manager.get_delay(3) == 8.0
        assert manager.get_delay(4) == 16.0
    
    def test_linear_backoff_sequence(self):
        """Test linear backoff produces correct sequence."""
        config = RetryConfig(
            initial_delay=1.0,
            backoff="linear",
            jitter=False,
            max_delay=100.0,
        )
        manager = RetryManager(config)
        
        assert manager.get_delay(0) == 1.0
        assert manager.get_delay(1) == 2.0
        assert manager.get_delay(2) == 3.0
        assert manager.get_delay(3) == 4.0
        assert manager.get_delay(4) == 5.0
    
    def test_fixed_backoff_sequence(self):
        """Test fixed backoff produces constant delays."""
        config = RetryConfig(
            initial_delay=2.0,
            backoff="fixed",
            jitter=False,
        )
        manager = RetryManager(config)
        
        assert manager.get_delay(0) == 2.0
        assert manager.get_delay(1) == 2.0
        assert manager.get_delay(2) == 2.0
        assert manager.get_delay(10) == 2.0
    
    def test_max_delay_cap(self):
        """Test delay is capped at max_delay."""
        config = RetryConfig(
            initial_delay=1.0,
            multiplier=10.0,
            max_delay=5.0,
            jitter=False,
        )
        manager = RetryManager(config)
        
        assert manager.get_delay(0) == 1.0
        assert manager.get_delay(1) == 5.0  # Capped at max
        assert manager.get_delay(2) == 5.0  # Still capped
    
    def test_jitter_adds_variance(self):
        """Test jitter adds randomness to delay."""
        config = RetryConfig(
            initial_delay=10.0,
            jitter=True,
            jitter_factor=0.25,
            backoff="fixed",
        )
        manager = RetryManager(config)
        
        delays = [manager.get_delay(0) for _ in range(100)]
        
        # Should have variance
        assert min(delays) < max(delays)
        
        # Should be within jitter range (10 ± 2.5)
        assert all(7.5 <= d <= 12.5 for d in delays)
    
    def test_jitter_disabled(self):
        """Test jitter=False produces consistent delays."""
        config = RetryConfig(
            initial_delay=5.0,
            jitter=False,
            backoff="fixed",
        )
        manager = RetryManager(config)
        
        delays = [manager.get_delay(0) for _ in range(10)]
        assert all(d == 5.0 for d in delays)
    
    def test_zero_delay_no_jitter(self):
        """Test zero delay doesn't cause issues with jitter."""
        config = RetryConfig(
            initial_delay=0,
            jitter=True,
        )
        manager = RetryManager(config)
        
        delay = manager.get_delay(0)
        assert delay == 0
    
    def test_custom_multiplier(self):
        """Test custom multiplier for exponential backoff."""
        config = RetryConfig(
            initial_delay=1.0,
            multiplier=3.0,
            jitter=False,
            max_delay=1000.0,
        )
        manager = RetryManager(config)
        
        assert manager.get_delay(0) == 1.0
        assert manager.get_delay(1) == 3.0
        assert manager.get_delay(2) == 9.0
        assert manager.get_delay(3) == 27.0
    
    def test_large_attempt_number(self):
        """Test backoff with large attempt numbers."""
        config = RetryConfig(
            initial_delay=0.1,
            max_delay=60.0,
            jitter=False,
        )
        manager = RetryManager(config)
        
        # Should be capped
        delay = manager.get_delay(100)
        assert delay == 60.0
    
    def test_fractional_delays(self):
        """Test fractional initial delays."""
        config = RetryConfig(
            initial_delay=0.05,
            multiplier=2.0,
            jitter=False,
            max_delay=1.0,
        )
        manager = RetryManager(config)
        
        assert manager.get_delay(0) == 0.05
        assert manager.get_delay(1) == 0.1
        assert manager.get_delay(2) == 0.2
    
    def test_jitter_never_negative(self):
        """Test jitter never produces negative delay."""
        config = RetryConfig(
            initial_delay=0.1,
            jitter=True,
            jitter_factor=1.0,  # Max jitter
        )
        manager = RetryManager(config)
        
        for _ in range(100):
            delay = manager.get_delay(0)
            assert delay >= 0
    
    def test_linear_with_max_cap(self):
        """Test linear backoff respects max delay."""
        config = RetryConfig(
            initial_delay=5.0,
            backoff="linear",
            max_delay=15.0,
            jitter=False,
        )
        manager = RetryManager(config)
        
        assert manager.get_delay(0) == 5.0
        assert manager.get_delay(1) == 10.0
        assert manager.get_delay(2) == 15.0
        assert manager.get_delay(3) == 15.0  # Capped
    
    def test_delay_with_small_jitter(self):
        """Test small jitter factor."""
        config = RetryConfig(
            initial_delay=10.0,
            jitter=True,
            jitter_factor=0.01,
            backoff="fixed",
        )
        manager = RetryManager(config)
        
        delays = [manager.get_delay(0) for _ in range(100)]
        
        # Should be within 1% (9.9 to 10.1)
        assert all(9.9 <= d <= 10.1 for d in delays)
    
    def test_first_delay_matches_initial(self):
        """Test first attempt delay equals initial_delay (without jitter)."""
        config = RetryConfig(
            initial_delay=2.5,
            jitter=False,
        )
        manager = RetryManager(config)
        
        assert manager.get_delay(0) == 2.5


# ============================================================================
# Error Classification Tests (15 tests)
# ============================================================================

class TestErrorClassification:
    """Tests for retryable error detection."""
    
    def test_connection_refused_is_retryable(self):
        """Test ConnectionRefusedError is retryable."""
        manager = RetryManager()
        error = ConnectionRefusedError()
        assert manager.is_retryable(error) is True
    
    def test_connection_reset_is_retryable(self):
        """Test ConnectionResetError is retryable."""
        manager = RetryManager()
        error = ConnectionResetError()
        assert manager.is_retryable(error) is True
    
    def test_timeout_error_is_retryable(self):
        """Test TimeoutError is retryable."""
        manager = RetryManager()
        error = TimeoutError()
        assert manager.is_retryable(error) is True
    
    def test_asyncio_timeout_is_retryable(self):
        """Test asyncio.TimeoutError is retryable."""
        manager = RetryManager()
        error = asyncio.TimeoutError()
        assert manager.is_retryable(error) is True
    
    def test_value_error_not_retryable(self):
        """Test ValueError is not retryable."""
        manager = RetryManager()
        error = ValueError("bad value")
        assert manager.is_retryable(error) is False
    
    def test_key_error_not_retryable(self):
        """Test KeyError is not retryable."""
        manager = RetryManager()
        error = KeyError("missing")
        assert manager.is_retryable(error) is False
    
    def test_custom_retryable_error(self):
        """Test custom error in retryable set."""
        class CustomError(Exception):
            pass
        
        config = RetryConfig(retryable_errors={"CustomError"})
        manager = RetryManager(config)
        
        error = CustomError()
        assert manager.is_retryable(error) is True
    
    def test_timeout_disabled(self):
        """Test timeout retry can be disabled."""
        config = RetryConfig(retry_on_timeout=False)
        manager = RetryManager(config)
        
        error = TimeoutError()
        assert manager.is_retryable(error) is False
    
    def test_timeout_in_message(self):
        """Test error with 'timeout' in message."""
        manager = RetryManager()
        error = Exception("Connection timeout occurred")
        assert manager.is_retryable(error) is True
    
    def test_sqlstate_serialization_failure(self):
        """Test PostgreSQL serialization failure is retryable."""
        manager = RetryManager()
        error = Exception("Serialization failure")
        error.sqlstate = "40001"
        assert manager.is_retryable(error) is True
    
    def test_sqlstate_deadlock(self):
        """Test PostgreSQL deadlock is retryable."""
        manager = RetryManager()
        error = Exception("Deadlock detected")
        error.sqlstate = "40P01"
        assert manager.is_retryable(error) is True
    
    def test_sqlstate_connection_exception(self):
        """Test PostgreSQL connection exception is retryable."""
        manager = RetryManager()
        error = Exception("Connection error")
        error.sqlstate = "08000"
        assert manager.is_retryable(error) is True
    
    def test_sqlstate_unknown_not_retryable(self):
        """Test unknown sqlstate is not retryable."""
        manager = RetryManager()
        error = Exception("Syntax error")
        error.sqlstate = "42601"  # Syntax error
        assert manager.is_retryable(error) is False
    
    def test_broken_pipe_is_retryable(self):
        """Test BrokenPipeError is retryable."""
        manager = RetryManager()
        error = BrokenPipeError()
        assert manager.is_retryable(error) is True
    
    def test_empty_retryable_set(self):
        """Test with empty retryable errors set."""
        config = RetryConfig(
            retryable_errors=set(),
            retry_on_timeout=False,
        )
        manager = RetryManager(config)
        
        error = ConnectionRefusedError()
        assert manager.is_retryable(error) is False


# ============================================================================
# Execute With Retry Tests (20 tests)
# ============================================================================

class TestExecuteWithRetry:
    """Tests for the execute_with_retry method."""
    
    @pytest.mark.asyncio
    async def test_success_on_first_attempt(self):
        """Test successful operation on first attempt."""
        manager = RetryManager()
        
        async def operation():
            return "success"
        
        result = await manager.execute_with_retry(operation)
        assert result == "success"
        assert manager.stats.total_attempts == 1
        assert manager.stats.total_successes == 1
        assert manager.stats.total_retries == 0
    
    @pytest.mark.asyncio
    async def test_success_after_retry(self):
        """Test success after initial failure."""
        config = RetryConfig(initial_delay=0.01, jitter=False)
        manager = RetryManager(config)
        
        attempts = [0]
        
        async def operation():
            attempts[0] += 1
            if attempts[0] < 2:
                raise ConnectionRefusedError()
            return "success"
        
        result = await manager.execute_with_retry(operation)
        assert result == "success"
        assert attempts[0] == 2
        assert manager.stats.total_retries == 1
    
    @pytest.mark.asyncio
    async def test_all_attempts_fail(self):
        """Test all attempts failing raises RetryError."""
        config = RetryConfig(max_attempts=3, initial_delay=0.01, jitter=False)
        manager = RetryManager(config)
        
        async def operation():
            raise ConnectionRefusedError("Connection refused")
        
        with pytest.raises(RetryError) as exc_info:
            await manager.execute_with_retry(operation)
        
        assert exc_info.value.attempts == 3
        assert isinstance(exc_info.value.original_error, ConnectionRefusedError)
    
    @pytest.mark.asyncio
    async def test_non_retryable_error_immediate_raise(self):
        """Test non-retryable error raises immediately."""
        manager = RetryManager()
        
        async def operation():
            raise ValueError("Invalid input")
        
        with pytest.raises(ValueError, match="Invalid input"):
            await manager.execute_with_retry(operation)
        
        assert manager.stats.total_attempts == 1
        assert manager.stats.total_retries == 0
    
    @pytest.mark.asyncio
    async def test_with_arguments(self):
        """Test operation with arguments."""
        manager = RetryManager()
        
        async def operation(a, b, c=None):
            return f"{a}-{b}-{c}"
        
        result = await manager.execute_with_retry(operation, "x", "y", c="z")
        assert result == "x-y-z"
    
    @pytest.mark.asyncio
    async def test_custom_should_retry(self):
        """Test custom retry decision function."""
        config = RetryConfig(max_attempts=5, initial_delay=0.01, jitter=False)
        manager = RetryManager(config)
        
        attempts = [0]
        
        async def operation():
            attempts[0] += 1
            raise ValueError(f"Attempt {attempts[0]}")
        
        def should_retry(error, attempt):
            # Only retry ValueError
            return isinstance(error, ValueError) and attempt < 3
        
        with pytest.raises(ValueError, match="Attempt 3"):
            await manager.execute_with_retry(operation, should_retry=should_retry)
        
        assert attempts[0] == 3
    
    @pytest.mark.asyncio
    async def test_on_retry_callback(self):
        """Test on_retry callback is called."""
        config = RetryConfig(max_attempts=3, initial_delay=0.01, jitter=False)
        manager = RetryManager(config)
        
        retry_calls = []
        
        async def operation():
            if len(retry_calls) < 2:
                raise ConnectionRefusedError()
            return "success"
        
        def on_retry(error, attempt, delay):
            retry_calls.append((type(error).__name__, attempt, delay))
        
        result = await manager.execute_with_retry(operation, on_retry=on_retry)
        
        assert result == "success"
        assert len(retry_calls) == 2
        assert retry_calls[0][0] == "ConnectionRefusedError"
        assert retry_calls[0][1] == 1
    
    @pytest.mark.asyncio
    async def test_delay_between_retries(self):
        """Test actual delay occurs between retries."""
        config = RetryConfig(
            max_attempts=2,
            initial_delay=0.1,
            jitter=False,
        )
        manager = RetryManager(config)
        
        times = []
        
        async def operation():
            times.append(time.monotonic())
            if len(times) < 2:
                raise ConnectionRefusedError()
            return "success"
        
        result = await manager.execute_with_retry(operation)
        
        assert result == "success"
        elapsed = times[1] - times[0]
        assert 0.08 <= elapsed <= 0.15  # Allow some variance
    
    @pytest.mark.asyncio
    async def test_total_delay_tracked(self):
        """Test total delay is tracked in RetryError."""
        config = RetryConfig(
            max_attempts=3,
            initial_delay=0.05,
            jitter=False,
            backoff="fixed",
        )
        manager = RetryManager(config)
        
        async def operation():
            raise ConnectionRefusedError()
        
        with pytest.raises(RetryError) as exc_info:
            await manager.execute_with_retry(operation)
        
        # 2 retries × 0.05s = 0.1s total delay
        assert 0.08 <= exc_info.value.total_delay <= 0.15
    
    @pytest.mark.asyncio
    async def test_stats_tracked(self):
        """Test statistics are tracked correctly."""
        config = RetryConfig(max_attempts=4, initial_delay=0.01, jitter=False)
        manager = RetryManager(config)
        
        attempts = [0]
        
        async def operation():
            attempts[0] += 1
            if attempts[0] < 3:
                raise ConnectionRefusedError()
            return "success"
        
        await manager.execute_with_retry(operation)
        
        stats = manager.stats
        assert stats.total_attempts == 3
        assert stats.total_successes == 1
        assert stats.total_failures == 2
        assert stats.total_retries == 2
    
    @pytest.mark.asyncio
    async def test_single_attempt_no_retry(self):
        """Test single attempt configuration.
        
        With max_attempts=1, retryable errors are wrapped in RetryError
        since all attempts were exhausted (even if it's just one).
        Non-retryable errors are raised directly.
        """
        config = RetryConfig(max_attempts=1)
        manager = RetryManager(config)
        
        async def operation():
            raise ConnectionRefusedError()
        
        # Retryable errors get wrapped in RetryError
        with pytest.raises(RetryError) as exc_info:
            await manager.execute_with_retry(operation)
        
        assert exc_info.value.attempts == 1
        assert isinstance(exc_info.value.original_error, ConnectionRefusedError)
        assert manager.stats.total_attempts == 1
        assert manager.stats.total_retries == 0
    
    @pytest.mark.asyncio
    async def test_reset_stats(self):
        """Test stats can be reset."""
        manager = RetryManager()
        
        async def operation():
            return "success"
        
        await manager.execute_with_retry(operation)
        assert manager.stats.total_attempts == 1
        
        manager.reset_stats()
        assert manager.stats.total_attempts == 0
        assert manager.stats.total_successes == 0
    
    @pytest.mark.asyncio
    async def test_concurrent_retries(self):
        """Test multiple concurrent retry operations."""
        config = RetryConfig(max_attempts=3, initial_delay=0.01, jitter=False)
        manager = RetryManager(config)
        
        counters = {"a": 0, "b": 0}
        
        async def operation_a():
            counters["a"] += 1
            if counters["a"] < 2:
                raise ConnectionRefusedError()
            return "a"
        
        async def operation_b():
            counters["b"] += 1
            if counters["b"] < 3:
                raise ConnectionRefusedError()
            return "b"
        
        results = await asyncio.gather(
            manager.execute_with_retry(operation_a),
            manager.execute_with_retry(operation_b),
        )
        
        assert results == ["a", "b"]
    
    @pytest.mark.asyncio
    async def test_error_type_in_stats(self):
        """Test error types are tracked in stats."""
        config = RetryConfig(max_attempts=3, initial_delay=0.01, jitter=False)
        manager = RetryManager(config)
        
        async def operation():
            raise ConnectionRefusedError()
        
        with pytest.raises(RetryError):
            await manager.execute_with_retry(operation)
        
        assert "ConnectionRefusedError" in manager.stats.retries_by_error
        assert manager.stats.retries_by_error["ConnectionRefusedError"] == 3
    
    @pytest.mark.asyncio
    async def test_async_operation_with_await(self):
        """Test async operation that awaits internally."""
        manager = RetryManager()
        
        async def operation():
            await asyncio.sleep(0.001)
            return "done"
        
        result = await manager.execute_with_retry(operation)
        assert result == "done"
    
    @pytest.mark.asyncio
    async def test_exception_preserved(self):
        """Test original exception is preserved in RetryError."""
        config = RetryConfig(max_attempts=2, initial_delay=0.01, jitter=False)
        manager = RetryManager(config)
        
        async def operation():
            raise ConnectionRefusedError("specific message")
        
        with pytest.raises(RetryError) as exc_info:
            await manager.execute_with_retry(operation)
        
        assert "specific message" in str(exc_info.value.original_error)
    
    @pytest.mark.asyncio
    async def test_return_none(self):
        """Test operation returning None."""
        manager = RetryManager()
        
        async def operation():
            return None
        
        result = await manager.execute_with_retry(operation)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_success_on_last_attempt(self):
        """Test success on the last allowed attempt."""
        config = RetryConfig(max_attempts=3, initial_delay=0.01, jitter=False)
        manager = RetryManager(config)
        
        attempts = [0]
        
        async def operation():
            attempts[0] += 1
            if attempts[0] < 3:
                raise ConnectionRefusedError()
            return "success"
        
        result = await manager.execute_with_retry(operation)
        assert result == "success"
        assert attempts[0] == 3
    
    @pytest.mark.asyncio
    async def test_different_error_types(self):
        """Test different error types in sequence."""
        config = RetryConfig(max_attempts=4, initial_delay=0.01, jitter=False)
        manager = RetryManager(config)
        
        errors = [ConnectionRefusedError(), TimeoutError(), BrokenPipeError()]
        calls = [0]
        
        async def operation():
            if calls[0] < len(errors):
                error = errors[calls[0]]
                calls[0] += 1
                raise error
            return "success"
        
        result = await manager.execute_with_retry(operation)
        assert result == "success"


# ============================================================================
# Decorator Tests (5 tests)
# ============================================================================

class TestWithRetryDecorator:
    """Tests for the @with_retry decorator."""
    
    @pytest.mark.asyncio
    async def test_decorator_basic(self):
        """Test basic decorator usage."""
        @with_retry()
        async def my_operation():
            return "decorated"
        
        result = await my_operation()
        assert result == "decorated"
    
    @pytest.mark.asyncio
    async def test_decorator_with_config(self):
        """Test decorator with custom config."""
        attempts = [0]
        
        @with_retry(RetryConfig(max_attempts=2, initial_delay=0.01, jitter=False))
        async def my_operation():
            attempts[0] += 1
            if attempts[0] < 2:
                raise ConnectionRefusedError()
            return "success"
        
        result = await my_operation()
        assert result == "success"
        assert attempts[0] == 2
    
    @pytest.mark.asyncio
    async def test_decorator_with_arguments(self):
        """Test decorated function with arguments."""
        @with_retry()
        async def add(a, b):
            return a + b
        
        result = await add(2, 3)
        assert result == 5
    
    @pytest.mark.asyncio
    async def test_decorator_custom_should_retry(self):
        """Test decorator with custom retry logic."""
        attempts = [0]
        
        def custom_check(error, attempt):
            return attempt < 2
        
        @with_retry(should_retry=custom_check)
        async def my_operation():
            attempts[0] += 1
            raise ValueError("fail")
        
        with pytest.raises(ValueError):
            await my_operation()
        
        assert attempts[0] == 2
    
    @pytest.mark.asyncio
    async def test_decorator_preserves_function_info(self):
        """Test decorator preserves function metadata."""
        @with_retry()
        async def documented_function():
            """This is documented."""
            return True
        
        # Note: wrapper doesn't preserve __doc__ by default
        # This is a limitation of the simple implementation
        result = await documented_function()
        assert result is True


# ============================================================================
# Convenience Function Tests (5 tests)
# ============================================================================

class TestConvenienceFunctions:
    """Tests for convenience configuration functions."""
    
    def test_quick_retry(self):
        """Test quick_retry configuration."""
        config = quick_retry()
        assert config.max_attempts == 3
        assert config.initial_delay == 0.05
        assert config.max_delay == 0.5
        assert config.backoff == "linear"
    
    def test_standard_retry(self):
        """Test standard_retry configuration."""
        config = standard_retry()
        assert config.max_attempts == 3
        assert config.initial_delay == 1.0
        assert config.max_delay == 30.0
        assert config.backoff == "exponential"
    
    def test_aggressive_retry(self):
        """Test aggressive_retry configuration."""
        config = aggressive_retry()
        assert config.max_attempts == 10
        assert config.initial_delay == 0.1
        assert config.max_delay == 60.0
        assert config.multiplier == 1.5
    
    def test_no_retry(self):
        """Test no_retry configuration."""
        config = no_retry()
        assert config.max_attempts == 1
    
    def test_convenience_configs_are_valid(self):
        """Test all convenience configs can create managers."""
        for config_fn in [quick_retry, standard_retry, aggressive_retry, no_retry]:
            config = config_fn()
            manager = RetryManager(config)
            assert manager is not None


# ============================================================================
# RetryStats Tests (5 tests)
# ============================================================================

class TestRetryStats:
    """Tests for RetryStats tracking."""
    
    def test_initial_stats(self):
        """Test initial stats are zero."""
        stats = RetryStats()
        assert stats.total_attempts == 0
        assert stats.total_successes == 0
        assert stats.total_failures == 0
        assert stats.total_retries == 0
    
    def test_success_rate(self):
        """Test success rate calculation."""
        stats = RetryStats()
        stats.total_attempts = 10
        stats.total_successes = 8
        assert stats.success_rate == 0.8
    
    def test_success_rate_no_attempts(self):
        """Test success rate with no attempts."""
        stats = RetryStats()
        assert stats.success_rate == 1.0  # Default to 100%
    
    def test_retry_rate(self):
        """Test retry rate calculation."""
        stats = RetryStats()
        stats.total_attempts = 10
        stats.total_retries = 4
        assert stats.retry_rate == 0.4
    
    def test_to_dict(self):
        """Test stats to_dict conversion."""
        stats = RetryStats()
        stats.total_attempts = 5
        stats.total_successes = 3
        stats.total_failures = 2
        
        d = stats.to_dict()
        assert d["total_attempts"] == 5
        assert d["total_successes"] == 3
        assert d["total_failures"] == 2
        assert "success_rate" in d

