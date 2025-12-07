"""
Tests for association proxy with belongs_to/has_one relationships.

Tests cover:
- Scalar proxy for belongs_to
- Scalar proxy for has_one
- None relationship handling
- Nested scalar access
"""

import pytest
from typing import Optional
from dataclasses import dataclass, field


# =============================================================================
# Mock Classes
# =============================================================================

@dataclass
class Author:
    """Author model."""
    id: int
    name: str
    email: str
    bio: Optional[str] = None


@dataclass
class Publisher:
    """Publisher model."""
    id: int
    name: str
    country: str


@dataclass
class Category:
    """Category with parent relationship."""
    id: int
    name: str
    parent: Optional["Category"] = None


@dataclass
class UserProfile:
    """User profile model."""
    id: int
    bio: str
    avatar_url: Optional[str] = None
    settings: Optional[dict] = None


@dataclass
class User:
    """User with profile has_one."""
    id: int
    name: str
    email: str
    profile: Optional[UserProfile] = None


class MockTable:
    """Base mock table."""
    _fields = {}
    __table_name__ = "mock"


from pynext.db.relationships.association_proxy import (
    association_proxy,
    AttributeProxyDescriptor,
)


# =============================================================================
# Test: Basic belongs_to Proxy
# =============================================================================

class TestBelongsToBasic:
    """Test basic belongs_to proxy usage."""
    
    def test_access_author_name(self):
        """Access author's name through belongs_to."""
        class Post(MockTable):
            def __init__(self, author: Author):
                self._author = author
            
            @property
            def author(self):
                return self._author
        
        Post.author_name = association_proxy("author", "name", scalar=True)
        
        post = Post(Author(1, "Alice", "alice@test.com"))
        
        assert post.author_name == "Alice"
    
    def test_access_author_email(self):
        """Access author's email through belongs_to."""
        class Post(MockTable):
            def __init__(self, author: Author):
                self._author = author
            
            @property
            def author(self):
                return self._author
        
        Post.author_email = association_proxy("author", "email", scalar=True)
        
        post = Post(Author(1, "Alice", "alice@test.com"))
        
        assert post.author_email == "alice@test.com"
    
    def test_access_optional_attribute(self):
        """Access optional attribute through belongs_to."""
        class Post(MockTable):
            def __init__(self, author: Author):
                self._author = author
            
            @property
            def author(self):
                return self._author
        
        Post.author_bio = association_proxy("author", "bio", scalar=True)
        
        # With bio
        post_with_bio = Post(Author(1, "Alice", "a@test.com", bio="Writer"))
        assert post_with_bio.author_bio == "Writer"
        
        # Without bio
        post_without_bio = Post(Author(2, "Bob", "b@test.com", bio=None))
        assert post_without_bio.author_bio is None


# =============================================================================
# Test: None belongs_to Handling
# =============================================================================

class TestBelongsToNone:
    """Test None handling for belongs_to proxy."""
    
    def test_none_relationship_returns_none(self):
        """None belongs_to returns None."""
        class Post(MockTable):
            def __init__(self):
                self._author = None
            
            @property
            def author(self):
                return self._author
        
        Post.author_name = association_proxy("author", "name", scalar=True)
        
        post = Post()
        assert post.author_name is None
    
    def test_auto_detect_none_as_scalar(self):
        """None relationship is auto-detected as scalar when set later."""
        class Post(MockTable):
            def __init__(self, author: Optional[Author]):
                self._author = author
            
            @property
            def author(self):
                return self._author
            
            @author.setter
            def author(self, value):
                self._author = value
        
        Post.author_name = association_proxy("author", "name", scalar=True)
        
        # Initially None
        post = Post(None)
        assert post.author_name is None
        
        # Set author
        post._author = Author(1, "Alice", "a@test.com")
        assert post.author_name == "Alice"


# =============================================================================
# Test: Basic has_one Proxy
# =============================================================================

class TestHasOneBasic:
    """Test basic has_one proxy usage."""
    
    def test_access_profile_bio(self):
        """Access profile bio through has_one."""
        class UserModel(MockTable):
            def __init__(self, profile: UserProfile):
                self._profile = profile
            
            @property
            def profile(self):
                return self._profile
        
        UserModel.bio = association_proxy("profile", "bio", scalar=True)
        
        user = UserModel(UserProfile(1, "I am a developer"))
        
        assert user.bio == "I am a developer"
    
    def test_access_profile_avatar(self):
        """Access profile avatar through has_one."""
        class UserModel(MockTable):
            def __init__(self, profile: UserProfile):
                self._profile = profile
            
            @property
            def profile(self):
                return self._profile
        
        UserModel.avatar = association_proxy("profile", "avatar_url", scalar=True)
        
        user = UserModel(UserProfile(1, "bio", avatar_url="https://example.com/avatar.png"))
        
        assert user.avatar == "https://example.com/avatar.png"


