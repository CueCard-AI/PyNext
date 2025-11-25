# File-Based Routing in PyNext

> **Your file structure IS your URL structure. No configuration, no route definitions—just files.**

PyNext uses a file-system based router where the structure of your `pages/` directory automatically becomes your application's routes. It's intuitive, powerful, and requires zero configuration.

---

## Table of Contents

1. [What is File-Based Routing?](#what-is-file-based-routing)
2. [The Mental Model](#the-mental-model)
3. [Basic Routes](#basic-routes)
4. [Dynamic Routes](#dynamic-routes)
5. [Catch-All Routes](#catch-all-routes)
6. [Nested Routes](#nested-routes)
7. [Route Parameters](#route-parameters)
8. [Query Parameters](#query-parameters)
9. [Navigation](#navigation)
10. [Layouts](#layouts)
11. [Route Groups](#route-groups)
12. [API Routes](#api-routes)
13. [Route Matching](#route-matching)
14. [Advanced Patterns](#advanced-patterns)
15. [Best Practices](#best-practices)
16. [API Reference](#api-reference)

---

## What is File-Based Routing?

### The Elevator Pitch

Instead of defining routes in a configuration file, **your file structure becomes your routes**:

```
pages/                        URL
├── index.py             →    /
├── about.py             →    /about
├── contact.py           →    /contact
├── blog/
│   ├── index.py         →    /blog
│   └── [slug].py        →    /blog/:slug
└── docs/
    └── [...path].py     →    /docs/* (catch-all)
```

### First Principles: Files as Routes

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          THE FILE = ROUTE PRINCIPLE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ANALOGY: Think of your website as a BUILDING                              │
│                                                                              │
│                                                                              │
│   Traditional Routing (Config-Based):                                        │
│   ────────────────────────────────────                                      │
│                                                                              │
│   You need a DIRECTORY at the entrance that maps                            │
│   room names to room numbers:                                               │
│                                                                              │
│   ┌──────────────────────────────────┐                                      │
│   │  BUILDING DIRECTORY              │                                      │
│   │  ─────────────────              │                                      │
│   │  "/about"    → Room 101          │      routes.py:                      │
│   │  "/contact"  → Room 102          │      app.route("/about", about_view) │
│   │  "/blog/:id" → Room 201          │      app.route("/contact", contact)  │
│   │  ...                             │      app.route("/blog/:id", blog)    │
│   └──────────────────────────────────┘                                      │
│                                                                              │
│   Problem: Directory can get out of sync with actual rooms!                 │
│                                                                              │
│                                                                              │
│   File-Based Routing (PyNext):                                              │
│   ─────────────────────────────                                             │
│                                                                              │
│   The rooms ARE their addresses. No directory needed:                       │
│                                                                              │
│   ┌──────────────────────────────────┐                                      │
│   │        BUILDING                   │                                      │
│   │        ────────                   │                                      │
│   │                                   │     pages/                           │
│   │   📁 /about     (about.py)       │     ├── about.py                    │
│   │   📁 /contact   (contact.py)     │     ├── contact.py                  │
│   │   📁 /blog                       │     └── blog/                        │
│   │       📁 /[id]  ([id].py)        │         └── [id].py                 │
│   │                                   │                                      │
│   └──────────────────────────────────┘                                      │
│                                                                              │
│   Benefit: File = Route. Always in sync. Zero configuration!               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Concepts at a Glance

| Concept | Syntax | Example | URL |
|---------|--------|---------|-----|
| Static route | `name.py` | `about.py` | `/about` |
| Index route | `index.py` | `blog/index.py` | `/blog` |
| Dynamic segment | `[param].py` | `[id].py` | `/users/123` |
| Catch-all | `[...param].py` | `[...slug].py` | `/docs/a/b/c` |
| Nested route | Folders | `users/settings.py` | `/users/settings` |
| API route | `route.py` | `api/users/route.py` | `/api/users` |

---

## The Mental Model

### How Routes Are Matched

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ROUTE MATCHING FLOW                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   Request: GET /blog/hello-world                                            │
│        │                                                                     │
│        ▼                                                                     │
│   ┌────────────────────────────────────────────────────────────────────┐    │
│   │  1. FILE ROUTER scans pages/ directory                             │    │
│   └────────────────────────────────────────────────────────────────────┘    │
│        │                                                                     │
│        ▼                                                                     │
│   ┌────────────────────────────────────────────────────────────────────┐    │
│   │  2. BUILD ROUTE TRIE (at startup)                                  │    │
│   │                                                                     │    │
│   │     pages/                         Trie Structure:                  │    │
│   │     ├── index.py                                                    │    │
│   │     ├── about.py                   (root)                           │    │
│   │     └── blog/                       ├── "" → index.py               │    │
│   │         ├── index.py                ├── "about" → about.py          │    │
│   │         └── [slug].py               └── "blog"                      │    │
│   │                                          ├── "" → blog/index.py     │    │
│   │                                          └── [slug] → blog/[slug].py│    │
│   └────────────────────────────────────────────────────────────────────┘    │
│        │                                                                     │
│        ▼                                                                     │
│   ┌────────────────────────────────────────────────────────────────────┐    │
│   │  3. MATCH URL PATH                                                 │    │
│   │                                                                     │    │
│   │     /blog/hello-world                                              │    │
│   │        │      │                                                     │    │
│   │        │      └── "hello-world" matches [slug]                     │    │
│   │        │          └── params = {"slug": "hello-world"}             │    │
│   │        │                                                           │    │
│   │        └── "blog" matches static segment                           │    │
│   │                                                                     │    │
│   │     Result: blog/[slug].py with params = {"slug": "hello-world"}   │    │
│   │                                                                     │    │
│   └────────────────────────────────────────────────────────────────────┘    │
│        │                                                                     │
│        ▼                                                                     │
│   ┌────────────────────────────────────────────────────────────────────┐    │
│   │  4. EXECUTE PAGE FUNCTION                                          │    │
│   │                                                                     │    │
│   │     from pages.blog.[slug] import page_function                    │    │
│   │     html = page_function()  # params available via get_params()    │    │
│   │                                                                     │    │
│   └────────────────────────────────────────────────────────────────────┘    │
│        │                                                                     │
│        ▼                                                                     │
│   RESPONSE: Rendered HTML                                                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### The Trie Advantage

PyNext uses a **trie (prefix tree)** for O(path_segments) route matching—typically 2-4 lookups instead of checking every route:

```
Traditional (Linear Search):
─────────────────────────────
Check /about? No.
Check /contact? No.
Check /blog? No.
Check /blog/:slug? Yes!
→ O(n) where n = number of routes

PyNext (Trie Lookup):
─────────────────────
Look up "blog" → found node
Look up "hello-world" → matches [slug]
→ O(depth) where depth ≈ 2-4
```

---

## Basic Routes

### Index Routes

The `index.py` file becomes the index for that directory:

```python
# pages/index.py → /
from pynext import page, div, h1

@page(title="Home")
def index():
    return div()[
        h1()["Welcome Home"]
    ]
```

```python
# pages/blog/index.py → /blog
from pynext import page, div, h1

@page(title="Blog")
def blog_index():
    return div()[
        h1()["Blog Posts"]
    ]
```

### Named Routes

Any `.py` file (except `index.py`) becomes a named route:

```python
# pages/about.py → /about
from pynext import page, div, h1, p

@page(title="About Us")
def about():
    return div()[
        h1()["About Us"],
        p()["Learn more about our company."]
    ]
```

```python
# pages/contact.py → /contact
from pynext import page, div, h1

@page(title="Contact")
def contact():
    return div()[
        h1()["Contact Us"]
    ]
```

### Complete Mapping

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          FILE → URL MAPPING                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   FILE PATH                              URL PATH                           │
│   ─────────                              ────────                           │
│                                                                              │
│   pages/index.py                    →    /                                  │
│   pages/about.py                    →    /about                             │
│   pages/pricing.py                  →    /pricing                           │
│   pages/blog/index.py               →    /blog                              │
│   pages/blog/archive.py             →    /blog/archive                      │
│   pages/docs/intro.py               →    /docs/intro                        │
│   pages/docs/api/overview.py        →    /docs/api/overview                 │
│                                                                              │
│   RULE: File path minus "pages/" and ".py" = URL path                       │
│         index.py files become the directory's root                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Dynamic Routes

Dynamic routes use square brackets to capture URL segments.

### Single Dynamic Segment

```python
# pages/users/[id].py → /users/:id

from pynext import page, div, h1, p, get_params

@page(title="User Profile")
def user_profile():
    params = get_params()
    user_id = params.get("id")
    
    return div()[
        h1()["User Profile"],
        p()[f"User ID: {user_id}"]
    ]
```

**How it works:**

```
URL: /users/123
     └─────┬────┘
           │
           ▼
pages/users/[id].py
            └─┬─┘
              │
              ▼
         params = {"id": "123"}
```

URL examples:
- `/users/123` → `params = {"id": "123"}`
- `/users/alice` → `params = {"id": "alice"}`
- `/users/abc-def` → `params = {"id": "abc-def"}`

### Multiple Dynamic Segments

```python
# pages/blog/[year]/[month]/[slug].py → /blog/:year/:month/:slug

from pynext import page, div, h1, get_params

@page(title="Blog Post")
def blog_post():
    params = get_params()
    
    year = params.get("year")
    month = params.get("month")
    slug = params.get("slug")
    
    return div()[
        h1()[f"Post: {slug}"],
        p()[f"Published: {month}/{year}"]
    ]
```

```
URL: /blog/2024/03/hello-world
     └───────────────────────┘
                │
                ▼
    params = {
        "year": "2024",
        "month": "03",
        "slug": "hello-world"
    }
```

### Dynamic Folder Names

You can also use dynamic segments in folder names:

```
pages/
└── [category]/
    ├── index.py        # /:category
    └── [product].py    # /:category/:product
```

```python
# pages/[category]/[product].py

from pynext import page, get_params, div, h1, p

@page
def product_page():
    params = get_params()
    category = params.get("category")
    product = params.get("product")
    
    return div()[
        h1()[f"{product}"],
        p()[f"Category: {category}"]
    ]
```

URL: `/electronics/laptop` → `{"category": "electronics", "product": "laptop"}`

---

## Catch-All Routes

Catch-all routes capture **all remaining path segments** as a list.

### Basic Catch-All

```python
# pages/docs/[...slug].py → /docs/*

from pynext import page, div, h1, get_params

@page(title="Documentation")
def docs():
    params = get_params()
    slug = params.get("slug", [])  # ← LIST of segments, not string!
    
    # Join path segments
    path = "/".join(slug)
    
    return div()[
        h1()["Documentation"],
        p()[f"Path: {path}"]
    ]
```

**How it works:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CATCH-ALL ROUTES                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   FILE: pages/docs/[...slug].py                                             │
│                                                                              │
│   URL                           │  slug parameter                           │
│   ───                           │  ──────────────                           │
│                                 │                                           │
│   /docs                         │  []                                       │
│   /docs/intro                   │  ["intro"]                                │
│   /docs/api/v2                  │  ["api", "v2"]                           │
│   /docs/api/v2/users            │  ["api", "v2", "users"]                  │
│   /docs/a/b/c/d/e/f             │  ["a", "b", "c", "d", "e", "f"]          │
│                                 │                                           │
│   KEY: slug is ALWAYS a list!                                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Real-World Use Case: Documentation Site

```python
# pages/docs/[...path].py

from pynext import page, server_action, div, get_params
from pathlib import Path

@server_action
async def load_markdown(path: str) -> dict:
    """Load markdown documentation file."""
    import markdown
    
    file_path = Path("content/docs") / f"{path}.md"
    
    if not file_path.exists():
        return {"error": "Not found", "html": None}
    
    content = file_path.read_text()
    html = markdown.markdown(content, extensions=['fenced_code', 'tables'])
    
    return {"html": html, "error": None}

@page
async def docs_page():
    params = get_params()
    path_parts = params.get("path", ["index"])
    path = "/".join(path_parts)
    
    doc = await load_markdown(path)
    
    if doc["error"]:
        return div(class_="error")[
            h1()["404 - Not Found"],
            p()[f"Documentation for '{path}' not found."]
        ]
    
    return div(class_="docs")[
        div(class_="content", dangerouslySetInnerHTML=doc["html"])
    ]
```

---

## Nested Routes

Folders create nested URL paths. This is intuitive and maps directly to your mental model.

### Folder Structure = URL Structure

```
pages/
├── dashboard/
│   ├── index.py          # /dashboard
│   ├── analytics.py      # /dashboard/analytics
│   ├── settings/
│   │   ├── index.py      # /dashboard/settings
│   │   ├── profile.py    # /dashboard/settings/profile
│   │   └── security.py   # /dashboard/settings/security
│   └── users/
│       ├── index.py      # /dashboard/users
│       └── [id].py       # /dashboard/users/:id
```

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          NESTED ROUTES VISUALIZATION                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   /dashboard                                                                │
│   ├── /dashboard/analytics                                                  │
│   ├── /dashboard/settings                                                   │
│   │   ├── /dashboard/settings/profile                                       │
│   │   └── /dashboard/settings/security                                      │
│   └── /dashboard/users                                                      │
│       └── /dashboard/users/123                                              │
│                                                                              │
│   Each level can have:                                                      │
│   • index.py (the landing page for that path)                               │
│   • Named files (specific pages)                                            │
│   • [param].py (dynamic segments)                                           │
│   • More nested folders                                                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Example Implementation

```python
# pages/dashboard/index.py
from pynext import page, div, h1, a, nav

@page(title="Dashboard")
def dashboard():
    return div()[
        h1()["Dashboard"],
        nav()[
            a(href="/dashboard/analytics")["📊 Analytics"],
            a(href="/dashboard/settings")["⚙️ Settings"],
            a(href="/dashboard/users")["👥 Users"],
        ]
    ]

# pages/dashboard/settings/profile.py
from pynext import page, div, h1

@page(title="Profile Settings")
def profile_settings():
    return div()[
        h1()["Profile Settings"],
        # Profile form...
    ]
```

---

## Route Parameters

### get_params()

Access dynamic route parameters from any page:

```python
from pynext import get_params

@page
def user_page():
    params = get_params()
    
    # Single param
    user_id = params.get("id")
    
    # With default value
    tab = params.get("tab", "overview")
    
    # All params (useful for debugging)
    print(params)  # {"id": "123", "tab": "settings"}
    
    return div()[f"User {user_id}"]
```

### Parameter Types

All parameters are **strings**. Convert as needed:

```python
from pynext import get_params

@page
def product_page():
    params = get_params()
    
    # Convert to int
    product_id = int(params.get("id", "0"))
    
    # Convert to bool (careful with string "false"!)
    show_details = params.get("details", "true").lower() == "true"
    
    # Handle catch-all (always a list)
    path_segments = params.get("path", [])  # ["a", "b", "c"]
    
    return div()[f"Product {product_id}"]
```

### Type Validation Pattern

```python
from pynext import page, get_params, div, h1

@page
def user_page():
    params = get_params()
    user_id = params.get("id")
    
    # Validate it's a positive integer
    try:
        user_id = int(user_id)
        if user_id <= 0:
            raise ValueError()
    except (TypeError, ValueError):
        return div(class_="error")[
            h1()["Invalid User ID"],
            p()[f"'{params.get('id')}' is not a valid user ID"]
        ]
    
    # user_id is now a validated integer
    user = fetch_user(user_id)
    ...
```

---

## Query Parameters

### get_query()

Access URL query string parameters:

```python
from pynext import get_query

# URL: /search?q=python&page=2&sort=date

@page
def search_page():
    query = get_query()
    
    search_term = query.get("q", "")           # "python"
    page = int(query.get("page", "1"))         # 2
    sort = query.get("sort", "relevance")      # "date"
    
    return div()[
        h1()[f"Search: {search_term}"],
        p()[f"Page {page}, sorted by {sort}"]
    ]
```

### Multiple Values

For repeated query params (e.g., `?tag=python&tag=web&tag=api`):

```python
from pynext import get_query

@page
def filter_page():
    query = get_query()
    
    # get() returns first value only
    first_tag = query.get("tag")  # "python"
    
    # getlist() returns ALL values
    all_tags = query.getlist("tag")  # ["python", "web", "api"]
    
    return div()[
        p()[f"First tag: {first_tag}"],
        p()[f"All tags: {', '.join(all_tags)}"]
    ]
```

### Query vs Route Parameters

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      QUERY vs ROUTE PARAMETERS                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   URL: /products/123?color=blue&size=large                                  │
│        └────┬─────┘ └──────────┬──────────┘                                │
│             │                  │                                            │
│             │                  │                                            │
│             ▼                  ▼                                            │
│   ROUTE PARAMETERS       QUERY PARAMETERS                                   │
│   (from path)            (from query string)                                │
│                                                                             │
│   get_params()           get_query()                                        │
│   {"id": "123"}          {"color": "blue", "size": "large"}                │
│                                                                              │
│                                                                              │
│   WHEN TO USE WHICH:                                                        │
│   ──────────────────                                                        │
│                                                                              │
│   Route params:          Query params:                                      │
│   • Resource identity    • Filtering/sorting                                │
│   • Required values      • Optional values                                  │
│   • SEO-important        • Not SEO-critical                                 │
│                                                                              │
│   Examples:                                                                 │
│   /users/123             /users?role=admin&sort=name                        │
│   /blog/hello-world      /blog?page=2&limit=10                             │
│   /products/shoes        /products?color=blue&min_price=50                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Navigation

### Link Elements

Use standard `<a>` elements for navigation:

```python
from pynext import a

# Basic link
a(href="/about")["About Us"]

# External link (opens in new tab)
a(href="https://github.com", target="_blank", rel="noopener")["GitHub"]

# With classes
a(href="/", class_="nav-link active")["Home"]

# With dynamic href
a(href=f"/users/{user_id}")["View Profile"]
```

### Navigation Component

```python
from pynext import component, nav, a, ul, li

@component
def Navigation():
    links = [
        ("/", "Home", "🏠"),
        ("/about", "About", "ℹ️"),
        ("/blog", "Blog", "📝"),
        ("/contact", "Contact", "📧"),
    ]
    
    return nav(class_="main-nav")[
        ul()[
            [
                li()[
                    a(href=href)[f"{icon} {text}"]
                ]
                for href, text, icon in links
            ]
        ]
    ]
```

### Programmatic Navigation

For navigation after actions (like form submissions):

```python
from pynext import server_action

@server_action
async def create_post(data: dict) -> dict:
    post = await save_post(data)
    return {
        "success": True,
        "redirect": f"/blog/{post.slug}"  # Frontend handles redirect
    }

# In the client, handle the redirect:
# const result = await createPost(data);
# if (result.redirect) window.location.href = result.redirect;
```

### Active Link Styling

```python
from pynext import component, get_current_path, a

@component
def NavLink(href: str, children):
    current_path = get_current_path()
    is_active = current_path == href
    
    return a(
        href=href,
        class_=f"nav-link {'active' if is_active else ''}"
    )[children]
```

---

## Layouts

Layouts wrap pages with shared UI. See [LAYOUTS.md](LAYOUTS.md) for full documentation.

### Quick Overview

```python
# pages/layout.py - Root layout (wraps ALL pages)
from pynext import layout, div, nav, main, footer, a

@layout
def root_layout(children):
    return div(class_="app")[
        nav()[
            a(href="/")["Home"],
            a(href="/about")["About"],
        ],
        main()[children],
        footer()["© 2024 My App"],
    ]
```

### Layout Nesting

```
pages/
├── layout.py              # Root layout
└── dashboard/
    ├── layout.py          # Dashboard layout (nested)
    └── settings.py        # Settings page

Request: /dashboard/settings

Result:
┌─────────────────────────────────────────────────────────────────┐
│  Root Layout (header, nav)                                       │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Dashboard Layout (sidebar)                                │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  Settings Page (content)                             │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Route Groups

Route groups help organize routes without affecting the URL structure.

### The Concept (Future Feature)

```
pages/
├── (marketing)/           # Group - parentheses mean "don't include in URL"
│   ├── about.py          # → /about (not /marketing/about)
│   ├── pricing.py        # → /pricing
│   └── layout.py         # Shared layout for marketing pages
│
├── (app)/
│   ├── dashboard.py      # → /dashboard
│   ├── settings.py       # → /settings
│   └── layout.py         # Different layout for app pages
```

### Current Workaround

Until route groups are fully implemented, use layout composition:

```python
# components/layouts.py
from pynext import component

@component
def MarketingLayout(children):
    return div(class_="marketing-layout")[
        MarketingHeader(),
        children,
        MarketingFooter(),
    ]

@component
def AppLayout(children):
    return div(class_="app-layout")[
        AppSidebar(),
        children,
    ]

# pages/about.py
from components.layouts import MarketingLayout

@page
def about():
    return MarketingLayout()[
        h1()["About Us"],
        ...
    ]

# pages/dashboard.py
from components.layouts import AppLayout

@page
def dashboard():
    return AppLayout()[
        h1()["Dashboard"],
        ...
    ]
```

---

## API Routes

Create API endpoints alongside pages using `route.py` files.

### Convention

```
pages/
├── api/
│   ├── users/
│   │   ├── route.py      # GET, POST /api/users
│   │   └── [id]/
│   │       └── route.py  # GET, PUT, DELETE /api/users/:id
│   └── posts/
│       └── route.py      # /api/posts
```

### API Route Example

```python
# pages/api/users/route.py

from pynext import api_route
from pynext.server import JSONResponse

@api_route
async def GET(request):
    """List all users."""
    users = await get_all_users()
    return {"users": users}

@api_route
async def POST(request):
    """Create a new user."""
    data = await request.json()
    user = await create_user(data)
    return JSONResponse({"user": user}, status_code=201)
```

### Dynamic API Routes

```python
# pages/api/users/[id]/route.py

from pynext import api_route, get_params
from pynext.server import JSONResponse

@api_route
async def GET(request):
    """Get user by ID."""
    params = get_params()
    user_id = params.get("id")
    
    user = await get_user(user_id)
    if not user:
        return JSONResponse({"error": "Not found"}, status_code=404)
    
    return {"user": user}

@api_route
async def DELETE(request):
    """Delete user by ID."""
    params = get_params()
    await delete_user(params.get("id"))
    return JSONResponse({"deleted": True}, status_code=204)
```

See [API_ROUTES.md](API_ROUTES.md) for full documentation.

---

## Route Matching

### Priority Order

Routes are matched in this order (most specific first):

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ROUTE MATCHING PRIORITY                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   PRIORITY    ROUTE TYPE         EXAMPLE                                    │
│   ────────    ──────────         ───────                                    │
│                                                                              │
│   1 (first)   Static             /blog/featured                             │
│   2           Dynamic            /blog/[slug]                               │
│   3 (last)    Catch-all          /blog/[...path]                            │
│                                                                              │
│                                                                              │
│   EXAMPLE:                                                                  │
│   ────────                                                                  │
│                                                                              │
│   pages/                                                                     │
│   └── blog/                                                                  │
│       ├── featured.py       # STATIC - matches first                        │
│       ├── [slug].py         # DYNAMIC - matches second                      │
│       └── [...path].py      # CATCH-ALL - matches last                      │
│                                                                              │
│   URL                        MATCHED FILE           PARAMS                  │
│   ───                        ────────────           ──────                  │
│   /blog/featured             blog/featured.py       {}                      │
│   /blog/hello-world          blog/[slug].py         {slug: "hello-world"}   │
│   /blog/2024/03/post         blog/[...path].py      {path: ["2024","03","post"]}
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Conflict Resolution

Static routes always win over dynamic routes:

```
pages/
├── posts/
│   ├── new.py            # /posts/new (STATIC - wins)
│   └── [id].py           # /posts/:id (DYNAMIC)

/posts/new   → posts/new.py    (static wins!)
/posts/123   → posts/[id].py   (dynamic)
```

---

## Advanced Patterns

### Parallel Fetching

Load multiple data sources in parallel:

```python
from pynext import page, get_params
import asyncio

@page
async def user_page():
    params = get_params()
    user_id = params.get("id")
    
    # Fetch in parallel (much faster!)
    user, posts, followers = await asyncio.gather(
        fetch_user(user_id),
        fetch_user_posts(user_id),
        fetch_user_followers(user_id),
    )
    
    return div()[
        UserProfile(user),
        UserPosts(posts),
        UserFollowers(followers),
    ]
```

### Conditional Routes

Show different content based on conditions:

```python
from pynext import page, get_params

@page
async def product_page():
    params = get_params()
    product_id = params.get("id")
    
    product = await fetch_product(product_id)
    
    if not product:
        # 404 Not Found
        return NotFoundPage()
    
    if not product.is_published:
        # Redirect or preview mode
        return UnpublishedPage(product)
    
    return ProductPage(product)
```

### Protected Routes

Combine with middleware for auth:

```python
# middleware.py
from pynext import middleware, NextResponse

@middleware(matcher="/dashboard/*")
async def auth_middleware(ctx):
    if not ctx.get_cookie("auth_token"):
        return NextResponse.redirect("/login")
    return NextResponse.next()

# pages/dashboard/index.py (protected by middleware)
@page
def dashboard():
    return div()[h1()["Dashboard"]]
```

---

## Best Practices

### Do's and Don'ts

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ROUTING BEST PRACTICES                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ✓ DO                                                                      │
│   ────                                                                      │
│                                                                              │
│   ✓ Use descriptive parameter names                                        │
│     pages/users/[userId].py                                                 │
│     pages/blog/[postSlug].py                                                │
│                                                                              │
│   ✓ Group related routes in folders                                        │
│     pages/dashboard/settings/profile.py                                     │
│     pages/dashboard/settings/security.py                                    │
│                                                                              │
│   ✓ Use index.py for landing pages                                         │
│     pages/blog/index.py  (cleaner than pages/blog.py)                       │
│                                                                              │
│   ✓ Validate parameters                                                    │
│     if not user_id.isdigit(): return ErrorPage()                           │
│                                                                              │
│   ✓ Create a 404 page                                                      │
│     pages/not-found.py or pages/[...notfound].py                           │
│                                                                              │
│                                                                              │
│   ✗ DON'T                                                                   │
│   ───────                                                                   │
│                                                                              │
│   ✗ Use single-letter parameter names                                      │
│     pages/[x].py  → pages/[slug].py                                        │
│                                                                              │
│   ✗ Create deeply nested catch-alls                                        │
│     pages/a/b/c/d/[...rest].py  (hard to maintain)                         │
│                                                                              │
│   ✗ Mix naming conventions                                                 │
│     pages/userProfile.py  → pages/user-profile.py or pages/users/profile.py │
│                                                                              │
│   ✗ Forget to handle missing parameters                                    │
│     Always use .get("param", default) instead of ["param"]                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### URL Design

```python
# ✓ Good URL design
/users/123                    # Resource with ID
/users/123/posts              # Nested resource
/blog/hello-world             # Slug for readability
/products?category=shoes      # Query for filtering

# ✗ Avoid
/getUser?id=123              # Verbs in URLs
/users/123/getAllPosts       # Unnecessary verbosity
/page.php?id=123             # Technology-specific extensions
```

---

## API Reference

### Route Functions

```python
from pynext import get_params, get_query, get_current_path

# Get route parameters (from URL path)
params = get_params()  # {"id": "123", "slug": "hello"}

# Get query parameters (from URL query string)
query = get_query()    # {"page": "2", "sort": "date"}

# Get current path
path = get_current_path()  # "/users/123"
```

### @page Decorator

```python
from pynext import page

@page(
    title="Page Title",           # <title> tag
    description="Page desc",      # meta description
    head=["<link ...>"],          # Additional head elements
)
def my_page():
    return div()[...]
```

### @api_route Decorator

```python
from pynext import api_route

@api_route
async def GET(request):
    """Handle GET requests."""
    return {"data": "..."}

@api_route
async def POST(request):
    """Handle POST requests."""
    data = await request.json()
    return {"created": data}
```

### FileRouter Class

```python
from pynext.router import FileRouter

# Create router
router = FileRouter("pages/")

# Scan for routes
routes = router.scan()

# Match a URL
match = router.match("/users/123")
# RouteMatch(path="/users/123", params={"id": "123"}, handler=...)
```

---

## Related Documentation

- [Layouts](LAYOUTS.md) - Page layouts and nesting
- [API Routes](API_ROUTES.md) - REST API endpoints
- [Middleware](MIDDLEWARE.md) - Route protection
- [Server Actions](SERVER_ACTIONS.md) - Server-side functions

---

## Summary

You've learned:

1. ✅ How file-based routing works
2. ✅ Static, dynamic, and catch-all routes
3. ✅ Accessing route and query parameters
4. ✅ Creating nested routes with folders
5. ✅ Navigation between pages
6. ✅ API routes with route.py
7. ✅ Route matching priority
8. ✅ Best practices for URL design

Your file structure IS your API. Keep it organized! 📁
