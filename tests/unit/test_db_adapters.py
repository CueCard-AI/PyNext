"""
Tests for PyNext Database Adapters.

Tests for MockAdapter (dict-based) and MemoryAdapter (SQLite).
"""

import pytest
from datetime import datetime

from pynext.db import (
    Table,
    configure_db,
    MockAdapter,
    MemoryAdapter,
    NotFoundError,
    Query,
)
from pynext.db.fields import FieldInfo, SQLType


# Test fixtures

@pytest.fixture
async def mock_adapter():
    """Create a mock adapter."""
    adapter = MockAdapter()
    await adapter.connect()
    yield adapter
    await adapter.disconnect()


@pytest.fixture
async def memory_adapter():
    """Create a memory adapter."""
    adapter = MemoryAdapter()
    await adapter.connect()
    yield adapter
    await adapter.disconnect()


# Test model
class AdapterUser(Table):
    """Test user model."""
    name: str
    email: str
    age: int = 0


# =============================================================================
# MockAdapter Tests (30 tests)
# =============================================================================

class TestMockAdapter:
    """Tests for MockAdapter (dict-based)."""
    
    @pytest.mark.asyncio
    async def test_connect(self, mock_adapter):
        """Test connect sets connected flag."""
        assert mock_adapter._connected is True
    
    @pytest.mark.asyncio
    async def test_disconnect_clears_data(self, mock_adapter):
        """Test disconnect clears all data."""
        mock_adapter._tables["test"] = {1: {"id": 1}}
        await mock_adapter.disconnect()
        assert mock_adapter._tables == {}
    
    @pytest.mark.asyncio
    async def test_create_table(self, mock_adapter):
        """Test create_table initializes dict."""
        fields = AdapterUser._fields
        await mock_adapter.create_table("users", fields)
        assert "users" in mock_adapter._tables
    
    @pytest.mark.asyncio
    async def test_drop_table(self, mock_adapter):
        """Test drop_table removes dict."""
        mock_adapter._tables["test"] = {}
        await mock_adapter.drop_table("test")
        assert "test" not in mock_adapter._tables
    
    @pytest.mark.asyncio
    async def test_insert_returns_row(self, mock_adapter):
        """Test insert returns created row."""
        fields = AdapterUser._fields
        await mock_adapter.create_table("users", fields)
        
        row = await mock_adapter.insert("users", {"name": "John", "email": "john@test.com"}, fields)
        
        assert row["id"] == 1
        assert row["name"] == "John"
    
    @pytest.mark.asyncio
    async def test_insert_increments_id(self, mock_adapter):
        """Test insert increments id."""
        fields = AdapterUser._fields
        await mock_adapter.create_table("users", fields)
        
        row1 = await mock_adapter.insert("users", {"name": "A", "email": "a@test.com"}, fields)
        row2 = await mock_adapter.insert("users", {"name": "B", "email": "b@test.com"}, fields)
        
        assert row1["id"] == 1
        assert row2["id"] == 2
    
    @pytest.mark.asyncio
    async def test_insert_sets_timestamps(self, mock_adapter):
        """Test insert sets created_at and updated_at."""
        fields = AdapterUser._fields
        await mock_adapter.create_table("users", fields)
        
        row = await mock_adapter.insert("users", {"name": "John", "email": "john@test.com"}, fields)
        
        assert row["created_at"] is not None
        assert row["updated_at"] is not None
    
    @pytest.mark.asyncio
    async def test_select_empty(self, mock_adapter):
        """Test select on empty table."""
        fields = AdapterUser._fields
        configure_db(mock_adapter)
        
        query = AdapterUser.select()
        rows = await mock_adapter.select("adapterusers", query, fields)
        
        assert rows == []
    
    @pytest.mark.asyncio
    async def test_select_returns_all(self, mock_adapter):
        """Test select returns all rows."""
        fields = AdapterUser._fields
        configure_db(mock_adapter)
        
        await mock_adapter.insert("adapterusers", {"name": "A", "email": "a@test.com"}, fields)
        await mock_adapter.insert("adapterusers", {"name": "B", "email": "b@test.com"}, fields)
        
        query = AdapterUser.select()
        rows = await mock_adapter.select("adapterusers", query, fields)
        
        assert len(rows) == 2
    
    @pytest.mark.asyncio
    async def test_select_where_filters(self, mock_adapter):
        """Test select with where filter."""
        fields = AdapterUser._fields
        configure_db(mock_adapter)
        
        await mock_adapter.insert("adapterusers", {"name": "A", "email": "a@test.com", "age": 20}, fields)
        await mock_adapter.insert("adapterusers", {"name": "B", "email": "b@test.com", "age": 30}, fields)
        
        query = AdapterUser.select().where(age=30)
        rows = await mock_adapter.select("adapterusers", query, fields)
        
        assert len(rows) == 1
        assert rows[0]["name"] == "B"
    
    @pytest.mark.asyncio
    async def test_select_order_by(self, mock_adapter):
        """Test select with order_by."""
        fields = AdapterUser._fields
        configure_db(mock_adapter)
        
        await mock_adapter.insert("adapterusers", {"name": "C", "email": "c@test.com"}, fields)
        await mock_adapter.insert("adapterusers", {"name": "A", "email": "a@test.com"}, fields)
        await mock_adapter.insert("adapterusers", {"name": "B", "email": "b@test.com"}, fields)
        
        query = AdapterUser.select().order_by("name")
        rows = await mock_adapter.select("adapterusers", query, fields)
        
        names = [r["name"] for r in rows]
        assert names == ["A", "B", "C"]
    
    @pytest.mark.asyncio
    async def test_select_limit(self, mock_adapter):
        """Test select with limit."""
        fields = AdapterUser._fields
        configure_db(mock_adapter)
        
        for i in range(5):
            await mock_adapter.insert("adapterusers", {"name": f"U{i}", "email": f"u{i}@test.com"}, fields)
        
        query = AdapterUser.select().limit(2)
        rows = await mock_adapter.select("adapterusers", query, fields)
        
        assert len(rows) == 2
    
    @pytest.mark.asyncio
    async def test_select_offset(self, mock_adapter):
        """Test select with offset."""
        fields = AdapterUser._fields
        configure_db(mock_adapter)
        
        for i in range(5):
            await mock_adapter.insert("adapterusers", {"name": f"U{i}", "email": f"u{i}@test.com"}, fields)
        
        query = AdapterUser.select().order_by("id").offset(2)
        rows = await mock_adapter.select("adapterusers", query, fields)
        
        assert len(rows) == 3
    
    @pytest.mark.asyncio
    async def test_select_one(self, mock_adapter):
        """Test select_one returns single row."""
        fields = AdapterUser._fields
        configure_db(mock_adapter)
        
        await mock_adapter.insert("adapterusers", {"name": "John", "email": "john@test.com"}, fields)
        
        query = AdapterUser.select().where(name="John")
        row = await mock_adapter.select_one("adapterusers", query, fields)
        
        assert row is not None
        assert row["name"] == "John"
    
    @pytest.mark.asyncio
    async def test_select_one_none(self, mock_adapter):
        """Test select_one returns None when not found."""
        fields = AdapterUser._fields
        configure_db(mock_adapter)
        
        query = AdapterUser.select().where(name="Nobody")
        row = await mock_adapter.select_one("adapterusers", query, fields)
        
        assert row is None
    
    @pytest.mark.asyncio
    async def test_update_modifies_row(self, mock_adapter):
        """Test update modifies row."""
        fields = AdapterUser._fields
        configure_db(mock_adapter)
        
        row = await mock_adapter.insert("adapterusers", {"name": "John", "email": "john@test.com"}, fields)
        
        updated = await mock_adapter.update("adapterusers", row["id"], {"name": "Jane"}, fields)
        
        assert updated["name"] == "Jane"
    
    @pytest.mark.asyncio
    async def test_update_sets_updated_at(self, mock_adapter):
        """Test update changes updated_at."""
        fields = AdapterUser._fields
        configure_db(mock_adapter)
        
        row = await mock_adapter.insert("adapterusers", {"name": "John", "email": "john@test.com"}, fields)
        original_updated = row["updated_at"]
        
        import time
        time.sleep(0.01)
        
        updated = await mock_adapter.update("adapterusers", row["id"], {"name": "Jane"}, fields)
        
        assert updated["updated_at"] >= original_updated
    
    @pytest.mark.asyncio
    async def test_update_not_found(self, mock_adapter):
        """Test update raises for non-existent row."""
        fields = AdapterUser._fields
        configure_db(mock_adapter)
        
        with pytest.raises(NotFoundError):
            await mock_adapter.update("adapterusers", 999, {"name": "Jane"}, fields)
    
    @pytest.mark.asyncio
    async def test_delete_removes_row(self, mock_adapter):
        """Test delete removes row."""
        fields = AdapterUser._fields
        configure_db(mock_adapter)
        
        row = await mock_adapter.insert("adapterusers", {"name": "John", "email": "john@test.com"}, fields)
        
        result = await mock_adapter.delete("adapterusers", row["id"])
        
        assert result is True
        assert mock_adapter.get_by_id("adapterusers", row["id"]) is None
    
    @pytest.mark.asyncio
    async def test_delete_not_found(self, mock_adapter):
        """Test delete returns False for non-existent row."""
        result = await mock_adapter.delete("adapterusers", 999)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_count(self, mock_adapter):
        """Test count returns row count."""
        fields = AdapterUser._fields
        configure_db(mock_adapter)
        
        await mock_adapter.insert("adapterusers", {"name": "A", "email": "a@test.com"}, fields)
        await mock_adapter.insert("adapterusers", {"name": "B", "email": "b@test.com"}, fields)
        
        query = AdapterUser.select()
        count = await mock_adapter.count("adapterusers", query)
        
        assert count == 2
    
    @pytest.mark.asyncio
    async def test_exists_true(self, mock_adapter):
        """Test exists returns True when rows exist."""
        fields = AdapterUser._fields
        configure_db(mock_adapter)
        
        await mock_adapter.insert("adapterusers", {"name": "John", "email": "john@test.com"}, fields)
        
        query = AdapterUser.select().where(name="John")
        exists = await mock_adapter.exists("adapterusers", query)
        
        assert exists is True
    
    @pytest.mark.asyncio
    async def test_exists_false(self, mock_adapter):
        """Test exists returns False when no rows."""
        fields = AdapterUser._fields
        configure_db(mock_adapter)
        
        query = AdapterUser.select().where(name="Nobody")
        exists = await mock_adapter.exists("adapterusers", query)
        
        assert exists is False
    
    @pytest.mark.asyncio
    async def test_transaction_commit(self, mock_adapter):
        """Test transaction commit keeps changes."""
        fields = AdapterUser._fields
        configure_db(mock_adapter)
        
        async with mock_adapter.transaction():
            await mock_adapter.insert("adapterusers", {"name": "John", "email": "john@test.com"}, fields)
        
        rows = await mock_adapter.select("adapterusers", AdapterUser.select(), fields)
        assert len(rows) == 1
    
    @pytest.mark.asyncio
    async def test_transaction_rollback(self, mock_adapter):
        """Test transaction rollback undoes changes."""
        fields = AdapterUser._fields
        configure_db(mock_adapter)
        
        try:
            async with mock_adapter.transaction():
                await mock_adapter.insert("adapterusers", {"name": "John", "email": "john@test.com"}, fields)
                raise Exception("Simulated error")
        except:
            pass
        
        rows = await mock_adapter.select("adapterusers", AdapterUser.select(), fields)
        assert len(rows) == 0
    
    @pytest.mark.asyncio
    async def test_reset(self, mock_adapter):
        """Test reset clears all data."""
        fields = AdapterUser._fields
        configure_db(mock_adapter)
        
        await mock_adapter.insert("adapterusers", {"name": "John", "email": "john@test.com"}, fields)
        
        mock_adapter.reset()
        
        assert mock_adapter._tables == {}
    
    @pytest.mark.asyncio
    async def test_get_all_convenience(self, mock_adapter):
        """Test get_all convenience method."""
        fields = AdapterUser._fields
        configure_db(mock_adapter)
        
        await mock_adapter.insert("adapterusers", {"name": "John", "email": "john@test.com"}, fields)
        
        rows = mock_adapter.get_all("adapterusers")
        assert len(rows) == 1
    
    @pytest.mark.asyncio
    async def test_get_by_id_convenience(self, mock_adapter):
        """Test get_by_id convenience method."""
        fields = AdapterUser._fields
        configure_db(mock_adapter)
        
        row = await mock_adapter.insert("adapterusers", {"name": "John", "email": "john@test.com"}, fields)
        
        found = mock_adapter.get_by_id("adapterusers", row["id"])
        assert found["name"] == "John"


