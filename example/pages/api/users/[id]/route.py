"""
Single user API route.

Demonstrates:
- Dynamic API routes with params
- GET, PUT, DELETE methods
"""

from pynext import api_route, JSONResponse, get_params

# Import shared users list
from ..route import USERS


@api_route
async def GET(request):
    """Get a single user by ID."""
    params = get_params()
    user_id = int(params.get("id", 0))
    
    user = next((u for u in USERS if u["id"] == user_id), None)
    
    if not user:
        return JSONResponse({"error": "User not found"}, status_code=404)
    
    return {"user": user}


@api_route
async def PUT(request):
    """Update a user."""
    params = get_params()
    user_id = int(params.get("id", 0))
    
    user = next((u for u in USERS if u["id"] == user_id), None)
    
    if not user:
        return JSONResponse({"error": "User not found"}, status_code=404)
    
    data = await request.json()
    
    if "name" in data:
        user["name"] = data["name"]
    if "email" in data:
        user["email"] = data["email"]
    
    return {"user": user, "message": "User updated"}


@api_route
async def DELETE(request):
    """Delete a user."""
    params = get_params()
    user_id = int(params.get("id", 0))
    
    global USERS
    user = next((u for u in USERS if u["id"] == user_id), None)
    
    if not user:
        return JSONResponse({"error": "User not found"}, status_code=404)
    
    USERS = [u for u in USERS if u["id"] != user_id]
    
    return {"message": "User deleted", "id": user_id}

