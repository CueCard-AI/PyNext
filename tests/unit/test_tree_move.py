"""
Test Phase 7.6: Tree Move Operations.

Comprehensive tests for move_to() and make_root() operations.
"""

import pytest
from typing import Optional, List
from unittest.mock import Mock, MagicMock, AsyncMock, patch

from pynext.db.relationships.tree import TreeMixin


# =============================================================================
# Mock Model for Testing
# =============================================================================

class MockTreeNode(TreeMixin):
    """Mock tree node for testing move operations."""
    
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
        self._conditions = {}
        self._in_conditions = {}
    
    def where(self, **kwargs):
        self._conditions.update(kwargs)
        return self
    
    def where_in(self, **kwargs):
        self._in_conditions.update(kwargs)
        return self
    
    def where_null(self, field):
        self._conditions['_null'] = field
        return self
    
    async def count(self):
        return sum(1 for n in self._nodes.values() if self._matches(n))
    
    def _matches(self, node):
        # Check where_in conditions
        for f, vals in self._in_conditions.items():
            if getattr(node, f, None) not in vals:
                return False
        # Check where conditions
        for f, v in self._conditions.items():
            if f.startswith('_'):
                continue
            if getattr(node, f, None) != v:
                return False
        return True
    
    def __await__(self):
        async def _await():
            return [n for n in self._nodes.values() if self._matches(n)]
        return _await().__await__()


# =============================================================================
# Test move_to() Basic Behavior
# =============================================================================

class TestMoveToBasic:
    """Test basic move_to() behavior."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_move_to_new_parent(self):
        """Move node to new parent updates parent_id."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        parent1 = MockTreeNode(id=2, name="Parent1", parent_id=1)
        parent2 = MockTreeNode(id=3, name="Parent2", parent_id=1)
        child = MockTreeNode(id=4, name="Child", parent_id=2)
        
        await child.move_to(parent2)
        
        assert child.parent_id == 3
    
    @pytest.mark.asyncio
    async def test_move_to_none_makes_root(self):
        """Moving to None makes node a root."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        
        await child.move_to(None)
        
        assert child.parent_id is None
        assert child.is_root is True
    
    @pytest.mark.asyncio
    async def test_move_clears_cache(self):
        """Move clears cached ancestors."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        
        # Populate cache
        await child.ancestors()
        assert child._cached_ancestors is not None
        
        # Move
        await child.move_to(None)
        
        assert child._cached_ancestors is None
    
    @pytest.mark.asyncio
    async def test_move_saves_node(self):
        """Move saves the node."""
        saved = []
        
        class SavingNode(MockTreeNode):
            async def save(self):
                saved.append(self.id)
        
        SavingNode._nodes = {}
        root = SavingNode(id=1, name="Root", parent_id=None)
        child = SavingNode(id=2, name="Child", parent_id=1)
        
        await child.move_to(None)
        
        assert 2 in saved


# =============================================================================
# Test move_to() Validation
# =============================================================================

