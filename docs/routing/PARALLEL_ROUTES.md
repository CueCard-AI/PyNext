# PyNext Parallel Routes

> **Independent Streaming • Selective Hydration • Slot-Level Caching**

## Overview

Parallel Routes allow you to render multiple pages simultaneously in named "slots" within a single layout. Each slot can load independently, stream its content as it's ready, and be cached separately.

PyNext's implementation is fundamentally more efficient than Next.js:

| Feature | Next.js | PyNext |
|---------|---------|--------|
| **Slot Resolution** | Runtime | **Build-time compiled** |
| **Streaming** | Sequential | **Independent per slot** |
| **Hydration** | All slots | **Only interactive slots** |
| **Caching** | Page-level | **Slot-level granularity** |
| **Bundle Size** | Full page JS | **Per-slot bundles** |

## SolidJS Principles Applied

### 1. Build-Time Slot Compilation
```python
# Slot hierarchies are pre-resolved at build time
# Zero runtime resolution overhead

# Build output:
# {
#   "hierarchies": {
#     "dashboard": {
#       "sidebar": { "routes": [...], "requiresHydration": false },
#       "main": { "routes": [...], "requiresHydration": true }
#     }
#   }
# }
```

### 2. Independent Streaming
```
Request arrives
       │
       ▼
┌──────────────────────────────────────┐
│     Start rendering all slots        │
│           in parallel                │
└──────────────────────────────────────┘
       │
       ├─────────────┬─────────────┐
       ▼             ▼             ▼
   [Sidebar]     [Main]       [Modal]
   Fast DB       Slow API     No data
       │             │             │
       ▼             │             ▼
   STREAM!           │         STREAM!
   (50ms)            │         (10ms)
                     ▼
                 STREAM!
                 (200ms)
```

### 3. Selective Hydration
```python
# Static slot - ZERO JavaScript shipped
@sidebar/page.py → Pure HTML navigation

# Interactive slot - Only this slot's JS shipped
@main/page.py → Signal-based content with hydration
```

### 4. Slot-Level Caching (Fine-Grained ISR)
```python
# Different TTLs per slot
SlotConfig("sidebar", cache_ttl=3600)   # 1 hour cache
SlotConfig("main", cache_ttl=60)        # 1 minute cache
SlotConfig("notifications", cache_ttl=0) # No cache (real-time)
```

---

## Quick Start

### Directory Structure

```
pages/
├── @sidebar/              # Sidebar slot
│   ├── default.py        # Default content when no route matches
│   ├── loading.py        # Loading skeleton
│   ├── error.py          # Error state
│   └── categories/
│       └── page.py       # /categories renders here
├── @main/                 # Main content slot
│   ├── page.py           # Default main content
│   ├── loading.py        # Main loading state
│   └── [id]/
│       └── page.py       # /items/:id renders here
├── @modal/                # Modal slot (for intercepting routes)
│   └── default.py        # Empty by default
└── layout.py              # Defines slot placements
```

### Layout with Slots

```python
# pages/layout.py
from pynext import Slot
from pynext.html import div, aside, main

@layout
def dashboard_layout():
    return div(class_="dashboard-container")[
        aside(class_="sidebar")[
            Slot("sidebar", loading=SidebarSkeleton)
        ],
        main(class_="content")[
            Slot("main", loading=ContentSkeleton)
        ],
        Slot("modal"),  # For modals over current content
    ]

def SidebarSkeleton():
    return div(class_="skeleton sidebar-skeleton")[
        div(class_="skeleton-line"),
        div(class_="skeleton-line"),
        div(class_="skeleton-line"),
    ]

def ContentSkeleton():
    return div(class_="skeleton content-skeleton")[
        div(class_="skeleton-title"),
        div(class_="skeleton-text"),
        div(class_="skeleton-text"),
    ]
```

### Slot Content Pages

