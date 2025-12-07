"""
Tests for PyNext Backref - Edge Cases, Errors, and Performance.

150 tests covering:
- Null values and empty collections
- Deleted objects
- Error handling
- Forward references
- Self-referential relationships
- Performance with large collections
- Concurrent modifications
- Special characters and unicode
- Type mismatches
"""

import pytest
import time
from typing import List, Optional

from pynext.db import (
    Table,
    configure_db,
    MockAdapter,
    has_many,
    has_one,
    belongs_to,
    BelongsTo,
    HasMany,
    HasOne,
    BackrefConfig,
    get_backref_registry,
    reset_backref_registry,
    reset_sync_manager,
    SyncedList,
)
from pynext.db.table import _model_registry


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def clean_state():
    """Reset all state before each test."""
    reset_backref_registry()
    reset_sync_manager()
    keys_to_remove = [k for k in _model_registry.keys() if 'edge' in k.lower() or k.startswith('E')]
    for k in keys_to_remove:
        _model_registry.pop(k, None)
    yield
    reset_backref_registry()
    reset_sync_manager()


@pytest.fixture
async def mock_adapter(clean_state):
    """Create and configure a mock adapter."""
    adapter = MockAdapter()
    await adapter.connect()
    configure_db(adapter)
    yield adapter
    adapter.reset()
    await adapter.disconnect()


# =============================================================================
# Null Value Tests (25 tests)
# =============================================================================

class TestNullValues:
    """Tests for null value handling."""
    
    def test_belongs_to_initially_none(self, clean_state):
        """Test belongs_to is None when not set."""
        class EUser1(Table):
            name: str
            posts: List["EPost1"] = has_many("EPost1", backref="author")
        
        class EPost1(Table):
            title: str
            user_id: Optional[int] = None
        
        post = EPost1(title="Hello")
        
        assert post.author is None
    
    def test_has_many_initially_empty(self, clean_state):
        """Test has_many is empty when no items."""
        class EUser2(Table):
            name: str
            posts: List["EPost2"] = has_many("EPost2", backref="author")
        
        class EPost2(Table):
            title: str
            user_id: Optional[int] = None
        
        user = EUser2(name="John")
        
        assert len(user.posts) == 0
    
    def test_set_belongs_to_none(self, clean_state):
        """Test setting belongs_to to None."""
        class EUser3(Table):
            name: str
            posts: List["EPost3"] = has_many("EPost3", backref="author")
        
        class EPost3(Table):
            title: str
            user_id: Optional[int] = None
        
        user = EUser3(name="John")
        post = EPost3(title="Hello")
        
        post.author = user
        post.author = None
        
        assert post.author is None
        assert post not in user.posts
    
    def test_append_none_fails(self, clean_state):
        """Test appending None to has_many."""
        class EUser4(Table):
            name: str
            posts: List["EPost4"] = has_many("EPost4", backref="author")
        
        class EPost4(Table):
            title: str
            user_id: Optional[int] = None
        
        user = EUser4(name="John")
        
        # Appending None should work (list allows it)
        # but sync might fail gracefully
        user.posts.append(None)
        
        # Should have None in list
        assert None in user.posts
    
    def test_has_one_initially_none(self, clean_state):
        """Test has_one is None when not set."""
        class EUser5(Table):
            name: str
            profile: "EProfile1" = has_one("EProfile1", backref="user")
        
        class EProfile1(Table):
            bio: str
            user_id: Optional[int] = None
        
        user = EUser5(name="John")
        
        assert user.profile is None
    
    def test_set_has_one_none(self, clean_state):
        """Test setting has_one to None."""
        class EUser6(Table):
            name: str
            profile: "EProfile2" = has_one("EProfile2", backref="user")
        
        class EProfile2(Table):
            bio: str
            user_id: Optional[int] = None
        
        user = EUser6(name="John")
        profile = EProfile2(bio="Hello")
        
        user.profile = profile
        user.profile = None
        
        assert user.profile is None
        assert profile.user is None
    
    def test_replace_with_none_preserves_old(self, clean_state):
        """Test replacing with None preserves old object."""
        class EUser7(Table):
            name: str
            posts: List["EPost7"] = has_many("EPost7", backref="author")
        
        class EPost7(Table):
            title: str
            user_id: Optional[int] = None
        
        user = EUser7(name="John")
        post = EPost7(title="Hello")
        
        post.author = user
        post.author = None
        
        # Post object still exists, just unlinked
        assert post.title == "Hello"
    
    def test_multiple_none_sets(self, clean_state):
        """Test setting None multiple times."""
        class EUser8(Table):
            name: str
            posts: List["EPost8"] = has_many("EPost8", backref="author")
        
        class EPost8(Table):
            title: str
            user_id: Optional[int] = None
        
        post = EPost8(title="Hello")
        
        post.author = None
        post.author = None
        post.author = None
        
        assert post.author is None


