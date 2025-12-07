"""
Tests for scalar association proxy (belongs_to/has_one relationships).

Tests cover:
- Scalar value access
- None handling
- Auto-detection of scalar relationships
- Forced scalar mode
"""

import pytest
from typing import Optional
from dataclasses import dataclass, field


# =============================================================================
# Mock Classes
# =============================================================================

@dataclass
class MockDepartment:
    """Mock department for testing."""
    id: int
    name: str
    code: str
    budget: float = 100000.0


@dataclass
class MockProfile:
    """Mock user profile."""
    id: int
    bio: str
    avatar_url: Optional[str] = None


@dataclass
class MockUser:
    """Mock user with department relationship."""
    id: int
    name: str
    email: str
    department_id: Optional[int] = None
    department: Optional[MockDepartment] = None
    profile: Optional[MockProfile] = None
    _fields: dict = field(default_factory=dict)
    __table_name__: str = "users"


class MockTable:
    """Base mock table."""
    _fields = {}
    __table_name__ = "mock"


from pynext.db.relationships.association_proxy import (
    association_proxy,
    AttributeProxyDescriptor,
    ProxyCollection,
    _traverse_path,
)


# =============================================================================
# Test: Basic Scalar Access
# =============================================================================

class TestScalarBasicAccess:
    """Test basic scalar proxy access."""
    
    def test_access_scalar_attribute(self):
        """Access scalar attribute through belongs_to."""
        class Post(MockTable):
            def __init__(self, author: MockUser):
                self._author = author
            
            @property
            def author(self):
                return self._author
        
        Post.author_name = association_proxy("author", "name", scalar=True)
        
        author = MockUser(1, "Alice", "alice@test.com")
        post = Post(author)
        
        result = post.author_name
        assert result == "Alice"
        assert isinstance(result, str)
    
    def test_access_integer_scalar(self):
        """Access integer attribute."""
        class Employee(MockTable):
            def __init__(self, dept: MockDepartment):
                self._department = dept
            
            @property
            def department(self):
                return self._department
        
        Employee.dept_id = association_proxy("department", "id", scalar=True)
        
        dept = MockDepartment(42, "Engineering", "ENG")
        emp = Employee(dept)
        
        assert emp.dept_id == 42
    
    def test_access_float_scalar(self):
        """Access float attribute."""
        class Employee(MockTable):
            def __init__(self, dept: MockDepartment):
                self._department = dept
            
            @property
            def department(self):
                return self._department
        
        Employee.dept_budget = association_proxy("department", "budget", scalar=True)
        
        dept = MockDepartment(1, "Engineering", "ENG", budget=150000.0)
        emp = Employee(dept)
        
        assert emp.dept_budget == 150000.0
    
    def test_access_nested_scalar(self):
        """Access nested attribute path."""
        @dataclass
        class MockAddress:
            city: str
            country: str
        
        @dataclass
        class MockCompany:
            name: str
            address: MockAddress
        
        class Employee(MockTable):
            def __init__(self, company: MockCompany):
                self._company = company
            
            @property
            def company(self):
                return self._company
        
        Employee.company_city = association_proxy("company", "address.city", scalar=True)
        
        address = MockAddress("San Francisco", "USA")
        company = MockCompany("Acme Corp", address)
        emp = Employee(company)
        
        assert emp.company_city == "San Francisco"


# =============================================================================
# Test: None Handling
# =============================================================================

