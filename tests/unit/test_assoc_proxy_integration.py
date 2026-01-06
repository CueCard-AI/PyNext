"""
Tests for association proxy integration patterns.

Tests cover:
- Real-world usage scenarios
- E-commerce patterns
- User permissions
- Content management
- Complex relationship graphs
"""

import pytest
from typing import List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta


# =============================================================================
# Mock Classes for Real-World Scenarios
# =============================================================================

# E-Commerce Models
@dataclass
class Tag:
    id: int
    name: str
    color: str = "gray"


@dataclass
class Category:
    id: int
    name: str
    slug: str
    parent: Optional["Category"] = None


@dataclass
class ProductTag:
    id: int
    product_id: int
    tag_id: int
    tag: Optional[Tag] = None
    added_at: datetime = field(default_factory=datetime.now)


@dataclass
class ProductCategory:
    id: int
    product_id: int
    category_id: int
    category: Optional[Category] = None
    is_primary: bool = False


@dataclass
class Variant:
    id: int
    product_id: int
    sku: str
    price: float
    stock: int = 0


# User/Permissions Models
@dataclass
class Permission:
    id: int
    name: str
    code: str


@dataclass
class Role:
    id: int
    name: str
    permissions: List[Permission] = field(default_factory=list)


@dataclass
class UserRole:
    id: int
    user_id: int
    role_id: int
    role: Optional[Role] = None
    granted_at: datetime = field(default_factory=datetime.now)


# CMS Models
@dataclass
class Author:
    id: int
    name: str
    email: str
    bio: Optional[str] = None


@dataclass
class Comment:
    id: int
    post_id: int
    author: Optional[Author] = None
    content: str = ""
    approved: bool = False


class MockTable:
    _fields = {}
    __table_name__ = "mock"


from pynext.db.relationships.association_proxy import (
    association_proxy,
    ProxyCollection,
)


# =============================================================================
# Test: E-Commerce Product Tags
# =============================================================================

class TestECommerceProductTags:
    """Test e-commerce product tagging pattern."""
    
    def test_product_tag_names(self):
        """Access tag names through product_tags junction."""
        class Product(MockTable):
            def __init__(self, product_tags: List[ProductTag]):
                self.id = 1
                self._product_tags = product_tags
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tag_names = association_proxy("product_tags", "tag.name")
        
        tags = [Tag(1, "electronics"), Tag(2, "sale"), Tag(3, "featured")]
        product_tags = [ProductTag(i, 1, t.id, tag=t) for i, t in enumerate(tags, 1)]
        product = Product(product_tags)
        
        assert list(product.tag_names) == ["electronics", "sale", "featured"]
    
    def test_product_tag_colors(self):
        """Access tag colors for display."""
        class Product(MockTable):
            def __init__(self, product_tags: List[ProductTag]):
                self._product_tags = product_tags
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tag_colors = association_proxy("product_tags", "tag.color")
        
        product_tags = [
            ProductTag(1, 1, 1, tag=Tag(1, "sale", "red")),
            ProductTag(2, 1, 2, tag=Tag(2, "new", "green")),
        ]
        product = Product(product_tags)
        
        assert list(product.tag_colors) == ["red", "green"]
    
    def test_add_tag_with_creator(self):
        """Add tag to product using creator."""
        class Product(MockTable):
            def __init__(self):
                self.id = 1
                self._product_tags = []
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tags = association_proxy(
            "product_tags",
            "tag",
            creator=lambda tag: ProductTag(0, 1, tag.id, tag=tag)
        )
        
        product = Product()
        product.tags.append(Tag(1, "new_tag"))
        product.tags.append(Tag(2, "another"))
        
        assert len(product._product_tags) == 2
        assert list(product.tags)[0].name == "new_tag"


# =============================================================================
# Test: E-Commerce Product Categories
# =============================================================================

