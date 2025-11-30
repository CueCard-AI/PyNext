"""
PyNext Proxy - Simple API Proxy Configuration

Easily proxy API requests to backend servers
without CORS issues.

Usage:
    # proxy.py - Auto-discovered
    from pynext import proxy
    
    @proxy("/api/external/*")
    def external_api():
        return "https://api.example.com"
    
    @proxy("/api/secure/*")
    def secure_api():
        return {
            "target": "https://secure.example.com",
            "headers": {"Authorization": f"Bearer {env('API_KEY')}"},
        }

Features:
- Decorator-based configuration
- Path rewriting support
- Header injection
- WebSocket proxy
- Dev-only proxies
"""

from .config import (
    ProxyConfig,
    ProxyRoute,
    proxy,
    load_proxy_config,
)
from .router import ProxyRouter, match_proxy
from .handler import ProxyHandler, proxy_request
from .middleware import ProxyMiddleware, create_proxy_middleware

__all__ = [
    # Config
    "ProxyConfig",
    "ProxyRoute",
    "proxy",
    "load_proxy_config",
    # Router
    "ProxyRouter",
    "match_proxy",
    # Handler
    "ProxyHandler",
    "proxy_request",
    # Middleware
    "ProxyMiddleware",
    "create_proxy_middleware",
]

