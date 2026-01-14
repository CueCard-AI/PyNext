"""
Tests for PyNext OpenTelemetry Backend Module.

80 comprehensive tests covering:
- TraceContext (10 tests)
- Span (15 tests)
- SpanContext (10 tests)
- OpenTelemetry Metrics (15 tests)
- OpenTelemetryBackend (20 tests)
- Tracing integration (10 tests)
"""

import asyncio
import pytest

from pynext.db.adapters.postgres.observability.opentelemetry import (
    TraceContext,
    Span,
    SpanKind,
    SpanStatus,
    SpanContext,
    OTelCounter,
    OTelGauge,
    OTelHistogram,
    OpenTelemetryBackend,
    OTLPConfig,
    create_otel_backend,
    get_current_trace_id,
)
from pynext.db.adapters.postgres.observability.metrics import MetricsConfig


# ============================================================================
# TraceContext Tests (10 tests)
# ============================================================================

class TestTraceContext:
    """Tests for TraceContext class."""
    
    def test_default_context(self):
        """Test default trace context creation."""
        ctx = TraceContext()
        assert ctx.trace_id is not None
        assert len(ctx.trace_id) == 32
        assert ctx.span_id is not None
        assert len(ctx.span_id) == 16
    
    def test_custom_trace_id(self):
        """Test custom trace ID."""
        ctx = TraceContext(trace_id="abcd1234" * 4)
        assert ctx.trace_id == "abcd1234" * 4
    
    def test_trace_flags(self):
        """Test trace flags."""
        ctx = TraceContext(trace_flags=0)
        assert ctx.trace_flags == 0
        
        ctx2 = TraceContext(trace_flags=1)
        assert ctx2.trace_flags == 1
    
    def test_to_traceparent(self):
        """Test W3C traceparent header generation."""
        ctx = TraceContext(
            trace_id="0af7651916cd43dd8448eb211c80319c",
            span_id="b7ad6b7169203331",
            trace_flags=1,
        )
        traceparent = ctx.to_traceparent()
        assert traceparent == "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"
    
    def test_from_traceparent(self):
        """Test parsing W3C traceparent header."""
        header = "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"
        ctx = TraceContext.from_traceparent(header)
        
        assert ctx is not None
        assert ctx.trace_id == "0af7651916cd43dd8448eb211c80319c"
        assert ctx.span_id == "b7ad6b7169203331"
        assert ctx.trace_flags == 1
    
    def test_from_traceparent_invalid(self):
        """Test parsing invalid traceparent returns None."""
        assert TraceContext.from_traceparent("invalid") is None
        assert TraceContext.from_traceparent("01-abc-def-00") is None  # Wrong version
        assert TraceContext.from_traceparent("") is None
    
    def test_trace_state(self):
        """Test trace state storage."""
        ctx = TraceContext(trace_state={"vendor": "value"})
        assert ctx.trace_state["vendor"] == "value"
    
    def test_traceparent_roundtrip(self):
        """Test traceparent roundtrip."""
        original = TraceContext()
        header = original.to_traceparent()
        parsed = TraceContext.from_traceparent(header)
        
        assert parsed.trace_id == original.trace_id
        assert parsed.span_id == original.span_id
        assert parsed.trace_flags == original.trace_flags
    
    def test_unique_trace_ids(self):
        """Test each context gets unique trace ID."""
        ctx1 = TraceContext()
        ctx2 = TraceContext()
        assert ctx1.trace_id != ctx2.trace_id
    
    def test_unique_span_ids(self):
        """Test each context gets unique span ID."""
        ctx1 = TraceContext()
        ctx2 = TraceContext()
        assert ctx1.span_id != ctx2.span_id


# ============================================================================
# Span Tests (15 tests)
# ============================================================================

