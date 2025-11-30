"""
Tests for Migration Operations (op.* API).

Tests the operations API used in Python migrations.

60 tests covering:
- Table operations (create, drop, rename)
- Column operations (add, drop, rename, alter)
- Index operations
- Data operations (execute, fetch)
- Dry-run mode
- SQL formatting
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from pynext.db.migrations.operations import Operations, op


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_adapter():
    """Create a mock adapter."""
    adapter = AsyncMock()
    adapter.execute = AsyncMock(return_value=None)
    adapter.fetch_all = AsyncMock(return_value=[])
    adapter.fetch_one = AsyncMock(return_value=None)
    return adapter


@pytest.fixture
def operations(mock_adapter):
    """Create configured Operations instance."""
    ops = Operations()
    ops.configure(mock_adapter, dialect="sqlite", dry_run=False)
    return ops


@pytest.fixture
def dry_run_ops(mock_adapter):
    """Create Operations in dry-run mode."""
    ops = Operations()
    ops.configure(mock_adapter, dialect="sqlite", dry_run=True)
    return ops


# =============================================================================
# Configuration Tests
# =============================================================================

class TestConfiguration:
    """Tests for Operations configuration."""
    
    def test_initial_state(self):
        """Test initial state before configuration."""
        ops = Operations()
        assert ops._adapter is None
        assert ops._dialect == "sqlite"
        assert ops._dry_run is False
    
    def test_configure(self, mock_adapter):
        """Test configuration."""
        ops = Operations()
        ops.configure(mock_adapter, dialect="postgresql", dry_run=True)
        
        assert ops._adapter == mock_adapter
        assert ops._dialect == "postgresql"
        assert ops._dry_run is True
    
    def test_sql_statements_empty(self, dry_run_ops):
        """Test SQL statements list starts empty."""
        assert dry_run_ops.sql_statements == []


# =============================================================================
# Table Operations Tests
# =============================================================================

class TestTableOperations:
    """Tests for table operations."""
    
    @pytest.mark.asyncio
    async def test_create_table(self, operations, mock_adapter):
        """Test create_table operation."""
        await operations.create_table("users", {
            "id": "serial primary key",
            "name": "varchar(255) not null",
        })
        
        mock_adapter.execute.assert_called_once()
        sql = mock_adapter.execute.call_args[0][0]
        assert "CREATE TABLE" in sql
        assert "users" in sql
        assert "id serial primary key" in sql
        assert "name varchar(255) not null" in sql
    
    @pytest.mark.asyncio
    async def test_create_table_if_not_exists(self, operations, mock_adapter):
        """Test create_table with IF NOT EXISTS."""
        await operations.create_table("users", {"id": "integer"}, if_not_exists=True)
        
        sql = mock_adapter.execute.call_args[0][0]
        assert "IF NOT EXISTS" in sql
    
    @pytest.mark.asyncio
    async def test_create_table_without_if_not_exists(self, operations, mock_adapter):
        """Test create_table without IF NOT EXISTS."""
        await operations.create_table("users", {"id": "integer"}, if_not_exists=False)
        
        sql = mock_adapter.execute.call_args[0][0]
        assert "IF NOT EXISTS" not in sql
    
    @pytest.mark.asyncio
    async def test_drop_table(self, operations, mock_adapter):
        """Test drop_table operation."""
        await operations.drop_table("users")
        
        sql = mock_adapter.execute.call_args[0][0]
        assert "DROP TABLE" in sql
        assert "users" in sql
    
    @pytest.mark.asyncio
    async def test_drop_table_if_exists(self, operations, mock_adapter):
        """Test drop_table with IF EXISTS."""
        await operations.drop_table("users", if_exists=True)
        
        sql = mock_adapter.execute.call_args[0][0]
        assert "IF EXISTS" in sql
    
    @pytest.mark.asyncio
    async def test_drop_table_cascade_postgresql(self, mock_adapter):
        """Test drop_table with CASCADE for PostgreSQL."""
        ops = Operations()
        ops.configure(mock_adapter, dialect="postgresql", dry_run=False)
        
        await ops.drop_table("users", cascade=True)
        
        sql = mock_adapter.execute.call_args[0][0]
        assert "CASCADE" in sql
    
    @pytest.mark.asyncio
    async def test_drop_table_cascade_sqlite(self, operations, mock_adapter):
        """Test drop_table with CASCADE for SQLite (ignored)."""
        await operations.drop_table("users", cascade=True)
        
        sql = mock_adapter.execute.call_args[0][0]
        # SQLite doesn't support CASCADE
        assert "CASCADE" not in sql
    
    @pytest.mark.asyncio
    async def test_rename_table(self, operations, mock_adapter):
        """Test rename_table operation."""
        await operations.rename_table("users", "accounts")
        
        sql = mock_adapter.execute.call_args[0][0]
        assert "ALTER TABLE users RENAME TO accounts" in sql


# =============================================================================
# Column Operations Tests
# =============================================================================

class TestColumnOperations:
    """Tests for column operations."""
    
    @pytest.mark.asyncio
    async def test_add_column_basic(self, operations, mock_adapter):
        """Test basic add_column operation."""
        await operations.add_column("users", "email", "varchar(255)")
        
        sql = mock_adapter.execute.call_args[0][0]
        assert "ALTER TABLE users ADD COLUMN email varchar(255)" in sql
    
    @pytest.mark.asyncio
    async def test_add_column_not_null(self, operations, mock_adapter):
        """Test add_column with NOT NULL."""
        await operations.add_column("users", "email", "varchar(255)", nullable=False)
        
        sql = mock_adapter.execute.call_args[0][0]
        assert "NOT NULL" in sql
    
    @pytest.mark.asyncio
    async def test_add_column_with_default_string(self, operations, mock_adapter):
        """Test add_column with string default."""
        await operations.add_column("users", "role", "varchar(50)", default="user")
        
        sql = mock_adapter.execute.call_args[0][0]
        assert "DEFAULT 'user'" in sql
    
    @pytest.mark.asyncio
    async def test_add_column_with_default_int(self, operations, mock_adapter):
        """Test add_column with integer default."""
        await operations.add_column("users", "count", "integer", default=0)
        
        sql = mock_adapter.execute.call_args[0][0]
        assert "DEFAULT 0" in sql
    
    @pytest.mark.asyncio
    async def test_add_column_with_default_bool(self, operations, mock_adapter):
        """Test add_column with boolean default."""
        await operations.add_column("users", "active", "boolean", default=True)
        
        sql = mock_adapter.execute.call_args[0][0]
        assert "DEFAULT 1" in sql
    
    @pytest.mark.asyncio
    async def test_drop_column_postgresql(self, mock_adapter):
        """Test drop_column for PostgreSQL."""
        ops = Operations()
        ops.configure(mock_adapter, dialect="postgresql", dry_run=False)
        
        await ops.drop_column("users", "old_column")
        
        sql = mock_adapter.execute.call_args[0][0]
        assert "ALTER TABLE users DROP COLUMN old_column" in sql
    
    @pytest.mark.asyncio
    async def test_drop_column_sqlite(self, operations, mock_adapter):
        """Test drop_column for SQLite (comment)."""
        await operations.drop_column("users", "old_column")
        
        sql = mock_adapter.execute.call_args[0][0]
        assert "SQLite" in sql or "DROP COLUMN" in sql
    
    @pytest.mark.asyncio
    async def test_rename_column(self, operations, mock_adapter):
        """Test rename_column operation."""
        await operations.rename_column("users", "name", "full_name")
        
        sql = mock_adapter.execute.call_args[0][0]
        assert "RENAME COLUMN name TO full_name" in sql
    
    @pytest.mark.asyncio
    async def test_alter_column_type_postgresql(self, mock_adapter):
        """Test alter_column type change for PostgreSQL."""
        ops = Operations()
        ops.configure(mock_adapter, dialect="postgresql", dry_run=False)
        
        await ops.alter_column("users", "bio", type_def="text")
        
        sql = mock_adapter.execute.call_args[0][0]
        assert "ALTER COLUMN bio TYPE text" in sql
    
    @pytest.mark.asyncio
    async def test_alter_column_nullable_postgresql(self, mock_adapter):
        """Test alter_column nullable change for PostgreSQL."""
        ops = Operations()
        ops.configure(mock_adapter, dialect="postgresql", dry_run=False)
        
        await ops.alter_column("users", "email", nullable=False)
        
        sql = mock_adapter.execute.call_args[0][0]
        assert "SET NOT NULL" in sql
    
    @pytest.mark.asyncio
    async def test_alter_column_drop_not_null(self, mock_adapter):
        """Test alter_column drop NOT NULL for PostgreSQL."""
        ops = Operations()
        ops.configure(mock_adapter, dialect="postgresql", dry_run=False)
        
        await ops.alter_column("users", "email", nullable=True)
        
        sql = mock_adapter.execute.call_args[0][0]
        assert "DROP NOT NULL" in sql
    
    @pytest.mark.asyncio
    async def test_alter_column_default(self, mock_adapter):
        """Test alter_column set default for PostgreSQL."""
        ops = Operations()
        ops.configure(mock_adapter, dialect="postgresql", dry_run=False)
        
        await ops.alter_column("users", "role", default="admin")
        
        sql = mock_adapter.execute.call_args[0][0]
        assert "SET DEFAULT" in sql
    
    @pytest.mark.asyncio
    async def test_alter_column_drop_default(self, mock_adapter):
        """Test alter_column drop default for PostgreSQL."""
        ops = Operations()
        ops.configure(mock_adapter, dialect="postgresql", dry_run=False)
        
        await ops.alter_column("users", "role", drop_default=True)
        
        sql = mock_adapter.execute.call_args[0][0]
        assert "DROP DEFAULT" in sql
    
    @pytest.mark.asyncio
    async def test_alter_column_sqlite_not_supported(self, operations, mock_adapter):
        """Test alter_column for SQLite (not supported)."""
        await operations.alter_column("users", "bio", type_def="text")
        
        sql = mock_adapter.execute.call_args[0][0]
        assert "SQLite" in sql


# =============================================================================
# Index Operations Tests
# =============================================================================

class TestIndexOperations:
    """Tests for index operations."""
    
    @pytest.mark.asyncio
    async def test_create_index(self, operations, mock_adapter):
        """Test create_index operation."""
        await operations.create_index("ix_users_email", "users", ["email"])
        
        sql = mock_adapter.execute.call_args[0][0]
        assert "CREATE INDEX" in sql
        assert "ix_users_email" in sql
        assert "ON users (email)" in sql
    
    @pytest.mark.asyncio
    async def test_create_unique_index(self, operations, mock_adapter):
        """Test create_index with unique."""
        await operations.create_index("uix_users_email", "users", ["email"], unique=True)
        
        sql = mock_adapter.execute.call_args[0][0]
        assert "CREATE UNIQUE INDEX" in sql
    
    @pytest.mark.asyncio
    async def test_create_multi_column_index(self, operations, mock_adapter):
        """Test create_index with multiple columns."""
        await operations.create_index("ix_users_name", "users", ["first_name", "last_name"])
        
        sql = mock_adapter.execute.call_args[0][0]
        assert "first_name, last_name" in sql
    
    @pytest.mark.asyncio
    async def test_create_index_if_not_exists(self, operations, mock_adapter):
        """Test create_index with IF NOT EXISTS."""
        await operations.create_index("ix_test", "users", ["email"], if_not_exists=True)
        
        sql = mock_adapter.execute.call_args[0][0]
        assert "IF NOT EXISTS" in sql
    
    @pytest.mark.asyncio
    async def test_drop_index(self, operations, mock_adapter):
        """Test drop_index operation."""
        await operations.drop_index("ix_users_email")
        
        sql = mock_adapter.execute.call_args[0][0]
        assert "DROP INDEX" in sql
        assert "ix_users_email" in sql
    
    @pytest.mark.asyncio
    async def test_drop_index_if_exists(self, operations, mock_adapter):
        """Test drop_index with IF EXISTS."""
        await operations.drop_index("ix_users_email", if_exists=True)
        
        sql = mock_adapter.execute.call_args[0][0]
        assert "IF EXISTS" in sql


# =============================================================================
# Constraint Operations Tests
# =============================================================================

class TestConstraintOperations:
    """Tests for constraint operations."""
    
    @pytest.mark.asyncio
    async def test_add_foreign_key_postgresql(self, mock_adapter):
        """Test add_foreign_key for PostgreSQL."""
        ops = Operations()
        ops.configure(mock_adapter, dialect="postgresql", dry_run=False)
        
        await ops.add_foreign_key("fk_posts_user", "posts", "user_id", "users")
        
        sql = mock_adapter.execute.call_args[0][0]
        assert "ADD CONSTRAINT fk_posts_user" in sql
        assert "FOREIGN KEY (user_id) REFERENCES users(id)" in sql
    
    @pytest.mark.asyncio
    async def test_add_foreign_key_on_delete(self, mock_adapter):
        """Test add_foreign_key with ON DELETE."""
        ops = Operations()
        ops.configure(mock_adapter, dialect="postgresql", dry_run=False)
        
        await ops.add_foreign_key("fk_posts_user", "posts", "user_id", "users", on_delete="SET NULL")
        
        sql = mock_adapter.execute.call_args[0][0]
        assert "ON DELETE SET NULL" in sql
    
    @pytest.mark.asyncio
    async def test_add_foreign_key_sqlite(self, operations, mock_adapter):
        """Test add_foreign_key for SQLite (not supported)."""
        await operations.add_foreign_key("fk_posts_user", "posts", "user_id", "users")
        
        sql = mock_adapter.execute.call_args[0][0]
        assert "SQLite" in sql
    
    @pytest.mark.asyncio
    async def test_drop_constraint_postgresql(self, mock_adapter):
        """Test drop_constraint for PostgreSQL."""
        ops = Operations()
        ops.configure(mock_adapter, dialect="postgresql", dry_run=False)
        
        await ops.drop_constraint("posts", "fk_posts_user")
        
        sql = mock_adapter.execute.call_args[0][0]
        assert "DROP CONSTRAINT fk_posts_user" in sql


# =============================================================================
# Data Operations Tests
# =============================================================================

class TestDataOperations:
    """Tests for data operations."""
    
    @pytest.mark.asyncio
    async def test_execute(self, operations, mock_adapter):
        """Test execute operation."""
        await operations.execute("UPDATE users SET role = $1 WHERE id = $2", "admin", 1)
        
        mock_adapter.execute.assert_called_once()
        call_args = mock_adapter.execute.call_args
        assert "UPDATE users SET role = $1 WHERE id = $2" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_fetch(self, operations, mock_adapter):
        """Test fetch operation."""
        mock_adapter.fetch_all.return_value = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]
        
        rows = []
        async for row in operations.fetch("SELECT * FROM users"):
            rows.append(row)
        
        assert len(rows) == 2
        assert rows[0]["name"] == "Alice"
    
    @pytest.mark.asyncio
    async def test_fetch_one(self, operations, mock_adapter):
        """Test fetch_one operation."""
        mock_adapter.fetch_one.return_value = {"id": 1, "name": "Alice"}
        
        row = await operations.fetch_one("SELECT * FROM users WHERE id = $1", 1)
        
        assert row["name"] == "Alice"
    
    @pytest.mark.asyncio
    async def test_fetch_one_none(self, operations, mock_adapter):
        """Test fetch_one returns None when no result."""
        mock_adapter.fetch_one.return_value = None
        
        row = await operations.fetch_one("SELECT * FROM users WHERE id = $1", 999)
        
        assert row is None
    
    @pytest.mark.asyncio
    async def test_fetch_val(self, operations, mock_adapter):
        """Test fetch_val operation."""
        mock_adapter.fetch_one.return_value = {"count": 42}
        
        val = await operations.fetch_val("SELECT COUNT(*) FROM users")
        
        assert val == 42
    
    @pytest.mark.asyncio
    async def test_fetch_val_none(self, operations, mock_adapter):
        """Test fetch_val returns None when no result."""
        mock_adapter.fetch_one.return_value = None
        
        val = await operations.fetch_val("SELECT COUNT(*) FROM empty_table")
        
        assert val is None
    
    @pytest.mark.asyncio
    async def test_bulk_insert(self, operations, mock_adapter):
        """Test bulk_insert operation."""
        await operations.bulk_insert("users", [
            {"name": "Alice", "email": "alice@example.com"},
            {"name": "Bob", "email": "bob@example.com"},
        ])
        
        assert mock_adapter.execute.call_count == 2
    
    @pytest.mark.asyncio
    async def test_bulk_insert_empty(self, operations, mock_adapter):
        """Test bulk_insert with empty list."""
        count = await operations.bulk_insert("users", [])
        
        assert count == 0
        mock_adapter.execute.assert_not_called()


# =============================================================================
# Dry-Run Mode Tests
# =============================================================================

class TestDryRunMode:
    """Tests for dry-run mode."""
    
    @pytest.mark.asyncio
    async def test_dry_run_collects_sql(self, dry_run_ops):
        """Test dry-run mode collects SQL."""
        await dry_run_ops.create_table("users", {"id": "integer"})
        
        assert len(dry_run_ops.sql_statements) == 1
        assert "CREATE TABLE" in dry_run_ops.sql_statements[0]
    
    @pytest.mark.asyncio
    async def test_dry_run_doesnt_execute(self, dry_run_ops, mock_adapter):
        """Test dry-run mode doesn't execute SQL."""
        await dry_run_ops.create_table("users", {"id": "integer"})
        
        # Adapter should not be called
        mock_adapter.execute.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_dry_run_multiple_statements(self, dry_run_ops):
        """Test dry-run mode collects multiple statements."""
        await dry_run_ops.create_table("users", {"id": "integer"})
        await dry_run_ops.add_column("users", "name", "varchar(255)")
        await dry_run_ops.create_index("ix_users_name", "users", ["name"])
        
        assert len(dry_run_ops.sql_statements) == 3
    
    @pytest.mark.asyncio
    async def test_dry_run_execute_with_params(self, dry_run_ops):
        """Test dry-run mode formats execute with params."""
        await dry_run_ops.execute("UPDATE users SET role = $1 WHERE id = $2", "admin", 1)
        
        sql = dry_run_ops.sql_statements[0]
        assert "'admin'" in sql
        assert "1" in sql
    
    @pytest.mark.asyncio
    async def test_dry_run_fetch_returns_empty(self, dry_run_ops):
        """Test dry-run mode fetch returns nothing."""
        rows = []
        async for row in dry_run_ops.fetch("SELECT * FROM users"):
            rows.append(row)
        
        assert rows == []


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestErrorHandling:
    """Tests for error handling."""
    
    @pytest.mark.asyncio
    async def test_execute_without_adapter(self):
        """Test execute raises error without adapter."""
        ops = Operations()
        
        with pytest.raises(RuntimeError, match="No adapter configured"):
            await ops.execute("SELECT 1")
    
    @pytest.mark.asyncio
    async def test_fetch_without_adapter(self):
        """Test fetch raises error without adapter."""
        ops = Operations()
        
        with pytest.raises(RuntimeError, match="No adapter configured"):
            async for _ in ops.fetch("SELECT 1"):
                pass


