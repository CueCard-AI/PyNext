"""
Proxy Configuration - Decorator-Based Setup

Define proxy routes using simple decorators.
Configuration is auto-discovered from proxy.py.

Example:
    @proxy("/api/users/*")
    def users_api():
        return "https://users.example.com"
"""

from __future__ import annotations

import inspect
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union
from functools import wraps


@dataclass
class ProxyRoute:
    """
    A single proxy route configuration.
    
    Attributes:
        pattern: URL pattern to match (e.g., "/api/*")
        target: Target URL or URL generator
        rewrite: Path rewrite pattern (e.g., "/v2/$1")
        headers: Headers to add to proxied requests
        websocket: Whether this is a WebSocket proxy
        dev_only: Only active in development mode
        timeout: Request timeout in seconds
        name: Route name for debugging
    """
    pattern: str
    target: Union[str, Callable[[], Union[str, Dict[str, Any]]]]
    rewrite: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    websocket: bool = False
    dev_only: bool = False
    timeout: int = 30
    name: Optional[str] = None
    
    def get_target(self) -> str:
        """Resolve target URL."""
        if callable(self.target):
            result = self.target()
            if isinstance(result, dict):
                return result.get("target", "")
            return result
        return self.target
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers including from callable target."""
        headers = self.headers.copy()
        
        if callable(self.target):
            result = self.target()
            if isinstance(result, dict):
                headers.update(result.get("headers", {}))
        
        return headers
    
    def is_active(self, is_dev: bool = False) -> bool:
        """Check if route is active in current mode."""
        if self.dev_only and not is_dev:
            return False
        return True
    
    def match(self, path: str) -> Optional[Dict[str, str]]:
        """
        Match path against pattern.
        
        Returns captured groups if matched, None otherwise.
        """
        import re
        
        # Convert glob pattern to regex
        regex_pattern = self.pattern
        regex_pattern = regex_pattern.replace(".", r"\.")
        regex_pattern = regex_pattern.replace("*", "(.*)")
        regex_pattern = f"^{regex_pattern}$"
        
        match = re.match(regex_pattern, path)
        if not match:
            return None
        
        return {
            f"${i+1}": group
            for i, group in enumerate(match.groups())
        }
    
    def rewrite_path(self, path: str, groups: Dict[str, str]) -> str:
        """Apply path rewriting."""
        if not self.rewrite:
            # Default: strip the matched prefix
            return path
        
        result = self.rewrite
        for key, value in groups.items():
            result = result.replace(key, value)
        
        return result


@dataclass
class ProxyConfig:
    """
    Complete proxy configuration.
    
    Attributes:
        routes: List of proxy routes
        global_headers: Headers for all proxied requests
        default_timeout: Default timeout for all routes
    """
    routes: List[ProxyRoute] = field(default_factory=list)
    global_headers: Dict[str, str] = field(default_factory=dict)
    default_timeout: int = 30
    
    def add_route(self, route: ProxyRoute):
        """Add a route to the configuration."""
        self.routes.append(route)
    
    def find_route(
        self,
        path: str,
        is_dev: bool = False,
    ) -> Optional[tuple[ProxyRoute, Dict[str, str]]]:
        """
        Find matching route for a path.
        
        Returns (route, captured_groups) or None.
        """
        for route in self.routes:
            if not route.is_active(is_dev):
                continue
            
            groups = route.match(path)
            if groups is not None:
                return route, groups
        
        return None


# Global config instance
_config = ProxyConfig()


def get_proxy_config() -> ProxyConfig:
    """Get the global proxy configuration."""
    return _config


def proxy(
    pattern: str,
    rewrite: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    websocket: bool = False,
    dev_only: bool = False,
    timeout: int = 30,
) -> Callable:
    """
    Decorator to define a proxy route.
    
    The decorated function should return a target URL
    or a dict with target and additional configuration.
    
    Args:
        pattern: URL pattern to match (e.g., "/api/*")
        rewrite: Path rewrite pattern
        headers: Headers to add
        websocket: Enable WebSocket proxy
        dev_only: Only active in development
        timeout: Request timeout in seconds
        
    Returns:
        Decorator function
        
    Example:
        # Simple proxy
        @proxy("/api/users/*")
        def users_api():
            return "https://users.example.com"
        
        # With path rewriting
        @proxy("/api/v1/*", rewrite="/v2/$1")
        def api_v1():
            return "https://api.example.com"
        
        # With dynamic headers
        @proxy("/api/secure/*")
        def secure_api():
            return {
                "target": "https://secure.example.com",
                "headers": {
                    "Authorization": f"Bearer {os.environ.get('API_KEY')}",
                },
            }
        
        # WebSocket proxy
        @proxy("/ws/*", websocket=True)
        def ws_proxy():
            return "ws://realtime.example.com"
        
        # Dev-only mock API
        @proxy("/api/mock/*", dev_only=True)
        def mock_api():
            return "http://localhost:3001"
    """
    def decorator(func: Callable) -> Callable:
        route = ProxyRoute(
            pattern=pattern,
            target=func,
            rewrite=rewrite,
            headers=headers or {},
            websocket=websocket,
            dev_only=dev_only,
            timeout=timeout,
            name=func.__name__,
        )
        
        _config.add_route(route)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        wrapper._proxy_route = route
        return wrapper
    
    return decorator


def load_proxy_config(
    path: Optional[Path] = None,
    app_dir: Optional[Path] = None,
) -> ProxyConfig:
    """
    Load proxy configuration from proxy.py.
    
    Looks for proxy.py in the app directory and imports it,
    which registers routes via the @proxy decorator.
    
    Args:
        path: Direct path to proxy.py
        app_dir: App directory to search for proxy.py
        
    Returns:
        ProxyConfig with loaded routes
    """
    import importlib.util
    
    # Find proxy.py
    if path is None:
        if app_dir is None:
            app_dir = Path.cwd()
        
        # Look in common locations
        for loc in ["proxy.py", "app/proxy.py", "pages/proxy.py"]:
            candidate = app_dir / loc
            if candidate.exists():
                path = candidate
                break
    
    if path is None or not path.exists():
        return _config
    
    # Import the proxy module to register decorators
    spec = importlib.util.spec_from_file_location("proxy", path)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    
    return _config


def clear_proxy_config():
    """Clear all proxy routes (mainly for testing)."""
    global _config
    _config = ProxyConfig()

