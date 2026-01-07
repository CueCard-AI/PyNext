"""
PyNext Testing - Query Methods

WHAT THIS FILE DOES:
Provides query methods for finding elements in rendered HTML.
Supports getBy* (throws if not found), queryBy* (returns None), and findBy* (async).

WHY THIS EXISTS:
Testing Library pattern requires three variants of each query:
1. getBy* - Throws if element not found (assertive)
2. queryBy* - Returns None if not found (non-assertive)
3. findBy* - Async, waits for element to appear

HOW IT WORKS:
- Searches HTMLNode tree recursively
- Supports text matching (exact and regex)
- Supports ARIA roles and attributes
- Supports data-testid attributes
- Supports label associations

WHO USES THIS:
- RTL-style testing API (client.py)
- Direct query usage in tests

WHEN TO USE:
- Finding elements by text: getByText
- Finding elements by role: getByRole
- Finding elements by test ID: getByTestId
- Finding elements by label: getByLabelText
- Finding elements by placeholder: getByPlaceholderText

EXAMPLES:
    from pynext.testing.queries import getByText, queryByText, findByText
    
    element = getByText(container, "Submit")  # Throws if not found
    element = queryByText(container, "Submit")  # Returns None if not found
    element = await findByText(container, "Submit")  # Waits for element
"""

from __future__ import annotations

import asyncio
import re
import time
from typing import Any, Callable, List, Optional, Pattern, Union

from pynext.testing.render import HTMLNode


# =============================================================================
# Utility Functions
# =============================================================================

def _match_text(text: str, pattern: Union[str, Pattern], exact: bool = True) -> bool:
    """
    Check if text matches pattern.
    
    Args:
        text: Text to match
        pattern: String or regex pattern
        exact: If True, exact match; if False, substring match
        
    Returns:
        True if text matches pattern
    """
    if isinstance(pattern, Pattern):
        return bool(pattern.search(text))
    elif exact:
        return text == pattern
    else:
        return pattern in text


def _get_element_text(node: HTMLNode) -> str:
    """
    Get all text content from an element.
    
    Args:
        node: HTMLNode to get text from
        
    Returns:
        Text content
    """
    return node.text


def _get_accessible_name(node: HTMLNode) -> Optional[str]:
    """
    Get accessible name of an element (for role matching).
    
    Priority:
    1. aria-label
    2. aria-labelledby
    3. Label association (for/id)
    4. Text content
    5. Title attribute
    6. Alt text (for images)
    
    Args:
        node: HTMLNode to get accessible name from
        
    Returns:
        Accessible name or None
    """
    # aria-label
    if "aria-label" in node.attrs:
        return node.attrs["aria-label"]
    
    # aria-labelledby (would need to resolve ID, simplified here)
    if "aria-labelledby" in node.attrs:
        # In real implementation, would find element by ID
        pass
    
    # Label association
    if "id" in node.attrs:
        # Would find associated label by for attribute
        pass
    
    # Text content
    text = _get_element_text(node).strip()
    if text:
        return text
    
    # Title attribute
    if "title" in node.attrs:
        return node.attrs["title"]
    
    # Alt text
    if node.tag == "img" and "alt" in node.attrs:
        return node.attrs["alt"]
    
    return None


def _get_role(node: HTMLNode) -> Optional[str]:
    """
    Get ARIA role of an element.
    
    Args:
        node: HTMLNode to get role from
        
    Returns:
        Role string or None
    """
    # Explicit role
    if "role" in node.attrs:
        return node.attrs["role"]
    
    # Implicit roles
    implicit_roles = {
        "button": "button",
        "a": "link",
        "input": _get_input_role(node),
        "img": "img",
        "nav": "navigation",
        "main": "main",
        "header": "banner",
        "footer": "contentinfo",
        "aside": "complementary",
        "form": "form",
        "article": "article",
        "section": "region",
        "ul": "list",
        "ol": "list",
        "li": "listitem",
        "h1": "heading",
        "h2": "heading",
        "h3": "heading",
        "h4": "heading",
        "h5": "heading",
        "h6": "heading",
    }
    
    return implicit_roles.get(node.tag)