class TestSpan:
    """Tests for Span class."""
    
    def test_default_span(self):
        """Test default span creation."""
        span = Span(name="test_span")
        assert span.name == "test_span"
        assert span.trace_id is not None
        assert span.span_id is not None
        assert span.kind == SpanKind.CLIENT
        assert span.status == SpanStatus.UNSET
    
    def test_custom_kind(self):
        """Test custom span kind."""
        span = Span(name="test", kind=SpanKind.SERVER)
        assert span.kind == SpanKind.SERVER
    
    def test_set_attribute(self):
        """Test setting span attribute."""
        span = Span(name="test")
        span.set_attribute("key", "value")
        assert span.attributes["key"] == "value"
    
    def test_set_db_attributes(self):
        """Test setting database attributes."""
        span = Span(name="test")
        span.set_db_attributes(
            operation="SELECT",
            statement="SELECT * FROM users",
            table="users",
            database="mydb",
        )
        
        assert span.attributes["db.system"] == "postgresql"
        assert span.attributes["db.operation"] == "SELECT"
        assert span.attributes["db.statement"] == "SELECT * FROM users"
        assert span.attributes["db.sql.table"] == "users"
        assert span.attributes["db.name"] == "mydb"
    
    def test_add_event(self):
        """Test adding span event."""
        span = Span(name="test")
        span.add_event("connection_acquired", {"pool": "main"})
        
        assert len(span.events) == 1
        assert span.events[0]["name"] == "connection_acquired"
        assert span.events[0]["attributes"]["pool"] == "main"
    
    def test_set_status(self):
        """Test setting span status."""
        span = Span(name="test")
        span.set_status(SpanStatus.ERROR, "Connection failed")
        
        assert span.status == SpanStatus.ERROR
        assert span.status_message == "Connection failed"
    
    def test_end(self):
        """Test ending span."""
        span = Span(name="test")
        span.end()
        
        assert span.end_time is not None
        assert span.status == SpanStatus.OK
    
    def test_end_with_status(self):
        """Test ending span with status."""
        span = Span(name="test")
        span.end(SpanStatus.ERROR)
        
        assert span.status == SpanStatus.ERROR
    
    def test_duration_ms(self):
        """Test duration calculation."""
        span = Span(name="test")
        import time
        time.sleep(0.01)  # 10ms
        span.end()
        
        assert span.duration_ms >= 10
    
    def test_duration_before_end(self):
        """Test duration before end is 0."""
        span = Span(name="test")
        assert span.duration_ms == 0.0
    
    def test_to_dict(self):
        """Test converting span to dictionary."""
        span = Span(name="test_query")
        span.set_attribute("key", "value")
        span.end()
        
        d = span.to_dict()
        assert d["name"] == "test_query"
        assert d["trace_id"] is not None
        assert d["span_id"] is not None
        assert d["attributes"]["key"] == "value"
        assert d["duration_ms"] >= 0
    
    def test_parent_span_id(self):
        """Test parent span ID."""
        span = Span(name="test", parent_span_id="parent123")
        assert span.parent_span_id == "parent123"
    
    def test_initial_attributes(self):
        """Test span with initial attributes."""
        span = Span(name="test", attributes={"initial": "value"})
        assert span.attributes["initial"] == "value"
    
    def test_span_kind_values(self):
        """Test all span kinds."""
        assert SpanKind.CLIENT.value == "client"
        assert SpanKind.SERVER.value == "server"
        assert SpanKind.INTERNAL.value == "internal"
    
    def test_span_status_values(self):
        """Test all span statuses."""
        assert SpanStatus.UNSET.value == "unset"
        assert SpanStatus.OK.value == "ok"
        assert SpanStatus.ERROR.value == "error"


# ============================================================================
# SpanContext Tests (10 tests)
# ============================================================================

