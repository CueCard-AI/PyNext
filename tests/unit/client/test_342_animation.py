"""
Phase 34.2: Web Animations API Tests

Tests for Web Animations API:
- element.animate()
- Animation object control
- Animation helpers (fade_in, slide_in, etc.)

Total: 20 tests
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# Element.animate() Tests (8 tests)
# =============================================================================

class TestElementAnimate:
    """Tests for element.animate() method."""
    
    def test_animate_basic(self):
        """element.animate should pass through unchanged."""
        code = '''
anim = el.animate([
    {"opacity": "0"},
    {"opacity": "1"},
], duration=300)
'''
        result = transpile(code)
        assert "el.animate" in result
        assert "opacity" in result
    
    def test_animate_with_options(self):
        """element.animate with options should work."""
        code = '''
anim = el.animate([
    {"transform": "scale(0.9)"},
    {"transform": "scale(1)"},
], duration=300, easing="ease-out", fill="forwards")
'''
        result = transpile(code)
        assert "animate" in result
        assert "ease-out" in result or "easing" in result
    
    def test_animate_await_finished(self):
        """Awaiting animation.finished should work."""
        code = '''
async def animate_el():
    anim = el.animate([
        {"opacity": "0"},
        {"opacity": "1"},
    ], duration=300)
    await anim.finished
'''
        result = transpile(code)
        assert "finished" in result
        assert "await" in result
    
    def test_animate_multiple_keyframes(self):
        """element.animate with multiple keyframes should work."""
        code = '''
anim = el.animate([
    {"opacity": "0", "transform": "translateY(-20px)"},
    {"opacity": "0.5", "transform": "translateY(-10px)"},
    {"opacity": "1", "transform": "translateY(0)"},
], duration=500)
'''
        result = transpile(code)
        assert "animate" in result
        assert "translateY" in result
    
    def test_animate_with_delay(self):
        """element.animate with delay should work."""
        code = '''
anim = el.animate([
    {"opacity": "0"},
    {"opacity": "1"},
], duration=300, delay=100)
'''
        result = transpile(code)
        assert "delay" in result
    
    def test_animate_with_iterations(self):
        """element.animate with iterations should work."""
        code = '''
anim = el.animate([
    {"transform": "rotate(0deg)"},
    {"transform": "rotate(360deg)"},
], duration=1000, iterations=3)
'''
        result = transpile(code)
        assert "iterations" in result
    
    def test_animate_infinite(self):
        """element.animate with infinite iterations should work."""
        code = '''
anim = el.animate([
    {"opacity": "0.5"},
    {"opacity": "1"},
    {"opacity": "0.5"},
], duration=2000, iterations=float("inf"))
'''
        result = transpile(code)
        assert "iterations" in result
    
    def test_get_animations(self):
        """element.getAnimations should pass through unchanged."""
        code = '''
animations = el.getAnimations()
for anim in animations:
    anim.pause()
'''
        result = transpile(code)
        assert "getAnimations" in result


# =============================================================================
# Animation Control Tests (6 tests)
# =============================================================================

class TestAnimationControl:
    """Tests for Animation object control methods."""
    
    def test_animation_pause(self):
        """animation.pause() should work."""
        code = '''
anim = el.animate([{"opacity": "0"}, {"opacity": "1"}], duration=300)
anim.pause()
'''
        result = transpile(code)
        assert "pause" in result
    
    def test_animation_play(self):
        """animation.play() should work."""
        code = '''
anim = el.animate([{"opacity": "0"}, {"opacity": "1"}], duration=300)
anim.pause()
anim.play()
'''
        result = transpile(code)
        assert "play" in result
    
    def test_animation_cancel(self):
        """animation.cancel() should work."""
        code = '''
anim = el.animate([{"opacity": "0"}, {"opacity": "1"}], duration=300)
anim.cancel()
'''
        result = transpile(code)
        assert "cancel" in result
    
    def test_animation_reverse(self):
        """animation.reverse() should work."""
        code = '''
anim = el.animate([{"opacity": "0"}, {"opacity": "1"}], duration=300)
anim.reverse()
'''
        result = transpile(code)
        assert "reverse" in result
    
    def test_animation_playback_rate(self):
        """animation.playbackRate should work."""
        code = '''
anim = el.animate([{"opacity": "0"}, {"opacity": "1"}], duration=300)
anim.playbackRate = 2.0
'''
        result = transpile(code)
        assert "playbackRate" in result
    
    def test_animation_current_time(self):
        """animation.currentTime should work."""
        code = '''
anim = el.animate([{"opacity": "0"}, {"opacity": "1"}], duration=300)
anim.currentTime = 150
'''
        result = transpile(code)
        assert "currentTime" in result


# =============================================================================
# Animation Helpers Tests (6 tests)
# =============================================================================

class TestAnimationHelpers:
    """Tests for animation helper functions."""
    
    def test_fade_in(self):
        """fade_in helper should work."""
        code = '''
from pynext.client.animation import fade_in

async def show():
    await fade_in(el)
'''
        result = transpile(code)
        assert "fade_in" in result
    
    def test_fade_out(self):
        """fade_out helper should work."""
        code = '''
from pynext.client.animation import fade_out

async def hide():
    await fade_out(el, duration=500)
'''
        result = transpile(code)
        assert "fade_out" in result
    
    def test_slide_in(self):
        """slide_in helper should work."""
        code = '''
from pynext.client.animation import slide_in

async def slide():
    await slide_in(el, direction="bottom")
'''
        result = transpile(code)
        assert "slide_in" in result
        assert "bottom" in result
    
    def test_scale_in(self):
        """scale_in helper should work."""
        code = '''
from pynext.client.animation import scale_in

async def pop():
    await scale_in(modal)
'''
        result = transpile(code)
        assert "scale_in" in result
    
    def test_shake(self):
        """shake helper should work."""
        code = '''
from pynext.client.animation import shake

async def error_shake():
    await shake(input_el)
'''
        result = transpile(code)
        assert "shake" in result
    
    def test_pulse(self):
        """pulse helper should work."""
        code = '''
from pynext.client.animation import pulse

async def click_feedback():
    await pulse(button)
'''
        result = transpile(code)
        assert "pulse" in result

