"""
File-based router for PyNext.

Scans the pages/ directory and creates routes based on file structure.
Supports:
- Page routes (index.py, about.py)
- Dynamic routes ([id].py, [...slug].py)
- Route groups ((folder))
- Layouts (layout.py)
- Templates (template.py)
- Special files (loading.py, error.py, not-found.py, unauthorized.py, forbidden.py)
- API routes (api/route.py)
"""

from __future__ import annotations

import importlib.util
import os
import sys
import contextvars
from pathlib import Path
from typing import Any, Callable, Optional, TYPE_CHECKING

from pynext.router.dynamic import (
    RoutePattern,
    file_path_to_route,
    match_route,
    sort_routes,
)
from pynext.router.trie import RouteTrie, LayoutCache, SpecialFilesCache
from pynext.router.groups import (
    is_route_group,
    strip_groups,
    scan_groups,
    GroupRegistry,
)

if TYPE_CHECKING:
    from pynext.core.component import PageComponent, LayoutComponent, LoadingComponent, ErrorComponent, NotFoundComponent
    from pynext.core.api_route import APIRoute
    from pynext.core.route_config import RouteConfig


# Special file names (without .py extension)
SPECIAL_FILES = frozenset([
    "layout", "template", "loading", "error", 
    "not-found", "not_found",
    "unauthorized", "forbidden",
])


# Context variables for request data
_current_params: contextvars.ContextVar[dict[str, str]] = contextvars.ContextVar(
    "current_params", default={}
)
_current_query: contextvars.ContextVar[dict[str, str]] = contextvars.ContextVar(
    "current_query", default={}
)


def get_params() -> dict[str, str]:
    """Get route parameters for the current request."""
    return _current_params.get()


def get_query() -> dict[str, str]:
    """Get query parameters for the current request."""
    return _current_query.get()


class Route:
    """A single route entry."""
    
    def __init__(
        self,
        pattern: RoutePattern,
        handler: "PageComponent",
        module_path: str,
        layouts: Optional[list["LayoutComponent"]] = None,
        loading: Optional["LoadingComponent"] = None,
        error: Optional["ErrorComponent"] = None,
        config: Optional["RouteConfig"] = None,
    ):
        self.pattern = pattern
        self.handler = handler
        self.module_path = module_path
        self.layouts = layouts or []
        self.loading = loading
        self.error = error
        self.config = config  # RouteConfig from @route_config decorator
    
    def match(self, path: str) -> Optional[dict[str, str]]:
        """Try to match this route against a path."""
        return match_route(path, self.pattern)
    
    async def handle(self, request) -> str:
        """Handle a request to this route."""
        # Set context variables
        params = self.match(request.url.path) or {}
        query = dict(request.query_params)
        
        params_token = _current_params.set(params)
        query_token = _current_query.set(query)
        
        try:
            return await self.handler.handle_request(request, layouts=self.layouts)
        finally:
            _current_params.reset(params_token)
            _current_query.reset(query_token)
    
    def __repr__(self) -> str:
        return f"Route({self.pattern.url_pattern!r})"


class APIRouteEntry:
    """An API route entry."""
    
    def __init__(
        self,
        pattern: RoutePattern,
        handler: "APIRoute",
        module_path: str,
    ):
        self.pattern = pattern
        self.handler = handler
        self.module_path = module_path
    
    def match(self, path: str) -> Optional[dict[str, str]]:
        """Try to match this route against a path."""
        return match_route(path, self.pattern)
    
    async def handle(self, request):
        """Handle an API request."""
        params = self.match(request.url.path) or {}
        query = dict(request.query_params)
        
        params_token = _current_params.set(params)
        query_token = _current_query.set(query)
        
        try:
            return await self.handler.handle(request)
        finally:
            _current_params.reset(params_token)
            _current_query.reset(query_token)
    
    def __repr__(self) -> str:
        return f"APIRoute({self.pattern.url_pattern!r})"


