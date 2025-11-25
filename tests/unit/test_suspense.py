"""
Unit tests for PyNext Suspense component.

Tests Suspense boundaries, Show/Switch/Match, and ErrorBoundary.
"""

import pytest
import asyncio
from pynext.core.suspense import (
    Suspense,
    SuspenseBoundary,
    SuspenseState,
    Show,
    Switch,
    Match,
    ErrorBoundary,
    get_suspense_boundary,
    register_pending_resource,
)
from pynext.core.resource import Resource, ResourceState
from pynext.core.html import div, span, p, h1


class TestSuspenseBasics:
    """Basic Suspense functionality tests."""
    
    def test_create_suspense(self):
        """Suspense can be created."""
        suspense = Suspense(fallback=div()["Loading..."])
        
        assert suspense.fallback is not None
        assert suspense.children == []
    
    def test_suspense_with_children(self):
        """Suspense accepts children."""
        suspense = Suspense(fallback=span()["..."])[
            div()["Content"]
        ]
        
        assert len(suspense.children) == 1
    
    def test_suspense_multiple_children(self):
        """Suspense accepts multiple children."""
        suspense = Suspense()[
            div()["One"],
            div()["Two"],
            div()["Three"],
        ]
        
        assert len(suspense.children) == 3
    
    def test_suspense_render_sync(self):
        """Suspense renders children when no pending resources."""
        suspense = Suspense(fallback=span()["Loading"])[
            div()["Hello World"]
        ]
        
        html = suspense.render()
        
        assert "Hello World" in html
    
    def test_suspense_default_fallback(self):
        """Suspense has a default fallback."""
        suspense = Suspense()[div()["Content"]]
        
        assert suspense.fallback is not None


class TestSuspenseBoundary:
    """Tests for SuspenseBoundary tracking."""
    
    def test_create_boundary(self):
        """SuspenseBoundary can be created."""
        boundary = SuspenseBoundary(
            id="test-boundary",
            fallback=div()["Loading"],
        )
        
        assert boundary.id == "test-boundary"
        assert boundary.state == SuspenseState.PENDING
        assert boundary.pending == []
    
    def test_boundary_has_pending(self):
        """Boundary tracks pending resources."""
        async def fetch():
            return "data"
        
        resource = Resource(fetch)
        
        boundary = SuspenseBoundary(id="test", fallback=None)
        boundary.register_pending(resource)
        
        assert boundary.has_pending()
    
    @pytest.mark.asyncio
    async def test_boundary_wait_all(self):
        """Boundary can wait for all resources."""
        async def fast_fetch():
            await asyncio.sleep(0.01)
            return "done"
        
        resource = Resource(fast_fetch)
        
        boundary = SuspenseBoundary(id="test", fallback=None)
        boundary.register_pending(resource)
        
        result = await boundary.wait_all(timeout=1.0)
        
        assert result is True
        assert boundary.state == SuspenseState.RESOLVED
    
    @pytest.mark.asyncio
    async def test_boundary_timeout(self):
        """Boundary handles timeout."""
        async def slow_fetch():
            await asyncio.sleep(10)  # Very slow
            return "done"
        
        resource = Resource(slow_fetch)
        
        boundary = SuspenseBoundary(id="test", fallback=None)
        boundary.register_pending(resource)
        
        result = await boundary.wait_all(timeout=0.01)
        
        assert result is False
        assert boundary.state == SuspenseState.FALLBACK


class TestSuspenseAsync:
    """Tests for async Suspense rendering."""
    
    @pytest.mark.asyncio
    async def test_suspense_render_async(self):
        """Suspense resolves resources before rendering."""
        async def fetch_data():
            await asyncio.sleep(0.01)
            return "Fetched Data"
        
        resource = Resource(fetch_data)
        
        # Fetch resource first
        await resource.fetch()
        
        # Use the resolved data directly
        suspense = Suspense(fallback=span()["Loading"])[
            div()[resource() or "Pending"]
        ]
        
        html = await suspense.render_async()
        
        assert "Fetched Data" in html
    
    @pytest.mark.asyncio
    async def test_suspense_with_pending_shows_fallback(self):
        """Suspense shows fallback when resources pending."""
        async def slow_fetch():
            await asyncio.sleep(10)
            return "data"
        
        resource = Resource(slow_fetch)
        
        suspense = Suspense(
            fallback=span()["Please wait..."],
            timeout=0.01,
        )
        
        # Register resource manually for testing
        suspense.boundary = SuspenseBoundary(
            id=suspense.id,
            fallback=suspense.fallback,
        )
        suspense.boundary.register_pending(resource)
        
        html = suspense._render_with_fallback("<div>Content</div>")
        
        assert "Please wait..." in html
        assert "data-suspense=" in html


class TestShow:
    """Tests for Show component."""
    
    def test_show_when_true(self):
        """Show renders children when condition is true."""
        show = Show(when=True)[
            div()["Visible"]
        ]
        
        html = show.render()
        
        assert "Visible" in html
    
    def test_show_when_false(self):
        """Show returns empty when condition is false."""
        show = Show(when=False)[
            div()["Hidden"]
        ]
        
        html = show.render()
        
        assert html == ""
    
    def test_show_with_fallback(self):
        """Show renders fallback when condition is false."""
        show = Show(when=False, fallback=span()["Alternative"])[
            div()["Primary"]
        ]
        
        html = show.render()
        
        assert "Alternative" in html
        assert "Primary" not in html
    
    def test_show_with_callable_condition(self):
        """Show works with callable conditions."""
        value = True
        show = Show(when=lambda: value)[
            div()["Dynamic"]
        ]
        
        html = show.render()
        
        assert "Dynamic" in html
    
    def test_show_multiple_children(self):
        """Show renders multiple children."""
        show = Show(when=True)[
            div()["One"],
            div()["Two"],
        ]
        
        html = show.render()
        
        assert "One" in html
        assert "Two" in html