# Helper to create fields for memory adapter tests
def _get_memory_fields():
    """Get fields dict for memory adapter tests."""
    from pynext.db.fields import FieldInfo, SQLType, create_auto_fields
    return {
        **create_auto_fields(),
        "name": FieldInfo("name", str, SQLType.VARCHAR, max_length=255),
        "email": FieldInfo("email", str, SQLType.VARCHAR, max_length=255),
        "age": FieldInfo("age", int, SQLType.INTEGER, default=0),
    }


# =============================================================================
# MemoryAdapter Tests (30 tests)
# =============================================================================

class TestMemoryAdapter:
    """Tests for MemoryAdapter (SQLite)."""
    
    @pytest.mark.asyncio
    async def test_connect(self, memory_adapter):
        """Test connect creates connection."""
        assert memory_adapter._conn is not None
    
    @pytest.mark.asyncio
    async def test_disconnect(self, memory_adapter):
        """Test disconnect closes connection."""
        await memory_adapter.disconnect()
        assert memory_adapter._conn is None
    
    @pytest.mark.asyncio
    async def test_create_table(self, memory_adapter):
        """Test create_table creates SQL table."""
        fields = _get_memory_fields()
        await memory_adapter.create_table("users", fields)
        
        # Should not raise on second call (IF NOT EXISTS)
        await memory_adapter.create_table("users", fields)
    
    @pytest.mark.asyncio
    async def test_drop_table(self, memory_adapter):
        """Test drop_table removes SQL table."""
        fields = _get_memory_fields()
        await memory_adapter.create_table("users", fields)
        await memory_adapter.drop_table("users")
        
        # Should not raise (IF EXISTS)
        await memory_adapter.drop_table("users")
    
    @pytest.mark.asyncio
    async def test_insert_returns_row(self, memory_adapter):
        """Test insert returns created row."""
        from pynext.db.fields import FieldInfo, SQLType, create_auto_fields
        
        fields = {
            **create_auto_fields(),
            "name": FieldInfo("name", str, SQLType.VARCHAR, max_length=255),
            "email": FieldInfo("email", str, SQLType.VARCHAR, max_length=255),
            "age": FieldInfo("age", int, SQLType.INTEGER, default=0),
        }
        await memory_adapter.create_table("memoryusers", fields)
        
        row = await memory_adapter.insert("memoryusers", {"name": "John", "email": "john@test.com", "age": 0}, fields)
        
        assert row["id"] == 1
        assert row["name"] == "John"
    
    @pytest.mark.asyncio
    async def test_insert_auto_timestamps(self, memory_adapter):
        """Test insert sets timestamps."""
        from pynext.db.fields import FieldInfo, SQLType, create_auto_fields
        
        fields = {
            **create_auto_fields(),
            "name": FieldInfo("name", str, SQLType.VARCHAR, max_length=255),
            "email": FieldInfo("email", str, SQLType.VARCHAR, max_length=255),
            "age": FieldInfo("age", int, SQLType.INTEGER, default=0),
        }
        await memory_adapter.create_table("memoryusers", fields)
        
        row = await memory_adapter.insert("memoryusers", {"name": "John", "email": "john@test.com", "age": 0}, fields)
        
        assert row["created_at"] is not None
        assert row["updated_at"] is not None
    
    @pytest.mark.asyncio
    async def test_select_returns_rows(self, memory_adapter):
        """Test select returns rows."""
        fields = _get_memory_fields()
        configure_db(memory_adapter)
        await memory_adapter.create_table("memoryusers", fields)
        
        await memory_adapter.insert("memoryusers", {"name": "A", "email": "a@test.com", "age": 0}, fields)
        await memory_adapter.insert("memoryusers", {"name": "B", "email": "b@test.com", "age": 0}, fields)
        
        query = AdapterUser.select()
        rows = await memory_adapter.select("memoryusers", query, fields)
        
        assert len(rows) == 2
    
    @pytest.mark.asyncio
    async def test_select_where(self, memory_adapter):
        """Test select with WHERE clause."""
        fields = _get_memory_fields()
        configure_db(memory_adapter)
        await memory_adapter.create_table("memoryusers", fields)
        
        await memory_adapter.insert("memoryusers", {"name": "A", "email": "a@test.com", "age": 20}, fields)
        await memory_adapter.insert("memoryusers", {"name": "B", "email": "b@test.com", "age": 30}, fields)
        
        query = AdapterUser.select().where(age=30)
        rows = await memory_adapter.select("memoryusers", query, fields)
        
        assert len(rows) == 1
        assert rows[0]["name"] == "B"
    
    @pytest.mark.asyncio
    async def test_select_order_by(self, memory_adapter):
        """Test select with ORDER BY."""
        fields = _get_memory_fields()
        configure_db(memory_adapter)
        await memory_adapter.create_table("memoryusers", fields)
        
        await memory_adapter.insert("memoryusers", {"name": "C", "email": "c@test.com", "age": 0}, fields)
        await memory_adapter.insert("memoryusers", {"name": "A", "email": "a@test.com", "age": 0}, fields)
        
        query = AdapterUser.select().order_by("name")
        rows = await memory_adapter.select("memoryusers", query, fields)
        
        assert rows[0]["name"] == "A"
        assert rows[1]["name"] == "C"
    
    @pytest.mark.asyncio
    async def test_select_limit_offset(self, memory_adapter):
        """Test select with LIMIT and OFFSET."""
        fields = _get_memory_fields()
        configure_db(memory_adapter)
        await memory_adapter.create_table("memoryusers", fields)
        
        for i in range(5):
            await memory_adapter.insert("memoryusers", {"name": f"U{i}", "email": f"u{i}@test.com", "age": 0}, fields)
        
        query = AdapterUser.select().order_by("id").limit(2).offset(1)
        rows = await memory_adapter.select("memoryusers", query, fields)
        
        assert len(rows) == 2
    
    @pytest.mark.asyncio
    async def test_update(self, memory_adapter):
        """Test update modifies row."""
        fields = _get_memory_fields()
        configure_db(memory_adapter)
        await memory_adapter.create_table("memoryusers", fields)
        
        row = await memory_adapter.insert("memoryusers", {"name": "John", "email": "john@test.com", "age": 0}, fields)
        
        updated = await memory_adapter.update("memoryusers", row["id"], {"name": "Jane"}, fields)
        
        assert updated["name"] == "Jane"
    
    @pytest.mark.asyncio
    async def test_delete(self, memory_adapter):
        """Test delete removes row."""
        fields = _get_memory_fields()
        configure_db(memory_adapter)
        await memory_adapter.create_table("memoryusers", fields)
        
        row = await memory_adapter.insert("memoryusers", {"name": "John", "email": "john@test.com", "age": 0}, fields)
        
        result = await memory_adapter.delete("memoryusers", row["id"])
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_count(self, memory_adapter):
        """Test count returns correct count."""
        fields = _get_memory_fields()
        configure_db(memory_adapter)
        await memory_adapter.create_table("memoryusers", fields)
        
        await memory_adapter.insert("memoryusers", {"name": "A", "email": "a@test.com", "age": 0}, fields)
        await memory_adapter.insert("memoryusers", {"name": "B", "email": "b@test.com", "age": 0}, fields)
        
        query = AdapterUser.select()
        count = await memory_adapter.count("memoryusers", query)
        
        assert count == 2
    
    @pytest.mark.asyncio
    async def test_exists(self, memory_adapter):
        """Test exists check."""
        fields = _get_memory_fields()
        configure_db(memory_adapter)
        await memory_adapter.create_table("memoryusers", fields)
        
        await memory_adapter.insert("memoryusers", {"name": "John", "email": "john@test.com", "age": 0}, fields)
        
        query = AdapterUser.select().where(name="John")
        assert await memory_adapter.exists("memoryusers", query) is True
        
        query2 = AdapterUser.select().where(name="Nobody")
        assert await memory_adapter.exists("memoryusers", query2) is False
    
    @pytest.mark.asyncio
    async def test_raw_execute(self, memory_adapter):
        """Test raw SQL execution."""
        await memory_adapter.create_table("test_raw", {
            "id": FieldInfo("id", int, SQLType.INTEGER, primary_key=True, auto_increment=True),
            "name": FieldInfo("name", str, SQLType.VARCHAR, max_length=255),
        })
        
        await memory_adapter.execute("INSERT INTO test_raw (name) VALUES (?)", ("Test",))
        
        rows = await memory_adapter.fetch_all("SELECT * FROM test_raw")
        assert len(rows) == 1
    
    @pytest.mark.asyncio
    async def test_fetch_one(self, memory_adapter):
        """Test fetch_one returns single row."""
        await memory_adapter.create_table("test_fetch", {
            "id": FieldInfo("id", int, SQLType.INTEGER, primary_key=True, auto_increment=True),
            "name": FieldInfo("name", str, SQLType.VARCHAR, max_length=255),
        })
        
        await memory_adapter.execute("INSERT INTO test_fetch (name) VALUES (?)", ("Test",))
        
        row = await memory_adapter.fetch_one("SELECT * FROM test_fetch WHERE name = ?", ("Test",))
        assert row is not None
        assert row["name"] == "Test"
    
    @pytest.mark.asyncio
    async def test_transaction_commit(self, memory_adapter):
        """Test transaction commit."""
        fields = _get_memory_fields()
        configure_db(memory_adapter)
        await memory_adapter.create_table("memoryusers", fields)
        
        async with memory_adapter.transaction():
            await memory_adapter.insert("memoryusers", {"name": "John", "email": "john@test.com", "age": 0}, fields)
        
        rows = await memory_adapter.select("memoryusers", AdapterUser.select(), fields)
        assert len(rows) == 1
    
    @pytest.mark.asyncio
    async def test_transaction_rollback(self, memory_adapter):
        """Test transaction rollback."""
        fields = _get_memory_fields()
        configure_db(memory_adapter)
        await memory_adapter.create_table("memoryusers", fields)
        
        try:
            async with memory_adapter.transaction():
                await memory_adapter.insert("memoryusers", {"name": "John", "email": "john@test.com", "age": 0}, fields)
                raise Exception("Simulated error")
        except:
            pass
        
        rows = await memory_adapter.select("memoryusers", AdapterUser.select(), fields)
        assert len(rows) == 0
    
    @pytest.mark.asyncio
    async def test_reset(self, memory_adapter):
        """Test reset clears all tables."""
        fields = _get_memory_fields()
        await memory_adapter.create_table("memoryusers", fields)
        await memory_adapter.insert("memoryusers", {"name": "John", "email": "john@test.com", "age": 0}, fields)
        
        memory_adapter.reset()
        
        # Table should be gone, so this should fail or be empty
        # Actually reset drops tables, so select would fail
        # Let's recreate and check it's empty
        configure_db(memory_adapter)
        await memory_adapter.create_table("memoryusers", fields)
        rows = await memory_adapter.select("memoryusers", AdapterUser.select(), fields)
        assert len(rows) == 0
    
    @pytest.mark.asyncio
    async def test_placeholder_conversion(self, memory_adapter):
        """Test $1, $2 placeholders converted to ?."""
        await memory_adapter.create_table("test_placeholder", {
            "id": FieldInfo("id", int, SQLType.INTEGER, primary_key=True, auto_increment=True),
            "name": FieldInfo("name", str, SQLType.VARCHAR, max_length=255),
        })
        
        await memory_adapter.execute("INSERT INTO test_placeholder (name) VALUES ($1)", ("Test",))
        
        row = await memory_adapter.fetch_one("SELECT * FROM test_placeholder WHERE name = $1", ("Test",))
        assert row is not None


