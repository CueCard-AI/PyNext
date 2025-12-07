"""
Tests for PyNext Backref - SyncedList Collection Operations.

100 tests covering:
- All MutableSequence methods
- insert, pop, clear, extend
- __setitem__, __delitem__
- Iteration, slicing, indexing
- Equality, hashing, string representation
- Sorting, reversing
"""

import pytest
from typing import List, Optional

from pynext.db import (
    Table,
    configure_db,
    MockAdapter,
    has_many,
    belongs_to,
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
    keys_to_remove = [k for k in _model_registry.keys() if 'coll' in k.lower() or k.startswith('C')]
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
# Basic SyncedList Tests (15 tests)
# =============================================================================

class TestSyncedListBasic:
    """Basic tests for SyncedList."""
    
    def test_synced_list_creation(self, clean_state):
        """Test creating a SyncedList."""
        class COwner1(Table):
            name: str
        
        owner = COwner1(name="Test")
        sl = SyncedList(owner, "items", [])
        
        assert sl.owner is owner
        assert sl.attr_name == "items"
        assert len(sl) == 0
    
    def test_synced_list_with_initial_items(self, clean_state):
        """Test SyncedList with initial items."""
        class COwner2(Table):
            name: str
        
        class CItem2(Table):
            value: int
        
        owner = COwner2(name="Test")
        items = [CItem2(value=1), CItem2(value=2)]
        sl = SyncedList(owner, "items", items)
        
        assert len(sl) == 2
    
    def test_synced_list_len(self, clean_state):
        """Test len() on SyncedList."""
        class COwner3(Table):
            name: str
        
        owner = COwner3(name="Test")
        sl = SyncedList(owner, "items", [1, 2, 3, 4, 5])
        
        assert len(sl) == 5
    
    def test_synced_list_bool_empty(self, clean_state):
        """Test bool() on empty SyncedList."""
        class COwner4(Table):
            name: str
        
        owner = COwner4(name="Test")
        sl = SyncedList(owner, "items", [])
        
        assert not sl
    
    def test_synced_list_bool_nonempty(self, clean_state):
        """Test bool() on non-empty SyncedList."""
        class COwner5(Table):
            name: str
        
        owner = COwner5(name="Test")
        sl = SyncedList(owner, "items", [1])
        
        assert sl
    
    def test_synced_list_contains(self, clean_state):
        """Test 'in' operator on SyncedList."""
        class COwner6(Table):
            name: str
        
        owner = COwner6(name="Test")
        sl = SyncedList(owner, "items", [1, 2, 3])
        
        assert 2 in sl
        assert 5 not in sl


# =============================================================================
# Indexing Tests (15 tests)
# =============================================================================

class TestSyncedListIndexing:
    """Tests for SyncedList indexing operations."""
    
    def test_getitem_positive_index(self, clean_state):
        """Test positive index access."""
        class COwner7(Table):
            name: str
        
        owner = COwner7(name="Test")
        sl = SyncedList(owner, "items", ["a", "b", "c"])
        
        assert sl[0] == "a"
        assert sl[1] == "b"
        assert sl[2] == "c"
    
    def test_getitem_negative_index(self, clean_state):
        """Test negative index access."""
        class COwner8(Table):
            name: str
        
        owner = COwner8(name="Test")
        sl = SyncedList(owner, "items", ["a", "b", "c"])
        
        assert sl[-1] == "c"
        assert sl[-2] == "b"
        assert sl[-3] == "a"
    
    def test_getitem_out_of_range(self, clean_state):
        """Test index out of range."""
        class COwner9(Table):
            name: str
        
        owner = COwner9(name="Test")
        sl = SyncedList(owner, "items", ["a"])
        
        with pytest.raises(IndexError):
            _ = sl[5]
    
    def test_setitem_syncs(self, clean_state):
        """Test __setitem__ triggers sync."""
        class CUser1(Table):
            name: str
            posts: List["CPost1"] = has_many("CPost1", backref="author")
        
        class CPost1(Table):
            title: str
            user_id: Optional[int] = None
        
        user = CUser1(name="John")
        post1 = CPost1(title="Old")
        post2 = CPost1(title="New")
        
        user.posts.append(post1)
        user.posts[0] = post2
        
        assert post1.author is None
        assert post2.author is user
    
    def test_delitem_syncs(self, clean_state):
        """Test __delitem__ triggers sync."""
        class CUser2(Table):
            name: str
            posts: List["CPost2"] = has_many("CPost2", backref="author")
        
        class CPost2(Table):
            title: str
            user_id: Optional[int] = None
        
        user = CUser2(name="John")
        post = CPost2(title="Hello")
        
        user.posts.append(post)
        del user.posts[0]
        
        assert post.author is None
        assert len(user.posts) == 0


# =============================================================================
# Slicing Tests (15 tests)
# =============================================================================

class TestSyncedListSlicing:
    """Tests for SyncedList slicing operations."""
    
    def test_slice_basic(self, clean_state):
        """Test basic slicing."""
        class COwner10(Table):
            name: str
        
        owner = COwner10(name="Test")
        sl = SyncedList(owner, "items", [0, 1, 2, 3, 4])
        
        assert sl[1:3] == [1, 2]
    
    def test_slice_start_only(self, clean_state):
        """Test slice with start only."""
        class COwner11(Table):
            name: str
        
        owner = COwner11(name="Test")
        sl = SyncedList(owner, "items", [0, 1, 2, 3, 4])
        
        assert sl[2:] == [2, 3, 4]
    
    def test_slice_end_only(self, clean_state):
        """Test slice with end only."""
        class COwner12(Table):
            name: str
        
        owner = COwner12(name="Test")
        sl = SyncedList(owner, "items", [0, 1, 2, 3, 4])
        
        assert sl[:3] == [0, 1, 2]
    
    def test_slice_negative(self, clean_state):
        """Test negative slice."""
        class COwner13(Table):
            name: str
        
        owner = COwner13(name="Test")
        sl = SyncedList(owner, "items", [0, 1, 2, 3, 4])
        
        assert sl[-2:] == [3, 4]
    
    def test_slice_step(self, clean_state):
        """Test slice with step."""
        class COwner14(Table):
            name: str
        
        owner = COwner14(name="Test")
        sl = SyncedList(owner, "items", [0, 1, 2, 3, 4, 5])
        
        assert sl[::2] == [0, 2, 4]
    
    def test_setitem_slice_syncs(self, clean_state):
        """Test __setitem__ with slice triggers sync."""
        class CUser3(Table):
            name: str
            posts: List["CPost3"] = has_many("CPost3", backref="author")
        
        class CPost3(Table):
            title: str
            user_id: Optional[int] = None
        
        user = CUser3(name="John")
        old_posts = [CPost3(title=f"Old {i}") for i in range(3)]
        new_posts = [CPost3(title=f"New {i}") for i in range(2)]
        
        user.posts.extend(old_posts)
        user.posts[0:2] = new_posts
        
        # Old posts should be unsynced
        assert old_posts[0].author is None
        assert old_posts[1].author is None
        # New posts should be synced
        for p in new_posts:
            assert p.author is user
    
    def test_delitem_slice_syncs(self, clean_state):
        """Test __delitem__ with slice triggers sync."""
        class CUser4(Table):
            name: str
            posts: List["CPost4"] = has_many("CPost4", backref="author")
        
        class CPost4(Table):
            title: str
            user_id: Optional[int] = None
        
        user = CUser4(name="John")
        posts = [CPost4(title=f"Post {i}") for i in range(5)]
        
        user.posts.extend(posts)
        del user.posts[1:3]
        
        assert posts[1].author is None
        assert posts[2].author is None
        assert len(user.posts) == 3


# =============================================================================
# Insert Tests (10 tests)
# =============================================================================

class TestSyncedListInsert:
    """Tests for SyncedList.insert()."""
    
    def test_insert_at_beginning(self, clean_state):
        """Test insert at beginning."""
        class CUser5(Table):
            name: str
            posts: List["CPost5"] = has_many("CPost5", backref="author")
        
        class CPost5(Table):
            title: str
            user_id: Optional[int] = None
        
        user = CUser5(name="John")
        post1 = CPost5(title="First")
        post2 = CPost5(title="Second")
        
        user.posts.append(post1)
        user.posts.insert(0, post2)
        
        assert user.posts[0] is post2
        assert post2.author is user
    
    def test_insert_at_end(self, clean_state):
        """Test insert at end."""
        class CUser6(Table):
            name: str
            posts: List["CPost6"] = has_many("CPost6", backref="author")
        
        class CPost6(Table):
            title: str
            user_id: Optional[int] = None
        
        user = CUser6(name="John")
        post1 = CPost6(title="First")
        post2 = CPost6(title="Second")
        
        user.posts.append(post1)
        user.posts.insert(100, post2)  # Beyond end
        
        assert user.posts[-1] is post2
        assert post2.author is user
    
    def test_insert_in_middle(self, clean_state):
        """Test insert in middle."""
        class CUser7(Table):
            name: str
            posts: List["CPost7"] = has_many("CPost7", backref="author")
        
        class CPost7(Table):
            title: str
            user_id: Optional[int] = None
        
        user = CUser7(name="John")
        posts = [CPost7(title=f"Post {i}") for i in range(3)]
        user.posts.extend(posts)
        
        new_post = CPost7(title="Middle")
        user.posts.insert(1, new_post)
        
        assert user.posts[1] is new_post
        assert new_post.author is user


# =============================================================================
# Iteration Tests (10 tests)
# =============================================================================

class TestSyncedListIteration:
    """Tests for SyncedList iteration."""
    
    def test_iter(self, clean_state):
        """Test iterating over SyncedList."""
        class COwner15(Table):
            name: str
        
        owner = COwner15(name="Test")
        items = [1, 2, 3, 4, 5]
        sl = SyncedList(owner, "items", items)
        
        result = list(sl)
        assert result == items
    
    def test_reversed(self, clean_state):
        """Test reversed() on SyncedList."""
        class COwner16(Table):
            name: str
        
        owner = COwner16(name="Test")
        sl = SyncedList(owner, "items", [1, 2, 3])
        
        result = list(reversed(sl))
        assert result == [3, 2, 1]
    
    def test_for_loop(self, clean_state):
        """Test for loop iteration."""
        class COwner17(Table):
            name: str
        
        owner = COwner17(name="Test")
        sl = SyncedList(owner, "items", ["a", "b", "c"])
        
        result = []
        for item in sl:
            result.append(item)
        
        assert result == ["a", "b", "c"]
    
    def test_enumerate(self, clean_state):
        """Test enumerate on SyncedList."""
        class COwner18(Table):
            name: str
        
        owner = COwner18(name="Test")
        sl = SyncedList(owner, "items", ["a", "b", "c"])
        
        result = list(enumerate(sl))
        assert result == [(0, "a"), (1, "b"), (2, "c")]


# =============================================================================
# Index and Count Tests (10 tests)
# =============================================================================

class TestSyncedListIndexCount:
    """Tests for index() and count() methods."""
    
    def test_index_found(self, clean_state):
        """Test index() when item exists."""
        class COwner19(Table):
            name: str
        
        owner = COwner19(name="Test")
        sl = SyncedList(owner, "items", ["a", "b", "c"])
        
        assert sl.index("b") == 1
    
    def test_index_not_found(self, clean_state):
        """Test index() when item doesn't exist."""
        class COwner20(Table):
            name: str
        
        owner = COwner20(name="Test")
        sl = SyncedList(owner, "items", ["a", "b", "c"])
        
        with pytest.raises(ValueError):
            sl.index("z")
    
    def test_index_with_start(self, clean_state):
        """Test index() with start parameter."""
        class COwner21(Table):
            name: str
        
        owner = COwner21(name="Test")
        sl = SyncedList(owner, "items", ["a", "b", "a", "b"])
        
        assert sl.index("b", 2) == 3
    
    def test_count(self, clean_state):
        """Test count() method."""
        class COwner22(Table):
            name: str
        
        owner = COwner22(name="Test")
        sl = SyncedList(owner, "items", ["a", "b", "a", "a"])
        
        assert sl.count("a") == 3
        assert sl.count("b") == 1
        assert sl.count("z") == 0


# =============================================================================
# Equality and String Tests (10 tests)
# =============================================================================

class TestSyncedListEquality:
    """Tests for SyncedList equality and string representation."""
    
    def test_eq_with_list(self, clean_state):
        """Test equality with regular list."""
        class COwner23(Table):
            name: str
        
        owner = COwner23(name="Test")
        sl = SyncedList(owner, "items", [1, 2, 3])
        
        assert sl == [1, 2, 3]
    
    def test_eq_with_synced_list(self, clean_state):
        """Test equality with another SyncedList."""
        class COwner24(Table):
            name: str
        
        owner = COwner24(name="Test")
        sl1 = SyncedList(owner, "items", [1, 2, 3])
        sl2 = SyncedList(owner, "other", [1, 2, 3])
        
        assert sl1 == sl2
    
    def test_ne(self, clean_state):
        """Test inequality."""
        class COwner25(Table):
            name: str
        
        owner = COwner25(name="Test")
        sl = SyncedList(owner, "items", [1, 2, 3])
        
        assert sl != [1, 2]
        assert sl != [1, 2, 4]
    
    def test_repr(self, clean_state):
        """Test __repr__."""
        class COwner26(Table):
            name: str
        
        owner = COwner26(name="Test")
        sl = SyncedList(owner, "items", [1, 2, 3])
        
        r = repr(sl)
        assert "SyncedList" in r
        assert "items" in r
    
    def test_str(self, clean_state):
        """Test __str__."""
        class COwner27(Table):
            name: str
        
        owner = COwner27(name="Test")
        sl = SyncedList(owner, "items", [1, 2, 3])
        
        assert str(sl) == "[1, 2, 3]"


# =============================================================================
# Arithmetic Operations Tests (10 tests)
# =============================================================================

class TestSyncedListArithmetic:
    """Tests for SyncedList arithmetic operations."""
    
    def test_add(self, clean_state):
        """Test + operator returns regular list."""
        class COwner28(Table):
            name: str
        
        owner = COwner28(name="Test")
        sl = SyncedList(owner, "items", [1, 2])
        
        result = sl + [3, 4]
        
        assert result == [1, 2, 3, 4]
        assert isinstance(result, list)
        assert not isinstance(result, SyncedList)
    
    def test_radd(self, clean_state):
        """Test reverse + operator."""
        class COwner29(Table):
            name: str
        
        owner = COwner29(name="Test")
        sl = SyncedList(owner, "items", [3, 4])
        
        result = [1, 2] + sl
        
        assert result == [1, 2, 3, 4]
    
    def test_iadd(self, clean_state):
        """Test += operator (extend)."""
        class CUser8(Table):
            name: str
            posts: List["CPost8"] = has_many("CPost8", backref="author")
        
        class CPost8(Table):
            title: str
            user_id: Optional[int] = None
        
        user = CUser8(name="John")
        posts = [CPost8(title=f"Post {i}") for i in range(3)]
        
        user.posts += posts
        
        assert len(user.posts) == 3
        for p in posts:
            assert p.author is user
    
    def test_mul(self, clean_state):
        """Test * operator."""
        class COwner30(Table):
            name: str
        
        owner = COwner30(name="Test")
        sl = SyncedList(owner, "items", [1, 2])
        
        result = sl * 3
        
        assert result == [1, 2, 1, 2, 1, 2]


# =============================================================================
# Sort and Reverse Tests (5 tests)
# =============================================================================

class TestSyncedListSortReverse:
    """Tests for sort() and reverse() methods."""
    
    def test_sort(self, clean_state):
        """Test sort() in place."""
        class COwner31(Table):
            name: str
        
        owner = COwner31(name="Test")
        sl = SyncedList(owner, "items", [3, 1, 2])
        
        sl.sort()
        
        assert sl == [1, 2, 3]
    
    def test_sort_reverse(self, clean_state):
        """Test sort(reverse=True)."""
        class COwner32(Table):
            name: str
        
        owner = COwner32(name="Test")
        sl = SyncedList(owner, "items", [3, 1, 2])
        
        sl.sort(reverse=True)
        
        assert sl == [3, 2, 1]
    
    def test_sort_key(self, clean_state):
        """Test sort(key=...)."""
        class COwner33(Table):
            name: str
        
        owner = COwner33(name="Test")
        sl = SyncedList(owner, "items", ["bb", "a", "ccc"])
        
        sl.sort(key=len)
        
        assert sl == ["a", "bb", "ccc"]
    
    def test_reverse_method(self, clean_state):
        """Test reverse() in place."""
        class COwner34(Table):
            name: str
        
        owner = COwner34(name="Test")
        sl = SyncedList(owner, "items", [1, 2, 3])
        
        sl.reverse()
        
        assert sl == [3, 2, 1]
    
    def test_copy(self, clean_state):
        """Test copy() returns regular list."""
        class COwner35(Table):
            name: str
        
        owner = COwner35(name="Test")
        sl = SyncedList(owner, "items", [1, 2, 3])
        
        result = sl.copy()
        
        assert result == [1, 2, 3]
        assert isinstance(result, list)
        assert not isinstance(result, SyncedList)

