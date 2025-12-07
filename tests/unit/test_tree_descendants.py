"""
Test Phase 7.6: TreeMixin descendants() method.

These tests verify the descendants() method works correctly with both
CTE (PostgreSQL) and app-level fallback strategies.
"""

import pytest
from typing import Optional, List
from unittest.mock import Mock, MagicMock, AsyncMock, patch

from pynext.db.relationships.tree import TreeMixin


# =============================================================================
# Mock Model for Testing
# =============================================================================

class MockTreeNode(TreeMixin):
    """Mock tree node for testing descendants."""
    
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
    
    def where_in(self, **kwargs):
        self._where_conditions['_in'] = kwargs
        return self
    
    def where_null(self, field):
        self._where_conditions['_null'] = field
        return self
    
    async def count(self):
        return sum(1 for n in self._nodes.values() 
                   if self._matches(n))
    
    def _matches(self, node):
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


class MockAdapter:
    supports_cte = False
    
    async def fetch(self, query: str, *params) -> List[dict]:
        return []


# =============================================================================
# Test descendants() Basic Behavior
# =============================================================================

class TestDescendantsBasic:
    """Test basic descendants() behavior."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_descendants_empty_for_leaf(self):
        """Leaf node has no descendants."""
        leaf = MockTreeNode(id=1, name="Leaf", parent_id=None)
        descendants = await leaf.descendants()
        assert descendants == []
    
    @pytest.mark.asyncio
    async def test_descendants_single_child(self):
        """Node with one child."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        
        descendants = await root.descendants()
        assert len(descendants) == 1
        assert descendants[0].id == 2
    
    @pytest.mark.asyncio
    async def test_descendants_multiple_levels(self):
        """Node with multiple levels of descendants."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        grandchild = MockTreeNode(id=3, name="Grandchild", parent_id=2)
        
        descendants = await root.descendants()
        assert len(descendants) == 2
        # BFS order: children first, then grandchildren
        assert 2 in [d.id for d in descendants]
        assert 3 in [d.id for d in descendants]
    
    @pytest.mark.asyncio
    async def test_descendants_include_self(self):
        """descendants(include_self=True) includes current node."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        
        descendants = await root.descendants(include_self=True)
        assert len(descendants) == 2
        assert descendants[0].id == 1  # Self first
    
    @pytest.mark.asyncio
    async def test_descendants_include_self_for_leaf(self):
        """descendants(include_self=True) on leaf returns just self."""
        leaf = MockTreeNode(id=1, name="Leaf", parent_id=None)
        descendants = await leaf.descendants(include_self=True)
        assert len(descendants) == 1
        assert descendants[0].id == 1


# =============================================================================
# Test App-Level Traversal
# =============================================================================

class TestDescendantsAppLevel:
    """Test app-level descendant traversal."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_app_level_single_child(self):
        """App-level traversal with single child."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        
        descendants = await root.descendants(use_cte=False)
        assert len(descendants) == 1
        assert descendants[0].name == "Child"
    
    @pytest.mark.asyncio
    async def test_app_level_wide_tree(self):
        """App-level traversal with wide tree."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        for i in range(5):
            MockTreeNode(id=i+2, name=f"Child{i}", parent_id=1)
        
        descendants = await root.descendants(use_cte=False)
        assert len(descendants) == 5
    
    @pytest.mark.asyncio
    async def test_app_level_deep_tree(self):
        """App-level traversal with deep tree."""
        nodes = []
        for i in range(10):
            node = MockTreeNode(
                id=i+1,
                name=f"Level{i}",
                parent_id=i if i > 0 else None
            )
            nodes.append(node)
        
        root = nodes[0]
        descendants = await root.descendants(use_cte=False)
        
        assert len(descendants) == 9
    
    @pytest.mark.asyncio
    async def test_app_level_mixed_tree(self):
        """App-level traversal with mixed tree (wide and deep)."""
        # Root
        #   ├── A
        #   │   └── A1
        #   ├── B
        #   │   └── B1
        #   └── C
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        a = MockTreeNode(id=2, name="A", parent_id=1)
        b = MockTreeNode(id=3, name="B", parent_id=1)
        c = MockTreeNode(id=4, name="C", parent_id=1)
        a1 = MockTreeNode(id=5, name="A1", parent_id=2)
        b1 = MockTreeNode(id=6, name="B1", parent_id=3)
        
        descendants = await root.descendants(use_cte=False)
        
        assert len(descendants) == 5
        # All nodes should be present
        descendant_ids = {d.id for d in descendants}
        assert descendant_ids == {2, 3, 4, 5, 6}


# =============================================================================
# Test max_depth Parameter
# =============================================================================

class TestDescendantsMaxDepth:
    """Test max_depth parameter."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_max_depth_1(self):
        """max_depth=1 returns only direct children."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        grandchild = MockTreeNode(id=3, name="Grandchild", parent_id=2)
        
        descendants = await root.descendants(max_depth=1)
        assert len(descendants) == 1
        assert descendants[0].id == 2
    
    @pytest.mark.asyncio
    async def test_max_depth_2(self):
        """max_depth=2 returns children and grandchildren."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        grandchild = MockTreeNode(id=3, name="Grandchild", parent_id=2)
        great_grandchild = MockTreeNode(id=4, name="GreatGrandchild", parent_id=3)
        
        descendants = await root.descendants(max_depth=2)
        assert len(descendants) == 2
        descendant_ids = {d.id for d in descendants}
        assert descendant_ids == {2, 3}
    
    @pytest.mark.asyncio
    async def test_max_depth_none_unlimited(self):
        """max_depth=None returns all descendants."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        grandchild = MockTreeNode(id=3, name="Grandchild", parent_id=2)
        great_grandchild = MockTreeNode(id=4, name="GreatGrandchild", parent_id=3)
        
        descendants = await root.descendants(max_depth=None)
        assert len(descendants) == 3
    
    @pytest.mark.asyncio
    async def test_max_depth_0(self):
        """max_depth=0 returns no descendants."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        
        descendants = await root.descendants(max_depth=0)
        assert descendants == []


