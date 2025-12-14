"""
Final batch of router tests to reach 600 total.
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
# SECTION 1: MORE PATTERN TESTS
# =============================================================================

class TestMorePatterns:
    """More pattern tests."""
    
    def test_pattern_with_numbers(self):
        """Pattern with numbers in path."""
        route = Route("/v1/api/users", component=lambda: None)
        assert route.match("/v1/api/users") == {}
    
    def test_pattern_version_param(self):
        """Version as parameter."""
        route = Route("/:version/api", component=lambda: None)
        assert route.match("/v2/api") == {"version": "v2"}
    
    def test_pattern_date_like(self):
        """Date-like path segments."""
        route = Route("/archive/:year/:month/:day", component=lambda: None)
        assert route.match("/archive/2024/06/15") == {"year": "2024", "month": "06", "day": "15"}
    
    def test_pattern_uuid(self):
        """UUID-like param."""
        route = Route("/items/:uuid", component=lambda: None)
        assert route.match("/items/123e4567-e89b-12d3-a456-426614174000") == {
            "uuid": "123e4567-e89b-12d3-a456-426614174000"
        }
    
    def test_pattern_base64_like(self):
        """Base64-like param."""
        route = Route("/decode/:data", component=lambda: None)
        assert route.match("/decode/SGVsbG8gV29ybGQ=") == {"data": "SGVsbG8gV29ybGQ="}
    
    def test_pattern_email_like(self):
        """Email-like segment."""
        route = Route("/users/by-email/:email", component=lambda: None)
        # Note: @ is allowed in path segments
        assert route.match("/users/by-email/test@example.com") == {"email": "test@example.com"}
    
    def test_pattern_phone_like(self):
        """Phone-like segment."""
        route = Route("/call/:phone", component=lambda: None)
        assert route.match("/call/+1-555-123-4567") == {"phone": "+1-555-123-4567"}


# =============================================================================
# SECTION 2: MORE LINK TESTS
# =============================================================================

class TestMoreLinkTests:
    """More Link tests."""
    
    def test_link_with_target(self):
        """Link with target attribute."""
        link = Link(href="/", target="_blank")["External"]
        result = str(link)
        assert 'target="_blank"' in result
    
    def test_link_with_rel(self):
        """Link with rel attribute."""
        link = Link(href="/", rel="noopener")["Safe"]
        result = str(link)
        assert 'rel="noopener"' in result
    
    def test_link_with_download(self):
        """Link with download attribute."""
        link = Link(href="/file.pdf", download="report.pdf")["Download"]
        result = str(link)
        # download attribute should be present
        assert "download" in result
    
    def test_link_disabled_pattern(self):
        """Disabled link pattern."""
        link = Link(href="/", **{"aria-disabled": "true"})["Disabled"]
        result = str(link)
        assert "aria-disabled" in result
    
    def test_link_with_data_attrs(self):
        """Link with custom data attributes."""
        link = Link(href="/", **{"data-testid": "home-link", "data-analytics": "nav"})["Home"]
        result = str(link)
        assert "data-testid" in result
    
    def test_link_nested_elements(self):
        """Link with nested string content."""
        link = Link(href="/")[
            "Click ",
            "here",
        ]
        result = str(link)
        assert "Click" in result
        assert "here" in result


# =============================================================================
# SECTION 3: MORE ROUTER TESTS
# =============================================================================

class TestMoreRouterTests:
    """More Router tests."""
    
    def test_router_many_routes(self):
        """Router with many routes."""
        routes = [Route(f"/path{i}", component=lambda: f"Page{i}") for i in range(20)]
        
        router = Router()
        router.routes = routes
        
        assert len(router.routes) == 20
    
    def test_router_mixed_routes(self):
        """Router with mixed static and dynamic."""
        router = Router()[
            Route("/", component=lambda: "Home"),
            Route("/about", component=lambda: "About"),
            Route("/users/:id", component=lambda: "User"),
            Route("/products/:category/:id", component=lambda: "Product"),
        ]
        
        assert len(router.routes) == 4
    
    def test_router_route_matching_priority(self):
        """Router respects route order for priority."""
        router = Router()[
            Route("/users/me", component=lambda: "Me"),
            Route("/users/:id", component=lambda: "User"),
        ]
        
        matched, params = router._find_matching_route("/users/me")
        assert params == {}  # Static match, no params
    
    def test_router_no_fallback(self):
        """Router without fallback."""
        router = Router()
        assert router.fallback is None
    
    def test_router_with_fallback(self):
        """Router with custom fallback."""
        def Custom404():
            return "Not found"
        
        router = Router(fallback=Custom404)
        assert router.fallback == Custom404


# =============================================================================
# SECTION 4: MORE NAVIGATION TESTS
# =============================================================================

class TestMoreNavigationTests:
    """More navigation tests."""
    
    def test_navigate_different_paths(self):
        """Navigate to various path types."""
        ctx = _create_router_context("/")
        navigate = useNavigate()
        
        paths = ["/a", "/b/c", "/d/e/f", "/g-h", "/i_j", "/k.l"]
        
        for path in paths:
            navigate(path)
            assert ctx.pathname() == path
    
    def test_navigate_preserves_context(self):
        """Navigation preserves context reference."""
        ctx = _create_router_context("/")
        
        navigate1 = useNavigate()
        navigate2 = useNavigate()
        
        navigate1("/page1")
        navigate2("/page2")
        
        assert ctx.pathname() == "/page2"
    
    def test_navigator_back_forward(self):
        """Navigator back/forward methods."""
        ctx = _create_router_context("/")
        nav = Navigator()
        
        # These shouldn't crash
        nav.back()
        nav.forward()
    
    def test_navigate_replace_preserves_state(self):
        """Replace mode navigation."""
        ctx = _create_router_context("/old")
        navigate = useNavigate()
        
        navigate("/new", replace=True)
        assert ctx.pathname() == "/new"


# =============================================================================
# SECTION 5: MORE PARAMS TESTS
# =============================================================================

class TestMoreParamsTests:
    """More params tests."""
    
    def test_params_complex_values(self):
        """Params with complex values."""
        ctx = _create_router_context("/")
        ctx.params.set({
            "slug": "my-awesome-post-title-2024",
            "version": "v1.2.3",
            "locale": "en-US",
        })
        
        params = useParams()
        assert params["slug"] == "my-awesome-post-title-2024"
        assert params["version"] == "v1.2.3"
        assert params["locale"] == "en-US"
    
    def test_params_numeric_string(self):
        """Numeric string params."""
        ctx = _create_router_context("/")
        ctx.params.set({"id": "12345", "page": "1"})
        
        params = useParams()
        assert params["id"] == "12345"
        assert int(params["page"]) == 1
    
    def test_params_update_clears_old(self):
        """Params update clears old values."""
        ctx = _create_router_context("/")
        ctx.params.set({"old": "value"})
        
        ctx.params.set({"new": "value"})
        
        params = useParams()
        assert "old" not in params
        assert params["new"] == "value"


# =============================================================================
# SECTION 6: MORE QUERY TESTS
# =============================================================================

class TestMoreQueryTests:
    """More query tests."""
    
    def test_query_boolean_style(self):
        """Boolean-style query params."""
        ctx = _create_router_context("/")
        ctx.query.set({"debug": "true", "verbose": "false"})
        
        params, _ = useSearchParams()
        assert params["debug"] == "true"
        assert params["verbose"] == "false"
    
    def test_query_array_style(self):
        """Array-style query params."""
        ctx = _create_router_context("/")
        ctx.query.set({"ids": "1,2,3,4,5"})
        
        params, _ = useSearchParams()
        assert params["ids"] == "1,2,3,4,5"
    
    def test_query_complex_filter(self):
        """Complex filter query."""
        ctx = _create_router_context("/")
        ctx.query.set({
            "status": "active",
            "type": "premium",
            "sort": "created_at",
            "order": "desc",
            "page": "1",
            "limit": "20",
        })
        
        params, _ = useSearchParams()
        assert len(params) == 6


# =============================================================================
# SECTION 7: MORE LOCATION TESTS
# =============================================================================

class TestMoreLocationTests:
    """More location tests."""
    
    def test_location_complex(self):
        """Complex location state."""
        ctx = _create_router_context("/page/sub")
        ctx.query.set({"a": "1", "b": "2"})
        ctx.hash_.set("sec")
        
        location = useLocation()
        
        assert location.pathname == "/page/sub"
        assert "a=1" in location.search
        assert location.hash == "#sec"
    
    def test_location_state_default(self):
        """Location state defaults to None."""
        location = Location(pathname="/", search="", hash="")
        assert location.state is None
    
    def test_location_with_state(self):
        """Location with custom state."""
        location = Location(
            pathname="/",
            search="",
            hash="",
            state={"from": "/login"}
        )
        assert location.state["from"] == "/login"


# =============================================================================
# SECTION 8: MORE MATCH TESTS
# =============================================================================

class TestMoreMatchTests:
    """More match tests."""
    
    def test_match_static_paths(self):
        """Match various static paths."""
        ctx = _create_router_context("/about")
        
        assert useMatch("/about") == {}
        assert useMatch("/contact") is None
        assert useMatch("/about-us") is None
    
    def test_match_dynamic_extraction(self):
        """Match extracts dynamic params."""
        ctx = _create_router_context("/users/abc-123/posts/xyz-789")
        
        result = useMatch("/users/:userId/posts/:postId")
        assert result == {"userId": "abc-123", "postId": "xyz-789"}
    
    def test_match_partial_pattern(self):
        """Match doesn't match partial."""
        ctx = _create_router_context("/users/123/extra")
        
        # Should not match because of extra segment
        assert useMatch("/users/:id") is None


