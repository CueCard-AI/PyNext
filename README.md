# PyNext 🐍⚡

**Build modern, reactive web apps in pure Python.**

PyNext combines the best ideas from modern JavaScript frameworks—but lets you write everything in Python. Get Next.js-style file routing, SolidJS-inspired reactivity, and the entire Python ecosystem on your server.

```python
from pynext import page, Signal, div, h1, button, span

@page
def home():
    count = Signal(0)
    
    return div()[
        h1()["Welcome to PyNext!"],
        button(onclick=lambda: count.set(count() + 1))[
            "Clicked ", span()[count], " times"
        ]
    ]
```

That's it. No JavaScript. No build step for basic apps. Just Python.

---

## Why PyNext?

### The Problem

Building modern web apps typically means:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     THE TRADITIONAL STACK                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   Your Python Backend                Your JavaScript Frontend               │
│   ──────────────────                 ────────────────────────               │
│   • FastAPI/Django/Flask             • React/Vue/Svelte                     │
│   • Business logic                   • UI components                        │
│   • Database access                  • State management                     │
│   • ML/Data processing               • API calls back to Python             │
│                                                                              │
│                          ┌─────────────┐                                    │
│                          │   REST API  │                                    │
│                          │   GraphQL   │                                    │
│                          │   JSON      │                                    │
│                          └─────────────┘                                    │
│                                                                              │
│   You end up maintaining TWO codebases, TWO languages, TWO mental models.  │
│   Data serialization overhead. Type mismatches. Double the complexity.      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### The PyNext Solution

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         THE PYNEXT STACK                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                         JUST PYTHON                                          │
│                         ───────────                                          │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                                                                      │   │
│   │     @page                                                            │   │
│   │     def dashboard():                                                 │   │
│   │         users = Resource(fetch_users)         # Async data           │   │
│   │         theme = Signal("dark")                # Reactive state       │   │
│   │                                                                      │   │
│   │         return div()[                                                │   │
│   │             UserTable(users=users),           # Component            │   │
│   │             ThemeToggle(theme=theme)          # Interactive          │   │
│   │         ]                                                            │   │
│   │                                                                      │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│   • One language, one codebase, one mental model                            │
│   • Full Python ecosystem (pandas, numpy, scikit-learn, etc.)               │
│   • Reactive UI with surgical DOM updates                                   │
│   • Server Actions: call Python from button clicks                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Vision

**PyNext exists because Python developers deserve a first-class web framework.**

Not a Python-to-JavaScript transpiler. Not a wrapper around React. A framework that:

1. **Embraces Python's strengths** — Dynamic typing, decorators, the massive package ecosystem
2. **Learns from JavaScript's best ideas** — Fine-grained reactivity, file-based routing, islands architecture
3. **Ships minimal JavaScript** — Only what's needed for interactivity
4. **Keeps complexity low** — No virtual DOM, no hydration mismatches, no "use client" directives

---

## Design Inspirations

PyNext stands on the shoulders of giants:

| Framework | What We Learned |
|-----------|-----------------|
| **Next.js** | File-based routing, layouts, server components, ISR, middleware |
| **SolidJS** | Fine-grained reactivity (Signals), no virtual DOM, surgical updates |
| **Astro** | Islands architecture, ship minimal JavaScript, content-first |
| **HTMX** | Server-driven UI, HTML as the hypermedia |
| **FastAPI** | Pythonic API design, automatic docs, modern async |

### The Key Insight: Fine-Grained Reactivity

Most frameworks (React, Vue) use a **virtual DOM**: when state changes, they re-render components and diff against the previous output.

PyNext uses **fine-grained reactivity** (like SolidJS): when state changes, we update **only the exact DOM nodes** that depend on that state.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              VIRTUAL DOM (React)              FINE-GRAINED (PyNext)         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   count.set(5)                               count.set(5)                   │
│        │                                          │                         │
│        ▼                                          ▼                         │
│   Re-render component                        Signal notifies                │
│        │                                          │                         │
│        ▼                                          ▼                         │
│   Create virtual DOM                         Update <span>                  │
│        │                                     (direct mutation)              │
│        ▼                                                                    │
│   Diff with previous                         Done! (~0.1ms)                 │
│        │                                                                    │
│        ▼                                                                    │
│   Apply patches                                                             │
│        │                                                                    │
│        ▼                                                                    │
│   Done! (~2-5ms)                                                            │
│                                                                              │
│   More work, but enables                     Less work, faster updates,     │
│   time-slicing, suspense                     simpler mental model           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Core Concepts

