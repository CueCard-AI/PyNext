"""
Proxy Handler - Request Forwarding

Handles the actual proxying of requests to target servers.
Supports both HTTP and WebSocket connections.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
import json

from .router import ProxyMatch


@dataclass
class ProxyRequest:
    """
    A request to be proxied.
    
    Attributes:
        method: HTTP method
        path: Original request path
        headers: Request headers
        body: Request body
        query_string: Query string
    """
    method: str
    path: str
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[bytes] = None
    query_string: str = ""


@dataclass
class ProxyResponse:
    """
    Response from proxied request.
    
    Attributes:
        status_code: HTTP status code
        headers: Response headers
        body: Response body
        elapsed_ms: Time taken in milliseconds
    """
    status_code: int
    headers: Dict[str, str]
    body: bytes
    elapsed_ms: float = 0.0
    
    @property
    def is_success(self) -> bool:
        """Check if response was successful."""
        return 200 <= self.status_code < 300
    
    @property
    def text(self) -> str:
        """Get body as text."""
        return self.body.decode("utf-8", errors="replace")
    
    @property
    def json(self) -> Any:
        """Parse body as JSON."""
        return json.loads(self.body)


class ProxyHandler:
    """
    Handles proxying HTTP requests.
    
    Uses httpx for async HTTP requests with connection pooling.
    
    Example:
        >>> handler = ProxyHandler()
        >>> response = await handler.forward(match, request)
        >>> print(response.status_code)
    """
    
    def __init__(
        self,
        timeout: int = 30,
        max_connections: int = 100,
    ):
        self.timeout = timeout
        self.max_connections = max_connections
        self._client: Optional[Any] = None
    
    async def get_client(self):
        """Get or create HTTP client."""
        if self._client is None:
            try:
                import httpx
                self._client = httpx.AsyncClient(
                    timeout=self.timeout,
                    limits=httpx.Limits(max_connections=self.max_connections),
                    follow_redirects=True,
                )
            except ImportError:
                # Fallback to simple implementation
                self._client = SimpleHttpClient(timeout=self.timeout)
        return self._client
    
    async def forward(
        self,
        match: ProxyMatch,
        request: ProxyRequest,
    ) -> ProxyResponse:
        """
        Forward a request to the proxy target.
        
        Args:
            match: Matched proxy route
            request: Request to forward
            
        Returns:
            ProxyResponse from target
        """
        import time
        start = time.time()
        
        client = await self.get_client()
        
        # Build full URL
        url = match.target_url
        if request.query_string:
            url = f"{url}?{request.query_string}"
        
        # Merge headers
        headers = request.headers.copy()
        headers.update(match.headers)
        
        # Remove hop-by-hop headers
        hop_headers = [
            "connection", "keep-alive", "proxy-authenticate",
            "proxy-authorization", "te", "trailers", "transfer-encoding",
            "upgrade", "host",
        ]
        for h in hop_headers:
            headers.pop(h, None)
            headers.pop(h.title(), None)
        
        try:
            # Make request
            response = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                content=request.body,
            )
            
            elapsed = (time.time() - start) * 1000
            
            return ProxyResponse(
                status_code=response.status_code,
                headers=dict(response.headers),
                body=response.content,
                elapsed_ms=elapsed,
            )
        
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            
            return ProxyResponse(
                status_code=502,
                headers={"Content-Type": "application/json"},
                body=json.dumps({
                    "error": "Bad Gateway",
                    "message": str(e),
                    "target": match.target_url,
                }).encode(),
                elapsed_ms=elapsed,
            )
    
    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


class SimpleHttpClient:
    """
    Simple HTTP client fallback when httpx is not available.
    
    Uses urllib for basic functionality.
    """
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
    
    async def request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        content: Optional[bytes] = None,
    ):
        """Make an HTTP request."""
        import urllib.request
        import urllib.error
        
        def sync_request():
            req = urllib.request.Request(
                url,
                data=content,
                headers=headers,
                method=method,
            )
            
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    return SimpleResponse(
                        status_code=response.status,
                        headers=dict(response.headers),
                        content=response.read(),
                    )
            except urllib.error.HTTPError as e:
                return SimpleResponse(
                    status_code=e.code,
                    headers=dict(e.headers),
                    content=e.read(),
                )
        
        # Run in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, sync_request)
    
    async def aclose(self):
        """No cleanup needed."""
        pass


@dataclass
class SimpleResponse:
    """Simple response object for fallback client."""
    status_code: int
    headers: Dict[str, str]
    content: bytes


async def proxy_request(
    method: str,
    path: str,
    headers: Optional[Dict[str, str]] = None,
    body: Optional[bytes] = None,
    query_string: str = "",
    is_dev: bool = False,
) -> Optional[ProxyResponse]:
    """
    Proxy a request if it matches a proxy route.
    
    Convenience function for quick proxying.
    
    Args:
        method: HTTP method
        path: Request path
        headers: Request headers
        body: Request body
        query_string: Query string
        is_dev: Whether in development mode
        
    Returns:
        ProxyResponse if matched and proxied, None otherwise
        
    Example:
        >>> response = await proxy_request("GET", "/api/users/123")
        >>> if response:
        ...     print(response.json)
    """
    from .router import match_proxy
    
    match = match_proxy(path, is_dev)
    if not match:
        return None
    
    request = ProxyRequest(
        method=method,
        path=path,
        headers=headers or {},
        body=body,
        query_string=query_string,
    )
    
    handler = ProxyHandler(timeout=match.route.timeout)
    try:
        return await handler.forward(match, request)
    finally:
        await handler.close()


class WebSocketProxy:
    """
    Handles WebSocket proxying.
    
    Creates bidirectional connection between client
    and target WebSocket server.
    """
    
    def __init__(self, target_url: str, headers: Dict[str, str]):
        self.target_url = target_url
        self.headers = headers
        self._client_ws: Optional[Any] = None
        self._target_ws: Optional[Any] = None
    
    async def connect(self, client_ws: Any):
        """
        Establish proxy connection.
        
        Args:
            client_ws: Client WebSocket connection
        """
        try:
            import websockets
        except ImportError:
            raise ImportError(
                "websockets package required for WebSocket proxy. "
                "Install with: pip install websockets"
            )
        
        self._client_ws = client_ws
        
        # Connect to target
        self._target_ws = await websockets.connect(
            self.target_url,
            extra_headers=self.headers,
        )
        
        # Create bidirectional relay
        await asyncio.gather(
            self._relay_client_to_target(),
            self._relay_target_to_client(),
        )
    
    async def _relay_client_to_target(self):
        """Relay messages from client to target."""
        try:
            async for message in self._client_ws:
                await self._target_ws.send(message)
        except:
            pass
        finally:
            await self._close()
    
    async def _relay_target_to_client(self):
        """Relay messages from target to client."""
        try:
            async for message in self._target_ws:
                await self._client_ws.send(message)
        except:
            pass
        finally:
            await self._close()
    
    async def _close(self):
        """Close both connections."""
        if self._target_ws:
            await self._target_ws.close()
        if self._client_ws:
            await self._client_ws.close()

