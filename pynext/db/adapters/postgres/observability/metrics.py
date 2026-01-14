"""
PyNext Database Metrics Module.

Provides metrics collection and export for database operations.
Supports pluggable backends (Prometheus, OpenTelemetry) with a
consistent API.

Why Metrics?
────────────
Logs tell you WHAT happened. Metrics tell you HOW OFTEN and HOW LONG.

Example logs:
    "Query took 523ms"
    "Query took 12ms"
    "Query took 890ms"

Example metrics:
    p50: 100ms, p95: 500ms, p99: 800ms
    queries/sec: 1,234
    error_rate: 0.1%

This module provides:
- Counters (queries_total, errors_total)
- Gauges (connections_active, connections_idle)
- Histograms (query_duration_seconds)
- Labels for segmentation (table, query_type, status)
- Pluggable backends (Prometheus, OpenTelemetry)

Usage Levels:

Level 1: Enable Metrics (Just Works)
    adapter = PostgresAdapter("postgresql://...", metrics=True)

Level 2: Choose Backend
    adapter = PostgresAdapter("postgresql://...", metrics="prometheus")

Level 3: Full Configuration
    adapter = PostgresAdapter("postgresql://...", metrics=MetricsConfig(
        backend="prometheus",
        prefix="myapp_db",
        buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
    ))

AI-Friendly Design:
- Clear metric names and descriptions
- Type hints on all parameters
- Consistent labeling strategy
- Examples in docstrings
"""

from __future__ import annotations

import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

# ============================================================================
# Constants
# ============================================================================

# Default histogram buckets (in seconds)
DEFAULT_BUCKETS = (0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)

# Default prefix for all metrics
DEFAULT_PREFIX = "pynext_db"


# ============================================================================
# Enums
# ============================================================================

class MetricType(str, Enum):
    """Types of metrics."""
    COUNTER = "counter"     # Ever-increasing count
    GAUGE = "gauge"         # Value that can go up or down
    HISTOGRAM = "histogram" # Distribution of values


class BackendType(str, Enum):
    """Supported metrics backends."""
    PROMETHEUS = "prometheus"
    OPENTELEMETRY = "opentelemetry"
    MEMORY = "memory"  # In-memory for testing


# ============================================================================
# Configuration
# ============================================================================

@dataclass
class MetricsConfig:
    """Configuration for database metrics.
    
    This dataclass controls how database metrics are collected and exported.
    All options have sensible defaults.
    
    Attributes:
        enabled: Whether metrics collection is enabled
        backend: Which backend to use (prometheus, opentelemetry, memory)
        prefix: Prefix for all metric names (e.g., "myapp_db")
        buckets: Histogram bucket boundaries (in seconds)
        labels: Additional labels to add to all metrics
        collect_pool_metrics: Whether to collect pool statistics
        collect_query_metrics: Whether to collect query statistics
        histogram_quantiles: Quantiles to compute for histograms
        
    Example:
        # Default configuration
        config = MetricsConfig()
        
        # Custom prefix and backend
        config = MetricsConfig(
            backend=BackendType.PROMETHEUS,
            prefix="myapp_db",
        )
        
        # Custom buckets for query duration
        config = MetricsConfig(
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0],
        )
    """
    enabled: bool = True
    backend: BackendType = BackendType.MEMORY
    prefix: str = DEFAULT_PREFIX
    buckets: Tuple[float, ...] = DEFAULT_BUCKETS
    labels: Dict[str, str] = field(default_factory=dict)
    collect_pool_metrics: bool = True
    collect_query_metrics: bool = True
    histogram_quantiles: Tuple[float, ...] = (0.5, 0.9, 0.95, 0.99)
    
    def __post_init__(self):
        """Validate configuration."""
        if isinstance(self.backend, str):
            self.backend = BackendType(self.backend.lower())
        if not self.prefix:
            self.prefix = DEFAULT_PREFIX
        if not self.buckets:
            self.buckets = DEFAULT_BUCKETS


# ============================================================================
# Metric Definitions
# ============================================================================

