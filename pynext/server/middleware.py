"""
Middleware for PyNext server.

Provides compression, caching, and other performance optimizations.
"""

from __future__ import annotations

import gzip
import hashlib
import io
from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Message, Receive, Scope, Send


# =============================================================================
# Compression Middleware
# =============================================================================

class CompressionMiddleware(BaseHTTPMiddleware):
    """
    Middleware that compresses responses using gzip.
    
    Only compresses responses that:
    - Are larger than min_size bytes
    - Have a compressible content type
    - Client accepts gzip encoding
    """
    
    COMPRESSIBLE_TYPES = frozenset([
        "text/html",
        "text/css",
        "text/javascript",
        "application/javascript",
        "application/json",
        "text/plain",
        "text/xml",
        "application/xml",
        "image/svg+xml",
    ])
    
    def __init__(
        self,
        app: ASGIApp,
        minimum_size: int = 500,
        compression_level: int = 6,
    ):
        super().__init__(app)
        self.minimum_size = minimum_size
        self.compression_level = compression_level
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check if client accepts gzip
        accept_encoding = request.headers.get("accept-encoding", "")
        if "gzip" not in accept_encoding.lower():
            return await call_next(request)
        
        # Get original response
        response = await call_next(request)
        
        # Check if response should be compressed
        content_type = response.headers.get("content-type", "")
        base_content_type = content_type.split(";")[0].strip()
        
        if base_content_type not in self.COMPRESSIBLE_TYPES:
            return response
        
        # Check if already encoded
        if "content-encoding" in response.headers:
            return response
        
        # Get response body
        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        
        # Check minimum size
        if len(body) < self.minimum_size:
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )
        
        # Compress
        compressed = gzip.compress(body, compresslevel=self.compression_level)
        
        # Only use compressed if smaller
        if len(compressed) >= len(body):
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )
        
        # Return compressed response
        headers = dict(response.headers)
        headers["content-encoding"] = "gzip"
        headers["content-length"] = str(len(compressed))
        headers["vary"] = "accept-encoding"
        
        return Response(
            content=compressed,
            status_code=response.status_code,
            headers=headers,
            media_type=response.media_type,
        )


# =============================================================================
# ETag Middleware
# =============================================================================

class ETagMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds ETag headers and handles conditional requests.
    
    - Generates ETag from response content hash
    - Returns 304 Not Modified if ETag matches
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Only apply to GET/HEAD requests
        if request.method not in ("GET", "HEAD"):
            return await call_next(request)
        
        # Get original response
        response = await call_next(request)
        
        # Skip if already has ETag
        if "etag" in response.headers:
            return response
        
        # Skip certain status codes
        if response.status_code not in (200,):
            return response
        
        # Get response body
        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        
        # Generate ETag
        etag = f'"{hashlib.md5(body).hexdigest()}"'
        
        # Check If-None-Match header
        if_none_match = request.headers.get("if-none-match")
        if if_none_match and if_none_match == etag:
            return Response(
                status_code=304,
                headers={"etag": etag},
            )
        
        # Return response with ETag
        headers = dict(response.headers)
        headers["etag"] = etag
        
        return Response(
            content=body,
            status_code=response.status_code,
            headers=headers,
            media_type=response.media_type,
        )


# =============================================================================
# Security Headers Middleware
# =============================================================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds security headers to responses.
    """
    
    DEFAULT_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
    }
    
    def __init__(
        self,
        app: ASGIApp,
        headers: Optional[dict[str, str]] = None,
        content_security_policy: Optional[str] = None,
    ):
        super().__init__(app)
        self.headers = {**self.DEFAULT_HEADERS, **(headers or {})}
        if content_security_policy:
            self.headers["Content-Security-Policy"] = content_security_policy
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        for key, value in self.headers.items():
            response.headers[key] = value
        
        return response


# =============================================================================
# Timing Middleware
# =============================================================================

class TimingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds Server-Timing header for performance monitoring.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        import time
        
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = (time.perf_counter() - start_time) * 1000  # ms
        
        response.headers["Server-Timing"] = f"total;dur={process_time:.2f}"
        
        return response


# =============================================================================
# Cache Control Middleware
# =============================================================================

class CacheControlMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds Cache-Control headers based on content type.
    """
    
    CACHE_RULES = {
        # Static assets - long cache
        "text/css": "public, max-age=31536000, immutable",
        "application/javascript": "public, max-age=31536000, immutable",
        "image/": "public, max-age=31536000, immutable",
        "font/": "public, max-age=31536000, immutable",
        
        # HTML - short cache or no cache
        "text/html": "no-cache, must-revalidate",
        
        # API responses - no cache by default
        "application/json": "no-store",
    }
    
    def __init__(self, app: ASGIApp, debug: bool = False):
        super().__init__(app)
        self.debug = debug
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Skip if already has Cache-Control
        if "cache-control" in response.headers:
            return response
        
        # In debug mode, don't cache anything
        if self.debug:
            response.headers["Cache-Control"] = "no-store"
            return response
        
        # Get content type
        content_type = response.headers.get("content-type", "")
        
        # Find matching rule
        for pattern, cache_control in self.CACHE_RULES.items():
            if content_type.startswith(pattern):
                response.headers["Cache-Control"] = cache_control
                break
        
        return response


# =============================================================================
# Middleware Stack Builder
# =============================================================================

def add_performance_middleware(
    app: ASGIApp,
    *,
    compression: bool = True,
    etag: bool = True,
    security_headers: bool = True,
    timing: bool = False,
    cache_control: bool = True,
    debug: bool = False,
) -> ASGIApp:
    """
    Add performance middleware stack to an app.
    
    Args:
        app: The ASGI app to wrap
        compression: Enable gzip compression
        etag: Enable ETag generation and 304 responses
        security_headers: Add security headers
        timing: Add Server-Timing header
        cache_control: Add Cache-Control headers
        debug: Enable debug mode (disables caching)
    
    Returns:
        Wrapped ASGI app with middleware
    """
    if timing:
        app = TimingMiddleware(app)
    
    if cache_control:
        app = CacheControlMiddleware(app, debug=debug)
    
    if security_headers:
        app = SecurityHeadersMiddleware(app)
    
    if etag and not debug:
        app = ETagMiddleware(app)
    
    if compression:
        app = CompressionMiddleware(app)
    
    return app

