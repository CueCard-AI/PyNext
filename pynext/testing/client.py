"""
PyNext Testing - React Testing Library Style API

WHAT THIS FILE DOES:
Provides a React Testing Library-style API for testing PyNext client components.
Includes render(), screen, fireEvent, waitFor, cleanup, within, act, and renderHook.

WHY THIS EXISTS:
React Testing Library is the gold standard for testing React components.
PyNext needs a similar API that works with Python components and transpiled JavaScript.
This provides familiar testing patterns for developers coming from React.

HOW IT WORKS:
1. Uses existing render.py infrastructure for HTML parsing
2. Provides DOM-like query interface (screen object)
3. Simulates browser events (fireEvent)
4. Handles async updates (waitFor, act)
5. Supports hook testing (renderHook)

WHO USES THIS:
- Developers writing tests for PyNext components
- Testing transpiled JavaScript code
- Integration tests for client-side functionality

WHEN TO USE:
- Testing component rendering
- Testing user interactions (clicks, form inputs)
- Testing async component updates
- Testing custom hooks/effects

EXAMPLES:
    from pynext.testing.client import render, screen, fireEvent, waitFor
    
    def test_button():
        render(Button, label="Click me")
        button = screen.getByRole("button")
        fireEvent.click(button)
        assert screen.getByText("Clicked!")
    
    async def test_async_component():
        render(UserProfile, user_id=123)
        await waitFor(lambda: screen.getByText("John Doe"))
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type, Union
from html.parser import HTMLParser

from pynext.testing.render import (
    render as base_render,
    RenderResult,
    HTMLNode,
    parse_html,
)
from pynext.testing.async_utils import wait_for as async_wait_for
from pynext.testing.client_events import fireEvent


# =============================================================================
# Global State for Testing
# =============================================================================

_rendered_components: List[RenderResult] = []
_current_container: Optional[HTMLNode] = None


# =============================================================================
# RenderResult Extension for RTL
# =============================================================================

@dataclass
class RTLRenderResult:
    """
    Extended RenderResult with RTL-specific features.
    
    Wraps the base RenderResult and adds methods for:
    - DOM queries
    - Event firing
    - Async waiting
    - Cleanup
    """
    result: RenderResult
    container: HTMLNode = field(default=None)
    
    def __post_init__(self):
        """Set container to root if not provided."""
        if self.container is None:
            self.container = self.result.root if self.result.root else HTMLNode("div", {}, [])
    
    def getByText(self, text: Union[str, Any], exact: bool = True) -> HTMLNode:
        """Find element by text content (throws if not found)."""
        from pynext.testing.queries import getByText
        return getByText(self.container, text, exact=exact)
    
    def queryByText(self, text: Union[str, Any], exact: bool = True) -> Optional[HTMLNode]:
        """Find element by text content (returns None if not found)."""
        from pynext.testing.queries import queryByText
        return queryByText(self.container, text, exact=exact)
    
    def findByText(self, text: Union[str, Any], exact: bool = True, timeout: float = 5.0) -> HTMLNode:
        """Find element by text content (async, waits for element)."""
        from pynext.testing.queries import findByText
        return findByText(self.container, text, exact=exact, timeout=timeout)
    
    def getByRole(self, role: str, name: Optional[str] = None) -> HTMLNode:
        """Find element by ARIA role (throws if not found)."""
        from pynext.testing.queries import getByRole
        return getByRole(self.container, role, name=name)
    
    def queryByRole(self, role: str, name: Optional[str] = None) -> Optional[HTMLNode]:
        """Find element by ARIA role (returns None if not found)."""
        from pynext.testing.queries import queryByRole
        return queryByRole(self.container, role, name=name)
    
    def findByRole(self, role: str, name: Optional[str] = None, timeout: float = 5.0) -> HTMLNode:
        """Find element by ARIA role (async, waits for element)."""
        from pynext.testing.queries import findByRole
        return findByRole(self.container, role, name=name, timeout=timeout)
    
    def getByTestId(self, test_id: str) -> HTMLNode:
        """Find element by data-testid attribute (throws if not found)."""
        from pynext.testing.queries import getByTestId
        return getByTestId(self.container, test_id)
    
    def queryByTestId(self, test_id: str) -> Optional[HTMLNode]:
        """Find element by data-testid attribute (returns None if not found)."""
        from pynext.testing.queries import queryByTestId
        return queryByTestId(self.container, test_id)
    
    def findByTestId(self, test_id: str, timeout: float = 5.0) -> HTMLNode:
        """Find element by data-testid attribute (async, waits for element)."""
        from pynext.testing.queries import findByTestId
        return findByTestId(self.container, test_id, timeout=timeout)
    
    def getByLabelText(self, text: Union[str, Any], exact: bool = True) -> HTMLNode:
        """Find element by associated label text (throws if not found)."""
        from pynext.testing.queries import getByLabelText
        return getByLabelText(self.container, text, exact=exact)
    
    def queryByLabelText(self, text: Union[str, Any], exact: bool = True) -> Optional[HTMLNode]:
        """Find element by associated label text (returns None if not found)."""
        from pynext.testing.queries import queryByLabelText
        return queryByLabelText(self.container, text, exact=exact)
    
    def findByLabelText(self, text: Union[str, Any], exact: bool = True, timeout: float = 5.0) -> HTMLNode:
        """Find element by associated label text (async, waits for element)."""
        from pynext.testing.queries import findByLabelText
        return findByLabelText(self.container, text, exact=exact, timeout=timeout)
    
    def getByPlaceholderText(self, text: Union[str, Any], exact: bool = True) -> HTMLNode:
        """Find element by placeholder text (throws if not found)."""
        from pynext.testing.queries import getByPlaceholderText
        return getByPlaceholderText(self.container, text, exact=exact)
    
    def queryByPlaceholderText(self, text: Union[str, Any], exact: bool = True) -> Optional[HTMLNode]:
        """Find element by placeholder text (returns None if not found)."""
        from pynext.testing.queries import queryByPlaceholderText
        return queryByPlaceholderText(self.container, text, exact=exact)
    
    def findByPlaceholderText(self, text: Union[str, Any], exact: bool = True, timeout: float = 5.0) -> HTMLNode:
        """Find element by placeholder text (async, waits for element)."""
        from pynext.testing.queries import findByPlaceholderText
        return findByPlaceholderText(self.container, text, exact=exact, timeout=timeout)
    
    def getAllByText(self, text: Union[str, Any], exact: bool = True) -> List[HTMLNode]:
        """Find all elements by text content (throws if none found)."""
        from pynext.testing.queries import getAllByText
        return getAllByText(self.container, text, exact=exact)
    
    def queryAllByText(self, text: Union[str, Any], exact: bool = True) -> List[HTMLNode]:
        """Find all elements by text content (returns empty list if none found)."""
        from pynext.testing.queries import queryAllByText
        return queryAllByText(self.container, text, exact=exact)
    
    def findAllByText(self, text: Union[str, Any], exact: bool = True, timeout: float = 5.0) -> List[HTMLNode]:
        """Find all elements by text content (async, waits for elements)."""
        from pynext.testing.queries import findAllByText
        return findAllByText(self.container, text, exact=exact, timeout=timeout)
    
    def rerender(self, props: Optional[Dict[str, Any]] = None) -> "RTLRenderResult":
        """Re-render the component with new props."""
        # Get the original component
        component = self.result.component
        if component is None:
            raise ValueError("Cannot rerender: component not found")
        
        # Re-render with new props
        if props:
            # Update component props if it has a way to do so
            if hasattr(component, "__dict__"):
                component.__dict__.update(props)
            elif hasattr(component, "props"):
                component.props.update(props)
        
        # Re-render
        new_result = base_render(component)
        rtl_result = RTLRenderResult(new_result, container=new_result.root)
        
        # Update global state
        if self in _rendered_components:
            idx = _rendered_components.index(self)
            _rendered_components[idx] = rtl_result
        
        return rtl_result


# =============================================================================
# render() - Main Entry Point
# =============================================================================

def render(
    component: Union[Type, Callable, Any],
    *args,
    **props,
) -> RTLRenderResult:
    """
    Render a component for testing (RTL-style).
    
    This is the main entry point for testing. It renders a component
    and returns an RTLRenderResult with query methods and utilities.
    
    Args:
        component: Component class, function, or instance
        *args: Positional arguments for the component
        **props: Keyword arguments (props) for the component
        
    Returns:
        RTLRenderResult with query methods and event firing
        
    Example:
        result = render(Button, label="Click me")
        button = result.getByRole("button")
        fireEvent.click(button)
    """
    # Render using base render function
    result = base_render(component, *args, **props)
    
    # Create RTL wrapper
    rtl_result = RTLRenderResult(result)
    
    # Store in global list for cleanup
    _rendered_components.append(rtl_result)
    global _current_container
    _current_container = rtl_result.container
    
    return rtl_result


# =============================================================================
# screen - Global Screen Object
# =============================================================================

class Screen:
    """
    Global screen object for querying the last rendered component.
    
    This provides convenient access to query methods without
    needing to store the render result.
    
    Example:
        render(Button, label="Click me")
        button = screen.getByRole("button")
        screen.getByText("Click me")
    """
    
    def getByText(self, text: Union[str, Any], exact: bool = True) -> HTMLNode:
        """Find element by text content (throws if not found)."""
        if _current_container is None:
            raise ValueError("No component rendered. Call render() first.")
        from pynext.testing.queries import getByText
        return getByText(_current_container, text, exact=exact)
    
    def queryByText(self, text: Union[str, Any], exact: bool = True) -> Optional[HTMLNode]:
        """Find element by text content (returns None if not found)."""
        if _current_container is None:
            return None
        from pynext.testing.queries import queryByText
        return queryByText(_current_container, text, exact=exact)
    
    async def findByText(self, text: Union[str, Any], exact: bool = True, timeout: float = 5.0) -> HTMLNode:
        """Find element by text content (async, waits for element)."""
        if _current_container is None:
            raise ValueError("No component rendered. Call render() first.")
        from pynext.testing.queries import findByText
        return await findByText(_current_container, text, exact=exact, timeout=timeout)
    
    def getByRole(self, role: str, name: Optional[str] = None) -> HTMLNode:
        """Find element by ARIA role (throws if not found)."""
        if _current_container is None:
            raise ValueError("No component rendered. Call render() first.")
        from pynext.testing.queries import getByRole
        return getByRole(_current_container, role, name=name)
    
    def queryByRole(self, role: str, name: Optional[str] = None) -> Optional[HTMLNode]:
        """Find element by ARIA role (returns None if not found)."""
        if _current_container is None:
            return None
        from pynext.testing.queries import queryByRole
        return queryByRole(_current_container, role, name=name)
    
    async def findByRole(self, role: str, name: Optional[str] = None, timeout: float = 5.0) -> HTMLNode:
        """Find element by ARIA role (async, waits for element)."""
        if _current_container is None:
            raise ValueError("No component rendered. Call render() first.")
        from pynext.testing.queries import findByRole
        return await findByRole(_current_container, role, name=name, timeout=timeout)
    
    def getByTestId(self, test_id: str) -> HTMLNode:
        """Find element by data-testid attribute (throws if not found)."""
        if _current_container is None:
            raise ValueError("No component rendered. Call render() first.")
        from pynext.testing.queries import getByTestId
        return getByTestId(_current_container, test_id)
    
    def queryByTestId(self, test_id: str) -> Optional[HTMLNode]:
        """Find element by data-testid attribute (returns None if not found)."""
        if _current_container is None:
            return None
        from pynext.testing.queries import queryByTestId
        return queryByTestId(_current_container, test_id)
    
    async def findByTestId(self, test_id: str, timeout: float = 5.0) -> HTMLNode:
        """Find element by data-testid attribute (async, waits for element)."""
        if _current_container is None:
            raise ValueError("No component rendered. Call render() first.")
        from pynext.testing.queries import findByTestId
        return await findByTestId(_current_container, test_id, timeout=timeout)
    
    def getByLabelText(self, text: Union[str, Any], exact: bool = True) -> HTMLNode:
        """Find element by associated label text (throws if not found)."""
        if _current_container is None:
            raise ValueError("No component rendered. Call render() first.")
        from pynext.testing.queries import getByLabelText
        return getByLabelText(_current_container, text, exact=exact)
    
    def queryByLabelText(self, text: Union[str, Any], exact: bool = True) -> Optional[HTMLNode]:
        """Find element by associated label text (returns None if not found)."""
        if _current_container is None:
            return None
        from pynext.testing.queries import queryByLabelText
        return queryByLabelText(_current_container, text, exact=exact)
    
    async def findByLabelText(self, text: Union[str, Any], exact: bool = True, timeout: float = 5.0) -> HTMLNode:
        """Find element by associated label text (async, waits for element)."""
        if _current_container is None:
            raise ValueError("No component rendered. Call render() first.")
        from pynext.testing.queries import findByLabelText
        return await findByLabelText(_current_container, text, exact=exact, timeout=timeout)
    
    def getByPlaceholderText(self, text: Union[str, Any], exact: bool = True) -> HTMLNode:
        """Find element by placeholder text (throws if not found)."""
        if _current_container is None:
            raise ValueError("No component rendered. Call render() first.")
        from pynext.testing.queries import getByPlaceholderText
        return getByPlaceholderText(_current_container, text, exact=exact)
    
    def queryByPlaceholderText(self, text: Union[str, Any], exact: bool = True) -> Optional[HTMLNode]:
        """Find element by placeholder text (returns None if not found)."""
        if _current_container is None:
            return None
        from pynext.testing.queries import queryByPlaceholderText
        return queryByPlaceholderText(_current_container, text, exact=exact)
    
    async def findByPlaceholderText(self, text: Union[str, Any], exact: bool = True, timeout: float = 5.0) -> HTMLNode:
        """Find element by placeholder text (async, waits for element)."""
        if _current_container is None:
            raise ValueError("No component rendered. Call render() first.")
        from pynext.testing.queries import findByPlaceholderText
        return await findByPlaceholderText(_current_container, text, exact=exact, timeout=timeout)
    
    def getAllByText(self, text: Union[str, Any], exact: bool = True) -> List[HTMLNode]:
        """Find all elements by text content (throws if none found)."""
        if _current_container is None:
            raise ValueError("No component rendered. Call render() first.")
        from pynext.testing.queries import getAllByText
        return getAllByText(_current_container, text, exact=exact)
    
    def queryAllByText(self, text: Union[str, Any], exact: bool = True) -> List[HTMLNode]:
        """Find all elements by text content (returns empty list if none found)."""
        if _current_container is None:
            return []
        from pynext.testing.queries import queryAllByText
        return queryAllByText(_current_container, text, exact=exact)
    
    async def findAllByText(self, text: Union[str, Any], exact: bool = True, timeout: float = 5.0) -> List[HTMLNode]:
        """Find all elements by text content (async, waits for elements)."""
        if _current_container is None:
            raise ValueError("No component rendered. Call render() first.")
        from pynext.testing.queries import findAllByText
        return await findAllByText(_current_container, text, exact=exact, timeout=timeout)


# Global screen instance
screen = Screen()


# =============================================================================
# cleanup() - Cleanup Rendered Components
# =============================================================================

def cleanup() -> None:
    """
    Cleanup all rendered components.
    
    This should be called after each test to ensure
    no state leaks between tests.
    
    Example:
        def test_something():
            render(Button, label="Click")
            # ... test code ...
            cleanup()  # Clean up
    """
    global _rendered_components, _current_container
    _rendered_components.clear()
    _current_container = None


# =============================================================================
# within() - Scoped Queries
# =============================================================================

class ScopedScreen:
    """
    Scoped screen object for querying within an element.
    """
    
    def __init__(self, container: HTMLNode):
        self._container = container
    
    def getByText(self, text: Union[str, Any], exact: bool = True) -> HTMLNode:
        from pynext.testing.queries import getByText
        return getByText(self._container, text, exact=exact)
    
    def queryByText(self, text: Union[str, Any], exact: bool = True) -> Optional[HTMLNode]:
        from pynext.testing.queries import queryByText
        return queryByText(self._container, text, exact=exact)
    
    async def findByText(self, text: Union[str, Any], exact: bool = True, timeout: float = 5.0) -> HTMLNode:
        from pynext.testing.queries import findByText
        return await findByText(self._container, text, exact=exact, timeout=timeout)
    
    def getByRole(self, role: str, name: Optional[str] = None) -> HTMLNode:
        from pynext.testing.queries import getByRole
        return getByRole(self._container, role, name=name)
    
    def queryByRole(self, role: str, name: Optional[str] = None) -> Optional[HTMLNode]:
        from pynext.testing.queries import queryByRole
        return queryByRole(self._container, role, name=name)
    
    async def findByRole(self, role: str, name: Optional[str] = None, timeout: float = 5.0) -> HTMLNode:
        from pynext.testing.queries import findByRole
        return await findByRole(self._container, role, name=name, timeout=timeout)
    
    def getByTestId(self, test_id: str) -> HTMLNode:
        from pynext.testing.queries import getByTestId
        return getByTestId(self._container, test_id)
    
    def queryByTestId(self, test_id: str) -> Optional[HTMLNode]:
        from pynext.testing.queries import queryByTestId
        return queryByTestId(self._container, test_id)
    
    async def findByTestId(self, test_id: str, timeout: float = 5.0) -> HTMLNode:
        from pynext.testing.queries import findByTestId
        return await findByTestId(self._container, test_id, timeout=timeout)
    
    def getByLabelText(self, text: Union[str, Any], exact: bool = True) -> HTMLNode:
        from pynext.testing.queries import getByLabelText
        return getByLabelText(self._container, text, exact=exact)
    
    def queryByLabelText(self, text: Union[str, Any], exact: bool = True) -> Optional[HTMLNode]:
        from pynext.testing.queries import queryByLabelText
        return queryByLabelText(self._container, text, exact=exact)
    
    async def findByLabelText(self, text: Union[str, Any], exact: bool = True, timeout: float = 5.0) -> HTMLNode:
        from pynext.testing.queries import findByLabelText
        return await findByLabelText(self._container, text, exact=exact, timeout=timeout)
    
    def getByPlaceholderText(self, text: Union[str, Any], exact: bool = True) -> HTMLNode:
        from pynext.testing.queries import getByPlaceholderText
        return getByPlaceholderText(self._container, text, exact=exact)
    
    def queryByPlaceholderText(self, text: Union[str, Any], exact: bool = True) -> Optional[HTMLNode]:
        from pynext.testing.queries import queryByPlaceholderText
        return queryByPlaceholderText(self._container, text, exact=exact)
    
    async def findByPlaceholderText(self, text: Union[str, Any], exact: bool = True, timeout: float = 5.0) -> HTMLNode:
        from pynext.testing.queries import findByPlaceholderText
        return await findByPlaceholderText(self._container, text, exact=exact, timeout=timeout)
    
    def getAllByText(self, text: Union[str, Any], exact: bool = True) -> List[HTMLNode]:
        from pynext.testing.queries import getAllByText
        return getAllByText(self._container, text, exact=exact)
    
    def queryAllByText(self, text: Union[str, Any], exact: bool = True) -> List[HTMLNode]:
        from pynext.testing.queries import queryAllByText
        return queryAllByText(self._container, text, exact=exact)
    
    async def findAllByText(self, text: Union[str, Any], exact: bool = True, timeout: float = 5.0) -> List[HTMLNode]:
        from pynext.testing.queries import findAllByText
        return await findAllByText(self._container, text, exact=exact, timeout=timeout)


def within(element: HTMLNode) -> ScopedScreen:
    """
    Create a scoped screen object for querying within an element.
    
    This is useful when you want to scope queries to a specific
    part of the DOM tree.
    
    Args:
        element: HTMLNode to scope queries to
        
    Returns:
        ScopedScreen object scoped to the element
        
    Example:
        render(Card, content="Hello")
        card = screen.getByRole("article")
        within(card).getByText("Hello")
    """
    return ScopedScreen(element)


# =============================================================================
# act() - Batch Updates
# =============================================================================

def act(callback: Callable[[], Any]) -> Any:
    """
    Batch multiple updates together.
    
    This ensures that all updates within the callback
    are processed together, preventing unnecessary
    intermediate renders.
    
    Args:
        callback: Function to execute
        
    Returns:
        Result of callback
        
    Example:
        act(lambda: [
            count.set(1),
            name.set("John"),
        ])
    """
    return callback()


# =============================================================================
# waitFor() - Async Waiting
# =============================================================================

async def waitFor(
    condition: Callable[[], bool],
    timeout: float = 5.0,
    interval: float = 0.05,
) -> None:
    """
    Wait for a condition to become true.
    
    This is useful for testing async updates that happen
    after some time or after async operations.
    
    Args:
        condition: Function that returns True when condition is met
        timeout: Maximum time to wait in seconds
        interval: Time between checks in seconds
        
    Raises:
        TimeoutError: If condition is not met within timeout
        
    Example:
        async def test_async_update():
            render(UserProfile, user_id=123)
            await waitFor(lambda: screen.getByText("John Doe") is not None)
    """
    start = time.time()
    while time.time() - start < timeout:
        try:
            if condition():
                return
        except Exception:
            pass  # Condition may throw before element exists
        await asyncio.sleep(interval)
    
    raise TimeoutError(f"Condition not met within {timeout} seconds")


# =============================================================================
# renderHook() - Test Hooks/Effects
# =============================================================================

@dataclass
class HookResult:
    """
    Result of rendering a hook.
    
    Contains the current value and methods to
    update and re-render the hook.
    """
    current: Any
    rerender: Callable[[Optional[Dict[str, Any]]], "HookResult"]
    
    def __init__(self, hook_fn: Callable, initial_props: Optional[Dict[str, Any]] = None):
        self._hook_fn = hook_fn
        self._props = initial_props or {}
        self.current = self._call_hook()
    
    def _call_hook(self) -> Any:
        """Call the hook function with current props."""
        return self._hook_fn(**self._props)
    
    def rerender(self, props: Optional[Dict[str, Any]] = None) -> "HookResult":
        """Re-render the hook with new props."""
        if props:
            self._props.update(props)
        self.current = self._call_hook()
        return self


def renderHook(
    hook_fn: Callable,
    initial_props: Optional[Dict[str, Any]] = None,
) -> HookResult:
    """
    Render a hook for testing.
    
    This is useful for testing custom hooks, effects,
    or any function that manages state.
    
    Args:
        hook_fn: Hook function to test
        initial_props: Initial props to pass to hook
        
    Returns:
        HookResult with current value and rerender method
        
    Example:
        def use_counter(initial=0):
            count = signal(initial)
            increment = lambda: count.set(count() + 1)
            return count, increment
        
        result = renderHook(use_counter, initial_props={"initial": 10})
        assert result.current[0]() == 10
        result.current[1]()  # increment
        result = result.rerender()
        assert result.current[0]() == 11
    """
    return HookResult(hook_fn, initial_props)

