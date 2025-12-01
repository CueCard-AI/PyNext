"""
Tests for PyNext Prometheus Backend Module.

80 comprehensive tests covering:
- PrometheusCounter (15 tests)
- PrometheusGauge (15 tests)
- PrometheusHistogram (15 tests)
- PrometheusRegistry (20 tests)
- PrometheusBackend (15 tests)
"""

import threading
import pytest

from pynext.db.adapters.postgres_prometheus import (
    PrometheusCounter,
    PrometheusGauge,
    PrometheusHistogram,
    PrometheusRegistry,
    PrometheusBackend,
    create_prometheus_backend,
)
from pynext.db.adapters.postgres_metrics import MetricsConfig, DEFAULT_BUCKETS


# ============================================================================
# PrometheusCounter Tests (15 tests)
# ============================================================================

class TestPrometheusCounter:
    """Tests for PrometheusCounter class."""
    
    def test_basic_increment(self):
        """Test basic counter increment."""
        counter = PrometheusCounter(name="test_counter")
        counter.inc()
        assert counter.get() == 1.0
    
    def test_increment_with_value(self):
        """Test counter increment with custom value."""
        counter = PrometheusCounter(name="test_counter")
        counter.inc(5.0)
        assert counter.get() == 5.0
    
    def test_accumulates_values(self):
        """Test counter accumulates values."""
        counter = PrometheusCounter(name="test_counter")
        counter.inc(1.0)
        counter.inc(2.0)
        counter.inc(3.0)
        assert counter.get() == 6.0
    
    def test_with_labels(self):
        """Test counter with labels."""
        counter = PrometheusCounter(name="test_counter", labels=("method",))
        counter.inc(labels={"method": "GET"})
        counter.inc(labels={"method": "POST"})
        
        assert counter.get({"method": "GET"}) == 1.0
        assert counter.get({"method": "POST"}) == 1.0
    
    def test_multiple_label_values(self):
        """Test counter with multiple label values."""
        counter = PrometheusCounter(name="test_counter")
        counter.inc(5.0, {"status": "200"})
        counter.inc(2.0, {"status": "500"})
        
        assert counter.get({"status": "200"}) == 5.0
        assert counter.get({"status": "500"}) == 2.0
    
    def test_get_nonexistent(self):
        """Test getting nonexistent counter value."""
        counter = PrometheusCounter(name="test_counter")
        assert counter.get() == 0.0
        assert counter.get({"method": "GET"}) == 0.0
    
    def test_expose_basic(self):
        """Test Prometheus format exposure."""
        counter = PrometheusCounter(name="test_counter", help="Test counter")
        counter.inc(5.0)
        
        output = counter.expose()
        assert "# HELP test_counter Test counter" in output
        assert "# TYPE test_counter counter" in output
        assert "test_counter 5" in output
    
    def test_expose_with_labels(self):
        """Test exposure with labels."""
        counter = PrometheusCounter(name="test_counter")
        counter.inc(labels={"method": "GET", "path": "/api"})
        
        output = counter.expose()
        assert 'test_counter{method="GET",path="/api"}' in output
    
    def test_labels_key_sorted(self):
        """Test labels are sorted consistently."""
        counter = PrometheusCounter(name="test_counter")
        counter.inc(labels={"z": "1", "a": "2"})
        counter.inc(labels={"a": "2", "z": "1"})
        
        # Both should hit the same key
        assert counter.get({"a": "2", "z": "1"}) == 2.0
    
    def test_empty_values_not_exposed(self):
        """Test counter with no values exposes minimal output."""
        counter = PrometheusCounter(name="test_counter", help="Test")
        output = counter.expose()
        assert "# HELP" in output
        assert "# TYPE" in output
    
    def test_help_text(self):
        """Test help text is included."""
        counter = PrometheusCounter(name="my_counter", help="Counts things")
        output = counter.expose()
        assert "# HELP my_counter Counts things" in output
    
    def test_no_help_text(self):
        """Test counter without help text."""
        counter = PrometheusCounter(name="my_counter")
        counter.inc()
        output = counter.expose()
        assert "# TYPE my_counter counter" in output
    
    def test_multiple_label_combinations(self):
        """Test multiple different label combinations."""
        counter = PrometheusCounter(name="requests")
        counter.inc(labels={"method": "GET", "status": "200"})
        counter.inc(labels={"method": "POST", "status": "201"})
        counter.inc(labels={"method": "GET", "status": "404"})
        
        assert counter.get({"method": "GET", "status": "200"}) == 1.0
        assert counter.get({"method": "POST", "status": "201"}) == 1.0
        assert counter.get({"method": "GET", "status": "404"}) == 1.0
    
    def test_float_values(self):
        """Test counter with float values."""
        counter = PrometheusCounter(name="test_counter")
        counter.inc(0.5)
        counter.inc(0.3)
        assert abs(counter.get() - 0.8) < 0.001
    
    def test_large_values(self):
        """Test counter with large values."""
        counter = PrometheusCounter(name="test_counter")
        counter.inc(1000000.0)
        counter.inc(2000000.0)
        assert counter.get() == 3000000.0


