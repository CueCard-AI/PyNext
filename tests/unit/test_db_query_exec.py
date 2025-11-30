"""
Tests for PyNext Database Query Execution Methods.

Comprehensive tests for query execution: first, count, exists, pagination,
async iteration, aggregations, and more.
"""

import pytest
from typing import Optional

from pynext.db import (
    Table,
    configure_db,
    MockAdapter,
    NotFoundError,
)


# =============================================================================
# Test Models
# =============================================================================

class QueryUser(Table):
    """Test user model."""
    name: str
    email: str
    age: int = 0
    role: str = "user"
    active: bool = True
    score: float = 0.0


class QueryProduct(Table):
    """Test product model."""
    name: str
    price: float = 0.0
    stock: int = 0
    category: str = "general"


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
async def populated_users(mock_adapter):
    """Create test users."""
    users = await QueryUser.insert_many([
        {"name": "Alice", "email": "alice@example.com", "age": 25, "role": "admin", "score": 95.5},
        {"name": "Bob", "email": "bob@example.com", "age": 30, "role": "user", "score": 85.0},
        {"name": "Charlie", "email": "charlie@example.com", "age": 35, "role": "user", "score": 75.5},
        {"name": "Diana", "email": "diana@example.com", "age": 28, "role": "moderator", "score": 90.0},
        {"name": "Eve", "email": "eve@example.com", "age": 22, "role": "user", "score": 80.0},
    ])
    return users


# =============================================================================
# First Tests (15 tests)
# =============================================================================

class TestFirst:
    """Tests for Query.first()."""
    
    @pytest.mark.asyncio
    async def test_first_basic(self, mock_adapter, populated_users):
        """Test basic first()."""
        user = await QueryUser.select().first()
        
        assert user is not None
        assert isinstance(user, QueryUser)
    
    @pytest.mark.asyncio
    async def test_first_with_filter(self, mock_adapter, populated_users):
        """Test first() with where filter."""
        user = await QueryUser.select().where(role="admin").first()
        
        assert user is not None
        assert user.role == "admin"
    
    @pytest.mark.asyncio
    async def test_first_with_order(self, mock_adapter, populated_users):
        """Test first() with ordering."""
        user = await QueryUser.select().order_by("age").first()
        
        assert user.name == "Eve"  # Youngest
    
    @pytest.mark.asyncio
    async def test_first_descending_order(self, mock_adapter, populated_users):
        """Test first() with descending order."""
        user = await QueryUser.select().order_by("-age").first()
        
        assert user.name == "Charlie"  # Oldest
    
    @pytest.mark.asyncio
    async def test_first_empty(self, mock_adapter):
        """Test first() on empty table."""
        user = await QueryUser.select().first()
        
        assert user is None
    
    @pytest.mark.asyncio
    async def test_first_no_match(self, mock_adapter, populated_users):
        """Test first() with no matching records."""
        user = await QueryUser.select().where(role="nonexistent").first()
        
        assert user is None
    
    @pytest.mark.asyncio
    async def test_first_or_raise_exists(self, mock_adapter, populated_users):
        """Test first_or_raise() with matching record."""
        user = await QueryUser.select().where(role="admin").first_or_raise()
        
        assert user.role == "admin"
    
    @pytest.mark.asyncio
    async def test_first_or_raise_empty(self, mock_adapter):
        """Test first_or_raise() on empty table."""
        with pytest.raises(NotFoundError):
            await QueryUser.select().first_or_raise()
    
    @pytest.mark.asyncio
    async def test_first_or_raise_no_match(self, mock_adapter, populated_users):
        """Test first_or_raise() with no match."""
        with pytest.raises(NotFoundError):
            await QueryUser.select().where(role="nonexistent").first_or_raise()
    
    @pytest.mark.asyncio
    async def test_one_exists(self, mock_adapter, populated_users):
        """Test one() with matching record."""
        user = await QueryUser.select().where(name="Alice").one()
        
        assert user.name == "Alice"
    
    @pytest.mark.asyncio
    async def test_one_empty(self, mock_adapter):
        """Test one() on empty table."""
        with pytest.raises(NotFoundError):
            await QueryUser.select().one()
    
    @pytest.mark.asyncio
    async def test_last_basic(self, mock_adapter, populated_users):
        """Test last() returns last record."""
        user = await QueryUser.select().last()
        
        assert user is not None
    
    @pytest.mark.asyncio
    async def test_last_with_order(self, mock_adapter, populated_users):
        """Test last() with ordering."""
        user = await QueryUser.select().order_by("age").last()
        
        assert user.name == "Charlie"  # Oldest (last in ASC order)
    
    @pytest.mark.asyncio
    async def test_last_empty(self, mock_adapter):
        """Test last() on empty table."""
        user = await QueryUser.select().last()
        
        assert user is None
    
    @pytest.mark.asyncio
    async def test_first_chained_filters(self, mock_adapter, populated_users):
        """Test first() with chained filters."""
        user = await (
            QueryUser.select()
            .where(role="user")
            .where(active=True)
            .first()
        )
        
        assert user is not None
        assert user.role == "user"


