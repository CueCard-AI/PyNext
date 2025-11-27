# Error Pages

Custom 401, 403, 404, and 500 error pages with zero JavaScript.

---

## The Problem (Why This Exists)

HTTP errors happen. Users get them. The default browser error pages are:
- **Ugly** - generic browser chrome, no branding
- **Unhelpful** - "403 Forbidden" tells users nothing
- **Dead ends** - no way to navigate back or recover

Good error pages:
- **Match your brand** - same styling as your app
- **Explain what happened** - "You need to sign in" vs "401"
- **Provide next steps** - links to login, home, or support

### Real-World Analogy

Think of error pages like **helpful store signs**:

| Bad Sign | Good Sign |
|----------|-----------|
| "CLOSED" | "We're closed now. Open Mon-Fri 9-5. Call us at..." |
| "NO ENTRY" | "Staff only. Visitors please check in at reception." |
| "ERROR" | "Sorry, we couldn't find that item. Try searching or browse our catalog." |

---

## First Principles: How Error Pages Work

### The Core Concept

PyNext provides:
1. **Error exceptions** - Raise to trigger error pages
2. **Error page decorators** - Define custom error page components
3. **Default fallbacks** - Built-in pages if you don't customize
4. **Zero JS rendering** - Error pages ship no JavaScript (reliability)

### Mental Model

```
┌─────────────────────────────────────────────────────────┐
│                    CODE PATH                            │
│                                                         │
│   @page                                                 │
│   def admin():                                          │
│       if not user:                                      │
│           raise UnauthorizedError()  ──────┐           │
│       if not user.is_admin:                │           │
│           raise ForbiddenError() ───────────┤           │
│       return AdminPage()                    │           │
│                               ┌─────────────┘           │
│                               ▼                         │
│   ┌─────────────────────────────────────────────────┐  │
│   │              ERROR HANDLING                      │  │
│   │                                                  │  │
│   │   1. Catch PyNextError                          │  │
│   │   2. Look for custom page (unauthorized.py)     │  │
│   │   3. Render page with error details             │  │
│   │   4. Return HTML with status code               │  │
│   │                                                  │  │
│   └─────────────────────────────────────────────────┘  │
│                               │                         │
│                               ▼                         │
│   HTML Response (401/403/404/500)                      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Step-by-Step: What Happens When You Raise an Error

1. **Page code raises error**:
   ```python
   raise UnauthorizedError("Please sign in to view this page")
   ```

2. **PyNext catches the error** in the request handler

3. **Custom page lookup**:
   ```
   Looking for: pages/unauthorized.py
   Found: Yes → Use custom page
   Not found: Use default 401 page
   ```

4. **Page rendered with error details**:
   ```python
   # Your custom page receives the error
   def custom_401(error=None):
       message = error.message  # "Please sign in to view this page"
   ```

5. **HTML returned** with correct status code (401)

---

## Quick Start (Copy-Paste Ready)

### Raising Errors (In Your Pages)

```python
# pages/admin/page.py

from pynext import page, unauthorized, forbidden

@page(title="Admin Dashboard")
def admin():
    user = get_current_user()
    
    # Not logged in → 401
    if not user:
        unauthorized("Please sign in to access the admin area")
    
    # Logged in but not admin → 403
    if not user.is_admin:
        forbidden("You need admin privileges to access this page")
    
    return AdminDashboard()
```

**What this does:**
- `unauthorized()` raises `UnauthorizedError` with 401 status
- `forbidden()` raises `ForbiddenError` with 403 status
- PyNext catches these and renders appropriate error pages

### Creating Custom Error Pages

**401 Unauthorized Page**:

```python
# pages/unauthorized.py

from pynext import unauthorized_page, div, h1, p, a

@unauthorized_page
def custom_401(error=None):
    return div(class_="error-page")[
        h1()["Sign In Required"],
        p()[error.message if error else "Please sign in to continue"],
        a(href="/login", class_="btn btn-primary")["Go to Login"],
        a(href="/", class_="btn btn-secondary")["Back to Home"],
    ]
```

**403 Forbidden Page**:

```python
# pages/forbidden.py

from pynext import forbidden_page, div, h1, p, a