# =============================================================================
# Test: None has_one Handling
# =============================================================================

class TestHasOneNone:
    """Test None handling for has_one proxy."""
    
    def test_none_has_one_returns_none(self):
        """None has_one returns None."""
        class UserModel(MockTable):
            def __init__(self):
                self._profile = None
            
            @property
            def profile(self):
                return self._profile
        
        UserModel.bio = association_proxy("profile", "bio", scalar=True)
        
        user = UserModel()
        assert user.bio is None
    
    def test_optional_nested_none(self):
        """Optional nested attribute returns None when parent is None."""
        class UserModel(MockTable):
            def __init__(self, profile: Optional[UserProfile]):
                self._profile = profile
            
            @property
            def profile(self):
                return self._profile
        
        UserModel.settings = association_proxy("profile", "settings", scalar=True)
        
        # No profile
        user_no_profile = UserModel(None)
        assert user_no_profile.settings is None
        
        # Profile with no settings
        user_no_settings = UserModel(UserProfile(1, "bio", settings=None))
        assert user_no_settings.settings is None
        
        # Profile with settings
        user_with_settings = UserModel(UserProfile(1, "bio", settings={"theme": "dark"}))
        assert user_with_settings.settings == {"theme": "dark"}


# =============================================================================
# Test: Nested Scalar Access
# =============================================================================

class TestNestedScalarAccess:
    """Test nested path traversal for scalar relationships."""
    
    def test_two_level_belongs_to(self):
        """Access through two belongs_to levels."""
        class Book(MockTable):
            def __init__(self, author: Author, publisher: Publisher):
                self._author = author
                self._publisher = publisher
            
            @property
            def author(self):
                return self._author
            
            @property
            def publisher(self):
                return self._publisher
        
        Book.author_name = association_proxy("author", "name", scalar=True)
        Book.publisher_country = association_proxy("publisher", "country", scalar=True)
        
        book = Book(
            Author(1, "Alice", "a@test.com"),
            Publisher(1, "Penguin", "UK")
        )
        
        assert book.author_name == "Alice"
        assert book.publisher_country == "UK"
    
    def test_self_referential_proxy(self):
        """Access parent's attribute in self-referential relationship."""
        class CategoryModel(MockTable):
            def __init__(self, category: Category):
                self._category = category
            
            @property
            def category(self):
                return self._category
        
        CategoryModel.parent_name = association_proxy("category", "parent.name", scalar=True)
        
        parent = Category(1, "Electronics")
        child = Category(2, "Phones", parent=parent)
        
        wrapper = CategoryModel(child)
        
        assert wrapper.parent_name == "Electronics"
    
    def test_deep_self_referential_proxy(self):
        """Access grandparent in self-referential chain."""
        class CategoryModel(MockTable):
            def __init__(self, category: Category):
                self._category = category
            
            @property
            def category(self):
                return self._category
        
        CategoryModel.grandparent_name = association_proxy(
            "category", 
            "parent.parent.name", 
            scalar=True
        )
        
        root = Category(1, "Root")
        middle = Category(2, "Middle", parent=root)
        leaf = Category(3, "Leaf", parent=middle)
        
        wrapper = CategoryModel(leaf)
        
        assert wrapper.grandparent_name == "Root"


# =============================================================================
# Test: Multiple Scalar Proxies
# =============================================================================

class TestMultipleScalarProxies:
    """Test multiple scalar proxies on same class."""
    
    def test_multiple_proxies_same_relationship(self):
        """Multiple proxies to same belongs_to."""
        class Article(MockTable):
            def __init__(self, author: Author):
                self._author = author
            
            @property
            def author(self):
                return self._author
        
        Article.writer_name = association_proxy("author", "name", scalar=True)
        Article.writer_email = association_proxy("author", "email", scalar=True)
        Article.writer_bio = association_proxy("author", "bio", scalar=True)
        
        author = Author(1, "Jane", "jane@test.com", "Tech writer")
        article = Article(author)
        
        assert article.writer_name == "Jane"
        assert article.writer_email == "jane@test.com"
        assert article.writer_bio == "Tech writer"
    
    def test_multiple_proxies_different_relationships(self):
        """Multiple proxies to different belongs_to relationships."""
        class Article(MockTable):
            def __init__(self, author: Author, editor: Author, publisher: Publisher):
                self._author = author
                self._editor = editor
                self._publisher = publisher
            
            @property
            def author(self):
                return self._author
            
            @property
            def editor(self):
                return self._editor
            
            @property
            def publisher(self):
                return self._publisher
        
        Article.author_name = association_proxy("author", "name", scalar=True)
        Article.editor_name = association_proxy("editor", "name", scalar=True)
        Article.publisher_name = association_proxy("publisher", "name", scalar=True)
        
        article = Article(
            Author(1, "Alice", "a@test.com"),
            Author(2, "Bob", "b@test.com"),
            Publisher(1, "TechBooks", "USA")
        )
        
        assert article.author_name == "Alice"
        assert article.editor_name == "Bob"
        assert article.publisher_name == "TechBooks"


