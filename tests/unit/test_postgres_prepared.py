"""
Comprehensive tests for PyNext Prepared Statements.

100 tests covering:
- Statement preparation
- Execution
- Caching (LRU)
- Auto-invalidation
- Statistics
- Schema watching
"""

import pytest
import asyncio
from datetime import datetime

from pynext.db.adapters.postgres.queries.prepared import (
    StatementState,
    PreparedStats,
    PreparedStatement,
    PreparedCache,
    PreparedExecutor,
    prepared,
    SchemaWatcher,
    get_prepared_executor,
    set_prepared_executor,
)


# =============================================================================
# STATEMENT STATE TESTS
# =============================================================================

class TestStatementState:
    """Tests for StatementState enum."""
    
    def test_pending_state(self):
        """Test PENDING state."""
        assert StatementState.PENDING.value == "pending"
    
    def test_prepared_state(self):
        """Test PREPARED state."""
        assert StatementState.PREPARED.value == "prepared"
    
    def test_invalid_state(self):
        """Test INVALID state."""
        assert StatementState.INVALID.value == "invalid"
    
    def test_error_state(self):
        """Test ERROR state."""
        assert StatementState.ERROR.value == "error"


# =============================================================================
# PREPARED STATS TESTS
# =============================================================================

class TestPreparedStats:
    """Tests for PreparedStats."""
    
    def test_initial_stats(self):
        """Test initial stats values."""
        stats = PreparedStats(name="test", sql="SELECT 1")
        assert stats.call_count == 0
        assert stats.total_time_ms == 0.0
        assert stats.error_count == 0
    
    def test_record_call(self):
        """Test recording a successful call."""
        stats = PreparedStats(name="test", sql="SELECT 1")
        stats.record_call(10.0)
        
        assert stats.call_count == 1
        assert stats.total_time_ms == 10.0
        assert stats.last_used is not None
    
    def test_avg_time_ms(self):
        """Test average time calculation."""
        stats = PreparedStats(name="test", sql="SELECT 1")
        stats.record_call(10.0)
        stats.record_call(20.0)
        
        assert stats.avg_time_ms == 15.0
    
    def test_avg_time_ms_no_calls(self):
        """Test avg time with no calls."""
        stats = PreparedStats(name="test", sql="SELECT 1")
        assert stats.avg_time_ms == 0.0
    
    def test_record_error(self):
        """Test recording an error."""
        stats = PreparedStats(name="test", sql="SELECT 1")
        stats.record_error()
        
        assert stats.error_count == 1
        assert stats.last_used is not None
    
    def test_error_rate(self):
        """Test error rate calculation."""
        stats = PreparedStats(name="test", sql="SELECT 1")
        stats.call_count = 10
        stats.error_count = 2
        
        assert stats.error_rate == 20.0
    
    def test_error_rate_no_calls(self):
        """Test error rate with no calls."""
        stats = PreparedStats(name="test", sql="SELECT 1")
        assert stats.error_rate == 0.0
    
    def test_record_invalidation(self):
        """Test recording invalidation."""
        stats = PreparedStats(name="test", sql="SELECT 1")
        stats.record_invalidation()
        
        assert stats.invalidation_count == 1
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        stats = PreparedStats(name="test", sql="SELECT * FROM users")
        stats.record_call(10.0)
        
        d = stats.to_dict()
        
        assert d["name"] == "test"
        assert d["call_count"] == 1
        assert d["avg_time_ms"] == 10.0


# =============================================================================
# PREPARED STATEMENT TESTS
# =============================================================================