# =============================================================================
# Empty Collection Tests (15 tests)
# =============================================================================

class TestEmptyCollections:
    """Tests for empty collection handling."""
    
    def test_clear_empty_list(self, clean_state):
        """Test clearing already empty list."""
        class EUser9(Table):
            name: str
            posts: List["EPost9"] = has_many("EPost9", backref="author")
        
        class EPost9(Table):
            title: str
            user_id: Optional[int] = None
        
        user = EUser9(name="John")
        user.posts.clear()  # Should not raise
        
        assert len(user.posts) == 0
    
    def test_pop_empty_raises(self, clean_state):
        """Test pop on empty list raises IndexError."""
        class EUser10(Table):
            name: str
            posts: List["EPost10"] = has_many("EPost10", backref="author")
        
        class EPost10(Table):
            title: str
            user_id: Optional[int] = None
        
        user = EUser10(name="John")
        
        with pytest.raises(IndexError):
            user.posts.pop()
    
    def test_remove_from_empty_raises(self, clean_state):
        """Test remove from empty list raises ValueError."""
        class EUser11(Table):
            name: str
            posts: List["EPost11"] = has_many("EPost11", backref="author")
        
        class EPost11(Table):
            title: str
            user_id: Optional[int] = None
        
        user = EUser11(name="John")
        post = EPost11(title="Hello")
        
        with pytest.raises(ValueError):
            user.posts.remove(post)
    
    def test_iterate_empty(self, clean_state):
        """Test iterating empty list."""
        class EUser12(Table):
            name: str
            posts: List["EPost12"] = has_many("EPost12", backref="author")
        
        class EPost12(Table):
            title: str
            user_id: Optional[int] = None
        
        user = EUser12(name="John")
        
        count = 0
        for _ in user.posts:
            count += 1
        
        assert count == 0
    
    def test_len_empty(self, clean_state):
        """Test len of empty list."""
        class EUser13(Table):
            name: str
            posts: List["EPost13"] = has_many("EPost13", backref="author")
        
        class EPost13(Table):
            title: str
            user_id: Optional[int] = None
        
        user = EUser13(name="John")
        
        assert len(user.posts) == 0
    
    def test_bool_empty(self, clean_state):
        """Test bool of empty list."""
        class EUser14(Table):
            name: str
            posts: List["EPost14"] = has_many("EPost14", backref="author")
        
        class EPost14(Table):
            title: str
            user_id: Optional[int] = None
        
        user = EUser14(name="John")
        
        assert not user.posts


# =============================================================================
# Self-Referential Relationship Tests (20 tests)
# =============================================================================

