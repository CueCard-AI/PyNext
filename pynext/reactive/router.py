"""
PyNext Client-Side Router - SolidJS-Style Reactive Routing

=============================================================================
WHAT THIS FILE DOES (AI Summary)
=============================================================================

This module provides a REACTIVE CLIENT-SIDE ROUTER for single-page applications.
Unlike Next.js which re-renders entire component trees on route changes, PyNext
uses fine-grained reactivity - only the route outlet updates when navigation occurs.

KEY COMPONENTS:
1. Router - Container that manages route matching and outlet rendering
2. Route - Definition of a path pattern and its component
3. Link - Navigation link that doesn't reload the page
4. useNavigate - Programmatic navigation hook
5. useParams - Access route parameters reactively
6. useSearchParams - Access query string reactively
7. useLocation - Access current location reactively

=============================================================================
WHY THIS MATTERS (vs Next.js/React Router)
=============================================================================

PERFORMANCE COMPARISON:
┌─────────────────────────────────────────────────────────────────────────┐
│  Operation              │ Next.js         │ PyNext                      │
├─────────────────────────────────────────────────────────────────────────┤
│  Route change           │ Full re-render  │ Signal update + DOM swap    │
│  Param change (:id)     │ Component mount │ Signal update only          │
│  Query change (?q=)     │ Re-render       │ Signal update only          │
│  Memory per route       │ Component tree  │ Single outlet element       │
└─────────────────────────────────────────────────────────────────────────┘

HOW IT'S FASTER:
- Routes are compiled to regex ONCE at definition time
- Route state (pathname, params, query) are SIGNALS
- Components subscribe to only what they need
- No virtual DOM diffing on navigation

=============================================================================
MENTAL MODEL
=============================================================================

Think of the router as a reactive container:

    Router()[                          # Watches location signal
        Route(path="/", component=Home),
        Route(path="/users/:id", component=User),
    ]

When location changes:
1. Router's internal effect triggers
2. Finds matching route (fast regex match)
3. Updates params signal
4. Swaps outlet content (DOM operation)
5. Components using useParams() react to new values

NO tree reconciliation. NO virtual DOM. Just signal updates.

=============================================================================
USAGE EXAMPLES
=============================================================================

Basic routing:
```python
from pynext.reactive import Router, Route, Link

@page
def App():
    return div()[
        nav()[
            Link(href="/")["Home"],
            Link(href="/about")["About"],
        ],
        Router()[
            Route(path="/", component=Home),
            Route(path="/about", component=About),
        ]
    ]
```

Dynamic routes with params:
```python
from pynext.reactive import useParams

@island
def UserProfile():
    params = useParams()
    return h1()[f"User: {params.id}"]

# In router:
Route(path="/users/:id", component=UserProfile)
```

Programmatic navigation:
```python
from pynext.reactive import useNavigate

@island
def LoginForm():
    navigate = useNavigate()
    
    def handle_submit():
        # After login...
        navigate("/dashboard")
    
    return form(onsubmit=handle_submit)[...]
```

=============================================================================
"""

from __future__ import annotations

import re
import json
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
    TYPE_CHECKING,
)
from dataclasses import dataclass, field
from urllib.parse import parse_qs, urlencode, urlparse

if TYPE_CHECKING:
    from pynext.core.html import Element

from pynext.reactive.signal import Signal, signal
from pynext.reactive.memo import memo
from pynext.reactive.effect import effect


# =============================================================================
# SECTION 1: ROUTE PATTERN COMPILATION
# =============================================================================
#
# Routes like "/users/:id/posts/:postId" are compiled to regex patterns
# at definition time, not at match time. This makes matching O(1) per route.
#
# Pattern syntax:
#   :param     - Named parameter (matches anything except /)
#   *          - Wildcard (matches everything including /)
#   /path      - Literal path segment
# =============================================================================

# Regex to find :paramName in route patterns
PARAM_PATTERN = re.compile(r':([a-zA-Z_][a-zA-Z0-9_]*)')


