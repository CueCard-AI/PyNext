# PyNext Client-Side Router

## Who Is This For?

- **Python web developers** who want SPA navigation without React
- **Teams migrating from Next.js** who want familiar routing patterns
- **AI assistants** helping developers build PyNext applications

## What Is It?

A **SolidJS-style reactive router** for PyNext that enables single-page application (SPA) navigation without page reloads. Routes are reactive—when the URL changes, only the affected components update.

## When To Use It

| Scenario | Use Router? |
|----------|-------------|
| Multi-page SPA | ✅ Yes |
| Blog with articles | ✅ Yes |
| Dashboard with tabs | ✅ Yes |
| Simple landing page | ❌ No |
| Static marketing site | ❌ No |

## Where It Lives

| Component | File | Description |
|-----------|------|-------------|
| Python API | `pynext/reactive/router.py` | Router, Route, Link, hooks |
| JS Runtime | `pynext/runtime/router.js` | Client-side navigation |
| Tests | `tests/unit/router/` | 525+ comprehensive tests |

## Why Use PyNext Router?

### Performance Advantage

```
Next.js Router Flow:
URL Change → React State → Full Tree Reconcile → VDOM Diff → DOM Update
                              (100-500ms)

PyNext Router Flow:
URL Change → Signal Update → Route Outlet Update
                              (5-10ms)
```

| Metric | Next.js | PyNext |
|--------|---------|--------|
| Route change | 50-100ms | < 10ms |
| Param update | Re-render component | Signal update only |
| Memory per route | Component instance | Single outlet element |

### Why Fine-Grained Reactivity Wins

```python
# PyNext: Only useParams() subscribers re-render
@island
def UserProfile():
    params = useParams()  # Subscribes to params signal
    return h1()[f"User {params['id']}"]  # Only this updates

# React: Entire route component re-renders on param change
```

## How It Works

### Basic Routing

```python
from pynext.reactive import Router, Route, Link
from pynext import page

@page
def App():
    return div()[
        # Navigation
        nav()[
            Link(href="/")["Home"],
            Link(href="/about")["About"],
            Link(href="/users")["Users"],
        ],
        
        # Router outlet
        Router()[
            Route(path="/", component=Home),
            Route(path="/about", component=About),
            Route(path="/users", component=UserList),
            Route(path="/users/:id", component=UserDetail),
        ]
    ]
```

### Dynamic Routes with Parameters

```python
from pynext.reactive import useParams
from pynext import island

@island
def UserDetail():
    params = useParams()  # {"id": "123"}
    user_id = params["id"]
    
    return article()[
        h1()[f"User #{user_id}"],
        # Fetch and display user data...
    ]
```

### Programmatic Navigation

```python
from pynext.reactive import useNavigate

@island
def LoginForm():
    navigate = useNavigate()
    
    def handle_login():
        # After successful login...
        navigate("/dashboard")
    
    def handle_cancel():
        navigate(-1)  # Go back
    
    return form(onsubmit=handle_login)[
        # Form fields...
        button(type="submit")["Login"],
        button(type="button", onclick=handle_cancel)["Cancel"],
    ]
```

### Query String Parameters

```python
from pynext.reactive import useSearchParams

@island
def SearchPage():
    params, setParams = useSearchParams()
    query = params.get("q", "")
    
    def search(new_query):
        setParams({"q": new_query})
    
    return div()[
        input(value=query, oninput=lambda e: search(e.target.value)),
        SearchResults(query=query),
    ]
```

### Active Link Styling

```python
# Link automatically adds "active" class when path matches
Link(href="/about", active_class="is-active")["About"]

# Use exact matching for root path
Link(href="/", exact=True, active_class="current")["Home"]
```

### Prefetching

```python
# Prefetch on hover (loads route content ahead of time)
Link(href="/products", prefetch=True)["Products"]

# Programmatic prefetch
navigate = useNavigate()
navigate.prefetch("/products/123")
```

### Route Guards

```python
from pynext.reactive import createRouteGuard, Redirect

def auth_guard():
    if not is_logged_in():
        return Redirect("/login")
    return None  # Allow access

guard = createRouteGuard(auth_guard)

Route(path="/dashboard", component=Dashboard, guards=[guard])
```

### Nested Routes with Layouts

```python
from pynext.reactive import Outlet

@component
def DashboardLayout():
    return div()[
        Sidebar(),
        main()[
            str(Outlet())  # Child routes render here
        ],
    ]

# Routes
Route(path="/dashboard", component=DashboardLayout),
Route(path="/dashboard/overview", component=Overview),
Route(path="/dashboard/analytics", component=Analytics),
```

## API Reference

### Components

#### `Router`

Container for route definitions.

```python
Router(
    base: str = "",           # Base path prefix
    fallback: Callable = None  # 404 component
)[
    Route(...),
    Route(...),
]
```

#### `Route`

Defines a path-to-component mapping.

```python
Route(
    path: str,                # URL pattern (e.g., "/users/:id")
    component: Callable,      # Component to render
    exact: bool = True,       # Match exactly
    guards: List = None       # Route guards
)
```

#### `Link`

Navigation link (no page reload).

```python
Link(
    href: str,                    # Target path
    replace: bool = False,        # Replace history entry
    prefetch: bool = False,       # Prefetch on hover
    active_class: str = "active", # Class when active
    exact: bool = False           # Exact match for active
)["Link Text"]
```

#### `Outlet`

Placeholder for nested route content.

```python
Outlet()  # Renders child route component
```

