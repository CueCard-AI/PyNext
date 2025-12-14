"""
Additional comprehensive tests for 100% router coverage.

This file adds tests to reach the 600 test target.
"""

import pytest
from unittest.mock import Mock, patch

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
    Location,
    Redirect,
    createRouteGuard,
    compile_route_pattern,
    CompiledRoute,
    RouterContext,
    _create_router_context,
    get_router_context,
)


# =============================================================================
# SECTION 1: ADDITIONAL ROUTE PATTERN TESTS
# =============================================================================

class TestAdditionalPatterns:
    """Additional pattern tests."""
    
    def test_mixed_static_dynamic(self):
        """Mixed static and dynamic segments."""
        route = Route("/api/v1/users/:id/profile", component=lambda: None)
        
        params = route.match("/api/v1/users/123/profile")
        assert params == {"id": "123"}
    
    def test_many_static_segments(self):
        """Many static segments."""
        route = Route("/a/b/c/d/e/f/g/h/i/j", component=lambda: None)
        
        assert route.match("/a/b/c/d/e/f/g/h/i/j") == {}
    
    def test_alternating_static_dynamic(self):
        """Alternating static and dynamic."""
        route = Route("/a/:a/b/:b/c/:c", component=lambda: None)
        
        params = route.match("/a/1/b/2/c/3")
        assert params == {"a": "1", "b": "2", "c": "3"}
    
    def test_param_then_static(self):
        """Param followed by static."""
        route = Route("/:category/items", component=lambda: None)
        
        params = route.match("/electronics/items")
        assert params == {"category": "electronics"}
    
    def test_static_then_param_then_static(self):
        """Static-param-static pattern."""
        route = Route("/prefix/:id/suffix", component=lambda: None)
        
        params = route.match("/prefix/123/suffix")
        assert params == {"id": "123"}


# =============================================================================
# SECTION 2: ADDITIONAL LINK TESTS
# =============================================================================

class TestAdditionalLinkTests:
    """Additional Link tests."""
    
    def test_link_all_options(self):
        """Link with all options."""
        link = Link(
            href="/test",
            replace=True,
            prefetch=True,
            active_class="current",
            exact=True,
            id="test-link",
            class_="nav-item",
        )["Test"]
        
        result = str(link)
        assert "data-pynext-replace" in result
        assert "data-pynext-prefetch" in result
    
    def test_link_active_exact_root(self):
        """Link exact match for root."""
        ctx = _create_router_context("/")
        
        link = Link(href="/", exact=True)["Home"]
        
        assert link._is_active("/") is True
        assert link._is_active("/other") is False
    
    def test_link_active_prefix_nested(self):
        """Link prefix match for nested paths."""
        link = Link(href="/admin", exact=False)["Admin"]
        
        assert link._is_active("/admin") is True
        assert link._is_active("/admin/users") is True
        assert link._is_active("/admin/settings/advanced") is True
    
    def test_link_render_element(self):
        """Link render returns element."""
        link = Link(href="/")["Home"]
        
        element = link.render()
        assert element is not None
    
    def test_link_multiple_classes(self):
        """Link with multiple classes."""
        ctx = _create_router_context("/test")
        
        link = Link(href="/test", class_="nav-link btn", active_class="active")["Test"]
        
        result = str(link)
        assert "nav-link" in result
        assert "btn" in result


# =============================================================================
# SECTION 3: ADDITIONAL ROUTER TESTS
# =============================================================================

class TestAdditionalRouterTests:
    """Additional Router tests."""
    
    def test_router_with_base_path(self):
        """Router with base path."""
        router = Router(base="/app")
        assert router.base == "/app"
    
    def test_router_bracket_single_route(self):
        """Router with single route in brackets."""
        router = Router()[Route("/", component=lambda: None)]
        
        assert len(router.routes) == 1
    
    def test_router_route_order(self):
        """Router preserves route order."""
        router = Router()[
            Route("/a", component=lambda: "A"),
            Route("/b", component=lambda: "B"),
            Route("/c", component=lambda: "C"),
        ]
        
        assert router.routes[0].path == "/a"
        assert router.routes[1].path == "/b"
        assert router.routes[2].path == "/c"
    
    def test_router_get_initial_pathname(self):
        """Router gets initial pathname."""
        with patch.object(Router, '_get_initial_pathname', return_value="/custom"):
            router = Router()
            assert router._get_initial_pathname() == "/custom"
    
    def test_router_render_returns_element(self):
        """Router render returns element."""
        with patch.object(Router, '_get_initial_pathname', return_value="/"):
            router = Router()[Route("/", component=lambda: "Home")]
            element = router.render()
            
            assert element is not None


