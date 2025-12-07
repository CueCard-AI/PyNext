"""
Test Phase 7.6: TreeMixin Configuration.

Comprehensive tests for TreeMixin configuration options.
"""

import pytest
from typing import Optional, List

from pynext.db.relationships.tree import TreeMixin


# =============================================================================
# Test Default Configuration
# =============================================================================

class TestDefaultConfiguration:
    """Test default configuration values."""
    
    def test_default_parent_field(self):
        """Default parent field is 'parent_id'."""
        class Node(TreeMixin):
            def __init__(self, id, parent_id=None):
                self.id = id
                self.parent_id = parent_id
        
        node = Node(1)
        assert node._tree_parent_field == "parent_id"
    
    def test_default_name_field(self):
        """Default name field is 'name'."""
        class Node(TreeMixin):
            def __init__(self, id, name):
                self.id = id
                self.name = name
        
        node = Node(1, "Test")
        assert node._tree_name_field == "name"
    
    def test_default_separator(self):
        """Default separator is '/'."""
        class Node(TreeMixin):
            def __init__(self, id):
                self.id = id
        
        node = Node(1)
        assert node._tree_separator == "/"


# =============================================================================
# Test Custom Parent Field
# =============================================================================

class TestCustomParentField:
    """Test custom parent field configuration."""
    
    def test_manager_id_field(self):
        """Use manager_id as parent field."""
        class Employee(TreeMixin):
            _tree_parent_field = "manager_id"
            
            def __init__(self, id, name, manager_id=None):
                self.id = id
                self.name = name
                self.manager_id = manager_id
        
        ceo = Employee(1, "CEO", manager_id=None)
        vp = Employee(2, "VP", manager_id=1)
        
        assert ceo.is_root is True
        assert vp.is_root is False
    
    def test_reports_to_id_field(self):
        """Use reports_to_id as parent field."""
        class Employee(TreeMixin):
            _tree_parent_field = "reports_to_id"
            
            def __init__(self, id, name, reports_to_id=None):
                self.id = id
                self.name = name
                self.reports_to_id = reports_to_id
        
        boss = Employee(1, "Boss", reports_to_id=None)
        worker = Employee(2, "Worker", reports_to_id=1)
        
        assert boss.is_root is True
        assert worker.is_root is False
    
    def test_reply_to_id_field(self):
        """Use reply_to_id as parent field (comments)."""
        class Comment(TreeMixin):
            _tree_parent_field = "reply_to_id"
            
            def __init__(self, id, content, reply_to_id=None):
                self.id = id
                self.content = content
                self.reply_to_id = reply_to_id
        
        root_comment = Comment(1, "Original", reply_to_id=None)
        reply = Comment(2, "Reply", reply_to_id=1)
        
        assert root_comment.is_root is True
        assert reply.is_root is False
    
    def test_folder_id_field(self):
        """Use folder_id as parent field."""
        class File(TreeMixin):
            _tree_parent_field = "folder_id"
            
            def __init__(self, id, name, folder_id=None):
                self.id = id
                self.name = name
                self.folder_id = folder_id
        
        root = File(1, "/", folder_id=None)
        home = File(2, "home", folder_id=1)
        
        assert root.is_root is True
        assert home.is_root is False


# =============================================================================
# Test Custom Name Field
# =============================================================================

class TestCustomNameField:
    """Test custom name field configuration."""
    
    def test_title_field(self):
        """Use title as name field."""
        class Page(TreeMixin):
            _tree_name_field = "title"
            
            def __init__(self, id, title, parent_id=None):
                self.id = id
                self.title = title
                self.parent_id = parent_id
                self._cached_ancestors = None
        
        root = Page(1, "Home")
        child = Page(2, "About", parent_id=1)
        child._cached_ancestors = [root]
        
        assert child._get_node_name(child) == "About"
        assert child.path == "Home/About"
    
    def test_label_field(self):
        """Use label as name field."""
        class MenuItem(TreeMixin):
            _tree_name_field = "label"
            
            def __init__(self, id, label, parent_id=None):
                self.id = id
                self.label = label
                self.parent_id = parent_id
                self._cached_ancestors = None
        
        root = MenuItem(1, "Main Menu")
        child = MenuItem(2, "Products", parent_id=1)
        child._cached_ancestors = [root]
        
        assert child.path == "Main Menu/Products"
    
    def test_slug_field(self):
        """Use slug as name field."""
        class Category(TreeMixin):
            _tree_name_field = "slug"
            
            def __init__(self, id, slug, parent_id=None):
                self.id = id
                self.slug = slug
                self.parent_id = parent_id
                self._cached_ancestors = None
        
        root = Category(1, "electronics")
        child = Category(2, "computers", parent_id=1)
        child._cached_ancestors = [root]
        
        assert child.path == "electronics/computers"


