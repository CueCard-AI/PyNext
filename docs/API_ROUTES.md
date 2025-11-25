# API Routes in PyNext

PyNext provides Next.js-style API routes for building REST endpoints. Create `route.py` files in the `pages/api/` directory to define HTTP handlers.

## Table of Contents

- [Overview](#overview)
- [Creating API Routes](#creating-api-routes)
- [HTTP Methods](#http-methods)
- [Request and Response](#request-and-response)
- [Dynamic Routes](#dynamic-routes)
- [Error Handling](#error-handling)
- [Middleware Patterns](#middleware-patterns)
- [Examples](#examples)
- [Best Practices](#best-practices)

---

## Overview

### How It Works

```
pages/
└── api/
    ├── health/
    │   └── route.py      # GET /api/health
    ├── users/
    │   ├── route.py      # GET, POST /api/users
    │   └── [id]/
    │       └── route.py  # GET, PUT, DELETE /api/users/:id
    └── posts/
        └── route.py      # /api/posts
```

Each `route.py` file exports handler functions named after HTTP methods:
- `GET` - Read operations
- `POST` - Create operations
- `PUT` - Update operations (full)
- `PATCH` - Update operations (partial)
- `DELETE` - Delete operations
- `HEAD` - Headers only
- `OPTIONS` - CORS preflight

### Key Concepts

| Concept | Description |
|---------|-------------|
| **Route File** | `route.py` in any `pages/api/` subdirectory |
| **Handler** | Function named after HTTP method (GET, POST, etc.) |
| **Request** | FastAPI Request object with body, params, headers |
| **Response** | Return dict, JSONResponse, or Response |

---

## Creating API Routes

### Basic Route

```python
# pages/api/hello/route.py

from pynext import api_route

@api_route
async def GET(request):
    """Handle GET /api/hello"""
    return {"message": "Hello, World!"}
```

### Multiple Methods

```python
# pages/api/users/route.py

from pynext import api_route, JSONResponse

# In-memory storage for demo
users = []

@api_route
async def GET(request):
    """List all users."""
    return {"users": users, "total": len(users)}

@api_route
async def POST(request):
    """Create a new user."""
    data = await request.json()
    
    user = {
        "id": len(users) + 1,
        "name": data.get("name"),
        "email": data.get("email"),
    }
    users.append(user)
    
    return JSONResponse({"user": user}, status_code=201)
```

---

## HTTP Methods

### All Supported Methods

```python
# pages/api/resource/route.py

from pynext import api_route, JSONResponse

@api_route
async def GET(request):
    """Read resource(s)."""
    return {"data": [...]}

@api_route
async def POST(request):
    """Create resource."""
    data = await request.json()
    return JSONResponse({"created": data}, status_code=201)

@api_route
async def PUT(request):
    """Replace resource."""
    data = await request.json()
    return {"updated": data}

@api_route
async def PATCH(request):
    """Partially update resource."""
    data = await request.json()
    return {"patched": data}

@api_route
async def DELETE(request):
    """Delete resource."""
    return {"deleted": True}

@api_route
async def HEAD(request):
    """Return headers only (no body)."""
    from pynext import Response
    return Response(headers={"X-Total-Count": "100"})

@api_route
async def OPTIONS(request):
    """CORS preflight or capability discovery."""
    from pynext import Response
    return Response(
        headers={
            "Allow": "GET, POST, PUT, DELETE",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE",
        }
    )
```

### Method Not Allowed

If a client uses an unsupported method, PyNext returns `405 Method Not Allowed`:

```json
{
    "error": "Method PATCH not allowed"
}
```

---

## Request and Response

### Reading Request Data

```python
from pynext import api_route, get_params, get_query

@api_route
async def POST(request):
    # JSON body
    data = await request.json()
    
    # Form data
    form = await request.form()
    
    # URL path parameters (from dynamic routes)
    params = get_params()  # {"id": "123"}
    
    # Query string parameters
    query = get_query()  # {"page": "1", "limit": "10"}
    
    # Headers
    auth = request.headers.get("Authorization")
    
    # Cookies
    session = request.cookies.get("session_id")
    
    return {"received": data}
```

### Response Types

```python
from pynext import api_route, JSONResponse, Response, RedirectResponse, HTMLResponse

@api_route
async def GET(request):
    # Dict → auto-converted to JSON
    return {"status": "ok"}

@api_route
async def POST(request):
    # JSONResponse with status code
    return JSONResponse(
        {"id": 123, "created": True},
        status_code=201,
        headers={"X-Custom": "value"}
    )

@api_route
async def DELETE(request):
    # No content response
    return Response(status_code=204)

@api_route
async def GET(request):
    # Redirect
    return RedirectResponse("/api/v2/users")

@api_route
async def GET(request):
    # HTML response
    return HTMLResponse("<h1>Hello</h1>")
```

### Response Helpers

```python
from pynext import JSONResponse, Response, RedirectResponse, HTMLResponse

# JSON with options
JSONResponse(
    content={"data": [...]},
    status_code=200,
    headers={"Cache-Control": "max-age=3600"}
)

# Plain response
Response(
    content="Plain text",
    media_type="text/plain",
    status_code=200
)

# Redirect
RedirectResponse(
    url="/new-location",
    status_code=307  # Temporary redirect (preserves method)
)

# HTML
HTMLResponse(
    content="<html>...</html>",
    status_code=200
)
```

---

## Dynamic Routes

### Path Parameters

```python
# pages/api/users/[id]/route.py

from pynext import api_route, get_params, JSONResponse

@api_route
async def GET(request):
    """Get user by ID."""
    params = get_params()
    user_id = params.get("id")  # From URL: /api/users/123
    
    # Fetch user...
    user = await get_user(user_id)
    
    if not user:
        return JSONResponse({"error": "User not found"}, status_code=404)
    
    return {"user": user}

@api_route
async def DELETE(request):
    """Delete user by ID."""
    params = get_params()
    user_id = params.get("id")
    
    await delete_user(user_id)
    
    return {"deleted": True, "id": user_id}
```

### Multiple Parameters

```python
# pages/api/posts/[postId]/comments/[commentId]/route.py

from pynext import api_route, get_params

@api_route
async def GET(request):
    params = get_params()
    
    post_id = params.get("postId")
    comment_id = params.get("commentId")
    
    # /api/posts/5/comments/10
    # → {"postId": "5", "commentId": "10"}
    
    return {"post_id": post_id, "comment_id": comment_id}
```

### Catch-All Routes

```python
# pages/api/files/[...path]/route.py

from pynext import api_route, get_params

@api_route
async def GET(request):
    params = get_params()
    path = params.get("path", [])
    
    # /api/files/docs/2024/report.pdf
    # → {"path": ["docs", "2024", "report.pdf"]}
    
    file_path = "/".join(path)
    return {"file": file_path}
```

---

## Error Handling

### Returning Errors

```python
from pynext import api_route, JSONResponse

@api_route
async def GET(request):
    params = get_params()
    user_id = params.get("id")
    
    # Not found
    user = await get_user(user_id)
    if not user:
        return JSONResponse(
            {"error": "User not found", "id": user_id},
            status_code=404
        )
    
    return {"user": user}

@api_route
async def POST(request):
    try:
        data = await request.json()
    except:
        return JSONResponse(
            {"error": "Invalid JSON"},
            status_code=400
        )
    
    # Validation
    if not data.get("email"):
        return JSONResponse(
            {"error": "Email is required", "field": "email"},
            status_code=422
        )
    
    return {"created": True}
```

### Try-Catch Pattern

```python
from pynext import api_route, JSONResponse
import traceback

@api_route
async def POST(request):
    try:
        data = await request.json()
        result = await process_data(data)
        return {"result": result}
        
    except ValidationError as e:
        return JSONResponse(
            {"error": "Validation failed", "details": e.errors()},
            status_code=422
        )
        
    except DatabaseError as e:
        return JSONResponse(
            {"error": "Database error"},
            status_code=503
        )
        
    except Exception as e:
        # Log the error
        print(f"Unexpected error: {e}")
        traceback.print_exc()
        
        return JSONResponse(
            {"error": "Internal server error"},
            status_code=500
        )
```

---

## Middleware Patterns

### Authentication Wrapper

```python
from pynext import api_route, JSONResponse
from functools import wraps

def require_auth(handler):
    """Decorator to require authentication."""
    @wraps(handler)
    async def wrapper(request):
        # Check auth header
        auth = request.headers.get("Authorization")
        
        if not auth or not auth.startswith("Bearer "):
            return JSONResponse(
                {"error": "Authentication required"},
                status_code=401
            )
        
        token = auth.replace("Bearer ", "")
        user = await verify_token(token)
        
        if not user:
            return JSONResponse(
                {"error": "Invalid token"},
                status_code=401
            )
        
        # Add user to request state
        request.state.user = user
        
        return await handler(request)
    
    return wrapper

# Usage
@api_route
@require_auth
async def GET(request):
    user = request.state.user
    return {"user": user}
```

### Rate Limiting

```python
from pynext import api_route, JSONResponse
from collections import defaultdict
from datetime import datetime, timedelta

# Simple in-memory rate limiter
request_counts = defaultdict(list)
RATE_LIMIT = 100
RATE_WINDOW = 60  # seconds

def rate_limit(handler):
    @wraps(handler)
    async def wrapper(request):
        client_ip = request.client.host
        now = datetime.now()
        window_start = now - timedelta(seconds=RATE_WINDOW)
        
        # Clean old requests
        request_counts[client_ip] = [
            t for t in request_counts[client_ip]
            if t > window_start
        ]
        
        if len(request_counts[client_ip]) >= RATE_LIMIT:
            return JSONResponse(
                {"error": "Rate limit exceeded"},
                status_code=429,
                headers={"Retry-After": str(RATE_WINDOW)}
            )
        
        request_counts[client_ip].append(now)
        return await handler(request)
    
    return wrapper

@api_route
@rate_limit
async def GET(request):
    return {"data": "..."}
```

---

## Examples

### RESTful CRUD API

```python
# pages/api/products/route.py

from pynext import api_route, JSONResponse

products = []

@api_route
async def GET(request):
    """List products with pagination."""
    from pynext import get_query
    
    query = get_query()
    page = int(query.get("page", 1))
    limit = int(query.get("limit", 10))
    
    start = (page - 1) * limit
    end = start + limit
    
    return {
        "products": products[start:end],
        "total": len(products),
        "page": page,
        "pages": (len(products) + limit - 1) // limit
    }

@api_route
async def POST(request):
    """Create a product."""
    data = await request.json()
    
    product = {
        "id": len(products) + 1,
        **data
    }
    products.append(product)
    
    return JSONResponse(product, status_code=201)
```

```python
# pages/api/products/[id]/route.py

from pynext import api_route, get_params, JSONResponse

@api_route
async def GET(request):
    """Get product by ID."""
    params = get_params()
    product_id = int(params["id"])
    
    product = next((p for p in products if p["id"] == product_id), None)
    
    if not product:
        return JSONResponse({"error": "Not found"}, status_code=404)
    
    return product

@api_route
async def PUT(request):
    """Update product."""
    params = get_params()
    product_id = int(params["id"])
    data = await request.json()
    
    for i, p in enumerate(products):
        if p["id"] == product_id:
            products[i] = {"id": product_id, **data}
            return products[i]
    
    return JSONResponse({"error": "Not found"}, status_code=404)

@api_route
async def DELETE(request):
    """Delete product."""
    params = get_params()
    product_id = int(params["id"])
    
    global products
    products = [p for p in products if p["id"] != product_id]
    
    return Response(status_code=204)
```

### File Upload

```python
# pages/api/upload/route.py

from pynext import api_route, JSONResponse
from pathlib import Path
import shutil

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@api_route
async def POST(request):
    """Handle file upload."""
    form = await request.form()
    file = form.get("file")
    
    if not file:
        return JSONResponse(
            {"error": "No file provided"},
            status_code=400
        )
    
    # Save file
    file_path = UPLOAD_DIR / file.filename
    
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    return {
        "filename": file.filename,
        "size": file_path.stat().st_size,
        "path": str(file_path)
    }
```

---

## Best Practices

### 1. Use Proper Status Codes

```python
# 200 - OK (default for GET)
return {"data": [...]}

# 201 - Created (POST success)
return JSONResponse({"id": 123}, status_code=201)

# 204 - No Content (DELETE success)
return Response(status_code=204)

# 400 - Bad Request (invalid input)
return JSONResponse({"error": "Invalid data"}, status_code=400)

# 401 - Unauthorized (not authenticated)
return JSONResponse({"error": "Auth required"}, status_code=401)

# 403 - Forbidden (not authorized)
return JSONResponse({"error": "Not allowed"}, status_code=403)

# 404 - Not Found
return JSONResponse({"error": "Not found"}, status_code=404)

# 422 - Unprocessable Entity (validation failed)
return JSONResponse({"error": "Validation failed"}, status_code=422)

# 500 - Internal Server Error
return JSONResponse({"error": "Server error"}, status_code=500)
```

### 2. Validate Input

```python
from pydantic import BaseModel, EmailStr

class CreateUserRequest(BaseModel):
    name: str
    email: EmailStr

@api_route
async def POST(request):
    try:
        data = CreateUserRequest(**(await request.json()))
    except ValidationError as e:
        return JSONResponse(
            {"error": "Validation failed", "details": e.errors()},
            status_code=422
        )
    
    # data is now validated
    return {"user": {"name": data.name, "email": data.email}}
```

### 3. Keep Handlers Focused

```python
# Good: Focused handler
@api_route
async def POST(request):
    data = await request.json()
    user = await user_service.create(data)  # Business logic in service
    return JSONResponse(user.dict(), status_code=201)

# Avoid: Too much logic in handler
@api_route
async def POST(request):
    data = await request.json()
    # 50 lines of business logic...
```

### 4. Use Async for I/O

```python
# Good: Async for database/network
@api_route
async def GET(request):
    users = await db.fetch_all("SELECT * FROM users")
    return {"users": users}

# Avoid: Blocking operations
@api_route
async def GET(request):
    users = db.fetch_all_sync("SELECT * FROM users")  # Blocks!
```

---

## API Reference

### @api_route Decorator

```python
from pynext import api_route

@api_route
async def GET(request):
    """
    Define an API route handler.
    
    Function name must be an HTTP method:
    GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS
    
    Args:
        request: FastAPI Request object
    
    Returns:
        dict, JSONResponse, or Response
    """
    return {"data": "..."}
```

### Response Helpers

```python
from pynext import JSONResponse, Response, RedirectResponse, HTMLResponse

JSONResponse(content, status_code=200, headers=None)
Response(content=None, status_code=200, headers=None, media_type=None)
RedirectResponse(url, status_code=307, headers=None)
HTMLResponse(content, status_code=200, headers=None)
```

### Request Utilities

```python
from pynext import get_params, get_query

params = get_params()  # URL path parameters
query = get_query()    # Query string parameters
```

---

## Next Steps

- **[State + Data Integration](STATE_DATA_INTEGRATION.md)** - How API Routes work with Signals and state
- [Layouts](LAYOUTS.md) - Page layouts and structure
- [Server Actions](SERVER_ACTIONS.md) - RPC-style server functions (comparison)
- [Routing](ROUTING.md) - File-based routing system