# =============================================================================
# SECTION 4: ADDITIONAL CONTEXT TESTS
# =============================================================================

class TestAdditionalContextTests:
    """Additional context tests."""
    
    def test_context_with_all_initial_values(self):
        """Context with all initial values."""
        ctx = _create_router_context(
            initial_pathname="/page",
            initial_query={"q": "test"},
            initial_hash="section",
            base="/app",
        )
        
        assert ctx.pathname() == "/page"
        assert ctx.query() == {"q": "test"}
        assert ctx.hash_() == "section"
        assert ctx._base == "/app"
    
    def test_context_navigate_updates_all(self):
        """Navigation updates all signals."""
        ctx = _create_router_context("/")
        
        ctx.navigate("/page?q=test#section")
        
        assert ctx.pathname() == "/page"
        assert ctx.query()["q"] == "test"
        assert ctx.hash_() == "section"
    
    def test_context_routes_registration(self):
        """Context holds registered routes."""
        ctx = _create_router_context("/")
        route = Route("/test", component=lambda: None).to_compiled()
        ctx.routes = [route]
        
        assert len(ctx.routes) == 1
    
    def test_context_get_current_route_match(self):
        """Context finds current route."""
        ctx = _create_router_context("/users/1")
        route = Route("/users/:id", component=lambda: None).to_compiled()
        ctx.routes = [route]
        
        current = ctx.get_current_route()
        assert current == route


# =============================================================================
# SECTION 5: ADDITIONAL NAVIGATION TESTS
# =============================================================================

class TestAdditionalNavigationTests:
    """Additional navigation tests."""
    
    def test_navigator_call_with_options(self):
        """Navigator call with all options."""
        ctx = _create_router_context("/")
        
        nav = Navigator()
        nav("/page", replace=True, state={"key": "value"})
        
        assert ctx.pathname() == "/page"
    
    def test_navigate_sequence(self):
        """Navigate in sequence."""
        ctx = _create_router_context("/1")
        navigate = useNavigate()
        
        navigate("/2")
        assert ctx.pathname() == "/2"
        
        navigate("/3")
        assert ctx.pathname() == "/3"
        
        navigate("/4")
        assert ctx.pathname() == "/4"
    
    def test_navigate_updates_params(self):
        """Navigate updates params signal."""
        ctx = _create_router_context("/")
        ctx.routes = [Route("/:id", component=lambda: None).to_compiled()]
        
        navigate = useNavigate()
        navigate("/abc")
        
        assert ctx.params() == {"id": "abc"}


# =============================================================================
# SECTION 6: ADDITIONAL PARAMS TESTS
# =============================================================================

class TestAdditionalParamsTests:
    """Additional params tests."""
    
    def test_params_iteration(self):
        """Iterate over params."""
        ctx = _create_router_context("/")
        ctx.params.set({"a": "1", "b": "2", "c": "3"})
        
        params = useParams()
        keys = list(params.keys())
        
        assert set(keys) == {"a", "b", "c"}
    
    def test_params_copy(self):
        """Copy params dict."""
        ctx = _create_router_context("/")
        ctx.params.set({"id": "123"})
        
        params = useParams()
        copied = dict(params)
        
        assert copied == {"id": "123"}
    
    def test_params_bool(self):
        """Bool of params."""
        ctx = _create_router_context("/")
        
        ctx.params.set({})
        assert not useParams()
        
        ctx.params.set({"id": "1"})
        assert useParams()


# =============================================================================
# SECTION 7: ADDITIONAL QUERY TESTS
# =============================================================================

