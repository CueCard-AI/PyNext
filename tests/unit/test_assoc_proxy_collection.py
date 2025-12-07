"""
Tests for ProxyCollection operations.

Tests cover:
- Iteration
- Indexing and slicing
- Length and boolean conversion
- Contains check
- Copy and to_list
- Comparison
- Concatenation
"""

import pytest
from typing import List, Optional
from dataclasses import dataclass, field


# =============================================================================
# Mock Classes
# =============================================================================

@dataclass
class MockItem:
    """Simple mock item."""
    id: int
    name: str
    value: int = 0
    active: bool = True


class MockOwner:
    """Mock owner with items collection."""
    _fields = {}
    __table_name__ = "owners"
    
    def __init__(self, items: List[MockItem] = None):
        self._items = items or []
    
    @property
    def items(self):
        return self._items
    
    @items.setter
    def items(self, value):
        self._items = value


from pynext.db.relationships.association_proxy import (
    association_proxy,
    ProxyCollection,
)


# =============================================================================
# Helper to Create Proxy Owner
# =============================================================================

def create_owner_with_proxy(items: List[MockItem] = None):
    """Create an owner instance with proxy configured."""
    
    class OwnerWithProxy(MockOwner):
        names = association_proxy("items", "name")
        values = association_proxy("items", "value")
        actives = association_proxy("items", "active")
    
    return OwnerWithProxy(items)


# =============================================================================
# Test: Iteration
# =============================================================================

class TestProxyIteration:
    """Test iteration over ProxyCollection."""
    
    def test_iterate_empty(self):
        """Iterate over empty collection."""
        owner = create_owner_with_proxy([])
        result = list(owner.names)
        assert result == []
    
    def test_iterate_single_item(self):
        """Iterate over single item."""
        owner = create_owner_with_proxy([MockItem(1, "Alice")])
        result = list(owner.names)
        assert result == ["Alice"]
    
    def test_iterate_multiple_items(self):
        """Iterate over multiple items."""
        items = [
            MockItem(1, "Alice"),
            MockItem(2, "Bob"),
            MockItem(3, "Charlie"),
        ]
        owner = create_owner_with_proxy(items)
        result = list(owner.names)
        assert result == ["Alice", "Bob", "Charlie"]
    
    def test_iterate_preserves_order(self):
        """Iteration preserves source order."""
        items = [MockItem(i, f"Item{i}") for i in range(10)]
        owner = create_owner_with_proxy(items)
        result = list(owner.names)
        expected = [f"Item{i}" for i in range(10)]
        assert result == expected
    
    def test_iterate_with_for_loop(self):
        """for loop works correctly."""
        items = [MockItem(1, "A"), MockItem(2, "B")]
        owner = create_owner_with_proxy(items)
        
        collected = []
        for name in owner.names:
            collected.append(name)
        
        assert collected == ["A", "B"]
    
    def test_iterate_twice(self):
        """Can iterate multiple times."""
        items = [MockItem(1, "Test")]
        owner = create_owner_with_proxy(items)
        
        first = list(owner.names)
        second = list(owner.names)
        
        assert first == second == ["Test"]
    
    def test_iterate_different_attrs(self):
        """Different proxies iterate independently."""
        items = [MockItem(1, "A", 10), MockItem(2, "B", 20)]
        owner = create_owner_with_proxy(items)
        
        names = list(owner.names)
        values = list(owner.values)
        
        assert names == ["A", "B"]
        assert values == [10, 20]


# =============================================================================
# Test: Indexing
# =============================================================================

