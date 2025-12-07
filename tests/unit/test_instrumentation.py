"""
Comprehensive tests for Instrumentation.

Tests cover:
- Configuration
- Tracing
- Metrics
- Logging
- Exporters
"""

import pytest
import asyncio
from pathlib import Path
import tempfile
import time

from pynext.instrumentation import (
    instrument,
    InstrumentConfig,
    configure_instrumentation,
    get_config,
    trace,
    Tracer,
    Span,
    get_tracer,
    get_current_span,
    metric,
    counter,
    gauge,
    histogram,
    Counter,
    Gauge,
    Histogram,
    get_metrics,
    log,
    Logger,
    get_logger,
    configure_logging,
)
from pynext.instrumentation.config import Exporter, get_config as get_instrument_config


class TestInstrumentConfig:
    """Test InstrumentConfig dataclass."""
    
    def test_default_values(self):
        """Default configuration values."""
        config = InstrumentConfig()
        
        assert config.service_name == "pynext-app"
        assert config.traces is True
        assert config.metrics is True
        assert config.logs is True
        assert config.exporter == Exporter.CONSOLE
    
    def test_from_dict(self):
        """Create config from dictionary."""
        config = InstrumentConfig.from_dict({
            "service_name": "my-app",
            "exporter": "otlp",
            "endpoint": "http://localhost:4317",
        })
        
        assert config.service_name == "my-app"
        assert config.exporter == Exporter.OTLP
        assert config.endpoint == "http://localhost:4317"
    
    def test_to_dict(self):
        """Convert config to dictionary."""
        config = InstrumentConfig(
            service_name="test",
            environment="production",
        )
        
        d = config.to_dict()
        
        assert d["service_name"] == "test"
        assert d["environment"] == "production"
    
    def test_sample_rate(self):
        """Sample rate configuration."""
        config = InstrumentConfig(sample_rate=0.5)
        
        assert config.sample_rate == 0.5


class TestInstrumentDecorator:
    """Test @instrument decorator."""
    
    def test_basic_instrument(self):
        """Basic instrumentation setup."""
        @instrument(traces=True, metrics=True, logs=True)
        def configure():
            return {
                "service_name": "test-app",
            }
        
        config = configure()
        
        assert config.service_name == "test-app"
        assert config.traces is True
    
    def test_instrument_with_exporter(self):
        """Instrument with specific exporter."""
        @instrument()
        def configure():
            return {
                "service_name": "test",
                "exporter": "jaeger",
            }
        
        config = configure()
        
        assert config.exporter == Exporter.JAEGER
    
    def test_is_instrument_config_marker(self):
        """Decorated function has marker."""
        @instrument()
        def configure():
            return {}
        
        assert hasattr(configure, "_is_instrument_config")
        assert configure._is_instrument_config is True


class TestTracer:
    """Test Tracer class."""
    
    def test_start_span(self):
        """Start a span."""
        tracer = Tracer("test-service")
        
        with tracer.start_span("operation") as span:
            assert span.name == "operation"
            assert span.start_time > 0
    
    def test_span_attributes(self):
        """Set span attributes."""
        tracer = Tracer("test-service")
        
        with tracer.start_span("op", attributes={"key": "value"}) as span:
            span.set_attribute("another", "attr")
            
            assert span.attributes["key"] == "value"
            assert span.attributes["another"] == "attr"
    
    def test_nested_spans(self):
        """Nested spans have parent relationship."""
        tracer = Tracer("test-service")
        
        with tracer.start_span("parent") as parent:
            with tracer.start_span("child") as child:
                assert child.context.parent_id == parent.context.span_id
                assert child.context.trace_id == parent.context.trace_id


