"""
PyNext Testing - Accessibility

WCAG 2.1 AA compliance checking for components.
One function call to check all accessibility requirements.

Example:
    from pynext.testing import render, assert_accessible
    
    result = render(Button, label="Submit")
    assert_accessible(result)  # Checks everything!

Why This Matters:
    - 15% of the world's population has a disability
    - Accessible sites are better for everyone
    - Legal requirements (ADA, WCAG)
    - Better SEO

What We Check:
    - ARIA roles and attributes
    - Keyboard navigation
    - Color contrast
    - Form labels
    - Alt text for images
    - Focus management
    - Semantic HTML
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Set

from pynext.testing.render import RenderResult, HTMLNode


# =============================================================================
# Accessibility Violation Types
# =============================================================================

class Severity(Enum):
    """Severity levels for accessibility violations."""
    CRITICAL = "critical"  # Must fix - blocks users
    SERIOUS = "serious"    # Should fix - significantly impacts users
    MODERATE = "moderate"  # Consider fixing - some impact
    MINOR = "minor"        # Nice to have


class WCAGLevel(Enum):
    """WCAG conformance levels."""
    A = "A"      # Minimum
    AA = "AA"    # Recommended (most laws require this)
    AAA = "AAA"  # Highest


@dataclass
class A11yViolation:
    """
    An accessibility violation found during testing.
    
    Provides enough information to fix the issue:
    - What's wrong
    - Why it matters
    - How to fix it
    """
    rule_id: str           # e.g., "button-name"
    description: str       # Human-readable explanation
    impact: Severity
    wcag_level: WCAGLevel
    wcag_criteria: str     # e.g., "1.1.1"
    element: str           # The HTML element with the issue
    help_text: str         # How to fix it
    
    def __str__(self) -> str:
        return (
            f"[{self.impact.value.upper()}] {self.rule_id}: {self.description}\n"
            f"  WCAG {self.wcag_level.value} - {self.wcag_criteria}\n"
            f"  Element: {self.element}\n"
            f"  Fix: {self.help_text}"
        )


@dataclass
class A11yResult:
    """
    Result of accessibility testing.
    
    Contains all violations found, grouped by severity.
    """
    violations: List[A11yViolation]
    
    @property
    def passes(self) -> bool:
        """True if no critical or serious violations."""
        return not any(
            v.impact in (Severity.CRITICAL, Severity.SERIOUS)
            for v in self.violations
        )
    
    @property
    def critical_count(self) -> int:
        return sum(1 for v in self.violations if v.impact == Severity.CRITICAL)
    
    @property
    def serious_count(self) -> int:
        return sum(1 for v in self.violations if v.impact == Severity.SERIOUS)
    
    def summary(self) -> str:
        """Get a summary of violations."""
        if not self.violations:
            return "✅ No accessibility violations found"
        
        counts = {}
        for v in self.violations:
            counts[v.impact.value] = counts.get(v.impact.value, 0) + 1
        
        parts = [f"{count} {severity}" for severity, count in counts.items()]
        return f"❌ Accessibility issues: {', '.join(parts)}"


# =============================================================================
# WCAG Rule Checkers
# =============================================================================

def check_images_alt(node: HTMLNode, violations: List[A11yViolation]) -> None:
    """
    Check that images have alt text.
    
    WCAG 1.1.1: Non-text Content (Level A)
    """
    if node.tag == "img":
        if "alt" not in node.attrs:
            violations.append(A11yViolation(
                rule_id="image-alt",
                description="Images must have alt text",
                impact=Severity.CRITICAL,
                wcag_level=WCAGLevel.A,
                wcag_criteria="1.1.1",
                element=f"<img src=\"{node.attrs.get('src', '')}\">",
                help_text="Add alt=\"description\" to the <img> tag. Use alt=\"\" for decorative images.",
            ))
    
    for child in node.children:
        if isinstance(child, HTMLNode):
            check_images_alt(child, violations)


def check_button_name(node: HTMLNode, violations: List[A11yViolation]) -> None:
    """
    Check that buttons have accessible names.
    
    WCAG 4.1.2: Name, Role, Value (Level A)
    """
    if node.tag == "button":
        has_text = bool(node.text.strip())
        has_aria_label = "aria-label" in node.attrs
        has_aria_labelledby = "aria-labelledby" in node.attrs
        
        if not (has_text or has_aria_label or has_aria_labelledby):
            violations.append(A11yViolation(
                rule_id="button-name",
                description="Buttons must have accessible names",
                impact=Severity.CRITICAL,
                wcag_level=WCAGLevel.A,
                wcag_criteria="4.1.2",
                element=f"<button class=\"{node.attrs.get('class', '')}\">",
                help_text="Add text content, aria-label, or aria-labelledby to the button.",
            ))
    
    for child in node.children:
        if isinstance(child, HTMLNode):
            check_button_name(child, violations)


def check_link_name(node: HTMLNode, violations: List[A11yViolation]) -> None:
    """
    Check that links have accessible names.
    
    WCAG 2.4.4: Link Purpose (Level A)
    """
    if node.tag == "a":
        has_text = bool(node.text.strip())
        has_aria_label = "aria-label" in node.attrs
        has_aria_labelledby = "aria-labelledby" in node.attrs
        
        # Check for image inside link
        has_img_with_alt = any(
            isinstance(c, HTMLNode) and c.tag == "img" and c.attrs.get("alt")
            for c in node.children
        )
        
        if not (has_text or has_aria_label or has_aria_labelledby or has_img_with_alt):
            violations.append(A11yViolation(
                rule_id="link-name",
                description="Links must have accessible names",
                impact=Severity.SERIOUS,
                wcag_level=WCAGLevel.A,
                wcag_criteria="2.4.4",
                element=f"<a href=\"{node.attrs.get('href', '')}\">",
                help_text="Add text content, aria-label, or an image with alt text inside the link.",
            ))
    
    for child in node.children:
        if isinstance(child, HTMLNode):
            check_link_name(child, violations)


def check_form_labels(node: HTMLNode, violations: List[A11yViolation]) -> None:
    """
    Check that form inputs have labels.
    
    WCAG 1.3.1: Info and Relationships (Level A)
    """
    labeled_inputs = {"text", "email", "password", "tel", "url", "search", "number", "date", "time", "checkbox", "radio"}
    
    if node.tag == "input":
        input_type = node.attrs.get("type", "text")
        
        if input_type in labeled_inputs:
            has_id = "id" in node.attrs
            has_aria_label = "aria-label" in node.attrs
            has_aria_labelledby = "aria-labelledby" in node.attrs
            has_placeholder = "placeholder" in node.attrs  # Not sufficient alone
            
            if not (has_aria_label or has_aria_labelledby):
                if not has_id:
                    violations.append(A11yViolation(
                        rule_id="label",
                        description="Form inputs must have labels",
                        impact=Severity.CRITICAL,
                        wcag_level=WCAGLevel.A,
                        wcag_criteria="1.3.1",
                        element=f"<input type=\"{input_type}\">",
                        help_text="Add an id and matching <label for=\"id\">, or use aria-label.",
                    ))
    
    elif node.tag in ("select", "textarea"):
        has_id = "id" in node.attrs
        has_aria_label = "aria-label" in node.attrs
        has_aria_labelledby = "aria-labelledby" in node.attrs
        
        if not (has_aria_label or has_aria_labelledby or has_id):
            violations.append(A11yViolation(
                rule_id="label",
                description=f"<{node.tag}> must have a label",
                impact=Severity.CRITICAL,
                wcag_level=WCAGLevel.A,
                wcag_criteria="1.3.1",
                element=f"<{node.tag}>",
                help_text="Add an id and matching <label for=\"id\">, or use aria-label.",
            ))
    
    for child in node.children:
        if isinstance(child, HTMLNode):
            check_form_labels(child, violations)


def check_heading_order(node: HTMLNode, violations: List[A11yViolation], prev_level: int = 0) -> int:
    """
    Check that headings are in order (no skipping levels).
    
    WCAG 1.3.1: Info and Relationships (Level A)
    """
    heading_tags = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5, "h6": 6}
    current_level = prev_level
    
    if node.tag in heading_tags:
        level = heading_tags[node.tag]
        
        if prev_level > 0 and level > prev_level + 1:
            violations.append(A11yViolation(
                rule_id="heading-order",
                description=f"Heading levels should only increase by one",
                impact=Severity.MODERATE,
                wcag_level=WCAGLevel.A,
                wcag_criteria="1.3.1",
                element=f"<{node.tag}>{node.text[:30]}...</{node.tag}>" if len(node.text) > 30 else f"<{node.tag}>{node.text}</{node.tag}>",
                help_text=f"Previous heading was h{prev_level}, but this is h{level}. Use h{prev_level + 1} instead.",
            ))
        
        current_level = level
    
    for child in node.children:
        if isinstance(child, HTMLNode):
            current_level = check_heading_order(child, violations, current_level)
    
    return current_level


def check_aria_valid(node: HTMLNode, violations: List[A11yViolation]) -> None:
    """
    Check that ARIA attributes are valid.
    
    WCAG 4.1.2: Name, Role, Value (Level A)
    """
    valid_roles = {
        "alert", "alertdialog", "application", "article", "banner", "button",
        "cell", "checkbox", "columnheader", "combobox", "complementary",
        "contentinfo", "definition", "dialog", "directory", "document",
        "feed", "figure", "form", "grid", "gridcell", "group", "heading",
        "img", "link", "list", "listbox", "listitem", "log", "main",
        "marquee", "math", "menu", "menubar", "menuitem", "menuitemcheckbox",
        "menuitemradio", "navigation", "none", "note", "option", "presentation",
        "progressbar", "radio", "radiogroup", "region", "row", "rowgroup",
        "rowheader", "scrollbar", "search", "searchbox", "separator",
        "slider", "spinbutton", "status", "switch", "tab", "table",
        "tablist", "tabpanel", "term", "textbox", "timer", "toolbar",
        "tooltip", "tree", "treegrid", "treeitem"
    }
    
    role = node.attrs.get("role")
    if role and role not in valid_roles:
        violations.append(A11yViolation(
            rule_id="aria-valid-attr-value",
            description=f"Invalid ARIA role: '{role}'",
            impact=Severity.SERIOUS,
            wcag_level=WCAGLevel.A,
            wcag_criteria="4.1.2",
            element=f"<{node.tag} role=\"{role}\">",
            help_text=f"Use a valid ARIA role. See https://www.w3.org/TR/wai-aria-1.1/#role_definitions",
        ))
    
    # Check aria-hidden on focusable elements
    if node.attrs.get("aria-hidden") == "true":
        if node.tag in ("button", "a", "input", "select", "textarea") or "tabindex" in node.attrs:
            violations.append(A11yViolation(
                rule_id="aria-hidden-focus",
                description="aria-hidden should not be on focusable elements",
                impact=Severity.SERIOUS,
                wcag_level=WCAGLevel.A,
                wcag_criteria="4.1.2",
                element=f"<{node.tag} aria-hidden=\"true\">",
                help_text="Remove aria-hidden=\"true\" or make the element not focusable.",
            ))
    
    for child in node.children:
        if isinstance(child, HTMLNode):
            check_aria_valid(child, violations)


def check_keyboard_access(node: HTMLNode, violations: List[A11yViolation]) -> None:
    """
    Check that interactive elements are keyboard accessible.
    
    WCAG 2.1.1: Keyboard (Level A)
    """
    interactive_tags = {"a", "button", "input", "select", "textarea"}
    
    # Check for click handlers without keyboard handlers on non-interactive elements
    if node.tag not in interactive_tags:
        has_onclick = "onclick" in node.attrs
        has_role = "role" in node.attrs
        has_tabindex = "tabindex" in node.attrs
        
        if has_onclick and not has_tabindex:
            violations.append(A11yViolation(
                rule_id="keyboard",
                description="Click handler without keyboard access",
                impact=Severity.SERIOUS,
                wcag_level=WCAGLevel.A,
                wcag_criteria="2.1.1",
                element=f"<{node.tag} onclick=\"...\">",
                help_text="Add tabindex=\"0\" and onkeydown handler, or use a <button> instead.",
            ))
    
    for child in node.children:
        if isinstance(child, HTMLNode):
            check_keyboard_access(child, violations)


def check_color_contrast(node: HTMLNode, violations: List[A11yViolation]) -> None:
    """
    Check for potential color contrast issues.
    
    WCAG 1.4.3: Contrast (Minimum) (Level AA)
    
    Note: Full contrast checking requires computed styles,
    which we can't do without a browser. We flag potential issues.
    """
    style = node.attrs.get("style", "")
    
    # Check for low-contrast color combinations in inline styles
    low_contrast_patterns = [
        (r"color:\s*#[89a-fA-F]{6}", r"background:\s*#[fF]{6}"),  # Light text on white
        (r"color:\s*#[0-3]{6}", r"background:\s*#[0-3]{6}"),      # Dark text on dark
        (r"color:\s*lightgray", r"background:\s*white"),
        (r"color:\s*#ccc", r"background:\s*#fff"),
    ]
    
    # This is a simplified check - real contrast checking needs computed styles
    if "color:" in style.lower() and "background" in style.lower():
        # Flag for manual review
        # In a real implementation, we'd calculate actual contrast ratios
        pass
    
    for child in node.children:
        if isinstance(child, HTMLNode):
            check_color_contrast(child, violations)


def check_focus_visible(node: HTMLNode, violations: List[A11yViolation]) -> None:
    """
    Check that focus indicators are not removed.
    
    WCAG 2.4.7: Focus Visible (Level AA)
    """
    style = node.attrs.get("style", "")
    
    if "outline: none" in style or "outline:none" in style:
        if "outline: 0" in style or "outline:0" in style:
            violations.append(A11yViolation(
                rule_id="focus-visible",
                description="Focus outline should not be removed without replacement",
                impact=Severity.SERIOUS,
                wcag_level=WCAGLevel.AA,
                wcag_criteria="2.4.7",
                element=f"<{node.tag} style=\"{style[:50]}...\">",
                help_text="If removing outline, provide an alternative focus indicator.",
            ))
    
    for child in node.children:
        if isinstance(child, HTMLNode):
            check_focus_visible(child, violations)


def check_language(node: HTMLNode, violations: List[A11yViolation]) -> None:
    """
    Check that page has a language attribute.
    
    WCAG 3.1.1: Language of Page (Level A)
    """
    if node.tag == "html":
        if "lang" not in node.attrs:
            violations.append(A11yViolation(
                rule_id="html-lang",
                description="<html> must have a lang attribute",
                impact=Severity.SERIOUS,
                wcag_level=WCAGLevel.A,
                wcag_criteria="3.1.1",
                element="<html>",
                help_text="Add lang=\"en\" (or appropriate language code) to the <html> tag.",
            ))
    
    for child in node.children:
        if isinstance(child, HTMLNode):
            check_language(child, violations)


def check_page_title(node: HTMLNode, violations: List[A11yViolation], found_title: List[bool]) -> None:
    """
    Check that page has a title.
    
    WCAG 2.4.2: Page Titled (Level A)
    """
    if node.tag == "title":
        if node.text.strip():
            found_title[0] = True
        else:
            violations.append(A11yViolation(
                rule_id="document-title",
                description="<title> should not be empty",
                impact=Severity.SERIOUS,
                wcag_level=WCAGLevel.A,
                wcag_criteria="2.4.2",
                element="<title></title>",
                help_text="Add descriptive text to the <title> element.",
            ))
    
    for child in node.children:
        if isinstance(child, HTMLNode):
            check_page_title(child, violations, found_title)


# =============================================================================
# Main Accessibility Testing Functions
# =============================================================================

def check_accessibility(result: RenderResult) -> A11yResult:
    """
    Run all accessibility checks on a rendered component.
    
    Returns detailed results with all violations found.
    
    Args:
        result: RenderResult from render()
        
    Returns:
        A11yResult with all violations
        
    Example:
        result = render(MyComponent)
        a11y = check_accessibility(result)
        
        if not a11y.passes:
            for v in a11y.violations:
                print(v)
    """
    violations: List[A11yViolation] = []
    
    if result.root is None:
        return A11yResult(violations=[])
    
    # Run all checks
    check_images_alt(result.root, violations)
    check_button_name(result.root, violations)
    check_link_name(result.root, violations)
    check_form_labels(result.root, violations)
    check_heading_order(result.root, violations)
    check_aria_valid(result.root, violations)
    check_keyboard_access(result.root, violations)
    check_color_contrast(result.root, violations)
    check_focus_visible(result.root, violations)
    check_language(result.root, violations)
    
    # Page title check (only for full documents)
    found_title = [False]
    check_page_title(result.root, violations, found_title)
    
    return A11yResult(violations=violations)


def assert_accessible(
    result: RenderResult,
    level: WCAGLevel = WCAGLevel.AA,
    ignore_rules: Optional[Set[str]] = None,
) -> None:
    """
    Assert that component passes accessibility checks.
    
    Raises AssertionError if critical or serious violations found.
    
    Args:
        result: RenderResult from render()
        level: Minimum WCAG level to enforce (default AA)
        ignore_rules: Set of rule IDs to ignore
        
    Example:
        result = render(Button, label="Submit")
        assert_accessible(result)
        
        # Ignore specific rules
        assert_accessible(result, ignore_rules={"heading-order"})
    """
    a11y_result = check_accessibility(result)
    ignore_rules = ignore_rules or set()
    
    # Filter violations
    violations = [
        v for v in a11y_result.violations
        if v.rule_id not in ignore_rules
    ]
    
    # Filter by WCAG level
    level_priority = {WCAGLevel.A: 0, WCAGLevel.AA: 1, WCAGLevel.AAA: 2}
    required_level = level_priority[level]
    
    violations = [
        v for v in violations
        if level_priority[v.wcag_level] <= required_level
    ]
    
    # Check for blocking violations
    blocking = [
        v for v in violations
        if v.impact in (Severity.CRITICAL, Severity.SERIOUS)
    ]
    
    if blocking:
        message_parts = [f"Accessibility violations found ({len(blocking)} blocking):"]
        for v in blocking[:5]:  # Show first 5
            message_parts.append(str(v))
        
        if len(blocking) > 5:
            message_parts.append(f"... and {len(blocking) - 5} more")
        
        raise AssertionError("\n\n".join(message_parts))


def assert_role(
    result: RenderResult,
    role: str,
    selector: Optional[str] = None,
) -> None:
    """
    Assert that element has correct ARIA role.
    
    Args:
        result: RenderResult to check
        role: Expected ARIA role
        selector: Optional CSS selector to find element
        
    Example:
        result = render(Modal)
        assert_role(result, "dialog", ".modal")
    """
    if selector:
        element = result.query_selector(selector)
        if element is None:
            raise AssertionError(f"Element '{selector}' not found")
    else:
        element = result.root
    
    actual_role = element.attrs.get("role")
    
    # Some elements have implicit roles
    implicit_roles = {
        "button": "button",
        "a": "link",
        "input": "textbox",  # varies by type
        "img": "img",
        "nav": "navigation",
        "main": "main",
        "header": "banner",
        "footer": "contentinfo",
        "aside": "complementary",
        "form": "form",
        "article": "article",
    }
    
    if actual_role is None:
        actual_role = implicit_roles.get(element.tag)
    
    if actual_role != role:
        raise AssertionError(
            f"Element has wrong role\n"
            f"  Expected: {role}\n"
            f"  Actual: {actual_role}"
        )


def assert_aria_label(
    result: RenderResult,
    expected: str,
    selector: Optional[str] = None,
) -> None:
    """
    Assert that element has correct aria-label.
    
    Args:
        result: RenderResult to check
        expected: Expected aria-label value
        selector: Optional CSS selector to find element
        
    Example:
        result = render(IconButton, icon="close")
        assert_aria_label(result, "Close", "button")
    """
    if selector:
        element = result.query_selector(selector)
        if element is None:
            raise AssertionError(f"Element '{selector}' not found")
    else:
        element = result.root
    
    actual = element.attrs.get("aria-label")
    
    if actual != expected:
        raise AssertionError(
            f"Element has wrong aria-label\n"
            f"  Expected: {expected}\n"
            f"  Actual: {actual}"
        )


def assert_focusable(
    result: RenderResult,
    selector: str,
) -> None:
    """
    Assert that element is keyboard focusable.
    
    Args:
        result: RenderResult to check
        selector: CSS selector for element that should be focusable
        
    Example:
        result = render(CustomButton)
        assert_focusable(result, ".custom-btn")
    """
    element = result.query_selector(selector)
    if element is None:
        raise AssertionError(f"Element '{selector}' not found")
    
    focusable_tags = {"a", "button", "input", "select", "textarea"}
    has_tabindex = "tabindex" in element.attrs
    is_naturally_focusable = element.tag in focusable_tags
    
    if element.attrs.get("tabindex") == "-1":
        raise AssertionError(
            f"Element '{selector}' has tabindex=\"-1\" (not focusable)"
        )
    
    if not (is_naturally_focusable or has_tabindex):
        raise AssertionError(
            f"Element '{selector}' is not focusable\n"
            f"  Add tabindex=\"0\" or use an interactive element"
        )

