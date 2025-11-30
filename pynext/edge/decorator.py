"""
Edge Decorator - Mark Functions for Edge Deployment

Simple decorator to mark API routes for edge runtime.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union


@dataclass
class EdgeConfig:
    """
    Edge function configuration.
    
    Attributes:
        runtime: Target runtime (cloudflare, vercel, deno, bun)
        regions: Deployment regions
        memory: Memory limit in MB
        timeout: Timeout in seconds
        bindings: Platform-specific bindings (KV, D1, etc.)
    """
    runtime: Optional[str] = None  # Auto-detect if None
    regions: List[str] = field(default_factory=list)
    memory: int = 128
    timeout: int = 30
    bindings: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "runtime": self.runtime,
            "regions": self.regions,
            "memory": self.memory,
            "timeout": self.timeout,
            "bindings": self.bindings,
        }


def edge(
    func: Optional[Callable] = None,
    *,
    runtime: Optional[str] = None,
    regions: Optional[List[str]] = None,
    memory: int = 128,
    timeout: int = 30,
    **bindings,
) -> Union[Callable, Callable[[Callable], Callable]]:
    """
    Mark a function for edge runtime deployment.
    
    Can be used as a simple decorator or with configuration:
    
    Args:
        func: Function to decorate (when used without parentheses)
        runtime: Target runtime (cloudflare, vercel, deno, bun)
        regions: Deployment regions
        memory: Memory limit in MB
        timeout: Timeout in seconds
        **bindings: Platform-specific bindings
        
    Returns:
        Decorated function
        
    Example:
        # Simple usage
        @edge
        async def handler(request):
            return {"hello": "world"}
        
        # With configuration
        @edge(runtime="cloudflare", timeout=60)
        async def handler(request):
            return {"hello": "world"}
        
        # With bindings
        @edge(runtime="cloudflare", KV="MY_KV_NAMESPACE")
        async def handler(request):
            value = await request.env.KV.get("key")
            return {"value": value}
    """
    config = EdgeConfig(
        runtime=runtime,
        regions=regions or [],
        memory=memory,
        timeout=timeout,
        bindings=bindings,
    )
    
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            # The actual function execution
            return await fn(*args, **kwargs)
        
        # Attach edge configuration
        wrapper._edge_config = config
        wrapper._is_edge_function = True
        
        return wrapper
    
    # Handle both @edge and @edge() usage
    if func is not None:
        return decorator(func)
    return decorator


def is_edge_function(func: Callable) -> bool:
    """Check if a function is marked for edge deployment."""
    return getattr(func, "_is_edge_function", False)


def get_edge_config(func: Callable) -> Optional[EdgeConfig]:
    """Get edge configuration from a function."""
    return getattr(func, "_edge_config", None)


class EdgeRequest:
    """
    Edge request with platform bindings.
    
    Wraps the standard request with access to
    platform-specific features.
    """
    
    def __init__(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        body: Optional[bytes] = None,
        env: Optional[Dict[str, Any]] = None,
    ):
        self.method = method
        self.url = url
        self.headers = headers
        self.body = body
        self._env = env or {}
    
    @property
    def env(self) -> "EdgeEnv":
        """Access platform bindings."""
        return EdgeEnv(self._env)
    
    async def json(self) -> Any:
        """Parse body as JSON."""
        import json
        if self.body:
            return json.loads(self.body)
        return None
    
    async def text(self) -> str:
        """Get body as text."""
        if self.body:
            return self.body.decode("utf-8")
        return ""
    
    @property
    def path(self) -> str:
        """Get URL path."""
        from urllib.parse import urlparse
        return urlparse(self.url).path
    
    @property
    def query(self) -> Dict[str, str]:
        """Get query parameters."""
        from urllib.parse import urlparse, parse_qs
        qs = urlparse(self.url).query
        params = parse_qs(qs)
        return {k: v[0] if len(v) == 1 else v for k, v in params.items()}


class EdgeEnv:
    """
    Access to platform bindings.
    
    Provides typed access to KV, D1, R2, etc.
    """
    
    def __init__(self, bindings: Dict[str, Any]):
        self._bindings = bindings
    
    def __getattr__(self, name: str) -> Any:
        """Access binding by name."""
        if name.startswith("_"):
            raise AttributeError(name)
        
        if name in self._bindings:
            return self._bindings[name]
        
        raise AttributeError(
            f"Binding '{name}' not configured. "
            f"Add it to @edge decorator: @edge({name}='BINDING_NAME')"
        )
    
    def get(self, name: str, default: Any = None) -> Any:
        """Get binding with default."""
        return self._bindings.get(name, default)


class EdgeResponse:
    """
    Edge response builder.
    
    Provides consistent response format across platforms.
    """
    
    def __init__(
        self,
        body: Any = None,
        status: int = 200,
        headers: Optional[Dict[str, str]] = None,
    ):
        self.body = body
        self.status = status
        self.headers = headers or {}
    
    @classmethod
    def json(
        cls,
        data: Any,
        status: int = 200,
        headers: Optional[Dict[str, str]] = None,
    ) -> "EdgeResponse":
        """Create JSON response."""
        import json
        return cls(
            body=json.dumps(data),
            status=status,
            headers={
                "Content-Type": "application/json",
                **(headers or {}),
            },
        )
    
    @classmethod
    def text(
        cls,
        text: str,
        status: int = 200,
        headers: Optional[Dict[str, str]] = None,
    ) -> "EdgeResponse":
        """Create text response."""
        return cls(
            body=text,
            status=status,
            headers={
                "Content-Type": "text/plain",
                **(headers or {}),
            },
        )
    
    @classmethod
    def html(
        cls,
        html: str,
        status: int = 200,
        headers: Optional[Dict[str, str]] = None,
    ) -> "EdgeResponse":
        """Create HTML response."""
        return cls(
            body=html,
            status=status,
            headers={
                "Content-Type": "text/html",
                **(headers or {}),
            },
        )
    
    @classmethod
    def redirect(
        cls,
        url: str,
        status: int = 302,
    ) -> "EdgeResponse":
        """Create redirect response."""
        return cls(
            body=None,
            status=status,
            headers={"Location": url},
        )