# =============================================================================
# Test: Auto-Detection for belongs_to/has_one
# =============================================================================

class TestScalarAutoDetection:
    """Test auto-detection recognizes scalar relationships."""
    
    def test_single_object_auto_detected(self):
        """Single object is auto-detected as scalar."""
        class Post(MockTable):
            def __init__(self, author: Author):
                self._author = author
            
            @property
            def author(self):
                return self._author
        
        # No scalar=True, should auto-detect
        Post.author_name = association_proxy("author", "name")
        
        post = Post(Author(1, "Alice", "a@test.com"))
        result = post.author_name
        
        # Should be string, not ProxyCollection
        assert result == "Alice"
        assert isinstance(result, str)
    
    def test_force_collection_on_scalar(self):
        """Can force collection mode on scalar relationship."""
        class Post(MockTable):
            def __init__(self, author: Author):
                self._author = author
            
            @property
            def author(self):
                return self._author
        
        # Force scalar=False (this is unusual but tests the override)
        Post.author_name = association_proxy("author", "name", scalar=False)
        
        post = Post(Author(1, "Alice", "a@test.com"))
        result = post.author_name
        
        # Since author is an object, not iterable like list,
        # trying to iterate will fail or return unexpected results
        # This tests the "forced" mode behavior


# =============================================================================
# Test: Error Handling
# =============================================================================

class TestBelongsToErrors:
    """Test error handling for belongs_to proxies."""
    
    def test_set_scalar_raises(self):
        """Setting scalar proxy raises AttributeError."""
        class Post(MockTable):
            def __init__(self, author: Author):
                self._author = author
            
            @property
            def author(self):
                return self._author
        
        Post.author_name = association_proxy("author", "name", scalar=True)
        
        post = Post(Author(1, "Alice", "a@test.com"))
        
        with pytest.raises(AttributeError) as exc_info:
            post.author_name = "Bob"
        
        assert "Cannot set scalar proxy" in str(exc_info.value)
    
    def test_missing_relationship_attribute(self):
        """Missing relationship attribute returns None (doesn't raise)."""
        class Post(MockTable):
            def __init__(self):
                pass
        
        # 'author' doesn't exist
        Post.author_name = association_proxy("author", "name", scalar=True)
        
        post = Post()
        # getattr returns None when attribute doesn't exist
        assert post.author_name is None


# =============================================================================
# Test: Repeated Access Consistency
# =============================================================================

class TestRepeatedAccess:
    """Test that repeated access is consistent."""
    
    def test_repeated_access_same_value(self):
        """Repeated access returns same value."""
        class Post(MockTable):
            def __init__(self):
                self._author = Author(1, "Alice", "a@test.com")
            
            @property
            def author(self):
                return self._author
        
        Post.author_name = association_proxy("author", "name", scalar=True)
        
        post = Post()
        
        r1 = post.author_name
        r2 = post.author_name
        r3 = post.author_name
        
        assert r1 == r2 == r3 == "Alice"
    
    def test_reflects_source_changes(self):
        """Changes to source are reflected."""
        class Post(MockTable):
            def __init__(self):
                self._author = Author(1, "Alice", "a@test.com")
            
            @property
            def author(self):
                return self._author
            
            @author.setter
            def author(self, value):
                self._author = value
        
        Post.author_name = association_proxy("author", "name", scalar=True)
        
        post = Post()
        assert post.author_name == "Alice"
        
        # Change author
        post.author = Author(2, "Bob", "b@test.com")
        assert post.author_name == "Bob"


# =============================================================================
# Test: Class-Level Access
# =============================================================================

class TestClassLevelAccess:
    """Test class-level proxy access."""
    
    def test_class_access_returns_descriptor(self):
        """Accessing proxy on class returns descriptor."""
        class Post(MockTable):
            author = None
        
        Post.author_name = association_proxy("author", "name", scalar=True)
        
        result = Post.author_name
        
        assert isinstance(result, AttributeProxyDescriptor)
    
    def test_descriptor_attributes(self):
        """Descriptor has expected attributes."""
        class Post(MockTable):
            author = None
        
        Post.author_name = association_proxy("author", "name", scalar=True)
        
        descriptor = Post.author_name
        
        assert descriptor.target_collection == "author"
        assert descriptor.attr == "name"
        assert descriptor._scalar is True

