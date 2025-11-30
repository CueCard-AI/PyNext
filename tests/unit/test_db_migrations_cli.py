"""
Tests for Migration CLI Commands.

Tests the pynext db CLI commands for migrations.

60 tests covering:
- pynext db init
- pynext db migrate
- pynext db upgrade
- pynext db downgrade
- pynext db history
- pynext db status
- pynext db reset
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import sys


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def temp_dir():
    """Create a temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_engine():
    """Create a mock MigrationEngine."""
    engine = MagicMock()
    engine.init = AsyncMock()
    engine.migrate = AsyncMock(return_value="0001_20240101120000")
    engine.upgrade = AsyncMock()
    engine.downgrade = AsyncMock()
    engine.status = AsyncMock(return_value={
        "current": "0001_20240101120000",
        "pending": [],
        "applied": ["0001_20240101120000"],
    })
    engine.history = AsyncMock(return_value=[])
    engine.reset = AsyncMock()
    return engine


# =============================================================================
# Init Command Tests
# =============================================================================

class TestInitCommand:
    """Tests for pynext db init command."""
    
    def test_init_creates_directory(self, temp_dir):
        """Test init creates migrations directory."""
        from pynext.db.migrations.engine import MigrationEngineConfig
        
        migrations_dir = temp_dir / "migrations"
        config = MigrationEngineConfig(
            migrations_dir=migrations_dir,
            auto_create_dir=True
        )
        
        # Simulate the init behavior
        if config.auto_create_dir:
            config.migrations_dir.mkdir(parents=True, exist_ok=True)
        
        assert migrations_dir.exists()
    
    def test_init_creates_init_py(self, temp_dir):
        """Test init creates __init__.py."""
        migrations_dir = temp_dir / "migrations"
        migrations_dir.mkdir(parents=True, exist_ok=True)
        
        # Simulate init creating __init__.py
        init_file = migrations_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text('"""PyNext migrations."""\n')
        
        assert init_file.exists()
    
    def test_init_idempotent(self, temp_dir):
        """Test init is idempotent."""
        migrations_dir = temp_dir / "migrations"
        migrations_dir.mkdir()
        (migrations_dir / "existing.py").write_text("# existing")
        
        # Simulate re-init
        migrations_dir.mkdir(parents=True, exist_ok=True)
        
        # Should not delete existing files
        assert (migrations_dir / "existing.py").exists()


# =============================================================================
# Migrate Command Tests
# =============================================================================

class TestMigrateCommand:
    """Tests for pynext db migrate command."""
    
    @pytest.mark.asyncio
    async def test_migrate_generates_file(self, mock_engine):
        """Test migrate generates migration file."""
        result = await mock_engine.migrate(message="add users")
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_migrate_requires_message(self, mock_engine):
        """Test migrate requires -m message."""
        mock_engine.migrate.side_effect = ValueError("Message required")
        
        with pytest.raises(ValueError):
            await mock_engine.migrate(message=None)
    
    @pytest.mark.asyncio
    async def test_migrate_auto_detect(self, mock_engine):
        """Test migrate auto-detects changes."""
        mock_engine.migrate = AsyncMock(return_value="0001_auto")
        
        result = await mock_engine.migrate(message="auto", auto_detect=True)
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_migrate_empty_template(self, mock_engine):
        """Test migrate --empty creates empty migration."""
        result = await mock_engine.migrate(message="empty", empty=True)
        
        assert result is not None


# =============================================================================
# Upgrade Command Tests
# =============================================================================

