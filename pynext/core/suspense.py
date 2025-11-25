"""
Suspense component for handling async loading states.

Inspired by SolidJS's Suspense, this provides a declarative way to handle
loading states for async resources and lazy components.

Usage:
    Suspense(fallback=Loading())[
        AsyncComponent()
    ]

Features:
    - Automatic fallback rendering while resources load
    - Nested Suspense boundaries
    - Integration with Resource primitive
    - Server-side streaming support
    - Client-side hydration with placeholders
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    Callable,
    List,
    Optional,
    Union,
    TYPE_CHECKING,
)
import contextvars

if TYPE_CHECKING:
    from pynext.core.resource import Resource
    from pynext.core.html import Element


# Context for tracking Suspense boundaries
_suspense_context: contextvars.ContextVar[Optional["SuspenseBoundary"]] = contextvars.ContextVar(
    "suspense_context", default=None
)


class SuspenseState(Enum):
    """Suspense boundary states."""
    PENDING = "pending"      # Has unresolved resources
    RESOLVED = "resolved"    # All resources ready
    FALLBACK = "fallback"    # Showing fallback content
    STREAMING = "streaming"  # Streaming content chunks


@dataclass
class PendingResource:
    """A resource that is pending resolution."""
    id: str
    resource: "Resource"
    placeholder_id: str


@dataclass
class SuspenseBoundary:
    """
    A Suspense boundary that tracks pending resources.
    
    When children render, any Resource in PENDING state registers
    with this boundary. The boundary decides whether to show
    fallback or wait for resolution.
    """
    id: str
    fallback: Any
    parent: Optional["SuspenseBoundary"] = None
    pending: List[PendingResource] = field(default_factory=list)
    state: SuspenseState = SuspenseState.PENDING
    resolved_content: Optional[str] = None
    
    def register_pending(self, resource: "Resource") -> str:
        """
        Register a pending resource and return a placeholder ID.
        
        The placeholder ID is used for streaming replacement.
        """
        placeholder_id = f"suspense-{self.id}-{len(self.pending)}"
        self.pending.append(PendingResource(
            id=resource._id,
            resource=resource,
            placeholder_id=placeholder_id,
        ))
        return placeholder_id
    
    def has_pending(self) -> bool:
        """Check if any resources are still pending."""
        from pynext.core.resource import ResourceState
        return any(
            p.resource.state() in (ResourceState.UNRESOLVED, ResourceState.PENDING)
            for p in self.pending
        )
    
    async def wait_all(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for all pending resources to resolve.
        
        Returns True if all resolved, False if timeout.
        """
        if not self.pending:
            self.state = SuspenseState.RESOLVED
            return True
        
        try:
            tasks = [p.resource.fetch() for p in self.pending]
            if timeout:
                await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=timeout
                )
            else:
                await asyncio.gather(*tasks, return_exceptions=True)
            
            self.state = SuspenseState.RESOLVED
            return True
        except asyncio.TimeoutError:
            self.state = SuspenseState.FALLBACK
            return False
    
    def clear(self) -> None:
        """Clear all pending resources."""
        self.pending.clear()
        self.state = SuspenseState.PENDING


