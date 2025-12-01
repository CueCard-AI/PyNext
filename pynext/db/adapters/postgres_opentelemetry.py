"""
PyNext OpenTelemetry Backend Module.

Provides OpenTelemetry-compatible metrics and tracing export for
database operations. Supports OTLP protocol for exporting to
various observability backends.

OpenTelemetry Overview:
──────────────────────
OpenTelemetry is a vendor-neutral observability framework that provides:
- Metrics (counters, gauges, histograms)
- Traces (spans with timing and context)
- Logs (structured log events)

This module focuses on metrics and tracing for database operations.

Trace Structure:
    [Request Trace]
    └── [Database Span]
        ├── db.system: postgresql
        ├── db.name: mydb
        ├── db.operation: SELECT
        ├── db.statement: SELECT * FROM users
        └── duration: 15ms

Usage:
    from pynext.db.adapters.postgres_opentelemetry import OpenTelemetryBackend
    
    backend = OpenTelemetryBackend()
    backend.counter_inc("queries_total", labels={"query_type": "SELECT"})
    
    # Start a span for a query
    with backend.span("SELECT * FROM users") as span:
        # Execute query
        pass

AI-Friendly Design:
- Standard OpenTelemetry semantics
- Thread-safe operations
- Follows semantic conventions for databases
"""

from __future__ import annotations

import threading
import time
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from .postgres_metrics import (
    MetricsBackend,
    MetricsConfig,
    DEFAULT_BUCKETS,
)


# ============================================================================
# Context Variables for Tracing
# ============================================================================

_current_span: ContextVar[Optional["Span"]] = ContextVar("current_span", default=None)
_trace_context: ContextVar[Optional["TraceContext"]] = ContextVar("trace_context", default=None)


# ============================================================================
# Span and Trace Classes
# ============================================================================

class SpanKind(str, Enum):
    """Types of spans."""
    CLIENT = "client"       # Outgoing request (our DB queries)
    SERVER = "server"       # Incoming request
    INTERNAL = "internal"   # Internal operation


class SpanStatus(str, Enum):
    """Span status codes."""
    UNSET = "unset"
    OK = "ok"
    ERROR = "error"


@dataclass
class TraceContext:
    """Context for distributed tracing.
    
    Propagates trace information across service boundaries.
    
    Attributes:
        trace_id: 32-character hex string
        span_id: 16-character hex string
        trace_flags: Trace flags (sampling, etc.)
        trace_state: Additional vendor-specific state
    """
    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    span_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    trace_flags: int = 1  # Sampled
    trace_state: Dict[str, str] = field(default_factory=dict)
    
    def to_traceparent(self) -> str:
        """Generate W3C Trace Context traceparent header.
        
        Format: {version}-{trace_id}-{span_id}-{flags}
        Example: 00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01
        """
        return f"00-{self.trace_id}-{self.span_id}-{self.trace_flags:02x}"
    
    @classmethod
    def from_traceparent(cls, header: str) -> Optional["TraceContext"]:
        """Parse W3C Trace Context traceparent header."""
        try:
            parts = header.split("-")
            if len(parts) != 4 or parts[0] != "00":
                return None
            return cls(
                trace_id=parts[1],
                span_id=parts[2],
                trace_flags=int(parts[3], 16),
            )
        except (ValueError, IndexError):
            return None