class TestScalarNoneHandling:
    """Test None handling for scalar proxies."""
    
    def test_none_relationship_returns_none(self):
        """None relationship returns None."""
        class Post(MockTable):
            def __init__(self):
                self._author = None
            
            @property
            def author(self):
                return self._author
        
        Post.author_name = association_proxy("author", "name", scalar=True)
        
        post = Post()
        assert post.author_name is None
    
    def test_none_in_path_returns_none(self):
        """None in nested path returns None."""
        class Employee(MockTable):
            def __init__(self, user: MockUser):
                self._user = user
            
            @property
            def user(self):
                return self._user
        
        Employee.profile_bio = association_proxy("user", "profile.bio", scalar=True)
        
        # User without profile
        user = MockUser(1, "Alice", "a@test.com", profile=None)
        emp = Employee(user)
        
        assert emp.profile_bio is None
    
    def test_missing_attribute_returns_none(self):
        """Missing attribute returns None."""
        class Model(MockTable):
            def __init__(self, obj):
                self._obj = obj
            
            @property
            def obj(self):
                return self._obj
        
        Model.missing = association_proxy("obj", "nonexistent_attr", scalar=True)
        
        model = Model(object())
        assert model.missing is None
    
    def test_none_attribute_value_returns_none(self):
        """Attribute that is None returns None."""
        class Post(MockTable):
            def __init__(self):
                self._profile = MockProfile(1, "Bio", avatar_url=None)
            
            @property
            def profile(self):
                return self._profile
        
        Post.avatar = association_proxy("profile", "avatar_url", scalar=True)
        
        post = Post()
        assert post.avatar is None


# =============================================================================
# Test: Auto-Detection
# =============================================================================

class TestScalarAutoDetection:
    """Test automatic scalar/collection detection."""
    
    def test_single_object_detected_as_scalar(self):
        """Single object is auto-detected as scalar."""
        class Post(MockTable):
            def __init__(self, author: MockUser):
                self._author = author
            
            @property
            def author(self):
                return self._author
        
        # Note: scalar=None (auto-detect)
        Post.author_name = association_proxy("author", "name")
        
        author = MockUser(1, "Alice", "a@test.com")
        post = Post(author)
        
        # Should return string, not ProxyCollection
        result = post.author_name
        assert result == "Alice"
        assert isinstance(result, str)
    
    def test_list_detected_as_collection(self):
        """List is auto-detected as collection."""
        class User(MockTable):
            def __init__(self, posts):
                self._posts = posts
            
            @property
            def posts(self):
                return self._posts
        
        User.post_titles = association_proxy("posts", "title")
        
        posts = [
            type('Post', (), {'title': 'Post 1'})(),
            type('Post', (), {'title': 'Post 2'})(),
        ]
        user = User(posts)
        
        result = user.post_titles
        assert isinstance(result, ProxyCollection)
        assert list(result) == ["Post 1", "Post 2"]
    
    def test_forced_scalar_overrides_detection(self):
        """scalar=True forces scalar mode even for lists."""
        class Model(MockTable):
            def __init__(self, items):
                self._items = items
            
            @property
            def items(self):
                return self._items
        
        # Force scalar mode - will get first item
        Model.first_name = association_proxy("items", "name", scalar=True)
        
        items = [
            type('Item', (), {'name': 'First'})(),
            type('Item', (), {'name': 'Second'})(),
        ]
        model = Model(items)
        
        # Since items is a list, traversing with scalar mode on a list
        # actually returns None (list doesn't have 'name' attr directly)
        # This tests the "forced" behavior
        result = model.first_name
        assert result is None  # List doesn't have .name


# =============================================================================
# Test: Multiple Scalar Proxies
# =============================================================================

class TestMultipleScalarProxies:
    """Test multiple scalar proxies on same class."""
    
    def test_two_proxies_same_source(self):
        """Two proxies can access same source."""
        class Post(MockTable):
            def __init__(self, author: MockUser):
                self._author = author
            
            @property
            def author(self):
                return self._author
        
        Post.author_name = association_proxy("author", "name", scalar=True)
        Post.author_email = association_proxy("author", "email", scalar=True)
        
        author = MockUser(1, "Alice", "alice@test.com")
        post = Post(author)
        
        assert post.author_name == "Alice"
        assert post.author_email == "alice@test.com"
    
    def test_three_proxies_different_sources(self):
        """Multiple proxies to different sources."""
        class Article(MockTable):
            def __init__(self, author: MockUser, dept: MockDepartment):
                self._author = author
                self._department = dept
            
            @property
            def author(self):
                return self._author
            
            @property
            def department(self):
                return self._department
        
        Article.author_name = association_proxy("author", "name", scalar=True)
        Article.dept_name = association_proxy("department", "name", scalar=True)
        Article.dept_code = association_proxy("department", "code", scalar=True)
        
        author = MockUser(1, "Bob", "bob@test.com")
        dept = MockDepartment(2, "Marketing", "MKT")
        article = Article(author, dept)
        
        assert article.author_name == "Bob"
        assert article.dept_name == "Marketing"
        assert article.dept_code == "MKT"


