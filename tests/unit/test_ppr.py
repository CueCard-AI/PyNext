"""
Unit tests for Partial Prerendering (PPR).

Tests:
- PPR decorators
- Static/dynamic analysis
- PPR boundaries
- Streaming integration
"""

import pytest
import asyncio
from pynext.core.ppr import (
    partial_prerender,
    static_part,
    dynamic_part,
    StaticShell,
    DynamicHole,
    PPRMode,
    ComponentType,
    PPRContext,
    PPRBoundary,
    PPRAnalyzer,
    get_ppr_context,
    create_ppr_context,
    analyze_component,
    get_ppr_runtime_js,
    needs_ppr_runtime,
)
from pynext.core.html import div, h1, p


class TestPPRDecorators:
    """Tests for PPR decorators."""
    
    def test_partial_prerender_marks_function(self):
        """@partial_prerender should mark function."""
        @partial_prerender()
        def my_page():
            return div()["Hello"]
        
        assert hasattr(my_page, '_ppr_enabled')
        assert my_page._ppr_enabled is True
    
    def test_static_part_marks_function(self):
        """@static_part should mark function as static."""
        @static_part
        def my_header():
            return h1()["Header"]
        
        assert hasattr(my_header, '_ppr_static')
        assert my_header._ppr_static is True
    
    def test_dynamic_part_marks_function(self):
        """@dynamic_part should mark function as dynamic."""
        @dynamic_part()
        def my_content():
            return p()["Dynamic"]
        
        assert hasattr(my_content, '_ppr_dynamic')
        assert my_content._ppr_dynamic is True


class TestPPRContext:
    """Tests for PPR context."""
    
    def test_create_context(self):
        """Should create PPR context."""
        ctx = create_ppr_context(mode=PPRMode.HYBRID)
        
        assert ctx.mode == PPRMode.HYBRID
        assert len(ctx.boundaries) == 0
    
    def test_add_boundary(self):
        """Context should track boundaries."""
        ctx = PPRContext(mode=PPRMode.HYBRID)
        
        boundary = PPRBoundary(
            id="test-1",
            placeholder_html="<div>Loading...</div>",
        )
        
        ctx.add_boundary(boundary)
        
        assert "test-1" in ctx.boundaries
        assert "test-1" in ctx.dynamic_pending
    
    def test_resolve_boundary(self):
        """Context should resolve boundaries."""
        ctx = PPRContext(mode=PPRMode.HYBRID)
        
        boundary = PPRBoundary(
            id="test-1",
            placeholder_html="<div>Loading...</div>",
        )
        ctx.add_boundary(boundary)
        
        ctx.resolve_boundary("test-1", "<div>Content</div>")
        
        assert ctx.boundaries["test-1"].is_resolved
        assert ctx.boundaries["test-1"].resolved_content == "<div>Content</div>"
        assert "test-1" not in ctx.dynamic_pending


class TestPPRBoundary:
    """Tests for PPR boundaries."""
    
    def test_boundary_creation(self):
        """Should create boundary with placeholder."""
        boundary = PPRBoundary(
            id="boundary-1",
            placeholder_html="<div>Loading...</div>",
        )
        
        assert boundary.id == "boundary-1"
        assert boundary.is_resolved is False
    
    def test_boundary_tracks_state(self):
        """Boundary should track resolution state."""
        boundary = PPRBoundary(
            id="boundary-1",
            placeholder_html="<div>Loading...</div>",
        )
        
        assert not boundary.is_resolved
        
        boundary.is_resolved = True
        boundary.resolved_content = "<div>Done</div>"
        
        assert boundary.is_resolved


class TestPPRAnalyzer:
    """Tests for PPR component analyzer."""
    
    def test_analyzer_detects_static(self):
        """Analyzer should detect static components."""
        def static_component():
            return div()["Static content"]
        
        analysis = analyze_component(static_component)
        
        # No signals, async, or request data
        assert not analysis.has_signals
        assert not analysis.has_async
        assert not analysis.has_request_data
    
    def test_analyzer_detects_async(self):
        """Analyzer should detect async components."""
        async def async_component():
            await asyncio.sleep(0)
            return div()["Async"]
        
        analysis = analyze_component(async_component)
        
        assert analysis.has_async
    
    def test_is_fully_static(self):
        """Analyzer should determine fully static."""
        analyzer = PPRAnalyzer()
        
        def static_fn():
            return "static"
        
        assert analyzer.is_fully_static(static_fn)


class TestStaticShell:
    """Tests for StaticShell component."""
    
    def test_static_shell_renders_children(self):
        """StaticShell should render its children."""
        shell = StaticShell()[
            div()["Child 1"],
            div()["Child 2"],
        ]
        
        html = shell.render()
        
        assert "Child 1" in html
        assert "Child 2" in html
    
    def test_static_shell_no_wrapper(self):
        """StaticShell should not add extra wrapper."""
        shell = StaticShell()[
            div()["Content"]
        ]
        
        html = shell.render()
        
        # Should just be the children, no PPR markers
        assert "data-ppr" not in html


class TestDynamicHole:
    """Tests for DynamicHole component."""
    
    def test_dynamic_hole_renders_placeholder(self):
        """DynamicHole should render placeholder."""
        hole = DynamicHole(
            fallback=lambda: div()["Loading..."],
        )[
            div()["Dynamic content"]
        ]
        
        html = hole.render()
        
        assert "data-ppr" in html
        assert "Loading..." in html
    
    def test_dynamic_hole_tracks_id(self):
        """DynamicHole should have unique ID."""
        hole1 = DynamicHole()
        hole2 = DynamicHole()
        
        assert hole1.id != hole2.id
        assert "hole_" in hole1.id


class TestPPRRuntime:
    """Tests for PPR runtime."""
    
    def test_runtime_js_content(self):
        """PPR runtime should contain essential functions."""
        js = get_ppr_runtime_js()
        
        assert "ppr" in js
        assert "resolve" in js
        assert "setLoading" in js
        assert "setError" in js
    
    def test_needs_runtime_false_without_boundaries(self):
        """Should not need runtime without boundaries."""
        # Create fresh context
        ctx = create_ppr_context()
        
        assert not needs_ppr_runtime() or len(ctx.boundaries) == 0


class TestPPRGranularity:
    """Tests for component-level PPR granularity."""
    
    def test_component_level_boundaries(self):
        """PPR should work at component level, not just page level."""
        ctx = create_ppr_context()
        
        # Multiple boundaries in same page
        boundary1 = PPRBoundary(id="sidebar", placeholder_html="<div>Sidebar loading</div>")
        boundary2 = PPRBoundary(id="main", placeholder_html="<div>Main loading</div>")
        boundary3 = PPRBoundary(id="footer", placeholder_html="<div>Footer loading</div>")
        
        ctx.add_boundary(boundary1)
        ctx.add_boundary(boundary2)
        ctx.add_boundary(boundary3)
        
        # All three should be tracked
        assert len(ctx.boundaries) == 3
        assert len(ctx.dynamic_pending) == 3
    
    def test_independent_resolution(self):
        """Boundaries should resolve independently."""
        ctx = create_ppr_context()
        
        ctx.add_boundary(PPRBoundary(id="fast", placeholder_html=""))
        ctx.add_boundary(PPRBoundary(id="slow", placeholder_html=""))
        
        # Resolve fast one
        ctx.resolve_boundary("fast", "Fast content")
        
        # Fast resolved, slow still pending
        assert ctx.boundaries["fast"].is_resolved
        assert not ctx.boundaries["slow"].is_resolved
        assert "fast" not in ctx.dynamic_pending
        assert "slow" in ctx.dynamic_pending