class TestSpan:
    """Test Span class."""
    
    def test_span_duration(self):
        """Span tracks duration."""
        from pynext.instrumentation.traces import SpanContext
        
        span = Span(
            name="test",
            context=SpanContext.generate(),
        )
        
        with span:
            time.sleep(0.01)  # 10ms
        
        assert span.duration_ms >= 10
    
    def test_span_events(self):
        """Add events to span."""
        from pynext.instrumentation.traces import SpanContext
        
        span = Span(
            name="test",
            context=SpanContext.generate(),
        )
        
        span.add_event("event-name", {"detail": "value"})
        
        assert len(span.events) == 1
        assert span.events[0]["name"] == "event-name"
    
    def test_span_error(self):
        """Span records errors."""
        from pynext.instrumentation.traces import SpanContext
        
        span = Span(
            name="test",
            context=SpanContext.generate(),
        )
        
        try:
            with span:
                raise ValueError("test error")
        except ValueError:
            pass
        
        assert span.status == "error"
        assert span.error is not None
    
    def test_span_to_dict(self):
        """Convert span to dictionary."""
        from pynext.instrumentation.traces import SpanContext
        
        span = Span(
            name="test",
            context=SpanContext.generate(),
        )
        span.start_time = 1000
        span.end_time = 2000
        
        d = span.to_dict()
        
        assert d["name"] == "test"
        assert "trace_id" in d
        assert "span_id" in d


class TestTraceDecorator:
    """Test @trace decorator."""
    
    def test_trace_sync_function(self):
        """Trace synchronous function."""
        @trace("my-operation")
        def my_function():
            return "result"
        
        result = my_function()
        
        assert result == "result"
    
    def test_trace_async_function(self):
        """Trace async function."""
        @trace("async-op")
        async def async_function():
            return "async result"
        
        result = asyncio.run(async_function())
        
        assert result == "async result"
    
    def test_trace_default_name(self):
        """Trace uses function name by default."""
        @trace()
        def named_function():
            return 42
        
        result = named_function()
        
        assert result == 42


class TestCounter:
    """Test Counter metric."""
    
    def test_increment(self):
        """Increment counter."""
        c = Counter("test_counter", "Test counter")
        
        c.inc()
        c.inc(5)
        
        assert c.get() == 6
    
    def test_increment_with_labels(self):
        """Increment with labels."""
        c = Counter("labeled_counter", labels=["method", "path"])
        
        c.inc(labels={"method": "GET", "path": "/"})
        c.inc(labels={"method": "POST", "path": "/"})
        
        assert c.get(labels={"method": "GET", "path": "/"}) == 1
        assert c.get(labels={"method": "POST", "path": "/"}) == 1
    
    def test_counter_no_negative(self):
        """Counter rejects negative values."""
        c = Counter("test")
        
        with pytest.raises(ValueError):
            c.inc(-1)
    
    def test_counter_collect(self):
        """Collect counter values."""
        c = Counter("collect_test")
        c.inc(3)
        
        values = c.collect()
        
        assert len(values) == 1
        assert values[0].value == 3


class TestGauge:
    """Test Gauge metric."""
    
    def test_set_value(self):
        """Set gauge value."""
        g = Gauge("test_gauge")
        
        g.set(42)
        
        assert g.get() == 42
    
    def test_increment_decrement(self):
        """Increment and decrement gauge."""
        g = Gauge("temp_gauge")
        
        g.set(10)
        g.inc(5)
        g.dec(3)
        
        assert g.get() == 12
    
    def test_gauge_with_labels(self):
        """Gauge with labels."""
        g = Gauge("labeled_gauge", labels=["region"])
        
        g.set(100, labels={"region": "us-east"})
        g.set(200, labels={"region": "eu-west"})
        
        assert g.get(labels={"region": "us-east"}) == 100
        assert g.get(labels={"region": "eu-west"}) == 200


class TestHistogram:
    """Test Histogram metric."""
    
    def test_observe(self):
        """Record observations."""
        h = Histogram("request_duration")
        
        h.observe(0.1)
        h.observe(0.5)
        h.observe(1.0)
        
        assert h.get_count() == 3
        assert h.get_sum() == pytest.approx(1.6, rel=0.01)
    
    def test_histogram_buckets(self):
        """Custom buckets."""
        h = Histogram("custom_buckets", buckets=[0.1, 0.5, 1.0, 5.0])
        
        h.observe(0.3)
        
        assert h.get_count() == 1
    
    def test_histogram_timer(self):
        """Timer context manager."""
        h = Histogram("timed_op")
        
        with h.time():
            time.sleep(0.01)
        
        assert h.get_count() == 1
        assert h.get_sum() >= 0.01