### 1. Signals: Reactive Values

A Signal is a container for a value that can notify subscribers when it changes.

```python
from pynext import Signal

count = Signal(0)       # Create with initial value

count()                 # Read: returns 0
count.set(5)            # Write: sets to 5
count.update(lambda x: x + 1)  # Update: applies function
```

**Why Signals?** They're the foundation of reactivity. When you put a Signal in your UI, PyNext automatically tracks the dependency and updates just that part when the Signal changes.

```python
# Only the <span> updates when count changes, not the whole component
button()[
    "Clicked ", span()[count], " times"  
]
```

### 2. Pages: File-Based Routing

Create a file, get a route. No configuration needed.

```
pages/
├── index.py        → /
├── about.py        → /about
├── blog/
│   ├── index.py    → /blog
│   └── [slug].py   → /blog/:slug (dynamic)
└── docs/
    └── [...path].py → /docs/* (catch-all)
```

```python
# pages/blog/[slug].py
from pynext import page, get_params

@page(title="Blog Post")
def blog_post():
    params = get_params()
    slug = params["slug"]  # From URL
    
    return article()[
        h1()[f"Post: {slug}"]
    ]
```

### 3. Server Actions: RPC to Python

Call Python functions directly from UI events. No REST API needed.

```python
from pynext import server_action, Signal, button, div
import pandas as pd  # Use ANY Python package!

@server_action
async def analyze_csv(file_path: str) -> dict:
    df = pd.read_csv(file_path)  # Full Python power
    return {
        "rows": len(df),
        "mean": df["sales"].mean(),
        "top_product": df.groupby("product")["sales"].sum().idxmax()
    }

@page
def analytics():
    result = Signal(None)
    
    async def run_analysis():
        result.set(await analyze_csv("/data/sales.csv"))
    
    return div()[
        button(onclick=run_analysis)["Analyze Sales Data"],
        Show(when=result)[
            div()[f"Found {result()['rows']} rows"]
        ]
    ]
```

**How it works:**

```
Browser                                Server
───────                                ──────
button click
    │
    ▼
POST /_pynext/action ─────────────────▶ FastAPI receives
    {action: "analyze_csv",              │
     args: ["/data/sales.csv"]}          ▼
                                      @server_action runs
                                      (full Python access)
                                         │
Update Signal ◀─────────────────────── Return JSON
Update DOM (just the result div)
```

### 4. Components: Reusable UI

```python
from pynext import component, Signal, div, button, span

@component
def Counter(initial: int = 0):
    count = Signal(initial)
    
    return div(class_="counter")[
        span()[count],
        button(onclick=lambda: count.update(lambda x: x + 1))["+"],
        button(onclick=lambda: count.update(lambda x: x - 1))["-"],
    ]

# Use it
@page
def home():
    return div()[
        Counter(initial=10),
        Counter(initial=0),
    ]
```

### 5. Layouts: Shared UI

Wrap pages in consistent layouts. Layouts nest automatically.

```python
# pages/layout.py - wraps ALL pages
@layout
def root_layout(children):
    return html()[
        head()[title()["My App"]],
        body()[
            nav()[a(href="/")["Home"], a(href="/about")["About"]],
            main()[children],  # Page content goes here
            footer()["© 2024"]
        ]
    ]

# pages/dashboard/layout.py - wraps /dashboard/* pages
@layout
def dashboard_layout(children):
    return div(class_="dashboard")[
        Sidebar(),
        div(class_="content")[children]
    ]
```

---

## Getting Started

### Install

```bash
pip install pynext
```

### Create a Project

```bash
pynext init my-app
cd my-app
pynext dev
```

Open http://localhost:3000

### Project Structure

```
my-app/
├── pages/              # Routes (file-based)
│   ├── index.py        # → /
│   ├── about.py        # → /about
│   └── layout.py       # Wraps all pages
├── components/         # Reusable components
├── public/             # Static files (images, etc.)
├── pynext.config.py    # Configuration
└── pyproject.toml
```

### Your First Page

```python
# pages/index.py
from pynext import page, Signal, div, h1, p, button

@page(title="Home", description="Welcome to my app")
def home():
    count = Signal(0)
    
    return div(class_="container")[
        h1()["Hello, PyNext!"],
        p()["A reactive Python web framework."],
        
        button(onclick=lambda: count.set(count() + 1))[
        "Count: ", count
    ]
    ]
```

---

## When to Use PyNext

### ✅ Great For

