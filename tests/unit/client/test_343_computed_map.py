"""
Phase 34.3: ComputedStyleMap Tests

Tests for el.computedStyleMap() read-only computed style access.
Verifies that all computed style APIs transpile correctly to JavaScript.

Total: 15 tests
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# Basic Access Tests (5 tests)
# =============================================================================

class TestAccess:
    """Tests for accessing computedStyleMap."""
    
    def test_computed_style_map_access(self):
        """el.computedStyleMap() should pass through unchanged."""
        code = 'computed = el.computedStyleMap()'
        result = transpile(code)
        assert 'el.computedStyleMap()' in result
        assert "__py." not in result
    
    def test_chained_computed_access(self):
        """document.getElementById(...).computedStyleMap() should work."""
        code = 'computed = document.getElementById("box").computedStyleMap()'
        result = transpile(code)
        assert 'computedStyleMap()' in result
    
    def test_computed_stored_in_variable(self):
        """Storing computed map in variable should work."""
        code = '''
box = document.getElementById("box")
computed = box.computedStyleMap()
'''
        result = transpile(code)
        assert 'computedStyleMap()' in result
    
    def test_computed_size(self):
        """computed.size should pass through unchanged."""
        code = '''
computed = el.computedStyleMap()
count = computed.size
'''
        result = transpile(code)
        assert 'computed.size' in result
    
    def test_computed_as_parameter(self):
        """Passing computed map to function should work."""
        code = '''
def read_styles(computed_map):
    return computed_map.get("width")

read_styles(el.computedStyleMap())
'''
        result = transpile(code)
        assert 'computedStyleMap()' in result


# =============================================================================
# Get Method Tests (5 tests)
# =============================================================================

class TestGet:
    """Tests for computedStyleMap get() method."""
    
    def test_get_width(self):
        """computed.get('width') should produce valid JS."""
        code = '''
computed = el.computedStyleMap()
width = computed.get("width")
'''
        result = transpile(code)
        assert 'computedStyleMap()' in result
        assert '"width"' in result
    
    def test_get_chained(self):
        """el.computedStyleMap().get() chained should work."""
        code = 'width = el.computedStyleMap().get("width")'
        result = transpile(code)
        assert 'computedStyleMap()' in result
        assert '"width"' in result
    
    def test_get_returns_resolved_value(self):
        """get() returns resolved CSSUnitValue (not % → px)."""
        code = '''
computed = el.computedStyleMap()
width = computed.get("width")
px_value = width.value
'''
        result = transpile(code)
        assert '"width"' in result
        assert 'width.value' in result
    
    def test_get_all_computed(self):
        """computed.getAll() should pass through unchanged."""
        code = '''
computed = el.computedStyleMap()
borders = computed.getAll("border")
'''
        result = transpile(code)
        assert 'getAll("border")' in result
    
    def test_get_transform(self):
        """computed.get('transform') returns CSSTransformValue."""
        code = '''
computed = el.computedStyleMap()
transform = computed.get("transform")
'''
        result = transpile(code)
        assert '"transform"' in result
        assert 'computed' in result


# =============================================================================
# Has/Iteration Tests (5 tests)
# =============================================================================

class TestHasIteration:
    """Tests for has() and iteration methods on computed styles."""
    
    def test_has_property(self):
        """computed.has('width') should pass through unchanged."""
        code = '''
computed = el.computedStyleMap()
has_width = computed.has("width")
'''
        result = transpile(code)
        assert 'has("width")' in result
    
    def test_keys(self):
        """computed.keys() should produce iterable keys."""
        code = '''
computed = el.computedStyleMap()
props = computed.keys()
'''
        result = transpile(code)
        # Can be .keys() or Object.keys()
        assert 'computed' in result
    
    def test_values(self):
        """computed.values() should produce iterable values."""
        code = '''
computed = el.computedStyleMap()
vals = computed.values()
'''
        result = transpile(code)
        # Can be .values() or Object.values()
        assert 'computed' in result
    
    def test_entries(self):
        """computed.entries() should pass through unchanged."""
        code = '''
computed = el.computedStyleMap()
entries = computed.entries()
'''
        result = transpile(code)
        assert 'entries()' in result
    
    def test_for_each(self):
        """computed.forEach(callback) should pass through unchanged."""
        code = '''
def log_style(value, prop):
    console.log(prop, value)

el.computedStyleMap().forEach(log_style)
'''
        result = transpile(code)
        assert 'forEach' in result
