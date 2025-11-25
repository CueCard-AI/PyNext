# PyNext Layouts

> **Wrap your pages with shared UI—navigation, sidebars, footers—without repetition.**

Layouts in PyNext provide a way to define UI that persists across multiple pages. They eliminate redundancy, enable nested compositions, and keep your code DRY.

---

## Table of Contents

1. [What Are Layouts?](#what-are-layouts)
2. [The Mental Model](#the-mental-model)
3. [Creating Layouts](#creating-layouts)
4. [Nested Layouts](#nested-layouts)
5. [Layout Resolution](#layout-resolution)
6. [Special Files](#special-files)
7. [Data Fetching in Layouts](#data-fetching-in-layouts)
8. [Layout Patterns](#layout-patterns)
9. [Best Practices](#best-practices)
10. [API Reference](#api-reference)

---

## What Are Layouts?

### The Elevator Pitch

Layouts are **wrapper components** that surround page content. They're perfect for:

- 🧭 **Navigation bars** - Present on every page
- 📊 **Sidebars** - Dashboard navigation, filters
- 🦶 **Footers** - Copyright, links
- 🎨 **Theme providers** - Dark mode, branding
- 🔐 **Auth wrappers** - Login state checks

### The Problem Layouts Solve

```python
# WITHOUT layouts - repeating UI in every page 😢

# pages/index.py
@page
def home():
    return div()[
        Header(),        # Repeated
        Navigation(),    # Repeated
        div()[
            h1()["Home Page"]
        ],
        Footer(),        # Repeated
    ]

# pages/about.py
@page
def about():
    return div()[
        Header(),        # Repeated again!
        Navigation(),    # Repeated again!
        div()[
            h1()["About Page"]
        ],
        Footer(),        # Repeated again!
    ]

# pages/contact.py
@page
def contact():
    return div()[
        Header(),        # And again...
        Navigation(),    # And again...
        div()[
            h1()["Contact Page"]
        ],
        Footer(),        # And again...
    ]
```

```python
# WITH layouts - define once, use everywhere! 🎉

# pages/layout.py
@layout
def root_layout(children):
    return div()[
        Header(),
        Navigation(),
        div()[children],  # Pages go here!
        Footer(),
    ]

# pages/index.py - Just the unique content!
@page
def home():
    return h1()["Home Page"]

# pages/about.py - Clean and focused!
@page
def about():
    return h1()["About Page"]
```

---

## The Mental Model

### First Principles: The Nesting Doll Analogy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          THE NESTING DOLL ANALOGY                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   Think of layouts as RUSSIAN NESTING DOLLS (Matryoshka):                   │
│                                                                              │
│                                                                              │
│   ┌───────────────────────────────────────────────────────────────────┐     │
│   │  ROOT LAYOUT (pages/layout.py)                                     │     │
│   │  ┌───────────────────────────────────────────────────────────┐    │     │
│   │  │  ┌─────────────────────────────────────────────────────┐  │    │     │
│   │  │  │  SECTION LAYOUT (pages/dashboard/layout.py)         │  │    │     │
│   │  │  │  ┌─────────────────────────────────────────────┐    │  │    │     │
│   │  │  │  │                                             │    │  │    │     │
│   │  │  │  │           PAGE CONTENT                      │    │  │    │     │
│   │  │  │  │      (pages/dashboard/settings.py)          │    │  │    │     │
│   │  │  │  │                                             │    │  │    │     │
│   │  │  │  └─────────────────────────────────────────────┘    │  │    │     │
│   │  │  │                                                     │  │    │     │
│   │  │  └─────────────────────────────────────────────────────┘  │    │     │
│   │  │                                                           │    │     │
│   │  └───────────────────────────────────────────────────────────┘    │     │
│   │                                                                    │     │
│   └───────────────────────────────────────────────────────────────────┘     │
│                                                                              │
│                                                                              │
│   Like nesting dolls:                                                       │
│   • Outer dolls (layouts) contain inner dolls (nested layouts/pages)        │
│   • Each layer adds its own decoration (UI elements)                        │
│   • The innermost doll is your page content                                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### How Layouts Compose

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          LAYOUT COMPOSITION                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   Request: GET /dashboard/settings                                          │
│                                                                              │
│                                                                              │
│   FILE STRUCTURE:                    RENDERED RESULT:                       │
│                                                                              │
│   pages/                             ┌─────────────────────────────────────┐│
│   ├── layout.py ─────────────────────│ [Navigation] [User Menu]           ││
│   │                                  ├─────────────────────────────────────┤│
│   └── dashboard/                     │ ┌───────┬───────────────────────┐  ││
│       ├── layout.py ─────────────────│ │       │                       │  ││
│       │                              │ │Sidebar│  Settings Page        │  ││
│       └── settings.py ───────────────│ │       │  ───────────────      │  ││
│                                      │ │ • Home│  [Form fields...]     │  ││
│                                      │ │ • Set │                       │  ││
│                                      │ │ • Prof│                       │  ││
│                                      │ │       │                       │  ││
│                                      │ └───────┴───────────────────────┘  ││
│                                      ├─────────────────────────────────────┤│
│                                      │ [Footer]                            ││
│                                      └─────────────────────────────────────┘│
│                                                                              │
│   ROOT LAYOUT adds: header, footer                                          │
│   DASHBOARD LAYOUT adds: sidebar                                            │
│   PAGE provides: actual content                                             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Creating Layouts

### Basic Layout

Create a `layout.py` file in any directory:

```python
# pages/layout.py - The ROOT layout (wraps ALL pages)

from pynext import layout, div, header, nav, main, footer, a

@layout
def root_layout(children):
    """
    This layout wraps every page in your application.
    'children' is the page content (or nested layout).
    """
    return div(class_="app")[
        # Header with navigation
        header(class_="header")[
            nav(class_="nav")[
                a(href="/", class_="logo")["🚀 MyApp"],
                div(class_="nav-links")[
                    a(href="/")["Home"],
                    a(href="/about")["About"],
                    a(href="/blog")["Blog"],
                    a(href="/contact")["Contact"],
                ],
            ]
        ],
        
        # Main content area
        main(class_="main")[
            children  # ← Pages render here!
        ],
        
        # Footer
        footer(class_="footer")[
            p()["© 2024 MyApp. All rights reserved."],
            div(class_="footer-links")[
                a(href="/privacy")["Privacy"],
                a(href="/terms")["Terms"],
            ],
        ],
    ]
```

### What `children` Contains

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CHILDREN PARAMETER                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   The 'children' parameter receives:                                        │
│                                                                              │
│   • If there's a NESTED LAYOUT → that layout wrapping the page             │
│   • If NO nested layout → the PAGE content directly                         │
│                                                                              │
│                                                                              │
│   CASE 1: No nested layouts                                                 │
│   ──────────────────────────                                                │
│                                                                              │
│   pages/layout.py (root_layout)                                             │
│   pages/about.py                                                            │
│                                                                              │
│   root_layout(children=about_page())                                        │
│                                                                              │
│                                                                              │
│   CASE 2: With nested layouts                                               │
│   ────────────────────────────                                              │
│                                                                              │
│   pages/layout.py (root_layout)                                             │
│   pages/dashboard/layout.py (dashboard_layout)                              │
│   pages/dashboard/settings.py                                               │
│                                                                              │
│   root_layout(                                                              │
│       children=dashboard_layout(                                            │
│           children=settings_page()                                          │
│       )                                                                     │
│   )                                                                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Layout with Head Elements

Add page metadata, styles, and scripts:

```python
from pynext import layout, div, head, html, body, script, link

@layout
def root_layout(children):
    return html(lang="en")[
        head()[
            meta(charset="UTF-8"),
            meta(name="viewport", content="width=device-width, initial-scale=1.0"),
            title()["MyApp"],
            link(rel="stylesheet", href="/styles.css"),
            script(src="/app.js", defer=True),
        ],
        body(class_="app")[
            children,
        ],
    ]
```

---

## Nested Layouts

Create layouts at any folder level. They automatically nest!

### Example Structure

```
pages/
├── layout.py                 # Root layout
├── index.py                  # Homepage
│
├── blog/
│   ├── layout.py            # Blog layout (nested in root)
│   ├── index.py             # Blog listing
│   └── [slug].py            # Blog post
│
└── dashboard/
    ├── layout.py            # Dashboard layout (nested in root)
    ├── index.py             # Dashboard home
    └── settings/
        ├── layout.py        # Settings layout (nested in dashboard)
        ├── index.py         # Settings home
        └── profile.py       # Profile settings
```

### Nested Layout Implementation

```python
# pages/layout.py - ROOT
from pynext import layout, div, header, main, footer

@layout
def root_layout(children):
    return div(class_="app")[
        header(class_="main-header")[
            a(href="/")["🏠 Home"],
            a(href="/dashboard")["📊 Dashboard"],
            a(href="/blog")["📝 Blog"],
        ],
        main(class_="content")[children],
        footer()["© 2024"],
    ]


# pages/dashboard/layout.py - DASHBOARD (nested)
from pynext import layout, div, nav, aside

@layout
def dashboard_layout(children):
    """
    This receives the page (or nested layout) as 'children'.
    It's then wrapped by root_layout automatically.
    """
    return div(class_="dashboard")[
        # Sidebar navigation
        aside(class_="sidebar")[
            nav()[
                a(href="/dashboard")["📊 Overview"],
                a(href="/dashboard/analytics")["📈 Analytics"],
                a(href="/dashboard/settings")["⚙️ Settings"],
            ]
        ],
        # Main dashboard content
        div(class_="dashboard-content")[children],
    ]


# pages/dashboard/settings/layout.py - SETTINGS (nested in dashboard)
from pynext import layout, div, nav

@layout
def settings_layout(children):
    return div(class_="settings")[
        nav(class_="settings-nav")[
            a(href="/dashboard/settings")["General"],
            a(href="/dashboard/settings/profile")["Profile"],
            a(href="/dashboard/settings/security")["Security"],
            a(href="/dashboard/settings/billing")["Billing"],
        ],
        div(class_="settings-content")[children],
    ]
```

### Rendered Result

For a request to `/dashboard/settings/profile`:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ROOT LAYOUT                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  [🏠 Home] [📊 Dashboard] [📝 Blog]                    ← main-header   ││
│  ├─────────────────────────────────────────────────────────────────────────┤│
│  │  DASHBOARD LAYOUT                                                       ││
│  │  ┌───────────┬─────────────────────────────────────────────────────────┐││
│  │  │ 📊 Overview│  SETTINGS LAYOUT                                       │││
│  │  │ 📈 Analytics  ┌─────────────────────────────────────────────────────┐│││
│  │  │ ⚙️ Settings   │  [General] [Profile] [Security] [Billing]          ││││
│  │  │  (sidebar)    ├─────────────────────────────────────────────────────┤│││
│  │  │               │  PAGE: Profile Settings                             ││││
│  │  │               │  ─────────────────────                             ││││
│  │  │               │  [Avatar upload]                                    ││││
│  │  │               │  [Name: ___________]                                ││││
│  │  │               │  [Email: __________]                                ││││
│  │  │               │                                                      ││││
│  │  │               └─────────────────────────────────────────────────────┘│││
│  │  └───────────┴─────────────────────────────────────────────────────────┘││
│  ├─────────────────────────────────────────────────────────────────────────┤│
│  │  © 2024                                                  ← footer       ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Layout Resolution

PyNext automatically finds and nests layouts from root to page.

### Resolution Algorithm

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          LAYOUT RESOLUTION                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   For route: /dashboard/settings/profile                                    │
│                                                                              │
│   PyNext searches for layouts in order:                                     │
│                                                                              │
│   1. pages/layout.py                          ← Found (ROOT)                │
│   2. pages/dashboard/layout.py                ← Found                       │
│   3. pages/dashboard/settings/layout.py       ← Found                       │
│   4. (page: pages/dashboard/settings/profile.py)                            │
│                                                                              │
│                                                                              │
│   Composition (inside-out):                                                 │
│   ─────────────────────────                                                 │
│                                                                              │
│   content = profile_page()                                                  │
│   content = settings_layout(children=content)                               │
│   content = dashboard_layout(children=content)                              │
│   content = root_layout(children=content)                                   │
│                                                                              │
│                                                                              │
│   Result:                                                                   │
│   ───────                                                                   │
│                                                                              │
│   root_layout ──┐                                                           │
│                 └──► dashboard_layout ──┐                                   │
│                                         └──► settings_layout ──┐            │
│                                                                 └──► page   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Partial Layout Trees

Not every folder needs a layout:

```
pages/
├── layout.py              # Root layout ✓
├── blog/
│   ├── layout.py         # Blog has its own layout ✓
│   └── [slug].py
├── about.py               # No layout folder → uses root only
└── docs/
    ├── intro.py           # No layout.py here → uses root only
    └── api/
        └── overview.py    # Still just root layout
```

```
/blog/hello     → root_layout > blog_layout > page
/about          → root_layout > page (no nesting)
/docs/api/overview → root_layout > page (no intermediate layouts)
```

---

## Special Files

PyNext supports special files alongside layouts:

### loading.py - Loading State

```python
# pages/dashboard/loading.py
from pynext import div, span

def loading():
    """Shown while dashboard content is loading."""
    return div(class_="loading")[
        div(class_="spinner"),
        span()["Loading dashboard..."]
    ]
```

### error.py - Error Boundary

```python
# pages/dashboard/error.py
from pynext import div, h1, p, button

def error(error_info):
    """Shown when an error occurs in dashboard pages."""
    return div(class_="error")[
        h1()["Something went wrong"],
        p()[str(error_info.get("message", "Unknown error"))],
        button(onclick="location.reload()")["Try Again"],
    ]
```

### not-found.py - 404 Page

```python
# pages/not-found.py (global 404)
from pynext import page, div, h1, p, a

@page(title="Page Not Found")
def not_found():
    return div(class_="not-found")[
        h1()["404 - Page Not Found"],
        p()["The page you're looking for doesn't exist."],
        a(href="/")["Go Home"],
    ]
```

### Special Files Hierarchy

```
pages/
├── layout.py          # Root layout
├── loading.py         # Global loading
├── error.py           # Global error
├── not-found.py       # Global 404
│
└── dashboard/
    ├── layout.py      # Dashboard layout
    ├── loading.py     # Dashboard-specific loading
    ├── error.py       # Dashboard-specific error
    └── settings.py
```

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SPECIAL FILES RESOLUTION                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   When rendering /dashboard/settings:                                       │
│                                                                              │
│   LOADING STATE:                                                            │
│   ───────────────                                                           │
│   1. Check pages/dashboard/loading.py ← Use if exists                      │
│   2. Check pages/loading.py          ← Fallback                            │
│   3. Default loading UI              ← Built-in fallback                   │
│                                                                              │
│   ERROR STATE:                                                              │
│   ─────────────                                                             │
│   1. Check pages/dashboard/error.py  ← Use if exists                       │
│   2. Check pages/error.py            ← Fallback                            │
│   3. Default error UI                ← Built-in fallback                   │
│                                                                              │
│   The CLOSEST special file to the route is used!                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Fetching in Layouts

### Async Layouts

Layouts can fetch data:

```python
# pages/layout.py
from pynext import layout, div, nav

@layout
async def root_layout(children):
    # Fetch user data for navigation
    user = await get_current_user()
    nav_items = await get_navigation()
    
    return div(class_="app")[
        Navigation(user=user, items=nav_items),
        main()[children],
        Footer(),
    ]
```

### Layout Data Availability

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DATA FLOW IN LAYOUTS                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   IMPORTANT: Layouts render BEFORE pages!                                   │
│                                                                              │
│                                                                              │
│   RENDER ORDER:                                                             │
│   ─────────────                                                             │
│                                                                              │
│   1. Root layout fetches its data                                           │
│   2. Nested layouts fetch their data (in order)                             │
│   3. Page fetches its data                                                  │
│   4. Everything composes together                                           │
│                                                                              │
│                                                                              │
│   DATA SHARING OPTIONS:                                                     │
│   ─────────────────────                                                     │
│                                                                              │
│   Option 1: Context (recommended)                                           │
│   ────────────────────────────────                                          │
│   Layout stores data in context, pages read from context                    │
│                                                                              │
│   Option 2: Parallel fetching                                               │
│   ────────────────────────────────                                          │
│   Each level fetches independently (may duplicate requests)                 │
│                                                                              │
│   Option 3: Props drilling (not available)                                  │
│   ─────────────────────────────────────────                                 │
│   Layouts can't directly pass props to pages                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Using Context for Shared Data

```python
# lib/context.py
from pynext import create_context

UserContext = create_context("user")
ThemeContext = create_context("theme")

# pages/layout.py
from pynext import layout
from lib.context import UserContext, ThemeContext

@layout
async def root_layout(children):
    user = await get_current_user()
    theme = await get_user_theme(user.id) if user else "light"
    
    return UserContext.Provider(value=user)[
        ThemeContext.Provider(value=theme)[
            div(class_=f"app theme-{theme}")[children]
        ]
    ]

# pages/dashboard/index.py
from pynext import page, use_context
from lib.context import UserContext

@page
def dashboard():
    user = use_context(UserContext)
    
    return div()[
        h1()[f"Welcome, {user.name}!"],
    ]
```

---

## Layout Patterns

### Pattern 1: Auth Layout

```python
# pages/layout.py
from pynext import layout, redirect
from lib.auth import get_session

@layout
async def root_layout(children):
    session = await get_session()
    
    return div(class_="app")[
        TopBar(user=session.user if session else None),
        children,
    ]

# pages/(protected)/layout.py
from pynext import layout, redirect
from lib.auth import get_session

@layout
async def protected_layout(children):
    session = await get_session()
    
    if not session:
        # Redirect unauthenticated users
        return redirect("/login")
    
    return div(class_="protected")[
        children
    ]
```

### Pattern 2: Marketing vs App Layout

```python
# pages/(marketing)/layout.py
@layout
def marketing_layout(children):
    """Clean, simple layout for landing pages."""
    return div(class_="marketing")[
        MarketingNav(),
        children,
        MarketingFooter(),
    ]

# pages/(app)/layout.py
@layout
def app_layout(children):
    """Full-featured layout for authenticated app."""
    return div(class_="app")[
        AppHeader(),
        div(class_="app-body")[
            Sidebar(),
            main()[children],
        ],
    ]
```

### Pattern 3: Responsive Sidebar

```python
# pages/dashboard/layout.py
from pynext import layout, Signal

@layout
def dashboard_layout(children):
    sidebar_open = Signal(True)
    
    return div(class_="dashboard")[
        # Mobile toggle
        button(
            class_="sidebar-toggle",
            onclick=lambda: sidebar_open.set(not sidebar_open.get())
        )["☰"],
        
        # Sidebar (conditional class)
        aside(
            class_=lambda: f"sidebar {'open' if sidebar_open.get() else 'closed'}"
        )[
            DashboardNav(),
        ],
        
        # Content
        div(class_="dashboard-main")[children],
    ]
```

### Pattern 4: Breadcrumbs Layout

```python
# pages/products/layout.py
from pynext import layout, get_current_path

@layout
def products_layout(children):
    path = get_current_path()
    
    # Build breadcrumb from path
    segments = path.strip("/").split("/")
    breadcrumbs = []
    current = ""
    
    for segment in segments:
        current += f"/{segment}"
        breadcrumbs.append({
            "label": segment.replace("-", " ").title(),
            "href": current,
        })
    
    return div(class_="products-page")[
        nav(class_="breadcrumbs")[
            [
                span()[
                    a(href=crumb["href"])[crumb["label"]],
                    " / " if i < len(breadcrumbs) - 1 else ""
                ]
                for i, crumb in enumerate(breadcrumbs)
            ]
        ],
        children,
    ]
```

### Pattern 5: Theme Provider Layout

```python
# pages/layout.py
from pynext import layout, Signal, create_context

ThemeContext = create_context("theme")

@layout
def root_layout(children):
    theme = Signal("light")
    
    def toggle_theme():
        theme.set("dark" if theme.get() == "light" else "light")
    
    return ThemeContext.Provider(value={"theme": theme, "toggle": toggle_theme})[
        html(class_=lambda: f"theme-{theme.get()}")[
            head()[...],
            body()[
                ThemeToggle(toggle=toggle_theme),
                children,
            ],
        ]
    ]

# Any nested component can access theme
from pynext import use_context

def ThemeToggle(toggle):
    ctx = use_context(ThemeContext)
    return button(onclick=toggle)[
        "🌙" if ctx["theme"].get() == "light" else "☀️"
    ]
```

---

## Best Practices

### Do's and Don'ts

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          LAYOUT BEST PRACTICES                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ✓ DO                                                                      │
│   ────                                                                      │
│                                                                              │
│   ✓ Keep layouts focused on structure, not content                         │
│     Layout: header, nav, footer                                             │
│     Page: actual content                                                    │
│                                                                              │
│   ✓ Use context for shared data (auth, theme, user)                        │
│     UserContext.Provider in layout → use_context in pages                   │
│                                                                              │
│   ✓ Create special files for loading/error states                          │
│     pages/dashboard/loading.py for dashboard-specific loading              │
│                                                                              │
│   ✓ Nest layouts logically (by feature/section)                            │
│     pages/dashboard/layout.py for all dashboard pages                       │
│                                                                              │
│   ✓ Keep layout renders fast                                               │
│     Layouts render on every page in their scope                             │
│                                                                              │
│                                                                              │
│   ✗ DON'T                                                                   │
│   ───────                                                                   │
│                                                                              │
│   ✗ Put page-specific logic in layouts                                     │
│     Layouts should be generic wrappers                                      │
│                                                                              │
│   ✗ Fetch heavy data in root layout                                        │
│     It runs for EVERY page - keep it light                                  │
│                                                                              │
│   ✗ Create deeply nested layouts (>3 levels)                               │
│     Hard to maintain and debug                                              │
│                                                                              │
│   ✗ Duplicate layout code across files                                     │
│     Extract shared components instead                                       │
│                                                                              │
│   ✗ Forget to include {children}                                           │
│     Your pages won't render!                                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Layout Organization

```
# Recommended structure

pages/
├── layout.py              # Minimal: html, head, body, analytics
│
├── (marketing)/           # Marketing pages group
│   ├── layout.py          # Marketing nav, footer
│   ├── index.py
│   ├── about.py
│   └── pricing.py
│
├── (app)/                 # App pages group
│   ├── layout.py          # App shell, auth check
│   │
│   ├── dashboard/
│   │   ├── layout.py      # Dashboard sidebar
│   │   ├── index.py
│   │   └── analytics.py
│   │
│   └── settings/
│       ├── layout.py      # Settings tabs
│       ├── index.py
│       └── profile.py
│
└── (auth)/               # Auth pages (minimal layout)
    ├── layout.py          # Centered, minimal
    ├── login.py
    └── register.py

components/
├── layouts/
│   ├── MarketingNav.py
│   ├── AppSidebar.py
│   └── Footer.py
```

---

## API Reference

### @layout Decorator

```python
from pynext import layout

@layout
def my_layout(children):
    """
    children: The page content or nested layout to render.
    Returns: The layout JSX/HTML with children embedded.
    """
    return div()[
        Header(),
        children,  # Required!
        Footer(),
    ]

# Async layout
@layout
async def async_layout(children):
    data = await fetch_data()
    return div()[children]
```

### Special File Exports

```python
# loading.py
def loading():
    """No decorator needed."""
    return div()["Loading..."]

# error.py
def error(error_info: dict):
    """Receives error details."""
    return div()[error_info.get("message")]

# not-found.py
@page  # Use @page decorator
def not_found():
    return div()["404 Not Found"]
```

### Context API

```python
from pynext import create_context, use_context

# Create
UserContext = create_context("user")

# Provide (in layout)
UserContext.Provider(value=user)[children]

# Consume (in pages/components)
user = use_context(UserContext)
```

### Layout Resolution Functions

```python
from pynext.router import get_layouts_for_path

# Get layout chain for a path
layouts = get_layouts_for_path("/dashboard/settings")
# [root_layout, dashboard_layout, settings_layout]
```

---

## Related Documentation

- [Routing](ROUTING.md) - File-based routing system
- [Streaming & Suspense](STREAMING_SUSPENSE.md) - Loading states with Suspense
- [State Management](STATE_MANAGEMENT.md) - Context and signals
- [Components](COMPONENTS.md) - Building reusable components

---

## Summary

You've learned:

1. ✅ What layouts are and why they matter
2. ✅ How to create and nest layouts
3. ✅ Layout resolution algorithm
4. ✅ Special files (loading, error, not-found)
5. ✅ Data fetching in layouts
6. ✅ Common layout patterns
7. ✅ Best practices for organization

Layouts are the skeleton of your app—structure them well! 🦴