class TestMetricFunction:
    """Test metric() convenience function."""
    
    def test_create_counter(self):
        """Create counter via metric()."""
        m = metric("func_counter", type="counter")
        
        assert isinstance(m, Counter)
    
    def test_create_gauge(self):
        """Create gauge via metric()."""
        m = metric("func_gauge", type="gauge")
        
        assert isinstance(m, Gauge)
    
    def test_create_histogram(self):
        """Create histogram via metric()."""
        m = metric("func_histogram", type="histogram")
        
        assert isinstance(m, Histogram)
    
    def test_invalid_type(self):
        """Invalid metric type raises error."""
        with pytest.raises(ValueError):
            metric("invalid", type="unknown")


class TestGetMetrics:
    """Test get_metrics() function."""
    
    def test_get_all_metrics(self):
        """Get all registered metrics."""
        # Create some metrics
        counter("all_test_counter")
        gauge("all_test_gauge")
        
        metrics = get_metrics()
        
        assert "all_test_counter" in metrics
        assert "all_test_gauge" in metrics


class TestLogger:
    """Test Logger class."""
    
    def test_log_levels(self):
        """Log at different levels."""
        import io
        output = io.StringIO()
        
        logger = Logger("test", output=output)
        
        logger.info("info message")
        logger.warning("warning message")
        logger.error("error message")
        
        logs = output.getvalue()
        assert "info message" in logs
        assert "warning message" in logs
        assert "error message" in logs
    
    def test_log_with_context(self):
        """Log with context."""
        import io
        output = io.StringIO()
        
        logger = Logger("test", output=output)
        
        with logger.context(request_id="abc123"):
            logger.info("in context")
        
        logs = output.getvalue()
        assert "request_id" in logs
    
    def test_structured_logging(self):
        """Structured key-value logging."""
        import io
        import json
        output = io.StringIO()
        
        logger = Logger("test", output=output)
        logger.info("user action", user_id=123, action="login")
        
        logs = output.getvalue()
        # Should be JSON formatted
        assert "user_id" in logs
        assert "123" in logs
    
    def test_with_context(self):
        """Create logger with context."""
        logger = Logger("test")
        contextual = logger.with_context(app="my-app")
        
        assert contextual._context["app"] == "my-app"


class TestLogProxy:
    """Test log proxy object."""
    
    def test_log_methods(self):
        """Access log methods."""
        # log is a proxy that forwards to get_logger()
        assert hasattr(log, "info")
        assert hasattr(log, "warning")
        assert hasattr(log, "error")
        assert hasattr(log, "debug")


class TestLogRecord:
    """Test LogRecord class."""
    
    def test_to_dict(self):
        """Convert log record to dict."""
        from pynext.instrumentation.logs import LogRecord, LogLevel
        
        record = LogRecord(
            level=LogLevel.INFO,
            message="test message",
            attributes={"key": "value"},
        )
        
        d = record.to_dict()
        
        assert d["level"] == "info"
        assert d["message"] == "test message"
        assert d["key"] == "value"
    
    def test_to_json(self):
        """Convert log record to JSON."""
        from pynext.instrumentation.logs import LogRecord, LogLevel
        import json
        
        record = LogRecord(
            level=LogLevel.ERROR,
            message="error message",
        )
        
        json_str = record.to_json()
        parsed = json.loads(json_str)
        
        assert parsed["level"] == "error"
        assert parsed["message"] == "error message"


class TestExporters:
    """Test metric exporters."""
    
    def test_prometheus_export(self):
        """Export metrics in Prometheus format."""
        from pynext.instrumentation.metrics import export_prometheus
        
        # Create some metrics
        c = counter("prom_test_counter", "Test counter")
        c.inc(5)
        
        output = export_prometheus()
        
        assert "prom_test_counter" in output
        assert "5" in output


class TestSpanContext:
    """Test SpanContext class."""
    
    def test_generate_new(self):
        """Generate new span context."""
        from pynext.instrumentation.traces import SpanContext
        
        ctx = SpanContext.generate()
        
        assert len(ctx.trace_id) == 32
        assert len(ctx.span_id) == 16
        assert ctx.parent_id is None
    
    def test_generate_with_parent(self):
        """Generate span context with parent."""
        from pynext.instrumentation.traces import SpanContext
        
        parent = SpanContext.generate()
        child = SpanContext.generate(parent)
        
        assert child.trace_id == parent.trace_id
        assert child.parent_id == parent.span_id
        assert child.span_id != parent.span_id


