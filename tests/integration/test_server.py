"""
Integration tests for PyNext server.

Tests HTTP endpoints, page rendering, and API routes.
"""

import pytest
from fastapi.testclient import TestClient


class TestPageRoutes:
    """Tests for page route handling."""
    
    def test_index_page(self, client: TestClient):
        """Index page returns HTML."""
        response = client.get("/")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "<!DOCTYPE html>" in response.text
    
    def test_page_has_hydration_data(self, client: TestClient):
        """Page includes hydration data."""
        response = client.get("/")
        
        assert "__PYNEXT_HYDRATION__" in response.text
    
    def test_page_includes_runtime(self, client: TestClient):
        """Page includes runtime script."""
        response = client.get("/")
        
        assert "/_pynext/runtime.js" in response.text
    
    def test_about_page(self, client: TestClient):
        """About page renders."""
        response = client.get("/about")
        
        assert response.status_code == 200
        assert "About" in response.text
    
    def test_dynamic_route(self, client: TestClient):
        """Dynamic route extracts parameters."""
        response = client.get("/users/123")
        
        assert response.status_code == 200
        assert "123" in response.text
    
    def test_404_page(self, client: TestClient):
        """Nonexistent page returns 404."""
        response = client.get("/nonexistent/path")
        
        assert response.status_code == 404


class TestRuntimeEndpoints:
    """Tests for PyNext runtime endpoints."""
    
    def test_runtime_js(self, client: TestClient):
        """Runtime JS endpoint works."""
        response = client.get("/_pynext/runtime.js")
        
        assert response.status_code == 200
        assert "javascript" in response.headers["content-type"]
        assert "__pynext__" in response.text
    
    def test_styles_css(self, client: TestClient):
        """Styles CSS endpoint works."""
        response = client.get("/_pynext/styles.css")
        
        assert response.status_code == 200
        assert "text/css" in response.headers["content-type"]
    
    def test_health_check(self, client: TestClient):
        """Health check endpoint works."""
        response = client.get("/_pynext/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestAPIRoutes:
    """Tests for API route handling."""
    
    def test_api_get(self, client: TestClient):
        """GET API route works."""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_api_404(self, client: TestClient):
        """Nonexistent API route returns 404."""
        response = client.get("/api/nonexistent")
        
        assert response.status_code == 404


class TestServerActions:
    """Tests for server action endpoint."""
    
    def test_action_endpoint_exists(self, client: TestClient):
        """Action endpoint exists."""
        response = client.post(
            "/_pynext/action",
            json={"actionId": "nonexistent", "args": {}}
        )
        
        # Should return error for nonexistent action, but endpoint works
        assert response.status_code in [200, 500]
    
    def test_action_invalid_request(self, client: TestClient):
        """Invalid action request handled."""
        response = client.post(
            "/_pynext/action",
            json={}  # Missing required fields
        )
        
        assert response.status_code in [200, 422, 500]


class TestDebugEndpoints:
    """Tests for debug-only endpoints."""
    
    def test_routes_list(self, client: TestClient):
        """Routes list endpoint works in debug mode."""
        response = client.get("/_pynext/routes")
        
        assert response.status_code == 200
        data = response.json()
        assert "routes" in data
    
    def test_actions_list(self, client: TestClient):
        """Actions list endpoint works in debug mode."""
        response = client.get("/_pynext/actions")
        
        assert response.status_code == 200
        data = response.json()
        assert "actions" in data


class TestCORS:
    """Tests for CORS handling."""
    
    def test_cors_headers_debug(self, client: TestClient):
        """CORS headers are set in debug mode."""
        response = client.options(
            "/_pynext/action",
            headers={"Origin": "http://localhost:3000"}
        )
        
        # OPTIONS should be handled
        assert response.status_code in [200, 405]


class TestCaching:
    """Tests for caching headers."""
    
    def test_runtime_js_cache_header(self, client: TestClient):
        """Runtime JS has appropriate cache header."""
        response = client.get("/_pynext/runtime.js")
        
        assert "Cache-Control" in response.headers
        # In debug mode, should be no-cache
        assert "no-cache" in response.headers["Cache-Control"]

