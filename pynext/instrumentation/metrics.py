"""
Metrics - Prometheus-Compatible Metrics Collection

Simple API for defining and recording metrics.
Supports counters, gauges, and histograms.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union
from enum import Enum


class MetricType(str, Enum):
    """Types of metrics."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


@dataclass
class MetricValue:
    """
    A single metric value with labels.
    
    Attributes:
        value: Numeric value
        labels: Label key-value pairs
        timestamp: Recording timestamp
    """
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class Counter:
    """
    A counter metric that only increases.
    
    Example:
        requests = Counter("http_requests_total", "Total HTTP requests")
        requests.inc()
        requests.inc(labels={"method": "GET", "path": "/"})
    """
    
    def __init__(
        self,
        name: str,
        description: str = "",
        labels: Optional[List[str]] = None,
    ):
        self.name = name
        self.description = description
        self.label_names = labels or []
        self._values: Dict[tuple, float] = {}
    
    def inc(
        self,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None,
    ):
        """
        Increment the counter.
        
        Args:
            value: Amount to increment (must be positive)
            labels: Label values
        """
        if value < 0:
            raise ValueError("Counter can only increase")
        
        key = self._label_key(labels)
        self._values[key] = self._values.get(key, 0) + value
    
    def get(self, labels: Optional[Dict[str, str]] = None) -> float:
        """Get current counter value."""
        key = self._label_key(labels)
        return self._values.get(key, 0)
    
    def _label_key(self, labels: Optional[Dict[str, str]]) -> tuple:
        """Create hashable key from labels."""
        if not labels:
            return ()
        return tuple(sorted(labels.items()))
    
    def collect(self) -> List[MetricValue]:
        """Collect all values for export."""
        return [
            MetricValue(
                value=value,
                labels=dict(key) if key else {},
            )
            for key, value in self._values.items()
        ]


class Gauge:
    """
    A gauge metric that can increase or decrease.
    
    Example:
        temperature = Gauge("temperature_celsius", "Current temperature")
        temperature.set(23.5)
        temperature.inc()
        temperature.dec(0.5)
    """
    
    def __init__(
        self,
        name: str,
        description: str = "",
        labels: Optional[List[str]] = None,
    ):
        self.name = name
        self.description = description
        self.label_names = labels or []
        self._values: Dict[tuple, float] = {}
    
    def set(
        self,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ):
        """Set gauge to a specific value."""
        key = self._label_key(labels)
        self._values[key] = value
    
    def inc(
        self,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None,
    ):
        """Increment the gauge."""
        key = self._label_key(labels)
        self._values[key] = self._values.get(key, 0) + value
    
    def dec(
        self,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None,
    ):
        """Decrement the gauge."""
        key = self._label_key(labels)
        self._values[key] = self._values.get(key, 0) - value
    
    def get(self, labels: Optional[Dict[str, str]] = None) -> float:
        """Get current gauge value."""
        key = self._label_key(labels)
        return self._values.get(key, 0)
    
    def _label_key(self, labels: Optional[Dict[str, str]]) -> tuple:
        """Create hashable key from labels."""
        if not labels:
            return ()
        return tuple(sorted(labels.items()))
    
    def collect(self) -> List[MetricValue]:
        """Collect all values for export."""
        return [
            MetricValue(
                value=value,
                labels=dict(key) if key else {},
            )
            for key, value in self._values.items()
        ]


class Histogram:
    """
    A histogram metric for distributions.
    
    Records observations in buckets for percentile calculation.
    
    Example:
        latency = Histogram(
            "request_latency_seconds",
            "Request latency",
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0],
        )
        
        with latency.time():
            process_request()
    """
    
    DEFAULT_BUCKETS = [
        0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5,
        0.75, 1.0, 2.5, 5.0, 7.5, 10.0, float("inf"),
    ]
    
    def __init__(
        self,
        name: str,
        description: str = "",
        labels: Optional[List[str]] = None,
        buckets: Optional[List[float]] = None,
    ):
        self.name = name
        self.description = description
        self.label_names = labels or []
        self.buckets = sorted(buckets or self.DEFAULT_BUCKETS)
        
        self._counts: Dict[tuple, Dict[float, int]] = {}
        self._sums: Dict[tuple, float] = {}
        self._totals: Dict[tuple, int] = {}
    
    def observe(
        self,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ):
        """
        Record an observation.
        
        Args:
            value: Observed value
            labels: Label values
        """
        key = self._label_key(labels)
        
        # Initialize if needed
        if key not in self._counts:
            self._counts[key] = {b: 0 for b in self.buckets}
            self._sums[key] = 0
            self._totals[key] = 0
        
        # Increment bucket counts
        for bucket in self.buckets:
            if value <= bucket:
                self._counts[key][bucket] += 1
        
        self._sums[key] += value
        self._totals[key] += 1
    
    def time(self, labels: Optional[Dict[str, str]] = None):
        """
        Context manager to time a block of code.
        
        Returns:
            Timer context manager
        """
        return _HistogramTimer(self, labels)
    
    def get_sum(self, labels: Optional[Dict[str, str]] = None) -> float:
        """Get sum of all observations."""
        key = self._label_key(labels)
        return self._sums.get(key, 0)
    
    def get_count(self, labels: Optional[Dict[str, str]] = None) -> int:
        """Get count of observations."""
        key = self._label_key(labels)
        return self._totals.get(key, 0)
    
    def _label_key(self, labels: Optional[Dict[str, str]]) -> tuple:
        """Create hashable key from labels."""
        if not labels:
            return ()
        return tuple(sorted(labels.items()))
    
    def collect(self) -> List[MetricValue]:
        """Collect all values for export."""
        values = []
        
        for key in self._counts:
            labels = dict(key) if key else {}
            
            # Bucket values
            for bucket, count in self._counts[key].items():
                values.append(MetricValue(
                    value=count,
                    labels={**labels, "le": str(bucket)},
                ))
            
            # Sum
            values.append(MetricValue(
                value=self._sums[key],
                labels={**labels, "__type": "sum"},
            ))
            
            # Count
            values.append(MetricValue(
                value=self._totals[key],
                labels={**labels, "__type": "count"},
            ))
        
        return values


