"""
Tests for PostgreSQL Per-Query Timeout Management.

Tests cover:
- QueryTimeoutConfig validation and defaults
- Query type detection (SELECT, INSERT, etc.)
- Table name extraction
- Per-type timeout rules
- Per-table timeout rules
- Per-pattern timeout rules
- Rule priority ordering
- Timeout statistics
- Execute with timeout
- Convenience configurations
"""

import asyncio
import pytest
import re
from unittest.mock import AsyncMock, MagicMock, patch

from pynext.db.adapters.postgres.performance.timeout import (
    QueryType,
    QueryTimeoutConfig,
    QueryWithTimeout,
    QueryTimeoutError,
    TimeoutStats,
    TimeoutManager,
    quick_timeout_config,
    standard_timeout_config,
    batch_timeout_config,
    no_timeout_config,
)


# =============================================================================
# QueryTimeoutConfig Tests
# =============================================================================

class TestQueryTimeoutConfig:
    """Tests for QueryTimeoutConfig dataclass."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = QueryTimeoutConfig()
        assert config.default == 30.0
        assert config.per_type == {}
        assert config.per_table == {}
        assert config.per_pattern == {}
        assert config.enabled is True
    
    def test_custom_default(self):
        """Test custom default timeout."""
        config = QueryTimeoutConfig(default=60.0)
        assert config.default == 60.0
    
    def test_per_type_config(self):
        """Test per-type timeout configuration."""
        config = QueryTimeoutConfig(
            per_type={"select": 10.0, "insert": 30.0}
        )
        assert config.per_type["select"] == 10.0
        assert config.per_type["insert"] == 30.0
    
    def test_per_table_config(self):
        """Test per-table timeout configuration."""
        config = QueryTimeoutConfig(
            per_table={"users": 15.0, "large_table": 120.0}
        )
        assert config.per_table["users"] == 15.0
        assert config.per_table["large_table"] == 120.0
    
    def test_per_pattern_config(self):
        """Test per-pattern timeout configuration."""
        config = QueryTimeoutConfig(
            per_pattern={r".*analytics.*": 300.0}
        )
        assert config.per_pattern[r".*analytics.*"] == 300.0
    
    def test_negative_default_raises(self):
        """Test that negative default raises error."""
        with pytest.raises(ValueError, match="default timeout must be >= 0"):
            QueryTimeoutConfig(default=-1.0)
    
    def test_negative_per_type_raises(self):
        """Test that negative per-type value raises error."""
        with pytest.raises(ValueError, match="per_type"):
            QueryTimeoutConfig(per_type={"select": -5.0})
    
    def test_negative_per_table_raises(self):
        """Test that negative per-table value raises error."""
        with pytest.raises(ValueError, match="per_table"):
            QueryTimeoutConfig(per_table={"users": -1.0})
    
    def test_negative_per_pattern_raises(self):
        """Test that negative per-pattern value raises error."""
        with pytest.raises(ValueError, match="per_pattern"):
            QueryTimeoutConfig(per_pattern={r".*": -10.0})
    
    def test_zero_timeout_allowed(self):
        """Test that zero timeout is allowed."""
        config = QueryTimeoutConfig(default=0.0)
        assert config.default == 0.0
    
    def test_disabled_config(self):
        """Test disabled configuration."""
        config = QueryTimeoutConfig(enabled=False)
        assert config.enabled is False
    
    def test_full_config(self):
        """Test full configuration with all options."""
        config = QueryTimeoutConfig(
            default=30.0,
            per_type={"select": 10.0, "insert": 60.0},
            per_table={"cache": 5.0},
            per_pattern={r"EXPLAIN": 120.0},
            enabled=True,
        )
        assert config.default == 30.0
        assert len(config.per_type) == 2
        assert len(config.per_table) == 1
        assert len(config.per_pattern) == 1


# =============================================================================
# Query Type Detection Tests
# =============================================================================

class TestQueryTypeDetection:
    """Tests for query type detection."""
    
    @pytest.fixture
    def manager(self):
        return TimeoutManager()
    
    def test_detect_select(self, manager):
        """Test SELECT query detection."""
        assert manager.detect_query_type("SELECT * FROM users") == QueryType.SELECT
        assert manager.detect_query_type("  SELECT id FROM users") == QueryType.SELECT
        assert manager.detect_query_type("select * from users") == QueryType.SELECT
    
    def test_detect_insert(self, manager):
        """Test INSERT query detection."""
        assert manager.detect_query_type("INSERT INTO users (name) VALUES ('John')") == QueryType.INSERT
        assert manager.detect_query_type("insert into users values (1)") == QueryType.INSERT
    
    def test_detect_update(self, manager):
        """Test UPDATE query detection."""
        assert manager.detect_query_type("UPDATE users SET name = 'John'") == QueryType.UPDATE
        assert manager.detect_query_type("update users set active = true") == QueryType.UPDATE
    
    def test_detect_delete(self, manager):
        """Test DELETE query detection."""
        assert manager.detect_query_type("DELETE FROM users WHERE id = 1") == QueryType.DELETE
        assert manager.detect_query_type("delete from users") == QueryType.DELETE
    
    def test_detect_ddl_create(self, manager):
        """Test CREATE DDL detection."""
        assert manager.detect_query_type("CREATE TABLE users (id INT)") == QueryType.DDL
        assert manager.detect_query_type("CREATE INDEX idx ON users(id)") == QueryType.DDL
    
    def test_detect_ddl_alter(self, manager):
        """Test ALTER DDL detection."""
        assert manager.detect_query_type("ALTER TABLE users ADD COLUMN age INT") == QueryType.DDL
    
    def test_detect_ddl_drop(self, manager):
        """Test DROP DDL detection."""
        assert manager.detect_query_type("DROP TABLE users") == QueryType.DDL
        assert manager.detect_query_type("DROP INDEX idx") == QueryType.DDL
    
    def test_detect_ddl_truncate(self, manager):
        """Test TRUNCATE DDL detection."""
        assert manager.detect_query_type("TRUNCATE TABLE users") == QueryType.DDL
    
    def test_detect_transaction_begin(self, manager):
        """Test BEGIN transaction detection."""
        assert manager.detect_query_type("BEGIN") == QueryType.TRANSACTION
        assert manager.detect_query_type("BEGIN TRANSACTION") == QueryType.TRANSACTION
    
    def test_detect_transaction_commit(self, manager):
        """Test COMMIT transaction detection."""
        assert manager.detect_query_type("COMMIT") == QueryType.TRANSACTION
    
    def test_detect_transaction_rollback(self, manager):
        """Test ROLLBACK transaction detection."""
        assert manager.detect_query_type("ROLLBACK") == QueryType.TRANSACTION
    
    def test_detect_transaction_savepoint(self, manager):
        """Test SAVEPOINT detection."""
        assert manager.detect_query_type("SAVEPOINT my_savepoint") == QueryType.TRANSACTION
    
    def test_detect_other(self, manager):
        """Test OTHER query type for unknown queries."""
        assert manager.detect_query_type("EXPLAIN SELECT * FROM users") == QueryType.OTHER
        assert manager.detect_query_type("VACUUM users") == QueryType.OTHER
        assert manager.detect_query_type("ANALYZE users") == QueryType.OTHER


# =============================================================================
# Table Extraction Tests
# =============================================================================

class TestTableExtraction:
    """Tests for table name extraction."""
    
    @pytest.fixture
    def manager(self):
        return TimeoutManager()
    
    def test_extract_from_select(self, manager):
        """Test table extraction from SELECT."""
        assert manager.extract_table("SELECT * FROM users") == "users"
        assert manager.extract_table("SELECT * FROM Users") == "users"
    
    def test_extract_from_insert(self, manager):
        """Test table extraction from INSERT."""
        assert manager.extract_table("INSERT INTO users VALUES (1)") == "users"
    
    def test_extract_from_update(self, manager):
        """Test table extraction from UPDATE."""
        assert manager.extract_table("UPDATE users SET name = 'John'") == "users"
    
    def test_extract_from_delete(self, manager):
        """Test table extraction from DELETE."""
        assert manager.extract_table("DELETE FROM users WHERE id = 1") == "users"
    
    def test_extract_from_join(self, manager):
        """Test table extraction from JOIN."""
        result = manager.extract_table("SELECT * FROM users JOIN orders ON users.id = orders.user_id")
        assert result == "users"  # First table
    
    def test_extract_from_create(self, manager):
        """Test table extraction from CREATE TABLE."""
        assert manager.extract_table("CREATE TABLE users (id INT)") == "users"
    
    def test_extract_with_schema(self, manager):
        """Test table extraction handles schema prefix."""
        # Currently extracts just the table name after FROM
        result = manager.extract_table("SELECT * FROM public.users")
        # Should handle this gracefully
        assert result is not None
    
    def test_extract_with_alias(self, manager):
        """Test table extraction with alias."""
        result = manager.extract_table("SELECT * FROM users u")
        assert result == "users"
    
    def test_extract_no_table(self, manager):
        """Test extraction when no table found."""
        assert manager.extract_table("SELECT 1") is None
        assert manager.extract_table("SELECT NOW()") is None


# =============================================================================
# Timeout Resolution Tests
# =============================================================================

class TestTimeoutResolution:
    """Tests for timeout resolution with various rules."""
    
    def test_default_timeout(self):
        """Test default timeout is used."""
        manager = TimeoutManager(QueryTimeoutConfig(default=25.0))
        assert manager.get_timeout("SELECT * FROM users") == 25.0
    
    def test_per_type_select(self):
        """Test per-type timeout for SELECT."""
        manager = TimeoutManager(QueryTimeoutConfig(
            default=30.0,
            per_type={"select": 10.0}
        ))
        assert manager.get_timeout("SELECT * FROM users") == 10.0
    
    def test_per_type_insert(self):
        """Test per-type timeout for INSERT."""
        manager = TimeoutManager(QueryTimeoutConfig(
            default=30.0,
            per_type={"insert": 60.0}
        ))
        assert manager.get_timeout("INSERT INTO users VALUES (1)") == 60.0
    
    def test_per_table_overrides_type(self):
        """Test per-table takes precedence over per-type."""
        manager = TimeoutManager(QueryTimeoutConfig(
            default=30.0,
            per_type={"select": 10.0},
            per_table={"slow_table": 120.0}
        ))
        assert manager.get_timeout("SELECT * FROM slow_table") == 120.0
    
    def test_per_pattern_overrides_table(self):
        """Test per-pattern takes precedence over per-table."""
        manager = TimeoutManager(QueryTimeoutConfig(
            default=30.0,
            per_table={"analytics": 60.0},
            per_pattern={r".*EXPLAIN.*": 180.0}
        ))
        assert manager.get_timeout("EXPLAIN SELECT * FROM analytics") == 180.0
    
    def test_override_overrides_all(self):
        """Test explicit override takes precedence."""
        manager = TimeoutManager(QueryTimeoutConfig(
            default=30.0,
            per_type={"select": 10.0},
            per_table={"users": 20.0},
            per_pattern={r".*users.*": 25.0}
        ))
        assert manager.get_timeout("SELECT * FROM users", override=5.0) == 5.0
    
    def test_disabled_returns_default(self):
        """Test disabled config returns default."""
        manager = TimeoutManager(QueryTimeoutConfig(
            default=30.0,
            per_type={"select": 10.0},
            enabled=False
        ))
        assert manager.get_timeout("SELECT * FROM users") == 30.0
    
    def test_pattern_case_insensitive(self):
        """Test pattern matching is case insensitive."""
        manager = TimeoutManager(QueryTimeoutConfig(
            per_pattern={r".*BULK.*": 300.0}
        ))
        assert manager.get_timeout("INSERT bulk_data INTO table") == 300.0
    
    def test_multiple_patterns_first_wins(self):
        """Test first matching pattern wins."""
        manager = TimeoutManager(QueryTimeoutConfig(
            per_pattern={
                r".*analytics.*": 100.0,
                r".*SELECT.*": 200.0,
            }
        ))
        # analytics pattern is first
        result = manager.get_timeout("SELECT * FROM analytics")
        assert result == 100.0
    
    def test_table_case_insensitive(self):
        """Test table lookup is case insensitive."""
        manager = TimeoutManager(QueryTimeoutConfig(
            per_table={"users": 15.0}
        ))
        assert manager.get_timeout("SELECT * FROM Users") == 15.0
        assert manager.get_timeout("SELECT * FROM USERS") == 15.0


# =============================================================================
# QueryWithTimeout Tests
# =============================================================================

class TestQueryWithTimeout:
    """Tests for QueryWithTimeout bundling."""
    
    def test_basic_bundling(self):
        """Test basic query bundling."""
        manager = TimeoutManager(QueryTimeoutConfig(default=30.0))
        qt = manager.with_timeout("SELECT * FROM users")
        
        assert qt.query == "SELECT * FROM users"
        assert qt.timeout == 30.0
        assert qt.query_type == QueryType.SELECT
        assert qt.matched_rule == "default"
    
    def test_bundling_with_type_rule(self):
        """Test bundling records type rule."""
        manager = TimeoutManager(QueryTimeoutConfig(
            per_type={"select": 10.0}
        ))
        qt = manager.with_timeout("SELECT * FROM users")
        
        assert qt.timeout == 10.0
        assert "type:select" in qt.matched_rule
    
    def test_bundling_with_table_rule(self):
        """Test bundling records table rule."""
        manager = TimeoutManager(QueryTimeoutConfig(
            per_table={"users": 15.0}
        ))
        qt = manager.with_timeout("SELECT * FROM users")
        
        assert qt.timeout == 15.0
        assert "table:users" in qt.matched_rule
    
    def test_bundling_with_pattern_rule(self):
        """Test bundling records pattern rule."""
        manager = TimeoutManager(QueryTimeoutConfig(
            per_pattern={r".*analytics.*": 300.0}
        ))
        qt = manager.with_timeout("SELECT * FROM analytics_data")
        
        assert qt.timeout == 300.0
        assert "pattern:" in qt.matched_rule
    
    def test_bundling_with_override(self):
        """Test bundling with explicit override."""
        manager = TimeoutManager()
        qt = manager.with_timeout("SELECT * FROM users", timeout=5.0)
        
        assert qt.timeout == 5.0
        assert qt.matched_rule == "override"
    
    def test_repr(self):
        """Test QueryWithTimeout repr."""
        qt = QueryWithTimeout(
            query="SELECT 1",
            timeout=10.0,
            query_type=QueryType.SELECT,
            matched_rule="default"
        )
        repr_str = repr(qt)
        assert "10" in repr_str
        assert "select" in repr_str


# =============================================================================
# Statistics Tests
# =============================================================================

class TestTimeoutStats:
    """Tests for timeout statistics tracking."""
    
    def test_initial_stats(self):
        """Test initial statistics are zero."""
        manager = TimeoutManager()
        stats = manager.get_stats()
        
        assert stats.total_queries == 0
        assert stats.timeouts == 0
        assert stats.timeout_rate == 0.0
        assert stats.avg_timeout_ms == 0.0
    
    def test_stats_after_queries(self):
        """Test statistics after queries."""
        manager = TimeoutManager(QueryTimeoutConfig(
            per_type={"select": 10.0, "insert": 30.0}
        ))
        
        manager.with_timeout("SELECT * FROM users")
        manager.with_timeout("INSERT INTO users VALUES (1)")
        
        stats = manager.get_stats()
        assert stats.total_queries == 2
        assert stats.by_type["select"] == 1
        assert stats.by_type["insert"] == 1
    
    def test_stats_by_rule(self):
        """Test statistics track matched rules."""
        manager = TimeoutManager(QueryTimeoutConfig(
            per_type={"select": 10.0}
        ))
        
        manager.with_timeout("SELECT * FROM users")
        manager.with_timeout("SELECT * FROM orders")
        manager.with_timeout("INSERT INTO users VALUES (1)")  # Uses default
        
        stats = manager.get_stats()
        assert "type:select" in stats.by_rule
        assert stats.by_rule["type:select"] == 2
    
    def test_stats_avg_timeout(self):
        """Test average timeout calculation."""
        manager = TimeoutManager(QueryTimeoutConfig(
            per_type={"select": 10.0, "insert": 30.0}
        ))
        
        manager.with_timeout("SELECT * FROM users")  # 10s
        manager.with_timeout("INSERT INTO users VALUES (1)")  # 30s
        
        stats = manager.get_stats()
        # Average: (10 + 30) / 2 = 20s = 20000ms
        assert stats.avg_timeout_ms == 20000.0
    
    def test_stats_reset(self):
        """Test statistics reset."""
        manager = TimeoutManager()
        manager.with_timeout("SELECT 1")
        
        manager.reset_stats()
        stats = manager.get_stats()
        
        assert stats.total_queries == 0
    
    def test_stats_to_dict(self):
        """Test statistics to dictionary conversion."""
        manager = TimeoutManager()
        manager.with_timeout("SELECT 1")
        
        stats_dict = manager.get_stats().to_dict()
        
        assert "total_queries" in stats_dict
        assert "timeouts" in stats_dict
        assert "timeout_rate" in stats_dict
        assert "avg_timeout_ms" in stats_dict
        assert "by_type" in stats_dict
        assert "by_rule" in stats_dict


# =============================================================================
# Execute With Timeout Tests
# =============================================================================

class TestExecuteWithTimeout:
    """Tests for execute_with_timeout."""
    
    @pytest.mark.asyncio
    async def test_successful_execution(self):
        """Test successful query execution."""
        manager = TimeoutManager(QueryTimeoutConfig(default=5.0))
        
        async def mock_executor(query):
            await asyncio.sleep(0.01)
            return [{"id": 1}]
        
        result = await manager.execute_with_timeout(
            "SELECT * FROM users",
            executor=mock_executor,
        )
        
        assert result == [{"id": 1}]
    
    @pytest.mark.asyncio
    async def test_timeout_raises_error(self):
        """Test timeout raises QueryTimeoutError."""
        manager = TimeoutManager(QueryTimeoutConfig(default=0.1))
        
        async def slow_executor(query):
            await asyncio.sleep(1.0)
            return []
        
        with pytest.raises(QueryTimeoutError) as exc_info:
            await manager.execute_with_timeout(
                "SELECT * FROM slow_table",
                executor=slow_executor,
            )
        
        assert exc_info.value.timeout == 0.1
        assert exc_info.value.query_type == QueryType.SELECT
    
    @pytest.mark.asyncio
    async def test_timeout_records_stats(self):
        """Test timeout increments statistics."""
        manager = TimeoutManager(QueryTimeoutConfig(default=0.05))
        
        async def slow_executor(query):
            await asyncio.sleep(1.0)
            return []
        
        try:
            await manager.execute_with_timeout(
                "SELECT * FROM users",
                executor=slow_executor,
            )
        except QueryTimeoutError:
            pass
        
        stats = manager.get_stats()
        assert stats.timeouts == 1
    
    @pytest.mark.asyncio
    async def test_timeout_with_override(self):
        """Test execution with timeout override."""
        manager = TimeoutManager(QueryTimeoutConfig(default=10.0))
        
        async def slow_executor(query):
            await asyncio.sleep(0.5)
            return []
        
        with pytest.raises(QueryTimeoutError):
            await manager.execute_with_timeout(
                "SELECT * FROM users",
                executor=slow_executor,
                timeout=0.1,
            )
    
    @pytest.mark.asyncio
    async def test_executor_exception_propagates(self):
        """Test executor exceptions propagate correctly."""
        manager = TimeoutManager()
        
        async def failing_executor(query):
            raise ValueError("Database error")
        
        with pytest.raises(ValueError, match="Database error"):
            await manager.execute_with_timeout(
                "SELECT * FROM users",
                executor=failing_executor,
            )


# =============================================================================
# QueryTimeoutError Tests
# =============================================================================

class TestQueryTimeoutError:
    """Tests for QueryTimeoutError exception."""
    
    def test_error_attributes(self):
        """Test error has correct attributes."""
        error = QueryTimeoutError(
            query="SELECT * FROM users",
            timeout=10.0,
            elapsed=12.5,
            query_type=QueryType.SELECT,
        )
        
        assert error.query == "SELECT * FROM users"
        assert error.timeout == 10.0
        assert error.elapsed == 12.5
        assert error.query_type == QueryType.SELECT
    
    def test_error_message(self):
        """Test error message is informative."""
        error = QueryTimeoutError(
            query="SELECT * FROM users",
            timeout=10.0,
            elapsed=12.5,
            query_type=QueryType.SELECT,
        )
        
        message = str(error)
        assert "12.5" in message
        assert "10" in message
        assert "select" in message.lower()
    
    def test_error_truncates_long_query(self):
        """Test long queries are truncated in message."""
        long_query = "SELECT " + "x, " * 100 + "y FROM users"
        error = QueryTimeoutError(
            query=long_query,
            timeout=10.0,
            elapsed=12.5,
        )
        
        message = str(error)
        assert "..." in message
        assert len(message) < len(long_query) + 100


# =============================================================================
# Convenience Configuration Tests
# =============================================================================

class TestConvenienceConfigs:
    """Tests for convenience configuration functions."""
    
    def test_quick_timeout_config(self):
        """Test quick timeout configuration."""
        config = quick_timeout_config()
        
        assert config.default == 10.0
        assert config.per_type["select"] == 5.0
    
    def test_standard_timeout_config(self):
        """Test standard timeout configuration."""
        config = standard_timeout_config()
        
        assert config.default == 30.0
        assert config.per_type["select"] == 15.0
        assert config.per_type["ddl"] == 60.0
    
    def test_batch_timeout_config(self):
        """Test batch timeout configuration."""
        config = batch_timeout_config()
        
        assert config.default == 120.0
        assert config.per_type["ddl"] == 300.0
    
    def test_no_timeout_config(self):
        """Test no timeout configuration."""
        config = no_timeout_config()
        
        assert config.default == 3600.0
        assert config.enabled is False


# =============================================================================
# Manager Tests
# =============================================================================

class TestTimeoutManager:
    """Tests for TimeoutManager class."""
    
    def test_default_manager(self):
        """Test manager with default config."""
        manager = TimeoutManager()
        assert manager.config.default == 30.0
    
    def test_manager_with_config(self):
        """Test manager with custom config."""
        config = QueryTimeoutConfig(default=60.0)
        manager = TimeoutManager(config)
        assert manager.config.default == 60.0
    
    def test_manager_repr(self):
        """Test manager string representation."""
        manager = TimeoutManager(QueryTimeoutConfig(
            per_type={"select": 10.0},
            per_table={"users": 20.0},
            per_pattern={r".*": 30.0},
        ))
        
        repr_str = repr(manager)
        assert "types=1" in repr_str
        assert "tables=1" in repr_str
        assert "patterns=1" in repr_str
    
    def test_invalid_pattern_logged(self):
        """Test invalid regex pattern is logged but doesn't crash."""
        # Invalid regex should be handled gracefully
        config = QueryTimeoutConfig(
            per_pattern={"[invalid": 10.0}  # Invalid regex
        )
        manager = TimeoutManager(config)
        
        # Should still work, just skip invalid pattern
        timeout = manager.get_timeout("SELECT * FROM users")
        assert timeout == 30.0  # Default


