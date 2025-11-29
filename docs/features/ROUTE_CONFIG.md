# Route Segment Configuration

> Per-route control over rendering, caching, and runtime - simpler than Next.js, faster at startup.

## The Problem

Different pages need different behavior:

```
Landing page  → Static, cached forever
Product page  → ISR, refresh every hour
Dashboard     → Dynamic, never cache
API endpoint  → Edge runtime for speed
```

**Next.js approach** (scattered exports):

```javascript
// Next.js - multiple exports in the file
export const dynamic = 'force-dynamic'
export const revalidate = 60
export const runtime = 'edge'

export default function Page() { ... }
```

**PyNext approach** (single decorator):

```python
# PyNext - one decorator, all options
@route_config(dynamic="force", revalidate=60, runtime="edge")
@page
def Page():
    ...
```

---

## First Principles

### What is Route Segment Config?

Think of it like a **profile for each page**:

```
┌─────────────────────────────────────────────────────────────┐
│                     Your Page                                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   "How should I be rendered?"                                │
│   "Should my response be cached?"                            │
│   "Where should I run?"                                      │
│                                                              │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Route Config                              │
│                                                              │
│   dynamic = "static"    → Generate at build time             │
│   revalidate = 3600     → Regenerate every hour              │
│   runtime = "python"    → Standard Python server             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Static vs Dynamic

```
                    STATIC                         DYNAMIC
                    ──────                         ───────
                    
When Generated:     Build time                     Request time
Speed:              Fastest (pre-built)            Slower (computed)
Data Freshness:     Stale (until rebuild)          Always fresh
Use Case:           About page, docs               Dashboard, search

                         ISR (Incremental Static Regen)
                         ────────────────────────────────
                         
When Generated:     Build time + periodic refresh
Speed:              Fast (cached) + fresh data
Data Freshness:     Configurable (every N seconds)
Use Case:           Product pages, blog posts
```

### Caching Flow

```
Request arrives
      │
      ▼
┌─────────────────┐
│  Check Cache    │
└────────┬────────┘
         │
    Cached? ──No──→ ┌──────────────┐
         │          │ Render Page  │
        Yes         └──────┬───────┘
         │                 │
         ▼                 ▼
┌──────────────┐   ┌──────────────┐
│ Return Cache │   │ Store Cache  │
└──────────────┘   └──────────────┘
                          │
                          ▼
                   ┌──────────────┐
                   │ Return HTML  │
                   └──────────────┘
```

---

## Quick Start

### 3 Lines to Configure Any Route

```python
from pynext import page, route_config

@route_config(revalidate=60)  # Refresh every 60 seconds
@page
def ProductPage(id: str):
    product = fetch_product(id)
    return ProductCard(product)
```

That's it. Your page now uses ISR with 60-second revalidation.

### Common Patterns

```python
# Static page (build time only)
@route_config(dynamic="static")

# Dynamic page (always fresh)
@route_config(dynamic="force", cache="no-store")

# ISR with cache tags
@route_config(revalidate=3600, tags=["products"])

# Edge runtime
@route_config(runtime="edge", max_duration=30)
```

---

## Complete API Reference

### The `@route_config` Decorator

```python
from pynext import route_config

@route_config(
    # === Rendering Mode ===
    dynamic="auto",      # "auto" | "force" | "error" | "static"
    dynamic_params=True, # Allow undefined dynamic params
    
    # === Caching ===
    revalidate=False,    # False | 0 | seconds (int)
    cache="auto",        # "auto" | "force" | "no-store"
    tags=[],             # Cache tags for invalidation
    
    # === Runtime ===
    runtime="python",    # "python" | "edge"
    max_duration=60,     # Max execution seconds
    preferred_region="auto",  # Region hint(s)
)
```

### Parameter Details

#### `dynamic` - Rendering Mode

| Value | Description | Use Case |
|-------|-------------|----------|
| `"auto"` | PyNext decides based on usage | Default, let framework optimize |
| `"force"` | Always render at request time | Dashboard, personalized content |
| `"error"` | Error if dynamic features used | Ensure page is fully static |
| `"static"` | Force static generation | Landing pages, docs |

```python
# Always render fresh (user-specific content)
@route_config(dynamic="force")
@page
def Dashboard():
    user = get_current_user()
    return DashboardContent(user)