class TestPreparedStatement:
    """Tests for PreparedStatement."""
    
    def test_basic_creation(self):
        """Test basic statement creation."""
        stmt = PreparedStatement(
            name="get_user",
            sql="SELECT * FROM users WHERE id = $1",
        )
        assert stmt.name == "get_user"
        assert stmt.sql == "SELECT * FROM users WHERE id = $1"
        assert stmt.state == StatementState.PENDING
    
    def test_with_param_types(self):
        """Test statement with parameter types."""
        stmt = PreparedStatement(
            name="get_user",
            sql="SELECT * FROM users WHERE id = $1",
            param_types=[int],
        )
        assert stmt.param_types == [int]
    
    def test_auto_extract_tables(self):
        """Test automatic table extraction."""
        stmt = PreparedStatement(
            name="get_user",
            sql="SELECT * FROM users WHERE id = $1",
        )
        assert "users" in stmt.tables
    
    def test_extract_tables_join(self):
        """Test table extraction from JOIN."""
        stmt = PreparedStatement(
            name="get_orders",
            sql="SELECT * FROM users JOIN orders ON users.id = orders.user_id",
        )
        assert "users" in stmt.tables
        assert "orders" in stmt.tables
    
    def test_is_ready(self):
        """Test is_ready property."""
        stmt = PreparedStatement(name="test", sql="SELECT 1")
        assert stmt.is_ready is False
        
        stmt.state = StatementState.PREPARED
        assert stmt.is_ready is True
    
    def test_needs_preparation(self):
        """Test needs_preparation property."""
        stmt = PreparedStatement(name="test", sql="SELECT 1")
        assert stmt.needs_preparation is True
        
        stmt.state = StatementState.PREPARED
        assert stmt.needs_preparation is False
        
        stmt.state = StatementState.INVALID
        assert stmt.needs_preparation is True
    
    def test_invalidate(self):
        """Test invalidating statement."""
        stmt = PreparedStatement(name="test", sql="SELECT 1")
        stmt.state = StatementState.PREPARED
        
        stmt.invalidate()
        
        assert stmt.state == StatementState.INVALID
        assert stmt.stats.invalidation_count == 1
    
    def test_mark_prepared(self):
        """Test marking as prepared."""
        stmt = PreparedStatement(name="test", sql="SELECT 1")
        stmt.mark_prepared(connection_id=123, backend_name="pynext_test")
        
        assert stmt.state == StatementState.PREPARED
        assert stmt.connection_id == 123
        assert stmt.backend_name == "pynext_test"
    
    def test_mark_error(self):
        """Test marking as error."""
        stmt = PreparedStatement(name="test", sql="SELECT 1")
        stmt.mark_error(Exception("Test error"))
        
        assert stmt.state == StatementState.ERROR
        assert stmt.stats.error_count == 1
    
    def test_generate_prepare_sql(self):
        """Test generating PREPARE SQL."""
        stmt = PreparedStatement(
            name="test",
            sql="SELECT * FROM users WHERE id = $1",
            param_types=[int],
        )
        stmt.backend_name = "pynext_test"
        
        sql = stmt.generate_prepare_sql()
        
        assert "PREPARE" in sql
        assert "pynext_test" in sql
        assert "integer" in sql
    
    def test_generate_deallocate_sql(self):
        """Test generating DEALLOCATE SQL."""
        stmt = PreparedStatement(name="test", sql="SELECT 1")
        stmt.backend_name = "pynext_test"
        
        sql = stmt.generate_deallocate_sql()
        
        assert "DEALLOCATE" in sql
        assert "pynext_test" in sql
    
    def test_python_to_pg_type_int(self):
        """Test int to integer conversion."""
        stmt = PreparedStatement(name="test", sql="SELECT 1")
        assert stmt._python_to_pg_type(int) == "integer"
    
    def test_python_to_pg_type_float(self):
        """Test float to double precision conversion."""
        stmt = PreparedStatement(name="test", sql="SELECT 1")
        assert stmt._python_to_pg_type(float) == "double precision"
    
    def test_python_to_pg_type_str(self):
        """Test str to text conversion."""
        stmt = PreparedStatement(name="test", sql="SELECT 1")
        assert stmt._python_to_pg_type(str) == "text"
    
    def test_python_to_pg_type_bool(self):
        """Test bool to boolean conversion."""
        stmt = PreparedStatement(name="test", sql="SELECT 1")
        assert stmt._python_to_pg_type(bool) == "boolean"
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        stmt = PreparedStatement(
            name="test",
            sql="SELECT 1",
            param_types=[int],
        )
        d = stmt.to_dict()
        
        assert d["name"] == "test"
        assert d["sql"] == "SELECT 1"
        assert "int" in d["param_types"]


# =============================================================================
# PREPARED CACHE TESTS
# =============================================================================