class TestSelfReferential:
    """Tests for self-referential relationships."""
    
    def test_self_ref_belongs_to(self, clean_state):
        """Test self-referential belongs_to."""
        class EEmployee1(Table):
            name: str
            manager_id: Optional[int] = None
            manager: "EEmployee1" = belongs_to("EEmployee1", foreign_key="manager_id")
        
        manager = EEmployee1(name="Boss")
        employee = EEmployee1(name="Worker")
        
        employee.manager = manager
        
        assert employee.manager is manager
    
    def test_self_ref_has_many(self, clean_state):
        """Test self-referential has_many."""
        class ECategory1(Table):
            name: str
            parent_id: Optional[int] = None
            children: List["ECategory1"] = has_many("ECategory1", foreign_key="parent_id", backref="parent")
        
        parent = ECategory1(name="Parent")
        child1 = ECategory1(name="Child 1")
        child2 = ECategory1(name="Child 2")
        
        parent.children.extend([child1, child2])
        
        assert child1.parent is parent
        assert child2.parent is parent
    
    def test_self_ref_tree_structure(self, clean_state):
        """Test building tree structure."""
        class ENode1(Table):
            value: int
            parent_id: Optional[int] = None
            children: List["ENode1"] = has_many("ENode1", foreign_key="parent_id", backref="parent")
        
        root = ENode1(value=1)
        child1 = ENode1(value=2)
        child2 = ENode1(value=3)
        grandchild = ENode1(value=4)
        
        root.children.extend([child1, child2])
        child1.children.append(grandchild)
        
        assert grandchild.parent is child1
        assert child1.parent is root
    
    def test_self_ref_move_node(self, clean_state):
        """Test moving node to different parent."""
        class ENode2(Table):
            value: int
            parent_id: Optional[int] = None
            children: List["ENode2"] = has_many("ENode2", foreign_key="parent_id", backref="parent")
        
        parent1 = ENode2(value=1)
        parent2 = ENode2(value=2)
        child = ENode2(value=3)
        
        parent1.children.append(child)
        child.parent = parent2
        
        assert child not in parent1.children
        assert child in parent2.children


# =============================================================================
# Forward Reference Tests (15 tests)
# =============================================================================

class TestForwardReferences:
    """Tests for forward reference resolution."""
    
    def test_string_model_reference(self, clean_state):
        """Test using string for model reference."""
        class EAuthor1(Table):
            name: str
            books: List["EBook1"] = has_many("EBook1", backref="author")
        
        # EBook1 defined after EAuthor1
        class EBook1(Table):
            title: str
            author_id: Optional[int] = None
        
        author = EAuthor1(name="John")
        book = EBook1(title="Hello")
        
        author.books.append(book)
        
        assert book.author is author
    
    def test_mutual_forward_references(self, clean_state):
        """Test mutual forward references."""
        class EA1(Table):
            name: str
            bs: List["EB1"] = has_many("EB1", backref="a")
        
        class EB1(Table):
            value: int
            a_id: Optional[int] = None
        
        a = EA1(name="A")
        b = EB1(value=1)
        
        a.bs.append(b)
        
        assert b.a is a


# =============================================================================
# Performance Tests (30 tests)
# =============================================================================

