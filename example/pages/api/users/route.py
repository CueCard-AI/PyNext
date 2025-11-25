"""
Users API route.

Demonstrates:
- API route handlers
- GET, POST methods
- JSONResponse
"""

from pynext import api_route, JSONResponse, get_params

# In-memory "database" for demo
USERS = [
    {"id": 1, "name": "Alice", "email": "alice@example.com"},
    {"id": 2, "name": "Bob", "email": "bob@example.com"},
    {"id": 3, "name": "Charlie", "email": "charlie@example.com"},
]


@api_route
async def GET(request):
    """Get all users."""
    return {"users": USERS, "total": len(USERS)}


@api_route
async def POST(request):
    """Create a new user."""
    data = await request.json()
    
    # Validate
    if not data.get("name") or not data.get("email"):
        return JSONResponse(
            {"error": "Name and email are required"},
            status_code=400
        )
    
    # Create user
    new_user = {
        "id": max(u["id"] for u in USERS) + 1 if USERS else 1,
        "name": data["name"],
        "email": data["email"],
    }
    USERS.append(new_user)
    
    return JSONResponse(
        {"user": new_user, "message": "User created"},
        status_code=201
    )

