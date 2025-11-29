"""
PyNext Testing - Assertions

AI-friendly assertion functions with descriptive names.
Each assertion clearly describes what it checks.

Example:
    from pynext.testing import render, assert_text, assert_has_class
    
    result = render(Button, label="Click")
    assert_text(result, "Click")
    assert_has_class(result, "btn-primary")

Why AI-Friendly Names:
    - assert_text() is clearer than expect(result).toHaveText()
    - assert_has_class() is clearer than expect(result.className).toContain()
    - No chained API to learn, just simple function calls
    - LLMs can understand and generate these easily
"""

from __future__ import annotations

import re
from typing import Any, List, Optional, Union

from pynext.testing.render import RenderResult, HTMLNode


# =============================================================================
# Core Assertion Helpers
# =============================================================================

class AssertionError(Exception):
    """
    Custom assertion error with helpful messages.
    
    Shows what was expected vs what was found,
    making debugging much easier.
    """
    
    def __init__(
        self,
        message: str,
        expected: Any = None,
        actual: Any = None,
        html_context: str = None,
    ):
        self.expected = expected
        self.actual = actual
        self.html_context = html_context
        
        # Build detailed message
        full_message = message
        if expected is not None and actual is not None:
            full_message += f"\n  Expected: {expected!r}\n  Actual:   {actual!r}"
        if html_context:
            # Show truncated HTML for context
            truncated = html_context[:200] + "..." if len(html_context) > 200 else html_context
            full_message += f"\n  HTML: {truncated}"
        
        super().__init__(full_message)


def _get_target(
    result: Union[RenderResult, HTMLNode],
    selector: Optional[str] = None,
) -> HTMLNode:
    """
    Get the target element for assertions.
    
    If selector is provided, finds that element.
    Otherwise returns the root element.
    """
    if isinstance(result, HTMLNode):
        return result
    
    if selector:
        element = result.query_selector(selector)
        if element is None:
            raise AssertionError(
                f"Element not found: '{selector}'",
                expected=f"Element matching '{selector}'",
                actual="No element found",
                html_context=result.html,
            )
        return element
    
    return result.root


# =============================================================================
# Text Assertions
# =============================================================================

def assert_text(
    result: Union[RenderResult, HTMLNode],
    expected: str,
    selector: Optional[str] = None,
    exact: bool = False,
) -> None:
    """
    Assert that element contains expected text.
    
    Args:
        result: RenderResult or HTMLNode to check
        expected: Text that should be present
        selector: Optional CSS selector to find element
        exact: If True, text must match exactly (not just contain)
        
    Example:
        result = render(Button, label="Click me")
        assert_text(result, "Click me")
        assert_text(result, "Click me", selector="button", exact=True)
    """
    target = _get_target(result, selector)
    actual = target.text.strip()
    
    if exact:
        if actual != expected:
            raise AssertionError(
                f"Text does not match exactly",
                expected=expected,
                actual=actual,
                html_context=result.html if isinstance(result, RenderResult) else None,
            )
    else:
        if expected not in actual:
            raise AssertionError(
                f"Text '{expected}' not found in element",
                expected=expected,
                actual=actual,
                html_context=result.html if isinstance(result, RenderResult) else None,
            )


def assert_no_text(
    result: Union[RenderResult, HTMLNode],
    unexpected: str,
    selector: Optional[str] = None,
) -> None:
    """
    Assert that element does NOT contain text.
    
    Args:
        result: RenderResult or HTMLNode to check
        unexpected: Text that should NOT be present
        selector: Optional CSS selector to find element
        
    Example:
        result = render(EmptyState)
        assert_no_text(result, "Loading...")
    """
    target = _get_target(result, selector)
    actual = target.text.strip()
    
    if unexpected in actual:
        raise AssertionError(
            f"Unexpected text '{unexpected}' found in element",
            expected=f"Text NOT containing '{unexpected}'",
            actual=actual,
            html_context=result.html if isinstance(result, RenderResult) else None,
        )


def assert_text_matches(
    result: Union[RenderResult, HTMLNode],
    pattern: str,
    selector: Optional[str] = None,
) -> None:
    """
    Assert that element text matches regex pattern.
    
    Args:
        result: RenderResult or HTMLNode to check
        pattern: Regular expression pattern
        selector: Optional CSS selector to find element
        
    Example:
        result = render(Timestamp, date=now)
        assert_text_matches(result, r"\\d{4}-\\d{2}-\\d{2}")
    """
    target = _get_target(result, selector)
    actual = target.text.strip()
    
    if not re.search(pattern, actual):
        raise AssertionError(
            f"Text does not match pattern '{pattern}'",
            expected=f"Text matching /{pattern}/",
            actual=actual,
            html_context=result.html if isinstance(result, RenderResult) else None,
        )


