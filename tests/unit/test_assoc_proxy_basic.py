"""
Tests for association_proxy basic functionality.

Tests cover:
- Basic proxy creation and access
- Simple path traversal
- Descriptor behavior
- Type detection
- Basic iteration
"""

import pytest
from typing import List, Optional
from dataclasses import dataclass, field


# =============================================================================
# Mock Classes for Testing
# =============================================================================

@dataclass
class MockCourse:
    """Mock course model for testing."""
    id: int
    name: str
    credits: int = 3
    active: bool = True


@dataclass
class MockEnrollment:
    """Mock enrollment junction model."""
    id: int
    student_id: int
    course_id: int
    course: Optional[MockCourse] = None
    grade: Optional[str] = None


@dataclass
class MockDepartment:
    """Mock department for scalar proxy testing."""
    id: int
    name: str
    code: str


@dataclass
class MockUser:
    """Mock user model for testing."""
    id: int
    name: str
    email: str
    department_id: Optional[int] = None
    department: Optional[MockDepartment] = None
    _fields: dict = field(default_factory=dict)
    __table_name__: str = "users"


class MockTable:
    """Base mock table that looks like a PyNext Table."""
    _fields = {}
    __table_name__ = "mock_table"


class MockStudent(MockTable):
    """Mock student model with enrollments."""
    
    def __init__(self, student_id: int, name: str):
        self.id = student_id
        self.name = name
        self._enrollments: List[MockEnrollment] = []
    
    @property
    def enrollments(self):
        return self._enrollments
    
    @enrollments.setter
    def enrollments(self, value):
        self._enrollments = value


# =============================================================================
# Import the association_proxy
# =============================================================================

from pynext.db.relationships.association_proxy import (
    association_proxy,
    AttributeProxyDescriptor,
    ProxyCollection,
    _traverse_path,
    _is_collection_type,
)


# =============================================================================
# Test: association_proxy Function
# =============================================================================

class TestAssociationProxyFunction:
    """Test the association_proxy() function itself."""
    
    def test_creates_descriptor(self):
        """association_proxy returns a descriptor."""
        descriptor = association_proxy("enrollments", "course")
        assert isinstance(descriptor, AttributeProxyDescriptor)
    
    def test_stores_target_collection(self):
        """Descriptor stores target_collection parameter."""
        descriptor = association_proxy("enrollments", "course")
        assert descriptor.target_collection == "enrollments"
    
    def test_stores_attr(self):
        """Descriptor stores attr parameter."""
        descriptor = association_proxy("enrollments", "course.name")
        assert descriptor.attr == "course.name"
    
    def test_stores_creator(self):
        """Descriptor stores creator function."""
        creator = lambda x: x
        descriptor = association_proxy("enrollments", "course", creator=creator)
        assert descriptor.creator is creator
    
    def test_stores_scalar_flag(self):
        """Descriptor stores scalar flag."""
        descriptor = association_proxy("department", "name", scalar=True)
        assert descriptor._scalar is True
    
    def test_stores_flatten_flag(self):
        """Descriptor stores flatten flag."""
        descriptor = association_proxy("roles", "permissions", flatten=True)
        assert descriptor.flatten is True
    
    def test_default_scalar_is_none(self):
        """Default scalar is None for auto-detection."""
        descriptor = association_proxy("enrollments", "course")
        assert descriptor._scalar is None
    
    def test_default_flatten_is_false(self):
        """Default flatten is False."""
        descriptor = association_proxy("enrollments", "course")
        assert descriptor.flatten is False
    
    def test_default_creator_is_none(self):
        """Default creator is None."""
        descriptor = association_proxy("enrollments", "course")
        assert descriptor.creator is None


class TestAssociationProxyAliases:
    """Test the convenience aliases."""
    
    def test_proxy_alias_exists(self):
        """The 'proxy' alias is available."""
        from pynext.db.relationships.association_proxy import proxy
        descriptor = proxy("enrollments", "course")
        assert isinstance(descriptor, AttributeProxyDescriptor)
    
    def test_attr_proxy_alias_exists(self):
        """The 'attr_proxy' alias is available."""
        from pynext.db.relationships.association_proxy import attr_proxy
        descriptor = attr_proxy("enrollments", "course")
        assert isinstance(descriptor, AttributeProxyDescriptor)


# =============================================================================
# Test: AttributeProxyDescriptor
# =============================================================================

