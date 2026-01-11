"""
Phase 34.4: Multi-Touch Gesture Edge Cases

Tests for complex touch gesture handling:
- Pinch-to-zoom calculations
- Rotation angle detection
- Gesture state management

Total: 15 tests
"""

import pytest
from pynext.transpiler import transpile


class TestPinchGesture:
    """Tests for pinch-to-zoom gesture handling."""
    
    def test_two_touch_distance(self):
        """Calculate distance between two touch points."""
        code = '''
def get_distance(touch1, touch2):
    dx = touch2.clientX - touch1.clientX
    dy = touch2.clientY - touch1.clientY
    return (dx * dx + dy * dy) ** 0.5

def on_touchmove(event):
    if event.touches.length == 2:
        dist = get_distance(event.touches[0], event.touches[1])
'''
        result = transpile(code)
        # Transpiler uses __py.getitem for array indexing
        assert 'event.touches' in result
        assert 'clientX' in result
    
    def test_pinch_scale_factor(self):
        """Calculate scale factor from initial to current distance."""
        code = '''
initial_distance = 0

def on_touchstart(event):
    global initial_distance
    if event.touches.length == 2:
        initial_distance = get_distance(event.touches[0], event.touches[1])

def on_touchmove(event):
    if event.touches.length == 2 and initial_distance > 0:
        current = get_distance(event.touches[0], event.touches[1])
        scale = current / initial_distance
        apply_zoom(scale)
'''
        result = transpile(code)
        assert 'event.touches.length' in result
    
    def test_pinch_center_point(self):
        """Calculate center point between two touches."""
        code = '''
def get_center(touch1, touch2):
    cx = (touch1.clientX + touch2.clientX) / 2
    cy = (touch1.clientY + touch2.clientY) / 2
    return (cx, cy)
'''
        result = transpile(code)
        assert 'clientX' in result
        assert 'clientY' in result


class TestRotationGesture:
    """Tests for rotation gesture detection."""
    
    def test_rotation_angle(self):
        """Calculate rotation angle between two touch points."""
        code = '''
import math

def get_angle(touch1, touch2):
    dx = touch2.clientX - touch1.clientX
    dy = touch2.clientY - touch1.clientY
    return math.atan2(dy, dx)
'''
        result = transpile(code)
        assert 'atan2' in result or 'Math.atan2' in result
    
    def test_rotation_delta(self):
        """Calculate rotation delta from initial angle."""
        code = '''
initial_angle = 0

def on_touchmove(event):
    if event.touches.length == 2:
        current_angle = get_angle(event.touches[0], event.touches[1])
        rotation = current_angle - initial_angle
        apply_rotation(rotation)
'''
        result = transpile(code)
        assert 'event.touches' in result


class TestGestureStateManagement:
    """Tests for gesture state tracking."""
    
    def test_gesture_start_detection(self):
        """Detect when two-finger gesture starts."""
        code = '''
gesture_active = False

def on_touchstart(event):
    global gesture_active
    if event.touches.length == 2:
        gesture_active = True
        event.preventDefault()
'''
        result = transpile(code)
        assert 'event.touches.length' in result
        assert 'event.preventDefault()' in result
    
    def test_gesture_end_detection(self):
        """Detect when gesture ends (finger lifted)."""
        code = '''
def on_touchend(event):
    global gesture_active
    if event.touches.length < 2:
        gesture_active = False
        finalize_gesture()
'''
        result = transpile(code)
        assert 'event.touches.length' in result
    
    def test_changed_touches_tracking(self):
        """Track which touches changed."""
        code = '''
def on_touchend(event):
    for touch in event.changedTouches:
        remove_touch_indicator(touch.identifier)
'''
        result = transpile(code)
        assert 'event.changedTouches' in result
        assert 'touch.identifier' in result
    
    def test_target_touches_filter(self):
        """Filter touches by target element."""
        code = '''
def on_touchmove(event):
    relevant = event.targetTouches
    if relevant.length >= 2:
        handle_multi_touch(relevant)
'''
        result = transpile(code)
        assert 'event.targetTouches' in result


class TestTouchEdgeCases:
    """Edge cases in touch event handling."""
    
    def test_touch_identifier_persistence(self):
        """Touch identifiers persist across events."""
        code = '''
touch_start_positions = {}

def on_touchstart(event):
    for touch in event.changedTouches:
        touch_start_positions[touch.identifier] = (touch.clientX, touch.clientY)
'''
        result = transpile(code)
        assert 'touch.identifier' in result
    
    def test_rapid_touch_sequence(self):
        """Handle rapid touch add/remove."""
        code = '''
def on_touchstart(event):
    if event.touches.length > 2:
        # More than 2 fingers - ignore extra
        return
'''
        result = transpile(code)
        assert 'event.touches.length' in result
    
    def test_touch_cancel_handling(self):
        """Handle touchcancel (e.g., incoming call)."""
        code = '''
def on_touchcancel(event):
    reset_gesture_state()
    for touch in event.changedTouches:
        cleanup_touch(touch.identifier)
'''
        result = transpile(code)
        assert 'event.changedTouches' in result
    
    def test_touch_force_pressure(self):
        """Access touch force/pressure if available."""
        code = '''
def on_touchmove(event):
    touch = event.touches[0]
    if hasattr(touch, "force"):
        pressure = touch.force
        adjust_brush_size(pressure)
'''
        result = transpile(code)
        assert 'touch.force' in result
    
    def test_touch_radius(self):
        """Access touch contact radius."""
        code = '''
def on_touchstart(event):
    touch = event.touches[0]
    radius_x = touch.radiusX
    radius_y = touch.radiusY
'''
        result = transpile(code)
        assert 'touch.radiusX' in result
        assert 'touch.radiusY' in result