# =============================================================================
# Class Assertions
# =============================================================================

def assert_has_class(
    result: Union[RenderResult, HTMLNode],
    class_name: str,
    selector: Optional[str] = None,
) -> None:
    """
    Assert that element has a CSS class.
    
    Args:
        result: RenderResult or HTMLNode to check
        class_name: CSS class that should be present
        selector: Optional CSS selector to find element
        
    Example:
        result = render(Button, variant="primary")
        assert_has_class(result, "btn-primary")
    """
    target = _get_target(result, selector)
    
    if not target.has_class(class_name):
        raise AssertionError(
            f"Element does not have class '{class_name}'",
            expected=f"Class '{class_name}'",
            actual=f"Classes: {target.classes}",
            html_context=result.html if isinstance(result, RenderResult) else None,
        )


def assert_no_class(
    result: Union[RenderResult, HTMLNode],
    class_name: str,
    selector: Optional[str] = None,
) -> None:
    """
    Assert that element does NOT have a CSS class.
    
    Args:
        result: RenderResult or HTMLNode to check
        class_name: CSS class that should NOT be present
        selector: Optional CSS selector to find element
        
    Example:
        result = render(Button, disabled=False)
        assert_no_class(result, "disabled")
    """
    target = _get_target(result, selector)
    
    if target.has_class(class_name):
        raise AssertionError(
            f"Element unexpectedly has class '{class_name}'",
            expected=f"No class '{class_name}'",
            actual=f"Classes: {target.classes}",
            html_context=result.html if isinstance(result, RenderResult) else None,
        )


def assert_classes(
    result: Union[RenderResult, HTMLNode],
    classes: List[str],
    selector: Optional[str] = None,
) -> None:
    """
    Assert that element has ALL of the specified classes.
    
    Args:
        result: RenderResult or HTMLNode to check
        classes: List of CSS classes that should all be present
        selector: Optional CSS selector to find element
        
    Example:
        result = render(Card, size="lg", variant="outlined")
        assert_classes(result, ["card", "card-lg", "card-outlined"])
    """
    target = _get_target(result, selector)
    
    missing = [c for c in classes if not target.has_class(c)]
    if missing:
        raise AssertionError(
            f"Element missing classes: {missing}",
            expected=f"All classes: {classes}",
            actual=f"Classes: {target.classes}",
            html_context=result.html if isinstance(result, RenderResult) else None,
        )


# =============================================================================
# Attribute Assertions
# =============================================================================

def assert_has_attribute(
    result: Union[RenderResult, HTMLNode],
    name: str,
    value: Optional[str] = None,
    selector: Optional[str] = None,
) -> None:
    """
    Assert that element has an HTML attribute.
    
    Args:
        result: RenderResult or HTMLNode to check
        name: Attribute name
        value: Optional expected value (if None, just checks existence)
        selector: Optional CSS selector to find element
        
    Example:
        result = render(Button, disabled=True)
        assert_has_attribute(result, "disabled")
        assert_has_attribute(result, "type", "button")
    """
    target = _get_target(result, selector)
    
    if not target.has_attribute(name, value):
        if value is None:
            raise AssertionError(
                f"Element does not have attribute '{name}'",
                expected=f"Attribute '{name}'",
                actual=f"Attributes: {list(target.attrs.keys())}",
                html_context=result.html if isinstance(result, RenderResult) else None,
            )
        else:
            actual_value = target.attrs.get(name, "<not set>")
            raise AssertionError(
                f"Attribute '{name}' has wrong value",
                expected=f"{name}=\"{value}\"",
                actual=f"{name}=\"{actual_value}\"",
                html_context=result.html if isinstance(result, RenderResult) else None,
            )


def assert_no_attribute(
    result: Union[RenderResult, HTMLNode],
    name: str,
    selector: Optional[str] = None,
) -> None:
    """
    Assert that element does NOT have an attribute.
    
    Args:
        result: RenderResult or HTMLNode to check
        name: Attribute that should NOT be present
        selector: Optional CSS selector to find element
        
    Example:
        result = render(Button, disabled=False)
        assert_no_attribute(result, "disabled")
    """
    target = _get_target(result, selector)
    
    if name in target.attrs:
        raise AssertionError(
            f"Element unexpectedly has attribute '{name}'",
            expected=f"No attribute '{name}'",
            actual=f"{name}=\"{target.attrs[name]}\"",
            html_context=result.html if isinstance(result, RenderResult) else None,
        )


# =============================================================================
# Element Assertions
# =============================================================================

