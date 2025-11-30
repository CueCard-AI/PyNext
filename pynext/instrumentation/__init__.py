"""
PyNext Instrumentation - Observability Made Simple

Add traces, metrics, and structured logging with
simple decorators. Zero-config defaults, full
customization when needed.

Usage:
    # instrumentation.py - Auto-discovered
    from pynext import instrument, trace, metric, log
    
    @instrument(traces=True, metrics=True)
    def configure():
        return {
            "service_name": "my-app",
            "exporter": "otlp",
        }
    
    # Per-route tracing
    @trace("fetch-users")
    async def get_users():
        return await db.users.find_all()
    
    # Custom metrics
    page_views = metric("page_views", type="counter")
    page_views.inc()
    
    # Structured logging
    log.info("User action", user_id=123, action="login")

Features:
- OpenTelemetry traces
- Prometheus-compatible metrics
- Structured JSON logging
- Multiple exporters (OTLP, Jaeger, Console)
"""

from .config import (
    InstrumentConfig,
    instrument,
    configure_instrumentation,
    get_config,
)
from .traces import (
    Tracer,
    Span,
    trace,
    get_tracer,
    get_current_span,
)
from .metrics import (
    Counter,
    Gauge,
    Histogram,
    metric,
    counter,
    gauge,
    histogram,
    get_metrics,
)
from .logs import (
    Logger,
    log,
    get_logger,
    configure_logging,
)

__all__ = [
    # Config
    "InstrumentConfig",
    "instrument",
    "configure_instrumentation",
    "get_config",
    # Traces
    "Tracer",
    "Span",
    "trace",
    "get_tracer",
    "get_current_span",
    # Metrics
    "Counter",
    "Gauge",
    "Histogram",
    "metric",
    "counter",
    "gauge",
    "histogram",
    "get_metrics",
    # Logs
    "Logger",
    "log",
    "get_logger",
    "configure_logging",
]

