"""
Test Phase 7.6: Tree Edge Cases.

These tests verify TreeMixin handles edge cases correctly:
- Cycles (prevented by design)
- Orphans
- Deep trees
- Wide trees
- Move operations
"""

import pytest
from typing import Optional, List
from unittest.mock import Mock, MagicMock, AsyncMock, patch

from pynext.db.relationships.tree import TreeMixin


# =============================================================================
# Mock Model for Testing
# =============================================================================

class MockTreeNode(TreeMixin):
    """Mock tree node for testing edge cases."""
    
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
    
    async def save(self):
        """Mock save."""
        pass
    
    async def _supports_cte(self) -> bool:
        return False


class MockQuery:
    """Mock query for testing."""
    
    def __init__(self, nodes):
        self._nodes = nodes
        self._where_conditions = {}
        self._null_field = None
    
    def where(self, **kwargs):
        self._where_conditions.update(kwargs)
        return self
    
    def where_in(self, **kwargs):
        self._where_conditions['_in'] = kwargs
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
        if '_in' in self._where_conditions:
            for field, values in self._where_conditions['_in'].items():
                if getattr(node, field, None) not in values:
                    return False
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


# =============================================================================
# Test Orphan Nodes
# =============================================================================

class TestOrphanNodes:
    """Test handling of orphan nodes (missing parent)."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_orphan_ancestors_empty(self):
        """Orphan node has no ancestors."""
        orphan = MockTreeNode(id=1, name="Orphan", parent_id=999)
        
        ancestors = await orphan.ancestors()
        
        assert ancestors == []
    
    @pytest.mark.asyncio
    async def test_orphan_depth_zero(self):
        """Orphan node has depth 0."""
        orphan = MockTreeNode(id=1, name="Orphan", parent_id=999)
        
        depth = await orphan.depth()
        
        assert depth == 0
    
    @pytest.mark.asyncio
    async def test_orphan_root_is_self(self):
        """Orphan's root is itself."""
        orphan = MockTreeNode(id=1, name="Orphan", parent_id=999)
        
        root = await orphan.root()
        
        assert root.id == 1
    
    @pytest.mark.asyncio
    async def test_orphan_path_is_just_name(self):
        """Orphan's path is just its name."""
        orphan = MockTreeNode(id=1, name="Orphan", parent_id=999)
        await orphan.ancestors()  # Populate cache
        
        assert orphan.path == "Orphan"
    
    @pytest.mark.asyncio
    async def test_orphan_is_not_root(self):
        """Orphan is not root (has parent_id)."""
        orphan = MockTreeNode(id=1, name="Orphan", parent_id=999)
        
        assert orphan.is_root is False


# =============================================================================
# Test Deep Trees
# =============================================================================