@dataclass
class MetricDefinition:
    """Definition of a metric.
    
    Describes what a metric is, how it should be collected, and
    what labels it supports.
    
    Attributes:
        name: Metric name (without prefix)
        type: Type of metric (counter, gauge, histogram)
        description: Human-readable description
        labels: Labels this metric supports
        unit: Unit of measurement (e.g., "seconds", "bytes")
    """
    name: str
    type: MetricType
    description: str
    labels: Tuple[str, ...] = ()
    unit: str = ""
    
    def full_name(self, prefix: str) -> str:
        """Get full metric name with prefix."""
        return f"{prefix}_{self.name}"


# Standard metrics for database operations
STANDARD_METRICS = {
    # Connection pool metrics
    "connections_active": MetricDefinition(
        name="connections_active",
        type=MetricType.GAUGE,
        description="Number of active database connections",
        labels=("pool_name",),
    ),
    "connections_idle": MetricDefinition(
        name="connections_idle",
        type=MetricType.GAUGE,
        description="Number of idle database connections",
        labels=("pool_name",),
    ),
    "connections_waiting": MetricDefinition(
        name="connections_waiting",
        type=MetricType.GAUGE,
        description="Number of requests waiting for a connection",
        labels=("pool_name",),
    ),
    "connections_total": MetricDefinition(
        name="connections_total",
        type=MetricType.COUNTER,
        description="Total number of connections created",
        labels=("pool_name",),
    ),
    "connections_closed": MetricDefinition(
        name="connections_closed",
        type=MetricType.COUNTER,
        description="Total number of connections closed",
        labels=("pool_name", "reason"),
    ),
    
    # Query metrics
    "queries_total": MetricDefinition(
        name="queries_total",
        type=MetricType.COUNTER,
        description="Total number of queries executed",
        labels=("query_type", "table", "status"),
    ),
    "query_duration_seconds": MetricDefinition(
        name="query_duration_seconds",
        type=MetricType.HISTOGRAM,
        description="Query duration in seconds",
        labels=("query_type", "table"),
        unit="seconds",
    ),
    "slow_queries_total": MetricDefinition(
        name="slow_queries_total",
        type=MetricType.COUNTER,
        description="Total number of slow queries",
        labels=("table",),
    ),
    "query_errors_total": MetricDefinition(
        name="query_errors_total",
        type=MetricType.COUNTER,
        description="Total number of query errors",
        labels=("query_type", "error_type"),
    ),
    
    # Pool health metrics
    "pool_exhausted_total": MetricDefinition(
        name="pool_exhausted_total",
        type=MetricType.COUNTER,
        description="Total times the pool was exhausted",
        labels=("pool_name",),
    ),
    "pool_wait_time_seconds": MetricDefinition(
        name="pool_wait_time_seconds",
        type=MetricType.HISTOGRAM,
        description="Time spent waiting for a connection",
        labels=("pool_name",),
        unit="seconds",
    ),
    
    # Transaction metrics
    "transactions_total": MetricDefinition(
        name="transactions_total",
        type=MetricType.COUNTER,
        description="Total number of transactions",
        labels=("status",),  # committed, rolled_back
    ),
    
    # Retry/Circuit breaker metrics
    "retries_total": MetricDefinition(
        name="retries_total",
        type=MetricType.COUNTER,
        description="Total number of query retries",
        labels=("query_type",),
    ),
    "circuit_breaker_state": MetricDefinition(
        name="circuit_breaker_state",
        type=MetricType.GAUGE,
        description="Circuit breaker state (0=closed, 1=open, 0.5=half-open)",
        labels=("breaker_name",),
    ),
    
    # Cache metrics
    "cache_hits_total": MetricDefinition(
        name="cache_hits_total",
        type=MetricType.COUNTER,
        description="Total cache hits",
        labels=("cache_type",),
    ),
    "cache_misses_total": MetricDefinition(
        name="cache_misses_total",
        type=MetricType.COUNTER,
        description="Total cache misses",
        labels=("cache_type",),
    ),
}


# ============================================================================
# Abstract Backend Interface
# ============================================================================