@dataclass
class Span:
    """A trace span representing a database operation.
    
    Spans track the execution of a single operation with timing,
    attributes, and status information.
    
    Attributes:
        name: Span name (usually the operation type)
        trace_id: Parent trace ID
        span_id: This span's ID
        parent_span_id: Parent span ID (if nested)
        kind: Type of span (client, server, internal)
        start_time: When the span started
        end_time: When the span ended
        status: Span status (ok, error, unset)
        attributes: Key-value attributes
        events: List of events during the span
    """
    name: str
    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    span_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    parent_span_id: Optional[str] = None
    kind: SpanKind = SpanKind.CLIENT
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    status: SpanStatus = SpanStatus.UNSET
    status_message: str = ""
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    
    # Database semantic conventions
    _DB_ATTRIBUTES = {
        "db.system": "postgresql",
        "db.connection_string": None,
        "db.name": None,
        "db.operation": None,
        "db.statement": None,
        "db.sql.table": None,
    }
    
    def set_attribute(self, key: str, value: Any) -> None:
        """Set a span attribute."""
        self.attributes[key] = value
    
    def set_db_attributes(
        self,
        operation: Optional[str] = None,
        statement: Optional[str] = None,
        table: Optional[str] = None,
        database: Optional[str] = None,
    ) -> None:
        """Set database-specific attributes following semantic conventions."""
        self.attributes["db.system"] = "postgresql"
        if operation:
            self.attributes["db.operation"] = operation
        if statement:
            self.attributes["db.statement"] = statement
        if table:
            self.attributes["db.sql.table"] = table
        if database:
            self.attributes["db.name"] = database
    
    def add_event(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add an event to the span."""
        self.events.append({
            "name": name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "attributes": attributes or {},
        })
    
    def set_status(self, status: SpanStatus, message: str = "") -> None:
        """Set the span status."""
        self.status = status
        self.status_message = message
    
    def end(self, status: Optional[SpanStatus] = None) -> None:
        """End the span."""
        self.end_time = datetime.now(timezone.utc)
        if status:
            self.status = status
        elif self.status == SpanStatus.UNSET:
            self.status = SpanStatus.OK
    
    @property
    def duration_ms(self) -> float:
        """Get span duration in milliseconds."""
        if not self.end_time:
            return 0.0
        delta = self.end_time - self.start_time
        return delta.total_seconds() * 1000
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dictionary."""
        return {
            "name": self.name,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "kind": self.kind.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "status": self.status.value,
            "status_message": self.status_message,
            "attributes": self.attributes,
            "events": self.events,
        }


class SpanContext:
    """Context manager for spans."""
    
    def __init__(self, span: Span, backend: "OpenTelemetryBackend"):
        self.span = span
        self.backend = backend
        self._token = None
    
    def __enter__(self) -> Span:
        self._token = _current_span.set(self.span)
        return self.span
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            self.span.set_status(SpanStatus.ERROR, str(exc_val))
            self.span.add_event("exception", {
                "exception.type": type(exc_val).__name__,
                "exception.message": str(exc_val),
            })
        self.span.end()
        self.backend._record_span(self.span)
        if self._token:
            _current_span.reset(self._token)
    
    async def __aenter__(self) -> Span:
        return self.__enter__()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return self.__exit__(exc_type, exc_val, exc_tb)


# ============================================================================
# OpenTelemetry Metrics (In-Memory Implementation)
# ============================================================================

@dataclass
class OTelCounter:
    """OpenTelemetry counter implementation."""
    name: str
    description: str = ""
    unit: str = ""
    values: Dict[str, float] = field(default_factory=dict)
    
    def add(self, value: float = 1.0, attributes: Optional[Dict[str, str]] = None) -> None:
        key = self._attrs_key(attributes)
        if key not in self.values:
            self.values[key] = 0.0
        self.values[key] += value
    
    def get(self, attributes: Optional[Dict[str, str]] = None) -> float:
        return self.values.get(self._attrs_key(attributes), 0.0)
    
    def _attrs_key(self, attrs: Optional[Dict[str, str]]) -> str:
        if not attrs:
            return ""
        return ",".join(f"{k}={v}" for k, v in sorted(attrs.items()))


@dataclass
class OTelGauge:
    """OpenTelemetry gauge implementation."""
    name: str
    description: str = ""
    unit: str = ""
    values: Dict[str, float] = field(default_factory=dict)
    
    def set(self, value: float, attributes: Optional[Dict[str, str]] = None) -> None:
        key = self._attrs_key(attributes)
        self.values[key] = value
    
    def get(self, attributes: Optional[Dict[str, str]] = None) -> float:
        return self.values.get(self._attrs_key(attributes), 0.0)
    
    def _attrs_key(self, attrs: Optional[Dict[str, str]]) -> str:
        if not attrs:
            return ""
        return ",".join(f"{k}={v}" for k, v in sorted(attrs.items()))


@dataclass
class OTelHistogram:
    """OpenTelemetry histogram implementation."""
    name: str
    description: str = ""
    unit: str = ""
    boundaries: Tuple[float, ...] = DEFAULT_BUCKETS
    observations: Dict[str, List[float]] = field(default_factory=dict)
    
    def record(self, value: float, attributes: Optional[Dict[str, str]] = None) -> None:
        key = self._attrs_key(attributes)
        if key not in self.observations:
            self.observations[key] = []
        self.observations[key].append(value)
    
    def get_observations(self, attributes: Optional[Dict[str, str]] = None) -> List[float]:
        return list(self.observations.get(self._attrs_key(attributes), []))
    
    def _attrs_key(self, attrs: Optional[Dict[str, str]]) -> str:
        if not attrs:
            return ""
        return ",".join(f"{k}={v}" for k, v in sorted(attrs.items()))


# ============================================================================
# OpenTelemetry Backend
# ============================================================================

class OpenTelemetryBackend(MetricsBackend):
    """OpenTelemetry metrics and tracing backend.
    
    Provides OpenTelemetry-compatible metrics collection and
    tracing for database operations.
    
    This is an in-memory implementation that can be extended
    to export via OTLP to various backends (Jaeger, Zipkin, etc.).
    
    Example:
        backend = OpenTelemetryBackend()
        
        # Metrics
        backend.counter_inc("queries_total", labels={"type": "SELECT"})
        
        # Tracing
        with backend.span("SELECT * FROM users") as span:
            span.set_db_attributes(operation="SELECT", table="users")
            # Execute query
    """
    
    def __init__(self, config: Optional[MetricsConfig] = None):
        """Initialize OpenTelemetry backend.
        
        Args:
            config: Metrics configuration
        """
        self._config = config or MetricsConfig()
        self._lock = threading.Lock()
        
        # Metrics
        self._counters: Dict[str, OTelCounter] = {}
        self._gauges: Dict[str, OTelGauge] = {}
        self._histograms: Dict[str, OTelHistogram] = {}
        
        # Traces
        self._spans: List[Span] = []
        self._max_spans = 10000  # Limit stored spans
    
    # ========================================================================
    # Metrics Backend Interface
    # ========================================================================
    
    def counter_inc(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Increment a counter."""
        with self._lock:
            if name not in self._counters:
                self._counters[name] = OTelCounter(name=name)
            self._counters[name].add(value, labels)
    
    def gauge_set(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Set a gauge value."""
        with self._lock:
            if name not in self._gauges:
                self._gauges[name] = OTelGauge(name=name)
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
                self._histograms[name] = OTelHistogram(
                    name=name,
                    boundaries=self._config.buckets,
                )
            self._histograms[name].record(value, labels)
    
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
    
    def reset(self) -> None:
        """Reset all metrics and traces."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._spans.clear()
    
    # ========================================================================
    # Tracing
    # ========================================================================
    
    def span(
        self,
        name: str,
        kind: SpanKind = SpanKind.CLIENT,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> SpanContext:
        """Create a new span.
        
        Args:
            name: Span name (e.g., query text or operation)
            kind: Type of span
            attributes: Initial attributes
        
        Returns:
            SpanContext that can be used as a context manager
        
        Example:
            with backend.span("SELECT * FROM users") as span:
                span.set_db_attributes(operation="SELECT", table="users")
                result = await execute_query(...)
        """
        # Get parent span if exists
        parent_span = _current_span.get()
        
        # Get or create trace context
        trace_ctx = _trace_context.get()
        if trace_ctx:
            trace_id = trace_ctx.trace_id
        elif parent_span:
            trace_id = parent_span.trace_id
        else:
            trace_id = uuid.uuid4().hex
        
        # Create new span
        span = Span(
            name=name,
            trace_id=trace_id,
            span_id=uuid.uuid4().hex[:16],
            parent_span_id=parent_span.span_id if parent_span else None,
            kind=kind,
            attributes=dict(attributes) if attributes else {},
        )
        
        return SpanContext(span, self)
    
    def start_span(
        self,
        name: str,
        kind: SpanKind = SpanKind.CLIENT,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Span:
        """Start a new span without context manager.
        
        Use this when you need manual span management.
        Remember to call span.end() when done.
        """
        parent_span = _current_span.get()
        trace_ctx = _trace_context.get()
        
        if trace_ctx:
            trace_id = trace_ctx.trace_id
        elif parent_span:
            trace_id = parent_span.trace_id
        else:
            trace_id = uuid.uuid4().hex
        
        span = Span(
            name=name,
            trace_id=trace_id,
            span_id=uuid.uuid4().hex[:16],
            parent_span_id=parent_span.span_id if parent_span else None,
            kind=kind,
            attributes=dict(attributes) if attributes else {},
        )
        
        _current_span.set(span)
        return span
    
    def end_span(self, span: Span) -> None:
        """End a span started with start_span."""
        span.end()
        self._record_span(span)
        _current_span.set(None)
    
    def _record_span(self, span: Span) -> None:
        """Record a completed span."""
        with self._lock:
            self._spans.append(span)
            # Limit stored spans
            if len(self._spans) > self._max_spans:
                self._spans = self._spans[-self._max_spans:]
    
    def get_spans(
        self,
        trace_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get recorded spans.
        
        Args:
            trace_id: Filter by trace ID
            limit: Maximum number of spans to return
        
        Returns:
            List of span dictionaries
        """
        with self._lock:
            spans = self._spans
            if trace_id:
                spans = [s for s in spans if s.trace_id == trace_id]
            return [s.to_dict() for s in spans[-limit:]]
    
    def get_current_span(self) -> Optional[Span]:
        """Get the currently active span."""
        return _current_span.get()
    
    # ========================================================================
    # Trace Context
    # ========================================================================
    
    def set_trace_context(self, context: TraceContext) -> None:
        """Set the trace context for propagation."""
        _trace_context.set(context)
    
    def get_trace_context(self) -> Optional[TraceContext]:
        """Get the current trace context."""
        return _trace_context.get()
    
    def inject_trace_headers(self) -> Dict[str, str]:
        """Get trace headers for propagation.
        
        Returns headers that can be passed to downstream services.
        """
        ctx = _trace_context.get()
        span = _current_span.get()
        
        if ctx:
            return {"traceparent": ctx.to_traceparent()}
        elif span:
            # Create context from current span
            ctx = TraceContext(trace_id=span.trace_id, span_id=span.span_id)
            return {"traceparent": ctx.to_traceparent()}
        
        return {}
    
    def extract_trace_headers(self, headers: Dict[str, str]) -> Optional[TraceContext]:
        """Extract trace context from headers.
        
        Args:
            headers: HTTP headers (case-insensitive)
        
        Returns:
            TraceContext if found, None otherwise
        """
        # Normalize header names to lowercase
        headers_lower = {k.lower(): v for k, v in headers.items()}
        
        traceparent = headers_lower.get("traceparent")
        if traceparent:
            return TraceContext.from_traceparent(traceparent)
        
        return None
    
    # ========================================================================
    # Database-Specific Helpers
    # ========================================================================
    
    def db_span(
        self,
        query: str,
        operation: Optional[str] = None,
        table: Optional[str] = None,
        database: Optional[str] = None,
    ) -> SpanContext:
        """Create a database-specific span with semantic attributes.
        
        Convenience method that sets appropriate database attributes.
        
        Args:
            query: SQL query text
            operation: Query type (SELECT, INSERT, etc.)
            table: Table name
            database: Database name
        
        Example:
            with backend.db_span("SELECT * FROM users", operation="SELECT", table="users"):
                # Execute query
                pass
        """
        span_ctx = self.span(query, SpanKind.CLIENT)
        span_ctx.span.set_db_attributes(
            operation=operation,
            statement=query,
            table=table,
            database=database,
        )
        return span_ctx


# ============================================================================
# Configuration
# ============================================================================

@dataclass
class OTLPConfig:
    """Configuration for OTLP export.
    
    For use with a real OpenTelemetry SDK.
    
    Attributes:
        endpoint: OTLP endpoint URL
        headers: Additional headers for authentication
        timeout_seconds: Export timeout
        compression: Compression type (none, gzip)
    """
    endpoint: str = "http://localhost:4317"
    headers: Dict[str, str] = field(default_factory=dict)
    timeout_seconds: float = 10.0
    compression: str = "none"


# ============================================================================
# Convenience Functions
# ============================================================================

def create_otel_backend(
    prefix: str = "pynext_db",
    buckets: Tuple[float, ...] = DEFAULT_BUCKETS,
) -> OpenTelemetryBackend:
    """Create an OpenTelemetry backend with common options.
    
    Args:
        prefix: Metric name prefix
        buckets: Histogram bucket boundaries
    
    Returns:
        Configured OpenTelemetryBackend instance
    """
    config = MetricsConfig(prefix=prefix, buckets=buckets)
    return OpenTelemetryBackend(config)


def get_current_trace_id() -> Optional[str]:
    """Get the current trace ID if in a span context."""
    span = _current_span.get()
    if span:
        return span.trace_id
    ctx = _trace_context.get()
    if ctx:
        return ctx.trace_id
    return None


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # Span types
    "SpanKind",
    "SpanStatus",
    "Span",
    "SpanContext",
    "TraceContext",
    
    # Metrics types
    "OTelCounter",
    "OTelGauge",
    "OTelHistogram",
    
    # Backend
    "OpenTelemetryBackend",
    "OTLPConfig",
    
    # Convenience
    "create_otel_backend",
    "get_current_trace_id",
]

