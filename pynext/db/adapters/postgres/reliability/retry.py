"""
PostgreSQL Retry Logic with Exponential Backoff.

This module provides intelligent retry logic for database operations,
implementing exponential backoff with jitter for optimal retry behavior.

Why Retry Logic Matters:
- Transient failures (network blips, connection drops) are common
- Without retry, a single failure = user-facing error
- With retry, transient failures are invisible to users

How It Works:

1. Operation fails
2. Check if error is retryable (connection errors, timeouts)
3. Calculate delay: initial_delay * (multiplier ^ attempt)
4. Add jitter to prevent thundering herd
5. Wait, then retry
6. Repeat until success or max_attempts

AI-Friendly Design:
- Clear configuration with sensible defaults
- Explicit error classification
- Comprehensive logging
- Easy to extend with custom retry logic

Example:
    # Simple usage
    retry = RetryManager()
    result = await retry.execute_with_retry(my_async_operation)
    
    # Custom configuration
    retry = RetryManager(RetryConfig(
        max_attempts=5,
        initial_delay=0.5,
        backoff="exponential",
    ))
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, List, Optional, Set, Type, TypeVar, Union

logger = logging.getLogger("pynext.db.postgres.retry")

T = TypeVar("T")


class BackoffStrategy(Enum):
    """Backoff strategy for retries.
    
    EXPONENTIAL: delay = initial * (multiplier ^ attempt)
                 Best for: Most cases. Prevents overwhelming a recovering service.
    
    LINEAR: delay = initial * attempt
            Best for: When you want predictable, steady backoff.
    
    FIXED: delay = initial (constant)
           Best for: When timing is critical and you want consistent delays.
    """
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIXED = "fixed"


# Default retryable errors - these are typically transient
DEFAULT_RETRYABLE_ERRORS: Set[str] = {
    # Connection errors
    "ConnectionRefusedError",
    "ConnectionResetError",
    "ConnectionAbortedError",
    "BrokenPipeError",
    
    # asyncpg errors
    "InterfaceError",
    "ConnectionDoesNotExistError",
    "InterfaceWarning",
    "CannotConnectNowError",
    
    # Timeout errors
    "TimeoutError",
    "asyncio.TimeoutError",
    
    # PostgreSQL transient errors
    "SerializationFailure",  # 40001
    "DeadlockDetected",      # 40P01
    "LockNotAvailable",      # 55P03
    "TooManyConnections",    # 53300
}


@dataclass
class RetryConfig:
    """Configuration for retry behavior.
    
    Attributes:
        max_attempts: Maximum number of attempts (including initial).
                     Default: 3 (initial + 2 retries)
        initial_delay: Initial delay between retries in seconds.
                      Default: 1.0
        max_delay: Maximum delay between retries in seconds.
                  Default: 30.0 (prevents excessively long waits)
        backoff: Backoff strategy ("exponential", "linear", "fixed").
                Default: "exponential"
        multiplier: Multiplier for exponential backoff.
                   Default: 2.0 (1s, 2s, 4s, 8s...)
        jitter: Add random jitter to prevent thundering herd.
               Default: True
        jitter_factor: Maximum jitter as fraction of delay.
                      Default: 0.25 (±25% of delay)
        retryable_errors: Error types that should trigger retry.
                         Default: common transient errors
        retry_on_timeout: Whether to retry on timeout errors.
                         Default: True
        log_retries: Whether to log retry attempts.
                    Default: True
    
    Example:
        # Conservative retry (production)
        config = RetryConfig(
            max_attempts=3,
            initial_delay=1.0,
            max_delay=30.0,
            backoff="exponential",
        )
        
        # Aggressive retry (background jobs)
        config = RetryConfig(
            max_attempts=10,
            initial_delay=0.1,
            max_delay=60.0,
            backoff="exponential",
            multiplier=1.5,
        )
        
        # Fast retry (real-time)
        config = RetryConfig(
            max_attempts=3,
            initial_delay=0.05,
            max_delay=0.5,
            backoff="linear",
        )
    """
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 30.0
    backoff: str = "exponential"
    multiplier: float = 2.0
    jitter: bool = True
    jitter_factor: float = 0.25
    retryable_errors: Set[str] = field(default_factory=lambda: DEFAULT_RETRYABLE_ERRORS.copy())
    retry_on_timeout: bool = True
    log_retries: bool = True
    
    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.max_attempts < 1:
            raise ValueError(f"max_attempts must be >= 1, got {self.max_attempts}")
        if self.initial_delay < 0:
            raise ValueError(f"initial_delay must be >= 0, got {self.initial_delay}")
        if self.max_delay < 0:
            raise ValueError(f"max_delay must be >= 0, got {self.max_delay}")
        if self.multiplier <= 0:
            raise ValueError(f"multiplier must be > 0, got {self.multiplier}")
        if not 0 <= self.jitter_factor <= 1:
            raise ValueError(f"jitter_factor must be 0-1, got {self.jitter_factor}")
        if self.backoff not in ("exponential", "linear", "fixed"):
            raise ValueError(f"backoff must be exponential/linear/fixed, got {self.backoff}")


@dataclass
class RetryStats:
    """Statistics for retry operations.
    
    Useful for monitoring retry behavior in production.
    """
    total_attempts: int = 0
    total_retries: int = 0
    total_successes: int = 0
    total_failures: int = 0
    total_delay_ms: float = 0.0
    retries_by_error: dict = field(default_factory=dict)
    
    @property
    def success_rate(self) -> float:
        """Success rate as a fraction (0-1)."""
        if self.total_attempts == 0:
            return 1.0
        return self.total_successes / self.total_attempts
    
    @property
    def retry_rate(self) -> float:
        """Fraction of attempts that were retries."""
        if self.total_attempts == 0:
            return 0.0
        return self.total_retries / self.total_attempts
    
    @property
    def avg_retries_per_success(self) -> float:
        """Average retries needed for each success."""
        if self.total_successes == 0:
            return 0.0
        return self.total_retries / self.total_successes
    
    def record_attempt(self, is_retry: bool = False) -> None:
        """Record an attempt."""
        self.total_attempts += 1
        if is_retry:
            self.total_retries += 1
    
    def record_success(self) -> None:
        """Record a successful operation."""
        self.total_successes += 1
    
    def record_failure(self, error: Exception) -> None:
        """Record a failed operation."""
        self.total_failures += 1
        error_name = type(error).__name__
        self.retries_by_error[error_name] = self.retries_by_error.get(error_name, 0) + 1
    
    def record_delay(self, delay_ms: float) -> None:
        """Record delay time."""
        self.total_delay_ms += delay_ms
    
    def to_dict(self) -> dict:
        """Convert to dictionary for logging/metrics."""
        return {
            "total_attempts": self.total_attempts,
            "total_retries": self.total_retries,
            "total_successes": self.total_successes,
            "total_failures": self.total_failures,
            "success_rate": self.success_rate,
            "retry_rate": self.retry_rate,
            "avg_retries_per_success": self.avg_retries_per_success,
            "total_delay_ms": self.total_delay_ms,
            "retries_by_error": self.retries_by_error,
        }


class RetryError(Exception):
    """Raised when all retry attempts fail.
    
    Attributes:
        original_error: The last error that caused failure
        attempts: Number of attempts made
        total_delay: Total time spent waiting between retries
    """
    
    def __init__(
        self,
        message: str,
        original_error: Exception,
        attempts: int,
        total_delay: float,
    ):
        super().__init__(message)
        self.original_error = original_error
        self.attempts = attempts
        self.total_delay = total_delay
    
    def __str__(self) -> str:
        return (
            f"RetryError: {self.args[0]} "
            f"(attempts={self.attempts}, total_delay={self.total_delay:.2f}s, "
            f"last_error={type(self.original_error).__name__}: {self.original_error})"
        )


class RetryManager:
    """Manages retry logic with configurable backoff.
    
    This class handles retrying failed operations with intelligent backoff,
    jitter, and error classification.
    
    Basic Usage:
        retry = RetryManager()
        result = await retry.execute_with_retry(async_operation)
    
    With Configuration:
        config = RetryConfig(max_attempts=5, backoff="exponential")
        retry = RetryManager(config)
        result = await retry.execute_with_retry(async_operation)
    
    With Arguments:
        result = await retry.execute_with_retry(
            fetch_user,
            user_id,
            include_posts=True,
        )
    
    Custom Retry Decision:
        def should_retry(error, attempt):
            if isinstance(error, RateLimitError):
                return attempt < 10  # More retries for rate limits
            return attempt < 3
        
        retry = RetryManager()
        result = await retry.execute_with_retry(
            operation,
            should_retry=should_retry,
        )
    """
    
    def __init__(self, config: Optional[RetryConfig] = None):
        """Initialize the retry manager.
        
        Args:
            config: Retry configuration. Uses defaults if not provided.
        """
        self._config = config or RetryConfig()
        self._stats = RetryStats()
    
    @property
    def config(self) -> RetryConfig:
        """Get the retry configuration."""
        return self._config
    
    @property
    def stats(self) -> RetryStats:
        """Get retry statistics."""
        return self._stats
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt number.
        
        Args:
            attempt: The attempt number (0-based, 0 = first retry)
        
        Returns:
            Delay in seconds before the retry
        
        Example:
            # With defaults (exponential, multiplier=2, initial=1s)
            get_delay(0)  # 1.0s
            get_delay(1)  # 2.0s
            get_delay(2)  # 4.0s
            get_delay(3)  # 8.0s
            get_delay(4)  # 16.0s
            get_delay(5)  # 30.0s (capped at max_delay)
        """
        config = self._config
        
        # Calculate base delay based on strategy
        if config.backoff == "exponential":
            delay = config.initial_delay * (config.multiplier ** attempt)
        elif config.backoff == "linear":
            delay = config.initial_delay * (attempt + 1)
        else:  # fixed
            delay = config.initial_delay
        
        # Cap at max delay
        delay = min(delay, config.max_delay)
        
        # Add jitter if enabled
        if config.jitter and delay > 0:
            jitter_range = delay * config.jitter_factor
            jitter = random.uniform(-jitter_range, jitter_range)
            delay = max(0, delay + jitter)
        
        return delay
    
    def is_retryable(self, error: Exception) -> bool:
        """Check if an error should trigger a retry.
        
        Args:
            error: The exception that occurred
        
        Returns:
            True if the error is retryable
        
        An error is retryable if:
        1. It's a timeout and retry_on_timeout is True
        2. Its class name is in retryable_errors (excluding timeouts if disabled)
        3. It has a PostgreSQL error code that's transient
        """
        config = self._config
        error_name = type(error).__name__
        
        # Check for timeout errors first - this takes precedence
        is_timeout = isinstance(error, (asyncio.TimeoutError, TimeoutError))
        if is_timeout:
            return config.retry_on_timeout
        
        # Check for timeout in message
        if "timeout" in str(error).lower():
            return config.retry_on_timeout
        
        # Check if error type is in retryable set (but not timeouts already handled)
        if error_name in config.retryable_errors:
            # Skip TimeoutError if retry_on_timeout is False
            if error_name in ("TimeoutError", "asyncio.TimeoutError") and not config.retry_on_timeout:
                return False
            return True
        
        # Check for PostgreSQL error codes (if available)
        if hasattr(error, "sqlstate"):
            sqlstate = getattr(error, "sqlstate", "")
            # Transient error codes
            transient_codes = {
                "40001",  # serialization_failure
                "40P01",  # deadlock_detected
                "55P03",  # lock_not_available
                "53300",  # too_many_connections
                "57P03",  # cannot_connect_now
                "08000",  # connection_exception
                "08003",  # connection_does_not_exist
                "08006",  # connection_failure
            }
            if sqlstate in transient_codes:
                return True
        
        return False
    
    def should_retry(
        self,
        error: Exception,
        attempt: int,
        custom_check: Optional[Callable[[Exception, int], bool]] = None,
    ) -> bool:
        """Determine if we should retry after an error.
        
        Args:
            error: The exception that occurred
            attempt: Current attempt number (1-based)
            custom_check: Optional custom retry decision function
        
        Returns:
            True if we should retry
        """
        # Check attempt limit
        if attempt >= self._config.max_attempts:
            return False
        
        # Use custom check if provided
        if custom_check is not None:
            return custom_check(error, attempt)
        
        # Use default retryable check
        return self.is_retryable(error)
    
    async def execute_with_retry(
        self,
        operation: Callable[..., Any],
        *args: Any,
        should_retry: Optional[Callable[[Exception, int], bool]] = None,
        on_retry: Optional[Callable[[Exception, int, float], None]] = None,
        **kwargs: Any,
    ) -> Any:
        """Execute an operation with retry logic.
        
        Args:
            operation: Async function to execute
            *args: Positional arguments for the operation
            should_retry: Custom retry decision function
            on_retry: Callback called before each retry
            **kwargs: Keyword arguments for the operation
        
        Returns:
            The result of the operation
        
        Raises:
            RetryError: If all attempts fail
        
        Example:
            async def fetch_user(user_id: int) -> dict:
                async with db.acquire() as conn:
                    return await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
            
            retry = RetryManager()
            user = await retry.execute_with_retry(fetch_user, 123)
        """
        config = self._config
        last_error: Optional[Exception] = None
        total_delay = 0.0
        
        for attempt in range(1, config.max_attempts + 1):
            self._stats.record_attempt(is_retry=(attempt > 1))
            
            try:
                result = await operation(*args, **kwargs)
                self._stats.record_success()
                
                if attempt > 1 and config.log_retries:
                    logger.info(
                        f"Operation succeeded after {attempt} attempts "
                        f"(total_delay={total_delay:.2f}s)"
                    )
                
                return result
                
            except Exception as e:
                last_error = e
                self._stats.record_failure(e)
                
                # Check if this is the last attempt
                if attempt >= config.max_attempts:
                    # All attempts exhausted - wrap in RetryError if it was a retryable error
                    if self.is_retryable(e) or (should_retry is not None and should_retry(e, attempt)):
                        raise RetryError(
                            f"All {config.max_attempts} attempts failed",
                            original_error=last_error,
                            attempts=config.max_attempts,
                            total_delay=total_delay,
                        )
                    # Non-retryable error on last attempt - raise as-is
                    if config.log_retries:
                        logger.warning(
                            f"Operation failed (non-retryable): {type(e).__name__}: {e}"
                        )
                    raise
                
                # Check if we should retry
                if not self.should_retry(e, attempt, should_retry):
                    if config.log_retries:
                        logger.warning(
                            f"Operation failed (non-retryable): {type(e).__name__}: {e}"
                        )
                    raise
                
                # Calculate delay
                delay = self.get_delay(attempt - 1)
                total_delay += delay
                self._stats.record_delay(delay * 1000)  # Convert to ms
                
                if config.log_retries:
                    logger.warning(
                        f"Retry {attempt}/{config.max_attempts}: "
                        f"{type(e).__name__}: {e} "
                        f"(delay={delay:.2f}s)"
                    )
                
                # Call retry callback if provided
                if on_retry is not None:
                    on_retry(e, attempt, delay)
                
                # Wait before retry
                await asyncio.sleep(delay)
        
        # This should not be reached, but just in case
        raise RetryError(
            f"All {config.max_attempts} attempts failed",
            original_error=last_error,
            attempts=config.max_attempts,
            total_delay=total_delay,
        )
    
    def reset_stats(self) -> None:
        """Reset retry statistics."""
        self._stats = RetryStats()


