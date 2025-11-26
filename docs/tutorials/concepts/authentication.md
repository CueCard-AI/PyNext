# Authentication

> **Implement login, logout, and protected routes**

Learn how to add authentication to your PyNext application with sessions, protected routes, and user management.

---

## What You'll Learn

- Session-based authentication
- Login and logout flows
- Protected routes with middleware
- User context and state
- Security best practices

---

## Basic Auth Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Login      │────▶│   Server     │────▶│   Session    │
│   Form       │     │   Validates  │     │   Created    │
└──────────────┘     └──────────────┘     └──────────────┘
                                                 │
                                                 ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Protected  │◀────│   Middleware │◀────│   Cookie     │
│   Content    │     │   Checks     │     │   Sent       │
└──────────────┘     └──────────────┘     └──────────────┘
```

---

## Step 1: User Model

```python
# db/models.py
from dataclasses import dataclass
from typing import Optional
import hashlib
import os

@dataclass
class User:
    id: int
    email: str
    password_hash: str
    name: str
    
    def check_password(self, password: str) -> bool:
        """Verify password against stored hash."""
        return hash_password(password) == self.password_hash


def hash_password(password: str) -> str:
    """Hash a password securely."""
    # In production, use bcrypt or argon2
    salt = os.environ.get("PASSWORD_SALT", "dev-salt")
    return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
```

---

## Step 2: Session Management

```python
# auth/session.py
import secrets
from datetime import datetime, timedelta
from typing import Optional

# In production, use Redis or database for sessions
sessions = {}

def create_session(user_id: int) -> str:
    """Create a new session and return the token."""
    token = secrets.token_urlsafe(32)
    sessions[token] = {
        "user_id": user_id,
        "created_at": datetime.now(),
        "expires_at": datetime.now() + timedelta(days=7),
    }
    return token


def get_session(token: str) -> Optional[dict]:
    """Get session data by token."""
    session = sessions.get(token)
    if not session:
        return None
    
    if datetime.now() > session["expires_at"]:
        del sessions[token]
        return None
    
    return session


def delete_session(token: str) -> bool:
    """Delete a session (logout)."""
    if token in sessions:
        del sessions[token]
        return True
    return False


def get_user_from_session(token: str) -> Optional[User]:
    """Get the user associated with a session."""
    session = get_session(token)
    if not session:
        return None
    
    from db.queries import get_user
    return get_user(session["user_id"])
```

---

## Step 3: Auth Server Actions

```python
# auth/actions.py
from pynext import server_action, get_cookies, set_cookie, delete_cookie
from auth.session import create_session, delete_session, get_user_from_session
from db.queries import get_user_by_email
from db.models import hash_password


@server_action
async def login(email: str, password: str):
    """Authenticate user and create session."""
    # Find user
    user = get_user_by_email(email)
    if not user:
        return {"success": False, "error": "Invalid email or password"}
    
    # Verify password
    if not user.check_password(password):
        return {"success": False, "error": "Invalid email or password"}
    
    # Create session
    token = create_session(user.id)
    
    # Set cookie
    set_cookie("session", token, {
        "httponly": True,
        "secure": True,  # HTTPS only in production
        "samesite": "lax",
        "max_age": 60 * 60 * 24 * 7,  # 7 days
    })
    
    return {"success": True, "user": {"id": user.id, "name": user.name}}


@server_action
async def logout():
    """End user session."""
    cookies = get_cookies()
    token = cookies.get("session")
    
    if token:
        delete_session(token)
        delete_cookie("session")
    
    return {"success": True}


@server_action
async def register(name: str, email: str, password: str):
    """Create a new user account."""
    from db.queries import get_user_by_email, create_user
    
    # Check if email exists
    existing = get_user_by_email(email)
    if existing:
        return {"success": False, "error": "Email already registered"}
    
    # Validate password
    if len(password) < 8:
        return {"success": False, "error": "Password must be at least 8 characters"}
    
    # Create user
    user_id = create_user(
        name=name,
        email=email,
        password_hash=hash_password(password),
    )
    
    # Auto-login
    token = create_session(user_id)
    set_cookie("session", token, {
        "httponly": True,
        "secure": True,
        "samesite": "lax",
        "max_age": 60 * 60 * 24 * 7,
    })
    
    return {"success": True}


def get_current_user():
    """Get the currently logged-in user."""
    cookies = get_cookies()
    token = cookies.get("session")
    
    if not token:
        return None
    
    return get_user_from_session(token)
```

---

## Step 4: Protected Route Middleware

```python
# middleware.py
from pynext import middleware, redirect, get_cookies
from auth.session import get_session

# Routes that don't require auth
PUBLIC_ROUTES = ["/", "/login", "/register", "/about"]


@middleware
def auth_middleware(request):
    """Protect routes that require authentication."""
    path = request.path
    
    # Allow public routes
    if path in PUBLIC_ROUTES or path.startswith("/api/public"):
        return None  # Continue to route
    
    # Check for session
    token = request.cookies.get("session")
    if not token:
        return redirect(f"/login?next={path}")
    
    session = get_session(token)
    if not session:
        return redirect(f"/login?next={path}")
    
    # Attach user to request for use in pages
    request.user_id = session["user_id"]
    
    return None  # Continue to route