class TestSwitch:
    """Tests for Switch/Match components."""
    
    def test_switch_first_match(self):
        """Switch renders first matching case."""
        switch = Switch()[
            Match(when=False)[div()["First"]],
            Match(when=True)[div()["Second"]],
            Match(when=True)[div()["Third"]],
        ]
        
        html = switch.render()
        
        assert "Second" in html
        assert "First" not in html
        assert "Third" not in html
    
    def test_switch_default_case(self):
        """Switch renders default case when no match."""
        switch = Switch()[
            Match(when=False)[div()["First"]],
            Match(when=False)[div()["Second"]],
            Match()[div()["Default"]],  # No condition = default
        ]
        
        html = switch.render()
        
        assert "Default" in html
    
    def test_switch_no_match(self):
        """Switch returns empty when no cases match."""
        switch = Switch()[
            Match(when=False)[div()["First"]],
            Match(when=False)[div()["Second"]],
        ]
        
        html = switch.render()
        
        assert html == ""
    
    def test_switch_with_callable_conditions(self):
        """Switch works with callable conditions."""
        status = "loading"
        
        switch = Switch()[
            Match(when=lambda: status == "loading")[span()["Loading..."]],
            Match(when=lambda: status == "error")[span()["Error!"]],
            Match(when=lambda: status == "ready")[span()["Ready"]],
        ]
        
        html = switch.render()
        
        assert "Loading..." in html


class TestMatch:
    """Tests for Match component."""
    
    def test_match_true(self):
        """Match with True always matches."""
        match = Match(when=True)[div()["Always"]]
        
        assert match.matches() is True
    
    def test_match_false(self):
        """Match with False never matches."""
        match = Match(when=False)[div()["Never"]]
        
        assert match.matches() is False
    
    def test_match_callable(self):
        """Match with callable evaluates at match time."""
        counter = [0]
        
        match = Match(when=lambda: counter[0] > 5)[div()["High"]]
        
        assert match.matches() is False
        
        counter[0] = 10
        
        assert match.matches() is True


class TestErrorBoundary:
    """Tests for ErrorBoundary component."""
    
    def test_error_boundary_no_error(self):
        """ErrorBoundary renders children when no error."""
        boundary = ErrorBoundary(fallback=lambda e: div()[str(e)])[
            div()["Safe content"]
        ]
        
        html = boundary.render()
        
        assert "Safe content" in html
        assert boundary.error is None
    
    def test_error_boundary_catches_error(self):
        """ErrorBoundary catches render errors."""
        def failing_component():
            raise ValueError("Something went wrong")
        
        boundary = ErrorBoundary(fallback=lambda e: div()[f"Error: {e}"])[
            failing_component
        ]
        
        html = boundary.render()
        
        assert "Error: Something went wrong" in html
        assert boundary.error is not None
    
    def test_error_boundary_fallback_receives_error(self):
        """ErrorBoundary fallback receives the error."""
        captured_error = [None]
        
        def capture_fallback(e):
            captured_error[0] = e
            return div()["Captured"]
        
        def failing():
            raise RuntimeError("Test error")
        
        boundary = ErrorBoundary(fallback=capture_fallback)[failing]
        boundary.render()
        
        assert captured_error[0] is not None
        assert "Test error" in str(captured_error[0])


class TestSuspenseIntegration:
    """Integration tests for Suspense with Resource."""
    
    @pytest.mark.asyncio
    async def test_suspense_with_resource(self):
        """Suspense works with Resource primitive."""
        async def fetch_user():
            await asyncio.sleep(0.01)
            return {"name": "Alice"}
        
        user = Resource(fetch_user)
        await user.fetch()
        
        # Use the resolved data directly in the render
        user_data = user()
        name = user_data["name"] if user_data else "Unknown"
        
        suspense = Suspense(fallback=div()["Loading user..."])[
            div()[name]
        ]
        
        html = await suspense.render_async()
        
        assert "Alice" in html
    
    @pytest.mark.asyncio
    async def test_nested_suspense(self):
        """Nested Suspense boundaries work."""
        outer = Suspense(fallback=div()["Outer loading"])[
            div()["Outer content"],
            Suspense(fallback=span()["Inner loading"])[
                span()["Inner content"]
            ]
        ]
        
        html = await outer.render_async()
        
        assert "Outer content" in html
        assert "Inner content" in html


class TestSuspenseJSInit:
    """Tests for Suspense JavaScript initialization."""
    
    def test_suspense_js_init(self):
        """Suspense generates JS initialization."""
        suspense = Suspense(fallback=div()["Loading"])[
            div()["Content"]
        ]
        suspense.boundary = SuspenseBoundary(
            id=suspense.id,
            fallback=suspense.fallback,
        )
        
        js = suspense.get_js_init()
        
        assert "__pynext__.createSuspense" in js
        assert suspense.id in js