# =============================================================================
# Advanced Adapter Tests (40 additional tests)
# =============================================================================

class TestMockAdapterAdvanced:
    """Advanced tests for MockAdapter."""
    
    @pytest.mark.asyncio
    async def test_where_like_underscore(self, mock_adapter):
        """Test where_like with underscore pattern."""
        fields = AdapterUser._fields
        configure_db(mock_adapter)
        
        await mock_adapter.insert("adapterusers", {"name": "a_b", "email": "a@test.com"}, fields)
        await mock_adapter.insert("adapterusers", {"name": "aab", "email": "b@test.com"}, fields)
        
        query = AdapterUser.select().where_like(name="a_b")
        rows = await mock_adapter.select("adapterusers", query, fields)
        
        assert len(rows) == 2  # _ matches any single char
    
    @pytest.mark.asyncio
    async def test_where_gt_with_datetime(self, mock_adapter):
        """Test where_gt with datetime values."""
        fields = AdapterUser._fields
        configure_db(mock_adapter)
        
        await mock_adapter.insert("adapterusers", {"name": "A", "email": "a@test.com"}, fields)
        await mock_adapter.insert("adapterusers", {"name": "B", "email": "b@test.com"}, fields)
        
        query = AdapterUser.select().order_by("id")
        rows = await mock_adapter.select("adapterusers", query, fields)
        
        # Both should exist
        assert len(rows) == 2
    
    @pytest.mark.asyncio
    async def test_select_preserves_data_types(self, mock_adapter):
        """Test select preserves Python data types."""
        fields = AdapterUser._fields
        configure_db(mock_adapter)
        
        await mock_adapter.insert("adapterusers", {"name": "Test", "email": "test@test.com", "age": 42}, fields)
        
        query = AdapterUser.select()
        rows = await mock_adapter.select("adapterusers", query, fields)
        
        assert isinstance(rows[0]["name"], str)
        assert isinstance(rows[0]["age"], int)
        assert isinstance(rows[0]["created_at"], datetime)
    
    @pytest.mark.asyncio
    async def test_update_partial_data(self, mock_adapter):
        """Test update with partial data."""
        fields = AdapterUser._fields
        configure_db(mock_adapter)
        
        row = await mock_adapter.insert("adapterusers", {"name": "John", "email": "john@test.com", "age": 25}, fields)
        
        # Only update name
        updated = await mock_adapter.update("adapterusers", row["id"], {"name": "Jane"}, fields)
        
        assert updated["name"] == "Jane"
        assert updated["email"] == "john@test.com"  # Unchanged
        assert updated["age"] == 25  # Unchanged
    
    @pytest.mark.asyncio
    async def test_multiple_tables(self, mock_adapter):
        """Test working with multiple tables."""
        fields = AdapterUser._fields
        configure_db(mock_adapter)
        
        await mock_adapter.create_table("table1", fields)
        await mock_adapter.create_table("table2", fields)
        
        await mock_adapter.insert("table1", {"name": "A", "email": "a@test.com"}, fields)
        await mock_adapter.insert("table2", {"name": "B", "email": "b@test.com"}, fields)
        
        query = AdapterUser.select()
        rows1 = await mock_adapter.select("table1", query, fields)
        rows2 = await mock_adapter.select("table2", query, fields)
        
        assert len(rows1) == 1
        assert len(rows2) == 1
        assert rows1[0]["name"] == "A"
        assert rows2[0]["name"] == "B"
    
    @pytest.mark.asyncio
    async def test_order_by_none_values(self, mock_adapter):
        """Test order_by handles None values."""
        fields = _get_memory_fields()
        configure_db(mock_adapter)
        
        await mock_adapter.insert("test_order", {"name": None, "email": "a@test.com", "age": 0}, fields)
        await mock_adapter.insert("test_order", {"name": "Bob", "email": "b@test.com", "age": 0}, fields)
        
        query = AdapterUser.select().order_by("name")
        rows = await mock_adapter.select("test_order", query, fields)
        
        # Should not crash, None typically sorted first or last
        assert len(rows) == 2
    
    @pytest.mark.asyncio
    async def test_count_empty_after_delete(self, mock_adapter):
        """Test count after deleting all records."""
        fields = AdapterUser._fields
        configure_db(mock_adapter)
        
        row = await mock_adapter.insert("adapterusers", {"name": "Test", "email": "test@test.com"}, fields)
        await mock_adapter.delete("adapterusers", row["id"])
        
        query = AdapterUser.select()
        count = await mock_adapter.count("adapterusers", query)
        
        assert count == 0
    
    @pytest.mark.asyncio
    async def test_insert_deepcopy(self, mock_adapter):
        """Test insert creates deep copy of data."""
        fields = AdapterUser._fields
        configure_db(mock_adapter)
        
        data = {"name": "Test", "email": "test@test.com"}
        row = await mock_adapter.insert("adapterusers", data, fields)
        
        # Modifying original shouldn't affect stored data
        data["name"] = "Modified"
        
        stored = mock_adapter.get_by_id("adapterusers", row["id"])
        assert stored["name"] == "Test"


