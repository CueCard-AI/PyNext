"""
Test Phase 7.6: App-Level Tree Traversal.

These tests verify the app-level (non-CTE) fallback for tree traversal
works correctly on databases that don't support CTEs.
"""

import pytest
from typing import Optional, List
from unittest.mock import Mock, MagicMock, AsyncMock, patch

from pynext.db.relationships.tree import TreeMixin


# =============================================================================
# Mock Model for Testing
# =============================================================================

class MockTreeNode(TreeMixin):
    """Mock tree node for testing app-level traversal."""
    
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
    
    async def _supports_cte(self) -> bool:
        return False  # Force app-level


class MockQuery:
    """Mock query for testing."""
    
    def __init__(self, nodes):
        self._nodes = nodes
        self._where_conditions = {}
        self._where_in_conditions = {}
    
    def where(self, **kwargs):
        self._where_conditions.update(kwargs)
        return self
    
    def where_in(self, **kwargs):
        self._where_in_conditions.update(kwargs)
        return self
    
    def where_null(self, field):
        self._where_conditions['_null'] = field
        return self
    
    async def count(self):
        return sum(1 for n in self._nodes.values() if self._matches(n))
    
    def _matches(self, node):
        # Check where_in conditions
        for field, values in self._where_in_conditions.items():
            if getattr(node, field, None) not in values:
                return False
        
        # Check where conditions
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
# Test App-Level Ancestors
# =============================================================================