def _get_input_role(node: HTMLNode) -> str:
    """Get role for input elements based on type."""
    input_type = node.attrs.get("type", "text")
    
    role_map = {
        "button": "button",
        "checkbox": "checkbox",
        "radio": "radio",
        "range": "slider",
        "search": "searchbox",
        "submit": "button",
        "reset": "button",
    }
    
    return role_map.get(input_type, "textbox")


def _find_all_descendants(node: HTMLNode) -> List[HTMLNode]:
    """
    Get all descendant nodes (including self).
    
    Args:
        node: Root node
        
    Returns:
        List of all descendant nodes
    """
    result = [node]
    for child in node.children:
        if isinstance(child, HTMLNode):
            result.extend(_find_all_descendants(child))
    return result


# =============================================================================
# Query by Text
# =============================================================================

def _find_by_text(
    container: HTMLNode,
    text: Union[str, Pattern],
    exact: bool = True,
) -> List[HTMLNode]:
    """
    Find all elements matching text pattern.
    
    Args:
        container: Container node to search in
        text: Text pattern (string or regex)
        exact: If True, exact match; if False, substring match
        
    Returns:
        List of matching nodes
    """
    results = []
    for node in _find_all_descendants(container):
        node_text = _get_element_text(node)
        if _match_text(node_text, text, exact=exact):
            results.append(node)
    return results


def getByText(
    container: HTMLNode,
    text: Union[str, Pattern],
    exact: bool = True,
) -> HTMLNode:
    """
    Find element by text content (throws if not found).
    
    Args:
        container: Container node to search in
        text: Text pattern (string or regex)
        exact: If True, exact match; if False, substring match
        
    Returns:
        First matching HTMLNode
        
    Raises:
        ValueError: If no element found
    """
    results = _find_by_text(container, text, exact=exact)
    if not results:
        pattern_str = text.pattern if isinstance(text, Pattern) else text
        raise ValueError(f"Unable to find element with text: {pattern_str}")
    return results[0]


def queryByText(
    container: HTMLNode,
    text: Union[str, Pattern],
    exact: bool = True,
) -> Optional[HTMLNode]:
    """
    Find element by text content (returns None if not found).
    
    Args:
        container: Container node to search in
        text: Text pattern (string or regex)
        exact: If True, exact match; if False, substring match
        
    Returns:
        First matching HTMLNode or None
    """
    results = _find_by_text(container, text, exact=exact)
    return results[0] if results else None


async def findByText(
    container: HTMLNode,
    text: Union[str, Pattern],
    exact: bool = True,
    timeout: float = 5.0,
    interval: float = 0.05,
) -> HTMLNode:
    """
    Find element by text content (async, waits for element).
    
    Args:
        container: Container node to search in
        text: Text pattern (string or regex)
        exact: If True, exact match; if False, substring match
        timeout: Maximum time to wait in seconds
        interval: Time between checks in seconds
        
    Returns:
        First matching HTMLNode
        
    Raises:
        TimeoutError: If element not found within timeout
    """
    start = time.time()
    while time.time() - start < timeout:
        result = queryByText(container, text, exact=exact)
        if result is not None:
            return result
        await asyncio.sleep(interval)
    
    pattern_str = text.pattern if isinstance(text, Pattern) else text
    raise TimeoutError(f"Element with text '{pattern_str}' not found within {timeout} seconds")


def getAllByText(
    container: HTMLNode,
    text: Union[str, Pattern],
    exact: bool = True,
) -> List[HTMLNode]:
    """
    Find all elements by text content (throws if none found).
    
    Args:
        container: Container node to search in
        text: Text pattern (string or regex)
        exact: If True, exact match; if False, substring match
        
    Returns:
        List of matching HTMLNodes
        
    Raises:
        ValueError: If no elements found
    """
    results = _find_by_text(container, text, exact=exact)
    if not results:
        pattern_str = text.pattern if isinstance(text, Pattern) else text
        raise ValueError(f"Unable to find elements with text: {pattern_str}")
    return results


