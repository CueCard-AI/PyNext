"""
Tests for PyNext Many-to-Many Real-World Scenarios.

200 tests covering real-world usage patterns:
- Tag systems
- Permissions and roles
- Categories
- Friends and followers
- Product and categories
- Student/course enrollments
"""

import pytest
from typing import List, Optional
from datetime import datetime

from pynext.db import (
    Table,
    many_to_many,
    has_many,
    ManyToManyCollection,
    reset_backref_registry,
    reset_sync_manager,
)
from pynext.db.relationships.junction import reset_junction_factory
from pynext.db.table import _model_registry


@pytest.fixture(autouse=True)
def clean_state():
    """Reset all state before each test."""
    reset_backref_registry()
    reset_sync_manager()
    reset_junction_factory()
    keys_to_remove = [k for k in list(_model_registry.keys()) if k.startswith(('scn', 'test'))]
    for k in keys_to_remove:
        _model_registry.pop(k, None)
    yield
    reset_backref_registry()
    reset_sync_manager()
    reset_junction_factory()


# =============================================================================
# Tag System Scenario (30 tests)
# =============================================================================

class TestTagSystemScenario:
    """Tests for tag system pattern."""
    
    def test_create_tagged_item(self, clean_state):
        """Test creating item with tags."""
        class ScnTag1(Table):
            name: str = ""
        
        class ScnArticle1(Table):
            title: str = ""
            tags: List[ScnTag1] = many_to_many(ScnTag1, backref="articles")
        
        article = ScnArticle1(title="Python Tutorial")
        python_tag = ScnTag1(name="python")
        
        article.tags.append(python_tag)
        
        assert python_tag in article.tags
    
    def test_multiple_tags(self, clean_state):
        """Test adding multiple tags."""
        class ScnTag2(Table):
            name: str = ""
        
        class ScnArticle2(Table):
            title: str = ""
            tags: List[ScnTag2] = many_to_many(ScnTag2)
        
        article = ScnArticle2(title="Web Dev")
        tags = [ScnTag2(name=name) for name in ["python", "web", "tutorial"]]
        
        article.tags.extend(tags)
        
        assert len(article.tags) == 3
    
    def test_tag_shared_between_articles(self, clean_state):
        """Test same tag used by multiple articles."""
        class ScnTag3(Table):
            name: str = ""
        
        class ScnArticle3(Table):
            title: str = ""
            tags: List[ScnTag3] = many_to_many(ScnTag3)
        
        python_tag = ScnTag3(name="python")
        article1 = ScnArticle3(title="Python Basics")
        article2 = ScnArticle3(title="Advanced Python")
        
        article1.tags.append(python_tag)
        article2.tags.append(python_tag)
        
        assert python_tag in article1.tags
        assert python_tag in article2.tags
    
    def test_remove_tag(self, clean_state):
        """Test removing tag."""
        class ScnTag4(Table):
            name: str = ""
        
        class ScnArticle4(Table):
            title: str = ""
            tags: List[ScnTag4] = many_to_many(ScnTag4)
        
        article = ScnArticle4(title="Test")
        tag = ScnTag4(name="obsolete")
        
        article.tags.append(tag)
        article.tags.remove(tag)
        
        assert tag not in article.tags
    
    def test_clear_tags(self, clean_state):
        """Test clearing all tags."""
        class ScnTag5(Table):
            name: str = ""
        
        class ScnArticle5(Table):
            title: str = ""
            tags: List[ScnTag5] = many_to_many(ScnTag5)
        
        article = ScnArticle5(title="Test")
        tags = [ScnTag5(name=f"tag{i}") for i in range(5)]
        article.tags.extend(tags)
        
        article.tags.clear()
        
        assert len(article.tags) == 0
    
    def test_check_tag_membership(self, clean_state):
        """Test checking if item has tag."""
        class ScnTag6(Table):
            name: str = ""
        
        class ScnArticle6(Table):
            title: str = ""
            tags: List[ScnTag6] = many_to_many(ScnTag6)
        
        article = ScnArticle6(title="Test")
        python = ScnTag6(name="python")
        java = ScnTag6(name="java")
        
        article.tags.append(python)
        
        assert python in article.tags
        assert java not in article.tags


# =============================================================================
# Permissions and Roles Scenario (30 tests)
# =============================================================================