class TestECommerceCategories:
    """Test product categorization pattern."""
    
    def test_category_names(self):
        """Get all category names for a product."""
        class Product(MockTable):
            def __init__(self, product_categories: List[ProductCategory]):
                self._product_categories = product_categories
            
            @property
            def product_categories(self):
                return self._product_categories
        
        Product.category_names = association_proxy("product_categories", "category.name")
        
        product_categories = [
            ProductCategory(1, 1, 1, category=Category(1, "Electronics", "electronics")),
            ProductCategory(2, 1, 2, category=Category(2, "Phones", "phones")),
        ]
        product = Product(product_categories)
        
        assert list(product.category_names) == ["Electronics", "Phones"]
    
    def test_category_slugs_for_url(self):
        """Get category slugs for URL building."""
        class Product(MockTable):
            def __init__(self, product_categories: List[ProductCategory]):
                self._product_categories = product_categories
            
            @property
            def product_categories(self):
                return self._product_categories
        
        Product.category_slugs = association_proxy("product_categories", "category.slug")
        
        product_categories = [
            ProductCategory(1, 1, 1, category=Category(1, "Electronics", "electronics")),
        ]
        product = Product(product_categories)
        
        assert list(product.category_slugs) == ["electronics"]
    
    def test_primary_category_name(self):
        """Get primary category for display."""
        class Product(MockTable):
            def __init__(self, product_categories: List[ProductCategory]):
                self._product_categories = product_categories
            
            @property
            def product_categories(self):
                return self._product_categories
            
            @property
            def primary_category_rel(self):
                for pc in self._product_categories:
                    if pc.is_primary:
                        return pc
                return None
        
        Product.primary_category_name = association_proxy(
            "primary_category_rel", 
            "category.name",
            scalar=True
        )
        
        product_categories = [
            ProductCategory(1, 1, 1, category=Category(1, "Electronics", "e"), is_primary=False),
            ProductCategory(2, 1, 2, category=Category(2, "Phones", "p"), is_primary=True),
        ]
        product = Product(product_categories)
        
        assert product.primary_category_name == "Phones"


# =============================================================================
# Test: E-Commerce Product Variants
# =============================================================================

class TestProductVariants:
    """Test product variants pattern."""
    
    def test_variant_skus(self):
        """Get all SKUs for a product."""
        class Product(MockTable):
            def __init__(self, variants: List[Variant]):
                self._variants = variants
            
            @property
            def variants(self):
                return self._variants
        
        Product.skus = association_proxy("variants", "sku")
        
        variants = [
            Variant(1, 1, "PHONE-BLK-64", 999.0),
            Variant(2, 1, "PHONE-WHT-64", 999.0),
            Variant(3, 1, "PHONE-BLK-128", 1099.0),
        ]
        product = Product(variants)
        
        assert list(product.skus) == ["PHONE-BLK-64", "PHONE-WHT-64", "PHONE-BLK-128"]
    
    def test_variant_prices(self):
        """Get all prices for comparison."""
        class Product(MockTable):
            def __init__(self, variants: List[Variant]):
                self._variants = variants
            
            @property
            def variants(self):
                return self._variants
        
        Product.prices = association_proxy("variants", "price")
        
        variants = [
            Variant(1, 1, "S", 29.99),
            Variant(2, 1, "M", 34.99),
            Variant(3, 1, "L", 39.99),
        ]
        product = Product(variants)
        
        prices = list(product.prices)
        assert min(prices) == 29.99
        assert max(prices) == 39.99


# =============================================================================
# Test: User Roles and Permissions
# =============================================================================

class TestUserPermissions:
    """Test user roles and permissions pattern."""
    
    def test_role_names(self):
        """Get user's role names."""
        class User(MockTable):
            def __init__(self, user_roles: List[UserRole]):
                self._user_roles = user_roles
            
            @property
            def user_roles(self):
                return self._user_roles
        
        User.role_names = association_proxy("user_roles", "role.name")
        
        roles = [
            Role(1, "Admin"),
            Role(2, "Editor"),
        ]
        user_roles = [UserRole(i, 1, r.id, role=r) for i, r in enumerate(roles, 1)]
        user = User(user_roles)
        
        assert list(user.role_names) == ["Admin", "Editor"]
    
    def test_check_role(self):
        """Check if user has specific role."""
        class User(MockTable):
            def __init__(self, user_roles: List[UserRole]):
                self._user_roles = user_roles
            
            @property
            def user_roles(self):
                return self._user_roles
        
        User.role_names = association_proxy("user_roles", "role.name")
        
        user_roles = [
            UserRole(1, 1, 1, role=Role(1, "Admin")),
            UserRole(2, 1, 2, role=Role(2, "Editor")),
        ]
        user = User(user_roles)
        
        assert "Admin" in user.role_names
        assert "SuperAdmin" not in user.role_names
    
    def test_get_roles_directly(self):
        """Get role objects for detailed inspection."""
        class User(MockTable):
            def __init__(self, user_roles: List[UserRole]):
                self._user_roles = user_roles
            
            @property
            def user_roles(self):
                return self._user_roles
        
        User.roles = association_proxy("user_roles", "role")
        
        admin_role = Role(1, "Admin", [
            Permission(1, "Read", "read"),
            Permission(2, "Write", "write"),
        ])
        user_roles = [UserRole(1, 1, 1, role=admin_role)]
        user = User(user_roles)
        
        roles = list(user.roles)
        assert len(roles) == 1
        assert roles[0].name == "Admin"
        assert len(roles[0].permissions) == 2