def queryAllByText(
    container: HTMLNode,
    text: Union[str, Pattern],
    exact: bool = True,
) -> List[HTMLNode]:
    """
    Find all elements by text content (returns empty list if none found).
    
    Args:
        container: Container node to search in
        text: Text pattern (string or regex)
        exact: If True, exact match; if False, substring match
        
    Returns:
        List of matching HTMLNodes (may be empty)
    """
    return _find_by_text(container, text, exact=exact)


async def findAllByText(
    container: HTMLNode,
    text: Union[str, Pattern],
    exact: bool = True,
    timeout: float = 5.0,
    interval: float = 0.05,
) -> List[HTMLNode]:
    """
    Find all elements by text content (async, waits for elements).
    
    Args:
        container: Container node to search in
        text: Text pattern (string or regex)
        exact: If True, exact match; if False, substring match
        timeout: Maximum time to wait in seconds
        interval: Time between checks in seconds
        
    Returns:
        List of matching HTMLNodes
        
    Raises:
        TimeoutError: If no elements found within timeout
    """
    start = time.time()
    while time.time() - start < timeout:
        results = queryAllByText(container, text, exact=exact)
        if results:
            return results
        await asyncio.sleep(interval)
    
    pattern_str = text.pattern if isinstance(text, Pattern) else text
    raise TimeoutError(f"Elements with text '{pattern_str}' not found within {timeout} seconds")


# =============================================================================
# Query by Role
# =============================================================================

def _find_by_role(
    container: HTMLNode,
    role: str,
    name: Optional[str] = None,
) -> List[HTMLNode]:
    """
    Find all elements matching role (and optionally name).
    
    Args:
        container: Container node to search in
        role: ARIA role
        name: Optional accessible name
        
    Returns:
        List of matching nodes
    """
    results = []
    for node in _find_all_descendants(container):
        node_role = _get_role(node)
        if node_role == role:
            if name is None:
                results.append(node)
            else:
                accessible_name = _get_accessible_name(node)
                if accessible_name and _match_text(accessible_name, name, exact=False):
                    results.append(node)
    return results


def getByRole(
    container: HTMLNode,
    role: str,
    name: Optional[str] = None,
) -> HTMLNode:
    """
    Find element by ARIA role (throws if not found).
    
    Args:
        container: Container node to search in
        role: ARIA role
        name: Optional accessible name
        
    Returns:
        First matching HTMLNode
        
    Raises:
        ValueError: If no element found
    """
    results = _find_by_role(container, role, name=name)
    if not results:
        msg = f"Unable to find element with role: {role}"
        if name:
            msg += f" and name: {name}"
        raise ValueError(msg)
    return results[0]


def queryByRole(
    container: HTMLNode,
    role: str,
    name: Optional[str] = None,
) -> Optional[HTMLNode]:
    """
    Find element by ARIA role (returns None if not found).
    
    Args:
        container: Container node to search in
        role: ARIA role
        name: Optional accessible name
        
    Returns:
        First matching HTMLNode or None
    """
    results = _find_by_role(container, role, name=name)
    return results[0] if results else None


async def findByRole(
    container: HTMLNode,
    role: str,
    name: Optional[str] = None,
    timeout: float = 5.0,
    interval: float = 0.05,
) -> HTMLNode:
    """
    Find element by ARIA role (async, waits for element).
    
    Args:
        container: Container node to search in
        role: ARIA role
        name: Optional accessible name
        timeout: Maximum time to wait in seconds
        interval: Time between checks in seconds
        
    Returns:
        First matching HTMLNode
        
    Raises:
        TimeoutError: If element not found within timeout
    """
    start = time.time()
    while time.time() - start < timeout:
        result = queryByRole(container, role, name=name)
        if result is not None:
            return result
        await asyncio.sleep(interval)
    
    msg = f"Element with role '{role}'"
    if name:
        msg += f" and name '{name}'"
    msg += f" not found within {timeout} seconds"
    raise TimeoutError(msg)


