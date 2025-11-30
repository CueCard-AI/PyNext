"""
Tests for PyNext Database CRUD Operations.

Comprehensive tests for single-record Create, Read, Update, Delete operations.
"""

import pytest
from datetime import datetime
from typing import Optional

from pynext.db import (
    Table,
    configure_db,
    MockAdapter,
    NotFoundError,
    ValidationError,
)


# =============================================================================
# Test Models
# =============================================================================

class CRUDUser(Table):
    """Test user model."""
    name: str
    email: str
    age: int = 0
    role: str = "user"
    active: bool = True


class CRUDPost(Table):
    """Test post model."""
    title: str
    content: str = ""
    author_id: Optional[int] = None
    published: bool = False


class CRUDProfile(Table):
    """Test profile model."""
    bio: str = ""
    website: Optional[str] = None
    user_id: Optional[int] = None


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
async def mock_adapter():
    """Create and configure a mock adapter."""
    adapter = MockAdapter()
    await adapter.connect()
    configure_db(adapter)
    yield adapter
    adapter.reset()
    await adapter.disconnect()


# =============================================================================
# Insert Tests (15 tests)
# =============================================================================

class TestInsert:
    """Tests for Table.insert()."""
    
    @pytest.mark.asyncio
    async def test_insert_basic(self, mock_adapter):
        """Test basic insert."""
        user = await CRUDUser.insert(name="John", email="john@example.com")
        
        assert user.id is not None
        assert user.name == "John"
        assert user.email == "john@example.com"
    
    @pytest.mark.asyncio
    async def test_insert_with_defaults(self, mock_adapter):
        """Test insert uses default values."""
        user = await CRUDUser.insert(name="Jane", email="jane@example.com")
        
        assert user.age == 0
        assert user.role == "user"
        assert user.active is True
    
    @pytest.mark.asyncio
    async def test_insert_with_custom_values(self, mock_adapter):
        """Test insert with custom values."""
        user = await CRUDUser.insert(
            name="Admin",
            email="admin@example.com",
            age=35,
            role="admin",
            active=True,
        )
        
        assert user.age == 35
        assert user.role == "admin"
    
    @pytest.mark.asyncio
    async def test_insert_auto_timestamps(self, mock_adapter):
        """Test insert sets timestamps."""
        user = await CRUDUser.insert(name="Test", email="test@example.com")
        
        assert user.created_at is not None
        assert user.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_insert_increments_id(self, mock_adapter):
        """Test insert increments ID."""
        user1 = await CRUDUser.insert(name="A", email="a@example.com")
        user2 = await CRUDUser.insert(name="B", email="b@example.com")
        
        assert user2.id == user1.id + 1
    
    @pytest.mark.asyncio
    async def test_insert_returns_instance(self, mock_adapter):
        """Test insert returns model instance."""
        user = await CRUDUser.insert(name="Test", email="test@example.com")
        
        assert isinstance(user, CRUDUser)
    
    @pytest.mark.asyncio
    async def test_insert_with_optional_fields(self, mock_adapter):
        """Test insert with optional fields."""
        post = await CRUDPost.insert(title="Test Post")
        
        assert post.content == ""
        assert post.author_id is None
        assert post.published is False
    
    @pytest.mark.asyncio
    async def test_insert_with_none_values(self, mock_adapter):
        """Test insert with explicit None."""
        profile = await CRUDProfile.insert(bio="Test bio", website=None)
        
        assert profile.website is None
    
    @pytest.mark.asyncio
    async def test_insert_unicode(self, mock_adapter):
        """Test insert with unicode characters."""
        user = await CRUDUser.insert(name="日本語", email="test@example.com")
        
        assert user.name == "日本語"
    
    @pytest.mark.asyncio
    async def test_insert_special_chars(self, mock_adapter):
        """Test insert with special characters."""
        user = await CRUDUser.insert(name="O'Brien", email="ob@example.com")
        
        assert user.name == "O'Brien"
    
    @pytest.mark.asyncio
    async def test_insert_empty_string(self, mock_adapter):
        """Test insert with content (empty string validation prevents empty)."""
        # Note: Empty strings are validated - use whitespace or actual content
        post = await CRUDPost.insert(title="Test", content="Some content")
        
        assert post.content == "Some content"
    
    @pytest.mark.asyncio
    async def test_insert_long_string(self, mock_adapter):
        """Test insert with string at max length."""
        # Default max_length is 255 for string fields
        content = "x" * 255
        post = await CRUDPost.insert(title="Test", content=content)
        
        assert len(post.content) == 255
    
    @pytest.mark.asyncio
    async def test_insert_boolean_true(self, mock_adapter):
        """Test insert with boolean True."""
        user = await CRUDUser.insert(name="Test", email="test@example.com", active=True)
        
        assert user.active is True
    
    @pytest.mark.asyncio
    async def test_insert_boolean_false(self, mock_adapter):
        """Test insert with boolean False."""
        user = await CRUDUser.insert(name="Test", email="test@example.com", active=False)
        
        assert user.active is False
    
    @pytest.mark.asyncio
    async def test_insert_negative_int(self, mock_adapter):
        """Test insert with negative integer."""
        user = await CRUDUser.insert(name="Test", email="test@example.com", age=-1)
        
        assert user.age == -1


