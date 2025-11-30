# Proxy Configuration

Simple API proxy with decorator-based setup.

## The Problem

Frontend apps often need to proxy API requests to avoid CORS issues or consolidate backends. Traditional solutions require verbose configuration files.

**Next.js**: `next.config.js` rewrites - verbose, not type-safe.

**PyNext**: Decorator-based, dynamic, Python-native configuration.

## Quick Start

```python
# proxy.py - Auto-discovered
from pynext import proxy

@proxy("/api/users/*")
def users_api():
    return "https://users.example.com"

@proxy("/api/products/*")
def products_api():
    return "https://products.example.com"
```

Now requests to `/api/users/123` proxy to `https://users.example.com/123`.

## How It Works

### First Principles

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Browser    │ →  │  PyNext     │ →  │  Backend    │
│  /api/users │    │  Proxy      │    │  API        │
└─────────────┘    └─────────────┘    └─────────────┘
       ↑                  │                  │
       └──────────────────┴──────────────────┘
                  Response flows back
```

1. **Match**: Request path matches proxy pattern
2. **Rewrite**: Optionally transform the path
3. **Headers**: Add authentication or custom headers
4. **Forward**: Send request to target backend
5. **Return**: Pass response back to client

### Benefits

- **CORS solved**: Same origin for frontend
- **Auth injection**: Add tokens server-side
- **API aggregation**: Multiple backends, one endpoint
- **Dev mocking**: Switch to mock server in dev

## API Reference

### @proxy Decorator

```python
@proxy(
    pattern,          # URL pattern to match
    rewrite=None,     # Path rewrite pattern
    headers=None,     # Headers to add
    websocket=False,  # WebSocket support
    dev_only=False,   # Only active in development
    timeout=30,       # Request timeout in seconds
)
def config_function():
    return "target_url"
    # or
    return {
        "target": "target_url",
        "headers": {"Authorization": "Bearer token"},
    }
```

### Pattern Matching

```python
# Simple wildcard
@proxy("/api/users/*")    # Matches /api/users/123, /api/users/abc

# Multiple segments
@proxy("/api/*/items/*")  # Matches /api/users/items/123

# Exact match
@proxy("/api/health")     # Only matches /api/health
```

### Path Rewriting

```python
# Strip prefix
@proxy("/api/v1/*", rewrite="/$1")
def api():
    return "https://api.example.com"
# /api/v1/users → https://api.example.com/users

# Change version
@proxy("/api/v1/*", rewrite="/v2/$1")
def api():
    return "https://api.example.com"
# /api/v1/users → https://api.example.com/v2/users

# Multiple captures
@proxy("/api/*/items/*", rewrite="/products/$1/items/$2")
def api():
    return "https://api.example.com"
# /api/users/items/123 → https://api.example.com/products/users/items/123
```

### Header Injection

```python
# Static headers
@proxy("/api/secure/*", headers={"X-API-Key": "secret"})
def secure():
    return "https://secure.example.com"

# Dynamic headers
@proxy("/api/auth/*")
def auth_api():
    import os
    return {
        "target": "https://auth.example.com",
        "headers": {
            "Authorization": f"Bearer {os.environ.get('API_TOKEN')}",
            "X-Request-ID": str(uuid.uuid4()),
        },
    }
```

## Patterns

### Multiple Backends

```python
# proxy.py
from pynext import proxy

@proxy("/api/users/*")
def users():
    return "https://users-service.internal"

@proxy("/api/products/*")
def products():
    return "https://products-service.internal"

@proxy("/api/orders/*")
def orders():
    return "https://orders-service.internal"
```

### Environment-Based Routing

```python
import os

@proxy("/api/*")
def api():
    env = os.environ.get("PYNEXT_ENV", "development")
    
    targets = {
        "development": "http://localhost:3001",
        "staging": "https://api-staging.example.com",
        "production": "https://api.example.com",
    }
    
    return targets.get(env, targets["development"])
```

### Dev Mock Server

```python
@proxy("/api/mock/*", dev_only=True)
def mock_api():
    """Only active in development mode."""
    return "http://localhost:4000"

