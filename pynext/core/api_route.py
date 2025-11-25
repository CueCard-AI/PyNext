"""
API Route handlers for PyNext.

Provides Next.js-style route.py handlers with HTTP method exports.
"""

from __future__ import annotations

import asyncio
import functools
import inspect
from typing import Any, Callable, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import Request
    from fastapi.responses import Response, JSONResponse


class APIHandler:
    """
    Wrapper for API route handlers.
    
    Supports both sync and async handlers with automatic
    response handling.
    """
    
    def __init__(
        self,
        fn: Callable,
        method: str,
    ):
        self._fn = fn
        self._method = method.upper()
        self._is_async = asyncio.iscoroutinefunction(fn)
        functools.update_wrapper(self, fn)
    
    async def __call__(self, request: "Request") -> "Response":
        """Handle the request."""
        from fastapi.responses import JSONResponse, Response
        
        try:
            # Call handler
            if self._is_async:
                result = await self._fn(request)
            else:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, lambda: self._fn(request))
            
            # Handle response
            if isinstance(result, Response):
                return result
            
            # Auto-convert dict/list to JSON
            if isinstance(result, (dict, list)):
                return JSONResponse(result)
            
            # String response
            if isinstance(result, str):
                return Response(content=result, media_type="text/plain")
            
            # None - return 204 No Content
            if result is None:
                return Response(status_code=204)
            
            # Try JSON serialization
            return JSONResponse(result)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JSONResponse(
                {"error": str(e)},
                status_code=500
            )
    
    @property
    def method(self) -> str:
        return self._method


class APIRoute:
    """
    Container for all HTTP method handlers in a route file.
    
    Collects GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS handlers.
    """
    
    METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]
    
    def __init__(
        self,
        handlers: dict[str, APIHandler],
        route_path: str,
    ):
        self._handlers = handlers
        self._route_path = route_path
    
    def get_handler(self, method: str) -> Optional[APIHandler]:
        """Get handler for a specific HTTP method."""
        return self._handlers.get(method.upper())
    
    @property
    def methods(self) -> list[str]:
        """Get list of supported HTTP methods."""
        return list(self._handlers.keys())
    
    @property
    def route_path(self) -> str:
        return self._route_path
    
    async def handle(self, request: "Request") -> "Response":
        """Handle a request, dispatching to the appropriate method handler."""
        from fastapi.responses import JSONResponse
        
        method = request.method.upper()
        handler = self.get_handler(method)
        
        if not handler:
            # Return 405 Method Not Allowed
            return JSONResponse(
                {"error": f"Method {method} not allowed"},
                status_code=405,
                headers={"Allow": ", ".join(self.methods)}
            )
        
        return await handler(request)


def api_route(fn: Callable) -> APIHandler:
    """
    Decorator to mark a function as an API route handler.
    
    The function name determines the HTTP method (GET, POST, etc.).
    
    Usage:
        # pages/api/users/route.py
        
        @api_route
        async def GET(request):
            users = await get_users()
            return {"users": users}
        
        @api_route
        async def POST(request):
            data = await request.json()
            user = await create_user(data)
            return JSONResponse({"user": user}, status_code=201)
    """
    method = fn.__name__.upper()
    
    if method not in APIRoute.METHODS:
        raise ValueError(
            f"Invalid API route method: {fn.__name__}. "
            f"Must be one of: {', '.join(APIRoute.METHODS)}"
        )
    
    return APIHandler(fn, method)


def collect_api_handlers(module: Any) -> Optional[APIRoute]:
    """
    Collect all API handlers from a route.py module.
    
    Looks for functions decorated with @api_route.
    """
    handlers = {}
    
    for name in dir(module):
        if name.startswith("_"):
            continue
        
        obj = getattr(module, name)
        
        if isinstance(obj, APIHandler):
            handlers[obj.method] = obj
    
    if not handlers:
        return None
    
    # Get route path from module file
    route_path = getattr(module, "__file__", "unknown")
    
    return APIRoute(handlers, route_path)


# Response helpers (re-exported from FastAPI for convenience)

def JSONResponse(
    content: Any,
    status_code: int = 200,
    headers: Optional[dict[str, str]] = None,
    **kwargs
) -> "Response":
    """Create a JSON response."""
    from fastapi.responses import JSONResponse as FastAPIJSONResponse
    return FastAPIJSONResponse(content, status_code=status_code, headers=headers, **kwargs)


def Response(
    content: Any = None,
    status_code: int = 200,
    headers: Optional[dict[str, str]] = None,
    media_type: Optional[str] = None,
    **kwargs
) -> "Response":
    """Create a generic response."""
    from fastapi.responses import Response as FastAPIResponse
    return FastAPIResponse(content=content, status_code=status_code, headers=headers, media_type=media_type, **kwargs)


def RedirectResponse(
    url: str,
    status_code: int = 307,
    headers: Optional[dict[str, str]] = None,
) -> "Response":
    """Create a redirect response."""
    from fastapi.responses import RedirectResponse as FastAPIRedirectResponse
    return FastAPIRedirectResponse(url=url, status_code=status_code, headers=headers)


def HTMLResponse(
    content: str,
    status_code: int = 200,
    headers: Optional[dict[str, str]] = None,
) -> "Response":
    """Create an HTML response."""
    from fastapi.responses import HTMLResponse as FastAPIHTMLResponse
    return FastAPIHTMLResponse(content=content, status_code=status_code, headers=headers)


def StreamingResponse(
    content: Any,
    status_code: int = 200,
    headers: Optional[dict[str, str]] = None,
    media_type: Optional[str] = None,
) -> "Response":
    """Create a streaming response."""
    from fastapi.responses import StreamingResponse as FastAPIStreamingResponse
    return FastAPIStreamingResponse(content=content, status_code=status_code, headers=headers, media_type=media_type)