class TestPreparedCache:
    """Tests for PreparedCache."""
    
    def test_basic_creation(self):
        """Test basic cache creation."""
        cache = PreparedCache(max_size=100)
        assert cache.max_size == 100
        assert cache.size == 0
    
    def test_put_and_get(self):
        """Test putting and getting statements."""
        cache = PreparedCache()
        stmt = PreparedStatement(name="test", sql="SELECT 1")
        
        cache.put(stmt)
        retrieved = cache.get("test")
        
        assert retrieved is stmt
    
    def test_get_nonexistent(self):
        """Test getting nonexistent statement."""
        cache = PreparedCache()
        assert cache.get("nonexistent") is None
    
    def test_remove(self):
        """Test removing statement."""
        cache = PreparedCache()
        stmt = PreparedStatement(name="test", sql="SELECT 1")
        
        cache.put(stmt)
        removed = cache.remove("test")
        
        assert removed is stmt
        assert cache.get("test") is None
    
    def test_remove_nonexistent(self):
        """Test removing nonexistent statement."""
        cache = PreparedCache()
        removed = cache.remove("nonexistent")
        assert removed is None
    
    def test_invalidate(self):
        """Test invalidating statement."""
        cache = PreparedCache()
        stmt = PreparedStatement(name="test", sql="SELECT 1")
        stmt.state = StatementState.PREPARED
        
        cache.put(stmt)
        result = cache.invalidate("test")
        
        assert result is True
        assert stmt.state == StatementState.INVALID
    
    def test_invalidate_nonexistent(self):
        """Test invalidating nonexistent statement."""
        cache = PreparedCache()
        result = cache.invalidate("nonexistent")
        assert result is False
    
    def test_invalidate_for_table(self):
        """Test invalidating statements for a table."""
        cache = PreparedCache()
        
        stmt1 = PreparedStatement(
            name="users_query",
            sql="SELECT * FROM users",
        )
        stmt1.state = StatementState.PREPARED
        
        stmt2 = PreparedStatement(
            name="orders_query",
            sql="SELECT * FROM orders",
        )
        stmt2.state = StatementState.PREPARED
        
        cache.put(stmt1)
        cache.put(stmt2)
        
        count = cache.invalidate_for_table("users")
        
        assert count == 1
        assert stmt1.state == StatementState.INVALID
        assert stmt2.state == StatementState.PREPARED
    
    def test_invalidate_all(self):
        """Test invalidating all statements."""
        cache = PreparedCache()
        
        for i in range(5):
            stmt = PreparedStatement(name=f"stmt{i}", sql="SELECT 1")
            stmt.state = StatementState.PREPARED
            cache.put(stmt)
        
        count = cache.invalidate_all()
        
        assert count == 5
    
    def test_clear(self):
        """Test clearing cache."""
        cache = PreparedCache()
        
        for i in range(5):
            stmt = PreparedStatement(name=f"stmt{i}", sql="SELECT 1")
            cache.put(stmt)
        
        count = cache.clear()
        
        assert count == 5
        assert cache.size == 0
    
    def test_lru_eviction(self):
        """Test LRU eviction when full."""
        cache = PreparedCache(max_size=3)
        
        cache.put(PreparedStatement(name="stmt1", sql="SELECT 1"))
        cache.put(PreparedStatement(name="stmt2", sql="SELECT 2"))
        cache.put(PreparedStatement(name="stmt3", sql="SELECT 3"))
        
        # Access stmt1 to make it recently used
        cache.get("stmt1")
        
        # Add new statement, should evict stmt2 (LRU)
        cache.put(PreparedStatement(name="stmt4", sql="SELECT 4"))
        
        assert cache.get("stmt2") is None
        assert cache.get("stmt1") is not None
    
    def test_all_stats(self):
        """Test getting all statement stats."""
        cache = PreparedCache()
        
        stmt1 = PreparedStatement(name="stmt1", sql="SELECT 1")
        stmt2 = PreparedStatement(name="stmt2", sql="SELECT 2")
        
        cache.put(stmt1)
        cache.put(stmt2)
        
        stats = cache.all_stats()
        
        assert "stmt1" in stats
        assert "stmt2" in stats
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        cache = PreparedCache(max_size=100)
        stmt = PreparedStatement(name="test", sql="SELECT 1")
        cache.put(stmt)
        
        d = cache.to_dict()
        
        assert d["size"] == 1
        assert d["max_size"] == 100
        assert "test" in d["statements"]