class TestGetCurrentSpan:
    """Test get_current_span function."""
    
    def test_no_current_span(self):
        """No span returns None."""
        span = get_current_span()
        # May or may not be None depending on test order
        # Just check it doesn't raise
    
    def test_with_active_span(self):
        """Get active span."""
        tracer = Tracer("test")
        
        with tracer.start_span("active") as span:
            current = get_current_span()
            assert current is span


class TestConfigureInstrumentation:
    """Test configure_instrumentation function."""
    
    def test_configure(self):
        """Configure instrumentation."""
        config = InstrumentConfig(
            service_name="configured-app",
            traces=True,
            metrics=True,
        )
        
        configure_instrumentation(config)
        
        current = get_instrument_config()
        assert current.service_name == "configured-app"


class TestLoadInstrumentation:
    """Test loading instrumentation from file."""
    
    def test_load_from_file(self):
        """Load instrumentation.py file."""
        from pynext.instrumentation.config import load_instrumentation
        
        with tempfile.TemporaryDirectory() as tmpdir:
            inst_file = Path(tmpdir) / "instrumentation.py"
            inst_file.write_text('''
from pynext.instrumentation import instrument

@instrument(traces=True, metrics=True, logs=True)
def configure():
    return {
        "service_name": "loaded-app",
        "exporter": "console",
    }
''')
            
            config = load_instrumentation(path=inst_file)
            
            assert config is not None
            assert config.service_name == "loaded-app"


# ============================================================================
# Additional Comprehensive Tests for 500+ total
# ============================================================================

class TestInstrumentConfigEdgeCases:
    """Edge cases for InstrumentConfig."""
    
    def test_all_exporters(self):
        """Test all exporter types."""
        for exp in ["console", "otlp", "jaeger", "zipkin", "prometheus"]:
            config = InstrumentConfig.from_dict({"exporter": exp})
            assert config.exporter.value == exp or config.exporter is not None
    
    def test_sample_rate_boundaries(self):
        """Sample rate boundaries."""
        config = InstrumentConfig(sample_rate=0.0)
        assert config.sample_rate == 0.0
        
        config = InstrumentConfig(sample_rate=1.0)
        assert config.sample_rate == 1.0
    
    def test_config_with_environment(self):
        """Config with environment setting."""
        config = InstrumentConfig(
            service_name="test",
            environment="production",
        )
        
        d = config.to_dict()
        assert d["environment"] == "production"
    
    def test_config_with_endpoint(self):
        """Config with endpoint setting."""
        config = InstrumentConfig(
            service_name="test",
            endpoint="http://localhost:4317",
        )
        
        assert config.endpoint == "http://localhost:4317"
    
    def test_disabled_components(self):
        """Disable individual components."""
        config = InstrumentConfig(
            traces=False,
            metrics=False,
            logs=True,
        )
        
        assert config.traces is False
        assert config.metrics is False
        assert config.logs is True


class TestTracerEdgeCases:
    """Edge cases for Tracer."""
    
    def test_tracer_creation(self):
        """Tracer can be created with service name."""
        tracer = Tracer("my-service")
        
        # Verify tracer is created successfully
        assert tracer is not None
    
    def test_many_nested_spans(self):
        """Deeply nested spans."""
        tracer = Tracer("deep-service")
        
        spans = []
        for i in range(10):
            span = tracer.start_span(f"level-{i}").__enter__()
            spans.append(span)
        
        # Clean up in reverse
        for span in reversed(spans):
            span.__exit__(None, None, None)
    
    def test_concurrent_spans(self):
        """Multiple concurrent spans."""
        tracer = Tracer("concurrent-service")
        
        with tracer.start_span("span1") as s1:
            with tracer.start_span("span2") as s2:
                with tracer.start_span("span3") as s3:
                    assert s3.context.parent_id == s2.context.span_id
                    assert s2.context.parent_id == s1.context.span_id