| Use Case | Why PyNext Shines |
|----------|-------------------|
| **Data dashboards** | Python has pandas, numpy, plotly. No need to serialize to JS. |
| **Internal tools** | Fast development, full backend access, simple deployment |
| **ML/AI interfaces** | Call scikit-learn, transformers, etc. directly from UI |
| **Content sites** | Static generation, ISR, zero JS for static pages |
| **Prototypes** | Ship fast, iterate faster, one language to maintain |

### ⚠️ Consider Alternatives For

| Use Case | Better Alternative |
|----------|--------------------|
| Heavy client-side apps (games, editors) | React, Vue, or vanilla JS |
| Existing large React codebase | Keep React, add Python API |
| Team with no Python experience | Stick with JS frameworks |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PYNEXT ARCHITECTURE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                              REQUEST                                         │
│                                 │                                            │
│                                 ▼                                            │
│                         ┌───────────────┐                                   │
│                         │   FastAPI     │                                   │
│                         │   (ASGI)      │                                   │
│                         └───────┬───────┘                                   │
│                                 │                                            │
│               ┌─────────────────┼─────────────────┐                         │
│               ▼                 ▼                 ▼                         │
│      ┌─────────────┐   ┌─────────────┐   ┌─────────────┐                   │
│      │ Middleware  │   │   Router    │   │ API Routes  │                   │
│      │ (auth, i18n)│   │(file-based) │   │ (REST)      │                   │
│      └─────────────┘   └──────┬──────┘   └─────────────┘                   │
│                               │                                             │
│                               ▼                                             │
│                      ┌─────────────────┐                                    │
│                      │  Page Component │                                    │
│                      │  + Layout       │                                    │
│                      └────────┬────────┘                                    │
│                               │                                             │
│               ┌───────────────┼───────────────┐                             │
│               ▼               ▼               ▼                             │
│      ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                     │
│      │  Signals    │  │  Resources  │  │  Suspense   │                     │
│      │  (state)    │  │  (async)    │  │  (loading)  │                     │
│      └─────────────┘  └─────────────┘  └─────────────┘                     │
│                               │                                             │
│                               ▼                                             │
│                      ┌─────────────────┐                                    │
│                      │  HTML Render    │                                    │
│                      │  + Hydration    │                                    │
│                      │  Markers        │                                    │
│                      └────────┬────────┘                                    │
│                               │                                             │
│                               ▼                                             │
│                          RESPONSE                                           │
│                      (HTML + ~5KB JS)                                       │
│                                                                              │
│                               │                                             │
│                               ▼                                             │
│                      ┌─────────────────┐                                    │
│                      │  Browser        │                                    │
│                      │  Hydration      │                                    │
│                      │  (Signals live) │                                    │
│                      └─────────────────┘                                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### The Hydration Process

1. **Server renders** Python components to HTML with reactive markers
2. **Browser receives** HTML (immediately visible) + small JS runtime (~5KB)
3. **JS runtime hydrates** by connecting to marked DOM elements
4. **Signals become live** — user interactions trigger updates

```python
# Python (Server)
count = Signal(0)
span()[count]

# Rendered HTML
<span data-pynext-signal="sig_123">0</span>

# After Hydration (Browser)
# sig_123 is now a live Signal
# count.set(5) → <span> shows "5" instantly
```

---

## Feature Overview

### Rendering Strategies

| Strategy | Use Case | JS Shipped |
|----------|----------|------------|
| **Full Hydration** | Interactive pages | ~5KB + components |
| **Islands** | Mostly static with some interactive parts | ~500B per island |
| **Static (SSG)** | Blogs, docs, marketing | **0 KB** |
| **ISR** | Dynamic content that changes periodically | ~5KB |
| **Streaming** | Large pages, slow data | ~5KB (progressive) |

### State Primitives

| Primitive | Purpose | Example |
|-----------|---------|---------|
| `Signal` | Single reactive value | `count = Signal(0)` |
| `Store` | Nested reactive object | `user = Store({"name": "Alice"})` |
| `Computed` | Derived value | `doubled = Computed(lambda: count() * 2)` |
| `Effect` | Side effects | `@Effect def log(): print(count())` |
| `Resource` | Async data with loading/error | `users = Resource(fetch_users)` |

### Rendering Helpers

