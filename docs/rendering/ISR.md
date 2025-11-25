# PyNext Incremental Static Regeneration (ISR)

> **Serve static pages with dynamic freshness—automatically regenerate content without rebuilding your entire site.**

ISR combines the speed of static sites with the flexibility of dynamic rendering. Pages are served instantly from cache, then regenerated in the background when stale.

---

## Table of Contents

1. [What is ISR?](#what-is-isr)
2. [The Mental Model](#the-mental-model)
3. [Quick Start](#quick-start)
4. [Core Concepts](#core-concepts)
5. [Revalidation Strategies](#revalidation-strategies)
6. [Invalidation Scopes](#invalidation-scopes)
7. [On-Demand Revalidation](#on-demand-revalidation)
8. [Cache Architecture](#cache-architecture)
9. [Real-World Examples](#real-world-examples)
10. [Performance](#performance)
11. [Best Practices](#best-practices)
12. [Debugging](#debugging)
13. [API Reference](#api-reference)

---

## What is ISR?

### The Elevator Pitch

**Incremental Static Regeneration** lets you create or update static pages *after* you've built your site. Instead of rebuilding everything when content changes, only the affected pages regenerate—automatically, in the background.

### The Three Rendering Strategies

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          RENDERING STRATEGIES                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   1. STATIC SITE GENERATION (SSG)                                           │
│   ────────────────────────────────                                          │
│                                                                              │
│   Build Time                           Runtime                               │
│   ──────────                           ───────                               │
│   Generate all pages  ───────────────► Serve from cache (instant!)          │
│   └── /products/1                      └── But... content never updates! 😢 │
│   └── /products/2                                                           │
│   └── /products/...1000                                                     │
│                                                                              │
│   ✓ Super fast                         ✗ Stale content                      │
│   ✓ Great for SEO                      ✗ Must rebuild for changes           │
│   ✗ Slow builds (1000s of pages)                                           │
│                                                                              │
│                                                                              │
│   2. SERVER-SIDE RENDERING (SSR)                                            │
│   ──────────────────────────────                                            │
│                                                                              │
│   Build Time                           Runtime                               │
│   ──────────                           ───────                               │
│   Nothing special     ───────────────► Render on every request              │
│                                        └── Always fresh! 😊                 │
│                                        └── But... slow! 😢                  │
│                                                                              │
│   ✓ Always fresh content               ✗ Slower TTFB                        │
│   ✓ No stale data                      ✗ Higher server load                 │
│   ✗ No caching benefits                                                     │
│                                                                              │
│                                                                              │
│   3. INCREMENTAL STATIC REGENERATION (ISR) ⭐                               │
│   ───────────────────────────────────────────                               │
│                                                                              │
│   Build Time                           Runtime                               │
│   ──────────                           ───────                               │
│   Generate initial    ───────────────► Serve from cache (instant!)          │
│   pages                                     │                                │
│                                             ▼                                │
│                                        Is page stale?                        │
│                                        ├── No: Serve cached                 │
│                                        └── Yes: Serve cached +              │
│                                                 Regenerate in background    │
│                                                                              │
│   ✓ Fast like static                   ✓ Fresh like SSR                     │
│   ✓ Great for SEO                      ✓ Low server load                    │
│   ✓ No full rebuilds                   ✓ Handles traffic spikes             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### PyNext ISR vs Next.js ISR

| Feature | Next.js | PyNext |
|---------|---------|--------|
| **Granularity** | Page-level | **Component-level** |
| **Invalidation** | Time-based | **Time, tag, signal, resource** |
| **Regeneration** | Full page | **Partial (changed only)** |
| **Cache Keys** | Route-based | **Signal/Resource-based** |

---

## The Mental Model

### First Principles: The Library Analogy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          THE LIBRARY ANALOGY                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   Think of your website as a LIBRARY:                                       │
│                                                                              │
│   BOOKS = Your rendered pages                                               │
│   LIBRARIAN = ISR cache system                                              │
│   PUBLISHER = Your data sources (CMS, database, API)                        │
│                                                                              │
│                                                                              │
│   WITHOUT ISR (SSR):                                                        │
│   ──────────────────                                                        │
│                                                                              │
│   Visitor: "I'd like the Products page"                                     │
│   Librarian: "Let me write that book right now..."                          │
│              *writes for 500ms*                                              │
│              "Here you go!"                                                  │
│                                                                              │
│   Every visitor waits for the book to be written. 😴                        │
│                                                                              │
│                                                                              │
│   WITH ISR:                                                                 │
│   ─────────                                                                 │
│                                                                              │
│   Visitor 1: "I'd like the Products page"                                   │
│   Librarian: "Here's our copy!" (instant)                                   │
│              *checks timestamp: "This is 30min old, I'll update it"*        │
│              *starts writing new version in backroom*                        │
│                                                                              │
│   Visitor 2 (5 sec later): "I'd like the Products page"                     │
│   Librarian: "Here's our copy!" (instant - same old version)                │
│                                                                              │
│   Visitor 3 (60 sec later): "I'd like the Products page"                    │
│   Librarian: "Here's our FRESH copy!" (instant - newly written version)     │
│                                                                              │
│   Everyone gets books instantly! Fresh books written in background! 🎉      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Stale-While-Revalidate

The core principle of ISR is **Stale-While-Revalidate**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       STALE-WHILE-REVALIDATE FLOW                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   TIMELINE                                                                  │
│   ────────                                                                  │
│                                                                              │
│   0s         60s        120s       180s       240s                          │
│   │          │          │          │          │                             │
│   ▼          ▼          ▼          ▼          ▼                             │
│   ┌──────────────────────────────────────────────────────────────────────┐  │
│   │                                                                       │  │
│   │  Page generated                                                       │  │
│   │  revalidate=60 seconds                                               │  │
│   │                                                                       │  │
│   │  0-60s:  FRESH                                                        │  │
│   │          └── Serve cached, no background work                         │  │
│   │                                                                       │  │
│   │  60s+:   STALE                                                        │  │
│   │          └── Serve cached (still fast!)                               │  │
│   │          └── Trigger background regeneration                          │  │
│   │                                                                       │  │
│   │  After regen completes: Cache updated                                │  │
│   │          └── Next request gets fresh content                          │  │
│   │                                                                       │  │
│   └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│                                                                              │
│   REQUEST FLOW:                                                             │
│   ─────────────                                                             │
│                                                                              │
│   Request @ 30s  ──► Cache: FRESH ──► Return cached (instant) ✓            │
│                                                                              │
│   Request @ 90s  ──► Cache: STALE ──┬► Return cached (instant) ✓           │
│                                     └► Background: Regenerate              │
│                                                                              │
│   Request @ 100s ──► Cache: FRESH ──► Return NEW cached (instant) ✓        │
│                      (regeneration completed)                               │
│                                                                              │
│                                                                              │
│   KEY INSIGHT: Users NEVER wait for regeneration!                           │
│                They always get cached content instantly.                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Time-Based Revalidation

```python
from pynext import revalidate, page, div, h1

@revalidate(seconds=60)  # Regenerate after 60 seconds
@page
def products():
    """This page revalidates every 60 seconds."""
    products = fetch_products()  # Expensive database call
    
    return div()[
        h1()["Our Products"],
        [ProductCard(p) for p in products]
    ]
```

### What Happens

```
First Request (cache miss):
├── Page renders (500ms)
├── HTML cached
├── Response sent (500ms total)
└── Cache TTL: 60 seconds

Requests 2-100 (within 60s):
├── Cache hit!
├── Response sent (~5ms)
└── No rendering needed

Request 101 (after 60s):
├── Cache: STALE
├── Return stale content (~5ms) ←── User doesn't wait!
└── Background: Regenerate page

Request 102+:
├── Fresh content served (~5ms)
└── New 60s TTL starts
```

---

## Core Concepts

### 1. Time-Based Revalidation

The simplest form—regenerate after a time interval:

```python
from pynext import revalidate

@revalidate(seconds=60)  # 1 minute
def frequently_updated():
    """News feed, stock prices, etc."""
    ...

@revalidate(seconds=3600)  # 1 hour
def moderately_updated():
    """Blog posts, product listings, etc."""
    ...

@revalidate(seconds=86400)  # 24 hours
def rarely_updated():
    """About page, terms of service, etc."""
    ...
```

### 2. Tag-Based Invalidation

Group related content with tags for bulk invalidation:

```python
from pynext import revalidate, revalidate_tag

# Multiple pages share the "products" tag
@revalidate(tags=["products", "featured"])
def featured_products():
    return div()[ProductGrid(fetch_featured())]

@revalidate(tags=["products", "catalog"])
def product_catalog():
    return div()[ProductList(fetch_all())]

@revalidate(tags=["products"])
def product_page(product_id):
    return div()[ProductDetail(fetch_product(product_id))]

# When a product changes, invalidate ALL pages with "products" tag:
await revalidate_tag("products")
# → featured_products, product_catalog, product_page all regenerate!
```

### 3. Component-Level Revalidation

PyNext's superpower: Only regenerate the specific component that changed, not the entire page!

```python
from pynext import revalidate, InvalidationScope, page

# This component revalidates independently
@revalidate(seconds=60, scope=InvalidationScope.COMPONENT)
def ProductPrice(product_id):
    """Only this component regenerates, not the whole page!"""
    price = fetch_price(product_id)
    return span(class_="price")[f"${price}"]

@revalidate(seconds=3600, scope=InvalidationScope.COMPONENT)
def ProductReviews(product_id):
    """Reviews update hourly."""
    reviews = fetch_reviews(product_id)
    return div(class_="reviews")[
        [ReviewCard(r) for r in reviews]
    ]

# The page uses these components
@revalidate(seconds=86400)  # Page structure rarely changes
@page
def product_page(product_id):
    product = fetch_product(product_id)
    
    return div()[
        h1()[product.name],           # Static from page cache
        ProductPrice(product_id),      # Revalidates every 60s
        p()[product.description],      # Static from page cache
        ProductReviews(product_id),    # Revalidates every hour
    ]
```

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       COMPONENT-LEVEL REVALIDATION                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   PAGE: /products/123                                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  ┌─────────────────────────────────────────────────────────────┐    │   │
│   │  │  HEADER (static, revalidates: 24h)                          │    │   │
│   │  └─────────────────────────────────────────────────────────────┘    │   │
│   │  ┌─────────────────────────────────────────────────────────────┐    │   │
│   │  │  PRODUCT NAME (static, revalidates: 24h)                    │    │   │
│   │  └─────────────────────────────────────────────────────────────┘    │   │
│   │  ┌─────────────────────────────────────────────────────────────┐    │   │
│   │  │  💰 PRODUCT PRICE (component, revalidates: 60s)             │    │   │
│   │  │      └── Only THIS regenerates when price changes!         │    │   │
│   │  └─────────────────────────────────────────────────────────────┘    │   │
│   │  ┌─────────────────────────────────────────────────────────────┐    │   │
│   │  │  DESCRIPTION (static, revalidates: 24h)                     │    │   │
│   │  └─────────────────────────────────────────────────────────────┘    │   │
│   │  ┌─────────────────────────────────────────────────────────────┐    │   │
│   │  │  ⭐ REVIEWS (component, revalidates: 1h)                    │    │   │
│   │  │      └── Only THIS regenerates when reviews change!        │    │   │
│   │  └─────────────────────────────────────────────────────────────┘    │   │
│   │  ┌─────────────────────────────────────────────────────────────┐    │   │
│   │  │  FOOTER (static, revalidates: 24h)                          │    │   │
│   │  └─────────────────────────────────────────────────────────────┘    │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│   RESULT: 80% of page served from cache, only changed parts regenerate!     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4. On-Demand Revalidation

Don't wait for TTL—trigger revalidation immediately when content changes:

```python
from pynext import revalidate_path, revalidate_tag, revalidate_component

# CMS webhook handler
@api_route
async def POST(request):
    data = await request.json()
    
    if data["event"] == "product.updated":
        product_id = data["product_id"]
        
        # Revalidate the specific product page
        await revalidate_path(f"/products/{product_id}")
        
    elif data["event"] == "inventory.changed":
        # Revalidate all pages with "products" tag
        await revalidate_tag("products")
        
    elif data["event"] == "price.changed":
        # Revalidate just the price component everywhere
        await revalidate_component("ProductPrice")
    
    return {"revalidated": True}
```

---

## Revalidation Strategies

### Strategy Comparison

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       REVALIDATION STRATEGIES                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   STRATEGY          WHEN TO USE                        EXAMPLE              │
│   ────────          ───────────                        ───────              │
│                                                                              │
│   TIME-BASED        Regular update frequency           Stock prices (1min)  │
│   seconds=60        Known freshness requirements       Blog posts (1hr)     │
│                     Simple to implement                News (5min)          │
│                                                                              │
│   TAG-BASED         Related content groups             Products + catalog   │
│   tags=["..."]      CMS-driven content                 Blog + categories    │
│                     Bulk invalidation needed           User profiles        │
│                                                                              │
│   ON-DEMAND         Webhooks from CMS/database         Content publish      │
│   revalidate_*()    User-triggered updates             Profile save         │
│                     Event-driven freshness             Order completion     │
│                                                                              │
│   COMPONENT         Mixed freshness on same page       Price + description  │
│   scope=COMPONENT   Expensive components               Reviews + ratings    │
│                     Independent update cycles          Stats + content      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Combining Strategies

```python
from pynext import revalidate, InvalidationScope

@revalidate(
    seconds=3600,                          # Fallback: revalidate hourly
    tags=["products", "featured"],         # Bulk invalidation via tags
    scope=InvalidationScope.COMPONENT,     # Only regenerate this component
)
def FeaturedProducts():
    """
    Revalidation strategy:
    1. Automatically every hour (seconds=3600)
    2. When "products" or "featured" tag is invalidated
    3. Only this component regenerates, not the full page
    """
    products = fetch_featured_products()
    return div()[ProductGrid(products)]
```

---

## Invalidation Scopes

### Available Scopes

```python
from pynext import InvalidationScope

# PAGE (default): Regenerate entire page
@revalidate(scope=InvalidationScope.PAGE)

# COMPONENT: Only regenerate this component
@revalidate(scope=InvalidationScope.COMPONENT)

# RESOURCE: Tied to a Resource's refetch
@revalidate(scope=InvalidationScope.RESOURCE)

# TAG: Invalidate via tag groups
@revalidate(scope=InvalidationScope.TAG, tags=["products"])
```

### Scope Comparison

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          INVALIDATION SCOPES                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   PAGE SCOPE (Traditional)                                                  │
│   ────────────────────────                                                  │
│                                                                              │
│   When ProductPrice stales → Entire page regenerates                        │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────┐       │
│   │ [Header     ] ─┐                                                 │       │
│   │ [Title      ] ─┤                                                 │       │
│   │ [Price  💰  ] ─┼── ALL regenerate together (expensive!)         │       │
│   │ [Description] ─┤                                                 │       │
│   │ [Reviews    ] ─┤                                                 │       │
│   │ [Footer     ] ─┘                                                 │       │
│   └─────────────────────────────────────────────────────────────────┘       │
│                                                                              │
│   Work done: 100% of page                                                   │
│                                                                              │
│                                                                              │
│   COMPONENT SCOPE (PyNext Innovation)                                       │
│   ────────────────────────────────────                                      │
│                                                                              │
│   When ProductPrice stales → Only ProductPrice regenerates                  │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────┐       │
│   │ [Header     ] ← cached                                          │       │
│   │ [Title      ] ← cached                                          │       │
│   │ [Price  💰  ] ← REGENERATES (just this!)                        │       │
│   │ [Description] ← cached                                          │       │
│   │ [Reviews    ] ← cached                                          │       │
│   │ [Footer     ] ← cached                                          │       │
│   └─────────────────────────────────────────────────────────────────┘       │
│                                                                              │
│   Work done: 5% of page                                                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## On-Demand Revalidation

### API Endpoints

PyNext provides built-in revalidation endpoints:

```bash
# Revalidate a specific path
curl -X POST http://localhost:3000/api/revalidate/path \
  -H "x-revalidate-token: your-secret-token" \
  -d '{"path": "/products/123"}'

# Revalidate by tag
curl -X POST http://localhost:3000/api/revalidate/tag \
  -H "x-revalidate-token: your-secret-token" \
  -d '{"tag": "products"}'

# Revalidate a component everywhere
curl -X POST http://localhost:3000/api/revalidate/component \
  -H "x-revalidate-token: your-secret-token" \
  -d '{"component": "ProductPrice"}'

# Get cache stats
curl http://localhost:3000/api/revalidate/stats \
  -H "x-revalidate-token: your-secret-token"
```

### CMS Webhook Integration

```python
# pages/api/cms-webhook/route.py

from pynext import api_route, revalidate_path, revalidate_tag
import hmac
import hashlib

WEBHOOK_SECRET = "your-cms-webhook-secret"

def verify_signature(payload: bytes, signature: str) -> bool:
    """Verify webhook signature from CMS."""
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

@api_route
async def POST(request):
    # Verify webhook authenticity
    signature = request.headers.get("x-webhook-signature", "")
    body = await request.body()
    
    if not verify_signature(body, signature):
        return {"error": "Invalid signature"}, 401
    
    data = await request.json()
    
    # Handle different CMS events
    event_type = data.get("event")
    
    if event_type == "entry.publish":
        content_type = data.get("content_type")
        entry_id = data.get("entry_id")
        
        if content_type == "product":
            await revalidate_path(f"/products/{entry_id}")
            await revalidate_tag("products")  # Also update listings
            
        elif content_type == "blog_post":
            slug = data.get("slug")
            await revalidate_path(f"/blog/{slug}")
            await revalidate_tag("blog")  # Update blog listing
            
        elif content_type == "homepage":
            await revalidate_path("/")
    
    elif event_type == "entry.unpublish":
        # Clear from cache
        await revalidate_path(data.get("url"))
    
    elif event_type == "bulk.publish":
        # Multiple entries published
        await revalidate_tag(data.get("content_type"))
    
    return {"revalidated": True, "event": event_type}
```

### Programmatic Revalidation

```python
from pynext import revalidate_path, revalidate_tag, revalidate_component

# In a server action after user saves data
@server_action
async def save_product(product_id: int, data: dict):
    # Save to database
    await db.products.update(product_id, data)
    
    # Revalidate affected pages
    await revalidate_path(f"/products/{product_id}")
    
    # If it's a featured product, also revalidate homepage
    if data.get("is_featured"):
        await revalidate_tag("featured")
    
    return {"saved": True}

# Batch revalidation
@server_action
async def bulk_update_prices(updates: list):
    for update in updates:
        await db.products.update_price(update["id"], update["price"])
    
    # Revalidate all product pages at once
    await revalidate_tag("products")
    
    return {"updated": len(updates)}
```

---

## Cache Architecture

### How the Cache Works

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CACHE ARCHITECTURE                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ISRCache                                                                  │
│   ────────                                                                  │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                        IN-MEMORY CACHE                               │   │
│   │  (Fast reads, limited by RAM)                                       │   │
│   │                                                                      │   │
│   │  Key                          Value                                  │   │
│   │  ───                          ─────                                  │   │
│   │  /products                    {html, created_at, config}            │   │
│   │  /products/123                {html, created_at, config}            │   │
│   │  /blog/hello-world            {html, created_at, config}            │   │
│   │                                                                      │   │
│   └─────────────────────────────────┬───────────────────────────────────┘   │
│                                     │                                        │
│                                     │ Persisted to                          │
│                                     ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                        DISK CACHE                                    │   │
│   │  (Survives restarts, larger capacity)                               │   │
│   │                                                                      │   │
│   │  ./cache/                                                            │   │
│   │  ├── _products.html                                                  │   │
│   │  ├── _products_123.html                                              │   │
│   │  ├── _blog_hello-world.html                                          │   │
│   │  └── _metadata.json                                                  │   │
│   │                                                                      │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│                                                                              │
│   CACHE ENTRY STRUCTURE:                                                    │
│   ──────────────────────                                                    │
│                                                                              │
│   CacheEntry {                                                              │
│       key: "/products/123"                                                  │
│       content: "<html>...</html>"                                           │
│       created_at: 1700000000.0                                              │
│       config: {                                                             │
│           seconds: 60,                                                      │
│           tags: ["products"],                                               │
│           scope: "page",                                                    │
│           component: null                                                   │
│       }                                                                     │
│   }                                                                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Cache Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CACHE REQUEST FLOW                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   Request: GET /products/123                                                │
│        │                                                                     │
│        ▼                                                                     │
│   ┌────────────────────────────────────────────────────────────────────┐    │
│   │  ISRMiddleware.dispatch()                                          │    │
│   └────────────────────────────────────────────────────────────────────┘    │
│        │                                                                     │
│        ▼                                                                     │
│   ┌────────────────────────────────────────────────────────────────────┐    │
│   │  Generate cache key                                                 │    │
│   │  key = "/products/123" + query_params + locale                     │    │
│   └────────────────────────────────────────────────────────────────────┘    │
│        │                                                                     │
│        ▼                                                                     │
│   ┌────────────────────────────────────────────────────────────────────┐    │
│   │  cache.get(key)                                                     │    │
│   └────────────────────────────────────────────────────────────────────┘    │
│        │                                                                     │
│        ├───────────────────────────────────────────────────────┐            │
│        │ Entry exists?                                         │            │
│        │                                                        │            │
│        ▼ YES                                                   ▼ NO         │
│   ┌──────────────────┐                                  ┌──────────────────┐│
│   │ Check freshness  │                                  │ CACHE MISS       ││
│   │ now - created_at │                                  │                  ││
│   │ vs config.seconds│                                  │ • Render page    ││
│   └────────┬─────────┘                                  │ • Cache result   ││
│            │                                            │ • Return HTML    ││
│   ┌────────┴────────┐                                   │                  ││
│   │                 │                                   │ Header:          ││
│   ▼ FRESH           ▼ STALE                             │ X-Cache: miss    ││
│   ┌───────────┐    ┌───────────────────────────┐        └──────────────────┘│
│   │ Return    │    │ Return cached (stale)      │                           │
│   │ cached    │    │ + Queue for regeneration   │                           │
│   │           │    │                            │                           │
│   │ Header:   │    │ Header:                    │                           │
│   │ X-Cache:  │    │ X-Cache: stale             │                           │
│   │ hit       │    │                            │                           │
│   └───────────┘    └─────────────┬──────────────┘                           │
│                                  │                                           │
│                                  ▼                                           │
│                    ┌───────────────────────────┐                            │
│                    │ Background Regeneration   │                            │
│                    │ Worker picks up task      │                            │
│                    │ Renders fresh content     │                            │
│                    │ Updates cache             │                            │
│                    └───────────────────────────┘                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Server Setup

```python
from fastapi import FastAPI
from pynext.server.isr import add_isr_middleware

app = FastAPI()

# This adds:
# - ISRMiddleware for automatic caching
# - /api/revalidate/* endpoints
# - Background regeneration worker

cache, worker = add_isr_middleware(
    app,
    cache_dir="./cache",           # Where to store cached pages
    secret_token="your-secret",    # For revalidation API auth
)

# Access cache directly if needed
print(cache.get_stats())
# {
#   "total_entries": 42,
#   "stale_entries": 3,
#   "tags": ["products", "blog", "featured"],
#   "disk_size_mb": 12.5
# }
```

---

## Real-World Examples

### E-Commerce Product Pages

```python
from pynext import revalidate, revalidate_tag, page, InvalidationScope

# Price updates frequently
@revalidate(seconds=60, scope=InvalidationScope.COMPONENT, tags=["prices"])
def ProductPrice(product_id):
    price = fetch_current_price(product_id)
    return div(class_="price")[
        span(class_="current")[f"${price.current}"],
        price.was_price and span(class_="was")[f"Was ${price.was_price}"]
    ]

# Stock updates in real-time
@revalidate(seconds=30, scope=InvalidationScope.COMPONENT, tags=["inventory"])
def StockStatus(product_id):
    stock = fetch_stock(product_id)
    if stock == 0:
        return span(class_="out-of-stock")["Out of Stock"]
    elif stock < 10:
        return span(class_="low-stock")[f"Only {stock} left!"]
    else:
        return span(class_="in-stock")["In Stock"]

# Reviews update hourly
@revalidate(seconds=3600, scope=InvalidationScope.COMPONENT, tags=["reviews"])
def ProductReviews(product_id):
    reviews = fetch_reviews(product_id)
    return div(class_="reviews")[
        div(class_="summary")[
            f"⭐ {reviews.average_rating}/5 ({reviews.count} reviews)"
        ],
        [ReviewCard(r) for r in reviews.recent[:5]]
    ]

# Main page structure rarely changes
@revalidate(seconds=86400, tags=["products"])
@page
def product_page(product_id):
    product = fetch_product(product_id)
    
    return div(class_="product-page")[
        # Static content (cached 24h)
        h1()[product.name],
        img(src=product.image, alt=product.name),
        
        # Dynamic components with their own cache
        ProductPrice(product_id),      # Updates every minute
        StockStatus(product_id),       # Updates every 30 seconds
        
        # Static content
        div(class_="description")[product.description],
        
        # Dynamic component
        ProductReviews(product_id),    # Updates hourly
    ]
```

### Blog with CMS

```python
from pynext import revalidate, revalidate_path, page

@revalidate(seconds=3600, tags=["blog", "posts"])
@page
def blog_listing():
    posts = fetch_recent_posts(limit=20)
    return div(class_="blog")[
        h1()["Blog"],
        [PostCard(p) for p in posts]
    ]

@revalidate(seconds=86400, tags=["blog"])  # Rarely changes
@page
def blog_post(slug):
    post = fetch_post_by_slug(slug)
    return article(class_="blog-post")[
        h1()[post.title],
        div(class_="meta")[
            f"By {post.author} • {post.date}"
        ],
        div(class_="content", dangerouslySetInnerHTML=post.html),
    ]

# CMS webhook when post is published/updated
@api_route
async def POST(request):
    data = await request.json()
    
    if data["event"] == "post.published":
        # Revalidate the specific post
        await revalidate_path(f"/blog/{data['slug']}")
        # Also revalidate the listing
        await revalidate_tag("posts")
        
    return {"ok": True}
```

### Dashboard with Real-Time Stats

```python
from pynext import revalidate, InvalidationScope

# Stats update every 10 seconds
@revalidate(seconds=10, scope=InvalidationScope.COMPONENT)
def LiveStats():
    stats = fetch_realtime_stats()
    return div(class_="live-stats")[
        StatCard("Active Users", stats.active_users, trend=stats.user_trend),
        StatCard("Orders/min", stats.orders_per_minute),
        StatCard("Revenue Today", f"${stats.revenue_today:,.2f}"),
    ]

# Charts update every minute
@revalidate(seconds=60, scope=InvalidationScope.COMPONENT)
def RevenueChart():
    data = fetch_revenue_data(days=30)
    return div(class_="chart")[
        Chart(type="line", data=data)
    ]

# Top products update every 5 minutes
@revalidate(seconds=300, scope=InvalidationScope.COMPONENT)
def TopProducts():
    products = fetch_top_products(limit=10)
    return div(class_="top-products")[
        h3()["Top Products"],
        [ProductRow(p) for p in products]
    ]

@page
def dashboard():
    return div(class_="dashboard")[
        h1()["Dashboard"],
        LiveStats(),       # Every 10s
        RevenueChart(),    # Every minute
        TopProducts(),     # Every 5 minutes
    ]
```

---

## Performance

### Metrics

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PERFORMANCE COMPARISON                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   SCENARIO: Product page with price, stock, reviews                         │
│                                                                              │
│   METRIC               SSR          ISR (Page)    ISR (Component)           │
│   ──────               ───          ──────────    ───────────────           │
│                                                                              │
│   Time to First Byte   500ms        5ms           5ms                       │
│   Cache Hit Rate       0%           95%           99%                       │
│   Server Load          High         Medium        Low                       │
│   Content Freshness    Real-time    60s stale     Mixed (10s-1h)           │
│                                                                              │
│   Regeneration Work:                                                        │
│   • SSR:            100% every request                                      │
│   • ISR (Page):     100% every 60 seconds                                  │
│   • ISR (Component): 5-20% (only changed components)                       │
│                                                                              │
│                                                                              │
│   TRAFFIC HANDLING:                                                         │
│   ─────────────────                                                         │
│                                                                              │
│   Requests/sec     SSR Load      ISR Load        Savings                   │
│   ────────────     ────────      ────────        ───────                   │
│   10               100%          5%              95%                        │
│   100              1000%         5%              99.5%                      │
│   1000             10000%        5%              99.95%                     │
│                                                                              │
│   ISR handles traffic spikes gracefully!                                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Cache Headers

ISR adds proper cache headers for CDN/edge caching:

```
HTTP/1.1 200 OK
Cache-Control: public, s-maxage=60, stale-while-revalidate=3600
ETag: "abc123"
X-PyNext-Cache: hit
```

| Header | Purpose |
|--------|---------|
| `s-maxage` | CDN cache duration |
| `stale-while-revalidate` | Serve stale while regenerating |
| `ETag` | Cache validation |
| `X-PyNext-Cache` | Debug: hit/miss/stale |

---

## Best Practices

### Do's and Don'ts

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ISR BEST PRACTICES                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ✓ DO                                                                      │
│   ────                                                                      │
│                                                                              │
│   ✓ Use tags for related content groups                                    │
│     @revalidate(tags=["products", "catalog"])                               │
│                                                                              │
│   ✓ Prefer component scope for mixed-freshness pages                       │
│     @revalidate(scope=InvalidationScope.COMPONENT)                          │
│                                                                              │
│   ✓ Set appropriate TTLs based on content type                             │
│     • Prices: 30-60 seconds                                                 │
│     • Listings: 5-15 minutes                                                │
│     • Static content: 1-24 hours                                            │
│                                                                              │
│   ✓ Use webhooks for instant updates                                       │
│     await revalidate_path("/products/123")                                  │
│                                                                              │
│   ✓ Monitor cache hit rates                                                 │
│     cache.get_stats()                                                       │
│                                                                              │
│                                                                              │
│   ✗ DON'T                                                                   │
│   ───────                                                                   │
│                                                                              │
│   ✗ Use ISR for user-specific content                                      │
│     # BAD: Caches for all users!                                           │
│     @revalidate(seconds=60)                                                 │
│     def my_dashboard(user_id):                                              │
│         return user_specific_data(user_id)                                  │
│                                                                              │
│   ✗ Set TTL too low (defeats caching purpose)                              │
│     # BAD: Basically SSR with extra steps                                  │
│     @revalidate(seconds=1)                                                  │
│                                                                              │
│   ✗ Forget to invalidate on content changes                                │
│     # BAD: Users see stale content                                         │
│     # Don't just rely on TTL, use webhooks!                                │
│                                                                              │
│   ✗ Cache sensitive data                                                   │
│     # BAD: PII exposed to all users                                        │
│     @revalidate(seconds=60)                                                 │
│     def user_profile():  # Contains email, phone                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Choosing TTL Values

```python
# Content type → Recommended TTL

# REAL-TIME (avoid ISR, use SSR or client fetch)
# Stock prices, live scores, chat messages

# NEAR REAL-TIME: 10-60 seconds
@revalidate(seconds=30)
def inventory_status(): ...

@revalidate(seconds=60)
def trending_products(): ...

# FREQUENTLY UPDATED: 5-15 minutes
@revalidate(seconds=300)
def product_listings(): ...

@revalidate(seconds=600)
def search_results(): ...

# OCCASIONALLY UPDATED: 1-6 hours
@revalidate(seconds=3600)
def blog_post(): ...

@revalidate(seconds=21600)  # 6 hours
def category_page(): ...

# RARELY UPDATED: 12-24 hours
@revalidate(seconds=86400)
def about_page(): ...

@revalidate(seconds=86400)
def terms_of_service(): ...
```

---

## Debugging

### Cache Inspection

```python
from pynext import get_isr_cache

cache = get_isr_cache()

# Get cache statistics
stats = cache.get_stats()
print(stats)
# {
#     "total_entries": 156,
#     "fresh_entries": 142,
#     "stale_entries": 14,
#     "tags": ["products", "blog", "featured"],
#     "total_size_bytes": 15234567,
#     "disk_size_mb": 14.5
# }

# Check specific entry
entry = cache.get("/products/123")
if entry:
    print(f"Created: {entry.created_at}")
    print(f"Is stale: {entry.is_stale}")
    print(f"Tags: {entry.config.tags}")
    print(f"TTL: {entry.config.seconds}s")
```

### Debug Headers

Enable debug mode to see cache status in response headers:

```python
# pynext.config.py
config = {
    "isr": {
        "debug": True,  # Adds debug headers
    }
}
```

Response headers:
```
X-PyNext-Cache: hit
X-PyNext-Cache-Key: /products/123:en
X-PyNext-Cache-Age: 45
X-PyNext-Cache-TTL: 60
X-PyNext-Cache-Tags: products,catalog
```

### Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable ISR debug logs
logging.getLogger("pynext.isr").setLevel(logging.DEBUG)

# Output:
# DEBUG:pynext.isr:Cache HIT for /products/123 (age: 45s, ttl: 60s)
# DEBUG:pynext.isr:Cache STALE for /products/456, queuing regeneration
# DEBUG:pynext.isr:Regenerated /products/456 in 234ms
```

---

## API Reference

### @revalidate Decorator

```python
@revalidate(
    seconds: Optional[int] = None,              # Time-based TTL
    tags: Optional[List[str]] = None,           # Tag groups
    scope: InvalidationScope = InvalidationScope.PAGE,  # Granularity
    on_demand: bool = False,                    # Only manual invalidation
    stale_while_revalidate: bool = True,        # Serve stale during regen
    background_regeneration: bool = True,       # Regen in background
)
def my_component(): ...
```

### Revalidation Functions

```python
from pynext import revalidate_path, revalidate_tag, revalidate_component

# Invalidate by URL path
await revalidate_path("/products/123")
await revalidate_path("/blog/hello-world")

# Invalidate by tag
await revalidate_tag("products")
await revalidate_tag("blog")

# Invalidate component everywhere
await revalidate_component("ProductPrice")
await revalidate_component("StockStatus")
```

### InvalidationScope Enum

```python
from pynext import InvalidationScope

InvalidationScope.PAGE       # Regenerate entire page
InvalidationScope.COMPONENT  # Only regenerate this component
InvalidationScope.RESOURCE   # Tied to Resource refetch
InvalidationScope.TAG        # Group invalidation via tags
```

### ISRCache Class

```python
from pynext import get_isr_cache, init_isr_cache

# Initialize cache
cache = init_isr_cache(
    cache_dir=Path("./cache"),  # Disk persistence
    max_size_mb=100,            # Memory limit
)

# Or get existing cache
cache = get_isr_cache()

# Cache operations
entry = cache.get("/products/123")
cache.set("/products/123", html_content, config)

# Invalidation
cache.invalidate_by_path("/products/123")
cache.invalidate_by_tag("products")
cache.invalidate_by_component("ProductPrice")

# Stats
stats = cache.get_stats()
```

### RevalidateConfig

```python
from pynext import RevalidateConfig

config = RevalidateConfig(
    seconds=60,                        # TTL in seconds
    tags=["products"],                 # Tag groups
    scope=InvalidationScope.COMPONENT, # Granularity
    on_demand=False,                   # Time-based + on-demand
    stale_while_revalidate=True,       # Serve stale during regen
    background_regeneration=True,      # Non-blocking regeneration
)
```

---

## Related Documentation

- [Static Generation](STATIC_GENERATION.md) - Build-time static generation
- [Streaming & Suspense](STREAMING_SUSPENSE.md) - Progressive rendering
- [Server Actions](SERVER_ACTIONS.md) - Trigger revalidation from actions
- [Middleware](MIDDLEWARE.md) - Cache headers and CDN integration

---

## Summary

You've learned:

1. ✅ What ISR is and why it matters
2. ✅ Stale-while-revalidate pattern
3. ✅ Time-based vs tag-based vs on-demand revalidation
4. ✅ Component-level granularity (PyNext innovation)
5. ✅ Cache architecture and flow
6. ✅ Real-world implementation patterns
7. ✅ Performance benefits and best practices
8. ✅ Debugging and monitoring

ISR gives you the best of both worlds: the speed of static sites with the freshness of dynamic rendering. Use it wisely! ⚡
