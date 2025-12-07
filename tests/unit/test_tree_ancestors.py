"""
Test Phase 7.6: TreeMixin ancestors() method.

These tests verify the ancestors() method works correctly with both
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
    """Mock tree node for testing."""
    
    _nodes = {}  # Class-level storage for test data
    
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
        """Mock get method."""
        return cls._nodes.get(id)
    
    @classmethod
    def clear(cls):
        """Clear test data."""
        cls._nodes = {}
    
    async def _get_adapter(self):
        """Return mock adapter."""
        return MockAdapter()
    
    async def _supports_cte(self) -> bool:
        """Default: no CTE support (use app-level)."""
        return False


class MockAdapter:
    """Mock adapter for testing."""
    supports_cte = False
    
    async def fetch(self, query: str, *params) -> List[dict]:
        return []


# =============================================================================
# Test ancestors() Basic Behavior
# =============================================================================

class TestAncestorsBasic:
    """Test basic ancestors() behavior."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Clear test data before each test."""
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_ancestors_empty_for_root(self):
        """Root node has no ancestors."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        ancestors = await root.ancestors()
        assert ancestors == []
    
    @pytest.mark.asyncio
    async def test_ancestors_single_parent(self):
        """Node with one parent."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        
        ancestors = await child.ancestors()
        assert len(ancestors) == 1
        assert ancestors[0].id == 1
    
    @pytest.mark.asyncio
    async def test_ancestors_multiple_levels(self):
        """Node with multiple ancestors."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        parent = MockTreeNode(id=2, name="Parent", parent_id=1)
        child = MockTreeNode(id=3, name="Child", parent_id=2)
        
        ancestors = await child.ancestors()
        assert len(ancestors) == 2
        # Order: immediate parent first, then grandparent
        assert ancestors[0].id == 2
        assert ancestors[1].id == 1
    
    @pytest.mark.asyncio
    async def test_ancestors_include_self(self):
        """ancestors(include_self=True) includes current node."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        
        ancestors = await child.ancestors(include_self=True)
        assert len(ancestors) == 2
        assert ancestors[0].id == 2  # Self first
        assert ancestors[1].id == 1
    
    @pytest.mark.asyncio
    async def test_ancestors_include_self_for_root(self):
        """ancestors(include_self=True) on root returns just self."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        ancestors = await root.ancestors(include_self=True)
        assert len(ancestors) == 1
        assert ancestors[0].id == 1


# =============================================================================
# Test App-Level Traversal
# =============================================================================

class TestAncestorsAppLevel:
    """Test app-level ancestor traversal."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_app_level_single_parent(self):
        """App-level traversal with single parent."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        
        ancestors = await child.ancestors(use_cte=False)
        assert len(ancestors) == 1
        assert ancestors[0].name == "Root"
    
    @pytest.mark.asyncio
    async def test_app_level_deep_hierarchy(self):
        """App-level traversal with deep hierarchy."""
        nodes = []
        for i in range(10):
            node = MockTreeNode(
                id=i+1,
                name=f"Level{i}",
                parent_id=i if i > 0 else None
            )
            nodes.append(node)
        
        deepest = nodes[-1]
        ancestors = await deepest.ancestors(use_cte=False)
        
        assert len(ancestors) == 9
        # Check order: parent first, root last
        assert ancestors[0].id == 9  # Parent
        assert ancestors[-1].id == 1  # Root
    
    @pytest.mark.asyncio
    async def test_app_level_caches_result(self):
        """App-level traversal caches ancestors."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        
        assert child._cached_ancestors is None
        await child.ancestors(use_cte=False)
        assert child._cached_ancestors is not None
        assert len(child._cached_ancestors) == 1
    
    @pytest.mark.asyncio
    async def test_app_level_handles_missing_parent(self):
        """App-level traversal handles missing parent gracefully."""
        # Child references non-existent parent
        child = MockTreeNode(id=2, name="Child", parent_id=999)
        
        ancestors = await child.ancestors(use_cte=False)
        assert ancestors == []


# =============================================================================
# Test CTE Traversal
# =============================================================================

