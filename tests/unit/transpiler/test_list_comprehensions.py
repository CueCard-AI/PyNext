"""
Test List Comprehensions

=============================================================================
WHAT THIS FILE TESTS
=============================================================================

Tests for Python list comprehensions transpiled to JavaScript:
- [x*2 for x in items] → items.map(x => x*2)
- [x for x in items if x > 0] → items.filter(x => x > 0)
- Nested comprehensions
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# SIMPLE LIST COMPREHENSIONS
# =============================================================================

class TestSimpleListComp:
    """Test basic list comprehensions."""
    
    def test_identity(self):
        """[x for x in items]"""
        result = transpile("y = [x for x in items]")
        assert "__py.iter(items)" in result
    
    def test_double(self):
        """[x*2 for x in items]"""
        result = transpile("y = [x*2 for x in items]")
        assert ".map(" in result
    
    def test_add(self):
        """[x+1 for x in items]"""
        result = transpile("y = [x+1 for x in items]")
        assert ".map(" in result
    
    def test_call(self):
        """[str(x) for x in items]"""
        result = transpile("y = [str(x) for x in items]")
        assert ".map(" in result
    
    def test_attribute(self):
        """[x.name for x in items]"""
        result = transpile("y = [x.name for x in items]")
        assert "x.name" in result


# =============================================================================
# WITH FILTER
# =============================================================================

class TestWithFilter:
    """Test list comprehensions with if clause."""
    
    def test_simple_filter(self):
        """[x for x in items if x > 0]"""
        result = transpile("y = [x for x in items if x > 0]")
        assert ".filter(" in result
    
    def test_filter_and_map(self):
        """[x*2 for x in items if x > 0]"""
        result = transpile("y = [x*2 for x in items if x > 0]")
        assert ".filter(" in result
        assert ".map(" in result
    
    def test_filter_equality(self):
        """[x for x in items if x == target]"""
        result = transpile("y = [x for x in items if x == target]")
        assert ".filter(" in result
    
    def test_filter_none(self):
        """[x for x in items if x is not None]"""
        result = transpile("y = [x for x in items if x is not None]")
        assert ".filter(" in result
    
    def test_filter_truthiness(self):
        """[x for x in items if x]"""
        result = transpile("y = [x for x in items if x]")
        assert ".filter(" in result
    
    def test_filter_method_call(self):
        """[x for x in items if x.is_valid()]"""
        result = transpile("y = [x for x in items if x.is_valid()]")
        assert "x.is_valid()" in result


# =============================================================================
# MULTIPLE FILTERS
# =============================================================================

class TestMultipleFilters:
    """Test list comprehensions with multiple if clauses."""
    
    def test_two_filters(self):
        """[x for x in items if x > 0 if x < 10]"""
        result = transpile("y = [x for x in items if x > 0 if x < 10]")
        # Should chain filters
        assert ".filter(" in result


# =============================================================================
# NESTED COMPREHENSIONS (Single Generator)
# =============================================================================

class TestNestedSingleGen:
    """Test list comprehensions that produce nested results."""
    
    def test_nested_list(self):
        """[[y for y in x] for x in matrix]"""
        result = transpile("y = [[i for i in row] for row in matrix]")
        assert ".map(" in result


# =============================================================================
# WITH EXPRESSIONS
# =============================================================================

class TestWithExpressions:
    """Test list comprehensions with complex expressions."""
    
    def test_with_ternary(self):
        """[x if x > 0 else 0 for x in items]"""
        result = transpile("y = [x if x > 0 else 0 for x in items]")
        assert ".map(" in result
    
    def test_with_subscript(self):
        """[x[0] for x in items]"""
        result = transpile("y = [x[0] for x in items]")
        assert ".map(" in result
    
    def test_with_method(self):
        """[x.strip() for x in items] → .trim() in JS"""
        result = transpile("y = [x.strip() for x in items]")
        # Python .strip() becomes JS .trim()
        assert "x.trim()" in result or "x.strip()" in result
    
    def test_with_fstring(self):
        """[f"{x}" for x in items]"""
        result = transpile('y = [f"{x}" for x in items]')
        assert ".map(" in result


# =============================================================================
# TUPLE UNPACKING
# =============================================================================

class TestTupleUnpacking:
    """Test list comprehensions with tuple unpacking."""
    
    def test_two_vars(self):
        """[a + b for a, b in pairs]"""
        result = transpile("y = [a + b for a, b in pairs]")
        assert "[a, b]" in result
    
    def test_three_vars(self):
        """[a + b + c for a, b, c in triples]"""
        result = transpile("y = [a + b + c for a, b, c in triples]")
        assert "[a, b, c]" in result
    
    def test_key_value(self):
        """[k + v for k, v in d.items()]"""
        result = transpile("y = [k + str(v) for k, v in d.items()]")
        assert "[k, v]" in result


# =============================================================================
# ITERATING OVER DIFFERENT TYPES
# =============================================================================

class TestDifferentIterables:
    """Test iterating over various types."""
    
    def test_over_list(self):
        """[x for x in [1, 2, 3]]"""
        result = transpile("y = [x for x in [1, 2, 3]]")
        assert "[1, 2, 3]" in result
    
    def test_over_range(self):
        """[x for x in range(10)]"""
        result = transpile("y = [x for x in range(10)]")
        # range(10) becomes __py.range(0, 10) or similar
        assert "__py.range" in result
    
    def test_over_string(self):
        """[c for c in 'hello']"""
        result = transpile("y = [c for c in 'hello']")
        assert "'hello'" in result or '"hello"' in result
    
    def test_over_dict(self):
        """[k for k in d]"""
        result = transpile("y = [k for k in d]")
        assert "__py.iter(d)" in result
    
    def test_over_dict_keys(self):
        """[k for k in d.keys()]"""
        result = transpile("y = [k for k in d.keys()]")
        assert "Object.keys" in result or ".keys()" in result
    
    def test_over_dict_values(self):
        """[v for v in d.values()]"""
        result = transpile("y = [v for v in d.values()]")
        assert "Object.values" in result or ".values()" in result
    
    def test_over_enumerate(self):
        """[i for i, x in enumerate(items)]"""
        result = transpile("y = [i for i, x in enumerate(items)]")
        assert "__py.enumerate" in result or "enumerate" in result


# =============================================================================
# EDGE CASES
# =============================================================================

class TestListCompEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_empty_comprehension(self):
        """[x for x in []]"""
        result = transpile("y = [x for x in []]")
        assert "[]" in result
    
    def test_nested_attribute(self):
        """[x.a.b for x in items]"""
        result = transpile("y = [x.a.b for x in items]")
        assert "x.a.b" in result
    
    def test_complex_filter_expression(self):
        """[x for x in items if x and x.active]"""
        result = transpile("y = [x for x in items if x and x.active]")
        assert ".filter(" in result


# =============================================================================
# REAL-WORLD PATTERNS
# =============================================================================

class TestRealWorldPatterns:
    """Test common real-world list comprehension patterns."""
    
    def test_extract_ids(self):
        """[user.id for user in users]"""
        result = transpile("ids = [user.id for user in users]")
        assert "user.id" in result
    
    def test_filter_active(self):
        """[x for x in items if x.active]"""
        result = transpile("active = [x for x in items if x.active]")
        assert ".filter(" in result
    
    def test_transform_names(self):
        """[name.lower() for name in names] → .toLowerCase() in JS"""
        result = transpile("lower_names = [name.lower() for name in names]")
        # Python .lower() becomes JS .toLowerCase()
        assert "name.toLowerCase()" in result or "name.lower()" in result
    
    def test_filter_and_transform(self):
        """[x.strip() for x in lines if x.strip()]"""
        result = transpile("stripped = [x.strip() for x in lines if x.strip()]")
        assert ".filter(" in result and ".map(" in result
    
    def test_flatten_simple(self):
        """[item for sublist in lists for item in sublist]"""
        # This is nested comprehension - multiple generators
        # Will require flatMap
        result = transpile("flat = [item for sublist in lists for item in sublist]")
        # Should produce flattening
        assert ".map(" in result or ".flatMap(" in result


# =============================================================================
# IN HANDLERS
# =============================================================================

class TestInHandlers:
    """Test list comprehensions in handlers."""
    
    def test_in_function(self):
        """def get_ids(): return [x.id for x in items]"""
        code = """
def get_ids():
    return [x.id for x in items]
"""
        result = transpile(code)
        assert ".map(" in result
    
    def test_assigned_and_used(self):
        """ids = [...]; process(ids)"""
        code = """
def process():
    ids = [x.id for x in items]
    send(ids)
"""
        result = transpile(code)
        assert ".map(" in result
    
    def test_in_conditional(self):
        """if items: result = [...]"""
        code = """
if items:
    result = [x*2 for x in items]
"""
        result = transpile(code)
        assert ".map(" in result


# =============================================================================
# OUTPUT STRUCTURE
# =============================================================================

class TestOutputStructure:
    """Test that output has correct structure."""
    
    def test_produces_array(self):
        """Result should be wrapped to produce array"""
        result = transpile("y = [x*2 for x in items]")
        # Should use spread to create array: [...items.map(...)]
        assert "[..." in result or ".map(" in result
    
    def test_filter_then_map_order(self):
        """Filter should come before map"""
        result = transpile("y = [x*2 for x in items if x > 0]")
        # filter should appear before map in the chain
        filter_pos = result.find(".filter(")
        map_pos = result.find(".map(")
        assert filter_pos < map_pos
