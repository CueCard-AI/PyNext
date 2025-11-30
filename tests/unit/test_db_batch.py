"""
Tests for PyNext Database Batch Operations.

Comprehensive tests for insert_many, update_many, delete_many, upsert.
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

class BatchUser(Table):
    """Test user model for batch operations."""
    name: str
    email: str
    age: int = 0
    role: str = "user"
    active: bool = True


class BatchProduct(Table):
    """Test product model for batch operations."""
    name: str
    price: float = 0.0
    stock: int = 0
    category: str = "general"


class BatchOrder(Table):
    """Test order model for batch operations."""
    user_id: int
    product_id: int
    quantity: int = 1
    status: str = "pending"


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
# Insert Many Tests (20 tests)
# =============================================================================

class TestInsertMany:
    """Tests for Table.insert_many()."""
    
    @pytest.mark.asyncio
    async def test_insert_many_basic(self, mock_adapter):
        """Test basic insert_many."""
        users = await BatchUser.insert_many([
            {"name": "Alice", "email": "alice@example.com"},
            {"name": "Bob", "email": "bob@example.com"},
        ])
        
        assert len(users) == 2
        assert users[0].name == "Alice"
        assert users[1].name == "Bob"
    
    @pytest.mark.asyncio
    async def test_insert_many_returns_instances(self, mock_adapter):
        """Test insert_many returns model instances."""
        users = await BatchUser.insert_many([
            {"name": "Alice", "email": "alice@example.com"},
        ])
        
        assert isinstance(users[0], BatchUser)
    
    @pytest.mark.asyncio
    async def test_insert_many_assigns_ids(self, mock_adapter):
        """Test insert_many assigns unique IDs."""
        users = await BatchUser.insert_many([
            {"name": "A", "email": "a@example.com"},
            {"name": "B", "email": "b@example.com"},
            {"name": "C", "email": "c@example.com"},
        ])
        
        ids = [u.id for u in users]
        assert len(ids) == len(set(ids))  # All unique
    
    @pytest.mark.asyncio
    async def test_insert_many_increments_ids(self, mock_adapter):
        """Test insert_many increments IDs sequentially."""
        users = await BatchUser.insert_many([
            {"name": "A", "email": "a@example.com"},
            {"name": "B", "email": "b@example.com"},
            {"name": "C", "email": "c@example.com"},
        ])
        
        assert users[1].id == users[0].id + 1
        assert users[2].id == users[1].id + 1
    
    @pytest.mark.asyncio
    async def test_insert_many_sets_timestamps(self, mock_adapter):
        """Test insert_many sets timestamps."""
        users = await BatchUser.insert_many([
            {"name": "Alice", "email": "alice@example.com"},
        ])
        
        assert users[0].created_at is not None
        assert users[0].updated_at is not None
    
    @pytest.mark.asyncio
    async def test_insert_many_uses_defaults(self, mock_adapter):
        """Test insert_many uses default values."""
        users = await BatchUser.insert_many([
            {"name": "Alice", "email": "alice@example.com"},
        ])
        
        assert users[0].age == 0
        assert users[0].role == "user"
        assert users[0].active is True
    
    @pytest.mark.asyncio
    async def test_insert_many_with_custom_values(self, mock_adapter):
        """Test insert_many with custom values."""
        users = await BatchUser.insert_many([
            {"name": "Admin", "email": "admin@example.com", "role": "admin", "age": 35},
        ])
        
        assert users[0].role == "admin"
        assert users[0].age == 35
    
    @pytest.mark.asyncio
    async def test_insert_many_empty_list(self, mock_adapter):
        """Test insert_many with empty list."""
        users = await BatchUser.insert_many([])
        
        assert users == []
    
    @pytest.mark.asyncio
    async def test_insert_many_single_record(self, mock_adapter):
        """Test insert_many with single record."""
        users = await BatchUser.insert_many([
            {"name": "Solo", "email": "solo@example.com"},
        ])
        
        assert len(users) == 1
    
    @pytest.mark.asyncio
    async def test_insert_many_large_batch(self, mock_adapter):
        """Test insert_many with large batch."""
        records = [
            {"name": f"User{i}", "email": f"user{i}@example.com"}
            for i in range(100)
        ]
        
        users = await BatchUser.insert_many(records)
        
        assert len(users) == 100
    
    @pytest.mark.asyncio
    async def test_insert_many_persists(self, mock_adapter):
        """Test insert_many persists to database."""
        await BatchUser.insert_many([
            {"name": "A", "email": "a@example.com"},
            {"name": "B", "email": "b@example.com"},
        ])
        
        count = await BatchUser.count()
        assert count == 2
    
    @pytest.mark.asyncio
    async def test_insert_many_with_unicode(self, mock_adapter):
        """Test insert_many with unicode."""
        users = await BatchUser.insert_many([
            {"name": "日本語", "email": "ja@example.com"},
            {"name": "한국어", "email": "ko@example.com"},
        ])
        
        assert users[0].name == "日本語"
        assert users[1].name == "한국어"
    
    @pytest.mark.asyncio
    async def test_insert_many_mixed_values(self, mock_adapter):
        """Test insert_many with mixed default/custom values."""
        users = await BatchUser.insert_many([
            {"name": "Default", "email": "default@example.com"},
            {"name": "Custom", "email": "custom@example.com", "age": 25, "role": "admin"},
        ])
        
        assert users[0].age == 0
        assert users[1].age == 25
    
    @pytest.mark.asyncio
    async def test_insert_many_products(self, mock_adapter):
        """Test insert_many with different model."""
        products = await BatchProduct.insert_many([
            {"name": "Widget", "price": 9.99, "stock": 100},
            {"name": "Gadget", "price": 19.99, "stock": 50},
        ])
        
        assert len(products) == 2
        assert products[0].price == 9.99
    
    @pytest.mark.asyncio
    async def test_insert_many_sequential_calls(self, mock_adapter):
        """Test multiple insert_many calls."""
        users1 = await BatchUser.insert_many([
            {"name": "A", "email": "a@example.com"},
        ])
        
        users2 = await BatchUser.insert_many([
            {"name": "B", "email": "b@example.com"},
        ])
        
        assert users2[0].id > users1[0].id
    
    @pytest.mark.asyncio
    async def test_insert_many_different_models(self, mock_adapter):
        """Test insert_many with different models."""
        users = await BatchUser.insert_many([
            {"name": "John", "email": "john@example.com"},
        ])
        
        products = await BatchProduct.insert_many([
            {"name": "Widget", "price": 9.99},
        ])
        
        orders = await BatchOrder.insert_many([
            {"user_id": users[0].id, "product_id": products[0].id, "quantity": 2},
        ])
        
        assert orders[0].user_id == users[0].id
    
    @pytest.mark.asyncio
    async def test_insert_many_boolean_values(self, mock_adapter):
        """Test insert_many with boolean values."""
        users = await BatchUser.insert_many([
            {"name": "Active", "email": "active@example.com", "active": True},
            {"name": "Inactive", "email": "inactive@example.com", "active": False},
        ])
        
        assert users[0].active is True
        assert users[1].active is False
    
    @pytest.mark.asyncio
    async def test_insert_many_zero_values(self, mock_adapter):
        """Test insert_many with zero values."""
        products = await BatchProduct.insert_many([
            {"name": "Free", "price": 0.0, "stock": 0},
        ])
        
        assert products[0].price == 0.0
        assert products[0].stock == 0
    
    @pytest.mark.asyncio
    async def test_insert_many_preserves_order(self, mock_adapter):
        """Test insert_many preserves order."""
        users = await BatchUser.insert_many([
            {"name": "First", "email": "first@example.com"},
            {"name": "Second", "email": "second@example.com"},
            {"name": "Third", "email": "third@example.com"},
        ])
        
        assert users[0].name == "First"
        assert users[1].name == "Second"
        assert users[2].name == "Third"
    
    @pytest.mark.asyncio
    async def test_insert_many_with_floats(self, mock_adapter):
        """Test insert_many with float values."""
        products = await BatchProduct.insert_many([
            {"name": "A", "price": 0.01},
            {"name": "B", "price": 99.99},
            {"name": "C", "price": 1000.50},
        ])
        
        assert products[0].price == 0.01
        assert products[2].price == 1000.50


# =============================================================================
# Update Many Tests (15 tests)
# =============================================================================

class TestUpdateMany:
    """Tests for Table.update_many()."""
    
    @pytest.mark.asyncio
    async def test_update_many_basic(self, mock_adapter):
        """Test basic update_many."""
        await BatchUser.insert_many([
            {"name": "A", "email": "a@example.com", "role": "user"},
            {"name": "B", "email": "b@example.com", "role": "user"},
            {"name": "C", "email": "c@example.com", "role": "admin"},
        ])
        
        count = await BatchUser.update_many(
            where={"role": "user"},
            set={"active": False},
        )
        
        assert count == 2
    
    @pytest.mark.asyncio
    async def test_update_many_returns_count(self, mock_adapter):
        """Test update_many returns affected count."""
        await BatchUser.insert_many([
            {"name": f"User{i}", "email": f"user{i}@example.com", "role": "user"}
            for i in range(5)
        ])
        
        count = await BatchUser.update_many(
            where={"role": "user"},
            set={"role": "member"},
        )
        
        assert count == 5
    
    @pytest.mark.asyncio
    async def test_update_many_persists(self, mock_adapter):
        """Test update_many persists changes."""
        await BatchUser.insert_many([
            {"name": "A", "email": "a@example.com", "active": True},
            {"name": "B", "email": "b@example.com", "active": True},
        ])
        
        await BatchUser.update_many(
            where={"active": True},
            set={"active": False},
        )
        
        users = await BatchUser.select().where(active=False)
        assert len(users) == 2
    
    @pytest.mark.asyncio
    async def test_update_many_no_match(self, mock_adapter):
        """Test update_many with no matching records."""
        await BatchUser.insert(name="A", email="a@example.com", role="user")
        
        count = await BatchUser.update_many(
            where={"role": "admin"},
            set={"active": False},
        )
        
        assert count == 0
    
    @pytest.mark.asyncio
    async def test_update_many_multiple_fields(self, mock_adapter):
        """Test update_many with multiple set fields."""
        await BatchUser.insert_many([
            {"name": "A", "email": "a@example.com", "role": "user"},
        ])
        
        await BatchUser.update_many(
            where={"role": "user"},
            set={"role": "member", "active": False, "age": 25},
        )
        
        user = await BatchUser.first()
        assert user.role == "member"
        assert user.active is False
        assert user.age == 25
    
    @pytest.mark.asyncio
    async def test_update_many_selective(self, mock_adapter):
        """Test update_many only affects matching records."""
        await BatchUser.insert_many([
            {"name": "Admin", "email": "admin@example.com", "role": "admin"},
            {"name": "User1", "email": "user1@example.com", "role": "user"},
            {"name": "User2", "email": "user2@example.com", "role": "user"},
        ])
        
        await BatchUser.update_many(
            where={"role": "user"},
            set={"active": False},
        )
        
        admin = await BatchUser.get_by(role="admin")
        assert admin.active is True
    
    @pytest.mark.asyncio
    async def test_update_many_all_records(self, mock_adapter):
        """Test update_many affects all matching records."""
        await BatchUser.insert_many([
            {"name": f"User{i}", "email": f"user{i}@example.com", "role": "user"}
            for i in range(10)
        ])
        
        count = await BatchUser.update_many(
            where={"role": "user"},
            set={"role": "member"},
        )
        
        assert count == 10
    
    @pytest.mark.asyncio
    async def test_update_many_boolean_to_true(self, mock_adapter):
        """Test update_many sets boolean to True."""
        await BatchUser.insert_many([
            {"name": "A", "email": "a@example.com", "active": False},
            {"name": "B", "email": "b@example.com", "active": False},
        ])
        
        await BatchUser.update_many(
            where={"active": False},
            set={"active": True},
        )
        
        users = await BatchUser.select().where(active=True)
        assert len(users) == 2
    
    @pytest.mark.asyncio
    async def test_update_many_integer(self, mock_adapter):
        """Test update_many with integer field."""
        await BatchProduct.insert_many([
            {"name": "A", "stock": 100},
            {"name": "B", "stock": 100},
        ])
        
        await BatchProduct.update_many(
            where={"stock": 100},
            set={"stock": 0},
        )
        
        products = await BatchProduct.select().where(stock=0)
        assert len(products) == 2
    
    @pytest.mark.asyncio
    async def test_update_many_float(self, mock_adapter):
        """Test update_many with float field."""
        await BatchProduct.insert_many([
            {"name": "A", "price": 10.0},
            {"name": "B", "price": 10.0},
        ])
        
        await BatchProduct.update_many(
            where={"price": 10.0},
            set={"price": 15.0},
        )
        
        products = await BatchProduct.select().where(price=15.0)
        assert len(products) == 2
    
    @pytest.mark.asyncio
    async def test_update_many_empty_table(self, mock_adapter):
        """Test update_many on empty table."""
        count = await BatchUser.update_many(
            where={"role": "user"},
            set={"active": False},
        )
        
        assert count == 0
    
    @pytest.mark.asyncio
    async def test_update_many_multiple_where(self, mock_adapter):
        """Test update_many with multiple where conditions."""
        await BatchUser.insert_many([
            {"name": "A", "email": "a@example.com", "role": "user", "age": 25},
            {"name": "B", "email": "b@example.com", "role": "user", "age": 30},
            {"name": "C", "email": "c@example.com", "role": "admin", "age": 25},
        ])
        
        count = await BatchUser.update_many(
            where={"role": "user", "age": 25},
            set={"active": False},
        )
        
        assert count == 1
    
    @pytest.mark.asyncio
    async def test_update_many_with_unicode(self, mock_adapter):
        """Test update_many with unicode."""
        await BatchUser.insert_many([
            {"name": "Test", "email": "test@example.com", "role": "user"},
        ])
        
        await BatchUser.update_many(
            where={"role": "user"},
            set={"name": "日本語"},
        )
        
        user = await BatchUser.first()
        assert user.name == "日本語"
    
    @pytest.mark.asyncio
    async def test_update_many_status_field(self, mock_adapter):
        """Test update_many with status field."""
        await BatchOrder.insert_many([
            {"user_id": 1, "product_id": 1, "status": "pending"},
            {"user_id": 2, "product_id": 1, "status": "pending"},
            {"user_id": 1, "product_id": 2, "status": "shipped"},
        ])
        
        count = await BatchOrder.update_many(
            where={"status": "pending"},
            set={"status": "processing"},
        )
        
        assert count == 2
    
    @pytest.mark.asyncio
    async def test_update_many_by_id_field(self, mock_adapter):
        """Test update_many filtering by foreign key."""
        await BatchOrder.insert_many([
            {"user_id": 1, "product_id": 1, "status": "pending"},
            {"user_id": 1, "product_id": 2, "status": "pending"},
            {"user_id": 2, "product_id": 1, "status": "pending"},
        ])
        
        count = await BatchOrder.update_many(
            where={"user_id": 1},
            set={"status": "confirmed"},
        )
        
        assert count == 2


# =============================================================================
# Delete Many Tests (15 tests)
# =============================================================================

class TestDeleteMany:
    """Tests for Table.delete_many()."""
    
    @pytest.mark.asyncio
    async def test_delete_many_basic(self, mock_adapter):
        """Test basic delete_many."""
        await BatchUser.insert_many([
            {"name": "A", "email": "a@example.com", "role": "user"},
            {"name": "B", "email": "b@example.com", "role": "user"},
            {"name": "C", "email": "c@example.com", "role": "admin"},
        ])
        
        count = await BatchUser.delete_many(where={"role": "user"})
        
        assert count == 2
    
    @pytest.mark.asyncio
    async def test_delete_many_returns_count(self, mock_adapter):
        """Test delete_many returns deleted count."""
        await BatchUser.insert_many([
            {"name": f"User{i}", "email": f"user{i}@example.com", "role": "user"}
            for i in range(5)
        ])
        
        count = await BatchUser.delete_many(where={"role": "user"})
        
        assert count == 5
    
    @pytest.mark.asyncio
    async def test_delete_many_removes_records(self, mock_adapter):
        """Test delete_many removes records from database."""
        await BatchUser.insert_many([
            {"name": "A", "email": "a@example.com", "active": False},
            {"name": "B", "email": "b@example.com", "active": False},
            {"name": "C", "email": "c@example.com", "active": True},
        ])
        
        await BatchUser.delete_many(where={"active": False})
        
        remaining = await BatchUser.count()
        assert remaining == 1
    
    @pytest.mark.asyncio
    async def test_delete_many_no_match(self, mock_adapter):
        """Test delete_many with no matching records."""
        await BatchUser.insert(name="A", email="a@example.com", role="user")
        
        count = await BatchUser.delete_many(where={"role": "admin"})
        
        assert count == 0
    
    @pytest.mark.asyncio
    async def test_delete_many_preserves_others(self, mock_adapter):
        """Test delete_many preserves non-matching records."""
        await BatchUser.insert_many([
            {"name": "Admin", "email": "admin@example.com", "role": "admin"},
            {"name": "User", "email": "user@example.com", "role": "user"},
        ])
        
        await BatchUser.delete_many(where={"role": "user"})
        
        admin = await BatchUser.get_by(role="admin")
        assert admin is not None
    
    @pytest.mark.asyncio
    async def test_delete_many_all_matching(self, mock_adapter):
        """Test delete_many deletes all matching."""
        await BatchUser.insert_many([
            {"name": f"User{i}", "email": f"user{i}@example.com", "role": "user"}
            for i in range(10)
        ])
        
        count = await BatchUser.delete_many(where={"role": "user"})
        
        assert count == 10
        remaining = await BatchUser.count()
        assert remaining == 0
    
    @pytest.mark.asyncio
    async def test_delete_many_by_boolean(self, mock_adapter):
        """Test delete_many by boolean field."""
        await BatchUser.insert_many([
            {"name": "A", "email": "a@example.com", "active": True},
            {"name": "B", "email": "b@example.com", "active": False},
            {"name": "C", "email": "c@example.com", "active": False},
        ])
        
        count = await BatchUser.delete_many(where={"active": False})
        
        assert count == 2
    
    @pytest.mark.asyncio
    async def test_delete_many_by_integer(self, mock_adapter):
        """Test delete_many by integer field."""
        await BatchProduct.insert_many([
            {"name": "A", "stock": 0},
            {"name": "B", "stock": 0},
            {"name": "C", "stock": 10},
        ])
        
        count = await BatchProduct.delete_many(where={"stock": 0})
        
        assert count == 2
    
    @pytest.mark.asyncio
    async def test_delete_many_empty_table(self, mock_adapter):
        """Test delete_many on empty table."""
        count = await BatchUser.delete_many(where={"role": "user"})
        
        assert count == 0
    
    @pytest.mark.asyncio
    async def test_delete_many_multiple_where(self, mock_adapter):
        """Test delete_many with multiple where conditions."""
        await BatchUser.insert_many([
            {"name": "A", "email": "a@example.com", "role": "user", "active": False},
            {"name": "B", "email": "b@example.com", "role": "user", "active": True},
            {"name": "C", "email": "c@example.com", "role": "admin", "active": False},
        ])
        
        count = await BatchUser.delete_many(where={"role": "user", "active": False})
        
        assert count == 1
    
    @pytest.mark.asyncio
    async def test_delete_many_by_status(self, mock_adapter):
        """Test delete_many by status field."""
        await BatchOrder.insert_many([
            {"user_id": 1, "product_id": 1, "status": "cancelled"},
            {"user_id": 2, "product_id": 1, "status": "cancelled"},
            {"user_id": 1, "product_id": 2, "status": "completed"},
        ])
        
        count = await BatchOrder.delete_many(where={"status": "cancelled"})
        
        assert count == 2
    
    @pytest.mark.asyncio
    async def test_delete_many_by_fk(self, mock_adapter):
        """Test delete_many by foreign key."""
        await BatchOrder.insert_many([
            {"user_id": 1, "product_id": 1},
            {"user_id": 1, "product_id": 2},
            {"user_id": 2, "product_id": 1},
        ])
        
        count = await BatchOrder.delete_many(where={"user_id": 1})
        
        assert count == 2
    
    @pytest.mark.asyncio
    async def test_delete_many_cascade_simulation(self, mock_adapter):
        """Test delete_many for cascade-like deletion."""
        user = await BatchUser.insert(name="John", email="john@example.com")
        
        await BatchOrder.insert_many([
            {"user_id": user.id, "product_id": 1},
            {"user_id": user.id, "product_id": 2},
        ])
        
        # Delete user's orders first (simulating cascade)
        await BatchOrder.delete_many(where={"user_id": user.id})
        await user.delete()
        
        order_count = await BatchOrder.count()
        user_count = await BatchUser.count()
        
        assert order_count == 0
        assert user_count == 0
    
    @pytest.mark.asyncio
    async def test_delete_many_and_count(self, mock_adapter):
        """Test delete_many updates count correctly."""
        await BatchUser.insert_many([
            {"name": f"User{i}", "email": f"user{i}@example.com"}
            for i in range(10)
        ])
        
        initial_count = await BatchUser.count()
        await BatchUser.delete_many(where={"role": "user"})
        final_count = await BatchUser.count()
        
        assert initial_count == 10
        assert final_count == 0
    
    @pytest.mark.asyncio
    async def test_delete_many_specific_category(self, mock_adapter):
        """Test delete_many by category."""
        await BatchProduct.insert_many([
            {"name": "A", "category": "electronics"},
            {"name": "B", "category": "electronics"},
            {"name": "C", "category": "clothing"},
        ])
        
        count = await BatchProduct.delete_many(where={"category": "electronics"})
        
        assert count == 2


# =============================================================================
# Upsert Tests (10 tests)
# =============================================================================

class TestUpsert:
    """Tests for Table.upsert()."""
    
    @pytest.mark.asyncio
    async def test_upsert_insert(self, mock_adapter):
        """Test upsert inserts when not exists."""
        user = await BatchUser.upsert(
            where={"email": "new@example.com"},
            create={"name": "New User", "email": "new@example.com"},
        )
        
        assert user.id is not None
        assert user.name == "New User"
    
    @pytest.mark.asyncio
    async def test_upsert_update(self, mock_adapter):
        """Test upsert updates when exists."""
        await BatchUser.insert(name="Old Name", email="existing@example.com")
        
        user = await BatchUser.upsert(
            where={"email": "existing@example.com"},
            create={"name": "New Name", "email": "existing@example.com"},
            update={"name": "Updated Name"},
        )
        
        assert user.name == "Updated Name"
    
    @pytest.mark.asyncio
    async def test_upsert_uses_create_for_update(self, mock_adapter):
        """Test upsert uses create values for update when update not specified."""
        await BatchUser.insert(name="Old Name", email="existing@example.com")
        
        user = await BatchUser.upsert(
            where={"email": "existing@example.com"},
            create={"name": "New Name", "email": "existing@example.com"},
        )
        
        assert user.name == "New Name"
    
    @pytest.mark.asyncio
    async def test_upsert_returns_instance(self, mock_adapter):
        """Test upsert returns model instance."""
        user = await BatchUser.upsert(
            where={"email": "test@example.com"},
            create={"name": "Test", "email": "test@example.com"},
        )
        
        assert isinstance(user, BatchUser)
    
    @pytest.mark.asyncio
    async def test_upsert_preserves_id_on_update(self, mock_adapter):
        """Test upsert preserves ID when updating."""
        original = await BatchUser.insert(name="Old", email="test@example.com")
        
        updated = await BatchUser.upsert(
            where={"email": "test@example.com"},
            create={"name": "New", "email": "test@example.com"},
            update={"name": "Updated"},
        )
        
        assert updated.id == original.id
    
    @pytest.mark.asyncio
    async def test_upsert_by_multiple_fields(self, mock_adapter):
        """Test upsert with multiple where fields."""
        await BatchUser.insert(name="John", email="john@example.com", role="user")
        
        user = await BatchUser.upsert(
            where={"email": "john@example.com", "role": "user"},
            create={"name": "John", "email": "john@example.com", "role": "user"},
            update={"name": "John Updated"},
        )
        
        assert user.name == "John Updated"
    
    @pytest.mark.asyncio
    async def test_upsert_insert_only_once(self, mock_adapter):
        """Test upsert only inserts once."""
        await BatchUser.upsert(
            where={"email": "once@example.com"},
            create={"name": "Once", "email": "once@example.com"},
        )
        
        await BatchUser.upsert(
            where={"email": "once@example.com"},
            create={"name": "Twice", "email": "once@example.com"},
            update={"name": "Updated"},
        )
        
        count = await BatchUser.count()
        assert count == 1
    
    @pytest.mark.asyncio
    async def test_upsert_with_defaults(self, mock_adapter):
        """Test upsert insert uses defaults."""
        user = await BatchUser.upsert(
            where={"email": "defaults@example.com"},
            create={"name": "Defaults", "email": "defaults@example.com"},
        )
        
        assert user.age == 0
        assert user.role == "user"
        assert user.active is True
    
    @pytest.mark.asyncio
    async def test_upsert_update_partial(self, mock_adapter):
        """Test upsert update only changes specified fields."""
        await BatchUser.insert(name="Original", email="partial@example.com", age=25)
        
        user = await BatchUser.upsert(
            where={"email": "partial@example.com"},
            create={"name": "New", "email": "partial@example.com"},
            update={"name": "Changed"},
        )
        
        assert user.name == "Changed"
        assert user.age == 25  # Preserved
    
    @pytest.mark.asyncio
    async def test_upsert_different_models(self, mock_adapter):
        """Test upsert works across different models."""
        user = await BatchUser.upsert(
            where={"email": "user@example.com"},
            create={"name": "User", "email": "user@example.com"},
        )
        
        product = await BatchProduct.upsert(
            where={"name": "Widget"},
            create={"name": "Widget", "price": 9.99},
        )
        
        assert user.id is not None
        assert product.id is not None