@forbidden_page
def custom_403(error=None):
    return div(class_="error-page")[
        h1()["Access Denied"],
        p()[error.message if error else "You don't have permission for this page"],
        a(href="/", class_="btn")["Return Home"],
    ]
```

---

## Complete API Reference

### Error Classes

#### `UnauthorizedError` (401)

**What it is**: User is not authenticated (not logged in).

**When to use**: Protected pages that require login.

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `message` | `str` | `"Please sign in to continue"` | Error message |
| `redirect_to` | `str` | `"/login"` | Where to redirect after login |
| `return_to` | `str` | `None` | URL to return to after login |

**Example**:

```python
from pynext import UnauthorizedError

# Basic
raise UnauthorizedError()

# With message
raise UnauthorizedError("Members only content")

# With custom redirect
raise UnauthorizedError(
    message="Premium subscribers only",
    redirect_to="/subscribe",
    return_to="/premium-content",
)
```

---

#### `ForbiddenError` (403)

**What it is**: User is authenticated but lacks permission.

**When to use**: When logged-in user can't access a resource.

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `message` | `str` | `"You don't have permission..."` | Error message |
| `required_role` | `str` | `None` | Role needed (for display) |

**Example**:

```python
from pynext import ForbiddenError

# Basic
raise ForbiddenError()

# With role info
raise ForbiddenError(
    message="Only administrators can access user management",
    required_role="admin",
)
```

---

#### `NotFoundError` (404)

**What it is**: Resource doesn't exist.

**When to use**: When a dynamic resource isn't found.

**Example**:

```python
from pynext import NotFoundError, raise_not_found

# As exception
raise NotFoundError(f"Post '{slug}' not found")

# As convenience function
post = get_post(slug)
if not post:
    raise_not_found(f"Post '{slug}' doesn't exist")
```

---

#### `ServerError` (500)

**What it is**: Internal server error.

**When to use**: When something unexpected fails.

**Example**:

```python
from pynext import ServerError, server_error

try:
    result = external_api.call()
except APIError:
    server_error("We're having trouble connecting to our servers")
```

---

#### `BadRequestError` (400)

**What it is**: Client sent invalid data.

**When to use**: Invalid form data, malformed requests.

**Example**:

```python
from pynext import BadRequestError, bad_request

if not is_valid_email(email):
    bad_request("Please enter a valid email address")
```

---

### Convenience Functions

One-liner functions that raise the corresponding errors:

```python
from pynext import unauthorized, forbidden, raise_not_found, bad_request, server_error

# These raise immediately
unauthorized("Must be logged in")       # → UnauthorizedError
forbidden("Admin only")                   # → ForbiddenError
raise_not_found("Page doesn't exist")    # → NotFoundError (renamed to avoid conflict with @not_found)
bad_request("Invalid input")             # → BadRequestError
server_error("Something broke")          # → ServerError
```

---

### Error Page Decorators

#### `@unauthorized_page`

**What it does**: Marks a function as the custom 401 page.

**File location**: `pages/unauthorized.py`

```python
from pynext import unauthorized_page

@unauthorized_page
def my_401_page(error=None):
    # error is the UnauthorizedError that was raised
    return div()[
        h1()["Please Sign In"],
        p()[error.message if error else "Default message"],
    ]
```

---

#### `@forbidden_page`

**What it does**: Marks a function as the custom 403 page.

**File location**: `pages/forbidden.py`

```python
from pynext import forbidden_page

@forbidden_page
def my_403_page(error=None):
    return div()[
        h1()["Access Denied"],
        p()[error.message if error else "No permission"],
    ]
```

---

#### `@not_found_page`

**What it does**: Marks a function as the custom 404 page.

**File location**: `pages/not-found.py` or `pages/not_found.py`

```python
from pynext import not_found_page

@not_found_page
def my_404_page(error=None):
    return div()[
        h1()["Page Not Found"],
        p()["The page you're looking for doesn't exist."],
    ]
```

---

#### `@server_error_page`

**What it does**: Marks a function as the custom 500 page.

**File location**: `pages/error.py`

```python
from pynext import server_error_page

@server_error_page
def my_500_page(error=None):
    return div()[
        h1()["Something Went Wrong"],
        p()["We're working on fixing this."],
    ]
