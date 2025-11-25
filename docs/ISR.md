# PyNext Incremental Static Regeneration (ISR)

> Component-Level Cache Invalidation with Fine-Grained Updates

## Overview

PyNext ISR goes beyond Next.js with component-level granularity:

| Feature | Next.js | PyNext |
|---------|---------|--------|
| **Granularity** | Page-level | **Component-level** |
| **Invalidation** | Time-based | **Time, tag, signal** |
| **Regeneration** | Full page | **Partial (changed only)** |
| **Cache Keys** | Route-based | **Signal/Resource-based** |

## Quick Start

```python
from pynext import revalidate

@revalidate(seconds=60)
def product_list():
    """Revalidates every 60 seconds."""
    products = fetch_products()
    return div([product_card(p) for p in products])
```

## Core Concepts

### 1. Time-Based Revalidation

```python
from pynext import revalidate

@revalidate(seconds=60)  # Revalidate after 60 seconds
def pricing_table():
    prices = fetch_prices()
    return table([
        tr(td(p.name), td(f"${p.price}"))
        for p in prices
    ])
```

### 2. Tag-Based Invalidation

Group related content with tags:

```python
@revalidate(tags=["products", "featured"])
def featured_products():
    return div([product_card(p) for p in fetch_featured()])

@revalidate(tags=["products"])
def product_list():
    return div([product_card(p) for p in fetch_all()])

# Later: Invalidate all product-related content
await revalidate_tag("products")
```

### 3. Component-Level Scope

Only regenerate specific components:

```python
from pynext import revalidate, InvalidationScope

@revalidate(
    seconds=60,
    scope=InvalidationScope.COMPONENT,  # Not whole page!
)
def product_card(product):
    """Only this component regenerates, not the whole page."""
    return div(
        img(src=product.image, alt=product.name),
        h3(product.name),
        p(f"${product.price}"),
    )
```

### 4. On-Demand Revalidation

Trigger revalidation via API:

```python
from pynext import revalidate_path, revalidate_tag, revalidate_component

# Revalidate a specific path
await revalidate_path("/products")

# Revalidate by tag
await revalidate_tag("products")

# Revalidate a specific component everywhere
await revalidate_component("ProductCard")
```

## Invalidation Scopes

```python
from pynext import InvalidationScope

# PAGE: Regenerate entire page (like Next.js)
@revalidate(scope=InvalidationScope.PAGE)

# COMPONENT: Only regenerate this component
@revalidate(scope=InvalidationScope.COMPONENT)

# RESOURCE: Tied to a Resource's refetch
@revalidate(scope=InvalidationScope.RESOURCE)

# TAG: Invalidate via tag groups
@revalidate(scope=InvalidationScope.TAG, tags=["products"])
```

## Stale-While-Revalidate

Serve stale content while regenerating:

```
Request → Cache Check
   │
   ├── Fresh? → Serve immediately
   │
   ├── Stale? → Serve stale + queue regeneration
   │            └── Background: Regenerate → Update cache
   │
   └── Missing? → Generate → Cache → Serve
```

```python
from pynext import RevalidateConfig

config = RevalidateConfig(
    seconds=60,
    stale_while_revalidate=True,  # Default
    background_regeneration=True,  # Default
)
```

## Cache API

### ISRCache

```python
from pynext import get_isr_cache, init_isr_cache

# Initialize with disk persistence
cache = init_isr_cache(cache_dir=Path("./cache"))

# Get entry
entry = cache.get("/products")
if entry and not entry.is_stale:
    return entry.content

# Set entry
cache.set(
    "/products",
    rendered_html,
    RevalidateConfig(seconds=60, tags=["products"]),
)

# Invalidate
cache.invalidate_by_tag("products")
cache.invalidate_by_path("/products")
cache.invalidate_by_component("ProductCard")

# Stats
stats = cache.get_stats()
# {
#   "total_entries": 42,
#   "stale_entries": 3,
#   "tags": ["products", "featured", "blog"],
# }
```

### Disk Persistence

```python
# Cache persists across server restarts
cache = init_isr_cache(cache_dir=Path("./cache"))

# Load existing cache on startup
cache.load_from_disk()
```

## On-Demand Revalidation API

### Webhook Integration

```python
# Trigger revalidation from CMS webhook
@app.post("/api/revalidate")
async def handle_cms_webhook(request):
    data = await request.json()
    
    if data["type"] == "product_updated":
        await revalidate_tag("products")
    elif data["type"] == "post_published":
        await revalidate_path(f"/blog/{data['slug']}")
    
    return {"revalidated": True}
```

### Built-in Endpoints

PyNext includes revalidation endpoints:

```bash
# Revalidate a path
curl -X POST http://localhost:3000/api/revalidate/path \
  -H "x-revalidate-token: secret" \
  -d '{"path": "/products"}'

# Revalidate a tag
curl -X POST http://localhost:3000/api/revalidate/tag \
  -H "x-revalidate-token: secret" \
  -d '{"tag": "products"}'

# Revalidate a component
curl -X POST http://localhost:3000/api/revalidate/component \
  -H "x-revalidate-token: secret" \
  -d '{"component": "ProductCard"}'

# Get cache stats
curl http://localhost:3000/api/revalidate/stats \
  -H "x-revalidate-token: secret"
```

