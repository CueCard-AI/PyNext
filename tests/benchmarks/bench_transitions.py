"""
Benchmarks for PyNext Transitions & Navigation.

Measures:
1. Link component rendering
2. Transition CSS generation
3. Navigation script generation
4. TransitionConfig creation

Run with:
    python -m pytest tests/benchmarks/bench_transitions.py -v --benchmark-only
"""

import pytest
import json
from pynext.core.transitions import (
    TransitionType,
    TransitionConfig,
    TransitionManager,
    PageTransition,
    transition,
    Link,
    navigate_script,
    back_script,
    forward_script,
    get_transition_css,
    get_transition_style_tag,
    generate_navigation_data,
    get_navigation_script,
)
from pynext.core.html import div, img


# =============================================================================
# Link Component Benchmarks
# =============================================================================

class TestLinkBenchmarks:
    """Benchmarks for Link component."""
    
    def test_simple_link(self, benchmark):
        """Render simple link."""
        def render():
            return Link(href="/about").render()
        
        result = benchmark(render)
        assert 'href="/about"' in result
    
    def test_link_with_transition(self, benchmark):
        """Render link with transition."""
        def render():
            return Link(
                href="/dashboard",
                transition=TransitionType.SLIDE_LEFT
            ).render()
        
        result = benchmark(render)
        assert "slide-left" in result
    
    def test_link_with_content(self, benchmark):
        """Render link with content."""
        def render():
            return Link(href="/home")["Go Home"].render()
        
        result = benchmark(render)
        assert "Go Home" in result
    
    def test_many_links(self, benchmark):
        """Render many links."""
        def render():
            return [
                Link(href=f"/page-{i}", transition=TransitionType.FADE).render()
                for i in range(20)
            ]
        
        result = benchmark(render)
        assert len(result) == 20


# =============================================================================
# CSS Generation Benchmarks
# =============================================================================

class TestCSSBenchmarks:
    """Benchmarks for CSS generation."""
    
    def test_get_transition_css(self, benchmark):
        """Generate transition CSS."""
        result = benchmark(get_transition_css)
        
        assert "@view-transition" in result
    
    def test_get_style_tag(self, benchmark):
        """Generate style tag."""
        result = benchmark(get_transition_style_tag)
        
        assert "<style>" in result


# =============================================================================
# Navigation Script Benchmarks
# =============================================================================

class TestScriptBenchmarks:
    """Benchmarks for script generation."""
    
    def test_navigate_script(self, benchmark):
        """Generate navigate script."""
        def generate():
            return navigate_script("/dashboard", transition=TransitionType.FADE)
        
        result = benchmark(generate)
        assert "__pynext__.navigate" in result
    
    def test_back_script(self, benchmark):
        """Generate back script."""
        result = benchmark(back_script)
        
        assert "__pynext__.back" in result
    
    def test_forward_script(self, benchmark):
        """Generate forward script."""
        result = benchmark(forward_script)
        
        assert "__pynext__.forward" in result
    
    def test_navigation_data(self, benchmark):
        """Generate navigation data."""
        routes = [f"/page-{i}" for i in range(50)]
        
        def generate():
            return generate_navigation_data(
                routes=routes,
                current_route="/page-25",
                prefetch_routes=["/page-26", "/page-27"]
            )
        
        result = benchmark(generate)
        assert "/page-25" in result
    
    def test_navigation_script(self, benchmark):
        """Generate navigation script tag."""
        routes = [f"/page-{i}" for i in range(20)]
        
        def generate():
            return get_navigation_script(
                routes=routes,
                current_route="/page-0"
            )
        
        result = benchmark(generate)
        assert "__PYNEXT_NAV__" in result


# =============================================================================
# TransitionConfig Benchmarks
# =============================================================================

class TestConfigBenchmarks:
    """Benchmarks for TransitionConfig."""
    
    def test_default_config(self, benchmark):
        """Create default config."""
        def create():
            return TransitionConfig()
        
        result = benchmark(create)
        assert result.type == TransitionType.FADE
    
    def test_custom_config(self, benchmark):
        """Create custom config."""
        def create():
            return TransitionConfig(
                type=TransitionType.SLIDE_LEFT,
                duration=500,
                easing="ease-out",
                delay=100
            )
        
        result = benchmark(create)
        assert result.duration == 500
    
    def test_many_configs(self, benchmark):
        """Create many configs."""
        def create():
            return [
                TransitionConfig(
                    type=TransitionType.FADE,
                    duration=i * 100
                )
                for i in range(20)
            ]
        
        result = benchmark(create)
        assert len(result) == 20


