# PyNext 🐍⚡

A Python web framework that brings **Next.js-style routing** and **SolidJS-inspired fine-grained reactivity** to the Python ecosystem.

## Features

- 📁 **File-based Routing** - Create pages in `pages/` and routes are automatically generated
- ⚡ **Fine-grained Reactivity** - Signals, Effects, Memos, and Stores for precise DOM updates
- 🐍 **Server Actions** - Call Python functions from the client with full package access
- 📦 **NPM Integration** - Use npm packages with automatic bundling via esbuild
- 🔥 **Hot Reloading** - Instant updates during development
- 🎨 **Pythonic API** - Clean, decorator-based component syntax
- ⏳ **Suspense & Streaming** - Progressive rendering with loading states (5,000x faster TTFB)
- 🛡️ **Error Boundaries** - Graceful error handling with fallbacks
- 🏝️ **Islands Architecture** - Selective hydration for 95%+ smaller JS bundles
- 📦 **Code Splitting** - Lazy loading with per-route bundles and smart prefetching
- 🎬 **View Transitions** - Smooth page transitions with the View Transitions API
- 🖼️ **Image Optimization** - Build-time processing, AVIF/WebP, zero JS for static images
- 📄 **Static Site Generation** - Zero JS for static pages, incremental builds
- ♻️ **Incremental Static Regeneration** - Component-level cache invalidation
- 🔀 **Edge Middleware** - O(1) route matching, streaming, lazy loading
- 🌍 **Internationalization** - Signal-based i18n with direct DOM updates (no re-renders)

## Documentation

### Core Guides
| Guide | Description |
|-------|-------------|
| **[Getting Started](docs/GETTING_STARTED.md)** | Installation, first project, tutorial walkthrough |
| **[Routing](docs/ROUTING.md)** | File-based routing, dynamic routes, navigation |
| **[Layouts](docs/LAYOUTS.md)** | Nested layouts, loading states, error boundaries |
| **[HTML API](docs/HTML_API.md)** | All elements, attributes, event handlers |
| **[State Management](docs/STATE_MANAGEMENT.md)** | Signals, Stores, Computed, Effects |
| **[Server Actions](docs/SERVER_ACTIONS.md)** | RPC, Python packages, security |
| **[API Routes](docs/API_ROUTES.md)** | REST endpoints, HTTP methods, responses |
| **[Configuration](docs/CONFIGURATION.md)** | All config options, environments |

### Advanced Guides
| Guide | Description |
|-------|-------------|
| **[Hydration](docs/HYDRATION.md)** | Server→Client state transfer, Resource hydration |
| **[Streaming & Suspense](docs/STREAMING_SUSPENSE.md)** | Progressive rendering, out-of-order streaming, benchmarks |
| **[Islands Architecture](docs/ISLANDS.md)** | Selective hydration, @island decorator, 95%+ smaller bundles |
| **[Code Splitting](docs/CODE_SPLITTING.md)** | Lazy loading, per-route bundles, prefetching |
| **[Transitions](docs/TRANSITIONS.md)** | View Transitions API, SPA navigation, animations |
| **[Image Optimization](docs/IMAGE_OPTIMIZATION.md)** | Build-time processing, zero JS, AVIF-first |
| **[Font Optimization](docs/FONT_OPTIMIZATION.md)** | Zero layout shift, zero JS, build-time size-adjust |
| **[Script Optimization](docs/SCRIPT_OPTIMIZATION.md)** | Zero wrapper JS, native loading, build-time analysis |
| **[Static Generation](docs/STATIC_GENERATION.md)** | SSG with zero JS detection, incremental builds |
| **[ISR](docs/ISR.md)** | Component-level cache invalidation, on-demand revalidation |
| **[Middleware](docs/MIDDLEWARE.md)** | Edge middleware, O(1) matching, streaming |
| **[Internationalization](docs/I18N.md)** | Signal-based i18n, direct DOM updates, lazy loading |
| **[Partial Prerendering](docs/PARTIAL_PRERENDERING.md)** | Component-level PPR, static shells, dynamic holes |
| **[Parallel Routes](docs/PARALLEL_ROUTES.md)** | Independent streaming, slot-level caching, selective hydration |
| **[Intercepting Routes](docs/INTERCEPTING_ROUTES.md)** | Modal patterns, static background, URL-driven state |
| **[State + Data Integration](docs/STATE_DATA_INTEGRATION.md)** | Signals with Server Actions & API Routes |
| **[State Patterns](docs/STATE_PATTERNS.md)** | Forms, async, state machines, advanced patterns |
| **[React Integration](docs/REACT_INTEGRATION.md)** | Using React/npm components |
| **[NPM Packages](docs/NPM_PACKAGES.md)** | Chart.js, D3, lodash, bundle optimization |
| **[CLI Reference](docs/CLI.md)** | Commands, options, environment variables |
| **[Testing](docs/TESTING.md)** | Unit tests, integration, E2E with Playwright |
| **[Deployment](docs/DEPLOYMENT.md)** | Docker, cloud platforms, production setup |