# =============================================================================
# Test: CMS Blog Posts
# =============================================================================

class TestCMSBlogPosts:
    """Test CMS blog post patterns."""
    
    def test_post_author_name(self):
        """Get post author's name."""
        class Post(MockTable):
            def __init__(self, author: Author):
                self._author = author
            
            @property
            def author(self):
                return self._author
        
        Post.author_name = association_proxy("author", "name", scalar=True)
        
        post = Post(Author(1, "Jane Doe", "jane@blog.com"))
        
        assert post.author_name == "Jane Doe"
    
    def test_comment_authors(self):
        """Get all comment author names."""
        class Post(MockTable):
            def __init__(self, comments: List[Comment]):
                self._comments = comments
            
            @property
            def comments(self):
                return self._comments
        
        Post.commenter_names = association_proxy("comments", "author.name")
        
        comments = [
            Comment(1, 1, Author(1, "Alice", "a@test.com"), "Great post!"),
            Comment(2, 1, Author(2, "Bob", "b@test.com"), "Thanks!"),
        ]
        post = Post(comments)
        
        assert list(post.commenter_names) == ["Alice", "Bob"]
    
    def test_approved_comment_count(self):
        """Filter and count approved comments."""
        import asyncio
        
        class Post(MockTable):
            def __init__(self, comments: List[Comment]):
                self._comments = comments
            
            @property
            def comments(self):
                return self._comments
        
        Post.comment_authors = association_proxy("comments", "author")
        
        comments = [
            Comment(1, 1, Author(1, "Alice", "a@test.com"), approved=True),
            Comment(2, 1, Author(2, "Bob", "b@test.com"), approved=False),
            Comment(3, 1, Author(3, "Charlie", "c@test.com"), approved=True),
        ]
        post = Post(comments)
        
        # Note: filter is async
        all_authors = list(post.comment_authors)
        assert len(all_authors) == 3


# =============================================================================
# Test: Multi-Level Relationships
# =============================================================================

class TestMultiLevelRelationships:
    """Test complex relationship traversal."""
    
    def test_product_category_parent_names(self):
        """Get parent category names for breadcrumbs."""
        class Product(MockTable):
            def __init__(self, product_categories: List[ProductCategory]):
                self._product_categories = product_categories
            
            @property
            def product_categories(self):
                return self._product_categories
        
        Product.parent_category_names = association_proxy(
            "product_categories", 
            "category.parent.name"
        )
        
        parent = Category(1, "Electronics", "electronics")
        child = Category(2, "Phones", "phones", parent=parent)
        product_categories = [ProductCategory(1, 1, 2, category=child)]
        product = Product(product_categories)
        
        assert list(product.parent_category_names) == ["Electronics"]
    
    def test_nested_with_none_handling(self):
        """Handle None in nested paths gracefully."""
        class Product(MockTable):
            def __init__(self, product_categories: List[ProductCategory]):
                self._product_categories = product_categories
            
            @property
            def product_categories(self):
                return self._product_categories
        
        Product.grandparent_names = association_proxy(
            "product_categories",
            "category.parent.parent.name"
        )
        
        # Root category has no parent
        root = Category(1, "Root", "root", parent=None)
        child = Category(2, "Child", "child", parent=root)
        product_categories = [ProductCategory(1, 1, 2, category=child)]
        product = Product(product_categories)
        
        # Should return empty (None grandparent)
        assert list(product.grandparent_names) == []


# =============================================================================
# Test: Combined Read and Write Operations
# =============================================================================

