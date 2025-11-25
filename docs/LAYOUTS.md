# Layouts in PyNext

Layouts provide a way to wrap pages with shared UI like navigation, sidebars, and footers. PyNext supports nested layouts that compose from the root to the innermost route.

## Table of Contents

- [Overview](#overview)
- [Creating Layouts](#creating-layouts)
- [Nested Layouts](#nested-layouts)
- [Layout Resolution](#layout-resolution)
- [Special Files](#special-files)
- [Examples](#examples)
- [Best Practices](#best-practices)

---

## Overview

### How Layouts Work

```
pages/
├── layout.py              # Root layout (wraps ALL pages)
├── index.py               # /
├── about.py               # /about
└── dashboard/
    ├── layout.py          # Dashboard layout (wraps dashboard pages)
    ├── index.py           # /dashboard
    └── settings.py        # /dashboard/settings
```

When a user visits `/dashboard/settings`:

```
┌─────────────────────────────────────────────────────────┐
│  Root Layout (pages/layout.py)                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Dashboard Layout (pages/dashboard/layout.py)      │  │
│  │  ┌─────────────────────────────────────────────┐  │  │
│  │  │  Settings Page (pages/dashboard/settings.py) │  │  │
│  │  └─────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Key Concepts

| Concept | Description |
|---------|-------------|
| **Root Layout** | `pages/layout.py` wraps all pages |
| **Nested Layout** | `pages/folder/layout.py` wraps pages in that folder |
| **Children** | The `children` parameter contains wrapped content |
| **Composition** | Layouts nest from root to innermost |

---

## Creating Layouts

### Basic Layout

```python
# pages/layout.py

from pynext import layout, div, nav, main, footer, a, h1

@layout
def root_layout(children):
    """Root layout wrapping all pages."""
    return div(class_="app")[
        # Header
        nav(class_="navbar")[
            h1()["My App"],
            div()[
                a(href="/")["Home"],
                a(href="/about")["About"],
                a(href="/contact")["Contact"]
            ]
        ],
        
        # Main content (children = page content)
        main(class_="content")[
            children
        ],
        
        # Footer
        footer()[
            "© 2024 My App"
        ]
    ]
```

### The Children Parameter

The `children` parameter is **required** and contains the wrapped content:

```python
@layout
def my_layout(children):  # ← Required parameter
    return div()[
        children  # ← Insert child content here
    ]
```

For the root layout:
- `children` = the page component output

For nested layouts:
- `children` = the next nested layout (or page if innermost)

---

## Nested Layouts

### Dashboard Example

```python
# pages/dashboard/layout.py

from pynext import layout, div, aside, nav, a

@layout
def dashboard_layout(children):
    """Dashboard layout with sidebar."""
    return div(class_="dashboard")[
        # Sidebar navigation
        aside(class_="sidebar")[
            nav()[
                a(href="/dashboard")["Overview"],
                a(href="/dashboard/analytics")["Analytics"],
                a(href="/dashboard/settings")["Settings"],
            ]
        ],
        
        # Dashboard content area
        div(class_="dashboard-main")[
            children  # ← Page or nested layout goes here
        ]
    ]
```

### Layout Nesting Order

Layouts are applied from **root to innermost**:

```python
# Request: /dashboard/settings

# 1. Root layout wraps everything
root_layout(
    # 2. Dashboard layout wraps the page
    dashboard_layout(
        # 3. Settings page is the innermost content
        settings_page()
    )
)
```

---

## Layout Resolution

### How Layouts Are Found

For a page at `pages/a/b/c/page.py`, PyNext looks for layouts at:

1. `pages/layout.py` (root)
2. `pages/a/layout.py`
3. `pages/a/b/layout.py`
4. `pages/a/b/c/layout.py`

All found layouts are nested in order.

### Example Resolution

```
Request: /dashboard/settings

pages/
├── layout.py              # ✓ Applied (1st - outermost)
├── dashboard/
│   ├── layout.py          # ✓ Applied (2nd)
│   └── settings.py        # The page itself

Result:
  root_layout(
    dashboard_layout(
      settings_page()
    )
  )
```

### No Layout Needed

If you don't want a layout for a section, simply don't create a `layout.py` file.

```
pages/
├── layout.py              # Root layout (applies to all)
├── public/
│   └── terms.py           # No layout.py here = only root layout
└── dashboard/
    ├── layout.py          # Dashboard layout
    └── index.py
```

---

## Special Files

PyNext recognizes special files alongside `layout.py`:

| File | Purpose |
|------|---------|
| `layout.py` | Wraps child routes |
| `loading.py` | Loading UI for route |
| `error.py` | Error boundary for route |
| `not-found.py` | 404 page (root only) |

### Loading Component

```python
# pages/dashboard/loading.py

from pynext import loading, div

@loading
def dashboard_loading():
    """Shown while dashboard content loads."""
    return div(class_="loading")[
        div(class_="spinner"),
        "Loading dashboard..."
    ]
```

### Error Boundary

```python
# pages/dashboard/error.py

from pynext import error, div, h1, p, button

@error
def dashboard_error(error, reset):
    """Shown when an error occurs in dashboard."""
    return div(class_="error")[
        h1()["Dashboard Error"],
        p()[str(error)],
        button(onclick=reset)["Retry"]
    ]
```

### Not Found Page

```python
# pages/not-found.py

from pynext import not_found, div, h1, a

@not_found
def custom_404():
    """Custom 404 page."""
    return div(class_="not-found")[
        h1()["404 - Page Not Found"],
        a(href="/")["Go Home"]
    ]
```

---

## Examples

### Complete App Structure

```
pages/
├── layout.py              # App shell
├── loading.py             # Global loading
├── error.py               # Global error
├── not-found.py           # 404 page
├── index.py               # /
├── about.py               # /about
├── auth/
│   ├── login.py           # /auth/login
│   └── register.py        # /auth/register
└── dashboard/
    ├── layout.py          # Dashboard shell
    ├── loading.py         # Dashboard loading
    ├── error.py           # Dashboard error
    ├── index.py           # /dashboard
    ├── analytics.py       # /dashboard/analytics
    └── settings/
        ├── layout.py      # Settings shell
        ├── index.py       # /dashboard/settings
        └── profile.py     # /dashboard/settings/profile
```

### Root Layout with Theme

```python
# pages/layout.py

from pynext import layout, html, head, body, title, meta, link, script, div

@layout
def root_layout(children):
    return html(lang="en")[
        head()[
            meta(charset="utf-8"),
            meta(name="viewport", content="width=device-width, initial-scale=1"),
            title()["My App"],
            link(rel="stylesheet", href="/static/styles.css"),
        ],
        body()[
            div(id="app")[
                children
            ],
            script(src="/static/app.js", defer=True)
        ]
    ]
```

### Dashboard with Stats Header

```python
# pages/dashboard/layout.py

from pynext import layout, div, aside, header, nav, a, span

@layout
def dashboard_layout(children):
    return div(class_="dashboard")[
        # Top stats bar
        header(class_="dashboard-header")[
            span()["Users: 1,234"],
            span()["Revenue: $12.3k"],
            span()["Active: 456"]
        ],
        
        # Main area with sidebar
        div(class_="dashboard-body")[
            aside(class_="sidebar")[
                nav()[
                    a(href="/dashboard")["📊 Overview"],
                    a(href="/dashboard/analytics")["📈 Analytics"],
                    a(href="/dashboard/settings")["⚙️ Settings"],
                ]
            ],
            div(class_="main")[
                children
            ]
        ]
    ]
```

---

## Best Practices

### 1. Keep Layouts Focused

```python
# Good: Focused layout
@layout
def dashboard_layout(children):
    return div(class_="dashboard")[
        Sidebar(),  # Extracted component
        div()[children]
    ]

# Avoid: Too much logic in layout
@layout
def dashboard_layout(children):
    # Complex data fetching, state, etc.
    pass
```

### 2. Extract Reusable Components

```python
# components/nav.py
@component
def MainNav():
    return nav()[...]

# pages/layout.py
@layout
def root_layout(children):
    return div()[
        MainNav(),  # Reused component
        main()[children],
        Footer()
    ]
```

### 3. Use Semantic HTML

```python
# Good: Semantic structure
@layout
def layout(children):
    return div()[
        header()[...],
        nav()[...],
        main()[children],
        aside()[...],
        footer()[...]
    ]
```

### 4. Handle Loading States

```python
# pages/dashboard/loading.py
@loading
def dashboard_loading():
    return div(class_="skeleton")[
        div(class_="skeleton-header"),
        div(class_="skeleton-sidebar"),
        div(class_="skeleton-content")
    ]
```

### 5. Provide Error Recovery

```python
# pages/dashboard/error.py
@error
def dashboard_error(error, reset):
    return div()[
        "Something went wrong",
        button(onclick=reset)["Try Again"],
        a(href="/")["Go Home"]  # Fallback option
    ]
```

---

## API Reference

### @layout Decorator

```python
from pynext import layout

@layout
def my_layout(children):
    """
    Define a layout component.
    
    Args:
        children: The wrapped content (required parameter)
    
    Returns:
        Element tree representing the layout
    """
    return div()[children]
```

### @loading Decorator

```python
from pynext import loading

@loading
def my_loading():
    """
    Define a loading component.
    
    Returns:
        Element tree shown while loading
    """
    return div()["Loading..."]
```

### @error Decorator

```python
from pynext import error

@error
def my_error(error, reset):
    """
    Define an error boundary.
    
    Args:
        error: The exception that occurred
        reset: Function to retry rendering
    
    Returns:
        Element tree shown on error
    """
    return div()[str(error), button(onclick=reset)["Retry"]]
```

### @not_found Decorator

```python
from pynext import not_found

@not_found
def my_404():
    """
    Define a 404 page.
    
    Returns:
        Element tree for 404 page
    """
    return div()["Not Found"]
```

---

## Next Steps

- [Routing](ROUTING.md) - File-based routing system
- [API Routes](API_ROUTES.md) - REST API endpoints
- [Metadata](METADATA.md) - SEO and social sharing