| Helper | Purpose | Example |
|--------|---------|---------|
| `Show` | Conditional | `Show(when=visible)[Content()]` |
| `For` | Lists | `For(each=items, render=Item)` |
| `Switch/Match` | Multi-way conditional | `Switch()[Match(when=...)...]` |
| `Suspense` | Loading boundaries | `Suspense(fallback=Spinner())[...]` |
| `ErrorBoundary` | Error handling | `ErrorBoundary(fallback=...)[...]` |

### Performance Features

| Feature | What It Does | Benefit |
|---------|--------------|---------|
| **Islands** | Only hydrate interactive parts | 95%+ smaller JS |
| **Code Splitting** | Per-route bundles, lazy loading | Faster initial load |
| **Image Optimization** | Build-time AVIF/WebP, lazy load | Faster LCP |
| **Font Optimization** | Precomputed fallback metrics | Zero CLS |
| **Streaming** | Progressive HTML delivery | 5,000x faster TTFB |

---

## Comparison

### PyNext vs Next.js

| Aspect | Next.js | PyNext |
|--------|---------|--------|
| **Language** | JavaScript/TypeScript | Python |
| **Reactivity** | Virtual DOM (React) | Fine-grained (Signals) |
| **Server Access** | Server Components, API Routes | Server Actions (direct RPC) |
| **Data Libraries** | Need to serialize to JSON | Use pandas, numpy directly |
| **JS Bundle** | 50-200KB+ | 5KB base, 0 for static |
| **Learning Curve** | React + Next.js concepts | Just Python |

### PyNext vs HTMX

| Aspect | HTMX | PyNext |
|--------|------|--------|
| **Interactivity** | Server-driven HTML swaps | Client-side reactivity |
| **State** | Server-only | Client Signals + Server Actions |
| **Granularity** | Element replacement | Surgical DOM updates |
| **Complex UIs** | Many round-trips | Local updates, fewer requests |

### PyNext vs Streamlit

| Aspect | Streamlit | PyNext |
|--------|-----------|--------|
| **Target** | Data apps, notebooks | Production web apps |
| **Routing** | Single page | File-based, multi-page |
| **Customization** | Limited widgets | Full HTML/CSS control |
| **Deployment** | Streamlit Cloud | Any ASGI server |
| **Performance** | Re-runs entire script | Fine-grained updates |

---

## 📚 Documentation

**[📖 Full Documentation Index →](docs/README.md)**

### Quick Links

| Getting Started | Building Apps | Going to Production |
|-----------------|---------------|---------------------|
| [Getting Started](docs/getting-started/GETTING_STARTED.md) | [Server Actions](docs/data-server/SERVER_ACTIONS.md) | [Deployment](docs/production/DEPLOYMENT.md) |
| [Routing](docs/routing/ROUTING.md) | [State Management](docs/core-concepts/STATE_MANAGEMENT.md) | [Testing](docs/production/TESTING.md) |
| [HTML API](docs/core-concepts/HTML_API.md) | [State Patterns](docs/data-server/STATE_PATTERNS.md) | [Configuration](docs/getting-started/CONFIGURATION.md) |
| [Layouts](docs/routing/LAYOUTS.md) | [API Routes](docs/data-server/API_ROUTES.md) | [CLI Reference](docs/getting-started/CLI.md) |

### Learning Paths

| Goal | Path |
|------|------|
| **🟢 New to PyNext** | [Getting Started](docs/getting-started/GETTING_STARTED.md) → [HTML API](docs/core-concepts/HTML_API.md) → [Routing](docs/routing/ROUTING.md) → [State](docs/core-concepts/STATE_MANAGEMENT.md) |
| **🟡 Building Apps** | [Server Actions](docs/data-server/SERVER_ACTIONS.md) → [State Patterns](docs/data-server/STATE_PATTERNS.md) → [Streaming](docs/rendering/STREAMING_SUSPENSE.md) |
| **🔴 Performance** | [Islands](docs/rendering/ISLANDS.md) → [ISR](docs/rendering/ISR.md) → [Image Optimization](docs/optimization/IMAGE_OPTIMIZATION.md) |
| **📝 Content Sites** | [Static Generation](docs/rendering/STATIC_GENERATION.md) → [ISR](docs/rendering/ISR.md) → [Draft Mode](docs/advanced/DRAFT_MODE.md) |

### All 32 Guides

<details>
<summary><strong>🚀 Getting Started</strong> (3 guides)</summary>

| Guide | Description |
|-------|-------------|
| [Getting Started](docs/getting-started/GETTING_STARTED.md) | Installation, project setup, first app |
| [CLI Reference](docs/getting-started/CLI.md) | `pynext dev`, `build`, `init` commands |
| [Configuration](docs/getting-started/CONFIGURATION.md) | `pynext.config.py` options |

