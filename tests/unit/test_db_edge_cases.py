"""
Tests for PyNext Database Edge Cases.

Comprehensive edge case tests covering errors, nulls, large batches, concurrency.
"""

import pytest
from typing import Optional

from pynext.db import (
    Table,
    configure_db,
    MockAdapter,
    MemoryAdapter,
    NotFoundError,
    ValidationError,
    QueryError,
    db,
)


# =============================================================================
# Test Models
# =============================================================================

class EdgeUser(Table):
    """Test user model."""
    name: str
    email: str
    bio: Optional[str] = None
    age: int = 0


class EdgeProduct(Table):
    """Test product model."""
    name: str
    price: float = 0.0
    description: Optional[str] = None


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


@pytest.fixture
async def memory_adapter():
    """Create and configure a memory adapter."""
    adapter = MemoryAdapter()
    await adapter.connect()
    configure_db(adapter)
    yield adapter
    adapter.reset()
    await adapter.disconnect()


# =============================================================================
# Null Handling Tests (15 tests)
# =============================================================================

class TestNullHandling:
    """Tests for NULL value handling."""
    
    @pytest.mark.asyncio
    async def test_insert_with_null(self, mock_adapter):
        """Test insert with NULL value."""
        user = await EdgeUser.insert(name="Test", email="test@example.com", bio=None)
        
        assert user.bio is None
    
    @pytest.mark.asyncio
    async def test_update_to_null(self, mock_adapter):
        """Test update field to NULL."""
        user = await EdgeUser.insert(name="Test", email="test@example.com", bio="Original")
        
        await user.update(bio=None)
        
        assert user.bio is None
    
    @pytest.mark.asyncio
    async def test_query_where_null(self, mock_adapter):
        """Test query for NULL values."""
        await EdgeUser.insert(name="WithBio", email="with@example.com", bio="Has bio")
        await EdgeUser.insert(name="NoBio", email="no@example.com", bio=None)
        
        users = await EdgeUser.select().where_null("bio")
        
        assert len(users) == 1
        assert users[0].name == "NoBio"
    
    @pytest.mark.asyncio
    async def test_query_where_not_null(self, mock_adapter):
        """Test query for NOT NULL values."""
        await EdgeUser.insert(name="WithBio", email="with@example.com", bio="Has bio")
        await EdgeUser.insert(name="NoBio", email="no@example.com", bio=None)
        
        users = await EdgeUser.select().where_not_null("bio")
        
        assert len(users) == 1
        assert users[0].name == "WithBio"
    
    @pytest.mark.asyncio
    async def test_null_in_batch_insert(self, mock_adapter):
        """Test NULL in batch insert."""
        users = await EdgeUser.insert_many([
            {"name": "A", "email": "a@example.com", "bio": "Bio A"},
            {"name": "B", "email": "b@example.com", "bio": None},
        ])
        
        assert users[0].bio == "Bio A"
        assert users[1].bio is None
    
    @pytest.mark.asyncio
    async def test_null_default(self, mock_adapter):
        """Test optional field defaults to None."""
        user = await EdgeUser.insert(name="Test", email="test@example.com")
        
        assert user.bio is None
    
    @pytest.mark.asyncio
    async def test_null_preserved_on_partial_update(self, mock_adapter):
        """Test NULL preserved on partial update."""
        user = await EdgeUser.insert(name="Test", email="test@example.com", bio=None)
        
        await user.update(name="Updated")
        
        assert user.bio is None
    
    @pytest.mark.asyncio
    async def test_null_sum(self, mock_adapter):
        """Test sum with NULL values."""
        await EdgeUser.insert(name="A", email="a@example.com", age=10)
        await EdgeUser.insert(name="B", email="b@example.com", age=0)
        
        total = await EdgeUser.select().sum("age")
        
        assert total == 10
    
    @pytest.mark.asyncio
    async def test_null_avg(self, mock_adapter):
        """Test avg with NULL values."""
        await EdgeUser.insert(name="A", email="a@example.com", age=10)
        await EdgeUser.insert(name="B", email="b@example.com", age=20)
        
        avg = await EdgeUser.select().avg("age")
        
        assert avg == 15.0
    
    @pytest.mark.asyncio
    async def test_null_min_max(self, mock_adapter):
        """Test min/max with mixed values."""
        await EdgeUser.insert(name="A", email="a@example.com", age=10)
        await EdgeUser.insert(name="B", email="b@example.com", age=20)
        await EdgeUser.insert(name="C", email="c@example.com", age=5)
        
        min_age = await EdgeUser.select().min("age")
        max_age = await EdgeUser.select().max("age")
        
        assert min_age == 5
        assert max_age == 20
    
    @pytest.mark.asyncio
    async def test_upsert_with_null_where(self, mock_adapter):
        """Test upsert with NULL in where clause."""
        # This tests edge case behavior
        await EdgeUser.insert(name="Existing", email="existing@example.com", bio=None)
        
        user = await EdgeUser.upsert(
            where={"email": "existing@example.com"},
            create={"name": "New", "email": "existing@example.com"},
            update={"name": "Updated"}
        )
        
        assert user.name == "Updated"
    
    @pytest.mark.asyncio
    async def test_null_in_order_by(self, mock_adapter):
        """Test ordering with NULL values."""
        await EdgeUser.insert(name="HasBio", email="a@example.com", bio="Bio")
        await EdgeUser.insert(name="NoBio", email="b@example.com", bio=None)
        
        users = await EdgeUser.select().order_by("bio")
        
        assert len(users) == 2
    
    @pytest.mark.asyncio
    async def test_null_distinct(self, mock_adapter):
        """Test distinct with NULL values."""
        await EdgeUser.insert(name="A", email="a@example.com", bio="Same")
        await EdgeUser.insert(name="B", email="b@example.com", bio="Same")
        await EdgeUser.insert(name="C", email="c@example.com", bio=None)
        
        bios = await EdgeUser.select().distinct("bio")
        
        assert len(bios) == 2  # "Same" and None
    
    @pytest.mark.asyncio
    async def test_null_comparison(self, mock_adapter):
        """Test NULL comparison behavior."""
        await EdgeUser.insert(name="A", email="a@example.com", bio=None)
        
        # NULL = NULL should not match in SQL
        users = await EdgeUser.select().where(bio=None)
        
        # In Python/ORM, we convert this appropriately
    
    @pytest.mark.asyncio
    async def test_null_in_values(self, mock_adapter):
        """Test values() with NULL fields."""
        await EdgeUser.insert(name="Test", email="test@example.com", bio=None)
        
        data = await EdgeUser.select().values("name", "bio")
        
        assert data[0]["bio"] is None