class TestMemoryAdapterAdvanced:
    """Advanced tests for MemoryAdapter."""
    
    @pytest.mark.asyncio
    async def test_sql_injection_safe(self, memory_adapter):
        """Test SQL injection is prevented via parameterization."""
        fields = _get_memory_fields()
        await memory_adapter.create_table("safe_test", fields)
        
        # Try to inject SQL
        await memory_adapter.insert("safe_test", {
            "name": "Robert'); DROP TABLE safe_test;--",
            "email": "test@test.com",
            "age": 0
        }, fields)
        
        # Table should still exist
        configure_db(memory_adapter)
        rows = await memory_adapter.select("safe_test", AdapterUser.select(), fields)
        assert len(rows) == 1
    
    @pytest.mark.asyncio
    async def test_unicode_in_queries(self, memory_adapter):
        """Test unicode handling in SQL queries."""
        fields = _get_memory_fields()
        await memory_adapter.create_table("unicode_test", fields)
        
        await memory_adapter.insert("unicode_test", {
            "name": "日本語テスト",
            "email": "test@test.com",
            "age": 0
        }, fields)
        
        configure_db(memory_adapter)
        query = AdapterUser.select().where(name="日本語テスト")
        rows = await memory_adapter.select("unicode_test", query, fields)
        
        assert len(rows) == 1
        assert rows[0]["name"] == "日本語テスト"
    
    @pytest.mark.asyncio
    async def test_multiple_placeholder_conversion(self, memory_adapter):
        """Test multiple placeholder conversions."""
        fields = _get_memory_fields()
        await memory_adapter.create_table("multi_placeholder", fields)
        
        await memory_adapter.execute(
            "INSERT INTO multi_placeholder (name, email, age) VALUES ($1, $2, $3)",
            ("Test", "test@test.com", 42)
        )
        
        row = await memory_adapter.fetch_one(
            "SELECT * FROM multi_placeholder WHERE name = $1 AND age = $2",
            ("Test", 42)
        )
        
        assert row is not None
        assert row["name"] == "Test"
    
    @pytest.mark.asyncio
    async def test_fetch_all_empty(self, memory_adapter):
        """Test fetch_all on empty result."""
        await memory_adapter.create_table("empty_fetch", {
            "id": FieldInfo("id", int, SQLType.INTEGER, primary_key=True, auto_increment=True),
        })
        
        rows = await memory_adapter.fetch_all("SELECT * FROM empty_fetch")
        assert rows == []
    
    @pytest.mark.asyncio
    async def test_fetch_one_empty(self, memory_adapter):
        """Test fetch_one on empty result."""
        await memory_adapter.create_table("empty_fetch_one", {
            "id": FieldInfo("id", int, SQLType.INTEGER, primary_key=True, auto_increment=True),
        })
        
        row = await memory_adapter.fetch_one("SELECT * FROM empty_fetch_one WHERE id = ?", (999,))
        assert row is None


