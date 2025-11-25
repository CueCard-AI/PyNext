# Code Splitting & Lazy Loading

PyNext supports advanced code splitting strategies to optimize your application's initial load time and overall performance.

## Table of Contents

- [Overview](#overview)
- [The `lazy()` Primitive](#the-lazy-primitive)
- [Lazy Routes](#lazy-routes)
- [Prefetching Strategies](#prefetching-strategies)
- [Route-Based Bundling](#route-based-bundling)
- [Integration with Suspense](#integration-with-suspense)
- [Performance Benchmarks](#performance-benchmarks)
- [API Reference](#api-reference)
- [Best Practices](#best-practices)

---

## Overview

Code splitting allows you to break your application into smaller chunks that load on-demand. This improves:

- **Initial Load Time**: Ship less JavaScript upfront
- **Time to Interactive (TTI)**: Faster initial interactivity
- **Memory Usage**: Load code only when needed
- **Cache Efficiency**: Better long-term caching

### How It Works

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        CODE SPLITTING FLOW                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. BUILD TIME                                                          │
│  ─────────────                                                          │
│                                                                         │
│  [Source Code] → [Analyze Dependencies] → [Generate Chunks]            │
│                                                                         │
│      pages/              ┌─────────────┐    ┌──────────────┐           │
│      ├── index.py   →    │  Analyzer   │ →  │ chunks/      │           │
│      ├── dashboard.py    │             │    │ ├── shared.js│           │
│      └── settings.py     └─────────────┘    │ ├── index.js │           │
│                                             │ ├── dashboard.js│        │
│                                             │ └── settings.js│         │
│                                             └──────────────┘           │
│                                                                         │
│  2. INITIAL LOAD                                                        │
│  ───────────────                                                        │
│                                                                         │
│  Client requests /dashboard                                             │
│                                                                         │
│  Server sends:                                                          │
│  ┌───────────────────────────────────────┐                             │
│  │ HTML (streaming)                      │                             │
│  │ ├── <link rel="modulepreload" ...>    │  ← Preload hints           │
│  │ ├── Shell content                     │                             │
│  │ └── Lazy placeholders                 │                             │
│  └───────────────────────────────────────┘                             │
│                                                                         │
│  3. CLIENT HYDRATION                                                    │
│  ───────────────────                                                    │
│                                                                         │
│  Browser loads:                                                         │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐                    │
│  │ shared.js  │ →  │ runtime.js │ →  │dashboard.js│                    │
│  │ (common)   │    │ (signals)  │    │ (page)     │                    │
│  └────────────┘    └────────────┘    └────────────┘                    │
│                                                                         │
│  4. LAZY LOADING                                                        │
│  ───────────────                                                        │
│                                                                         │
│  User hovers link → Prefetch chunk → User clicks → Instant load        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## The `lazy()` Primitive

The `lazy()` function creates a component that loads on-demand.

### Basic Usage

```python
from pynext import lazy, Suspense, div, span

# Create a lazy component
HeavyChart = lazy(lambda: import_component("components.chart"))

# Use with Suspense for loading state
@page
def Dashboard():
    return Suspense(fallback=ChartSkeleton())[
        HeavyChart(data=chart_data)
    ]
```

### With Custom Options

```python
# Named lazy component
UserWidget = lazy(
    lambda: import_component("components.user_widget"),
    name="UserWidget",           # For debugging
    chunk_name="widgets/user",   # Custom chunk path
    preload=True,                # Start loading immediately
)
```

### Async Loaders

```python
# Async loader for remote components
RemoteWidget = lazy(
    async lambda: await fetch_component("https://cdn.example.com/widget.js")
)
```

---

## Lazy Routes

The `@lazy_route` decorator creates routes that load on-demand.

### Basic Lazy Route

```python
from pynext import lazy_route, div

@lazy_route("/analytics")
def AnalyticsPage():
    # This entire page loads only when visiting /analytics
    return div()[
        AnalyticsDashboard(),
        HeavyCharts(),
        DataTables(),
    ]
```

### With Preloading

```python
@lazy_route("/critical-page", preload=True)
def CriticalPage():
    # Starts loading immediately (background)
    return div()["Critical content"]
```

### With Prefetch Strategy

```python
from pynext import lazy_route, PrefetchStrategy

@lazy_route("/settings", prefetch=PrefetchStrategy.HOVER)
def SettingsPage():
    # Prefetches when user hovers a link to /settings
    return div()["Settings"]
```

---

## Prefetching Strategies

PyNext supports multiple prefetching strategies to optimize navigation.

### Available Strategies

| Strategy | When Prefetched | Use Case |
|----------|-----------------|----------|
| `HOVER` | On link hover | Default, good balance |
| `VISIBLE` | When link is visible | Important links above fold |
| `IDLE` | When browser is idle | Background prefetch |
| `NONE` | Never prefetched | Rarely visited pages |

### Using prefetch_link

```python
from pynext import a, prefetch_link, PrefetchStrategy

# Create a prefetching link
a(**prefetch_link("/dashboard", strategy=PrefetchStrategy.HOVER))[
    "Go to Dashboard"
]

# Rendered HTML:
# <a href="/dashboard" data-prefetch="hover">Go to Dashboard</a>
```

### Prefetch Configuration

```python
from pynext import PrefetchConfig

config = PrefetchConfig(
    default_strategy=PrefetchStrategy.HOVER,
    always_prefetch=["/dashboard", "/home"],  # Critical routes
    never_prefetch=["/admin", "/debug"],      # Rarely used
    max_concurrent=2,                          # Limit parallel prefetches
)
```

---

## Route-Based Bundling

PyNext automatically generates optimized bundles per route.

### Bundle Structure

```
.pynext/
└── chunks/
    ├── manifest.json      # Chunk manifest
    ├── shared.js          # Common dependencies
    ├── index.js           # / route
    ├── dashboard.js       # /dashboard route
    ├── users-id.js        # /users/[id] route
    └── settings.js        # /settings route
```

### Using RouteChunkGenerator

```python
from pynext.bundler.route_chunks import RouteChunkGenerator

# Analyze and generate chunks
generator = RouteChunkGenerator(
    router=app.router,
    output_dir=".pynext/chunks",
)

# Analyze all routes
generator.analyze_all_routes()

# Generate chunk files
chunks = generator.generate_chunks()

# Get manifest
manifest = generator.get_manifest()
```

### Chunk Manifest

```json
{
  "chunks": {
    "/dashboard": {
      "name": "dashboard",
      "url": "/__pynext__/chunks/dashboard.js?v=abc123",
      "size": 2048,
      "hash": "abc123",
      "needsSignals": true,
      "needsResource": true
    }
  },
  "shared": {
    "name": "shared",
    "url": "/__pynext__/chunks/shared.js",
    "size": 4096,
    "hash": "def456"
  }
}
```

### Preload Tags

```python
# Get preload tags for a route
tags = generator.get_preload_tags("/dashboard")

# Returns:
# <link rel="modulepreload" href="/__pynext__/chunks/dashboard.js?v=abc123">
# <link rel="modulepreload" href="/__pynext__/chunks/shared.js">
```

---

## Integration with Suspense

Lazy components work seamlessly with Suspense.

### Basic Integration

```python
from pynext import lazy, Suspense, div

HeavyComponent = lazy(lambda: import_component("heavy"))

@page
def MyPage():
    return Suspense(fallback=div()["Loading..."])[
        HeavyComponent()
    ]
```

### Nested Suspense Boundaries

```python
@page
def Dashboard():
    return div()[
        # Header loads first
        Header(),
        
        # Main content with fallback
        Suspense(fallback=MainSkeleton())[
            MainContent(),
            
            # Sidebar loads independently
            Suspense(fallback=SidebarSkeleton())[
                Sidebar()
            ]
        ]
    ]
```

### With Resource Loading

```python
from pynext import lazy, Suspense, Resource

# Lazy component that uses resources
AnalyticsDashboard = lazy(lambda: import_component("analytics"))

@page
def Analytics():
    data = Resource(fetch_analytics)
    
    return Suspense(fallback=AnalyticsSkeleton())[
        AnalyticsDashboard(data=data)
    ]
```

---

## Performance Benchmarks

### Lazy Component Overhead

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    LAZY LOADING PERFORMANCE                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  CREATION TIME:                                                         │
│  ─────────────                                                          │
│  lazy() call:           ~2.1μs                                          │
│  With options:          ~2.1μs                                          │
│  Boundary creation:     ~0.4μs                                          │
│                                                                         │
│  RENDERING TIME:                                                        │
│  ──────────────                                                         │
│  Placeholder render:    ~0.5μs                                          │
│  Loaded render:         ~1.7μs                                          │
│  With custom fallback:  ~1.2μs                                          │
│                                                                         │
│  SCRIPT GENERATION:                                                     │
│  ─────────────────                                                      │
│  Single component:      ~1.3μs                                          │
│  10 components:         ~12μs                                           │
│                                                                         │
│  CHUNK URL GENERATION:                                                  │
│  ─────────────────────                                                  │
│  get_chunk_url():       ~0.1μs (9.4M ops/sec)                           │
│  get_preload_tag():     ~0.2μs                                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Payload Size Analysis

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PAYLOAD SIZE ANALYSIS                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  LAZY BOUNDARY HTML:                                                    │
│  ───────────────────                                                    │
│  Single lazy component:     ~200 bytes                                  │
│  With custom fallback:      ~350 bytes                                  │
│                                                                         │
│  HYDRATION SCRIPT:                                                      │
│  ─────────────────                                                      │
│  Single component:          ~200 bytes                                  │
│  10 components:             ~2 KB                                       │
│  Per-component overhead:    ~150 bytes                                  │
│                                                                         │
│  COMPARISON WITH STATIC:                                                │
│  ───────────────────────                                                │
│  Static component:          20 bytes                                    │
│  Lazy equivalent:           350 bytes (HTML + script)                   │
│  Overhead:                  330 bytes per lazy boundary                 │
│                                                                         │
│  ⚠️  Note: Overhead is justified when:                                  │
│     - Component code > 5KB (typical React component)                    │
│     - Component not immediately needed                                  │
│     - Component has expensive dependencies                              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Real-World Scenarios

| Scenario | Time | Notes |
|----------|------|-------|
| Dashboard with 3 lazy widgets | 17μs | Minimal overhead |
| Blog with lazy comments | 10μs | Comments load on scroll |
| E-commerce with lazy reviews | 15μs | Reviews not blocking |

---

## API Reference

### `lazy(loader, **options)`

Creates a lazy-loaded component.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `loader` | `Callable[[], T]` | required | Function returning the component |
| `name` | `str` | auto | Component name for debugging |
| `preload` | `bool` | `False` | Start loading immediately |
| `chunk_name` | `str` | auto | Custom chunk file name |

**Returns:** `LazyComponent[T]`

### `lazy_route(path, **options)`

Decorator to create a lazy-loaded route.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | `str` | required | Route path pattern |
| `preload` | `bool` | `False` | Preload on page load |
| `prefetch` | `PrefetchStrategy` | `HOVER` | When to prefetch |

### `prefetch_link(href, strategy)`

Generate prefetch attributes for a link.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `href` | `str` | required | Link destination |
| `strategy` | `PrefetchStrategy` | `HOVER` | Prefetch strategy |

**Returns:** `Dict[str, str]` - HTML attributes

### `LazyComponent`

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `id` | `str` | Unique component ID |
| `state` | `LoadingState` | Current loading state |
| `component` | `T | None` | Loaded component |
| `error` | `Exception | None` | Loading error |

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `load()` | `Awaitable[T]` | Load the component |
| `preload()` | `None` | Start loading in background |
| `get_chunk_url()` | `str` | Get chunk URL |
| `get_preload_tag()` | `str` | Get HTML preload tag |

### `LoadingState`

| Value | Description |
|-------|-------------|
| `IDLE` | Not yet loaded |
| `LOADING` | Currently loading |
| `LOADED` | Successfully loaded |
| `ERROR` | Loading failed |

### `PrefetchStrategy`

| Value | Description |
|-------|-------------|
| `HOVER` | Prefetch on hover |
| `VISIBLE` | Prefetch when visible |
| `IDLE` | Prefetch when idle |
| `NONE` | Don't prefetch |

---

## Best Practices

### 1. Use Lazy for Heavy Components

```python
# ✅ Good: Heavy charting library
ChartComponent = lazy(lambda: import_component("heavy_charts"))

# ❌ Avoid: Simple static component
SimpleText = lazy(lambda: span()["Hello"])  # Overhead not worth it
```

### 2. Combine with Islands

```python
from pynext import island, lazy

# Lazy + Island = Optimal loading
@island
def InteractiveChart():
    return LazyChart()  # Loads only when island hydrates

LazyChart = lazy(lambda: import_component("chart"))
```

### 3. Strategic Prefetching

```python
# ✅ Prefetch likely navigation targets
a(**prefetch_link("/dashboard", PrefetchStrategy.VISIBLE))["Dashboard"]

# ✅ Don't prefetch rarely visited pages
a(**prefetch_link("/admin", PrefetchStrategy.NONE))["Admin"]
```

### 4. Use Suspense Boundaries

```python
# ✅ Always wrap lazy components in Suspense
Suspense(fallback=Skeleton())[
    LazyComponent()
]

# ❌ Avoid: Lazy without fallback
LazyComponent()  # No loading state shown
```

### 5. Group Related Components

```python
# ✅ Single chunk for related components
AnalyticsSuite = lazy(
    lambda: import_component("analytics.suite"),
    chunk_name="analytics"
)

# This loads: Charts, Tables, Filters together
```

### 6. Preload Critical Routes

```python
# ✅ Preload routes users will likely visit
@lazy_route("/onboarding/step-2", preload=True)
def OnboardingStep2():
    ...  # Ready when user finishes step 1
```

---

## Client-Side Runtime

The lazy loading runtime (`lazy.js`) handles:

- Dynamic chunk loading via `import()`
- Loading state management
- Intersection Observer for visibility
- Prefetch queue management
- Integration with navigation

### Global API

```javascript
// Register a lazy component
__pynext__.registerLazy(id, {
  chunk: "/path/to/chunk.js",
  props: { ... },
  preload: false
});

// Initialize lazy loading
__pynext__.initLazyLoading();

// Prefetch a chunk
__pynext__.prefetchChunk("/path/to/chunk.js");

// Prefetch a route
__pynext__.prefetchRoute("/dashboard");

// Get loading stats
__pynext__.getLazyStats();
// { total: 5, idle: 2, loading: 1, loaded: 2, error: 0 }
```

---

## Debugging

### Enable Debug Logging

```javascript
window.__PYNEXT_DEBUG__ = true;

// Console output:
// [PyNext Lazy] Registered lazy component: lazy-abc123
// [PyNext Lazy] Loading chunk: /__pynext__/chunks/widget.js
// [PyNext Lazy] Loaded chunk in 45.23ms
```

### Check Loading Stats

```javascript
console.table(__pynext__.getLazyStats());
```

### Inspect Lazy Components

```javascript
// All registered components
console.log(__pynext__._lazyComponents);

// All loaded chunks
console.log(__pynext__._loadedChunks);
```

---

## Related Documentation

- [Islands Architecture](./ISLANDS.md) - Selective hydration
- [Streaming & Suspense](./STREAMING_SUSPENSE.md) - Progressive loading
- [Hydration](./HYDRATION.md) - Client-side state restoration
- [Performance Optimization](./PERFORMANCE.md) - Overall optimization guide

