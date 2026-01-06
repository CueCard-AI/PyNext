"""
Test Delete Statement Transpilation

=============================================================================
WHAT THIS FILE TESTS
=============================================================================

Delete statements: del x, del items[i], del obj.attr

=============================================================================
EXPECTED TRANSFORMATIONS
=============================================================================

Python              → JavaScript
del x               → x = undefined;
del items[0]        → __py.del(items, 0);
del items[-1]       → __py.del(items, -1);
del d["key"]        → __py.del(d, "key");
del obj.attr        → delete obj.attr;
"""

import pytest
from pynext.transpiler import transpile, TranspileError


# =============================================================================
# DELETE VARIABLE
# =============================================================================

class TestDeleteVariable:
    """Test deleting variables."""
    
    def test_delete_variable(self):
        """del x"""
        result = transpile("del x")
        assert "x = undefined" in result or "delete x" in result


# =============================================================================
# DELETE LIST ITEM
# =============================================================================

class TestDeleteListItem:
    """Test deleting list items."""
    
    def test_delete_first(self):
        """del items[0]"""
        result = transpile("del items[0]")
        assert "__py.del(items, 0)" in result
    
    def test_delete_last(self):
        """del items[-1]"""
        result = transpile("del items[-1]")
        # Negative literals may be wrapped in parentheses for precedence
        assert "__py.del(items, -1)" in result or "__py.del(items, (-1))" in result
    
    def test_delete_middle(self):
        """del items[5]"""
        result = transpile("del items[5]")
        assert "__py.del(items, 5)" in result
    
    def test_delete_with_variable_index(self):
        """del items[i]"""
        result = transpile("del items[i]")
        assert "__py.del(items, i)" in result


# =============================================================================
# DELETE DICT KEY
# =============================================================================

class TestDeleteDictKey:
    """Test deleting dictionary keys."""
    
    def test_delete_string_key(self):
        """del d["key"]"""
        result = transpile('del d["key"]')
        assert "__py.del" in result and '"key"' in result
    
    def test_delete_variable_key(self):
        """del d[key]"""
        result = transpile("del d[key]")
        assert "__py.del(d, key)" in result


# =============================================================================
# DELETE ATTRIBUTE
# =============================================================================

class TestDeleteAttribute:
    """Test deleting object attributes."""
    
    def test_delete_attribute(self):
        """del obj.attr"""
        result = transpile("del obj.attr")
        assert "delete obj.attr" in result
    
    def test_delete_nested_attribute(self):
        """del obj.inner.attr"""
        result = transpile("del obj.inner.attr")
        assert "delete obj.inner.attr" in result


# =============================================================================
# DELETE IN CONTEXT
# =============================================================================

class TestDeleteInContext:
    """Test delete in various contexts."""
    
    def test_delete_in_if(self):
        """if cond: del items[0]"""
        result = transpile("if cond:\n    del items[0]")
        assert "__py.del" in result
    
    def test_delete_in_for(self):
        """for i in indices: del items[i]"""
        result = transpile("for i in indices:\n    del items[i]")
        assert "__py.del" in result
    
    def test_delete_in_function(self):
        """def cleanup(): del items[0]"""
        result = transpile("def cleanup():\n    del items[0]")
        assert "__py.del" in result


# =============================================================================
# EDGE CASES
# =============================================================================

class TestDeleteEdgeCases:
    """Test edge cases for delete statements."""
    
    def test_delete_negative_index(self):
        """del items[-2]"""
        result = transpile("del items[-2]")
        # Negative literals may be wrapped in parentheses for precedence
        assert "__py.del(items, -2)" in result or "__py.del(items, (-2))" in result
    
    def test_delete_expression_index(self):
        """del items[i + 1]"""
        result = transpile("del items[i + 1]")
        assert "__py.del" in result
