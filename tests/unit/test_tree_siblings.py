"""
Test Phase 7.6: TreeMixin siblings() method.

These tests verify the siblings() method works correctly.
"""

import pytest
from typing import Optional, List
from unittest.mock import Mock, MagicMock, AsyncMock, patch

from pynext.db.relationships.tree import TreeMixin


# =============================================================================
# Mock Model for Testing
# =============================================================================

class MockTreeNode(TreeMixin):
    """Mock tree node for testing siblings."""
    
    _nodes = {}
    
    def __init__(
        self,
        id: int,
        name: str,
        parent_id: Optional[int] = None,
    ):
        self.id = id
        self.name = name
        self.parent_id = parent_id
        self._cached_ancestors = None
        MockTreeNode._nodes[id] = self
    
    @classmethod
    async def get(cls, id: int) -> Optional["MockTreeNode"]:
        return cls._nodes.get(id)
    
    @classmethod
    def select(cls):
        return MockQuery(cls._nodes)
    
    @classmethod
    def clear(cls):
        cls._nodes = {}
    
    async def _get_adapter(self):
        return MockAdapter()
    
    async def _supports_cte(self) -> bool:
        return False


class MockQuery:
    """Mock query for testing."""
    
    def __init__(self, nodes):
        self._nodes = nodes
        self._where_conditions = {}
        self._where_in_conditions = {}
        self._null_field = None
    
    def where(self, **kwargs):
        self._where_conditions.update(kwargs)
        return self
    
    def where_in(self, **kwargs):
        self._where_in_conditions.update(kwargs)
        return self
    
    def where_null(self, field):
        self._null_field = field
        return self
    
    async def count(self):
        return sum(1 for n in self._nodes.values() if self._matches(n))
    
    def _matches(self, node):
        if self._null_field:
            if getattr(node, self._null_field, 'NOT_NULL') is not None:
                return False
        for field, values in self._where_in_conditions.items():
            if getattr(node, field, None) not in values:
                return False
        for field, value in self._where_conditions.items():
            if getattr(node, field, None) != value:
                return False
        return True
    
    def __await__(self):
        async def _await():
            return [n for n in self._nodes.values() if self._matches(n)]
        return _await().__await__()


class MockAdapter:
    supports_cte = False


# =============================================================================
# Test siblings() Basic Behavior
# =============================================================================

class TestSiblingsBasic:
    """Test basic siblings() behavior."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_siblings_empty_for_only_child(self):
        """Only child has no siblings."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        only_child = MockTreeNode(id=2, name="OnlyChild", parent_id=1)
        
        siblings = await only_child.siblings()
        assert siblings == []
    
    @pytest.mark.asyncio
    async def test_siblings_with_one_sibling(self):
        """Node with one sibling."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child1 = MockTreeNode(id=2, name="Child1", parent_id=1)
        child2 = MockTreeNode(id=3, name="Child2", parent_id=1)
        
        siblings = await child1.siblings()
        assert len(siblings) == 1
        assert siblings[0].id == 3
    
    @pytest.mark.asyncio
    async def test_siblings_with_multiple_siblings(self):
        """Node with multiple siblings."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child1 = MockTreeNode(id=2, name="Child1", parent_id=1)
        child2 = MockTreeNode(id=3, name="Child2", parent_id=1)
        child3 = MockTreeNode(id=4, name="Child3", parent_id=1)
        
        siblings = await child1.siblings()
        assert len(siblings) == 2
        sibling_ids = {s.id for s in siblings}
        assert sibling_ids == {3, 4}
    
    @pytest.mark.asyncio
    async def test_siblings_include_self(self):
        """siblings(include_self=True) includes current node."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child1 = MockTreeNode(id=2, name="Child1", parent_id=1)
        child2 = MockTreeNode(id=3, name="Child2", parent_id=1)
        
        siblings = await child1.siblings(include_self=True)
        assert len(siblings) == 2
        sibling_ids = {s.id for s in siblings}
        assert sibling_ids == {2, 3}
    
    @pytest.mark.asyncio
    async def test_siblings_exclude_self_by_default(self):
        """siblings() excludes self by default."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child1 = MockTreeNode(id=2, name="Child1", parent_id=1)
        child2 = MockTreeNode(id=3, name="Child2", parent_id=1)
        
        siblings = await child1.siblings()
        sibling_ids = {s.id for s in siblings}
        assert 2 not in sibling_ids


# =============================================================================
# Test Root-Level Siblings
# =============================================================================

class TestRootSiblings:
    """Test siblings for root-level nodes."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_single_root_no_siblings(self):
        """Single root has no siblings."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        siblings = await root.siblings()
        assert siblings == []
    
    @pytest.mark.asyncio
    async def test_multiple_roots_are_siblings(self):
        """Multiple roots are siblings of each other."""
        root1 = MockTreeNode(id=1, name="Root1", parent_id=None)
        root2 = MockTreeNode(id=2, name="Root2", parent_id=None)
        root3 = MockTreeNode(id=3, name="Root3", parent_id=None)
        
        siblings = await root1.siblings()
        assert len(siblings) == 2
        sibling_ids = {s.id for s in siblings}
        assert sibling_ids == {2, 3}
    
    @pytest.mark.asyncio
    async def test_root_siblings_include_self(self):
        """Root siblings with include_self."""
        root1 = MockTreeNode(id=1, name="Root1", parent_id=None)
        root2 = MockTreeNode(id=2, name="Root2", parent_id=None)
        
        siblings = await root1.siblings(include_self=True)
        assert len(siblings) == 2
        sibling_ids = {s.id for s in siblings}
        assert sibling_ids == {1, 2}