</details>

<details>
<summary><strong>🧱 Core Concepts</strong> (3 guides)</summary>

| Guide | Description |
|-------|-------------|
| [HTML API](docs/core-concepts/HTML_API.md) | Building UI with `div`, `span`, `button`, etc. |
| [State Management](docs/core-concepts/STATE_MANAGEMENT.md) | Signals, Stores, Computed, Effects |
| [Hydration](docs/core-concepts/HYDRATION.md) | How server HTML becomes interactive |

</details>

<details>
<summary><strong>🛤️ Routing & Navigation</strong> (5 guides)</summary>

| Guide | Description |
|-------|-------------|
| [Routing](docs/routing/ROUTING.md) | File-based routing, dynamic routes, catch-all |
| [Layouts](docs/routing/LAYOUTS.md) | Shared UI wrappers, nesting |
| [Transitions](docs/routing/TRANSITIONS.md) | Page transitions, View Transitions API |
| [Parallel Routes](docs/routing/PARALLEL_ROUTES.md) | Multiple pages in one layout (slots) |
| [Intercepting Routes](docs/routing/INTERCEPTING_ROUTES.md) | Modal patterns, route interception |

</details>

<details>
<summary><strong>📊 Data & Server</strong> (4 guides)</summary>

| Guide | Description |
|-------|-------------|
| [Server Actions](docs/data-server/SERVER_ACTIONS.md) | Call Python from browser events |
| [API Routes](docs/data-server/API_ROUTES.md) | REST endpoints alongside pages |
| [State Patterns](docs/data-server/STATE_PATTERNS.md) | Forms, async state, optimistic updates |
| [State & Data Integration](docs/data-server/STATE_DATA_INTEGRATION.md) | Full data flow patterns |

</details>

<details>
<summary><strong>⚡ Rendering Strategies</strong> (5 guides)</summary>

| Guide | Description |
|-------|-------------|
| [Streaming & Suspense](docs/rendering/STREAMING_SUSPENSE.md) | Progressive rendering, loading states |
| [Islands Architecture](docs/rendering/ISLANDS.md) | Selective hydration, minimal JS |
| [Static Generation](docs/rendering/STATIC_GENERATION.md) | Build-time rendering, zero JS |
| [ISR](docs/rendering/ISR.md) | Incremental Static Regeneration |
| [Partial Prerendering](docs/rendering/PARTIAL_PRERENDERING.md) | Static shell + dynamic content |

</details>

<details>
<summary><strong>🔧 Advanced Features</strong> (3 guides)</summary>

| Guide | Description |
|-------|-------------|
| [Middleware](docs/advanced/MIDDLEWARE.md) | Request interception, auth, redirects |
| [Draft Mode](docs/advanced/DRAFT_MODE.md) | CMS preview, unpublished content |
| [Internationalization](docs/advanced/I18N.md) | Multi-language support |

</details>

<details>
<summary><strong>📦 Optimization</strong> (4 guides)</summary>

| Guide | Description |
|-------|-------------|
| [Image Optimization](docs/optimization/IMAGE_OPTIMIZATION.md) | AVIF/WebP, lazy loading, BlurHash |
| [Font Optimization](docs/optimization/FONT_OPTIMIZATION.md) | Zero layout shift, subsetting |
| [Script Optimization](docs/optimization/SCRIPT_OPTIMIZATION.md) | Third-party scripts, loading strategies |
| [Code Splitting](docs/optimization/CODE_SPLITTING.md) | Bundle optimization, lazy loading |

</details>

<details>
<summary><strong>🔌 Integrations</strong> (2 guides)</summary>

| Guide | Description |
|-------|-------------|
| [NPM Packages](docs/integrations/NPM_PACKAGES.md) | Using npm packages in PyNext |
| [React Integration](docs/integrations/REACT_INTEGRATION.md) | Using React components via Preact |

</details>

<details>
<summary><strong>🚢 Production</strong> (2 guides)</summary>

| Guide | Description |
|-------|-------------|
| [Deployment](docs/production/DEPLOYMENT.md) | Docker, cloud platforms, production setup |
| [Testing](docs/production/TESTING.md) | Unit tests, integration, E2E with Playwright |

</details>

<details>
<summary><strong>📋 Reference</strong> (1 guide)</summary>

| Guide | Description |
|-------|-------------|
| [Phase 2 Features](docs/reference/PHASE2_FEATURES.md) | Roadmap and upcoming features |

