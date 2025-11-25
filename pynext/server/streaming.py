"""
Streaming HTML Response for PyNext.

Enables progressive rendering by streaming HTML chunks as they become available.
This provides faster Time-to-First-Byte (TTFB) and perceived performance.

Features:
    - Stream shell (head, layout) immediately
    - Stream content chunks as Resources resolve
    - Out-of-order streaming with placeholder replacement
    - Suspense boundary integration
    - Client-side hydration of streamed content
"""

from __future__ import annotations

import asyncio
import json
from typing import (
    Any,
    AsyncGenerator,
    Callable,
    Dict,
    List,
    Optional,
    TYPE_CHECKING,
)
from dataclasses import dataclass, field

from fastapi import Response
from fastapi.responses import StreamingResponse

if TYPE_CHECKING:
    from pynext.core.suspense import Suspense, SuspenseBoundary
    from pynext.core.resource import Resource


@dataclass
class StreamChunk:
    """A chunk of HTML to be streamed."""
    content: str
    chunk_type: str = "html"  # "html", "script", "replacement"
    placeholder_id: Optional[str] = None


@dataclass  
class StreamingContext:
    """Context for managing streaming state."""
    chunks: List[StreamChunk] = field(default_factory=list)
    pending_suspense: Dict[str, "SuspenseBoundary"] = field(default_factory=dict)
    completed: bool = False
    shell_sent: bool = False


class StreamingHTMLResponse(StreamingResponse):
    """
    A streaming HTML response that sends chunks progressively.
    
    Usage:
        async def render():
            yield shell_html
            async for chunk in stream_suspense_boundaries():
                yield chunk
        
        return StreamingHTMLResponse(render())
    """
    
    def __init__(
        self,
        content: AsyncGenerator[str, None],
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        media_type: str = "text/html; charset=utf-8",
    ):
        super().__init__(
            content=content,
            status_code=status_code,
            headers=headers or {},
            media_type=media_type,
        )
        
        # Enable chunked transfer encoding
        self.headers["Transfer-Encoding"] = "chunked"
        self.headers["X-Content-Type-Options"] = "nosniff"


async def stream_page(
    shell: str,
    suspense_boundaries: List["SuspenseBoundary"],
    timeout: float = 10.0,
) -> AsyncGenerator[str, None]:
    """
    Stream a page with Suspense boundaries.
    
    1. Send the shell immediately (head, layout skeleton)
    2. Wait for Suspense boundaries to resolve
    3. Stream replacement scripts for each resolved boundary
    4. Close the response
    
    Args:
        shell: Initial HTML shell (includes placeholders)
        suspense_boundaries: List of Suspense boundaries to resolve
        timeout: Maximum time to wait for all boundaries
    
    Yields:
        HTML chunks
    """
    # 1. Send shell immediately
    yield shell
    
    if not suspense_boundaries:
        return
    
    # 2. Create tasks for each boundary
    pending = {b.id: b for b in suspense_boundaries if b.has_pending()}
    
    if not pending:
        return
    
    # 3. Stream as boundaries resolve
    start_time = asyncio.get_event_loop().time()
    
    while pending:
        elapsed = asyncio.get_event_loop().time() - start_time
        remaining_timeout = max(0.1, timeout - elapsed)
        
        if elapsed >= timeout:
            # Timeout - send error scripts for remaining
            for boundary_id, boundary in pending.items():
                yield _create_timeout_script(boundary_id)
            break
        
        # Wait for any boundary to complete
        tasks = {
            boundary_id: asyncio.create_task(boundary.wait_all(timeout=remaining_timeout))
            for boundary_id, boundary in pending.items()
        }
        
        done, _ = await asyncio.wait(
            tasks.values(),
            timeout=remaining_timeout,
            return_when=asyncio.FIRST_COMPLETED,
        )
        
        # Find which boundaries completed
        completed_ids = []
        for boundary_id, task in tasks.items():
            if task.done():
                completed_ids.append(boundary_id)
        
        # Stream replacement scripts for completed boundaries
        for boundary_id in completed_ids:
            boundary = pending.pop(boundary_id)
            
            if boundary.resolved_content:
                yield _create_replacement_script(
                    boundary_id,
                    boundary.resolved_content,
                )


def _create_replacement_script(boundary_id: str, content: str) -> str:
    """
    Create a script that replaces a Suspense placeholder with resolved content.
    
    This uses a technique similar to React's streaming SSR:
    1. Find the placeholder element
    2. Replace it with the resolved content
    3. Hydrate the new content
    """
    # Escape content for JavaScript string
    escaped_content = json.dumps(content)
    
    return f'''<script>
(function() {{
  var placeholder = document.querySelector('[data-suspense="{boundary_id}"]');
  if (placeholder) {{
    var content = {escaped_content};
    var temp = document.createElement('div');
    temp.innerHTML = content;
    
    // Replace placeholder with content
    while (temp.firstChild) {{
      placeholder.parentNode.insertBefore(temp.firstChild, placeholder);
    }}
    placeholder.remove();
    
    // Trigger hydration for new content
    if (window.__pynext__ && window.__pynext__.hydrateElement) {{
      window.__pynext__.hydrateElement(placeholder.parentNode);
    }}
  }}
}})();
</script>
'''


