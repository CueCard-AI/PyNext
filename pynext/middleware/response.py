"""
PyNext Middleware Response Helpers.

Provides convenient functions for common middleware responses.
"""

from typing import Any, Dict, Optional
from starlette.responses import Response, JSONResponse, RedirectResponse

from pynext.middleware.edge import MiddlewareResponse, NextResponse


def redirect(
    url: str,
    permanent: bool = False,
    headers: Optional[Dict[str, str]] = None
) -> MiddlewareResponse:
    """
    Redirect to another URL.
    
    Args:
        url: Target URL
        permanent: If True, use 308 (permanent), else 307 (temporary)
        headers: Additional headers to include
    
    Example:
        @middleware(matcher="/old-path")
        async def redirect_old(ctx):
            return redirect("/new-path", permanent=True)
    """
    status = 308 if permanent else 307
    return NextResponse.redirect(url, status=status, headers=headers)


def rewrite(
    path: str,
    headers: Optional[Dict[str, str]] = None
) -> MiddlewareResponse:
    """
    Internally rewrite to a different path.
    
    The URL in the browser stays the same, but the server
    serves content from a different path.
    
    Args:
        path: Internal path to serve
        headers: Additional headers
    
    Example:
        @middleware(matcher="/products/:id")
        async def ab_test(ctx):
            if ctx.get_cookie("variant") == "B":
                return rewrite("/products-v2" + ctx.path.split("/products")[1])
            return next_response()
    """
    return NextResponse.rewrite(path, headers=headers)


def next_response(
    headers: Optional[Dict[str, str]] = None,
    cookies: Optional[Dict[str, Dict[str, Any]]] = None
) -> MiddlewareResponse:
    """
    Continue to the next middleware or handler.
    
    Optionally add headers or cookies to the response.
    
    Args:
        headers: Headers to add to response
        cookies: Cookies to set
    
    Example:
        @middleware(matcher="/*")
        async def add_headers(ctx):
            return next_response(headers={
                "X-Custom-Header": "value"
            })
    """
    return NextResponse.next(headers=headers, cookies=cookies)


def json_response(
    data: Any,
    status: int = 200,
    headers: Optional[Dict[str, str]] = None
) -> MiddlewareResponse:
    """
    Return a JSON response directly from middleware.
    
    Args:
        data: JSON-serializable data
        status: HTTP status code
        headers: Additional headers
    
    Example:
        @middleware(matcher="/api/*")
        async def rate_limit(ctx):
            if is_rate_limited(ctx):
                return json_response(
                    {"error": "Too many requests"},
                    status=429
                )
            return next_response()
    """
    return NextResponse.json(data, status=status, headers=headers)


def html_response(
    content: str,
    status: int = 200,
    headers: Optional[Dict[str, str]] = None
) -> MiddlewareResponse:
    """
    Return an HTML response directly from middleware.
    
    Args:
        content: HTML content
        status: HTTP status code
        headers: Additional headers
    """
    from starlette.responses import HTMLResponse
    
    response = HTMLResponse(content=content, status_code=status)
    
    if headers:
        for key, value in headers.items():
            response.headers[key] = value
    
    return MiddlewareResponse(
        action="response",
        response=response,
    )


def not_found(message: str = "Not Found") -> MiddlewareResponse:
    """Return a 404 response."""
    return json_response({"error": message}, status=404)


def unauthorized(message: str = "Unauthorized") -> MiddlewareResponse:
    """Return a 401 response."""
    return json_response({"error": message}, status=401)


def forbidden(message: str = "Forbidden") -> MiddlewareResponse:
    """Return a 403 response."""
    return json_response({"error": message}, status=403)


def bad_request(message: str = "Bad Request") -> MiddlewareResponse:
    """Return a 400 response."""
    return json_response({"error": message}, status=400)


def set_cookie(
    name: str,
    value: str,
    max_age: Optional[int] = None,
    path: str = "/",
    domain: Optional[str] = None,
    secure: bool = False,
    http_only: bool = True,
    same_site: str = "lax"
) -> Dict[str, Any]:
    """
    Create a cookie configuration for next_response().
    
    Example:
        @middleware(matcher="/login")
        async def set_session(ctx):
            return next_response(cookies={
                "session": set_cookie("session", "abc123", max_age=3600)
            })
    """
    return {
        "value": value,
        "max_age": max_age,
        "path": path,
        "domain": domain,
        "secure": secure,
        "httponly": http_only,
        "samesite": same_site,
    }


def delete_cookie(name: str, path: str = "/") -> Dict[str, Any]:
    """
    Create a cookie deletion configuration.
    
    Example:
        @middleware(matcher="/logout")
        async def clear_session(ctx):
            return next_response(cookies={
                "session": delete_cookie("session")
            })
    """
    return {
        "value": "",
        "max_age": 0,
        "path": path,
    }

