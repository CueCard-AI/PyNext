"""
Benchmark tests for PyNext Suspense and Streaming.

Tracks render performance and overhead.
"""

import pytest
import asyncio
from pynext.core.suspense import (
    Suspense,
    Show,
    Switch,
    Match,
    ErrorBoundary,
    SuspenseBoundary,
)
from pynext.core.resource import Resource
from pynext.core.html import div, span, h1, p, ul, li
from pynext.server.streaming import (
    PageShell,
    create_loading_skeleton,
    create_suspense_placeholder,
    get_streaming_css,
)


@pytest.mark.benchmark
class TestShowBenchmarks:
    """Benchmarks for Show component."""
    
    def test_show_true(self, benchmark):
        """Benchmark Show with true condition."""
        def render():
            show = Show(when=True)[div()["Content"]]
            return show.render()
        
        result = benchmark(render)
        assert "Content" in result
    
    def test_show_false(self, benchmark):
        """Benchmark Show with false condition."""
        def render():
            show = Show(when=False, fallback=span()["Fallback"])[
                div()["Content"]
            ]
            return show.render()
        
        result = benchmark(render)
        assert "Fallback" in result
    
    def test_show_callable_condition(self, benchmark):
        """Benchmark Show with callable condition."""
        value = True
        
        def render():
            show = Show(when=lambda: value)[div()["Dynamic"]]
            return show.render()
        
        result = benchmark(render)
        assert "Dynamic" in result


@pytest.mark.benchmark
class TestSwitchBenchmarks:
    """Benchmarks for Switch/Match components."""
    
    def test_switch_first_match(self, benchmark):
        """Benchmark Switch matching first case."""
        def render():
            switch = Switch()[
                Match(when=True)[div()["First"]],
                Match(when=True)[div()["Second"]],
                Match()[div()["Default"]],
            ]
            return switch.render()
        
        result = benchmark(render)
        assert "First" in result
    
    def test_switch_last_match(self, benchmark):
        """Benchmark Switch matching last case (worst case)."""
        def render():
            switch = Switch()[
                Match(when=False)[div()["First"]],
                Match(when=False)[div()["Second"]],
                Match(when=False)[div()["Third"]],
                Match()[div()["Default"]],
            ]
            return switch.render()
        
        result = benchmark(render)
        assert "Default" in result
    
    def test_switch_many_cases(self, benchmark):
        """Benchmark Switch with many cases."""
        status = "case_5"
        
        def render():
            switch = Switch()[
                Match(when=lambda: status == "case_1")[span()["1"]],
                Match(when=lambda: status == "case_2")[span()["2"]],
                Match(when=lambda: status == "case_3")[span()["3"]],
                Match(when=lambda: status == "case_4")[span()["4"]],
                Match(when=lambda: status == "case_5")[span()["5"]],
                Match(when=lambda: status == "case_6")[span()["6"]],
                Match()[span()["Default"]],
            ]
            return switch.render()
        
        result = benchmark(render)
        assert "5" in result


@pytest.mark.benchmark
class TestErrorBoundaryBenchmarks:
    """Benchmarks for ErrorBoundary."""
    
    def test_no_error(self, benchmark):
        """Benchmark ErrorBoundary with no error."""
        def render():
            boundary = ErrorBoundary(fallback=lambda e: div()["Error"])[
                div()[h1()["Title"], p()["Content"]]
            ]
            return boundary.render()
        
        result = benchmark(render)
        assert "Title" in result
    
    def test_with_error(self, benchmark):
        """Benchmark ErrorBoundary catching error."""
        def failing():
            raise ValueError("Test error")
        
        def render():
            boundary = ErrorBoundary(fallback=lambda e: div()[str(e)])[
                failing
            ]
            return boundary.render()
        
        result = benchmark(render)
        assert "Test error" in result
    
    def test_nested_boundaries(self, benchmark):
        """Benchmark nested ErrorBoundaries."""
        def render():
            inner = ErrorBoundary(fallback=lambda e: div()["Inner error"])[
                div()["Safe content"]
            ]
            outer = ErrorBoundary(fallback=lambda e: div()["Outer error"])[
                inner  # Pass the component itself, not nested in div
            ]
            return outer.render()
        
        result = benchmark(render)
        assert "Safe content" in result