# ============================================================================
# PrometheusGauge Tests (15 tests)
# ============================================================================

class TestPrometheusGauge:
    """Tests for PrometheusGauge class."""
    
    def test_set_value(self):
        """Test setting gauge value."""
        gauge = PrometheusGauge(name="test_gauge")
        gauge.set(42.0)
        assert gauge.get() == 42.0
    
    def test_set_overwrites(self):
        """Test set overwrites previous value."""
        gauge = PrometheusGauge(name="test_gauge")
        gauge.set(10.0)
        gauge.set(20.0)
        assert gauge.get() == 20.0
    
    def test_increment(self):
        """Test gauge increment."""
        gauge = PrometheusGauge(name="test_gauge")
        gauge.set(10.0)
        gauge.inc(5.0)
        assert gauge.get() == 15.0
    
    def test_decrement(self):
        """Test gauge decrement."""
        gauge = PrometheusGauge(name="test_gauge")
        gauge.set(10.0)
        gauge.dec(3.0)
        assert gauge.get() == 7.0
    
    def test_with_labels(self):
        """Test gauge with labels."""
        gauge = PrometheusGauge(name="test_gauge")
        gauge.set(5.0, {"pool": "main"})
        gauge.set(10.0, {"pool": "replica"})
        
        assert gauge.get({"pool": "main"}) == 5.0
        assert gauge.get({"pool": "replica"}) == 10.0
    
    def test_get_nonexistent(self):
        """Test getting nonexistent gauge value."""
        gauge = PrometheusGauge(name="test_gauge")
        assert gauge.get() == 0.0
    
    def test_expose_basic(self):
        """Test Prometheus format exposure."""
        gauge = PrometheusGauge(name="test_gauge", help="Test gauge")
        gauge.set(42.0)
        
        output = gauge.expose()
        assert "# HELP test_gauge Test gauge" in output
        assert "# TYPE test_gauge gauge" in output
        assert "test_gauge 42" in output
    
    def test_expose_with_labels(self):
        """Test exposure with labels."""
        gauge = PrometheusGauge(name="connections")
        gauge.set(5.0, {"pool": "main"})
        
        output = gauge.expose()
        assert 'connections{pool="main"}' in output
    
    def test_negative_values(self):
        """Test gauge with negative values."""
        gauge = PrometheusGauge(name="test_gauge")
        gauge.set(-5.0)
        assert gauge.get() == -5.0
    
    def test_zero_value(self):
        """Test gauge with zero value."""
        gauge = PrometheusGauge(name="test_gauge")
        gauge.set(10.0)
        gauge.set(0.0)
        assert gauge.get() == 0.0
    
    def test_inc_from_zero(self):
        """Test increment from zero."""
        gauge = PrometheusGauge(name="test_gauge")
        gauge.inc(5.0)
        assert gauge.get() == 5.0
    
    def test_dec_from_zero(self):
        """Test decrement from zero."""
        gauge = PrometheusGauge(name="test_gauge")
        gauge.dec(5.0)
        assert gauge.get() == -5.0
    
    def test_multiple_label_combinations(self):
        """Test multiple different label combinations."""
        gauge = PrometheusGauge(name="pool_size")
        gauge.set(10.0, {"pool": "main", "type": "active"})
        gauge.set(5.0, {"pool": "main", "type": "idle"})
        
        assert gauge.get({"pool": "main", "type": "active"}) == 10.0
        assert gauge.get({"pool": "main", "type": "idle"}) == 5.0
    
    def test_float_precision(self):
        """Test gauge with float precision."""
        gauge = PrometheusGauge(name="test_gauge")
        gauge.set(0.123456789)
        assert abs(gauge.get() - 0.123456789) < 1e-9
    
    def test_help_text(self):
        """Test help text is included."""
        gauge = PrometheusGauge(name="my_gauge", help="Current value")
        gauge.set(1.0)
        output = gauge.expose()
        assert "# HELP my_gauge Current value" in output