```python
# pages/@sidebar/page.py
from pynext.html import nav, a, ul, li

def sidebar():
    return nav(class_="nav-menu")[
        ul()[
            li()[a(href="/dashboard")["Dashboard"]],
            li()[a(href="/projects")["Projects"]],
            li()[a(href="/settings")["Settings"]],
        ]
    ]

# pages/@main/page.py
from pynext.html import div, h1, p

def main_content():
    return div()[
        h1()["Welcome to Dashboard"],
        p()["Select an item from the sidebar."],
    ]

# pages/@main/[id]/page.py
from pynext import createResource
from pynext.html import div, h1, p

def item_detail(id: str):
    item = createResource(lambda: fetch_item(id))
    
    return div()[
        h1()[item().name],
        p()[item().description],
    ]
```

### Build Command

```bash
pynext build

# Output:
# [PyNext] Compiling parallel routes...
# [PyNext] Compiled 4 parallel slots:
# [PyNext]   → Static slots: 2
# [PyNext]   → Interactive slots: 2
# [PyNext]   → Slot-level caching enabled
```

---

## Core Concepts

### The @folder Convention

Directories starting with `@` define parallel slots:

```
@slotname/
├── page.py       # Main content for this slot
├── default.py    # Fallback when no route matches
├── loading.py    # Loading state component
├── error.py      # Error boundary component
└── [param]/      # Dynamic routes within slot
    └── page.py
```

| File | Purpose |
|------|---------|
| `page.py` | Main slot content for the route |
| `default.py` | Shown when no specific route matches |
| `loading.py` | Shown while slot is loading |
| `error.py` | Shown when slot errors |

### Slot Component

The `Slot` component defines where slot content renders:

```python
from pynext import Slot

Slot(
    name="sidebar",           # Matches @sidebar/ folder
    loading=LoadingComponent, # Optional loading state
    error=ErrorComponent,     # Optional error handler
    default=DefaultComponent, # Optional default content
    className="my-slot",      # CSS class
    stream=True,              # Enable independent streaming
)
```

### Slot Matching

When a request comes in, PyNext matches routes within each slot:

```
Request: /dashboard/items/123

Layout: pages/layout.py
  │
  ├── @sidebar/ slot
  │     └── No specific route → uses default.py
  │
  ├── @main/ slot
  │     └── Matches [id]/page.py with id="123"
  │
  └── @modal/ slot
        └── No content → empty
```

---

## Build-Time Compilation

### How It Works

At build time, PyNext:

1. **Scans** for all `@folder` directories
2. **Analyzes** each slot for interactivity (signals, effects)
3. **Compiles** slot hierarchies into a manifest
4. **Generates** per-slot bundles for interactive slots

```
                         BUILD TIME
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   pages/                                                        │
│   ├── @sidebar/                                                 │
│   ├── @main/           ┌───────────────────────┐                │
│   └── layout.py   ──▶  │ ParallelRoutesScanner │                │
│                        └───────────┬───────────┘                │
│                                    │                            │
│                                    ▼                            │
│                        ┌───────────────────────┐                │
│                        │ ParallelRoutesCompiler│                │
│                        │                       │                │
│                        │  ┌─────────────────┐  │                │
│                        │  │ For each slot:  │  │                │
│                        │  │                 │  │                │
│                        │  │ 1. Parse routes │  │                │
│                        │  │ 2. Analyze AST  │  │                │
│                        │  │ 3. Detect       │  │                │
│                        │  │    interactivity│  │                │
│                        │  │ 4. Generate     │  │                │
│                        │  │    bundle ID    │  │                │
│                        │  └─────────────────┘  │                │
│                        └───────────┬───────────┘                │
│                                    │                            │
│                                    ▼                            │
│                        ┌───────────────────────┐                │
│                        │ CompiledSlotHierarchy │                │
│                        │                       │                │
│                        │ - Pre-resolved routes │                │
│                        │ - Hydration flags     │                │
│                        │ - Cache configs       │                │
│                        └───────────────────────┘                │
│                                    │                            │
│                                    ▼                            │
│                        parallel-manifest.json                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Manifest Output

```json
{
  "hierarchies": {
    "": {
      "sidebar": {
        "name": "sidebar",
        "routes": [
          { "pattern": "/", "module": "pages/@sidebar/page.py" },
          { "pattern": "/categories", "module": "pages/@sidebar/categories/page.py" }
        ],
        "default": "pages/@sidebar/default.py",
        "loading": "pages/@sidebar/loading.py",
        "error": null,
        "config": {
          "cache_ttl": 3600,
          "stream_independent": true
        },
        "requiresHydration": false,
        "bundleId": null
      },
      "main": {
        "name": "main",
        "routes": [
          { "pattern": "/", "module": "pages/@main/page.py" },
          { "pattern": "/:id", "module": "pages/@main/[id]/page.py" }
        ],
        "default": null,
        "loading": "pages/@main/loading.py",
        "error": "pages/@main/error.py",
        "config": {
          "cache_ttl": 60,
          "stream_independent": true
        },
        "requiresHydration": true,
        "bundleId": "a1b2c3d4e5f6"
      }
    }
  },
  "slotBundles": {
    "@main": "a1b2c3d4e5f6"
  },
  "stats": {
    "totalSlots": 3,
    "interactiveSlots": 1,
    "staticSlots": 2
  }
}
```

### Interactivity Detection

The compiler analyzes each slot's Python files for:

```python
# These patterns mark a slot as INTERACTIVE:

Signal("value")           # Reactive signal
Store({"key": "value"})   # Reactive store
Effect(lambda: ...)       # Side effect
createResource(fetcher)   # Async resource

@island                   # Island decorator
@island(strategy="load")  # Island with strategy
```

**Static slots** (no interactivity) ship **zero JavaScript**.

---

## Independent Streaming

### How Streaming Works

Each slot streams its content as soon as it's ready:

```python
async def stream_parallel_slots(hierarchy, path, request):
    """
    Stream slots as they complete.
    
    Fast slots appear before slow ones (out-of-order streaming).
    """
    matches = hierarchy.match_slots(path)
    
    # Start all slots in parallel
    pending = {}
    for slot_name, match in matches.items():
        task = asyncio.create_task(render_slot(slot_name, match))
        pending[slot_name] = task
    
    # Yield as each completes
    while pending:
        done, _ = await asyncio.wait(
            pending.values(),
            return_when=asyncio.FIRST_COMPLETED,
        )
        
        for task in done:
            slot_name = find_slot_for_task(task)
            content = task.result()
            yield slot_name, content
            del pending[slot_name]
```

### Streaming Timeline

```
Time →

0ms    50ms   100ms  150ms  200ms  250ms
│      │      │      │      │      │
▼      ▼      ▼      ▼      ▼      ▼
┌──────────────────────────────────────┐
│ Initial HTML shell sent              │
└──────────────────────────────────────┘
       │
       │ ┌────────────────────────────┐
       └─│ Sidebar slot streams      │ (fast DB query)
         │ <div data-slot="sidebar"> │
         │   <nav>...</nav>          │
         │ </div>                    │
         └────────────────────────────┘
                      │
                      │ ┌────────────────────────────┐
                      └─│ Modal slot streams        │ (no data)
                        │ <div data-slot="modal">   │
                        │   <!-- empty -->          │
                        │ </div>                    │
                        └────────────────────────────┘
                                            │
                                            │ ┌────────────────────────────┐
                                            └─│ Main slot streams         │ (slow API)
                                              │ <div data-slot="main">    │
                                              │   <article>...</article>  │
                                              │ </div>                    │
                                              └────────────────────────────┘
```

### Benefits of Independent Streaming

| Metric | Sequential | Independent Streaming |
|--------|------------|----------------------|
| TTFB | Slowest slot | **First slot ready** |
| Perceived Load | Wait for all | **Progressive** |
| User Interaction | After all slots | **Per-slot** |

---

## Selective Hydration

### Static vs Interactive Slots

```
┌─────────────────────────────────────────────────────────────────┐
│                        Page Layout                               │
├───────────────────┬─────────────────────────────────────────────┤
│                   │                                             │
│   @sidebar/       │             @main/                          │
│                   │                                             │
│   ┌───────────┐   │   ┌─────────────────────────────────────┐   │
│   │           │   │   │                                     │   │
│   │  STATIC   │   │   │          INTERACTIVE                │   │
│   │           │   │   │                                     │   │
│   │  No JS    │   │   │    Signal-based content             │   │
│   │  Pure HTML│   │   │    createResource for data          │   │
│   │           │   │   │    Event handlers                   │   │
│   │           │   │   │                                     │   │
│   │  0 KB     │   │   │    Only main-slot.js loaded         │   │
│   │           │   │   │    (~2KB for this slot)             │   │
│   └───────────┘   │   └─────────────────────────────────────┘   │
│                   │                                             │
└───────────────────┴─────────────────────────────────────────────┘