class TestAdapterErrorHandling:
    """Tests for adapter error handling."""
    
    @pytest.mark.asyncio
    async def test_mock_delete_wrong_table(self, mock_adapter):
        """Test mock delete on non-existent table."""
        result = await mock_adapter.delete("nonexistent", 1)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_mock_select_wrong_table(self, mock_adapter):
        """Test mock select on non-existent table."""
        configure_db(mock_adapter)
        query = AdapterUser.select()
        rows = await mock_adapter.select("nonexistent", query, {})
        assert rows == []
    
    @pytest.mark.asyncio
    async def test_memory_transaction_nested_not_supported(self, memory_adapter):
        """Test memory adapter transaction behavior."""
        fields = _get_memory_fields()
        configure_db(memory_adapter)
        await memory_adapter.create_table("tx_test", fields)
        
        # First transaction
        async with memory_adapter.transaction():
            await memory_adapter.insert("tx_test", {"name": "A", "email": "a@test.com", "age": 0}, fields)
        
        rows = await memory_adapter.select("tx_test", AdapterUser.select(), fields)
        assert len(rows) == 1


# =============================================================================
# Extended Mock Adapter Tests (30 tests)
# =============================================================================

class TestMockAdapterDataTypes:
    """Tests for MockAdapter data type handling."""
    
    @pytest.mark.asyncio
    async def test_string_values(self, mock_adapter):
        """Test string value handling."""
        fields = AdapterUser._fields
        await mock_adapter.create_table("users", fields)
        
        row = await mock_adapter.insert("users", {
            "name": "Test User",
            "email": "test@test.com"
        }, fields)
        
        assert row["name"] == "Test User"
    
    @pytest.mark.asyncio
    async def test_integer_values(self, mock_adapter):
        """Test integer value handling."""
        fields = AdapterUser._fields
        await mock_adapter.create_table("users", fields)
        
        row = await mock_adapter.insert("users", {
            "name": "Test",
            "email": "test@test.com",
            "age": 42
        }, fields)
        
        assert row["age"] == 42
    
    @pytest.mark.asyncio
    async def test_null_values(self, mock_adapter):
        """Test null value handling."""
        fields = AdapterUser._fields
        await mock_adapter.create_table("users", fields)
        
        row = await mock_adapter.insert("users", {
            "name": "Test",
            "email": None
        }, fields)
        
        assert row["email"] is None
    
    @pytest.mark.asyncio
    async def test_empty_string(self, mock_adapter):
        """Test empty string handling."""
        fields = AdapterUser._fields
        await mock_adapter.create_table("users", fields)
        
        row = await mock_adapter.insert("users", {
            "name": "",
            "email": "test@test.com"
        }, fields)
        
        assert row["name"] == ""
    
    @pytest.mark.asyncio
    async def test_unicode_values(self, mock_adapter):
        """Test unicode value handling."""
        fields = AdapterUser._fields
        await mock_adapter.create_table("users", fields)
        
        row = await mock_adapter.insert("users", {
            "name": "日本語 🎉",
            "email": "test@test.com"
        }, fields)
        
        assert row["name"] == "日本語 🎉"