# =============================================================================
# TransitionManager Benchmarks
# =============================================================================

class TestManagerBenchmarks:
    """Benchmarks for TransitionManager."""
    
    def test_manager_creation(self, benchmark):
        """Create transition manager."""
        def create():
            return TransitionManager()
        
        result = benchmark(create)
        assert result is not None
    
    def test_register_transition(self, benchmark):
        """Register transitions."""
        manager = TransitionManager()
        
        def register():
            for i in range(10):
                manager.register_transition(
                    f"trans-{i}",
                    TransitionConfig(duration=i * 100)
                )
        
        benchmark(register)
        assert len(manager._custom_transitions) >= 10
    
    def test_get_transition(self, benchmark):
        """Get transition config."""
        manager = TransitionManager()
        manager.register_transition("my-trans", TransitionConfig(duration=500))
        
        def get():
            return manager.get_transition("my-trans")
        
        result = benchmark(get)
        assert result.duration == 500


# =============================================================================
# PageTransition Benchmarks
# =============================================================================

class TestPageTransitionBenchmarks:
    """Benchmarks for PageTransition wrapper."""
    
    def test_page_transition_render(self, benchmark):
        """Render page transition."""
        content = div()["Page content here"]
        
        def render():
            page = PageTransition(content=content, name="main")
            return page.render()
        
        result = benchmark(render)
        assert "Page content" in result
    
    def test_page_transition_complex(self, benchmark):
        """Render complex page transition."""
        content = div()[
            div()["Header"],
            div()["Main content " * 50],
            div()["Footer"],
        ]
        
        def render():
            page = PageTransition(content=content, name="complex-page")
            return page.render()
        
        result = benchmark(render)
        assert "Header" in result


# =============================================================================
# Transition Decorator Benchmarks
# =============================================================================

class TestDecoratorBenchmarks:
    """Benchmarks for @transition decorator."""
    
    def test_apply_decorator(self, benchmark):
        """Apply transition decorator."""
        def apply():
            @transition("test-trans")
            def Component():
                return div()["Content"]
            return Component
        
        result = benchmark(apply)
        assert result._transition_name == "test-trans"
    
    def test_call_decorated(self, benchmark):
        """Call decorated component."""
        @transition("my-component")
        def MyComponent():
            return div()["Decorated content"]
        
        def call():
            return MyComponent()
        
        result = benchmark(call)


# =============================================================================
# Summary Stats
# =============================================================================

def test_print_transitions_summary():
    """Print transitions performance summary."""
    import time
    
    print("\n" + "=" * 70)
    print("TRANSITIONS & NAVIGATION PERFORMANCE SUMMARY")
    print("=" * 70)
    
    # Link rendering
    start = time.perf_counter()
    for _ in range(1000):
        Link(href="/page", transition=TransitionType.FADE).render()
    link_time = (time.perf_counter() - start) * 1000
    
    print(f"\n1000 Link renders: {link_time:.2f}ms ({link_time/1000*1000:.2f}μs/render)")
    
    # CSS generation
    start = time.perf_counter()
    for _ in range(100):
        get_transition_css()
    css_time = (time.perf_counter() - start) * 1000
    
    print(f"100 CSS generations: {css_time:.2f}ms")
    
    # Navigate script
    start = time.perf_counter()
    for _ in range(1000):
        navigate_script("/dashboard", transition=TransitionType.SLIDE_LEFT)
    script_time = (time.perf_counter() - start) * 1000
    
    print(f"1000 navigate scripts: {script_time:.2f}ms")
    
    # Navigation data
    routes = [f"/page-{i}" for i in range(100)]
    
    start = time.perf_counter()
    for _ in range(100):
        generate_navigation_data(routes, "/page-50", ["/page-51"])
    data_time = (time.perf_counter() - start) * 1000
    
    print(f"100 navigation data (100 routes): {data_time:.2f}ms")
    
    # Size analysis
    css = get_transition_css()
    style_tag = get_transition_style_tag()
    
    print(f"\nTransition CSS size: {len(css)} bytes")
    print(f"Style tag size: {len(style_tag)} bytes")
    
    print("\nTransition Types:")
    for t in TransitionType:
        print(f"  - {t.value}")
    
    print("\n" + "=" * 70)