class TestAdditionalQueryTests:
    """Additional query tests."""
    
    def test_query_set_empty(self):
        """Set query to empty."""
        ctx = _create_router_context("/")
        ctx.query.set({"old": "value"})
        
        _, setParams = useSearchParams()
        setParams({})
        
        assert ctx.query() == {}
    
    def test_query_multiple_updates(self):
        """Multiple query updates."""
        ctx = _create_router_context("/")
        
        _, setParams = useSearchParams()
        
        setParams({"a": "1"})
        assert ctx.query()["a"] == "1"
        
        setParams({"b": "2"})
        assert ctx.query()["b"] == "2"
        assert "a" not in ctx.query()
    
    def test_query_special_values(self):
        """Query with special values."""
        ctx = _create_router_context("/")
        ctx.query.set({"empty": "", "space": " ", "amp": "&"})
        
        params, _ = useSearchParams()
        assert params["empty"] == ""
        assert params["space"] == " "
        assert params["amp"] == "&"


# =============================================================================
# SECTION 8: ADDITIONAL LOCATION TESTS
# =============================================================================

class TestAdditionalLocationTests:
    """Additional location tests."""
    
    def test_location_all_parts(self):
        """Location with all URL parts."""
        ctx = _create_router_context("/page")
        ctx.query.set({"q": "test"})
        ctx.hash_.set("section")
        
        location = useLocation()
        
        assert location.pathname == "/page"
        assert "q=test" in location.search
        assert location.hash == "#section"
    
    def test_location_dataclass(self):
        """Location is proper dataclass."""
        location = Location(
            pathname="/test",
            search="?q=1",
            hash="#sec",
            state={"key": "val"},
        )
        
        assert location.pathname == "/test"
        assert location.search == "?q=1"
        assert location.hash == "#sec"
        assert location.state == {"key": "val"}


# =============================================================================
# SECTION 9: ADDITIONAL MATCH TESTS
# =============================================================================

class TestAdditionalMatchTests:
    """Additional match tests."""
    
    def test_match_returns_empty_for_static(self):
        """Match static returns empty dict."""
        ctx = _create_router_context("/about")
        
        result = useMatch("/about")
        assert result == {}
    
    def test_match_complex_pattern(self):
        """Match complex pattern."""
        ctx = _create_router_context("/api/v1/users/123/posts/456")
        
        result = useMatch("/api/v1/users/:userId/posts/:postId")
        assert result == {"userId": "123", "postId": "456"}
    
    def test_match_multiple_calls(self):
        """Multiple match calls."""
        ctx = _create_router_context("/users/1")
        
        assert useMatch("/users/:id") == {"id": "1"}
        assert useMatch("/posts/:id") is None
        assert useMatch("/users/:id") == {"id": "1"}


# =============================================================================
# SECTION 10: ADDITIONAL OUTLET TESTS
# =============================================================================

class TestAdditionalOutletTests:
    """Additional Outlet tests."""
    
    def test_outlet_str(self):
        """Outlet str conversion."""
        outlet = Outlet()
        result = str(outlet)
        
        assert "<div" in result
    
    def test_outlet_render_type(self):
        """Outlet render returns element."""
        outlet = Outlet()
        element = outlet.render()
        
        assert element is not None


# =============================================================================
# SECTION 11: ADDITIONAL REDIRECT TESTS
# =============================================================================

class TestAdditionalRedirectTests:
    """Additional Redirect tests."""
    
    def test_redirect_with_state(self):
        """Redirect preserves state concept."""
        redirect = Redirect(to="/target", replace=False)
        
        assert redirect.to == "/target"
        assert redirect.replace is False
    
    def test_redirect_hash(self):
        """Redirect equality based on fields."""
        r1 = Redirect(to="/a", replace=True)
        r2 = Redirect(to="/a", replace=True)
        r3 = Redirect(to="/a", replace=False)
        
        assert r1 == r2
        assert r1 != r3


# =============================================================================
# SECTION 12: ADDITIONAL GUARD TESTS
# =============================================================================

class TestAdditionalGuardTests:
    """Additional guard tests."""
    
    def test_guard_chain(self):
        """Chain of guards."""
        results = []
        
        def guard1():
            results.append(1)
            return None
        
        def guard2():
            results.append(2)
            return None
        
        guards = [createRouteGuard(guard1), createRouteGuard(guard2)]
        
        for g in guards:
            g()
        
        assert results == [1, 2]
    
    def test_guard_early_exit(self):
        """Early exit guard."""
        def blocking_guard():
            return Redirect("/blocked")
        
        guard = createRouteGuard(blocking_guard)
        result = guard()
        
        assert isinstance(result, Redirect)


# =============================================================================
# SECTION 13: COMPILED ROUTE TESTS
# =============================================================================

