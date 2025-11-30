# Edge Runtime

Deploy anywhere: Cloudflare, Vercel, Deno, Bun.

## The Problem

Edge functions run closer to users for faster responses. Each platform has different APIs and deployment requirements.

**Traditional**: Write platform-specific code for each provider.

**PyNext**: One decorator, deploy anywhere.

## Quick Start

```python
# pages/api/hello.py
from pynext import api_route, edge

@api_route
@edge
async def handler(request):
    return {"message": "Hello from the edge!"}
```

Deploy:
```bash
pynext build --edge cloudflare
```

## How It Works

### First Principles

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Python     │ →  │   Build      │ →  │   Platform   │
│   @edge      │    │   Output     │    │   Runtime    │
└──────────────┘    └──────────────┘    └──────────────┘
```

1. **Write**: Python functions with `@edge` decorator
2. **Build**: Generate platform-specific bundles
3. **Deploy**: Upload to edge platform
4. **Run**: Execute at edge locations worldwide

### Benefits

- **Low latency**: Code runs near users
- **No cold starts**: (platform dependent)
- **Global scale**: Deploy to all regions
- **One codebase**: Same Python for all platforms

## API Reference

### @edge Decorator

```python
from pynext import edge

@edge  # Simple usage
async def handler(request):
    return {"ok": True}

@edge(
    runtime="cloudflare",  # Specific platform
    regions=["us-east-1", "eu-west-1"],  # Deploy regions
    memory=256,            # Memory limit (MB)
    timeout=60,            # Timeout (seconds)
)
async def configured_handler(request):
    return {"ok": True}

# With platform bindings
@edge(KV="MY_KV_NAMESPACE", D1="MY_DATABASE")
async def handler_with_bindings(request):
    value = await request.env.KV.get("key")
    return {"value": value}
```

### EdgeRequest

```python
@edge
async def handler(request):
    # Request properties
    request.method      # "GET", "POST", etc.
    request.url         # Full URL string
    request.path        # URL path
    request.query       # Query parameters dict
    request.headers     # Headers dict
    
    # Body parsing
    text = await request.text()
    json_data = await request.json()
    
    # Platform bindings
    request.env.KV      # KV namespace
    request.env.D1      # D1 database
    request.env.R2      # R2 bucket
    
    return {"method": request.method}
```

### EdgeResponse

```python
from pynext.edge import EdgeResponse

# JSON response
return EdgeResponse.json({"message": "Hello"})
return EdgeResponse.json({"error": "Not found"}, status=404)

# Text response
return EdgeResponse.text("Hello, World!")

# HTML response
return EdgeResponse.html("<h1>Hello</h1>")

# Redirect
return EdgeResponse.redirect("/login", status=302)

# Custom response
return EdgeResponse(
    body='{"custom": true}',
    status=200,
    headers={"X-Custom": "value"},
)
```

## Platform Adapters

### Cloudflare Workers

```python
@edge(runtime="cloudflare")
async def handler(request):
    # Access KV
    kv_value = await request.env.KV.get("key")
    
    # Access D1 database
    result = await request.env.D1.prepare(
        "SELECT * FROM users WHERE id = ?"
    ).bind(123).first()
    
    # Access R2 bucket
    object = await request.env.R2.get("file.txt")
    
    return {"value": kv_value}
```

Build output:
```
dist/
├── _worker.js        # Worker bundle
├── wrangler.toml     # Configuration
└── static/           # Static assets
```

### Vercel Edge

```python
@edge(runtime="vercel")
async def handler(request):
    return {"message": "Hello from Vercel Edge!"}
```

Build output:
```
dist/
├── api/
│   └── handler.js    # Edge function
├── vercel.json       # Configuration
└── static/           # Static assets
```

### Deno Deploy

```python
@edge(runtime="deno")
async def handler(request):
    return {"runtime": "deno"}
```

Build output:
```
dist/
├── main.ts           # Deno entry point
├── deno.json         # Configuration
└── static/           # Static assets
```

### Bun

```python
@edge(runtime="bun")
async def handler(request):
    return {"runtime": "bun"}
```

Build output:
```
dist/
├── server.ts         # Bun entry point
├── bunfig.toml       # Configuration
└── static/           # Static assets
```

## Patterns

### API Route

```python
from pynext import api_route, edge

@api_route
@edge
async def get_user(request, id: int):
    user = await db.users.get(id)
    if not user:
        return EdgeResponse.json({"error": "Not found"}, status=404)
    return {"user": user}
```

### Authentication Middleware

```python
@edge
async def auth_handler(request):
    token = request.headers.get("Authorization")
    
    if not token:
        return EdgeResponse.json(
            {"error": "Unauthorized"},
            status=401,
        )
    
    # Verify token...
    return {"authenticated": True}