# =============================================================================
# Test: Scalar Set Errors
# =============================================================================

class TestScalarSetErrors:
    """Test that setting scalar proxies gives helpful errors."""
    
    def test_set_scalar_raises_error(self):
        """Setting scalar proxy raises AttributeError."""
        class Post(MockTable):
            def __init__(self, author: MockUser):
                self._author = author
            
            @property
            def author(self):
                return self._author
        
        Post.author_name = association_proxy("author", "name", scalar=True)
        
        author = MockUser(1, "Alice", "a@test.com")
        post = Post(author)
        
        with pytest.raises(AttributeError) as exc_info:
            post.author_name = "Bob"
        
        assert "Cannot set scalar proxy" in str(exc_info.value)
        assert "author" in str(exc_info.value)


# =============================================================================
# Test: Deep Nested Paths
# =============================================================================

class TestScalarDeepPaths:
    """Test deeply nested path traversal."""
    
    def test_three_level_path(self):
        """Three-level path works."""
        @dataclass
        class Level3:
            value: str
        
        @dataclass
        class Level2:
            level3: Level3
        
        @dataclass
        class Level1:
            level2: Level2
        
        class Model(MockTable):
            def __init__(self, l1: Level1):
                self._level1 = l1
            
            @property
            def level1(self):
                return self._level1
        
        Model.deep_value = association_proxy("level1", "level2.level3.value", scalar=True)
        
        l3 = Level3("deep!")
        l2 = Level2(l3)
        l1 = Level1(l2)
        model = Model(l1)
        
        assert model.deep_value == "deep!"
    
    def test_four_level_path(self):
        """Four-level path works."""
        @dataclass
        class L4:
            data: int
        
        @dataclass
        class L3:
            l4: L4
        
        @dataclass
        class L2:
            l3: L3
        
        @dataclass
        class L1:
            l2: L2
        
        class Model(MockTable):
            def __init__(self, l1: L1):
                self._l1 = l1
            
            @property
            def l1(self):
                return self._l1
        
        Model.data = association_proxy("l1", "l2.l3.l4.data", scalar=True)
        
        l4 = L4(42)
        l3 = L3(l4)
        l2 = L2(l3)
        l1 = L1(l2)
        model = Model(l1)
        
        assert model.data == 42
    
    def test_none_at_any_level_returns_none(self):
        """None at any level returns None."""
        @dataclass
        class Level3:
            value: str
        
        @dataclass
        class Level2:
            level3: Optional[Level3]
        
        @dataclass
        class Level1:
            level2: Level2
        
        class Model(MockTable):
            def __init__(self, l1: Level1):
                self._level1 = l1
            
            @property
            def level1(self):
                return self._level1
        
        Model.deep_value = association_proxy("level1", "level2.level3.value", scalar=True)
        
        l2 = Level2(level3=None)  # None at level 3
        l1 = Level1(l2)
        model = Model(l1)
        
        assert model.deep_value is None


# =============================================================================
# Test: Different Data Types
# =============================================================================