```

---

## Real-World Patterns

### Pattern 1: Auth-Aware 401 Page

**Scenario**: Show different content based on auth state.

```python
# pages/unauthorized.py

from pynext import unauthorized_page, div, h1, p, a, get_context

@unauthorized_page
def auth_aware_401(error=None):
    ctx = get_context()
    
    # Check if user is partially authenticated
    partial_user = ctx.get("partial_user")
    
    if partial_user:
        # User started auth but didn't complete (e.g., MFA pending)
        return div(class_="error-page")[
            h1()["Verification Required"],
            p()[f"Hi {partial_user.name}, please complete verification"],
            a(href="/auth/verify")["Complete Verification"],
        ]
    
    # Fully unauthenticated
    return div(class_="error-page")[
        h1()["Sign In Required"],
        p()[error.message if error else "Please sign in to continue"],
        div(class_="auth-buttons")[
            a(href="/login", class_="btn btn-primary")["Sign In"],
            a(href="/register", class_="btn btn-outline")["Create Account"],
        ],
    ]
```

---

### Pattern 2: Role-Based 403 Page

**Scenario**: Show what role is needed and how to get it.

```python
# pages/forbidden.py

from pynext import forbidden_page, div, h1, p, a, ul, li

@forbidden_page
def role_based_403(error=None):
    required_role = getattr(error, 'required_role', None) if error else None
    
    role_info = {
        "admin": {
            "title": "Admin Access Required",
            "how_to": "Contact your organization administrator.",
        },
        "premium": {
            "title": "Premium Feature",
            "how_to": "Upgrade your subscription to access this feature.",
            "link": "/pricing",
            "link_text": "View Plans",
        },
        "verified": {
            "title": "Verification Required",
            "how_to": "Please verify your email address.",
            "link": "/settings/verify",
            "link_text": "Verify Now",
        },
    }
    
    info = role_info.get(required_role, {
        "title": "Access Denied",
        "how_to": "You don't have permission to access this page.",
    })
    
    return div(class_="error-page")[
        h1()[info["title"]],
        p()[error.message if error else info["how_to"]],
        a(href=info.get("link", "/"), class_="btn")[
            info.get("link_text", "Go Back")
        ],
    ]
```

---

### Pattern 3: Helpful 404 with Search

**Scenario**: Help users find what they're looking for.

```python
# pages/not-found.py

from pynext import not_found_page, div, h1, p, a, form, input_, ul, li

@not_found_page
def helpful_404(error=None):
    return div(class_="error-page")[
        h1()["Page Not Found"],
        p()["We couldn't find what you're looking for."],
        
        # Search box
        form(action="/search", method="get", class_="search-form")[
            input_(
                type="search",
                name="q",
                placeholder="Search for content...",
                class_="search-input",
            ),
        ],
        
        # Popular pages
        div(class_="popular-pages")[
            p(class_="section-title")["Popular Pages:"],
            ul()[
                li()[a(href="/")["Home"]],
                li()[a(href="/docs")["Documentation"]],
                li()[a(href="/blog")["Blog"]],
                li()[a(href="/contact")["Contact Us"]],
            ],
        ],
        
        # Support link
        p(class_="support")[
            "Need help? ",
            a(href="/support")["Contact support"],
        ],
    ]
```

---

### Pattern 4: Branded 500 Page

**Scenario**: Maintain brand trust during errors.

```python
# pages/error.py

from pynext import server_error_page, div, h1, p, a, img

@server_error_page
def branded_500(error=None):
    return div(class_="error-page error-500")[
        img(
            src="/images/error-illustration.svg",
            alt="Error illustration",
            class_="error-image",
        ),
        h1()["Oops! Something went wrong"],
        p()[
            "We're experiencing technical difficulties. "
            "Our team has been notified and is working on it."
        ],
        div(class_="error-actions")[
            a(href="/", class_="btn btn-primary")["Go to Homepage"],
            a(href="/status", class_="btn btn-secondary")["Check Status"],
        ],
        p(class_="error-id")[
            f"Error ID: {generate_error_id()}" if error else ""
        ],
    ]
