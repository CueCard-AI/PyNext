"""
Test Dict Comprehensions

=============================================================================
WHAT THIS FILE TESTS
=============================================================================

Tests for Python dict comprehensions transpiled to JavaScript:
- {k: v for k, v in items} → Object.fromEntries(...)
- {k: v*2 for k, v in items if v > 0}
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# SIMPLE DICT COMPREHENSIONS
# =============================================================================

class TestSimpleDictComp:
    """Test basic dict comprehensions."""
    
    def test_identity(self):
        """{k: v for k, v in items}"""
        result = transpile("y = {k: v for k, v in items}")
        assert "Object.fromEntries" in result
    
    def test_transform_value(self):
        """{k: v*2 for k, v in items}"""
        result = transpile("y = {k: v*2 for k, v in items}")
        assert "Object.fromEntries" in result
    
    def test_from_dict_items(self):
        """{k: v for k, v in d.items()}"""
        result = transpile("y = {k: v for k, v in d.items()}")
        assert "Object.fromEntries" in result
        # Phase 33.2: dict.items() now uses __py.dict.items() runtime helper
        assert "Object.entries" in result or ".items()" in result or "__py.dict.items" in result


# =============================================================================
# WITH FILTER
# =============================================================================

class TestWithFilter:
    """Test dict comprehensions with if clause."""
    
    def test_filter_value(self):
        """{k: v for k, v in d.items() if v > 0}"""
        result = transpile("y = {k: v for k, v in d.items() if v > 0}")
        assert ".filter(" in result
    
    def test_filter_key(self):
        """{k: v for k, v in d.items() if k.startswith('a')}"""
        result = transpile("y = {k: v for k, v in d.items() if k.startswith('a')}")
        assert ".filter(" in result
    
    def test_filter_and_transform(self):
        """{k: v*2 for k, v in d.items() if v > 0}"""
        result = transpile("y = {k: v*2 for k, v in d.items() if v > 0}")
        assert ".filter(" in result and ".map(" in result


# =============================================================================
# KEY TRANSFORMATIONS
# =============================================================================

class TestKeyTransformations:
    """Test dict comprehensions with key transformations."""
    
    def test_uppercase_keys(self):
        """{k.upper(): v for k, v in d.items()} → .toUpperCase() in JS"""
        result = transpile("y = {k.upper(): v for k, v in d.items()}")
        # Python .upper() becomes JS .toUpperCase()
        assert "k.toUpperCase()" in result or "k.upper()" in result
    
    def test_key_from_value(self):
        """{v: k for k, v in d.items()} - invert dict"""
        result = transpile("y = {v: k for k, v in d.items()}")
        assert "Object.fromEntries" in result


# =============================================================================
# FROM LIST OF TUPLES
# =============================================================================

class TestFromTuples:
    """Test dict comprehensions from list of tuples."""
    
    def test_from_pairs(self):
        """{k: v for k, v in pairs}"""
        result = transpile("y = {k: v for k, v in pairs}")
        assert "Object.fromEntries" in result
    
    def test_from_enumerate(self):
        """{i: x for i, x in enumerate(items)}"""
        result = transpile("y = {i: x for i, x in enumerate(items)}")
        assert "Object.fromEntries" in result
    
    def test_from_zip(self):
        """{k: v for k, v in zip(keys, values)}"""
        result = transpile("y = {k: v for k, v in zip(keys, values)}")
        assert "Object.fromEntries" in result


# =============================================================================
# SINGLE VARIABLE ITERATION
# =============================================================================

class TestSingleVariable:
    """Test dict comprehensions with single iteration variable."""
    
    def test_key_from_item(self):
        """{x.id: x for x in items}"""
        result = transpile("y = {x.id: x for x in items}")
        assert "Object.fromEntries" in result
        assert "x.id" in result
    
    def test_key_and_value_from_item(self):
        """{x.name: x.value for x in items}"""
        result = transpile("y = {x.name: x.value for x in items}")
        assert "x.name" in result and "x.value" in result


# =============================================================================
# COMPLEX EXPRESSIONS
# =============================================================================

class TestComplexExpressions:
    """Test dict comprehensions with complex expressions."""
    
    def test_computed_key(self):
        """{f"key_{i}": x for i, x in enumerate(items)}"""
        result = transpile('y = {f"key_{i}": x for i, x in enumerate(items)}')
        assert "Object.fromEntries" in result
    
    def test_nested_value(self):
        """{k: {"value": v} for k, v in items}"""
        result = transpile('y = {k: {"value": v} for k, v in items}')
        assert "Object.fromEntries" in result
    
    def test_ternary_value(self):
        """{k: v if v else 0 for k, v in items}"""
        result = transpile("y = {k: v if v else 0 for k, v in items}")
        assert "Object.fromEntries" in result


# =============================================================================
# EDGE CASES
# =============================================================================

class TestDictCompEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_empty_source(self):
        """{k: v for k, v in []}"""
        result = transpile("y = {k: v for k, v in []}")
        assert "Object.fromEntries" in result
    
    def test_constant_value(self):
        """{k: 1 for k in keys}"""
        result = transpile("y = {k: 1 for k in keys}")
        assert "Object.fromEntries" in result


# =============================================================================
# REAL-WORLD PATTERNS
# =============================================================================

class TestRealWorldPatterns:
    """Test common real-world dict comprehension patterns."""
    
    def test_index_by_id(self):
        """{item.id: item for item in items}"""
        result = transpile("index = {item.id: item for item in items}")
        assert "item.id" in result
    
    def test_count_by_key(self):
        """{k: len(v) for k, v in groups.items()}"""
        result = transpile("counts = {k: len(v) for k, v in groups.items()}")
        assert "Object.fromEntries" in result
    
    def test_filter_dict(self):
        """{k: v for k, v in d.items() if k in allowed_keys}"""
        result = transpile("filtered = {k: v for k, v in d.items() if k in allowed_keys}")
        assert ".filter(" in result
    
    def test_transform_dict_values(self):
        """{k: process(v) for k, v in d.items()}"""
        result = transpile("processed = {k: process(v) for k, v in d.items()}")
        assert "process(v)" in result


# =============================================================================
# IN HANDLERS
# =============================================================================

class TestInHandlers:
    """Test dict comprehensions in handlers."""
    
    def test_in_function(self):
        """def index(): return {x.id: x for x in items}"""
        code = """
def build_index():
    return {x.id: x for x in items}
"""
        result = transpile(code)
        assert "Object.fromEntries" in result
    
    def test_in_conditional(self):
        """if items: index = {...}"""
        code = """
if items:
    index = {x.id: x for x in items}
"""
        result = transpile(code)
        assert "Object.fromEntries" in result


# =============================================================================
# OUTPUT STRUCTURE
# =============================================================================

class TestOutputStructure:
    """Test that output has correct structure."""
    
    def test_uses_object_from_entries(self):
        """Should use Object.fromEntries"""
        result = transpile("y = {k: v for k, v in items}")
        assert "Object.fromEntries" in result
    
    def test_produces_key_value_pairs(self):
        """Should map to [key, value] pairs"""
        result = transpile("y = {k: v*2 for k, v in items}")
        # The map should produce [k, ...] pairs
        assert "[k," in result or "=> [" in result