### Hooks

#### `useNavigate()`

Get navigation function.

```python
navigate = useNavigate()

navigate("/path")              # Push
navigate("/path", replace=True) # Replace
navigate(-1)                   # Back
navigate.prefetch("/path")     # Prefetch
```

#### `useParams()`

Get route parameters (reactive).

```python
params = useParams()
user_id = params["id"]
```

#### `useSearchParams()`

Get/set query string parameters.

```python
params, setParams = useSearchParams()
query = params.get("q", "")
setParams({"q": "new query"})
```

#### `useLocation()`

Get current location (reactive).

```python
location = useLocation()
# location.pathname = "/users/123"
# location.search = "?tab=posts"
# location.hash = "#section"
```

#### `useMatch(pattern)`

Check if current path matches pattern.

```python
match = useMatch("/users/:id")
if match:
    user_id = match["id"]
```

### Types

#### `Location`

```python
@dataclass
class Location:
    pathname: str    # "/users/123"
    search: str      # "?q=test"
    hash: str        # "#section"
    state: dict      # History state
```

#### `Redirect`

```python
Redirect(
    to: str,           # Target path
    replace: bool = True  # Replace history
)
```

## Path Pattern Syntax

| Pattern | Example Match | Params |
|---------|--------------|--------|
| `/` | `/` | `{}` |
| `/about` | `/about` | `{}` |
| `/users/:id` | `/users/123` | `{"id": "123"}` |
| `/users/:id/posts/:postId` | `/users/1/posts/2` | `{"id": "1", "postId": "2"}` |
| `/files/*` | `/files/path/to/file` | `{"*": "path/to/file"}` |

## SSR + Hydration

### Server-Side

```python
@page
def PageWithRouter():
    # Router renders correct route based on request path
    return Router()[
        Route(path="/", component=Home),
        Route(path="/about", component=About),
    ]
```

### Generated HTML

```html
<div data-pynext-router="true" data-pynext-route-data='{"pathname":"/","params":{}}'>
  <!-- Matched component HTML -->
</div>
```

### Client-Side Hydration

```javascript
// Automatically initialized from signals.js
// Listens for Link clicks and popstate events
// Updates route signals on navigation
```

## Examples

### Linear Clone Navigation

```python
@page
def LinearApp():
    return Router()[
        Route(path="/", component=Dashboard),
        Route(path="/issues", component=IssueList),
        Route(path="/issues/:id", component=IssueDetail),
        Route(path="/projects/:id", component=ProjectBoard),
        Route(path="/settings", component=Settings),
    ]

@island
def IssueDetail():
    params = useParams()
    navigate = useNavigate()
    
    return div()[
        button(onclick=lambda: navigate("/issues"))["← Back"],
        h1()[f"Issue #{params['id']}"],
        # Issue content...
    ]
```

### E-commerce Product Catalog

```python
@page
def Shop():
    return Router()[
        Route(path="/shop", component=ProductList),
        Route(path="/shop/:category", component=CategoryView),
        Route(path="/shop/:category/:product", component=ProductDetail),
        Route(path="/cart", component=Cart),
        Route(path="/checkout", component=Checkout),
    ]

@island
def ProductDetail():
    params = useParams()
    query = useSearchParams()[0]
    
    category = params["category"]
    product = params["product"]
    variant = query.get("variant", "default")
    
    return article()[
        Breadcrumbs(category=category),
        ProductInfo(product=product, variant=variant),
        AddToCartButton(),
    ]
```

### Documentation Site

```python
@page
def Docs():
    return Router()[
        Route(path="/docs", component=DocsHome),
        Route(path="/docs/:section", component=Section),
        Route(path="/docs/:section/:page", component=Page),
    ]

@island  
def DocNav():
    match_section = useMatch("/docs/:section")
    match_page = useMatch("/docs/:section/:page")
    
    current_section = match_section["section"] if match_section else None
    current_page = match_page["page"] if match_page else None
    
    return nav()[
        # Highlight current section/page
        For(sections, lambda sec: 
            NavSection(
                section=sec, 
                is_active=sec["id"] == current_section
            )
        ),
    ]
```

## Performance Benchmarks

| Operation | Time | Notes |
|-----------|------|-------|
| Route compile | < 0.1ms | Regex compilation |
| Route match | < 0.01ms | Per route |
| Navigate | < 5ms | Signal update + fetch |
| 100 routes match | < 1ms | Linear search |

## Testing

```bash
# Run router tests
pytest tests/unit/router/ -v

# Run with coverage
pytest tests/unit/router/ --cov=pynext.reactive.router
```

## Migration from React Router

| React Router | PyNext Router |
|--------------|---------------|
| `<Routes>` | `Router()` |
| `<Route path="/x" element={...}>` | `Route(path="/x", component=...)` |
| `<Link to="/x">` | `Link(href="/x")` |
| `useNavigate()` | `useNavigate()` |
| `useParams()` | `useParams()` |
| `useSearchParams()` | `useSearchParams()` |
| `useLocation()` | `useLocation()` |
| `<Outlet>` | `Outlet()` |

---

## Summary

PyNext Router provides:

- ✅ **Fine-grained reactivity** (no full re-renders)
- ✅ **Simple, familiar API** (React Router-like)
- ✅ **SSR + Hydration** support
- ✅ **< 10ms route changes**
- ✅ **Prefetching** for instant navigation
- ✅ **Route guards** for protected routes
- ✅ **525+ tests** for reliability

