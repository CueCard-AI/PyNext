"""
Benchmarks for PyNext Islands Architecture.

Measures:
1. Island rendering performance
2. Bundle size analysis
3. Hydration data generation
4. Strategy overhead comparison
5. Static vs island comparison

Run with:
    python -m pytest tests/benchmarks/bench_islands.py -v --benchmark-only
"""

import pytest
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pynext.core.island import (
    island,
    static,
    HydrationStrategy,
    IslandBoundary,
    IslandMetadata,
    InteractivityType,
    is_interactive,
    collect_islands,
    get_island_hydration_data,
    generate_island_script,
    get_island_bundle_requirements,
    get_minimal_runtime_for_island,
    ComponentAnalyzer,
)
from pynext.reactive import Signal
from pynext.core.html import div, button, span, p, h1, section, article


# =============================================================================
# Test Components
# =============================================================================

@island
def SimpleIsland():
    """Minimal island with signal."""
    count = Signal(0)
    return button(onclick=lambda: count.set(count() + 1))[count]


@island(strategy=HydrationStrategy.VISIBLE)
def LazyIsland():
    """Island with visible strategy."""
    return div()["Lazy loaded content"]


@island(strategy=HydrationStrategy.IDLE)
def IdleIsland():
    """Island with idle strategy."""
    return span()["Idle content"]


@island(strategy=HydrationStrategy.MEDIA, media="(min-width: 768px)")
def MediaIsland():
    """Island with media query."""
    return div()["Desktop content"]


@island(strategy=HydrationStrategy.NONE)
def SSROnlyIsland():
    """Island that never hydrates."""
    return p()["Server only"]


@static
def StaticComponent():
    """Explicitly static component."""
    return div()["Static content"]


def create_complex_island():
    """Create a complex island with multiple signals."""
    @island
    def ComplexIsland():
        count = Signal(0)
        name = Signal("World")
        items = Signal([1, 2, 3, 4, 5])
        
        return div()[
            h1()[f"Hello, {name}!"],
            button(onclick=lambda: count.set(count() + 1))[count],
            div()[[span()[str(i)] for i in items()]],
        ]
    
    return ComplexIsland


# =============================================================================
# Rendering Benchmarks
# =============================================================================

class TestIslandRenderingBenchmarks:
    """Benchmarks for island rendering performance."""
    
    def test_simple_island_render(self, benchmark):
        """Benchmark simple island rendering."""
        @island
        def Counter():
            return button()["Click me"]
        
        def render():
            result = Counter()
            return result.render()
        
        html = benchmark(render)
        assert "data-island" in html
    
    def test_island_with_signal_render(self, benchmark):
        """Benchmark island with signal rendering."""
        def render():
            result = SimpleIsland()
            return result.render()
        
        html = benchmark(render)
        assert "data-island" in html
    
    def test_complex_island_render(self, benchmark):
        """Benchmark complex island rendering."""
        ComplexIsland = create_complex_island()
        
        def render():
            result = ComplexIsland()
            return result.render()
        
        html = benchmark(render)
        assert "data-island" in html
    
    def test_multiple_islands_render(self, benchmark):
        """Benchmark rendering multiple islands."""
        @island
        def Widget(n):
            return div()[f"Widget {n}"]
        
        def render():
            islands = [Widget(n=i) for i in range(10)]
            return [island.render() for island in islands]
        
        results = benchmark(render)
        assert len(results) == 10
    
    def test_static_component_render(self, benchmark):
        """Benchmark static component (baseline)."""
        def render():
            return StaticComponent()
        
        result = benchmark(render)
        # Static components don't return IslandBoundary
        assert result is not None


class TestIslandOverheadBenchmarks:
    """Measure overhead of island vs static."""
    
    def test_static_div_baseline(self, benchmark):
        """Baseline: plain div rendering."""
        def render():
            return div()["Content"].render()
        
        html = benchmark(render)
        assert "<div>" in html
    
    def test_island_div_overhead(self, benchmark):
        """Island wrapper overhead."""
        @island
        def IslandDiv():
            return div()["Content"]
        
        def render():
            return IslandDiv().render()
        
        html = benchmark(render)
        assert "data-island" in html
    
    def test_strategy_visible_overhead(self, benchmark):
        """Visible strategy overhead."""
        @island(strategy=HydrationStrategy.VISIBLE)
        def VisibleDiv():
            return div()["Content"]
        
        def render():
            return VisibleDiv().render()
        
        html = benchmark(render)
        assert 'data-hydrate="visible"' in html
    
    def test_strategy_media_overhead(self, benchmark):
        """Media query strategy overhead."""
        @island(strategy=HydrationStrategy.MEDIA, media="(min-width: 768px)")
        def MediaDiv():
            return div()["Content"]
        
        def render():
            return MediaDiv().render()
        
        html = benchmark(render)
        assert 'data-hydrate="media"' in html


