"""
Templates for all generator types.

Each type has:
- minimal: Just the essentials, no boilerplate
- full: Complete with imports, docstrings, examples

Why Two Styles?
    - minimal: For experienced devs who know what they need
    - full: For learning, reference, and comprehensive scaffolding
"""

from typing import Dict, Literal

# ============================================
# Template Definitions
# ============================================

TEMPLATES: Dict[str, Dict[Literal["minimal", "full"], str]] = {
    
    # ----------------------------------------
    # Page
    # ----------------------------------------
    "page": {
        "minimal": '''"""Page: {title}"""
from pynext import div, h1

def {name}():
    return div(
        h1("{title}")
    )
''',
        "full": '''"""
{title} Page

Route: /{route}
"""

from pynext import (
    div, h1, p, section,
    Metadata, Link,
)

# SEO metadata
metadata = Metadata(
    title="{title}",
    description="{title} page",
)


async def get_data():
    """
    Fetch data for this page.
    
    Runs on the server before rendering.
    Return data that the page component needs.
    
    Example:
        return {{"items": await db.get_items()}}
    """
    return {{
        "message": "Hello from {title}!",
    }}


def {name}(data: dict):
    """
    {title} Page
    
    Args:
        data: Server-fetched data from get_data()
    
    Example:
        # Access data
        message = data["message"]
    """
    return div(class_="container mx-auto px-4 py-8")(
        # Header
        section(class_="mb-8")(
            h1(class_="text-3xl font-bold text-gray-900")(
                "{title}"
            ),
            p(class_="mt-2 text-gray-600")(
                data.get("message", "Welcome!")
            ),
        ),
        
        # Content
        section(class_="space-y-4")(
            p("Edit this page at pages/{route}.py"),
            
            # Navigation example
            Link(href="/")(
                "← Back to Home"
            ),
        ),
    )
''',
    },
    
    # ----------------------------------------
    # Component
    # ----------------------------------------
    "component": {
        "minimal": '''"""Component: {title}"""
from pynext import div

def {name}():
    return div(class_="")("{title}")
''',
        "full": '''"""
{title} Component

A reusable UI component.

Example:
    from components.{name} import {name}
    
    {name}(title="Hello", variant="primary")
"""

from typing import Literal, Optional
from pynext import div, span


def {name}(
    title: str = "{title}",
    variant: Literal["primary", "secondary", "outline"] = "primary",
    class_: Optional[str] = None,
):
    """
    {title} Component
    
    Args:
        title: Display text
        variant: Visual style - "primary", "secondary", or "outline"
        class_: Additional CSS classes
    
    Returns:
        PyNext component
    
    Example:
        # Basic usage
        {name}(title="Click me")
        
        # With variant
        {name}(title="Secondary", variant="secondary")
        
        # With custom classes
        {name}(class_="mt-4 shadow-lg")
    """
    # Variant styles
    variant_classes = {{
        "primary": "bg-blue-600 text-white hover:bg-blue-700",
        "secondary": "bg-gray-200 text-gray-800 hover:bg-gray-300",
        "outline": "border-2 border-blue-600 text-blue-600 hover:bg-blue-50",
    }}
    
    base_classes = "px-4 py-2 rounded-lg font-medium transition-colors"
    
    return div(
        class_=f"{{base_classes}} {{variant_classes[variant]}} {{class_ or ''}}".strip()
    )(
        span(title)
    )
''',
    },
    
    # ----------------------------------------
    # Island (Interactive Component)
    # ----------------------------------------
    "island": {
        "minimal": '''"""Island: {title}"""
from pynext import div, button, Signal
from pynext.islands import island

@island
def {name}():
    count = Signal(0)
    
    return div(
        button(on_click=lambda: count.set(count() + 1))(
            f"Count: {{count()}}"
        )
    )
''',
        "full": '''"""
{title} Island

An interactive component that hydrates on the client.
Uses fine-grained reactivity (SolidJS principles).

Example:
    from components.{name} import {name}
    
    # In your page
    {name}(initial_value=10)
"""

from pynext import (
    div, button, span,
    Signal, Computed, Effect,
)
from pynext.islands import island


@island
def {name}(initial_value: int = 0):
    """
    {title} Interactive Component
    
    Hydrates on the client for interactivity.
    Uses signals for fine-grained reactivity.
    
    Args:
        initial_value: Starting value
    
    Example:
        # Basic
        {name}()
        
        # With initial value
        {name}(initial_value=5)
    """
    # Signals - fine-grained reactive state
    # Only the specific DOM that reads this will update
    count = Signal(initial_value)
    
    # Computed - derived values, auto-updates when dependencies change
    doubled = Computed(lambda: count() * 2)
    is_even = Computed(lambda: count() % 2 == 0)
    
    # Effect - side effects that run when dependencies change
    Effect(lambda: print(f"Count is now: {{count()}}"))
    
    def increment():
        count.set(count() + 1)
    
    def decrement():
        count.set(max(0, count() - 1))
    
    def reset():
        count.set(initial_value)
    
    return div(class_="flex flex-col items-center gap-4 p-6 bg-white rounded-lg shadow")(
        # Display
        div(class_="text-center")(
            span(class_="text-4xl font-bold text-gray-900")(
                lambda: str(count())
            ),
            span(class_="block text-sm text-gray-500 mt-1")(
                lambda: f"Doubled: {{doubled()}} | {{'Even' if is_even() else 'Odd'}}"
            ),
        ),
        
        # Controls
        div(class_="flex gap-2")(
            button(
                class_="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600",
                on_click=decrement,
            )("-"),
            
            button(
                class_="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300",
                on_click=reset,
            )("Reset"),
            
            button(
                class_="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600",
                on_click=increment,
            )("+"),
        ),
    )
''',
    },
    
    # ----------------------------------------
    # API Route
    # ----------------------------------------
    "api": {
        "minimal": '''"""API: {route}"""
from pynext.api import api

@api
async def handler(request):
    return {{"message": "Hello from {title}"}}
''',
        "full": '''"""
{title} API Route

Endpoint: /api/{route}
Methods: GET, POST

Example:
    # GET request
    fetch('/api/{route}')
    
    # POST request
    fetch('/api/{route}', {{
        method: 'POST',
        body: JSON.stringify({{ name: 'John' }})
    }})
"""

from typing import Optional
from pynext.api import api, Request, Response


@api
async def GET(request: Request) -> Response:
    """
    Handle GET requests.
    
    Args:
        request: Incoming request object
    
    Returns:
        JSON response
    
    Example:
        GET /api/{route}?limit=10
    """
    # Access query parameters
    limit = request.query.get("limit", 10)
    
    # Your logic here
    items = []  # await db.get_items(limit=limit)
    
    return Response.json({{
        "items": items,
        "count": len(items),
    }})


@api
async def POST(request: Request) -> Response:
    """
    Handle POST requests.
    
    Args:
        request: Incoming request with JSON body
    
    Returns:
        JSON response
    
    Example:
        POST /api/{route}
        Body: {{"name": "John", "email": "john@example.com"}}
    """
    # Parse JSON body
    try:
        data = await request.json()
    except Exception:
        return Response.json(
            {{"error": "Invalid JSON"}},
            status=400
        )
    
    # Validate required fields
    if not data.get("name"):
        return Response.json(
            {{"error": "Name is required"}},
            status=400
        )
    
    # Your logic here
    # result = await db.create_item(data)
    
    return Response.json({{
        "success": True,
        "data": data,
    }}, status=201)
''',
    },
    
    # ----------------------------------------
    # Layout
    # ----------------------------------------
    "layout": {
        "minimal": '''"""Layout for {title}"""
from pynext import div

def layout(children):
    return div(class_="min-h-screen")(
        children
    )
''',
        "full": '''"""
{title} Layout

Wraps all pages in this directory.
Persists across navigation (doesn't remount).

Example structure:
    pages/
    └── {route}/
        ├── layout.py  ← You are here
        ├── page.py    ← Wrapped by this layout
        └── settings/
            └── page.py  ← Also wrapped by this layout
"""

from pynext import div, nav, main, footer, Link


def layout(children):
    """
    Layout wrapper for {title} section.
    
    Args:
        children: Page content to wrap
    
    Note:
        This layout persists across navigation.
        Use template.py if you need to remount on each navigation.
    """
    return div(class_="min-h-screen flex flex-col")(
        # Navigation
        nav(class_="bg-white shadow-sm border-b")(
            div(class_="container mx-auto px-4 py-3 flex items-center gap-6")(
                Link(href="/{route}", class_="font-semibold text-gray-900")(
                    "{title}"
                ),
                Link(href="/{route}/settings", class_="text-gray-600 hover:text-gray-900")(
                    "Settings"
                ),
            ),
        ),
        
        # Main content
        main(class_="flex-1 container mx-auto px-4 py-8")(
            children
        ),
        
        # Footer
        footer(class_="bg-gray-100 border-t")(
            div(class_="container mx-auto px-4 py-4 text-center text-gray-600")(
                "© 2024 {title}"
            ),
        ),
    )
''',
    },
    
    # ----------------------------------------
    # Template (remounts on navigation)
    # ----------------------------------------
    "template": {
        "minimal": '''"""Template for {title}"""
from pynext import div

def template(children):
    return div(children)
''',
        "full": '''"""
{title} Template

Like layout, but REMOUNTS on every navigation.
Use for animations, resetting state, etc.

Difference from Layout:
    - layout.py: Persists across navigation (shared state)
    - template.py: Remounts on navigation (fresh state)

Example use cases:
    - Page enter/exit animations
    - Resetting scroll position
    - Fresh component state on each visit
"""

from pynext import div
from pynext.transitions import FadeIn


def template(children):
    """
    Template wrapper that remounts on navigation.
    
    Args:
        children: Page content to wrap
    
    Note:
        This will remount (re-render from scratch) on every navigation.
        Use layout.py if you want persistence.
    """
    return FadeIn(duration=200)(
        div(class_="animate-in fade-in duration-200")(
            children
        )
    )
''',
    },
    
    # ----------------------------------------
    # Loading
    # ----------------------------------------
    "loading": {
        "minimal": '''"""Loading state for {title}"""
from pynext import div

def loading():
    return div("Loading...")
''',
        "full": '''"""
{title} Loading State

Shown while the page is loading data.
Automatically displayed during async get_data().

Why Loading States Matter:
    - Better user experience
    - Prevents layout shift
    - Shows progress to users
"""

from pynext import div, span


def loading():
    """
    Loading skeleton for {title} page.
    
    Displayed automatically while get_data() is running.
    """
    return div(class_="container mx-auto px-4 py-8 animate-pulse")(
        # Header skeleton
        div(class_="mb-8")(
            div(class_="h-8 bg-gray-200 rounded w-1/3 mb-2"),
            div(class_="h-4 bg-gray-200 rounded w-1/2"),
        ),
        
        # Content skeleton
        div(class_="space-y-4")(
            div(class_="h-4 bg-gray-200 rounded w-full"),
            div(class_="h-4 bg-gray-200 rounded w-5/6"),
            div(class_="h-4 bg-gray-200 rounded w-4/6"),
        ),
        
        # Screen reader text
        span(class_="sr-only")("Loading {title}..."),
    )
''',
    },
    
    # ----------------------------------------
    # Error
    # ----------------------------------------
    "error": {
        "minimal": '''"""Error boundary for {title}"""
from pynext import div, h1

def error(error_info):
    return div(
        h1("Something went wrong"),
    )
''',
        "full": '''"""
{title} Error Boundary

Catches errors in child components.
Shows user-friendly error message.

Example:
    If any component in pages/{route}/ throws an error,
    this error boundary will catch it and display this UI.
"""

from pynext import div, h1, p, button, pre, code


def error(error_info: dict):
    """
    Error boundary for {title} section.
    
    Args:
        error_info: Error details
            - message: Error message
            - stack: Stack trace (dev only)
            - reset: Function to retry
    
    Example:
        error_info = {{
            "message": "Failed to fetch data",
            "stack": "...",
            "reset": lambda: None,
        }}
    """
    message = error_info.get("message", "An unexpected error occurred")
    stack = error_info.get("stack")
    reset = error_info.get("reset")
    
    return div(class_="min-h-[50vh] flex items-center justify-center")(
        div(class_="max-w-md w-full p-8 text-center")(
            # Icon
            div(class_="text-6xl mb-4")("⚠️"),
            
            # Title
            h1(class_="text-2xl font-bold text-gray-900 mb-2")(
                "Something went wrong"
            ),
            
            # Message
            p(class_="text-gray-600 mb-6")(message),
            
            # Retry button
            button(
                class_="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700",
                on_click=reset,
            )("Try Again") if reset else None,
            
            # Stack trace (dev only)
            pre(class_="mt-6 p-4 bg-gray-100 rounded text-left text-xs overflow-auto max-h-48")(
                code(stack)
            ) if stack else None,
        ),
    )
''',
    },
    
    # ----------------------------------------
    # Middleware
    # ----------------------------------------
    "middleware": {
        "minimal": '''"""Middleware"""
from pynext.middleware import middleware

@middleware
async def handler(request, next_handler):
    return await next_handler(request)
''',
        "full": '''"""
Request Middleware

Runs before every request.
Use for authentication, logging, redirects, etc.

Example use cases:
    - Check authentication
    - Add headers
    - Log requests
    - Redirect based on conditions
"""

from pynext.middleware import middleware, NextResponse


@middleware
async def handler(request, next_handler):
    """
    Global middleware handler.
    
    Args:
        request: Incoming request
        next_handler: Next middleware or route handler
    
    Returns:
        Response (either from next_handler or custom)
    
    Example:
        # Allow request to continue
        return await next_handler(request)
        
        # Redirect
        return NextResponse.redirect("/login")
        
        # Return custom response
        return NextResponse.json({{"error": "Unauthorized"}}, status=401)
    """
    # Get request info
    path = request.url.path
    method = request.method
    
    # Example: Logging
    print(f"[{{method}}] {{path}}")
    
    # Example: Check authentication for protected routes
    if path.startswith("/dashboard"):
        token = request.cookies.get("auth_token")
        if not token:
            return NextResponse.redirect("/login")
    
    # Example: Add custom headers
    response = await next_handler(request)
    response.headers["X-Custom-Header"] = "PyNext"
    
    return response


# Configure which routes this middleware applies to
config = {{
    "matcher": [
        # Match all routes except static files
        "/((?!_next/static|_next/image|favicon.ico).*)",
    ],
}}
''',
    },
    
    # ----------------------------------------
    # Server Action
    # ----------------------------------------
    "action": {
        "minimal": '''"""Action: {title}"""
from pynext.actions import action

@action
async def {name}(data):
    return {{"success": True}}
''',
        "full": '''"""
{title} Server Action

A server-side function callable from the client.
Handles form submissions and mutations.

Example:
    from actions.{name} import {name}
    
    # In your component
    form(on_submit={name})(
        input(name="email"),
        button("Submit")
    )
"""

from typing import Optional
from pynext.actions import action, ActionError
from pynext import redirect


@action
async def {name}(form_data: dict) -> dict:
    """
    {title} action handler.
    
    Args:
        form_data: Form data as dictionary
    
    Returns:
        Result dictionary
    
    Raises:
        ActionError: On validation or processing errors
    
    Example:
        form_data = {{"email": "user@example.com", "name": "John"}}
        result = await {name}(form_data)
    """
    # Validate input
    email = form_data.get("email")
    name = form_data.get("name")
    
    if not email:
        raise ActionError("Email is required", field="email")
    
    if not name:
        raise ActionError("Name is required", field="name")
    
    # Validate email format
    if "@" not in email:
        raise ActionError("Invalid email format", field="email")
    
    # Process the action
    try:
        # Your logic here
        # result = await db.create_user(email=email, name=name)
        result = {{"id": 1, "email": email, "name": name}}
        
    except Exception as e:
        raise ActionError(f"Failed to process: {{str(e)}}")
    
    # Return success
    return {{
        "success": True,
        "data": result,
        "message": f"Successfully processed for {{name}}",
    }}


@action
async def {name}_delete(id: int) -> dict:
    """
    Delete action for {title}.
    
    Args:
        id: ID of item to delete
    
    Returns:
        Success status
    """
    if not id:
        raise ActionError("ID is required")
    
    # Your delete logic here
    # await db.delete(id)
    
    return {{"success": True, "deleted_id": id}}
''',
    },
    
    # ----------------------------------------
    # Hook
    # ----------------------------------------
    "hook": {
        "minimal": '''"""Hook: {title}"""
from pynext import Signal

def {name}(initial=None):
    state = Signal(initial)
    return state
''',
        "full": '''"""
{title} Hook

A reusable hook for shared logic.

Example:
    from hooks.{name} import {name}
    
    # In your component
    value, set_value, reset = {name}(initial="hello")
"""

from typing import TypeVar, Generic, Callable, Optional
from pynext import Signal, Computed, Effect


T = TypeVar("T")


def {name}(initial: T = None) -> tuple[Callable[[], T], Callable[[T], None], Callable[[], None]]:
    """
    {title} hook.
    
    A reusable hook for managing state with common operations.
    
    Args:
        initial: Initial value
    
    Returns:
        Tuple of (getter, setter, reset)
        - getter: Function to get current value
        - setter: Function to set new value
        - reset: Function to reset to initial value
    
    Example:
        # Basic usage
        value, set_value, reset = {name}("hello")
        
        print(value())      # "hello"
        set_value("world")
        print(value())      # "world"
        reset()
        print(value())      # "hello"
    """
    state = Signal(initial)
    
    def getter() -> T:
        return state()
    
    def setter(new_value: T) -> None:
        state.set(new_value)
    
    def reset() -> None:
        state.set(initial)
    
    return getter, setter, reset


def use_toggle(initial: bool = False) -> tuple[Callable[[], bool], Callable[[], None], Callable[[bool], None]]:
    """
    Boolean toggle hook.
    
    Args:
        initial: Initial boolean value
    
    Returns:
        Tuple of (value, toggle, set_value)
    
    Example:
        is_open, toggle, set_open = use_toggle(False)
        
        toggle()  # Now True
        toggle()  # Now False
        set_open(True)  # Force True
    """
    state = Signal(initial)
    
    def value() -> bool:
        return state()
    
    def toggle() -> None:
        state.set(not state())
    
    def set_value(new_value: bool) -> None:
        state.set(new_value)
    
    return value, toggle, set_value


def use_counter(initial: int = 0, min_val: Optional[int] = None, max_val: Optional[int] = None):
    """
    Counter hook with optional bounds.
    
    Args:
        initial: Starting count
        min_val: Minimum allowed value
        max_val: Maximum allowed value
    
    Returns:
        Dict with count, increment, decrement, reset, set_count
    
    Example:
        counter = use_counter(0, min_val=0, max_val=100)
        
        counter["increment"]()
        print(counter["count"]())  # 1
    """
    state = Signal(initial)
    
    def count() -> int:
        return state()
    
    def increment(amount: int = 1) -> None:
        new_val = state() + amount
        if max_val is not None:
            new_val = min(new_val, max_val)
        state.set(new_val)
    
    def decrement(amount: int = 1) -> None:
        new_val = state() - amount
        if min_val is not None:
            new_val = max(new_val, min_val)
        state.set(new_val)
    
    def reset() -> None:
        state.set(initial)
    
    def set_count(value: int) -> None:
        if min_val is not None:
            value = max(value, min_val)
        if max_val is not None:
            value = min(value, max_val)
        state.set(value)
    
    return {{
        "count": count,
        "increment": increment,
        "decrement": decrement,
        "reset": reset,
        "set_count": set_count,
    }}
''',
    },
}