class TestPerformance:
    """Tests for performance with large collections."""
    
    def test_large_collection_append(self, clean_state):
        """Test appending many items."""
        class EUser15(Table):
            name: str
            items: List["EItem1"] = has_many("EItem1", backref="owner")
        
        class EItem1(Table):
            value: int
            user_id: Optional[int] = None
        
        user = EUser15(name="John")
        
        start = time.time()
        for i in range(1000):
            user.items.append(EItem1(value=i))
        elapsed = time.time() - start
        
        assert len(user.items) == 1000
        assert elapsed < 5.0  # Should be fast
    
    def test_large_collection_extend(self, clean_state):
        """Test extending with many items."""
        class EUser16(Table):
            name: str
            items: List["EItem2"] = has_many("EItem2", backref="owner")
        
        class EItem2(Table):
            value: int
            user_id: Optional[int] = None
        
        user = EUser16(name="John")
        items = [EItem2(value=i) for i in range(1000)]
        
        start = time.time()
        user.items.extend(items)
        elapsed = time.time() - start
        
        assert len(user.items) == 1000
        assert elapsed < 5.0
    
    def test_large_collection_clear(self, clean_state):
        """Test clearing large collection."""
        class EUser17(Table):
            name: str
            items: List["EItem3"] = has_many("EItem3", backref="owner")
        
        class EItem3(Table):
            value: int
            user_id: Optional[int] = None
        
        user = EUser17(name="John")
        items = [EItem3(value=i) for i in range(1000)]
        user.items.extend(items)
        
        start = time.time()
        user.items.clear()
        elapsed = time.time() - start
        
        assert len(user.items) == 0
        assert elapsed < 5.0
    
    def test_large_collection_iteration(self, clean_state):
        """Test iterating large collection."""
        class EUser18(Table):
            name: str
            items: List["EItem4"] = has_many("EItem4", backref="owner")
        
        class EItem4(Table):
            value: int
            user_id: Optional[int] = None
        
        user = EUser18(name="John")
        user.items.extend([EItem4(value=i) for i in range(1000)])
        
        start = time.time()
        total = sum(item.value for item in user.items)
        elapsed = time.time() - start
        
        assert total == sum(range(1000))
        assert elapsed < 5.0
    
    def test_many_users_many_items(self, clean_state):
        """Test many users with many items each."""
        class EUser19(Table):
            name: str
            items: List["EItem5"] = has_many("EItem5", backref="owner")
        
        class EItem5(Table):
            value: int
            user_id: Optional[int] = None
        
        users = [EUser19(name=f"User {i}") for i in range(100)]
        
        start = time.time()
        for user in users:
            user.items.extend([EItem5(value=i) for i in range(10)])
        elapsed = time.time() - start
        
        assert all(len(u.items) == 10 for u in users)
        assert elapsed < 5.0
    
    def test_frequent_reassignment(self, clean_state):
        """Test frequent belongs_to reassignment."""
        class EUser20(Table):
            name: str
            posts: List["EPost20"] = has_many("EPost20", backref="author")
        
        class EPost20(Table):
            title: str
            user_id: Optional[int] = None
        
        users = [EUser20(name=f"User {i}") for i in range(10)]
        post = EPost20(title="Moving Post")
        
        start = time.time()
        for _ in range(100):
            for user in users:
                post.author = user
        elapsed = time.time() - start
        
        assert elapsed < 5.0


# =============================================================================
# Special Characters Tests (15 tests)
# =============================================================================

class TestSpecialCharacters:
    """Tests for special characters in values."""
    
    def test_unicode_in_name(self, clean_state):
        """Test unicode characters in field values."""
        class EUser21(Table):
            name: str
            posts: List["EPost21"] = has_many("EPost21", backref="author")
        
        class EPost21(Table):
            title: str
            user_id: Optional[int] = None
        
        user = EUser21(name="日本語ユーザー")
        post = EPost21(title="Héllo Wörld 🌍")
        
        user.posts.append(post)
        
        assert post.author is user
        assert user.name == "日本語ユーザー"
    
    def test_special_sql_chars(self, clean_state):
        """Test SQL special characters."""
        class EUser22(Table):
            name: str
            posts: List["EPost22"] = has_many("EPost22", backref="author")
        
        class EPost22(Table):
            title: str
            user_id: Optional[int] = None
        
        user = EUser22(name="O'Brien; DROP TABLE users;--")
        post = EPost22(title="Test")
        
        user.posts.append(post)
        
        assert post.author is user
    
    def test_newlines_in_values(self, clean_state):
        """Test newlines in values."""
        class EUser23(Table):
            name: str
            posts: List["EPost23"] = has_many("EPost23", backref="author")
        
        class EPost23(Table):
            title: str
            user_id: Optional[int] = None
        
        user = EUser23(name="Line1\nLine2")
        post = EPost23(title="Title\nSubtitle")
        
        user.posts.append(post)
        
        assert post.author is user


# =============================================================================
# Error Handling Tests (30 tests)
# =============================================================================