class MetricsBackend(ABC):
    """Abstract base class for metrics backends.
    
    All backends must implement this interface. Backends handle
    the actual storage and export of metrics.
    
    Subclasses:
    - PrometheusBackend: Exports to Prometheus format
    - OpenTelemetryBackend: Exports via OTLP
    - MemoryBackend: Stores in memory (for testing)
    """
    
    @abstractmethod
    def counter_inc(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Increment a counter.
        
        Args:
            name: Full metric name (with prefix)
            value: Value to add (default 1)
            labels: Label key-value pairs
        """
        pass
    
    @abstractmethod
    def gauge_set(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Set a gauge value.
        
        Args:
            name: Full metric name (with prefix)
            value: Value to set
            labels: Label key-value pairs
        """
        pass
    
    @abstractmethod
    def histogram_observe(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Record a histogram observation.
        
        Args:
            name: Full metric name (with prefix)
            value: Value to observe
            labels: Label key-value pairs
        """
        pass
    
    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics as a dictionary.
        
        Returns:
            Dictionary of metric name -> metric data
        """
        pass
    
    @abstractmethod
    def reset(self) -> None:
        """Reset all metrics."""
        pass


# ============================================================================
# Memory Backend (for testing)
# ============================================================================

class MemoryBackend(MetricsBackend):
    """In-memory metrics backend for testing.
    
    Stores all metrics in memory with thread-safe access.
    Useful for unit tests and development.
    
    Example:
        backend = MemoryBackend()
        backend.counter_inc("requests_total", labels={"method": "GET"})
        print(backend.get_metrics())
    """
    
    def __init__(self, buckets: Tuple[float, ...] = DEFAULT_BUCKETS):
        """Initialize memory backend.
        
        Args:
            buckets: Histogram bucket boundaries
        """
        self._lock = threading.Lock()
        self._counters: Dict[str, Dict[str, float]] = {}
        self._gauges: Dict[str, Dict[str, float]] = {}
        self._histograms: Dict[str, Dict[str, List[float]]] = {}
        self._buckets = buckets
    
    def _labels_key(self, labels: Optional[Dict[str, str]]) -> str:
        """Create a hashable key from labels."""
        if not labels:
            return ""
        return ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
    
    def counter_inc(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Increment a counter."""
        key = self._labels_key(labels)
        with self._lock:
            if name not in self._counters:
                self._counters[name] = {}
            if key not in self._counters[name]:
                self._counters[name][key] = 0.0
            self._counters[name][key] += value
    
    def gauge_set(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Set a gauge value."""
        key = self._labels_key(labels)
        with self._lock:
            if name not in self._gauges:
                self._gauges[name] = {}
            self._gauges[name][key] = value
    
    def gauge_inc(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Increment a gauge value."""
        key = self._labels_key(labels)
        with self._lock:
            if name not in self._gauges:
                self._gauges[name] = {}
            if key not in self._gauges[name]:
                self._gauges[name][key] = 0.0
            self._gauges[name][key] += value
    
    def gauge_dec(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Decrement a gauge value."""
        self.gauge_inc(name, -value, labels)
    
    def histogram_observe(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Record a histogram observation."""
        key = self._labels_key(labels)
        with self._lock:
            if name not in self._histograms:
                self._histograms[name] = {}
            if key not in self._histograms[name]:
                self._histograms[name][key] = []
            self._histograms[name][key].append(value)
    
    def get_counter(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None,
    ) -> float:
        """Get counter value."""
        key = self._labels_key(labels)
        with self._lock:
            return self._counters.get(name, {}).get(key, 0.0)
    
    def get_gauge(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None,
    ) -> float:
        """Get gauge value."""
        key = self._labels_key(labels)
        with self._lock:
            return self._gauges.get(name, {}).get(key, 0.0)
    
    def get_histogram(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None,
    ) -> List[float]:
        """Get histogram observations."""
        key = self._labels_key(labels)
        with self._lock:
            return list(self._histograms.get(name, {}).get(key, []))
    
    def get_histogram_stats(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None,
    ) -> Dict[str, float]:
        """Get histogram statistics."""
        observations = self.get_histogram(name, labels)
        if not observations:
            return {"count": 0, "sum": 0, "min": 0, "max": 0, "avg": 0}
        
        return {
            "count": len(observations),
            "sum": sum(observations),
            "min": min(observations),
            "max": max(observations),
            "avg": sum(observations) / len(observations),
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics."""
        with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {
                    name: {
                        key: {
                            "observations": list(values),
                            "count": len(values),
                            "sum": sum(values) if values else 0,
                        }
                        for key, values in label_values.items()
                    }
                    for name, label_values in self._histograms.items()
                },
            }
    
    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()


# ============================================================================
# Metrics Collector
# ============================================================================

class MetricsCollector:
    """Central metrics collector for database operations.
    
    The main class for collecting and recording database metrics.
    Uses a pluggable backend for actual metric storage/export.
    
    Features:
    - Automatic metric registration
    - Thread-safe operations
    - Label validation
    - Metric name prefixing
    
    Example:
        # Create collector with default in-memory backend
        collector = MetricsCollector()
        
        # Record query
        collector.record_query("SELECT", "users", 0.05, "success")
        
        # Record pool stats
        collector.record_pool_stats("main", active=5, idle=10, waiting=0)
        
        # Get metrics
        print(collector.get_metrics())
    """
    
    def __init__(
        self,
        config: Optional[MetricsConfig] = None,
        backend: Optional[MetricsBackend] = None,
    ):
        """Initialize metrics collector.
        
        Args:
            config: Metrics configuration
            backend: Custom backend (auto-created from config if not provided)
        """
        self.config = config or MetricsConfig()
        
        # Create or use provided backend
        if backend:
            self._backend = backend
        elif self.config.backend == BackendType.MEMORY:
            self._backend = MemoryBackend(self.config.buckets)
        elif self.config.backend == BackendType.PROMETHEUS:
            # Lazy import to avoid dependency
            from .prometheus import PrometheusBackend
            self._backend = PrometheusBackend(self.config)
        elif self.config.backend == BackendType.OPENTELEMETRY:
            # Lazy import to avoid dependency
            from .opentelemetry import OpenTelemetryBackend
            self._backend = OpenTelemetryBackend(self.config)
        else:
            self._backend = MemoryBackend(self.config.buckets)
        
        # Register standard metrics
        self._metrics = dict(STANDARD_METRICS)
    
    @property
    def enabled(self) -> bool:
        """Whether metrics collection is enabled."""
        return self.config.enabled
    
    def _full_name(self, name: str) -> str:
        """Get full metric name with prefix."""
        return f"{self.config.prefix}_{name}"
    
    def _merge_labels(self, labels: Optional[Dict[str, str]]) -> Dict[str, str]:
        """Merge provided labels with default labels."""
        result = dict(self.config.labels)
        if labels:
            result.update(labels)
        return result
    
    # ========================================================================
    # Query Metrics
    # ========================================================================
    
    def record_query(
        self,
        query_type: str,
        table: str,
        duration_seconds: float,
        status: str = "success",
    ) -> None:
        """Record a query execution.
        
        Args:
            query_type: Type of query (SELECT, INSERT, UPDATE, DELETE)
            table: Table name
            duration_seconds: Query duration in seconds
            status: Query status (success, error)
        
        Example:
            collector.record_query("SELECT", "users", 0.05, "success")
        """
        if not self.config.enabled or not self.config.collect_query_metrics:
            return
        
        labels = {"query_type": query_type, "table": table, "status": status}
        
        # Increment query counter
        self._backend.counter_inc(
            self._full_name("queries_total"),
            labels=self._merge_labels(labels),
        )
        
        # Record duration histogram
        self._backend.histogram_observe(
            self._full_name("query_duration_seconds"),
            duration_seconds,
            labels=self._merge_labels({"query_type": query_type, "table": table}),
        )
    
    def record_slow_query(self, table: str) -> None:
        """Record a slow query.
        
        Args:
            table: Table name
        """
        if not self.config.enabled:
            return
        
        self._backend.counter_inc(
            self._full_name("slow_queries_total"),
            labels=self._merge_labels({"table": table}),
        )
    
    def record_query_error(
        self,
        query_type: str,
        error_type: str,
    ) -> None:
        """Record a query error.
        
        Args:
            query_type: Type of query
            error_type: Type of error (e.g., "TimeoutError")
        """
        if not self.config.enabled:
            return
        
        self._backend.counter_inc(
            self._full_name("query_errors_total"),
            labels=self._merge_labels({"query_type": query_type, "error_type": error_type}),
        )
    
    # ========================================================================
    # Connection Pool Metrics
    # ========================================================================
    
    def record_pool_stats(
        self,
        pool_name: str,
        active: int,
        idle: int,
        waiting: int,
    ) -> None:
        """Record connection pool statistics.
        
        Args:
            pool_name: Name of the pool
            active: Number of active connections
            idle: Number of idle connections
            waiting: Number of waiting requests
        
        Example:
            collector.record_pool_stats("main", active=5, idle=10, waiting=0)
        """
        if not self.config.enabled or not self.config.collect_pool_metrics:
            return
        
        labels = self._merge_labels({"pool_name": pool_name})
        
        self._backend.gauge_set(
            self._full_name("connections_active"),
            float(active),
            labels=labels,
        )
        self._backend.gauge_set(
            self._full_name("connections_idle"),
            float(idle),
            labels=labels,
        )
        self._backend.gauge_set(
            self._full_name("connections_waiting"),
            float(waiting),
            labels=labels,
        )
    
    def record_connection_created(self, pool_name: str) -> None:
        """Record a new connection being created."""
        if not self.config.enabled:
            return
        
        self._backend.counter_inc(
            self._full_name("connections_total"),
            labels=self._merge_labels({"pool_name": pool_name}),
        )
    
    def record_connection_closed(
        self,
        pool_name: str,
        reason: str = "normal",
    ) -> None:
        """Record a connection being closed.
        
        Args:
            pool_name: Name of the pool
            reason: Reason for closing (normal, error, timeout, leak)
        """
        if not self.config.enabled:
            return
        
        self._backend.counter_inc(
            self._full_name("connections_closed"),
            labels=self._merge_labels({"pool_name": pool_name, "reason": reason}),
        )
    
    def record_pool_exhausted(self, pool_name: str) -> None:
        """Record pool exhaustion event."""
        if not self.config.enabled:
            return
        
        self._backend.counter_inc(
            self._full_name("pool_exhausted_total"),
            labels=self._merge_labels({"pool_name": pool_name}),
        )
    
    def record_pool_wait_time(
        self,
        pool_name: str,
        wait_seconds: float,
    ) -> None:
        """Record time spent waiting for a connection.
        
        Args:
            pool_name: Name of the pool
            wait_seconds: Time spent waiting in seconds
        """
        if not self.config.enabled:
            return
        
        self._backend.histogram_observe(
            self._full_name("pool_wait_time_seconds"),
            wait_seconds,
            labels=self._merge_labels({"pool_name": pool_name}),
        )
    
    # ========================================================================
    # Transaction Metrics
    # ========================================================================
    
    def record_transaction(self, status: str) -> None:
        """Record a transaction completion.
        
        Args:
            status: Transaction status (committed, rolled_back)
        """
        if not self.config.enabled:
            return
        
        self._backend.counter_inc(
            self._full_name("transactions_total"),
            labels=self._merge_labels({"status": status}),
        )
    
    # ========================================================================
    # Retry/Circuit Breaker Metrics
    # ========================================================================
    
    def record_retry(self, query_type: str) -> None:
        """Record a query retry."""
        if not self.config.enabled:
            return
        
        self._backend.counter_inc(
            self._full_name("retries_total"),
            labels=self._merge_labels({"query_type": query_type}),
        )
    
    def record_circuit_breaker_state(
        self,
        breaker_name: str,
        state: str,
    ) -> None:
        """Record circuit breaker state.
        
        Args:
            breaker_name: Name of the circuit breaker
            state: State (closed, open, half_open)
        """
        if not self.config.enabled:
            return
        
        # Convert state to numeric value
        state_value = {"closed": 0.0, "open": 1.0, "half_open": 0.5}.get(state, 0.0)
        
        self._backend.gauge_set(
            self._full_name("circuit_breaker_state"),
            state_value,
            labels=self._merge_labels({"breaker_name": breaker_name}),
        )
    
    # ========================================================================
    # Cache Metrics
    # ========================================================================
    
    def record_cache_hit(self, cache_type: str = "query") -> None:
        """Record a cache hit."""
        if not self.config.enabled:
            return
        
        self._backend.counter_inc(
            self._full_name("cache_hits_total"),
            labels=self._merge_labels({"cache_type": cache_type}),
        )
    
    def record_cache_miss(self, cache_type: str = "query") -> None:
        """Record a cache miss."""
        if not self.config.enabled:
            return
        
        self._backend.counter_inc(
            self._full_name("cache_misses_total"),
            labels=self._merge_labels({"cache_type": cache_type}),
        )
    
    # ========================================================================
    # Low-Level Access
    # ========================================================================
    
    def counter_inc(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Increment a custom counter."""
        if not self.config.enabled:
            return
        self._backend.counter_inc(
            self._full_name(name),
            value,
            labels=self._merge_labels(labels),
        )
    
    def gauge_set(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Set a custom gauge."""
        if not self.config.enabled:
            return
        self._backend.gauge_set(
            self._full_name(name),
            value,
            labels=self._merge_labels(labels),
        )
    
    def histogram_observe(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Record a custom histogram observation."""
        if not self.config.enabled:
            return
        self._backend.histogram_observe(
            self._full_name(name),
            value,
            labels=self._merge_labels(labels),
        )
    
    # ========================================================================
    # Export
    # ========================================================================
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics.
        
        Returns:
            Dictionary with all metrics
        """
        return self._backend.get_metrics()
    
    def reset(self) -> None:
        """Reset all metrics."""
        self._backend.reset()
    
    def get_backend(self) -> MetricsBackend:
        """Get the underlying backend."""
        return self._backend


# ============================================================================
# Timing Context Manager
# ============================================================================

class Timer:
    """Context manager for timing operations.
    
    Automatically records duration to a histogram when the context exits.
    
    Example:
        collector = MetricsCollector()
        
        with Timer(collector, "query_duration_seconds", {"table": "users"}):
            # Execute query
            await db.execute("SELECT * FROM users")
    """
    
    def __init__(
        self,
        collector: MetricsCollector,
        metric_name: str,
        labels: Optional[Dict[str, str]] = None,
    ):
        """Initialize timer.
        
        Args:
            collector: Metrics collector
            metric_name: Histogram metric name
            labels: Labels for the metric
        """
        self.collector = collector
        self.metric_name = metric_name
        self.labels = labels
        self._start: Optional[float] = None
    
    def __enter__(self) -> "Timer":
        """Start timing."""
        self._start = time.monotonic()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Stop timing and record duration."""
        if self._start is not None:
            duration = time.monotonic() - self._start
            self.collector.histogram_observe(self.metric_name, duration, self.labels)
    
    async def __aenter__(self) -> "Timer":
        """Async start timing."""
        self._start = time.monotonic()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async stop timing and record duration."""
        if self._start is not None:
            duration = time.monotonic() - self._start
            self.collector.histogram_observe(self.metric_name, duration, self.labels)
    
    @property
    def elapsed(self) -> float:
        """Get elapsed time in seconds."""
        if self._start is None:
            return 0.0
        return time.monotonic() - self._start


# ============================================================================
# Convenience Functions
# ============================================================================

def create_collector(
    backend: Union[str, BackendType] = BackendType.MEMORY,
    prefix: str = DEFAULT_PREFIX,
    **kwargs: Any,
) -> MetricsCollector:
    """Create a metrics collector with common options.
    
    Args:
        backend: Backend type (prometheus, opentelemetry, memory)
        prefix: Metric name prefix
        **kwargs: Additional MetricsConfig options
    
    Returns:
        Configured MetricsCollector instance
    
    Example:
        # In-memory collector for testing
        collector = create_collector()
        
        # Prometheus collector for production
        collector = create_collector(backend="prometheus", prefix="myapp_db")
    """
    if isinstance(backend, str):
        backend = BackendType(backend.lower())
    
    config = MetricsConfig(
        backend=backend,
        prefix=prefix,
        **kwargs,
    )
    
    return MetricsCollector(config)


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # Configuration
    "MetricsConfig",
    "MetricType",
    "BackendType",
    "MetricDefinition",
    "STANDARD_METRICS",
    "DEFAULT_BUCKETS",
    "DEFAULT_PREFIX",
    
    # Backend Interface
    "MetricsBackend",
    "MemoryBackend",
    
    # Collector
    "MetricsCollector",
    
    # Utilities
    "Timer",
    "create_collector",
]