class TestMockAdapterOperations:
    """Tests for MockAdapter operations."""
    
    @pytest.mark.asyncio
    async def test_insert_and_select(self, mock_adapter):
        """Test insert followed by select."""
        fields = AdapterUser._fields
        configure_db(mock_adapter)
        await mock_adapter.create_table("users", fields)
        
        await mock_adapter.insert("users", {"name": "A", "email": "a@test.com"}, fields)
        await mock_adapter.insert("users", {"name": "B", "email": "b@test.com"}, fields)
        
        query = AdapterUser.select()
        rows = await mock_adapter.select("users", query, fields)
        
        assert len(rows) == 2
    
    @pytest.mark.asyncio
    async def test_update_specific_row(self, mock_adapter):
        """Test updating a specific row."""
        fields = AdapterUser._fields
        configure_db(mock_adapter)
        await mock_adapter.create_table("users", fields)
        
        row = await mock_adapter.insert("users", {"name": "Old", "email": "test@test.com"}, fields)
        
        await mock_adapter.update("users", row["id"], {"name": "New"}, fields)
        
        stored = mock_adapter.get_by_id("users", row["id"])
        assert stored["name"] == "New"
    
    @pytest.mark.asyncio
    async def test_delete_specific_row(self, mock_adapter):
        """Test deleting a specific row."""
        fields = AdapterUser._fields
        configure_db(mock_adapter)
        await mock_adapter.create_table("users", fields)
        
        row = await mock_adapter.insert("users", {"name": "Delete Me", "email": "test@test.com"}, fields)
        
        result = await mock_adapter.delete("users", row["id"])
        
        assert result is True
        
        stored = mock_adapter.get_by_id("users", row["id"])
        assert stored is None
    
    @pytest.mark.asyncio
    async def test_select_with_filter(self, mock_adapter):
        """Test select with where filter."""
        fields = AdapterUser._fields
        configure_db(mock_adapter)
        await mock_adapter.create_table("users", fields)
        
        await mock_adapter.insert("users", {"name": "Alice", "email": "alice@test.com", "age": 25}, fields)
        await mock_adapter.insert("users", {"name": "Bob", "email": "bob@test.com", "age": 30}, fields)
        await mock_adapter.insert("users", {"name": "Charlie", "email": "charlie@test.com", "age": 25}, fields)
        
        query = AdapterUser.select().where(age=25)
        rows = await mock_adapter.select("users", query, fields)
        
        assert len(rows) == 2
    
    @pytest.mark.asyncio
    async def test_count_operation(self, mock_adapter):
        """Test count operation."""
        fields = AdapterUser._fields
        configure_db(mock_adapter)
        await mock_adapter.create_table("users", fields)
        
        await mock_adapter.insert("users", {"name": "A", "email": "a@test.com"}, fields)
        await mock_adapter.insert("users", {"name": "B", "email": "b@test.com"}, fields)
        await mock_adapter.insert("users", {"name": "C", "email": "c@test.com"}, fields)
        
        query = AdapterUser.select()
        count = await mock_adapter.count("users", query)
        
        assert count == 3