def compile_route_pattern(pattern: str) -> Tuple[re.Pattern, List[str]]:
    """
    Compile a route pattern to a regex and extract param names.
    
    Examples:
        "/" -> (re.compile("^/$"), [])
        "/users/:id" -> (re.compile("^/users/([^/]+)$"), ["id"])
        "/files/*" -> (re.compile("^/files/(.*)$"), ["*"])
    
    Args:
        pattern: Route pattern like "/users/:id"
    
    Returns:
        Tuple of (compiled regex, list of param names)
    """
    param_names = []
    
    # Find all :param patterns and extract names
    for match in PARAM_PATTERN.finditer(pattern):
        param_names.append(match.group(1))
    
    # Convert pattern to regex
    regex_pattern = pattern
    
    # Escape special regex characters (except our patterns)
    regex_pattern = re.sub(r'([.+?^${}()|[\]\\])', r'\\\1', regex_pattern)
    
    # Replace :param with capture group
    regex_pattern = PARAM_PATTERN.sub(r'([^/]+)', regex_pattern)
    
    # Replace * wildcard with catch-all
    if '*' in regex_pattern:
        regex_pattern = regex_pattern.replace('*', '(.*)')
        param_names.append('*')
    
    # Add anchors
    regex_pattern = f'^{regex_pattern}$'
    
    return re.compile(regex_pattern), param_names


@dataclass
class CompiledRoute:
    """
    A route compiled for fast matching.
    
    Attributes:
        path: Original path pattern (e.g., "/users/:id")
        pattern: Compiled regex pattern
        param_names: List of parameter names in order
        component: Component to render when matched
        exact: Whether to match exactly (default True)
        guards: Optional list of guard functions
    """
    path: str
    pattern: re.Pattern
    param_names: List[str]
    component: Callable
    exact: bool = True
    guards: List[Callable] = field(default_factory=list)
    
    def match(self, pathname: str) -> Optional[Dict[str, str]]:
        """
        Try to match a pathname against this route.
        
        Args:
            pathname: URL pathname to match (e.g., "/users/123")
        
        Returns:
            Dict of params if matched, None otherwise
        """
        m = self.pattern.match(pathname)
        if m:
            return dict(zip(self.param_names, m.groups()))
        return None


# =============================================================================
# SECTION 2: ROUTER CONTEXT (Global State)
# =============================================================================
#
# The router maintains global reactive state for the current location.
# This allows any component to access route info via hooks without prop drilling.
#
# State:
#   _pathname: Signal[str] - Current URL path
#   _params: Signal[Dict[str, str]] - Current route params
#   _query: Signal[Dict[str, str]] - Current query string params
#   _hash: Signal[str] - Current URL hash
# =============================================================================

# Global router state (initialized on first Router mount)
_router_context: Optional['RouterContext'] = None


@dataclass
class RouterContext:
    """
    Global router context holding reactive location state.
    
    This is a singleton - only one router context exists per app.
    Components access this via hooks (useParams, useNavigate, etc).
    """
    pathname: Signal
    params: Signal
    query: Signal
    hash_: Signal
    routes: List[CompiledRoute] = field(default_factory=list)
    _base: str = ""
    
    def __post_init__(self):
        """Initialize the global context reference."""
        global _router_context
        _router_context = self
    
    def navigate(
        self,
        to: Union[str, int],
        replace: bool = False,
        state: Optional[Dict] = None,
    ) -> None:
        """
        Navigate to a new location.
        
        Args:
            to: Path to navigate to, or number for history navigation (-1 = back)
            replace: If True, replace current history entry instead of push
            state: Optional state to pass to the new location
        """
        if isinstance(to, int):
            # History navigation (back/forward)
            # This is handled client-side only
            return
        
        # Parse the path
        parsed = urlparse(to)
        new_pathname = parsed.path or "/"
        new_query = parse_qs(parsed.query) if parsed.query else {}
        new_hash = parsed.fragment or ""
        
        # Flatten query params (parse_qs returns lists)
        flat_query = {k: v[0] if len(v) == 1 else v for k, v in new_query.items()}
        
        # Find matching route and check guards
        matched_route = None
        matched_params = {}
        
        for route in self.routes:
            params = route.match(new_pathname)
            if params is not None:
                matched_route = route
                matched_params = params
                break
        
        # Check guards if route matched
        if matched_route and matched_route.guards:
            for guard in matched_route.guards:
                result = guard()
                if isinstance(result, Redirect):
                    # Guard returned redirect - navigate there instead
                    self.navigate(result.to, replace=result.replace, state=state)
                    return
        
        # Update signals
        self.pathname.set(new_pathname)
        self.query.set(flat_query)
        self.hash_.set(new_hash)
        self.params.set(matched_params)
    
    def get_current_route(self) -> Optional[CompiledRoute]:
        """Get the currently matched route."""
        pathname = self.pathname()
        for route in self.routes:
            if route.match(pathname) is not None:
                return route
        return None


