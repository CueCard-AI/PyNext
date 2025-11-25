"""
Integration tests for PyNext API routes.

Tests REST endpoint creation, HTTP methods, and response handling.
"""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from pynext.server.app import create_app


class TestAPIRouteCreation:
    """Tests for API route file handling."""
    
    @pytest.fixture
    def app_with_api(self, temp_pages_dir: Path):
        """Create app with various API routes."""
        api_dir = temp_pages_dir / "api"
        api_dir.mkdir()
        
        # Simple health endpoint
        health_dir = api_dir / "health"
        health_dir.mkdir()
        (health_dir / "route.py").write_text('''
from pynext import api_route

@api_route
async def GET(request):
    return {"status": "healthy", "version": "1.0"}
''')
        
        # Users CRUD endpoint
        users_dir = api_dir / "users"
        users_dir.mkdir()
        (users_dir / "route.py").write_text('''
from pynext import api_route, JSONResponse

users_db = [
    {"id": 1, "name": "Alice", "email": "alice@example.com"},
    {"id": 2, "name": "Bob", "email": "bob@example.com"},
]

@api_route
async def GET(request):
    """List all users."""
    return {"users": users_db, "total": len(users_db)}

@api_route
async def POST(request):
    """Create a new user."""
    data = await request.json()
    new_user = {
        "id": len(users_db) + 1,
        "name": data.get("name"),
        "email": data.get("email"),
    }
    users_db.append(new_user)
    return JSONResponse({"user": new_user}, status_code=201)
''')
        
        # Dynamic user endpoint
        user_id_dir = users_dir / "[id]"
        user_id_dir.mkdir()
        (user_id_dir / "route.py").write_text('''
from pynext import api_route, JSONResponse
from pynext.router import get_params

@api_route
async def GET(request):
    """Get a specific user."""
    params = get_params()
    user_id = int(params.get("id", 0))
    
    # Mock user lookup
    if user_id == 1:
        return {"user": {"id": 1, "name": "Alice"}}
    elif user_id == 2:
        return {"user": {"id": 2, "name": "Bob"}}
    
    return JSONResponse({"error": "User not found"}, status_code=404)

@api_route
async def PUT(request):
    """Update a user."""
    params = get_params()
    user_id = int(params.get("id", 0))
    data = await request.json()
    
    return {"user": {"id": user_id, **data}}

@api_route
async def DELETE(request):
    """Delete a user."""
    params = get_params()
    user_id = int(params.get("id", 0))
    
    return JSONResponse({"deleted": user_id}, status_code=200)
''')
        
        # Index page (needed for app to work)
        (temp_pages_dir / "index.py").write_text('''
from pynext import page, div

@page
def index():
    return div()["Home"]
''')
        
        return create_app(
            pages_dir=str(temp_pages_dir),
            static_dir=str(temp_pages_dir.parent / "public"),
            debug=True,
        )
    
    @pytest.fixture
    def api_client(self, app_with_api):
        return TestClient(app_with_api.app)
    
    def test_get_health(self, api_client):
        """GET /api/health returns health status."""
        response = api_client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0"
    
    def test_get_users_list(self, api_client):
        """GET /api/users returns user list."""
        response = api_client.get("/api/users")
        
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert len(data["users"]) >= 2
    
    def test_post_create_user(self, api_client):
        """POST /api/users creates a new user."""
        response = api_client.post(
            "/api/users",
            json={"name": "Charlie", "email": "charlie@example.com"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["user"]["name"] == "Charlie"
        assert "id" in data["user"]
    
    def test_get_user_by_id(self, api_client):
        """GET /api/users/1 returns specific user."""
        response = api_client.get("/api/users/1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["id"] == 1
        assert data["user"]["name"] == "Alice"
    
    def test_get_user_not_found(self, api_client):
        """GET /api/users/999 returns 404."""
        response = api_client.get("/api/users/999")
        
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
    
    def test_put_update_user(self, api_client):
        """PUT /api/users/1 updates user."""
        response = api_client.put(
            "/api/users/1",
            json={"name": "Alice Updated", "email": "alice.new@example.com"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["id"] == 1
        assert data["user"]["name"] == "Alice Updated"
    
    def test_delete_user(self, api_client):
        """DELETE /api/users/1 deletes user."""
        response = api_client.delete("/api/users/1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["deleted"] == 1


class TestAPIRouteEdgeCases:
    """Tests for edge cases in API routes."""
    
    @pytest.fixture
    def app_edge_cases(self, temp_pages_dir: Path):
        """Create app with edge case API routes."""
        api_dir = temp_pages_dir / "api"
        api_dir.mkdir()
        
        # Endpoint that returns different content types
        echo_dir = api_dir / "echo"
        echo_dir.mkdir()
        (echo_dir / "route.py").write_text('''
from pynext import api_route
from fastapi.responses import PlainTextResponse, HTMLResponse

@api_route
async def GET(request):
    format = request.query_params.get("format", "json")
    
    if format == "text":
        return PlainTextResponse("Hello, World!")
    elif format == "html":
        return HTMLResponse("<h1>Hello</h1>")
    
    return {"message": "Hello, World!"}

@api_route
async def POST(request):
    data = await request.json()
    return {"echo": data}
''')
        
        # Endpoint with query params
        search_dir = api_dir / "search"
        search_dir.mkdir()
        (search_dir / "route.py").write_text('''
from pynext import api_route
from pynext.router import get_query

@api_route
async def GET(request):
    query = get_query()
    q = query.get("q", "")
    page = int(query.get("page", 1))
    limit = int(query.get("limit", 10))
    
    return {
        "query": q,
        "page": page,
        "limit": limit,
        "results": [f"Result {i}" for i in range(limit)]
    }
''')
        
        # Endpoint with headers
        auth_dir = api_dir / "auth"
        auth_dir.mkdir()
        (auth_dir / "route.py").write_text('''
from pynext import api_route, JSONResponse

@api_route
async def GET(request):
    auth_header = request.headers.get("authorization", "")
    
    if not auth_header.startswith("Bearer "):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    token = auth_header.replace("Bearer ", "")
    return {"authenticated": True, "token": token[:8] + "..."}
''')
        
        (temp_pages_dir / "index.py").write_text('''
from pynext import page, div

@page
def index():
    return div()["Home"]
''')
        
        return create_app(
            pages_dir=str(temp_pages_dir),
            static_dir=str(temp_pages_dir.parent / "public"),
            debug=True,
        )
    
    @pytest.fixture
    def edge_client(self, app_edge_cases):
        return TestClient(app_edge_cases.app)
    
    def test_query_params(self, edge_client):
        """Query parameters are parsed correctly."""
        response = edge_client.get("/api/search?q=test&page=2&limit=5")
        
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "test"
        assert data["page"] == 2
        assert data["limit"] == 5
    
    def test_auth_header(self, edge_client):
        """Authorization header is accessible."""
        response = edge_client.get(
            "/api/auth",
            headers={"Authorization": "Bearer secret_token_12345"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True
    
    def test_missing_auth(self, edge_client):
        """Missing auth returns 401."""
        response = edge_client.get("/api/auth")
        
        assert response.status_code == 401
    
    def test_json_content_type(self, edge_client):
        """Default response is JSON."""
        response = edge_client.get("/api/echo")
        
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]
    
    def test_text_content_type(self, edge_client):
        """Text response when requested."""
        response = edge_client.get("/api/echo?format=text")
        
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]
    
    def test_html_content_type(self, edge_client):
        """HTML response when requested."""
        response = edge_client.get("/api/echo?format=html")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_post_echo(self, edge_client):
        """POST body is echoed back."""
        response = edge_client.post(
            "/api/echo",
            json={"key": "value", "nested": {"a": 1}}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["echo"]["key"] == "value"
        assert data["echo"]["nested"]["a"] == 1