## Partial Page Regeneration

Only regenerate changed components:

```
Page: /products
├── Header (static)
├── Navigation (static)
├── ProductList (@revalidate) ← Only this regenerates
├── Sidebar (static)
└── Footer (static)

Result: 80% of page served from cache
```

## Background Regeneration Worker

```python
from pynext.core.isr import RegenerationWorker

# Worker processes stale entries in background
worker = RegenerationWorker(cache)
await worker.start()

# Register regeneration functions
worker.register_regenerator(
    "/products",
    lambda: render_products_page()
)
```

## Performance Comparison

| Metric | Next.js ISR | PyNext ISR |
|--------|-------------|------------|
| Granularity | Page | **Component** |
| Partial Regeneration | No | **Yes** |
| Tag-Based Invalidation | Limited | **Full** |
| Background Workers | Single | **Configurable** |

## Best Practices

1. **Use tags for related content** - Easier bulk invalidation
2. **Prefer component scope** - Faster regeneration
3. **Set appropriate TTL** - Balance freshness vs. load
4. **Use webhooks for instant updates** - Don't wait for TTL

## Architecture

### File Structure

```
pynext/
├── core/
│   └── isr.py           # ISRCache, decorators, revalidation functions
├── cache/
│   └── __init__.py      # Re-exports from core/isr.py
└── server/
    └── isr.py           # ISRMiddleware, on-demand API routes
```

### Key Classes

#### `ISRCache`

In-memory and disk-persisted cache with component-level granularity:

```python
from pynext.core.isr import ISRCache

cache = ISRCache(cache_dir=Path("./cache"))

# Store with config
cache.set("/products", html, RevalidateConfig(seconds=60, tags=["products"]))

# Retrieve (handles expiration + stale-while-revalidate)
entry = cache.get("/products")

# Invalidation methods
cache.invalidate_by_path("/products")
cache.invalidate_by_tag("products")
cache.invalidate_by_component("ProductCard")
cache.invalidate_by_resource("products_resource")
```

#### `ISRMiddleware`

FastAPI middleware for automatic caching:

```python
from pynext.server.isr import ISRMiddleware, add_isr_middleware

# Quick setup
cache, worker = add_isr_middleware(
    app,
    cache_dir="./cache",
    secret_token="your-secret"
)
```

Features:
- Automatic cache-key generation from request
- Stale-while-revalidate semantics
- Cache headers for CDN/edge (Cache-Control, ETag)
- X-PyNext-Cache header (hit/miss/stale)

#### `RegenerationWorker`

Background task for stale-while-revalidate:

```python
from pynext.core.isr import RegenerationWorker

worker = RegenerationWorker(cache)
await worker.start()

# Register how to regenerate specific keys
worker.register_regenerator("/products", render_products)
```

### Server Setup

```python
from fastapi import FastAPI
from pynext.server.isr import add_isr_middleware

app = FastAPI()

# This adds:
# - ISRMiddleware for caching
# - /api/revalidate/path endpoint
# - /api/revalidate/tag endpoint
# - /api/revalidate/component endpoint
# - /api/revalidate/stats endpoint
# - Background regeneration worker

cache, worker = add_isr_middleware(
    app,
    cache_dir="./cache",
    secret_token="your-secret-token"
)

# Worker starts/stops with app lifecycle
```

### Cache Flow

```
Request: GET /products
    │
    ├─▶ ISRMiddleware.dispatch()
    │    │
    │    ├─▶ Generate cache key (path + query + locale)
    │    │
    │    ├─▶ cache.get(key)
    │    │    │
    │    │    ├─▶ Entry exists + fresh
    │    │    │    └─▶ Return cached content (X-PyNext-Cache: hit)
    │    │    │
    │    │    ├─▶ Entry exists + stale
    │    │    │    ├─▶ Queue for regeneration
    │    │    │    └─▶ Return stale content (X-PyNext-Cache: stale)
    │    │    │
    │    │    └─▶ No entry (miss)
    │    │         ├─▶ Call next middleware → Render page
    │    │         ├─▶ Cache result
    │    │         └─▶ Return content (X-PyNext-Cache: miss)
    │    │
    │    └─▶ Add cache headers (Cache-Control, ETag)
    │
    └─▶ Response
```

## API Reference

### @revalidate

```python
@revalidate(
    seconds: Optional[int] = None,      # Time-based TTL
    tags: Optional[List[str]] = None,   # Tag groups
    scope: InvalidationScope = PAGE,    # Invalidation scope
    on_demand: bool = False,            # Only invalidate manually
)
def component():
    ...
```

### Revalidation Functions

```python
# Invalidate by path
await revalidate_path("/products")

# Invalidate by tag
await revalidate_tag("products")

# Invalidate by component
await revalidate_component("ProductCard")
```

### RevalidateConfig

```python
RevalidateConfig(
    seconds: Optional[int] = None,
    tags: List[str] = [],
    scope: InvalidationScope = PAGE,
    on_demand: bool = False,
    stale_while_revalidate: bool = True,
    background_regeneration: bool = True,
)
```