class Suspense:
    """
    Suspense component for handling async loading states.
    
    Wraps children that may have pending Resources or lazy components.
    Shows fallback content while waiting for async operations.
    
    Args:
        fallback: Content to show while loading (default: "Loading...")
        timeout: Max time to wait before showing fallback (streaming mode)
    
    Usage:
        # Basic usage
        Suspense(fallback=div()["Loading..."])[
            UserProfile()  # May contain Resource
        ]
        
        # With custom loading component
        Suspense(fallback=Spinner())[
            DataTable(data=resource)
        ]
        
        # Nested suspense
        Suspense(fallback=PageSkeleton())[
            Header(),
            Suspense(fallback=CardSkeleton())[
                DataCard()
            ]
        ]
    """
    
    def __init__(
        self,
        fallback: Any = None,
        timeout: Optional[float] = None,
    ):
        self.id = f"suspense_{uuid.uuid4().hex[:8]}"
        self.fallback = fallback or _default_fallback()
        self.timeout = timeout
        self.children: List[Any] = []
        self.boundary: Optional[SuspenseBoundary] = None
    
    def __getitem__(self, children: Any) -> "Suspense":
        """Add children using bracket syntax: Suspense()[children]"""
        if isinstance(children, tuple):
            self.children = list(children)
        elif isinstance(children, list):
            self.children = children
        else:
            self.children = [children]
        return self
    
    def __call__(self, *children: Any) -> "Suspense":
        """Add children using call syntax: Suspense()(child1, child2)"""
        self.children = list(children)
        return self
    
    def render(self) -> str:
        """
        Render the Suspense component.
        
        This is the synchronous render path. For streaming,
        use render_streaming() instead.
        """
        # Create boundary and set as current
        parent = _suspense_context.get()
        self.boundary = SuspenseBoundary(
            id=self.id,
            fallback=self.fallback,
            parent=parent,
        )
        
        token = _suspense_context.set(self.boundary)
        
        try:
            # Render children (they will register pending resources)
            content = self._render_children()
            
            # If any resources are pending, show fallback
            if self.boundary.has_pending():
                return self._render_with_fallback(content)
            
            return content
            
        finally:
            _suspense_context.reset(token)
    
    async def render_async(self) -> str:
        """
        Render with async resource resolution.
        
        Waits for all resources to resolve before returning.
        """
        # Create boundary
        parent = _suspense_context.get()
        self.boundary = SuspenseBoundary(
            id=self.id,
            fallback=self.fallback,
            parent=parent,
        )
        
        token = _suspense_context.set(self.boundary)
        
        try:
            # First render pass (collects pending resources)
            content = self._render_children()
            
            # Wait for resources
            if self.boundary.has_pending():
                resolved = await self.boundary.wait_all(timeout=self.timeout)
                
                if resolved:
                    # Re-render with resolved data
                    self.boundary.clear()
                    content = self._render_children()
                else:
                    # Timeout - show fallback
                    return self._render_with_fallback(content)
            
            return content
            
        finally:
            _suspense_context.reset(token)
    
    def _render_children(self) -> str:
        """Render all children to HTML."""
        parts = []
        
        for child in self.children:
            if hasattr(child, 'render'):
                parts.append(child.render())
            elif callable(child):
                result = child()
                if hasattr(result, 'render'):
                    parts.append(result.render())
                else:
                    parts.append(str(result))
            else:
                parts.append(str(child))
        
        return "".join(parts)
    
    def _render_with_fallback(self, content: str) -> str:
        """
        Render with fallback and placeholder for streaming.
        
        The placeholder will be replaced when content resolves.
        """
        # Render fallback
        fallback_html = ""
        if hasattr(self.fallback, 'render'):
            fallback_html = self.fallback.render()
        elif callable(self.fallback):
            result = self.fallback()
            if hasattr(result, 'render'):
                fallback_html = result.render()
            else:
                fallback_html = str(result)
        else:
            fallback_html = str(self.fallback)
        
        # Wrap in container with data attributes for hydration
        return f'''<div data-suspense="{self.id}" data-state="pending">
  <div data-suspense-fallback>{fallback_html}</div>
  <template data-suspense-content>{content}</template>
</div>'''
    
    def get_js_init(self) -> str:
        """Generate JavaScript initialization for client hydration."""
        pending_ids = [p.id for p in (self.boundary.pending if self.boundary else [])]
        
        return f'''__pynext__.createSuspense("{self.id}", {{
  pendingResources: {pending_ids},
  timeout: {self.timeout or "null"}
}});'''


def _default_fallback():
    """Default fallback content."""
    from pynext.core.html import div, span
    return div(class_="suspense-loading")[
        span(class_="spinner")[""],
        span()["Loading..."]
    ]


# =============================================================================
# Suspense Context Utilities
# =============================================================================

def get_suspense_boundary() -> Optional[SuspenseBoundary]:
    """Get the current Suspense boundary (if any)."""
    return _suspense_context.get()


def register_pending_resource(resource: "Resource") -> Optional[str]:
    """
    Register a pending resource with the nearest Suspense boundary.
    
    Returns the placeholder ID if registered, None otherwise.
    """
    boundary = _suspense_context.get()
    if boundary:
        return boundary.register_pending(resource)
    return None


# =============================================================================
# Show Component (Conditional Rendering)
# =============================================================================

