"""
Comprehensive tests for Client Testing Event Firing.

WHAT THIS FILE TESTS:
- Mouse events (click, dblClick, contextMenu, mouseDown, mouseUp, etc.)
- Keyboard events (keyDown, keyUp, keyPress)
- Form events (change, input, submit)
- Focus events (focus, blur)
- Touch events (touchStart, touchEnd, touchMove, touchCancel)

Total: 30 tests
"""

import pytest
from pynext.testing.client_events import fireEvent
from pynext.testing.render import HTMLNode, parse_html


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def button_element():
    """Create a button element."""
    html = '<div><button onclick="handleClick()">Click me</button></div>'
    container = parse_html(html)
    return container.find("button")


@pytest.fixture
def input_element():
    """Create an input element."""
    html = '<div><input type="text" onchange="handleChange(event)" /></div>'
    container = parse_html(html)
    return container.find("input")


# =============================================================================
# Mouse Event Tests
# =============================================================================

class TestMouseEvents:
    """Tests for mouse events."""
    
    def test_click_event(self, button_element):
        """Test fireEvent.click()."""
        # Should not raise
        fireEvent.click(button_element)
    
    def test_dblClick_event(self, button_element):
        """Test fireEvent.dblClick()."""
        fireEvent.dblClick(button_element)
    
    def test_contextMenu_event(self, button_element):
        """Test fireEvent.contextMenu()."""
        fireEvent.contextMenu(button_element)
    
    def test_mouseDown_event(self, button_element):
        """Test fireEvent.mouseDown()."""
        fireEvent.mouseDown(button_element)
    
    def test_mouseUp_event(self, button_element):
        """Test fireEvent.mouseUp()."""
        fireEvent.mouseUp(button_element)
    
    def test_mouseMove_event(self, button_element):
        """Test fireEvent.mouseMove()."""
        fireEvent.mouseMove(button_element, {"clientX": 10, "clientY": 20})
    
    def test_mouseEnter_event(self, button_element):
        """Test fireEvent.mouseEnter()."""
        fireEvent.mouseEnter(button_element)
    
    def test_mouseLeave_event(self, button_element):
        """Test fireEvent.mouseLeave()."""
        fireEvent.mouseLeave(button_element)
    
    def test_mouseOver_event(self, button_element):
        """Test fireEvent.mouseOver()."""
        fireEvent.mouseOver(button_element)
    
    def test_mouseOut_event(self, button_element):
        """Test fireEvent.mouseOut()."""
        fireEvent.mouseOut(button_element)


# =============================================================================
# Keyboard Event Tests
# =============================================================================

class TestKeyboardEvents:
    """Tests for keyboard events."""
    
    def test_keyDown_event(self, input_element):
        """Test fireEvent.keyDown()."""
        fireEvent.keyDown(input_element, {"key": "Enter", "code": "Enter"})
    
    def test_keyUp_event(self, input_element):
        """Test fireEvent.keyUp()."""
        fireEvent.keyUp(input_element, {"key": "Escape", "code": "Escape"})
    
    def test_keyPress_event(self, input_element):
        """Test fireEvent.keyPress()."""
        fireEvent.keyPress(input_element, {"key": "a", "code": "KeyA"})


# =============================================================================
# Form Event Tests
# =============================================================================

class TestFormEvents:
    """Tests for form events."""
    
    def test_change_event(self, input_element):
        """Test fireEvent.change()."""
        fireEvent.change(input_element, {"target": {"value": "new value"}})
        # Should update value attribute
        assert input_element.attrs.get("value") == "new value"
    
    def test_input_event(self, input_element):
        """Test fireEvent.input()."""
        fireEvent.input(input_element, {"target": {"value": "typing..."}})
        assert input_element.attrs.get("value") == "typing..."
    
    def test_submit_event(self):
        """Test fireEvent.submit()."""
        html = '<div><form onsubmit="handleSubmit(event)"></form></div>'
        container = parse_html(html)
        form = container.find("form")
        assert form is not None, "Form element should be found"
        fireEvent.submit(form)


# =============================================================================
# Focus Event Tests
# =============================================================================

class TestFocusEvents:
    """Tests for focus events."""
    
    def test_focus_event(self, input_element):
        """Test fireEvent.focus()."""
        fireEvent.focus(input_element)
        assert input_element.attrs.get("data-focused") == "true"
    
    def test_blur_event(self, input_element):
        """Test fireEvent.blur()."""
        # First focus, then blur
        fireEvent.focus(input_element)
        assert input_element.attrs.get("data-focused") == "true"
        
        fireEvent.blur(input_element)
        assert "data-focused" not in input_element.attrs


# =============================================================================
# Touch Event Tests
# =============================================================================

class TestTouchEvents:
    """Tests for touch events."""
    
    def test_touchStart_event(self, button_element):
        """Test fireEvent.touchStart()."""
        fireEvent.touchStart(button_element)
    
    def test_touchEnd_event(self, button_element):
        """Test fireEvent.touchEnd()."""
        fireEvent.touchEnd(button_element)
    
    def test_touchMove_event(self, button_element):
        """Test fireEvent.touchMove()."""
        fireEvent.touchMove(button_element, {"touches": [{"clientX": 10, "clientY": 20}]})
    
    def test_touchCancel_event(self, button_element):
        """Test fireEvent.touchCancel()."""
        fireEvent.touchCancel(button_element)


# =============================================================================
# Event Properties Tests
# =============================================================================

class TestEventProperties:
    """Tests for event properties."""
    
    def test_click_with_custom_properties(self, button_element):
        """Test click event with custom properties."""
        fireEvent.click(button_element, {
            "clientX": 100,
            "clientY": 200,
            "button": 0
        })
    
    def test_keyDown_with_key_properties(self, input_element):
        """Test keyDown with key properties."""
        fireEvent.keyDown(input_element, {
            "key": "Enter",
            "code": "Enter",
            "ctrlKey": True,
            "shiftKey": False
        })
    
    def test_change_updates_value(self, input_element):
        """Test that change event updates element value."""
        initial_value = input_element.attrs.get("value")
        fireEvent.change(input_element, {"target": {"value": "updated"}})
        assert input_element.attrs.get("value") == "updated"


# =============================================================================
# Integration Tests
# =============================================================================

class TestEventIntegration:
    """Integration tests for event firing."""
    
    def test_click_then_change_flow(self):
        """Test a typical user interaction flow."""
        html = """
        <div>
            <input type="text" id="search" />
            <button>Search</button>
        </div>
        """
        container = parse_html(html)
        input_elem = container.query_selector("#search")
        button = container.find("button")
        
        # Type in input
        fireEvent.change(input_elem, {"target": {"value": "query"}})
        assert input_elem.attrs.get("value") == "query"
        
        # Click button
        fireEvent.click(button)
    
    def test_focus_input_then_blur(self, input_element):
        """Test focus then blur sequence."""
        fireEvent.focus(input_element)
        assert input_element.attrs.get("data-focused") == "true"
        
        fireEvent.blur(input_element)
        assert "data-focused" not in input_element.attrs