# ============================================
# Template Functions
# ============================================

def get_template(generator_type: str, style: str = "full") -> str:
    """
    Get template for a generator type.
    
    Args:
        generator_type: Type of generator
        style: "minimal" or "full"
    
    Returns:
        Template string
    
    Raises:
        ValueError: If type or style is invalid
    
    Example:
        template = get_template("page", "minimal")
        template = get_template("component", "full")
    """
    if generator_type not in TEMPLATES:
        valid = ", ".join(TEMPLATES.keys())
        raise ValueError(
            f"Unknown generator type '{generator_type}'.\n"
            f"Valid types: {valid}"
        )
    
    if style not in ("minimal", "full"):
        raise ValueError(
            f"Unknown template style '{style}'.\n"
            f"Valid styles: minimal, full"
        )
    
    return TEMPLATES[generator_type][style]


def render_template(template: str, **context) -> str:
    """
    Render a template with context variables.
    
    Args:
        template: Template string with {placeholders}
        **context: Variables to substitute
    
    Returns:
        Rendered template
    
    Example:
        rendered = render_template(
            "Hello {name}!",
            name="World"
        )
        # "Hello World!"
    """
    return template.format(**context)


def list_generator_types() -> list[str]:
    """
    List all available generator types.
    
    Returns:
        List of type names
    """
    return list(TEMPLATES.keys())

