"""
Test Phase 7.6: Tree Path Operations.

Comprehensive tests for path property and path-related functionality.
"""

import pytest
from typing import Optional, List

from pynext.db.relationships.tree import TreeMixin


# =============================================================================
# Mock Model for Testing
# =============================================================================

class MockTreeNode(TreeMixin):
    """Mock tree node for testing paths."""
    
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
    
    async def count(self):
        return sum(1 for n in self._nodes.values() if self._matches(n))
    
    def _matches(self, node):
        for f, vals in self._in_conditions.items():
            if getattr(node, f, None) not in vals:
                return False
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
# Test Path Property
# =============================================================================

class TestPathProperty:
    """Test the path property."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    def test_path_without_cache_is_just_name(self):
        """Path without cached ancestors is just node name."""
        node = MockTreeNode(id=1, name="Category")
        assert node.path == "Category"
    
    @pytest.mark.asyncio
    async def test_path_with_ancestors(self):
        """Path with ancestors includes full hierarchy."""
        root = MockTreeNode(id=1, name="Root")
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        
        await child.ancestors()
        
        assert child.path == "Root/Child"
    
    @pytest.mark.asyncio
    async def test_path_deep_hierarchy(self):
        """Path with deep hierarchy."""
        nodes = []
        for i in range(5):
            node = MockTreeNode(
                id=i+1,
                name=f"Level{i}",
                parent_id=i if i > 0 else None
            )
            nodes.append(node)
        
        await nodes[-1].ancestors()
        
        assert nodes[-1].path == "Level0/Level1/Level2/Level3/Level4"
    
    @pytest.mark.asyncio
    async def test_path_root_node(self):
        """Path for root node is just its name."""
        root = MockTreeNode(id=1, name="Root")
        await root.ancestors()
        
        assert root.path == "Root"


# =============================================================================
# Test Custom Separators
# =============================================================================

class TestCustomSeparator:
    """Test custom path separators."""
    
    def test_arrow_separator(self):
        """Test arrow separator."""
        class ArrowNode(TreeMixin):
            _tree_separator = " > "
            
            def __init__(self, id, name, parent_id=None):
                self.id = id
                self.name = name
                self.parent_id = parent_id
                self._cached_ancestors = None
        
        root = ArrowNode(1, "Root")
        child = ArrowNode(2, "Child", parent_id=1)
        child._cached_ancestors = [root]
        
        assert child.path == "Root > Child"
    
    def test_backslash_separator(self):
        """Test backslash separator (Windows paths)."""
        class WinNode(TreeMixin):
            _tree_separator = "\\"
            
            def __init__(self, id, name, parent_id=None):
                self.id = id
                self.name = name
                self.parent_id = parent_id
                self._cached_ancestors = None
        
        root = WinNode(1, "C:")
        child = WinNode(2, "Users", parent_id=1)
        child._cached_ancestors = [root]
        
        assert child.path == "C:\\Users"
    
    def test_dot_separator(self):
        """Test dot separator (domain-style)."""
        class DomainNode(TreeMixin):
            _tree_separator = "."
            
            def __init__(self, id, name, parent_id=None):
                self.id = id
                self.name = name
                self.parent_id = parent_id
                self._cached_ancestors = None
        
        # Note: Path is root-to-leaf, so it would be backwards for domains
        root = DomainNode(1, "com")
        child = DomainNode(2, "example", parent_id=1)
        child._cached_ancestors = [root]
        
        assert child.path == "com.example"
    
    def test_empty_separator(self):
        """Test empty separator."""
        class NoSepNode(TreeMixin):
            _tree_separator = ""
            
            def __init__(self, id, name, parent_id=None):
                self.id = id
                self.name = name
                self.parent_id = parent_id
                self._cached_ancestors = None
        
        root = NoSepNode(1, "A")
        child = NoSepNode(2, "B", parent_id=1)
        child._cached_ancestors = [root]
        
        assert child.path == "AB"


# =============================================================================
# Test Custom Name Fields
# =============================================================================

class TestCustomNameField:
    """Test custom name fields for path."""
    
    def test_title_field(self):
        """Use title field for path."""
        class TitleNode(TreeMixin):
            _tree_name_field = "title"
            
            def __init__(self, id, title, parent_id=None):
                self.id = id
                self.title = title
                self.parent_id = parent_id
                self._cached_ancestors = None
        
        root = TitleNode(1, "Root Title")
        child = TitleNode(2, "Child Title", parent_id=1)
        child._cached_ancestors = [root]
        
        assert child.path == "Root Title/Child Title"
    
    def test_label_field(self):
        """Use label field for path."""
        class LabelNode(TreeMixin):
            _tree_name_field = "label"
            
            def __init__(self, id, label, parent_id=None):
                self.id = id
                self.label = label
                self.parent_id = parent_id
                self._cached_ancestors = None
        
        root = LabelNode(1, "Root Label")
        child = LabelNode(2, "Child Label", parent_id=1)
        child._cached_ancestors = [root]
        
        assert child.path == "Root Label/Child Label"
    
    def test_slug_field(self):
        """Use slug field for path (URL-friendly)."""
        class SlugNode(TreeMixin):
            _tree_name_field = "slug"
            
            def __init__(self, id, slug, parent_id=None):
                self.id = id
                self.slug = slug
                self.parent_id = parent_id
                self._cached_ancestors = None
        
        root = SlugNode(1, "electronics")
        child = SlugNode(2, "computers", parent_id=1)
        gc = SlugNode(3, "laptops", parent_id=2)
        gc._cached_ancestors = [child, root]
        
        assert gc.path == "electronics/computers/laptops"


# =============================================================================
# Test path_ids Property
# =============================================================================

class TestPathIds:
    """Test the path_ids property."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    def test_path_ids_without_cache(self):
        """path_ids without cache is just node id."""
        node = MockTreeNode(id=5, name="Node")
        assert node.path_ids == [5]
    
    @pytest.mark.asyncio
    async def test_path_ids_with_ancestors(self):
        """path_ids with ancestors includes all IDs."""
        root = MockTreeNode(id=1, name="Root")
        child = MockTreeNode(id=5, name="Child", parent_id=1)
        
        await child.ancestors()
        
        assert child.path_ids == [1, 5]
    
    @pytest.mark.asyncio
    async def test_path_ids_deep_hierarchy(self):
        """path_ids with deep hierarchy."""
        nodes = []
        for i in range(5):
            node = MockTreeNode(
                id=i*10 + 1,  # IDs: 1, 11, 21, 31, 41
                name=f"Level{i}",
                parent_id=(i-1)*10 + 1 if i > 0 else None
            )
            nodes.append(node)
        
        await nodes[-1].ancestors()
        
        assert nodes[-1].path_ids == [1, 11, 21, 31, 41]