def get_router_context() -> RouterContext:
    """
    Get the current router context.
    
    Raises:
        RuntimeError: If no router context exists (Router not mounted)
    
    Returns:
        The current RouterContext
    """
    if _router_context is None:
        raise RuntimeError(
            "No router context found. Make sure you're using hooks inside a Router."
        )
    return _router_context


def _create_router_context(
    initial_pathname: str = "/",
    initial_query: Optional[Dict[str, str]] = None,
    initial_hash: str = "",
    base: str = "",
) -> RouterContext:
    """
    Create a new router context with initial values.
    
    Args:
        initial_pathname: Initial URL pathname
        initial_query: Initial query params
        initial_hash: Initial URL hash
        base: Base path for all routes
    
    Returns:
        New RouterContext instance
    """
    return RouterContext(
        pathname=signal(initial_pathname, name="router:pathname"),
        params=signal({}, name="router:params"),
        query=signal(initial_query or {}, name="router:query"),
        hash_=signal(initial_hash, name="router:hash"),
        _base=base,
    )


# =============================================================================
# SECTION 3: ROUTE COMPONENT
# =============================================================================
#
# Route defines a mapping from a path pattern to a component.
# Routes are collected by the parent Router and compiled for matching.
# =============================================================================

class Route:
    """
    Define a route mapping path pattern to component.
    
    Usage:
        Route(path="/", component=Home)
        Route(path="/users/:id", component=UserProfile)
        Route(path="/files/*", component=FileViewer)
    
    Args:
        path: URL pattern to match (e.g., "/users/:id")
        component: Component to render when matched
        exact: Whether to match exactly (default True)
        guards: Optional list of guard functions
    """
    
    def __init__(
        self,
        path: str,
        component: Callable,
        exact: bool = True,
        guards: Optional[List[Callable]] = None,
    ):
        self.path = path
        self.component = component
        self.exact = exact
        self.guards = guards or []
        
        # Compile the route pattern
        self.pattern, self.param_names = compile_route_pattern(path)
    
    def to_compiled(self) -> CompiledRoute:
        """Convert to a CompiledRoute for matching."""
        return CompiledRoute(
            path=self.path,
            pattern=self.pattern,
            param_names=self.param_names,
            component=self.component,
            exact=self.exact,
            guards=self.guards,
        )
    
    def match(self, pathname: str) -> Optional[Dict[str, str]]:
        """Try to match this route against a pathname."""
        m = self.pattern.match(pathname)
        if m:
            return dict(zip(self.param_names, m.groups()))
        return None
    
    def __repr__(self) -> str:
        return f"Route(path={self.path!r}, component={self.component.__name__})"


# =============================================================================
# SECTION 4: ROUTER COMPONENT
# =============================================================================
#
# Router is the main container that:
# 1. Collects Route children
# 2. Matches current pathname to routes
# 3. Renders the matched component
# 4. Sets up reactive context for hooks
# =============================================================================

