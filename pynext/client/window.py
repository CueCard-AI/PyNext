"""
PyNext Client - Window Interface

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Provides Python type stubs for the browser Window interface. The Window object
represents the browser window and provides access to global browser APIs like
getComputedStyle, matchMedia, and more.

=============================================================================
WHY THIS EXISTS
=============================================================================

The Window API is essential for:
- Getting computed styles (final rendered CSS values)
- Media query detection (responsive design)
- Browser feature detection
- Global browser utilities

All APIs transpile directly to JavaScript with zero runtime overhead.

=============================================================================
HOW IT WORKS
=============================================================================

These are type stubs that:
1. Define the Python API that mirrors JavaScript Window API exactly
2. Provide type information for static analysis and IDE autocompletion
3. Transpile to identical JavaScript (passthrough - no transformation)

Example:
    window.getComputedStyle(el)  ->  window.getComputedStyle(el)

=============================================================================
WHO USES THIS
=============================================================================

- Web developers querying computed styles
- Responsive design implementations using matchMedia
- The transpiler for passthrough detection
- IDEs for autocompletion and type checking

=============================================================================
EXAMPLES
=============================================================================

    from pynext.client import window, document
    
    # Get computed styles
    el = document.getElementById("box")
    computed = window.getComputedStyle(el)
    actual_width = computed.width  # "200px"
    
    # Computed styles for pseudo-elements
    before_styles = window.getComputedStyle(el, "::before")
    
    # Media query detection
    is_mobile = window.matchMedia("(max-width: 768px)").matches
"""

from __future__ import annotations
from typing import (
    Any,
    Callable,
    List,
    Optional,
    TYPE_CHECKING,
)

if TYPE_CHECKING:
    from pynext.client.dom import Element, CSSStyleDeclaration


# =============================================================================
# MediaQueryList
# =============================================================================

class MediaQueryList:
    """
    WHO: Developers implementing responsive design
    WHAT: Represents results of a media query
    WHEN: Use with window.matchMedia() to detect screen sizes/features
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Enables responsive behavior without CSS-only solutions
    HOW: Passthrough to JavaScript - same API, zero runtime cost
    
    Example:
        mql = window.matchMedia("(max-width: 768px)")
        if mql.matches:
            # Mobile layout
            ...
        
        # Listen for changes
        def on_change(event):
            if event.matches:
                print("Now mobile")
        mql.addEventListener("change", on_change)
    """
    
    @property
    def matches(self) -> bool:
        """True if document matches the media query."""
        ...
    
    @property
    def media(self) -> str:
        """The media query string."""
        ...
    
    def addEventListener(
        self,
        type: str,
        listener: Callable[[MediaQueryListEvent], None],
        options: Optional[dict] = None
    ) -> None:
        """Add a listener for media query changes."""
        ...
    
    def removeEventListener(
        self,
        type: str,
        listener: Callable[[MediaQueryListEvent], None],
        options: Optional[dict] = None
    ) -> None:
        """Remove a media query change listener."""
        ...


class MediaQueryListEvent:
    """Event fired when a media query's match status changes."""
    
    @property
    def matches(self) -> bool:
        """True if media query now matches."""
        ...
    
    @property
    def media(self) -> str:
        """The media query string."""
        ...


# =============================================================================
# Window Interface
# =============================================================================

