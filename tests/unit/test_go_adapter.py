"""
Unit tests for Go Bridge PostgreSQL adapter.

Tests GoPostgresAdapter class and adapter auto-selection.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from pynext.db.adapters.go_adapter import (
    GoPostgresAdapter,
    is_go_available,
)


class TestIsGoAvailable:
    """is_go_available tests."""
    
    def test_returns_boolean(self):
        """is_go_available should return boolean."""
        result = is_go_available()
        assert isinstance(result, bool)


class TestGoPostgresAdapterInit:
    """GoPostgresAdapter initialization tests."""
    
    def test_create_adapter(self):
        """Create adapter with DSN."""
        adapter = GoPostgresAdapter("postgresql://localhost/test")
        assert adapter._dsn == "postgresql://localhost/test"
        assert adapter._connected is False
    
    def test_create_with_pool_settings(self):
        """Create adapter with custom pool settings."""
        adapter = GoPostgresAdapter(
            "postgresql://localhost/test",
            pool_min_size=5,
            pool_max_size=20,
        )
        assert adapter._pool_min_size == 5
        assert adapter._pool_max_size == 20
    
    def test_create_with_timeout(self):
        """Create adapter with custom timeout."""
        adapter = GoPostgresAdapter(
            "postgresql://localhost/test",
            query_timeout=5000,
        )
        assert adapter._query_timeout == 5000
    
    def test_create_with_require_go(self):
        """Create adapter with require_go flag."""
        adapter = GoPostgresAdapter(
            "postgresql://localhost/test",
            require_go=True,
        )
        assert adapter._require_go is True
    
    def test_default_require_go_false(self):
        """require_go should default to False."""
        adapter = GoPostgresAdapter("postgresql://localhost/test")
        assert adapter._require_go is False


class TestGoPostgresAdapterProperties:
    """GoPostgresAdapter property tests."""
    
    def test_is_go_powered_false_before_connect(self):
        """is_go_powered should be False before connect."""
        adapter = GoPostgresAdapter("postgresql://localhost/test")
        assert adapter.is_go_powered is False


class TestGoPostgresAdapterConnect:
    """GoPostgresAdapter connect tests."""
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(is_go_available(), reason="Tests Go-not-available path")
    async def test_connect_fallback_warning(self):
        """connect should set connected flag in fallback mode."""
        adapter = GoPostgresAdapter("postgresql://localhost/test")
        
        # In fallback mode without asyncpg, should just set connected
        await adapter.connect()
        assert adapter._connected is True
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(is_go_available(), reason="Tests Go-not-available path")
    async def test_connect_require_go_raises(self):
        """connect with require_go should raise when Go unavailable."""
        adapter = GoPostgresAdapter(
            "postgresql://localhost/test",
            require_go=True,
        )
        
        from pynext_go.errors import GoNotAvailableError
        with pytest.raises(GoNotAvailableError):
            await adapter.connect()
    
    @pytest.mark.asyncio
    async def test_connect_twice_noop(self):
        """Connecting twice should be a no-op."""
        adapter = GoPostgresAdapter("postgresql://localhost/test")
        adapter._connected = True  # Pretend already connected
        
        # Should not raise or do anything
        await adapter.connect()
        assert adapter._connected is True


class TestGoPostgresAdapterDisconnect:
    """GoPostgresAdapter disconnect tests."""
    
    @pytest.mark.asyncio
    async def test_disconnect_unconnected(self):
        """Disconnecting when not connected should be safe."""
        adapter = GoPostgresAdapter("postgresql://localhost/test")
        await adapter.disconnect()
        assert adapter._connected is False
    
    @pytest.mark.asyncio
    async def test_disconnect_clears_bridge(self):
        """Disconnect should clear bridge reference."""
        adapter = GoPostgresAdapter("postgresql://localhost/test")
        adapter._bridge = Mock()  # Fake bridge
        adapter._connected = True
        
        await adapter.disconnect()
        
        assert adapter._bridge is None
        assert adapter._connected is False


class TestGoPostgresAdapterCheckConnected:
    """_check_connected tests."""
    
    def test_check_connected_raises_when_not(self):
        """_check_connected should raise when not connected."""
        adapter = GoPostgresAdapter("postgresql://localhost/test")
        
        with pytest.raises(Exception, match="Not connected"):
            adapter._check_connected()
    
    def test_check_connected_passes_when_connected(self):
        """_check_connected should pass when connected."""
        adapter = GoPostgresAdapter("postgresql://localhost/test")
        adapter._connected = True
        
        # Should not raise
        adapter._check_connected()


class TestGoPostgresAdapterBuildSelect:
    """_build_select tests."""
    
    def test_build_simple_select(self):
        """Build simple SELECT without filters."""
        adapter = GoPostgresAdapter("postgresql://localhost/test")
        
        query = Mock()
        query._filters = []
        query._order_by = []
        query._limit = None
        query._offset = None
        
        sql, params = adapter._build_select("users", query)
        
        assert 'SELECT * FROM "users"' in sql
        assert params == ()
    
    def test_build_select_with_filters(self):
        """Build SELECT with filters."""
        adapter = GoPostgresAdapter("postgresql://localhost/test")
        
        query = Mock()
        query._filters = [("age", ">=", 18), ("active", "=", True)]
        query._order_by = []
        query._limit = None
        query._offset = None
        
        sql, params = adapter._build_select("users", query)
        
        assert "WHERE" in sql
        assert '"age" >= $1' in sql
        assert '"active" = $2' in sql
        assert params == (18, True)
    
    def test_build_select_with_order(self):
        """Build SELECT with ORDER BY."""
        adapter = GoPostgresAdapter("postgresql://localhost/test")
        
        query = Mock()
        query._filters = []
        query._order_by = [("created_at", True), ("name", False)]
        query._limit = None
        query._offset = None
        
        sql, params = adapter._build_select("users", query)
        
        assert "ORDER BY" in sql
        assert '"created_at" DESC' in sql
        assert '"name" ASC' in sql
    
    def test_build_select_with_limit(self):
        """Build SELECT with LIMIT."""
        adapter = GoPostgresAdapter("postgresql://localhost/test")
        
        query = Mock()
        query._filters = []
        query._order_by = []
        query._limit = 10
        query._offset = None
        
        sql, params = adapter._build_select("users", query)
        
        assert "LIMIT 10" in sql
    
    def test_build_select_with_offset(self):
        """Build SELECT with OFFSET."""
        adapter = GoPostgresAdapter("postgresql://localhost/test")
        
        query = Mock()
        query._filters = []
        query._order_by = []
        query._limit = None
        query._offset = 20
        
        sql, params = adapter._build_select("users", query)
        
        assert "OFFSET 20" in sql
    
    def test_build_count(self):
        """Build COUNT query."""
        adapter = GoPostgresAdapter("postgresql://localhost/test")
        
        query = Mock()
        query._filters = []
        query._order_by = []
        query._limit = None
        query._offset = None
        
        sql, params = adapter._build_select("users", query, count=True)
        
        assert "SELECT COUNT(*) as count" in sql
        assert "ORDER BY" not in sql  # No ordering for count
    
    def test_build_select_with_explicit_limit(self):
        """Build SELECT with explicit limit parameter."""
        adapter = GoPostgresAdapter("postgresql://localhost/test")
        
        query = Mock()
        query._filters = []
        query._order_by = []
        query._limit = 100  # Query limit
        query._offset = None
        
        sql, params = adapter._build_select("users", query, limit=1)
        
        # Explicit limit should take precedence
        assert "LIMIT 1" in sql


class TestGoPostgresAdapterFieldToSqlType:
    """_field_to_sql_type tests."""
    
    def test_integer_type(self):
        """Map integer field to SQL type."""
        adapter = GoPostgresAdapter("postgresql://localhost/test")
        
        # Create a simple mock field
        from unittest.mock import Mock
        field = Mock()
        field.name = "count"
        from pynext.db.fields import SQLType
        field.sql_type = SQLType.INTEGER
        
        sql_type = adapter._field_to_sql_type(field)
        assert sql_type == "INTEGER"
    
    def test_text_type(self):
        """Map text field to SQL type."""
        adapter = GoPostgresAdapter("postgresql://localhost/test")
        
        from unittest.mock import Mock
        field = Mock()
        field.name = "name"
        from pynext.db.fields import SQLType
        field.sql_type = SQLType.TEXT
        
        sql_type = adapter._field_to_sql_type(field)
        assert sql_type == "TEXT"
    
    def test_varchar_with_length(self):
        """Map varchar field with max_length."""
        adapter = GoPostgresAdapter("postgresql://localhost/test")
        
        from unittest.mock import Mock
        field = Mock()
        field.name = "code"
        from pynext.db.fields import SQLType
        field.sql_type = SQLType.VARCHAR
        field.max_length = 50
        
        sql_type = adapter._field_to_sql_type(field)
        assert sql_type == "VARCHAR(50)"
    
    def test_id_field_serial(self):
        """id field should be SERIAL PRIMARY KEY."""
        adapter = GoPostgresAdapter("postgresql://localhost/test")
        
        from unittest.mock import Mock
        field = Mock()
        field.name = "id"
        from pynext.db.fields import SQLType
        field.sql_type = SQLType.INTEGER
        
        sql_type = adapter._field_to_sql_type(field)
        assert sql_type == "SERIAL PRIMARY KEY"


class TestGoPostgresAdapterTransaction:
    """Transaction method tests."""
    
    @pytest.mark.asyncio
    async def test_begin_transaction_sets_flag(self):
        """begin_transaction should set in_transaction flag."""
        adapter = GoPostgresAdapter("postgresql://localhost/test")
        adapter._connected = True
        adapter._bridge = Mock()
        adapter._bridge.execute = Mock(return_value=Mock(success=True, rows_affected=0))
        
        await adapter.begin_transaction()
        assert adapter._in_transaction is True
    
    @pytest.mark.asyncio
    async def test_begin_transaction_twice_raises(self):
        """begin_transaction twice should raise."""
        adapter = GoPostgresAdapter("postgresql://localhost/test")
        adapter._connected = True
        adapter._in_transaction = True
        
        with pytest.raises(Exception, match="Already in transaction"):
            await adapter.begin_transaction()
    
    @pytest.mark.asyncio
    async def test_commit_clears_flag(self):
        """commit_transaction should clear in_transaction flag."""
        adapter = GoPostgresAdapter("postgresql://localhost/test")
        adapter._connected = True
        adapter._in_transaction = True
        adapter._bridge = Mock()
        adapter._bridge.execute = Mock(return_value=Mock(success=True, rows_affected=0))
        
        await adapter.commit_transaction()
        assert adapter._in_transaction is False
    
    @pytest.mark.asyncio
    async def test_commit_without_transaction_raises(self):
        """commit_transaction without begin should raise."""
        adapter = GoPostgresAdapter("postgresql://localhost/test")
        adapter._connected = True
        adapter._in_transaction = False
        
        with pytest.raises(Exception, match="Not in transaction"):
            await adapter.commit_transaction()
    
    @pytest.mark.asyncio
    async def test_rollback_clears_flag(self):
        """rollback_transaction should clear in_transaction flag."""
        adapter = GoPostgresAdapter("postgresql://localhost/test")
        adapter._connected = True
        adapter._in_transaction = True
        adapter._bridge = Mock()
        adapter._bridge.execute = Mock(return_value=Mock(success=True, rows_affected=0))
        
        await adapter.rollback_transaction()
        assert adapter._in_transaction is False
    
    @pytest.mark.asyncio
    async def test_rollback_without_transaction_noop(self):
        """rollback_transaction without begin should be no-op."""
        adapter = GoPostgresAdapter("postgresql://localhost/test")
        adapter._connected = True
        adapter._in_transaction = False
        
        # Should not raise
        await adapter.rollback_transaction()


class TestGetBestAdapter:
    """get_best_adapter tests."""
    
    def test_function_exists(self):
        """get_best_adapter should be importable."""
        from pynext.db.adapters import get_best_adapter
        assert callable(get_best_adapter)
    
    @pytest.mark.skipif(is_go_available(), reason="Tests Go-not-available path")
    def test_get_best_adapter_require_go_raises(self):
        """get_best_adapter with require_go should raise when unavailable."""
        from pynext.db.adapters import get_best_adapter
        
        with pytest.raises(ImportError, match="Go bridge required"):
            get_best_adapter("postgresql://localhost/test", require_go=True)
    
    def test_get_best_adapter_prefer_go_false(self):
        """get_best_adapter with prefer_go=False should use asyncpg."""
        from pynext.db.adapters import get_best_adapter
        
        try:
            adapter = get_best_adapter(
                "postgresql://localhost/test",
                prefer_go=False,
            )
            # Should get PostgresAdapter, not GoPostgresAdapter
            assert not isinstance(adapter, GoPostgresAdapter)
        except ImportError:
            # asyncpg not available either
            pass


class TestGoPostgresAdapterCRUD:
    """CRUD operation tests (mocked)."""
    
    @pytest.fixture
    def connected_adapter(self):
        """Create connected adapter with mock bridge."""
        adapter = GoPostgresAdapter("postgresql://localhost/test")
        adapter._connected = True
        adapter._bridge = Mock()
        return adapter
    
    @pytest.mark.asyncio
    async def test_execute_returns_rows_affected(self, connected_adapter):
        """execute should return rows_affected."""
        adapter = connected_adapter
        adapter._bridge.execute.return_value = Mock(
            success=True,
            rows_affected=5,
        )
        
        result = await adapter.execute("DELETE FROM t WHERE x > 0")
        assert result == 5
    
    @pytest.mark.asyncio
    async def test_fetch_all_returns_dicts(self, connected_adapter):
        """fetch_all should return list of dicts."""
        adapter = connected_adapter
        adapter._bridge.execute.return_value = Mock(
            success=True,
            to_dicts=lambda: [{"id": 1}, {"id": 2}],
        )
        
        results = await adapter.fetch_all("SELECT * FROM t")
        assert len(results) == 2
        assert results[0]["id"] == 1
    
    @pytest.mark.asyncio
    async def test_fetch_one_returns_first(self, connected_adapter):
        """fetch_one should return first row."""
        adapter = connected_adapter
        adapter._bridge.execute.return_value = Mock(
            success=True,
            to_dicts=lambda: [{"id": 1}, {"id": 2}],
        )
        
        result = await adapter.fetch_one("SELECT * FROM t")
        assert result == {"id": 1}
    
    @pytest.mark.asyncio
    async def test_fetch_one_returns_none_empty(self, connected_adapter):
        """fetch_one should return None when empty."""
        adapter = connected_adapter
        adapter._bridge.execute.return_value = Mock(
            success=True,
            to_dicts=lambda: [],
        )
        
        result = await adapter.fetch_one("SELECT * FROM t WHERE 1=0")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_count_returns_int(self, connected_adapter):
        """count should return integer."""
        adapter = connected_adapter
        adapter._bridge.execute.return_value = Mock(
            success=True,
            to_dicts=lambda: [{"count": 42}],
        )
        
        query = Mock()
        query._filters = []
        query._order_by = []
        query._limit = None
        query._offset = None
        
        result = await adapter.count("users", query)
        assert result == 42
    
    @pytest.mark.asyncio
    async def test_exists_returns_bool(self, connected_adapter):
        """exists should return boolean."""
        adapter = connected_adapter
        adapter._bridge.execute.return_value = Mock(
            success=True,
            to_dicts=lambda: [{"count": 1}],
        )
        
        query = Mock()
        query._filters = []
        query._order_by = []
        query._limit = None
        query._offset = None
        
        result = await adapter.exists("users", query)
        assert result is True