</details>

### Documentation Structure

```
docs/
├── README.md                    ← Full index with search
│
├── getting-started/             🚀 Start here
│   ├── GETTING_STARTED.md
│   ├── CLI.md
│   └── CONFIGURATION.md
│
├── core-concepts/               🧱 Fundamentals
│   ├── HTML_API.md
│   ├── STATE_MANAGEMENT.md
│   └── HYDRATION.md
│
├── routing/                     🛤️ Navigation
│   ├── ROUTING.md
│   ├── LAYOUTS.md
│   ├── TRANSITIONS.md
│   ├── PARALLEL_ROUTES.md
│   └── INTERCEPTING_ROUTES.md
│
├── data-server/                 📊 Data & Forms
│   ├── SERVER_ACTIONS.md
│   ├── API_ROUTES.md
│   ├── STATE_PATTERNS.md
│   └── STATE_DATA_INTEGRATION.md
│
├── rendering/                   ⚡ Rendering
│   ├── STREAMING_SUSPENSE.md
│   ├── ISLANDS.md
│   ├── STATIC_GENERATION.md
│   ├── ISR.md
│   └── PARTIAL_PRERENDERING.md
│
├── advanced/                    🔧 Power Features
│   ├── MIDDLEWARE.md
│   ├── DRAFT_MODE.md
│   └── I18N.md
│
├── optimization/                📦 Performance
│   ├── IMAGE_OPTIMIZATION.md
│   ├── FONT_OPTIMIZATION.md
│   ├── SCRIPT_OPTIMIZATION.md
│   └── CODE_SPLITTING.md
│
├── integrations/                🔌 External Tools
│   ├── NPM_PACKAGES.md
│   └── REACT_INTEGRATION.md
│
├── production/                  🚢 Deployment
│   ├── DEPLOYMENT.md
│   └── TESTING.md
│
└── reference/                   📋 Reference
    └── PHASE2_FEATURES.md
```

---

## Quick Examples

### Counter

```python
from pynext import page, Signal, div, button

@page
def counter():
    count = Signal(0)
    
    return div()[
        button(onclick=lambda: count.set(count() - 1))["-"],
        span()[count],
        button(onclick=lambda: count.set(count() + 1))["+"],
    ]
```

### Todo List

```python
from pynext import page, Signal, Store, div, input_, button, ul, li, For

@page
def todos():
    todos = Store([])
    new_todo = Signal("")
    
    def add_todo():
        if new_todo():
            todos.append({"text": new_todo(), "done": False})
            new_todo.set("")
    
    return div()[
        input_(value=new_todo, oninput=lambda e: new_todo.set(e.target.value)),
        button(onclick=add_todo)["Add"],
        ul()[
            For(each=todos, render=lambda todo, i: 
                li()[
                    input_(type="checkbox", checked=todo["done"]),
                    span()[todo["text"]]
                ]
            )
        ]
    ]
```

### Data Dashboard

```python
from pynext import page, server_action, Resource, Suspense, div, table
import pandas as pd

@server_action
async def get_sales_data():
    df = pd.read_csv("sales.csv")
    return df.to_dict(orient="records")

@page
def dashboard():
    sales = Resource(get_sales_data)
    
    return div()[
        h1()["Sales Dashboard"],
        Suspense(fallback=div()["Loading..."])[
            table()[
                For(each=sales, render=lambda row:
                    tr()[
                        td()[row["product"]],
                        td()[f"${row['amount']:,.2f}"]
                    ]
                )
            ]
        ]
    ]
```

---

## Requirements

- **Python 3.10+**
- **Node.js** (optional, for npm packages)

### Dependencies

- `fastapi` — ASGI framework
- `uvicorn` — ASGI server
- `orjson` — Fast JSON
- `pydantic` — Validation

---

## CLI Commands

```bash
pynext init my-app   # Create new project
pynext dev           # Start dev server (hot reload)
pynext build         # Build for production
pynext start         # Start production server
pynext routes        # List all routes
```

---

## Configuration

```python
# pynext.config.py

# NPM packages to bundle
npm_packages = [
    "chart.js",
    "lodash",
]

# Build settings
build = {
    "output": ".pynext/build",
    "minify": True,
}

# React compatibility (use npm React components)
react_compat = True
```

---

## Contributing

Contributions are welcome! See our [Contributing Guide](CONTRIBUTING.md) for details.

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">
  <strong>Built with ❤️ for Python developers who want modern web UIs.</strong>
</p>