# =============================================================================
# SECTION 9: MORE GUARD TESTS
# =============================================================================

class TestMoreGuardTests:
    """More guard tests."""
    
    def test_guard_with_redirect_query(self):
        """Guard redirect with query string."""
        def guard():
            return Redirect(to="/login?returnUrl=/dashboard")
        
        result = createRouteGuard(guard)()
        assert "returnUrl" in result.to
    
    def test_guard_conditional(self):
        """Conditional guard based on state."""
        state = {"role": "user"}
        
        def admin_guard():
            if state["role"] != "admin":
                return Redirect("/unauthorized")
            return None
        
        guard = createRouteGuard(admin_guard)
        
        assert isinstance(guard(), Redirect)
        
        state["role"] = "admin"
        assert guard() is None
    
    def test_guard_chain_with_pass(self):
        """Guard chain all pass."""
        results = []
        
        guards = [
            createRouteGuard(lambda: (results.append(1), None)[1]),
            createRouteGuard(lambda: (results.append(2), None)[1]),
            createRouteGuard(lambda: (results.append(3), None)[1]),
        ]
        
        for g in guards:
            if g() is not None:
                break
        
        assert results == [1, 2, 3]


# =============================================================================
# SECTION 10: MORE COMPILED ROUTE TESTS
# =============================================================================

