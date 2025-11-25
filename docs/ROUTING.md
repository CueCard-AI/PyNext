# File-Based Routing in PyNext

PyNext uses a file-system based router where the structure of your `pages/` directory automatically becomes your application's routes.

## Table of Contents

- [Overview](#overview)
- [Basic Routes](#basic-routes)
- [Dynamic Routes](#dynamic-routes)
- [Catch-All Routes](#catch-all-routes)
- [Nested Routes](#nested-routes)
- [Route Parameters](#route-parameters)
- [Query Parameters](#query-parameters)
- [Navigation](#navigation)
- [Layouts](#layouts)
- [Route Groups](#route-groups)
- [API Routes](#api-routes)
- [Route Matching](#route-matching)
- [Best Practices](#best-practices)

---

## Overview

### How It Works

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

### Key Concepts

| Concept | Syntax | Example |
|---------|--------|---------|
| Static route | `name.py` | `about.py` → `/about` |
| Index route | `index.py` | `blog/index.py` → `/blog` |
| Dynamic segment | `[param].py` | `[id].py` → `/:id` |
| Catch-all | `[...param].py` | `[...slug].py` → `/*` |
| Nested route | Folders | `users/settings.py` → `/users/settings` |

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

### Route Mapping

```
File Path                    URL Path
─────────────────────────    ─────────────────
pages/index.py               /
pages/about.py               /about
pages/pricing.py             /pricing
pages/blog/index.py          /blog
pages/blog/archive.py        /blog/archive
pages/docs/intro.py          /docs/intro
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

URL examples:
- `/users/123` → `params = {"id": "123"}`
- `/users/alice` → `params = {"id": "alice"}`

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

URL: `/blog/2024/03/hello-world`
```python
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

from pynext import page, get_params

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

Catch-all routes capture all remaining path segments.

### Basic Catch-All

```python
# pages/docs/[...slug].py → /docs/*

from pynext import page, div, h1, get_params

@page(title="Documentation")
def docs():
    params = get_params()
    slug = params.get("slug", [])  # List of segments
    
    # Join path segments
    path = "/".join(slug)
    
    return div()[
        h1()["Documentation"],
        p()[f"Path: {path}"]
    ]
```

URL examples:
- `/docs/intro` → `slug = ["intro"]`
- `/docs/api/v2/users` → `slug = ["api", "v2", "users"]`
- `/docs` → `slug = []` (empty)

### Use Cases

```python
# Markdown documentation viewer
# pages/docs/[...path].py

from pynext import page, server_action, div, get_params
from pathlib import Path

@server_action
async def load_markdown(path: str) -> dict:
    import markdown
    
    file_path = Path("content/docs") / f"{path}.md"
    
    if not file_path.exists():
        return {"error": "Not found", "html": None}
    
    content = file_path.read_text()
    html = markdown.markdown(content)
    
    return {"html": html, "error": None}

@page
def docs_page():
    params = get_params()
    path = "/".join(params.get("path", ["index"]))
    
    # Load and render markdown...
```

---

## Nested Routes

Folders create nested URL paths:

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

### Example Structure

```python
# pages/dashboard/index.py
from pynext import page, div, h1, a

@page(title="Dashboard")
def dashboard():
    return div()[
        h1()["Dashboard"],
        nav()[
            a(href="/dashboard/analytics")["Analytics"],
            a(href="/dashboard/settings")["Settings"],
            a(href="/dashboard/users")["Users"]
        ]
    ]
```

```python
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

Access dynamic route parameters:

```python
from pynext import get_params

@page
def user_page():
    params = get_params()
    
    # Single param
    user_id = params.get("id")
    
    # With default
    tab = params.get("tab", "overview")
    
    # All params
    print(params)  # {"id": "123", "tab": "settings"}
```

### Parameter Types

All parameters are strings. Convert as needed:

```python
from pynext import get_params

@page
def product_page():
    params = get_params()
    
    # Convert to int
    product_id = int(params.get("id", "0"))
    
    # Handle catch-all (list)
    path_segments = params.get("path", [])  # ["a", "b", "c"]
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
    
    search_term = query.get("q", "")      # "python"
    page = int(query.get("page", "1"))    # 2
    sort = query.get("sort", "relevance") # "date"
    
    return div()[
        h1()[f"Search: {search_term}"],
        p()[f"Page {page}, sorted by {sort}"]
    ]
```

### Multiple Values

For repeated query params (e.g., `?tag=python&tag=web`):

```python
from pynext import get_query

@page
def filter_page():
    query = get_query()
    
    # get() returns first value
    first_tag = query.get("tag")  # "python"
    
    # getlist() returns all values
    all_tags = query.getlist("tag")  # ["python", "web"]
```

---

## Navigation

### Link Elements

Use standard `<a>` elements for navigation:

```python
from pynext import a

# Basic link
a(href="/about")["About Us"]

# External link
a(href="https://example.com", target="_blank")["External"]

# With classes
a(href="/", class_="nav-link active")["Home"]
```

### Navigation Component

```python
from pynext import component, nav, a, ul, li

@component
def Navigation():
    links = [
        ("/", "Home"),
        ("/about", "About"),
        ("/blog", "Blog"),
        ("/contact", "Contact"),
    ]
    
    return nav(class_="main-nav")[
        ul()[
            [li()[a(href=href)[text]] for href, text in links]
        ]
    ]
```

### Programmatic Navigation

```python
from pynext import server_action, button

@server_action
async def create_post(data: dict) -> dict:
    post_id = await save_post(data)
    return {"redirect": f"/blog/{post_id}"}

# Client-side redirect after action
button(onclick=lambda: handle_create())["Create Post"]

# In JavaScript (client-side):
# const result = await createPost(data);
# if (result.redirect) window.location.href = result.redirect;
```

---

## Layouts

### Shared Layout Component

Create a layout component for shared UI:

```python
# components/layout.py

from pynext import component, div, header, main, footer, a

@component
def Layout(children, title="PyNext App"):
    return div(class_="layout")[
        header(class_="header")[
            nav()[
                a(href="/")["Home"],
                a(href="/about")["About"],
                a(href="/contact")["Contact"]
            ]
        ],
        
        main(class_="content")[
            children
        ],
        
        footer(class_="footer")[
            "© 2024 PyNext App"
        ]
    ]
```

### Using the Layout

```python
# pages/index.py

from pynext import page, div, h1
from components.layout import Layout

@page(title="Home")
def index():
    return Layout()[
        div()[
            h1()["Welcome Home"],
            p()["This content is wrapped in the layout."]
        ]
    ]
```

### Page-Specific Layouts

```python
# components/dashboard_layout.py

from pynext import component, div, aside, main

@component
def DashboardLayout(children):
    return div(class_="dashboard")[
        aside(class_="sidebar")[
            # Sidebar navigation
        ],
        main(class_="main-content")[
            children
        ]
    ]
```

```python
# pages/dashboard/index.py

from components.dashboard_layout import DashboardLayout

@page(title="Dashboard")
def dashboard():
    return DashboardLayout()[
        h1()["Dashboard"]
    ]
```

---

## Route Groups

Route groups help organize routes without affecting the URL structure.

### Concept (Future Feature)

```
pages/
├── (marketing)/           # Group - doesn't affect URL
│   ├── about.py          # /about
│   ├── pricing.py        # /pricing
│   └── layout.py         # Shared layout for group
│
├── (dashboard)/
│   ├── index.py          # /
│   ├── settings.py       # /settings
│   └── layout.py         # Different layout
```

### Current Workaround

Use a prefix in your module names:

```python
# pages/about.py (marketing section)
# pages/pricing.py (marketing section)
# pages/dashboard.py (app section)

# Import different layouts based on route
from components.marketing_layout import Layout  # For marketing
from components.app_layout import Layout        # For app
```

---

## API Routes

Create API endpoints alongside pages:

### Convention

```
pages/
├── api/
│   ├── users.py          # /api/users
│   ├── posts/
│   │   ├── index.py      # /api/posts
│   │   └── [id].py       # /api/posts/:id
```

### API Route Example

```python
# pages/api/users.py

from pynext import api_route
from pynext.server import JSONResponse

@api_route(methods=["GET", "POST"])
async def users(request):
    if request.method == "GET":
        users = await get_all_users()
        return JSONResponse({"users": users})
    
    elif request.method == "POST":
        data = await request.json()
        user = await create_user(data)
        return JSONResponse({"user": user}, status_code=201)
```

### RESTful API

```python
# pages/api/posts/[id].py

from pynext import api_route, get_params
from pynext.server import JSONResponse

@api_route(methods=["GET", "PUT", "DELETE"])
async def post_handler(request):
    params = get_params()
    post_id = params.get("id")
    
    if request.method == "GET":
        post = await get_post(post_id)
        return JSONResponse({"post": post})
    
    elif request.method == "PUT":
        data = await request.json()
        post = await update_post(post_id, data)
        return JSONResponse({"post": post})
    
    elif request.method == "DELETE":
        await delete_post(post_id)
        return JSONResponse({"deleted": True})
```

---

## Route Matching

### Priority Order

Routes are matched in this order:

1. **Static routes** (`about.py`)
2. **Dynamic routes** (`[id].py`)
3. **Catch-all routes** (`[...slug].py`)

```
pages/
├── blog/
│   ├── featured.py       # /blog/featured (matches first)
│   ├── [slug].py         # /blog/:slug (matches second)
│   └── [...path].py      # /blog/* (matches last)
```

### Matching Examples

| URL | Matched File | Params |
|-----|--------------|--------|
| `/blog/featured` | `blog/featured.py` | `{}` |
| `/blog/hello-world` | `blog/[slug].py` | `{slug: "hello-world"}` |
| `/blog/2024/03/post` | `blog/[...path].py` | `{path: ["2024", "03", "post"]}` |

### Conflict Resolution

```
pages/
├── posts/
│   ├── new.py            # /posts/new (static)
│   └── [id].py           # /posts/:id (dynamic)
```

`/posts/new` → `posts/new.py` (static wins)
`/posts/123` → `posts/[id].py` (dynamic)

---

## Best Practices

### 1. Use Descriptive Names

```python
# Good
pages/users/[userId].py
pages/blog/[postSlug].py

# Avoid
pages/users/[x].py
pages/blog/[p].py
```

### 2. Group Related Routes

```
pages/
├── users/
│   ├── index.py          # List users
│   ├── [id].py           # View user
│   └── [id]/
│       ├── edit.py       # Edit user
│       └── settings.py   # User settings
```

### 3. Use Index Files

```python
# pages/blog/index.py - Clear entry point
# vs
# pages/blog.py - Less clear
```

### 4. Validate Parameters

```python
from pynext import page, get_params, div, h1

@page
def user_page():
    params = get_params()
    user_id = params.get("id")
    
    # Validate
    if not user_id or not user_id.isdigit():
        return div(class_="error")[
            h1()["Invalid User ID"]
        ]
    
    # Continue with valid ID...
```

### 5. Handle 404s

```python
# pages/[...notfound].py

from pynext import page, div, h1, a

@page(title="Page Not Found")
def not_found():
    return div(class_="not-found")[
        h1()["404 - Page Not Found"],
        p()["The page you're looking for doesn't exist."],
        a(href="/")["Go Home"]
    ]
```

---

## API Reference

### Route Functions

```python
from pynext import get_params, get_query

# Get route parameters (from URL path)
params = get_params()  # {"id": "123", "slug": "hello"}

# Get query parameters (from URL query string)
query = get_query()    # {"page": "2", "sort": "date"}
```

### Page Decorator

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

### Router Internals

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

## Next Steps

- [HTML API](HTML_API.md) - All elements and attributes
- [State Management](STATE_MANAGEMENT.md) - Signals and reactivity
- [Server Actions](SERVER_ACTIONS.md) - Server-side Python functions
- [Configuration](CONFIGURATION.md) - Framework configuration