class TestProxyIndexing:
    """Test indexing and slicing."""
    
    def test_index_first(self):
        """Get first item."""
        items = [MockItem(1, "A"), MockItem(2, "B"), MockItem(3, "C")]
        owner = create_owner_with_proxy(items)
        assert owner.names[0] == "A"
    
    def test_index_last(self):
        """Get last item."""
        items = [MockItem(1, "A"), MockItem(2, "B"), MockItem(3, "C")]
        owner = create_owner_with_proxy(items)
        assert owner.names[2] == "C"
    
    def test_index_negative(self):
        """Negative indexing works."""
        items = [MockItem(1, "A"), MockItem(2, "B"), MockItem(3, "C")]
        owner = create_owner_with_proxy(items)
        assert owner.names[-1] == "C"
        assert owner.names[-2] == "B"
        assert owner.names[-3] == "A"
    
    def test_index_out_of_range(self):
        """Index out of range raises IndexError."""
        items = [MockItem(1, "A")]
        owner = create_owner_with_proxy(items)
        
        with pytest.raises(IndexError):
            _ = owner.names[10]
    
    def test_slice_all(self):
        """Slice all items."""
        items = [MockItem(1, "A"), MockItem(2, "B"), MockItem(3, "C")]
        owner = create_owner_with_proxy(items)
        assert owner.names[:] == ["A", "B", "C"]
    
    def test_slice_first_two(self):
        """Slice first two items."""
        items = [MockItem(1, "A"), MockItem(2, "B"), MockItem(3, "C")]
        owner = create_owner_with_proxy(items)
        assert owner.names[:2] == ["A", "B"]
    
    def test_slice_last_two(self):
        """Slice last two items."""
        items = [MockItem(1, "A"), MockItem(2, "B"), MockItem(3, "C")]
        owner = create_owner_with_proxy(items)
        assert owner.names[-2:] == ["B", "C"]
    
    def test_slice_middle(self):
        """Slice middle items."""
        items = [MockItem(i, chr(65+i)) for i in range(5)]
        owner = create_owner_with_proxy(items)
        assert owner.names[1:4] == ["B", "C", "D"]
    
    def test_slice_with_step(self):
        """Slice with step."""
        items = [MockItem(i, chr(65+i)) for i in range(5)]
        owner = create_owner_with_proxy(items)
        assert owner.names[::2] == ["A", "C", "E"]
    
    def test_slice_empty_range(self):
        """Slice with empty range returns empty list."""
        items = [MockItem(1, "A")]
        owner = create_owner_with_proxy(items)
        assert owner.names[5:10] == []


# =============================================================================
# Test: Length
# =============================================================================

class TestProxyLength:
    """Test len() on ProxyCollection."""
    
    def test_len_empty(self):
        """Empty collection has length 0."""
        owner = create_owner_with_proxy([])
        assert len(owner.names) == 0
    
    def test_len_one(self):
        """Single item has length 1."""
        owner = create_owner_with_proxy([MockItem(1, "A")])
        assert len(owner.names) == 1
    
    def test_len_multiple(self):
        """Multiple items have correct length."""
        items = [MockItem(i, f"Item{i}") for i in range(5)]
        owner = create_owner_with_proxy(items)
        assert len(owner.names) == 5
    
    def test_len_large(self):
        """Large collection has correct length."""
        items = [MockItem(i, f"Item{i}") for i in range(100)]
        owner = create_owner_with_proxy(items)
        assert len(owner.names) == 100
    
    def test_len_reflects_changes(self):
        """Length reflects source changes."""
        owner = create_owner_with_proxy([])
        assert len(owner.names) == 0
        
        owner._items.append(MockItem(1, "A"))
        assert len(owner.names) == 1
        
        owner._items.append(MockItem(2, "B"))
        assert len(owner.names) == 2


# =============================================================================
# Test: Boolean Conversion
# =============================================================================

class TestProxyBoolean:
    """Test bool() on ProxyCollection."""
    
    def test_empty_is_falsy(self):
        """Empty collection is falsy."""
        owner = create_owner_with_proxy([])
        assert not owner.names
        assert bool(owner.names) is False
    
    def test_non_empty_is_truthy(self):
        """Non-empty collection is truthy."""
        owner = create_owner_with_proxy([MockItem(1, "A")])
        assert owner.names
        assert bool(owner.names) is True
    
    def test_in_if_statement_empty(self):
        """Empty collection works in if statement."""
        owner = create_owner_with_proxy([])
        if owner.names:
            pytest.fail("Should not enter if block")
    
    def test_in_if_statement_non_empty(self):
        """Non-empty collection works in if statement."""
        owner = create_owner_with_proxy([MockItem(1, "A")])
        entered = False
        if owner.names:
            entered = True
        assert entered


# =============================================================================
# Test: Contains
# =============================================================================

