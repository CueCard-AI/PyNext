"""
Distributed Tracing - Track Request Flow

Simple decorator-based tracing that integrates with
OpenTelemetry for distributed trace collection.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union


@dataclass
class SpanContext:
    """
    Span context for distributed tracing.
    
    Attributes:
        trace_id: Unique trace identifier
        span_id: Unique span identifier
        parent_id: Parent span ID (if nested)
    """
    trace_id: str
    span_id: str
    parent_id: Optional[str] = None
    
    @classmethod
    def generate(cls, parent: Optional["SpanContext"] = None) -> "SpanContext":
        """Generate new span context."""
        return cls(
            trace_id=parent.trace_id if parent else uuid.uuid4().hex[:32],
            span_id=uuid.uuid4().hex[:16],
            parent_id=parent.span_id if parent else None,
        )


@dataclass
class Span:
    """
    A single span in a trace.
    
    Represents a unit of work with timing, attributes,
    and status information.
    
    Attributes:
        name: Span name
        context: Span context
        start_time: Start timestamp (nanoseconds)
        end_time: End timestamp (nanoseconds)
        attributes: Key-value attributes
        events: Span events
        status: Span status (ok, error)
    """
    name: str
    context: SpanContext
    start_time: int = 0
    end_time: int = 0
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "ok"
    error: Optional[Exception] = None
    
    def __enter__(self) -> "Span":
        """Start span."""
        self.start_time = time.time_ns()
        _current_span.set(self)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End span."""
        self.end_time = time.time_ns()
        
        if exc_val:
            self.status = "error"
            self.error = exc_val
            self.record_exception(exc_val)
        
        # Export span
        _export_span(self)
        
        # Restore parent span
        _current_span.set(None)
        
        return False
    
    @property
    def duration_ms(self) -> float:
        """Get duration in milliseconds."""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time) / 1_000_000
        return 0
    
    def set_attribute(self, key: str, value: Any):
        """Set a span attribute."""
        self.attributes[key] = value
    
    def add_event(self, name: str, attributes: Optional[Dict] = None):
        """Add an event to the span."""
        self.events.append({
            "name": name,
            "timestamp": time.time_ns(),
            "attributes": attributes or {},
        })
    
    def record_exception(self, exception: Exception):
        """Record an exception on the span."""
        self.add_event("exception", {
            "type": type(exception).__name__,
            "message": str(exception),
        })
    
    def set_status(self, status: str, description: str = ""):
        """Set span status."""
        self.status = status
        if description:
            self.attributes["status.description"] = description
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for export."""
        return {
            "name": self.name,
            "trace_id": self.context.trace_id,
            "span_id": self.context.span_id,
            "parent_id": self.context.parent_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "attributes": self.attributes,
            "events": self.events,
        }


# Context variable for current span
_current_span: ContextVar[Optional[Span]] = ContextVar("current_span", default=None)


def get_current_span() -> Optional[Span]:
    """Get the current active span."""
    return _current_span.get()


class Tracer:
    """
    Creates and manages spans.
    
    Example:
        tracer = Tracer("my-service")
        
        with tracer.start_span("operation") as span:
            span.set_attribute("key", "value")
            do_work()
    """
    
    def __init__(self, name: str):
        self.name = name
    
    @contextmanager
    def start_span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
    ):
        """
        Start a new span.
        
        Args:
            name: Span name
            attributes: Initial attributes
            
        Yields:
            Span object
        """
        parent = get_current_span()
        context = SpanContext.generate(parent.context if parent else None)
        
        span = Span(
            name=name,
            context=context,
            attributes={
                "service.name": self.name,
                **(attributes or {}),
            },
        )
        
        with span:
            yield span
    
    def start_as_current_span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
    ):
        """
        Decorator to wrap function in a span.
        
        Args:
            name: Span name
            attributes: Initial attributes
            
        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                with self.start_span(name, attributes) as span:
                    span.set_attribute("function", func.__name__)
                    return func(*args, **kwargs)
            
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                with self.start_span(name, attributes) as span:
                    span.set_attribute("function", func.__name__)
                    return await func(*args, **kwargs)
            
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper
        
        return decorator


# Global tracer
_tracer: Optional[Tracer] = None
_exporter: Optional[Callable] = None


def get_tracer(name: str = "pynext") -> Tracer:
    """Get or create a tracer."""
    global _tracer
    if _tracer is None or _tracer.name != name:
        _tracer = Tracer(name)
    return _tracer


def trace(
    name: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
) -> Callable:
    """
    Decorator to trace a function.
    
    Creates a span for the function execution with
    automatic timing and error recording.
    
    Args:
        name: Span name (defaults to function name)
        attributes: Initial attributes
        
    Returns:
        Decorator function
        
    Example:
        @trace("fetch-users")
        async def get_users():
            return await db.users.find_all()
        
        @trace()  # Uses function name
        def process_data(data):
            return transform(data)
    """
    def decorator(func: Callable) -> Callable:
        span_name = name or func.__name__
        tracer = get_tracer()
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            with tracer.start_span(span_name, attributes) as span:
                span.set_attribute("function", func.__name__)
                span.set_attribute("module", func.__module__)
                return func(*args, **kwargs)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            with tracer.start_span(span_name, attributes) as span:
                span.set_attribute("function", func.__name__)
                span.set_attribute("module", func.__module__)
                return await func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def configure_tracer(config):
    """Configure the tracer with InstrumentConfig."""
    global _tracer, _exporter
    
    from .config import Exporter
    
    _tracer = Tracer(config.service_name)
    
    # Set up exporter
    if config.exporter == Exporter.CONSOLE:
        _exporter = _console_exporter
    elif config.exporter == Exporter.OTLP:
        _exporter = _create_otlp_exporter(config.endpoint)
    else:
        _exporter = _console_exporter


def _export_span(span: Span):
    """Export a completed span."""
    if _exporter:
        _exporter(span)


def _console_exporter(span: Span):
    """Export span to console."""
    import json
    print(f"[TRACE] {json.dumps(span.to_dict(), indent=2)}")


def _create_otlp_exporter(endpoint: Optional[str]):
    """Create OTLP exporter."""
    # This would integrate with OpenTelemetry SDK
    # For now, return console exporter
    return _console_exporter