```

### Geolocation-Based Routing

```python
@edge
async def geo_handler(request):
    # Cloudflare provides geolocation
    country = request.headers.get("CF-IPCountry", "US")
    
    if country == "EU":
        return EdgeResponse.redirect("https://eu.example.com")
    
    return {"region": country}
```

### Caching

```python
@edge
async def cached_handler(request):
    # Check cache
    cached = await request.env.KV.get("cached-data")
    if cached:
        return {"data": cached, "cached": True}
    
    # Compute fresh data
    data = await expensive_computation()
    
    # Cache for 1 hour
    await request.env.KV.put("cached-data", data, expirationTtl=3600)
    
    return {"data": data, "cached": False}
```

## Platform Detection

```python
from pynext.edge import detect_platform, EdgePlatform

info = detect_platform()

if info.platform == EdgePlatform.CLOUDFLARE:
    print("Running on Cloudflare Workers")
    print(f"Region: {info.region}")
    
elif info.platform == EdgePlatform.VERCEL:
    print("Running on Vercel Edge")
    
elif info.platform == EdgePlatform.DENO:
    print("Running on Deno Deploy")
    
elif info.platform == EdgePlatform.BUN:
    print("Running on Bun")
```

## Build Commands

```bash
# Auto-detect platform
pynext build --edge

# Specific platform
pynext build --edge cloudflare
pynext build --edge vercel
pynext build --edge deno
pynext build --edge bun

# With configuration
pynext build --edge cloudflare --output dist/
```

## EdgeBuilder

Programmatic build:

```python
from pynext.edge import EdgeBuilder, build_for_edge, EdgePlatform
from pathlib import Path

# Using builder class
builder = EdgeBuilder(
    app_dir=Path("app"),
    output_dir=Path("dist"),
    platform=EdgePlatform.CLOUDFLARE,
    config={
        "name": "my-worker",
        "bindings": {"KV": "MY_KV"},
    },
)

result = builder.build()

if result.success:
    print(f"Built to {result.output_dir}")
    print(f"Entry point: {result.entry_point}")
    print(f"Config file: {result.config_file}")
else:
    print(f"Errors: {result.errors}")

# Using convenience function
result = build_for_edge(
    app_dir=Path("app"),
    output_dir=Path("dist"),
    platform="cloudflare",
)
```

## Configuration

### EdgeConfig

```python
from pynext.edge import EdgeConfig

config = EdgeConfig(
    runtime="cloudflare",
    regions=["us-east-1", "eu-west-1", "ap-southeast-1"],
    memory=256,
    timeout=30,
    bindings={
        "KV": "MY_KV_NAMESPACE",
        "D1": "MY_DATABASE",
        "R2": "MY_BUCKET",
    },
)
```

### Platform-Specific Files

#### wrangler.toml (Cloudflare)
```toml
name = "my-worker"
main = "dist/_worker.js"
compatibility_date = "2024-01-01"

[[kv_namespaces]]
binding = "KV"
id = "your-kv-namespace-id"

[[d1_databases]]
binding = "D1"
database_name = "my-database"
database_id = "your-database-id"
```

#### vercel.json (Vercel)
```json
{
  "functions": {
    "api/**/*.js": {
      "runtime": "edge"
    }
  }
}
```

#### deno.json (Deno)
```json
{
  "tasks": {
    "start": "deno run --allow-net --allow-env main.ts"
  }
}
```

## Migration from Vercel Edge

### Before (Vercel)

```typescript
// pages/api/hello.ts
import { NextRequest } from 'next/server';

export const config = {
  runtime: 'edge',
};

export default async function handler(req: NextRequest) {
  return new Response(JSON.stringify({ message: 'Hello' }), {
    headers: { 'Content-Type': 'application/json' },
  });
}
```

### After (PyNext)

```python
# pages/api/hello.py
from pynext import api_route, edge

@api_route
@edge
async def handler(request):
    return {"message": "Hello"}
```

## Troubleshooting

### Platform Not Detected

```python
from pynext.edge import detect_platform

info = detect_platform()
if info.platform == EdgePlatform.UNKNOWN:
    print("Platform not detected")
    print("Set environment variables for your platform")
```

### Bindings Not Available

```python
@edge(KV="MY_KV")  # Must declare bindings
async def handler(request):
    try:
        value = await request.env.KV.get("key")
    except AttributeError as e:
        print(f"Binding not configured: {e}")
```

### Build Errors

```python
result = builder.build()
if not result.success:
    for error in result.errors:
        print(f"Error: {error}")
```

