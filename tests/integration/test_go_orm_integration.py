"""
Integration tests for Go Bridge with PyNext ORM.

Tests the full integration path from Table.q() through Go bridge.
These tests are designed to work both with and without the actual
Go library by using mocks where needed.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Optional

from pynext.db.adapters.go_adapter import GoPostgresAdapter, is_go_available


# =============================================================================
# Mock Table for Testing
# =============================================================================

class MockTable:
    """Mock Table class for testing ORM integration."""
    
    __table_name__ = "users"
    __fields__ = {
        "id": Mock(name="id", sql_type=Mock()),
        "name": Mock(name="name", sql_type=Mock()),
        "email": Mock(name="email", sql_type=Mock()),
        "age": Mock(name="age", sql_type=Mock()),
    }
    
    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.name = kwargs.get("name")
        self.email = kwargs.get("email")
        self.age = kwargs.get("age")


class MockQuery:
    """Mock Query class for testing."""
    
    def __init__(self):
        self._filters = []
        self._order_by = []
        self._limit = None
        self._offset = None
    
    def where(self, field, op, value):
        self._filters.append((field, op, value))
        return self
    
    def order_by(self, field, desc=False):
        self._order_by.append((field, desc))
        return self
    
    def limit(self, n):
        self._limit = n
        return self
    
    def offset(self, n):
        self._offset = n
        return self


# =============================================================================
# Integration Tests
# =============================================================================

class TestGoAdapterTableIntegration:
    """Tests for adapter integration with Table-like objects."""
    
    @pytest.fixture
    def adapter(self):
        """Create adapter with mock bridge."""
        adapter = GoPostgresAdapter("postgresql://localhost/test")
        adapter._connected = True
        adapter._bridge = Mock()
        return adapter
    
    @pytest.mark.asyncio
    async def test_select_all_users(self, adapter):
        """Select all users from table."""
        adapter._bridge.execute.return_value = Mock(
            success=True,
            to_dicts=lambda: [
                {"id": 1, "name": "Alice", "email": "alice@example.com", "age": 25},
                {"id": 2, "name": "Bob", "email": "bob@example.com", "age": 30},
            ],
        )
        
        query = MockQuery()
        results = await adapter.select("users", query, MockTable.__fields__)
        
        assert len(results) == 2
        assert results[0]["name"] == "Alice"
        assert results[1]["name"] == "Bob"
    
    @pytest.mark.asyncio
    async def test_select_with_filter(self, adapter):
        """Select users with age filter."""
        adapter._bridge.execute.return_value = Mock(
            success=True,
            to_dicts=lambda: [
                {"id": 2, "name": "Bob", "email": "bob@example.com", "age": 30},
            ],
        )
        
        query = MockQuery().where("age", ">=", 30)
        results = await adapter.select("users", query, MockTable.__fields__)
        
        assert len(results) == 1
        assert results[0]["age"] == 30
        
        # Verify SQL was built correctly
        call_args = adapter._bridge.execute.call_args
        sql = call_args[0][0]
        assert "WHERE" in sql
        assert '"age" >=' in sql
    
    @pytest.mark.asyncio
    async def test_select_with_order(self, adapter):
        """Select users ordered by name."""
        adapter._bridge.execute.return_value = Mock(
            success=True,
            to_dicts=lambda: [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"},
            ],
        )
        
        query = MockQuery().order_by("name", desc=False)
        results = await adapter.select("users", query, MockTable.__fields__)
        
        call_args = adapter._bridge.execute.call_args
        sql = call_args[0][0]
        assert "ORDER BY" in sql
        assert '"name" ASC' in sql
    
    @pytest.mark.asyncio
    async def test_select_with_pagination(self, adapter):
        """Select users with limit and offset."""
        adapter._bridge.execute.return_value = Mock(
            success=True,
            to_dicts=lambda: [{"id": 3, "name": "Charlie"}],
        )
        
        query = MockQuery().limit(10).offset(20)
        results = await adapter.select("users", query, MockTable.__fields__)
        
        call_args = adapter._bridge.execute.call_args
        sql = call_args[0][0]
        assert "LIMIT 10" in sql
        assert "OFFSET 20" in sql
    
    @pytest.mark.asyncio
    async def test_select_one(self, adapter):
        """Select single user by id."""
        adapter._bridge.execute.return_value = Mock(
            success=True,
            to_dicts=lambda: [
                {"id": 1, "name": "Alice", "email": "alice@example.com"},
            ],
        )
        
        query = MockQuery().where("id", "=", 1)
        result = await adapter.select_one("users", query, MockTable.__fields__)
        
        assert result is not None
        assert result["id"] == 1
        assert result["name"] == "Alice"
    
    @pytest.mark.asyncio
    async def test_select_one_not_found(self, adapter):
        """Select single user not found returns None."""
        adapter._bridge.execute.return_value = Mock(
            success=True,
            to_dicts=lambda: [],
        )
        
        query = MockQuery().where("id", "=", 9999)
        result = await adapter.select_one("users", query, MockTable.__fields__)
        
        assert result is None


class TestGoAdapterInsertIntegration:
    """Tests for insert operations."""
    
    @pytest.fixture
    def adapter(self):
        """Create adapter with mock bridge."""
        adapter = GoPostgresAdapter("postgresql://localhost/test")
        adapter._connected = True
        adapter._bridge = Mock()
        return adapter
    
    @pytest.mark.asyncio
    async def test_insert_user(self, adapter):
        """Insert new user."""
        adapter._bridge.execute.return_value = Mock(
            success=True,
            to_dicts=lambda: [
                {"id": 3, "name": "Charlie", "email": "charlie@example.com", "age": 28},
            ],
        )
        
        data = {"name": "Charlie", "email": "charlie@example.com", "age": 28}
        result = await adapter.insert("users", data, MockTable.__fields__)
        
        assert result["id"] == 3
        assert result["name"] == "Charlie"
        
        # Verify SQL
        call_args = adapter._bridge.execute.call_args
        sql = call_args[0][0]
        assert "INSERT INTO" in sql
        assert "RETURNING *" in sql
    
    @pytest.mark.asyncio
    async def test_insert_minimal_user(self, adapter):
        """Insert user with only required fields."""
        adapter._bridge.execute.return_value = Mock(
            success=True,
            to_dicts=lambda: [
                {"id": 4, "name": "Dave", "email": None, "age": None},
            ],
        )
        
        data = {"name": "Dave"}
        result = await adapter.insert("users", data, MockTable.__fields__)
        
        assert result["id"] == 4
        assert result["name"] == "Dave"


class TestGoAdapterUpdateIntegration:
    """Tests for update operations."""
    
    @pytest.fixture
    def adapter(self):
        """Create adapter with mock bridge."""
        adapter = GoPostgresAdapter("postgresql://localhost/test")
        adapter._connected = True
        adapter._bridge = Mock()
        return adapter
    
    @pytest.mark.asyncio
    async def test_update_user(self, adapter):
        """Update user by id."""
        adapter._bridge.execute.return_value = Mock(
            success=True,
            to_dicts=lambda: [
                {"id": 1, "name": "Alice Updated", "email": "alice@example.com", "age": 26},
            ],
        )
        
        data = {"name": "Alice Updated", "age": 26}
        result = await adapter.update("users", 1, data, MockTable.__fields__)
        
        assert result["name"] == "Alice Updated"
        assert result["age"] == 26
        
        # Verify SQL
        call_args = adapter._bridge.execute.call_args
        sql = call_args[0][0]
        assert "UPDATE" in sql
        assert "SET" in sql
        assert "WHERE id" in sql
    
    @pytest.mark.asyncio
    async def test_update_no_data(self, adapter):
        """Update with no data should just return current record."""
        adapter._bridge.execute.return_value = Mock(
            success=True,
            to_dicts=lambda: [
                {"id": 1, "name": "Alice", "email": "alice@example.com"},
            ],
        )
        
        result = await adapter.update("users", 1, {}, MockTable.__fields__)
        
        # Should have fetched current record
        call_args = adapter._bridge.execute.call_args
        sql = call_args[0][0]
        assert "SELECT" in sql


class TestGoAdapterDeleteIntegration:
    """Tests for delete operations."""
    
    @pytest.fixture
    def adapter(self):
        """Create adapter with mock bridge."""
        adapter = GoPostgresAdapter("postgresql://localhost/test")
        adapter._connected = True
        adapter._bridge = Mock()
        return adapter
    
    @pytest.mark.asyncio
    async def test_delete_user(self, adapter):
        """Delete user by id."""
        adapter._bridge.execute.return_value = Mock(
            success=True,
            rows_affected=1,
        )
        
        result = await adapter.delete("users", 1)
        
        assert result is True
        
        # Verify SQL
        call_args = adapter._bridge.execute.call_args
        sql = call_args[0][0]
        assert "DELETE FROM" in sql
        assert "WHERE id" in sql
    
    @pytest.mark.asyncio
    async def test_delete_not_found(self, adapter):
        """Delete non-existent user returns False."""
        adapter._bridge.execute.return_value = Mock(
            success=True,
            rows_affected=0,
        )
        
        result = await adapter.delete("users", 9999)
        
        assert result is False


class TestGoAdapterCountIntegration:
    """Tests for count operations."""
    
    @pytest.fixture
    def adapter(self):
        """Create adapter with mock bridge."""
        adapter = GoPostgresAdapter("postgresql://localhost/test")
        adapter._connected = True
        adapter._bridge = Mock()
        return adapter
    
    @pytest.mark.asyncio
    async def test_count_all(self, adapter):
        """Count all users."""
        adapter._bridge.execute.return_value = Mock(
            success=True,
            to_dicts=lambda: [{"count": 42}],
        )
        
        query = MockQuery()
        result = await adapter.count("users", query)
        
        assert result == 42
        
        # Verify SQL
        call_args = adapter._bridge.execute.call_args
        sql = call_args[0][0]
        assert "COUNT(*)" in sql
    
    @pytest.mark.asyncio
    async def test_count_with_filter(self, adapter):
        """Count users with filter."""
        adapter._bridge.execute.return_value = Mock(
            success=True,
            to_dicts=lambda: [{"count": 10}],
        )
        
        query = MockQuery().where("age", ">=", 18)
        result = await adapter.count("users", query)
        
        assert result == 10


class TestGoAdapterExistsIntegration:
    """Tests for exists operations."""
    
    @pytest.fixture
    def adapter(self):
        """Create adapter with mock bridge."""
        adapter = GoPostgresAdapter("postgresql://localhost/test")
        adapter._connected = True
        adapter._bridge = Mock()
        return adapter
    
    @pytest.mark.asyncio
    async def test_exists_true(self, adapter):
        """Exists returns True when records match."""
        adapter._bridge.execute.return_value = Mock(
            success=True,
            to_dicts=lambda: [{"count": 5}],
        )
        
        query = MockQuery().where("age", ">", 18)
        result = await adapter.exists("users", query)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_exists_false(self, adapter):
        """Exists returns False when no records match."""
        adapter._bridge.execute.return_value = Mock(
            success=True,
            to_dicts=lambda: [{"count": 0}],
        )
        
        query = MockQuery().where("age", ">", 100)
        result = await adapter.exists("users", query)
        
        assert result is False


class TestGoAdapterTransactionIntegration:
    """Tests for transaction integration."""
    
    @pytest.fixture
    def adapter(self):
        """Create adapter with mock bridge."""
        adapter = GoPostgresAdapter("postgresql://localhost/test")
        adapter._connected = True
        adapter._bridge = Mock()
        adapter._bridge.execute.return_value = Mock(success=True, rows_affected=0)
        return adapter
    
    @pytest.mark.asyncio
    async def test_transaction_lifecycle(self, adapter):
        """Test begin, operations, commit."""
        await adapter.begin_transaction()
        assert adapter._in_transaction is True
        
        # Simulate operations
        adapter._bridge.execute.return_value = Mock(
            success=True,
            to_dicts=lambda: [{"id": 1}],
        )
        await adapter.fetch_one("SELECT 1")
        
        await adapter.commit_transaction()
        assert adapter._in_transaction is False
    
    @pytest.mark.asyncio
    async def test_transaction_rollback(self, adapter):
        """Test begin, operations, rollback."""
        await adapter.begin_transaction()
        assert adapter._in_transaction is True
        
        await adapter.rollback_transaction()
        assert adapter._in_transaction is False


class TestGoAdapterBatchIntegration:
    """Tests for batch operations."""
    
    @pytest.fixture
    def adapter(self):
        """Create adapter with mock bridge."""
        adapter = GoPostgresAdapter("postgresql://localhost/test")
        adapter._connected = True
        adapter._bridge = Mock()
        return adapter
    
    @pytest.mark.asyncio
    async def test_insert_many(self, adapter):
        """Insert multiple records."""
        # Mock consecutive insert calls
        call_count = [0]
        
        def mock_execute(sql, params):
            call_count[0] += 1
            return Mock(
                success=True,
                to_dicts=lambda: [{"id": call_count[0], "name": f"User{call_count[0]}"}],
            )
        
        adapter._bridge.execute = Mock(side_effect=mock_execute)
        
        records = [
            {"name": "User1"},
            {"name": "User2"},
            {"name": "User3"},
        ]
        
        results = await adapter.insert_many("users", records, MockTable.__fields__)
        
        assert len(results) == 3
        assert adapter._bridge.execute.call_count == 3


class TestGoAdapterErrorIntegration:
    """Tests for error handling in operations."""
    
    @pytest.fixture
    def adapter(self):
        """Create adapter with mock bridge."""
        adapter = GoPostgresAdapter("postgresql://localhost/test")
        adapter._connected = True
        adapter._bridge = Mock()
        return adapter
    
    @pytest.mark.asyncio
    async def test_query_error_raised(self, adapter):
        """Query error should be raised."""
        adapter._bridge.execute.return_value = Mock(
            success=False,
            error="relation 'nonexistent' does not exist",
        )
        
        with pytest.raises(Exception, match="relation"):
            await adapter.fetch_all("SELECT * FROM nonexistent")
    
    @pytest.mark.asyncio
    async def test_timeout_error_raised(self, adapter):
        """Timeout error should be raised."""
        from pynext_go.errors import BridgeTimeoutError
        adapter._bridge.execute.side_effect = BridgeTimeoutError()
        
        with pytest.raises(TimeoutError):
            await adapter.execute("SELECT pg_sleep(100)")


class TestGoAdapterCreateTableIntegration:
    """Tests for table creation."""
    
    @pytest.fixture
    def adapter(self):
        """Create adapter with mock bridge."""
        adapter = GoPostgresAdapter("postgresql://localhost/test")
        adapter._connected = True
        adapter._bridge = Mock()
        adapter._bridge.execute.return_value = Mock(success=True, rows_affected=0)
        return adapter
    
    @pytest.mark.asyncio
    async def test_create_simple_table(self, adapter):
        """Create simple table."""
        from pynext.db.fields import FieldInfo, SQLType
        
        fields = {
            "id": FieldInfo("id", int, SQLType.INTEGER),
            "name": FieldInfo("name", str, SQLType.TEXT),
        }
        
        await adapter.create_table("test_table", fields)
        
        call_args = adapter._bridge.execute.call_args
        sql = call_args[0][0]
        assert "CREATE TABLE IF NOT EXISTS" in sql
        assert '"test_table"' in sql
    
    @pytest.mark.asyncio
    async def test_drop_table(self, adapter):
        """Drop table."""
        await adapter.drop_table("test_table")
        
        call_args = adapter._bridge.execute.call_args
        sql = call_args[0][0]
        assert "DROP TABLE IF EXISTS" in sql
        assert '"test_table"' in sql