# =============================================================================
# Hydration Script Benchmarks
# =============================================================================

class TestHydrationScriptBenchmarks:
    """Benchmarks for hydration script generation."""
    
    def test_single_island_script(self, benchmark):
        """Generate script for single island."""
        result = SimpleIsland()
        
        def generate():
            return result.get_hydration_script()
        
        script = benchmark(generate)
        assert "__pynext__.registerIsland" in script
    
    def test_multiple_islands_script(self, benchmark):
        """Generate script for multiple islands."""
        islands = [SimpleIsland() for _ in range(10)]
        
        def generate():
            return generate_island_script(islands)
        
        script = benchmark(generate)
        assert "hydrateIslands" in script
    
    def test_hydration_data_generation(self, benchmark):
        """Generate hydration data JSON."""
        islands = [SimpleIsland() for _ in range(10)]
        
        def generate():
            data = get_island_hydration_data(islands)
            return json.dumps(data)
        
        json_data = benchmark(generate)
        assert "islands" in json_data


# =============================================================================
# Bundle Analysis Benchmarks
# =============================================================================

class TestBundleAnalysisBenchmarks:
    """Benchmarks for bundle requirement analysis."""
    
    def test_analyze_single_island(self, benchmark):
        """Analyze bundle requirements for single island."""
        result = SimpleIsland()
        result.metadata.interactivity = {InteractivityType.SIGNAL, InteractivityType.EVENT}
        
        def analyze():
            return get_island_bundle_requirements([result])
        
        reqs = benchmark(analyze)
        assert result.id in reqs
    
    def test_analyze_multiple_islands(self, benchmark):
        """Analyze bundle requirements for multiple islands."""
        islands = []
        for _ in range(20):
            island_result = SimpleIsland()
            island_result.metadata.interactivity = {InteractivityType.SIGNAL}
            islands.append(island_result)
        
        def analyze():
            return get_island_bundle_requirements(islands)
        
        reqs = benchmark(analyze)
        assert len(reqs) == 20
    
    def test_minimal_runtime_selection(self, benchmark):
        """Select minimal runtime modules."""
        result = SimpleIsland()
        result.metadata.interactivity = {InteractivityType.SIGNAL, InteractivityType.EVENT}
        
        def select():
            return get_minimal_runtime_for_island(result)
        
        modules = benchmark(select)
        assert "core" in modules


# =============================================================================
# Component Analyzer Benchmarks
# =============================================================================

class TestComponentAnalyzerBenchmarks:
    """Benchmarks for component analysis."""
    
    def test_analyze_static_component(self, benchmark):
        """Analyze static component."""
        analyzer = ComponentAnalyzer()
        component = div()["Static"]
        
        def analyze():
            return analyzer.analyze(component)
        
        result = benchmark(analyze)
        assert result["is_interactive"] is False
    
    def test_analyze_island_component(self, benchmark):
        """Analyze island component."""
        analyzer = ComponentAnalyzer()
        result = SimpleIsland()
        
        def analyze():
            return analyzer.analyze(result)
        
        analysis = benchmark(analyze)
        assert analysis["is_island"] is True
    
    def test_analyze_large_tree(self, benchmark):
        """Analyze large component tree."""
        analyzer = ComponentAnalyzer()
        
        # Create a tree with 100 components
        components = [div()[f"Component {i}"] for i in range(100)]
        tree = div()[components]
        
        def analyze():
            return analyzer.analyze(tree)
        
        result = benchmark(analyze)
        assert result is not None


# =============================================================================
# Collection Benchmarks
# =============================================================================