# ============================================================================
# PrometheusHistogram Tests (15 tests)
# ============================================================================

class TestPrometheusHistogram:
    """Tests for PrometheusHistogram class."""
    
    def test_observe_single(self):
        """Test single observation."""
        histogram = PrometheusHistogram(name="test_histogram")
        histogram.observe(0.5)
        assert histogram.get_observations() == [0.5]
    
    def test_observe_multiple(self):
        """Test multiple observations."""
        histogram = PrometheusHistogram(name="test_histogram")
        histogram.observe(0.1)
        histogram.observe(0.5)
        histogram.observe(1.0)
        assert histogram.get_observations() == [0.1, 0.5, 1.0]
    
    def test_with_labels(self):
        """Test histogram with labels."""
        histogram = PrometheusHistogram(name="test_histogram")
        histogram.observe(0.1, {"table": "users"})
        histogram.observe(0.5, {"table": "orders"})
        
        assert histogram.get_observations({"table": "users"}) == [0.1]
        assert histogram.get_observations({"table": "orders"}) == [0.5]
    
    def test_get_nonexistent(self):
        """Test getting nonexistent histogram observations."""
        histogram = PrometheusHistogram(name="test_histogram")
        assert histogram.get_observations() == []
    
    def test_custom_buckets(self):
        """Test histogram with custom buckets."""
        buckets = (0.01, 0.1, 1.0, 10.0)
        histogram = PrometheusHistogram(name="test_histogram", buckets=buckets)
        assert histogram.buckets == buckets
    
    def test_expose_basic(self):
        """Test Prometheus format exposure."""
        histogram = PrometheusHistogram(
            name="test_histogram",
            help="Test histogram",
            buckets=(0.1, 0.5, 1.0),
        )
        histogram.observe(0.2)
        histogram.observe(0.8)
        
        output = histogram.expose()
        assert "# HELP test_histogram Test histogram" in output
        assert "# TYPE test_histogram histogram" in output
        assert "test_histogram_bucket" in output
        assert "test_histogram_sum" in output
        assert "test_histogram_count" in output
    
    def test_expose_buckets(self):
        """Test bucket values in exposure."""
        histogram = PrometheusHistogram(
            name="duration",
            buckets=(0.1, 0.5, 1.0),
        )
        histogram.observe(0.2)  # Falls in 0.5 bucket
        histogram.observe(0.8)  # Falls in 1.0 bucket
        
        output = histogram.expose()
        assert 'le="0.1"' in output
        assert 'le="0.5"' in output
        assert 'le="1.0"' in output
        assert 'le="+Inf"' in output
    
    def test_expose_sum(self):
        """Test sum value in exposure."""
        histogram = PrometheusHistogram(name="duration", buckets=(1.0,))
        histogram.observe(0.1)
        histogram.observe(0.2)
        histogram.observe(0.3)
        
        output = histogram.expose()
        assert "duration_sum 0.6" in output or "duration_sum{} 0.6" in output
    
    def test_expose_count(self):
        """Test count value in exposure."""
        histogram = PrometheusHistogram(name="duration", buckets=(1.0,))
        histogram.observe(0.1)
        histogram.observe(0.2)
        histogram.observe(0.3)
        
        output = histogram.expose()
        assert "duration_count 3" in output or "duration_count{} 3" in output
    
    def test_bucket_cumulative(self):
        """Test bucket counts are cumulative."""
        histogram = PrometheusHistogram(
            name="duration",
            buckets=(0.1, 0.5, 1.0),
        )
        # All values
        histogram.observe(0.05)  # <= 0.1
        histogram.observe(0.2)   # <= 0.5
        histogram.observe(0.8)   # <= 1.0
        
        output = histogram.expose()
        # Buckets should be cumulative
        # 0.1 bucket: 1 (just 0.05)
        # 0.5 bucket: 2 (0.05 + 0.2)
        # 1.0 bucket: 3 (0.05 + 0.2 + 0.8)
        assert 'le="0.1"} 1' in output
        assert 'le="0.5"} 2' in output
        assert 'le="1.0"} 3' in output
    
    def test_expose_with_labels(self):
        """Test exposure with labels."""
        histogram = PrometheusHistogram(name="duration", buckets=(1.0,))
        histogram.observe(0.5, {"table": "users"})
        
        output = histogram.expose()
        assert 'table="users"' in output
    
    def test_many_observations(self):
        """Test histogram with many observations."""
        histogram = PrometheusHistogram(name="test_histogram")
        for i in range(100):
            histogram.observe(i / 100.0)
        
        assert len(histogram.get_observations()) == 100
    
    def test_zero_observation(self):
        """Test histogram with zero observation."""
        histogram = PrometheusHistogram(name="duration", buckets=(0.1, 1.0))
        histogram.observe(0.0)
        
        observations = histogram.get_observations()
        assert 0.0 in observations
    
    def test_large_observation(self):
        """Test histogram with large observation."""
        histogram = PrometheusHistogram(name="duration", buckets=(1.0, 10.0))
        histogram.observe(100.0)  # Larger than all buckets
        
        output = histogram.expose()
        assert 'le="+Inf"} 1' in output
    
    def test_help_text(self):
        """Test help text is included."""
        histogram = PrometheusHistogram(
            name="my_histogram",
            help="Distribution of values",
        )
        histogram.observe(1.0)
        output = histogram.expose()
        assert "# HELP my_histogram Distribution of values" in output