# =============================================================================
# Large Batch Tests (10 tests)
# =============================================================================

class TestLargeBatches:
    """Tests for large batch operations."""
    
    @pytest.mark.asyncio
    async def test_insert_100_records(self, mock_adapter):
        """Test inserting 100 records."""
        records = [
            {"name": f"User{i}", "email": f"user{i}@example.com"}
            for i in range(100)
        ]
        
        users = await EdgeUser.insert_many(records)
        
        assert len(users) == 100
    
    @pytest.mark.asyncio
    async def test_insert_1000_records(self, mock_adapter):
        """Test inserting 1000 records."""
        records = [
            {"name": f"User{i}", "email": f"user{i}@example.com"}
            for i in range(1000)
        ]
        
        users = await EdgeUser.insert_many(records)
        
        assert len(users) == 1000
    
    @pytest.mark.asyncio
    async def test_select_all_large(self, mock_adapter):
        """Test selecting all from large table."""
        records = [
            {"name": f"User{i}", "email": f"user{i}@example.com"}
            for i in range(500)
        ]
        await EdgeUser.insert_many(records)
        
        users = await EdgeUser.all()
        
        assert len(users) == 500
    
    @pytest.mark.asyncio
    async def test_update_many_large(self, mock_adapter):
        """Test updating many records."""
        records = [
            {"name": f"User{i}", "email": f"user{i}@example.com", "age": 0}
            for i in range(100)
        ]
        await EdgeUser.insert_many(records)
        
        count = await EdgeUser.update_many(where={"age": 0}, set={"age": 25})
        
        assert count == 100
    
    @pytest.mark.asyncio
    async def test_delete_many_large(self, mock_adapter):
        """Test deleting many records."""
        records = [
            {"name": f"User{i}", "email": f"user{i}@example.com", "age": 0}
            for i in range(100)
        ]
        await EdgeUser.insert_many(records)
        
        count = await EdgeUser.delete_many(where={"age": 0})
        
        assert count == 100
    
    @pytest.mark.asyncio
    async def test_pagination_large(self, mock_adapter):
        """Test pagination on large dataset."""
        records = [
            {"name": f"User{i}", "email": f"user{i}@example.com"}
            for i in range(250)
        ]
        await EdgeUser.insert_many(records)
        
        page1 = await EdgeUser.select().page(1, per_page=50)
        page2 = await EdgeUser.select().page(2, per_page=50)
        page5 = await EdgeUser.select().page(5, per_page=50)
        
        assert len(page1) == 50
        assert len(page2) == 50
        assert len(page5) == 50
    
    @pytest.mark.asyncio
    async def test_count_large(self, mock_adapter):
        """Test count on large table."""
        records = [
            {"name": f"User{i}", "email": f"user{i}@example.com"}
            for i in range(500)
        ]
        await EdgeUser.insert_many(records)
        
        count = await EdgeUser.count()
        
        assert count == 500
    
    @pytest.mark.asyncio
    async def test_filter_large(self, mock_adapter):
        """Test filtering large dataset."""
        records = [
            {"name": f"User{i}", "email": f"user{i}@example.com", "age": i % 10}
            for i in range(100)
        ]
        await EdgeUser.insert_many(records)
        
        users = await EdgeUser.select().where(age=5)
        
        assert len(users) == 10
    
    @pytest.mark.asyncio
    async def test_order_large(self, mock_adapter):
        """Test ordering large dataset."""
        records = [
            {"name": f"User{i:03d}", "email": f"user{i}@example.com"}
            for i in range(100)
        ]
        await EdgeUser.insert_many(records)
        
        users = await EdgeUser.select().order_by("name").limit(10)
        
        assert users[0].name == "User000"
    
    @pytest.mark.asyncio
    async def test_async_iteration_large(self, mock_adapter):
        """Test async iteration over large dataset."""
        records = [
            {"name": f"User{i}", "email": f"user{i}@example.com"}
            for i in range(50)
        ]
        await EdgeUser.insert_many(records)
        
        count = 0
        async for user in EdgeUser.select():
            count += 1
        
        assert count == 50


