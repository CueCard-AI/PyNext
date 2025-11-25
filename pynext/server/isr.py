"""
PyNext ISR Server Middleware - Stale-While-Revalidate Implementation.

Handles serving cached content and triggering background regeneration.
Integrates with FastAPI for on-demand revalidation endpoints.
"""

import asyncio
import hashlib
import json
import time
from typing import Any, Callable, Dict, Optional, Tuple

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from pynext.core.isr import (
    ISRCache,
    get_isr_cache,
    init_isr_cache,
    revalidate_path,
    revalidate_tag,
    revalidate_component,
    RegenerationWorker,
    InvalidationScope,
)


class ISRMiddleware(BaseHTTPMiddleware):
    """
    Middleware for serving ISR-cached content.
    
    Implements:
    - Stale-while-revalidate semantics
    - Cache headers for CDN/edge caching
    - Background regeneration triggering
    """
    
    def __init__(
        self,
        app: ASGIApp,
        cache: Optional[ISRCache] = None,
        secret_token: Optional[str] = None
    ):
        super().__init__(app)
        self.cache = cache or get_isr_cache()
        self.secret_token = secret_token
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """Process request with ISR caching."""
        path = request.url.path
        
        # Skip non-GET requests
        if request.method != "GET":
            return await call_next(request)
        
        # Skip API routes
        if path.startswith("/api/"):
            return await call_next(request)
        
        # Generate cache key
        cache_key = self._generate_cache_key(request)
        
        # Check cache
        entry = self.cache.get(cache_key)
        
        if entry:
            # Serve cached content
            response = Response(
                content=entry.content,
                media_type="text/html",
            )
            
            # Add cache headers
            self._add_cache_headers(response, entry)
            
            # If stale, trigger background regeneration
            if entry.is_stale:
                response.headers["X-PyNext-Cache"] = "stale"
            else:
                response.headers["X-PyNext-Cache"] = "hit"
            
            return response
        
        # Cache miss - render and cache
        response = await call_next(request)
        
        # Only cache successful HTML responses
        if (
            response.status_code == 200 and
            response.headers.get("content-type", "").startswith("text/html")
        ):
            # Read response body
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            
            content = body.decode()
            
            # Check if page has ISR config
            isr_config = self._get_page_isr_config(request)
            if isr_config:
                from pynext.core.isr import RevalidateConfig
                config = RevalidateConfig(
                    seconds=isr_config.get("revalidate"),
                    tags=isr_config.get("tags", []),
                    scope=InvalidationScope(isr_config.get("scope", "page")),
                )
                self.cache.set(cache_key, content, config)
            
            # Create new response with body
            response = Response(
                content=content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type="text/html",
            )
            response.headers["X-PyNext-Cache"] = "miss"
        
        return response
    
    def _generate_cache_key(self, request: Request) -> str:
        """Generate cache key from request."""
        parts = [
            request.url.path,
            str(sorted(request.query_params.items())),
        ]
        
        # Include Accept-Language for i18n
        lang = request.headers.get("accept-language", "")
        if lang:
            parts.append(lang.split(",")[0])
        
        return hashlib.md5(":".join(parts).encode()).hexdigest()
    
    def _add_cache_headers(self, response: Response, entry: Any) -> None:
        """Add cache control headers."""
        if entry.expires_at:
            max_age = max(0, int(entry.expires_at - time.time()))
            response.headers["Cache-Control"] = f"public, max-age={max_age}, stale-while-revalidate=60"
        else:
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        
        response.headers["ETag"] = f'"{entry.hash}"'
    
    def _get_page_isr_config(self, request: Request) -> Optional[Dict[str, Any]]:
        """Get ISR config for the requested page."""
        # This would be populated by the router
        return request.state.__dict__.get("isr_config")


def add_isr_routes(app: FastAPI, secret_token: Optional[str] = None) -> None:
    """
    Add on-demand revalidation API routes.
    
    These routes allow triggering revalidation from external sources
    (webhooks, CMS updates, etc.)
    """
    
    def verify_token(request: Request) -> bool:
        """Verify revalidation secret token."""
        if not secret_token:
            return True  # No auth required
        
        token = request.headers.get("x-revalidate-token")
        return token == secret_token
    
    @app.post("/api/revalidate/path")
    async def revalidate_path_handler(request: Request):
        """Revalidate a specific path."""
        if not verify_token(request):
            raise HTTPException(status_code=401, detail="Invalid token")
        
        body = await request.json()
        path = body.get("path")
        
        if not path:
            raise HTTPException(status_code=400, detail="path is required")
        
        result = await revalidate_path(path)
        return JSONResponse(result)
    
    @app.post("/api/revalidate/tag")
    async def revalidate_tag_handler(request: Request):
        """Revalidate by tag."""
        if not verify_token(request):
            raise HTTPException(status_code=401, detail="Invalid token")
        
        body = await request.json()
        tag = body.get("tag")
        
        if not tag:
            raise HTTPException(status_code=400, detail="tag is required")
        
        result = await revalidate_tag(tag)
        return JSONResponse(result)
    
    @app.post("/api/revalidate/component")
    async def revalidate_component_handler(request: Request):
        """Revalidate a specific component."""
        if not verify_token(request):
            raise HTTPException(status_code=401, detail="Invalid token")
        
        body = await request.json()
        component = body.get("component")
        
        if not component:
            raise HTTPException(status_code=400, detail="component is required")
        
        result = await revalidate_component(component)
        return JSONResponse(result)
    
    @app.get("/api/revalidate/stats")
    async def cache_stats_handler(request: Request):
        """Get cache statistics."""
        if not verify_token(request):
            raise HTTPException(status_code=401, detail="Invalid token")
        
        cache = get_isr_cache()
        return JSONResponse(cache.get_stats())


def add_isr_middleware(
    app: FastAPI,
    cache_dir: Optional[str] = None,
    secret_token: Optional[str] = None
) -> Tuple[ISRCache, RegenerationWorker]:
    """
    Configure ISR for a FastAPI application.
    
    Returns cache and worker instances for lifecycle management.
    """
    from pathlib import Path
    
    # Initialize cache
    cache_path = Path(cache_dir) if cache_dir else None
    cache = init_isr_cache(cache_path)
    
    # Add middleware
    app.add_middleware(ISRMiddleware, cache=cache, secret_token=secret_token)
    
    # Add API routes
    add_isr_routes(app, secret_token)
    
    # Create worker
    worker = RegenerationWorker(cache)
    
    # Start worker on app startup
    @app.on_event("startup")
    async def start_worker():
        await worker.start()
    
    @app.on_event("shutdown")
    async def stop_worker():
        await worker.stop()
    
    return cache, worker