class TestAncestorsCTE:
    """Test CTE-based ancestor traversal."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_cte_called_when_supported(self):
        """CTE method called when database supports it."""
        class CTENode(MockTreeNode):
            _cte_called = False
            
            async def _supports_cte(self) -> bool:
                return True
            
            async def _ancestors_cte(self):
                CTENode._cte_called = True
                return []
        
        CTENode._nodes = {}
        root = CTENode(id=1, name="Root", parent_id=None)
        child = CTENode(id=2, name="Child", parent_id=1)
        
        await child.ancestors()
        assert CTENode._cte_called
    
    @pytest.mark.asyncio
    async def test_app_level_called_when_no_cte(self):
        """App-level called when CTE not supported."""
        class NoCTENode(MockTreeNode):
            _app_called = False
            
            async def _supports_cte(self) -> bool:
                return False
            
            async def _ancestors_app_level(self):
                NoCTENode._app_called = True
                return []
        
        NoCTENode._nodes = {}
        child = NoCTENode(id=2, name="Child", parent_id=1)
        
        await child.ancestors()
        assert NoCTENode._app_called


# =============================================================================
# Test Force Strategy
# =============================================================================

class TestAncestorsForceStrategy:
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
            
            async def _supports_cte(self) -> bool:
                return True
            
            async def _ancestors_cte(self):
                BothNode._cte_called = True
                return []
            
            async def _ancestors_app_level(self):
                BothNode._app_called = True
                return []
        
        BothNode._nodes = {}
        root = BothNode(id=1, name="Root", parent_id=None)
        child = BothNode(id=2, name="Child", parent_id=1)
        
        await child.ancestors(use_cte=False)
        assert BothNode._app_called
        assert not BothNode._cte_called
    
    @pytest.mark.asyncio
    async def test_force_cte(self):
        """Force CTE even if app-level would be used."""
        class BothNode(MockTreeNode):
            _cte_called = False
            _app_called = False
            
            async def _supports_cte(self) -> bool:
                return False  # Would normally use app-level
            
            async def _ancestors_cte(self):
                BothNode._cte_called = True
                return []
            
            async def _ancestors_app_level(self):
                BothNode._app_called = True
                return []
        
        BothNode._nodes = {}
        root = BothNode(id=1, name="Root", parent_id=None)
        child = BothNode(id=2, name="Child", parent_id=1)
        
        await child.ancestors(use_cte=True)
        assert BothNode._cte_called
        assert not BothNode._app_called


# =============================================================================
# Test Path After Ancestors
# =============================================================================

class TestPathAfterAncestors:
    """Test that path works correctly after fetching ancestors."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_path_uses_cached_ancestors(self):
        """Path uses cached ancestors after fetch."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        parent = MockTreeNode(id=2, name="Parent", parent_id=1)
        child = MockTreeNode(id=3, name="Child", parent_id=2)
        
        # Before: no cache
        assert child.path == "Child"
        
        # Fetch ancestors
        await child.ancestors()
        
        # After: includes full path
        assert child.path == "Root/Parent/Child"
    
    @pytest.mark.asyncio
    async def test_path_ids_uses_cached_ancestors(self):
        """path_ids uses cached ancestors after fetch."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        
        # Before: no cache
        assert child.path_ids == [2]
        
        # Fetch ancestors
        await child.ancestors()
        
        # After: includes full path
        assert child.path_ids == [1, 2]


# =============================================================================
# Test Edge Cases
# =============================================================================

class TestAncestorsEdgeCases:
    """Test edge cases for ancestors."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_very_deep_hierarchy(self):
        """Handle very deep hierarchy."""
        nodes = []
        for i in range(100):
            node = MockTreeNode(
                id=i+1,
                name=f"Node{i}",
                parent_id=i if i > 0 else None
            )
            nodes.append(node)
        
        ancestors = await nodes[-1].ancestors()
        assert len(ancestors) == 99
    
    @pytest.mark.asyncio
    async def test_orphan_node(self):
        """Handle orphan node (parent doesn't exist)."""
        orphan = MockTreeNode(id=1, name="Orphan", parent_id=999)
        ancestors = await orphan.ancestors()
        assert ancestors == []
    
    @pytest.mark.asyncio
    async def test_root_with_zero_id(self):
        """Handle root with ID=0."""
        root = MockTreeNode(id=0, name="Root", parent_id=None)
        child = MockTreeNode(id=1, name="Child", parent_id=0)
        
        ancestors = await child.ancestors()
        assert len(ancestors) == 1
        assert ancestors[0].id == 0
    
    @pytest.mark.asyncio
    async def test_multiple_trees(self):
        """Handle multiple independent trees."""
        # Tree 1
        root1 = MockTreeNode(id=1, name="Root1", parent_id=None)
        child1 = MockTreeNode(id=2, name="Child1", parent_id=1)
        
        # Tree 2
        root2 = MockTreeNode(id=3, name="Root2", parent_id=None)
        child2 = MockTreeNode(id=4, name="Child2", parent_id=3)
        
        # Each child should only see its own tree
        ancestors1 = await child1.ancestors()
        ancestors2 = await child2.ancestors()
        
        assert len(ancestors1) == 1
        assert ancestors1[0].id == 1
        
        assert len(ancestors2) == 1
        assert ancestors2[0].id == 3


# =============================================================================
# Test Return Types
# =============================================================================

class TestAncestorsReturnTypes:
    """Test return types of ancestors method."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_returns_list(self):
        """ancestors() returns a list."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        result = await root.ancestors()
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_returns_same_type_instances(self):
        """ancestors() returns instances of the same class."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        
        ancestors = await child.ancestors()
        assert all(isinstance(a, MockTreeNode) for a in ancestors)
    
    @pytest.mark.asyncio
    async def test_is_async(self):
        """ancestors() is an async method."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        # This should be a coroutine
        coro = root.ancestors()
        assert hasattr(coro, '__await__')
        await coro  # Clean up


# =============================================================================
# Test Custom Parent Field
# =============================================================================

class TestAncestorsCustomParentField:
    """Test ancestors with custom parent field."""
    
    @pytest.mark.asyncio
    async def test_custom_parent_field(self):
        """ancestors() works with custom parent field."""
        class EmployeeNode(TreeMixin):
            _tree_parent_field = "manager_id"
            _nodes = {}
            
            def __init__(self, id, name, manager_id=None):
                self.id = id
                self.name = name
                self.manager_id = manager_id
                self._cached_ancestors = None
                EmployeeNode._nodes[id] = self
            
            @classmethod
            async def get(cls, id):
                return cls._nodes.get(id)
            
            async def _supports_cte(self):
                return False
        
        ceo = EmployeeNode(1, "CEO", manager_id=None)
        vp = EmployeeNode(2, "VP", manager_id=1)
        manager = EmployeeNode(3, "Manager", manager_id=2)
        
        ancestors = await manager.ancestors()
        assert len(ancestors) == 2
        assert ancestors[0].name == "VP"
        assert ancestors[1].name == "CEO"