Total JS: Only what @main/ needs (vs full page hydration)
```

### Per-Slot Bundle Generation

```python
# Build output for interactive slots:

dist/
├── _parallel/
│   ├── parallel-manifest.json
│   └── bundles/
│       └── a1b2c3d4e5f6.js   # @main/ slot bundle only
```

### Hydration Flow

```
                           Page Load
                              │
                              ▼
                    ┌─────────────────┐
                    │ HTML received   │
                    │ (all slots)     │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
        ┌──────────┐   ┌──────────┐   ┌──────────┐
        │ @sidebar │   │  @main   │   │ @modal   │
        │          │   │          │   │          │
        │ STATIC   │   │INTERACTIVE│  │ STATIC   │
        │          │   │          │   │          │
        │ ✓ Done   │   │ Load JS  │   │ ✓ Done   │
        └──────────┘   └────┬─────┘   └──────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │ Hydrate only │
                    │ @main/ slot  │
                    └──────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │ Interactive! │
                    └──────────────┘
```

---

## Slot-Level Caching

### Configuration

```python
# In pages/layout.py or through SlotConfig

from pynext.router.parallel import SlotConfig

# Configure per-slot caching
sidebar_config = SlotConfig(
    name="sidebar",
    cache_ttl=3600,  # Cache for 1 hour
)

main_config = SlotConfig(
    name="main",
    cache_ttl=60,  # Cache for 1 minute
)

notifications_config = SlotConfig(
    name="notifications",
    cache_ttl=0,  # Never cache (real-time)
)
```

### Cache Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        SlotCacheManager                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Cache Key Format: "{slot_id}:{path}"                          │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                    Cache Entries                        │   │
│   ├─────────────────────────────────────────────────────────┤   │
│   │ @sidebar:/             │ TTL: 3600s │ ETag: abc123     │   │
│   │ @sidebar:/categories   │ TTL: 3600s │ ETag: def456     │   │
│   │ @main:/                │ TTL: 60s   │ ETag: ghi789     │   │
│   │ @main:/items/1         │ TTL: 60s   │ ETag: jkl012     │   │
│   │ @main:/items/2         │ TTL: 60s   │ ETag: mno345     │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│   Methods:                                                      │
│   - get(slot_id, path) → CacheEntry                             │
│   - set(slot_id, path, content, ttl, dependencies)              │
│   - invalidate(slot_id) → Clear all entries for slot            │
│   - invalidate_by_tag(tag) → Clear by dependency tag            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Cache Entry Structure

```python
@dataclass
class SlotCacheEntry:
    slot_id: str          # @sidebar, @main, etc.
    content: str          # Rendered HTML
    etag: str             # Content hash for validation
    expires_at: float     # Unix timestamp
    dependencies: List[str]  # Tags for invalidation
```

### Invalidation Strategies

```python
from pynext.bundler.parallel import invalidate_slot, invalidate_slot_tag

# Invalidate a specific slot
invalidate_slot("@sidebar")  # Clears all @sidebar cache entries

# Invalidate by tag (when data changes)
invalidate_slot_tag("products")  # Clears slots depending on "products"
```

### Stale-While-Revalidate

```
Request for @main:/items/123
           │
           ▼
    ┌──────────────┐
    │ Check Cache  │
    └──────┬───────┘
           │
     ┌─────┴─────┐
     │           │
   MISS        HIT
     │           │
     ▼           ▼
┌─────────┐  ┌─────────────────────────────┐
│ Render  │  │ Is expired?                 │
│ & Cache │  │                             │
└─────────┘  │  ┌────────────────────────┐ │
             │  │ YES: Return stale +    │ │
             │  │      trigger rerender  │ │
             │  │                        │ │
             │  │ NO: Return cached      │ │
             │  └────────────────────────┘ │
             └─────────────────────────────┘
