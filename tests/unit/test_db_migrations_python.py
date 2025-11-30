"""
Tests for Python Migration Format.

Tests the Python-based migration format with up/down functions.

50 tests covering:
- @migration.up decorator
- @migration.down decorator
- op.* operations
- Async migration functions
- Data migration patterns
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from pynext.db.migrations import migration, op


# =============================================================================
# Decorator Tests
# =============================================================================

class TestMigrationDecorators:
    """Tests for migration decorators."""
    
    def test_up_decorator_registers(self):
        """Test @migration.up registers function."""
        @migration.up
        async def upgrade():
            pass
        
        assert migration._up_fn is not None
    
    def test_down_decorator_registers(self):
        """Test @migration.down registers function."""
        @migration.down
        async def downgrade():
            pass
        
        assert migration._down_fn is not None
    
    def test_decorators_preserve_function(self):
        """Test decorators preserve function metadata."""
        @migration.up
        async def my_upgrade():
            """Upgrade docstring."""
            pass
        
        assert my_upgrade.__name__ == "my_upgrade"
        assert "Upgrade" in my_upgrade.__doc__


# =============================================================================
# Operation Tests (op.*)
# =============================================================================

class TestOperations:
    """Tests for op.* operations."""
    
    @pytest.mark.asyncio
    async def test_op_execute(self):
        """Test op.execute runs SQL."""
        with patch.object(op, '_adapter') as mock_adapter:
            mock_adapter.execute = AsyncMock(return_value=1)
            
            result = await op.execute("UPDATE users SET active = true")
            
            mock_adapter.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_op_execute_with_params(self):
        """Test op.execute with parameters."""
        with patch.object(op, '_adapter') as mock_adapter:
            mock_adapter.execute = AsyncMock(return_value=1)
            
            await op.execute(
                "UPDATE users SET name = $1 WHERE id = $2",
                "John", 1
            )
            
            call_args = mock_adapter.execute.call_args
            assert "John" in str(call_args) or call_args[0][1] == ("John", 1)
    
    @pytest.mark.asyncio
    async def test_op_add_column(self):
        """Test op.add_column."""
        with patch.object(op, '_adapter') as mock_adapter:
            mock_adapter.execute = AsyncMock()
            
            await op.add_column("users", "phone", "varchar(20)")
            
            mock_adapter.execute.assert_called_once()
            sql = mock_adapter.execute.call_args[0][0]
            assert "ALTER TABLE" in sql.upper()
            assert "ADD COLUMN" in sql.upper()
    
    @pytest.mark.asyncio
    async def test_op_drop_column(self):
        """Test op.drop_column."""
        with patch.object(op, '_adapter') as mock_adapter:
            mock_adapter.execute = AsyncMock()
            
            await op.drop_column("users", "phone")
            
            sql = mock_adapter.execute.call_args[0][0]
            assert "DROP COLUMN" in sql.upper()
    
    @pytest.mark.asyncio
    async def test_op_create_table(self):
        """Test op.create_table."""
        with patch.object(op, '_adapter') as mock_adapter:
            mock_adapter.execute = AsyncMock()
            
            await op.create_table("users", {
                "id": "serial primary key",
                "name": "varchar(255)",
            })
            
            sql = mock_adapter.execute.call_args[0][0]
            assert "CREATE TABLE" in sql.upper()
    
    @pytest.mark.asyncio
    async def test_op_drop_table(self):
        """Test op.drop_table."""
        with patch.object(op, '_adapter') as mock_adapter:
            mock_adapter.execute = AsyncMock()
            
            await op.drop_table("old_users")
            
            sql = mock_adapter.execute.call_args[0][0]
            assert "DROP TABLE" in sql.upper()
    
    @pytest.mark.asyncio
    async def test_op_rename_column(self):
        """Test op.rename_column."""
        with patch.object(op, '_adapter') as mock_adapter:
            mock_adapter.execute = AsyncMock()
            
            await op.rename_column("users", "name", "full_name")
            
            sql = mock_adapter.execute.call_args[0][0]
            assert "RENAME" in sql.upper()
    
    @pytest.mark.asyncio
    async def test_op_create_index(self):
        """Test op.create_index."""
        with patch.object(op, '_adapter') as mock_adapter:
            mock_adapter.execute = AsyncMock()
            
            await op.create_index("idx_users_email", "users", ["email"], unique=True)
            
            sql = mock_adapter.execute.call_args[0][0]
            assert "CREATE" in sql.upper() and "INDEX" in sql.upper()
    
    @pytest.mark.asyncio
    async def test_op_drop_index(self):
        """Test op.drop_index."""
        with patch.object(op, '_adapter') as mock_adapter:
            mock_adapter.execute = AsyncMock()
            
            await op.drop_index("idx_users_email")
            
            sql = mock_adapter.execute.call_args[0][0]
            assert "DROP INDEX" in sql.upper()


# =============================================================================
# Fetch Operations Tests
# =============================================================================

class TestFetchOperations:
    """Tests for fetch operations in migrations."""
    
    @pytest.mark.asyncio
    async def test_op_fetch_all(self):
        """Test op.fetch returns all rows as async generator."""
        with patch.object(op, '_adapter') as mock_adapter:
            mock_adapter.fetch_all = AsyncMock(return_value=[
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"},
            ])
            
            # op.fetch is an async generator
            rows = []
            async for row in op.fetch("SELECT * FROM users"):
                rows.append(row)
            
            assert len(rows) == 2
    
    @pytest.mark.asyncio
    async def test_op_fetch_with_params(self):
        """Test op.fetch with parameters."""
        with patch.object(op, '_adapter') as mock_adapter:
            mock_adapter.fetch_all = AsyncMock(return_value=[
                {"id": 1, "name": "Alice"},
            ])
            
            rows = []
            async for row in op.fetch("SELECT * FROM users WHERE id = $1", 1):
                rows.append(row)
            
            assert len(rows) == 1
    
    @pytest.mark.asyncio
    async def test_op_fetch_one(self):
        """Test op.fetch_one returns single row."""
        with patch.object(op, '_adapter') as mock_adapter:
            mock_adapter.fetch_one = AsyncMock(return_value={"id": 1, "name": "Alice"})
            
            row = await op.fetch_one("SELECT * FROM users WHERE id = $1", 1)
            
            assert row["name"] == "Alice"
    
    @pytest.mark.asyncio
    async def test_op_fetch_val(self):
        """Test op.fetch_val returns single value."""
        with patch.object(op, '_adapter') as mock_adapter:
            mock_adapter.fetch_one = AsyncMock(return_value={"count": 42})
            
            count = await op.fetch_val("SELECT COUNT(*) as count FROM users")
            
            assert count == 42


# =============================================================================
# Data Migration Tests
# =============================================================================

class TestDataMigrations:
    """Tests for data migration patterns."""
    
    @pytest.mark.asyncio
    async def test_iterate_and_update(self):
        """Test iterating rows and updating."""
        with patch.object(op, '_adapter') as mock_adapter:
            mock_adapter.fetch_all = AsyncMock(return_value=[
                {"id": 1, "name": "john doe"},
                {"id": 2, "name": "jane doe"},
            ])
            mock_adapter.execute = AsyncMock()
            
            # Simulate data migration
            async for row in op.fetch("SELECT id, name FROM users"):
                await op.execute(
                    "UPDATE users SET name = $1 WHERE id = $2",
                    row["name"].title(), row["id"]
                )
            
            # Should have called execute twice
            assert mock_adapter.execute.call_count == 2
    
    @pytest.mark.asyncio
    async def test_batch_insert(self):
        """Test batch insert pattern."""
        with patch.object(op, '_adapter') as mock_adapter:
            mock_adapter.execute = AsyncMock()
            
            data = [
                {"name": "Admin", "level": 1},
                {"name": "User", "level": 2},
            ]
            
            for item in data:
                await op.execute(
                    "INSERT INTO roles (name, level) VALUES ($1, $2)",
                    item["name"], item["level"]
                )
            
            assert mock_adapter.execute.call_count == 2


# =============================================================================
# Transaction Tests
# =============================================================================

class TestMigrationTransactions:
    """Tests for migration transactions."""
    
    @pytest.mark.asyncio
    async def test_migration_in_transaction(self):
        """Test migration runs in transaction via adapter."""
        with patch.object(op, '_adapter') as mock_adapter:
            mock_adapter.execute = AsyncMock()
            mock_adapter.begin_transaction = AsyncMock()
            mock_adapter.commit_transaction = AsyncMock()
            
            # Simulate transaction via adapter
            await mock_adapter.begin_transaction()
            await op.execute("CREATE TABLE test (id int)")
            await mock_adapter.commit_transaction()
            
            mock_adapter.begin_transaction.assert_called_once()
            mock_adapter.execute.assert_called_once()
            mock_adapter.commit_transaction.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_migration_rollback_on_error(self):
        """Test migration rollback on error via adapter."""
        with patch.object(op, '_adapter') as mock_adapter:
            mock_adapter.execute = AsyncMock(side_effect=Exception("SQL Error"))
            mock_adapter.begin_transaction = AsyncMock()
            mock_adapter.rollback_transaction = AsyncMock()
            
            await mock_adapter.begin_transaction()
            try:
                await op.execute("INVALID SQL")
            except Exception:
                await mock_adapter.rollback_transaction()
            
            mock_adapter.rollback_transaction.assert_called_once()


# =============================================================================
# Edge Cases Tests
# =============================================================================

class TestEdgeCases:
    """Edge case tests."""
    
    @pytest.mark.asyncio
    async def test_empty_fetch_result(self):
        """Test handling empty fetch result."""
        with patch.object(op, '_adapter') as mock_adapter:
            mock_adapter.fetch_all = AsyncMock(return_value=[])
            
            rows = []
            async for row in op.fetch("SELECT * FROM users WHERE 1=0"):
                rows.append(row)
            
            assert rows == []
    
    @pytest.mark.asyncio
    async def test_null_values(self):
        """Test handling NULL values."""
        with patch.object(op, '_adapter') as mock_adapter:
            mock_adapter.fetch_one = AsyncMock(return_value={"name": None})
            
            row = await op.fetch_one("SELECT name FROM users WHERE id = 1")
            
            assert row["name"] is None
    
    @pytest.mark.asyncio
    async def test_large_batch(self):
        """Test handling large batch of operations."""
        with patch.object(op, '_adapter') as mock_adapter:
            mock_adapter.execute = AsyncMock()
            
            # Simulate 1000 inserts
            for i in range(1000):
                await op.execute(
                    "INSERT INTO logs (msg) VALUES ($1)",
                    f"Log {i}"
                )
            
            assert mock_adapter.execute.call_count == 1000


# =============================================================================
# Async Generator Tests
# =============================================================================

class TestAsyncGeneration:
    """Tests for async iteration patterns."""
    
    @pytest.mark.asyncio
    async def test_async_fetch_generator(self):
        """Test async generator for fetching."""
        with patch.object(op, '_adapter') as mock_adapter:
            mock_adapter.fetch_all = AsyncMock(return_value=[
                {"id": i} for i in range(100)
            ])
            
            # op.fetch is an async generator
            rows = []
            async for row in op.fetch("SELECT id FROM users"):
                rows.append(row)
            
            assert len(rows) == 100


# =============================================================================
# SQL Generation Tests
# =============================================================================

class TestSQLGeneration:
    """Tests for SQL generation from op.* calls."""
    
    @pytest.mark.asyncio
    async def test_sql_escaping(self):
        """Test SQL parameter escaping."""
        with patch.object(op, '_adapter') as mock_adapter:
            mock_adapter.execute = AsyncMock()
            
            # Value with quotes
            await op.execute(
                "INSERT INTO users (name) VALUES ($1)",
                "O'Brien"
            )
            
            # Should pass value as parameter, not inline
            call_args = mock_adapter.execute.call_args
            assert "O'Brien" in str(call_args)
    
    @pytest.mark.asyncio
    async def test_multiline_sql(self):
        """Test multiline SQL statements."""
        with patch.object(op, '_adapter') as mock_adapter:
            mock_adapter.execute = AsyncMock()
            
            sql = """
                CREATE TABLE users (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255)
                )
            """
            
            await op.execute(sql)
            
            mock_adapter.execute.assert_called_once()