def with_retry(
    config: Optional[RetryConfig] = None,
    should_retry: Optional[Callable[[Exception, int], bool]] = None,
) -> Callable:
    """Decorator to add retry logic to an async function.
    
    Args:
        config: Retry configuration
        should_retry: Custom retry decision function
    
    Example:
        @with_retry(RetryConfig(max_attempts=5))
        async def fetch_data():
            return await db.query("SELECT * FROM data")
        
        # Now fetch_data will automatically retry on failure
        data = await fetch_data()
    """
    manager = RetryManager(config)
    
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await manager.execute_with_retry(
                func,
                *args,
                should_retry=should_retry,
                **kwargs,
            )
        return wrapper
    
    return decorator


# Convenience functions for common retry patterns

def quick_retry() -> RetryConfig:
    """Quick retry for real-time operations.
    
    - 3 attempts
    - 50ms initial delay
    - 500ms max delay
    - Linear backoff
    """
    return RetryConfig(
        max_attempts=3,
        initial_delay=0.05,
        max_delay=0.5,
        backoff="linear",
    )


def standard_retry() -> RetryConfig:
    """Standard retry for most operations.
    
    - 3 attempts
    - 1s initial delay
    - 30s max delay
    - Exponential backoff
    """
    return RetryConfig()


def aggressive_retry() -> RetryConfig:
    """Aggressive retry for background jobs.
    
    - 10 attempts
    - 100ms initial delay
    - 60s max delay
    - Exponential backoff with 1.5x multiplier
    """
    return RetryConfig(
        max_attempts=10,
        initial_delay=0.1,
        max_delay=60.0,
        multiplier=1.5,
    )


def no_retry() -> RetryConfig:
    """No retry (single attempt).
    
    Useful when you want to handle retries at a higher level.
    """
    return RetryConfig(max_attempts=1)