class TestCollectionBenchmarks:
    """Benchmarks for island collection."""
    
    def test_collect_single_island(self, benchmark):
        """Collect single island from tree."""
        result = SimpleIsland()
        
        def collect():
            return collect_islands(result)
        
        islands = benchmark(collect)
        assert len(islands) == 1
    
    def test_collect_nested_islands(self, benchmark):
        """Collect islands from nested structure."""
        islands_list = [SimpleIsland() for _ in range(10)]
        
        def collect():
            return collect_islands(islands_list)
        
        islands = benchmark(collect)
        assert len(islands) == 10
    
    def test_is_interactive_check(self, benchmark):
        """Check if component is interactive."""
        result = SimpleIsland()
        
        def check():
            return is_interactive(result)
        
        interactive = benchmark(check)
        assert interactive is True


# =============================================================================
# Payload Size Analysis
# =============================================================================

class TestPayloadSizeBenchmarks:
    """Analyze payload sizes for islands."""
    
    def test_island_html_size(self):
        """Measure island HTML size."""
        result = SimpleIsland()
        html = result.render()
        
        size = len(html.encode('utf-8'))
        print(f"\nSimple island HTML: {size} bytes")
        
        # Should be reasonable
        assert size < 500
    
    def test_island_script_size(self):
        """Measure hydration script size."""
        result = SimpleIsland()
        script = result.get_hydration_script()
        
        size = len(script.encode('utf-8'))
        print(f"\nSingle island script: {size} bytes")
        
        # Script should be compact
        assert size < 500
    
    def test_multiple_islands_script_size(self):
        """Measure script size for multiple islands."""
        islands = [SimpleIsland() for _ in range(10)]
        script = generate_island_script(islands)
        
        size = len(script.encode('utf-8'))
        print(f"\n10 islands script: {size} bytes")
        
        # Should scale reasonably
        assert size < 5000
    
    def test_hydration_data_size(self):
        """Measure hydration data JSON size."""
        islands = [SimpleIsland() for _ in range(10)]
        data = get_island_hydration_data(islands)
        json_str = json.dumps(data)
        
        size = len(json_str.encode('utf-8'))
        print(f"\n10 islands JSON: {size} bytes")
        
        # Data should be compact
        assert size < 2000
    
    def test_static_vs_island_comparison(self):
        """Compare static component vs island sizes."""
        # Static
        static_html = div()["Hello World"].render()
        static_size = len(static_html.encode('utf-8'))
        
        # Island
        @island
        def HelloIsland():
            return div()["Hello World"]
        
        island_result = HelloIsland()
        island_html = island_result.render()
        island_size = len(island_html.encode('utf-8'))
        
        script = island_result.get_hydration_script()
        script_size = len(script.encode('utf-8'))
        
        total_island_size = island_size + script_size
        
        overhead = total_island_size - static_size
        overhead_pct = (overhead / static_size) * 100 if static_size > 0 else 0
        
        print(f"\nStatic HTML: {static_size} bytes")
        print(f"Island HTML: {island_size} bytes")
        print(f"Island Script: {script_size} bytes")
        print(f"Total Island: {total_island_size} bytes")
        print(f"Overhead: {overhead} bytes ({overhead_pct:.1f}%)")


# =============================================================================
# Strategy Performance Comparison
# =============================================================================

class TestStrategyPerformance:
    """Compare performance of different hydration strategies."""
    
    def test_all_strategies_render_time(self, benchmark):
        """Measure render time for all strategies."""
        strategies = [
            ("LOAD", HydrationStrategy.LOAD),
            ("VISIBLE", HydrationStrategy.VISIBLE),
            ("IDLE", HydrationStrategy.IDLE),
            ("MEDIA", HydrationStrategy.MEDIA),
            ("NONE", HydrationStrategy.NONE),
        ]
        
        def render_all():
            results = []
            for name, strategy in strategies:
                @island(strategy=strategy)
                def TestIsland():
                    return div()[f"Strategy: {name}"]
                results.append(TestIsland().render())
            return results
        
        results = benchmark(render_all)
        assert len(results) == 5
    
    def test_strategy_script_sizes(self):
        """Compare script sizes by strategy."""
        print("\nScript sizes by strategy:")
        
        for strategy in HydrationStrategy:
            @island(strategy=strategy)
            def TestIsland():
                return div()[f"Content"]
            
            result = TestIsland()
            script = result.get_hydration_script()
            size = len(script.encode('utf-8'))
            print(f"  {strategy.value}: {size} bytes")


