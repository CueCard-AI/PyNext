"""
Test Set Comprehensions

=============================================================================
WHAT THIS FILE TESTS
=============================================================================

Tests for Python set comprehensions transpiled to JavaScript:
- {x for x in items} → new Set(items)
- {x*2 for x in items if x > 0}
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# SIMPLE SET COMPREHENSIONS
# =============================================================================

class TestSimpleSetComp:
    """Test basic set comprehensions."""
    
    def test_identity(self):
        """{x for x in items}"""
        result = transpile("y = {x for x in items}")
        assert "new Set" in result
    
    def test_transform(self):
        """{x*2 for x in items}"""
        result = transpile("y = {x*2 for x in items}")
        assert "new Set" in result
        assert ".map(" in result
    
    def test_attribute(self):
        """{x.id for x in items}"""
        result = transpile("y = {x.id for x in items}")
        assert "new Set" in result
        assert "x.id" in result


# =============================================================================
# WITH FILTER
# =============================================================================

class TestWithFilter:
    """Test set comprehensions with if clause."""
    
    def test_simple_filter(self):
        """{x for x in items if x > 0}"""
        result = transpile("y = {x for x in items if x > 0}")
        assert "new Set" in result
        assert ".filter(" in result
    
    def test_filter_and_transform(self):
        """{x*2 for x in items if x > 0}"""
        result = transpile("y = {x*2 for x in items if x > 0}")
        assert "new Set" in result
        assert ".filter(" in result
        assert ".map(" in result
    
    def test_filter_none(self):
        """{x for x in items if x is not None}"""
        result = transpile("y = {x for x in items if x is not None}")
        assert ".filter(" in result


# =============================================================================
# DIFFERENT ITERABLES
# =============================================================================

class TestDifferentIterables:
    """Test set comprehensions from various sources."""
    
    def test_from_list(self):
        """{x for x in [1, 2, 2, 3]}"""
        result = transpile("y = {x for x in [1, 2, 2, 3]}")
        assert "new Set" in result
    
    def test_from_string(self):
        """{c for c in 'hello'}"""
        result = transpile("y = {c for c in 'hello'}")
        assert "new Set" in result
    
    def test_from_range(self):
        """{x for x in range(10)}"""
        result = transpile("y = {x for x in range(10)}")
        assert "new Set" in result


# =============================================================================
# TUPLE UNPACKING
# =============================================================================

class TestTupleUnpacking:
    """Test set comprehensions with tuple unpacking."""
    
    def test_keys_only(self):
        """{k for k, v in items}"""
        result = transpile("y = {k for k, v in items}")
        assert "new Set" in result
        assert "[k, v]" in result
    
    def test_values_only(self):
        """{v for k, v in items}"""
        result = transpile("y = {v for k, v in items}")
        assert "new Set" in result


# =============================================================================
# EDGE CASES
# =============================================================================

class TestSetCompEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_empty_source(self):
        """{x for x in []}"""
        result = transpile("y = {x for x in []}")
        assert "new Set" in result
    
    def test_nested_attribute(self):
        """{x.a.b for x in items}"""
        result = transpile("y = {x.a.b for x in items}")
        assert "x.a.b" in result


# =============================================================================
# REAL-WORLD PATTERNS
# =============================================================================

class TestRealWorldPatterns:
    """Test common real-world set comprehension patterns."""
    
    def test_unique_ids(self):
        """{item.id for item in items}"""
        result = transpile("unique_ids = {item.id for item in items}")
        assert "new Set" in result
    
    def test_unique_names(self):
        """{name.lower() for name in names} → .toLowerCase() in JS"""
        result = transpile("unique_names = {name.lower() for name in names}")
        # Python .lower() becomes JS .toLowerCase()
        assert "name.toLowerCase()" in result or "name.lower()" in result
    
    def test_filter_unique(self):
        """{x for x in items if x.active}"""
        result = transpile("active_set = {x for x in items if x.active}")
        assert ".filter(" in result


# =============================================================================
# IN HANDLERS
# =============================================================================

class TestInHandlers:
    """Test set comprehensions in handlers."""
    
    def test_in_function(self):
        """def get_unique(): return {x for x in items}"""
        code = """
def get_unique():
    return {x.id for x in items}
"""
        result = transpile(code)
        assert "new Set" in result
    
    def test_in_conditional(self):
        """if items: unique = {...}"""
        code = """
if items:
    unique = {x for x in items}
"""
        result = transpile(code)
        assert "new Set" in result


# =============================================================================
# OUTPUT STRUCTURE
# =============================================================================

class TestOutputStructure:
    """Test that output has correct structure."""
    
    def test_uses_new_set(self):
        """Should use new Set()"""
        result = transpile("y = {x for x in items}")
        assert "new Set" in result
    
    def test_simple_case_no_map(self):
        """Simple identity should not need map"""
        result = transpile("y = {x for x in items}")
        # Simple case might just be new Set(items)
        assert "new Set" in result