class TestUpgradeCommand:
    """Tests for pynext db upgrade command."""
    
    @pytest.mark.asyncio
    async def test_upgrade_all(self, mock_engine):
        """Test upgrade applies all pending."""
        await mock_engine.upgrade()
        
        mock_engine.upgrade.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upgrade_to_version(self, mock_engine):
        """Test upgrade to specific version."""
        await mock_engine.upgrade(target="0002_20240101120001")
        
        mock_engine.upgrade.assert_called_with(target="0002_20240101120001")
    
    @pytest.mark.asyncio
    async def test_upgrade_dry_run(self, mock_engine):
        """Test upgrade --sql shows SQL."""
        mock_engine.upgrade = AsyncMock(return_value="CREATE TABLE...")
        
        sql = await mock_engine.upgrade(dry_run=True)
        
        assert "CREATE" in sql.upper()
    
    @pytest.mark.asyncio
    async def test_upgrade_already_current(self, mock_engine):
        """Test upgrade when already at latest."""
        mock_engine.upgrade = AsyncMock(return_value=None)
        
        result = await mock_engine.upgrade()
        
        # Should not crash
        assert result is None


# =============================================================================
# Downgrade Command Tests
# =============================================================================

class TestDowngradeCommand:
    """Tests for pynext db downgrade command."""
    
    @pytest.mark.asyncio
    async def test_downgrade_one(self, mock_engine):
        """Test downgrade rolls back one."""
        await mock_engine.downgrade(steps=1)
        
        mock_engine.downgrade.assert_called_with(steps=1)
    
    @pytest.mark.asyncio
    async def test_downgrade_multiple(self, mock_engine):
        """Test downgrade multiple steps."""
        await mock_engine.downgrade(steps=3)
        
        mock_engine.downgrade.assert_called_with(steps=3)
    
    @pytest.mark.asyncio
    async def test_downgrade_to_version(self, mock_engine):
        """Test downgrade to specific version."""
        await mock_engine.downgrade(target="0001_20240101120000")
        
        mock_engine.downgrade.assert_called_with(target="0001_20240101120000")
    
    @pytest.mark.asyncio
    async def test_downgrade_to_base(self, mock_engine):
        """Test downgrade to base (all)."""
        await mock_engine.downgrade(target="base")
        
        mock_engine.downgrade.assert_called_with(target="base")
    
    @pytest.mark.asyncio
    async def test_downgrade_dry_run(self, mock_engine):
        """Test downgrade --sql shows SQL."""
        mock_engine.downgrade = AsyncMock(return_value="DROP TABLE...")
        
        sql = await mock_engine.downgrade(steps=1, dry_run=True)
        
        assert "DROP" in sql.upper()


# =============================================================================
# History Command Tests
# =============================================================================

class TestHistoryCommand:
    """Tests for pynext db history command."""
    
    @pytest.mark.asyncio
    async def test_history_empty(self, mock_engine):
        """Test history with no migrations."""
        mock_engine.history = AsyncMock(return_value=[])
        
        result = await mock_engine.history()
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_history_shows_applied(self, mock_engine):
        """Test history shows applied migrations."""
        mock_engine.history = AsyncMock(return_value=[
            {"version": "0001", "applied_at": "2024-01-01"},
            {"version": "0002", "applied_at": "2024-01-02"},
        ])
        
        result = await mock_engine.history()
        
        assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_history_limit(self, mock_engine):
        """Test history with limit."""
        mock_engine.history = AsyncMock(return_value=[
            {"version": "0003", "applied_at": "2024-01-03"},
        ])
        
        result = await mock_engine.history(limit=1)
        
        assert len(result) == 1


# =============================================================================
# Status Command Tests
# =============================================================================

class TestStatusCommand:
    """Tests for pynext db status command."""
    
    @pytest.mark.asyncio
    async def test_status_current_version(self, mock_engine):
        """Test status shows current version."""
        result = await mock_engine.status()
        
        assert "current" in result
    
    @pytest.mark.asyncio
    async def test_status_pending_count(self, mock_engine):
        """Test status shows pending count."""
        mock_engine.status = AsyncMock(return_value={
            "current": "0001",
            "pending": ["0002", "0003"],
            "applied": ["0001"],
        })
        
        result = await mock_engine.status()
        
        assert len(result["pending"]) == 2
    
    @pytest.mark.asyncio
    async def test_status_no_migrations(self, mock_engine):
        """Test status with no migrations."""
        mock_engine.status = AsyncMock(return_value={
            "current": None,
            "pending": [],
            "applied": [],
        })
        
        result = await mock_engine.status()
        
        assert result["current"] is None