## Quick Start

```bash
# Create a new project
pynext init my-app

# Navigate and start dev server
cd my-app
pip install pynext
pynext dev

# Open http://localhost:3000
```

## Component Syntax

PyNext uses a Pythonic, decorator-based syntax for components:

```python
from pynext import component, page, Signal, div, h1, button, span

@component
def Counter():
    count = Signal(0)
    
    return div(class_="counter")[
        h1()["Count: ", span()[count]],
        button(onclick=lambda: count.update(lambda x: x + 1))["Increment"]
    ]

@page(title="Home")
def index():
    return div()[
        h1()["Welcome to PyNext!"],
        Counter()
    ]
```

## Reactive Primitives

### Signal
A reactive value that triggers updates when changed:

```python
from pynext import Signal

count = Signal(0)
name = Signal("World")

# Read
print(count())  # 0

# Write
count.set(5)
count.update(lambda x: x + 1)
```

### Computed / Memo
Derived values that auto-update:

```python
from pynext import Signal, Computed

count = Signal(5)
doubled = Computed(lambda: count() * 2)

print(doubled())  # 10
count.set(10)
print(doubled())  # 20
```

### Store
Nested reactive state:

```python
from pynext import Store

user = Store({
    "name": "Alice",
    "settings": {"theme": "dark"}
})

# Access
print(user.name)  # "Alice"
print(user.settings.theme)  # "dark"

# Update
user.name = "Bob"
user.settings.theme = "light"
```

### Effect
Side effects that run when dependencies change:

```python
from pynext import Signal, Effect

count = Signal(0)

@Effect
def log_changes():
    print(f"Count changed to: {count()}")
```

### Resource
Async data fetching with automatic loading/error states:

```python
from pynext import Resource, Signal

# Simple resource
users = Resource(fetch_users)
await users.fetch()

# Resource with reactive source (refetches when source changes)
user_id = Signal(1)
user = Resource(fetch_user, source=user_id)

# Access states
user.loading()   # True while fetching
user.error()     # Exception if failed
user()           # The data
user.latest      # Last successful value (stale during refresh)

# Operations
await user.refetch()     # Force refetch
await user.mutate(data)  # Optimistic update
user.invalidate()        # Mark stale
```

> 📖 **Full Documentation:** [Hydration Guide](docs/HYDRATION.md) - Resource hydration, payload optimization

### Suspense
Show loading states while async data loads:

```python
from pynext import Suspense, Show, Switch, Match, ErrorBoundary

# Suspense with fallback while loading
Suspense(fallback=Skeleton())[
    UserProfile()  # Shows Skeleton until data ready
]

# Conditional rendering
Show(when=user.loading, fallback=Spinner())[
    UserCard(user=user())
]

# Multi-way conditional
Switch()[
    Match(when=lambda: status() == "loading")[Spinner()],
    Match(when=lambda: status() == "error")[ErrorMessage()],
    Match()[Content()]  # Default
]

# Error boundary for graceful degradation
ErrorBoundary(fallback=lambda e: ErrorDisplay(e))[
    RiskyComponent()
]
```

> 📖 **Full Documentation:** [Streaming & Suspense](docs/STREAMING_SUSPENSE.md) - Progressive rendering, benchmarks

### Islands (Selective Hydration)
Only hydrate interactive components - static content stays as pure HTML:

```python
from pynext import island, static, Signal, HydrationStrategy

@island  # 🏝️ Only this component gets JavaScript
def Counter():
    count = Signal(0)
    return button(onclick=lambda: count.set(count() + 1))[
        "Count: ", count
    ]

@island(strategy=HydrationStrategy.VISIBLE)  # Hydrate when scrolled into view
def LazyChart():
    return ChartComponent(data=chart_data)

@static  # Explicitly no JavaScript
def Footer():
    return footer()["© 2024 Company"]

@page
def HomePage():
    return div()[
        h1()["Welcome"],     # Static - 0 bytes JS
        Counter(),            # 🏝️ Island - ~500 bytes JS
        LazyChart(),          # 🏝️ Island - loads on scroll
        Footer(),             # Static - 0 bytes JS
    ]
```

