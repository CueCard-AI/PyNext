"""
Phase 34.4: Extra Event Types Tests

Tests for additional event types:
- PromiseRejectionEvent
- ProgressEvent
- PageTransitionEvent
- DeviceMotionEvent
- DeviceOrientationEvent
- SecurityPolicyViolationEvent

Total: 10 tests
"""

import pytest
from pynext.transpiler import transpile


class TestPromiseRejectionEvent:
    """Tests for PromiseRejectionEvent."""
    
    def test_promise_property(self):
        """Access the rejected promise."""
        code = '''
def on_rejection(event):
    promise = event.promise
'''
        result = transpile(code)
        assert 'event.promise' in result
        assert '__py.' not in result
    
    def test_reason_property(self):
        """Access the rejection reason."""
        code = '''
def on_rejection(event):
    reason = event.reason
    if reason:
        console.error(reason.message)
'''
        result = transpile(code)
        assert 'event.reason' in result


class TestProgressEvent:
    """Tests for ProgressEvent."""
    
    def test_loaded_and_total(self):
        """Access loaded and total bytes."""
        code = '''
def on_progress(event):
    loaded = event.loaded
    total = event.total
    percent = (loaded / total) * 100
'''
        result = transpile(code)
        assert 'event.loaded' in result
        assert 'event.total' in result
    
    def test_length_computable_check(self):
        """Check if length is computable."""
        code = '''
def on_progress(event):
    if event.lengthComputable:
        update_progress(event.loaded, event.total)
    else:
        show_indeterminate_progress()
'''
        result = transpile(code)
        assert 'event.lengthComputable' in result


class TestPageTransitionEvent:
    """Tests for PageTransitionEvent (bfcache)."""
    
    def test_persisted_property(self):
        """Check if page was restored from bfcache."""
        code = '''
def on_pageshow(event):
    if event.persisted:
        refresh_data()
        reconnect_websockets()
'''
        result = transpile(code)
        assert 'event.persisted' in result


class TestDeviceMotionEvent:
    """Tests for DeviceMotionEvent."""
    
    def test_acceleration_property(self):
        """Access acceleration data."""
        code = '''
def on_motion(event):
    accel = event.acceleration
    if accel:
        x, y, z = accel.x, accel.y, accel.z
'''
        result = transpile(code)
        assert 'event.acceleration' in result
    
    def test_rotation_rate_property(self):
        """Access rotation rate data."""
        code = '''
def on_motion(event):
    rotation = event.rotationRate
    if rotation:
        alpha = rotation.alpha
'''
        result = transpile(code)
        assert 'event.rotationRate' in result


class TestDeviceOrientationEvent:
    """Tests for DeviceOrientationEvent."""
    
    def test_orientation_properties(self):
        """Access alpha, beta, gamma orientation."""
        code = '''
def on_orientation(event):
    heading = event.alpha
    tilt_fb = event.beta
    tilt_lr = event.gamma
'''
        result = transpile(code)
        assert 'event.alpha' in result
        assert 'event.beta' in result
        assert 'event.gamma' in result


class TestSecurityPolicyViolationEvent:
    """Tests for SecurityPolicyViolationEvent (CSP)."""
    
    def test_csp_violation_properties(self):
        """Access CSP violation details."""
        code = '''
def on_csp_violation(event):
    directive = event.violatedDirective
    blocked = event.blockedURI
    doc = event.documentURI
'''
        result = transpile(code)
        assert 'event.violatedDirective' in result
        assert 'event.blockedURI' in result
        assert 'event.documentURI' in result