def getAllByRole(
    container: HTMLNode,
    role: str,
    name: Optional[str] = None,
) -> List[HTMLNode]:
    """
    Find all elements by ARIA role (throws if none found).
    
    Args:
        container: Container node to search in
        role: ARIA role
        name: Optional accessible name
        
    Returns:
        List of matching HTMLNodes
        
    Raises:
        ValueError: If no elements found
    """
    results = _find_by_role(container, role, name=name)
    if not results:
        msg = f"Unable to find elements with role: {role}"
        if name:
            msg += f" and name: {name}"
        raise ValueError(msg)
    return results


def queryAllByRole(
    container: HTMLNode,
    role: str,
    name: Optional[str] = None,
) -> List[HTMLNode]:
    """
    Find all elements by ARIA role (returns empty list if none found).
    
    Args:
        container: Container node to search in
        role: ARIA role
        name: Optional accessible name
        
    Returns:
        List of matching HTMLNodes (may be empty)
    """
    return _find_by_role(container, role, name=name)


async def findAllByRole(
    container: HTMLNode,
    role: str,
    name: Optional[str] = None,
    timeout: float = 5.0,
    interval: float = 0.05,
) -> List[HTMLNode]:
    """
    Find all elements by ARIA role (async, waits for elements).
    
    Args:
        container: Container node to search in
        role: ARIA role
        name: Optional accessible name
        timeout: Maximum time to wait in seconds
        interval: Time between checks in seconds
        
    Returns:
        List of matching HTMLNodes
        
    Raises:
        TimeoutError: If no elements found within timeout
    """
    start = time.time()
    while time.time() - start < timeout:
        results = queryAllByRole(container, role, name=name)
        if results:
            return results
        await asyncio.sleep(interval)
    
    msg = f"Elements with role '{role}'"
    if name:
        msg += f" and name '{name}'"
    msg += f" not found within {timeout} seconds"
    raise TimeoutError(msg)


# =============================================================================
# Query by Test ID
# =============================================================================

def _find_by_test_id(
    container: HTMLNode,
    test_id: str,
) -> List[HTMLNode]:
    """
    Find all elements with matching data-testid.
    
    Args:
        container: Container node to search in
        test_id: Test ID value
        
    Returns:
        List of matching nodes
    """
    results = []
    for node in _find_all_descendants(container):
        if node.attrs.get("data-testid") == test_id:
            results.append(node)
    return results


def getByTestId(
    container: HTMLNode,
    test_id: str,
) -> HTMLNode:
    """
    Find element by data-testid attribute (throws if not found).
    
    Args:
        container: Container node to search in
        test_id: Test ID value
        
    Returns:
        First matching HTMLNode
        
    Raises:
        ValueError: If no element found
    """
    results = _find_by_test_id(container, test_id)
    if not results:
        raise ValueError(f"Unable to find element with test ID: {test_id}")
    return results[0]


def queryByTestId(
    container: HTMLNode,
    test_id: str,
) -> Optional[HTMLNode]:
    """
    Find element by data-testid attribute (returns None if not found).
    
    Args:
        container: Container node to search in
        test_id: Test ID value
        
    Returns:
        First matching HTMLNode or None
    """
    results = _find_by_test_id(container, test_id)
    return results[0] if results else None


async def findByTestId(
    container: HTMLNode,
    test_id: str,
    timeout: float = 5.0,
    interval: float = 0.05,
) -> HTMLNode:
    """
    Find element by data-testid attribute (async, waits for element).
    
    Args:
        container: Container node to search in
        test_id: Test ID value
        timeout: Maximum time to wait in seconds
        interval: Time between checks in seconds
        
    Returns:
        First matching HTMLNode
        
    Raises:
        TimeoutError: If element not found within timeout
    """
    start = time.time()
    while time.time() - start < timeout:
        result = queryByTestId(container, test_id)
        if result is not None:
            return result
        await asyncio.sleep(interval)
    
    raise TimeoutError(f"Element with test ID '{test_id}' not found within {timeout} seconds")


