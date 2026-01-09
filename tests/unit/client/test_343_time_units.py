"""
Phase 34.3: CSS Typed OM Time Units Tests

Tests for CSS time unit factory methods:
- CSS.s() - seconds
- CSS.ms() - milliseconds
- Conversion between time units

Total: 10 tests
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# CSS.s() Seconds Tests (5 tests)
# =============================================================================

class TestSecondsFactory:
    """Tests for CSS.s() seconds factory method."""
    
    def test_s_basic(self):
        """CSS.s(0.3) should create a 0.3 second value."""
        code = 'duration = CSS.s(0.3)'
        result = transpile(code)
        assert 'CSS.s(0.3)' in result
        assert 'duration' in result
    
    def test_s_integer(self):
        """CSS.s(1) should create a 1 second value."""
        code = 'duration = CSS.s(1)'
        result = transpile(code)
        assert 'CSS.s(1)' in result
    
    def test_s_in_animation(self):
        """CSS.s() should work for animation durations."""
        code = '''
animation_duration = CSS.s(0.5)
el.attributeStyleMap.set("animation-duration", animation_duration)
'''
        result = transpile(code)
        assert 'CSS.s(0.5)' in result
        assert 'set("animation-duration"' in result
    
    def test_s_in_transition(self):
        """CSS.s() should work for transition durations."""
        code = '''
transition_time = CSS.s(0.25)
el.attributeStyleMap.set("transition-duration", transition_time)
'''
        result = transpile(code)
        assert 'CSS.s(0.25)' in result
        assert 'transition-duration' in result
    
    def test_s_zero(self):
        """CSS.s(0) should create a zero second value."""
        code = 'no_delay = CSS.s(0)'
        result = transpile(code)
        assert 'CSS.s(0)' in result


# =============================================================================
# CSS.ms() Milliseconds Tests (3 tests)
# =============================================================================

class TestMillisecondsFactory:
    """Tests for CSS.ms() milliseconds factory method."""
    
    def test_ms_basic(self):
        """CSS.ms(300) should create a 300ms value."""
        code = 'duration = CSS.ms(300)'
        result = transpile(code)
        assert 'CSS.ms(300)' in result
    
    def test_ms_small(self):
        """CSS.ms(16) should create a 16ms value (one frame at 60fps)."""
        code = 'frame_time = CSS.ms(16)'
        result = transpile(code)
        assert 'CSS.ms(16)' in result
    
    def test_ms_in_delay(self):
        """CSS.ms() should work for animation delays."""
        code = '''
delay = CSS.ms(100)
el.attributeStyleMap.set("animation-delay", delay)
'''
        result = transpile(code)
        assert 'CSS.ms(100)' in result
        assert 'animation-delay' in result


# =============================================================================
# Time Unit Conversion Tests (2 tests)
# =============================================================================

class TestTimeConversion:
    """Tests for converting between time units."""
    
    def test_s_to_ms_arithmetic(self):
        """Multiplying seconds by 1000 conceptually gives milliseconds."""
        code = '''
seconds = CSS.s(0.5)
# To get equivalent ms, multiply value
scaled = seconds.mul(1000)
'''
        result = transpile(code)
        assert 'CSS.s(0.5)' in result
        assert 'mul(1000)' in result
    
    def test_ms_to_s_arithmetic(self):
        """Dividing milliseconds by 1000 conceptually gives seconds."""
        code = '''
ms = CSS.ms(500)
# To get equivalent seconds, divide value  
scaled = ms.div(1000)
'''
        result = transpile(code)
        assert 'CSS.ms(500)' in result
        assert 'div(1000)' in result