class TestAttributeProxyDescriptor:
    """Test the AttributeProxyDescriptor class."""
    
    def test_init_stores_all_params(self):
        """__init__ stores all parameters correctly."""
        creator = lambda x: x
        descriptor = AttributeProxyDescriptor(
            target_collection="enrollments",
            attr="course.name",
            creator=creator,
            scalar=True,
            flatten=True,
        )
        assert descriptor.target_collection == "enrollments"
        assert descriptor.attr == "course.name"
        assert descriptor.creator is creator
        assert descriptor._scalar is True
        assert descriptor.flatten is True
    
    def test_set_name_stores_name(self):
        """__set_name__ stores the attribute name."""
        descriptor = AttributeProxyDescriptor("enrollments", "course")
        descriptor.__set_name__(MockStudent, "courses")
        assert descriptor._name == "courses"
    
    def test_set_name_stores_owner_class(self):
        """__set_name__ stores the owner class."""
        descriptor = AttributeProxyDescriptor("enrollments", "course")
        descriptor.__set_name__(MockStudent, "courses")
        assert descriptor._owner_class is MockStudent
    
    def test_get_on_class_returns_descriptor(self):
        """Accessing on class returns the descriptor itself."""
        
        class TestModel(MockTable):
            enrollments = []
            courses = association_proxy("enrollments", "course")
        
        result = TestModel.courses
        assert isinstance(result, AttributeProxyDescriptor)
    
    def test_repr_without_creator(self):
        """__repr__ works without creator."""
        descriptor = AttributeProxyDescriptor("enrollments", "course.name")
        result = repr(descriptor)
        assert "enrollments" in result
        assert "course.name" in result
        assert "creator" not in result
    
    def test_repr_with_creator(self):
        """__repr__ includes creator indication."""
        descriptor = AttributeProxyDescriptor(
            "enrollments", "course", creator=lambda x: x
        )
        result = repr(descriptor)
        assert "creator" in result


# =============================================================================
# Test: Path Traversal Helper
# =============================================================================

class TestTraversePath:
    """Test the _traverse_path helper function."""
    
    def test_single_level_path(self):
        """Traverse single attribute."""
        course = MockCourse(id=1, name="Math")
        result = _traverse_path(course, "name")
        assert result == "Math"
    
    def test_two_level_path(self):
        """Traverse two-level path."""
        course = MockCourse(id=1, name="Math")
        enrollment = MockEnrollment(id=1, student_id=1, course_id=1, course=course)
        result = _traverse_path(enrollment, "course.name")
        assert result == "Math"
    
    def test_three_level_path(self):
        """Traverse three-level path."""
        dept = MockDepartment(id=1, name="Science", code="SCI")
        user = MockUser(id=1, name="Alice", email="a@test.com", department=dept)
        
        # Create mock post with author
        @dataclass
        class MockPost:
            author: MockUser
        
        post = MockPost(author=user)
        result = _traverse_path(post, "author.department.name")
        assert result == "Science"
    
    def test_none_object_returns_none(self):
        """None object returns None."""
        result = _traverse_path(None, "name")
        assert result is None
    
    def test_none_in_chain_returns_none(self):
        """None in the middle of chain returns None."""
        enrollment = MockEnrollment(id=1, student_id=1, course_id=1, course=None)
        result = _traverse_path(enrollment, "course.name")
        assert result is None
    
    def test_missing_attribute_returns_none(self):
        """Missing attribute returns None."""
        course = MockCourse(id=1, name="Math")
        result = _traverse_path(course, "nonexistent")
        assert result is None
    
    def test_empty_path(self):
        """Empty path returns original object."""
        course = MockCourse(id=1, name="Math")
        result = _traverse_path(course, "")
        assert result == course
    
    def test_id_attribute(self):
        """Traverse to id attribute."""
        course = MockCourse(id=42, name="Math")
        result = _traverse_path(course, "id")
        assert result == 42
    
    def test_boolean_attribute(self):
        """Traverse to boolean attribute."""
        course = MockCourse(id=1, name="Math", active=True)
        result = _traverse_path(course, "active")
        assert result is True
    
    def test_integer_attribute(self):
        """Traverse to integer attribute."""
        course = MockCourse(id=1, name="Math", credits=4)
        result = _traverse_path(course, "credits")
        assert result == 4


# =============================================================================
# Test: Collection Type Detection
# =============================================================================