def getAllByTestId(
    container: HTMLNode,
    test_id: str,
) -> List[HTMLNode]:
    """
    Find all elements by data-testid attribute (throws if none found).
    
    Args:
        container: Container node to search in
        test_id: Test ID value
        
    Returns:
        List of matching HTMLNodes
        
    Raises:
        ValueError: If no elements found
    """
    results = _find_by_test_id(container, test_id)
    if not results:
        raise ValueError(f"Unable to find elements with test ID: {test_id}")
    return results


def queryAllByTestId(
    container: HTMLNode,
    test_id: str,
) -> List[HTMLNode]:
    """
    Find all elements by data-testid attribute (returns empty list if none found).
    
    Args:
        container: Container node to search in
        test_id: Test ID value
        
    Returns:
        List of matching HTMLNodes (may be empty)
    """
    return _find_by_test_id(container, test_id)


async def findAllByTestId(
    container: HTMLNode,
    test_id: str,
    timeout: float = 5.0,
    interval: float = 0.05,
) -> List[HTMLNode]:
    """
    Find all elements by data-testid attribute (async, waits for elements).
    
    Args:
        container: Container node to search in
        test_id: Test ID value
        timeout: Maximum time to wait in seconds
        interval: Time between checks in seconds
        
    Returns:
        List of matching HTMLNodes
        
    Raises:
        TimeoutError: If no elements found within timeout
    """
    start = time.time()
    while time.time() - start < timeout:
        results = queryAllByTestId(container, test_id)
        if results:
            return results
        await asyncio.sleep(interval)
    
    raise TimeoutError(f"Elements with test ID '{test_id}' not found within {timeout} seconds")


# =============================================================================
# Query by Label Text
# =============================================================================

def _find_by_label_text(
    container: HTMLNode,
    text: Union[str, Pattern],
    exact: bool = True,
) -> List[HTMLNode]:
    """
    Find all form elements with matching label text.
    
    Args:
        container: Container node to search in
        text: Label text pattern
        exact: If True, exact match; if False, substring match
        
    Returns:
        List of matching nodes
    """
    results = []
    
    # First, find all labels with matching text
    labels = []
    for node in _find_all_descendants(container):
        if node.tag == "label":
            label_text = _get_element_text(node).strip()  # Strip whitespace
            if _match_text(label_text, text, exact=exact):
                labels.append(node)
    
    # Find associated inputs
    for label in labels:
        # Check for 'for' attribute
        label_for = label.attrs.get("for")
        if label_for:
            # Find input with matching id
            for node in _find_all_descendants(container):
                if node.attrs.get("id") == label_for:
                    results.append(node)
        
        # Check for nested input
        for child in label.children:
            if isinstance(child, HTMLNode) and child.tag in ("input", "select", "textarea"):
                results.append(child)
    
    return results


def getByLabelText(
    container: HTMLNode,
    text: Union[str, Pattern],
    exact: bool = True,
) -> HTMLNode:
    """
    Find element by associated label text (throws if not found).
    
    Args:
        container: Container node to search in
        text: Label text pattern
        exact: If True, exact match; if False, substring match
        
    Returns:
        First matching HTMLNode
        
    Raises:
        ValueError: If no element found
    """
    results = _find_by_label_text(container, text, exact=exact)
    if not results:
        pattern_str = text.pattern if isinstance(text, Pattern) else text
        raise ValueError(f"Unable to find element with label text: {pattern_str}")
    return results[0]


def queryByLabelText(
    container: HTMLNode,
    text: Union[str, Pattern],
    exact: bool = True,
) -> Optional[HTMLNode]:
    """
    Find element by associated label text (returns None if not found).
    
    Args:
        container: Container node to search in
        text: Label text pattern
        exact: If True, exact match; if False, substring match
        
    Returns:
        First matching HTMLNode or None
    """
    results = _find_by_label_text(container, text, exact=exact)
    return results[0] if results else None


