"""
Proxy Middleware - FastAPI/Starlette Integration

Integrates proxy handling into the ASGI middleware stack.
Intercepts matching requests and forwards them to targets.
"""

from __future__ import annotations

import os
from typing import Any, Callable, Dict, Optional

from .config import ProxyConfig, get_proxy_config, load_proxy_config
from .router import ProxyRouter, ProxyMatch
from .handler import ProxyHandler, ProxyRequest


class ProxyMiddleware:
    """
    ASGI middleware for request proxying.
    
    Intercepts requests matching proxy patterns and forwards
    them to configured targets.
    
    Example:
        from fastapi import FastAPI
        from pynext.proxy import ProxyMiddleware
        
        app = FastAPI()
        app.add_middleware(ProxyMiddleware)
    """
    
    def __init__(
        self,
        app: Any,
        config: Optional[ProxyConfig] = None,
        is_dev: Optional[bool] = None,
    ):
        self.app = app
        self.config = config or get_proxy_config()
        self.router = ProxyRouter(self.config)
        self.is_dev = is_dev if is_dev is not None else self._detect_dev_mode()
        self._handler: Optional[ProxyHandler] = None
    
    def _detect_dev_mode(self) -> bool:
        """Detect if running in development mode."""
        return os.environ.get("PYNEXT_ENV", "development") == "development"
    
    async def __call__(self, scope: Dict, receive: Callable, send: Callable):
        """ASGI interface."""
        if scope["type"] == "http":
            # Check for proxy match
            path = scope.get("path", "")
            match = self.router.match(path, self.is_dev)
            
            if match:
                await self._handle_proxy(scope, receive, send, match)
                return
        
        elif scope["type"] == "websocket":
            # Check for WebSocket proxy
            path = scope.get("path", "")
            match = self.router.match(path, self.is_dev)
            
            if match and match.route.websocket:
                await self._handle_websocket_proxy(scope, receive, send, match)
                return
        
        # Not a proxy request - pass through
        await self.app(scope, receive, send)
    
    async def _handle_proxy(
        self,
        scope: Dict,
        receive: Callable,
        send: Callable,
        match: ProxyMatch,
    ):
        """Handle HTTP proxy request."""
        # Build request
        request = await self._build_request(scope, receive)
        
        # Get or create handler
        if self._handler is None:
            self._handler = ProxyHandler(timeout=match.route.timeout)
        
        # Forward request
        response = await self._handler.forward(match, request)
        
        # Send response
        await send({
            "type": "http.response.start",
            "status": response.status_code,
            "headers": [
                (k.encode(), v.encode())
                for k, v in response.headers.items()
                if k.lower() not in ("content-encoding", "transfer-encoding")
            ],
        })
        
        await send({
            "type": "http.response.body",
            "body": response.body,
        })
    
    async def _build_request(
        self,
        scope: Dict,
        receive: Callable,
    ) -> ProxyRequest:
        """Build ProxyRequest from ASGI scope."""
        # Collect headers
        headers = {}
        for key, value in scope.get("headers", []):
            headers[key.decode()] = value.decode()
        
        # Read body
        body = b""
        while True:
            message = await receive()
            body += message.get("body", b"")
            if not message.get("more_body", False):
                break
        
        # Get query string
        query_string = scope.get("query_string", b"").decode()
        
        return ProxyRequest(
            method=scope.get("method", "GET"),
            path=scope.get("path", "/"),
            headers=headers,
            body=body if body else None,
            query_string=query_string,
        )
    
    async def _handle_websocket_proxy(
        self,
        scope: Dict,
        receive: Callable,
        send: Callable,
        match: ProxyMatch,
    ):
        """Handle WebSocket proxy."""
        from .handler import WebSocketProxy
        
        # Accept the WebSocket connection
        await send({"type": "websocket.accept"})
        
        # Create proxy
        proxy = WebSocketProxy(
            target_url=match.target_url,
            headers=match.headers,
        )
        
        # Create a wrapper for the client WebSocket
        client_ws = ASGIWebSocket(receive, send)
        
        try:
            await proxy.connect(client_ws)
        except Exception as e:
            await send({
                "type": "websocket.close",
                "code": 1011,  # Internal error
            })


class ASGIWebSocket:
    """Wrapper to use ASGI WebSocket with standard interface."""
    
    def __init__(self, receive: Callable, send: Callable):
        self._receive = receive
        self._send = send
        self._closed = False
    
    async def send(self, message: Any):
        """Send message to client."""
        if self._closed:
            return
        
        if isinstance(message, bytes):
            await self._send({
                "type": "websocket.send",
                "bytes": message,
            })
        else:
            await self._send({
                "type": "websocket.send",
                "text": str(message),
            })
    
    async def close(self, code: int = 1000):
        """Close WebSocket."""
        if self._closed:
            return
        
        self._closed = True
        await self._send({
            "type": "websocket.close",
            "code": code,
        })
    
    def __aiter__(self):
        return self
    
    async def __anext__(self):
        if self._closed:
            raise StopAsyncIteration
        
        message = await self._receive()
        
        if message["type"] == "websocket.disconnect":
            self._closed = True
            raise StopAsyncIteration
        
        return message.get("text") or message.get("bytes")


def create_proxy_middleware(
    config: Optional[ProxyConfig] = None,
    auto_load: bool = True,
) -> type:
    """
    Create a configured proxy middleware class.
    
    Args:
        config: Optional pre-configured ProxyConfig
        auto_load: Whether to auto-load from proxy.py
        
    Returns:
        Configured middleware class
        
    Example:
        from fastapi import FastAPI
        from pynext.proxy import create_proxy_middleware
        
        Middleware = create_proxy_middleware()
        
        app = FastAPI()
        app.add_middleware(Middleware)
    """
    if auto_load and config is None:
        config = load_proxy_config()
    
    class ConfiguredProxyMiddleware(ProxyMiddleware):
        def __init__(self, app: Any):
            super().__init__(app, config=config)
    
    return ConfiguredProxyMiddleware