# =============================================================================
# Test Custom Separator
# =============================================================================

class TestCustomSeparator:
    """Test custom separator configuration."""
    
    def test_arrow_separator(self):
        """Use arrow separator."""
        class Node(TreeMixin):
            _tree_separator = " → "
            
            def __init__(self, id, name, parent_id=None):
                self.id = id
                self.name = name
                self.parent_id = parent_id
                self._cached_ancestors = None
        
        root = Node(1, "Root")
        child = Node(2, "Child", parent_id=1)
        child._cached_ancestors = [root]
        
        assert child.path == "Root → Child"
    
    def test_colon_separator(self):
        """Use colon separator."""
        class Namespace(TreeMixin):
            _tree_separator = "::"
            
            def __init__(self, id, name, parent_id=None):
                self.id = id
                self.name = name
                self.parent_id = parent_id
                self._cached_ancestors = None
        
        root = Namespace(1, "std")
        child = Namespace(2, "string", parent_id=1)
        child._cached_ancestors = [root]
        
        assert child.path == "std::string"
    
    def test_dot_separator(self):
        """Use dot separator (package-style)."""
        class Package(TreeMixin):
            _tree_separator = "."
            
            def __init__(self, id, name, parent_id=None):
                self.id = id
                self.name = name
                self.parent_id = parent_id
                self._cached_ancestors = None
        
        root = Package(1, "com")
        child = Package(2, "example", parent_id=1)
        grandchild = Package(3, "app", parent_id=2)
        grandchild._cached_ancestors = [child, root]
        
        assert grandchild.path == "com.example.app"


# =============================================================================
# Test Combined Configuration
# =============================================================================

class TestCombinedConfiguration:
    """Test multiple configuration options together."""
    
    def test_all_custom_config(self):
        """Use all custom configuration options."""
        class OrgEmployee(TreeMixin):
            _tree_parent_field = "manager_id"
            _tree_name_field = "full_name"
            _tree_separator = " > "
            
            def __init__(self, id, full_name, manager_id=None):
                self.id = id
                self.full_name = full_name
                self.manager_id = manager_id
                self._cached_ancestors = None
        
        ceo = OrgEmployee(1, "Alice Smith", manager_id=None)
        vp = OrgEmployee(2, "Bob Jones", manager_id=1)
        dev = OrgEmployee(3, "Carol Davis", manager_id=2)
        dev._cached_ancestors = [vp, ceo]
        
        assert dev.is_root is False
        assert ceo.is_root is True
        assert dev.path == "Alice Smith > Bob Jones > Carol Davis"
    
    def test_file_system_config(self):
        """Unix-style file system configuration."""
        class UnixPath(TreeMixin):
            _tree_parent_field = "parent_id"
            _tree_name_field = "name"
            _tree_separator = "/"
            
            def __init__(self, id, name, parent_id=None):
                self.id = id
                self.name = name
                self.parent_id = parent_id
                self._cached_ancestors = None
        
        root = UnixPath(1, "")
        home = UnixPath(2, "home", parent_id=1)
        user = UnixPath(3, "user", parent_id=2)
        user._cached_ancestors = [home, root]
        
        assert user.path == "/home/user"


# =============================================================================
# Test Inheritance
# =============================================================================

class TestConfigurationInheritance:
    """Test configuration inheritance in subclasses."""
    
    def test_subclass_inherits_config(self):
        """Subclass inherits parent configuration."""
        class BaseTree(TreeMixin):
            _tree_separator = " >> "
            
            def __init__(self, id, name, parent_id=None):
                self.id = id
                self.name = name
                self.parent_id = parent_id
                self._cached_ancestors = None
        
        class SubTree(BaseTree):
            pass
        
        node = SubTree(1, "Test")
        assert node._tree_separator == " >> "
    
    def test_subclass_overrides_config(self):
        """Subclass can override parent configuration."""
        class BaseTree(TreeMixin):
            _tree_separator = " >> "
            
            def __init__(self, id, name, parent_id=None):
                self.id = id
                self.name = name
                self.parent_id = parent_id
                self._cached_ancestors = None
        
        class SubTree(BaseTree):
            _tree_separator = " -> "
        
        base = BaseTree(1, "Base")
        sub = SubTree(2, "Sub")
        
        assert base._tree_separator == " >> "
        assert sub._tree_separator == " -> "