class _HistogramTimer:
    """Timer context manager for histograms."""
    
    def __init__(self, histogram: Histogram, labels: Optional[Dict[str, str]]):
        self.histogram = histogram
        self.labels = labels
        self.start_time: float = 0
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        self.histogram.observe(duration, self.labels)
        return False


# Global metric registry
_metrics: Dict[str, Union[Counter, Gauge, Histogram]] = {}


def get_metrics() -> Dict[str, Union[Counter, Gauge, Histogram]]:
    """Get all registered metrics."""
    return _metrics.copy()


def counter(
    name: str,
    description: str = "",
    labels: Optional[List[str]] = None,
) -> Counter:
    """
    Create or get a counter metric.
    
    Args:
        name: Metric name
        description: Metric description
        labels: Label names
        
    Returns:
        Counter instance
    """
    if name in _metrics:
        return _metrics[name]  # type: ignore
    
    c = Counter(name, description, labels)
    _metrics[name] = c
    return c


def gauge(
    name: str,
    description: str = "",
    labels: Optional[List[str]] = None,
) -> Gauge:
    """
    Create or get a gauge metric.
    
    Args:
        name: Metric name
        description: Metric description
        labels: Label names
        
    Returns:
        Gauge instance
    """
    if name in _metrics:
        return _metrics[name]  # type: ignore
    
    g = Gauge(name, description, labels)
    _metrics[name] = g
    return g


def histogram(
    name: str,
    description: str = "",
    labels: Optional[List[str]] = None,
    buckets: Optional[List[float]] = None,
) -> Histogram:
    """
    Create or get a histogram metric.
    
    Args:
        name: Metric name
        description: Metric description
        labels: Label names
        buckets: Histogram buckets
        
    Returns:
        Histogram instance
    """
    if name in _metrics:
        return _metrics[name]  # type: ignore
    
    h = Histogram(name, description, labels, buckets)
    _metrics[name] = h
    return h


def metric(
    name: str,
    type: str = "counter",
    description: str = "",
    labels: Optional[List[str]] = None,
    **kwargs,
) -> Union[Counter, Gauge, Histogram]:
    """
    Create a metric by type string.
    
    Args:
        name: Metric name
        type: "counter", "gauge", or "histogram"
        description: Metric description
        labels: Label names
        **kwargs: Additional arguments for specific metric types
        
    Returns:
        Metric instance
        
    Example:
        page_views = metric("page_views", type="counter")
        page_views.inc()
    """
    if type == "counter":
        return counter(name, description, labels)
    elif type == "gauge":
        return gauge(name, description, labels)
    elif type == "histogram":
        return histogram(name, description, labels, kwargs.get("buckets"))
    else:
        raise ValueError(f"Unknown metric type: {type}")


def configure_metrics(config):
    """Configure metrics with InstrumentConfig."""
    # Set up any global metric configuration
    pass


def export_prometheus() -> str:
    """
    Export all metrics in Prometheus format.
    
    Returns:
        Prometheus text format string
    """
    lines = []
    
    for name, metric in _metrics.items():
        # Type declaration
        if isinstance(metric, Counter):
            lines.append(f"# TYPE {name} counter")
        elif isinstance(metric, Gauge):
            lines.append(f"# TYPE {name} gauge")
        elif isinstance(metric, Histogram):
            lines.append(f"# TYPE {name} histogram")
        
        # Description
        if metric.description:
            lines.append(f"# HELP {name} {metric.description}")
        
        # Values
        for value in metric.collect():
            label_str = ""
            if value.labels:
                label_pairs = [f'{k}="{v}"' for k, v in value.labels.items()]
                label_str = "{" + ",".join(label_pairs) + "}"
            
            lines.append(f"{name}{label_str} {value.value}")
    
    return "\n".join(lines)