class TestProxyContains:
    """Test 'in' operator on ProxyCollection."""
    
    def test_contains_true(self):
        """in returns True for existing item."""
        items = [MockItem(1, "Alice"), MockItem(2, "Bob")]
        owner = create_owner_with_proxy(items)
        assert "Alice" in owner.names
        assert "Bob" in owner.names
    
    def test_contains_false(self):
        """in returns False for non-existing item."""
        items = [MockItem(1, "Alice")]
        owner = create_owner_with_proxy(items)
        assert "Bob" not in owner.names
    
    def test_contains_empty(self):
        """in returns False for empty collection."""
        owner = create_owner_with_proxy([])
        assert "anything" not in owner.names
    
    def test_contains_integer(self):
        """in works for integer values."""
        items = [MockItem(1, "A", 10), MockItem(2, "B", 20)]
        owner = create_owner_with_proxy(items)
        assert 10 in owner.values
        assert 30 not in owner.values
    
    def test_contains_boolean(self):
        """in works for boolean values."""
        items = [MockItem(1, "A", active=True)]
        owner = create_owner_with_proxy(items)
        assert True in owner.actives
        assert False not in owner.actives


# =============================================================================
# Test: Equality
# =============================================================================

class TestProxyEquality:
    """Test equality comparison."""
    
    def test_equals_list(self):
        """ProxyCollection equals equivalent list."""
        items = [MockItem(1, "A"), MockItem(2, "B")]
        owner = create_owner_with_proxy(items)
        assert owner.names == ["A", "B"]
    
    def test_not_equals_different_list(self):
        """ProxyCollection not equals different list."""
        items = [MockItem(1, "A")]
        owner = create_owner_with_proxy(items)
        assert owner.names != ["X"]
    
    def test_equals_empty_list(self):
        """Empty collection equals empty list."""
        owner = create_owner_with_proxy([])
        assert owner.names == []
    
    def test_equals_another_proxy(self):
        """Two proxies with same values are equal."""
        items = [MockItem(1, "A")]
        owner1 = create_owner_with_proxy(items)
        owner2 = create_owner_with_proxy([MockItem(2, "A")])  # Same name
        assert owner1.names == owner2.names


# =============================================================================
# Test: Copy and to_list
# =============================================================================

class TestProxyCopy:
    """Test copy() and to_list() methods."""
    
    def test_copy_returns_list(self):
        """copy() returns a regular list."""
        items = [MockItem(1, "A")]
        owner = create_owner_with_proxy(items)
        result = owner.names.copy()
        assert isinstance(result, list)
        assert result == ["A"]
    
    def test_copy_is_independent(self):
        """copy() returns independent list."""
        items = [MockItem(1, "A")]
        owner = create_owner_with_proxy(items)
        copied = owner.names.copy()
        
        # Modify source
        owner._items.append(MockItem(2, "B"))
        
        # Copy should not change
        assert copied == ["A"]
    
    def test_to_list_returns_list(self):
        """to_list() returns regular list."""
        items = [MockItem(1, "A"), MockItem(2, "B")]
        owner = create_owner_with_proxy(items)
        result = owner.names.to_list()
        assert isinstance(result, list)
        assert result == ["A", "B"]
    
    def test_to_list_empty(self):
        """to_list() on empty returns empty list."""
        owner = create_owner_with_proxy([])
        assert owner.names.to_list() == []


# =============================================================================
# Test: Concatenation
# =============================================================================

class TestProxyConcatenation:
    """Test + operator."""
    
    def test_add_list(self):
        """proxy + list works."""
        items = [MockItem(1, "A")]
        owner = create_owner_with_proxy(items)
        result = owner.names + ["B", "C"]
        assert result == ["A", "B", "C"]
    
    def test_radd_list(self):
        """list + proxy works."""
        items = [MockItem(1, "B")]
        owner = create_owner_with_proxy(items)
        result = ["A"] + owner.names
        assert result == ["A", "B"]
    
    def test_add_empty(self):
        """proxy + empty list."""
        items = [MockItem(1, "A")]
        owner = create_owner_with_proxy(items)
        result = owner.names + []
        assert result == ["A"]


# =============================================================================
# Test: count() and index()
# =============================================================================