**Result:** 95%+ smaller JavaScript bundles vs full hydration!

> 📖 **Full Documentation:** [Islands Architecture](docs/ISLANDS.md) - Strategies, bundle analysis, best practices

## State Management

PyNext uses **fine-grained reactivity** - state changes update only the specific DOM nodes that depend on them, not entire components.

> 📖 **Full Documentation:**
> - [State Management Guide](docs/STATE_MANAGEMENT.md) - Core concepts and API
> - [Advanced State Patterns](docs/STATE_PATTERNS.md) - Forms, async, state machines

### How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                     Signal Update Flow                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   count.set(5)                                                  │
│        │                                                         │
│        ▼                                                         │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │              Signal notifies subscribers                 │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                    │                    │               │
│        ▼                    ▼                    ▼               │
│   ┌──────────┐       ┌──────────┐        ┌──────────┐          │
│   │  DOM     │       │ Computed │        │  Effect  │          │
│   │ span     │       │ doubled  │        │ logger   │          │
│   │ updates  │       │ recalcs  │        │ runs     │          │
│   └──────────┘       └──────────┘        └──────────┘          │
│                                                                  │
│   No virtual DOM diffing - direct, surgical updates!            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### State Primitives Summary

| Primitive | Purpose | Example |
|-----------|---------|---------|
| `Signal` | Single reactive value | `count = Signal(0)` |
| `Store` | Nested reactive object | `user = Store({"name": "Alice"})` |
| `Computed` | Derived value (auto-deps) | `doubled = Computed(lambda: count() * 2)` |
| `Effect` | Side effects (auto-deps) | `@Effect def log(): print(count())` |
| `Resource` | Async data with states | `users = Resource(fetch_users)` |
| `Suspense` | Loading boundaries | `Suspense(fallback=Spinner())[Content()]` |
| `Show` | Conditional rendering | `Show(when=visible)[Content()]` |
| `ErrorBoundary` | Error handling | `ErrorBoundary(fallback=...)[Risky()]` |
| `@island` | Selective hydration | `@island def Widget(): ...` |
| `@static` | No hydration | `@static def Footer(): ...` |
| `batch` | Group updates | `batch(lambda: (a.set(1), b.set(2)))` |

### Server-to-Client Flow

```python
# Python (Server)
count = Signal(0)

@page
def my_page():
    return span()[count]  # Renders with hydration markers

# HTML Output
# <span data-signal="sig_123">0</span>
# <script>window.__PYNEXT_HYDRATION__ = {...}</script>

# JavaScript (Client) 
# Hydrates signals, attaches event handlers
# count.set(5) → Updates only this span element
```

## File-based Routing

Create files in the `pages/` directory:

```
pages/
├── index.py        → /
├── about.py        → /about
├── users/
│   ├── index.py    → /users
│   └── [id].py     → /users/:id
└── docs/
    └── [...slug].py → /docs/* (catch-all)
```

### Dynamic Routes

```python
# pages/users/[id].py
from pynext import page, get_params

@page(title="User Profile")
def user_profile():
    params = get_params()
    user_id = params.get("id")
    
    return div()[f"User ID: {user_id}"]
```

## Server Actions

Call Python functions from the client with full access to the Python ecosystem.

> 📖 **Full Documentation:**
> - [Server Actions Guide](docs/SERVER_ACTIONS.md) - Complete RPC system, security, and patterns

```python
from pynext import server_action, button
import pandas as pd  # Use any Python package!

@server_action
async def analyze_data(file_path: str) -> dict:
    df = pd.read_csv(file_path)
    return {
        "rows": len(df),
        "columns": list(df.columns),
        "summary": df.describe().to_dict()
    }

# In your component
button(onclick=lambda: analyze_data("/data/sales.csv"))["Analyze"]
```

### How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                  Server Action Flow                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   BROWSER                          SERVER                        │
│   ────────                         ──────                        │
│                                                                  │
│   button click                                                   │
│        │                                                         │
│        ▼                                                         │
│   callAction()  ──── POST /_pynext/action ────▶  FastAPI        │
│                      {actionId, args}            Endpoint        │
│                                                     │            │
│                                                     ▼            │
│                                              Action Registry     │
│                                                     │            │
│                                                     ▼            │
│                                              @server_action      │
│                                              async def analyze() │
│                                                 import pandas    │
│                                                 ...full Python!  │
│                                                     │            │
│   Update UI     ◀──── {data: {...}} ────────────────┘           │
│   (Signals)                                                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Features

