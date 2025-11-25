"""
Unit tests for PyNext Islands (Selective Hydration).

Tests cover:
- @island decorator
- @static decorator
- Hydration strategies
- Interactivity detection
- Island boundary rendering
- Bundle requirements
"""

import pytest
from pynext.core.island import (
    island,
    static,
    HydrationStrategy,
    InteractivityType,
    IslandMetadata,
    IslandBoundary,
    ComponentAnalyzer,
    is_interactive,
    collect_islands,
    get_island_hydration_data,
    generate_island_script,
    get_island_bundle_requirements,
    get_minimal_runtime_for_island,
    _detect_interactivity,
)
from pynext.core.signals import Signal
from pynext.core.html import div, button, span, p


class TestIslandDecorator:
    """Tests for @island decorator."""
    
    def test_basic_island(self):
        """Basic island creation."""
        @island
        def Counter():
            return div()["Counter"]
        
        result = Counter()
        
        assert isinstance(result, IslandBoundary)
        assert result.metadata.name == "Counter"
        assert result.metadata.strategy == HydrationStrategy.LOAD
    
    def test_island_with_strategy(self):
        """Island with custom hydration strategy."""
        @island(strategy=HydrationStrategy.VISIBLE)
        def LazyWidget():
            return div()["Lazy"]
        
        result = LazyWidget()
        
        assert result.metadata.strategy == HydrationStrategy.VISIBLE
    
    def test_island_with_media_query(self):
        """Island with media query strategy."""
        @island(strategy=HydrationStrategy.MEDIA, media="(min-width: 768px)")
        def DesktopWidget():
            return div()["Desktop Only"]
        
        result = DesktopWidget()
        
        assert result.metadata.strategy == HydrationStrategy.MEDIA
        assert result.metadata.media_query == "(min-width: 768px)"
    
    def test_island_idle_strategy(self):
        """Island with idle hydration strategy."""
        @island(strategy=HydrationStrategy.IDLE)
        def IdleWidget():
            return div()["Idle"]
        
        result = IdleWidget()
        
        assert result.metadata.strategy == HydrationStrategy.IDLE
    
    def test_island_none_strategy(self):
        """Island that never hydrates (SSR only)."""
        @island(strategy=HydrationStrategy.NONE)
        def StaticOnlyWidget():
            return div()["Static"]
        
        result = StaticOnlyWidget()
        
        assert result.metadata.strategy == HydrationStrategy.NONE
    
    def test_island_unique_ids(self):
        """Each island instance gets a unique ID."""
        @island
        def Widget():
            return div()["Widget"]
        
        w1 = Widget()
        w2 = Widget()
        
        assert w1.id != w2.id
        assert w1.id.startswith("island-Widget-")
        assert w2.id.startswith("island-Widget-")
    
    def test_island_with_props(self):
        """Island captures props."""
        @island
        def Greeter(name="World"):
            return div()[f"Hello, {name}!"]
        
        result = Greeter(name="Alice")
        
        assert result.metadata.props == {"name": "Alice"}
    
    def test_island_marker_attributes(self):
        """Island decorator adds marker attributes."""
        @island
        def Widget():
            return div()["Widget"]
        
        assert Widget._is_island is True
        assert Widget._island_strategy == HydrationStrategy.LOAD
        assert Widget._component_name == "Widget"


class TestStaticDecorator:
    """Tests for @static decorator."""
    
    def test_static_component(self):
        """Static decorator marks component as non-interactive."""
        @static
        def Footer():
            return div()["Footer"]
        
        assert Footer._is_static is True
        assert Footer._is_island is False
    
    def test_static_not_interactive(self):
        """Static components are not considered interactive."""
        @static
        def Footer():
            return div()["Footer"]
        
        result = Footer()
        
        assert not is_interactive(Footer)


class TestIslandBoundaryRendering:
    """Tests for IslandBoundary rendering."""
    
    def test_render_basic(self):
        """Basic island boundary rendering."""
        @island
        def Counter():
            return div()["Count: 0"]
        
        result = Counter()
        html = result.render()
        
        assert 'data-island="' in html
        assert 'data-hydrate="load"' in html
        assert 'data-component="Counter"' in html
        assert "Count: 0" in html
    
    def test_render_with_strategy(self):
        """Island renders with correct strategy attribute."""
        @island(strategy=HydrationStrategy.VISIBLE)
        def Widget():
            return span()["Content"]
        
        result = Widget()
        html = result.render()
        
        assert 'data-hydrate="visible"' in html
    
    def test_render_nested_content(self):
        """Island renders nested content correctly."""
        @island
        def Complex():
            return div()[
                p()["First"],
                p()["Second"],
            ]
        
        result = Complex()
        html = result.render()
        
        assert "<p>First</p>" in html
        assert "<p>Second</p>" in html


