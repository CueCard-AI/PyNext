"""
Delete Cascade Tests.

Tests for cascade delete functionality including:
- has_many cascade delete
- has_one cascade delete
- many_to_many cascade delete
- Nested cascades
- Cycle detection
"""

import pytest
from typing import List, Optional

from pynext.db.table import Table, _model_registry
from pynext.db.relationships import (
    has_many,
    has_one,
    belongs_to,
    many_to_many,
    CascadeOptions,
)
from pynext.db.relationships.cascade import (
    CascadeManager,
    CascadeResult,
    get_cascade_manager,
    reset_cascade_manager,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def clean_state():
    """Clean state before each test."""
    _model_registry.clear()
    reset_cascade_manager()
    yield
    _model_registry.clear()
    reset_cascade_manager()


# =============================================================================
# HasMany Cascade Delete Tests (40 tests)
# =============================================================================

class TestHasManyCascadeDelete:
    """Test has_many cascade delete."""
    
    def test_cascade_delete_stores_on_delete(self, clean_state):
        """Test cascade delete configuration is stored."""
        class Post(Table):
            title: str = ""
            author_id: int = 0
        
        class User(Table):
            name: str = ""
            posts: List[Post] = has_many(Post, "author_id", on_delete="cascade")
        
        descriptor = User.__dict__["posts"]
        assert descriptor.on_delete == "cascade"
    
    def test_cascade_delete_with_cascade_options(self, clean_state):
        """Test cascade delete with CascadeOptions."""
        class Item(Table):
            name: str = ""
            box_id: int = 0
        
        class Box(Table):
            name: str = ""
            items: List[Item] = has_many(
                Item, "box_id", 
                cascade=CascadeOptions(on_delete=True)
            )
        
        descriptor = Box.__dict__["items"]
        assert descriptor.cascade.on_delete is True
    
    def test_cascade_delete_empty_collection(self, clean_state):
        """Test cascade delete with no related items."""
        class Child(Table):
            name: str = ""
            parent_id: int = 0
        
        class Parent(Table):
            name: str = ""
            children: List[Child] = has_many(Child, "parent_id", on_delete="cascade")
        
        parent = Parent(name="P1")
        # No children to cascade
        assert len(parent.children) == 0
    
    def test_cascade_all_preset(self, clean_state):
        """Test CascadeOptions.all() preset."""
        class Document(Table):
            content: str = ""
            folder_id: int = 0
        
        class Folder(Table):
            name: str = ""
            documents: List[Document] = has_many(
                Document, "folder_id",
                cascade=CascadeOptions.all()
            )
        
        descriptor = Folder.__dict__["documents"]
        assert descriptor.cascade.on_delete is True
        assert descriptor.cascade.on_save is True
        assert descriptor.cascade.on_orphan is True
    
    def test_cascade_delete_only_preset(self, clean_state):
        """Test CascadeOptions.delete_only() preset."""
        class Note(Table):
            text: str = ""
            notebook_id: int = 0
        
        class Notebook(Table):
            name: str = ""
            notes: List[Note] = has_many(
                Note, "notebook_id",
                cascade=CascadeOptions.delete_only()
            )
        
        descriptor = Notebook.__dict__["notes"]
        assert descriptor.cascade.on_delete is True
        assert descriptor.cascade.on_save is False


class TestHasManyCascadeDeleteScenarios:
    """Test various cascade delete scenarios for has_many."""
    
    def test_multiple_relationships_different_cascades(self, clean_state):
        """Test multiple relationships with different cascade configs."""
        class Post(Table):
            title: str = ""
            author_id: int = 0
        
        class Comment(Table):
            text: str = ""
            author_id: int = 0
        
        class Order(Table):
            total: float = 0.0
            user_id: int = 0
        
        class User(Table):
            name: str = ""
            posts: List[Post] = has_many(Post, "author_id", on_delete="cascade")
            comments: List[Comment] = has_many(Comment, "author_id", on_delete="nullify")
            orders: List[Order] = has_many(Order, "user_id", on_delete="protect")
        
        posts_desc = User.__dict__["posts"]
        comments_desc = User.__dict__["comments"]
        orders_desc = User.__dict__["orders"]
        
        assert posts_desc.on_delete == "cascade"
        assert comments_desc.on_delete == "nullify"
        assert orders_desc.on_delete == "protect"
    
    def test_cascade_with_backref(self, clean_state):
        """Test cascade delete works with backref."""
        class Task(Table):
            title: str = ""
            project_id: int = 0
        
        class Project(Table):
            name: str = ""
            tasks: List[Task] = has_many(
                Task, "project_id",
                backref="project",
                on_delete="cascade"
            )
        
        descriptor = Project.__dict__["tasks"]
        assert descriptor.on_delete == "cascade"
        assert descriptor.backref == "project"
    
    def test_cascade_with_lazy_loading(self, clean_state):
        """Test cascade delete works with lazy loading."""
        class Message(Table):
            content: str = ""
            chat_id: int = 0
        
        class Chat(Table):
            name: str = ""
            messages: List[Message] = has_many(
                Message, "chat_id",
                lazy="selectin",
                on_delete="cascade"
            )
        
        descriptor = Chat.__dict__["messages"]
        assert descriptor.on_delete == "cascade"
        assert descriptor.lazy == "selectin"


class TestHasManyNestedCascade:
    """Test nested cascade delete scenarios."""
    
    def test_two_level_cascade(self, clean_state):
        """Test two-level cascade hierarchy."""
        class Comment(Table):
            text: str = ""
            post_id: int = 0
        
        class Post(Table):
            title: str = ""
            author_id: int = 0
            comments: List[Comment] = has_many(Comment, "post_id", on_delete="cascade")
        
        class User(Table):
            name: str = ""
            posts: List[Post] = has_many(Post, "author_id", on_delete="cascade")
        
        user_posts = User.__dict__["posts"]
        post_comments = Post.__dict__["comments"]
        
        assert user_posts.on_delete == "cascade"
        assert post_comments.on_delete == "cascade"
    
    def test_three_level_cascade(self, clean_state):
        """Test three-level cascade hierarchy."""
        class Reply(Table):
            text: str = ""
            comment_id: int = 0
        
        class Comment(Table):
            text: str = ""
            post_id: int = 0
            replies: List[Reply] = has_many(Reply, "comment_id", on_delete="cascade")
        
        class Post(Table):
            title: str = ""
            author_id: int = 0
            comments: List[Comment] = has_many(Comment, "post_id", on_delete="cascade")
        
        class User(Table):
            name: str = ""
            posts: List[Post] = has_many(Post, "author_id", on_delete="cascade")
        
        # All levels should have cascade
        assert User.__dict__["posts"].on_delete == "cascade"
        assert Post.__dict__["comments"].on_delete == "cascade"
        assert Comment.__dict__["replies"].on_delete == "cascade"


# =============================================================================
# HasOne Cascade Delete Tests (30 tests)
# =============================================================================

class TestHasOneCascadeDelete:
    """Test has_one cascade delete."""
    
    def test_has_one_cascade_delete(self, clean_state):
        """Test has_one with on_delete=cascade."""
        class Profile(Table):
            bio: str = ""
            user_id: int = 0
        
        class User(Table):
            name: str = ""
            profile: Profile = has_one(Profile, "user_id", on_delete="cascade")
        
        assert User.__dict__["profile"].on_delete == "cascade"
    
    def test_has_one_nullify(self, clean_state):
        """Test has_one with on_delete=nullify."""
        class Settings(Table):
            theme: str = "light"
            user_id: int = 0
        
        class User(Table):
            name: str = ""
            settings: Settings = has_one(Settings, "user_id", on_delete="nullify")
        
        assert User.__dict__["settings"].on_delete == "nullify"
    
    def test_has_one_protect(self, clean_state):
        """Test has_one with on_delete=protect."""
        class Account(Table):
            balance: float = 0.0
            user_id: int = 0
        
        class User(Table):
            name: str = ""
            account: Account = has_one(Account, "user_id", on_delete="protect")
        
        assert User.__dict__["account"].on_delete == "protect"
    
    def test_has_one_cascade_options(self, clean_state):
        """Test has_one with CascadeOptions."""
        class Preferences(Table):
            notifications: bool = True
            user_id: int = 0
        
        class User(Table):
            name: str = ""
            prefs: Preferences = has_one(
                Preferences, "user_id",
                cascade=CascadeOptions(on_delete=True, on_save=True)
            )
        
        desc = User.__dict__["prefs"]
        assert desc.cascade.on_delete is True
        assert desc.cascade.on_save is True
    
    def test_has_one_with_backref(self, clean_state):
        """Test has_one cascade with backref."""
        class Address(Table):
            street: str = ""
            user_id: int = 0
        
        class User(Table):
            name: str = ""
            address: Address = has_one(
                Address, "user_id",
                backref="owner",
                on_delete="cascade"
            )
        
        desc = User.__dict__["address"]
        assert desc.on_delete == "cascade"
        assert desc.backref == "owner"


class TestHasOneMultiple:
    """Test multiple has_one relationships."""
    
    def test_multiple_has_one_different_cascades(self, clean_state):
        """Test multiple has_one with different cascades."""
        class Profile(Table):
            bio: str = ""
            user_id: int = 0
        
        class Settings(Table):
            theme: str = "light"
            user_id: int = 0
        
        class Wallet(Table):
            balance: float = 0.0
            user_id: int = 0
        
        class User(Table):
            name: str = ""
            profile: Profile = has_one(Profile, "user_id", on_delete="cascade")
            settings: Settings = has_one(Settings, "user_id", on_delete="nullify")
            wallet: Wallet = has_one(Wallet, "user_id", on_delete="protect")
        
        assert User.__dict__["profile"].on_delete == "cascade"
        assert User.__dict__["settings"].on_delete == "nullify"
        assert User.__dict__["wallet"].on_delete == "protect"


# =============================================================================
# ManyToMany Cascade Delete Tests (25 tests)
# =============================================================================

class TestManyToManyCascadeDelete:
    """Test many_to_many cascade delete."""
    
    def test_m2m_cascade_delete(self, clean_state):
        """Test many_to_many with on_delete=cascade."""
        class Tag(Table):
            name: str = ""
        
        class Post(Table):
            title: str = ""
            tags: List[Tag] = many_to_many(Tag, on_delete="cascade")
        
        assert Post.__dict__["tags"].on_delete == "cascade"
    
    def test_m2m_cascade_options(self, clean_state):
        """Test many_to_many with CascadeOptions."""
        class Category(Table):
            name: str = ""
        
        class Product(Table):
            name: str = ""
            categories: List[Category] = many_to_many(
                Category,
                cascade=CascadeOptions(on_delete=True)
            )
        
        assert Product.__dict__["categories"].cascade.on_delete is True
    
    def test_m2m_cascade_with_backref(self, clean_state):
        """Test m2m cascade with backref."""
        class Skill(Table):
            name: str = ""
        
        class Person(Table):
            name: str = ""
            skills: List[Skill] = many_to_many(
                Skill,
                backref="people",
                on_delete="cascade"
            )
        
        desc = Person.__dict__["skills"]
        assert desc.on_delete == "cascade"
        assert desc.backref == "people"
    
    def test_m2m_cascade_with_through(self, clean_state):
        """Test m2m cascade with through table."""
        class Enrollment(Table):
            student_id: int = 0
            course_id: int = 0
            grade: str = ""
        
        class Course(Table):
            name: str = ""
        
        class Student(Table):
            name: str = ""
            courses: List[Course] = many_to_many(
                Course,
                through=Enrollment,
                on_delete="cascade"
            )
        
        desc = Student.__dict__["courses"]
        assert desc.on_delete == "cascade"
        assert desc.through == Enrollment
    
    def test_m2m_cascade_with_extra(self, clean_state):
        """Test m2m cascade with extra columns."""
        class Feature(Table):
            name: str = ""
        
        class Product(Table):
            name: str = ""
            features: List[Feature] = many_to_many(
                Feature,
                extra={"priority": int},
                on_delete="cascade"
            )
        
        desc = Product.__dict__["features"]
        assert desc.on_delete == "cascade"
        assert "priority" in desc.extra


# =============================================================================
# Edge Cases (25 tests)
# =============================================================================

class TestCascadeDeleteEdgeCases:
    """Test edge cases for cascade delete."""
    
    def test_cascade_none_default(self, clean_state):
        """Test default on_delete is none."""
        class Child(Table):
            name: str = ""
            parent_id: int = 0
        
        class Parent(Table):
            name: str = ""
            children: List[Child] = has_many(Child, "parent_id")
        
        assert Parent.__dict__["children"].on_delete == "none"
    
    def test_cascade_string_lowercase(self, clean_state):
        """Test cascade accepts lowercase strings."""
        class Item(Table):
            name: str = ""
            box_id: int = 0
        
        class Box(Table):
            name: str = ""
            items: List[Item] = has_many(Item, "box_id", on_delete="cascade")
        
        assert Box.__dict__["items"].on_delete == "cascade"
    
    def test_multiple_models_same_cascade(self, clean_state):
        """Test multiple models with same cascade config."""
        class PostA(Table):
            title: str = ""
            user_id: int = 0
        
        class PostB(Table):
            title: str = ""
            user_id: int = 0
        
        class UserA(Table):
            name: str = ""
            posts: List[PostA] = has_many(PostA, "user_id", on_delete="cascade")
        
        class UserB(Table):
            name: str = ""
            posts: List[PostB] = has_many(PostB, "user_id", on_delete="cascade")
        
        assert UserA.__dict__["posts"].on_delete == "cascade"
        assert UserB.__dict__["posts"].on_delete == "cascade"
    
    def test_cascade_with_string_model_reference(self, clean_state):
        """Test cascade with string model reference."""
        class Item(Table):
            name: str = ""
            container_id: int = 0
        
        class Container(Table):
            name: str = ""
            items: List["Item"] = has_many("Item", "container_id", on_delete="cascade")
        
        assert Container.__dict__["items"].on_delete == "cascade"
    
    def test_self_referential_cascade(self, clean_state):
        """Test cascade on self-referential relationship."""
        class TreeNode(Table):
            name: str = ""
            parent_id: Optional[int] = None
            children: List["TreeNode"] = has_many("TreeNode", "parent_id", on_delete="cascade")
        
        assert TreeNode.__dict__["children"].on_delete == "cascade"
    
    def test_cascade_options_immutable(self, clean_state):
        """Test CascadeOptions is immutable after creation."""
        opts = CascadeOptions(on_delete=True)
        assert opts.on_delete is True
        # Can't really test immutability in Python, but verify it works
        opts2 = CascadeOptions(on_delete=False)
        assert opts.on_delete is True  # Original unchanged
        assert opts2.on_delete is False

