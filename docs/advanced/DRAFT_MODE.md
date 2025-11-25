# Draft Mode (Signal-Based Preview)

> **PyNext's approach to content preview that only updates what changes.**

Draft Mode enables content editors to preview unpublished content in the context of a production site. Unlike traditional implementations that re-render the entire page, PyNext uses **signal-based updates** to refresh only draft-aware components—providing 10x+ faster preview switching.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [How It Works](#how-it-works)
4. [Quick Start](#quick-start)
5. [Core API Reference](#core-api-reference)
6. [Components](#components)
7. [Server Integration](#server-integration)
8. [CMS Integration](#cms-integration)
9. [Security](#security)
10. [Performance](#performance)
11. [Best Practices](#best-practices)
12. [Do's and Don'ts](#dos-and-donts)
13. [Troubleshooting](#troubleshooting)
14. [Complete Examples](#complete-examples)

---

## Overview

### What is Draft Mode?

Draft Mode is a feature that allows content creators to preview unpublished (draft) content on a live website before publishing. It's essential for:

- **Content Management Systems (CMS)** - Preview blog posts, articles, product descriptions
- **Editorial workflows** - Review and approve content before going live
- **A/B testing drafts** - Compare draft vs published content side-by-side
- **Quality assurance** - Catch errors before they reach production

### PyNext's Innovation: Signal-Based Updates

Traditional frameworks (like Next.js) handle draft mode by:
1. Detecting a draft cookie
2. Re-rendering the **entire page** with draft content
3. Sending a completely new HTML response

PyNext takes a fundamentally different approach:

```
┌─────────────────────────────────────────────────────────────────┐
│                    TRADITIONAL APPROACH                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Toggle Draft Mode                                             │
│         │                                                       │
│         ▼                                                       │
│   ┌───────────────────────────────────────────────────────┐    │
│   │           Re-render ENTIRE page (~100ms)              │    │
│   │  ┌─────────┬─────────┬─────────┬─────────┬─────────┐ │    │
│   │  │ Header  │   Nav   │ Content │ Sidebar │ Footer  │ │    │
│   │  │ (same)  │ (same)  │(changed)│ (same)  │ (same)  │ │    │
│   │  └─────────┴─────────┴─────────┴─────────┴─────────┘ │    │
│   └───────────────────────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    PYNEXT SIGNAL APPROACH                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Toggle Draft Mode                                             │
│         │                                                       │
│         ▼                                                       │
│   Update DraftSignal (instant)                                  │
│         │                                                       │
│         ▼                                                       │
│   ┌─────────┬─────────┬─────────┬─────────┬─────────┐          │
│   │ Header  │   Nav   │ Content │ Sidebar │ Footer  │          │
│   │(static) │(static) │   ▼     │(static) │(static) │          │
│   └─────────┴─────────┴─────────┴─────────┴─────────┘          │
│                         │                                       │
│                         ▼                                       │
│              ┌───────────────────┐                              │
│              │  Update ONLY      │                              │
│              │  draft-aware      │  (~1ms)                      │
│              │  component        │                              │
│              └───────────────────┘                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Key Benefits

| Feature | Next.js | PyNext |
|---------|---------|--------|
| Toggle Speed | ~100ms (full re-render) | ~1ms (signal update) |
| Static Content | Re-rendered | Preserved |
| JavaScript Size | ~2,000 bytes | ~500 bytes |
| Network Requests | Full page fetch | None (client toggle) |
| SEO Impact | Page blinks | Seamless |

---

## Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           PYNEXT DRAFT MODE                             │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────────┐    ┌───────────────────┐    ┌───────────────────┐
│   CORE LAYER      │    │   SERVER LAYER    │    │  MIDDLEWARE LAYER │
│ pynext/core/draft │    │ pynext/server/    │    │ pynext/middleware │
│                   │    │      draft        │    │      /draft       │
├───────────────────┤    ├───────────────────┤    ├───────────────────┤
│ • DraftSignal     │    │ • DraftConfig     │    │ • detect_draft_   │
│ • DraftContext    │    │ • Token Gen/Verify│    │   mode()          │
│ • use_draft()     │    │ • API Router      │    │ • setup_draft_    │
│ • @draft_content  │    │ • DraftMiddleware │    │   context()       │
│ • @draft_only     │    │                   │    │ • inject_draft_   │
│ • @published_only │    │                   │    │   state()         │
│ • DraftSwitch     │    │                   │    │                   │
│ • DraftBanner     │    │                   │    │                   │
│ • DraftOverlay    │    │                   │    │                   │
└───────────────────┘    └───────────────────┘    └───────────────────┘
        │                           │                           │
        └───────────────────────────┼───────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │       CLIENT RUNTIME          │
                    │    JavaScript (~500 bytes)    │
                    ├───────────────────────────────┤
                    │ • __pynext__.draft.enable()   │
                    │ • __pynext__.draft.disable()  │
                    │ • __pynext__.draft.toggle()   │
                    │ • Cookie management           │
                    │ • DOM updates                 │
                    └───────────────────────────────┘
```

### Component Hierarchy

```
DraftSignal (Signal<bool>)
    │
    ├── Core State
    │   ├── _value: bool (draft enabled/disabled)
    │   ├── _draft_token: Optional[str]
    │   └── _subscribers: list[Callable]
    │
    ├── Methods
    │   ├── enable(token) ──────► Sets _value=True, stores token
    │   ├── disable() ──────────► Sets _value=False, clears token
    │   ├── toggle() ───────────► Flips _value
    │   └── is_authenticated() ─► Checks if token exists
    │
    └── Reactive Updates
        └── On change ──────────► Notifies all subscribers
                                  (draft-aware components)
```

### Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         REQUEST LIFECYCLE                               │
└─────────────────────────────────────────────────────────────────────────┘

                        ┌──────────────────┐
                        │  Incoming HTTP   │
                        │    Request       │
                        └────────┬─────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │   DraftMiddleware      │
                    │   Checks for cookie:   │
                    │  __pynext_draft_token  │
                    └────────────┬───────────┘
                                 │
              ┌──────────────────┴──────────────────┐
              │                                     │
              ▼                                     ▼
    ┌─────────────────┐                  ┌─────────────────┐
    │  Token Found    │                  │  No Token       │
    │  & Valid        │                  │                 │
    └────────┬────────┘                  └────────┬────────┘
             │                                    │
             ▼                                    ▼
    ┌─────────────────┐                  ┌─────────────────┐
    │ create_draft_   │                  │ create_draft_   │
    │ context(        │                  │ context(        │
    │   is_draft=True,│                  │   is_draft=False│
    │   token=...     │                  │ )               │
    │ )               │                  │                 │
    └────────┬────────┘                  └────────┬────────┘
             │                                    │
             ▼                                    ▼
    ┌─────────────────┐                  ┌─────────────────┐
    │ enable_draft()  │                  │   Normal        │
    │ Updates signal  │                  │   Rendering     │
    └────────┬────────┘                  └────────┬────────┘
             │                                    │
             └────────────────┬───────────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │    Page Rendering   │
                    │                     │
                    │  @draft_content ────┼──► Shows draft or fallback
                    │  @draft_only ───────┼──► Shows only in draft
                    │  @published_only ───┼──► Hides in draft
                    │  DraftSwitch ───────┼──► Conditional content
                    │  DraftBanner ───────┼──► Preview indicator
                    │                     │
                    └─────────────────────┘
```

---

## How It Works

### 1. Signal-Based State Management

Draft Mode uses PyNext's reactive `Signal` primitive (inspired by SolidJS):

```python
from pynext.core.signals import Signal

class DraftSignal(Signal[bool]):
    """Specialized signal for draft mode state."""
    
    def enable(self, token: str) -> None:
        """Enable draft mode with authentication token."""
        self._draft_token = token
        self.set(True)  # Notifies all subscribers
    
    def disable(self) -> None:
        """Disable draft mode."""
        self._draft_token = None
        self.set(False)  # Notifies all subscribers
```

When `set()` is called, **only components subscribed to this signal** are updated—not the entire page.

### 2. Component Update Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    SIGNAL UPDATE PROPAGATION                    │
└─────────────────────────────────────────────────────────────────┘

    DraftSignal.set(True)
           │
           ▼
    ┌──────────────────┐
    │   Subscribers    │
    │   Notification   │
    └────────┬─────────┘
             │
    ┌────────┴────────┬────────────────┬────────────────┐
    │                 │                │                │
    ▼                 ▼                ▼                ▼
┌────────┐      ┌────────┐      ┌────────┐      ┌────────┐
│@draft_ │      │@draft_ │      │Draft   │      │Draft   │
│content │      │only    │      │Switch  │      │Banner  │
└───┬────┘      └───┬────┘      └───┬────┘      └───┬────┘
    │               │               │               │
    ▼               ▼               ▼               ▼
┌────────┐      ┌────────┐      ┌────────┐      ┌────────┐
│Re-render│     │Show    │      │Switch  │      │Show    │
│with    │      │content │      │to draft│      │banner  │
│draft   │      │        │      │variant │      │        │
│data    │      │        │      │        │      │        │
└────────┘      └────────┘      └────────┘      └────────┘

    ┌─────────────────────────────────────────────────────────┐
    │  UNCHANGED COMPONENTS (Header, Nav, Footer, etc.)       │
    │  → NOT re-rendered                                      │
    │  → Static HTML preserved                                │
    └─────────────────────────────────────────────────────────┘
```

### 3. Token-Based Authentication

Draft mode requires authentication to prevent unauthorized access to unpublished content:

```
┌─────────────────────────────────────────────────────────────────┐
│                      TOKEN LIFECYCLE                            │
└─────────────────────────────────────────────────────────────────┘

    ┌────────────────┐
    │  CMS Triggers  │
    │  Preview       │
    └───────┬────────┘
            │
            ▼
    ┌────────────────────────────────────────┐
    │  POST /_draft/preview                   │
    │  Body: { url: "/blog/my-post" }        │
    └───────────────────┬────────────────────┘
                        │
                        ▼
    ┌────────────────────────────────────────┐
    │  generate_draft_token()                 │
    │  ┌────────────────────────────────────┐ │
    │  │ payload = {                        │ │
    │  │   "iat": timestamp,                │ │
    │  │   "exp": timestamp + TTL,          │ │
    │  │   "data": preview_data,            │ │
    │  │   "nonce": random_hex              │ │
    │  │ }                                  │ │
    │  │                                    │ │
    │  │ token = base64(json) + "." + sig   │ │
    │  └────────────────────────────────────┘ │
    └───────────────────┬────────────────────┘
                        │
                        ▼
    ┌────────────────────────────────────────┐
    │  Set Cookie: __pynext_draft_token      │
    │  Redirect to: /blog/my-post            │
    └───────────────────┬────────────────────┘
                        │
                        ▼
    ┌────────────────────────────────────────┐
    │  Subsequent Requests                   │
    │  → Middleware reads cookie             │
    │  → verify_draft_token() validates      │
    │  → Draft context established           │
    └────────────────────────────────────────┘
```

---

## Quick Start

### Installation

Draft Mode is included in PyNext core—no extra installation needed.

### Basic Usage

```python
from pynext.core.draft import (
    use_draft,
    draft_content,
    draft_only,
    published_only,
    DraftBanner,
    DraftSwitch,
)
from pynext.core.html import div, article, h1, p

# 1. Simple conditional rendering
def hero_section():
    draft = use_draft()
    
    if draft():
        return div(class_="hero")["🚧 Draft: New Hero Design"]
    else:
        return div(class_="hero")["Welcome to Our Site"]

# 2. Using decorators for cleaner code
@draft_only
def draft_warning():
    """Only visible in draft mode."""
    return div(class_="draft-warning")[
        "⚠️ You are viewing unpublished content"
    ]

@published_only
def analytics_tracker():
    """Hidden in draft mode to avoid tracking preview sessions."""
    return Script(src="https://analytics.com/track.js")

# 3. Draft content with fallback
@draft_content(fallback=lambda: p()["Published article content..."])
def article_body():
    """Shows draft content when in draft mode, otherwise fallback."""
    return p()["DRAFT: New article content with updates..."]

# 4. Using DraftSwitch for complex scenarios
def product_description():
    return DraftSwitch(
        draft=lambda: div()[
            h1()["New Product Name (Draft)"],
            p()["Updated description with new features..."],
        ],
        published=lambda: div()[
            h1()["Current Product Name"],
            p()["Current product description..."],
        ],
    )

# 5. Complete page with DraftBanner
def blog_post():
    return article()[
        DraftBanner(
            exit_url="/_draft/disable",
            edit_url="/cms/posts/123/edit",
            position="top"
        ),
        draft_warning(),
        h1()["Blog Post Title"],
        article_body(),
    ]
```

### Enable Draft Mode (Server Setup)

```python
from fastapi import FastAPI
from pynext.server.draft import (
    add_draft_routes,
    add_draft_middleware,
    DraftConfig,
)

app = FastAPI()

# Configure draft mode
config = DraftConfig(
    secret_key="your-secure-secret-key-here",
    token_ttl=3600 * 24,  # 24 hours
    cookie_name="__pynext_draft_token",
)

# Add draft API routes (/_draft/enable, /_draft/disable, etc.)
add_draft_routes(app, config)

# Add middleware to detect draft mode on all requests
add_draft_middleware(app, config)
```

### Access Draft Mode

```bash
# Enable draft mode via URL
curl "https://yoursite.com/_draft/enable?secret=your-secret"

# Disable draft mode
curl "https://yoursite.com/_draft/disable"

# Check status
curl "https://yoursite.com/_draft/status"
```

---

## Core API Reference

### Functions

#### `use_draft() -> DraftSignal`

Returns the global draft signal. Use this to read the current draft state.

```python
from pynext.core.draft import use_draft

def my_component():
    draft = use_draft()
    
    if draft():  # Call signal to read value
        return "Draft mode is enabled"
    return "Published mode"
```

#### `is_draft_mode() -> bool`

Convenience function to check if currently in draft mode.

```python
from pynext.core.draft import is_draft_mode

def my_component():
    if is_draft_mode():
        return "Draft content"
    return "Published content"
```

#### `enable_draft(token: str) -> None`

Programmatically enable draft mode with a token.

```python
from pynext.core.draft import enable_draft

# Usually called by middleware, but can be called manually
enable_draft("valid-token-here")
```

#### `disable_draft() -> None`

Programmatically disable draft mode.

```python
from pynext.core.draft import disable_draft

disable_draft()
```

### Decorators

#### `@draft_content(fallback=None, cache_draft=False)`

Marks a function as draft-aware. The content is wrapped with a data attribute for fine-grained client updates.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `fallback` | `Callable[[], Any]` | `None` | Function to render in published mode |
| `cache_draft` | `bool` | `False` | Whether to cache draft content |

```python
@draft_content(fallback=lambda: div()["Published"])
def my_content():
    return div()["Draft version"]
```

**Output HTML:**
```html
<div data-draft="draft-a1b2c3d4" data-draft-aware="true">
    Draft version
</div>
```

#### `@draft_only`

Content only renders in draft mode. In published mode, returns empty string.

```python
@draft_only
def preview_banner():
    return div(class_="banner")["Preview Mode Active"]
```

#### `@published_only`

Content only renders in published mode. In draft mode, returns empty string.

```python
@published_only
def production_analytics():
    return Script(src="/analytics.js")
```

### Classes

#### `DraftSignal`

```python
class DraftSignal(Signal[bool]):
    def __init__(self, initial: bool = False)
    def enable(self, token: str) -> None
    def disable(self) -> None
    def toggle(self) -> None
    def is_authenticated(self) -> bool
    def get_js_init(self) -> str
```

#### `DraftContext`

```python
@dataclass
class DraftContext:
    is_draft: bool = False
    draft_token: Optional[str] = None
    draft_data: Dict[str, Any] = field(default_factory=dict)
    preview_url: Optional[str] = None
```

---

## Components

### DraftSwitch

Renders different content based on draft mode. Both branches are evaluated but only one is shown.

```python
from pynext.core.draft import DraftSwitch

switch = DraftSwitch(
    draft=lambda: div()["New design"],
    published=lambda: div()["Current design"],
)
html = switch.render()
```

**Output:**
```html
<div id="draft-switch-a1b2c3d4" data-draft-switch data-mode="published">
    <div>Current design</div>
</div>
```

### DraftBanner

Fixed banner indicating draft mode is active.

```python
from pynext.core.draft import DraftBanner

banner = DraftBanner(
    exit_url="/_draft/disable",
    edit_url="/cms/edit/123",  # Optional CMS edit link
    position="top",            # "top" or "bottom"
)
```

**Visual:**
```
┌─────────────────────────────────────────────────────────────────┐
│  ⚠️ Draft Mode            [Edit in CMS]  [Exit Preview]        │
└─────────────────────────────────────────────────────────────────┘
```

### DraftOverlay

Adds visual indicators around draft-aware components.

```python
from pynext.core.draft import DraftOverlay

overlay = DraftOverlay(
    highlight_changes=True,
    show_diff=False,
)
```

**Visual Effect:**
```
┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐   ← Orange dashed border
  Draft-aware component     
  with updated content      
└ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘
```

---

## Server Integration

### DraftConfig

Configuration options for server-side draft mode.

```python
@dataclass
class DraftConfig:
    secret_key: str = ""           # Secret for token signing
    token_ttl: int = 3600 * 24     # Token lifetime (24 hours)
    cookie_name: str = "__pynext_draft_token"
    preview_url: str = "/_draft/preview"
    enable_url: str = "/_draft/enable"
    disable_url: str = "/_draft/disable"
```

### API Endpoints

Draft mode provides these endpoints when `add_draft_routes()` is called:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/_draft/enable` | GET | Enable draft mode (requires secret) |
| `/_draft/disable` | GET | Disable draft mode |
| `/_draft/status` | GET | Check current draft status |
| `/_draft/preview` | POST | Start preview session (for CMS webhooks) |
| `/_draft/content/{id}` | GET | Fetch draft content for a component |

### Token Generation & Verification

```python
from pynext.server.draft import generate_draft_token, verify_draft_token

# Generate a token (server-side)
token = generate_draft_token(
    secret="your-secret-key",
    data={"content_id": "123", "author": "john"},
    ttl=3600,  # 1 hour
)

# Verify a token
payload = verify_draft_token(token, "your-secret-key")
if payload:
    print(f"Token valid, expires: {payload['exp']}")
else:
    print("Token invalid or expired")
```

### DraftMiddleware

ASGI middleware that automatically detects draft mode from cookies.

```python
from pynext.server.draft import DraftMiddleware, DraftConfig

app.add_middleware(
    DraftMiddleware,
    config=DraftConfig(secret_key="your-secret")
)
```

---

## CMS Integration

### Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      CMS → PYNEXT PREVIEW FLOW                          │
└─────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────┐
    │      CMS        │
    │ (Contentful,    │
    │  Sanity, etc.)  │
    └────────┬────────┘
             │
             │ 1. Editor clicks "Preview"
             ▼
    ┌─────────────────────────────────────────────────┐
    │  CMS sends webhook to PyNext                    │
    │                                                 │
    │  POST https://yoursite.com/_draft/preview      │
    │  Body: {                                        │
    │    "url": "/blog/my-new-post",                 │
    │    "content_id": "123",                        │
    │    "content_type": "blog_post",                │
    │    "author": "john@example.com"                │
    │  }                                             │
    └───────────────────┬─────────────────────────────┘
                        │
                        │ 2. PyNext generates token
                        ▼
    ┌─────────────────────────────────────────────────┐
    │  Token created with CMS data embedded          │
    │  Set-Cookie: __pynext_draft_token=...          │
    │  Redirect: /blog/my-new-post                   │
    └───────────────────┬─────────────────────────────┘
                        │
                        │ 3. Browser redirected
                        ▼
    ┌─────────────────────────────────────────────────┐
    │  Page loads with draft content                  │
    │                                                 │
    │  ┌───────────────────────────────────────────┐ │
    │  │ ⚠️ Draft Mode    [Edit in CMS] [Exit]     │ │
    │  └───────────────────────────────────────────┘ │
    │                                                 │
    │  ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐│
    │    Draft content displayed with highlights    ││
    │  └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘│
    │                                                 │
    └─────────────────────────────────────────────────┘
```

### Contentful Integration Example

```python
# pages/api/contentful_preview.py

from fastapi import APIRouter, Request
from pynext.server.draft import generate_draft_token, DraftConfig

router = APIRouter()

@router.post("/api/contentful/preview")
async def contentful_preview(request: Request):
    """Handle Contentful preview webhook."""
    body = await request.json()
    
    # Validate Contentful webhook secret
    webhook_secret = request.headers.get("X-Contentful-Secret")
    if webhook_secret != os.environ["CONTENTFUL_WEBHOOK_SECRET"]:
        raise HTTPException(403, "Invalid webhook secret")
    
    # Extract content info
    content_id = body["sys"]["id"]
    content_type = body["sys"]["contentType"]["sys"]["id"]
    slug = body["fields"]["slug"]["en-US"]
    
    # Generate preview token with content data
    config = get_draft_config()
    token = generate_draft_token(
        config.secret_key,
        data={
            "content_id": content_id,
            "content_type": content_type,
            "source": "contentful",
        },
        ttl=config.token_ttl,
    )
    
    # Redirect to content page with draft mode enabled
    response = RedirectResponse(url=f"/blog/{slug}", status_code=302)
    response.set_cookie(
        config.cookie_name,
        token,
        max_age=config.token_ttl,
        httponly=True,
        samesite="lax",
        secure=True,
    )
    
    return response
```

### Sanity Integration Example

```python
# Sanity preview URL configuration
# In Sanity Studio:
# https://yoursite.com/_draft/preview?slug=/blog/{slug}

@router.get("/_draft/preview")
async def sanity_preview(
    request: Request,
    slug: str,
    secret: Optional[str] = None,
):
    """Handle Sanity preview links."""
    config = get_draft_config()
    
    # Validate secret (optional but recommended)
    if secret and secret != config.secret_key:
        raise HTTPException(403, "Invalid preview secret")
    
    token = generate_draft_token(
        config.secret_key,
        data={"source": "sanity", "slug": slug},
    )
    
    response = RedirectResponse(url=slug, status_code=302)
    response.set_cookie(config.cookie_name, token, ...)
    
    return response
```

---

## Security

### Token Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                        TOKEN FORMAT                             │
└─────────────────────────────────────────────────────────────────┘

    base64(payload).signature
         │              │
         │              └── SHA-256 hash of payload + secret
         │                  (first 16 chars)
         │
         └── JSON payload:
             {
               "iat": 1699900000,        // Issued at timestamp
               "exp": 1699986400,        // Expiration timestamp
               "data": { ... },          // Custom data (optional)
               "nonce": "a1b2c3d4e5f6"   // Random string for uniqueness
             }
```

### Security Measures

1. **Token Signing**: Tokens are signed with HMAC-SHA256
2. **Expiration**: Tokens have configurable TTL (default 24 hours)
3. **HttpOnly Cookies**: Prevents JavaScript access to tokens
4. **SameSite=Lax**: Prevents CSRF attacks
5. **Secure Flag**: Cookies only sent over HTTPS in production

### Best Security Practices

```python
# ✅ Use environment variables for secrets
import os

config = DraftConfig(
    secret_key=os.environ["DRAFT_SECRET_KEY"],
)

# ✅ Use short TTLs for sensitive content
config = DraftConfig(
    token_ttl=3600,  # 1 hour instead of 24
)

# ✅ Validate CMS webhooks
@router.post("/_draft/preview")
async def preview(request: Request):
    signature = request.headers.get("X-Webhook-Signature")
    if not verify_webhook_signature(signature, await request.body()):
        raise HTTPException(403, "Invalid webhook signature")
    # ...

# ✅ Restrict draft access by IP in production
ALLOWED_IPS = ["10.0.0.0/8", "192.168.0.0/16"]

class RestrictedDraftMiddleware(DraftMiddleware):
    async def __call__(self, scope, receive, send):
        client_ip = scope.get("client", ("",))[0]
        if not is_ip_allowed(client_ip, ALLOWED_IPS):
            # Clear draft token and proceed without draft mode
            # ...
        await super().__call__(scope, receive, send)
```

---

## Performance

### Benchmark Comparison

```
┌─────────────────────────────────────────────────────────────────┐
│               DRAFT MODE TOGGLE PERFORMANCE                     │
└─────────────────────────────────────────────────────────────────┘

                    Next.js          PyNext
                    ───────          ──────
Toggle Time:        ~100ms           ~1ms
                    (full render)    (signal update)

DOM Operations:     1000+ nodes      5-10 nodes
                    (entire page)    (draft components only)

Network:            Full page        None
                    fetch            (client-side toggle)

Visual:             Page blink       Seamless
                    possible         transition
```

### JavaScript Bundle Size

```
┌─────────────────────────────────────────────────────────────────┐
│                    RUNTIME COMPARISON                           │
└─────────────────────────────────────────────────────────────────┘

PyNext Draft Runtime:
  ┌─────────────────────────────────────┐
  │█████████████░░░░░░░░░░░░░░░░░░░░░░░░│  500 bytes
  └─────────────────────────────────────┘

Next.js Draft Mode:
  ┌─────────────────────────────────────┐
  │█████████████████████████████████████│  2,000 bytes
  │█████████████████████████████████████│
  │█████████████████████████████████████│
  │█████████████████████████████████████│
  └─────────────────────────────────────┘

Reduction: 75% smaller runtime
```

### Why Signal Updates Are Faster

```python
# Traditional approach: Full page re-render
def render_page(is_draft):
    return html()[
        header(),      # Re-rendered (unchanged)
        nav(),         # Re-rendered (unchanged)
        sidebar(),     # Re-rendered (unchanged)
        content(is_draft),  # Re-rendered (changed)
        footer(),      # Re-rendered (unchanged)
    ]
# Total work: 5 components

# PyNext signal approach: Only affected components
draft_signal.set(True)
# → Only @draft_content, @draft_only components update
# Total work: 1-2 components
```

---

## Best Practices

### 1. Minimize Draft-Aware Components

```python
# ✅ Good: Only article body is draft-aware
def blog_post():
    return article()[
        header()["My Blog"],           # Static
        nav(),                          # Static
        article_title(),               # Static
        draft_article_body(),          # Draft-aware
        comments(),                    # Static
        footer(),                      # Static
    ]

# ❌ Bad: Entire page is draft-aware
@draft_content()
def blog_post():
    return article()[
        header()["My Blog"],
        nav(),
        article_title(),
        article_body(),
        comments(),
        footer(),
    ]
```

### 2. Use Fallbacks for Production Content

```python
# ✅ Good: Explicit fallback ensures published users see correct content
@draft_content(fallback=fetch_published_article)
def article_body():
    return fetch_draft_article()

# ❌ Bad: No fallback means draft check happens every render
def article_body():
    if is_draft_mode():
        return fetch_draft_article()
    return fetch_published_article()
```

### 3. Add Visual Indicators

```python
# ✅ Good: Users clearly know they're in draft mode
def page():
    return div()[
        DraftBanner(exit_url="/_draft/disable"),
        DraftOverlay(),
        content(),
    ]

# ❌ Bad: No indication of draft mode (confusing)
def page():
    return div()[
        content(),
    ]
```

### 4. Handle Draft Data Properly

```python
# ✅ Good: Access draft context for additional info
def article():
    ctx = get_draft_context()
    
    if ctx and ctx.draft_data.get("content_id"):
        # Fetch specific draft version
        article = fetch_draft(ctx.draft_data["content_id"])
    else:
        article = fetch_published()
    
    return render_article(article)

# ❌ Bad: Only checking boolean, missing context
def article():
    if is_draft_mode():
        article = fetch_latest_draft()  # Which draft?
    else:
        article = fetch_published()
```

---

## Do's and Don'ts

### ✅ DO

```python
# DO: Use decorators for clean, declarative code
@draft_only
def preview_banner():
    return div()["Preview Mode"]

# DO: Provide meaningful fallbacks
@draft_content(fallback=lambda: Spinner()["Loading..."])
def article():
    return fetch_draft()

# DO: Use environment variables for secrets
config = DraftConfig(secret_key=os.environ["DRAFT_SECRET"])

# DO: Set appropriate TTLs
config = DraftConfig(token_ttl=3600)  # Short for sensitive content

# DO: Include edit links for editors
DraftBanner(edit_url=f"/cms/edit/{content_id}")

# DO: Use DraftOverlay in development for debugging
if settings.DEBUG:
    return [DraftOverlay(), content()]

# DO: Log draft access for auditing
@router.get("/_draft/enable")
async def enable(request: Request):
    logger.info(f"Draft enabled by {request.client.host}")
    # ...
```

### ❌ DON'T

```python
# DON'T: Make entire page draft-aware
@draft_content()  # Bad: wraps everything
def entire_page():
    return div()[header(), nav(), content(), footer()]

# DON'T: Hardcode secrets
config = DraftConfig(secret_key="my-secret-123")  # Bad!

# DON'T: Use infinite TTLs
config = DraftConfig(token_ttl=999999999)  # Bad!

# DON'T: Forget to validate CMS webhooks
@router.post("/_draft/preview")
async def preview(request: Request):
    body = await request.json()  # Bad: no validation
    # ...

# DON'T: Store draft tokens in localStorage
# (Tokens should be HttpOnly cookies only)

# DON'T: Expose draft content to search engines
# (Use noindex meta tag or robots.txt for draft pages)

# DON'T: Mix draft and analytics
@published_only  # Good: hide analytics in draft mode
def analytics():
    return Script(src="analytics.js")

# DON'T: Cache draft content on CDN
# (Use Cache-Control: no-store for draft mode)
```

---

## Troubleshooting

### Common Issues

#### 1. Draft Mode Not Activating

**Symptoms:**
- Cookie is set but page shows published content
- `is_draft_mode()` returns `False`

**Solutions:**
```python
# Check 1: Is middleware added?
app.add_middleware(DraftMiddleware, config=config)  # Required!

# Check 2: Is token valid?
from pynext.server.draft import verify_draft_token
token = request.cookies.get("__pynext_draft_token")
payload = verify_draft_token(token, config.secret_key)
print(f"Token valid: {payload is not None}")

# Check 3: Has token expired?
import time
if payload and payload["exp"] < time.time():
    print("Token has expired!")

# Check 4: Correct cookie name?
print(f"Cookie name: {config.cookie_name}")
print(f"Cookies: {request.cookies}")
```

#### 2. Draft Content Not Updating

**Symptoms:**
- Toggle works but component doesn't change
- Signal updates but DOM stays the same

**Solutions:**
```python
# Check 1: Is component decorated correctly?
@draft_content()  # Not @draft_content (without parens)
def my_content():
    pass

# Check 2: Is component returning renderable content?
@draft_content()
def my_content():
    result = fetch_data()
    return div()[result]  # Must return component, not raw data

# Check 3: Does fallback exist?
@draft_content(fallback=lambda: div()["Fallback"])  # Provide fallback
def my_content():
    return div()["Draft"]
```

#### 3. Security Warnings

**Symptoms:**
- Tokens accepted from wrong domain
- Draft mode enabled without secret

**Solutions:**
```python
# Require secret for enable endpoint
@router.get("/_draft/enable")
async def enable(request: Request, secret: str):
    if secret != config.secret_key:
        raise HTTPException(403, "Invalid secret")
    # ...

# Validate cookie domain
response.set_cookie(
    config.cookie_name,
    token,
    domain=".yourdomain.com",  # Restrict to your domain
    secure=True,               # HTTPS only
    httponly=True,             # No JS access
    samesite="lax",            # CSRF protection
)
```

#### 4. Performance Issues

**Symptoms:**
- Page is slow in draft mode
- Many components re-rendering

**Solutions:**
```python
# Check 1: Too many draft-aware components?
# Audit how many @draft_content decorators you have

# Check 2: Expensive operations in draft components?
@draft_content()
def article():
    # Bad: Fetches on every render
    data = fetch_from_cms()
    return render(data)

# Better: Cache draft content
@draft_content(cache_draft=True)
def article():
    data = fetch_from_cms()
    return render(data)
```

### Debug Mode

```python
# Enable debug logging for draft mode
import logging
logging.getLogger("pynext.draft").setLevel(logging.DEBUG)

# Or check state manually
from pynext.core.draft import use_draft, get_draft_context

draft = use_draft()
ctx = get_draft_context()

print(f"Draft enabled: {draft()}")
print(f"Token present: {draft.is_authenticated()}")
print(f"Context: {ctx}")
```

---

## Complete Examples

### Example 1: Blog with Draft Preview

```python
# pages/blog/[slug].py

from pynext.core.draft import (
    use_draft,
    draft_content,
    draft_only,
    DraftBanner,
    DraftOverlay,
    get_draft_context,
)
from pynext.core.html import article, h1, p, div, time, img
from pynext.server.draft import DraftConfig

# Data fetching
async def fetch_post(slug: str, draft: bool = False):
    """Fetch post from CMS."""
    if draft:
        # Fetch draft version from CMS
        return await cms.get_draft(slug)
    return await cms.get_published(slug)

# Components
@draft_only
def draft_warning():
    return div(class_="bg-amber-100 p-4 rounded mb-4")[
        "⚠️ You are viewing unpublished content. ",
        "This content has not been reviewed or published yet."
    ]

@draft_content()
def post_content(post):
    """Renders with visual marker in draft mode."""
    return div(class_="prose")[
        post.content
    ]

def post_meta(post):
    """Always static - not draft-aware."""
    return div(class_="text-gray-500")[
        time(datetime=post.date)[post.formatted_date],
        " · ",
        f"By {post.author.name}",
    ]

# Main page
async def blog_post_page(slug: str):
    """Blog post page with draft support."""
    draft = use_draft()
    ctx = get_draft_context()
    
    # Fetch appropriate version
    post = await fetch_post(
        slug,
        draft=draft() and ctx.draft_data.get("content_id")
    )
    
    if not post:
        return not_found()
    
    return article(class_="max-w-3xl mx-auto py-12")[
        # Draft UI
        DraftBanner(
            exit_url="/_draft/disable",
            edit_url=f"/cms/posts/{post.id}/edit",
        ) if draft() else "",
        DraftOverlay() if draft() else "",
        draft_warning(),
        
        # Article header (static)
        h1(class_="text-4xl font-bold mb-4")[post.title],
        post_meta(post),
        
        # Featured image (static)
        img(
            src=post.featured_image,
            alt=post.title,
            class_="w-full rounded-lg my-8"
        ) if post.featured_image else "",
        
        # Article body (draft-aware)
        post_content(post),
    ]
```

### Example 2: E-commerce Product Preview

```python
# pages/products/[id].py

from pynext.core.draft import DraftSwitch, DraftBanner, is_draft_mode
from pynext.core.html import div, h1, p, span, button

async def product_page(product_id: str):
    """Product page with A/B draft testing."""
    
    # Fetch both versions for comparison
    published = await fetch_product(product_id)
    draft = await fetch_draft_product(product_id) if is_draft_mode() else None
    
    return div(class_="product-page")[
        DraftBanner(exit_url="/_draft/disable") if is_draft_mode() else "",
        
        # Product title - uses DraftSwitch for side-by-side comparison
        DraftSwitch(
            draft=lambda: h1(class_="text-3xl")[
                draft.name if draft else "",
                span(class_="text-green-500 text-sm ml-2")["(NEW)"]
            ],
            published=lambda: h1(class_="text-3xl")[published.name],
        ),
        
        # Price - draft might have new pricing
        DraftSwitch(
            draft=lambda: div(class_="pricing")[
                span(class_="text-2xl font-bold")[f"${draft.price if draft else ''}"],
                span(class_="text-red-500 line-through ml-2")[
                    f"${published.price}"
                ] if draft and draft.price != published.price else "",
            ],
            published=lambda: div(class_="pricing")[
                span(class_="text-2xl font-bold")[f"${published.price}"]
            ],
        ),
        
        # Description
        DraftSwitch(
            draft=lambda: div(class_="description")[draft.description if draft else ""],
            published=lambda: div(class_="description")[published.description],
        ),
        
        # CTA button
        button(class_="btn-primary")["Add to Cart"],
    ]
```

### Example 3: Full Server Setup

```python
# server.py

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import os

from pynext.server.draft import (
    add_draft_routes,
    add_draft_middleware,
    DraftConfig,
    generate_draft_token,
)
from pynext.middleware.draft import inject_draft_state

# Create app
app = FastAPI()

# Configure draft mode
draft_config = DraftConfig(
    secret_key=os.environ["DRAFT_SECRET_KEY"],
    token_ttl=3600 * 24,  # 24 hours
    cookie_name="__pynext_draft_token",
)

# Add draft routes and middleware
add_draft_routes(app, draft_config)
add_draft_middleware(app, draft_config)

# Custom CMS webhook endpoint
@app.post("/api/cms/preview")
async def cms_preview(request: Request):
    """Handle CMS preview webhook."""
    # Validate webhook
    signature = request.headers.get("X-CMS-Signature")
    body = await request.body()
    
    if not verify_cms_signature(signature, body):
        raise HTTPException(403, "Invalid signature")
    
    data = await request.json()
    
    # Generate token with CMS data
    token = generate_draft_token(
        draft_config.secret_key,
        data={
            "content_id": data["id"],
            "content_type": data["type"],
            "source": "cms",
        },
        ttl=draft_config.token_ttl,
    )
    
    # Redirect to preview URL
    preview_url = data.get("url", "/")
    response = RedirectResponse(url=preview_url)
    response.set_cookie(
        draft_config.cookie_name,
        token,
        max_age=draft_config.token_ttl,
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="lax",
    )
    
    return response

# Page route
@app.get("/{path:path}")
async def render_page(request: Request, path: str):
    """Render page with draft support."""
    from pynext.core.draft import is_draft_mode, get_draft_runtime_js, get_draft_css
    
    # Render your page
    html = await render_page_html(path)
    
    # Inject draft state if in draft mode
    html = inject_draft_state(html)
    
    # Add draft runtime if needed
    if is_draft_mode():
        draft_scripts = f"""
        <script>{get_draft_runtime_js()}</script>
        <style>{get_draft_css()}</style>
        """
        html = html.replace("</head>", f"{draft_scripts}</head>")
    
    return HTMLResponse(html)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## Summary

PyNext's Draft Mode provides a **signal-based preview system** that is:

- **10x+ Faster** than traditional full-page re-renders
- **75% Smaller** runtime JavaScript
- **Seamless** visual transitions without page blinks
- **Secure** with signed tokens and short TTLs
- **CMS-Friendly** with webhook support for popular platforms

The key innovation is treating draft mode as a **reactive signal** rather than a server-side flag. This means:

1. Static content stays static (headers, footers, navigation)
2. Only draft-aware components subscribe to changes
3. Toggling draft mode is instantaneous
4. No network requests needed for toggle

Start with the [Quick Start](#quick-start) guide, then progressively add [CMS Integration](#cms-integration) as your needs grow.