```

---

## Step 5: Login Page

```python
# pages/login.py
from pynext import page, server_action, div, h1, form, a, Signal
from pynext.shadcn import Button, Input, Label, Card, CardHeader, CardTitle, CardContent, Alert

from auth.actions import login

# State
error = Signal(None)
loading = Signal(False)


@server_action
async def handle_login(data: dict):
    loading.set(True)
    error.set(None)
    
    result = await login(data.get("email", ""), data.get("password", ""))
    
    loading.set(False)
    
    if not result["success"]:
        error.set(result["error"])
        return
    
    # Redirect to dashboard (or 'next' param)
    from pynext import redirect
    redirect("/dashboard")


@page(title="Login")
def login_page():
    return div(class_="min-h-screen flex items-center justify-center p-4")[
        Card(class_="w-full max-w-md")[
            CardHeader()[
                CardTitle(class_="text-center")["Welcome Back"],
            ],
            CardContent()[
                error.value and Alert(variant="destructive", class_="mb-4")[
                    error.value
                ],
                
                form(action=handle_login, class_="space-y-4")[
                    div(class_="space-y-2")[
                        Label(html_for="email")["Email"],
                        Input(
                            id="email",
                            name="email",
                            type="email",
                            required=True,
                            placeholder="you@example.com",
                        ),
                    ],
                    div(class_="space-y-2")[
                        Label(html_for="password")["Password"],
                        Input(
                            id="password",
                            name="password",
                            type="password",
                            required=True,
                        ),
                    ],
                    Button(type="submit", class_="w-full", disabled=loading.value)[
                        "Signing in..." if loading.value else "Sign In"
                    ],
                ],
                
                div(class_="text-center mt-4 text-sm text-muted-foreground")[
                    "Don't have an account? ",
                    a(href="/register", class_="text-primary hover:underline")[
                        "Sign up"
                    ],
                ],
            ],
        ],
    ]
```

---

## Step 6: User Context

```python
# auth/context.py
from pynext import Signal
from auth.actions import get_current_user

# Current user state
current_user = Signal(None)

def init_user():
    """Initialize user from session on page load."""
    user = get_current_user()
    current_user.set(user)

def require_user():
    """Get current user or redirect to login."""
    from pynext import redirect
    
    user = current_user.value
    if not user:
        # PyNext handles redirect on both server and client
        redirect("/login")
        return None
    return user
```

Using in components:

```python
from auth.context import current_user

def UserMenu():
    user = current_user.value
    
    if not user:
        return Button()[a(href="/login")["Sign In"]]
    
    return DropdownMenu()[
        DropdownMenuTrigger()[
            Avatar()[
                AvatarFallback()[user.initials]
            ]
        ],
        DropdownMenuContent()[
            DropdownMenuLabel()[user.name],
            DropdownMenuSeparator(),
            DropdownMenuItem(onclick=logout)["Log Out"],
        ],
    ]
```

---

## Step 7: Protected Page Example

```python
# pages/dashboard.py
from pynext import page, redirect
from auth.context import current_user

@page(title="Dashboard")
def dashboard():
    user = current_user.value
    
    # This shouldn't happen if middleware works, but double-check
    if not user:
        return redirect("/login")
    
    return div(class_="p-8")[
        h1(class_="text-2xl font-bold mb-4")[
            f"Welcome, {user.name}!"
        ],
        # Dashboard content...
    ]
```

---

## Security Best Practices

### 1. Password Security

```python
# Use bcrypt or argon2 in production
import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), hash.encode())
```

### 2. CSRF Protection

```python
# Generate CSRF token
def get_csrf_token():
    token = secrets.token_urlsafe(32)
    # Store in session
    return token

# In forms
input(type="hidden", name="csrf_token", value=get_csrf_token())

# Validate in server action
if data.get("csrf_token") != session.get("csrf_token"):
    return {"error": "Invalid request"}
```

### 3. Rate Limiting

```python
from collections import defaultdict
from datetime import datetime, timedelta

login_attempts = defaultdict(list)

def check_rate_limit(email: str) -> bool:
    """Check if login attempts are rate limited."""
    now = datetime.now()
    attempts = login_attempts[email]
    
    # Remove old attempts
    attempts[:] = [t for t in attempts if now - t < timedelta(minutes=15)]
    
    if len(attempts) >= 5:
        return False  # Rate limited
    
    attempts.append(now)
    return True
```

### 4. Secure Cookies

```python
set_cookie("session", token, {
    "httponly": True,     # Not accessible via JavaScript
    "secure": True,       # HTTPS only
    "samesite": "lax",    # CSRF protection
    "path": "/",          # Available on all paths
    "max_age": 604800,    # 7 days
})
```

---

## Complete Auth System

```
auth/
├── __init__.py
├── actions.py      # login, logout, register
├── session.py      # Session management
├── context.py      # User context/state
├── middleware.py   # Route protection
└── utils.py        # Password hashing, etc.
```

---

## Key Takeaways

1. **Sessions for state** — Store session ID in HttpOnly cookie
2. **Middleware for protection** — Check auth before page loads
3. **Never trust client** — Always validate on server
4. **Hash passwords** — Use bcrypt or argon2
5. **Secure cookies** — HttpOnly, Secure, SameSite

---

## Related Tutorials

- [Forms & Validation](./forms-and-validation.md) - Login/signup forms
- [State Management](./state-management.md) - User state patterns