```

---

## Slot Component API

### Basic Slot

```python
from pynext import Slot

Slot("sidebar")
```

**Generated HTML:**
```html
<div id="slot-sidebar-a1b2c3"
     class="pynext-slot"
     data-slot="sidebar"
     data-slot-state="ready">
  <!-- slot content here -->
</div>
```

### Slot with Loading State

```python
def SidebarSkeleton():
    return div(class_="skeleton")[
        div(class_="skeleton-line"),
        div(class_="skeleton-line"),
    ]

Slot("sidebar", loading=SidebarSkeleton)
```

**While loading:**
```html
<div id="slot-sidebar-a1b2c3"
     class="pynext-slot"
     data-slot="sidebar"
     data-slot-state="loading">
  <div class="skeleton">
    <div class="skeleton-line"></div>
    <div class="skeleton-line"></div>
  </div>
</div>
```

### Slot with Error Handler

```python
def SidebarError(error: Exception):
    return div(class_="error")[
        h3()["Failed to load sidebar"],
        p()[str(error)],
    ]

Slot("sidebar", error=SidebarError)
```

### Slot with Default Content

```python
def SidebarDefault():
    return div()[
        p()["Select a category"],
    ]

Slot("sidebar", default=SidebarDefault)
```

### SlotGroup

Group slots for coordinated loading:

```python
from pynext import SlotGroup, Slot

def PageSkeleton():
    return div(class_="page-skeleton")[
        div(class_="header-skeleton"),
        div(class_="content-skeleton"),
    ]

SlotGroup(loading=PageSkeleton)[
    Slot("header"),
    Slot("sidebar"),
    Slot("main"),
    Slot("footer"),
]
```

**Behavior:**
- If ANY slot is loading, show group loading state
- When ALL slots are ready, show all slot content

### Convenience Helpers

```python
from pynext.core.slot import sidebar_slot, main_slot, modal_slot

# Pre-configured slots
sidebar_slot(loading=MySkeleton)  # class="sidebar-slot"
main_slot(loading=MySkeleton)     # class="main-slot"
modal_slot()                       # class="modal-slot"
```

---

## Streaming Runtime

### Client-Side JavaScript

```javascript
// Minimal runtime for slot updates (~300 bytes)
window.__pynext__.slots = {
  // Update slot content from stream
  update: function(name, content) {
    var slot = document.querySelector('[data-slot="' + name + '"]');
    if (slot) {
      slot.innerHTML = content;
      slot.setAttribute('data-slot-state', 'ready');
    }
  },
  
  // Set loading state
  setLoading: function(name) {
    var slot = document.querySelector('[data-slot="' + name + '"]');
    if (slot) {
      slot.setAttribute('data-slot-state', 'loading');
    }
  },
  
  // Set error state
  setError: function(name, message) {
    var slot = document.querySelector('[data-slot="' + name + '"]');
    if (slot) {
      slot.innerHTML = '<div class="slot-error">' + message + '</div>';
      slot.setAttribute('data-slot-state', 'error');
    }
  }
};
```

### Streaming Protocol

```html
<!-- Initial page with placeholders -->
<div data-slot="sidebar" data-slot-state="loading">
  <div class="skeleton">...</div>
</div>
<div data-slot="main" data-slot-state="loading">
  <div class="skeleton">...</div>
</div>

<!-- Streamed updates (as each slot completes) -->
<script>__pynext__.slots.update('sidebar', '<nav>...</nav>');</script>
<!-- ... later ... -->
<script>__pynext__.slots.update('main', '<article>...</article>');</script>
```

---

## Slot CSS

### Built-in Styles

```css
/* Base slot styles */
.pynext-slot {
  position: relative;
}

/* Loading overlay */
.pynext-slot[data-slot-state="loading"]::after {
  content: "";
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.8);
}

/* Pending state (empty placeholder) */
.pynext-slot[data-slot-state="pending"] {
  min-height: 100px;
}