class TestMoreCompiledRouteTests:
    """More compiled route tests."""
    
    def test_compiled_preserves_all(self):
        """Compiled route preserves all properties."""
        guard = lambda: None
        route = Route(
            "/users/:id",
            component=lambda: "User",
            exact=False,
            guards=[guard],
        )
        
        compiled = route.to_compiled()
        
        assert compiled.path == "/users/:id"
        assert compiled.exact is False
        assert len(compiled.guards) == 1
    
    def test_compiled_match_returns_correct(self):
        """Compiled match returns correct params."""
        route = Route("/a/:a/b/:b", component=lambda: None).to_compiled()
        
        params = route.match("/a/1/b/2")
        assert params == {"a": "1", "b": "2"}


# =============================================================================
# SECTION 11: MORE OUTLET TESTS
# =============================================================================

class TestMoreOutletTests:
    """More Outlet tests."""
    
    def test_outlet_attributes(self):
        """Outlet renders with attributes."""
        outlet = Outlet()
        result = str(outlet)
        
        assert 'data-pynext-outlet="true"' in result
    
    def test_outlet_is_div(self):
        """Outlet renders as div."""
        outlet = Outlet()
        result = str(outlet)
        
        assert "<div" in result


# =============================================================================
# SECTION 12: MORE REDIRECT TESTS
# =============================================================================