class TestIsCollectionType:
    """Test the _is_collection_type helper."""
    
    def test_list_is_collection(self):
        """List is detected as collection."""
        assert _is_collection_type([1, 2, 3]) is True
    
    def test_tuple_is_collection(self):
        """Tuple is detected as collection."""
        assert _is_collection_type((1, 2, 3)) is True
    
    def test_set_is_collection(self):
        """Set is detected as collection."""
        assert _is_collection_type({1, 2, 3}) is True
    
    def test_none_is_not_collection(self):
        """None is not a collection."""
        assert _is_collection_type(None) is False
    
    def test_string_is_not_collection(self):
        """String is not treated as collection."""
        assert _is_collection_type("hello") is False
    
    def test_table_instance_is_not_collection(self):
        """Table instance is not a collection."""
        user = MockUser(id=1, name="Alice", email="a@test.com")
        assert _is_collection_type(user) is False
    
    def test_empty_list_is_collection(self):
        """Empty list is still a collection."""
        assert _is_collection_type([]) is True


# =============================================================================
# Test: Basic Proxy Access
# =============================================================================

class TestBasicProxyAccess:
    """Test basic proxy access patterns."""
    
    def test_access_simple_attribute(self):
        """Access simple attribute through proxy."""
        # Create test data
        student = MockStudent(1, "Alice")
        course1 = MockCourse(id=1, name="Math")
        course2 = MockCourse(id=2, name="Physics")
        student._enrollments = [
            MockEnrollment(1, 1, 1, course=course1),
            MockEnrollment(2, 1, 2, course=course2),
        ]
        
        # Create proxy
        class StudentWithProxy(MockTable):
            def __init__(self, student):
                self._student = student
                self.id = student.id
                self.name = student.name
                self._enrollments = student._enrollments
            
            @property
            def enrollments(self):
                return self._enrollments
        
        StudentWithProxy.course_names = association_proxy("enrollments", "course.name")
        
        student_proxy = StudentWithProxy(student)
        result = student_proxy.course_names
        
        # Should return ProxyCollection
        assert isinstance(result, ProxyCollection)
        assert list(result) == ["Math", "Physics"]
    
    def test_access_object_attribute(self):
        """Access full objects through proxy."""
        student = MockStudent(1, "Alice")
        course1 = MockCourse(id=1, name="Math")
        course2 = MockCourse(id=2, name="Physics")
        student._enrollments = [
            MockEnrollment(1, 1, 1, course=course1),
            MockEnrollment(2, 1, 2, course=course2),
        ]
        
        class StudentWithProxy(MockTable):
            def __init__(self, student):
                self.id = student.id
                self._enrollments = student._enrollments
            
            @property
            def enrollments(self):
                return self._enrollments
        
        StudentWithProxy.courses = association_proxy("enrollments", "course")
        
        student_proxy = StudentWithProxy(student)
        result = student_proxy.courses
        
        assert isinstance(result, ProxyCollection)
        courses = list(result)
        assert len(courses) == 2
        assert courses[0] is course1
        assert courses[1] is course2
    
    def test_empty_collection_returns_empty(self):
        """Empty source collection returns empty proxy."""
        class EmptyStudent(MockTable):
            def __init__(self):
                self._enrollments = []
            
            @property
            def enrollments(self):
                return self._enrollments
        
        EmptyStudent.course_names = association_proxy("enrollments", "course.name")
        
        student = EmptyStudent()
        result = student.course_names
        
        assert isinstance(result, ProxyCollection)
        assert list(result) == []
        assert len(result) == 0


class TestProxyWithNoneValues:
    """Test proxy behavior with None values in the chain."""
    
    def test_none_intermediate_skipped(self):
        """None intermediate values are skipped."""
        class StudentWithNulls(MockTable):
            def __init__(self):
                self._enrollments = [
                    MockEnrollment(1, 1, 1, course=MockCourse(1, "Math")),
                    MockEnrollment(2, 1, 2, course=None),  # No course!
                    MockEnrollment(3, 1, 3, course=MockCourse(3, "Physics")),
                ]
            
            @property
            def enrollments(self):
                return self._enrollments
        
        StudentWithNulls.course_names = association_proxy("enrollments", "course.name")
        
        student = StudentWithNulls()
        result = list(student.course_names)
        
        # Should skip the None course
        assert result == ["Math", "Physics"]
    
    def test_none_source_returns_empty(self):
        """None source relationship returns empty collection."""
        class StudentNoEnrollments(MockTable):
            enrollments = None
        
        StudentNoEnrollments.course_names = association_proxy("enrollments", "course.name")
        
        student = StudentNoEnrollments()
        result = student.course_names
        
        assert isinstance(result, ProxyCollection)
        assert list(result) == []