# Must be static (error if using cookies, headers, etc.)
@route_config(dynamic="error")
@page
def LandingPage():
    return StaticContent()
```

#### `revalidate` - ISR Timing

| Value | Description |
|-------|-------------|
| `False` | No ISR (default) |
| `0` | Revalidate every request |
| `60` | Revalidate every 60 seconds |
| `3600` | Revalidate every hour |

```python
# Regenerate every 5 minutes
@route_config(revalidate=300)
@page
def BlogPost(slug: str):
    post = fetch_post(slug)
    return Article(post)
```

#### `cache` - Caching Behavior

| Value | Description | Headers Generated |
|-------|-------------|-------------------|
| `"auto"` | PyNext decides | Based on dynamic/revalidate |
| `"force"` | Always cache | `Cache-Control: public, max-age=31536000, immutable` |
| `"no-store"` | Never cache | `Cache-Control: no-store, must-revalidate` |

```python
# Never cache (real-time data)
@route_config(cache="no-store")
@page
def LiveFeed():
    return RealTimeData()
```

#### `tags` - Cache Tags

Tags for on-demand revalidation:

```python
@route_config(revalidate=3600, tags=["products", "featured"])
@page
def ProductPage(id: str):
    return Product(id)

# Later, invalidate all pages with "products" tag:
from pynext import revalidate_tag
revalidate_tag("products")
```

#### `runtime` - Execution Environment

| Value | Description | Limitations |
|-------|-------------|-------------|
| `"python"` | Standard Python (default) | None |
| `"edge"` | Edge runtime (Workers) | No filesystem, limited packages |

```python
# Run on edge (fast, close to user)
@route_config(runtime="edge", max_duration=10)
@api_route
async def geo_lookup(request):
    # Minimal code for speed
    return JSONResponse({"region": detect_region(request)})
```

#### `max_duration` - Timeout

Maximum execution time in seconds:

```python
# Long-running computation
@route_config(max_duration=120)  # 2 minutes
@api_route
async def generate_report(request):
    return await build_large_report()
```

#### `preferred_region` - Deployment Hint

```python
# Run in specific regions
@route_config(
    runtime="edge",
    preferred_region=["us-east-1", "eu-west-1"]
)
@api_route
async def fast_api(request):
    ...
```

---

## Convenience Shortcuts

For common patterns, use shortcuts instead of the full decorator:

### `@static_route`

```python
from pynext import static_route

@static_route(revalidate=3600)  # 1-hour ISR
@page
def BlogPage():
    return posts()

# Equivalent to:
# @route_config(dynamic="static", revalidate=3600)
```

### `@dynamic_route`

```python
from pynext import dynamic_route

@dynamic_route()  # Always fresh, no cache
@page
def DashboardPage():
    return dashboard()

# Equivalent to:
# @route_config(dynamic="force", cache="no-store")
```

### `@edge_route`

```python
from pynext import edge_route

@edge_route(max_duration=10)
@api_route
async def fast_api(request):
    return quick_response()

# Equivalent to:
# @route_config(runtime="edge", max_duration=10)
```

### `@cached_route`

```python
from pynext import cached_route

@cached_route(300, tags=["data"])  # 5 min cache
@page
def DataPage():
    return data()

# Equivalent to:
# @route_config(revalidate=300, tags=["data"])
```

### `@no_cache_route`

```python
from pynext import no_cache_route

@no_cache_route()
@api_route
async def realtime(request):
    return live_data()

# Equivalent to:
# @route_config(cache="no-store")
```

---

## Real-World Patterns

### E-commerce Product Page

```python
# pages/products/[id]/page.py
from pynext import page, route_config

@route_config(
    revalidate=300,           # Refresh every 5 min
    tags=["products"],        # For on-demand invalidation
    dynamic_params=True,      # Allow any product ID
)
@page
def ProductPage(id: str):
    product = fetch_product(id)
    
    if not product:
        raise NotFoundError(f"Product {id} not found")
    
    return div(
        ProductGallery(product.images),
        ProductInfo(product),
        AddToCart(product.id),
    )