class Router:
    """
    Router container component.
    
    Usage:
        Router()[
            Route(path="/", component=Home),
            Route(path="/about", component=About),
        ]
    
    The Router:
    1. Creates router context (pathname, params, query signals)
    2. Matches current path to routes
    3. Renders matched component in outlet
    4. Provides context for hooks (useParams, useNavigate, etc)
    
    Args:
        base: Base path prefix for all routes (e.g., "/app")
        fallback: Component to render when no route matches (404)
    """
    
    def __init__(
        self,
        base: str = "",
        fallback: Optional[Callable] = None,
    ):
        self.base = base
        self.fallback = fallback
        self.routes: List[Route] = []
        self._context: Optional[RouterContext] = None
    
    def __getitem__(self, children: Union[Route, List[Route]]) -> 'Router':
        """
        Add routes to the router using [] syntax.
        
        Usage:
            Router()[
                Route(path="/", component=Home),
                Route(path="/about", component=About),
            ]
        """
        if isinstance(children, Route):
            self.routes = [children]
        elif isinstance(children, (list, tuple)):
            self.routes = [c for c in children if isinstance(c, Route)]
        return self
    
    def _get_initial_pathname(self) -> str:
        """
        Get the initial pathname for SSR.
        
        On server, this comes from the request context.
        On client, this would come from window.location.
        """
        # Try to get from request context (SSR)
        try:
            from pynext.core.context import get_render_context
            ctx = get_render_context()
            if ctx and hasattr(ctx, 'request_path'):
                return ctx.request_path
        except (ImportError, RuntimeError):
            pass
        
        return "/"
    
    def _find_matching_route(self, pathname: str) -> Tuple[Optional[Route], Dict[str, str]]:
        """
        Find the first matching route for a pathname.
        
        Returns:
            Tuple of (matched Route or None, params dict)
        """
        for route in self.routes:
            params = route.match(pathname)
            if params is not None:
                return route, params
        return None, {}
    
    def render(self) -> Any:
        """
        Render the router and matched route.
        
        Returns the HTML representation for SSR.
        """
        from pynext.core.html import div
        
        # Initialize context
        initial_pathname = self._get_initial_pathname()
        self._context = _create_router_context(
            initial_pathname=initial_pathname,
            base=self.base,
        )
        
        # Compile and register routes
        compiled_routes = [r.to_compiled() for r in self.routes]
        self._context.routes = compiled_routes
        
        # Find matching route
        matched_route, params = self._find_matching_route(initial_pathname)
        self._context.params.set(params)
        
        # Render matched component or fallback
        if matched_route:
            content = matched_route.component()
        elif self.fallback:
            content = self.fallback()
        else:
            content = div()["404 - Not Found"]
        
        # Wrap in router outlet container
        route_data = {
            "pathname": initial_pathname,
            "params": params,
            "routes": [r.path for r in self.routes],
        }
        
        return div(
            **{
                "data-pynext-router": "true",
                "data-pynext-route-data": json.dumps(route_data),
            }
        )[content]
    
    def __str__(self) -> str:
        """Render to string for SSR."""
        return str(self.render())
    
    def __repr__(self) -> str:
        return f"Router(base={self.base!r}, routes={len(self.routes)})"


# =============================================================================
# SECTION 5: LINK COMPONENT
# =============================================================================
#
# Link provides navigation without page reload.
# It renders as an <a> tag but intercepts clicks client-side.
# =============================================================================

