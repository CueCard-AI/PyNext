"""
PyNext Focus Module

Focus management for accessible PyNext applications.

Provides:
- Focus trapping (modals/dialogs)
- Focus restoration
- Roving focus (menus/lists)
- Skip links

Usage:
    from pynext.focus import FocusTrap, RovingFocus, SkipLink
    
    Dialog()[
        FocusTrap(auto_focus=True)[
            DialogContent()[...]
        ]
    ]
"""

from __future__ import annotations

from typing import Any, Callable, List, Optional
from dataclasses import dataclass


# =============================================================================
# Focus Trap
# =============================================================================

def FocusTrap(
    auto_focus: bool = True,
    restore_focus: bool = True,
    children=None,
    class_: str = "",
):
    """
    Component that traps focus within its children.
    
    Pressing Tab at the last focusable element wraps to the first,
    and Shift+Tab at the first wraps to the last.
    
    Usage:
        Dialog()[
            FocusTrap()[
                DialogContent()[
                    Input(),
                    Button()["OK"],
                ]
            ]
        ]
    
    Args:
        auto_focus: Automatically focus first element when mounted
        restore_focus: Restore focus to previous element when unmounted
        children: Content to trap focus within
    """
    from pynext import div
    from pynext.tw import cn
    
    return div(
        class_=cn("contents", class_),
        data_pynext_focus_trap="true",
        data_focus_trap_autofocus=str(auto_focus).lower(),
        data_focus_trap_restore=str(restore_focus).lower(),
    )[children]


# =============================================================================
# Roving Focus
# =============================================================================

def RovingFocus(
    orientation: str = "vertical",
    loop: bool = True,
    selector: str = "[data-roving-item]",
    children=None,
    class_: str = "",
):
    """
    Component that enables arrow key navigation between items.
    
    Usage:
        RovingFocus(orientation="vertical")[
            RovingFocusItem()[Button()["Item 1"]],
            RovingFocusItem()[Button()["Item 2"]],
            RovingFocusItem()[Button()["Item 3"]],
        ]
    
    Args:
        orientation: "vertical" (up/down), "horizontal" (left/right), or "both"
        loop: Whether to wrap at ends
        selector: CSS selector for focusable items
        children: Items to navigate between
    """
    from pynext import div
    from pynext.tw import cn
    
    return div(
        class_=cn(class_),
        data_roving_group="true",
        data_roving_orientation=orientation,
        data_roving_loop=str(loop).lower(),
        data_roving_selector=selector,
        role="group",
    )[children]


def RovingFocusItem(children=None, class_: str = ""):
    """
    An item within a RovingFocus group.
    
    Usage:
        RovingFocus()[
            RovingFocusItem()[Button()["Item 1"]],
            RovingFocusItem()[Button()["Item 2"]],
        ]
    """
    from pynext import div
    from pynext.tw import cn
    
    return div(
        class_=cn("contents", class_),
        data_roving_item="true",
        tabindex="-1",
    )[children]


# =============================================================================
# Skip Links
# =============================================================================

def SkipLinks(
    links: Optional[List[tuple]] = None,
    class_: str = "",
):
    """
    Accessible skip links for keyboard navigation.
    
    Skip links are hidden until focused (Tab key), allowing keyboard
    users to quickly navigate to main content.
    
    Usage:
        SkipLinks(links=[
            ("main-content", "Skip to main content"),
            ("navigation", "Skip to navigation"),
        ])
    
    Args:
        links: List of (target_id, label) tuples
    """
    from pynext import div, a
    from pynext.tw import cn
    
    if links is None:
        links = [
            ("main-content", "Skip to main content"),
        ]
    
    return div(class_=cn(
        "sr-only focus-within:not-sr-only",
        "fixed top-0 left-0 z-50",
        class_,
    ))[
        [
            a(
                href=f"#{target_id}",
                class_=cn(
                    "absolute top-2 left-2",
                    "bg-background border shadow-lg",
                    "px-4 py-2 rounded-md",
                    "text-sm font-medium",
                    "focus:outline-none focus:ring-2 focus:ring-ring",
                ),
                data_skip_link=target_id,
            )[label]
            for target_id, label in links
        ]
    ]


def SkipLink(
    target_id: str,
    label: str = "Skip to content",
    class_: str = "",
):
    """
    A single skip link.
    
    Usage:
        SkipLink("main-content", "Skip to main content")
    """
    from pynext import a
    from pynext.tw import cn
    
    return a(
        href=f"#{target_id}",
        class_=cn(
            "sr-only focus:not-sr-only",
            "absolute top-2 left-2 z-50",
            "bg-background border shadow-lg",
            "px-4 py-2 rounded-md",
            "text-sm font-medium",
            "focus:outline-none focus:ring-2 focus:ring-ring",
            class_,
        ),
        data_skip_link=target_id,
    )[label]


# =============================================================================
# Focus Scope
# =============================================================================

def FocusScope(
    contain: bool = False,
    restore_focus: bool = False,
    auto_focus: bool = False,
    children=None,
    class_: str = "",
):
    """
    Manages focus within a scope.
    
    Less restrictive than FocusTrap - doesn't trap, but manages
    focus behavior.
    
    Args:
        contain: Keep focus within scope (like FocusTrap but escapable)
        restore_focus: Restore focus when scope unmounts
        auto_focus: Focus first element on mount
    """
    from pynext import div
    from pynext.tw import cn
    
    return div(
        class_=cn("contents", class_),
        data_focus_scope="true",
        data_focus_scope_contain=str(contain).lower(),
        data_focus_scope_restore=str(restore_focus).lower(),
        data_focus_scope_autofocus=str(auto_focus).lower(),
    )[children]


# =============================================================================
# Focus Ring
# =============================================================================

def FocusRing(
    visible: str = "auto",
    children=None,
    class_: str = "",
):
    """
    Wrapper that manages focus ring visibility.
    
    Args:
        visible: "auto" (keyboard only), "always", or "never"
    """
    from pynext import div
    from pynext.tw import cn
    
    ring_class = ""
    if visible == "auto":
        ring_class = "focus-visible:ring-2 focus-visible:ring-ring"
    elif visible == "always":
        ring_class = "focus:ring-2 focus:ring-ring"
    # "never" adds no ring class
    
    return div(
        class_=cn(ring_class, class_),
        data_focus_ring=visible,
    )[children]


# =============================================================================
# Visually Hidden
# =============================================================================

def VisuallyHidden(children=None, as_: str = "span"):
    """
    Content that is visually hidden but accessible to screen readers.
    
    Usage:
        Button()[
            "🔍",
            VisuallyHidden()["Search"]
        ]
    """
    from pynext import span, div
    
    Element = span if as_ == "span" else div
    
    return Element(
        class_="sr-only",
        # Tailwind's sr-only handles all the CSS
    )[children]


# =============================================================================
# Utilities
# =============================================================================

def get_focusable_selector() -> str:
    """
    Get CSS selector for focusable elements.
    
    Useful for custom focus management.
    """
    return ", ".join([
        "a[href]:not([disabled])",
        "button:not([disabled])",
        "input:not([disabled])",
        "select:not([disabled])",
        "textarea:not([disabled])",
        '[tabindex]:not([tabindex="-1"]):not([disabled])',
        '[contenteditable="true"]',
    ])


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Components
    "FocusTrap",
    "RovingFocus",
    "RovingFocusItem",
    "SkipLinks",
    "SkipLink",
    "FocusScope",
    "FocusRing",
    "VisuallyHidden",
    # Utilities
    "get_focusable_selector",
]