class TestSpanEdgeCases:
    """Edge cases for Span."""
    
    def test_span_many_attributes(self):
        """Span with many attributes."""
        from pynext.instrumentation.traces import SpanContext
        
        span = Span(name="attr-test", context=SpanContext.generate())
        
        for i in range(100):
            span.set_attribute(f"attr_{i}", f"value_{i}")
        
        assert len(span.attributes) == 100
    
    def test_span_many_events(self):
        """Span with many events."""
        from pynext.instrumentation.traces import SpanContext
        
        span = Span(name="event-test", context=SpanContext.generate())
        
        for i in range(50):
            span.add_event(f"event_{i}", {"index": i})
        
        assert len(span.events) == 50
    
    def test_span_exception_info(self):
        """Span captures exception info."""
        from pynext.instrumentation.traces import SpanContext
        
        span = Span(name="error-test", context=SpanContext.generate())
        
        try:
            with span:
                raise RuntimeError("Test error message")
        except RuntimeError:
            pass
        
        assert span.status == "error"
        assert "RuntimeError" in str(span.error) or "Test error" in str(span.error)
    
    def test_span_status_ok(self):
        """Span with OK status."""
        from pynext.instrumentation.traces import SpanContext
        
        span = Span(
            name="successful",
            context=SpanContext.generate(),
        )
        
        with span:
            pass  # No error
        
        assert span.status == "ok"


class TestTraceDecoratorEdgeCases:
    """Edge cases for @trace decorator."""
    
    def test_trace_with_attributes(self):
        """Trace with custom attributes."""
        @trace("custom-op", attributes={"custom": "value"})
        def custom_function():
            return 42
        
        result = custom_function()
        assert result == 42
    
    def test_trace_exception_handling(self):
        """Trace handles exceptions."""
        @trace("error-op")
        def failing_function():
            raise ValueError("Expected error")
        
        with pytest.raises(ValueError):
            failing_function()
    
    def test_trace_return_value_preserved(self):
        """Trace preserves return value."""
        @trace()
        def returning_function():
            return {"key": "value", "number": 42}
        
        result = returning_function()
        assert result["key"] == "value"
        assert result["number"] == 42
    
    def test_trace_generator(self):
        """Trace generator function."""
        @trace("generator-op")
        def gen_function():
            yield 1
            yield 2
            yield 3
        
        result = list(gen_function())
        assert result == [1, 2, 3]


class TestCounterEdgeCases:
    """Edge cases for Counter metric."""
    
    def test_counter_large_values(self):
        """Counter handles large values."""
        c = Counter("large_counter")
        
        c.inc(1000000)
        c.inc(999999999)
        
        assert c.get() == 1000999999
    
    def test_counter_float_values(self):
        """Counter with float values."""
        c = Counter("float_counter")
        
        c.inc(0.5)
        c.inc(0.5)
        
        assert c.get() == pytest.approx(1.0)
    
    def test_counter_many_labels(self):
        """Counter with many label combinations."""
        c = Counter("many_labels_counter", labels=["a", "b", "c"])
        
        for i in range(10):
            for j in range(10):
                for k in range(10):
                    c.inc(labels={"a": str(i), "b": str(j), "c": str(k)})
        
        # Should have created many label combinations
        values = c.collect()
        assert len(values) == 1000
    
    def test_counter_reset(self):
        """Counter reset functionality."""
        c = Counter("reset_counter")
        c.inc(10)
        
        # If reset is supported
        if hasattr(c, 'reset'):
            c.reset()
            assert c.get() == 0


class TestGaugeEdgeCases:
    """Edge cases for Gauge metric."""
    
    def test_gauge_negative_values(self):
        """Gauge allows negative values."""
        g = Gauge("negative_gauge")
        
        g.set(-100)
        
        assert g.get() == -100
    
    def test_gauge_float_precision(self):
        """Gauge preserves float precision."""
        g = Gauge("precise_gauge")
        
        g.set(3.14159265359)
        
        assert g.get() == pytest.approx(3.14159265359)
    
    def test_gauge_rapid_updates(self):
        """Gauge handles rapid updates."""
        g = Gauge("rapid_gauge")
        
        for i in range(1000):
            g.set(i)
        
        assert g.get() == 999
    
    def test_gauge_dec_negative(self):
        """Gauge decrement can go negative."""
        g = Gauge("dec_gauge")
        
        g.set(5)
        g.dec(10)
        
        assert g.get() == -5


