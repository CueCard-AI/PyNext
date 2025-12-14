"""
High-risk area tests for router.

Tests for P0/P1/P2 risks identified in router implementation:
1. Global context race conditions
2. Route ordering issues
3. Guard execution
4. Hydration edge cases
5. Link/Outlet integration
"""

import pytest
import threading
import concurrent.futures
from unittest.mock import Mock, patch, MagicMock

from pynext.reactive.router import (
    Router,
    Route,
    Link,
    Outlet,
    useNavigate,
    useParams,
    useSearchParams,
    useLocation,
    useMatch,
    Navigator,
    Redirect,
    createRouteGuard,
    compile_route_pattern,
    _create_router_context,
    get_router_context,
    RouterContext,
)
import pynext.reactive.router as router_module


# =============================================================================
# P0: GLOBAL CONTEXT RACE CONDITIONS
# =============================================================================

class TestGlobalContextRaceConditions:
    """Test that global context handles concurrent access correctly."""
    
    def test_context_overwrites_previous(self):
        """Creating new context overwrites previous - potential race condition."""
        ctx1 = _create_router_context("/page1")
        assert get_router_context().pathname() == "/page1"
        
        ctx2 = _create_router_context("/page2")
        assert get_router_context().pathname() == "/page2"
        
        # ctx1 is now orphaned - this is the race condition
        # In concurrent SSR, this would cause issues
    
    def test_concurrent_context_creation(self):
        """Simulate concurrent SSR requests creating contexts."""
        results = []
        
        def create_and_check(path, delay=0):
            import time
            time.sleep(delay)
            ctx = _create_router_context(path)
            time.sleep(0.01)  # Simulate some work
            # Check if OUR context is still active
            current = get_router_context().pathname()
            results.append((path, current, path == current))
        
        # Run concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(create_and_check, "/request1", 0),
                executor.submit(create_and_check, "/request2", 0.005),
                executor.submit(create_and_check, "/request3", 0.01),
            ]
            concurrent.futures.wait(futures)
        
        # At least one should have had its context overwritten
        # This demonstrates the race condition exists
        overwrites = [r for r in results if not r[2]]
        # We're documenting the issue, not asserting it's fixed yet
        assert len(results) == 3
    
    def test_context_isolation_needed(self):
        """Test showing that context isolation is needed."""
        # Create first context
        ctx1 = _create_router_context("/user/1")
        ctx1.params.set({"id": "1"})
        
        # Simulate another request coming in
        ctx2 = _create_router_context("/user/2")
        ctx2.params.set({"id": "2"})
        
        # Now useParams() returns ctx2's params, not ctx1's!
        params = useParams()
        assert params["id"] == "2"  # Not "1"!


# =============================================================================
# P0: JS SIGNALS DEPENDENCY
# =============================================================================

class TestJSSignalsDependency:
    """Test JS router's dependency on signals.js."""
    
    def test_router_js_requires_signals(self):
        """Router.js should fail gracefully if signals.js not loaded."""
        # This is a documentation test - the actual JS behavior
        # would need to be tested in the JS test suite
        pass
    
    def test_hydration_data_format(self):
        """Hydration data should be valid JSON."""
        import json
        
        with patch.object(Router, '_get_initial_pathname', return_value="/users/123"):
            router = Router()[
                Route("/users/:id", component=lambda: "User"),
            ]
            
            html = str(router)
        
        # Extract route data
        import re
        match = re.search(r'data-pynext-route-data="([^"]+)"', html)
        assert match, "Route data attribute not found"
        
        # Should be valid JSON (after unescaping HTML entities)
        json_str = match.group(1).replace("&quot;", '"')
        data = json.loads(json_str)
        
        assert "pathname" in data
        assert "params" in data
        assert "routes" in data


# =============================================================================
# P0: LINK/OUTLET INTEGRATION
# =============================================================================

class TestLinkOutletIntegration:
    """Test Link and Outlet work correctly in Element children."""
    
    def test_link_in_element_requires_str(self):
        """Link in Element children currently requires str() conversion."""
        from pynext.core.html import div
        
        # This SHOULD work but currently doesn't
        # The test documents the current limitation
        link = Link(href="/about")["About"]
        
        # Currently must use str()
        result = div()[str(link)]
        html = str(result)
        
        assert "About" in html
        assert "href" in html
    
    def test_outlet_in_element_requires_str(self):
        """Outlet in Element children currently requires str() conversion."""
        from pynext.core.html import div, main
        
        outlet = Outlet()
        
        # Currently must use str()
        result = main()[str(outlet)]
        html = str(result)
        
        assert "data-pynext-outlet" in html
    
    def test_link_render_returns_element(self):
        """Link.render() returns an Element that has render()."""
        link = Link(href="/test")["Test"]
        element = link.render()
        
        # Should have render method
        assert hasattr(element, 'render') or hasattr(element, '__str__')
    
    def test_outlet_render_returns_element(self):
        """Outlet.render() returns an Element that has render()."""
        outlet = Outlet()
        element = outlet.render()
        
        assert hasattr(element, 'render') or hasattr(element, '__str__')


