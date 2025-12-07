"""
Test Phase 7.6: TreeMixin depth(), root(), is_leaf() methods.

These tests verify the depth-related methods of TreeMixin.
"""

import pytest
from typing import Optional, List
from unittest.mock import Mock, MagicMock, AsyncMock, patch

from pynext.db.relationships.tree import TreeMixin


# =============================================================================
# Mock Model for Testing
# =============================================================================

class MockTreeNode(TreeMixin):
    """Mock tree node for testing."""
    
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
    
    def where(self, **kwargs):
        self._where_conditions.update(kwargs)
        return self
    
    def where_null(self, field):
        self._where_conditions['_null'] = field
        return self
    
    async def count(self):
        count = 0
        for node in self._nodes.values():
            if self._matches(node):
                count += 1
        return count
    
    def _matches(self, node):
        for field, value in self._where_conditions.items():
            if field.startswith('_'):
                continue
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
# Test depth() Method
# =============================================================================

class TestDepth:
    """Test the depth() method."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_depth_root_is_zero(self):
        """Root node has depth 0."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        assert await root.depth() == 0
    
    @pytest.mark.asyncio
    async def test_depth_direct_child(self):
        """Direct child has depth 1."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        assert await child.depth() == 1
    
    @pytest.mark.asyncio
    async def test_depth_grandchild(self):
        """Grandchild has depth 2."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        grandchild = MockTreeNode(id=3, name="Grandchild", parent_id=2)
        assert await grandchild.depth() == 2
    
    @pytest.mark.asyncio
    async def test_depth_deep_hierarchy(self):
        """Deep hierarchy has correct depth."""
        nodes = []
        for i in range(10):
            node = MockTreeNode(
                id=i+1,
                name=f"Level{i}",
                parent_id=i if i > 0 else None
            )
            nodes.append(node)
        
        # Check each level
        for i, node in enumerate(nodes):
            assert await node.depth() == i
    
    @pytest.mark.asyncio
    async def test_depth_is_async(self):
        """depth() is an async method."""
        node = MockTreeNode(id=1, name="Node", parent_id=None)
        coro = node.depth()
        assert hasattr(coro, '__await__')
        await coro


# =============================================================================
# Test root() Method
# =============================================================================

class TestRoot:
    """Test the root() method."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_root_returns_self_for_root(self):
        """Root node returns itself."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        result = await root.root()
        assert result.id == 1
    
    @pytest.mark.asyncio
    async def test_root_from_child(self):
        """Child returns the root."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        result = await child.root()
        assert result.id == 1
    
    @pytest.mark.asyncio
    async def test_root_from_deep_child(self):
        """Deep child returns the root."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        grandchild = MockTreeNode(id=3, name="Grandchild", parent_id=2)
        great_grandchild = MockTreeNode(id=4, name="GreatGrandchild", parent_id=3)
        
        result = await great_grandchild.root()
        assert result.id == 1
        assert result.name == "Root"
    
    @pytest.mark.asyncio
    async def test_root_is_async(self):
        """root() is an async method."""
        node = MockTreeNode(id=1, name="Node", parent_id=None)
        coro = node.root()
        assert hasattr(coro, '__await__')
        await coro
    
    @pytest.mark.asyncio
    async def test_root_from_multiple_trees(self):
        """Each tree has its own root."""
        root1 = MockTreeNode(id=1, name="Root1", parent_id=None)
        child1 = MockTreeNode(id=2, name="Child1", parent_id=1)
        
        root2 = MockTreeNode(id=3, name="Root2", parent_id=None)
        child2 = MockTreeNode(id=4, name="Child2", parent_id=3)
        
        assert (await child1.root()).id == 1
        assert (await child2.root()).id == 3


# =============================================================================
# Test is_leaf() Method
# =============================================================================

