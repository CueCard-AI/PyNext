"""
PostgreSQL Circuit Breaker Pattern.

This module implements the circuit breaker pattern for database operations,
preventing cascade failures when the database is struggling.

Why Circuit Breakers?

When a database is overloaded or failing, continuing to send requests:
1. Makes the problem worse (more load)
2. Wastes resources (connections, threads)
3. Creates user-facing timeouts
4. Can cause cascade failures

A circuit breaker "trips" when failures exceed a threshold, immediately
rejecting requests instead of waiting for them to fail.

Circuit States:

    CLOSED (normal)
        │
        │ failures > threshold
        ▼
    OPEN (rejecting)
        │
        │ timeout expires
        ▼
    HALF_OPEN (testing)
        │
        ├─ success → CLOSED
        └─ failure → OPEN

Three Scopes:

1. GLOBAL: One breaker for entire database
   - Simple, catches database-wide issues
   
2. PER_CONNECTION: One breaker per connection
   - Isolates bad connections
   
3. PER_QUERY_TYPE: Separate breakers for reads/writes
   - Allows reads while writes are failing

AI-Friendly Design:
- Clear state machine
- Observable state transitions
- Comprehensive logging
- Easy to configure and extend
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Type, TypeVar

logger = logging.getLogger("pynext.db.postgres.circuit")

T = TypeVar("T")


class CircuitState(Enum):
    """State of the circuit breaker.
    
    CLOSED: Normal operation, requests flow through
    OPEN: Circuit is tripped, requests are rejected immediately
    HALF_OPEN: Testing if the service has recovered
    """
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitScope(Enum):
    """Scope of the circuit breaker.
    
    GLOBAL: One breaker for the entire database
    CONNECTION: One breaker per connection
    QUERY_TYPE: Separate breakers for reads/writes/etc
    """
    GLOBAL = "global"
    CONNECTION = "connection"
    QUERY_TYPE = "query_type"


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breakers.
    
    Attributes:
        failure_threshold: Number of failures before opening circuit.
                          Default: 5
        success_threshold: Successes needed to close from half-open.
                          Default: 2
        timeout: Seconds to wait before testing recovery (half-open).
                Default: 30.0
        scope: Circuit breaker scope (global, connection, query_type).
              Default: "global"
        half_open_max_requests: Max concurrent requests in half-open state.
                               Default: 1
        failure_rate_threshold: Alternative: trip when failure rate exceeds this.
                               Default: None (use failure_threshold)
        sample_window: Time window for failure rate calculation.
                      Default: 60.0 seconds
        excluded_errors: Error types that don't count as failures.
                        Default: empty set
    
    Example:
        # Standard circuit breaker
        config = CircuitBreakerConfig(
            failure_threshold=5,
            success_threshold=2,
            timeout=30.0,
        )
        
        # Sensitive circuit breaker (trips quickly)
        config = CircuitBreakerConfig(
            failure_threshold=3,
            timeout=10.0,
        )
        
        # Rate-based circuit breaker
        config = CircuitBreakerConfig(
            failure_rate_threshold=0.5,  # 50% failure rate
            sample_window=60.0,
        )
    """
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout: float = 30.0
    scope: str = "global"
    half_open_max_requests: int = 1
    failure_rate_threshold: Optional[float] = None
    sample_window: float = 60.0
    excluded_errors: Set[Type[Exception]] = field(default_factory=set)
    
    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.failure_threshold < 1:
            raise ValueError(f"failure_threshold must be >= 1, got {self.failure_threshold}")
        if self.success_threshold < 1:
            raise ValueError(f"success_threshold must be >= 1, got {self.success_threshold}")
        if self.timeout < 0:
            raise ValueError(f"timeout must be >= 0, got {self.timeout}")
        if self.scope not in ("global", "connection", "query_type"):
            raise ValueError(f"scope must be global/connection/query_type, got {self.scope}")
        if self.failure_rate_threshold is not None:
            if not 0 < self.failure_rate_threshold <= 1:
                raise ValueError(f"failure_rate_threshold must be 0-1, got {self.failure_rate_threshold}")