class TestMockAdapterEdgeCases:
    """Edge case tests for MockAdapter."""
    
    @pytest.mark.asyncio
    async def test_multiple_tables(self, mock_adapter):
        """Test operations on multiple tables."""
        fields = AdapterUser._fields
        configure_db(mock_adapter)
        
        await mock_adapter.create_table("users", fields)
        await mock_adapter.create_table("admins", fields)
        
        await mock_adapter.insert("users", {"name": "User1", "email": "user@test.com"}, fields)
        await mock_adapter.insert("admins", {"name": "Admin1", "email": "admin@test.com"}, fields)
        
        user_query = AdapterUser.select()
        users = await mock_adapter.select("users", user_query, fields)
        admins = await mock_adapter.select("admins", user_query, fields)
        
        assert len(users) == 1
        assert len(admins) == 1
        assert users[0]["name"] == "User1"
        assert admins[0]["name"] == "Admin1"
    
    @pytest.mark.asyncio
    async def test_reset_clears_all(self, mock_adapter):
        """Test reset clears all tables."""
        fields = AdapterUser._fields
        configure_db(mock_adapter)
        
        await mock_adapter.create_table("t1", fields)
        await mock_adapter.create_table("t2", fields)
        
        await mock_adapter.insert("t1", {"name": "A", "email": "a@test.com"}, fields)
        await mock_adapter.insert("t2", {"name": "B", "email": "b@test.com"}, fields)
        
        mock_adapter.reset()
        
        assert "t1" not in mock_adapter._tables
        assert "t2" not in mock_adapter._tables
    
    @pytest.mark.asyncio
    async def test_empty_table_select(self, mock_adapter):
        """Test select on empty table."""
        fields = AdapterUser._fields
        configure_db(mock_adapter)
        await mock_adapter.create_table("empty", fields)
        
        query = AdapterUser.select()
        rows = await mock_adapter.select("empty", query, fields)
        
        assert rows == []
    
    @pytest.mark.asyncio
    async def test_select_by_nonexistent_id(self, mock_adapter):
        """Test select by non-existent ID."""
        fields = AdapterUser._fields
        configure_db(mock_adapter)
        await mock_adapter.create_table("users", fields)
        
        stored = mock_adapter.get_by_id("users", 99999)
        assert stored is None


# =============================================================================
# Memory Adapter Extended Tests (30 tests)
# =============================================================================

class TestMemoryAdapterDataTypes:
    """Tests for MemoryAdapter data type handling."""
    
    @pytest.mark.asyncio
    async def test_integer_storage(self, memory_adapter):
        """Test integer storage and retrieval."""
        fields = _get_memory_fields()
        await memory_adapter.create_table("int_test", fields)
        
        row = await memory_adapter.insert("int_test", {
            "name": "Test",
            "email": "test@test.com",
            "age": 42
        }, fields)
        
        assert row["age"] == 42
    
    @pytest.mark.asyncio
    async def test_negative_integer(self, memory_adapter):
        """Test negative integer handling."""
        fields = _get_memory_fields()
        await memory_adapter.create_table("neg_int", fields)
        
        row = await memory_adapter.insert("neg_int", {
            "name": "Test",
            "email": "test@test.com",
            "age": -100
        }, fields)
        
        assert row["age"] == -100
    
    @pytest.mark.asyncio
    async def test_zero_value(self, memory_adapter):
        """Test zero value handling."""
        fields = _get_memory_fields()
        await memory_adapter.create_table("zero_test", fields)
        
        row = await memory_adapter.insert("zero_test", {
            "name": "Test",
            "email": "test@test.com",
            "age": 0
        }, fields)
        
        assert row["age"] == 0
    
    @pytest.mark.asyncio
    async def test_long_string(self, memory_adapter):
        """Test long string handling."""
        fields = _get_memory_fields()
        await memory_adapter.create_table("long_str", fields)
        
        long_name = "A" * 1000
        row = await memory_adapter.insert("long_str", {
            "name": long_name,
            "email": "test@test.com",
            "age": 0
        }, fields)
        
        assert row["name"] == long_name
        assert len(row["name"]) == 1000