class TestIsLeaf:
    """Test the is_leaf() method."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_is_leaf_single_node(self):
        """Single node is a leaf."""
        node = MockTreeNode(id=1, name="Single", parent_id=None)
        assert await node.is_leaf() is True
    
    @pytest.mark.asyncio
    async def test_is_leaf_with_children(self):
        """Node with children is not a leaf."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        assert await root.is_leaf() is False
    
    @pytest.mark.asyncio
    async def test_is_leaf_bottom_node(self):
        """Bottom node is a leaf."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        grandchild = MockTreeNode(id=3, name="Grandchild", parent_id=2)
        
        assert await grandchild.is_leaf() is True
    
    @pytest.mark.asyncio
    async def test_is_leaf_middle_node(self):
        """Middle node is not a leaf."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        grandchild = MockTreeNode(id=3, name="Grandchild", parent_id=2)
        
        assert await child.is_leaf() is False
    
    @pytest.mark.asyncio
    async def test_is_leaf_multiple_leaves(self):
        """Multiple leaves in a tree."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child1 = MockTreeNode(id=2, name="Child1", parent_id=1)
        child2 = MockTreeNode(id=3, name="Child2", parent_id=1)
        
        assert await child1.is_leaf() is True
        assert await child2.is_leaf() is True
    
    @pytest.mark.asyncio
    async def test_is_leaf_is_async(self):
        """is_leaf() is an async method."""
        node = MockTreeNode(id=1, name="Node", parent_id=None)
        coro = node.is_leaf()
        assert hasattr(coro, '__await__')
        await coro


# =============================================================================
# Test parent() Method
# =============================================================================

class TestParent:
    """Test the parent() method."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_parent_none_for_root(self):
        """Root has no parent."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        parent = await root.parent()
        assert parent is None
    
    @pytest.mark.asyncio
    async def test_parent_returns_parent(self):
        """Child returns its parent."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        
        parent = await child.parent()
        assert parent is not None
        assert parent.id == 1
    
    @pytest.mark.asyncio
    async def test_parent_deep_hierarchy(self):
        """Each node returns correct parent."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        grandchild = MockTreeNode(id=3, name="Grandchild", parent_id=2)
        
        assert (await grandchild.parent()).id == 2
        assert (await child.parent()).id == 1
        assert (await root.parent()) is None
    
    @pytest.mark.asyncio
    async def test_parent_is_async(self):
        """parent() is an async method."""
        node = MockTreeNode(id=1, name="Node", parent_id=None)
        coro = node.parent()
        assert hasattr(coro, '__await__')
        await coro


# =============================================================================
# Test Combined Behavior
# =============================================================================

class TestCombinedDepthMethods:
    """Test combined behavior of depth-related methods."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_root_depth_is_zero(self):
        """Root found via root() has depth 0."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        
        found_root = await child.root()
        assert await found_root.depth() == 0
    
    @pytest.mark.asyncio
    async def test_leaf_has_no_children(self):
        """is_leaf() true means no children()."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        leaf = MockTreeNode(id=2, name="Leaf", parent_id=1)
        
        assert await leaf.is_leaf() is True
        children = await leaf.children()
        assert len(children) == 0
    
    @pytest.mark.asyncio
    async def test_non_leaf_has_children(self):
        """is_leaf() false means has children()."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        
        assert await root.is_leaf() is False
        children = await root.children()
        assert len(children) == 1


# =============================================================================
# Test Edge Cases
# =============================================================================

class TestDepthEdgeCases:
    """Test edge cases for depth methods."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_depth_orphan_node(self):
        """Orphan node (missing parent) has depth 0."""
        orphan = MockTreeNode(id=1, name="Orphan", parent_id=999)
        # ancestors() returns [] for missing parent
        # So depth = 0
        depth = await orphan.depth()
        assert depth == 0
    
    @pytest.mark.asyncio
    async def test_root_orphan_node(self):
        """Orphan node returns itself as root."""
        orphan = MockTreeNode(id=1, name="Orphan", parent_id=999)
        result = await orphan.root()
        assert result.id == 1
    
    @pytest.mark.asyncio
    async def test_very_deep_depth(self):
        """Handle very deep tree depth."""
        nodes = []
        for i in range(50):
            node = MockTreeNode(
                id=i+1,
                name=f"Level{i}",
                parent_id=i if i > 0 else None
            )
            nodes.append(node)
        
        deepest = nodes[-1]
        assert await deepest.depth() == 49
    
    @pytest.mark.asyncio
    async def test_multiple_roots(self):
        """Handle multiple root nodes."""
        root1 = MockTreeNode(id=1, name="Root1", parent_id=None)
        root2 = MockTreeNode(id=2, name="Root2", parent_id=None)
        
        assert await root1.depth() == 0
        assert await root2.depth() == 0
        assert (await root1.root()).id == 1
        assert (await root2.root()).id == 2