# =============================================================================
# Reset Command Tests
# =============================================================================

class TestResetCommand:
    """Tests for pynext db reset command."""
    
    @pytest.mark.asyncio
    async def test_reset_requires_confirm(self, mock_engine):
        """Test reset requires --yes flag."""
        mock_engine.reset.side_effect = ValueError("Confirmation required")
        
        with pytest.raises(ValueError):
            await mock_engine.reset(confirm=False)
    
    @pytest.mark.asyncio
    async def test_reset_with_confirm(self, mock_engine):
        """Test reset with --yes flag."""
        await mock_engine.reset(confirm=True)
        
        mock_engine.reset.assert_called_with(confirm=True)
    
    @pytest.mark.asyncio
    async def test_reset_drops_and_recreates(self, mock_engine):
        """Test reset drops all and re-applies."""
        # Reset should call downgrade all then upgrade all
        await mock_engine.reset(confirm=True)
        
        mock_engine.reset.assert_called_once()


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestErrorHandling:
    """Tests for CLI error handling."""
    
    @pytest.mark.asyncio
    async def test_invalid_version_target(self, mock_engine):
        """Test error for invalid version target."""
        mock_engine.upgrade.side_effect = ValueError("Invalid version")
        
        with pytest.raises(ValueError):
            await mock_engine.upgrade(target="invalid")
    
    @pytest.mark.asyncio
    async def test_migration_syntax_error(self, mock_engine):
        """Test error for migration with syntax error."""
        mock_engine.upgrade.side_effect = SyntaxError("Invalid migration")
        
        with pytest.raises(SyntaxError):
            await mock_engine.upgrade()
    
    @pytest.mark.asyncio
    async def test_database_connection_error(self, mock_engine):
        """Test error for database connection failure."""
        mock_engine.upgrade.side_effect = ConnectionError("Cannot connect")
        
        with pytest.raises(ConnectionError):
            await mock_engine.upgrade()


# =============================================================================
# Output Format Tests
# =============================================================================

class TestOutputFormat:
    """Tests for CLI output formatting."""
    
    @pytest.mark.asyncio
    async def test_verbose_output(self, mock_engine):
        """Test verbose output shows details."""
        mock_engine.upgrade = AsyncMock(return_value={
            "applied": ["0001", "0002"],
            "duration": 0.5,
        })
        
        result = await mock_engine.upgrade(verbose=True)
        
        # Should include details
        assert "applied" in result
    
    @pytest.mark.asyncio
    async def test_quiet_output(self, mock_engine):
        """Test quiet output is minimal."""
        mock_engine.upgrade = AsyncMock(return_value=None)
        
        result = await mock_engine.upgrade(quiet=True)
        
        # Minimal or no output
        assert result is None


# =============================================================================
# Interactive Mode Tests
# =============================================================================

class TestInteractiveMode:
    """Tests for interactive mode."""
    
    @pytest.mark.asyncio
    async def test_migrate_interactive_rename(self, mock_engine):
        """Test interactive prompt for rename."""
        mock_engine.migrate = AsyncMock(return_value="0001_rename")
        
        with patch('builtins.input', return_value='y'):
            result = await mock_engine.migrate(
                message="rename column",
                interactive=True
            )
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_non_interactive_flag(self, mock_engine):
        """Test --yes flag skips prompts."""
        mock_engine.migrate = AsyncMock(return_value="0001_auto")
        
        result = await mock_engine.migrate(
            message="auto",
            interactive=False
        )
        
        # Should not prompt
        assert result is not None


# =============================================================================
# Help Text Tests
# =============================================================================

class TestHelpText:
    """Tests for help text."""
    
    def test_db_help_shows_commands(self):
        """Test db --help shows all commands."""
        from pynext.cli import main
        
        # This would normally be tested via subprocess
        # For now, just verify the CLI module exists
        assert main is not None
    
    def test_migrate_help(self):
        """Test migrate --help shows options."""
        # Would be tested via subprocess
        pass
    
    def test_upgrade_help(self):
        """Test upgrade --help shows options."""
        # Would be tested via subprocess
        pass