class TestProxyReturnTypes:
    """Test that proxies return correct types."""
    
    def test_string_attribute_returns_strings(self):
        """String attributes return list of strings."""
        class Model(MockTable):
            def __init__(self):
                self._items = [
                    type('Item', (), {'name': 'Alice'})(),
                    type('Item', (), {'name': 'Bob'})(),
                ]
            
            @property
            def items(self):
                return self._items
        
        Model.names = association_proxy("items", "name")
        
        model = Model()
        result = list(model.names)
        
        assert result == ["Alice", "Bob"]
        assert all(isinstance(name, str) for name in result)
    
    def test_integer_attribute_returns_integers(self):
        """Integer attributes return list of integers."""
        class Model(MockTable):
            def __init__(self):
                self._items = [
                    type('Item', (), {'count': 10})(),
                    type('Item', (), {'count': 20})(),
                ]
            
            @property
            def items(self):
                return self._items
        
        Model.counts = association_proxy("items", "count")
        
        model = Model()
        result = list(model.counts)
        
        assert result == [10, 20]
        assert all(isinstance(count, int) for count in result)
    
    def test_boolean_attribute_returns_booleans(self):
        """Boolean attributes return list of booleans."""
        class Model(MockTable):
            def __init__(self):
                self._items = [
                    type('Item', (), {'active': True})(),
                    type('Item', (), {'active': False})(),
                ]
            
            @property
            def items(self):
                return self._items
        
        Model.actives = association_proxy("items", "active")
        
        model = Model()
        result = list(model.actives)
        
        assert result == [True, False]


# =============================================================================
# Test: Descriptor Name Resolution
# =============================================================================

class TestDescriptorNameResolution:
    """Test that descriptor names are properly set."""
    
    def test_name_set_from_class_attribute(self):
        """Descriptor name is set from class attribute."""
        class Model(MockTable):
            enrollments = []
            courses = association_proxy("enrollments", "course")
        
        descriptor = Model.__dict__["courses"]
        assert descriptor._name == "courses"
    
    def test_owner_class_set(self):
        """Descriptor owner class is set."""
        class Model(MockTable):
            enrollments = []
            courses = association_proxy("enrollments", "course")
        
        descriptor = Model.__dict__["courses"]
        assert descriptor._owner_class is Model


# =============================================================================
# Test: Multiple Proxies on Same Class
# =============================================================================

class TestMultipleProxies:
    """Test multiple proxies on the same class."""
    
    def test_multiple_proxies_independent(self):
        """Multiple proxies work independently."""
        class Model(MockTable):
            def __init__(self):
                self._enrollments = [
                    MockEnrollment(1, 1, 1, course=MockCourse(1, "Math", 3)),
                    MockEnrollment(2, 1, 2, course=MockCourse(2, "Physics", 4)),
                ]
            
            @property
            def enrollments(self):
                return self._enrollments
        
        Model.course_names = association_proxy("enrollments", "course.name")
        Model.course_credits = association_proxy("enrollments", "course.credits")
        
        model = Model()
        
        names = list(model.course_names)
        credits = list(model.course_credits)
        
        assert names == ["Math", "Physics"]
        assert credits == [3, 4]
    
    def test_three_proxies_on_same_source(self):
        """Three proxies can access same source collection."""
        class Model(MockTable):
            def __init__(self):
                self._items = [
                    type('Item', (), {'a': 1, 'b': 'x', 'c': True})(),
                    type('Item', (), {'a': 2, 'b': 'y', 'c': False})(),
                ]
            
            @property
            def items(self):
                return self._items
        
        Model.a_values = association_proxy("items", "a")
        Model.b_values = association_proxy("items", "b")
        Model.c_values = association_proxy("items", "c")
        
        model = Model()
        
        assert list(model.a_values) == [1, 2]
        assert list(model.b_values) == ["x", "y"]
        assert list(model.c_values) == [True, False]


# =============================================================================
# Test: Proxy Consistency
# =============================================================================