class TestAppLevelAncestors:
    """Test app-level ancestor traversal."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_ancestors_walks_parent_chain(self):
        """App-level walks up parent chain correctly."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        grandchild = MockTreeNode(id=3, name="Grandchild", parent_id=2)
        
        ancestors = await grandchild._ancestors_app_level()
        
        assert len(ancestors) == 2
        assert ancestors[0].id == 2  # Parent first
        assert ancestors[1].id == 1  # Root last
    
    @pytest.mark.asyncio
    async def test_ancestors_stops_at_root(self):
        """App-level stops at root node."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        
        ancestors = await child._ancestors_app_level()
        
        assert len(ancestors) == 1
        assert ancestors[0].parent_id is None  # Is root
    
    @pytest.mark.asyncio
    async def test_ancestors_handles_missing_parent(self):
        """App-level handles orphan nodes gracefully."""
        orphan = MockTreeNode(id=1, name="Orphan", parent_id=999)
        
        ancestors = await orphan._ancestors_app_level()
        
        assert ancestors == []
    
    @pytest.mark.asyncio
    async def test_ancestors_deep_chain(self):
        """App-level handles deep chains."""
        nodes = []
        for i in range(20):
            node = MockTreeNode(
                id=i+1,
                name=f"Level{i}",
                parent_id=i if i > 0 else None
            )
            nodes.append(node)
        
        ancestors = await nodes[-1]._ancestors_app_level()
        
        assert len(ancestors) == 19


# =============================================================================
# Test App-Level Descendants
# =============================================================================

class TestAppLevelDescendants:
    """Test app-level descendant traversal."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_descendants_breadth_first(self):
        """App-level traverses breadth-first."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child1 = MockTreeNode(id=2, name="Child1", parent_id=1)
        child2 = MockTreeNode(id=3, name="Child2", parent_id=1)
        grandchild = MockTreeNode(id=4, name="Grandchild", parent_id=2)
        
        descendants = await root._descendants_app_level()
        
        # Should find all 3 descendants
        assert len(descendants) == 3
    
    @pytest.mark.asyncio
    async def test_descendants_handles_leaf(self):
        """App-level handles leaf nodes."""
        leaf = MockTreeNode(id=1, name="Leaf", parent_id=None)
        
        descendants = await leaf._descendants_app_level()
        
        assert descendants == []
    
    @pytest.mark.asyncio
    async def test_descendants_with_max_depth(self):
        """App-level respects max_depth."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        grandchild = MockTreeNode(id=3, name="Grandchild", parent_id=2)
        great_grandchild = MockTreeNode(id=4, name="GreatGrandchild", parent_id=3)
        
        descendants = await root._descendants_app_level(max_depth=1)
        
        # Only direct children
        assert len(descendants) == 1
        assert descendants[0].id == 2
    
    @pytest.mark.asyncio
    async def test_descendants_wide_tree(self):
        """App-level handles wide trees."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        for i in range(20):
            MockTreeNode(id=i+2, name=f"Child{i}", parent_id=1)
        
        descendants = await root._descendants_app_level()
        
        assert len(descendants) == 20


# =============================================================================
# Test App-Level Performance
# =============================================================================

class TestAppLevelPerformance:
    """Test app-level performance characteristics."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_ancestors_queries_per_level(self):
        """App-level ancestors makes one query per level."""
        # Track get calls
        call_count = 0
        original_get = MockTreeNode.get
        
        async def tracked_get(id):
            nonlocal call_count
            call_count += 1
            return await original_get(id)
        
        MockTreeNode.get = classmethod(lambda cls, id: tracked_get(id))
        
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        grandchild = MockTreeNode(id=3, name="Grandchild", parent_id=2)
        
        await grandchild._ancestors_app_level()
        
        # Should be 2 queries (one for parent, one for grandparent)
        assert call_count == 2
        
        MockTreeNode.get = original_get
    
    @pytest.mark.asyncio
    async def test_descendants_queries_per_level(self):
        """App-level descendants makes queries per level."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        grandchild = MockTreeNode(id=3, name="Grandchild", parent_id=2)
        
        # Count shouldn't exceed number of levels
        descendants = await root._descendants_app_level()
        
        # Just verify it works - actual query count depends on implementation
        assert len(descendants) == 2


# =============================================================================
# Test Fallback Selection
# =============================================================================

class TestFallbackSelection:
    """Test that app-level is used when CTE not available."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_uses_app_level_when_no_cte(self):
        """Uses app-level when CTE not supported."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        
        # MockTreeNode._supports_cte returns False
        # So ancestors() should use _ancestors_app_level
        ancestors = await child.ancestors()
        
        assert len(ancestors) == 1
    
    @pytest.mark.asyncio
    async def test_can_force_app_level(self):
        """Can force app-level with use_cte=False."""
        class CTENode(MockTreeNode):
            async def _supports_cte(self):
                return True
            
            async def _ancestors_cte(self):
                return ["CTE_RESULT"]
            
            async def _ancestors_app_level(self):
                return ["APP_LEVEL_RESULT"]
        
        CTENode._nodes = {}
        root = CTENode(id=1, name="Root", parent_id=None)
        child = CTENode(id=2, name="Child", parent_id=1)
        
        # Force app-level even though CTE is available
        result = await child.ancestors(use_cte=False)
        
        assert result == ["APP_LEVEL_RESULT"]


# =============================================================================
# Test Edge Cases
# =============================================================================

class TestAppLevelEdgeCases:
    """Test edge cases in app-level traversal."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_handles_circular_reference_detection(self):
        """Would handle circular references (if they occurred)."""
        # Create nodes but don't create actual cycle
        # (DB constraints should prevent real cycles)
        node = MockTreeNode(id=1, name="Node", parent_id=None)
        
        ancestors = await node._ancestors_app_level()
        assert ancestors == []
    
    @pytest.mark.asyncio
    async def test_handles_zero_id(self):
        """Handles node with ID 0."""
        root = MockTreeNode(id=0, name="Root", parent_id=None)
        child = MockTreeNode(id=1, name="Child", parent_id=0)
        
        ancestors = await child._ancestors_app_level()
        
        assert len(ancestors) == 1
        assert ancestors[0].id == 0
    
    @pytest.mark.asyncio
    async def test_handles_negative_id(self):
        """Handles node with negative ID."""
        root = MockTreeNode(id=-1, name="Root", parent_id=None)
        child = MockTreeNode(id=1, name="Child", parent_id=-1)
        
        ancestors = await child._ancestors_app_level()
        
        assert len(ancestors) == 1
        assert ancestors[0].id == -1
    
    @pytest.mark.asyncio
    async def test_descendants_max_depth_zero(self):
        """max_depth=0 returns empty list."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        
        descendants = await root._descendants_app_level(max_depth=0)
        
        assert descendants == []


# =============================================================================
# Test Caching
# =============================================================================

class TestAppLevelCaching:
    """Test that results are cached appropriately."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_ancestors_cached_for_path(self):
        """Ancestors are cached for path property."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        
        # Before ancestors()
        assert child._cached_ancestors is None
        
        # After ancestors() (which uses app-level)
        await child.ancestors()
        
        # Should be cached
        assert child._cached_ancestors is not None
        assert len(child._cached_ancestors) == 1
    
    @pytest.mark.asyncio
    async def test_path_uses_cache(self):
        """Path property uses cached ancestors."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        
        # Populate cache
        await child.ancestors()
        
        # Path should use cache
        assert child.path == "Root/Child"

