"""
PostgreSQL Observability Features (Phase 5.5).

This module contains monitoring and logging components:
- logging.py: Structured logging with context
- metrics.py: Metrics collection framework
- prometheus.py: Prometheus metrics backend
- opentelemetry.py: OpenTelemetry tracing backend
- analyzer.py: Query analysis and optimization hints
- monitor.py: Pool health monitoring and leak detection
"""

from .logging import (
    LogConfig,
    QueryContext,
    DBLogger,
    LogLevel,
    LogFormat,
    LogEvent,
    LogRecord,
    QueryTracker,
    set_trace_id,
    get_trace_id,
    set_client_ip,
    get_client_ip,
)
from .metrics import (
    MetricsConfig,
    MetricsCollector,
    MetricsBackend,
    MetricType,
    BackendType,
    MetricDefinition,
    MemoryBackend,
    Timer,
)
from .prometheus import (
    PrometheusBackend,
    PrometheusCounter,
    PrometheusGauge,
    PrometheusHistogram,
    PrometheusRegistry,
)
from .opentelemetry import (
    OpenTelemetryBackend,
    OTLPConfig,
    SpanKind,
    SpanStatus,
    TraceContext,
    Span,
    SpanContext,
    OTelCounter,
    OTelGauge,
    OTelHistogram,
)
from .analyzer import (
    QueryAnalyzer,
    AnalyzerConfig,
    ExplainResult,
    SuggestionType,
    ScanType,
    ExplainNode,
    QuerySuggestion,
    AnalysisResult,
)
from .monitor import (
    PoolMonitor,
    MonitorConfig,
    LeakDetector,
    HealthChecker,
    PoolEventType,
    ConnectionState,
    ConnectionInfo,
    LeakInfo,
    PoolEvent,
    PoolStats,
)

__all__ = [
    # Logging
    "LogConfig",
    "QueryContext",
    "DBLogger",
    "LogLevel",
    "LogFormat",
    "LogEvent",
    "LogRecord",
    "QueryTracker",
    "set_trace_id",
    "get_trace_id",
    "set_client_ip",
    "get_client_ip",
    # Metrics
    "MetricsConfig",
    "MetricsCollector",
    "MetricsBackend",
    "MetricType",
    "BackendType",
    "MetricDefinition",
    "MemoryBackend",
    "Timer",
    # Prometheus
    "PrometheusBackend",
    "PrometheusCounter",
    "PrometheusGauge",
    "PrometheusHistogram",
    "PrometheusRegistry",
    # OpenTelemetry
    "OpenTelemetryBackend",
    "OTLPConfig",
    "SpanKind",
    "SpanStatus",
    "TraceContext",
    "Span",
    "SpanContext",
    "OTelCounter",
    "OTelGauge",
    "OTelHistogram",
    # Analyzer
    "QueryAnalyzer",
    "AnalyzerConfig",
    "ExplainResult",
    "SuggestionType",
    "ScanType",
    "ExplainNode",
    "QuerySuggestion",
    "AnalysisResult",
    # Monitor
    "PoolMonitor",
    "MonitorConfig",
    "LeakDetector",
    "HealthChecker",
    "PoolEventType",
    "ConnectionState",
    "ConnectionInfo",
    "LeakInfo",
    "PoolEvent",
    "PoolStats",
]