| Feature | Description |
|---------|-------------|
| **Full Python** | Use pandas, numpy, scikit-learn, any pip package |
| **Type Hints** | Automatic validation with Pydantic |
| **Async/Sync** | Both supported (sync runs in thread pool) |
| **JSON-RPC** | Simple `{actionId, args}` → `{data, error}` protocol |
| **File Access** | Read/write files, database connections |
| **Security** | Built-in patterns for auth, rate limiting, validation |

## NPM Integration

Use npm packages in your PyNext apps:

```python
# pynext.config.py
npm_packages = [
    "chart.js",
    "lodash",
    {"d3": "^7.0.0"}
]
```

```python
from pynext.bundler import npm_import

chart_url = npm_import("chart.js")
# Use in your component...
```

## HTML Elements

PyNext provides all standard HTML elements:

```python
from pynext import (
    # Layout
    div, span, section, article, header, footer, nav, main,
    
    # Text
    h1, h2, h3, p, a, strong, em, code, pre,
    
    # Forms
    form, input_, textarea, button, select, option, label,
    
    # Lists
    ul, ol, li,
    
    # Tables
    table, thead, tbody, tr, th, td,
    
    # Media
    img, video, audio, canvas, svg,
)

# Fluent API
div(class_="container", id="main")[
    h1()["Title"],
    p()["Paragraph with ", strong()["bold"], " text"]
]
```

## CLI Commands

```bash
# Start development server
pynext dev

# Build for production
pynext build

# Initialize new project
pynext init my-app

# List all routes
pynext routes
```

## Project Structure

```
my-app/
├── pages/              # Page components (file-based routing)
│   ├── index.py
│   └── about.py
├── components/         # Reusable components
├── public/             # Static files
├── pynext.config.py    # Configuration
└── pyproject.toml
```

## Configuration

```python
# pynext.config.py

# NPM packages to bundle
npm_packages = [
    "chart.js",
]

# Build options
build = {
    "output": ".pynext/build",
    "minify": True,
}
```

## How It Works

PyNext uses a **hybrid rendering model**:

1. **Server-side**: Python components render to HTML with reactive markers
2. **Client-side**: A minimal (~5KB) JavaScript runtime hydrates the page
3. **Reactivity**: Changes to Signals update only affected DOM nodes

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Python         │     │  Server Actions  │     │  JS Runtime     │
│  Components     │────▶│  (RPC Bridge)    │────▶│  (Signals)      │
│  @component     │     │  @server_action  │     │  Hydration      │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

## Requirements

- Python 3.10+
- Node.js (for npm integration, optional)

## React Component Support

PyNext supports React npm packages via **Preact aliasing** (~4KB vs ~40KB).

> 📖 **[Full Documentation: React Integration Guide](docs/REACT_INTEGRATION.md)**

### Quick Example

```python
from pynext import page, Signal, div, span, ReactComponent

@page
def dashboard():
    value = Signal(50)
    
    return div()[
        # Native PyNext - instant DOM updates
        span()["Value: ", value],
        
        # React component with shared signal
        ReactComponent(
            package="@mui/material",
            component="Slider",
            props={
                "value": value,           # Signal passed as prop
                "onChange": value.set,     # Signal setter as callback
                "min": 0,
                "max": 100
            }
        )
    ]
```

### Key Features

| Feature | Description |
|---------|-------------|
| **Preact Aliasing** | React → Preact (~4KB vs ~40KB) |
| **Signal Integration** | PyNext signals work as React props |
| **Bi-directional Updates** | React events update PyNext signals |
| **Auto-detection** | Common React packages detected automatically |
| **~99% Compatibility** | Works with MUI, Chakra, Radix, etc. |

### Configuration

```python
# pynext.config.py
react_compat = True  # Enable react → preact aliasing

npm_packages = [
    "@mui/material",
    "@emotion/react",
    "@emotion/styled",
]
```

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     PyNext Signal                                │
│                     value = Signal(50)                           │
└───────────────────────────┬─────────────────────────────────────┘
                            │
          ┌─────────────────┼─────────────────┐
          ▼                                   ▼