class FileRouter:
    """
    File-based router that scans a pages directory.
    
    Supports:
    - Page routes (index.py, about.py, [id].py)
    - Route groups ((folder)) - organize without affecting URLs
    - Layouts (layout.py)
    - Templates (template.py) - layouts that remount on navigation
    - Special files (loading.py, error.py, not-found.py, unauthorized.py, forbidden.py)
    - API routes (api/*/route.py)
    
    Performance optimizations:
    - Radix trie for O(1) static route matching, O(log n) dynamic
    - Pre-computed layout chains per directory
    - Route groups resolved at startup (O(1) lookup)
    - Cached special file resolution with inheritance
    
    Usage:
        router = FileRouter("./pages")
        route, params = router.match("/users/123")
    """
    
    def __init__(self, pages_dir: str = "pages", use_trie: bool = True):
        self.pages_dir = Path(pages_dir).resolve()
        self.routes: list[Route] = []
        self.api_routes: list[APIRouteEntry] = []
        self._modules: dict[str, Any] = {}
        
        # Use trie for fast matching (can be disabled for debugging)
        self._use_trie = use_trie
        self._page_trie: RouteTrie[Route] = RouteTrie()
        self._api_trie: RouteTrie[APIRouteEntry] = RouteTrie()
        
        # Route groups registry (built once at startup)
        self._groups: Optional[GroupRegistry] = None
        
        # Cached special components
        self._layout_cache = LayoutCache()
        self._loading_cache = SpecialFilesCache()
        self._error_cache = SpecialFilesCache()
        self._not_found: Optional["NotFoundComponent"] = None  # Global 404
        self._unauthorized: Optional["ErrorPage"] = None  # Global 401
        self._forbidden: Optional["ErrorPage"] = None  # Global 403
        
        # Template cache
        self._templates: dict[str, Any] = {}
        
        # Legacy dicts (kept for compatibility)
        self._layouts: dict[str, "LayoutComponent"] = {}
        self._loadings: dict[str, "LoadingComponent"] = {}
        self._errors: dict[str, "ErrorComponent"] = {}
    
    def scan(self) -> None:
        """Scan the pages directory and register routes."""
        self.routes = []
        self.api_routes = []
        self._modules = {}
        self._layouts = {}
        self._loadings = {}
        self._errors = {}
        self._templates = {}
        self._not_found = None
        self._unauthorized = None
        self._forbidden = None
        
        # Reset caches
        self._page_trie = RouteTrie()
        self._api_trie = RouteTrie()
        self._layout_cache.clear()
        self._loading_cache.clear()
        self._error_cache.clear()
        
        if not self.pages_dir.exists():
            return
        
        # Scan route groups first (O(n) once at startup)
        self._groups = scan_groups(self.pages_dir)
        
        # First pass: collect special files (layouts, loading, error, not-found, etc.)
        for py_file in self.pages_dir.rglob("*.py"):
            if "__pycache__" in str(py_file) or py_file.name.startswith("_"):
                continue
            
            stem = py_file.stem
            
            if stem in SPECIAL_FILES:
                self._register_special_file(py_file, stem)
        
        # Second pass: collect page and API routes
        for py_file in self.pages_dir.rglob("*.py"):
            if "__pycache__" in str(py_file) or py_file.name.startswith("_"):
                continue
            
            stem = py_file.stem
            
            # Skip special files
            if stem in SPECIAL_FILES:
                continue
            
            # Check if it's an API route
            if stem == "route":
                self._register_api_route(py_file)
            else:
                self._register_page(py_file)
        
        # Sort routes by priority (for fallback linear matching)
        self.routes = sorted(
            self.routes,
            key=lambda r: (
                r.pattern.is_optional_catch_all,
                r.pattern.is_catch_all,
                r.pattern.priority,
            )
        )
        
        self.api_routes = sorted(
            self.api_routes,
            key=lambda r: (
                r.pattern.is_optional_catch_all,
                r.pattern.is_catch_all,
                r.pattern.priority,
            )
        )
    
    def _register_special_file(self, file_path: Path, file_type: str) -> None:
        """Register a special file (layout, template, loading, error, not-found, unauthorized, forbidden)."""
        module = self._load_module(file_path)
        if not module:
            return
        
        # Get the directory path relative to pages_dir, stripping route groups
        rel_path = file_path.parent.relative_to(self.pages_dir)
        # Strip route groups from the path
        parts = [p for p in rel_path.parts if not is_route_group(p)]
        dir_path = str(Path(*parts)) if parts else ""
        if dir_path == ".":
            dir_path = ""
        
        if file_type == "layout":
            handler = self._find_layout_handler(module)
            if handler:
                self._layouts[dir_path] = handler
                self._layout_cache.add_layout(dir_path, handler)
        
        elif file_type == "template":
            handler = self._find_template_handler(module)
            if handler:
                self._templates[dir_path] = handler
        
        elif file_type == "loading":
            handler = self._find_loading_handler(module)
            if handler:
                self._loadings[dir_path] = handler
                self._loading_cache.add(dir_path, handler)
        
        elif file_type == "error":
            handler = self._find_error_handler(module)
            if handler:
                self._errors[dir_path] = handler
                self._error_cache.add(dir_path, handler)
        
        elif file_type in ("not-found", "not_found"):
            handler = self._find_not_found_handler(module)
            if handler:
                self._not_found = handler
        
        elif file_type == "unauthorized":
            handler = self._find_error_page_handler(module, 401)
            if handler:
                self._unauthorized = handler
        
        elif file_type == "forbidden":
            handler = self._find_error_page_handler(module, 403)
            if handler:
                self._forbidden = handler
    
    def _register_page(self, file_path: Path) -> None:
        """Register a page file as a route."""
        rel_path = file_path.relative_to(self.pages_dir)
        
        # Strip route groups from the path but keep the file structure
        # Example: (app)/users/[id].py -> users/[id].py
        parts = [p for p in rel_path.parts if not is_route_group(p)]
        stripped_path = str(Path(*parts)) if parts else str(rel_path)
        
        # Convert file path to route pattern
        route_pattern = file_path_to_route(stripped_path)
        
        module = self._load_module(file_path)
        if not module:
            return
        
        handler = self._find_page_handler(module)
        if not handler:
            return
        
        # Extract RouteConfig from handler or module
        route_config = self._extract_route_config(handler, module)
        
        # Get directory path for cache lookup
        dir_path = str(rel_path.parent)
        if dir_path == ".":
            dir_path = ""
        
        # Use cached layout chain (O(1) lookup after first access)
        layouts = self._layout_cache.get_chain(dir_path)
        
        # Use cached special file resolution
        loading = self._loading_cache.get(dir_path)
        error = self._error_cache.get(dir_path)
        
        route = Route(
            pattern=route_pattern,
            handler=handler,
            module_path=str(file_path),
            layouts=layouts,
            loading=loading,
            error=error,
            config=route_config,
        )
        
        self.routes.append(route)
        
        # Register config by path for lookup
        if route_config:
            from pynext.core.route_config import register_path_config
            register_path_config(route_pattern.pattern, route_config)
        
        # Add to trie for fast matching
        # Convert pattern to trie format: /users/:id instead of /users/[id]
        trie_pattern = self._to_trie_pattern(route_pattern)
        self._page_trie.insert(trie_pattern, route, priority=route_pattern.priority)
    
    def _register_api_route(self, file_path: Path) -> None:
        """Register an API route file."""
        from pynext.core.api_route import collect_api_handlers
        
        # Get route pattern from directory path
        rel_dir = file_path.parent.relative_to(self.pages_dir)
        route_pattern = file_path_to_route(str(rel_dir / "index.py"))
        
        module = self._load_module(file_path)
        if not module:
            return
        
        handler = collect_api_handlers(module)
        if not handler:
            return
        
        route = APIRouteEntry(
            pattern=route_pattern,
            handler=handler,
            module_path=str(file_path),
        )
        
        self.api_routes.append(route)
        
        # Add to trie for fast matching
        trie_pattern = self._to_trie_pattern(route_pattern)
        self._api_trie.insert(trie_pattern, route, priority=route_pattern.priority)
    
    def _to_trie_pattern(self, pattern: RoutePattern) -> str:
        """Convert a RoutePattern to trie format."""
        # url_pattern is already in format like /users/:id
        url = pattern.url_pattern
        
        # Convert catch-all (*slug) and optional catch-all (*slug?)
        if pattern.is_optional_catch_all and pattern.params:
            # [[...slug]] -> *slug?
            url = url.rsplit("/", 1)[0] + "/*" + pattern.params[0] + "?"
        elif pattern.is_catch_all and pattern.params:
            # [...slug] -> *slug
            url = url.rsplit("/", 1)[0] + "/*" + pattern.params[0]
        
        return url
    
    def _get_layouts_for_path(self, file_path: Path) -> list["LayoutComponent"]:
        """Get all layouts that apply to a file path, from root to innermost."""
        layouts = []
        
        # Get relative directory path
        rel_path = file_path.relative_to(self.pages_dir)
        parts = list(rel_path.parent.parts)
        
        # Check root layout
        if "" in self._layouts:
            layouts.append(self._layouts[""])
        
        # Check each parent directory
        current = ""
        for part in parts:
            current = str(Path(current) / part) if current else part
            if current in self._layouts:
                layouts.append(self._layouts[current])
        
        return layouts
    
    def _get_loading_for_path(self, file_path: Path) -> Optional["LoadingComponent"]:
        """Get the closest loading component for a file path."""
        rel_path = file_path.relative_to(self.pages_dir)
        parts = list(rel_path.parent.parts)
        
        # Check from innermost to root
        current = str(Path(*parts)) if parts else ""
        while True:
            if current in self._loadings:
                return self._loadings[current]
            
            if not current:
                break
            
            # Go to parent
            parts = current.split(os.sep)
            parts = parts[:-1] if parts else []
            current = os.sep.join(parts)
        
        # Check root
        if "" in self._loadings:
            return self._loadings[""]
        
        return None
    
    def _get_error_for_path(self, file_path: Path) -> Optional["ErrorComponent"]:
        """Get the closest error component for a file path."""
        rel_path = file_path.relative_to(self.pages_dir)
        parts = list(rel_path.parent.parts)
        
        # Check from innermost to root
        current = str(Path(*parts)) if parts else ""
        while True:
            if current in self._errors:
                return self._errors[current]
            
            if not current:
                break
            
            # Go to parent
            parts = current.split(os.sep)
            parts = parts[:-1] if parts else []
            current = os.sep.join(parts)
        
        # Check root
        if "" in self._errors:
            return self._errors[""]
        
        return None
    
    def _load_module(self, file_path: Path) -> Optional[Any]:
        """Load a Python module from a file path."""
        module_name = f"pynext_pages.{file_path.stem}_{id(file_path)}"
        
        try:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if not spec or not spec.loader:
                return None
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            self._modules[str(file_path)] = module
            return module
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return None
    
    def _extract_route_config(self, handler: Any, module: Any) -> Optional["RouteConfig"]:
        """
        Extract RouteConfig from page handler or module.
        
        Checks in order:
        1. __route_config__ attribute on handler (from @route_config decorator)
        2. route_config module-level variable
        
        Args:
            handler: Page handler function/component
            module: Module containing the handler
        
        Returns:
            RouteConfig if found, None otherwise
        """
        from pynext.core.route_config import RouteConfig, get_route_config
        
        # Check handler for decorator config
        config = get_route_config(handler)
        if config:
            return config
        
        # Check if handler is a wrapped component
        if hasattr(handler, "fn"):
            config = get_route_config(handler.fn)
            if config:
                return config
        
        # Check module-level config (alternative syntax)
        if hasattr(module, "route_config"):
            mod_config = module.route_config
            if isinstance(mod_config, RouteConfig):
                return mod_config
        
        # Check for config dict and convert
        if hasattr(module, "config") and isinstance(module.config, dict):
            try:
                return RouteConfig.from_dict(module.config)
            except Exception:
                pass
        
        return None
    
    def _find_page_handler(self, module: Any) -> Optional["PageComponent"]:
        """Find a page component in a module."""
        from pynext.core.component import PageComponent, Component
        
        # Look for explicit 'page' export
        if hasattr(module, "page") and isinstance(module.page, PageComponent):
            return module.page
        
        # Look for any PageComponent
        for name in dir(module):
            if name.startswith("_"):
                continue
            obj = getattr(module, name)
            if isinstance(obj, PageComponent):
                return obj
        
        # Look for a 'default' function and wrap it
        if hasattr(module, "default"):
            default = module.default
            if callable(default):
                from pynext.core.component import page
                return page(default)
        
        # Look for any Component (not a special type)
        for name in dir(module):
            if name.startswith("_"):
                continue
            obj = getattr(module, name)
            if isinstance(obj, Component) and not hasattr(obj, "is_layout"):
                # Upgrade to PageComponent
                from pynext.core.component import PageComponent, ComponentMeta
                meta = ComponentMeta(
                    name=obj.name,
                    fn=obj._fn,
                    is_page=True,
                )
                return PageComponent(meta)
        
        return None
    
    def _find_layout_handler(self, module: Any) -> Optional["LayoutComponent"]:
        """Find a layout component in a module."""
        from pynext.core.component import LayoutComponent
        
        for name in dir(module):
            if name.startswith("_"):
                continue
            obj = getattr(module, name)
            if isinstance(obj, LayoutComponent):
                return obj
        
        return None
    
    def _find_loading_handler(self, module: Any) -> Optional["LoadingComponent"]:
        """Find a loading component in a module."""
        from pynext.core.component import LoadingComponent
        
        for name in dir(module):
            if name.startswith("_"):
                continue
            obj = getattr(module, name)
            if isinstance(obj, LoadingComponent):
                return obj
        
        return None
    
    def _find_error_handler(self, module: Any) -> Optional["ErrorComponent"]:
        """Find an error component in a module."""
        from pynext.core.component import ErrorComponent
        
        for name in dir(module):
            if name.startswith("_"):
                continue
            obj = getattr(module, name)
            if isinstance(obj, ErrorComponent):
                return obj
        
        return None
    
    def _find_not_found_handler(self, module: Any) -> Optional["NotFoundComponent"]:
        """Find a not-found component in a module."""
        from pynext.core.component import NotFoundComponent
        
        for name in dir(module):
            if name.startswith("_"):
                continue
            obj = getattr(module, name)
            if isinstance(obj, NotFoundComponent):
                return obj
        
        return None
    
    def _find_template_handler(self, module: Any) -> Optional[Any]:
        """Find a template in a module."""
        from pynext.core.template import Template
        
        for name in dir(module):
            if name.startswith("_"):
                continue
            obj = getattr(module, name)
            if isinstance(obj, Template):
                return obj
        
        return None
    
    def _find_error_page_handler(self, module: Any, status_code: int) -> Optional[Any]:
        """Find an error page handler (401, 403) in a module."""
        from pynext.core.errors import ErrorPage, UnauthorizedPage, ForbiddenPage
        
        for name in dir(module):
            if name.startswith("_"):
                continue
            obj = getattr(module, name)
            if isinstance(obj, ErrorPage) and obj.status_code == status_code:
                return obj
        
        return None
    
    def match(self, path: str) -> tuple[Optional[Route], dict[str, str]]:
        """
        Find a route matching the given path.
        
        Uses radix trie for O(1) static routes, O(log n) dynamic routes.
        Falls back to linear search if trie is disabled.
        
        Returns (route, params) or (None, {}) if no match.
        """
        if self._use_trie:
            route, params = self._page_trie.match(path)
            if route is not None:
                return route, params
        
        # Fallback to linear search (for debugging or if trie fails)
        for route in self.routes:
            params = route.match(path)
            if params is not None:
                return route, params
        
        return None, {}
    
    def match_api(self, path: str) -> tuple[Optional[APIRouteEntry], dict[str, str]]:
        """
        Find an API route matching the given path.
        
        Uses radix trie for O(1) static routes, O(log n) dynamic routes.
        Falls back to linear search if trie is disabled.
        
        Returns (route, params) or (None, {}) if no match.
        """
        if self._use_trie:
            route, params = self._api_trie.match(path)
            if route is not None:
                return route, params
        
        # Fallback to linear search
        for route in self.api_routes:
            params = route.match(path)
            if params is not None:
                return route, params
        
        return None, {}
    
    def get_not_found(self) -> Optional["NotFoundComponent"]:
        """Get the global 404 handler."""
        return self._not_found
    
    def get_unauthorized(self) -> Optional[Any]:
        """Get the global 401 handler."""
        return self._unauthorized
    
    def get_forbidden(self) -> Optional[Any]:
        """Get the global 403 handler."""
        return self._forbidden
    
    def get_groups(self) -> Optional[GroupRegistry]:
        """Get the route groups registry."""
        return self._groups
    
    def get_template(self, dir_path: str) -> Optional[Any]:
        """Get a template for a directory path."""
        return self._templates.get(dir_path)
    
    def reload(self, file_path: Optional[str] = None) -> None:
        """
        Reload routes, optionally just a single file.
        
        Used for hot reloading during development.
        """
        if file_path:
            # Reload single file
            file_path = str(Path(file_path).resolve())
            
            # Remove old route for this file
            self.routes = [r for r in self.routes if r.module_path != file_path]
            self.api_routes = [r for r in self.api_routes if r.module_path != file_path]
            
            # Remove from sys.modules to force reimport
            module = self._modules.get(file_path)
            if module:
                module_name = module.__name__
                if module_name in sys.modules:
                    del sys.modules[module_name]
            
            # Re-register based on file type
            path = Path(file_path)
            stem = path.stem
            
            if stem in SPECIAL_FILES:
                self._register_special_file(path, stem)
            elif stem == "route":
                self._register_api_route(path)
            else:
                self._register_page(path)
            
            # Re-sort
            self.routes = sorted(
                self.routes,
                key=lambda r: (
                    r.pattern.is_optional_catch_all,
                    r.pattern.is_catch_all,
                    r.pattern.priority,
                )
            )
        else:
            # Full rescan
            self.scan()
    
    def get_routes_info(self) -> list[dict]:
        """Get information about all routes for debugging."""
        info = []
        
        for route in self.routes:
            info.append({
                "type": "page",
                "pattern": route.pattern.url_pattern,
                "file": route.module_path,
                "handler": route.handler.name,
                "layouts": len(route.layouts),
            })
        
        for route in self.api_routes:
            info.append({
                "type": "api",
                "pattern": route.pattern.url_pattern,
                "file": route.module_path,
                "methods": route.handler.methods,
            })
        
        return info

