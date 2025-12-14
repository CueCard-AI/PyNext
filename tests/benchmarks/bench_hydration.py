"""
Benchmark tests for PyNext hydration performance.

Tracks hydration payload size and serialization speed.
"""

import pytest
import json
from pynext.reactive import Signal, Computed, Store
from pynext.core.component import page, component
from pynext.core.html import div, span, button, ul, li
from pynext.core.context import render_context


@pytest.mark.benchmark
class TestHydrationPayloadSize:
    """Benchmarks for hydration payload size."""
    
    def test_single_signal_payload(self):
        """Measure payload size for single signal."""
        signal = Signal(42, name="count")
        js_init = signal.get_js_init()
        
        # Should be reasonably small
        assert len(js_init) < 100
    
    def test_many_signals_payload(self):
        """Measure payload size for many signals."""
        signals = [Signal(i, name=f"signal_{i}") for i in range(100)]
        
        total_size = sum(len(s.get_js_init()) for s in signals)
        
        # 100 signals should be under 10KB
        assert total_size < 10000
    
    def test_store_payload(self):
        """Measure payload size for store."""
        store = Store({
            "user": {
                "name": "Alice",
                "email": "alice@example.com",
                "settings": {
                    "theme": "dark",
                    "notifications": True,
                    "language": "en"
                }
            },
            "items": [
                {"id": 1, "name": "Item 1"},
                {"id": 2, "name": "Item 2"},
                {"id": 3, "name": "Item 3"},
            ]
        }, name="app_state")
        
        js_init = store.get_js_init()
        
        # Complex store should still be reasonable
        assert len(js_init) < 1000
    
    def test_large_list_payload(self):
        """Measure payload size for large list in signal."""
        large_list = [{"id": i, "value": f"item_{i}"} for i in range(1000)]
        signal = Signal(large_list, name="items")
        
        js_init = signal.get_js_init()
        
        # 1000 items should be under 100KB
        assert len(js_init) < 100000


@pytest.mark.benchmark
class TestSerializationSpeed:
    """Benchmarks for serialization speed."""
    
    def test_signal_serialization(self, benchmark):
        """Benchmark signal serialization speed."""
        signal = Signal({"key": "value", "count": 42}, name="data")
        
        result = benchmark(signal.get_js_init)
        
        assert "__pynext__" in result
    
    def test_store_serialization(self, benchmark):
        """Benchmark store serialization speed."""
        store = Store({
            "users": [{"id": i, "name": f"User {i}"} for i in range(100)],
            "settings": {"theme": "dark", "lang": "en"},
        }, name="store")
        
        result = benchmark(store.get_js_init)
        
        assert "__pynext__" in result
    
    def test_many_signals_serialization(self, benchmark):
        """Benchmark serializing many signals."""
        signals = [Signal(i, name=f"sig_{i}") for i in range(100)]
        
        def serialize_all():
            return [s.get_js_init() for s in signals]
        
        result = benchmark(serialize_all)
        
        assert len(result) == 100
    
    def test_computed_serialization(self, benchmark):
        """Benchmark computed serialization."""
        count = Signal(5, name="count")
        doubled = Computed(lambda: count() * 2, name="doubled")
        
        result = benchmark(doubled.get_js_init)
        
        assert "__pynext__" in result


@pytest.mark.benchmark
class TestHydrationDataGeneration:
    """Benchmarks for full hydration data generation."""
    
    def test_simple_page_hydration(self, benchmark):
        """Benchmark hydration data for simple page."""
        @page(title="Simple")
        def simple_page():
            count = Signal(0)
            return div()[
                span()[count],
                button()["Click"]
            ]
        
        def generate():
            return simple_page.render_full_page()
        
        html = benchmark(generate)
        
        assert "__PYNEXT_HYDRATION__" in html
    
    def test_complex_page_hydration(self, benchmark):
        """Benchmark hydration data for complex page."""
        @page(title="Complex")
        def complex_page():
            items = Signal([f"Item {i}" for i in range(50)])
            selected = Signal(None)
            filter_text = Signal("")
            
            return div()[
                span()[f"Total: {len(items())}"],
                span()[f"Selected: {selected()}"],
                ul()[
                    [li()[item] for item in items()]
                ]
            ]
        
        def generate():
            return complex_page.render_full_page()
        
        html = benchmark(generate)
        
        assert "__PYNEXT_HYDRATION__" in html
    
    def test_nested_components_hydration(self, benchmark):
        """Benchmark hydration with nested components."""
        @component
        def Card(title: str, content: str):
            expanded = Signal(False)
            return div(class_="card")[
                div(class_="title")[title],
                expanded() and div(class_="content")[content],
                button(onclick=lambda: expanded.update(lambda x: not x))["Toggle"]
            ]
        
        @page(title="Cards")
        def cards_page():
            return div()[
                [Card(title=f"Card {i}", content=f"Content {i}") for i in range(10)]
            ]
        
        def generate():
            return cards_page.render_full_page()
        
        html = benchmark(generate)
        
        assert "__PYNEXT_HYDRATION__" in html


@pytest.mark.benchmark
class TestJSONPerformance:
    """Benchmarks for JSON operations in hydration."""
    
    def test_json_dumps_speed(self, benchmark):
        """Benchmark json.dumps for hydration data."""
        data = {
            "signals": {
                f"sig_{i}": {"value": i, "id": f"sig_{i}"}
                for i in range(100)
            },
            "stores": {
                "app": {
                    "users": [{"id": i, "name": f"User {i}"} for i in range(50)],
                    "settings": {"theme": "dark"}
                }
            },
            "events": {
                f"btn_{i}": {"click": f"handleClick_{i}()"}
                for i in range(20)
            }
        }
        
        result = benchmark(json.dumps, data)
        
        assert len(result) > 0
    
    def test_orjson_speed(self, benchmark):
        """Benchmark orjson for hydration data."""
        import orjson
        
        data = {
            "signals": {
                f"sig_{i}": {"value": i, "id": f"sig_{i}"}
                for i in range(100)
            },
            "stores": {
                "app": {
                    "users": [{"id": i, "name": f"User {i}"} for i in range(50)],
                }
            }
        }
        
        result = benchmark(orjson.dumps, data)
        
        assert len(result) > 0


@pytest.mark.benchmark
class TestHydrationScaling:
    """Benchmarks for hydration scaling behavior."""
    
    def test_linear_scaling(self, benchmark):
        """Verify hydration scales linearly with signal count."""
        counts = [10, 50, 100, 200]
        times = []
        
        for count in counts:
            signals = [Signal(i, name=f"sig_{i}") for i in range(count)]
            
            import time
            start = time.perf_counter()
            for s in signals:
                s.get_js_init()
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        
        # Check roughly linear scaling (2x signals ≈ 2x time)
        # Allow for significant variation due to system load
        ratio_50_to_10 = times[1] / times[0]
        ratio_100_to_50 = times[2] / times[1]
        
        # Should be roughly 5x and 2x respectively
        # Use generous bounds to avoid flaky failures on loaded systems
        assert ratio_50_to_10 < 15  # Not exponential
        assert ratio_100_to_50 < 8  # Not exponential