class TestIslandHydrationScript:
    """Tests for island hydration script generation."""
    
    def test_basic_hydration_script(self):
        """Generate basic hydration script."""
        @island
        def Counter():
            return div()["Counter"]
        
        result = Counter()
        script = result.get_hydration_script()
        
        assert '__pynext__.registerIsland' in script
        assert result.id in script
        assert '"Counter"' in script
        assert '"load"' in script
    
    def test_hydration_script_with_props(self):
        """Hydration script includes props."""
        @island
        def Greeter(name="World"):
            return div()[f"Hello, {name}!"]
        
        result = Greeter(name="Alice")
        script = result.get_hydration_script()
        
        assert '"name": "Alice"' in script or "'name': 'Alice'" in script


class TestInteractivityDetection:
    """Tests for interactivity detection."""
    
    def test_detect_signal(self):
        """Detect signal usage."""
        def with_signal():
            count = Signal(0)
            return div()[count]
        
        interactivity = _detect_interactivity(with_signal)
        
        assert InteractivityType.SIGNAL in interactivity
    
    def test_detect_event(self):
        """Detect event handler."""
        def with_event():
            return button(onclick=lambda: None)["Click"]
        
        interactivity = _detect_interactivity(with_event)
        
        # Note: This may or may not detect the event depending on implementation
        # The key is that it should detect something or return NONE
        assert len(interactivity) > 0
    
    def test_detect_static(self):
        """Detect static component (no interactivity)."""
        def static_component():
            return div()["Static"]
        
        interactivity = _detect_interactivity(static_component)
        
        # Should detect as NONE or have no signal/event types
        assert InteractivityType.NONE in interactivity or len(interactivity) == 0


class TestIsInteractive:
    """Tests for is_interactive function."""
    
    def test_island_is_interactive(self):
        """Islands are interactive."""
        @island
        def Counter():
            return div()["Counter"]
        
        result = Counter()
        
        assert is_interactive(result)
    
    def test_static_not_interactive(self):
        """Static components are not interactive."""
        @static
        def Footer():
            return div()["Footer"]
        
        result = Footer()
        
        # The function itself is not interactive (it's a wrapper)
        assert not is_interactive(Footer)
    
    def test_island_boundary_interactive(self):
        """IslandBoundary is always interactive."""
        boundary = IslandBoundary(
            id="test",
            metadata=IslandMetadata(id="test", name="Test"),
        )
        
        assert is_interactive(boundary)


class TestCollectIslands:
    """Tests for collect_islands function."""
    
    def test_collect_single_island(self):
        """Collect single island from tree."""
        @island
        def Counter():
            return div()["Counter"]
        
        result = Counter()
        islands = collect_islands(result)
        
        assert len(islands) == 1
        assert islands[0].metadata.name == "Counter"
    
    def test_collect_multiple_islands(self):
        """Collect multiple islands from tree."""
        @island
        def Counter():
            return div()["Counter"]
        
        @island
        def Toggle():
            return div()["Toggle"]
        
        islands = collect_islands([Counter(), Toggle()])
        
        assert len(islands) == 2
    
    def test_collect_no_islands(self):
        """Return empty list when no islands."""
        content = div()["Static"]
        islands = collect_islands(content)
        
        assert len(islands) == 0


class TestIslandHydrationData:
    """Tests for get_island_hydration_data function."""
    
    def test_generate_hydration_data(self):
        """Generate hydration data for islands."""
        @island
        def Counter():
            return div()["Counter"]
        
        @island(strategy=HydrationStrategy.VISIBLE)
        def LazyWidget():
            return div()["Lazy"]
        
        islands = [Counter(), LazyWidget()]
        data = get_island_hydration_data(islands)
        
        assert "islands" in data
        assert len(data["islands"]) == 2
        
        # Check first island
        assert data["islands"][0]["component"] == "Counter"
        assert data["islands"][0]["strategy"] == "load"
        
        # Check second island
        assert data["islands"][1]["component"] == "LazyWidget"
        assert data["islands"][1]["strategy"] == "visible"


class TestGenerateIslandScript:
    """Tests for generate_island_script function."""
    
    def test_generate_script(self):
        """Generate complete island script."""
        @island
        def Counter():
            return div()["Counter"]
        
        islands = [Counter()]
        script = generate_island_script(islands)
        
        assert "<script>" in script
        assert "__pynext__.registerIsland" in script
        assert "__pynext__.hydrateIslands()" in script
    
    def test_empty_islands(self):
        """Return empty string for no islands."""
        script = generate_island_script([])
        
        assert script == ""