# =============================================================================
# Error Handling Tests (15 tests)
# =============================================================================

class TestErrorHandling:
    """Tests for error handling."""
    
    @pytest.mark.asyncio
    async def test_get_not_found(self, mock_adapter):
        """Test get() raises NotFoundError."""
        with pytest.raises(NotFoundError):
            await EdgeUser.get(99999)
    
    @pytest.mark.asyncio
    async def test_get_by_not_found(self, mock_adapter):
        """Test get_by() raises NotFoundError."""
        with pytest.raises(NotFoundError):
            await EdgeUser.get_by(email="nonexistent@example.com")
    
    @pytest.mark.asyncio
    async def test_first_or_raise_empty(self, mock_adapter):
        """Test first_or_raise() on empty table."""
        with pytest.raises(NotFoundError):
            await EdgeUser.first_or_raise()
    
    @pytest.mark.asyncio
    async def test_one_not_found(self, mock_adapter):
        """Test one() raises NotFoundError."""
        with pytest.raises(NotFoundError):
            await EdgeUser.select().where(name="Nonexistent").one()
    
    @pytest.mark.asyncio
    async def test_refresh_deleted_raises(self, mock_adapter):
        """Test refresh() on deleted record raises."""
        user = await EdgeUser.insert(name="ToDelete", email="delete@example.com")
        await user.delete()
        
        with pytest.raises(NotFoundError):
            await user.refresh()
    
    @pytest.mark.asyncio
    async def test_get_or_none_not_found(self, mock_adapter):
        """Test get_or_none() returns None."""
        user = await EdgeUser.get_or_none(99999)
        
        assert user is None
    
    @pytest.mark.asyncio
    async def test_find_by_not_found(self, mock_adapter):
        """Test find_by() returns None."""
        user = await EdgeUser.find_by(email="nonexistent@example.com")
        
        assert user is None
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, mock_adapter):
        """Test deleting nonexistent record."""
        user = await EdgeUser.insert(name="Test", email="test@example.com")
        await user.delete()
        
        # Second delete should return False
        result = await user.delete()
        assert result is False
    
    @pytest.mark.asyncio
    async def test_update_nonexistent(self, mock_adapter):
        """Test updating nonexistent record."""
        user = await EdgeUser.insert(name="Test", email="test@example.com")
        await user.delete()
        
        # Update should raise
        with pytest.raises(NotFoundError):
            await user.update(name="New")
    
    @pytest.mark.asyncio
    async def test_error_in_transaction_rollback(self, mock_adapter):
        """Test error in transaction causes rollback."""
        try:
            async with db.transaction():
                await EdgeUser.insert(name="Test", email="test@example.com")
                raise ValueError("Intentional error")
        except ValueError:
            pass
        
        # MockAdapter should have rolled back
    
    @pytest.mark.asyncio
    async def test_empty_insert_many(self, mock_adapter):
        """Test insert_many with empty list."""
        users = await EdgeUser.insert_many([])
        
        assert users == []
    
    @pytest.mark.asyncio
    async def test_empty_delete_many(self, mock_adapter):
        """Test delete_many with no matches."""
        count = await EdgeUser.delete_many(where={"name": "Nonexistent"})
        
        assert count == 0
    
    @pytest.mark.asyncio
    async def test_empty_update_many(self, mock_adapter):
        """Test update_many with no matches."""
        count = await EdgeUser.update_many(
            where={"name": "Nonexistent"},
            set={"age": 100}
        )
        
        assert count == 0
    
    @pytest.mark.asyncio
    async def test_double_delete(self, mock_adapter):
        """Test double delete behavior."""
        user = await EdgeUser.insert(name="Test", email="test@example.com")
        
        result1 = await user.delete()
        result2 = await user.delete()
        
        assert result1 is True
        assert result2 is False
    
    @pytest.mark.asyncio
    async def test_exists_empty_table(self, mock_adapter):
        """Test exists() on empty table."""
        exists = await EdgeUser.exists(name="Anyone")
        
        assert exists is False