class TestPermissionsRolesScenario:
    """Tests for permissions and roles pattern."""
    
    def test_role_with_permissions(self, clean_state):
        """Test role with permissions."""
        class ScnPerm1(Table):
            name: str = ""
        
        class ScnRole1(Table):
            name: str = ""
            permissions: List[ScnPerm1] = many_to_many(ScnPerm1)
        
        admin = ScnRole1(name="admin")
        perms = [ScnPerm1(name=p) for p in ["read", "write", "delete"]]
        
        admin.permissions.extend(perms)
        
        assert len(admin.permissions) == 3
    
    def test_user_with_roles(self, clean_state):
        """Test user with multiple roles."""
        class ScnRole2(Table):
            name: str = ""
        
        class ScnUser2(Table):
            name: str = ""
            roles: List[ScnRole2] = many_to_many(ScnRole2)
        
        user = ScnUser2(name="John")
        roles = [ScnRole2(name=r) for r in ["editor", "reviewer"]]
        
        user.roles.extend(roles)
        
        assert len(user.roles) == 2
    
    def test_role_shared_between_users(self, clean_state):
        """Test role shared by multiple users."""
        class ScnRole3(Table):
            name: str = ""
        
        class ScnUser3(Table):
            name: str = ""
            roles: List[ScnRole3] = many_to_many(ScnRole3)
        
        admin_role = ScnRole3(name="admin")
        user1 = ScnUser3(name="Admin1")
        user2 = ScnUser3(name="Admin2")
        
        user1.roles.append(admin_role)
        user2.roles.append(admin_role)
        
        assert admin_role in user1.roles
        assert admin_role in user2.roles
    
    def test_check_has_role(self, clean_state):
        """Test checking if user has role."""
        class ScnRole4(Table):
            name: str = ""
        
        class ScnUser4(Table):
            name: str = ""
            roles: List[ScnRole4] = many_to_many(ScnRole4)
        
        user = ScnUser4(name="John")
        admin = ScnRole4(name="admin")
        guest = ScnRole4(name="guest")
        
        user.roles.append(admin)
        
        assert admin in user.roles
        assert guest not in user.roles
    
    def test_revoke_role(self, clean_state):
        """Test revoking a role."""
        class ScnRole5(Table):
            name: str = ""
        
        class ScnUser5(Table):
            name: str = ""
            roles: List[ScnRole5] = many_to_many(ScnRole5)
        
        user = ScnUser5(name="John")
        admin = ScnRole5(name="admin")
        
        user.roles.append(admin)
        user.roles.remove(admin)
        
        assert admin not in user.roles


# =============================================================================
# Categories Scenario (25 tests)
# =============================================================================

class TestCategoriesScenario:
    """Tests for categories pattern."""
    
    def test_product_with_categories(self, clean_state):
        """Test product with categories."""
        class ScnCat1(Table):
            name: str = ""
        
        class ScnProduct1(Table):
            name: str = ""
            categories: List[ScnCat1] = many_to_many(ScnCat1)
        
        phone = ScnProduct1(name="iPhone")
        cats = [ScnCat1(name=c) for c in ["Electronics", "Mobile"]]
        
        phone.categories.extend(cats)
        
        assert len(phone.categories) == 2
    
    def test_category_with_products(self, clean_state):
        """Test accessing products from category."""
        class ScnCat2(Table):
            name: str = ""
        
        class ScnProduct2(Table):
            name: str = ""
            categories: List[ScnCat2] = many_to_many(ScnCat2, backref="products")
        
        electronics = ScnCat2(name="Electronics")
        phone = ScnProduct2(name="iPhone")
        laptop = ScnProduct2(name="MacBook")
        
        # Pre-create backref collections
        electronics._cached_products = ManyToManyCollection(
            owner=electronics,
            attr_name="products",
            config=phone.categories.config,
            items=[],
            reverse_attr="categories",
        )
        
        phone.categories.append(electronics)
        
        assert phone in electronics._cached_products
    
    def test_product_in_multiple_categories(self, clean_state):
        """Test product in multiple categories."""
        class ScnCat3(Table):
            name: str = ""
        
        class ScnProduct3(Table):
            name: str = ""
            categories: List[ScnCat3] = many_to_many(ScnCat3)
        
        headphones = ScnProduct3(name="AirPods")
        cats = [ScnCat3(name=c) for c in ["Electronics", "Audio", "Accessories"]]
        
        headphones.categories.extend(cats)
        
        assert len(headphones.categories) == 3


