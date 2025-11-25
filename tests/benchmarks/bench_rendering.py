"""
Benchmark tests for PyNext rendering performance.

Tracks HTML generation speed and memory usage.
"""

import pytest
from pynext.core.html import div, span, h1, p, ul, li, a, button
from pynext.core.signals import Signal
from pynext.core.component import component, page


@pytest.mark.benchmark
class TestElementRenderingBenchmarks:
    """Benchmarks for HTML element rendering."""
    
    def test_simple_element(self, benchmark):
        """Benchmark rendering a simple element."""
        el = div()["Hello World"]
        
        result = benchmark(el.render)
        
        assert "<div>" in result
    
    def test_element_with_attributes(self, benchmark):
        """Benchmark rendering element with many attributes."""
        el = div(
            id="main",
            class_="container mx-auto p-4",
            data_testid="test",
            data_value="123",
            role="main",
            tabindex=0,
        )["Content"]
        
        result = benchmark(el.render)
        
        assert "id=" in result
    
    def test_nested_elements(self, benchmark):
        """Benchmark rendering nested elements."""
        el = div()[
            h1()["Title"],
            div(class_="content")[
                p()["Paragraph 1"],
                p()["Paragraph 2"],
                p()["Paragraph 3"],
            ],
            div(class_="sidebar")[
                ul()[
                    li()["Item 1"],
                    li()["Item 2"],
                    li()["Item 3"],
                ]
            ]
        ]
        
        result = benchmark(el.render)
        
        assert "<div>" in result
    
    def test_large_list(self, benchmark):
        """Benchmark rendering a large list."""
        items = [f"Item {i}" for i in range(100)]
        el = ul()[
            [li()[item] for item in items]
        ]
        
        result = benchmark(el.render)
        
        assert "Item 0" in result
        assert "Item 99" in result
    
    def test_deep_nesting(self, benchmark):
        """Benchmark deeply nested elements."""
        def create_nested(depth):
            if depth == 0:
                return span()["Leaf"]
            return div()[create_nested(depth - 1)]
        
        el = create_nested(20)  # 20 levels deep
        
        result = benchmark(el.render)
        
        assert "Leaf" in result


@pytest.mark.benchmark
class TestComponentRenderingBenchmarks:
    """Benchmarks for component rendering."""
    
    def test_simple_component(self, benchmark):
        """Benchmark rendering a simple component."""
        @component
        def Simple():
            return div()["Simple component"]
        
        result = benchmark(Simple.render_to_string)
        
        assert "Simple component" in result
    
    def test_component_with_props(self, benchmark):
        """Benchmark component with props."""
        @component
        def Card(title: str, content: str):
            return div(class_="card")[
                h1()[title],
                p()[content],
            ]
        
        def render():
            return Card.render_to_string(title="Test", content="Content")
        
        result = benchmark(render)
        
        assert "Test" in result
    
    def test_component_with_signal(self, benchmark):
        """Benchmark component with signals."""
        @component
        def Counter():
            count = Signal(0)
            return div()[
                span()[count],
                button()["Increment"],
            ]
        
        result = benchmark(Counter.render_to_string)
        
        assert "<div>" in result
    
    def test_page_full_render(self, benchmark):
        """Benchmark full page rendering."""
        @page(title="Benchmark Page")
        def benchmark_page():
            return div()[
                h1()["Title"],
                p()["Content"],
            ]
        
        result = benchmark(benchmark_page.render_full_page)
        
        assert "<!DOCTYPE html>" in result


@pytest.mark.benchmark
class TestHydrationDataBenchmarks:
    """Benchmarks for hydration data generation."""
    
    def test_signal_hydration_data(self, benchmark):
        """Benchmark signal JS initialization."""
        sig = Signal(42, name="test")
        
        result = benchmark(sig.get_js_init)
        
        assert "__pynext__" in result
    
    def test_multiple_signals(self, benchmark):
        """Benchmark multiple signals initialization."""
        signals = [Signal(i, name=f"sig_{i}") for i in range(50)]
        
        def generate_all():
            return [s.get_js_init() for s in signals]
        
        result = benchmark(generate_all)
        
        assert len(result) == 50