```

---

## How It Works Under the Hood

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    REQUEST FLOW                         │
│                                                         │
│   @page                                                 │
│   def my_page():                                        │
│       raise ForbiddenError()                           │
│           │                                             │
│           ▼                                             │
│   ┌─────────────────────────────────────────────────┐  │
│   │   PyNextApp.handle_page()                        │  │
│   │                                                  │  │
│   │   try:                                          │  │
│   │       html = await route.handle(request)        │  │
│   │   except ForbiddenError as e:          ◄────────┤  │
│   │       html = self._render_403(e)               │  │
│   │       return HTMLResponse(html, status=403)    │  │
│   │                                                  │  │
│   └─────────────────────────────────────────────────┘  │
│                               │                         │
│                               ▼                         │
│   ┌─────────────────────────────────────────────────┐  │
│   │   _render_403()                                  │  │
│   │                                                  │  │
│   │   1. Look for custom forbidden page             │  │
│   │   2. If found: forbidden.render_full_page(e)    │  │
│   │   3. If not: get_default_error_html(403, e)    │  │
│   │                                                  │  │
│   └─────────────────────────────────────────────────┘  │
│                               │                         │
│                               ▼                         │
│   HTML Response (no JavaScript!)                       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Zero JavaScript Rendering

Error pages are rendered without JavaScript:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="robots" content="noindex, nofollow">
    <title>403 Forbidden</title>
    <link rel="stylesheet" href="/_pynext/styles.css">
    <!-- No <script> tags! -->
</head>
<body>
    <div id="__pynext" class="error-container">
        <!-- Your error page content -->
    </div>
    <!-- No hydration, no React, no JavaScript -->
</body>
</html>
```

**Why no JavaScript?**
- **Reliability**: JS errors can't break error pages
- **Speed**: Renders instantly, no bundle to load
- **SEO**: `noindex` + fast load for crawlers
- **Accessibility**: Works with JS disabled

---

## Troubleshooting

### "My custom error page isn't showing"

**Check 1**: Is the file in the right location?

```
pages/
├── unauthorized.py   # For 401
├── forbidden.py      # For 403
├── not-found.py      # For 404 (or not_found.py)
├── error.py          # For 500
```

**Check 2**: Did you use the decorator?

```python
# Wrong - no decorator
def custom_401():
    return ...

# Right
@unauthorized_page
def custom_401():
    return ...
```

---

### "Error details aren't showing"

**Check**: Is your function accepting `error` parameter?

```python
# Wrong - no error param
@unauthorized_page
def my_401():
    return "Error"

# Right
@unauthorized_page
def my_401(error=None):
    return f"Error: {error.message if error else 'Unknown'}"
```

---

### "Getting 500 instead of 401/403"

**Check**: Are you using convenience functions or raising properly?

```python
# Wrong - just returning
def admin():
    if not user:
        return "Not authorized"  # Returns 200!

# Right - raising error
def admin():
    if not user:
        unauthorized()  # Returns 401
```

---

## Summary

**Key Takeaways**:

1. **Use error exceptions** (`UnauthorizedError`, `ForbiddenError`) in your pages
2. **Create custom error pages** with `@unauthorized_page`, `@forbidden_page`, etc.
3. **Error pages ship zero JavaScript** for reliability
4. **The `error` parameter** gives you access to the error message

**Error Quick Reference**:

| Status | Error Class | Convenience | Page Decorator | File |
|--------|-------------|-------------|----------------|------|
| 400 | `BadRequestError` | `bad_request()` | N/A | N/A |
| 401 | `UnauthorizedError` | `unauthorized()` | `@unauthorized_page` | `unauthorized.py` |
| 403 | `ForbiddenError` | `forbidden()` | `@forbidden_page` | `forbidden.py` |
| 404 | `NotFoundError` | `raise_not_found()` | `@not_found` / `@not_found_page` | `not-found.py` |
| 500 | `ServerError` | `server_error()` | `@server_error_page` | `error.py` |

**Next Steps**:

- [Route Groups](./ROUTE_GROUPS.md) - Organize pages
- [Templates](./TEMPLATE.md) - Page transitions
- [Project Structure](./PROJECT_STRUCTURE.md) - src/ folder support