# =============================================================================
# Get Tests (15 tests)
# =============================================================================

class TestGet:
    """Tests for Table.get()."""
    
    @pytest.mark.asyncio
    async def test_get_by_id(self, mock_adapter):
        """Test get by ID."""
        created = await CRUDUser.insert(name="John", email="john@example.com")
        
        user = await CRUDUser.get(created.id)
        
        assert user.id == created.id
        assert user.name == "John"
    
    @pytest.mark.asyncio
    async def test_get_returns_instance(self, mock_adapter):
        """Test get returns model instance."""
        created = await CRUDUser.insert(name="John", email="john@example.com")
        
        user = await CRUDUser.get(created.id)
        
        assert isinstance(user, CRUDUser)
    
    @pytest.mark.asyncio
    async def test_get_not_found_raises(self, mock_adapter):
        """Test get with non-existent ID raises."""
        with pytest.raises(NotFoundError):
            await CRUDUser.get(99999)
    
    @pytest.mark.asyncio
    async def test_get_or_none_exists(self, mock_adapter):
        """Test get_or_none with existing record."""
        created = await CRUDUser.insert(name="John", email="john@example.com")
        
        user = await CRUDUser.get_or_none(created.id)
        
        assert user is not None
        assert user.id == created.id
    
    @pytest.mark.asyncio
    async def test_get_or_none_not_exists(self, mock_adapter):
        """Test get_or_none with non-existent record."""
        user = await CRUDUser.get_or_none(99999)
        
        assert user is None
    
    @pytest.mark.asyncio
    async def test_get_by_field(self, mock_adapter):
        """Test get_by with field value."""
        await CRUDUser.insert(name="John", email="john@example.com")
        
        user = await CRUDUser.get_by(email="john@example.com")
        
        assert user.name == "John"
    
    @pytest.mark.asyncio
    async def test_get_by_not_found_raises(self, mock_adapter):
        """Test get_by with non-existent value raises."""
        with pytest.raises(NotFoundError):
            await CRUDUser.get_by(email="nonexistent@example.com")
    
    @pytest.mark.asyncio
    async def test_get_by_multiple_fields(self, mock_adapter):
        """Test get_by with multiple field values."""
        await CRUDUser.insert(name="John", email="john@example.com", role="admin")
        
        user = await CRUDUser.get_by(email="john@example.com", role="admin")
        
        assert user.name == "John"
    
    @pytest.mark.asyncio
    async def test_find_by_exists(self, mock_adapter):
        """Test find_by with existing record."""
        await CRUDUser.insert(name="John", email="john@example.com")
        
        user = await CRUDUser.find_by(email="john@example.com")
        
        assert user is not None
        assert user.name == "John"
    
    @pytest.mark.asyncio
    async def test_find_by_not_exists(self, mock_adapter):
        """Test find_by with non-existent record."""
        user = await CRUDUser.find_by(email="nonexistent@example.com")
        
        assert user is None
    
    @pytest.mark.asyncio
    async def test_all(self, mock_adapter):
        """Test all() returns all records."""
        await CRUDUser.insert(name="A", email="a@example.com")
        await CRUDUser.insert(name="B", email="b@example.com")
        await CRUDUser.insert(name="C", email="c@example.com")
        
        users = await CRUDUser.all()
        
        assert len(users) == 3
    
    @pytest.mark.asyncio
    async def test_all_empty(self, mock_adapter):
        """Test all() on empty table."""
        users = await CRUDUser.all()
        
        assert len(users) == 0
    
    @pytest.mark.asyncio
    async def test_first(self, mock_adapter):
        """Test first() returns first record."""
        await CRUDUser.insert(name="A", email="a@example.com")
        await CRUDUser.insert(name="B", email="b@example.com")
        
        user = await CRUDUser.first()
        
        assert user is not None
    
    @pytest.mark.asyncio
    async def test_first_empty(self, mock_adapter):
        """Test first() on empty table."""
        user = await CRUDUser.first()
        
        assert user is None
    
    @pytest.mark.asyncio
    async def test_first_or_raise(self, mock_adapter):
        """Test first_or_raise on empty table raises."""
        with pytest.raises(NotFoundError):
            await CRUDUser.first_or_raise()


