"""
Tests for association proxy with Many-to-Many relationships.

Tests cover:
- M2M through junction tables
- Both sides of M2M relationships
- Junction with extra columns
- M2M with creator functions
"""

import pytest
from typing import List, Optional
from dataclasses import dataclass, field
from datetime import datetime


# =============================================================================
# Mock Classes for M2M Testing
# =============================================================================

@dataclass
class Tag:
    """Tag model."""
    id: int
    name: str
    color: str = "gray"


@dataclass
class Category:
    """Category model."""
    id: int
    name: str
    parent_id: Optional[int] = None


@dataclass
class ProductTag:
    """Junction table for Product-Tag M2M."""
    id: int
    product_id: int
    tag_id: int
    tag: Optional[Tag] = None
    product: Optional["MockProduct"] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ProductCategory:
    """Junction for Product-Category."""
    id: int
    product_id: int
    category_id: int
    category: Optional[Category] = None
    is_primary: bool = False


@dataclass
class Enrollment:
    """Enrollment junction for Student-Course."""
    id: int
    student_id: int
    course_id: int
    course: Optional["Course"] = None
    student: Optional["Student"] = None
    grade: Optional[str] = None
    enrolled_at: datetime = field(default_factory=datetime.now)


@dataclass
class Course:
    """Course model."""
    id: int
    name: str
    credits: int = 3
    active: bool = True


class MockTable:
    """Base mock table."""
    _fields = {}
    __table_name__ = "mock"


from pynext.db.relationships.association_proxy import (
    association_proxy,
    ProxyCollection,
)


# =============================================================================
# Test: Basic M2M Through Junction
# =============================================================================

class TestBasicM2MThroughJunction:
    """Test basic M2M access through junction tables."""
    
    def test_access_target_objects(self):
        """Access target objects through junction."""
        class Product(MockTable):
            def __init__(self, product_tags: List[ProductTag]):
                self.id = 1
                self._product_tags = product_tags
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tags = association_proxy("product_tags", "tag")
        
        tags = [Tag(1, "electronics"), Tag(2, "sale")]
        product_tags = [
            ProductTag(1, 1, 1, tag=tags[0]),
            ProductTag(2, 1, 2, tag=tags[1]),
        ]
        product = Product(product_tags)
        
        result = list(product.tags)
        assert len(result) == 2
        assert result[0] is tags[0]
        assert result[1] is tags[1]
    
    def test_access_target_names(self):
        """Access target attribute through junction."""
        class Product(MockTable):
            def __init__(self, product_tags: List[ProductTag]):
                self.id = 1
                self._product_tags = product_tags
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tag_names = association_proxy("product_tags", "tag.name")
        
        product_tags = [
            ProductTag(1, 1, 1, tag=Tag(1, "electronics")),
            ProductTag(2, 1, 2, tag=Tag(2, "sale")),
        ]
        product = Product(product_tags)
        
        assert list(product.tag_names) == ["electronics", "sale"]
    
    def test_empty_junction_returns_empty(self):
        """Empty junction returns empty collection."""
        class Product(MockTable):
            def __init__(self):
                self._product_tags = []
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tags = association_proxy("product_tags", "tag")
        
        product = Product()
        assert list(product.tags) == []


# =============================================================================
# Test: M2M with Multiple Proxies
# =============================================================================