```

### Dashboard with Auth

```python
# pages/dashboard/page.py
from pynext import page, route_config, unauthorized

@route_config(
    dynamic="force",     # Always render fresh
    cache="no-store",    # Never cache (user-specific)
    max_duration=30,     # 30s timeout
)
@page
def DashboardPage():
    user = get_current_user()
    
    if not user:
        unauthorized("Please sign in")
    
    return Dashboard(
        UserStats(user.id),
        RecentActivity(user.id),
        Notifications(user.id),
    )
```

### Blog with ISR

```python
# pages/blog/[slug]/page.py
from pynext import page, route_config

@route_config(
    revalidate=3600,          # Hourly refresh
    tags=["blog", "posts"],   # Multiple tags
)
@page
def BlogPost(slug: str):
    post = fetch_post(slug)
    
    return article(
        h1(post.title),
        Metadata(author=post.author, date=post.date),
        Markdown(post.content),
        Comments(post.id),
    )
```

### Fast API Endpoint

```python
# pages/api/search/route.py
from pynext import api_route, route_config

@route_config(
    dynamic="force",
    cache="no-store",
    max_duration=10,     # Fast timeout
)
@api_route
async def search(request):
    query = request.query_params.get("q", "")
    
    if not query:
        return JSONResponse({"results": []})
    
    results = await search_index(query)
    
    return JSONResponse({
        "query": query,
        "results": results[:20],
    })
```

### Edge Geolocation

```python
# pages/api/geo/route.py
from pynext import api_route, route_config, Runtime

@route_config(
    runtime=Runtime.EDGE,
    max_duration=5,
    preferred_region=["auto"],  # All regions
)
@api_route
async def geo(request):
    # Available in edge runtime
    country = request.headers.get("cf-ipcountry", "US")
    city = request.headers.get("cf-ipcity", "")
    
    return JSONResponse({
        "country": country,
        "city": city,
        "timestamp": time.time(),
    })
```

---

## Under the Hood

### How Config Flows to Response

```
1. Import Time
   ─────────────
   @route_config decorator creates RouteConfig object
   Stores on function as __route_config__ attribute
   Registers in global registry for lookup
   
2. Startup (router.scan())
   ────────────────────────
   FileRouter loads each page module
   Extracts RouteConfig from handler
   Stores config on Route object
   Registers config by path
   
3. Request Time
   ─────────────
   Server matches route
   Gets config from route.config
   Generates cache headers
   Returns response with headers

                    Performance: Zero overhead
                    ──────────────────────────
   Config parsing:   Import time (once)
   Config lookup:    O(1) dict access
   Header generation: Pre-computed method
```

### Generated Headers

```python
config = RouteConfig(revalidate=60, tags=["products"])
headers = config.to_headers()

# Result:
{
    "Cache-Control": "public, s-maxage=60, stale-while-revalidate",
    "X-Cache-Tags": "products"
}
```

### Integration with ISR

Route config's `revalidate` integrates with PyNext's ISR system:

```python
@route_config(revalidate=60, tags=["products"])
@page
def ProductPage(id: str):
    ...

# The ISR system will:
# 1. Serve cached version immediately
# 2. Trigger background regeneration after 60s
# 3. Store new version in cache
# 4. Support on-demand invalidation via tags
```

---

## Comparison with Next.js

### Syntax Comparison

| Aspect | Next.js | PyNext |
|--------|---------|--------|
| **Location** | Module-level exports | Decorator on function |
| **Syntax** | `export const dynamic = '...'` | `@route_config(dynamic="...")` |
| **Type Safety** | None (strings) | Enums with IDE autocomplete |
| **Validation** | Runtime | Import time |
| **Centralization** | Scattered exports | Single decorator |

### Side-by-Side

```javascript
// Next.js (JavaScript)
export const dynamic = 'force-dynamic'
export const revalidate = 60
export const runtime = 'edge'
export const preferredRegion = ['us-east-1', 'eu-west-1']

export default function Page({ params }) {
  const product = await fetchProduct(params.id)
  return <Product data={product} />
}
```

```python
# PyNext (Python)
@route_config(
    dynamic="force",
    revalidate=60,
    runtime="edge",
    preferred_region=["us-east-1", "eu-west-1"],
)
@page
def Page(id: str):
    product = fetch_product(id)
    return Product(product)