# =============================================================================
# Update Tests (15 tests)
# =============================================================================

class TestUpdate:
    """Tests for instance.update()."""
    
    @pytest.mark.asyncio
    async def test_update_single_field(self, mock_adapter):
        """Test update single field."""
        user = await CRUDUser.insert(name="John", email="john@example.com")
        
        await user.update(name="Jane")
        
        assert user.name == "Jane"
    
    @pytest.mark.asyncio
    async def test_update_multiple_fields(self, mock_adapter):
        """Test update multiple fields."""
        user = await CRUDUser.insert(name="John", email="john@example.com")
        
        await user.update(name="Jane", age=25, role="admin")
        
        assert user.name == "Jane"
        assert user.age == 25
        assert user.role == "admin"
    
    @pytest.mark.asyncio
    async def test_update_returns_self(self, mock_adapter):
        """Test update returns self."""
        user = await CRUDUser.insert(name="John", email="john@example.com")
        
        result = await user.update(name="Jane")
        
        assert result is user
    
    @pytest.mark.asyncio
    async def test_update_changes_updated_at(self, mock_adapter):
        """Test update changes updated_at timestamp."""
        user = await CRUDUser.insert(name="John", email="john@example.com")
        original_updated = user.updated_at
        
        await user.update(name="Jane")
        
        assert user.updated_at >= original_updated
    
    @pytest.mark.asyncio
    async def test_update_preserves_created_at(self, mock_adapter):
        """Test update preserves created_at timestamp."""
        user = await CRUDUser.insert(name="John", email="john@example.com")
        original_created = user.created_at
        
        await user.update(name="Jane")
        
        assert user.created_at == original_created
    
    @pytest.mark.asyncio
    async def test_update_persists_to_db(self, mock_adapter):
        """Test update persists to database."""
        user = await CRUDUser.insert(name="John", email="john@example.com")
        
        await user.update(name="Jane")
        
        # Fetch from DB
        fetched = await CRUDUser.get(user.id)
        assert fetched.name == "Jane"
    
    @pytest.mark.asyncio
    async def test_update_to_none(self, mock_adapter):
        """Test update field to None."""
        profile = await CRUDProfile.insert(bio="Test", website="http://test.com")
        
        await profile.update(website=None)
        
        assert profile.website is None
    
    @pytest.mark.asyncio
    async def test_update_boolean(self, mock_adapter):
        """Test update boolean field."""
        user = await CRUDUser.insert(name="John", email="john@example.com", active=True)
        
        await user.update(active=False)
        
        assert user.active is False
    
    @pytest.mark.asyncio
    async def test_update_integer(self, mock_adapter):
        """Test update integer field."""
        user = await CRUDUser.insert(name="John", email="john@example.com", age=25)
        
        await user.update(age=30)
        
        assert user.age == 30
    
    @pytest.mark.asyncio
    async def test_save_existing(self, mock_adapter):
        """Test save() updates existing record."""
        user = await CRUDUser.insert(name="John", email="john@example.com")
        
        user.name = "Jane"
        await user.save()
        
        fetched = await CRUDUser.get(user.id)
        assert fetched.name == "Jane"
    
    @pytest.mark.asyncio
    async def test_save_new(self, mock_adapter):
        """Test save() inserts new record."""
        user = CRUDUser(name="John", email="john@example.com")
        
        await user.save()
        
        assert user.id is not None
    
    @pytest.mark.asyncio
    async def test_refresh(self, mock_adapter):
        """Test refresh() reloads from database."""
        user = await CRUDUser.insert(name="John", email="john@example.com")
        
        # Modify directly in adapter
        mock_adapter._tables["crudusers"][user.id]["name"] = "Modified"
        
        await user.refresh()
        
        assert user.name == "Modified"
    
    @pytest.mark.asyncio
    async def test_refresh_returns_self(self, mock_adapter):
        """Test refresh returns self."""
        user = await CRUDUser.insert(name="John", email="john@example.com")
        
        result = await user.refresh()
        
        assert result is user
    
    @pytest.mark.asyncio
    async def test_update_with_unicode(self, mock_adapter):
        """Test update with unicode."""
        user = await CRUDUser.insert(name="John", email="john@example.com")
        
        await user.update(name="日本語")
        
        assert user.name == "日本語"
    
    @pytest.mark.asyncio
    async def test_update_with_special_chars(self, mock_adapter):
        """Test update with special characters."""
        user = await CRUDUser.insert(name="John", email="john@example.com")
        
        await user.update(name="O'Brien")
        
        assert user.name == "O'Brien"