# =============================================================================
# Count and Exists Tests (15 tests)
# =============================================================================

class TestCountExists:
    """Tests for Query.count() and Query.exists()."""
    
    @pytest.mark.asyncio
    async def test_count_all(self, mock_adapter, populated_users):
        """Test count() all records."""
        count = await QueryUser.select().count()
        
        assert count == 5
    
    @pytest.mark.asyncio
    async def test_count_with_filter(self, mock_adapter, populated_users):
        """Test count() with filter."""
        count = await QueryUser.select().where(role="user").count()
        
        assert count == 3
    
    @pytest.mark.asyncio
    async def test_count_empty(self, mock_adapter):
        """Test count() on empty table."""
        count = await QueryUser.select().count()
        
        assert count == 0
    
    @pytest.mark.asyncio
    async def test_count_no_match(self, mock_adapter, populated_users):
        """Test count() with no matching records."""
        count = await QueryUser.select().where(role="nonexistent").count()
        
        assert count == 0
    
    @pytest.mark.asyncio
    async def test_count_single_match(self, mock_adapter, populated_users):
        """Test count() with single match."""
        count = await QueryUser.select().where(role="admin").count()
        
        assert count == 1
    
    @pytest.mark.asyncio
    async def test_exists_true(self, mock_adapter, populated_users):
        """Test exists() returns True."""
        exists = await QueryUser.select().where(role="admin").exists()
        
        assert exists is True
    
    @pytest.mark.asyncio
    async def test_exists_false(self, mock_adapter, populated_users):
        """Test exists() returns False."""
        exists = await QueryUser.select().where(role="nonexistent").exists()
        
        assert exists is False
    
    @pytest.mark.asyncio
    async def test_exists_empty_table(self, mock_adapter):
        """Test exists() on empty table."""
        exists = await QueryUser.select().exists()
        
        assert exists is False
    
    @pytest.mark.asyncio
    async def test_exists_all(self, mock_adapter, populated_users):
        """Test exists() with any records."""
        exists = await QueryUser.select().exists()
        
        assert exists is True
    
    @pytest.mark.asyncio
    async def test_count_with_multiple_filters(self, mock_adapter, populated_users):
        """Test count() with multiple filters."""
        count = await (
            QueryUser.select()
            .where(role="user")
            .where(active=True)
            .count()
        )
        
        assert count == 3
    
    @pytest.mark.asyncio
    async def test_exists_with_multiple_filters(self, mock_adapter, populated_users):
        """Test exists() with multiple filters."""
        exists = await (
            QueryUser.select()
            .where(role="admin")
            .where(active=True)
            .exists()
        )
        
        assert exists is True
    
    @pytest.mark.asyncio
    async def test_count_different_model(self, mock_adapter):
        """Test count() with different model."""
        await QueryProduct.insert_many([
            {"name": "A", "price": 10.0},
            {"name": "B", "price": 20.0},
        ])
        
        count = await QueryProduct.count()
        
        assert count == 2
    
    @pytest.mark.asyncio
    async def test_class_count(self, mock_adapter, populated_users):
        """Test Table.count() class method."""
        count = await QueryUser.count()
        
        assert count == 5
    
    @pytest.mark.asyncio
    async def test_class_exists(self, mock_adapter, populated_users):
        """Test Table.exists() class method."""
        exists = await QueryUser.exists(role="admin")
        
        assert exists is True
    
    @pytest.mark.asyncio
    async def test_count_after_delete(self, mock_adapter, populated_users):
        """Test count() updates after delete."""
        initial = await QueryUser.count()
        
        user = await QueryUser.first()
        await user.delete()
        
        final = await QueryUser.count()
        
        assert final == initial - 1


# =============================================================================
# Pagination Tests (15 tests)
# =============================================================================