class TestScalarDataTypes:
    """Test scalar proxy with different data types."""
    
    def test_string_type(self):
        """String attribute works."""
        class Model(MockTable):
            def __init__(self):
                self._obj = type('Obj', (), {'text': 'hello'})()
            
            @property
            def obj(self):
                return self._obj
        
        Model.text = association_proxy("obj", "text", scalar=True)
        
        assert Model().text == "hello"
    
    def test_int_type(self):
        """Integer attribute works."""
        class Model(MockTable):
            def __init__(self):
                self._obj = type('Obj', (), {'num': 42})()
            
            @property
            def obj(self):
                return self._obj
        
        Model.num = association_proxy("obj", "num", scalar=True)
        
        assert Model().num == 42
    
    def test_float_type(self):
        """Float attribute works."""
        class Model(MockTable):
            def __init__(self):
                self._obj = type('Obj', (), {'val': 3.14})()
            
            @property
            def obj(self):
                return self._obj
        
        Model.val = association_proxy("obj", "val", scalar=True)
        
        assert Model().val == 3.14
    
    def test_bool_type(self):
        """Boolean attribute works."""
        class Model(MockTable):
            def __init__(self):
                self._obj = type('Obj', (), {'flag': True})()
            
            @property
            def obj(self):
                return self._obj
        
        Model.flag = association_proxy("obj", "flag", scalar=True)
        
        assert Model().flag is True
    
    def test_list_type(self):
        """List attribute works (returns the list, not items)."""
        class Model(MockTable):
            def __init__(self):
                self._obj = type('Obj', (), {'items': [1, 2, 3]})()
            
            @property
            def obj(self):
                return self._obj
        
        Model.items = association_proxy("obj", "items", scalar=True)
        
        assert Model().items == [1, 2, 3]
    
    def test_dict_type(self):
        """Dict attribute works."""
        class Model(MockTable):
            def __init__(self):
                self._obj = type('Obj', (), {'data': {'key': 'value'}})()
            
            @property
            def obj(self):
                return self._obj
        
        Model.data = association_proxy("obj", "data", scalar=True)
        
        assert Model().data == {'key': 'value'}


# =============================================================================
# Test: Repeated Access
# =============================================================================

class TestScalarRepeatedAccess:
    """Test repeated access to scalar proxies."""
    
    def test_consistent_results(self):
        """Repeated access returns same value."""
        class Post(MockTable):
            def __init__(self):
                self._author = MockUser(1, "Alice", "a@test.com")
            
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
                self._author = MockUser(1, "Alice", "a@test.com")
            
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
        post.author = MockUser(2, "Bob", "b@test.com")
        assert post.author_name == "Bob"


# =============================================================================
# Test: Class-Level Access
# =============================================================================

class TestScalarClassAccess:
    """Test accessing proxy at class level."""
    
    def test_class_access_returns_descriptor(self):
        """Accessing on class returns descriptor."""
        class Post(MockTable):
            author = None
        
        Post.author_name = association_proxy("author", "name", scalar=True)
        
        result = Post.author_name
        assert isinstance(result, AttributeProxyDescriptor)
    
    def test_descriptor_has_correct_attrs(self):
        """Descriptor has correct attributes."""
        class Post(MockTable):
            author = None
        
        Post.author_name = association_proxy("author", "name", scalar=True)
        
        descriptor = Post.author_name
        assert descriptor.target_collection == "author"
        assert descriptor.attr == "name"
        assert descriptor._scalar is True


# =============================================================================
# Test: Edge Cases
# =============================================================================

class TestScalarEdgeCases:
    """Edge cases for scalar proxies."""
    
    def test_empty_string_value(self):
        """Empty string is returned correctly."""
        class Model(MockTable):
            def __init__(self):
                self._obj = type('Obj', (), {'name': ''})()
            
            @property
            def obj(self):
                return self._obj
        
        Model.name = association_proxy("obj", "name", scalar=True)
        
        assert Model().name == ""
    
    def test_zero_value(self):
        """Zero is returned correctly."""
        class Model(MockTable):
            def __init__(self):
                self._obj = type('Obj', (), {'count': 0})()
            
            @property
            def obj(self):
                return self._obj
        
        Model.count = association_proxy("obj", "count", scalar=True)
        
        assert Model().count == 0
    
    def test_false_value(self):
        """False is returned correctly (not confused with None)."""
        class Model(MockTable):
            def __init__(self):
                self._obj = type('Obj', (), {'active': False})()
            
            @property
            def obj(self):
                return self._obj
        
        Model.active = association_proxy("obj", "active", scalar=True)
        
        result = Model().active
        assert result is False
        assert result is not None
    
    def test_object_as_value(self):
        """Object attribute returns the object."""
        @dataclass
        class InnerObj:
            value: int
        
        class Model(MockTable):
            def __init__(self):
                self._obj = type('Obj', (), {'inner': InnerObj(42)})()
            
            @property
            def obj(self):
                return self._obj
        
        Model.inner = association_proxy("obj", "inner", scalar=True)
        
        result = Model().inner
        assert isinstance(result, InnerObj)
        assert result.value == 42