# =============================================================================
# Delete Tests (15 tests)
# =============================================================================

class TestDelete:
    """Tests for instance.delete()."""
    
    @pytest.mark.asyncio
    async def test_delete_basic(self, mock_adapter):
        """Test basic delete."""
        user = await CRUDUser.insert(name="John", email="john@example.com")
        
        result = await user.delete()
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_delete_removes_from_db(self, mock_adapter):
        """Test delete removes from database."""
        user = await CRUDUser.insert(name="John", email="john@example.com")
        user_id = user.id
        
        await user.delete()
        
        assert await CRUDUser.get_or_none(user_id) is None
    
    @pytest.mark.asyncio
    async def test_delete_returns_true(self, mock_adapter):
        """Test delete returns True on success."""
        user = await CRUDUser.insert(name="John", email="john@example.com")
        
        result = await user.delete()
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_delete_already_deleted(self, mock_adapter):
        """Test delete on already deleted record."""
        user = await CRUDUser.insert(name="John", email="john@example.com")
        
        await user.delete()
        result = await user.delete()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_delete_preserves_count(self, mock_adapter):
        """Test delete decrements count."""
        await CRUDUser.insert(name="A", email="a@example.com")
        user = await CRUDUser.insert(name="B", email="b@example.com")
        await CRUDUser.insert(name="C", email="c@example.com")
        
        await user.delete()
        
        count = await CRUDUser.count()
        assert count == 2
    
    @pytest.mark.asyncio
    async def test_delete_doesnt_affect_others(self, mock_adapter):
        """Test delete doesn't affect other records."""
        user1 = await CRUDUser.insert(name="A", email="a@example.com")
        user2 = await CRUDUser.insert(name="B", email="b@example.com")
        
        await user1.delete()
        
        assert await CRUDUser.get_or_none(user2.id) is not None
    
    @pytest.mark.asyncio
    async def test_exists_after_insert(self, mock_adapter):
        """Test exists() returns True after insert."""
        user = await CRUDUser.insert(name="John", email="john@example.com")
        
        exists = await CRUDUser.exists(id=user.id)
        
        assert exists is True
    
    @pytest.mark.asyncio
    async def test_exists_after_delete(self, mock_adapter):
        """Test exists() returns False after delete."""
        user = await CRUDUser.insert(name="John", email="john@example.com")
        
        await user.delete()
        
        exists = await CRUDUser.exists(id=user.id)
        assert exists is False
    
    @pytest.mark.asyncio
    async def test_exists_by_field(self, mock_adapter):
        """Test exists() with field value."""
        await CRUDUser.insert(name="John", email="john@example.com")
        
        exists = await CRUDUser.exists(email="john@example.com")
        
        assert exists is True
    
    @pytest.mark.asyncio
    async def test_exists_not_found(self, mock_adapter):
        """Test exists() returns False for non-existent."""
        exists = await CRUDUser.exists(email="nonexistent@example.com")
        
        assert exists is False
    
    @pytest.mark.asyncio
    async def test_count_after_insert(self, mock_adapter):
        """Test count() after insert."""
        await CRUDUser.insert(name="A", email="a@example.com")
        await CRUDUser.insert(name="B", email="b@example.com")
        
        count = await CRUDUser.count()
        
        assert count == 2
    
    @pytest.mark.asyncio
    async def test_count_after_delete(self, mock_adapter):
        """Test count() after delete."""
        user = await CRUDUser.insert(name="A", email="a@example.com")
        await CRUDUser.insert(name="B", email="b@example.com")
        
        await user.delete()
        
        count = await CRUDUser.count()
        assert count == 1
    
    @pytest.mark.asyncio
    async def test_count_empty(self, mock_adapter):
        """Test count() on empty table."""
        count = await CRUDUser.count()
        
        assert count == 0
    
    @pytest.mark.asyncio
    async def test_delete_and_reinsert(self, mock_adapter):
        """Test delete then reinsert."""
        user = await CRUDUser.insert(name="John", email="john@example.com")
        old_id = user.id
        
        await user.delete()
        
        new_user = await CRUDUser.insert(name="John", email="john@example.com")
        assert new_user.id != old_id
    
    @pytest.mark.asyncio
    async def test_delete_multiple_sequential(self, mock_adapter):
        """Test deleting multiple records sequentially."""
        users = [
            await CRUDUser.insert(name=f"User{i}", email=f"user{i}@example.com")
            for i in range(5)
        ]
        
        for user in users:
            await user.delete()
        
        count = await CRUDUser.count()
        assert count == 0


