"""
Test Phase 7.6: TreeMixin Basic Properties.

These tests verify the sync properties of TreeMixin:
- is_root
- path
- path_ids
- _get_node_name
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
    
    @classmethod
    async def get(cls, id: int) -> Optional["MockTreeNode"]:
        """Mock get method."""
        # This would be overridden in tests
        return None
    
    def select(self):
        """Mock select method."""
        return MockQuery()
    
    async def save(self):
        """Mock save method."""
        pass


class MockQuery:
    """Mock query for testing."""
    
    def where(self, **kwargs):
        return self
    
    def where_in(self, **kwargs):
        return self
    
    def where_null(self, field):
        return self
    
    async def count(self):
        return 0
    
    def __await__(self):
        async def _await():
            return []
        return _await().__await__()


# =============================================================================
# Test is_root Property
# =============================================================================

class TestIsRoot:
    """Test the is_root property."""
    
    def test_is_root_when_parent_id_none(self):
        """Node with parent_id=None is root."""
        node = MockTreeNode(id=1, name="Root", parent_id=None)
        assert node.is_root is True
    
    def test_is_root_when_has_parent(self):
        """Node with parent_id is not root."""
        node = MockTreeNode(id=2, name="Child", parent_id=1)
        assert node.is_root is False
    
    def test_is_root_with_zero_parent_id(self):
        """Node with parent_id=0 is not root (0 is valid ID)."""
        node = MockTreeNode(id=2, name="Child", parent_id=0)
        assert node.is_root is False
    
    def test_is_root_sync_property(self):
        """is_root is a sync property (no await needed)."""
        node = MockTreeNode(id=1, name="Root")
        # Should not raise - it's sync
        result = node.is_root
        assert isinstance(result, bool)
    
    def test_is_root_with_custom_parent_field(self):
        """Test with custom parent field name."""
        class CustomNode(TreeMixin):
            _tree_parent_field = "manager_id"
            
            def __init__(self, id, name, manager_id=None):
                self.id = id
                self.name = name
                self.manager_id = manager_id
        
        node1 = CustomNode(1, "CEO", manager_id=None)
        node2 = CustomNode(2, "VP", manager_id=1)
        
        assert node1.is_root is True
        assert node2.is_root is False


# =============================================================================
# Test _get_node_name Helper
# =============================================================================

class TestGetNodeName:
    """Test the _get_node_name helper."""
    
    def test_get_name_from_name_field(self):
        """Get name from 'name' field."""
        node = MockTreeNode(id=1, name="Electronics")
        assert node._get_node_name(node) == "Electronics"
    
    def test_get_name_from_title_field(self):
        """Get name from 'title' field when name not available."""
        class TitleNode(TreeMixin):
            def __init__(self, id, title):
                self.id = id
                self.title = title
        
        node = TitleNode(1, "My Title")
        assert node._get_node_name(node) == "My Title"
    
    def test_get_name_from_label_field(self):
        """Get name from 'label' field."""
        class LabelNode(TreeMixin):
            def __init__(self, id, label):
                self.id = id
                self.label = label
        
        node = LabelNode(1, "My Label")
        assert node._get_node_name(node) == "My Label"
    
    def test_get_name_fallback_to_id(self):
        """Fallback to id when no name field."""
        class IdOnlyNode(TreeMixin):
            def __init__(self, id):
                self.id = id
        
        node = IdOnlyNode(42)
        assert node._get_node_name(node) == "42"
    
    def test_get_name_with_custom_field(self):
        """Use custom name field from config."""
        class CustomNameNode(TreeMixin):
            _tree_name_field = "display_name"
            
            def __init__(self, id, display_name):
                self.id = id
                self.display_name = display_name
        
        node = CustomNameNode(1, "Custom Name")
        assert node._get_node_name(node) == "Custom Name"
    
    def test_get_name_with_none_value(self):
        """Handle None value gracefully."""
        class NoneNameNode(TreeMixin):
            def __init__(self, id):
                self.id = id
                self.name = None
                self.title = "Fallback Title"
        
        node = NoneNameNode(1)
        assert node._get_node_name(node) == "Fallback Title"
    
    def test_get_name_converts_to_string(self):
        """Convert non-string values to string."""
        class IntNameNode(TreeMixin):
            def __init__(self, id, name):
                self.id = id
                self.name = name
        
        node = IntNameNode(1, 123)
        assert node._get_node_name(node) == "123"


# =============================================================================
# Test path Property
# =============================================================================

class TestPath:
    """Test the path property."""
    
    def test_path_with_no_cached_ancestors(self):
        """Path returns just node name when no ancestors cached."""
        node = MockTreeNode(id=1, name="Electronics")
        node._cached_ancestors = None
        assert node.path == "Electronics"
    
    def test_path_with_cached_ancestors(self):
        """Path includes ancestors when cached."""
        root = MockTreeNode(id=1, name="Root")
        parent = MockTreeNode(id=2, name="Parent", parent_id=1)
        child = MockTreeNode(id=3, name="Child", parent_id=2)
        
        # Cache ancestors (parent to root order)
        child._cached_ancestors = [parent, root]
        
        assert child.path == "Root/Parent/Child"
    
    def test_path_with_single_ancestor(self):
        """Path with single ancestor."""
        root = MockTreeNode(id=1, name="Root")
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        
        child._cached_ancestors = [root]
        
        assert child.path == "Root/Child"
    
    def test_path_for_root_node(self):
        """Path for root node is just its name."""
        root = MockTreeNode(id=1, name="Root")
        root._cached_ancestors = []
        assert root.path == "Root"
    
    def test_path_with_custom_separator(self):
        """Use custom path separator."""
        class CustomSepNode(TreeMixin):
            _tree_separator = " > "
            
            def __init__(self, id, name, parent_id=None):
                self.id = id
                self.name = name
                self.parent_id = parent_id
                self._cached_ancestors = None
        
        root = CustomSepNode(1, "Root")
        child = CustomSepNode(2, "Child", parent_id=1)
        child._cached_ancestors = [root]
        
        assert child.path == "Root > Child"
    
    def test_path_with_deep_hierarchy(self):
        """Path with deep hierarchy."""
        nodes = []
        for i in range(5):
            node = MockTreeNode(
                id=i+1,
                name=f"Level{i}",
                parent_id=i if i > 0 else None
            )
            nodes.append(node)
        
        # Cache ancestors for deepest node (reverse order, parent to root)
        nodes[-1]._cached_ancestors = list(reversed(nodes[:-1]))
        
        assert nodes[-1].path == "Level0/Level1/Level2/Level3/Level4"
    
    def test_path_is_sync_property(self):
        """path is a sync property (no await needed)."""
        node = MockTreeNode(id=1, name="Test")
        # Should not raise - it's sync
        result = node.path
        assert isinstance(result, str)


# =============================================================================
# Test path_ids Property
# =============================================================================

class TestPathIds:
    """Test the path_ids property."""
    
    def test_path_ids_with_no_cached_ancestors(self):
        """path_ids returns just node id when no ancestors cached."""
        node = MockTreeNode(id=5, name="Node")
        node._cached_ancestors = None
        assert node.path_ids == [5]
    
    def test_path_ids_with_cached_ancestors(self):
        """path_ids includes ancestor IDs when cached."""
        root = MockTreeNode(id=1, name="Root")
        parent = MockTreeNode(id=2, name="Parent", parent_id=1)
        child = MockTreeNode(id=3, name="Child", parent_id=2)
        
        # Cache ancestors (parent to root order)
        child._cached_ancestors = [parent, root]
        
        assert child.path_ids == [1, 2, 3]
    
    def test_path_ids_for_root_node(self):
        """path_ids for root node is just its id."""
        root = MockTreeNode(id=1, name="Root")
        root._cached_ancestors = []
        assert root.path_ids == [1]
    
    def test_path_ids_with_deep_hierarchy(self):
        """path_ids with deep hierarchy."""
        nodes = []
        for i in range(5):
            node = MockTreeNode(
                id=i+1,
                name=f"Level{i}",
                parent_id=i if i > 0 else None
            )
            nodes.append(node)
        
        # Cache ancestors for deepest node
        nodes[-1]._cached_ancestors = list(reversed(nodes[:-1]))
        
        assert nodes[-1].path_ids == [1, 2, 3, 4, 5]
    
    def test_path_ids_is_sync_property(self):
        """path_ids is a sync property (no await needed)."""
        node = MockTreeNode(id=1, name="Test")
        # Should not raise - it's sync
        result = node.path_ids
        assert isinstance(result, list)


# =============================================================================
# Test Configuration Options
# =============================================================================

class TestConfiguration:
    """Test TreeMixin configuration options."""
    
    def test_default_parent_field(self):
        """Default parent field is 'parent_id'."""
        node = MockTreeNode(id=1, name="Test")
        assert node._tree_parent_field == "parent_id"
    
    def test_default_name_field(self):
        """Default name field is 'name'."""
        node = MockTreeNode(id=1, name="Test")
        assert node._tree_name_field == "name"
    
    def test_default_separator(self):
        """Default separator is '/'."""
        node = MockTreeNode(id=1, name="Test")
        assert node._tree_separator == "/"
    
    def test_custom_parent_field(self):
        """Can customize parent field name."""
        class CustomParentNode(TreeMixin):
            _tree_parent_field = "manager_id"
            
            def __init__(self, id, name, manager_id=None):
                self.id = id
                self.name = name
                self.manager_id = manager_id
        
        node = CustomParentNode(1, "Test")
        assert node._tree_parent_field == "manager_id"
        assert node.is_root is True
    
    def test_custom_name_field(self):
        """Can customize name field for path."""
        class CustomNameNode(TreeMixin):
            _tree_name_field = "title"
            
            def __init__(self, id, title, parent_id=None):
                self.id = id
                self.title = title
                self.parent_id = parent_id
                self._cached_ancestors = None
        
        node = CustomNameNode(1, "My Title")
        assert node._get_node_name(node) == "My Title"
    
    def test_custom_separator(self):
        """Can customize path separator."""
        class CustomSepNode(TreeMixin):
            _tree_separator = " -> "
            
            def __init__(self, id, name, parent_id=None):
                self.id = id
                self.name = name
                self.parent_id = parent_id
        
        node = CustomSepNode(1, "Test")
        assert node._tree_separator == " -> "


# =============================================================================
# Test Edge Cases
# =============================================================================

class TestEdgeCases:
    """Test edge cases for basic properties."""
    
    def test_node_without_id(self):
        """Handle node without id attribute."""
        class NoIdNode(TreeMixin):
            def __init__(self, name, parent_id=None):
                self.name = name
                self.parent_id = parent_id
                self._cached_ancestors = None
        
        node = NoIdNode("Test")
        # Should not crash
        assert node.is_root is True
        assert node.path == "Test"
    
    def test_empty_name(self):
        """Handle empty name."""
        node = MockTreeNode(id=1, name="")
        assert node._get_node_name(node) == ""
    
    def test_unicode_name(self):
        """Handle unicode in name."""
        node = MockTreeNode(id=1, name="日本語カテゴリ")
        assert node._get_node_name(node) == "日本語カテゴリ"
    
    def test_special_chars_in_name(self):
        """Handle special characters in name."""
        node = MockTreeNode(id=1, name="Category/With/Slashes")
        assert node._get_node_name(node) == "Category/With/Slashes"
    
    def test_very_long_path(self):
        """Handle very long path."""
        nodes = []
        for i in range(100):
            node = MockTreeNode(
                id=i+1,
                name=f"L{i}",
                parent_id=i if i > 0 else None
            )
            nodes.append(node)
        
        # Cache all ancestors
        nodes[-1]._cached_ancestors = list(reversed(nodes[:-1]))
        
        path = nodes[-1].path
        assert len(path.split("/")) == 100


# =============================================================================
# Test Multiple Instances
# =============================================================================

class TestMultipleInstances:
    """Test behavior with multiple node instances."""
    
    def test_cached_ancestors_not_shared(self):
        """Each instance has its own cached ancestors."""
        node1 = MockTreeNode(id=1, name="Node1")
        node2 = MockTreeNode(id=2, name="Node2")
        
        root = MockTreeNode(id=0, name="Root")
        node1._cached_ancestors = [root]
        
        # node2 should not have node1's cache
        assert node2._cached_ancestors is None
    
    def test_is_root_independent(self):
        """is_root is independent per instance."""
        root = MockTreeNode(id=1, name="Root", parent_id=None)
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        
        assert root.is_root is True
        assert child.is_root is False


# =============================================================================
# Test Property Types
# =============================================================================

class TestPropertyTypes:
    """Test return types of properties."""
    
    def test_is_root_returns_bool(self):
        """is_root returns boolean."""
        node = MockTreeNode(id=1, name="Test")
        assert isinstance(node.is_root, bool)
    
    def test_path_returns_string(self):
        """path returns string."""
        node = MockTreeNode(id=1, name="Test")
        assert isinstance(node.path, str)
    
    def test_path_ids_returns_list(self):
        """path_ids returns list of integers."""
        node = MockTreeNode(id=1, name="Test")
        result = node.path_ids
        assert isinstance(result, list)
        assert all(isinstance(x, int) for x in result)