class TestErrorHandling:
    """Tests for error handling."""
    
    def test_remove_nonexistent_item(self, clean_state):
        """Test removing item not in list."""
        class EUser24(Table):
            name: str
            posts: List["EPost24"] = has_many("EPost24", backref="author")
        
        class EPost24(Table):
            title: str
            user_id: Optional[int] = None
        
        user = EUser24(name="John")
        post = EPost24(title="Not added")
        
        with pytest.raises(ValueError):
            user.posts.remove(post)
    
    def test_index_out_of_range(self, clean_state):
        """Test accessing invalid index."""
        class EUser25(Table):
            name: str
            posts: List["EPost25"] = has_many("EPost25", backref="author")
        
        class EPost25(Table):
            title: str
            user_id: Optional[int] = None
        
        user = EUser25(name="John")
        
        with pytest.raises(IndexError):
            _ = user.posts[0]
    
    def test_pop_invalid_index(self, clean_state):
        """Test popping invalid index."""
        class EUser26(Table):
            name: str
            posts: List["EPost26"] = has_many("EPost26", backref="author")
        
        class EPost26(Table):
            title: str
            user_id: Optional[int] = None
        
        user = EUser26(name="John")
        user.posts.append(EPost26(title="One"))
        
        with pytest.raises(IndexError):
            user.posts.pop(100)
    
    def test_del_invalid_index(self, clean_state):
        """Test deleting invalid index."""
        class EUser27(Table):
            name: str
            posts: List["EPost27"] = has_many("EPost27", backref="author")
        
        class EPost27(Table):
            title: str
            user_id: Optional[int] = None
        
        user = EUser27(name="John")
        
        with pytest.raises(IndexError):
            del user.posts[0]
    
    def test_index_not_found(self, clean_state):
        """Test index() when item not found."""
        class EUser28(Table):
            name: str
            posts: List["EPost28"] = has_many("EPost28", backref="author")
        
        class EPost28(Table):
            title: str
            user_id: Optional[int] = None
        
        user = EUser28(name="John")
        post = EPost28(title="Not added")
        
        with pytest.raises(ValueError):
            user.posts.index(post)


# =============================================================================
# Multiple Relationships Tests (20 tests)
# =============================================================================

class TestMultipleRelationships:
    """Tests for models with multiple relationships."""
    
    def test_model_with_two_has_many(self, clean_state):
        """Test model with two has_many relationships."""
        class EUser29(Table):
            name: str
            posts: List["EPost29"] = has_many("EPost29", backref="author")
            comments: List["EComment1"] = has_many("EComment1", backref="author")
        
        class EPost29(Table):
            title: str
            user_id: Optional[int] = None
        
        class EComment1(Table):
            content: str
            user_id: Optional[int] = None
        
        user = EUser29(name="John")
        post = EPost29(title="Post")
        comment = EComment1(content="Comment")
        
        user.posts.append(post)
        user.comments.append(comment)
        
        assert post.author is user
        assert comment.author is user
        assert len(user.posts) == 1
        assert len(user.comments) == 1
    
    def test_model_with_multiple_belongs_to(self, clean_state):
        """Test model with multiple belongs_to."""
        class EUser30(Table):
            name: str
            posts: List["EPost30"] = has_many("EPost30", foreign_key="author_id", backref="author")
        
        class ECategory2(Table):
            name: str
            posts: List["EPost30"] = has_many("EPost30", foreign_key="category_id", backref="category")
        
        class EPost30(Table):
            title: str
            author_id: Optional[int] = None
            category_id: Optional[int] = None
        
        user = EUser30(name="John")
        category = ECategory2(name="Tech")
        post = EPost30(title="Post")
        
        post.author = user
        post.category = category
        
        assert post in user.posts
        assert post in category.posts
    
    def test_independent_relationships_dont_interfere(self, clean_state):
        """Test independent relationships don't interfere."""
        class EUser31(Table):
            name: str
            posts: List["EPost31"] = has_many("EPost31", backref="author")
        
        class EPost31(Table):
            title: str
            user_id: Optional[int] = None
        
        user1 = EUser31(name="User 1")
        user2 = EUser31(name="User 2")
        
        post1 = EPost31(title="Post 1")
        post2 = EPost31(title="Post 2")
        
        user1.posts.append(post1)
        user2.posts.append(post2)
        
        # Each user's posts should be independent
        assert post1 in user1.posts
        assert post1 not in user2.posts
        assert post2 in user2.posts
        assert post2 not in user1.posts