/* Loading animation */
.slot-loading {
  animation: slot-pulse 1.5s ease-in-out infinite;
}

@keyframes slot-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Error state */
.slot-error {
  color: #dc2626;
  padding: 1rem;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 0.25rem;
}

/* Ready animation */
.pynext-slot[data-slot-state="ready"] {
  animation: slot-fade-in 0.2s ease-out;
}

@keyframes slot-fade-in {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}
```

### Custom Slot Styling

```css
/* Custom sidebar slot */
.sidebar-slot {
  width: 280px;
  background: var(--sidebar-bg);
  border-right: 1px solid var(--border);
}

.sidebar-slot[data-slot-state="loading"] {
  background: var(--skeleton-bg);
}

/* Custom main slot */
.main-slot {
  flex: 1;
  padding: 2rem;
}

/* Custom modal slot */
.modal-slot:not(:empty) {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
}
```

---

## Common Patterns

### Dashboard Layout

```python
# pages/dashboard/layout.py
@layout
def dashboard_layout():
    return div(class_="dashboard")[
        header()[
            Slot("header", loading=HeaderSkeleton)
        ],
        div(class_="dashboard-body")[
            aside()[
                Slot("sidebar", loading=SidebarSkeleton)
            ],
            main()[
                Slot("main", loading=ContentSkeleton)
            ],
        ],
    ]

# pages/dashboard/@header/page.py
def dashboard_header():
    return nav()[
        Logo(),
        SearchBar(),
        UserMenu(),
    ]

# pages/dashboard/@sidebar/page.py
def dashboard_sidebar():
    return nav(class_="nav-menu")[
        NavLink("/dashboard", "Overview"),
        NavLink("/dashboard/projects", "Projects"),
        NavLink("/dashboard/settings", "Settings"),
    ]

# pages/dashboard/@main/page.py
def dashboard_overview():
    stats = createResource(fetch_dashboard_stats)
    return div()[
        h1()["Dashboard"],
        StatsGrid(stats),
    ]
```

### Master-Detail View

```python
# pages/products/layout.py
@layout
def products_layout():
    return div(class_="master-detail")[
        div(class_="master")[
            Slot("list", loading=ListSkeleton)
        ],
        div(class_="detail")[
            Slot("detail", loading=DetailSkeleton)
        ],
    ]

# pages/products/@list/page.py
def product_list():
    products = createResource(fetch_products)
    return ul(class_="product-list")[
        [ProductItem(p) for p in products()]
    ]

# pages/products/@detail/default.py
def detail_placeholder():
    return div(class_="empty-state")[
        p()["Select a product to view details"]
    ]

# pages/products/@detail/[id]/page.py
def product_detail(id: str):
    product = createResource(lambda: fetch_product(id))
    return article()[
        h1()[product().name],
        p()[product().description],
        Price(product().price),
    ]
```

### Modal Pattern

```python
# pages/layout.py
@layout
def root_layout():
    return div()[
        Slot("page"),
        Slot("modal"),  # Overlay for modals
    ]

# pages/@modal/default.py
def empty_modal():
    return ""  # Nothing by default

# pages/@modal/photo/[id]/page.py (via intercepting route)
def photo_modal(id: str):
    photo = createResource(lambda: fetch_photo(id))
    return div(class_="modal-backdrop", onclick="closeModal()")[
        div(class_="modal-content")[
            img(src=photo().url, alt=photo().title),
            h2()[photo().title],
        ]
    ]
```

---

## Performance Comparison

### Bundle Size

| Approach | Page JS Size | Notes |
|----------|--------------|-------|
| Full Page Hydration | ~50KB | Everything hydrated |
| Next.js Parallel Routes | ~30KB | Still hydrates all slots |
| **PyNext Parallel Routes** | **~5KB** | Only interactive slots |

### Loading Performance

| Metric | Sequential | Parallel + Streaming |
|--------|------------|---------------------|
| TTFB | 500ms (slowest slot) | **50ms (first slot)** |
| First Content | 500ms | **50ms** |
| Full Load | 500ms | **500ms** (unchanged) |
| Perceived Speed | ★★☆☆☆ | **★★★★★** |

### Cache Efficiency

| Approach | Cache Granularity | Invalidation |
|----------|-------------------|--------------|
| Page-level | Entire page | All or nothing |
| **Slot-level** | **Per slot** | **Fine-grained** |

Example: Sidebar changes → Only sidebar cache invalidated, main content stays cached.

---

## CLI Integration

### Build Command

```bash
pynext build --pages ./pages --output ./dist