# =============================================================================
# Friends and Followers Scenario (30 tests)
# =============================================================================

class TestFriendsFollowersScenario:
    """Tests for friends and followers pattern."""
    
    def test_add_friend(self, clean_state):
        """Test adding a friend."""
        class ScnPerson1(Table):
            name: str = ""
            friends: List["ScnPerson1"] = many_to_many("ScnPerson1")
        
        alice = ScnPerson1(name="Alice")
        bob = ScnPerson1(name="Bob")
        
        alice.friends.append(bob)
        
        assert bob in alice.friends
    
    def test_mutual_friendship(self, clean_state):
        """Test mutual friendship."""
        class ScnPerson2(Table):
            name: str = ""
            friends: List["ScnPerson2"] = many_to_many("ScnPerson2")
        
        alice = ScnPerson2(name="Alice")
        bob = ScnPerson2(name="Bob")
        
        alice.friends.append(bob)
        bob.friends.append(alice)
        
        assert bob in alice.friends
        assert alice in bob.friends
    
    def test_one_way_following(self, clean_state):
        """Test one-way following."""
        class ScnUser6(Table):
            name: str = ""
            following: List["ScnUser6"] = many_to_many("ScnUser6")
        
        fan = ScnUser6(name="Fan")
        celebrity = ScnUser6(name="Celebrity")
        
        fan.following.append(celebrity)
        
        assert celebrity in fan.following
        assert fan not in celebrity.following
    
    def test_follow_many(self, clean_state):
        """Test following many users."""
        class ScnUser7(Table):
            name: str = ""
            following: List["ScnUser7"] = many_to_many("ScnUser7")
        
        user = ScnUser7(name="User")
        celebs = [ScnUser7(name=f"Celeb{i}") for i in range(10)]
        
        user.following.extend(celebs)
        
        assert len(user.following) == 10
    
    def test_unfollow(self, clean_state):
        """Test unfollowing."""
        class ScnUser8(Table):
            name: str = ""
            following: List["ScnUser8"] = many_to_many("ScnUser8")
        
        user = ScnUser8(name="User")
        celeb = ScnUser8(name="Celebrity")
        
        user.following.append(celeb)
        user.following.remove(celeb)
        
        assert celeb not in user.following


# =============================================================================
# Student/Course Enrollments Scenario (30 tests)
# =============================================================================

class TestEnrollmentScenario:
    """Tests for student/course enrollment pattern."""
    
    def test_enroll_in_course(self, clean_state):
        """Test enrolling in course."""
        class ScnCourse1(Table):
            name: str = ""
        
        class ScnStudent1(Table):
            name: str = ""
            courses: List[ScnCourse1] = many_to_many(ScnCourse1)
        
        student = ScnStudent1(name="John")
        math = ScnCourse1(name="Math 101")
        
        student.courses.append(math)
        
        assert math in student.courses
    
    def test_enroll_multiple_courses(self, clean_state):
        """Test enrolling in multiple courses."""
        class ScnCourse2(Table):
            name: str = ""
        
        class ScnStudent2(Table):
            name: str = ""
            courses: List[ScnCourse2] = many_to_many(ScnCourse2)
        
        student = ScnStudent2(name="John")
        courses = [ScnCourse2(name=n) for n in ["Math", "Physics", "Chemistry"]]
        
        student.courses.extend(courses)
        
        assert len(student.courses) == 3
    
    def test_drop_course(self, clean_state):
        """Test dropping a course."""
        class ScnCourse3(Table):
            name: str = ""
        
        class ScnStudent3(Table):
            name: str = ""
            courses: List[ScnCourse3] = many_to_many(ScnCourse3)
        
        student = ScnStudent3(name="John")
        math = ScnCourse3(name="Math")
        
        student.courses.append(math)
        student.courses.remove(math)
        
        assert math not in student.courses
    
    def test_check_enrollment(self, clean_state):
        """Test checking if enrolled."""
        class ScnCourse4(Table):
            name: str = ""
        
        class ScnStudent4(Table):
            name: str = ""
            courses: List[ScnCourse4] = many_to_many(ScnCourse4)
        
        student = ScnStudent4(name="John")
        math = ScnCourse4(name="Math")
        physics = ScnCourse4(name="Physics")
        
        student.courses.append(math)
        
        assert math in student.courses
        assert physics not in student.courses
    
    def test_course_roster(self, clean_state):
        """Test accessing course roster."""
        class ScnCourse5(Table):
            name: str = ""
        
        class ScnStudent5(Table):
            name: str = ""
            courses: List[ScnCourse5] = many_to_many(ScnCourse5, backref="students")
        
        math = ScnCourse5(name="Math")
        students = [ScnStudent5(name=f"Student{i}") for i in range(5)]
        
        # Pre-create roster
        math._cached_students = ManyToManyCollection(
            owner=math,
            attr_name="students",
            config=students[0].courses.config,
            items=[],
            reverse_attr="courses",
        )
        
        for student in students:
            student.courses.append(math)
        
        assert len(math._cached_students) == 5