# =============================================================================
# Real-World Scenario Benchmarks
# =============================================================================

class TestRealWorldScenarios:
    """Benchmark real-world usage patterns."""
    
    def test_dashboard_page(self, benchmark):
        """Benchmark typical dashboard with mixed content."""
        @island
        def UserWidget():
            return div()["User info"]
        
        @island(strategy=HydrationStrategy.VISIBLE)
        def ChartWidget():
            return div()["Chart"]
        
        @island(strategy=HydrationStrategy.IDLE)
        def NotificationsWidget():
            return div()["Notifications"]
        
        def render_dashboard():
            return div()[
                h1()["Dashboard"],  # Static
                section()[
                    UserWidget(),
                    ChartWidget(),
                    NotificationsWidget(),
                ],
                p()["Footer"],  # Static
            ].render()
        
        html = benchmark(render_dashboard)
        assert "Dashboard" in html
    
    def test_blog_page(self, benchmark):
        """Benchmark blog page (mostly static with interactive elements)."""
        @island
        def LikeButton():
            count = Signal(42)
            return button()[f"❤️ {count}"]
        
        @island
        def CommentForm():
            return div()["Comment form"]
        
        def render_blog():
            content = article()[
                h1()["Blog Post Title"],
                p()["Lorem ipsum " * 100],  # Long content
                p()["More content " * 50],
                LikeButton(),  # Small island
                CommentForm(),  # Small island
            ].render()
            
            return content
        
        html = benchmark(render_blog)
        assert "Blog Post" in html
    
    def test_e_commerce_product(self, benchmark):
        """Benchmark e-commerce product page."""
        @island
        def AddToCart():
            return button()["Add to Cart"]
        
        @island
        def QuantitySelector():
            qty = Signal(1)
            return div()[f"Qty: {qty}"]
        
        @island(strategy=HydrationStrategy.VISIBLE)
        def Reviews():
            return div()["Reviews section"]
        
        def render_product():
            return div()[
                h1()["Product Name"],  # Static
                p()["$99.99"],  # Static
                div()["Description " * 20],  # Static
                AddToCart(),  # Island
                QuantitySelector(),  # Island
                Reviews(),  # Lazy island
            ].render()
        
        html = benchmark(render_product)
        assert "Product Name" in html


# =============================================================================
# Summary Stats
# =============================================================================

def test_print_summary_stats():
    """Print summary statistics for islands."""
    print("\n" + "=" * 70)
    print("ISLANDS ARCHITECTURE - PERFORMANCE SUMMARY")
    print("=" * 70)
    
    # Measure baseline
    static_content = div()[
        h1()["Title"],
        p()["Content " * 50],
        div()["Footer"],
    ].render()
    static_size = len(static_content.encode('utf-8'))
    
    # Measure with islands
    @island
    def InteractiveButton():
        return button()["Click"]
    
    island_content = div()[
        h1()["Title"],  # Static
        p()["Content " * 50],  # Static
        InteractiveButton(),  # Island
        div()["Footer"],  # Static
    ].render()
    
    island_result = InteractiveButton()
    script = island_result.get_hydration_script()
    
    island_size = len(island_content.encode('utf-8'))
    script_size = len(script.encode('utf-8'))
    
    print(f"\nPage Size Comparison:")
    print(f"  Static page:     {static_size} bytes")
    print(f"  Page with island: {island_size} bytes (HTML)")
    print(f"  Island script:    {script_size} bytes")
    print(f"  Total with island: {island_size + script_size} bytes")
    
    # Compare to hypothetical full hydration
    # (In full hydration, everything gets JavaScript)
    estimated_full_hydration = static_size * 3  # Rough estimate
    actual_island = island_size + script_size
    savings = estimated_full_hydration - actual_island
    savings_pct = (savings / estimated_full_hydration) * 100
    
    print(f"\nEstimated Savings vs Full Hydration:")
    print(f"  Full hydration (est): {estimated_full_hydration} bytes")
    print(f"  Islands approach:     {actual_island} bytes")
    print(f"  Savings:              {savings} bytes ({savings_pct:.1f}%)")
    
    print("\nHydration Strategies Available:")
    for strategy in HydrationStrategy:
        print(f"  - {strategy.value}")
    
    print("\n" + "=" * 70)

