"""
PyNext Prometheus Backend Module.

Provides Prometheus-compatible metrics export for database operations.
Generates metrics in Prometheus text exposition format that can be
scraped by Prometheus or compatible systems.

Prometheus Format Overview:
──────────────────────────
Prometheus uses a simple text format:

    # HELP metric_name Description of the metric
    # TYPE metric_name type
    metric_name{label="value"} 123.45

Types:
    - counter: Cumulative, always increases
    - gauge: Can go up or down
    - histogram: Distribution with buckets

Example Output:
    # HELP pynext_db_queries_total Total queries
    # TYPE pynext_db_queries_total counter
    pynext_db_queries_total{query_type="SELECT",table="users",status="success"} 1234

Usage:
    from pynext.db.adapters.postgres_prometheus import PrometheusBackend
    
    backend = PrometheusBackend()
    backend.counter_inc("queries_total", labels={"query_type": "SELECT"})
    
    # Get Prometheus format output
    output = backend.expose()
    # Serve this at /metrics endpoint

AI-Friendly Design:
- Standard Prometheus format (widely understood)
- Thread-safe operations
- Clear metric naming conventions
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from .postgres_metrics import (
    MetricsBackend,
    MetricsConfig,
    MetricType,
    STANDARD_METRICS,
    DEFAULT_BUCKETS,
)


# ============================================================================
# Prometheus Metric Classes
# ============================================================================

@dataclass
class PrometheusCounter:
    """A Prometheus counter metric.
    
    Counters always increase (or reset to zero on restart).
    
    Attributes:
        name: Metric name
        help: Description text
        labels: Set of label names this counter uses
        values: Map of label values -> counter value
    """
    name: str
    help: str = ""
    labels: Tuple[str, ...] = ()
    values: Dict[str, float] = field(default_factory=dict)
    
    def inc(self, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment the counter."""
        key = self._labels_key(labels)
        if key not in self.values:
            self.values[key] = 0.0
        self.values[key] += value
    
    def get(self, labels: Optional[Dict[str, str]] = None) -> float:
        """Get counter value."""
        key = self._labels_key(labels)
        return self.values.get(key, 0.0)
    
    def _labels_key(self, labels: Optional[Dict[str, str]]) -> str:
        """Create hashable key from labels."""
        if not labels:
            return ""
        return ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
    
    def expose(self) -> str:
        """Generate Prometheus format text."""
        lines = []
        if self.help:
            lines.append(f"# HELP {self.name} {self.help}")
        lines.append(f"# TYPE {self.name} counter")
        
        for label_key, value in self.values.items():
            if label_key:
                lines.append(f"{self.name}{{{label_key}}} {value}")
            else:
                lines.append(f"{self.name} {value}")
        
        return "\n".join(lines)


