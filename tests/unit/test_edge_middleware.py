"""
Tests for PyNext Edge Middleware.
"""

import pytest
import asyncio
import re
from unittest.mock import MagicMock, AsyncMock
from starlette.requests import Request
from starlette.testclient import TestClient
from pynext.middleware.edge import (
    middleware,
    MiddlewareConfig,
    MiddlewareContext,
    MiddlewareResponse,
    MiddlewareEntry,
    NextResponse,
    MatcherType,
    get_middleware_registry,
    matches_path,
    run_middleware_chain,
)
from pynext.middleware.response import (
    redirect,
    rewrite,
    next_response,
    json_response,
    html_response,
    not_found,
    unauthorized,
    forbidden,
    bad_request,
    set_cookie,
    delete_cookie,
)
from pynext.middleware.router import (
    MiddlewareRouter,
    MiddlewareMatcher,
    compile_matcher,
)


class TestMiddlewareConfig:
    """Tests for MiddlewareConfig."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = MiddlewareConfig()
        
        assert config.matcher == "/*"
        assert config.matcher_type == MatcherType.GLOB
        assert config.priority == 0
        assert config.timeout_ms == 5000
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = MiddlewareConfig(
            matcher="/admin/*",
            priority=10,
            exclude=["/admin/public/*"],
        )
        
        assert config.matcher == "/admin/*"
        assert config.priority == 10
        assert "/admin/public/*" in config.exclude


class TestMiddlewareContext:
    """Tests for MiddlewareContext."""
    
    def test_context_from_request(self):
        """Test creating context from request."""
        # Create mock request
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "query_string": b"foo=bar",
            "headers": [
                (b"user-agent", b"Mozilla/5.0"),
                (b"accept-language", b"en-US,en;q=0.9"),
            ],
        }
        request = Request(scope)
        
        ctx = MiddlewareContext.from_request(request)
        
        assert ctx.path == "/test"
        assert ctx.method == "GET"
        assert ctx.user_agent == "Mozilla/5.0"
    
    def test_context_device_detection(self):
        """Test device type detection."""
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/",
            "query_string": b"",
            "headers": [
                (b"user-agent", b"Mozilla/5.0 (iPhone; CPU iPhone OS)"),
            ],
        }
        request = Request(scope)
        
        ctx = MiddlewareContext.from_request(request)
        
        assert ctx.is_mobile() is True
    
    def test_context_bot_detection(self):
        """Test bot detection."""
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/",
            "query_string": b"",
            "headers": [
                (b"user-agent", b"Googlebot/2.1"),
            ],
        }
        request = Request(scope)
        
        ctx = MiddlewareContext.from_request(request)
        
        assert ctx.is_bot() is True
    
    def test_context_geo_data(self):
        """Test geo data extraction."""
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/",
            "query_string": b"",
            "headers": [
                (b"cf-ipcountry", b"US"),
                (b"cf-ipcity", b"San Francisco"),
            ],
        }
        request = Request(scope)
        
        ctx = MiddlewareContext.from_request(request)
        
        assert ctx.geo is not None
        assert ctx.geo["country"] == "US"


class TestNextResponse:
    """Tests for NextResponse factory."""
    
    def test_next_response(self):
        """Test next() response."""
        response = NextResponse.next()
        
        assert response.action == "next"
    
    def test_next_with_headers(self):
        """Test next() with headers."""
        response = NextResponse.next(headers={"X-Custom": "value"})
        
        assert response.headers["X-Custom"] == "value"
    
    def test_redirect_response(self):
        """Test redirect() response."""
        response = NextResponse.redirect("/login")
        
        assert response.action == "redirect"
        assert response.url == "/login"
        assert response.status == 307
    
    def test_redirect_permanent(self):
        """Test permanent redirect."""
        response = NextResponse.redirect("/new-url", status=308)
        
        assert response.status == 308
    
    def test_rewrite_response(self):
        """Test rewrite() response."""
        response = NextResponse.rewrite("/internal/path")
        
        assert response.action == "rewrite"
        assert response.url == "/internal/path"
    
    def test_json_response(self):
        """Test json() response."""
        response = NextResponse.json({"message": "Hello"})
        
        assert response.action == "response"
        assert response.response is not None


class TestResponseHelpers:
    """Tests for response helper functions."""
    
    def test_redirect_helper(self):
        """Test redirect helper."""
        response = redirect("/login")
        
        assert response.action == "redirect"
        assert response.url == "/login"
        assert response.status == 307
    
    def test_redirect_permanent(self):
        """Test permanent redirect."""
        response = redirect("/new", permanent=True)
        
        assert response.status == 308
    
    def test_rewrite_helper(self):
        """Test rewrite helper."""
        response = rewrite("/internal")
        
        assert response.action == "rewrite"
    
    def test_next_response_helper(self):
        """Test next_response helper."""
        response = next_response(headers={"X-Test": "value"})
        
        assert response.action == "next"
        assert response.headers["X-Test"] == "value"
    
    def test_json_response_helper(self):
        """Test json_response helper."""
        response = json_response({"data": "test"}, status=201)
        
        assert response.action == "response"
    
    def test_html_response_helper(self):
        """Test html_response helper."""
        response = html_response("<h1>Hello</h1>")
        
        assert response.action == "response"
    
    def test_error_helpers(self):
        """Test error response helpers."""
        assert not_found().response.status_code == 404
        assert unauthorized().response.status_code == 401
        assert forbidden().response.status_code == 403
        assert bad_request().response.status_code == 400
    
    def test_set_cookie_helper(self):
        """Test set_cookie helper."""
        cookie = set_cookie("session", "abc123", max_age=3600)
        
        assert cookie["value"] == "abc123"
        assert cookie["max_age"] == 3600
        assert cookie["httponly"] is True
    
    def test_delete_cookie_helper(self):
        """Test delete_cookie helper."""
        cookie = delete_cookie("session")
        
        assert cookie["value"] == ""
        assert cookie["max_age"] == 0


class TestMatcherCompilation:
    """Tests for matcher compilation."""
    
    def test_exact_matcher(self):
        """Test exact path matcher."""
        pattern = compile_matcher("/about", MatcherType.EXACT)
        
        assert pattern.match("/about") is not None
        assert pattern.match("/about/team") is None
    
    def test_prefix_matcher(self):
        """Test prefix matcher."""
        pattern = compile_matcher("/admin", MatcherType.PREFIX)
        
        assert pattern.match("/admin") is not None
        assert pattern.match("/admin/users") is not None
        assert pattern.match("/public") is None
    
    def test_glob_matcher_single_star(self):
        """Test glob matcher with single star."""
        pattern = compile_matcher("/api/*", MatcherType.GLOB)
        
        assert pattern.match("/api/users") is not None
        assert pattern.match("/api/products") is not None
        assert pattern.match("/api/users/1") is None  # * doesn't match /
    
    def test_glob_matcher_double_star(self):
        """Test glob matcher with double star."""
        pattern = compile_matcher("/api/**", MatcherType.GLOB)
        
        assert pattern.match("/api/users") is not None
        assert pattern.match("/api/users/1/profile") is not None
    
    def test_regex_matcher(self):
        """Test regex matcher."""
        pattern = compile_matcher(r"/user/\d+", MatcherType.REGEX)
        
        assert pattern.match("/user/123") is not None
        assert pattern.match("/user/abc") is None


class TestMiddlewareRouter:
    """Tests for MiddlewareRouter."""
    
    def test_router_creation(self):
        """Test router creation."""
        router = MiddlewareRouter()
        
        assert router._matchers == []
        assert router._path_cache == {}
    
    def test_get_stats(self):
        """Test router statistics."""
        router = MiddlewareRouter()
        
        stats = router.get_stats()
        
        assert "matchers" in stats
        assert "cached_paths" in stats
    
    def test_cache_clearing(self):
        """Test cache clearing."""
        router = MiddlewareRouter()
        router._path_cache["/test"] = ["middleware1"]
        
        router.clear_cache()
        
        assert router._path_cache == {}


class TestMiddlewareDecorator:
    """Tests for @middleware decorator."""
    
    def test_basic_decorator(self):
        """Test basic middleware decorator."""
        @middleware()
        async def test_middleware(ctx: MiddlewareContext):
            return NextResponse.next()
        
        assert hasattr(test_middleware, '_is_middleware')
        assert test_middleware._is_middleware is True
    
    def test_decorator_with_config(self):
        """Test decorator with custom config."""
        @middleware(MiddlewareConfig(matcher="/admin/*", priority=10))
        async def admin_middleware(ctx: MiddlewareContext):
            return NextResponse.next()
        
        config = admin_middleware._middleware_config
        assert config.matcher == "/admin/*"
        assert config.priority == 10
    
    def test_middleware_registration(self):
        """Test middleware is registered."""
        @middleware()
        async def registered_middleware(ctx: MiddlewareContext):
            return NextResponse.next()
        
        registry = get_middleware_registry()
        assert "registered_middleware" in registry


class TestMiddlewareMatching:
    """Tests for middleware path matching."""
    
    def test_matches_path_include(self):
        """Test path matching with include pattern."""
        async def dummy(ctx):
            return NextResponse.next()
        
        # Use config without /api/* in exclude list
        entry = MiddlewareEntry(
            func=dummy,
            config=MiddlewareConfig(matcher="/api/*", exclude=["/_next/*", "/static/*"]),
            compiled_matcher=compile_matcher("/api/*", MatcherType.GLOB),
        )
        
        assert matches_path(entry, "/api/users") is True
        assert matches_path(entry, "/public") is False
    
    def test_matches_path_exclude(self):
        """Test path matching with exclusions."""
        async def dummy(ctx):
            return NextResponse.next()
        
        entry = MiddlewareEntry(
            func=dummy,
            config=MiddlewareConfig(
                matcher="/*",
                exclude=["/_next/*", "/static/*"],
            ),
            compiled_matcher=compile_matcher("/*", MatcherType.GLOB),
        )
        
        assert matches_path(entry, "/page") is True
        assert matches_path(entry, "/_next/static/chunk.js") is False
        assert matches_path(entry, "/static/image.png") is False


class TestMiddlewareChain:
    """Tests for middleware chain execution."""
    
    @pytest.mark.asyncio
    async def test_chain_continues_on_next(self):
        """Test chain continues when middleware returns next()."""
        call_order = []
        
        async def first(ctx):
            call_order.append("first")
            return NextResponse.next()
        
        async def second(ctx):
            call_order.append("second")
            return NextResponse.next()
        
        entries = [
            MiddlewareEntry(
                func=first,
                config=MiddlewareConfig(priority=2),
                compiled_matcher=compile_matcher("/*", MatcherType.GLOB),
            ),
            MiddlewareEntry(
                func=second,
                config=MiddlewareConfig(priority=1),
                compiled_matcher=compile_matcher("/*", MatcherType.GLOB),
            ),
        ]
        
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "query_string": b"",
            "headers": [],
        }
        request = Request(scope)
        
        result = await run_middleware_chain(request, entries)
        
        # Chain completed, all middleware ran
        assert result is None
        # Higher priority runs first
        assert call_order == ["first", "second"]
    
    @pytest.mark.asyncio
    async def test_chain_stops_on_redirect(self):
        """Test chain stops when middleware returns redirect."""
        async def auth_check(ctx):
            return NextResponse.redirect("/login")
        
        async def should_not_run(ctx):
            raise AssertionError("Should not run")
        
        entries = [
            MiddlewareEntry(
                func=auth_check,
                config=MiddlewareConfig(priority=2),
                compiled_matcher=compile_matcher("/*", MatcherType.GLOB),
            ),
            MiddlewareEntry(
                func=should_not_run,
                config=MiddlewareConfig(priority=1),
                compiled_matcher=compile_matcher("/*", MatcherType.GLOB),
            ),
        ]
        
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/protected",
            "query_string": b"",
            "headers": [],
        }
        request = Request(scope)
        
        result = await run_middleware_chain(request, entries)
        
        assert result is not None
        assert result.action == "redirect"
        assert result.url == "/login"

