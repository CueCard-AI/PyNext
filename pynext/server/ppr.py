"""
PPR Server Handler for PyNext.

Handles streaming responses for PPR pages:
- Sends static shell immediately
- Streams dynamic content as it resolves
- Out-of-order replacement via inline scripts

Zero overhead for fully static pages.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, List, AsyncGenerator, Any, Callable
import asyncio
import json

from fastapi import Request, Response
from fastapi.responses import StreamingResponse, HTMLResponse

from pynext.core.ppr import (
    PPRContext,
    PPRBoundary,
    PPRMode,
    get_ppr_context,
    create_ppr_context,
    get_ppr_runtime_js,
    needs_ppr_runtime,
)


@dataclass
class PPRStreamConfig:
    """Configuration for PPR streaming."""
    timeout: float = 10.0           # Max time to wait for all content
    chunk_timeout: float = 3.0      # Max time per chunk
    flush_interval: float = 0.05    # How often to check for content
    send_runtime: bool = True       # Include PPR runtime JS
    

class PPRStreamHandler:
    """
    Handles streaming PPR responses.
    
    Flow:
    1. Render page (static parts + placeholders for dynamic)
    2. Stream static shell immediately
    3. Wait for dynamic content to resolve
    4. Stream replacement scripts for each resolved boundary
    5. Close stream when all complete or timeout
    """
    
    def __init__(self, config: Optional[PPRStreamConfig] = None):
        self.config = config or PPRStreamConfig()
    
    async def stream_response(
        self,
        page_fn: Callable,
        request: Request,
        args: tuple = (),
        kwargs: Optional[dict] = None,
    ) -> StreamingResponse:
        """
        Create a streaming response for a PPR page.
        
        Args:
            page_fn: The page function to render
            request: FastAPI request
            args: Positional arguments for page_fn
            kwargs: Keyword arguments for page_fn
        
        Returns:
            StreamingResponse with PPR content
        """
        kwargs = kwargs or {}
        
        return StreamingResponse(
            self._stream_content(page_fn, args, kwargs),
            media_type="text/html",
            headers={
                "Transfer-Encoding": "chunked",
                "X-Content-Type-Options": "nosniff",
            }
        )
    
    async def _stream_content(
        self,
        page_fn: Callable,
        args: tuple,
        kwargs: dict,
    ) -> AsyncGenerator[bytes, None]:
        """Generate streaming content."""
        # Create PPR context
        ctx = create_ppr_context(mode=PPRMode.HYBRID)
        
        # Start HTML document
        yield b"<!DOCTYPE html>\n<html>\n"
        
        # Render page (collects static + creates boundaries)
        import inspect
        if inspect.iscoroutinefunction(page_fn):
            result = await page_fn(*args, **kwargs)
        else:
            result = page_fn(*args, **kwargs)
        
        if hasattr(result, 'render'):
            html = result.render()
        else:
            html = str(result)
        
        # Send static shell
        yield html.encode('utf-8')
        
        # If no dynamic parts, we're done
        if not ctx.boundaries:
            yield b"\n</html>"
            return
        
        # Add PPR runtime if needed
        if self.config.send_runtime:
            runtime = get_ppr_runtime_js()
            yield f"\n<script>{runtime}</script>\n".encode('utf-8')
        
        # Stream dynamic content
        resolved = set()
        start_time = asyncio.get_event_loop().time()
        
        while len(resolved) < len(ctx.boundaries):
            # Check timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > self.config.timeout:
                break
            
            # Check each boundary
            for boundary_id, boundary in ctx.boundaries.items():
                if boundary_id in resolved:
                    continue
                
                if boundary.is_resolved and boundary.resolved_content:
                    # Stream replacement script
                    content = self._escape_for_js(boundary.resolved_content)
                    replacement_script = f"""
<script>
__pynext__.ppr.resolve("{boundary_id}", `{content}`);
</script>
"""
                    yield replacement_script.encode('utf-8')
                    resolved.add(boundary_id)
            
            await asyncio.sleep(self.config.flush_interval)
        
        # Handle unresolved boundaries (show fallbacks)
        for boundary_id in set(ctx.boundaries.keys()) - resolved:
            # Mark as failed
            error_script = f"""