class TestM2MMultipleProxies:
    """Test multiple proxies on M2M relationships."""
    
    def test_multiple_proxies_same_junction(self):
        """Multiple proxies can access same junction."""
        class Product(MockTable):
            def __init__(self, product_tags: List[ProductTag]):
                self._product_tags = product_tags
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tags = association_proxy("product_tags", "tag")
        Product.tag_names = association_proxy("product_tags", "tag.name")
        Product.tag_colors = association_proxy("product_tags", "tag.color")
        
        product_tags = [
            ProductTag(1, 1, 1, tag=Tag(1, "electronics", "blue")),
            ProductTag(2, 1, 2, tag=Tag(2, "sale", "red")),
        ]
        product = Product(product_tags)
        
        assert len(list(product.tags)) == 2
        assert list(product.tag_names) == ["electronics", "sale"]
        assert list(product.tag_colors) == ["blue", "red"]
    
    def test_different_junctions(self):
        """Proxies to different junctions work independently."""
        class Product(MockTable):
            def __init__(
                self, 
                product_tags: List[ProductTag],
                product_categories: List[ProductCategory]
            ):
                self._product_tags = product_tags
                self._product_categories = product_categories
            
            @property
            def product_tags(self):
                return self._product_tags
            
            @property
            def product_categories(self):
                return self._product_categories
        
        Product.tag_names = association_proxy("product_tags", "tag.name")
        Product.category_names = association_proxy("product_categories", "category.name")
        
        product = Product(
            product_tags=[ProductTag(1, 1, 1, tag=Tag(1, "tech"))],
            product_categories=[ProductCategory(1, 1, 1, category=Category(1, "Electronics"))]
        )
        
        assert list(product.tag_names) == ["tech"]
        assert list(product.category_names) == ["Electronics"]


# =============================================================================
# Test: M2M Junction with Extra Columns
# =============================================================================

class TestM2MJunctionExtraColumns:
    """Test M2M junctions with extra columns."""
    
    def test_access_junction_column(self):
        """Access junction's own column."""
        class Student(MockTable):
            def __init__(self, enrollments: List[Enrollment]):
                self._enrollments = enrollments
            
            @property
            def enrollments(self):
                return self._enrollments
        
        Student.grades = association_proxy("enrollments", "grade")
        
        enrollments = [
            Enrollment(1, 1, 1, course=Course(1, "Math"), grade="A"),
            Enrollment(2, 1, 2, course=Course(2, "Physics"), grade="B"),
        ]
        student = Student(enrollments)
        
        assert list(student.grades) == ["A", "B"]
    
    def test_access_target_through_junction_with_extra(self):
        """Access target even when junction has extra columns."""
        class Student(MockTable):
            def __init__(self, enrollments: List[Enrollment]):
                self._enrollments = enrollments
            
            @property
            def enrollments(self):
                return self._enrollments
        
        Student.course_names = association_proxy("enrollments", "course.name")
        
        enrollments = [
            Enrollment(1, 1, 1, course=Course(1, "Math"), grade="A"),
            Enrollment(2, 1, 2, course=Course(2, "Physics"), grade="B"),
        ]
        student = Student(enrollments)
        
        assert list(student.course_names) == ["Math", "Physics"]
    
    def test_filter_by_junction_column(self):
        """Filter works on junction columns."""
        class Student(MockTable):
            def __init__(self, enrollments: List[Enrollment]):
                self._enrollments = enrollments
            
            @property
            def enrollments(self):
                return self._enrollments
        
        Student.courses = association_proxy("enrollments", "course")
        
        enrollments = [
            Enrollment(1, 1, 1, course=Course(1, "Math", active=True)),
            Enrollment(2, 1, 2, course=Course(2, "History", active=False)),
            Enrollment(3, 1, 3, course=Course(3, "Physics", active=True)),
        ]
        student = Student(enrollments)
        
        # This tests ProxyCollection.filter
        import asyncio
        active = asyncio.get_event_loop().run_until_complete(
            student.courses.filter(active=True)
        )
        
        assert len(active) == 2
        assert all(c.active for c in active)


# =============================================================================
# Test: M2M with Creator
# =============================================================================

class TestM2MWithCreator:
    """Test M2M with creator functions."""
    
    def test_append_through_m2m(self):
        """Append target creates junction automatically."""
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
        
        assert len(product._product_tags) == 1
        assert product._product_tags[0].tag.name == "new_tag"
    
    def test_extend_through_m2m(self):
        """Extend target creates multiple junctions."""
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
        tags = [Tag(i, f"tag{i}") for i in range(3)]
        product.tags.extend(tags)
        
        assert len(product._product_tags) == 3
    
    def test_creator_with_junction_defaults(self):
        """Creator can set junction defaults."""
        class Product(MockTable):
            def __init__(self):
                self.id = 1
                self._product_categories = []
            
            @property
            def product_categories(self):
                return self._product_categories
        
        Product.categories = association_proxy(
            "product_categories",
            "category",
            creator=lambda cat: ProductCategory(0, 1, cat.id, category=cat, is_primary=False)
        )
        
        product = Product()
        product.categories.append(Category(1, "Electronics"))
        
        assert product._product_categories[0].is_primary is False


