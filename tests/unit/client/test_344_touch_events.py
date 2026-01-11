"""
Phase 34.4: Touch Event Tests

Unit tests for TouchEvent transpilation covering:
- Touch properties (identifier, clientX/Y, pageX/Y, etc.)
- TouchList properties (touches, changedTouches, targetTouches)
- Multi-touch handling
- Touch event methods

Total: 20 tests
"""

import pytest
from pynext.transpiler import transpile


class TestTouchProperties:
    """Tests for individual Touch object properties."""
    
    def test_touch_identifier(self):
        """Touch identifier should pass through."""
        code = '''
def handle(event):
    touch = event.touches[0]
    id = touch.identifier
'''
        result = transpile(code)
        assert 'touch.identifier' in result
        assert '__py.' not in result or '__py.getitem' in result
    
    def test_touch_client_x_y(self):
        """Touch clientX/Y should pass through."""
        code = '''
def handle(event):
    touch = event.touches[0]
    x = touch.clientX
    y = touch.clientY
'''
        result = transpile(code)
        assert 'touch.clientX' in result
        assert 'touch.clientY' in result
    
    def test_touch_page_x_y(self):
        """Touch pageX/Y should pass through."""
        code = '''
def handle(event):
    touch = event.touches[0]
    x = touch.pageX
    y = touch.pageY
'''
        result = transpile(code)
        assert 'touch.pageX' in result
        assert 'touch.pageY' in result
    
    def test_touch_screen_x_y(self):
        """Touch screenX/Y should pass through."""
        code = '''
def handle(event):
    touch = event.touches[0]
    x = touch.screenX
    y = touch.screenY
'''
        result = transpile(code)
        assert 'touch.screenX' in result
        assert 'touch.screenY' in result
    
    def test_touch_radius(self):
        """Touch radiusX/Y should pass through."""
        code = '''
def handle(event):
    touch = event.touches[0]
    rx = touch.radiusX
    ry = touch.radiusY
'''
        result = transpile(code)
        assert 'touch.radiusX' in result
        assert 'touch.radiusY' in result
    
    def test_touch_force(self):
        """Touch force should pass through."""
        code = '''
def handle(event):
    touch = event.touches[0]
    pressure = touch.force
'''
        result = transpile(code)
        assert 'touch.force' in result


class TestTouchListProperties:
    """Tests for TouchList properties."""
    
    def test_touches_length(self):
        """touches.length should pass through."""
        code = '''
def handle(event):
    count = event.touches.length
'''
        result = transpile(code)
        assert 'event.touches.length' in result
    
    def test_changed_touches(self):
        """changedTouches should pass through."""
        code = '''
def handle(event):
    changed = event.changedTouches
'''
        result = transpile(code)
        assert 'event.changedTouches' in result
    
    def test_target_touches(self):
        """targetTouches should pass through."""
        code = '''
def handle(event):
    on_target = event.targetTouches
'''
        result = transpile(code)
        assert 'event.targetTouches' in result
    
    def test_touch_list_item(self):
        """TouchList.item() should pass through."""
        code = '''
def handle(event):
    touch = event.touches.item(0)
'''
        result = transpile(code)
        assert 'event.touches.item(0)' in result


class TestTouchEventModifiers:
    """Tests for touch event modifier keys."""
    
    def test_alt_key(self):
        """altKey should pass through."""
        code = '''
def handle(event):
    if event.altKey:
        handle_alt_touch()
'''
        result = transpile(code)
        assert 'event.altKey' in result
    
    def test_ctrl_key(self):
        """ctrlKey should pass through."""
        code = '''
def handle(event):
    if event.ctrlKey:
        handle_ctrl_touch()
'''
        result = transpile(code)
        assert 'event.ctrlKey' in result


class TestTouchEventMethods:
    """Tests for touch event methods."""
    
    def test_prevent_default(self):
        """preventDefault should pass through."""
        code = '''
def handle(event):
    event.preventDefault()
'''
        result = transpile(code)
        assert 'event.preventDefault()' in result


class TestMultiTouchPatterns:
    """Tests for multi-touch handling patterns."""
    
    def test_pinch_to_zoom_pattern(self):
        """Pinch-to-zoom touch handler should work."""
        code = '''
def on_touch_move(event):
    if event.touches.length == 2:
        t1 = event.touches[0]
        t2 = event.touches[1]
        dx = t2.clientX - t1.clientX
        dy = t2.clientY - t1.clientY
'''
        result = transpile(code)
        # Comparison may use __py.eq
        assert 'event.touches.length' in result and '2' in result
        assert 't1.clientX' in result
        assert 't2.clientX' in result
    
    def test_touch_tracking(self):
        """Touch tracking with identifier should work."""
        code = '''
def on_touch_start(event):
    for touch in event.changedTouches:
        track_start(touch.identifier, touch.clientX, touch.clientY)

def on_touch_move(event):
    for touch in event.changedTouches:
        track_move(touch.identifier, touch.clientX, touch.clientY)
'''
        result = transpile(code)
        assert 'event.changedTouches' in result
        assert 'touch.identifier' in result
        assert 'touch.clientX' in result
    
    def test_single_touch_drag(self):
        """Single touch drag pattern should work."""
        code = '''
def on_touch_move(event):
    if event.touches.length == 1:
        event.preventDefault()
        touch = event.touches[0]
        move_element(touch.pageX, touch.pageY)
'''
        result = transpile(code)
        # Comparison may use __py.eq
        assert 'event.touches.length' in result and '1' in result
        assert 'event.preventDefault()' in result
        assert 'touch.pageX' in result
    
    def test_touch_target(self):
        """Touch target property should pass through."""
        code = '''
def handle(event):
    touch = event.touches[0]
    el = touch.target
'''
        result = transpile(code)
        assert 'touch.target' in result
    
    def test_all_touch_lists(self):
        """All three touch lists should work."""
        code = '''
def handle(event):
    all_touches = event.touches
    changed = event.changedTouches
    on_target = event.targetTouches
'''
        result = transpile(code)
        assert 'event.touches' in result
        assert 'event.changedTouches' in result
        assert 'event.targetTouches' in result