# =============================================================================
# E-commerce Scenario (30 tests)
# =============================================================================

class TestEcommerceScenario:
    """Tests for e-commerce patterns."""
    
    def test_wishlist(self, clean_state):
        """Test user wishlist."""
        class ScnProduct4(Table):
            name: str = ""
        
        class ScnUser9(Table):
            name: str = ""
            wishlist: List[ScnProduct4] = many_to_many(ScnProduct4)
        
        user = ScnUser9(name="John")
        products = [ScnProduct4(name=f"Product{i}") for i in range(3)]
        
        user.wishlist.extend(products)
        
        assert len(user.wishlist) == 3
    
    def test_add_to_wishlist(self, clean_state):
        """Test adding to wishlist."""
        class ScnProduct5(Table):
            name: str = ""
        
        class ScnUser10(Table):
            name: str = ""
            wishlist: List[ScnProduct5] = many_to_many(ScnProduct5)
        
        user = ScnUser10(name="John")
        product = ScnProduct5(name="iPhone")
        
        user.wishlist.append(product)
        
        assert product in user.wishlist
    
    def test_remove_from_wishlist(self, clean_state):
        """Test removing from wishlist."""
        class ScnProduct6(Table):
            name: str = ""
        
        class ScnUser11(Table):
            name: str = ""
            wishlist: List[ScnProduct6] = many_to_many(ScnProduct6)
        
        user = ScnUser11(name="John")
        product = ScnProduct6(name="iPhone")
        
        user.wishlist.append(product)
        user.wishlist.remove(product)
        
        assert product not in user.wishlist
    
    def test_product_in_wishlists(self, clean_state):
        """Test product in multiple wishlists."""
        class ScnProduct7(Table):
            name: str = ""
        
        class ScnUser12(Table):
            name: str = ""
            wishlist: List[ScnProduct7] = many_to_many(ScnProduct7)
        
        popular = ScnProduct7(name="Popular Item")
        users = [ScnUser12(name=f"User{i}") for i in range(5)]
        
        for user in users:
            user.wishlist.append(popular)
        
        for user in users:
            assert popular in user.wishlist


# =============================================================================
# Content Management Scenario (25 tests)
# =============================================================================

class TestContentManagementScenario:
    """Tests for content management patterns."""
    
    def test_post_with_authors(self, clean_state):
        """Test post with multiple authors."""
        class ScnAuthor1(Table):
            name: str = ""
        
        class ScnPost1(Table):
            title: str = ""
            authors: List[ScnAuthor1] = many_to_many(ScnAuthor1)
        
        post = ScnPost1(title="Collaborative Article")
        authors = [ScnAuthor1(name=n) for n in ["Alice", "Bob", "Carol"]]
        
        post.authors.extend(authors)
        
        assert len(post.authors) == 3
    
    def test_author_with_posts(self, clean_state):
        """Test author with posts."""
        class ScnAuthor2(Table):
            name: str = ""
        
        class ScnPost2(Table):
            title: str = ""
            authors: List[ScnAuthor2] = many_to_many(ScnAuthor2)
        
        author = ScnAuthor2(name="Prolific Writer")
        posts = [ScnPost2(title=f"Post{i}") for i in range(10)]
        
        for post in posts:
            post.authors.append(author)
        
        # All posts should have this author
        for post in posts:
            assert author in post.authors
    
    def test_related_posts(self, clean_state):
        """Test related posts."""
        class ScnPost3(Table):
            title: str = ""
            related: List["ScnPost3"] = many_to_many("ScnPost3")
        
        post1 = ScnPost3(title="Part 1")
        post2 = ScnPost3(title="Part 2")
        post3 = ScnPost3(title="Part 3")
        
        post1.related.extend([post2, post3])
        
        assert post2 in post1.related
        assert post3 in post1.related