┌─────────────────────┐              ┌─────────────────────┐
│  Native PyNext      │              │  React Component    │
│  span()[value]      │◄────────────►│  (via Preact)       │
│  Direct DOM update  │    Shared    │  Virtual DOM        │
│  ~0.1ms             │    State     │  ~1-2ms             │
└─────────────────────┘              └─────────────────────┘
```

See the [full React integration guide](docs/REACT_INTEGRATION.md) for advanced usage, troubleshooting, and API reference

## Image Optimization

Build-time image processing with **zero JavaScript** for static images:

```python
from pynext import Image, PriorityImage

# Zero JS - native lazy loading, AVIF-first
Image(
    src="/images/hero.jpg",
    alt="Hero image",
    width=1920,
    height=1080,
)

# Priority image with preload
PriorityImage(src="/images/lcp.jpg", alt="Above fold")
```

> 📖 **[Full Documentation: Image Optimization](docs/IMAGE_OPTIMIZATION.md)**

## Static Site Generation

**Zero JavaScript** for static pages:

```python
from pynext import static_page, static_props

@static_page()
def about():
    """This ships ZERO JavaScript!"""
    return div(h1("About"), p("Static content"))

@static_props
async def get_props(params):
    """Runs at build time."""
    return {"data": await fetch_data()}
```

> 📖 **[Full Documentation: Static Generation](docs/STATIC_GENERATION.md)**

## Incremental Static Regeneration

**Component-level** cache invalidation:

```python
from pynext import revalidate, revalidate_tag

@revalidate(seconds=60, tags=["products"])
def product_list():
    return div([product_card(p) for p in fetch_products()])

# On-demand revalidation
await revalidate_tag("products")
```

> 📖 **[Full Documentation: ISR](docs/ISR.md)**

## Edge Middleware

**O(1) route matching** with streaming:

```python
from pynext import middleware, NextResponse

@middleware(matcher="/admin/*")
async def auth(ctx):
    if not ctx.get_cookie("token"):
        return NextResponse.redirect("/login")
    return NextResponse.next()
```

> 📖 **[Full Documentation: Middleware](docs/MIDDLEWARE.md)**

## Internationalization

**Signal-based i18n** with direct DOM updates (no re-renders):

```python
from pynext import t, set_locale

# Translate
h1(t("welcome"))  # "Welcome" or "Bienvenue"

# Switch locale - only text nodes update!
set_locale("fr")
```

> 📖 **[Full Documentation: Internationalization](docs/I18N.md)**

## Font Optimization

Zero layout shift typography with zero JavaScript:

```python
from pynext import Font, GoogleFont

# Google Fonts - downloaded and optimized at build time
heading = GoogleFont("Playfair Display", weight=700)
body = GoogleFont("Inter", weight=[400, 500, 700])

def Page():
    return div()[
        h1(class_=heading)["Beautiful Typography"],
        p(class_=body)["With precomputed size-adjust for zero CLS."],
    ]
```

**What happens at build time:**
- Downloads fonts locally (no CDN dependency)
- Extracts font metrics (ascender, x-height, etc.)
- Computes `size-adjust` values for fallback fonts
- Subsets to used characters (300KB → 20KB)
- Converts to WOFF2 for optimal compression

**Result:** `font-display: swap` with zero layout shift, zero JavaScript.

> 📖 **[Full Documentation: Font Optimization](docs/FONT_OPTIMIZATION.md)**

## PyNext vs Next.js Performance

| Feature | Next.js | PyNext |
|---------|---------|--------|
| Image JS | ~15KB | **0 KB** |
| Font JS | ~3KB | **0 KB** |
| Font CLS | Runtime adjust | **Build-time adjust** |
| SSG Hydration | Full tree | **Islands only** |
| ISR Granularity | Page | **Component** |
| Middleware Cold Start | ~50ms | **<5ms** |
| i18n Locale Switch | Re-render | **Text-only update** |

## Dependencies

- `fastapi` - Modern ASGI framework with automatic OpenAPI docs
- `uvicorn` - ASGI server
- `watchfiles` - File watching for hot reload
- `orjson` - Fast JSON serialization
- `pydantic` - Data validation and settings
- `jinja2` - Template engine

## API Documentation

In debug mode, FastAPI provides automatic API documentation:

- **Swagger UI**: `http://localhost:3000/_pynext/docs`
- **ReDoc**: `http://localhost:3000/_pynext/redoc`
- **OpenAPI JSON**: `http://localhost:3000/_pynext/openapi.json`

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