class TestMoveToValidation:
    """Test move_to() validation."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_cannot_move_to_self(self):
        """Cannot move node to itself."""
        node = MockTreeNode(id=1, name="Node", parent_id=None)
        
        with pytest.raises(ValueError, match="Cannot move a node to itself"):
            await node.move_to(node)
    
    @pytest.mark.asyncio
    async def test_cannot_move_to_direct_child(self):
        """Cannot move node to its direct child."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        
        with pytest.raises(ValueError, match="Cannot move a node to one of its descendants"):
            await root.move_to(child)
    
    @pytest.mark.asyncio
    async def test_cannot_move_to_descendant(self):
        """Cannot move node to any descendant."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        grandchild = MockTreeNode(id=3, name="Grandchild", parent_id=2)
        
        with pytest.raises(ValueError, match="Cannot move a node to one of its descendants"):
            await root.move_to(grandchild)
    
    @pytest.mark.asyncio
    async def test_can_move_to_sibling(self):
        """Can move node to sibling (not a descendant)."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child1 = MockTreeNode(id=2, name="Child1", parent_id=1)
        child2 = MockTreeNode(id=3, name="Child2", parent_id=1)
        
        # Should not raise
        await child1.move_to(child2)
        assert child1.parent_id == 3
    
    @pytest.mark.asyncio
    async def test_can_move_to_ancestor(self):
        """Can move node to ancestor (up the tree)."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        grandchild = MockTreeNode(id=3, name="Grandchild", parent_id=2)
        
        # Should not raise - moving up the tree
        await grandchild.move_to(root)
        assert grandchild.parent_id == 1


# =============================================================================
# Test make_root()
# =============================================================================

class TestMakeRoot:
    """Test make_root() method."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_make_root_sets_parent_none(self):
        """make_root sets parent_id to None."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        
        await child.make_root()
        
        assert child.parent_id is None
    
    @pytest.mark.asyncio
    async def test_make_root_updates_is_root(self):
        """make_root updates is_root property."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        
        assert child.is_root is False
        
        await child.make_root()
        
        assert child.is_root is True
    
    @pytest.mark.asyncio
    async def test_make_root_on_root_is_noop(self):
        """make_root on existing root is a no-op."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        
        await root.make_root()
        
        assert root.is_root is True
        assert root.parent_id is None


# =============================================================================
# Test Move Scenarios
# =============================================================================

class TestMoveScenarios:
    """Test various move scenarios."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_move_leaf_to_different_branch(self):
        """Move leaf node to different branch."""
        # Tree: Root > [A > A1, B]
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        a = MockTreeNode(id=2, name="A", parent_id=1)
        b = MockTreeNode(id=3, name="B", parent_id=1)
        a1 = MockTreeNode(id=4, name="A1", parent_id=2)
        
        # Move A1 from under A to under B
        await a1.move_to(b)
        
        assert a1.parent_id == 3
    
    @pytest.mark.asyncio
    async def test_move_subtree_to_different_branch(self):
        """Move node with children to different branch."""
        # Tree: Root > [A > A1, B]
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        a = MockTreeNode(id=2, name="A", parent_id=1)
        b = MockTreeNode(id=3, name="B", parent_id=1)
        a1 = MockTreeNode(id=4, name="A1", parent_id=2)
        
        # Move A (with its child A1) to under B
        await a.move_to(b)
        
        assert a.parent_id == 3
        # A1 still has A as parent
        assert a1.parent_id == 2
    
    @pytest.mark.asyncio
    async def test_multiple_moves(self):
        """Multiple moves in sequence."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        a = MockTreeNode(id=2, name="A", parent_id=1)
        b = MockTreeNode(id=3, name="B", parent_id=1)
        
        # Move A to B
        await a.move_to(b)
        assert a.parent_id == 3
        
        # Move A back to root
        await a.move_to(root)
        assert a.parent_id == 1
        
        # Make A a root
        await a.make_root()
        assert a.parent_id is None


# =============================================================================
# Test Move with Different Tree Structures
# =============================================================================

class TestMoveTreeStructures:
    """Test move with various tree structures."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_move_in_deep_tree(self):
        """Move in deep tree structure."""
        nodes = []
        for i in range(10):
            node = MockTreeNode(
                id=i+1,
                name=f"Level{i}",
                parent_id=i if i > 0 else None
            )
            nodes.append(node)
        
        # Move Level5 to Level1
        await nodes[5].move_to(nodes[1])
        assert nodes[5].parent_id == 2
    
    @pytest.mark.asyncio
    async def test_move_in_wide_tree(self):
        """Move in wide tree structure."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        children = []
        for i in range(10):
            child = MockTreeNode(id=i+2, name=f"Child{i}", parent_id=1)
            children.append(child)
        
        # Move first child under second child
        await children[0].move_to(children[1])
        assert children[0].parent_id == 3
    
    @pytest.mark.asyncio
    async def test_move_between_trees(self):
        """Move node between independent trees."""
        # Tree 1
        root1 = MockTreeNode(id=1, name="Root1", parent_id=None)
        child1 = MockTreeNode(id=2, name="Child1", parent_id=1)
        
        # Tree 2
        root2 = MockTreeNode(id=3, name="Root2", parent_id=None)
        
        # Move child1 to tree 2
        await child1.move_to(root2)
        
        assert child1.parent_id == 3