# In production, these requests won't be proxied
```

### WebSocket Proxy

```python
@proxy("/ws/notifications", websocket=True)
def ws_notifications():
    return "ws://realtime.example.com"

@proxy("/ws/chat/*", websocket=True)
def ws_chat():
    return "wss://chat.example.com"
```

### Authentication Gateway

```python
@proxy("/api/secure/*")
def secure_api():
    """Add authentication to all requests."""
    from auth import get_service_token
    
    return {
        "target": "https://internal-api.example.com",
        "headers": {
            "Authorization": f"Bearer {get_service_token()}",
            "X-Service": "pynext-app",
        },
    }
```

### Rate-Limited API

```python
@proxy("/api/external/*", timeout=60)
def external_api():
    """External API with longer timeout."""
    return {
        "target": "https://slow-api.example.com",
        "headers": {
            "X-Rate-Limit-Key": os.environ.get("RATE_LIMIT_KEY"),
        },
    }
```

## Server Integration

### FastAPI Middleware

```python
# server.py
from fastapi import FastAPI
from pynext.proxy import ProxyMiddleware

app = FastAPI()
app.add_middleware(ProxyMiddleware)

# Or with custom config
from pynext.proxy import create_proxy_middleware

Middleware = create_proxy_middleware(auto_load=True)
app.add_middleware(Middleware)
```

### Manual Loading

```python
from pynext.proxy import load_proxy_config
from pathlib import Path

# Load from specific file
config = load_proxy_config(path=Path("./config/proxy.py"))

# Load from app directory
config = load_proxy_config(app_dir=Path("./app"))
```

## ProxyRoute Details

```python
from pynext.proxy import ProxyRoute, ProxyConfig

# Create route manually
route = ProxyRoute(
    pattern="/api/users/*",
    target="https://users.example.com",
    rewrite="/v2/$1",
    headers={"X-Custom": "value"},
    timeout=30,
    dev_only=False,
    websocket=False,
)

# Check if route matches
groups = route.match("/api/users/123")
if groups:
    rewritten = route.rewrite_path("/api/users/123", groups)
    # rewritten = "/v2/123"

# Create config
config = ProxyConfig()
config.add_route(route)
config.global_headers = {"X-Forwarded-For": "client"}

# Find matching route
result = config.find_route("/api/users/123", is_dev=True)
if result:
    matched_route, captured_groups = result
```

## Performance

| Metric | Description | Value |
|--------|-------------|-------|
| Latency overhead | Added by proxy | 1-2ms |
| Connection pooling | Reused connections | Yes |
| Timeout | Per request | Configurable |
| WebSocket support | Bidirectional | Full |

## Migration from Next.js

### Before (Next.js)

```javascript
// next.config.js
module.exports = {
  async rewrites() {
    return [
      {
        source: '/api/users/:path*',
        destination: 'https://users.example.com/:path*',
      },
      {
        source: '/api/products/:path*',
        destination: 'https://products.example.com/:path*',
      },
    ];
  },
};
```

### After (PyNext)

```python
# proxy.py
from pynext import proxy

@proxy("/api/users/*")
def users():
    return "https://users.example.com"

@proxy("/api/products/*")
def products():
    return "https://products.example.com"
```

## Troubleshooting

### Proxy Not Working

```python
# Check route is registered
from pynext.proxy import get_proxy_config

config = get_proxy_config()
print(f"Routes: {len(config.routes)}")
for route in config.routes:
    print(f"  {route.pattern} → {route.get_target()}")
```

### Headers Not Applied

```python
# Dynamic headers must be returned from function
@proxy("/api/*")
def api():
    # Wrong: headers parameter is static
    return "https://api.example.com"

# Right: return dict with headers
@proxy("/api/*")
def api():
    return {
        "target": "https://api.example.com",
        "headers": {"Authorization": f"Bearer {get_token()}"},
    }
```

### Dev-Only Route in Production

```python
# Check is_dev parameter
route.is_active(is_dev=False)  # False for dev_only routes
route.is_active(is_dev=True)   # True

# Middleware detects from environment
# PYNEXT_ENV=development → is_dev=True
# PYNEXT_ENV=production → is_dev=False
```

