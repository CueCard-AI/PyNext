"""
Transitions & Navigation for PyNext.

Implements smooth page transitions using the View Transitions API
and SPA-style client-side navigation.

Features:
- View Transitions API integration for smooth animations
- Client-side navigation without full page reloads
- Transition lifecycle hooks (before, during, after)
- Custom transition animations
- Fallback for browsers without View Transitions

Example:
    from pynext import transition, navigate, Link
    
    # Programmatic navigation with transition
    await navigate("/dashboard", transition="slide-left")
    
    # Link component with automatic transitions
    Link(href="/about", transition="fade")["About Us"]
    
    # Custom transition
    @transition("hero-expand")
    def ProductCard(product):
        return div(style=f"view-transition-name: product-{product.id}")[
            img(src=product.image),
            h2()[product.name]
        ]
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

from pynext.core.html import Element, a, div, script


T = TypeVar('T')


class TransitionType(Enum):
    """Built-in transition types."""
    
    NONE = "none"           # No transition
    FADE = "fade"           # Crossfade
    SLIDE_LEFT = "slide-left"   # Slide from right
    SLIDE_RIGHT = "slide-right"  # Slide from left
    SLIDE_UP = "slide-up"       # Slide from bottom
    SLIDE_DOWN = "slide-down"   # Slide from top
    SCALE = "scale"         # Scale in/out
    MORPH = "morph"         # Morph between states


@dataclass
class TransitionConfig:
    """Configuration for a transition."""
    
    # Transition type or custom name
    type: Union[TransitionType, str] = TransitionType.FADE
    
    # Duration in milliseconds
    duration: int = 300
    
    # Easing function
    easing: str = "ease-in-out"
    
    # Delay before starting
    delay: int = 0
    
    # Whether to use View Transitions API
    use_view_transitions: bool = True
    
    # Fallback animation for unsupported browsers
    fallback: Optional[str] = None
    
    # Custom CSS for the transition
    custom_css: Optional[str] = None


@dataclass
class NavigationState:
    """State of a navigation operation."""
    
    # Unique navigation ID
    id: str
    
    # Source URL
    from_url: str
    
    # Destination URL
    to_url: str
    
    # Transition config
    transition: TransitionConfig
    
    # Navigation state
    state: str = "pending"  # pending, transitioning, complete, aborted
    
    # Start time
    started_at: Optional[float] = None
    
    # Error if failed
    error: Optional[str] = None


class TransitionManager:
    """
    Manages page transitions and navigation.
    
    Coordinates between Python server and JavaScript client
    for smooth transitions.
    """
    
    def __init__(self):
        self._active_navigation: Optional[NavigationState] = None
        self._transition_hooks: Dict[str, List[Callable]] = {
            "before": [],
            "during": [],
            "after": [],
            "error": [],
        }
        self._custom_transitions: Dict[str, TransitionConfig] = {}
    
    def register_transition(
        self, 
        name: str, 
        config: TransitionConfig
    ) -> None:
        """Register a custom transition."""
        self._custom_transitions[name] = config
    
    def get_transition(self, name: str) -> TransitionConfig:
        """Get a transition config by name."""
        if name in self._custom_transitions:
            return self._custom_transitions[name]
        
        # Check built-in types
        try:
            trans_type = TransitionType(name)
            return TransitionConfig(type=trans_type)
        except ValueError:
            return TransitionConfig(type=TransitionType.FADE)
    
    def on_before(self, callback: Callable) -> Callable:
        """Register a before-navigation hook."""
        self._transition_hooks["before"].append(callback)
        return callback
    
    def on_after(self, callback: Callable) -> Callable:
        """Register an after-navigation hook."""
        self._transition_hooks["after"].append(callback)
        return callback
    
    def on_error(self, callback: Callable) -> Callable:
        """Register an error hook."""
        self._transition_hooks["error"].append(callback)
        return callback


# Global transition manager
_transition_manager = TransitionManager()


def get_transition_manager() -> TransitionManager:
    """Get the global transition manager."""
    return _transition_manager


# =============================================================================
# Transition Decorator
# =============================================================================

def transition(
    name: Optional[str] = None,
    duration: int = 300,
    easing: str = "ease-in-out",
) -> Callable[[T], T]:
    """
    Decorator to add view transition name to a component.
    
    Args:
        name: Transition name (auto-generated if not provided)
        duration: Transition duration in ms
        easing: CSS easing function
    
    Example:
        @transition("hero-image")
        def ProductImage(product):
            return img(src=product.image)
    """
    def decorator(func: T) -> T:
        transition_name = name or func.__name__
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # Add view-transition-name to the element
            if hasattr(result, '_attrs'):
                if 'style' in result._attrs:
                    result._attrs['style'] += f"; view-transition-name: {transition_name}"
                else:
                    result._attrs['style'] = f"view-transition-name: {transition_name}"
            
            return result
        
        wrapper._transition_name = transition_name
        wrapper._transition_duration = duration
        wrapper._transition_easing = easing
        
        return wrapper
    
    return decorator


# =============================================================================
# Link Component
# =============================================================================

def Link(
    href: str,
    transition: Union[TransitionType, str] = TransitionType.FADE,
    prefetch: bool = True,
    replace: bool = False,
    **attrs
) -> Element:
    """
    Navigation link with transitions support.
    
    Args:
        href: Destination URL
        transition: Transition type or name
        prefetch: Whether to prefetch on hover
        replace: Replace history instead of push
        **attrs: Additional HTML attributes
    
    Example:
        Link(href="/dashboard", transition="slide-left")["Dashboard"]
        Link(href="/home", prefetch=False)["Home"]
    """
    trans_name = transition.value if isinstance(transition, TransitionType) else transition
    
    link_attrs = {
        "href": href,
        "data-pynext-link": "true",
        "data-transition": trans_name,
        **attrs
    }
    
    if prefetch:
        link_attrs["data-prefetch"] = "hover"
    
    if replace:
        link_attrs["data-replace"] = "true"
    
    return a(**link_attrs)


# =============================================================================
# Navigation Functions
# =============================================================================

def navigate_script(
    to: str,
    transition: Union[TransitionType, str] = TransitionType.FADE,
    replace: bool = False,
) -> str:
    """
    Generate JavaScript for programmatic navigation.
    
    Returns JavaScript code that can be executed client-side.
    """
    trans_name = transition.value if isinstance(transition, TransitionType) else transition
    
    return f"""