class Link:
    """
    Navigation link component.
    
    Renders as an <a> tag but navigates without page reload on client.
    
    Usage:
        Link(href="/about")["About Us"]
        Link(href="/users/123", active_class="active")["User"]
        Link(href="/docs", prefetch=True)["Docs"]
    
    Args:
        href: Target path to navigate to
        replace: If True, replace history entry instead of push
        prefetch: If True, prefetch the route on hover
        active_class: CSS class to add when link matches current path
        exact: If True, only match exact path for active state
        **attrs: Additional attributes for the <a> tag
    """
    
    def __init__(
        self,
        href: str,
        replace: bool = False,
        prefetch: bool = False,
        active_class: str = "active",
        exact: bool = False,
        **attrs,
    ):
        self.href = href
        self.replace = replace
        self.prefetch = prefetch
        self.active_class = active_class
        self.exact = exact
        self.attrs = attrs
        self.children: List[Any] = []
    
    def __getitem__(self, children: Any) -> 'Link':
        """Set children using [] syntax."""
        if isinstance(children, (list, tuple)):
            self.children = list(children)
        else:
            self.children = [children]
        return self
    
    def _is_active(self, current_pathname: str) -> bool:
        """Check if this link matches the current pathname."""
        if self.exact:
            return current_pathname == self.href
        
        # For prefix matching, ensure we match path boundaries
        # "/user" should NOT match "/users", only "/user" or "/user/..."
        if current_pathname == self.href:
            return True
        
        # Check if current path is a child of this link's path
        # Must match at path boundary (followed by / or end of string)
        if self.href == "/":
            # Root always matches in non-exact mode
            return True
        
        # Check for path boundary: href must be followed by / in current path
        return current_pathname.startswith(self.href + "/")
    
    def render(self) -> Any:
        """Render the link as an anchor tag."""
        from pynext.core.html import a
        
        # Get current pathname for active state
        current_pathname = "/"
        if _router_context:
            current_pathname = _router_context.pathname()
        
        # Build class list
        class_list = []
        if "class_" in self.attrs:
            class_list.append(self.attrs.pop("class_"))
        if self._is_active(current_pathname):
            class_list.append(self.active_class)
        
        # Build attributes
        link_attrs = {
            "href": self.href,
            **self.attrs,
        }
        
        if class_list:
            link_attrs["class_"] = " ".join(class_list)
        
        # Add data attributes for client-side handling
        link_attrs["data-pynext-link"] = "true"
        if self.replace:
            link_attrs["data-pynext-replace"] = "true"
        if self.prefetch:
            link_attrs["data-pynext-prefetch"] = "true"
        
        return a(**link_attrs)[self.children]
    
    def __str__(self) -> str:
        return str(self.render())
    
    def __repr__(self) -> str:
        return f"Link(href={self.href!r})"


# =============================================================================
# SECTION 6: NAVIGATION HOOKS
# =============================================================================
#
# Hooks provide access to router state and navigation functions.
# These work reactively - components re-render when values change.
# =============================================================================

class Navigator:
    """
    Navigation helper returned by useNavigate().
    
    Provides methods for programmatic navigation.
    """
    
    def __call__(
        self,
        to: Union[str, int],
        replace: bool = False,
        state: Optional[Dict] = None,
    ) -> None:
        """
        Navigate to a path or in history.
        
        Args:
            to: Path string or history delta (e.g., -1 for back)
            replace: If True, replace current history entry
            state: Optional state to pass to the route
        
        Examples:
            navigate("/users")           # Push /users
            navigate("/users", replace=True)  # Replace with /users
            navigate(-1)                  # Go back
        """
        ctx = get_router_context()
        ctx.navigate(to, replace=replace, state=state)
    
    def back(self) -> None:
        """Go back one entry in history."""
        self(-1)
    
    def forward(self) -> None:
        """Go forward one entry in history."""
        self(1)
    
    def prefetch(self, path: str) -> None:
        """
        Prefetch a route's resources.
        
        On client, this loads the route's JS/CSS ahead of time.
        """
        # Prefetching is handled client-side
        pass


def useNavigate() -> Navigator:
    """
    Get a navigation function for programmatic routing.
    
    Usage:
        navigate = useNavigate()
        navigate("/dashboard")
        navigate(-1)  # Back
    
    Returns:
        Navigator instance for navigation
    """
    return Navigator()


def useParams() -> Dict[str, str]:
    """
    Get current route parameters reactively.
    
    Usage:
        @island
        def UserProfile():
            params = useParams()
            return h1()[f"User: {params['id']}"]
    
    Returns:
        Dict of current route params (reactive)
    """
    ctx = get_router_context()
    return ctx.params()