```

### Advantages Over Next.js

| Feature | Next.js | PyNext |
|---------|---------|--------|
| Config location | Scattered in file | Single decorator |
| Validation | Runtime error | Import-time error |
| IDE support | Basic | Full autocomplete |
| Type safety | No | Yes (enums) |
| Parsing | Each request | Once at import |
| Learning curve | Multiple patterns | One pattern |

---

## Performance

| Operation | Next.js | PyNext | Improvement |
|-----------|---------|--------|-------------|
| Config parse | Runtime (each request) | Import time (once) | **~1000x faster** |
| Config lookup | String comparison | O(1) dict | **Constant time** |
| Validation | Runtime error | Import error | **Fail fast** |
| Header generation | Computed | Method call | **Pre-optimized** |

### Why So Fast?

1. **Import-time parsing**: Config is parsed once when module loads
2. **Enum validation**: Invalid values caught at import, not runtime
3. **Dict registry**: O(1) lookup by path or function ID
4. **Pre-computed headers**: `to_headers()` is a simple method call

---

## Troubleshooting

### Config Not Applied

**Symptom**: Page doesn't respect config settings.

**Check**:
1. Decorator is above `@page` decorator
2. Config imported from `pynext`
3. Route is being matched correctly

```python
# ✅ Correct order
@route_config(dynamic="force")
@page
def MyPage():
    ...

# ❌ Wrong order - config won't be found
@page
@route_config(dynamic="force")
def MyPage():
    ...
```

### Invalid Dynamic Mode

**Error**: `ValueError: Invalid dynamic mode: 'invalid'`

**Fix**: Use valid values: `"auto"`, `"force"`, `"error"`, `"static"`

```python
# ❌ Invalid
@route_config(dynamic="always")

# ✅ Valid
@route_config(dynamic="force")
```

### Cache Not Working

**Symptom**: Page always renders fresh despite `revalidate`.

**Check**:
1. `cache` is not `"no-store"`
2. `dynamic` is not `"force"` (unless `cache="force"`)
3. CDN/proxy configured to respect `Cache-Control` headers

### Edge Runtime Errors

**Symptom**: Page fails on edge runtime.

**Common causes**:
1. Using filesystem operations
2. Using unsupported Python packages
3. Exceeding `max_duration`

```python
# ❌ Won't work on edge
@route_config(runtime="edge")
@page
def Page():
    data = open("file.txt").read()  # No filesystem on edge
    return div(data)

# ✅ Works on edge
@route_config(runtime="edge")
@page
def Page():
    data = fetch_from_api()  # API calls work
    return div(data)
```

---

## Best Practices

### 1. Start with Defaults

```python
# Let PyNext decide until you need control
@page
def MyPage():
    return content()
```

### 2. Use Shortcuts for Common Patterns

```python
# ❌ Verbose
@route_config(dynamic="static", revalidate=3600)

# ✅ Clear intent
@static_route(revalidate=3600)
```

### 3. Tag Everything for Invalidation

```python
@route_config(revalidate=3600, tags=["products", f"category:{cat_id}"])
@page
def ProductPage(id: str):
    ...
```

### 4. Set Appropriate Timeouts

```python
# Fast endpoints
@route_config(max_duration=10)

# Long computations
@route_config(max_duration=120)
```

### 5. Use Enums for Type Safety

```python
from pynext import Dynamic, Cache, Runtime

@route_config(
    dynamic=Dynamic.FORCE,
    cache=Cache.NO_STORE,
    runtime=Runtime.EDGE,
)
```

---

## Summary

| What | How |
|------|-----|
| Static page | `@route_config(dynamic="static")` |
| ISR (every hour) | `@route_config(revalidate=3600)` |
| Always fresh | `@route_config(dynamic="force", cache="no-store")` |
| Edge runtime | `@route_config(runtime="edge")` |
| Cache tags | `@route_config(tags=["products"])` |
| Fast shortcut | `@static_route()`, `@dynamic_route()`, etc. |

**One decorator. All options. Zero runtime overhead.**

That's route segment configuration in PyNext.