class TestDeepTrees:
    """Test handling of very deep trees."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_deep_tree_100_levels(self):
        """Handle tree with 100 levels."""
        nodes = []
        for i in range(100):
            node = MockTreeNode(
                id=i+1,
                name=f"Level{i}",
                parent_id=i if i > 0 else None
            )
            nodes.append(node)
        
        # Test deepest node
        deepest = nodes[-1]
        
        ancestors = await deepest.ancestors()
        assert len(ancestors) == 99
        
        depth = await deepest.depth()
        assert depth == 99
        
        root = await deepest.root()
        assert root.id == 1
    
    @pytest.mark.asyncio
    async def test_deep_tree_path(self):
        """Path for deep tree."""
        nodes = []
        for i in range(10):
            node = MockTreeNode(
                id=i+1,
                name=f"L{i}",
                parent_id=i if i > 0 else None
            )
            nodes.append(node)
        
        deepest = nodes[-1]
        await deepest.ancestors()
        
        # Path should have all levels
        path_parts = deepest.path.split("/")
        assert len(path_parts) == 10
    
    @pytest.mark.asyncio
    async def test_deep_tree_descendants(self):
        """Descendants from root of deep tree."""
        nodes = []
        for i in range(50):
            node = MockTreeNode(
                id=i+1,
                name=f"Level{i}",
                parent_id=i if i > 0 else None
            )
            nodes.append(node)
        
        root = nodes[0]
        descendants = await root.descendants()
        
        assert len(descendants) == 49


# =============================================================================
# Test Wide Trees
# =============================================================================

class TestWideTrees:
    """Test handling of very wide trees."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_wide_tree_100_children(self):
        """Handle parent with 100 children."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        
        for i in range(100):
            MockTreeNode(id=i+2, name=f"Child{i}", parent_id=1)
        
        descendants = await root.descendants()
        assert len(descendants) == 100
    
    @pytest.mark.asyncio
    async def test_wide_tree_siblings(self):
        """Siblings in wide tree."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        
        for i in range(50):
            MockTreeNode(id=i+2, name=f"Child{i}", parent_id=1)
        
        first_child = MockTreeNode._nodes[2]
        siblings = await first_child.siblings()
        
        assert len(siblings) == 49
    
    @pytest.mark.asyncio
    async def test_wide_tree_is_leaf(self):
        """All children are leaves in flat tree."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        
        for i in range(10):
            MockTreeNode(id=i+2, name=f"Child{i}", parent_id=1)
        
        # All children should be leaves
        for i in range(10):
            child = MockTreeNode._nodes[i+2]
            assert await child.is_leaf() is True


# =============================================================================
# Test Move Operations
# =============================================================================

class TestMoveOperations:
    """Test move_to and make_root operations."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_move_to_new_parent(self):
        """Move node to new parent."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        parent1 = MockTreeNode(id=2, name="Parent1", parent_id=1)
        parent2 = MockTreeNode(id=3, name="Parent2", parent_id=1)
        child = MockTreeNode(id=4, name="Child", parent_id=2)
        
        await child.move_to(parent2)
        
        assert child.parent_id == 3
    
    @pytest.mark.asyncio
    async def test_move_to_clears_cache(self):
        """Move clears cached ancestors."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        parent = MockTreeNode(id=2, name="Parent", parent_id=1)
        child = MockTreeNode(id=3, name="Child", parent_id=2)
        
        # Cache ancestors
        await child.ancestors()
        assert child._cached_ancestors is not None
        
        # Move
        await child.move_to(root)
        
        assert child._cached_ancestors is None
    
    @pytest.mark.asyncio
    async def test_move_to_self_raises(self):
        """Cannot move to self."""
        node = MockTreeNode(id=1, name="Node", parent_id=None)
        
        with pytest.raises(ValueError, match="Cannot move a node to itself"):
            await node.move_to(node)
    
    @pytest.mark.asyncio
    async def test_move_to_descendant_raises(self):
        """Cannot move to a descendant."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        grandchild = MockTreeNode(id=3, name="Grandchild", parent_id=2)
        
        with pytest.raises(ValueError, match="Cannot move a node to one of its descendants"):
            await root.move_to(grandchild)
    
    @pytest.mark.asyncio
    async def test_make_root(self):
        """Make node a root."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        
        assert child.is_root is False
        
        await child.make_root()
        
        assert child.is_root is True
        assert child.parent_id is None
    
    @pytest.mark.asyncio
    async def test_move_to_none_makes_root(self):
        """Moving to None makes node a root."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        
        await child.move_to(None)
        
        assert child.is_root is True


# =============================================================================
# Test Multiple Trees
# =============================================================================

class TestMultipleTrees:
    """Test handling of multiple independent trees."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_independent_trees(self):
        """Multiple trees are independent."""
        # Tree 1
        root1 = MockTreeNode(id=1, name="Root1", parent_id=None)
        child1 = MockTreeNode(id=2, name="Child1", parent_id=1)
        
        # Tree 2
        root2 = MockTreeNode(id=3, name="Root2", parent_id=None)
        child2 = MockTreeNode(id=4, name="Child2", parent_id=3)
        
        # Verify independence
        assert (await child1.root()).id == 1
        assert (await child2.root()).id == 3
        
        assert len(await root1.descendants()) == 1
        assert len(await root2.descendants()) == 1
    
    @pytest.mark.asyncio
    async def test_multiple_roots(self):
        """Multiple root nodes are siblings."""
        root1 = MockTreeNode(id=1, name="Root1", parent_id=None)
        root2 = MockTreeNode(id=2, name="Root2", parent_id=None)
        root3 = MockTreeNode(id=3, name="Root3", parent_id=None)
        
        siblings = await root1.siblings()
        
        assert len(siblings) == 2


# =============================================================================
# Test Special ID Values
# =============================================================================

class TestSpecialIdValues:
    """Test handling of special ID values."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_id_zero(self):
        """Handle ID = 0."""
        root = MockTreeNode(id=0, name="Root", parent_id=None)
        child = MockTreeNode(id=1, name="Child", parent_id=0)
        
        assert root.is_root is True
        assert (await child.parent()).id == 0
    
    @pytest.mark.asyncio
    async def test_large_ids(self):
        """Handle large IDs."""
        root = MockTreeNode(id=999999999, name="Root", parent_id=None)
        child = MockTreeNode(id=999999998, name="Child", parent_id=999999999)
        
        ancestors = await child.ancestors()
        assert len(ancestors) == 1
        assert ancestors[0].id == 999999999


# =============================================================================
# Test Unicode Names
# =============================================================================

class TestUnicodeNames:
    """Test handling of unicode in names."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_unicode_in_path(self):
        """Unicode names in path."""
        root = MockTreeNode(id=1, name="日本語", parent_id=None)
        child = MockTreeNode(id=2, name="カテゴリ", parent_id=1)
        
        await child.ancestors()
        
        assert child.path == "日本語/カテゴリ"
    
    @pytest.mark.asyncio
    async def test_emoji_in_name(self):
        """Emoji in names."""
        root = MockTreeNode(id=1, name="📁 Root", parent_id=None)
        child = MockTreeNode(id=2, name="📂 Child", parent_id=1)
        
        await child.ancestors()
        
        assert "📁" in child.path
        assert "📂" in child.path