async def findByLabelText(
    container: HTMLNode,
    text: Union[str, Pattern],
    exact: bool = True,
    timeout: float = 5.0,
    interval: float = 0.05,
) -> HTMLNode:
    """
    Find element by associated label text (async, waits for element).
    
    Args:
        container: Container node to search in
        text: Label text pattern
        exact: If True, exact match; if False, substring match
        timeout: Maximum time to wait in seconds
        interval: Time between checks in seconds
        
    Returns:
        First matching HTMLNode
        
    Raises:
        TimeoutError: If element not found within timeout
    """
    start = time.time()
    while time.time() - start < timeout:
        result = queryByLabelText(container, text, exact=exact)
        if result is not None:
            return result
        await asyncio.sleep(interval)
    
    pattern_str = text.pattern if isinstance(text, Pattern) else text
    raise TimeoutError(f"Element with label text '{pattern_str}' not found within {timeout} seconds")


def getAllByLabelText(
    container: HTMLNode,
    text: Union[str, Pattern],
    exact: bool = True,
) -> List[HTMLNode]:
    """
    Find all elements by associated label text (throws if none found).
    
    Args:
        container: Container node to search in
        text: Label text pattern
        exact: If True, exact match; if False, substring match
        
    Returns:
        List of matching HTMLNodes
        
    Raises:
        ValueError: If no elements found
    """
    results = _find_by_label_text(container, text, exact=exact)
    if not results:
        pattern_str = text.pattern if isinstance(text, Pattern) else text
        raise ValueError(f"Unable to find elements with label text: {pattern_str}")
    return results


def queryAllByLabelText(
    container: HTMLNode,
    text: Union[str, Pattern],
    exact: bool = True,
) -> List[HTMLNode]:
    """
    Find all elements by associated label text (returns empty list if none found).
    
    Args:
        container: Container node to search in
        text: Label text pattern
        exact: If True, exact match; if False, substring match
        
    Returns:
        List of matching HTMLNodes (may be empty)
    """
    return _find_by_label_text(container, text, exact=exact)


async def findAllByLabelText(
    container: HTMLNode,
    text: Union[str, Pattern],
    exact: bool = True,
    timeout: float = 5.0,
    interval: float = 0.05,
) -> List[HTMLNode]:
    """
    Find all elements by associated label text (async, waits for elements).
    
    Args:
        container: Container node to search in
        text: Label text pattern
        exact: If True, exact match; if False, substring match
        timeout: Maximum time to wait in seconds
        interval: Time between checks in seconds
        
    Returns:
        List of matching HTMLNodes
        
    Raises:
        TimeoutError: If no elements found within timeout
    """
    start = time.time()
    while time.time() - start < timeout:
        results = queryAllByLabelText(container, text, exact=exact)
        if results:
            return results
        await asyncio.sleep(interval)
    
    pattern_str = text.pattern if isinstance(text, Pattern) else text
    raise TimeoutError(f"Elements with label text '{pattern_str}' not found within {timeout} seconds")


# =============================================================================
# Query by Placeholder Text
# =============================================================================

def _find_by_placeholder_text(
    container: HTMLNode,
    text: Union[str, Pattern],
    exact: bool = True,
) -> List[HTMLNode]:
    """
    Find all input/textarea elements with matching placeholder.
    
    Args:
        container: Container node to search in
        text: Placeholder text pattern
        exact: If True, exact match; if False, substring match
        
    Returns:
        List of matching nodes
    """
    results = []
    for node in _find_all_descendants(container):
        if node.tag in ("input", "textarea"):
            placeholder = node.attrs.get("placeholder", "")
            if placeholder and _match_text(placeholder, text, exact=exact):
                results.append(node)
    return results