class TestProxyCountIndex:
    """Test count() and index() methods."""
    
    def test_count_existing(self):
        """count() returns count of matching items."""
        items = [
            MockItem(1, "A"),
            MockItem(2, "B"),
            MockItem(3, "A"),  # Duplicate
        ]
        owner = create_owner_with_proxy(items)
        assert owner.names.count("A") == 2
        assert owner.names.count("B") == 1
    
    def test_count_non_existing(self):
        """count() returns 0 for non-existing."""
        items = [MockItem(1, "A")]
        owner = create_owner_with_proxy(items)
        assert owner.names.count("X") == 0
    
    def test_index_found(self):
        """index() returns correct index."""
        items = [MockItem(1, "A"), MockItem(2, "B"), MockItem(3, "C")]
        owner = create_owner_with_proxy(items)
        assert owner.names.index("A") == 0
        assert owner.names.index("B") == 1
        assert owner.names.index("C") == 2
    
    def test_index_not_found(self):
        """index() raises ValueError for missing item."""
        items = [MockItem(1, "A")]
        owner = create_owner_with_proxy(items)
        
        with pytest.raises(ValueError):
            owner.names.index("X")
    
    def test_index_with_start(self):
        """index() respects start parameter."""
        items = [
            MockItem(1, "A"),
            MockItem(2, "A"),  # Second A
        ]
        owner = create_owner_with_proxy(items)
        assert owner.names.index("A", 1) == 1


# =============================================================================
# Test: repr and str
# =============================================================================

class TestProxyReprStr:
    """Test __repr__ and __str__."""
    
    def test_repr_format(self):
        """__repr__ has expected format."""
        items = [MockItem(1, "A")]
        owner = create_owner_with_proxy(items)
        result = repr(owner.names)
        assert "ProxyCollection" in result
        assert "items.name" in result
    
    def test_str_shows_values(self):
        """__str__ shows the values."""
        items = [MockItem(1, "A"), MockItem(2, "B")]
        owner = create_owner_with_proxy(items)
        result = str(owner.names)
        assert result == "['A', 'B']"


# =============================================================================
# Test: Large Collections
# =============================================================================

class TestLargeCollections:
    """Test behavior with large collections."""
    
    def test_1000_items(self):
        """Handle 1000 items."""
        items = [MockItem(i, f"Item{i}") for i in range(1000)]
        owner = create_owner_with_proxy(items)
        
        result = list(owner.names)
        assert len(result) == 1000
        assert result[0] == "Item0"
        assert result[999] == "Item999"
    
    def test_iteration_performance(self):
        """Iteration should be efficient."""
        items = [MockItem(i, f"Item{i}") for i in range(1000)]
        owner = create_owner_with_proxy(items)
        
        # Should complete quickly
        count = 0
        for _ in owner.names:
            count += 1
        
        assert count == 1000


# =============================================================================
# Test: Edge Cases
# =============================================================================

class TestCollectionEdgeCases:
    """Edge cases for collection operations."""
    
    def test_none_values_skipped(self):
        """None values in path are skipped."""
        @dataclass
        class ItemWithOptional:
            id: int
            child: Optional[MockItem] = None
        
        class OwnerWithNested(MockOwner):
            nested_names = association_proxy("items", "child.name")
            
            def __init__(self, items):
                self._items = items
            
            @property
            def items(self):
                return self._items
        
        items = [
            ItemWithOptional(1, MockItem(10, "A")),
            ItemWithOptional(2, None),  # None child
            ItemWithOptional(3, MockItem(30, "C")),
        ]
        owner = OwnerWithNested(items)
        
        result = list(owner.nested_names)
        assert result == ["A", "C"]  # Skips None
    
    def test_single_item_operations(self):
        """All operations work with single item."""
        owner = create_owner_with_proxy([MockItem(1, "Only")])
        
        assert len(owner.names) == 1
        assert owner.names[0] == "Only"
        assert owner.names[-1] == "Only"
        assert "Only" in owner.names
        assert list(owner.names) == ["Only"]
        assert owner.names == ["Only"]
    
    def test_modify_during_iteration(self):
        """Handles modification during iteration (creates new list)."""
        owner = create_owner_with_proxy([
            MockItem(1, "A"),
            MockItem(2, "B"),
        ])
        
        # Each iteration gets fresh values
        collected = []
        for i, name in enumerate(owner.names):
            collected.append(name)
            if i == 0:
                owner._items.append(MockItem(3, "C"))
        
        # First iteration only saw 2 items (list was created at start)
        assert collected == ["A", "B"]

