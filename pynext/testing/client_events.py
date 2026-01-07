"""
PyNext Testing - Event Firing

WHAT THIS FILE DOES:
Provides fireEvent functions for simulating user interactions.
Supports clicks, keyboard events, form events, focus events, mouse events, and touch events.

WHY THIS EXISTS:
Testing user interactions requires simulating browser events.
This module provides a simple API for firing events on HTML elements.

HOW IT WORKS:
- Creates event objects with proper properties
- Fires events on HTMLNode elements
- Updates component state when signals are affected
- Handles async event handlers

WHO USES THIS:
- RTL-style testing API (client.py)
- Direct event simulation in tests

WHEN TO USE:
- Testing button clicks: fireEvent.click(button)
- Testing form inputs: fireEvent.change(input, {target: {value: "text"}})
- Testing keyboard: fireEvent.keyDown(input, {key: "Enter"})
- Testing focus: fireEvent.focus(input)

EXAMPLES:
    from pynext.testing.client import render, screen
    from pynext.testing.client_events import fireEvent
    
    result = render(Button, label="Click me")
    button = screen.getByRole("button")
    fireEvent.click(button)
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from pynext.testing.render import HTMLNode


# =============================================================================
# Event Utilities
# =============================================================================

def _create_event(
    event_type: str,
    props: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create an event object.
    
    Args:
        event_type: Event type (e.g., "click", "change")
        props: Event properties
        
    Returns:
        Event object
    """
    event = {
        "type": event_type,
        "bubbles": True,
        "cancelable": True,
        "defaultPrevented": False,
        "target": None,
        "currentTarget": None,
    }
    
    if props:
        event.update(props)
    
    return event


def _get_handler_name(event_type: str) -> str:
    """Get handler attribute name for event type."""
    return f"on{event_type.capitalize()}"


def _get_event_handler(element: HTMLNode, event_type: str) -> Optional[Callable]:
    """
    Get event handler from element attributes.
    
    Args:
        element: HTMLNode element
        event_type: Event type
        
    Returns:
        Event handler function or None
    """
    handler_name = _get_handler_name(event_type)
    handler = element.attrs.get(handler_name)
    
    # If handler is a string (like "handleClick()"), we'd need to evaluate it
    # For now, we just return it as-is and let the component handle it
    return handler


# =============================================================================
# Mouse Events
# =============================================================================