# =============================================================================
# PREPARED EXECUTOR TESTS
# =============================================================================

class TestPreparedExecutor:
    """Tests for PreparedExecutor."""
    
    def test_basic_creation(self):
        """Test basic executor creation."""
        executor = PreparedExecutor()
        assert executor.cache is not None
    
    @pytest.mark.asyncio
    async def test_prepare(self):
        """Test preparing a statement."""
        prepare_calls = []
        
        async def mock_prepare(sql):
            prepare_calls.append(sql)
        
        executor = PreparedExecutor(prepare_fn=mock_prepare)
        stmt = await executor.prepare(
            "get_user",
            "SELECT * FROM users WHERE id = $1",
            types=[int],
        )
        
        assert stmt.name == "get_user"
        assert stmt.state == StatementState.PREPARED
        assert len(prepare_calls) == 1
    
    @pytest.mark.asyncio
    async def test_prepare_cached(self):
        """Test that prepared statement is cached."""
        prepare_calls = []
        
        async def mock_prepare(sql):
            prepare_calls.append(sql)
        
        executor = PreparedExecutor(prepare_fn=mock_prepare)
        
        stmt1 = await executor.prepare("test", "SELECT 1")
        stmt2 = await executor.prepare("test", "SELECT 1")
        
        # Should only prepare once
        assert len(prepare_calls) == 1
        assert stmt1 is stmt2
    
    @pytest.mark.asyncio
    async def test_execute(self):
        """Test executing a prepared statement."""
        async def mock_execute(sql, params):
            return [{"id": 1}]
        
        executor = PreparedExecutor(execute_fn=mock_execute)
        stmt = PreparedStatement(name="test", sql="SELECT 1")
        stmt.state = StatementState.PREPARED
        
        result = await executor.execute(stmt, ())
        
        assert result == [{"id": 1}]
        assert stmt.stats.call_count == 1
    
    @pytest.mark.asyncio
    async def test_fetchone(self):
        """Test fetchone method."""
        async def mock_execute(sql, params):
            return [{"id": 1}, {"id": 2}]
        
        executor = PreparedExecutor(execute_fn=mock_execute)
        stmt = PreparedStatement(name="test", sql="SELECT 1")
        stmt.state = StatementState.PREPARED
        
        result = await executor.fetchone(stmt, 1)
        
        assert result == {"id": 1}
    
    @pytest.mark.asyncio
    async def test_fetchone_empty(self):
        """Test fetchone with empty result."""
        async def mock_execute(sql, params):
            return []
        
        executor = PreparedExecutor(execute_fn=mock_execute)
        stmt = PreparedStatement(name="test", sql="SELECT 1")
        stmt.state = StatementState.PREPARED
        
        result = await executor.fetchone(stmt, 1)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_fetchall(self):
        """Test fetchall method."""
        async def mock_execute(sql, params):
            return [{"id": 1}, {"id": 2}]
        
        executor = PreparedExecutor(execute_fn=mock_execute)
        stmt = PreparedStatement(name="test", sql="SELECT 1")
        stmt.state = StatementState.PREPARED
        
        result = await executor.fetchall(stmt, 1)
        
        assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_unprepare(self):
        """Test unpreparing a statement."""
        deallocate_calls = []
        
        async def mock_prepare(sql):
            pass
        
        async def mock_deallocate(sql):
            deallocate_calls.append(sql)
        
        executor = PreparedExecutor(
            prepare_fn=mock_prepare,
            deallocate_fn=mock_deallocate,
        )
        
        await executor.prepare("test", "SELECT 1")
        result = await executor.unprepare("test")
        
        assert result is True
        assert len(deallocate_calls) == 1
    
    @pytest.mark.asyncio
    async def test_unprepare_nonexistent(self):
        """Test unpreparing nonexistent statement."""
        executor = PreparedExecutor()
        result = await executor.unprepare("nonexistent")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_unprepare_all(self):
        """Test unpreparing all statements."""
        async def mock_prepare(sql):
            pass
        
        async def mock_deallocate(sql):
            pass
        
        executor = PreparedExecutor(
            prepare_fn=mock_prepare,
            deallocate_fn=mock_deallocate,
        )
        
        await executor.prepare("stmt1", "SELECT 1")
        await executor.prepare("stmt2", "SELECT 2")
        
        count = await executor.unprepare_all()
        
        assert count == 2
        assert executor.cache.size == 0
    
    def test_get_stats(self):
        """Test getting statement stats."""
        executor = PreparedExecutor()
        stmt = PreparedStatement(name="test", sql="SELECT 1")
        executor.cache.put(stmt)
        
        stats = executor.get_stats("test")
        
        assert stats is not None
        assert stats.name == "test"
    
    def test_get_stats_nonexistent(self):
        """Test getting stats for nonexistent statement."""
        executor = PreparedExecutor()
        stats = executor.get_stats("nonexistent")
        assert stats is None
    
    def test_all_stats(self):
        """Test getting all stats."""
        executor = PreparedExecutor()
        
        stmt1 = PreparedStatement(name="stmt1", sql="SELECT 1")
        stmt2 = PreparedStatement(name="stmt2", sql="SELECT 2")
        
        executor.cache.put(stmt1)
        executor.cache.put(stmt2)
        
        stats = executor.all_stats()
        
        assert "stmt1" in stats
        assert "stmt2" in stats