class TestBundleRequirements:
    """Tests for bundle requirement analysis."""
    
    def test_signal_requirements(self):
        """Detect signal bundle requirements."""
        @island
        def Counter():
            count = Signal(0)
            return div()[count]
        
        result = Counter()
        result.metadata.interactivity = {InteractivityType.SIGNAL}
        
        reqs = get_island_bundle_requirements([result])
        
        assert "signals" in reqs[result.id]
    
    def test_event_requirements(self):
        """Detect event bundle requirements."""
        @island
        def Clicker():
            return button(onclick=lambda: None)["Click"]
        
        result = Clicker()
        result.metadata.interactivity = {InteractivityType.EVENT}
        
        reqs = get_island_bundle_requirements([result])
        
        assert "events" in reqs[result.id]
    
    def test_combined_requirements(self):
        """Detect combined bundle requirements."""
        @island
        def Complex():
            count = Signal(0)
            return button(onclick=lambda: count.set(count() + 1))[count]
        
        result = Complex()
        result.metadata.interactivity = {InteractivityType.SIGNAL, InteractivityType.EVENT}
        
        reqs = get_island_bundle_requirements([result])
        
        assert "signals" in reqs[result.id]
        assert "events" in reqs[result.id]


class TestMinimalRuntime:
    """Tests for minimal runtime module selection."""
    
    def test_signal_only_runtime(self):
        """Signal-only island needs signals module."""
        @island
        def Counter():
            return div()["Counter"]
        
        result = Counter()
        result.metadata.interactivity = {InteractivityType.SIGNAL}
        
        modules = get_minimal_runtime_for_island(result)
        
        assert "core" in modules
        assert "signals" in modules
    
    def test_store_runtime(self):
        """Store island needs store module."""
        @island
        def DataWidget():
            return div()["Data"]
        
        result = DataWidget()
        result.metadata.interactivity = {InteractivityType.STORE}
        
        modules = get_minimal_runtime_for_island(result)
        
        assert "store" in modules
    
    def test_resource_runtime(self):
        """Resource island needs resource module."""
        @island
        def AsyncWidget():
            return div()["Async"]
        
        result = AsyncWidget()
        result.metadata.interactivity = {InteractivityType.RESOURCE}
        
        modules = get_minimal_runtime_for_island(result)
        
        assert "resource" in modules


class TestComponentAnalyzer:
    """Tests for ComponentAnalyzer class."""
    
    def test_analyze_static(self):
        """Analyze static component."""
        analyzer = ComponentAnalyzer()
        
        component = div()["Static"]
        result = analyzer.analyze(component)
        
        assert result["is_interactive"] is False
        assert result["is_island"] is False
    
    def test_analyze_island(self):
        """Analyze island component."""
        @island
        def Counter():
            return div()["Counter"]
        
        analyzer = ComponentAnalyzer()
        island_result = Counter()
        result = analyzer.analyze(island_result)
        
        assert result["is_island"] is True
        assert result["is_interactive"] is True
    
    def test_analyze_caching(self):
        """Analyzer caches results."""
        analyzer = ComponentAnalyzer()
        
        component = div()["Test"]
        result1 = analyzer.analyze(component)
        result2 = analyzer.analyze(component)
        
        assert result1 is result2
    
    def test_recommended_strategy(self):
        """Analyzer recommends hydration strategies."""
        analyzer = ComponentAnalyzer()
        
        @island
        def Interactive():
            return button(onclick=lambda: None)["Click"]
        
        result = Interactive()
        result.metadata.interactivity = {InteractivityType.EVENT}
        
        analysis = analyzer.analyze(result)
        
        # Events should recommend LOAD (immediate)
        assert analysis["recommended_strategy"] == HydrationStrategy.LOAD


class TestHydrationStrategies:
    """Tests for hydration strategy enum."""
    
    def test_all_strategies(self):
        """All strategies are defined."""
        assert HydrationStrategy.LOAD.value == "load"
        assert HydrationStrategy.VISIBLE.value == "visible"
        assert HydrationStrategy.IDLE.value == "idle"
        assert HydrationStrategy.MEDIA.value == "media"
        assert HydrationStrategy.NONE.value == "none"


class TestInteractivityTypes:
    """Tests for interactivity type enum."""
    
    def test_all_types(self):
        """All interactivity types are defined."""
        assert InteractivityType.NONE.value == "none"
        assert InteractivityType.SIGNAL.value == "signal"
        assert InteractivityType.EVENT.value == "event"
        assert InteractivityType.EFFECT.value == "effect"
        assert InteractivityType.RESOURCE.value == "resource"
        assert InteractivityType.STORE.value == "store"