# Output:
# [PyNext] Building for production...
# [PyNext] Compiling parallel routes...
# [PyNext] Compiled 4 parallel slots:
# [PyNext]   → Static slots: 2
# [PyNext]   → Interactive slots: 2
# [PyNext]   → Slot-level caching enabled
# [PyNext] Build complete: dist
```

### Build Output

```
dist/
├── _parallel/
│   ├── parallel-manifest.json    # Compiled slot hierarchies
│   └── bundles/
│       └── a1b2c3d4e5f6.js      # Per-slot bundles
└── pages/
    └── ... (rendered pages)
```

---

## API Reference

### Components

| Component | Props | Description |
|-----------|-------|-------------|
| `Slot(name, ...)` | `name`, `loading`, `error`, `default`, `className`, `stream` | Slot placeholder |
| `SlotGroup(...)` | `loading`, `error`, children | Grouped slots |

### Configuration

| Class | Fields | Description |
|-------|--------|-------------|
| `SlotConfig` | `name`, `default`, `loading`, `error`, `cache_ttl`, `stream_independent` | Per-slot config |
| `ParallelBuildConfig` | `pages_dir`, `output_dir`, `cache_dir`, `analyze_hydration`, `generate_bundles` | Build config |

### Functions

| Function | Returns | Description |
|----------|---------|-------------|
| `get_parallel_scanner()` | `ParallelRouteScanner` | Global scanner |
| `scan_parallel_routes(pages_dir)` | `Dict[str, CompiledSlotHierarchy]` | Scan for routes |
| `get_slot_hierarchy(layout_path)` | `CompiledSlotHierarchy` | Get hierarchy |
| `compile_parallel_routes(...)` | `ParallelRoutesManifest` | Full compilation |
| `get_slot_cache()` | `SlotCacheManager` | Cache manager |
| `invalidate_slot(slot_id)` | `int` | Invalidate slot cache |
| `invalidate_slot_tag(tag)` | `int` | Invalidate by tag |

### Context

| Function | Returns | Description |
|----------|---------|-------------|
| `get_slot_context()` | `SlotContext` | Current context |
| `create_slot_context()` | `SlotContext` | New context |
| `set_slot_content(name, content)` | `None` | Set slot content |

---

## Troubleshooting

### Slots Not Rendering

1. **Check @folder naming:**
   ```
   ✓ pages/@sidebar/page.py
   ✗ pages/sidebar/page.py     # Missing @
   ```

2. **Verify layout has Slot:**
   ```python
   # In layout.py
   Slot("sidebar")  # Must match @sidebar
   ```

### Streaming Not Working

1. **Ensure stream=True (default):**
   ```python
   Slot("main", stream=True)
   ```

2. **Check for blocking code:**
   ```python
   # ❌ Blocking all slots
   await slow_operation()
   
   # ✅ Non-blocking
   task = asyncio.create_task(slow_operation())
   ```

### Cache Issues

1. **Verify TTL configuration:**
   ```python
   SlotConfig("sidebar", cache_ttl=3600)  # 3600 seconds
   ```

2. **Check invalidation:**
   ```python
   invalidate_slot("@sidebar")  # Include @ prefix
   ```

---

## Summary

PyNext Parallel Routes provide:

✅ **Build-Time Compilation** - Zero runtime slot resolution  
✅ **Independent Streaming** - Each slot streams as ready  
✅ **Selective Hydration** - Only interactive slots need JS  
✅ **Slot-Level Caching** - Fine-grained ISR per slot  
✅ **@folder Convention** - Intuitive file structure  
✅ **SlotGroup** - Coordinated slot loading  
✅ **Minimal Runtime** - ~300 bytes streaming JS  

**Result:** Fastest possible parallel content loading with minimal JavaScript.