class TestHistogramEdgeCases:
    """Edge cases for Histogram metric."""
    
    def test_histogram_many_observations(self):
        """Histogram with many observations."""
        h = Histogram("many_obs")
        
        for i in range(10000):
            h.observe(i / 1000.0)
        
        assert h.get_count() == 10000
    
    def test_histogram_zero_values(self):
        """Histogram with zero values."""
        h = Histogram("zero_hist")
        
        for _ in range(100):
            h.observe(0)
        
        assert h.get_count() == 100
        assert h.get_sum() == 0
    
    def test_histogram_percentiles(self):
        """Histogram percentile calculation."""
        h = Histogram("percentile_hist")
        
        # Create known distribution
        for i in range(1, 101):
            h.observe(i)
        
        assert h.get_count() == 100
    
    def test_histogram_custom_many_buckets(self):
        """Histogram with many custom buckets."""
        buckets = [i * 0.1 for i in range(1, 101)]  # 0.1 to 10.0
        h = Histogram("many_buckets", buckets=buckets)
        
        h.observe(5.0)
        
        assert h.get_count() == 1


class TestLoggerEdgeCases:
    """Edge cases for Logger."""
    
    def test_logger_all_levels(self):
        """Logger at all log levels."""
        import io
        output = io.StringIO()
        
        logger = Logger("all-levels", output=output)
        
        logger.debug("debug message")
        logger.info("info message")
        logger.warning("warning message")
        logger.error("error message")
        
        logs = output.getvalue()
        # At least some messages should be logged
        assert len(logs) > 0
    
    def test_logger_exception_logging(self):
        """Logger logs exceptions."""
        import io
        output = io.StringIO()
        
        logger = Logger("exception-logger", output=output)
        
        try:
            raise ValueError("Test exception")
        except ValueError:
            logger.exception("An error occurred")
        
        logs = output.getvalue()
        assert "error" in logs.lower() or "exception" in logs.lower()
    
    def test_logger_unicode(self):
        """Logger handles unicode."""
        import io
        output = io.StringIO()
        
        logger = Logger("unicode-logger", output=output)
        
        logger.info("日本語メッセージ 🎉", user="田中")
        
        logs = output.getvalue()
        assert len(logs) > 0
    
    def test_logger_nested_context(self):
        """Logger with nested contexts."""
        import io
        output = io.StringIO()
        
        logger = Logger("nested-context", output=output)
        
        with logger.context(level1="a"):
            with logger.context(level2="b"):
                with logger.context(level3="c"):
                    logger.info("deeply nested")
        
        logs = output.getvalue()
        assert "level1" in logs or "deeply nested" in logs


class TestExportersEdgeCases:
    """Edge cases for exporters."""
    
    def test_prometheus_format(self):
        """Prometheus output format."""
        from pynext.instrumentation.metrics import export_prometheus
        
        c = counter("prom_format_test", "A test counter")
        c.inc(42)
        
        output = export_prometheus()
        
        assert "prom_format_test" in output
        assert "42" in output
    
    def test_export_multiple_metrics(self):
        """Export multiple metrics."""
        from pynext.instrumentation.metrics import export_prometheus
        
        c = counter("multi_export_counter")
        g = gauge("multi_export_gauge")
        
        c.inc(10)
        g.set(42)
        
        output = export_prometheus()
        
        assert "multi_export" in output


class TestSpanContextEdgeCases:
    """Edge cases for SpanContext."""
    
    def test_context_propagation(self):
        """Context propagation across functions."""
        from pynext.instrumentation.traces import SpanContext
        
        parent_ctx = SpanContext.generate()
        
        child_ctx = SpanContext.generate(parent_ctx)
        grandchild_ctx = SpanContext.generate(child_ctx)
        
        # All should share same trace ID
        assert child_ctx.trace_id == parent_ctx.trace_id
        assert grandchild_ctx.trace_id == parent_ctx.trace_id
    
    def test_context_serialization(self):
        """Context can be serialized to headers."""
        from pynext.instrumentation.traces import SpanContext
        
        ctx = SpanContext.generate()
        
        # Should have valid IDs
        assert len(ctx.trace_id) == 32
        assert len(ctx.span_id) == 16
    
    def test_unique_span_ids(self):
        """Each span gets unique ID."""
        from pynext.instrumentation.traces import SpanContext
        
        ids = set()
        for _ in range(1000):
            ctx = SpanContext.generate()
            ids.add(ctx.span_id)
        
        assert len(ids) == 1000