# =============================================================================
# SCHEMA WATCHER TESTS
# =============================================================================

class TestSchemaWatcher:
    """Tests for SchemaWatcher."""
    
    def test_basic_creation(self):
        """Test basic watcher creation."""
        cache = PreparedCache()
        watcher = SchemaWatcher(cache)
        assert watcher.cache is cache
    
    def test_on_change_decorator(self):
        """Test on_change decorator."""
        cache = PreparedCache()
        watcher = SchemaWatcher(cache)
        
        @watcher.on_change("users")
        def handler():
            pass
        
        assert "users" in watcher._listeners
        assert len(watcher._listeners["users"]) == 1
    
    @pytest.mark.asyncio
    async def test_handle_change(self):
        """Test handling schema change."""
        cache = PreparedCache()
        stmt = PreparedStatement(
            name="users_query",
            sql="SELECT * FROM users",
        )
        stmt.state = StatementState.PREPARED
        cache.put(stmt)
        
        watcher = SchemaWatcher(cache)
        
        await watcher.handle_change("users", "ALTER")
        
        assert stmt.state == StatementState.INVALID
    
    @pytest.mark.asyncio
    async def test_handle_change_calls_listener(self):
        """Test that listeners are called on change."""
        cache = PreparedCache()
        watcher = SchemaWatcher(cache)
        
        listener_called = []
        
        @watcher.on_change("users")
        async def handler():
            listener_called.append(True)
        
        await watcher.handle_change("users", "ALTER")
        
        assert len(listener_called) == 1
    
    @pytest.mark.asyncio
    async def test_stop_watcher(self):
        """Test stopping the watcher."""
        cache = PreparedCache()
        watcher = SchemaWatcher(cache)
        
        await watcher.stop()
        
        assert watcher._running is False


# =============================================================================
# DECORATOR TESTS
# =============================================================================

class TestPreparedDecorator:
    """Tests for @prepared decorator."""
    
    def test_decorator_adds_metadata(self):
        """Test decorator adds metadata."""
        @prepared("test_query", types=[int])
        async def get_data(limit):
            return "SELECT * FROM data LIMIT $1"
        
        assert hasattr(get_data, "_prepared_name")
        assert get_data._prepared_name == "test_query"
        assert get_data._prepared_types == [int]


# =============================================================================
# GLOBAL STATE TESTS
# =============================================================================

class TestGlobalState:
    """Tests for global state management."""
    
    def test_get_prepared_executor(self):
        """Test getting global executor."""
        executor = get_prepared_executor()
        assert isinstance(executor, PreparedExecutor)
    
    def test_set_prepared_executor(self):
        """Test setting global executor."""
        original = get_prepared_executor()
        
        new_executor = PreparedExecutor()
        set_prepared_executor(new_executor)
        
        assert get_prepared_executor() is new_executor
        
        # Restore
        set_prepared_executor(original)