# =============================================================================
# Test Siblings at Different Levels
# =============================================================================

class TestSiblingsDifferentLevels:
    """Test siblings at different tree levels."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_siblings_only_from_same_level(self):
        """Siblings only include nodes with same parent."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child1 = MockTreeNode(id=2, name="Child1", parent_id=1)
        child2 = MockTreeNode(id=3, name="Child2", parent_id=1)
        grandchild1 = MockTreeNode(id=4, name="Grandchild1", parent_id=2)
        grandchild2 = MockTreeNode(id=5, name="Grandchild2", parent_id=2)
        
        # Child1's siblings: only Child2
        siblings1 = await child1.siblings()
        assert len(siblings1) == 1
        assert siblings1[0].id == 3
        
        # Grandchild1's siblings: only Grandchild2
        siblings_gc = await grandchild1.siblings()
        assert len(siblings_gc) == 1
        assert siblings_gc[0].id == 5
    
    @pytest.mark.asyncio
    async def test_cousins_not_siblings(self):
        """Cousins (same level, different parent) are not siblings."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child1 = MockTreeNode(id=2, name="Child1", parent_id=1)
        child2 = MockTreeNode(id=3, name="Child2", parent_id=1)
        gc1 = MockTreeNode(id=4, name="GC1", parent_id=2)  # Under Child1
        gc2 = MockTreeNode(id=5, name="GC2", parent_id=3)  # Under Child2
        
        # GC1 and GC2 are cousins, not siblings
        siblings = await gc1.siblings()
        assert gc2 not in siblings


# =============================================================================
# Test Edge Cases
# =============================================================================

class TestSiblingsEdgeCases:
    """Test edge cases for siblings."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_many_siblings(self):
        """Handle many siblings."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        for i in range(50):
            MockTreeNode(id=i+2, name=f"Child{i}", parent_id=1)
        
        first_child = MockTreeNode._nodes[2]
        siblings = await first_child.siblings()
        assert len(siblings) == 49
    
    @pytest.mark.asyncio
    async def test_isolated_node_no_siblings(self):
        """Isolated node (no parent, no siblings)."""
        isolated = MockTreeNode(id=1, name="Isolated", parent_id=None)
        siblings = await isolated.siblings()
        assert siblings == []
    
    @pytest.mark.asyncio
    async def test_siblings_is_async(self):
        """siblings() is an async method."""
        node = MockTreeNode(id=1, name="Node", parent_id=None)
        coro = node.siblings()
        assert hasattr(coro, '__await__')
        await coro


# =============================================================================
# Test Return Types
# =============================================================================

class TestSiblingsReturnTypes:
    """Test return types of siblings."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_returns_list(self):
        """siblings() returns a list."""
        node = MockTreeNode(id=1, name="Node", parent_id=None)
        result = await node.siblings()
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_returns_same_type_instances(self):
        """siblings() returns instances of the same class."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child1 = MockTreeNode(id=2, name="Child1", parent_id=1)
        child2 = MockTreeNode(id=3, name="Child2", parent_id=1)
        
        siblings = await child1.siblings()
        assert all(isinstance(s, MockTreeNode) for s in siblings)


# =============================================================================
# Test Subtree with Siblings
# =============================================================================

class TestSubtreeWithSiblings:
    """Test interaction between subtree() and siblings."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_subtree_independent_of_siblings(self):
        """Subtree doesn't include sibling branches."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child1 = MockTreeNode(id=2, name="Child1", parent_id=1)
        child2 = MockTreeNode(id=3, name="Child2", parent_id=1)
        gc1 = MockTreeNode(id=4, name="GC1", parent_id=2)
        gc2 = MockTreeNode(id=5, name="GC2", parent_id=3)
        
        # Subtree of Child1 should not include Child2 or GC2
        subtree = await child1.subtree()
        subtree_ids = {n.id for n in subtree}
        
        assert 2 in subtree_ids  # Self
        assert 4 in subtree_ids  # Child of Child1
        assert 3 not in subtree_ids  # Sibling
        assert 5 not in subtree_ids  # Nephew


# =============================================================================
# Test Move Operations
# =============================================================================

class TestMoveOperations:
    """Test moving nodes affects siblings correctly."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_move_changes_siblings(self):
        """Moving a node changes its siblings."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        parent1 = MockTreeNode(id=2, name="Parent1", parent_id=1)
        parent2 = MockTreeNode(id=3, name="Parent2", parent_id=1)
        child = MockTreeNode(id=4, name="Child", parent_id=2)
        
        # Initially Child has no siblings under Parent1
        siblings_before = await child.siblings()
        assert len(siblings_before) == 0
        
        # Move to Parent2 (just update parent_id for this test)
        child.parent_id = 3
        
        # Still no siblings (Parent2 has no other children)
        siblings_after = await child.siblings()
        assert len(siblings_after) == 0