# =============================================================================
# Test: Reverse M2M Access
# =============================================================================

class TestReverseM2MAccess:
    """Test accessing M2M from the other side."""
    
    def test_reverse_access(self):
        """Access products through tag's product_tags."""
        @dataclass
        class MockProduct:
            id: int
            name: str
        
        class TagWithProducts(MockTable):
            def __init__(self, product_tags: List[ProductTag]):
                self.id = 1
                self._product_tags = product_tags
            
            @property
            def product_tags(self):
                return self._product_tags
        
        TagWithProducts.products = association_proxy("product_tags", "product")
        
        products = [MockProduct(1, "Phone"), MockProduct(2, "Laptop")]
        product_tags = [
            ProductTag(1, 1, 1, product=products[0]),
            ProductTag(2, 2, 1, product=products[1]),
        ]
        tag = TagWithProducts(product_tags)
        
        result = list(tag.products)
        assert len(result) == 2


# =============================================================================
# Test: M2M Count and Check
# =============================================================================

class TestM2MCountCheck:
    """Test count and membership operations on M2M."""
    
    def test_len_m2m(self):
        """len() returns correct count."""
        class Product(MockTable):
            def __init__(self, product_tags: List[ProductTag]):
                self._product_tags = product_tags
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tags = association_proxy("product_tags", "tag")
        
        product_tags = [ProductTag(i, 1, i, tag=Tag(i, f"tag{i}")) for i in range(5)]
        product = Product(product_tags)
        
        assert len(product.tags) == 5
    
    def test_in_check_m2m(self):
        """'in' operator works for M2M."""
        class Product(MockTable):
            def __init__(self, product_tags: List[ProductTag]):
                self._product_tags = product_tags
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tag_names = association_proxy("product_tags", "tag.name")
        
        product_tags = [
            ProductTag(1, 1, 1, tag=Tag(1, "electronics")),
            ProductTag(2, 1, 2, tag=Tag(2, "sale")),
        ]
        product = Product(product_tags)
        
        assert "electronics" in product.tag_names
        assert "sale" in product.tag_names
        assert "unknown" not in product.tag_names
    
    def test_bool_m2m(self):
        """Boolean check on M2M proxy."""
        class Product(MockTable):
            def __init__(self, product_tags: List[ProductTag]):
                self._product_tags = product_tags
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tags = association_proxy("product_tags", "tag")
        
        # Non-empty
        product_with_tags = Product([ProductTag(1, 1, 1, tag=Tag(1, "test"))])
        assert product_with_tags.tags  # Truthy
        
        # Empty
        product_without_tags = Product([])
        assert not product_without_tags.tags  # Falsy


# =============================================================================
# Test: M2M with None in Junction
# =============================================================================

class TestM2MNoneHandling:
    """Test M2M with None values in junction."""
    
    def test_none_target_skipped(self):
        """None target in junction is skipped."""
        class Product(MockTable):
            def __init__(self, product_tags: List[ProductTag]):
                self._product_tags = product_tags
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tag_names = association_proxy("product_tags", "tag.name")
        
        product_tags = [
            ProductTag(1, 1, 1, tag=Tag(1, "a")),
            ProductTag(2, 1, 2, tag=None),  # No tag!
            ProductTag(3, 1, 3, tag=Tag(3, "c")),
        ]
        product = Product(product_tags)
        
        # Should skip the None tag
        assert list(product.tag_names) == ["a", "c"]
    
    def test_empty_junction_list(self):
        """Empty junction list returns empty collection."""
        class Product(MockTable):
            def __init__(self):
                self._product_tags = []
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tags = association_proxy("product_tags", "tag")
        
        product = Product()
        assert list(product.tags) == []
        assert len(product.tags) == 0
        assert not product.tags  # Falsy