# =============================================================================
# Test Force Strategy
# =============================================================================

class TestDescendantsForceStrategy:
    """Test forcing CTE or app-level strategy."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_force_app_level(self):
        """Force app-level even if CTE available."""
        class BothNode(MockTreeNode):
            _cte_called = False
            _app_called = False
            
            async def _supports_cte(self):
                return True
            
            async def _descendants_cte(self, max_depth=None):
                BothNode._cte_called = True
                return []
            
            async def _descendants_app_level(self, max_depth=None):
                BothNode._app_called = True
                return []
        
        BothNode._nodes = {}
        root = BothNode(id=1, name="Root", parent_id=None)
        
        await root.descendants(use_cte=False)
        assert BothNode._app_called
        assert not BothNode._cte_called


# =============================================================================
# Test subtree() Method
# =============================================================================

class TestSubtree:
    """Test subtree() method."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_subtree_default_includes_self(self):
        """subtree() includes self by default."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        
        subtree = await root.subtree()
        assert len(subtree) == 2
        assert subtree[0].id == 1  # Self first
    
    @pytest.mark.asyncio
    async def test_subtree_exclude_self(self):
        """subtree(include_self=False) excludes self."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        
        subtree = await root.subtree(include_self=False)
        assert len(subtree) == 1
        assert subtree[0].id == 2
    
    @pytest.mark.asyncio
    async def test_subtree_with_max_depth(self):
        """subtree() respects max_depth."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        grandchild = MockTreeNode(id=3, name="Grandchild", parent_id=2)
        
        subtree = await root.subtree(max_depth=1)
        # max_depth=1 means only direct children
        # But include_self=True adds self
        assert len(subtree) == 2  # Self + child


# =============================================================================
# Test children() Method
# =============================================================================

class TestChildren:
    """Test children() method."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_children_empty_for_leaf(self):
        """Leaf has no children."""
        leaf = MockTreeNode(id=1, name="Leaf", parent_id=None)
        children = await leaf.children()
        assert children == []
    
    @pytest.mark.asyncio
    async def test_children_single(self):
        """Node with single child."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        
        children = await root.children()
        assert len(children) == 1
        assert children[0].id == 2
    
    @pytest.mark.asyncio
    async def test_children_multiple(self):
        """Node with multiple children."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child1 = MockTreeNode(id=2, name="Child1", parent_id=1)
        child2 = MockTreeNode(id=3, name="Child2", parent_id=1)
        child3 = MockTreeNode(id=4, name="Child3", parent_id=1)
        
        children = await root.children()
        assert len(children) == 3
    
    @pytest.mark.asyncio
    async def test_children_excludes_grandchildren(self):
        """children() only returns direct children."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        grandchild = MockTreeNode(id=3, name="Grandchild", parent_id=2)
        
        children = await root.children()
        assert len(children) == 1
        assert children[0].id == 2


# =============================================================================
# Test Edge Cases
# =============================================================================

class TestDescendantsEdgeCases:
    """Test edge cases for descendants."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_very_wide_tree(self):
        """Handle very wide tree (many direct children)."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        for i in range(100):
            MockTreeNode(id=i+2, name=f"Child{i}", parent_id=1)
        
        descendants = await root.descendants()
        assert len(descendants) == 100
    
    @pytest.mark.asyncio
    async def test_isolated_node(self):
        """Handle node with no parent or children."""
        isolated = MockTreeNode(id=1, name="Isolated", parent_id=None)
        descendants = await isolated.descendants()
        assert descendants == []
    
    @pytest.mark.asyncio
    async def test_multiple_trees(self):
        """Handle multiple independent trees."""
        # Tree 1
        root1 = MockTreeNode(id=1, name="Root1", parent_id=None)
        child1 = MockTreeNode(id=2, name="Child1", parent_id=1)
        
        # Tree 2
        root2 = MockTreeNode(id=3, name="Root2", parent_id=None)
        child2 = MockTreeNode(id=4, name="Child2", parent_id=3)
        
        # Each root should only see its own descendants
        desc1 = await root1.descendants()
        desc2 = await root2.descendants()
        
        assert len(desc1) == 1
        assert desc1[0].id == 2
        
        assert len(desc2) == 1
        assert desc2[0].id == 4


# =============================================================================
# Test Return Types
# =============================================================================

class TestDescendantsReturnTypes:
    """Test return types of descendants methods."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_returns_list(self):
        """descendants() returns a list."""
        node = MockTreeNode(id=1, name="Node", parent_id=None)
        result = await node.descendants()
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_returns_same_type_instances(self):
        """descendants() returns instances of the same class."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        
        descendants = await root.descendants()
        assert all(isinstance(d, MockTreeNode) for d in descendants)
    
    @pytest.mark.asyncio
    async def test_is_async(self):
        """descendants() is an async method."""
        node = MockTreeNode(id=1, name="Node", parent_id=None)
        coro = node.descendants()
        assert hasattr(coro, '__await__')
        await coro