<script>
__pynext__.ppr.setError("{boundary_id}", "Content timed out");
</script>
"""
            yield error_script.encode('utf-8')
        
        yield b"\n</html>"
    
    def _escape_for_js(self, content: str) -> str:
        """Escape content for JavaScript template literal."""
        return (
            content
            .replace("\\", "\\\\")
            .replace("`", "\\`")
            .replace("${", "\\${")
            .replace("</script>", "<\\/script>")
        )


class PPRMiddleware:
    """
    ASGI middleware for PPR.
    
    Intercepts requests to PPR-enabled pages and handles streaming.
    """
    
    def __init__(
        self,
        app,
        ppr_pages: Optional[Dict[str, Any]] = None,
        config: Optional[PPRStreamConfig] = None,
    ):
        self.app = app
        self.ppr_pages = ppr_pages or {}
        self.handler = PPRStreamHandler(config)
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        path = scope["path"]
        
        # Check if this is a PPR page
        if path in self.ppr_pages:
            page_info = self.ppr_pages[path]
            
            # For fully static pages, skip streaming
            if page_info.get("is_fully_static"):
                await self.app(scope, receive, send)
                return
            
            # For hybrid pages, we could intercept and stream
            # For now, pass through to let the route handler decide
        
        await self.app(scope, receive, send)


def add_ppr_routes(app, ppr_manifest: Optional[Dict] = None):
    """
    Add PPR-related routes to a FastAPI app.
    
    Adds:
    - /_ppr/status: Check PPR status for debugging
    - /_ppr/boundary/<id>: SSE endpoint for boundary updates (future)
    """
    from fastapi import FastAPI
    
    @app.get("/_ppr/status")
    async def ppr_status():
        """Get PPR status for debugging."""
        return {
            "enabled": True,
            "pages": ppr_manifest.get("pages", {}) if ppr_manifest else {},
            "runtime": "minimal",
        }
    
    @app.get("/_ppr/runtime.js")
    async def ppr_runtime():
        """Serve PPR runtime JS."""
        return Response(
            content=get_ppr_runtime_js(),
            media_type="application/javascript",
        )


async def render_ppr_response(
    page_fn: Callable,
    request: Request,
    use_streaming: bool = True,
    **page_kwargs,
) -> Response:
    """
    Render a PPR page and return appropriate response.
    
    For pages with dynamic content:
    - If streaming supported: StreamingResponse
    - Otherwise: Wait for all, then HTMLResponse
    
    For fully static pages:
    - HTMLResponse (no streaming needed)
    """
    # Create context
    ctx = create_ppr_context()
    
    # Render page
    import inspect
    if inspect.iscoroutinefunction(page_fn):
        result = await page_fn(**page_kwargs)
    else:
        result = page_fn(**page_kwargs)
    
    if hasattr(result, 'render'):
        html = result.render()
    else:
        html = str(result)
    
    # Check if we need streaming
    if not ctx.boundaries:
        # Fully static, return immediately
        return HTMLResponse(content=html)
    
    if use_streaming:
        # Stream response
        handler = PPRStreamHandler()
        return await handler.stream_response(
            page_fn,
            request,
            kwargs=page_kwargs,
        )
    else:
        # Wait for all boundaries, then return
        timeout = 10.0
        start = asyncio.get_event_loop().time()
        
        while ctx.dynamic_pending:
            if asyncio.get_event_loop().time() - start > timeout:
                break
            await asyncio.sleep(0.05)
        
        # Replace placeholders
        import re
        for boundary_id, boundary in ctx.boundaries.items():
            if boundary.is_resolved and boundary.resolved_content:
                pattern = f'<div data-ppr="{boundary_id}"[^>]*>.*?</div>'
                html = re.sub(pattern, boundary.resolved_content, html, flags=re.DOTALL)
        
        return HTMLResponse(content=html)


# =============================================================================
# Integration with Route Handlers
# =============================================================================

def ppr_route(
    fallback: Optional[Callable] = None,
    timeout: float = 10.0,
    cache_shell: bool = True,
):
    """
    Decorator to mark a route for PPR handling.
    
    Example:
        @app.get("/products/{id}")
        @ppr_route(fallback=ProductSkeleton, timeout=5.0)
        async def product_page(id: str, request: Request):
            return ProductPage(id=id)
    """
    def decorator(fn: Callable) -> Callable:
        import functools
        
        @functools.wraps(fn)
        async def wrapper(request: Request, **kwargs):
            # Get page result
            import inspect
            if inspect.iscoroutinefunction(fn):
                result = await fn(request=request, **kwargs)
            else:
                result = fn(request=request, **kwargs)
            
            # Check if it's already a Response
            if isinstance(result, Response):
                return result
            
            # Render with PPR
            ctx = get_ppr_context()
            
            if hasattr(result, 'render'):
                html = result.render()
            else:
                html = str(result)
            
            # If no boundaries, return simple response
            if not ctx or not ctx.boundaries:
                return HTMLResponse(content=html)
            
            # Stream response
            handler = PPRStreamHandler(PPRStreamConfig(timeout=timeout))
            
            async def generate():
                yield html.encode('utf-8')
                
                if ctx.boundaries:
                    yield f"\n<script>{get_ppr_runtime_js()}</script>\n".encode('utf-8')
                    
                    resolved = set()
                    start = asyncio.get_event_loop().time()
                    
                    while len(resolved) < len(ctx.boundaries):
                        if asyncio.get_event_loop().time() - start > timeout:
                            break
                        
                        for bid, boundary in ctx.boundaries.items():
                            if bid in resolved:
                                continue
                            if boundary.is_resolved and boundary.resolved_content:
                                content = handler._escape_for_js(boundary.resolved_content)
                                yield f'<script>__pynext__.ppr.resolve("{bid}", `{content}`);</script>\n'.encode('utf-8')
                                resolved.add(bid)
                        
                        await asyncio.sleep(0.05)
            
            return StreamingResponse(
                generate(),
                media_type="text/html",
            )
        
        wrapper._ppr_enabled = True
        wrapper._ppr_fallback = fallback
        wrapper._ppr_timeout = timeout
        
        return wrapper
    
    return decorator

