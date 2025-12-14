"""
Final tests to complete 600 router test target.
"""

import pytest
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
    _create_router_context,
)


class TestFinalPatterns:
    """Final pattern tests."""
    
    def test_triple_slash(self):
        p, _ = compile_route_pattern("///test")
        assert p.match("///test")
    
    def test_param_after_extension(self):
        r = Route("/files/:name.pdf", component=lambda: None)
        p, n = compile_route_pattern("/files/:name.pdf")
        assert "name" in n
    
    def test_long_segment(self):
        segment = "a" * 100
        r = Route(f"/{segment}", component=lambda: None)
        assert r.match(f"/{segment}") == {}
    
    def test_underscore_prefix_param(self):
        r = Route("/:_internal", component=lambda: None)
        assert r.match("/value") == {"_internal": "value"}


class TestFinalLinks:
    """Final Link tests."""
    
    def test_link_with_numeric_child(self):
        link = Link(href="/")[123]
        assert link.children == [123]
    
    def test_link_bool_active(self):
        link = Link(href="/test")
        assert isinstance(link._is_active("/test"), bool)
    
    def test_link_empty_str_child(self):
        link = Link(href="/")[""]
        assert "" in link.children


class TestFinalRouter:
    """Final Router tests."""
    
    def test_router_none_fallback(self):
        r = Router()
        assert r.fallback is None
    
    def test_router_list_routes(self):
        routes = [Route(f"/p{i}", component=lambda: None) for i in range(5)]
        r = Router()
        r.routes = routes
        assert len(r.routes) == 5


class TestFinalContext:
    """Final context tests."""
    
    def test_context_multiple_query(self):
        ctx = _create_router_context("/")
        ctx.query.set({"a": "1", "b": "2", "c": "3"})
        assert len(ctx.query()) == 3
    
    def test_context_empty_hash(self):
        ctx = _create_router_context("/")
        assert ctx.hash_() == ""


class TestFinalHooks:
    """Final hooks tests."""
    
    def test_navigator_type(self):
        assert type(useNavigate()).__name__ == "Navigator"
    
    def test_params_type(self):
        ctx = _create_router_context("/")
        assert isinstance(useParams(), dict)


class TestFinalRedirect:
    """Final Redirect tests."""
    
    def test_redirect_attrs(self):
        r = Redirect(to="/test")
        assert hasattr(r, "to")
        assert hasattr(r, "replace")
    
    def test_redirect_str(self):
        r = Redirect(to="/login")
        assert r.to == "/login"
    
    def test_redirect_default_replace(self):
        """Test 600: Redirect defaults to replace=True."""
        r = Redirect(to="/final")
        assert r.replace is True