class TestCombinedOperations:
    """Test combined read/write operations."""
    
    def test_add_and_read_tags(self):
        """Add tags then read them back."""
        class Product(MockTable):
            def __init__(self):
                self.id = 1
                self._product_tags = []
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tags = association_proxy(
            "product_tags",
            "tag",
            creator=lambda t: ProductTag(0, 1, t.id, tag=t)
        )
        Product.tag_names = association_proxy("product_tags", "tag.name")
        
        product = Product()
        
        # Add tags
        product.tags.append(Tag(1, "first"))
        product.tags.append(Tag(2, "second"))
        
        # Read back
        assert list(product.tag_names) == ["first", "second"]
    
    def test_modify_tags_multiple_times(self):
        """Modify tags multiple times."""
        class Product(MockTable):
            def __init__(self):
                self.id = 1
                self._product_tags = []
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tags = association_proxy(
            "product_tags",
            "tag",
            creator=lambda t: ProductTag(0, 1, t.id, tag=t)
        )
        
        product = Product()
        
        # Add some tags
        product.tags.extend([Tag(1, "a"), Tag(2, "b")])
        assert len(list(product.tags)) == 2
        
        # Add more
        product.tags.append(Tag(3, "c"))
        assert len(list(product.tags)) == 3
        
        # Clear and add new
        product.tags.clear()
        assert len(list(product.tags)) == 0
        
        product.tags.append(Tag(4, "fresh"))
        assert len(list(product.tags)) == 1


# =============================================================================
# Test: Async Operations
# =============================================================================

class TestAsyncOperations:
    """Test async methods on proxies."""
    
    @pytest.mark.asyncio
    async def test_async_all(self):
        """Test async all() method."""
        class Product(MockTable):
            def __init__(self, product_tags: List[ProductTag]):
                self._product_tags = product_tags
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tags = association_proxy("product_tags", "tag")
        
        product_tags = [ProductTag(i, 1, i, tag=Tag(i, f"tag{i}")) for i in range(3)]
        product = Product(product_tags)
        
        result = await product.tags.all()
        
        assert len(result) == 3
    
    @pytest.mark.asyncio
    async def test_async_first(self):
        """Test async first() method."""
        class Product(MockTable):
            def __init__(self, product_tags: List[ProductTag]):
                self._product_tags = product_tags
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tags = association_proxy("product_tags", "tag")
        
        product_tags = [ProductTag(1, 1, 1, tag=Tag(1, "first_tag"))]
        product = Product(product_tags)
        
        result = await product.tags.first()
        
        assert result.name == "first_tag"
    
    @pytest.mark.asyncio
    async def test_async_filter(self):
        """Test async filter() method."""
        class Product(MockTable):
            def __init__(self, product_tags: List[ProductTag]):
                self._product_tags = product_tags
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tags = association_proxy("product_tags", "tag")
        
        product_tags = [
            ProductTag(1, 1, 1, tag=Tag(1, "sale", "red")),
            ProductTag(2, 1, 2, tag=Tag(2, "featured", "blue")),
            ProductTag(3, 1, 3, tag=Tag(3, "clearance", "red")),
        ]
        product = Product(product_tags)
        
        red_tags = await product.tags.filter(color="red")
        
        assert len(red_tags) == 2
        assert all(t.color == "red" for t in red_tags)


# =============================================================================
# Test: Performance Patterns
# =============================================================================

class TestPerformancePatterns:
    """Test patterns for good performance."""
    
    def test_iterate_once_collect(self):
        """Iterate once and collect for multiple uses."""
        class Product(MockTable):
            def __init__(self, product_tags: List[ProductTag]):
                self._product_tags = product_tags
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tag_names = association_proxy("product_tags", "tag.name")
        
        product_tags = [ProductTag(i, 1, i, tag=Tag(i, f"tag{i}")) for i in range(100)]
        product = Product(product_tags)
        
        # Collect once for multiple operations
        names = product.tag_names.to_list()
        
        assert len(names) == 100
        assert "tag0" in names
        assert "tag99" in names
    
    @pytest.mark.asyncio
    async def test_early_termination_with_first(self):
        """Use first() for early termination."""
        class Product(MockTable):
            access_count = 0
            
            def __init__(self, product_tags: List[ProductTag]):
                self._product_tags = product_tags
            
            @property
            def product_tags(self):
                Product.access_count += 1
                return self._product_tags
        
        Product.tags = association_proxy("product_tags", "tag")
        
        product_tags = [ProductTag(i, 1, i, tag=Tag(i, f"tag{i}")) for i in range(100)]
        product = Product(product_tags)
        Product.access_count = 0
        
        first = await product.tags.first()
        
        assert first.name == "tag0"