def assert_exists(
    result: RenderResult,
    selector: str,
) -> None:
    """
    Assert that an element matching selector exists.
    
    Args:
        result: RenderResult to check
        selector: CSS selector for element that should exist
        
    Example:
        result = render(Dialog, open=True)
        assert_exists(result, ".dialog-overlay")
    """
    element = result.query_selector(selector)
    if element is None:
        raise AssertionError(
            f"Element '{selector}' not found",
            expected=f"Element matching '{selector}'",
            actual="No element found",
            html_context=result.html,
        )


def assert_not_exists(
    result: RenderResult,
    selector: str,
) -> None:
    """
    Assert that NO element matching selector exists.
    
    Args:
        result: RenderResult to check
        selector: CSS selector for element that should NOT exist
        
    Example:
        result = render(Dialog, open=False)
        assert_not_exists(result, ".dialog-overlay")
    """
    element = result.query_selector(selector)
    if element is not None:
        raise AssertionError(
            f"Unexpected element '{selector}' found",
            expected=f"No element matching '{selector}'",
            actual=f"Found element <{element.tag}>",
            html_context=result.html,
        )


def assert_count(
    result: RenderResult,
    selector: str,
    expected_count: int,
) -> None:
    """
    Assert exact number of elements matching selector.
    
    Args:
        result: RenderResult to check
        selector: CSS selector to count
        expected_count: Expected number of matches
        
    Example:
        result = render(List, items=["a", "b", "c"])
        assert_count(result, "li", 3)
    """
    elements = result.query_selector_all(selector)
    actual_count = len(elements)
    
    if actual_count != expected_count:
        raise AssertionError(
            f"Wrong number of '{selector}' elements",
            expected=expected_count,
            actual=actual_count,
            html_context=result.html,
        )


def assert_count_at_least(
    result: RenderResult,
    selector: str,
    min_count: int,
) -> None:
    """
    Assert at least N elements matching selector.
    
    Args:
        result: RenderResult to check
        selector: CSS selector to count
        min_count: Minimum number of matches
        
    Example:
        result = render(Gallery, images=images)
        assert_count_at_least(result, "img", 1)
    """
    elements = result.query_selector_all(selector)
    actual_count = len(elements)
    
    if actual_count < min_count:
        raise AssertionError(
            f"Not enough '{selector}' elements",
            expected=f"At least {min_count}",
            actual=actual_count,
            html_context=result.html,
        )


def assert_tag(
    result: Union[RenderResult, HTMLNode],
    expected_tag: str,
    selector: Optional[str] = None,
) -> None:
    """
    Assert element has expected tag name.
    
    Args:
        result: RenderResult or HTMLNode to check
        expected_tag: Expected HTML tag (e.g., "button", "div")
        selector: Optional CSS selector to find element
        
    Example:
        result = render(Button)
        assert_tag(result, "button")
    """
    target = _get_target(result, selector)
    
    if target.tag != expected_tag:
        raise AssertionError(
            f"Element has wrong tag",
            expected=f"<{expected_tag}>",
            actual=f"<{target.tag}>",
            html_context=result.html if isinstance(result, RenderResult) else None,
        )


# =============================================================================
# Visibility Assertions
# =============================================================================

def assert_visible(
    result: Union[RenderResult, HTMLNode],
    selector: Optional[str] = None,
) -> None:
    """
    Assert that element is visible (not hidden).
    
    Checks for:
    - hidden attribute
    - style="display: none"
    - aria-hidden="true"
    
    Args:
        result: RenderResult or HTMLNode to check
        selector: Optional CSS selector to find element
        
    Example:
        result = render(Tooltip, visible=True)
        assert_visible(result, ".tooltip-content")
    """
    target = _get_target(result, selector)
    
    # Check hidden attribute
    if "hidden" in target.attrs:
        raise AssertionError(
            f"Element has 'hidden' attribute",
            expected="Visible element",
            actual="hidden attribute present",
            html_context=result.html if isinstance(result, RenderResult) else None,
        )
    
    # Check display: none in style
    style = target.attrs.get("style", "")
    if "display: none" in style or "display:none" in style:
        raise AssertionError(
            f"Element has display: none",
            expected="Visible element",
            actual=f"style=\"{style}\"",
            html_context=result.html if isinstance(result, RenderResult) else None,
        )
    
    # Check aria-hidden
    if target.attrs.get("aria-hidden") == "true":
        raise AssertionError(
            f"Element has aria-hidden=\"true\"",
            expected="Visible element",
            actual="aria-hidden=\"true\"",
            html_context=result.html if isinstance(result, RenderResult) else None,
        )