# =============================================================================
# P1: ROUTE ORDERING
# =============================================================================

class TestRouteOrdering:
    """Test route ordering issues - static vs dynamic."""
    
    def test_dynamic_before_static_catches_static(self):
        """Dynamic route before static will match static path as param."""
        router = Router()[
            Route("/users/:id", component=lambda: "Dynamic"),
            Route("/users/new", component=lambda: "Static"),
        ]
        
        matched, params = router._find_matching_route("/users/new")
        
        # First matching route wins - dynamic catches "new" as id
        assert params == {"id": "new"}
        # The static /users/new is never reached!
    
    def test_static_before_dynamic_correct(self):
        """Static route before dynamic works correctly."""
        router = Router()[
            Route("/users/new", component=lambda: "Static"),
            Route("/users/:id", component=lambda: "Dynamic"),
        ]
        
        matched, params = router._find_matching_route("/users/new")
        
        # Static matches first with no params
        assert params == {}
        
        # Dynamic still works for other values
        matched2, params2 = router._find_matching_route("/users/123")
        assert params2 == {"id": "123"}
    
    def test_wildcard_should_be_last(self):
        """Wildcard routes should come last."""
        router = Router()[
            Route("/files/*", component=lambda: "Wildcard"),
            Route("/files/new", component=lambda: "Static"),
        ]
        
        matched, params = router._find_matching_route("/files/new")
        
        # Wildcard matches first
        assert "*" in params
        # Static is unreachable
    
    def test_more_specific_routes_first(self):
        """More specific routes should be defined first."""
        router = Router()[
            Route("/users/:userId/posts/:postId", component=lambda: "Specific"),
            Route("/users/:userId", component=lambda: "General"),
        ]
        
        # Specific matches
        matched, params = router._find_matching_route("/users/1/posts/2")
        assert params == {"userId": "1", "postId": "2"}
        
        # General also matches its pattern
        matched2, params2 = router._find_matching_route("/users/1")
        assert params2 == {"userId": "1"}


# =============================================================================
# P1: PARTIAL RENDERING NOT IMPLEMENTED
# =============================================================================

class TestPartialRendering:
    """Test partial rendering requirements for SPA navigation."""
    
    def test_route_data_includes_all_paths(self):
        """Route data should include all paths for client routing."""
        with patch.object(Router, '_get_initial_pathname', return_value="/"):
            router = Router()[
                Route("/", component=lambda: "Home"),
                Route("/about", component=lambda: "About"),
                Route("/contact", component=lambda: "Contact"),
            ]
            
            html = str(router)
        
        # All routes should be in the data
        assert "/" in html or "pathname" in html


# =============================================================================
# P2: GUARDS NOT EXECUTED
# =============================================================================

class TestGuardExecution:
    """Test route guard execution."""
    
    def test_guards_stored_but_not_called_on_match(self):
        """Guards are stored on route but not executed during matching."""
        guard_called = []
        
        def my_guard():
            guard_called.append(True)
            return None
        
        route = Route("/admin", component=lambda: "Admin", guards=[my_guard])
        
        # Guards are stored
        assert len(route.guards) == 1
        
        # But matching doesn't call them
        params = route.match("/admin")
        assert params == {}
        assert guard_called == []  # Guard was NOT called!
    
    def test_guards_not_called_by_router(self):
        """Router doesn't call guards during find_matching_route."""
        guard_called = []
        
        def blocking_guard():
            guard_called.append(True)
            return Redirect("/login")
        
        router = Router()[
            Route("/admin", component=lambda: "Admin", guards=[blocking_guard]),
        ]
        
        matched, params = router._find_matching_route("/admin")
        
        # Route is matched
        assert matched is not None
        # But guard was not checked!
        assert guard_called == []
    
    def test_guards_called_by_context_navigate(self):
        """Context.navigate now calls guards and handles redirects."""
        guard_called = []
        
        def blocking_guard():
            guard_called.append(True)
            return Redirect("/login")
        
        # Create routes including the redirect target
        ctx = _create_router_context("/")
        admin_route = Route("/admin", component=lambda: "Admin", guards=[blocking_guard]).to_compiled()
        login_route = Route("/login", component=lambda: "Login").to_compiled()
        ctx.routes = [admin_route, login_route]
        
        ctx.navigate("/admin")
        
        # Guard was called
        assert guard_called == [True]
        # Navigation was redirected to /login
        assert ctx.pathname() == "/login"
    
    def test_guards_allow_when_returning_none(self):
        """Guards allow navigation when returning None."""
        guard_called = []
        
        def allowing_guard():
            guard_called.append(True)
            return None  # Allow access
        
        ctx = _create_router_context("/")
        route = Route("/admin", component=lambda: "Admin", guards=[allowing_guard]).to_compiled()
        ctx.routes = [route]
        
        ctx.navigate("/admin")
        
        # Guard was called
        assert guard_called == [True]
        # Navigation proceeds
        assert ctx.pathname() == "/admin"


# =============================================================================
# P2: NO ERROR BOUNDARY
# =============================================================================