class Window:
    """
    WHO: Web developers needing browser-level APIs
    WHAT: Represents the browser window
    WHEN: Use for computed styles, media queries, global utilities
    WHERE: Client-side code (transpiled to JavaScript)
    WHY: Provides access to essential browser APIs
    HOW: Passthrough to JavaScript - same API, zero runtime cost
    
    Key Features:
        - getComputedStyle(): Get final rendered CSS values
        - matchMedia(): Detect responsive breakpoints
        - scroll utilities: scrollTo, scrollBy
        - viewport dimensions: innerWidth, innerHeight
    
    Example:
        from pynext.client import window, document
        
        # Get computed styles
        el = document.getElementById("box")
        styles = window.getComputedStyle(el)
        print(styles.backgroundColor)  # "rgb(255, 0, 0)"
        
        # Pseudo-element styles
        before = window.getComputedStyle(el, "::before")
        print(before.content)
        
        # Media queries
        if window.matchMedia("(prefers-color-scheme: dark)").matches:
            apply_dark_theme()
    """
    
    # =========================================================================
    # Viewport Properties
    # =========================================================================
    
    @property
    def innerWidth(self) -> int:
        """Viewport width in pixels (excludes scrollbar)."""
        ...
    
    @property
    def innerHeight(self) -> int:
        """Viewport height in pixels (excludes scrollbar)."""
        ...
    
    @property
    def outerWidth(self) -> int:
        """Browser window width in pixels."""
        ...
    
    @property
    def outerHeight(self) -> int:
        """Browser window height in pixels."""
        ...
    
    @property
    def scrollX(self) -> float:
        """Horizontal scroll position."""
        ...
    
    @property
    def scrollY(self) -> float:
        """Vertical scroll position."""
        ...
    
    @property
    def pageXOffset(self) -> float:
        """Alias for scrollX."""
        ...
    
    @property
    def pageYOffset(self) -> float:
        """Alias for scrollY."""
        ...
    
    @property
    def devicePixelRatio(self) -> float:
        """Ratio of physical pixels to CSS pixels."""
        ...
    
    # =========================================================================
    # Computed Styles
    # =========================================================================
    
    def getComputedStyle(
        self,
        element: Element,
        pseudoElement: Optional[str] = None
    ) -> CSSStyleDeclaration:
        """
        Get the computed style of an element.
        
        Computed styles represent the final, rendered CSS values after all
        stylesheets, inheritance, and browser defaults have been applied.
        
        Args:
            element: The element to get styles for
            pseudoElement: Optional pseudo-element ("::before", "::after")
        
        Returns:
            CSSStyleDeclaration with computed values
        
        Example:
            # Get element's computed styles
            el = document.getElementById("box")
            computed = window.getComputedStyle(el)
            print(computed.width)           # "200px"
            print(computed.backgroundColor) # "rgb(255, 0, 0)"
            
            # Get CSS variable value
            color = computed.getPropertyValue("--primary-color")
            
            # Pseudo-element styles
            before = window.getComputedStyle(el, "::before")
            print(before.content)           # '"Hello"'
        """
        ...
    
    # =========================================================================
    # Media Queries
    # =========================================================================
    
    def matchMedia(self, query: str) -> MediaQueryList:
        """
        Check if a media query matches.
        
        Args:
            query: CSS media query string
        
        Returns:
            MediaQueryList with match status and change events
        
        Example:
            # Check responsive breakpoint
            is_mobile = window.matchMedia("(max-width: 768px)").matches
            
            # Check user preferences
            prefers_dark = window.matchMedia("(prefers-color-scheme: dark)").matches
            prefers_reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches
            
            # Listen for changes
            mql = window.matchMedia("(max-width: 768px)")
            def on_resize(event):
                if event.matches:
                    switch_to_mobile_layout()
            mql.addEventListener("change", on_resize)
        """
        ...
    
    # =========================================================================
    # Scroll Methods
    # =========================================================================
    
    def scrollTo(
        self,
        x: float = 0,
        y: float = 0,
        options: Optional[dict] = None
    ) -> None:
        """
        Scroll to a position.
        
        Args:
            x: Horizontal position
            y: Vertical position
            options: Optional {behavior: "smooth" | "instant" | "auto"}
        
        Example:
            window.scrollTo(0, 0)  # Scroll to top
            window.scrollTo(0, 500, {"behavior": "smooth"})
        """
        ...
    
    def scrollBy(
        self,
        x: float = 0,
        y: float = 0,
        options: Optional[dict] = None
    ) -> None:
        """
        Scroll by a delta.
        
        Args:
            x: Horizontal delta
            y: Vertical delta
            options: Optional {behavior: "smooth" | "instant" | "auto"}
        """
        ...
    
    # =========================================================================
    # Selection
    # =========================================================================
    
    def getSelection(self) -> Any:
        """Get the current text selection."""
        ...
    
    # =========================================================================
    # Focus
    # =========================================================================
    
    def focus(self) -> None:
        """Focus the window."""
        ...
    
    def blur(self) -> None:
        """Remove focus from the window."""
        ...
    
    # =========================================================================
    # Timers (already in scheduling module, but also on window)
    # =========================================================================
    
    def requestAnimationFrame(self, callback: Callable[[float], None]) -> int:
        """Request an animation frame callback."""
        ...
    
    def cancelAnimationFrame(self, handle: int) -> None:
        """Cancel an animation frame request."""
        ...
    
    def requestIdleCallback(
        self,
        callback: Callable[[Any], None],
        options: Optional[dict] = None
    ) -> int:
        """Request an idle callback."""
        ...
    
    def cancelIdleCallback(self, handle: int) -> None:
        """Cancel an idle callback."""
        ...


# =============================================================================
# Global window instance
# =============================================================================

class _WindowInstance(Window):
    """Singleton window instance for Python."""
    pass


# The global window object - transpiles to just 'window' in JavaScript
window: Window = _WindowInstance()


__all__ = [
    "Window",
    "window",
    "MediaQueryList",
    "MediaQueryListEvent",
]