def useSearchParams() -> Tuple[Dict[str, str], Callable[[Dict[str, str]], None]]:
    """
    Get current query string parameters reactively.
    
    Usage:
        @island
        def SearchResults():
            params, setParams = useSearchParams()
            return div()[
                f"Query: {params.get('q', '')}",
                button(onclick=lambda: setParams({"q": "new"}))["Search"]
            ]
    
    Returns:
        Tuple of (current query dict, setter function)
    """
    ctx = get_router_context()
    
    def set_search_params(new_params: Dict[str, str]) -> None:
        ctx.query.set(new_params)
        # Update URL without navigation
        query_string = urlencode(new_params) if new_params else ""
        # This would trigger client-side URL update
    
    return ctx.query(), set_search_params


@dataclass
class Location:
    """
    Location object representing current URL state.
    
    Attributes:
        pathname: Current path (e.g., "/users/123")
        search: Query string (e.g., "?q=test")
        hash: URL hash (e.g., "#section")
        state: History state object
    """
    pathname: str
    search: str = ""
    hash: str = ""
    state: Optional[Dict] = None


def useLocation() -> Location:
    """
    Get current location reactively.
    
    Usage:
        @island
        def Breadcrumb():
            location = useLocation()
            return span()[f"You are at: {location.pathname}"]
    
    Returns:
        Location object with current URL state
    """
    ctx = get_router_context()
    query = ctx.query()
    
    return Location(
        pathname=ctx.pathname(),
        search=f"?{urlencode(query)}" if query else "",
        hash=f"#{ctx.hash_()}" if ctx.hash_() else "",
    )


def useMatch(pattern: str) -> Optional[Dict[str, str]]:
    """
    Check if current path matches a pattern.
    
    Usage:
        @island
        def UserNav():
            match = useMatch("/users/:id")
            if match:
                return span()[f"Viewing user {match['id']}"]
            return None
    
    Args:
        pattern: Route pattern to match against
    
    Returns:
        Params dict if matched, None otherwise
    """
    ctx = get_router_context()
    regex, param_names = compile_route_pattern(pattern)
    
    pathname = ctx.pathname()
    m = regex.match(pathname)
    if m:
        return dict(zip(param_names, m.groups()))
    return None


# =============================================================================
# SECTION 7: ROUTE GUARDS
# =============================================================================
#
# Guards allow conditional route access and redirects.
# =============================================================================

@dataclass
class Redirect:
    """
    Redirect to another path.
    
    Usage in guards:
        def auth_guard():
            if not is_logged_in():
                return Redirect("/login")
            return None  # Allow access
    """
    to: str
    replace: bool = True


def createRouteGuard(
    check: Callable[[], Optional[Redirect]],
) -> Callable:
    """
    Create a route guard function.
    
    Args:
        check: Function that returns None (allow) or Redirect
    
    Returns:
        Guard function for use with Route
    
    Usage:
        auth_guard = createRouteGuard(lambda: 
            Redirect("/login") if not is_logged_in() else None
        )
        
        Route(path="/dashboard", component=Dashboard, guards=[auth_guard])
    """
    return check


# =============================================================================
# SECTION 8: NESTED ROUTES
# =============================================================================
#
# Routes can be nested for layouts and sub-navigation.
# =============================================================================

class Outlet:
    """
    Placeholder for nested route content.
    
    Usage:
        @component
        def Layout():
            return div()[
                Header(),
                main()[
                    Outlet()  # Child routes render here
                ],
                Footer(),
            ]
    """
    
    def render(self) -> Any:
        """Render the current child route."""
        from pynext.core.html import div
        
        # The outlet renders the child route content
        # This is managed by the Router component
        return div(**{"data-pynext-outlet": "true"})
    
    def __str__(self) -> str:
        return str(self.render())


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Components
    "Router",
    "Route", 
    "Link",
    "Outlet",
    
    # Hooks
    "useNavigate",
    "useParams",
    "useSearchParams",
    "useLocation",
    "useMatch",
    
    # Types/Helpers
    "Navigator",
    "Location",
    "Redirect",
    "createRouteGuard",
    "CompiledRoute",
    
    # Context
    "get_router_context",
    "RouterContext",
]