# =============================================================================
# Edge Cases Tests
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases."""
    
    def test_empty_query(self):
        """Test empty query string."""
        manager = TimeoutManager()
        timeout = manager.get_timeout("")
        assert timeout == 30.0  # Default
    
    def test_whitespace_query(self):
        """Test whitespace-only query."""
        manager = TimeoutManager()
        query_type = manager.detect_query_type("   ")
        assert query_type == QueryType.OTHER
    
    def test_very_long_query(self):
        """Test very long query."""
        manager = TimeoutManager()
        long_query = "SELECT " + ", ".join(f"col{i}" for i in range(1000)) + " FROM users"
        timeout = manager.get_timeout(long_query)
        assert timeout == 30.0
    
    def test_unicode_in_query(self):
        """Test Unicode characters in query."""
        manager = TimeoutManager()
        timeout = manager.get_timeout("SELECT * FROM users WHERE name = '日本語'")
        assert timeout == 30.0
    
    def test_special_characters_in_table(self):
        """Test special characters in table config."""
        manager = TimeoutManager(QueryTimeoutConfig(
            per_table={"my_table_123": 20.0}
        ))
        timeout = manager.get_timeout("SELECT * FROM my_table_123")
        assert timeout == 20.0
    
    def test_zero_timeout_execution(self):
        """Test zero timeout configuration."""
        manager = TimeoutManager(QueryTimeoutConfig(default=0.0))
        qt = manager.with_timeout("SELECT 1")
        assert qt.timeout == 0.0


# =============================================================================
# Concurrent Usage Tests
# =============================================================================

class TestConcurrentUsage:
    """Tests for concurrent timeout manager usage."""
    
    @pytest.mark.asyncio
    async def test_concurrent_timeout_resolution(self):
        """Test concurrent timeout resolution is thread-safe."""
        manager = TimeoutManager(QueryTimeoutConfig(
            per_type={"select": 10.0, "insert": 30.0}
        ))
        
        async def resolve_timeout(query):
            return manager.get_timeout(query)
        
        queries = [
            "SELECT * FROM users",
            "INSERT INTO users VALUES (1)",
            "UPDATE users SET active = true",
            "DELETE FROM users WHERE id = 1",
        ]
        
        results = await asyncio.gather(*[resolve_timeout(q) for q in queries])
        
        assert len(results) == 4
        assert results[0] == 10.0  # SELECT
        assert results[1] == 30.0  # INSERT
    
    @pytest.mark.asyncio
    async def test_concurrent_stats_updates(self):
        """Test concurrent statistics updates."""
        manager = TimeoutManager()
        
        async def use_manager():
            for _ in range(10):
                manager.with_timeout("SELECT 1")
                await asyncio.sleep(0.001)
        
        await asyncio.gather(*[use_manager() for _ in range(5)])
        
        stats = manager.get_stats()
        assert stats.total_queries == 50

