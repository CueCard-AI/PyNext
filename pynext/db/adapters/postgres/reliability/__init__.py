"""
PostgreSQL Reliability Features (Phase 5.3).

This module contains fault tolerance components:
- retry.py: Automatic retry with exponential backoff
- circuit.py: Circuit breaker pattern for failure isolation
- replica.py: Read replica routing and load balancing
- degradation.py: Graceful degradation under load
"""

from .retry import (
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
)
from .circuit import (
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
from .replica import (
    Replica,
    ReplicaConfig,
    ReplicaHealth,
    ReplicaManager,
    ReplicaStats,
    ReplicaSetStats,
    ReplicaUnavailableError,
    RoutingStrategy,
    simple_replicas,
    weighted_replicas,
)
from .degradation import (
    DegradationAction,
    DegradationConfig,
    DegradationError,
    DegradationLevel,
    DegradationManager,
    DegradationMetric,
    DegradationStats,
    DegradationTrigger,
    default_actions,
    default_triggers,
    disabled_config,
    lenient_config,
    strict_config,
)

__all__ = [
    # Retry
    "RetryConfig",
    "RetryManager",
    "RetryError",
    "RetryStats",
    "BackoffStrategy",
    "with_retry",
    "quick_retry",
    "standard_retry",
    "aggressive_retry",
    "no_retry",
    # Circuit Breaker
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerRegistry",
    "CircuitOpenError",
    "CircuitScope",
    "CircuitState",
    "CircuitStats",
    "create_global_breaker",
    "create_sensitive_breaker",
    "create_tolerant_breaker",
    # Replica
    "Replica",
    "ReplicaConfig",
    "ReplicaHealth",
    "ReplicaManager",
    "ReplicaStats",
    "ReplicaSetStats",
    "ReplicaUnavailableError",
    "RoutingStrategy",
    "simple_replicas",
    "weighted_replicas",
    # Degradation
    "DegradationAction",
    "DegradationConfig",
    "DegradationError",
    "DegradationLevel",
    "DegradationManager",
    "DegradationMetric",
    "DegradationStats",
    "DegradationTrigger",
    "default_actions",
    "default_triggers",
    "disabled_config",
    "lenient_config",
    "strict_config",
]