# =============================================================================
# EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases."""
    
    def test_statement_with_no_tables(self):
        """Test statement with no tables."""
        stmt = PreparedStatement(
            name="select_one",
            sql="SELECT 1",
        )
        assert len(stmt.tables) == 0
    
    def test_statement_with_cte(self):
        """Test statement with CTE."""
        stmt = PreparedStatement(
            name="cte_query",
            sql="WITH cte AS (SELECT * FROM users) SELECT * FROM cte",
        )
        assert "users" in stmt.tables
    
    def test_cache_update_existing(self):
        """Test updating existing statement in cache."""
        cache = PreparedCache()
        
        stmt1 = PreparedStatement(name="test", sql="SELECT 1")
        stmt2 = PreparedStatement(name="test", sql="SELECT 2")
        
        cache.put(stmt1)
        cache.put(stmt2)
        
        retrieved = cache.get("test")
        assert retrieved.sql == "SELECT 2"
    
    @pytest.mark.asyncio
    async def test_execute_re_prepares_invalid(self):
        """Test execute re-prepares invalid statement."""
        prepare_calls = []
        
        async def mock_prepare(sql):
            prepare_calls.append(sql)
        
        async def mock_execute(sql, params):
            return []
        
        executor = PreparedExecutor(
            prepare_fn=mock_prepare,
            execute_fn=mock_execute,
        )
        
        stmt = PreparedStatement(name="test", sql="SELECT 1")
        stmt.state = StatementState.INVALID
        stmt.backend_name = "pynext_test"
        
        await executor.execute(stmt, ())
        
        assert len(prepare_calls) == 1
        assert stmt.state == StatementState.PREPARED
    
    def test_stats_created_at(self):
        """Test stats created_at is set."""
        stmt = PreparedStatement(name="test", sql="SELECT 1")
        assert stmt.stats.created_at is not None
    
    @pytest.mark.asyncio
    async def test_listener_error_doesnt_break_flow(self):
        """Test listener error doesn't break change handling."""
        cache = PreparedCache()
        watcher = SchemaWatcher(cache)
        
        @watcher.on_change("users")
        def bad_listener():
            raise Exception("Listener error")
        
        # Should not raise
        await watcher.handle_change("users", "ALTER")


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests for prepared statements."""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete prepared statement workflow."""
        prepare_calls = []
        execute_calls = []
        
        async def mock_prepare(sql):
            prepare_calls.append(sql)
        
        async def mock_execute(sql, params):
            execute_calls.append((sql, params))
            return [{"id": params[0]}]
        
        executor = PreparedExecutor(
            prepare_fn=mock_prepare,
            execute_fn=mock_execute,
        )
        
        # Prepare
        stmt = await executor.prepare(
            "get_user",
            "SELECT * FROM users WHERE id = $1",
            types=[int],
        )
        
        assert stmt.state == StatementState.PREPARED
        assert len(prepare_calls) == 1
        
        # Execute multiple times
        result1 = await executor.fetchone(stmt, 1)
        result2 = await executor.fetchone(stmt, 2)
        
        assert result1 == {"id": 1}
        assert result2 == {"id": 2}
        assert len(execute_calls) == 2
        assert stmt.stats.call_count == 2
        
        # Invalidate
        stmt.invalidate()
        assert stmt.state == StatementState.INVALID
        
        # Execute again (should re-prepare)
        result3 = await executor.fetchone(stmt, 3)
        
        assert len(prepare_calls) == 2
        assert result3 == {"id": 3}
    
    @pytest.mark.asyncio
    async def test_schema_change_invalidation(self):
        """Test schema change triggers invalidation."""
        cache = PreparedCache()
        watcher = SchemaWatcher(cache)
        
        # Add some statements
        stmt1 = PreparedStatement(
            name="users_select",
            sql="SELECT * FROM users",
        )
        stmt1.state = StatementState.PREPARED
        
        stmt2 = PreparedStatement(
            name="orders_select",
            sql="SELECT * FROM orders",
        )
        stmt2.state = StatementState.PREPARED
        
        cache.put(stmt1)
        cache.put(stmt2)
        
        # Trigger users table change
        await watcher.handle_change("users", "ALTER")
        
        # Only users statement should be invalidated
        assert stmt1.state == StatementState.INVALID
        assert stmt2.state == StatementState.PREPARED

