"""
PyNext Middleware Module.

Provides edge-like middleware for:
- Request interception
- Redirects and rewrites
- Authentication
- Rate limiting
- Geo/device detection
"""

from pynext.middleware.edge import (
    middleware,
    MiddlewareConfig,
    MiddlewareContext,
    MiddlewareResponse,
    NextResponse,
    get_middleware_registry,
)

from pynext.middleware.response import (
    redirect,
    rewrite,
    next_response,
    json_response,
)

from pynext.middleware.router import (
    MiddlewareRouter,
    MiddlewareMatcher,
    compile_matcher,
)

__all__ = [
    # Decorators
    "middleware",
    # Config
    "MiddlewareConfig",
    "MiddlewareContext",
    "MiddlewareResponse",
    "NextResponse",
    "get_middleware_registry",
    # Response helpers
    "redirect",
    "rewrite",
    "next_response",
    "json_response",
    # Router
    "MiddlewareRouter",
    "MiddlewareMatcher",
    "compile_matcher",
]