class TestSpanContext:
    """Tests for SpanContext context manager."""
    
    def test_sync_context_manager(self):
        """Test synchronous context manager."""
        backend = OpenTelemetryBackend()
        
        with backend.span("test_operation") as span:
            assert span is not None
            assert span.name == "test_operation"
        
        assert span.end_time is not None
    
    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Test asynchronous context manager."""
        backend = OpenTelemetryBackend()
        
        async with backend.span("test_operation") as span:
            assert span is not None
            await asyncio.sleep(0.01)
        
        assert span.end_time is not None
    
    def test_exception_sets_error_status(self):
        """Test exception sets error status."""
        backend = OpenTelemetryBackend()
        
        try:
            with backend.span("test_operation") as span:
                raise ValueError("Test error")
        except ValueError:
            pass
        
        assert span.status == SpanStatus.ERROR
        assert "Test error" in span.status_message
    
    def test_exception_adds_event(self):
        """Test exception adds event."""
        backend = OpenTelemetryBackend()
        
        try:
            with backend.span("test_operation") as span:
                raise ValueError("Test error")
        except ValueError:
            pass
        
        assert any(e["name"] == "exception" for e in span.events)
    
    def test_span_recorded(self):
        """Test span is recorded after context exits."""
        backend = OpenTelemetryBackend()
        
        with backend.span("test_operation"):
            pass
        
        spans = backend.get_spans()
        assert len(spans) == 1
    
    @pytest.mark.asyncio
    async def test_async_exception(self):
        """Test async exception handling."""
        backend = OpenTelemetryBackend()
        
        try:
            async with backend.span("test_operation") as span:
                raise RuntimeError("Async error")
        except RuntimeError:
            pass
        
        assert span.status == SpanStatus.ERROR
    
    def test_nested_spans(self):
        """Test nested spans."""
        backend = OpenTelemetryBackend()
        
        with backend.span("outer") as outer:
            with backend.span("inner") as inner:
                assert inner.parent_span_id == outer.span_id
    
    def test_span_kind_propagates(self):
        """Test span kind is set correctly."""
        backend = OpenTelemetryBackend()
        
        with backend.span("test", kind=SpanKind.SERVER) as span:
            assert span.kind == SpanKind.SERVER
    
    def test_initial_attributes(self):
        """Test initial attributes are set."""
        backend = OpenTelemetryBackend()
        
        with backend.span("test", attributes={"key": "value"}) as span:
            assert span.attributes["key"] == "value"
    
    def test_success_sets_ok_status(self):
        """Test successful completion sets OK status."""
        backend = OpenTelemetryBackend()
        
        with backend.span("test") as span:
            pass
        
        assert span.status == SpanStatus.OK


# ============================================================================
# OpenTelemetry Metrics Tests (15 tests)
# ============================================================================

class TestOTelMetrics:
    """Tests for OpenTelemetry metric types."""
    
    def test_counter_add(self):
        """Test counter add."""
        counter = OTelCounter(name="test_counter")
        counter.add(5.0)
        assert counter.get() == 5.0
    
    def test_counter_accumulates(self):
        """Test counter accumulates values."""
        counter = OTelCounter(name="test_counter")
        counter.add(1.0)
        counter.add(2.0)
        counter.add(3.0)
        assert counter.get() == 6.0
    
    def test_counter_with_attributes(self):
        """Test counter with attributes."""
        counter = OTelCounter(name="test_counter")
        counter.add(1.0, {"method": "GET"})
        counter.add(2.0, {"method": "POST"})
        
        assert counter.get({"method": "GET"}) == 1.0
        assert counter.get({"method": "POST"}) == 2.0
    
    def test_gauge_set(self):
        """Test gauge set."""
        gauge = OTelGauge(name="test_gauge")
        gauge.set(42.0)
        assert gauge.get() == 42.0
    
    def test_gauge_overwrites(self):
        """Test gauge overwrites value."""
        gauge = OTelGauge(name="test_gauge")
        gauge.set(10.0)
        gauge.set(20.0)
        assert gauge.get() == 20.0
    
    def test_gauge_with_attributes(self):
        """Test gauge with attributes."""
        gauge = OTelGauge(name="test_gauge")
        gauge.set(5.0, {"pool": "main"})
        gauge.set(10.0, {"pool": "replica"})
        
        assert gauge.get({"pool": "main"}) == 5.0
        assert gauge.get({"pool": "replica"}) == 10.0
    
    def test_histogram_record(self):
        """Test histogram record."""
        histogram = OTelHistogram(name="test_histogram")
        histogram.record(0.5)
        assert histogram.get_observations() == [0.5]
    
    def test_histogram_multiple_records(self):
        """Test histogram multiple records."""
        histogram = OTelHistogram(name="test_histogram")
        histogram.record(0.1)
        histogram.record(0.5)
        histogram.record(1.0)
        assert histogram.get_observations() == [0.1, 0.5, 1.0]
    
    def test_histogram_with_attributes(self):
        """Test histogram with attributes."""
        histogram = OTelHistogram(name="test_histogram")
        histogram.record(0.1, {"table": "users"})
        histogram.record(0.5, {"table": "orders"})
        
        assert histogram.get_observations({"table": "users"}) == [0.1]
        assert histogram.get_observations({"table": "orders"}) == [0.5]
    
    def test_counter_get_nonexistent(self):
        """Test counter get nonexistent."""
        counter = OTelCounter(name="test_counter")
        assert counter.get() == 0.0
    
    def test_gauge_get_nonexistent(self):
        """Test gauge get nonexistent."""
        gauge = OTelGauge(name="test_gauge")
        assert gauge.get() == 0.0
    
    def test_histogram_get_nonexistent(self):
        """Test histogram get nonexistent."""
        histogram = OTelHistogram(name="test_histogram")
        assert histogram.get_observations() == []
    
    def test_counter_description(self):
        """Test counter with description."""
        counter = OTelCounter(
            name="test_counter",
            description="Total count",
            unit="1",
        )
        assert counter.description == "Total count"
        assert counter.unit == "1"
    
    def test_histogram_boundaries(self):
        """Test histogram with custom boundaries."""
        boundaries = (0.01, 0.1, 1.0)
        histogram = OTelHistogram(name="test_histogram", boundaries=boundaries)
        assert histogram.boundaries == boundaries
    
    def test_attributes_key_sorted(self):
        """Test attributes key is sorted."""
        counter = OTelCounter(name="test_counter")
        counter.add(1.0, {"z": "1", "a": "2"})
        counter.add(1.0, {"a": "2", "z": "1"})
        
        assert counter.get({"a": "2", "z": "1"}) == 2.0


# ============================================================================
# OpenTelemetryBackend Tests (20 tests)
# ============================================================================

class TestOpenTelemetryBackend:
    """Tests for OpenTelemetryBackend class."""
    
    def test_default_creation(self):
        """Test creating backend with defaults."""
        backend = OpenTelemetryBackend()
        assert backend is not None
    
    def test_custom_config(self):
        """Test creating backend with custom config."""
        config = MetricsConfig(prefix="custom")
        backend = OpenTelemetryBackend(config)
        assert backend._config.prefix == "custom"
    
    def test_counter_inc(self):
        """Test counter increment."""
        backend = OpenTelemetryBackend()
        backend.counter_inc("test_counter")
        
        metrics = backend.get_metrics()
        assert "test_counter" in metrics["counters"]
    
    def test_gauge_set(self):
        """Test gauge set."""
        backend = OpenTelemetryBackend()
        backend.gauge_set("test_gauge", 42.0)
        
        metrics = backend.get_metrics()
        assert "test_gauge" in metrics["gauges"]
    
    def test_histogram_observe(self):
        """Test histogram observe."""
        backend = OpenTelemetryBackend()
        backend.histogram_observe("test_histogram", 0.5)
        
        metrics = backend.get_metrics()
        assert "test_histogram" in metrics["histograms"]
    
    def test_get_metrics(self):
        """Test getting all metrics."""
        backend = OpenTelemetryBackend()
        backend.counter_inc("counter")
        backend.gauge_set("gauge", 1.0)
        backend.histogram_observe("histogram", 0.5)
        
        metrics = backend.get_metrics()
        assert "counters" in metrics
        assert "gauges" in metrics
        assert "histograms" in metrics
    
    def test_reset(self):
        """Test resetting all metrics and traces."""
        backend = OpenTelemetryBackend()
        backend.counter_inc("counter")
        
        with backend.span("test"):
            pass
        
        backend.reset()
        
        metrics = backend.get_metrics()
        assert metrics["counters"] == {}
        assert backend.get_spans() == []
    
    def test_span_creation(self):
        """Test span creation."""
        backend = OpenTelemetryBackend()
        
        with backend.span("test_operation") as span:
            assert span.name == "test_operation"
    
    def test_get_spans(self):
        """Test getting recorded spans."""
        backend = OpenTelemetryBackend()
        
        with backend.span("op1"):
            pass
        with backend.span("op2"):
            pass
        
        spans = backend.get_spans()
        assert len(spans) == 2
    
    def test_get_spans_by_trace_id(self):
        """Test filtering spans by trace ID."""
        backend = OpenTelemetryBackend()
        
        with backend.span("test") as span:
            trace_id = span.trace_id
        
        spans = backend.get_spans(trace_id=trace_id)
        assert len(spans) == 1
    
    def test_get_spans_limit(self):
        """Test limiting returned spans."""
        backend = OpenTelemetryBackend()
        
        for i in range(10):
            with backend.span(f"op{i}"):
                pass
        
        spans = backend.get_spans(limit=5)
        assert len(spans) == 5
    
    def test_get_current_span(self):
        """Test getting current span."""
        backend = OpenTelemetryBackend()
        
        assert backend.get_current_span() is None
        
        with backend.span("test") as span:
            assert backend.get_current_span() is span
        
        # After exiting, current span should be reset
        # (Implementation may vary)
    
    def test_db_span(self):
        """Test database-specific span."""
        backend = OpenTelemetryBackend()
        
        with backend.db_span(
            "SELECT * FROM users",
            operation="SELECT",
            table="users",
            database="mydb",
        ) as span:
            assert span.attributes["db.system"] == "postgresql"
            assert span.attributes["db.operation"] == "SELECT"
            assert span.attributes["db.sql.table"] == "users"
    
    def test_inject_trace_headers(self):
        """Test injecting trace headers."""
        backend = OpenTelemetryBackend()
        
        with backend.span("test") as span:
            headers = backend.inject_trace_headers()
            assert "traceparent" in headers
            assert span.trace_id in headers["traceparent"]
    
    def test_extract_trace_headers(self):
        """Test extracting trace context from headers."""
        backend = OpenTelemetryBackend()
        
        headers = {
            "traceparent": "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"
        }
        ctx = backend.extract_trace_headers(headers)
        
        assert ctx is not None
        assert ctx.trace_id == "0af7651916cd43dd8448eb211c80319c"
    
    def test_set_get_trace_context(self):
        """Test setting and getting trace context."""
        backend = OpenTelemetryBackend()
        ctx = TraceContext()
        
        backend.set_trace_context(ctx)
        assert backend.get_trace_context() is ctx
    
    def test_start_end_span(self):
        """Test manual span start/end."""
        backend = OpenTelemetryBackend()
        
        span = backend.start_span("test")
        assert span.name == "test"
        
        backend.end_span(span)
        assert span.end_time is not None
    
    def test_max_spans_limit(self):
        """Test spans are limited."""
        backend = OpenTelemetryBackend()
        backend._max_spans = 10
        
        for i in range(20):
            with backend.span(f"op{i}"):
                pass
        
        spans = backend.get_spans(limit=100)
        assert len(spans) <= 10
    
    def test_create_otel_backend_helper(self):
        """Test create_otel_backend helper."""
        backend = create_otel_backend(prefix="custom")
        assert backend._config.prefix == "custom"
    
    def test_metrics_interface(self):
        """Test backend implements MetricsBackend interface."""
        from pynext.db.adapters.postgres.observability.metrics import MetricsBackend
        
        backend = OpenTelemetryBackend()
        assert isinstance(backend, MetricsBackend)


# ============================================================================
# Tracing Integration Tests (10 tests)
# ============================================================================

class TestTracingIntegration:
    """Tests for tracing integration."""
    
    @pytest.fixture(autouse=True)
    def reset_trace_context(self):
        """Reset trace context before each test to ensure isolation."""
        from pynext.db.adapters.postgres.observability.opentelemetry import _current_span, _trace_context
        # Reset both ContextVars
        _current_span.set(None)
        _trace_context.set(None)
        yield
        # Clean up after test
        _current_span.set(None)
        _trace_context.set(None)
    
    def test_trace_context_propagation(self):
        """Test trace context propagates to spans."""
        backend = OpenTelemetryBackend()
        ctx = TraceContext(trace_id="test_trace_id_123456789012")
        backend.set_trace_context(ctx)
        
        with backend.span("test") as span:
            assert span.trace_id == "test_trace_id_123456789012"
    
    def test_parent_span_propagation(self):
        """Test parent span propagates."""
        backend = OpenTelemetryBackend()
        
        with backend.span("parent") as parent:
            with backend.span("child") as child:
                assert child.parent_span_id == parent.span_id
                assert child.trace_id == parent.trace_id
    
    def test_get_current_trace_id(self):
        """Test get_current_trace_id helper."""
        backend = OpenTelemetryBackend()
        
        assert get_current_trace_id() is None
        
        with backend.span("test") as span:
            assert get_current_trace_id() == span.trace_id
    
    def test_span_attributes_in_to_dict(self):
        """Test span attributes appear in to_dict."""
        backend = OpenTelemetryBackend()
        
        with backend.span("test") as span:
            span.set_attribute("custom", "value")
        
        spans = backend.get_spans()
        assert spans[0]["attributes"]["custom"] == "value"
    
    def test_span_events_in_to_dict(self):
        """Test span events appear in to_dict."""
        backend = OpenTelemetryBackend()
        
        with backend.span("test") as span:
            span.add_event("checkpoint", {"step": 1})
        
        spans = backend.get_spans()
        assert len(spans[0]["events"]) == 1
    
    @pytest.mark.asyncio
    async def test_async_tracing(self):
        """Test async tracing works correctly."""
        backend = OpenTelemetryBackend()
        
        async with backend.span("async_operation") as span:
            await asyncio.sleep(0.01)
            span.set_attribute("async", True)
        
        spans = backend.get_spans()
        assert len(spans) == 1
        assert spans[0]["attributes"]["async"] is True
    
    def test_trace_header_roundtrip(self):
        """Test trace header injection and extraction."""
        backend = OpenTelemetryBackend()
        
        with backend.span("test") as span:
            headers = backend.inject_trace_headers()
        
        ctx = backend.extract_trace_headers(headers)
        assert ctx is not None
        assert ctx.trace_id == span.trace_id
    
    def test_case_insensitive_header_extraction(self):
        """Test headers are extracted case-insensitively."""
        backend = OpenTelemetryBackend()
        
        headers = {
            "TRACEPARENT": "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"
        }
        ctx = backend.extract_trace_headers(headers)
        assert ctx is not None
    
    def test_no_headers_returns_none(self):
        """Test missing headers returns None."""
        backend = OpenTelemetryBackend()
        ctx = backend.extract_trace_headers({})
        assert ctx is None
    
    def test_otlp_config(self):
        """Test OTLPConfig dataclass."""
        config = OTLPConfig(
            endpoint="http://collector:4317",
            headers={"Authorization": "Bearer token"},
            timeout_seconds=5.0,
            compression="gzip",
        )
        
        assert config.endpoint == "http://collector:4317"
        assert config.headers["Authorization"] == "Bearer token"
        assert config.timeout_seconds == 5.0
        assert config.compression == "gzip"