# =============================================================================
# Test Special Characters in Names
# =============================================================================

class TestSpecialCharactersInPath:
    """Test paths with special characters."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_slash_in_name(self):
        """Handle slash in name (ambiguous with separator)."""
        root = MockTreeNode(id=1, name="Root")
        child = MockTreeNode(id=2, name="Child/With/Slashes", parent_id=1)
        
        await child.ancestors()
        
        # Note: This is ambiguous - might need escaping in real usage
        assert "Child/With/Slashes" in child.path
    
    @pytest.mark.asyncio
    async def test_unicode_in_path(self):
        """Handle unicode characters in path."""
        root = MockTreeNode(id=1, name="日本語")
        child = MockTreeNode(id=2, name="カテゴリ", parent_id=1)
        
        await child.ancestors()
        
        assert child.path == "日本語/カテゴリ"
    
    @pytest.mark.asyncio
    async def test_emoji_in_path(self):
        """Handle emoji in path."""
        root = MockTreeNode(id=1, name="📁 Documents")
        child = MockTreeNode(id=2, name="📂 Projects", parent_id=1)
        
        await child.ancestors()
        
        assert "📁" in child.path
        assert "📂" in child.path
    
    @pytest.mark.asyncio
    async def test_empty_name_in_path(self):
        """Handle empty name in path."""
        root = MockTreeNode(id=1, name="")
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        
        await child.ancestors()
        
        assert child.path == "/Child"
    
    @pytest.mark.asyncio
    async def test_whitespace_name(self):
        """Handle whitespace-only name."""
        root = MockTreeNode(id=1, name="   ")
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        
        await child.ancestors()
        
        assert "   " in child.path


# =============================================================================
# Test Path Caching
# =============================================================================

class TestPathCaching:
    """Test path caching behavior."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        MockTreeNode.clear()
        yield
        MockTreeNode.clear()
    
    @pytest.mark.asyncio
    async def test_ancestors_populates_cache(self):
        """Calling ancestors() populates cache for path."""
        root = MockTreeNode(id=1, name="Root")
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        
        assert child._cached_ancestors is None
        
        await child.ancestors()
        
        assert child._cached_ancestors is not None
    
    @pytest.mark.asyncio
    async def test_path_uses_cache(self):
        """Path uses cached ancestors without additional queries."""
        root = MockTreeNode(id=1, name="Root")
        child = MockTreeNode(id=2, name="Child", parent_id=1)
        
        # First call populates cache
        await child.ancestors()
        
        # Path should use cache (sync property)
        path1 = child.path
        path2 = child.path
        
        assert path1 == path2 == "Root/Child"
    
    @pytest.mark.asyncio
    async def test_cache_cleared_on_move(self):
        """Cache is cleared when node moves."""
        root = MockTreeNode(id=1, name="Root")
        parent1 = MockTreeNode(id=2, name="Parent1", parent_id=1)
        parent2 = MockTreeNode(id=3, name="Parent2", parent_id=1)
        child = MockTreeNode(id=4, name="Child", parent_id=2)
        
        await child.ancestors()
        assert child._cached_ancestors is not None
        
        await child.move_to(parent2)
        assert child._cached_ancestors is None