def getByPlaceholderText(
    container: HTMLNode,
    text: Union[str, Pattern],
    exact: bool = True,
) -> HTMLNode:
    """
    Find element by placeholder text (throws if not found).
    
    Args:
        container: Container node to search in
        text: Placeholder text pattern
        exact: If True, exact match; if False, substring match
        
    Returns:
        First matching HTMLNode
        
    Raises:
        ValueError: If no element found
    """
    results = _find_by_placeholder_text(container, text, exact=exact)
    if not results:
        pattern_str = text.pattern if isinstance(text, Pattern) else text
        raise ValueError(f"Unable to find element with placeholder text: {pattern_str}")
    return results[0]


def queryByPlaceholderText(
    container: HTMLNode,
    text: Union[str, Pattern],
    exact: bool = True,
) -> Optional[HTMLNode]:
    """
    Find element by placeholder text (returns None if not found).
    
    Args:
        container: Container node to search in
        text: Placeholder text pattern
        exact: If True, exact match; if False, substring match
        
    Returns:
        First matching HTMLNode or None
    """
    results = _find_by_placeholder_text(container, text, exact=exact)
    return results[0] if results else None


async def findByPlaceholderText(
    container: HTMLNode,
    text: Union[str, Pattern],
    exact: bool = True,
    timeout: float = 5.0,
    interval: float = 0.05,
) -> HTMLNode:
    """
    Find element by placeholder text (async, waits for element).
    
    Args:
        container: Container node to search in
        text: Placeholder text pattern
        exact: If True, exact match; if False, substring match
        timeout: Maximum time to wait in seconds
        interval: Time between checks in seconds
        
    Returns:
        First matching HTMLNode
        
    Raises:
        TimeoutError: If element not found within timeout
    """
    start = time.time()
    while time.time() - start < timeout:
        result = queryByPlaceholderText(container, text, exact=exact)
        if result is not None:
            return result
        await asyncio.sleep(interval)
    
    pattern_str = text.pattern if isinstance(text, Pattern) else text
    raise TimeoutError(f"Element with placeholder text '{pattern_str}' not found within {timeout} seconds")


def getAllByPlaceholderText(
    container: HTMLNode,
    text: Union[str, Pattern],
    exact: bool = True,
) -> List[HTMLNode]:
    """
    Find all elements by placeholder text (throws if none found).
    
    Args:
        container: Container node to search in
        text: Placeholder text pattern
        exact: If True, exact match; if False, substring match
        
    Returns:
        List of matching HTMLNodes
        
    Raises:
        ValueError: If no elements found
    """
    results = _find_by_placeholder_text(container, text, exact=exact)
    if not results:
        pattern_str = text.pattern if isinstance(text, Pattern) else text
        raise ValueError(f"Unable to find elements with placeholder text: {pattern_str}")
    return results


def queryAllByPlaceholderText(
    container: HTMLNode,
    text: Union[str, Pattern],
    exact: bool = True,
) -> List[HTMLNode]:
    """
    Find all elements by placeholder text (returns empty list if none found).
    
    Args:
        container: Container node to search in
        text: Placeholder text pattern
        exact: If True, exact match; if False, substring match
        
    Returns:
        List of matching HTMLNodes (may be empty)
    """
    return _find_by_placeholder_text(container, text, exact=exact)


async def findAllByPlaceholderText(
    container: HTMLNode,
    text: Union[str, Pattern],
    exact: bool = True,
    timeout: float = 5.0,
    interval: float = 0.05,
) -> List[HTMLNode]:
    """
    Find all elements by placeholder text (async, waits for elements).
    
    Args:
        container: Container node to search in
        text: Placeholder text pattern
        exact: If True, exact match; if False, substring match
        timeout: Maximum time to wait in seconds
        interval: Time between checks in seconds
        
    Returns:
        List of matching HTMLNodes
        
    Raises:
        TimeoutError: If no elements found within timeout
    """
    start = time.time()
    while time.time() - start < timeout:
        results = queryAllByPlaceholderText(container, text, exact=exact)
        if results:
            return results
        await asyncio.sleep(interval)
    
    pattern_str = text.pattern if isinstance(text, Pattern) else text
    raise TimeoutError(f"Elements with placeholder text '{pattern_str}' not found within {timeout} seconds")