class Show:
    """
    Conditional rendering component.
    
    Only renders children when condition is true.
    Optionally shows fallback when false.
    
    Usage:
        Show(when=user.loading, fallback=Spinner())[
            UserProfile(user=user())
        ]
    """
    
    def __init__(
        self,
        when: Any,
        fallback: Any = None,
    ):
        self.condition = when
        self.fallback = fallback
        self.children: List[Any] = []
    
    def __getitem__(self, children: Any) -> "Show":
        """Add children using bracket syntax."""
        if isinstance(children, tuple):
            self.children = list(children)
        elif isinstance(children, list):
            self.children = children
        else:
            self.children = [children]
        return self
    
    def render(self) -> str:
        """Render based on condition."""
        # Evaluate condition
        condition_value = self.condition() if callable(self.condition) else self.condition
        
        if condition_value:
            # Render children
            parts = []
            for child in self.children:
                if hasattr(child, 'render'):
                    parts.append(child.render())
                elif callable(child):
                    result = child()
                    if hasattr(result, 'render'):
                        parts.append(result.render())
                    else:
                        parts.append(str(result))
                else:
                    parts.append(str(child))
            return "".join(parts)
        else:
            # Render fallback
            if self.fallback is None:
                return ""
            if hasattr(self.fallback, 'render'):
                return self.fallback.render()
            elif callable(self.fallback):
                result = self.fallback()
                if hasattr(result, 'render'):
                    return result.render()
                return str(result)
            return str(self.fallback)


# =============================================================================
# Switch/Match Components
# =============================================================================

class Switch:
    """
    Multi-way conditional rendering.
    
    Like a switch statement - renders first matching case.
    
    Usage:
        Switch()[
            Match(when=lambda: status() == "loading")[Spinner()],
            Match(when=lambda: status() == "error")[ErrorMessage()],
            Match(when=lambda: status() == "ready")[Content()],
            Match()[DefaultContent()]  # No condition = default
        ]
    """
    
    def __init__(self):
        self.cases: List["Match"] = []
    
    def __getitem__(self, cases: Any) -> "Switch":
        """Add cases using bracket syntax."""
        if isinstance(cases, tuple):
            self.cases = list(cases)
        elif isinstance(cases, list):
            self.cases = cases
        else:
            self.cases = [cases]
        return self
    
    def render(self) -> str:
        """Render the first matching case."""
        for case in self.cases:
            if isinstance(case, Match):
                if case.matches():
                    return case.render()
        return ""


class Match:
    """
    A case in a Switch component.
    
    Usage:
        Match(when=lambda: count() > 10)[HighCount()]
    """
    
    def __init__(self, when: Any = True):
        self.condition = when
        self.children: List[Any] = []
    
    def __getitem__(self, children: Any) -> "Match":
        """Add children using bracket syntax."""
        if isinstance(children, tuple):
            self.children = list(children)
        elif isinstance(children, list):
            self.children = children
        else:
            self.children = [children]
        return self
    
    def matches(self) -> bool:
        """Check if this case matches."""
        if self.condition is True:
            return True
        if callable(self.condition):
            return bool(self.condition())
        return bool(self.condition)
    
    def render(self) -> str:
        """Render children."""
        parts = []
        for child in self.children:
            if hasattr(child, 'render'):
                parts.append(child.render())
            elif callable(child):
                result = child()
                if hasattr(result, 'render'):
                    parts.append(result.render())
                else:
                    parts.append(str(result))
            else:
                parts.append(str(child))
        return "".join(parts)


# =============================================================================
# ErrorBoundary Component
# =============================================================================

class ErrorBoundary:
    """
    Error boundary for catching render errors.
    
    Usage:
        ErrorBoundary(fallback=lambda err: ErrorDisplay(err))[
            RiskyComponent()
        ]
    """
    
    def __init__(self, fallback: Callable[[Exception], Any]):
        self.fallback = fallback
        self.children: List[Any] = []
        self.error: Optional[Exception] = None
    
    def __getitem__(self, children: Any) -> "ErrorBoundary":
        """Add children using bracket syntax."""
        if isinstance(children, tuple):
            self.children = list(children)
        elif isinstance(children, list):
            self.children = children
        else:
            self.children = [children]
        return self
    
    def render(self) -> str:
        """Render, catching any errors."""
        try:
            parts = []
            for child in self.children:
                if hasattr(child, 'render'):
                    parts.append(child.render())
                elif callable(child):
                    result = child()
                    if hasattr(result, 'render'):
                        parts.append(result.render())
                    else:
                        parts.append(str(result))
                else:
                    parts.append(str(child))
            return "".join(parts)
        except Exception as e:
            self.error = e
            fallback_result = self.fallback(e)
            if hasattr(fallback_result, 'render'):
                return fallback_result.render()
            return str(fallback_result)

