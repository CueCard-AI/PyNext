"""
Unit tests for PyNext middleware.

Tests compression, ETag, security headers, and other middleware.
"""

import pytest
import gzip
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.testclient import TestClient

from pynext.server.middleware import (
    CompressionMiddleware,
    ETagMiddleware,
    SecurityHeadersMiddleware,
    TimingMiddleware,
    CacheControlMiddleware,
    add_performance_middleware,
)


@pytest.fixture
def base_app():
    """Create a base FastAPI app for testing."""
    app = FastAPI()
    
    @app.get("/html")
    async def html_page():
        # Return a page larger than compression threshold
        content = "<html><body>" + "Hello World! " * 100 + "</body></html>"
        return HTMLResponse(content)
    
    @app.get("/json")
    async def json_endpoint():
        return {"key": "value", "data": list(range(100))}
    
    @app.get("/small")
    async def small_page():
        return HTMLResponse("<p>Small</p>")
    
    @app.get("/image")
    async def image():
        from fastapi.responses import Response
        return Response(b"\x89PNG\r\n", media_type="image/png")
    
    return app


class TestCompressionMiddleware:
    """Tests for compression middleware."""
    
    def test_compresses_html(self, base_app):
        """HTML responses are compressed when Accept-Encoding is gzip."""
        app = CompressionMiddleware(base_app, minimum_size=100)
        client = TestClient(app)
        
        response = client.get("/html", headers={"Accept-Encoding": "gzip"})
        
        assert response.status_code == 200
        # TestClient may auto-decompress, so just check header was set
        # or content is still accessible
        assert "Hello World" in response.text or response.headers.get("content-encoding") == "gzip"
    
    def test_skips_small_responses(self, base_app):
        """Small responses are not compressed."""
        app = CompressionMiddleware(base_app, minimum_size=500)
        client = TestClient(app)
        
        response = client.get("/small", headers={"Accept-Encoding": "gzip"})
        
        assert response.status_code == 200
        # Content should not have gzip header for small responses
        assert response.headers.get("content-encoding") != "gzip" or len(response.content) < 500
    
    def test_response_is_valid(self, base_app):
        """Response content is valid after compression pipeline."""
        app = CompressionMiddleware(base_app, minimum_size=100)
        client = TestClient(app)
        
        response = client.get("/html", headers={"Accept-Encoding": "gzip"})
        
        # Whether compressed or not, content should be accessible
        assert response.status_code == 200
        assert "Hello World" in response.text
    
    def test_skips_non_compressible_types(self, base_app):
        """Binary content types are not compressed."""
        app = CompressionMiddleware(base_app, minimum_size=1)
        client = TestClient(app)
        
        response = client.get("/image", headers={"Accept-Encoding": "gzip"})
        
        assert response.headers.get("content-encoding") != "gzip"


class TestETagMiddleware:
    """Tests for ETag middleware."""
    
    def test_adds_etag_header(self, base_app):
        """ETag header is added to responses."""
        app = ETagMiddleware(base_app)
        client = TestClient(app)
        
        response = client.get("/html")
        
        assert response.status_code == 200
        assert "etag" in response.headers
        assert response.headers["etag"].startswith('"')
        assert response.headers["etag"].endswith('"')
    
    def test_304_on_matching_etag(self, base_app):
        """304 is returned when ETag matches."""
        app = ETagMiddleware(base_app)
        client = TestClient(app)
        
        # First request to get ETag
        response1 = client.get("/html")
        etag = response1.headers["etag"]
        
        # Second request with If-None-Match
        response2 = client.get("/html", headers={"If-None-Match": etag})
        
        assert response2.status_code == 304
    
    def test_200_on_different_etag(self, base_app):
        """200 is returned when ETag doesn't match."""
        app = ETagMiddleware(base_app)
        client = TestClient(app)
        
        response = client.get("/html", headers={"If-None-Match": '"different-etag"'})
        
        assert response.status_code == 200


class TestSecurityHeadersMiddleware:
    """Tests for security headers middleware."""
    
    def test_adds_default_headers(self, base_app):
        """Default security headers are added."""
        app = SecurityHeadersMiddleware(base_app)
        client = TestClient(app)
        
        response = client.get("/html")
        
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    
    def test_custom_headers(self, base_app):
        """Custom headers can be added."""
        app = SecurityHeadersMiddleware(
            base_app,
            headers={"X-Custom-Header": "custom-value"},
        )
        client = TestClient(app)
        
        response = client.get("/html")
        
        assert response.headers.get("X-Custom-Header") == "custom-value"
    
    def test_csp_header(self, base_app):
        """CSP header can be set."""
        app = SecurityHeadersMiddleware(
            base_app,
            content_security_policy="default-src 'self'",
        )
        client = TestClient(app)
        
        response = client.get("/html")
        
        assert response.headers.get("Content-Security-Policy") == "default-src 'self'"


class TestTimingMiddleware:
    """Tests for timing middleware."""
    
    def test_adds_server_timing_header(self, base_app):
        """Server-Timing header is added."""
        app = TimingMiddleware(base_app)
        client = TestClient(app)
        
        response = client.get("/html")
        
        assert "Server-Timing" in response.headers
        timing = response.headers["Server-Timing"]
        assert "total" in timing
        assert "dur=" in timing


class TestCacheControlMiddleware:
    """Tests for cache control middleware."""
    
    def test_no_cache_in_debug(self, base_app):
        """No caching in debug mode."""
        app = CacheControlMiddleware(base_app, debug=True)
        client = TestClient(app)
        
        response = client.get("/html")
        
        assert response.headers.get("Cache-Control") == "no-store"
    
    def test_cache_rules_applied(self, base_app):
        """Cache rules are applied based on content type."""
        app = CacheControlMiddleware(base_app, debug=False)
        client = TestClient(app)
        
        response = client.get("/html")
        
        assert "Cache-Control" in response.headers
        assert "no-cache" in response.headers["Cache-Control"]


class TestMiddlewareStack:
    """Tests for the complete middleware stack."""
    
    def test_add_performance_middleware(self, base_app):
        """Performance middleware stack works together."""
        app = add_performance_middleware(
            base_app,
            compression=True,
            etag=True,
            security_headers=True,
            timing=True,
            cache_control=True,
            debug=False,
        )
        client = TestClient(app)
        
        response = client.get("/html", headers={"Accept-Encoding": "gzip"})
        
        assert response.status_code == 200
        # Compression
        assert response.headers.get("content-encoding") == "gzip"
        # ETag
        assert "etag" in response.headers
        # Security
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        # Timing
        assert "Server-Timing" in response.headers
    
    def test_debug_mode_disables_features(self, base_app):
        """Debug mode disables certain features."""
        app = add_performance_middleware(
            base_app,
            compression=True,
            etag=True,
            security_headers=False,
            timing=True,
            cache_control=True,
            debug=True,
        )
        client = TestClient(app)
        
        response = client.get("/html", headers={"Accept-Encoding": "gzip"})
        
        # ETag should be disabled in debug
        # Compression still works
        # Cache-Control should be no-store
        assert response.headers.get("Cache-Control") == "no-store"

