# State and Data Integration in PyNext

This guide explains how PyNext's reactive state system (Signals, Stores) integrates with data fetching mechanisms (Server Actions, API Routes). Understanding this connection is **critical** for building data-driven applications.

## Table of Contents

- [Overview](#overview)
- [The Signal-First Architecture](#the-signal-first-architecture)
- [Pattern 1: Server Actions + Signals](#pattern-1-server-actions--signals)
- [Pattern 2: API Routes + Signals](#pattern-2-api-routes--signals)
- [Pattern 3: Combined Approach](#pattern-3-combined-approach)
- [Complete Data Flow](#complete-data-flow)
- [Common Patterns](#common-patterns)
- [Best Practices](#best-practices)
- [Quick Reference](#quick-reference)
- [Troubleshooting](#troubleshooting)

---

## Overview

### The Core Principle

In PyNext, **Signals are the single source of truth for UI state**. Data fetching (via Server Actions or API Routes) always flows through Signals to update the UI:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        STATE + DATA FETCHING FLOW                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌────────────────┐     ┌────────────────┐     ┌────────────────┐         │
│   │    SIGNALS     │     │ SERVER ACTIONS │     │   API ROUTES   │         │
│   │  (Client State)│     │  (PyNext RPC)  │     │  (REST API)    │         │
│   └───────┬────────┘     └───────┬────────┘     └───────┬────────┘         │
│           │                      │                      │                   │
│           │    Direct binding    │    fetch() call      │                   │
│           │◀─────────────────────│◀─────────────────────│                   │
│           │                      │                      │                   │
│           ▼                      ▼                      ▼                   │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │                         UI UPDATES                               │      │
│   │  Signal changes → DOM updates automatically (fine-grained)       │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Insight

> **Signals are always the UI truth.** Regardless of where data comes from (Server Actions, API Routes, WebSockets), updating a Signal automatically updates all subscribed DOM nodes without manual intervention.

### Comparison Table

| Data Source | Best For | State Update Method | Latency |
|-------------|----------|---------------------|---------|
| Server Actions | Internal PyNext apps | `signal.set(result)` | ~50-200ms |
| API Routes | External clients, REST | `fetch()` → `signal.set()` | ~50-200ms |
| WebSocket | Real-time data | `onmessage` → `signal.set()` | ~10-50ms |
| Local computation | Derived values | `Computed` | ~0.1ms |

---

## The Signal-First Architecture

### What It Means

All UI state flows through Signals. This creates a predictable, unidirectional data flow:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      SIGNAL-FIRST ARCHITECTURE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   DATA SOURCES                    SIGNALS                   UI              │
│   ────────────                    ───────                   ──              │
│                                                                              │
│   ┌─────────────┐                                                            │
│   │ Server      │───┐                                                        │
│   │ Actions     │   │         ┌──────────────┐        ┌──────────────┐      │
│   └─────────────┘   │         │              │        │              │      │
│                     ├────────▶│   Signal     │───────▶│  DOM Node    │      │
│   ┌─────────────┐   │         │              │        │              │      │
│   │ API Routes  │───┤         └──────────────┘        └──────────────┘      │
│   └─────────────┘   │                │                       ▲              │
│                     │                │                       │              │
│   ┌─────────────┐   │                ▼                       │              │
│   │ WebSocket   │───┤         ┌──────────────┐        ┌──────────────┐      │
│   └─────────────┘   │         │              │        │              │      │
│                     ├────────▶│   Signal     │───────▶│  DOM Node    │      │
│   ┌─────────────┐   │         │              │        │              │      │
│   │ Local       │───┘         └──────────────┘        └──────────────┘      │
│   │ Events      │                    │                       ▲              │
│   └─────────────┘                    │                       │              │
│                                      ▼                       │              │
│                               ┌──────────────┐        ┌──────────────┐      │
│                               │   Computed   │───────▶│  DOM Node    │      │
│                               │   (derived)  │        │              │      │
│                               └──────────────┘        └──────────────┘      │
│                                                                              │
│   All data flows through Signals → Automatic UI synchronization             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Benefits

1. **Single Source of Truth** - UI always reflects Signal state
2. **Automatic Updates** - No manual DOM manipulation
3. **Predictable** - Clear data flow, easy to debug
4. **Performant** - Fine-grained updates, no re-renders

---

## Pattern 1: Server Actions + Signals

This is the **recommended pattern** for PyNext applications. Server Actions provide seamless Python-to-JavaScript communication, and Signals handle all UI updates.

### Basic Pattern

```python
from pynext import Signal, server_action, page, div, button, ul, li, span

# ============================================================
# STATE LAYER - Define Signals
# ============================================================

users = Signal([])           # Data signal
loading = Signal(False)      # Loading state
error = Signal(None)         # Error state

# ============================================================
# DATA LAYER - Define Server Actions
# ============================================================

@server_action
async def fetch_users():
    """Fetch all users from database."""
    import asyncpg
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        rows = await conn.fetch("SELECT * FROM users ORDER BY created_at DESC")
        return [dict(r) for r in rows]
    finally:
        await conn.close()

@server_action
async def create_user(name: str, email: str):
    """Create a new user."""
    import asyncpg
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        user = await conn.fetchrow(
            "INSERT INTO users (name, email) VALUES ($1, $2) RETURNING *",
            name, email
        )
        return dict(user)
    finally:
        await conn.close()

@server_action
async def delete_user(user_id: int):
    """Delete a user by ID."""
    import asyncpg
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute("DELETE FROM users WHERE id = $1", user_id)
        return {"deleted": user_id}
    finally:
        await conn.close()

# ============================================================
# UI LAYER - Page Component
# ============================================================

@page
def users_page():
    # Handler: Load users
    async def load_users():
        loading.set(True)
        error.set(None)
        try:
            result = await fetch_users()
            users.set(result)  # ← Signal update triggers UI refresh
        except Exception as e:
            error.set(str(e))
        finally:
            loading.set(False)
    
    # Handler: Add new user
    async def add_user(name: str, email: str):
        loading.set(True)
        try:
            new_user = await create_user(name, email)
            users.update(lambda u: u + [new_user])  # ← Append to signal
        except Exception as e:
            error.set(str(e))
        finally:
            loading.set(False)
    
    # Handler: Remove user
    async def remove_user(user_id: int):
        try:
            await delete_user(user_id)
            users.update(lambda u: [x for x in u if x["id"] != user_id])
        except Exception as e:
            error.set(str(e))
    
    # UI - Reactively bound to Signals
    return div(class_="users-page")[
        h1()["User Management"],
        
        # Actions
        div(class_="actions")[
            button(onclick=load_users, disabled=loading)["Load Users"],
            button(onclick=lambda: add_user("New User", "new@example.com"))["Add User"],
        ],
        
        # Loading state - shows/hides based on Signal
        loading() and div(class_="loading")[
            span(class_="spinner")[""],
            "Loading..."
        ],
        
        # Error state - shows/hides based on Signal
        error() and div(class_="error")[
            strong()["Error: "],
            error(),
            button(onclick=lambda: error.set(None))["Dismiss"]
        ],
        
        # User list - auto-updates when users Signal changes
        ul(class_="user-list")[
            [
                li(key=user["id"])[
                    span()[user["name"]],
                    span(class_="email")[user["email"]],
                    button(onclick=lambda u=user: remove_user(u["id"]))["Delete"]
                ]
                for user in users()
            ]
        ],
        
        # Summary - Computed from Signal
        div(class_="summary")[
            f"Total: {len(users())} users"
        ]
    ]
```

### Data Flow Visualization

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SERVER ACTIONS + SIGNALS FLOW                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   1. USER ACTION                                                             │
│      └── Click "Load Users" button                                          │
│                    │                                                         │
│                    ▼                                                         │
│   2. SET LOADING STATE                                                       │
│      └── loading.set(True)  ───────▶  UI shows spinner                      │
│                    │                                                         │
│                    ▼                                                         │
│   3. CALL SERVER ACTION                                                      │
│      └── POST /_pynext/action                                               │
│          {                                                                   │
│            "actionId": "fetch_users",                                        │
│            "args": {}                                                        │
│          }                                                                   │
│                    │                                                         │
│                    ▼                                                         │
│   4. PYTHON EXECUTES ON SERVER                                              │
│      └── async def fetch_users():                                           │
│          │   conn = await asyncpg.connect(...)                              │
│          │   rows = await conn.fetch("SELECT * FROM users")                 │
│          │   return [dict(r) for r in rows]                                 │
│          │                                                                   │
│          ▼                                                                   │
│   5. RETURN RESULT                                                           │
│      └── {"data": [{"id": 1, "name": "Alice"}, ...]}                        │
│                    │                                                         │
│                    ▼                                                         │
│   6. UPDATE SIGNALS                                                          │
│      ├── users.set(result)  ───────▶  ul updates with new list items        │
│      └── loading.set(False) ───────▶  UI hides spinner                      │
│                                                                              │
│   Total time: ~50-200ms (network + DB query)                                │
│   UI updates: Automatic, fine-grained                                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Pattern 2: API Routes + Signals

Use this pattern when:
- External clients need to access your API
- You're integrating with third-party services
- You need RESTful semantics
- Mobile apps or other frontends consume your API

### Basic Pattern

```python
# ============================================================
# API ROUTE: pages/api/posts/route.py
# ============================================================

from pynext import api_route, JSONResponse
from pynext.router import get_query
import asyncpg

@api_route
async def GET(request):
    """GET /api/posts - List posts with pagination."""
    query = get_query()
    page = int(query.get("page", 1))
    limit = int(query.get("limit", 10))
    offset = (page - 1) * limit
    
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        rows = await conn.fetch(
            "SELECT * FROM posts ORDER BY created_at DESC LIMIT $1 OFFSET $2",
            limit, offset
        )
        total = await conn.fetchval("SELECT COUNT(*) FROM posts")
        
        return {
            "posts": [dict(r) for r in rows],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }
    finally:
        await conn.close()

@api_route
async def POST(request):
    """POST /api/posts - Create a new post."""
    data = await request.json()
    
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        post = await conn.fetchrow(
            "INSERT INTO posts (title, content) VALUES ($1, $2) RETURNING *",
            data["title"], data["content"]
        )
        return JSONResponse({"post": dict(post)}, status_code=201)
    finally:
        await conn.close()
```

```python
# ============================================================
# PAGE COMPONENT: pages/blog.py
# ============================================================

from pynext import Signal, Computed, page, div, button, ul, li, h1, script

# State
posts = Signal([])
pagination = Signal({"page": 1, "total": 0, "pages": 0})
loading = Signal(False)
error = Signal(None)

# Derived state
has_next = Computed(lambda: pagination()["page"] < pagination()["pages"])
has_prev = Computed(lambda: pagination()["page"] > 1)

@page
def blog():
    return div(class_="blog")[
        h1()["Blog Posts"],
        
        # Post list
        div(id="posts-container")[
            loading() and div(class_="loading")["Loading..."],
            error() and div(class_="error")[error()],
            
            ul()[
                [li(key=p["id"])[p["title"]] for p in posts()]
            ]
        ],
        
        # Pagination controls
        div(class_="pagination")[
            button(id="prev-btn", disabled=not has_prev())["Previous"],
            span()[f"Page {pagination()['page']} of {pagination()['pages']}"],
            button(id="next-btn", disabled=not has_next())["Next"],
        ],
        
        # JavaScript to fetch from API Route
        script(type="module")["""
            // Access PyNext signals from JavaScript
            const posts = __pynext__.signals.posts;
            const pagination = __pynext__.signals.pagination;
            const loading = __pynext__.signals.loading;
            const error = __pynext__.signals.error;
            
            // Fetch posts from API route
            async function loadPosts(page = 1) {
                loading.set(true);
                error.set(null);
                
                try {
                    const response = await fetch(`/api/posts?page=${page}&limit=10`);
                    
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    
                    const data = await response.json();
                    
                    // Update signals → UI auto-updates
                    posts.set(data.posts);
                    pagination.set(data.pagination);
                    
                } catch (e) {
                    error.set(e.message);
                } finally {
                    loading.set(false);
                }
            }
            
            // Pagination handlers
            document.getElementById('prev-btn').onclick = () => {
                const current = pagination.get().page;
                if (current > 1) loadPosts(current - 1);
            };
            
            document.getElementById('next-btn').onclick = () => {
                const current = pagination.get().page;
                const total = pagination.get().pages;
                if (current < total) loadPosts(current + 1);
            };
            
            // Initial load
            loadPosts();
        """]
    ]
```

### Data Flow Visualization

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      API ROUTES + SIGNALS FLOW                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   1. JAVASCRIPT FETCH                                                        │
│      └── fetch('/api/posts?page=1&limit=10')                                │
│                    │                                                         │
│                    ▼                                                         │
│   2. HTTP REQUEST                                                            │
│      └── GET /api/posts?page=1&limit=10                                     │
│          Headers: Content-Type: application/json                            │
│                    │                                                         │
│                    ▼                                                         │
│   3. ROUTE HANDLER EXECUTES                                                  │
│      └── pages/api/posts/route.py                                           │
│          │                                                                   │
│          │   @api_route                                                      │
│          │   async def GET(request):                                        │
│          │       query = get_query()                                        │
│          │       ...database query...                                       │
│          │       return {"posts": [...], "pagination": {...}}               │
│          │                                                                   │
│          ▼                                                                   │
│   4. JSON RESPONSE                                                           │
│      └── {                                                                   │
│            "posts": [{"id": 1, "title": "..."}],                            │
│            "pagination": {"page": 1, "total": 50, "pages": 5}               │
│          }                                                                   │
│                    │                                                         │
│                    ▼                                                         │
│   5. UPDATE SIGNALS FROM JAVASCRIPT                                          │
│      ├── posts.set(data.posts)           ───▶  ul updates with posts        │
│      └── pagination.set(data.pagination) ───▶  controls update              │
│                                                                              │
│   Note: JavaScript interacts with the same Signal system as Python!         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Pattern 3: Combined Approach

For complex applications, combine Server Actions and API Routes with shared business logic.

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        COMBINED APPROACH                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                      ┌─────────────────────────────┐                        │
│                      │     SHARED SERVICES         │                        │
│                      │     (Business Logic)        │                        │
│                      └─────────────┬───────────────┘                        │
│                                    │                                         │
│                    ┌───────────────┼───────────────┐                        │
│                    │               │               │                        │
│                    ▼               ▼               ▼                        │
│         ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                 │
│         │   Server     │ │    API       │ │   Cron       │                 │
│         │   Actions    │ │    Routes    │ │   Jobs       │                 │
│         │              │ │              │ │              │                 │
│         │  PyNext UI   │ │  Mobile App  │ │  Background  │                 │
│         │  Internal    │ │  External    │ │  Tasks       │                 │
│         └──────────────┘ └──────────────┘ └──────────────┘                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Implementation

```python
# ============================================================
# SHARED SERVICES: services/posts.py
# ============================================================

import asyncpg
from typing import List, Optional
from dataclasses import dataclass

DATABASE_URL = "postgresql://..."

@dataclass
class Post:
    id: int
    title: str
    content: str
    author_id: int
    created_at: str

async def get_posts(
    limit: int = 10,
    offset: int = 0,
    author_id: Optional[int] = None
) -> List[Post]:
    """Fetch posts with optional filtering."""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        query = "SELECT * FROM posts"
        params = []
        
        if author_id:
            query += " WHERE author_id = $1"
            params.append(author_id)
        
        query += f" ORDER BY created_at DESC LIMIT ${len(params)+1} OFFSET ${len(params)+2}"
        params.extend([limit, offset])
        
        rows = await conn.fetch(query, *params)
        return [Post(**dict(r)) for r in rows]
    finally:
        await conn.close()

async def create_post(title: str, content: str, author_id: int) -> Post:
    """Create a new post."""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        row = await conn.fetchrow(
            "INSERT INTO posts (title, content, author_id) VALUES ($1, $2, $3) RETURNING *",
            title, content, author_id
        )
        return Post(**dict(row))
    finally:
        await conn.close()

async def delete_post(post_id: int, author_id: int) -> bool:
    """Delete a post (only if author matches)."""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        result = await conn.execute(
            "DELETE FROM posts WHERE id = $1 AND author_id = $2",
            post_id, author_id
        )
        return result == "DELETE 1"
    finally:
        await conn.close()
```

```python
# ============================================================
# SERVER ACTIONS: Use shared services for PyNext UI
# ============================================================

from pynext import server_action
from services.posts import get_posts, create_post, delete_post

@server_action
async def load_my_posts(limit: int = 10):
    """Load posts for the current user (PyNext pages)."""
    user = get_current_user()  # From session
    posts = await get_posts(limit=limit, author_id=user.id)
    return [p.__dict__ for p in posts]

@server_action
async def publish_post(title: str, content: str):
    """Create a post as current user."""
    user = get_current_user()
    post = await create_post(title, content, user.id)
    return post.__dict__

@server_action
async def remove_my_post(post_id: int):
    """Delete own post."""
    user = get_current_user()
    success = await delete_post(post_id, user.id)
    if not success:
        raise ValueError("Post not found or unauthorized")
    return {"deleted": post_id}
```

```python
# ============================================================
# API ROUTES: Use shared services for external clients
# ============================================================

# pages/api/posts/route.py

from pynext import api_route, JSONResponse
from services.posts import get_posts, create_post
from auth import verify_api_token

@api_route
async def GET(request):
    """GET /api/posts - Public endpoint for listing posts."""
    limit = int(request.query_params.get("limit", 10))
    offset = int(request.query_params.get("offset", 0))
    
    posts = await get_posts(limit=limit, offset=offset)
    return {
        "posts": [p.__dict__ for p in posts]
    }

@api_route
async def POST(request):
    """POST /api/posts - Create post (requires API token)."""
    # Authenticate via API token (not session)
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user = await verify_api_token(token)
    
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    data = await request.json()
    post = await create_post(data["title"], data["content"], user.id)
    
    return JSONResponse({"post": post.__dict__}, status_code=201)
```

```python
# ============================================================
# PAGE: pages/my-posts.py - Uses Server Actions
# ============================================================

from pynext import Signal, page, div, button, ul, li, form, input_, textarea

posts = Signal([])
loading = Signal(False)

@page
def my_posts():
    async def load():
        loading.set(True)
        result = await load_my_posts(limit=20)
        posts.set(result)
        loading.set(False)
    
    async def submit(e):
        e.preventDefault()
        title = e.target.title.value
        content = e.target.content.value
        
        new_post = await publish_post(title, content)
        posts.update(lambda p: [new_post] + p)
        
        e.target.reset()
    
    async def delete(post_id):
        await remove_my_post(post_id)
        posts.update(lambda p: [x for x in p if x["id"] != post_id])
    
    return div()[
        h1()["My Posts"],
        
        form(onsubmit=submit)[
            input_(name="title", placeholder="Title", required=True),
            textarea(name="content", placeholder="Content", required=True),
            button(type="submit")["Publish"]
        ],
        
        button(onclick=load)["Refresh"],
        
        loading() and div()["Loading..."],
        
        ul()[
            [
                li(key=p["id"])[
                    p["title"],
                    button(onclick=lambda pid=p["id"]: delete(pid))["Delete"]
                ]
                for p in posts()
            ]
        ]
    ]
```

### When to Use What

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CHOOSING THE RIGHT APPROACH                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                        CLIENT TYPE?                                  │   │
│   └─────────────────────────────┬───────────────────────────────────────┘   │
│                                 │                                            │
│               ┌─────────────────┼─────────────────┐                         │
│               │                 │                 │                         │
│               ▼                 ▼                 ▼                         │
│   ┌───────────────────┐ ┌───────────────┐ ┌───────────────┐                │
│   │   PyNext Page     │ │  Mobile App   │ │  Third-Party  │                │
│   │   (Internal)      │ │  (Your App)   │ │  (External)   │                │
│   └─────────┬─────────┘ └───────┬───────┘ └───────┬───────┘                │
│             │                   │                 │                         │
│             ▼                   ▼                 ▼                         │
│   ┌───────────────────┐ ┌───────────────┐ ┌───────────────┐                │
│   │  SERVER ACTION    │ │  API ROUTE    │ │  API ROUTE    │                │
│   │                   │ │  + Auth Token │ │  + API Key    │                │
│   │  • Session auth   │ │               │ │               │                │
│   │  • Direct binding │ │  • JWT auth   │ │  • Rate limit │                │
│   │  • Type-safe      │ │  • REST       │ │  • Versioning │                │
│   └───────────────────┘ └───────────────┘ └───────────────┘                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Complete Data Flow

### End-to-End Example

Here's a complete flow from user action to UI update:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         COMPLETE DATA FLOW                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ STEP 1: USER CLICKS "LOAD USERS"                                    │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │                                                                      │    │
│  │   button(onclick=load_users)["Load Users"]                          │    │
│  │            │                                                         │    │
│  │            │  onclick event                                          │    │
│  │            ▼                                                         │    │
│  │   async def load_users():                                           │    │
│  │       loading.set(True)  # ← Immediate UI feedback                  │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                   │                                          │
│                                   ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ STEP 2: LOADING STATE UPDATES                                       │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │                                                                      │    │
│  │   loading Signal: False → True                                       │    │
│  │            │                                                         │    │
│  │            │  Signal notifies subscribers                            │    │
│  │            ▼                                                         │    │
│  │   ┌─────────────────────────────────────────────────────────────┐   │    │
│  │   │  DOM Update:                                                 │   │    │
│  │   │  loading() && div()["Loading..."]                           │   │    │
│  │   │                     │                                        │   │    │
│  │   │                     ▼                                        │   │    │
│  │   │  <div> inserted: "Loading..."                               │   │    │
│  │   └─────────────────────────────────────────────────────────────┘   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                   │                                          │
│                                   ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ STEP 3: SERVER ACTION CALL                                          │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │                                                                      │    │
│  │   result = await fetch_users()                                       │    │
│  │            │                                                         │    │
│  │            │  POST /_pynext/action                                   │    │
│  │            │  {"actionId": "fetch_users", "args": {}}               │    │
│  │            │                                                         │    │
│  │            ▼                                                         │    │
│  │   ┌─────────────────────────────────────────────────────────────┐   │    │
│  │   │  SERVER:                                                     │   │    │
│  │   │                                                              │   │    │
│  │   │  @server_action                                              │   │    │
│  │   │  async def fetch_users():                                    │   │    │
│  │   │      conn = await asyncpg.connect(...)                       │   │    │
│  │   │      rows = await conn.fetch("SELECT * FROM users")          │   │    │
│  │   │      return [dict(r) for r in rows]                          │   │    │
│  │   │                                                              │   │    │
│  │   │  Response: {"data": [{"id": 1, "name": "Alice"}, ...]}      │   │    │
│  │   └─────────────────────────────────────────────────────────────┘   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                   │                                          │
│                                   ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ STEP 4: UPDATE DATA SIGNAL                                          │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │                                                                      │    │
│  │   users.set(result)                                                  │    │
│  │            │                                                         │    │
│  │            │  Signal: [] → [{"id": 1, "name": "Alice"}, ...]        │    │
│  │            │                                                         │    │
│  │            ▼                                                         │    │
│  │   ┌─────────────────────────────────────────────────────────────┐   │    │
│  │   │  DOM Update:                                                 │   │    │
│  │   │  ul()[[li()[u["name"]] for u in users()]]                   │   │    │
│  │   │                     │                                        │   │    │
│  │   │                     ▼                                        │   │    │
│  │   │  <ul>                                                        │   │    │
│  │   │    <li>Alice</li>                                           │   │    │
│  │   │    <li>Bob</li>                                             │   │    │
│  │   │    ...                                                       │   │    │
│  │   │  </ul>                                                       │   │    │
│  │   └─────────────────────────────────────────────────────────────┘   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                   │                                          │
│                                   ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ STEP 5: CLEAR LOADING STATE                                         │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │                                                                      │    │
│  │   loading.set(False)                                                 │    │
│  │            │                                                         │    │
│  │            │  Signal: True → False                                   │    │
│  │            ▼                                                         │    │
│  │   ┌─────────────────────────────────────────────────────────────┐   │    │
│  │   │  DOM Update:                                                 │   │    │
│  │   │  loading() && div()["Loading..."]                           │   │    │
│  │   │                     │                                        │   │    │
│  │   │                     ▼                                        │   │    │
│  │   │  <div> removed (condition now false)                        │   │    │
│  │   └─────────────────────────────────────────────────────────────┘   │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  TOTAL TIME: ~100-200ms                                                      │
│  DOM OPERATIONS: 3 (show spinner, update list, hide spinner)                │
│  RE-RENDERS: 0 (fine-grained updates only)                                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Common Patterns

### Loading States

Always provide feedback during async operations:

```python
from pynext import Signal, server_action

loading = Signal(False)
error = Signal(None)
data = Signal(None)

@server_action
async def fetch_data():
    import time
    time.sleep(1)  # Simulate slow request
    return {"result": "data"}

async def load():
    loading.set(True)
    error.set(None)
    
    try:
        result = await fetch_data()
        data.set(result)
    except Exception as e:
        error.set(str(e))
    finally:
        loading.set(False)

# In UI
div()[
    # Show loading spinner
    loading() and div(class_="spinner")["Loading..."],
    
    # Show error if any
    error() and div(class_="error")[error()],
    
    # Show data when available
    data() and div(class_="content")[str(data())]
]
```

### Error Handling

```python
from pynext import Signal

error = Signal(None)
errors = Signal({})  # Field-level errors

@server_action
async def submit_form(data: dict):
    validation_errors = {}
    
    if not data.get("email"):
        validation_errors["email"] = "Email is required"
    
    if not data.get("password"):
        validation_errors["password"] = "Password is required"
    elif len(data["password"]) < 8:
        validation_errors["password"] = "Password must be 8+ characters"
    
    if validation_errors:
        raise ValueError(validation_errors)
    
    # Process valid data...
    return {"success": True}

async def handle_submit(form_data):
    errors.set({})
    error.set(None)
    
    try:
        result = await submit_form(form_data)
        # Success!
    except ValueError as e:
        if isinstance(e.args[0], dict):
            errors.set(e.args[0])  # Field errors
        else:
            error.set(str(e))  # General error
    except Exception as e:
        error.set(f"Unexpected error: {e}")

# In UI
form()[
    div()[
        input_(name="email"),
        errors().get("email") and span(class_="field-error")[errors()["email"]]
    ],
    div()[
        input_(name="password", type="password"),
        errors().get("password") and span(class_="field-error")[errors()["password"]]
    ],
    error() and div(class_="form-error")[error()]
]
```

### Optimistic Updates

Update UI immediately, rollback on failure:

```python
from pynext import Signal, server_action

todos = Signal([])

@server_action
async def delete_todo(todo_id: int):
    import asyncpg
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute("DELETE FROM todos WHERE id = $1", todo_id)
    return {"deleted": todo_id}

async def optimistic_delete(todo_id):
    # Save current state for rollback
    previous = todos()
    
    # Optimistic update - remove immediately
    todos.update(lambda t: [x for x in t if x["id"] != todo_id])
    
    try:
        # Confirm with server
        await delete_todo(todo_id)
    except Exception:
        # Rollback on failure
        todos.set(previous)
        error.set("Failed to delete. Please try again.")
```

### Pagination

```python
from pynext import Signal, Computed, server_action

items = Signal([])
page = Signal(1)
total_pages = Signal(1)
per_page = 10

has_next = Computed(lambda: page() < total_pages())
has_prev = Computed(lambda: page() > 1)

@server_action
async def fetch_page(page_num: int):
    import asyncpg
    conn = await asyncpg.connect(DATABASE_URL)
    
    offset = (page_num - 1) * per_page
    rows = await conn.fetch(
        "SELECT * FROM items LIMIT $1 OFFSET $2",
        per_page, offset
    )
    total = await conn.fetchval("SELECT COUNT(*) FROM items")
    
    return {
        "items": [dict(r) for r in rows],
        "total_pages": (total + per_page - 1) // per_page
    }

async def load_page(page_num: int):
    result = await fetch_page(page_num)
    items.set(result["items"])
    page.set(page_num)
    total_pages.set(result["total_pages"])

# In UI
div()[
    ul()[[li()[item["name"]] for item in items()]],
    
    div(class_="pagination")[
        button(onclick=lambda: load_page(page() - 1), disabled=not has_prev())["Prev"],
        span()[f"Page {page()} of {total_pages()}"],
        button(onclick=lambda: load_page(page() + 1), disabled=not has_next())["Next"]
    ]
]
```

### Form State

```python
from pynext import Signal, Store, Computed, server_action

# Form state using Store for nested updates
form = Store({
    "name": "",
    "email": "",
    "message": ""
})

submitting = Signal(False)
submitted = Signal(False)

# Validation
is_valid = Computed(lambda: 
    len(form.name) > 0 and 
    "@" in form.email and 
    len(form.message) > 10
)

@server_action
async def submit_contact(data: dict):
    import smtplib
    # Send email...
    return {"success": True}

async def handle_submit():
    if not is_valid():
        return
    
    submitting.set(True)
    try:
        await submit_contact({
            "name": form.name,
            "email": form.email,
            "message": form.message
        })
        submitted.set(True)
    finally:
        submitting.set(False)

# In UI
div()[
    submitted() and div(class_="success")["Thank you!"],
    
    not submitted() and form(onsubmit=handle_submit)[
        input_(
            value=form.name,
            oninput=lambda e: setattr(form, "name", e.target.value),
            placeholder="Name"
        ),
        input_(
            value=form.email,
            oninput=lambda e: setattr(form, "email", e.target.value),
            placeholder="Email"
        ),
        textarea(
            value=form.message,
            oninput=lambda e: setattr(form, "message", e.target.value),
            placeholder="Message (10+ chars)"
        ),
        button(
            type="submit",
            disabled=not is_valid() or submitting()
        )[
            submitting() and "Sending..." or "Send"
        ]
    ]
]
```

### Real-Time Updates (WebSocket)

```python
from pynext import Signal, page, div, ul, li, script

messages = Signal([])

@page
def chat():
    return div()[
        ul(id="messages")[
            [li(key=m["id"])[m["text"]] for m in messages()]
        ],
        
        script(type="module")["""
            const messages = __pynext__.signals.messages;
            
            // Connect to WebSocket
            const ws = new WebSocket('wss://your-server.com/ws');
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                
                // Update Signal → UI auto-updates
                messages.update(current => [...current, data]);
            };
            
            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
        """]
    ]
```

---

## Best Practices

### 1. Keep Signals at the Right Scope

```python
# ✅ GOOD: Module-level for shared state
users = Signal([])

@page
def users_page():
    # Access shared signal
    return div()[[li()[u["name"]] for u in users()]]

# ❌ BAD: Creating signals inside functions (recreated each render)
@page
def users_page():
    users = Signal([])  # Wrong! Recreated each time
    ...
```

### 2. Use Computed for Derived State

```python
# ✅ GOOD: Derived with Computed
todos = Signal([])
completed_count = Computed(lambda: len([t for t in todos() if t["done"]]))
pending_count = Computed(lambda: len([t for t in todos() if not t["done"]]))

# ❌ BAD: Storing derived state
todos = Signal([])
completed_count = Signal(0)  # Wrong! Will get out of sync
```

### 3. Batch Related Updates

```python
from pynext import batch

# ✅ GOOD: Batch updates
async def load_dashboard():
    result = await fetch_dashboard()
    
    batch(lambda: (
        users.set(result["users"]),
        posts.set(result["posts"]),
        stats.set(result["stats"])
    ))  # Single UI update

# ❌ BAD: Multiple separate updates
async def load_dashboard():
    result = await fetch_dashboard()
    users.set(result["users"])   # UI update 1
    posts.set(result["posts"])   # UI update 2
    stats.set(result["stats"])   # UI update 3
```

### 4. Handle All States

```python
# ✅ GOOD: Handle loading, error, empty, and data states
div()[
    loading() and div()["Loading..."],
    error() and div()[error()],
    not loading() and not error() and len(items()) == 0 and div()["No items found"],
    len(items()) > 0 and ul()[[li()[i] for i in items()]]
]
```

### 5. Clean Up Effects

```python
from pynext import Effect

@page
def live_data():
    interval_id = Signal(None)
    
    @Effect
    def poll():
        # Start polling
        id = setInterval(lambda: fetch_data(), 5000)
        interval_id.set(id)
        
        # Cleanup function
        return lambda: clearInterval(interval_id())
    
    ...
```

---

## Quick Reference

### Data Fetching Decision Tree

| Question | Answer | Use |
|----------|--------|-----|
| Is client a PyNext page? | Yes | Server Action |
| Is client external (mobile, 3rd party)? | Yes | API Route |
| Need REST semantics? | Yes | API Route |
| Need session auth? | Yes | Server Action |
| Need API key auth? | Yes | API Route |
| Is it internal, simple call? | Yes | Server Action |

### State Update Methods

| Method | When to Use | Example |
|--------|-------------|---------|
| `signal.set(value)` | Replace entire value | `users.set([...])` |
| `signal.update(fn)` | Transform current value | `count.update(x => x + 1)` |
| `store.field = value` | Update nested field | `user.name = "Alice"` |
| `batch(fn)` | Multiple updates at once | `batch(() => { a.set(1); b.set(2) })` |

### Async Pattern Template

```python
data = Signal(None)
loading = Signal(False)
error = Signal(None)

async def fetch_pattern():
    loading.set(True)
    error.set(None)
    try:
        result = await server_action_or_fetch()
        data.set(result)
    except Exception as e:
        error.set(str(e))
    finally:
        loading.set(False)
```

---

## Troubleshooting

### Signal Not Updating UI

```python
# Problem: UI not updating
items = Signal([])
items()[0] = "new"  # ❌ Mutating array doesn't trigger

# Solution: Use set or update
items.update(lambda i: ["new"] + i[1:])  # ✅
```

### Server Action Not Called

```python
# Problem: async not awaited
async def handler():
    fetch_users()  # ❌ Not awaited

# Solution: await async functions
async def handler():
    await fetch_users()  # ✅
```

### State Lost on Navigation

```python
# Problem: Signals defined in page function
@page
def my_page():
    data = Signal([])  # ❌ Lost on navigation

# Solution: Module-level Signals
data = Signal([])  # ✅ Persists

@page
def my_page():
    return div()[str(data())]
```

### Race Conditions

```python
# Problem: Old request returns after new one
async def search(query):
    loading.set(True)
    result = await search_action(query)
    results.set(result)  # ❌ Might be stale

# Solution: Track request ID
request_id = Signal(0)

async def search(query):
    current_id = request_id() + 1
    request_id.set(current_id)
    
    loading.set(True)
    result = await search_action(query)
    
    # Only update if this is still the current request
    if request_id() == current_id:
        results.set(result)
        loading.set(False)
```

---

## Related Documentation

- **[State Management](STATE_MANAGEMENT.md)** - Deep dive into Signals, Stores, Computed, Effects
- **[State Patterns](STATE_PATTERNS.md)** - Advanced patterns: forms, async, state machines
- **[Server Actions](SERVER_ACTIONS.md)** - Complete Server Actions guide
- **[API Routes](API_ROUTES.md)** - REST endpoint creation
- **[React Integration](REACT_INTEGRATION.md)** - Using React components with PyNext Signals