__pynext__.navigate("{to}", {{
    transition: "{trans_name}",
    replace: {str(replace).lower()}
}});
"""


def back_script(transition: Union[TransitionType, str] = TransitionType.SLIDE_RIGHT) -> str:
    """Generate JavaScript for going back in history."""
    trans_name = transition.value if isinstance(transition, TransitionType) else transition
    return f'__pynext__.back({{ transition: "{trans_name}" }});'


def forward_script(transition: Union[TransitionType, str] = TransitionType.SLIDE_LEFT) -> str:
    """Generate JavaScript for going forward in history."""
    trans_name = transition.value if isinstance(transition, TransitionType) else transition
    return f'__pynext__.forward({{ transition: "{trans_name}" }});'


# =============================================================================
# Transition CSS
# =============================================================================

def get_transition_css() -> str:
    """
    Get CSS for built-in transitions.
    
    Returns CSS that should be included in the page head.
    """
    return """
/* PyNext View Transitions */
@view-transition {
    navigation: auto;
}

/* Fade transition (default) */
::view-transition-old(root),
::view-transition-new(root) {
    animation-duration: 0.3s;
    animation-timing-function: ease-in-out;
}

::view-transition-old(root) {
    animation-name: pynext-fade-out;
}

::view-transition-new(root) {
    animation-name: pynext-fade-in;
}

@keyframes pynext-fade-in {
    from { opacity: 0; }
    to { opacity: 1; }
}

@keyframes pynext-fade-out {
    from { opacity: 1; }
    to { opacity: 0; }
}

/* Slide left transition */
[data-transition="slide-left"]::view-transition-old(root) {
    animation-name: pynext-slide-out-left;
}

[data-transition="slide-left"]::view-transition-new(root) {
    animation-name: pynext-slide-in-left;
}

@keyframes pynext-slide-out-left {
    from { transform: translateX(0); }
    to { transform: translateX(-100%); opacity: 0; }
}

