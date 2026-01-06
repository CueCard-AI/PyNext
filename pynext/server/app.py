"""
ASGI application for PyNext.

Provides the main FastAPI application with routing, static files,
and action endpoints.
"""

from __future__ import annotations

import mimetypes
import traceback
from pathlib import Path
from typing import Any, Optional

import orjson
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from pynext.router.file_router import FileRouter
from pynext.server.actions import handle_action_request, get_registry
from pynext.server.middleware import add_performance_middleware
from pynext.runtime import get_runtime_js, get_runtime_path, is_production
from pynext.core.errors import (
    PyNextError,
    UnauthorizedError,
    ForbiddenError,
    NotFoundError,
    ServerError,
    get_default_error_html,
)
from pynext.core.paths import resolve_paths


class ActionRequest(BaseModel):
    """Request model for server actions."""
    actionId: str
    args: dict[str, Any] = {}


class PyNextApp:
    """
    Main PyNext application.
    
    Combines the file router, action handler, and static file serving.
    
    Features:
    - File-based routing with route groups
    - Custom error pages (401, 403, 404, 500)
    - Template support for page transitions
    - Auto-detection of src/ folder structure
    """
    
    def __init__(
        self,
        pages_dir: Optional[str] = None,
        static_dir: Optional[str] = None,
        debug: bool = False,
        compression: bool = True,
        etag: bool = True,
    ):
        # Auto-detect project structure if not specified
        if pages_dir is None or static_dir is None:
            paths = resolve_paths()
            if pages_dir is None:
                self.pages_dir = paths.pages
                if debug:
                    structure = "src/" if paths.uses_src else "standard"
                    print(f"[PyNext] Detected {structure} structure: {paths.pages}")
            else:
                self.pages_dir = Path(pages_dir).resolve()
            
            if static_dir is None:
                self.static_dir = paths.public
            else:
                self.static_dir = Path(static_dir).resolve()
        else:
            self.pages_dir = Path(pages_dir).resolve()
            self.static_dir = Path(static_dir).resolve()
        
        self.debug = debug
        self.compression = compression
        self.etag = etag
        
        # Initialize router
        self.router = FileRouter(str(self.pages_dir))
        self.router.scan()
        
        # Create FastAPI app
        self.app = self._create_app()
        
        # Add performance middleware
        self._wrapped_app = add_performance_middleware(
            self.app,
            compression=compression,
            etag=etag and not debug,
            security_headers=not debug,
            timing=debug,
            cache_control=True,
            debug=debug,
        )
    
    def _create_app(self) -> FastAPI:
        """Create the FastAPI application."""
        app = FastAPI(
            title="PyNext",
            description="Python web framework with SolidJS-inspired reactivity",
            version="0.1.0",
            debug=self.debug,
            docs_url="/_pynext/docs" if self.debug else None,
            redoc_url="/_pynext/redoc" if self.debug else None,
            openapi_url="/_pynext/openapi.json" if self.debug else None,
        )
        
        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"] if self.debug else [],
            allow_methods=["GET", "POST"],
            allow_headers=["*"],
        )
        
        # Store reference to PyNextApp for route handlers
        pynext_app = self
        
        @app.get("/_pynext/runtime.js", include_in_schema=False)
        async def serve_runtime() -> Response:
            """Serve the PyNext JavaScript runtime.
            
            In production mode (debug=False), serves minified slim runtime (~17KB).
            In development mode (debug=True), serves full runtime with comments (~174KB).
            """
            # Use minified in production (debug=False)
            use_minified = not pynext_app.debug
            content = get_runtime_js(minified=use_minified)
            return Response(
                content=content,
                media_type="application/javascript",
                headers={"Cache-Control": "public, max-age=31536000" if use_minified else "no-cache"},
            )
        
        @app.get("/_pynext/react-bridge.js", include_in_schema=False)
        async def serve_react_bridge() -> Response:
            """Serve the React bridge JavaScript."""
            bridge_path = get_runtime_path().parent / "react-bridge.js"
            if bridge_path.exists():
                content = bridge_path.read_text()
                return Response(
                    content=content,
                    media_type="application/javascript",
                    headers={"Cache-Control": "no-cache" if pynext_app.debug else "public, max-age=31536000"},
                )
            return Response(content="// React bridge not found", media_type="application/javascript", status_code=404)
        
        @app.get("/_pynext/js/{filename}", include_in_schema=False)
        async def serve_runtime_file(filename: str) -> Response:
            """Serve any runtime JavaScript file.
            
            Automatically uses slim/minified versions in production.
            Files: browser.js, keyboard.js, focus.js, theme.js, storage.js, sse.js, toast.js
            """
            from pynext.runtime import _get_runtime_file
            
            # Remove .js extension to get base name
            base_name = filename.replace('.js', '').replace('.slim', '').replace('.min', '')
            
            # Valid runtime files
            valid_files = {'browser', 'keyboard', 'focus', 'theme', 'storage', 'sse', 'toast', 
                          'signals', 'forms', 'control_flow', 'reactive', 'navigation'}
            
            if base_name not in valid_files:
                return Response(
                    content=f"// Unknown runtime file: {filename}",
                    media_type="application/javascript",
                    status_code=404
                )
            
            # Get the appropriate file (slim in production)
            use_slim = not pynext_app.debug
            file_path = _get_runtime_file(base_name, prefer_slim=use_slim)
            
            if file_path.exists():
                content = file_path.read_text()
                return Response(
                    content=content,
                    media_type="application/javascript",
                    headers={"Cache-Control": "public, max-age=31536000" if use_slim else "no-cache"},
                )
            
            return Response(
                content=f"// Runtime file not found: {filename}",
                media_type="application/javascript",
                status_code=404
            )
        
        @app.get("/_pynext/npm/{bundle_name}", include_in_schema=False)
        async def serve_npm_bundle(bundle_name: str) -> Response:
            """Serve bundled NPM packages."""
            bundle_path = pynext_app.pages_dir.parent / ".pynext" / "bundles" / bundle_name
            if bundle_path.exists():
                content = bundle_path.read_text()
                return Response(
                    content=content,
                    media_type="application/javascript",
                    headers={"Cache-Control": "no-cache" if pynext_app.debug else "public, max-age=31536000"},
                )
            return Response(content=f"// Bundle not found: {bundle_name}", media_type="application/javascript", status_code=404)
        
        @app.get("/_pynext/styles.css", include_in_schema=False)
        async def serve_styles() -> Response:
            """Serve base styles."""
            css = """
/* Tailwind CSS (for shadcn components) */
@import url('https://unpkg.com/tailwindcss@^2/dist/tailwind.min.css');

/* PyNext Base Styles */
*, *::before, *::after {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen,
        Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
}

img, picture, video, canvas, svg {
    display: block;
    max-width: 100%;
}

input, button, textarea, select {
    font: inherit;
}

p, h1, h2, h3, h4, h5, h6 {
    overflow-wrap: break-word;
}

#__pynext {
    isolation: isolate;
}
"""
            return Response(
                content=css,
                media_type="text/css",
                headers={"Cache-Control": "no-cache" if pynext_app.debug else "public, max-age=3600"},
            )
        
        @app.post("/_pynext/action", tags=["Server Actions"])
        async def handle_action(action: ActionRequest) -> JSONResponse:
            """
            Handle server action RPC calls.
            
            Server actions allow calling Python functions from the client
            with full access to Python packages.
            """
            try:
                result = await handle_action_request(action.model_dump())
                return JSONResponse(result)
            except Exception as e:
                return JSONResponse(
                    {"data": None, "error": f"Action failed: {e}"},
                    status_code=500,
                )
        
        @app.get("/_pynext/routes", tags=["Debug"])
        async def list_routes() -> dict:
            """List all registered routes (debug endpoint)."""
            if not pynext_app.debug:
                raise HTTPException(status_code=404, detail="Not available in production")
            
            return {
                "routes": pynext_app.router.get_routes_info(),
                "actions": get_registry().list_actions(),
            }
        
        @app.get("/_pynext/actions", tags=["Debug"])
        async def list_actions() -> dict:
            """List all registered server actions (debug endpoint)."""
            if not pynext_app.debug:
                raise HTTPException(status_code=404, detail="Not available in production")
            
            return {
                "actions": get_registry().list_actions(),
            }
        
        @app.get("/_pynext/health", include_in_schema=False)
        async def health_check() -> dict:
            """Health check endpoint."""
            from datetime import datetime
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
            }
        
        @app.get("/_pynext/env.json", include_in_schema=False)
        async def get_client_env() -> Response:
            """
            Serve public environment variables for client.
            
            Only variables prefixed with PYNEXT_PUBLIC_ are exposed.
            Used by runtime mode when env vars need to be dynamic.
            """
            try:
                from pynext.env_module import env
                from pynext.env.client import get_public_vars
                import json
                
                public_vars = get_public_vars(env.all())
                
                return Response(
                    content=json.dumps(public_vars, indent=2 if pynext_app.debug else None),
                    media_type="application/json",
                    headers={
                        "Cache-Control": "no-cache" if pynext_app.debug else "public, max-age=300",
                        "Content-Type": "application/json; charset=utf-8",
                    },
                )
            except Exception as e:
                return Response(
                    content="{}",
                    media_type="application/json",
                    status_code=200,  # Return empty obj, not error
                )
        
        # ========================================
        # OG Images: Dynamic generation endpoint
        # ========================================
        @app.get("/og/{path:path}.png", include_in_schema=False)
        @app.get("/og/{path:path}.jpg", include_in_schema=False)
        @app.get("/og/{path:path}.webp", include_in_schema=False)
        async def serve_og_image(path: str, request: Request) -> Response:
            """
            Serve dynamically generated OG image for a page.
            
            /og/blog/my-post.png -> generates OG for /blog/my-post
            """
            # Determine format from URL
            url_path = str(request.url.path)
            if url_path.endswith(".jpg"):
                format = "jpeg"
                media_type = "image/jpeg"
            elif url_path.endswith(".webp"):
                format = "webp"
                media_type = "image/webp"
            else:
                format = "png"
                media_type = "image/png"
            
            # Find route handler
            route_match = pynext_app.router.match(f"/{path}")
            if not route_match:
                return Response(status_code=404)
            
            handler = route_match[0] if isinstance(route_match, tuple) else route_match.handler
            params = route_match[1] if isinstance(route_match, tuple) else {}
            
            # Check if handler has OG config
            from pynext.og.decorator import get_og_config, get_og_handler
            
            config = get_og_config(handler)
            if not config:
                return Response(status_code=404)
            
            # Check ISR cache
            cache_key = f"og:{path}:{format}"
            if hasattr(pynext_app, "_og_cache"):
                cached = pynext_app._og_cache.get(cache_key)
                if cached:
                    return Response(
                        content=cached,
                        media_type=media_type,
                        headers={"Cache-Control": f"public, max-age={config.cache_seconds}"},
                    )
            
            try:
                from pynext.og import OGRenderer
                
                # Get custom handler or use template
                og_handler = get_og_handler(handler)
                
                if og_handler:
                    # Custom OG generator
                    canvas = og_handler(**params)
                else:
                    # Template-based generation
                    # Extract context from page metadata
                    context = {"title": path.replace("-", " ").replace("/", " - ").title()}
                    context.update(params)
                    canvas = config.template.render(context)
                
                # Render image
                renderer = OGRenderer()
                image_bytes = renderer.render(canvas, format)
                
                # Cache if enabled
                if config.cache and config.cache_seconds > 0:
                    if not hasattr(pynext_app, "_og_cache"):
                        pynext_app._og_cache = {}
                    pynext_app._og_cache[cache_key] = image_bytes
                
                return Response(
                    content=image_bytes,
                    media_type=media_type,
                    headers={"Cache-Control": f"public, max-age={config.cache_seconds}"},
                )
                
            except ImportError:
                # Pillow not installed
                return Response(status_code=500, content="Pillow required for OG images")
            except Exception as e:
                return Response(status_code=500, content=str(e))
        
        # ========================================
        # PWA: Manifest endpoint
        # ========================================
        @app.get("/manifest.json", include_in_schema=False)
        async def serve_manifest() -> Response:
            """
            Serve PWA manifest.json.
            
            Checks for static file first, then generates from config.
            """
            # Check for pre-generated static file
            static_path = pynext_app.static_dir / "manifest.json"
            if static_path.exists():
                return Response(
                    content=static_path.read_text(encoding="utf-8"),
                    media_type="application/manifest+json",
                    headers={"Cache-Control": "public, max-age=86400"},
                )
            
            # Try to generate from config
            manifest_config = pynext_app.config.get("manifest", None)
            
            if manifest_config:
                from pynext.pwa.manifest import PWAManifest
                
                if isinstance(manifest_config, dict):
                    config = PWAManifest(**manifest_config)
                elif isinstance(manifest_config, PWAManifest):
                    config = manifest_config
                else:
                    config = None
                
                if config:
                    # Detect icons for manifest
                    from pynext.pwa.icons import IconDetector
                    icons = IconDetector(pynext_app.static_dir).detect()
                    
                    from pynext.pwa.manifest import ManifestGenerator
                    generator = ManifestGenerator(config, icons)
                    content = generator.generate()
                    
                    return Response(
                        content=content,
                        media_type="application/manifest+json",
                        headers={"Cache-Control": "public, max-age=86400"},
                    )
            
            # No manifest available
            return Response(status_code=404)
        
        # ========================================
        # SEO: Sitemap endpoint
        # ========================================
        @app.get("/sitemap.xml", include_in_schema=False)
        async def serve_sitemap() -> Response:
            """
            Serve sitemap.xml.
            
            Checks for static file first, then generates dynamically if configured.
            """
            # Check for pre-generated static file
            static_path = pynext_app.static_dir / "sitemap.xml"
            if static_path.exists():
                return Response(
                    content=static_path.read_text(encoding="utf-8"),
                    media_type="application/xml",
                    headers={"Cache-Control": "public, max-age=3600"},
                )
            
            # Try to generate dynamically
            if pynext_app.config.get("dynamic_sitemap", False):
                from pynext.seo.sitemap import SitemapGenerator
                
                base_url = pynext_app.config.get("base_url", "")
                if not base_url:
                    # Try to construct from request
                    base_url = str(request.base_url).rstrip("/")
                
                generator = SitemapGenerator(pynext_app.router, base_url)
                xml = generator.generate()
                
                return Response(
                    content=xml,
                    media_type="application/xml",
                    headers={"Cache-Control": "public, max-age=3600"},
                )
            
            # No sitemap available
            return Response(status_code=404)
        
        # ========================================
        # SEO: Robots.txt endpoint
        # ========================================
        @app.get("/robots.txt", include_in_schema=False)
        async def serve_robots(request: Request) -> Response:
            """
            Serve robots.txt.
            
            Checks for static file first, then generates from config.
            """
            # Check for pre-generated static file
            static_path = pynext_app.static_dir / "robots.txt"
            if static_path.exists():
                return Response(
                    content=static_path.read_text(encoding="utf-8"),
                    media_type="text/plain",
                    headers={"Cache-Control": "public, max-age=3600"},
                )
            
            # Try to load config and generate
            robots_config = pynext_app.config.get("robots", None)
            
            if robots_config:
                from pynext.seo.robots import RobotsConfig
                
                if isinstance(robots_config, dict):
                    config = RobotsConfig.from_dict(robots_config)
                elif isinstance(robots_config, RobotsConfig):
                    config = robots_config
                else:
                    config = None
                
                if config:
                    base_url = pynext_app.config.get("base_url", str(request.base_url).rstrip("/"))
                    content = config.generate(base_url)
                    
                    return Response(
                        content=content,
                        media_type="text/plain",
                        headers={"Cache-Control": "public, max-age=3600"},
                    )
            
            # Default robots.txt (allow all)
            base_url = str(request.base_url).rstrip("/")
            default_robots = f"""User-agent: *
Allow: /

Sitemap: {base_url}/sitemap.xml
"""
            return Response(
                content=default_robots,
                media_type="text/plain",
                headers={"Cache-Control": "public, max-age=3600"},
            )
        
        # Mount static files if directory exists (before catch-all)
        if self.static_dir.exists():
            app.mount("/static", StaticFiles(directory=str(self.static_dir)), name="static")
        
        # API route handler (any method)
        @app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"], include_in_schema=False)
        async def handle_api_route(request: Request, path: str = "") -> Response:
            """Handle API route requests."""
            url_path = f"/api/{path}" if path else "/api"
            
            # Try to match an API route
            route, params = pynext_app.router.match_api(url_path)
            
            if route:
                try:
                    return await route.handle(request)
                except Exception as e:
                    if pynext_app.debug:
                        return JSONResponse(
                            {"error": str(e), "traceback": traceback.format_exc()},
                            status_code=500,
                        )
                    return JSONResponse({"error": "Internal server error"}, status_code=500)
            
            return JSONResponse({"error": "API route not found"}, status_code=404)
        
        # Catch-all route for pages - must be registered last
        @app.get("/{path:path}", include_in_schema=False)
        async def handle_page(request: Request, path: str = "") -> Response:
            """Handle a page request."""
            url_path = f"/{path}" if path else "/"
            
            # Try to match a route
            route, params = pynext_app.router.match(url_path)
            
            if route:
                try:
                    html = await route.handle(request)
                    
                    # Apply RouteConfig headers if present
                    headers = {}
                    if route.config:
                        headers = route.config.to_headers()
                    
                    return HTMLResponse(html, headers=headers)
                
                except UnauthorizedError as e:
                    # Handle 401 Unauthorized
                    return HTMLResponse(
                        pynext_app._render_401(e),
                        status_code=401,
                    )
                
                except ForbiddenError as e:
                    # Handle 403 Forbidden
                    return HTMLResponse(
                        pynext_app._render_403(e),
                        status_code=403,
                    )
                
                except NotFoundError as e:
                    # Handle 404 Not Found (raised programmatically)
                    return HTMLResponse(
                        pynext_app._render_404(url_path, e),
                        status_code=404,
                    )
                
                except PyNextError as e:
                    # Handle other PyNext errors
                    return HTMLResponse(
                        get_default_error_html(e.status_code, e),
                        status_code=e.status_code,
                    )
                
                except Exception as e:
                    # Try to render error page
                    error_html = pynext_app._render_error(e, route)
                    if error_html:
                        return HTMLResponse(error_html, status_code=500)
                    
                    if pynext_app.debug:
                        error_html = f"""
<!DOCTYPE html>
<html>
<head><title>Error</title></head>
<body style="font-family: monospace; padding: 20px;">
<h1 style="color: red;">Error rendering page</h1>
<pre>{traceback.format_exc()}</pre>
</body>
</html>
"""
                        return HTMLResponse(error_html, status_code=500)
                    return HTMLResponse("<h1>Internal Server Error</h1>", status_code=500)
            
            # Try static file from public directory
            static_path = pynext_app.static_dir / url_path.lstrip("/")
            if static_path.exists() and static_path.is_file():
                mime_type, _ = mimetypes.guess_type(str(static_path))
                return Response(
                    content=static_path.read_bytes(),
                    media_type=mime_type or "application/octet-stream",
                )
            
            # 404
            return HTMLResponse(
                pynext_app._render_404(url_path),
                status_code=404,
            )
        
        return app
    
    def _render_401(self, error: UnauthorizedError) -> str:
        """Render a 401 Unauthorized page."""
        # Try custom unauthorized page
        unauthorized = self.router.get_unauthorized()
        if unauthorized:
            try:
                return unauthorized.render_full_page(error)
            except Exception as e:
                if self.debug:
                    print(f"Error rendering custom 401: {e}")
        
        # Default 401
        return get_default_error_html(401, error)
    
    def _render_403(self, error: ForbiddenError) -> str:
        """Render a 403 Forbidden page."""
        # Try custom forbidden page
        forbidden = self.router.get_forbidden()
        if forbidden:
            try:
                return forbidden.render_full_page(error)
            except Exception as e:
                if self.debug:
                    print(f"Error rendering custom 403: {e}")
        
        # Default 403
        return get_default_error_html(403, error)
    
    def _render_404(self, path: str, error: Optional[NotFoundError] = None) -> str:
        """Render a 404 page."""
        # Try custom not-found page
        not_found = self.router.get_not_found()
        if not_found:
            try:
                return not_found.render_page()
            except Exception as e:
                if self.debug:
                    print(f"Error rendering custom 404: {e}")
        
        # Default 404
        if self.debug:
            routes_list = "<br>".join(
                f"• {r['pattern']} → {r['file']}"
                for r in self.router.get_routes_info()
            )
            return f"""
<!DOCTYPE html>
<html>
<head><title>404 Not Found</title></head>
<body style="font-family: sans-serif; padding: 40px; max-width: 600px; margin: 0 auto;">
<h1>404 - Page Not Found</h1>
<p>No route matches: <code>{path}</code></p>
<h3>Available routes:</h3>
<p style="font-family: monospace; font-size: 14px;">{routes_list or "No routes registered"}</p>
<p><small>Create a page at <code>pages/{path.strip('/')}.py</code> or <code>pages/{path.strip('/')}/index.py</code></small></p>
<hr>
<p><small>API docs available at <a href="/_pynext/docs">/_pynext/docs</a></small></p>
</body>
</html>
"""
        return get_default_error_html(404, error)
    
    def _render_error(self, error: Exception, route=None) -> Optional[str]:
        """Render an error page using the route's error handler if available."""
        if route and route.error:
            try:
                return route.error.render_error(error, reset_fn=None)
            except Exception as e:
                if self.debug:
                    print(f"Error rendering error page: {e}")
        return None
    
    def reload_routes(self, file_path: Optional[str] = None) -> None:
        """Reload routes for hot reloading."""
        self.router.reload(file_path)
    
    async def __call__(self, scope, receive, send):
        """ASGI interface."""
        await self._wrapped_app(scope, receive, send)


def create_app(
    pages_dir: str = "pages",
    static_dir: str = "public",
    debug: bool = False,
    compression: bool = True,
    etag: bool = True,
) -> PyNextApp:
    """
    Create a PyNext application.
    
    Args:
        pages_dir: Directory containing page components
        static_dir: Directory for static files
        debug: Enable debug mode (enables /docs endpoint)
        compression: Enable gzip compression (default: True)
        etag: Enable ETag headers (default: True)
    
    Returns:
        PyNextApp instance (ASGI compatible)
    """
    return PyNextApp(
        pages_dir=pages_dir,
        static_dir=static_dir,
        debug=debug,
        compression=compression,
        etag=etag,
    )