@dataclass
class CircuitStats:
    """Statistics for a circuit breaker.
    
    Tracks failures, successes, state transitions, and timing.
    """
    total_requests: int = 0
    total_successes: int = 0
    total_failures: int = 0
    total_rejections: int = 0
    state_transitions: int = 0
    last_failure_time: float = 0.0
    last_success_time: float = 0.0
    last_state_change: float = 0.0
    current_state: CircuitState = CircuitState.CLOSED
    time_in_open: float = 0.0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    
    # Rolling window for failure rate
    _recent_results: List[tuple] = field(default_factory=list)
    
    @property
    def failure_rate(self) -> float:
        """Current failure rate (0-1)."""
        if self.total_requests == 0:
            return 0.0
        return self.total_failures / self.total_requests
    
    def get_recent_failure_rate(self, window: float = 60.0) -> float:
        """Get failure rate within recent time window."""
        now = time.monotonic()
        cutoff = now - window
        
        # Filter to recent results
        recent = [(t, s) for t, s in self._recent_results if t > cutoff]
        
        if not recent:
            return 0.0
        
        failures = sum(1 for _, success in recent if not success)
        return failures / len(recent)
    
    def record_request(self) -> None:
        """Record a request attempt."""
        self.total_requests += 1
    
    def record_success(self) -> None:
        """Record a successful request."""
        now = time.monotonic()
        self.total_successes += 1
        self.last_success_time = now
        self.consecutive_successes += 1
        self.consecutive_failures = 0
        self._recent_results.append((now, True))
        self._trim_recent_results()
    
    def record_failure(self) -> None:
        """Record a failed request."""
        now = time.monotonic()
        self.total_failures += 1
        self.last_failure_time = now
        self.consecutive_failures += 1
        self.consecutive_successes = 0
        self._recent_results.append((now, False))
        self._trim_recent_results()
    
    def record_rejection(self) -> None:
        """Record a rejected request (circuit open)."""
        self.total_rejections += 1
    
    def record_state_change(self, new_state: CircuitState) -> None:
        """Record a state transition."""
        now = time.monotonic()
        
        # Track time spent in open state
        if self.current_state == CircuitState.OPEN:
            self.time_in_open += now - self.last_state_change
        
        self.current_state = new_state
        self.last_state_change = now
        self.state_transitions += 1
    
    def _trim_recent_results(self, max_size: int = 1000) -> None:
        """Keep recent results list bounded."""
        if len(self._recent_results) > max_size:
            self._recent_results = self._recent_results[-max_size:]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/metrics."""
        return {
            "total_requests": self.total_requests,
            "total_successes": self.total_successes,
            "total_failures": self.total_failures,
            "total_rejections": self.total_rejections,
            "failure_rate": self.failure_rate,
            "state_transitions": self.state_transitions,
            "current_state": self.current_state.value,
            "consecutive_failures": self.consecutive_failures,
            "consecutive_successes": self.consecutive_successes,
            "time_in_open": self.time_in_open,
        }


class CircuitOpenError(Exception):
    """Raised when a request is rejected due to open circuit.
    
    Attributes:
        circuit_name: Name of the circuit breaker
        time_until_half_open: Seconds until the circuit will try half-open
    """
    
    def __init__(
        self,
        message: str,
        circuit_name: str,
        time_until_half_open: float,
    ):
        super().__init__(message)
        self.circuit_name = circuit_name
        self.time_until_half_open = time_until_half_open
    
    def __str__(self) -> str:
        return (
            f"CircuitOpenError: {self.args[0]} "
            f"(circuit={self.circuit_name}, retry_in={self.time_until_half_open:.1f}s)"
        )


class CircuitBreaker:
    """Circuit breaker for a single scope.
    
    Tracks failures and manages state transitions.
    
    Usage:
        breaker = CircuitBreaker("my-service", config)
        
        # Check before making request
        if breaker.allow_request():
            try:
                result = await operation()
                breaker.record_success()
                return result
            except Exception as e:
                breaker.record_failure(e)
                raise
        else:
            raise CircuitOpenError(...)
    
    Or use the execute helper:
        result = await breaker.execute(operation)
    """
    
    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
    ):
        """Initialize the circuit breaker.
        
        Args:
            name: Name for this circuit breaker (for logging)
            config: Configuration. Uses defaults if not provided.
        """
        self._name = name
        self._config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._stats = CircuitStats()
        self._last_failure_time: float = 0.0
        self._last_state_change: float = time.monotonic()
        self._half_open_requests: int = 0
        self._lock = threading.Lock()
    
    @property
    def name(self) -> str:
        """Get the circuit breaker name."""
        return self._name
    
    @property
    def state(self) -> CircuitState:
        """Get the current circuit state."""
        return self._state
    
    @property
    def stats(self) -> CircuitStats:
        """Get circuit breaker statistics."""
        return self._stats
    
    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)."""
        return self._state == CircuitState.CLOSED
    
    @property
    def is_open(self) -> bool:
        """Check if circuit is open (rejecting requests)."""
        return self._state == CircuitState.OPEN
    
    @property
    def is_half_open(self) -> bool:
        """Check if circuit is half-open (testing recovery)."""
        return self._state == CircuitState.HALF_OPEN
    
    def _should_trip(self) -> bool:
        """Check if the circuit should trip open."""
        config = self._config
        
        # Check failure rate threshold (if configured)
        if config.failure_rate_threshold is not None:
            rate = self._stats.get_recent_failure_rate(config.sample_window)
            if rate >= config.failure_rate_threshold:
                return True
        
        # Check consecutive failures
        return self._stats.consecutive_failures >= config.failure_threshold
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should try half-open state."""
        if self._state != CircuitState.OPEN:
            return False
        
        time_since_open = time.monotonic() - self._last_state_change
        return time_since_open >= self._config.timeout
    
    def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to a new state."""
        old_state = self._state
        self._state = new_state
        self._last_state_change = time.monotonic()
        self._stats.record_state_change(new_state)
        
        if new_state == CircuitState.HALF_OPEN:
            self._half_open_requests = 0
        
        logger.info(
            f"Circuit '{self._name}' state change: {old_state.value} → {new_state.value}"
        )
    
    def allow_request(self) -> bool:
        """Check if a request should be allowed.
        
        Returns:
            True if the request can proceed, False if it should be rejected
        """
        with self._lock:
            if self._state == CircuitState.CLOSED:
                return True
            
            if self._state == CircuitState.OPEN:
                # Check if we should try half-open
                if self._should_attempt_reset():
                    self._transition_to(CircuitState.HALF_OPEN)
                    self._half_open_requests = 1
                    return True
                return False
            
            # Half-open: allow limited requests
            if self._half_open_requests < self._config.half_open_max_requests:
                self._half_open_requests += 1
                return True
            
            return False
    
    def record_success(self) -> None:
        """Record a successful request."""
        with self._lock:
            self._stats.record_success()
            
            if self._state == CircuitState.HALF_OPEN:
                # Check if we have enough successes to close
                if self._stats.consecutive_successes >= self._config.success_threshold:
                    self._transition_to(CircuitState.CLOSED)
    
    def record_failure(self, error: Optional[Exception] = None) -> None:
        """Record a failed request.
        
        Args:
            error: The exception that occurred (for filtering)
        """
        # Check if error is excluded
        if error is not None:
            for excluded in self._config.excluded_errors:
                if isinstance(error, excluded):
                    return
        
        with self._lock:
            self._stats.record_failure()
            self._last_failure_time = time.monotonic()
            
            if self._state == CircuitState.CLOSED:
                # Check if we should trip
                if self._should_trip():
                    self._transition_to(CircuitState.OPEN)
            
            elif self._state == CircuitState.HALF_OPEN:
                # Failure in half-open goes back to open
                self._transition_to(CircuitState.OPEN)
    
    def get_time_until_half_open(self) -> float:
        """Get seconds until the circuit will try half-open.
        
        Returns:
            Seconds remaining, or 0 if not in open state
        """
        if self._state != CircuitState.OPEN:
            return 0.0
        
        time_since_open = time.monotonic() - self._last_state_change
        remaining = self._config.timeout - time_since_open
        return max(0.0, remaining)
    
    async def execute(
        self,
        operation: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Execute an operation with circuit breaker protection.
        
        Args:
            operation: Async function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
        
        Returns:
            Result of the operation
        
        Raises:
            CircuitOpenError: If circuit is open
            Exception: If operation fails
        """
        self._stats.record_request()
        
        if not self.allow_request():
            self._stats.record_rejection()
            raise CircuitOpenError(
                f"Circuit '{self._name}' is open",
                circuit_name=self._name,
                time_until_half_open=self.get_time_until_half_open(),
            )
        
        try:
            result = await operation(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure(e)
            raise
    
    def reset(self) -> None:
        """Reset the circuit breaker to closed state."""
        with self._lock:
            self._transition_to(CircuitState.CLOSED)
            self._stats = CircuitStats()
    
    def force_open(self) -> None:
        """Force the circuit to open state."""
        with self._lock:
            self._transition_to(CircuitState.OPEN)
    
    def force_close(self) -> None:
        """Force the circuit to closed state."""
        with self._lock:
            self._transition_to(CircuitState.CLOSED)


class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers.
    
    Supports three scopes:
    - GLOBAL: Single breaker for all operations
    - CONNECTION: One breaker per connection ID
    - QUERY_TYPE: One breaker per query type (read, write, etc.)
    
    Usage:
        registry = CircuitBreakerRegistry(config)
        
        # Global breaker
        breaker = registry.get_global()
        
        # Per-connection breaker
        breaker = registry.get_for_connection("conn_123")
        
        # Per-query-type breaker
        breaker = registry.get_for_query_type("read")
    """
    
    def __init__(
        self,
        config: Optional[CircuitBreakerConfig] = None,
        default_config: Optional[CircuitBreakerConfig] = None,
    ):
        """Initialize the registry.
        
        Args:
            config: Configuration for the main scope
            default_config: Default config for any scope
        """
        self._config = config or default_config or CircuitBreakerConfig()
        self._default_config = default_config or self._config
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._lock = threading.Lock()
    
    def _get_or_create(
        self,
        key: str,
        config: Optional[CircuitBreakerConfig] = None,
    ) -> CircuitBreaker:
        """Get or create a circuit breaker for the given key."""
        with self._lock:
            if key not in self._breakers:
                self._breakers[key] = CircuitBreaker(
                    name=key,
                    config=config or self._default_config,
                )
            return self._breakers[key]
    
    def get_breaker(
        self,
        key: str,
        config: Optional[CircuitBreakerConfig] = None,
    ) -> CircuitBreaker:
        """Get a circuit breaker by key.
        
        Args:
            key: Unique key for the breaker
            config: Optional config override
        
        Returns:
            The circuit breaker for this key
        """
        return self._get_or_create(key, config)
    
    def get_global(self) -> CircuitBreaker:
        """Get the global circuit breaker."""
        return self._get_or_create("global", self._config)
    
    def get_for_connection(self, connection_id: str) -> CircuitBreaker:
        """Get the circuit breaker for a specific connection.
        
        Args:
            connection_id: Unique connection identifier
        
        Returns:
            The circuit breaker for this connection
        """
        return self._get_or_create(f"conn:{connection_id}")
    
    def get_for_query_type(self, query_type: str) -> CircuitBreaker:
        """Get the circuit breaker for a query type.
        
        Args:
            query_type: Type of query (e.g., "read", "write", "transaction")
        
        Returns:
            The circuit breaker for this query type
        """
        return self._get_or_create(f"query:{query_type}")
    
    def get_all_breakers(self) -> Dict[str, CircuitBreaker]:
        """Get all circuit breakers in the registry."""
        with self._lock:
            return dict(self._breakers)
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all circuit breakers."""
        with self._lock:
            return {
                key: breaker.stats.to_dict()
                for key, breaker in self._breakers.items()
            }
    
    def reset_all(self) -> None:
        """Reset all circuit breakers."""
        with self._lock:
            for breaker in self._breakers.values():
                breaker.reset()
    
    def remove_breaker(self, key: str) -> None:
        """Remove a circuit breaker from the registry."""
        with self._lock:
            self._breakers.pop(key, None)
    
    def clear(self) -> None:
        """Remove all circuit breakers."""
        with self._lock:
            self._breakers.clear()


# Convenience functions

def create_global_breaker(
    failure_threshold: int = 5,
    timeout: float = 30.0,
) -> CircuitBreaker:
    """Create a simple global circuit breaker.
    
    Args:
        failure_threshold: Failures before opening
        timeout: Seconds before trying half-open
    
    Returns:
        A configured circuit breaker
    """
    return CircuitBreaker(
        name="global",
        config=CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            timeout=timeout,
            scope="global",
        ),
    )


def create_sensitive_breaker(name: str) -> CircuitBreaker:
    """Create a sensitive circuit breaker (trips quickly).
    
    Good for critical paths where failures should immediately
    stop traffic.
    """
    return CircuitBreaker(
        name=name,
        config=CircuitBreakerConfig(
            failure_threshold=3,
            success_threshold=1,
            timeout=10.0,
        ),
    )


def create_tolerant_breaker(name: str) -> CircuitBreaker:
    """Create a tolerant circuit breaker (trips slowly).
    
    Good for operations where occasional failures are acceptable.
    """
    return CircuitBreaker(
        name=name,
        config=CircuitBreakerConfig(
            failure_threshold=10,
            success_threshold=3,
            timeout=60.0,
        ),
    )