class TestPagination:
    """Tests for Query pagination methods."""
    
    @pytest.mark.asyncio
    async def test_limit_basic(self, mock_adapter, populated_users):
        """Test limit() basic."""
        users = await QueryUser.select().limit(2)
        
        assert len(users) == 2
    
    @pytest.mark.asyncio
    async def test_limit_all(self, mock_adapter, populated_users):
        """Test limit() larger than total."""
        users = await QueryUser.select().limit(100)
        
        assert len(users) == 5
    
    @pytest.mark.asyncio
    async def test_limit_one(self, mock_adapter, populated_users):
        """Test limit(1)."""
        users = await QueryUser.select().limit(1)
        
        assert len(users) == 1
    
    @pytest.mark.asyncio
    async def test_offset_basic(self, mock_adapter, populated_users):
        """Test offset() basic."""
        users = await QueryUser.select().offset(2)
        
        assert len(users) == 3
    
    @pytest.mark.asyncio
    async def test_offset_beyond_total(self, mock_adapter, populated_users):
        """Test offset() beyond total."""
        users = await QueryUser.select().offset(100)
        
        assert len(users) == 0
    
    @pytest.mark.asyncio
    async def test_limit_offset_combined(self, mock_adapter, populated_users):
        """Test limit() and offset() combined."""
        users = await QueryUser.select().limit(2).offset(1)
        
        assert len(users) == 2
    
    @pytest.mark.asyncio
    async def test_page_first(self, mock_adapter, populated_users):
        """Test page() first page."""
        users = await QueryUser.select().page(1, per_page=2)
        
        assert len(users) == 2
    
    @pytest.mark.asyncio
    async def test_page_second(self, mock_adapter, populated_users):
        """Test page() second page."""
        users = await QueryUser.select().page(2, per_page=2)
        
        assert len(users) == 2
    
    @pytest.mark.asyncio
    async def test_page_last_partial(self, mock_adapter, populated_users):
        """Test page() last page partial."""
        users = await QueryUser.select().page(3, per_page=2)
        
        assert len(users) == 1
    
    @pytest.mark.asyncio
    async def test_page_beyond(self, mock_adapter, populated_users):
        """Test page() beyond last page."""
        users = await QueryUser.select().page(10, per_page=2)
        
        assert len(users) == 0
    
    @pytest.mark.asyncio
    async def test_page_with_filter(self, mock_adapter, populated_users):
        """Test page() with filter."""
        users = await QueryUser.select().where(role="user").page(1, per_page=2)
        
        assert len(users) == 2
        for user in users:
            assert user.role == "user"
    
    @pytest.mark.asyncio
    async def test_page_with_order(self, mock_adapter, populated_users):
        """Test page() with ordering."""
        users = await QueryUser.select().order_by("age").page(1, per_page=2)
        
        assert len(users) == 2
        assert users[0].age <= users[1].age
    
    @pytest.mark.asyncio
    async def test_limit_with_order(self, mock_adapter, populated_users):
        """Test limit() with ordering."""
        users = await QueryUser.select().order_by("-age").limit(3)
        
        assert len(users) == 3
        assert users[0].age >= users[1].age >= users[2].age
    
    @pytest.mark.asyncio
    async def test_offset_preserves_order(self, mock_adapter, populated_users):
        """Test offset() preserves ordering."""
        all_users = await QueryUser.select().order_by("name")
        offset_users = await QueryUser.select().order_by("name").offset(2)
        
        assert offset_users[0].name == all_users[2].name
    
    @pytest.mark.asyncio
    async def test_default_per_page(self, mock_adapter):
        """Test page() default per_page."""
        # Create 30 users
        for i in range(30):
            await QueryUser.insert(name=f"User{i}", email=f"user{i}@example.com")
        
        # Default is 20
        users = await QueryUser.select().page(1)
        
        assert len(users) == 20


# =============================================================================
# Aggregation Tests (15 tests)
# =============================================================================