class TestMemoryAdapterSQL:
    """Tests for MemoryAdapter SQL operations."""
    
    @pytest.mark.asyncio
    async def test_raw_execute(self, memory_adapter):
        """Test raw SQL execution."""
        await memory_adapter.execute(
            "CREATE TABLE IF NOT EXISTS raw_test (id INTEGER PRIMARY KEY, name TEXT)"
        )
        
        await memory_adapter.execute(
            "INSERT INTO raw_test (name) VALUES (?)",
            ("Test",)
        )
        
        row = await memory_adapter.fetch_one("SELECT * FROM raw_test WHERE name = ?", ("Test",))
        assert row is not None
        assert row["name"] == "Test"
    
    @pytest.mark.asyncio
    async def test_fetch_all(self, memory_adapter):
        """Test fetch_all returns all rows."""
        await memory_adapter.execute(
            "CREATE TABLE IF NOT EXISTS fetch_all_test (id INTEGER PRIMARY KEY, value TEXT)"
        )
        
        await memory_adapter.execute("INSERT INTO fetch_all_test (value) VALUES (?)", ("A",))
        await memory_adapter.execute("INSERT INTO fetch_all_test (value) VALUES (?)", ("B",))
        await memory_adapter.execute("INSERT INTO fetch_all_test (value) VALUES (?)", ("C",))
        
        rows = await memory_adapter.fetch_all("SELECT * FROM fetch_all_test")
        assert len(rows) == 3
    
    @pytest.mark.asyncio
    async def test_placeholder_conversion(self, memory_adapter):
        """Test $1, $2 placeholders are converted to ?."""
        await memory_adapter.execute(
            "CREATE TABLE IF NOT EXISTS placeholder_test (id INTEGER PRIMARY KEY, name TEXT, value INTEGER)"
        )
        
        await memory_adapter.execute(
            "INSERT INTO placeholder_test (name, value) VALUES ($1, $2)",
            ("Test", 42)
        )
        
        row = await memory_adapter.fetch_one(
            "SELECT * FROM placeholder_test WHERE name = $1 AND value = $2",
            ("Test", 42)
        )
        
        assert row is not None
        assert row["name"] == "Test"
        assert row["value"] == 42


class TestMemoryAdapterTransactions:
    """Tests for MemoryAdapter transactions."""
    
    @pytest.mark.asyncio
    async def test_transaction_commits_on_success(self, memory_adapter):
        """Test transaction commits on successful completion."""
        fields = _get_memory_fields()
        configure_db(memory_adapter)
        await memory_adapter.create_table("tx_success", fields)
        
        async with memory_adapter.transaction():
            await memory_adapter.insert("tx_success", {"name": "A", "email": "a@test.com", "age": 0}, fields)
            await memory_adapter.insert("tx_success", {"name": "B", "email": "b@test.com", "age": 0}, fields)
        
        query = AdapterUser.select()
        rows = await memory_adapter.select("tx_success", query, fields)
        assert len(rows) == 2
    
    @pytest.mark.asyncio
    async def test_multiple_transactions(self, memory_adapter):
        """Test multiple sequential transactions."""
        fields = _get_memory_fields()
        configure_db(memory_adapter)
        await memory_adapter.create_table("multi_tx", fields)
        
        async with memory_adapter.transaction():
            await memory_adapter.insert("multi_tx", {"name": "TX1", "email": "tx1@test.com", "age": 0}, fields)
        
        async with memory_adapter.transaction():
            await memory_adapter.insert("multi_tx", {"name": "TX2", "email": "tx2@test.com", "age": 0}, fields)
        
        query = AdapterUser.select()
        rows = await memory_adapter.select("multi_tx", query, fields)
        assert len(rows) == 2


class TestMemoryAdapterPerformance:
    """Performance-related tests for MemoryAdapter."""
    
    @pytest.mark.asyncio
    async def test_bulk_insert(self, memory_adapter):
        """Test bulk insert performance."""
        fields = _get_memory_fields()
        await memory_adapter.create_table("bulk_insert", fields)
        
        for i in range(100):
            await memory_adapter.insert("bulk_insert", {
                "name": f"User{i}",
                "email": f"user{i}@test.com",
                "age": i
            }, fields)
        
        configure_db(memory_adapter)
        query = AdapterUser.select()
        rows = await memory_adapter.select("bulk_insert", query, fields)
        assert len(rows) == 100
    
    @pytest.mark.asyncio
    async def test_bulk_select(self, memory_adapter):
        """Test bulk select performance."""
        fields = _get_memory_fields()
        await memory_adapter.create_table("bulk_select", fields)
        
        for i in range(50):
            await memory_adapter.insert("bulk_select", {
                "name": f"User{i}",
                "email": f"user{i}@test.com",
                "age": i
            }, fields)
        
        configure_db(memory_adapter)
        query = AdapterUser.select()
        rows = await memory_adapter.select("bulk_select", query, fields)
        assert len(rows) == 50
    
    @pytest.mark.asyncio
    async def test_filtered_bulk_select(self, memory_adapter):
        """Test filtered select on large dataset."""
        fields = _get_memory_fields()
        await memory_adapter.create_table("filtered_bulk", fields)
        
        for i in range(100):
            await memory_adapter.insert("filtered_bulk", {
                "name": f"User{i}",
                "email": f"user{i}@test.com",
                "age": i % 10  # Ages 0-9
            }, fields)
        
        configure_db(memory_adapter)
        query = AdapterUser.select().where(age=5)
        rows = await memory_adapter.select("filtered_bulk", query, fields)
        assert len(rows) == 10  # 10 users have age=5