class TestMoreRedirectTests:
    """More Redirect tests."""
    
    def test_redirect_various_paths(self):
        """Redirect to various paths."""
        paths = ["/", "/login", "/auth/callback", "/users/123"]
        
        for path in paths:
            redirect = Redirect(to=path)
            assert redirect.to == path
    
    def test_redirect_replace_modes(self):
        """Redirect with different replace modes."""
        r1 = Redirect(to="/", replace=True)
        r2 = Redirect(to="/", replace=False)
        
        assert r1.replace is True
        assert r2.replace is False


# =============================================================================
# SECTION 13: EDGE CASE COMPLETENESS
# =============================================================================

class TestEdgeCaseCompleteness:
    """Complete edge case coverage."""
    
    def test_very_deep_nesting(self):
        """Very deeply nested path."""
        segments = "/".join([f"seg{i}" for i in range(20)])
        path = f"/{segments}"
        
        route = Route(path, component=lambda: None)
        assert route.match(path) == {}
    
    def test_many_query_params(self):
        """Many query parameters."""
        ctx = _create_router_context("/")
        
        params = {f"param{i}": f"value{i}" for i in range(30)}
        ctx.query.set(params)
        
        result, _ = useSearchParams()
        assert len(result) == 30
    
    def test_long_param_name(self):
        """Long parameter name."""
        long_name = "veryLongParameterNameThatMightBreakThings"
        route = Route(f"/:{long_name}", component=lambda: None)
        
        assert route.match("/value") == {long_name: "value"}
    
    def test_special_param_values(self):
        """Special characters in param values."""
        ctx = _create_router_context("/")
        ctx.params.set({
            "file": "document-v2.0.pdf",
            "query": "hello+world",
            "encoded": "test%20value",
        })
        
        params = useParams()
        assert params["file"] == "document-v2.0.pdf"


# =============================================================================
# SECTION 14: INTEGRATION COMPLETENESS
# =============================================================================

class TestIntegrationCompleteness:
    """Complete integration coverage."""
    
    def test_full_navigation_cycle(self):
        """Full navigation cycle."""
        ctx = _create_router_context("/")
        ctx.routes = [
            Route("/", component=lambda: "Home").to_compiled(),
            Route("/page", component=lambda: "Page").to_compiled(),
        ]
        
        navigate = useNavigate()
        
        # Forward
        navigate("/page")
        assert ctx.pathname() == "/page"
        
        # With query
        navigate("/page?q=test")
        assert ctx.query()["q"] == "test"
        
        # With hash
        navigate("/page#section")
        assert ctx.hash_() == "section"
        
        # Back to home
        navigate("/")
        assert ctx.pathname() == "/"
    
    def test_dynamic_routing_cycle(self):
        """Dynamic routing cycle."""
        ctx = _create_router_context("/")
        ctx.routes = [
            Route("/items/:id", component=lambda: None).to_compiled(),
        ]
        
        navigate = useNavigate()
        
        for i in range(10):
            navigate(f"/items/{i}")
            assert useParams() == {"id": str(i)}

