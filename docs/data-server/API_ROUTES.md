# PyNext API Routes

> **Build powerful REST APIs alongside your pages—same routing system, full Python power.**

API Routes let you create HTTP endpoints (GET, POST, PUT, DELETE, etc.) that live alongside your pages. No separate server needed—your API is part of your app.

---

## Table of Contents

1. [What Are API Routes?](#what-are-api-routes)
2. [The Mental Model](#the-mental-model)
3. [Quick Start](#quick-start)
4. [HTTP Methods](#http-methods)
5. [Request Handling](#request-handling)
6. [Response Types](#response-types)
7. [Dynamic Routes](#dynamic-routes)
8. [Error Handling](#error-handling)
9. [Authentication](#authentication)
10. [Common Patterns](#common-patterns)
11. [Best Practices](#best-practices)
12. [API Reference](#api-reference)

---

## What Are API Routes?

### The Elevator Pitch

API Routes let you create **backend endpoints** using the same file-based routing as pages:

```
pages/
├── api/
│   ├── users/
│   │   ├── route.py          # GET/POST /api/users
│   │   └── [id]/
│   │       └── route.py      # GET/PUT/DELETE /api/users/:id
│   └── posts/
│       └── route.py          # /api/posts
└── index.py                  # Home page
```

### When to Use API Routes vs Server Actions

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      API ROUTES vs SERVER ACTIONS                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   USE API ROUTES WHEN:                USE SERVER ACTIONS WHEN:              │
│   ────────────────────                ────────────────────────              │
│                                                                              │
│   • Building public APIs              • Calling from your own UI            │
│   • Mobile apps need access           • Form submissions                    │
│   • Third-party integrations          • Button click handlers               │
│   • Webhooks from external services   • Internal data mutations             │
│   • RESTful resource endpoints        • Don't need REST semantics           │
│                                                                              │
│   Example:                            Example:                              │
│   ────────                            ────────                              │
│   /api/users → REST API               save_user() → called from form        │
│   /api/webhook → Stripe callback      toggle_like() → button handler        │
│   /api/v1/products → Public API       submit_comment() → UI action          │
│                                                                              │
│                                                                              │
│   ANALOGY:                                                                  │
│   ────────                                                                  │
│   API Routes = Restaurant's public menu (anyone can order)                  │
│   Server Actions = Kitchen's internal orders (staff only)                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## The Mental Model

### First Principles: The HTTP Request Cycle

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          HTTP REQUEST LIFECYCLE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ANALOGY: API Routes are like a RECEPTIONIST at a hotel                   │
│                                                                              │
│   1. RECEIVE REQUEST                                                        │
│      Guest arrives: "I want to check in" (POST /api/reservations)           │
│                                                                              │
│   2. VALIDATE                                                               │
│      Receptionist checks: "Do you have a reservation?"                      │
│                                                                              │
│   3. PROCESS                                                                │
│      Receptionist: Looks up room, prepares keys                             │
│                                                                              │
│   4. RESPOND                                                                │
│      Receptionist: "Here's your room key" (JSON response)                   │
│                                                                              │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                                                                     │   │
│   │   CLIENT                       SERVER                               │   │
│   │   ──────                       ──────                               │   │
│   │                                                                     │   │
│   │   POST /api/users              ┌──────────────────────────────────┐│   │
│   │   {                            │ pages/api/users/route.py         ││   │
│   │     "name": "Alice",     ──►   │                                  ││   │
│   │     "email": "a@b.com"         │ async def POST(request):         ││   │
│   │   }                            │     data = await request.json()  ││   │
│   │                                │     user = create_user(data)     ││   │
│   │                                │     return {"id": user.id}       ││   │
│   │                                └──────────────────────────────────┘│   │
│   │                                       │                            │   │
│   │   {"id": 123, "name": "Alice"} ◄──────┘                            │   │
│   │                                                                     │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### How Routing Works

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          API ROUTE MATCHING                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   FILE STRUCTURE:                                                           │
│                                                                              │
│   pages/api/                                                                │
│   ├── users/                                                                │
│   │   ├── route.py              # Handles /api/users                        │
│   │   └── [id]/                                                             │
│   │       └── route.py          # Handles /api/users/:id                    │
│   │                                                                          │
│   └── posts/                                                                │
│       ├── route.py              # Handles /api/posts                        │
│       └── [slug]/                                                           │
│           ├── route.py          # Handles /api/posts/:slug                  │
│           └── comments/                                                     │
│               └── route.py      # Handles /api/posts/:slug/comments         │
│                                                                              │
│                                                                              │
│   REQUEST MATCHING:                                                         │
│                                                                              │
│   GET /api/users           → pages/api/users/route.py → GET()              │
│   POST /api/users          → pages/api/users/route.py → POST()             │
│   GET /api/users/123       → pages/api/users/[id]/route.py → GET()         │
│   DELETE /api/users/123    → pages/api/users/[id]/route.py → DELETE()      │
│   GET /api/posts/hello     → pages/api/posts/[slug]/route.py → GET()       │
│   POST /api/posts/hello/comments → .../[slug]/comments/route.py → POST()   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Basic API Route

```python
# pages/api/hello/route.py

from pynext import api_route

@api_route
async def GET(request):
    """Handle GET /api/hello"""
    return {"message": "Hello, World!"}

@api_route
async def POST(request):
    """Handle POST /api/hello"""
    data = await request.json()
    return {
        "message": f"Hello, {data.get('name', 'World')}!",
        "received": data
    }
```

### Testing Your API

```bash
# GET request
curl http://localhost:3000/api/hello
# → {"message": "Hello, World!"}

# POST request
curl -X POST http://localhost:3000/api/hello \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice"}'
# → {"message": "Hello, Alice!", "received": {"name": "Alice"}}
```

---

## HTTP Methods

### Supported Methods

Define handlers for any HTTP method:

```python
# pages/api/users/route.py

from pynext import api_route

@api_route
async def GET(request):
    """List all users or get user by query param."""
    users = await get_all_users()
    return {"users": users}

@api_route
async def POST(request):
    """Create a new user."""
    data = await request.json()
    user = await create_user(data)
    return {"user": user, "created": True}

@api_route
async def HEAD(request):
    """Check if resource exists (no body)."""
    return None  # 200 OK with no body
```

```python
# pages/api/users/[id]/route.py

from pynext import api_route, get_params
from pynext.server import JSONResponse

@api_route
async def GET(request):
    """Get a specific user by ID."""
    params = get_params()
    user_id = params.get("id")
    
    user = await get_user(user_id)
    if not user:
        return JSONResponse({"error": "User not found"}, status_code=404)
    
    return {"user": user}

@api_route
async def PUT(request):
    """Update a user."""
    params = get_params()
    user_id = params.get("id")
    data = await request.json()
    
    user = await update_user(user_id, data)
    return {"user": user, "updated": True}

@api_route
async def PATCH(request):
    """Partially update a user."""
    params = get_params()
    user_id = params.get("id")
    data = await request.json()
    
    user = await patch_user(user_id, data)
    return {"user": user}

@api_route
async def DELETE(request):
    """Delete a user."""
    params = get_params()
    user_id = params.get("id")
    
    await delete_user(user_id)
    return JSONResponse(None, status_code=204)
```

### Method Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          HTTP METHODS REFERENCE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   METHOD     PURPOSE               BODY?    IDEMPOTENT?    SAFE?            │
│   ──────     ───────               ─────    ───────────    ─────            │
│                                                                              │
│   GET        Read/fetch data       No       Yes            Yes              │
│   POST       Create resource       Yes      No             No               │
│   PUT        Replace resource      Yes      Yes            No               │
│   PATCH      Partial update        Yes      No             No               │
│   DELETE     Remove resource       No*      Yes            No               │
│   HEAD       Same as GET, no body  No       Yes            Yes              │
│   OPTIONS    Check CORS/methods    No       Yes            Yes              │
│                                                                              │
│                                                                              │
│   COMMON PATTERNS:                                                          │
│   ────────────────                                                          │
│                                                                              │
│   GET    /api/users          → List all users                               │
│   POST   /api/users          → Create new user                              │
│   GET    /api/users/123      → Get user 123                                 │
│   PUT    /api/users/123      → Replace user 123 entirely                    │
│   PATCH  /api/users/123      → Update user 123 partially                    │
│   DELETE /api/users/123      → Delete user 123                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Request Handling

### The Request Object

```python
from pynext import api_route, get_params, get_query

@api_route
async def POST(request):
    # URL path parameters
    params = get_params()
    user_id = params.get("id")
    
    # Query string parameters
    query = get_query()
    page = int(query.get("page", "1"))
    limit = int(query.get("limit", "10"))
    
    # Request body (JSON)
    body = await request.json()
    
    # Form data
    form = await request.form()
    
    # Raw body
    raw = await request.body()
    
    # Headers
    auth = request.headers.get("authorization")
    content_type = request.headers.get("content-type")
    
    # Cookies
    session = request.cookies.get("session_id")
    
    # Request metadata
    method = request.method      # "POST"
    url = str(request.url)       # Full URL
    path = request.url.path      # "/api/users/123"
    
    # Client info
    client_ip = request.client.host
    
    return {"processed": True}
```

### Parsing Different Content Types

```python
from pynext import api_route

@api_route
async def POST(request):
    content_type = request.headers.get("content-type", "")
    
    if "application/json" in content_type:
        # JSON body
        data = await request.json()
        
    elif "application/x-www-form-urlencoded" in content_type:
        # Form data
        form = await request.form()
        data = dict(form)
        
    elif "multipart/form-data" in content_type:
        # File uploads
        form = await request.form()
        file = form.get("file")
        if file:
            contents = await file.read()
            filename = file.filename
            
    elif "text/plain" in content_type:
        # Plain text
        data = (await request.body()).decode("utf-8")
        
    else:
        # Raw bytes
        data = await request.body()
    
    return {"received": True}
```

### File Uploads

```python
# pages/api/upload/route.py

from pynext import api_route
from pynext.server import JSONResponse
import aiofiles
from pathlib import Path

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

@api_route
async def POST(request):
    """Handle file uploads."""
    form = await request.form()
    file = form.get("file")
    
    if not file:
        return JSONResponse(
            {"error": "No file provided"},
            status_code=400
        )
    
    # Check file size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        return JSONResponse(
            {"error": "File too large"},
            status_code=413
        )
    
    # Save file
    file_path = UPLOAD_DIR / file.filename
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(contents)
    
    return {
        "filename": file.filename,
        "size": len(contents),
        "path": str(file_path),
    }
```

---

## Response Types

### JSON Response (Default)

```python
@api_route
async def GET(request):
    # Simple dict → automatically becomes JSON
    return {"users": [...]}

# Explicit JSON with status code
from pynext.server import JSONResponse

@api_route
async def POST(request):
    return JSONResponse(
        {"created": True},
        status_code=201,
        headers={"X-Custom": "header"}
    )
```

### Other Response Types

```python
from pynext.server import (
    JSONResponse,
    PlainTextResponse,
    HTMLResponse,
    RedirectResponse,
    StreamingResponse,
    FileResponse,
)

@api_route
async def GET(request):
    response_type = request.query_params.get("format", "json")
    
    if response_type == "json":
        return JSONResponse({"data": "..."})
    
    elif response_type == "text":
        return PlainTextResponse("Plain text content")
    
    elif response_type == "html":
        return HTMLResponse("<h1>Hello HTML</h1>")
    
    elif response_type == "redirect":
        return RedirectResponse("/new-url", status_code=307)
    
    elif response_type == "file":
        return FileResponse("path/to/file.pdf")
```

### Streaming Response

```python
from pynext.server import StreamingResponse
import asyncio

@api_route
async def GET(request):
    """Stream large data."""
    
    async def generate():
        for i in range(100):
            yield f"data: {i}\n\n"
            await asyncio.sleep(0.1)
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
```

### Response Status Codes

```python
from pynext.server import JSONResponse

# Success responses
return JSONResponse({"data": ...}, status_code=200)  # OK (default)
return JSONResponse({"id": 123}, status_code=201)    # Created
return JSONResponse(None, status_code=204)           # No Content

# Client error responses
return JSONResponse({"error": "Bad request"}, status_code=400)
return JSONResponse({"error": "Unauthorized"}, status_code=401)
return JSONResponse({"error": "Forbidden"}, status_code=403)
return JSONResponse({"error": "Not found"}, status_code=404)
return JSONResponse({"error": "Conflict"}, status_code=409)
return JSONResponse({"error": "Unprocessable"}, status_code=422)
return JSONResponse({"error": "Rate limited"}, status_code=429)

# Server error responses
return JSONResponse({"error": "Internal error"}, status_code=500)
return JSONResponse({"error": "Not implemented"}, status_code=501)
return JSONResponse({"error": "Unavailable"}, status_code=503)
```

### Setting Headers and Cookies

```python
from pynext.server import JSONResponse

@api_route
async def POST(request):
    response = JSONResponse(
        {"logged_in": True},
        headers={
            "X-Request-Id": "abc123",
            "X-RateLimit-Remaining": "99",
        }
    )
    
    # Set cookie
    response.set_cookie(
        key="session_id",
        value="xyz789",
        max_age=3600,           # 1 hour
        httponly=True,          # Not accessible via JavaScript
        secure=True,            # HTTPS only
        samesite="lax",         # CSRF protection
    )
    
    return response

@api_route
async def DELETE(request):
    """Logout - clear session cookie."""
    response = JSONResponse({"logged_out": True})
    response.delete_cookie("session_id")
    return response
```

---

## Dynamic Routes

### Single Parameter

```python
# pages/api/users/[id]/route.py

from pynext import api_route, get_params

@api_route
async def GET(request):
    params = get_params()
    user_id = params.get("id")  # "123" from /api/users/123
    
    user = await get_user(user_id)
    return {"user": user}
```

### Multiple Parameters

```python
# pages/api/users/[userId]/posts/[postId]/route.py

from pynext import api_route, get_params

@api_route
async def GET(request):
    params = get_params()
    user_id = params.get("userId")  # "123"
    post_id = params.get("postId")  # "456"
    
    post = await get_user_post(user_id, post_id)
    return {"post": post}
```

### Catch-All Routes

```python
# pages/api/proxy/[...path]/route.py

from pynext import api_route, get_params
import httpx

@api_route
async def GET(request):
    """Proxy requests to another API."""
    params = get_params()
    path = params.get("path", [])  # List of segments
    full_path = "/".join(path)     # "users/123/posts"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.example.com/{full_path}")
        return response.json()
```

### Dynamic Route Visualization

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DYNAMIC ROUTE EXAMPLES                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   FILE PATH                              URL              PARAMS             │
│   ─────────                              ───              ──────             │
│                                                                              │
│   pages/api/users/[id]/route.py          /api/users/123   {id: "123"}       │
│                                                                              │
│   pages/api/[org]/[repo]/route.py        /api/acme/web    {org: "acme",     │
│                                                            repo: "web"}     │
│                                                                              │
│   pages/api/posts/[...slug]/route.py     /api/posts/a/b   {slug: ["a","b"]} │
│                                                                              │
│                                                                              │
│   PRIORITY (specific to generic):                                           │
│   ───────────────────────────────                                           │
│                                                                              │
│   1. pages/api/users/me/route.py        # Static: /api/users/me             │
│   2. pages/api/users/[id]/route.py      # Dynamic: /api/users/123           │
│   3. pages/api/[...path]/route.py       # Catch-all: /api/anything/else     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Error Handling

### Basic Error Handling

```python
from pynext import api_route, get_params
from pynext.server import JSONResponse

@api_route
async def GET(request):
    try:
    params = get_params()
    user_id = params.get("id")
    
        # Validate input
        if not user_id.isdigit():
            return JSONResponse(
                {"error": "Invalid user ID", "detail": "ID must be a number"},
                status_code=400
            )
        
        # Fetch data
        user = await get_user(int(user_id))
        
    if not user:
        return JSONResponse(
                {"error": "User not found"},
            status_code=404
        )
    
    return {"user": user}

    except DatabaseError as e:
        return JSONResponse(
            {"error": "Database error", "detail": str(e)},
            status_code=500
        )
    except Exception as e:
        return JSONResponse(
            {"error": "Internal server error"},
            status_code=500
        )
```

### Error Helper Functions

```python
# lib/api_errors.py

from pynext.server import JSONResponse

def bad_request(message: str, details: dict = None):
    return JSONResponse({
        "error": "Bad Request",
        "message": message,
        "details": details,
    }, status_code=400)

def unauthorized(message: str = "Authentication required"):
    return JSONResponse({
        "error": "Unauthorized",
        "message": message,
    }, status_code=401)

def forbidden(message: str = "Access denied"):
    return JSONResponse({
        "error": "Forbidden",
        "message": message,
    }, status_code=403)

def not_found(resource: str = "Resource"):
    return JSONResponse({
        "error": "Not Found",
        "message": f"{resource} not found",
    }, status_code=404)

def internal_error(message: str = "Internal server error"):
    return JSONResponse({
        "error": "Internal Server Error",
        "message": message,
    }, status_code=500)
```

### Using Error Helpers

```python
from pynext import api_route, get_params
from lib.api_errors import bad_request, not_found, unauthorized

@api_route
async def GET(request):
    params = get_params()
    user_id = params.get("id")
    
    # Validation
    if not user_id.isdigit():
        return bad_request("Invalid user ID", {"id": "Must be a number"})
    
    # Auth check
    if not request.headers.get("authorization"):
        return unauthorized()
    
    # Fetch
    user = await get_user(int(user_id))
    if not user:
        return not_found("User")
    
    return {"user": user}
```

### Validation with Pydantic

```python
from pynext import api_route
from pynext.server import JSONResponse
from pydantic import BaseModel, EmailStr, ValidationError

class CreateUserRequest(BaseModel):
    name: str
    email: EmailStr
    age: int

@api_route
async def POST(request):
    try:
        data = await request.json()
        user_data = CreateUserRequest(**data)
    except ValidationError as e:
        return JSONResponse({
            "error": "Validation failed",
            "details": e.errors(),
        }, status_code=422)
    
    user = await create_user(user_data.dict())
    return {"user": user}
```

---

## Authentication

### JWT Authentication

```python
# lib/auth.py

import jwt
from datetime import datetime, timedelta
from pynext.server import JSONResponse

SECRET_KEY = "your-secret-key"

def create_token(user_id: int) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=24),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise AuthError("Token expired")
    except jwt.InvalidTokenError:
        raise AuthError("Invalid token")

def get_auth_user(request) -> dict:
    """Extract and verify user from request."""
    auth_header = request.headers.get("authorization", "")
    
    if not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header[7:]
    try:
        payload = verify_token(token)
        return {"user_id": payload["user_id"]}
    except AuthError:
        return None
```

### Protected API Route

```python
# pages/api/protected/route.py

from pynext import api_route
from lib.auth import get_auth_user
from lib.api_errors import unauthorized

@api_route
async def GET(request):
    user = get_auth_user(request)
    
    if not user:
        return unauthorized("Valid token required")
    
    return {
        "message": "Protected data",
        "user_id": user["user_id"]
    }
```

### Auth Decorator

```python
# lib/decorators.py

from functools import wraps
from lib.auth import get_auth_user
from lib.api_errors import unauthorized, forbidden

def require_auth(handler):
    """Decorator: Require authentication."""
    @wraps(handler)
    async def wrapper(request):
        user = get_auth_user(request)
        if not user:
            return unauthorized()
        request.state.user = user
        return await handler(request)
    return wrapper

def require_role(*roles):
    """Decorator: Require specific role."""
    def decorator(handler):
        @wraps(handler)
        async def wrapper(request):
            user = get_auth_user(request)
            if not user:
                return unauthorized()
            if user.get("role") not in roles:
                return forbidden("Insufficient permissions")
            request.state.user = user
            return await handler(request)
    return wrapper
    return decorator
```

```python
# pages/api/admin/route.py

from pynext import api_route
from lib.decorators import require_auth, require_role

@api_route
@require_auth
async def GET(request):
    """Requires any authenticated user."""
    return {"admin_data": "..."}

@api_route
@require_role("admin", "superadmin")
async def DELETE(request):
    """Requires admin or superadmin role."""
    return {"deleted": True}
```

---

## Common Patterns

### Pattern 1: CRUD API

```python
# pages/api/posts/route.py

from pynext import api_route, get_query
from pynext.server import JSONResponse

@api_route
async def GET(request):
    """List posts with pagination."""
    query = get_query()
    page = int(query.get("page", "1"))
    limit = int(query.get("limit", "10"))
    
    posts = await get_posts(page=page, limit=limit)
    total = await count_posts()
    
    return {
        "posts": posts,
        "pagination": {
        "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit,
        }
    }

@api_route
async def POST(request):
    """Create a new post."""
    data = await request.json()
    post = await create_post(data)
    return JSONResponse({"post": post}, status_code=201)


# pages/api/posts/[id]/route.py

@api_route
async def GET(request):
    """Get single post."""
    params = get_params()
    post = await get_post(params["id"])
    if not post:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return {"post": post}

@api_route
async def PUT(request):
    """Update post."""
    params = get_params()
    data = await request.json()
    post = await update_post(params["id"], data)
    return {"post": post}

@api_route
async def DELETE(request):
    """Delete post."""
    params = get_params()
    await delete_post(params["id"])
    return JSONResponse(None, status_code=204)
```

### Pattern 2: Webhook Handler

```python
# pages/api/webhooks/stripe/route.py

from pynext import api_route
from pynext.server import JSONResponse
import stripe
import hmac
import hashlib

WEBHOOK_SECRET = "whsec_..."

@api_route
async def POST(request):
    """Handle Stripe webhooks."""
    body = await request.body()
    signature = request.headers.get("stripe-signature")
    
    # Verify webhook signature
    try:
        event = stripe.Webhook.construct_event(
            body, signature, WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        return JSONResponse({"error": "Invalid signature"}, status_code=400)
    
    # Handle event types
    if event["type"] == "payment_intent.succeeded":
        payment = event["data"]["object"]
        await handle_payment_success(payment)
    
    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        await handle_subscription_cancelled(subscription)
    
    return {"received": True}
```

### Pattern 3: Search API

```python
# pages/api/search/route.py

from pynext import api_route, get_query
from pynext.server import JSONResponse

@api_route
async def GET(request):
    """Search with filters."""
    query = get_query()
    
    # Search term
    q = query.get("q", "")
    if not q or len(q) < 2:
        return JSONResponse(
            {"error": "Search term must be at least 2 characters"},
            status_code=400
        )
    
    # Filters
    category = query.get("category")
    min_price = float(query.get("min_price", "0"))
    max_price = float(query.get("max_price", "999999"))
    sort = query.get("sort", "relevance")
    
    # Pagination
    page = int(query.get("page", "1"))
    limit = min(int(query.get("limit", "20")), 100)  # Max 100
    
    results = await search(
        query=q,
        category=category,
        price_range=(min_price, max_price),
        sort=sort,
        page=page,
        limit=limit,
    )
    
    return {
        "query": q,
        "results": results["items"],
        "total": results["total"],
        "took_ms": results["took_ms"],
    }
```

### Pattern 4: Batch Operations

```python
# pages/api/users/batch/route.py

from pynext import api_route
from pynext.server import JSONResponse

@api_route
async def POST(request):
    """Batch create/update users."""
    data = await request.json()
    operations = data.get("operations", [])
    
    results = []
    for op in operations:
        try:
            if op["action"] == "create":
                user = await create_user(op["data"])
                results.append({"success": True, "id": user["id"]})
            elif op["action"] == "update":
                user = await update_user(op["id"], op["data"])
                results.append({"success": True, "id": op["id"]})
            elif op["action"] == "delete":
                await delete_user(op["id"])
                results.append({"success": True, "id": op["id"]})
        except Exception as e:
            results.append({"success": False, "error": str(e)})
    
    success_count = sum(1 for r in results if r.get("success"))
    
    return {
        "results": results,
        "summary": {
            "total": len(operations),
            "success": success_count,
            "failed": len(operations) - success_count,
        }
    }
```

### Pattern 5: Rate Limiting

```python
# lib/rate_limit.py

from collections import defaultdict
import time

request_counts = defaultdict(list)

def is_rate_limited(key: str, limit: int = 100, window: int = 60) -> bool:
    """Check if key has exceeded rate limit."""
    now = time.time()
    window_start = now - window
    
    # Clean old entries
    request_counts[key] = [t for t in request_counts[key] if t > window_start]
    
    # Check limit
    if len(request_counts[key]) >= limit:
        return True
    
    request_counts[key].append(now)
    return False

def get_remaining(key: str, limit: int = 100) -> int:
    """Get remaining requests in window."""
    return max(0, limit - len(request_counts[key]))
```

```python
# pages/api/rate-limited/route.py

from pynext import api_route
from pynext.server import JSONResponse
from lib.rate_limit import is_rate_limited, get_remaining

RATE_LIMIT = 100
RATE_WINDOW = 60

@api_route
async def GET(request):
    client_ip = request.client.host
    
    if is_rate_limited(client_ip, RATE_LIMIT, RATE_WINDOW):
        return JSONResponse(
            {"error": "Rate limit exceeded"},
            status_code=429,
            headers={
                "Retry-After": str(RATE_WINDOW),
                "X-RateLimit-Limit": str(RATE_LIMIT),
                "X-RateLimit-Remaining": "0",
            }
        )
    
    return JSONResponse(
        {"data": "..."},
        headers={
            "X-RateLimit-Limit": str(RATE_LIMIT),
            "X-RateLimit-Remaining": str(get_remaining(client_ip, RATE_LIMIT)),
        }
    )
```

---

## Best Practices

### Do's and Don'ts

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          API ROUTES BEST PRACTICES                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ✓ DO                                                                      │
│   ────                                                                      │
│                                                                              │
│   ✓ Use proper HTTP methods                                                │
│     GET for reads, POST for creates, PUT/PATCH for updates                 │
│                                                                              │
│   ✓ Return appropriate status codes                                        │
│     201 for created, 204 for no content, 404 for not found                 │
│                                                                              │
│   ✓ Validate input data                                                    │
│     Use Pydantic, check types, sanitize strings                            │
│                                                                              │
│   ✓ Handle errors gracefully                                               │
│     Return structured error responses with helpful messages                 │
│                                                                              │
│   ✓ Version your APIs                                                      │
│     /api/v1/users or Accept: application/vnd.api+json;version=1            │
│                                                                              │
│   ✓ Document your endpoints                                                │
│     Use docstrings, OpenAPI, or API documentation tools                    │
│                                                                              │
│                                                                              │
│   ✗ DON'T                                                                   │
│   ───────                                                                   │
│                                                                              │
│   ✗ Expose internal errors                                                 │
│     Log them, but return generic messages to users                         │
│                                                                              │
│   ✗ Trust client input                                                     │
│     Always validate and sanitize                                           │
│                                                                              │
│   ✗ Return 200 for errors                                                  │
│     Use proper 4xx/5xx status codes                                        │
│                                                                              │
│   ✗ Hardcode secrets                                                       │
│     Use environment variables                                              │
│                                                                              │
│   ✗ Forget rate limiting                                                   │
│     Protect against abuse                                                  │
│                                                                              │
│   ✗ Return sensitive data                                                  │
│     Filter out passwords, internal IDs, etc.                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### API Response Structure

```python
# Consistent response format

# Success response
{
    "data": { ... },          # The actual data
    "meta": {                 # Optional metadata
        "page": 1,
        "limit": 10,
        "total": 100,
    }
}

# Error response
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input",
        "details": [
            {"field": "email", "message": "Invalid email format"}
        ]
    }
}

# List response
{
    "data": [...],
    "pagination": {
        "page": 1,
        "limit": 10,
        "total": 100,
        "has_next": true,
    }
}
```

---

## API Reference

### @api_route Decorator

```python
from pynext import api_route

@api_route
async def METHOD(request):
    """
    request: FastAPI/Starlette Request object
    Returns: dict (auto-JSON), Response, or JSONResponse
    """
    return {"data": "..."}
```

### Request Object

```python
# Path and URL
request.method          # "GET", "POST", etc.
request.url             # Full URL
request.url.path        # Path portion
request.url.query       # Query string

# Headers and cookies
request.headers         # Headers dict
request.cookies         # Cookies dict

# Body parsing
await request.json()    # Parse JSON body
await request.form()    # Parse form data
await request.body()    # Raw bytes

# Query params
request.query_params    # QueryParams object

# Client info
request.client.host     # Client IP
```

### Response Classes

```python
from pynext.server import (
    JSONResponse,
    PlainTextResponse,
    HTMLResponse,
    RedirectResponse,
    StreamingResponse,
    FileResponse,
)

# JSONResponse
JSONResponse(
    content: Any,
    status_code: int = 200,
    headers: dict = None,
)

# PlainTextResponse
PlainTextResponse(
    content: str,
    status_code: int = 200,
)

# HTMLResponse
HTMLResponse(
    content: str,
    status_code: int = 200,
)

# RedirectResponse
RedirectResponse(
    url: str,
    status_code: int = 307,
)

# StreamingResponse
StreamingResponse(
    content: AsyncGenerator,
    media_type: str = "text/plain",
    headers: dict = None,
)

# FileResponse
FileResponse(
    path: str,
    filename: str = None,
    media_type: str = None,
)
```

### Helper Functions

```python
from pynext import get_params, get_query

# Get route parameters
params = get_params()  # {"id": "123"}

# Get query parameters
query = get_query()    # {"page": "1", "sort": "name"}
```

---

## Related Documentation

- [Routing](ROUTING.md) - File-based routing system
- [Server Actions](SERVER_ACTIONS.md) - RPC-style server functions
- [Middleware](MIDDLEWARE.md) - Request interception
- [Authentication](AUTHENTICATION.md) - Auth patterns

---

## Summary

You've learned:

1. ✅ What API Routes are and when to use them
2. ✅ How to handle different HTTP methods
3. ✅ Request parsing and validation
4. ✅ Response types and status codes
5. ✅ Dynamic routes and parameters
6. ✅ Error handling patterns
7. ✅ Authentication strategies
8. ✅ Common API patterns

Build powerful APIs alongside your pages! 🚀