@keyframes pynext-slide-in-left {
    from { transform: translateX(100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}

/* Slide right transition */
[data-transition="slide-right"]::view-transition-old(root) {
    animation-name: pynext-slide-out-right;
}

[data-transition="slide-right"]::view-transition-new(root) {
    animation-name: pynext-slide-in-right;
}

@keyframes pynext-slide-out-right {
    from { transform: translateX(0); }
    to { transform: translateX(100%); opacity: 0; }
}

@keyframes pynext-slide-in-right {
    from { transform: translateX(-100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}

/* Slide up transition */
[data-transition="slide-up"]::view-transition-old(root) {
    animation-name: pynext-slide-out-up;
}

[data-transition="slide-up"]::view-transition-new(root) {
    animation-name: pynext-slide-in-up;
}

@keyframes pynext-slide-out-up {
    from { transform: translateY(0); }
    to { transform: translateY(-100%); opacity: 0; }
}

@keyframes pynext-slide-in-up {
    from { transform: translateY(100%); opacity: 0; }
    to { transform: translateY(0); opacity: 1; }
}

/* Slide down transition */
[data-transition="slide-down"]::view-transition-old(root) {
    animation-name: pynext-slide-out-down;
}

[data-transition="slide-down"]::view-transition-new(root) {
    animation-name: pynext-slide-in-down;
}

@keyframes pynext-slide-out-down {
    from { transform: translateY(0); }
    to { transform: translateY(100%); opacity: 0; }
}

@keyframes pynext-slide-in-down {
    from { transform: translateY(-100%); opacity: 0; }
    to { transform: translateY(0); opacity: 1; }
}

/* Scale transition */
[data-transition="scale"]::view-transition-old(root) {
    animation-name: pynext-scale-out;
}

[data-transition="scale"]::view-transition-new(root) {
    animation-name: pynext-scale-in;
}

@keyframes pynext-scale-out {
    from { transform: scale(1); }
    to { transform: scale(0.95); opacity: 0; }
}

@keyframes pynext-scale-in {
    from { transform: scale(1.05); opacity: 0; }
    to { transform: scale(1); opacity: 1; }
}

/* No transition */
[data-transition="none"]::view-transition-old(root),
[data-transition="none"]::view-transition-new(root) {
    animation: none;
}

/* Navigation loading indicator */
.pynext-nav-loading {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #3b82f6, #8b5cf6);
    transform-origin: left;
    animation: pynext-loading 1s ease-in-out infinite;
    z-index: 9999;
}

@keyframes pynext-loading {
    0% { transform: scaleX(0); }
    50% { transform: scaleX(0.5); }
    100% { transform: scaleX(1); }
}
"""


def get_transition_style_tag() -> str:
    """Get a style tag with transition CSS."""
    return f"<style>{get_transition_css()}</style>"


# =============================================================================
# Page Wrapper for Transitions
# =============================================================================

@dataclass
class PageTransition:
    """
    Wrapper for page content with transition support.
    """
    
    # Page content
    content: Any
    
    # Transition name for this page
    name: str = "root"
    
    # Page-specific transition config
    config: Optional[TransitionConfig] = None
    
    def render(self) -> str:
        """Render the page with transition attributes."""
        content_html = ""
        if hasattr(self.content, 'render'):
            content_html = self.content.render()
        else:
            content_html = str(self.content)
        
        style = f"view-transition-name: {self.name}"
        
        return f'<div data-page-transition="{self.name}" style="{style}">{content_html}</div>'


# =============================================================================
# Navigation Events
# =============================================================================

@dataclass
class NavigationEvent:
    """Event emitted during navigation."""
    
    type: str  # "start", "complete", "error", "abort"
    from_url: str
    to_url: str
    transition: str
    timestamp: float = 0
    error: Optional[str] = None


def generate_navigation_data(
    routes: List[str],
    current_route: str,
    prefetch_routes: Optional[List[str]] = None,
) -> str:
    """
    Generate JSON data for client-side navigation.
    
    This data is used by the navigation runtime.
    """
    data = {
        "routes": routes,
        "current": current_route,
        "prefetch": prefetch_routes or [],
        "viewTransitionsSupported": True,  # Client will verify
    }
    
    return json.dumps(data)


def get_navigation_script(
    routes: List[str],
    current_route: str,
    prefetch_routes: Optional[List[str]] = None,
) -> str:
    """Generate script tag with navigation data."""
    data = generate_navigation_data(routes, current_route, prefetch_routes)
    
    return f'''<script>
window.__PYNEXT_NAV__ = {data};
</script>'''