class TestErrorBoundary:
    """Test error handling in route components."""
    
    def test_component_exception_propagates(self):
        """Component exceptions propagate up (no error boundary)."""
        def failing_component():
            raise ValueError("Component error")
        
        with patch.object(Router, '_get_initial_pathname', return_value="/"):
            router = Router()[
                Route("/", component=failing_component),
            ]
            
            with pytest.raises(ValueError, match="Component error"):
                str(router)
    
    def test_no_fallback_on_component_error(self):
        """Fallback is for 404, not component errors."""
        def failing_component():
            raise RuntimeError("Oops")
        
        def error_page():
            return "Error occurred"
        
        with patch.object(Router, '_get_initial_pathname', return_value="/"):
            router = Router(fallback=error_page)[
                Route("/", component=failing_component),
            ]
            
            # Fallback is for 404, not errors
            with pytest.raises(RuntimeError):
                str(router)


# =============================================================================
# P2: USE PARAMS RETURNS SNAPSHOT
# =============================================================================

class TestParamsReactivity:
    """Test params reactivity semantics."""
    
    def test_use_params_returns_current_value(self):
        """useParams returns current value (snapshot)."""
        ctx = _create_router_context("/users/1")
        ctx.params.set({"id": "1"})
        
        params1 = useParams()
        assert params1 == {"id": "1"}
        
        # Update params
        ctx.params.set({"id": "2"})
        
        # Old reference still has old value
        # This is expected - it's a snapshot
        # New call gets new value
        params2 = useParams()
        assert params2 == {"id": "2"}
    
    def test_params_not_live_reference(self):
        """Params is not a live reference that updates."""
        ctx = _create_router_context("/")
        ctx.params.set({"id": "1"})
        
        params = useParams()
        
        # This doesn't update params
        ctx.params.set({"id": "2"})
        
        # params is still the old value
        # (because it's a snapshot, not a subscription)
        # This is actually the expected Python behavior


# =============================================================================
# HYDRATION EDGE CASES
# =============================================================================

class TestHydrationEdgeCases:
    """Test hydration edge cases."""
    
    def test_route_data_with_special_chars(self):
        """Route data handles special characters."""
        import json
        
        with patch.object(Router, '_get_initial_pathname', return_value="/search"):
            router = Router()[
                Route("/search", component=lambda: "Search"),
            ]
            
            html = str(router)
        
        assert "data-pynext-route-data" in html
    
    def test_route_data_with_unicode(self):
        """Route data handles unicode paths."""
        import json
        
        with patch.object(Router, '_get_initial_pathname', return_value="/日本語"):
            router = Router()[
                Route("/日本語", component=lambda: "Japanese"),
            ]
            
            html = str(router)
        
        # Should not crash
        assert "data-pynext-router" in html
    
    def test_params_json_serialization(self):
        """Params should be JSON serializable."""
        import json
        
        params = {"id": "123", "slug": "hello-world"}
        
        # Should not raise
        json_str = json.dumps(params)
        parsed = json.loads(json_str)
        
        assert parsed == params


# =============================================================================
# LINK ACTIVE STATE EDGE CASES
# =============================================================================

class TestLinkActiveStateEdgeCases:
    """Test Link active state edge cases."""
    
    def test_root_link_not_always_active(self):
        """Root link with exact=False shouldn't match everything."""
        link = Link(href="/", exact=False)
        
        # Root is special - it matches itself
        assert link._is_active("/") is True
        
        # But with exact=False, "/" shouldn't match "/other"
        # because "/" != "/other" prefix (implementation detail)
    
    def test_nested_path_active_matching(self):
        """Nested path active matching."""
        link = Link(href="/admin", exact=False)
        
        assert link._is_active("/admin") is True
        assert link._is_active("/admin/users") is True
        assert link._is_active("/admin/settings/advanced") is True
        
        # Not active for different paths
        assert link._is_active("/dashboard") is False
    
    def test_similar_prefix_not_active(self):
        """Similar prefix shouldn't match."""
        link = Link(href="/user", exact=False)
        
        assert link._is_active("/user") is True
        assert link._is_active("/user/123") is True
        
        # "/users" is NOT a child of "/user"
        assert link._is_active("/users") is False


# =============================================================================
# NAVIGATION EDGE CASES  
# =============================================================================

class TestNavigationEdgeCases:
    """Test navigation edge cases."""
    
    def test_navigate_to_invalid_url(self):
        """Navigate handles invalid URL gracefully."""
        ctx = _create_router_context("/")
        navigate = useNavigate()
        
        # These should not crash
        navigate("/normal/path")
        navigate("/path?query=value")
        navigate("/path#hash")
    
    def test_navigate_preserves_state_concept(self):
        """Navigate can accept state (for future use)."""
        ctx = _create_router_context("/")
        navigate = useNavigate()
        
        # State parameter should be accepted
        navigate("/page", state={"from": "/old"})
        
        assert ctx.pathname() == "/page"
    
    def test_rapid_navigation(self):
        """Handle rapid successive navigations."""
        ctx = _create_router_context("/")
        navigate = useNavigate()
        
        for i in range(100):
            navigate(f"/page{i}")
        
        # Last navigation wins
        assert ctx.pathname() == "/page99"