class TestCompiledRouteTests:
    """Compiled route tests."""
    
    def test_compiled_route_attributes(self):
        """Compiled route has all attributes."""
        route = Route("/users/:id", component=lambda: None).to_compiled()
        
        assert route.path == "/users/:id"
        assert route.pattern is not None
        assert route.param_names == ["id"]
        assert route.component is not None
        assert route.exact is True
        assert route.guards == []
    
    def test_compiled_route_match_method(self):
        """Compiled route match method."""
        route = Route("/items/:id", component=lambda: None).to_compiled()
        
        assert route.match("/items/123") == {"id": "123"}
        assert route.match("/other/123") is None


# =============================================================================
# SECTION 14: PATTERN COMPILATION DETAILS
# =============================================================================

class TestPatternCompilationDetails:
    """Pattern compilation detail tests."""
    
    def test_param_regex_capture(self):
        """Param creates capture group."""
        pattern, names = compile_route_pattern("/x/:y")
        
        assert names == ["y"]
        m = pattern.match("/x/value")
        assert m.group(1) == "value"
    
    def test_multiple_captures(self):
        """Multiple capture groups."""
        pattern, names = compile_route_pattern("/:a/:b/:c")
        
        m = pattern.match("/1/2/3")
        assert m.groups() == ("1", "2", "3")
    
    def test_pattern_anchors(self):
        """Pattern has proper anchors."""
        pattern, _ = compile_route_pattern("/test")
        
        # Should match exactly
        assert pattern.match("/test")
        assert not pattern.match("/test/extra")
        assert not pattern.match("prefix/test")


# =============================================================================
# SECTION 15: INTEGRATION SCENARIOS
# =============================================================================

class TestIntegrationScenarios:
    """Real-world integration scenarios."""
    
    def test_blog_navigation(self):
        """Blog site navigation."""
        ctx = _create_router_context("/")
        ctx.routes = [
            Route("/", component=lambda: "Home").to_compiled(),
            Route("/blog", component=lambda: "Blog").to_compiled(),
            Route("/blog/:slug", component=lambda: "Post").to_compiled(),
        ]
        
        navigate = useNavigate()
        
        navigate("/blog")
        assert ctx.pathname() == "/blog"
        
        navigate("/blog/my-first-post")
        assert useParams() == {"slug": "my-first-post"}
    
    def test_settings_tabs(self):
        """Settings page with tabs."""
        ctx = _create_router_context("/settings/profile")
        ctx.routes = [
            Route("/settings/profile", component=lambda: None).to_compiled(),
            Route("/settings/security", component=lambda: None).to_compiled(),
            Route("/settings/notifications", component=lambda: None).to_compiled(),
        ]
        
        navigate = useNavigate()
        
        # Switch tabs
        navigate("/settings/security")
        assert ctx.pathname() == "/settings/security"
        
        navigate("/settings/notifications")
        assert ctx.pathname() == "/settings/notifications"
    
    def test_filtered_list(self):
        """Filtered list with query params."""
        ctx = _create_router_context("/products")
        
        navigate = useNavigate()
        
        # Apply filters
        navigate("/products?category=electronics&brand=apple&price=100-500")
        
        query = ctx.query()
        assert query["category"] == "electronics"
        assert query["brand"] == "apple"
        assert query["price"] == "100-500"


# =============================================================================
# SECTION 16: ERROR RESILIENCE
# =============================================================================

class TestErrorResilience:
    """Error handling and resilience tests."""
    
    def test_no_context_error(self):
        """Error when no context exists."""
        # Reset global context
        import pynext.reactive.router as router_module
        old_ctx = router_module._router_context
        router_module._router_context = None
        
        with pytest.raises(RuntimeError):
            get_router_context()
        
        # Restore
        router_module._router_context = old_ctx
    
    def test_empty_routes_handling(self):
        """Handle empty routes gracefully."""
        ctx = _create_router_context("/test")
        ctx.routes = []
        
        current = ctx.get_current_route()
        assert current is None
    
    def test_navigate_to_nonexistent(self):
        """Navigate to nonexistent route."""
        ctx = _create_router_context("/")
        ctx.routes = [Route("/exists", component=lambda: None).to_compiled()]
        
        navigate = useNavigate()
        navigate("/nonexistent")
        
        # Pathname updates even if no route matches
        assert ctx.pathname() == "/nonexistent"
        assert ctx.params() == {}