def _create_timeout_script(boundary_id: str) -> str:
    """Create a script that shows timeout state for a Suspense boundary."""
    return f'''<script>
(function() {{
  var placeholder = document.querySelector('[data-suspense="{boundary_id}"]');
  if (placeholder) {{
    placeholder.setAttribute('data-state', 'timeout');
    // Keep showing fallback, but mark as timed out
    console.warn('Suspense boundary {boundary_id} timed out');
  }}
}})();
</script>
'''


class PageShell:
    """
    Helper for building the initial page shell.
    
    The shell includes:
    - DOCTYPE and html opening
    - Full head content
    - Layout skeleton with Suspense placeholders
    - Initial scripts
    """
    
    def __init__(
        self,
        title: str = "PyNext App",
        head_content: str = "",
        body_class: str = "",
    ):
        self.title = title
        self.head_content = head_content
        self.body_class = body_class
        self.initial_state: Dict[str, Any] = {}
        self.scripts: List[str] = []
    
    def add_state(self, key: str, value: Any) -> "PageShell":
        """Add initial state to be hydrated."""
        self.initial_state[key] = value
        return self
    
    def add_script(self, script: str) -> "PageShell":
        """Add an inline script."""
        self.scripts.append(script)
        return self
    
    def render_opening(self) -> str:
        """Render the opening part of the shell (before content)."""
        state_script = ""
        if self.initial_state:
            state_json = json.dumps(self.initial_state)
            state_script = f'<script>window.__PYNEXT_DATA__ = {state_json};</script>'
        
        extra_scripts = "\n    ".join(f"<script>{s}</script>" for s in self.scripts)
        
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.title}</title>
    {self.head_content}
    {state_script}
    {extra_scripts}
</head>
<body class="{self.body_class}">
'''
    
    def render_closing(self, runtime_url: str = "/__pynext__/runtime.js") -> str:
        """Render the closing part of the shell (after content)."""
        return f'''
<script src="{runtime_url}"></script>
</body>
</html>'''


async def create_streaming_response(
    page_component: Any,
    layouts: List[Any] = None,
    metadata: Optional[Any] = None,
    timeout: float = 10.0,
) -> StreamingHTMLResponse:
    """
    Create a streaming response for a page.
    
    Args:
        page_component: The page component to render
        layouts: Optional list of layout components
        metadata: Optional metadata for the page
        timeout: Maximum time to wait for async content
    
    Returns:
        StreamingHTMLResponse that progressively sends HTML
    """
    from pynext.core.suspense import Suspense, get_suspense_boundary
    
    # Collect Suspense boundaries during render
    suspense_boundaries: List["SuspenseBoundary"] = []
    
    async def generate_chunks():
        # Create shell
        shell = PageShell(
            title=getattr(metadata, 'title', 'PyNext App') if metadata else 'PyNext App',
        )
        
        # Send opening
        yield shell.render_opening()
        
        # Render layouts (usually fast, no async)
        if layouts:
            for layout in layouts:
                if hasattr(layout, 'render_opening'):
                    yield layout.render_opening()
        
        # Render page content (may contain Suspense)
        if hasattr(page_component, 'render_async'):
            content = await page_component.render_async()
        elif hasattr(page_component, 'render'):
            content = page_component.render()
        elif callable(page_component):
            result = page_component()
            if hasattr(result, 'render'):
                content = result.render()
            else:
                content = str(result)
        else:
            content = str(page_component)
        
        yield content
        
        # Close layouts
        if layouts:
            for layout in reversed(layouts):
                if hasattr(layout, 'render_closing'):
                    yield layout.render_closing()
        
        # Send closing and runtime
        yield shell.render_closing()
        
        # Stream Suspense resolutions
        async for chunk in stream_page("", suspense_boundaries, timeout):
            if chunk:  # Skip empty shell
                yield chunk
    
    return StreamingHTMLResponse(generate_chunks())


# =============================================================================
# Progressive Enhancement Utilities
# =============================================================================

def create_loading_skeleton(
    width: str = "100%",
    height: str = "1em",
    count: int = 1,
) -> str:
    """
    Create a loading skeleton placeholder.
    
    These animate while content loads.
    """
    skeletons = []
    for _ in range(count):
        skeletons.append(
            f'<div class="skeleton" style="width:{width};height:{height}"></div>'
        )
    return "\n".join(skeletons)


def create_suspense_placeholder(
    boundary_id: str,
    fallback_html: str,
) -> str:
    """
    Create HTML for a Suspense placeholder.
    
    This will be replaced by the resolved content via streaming.
    """
    return f'''<div data-suspense="{boundary_id}" data-state="pending">
  <div data-suspense-fallback>{fallback_html}</div>
</div>'''


# =============================================================================
# Streaming CSS for Loading States
# =============================================================================

STREAMING_CSS = '''
/* Suspense Loading States */
[data-suspense][data-state="pending"] [data-suspense-fallback] {
  display: block;
}

[data-suspense][data-state="resolved"] [data-suspense-fallback] {
  display: none;
}

[data-suspense][data-state="timeout"] [data-suspense-fallback] {
  opacity: 0.5;
}

/* Skeleton Loading Animation */
.skeleton {
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
  border-radius: 4px;
}

@keyframes skeleton-loading {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* Spinner */
.suspense-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #666;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #e0e0e0;
  border-top-color: #666;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
'''


def get_streaming_css() -> str:
    """Get CSS for streaming/Suspense states."""
    return STREAMING_CSS

