"""
PostgreSQL Performance Optimization (Phase 5.4).

This module contains query optimization components:
- timeout.py: Per-query timeout management
- query_cache.py: Query result caching with smart invalidation
- coalesce.py: Query coalescing for identical concurrent queries
- pipeline.py: Query pipelining for reduced round trips
- batch.py: Batch optimization for bulk operations
- scaling.py: Adaptive pool scaling based on load
"""

from .timeout import (
    QueryType,
    QueryTimeoutConfig,
    QueryWithTimeout,
    QueryTimeoutError,
    TimeoutStats,
    TimeoutManager,
    quick_timeout_config,
    standard_timeout_config,
    batch_timeout_config,
    no_timeout_config,
)
from .query_cache import (
    InvalidationStrategy,
    QueryCacheConfig,
    CacheEntry,
    CacheStats,
    QueryCache,
    simple_cache_config,
    smart_cache_config,
    aggressive_cache_config,
    no_cache_config,
)
from .coalesce import (
    CoalescingConfig,
    PendingQuery,
    CoalescingStats,
    CoalescingLimitError,
    QueryCoalescer,
    aggressive_coalescing_config,
    conservative_coalescing_config,
    disabled_coalescing_config,
)
from .pipeline import (
    PipelineConfig,
    PipelinedQuery,
    PipelineStats,
    QueryPipeline,
    high_throughput_config,
    low_latency_config,
    disabled_pipeline_config,
)
from .batch import (
    BatchConfig,
    BatchResult,
    BatchStats,
    BatchOptimizer,
    bulk_load_config,
    transactional_config,
    disabled_batch_config,
)
from .scaling import (
    AdaptiveScalingConfig,
    LoadSample,
    ScaleEvent,
    ScalingStats,
    ScalingRecommendation,
    AdaptiveScaler,
    aggressive_scaling_config,
    conservative_scaling_config,
    disabled_scaling_config,
)

__all__ = [
    # Timeout
    "QueryType",
    "QueryTimeoutConfig",
    "QueryWithTimeout",
    "QueryTimeoutError",
    "TimeoutStats",
    "TimeoutManager",
    "quick_timeout_config",
    "standard_timeout_config",
    "batch_timeout_config",
    "no_timeout_config",
    # Query Cache
    "InvalidationStrategy",
    "QueryCacheConfig",
    "CacheEntry",
    "CacheStats",
    "QueryCache",
    "simple_cache_config",
    "smart_cache_config",
    "aggressive_cache_config",
    "no_cache_config",
    # Coalescing
    "CoalescingConfig",
    "PendingQuery",
    "CoalescingStats",
    "CoalescingLimitError",
    "QueryCoalescer",
    "aggressive_coalescing_config",
    "conservative_coalescing_config",
    "disabled_coalescing_config",
    # Pipeline
    "PipelineConfig",
    "PipelinedQuery",
    "PipelineStats",
    "QueryPipeline",
    "high_throughput_config",
    "low_latency_config",
    "disabled_pipeline_config",
    # Batch
    "BatchConfig",
    "BatchResult",
    "BatchStats",
    "BatchOptimizer",
    "bulk_load_config",
    "transactional_config",
    "disabled_batch_config",
    # Scaling
    "AdaptiveScalingConfig",
    "LoadSample",
    "ScaleEvent",
    "ScalingStats",
    "ScalingRecommendation",
    "AdaptiveScaler",
    "aggressive_scaling_config",
    "conservative_scaling_config",
    "disabled_scaling_config",
]

