"""
Tests for PyNext Database Metrics Module.

100 comprehensive tests covering:
- MetricsConfig validation and defaults (15 tests)
- MetricType and BackendType enums (10 tests)
- MemoryBackend operations (25 tests)
- MetricsCollector functionality (35 tests)
- Timer context manager (10 tests)
- Edge cases and performance (5 tests)
"""

import asyncio
import threading
import time
from unittest.mock import MagicMock, patch

import pytest

from pynext.db.adapters.postgres_metrics import (
    MetricsConfig,
    MetricType,
    BackendType,
    MetricDefinition,
    STANDARD_METRICS,
    DEFAULT_BUCKETS,
    DEFAULT_PREFIX,
    MetricsBackend,
    MemoryBackend,
    MetricsCollector,
    Timer,
    create_collector,
)


# ============================================================================
# MetricsConfig Tests (15 tests)
# ============================================================================

class TestMetricsConfig:
    """Tests for MetricsConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = MetricsConfig()
        assert config.enabled is True
        assert config.backend == BackendType.MEMORY
        assert config.prefix == DEFAULT_PREFIX
        assert config.buckets == DEFAULT_BUCKETS
        assert config.labels == {}
        assert config.collect_pool_metrics is True
        assert config.collect_query_metrics is True
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = MetricsConfig(
            backend=BackendType.PROMETHEUS,
            prefix="myapp_db",
            collect_pool_metrics=False,
        )
        assert config.backend == BackendType.PROMETHEUS
        assert config.prefix == "myapp_db"
        assert config.collect_pool_metrics is False
    
    def test_string_backend_conversion(self):
        """Test string to BackendType conversion."""
        config = MetricsConfig(backend="prometheus")
        assert config.backend == BackendType.PROMETHEUS
        
        config2 = MetricsConfig(backend="opentelemetry")
        assert config2.backend == BackendType.OPENTELEMETRY
    
    def test_custom_buckets(self):
        """Test custom histogram buckets."""
        buckets = (0.01, 0.1, 1.0, 10.0)
        config = MetricsConfig(buckets=buckets)
        assert config.buckets == buckets
    
    def test_custom_labels(self):
        """Test custom default labels."""
        labels = {"service": "api", "env": "prod"}
        config = MetricsConfig(labels=labels)
        assert config.labels == labels
    
    def test_disabled_config(self):
        """Test disabled metrics."""
        config = MetricsConfig(enabled=False)
        assert config.enabled is False
    
    def test_custom_quantiles(self):
        """Test custom histogram quantiles."""
        quantiles = (0.5, 0.75, 0.99)
        config = MetricsConfig(histogram_quantiles=quantiles)
        assert config.histogram_quantiles == quantiles
    
    def test_empty_prefix_uses_default(self):
        """Test empty prefix falls back to default."""
        config = MetricsConfig(prefix="")
        assert config.prefix == DEFAULT_PREFIX
    
    def test_empty_buckets_uses_default(self):
        """Test empty buckets falls back to default."""
        config = MetricsConfig(buckets=())
        assert config.buckets == DEFAULT_BUCKETS
    
    def test_all_backends(self):
        """Test all backend types can be set."""
        for backend in BackendType:
            config = MetricsConfig(backend=backend)
            assert config.backend == backend
    
    def test_collect_flags_independent(self):
        """Test pool and query collection flags are independent."""
        config = MetricsConfig(
            collect_pool_metrics=False,
            collect_query_metrics=True,
        )
        assert config.collect_pool_metrics is False
        assert config.collect_query_metrics is True
    
    def test_custom_prefix(self):
        """Test custom metric prefix."""
        config = MetricsConfig(prefix="custom_db")
        assert config.prefix == "custom_db"
    
    def test_memory_backend_default(self):
        """Test memory backend is default."""
        config = MetricsConfig()
        assert config.backend == BackendType.MEMORY
    
    def test_default_buckets_value(self):
        """Test default buckets have sensible values."""
        assert DEFAULT_BUCKETS[0] == 0.001  # 1ms
        assert DEFAULT_BUCKETS[-1] == 10.0  # 10s
        assert len(DEFAULT_BUCKETS) == 12
    
    def test_default_prefix_value(self):
        """Test default prefix value."""
        assert DEFAULT_PREFIX == "pynext_db"


# ============================================================================
# MetricType and BackendType Tests (10 tests)
# ============================================================================

class TestMetricTypeEnum:
    """Tests for MetricType enum."""
    
    def test_all_types_exist(self):
        """Test all expected metric types exist."""
        assert MetricType.COUNTER
        assert MetricType.GAUGE
        assert MetricType.HISTOGRAM
    
    def test_type_string_values(self):
        """Test type string values."""
        assert MetricType.COUNTER.value == "counter"
        assert MetricType.GAUGE.value == "gauge"
        assert MetricType.HISTOGRAM.value == "histogram"
    
    def test_type_from_string(self):
        """Test creating type from string."""
        assert MetricType("counter") == MetricType.COUNTER
        assert MetricType("gauge") == MetricType.GAUGE
        assert MetricType("histogram") == MetricType.HISTOGRAM


class TestBackendTypeEnum:
    """Tests for BackendType enum."""
    
    def test_all_backends_exist(self):
        """Test all expected backends exist."""
        assert BackendType.PROMETHEUS
        assert BackendType.OPENTELEMETRY
        assert BackendType.MEMORY
    
    def test_backend_string_values(self):
        """Test backend string values."""
        assert BackendType.PROMETHEUS.value == "prometheus"
        assert BackendType.OPENTELEMETRY.value == "opentelemetry"
        assert BackendType.MEMORY.value == "memory"
    
    def test_backend_from_string(self):
        """Test creating backend from string."""
        assert BackendType("prometheus") == BackendType.PROMETHEUS
        assert BackendType("opentelemetry") == BackendType.OPENTELEMETRY
        assert BackendType("memory") == BackendType.MEMORY


class TestMetricDefinition:
    """Tests for MetricDefinition dataclass."""
    
    def test_definition_creation(self):
        """Test creating a metric definition."""
        definition = MetricDefinition(
            name="test_metric",
            type=MetricType.COUNTER,
            description="A test metric",
            labels=("label1", "label2"),
        )
        assert definition.name == "test_metric"
        assert definition.type == MetricType.COUNTER
        assert definition.description == "A test metric"
        assert definition.labels == ("label1", "label2")
    
    def test_full_name(self):
        """Test getting full metric name with prefix."""
        definition = MetricDefinition(
            name="queries_total",
            type=MetricType.COUNTER,
            description="Total queries",
        )
        assert definition.full_name("myapp") == "myapp_queries_total"
    
    def test_default_labels(self):
        """Test default empty labels."""
        definition = MetricDefinition(
            name="test",
            type=MetricType.GAUGE,
            description="Test",
        )
        assert definition.labels == ()
    
    def test_unit_field(self):
        """Test unit field."""
        definition = MetricDefinition(
            name="duration",
            type=MetricType.HISTOGRAM,
            description="Duration",
            unit="seconds",
        )
        assert definition.unit == "seconds"


class TestStandardMetrics:
    """Tests for standard metric definitions."""
    
    def test_standard_metrics_exist(self):
        """Test standard metrics are defined."""
        assert "connections_active" in STANDARD_METRICS
        assert "connections_idle" in STANDARD_METRICS
        assert "queries_total" in STANDARD_METRICS
        assert "query_duration_seconds" in STANDARD_METRICS
    
    def test_query_metrics_have_labels(self):
        """Test query metrics have appropriate labels."""
        queries_total = STANDARD_METRICS["queries_total"]
        assert "query_type" in queries_total.labels
        assert "table" in queries_total.labels
        assert "status" in queries_total.labels


# ============================================================================
# MemoryBackend Tests (25 tests)
# ============================================================================

class TestMemoryBackend:
    """Tests for MemoryBackend class."""
    
    def test_counter_inc_basic(self):
        """Test basic counter increment."""
        backend = MemoryBackend()
        backend.counter_inc("test_counter")
        assert backend.get_counter("test_counter") == 1.0
    
    def test_counter_inc_with_value(self):
        """Test counter increment with custom value."""
        backend = MemoryBackend()
        backend.counter_inc("test_counter", value=5.0)
        assert backend.get_counter("test_counter") == 5.0
    
    def test_counter_inc_accumulates(self):
        """Test counter accumulates values."""
        backend = MemoryBackend()
        backend.counter_inc("test_counter", value=1.0)
        backend.counter_inc("test_counter", value=2.0)
        backend.counter_inc("test_counter", value=3.0)
        assert backend.get_counter("test_counter") == 6.0
    
    def test_counter_with_labels(self):
        """Test counter with labels."""
        backend = MemoryBackend()
        backend.counter_inc("test_counter", labels={"method": "GET"})
        backend.counter_inc("test_counter", labels={"method": "POST"})
        
        assert backend.get_counter("test_counter", {"method": "GET"}) == 1.0
        assert backend.get_counter("test_counter", {"method": "POST"}) == 1.0
    
    def test_gauge_set(self):
        """Test gauge set."""
        backend = MemoryBackend()
        backend.gauge_set("test_gauge", 42.0)
        assert backend.get_gauge("test_gauge") == 42.0
    
    def test_gauge_set_overwrites(self):
        """Test gauge set overwrites previous value."""
        backend = MemoryBackend()
        backend.gauge_set("test_gauge", 10.0)
        backend.gauge_set("test_gauge", 20.0)
        assert backend.get_gauge("test_gauge") == 20.0
    
    def test_gauge_with_labels(self):
        """Test gauge with labels."""
        backend = MemoryBackend()
        backend.gauge_set("test_gauge", 5.0, labels={"pool": "main"})
        backend.gauge_set("test_gauge", 10.0, labels={"pool": "replica"})
        
        assert backend.get_gauge("test_gauge", {"pool": "main"}) == 5.0
        assert backend.get_gauge("test_gauge", {"pool": "replica"}) == 10.0
    
    def test_gauge_inc(self):
        """Test gauge increment."""
        backend = MemoryBackend()
        backend.gauge_set("test_gauge", 10.0)
        backend.gauge_inc("test_gauge", 5.0)
        assert backend.get_gauge("test_gauge") == 15.0
    
    def test_gauge_dec(self):
        """Test gauge decrement."""
        backend = MemoryBackend()
        backend.gauge_set("test_gauge", 10.0)
        backend.gauge_dec("test_gauge", 3.0)
        assert backend.get_gauge("test_gauge") == 7.0
    
    def test_histogram_observe(self):
        """Test histogram observation."""
        backend = MemoryBackend()
        backend.histogram_observe("test_histogram", 0.5)
        observations = backend.get_histogram("test_histogram")
        assert observations == [0.5]
    
    def test_histogram_multiple_observations(self):
        """Test multiple histogram observations."""
        backend = MemoryBackend()
        backend.histogram_observe("test_histogram", 0.1)
        backend.histogram_observe("test_histogram", 0.5)
        backend.histogram_observe("test_histogram", 1.0)
        observations = backend.get_histogram("test_histogram")
        assert observations == [0.1, 0.5, 1.0]
    
    def test_histogram_with_labels(self):
        """Test histogram with labels."""
        backend = MemoryBackend()
        backend.histogram_observe("test_histogram", 0.1, {"table": "users"})
        backend.histogram_observe("test_histogram", 0.5, {"table": "orders"})
        
        assert backend.get_histogram("test_histogram", {"table": "users"}) == [0.1]
        assert backend.get_histogram("test_histogram", {"table": "orders"}) == [0.5]
    
    def test_histogram_stats(self):
        """Test histogram statistics."""
        backend = MemoryBackend()
        backend.histogram_observe("test_histogram", 1.0)
        backend.histogram_observe("test_histogram", 2.0)
        backend.histogram_observe("test_histogram", 3.0)
        
        stats = backend.get_histogram_stats("test_histogram")
        assert stats["count"] == 3
        assert stats["sum"] == 6.0
        assert stats["min"] == 1.0
        assert stats["max"] == 3.0
        assert stats["avg"] == 2.0
    
    def test_histogram_stats_empty(self):
        """Test histogram statistics for empty histogram."""
        backend = MemoryBackend()
        stats = backend.get_histogram_stats("nonexistent")
        assert stats["count"] == 0
        assert stats["sum"] == 0
    
    def test_get_metrics(self):
        """Test getting all metrics."""
        backend = MemoryBackend()
        backend.counter_inc("counter1")
        backend.gauge_set("gauge1", 10.0)
        backend.histogram_observe("hist1", 0.5)
        
        metrics = backend.get_metrics()
        assert "counters" in metrics
        assert "gauges" in metrics
        assert "histograms" in metrics
    
    def test_reset(self):
        """Test resetting all metrics."""
        backend = MemoryBackend()
        backend.counter_inc("counter1")
        backend.gauge_set("gauge1", 10.0)
        backend.histogram_observe("hist1", 0.5)
        
        backend.reset()
        
        assert backend.get_counter("counter1") == 0.0
        assert backend.get_gauge("gauge1") == 0.0
        assert backend.get_histogram("hist1") == []
    
    def test_nonexistent_counter(self):
        """Test getting nonexistent counter returns 0."""
        backend = MemoryBackend()
        assert backend.get_counter("nonexistent") == 0.0
    
    def test_nonexistent_gauge(self):
        """Test getting nonexistent gauge returns 0."""
        backend = MemoryBackend()
        assert backend.get_gauge("nonexistent") == 0.0
    
    def test_nonexistent_histogram(self):
        """Test getting nonexistent histogram returns empty list."""
        backend = MemoryBackend()
        assert backend.get_histogram("nonexistent") == []
    
    def test_labels_key_generation(self):
        """Test labels key is deterministic."""
        backend = MemoryBackend()
        # Same labels in different order should produce same key
        labels1 = {"a": "1", "b": "2"}
        labels2 = {"b": "2", "a": "1"}
        
        key1 = backend._labels_key(labels1)
        key2 = backend._labels_key(labels2)
        assert key1 == key2
    
    def test_thread_safety_counter(self):
        """Test counter is thread-safe."""
        backend = MemoryBackend()
        
        def increment():
            for _ in range(1000):
                backend.counter_inc("test_counter")
        
        threads = [threading.Thread(target=increment) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert backend.get_counter("test_counter") == 10000.0
    
    def test_thread_safety_gauge(self):
        """Test gauge is thread-safe."""
        backend = MemoryBackend()
        
        def set_gauge(value):
            for _ in range(100):
                backend.gauge_set("test_gauge", value)
        
        threads = [threading.Thread(target=set_gauge, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Gauge should have some valid value (last write wins)
        assert 0 <= backend.get_gauge("test_gauge") < 10
    
    def test_thread_safety_histogram(self):
        """Test histogram is thread-safe."""
        backend = MemoryBackend()
        
        def observe():
            for _ in range(100):
                backend.histogram_observe("test_histogram", 0.5)
        
        threads = [threading.Thread(target=observe) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        observations = backend.get_histogram("test_histogram")
        assert len(observations) == 1000
    
    def test_empty_labels(self):
        """Test empty labels work correctly."""
        backend = MemoryBackend()
        backend.counter_inc("test_counter", labels={})
        backend.counter_inc("test_counter", labels=None)
        assert backend.get_counter("test_counter") == 2.0


# ============================================================================
# MetricsCollector Tests (35 tests)
# ============================================================================

class TestMetricsCollector:
    """Tests for MetricsCollector class."""
    
    def test_default_creation(self):
        """Test creating collector with defaults."""
        collector = MetricsCollector()
        assert collector.enabled is True
        assert collector.config.backend == BackendType.MEMORY
    
    def test_custom_config(self):
        """Test creating collector with custom config."""
        config = MetricsConfig(prefix="custom", collect_pool_metrics=False)
        collector = MetricsCollector(config)
        assert collector.config.prefix == "custom"
    
    def test_disabled_collector(self):
        """Test disabled collector does nothing."""
        config = MetricsConfig(enabled=False)
        collector = MetricsCollector(config)
        
        collector.record_query("SELECT", "users", 0.1)
        metrics = collector.get_metrics()
        assert metrics["counters"] == {}
    
    def test_record_query_success(self):
        """Test recording successful query."""
        collector = MetricsCollector()
        collector.record_query("SELECT", "users", 0.1, "success")
        
        backend = collector.get_backend()
        labels = {"query_type": "SELECT", "table": "users", "status": "success"}
        assert backend.get_counter("pynext_db_queries_total", labels) == 1.0
    
    def test_record_query_duration(self):
        """Test recording query duration."""
        collector = MetricsCollector()
        collector.record_query("SELECT", "users", 0.5)
        
        backend = collector.get_backend()
        labels = {"query_type": "SELECT", "table": "users"}
        observations = backend.get_histogram("pynext_db_query_duration_seconds", labels)
        assert observations == [0.5]
    
    def test_record_query_error(self):
        """Test recording query error."""
        collector = MetricsCollector()
        collector.record_query_error("SELECT", "TimeoutError")
        
        backend = collector.get_backend()
        labels = {"query_type": "SELECT", "error_type": "TimeoutError"}
        assert backend.get_counter("pynext_db_query_errors_total", labels) == 1.0
    
    def test_record_slow_query(self):
        """Test recording slow query."""
        collector = MetricsCollector()
        collector.record_slow_query("users")
        
        backend = collector.get_backend()
        assert backend.get_counter("pynext_db_slow_queries_total", {"table": "users"}) == 1.0
    
    def test_record_pool_stats(self):
        """Test recording pool statistics."""
        collector = MetricsCollector()
        collector.record_pool_stats("main", active=5, idle=10, waiting=2)
        
        backend = collector.get_backend()
        labels = {"pool_name": "main"}
        assert backend.get_gauge("pynext_db_connections_active", labels) == 5.0
        assert backend.get_gauge("pynext_db_connections_idle", labels) == 10.0
        assert backend.get_gauge("pynext_db_connections_waiting", labels) == 2.0
    
    def test_record_connection_created(self):
        """Test recording connection creation."""
        collector = MetricsCollector()
        collector.record_connection_created("main")
        
        backend = collector.get_backend()
        assert backend.get_counter("pynext_db_connections_total", {"pool_name": "main"}) == 1.0
    
    def test_record_connection_closed(self):
        """Test recording connection closure."""
        collector = MetricsCollector()
        collector.record_connection_closed("main", "timeout")
        
        backend = collector.get_backend()
        labels = {"pool_name": "main", "reason": "timeout"}
        assert backend.get_counter("pynext_db_connections_closed", labels) == 1.0
    
    def test_record_pool_exhausted(self):
        """Test recording pool exhaustion."""
        collector = MetricsCollector()
        collector.record_pool_exhausted("main")
        
        backend = collector.get_backend()
        assert backend.get_counter("pynext_db_pool_exhausted_total", {"pool_name": "main"}) == 1.0
    
    def test_record_pool_wait_time(self):
        """Test recording pool wait time."""
        collector = MetricsCollector()
        collector.record_pool_wait_time("main", 0.5)
        
        backend = collector.get_backend()
        observations = backend.get_histogram("pynext_db_pool_wait_time_seconds", {"pool_name": "main"})
        assert observations == [0.5]
    
    def test_record_transaction(self):
        """Test recording transaction."""
        collector = MetricsCollector()
        collector.record_transaction("committed")
        
        backend = collector.get_backend()
        assert backend.get_counter("pynext_db_transactions_total", {"status": "committed"}) == 1.0
    
    def test_record_retry(self):
        """Test recording retry."""
        collector = MetricsCollector()
        collector.record_retry("SELECT")
        
        backend = collector.get_backend()
        assert backend.get_counter("pynext_db_retries_total", {"query_type": "SELECT"}) == 1.0
    
    def test_record_circuit_breaker_open(self):
        """Test recording circuit breaker state."""
        collector = MetricsCollector()
        collector.record_circuit_breaker_state("main", "open")
        
        backend = collector.get_backend()
        assert backend.get_gauge("pynext_db_circuit_breaker_state", {"breaker_name": "main"}) == 1.0
    
    def test_record_circuit_breaker_closed(self):
        """Test recording circuit breaker closed state."""
        collector = MetricsCollector()
        collector.record_circuit_breaker_state("main", "closed")
        
        backend = collector.get_backend()
        assert backend.get_gauge("pynext_db_circuit_breaker_state", {"breaker_name": "main"}) == 0.0
    
    def test_record_circuit_breaker_half_open(self):
        """Test recording circuit breaker half-open state."""
        collector = MetricsCollector()
        collector.record_circuit_breaker_state("main", "half_open")
        
        backend = collector.get_backend()
        assert backend.get_gauge("pynext_db_circuit_breaker_state", {"breaker_name": "main"}) == 0.5
    
    def test_record_cache_hit(self):
        """Test recording cache hit."""
        collector = MetricsCollector()
        collector.record_cache_hit("query")
        
        backend = collector.get_backend()
        assert backend.get_counter("pynext_db_cache_hits_total", {"cache_type": "query"}) == 1.0
    
    def test_record_cache_miss(self):
        """Test recording cache miss."""
        collector = MetricsCollector()
        collector.record_cache_miss("query")
        
        backend = collector.get_backend()
        assert backend.get_counter("pynext_db_cache_misses_total", {"cache_type": "query"}) == 1.0
    
    def test_counter_inc_custom(self):
        """Test custom counter increment."""
        collector = MetricsCollector()
        collector.counter_inc("custom_counter", 5.0, {"label": "value"})
        
        backend = collector.get_backend()
        assert backend.get_counter("pynext_db_custom_counter", {"label": "value"}) == 5.0
    
    def test_gauge_set_custom(self):
        """Test custom gauge set."""
        collector = MetricsCollector()
        collector.gauge_set("custom_gauge", 42.0, {"label": "value"})
        
        backend = collector.get_backend()
        assert backend.get_gauge("pynext_db_custom_gauge", {"label": "value"}) == 42.0
    
    def test_histogram_observe_custom(self):
        """Test custom histogram observe."""
        collector = MetricsCollector()
        collector.histogram_observe("custom_histogram", 0.5, {"label": "value"})
        
        backend = collector.get_backend()
        observations = backend.get_histogram("pynext_db_custom_histogram", {"label": "value"})
        assert observations == [0.5]
    
    def test_get_metrics(self):
        """Test getting all metrics."""
        collector = MetricsCollector()
        collector.record_query("SELECT", "users", 0.1)
        
        metrics = collector.get_metrics()
        assert "counters" in metrics
        assert "histograms" in metrics
    
    def test_reset(self):
        """Test resetting metrics."""
        collector = MetricsCollector()
        collector.record_query("SELECT", "users", 0.1)
        collector.reset()
        
        metrics = collector.get_metrics()
        assert metrics["counters"] == {}
    
    def test_get_backend(self):
        """Test getting backend."""
        collector = MetricsCollector()
        backend = collector.get_backend()
        assert isinstance(backend, MemoryBackend)
    
    def test_custom_backend(self):
        """Test using custom backend."""
        custom_backend = MemoryBackend()
        collector = MetricsCollector(backend=custom_backend)
        
        collector.counter_inc("test", 1.0)
        assert custom_backend.get_counter("pynext_db_test") == 1.0
    
    def test_merge_labels(self):
        """Test label merging with defaults."""
        config = MetricsConfig(labels={"service": "api"})
        collector = MetricsCollector(config)
        
        merged = collector._merge_labels({"table": "users"})
        assert merged["service"] == "api"
        assert merged["table"] == "users"
    
    def test_full_name(self):
        """Test full metric name generation."""
        collector = MetricsCollector()
        assert collector._full_name("test") == "pynext_db_test"
    
    def test_custom_prefix_in_metrics(self):
        """Test custom prefix is used in metric names."""
        config = MetricsConfig(prefix="myapp")
        collector = MetricsCollector(config)
        
        collector.counter_inc("test", 1.0)
        backend = collector.get_backend()
        assert backend.get_counter("myapp_test") == 1.0
    
    def test_pool_metrics_disabled(self):
        """Test pool metrics can be disabled."""
        config = MetricsConfig(collect_pool_metrics=False)
        collector = MetricsCollector(config)
        
        collector.record_pool_stats("main", active=5, idle=10, waiting=0)
        
        backend = collector.get_backend()
        assert backend.get_gauge("pynext_db_connections_active", {"pool_name": "main"}) == 0.0
    
    def test_query_metrics_disabled(self):
        """Test query metrics can be disabled."""
        config = MetricsConfig(collect_query_metrics=False)
        collector = MetricsCollector(config)
        
        collector.record_query("SELECT", "users", 0.1)
        
        backend = collector.get_backend()
        labels = {"query_type": "SELECT", "table": "users", "status": "success"}
        assert backend.get_counter("pynext_db_queries_total", labels) == 0.0
    
    def test_multiple_query_types(self):
        """Test recording multiple query types."""
        collector = MetricsCollector()
        
        collector.record_query("SELECT", "users", 0.1)
        collector.record_query("INSERT", "users", 0.2)
        collector.record_query("UPDATE", "users", 0.3)
        collector.record_query("DELETE", "users", 0.4)
        
        backend = collector.get_backend()
        assert backend.get_counter("pynext_db_queries_total", {"query_type": "SELECT", "table": "users", "status": "success"}) == 1.0
        assert backend.get_counter("pynext_db_queries_total", {"query_type": "INSERT", "table": "users", "status": "success"}) == 1.0
    
    def test_multiple_tables(self):
        """Test recording queries to multiple tables."""
        collector = MetricsCollector()
        
        collector.record_query("SELECT", "users", 0.1)
        collector.record_query("SELECT", "orders", 0.2)
        collector.record_query("SELECT", "products", 0.3)
        
        backend = collector.get_backend()
        assert backend.get_counter("pynext_db_queries_total", {"query_type": "SELECT", "table": "users", "status": "success"}) == 1.0
        assert backend.get_counter("pynext_db_queries_total", {"query_type": "SELECT", "table": "orders", "status": "success"}) == 1.0
    
    def test_transaction_rollback(self):
        """Test recording transaction rollback."""
        collector = MetricsCollector()
        collector.record_transaction("rolled_back")
        
        backend = collector.get_backend()
        assert backend.get_counter("pynext_db_transactions_total", {"status": "rolled_back"}) == 1.0


# ============================================================================
# Timer Tests (10 tests)
# ============================================================================

class TestTimer:
    """Tests for Timer context manager."""
    
    def test_sync_timing(self):
        """Test synchronous timing."""
        collector = MetricsCollector()
        
        with Timer(collector, "test_duration", {"op": "test"}):
            time.sleep(0.05)
        
        backend = collector.get_backend()
        observations = backend.get_histogram("pynext_db_test_duration", {"op": "test"})
        assert len(observations) == 1
        assert observations[0] >= 0.05
    
    @pytest.mark.asyncio
    async def test_async_timing(self):
        """Test asynchronous timing."""
        collector = MetricsCollector()
        
        async with Timer(collector, "test_duration", {"op": "test"}):
            await asyncio.sleep(0.05)
        
        backend = collector.get_backend()
        observations = backend.get_histogram("pynext_db_test_duration", {"op": "test"})
        assert len(observations) == 1
        assert observations[0] >= 0.05
    
    def test_elapsed_property(self):
        """Test elapsed time property."""
        collector = MetricsCollector()
        timer = Timer(collector, "test_duration")
        
        with timer:
            time.sleep(0.05)
            elapsed_during = timer.elapsed
        
        elapsed_after = timer.elapsed
        assert elapsed_during >= 0.05
        assert elapsed_after >= 0.05
    
    def test_elapsed_before_start(self):
        """Test elapsed time before start returns 0."""
        collector = MetricsCollector()
        timer = Timer(collector, "test_duration")
        assert timer.elapsed == 0.0
    
    def test_no_labels(self):
        """Test timer with no labels."""
        collector = MetricsCollector()
        
        with Timer(collector, "test_duration"):
            time.sleep(0.01)
        
        backend = collector.get_backend()
        observations = backend.get_histogram("pynext_db_test_duration")
        assert len(observations) == 1
    
    def test_exception_still_records(self):
        """Test timer records even on exception."""
        collector = MetricsCollector()
        
        try:
            with Timer(collector, "test_duration"):
                time.sleep(0.01)
                raise ValueError("Test error")
        except ValueError:
            pass
        
        backend = collector.get_backend()
        observations = backend.get_histogram("pynext_db_test_duration")
        assert len(observations) == 1
    
    def test_nested_timers(self):
        """Test nested timers."""
        collector = MetricsCollector()
        
        with Timer(collector, "outer", {"op": "outer"}):
            time.sleep(0.01)
            with Timer(collector, "inner", {"op": "inner"}):
                time.sleep(0.01)
        
        backend = collector.get_backend()
        outer = backend.get_histogram("pynext_db_outer", {"op": "outer"})
        inner = backend.get_histogram("pynext_db_inner", {"op": "inner"})
        
        assert len(outer) == 1
        assert len(inner) == 1
        assert outer[0] >= inner[0]
    
    def test_multiple_timings(self):
        """Test multiple timings of same metric."""
        collector = MetricsCollector()
        
        for _ in range(5):
            with Timer(collector, "test_duration"):
                time.sleep(0.01)
        
        backend = collector.get_backend()
        observations = backend.get_histogram("pynext_db_test_duration")
        assert len(observations) == 5
    
    @pytest.mark.asyncio
    async def test_async_exception(self):
        """Test async timer records on exception."""
        collector = MetricsCollector()
        
        try:
            async with Timer(collector, "test_duration"):
                await asyncio.sleep(0.01)
                raise ValueError("Test error")
        except ValueError:
            pass
        
        backend = collector.get_backend()
        observations = backend.get_histogram("pynext_db_test_duration")
        assert len(observations) == 1
    
    def test_timer_precision(self):
        """Test timer has good precision."""
        collector = MetricsCollector()
        
        with Timer(collector, "test_duration") as timer:
            time.sleep(0.001)  # 1ms
        
        # Should measure at least 1ms
        assert timer.elapsed >= 0.001


# ============================================================================
# create_collector Helper Tests (5 tests)
# ============================================================================

class TestCreateCollectorHelper:
    """Tests for create_collector convenience function."""
    
    def test_create_collector_defaults(self):
        """Test create_collector with defaults."""
        collector = create_collector()
        assert collector.config.backend == BackendType.MEMORY
        assert collector.config.prefix == DEFAULT_PREFIX
    
    def test_create_collector_with_backend(self):
        """Test create_collector with backend."""
        collector = create_collector(backend="memory")
        assert collector.config.backend == BackendType.MEMORY
    
    def test_create_collector_with_prefix(self):
        """Test create_collector with prefix."""
        collector = create_collector(prefix="custom_db")
        assert collector.config.prefix == "custom_db"
    
    def test_create_collector_with_kwargs(self):
        """Test create_collector with additional kwargs."""
        collector = create_collector(
            backend="memory",
            prefix="myapp",
            collect_pool_metrics=False,
        )
        assert collector.config.prefix == "myapp"
        assert collector.config.collect_pool_metrics is False
    
    def test_create_collector_backend_enum(self):
        """Test create_collector with BackendType enum."""
        collector = create_collector(backend=BackendType.MEMORY)
        assert collector.config.backend == BackendType.MEMORY


# ============================================================================
# Edge Cases and Performance Tests (5 tests)
# ============================================================================

class TestEdgeCasesAndPerformance:
    """Tests for edge cases and performance."""
    
    def test_empty_labels(self):
        """Test handling empty labels."""
        collector = MetricsCollector()
        collector.record_query("SELECT", "users", 0.1)
        collector.record_query("SELECT", "users", 0.2)
        
        backend = collector.get_backend()
        labels = {"query_type": "SELECT", "table": "users", "status": "success"}
        assert backend.get_counter("pynext_db_queries_total", labels) == 2.0
    
    def test_special_characters_in_labels(self):
        """Test special characters in label values."""
        collector = MetricsCollector()
        collector.record_query("SELECT", "user:accounts", 0.1)
        
        backend = collector.get_backend()
        labels = {"query_type": "SELECT", "table": "user:accounts", "status": "success"}
        assert backend.get_counter("pynext_db_queries_total", labels) == 1.0
    
    def test_very_large_counter(self):
        """Test very large counter values."""
        backend = MemoryBackend()
        for _ in range(100000):
            backend.counter_inc("large_counter")
        assert backend.get_counter("large_counter") == 100000.0
    
    def test_many_label_combinations(self):
        """Test many different label combinations."""
        collector = MetricsCollector()
        
        for i in range(100):
            collector.record_query("SELECT", f"table_{i}", 0.1)
        
        backend = collector.get_backend()
        for i in range(100):
            labels = {"query_type": "SELECT", "table": f"table_{i}", "status": "success"}
            assert backend.get_counter("pynext_db_queries_total", labels) == 1.0
    
    def test_high_frequency_updates(self):
        """Test high frequency metric updates."""
        collector = MetricsCollector()
        
        start = time.monotonic()
        for _ in range(10000):
            collector.record_query("SELECT", "users", 0.001)
        elapsed = time.monotonic() - start
        
        # Should complete in reasonable time
        assert elapsed < 2.0  # Less than 2 seconds for 10k updates
        
        backend = collector.get_backend()
        labels = {"query_type": "SELECT", "table": "users", "status": "success"}
        assert backend.get_counter("pynext_db_queries_total", labels) == 10000.0

