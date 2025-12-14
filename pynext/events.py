"""
PyNext Event Modifiers

SolidJS-inspired event handler wrappers for common DOM event patterns.
These wrappers let you declaratively control event behavior without
needing to access the event object directly.

Example:
    from pynext.events import stop, prevent, self_only
    
    # Only close modal when clicking overlay (not children)
    div(onclick=self_only(lambda: show.set(False)))[
        div(class_="modal-content")[...]
    ]
    
    # Stop propagation
    button(onclick=stop(lambda: handle_click()))[...]
    
    # Prevent form submission default
    form(onsubmit=prevent(lambda: handle_submit()))[...]
    
    # Compose modifiers
    button(onclick=stop(prevent(lambda: handle())))[...]
"""

from dataclasses import dataclass, field
from typing import Callable, Union


@dataclass
class EventHandler:
    """
    Wrapper for event handlers with modifier metadata.
    
    This class carries both the handler function and flags for
    event modifiers that should be applied when the handler runs.
    
    Attributes:
        fn: The actual handler function to call
        stop: If True, call event.stopPropagation() before handler
        prevent: If True, call event.preventDefault() before handler
        self_only: If True, only fire if event.target === event.currentTarget
        once: If True, handler fires only once then removes itself
        capture: If True, use capture phase instead of bubble phase
    """
    fn: Callable
    stop: bool = False
    prevent: bool = False
    self_only: bool = False
    once: bool = False
    capture: bool = False
    
    def __call__(self, *args, **kwargs):
        """Allow EventHandler to be called directly (for testing)."""
        return self.fn(*args, **kwargs)
    
    def with_modifiers(self, **kwargs) -> "EventHandler":
        """Return a new EventHandler with additional modifiers."""
        return EventHandler(
            fn=self.fn,
            stop=kwargs.get("stop", self.stop),
            prevent=kwargs.get("prevent", self.prevent),
            self_only=kwargs.get("self_only", self.self_only),
            once=kwargs.get("once", self.once),
            capture=kwargs.get("capture", self.capture),
        )
    
    def get_modifiers(self) -> dict:
        """Get a dict of active modifiers for serialization."""
        mods = {}
        if self.stop:
            mods["stop"] = True
        if self.prevent:
            mods["prevent"] = True
        if self.self_only:
            mods["self_only"] = True
        if self.once:
            mods["once"] = True
        if self.capture:
            mods["capture"] = True
        return mods


def stop(handler: Union[Callable, EventHandler]) -> EventHandler:
    """
    Wrap handler to call stopPropagation() before execution.
    
    Prevents the event from bubbling up to parent elements.
    Use this for nested interactive elements where you don't want
    clicks to trigger parent handlers.
    
    Args:
        handler: A callable or existing EventHandler to wrap
        
    Returns:
        EventHandler with stop=True
        
    Example:
        # Inner button click doesn't trigger outer div's handler
        div(onclick=lambda: outer_action())[
            button(onclick=stop(lambda: inner_action()))[...]
        ]
    """
    if isinstance(handler, EventHandler):
        return handler.with_modifiers(stop=True)
    return EventHandler(fn=handler, stop=True)


def prevent(handler: Union[Callable, EventHandler]) -> EventHandler:
    """
    Wrap handler to call preventDefault() before execution.
    
    Prevents the default browser behavior for the event.
    Use this for form submissions, link clicks, etc. where you
    want to handle the action yourself.
    
    Args:
        handler: A callable or existing EventHandler to wrap
        
    Returns:
        EventHandler with prevent=True
        
    Example:
        # Handle form submission without page reload
        form(onsubmit=prevent(lambda: handle_submit()))[...]
        
        # Handle link click without navigation
        a(href="/page", onclick=prevent(lambda: navigate()))[...]
    """
    if isinstance(handler, EventHandler):
        return handler.with_modifiers(prevent=True)
    return EventHandler(fn=handler, prevent=True)


def self_only(handler: Union[Callable, EventHandler]) -> EventHandler:
    """
    Only fire handler if event.target === event.currentTarget.
    
    This means the handler only fires when the element itself is
    clicked, not when a child element is clicked. Perfect for modals
    where you want clicking the overlay to close, but not clicks
    on the modal content.
    
    Args:
        handler: A callable or existing EventHandler to wrap
        
    Returns:
        EventHandler with self_only=True
        
    Example:
        # Only close modal when clicking the overlay, not content
        div(class_="overlay", onclick=self_only(lambda: close_modal()))[
            div(class_="modal-content")[
                # Clicks here don't trigger close_modal
                ...
            ]
        ]
    """
    if isinstance(handler, EventHandler):
        return handler.with_modifiers(self_only=True)
    return EventHandler(fn=handler, self_only=True)


def once(handler: Union[Callable, EventHandler]) -> EventHandler:
    """
    Fire handler only once, then remove the listener.
    
    After the handler fires once, it automatically removes itself
    from the element. Useful for one-time actions like initialization
    clicks or first-interaction events.
    
    Args:
        handler: A callable or existing EventHandler to wrap
        
    Returns:
        EventHandler with once=True
        
    Example:
        # Show tooltip on first hover only
        div(onmouseenter=once(lambda: show_intro_tooltip()))[...]
    """
    if isinstance(handler, EventHandler):
        return handler.with_modifiers(once=True)
    return EventHandler(fn=handler, once=True)


def capture(handler: Union[Callable, EventHandler]) -> EventHandler:
    """
    Use capture phase instead of bubble phase.
    
    By default, event listeners fire during the "bubble" phase
    (from target up to root). Capture phase fires from root down
    to target. Use this when you need to intercept events before
    they reach their target.
    
    Args:
        handler: A callable or existing EventHandler to wrap
        
    Returns:
        EventHandler with capture=True
        
    Example:
        # Catch all clicks before they reach targets
        div(onclick=capture(lambda: log_click()))[...]
    """
    if isinstance(handler, EventHandler):
        return handler.with_modifiers(capture=True)
    return EventHandler(fn=handler, capture=True)


# Convenience aliases
stop_propagation = stop
prevent_default = prevent


__all__ = [
    "EventHandler",
    "stop",
    "prevent", 
    "self_only",
    "once",
    "capture",
    "stop_propagation",
    "prevent_default",
]