class TestAggregation:
    """Tests for Query aggregation methods."""
    
    @pytest.mark.asyncio
    async def test_sum_basic(self, mock_adapter, populated_users):
        """Test sum() basic."""
        total = await QueryUser.select().sum("age")
        
        assert total == 25 + 30 + 35 + 28 + 22
    
    @pytest.mark.asyncio
    async def test_sum_with_filter(self, mock_adapter, populated_users):
        """Test sum() with filter."""
        total = await QueryUser.select().where(role="user").sum("age")
        
        assert total == 30 + 35 + 22
    
    @pytest.mark.asyncio
    async def test_sum_empty(self, mock_adapter):
        """Test sum() on empty table."""
        total = await QueryUser.select().sum("age")
        
        assert total == 0
    
    @pytest.mark.asyncio
    async def test_sum_float(self, mock_adapter, populated_users):
        """Test sum() with float field."""
        total = await QueryUser.select().sum("score")
        
        assert abs(total - (95.5 + 85.0 + 75.5 + 90.0 + 80.0)) < 0.1
    
    @pytest.mark.asyncio
    async def test_avg_basic(self, mock_adapter, populated_users):
        """Test avg() basic."""
        avg = await QueryUser.select().avg("age")
        
        expected = (25 + 30 + 35 + 28 + 22) / 5
        assert abs(avg - expected) < 0.1
    
    @pytest.mark.asyncio
    async def test_avg_with_filter(self, mock_adapter, populated_users):
        """Test avg() with filter."""
        avg = await QueryUser.select().where(role="user").avg("age")
        
        expected = (30 + 35 + 22) / 3
        assert abs(avg - expected) < 0.1
    
    @pytest.mark.asyncio
    async def test_avg_empty(self, mock_adapter):
        """Test avg() on empty table."""
        avg = await QueryUser.select().avg("age")
        
        assert avg is None
    
    @pytest.mark.asyncio
    async def test_min_basic(self, mock_adapter, populated_users):
        """Test min() basic."""
        minimum = await QueryUser.select().min("age")
        
        assert minimum == 22
    
    @pytest.mark.asyncio
    async def test_min_with_filter(self, mock_adapter, populated_users):
        """Test min() with filter."""
        minimum = await QueryUser.select().where(role="user").min("age")
        
        assert minimum == 22
    
    @pytest.mark.asyncio
    async def test_min_empty(self, mock_adapter):
        """Test min() on empty table."""
        minimum = await QueryUser.select().min("age")
        
        assert minimum is None
    
    @pytest.mark.asyncio
    async def test_max_basic(self, mock_adapter, populated_users):
        """Test max() basic."""
        maximum = await QueryUser.select().max("age")
        
        assert maximum == 35
    
    @pytest.mark.asyncio
    async def test_max_with_filter(self, mock_adapter, populated_users):
        """Test max() with filter."""
        maximum = await QueryUser.select().where(role="user").max("age")
        
        assert maximum == 35
    
    @pytest.mark.asyncio
    async def test_max_empty(self, mock_adapter):
        """Test max() on empty table."""
        maximum = await QueryUser.select().max("age")
        
        assert maximum is None
    
    @pytest.mark.asyncio
    async def test_distinct_basic(self, mock_adapter, populated_users):
        """Test distinct() basic."""
        roles = await QueryUser.select().distinct("role")
        
        assert set(roles) == {"admin", "user", "moderator"}
    
    @pytest.mark.asyncio
    async def test_distinct_single_value(self, mock_adapter):
        """Test distinct() with single value."""
        for i in range(5):
            await QueryUser.insert(name=f"User{i}", email=f"user{i}@example.com", role="user")
        
        roles = await QueryUser.select().distinct("role")
        
        assert roles == ["user"]


# =============================================================================
# Values Tests (10 tests)
# =============================================================================

class TestValues:
    """Tests for Query.values() and values_list()."""
    
    @pytest.mark.asyncio
    async def test_values_single_field(self, mock_adapter, populated_users):
        """Test values() with single field."""
        data = await QueryUser.select().values("name")
        
        assert len(data) == 5
        assert all("name" in d for d in data)
    
    @pytest.mark.asyncio
    async def test_values_multiple_fields(self, mock_adapter, populated_users):
        """Test values() with multiple fields."""
        data = await QueryUser.select().values("name", "email")
        
        assert len(data) == 5
        assert all("name" in d and "email" in d for d in data)
    
    @pytest.mark.asyncio
    async def test_values_with_filter(self, mock_adapter, populated_users):
        """Test values() with filter."""
        data = await QueryUser.select().where(role="admin").values("name")
        
        assert len(data) == 1
        assert data[0]["name"] == "Alice"
    
    @pytest.mark.asyncio
    async def test_values_list_single(self, mock_adapter, populated_users):
        """Test values_list() with single field."""
        names = await QueryUser.select().values_list("name")
        
        assert len(names) == 5
        assert all(isinstance(n, tuple) for n in names)
    
    @pytest.mark.asyncio
    async def test_values_list_flat(self, mock_adapter, populated_users):
        """Test values_list() with flat=True."""
        names = await QueryUser.select().values_list("name", flat=True)
        
        assert len(names) == 5
        assert all(isinstance(n, str) for n in names)
    
    @pytest.mark.asyncio
    async def test_values_list_multiple(self, mock_adapter, populated_users):
        """Test values_list() with multiple fields."""
        data = await QueryUser.select().values_list("name", "email")
        
        assert len(data) == 5
        assert all(len(d) == 2 for d in data)
    
    @pytest.mark.asyncio
    async def test_values_empty(self, mock_adapter):
        """Test values() on empty table."""
        data = await QueryUser.select().values("name")
        
        assert data == []
    
    @pytest.mark.asyncio
    async def test_values_list_empty(self, mock_adapter):
        """Test values_list() on empty table."""
        data = await QueryUser.select().values_list("name", flat=True)
        
        assert data == []
    
    @pytest.mark.asyncio
    async def test_values_with_order(self, mock_adapter, populated_users):
        """Test values() with ordering."""
        data = await QueryUser.select().order_by("name").values("name")
        
        names = [d["name"] for d in data]
        assert names == sorted(names)
    
    @pytest.mark.asyncio
    async def test_values_list_with_limit(self, mock_adapter, populated_users):
        """Test values_list() with limit."""
        names = await QueryUser.select().limit(3).values_list("name", flat=True)
        
        assert len(names) == 3

