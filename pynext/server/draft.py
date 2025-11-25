"""
Draft Mode Server Integration for PyNext.

Provides API endpoints and middleware for draft mode:
- Enable/disable draft mode
- Token validation
- Draft content fetching

Integrates with CMS webhooks for content preview.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, Callable
import secrets
import time
import json
import hashlib

from fastapi import APIRouter, Request, Response, HTTPException, Depends
from fastapi.responses import JSONResponse, RedirectResponse

from pynext.core.draft import (
    DraftContext,
    create_draft_context,
    get_draft_context,
    enable_draft,
    disable_draft,
    is_draft_mode,
)


@dataclass
class DraftConfig:
    """Configuration for draft mode."""
    secret_key: str = ""  # Secret for token generation
    token_ttl: int = 3600 * 24  # Token TTL in seconds (24 hours)
    cookie_name: str = "__pynext_draft_token"
    preview_url: str = "/_draft/preview"
    enable_url: str = "/_draft/enable"
    disable_url: str = "/_draft/disable"


# Default config
_draft_config = DraftConfig()


def configure_draft(config: DraftConfig) -> None:
    """Set the draft configuration."""
    global _draft_config
    _draft_config = config


def get_draft_config() -> DraftConfig:
    """Get the current draft configuration."""
    return _draft_config


def generate_draft_token(
    secret: str,
    data: Optional[Dict[str, Any]] = None,
    ttl: int = 3600,
) -> str:
    """
    Generate a secure draft token.
    
    Args:
        secret: Secret key for signing
        data: Optional data to embed in token
        ttl: Time to live in seconds
    
    Returns:
        Signed token string
    """
    payload = {
        "iat": int(time.time()),
        "exp": int(time.time()) + ttl,
        "data": data or {},
        "nonce": secrets.token_hex(8),
    }
    
    payload_json = json.dumps(payload, sort_keys=True)
    signature = hashlib.sha256(f"{payload_json}{secret}".encode()).hexdigest()[:16]
    
    import base64
    encoded = base64.urlsafe_b64encode(payload_json.encode()).decode()
    
    return f"{encoded}.{signature}"


def verify_draft_token(token: str, secret: str) -> Optional[Dict[str, Any]]:
    """
    Verify a draft token.
    
    Args:
        token: Token to verify
        secret: Secret key used to sign
    
    Returns:
        Token payload if valid, None otherwise
    """
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        
        encoded, signature = parts
        
        import base64
        payload_json = base64.urlsafe_b64decode(encoded).decode()
        
        # Verify signature
        expected_sig = hashlib.sha256(f"{payload_json}{secret}".encode()).hexdigest()[:16]
        if signature != expected_sig:
            return None
        
        payload = json.loads(payload_json)
        
        # Check expiration
        if payload.get("exp", 0) < time.time():
            return None
        
        return payload
        
    except Exception:
        return None


def create_draft_router() -> APIRouter:
    """
    Create FastAPI router for draft mode endpoints.
    
    Endpoints:
    - GET /_draft/enable - Enable draft mode
    - GET /_draft/disable - Disable draft mode
    - GET /_draft/status - Check draft mode status
    - POST /_draft/preview - Start preview from CMS
    - GET /_draft/content/{id} - Get draft content
    """
    router = APIRouter(prefix="/_draft", tags=["draft"])
    
    @router.get("/enable")
    async def enable_draft_mode(
        request: Request,
        secret: Optional[str] = None,
        redirect: Optional[str] = None,
    ):
        """Enable draft mode."""
        config = get_draft_config()
        
        # Validate secret
        if config.secret_key:
            if secret != config.secret_key:
                raise HTTPException(status_code=403, detail="Invalid secret")
        
        # Generate token
        token = generate_draft_token(
            config.secret_key or "default",
            ttl=config.token_ttl,
        )
        
        # Create response
        redirect_url = redirect or request.headers.get("referer", "/")
        response = RedirectResponse(url=redirect_url, status_code=302)
        
        # Set cookie
        response.set_cookie(
            config.cookie_name,
            token,
            max_age=config.token_ttl,
            httponly=True,
            samesite="lax",
            secure=request.url.scheme == "https",
        )
        
        return response
    
    @router.get("/disable")
    async def disable_draft_mode(
        request: Request,
        redirect: Optional[str] = None,
    ):
        """Disable draft mode."""
        config = get_draft_config()
        
        redirect_url = redirect or request.headers.get("referer", "/")
        response = RedirectResponse(url=redirect_url, status_code=302)
        
        # Delete cookie
        response.delete_cookie(config.cookie_name)
        
        return response
    
    @router.get("/status")
    async def draft_status(request: Request):
        """Get current draft mode status."""
        config = get_draft_config()
        token = request.cookies.get(config.cookie_name)
        
        is_draft = False
        if token:
            payload = verify_draft_token(token, config.secret_key or "default")
            is_draft = payload is not None
        
        return JSONResponse({
            "enabled": is_draft,
            "tokenValid": is_draft,
        })
    
    @router.post("/preview")
    async def start_preview(
        request: Request,
        redirect: Optional[str] = None,
    ):
        """
        Start a preview session.
        
        Typically called by CMS webhook with preview data.
        """
        config = get_draft_config()
        
        try:
            body = await request.json()
        except Exception:
            body = {}
        
        # Generate token with preview data
        token = generate_draft_token(
            config.secret_key or "default",
            data=body,
            ttl=config.token_ttl,
        )
        
        redirect_url = redirect or body.get("url", "/")
        response = RedirectResponse(url=redirect_url, status_code=302)
        
        response.set_cookie(
            config.cookie_name,
            token,
            max_age=config.token_ttl,
            httponly=True,
            samesite="lax",
            secure=request.url.scheme == "https",
        )
        
        return response
    
    @router.get("/content/{content_id}")
    async def get_draft_content(
        request: Request,
        content_id: str,
    ):
        """
        Get draft content for a component.
        
        This endpoint is called by the client-side runtime
        to fetch draft versions of content.
        """
        config = get_draft_config()
        
        # Verify token
        token = (
            request.cookies.get(config.cookie_name) or
            request.headers.get("X-Draft-Token")
        )
        
        if not token:
            raise HTTPException(status_code=401, detail="No draft token")
        
        payload = verify_draft_token(token, config.secret_key or "default")
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Here you would fetch draft content from CMS
        # For now, return a placeholder
        return JSONResponse({
            "id": content_id,
            "content": f"Draft content for {content_id}",
            "isDraft": True,
        })
    
    return router


class DraftMiddleware:
    """
    ASGI middleware for draft mode detection.
    
    Checks for draft token in cookies and sets up draft context
    for the request.
    """
    
    def __init__(
        self,
        app,
        config: Optional[DraftConfig] = None,
    ):
        self.app = app
        self.config = config or get_draft_config()
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Check for draft token in cookies
        headers = dict(scope.get("headers", []))
        cookie_header = headers.get(b"cookie", b"").decode()
        
        is_draft = False
        draft_token = None
        
        # Parse cookies
        cookies = {}
        for cookie in cookie_header.split(";"):
            cookie = cookie.strip()
            if "=" in cookie:
                name, value = cookie.split("=", 1)
                cookies[name] = value
        
        # Check for draft token
        token = cookies.get(self.config.cookie_name)
        if token:
            payload = verify_draft_token(token, self.config.secret_key or "default")
            if payload:
                is_draft = True
                draft_token = token
        
        # Create draft context
        ctx = create_draft_context(is_draft=is_draft, token=draft_token)
        
        if is_draft:
            enable_draft(draft_token)
        
        await self.app(scope, receive, send)


def add_draft_routes(app, config: Optional[DraftConfig] = None):
    """
    Add draft mode routes to a FastAPI app.
    
    Args:
        app: FastAPI application
        config: Optional draft configuration
    """
    if config:
        configure_draft(config)
    
    router = create_draft_router()
    app.include_router(router)


def add_draft_middleware(app, config: Optional[DraftConfig] = None):
    """
    Add draft middleware to a FastAPI app.
    
    Args:
        app: FastAPI application
        config: Optional draft configuration
    """
    if config:
        configure_draft(config)
    
    app.add_middleware(DraftMiddleware, config=config or get_draft_config())

