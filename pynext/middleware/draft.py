"""
Draft Mode Middleware for PyNext.

Lightweight middleware for detecting and handling draft mode
in the request pipeline.
"""

from typing import Optional
from fastapi import Request

from pynext.core.draft import (
    create_draft_context,
    enable_draft,
    is_draft_mode,
)
from pynext.server.draft import (
    DraftConfig,
    get_draft_config,
    verify_draft_token,
)


async def detect_draft_mode(request: Request) -> bool:
    """
    Detect if request is in draft mode.
    
    Checks:
    1. Cookie for draft token
    2. Query parameter (for preview links)
    3. Header (for API calls)
    
    Returns:
        True if in draft mode
    """
    config = get_draft_config()
    secret = config.secret_key or "default"
    
    # Check cookie
    token = request.cookies.get(config.cookie_name)
    if token and verify_draft_token(token, secret):
        return True
    
    # Check query parameter
    token = request.query_params.get("draft_token")
    if token and verify_draft_token(token, secret):
        return True
    
    # Check header
    token = request.headers.get("X-Draft-Token")
    if token and verify_draft_token(token, secret):
        return True
    
    return False


async def setup_draft_context(request: Request) -> None:
    """
    Set up draft context for a request.
    
    Call this in request handlers to enable draft mode features.
    """
    config = get_draft_config()
    secret = config.secret_key or "default"
    
    # Try to get token
    token = (
        request.cookies.get(config.cookie_name) or
        request.query_params.get("draft_token") or
        request.headers.get("X-Draft-Token")
    )
    
    is_draft = False
    if token:
        payload = verify_draft_token(token, secret)
        is_draft = payload is not None
    
    # Create context
    ctx = create_draft_context(is_draft=is_draft, token=token if is_draft else None)
    
    if is_draft and token:
        enable_draft(token)


def get_draft_preview_url(
    content_id: str,
    content_type: str = "page",
    redirect_url: Optional[str] = None,
) -> str:
    """
    Generate a draft preview URL.
    
    Args:
        content_id: ID of content to preview
        content_type: Type of content (page, post, etc.)
        redirect_url: URL to redirect to after enabling preview
    
    Returns:
        Preview URL that enables draft mode
    """
    config = get_draft_config()
    
    url = f"{config.enable_url}?"
    
    if redirect_url:
        url += f"redirect={redirect_url}&"
    
    url += f"content_id={content_id}&content_type={content_type}"
    
    return url


def inject_draft_state(html: str) -> str:
    """
    Inject draft state into HTML for client-side hydration.
    
    Adds a script tag with draft state that the client runtime
    can pick up for initialization.
    """
    is_draft = is_draft_mode()
    
    if not is_draft:
        return html
    
    # Inject draft state before </head>
    draft_script = f'''<script>
window.__PYNEXT_DRAFT__ = {{
  enabled: true,
  authenticated: true
}};
</script>
'''
    
    if "</head>" in html:
        html = html.replace("</head>", f"{draft_script}</head>")
    else:
        # Prepend if no head
        html = draft_script + html
    
    return html