@dataclass
class PrometheusGauge:
    """A Prometheus gauge metric.
    
    Gauges can go up and down (e.g., current connections).
    
    Attributes:
        name: Metric name
        help: Description text
        labels: Set of label names this gauge uses
        values: Map of label values -> gauge value
    """
    name: str
    help: str = ""
    labels: Tuple[str, ...] = ()
    values: Dict[str, float] = field(default_factory=dict)
    
    def set(self, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Set the gauge value."""
        key = self._labels_key(labels)
        self.values[key] = value
    
    def inc(self, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment the gauge."""
        key = self._labels_key(labels)
        if key not in self.values:
            self.values[key] = 0.0
        self.values[key] += value
    
    def dec(self, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """Decrement the gauge."""
        self.inc(-value, labels)
    
    def get(self, labels: Optional[Dict[str, str]] = None) -> float:
        """Get gauge value."""
        key = self._labels_key(labels)
        return self.values.get(key, 0.0)
    
    def _labels_key(self, labels: Optional[Dict[str, str]]) -> str:
        """Create hashable key from labels."""
        if not labels:
            return ""
        return ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
    
    def expose(self) -> str:
        """Generate Prometheus format text."""
        lines = []
        if self.help:
            lines.append(f"# HELP {self.name} {self.help}")
        lines.append(f"# TYPE {self.name} gauge")
        
        for label_key, value in self.values.items():
            if label_key:
                lines.append(f"{self.name}{{{label_key}}} {value}")
            else:
                lines.append(f"{self.name} {value}")
        
        return "\n".join(lines)


@dataclass
class PrometheusHistogram:
    """A Prometheus histogram metric.
    
    Histograms track distributions using buckets plus sum and count.
    
    Example output:
        metric_bucket{le="0.01"} 5
        metric_bucket{le="0.1"} 15
        metric_bucket{le="+Inf"} 20
        metric_sum 2.5
        metric_count 20
    
    Attributes:
        name: Metric name
        help: Description text
        labels: Set of label names this histogram uses
        buckets: Upper bounds for histogram buckets
        observations: Map of label values -> list of observations
    """
    name: str
    help: str = ""
    labels: Tuple[str, ...] = ()
    buckets: Tuple[float, ...] = DEFAULT_BUCKETS
    observations: Dict[str, List[float]] = field(default_factory=dict)
    
    def observe(self, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record an observation."""
        key = self._labels_key(labels)
        if key not in self.observations:
            self.observations[key] = []
        self.observations[key].append(value)
    
    def get_observations(self, labels: Optional[Dict[str, str]] = None) -> List[float]:
        """Get all observations."""
        key = self._labels_key(labels)
        return list(self.observations.get(key, []))
    
    def _labels_key(self, labels: Optional[Dict[str, str]]) -> str:
        """Create hashable key from labels."""
        if not labels:
            return ""
        return ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
    
    def _compute_buckets(self, observations: List[float]) -> Dict[float, int]:
        """Compute bucket counts."""
        bucket_counts = {b: 0 for b in self.buckets}
        bucket_counts[float("inf")] = 0
        
        for obs in observations:
            for bucket in self.buckets:
                if obs <= bucket:
                    bucket_counts[bucket] += 1
            bucket_counts[float("inf")] += 1
        
        return bucket_counts
    
    def expose(self) -> str:
        """Generate Prometheus format text."""
        lines = []
        if self.help:
            lines.append(f"# HELP {self.name} {self.help}")
        lines.append(f"# TYPE {self.name} histogram")
        
        for label_key, obs in self.observations.items():
            bucket_counts = self._compute_buckets(obs)
            
            # Bucket lines
            cumulative = 0
            for bucket in sorted(self.buckets):
                cumulative += bucket_counts[bucket]
                if label_key:
                    lines.append(f'{self.name}_bucket{{{label_key},le="{bucket}"}} {cumulative}')
                else:
                    lines.append(f'{self.name}_bucket{{le="{bucket}"}} {cumulative}')
            
            # +Inf bucket
            total = len(obs)
            if label_key:
                lines.append(f'{self.name}_bucket{{{label_key},le="+Inf"}} {total}')
            else:
                lines.append(f'{self.name}_bucket{{le="+Inf"}} {total}')
            
            # Sum
            obs_sum = sum(obs) if obs else 0
            if label_key:
                lines.append(f"{self.name}_sum{{{label_key}}} {obs_sum}")
            else:
                lines.append(f"{self.name}_sum {obs_sum}")
            
            # Count
            if label_key:
                lines.append(f"{self.name}_count{{{label_key}}} {total}")
            else:
                lines.append(f"{self.name}_count {total}")
        
        return "\n".join(lines)


# ============================================================================
# Prometheus Registry
# ============================================================================

class PrometheusRegistry:
    """Registry for Prometheus metrics.
    
    Manages the collection of all metrics and provides
    thread-safe access and exposition.
    
    Example:
        registry = PrometheusRegistry()
        registry.register_counter("requests_total", "Total requests")
        registry.counter_inc("requests_total", labels={"method": "GET"})
        output = registry.expose()
    """
    
    def __init__(self, buckets: Tuple[float, ...] = DEFAULT_BUCKETS):
        """Initialize registry.
        
        Args:
            buckets: Default histogram buckets
        """
        self._lock = threading.Lock()
        self._counters: Dict[str, PrometheusCounter] = {}
        self._gauges: Dict[str, PrometheusGauge] = {}
        self._histograms: Dict[str, PrometheusHistogram] = {}
        self._buckets = buckets
    
    def register_counter(
        self,
        name: str,
        help: str = "",
        labels: Tuple[str, ...] = (),
    ) -> PrometheusCounter:
        """Register a new counter."""
        with self._lock:
            if name not in self._counters:
                self._counters[name] = PrometheusCounter(
                    name=name,
                    help=help,
                    labels=labels,
                )
            return self._counters[name]
    
    def register_gauge(
        self,
        name: str,
        help: str = "",
        labels: Tuple[str, ...] = (),
    ) -> PrometheusGauge:
        """Register a new gauge."""
        with self._lock:
            if name not in self._gauges:
                self._gauges[name] = PrometheusGauge(
                    name=name,
                    help=help,
                    labels=labels,
                )
            return self._gauges[name]
    
    def register_histogram(
        self,
        name: str,
        help: str = "",
        labels: Tuple[str, ...] = (),
        buckets: Optional[Tuple[float, ...]] = None,
    ) -> PrometheusHistogram:
        """Register a new histogram."""
        with self._lock:
            if name not in self._histograms:
                self._histograms[name] = PrometheusHistogram(
                    name=name,
                    help=help,
                    labels=labels,
                    buckets=buckets or self._buckets,
                )
            return self._histograms[name]
    
    def counter_inc(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Increment a counter."""
        with self._lock:
            if name not in self._counters:
                self._counters[name] = PrometheusCounter(name=name)
            self._counters[name].inc(value, labels)
    
    def gauge_set(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Set a gauge value."""
        with self._lock:
            if name not in self._gauges:
                self._gauges[name] = PrometheusGauge(name=name)
            self._gauges[name].set(value, labels)
    
    def histogram_observe(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Record a histogram observation."""
        with self._lock:
            if name not in self._histograms:
                self._histograms[name] = PrometheusHistogram(
                    name=name,
                    buckets=self._buckets,
                )
            self._histograms[name].observe(value, labels)
    
    def get_counter(self, name: str) -> Optional[PrometheusCounter]:
        """Get a counter by name."""
        with self._lock:
            return self._counters.get(name)
    
    def get_gauge(self, name: str) -> Optional[PrometheusGauge]:
        """Get a gauge by name."""
        with self._lock:
            return self._gauges.get(name)
    
    def get_histogram(self, name: str) -> Optional[PrometheusHistogram]:
        """Get a histogram by name."""
        with self._lock:
            return self._histograms.get(name)
    
    def expose(self) -> str:
        """Generate Prometheus text exposition format.
        
        Returns:
            String in Prometheus format ready to serve at /metrics
        """
        with self._lock:
            sections = []
            
            # Counters
            for counter in self._counters.values():
                if counter.values:
                    sections.append(counter.expose())
            
            # Gauges
            for gauge in self._gauges.values():
                if gauge.values:
                    sections.append(gauge.expose())
            
            # Histograms
            for histogram in self._histograms.values():
                if histogram.observations:
                    sections.append(histogram.expose())
            
            return "\n\n".join(sections)
    
    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics as a dictionary."""
        with self._lock:
            return {
                "counters": {
                    name: dict(counter.values)
                    for name, counter in self._counters.items()
                },
                "gauges": {
                    name: dict(gauge.values)
                    for name, gauge in self._gauges.items()
                },
                "histograms": {
                    name: {
                        key: {
                            "observations": list(obs),
                            "count": len(obs),
                            "sum": sum(obs) if obs else 0,
                        }
                        for key, obs in hist.observations.items()
                    }
                    for name, hist in self._histograms.items()
                },
            }


# ============================================================================
# Prometheus Backend
# ============================================================================

class PrometheusBackend(MetricsBackend):
    """Prometheus metrics backend.
    
    Implements the MetricsBackend interface for Prometheus-compatible
    metrics export. Uses a PrometheusRegistry internally.
    
    Example:
        config = MetricsConfig(backend=BackendType.PROMETHEUS)
        backend = PrometheusBackend(config)
        
        backend.counter_inc("requests_total", labels={"method": "GET"})
        
        # Get Prometheus format output
        output = backend.expose()
    """
    
    def __init__(self, config: Optional[MetricsConfig] = None):
        """Initialize Prometheus backend.
        
        Args:
            config: Metrics configuration
        """
        self._config = config or MetricsConfig()
        self._registry = PrometheusRegistry(self._config.buckets)
        
        # Register standard database metrics
        self._register_standard_metrics()
    
    def _register_standard_metrics(self) -> None:
        """Register standard database metrics."""
        for name, definition in STANDARD_METRICS.items():
            full_name = f"{self._config.prefix}_{name}"
            
            if definition.type == MetricType.COUNTER:
                self._registry.register_counter(
                    full_name,
                    definition.description,
                    definition.labels,
                )
            elif definition.type == MetricType.GAUGE:
                self._registry.register_gauge(
                    full_name,
                    definition.description,
                    definition.labels,
                )
            elif definition.type == MetricType.HISTOGRAM:
                self._registry.register_histogram(
                    full_name,
                    definition.description,
                    definition.labels,
                    self._config.buckets,
                )
    
    def counter_inc(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Increment a counter."""
        self._registry.counter_inc(name, value, labels)
    
    def gauge_set(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Set a gauge value."""
        self._registry.gauge_set(name, value, labels)
    
    def histogram_observe(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Record a histogram observation."""
        self._registry.histogram_observe(name, value, labels)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics as a dictionary."""
        return self._registry.get_metrics()
    
    def reset(self) -> None:
        """Reset all metrics."""
        self._registry.reset()
    
    def expose(self) -> str:
        """Generate Prometheus text exposition format.
        
        This is the main method for serving metrics at /metrics.
        
        Returns:
            String in Prometheus text format
        
        Example output:
            # HELP pynext_db_queries_total Total queries
            # TYPE pynext_db_queries_total counter
            pynext_db_queries_total{query_type="SELECT",table="users"} 1234
        """
        return self._registry.expose()
    
    def get_content_type(self) -> str:
        """Get the Content-Type header for Prometheus format.
        
        Returns:
            "text/plain; version=0.0.4; charset=utf-8"
        """
        return "text/plain; version=0.0.4; charset=utf-8"
    
    def get_registry(self) -> PrometheusRegistry:
        """Get the underlying registry."""
        return self._registry


# ============================================================================
# Convenience Functions
# ============================================================================

def create_prometheus_backend(
    prefix: str = "pynext_db",
    buckets: Tuple[float, ...] = DEFAULT_BUCKETS,
) -> PrometheusBackend:
    """Create a Prometheus backend with common options.
    
    Args:
        prefix: Metric name prefix
        buckets: Histogram bucket boundaries
    
    Returns:
        Configured PrometheusBackend instance
    """
    config = MetricsConfig(prefix=prefix, buckets=buckets)
    return PrometheusBackend(config)


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # Metric types
    "PrometheusCounter",
    "PrometheusGauge",
    "PrometheusHistogram",
    
    # Registry
    "PrometheusRegistry",
    
    # Backend
    "PrometheusBackend",
    
    # Convenience
    "create_prometheus_backend",
]