def assert_hidden(
    result: Union[RenderResult, HTMLNode],
    selector: Optional[str] = None,
) -> None:
    """
    Assert that element is hidden.
    
    Args:
        result: RenderResult or HTMLNode to check
        selector: Optional CSS selector to find element
        
    Example:
        result = render(Dropdown, open=False)
        assert_hidden(result, ".dropdown-menu")
    """
    target = _get_target(result, selector)
    
    is_hidden = (
        "hidden" in target.attrs
        or "display: none" in target.attrs.get("style", "")
        or "display:none" in target.attrs.get("style", "")
        or target.attrs.get("aria-hidden") == "true"
    )
    
    if not is_hidden:
        raise AssertionError(
            f"Element is not hidden",
            expected="Hidden element",
            actual="Element is visible",
            html_context=result.html if isinstance(result, RenderResult) else None,
        )


# =============================================================================
# HTML Content Assertions
# =============================================================================

def assert_html_contains(
    result: RenderResult,
    substring: str,
) -> None:
    """
    Assert that raw HTML contains substring.
    
    Use this when you need to check the actual HTML output,
    not the parsed DOM structure.
    
    Args:
        result: RenderResult to check
        substring: String that should be in the HTML
        
    Example:
        result = render(Script, src="/app.js")
        assert_html_contains(result, 'src="/app.js"')
    """
    if substring not in result.html:
        raise AssertionError(
            f"HTML does not contain '{substring}'",
            expected=f"HTML containing '{substring}'",
            actual=f"HTML: {result.html[:200]}...",
        )


def assert_html_not_contains(
    result: RenderResult,
    substring: str,
) -> None:
    """
    Assert that raw HTML does NOT contain substring.
    
    Args:
        result: RenderResult to check
        substring: String that should NOT be in the HTML
        
    Example:
        result = render(SafeContent, user_input=malicious)
        assert_html_not_contains(result, "<script>")
    """
    if substring in result.html:
        raise AssertionError(
            f"HTML unexpectedly contains '{substring}'",
            expected=f"HTML NOT containing '{substring}'",
            actual=f"Found at position {result.html.find(substring)}",
        )


# =============================================================================
# Console Assertions
# =============================================================================

def assert_no_console_errors(result: RenderResult) -> None:
    """
    Assert that no console errors occurred during render.
    
    Args:
        result: RenderResult to check
        
    Example:
        result = render(DataTable, data=valid_data)
        assert_no_console_errors(result)
    """
    if result.console_errors:
        raise AssertionError(
            f"Console errors occurred during render",
            expected="No console errors",
            actual=f"Errors: {result.console_errors}",
        )


def assert_console_log(
    result: RenderResult,
    expected_message: str,
) -> None:
    """
    Assert that a specific console.log message was output.
    
    Args:
        result: RenderResult to check
        expected_message: Message that should have been logged
        
    Example:
        result = render(DebugComponent)
        assert_console_log(result, "Component mounted")
    """
    if expected_message not in result.console_logs:
        raise AssertionError(
            f"Console log '{expected_message}' not found",
            expected=expected_message,
            actual=f"Logs: {result.console_logs}",
        )


# =============================================================================
# Performance Assertions
# =============================================================================

def assert_render_time(
    result: RenderResult,
    max_ms: float,
) -> None:
    """
    Assert that component rendered within time limit.
    
    Args:
        result: RenderResult to check
        max_ms: Maximum allowed render time in milliseconds
        
    Example:
        result = render(HeavyComponent)
        assert_render_time(result, max_ms=50)
    """
    if result.render_time_ms > max_ms:
        raise AssertionError(
            f"Render took too long",
            expected=f"<= {max_ms}ms",
            actual=f"{result.render_time_ms:.2f}ms",
        )


# =============================================================================
# Signal Assertions
# =============================================================================

def assert_signal_value(
    result: RenderResult,
    signal_name: str,
    expected_value: Any,
) -> None:
    """
    Assert that a signal has expected value.
    
    Args:
        result: RenderResult to check
        signal_name: Name of the signal to check
        expected_value: Expected value of the signal
        
    Example:
        result = render(Counter, initial=5)
        assert_signal_value(result, "count", 5)
    """
    if signal_name not in result.signals:
        raise AssertionError(
            f"Signal '{signal_name}' not found",
            expected=f"Signal named '{signal_name}'",
            actual=f"Available signals: {list(result.signals.keys())}",
        )
    
    actual = result.signals[signal_name]()
    if actual != expected_value:
        raise AssertionError(
            f"Signal '{signal_name}' has wrong value",
            expected=expected_value,
            actual=actual,
        )


def assert_has_signal(
    result: RenderResult,
    signal_name: str,
) -> None:
    """
    Assert that component has a signal with given name.
    
    Args:
        result: RenderResult to check
        signal_name: Name of the signal that should exist
        
    Example:
        result = render(Counter)
        assert_has_signal(result, "count")
    """
    if signal_name not in result.signals:
        raise AssertionError(
            f"Signal '{signal_name}' not found",
            expected=f"Signal named '{signal_name}'",
            actual=f"Available signals: {list(result.signals.keys())}",
        )