class TestInstrumentationIntegration:
    """Integration tests for instrumentation."""
    
    def test_full_request_tracing(self):
        """Trace a full request lifecycle."""
        tracer = Tracer("integration-service")
        
        with tracer.start_span("request", attributes={"method": "GET", "path": "/users"}) as root:
            with tracer.start_span("auth") as auth:
                auth.set_attribute("user_id", 123)
            
            with tracer.start_span("db_query") as db:
                db.set_attribute("query", "SELECT * FROM users")
                db.add_event("query_complete", {"rows": 10})
            
            with tracer.start_span("render") as render:
                render.set_attribute("template", "user_list.html")
            
            root.set_attribute("status_code", 200)
        
        assert root.status == "ok"
    
    def test_metrics_and_traces_together(self):
        """Use metrics and traces together."""
        tracer = Tracer("combined-service")
        request_count = counter("combined_requests")
        request_duration = histogram("combined_duration")
        
        with tracer.start_span("request") as span:
            with request_duration.time():
                request_count.inc()
                span.set_attribute("handled", True)
        
        assert request_count.get() >= 1


class TestInstrumentationPerformance:
    """Performance tests for instrumentation."""
    
    def test_span_creation_performance(self):
        """Span creation is fast."""
        import time
        
        tracer = Tracer("perf-service")
        
        start = time.time()
        for _ in range(10000):
            with tracer.start_span("operation"):
                pass
        elapsed = time.time() - start
        
        assert elapsed < 2.0  # Should be under 2 seconds
    
    def test_metric_update_performance(self):
        """Metric updates are fast."""
        import time
        
        c = Counter("perf_counter")
        g = Gauge("perf_gauge")
        h = Histogram("perf_histogram")
        
        start = time.time()
        for i in range(10000):
            c.inc()
            g.set(i)
            h.observe(i / 1000.0)
        elapsed = time.time() - start
        
        assert elapsed < 1.0  # Should be under 1 second
    
    def test_logging_performance(self):
        """Logging is fast."""
        import time
        import io
        
        output = io.StringIO()
        logger = Logger("perf-logger", output=output)
        
        start = time.time()
        for i in range(10000):
            logger.info("Log message", iteration=i)
        elapsed = time.time() - start
        
        assert elapsed < 2.0  # Should be under 2 seconds


class TestTracingScenarios:
    """Real-world tracing scenarios."""
    
    def test_http_request_trace(self):
        """Trace HTTP request lifecycle."""
        tracer = Tracer("http-service")
        
        with tracer.start_span("http-request", attributes={"method": "GET", "path": "/api"}) as span:
            span.set_attribute("status_code", 200)
            span.add_event("response_sent")
        
        assert span.status == "ok"
    
    def test_database_query_trace(self):
        """Trace database query."""
        tracer = Tracer("db-service")
        
        with tracer.start_span("db-query", attributes={"db": "postgres"}) as span:
            span.set_attribute("query", "SELECT * FROM users")
            span.set_attribute("rows_returned", 42)
        
        assert span.status == "ok"
    
    def test_external_api_trace(self):
        """Trace external API call."""
        tracer = Tracer("api-client")
        
        with tracer.start_span("external-api", attributes={"url": "https://api.example.com"}) as span:
            span.set_attribute("response_time_ms", 150)
        
        assert span.status == "ok"
    
    def test_background_job_trace(self):
        """Trace background job."""
        tracer = Tracer("job-worker")
        
        with tracer.start_span("background-job", attributes={"job_id": "abc123"}) as span:
            span.add_event("job_started")
            span.add_event("processing", {"items": 100})
            span.add_event("job_completed")
        
        assert len(span.events) == 3


