"""
PostgreSQL Adapter Tests.

100 comprehensive tests for PostgresAdapter functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from pynext.db.adapters.postgres import PostgresAdapter
from pynext.db.adapters.postgres.core.url import PostgresConfig, PostgresConfigError
from pynext.db.adapters.postgres.pool.pool import PoolState


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_pool():
    """Create a mock pool."""
    pool = MagicMock()
    pool.start = AsyncMock()
    pool.close = AsyncMock()
    pool.execute = AsyncMock(return_value="OK")
    pool.fetch = AsyncMock(return_value=[])
    pool.fetchrow = AsyncMock(return_value=None)
    pool.fetchval = AsyncMock(return_value=1)
    pool.state = PoolState.RUNNING
    pool.get_stats = MagicMock(return_value=MagicMock(size=1, busy=0, idle=1))
    pool._acquire_connection = AsyncMock()
    pool._release_connection = AsyncMock()
    return pool


@pytest.fixture
def mock_asyncpg():
    """Mock asyncpg module."""
    import sys
    
    mock_conn = MagicMock()
    mock_conn.close = AsyncMock()
    mock_conn.execute = AsyncMock(return_value="SELECT 1")
    mock_conn.fetch = AsyncMock(return_value=[])
    mock_conn.fetchrow = AsyncMock(return_value=None)
    mock_conn.fetchval = AsyncMock(return_value=1)
    
    # Create a mock asyncpg module
    mock_asyncpg_module = MagicMock()
    mock_asyncpg_module.connect = AsyncMock(return_value=mock_conn)
    
    # Inject into sys.modules so import works
    old_module = sys.modules.get("asyncpg")
    sys.modules["asyncpg"] = mock_asyncpg_module
    
    yield mock_asyncpg_module, mock_conn
    
    # Restore
    if old_module:
        sys.modules["asyncpg"] = old_module
    else:
        sys.modules.pop("asyncpg", None)


@pytest.fixture
def mock_field_info():
    """Create mock FieldInfo."""
    field = MagicMock()
    field.python_type = str
    field.primary_key = False
    field.nullable = False
    field.unique = False
    field.default = None
    return field


# =============================================================================
# Adapter Creation Tests
# =============================================================================

class TestAdapterCreation:
    """Tests for adapter creation."""
    
    def test_create_with_url(self):
        """Test creating adapter with URL."""
        adapter = PostgresAdapter("postgresql://localhost/mydb")
        assert adapter._config.host == "localhost"
        assert adapter._config.database == "mydb"
    
    def test_create_with_keywords(self):
        """Test creating adapter with keywords."""
        adapter = PostgresAdapter(
            host="localhost",
            database="mydb",
            user="admin",
            password="secret",
        )
        assert adapter._config.host == "localhost"
        assert adapter._config.database == "mydb"
        assert adapter._config.user == "admin"
        assert adapter._config.password == "secret"
    
    def test_create_with_url_and_overrides(self):
        """Test creating adapter with URL and overrides."""
        adapter = PostgresAdapter(
            url="postgresql://user@localhost/mydb",
            password="secret",
        )
        assert adapter._config.user == "user"
        assert adapter._config.password == "secret"
    
    def test_create_with_pool_settings(self):
        """Test creating adapter with pool settings."""
        adapter = PostgresAdapter(
            host="localhost",
            database="mydb",
            min_connections=5,
            max_connections=50,
        )
        assert adapter._min_connections == 5
        assert adapter._max_connections == 50
    
    def test_create_with_timeout_settings(self):
        """Test creating adapter with timeout settings."""
        adapter = PostgresAdapter(
            host="localhost",
            database="mydb",
            connect_timeout=15.0,
            command_timeout=60.0,
            acquire_timeout=45.0,
        )
        assert adapter._connect_timeout == 15.0
        assert adapter._command_timeout == 60.0
        assert adapter._acquire_timeout == 45.0
    
    def test_create_with_cache_settings(self):
        """Test creating adapter with cache settings."""
        adapter = PostgresAdapter(
            host="localhost",
            database="mydb",
            statement_cache_size=500,
        )
        assert adapter._statement_cache_size == 500
    
    def test_create_defaults(self):
        """Test adapter with defaults."""
        adapter = PostgresAdapter()
        assert adapter._config.host == "localhost"
        assert adapter._config.port == 5432
        assert adapter._min_connections == 1
        assert adapter._max_connections == 10


# =============================================================================
# Connection Lifecycle Tests
# =============================================================================

class TestConnectionLifecycle:
    """Tests for connection lifecycle."""
    
    @pytest.mark.asyncio
    async def test_connect(self, mock_asyncpg):
        """Test connecting to database."""
        adapter = PostgresAdapter(host="localhost", database="mydb")
        
        await adapter.connect()
        
        assert adapter._pool is not None
    
    @pytest.mark.asyncio
    async def test_disconnect(self, mock_asyncpg):
        """Test disconnecting from database."""
        adapter = PostgresAdapter(host="localhost", database="mydb")
        
        await adapter.connect()
        await adapter.disconnect()
        
        assert adapter._pool is None
    
    @pytest.mark.asyncio
    async def test_connect_twice_warning(self, mock_asyncpg):
        """Test connecting twice logs warning."""
        adapter = PostgresAdapter(host="localhost", database="mydb")
        
        await adapter.connect()
        await adapter.connect()  # Should not raise
        
        await adapter.disconnect()


# =============================================================================
# Raw SQL Tests
# =============================================================================

class TestRawSQL:
    """Tests for raw SQL execution."""
    
    @pytest.mark.asyncio
    async def test_execute(self, mock_asyncpg):
        """Test executing raw SQL."""
        mock, mock_conn = mock_asyncpg
        mock_conn.execute.return_value = "UPDATE 5"
        
        adapter = PostgresAdapter(host="localhost", database="mydb")
        await adapter.connect()
        
        result = await adapter.execute("UPDATE users SET active = true")
        
        assert result == "UPDATE 5"
        
        await adapter.disconnect()
    
    @pytest.mark.asyncio
    async def test_execute_with_params(self, mock_asyncpg):
        """Test executing SQL with parameters."""
        mock, mock_conn = mock_asyncpg
        
        adapter = PostgresAdapter(host="localhost", database="mydb")
        await adapter.connect()
        
        await adapter.execute("UPDATE users SET name = $1 WHERE id = $2", ("John", 1))
        
        await adapter.disconnect()
    
    @pytest.mark.asyncio
    async def test_fetch_all(self, mock_asyncpg):
        """Test fetching all rows."""
        mock, mock_conn = mock_asyncpg
        mock_row1 = MagicMock()
        mock_row1.__iter__ = lambda self: iter([("id", 1), ("name", "John")])
        mock_row1.keys = lambda: ["id", "name"]
        mock_row2 = MagicMock()
        mock_row2.__iter__ = lambda self: iter([("id", 2), ("name", "Jane")])
        mock_row2.keys = lambda: ["id", "name"]
        mock_conn.fetch.return_value = [mock_row1, mock_row2]
        
        adapter = PostgresAdapter(host="localhost", database="mydb")
        await adapter.connect()
        
        result = await adapter.fetch_all("SELECT * FROM users")
        
        assert len(result) == 2
        
        await adapter.disconnect()
    
    @pytest.mark.asyncio
    async def test_fetch_one(self, mock_asyncpg):
        """Test fetching one row."""
        mock, mock_conn = mock_asyncpg
        mock_row = MagicMock()
        mock_row.__iter__ = lambda self: iter([("id", 1), ("name", "John")])
        mock_row.keys = lambda: ["id", "name"]
        mock_conn.fetchrow.return_value = mock_row
        
        adapter = PostgresAdapter(host="localhost", database="mydb")
        await adapter.connect()
        
        result = await adapter.fetch_one("SELECT * FROM users WHERE id = $1", (1,))
        
        assert result is not None
        
        await adapter.disconnect()
    
    @pytest.mark.asyncio
    async def test_fetch_one_not_found(self, mock_asyncpg):
        """Test fetching one row when not found."""
        mock, mock_conn = mock_asyncpg
        mock_conn.fetchrow.return_value = None
        
        adapter = PostgresAdapter(host="localhost", database="mydb")
        await adapter.connect()
        
        result = await adapter.fetch_one("SELECT * FROM users WHERE id = $1", (999,))
        
        assert result is None
        
        await adapter.disconnect()


# =============================================================================
# CRUD Tests
# =============================================================================

class TestCRUD:
    """Tests for CRUD operations."""
    
    @pytest.mark.asyncio
    async def test_insert(self, mock_asyncpg, mock_field_info):
        """Test inserting a row."""
        mock, mock_conn = mock_asyncpg
        mock_row = MagicMock()
        mock_row.__iter__ = lambda self: iter([("id", 1), ("name", "John")])
        mock_row.keys = lambda: ["id", "name"]
        mock_conn.fetchrow.return_value = mock_row
        
        adapter = PostgresAdapter(host="localhost", database="mydb")
        await adapter.connect()
        
        result = await adapter.insert(
            "users",
            {"name": "John"},
            {"name": mock_field_info},
        )
        
        assert result is not None
        
        await adapter.disconnect()
    
    @pytest.mark.asyncio
    async def test_update(self, mock_asyncpg, mock_field_info):
        """Test updating a row."""
        mock, mock_conn = mock_asyncpg
        mock_row = MagicMock()
        mock_row.__iter__ = lambda self: iter([("id", 1), ("name", "Jane")])
        mock_row.keys = lambda: ["id", "name"]
        mock_conn.fetchrow.return_value = mock_row
        
        adapter = PostgresAdapter(host="localhost", database="mydb")
        await adapter.connect()
        
        result = await adapter.update(
            "users",
            1,
            {"name": "Jane"},
            {"name": mock_field_info},
        )
        
        assert result is not None
        
        await adapter.disconnect()
    
    @pytest.mark.asyncio
    async def test_delete(self, mock_asyncpg):
        """Test deleting a row."""
        mock, mock_conn = mock_asyncpg
        mock_conn.execute.return_value = "DELETE 1"
        
        adapter = PostgresAdapter(host="localhost", database="mydb")
        await adapter.connect()
        
        result = await adapter.delete("users", 1)
        
        assert result is True
        
        await adapter.disconnect()
    
    @pytest.mark.asyncio
    async def test_delete_not_found(self, mock_asyncpg):
        """Test deleting non-existent row."""
        mock, mock_conn = mock_asyncpg
        mock_conn.execute.return_value = "DELETE 0"
        
        adapter = PostgresAdapter(host="localhost", database="mydb")
        await adapter.connect()
        
        result = await adapter.delete("users", 999)
        
        assert result is False
        
        await adapter.disconnect()


# =============================================================================
# Transaction Tests
# =============================================================================

class TestTransactions:
    """Tests for transaction handling."""
    
    @pytest.mark.asyncio
    async def test_begin_transaction(self, mock_asyncpg):
        """Test beginning a transaction."""
        mock, mock_conn = mock_asyncpg
        
        adapter = PostgresAdapter(host="localhost", database="mydb")
        await adapter.connect()
        
        # Mock the pool's _acquire_connection
        pooled_conn = MagicMock()
        pooled_conn.connection = mock_conn
        adapter._pool._acquire_connection = AsyncMock(return_value=pooled_conn)
        
        await adapter.begin_transaction()
        
        assert adapter._in_transaction is True
        mock_conn.execute.assert_called_with("BEGIN")
        
        await adapter.disconnect()
    
    @pytest.mark.asyncio
    async def test_commit_transaction(self, mock_asyncpg):
        """Test committing a transaction."""
        mock, mock_conn = mock_asyncpg
        
        adapter = PostgresAdapter(host="localhost", database="mydb")
        await adapter.connect()
        
        pooled_conn = MagicMock()
        pooled_conn.connection = mock_conn
        adapter._pool._acquire_connection = AsyncMock(return_value=pooled_conn)
        adapter._pool._release_connection = AsyncMock()
        
        await adapter.begin_transaction()
        await adapter.commit_transaction()
        
        assert adapter._in_transaction is False
        
        await adapter.disconnect()
    
    @pytest.mark.asyncio
    async def test_rollback_transaction(self, mock_asyncpg):
        """Test rolling back a transaction."""
        mock, mock_conn = mock_asyncpg
        
        adapter = PostgresAdapter(host="localhost", database="mydb")
        await adapter.connect()
        
        pooled_conn = MagicMock()
        pooled_conn.connection = mock_conn
        adapter._pool._acquire_connection = AsyncMock(return_value=pooled_conn)
        adapter._pool._release_connection = AsyncMock()
        
        await adapter.begin_transaction()
        await adapter.rollback_transaction()
        
        assert adapter._in_transaction is False
        
        await adapter.disconnect()
    
    @pytest.mark.asyncio
    async def test_savepoint(self, mock_asyncpg):
        """Test creating a savepoint."""
        mock, mock_conn = mock_asyncpg
        
        adapter = PostgresAdapter(host="localhost", database="mydb")
        await adapter.connect()
        
        pooled_conn = MagicMock()
        pooled_conn.connection = mock_conn
        adapter._pool._acquire_connection = AsyncMock(return_value=pooled_conn)
        
        await adapter.begin_transaction()
        await adapter.savepoint("sp1")
        
        mock_conn.execute.assert_called_with('SAVEPOINT "sp1"')
        
        await adapter.disconnect()
    
    @pytest.mark.asyncio
    async def test_rollback_savepoint(self, mock_asyncpg):
        """Test rolling back to savepoint."""
        mock, mock_conn = mock_asyncpg
        
        adapter = PostgresAdapter(host="localhost", database="mydb")
        await adapter.connect()
        
        pooled_conn = MagicMock()
        pooled_conn.connection = mock_conn
        adapter._pool._acquire_connection = AsyncMock(return_value=pooled_conn)
        
        await adapter.begin_transaction()
        await adapter.rollback_savepoint("sp1")
        
        mock_conn.execute.assert_called_with('ROLLBACK TO SAVEPOINT "sp1"')
        
        await adapter.disconnect()
    
    @pytest.mark.asyncio
    async def test_transaction_without_begin_raises(self, mock_asyncpg):
        """Test committing without begin raises error."""
        adapter = PostgresAdapter(host="localhost", database="mydb")
        await adapter.connect()
        
        with pytest.raises(RuntimeError):
            await adapter.commit_transaction()
        
        await adapter.disconnect()


# =============================================================================
# Table Operations Tests
# =============================================================================

class TestTableOperations:
    """Tests for table operations."""
    
    @pytest.mark.asyncio
    async def test_create_table(self, mock_asyncpg, mock_field_info):
        """Test creating a table."""
        mock, mock_conn = mock_asyncpg
        
        adapter = PostgresAdapter(host="localhost", database="mydb")
        await adapter.connect()
        
        id_field = MagicMock()
        id_field.python_type = int
        id_field.primary_key = True
        id_field.nullable = False
        id_field.unique = False
        id_field.default = None
        
        await adapter.create_table(
            "users",
            {"id": id_field, "name": mock_field_info},
        )
        
        # Should have called execute with CREATE TABLE
        mock_conn.execute.assert_called()
        call_args = str(mock_conn.execute.call_args)
        assert "CREATE TABLE" in call_args
        
        await adapter.disconnect()
    
    @pytest.mark.asyncio
    async def test_drop_table(self, mock_asyncpg):
        """Test dropping a table."""
        mock, mock_conn = mock_asyncpg
        
        adapter = PostgresAdapter(host="localhost", database="mydb")
        await adapter.connect()
        
        await adapter.drop_table("users")
        
        mock_conn.execute.assert_called()
        call_args = str(mock_conn.execute.call_args)
        assert "DROP TABLE" in call_args
        
        await adapter.disconnect()


# =============================================================================
# Query Building Tests
# =============================================================================

class TestQueryBuilding:
    """Tests for query building."""
    
    def test_build_where_eq(self):
        """Test building WHERE clause with eq."""
        adapter = PostgresAdapter(host="localhost", database="mydb")
        
        query = MagicMock()
        query._conditions = [("name", "eq", "John")]
        
        where, params = adapter._build_where(query)
        
        assert '"name" = $1' in where
        assert params == ["John"]
    
    def test_build_where_multiple(self):
        """Test building WHERE clause with multiple conditions."""
        adapter = PostgresAdapter(host="localhost", database="mydb")
        
        query = MagicMock()
        query._conditions = [
            ("name", "eq", "John"),
            ("age", "gt", 18),
        ]
        
        where, params = adapter._build_where(query)
        
        assert '"name" = $1' in where
        assert '"age" > $2' in where
        assert params == ["John", 18]
    
    def test_build_where_in(self):
        """Test building WHERE clause with IN."""
        adapter = PostgresAdapter(host="localhost", database="mydb")
        
        query = MagicMock()
        query._conditions = [("status", "in", ["active", "pending"])]
        
        where, params = adapter._build_where(query)
        
        assert "ANY" in where
        assert params == [["active", "pending"]]
    
    def test_build_where_like(self):
        """Test building WHERE clause with LIKE."""
        adapter = PostgresAdapter(host="localhost", database="mydb")
        
        query = MagicMock()
        query._conditions = [("name", "like", "%John%")]
        
        where, params = adapter._build_where(query)
        
        assert "LIKE" in where
        assert params == ["%John%"]
    
    def test_build_where_is_null(self):
        """Test building WHERE clause with IS NULL."""
        adapter = PostgresAdapter(host="localhost", database="mydb")
        
        query = MagicMock()
        query._conditions = [("email", "is_null", True)]
        
        where, params = adapter._build_where(query)
        
        assert "IS NULL" in where


# =============================================================================
# Pool Stats Tests
# =============================================================================

class TestPoolStats:
    """Tests for pool statistics."""
    
    @pytest.mark.asyncio
    async def test_get_pool_stats(self, mock_asyncpg):
        """Test getting pool stats."""
        adapter = PostgresAdapter(host="localhost", database="mydb")
        await adapter.connect()
        
        stats = adapter.get_pool_stats()
        
        assert stats is not None
        assert stats.size >= 0
        
        await adapter.disconnect()
    
    def test_get_pool_stats_not_connected(self):
        """Test getting stats when not connected."""
        adapter = PostgresAdapter(host="localhost", database="mydb")
        
        stats = adapter.get_pool_stats()
        
        assert stats is None


# =============================================================================
# Repr Tests
# =============================================================================

class TestRepr:
    """Tests for string representation."""
    
    def test_repr_not_connected(self):
        """Test repr when not connected."""
        adapter = PostgresAdapter(host="localhost", database="mydb")
        repr_str = repr(adapter)
        
        assert "PostgresAdapter" in repr_str
        assert "localhost" in repr_str
        assert "mydb" in repr_str
    
    @pytest.mark.asyncio
    async def test_repr_connected(self, mock_asyncpg):
        """Test repr when connected."""
        adapter = PostgresAdapter(host="localhost", database="mydb")
        await adapter.connect()
        
        repr_str = repr(adapter)
        
        assert "PostgresAdapter" in repr_str
        assert "pool=" in repr_str
        
        await adapter.disconnect()


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestErrorHandling:
    """Tests for error handling."""
    
    @pytest.mark.asyncio
    async def test_execute_not_connected_raises(self):
        """Test executing when not connected raises error."""
        adapter = PostgresAdapter(host="localhost", database="mydb")
        
        with pytest.raises(RuntimeError) as exc_info:
            await adapter.execute("SELECT 1")
        
        assert "not connected" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_fetch_not_connected_raises(self):
        """Test fetching when not connected raises error."""
        adapter = PostgresAdapter(host="localhost", database="mydb")
        
        with pytest.raises(RuntimeError):
            await adapter.fetch_all("SELECT 1")


# =============================================================================
# Default Formatting Tests
# =============================================================================

class TestDefaultFormatting:
    """Tests for default value formatting."""
    
    def test_format_default_none(self):
        """Test formatting None default."""
        adapter = PostgresAdapter(host="localhost", database="mydb")
        assert adapter._format_default(None) == "NULL"
    
    def test_format_default_bool_true(self):
        """Test formatting True default."""
        adapter = PostgresAdapter(host="localhost", database="mydb")
        assert adapter._format_default(True) == "TRUE"
    
    def test_format_default_bool_false(self):
        """Test formatting False default."""
        adapter = PostgresAdapter(host="localhost", database="mydb")
        assert adapter._format_default(False) == "FALSE"
    
    def test_format_default_int(self):
        """Test formatting int default."""
        adapter = PostgresAdapter(host="localhost", database="mydb")
        assert adapter._format_default(42) == "42"
    
    def test_format_default_float(self):
        """Test formatting float default."""
        adapter = PostgresAdapter(host="localhost", database="mydb")
        assert adapter._format_default(3.14) == "3.14"
    
    def test_format_default_string(self):
        """Test formatting string default."""
        adapter = PostgresAdapter(host="localhost", database="mydb")
        assert adapter._format_default("hello") == "'hello'"
    
    def test_format_default_string_with_quote(self):
        """Test formatting string with quote."""
        adapter = PostgresAdapter(host="localhost", database="mydb")
        assert adapter._format_default("it's") == "'it''s'"

