"""
PyNext Edge Runtime - Deploy Anywhere

Universal edge function support for Cloudflare Workers,
Vercel Edge, Deno Deploy, and Bun.

Usage:
    from pynext import api_route, edge
    
    @api_route
    @edge  # Marks for edge deployment
    async def handler(request):
        return {"message": "Hello from the edge!"}
    
    # Specific runtime
    @api_route
    @edge(runtime="cloudflare")
    async def cf_handler(request):
        kv_value = await request.env.KV.get("key")
        return {"value": kv_value}

Features:
- Multi-platform deployment
- Platform auto-detection
- Type-safe bindings (KV, D1, etc.)
- Build command: pynext build --edge cloudflare
"""

from .decorator import edge, EdgeConfig
from .detector import detect_platform, EdgePlatform
from .adapters import (
    EdgeAdapter,
    CloudflareAdapter,
    VercelAdapter,
    DenoAdapter,
    BunAdapter,
    get_adapter,
)
from .builder import EdgeBuilder, build_for_edge

__all__ = [
    # Decorator
    "edge",
    "EdgeConfig",
    # Detection
    "detect_platform",
    "EdgePlatform",
    # Adapters
    "EdgeAdapter",
    "CloudflareAdapter",
    "VercelAdapter",
    "DenoAdapter",
    "BunAdapter",
    "get_adapter",
    # Builder
    "EdgeBuilder",
    "build_for_edge",
]