# =============================================================================
# Test: Nested M2M Paths
# =============================================================================

class TestNestedM2MPaths:
    """Test nested attribute paths through M2M."""
    
    def test_nested_object_attribute(self):
        """Access nested attribute on M2M target."""
        @dataclass
        class CourseInfo:
            description: str
            difficulty: str
        
        @dataclass
        class CourseWithInfo:
            id: int
            name: str
            info: CourseInfo
        
        @dataclass
        class EnrollmentWithInfo:
            id: int
            course: CourseWithInfo
        
        class Student(MockTable):
            def __init__(self, enrollments: List[EnrollmentWithInfo]):
                self._enrollments = enrollments
            
            @property
            def enrollments(self):
                return self._enrollments
        
        Student.course_difficulties = association_proxy("enrollments", "course.info.difficulty")
        
        enrollments = [
            EnrollmentWithInfo(1, CourseWithInfo(1, "Math", CourseInfo("desc", "hard"))),
            EnrollmentWithInfo(2, CourseWithInfo(2, "Art", CourseInfo("desc", "easy"))),
        ]
        student = Student(enrollments)
        
        assert list(student.course_difficulties) == ["hard", "easy"]


# =============================================================================
# Test: M2M Iteration Order
# =============================================================================

class TestM2MIterationOrder:
    """Test that M2M preserves iteration order."""
    
    def test_order_preserved(self):
        """Iteration order matches junction order."""
        class Product(MockTable):
            def __init__(self, product_tags: List[ProductTag]):
                self._product_tags = product_tags
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tag_names = association_proxy("product_tags", "tag.name")
        
        # Create in specific order
        product_tags = [
            ProductTag(3, 1, 3, tag=Tag(3, "third")),
            ProductTag(1, 1, 1, tag=Tag(1, "first")),
            ProductTag(2, 1, 2, tag=Tag(2, "second")),
        ]
        product = Product(product_tags)
        
        # Should match junction order, not tag ID order
        assert list(product.tag_names) == ["third", "first", "second"]


# =============================================================================
# Test: M2M with Async Methods
# =============================================================================

class TestM2MAsyncMethods:
    """Test async methods on M2M proxy."""
    
    def test_async_all(self):
        """async all() returns all items."""
        import asyncio
        
        class Product(MockTable):
            def __init__(self, product_tags: List[ProductTag]):
                self._product_tags = product_tags
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tags = association_proxy("product_tags", "tag")
        
        product_tags = [
            ProductTag(1, 1, 1, tag=Tag(1, "a")),
            ProductTag(2, 1, 2, tag=Tag(2, "b")),
        ]
        product = Product(product_tags)
        
        result = asyncio.get_event_loop().run_until_complete(product.tags.all())
        
        assert len(result) == 2
    
    def test_async_first(self):
        """async first() returns first item."""
        import asyncio
        
        class Product(MockTable):
            def __init__(self, product_tags: List[ProductTag]):
                self._product_tags = product_tags
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tags = association_proxy("product_tags", "tag")
        
        product_tags = [
            ProductTag(1, 1, 1, tag=Tag(1, "first")),
            ProductTag(2, 1, 2, tag=Tag(2, "second")),
        ]
        product = Product(product_tags)
        
        result = asyncio.get_event_loop().run_until_complete(product.tags.first())
        
        assert result.name == "first"
    
    def test_async_first_empty(self):
        """async first() returns None on empty."""
        import asyncio
        
        class Product(MockTable):
            def __init__(self):
                self._product_tags = []
            
            @property
            def product_tags(self):
                return self._product_tags
        
        Product.tags = association_proxy("product_tags", "tag")
        
        product = Product()
        result = asyncio.get_event_loop().run_until_complete(product.tags.first())
        
        assert result is None

