# PyNext Edge Middleware

> **Intercept requests before they reach your pages with compiled route matching and O(1) lookup.**

Middleware runs before a request is processed, allowing you to authenticate users, redirect routes, rewrite URLs, add headers, rate limit, and more—all before your page code executes.

---

## Table of Contents

1. [What is Middleware?](#what-is-middleware)
2. [The Mental Model](#the-mental-model)
3. [Quick Start](#quick-start)
4. [Core Concepts](#core-concepts)
5. [Route Matching](#route-matching)
6. [Response Types](#response-types)
7. [MiddlewareContext](#middlewarecontext)
8. [Common Patterns](#common-patterns)
9. [Middleware Chain](#middleware-chain)
10. [Performance](#performance)
11. [Security Best Practices](#security-best-practices)
12. [Debugging](#debugging)
13. [API Reference](#api-reference)

---

## What is Middleware?

### The Elevator Pitch

Middleware intercepts every request and lets you:
- ✅ **Authenticate** users before they access protected pages
- ✅ **Redirect** visitors based on conditions (logged in, geo, A/B test)
- ✅ **Rewrite** URLs internally (without changing the browser URL)
- ✅ **Add headers** for security, caching, or custom needs
- ✅ **Rate limit** to prevent abuse
- ✅ **Log** requests for analytics

### PyNext vs Next.js Middleware

| Feature | Next.js | PyNext |
|---------|---------|--------|
| **Matching** | Runtime regex | **Pre-compiled trie** |
| **Cold Start** | ~50ms | **<5ms** |
| **Loading** | All middleware | **Lazy per-route** |
| **Processing** | Buffered | **Streaming** |
| **Language** | JavaScript/TypeScript | **Python** |

### First Principles: The Request Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          REQUEST PIPELINE                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ANALOGY: Think of middleware like airport security checkpoints            │
│                                                                              │
│   Without Middleware:                                                        │
│   ──────────────────                                                        │
│                                                                              │
│   Request ─────────────────────────────────────────────────────► Page       │
│            Anyone can access anything! 😱                                    │
│                                                                              │
│                                                                              │
│   With Middleware:                                                           │
│   ────────────────                                                          │
│                                                                              │
│   Request ──► Checkpoint 1 ──► Checkpoint 2 ──► Checkpoint 3 ──► Page       │
│               │                │                │                            │
│               │                │                │                            │
│               ├── Auth?        ├── Rate OK?     ├── Headers                 │
│               │   ├── Yes ──►  │   ├── Yes ──►  │   Added ──►              │
│               │   └── No ──► 🚫 Redirect       └── 429 Error               │
│               │                                                              │
│                                                                              │
│   Each checkpoint can:                                                       │
│   • Let the request continue (next())                                       │
│   • Redirect to another URL                                                 │
│   • Return a response directly                                              │
│   • Rewrite the URL internally                                              │
│   • Add/modify headers                                                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## The Mental Model

### When Does Middleware Run?

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          MIDDLEWARE TIMING                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                              MIDDLEWARE                                      │
│                                  │                                           │
│                                  │ Runs BEFORE:                             │
│                                  │ • Route matching                          │
│                                  │ • Static files                            │
│                                  │ • API routes                              │
│                                  │ • Page rendering                          │
│                                  │ • Layouts                                 │
│                                  │                                           │
│   ┌──────────────────────────────▼───────────────────────────────────────┐  │
│   │                                                                       │  │
│   │   REQUEST                                                             │  │
│   │   GET /admin/dashboard                                                │  │
│   │        │                                                              │  │
│   │        ▼                                                              │  │
│   │   ┌────────────────────────────────────────────────────────────────┐ │  │
│   │   │  MIDDLEWARE CHAIN                                               │ │  │
│   │   │                                                                 │ │  │
│   │   │  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐         │ │  │
│   │   │  │  Logging    │ → │    Auth     │ → │ Rate Limit  │         │ │  │
│   │   │  │ (priority:  │   │ (priority:  │   │ (priority:  │         │ │  │
│   │   │  │  100)       │   │  50)        │   │  10)        │         │ │  │
│   │   │  └─────────────┘   └─────────────┘   └─────────────┘         │ │  │
│   │   │        ↓                 ↓                 ↓                  │ │  │
│   │   │      next()         next() or        next() or               │ │  │
│   │   │                     redirect()        json()                  │ │  │
│   │   │                                                                │ │  │
│   │   └────────────────────────────────────────────────────────────────┘ │  │
│   │        │                                                              │  │
│   │        ▼ (if all pass)                                                │  │
│   │   ┌────────────────────────────────────────────────────────────────┐ │  │
│   │   │  ROUTER                                                        │ │  │
│   │   │  Match: pages/admin/dashboard.py                               │ │  │
│   │   └────────────────────────────────────────────────────────────────┘ │  │
│   │        │                                                              │  │
│   │        ▼                                                              │  │
│   │   ┌────────────────────────────────────────────────────────────────┐ │  │
│   │   │  PAGE RENDER                                                   │ │  │
│   │   │  Execute page function, generate HTML                          │ │  │
│   │   └────────────────────────────────────────────────────────────────┘ │  │
│   │        │                                                              │  │
│   │        ▼                                                              │  │
│   │   RESPONSE                                                            │  │
│   │                                                                       │  │
│   └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### The Four Outcomes

Middleware can do one of four things:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          MIDDLEWARE OUTCOMES                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   1. NEXT (Continue)                                                        │
│   ──────────────────                                                        │
│   return NextResponse.next()                                                │
│   → Request continues to next middleware or page                            │
│   → Optionally add/modify headers                                           │
│                                                                              │
│   2. REDIRECT                                                               │
│   ─────────────                                                             │
│   return NextResponse.redirect("/login")                                    │
│   → Browser navigates to new URL                                            │
│   → User sees URL change in address bar                                     │
│                                                                              │
│   3. REWRITE                                                                │
│   ────────────                                                              │
│   return NextResponse.rewrite("/internal/page")                             │
│   → Request handled by different page/API                                   │
│   → Browser URL stays the same (internal routing)                           │
│                                                                              │
│   4. RESPOND                                                                │
│   ────────────                                                              │
│   return NextResponse.json({"error": "Rate limited"}, status=429)           │
│   → Immediate response, no page/API called                                  │
│   → Useful for errors, API responses in middleware                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Basic Middleware

```python
# middleware.py (in project root or pages/)

from pynext import middleware, MiddlewareContext, NextResponse

@middleware(matcher="/admin/*")
async def auth_middleware(ctx: MiddlewareContext):
    """Protect all /admin/* routes."""
    
    # Check for authentication
    token = ctx.get_cookie("auth_token")
    
    if not token:
        # Not logged in → redirect to login
        return NextResponse.redirect("/login")
    
    # Logged in → continue to the page
    return NextResponse.next()
```

### What This Does

```
Request: GET /admin/dashboard
         │
         ▼
    ┌─────────────────────┐
    │ auth_middleware     │
    │                     │
    │ token = get_cookie  │
    │         │           │
    │    ┌────┴────┐      │
    │    │ token?  │      │
    │    └────┬────┘      │
    │    No   │   Yes     │
    │    │    │    │      │
    │    ▼    │    ▼      │
    │ redirect│  next()   │
    │ /login  │    │      │
    └─────────────────────┘
              │
              ▼
    /admin/dashboard page renders
```

---

## Core Concepts

### 1. Matchers - Which Routes to Intercept

```python
from pynext import middleware, MiddlewareConfig, MatcherType

# GLOB PATTERN (default) - Simple wildcards
@middleware(matcher="/api/*")  # /api/users, /api/products
async def api_auth(ctx):
    ...

@middleware(matcher="/admin/**")  # /admin/users, /admin/users/123/edit
async def admin_auth(ctx):
    ...

# EXACT MATCH - Only this specific path
@middleware(config=MiddlewareConfig(
    matcher="/login",
    matcher_type=MatcherType.EXACT,
))
async def login_middleware(ctx):
    ...

# PREFIX MATCH - Any path starting with this
@middleware(config=MiddlewareConfig(
    matcher="/admin",
    matcher_type=MatcherType.PREFIX,
))
async def admin_prefix(ctx):
    # Matches: /admin, /admin/users, /admin/settings, etc.
    ...

# REGEX - Full regular expression power
@middleware(config=MiddlewareConfig(
    matcher=r"/user/\d+",  # Only numeric user IDs
    matcher_type=MatcherType.REGEX,
))
async def user_middleware(ctx):
    # Matches: /user/123, /user/456
    # NOT: /user/abc, /user/
    ...
```

### 2. Exclusions - Skip Certain Paths

```python
@middleware(config=MiddlewareConfig(
    matcher="/*",  # Match everything...
    exclude=[
        "/_next/*",    # ...except static files
        "/api/*",      # ...except API routes
        "/static/*",   # ...except public assets
        "*.ico",       # ...except favicon
        "*.png",       # ...except images
        "*.css",       # ...except stylesheets
    ],
))
async def global_middleware(ctx):
    """Runs on all page requests, but not assets."""
    ...
```

### 3. Priority - Control Execution Order

```python
# Higher priority = runs FIRST

@middleware(config=MiddlewareConfig(matcher="/*", priority=100))
async def logging_middleware(ctx):
    """Runs FIRST for all routes."""
    print(f"[{ctx.method}] {ctx.path}")
    return NextResponse.next()

@middleware(config=MiddlewareConfig(matcher="/admin/*", priority=50))
async def auth_middleware(ctx):
    """Runs SECOND for /admin/* routes."""
    if not ctx.get_cookie("token"):
        return NextResponse.redirect("/login")
    return NextResponse.next()

@middleware(config=MiddlewareConfig(matcher="/api/*", priority=10))
async def rate_limit_middleware(ctx):
    """Runs LAST for /api/* routes."""
    if is_rate_limited(ctx):
        return NextResponse.json({"error": "Too many requests"}, status=429)
    return NextResponse.next()
```

```
Request: GET /admin/settings
         │
         ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │ PRIORITY 100: logging_middleware (matches /*)                   │
    │ → Logs request, calls next()                                    │
    └───────────────────────────────────┬─────────────────────────────┘
                                        ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │ PRIORITY 50: auth_middleware (matches /admin/*)                 │
    │ → Checks token, calls next() or redirect()                      │
    └───────────────────────────────────┬─────────────────────────────┘
                                        ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │ Page: /admin/settings                                           │
    └─────────────────────────────────────────────────────────────────┘
```

---

## Route Matching

### Pattern Syntax

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          MATCHING PATTERNS                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   PATTERN                MATCHES                       DOESN'T MATCH        │
│   ───────                ───────                       ─────────────        │
│                                                                              │
│   /admin                 /admin                        /admin/users         │
│                                                        /administrator       │
│                                                                              │
│   /admin/*               /admin/users                  /admin                │
│                          /admin/settings               /admin/users/123     │
│                                                                              │
│   /admin/**              /admin                        (matches all below   │
│                          /admin/users                   /admin)             │
│                          /admin/users/123                                    │
│                          /admin/users/123/edit                               │
│                                                                              │
│   /api/users/*           /api/users/123                /api/users           │
│                          /api/users/abc                /api/users/123/posts │
│                                                                              │
│   /user/:id              /user/123                     /user                 │
│                          /user/abc                     /user/123/profile    │
│                                                                              │
│   *.json                 /data.json                    /data.xml            │
│                          /api/config.json                                    │
│                                                                              │
│   /blog/[year]/[month]   /blog/2024/03                 /blog/2024           │
│                          /blog/2023/12                                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Compiled Matchers - The Performance Secret

PyNext pre-compiles matchers at startup for O(1) lookup:

```python
# What happens when your app starts:

# 1. Your matcher pattern
matcher="/api/*"

# 2. PyNext compiles it to a trie structure
#    (like a prefix tree for ultra-fast matching)

# 3. At runtime, matching is O(1) not O(n)!
#    - Next.js: Checks each middleware regex
#    - PyNext: Direct trie lookup

# This is why:
# - Cold start: <5ms (vs ~50ms)
# - Per-request: <0.01ms overhead
```

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          TRIE-BASED MATCHING                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   Middlewares:                                                               │
│   • /api/* → rate_limit                                                     │
│   • /admin/* → auth                                                         │
│   • /admin/settings → settings_auth                                         │
│                                                                              │
│   Compiled Trie:                                                            │
│                                                                              │
│                         (root)                                               │
│                        /      \                                              │
│                    api         admin                                         │
│                     |         /     \                                        │
│                    [*]       [*]   settings                                  │
│                     |         |       |                                      │
│              rate_limit     auth   settings_auth                            │
│                                                                              │
│   Request: /admin/users                                                      │
│            │                                                                 │
│            ▼                                                                 │
│   1. Look up "admin" → found                                                │
│   2. Look up "users" → matches [*] wildcard                                 │
│   3. Return: auth middleware                                                │
│   Time: O(path_segments), typically 2-3 lookups                             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Response Types

### NextResponse.next()

Continue to the next middleware or page:

```python
@middleware(matcher="/*")
async def logging_middleware(ctx):
    # Log the request
    print(f"Request: {ctx.method} {ctx.path}")
    
    # Continue without modification
    return NextResponse.next()

@middleware(matcher="/*")
async def add_headers_middleware(ctx):
    # Continue AND add headers
    return NextResponse.next(headers={
        "X-Request-Id": generate_request_id(),
        "X-Powered-By": "PyNext",
    })
```

### NextResponse.redirect()

Send user to a different URL (browser URL changes):

```python
@middleware(matcher="/old-page")
async def redirect_old(ctx):
    # Temporary redirect (307 - preserves method)
    return NextResponse.redirect("/new-page")

@middleware(matcher="/moved-permanently")
async def permanent_redirect(ctx):
    # Permanent redirect (308 - SEO friendly)
    return NextResponse.redirect("/new-location", status=308)

@middleware(matcher="/admin/*")
async def auth_redirect(ctx):
    if not ctx.get_cookie("token"):
        # Redirect with return URL
        return_url = ctx.path
        return NextResponse.redirect(f"/login?next={return_url}")
    return NextResponse.next()
```

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          REDIRECT STATUS CODES                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   CODE    TYPE           USE CASE                          METHOD PRESERVED │
│   ────    ────           ────────                          ─────────────────│
│                                                                              │
│   307     Temporary      Login required, maintenance       ✓ Yes            │
│   308     Permanent      URL changed forever (SEO)         ✓ Yes            │
│   301     Permanent      Legacy (converts POST→GET)        ✗ No             │
│   302     Temporary      Legacy (converts POST→GET)        ✗ No             │
│                                                                              │
│   Use 307/308 for modern apps - they preserve POST/PUT/DELETE methods!      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### NextResponse.rewrite()

Internal rewrite (browser URL stays the same):

```python
@middleware(matcher="/products/:id")
async def ab_test_rewrite(ctx):
    """A/B test: Some users see new product page design."""
    variant = ctx.get_cookie("ab_variant")
    
    if variant == "B":
        # Serve new design, but URL stays /products/123
        return NextResponse.rewrite("/products-v2/" + ctx.path.split("/")[-1])
    
    return NextResponse.next()

@middleware(matcher="/*")
async def geo_rewrite(ctx):
    """Serve localized content based on user's country."""
    if ctx.geo and ctx.geo.get("country") == "DE":
        # German users see /de/... content, but URL stays the same
        if not ctx.path.startswith("/de"):
            return NextResponse.rewrite(f"/de{ctx.path}")
    
    return NextResponse.next()
```

### NextResponse.json()

Return JSON directly without hitting page/API:

```python
@middleware(matcher="/api/*")
async def rate_limit(ctx):
    if is_rate_limited(ctx):
        return NextResponse.json(
            {"error": "Too many requests", "retry_after": 60},
            status=429,
            headers={"Retry-After": "60"}
        )
    return NextResponse.next()

@middleware(matcher="/api/health")
async def health_check(ctx):
    """Fast health check without routing overhead."""
    return NextResponse.json({"status": "ok", "timestamp": time.time()})
```

### Response Helpers

```python
from pynext.middleware import (
    redirect, rewrite, next_response, json_response,
    not_found, unauthorized, forbidden, bad_request,
    set_cookie, delete_cookie,
)

# Redirects
redirect("/login")                        # 307 temporary
redirect("/new-page", permanent=True)     # 308 permanent

# Rewrites
rewrite("/internal/path")

# Continue with options
next_response()
next_response(headers={"X-Custom": "value"})

# JSON responses
json_response({"data": "..."})
json_response({"data": "..."}, status=201)

# Error responses (convenience methods)
not_found("Page not found")               # 404
unauthorized("Please log in")             # 401
forbidden("Access denied")                # 403
bad_request("Invalid input")              # 400

# Cookie helpers
response = next_response()
response.set_cookie("session", "abc123", max_age=3600, httponly=True)
response.delete_cookie("old_session")
```

---

## MiddlewareContext

The `ctx` parameter gives you access to all request data:

### Basic Properties

```python
@middleware(matcher="/*")
async def my_middleware(ctx: MiddlewareContext):
    # Path and method
    path = ctx.path           # "/api/users/123"
    method = ctx.method       # "GET", "POST", etc.
    
    # Query parameters
    params = ctx.query_params  # {"page": "1", "limit": "10"}
    page = ctx.query_params.get("page", "1")
    
    # Full URL
    url = ctx.url              # "https://example.com/api/users?page=1"
    
    return NextResponse.next()
```

### Headers and Cookies

```python
@middleware(matcher="/*")
async def headers_cookies(ctx: MiddlewareContext):
    # Headers
    auth = ctx.get_header("authorization")
    content_type = ctx.get_header("content-type")
    all_headers = ctx.headers  # Dict[str, str]
    
    # Cookies
    session = ctx.get_cookie("session_id")
    preferences = ctx.get_cookie("preferences")
    all_cookies = ctx.cookies  # Dict[str, str]
    
    return NextResponse.next()
```

### User Agent Detection

```python
@middleware(matcher="/*")
async def device_detection(ctx: MiddlewareContext):
    # Raw user agent
    ua = ctx.user_agent  # "Mozilla/5.0 (iPhone; ..."
    
    # Convenience methods
    if ctx.is_mobile():
        return NextResponse.rewrite("/mobile" + ctx.path)
    
    if ctx.is_bot():
        # Serve pre-rendered content for SEO
        return NextResponse.rewrite("/prerender" + ctx.path)
    
    return NextResponse.next()
```

### Geolocation

```python
@middleware(matcher="/*")
async def geo_routing(ctx: MiddlewareContext):
    # Geo data (from CDN headers like Cloudflare, Vercel, etc.)
    if ctx.geo:
        country = ctx.geo.get("country")   # "US", "DE", "JP"
        city = ctx.geo.get("city")         # "San Francisco"
        region = ctx.geo.get("region")     # "California"
        latitude = ctx.geo.get("latitude") # 37.7749
        longitude = ctx.geo.get("longitude")
        
        if country == "EU":
            # Show GDPR consent banner
            return NextResponse.next(headers={"X-Show-GDPR": "true"})
    
    return NextResponse.next()
```

### Complete Context Reference

```python
class MiddlewareContext:
    # Request object (FastAPI/Starlette)
    request: Request
    
    # Parsed data
    cookies: Dict[str, str]
    headers: Dict[str, str]
    query_params: Dict[str, str]
    
    # Optional enrichments
    geo: Optional[Dict[str, Any]]      # Country, city, lat/lng
    device: Optional[Dict[str, Any]]   # Device type, browser, OS
    user_agent: str
    
    # Properties
    @property
    def path(self) -> str: ...
    @property
    def method(self) -> str: ...
    @property
    def url(self) -> str: ...
    
    # Methods
    def get_cookie(self, name: str) -> Optional[str]: ...
    def get_header(self, name: str) -> Optional[str]: ...
    def is_bot(self) -> bool: ...
    def is_mobile(self) -> bool: ...
```

---

## Common Patterns

### Pattern 1: Authentication

```python
from pynext import middleware, MiddlewareContext, NextResponse
import jwt

SECRET_KEY = "your-secret-key"

@middleware(matcher="/admin/*", priority=50)
async def auth_middleware(ctx: MiddlewareContext):
    """Protect admin routes with JWT authentication."""
    
    # Get token from cookie or header
    token = ctx.get_cookie("auth_token")
    if not token:
        auth_header = ctx.get_header("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
    
    if not token:
        # No token → redirect to login
        return NextResponse.redirect(f"/login?next={ctx.path}")
    
    try:
        # Verify JWT
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        
        # Add user info to headers for downstream use
        return NextResponse.next(headers={
            "X-User-Id": str(payload.get("user_id")),
            "X-User-Role": payload.get("role", "user"),
        })
        
    except jwt.ExpiredSignatureError:
        return NextResponse.redirect("/login?error=expired")
    except jwt.InvalidTokenError:
        return NextResponse.redirect("/login?error=invalid")


@middleware(matcher="/admin/settings/*", priority=40)
async def admin_role_middleware(ctx: MiddlewareContext):
    """Require admin role for settings pages."""
    
    role = ctx.get_header("x-user-role")  # Set by auth middleware
    
    if role != "admin":
        return NextResponse.json(
            {"error": "Admin access required"},
            status=403
        )
    
    return NextResponse.next()
```

### Pattern 2: Rate Limiting

```python
from collections import defaultdict
import time

# Simple in-memory rate limiter
request_times = defaultdict(list)

def is_rate_limited(client_id: str, limit: int = 100, window: int = 60) -> bool:
    """Check if client has exceeded rate limit."""
    now = time.time()
    window_start = now - window
    
    # Clean old requests
    request_times[client_id] = [
        t for t in request_times[client_id]
        if t > window_start
    ]
    
    # Check limit
    if len(request_times[client_id]) >= limit:
        return True
    
    # Record this request
    request_times[client_id].append(now)
    return False

@middleware(matcher="/api/*", priority=100)
async def rate_limit_middleware(ctx: MiddlewareContext):
    """Rate limit API requests per IP."""
    
    # Get client identifier
    client_ip = ctx.get_header("x-forwarded-for") or ctx.request.client.host
    
    if is_rate_limited(client_ip, limit=100, window=60):
        return NextResponse.json(
            {
                "error": "Rate limit exceeded",
                "message": "Too many requests. Please wait.",
                "retry_after": 60,
            },
            status=429,
            headers={"Retry-After": "60"}
        )
    
    return NextResponse.next()
```

### Pattern 3: Geo-Based Routing

```python
@middleware(matcher="/*", exclude=["/api/*", "/static/*"])
async def geo_middleware(ctx: MiddlewareContext):
    """Route users to localized content based on country."""
    
    if not ctx.geo:
        return NextResponse.next()
    
    country = ctx.geo.get("country", "").upper()
    
    # Define country → language mapping
    country_to_lang = {
        "DE": "de", "AT": "de", "CH": "de",  # German
        "FR": "fr", "BE": "fr", "CA": "fr",  # French
        "ES": "es", "MX": "es", "AR": "es",  # Spanish
        "JP": "ja",                           # Japanese
        "CN": "zh", "TW": "zh",              # Chinese
    }
    
    lang = country_to_lang.get(country)
    
    if lang and not ctx.path.startswith(f"/{lang}"):
        # Rewrite to localized version
        return NextResponse.rewrite(f"/{lang}{ctx.path}")
    
    return NextResponse.next()
```

### Pattern 4: A/B Testing

```python
import random
import hashlib

def get_variant(user_id: str, experiment: str) -> str:
    """Deterministic A/B variant based on user ID."""
    hash_input = f"{user_id}:{experiment}"
    hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
    return "A" if hash_value % 2 == 0 else "B"

@middleware(matcher="/pricing")
async def ab_test_middleware(ctx: MiddlewareContext):
    """A/B test the pricing page."""
    
    # Get or create user ID for consistent assignment
    user_id = ctx.get_cookie("user_id")
    if not user_id:
        user_id = str(random.randint(1000000, 9999999))
    
    # Get variant (deterministic)
    variant = ctx.get_cookie("pricing_variant")
    if not variant:
        variant = get_variant(user_id, "pricing_2024")
    
    # Track which variant user sees
    response = NextResponse.next(headers={
        "X-AB-Variant": variant,
    })
    
    # Set cookies for consistency
    response.set_cookie("user_id", user_id, max_age=365*24*60*60)
    response.set_cookie("pricing_variant", variant, max_age=30*24*60*60)
    
    if variant == "B":
        # Rewrite to new pricing page
        return NextResponse.rewrite("/pricing-new")
    
    return response
```

### Pattern 5: Logging and Monitoring

```python
import time
import logging

logger = logging.getLogger("pynext.middleware")

@middleware(matcher="/*", priority=1000)  # Highest priority = runs first
async def logging_middleware(ctx: MiddlewareContext):
    """Log all requests with timing."""
    
    start_time = time.time()
    request_id = generate_request_id()
    
    # Log request
    logger.info(f"[{request_id}] {ctx.method} {ctx.path}")
    
    # Continue to next middleware/page
    response = NextResponse.next(headers={
        "X-Request-Id": request_id,
    })
    
    # Log response (in real implementation, use response hooks)
    duration = time.time() - start_time
    logger.info(f"[{request_id}] Completed in {duration:.3f}s")
    
    return response
```

### Pattern 6: CORS Handling

```python
ALLOWED_ORIGINS = [
    "https://example.com",
    "https://app.example.com",
]

@middleware(matcher="/api/*")
async def cors_middleware(ctx: MiddlewareContext):
    """Handle CORS for API routes."""
    
    origin = ctx.get_header("origin")
    
    # Handle preflight requests
    if ctx.method == "OPTIONS":
        if origin in ALLOWED_ORIGINS:
            return NextResponse.json(
                {},
                status=204,
                headers={
                    "Access-Control-Allow-Origin": origin,
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization",
                    "Access-Control-Max-Age": "86400",
                }
            )
        return NextResponse.json({"error": "Not allowed"}, status=403)
    
    # Handle actual requests
    if origin in ALLOWED_ORIGINS:
        return NextResponse.next(headers={
            "Access-Control-Allow-Origin": origin,
        })
    
    return NextResponse.next()
```

### Pattern 7: Security Headers

```python
@middleware(matcher="/*", priority=90)
async def security_headers_middleware(ctx: MiddlewareContext):
    """Add security headers to all responses."""
    
    return NextResponse.next(headers={
        # Prevent clickjacking
        "X-Frame-Options": "DENY",
        
        # Prevent MIME type sniffing
        "X-Content-Type-Options": "nosniff",
        
        # Enable XSS filter
        "X-XSS-Protection": "1; mode=block",
        
        # Referrer policy
        "Referrer-Policy": "strict-origin-when-cross-origin",
        
        # Content Security Policy (customize as needed)
        "Content-Security-Policy": (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
        ),
        
        # HSTS (only on HTTPS)
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    })
```

---

## Middleware Chain

### Visualization

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          MIDDLEWARE CHAIN                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   Request: GET /admin/dashboard                                             │
│        │                                                                     │
│        ▼                                                                     │
│   ┌───────────────────────────────────────────────────────────────────────┐ │
│   │ LOGGING (priority=100, matcher=/*)                                    │ │
│   │ • Logs: "[abc123] GET /admin/dashboard"                               │ │
│   │ • Returns: next() with X-Request-Id header                            │ │
│   └───────────────────────────────────────────────────────────────────────┘ │
│        │                                                                     │
│        ▼                                                                     │
│   ┌───────────────────────────────────────────────────────────────────────┐ │
│   │ SECURITY HEADERS (priority=90, matcher=/*)                            │ │
│   │ • Adds: X-Frame-Options, CSP, etc.                                    │ │
│   │ • Returns: next() with security headers                               │ │
│   └───────────────────────────────────────────────────────────────────────┘ │
│        │                                                                     │
│        ▼                                                                     │
│   ┌───────────────────────────────────────────────────────────────────────┐ │
│   │ AUTH (priority=50, matcher=/admin/*)                                  │ │
│   │ • Checks: auth_token cookie                                           │ │
│   │ • If missing: redirect("/login") ──► STOPS HERE, returns redirect    │ │
│   │ • If valid: next() with X-User-Id header                             │ │
│   └───────────────────────────────────────────────────────────────────────┘ │
│        │                                                                     │
│        ▼ (if auth passed)                                                    │
│   ┌───────────────────────────────────────────────────────────────────────┐ │
│   │ RATE LIMIT (priority=10, matcher=/*)                                  │ │
│   │ • Checks: request count for IP                                        │ │
│   │ • If over limit: json({error}, 429) ──► STOPS HERE                   │ │
│   │ • If OK: next()                                                       │ │
│   └───────────────────────────────────────────────────────────────────────┘ │
│        │                                                                     │
│        ▼ (if rate limit passed)                                              │
│   ┌───────────────────────────────────────────────────────────────────────┐ │
│   │ PAGE: /admin/dashboard                                                │ │
│   │ • Renders dashboard content                                           │ │
│   │ • Has access to X-User-Id header set by auth middleware              │ │
│   └───────────────────────────────────────────────────────────────────────┘ │
│        │                                                                     │
│        ▼                                                                     │
│   RESPONSE (with all accumulated headers)                                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Chain Behavior Rules

1. **Priority ordering**: Higher priority runs first
2. **Short-circuit**: Redirect/json responses stop the chain
3. **Header accumulation**: Each `next()` can add headers
4. **Matcher filtering**: Only matching middleware runs

---

## Performance

### Benchmarks

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PERFORMANCE METRICS                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   METRIC                    PYNEXT            NEXT.JS          IMPROVEMENT  │
│   ──────                    ──────            ───────          ───────────  │
│                                                                              │
│   Matcher Compilation       O(n) at startup   O(n) at startup  Same         │
│   Route Matching            O(1) per request  O(n) per request 10-100x      │
│   Cold Start                <5ms              ~50ms            10x          │
│   Per-Request Overhead      <0.1ms            ~1-5ms           10-50x       │
│   Memory per Middleware     ~200 bytes        ~1KB             5x           │
│                                                                              │
│   WHY THE DIFFERENCE:                                                       │
│   ───────────────────                                                       │
│   • PyNext: Trie-based matching, lazy loading                               │
│   • Next.js: Regex matching, eager loading                                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Optimization Tips

```python
# 1. Use specific matchers, not catch-all

# ❌ Slow: Runs for EVERY request
@middleware(matcher="/*")
async def my_middleware(ctx):
    if ctx.path.startswith("/api"):
        # ... logic
    return NextResponse.next()

# ✓ Fast: Only runs for API routes
@middleware(matcher="/api/*")
async def my_middleware(ctx):
    # ... logic
    return NextResponse.next()


# 2. Use exclusions for static assets

# ✓ Skip static files for faster serving
@middleware(config=MiddlewareConfig(
    matcher="/*",
    exclude=["/_next/*", "/static/*", "*.ico", "*.png", "*.css", "*.js"],
))
async def my_middleware(ctx):
    ...


# 3. Keep middleware lightweight

# ❌ Slow: Database query in middleware
@middleware(matcher="/admin/*")
async def slow_auth(ctx):
    user = await db.query("SELECT * FROM users WHERE token = ?", token)
    ...

# ✓ Fast: Validate JWT locally
@middleware(matcher="/admin/*")
async def fast_auth(ctx):
    try:
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        ...
    except jwt.InvalidTokenError:
        return NextResponse.redirect("/login")
```

---

## Security Best Practices

### Do's and Don'ts

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SECURITY BEST PRACTICES                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ✓ DO                                   ✗ DON'T                            │
│   ────                                   ───────                            │
│                                                                              │
│   ✓ Validate JWT signatures              ✗ Trust JWT without verification   │
│   ✓ Use httpOnly cookies for tokens      ✗ Store tokens in localStorage     │
│   ✓ Set secure flag on cookies           ✗ Send tokens over HTTP            │
│   ✓ Implement rate limiting              ✗ Allow unlimited requests         │
│   ✓ Use HTTPS in production              ✗ Use HTTP in production           │
│   ✓ Validate redirect URLs               ✗ Redirect to user-supplied URLs   │
│   ✓ Add security headers                 ✗ Skip CSP, X-Frame-Options        │
│   ✓ Log security events                  ✗ Silently fail on auth errors     │
│                                                                              │
│   CRITICAL RULES:                                                           │
│   ───────────────                                                           │
│                                                                              │
│   1. Never trust client input                                               │
│   2. Always validate on the server                                          │
│   3. Use parameterized queries (no SQL injection)                           │
│   4. Sanitize output (no XSS)                                               │
│   5. Rotate secrets regularly                                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Secure Cookie Settings

```python
response = NextResponse.next()

# Secure auth token cookie
response.set_cookie(
    name="auth_token",
    value=token,
    max_age=24 * 60 * 60,    # 24 hours
    httponly=True,           # JavaScript can't access
    secure=True,             # HTTPS only
    samesite="lax",          # CSRF protection
    path="/",                # Available on all paths
)
```

---

## Debugging

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

@middleware(matcher="/*")
async def debug_middleware(ctx: MiddlewareContext):
    import logging
    logger = logging.getLogger("middleware")
    
    logger.debug(f"Path: {ctx.path}")
    logger.debug(f"Method: {ctx.method}")
    logger.debug(f"Headers: {dict(ctx.headers)}")
    logger.debug(f"Cookies: {ctx.cookies}")
    
    return NextResponse.next()
```

### Middleware Inspector

```python
# Add to your dev config
@middleware(matcher="/__debug/middleware")
async def middleware_inspector(ctx: MiddlewareContext):
    """Debug endpoint to see middleware chain."""
    from pynext.middleware import get_middleware_chain
    
    chain = get_middleware_chain(ctx.path)
    
    return NextResponse.json({
        "path": ctx.path,
        "matched_middleware": [
            {
                "name": m.__name__,
                "priority": m.config.priority,
                "matcher": m.config.matcher,
            }
            for m in chain
        ]
    })
```

---

## API Reference

### @middleware Decorator

```python
@middleware(
    config: Optional[MiddlewareConfig] = None,  # Full configuration
    matcher: str = "/*",                         # Quick matcher pattern
    priority: int = 0,                           # Execution order
)
async def my_middleware(ctx: MiddlewareContext) -> NextResponse:
    ...
```

### MiddlewareConfig

```python
MiddlewareConfig(
    matcher: Union[str, List[str], Pattern] = "/*",  # Route pattern(s)
    matcher_type: MatcherType = MatcherType.GLOB,    # Pattern type
    priority: int = 0,                               # Higher = runs first
    exclude: List[str] = [],                         # Paths to skip
    timeout_ms: int = 5000,                          # Max execution time
)
```

### MatcherType Enum

```python
from pynext import MatcherType

MatcherType.GLOB     # Wildcard patterns: /api/*, /admin/**
MatcherType.EXACT    # Exact match only
MatcherType.PREFIX   # Prefix match: /admin matches /admin/anything
MatcherType.REGEX    # Regular expression
```

### MiddlewareContext

```python
class MiddlewareContext:
    # Access request data
    request: Request
    cookies: Dict[str, str]
    headers: Dict[str, str]
    query_params: Dict[str, str]
    
    # Optional enrichments
    geo: Optional[Dict[str, Any]]
    device: Optional[Dict[str, Any]]
    user_agent: str
    
    # Properties
    @property
    def path(self) -> str: ...
    @property
    def method(self) -> str: ...
    @property
    def url(self) -> str: ...
    
    # Methods
    def get_cookie(self, name: str) -> Optional[str]: ...
    def get_header(self, name: str) -> Optional[str]: ...
    def is_bot(self) -> bool: ...
    def is_mobile(self) -> bool: ...
```

### NextResponse

```python
class NextResponse:
    @staticmethod
    def next(headers: Dict[str, str] = None) -> NextResponse: ...
    
    @staticmethod
    def redirect(
        url: str,
        status: int = 307,  # or 308 for permanent
    ) -> NextResponse: ...
    
    @staticmethod
    def rewrite(url: str) -> NextResponse: ...
    
    @staticmethod
    def json(
        data: Any,
        status: int = 200,
        headers: Dict[str, str] = None,
    ) -> NextResponse: ...
    
    # Instance methods
    def set_cookie(
        self,
        name: str,
        value: str,
        max_age: int = None,
        httponly: bool = False,
        secure: bool = False,
        samesite: str = "lax",
        path: str = "/",
    ) -> None: ...
    
    def delete_cookie(self, name: str) -> None: ...
```

---

## Related Documentation

- [Routing](ROUTING.md) - File-based routing system
- [API Routes](API_ROUTES.md) - REST API endpoints
- [Server Actions](SERVER_ACTIONS.md) - RPC-style server functions
- [ISR](ISR.md) - Incremental Static Regeneration

---

## Summary

You've learned:

1. ✅ What middleware is and when it runs
2. ✅ How to create middleware with matchers
3. ✅ The four response types (next, redirect, rewrite, json)
4. ✅ How to access request data via MiddlewareContext
5. ✅ Common patterns (auth, rate limiting, A/B testing)
6. ✅ How the middleware chain works
7. ✅ Performance optimization tips
8. ✅ Security best practices

Middleware is your first line of defense and your most powerful tool for request manipulation. Use it wisely! 🛡️