class TestProxyConsistency:
    """Test that proxy results are consistent."""
    
    def test_repeated_access_same_result(self):
        """Repeated access returns same values."""
        class Model(MockTable):
            def __init__(self):
                self._items = [type('Item', (), {'name': 'Test'})()]
            
            @property
            def items(self):
                return self._items
        
        Model.names = association_proxy("items", "name")
        
        model = Model()
        
        result1 = list(model.names)
        result2 = list(model.names)
        result3 = list(model.names)
        
        assert result1 == result2 == result3 == ["Test"]
    
    def test_source_modification_reflected(self):
        """Changes to source collection are reflected in proxy."""
        class Model(MockTable):
            def __init__(self):
                self._items = []
            
            @property
            def items(self):
                return self._items
        
        Model.names = association_proxy("items", "name")
        
        model = Model()
        
        # Initially empty
        assert list(model.names) == []
        
        # Add item
        model._items.append(type('Item', (), {'name': 'New'})())
        
        # Should reflect change
        assert list(model.names) == ["New"]


# =============================================================================
# Test: ProxyCollection Basic Behavior
# =============================================================================

class TestProxyCollectionBasic:
    """Test ProxyCollection basic behavior."""
    
    def test_len(self):
        """len() works on ProxyCollection."""
        collection = ProxyCollection(
            owner=None,
            target_collection="items",
            attr="name",
        )
        # Since owner is None, it returns empty
        assert len(collection) == 0
    
    def test_bool_empty(self):
        """Empty collection is falsy."""
        collection = ProxyCollection(
            owner=None,
            target_collection="items",
            attr="name",
        )
        assert not collection
    
    def test_repr(self):
        """__repr__ returns readable string."""
        collection = ProxyCollection(
            owner=None,
            target_collection="items",
            attr="name",
        )
        result = repr(collection)
        assert "ProxyCollection" in result
        assert "items.name" in result
    
    def test_str(self):
        """__str__ returns list representation."""
        collection = ProxyCollection(
            owner=None,
            target_collection="items",
            attr="name",
        )
        result = str(collection)
        assert result == "[]"
    
    def test_to_list(self):
        """to_list() converts to regular Python list."""
        collection = ProxyCollection(
            owner=None,
            target_collection="items",
            attr="name",
        )
        result = collection.to_list()
        assert isinstance(result, list)
        assert result == []


# =============================================================================
# Test: Error Messages
# =============================================================================

class TestErrorMessages:
    """Test that error messages are clear and helpful."""
    
    def test_append_without_creator_error(self):
        """Append without creator gives clear error."""
        collection = ProxyCollection(
            owner=None,
            target_collection="items",
            attr="name",
            creator=None,
        )
        
        with pytest.raises(ValueError) as exc_info:
            collection.append("test")
        
        assert "creator function" in str(exc_info.value)
        assert "association_proxy" in str(exc_info.value)
    
    def test_setitem_error_message(self):
        """__setitem__ gives helpful error."""
        collection = ProxyCollection(
            owner=None,
            target_collection="items",
            attr="name",
        )
        
        with pytest.raises(TypeError) as exc_info:
            collection[0] = "test"
        
        assert "source collection" in str(exc_info.value)
    
    def test_delitem_error_message(self):
        """__delitem__ gives helpful error."""
        collection = ProxyCollection(
            owner=None,
            target_collection="items",
            attr="name",
        )
        
        with pytest.raises(TypeError) as exc_info:
            del collection[0]
        
        assert "remove()" in str(exc_info.value)


# =============================================================================
# Test: Exports from __init__.py
# =============================================================================

class TestExports:
    """Test that all exports are available."""
    
    def test_association_proxy_export(self):
        """association_proxy is exported from relationships package."""
        from pynext.db.relationships import association_proxy
        assert callable(association_proxy)
    
    def test_proxy_alias_export(self):
        """proxy alias is exported."""
        from pynext.db.relationships import proxy
        assert callable(proxy)
    
    def test_attr_proxy_alias_export(self):
        """attr_proxy alias is exported."""
        from pynext.db.relationships import attr_proxy
        assert callable(attr_proxy)
    
    def test_attribute_proxy_descriptor_export(self):
        """AttributeProxyDescriptor is exported."""
        from pynext.db.relationships import AttributeProxyDescriptor
        assert AttributeProxyDescriptor is not None
    
    def test_proxy_collection_export(self):
        """ProxyCollection is exported."""
        from pynext.db.relationships import ProxyCollection
        assert ProxyCollection is not None