# =============================================================================
# SQL Formatting Tests
# =============================================================================

class TestSQLFormatting:
    """Tests for SQL formatting."""
    
    def test_format_sql_with_string_param(self, operations):
        """Test SQL formatting with string parameter."""
        formatted = operations._format_sql("SELECT * FROM users WHERE name = $1", ("Alice",))
        assert "'Alice'" in formatted
    
    def test_format_sql_with_int_param(self, operations):
        """Test SQL formatting with integer parameter."""
        formatted = operations._format_sql("SELECT * FROM users WHERE id = $1", (42,))
        assert "42" in formatted
    
    def test_format_sql_with_multiple_params(self, operations):
        """Test SQL formatting with multiple parameters."""
        formatted = operations._format_sql(
            "UPDATE users SET name = $1, age = $2 WHERE id = $3",
            ("Alice", 30, 1)
        )
        assert "'Alice'" in formatted
        assert "30" in formatted
        assert "1" in formatted


# =============================================================================
# Global Instance Tests
# =============================================================================

class TestGlobalInstance:
    """Tests for global op instance."""
    
    def test_global_instance_exists(self):
        """Test global op instance exists."""
        assert op is not None
        assert isinstance(op, Operations)
    
    def test_global_instance_configurable(self, mock_adapter):
        """Test global op instance is configurable."""
        op.configure(mock_adapter, dialect="postgresql")
        assert op._dialect == "postgresql"