@pytest.mark.benchmark
class TestSuspenseBenchmarks:
    """Benchmarks for Suspense component."""
    
    def test_suspense_sync_render(self, benchmark):
        """Benchmark Suspense synchronous render."""
        def render():
            suspense = Suspense(fallback=span()["Loading"])[
                div()["Content"]
            ]
            return suspense.render()
        
        result = benchmark(render)
        assert "Content" in result
    
    def test_suspense_with_fallback(self, benchmark):
        """Benchmark Suspense fallback rendering."""
        def render():
            suspense = Suspense(fallback=div()[
                span(class_="spinner")[""],
                span()["Loading..."],
            ])[
                div()["Content"]
            ]
            return suspense.render()
        
        result = benchmark(render)
        assert "Content" in result
    
    def test_suspense_nested(self, benchmark):
        """Benchmark nested Suspense boundaries."""
        def render():
            outer = Suspense(fallback=div()["Outer loading"])[
                div()["Outer"],
                Suspense(fallback=span()["Inner loading"])[
                    span()["Inner"]
                ]
            ]
            return outer.render()
        
        result = benchmark(render)
        assert "Outer" in result


@pytest.mark.benchmark
class TestSuspenseBoundaryBenchmarks:
    """Benchmarks for SuspenseBoundary operations."""
    
    def test_create_boundary(self, benchmark):
        """Benchmark SuspenseBoundary creation."""
        def create():
            return SuspenseBoundary(
                id="test-boundary",
                fallback=div()["Loading"],
            )
        
        result = benchmark(create)
        assert result.id == "test-boundary"
    
    def test_register_pending(self, benchmark):
        """Benchmark registering pending resources."""
        boundary = SuspenseBoundary(id="test", fallback=None)
        
        async def fetch():
            return "data"
        
        resource = Resource(fetch)
        
        def register():
            return boundary.register_pending(resource)
        
        result = benchmark(register)
        assert result.startswith("suspense-")


@pytest.mark.benchmark
class TestStreamingBenchmarks:
    """Benchmarks for streaming helpers."""
    
    def test_shell_opening(self, benchmark):
        """Benchmark PageShell opening render."""
        shell = PageShell(title="Test App")
        
        result = benchmark(shell.render_opening)
        assert "<!DOCTYPE html>" in result
    
    def test_shell_closing(self, benchmark):
        """Benchmark PageShell closing render."""
        shell = PageShell()
        
        result = benchmark(shell.render_closing)
        assert "</html>" in result
    
    def test_skeleton_single(self, benchmark):
        """Benchmark single skeleton creation."""
        result = benchmark(create_loading_skeleton)
        assert "skeleton" in result
    
    def test_skeleton_multiple(self, benchmark):
        """Benchmark multiple skeletons."""
        def create():
            return create_loading_skeleton(count=10)
        
        result = benchmark(create)
        assert result.count("skeleton") == 10
    
    def test_suspense_placeholder(self, benchmark):
        """Benchmark Suspense placeholder creation."""
        def create():
            return create_suspense_placeholder(
                "test-id",
                "<div>Loading...</div>",
            )
        
        result = benchmark(create)
        assert 'data-suspense="test-id"' in result


@pytest.mark.benchmark
class TestCombinedBenchmarks:
    """Benchmarks for combined operations."""
    
    def test_full_page_shell(self, benchmark):
        """Benchmark full page shell generation."""
        def render():
            shell = PageShell(title="My App")
            shell.add_state("user", {"name": "Alice"})
            
            opening = shell.render_opening()
            content = div()[
                h1()["Welcome"],
                create_loading_skeleton(count=5),
            ].render()
            closing = shell.render_closing()
            
            return opening + content + closing
        
        result = benchmark(render)
        assert "<!DOCTYPE html>" in result
        assert "Welcome" in result
    
    def test_complex_page(self, benchmark):
        """Benchmark complex page with multiple components."""
        def render():
            status = "loading"
            
            # Render components individually and combine
            header = Show(when=True)[h1()["Header"]].render()
            
            switch = Switch()[
                Match(when=lambda: status == "loading")[
                    span()[create_loading_skeleton(count=3)]
                ],
                Match(when=lambda: status == "ready")[
                    div()["Content"]
                ],
            ].render()
            
            items = ErrorBoundary(fallback=lambda e: div()["Error"])[
                ul()[[li()[f"Item {i}"] for i in range(10)]]
            ].render()
            
            return f"<div>{header}{switch}{items}</div>"
        
        result = benchmark(render)
        assert "Header" in result