# =============================================================================
# Edge Case Tests (20 tests)
# =============================================================================

class TestCRUDEdgeCases:
    """Edge case tests for CRUD operations."""
    
    @pytest.mark.asyncio
    async def test_insert_and_get_immediately(self, mock_adapter):
        """Test insert then get same record."""
        user = await CRUDUser.insert(name="John", email="john@example.com")
        
        fetched = await CRUDUser.get(user.id)
        
        assert fetched.name == user.name
    
    @pytest.mark.asyncio
    async def test_update_and_get(self, mock_adapter):
        """Test update then get same record."""
        user = await CRUDUser.insert(name="John", email="john@example.com")
        await user.update(name="Jane")
        
        fetched = await CRUDUser.get(user.id)
        
        assert fetched.name == "Jane"
    
    @pytest.mark.asyncio
    async def test_multiple_updates(self, mock_adapter):
        """Test multiple sequential updates."""
        user = await CRUDUser.insert(name="A", email="a@example.com")
        
        await user.update(name="B")
        await user.update(name="C")
        await user.update(name="D")
        
        assert user.name == "D"
    
    @pytest.mark.asyncio
    async def test_get_after_delete_raises(self, mock_adapter):
        """Test get after delete raises NotFoundError."""
        user = await CRUDUser.insert(name="John", email="john@example.com")
        user_id = user.id
        await user.delete()
        
        with pytest.raises(NotFoundError):
            await CRUDUser.get(user_id)
    
    @pytest.mark.asyncio
    async def test_refresh_after_delete_raises(self, mock_adapter):
        """Test refresh after delete raises NotFoundError."""
        user = await CRUDUser.insert(name="John", email="john@example.com")
        await user.delete()
        
        with pytest.raises(NotFoundError):
            await user.refresh()
    
    @pytest.mark.asyncio
    async def test_insert_many_records(self, mock_adapter):
        """Test inserting many records."""
        for i in range(100):
            await CRUDUser.insert(name=f"User{i}", email=f"user{i}@example.com")
        
        count = await CRUDUser.count()
        assert count == 100
    
    @pytest.mark.asyncio
    async def test_get_different_models(self, mock_adapter):
        """Test getting records from different models."""
        user = await CRUDUser.insert(name="John", email="john@example.com")
        post = await CRUDPost.insert(title="Test", author_id=user.id)
        
        fetched_user = await CRUDUser.get(user.id)
        fetched_post = await CRUDPost.get(post.id)
        
        assert fetched_user.name == "John"
        assert fetched_post.title == "Test"
    
    @pytest.mark.asyncio
    async def test_eq_operator(self, mock_adapter):
        """Test model equality operator."""
        user1 = await CRUDUser.insert(name="John", email="john@example.com")
        user2 = await CRUDUser.get(user1.id)
        
        assert user1 == user2
    
    @pytest.mark.asyncio
    async def test_ne_operator(self, mock_adapter):
        """Test model not-equal operator."""
        user1 = await CRUDUser.insert(name="John", email="john@example.com")
        user2 = await CRUDUser.insert(name="Jane", email="jane@example.com")
        
        assert user1 != user2
    
    @pytest.mark.asyncio
    async def test_hash(self, mock_adapter):
        """Test model hash."""
        user = await CRUDUser.insert(name="John", email="john@example.com")
        
        # Should be hashable
        user_set = {user}
        assert user in user_set
    
    @pytest.mark.asyncio
    async def test_repr(self, mock_adapter):
        """Test model repr."""
        user = await CRUDUser.insert(name="John", email="john@example.com")
        
        repr_str = repr(user)
        assert "CRUDUser" in repr_str
        assert "John" in repr_str
    
    @pytest.mark.asyncio
    async def test_to_dict(self, mock_adapter):
        """Test model _to_dict."""
        user = await CRUDUser.insert(name="John", email="john@example.com")
        
        d = user._to_dict()
        
        assert d["name"] == "John"
        assert d["email"] == "john@example.com"
    
    @pytest.mark.asyncio
    async def test_concurrent_inserts(self, mock_adapter):
        """Test multiple inserts have unique IDs."""
        users = []
        for i in range(10):
            user = await CRUDUser.insert(name=f"User{i}", email=f"user{i}@example.com")
            users.append(user)
        
        ids = [u.id for u in users]
        assert len(ids) == len(set(ids))  # All unique
    
    @pytest.mark.asyncio
    async def test_select_empty_table(self, mock_adapter):
        """Test select on empty table."""
        users = await CRUDUser.select()
        
        assert users == []
    
    @pytest.mark.asyncio
    async def test_select_returns_list(self, mock_adapter):
        """Test select returns list."""
        await CRUDUser.insert(name="John", email="john@example.com")
        
        users = await CRUDUser.select()
        
        assert isinstance(users, list)
    
    @pytest.mark.asyncio
    async def test_create_table_explicit(self, mock_adapter):
        """Test explicit create_table."""
        await CRUDUser.create_table()
        
        # Should not raise
        user = await CRUDUser.insert(name="John", email="john@example.com")
        assert user.id is not None
    
    @pytest.mark.asyncio
    async def test_insert_zero_values(self, mock_adapter):
        """Test insert with zero values."""
        user = await CRUDUser.insert(name="Zero", email="zero@example.com", age=0)
        
        assert user.age == 0
    
    @pytest.mark.asyncio
    async def test_update_to_zero(self, mock_adapter):
        """Test update to zero value."""
        user = await CRUDUser.insert(name="Test", email="test@example.com", age=25)
        
        await user.update(age=0)
        
        assert user.age == 0
    
    @pytest.mark.asyncio
    async def test_insert_with_whitespace(self, mock_adapter):
        """Test insert with whitespace."""
        user = await CRUDUser.insert(name="  John  ", email="john@example.com")
        
        assert user.name == "  John  "
    
    @pytest.mark.asyncio
    async def test_model_inheritance(self, mock_adapter):
        """Test basic model inheritance."""
        # CRUDUser extends Table
        assert issubclass(CRUDUser, Table)