# ============================================================================
# PrometheusRegistry Tests (20 tests)
# ============================================================================

class TestPrometheusRegistry:
    """Tests for PrometheusRegistry class."""
    
    def test_register_counter(self):
        """Test registering a counter."""
        registry = PrometheusRegistry()
        counter = registry.register_counter("test_counter", "A test counter")
        assert counter is not None
        assert counter.name == "test_counter"
    
    def test_register_gauge(self):
        """Test registering a gauge."""
        registry = PrometheusRegistry()
        gauge = registry.register_gauge("test_gauge", "A test gauge")
        assert gauge is not None
        assert gauge.name == "test_gauge"
    
    def test_register_histogram(self):
        """Test registering a histogram."""
        registry = PrometheusRegistry()
        histogram = registry.register_histogram("test_histogram", "A test histogram")
        assert histogram is not None
        assert histogram.name == "test_histogram"
    
    def test_counter_inc(self):
        """Test incrementing counter via registry."""
        registry = PrometheusRegistry()
        registry.counter_inc("requests", labels={"method": "GET"})
        registry.counter_inc("requests", labels={"method": "GET"})
        
        counter = registry.get_counter("requests")
        assert counter.get({"method": "GET"}) == 2.0
    
    def test_gauge_set(self):
        """Test setting gauge via registry."""
        registry = PrometheusRegistry()
        registry.gauge_set("connections", 42.0, {"pool": "main"})
        
        gauge = registry.get_gauge("connections")
        assert gauge.get({"pool": "main"}) == 42.0
    
    def test_histogram_observe(self):
        """Test observing histogram via registry."""
        registry = PrometheusRegistry()
        registry.histogram_observe("duration", 0.5, {"table": "users"})
        
        histogram = registry.get_histogram("duration")
        assert histogram.get_observations({"table": "users"}) == [0.5]
    
    def test_get_nonexistent_counter(self):
        """Test getting nonexistent counter."""
        registry = PrometheusRegistry()
        assert registry.get_counter("nonexistent") is None
    
    def test_auto_create_counter(self):
        """Test counter is auto-created on first use."""
        registry = PrometheusRegistry()
        registry.counter_inc("new_counter")
        assert registry.get_counter("new_counter") is not None
    
    def test_auto_create_gauge(self):
        """Test gauge is auto-created on first use."""
        registry = PrometheusRegistry()
        registry.gauge_set("new_gauge", 1.0)
        assert registry.get_gauge("new_gauge") is not None
    
    def test_auto_create_histogram(self):
        """Test histogram is auto-created on first use."""
        registry = PrometheusRegistry()
        registry.histogram_observe("new_histogram", 1.0)
        assert registry.get_histogram("new_histogram") is not None
    
    def test_expose(self):
        """Test Prometheus format exposition."""
        registry = PrometheusRegistry()
        registry.counter_inc("requests_total")
        registry.gauge_set("connections_active", 5.0)
        registry.histogram_observe("query_duration", 0.1)
        
        output = registry.expose()
        assert "requests_total" in output
        assert "connections_active" in output
        assert "query_duration" in output
    
    def test_expose_empty(self):
        """Test exposition with no metrics."""
        registry = PrometheusRegistry()
        output = registry.expose()
        assert output == ""
    
    def test_reset(self):
        """Test resetting all metrics."""
        registry = PrometheusRegistry()
        registry.counter_inc("requests")
        registry.gauge_set("connections", 5.0)
        registry.histogram_observe("duration", 0.5)
        
        registry.reset()
        
        assert registry.get_counter("requests") is None
        assert registry.get_gauge("connections") is None
        assert registry.get_histogram("duration") is None
    
    def test_get_metrics(self):
        """Test getting all metrics as dictionary."""
        registry = PrometheusRegistry()
        registry.counter_inc("requests")
        registry.gauge_set("connections", 5.0)
        registry.histogram_observe("duration", 0.5)
        
        metrics = registry.get_metrics()
        assert "counters" in metrics
        assert "gauges" in metrics
        assert "histograms" in metrics
    
    def test_thread_safety(self):
        """Test registry is thread-safe."""
        registry = PrometheusRegistry()
        
        def increment():
            for _ in range(1000):
                registry.counter_inc("test_counter")
        
        threads = [threading.Thread(target=increment) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        counter = registry.get_counter("test_counter")
        assert counter.get() == 10000.0
    
    def test_custom_buckets(self):
        """Test registry with custom buckets."""
        buckets = (0.01, 0.1, 1.0)
        registry = PrometheusRegistry(buckets=buckets)
        registry.histogram_observe("duration", 0.5)
        
        histogram = registry.get_histogram("duration")
        assert histogram.buckets == buckets
    
    def test_register_same_counter_twice(self):
        """Test registering same counter twice returns same instance."""
        registry = PrometheusRegistry()
        counter1 = registry.register_counter("test_counter")
        counter2 = registry.register_counter("test_counter")
        assert counter1 is counter2
    
    def test_expose_multiple_sections(self):
        """Test exposition has proper formatting."""
        registry = PrometheusRegistry()
        registry.counter_inc("counter1")
        registry.counter_inc("counter2")
        
        output = registry.expose()
        # Should have separation between metrics
        assert output.count("# TYPE") == 2
    
    def test_register_with_labels(self):
        """Test registering with labels."""
        registry = PrometheusRegistry()
        counter = registry.register_counter(
            "requests",
            help="Total requests",
            labels=("method", "path"),
        )
        assert counter.labels == ("method", "path")
    
    def test_expose_sorted_labels(self):
        """Test labels are sorted in exposition."""
        registry = PrometheusRegistry()
        registry.counter_inc("test", labels={"z": "1", "a": "2"})
        
        output = registry.expose()
        # Labels should be sorted alphabetically
        assert 'a="2",z="1"' in output


# ============================================================================
# PrometheusBackend Tests (15 tests)
# ============================================================================

class TestPrometheusBackend:
    """Tests for PrometheusBackend class."""
    
    def test_default_creation(self):
        """Test creating backend with defaults."""
        backend = PrometheusBackend()
        assert backend is not None
    
    def test_custom_config(self):
        """Test creating backend with custom config."""
        config = MetricsConfig(prefix="custom")
        backend = PrometheusBackend(config)
        assert backend._config.prefix == "custom"
    
    def test_counter_inc(self):
        """Test counter increment."""
        backend = PrometheusBackend()
        backend.counter_inc("test_counter")
        
        metrics = backend.get_metrics()
        assert "test_counter" in metrics["counters"]
    
    def test_gauge_set(self):
        """Test gauge set."""
        backend = PrometheusBackend()
        backend.gauge_set("test_gauge", 42.0)
        
        metrics = backend.get_metrics()
        assert "test_gauge" in metrics["gauges"]
    
    def test_histogram_observe(self):
        """Test histogram observe."""
        backend = PrometheusBackend()
        backend.histogram_observe("test_histogram", 0.5)
        
        metrics = backend.get_metrics()
        assert "test_histogram" in metrics["histograms"]
    
    def test_get_metrics(self):
        """Test getting all metrics."""
        backend = PrometheusBackend()
        backend.counter_inc("counter")
        backend.gauge_set("gauge", 1.0)
        backend.histogram_observe("histogram", 0.5)
        
        metrics = backend.get_metrics()
        assert "counters" in metrics
        assert "gauges" in metrics
        assert "histograms" in metrics
    
    def test_reset(self):
        """Test resetting all metrics."""
        backend = PrometheusBackend()
        backend.counter_inc("counter")
        backend.reset()
        
        metrics = backend.get_metrics()
        assert metrics["counters"] == {}
    
    def test_expose(self):
        """Test Prometheus format exposition."""
        backend = PrometheusBackend()
        backend.counter_inc("test_counter")
        
        output = backend.expose()
        assert "test_counter" in output
    
    def test_get_content_type(self):
        """Test getting content type header."""
        backend = PrometheusBackend()
        content_type = backend.get_content_type()
        assert "text/plain" in content_type
        assert "version=0.0.4" in content_type
    
    def test_get_registry(self):
        """Test getting underlying registry."""
        backend = PrometheusBackend()
        registry = backend.get_registry()
        assert isinstance(registry, PrometheusRegistry)
    
    def test_standard_metrics_registered(self):
        """Test standard metrics are registered."""
        backend = PrometheusBackend()
        registry = backend.get_registry()
        
        # Check some standard metrics exist
        assert registry.get_counter("pynext_db_queries_total") is not None
    
    def test_labels_in_exposition(self):
        """Test labels appear in exposition."""
        backend = PrometheusBackend()
        backend.counter_inc("test_counter", labels={"method": "GET"})
        
        output = backend.expose()
        assert 'method="GET"' in output
    
    def test_custom_prefix(self):
        """Test custom prefix in metric names."""
        config = MetricsConfig(prefix="myapp")
        backend = PrometheusBackend(config)
        
        backend.counter_inc("test_counter")
        output = backend.expose()
        # Note: counter_inc takes full name, but standard metrics use prefix
        assert "test_counter" in output
    
    def test_create_prometheus_backend_helper(self):
        """Test create_prometheus_backend helper function."""
        backend = create_prometheus_backend(prefix="custom", buckets=(0.1, 1.0, 10.0))
        assert backend._config.prefix == "custom"
        assert backend._config.buckets == (0.1, 1.0, 10.0)
    
    def test_metrics_interface(self):
        """Test backend implements MetricsBackend interface."""
        from pynext.db.adapters.postgres_metrics import MetricsBackend
        
        backend = PrometheusBackend()
        assert isinstance(backend, MetricsBackend)