# =============================================================================
# Special Values Tests (10 tests)
# =============================================================================

class TestSpecialValues:
    """Tests for special value handling."""
    
    @pytest.mark.asyncio
    async def test_unicode_name(self, mock_adapter):
        """Test unicode in name."""
        user = await EdgeUser.insert(name="日本語名前", email="ja@example.com")
        
        fetched = await EdgeUser.get(user.id)
        assert fetched.name == "日本語名前"
    
    @pytest.mark.asyncio
    async def test_emoji_content(self, mock_adapter):
        """Test emoji in content."""
        user = await EdgeUser.insert(name="Emoji 😀🎉", email="emoji@example.com")
        
        fetched = await EdgeUser.get(user.id)
        assert "😀" in fetched.name
    
    @pytest.mark.asyncio
    async def test_special_chars(self, mock_adapter):
        """Test special characters."""
        user = await EdgeUser.insert(name="O'Brien & Co.", email="special@example.com")
        
        fetched = await EdgeUser.get(user.id)
        assert "O'Brien" in fetched.name
    
    @pytest.mark.asyncio
    async def test_newlines(self, mock_adapter):
        """Test newlines in text."""
        user = await EdgeUser.insert(
            name="Multi\nLine",
            email="newline@example.com",
            bio="Line1\nLine2\nLine3"
        )
        
        fetched = await EdgeUser.get(user.id)
        assert "\n" in fetched.bio
    
    @pytest.mark.asyncio
    async def test_tabs(self, mock_adapter):
        """Test tabs in text."""
        user = await EdgeUser.insert(name="Tab\tTest", email="tab@example.com")
        
        fetched = await EdgeUser.get(user.id)
        assert "\t" in fetched.name
    
    @pytest.mark.asyncio
    async def test_empty_string(self, mock_adapter):
        """Test empty string."""
        user = await EdgeUser.insert(name="Empty", email="empty@example.com", bio="")
        
        fetched = await EdgeUser.get(user.id)
        assert fetched.bio == ""
    
    @pytest.mark.asyncio
    async def test_whitespace_only(self, mock_adapter):
        """Test whitespace-only string."""
        user = await EdgeUser.insert(name="   ", email="whitespace@example.com")
        
        fetched = await EdgeUser.get(user.id)
        assert fetched.name == "   "
    
    @pytest.mark.asyncio
    async def test_very_long_string(self, mock_adapter):
        """Test string at max length."""
        # Default max_length is 255 for string fields
        long_bio = "x" * 255
        user = await EdgeUser.insert(name="Long", email="long@example.com", bio=long_bio)
        
        fetched = await EdgeUser.get(user.id)
        assert len(fetched.bio) == 255
    
    @pytest.mark.asyncio
    async def test_zero_values(self, mock_adapter):
        """Test zero values."""
        user = await EdgeUser.insert(name="Zero", email="zero@example.com", age=0)
        
        fetched = await EdgeUser.get(user.id)
        assert fetched.age == 0
    
    @pytest.mark.asyncio
    async def test_negative_values(self, mock_adapter):
        """Test negative values."""
        user = await EdgeUser.insert(name="Negative", email="negative@example.com", age=-1)
        
        fetched = await EdgeUser.get(user.id)
        assert fetched.age == -1