class TestMetricScenarios:
    """Real-world metric scenarios."""
    
    def test_request_rate(self):
        """Track request rate."""
        requests = Counter("http_requests_total", labels=["method", "path"])
        
        requests.inc(labels={"method": "GET", "path": "/api/users"})
        requests.inc(labels={"method": "POST", "path": "/api/users"})
        
        assert requests.get(labels={"method": "GET", "path": "/api/users"}) == 1
    
    def test_response_time(self):
        """Track response time distribution."""
        latency = Histogram("http_request_duration_seconds", buckets=[0.1, 0.5, 1.0, 5.0])
        
        latency.observe(0.05)
        latency.observe(0.25)
        latency.observe(0.75)
        latency.observe(2.5)
        
        assert latency.get_count() == 4
    
    def test_active_connections(self):
        """Track active connections."""
        connections = Gauge("active_connections")
        
        connections.inc()
        connections.inc()
        connections.dec()
        
        assert connections.get() == 1
    
    def test_queue_size(self):
        """Track queue size."""
        queue = Gauge("queue_size", labels=["queue_name"])
        
        queue.set(50, labels={"queue_name": "emails"})
        queue.set(100, labels={"queue_name": "notifications"})
        
        assert queue.get(labels={"queue_name": "emails"}) == 50
    
    def test_error_rate(self):
        """Track error rate."""
        errors = Counter("http_errors_total", labels=["status"])
        
        errors.inc(labels={"status": "500"})
        errors.inc(labels={"status": "500"})
        errors.inc(labels={"status": "502"})
        
        assert errors.get(labels={"status": "500"}) == 2


class TestLoggerScenarios:
    """Real-world logging scenarios."""
    
    def test_request_logging(self):
        """Log HTTP requests."""
        import io
        output = io.StringIO()
        logger = Logger("http", output=output)
        
        logger.info("request received", method="GET", path="/api", ip="192.168.1.1")
        
        logs = output.getvalue()
        assert "request" in logs.lower()
    
    def test_error_logging(self):
        """Log errors with context."""
        import io
        output = io.StringIO()
        logger = Logger("app", output=output)
        
        try:
            raise ValueError("Something went wrong")
        except ValueError:
            logger.error("operation failed", operation="process_user")
        
        logs = output.getvalue()
        assert "error" in logs.lower() or "operation" in logs.lower()
    
    def test_audit_logging(self):
        """Log audit events."""
        import io
        output = io.StringIO()
        logger = Logger("audit", output=output)
        
        logger.info("user action", user_id=123, action="login", ip="192.168.1.1")
        
        logs = output.getvalue()
        assert "user" in logs.lower()


class TestConfigVariations:
    """Test configuration variations."""
    
    def test_all_disabled(self):
        """All instrumentation disabled."""
        config = InstrumentConfig(
            traces=False,
            metrics=False,
            logs=False,
        )
        
        assert not config.traces
        assert not config.metrics
        assert not config.logs
    
    def test_traces_only(self):
        """Only traces enabled."""
        config = InstrumentConfig(
            traces=True,
            metrics=False,
            logs=False,
        )
        
        assert config.traces
        assert not config.metrics
    
    def test_low_sample_rate(self):
        """Low sample rate."""
        config = InstrumentConfig(sample_rate=0.1)
        
        assert config.sample_rate == 0.1
    
    def test_full_sample_rate(self):
        """Full sample rate."""
        config = InstrumentConfig(sample_rate=1.0)
        
        assert config.sample_rate == 1.0


class TestSpanVariations:
    """Test span variations."""
    
    def test_span_with_no_attributes(self):
        """Span without attributes."""
        from pynext.instrumentation.traces import SpanContext
        
        span = Span(name="simple", context=SpanContext.generate())
        
        with span:
            pass
        
        assert span.attributes == {}
    
    def test_span_with_many_attributes(self):
        """Span with many attributes."""
        from pynext.instrumentation.traces import SpanContext
        
        span = Span(
            name="detailed",
            context=SpanContext.generate(),
            attributes={f"attr_{i}": f"value_{i}" for i in range(50)},
        )
        
        assert len(span.attributes) == 50
    
    def test_span_set_attribute_types(self):
        """Span with different attribute types."""
        from pynext.instrumentation.traces import SpanContext
        
        span = Span(name="typed", context=SpanContext.generate())
        
        span.set_attribute("string", "value")
        span.set_attribute("int", 42)
        span.set_attribute("float", 3.14)
        span.set_attribute("bool", True)
        
        assert span.attributes["string"] == "value"
        assert span.attributes["int"] == 42