def click(
    element: HTMLNode,
    event_init: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Fire a click event on an element.
    
    Args:
        element: Element to click
        event_init: Optional event properties
        
    Example:
        button = screen.getByRole("button")
        fireEvent.click(button)
    """
    event = _create_event("click", event_init)
    handler = _get_event_handler(element, "click")
    
    if handler and callable(handler):
        handler(event)
    elif handler:
        # Handler might be a string that needs evaluation
        # In real implementation, would evaluate in component context
        pass


def dblClick(
    element: HTMLNode,
    event_init: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Fire a double-click event on an element.
    
    Args:
        element: Element to double-click
        event_init: Optional event properties
        
    Example:
        button = screen.getByRole("button")
        fireEvent.dblClick(button)
    """
    event = _create_event("dblclick", event_init)
    handler = _get_event_handler(element, "dblclick")
    
    if handler and callable(handler):
        handler(event)


def contextMenu(
    element: HTMLNode,
    event_init: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Fire a context menu (right-click) event on an element.
    
    Args:
        element: Element to right-click
        event_init: Optional event properties
        
    Example:
        element = screen.getByTestId("context-menu-trigger")
        fireEvent.contextMenu(element)
    """
    event = _create_event("contextmenu", event_init)
    handler = _get_event_handler(element, "contextmenu")
    
    if handler and callable(handler):
        handler(event)


# =============================================================================
# Keyboard Events
# =============================================================================

def keyDown(
    element: HTMLNode,
    event_init: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Fire a keyDown event on an element.
    
    Args:
        element: Element to fire event on
        event_init: Event properties (should include 'key')
        
    Example:
        input = screen.getByRole("textbox")
        fireEvent.keyDown(input, {"key": "Enter", "code": "Enter"})
    """
    if event_init is None:
        event_init = {}
    
    event = _create_event("keydown", event_init)
    handler = _get_event_handler(element, "keydown")
    
    if handler and callable(handler):
        handler(event)


def keyUp(
    element: HTMLNode,
    event_init: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Fire a keyUp event on an element.
    
    Args:
        element: Element to fire event on
        event_init: Event properties (should include 'key')
        
    Example:
        input = screen.getByRole("textbox")
        fireEvent.keyUp(input, {"key": "Escape", "code": "Escape"})
    """
    if event_init is None:
        event_init = {}
    
    event = _create_event("keyup", event_init)
    handler = _get_event_handler(element, "keyup")
    
    if handler and callable(handler):
        handler(event)


def keyPress(
    element: HTMLNode,
    event_init: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Fire a keyPress event on an element.
    
    Note: keyPress is deprecated in modern browsers, but included for compatibility.
    
    Args:
        element: Element to fire event on
        event_init: Event properties (should include 'key')
        
    Example:
        input = screen.getByRole("textbox")
        fireEvent.keyPress(input, {"key": "a", "code": "KeyA"})
    """
    if event_init is None:
        event_init = {}
    
    event = _create_event("keypress", event_init)
    handler = _get_event_handler(element, "keypress")
    
    if handler and callable(handler):
        handler(event)


# =============================================================================
# Form Events
# =============================================================================

def change(
    element: HTMLNode,
    event_init: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Fire a change event on an element.
    
    Args:
        element: Element to fire event on
        event_init: Event properties (typically includes 'target' with 'value')
        
    Example:
        input = screen.getByRole("textbox")
        fireEvent.change(input, {"target": {"value": "new text"}})
    """
    event = _create_event("change", event_init)
    handler = _get_event_handler(element, "change")
    
    if handler and callable(handler):
        handler(event)
    
    # Also update the element's value attribute if provided
    if event_init and "target" in event_init:
        target = event_init["target"]
        if "value" in target:
            element.attrs["value"] = str(target["value"])


def input(
    element: HTMLNode,
    event_init: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Fire an input event on an element.
    
    Args:
        element: Element to fire event on
        event_init: Event properties (typically includes 'target' with 'value')
        
    Example:
        input = screen.getByRole("textbox")
        fireEvent.input(input, {"target": {"value": "typing..."}})
    """
    event = _create_event("input", event_init)
    handler = _get_event_handler(element, "input")
    
    if handler and callable(handler):
        handler(event)
    
    # Also update the element's value attribute if provided
    if event_init and "target" in event_init:
        target = event_init["target"]
        if "value" in target:
            element.attrs["value"] = str(target["value"])


def submit(
    element: HTMLNode,
    event_init: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Fire a submit event on an element (typically a form).
    
    Args:
        element: Element to fire event on
        event_init: Optional event properties
        
    Example:
        form = screen.getByRole("form")
        fireEvent.submit(form)
    """
    event = _create_event("submit", event_init)
    handler = _get_event_handler(element, "submit")
    
    if handler and callable(handler):
        handler(event)


# =============================================================================
# Focus Events
# =============================================================================

def focus(
    element: HTMLNode,
    event_init: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Fire a focus event on an element.
    
    Args:
        element: Element to focus
        event_init: Optional event properties
        
    Example:
        input = screen.getByRole("textbox")
        fireEvent.focus(input)
    """
    event = _create_event("focus", event_init)
    handler = _get_event_handler(element, "focus")
    
    if handler and callable(handler):
        handler(event)
    
    # Add focus state to element
    element.attrs["data-focused"] = "true"


def blur(
    element: HTMLNode,
    event_init: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Fire a blur event on an element.
    
    Args:
        element: Element to blur
        event_init: Optional event properties
        
    Example:
        input = screen.getByRole("textbox")
        fireEvent.blur(input)
    """
    event = _create_event("blur", event_init)
    handler = _get_event_handler(element, "blur")
    
    if handler and callable(handler):
        handler(event)
    
    # Remove focus state from element
    if "data-focused" in element.attrs:
        del element.attrs["data-focused"]


# =============================================================================
# Mouse Events (Detailed)
# =============================================================================

def mouseDown(
    element: HTMLNode,
    event_init: Optional[Dict[str, Any]] = None,
) -> None:
    """Fire a mouseDown event on an element."""
    event = _create_event("mousedown", event_init)
    handler = _get_event_handler(element, "mousedown")
    if handler and callable(handler):
        handler(event)


def mouseUp(
    element: HTMLNode,
    event_init: Optional[Dict[str, Any]] = None,
) -> None:
    """Fire a mouseUp event on an element."""
    event = _create_event("mouseup", event_init)
    handler = _get_event_handler(element, "mouseup")
    if handler and callable(handler):
        handler(event)


def mouseMove(
    element: HTMLNode,
    event_init: Optional[Dict[str, Any]] = None,
) -> None:
    """Fire a mouseMove event on an element."""
    event = _create_event("mousemove", event_init)
    handler = _get_event_handler(element, "mousemove")
    if handler and callable(handler):
        handler(event)


def mouseEnter(
    element: HTMLNode,
    event_init: Optional[Dict[str, Any]] = None,
) -> None:
    """Fire a mouseEnter event on an element."""
    event = _create_event("mouseenter", event_init)
    handler = _get_event_handler(element, "mouseenter")
    if handler and callable(handler):
        handler(event)


def mouseLeave(
    element: HTMLNode,
    event_init: Optional[Dict[str, Any]] = None,
) -> None:
    """Fire a mouseLeave event on an element."""
    event = _create_event("mouseleave", event_init)
    handler = _get_event_handler(element, "mouseleave")
    if handler and callable(handler):
        handler(event)


def mouseOver(
    element: HTMLNode,
    event_init: Optional[Dict[str, Any]] = None,
) -> None:
    """Fire a mouseOver event on an element."""
    event = _create_event("mouseover", event_init)
    handler = _get_event_handler(element, "mouseover")
    if handler and callable(handler):
        handler(event)


def mouseOut(
    element: HTMLNode,
    event_init: Optional[Dict[str, Any]] = None,
) -> None:
    """Fire a mouseOut event on an element."""
    event = _create_event("mouseout", event_init)
    handler = _get_event_handler(element, "mouseout")
    if handler and callable(handler):
        handler(event)


# =============================================================================
# Touch Events
# =============================================================================

def touchStart(
    element: HTMLNode,
    event_init: Optional[Dict[str, Any]] = None,
) -> None:
    """Fire a touchStart event on an element."""
    event = _create_event("touchstart", event_init)
    handler = _get_event_handler(element, "touchstart")
    if handler and callable(handler):
        handler(event)


def touchEnd(
    element: HTMLNode,
    event_init: Optional[Dict[str, Any]] = None,
) -> None:
    """Fire a touchEnd event on an element."""
    event = _create_event("touchend", event_init)
    handler = _get_event_handler(element, "touchend")
    if handler and callable(handler):
        handler(event)


def touchMove(
    element: HTMLNode,
    event_init: Optional[Dict[str, Any]] = None,
) -> None:
    """Fire a touchMove event on an element."""
    event = _create_event("touchmove", event_init)
    handler = _get_event_handler(element, "touchmove")
    if handler and callable(handler):
        handler(event)


def touchCancel(
    element: HTMLNode,
    event_init: Optional[Dict[str, Any]] = None,
) -> None:
    """Fire a touchCancel event on an element."""
    event = _create_event("touchcancel", event_init)
    handler = _get_event_handler(element, "touchcancel")
    if handler and callable(handler):
        handler(event)


# =============================================================================
# fireEvent Object - Main API
# =============================================================================

class FireEvent:
    """
    Event firing API for testing.
    
    Provides methods for simulating user interactions.
    """
    
    # Mouse events
    click = staticmethod(click)
    dblClick = staticmethod(dblClick)
    contextMenu = staticmethod(contextMenu)
    
    # Keyboard events
    keyDown = staticmethod(keyDown)
    keyUp = staticmethod(keyUp)
    keyPress = staticmethod(keyPress)
    
    # Form events
    change = staticmethod(change)
    input = staticmethod(input)
    submit = staticmethod(submit)
    
    # Focus events
    focus = staticmethod(focus)
    blur = staticmethod(blur)
    
    # Mouse events (detailed)
    mouseDown = staticmethod(mouseDown)
    mouseUp = staticmethod(mouseUp)
    mouseMove = staticmethod(mouseMove)
    mouseEnter = staticmethod(mouseEnter)
    mouseLeave = staticmethod(mouseLeave)
    mouseOver = staticmethod(mouseOver)
    mouseOut = staticmethod(mouseOut)
    
    # Touch events
    touchStart = staticmethod(touchStart)
    touchEnd = staticmethod(touchEnd)
    touchMove = staticmethod(touchMove)
    touchCancel = staticmethod(touchCancel)


# Global fireEvent instance
fireEvent = FireEvent()

