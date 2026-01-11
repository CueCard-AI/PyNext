"""
Phase 34.4: Wheel and Pointer Event Deep Tests

Unit tests for deep WheelEvent and PointerEvent coverage:
- WheelEvent deltaX/Y/Z, deltaMode
- PointerEvent properties and methods
- Pointer capture APIs
- Coalesced and predicted events

Total: 15 tests
"""

import pytest
from pynext.transpiler import transpile


class TestWheelEventProperties:
    """Tests for WheelEvent properties."""
    
    def test_delta_x(self):
        """WheelEvent deltaX should pass through."""
        code = '''
def on_wheel(event):
    horizontal = event.deltaX
'''
        result = transpile(code)
        assert 'event.deltaX' in result
        assert '__py.' not in result
    
    def test_delta_y(self):
        """WheelEvent deltaY should pass through."""
        code = '''
def on_wheel(event):
    vertical = event.deltaY
'''
        result = transpile(code)
        assert 'event.deltaY' in result
    
    def test_delta_z(self):
        """WheelEvent deltaZ should pass through."""
        code = '''
def on_wheel(event):
    depth = event.deltaZ
'''
        result = transpile(code)
        assert 'event.deltaZ' in result
    
    def test_delta_mode(self):
        """WheelEvent deltaMode should pass through."""
        code = '''
def on_wheel(event):
    mode = event.deltaMode
    if mode == 0:  # Pixel mode
        handle_pixel_scroll(event.deltaY)
    elif mode == 1:  # Line mode
        handle_line_scroll(event.deltaY)
'''
        result = transpile(code)
        assert 'event.deltaMode' in result
    
    def test_zoom_pattern(self):
        """Zoom with wheel should work."""
        code = '''
def on_wheel(event):
    if event.ctrlKey:
        event.preventDefault()
        if event.deltaY < 0:
            zoom_in()
        else:
            zoom_out()

canvas.addEventListener("wheel", on_wheel, {"passive": False})
'''
        result = transpile(code)
        assert 'event.ctrlKey' in result
        assert 'event.deltaY' in result


class TestPointerEventProperties:
    """Tests for PointerEvent properties."""
    
    def test_pointer_id(self):
        """PointerEvent pointerId should pass through."""
        code = '''
def on_pointer_down(event):
    id = event.pointerId
'''
        result = transpile(code)
        assert 'event.pointerId' in result
    
    def test_pointer_type(self):
        """PointerEvent pointerType should pass through."""
        code = '''
def on_pointer_down(event):
    if event.pointerType == "touch":
        handle_touch()
    elif event.pointerType == "pen":
        handle_pen()
    elif event.pointerType == "mouse":
        handle_mouse()
'''
        result = transpile(code)
        assert 'event.pointerType' in result
    
    def test_pressure(self):
        """PointerEvent pressure should pass through."""
        code = '''
def on_pointer_move(event):
    pressure = event.pressure
    set_brush_size(pressure * 10)
'''
        result = transpile(code)
        assert 'event.pressure' in result
    
    def test_tilt(self):
        """PointerEvent tiltX/Y should pass through."""
        code = '''
def on_pointer_move(event):
    tilt_x = event.tiltX
    tilt_y = event.tiltY
    apply_tilt_shading(tilt_x, tilt_y)
'''
        result = transpile(code)
        assert 'event.tiltX' in result
        assert 'event.tiltY' in result
    
    def test_is_primary(self):
        """PointerEvent isPrimary should pass through."""
        code = '''
def on_pointer_down(event):
    if event.isPrimary:
        start_primary_interaction()
'''
        result = transpile(code)
        assert 'event.isPrimary' in result


class TestPointerCapture:
    """Tests for pointer capture methods."""
    
    def test_set_pointer_capture(self):
        """setPointerCapture should pass through."""
        code = '''
def on_pointer_down(event):
    event.target.setPointerCapture(event.pointerId)
'''
        result = transpile(code)
        assert 'setPointerCapture' in result
        assert 'event.pointerId' in result
    
    def test_release_pointer_capture(self):
        """releasePointerCapture should pass through."""
        code = '''
def on_pointer_up(event):
    event.target.releasePointerCapture(event.pointerId)
'''
        result = transpile(code)
        assert 'releasePointerCapture' in result
    
    def test_has_pointer_capture(self):
        """hasPointerCapture should pass through."""
        code = '''
def check_capture(event):
    if event.target.hasPointerCapture(event.pointerId):
        handle_captured()
'''
        result = transpile(code)
        assert 'hasPointerCapture' in result


class TestCoalescedPredictedEvents:
    """Tests for getCoalescedEvents and getPredictedEvents."""
    
    def test_get_coalesced_events(self):
        """getCoalescedEvents should pass through."""
        code = '''
def on_pointer_move(event):
    for e in event.getCoalescedEvents():
        draw_point(e.clientX, e.clientY)
'''
        result = transpile(code)
        assert 'getCoalescedEvents()' in result
    
    def test_get_predicted_events(self):
        """getPredictedEvents should pass through."""
        code = '''
def on_pointer_move(event):
    for e in event.getPredictedEvents():
        draw_predicted_point(e.clientX, e.clientY)
'''
        result = transpile(code)
        assert 'getPredictedEvents()' in result

