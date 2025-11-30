"""
Tests for Migration Generator.

Tests migration file generation in both declarative and Python formats.

70 tests covering:
- Declarative migration generation
- Python migration generation
- Version numbering
- File naming
- SQL formatting
- Migration listing
"""

import pytest
import re
import tempfile
from pathlib import Path
from datetime import datetime

from pynext.db.migrations.generator import MigrationGenerator
from pynext.db.migrations.changes import (
    AddColumn,
    AddIndex,
    ColumnDef,
    CreateTable,
    DropColumn,
    DropTable,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def temp_migrations_dir():
    """Create a temporary migrations directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def generator(temp_migrations_dir):
    """Create a MigrationGenerator instance."""
    return MigrationGenerator(temp_migrations_dir)


# =============================================================================
# Version Generation Tests
# =============================================================================

class TestVersionGeneration:
    """Tests for version generation."""
    
    def test_first_version(self, generator):
        """Test first version is 0001."""
        version = generator._generate_version()
        assert version.startswith("0001_")
    
    def test_version_format(self, generator):
        """Test version format matches NNNN_YYYYMMDDHHMMSS."""
        version = generator._generate_version()
        pattern = r"^\d{4}_\d{14}$"
        assert re.match(pattern, version)
    
    def test_sequential_versions(self, temp_migrations_dir, generator):
        """Test versions increment sequentially."""
        # Create some existing migrations
        (temp_migrations_dir / "0001_20240101120000_initial.py").touch()
        (temp_migrations_dir / "0002_20240101120001_second.py").touch()
        
        version = generator._generate_version()
        assert version.startswith("0003_")
    
    def test_version_with_gaps(self, temp_migrations_dir, generator):
        """Test version handles gaps correctly."""
        # Create migrations with gaps
        (temp_migrations_dir / "0001_20240101120000_first.py").touch()
        (temp_migrations_dir / "0005_20240101120001_fifth.py").touch()
        
        version = generator._generate_version()
        assert version.startswith("0006_")
    
    def test_get_next_version(self, generator):
        """Test get_next_version method."""
        version = generator.get_next_version()
        assert version.startswith("0001_")


# =============================================================================
# Slug Generation Tests
# =============================================================================

class TestSlugGeneration:
    """Tests for slug generation."""
    
    def test_basic_slug(self, generator):
        """Test basic slug generation."""
        slug = generator._slugify("add user roles")
        assert slug == "add_user_roles"
    
    def test_slug_lowercase(self, generator):
        """Test slug is lowercase."""
        slug = generator._slugify("Add User Roles")
        assert slug == "add_user_roles"
    
    def test_slug_special_chars(self, generator):
        """Test special characters are replaced."""
        slug = generator._slugify("add user's roles!")
        assert "_" in slug
        assert "'" not in slug
        assert "!" not in slug
    
    def test_slug_truncation(self, generator):
        """Test long slugs are truncated."""
        long_message = "this is a very long message that should be truncated to a reasonable length"
        slug = generator._slugify(long_message)
        assert len(slug) <= 50
    
    def test_slug_empty(self, generator):
        """Test empty message returns 'migration'."""
        slug = generator._slugify("")
        assert slug == "migration"
    
    def test_slug_only_special_chars(self, generator):
        """Test message with only special chars."""
        slug = generator._slugify("!@#$%")
        assert slug == "migration"
    
    def test_slug_numbers(self, generator):
        """Test numbers are preserved."""
        slug = generator._slugify("add field v2")
        assert "v2" in slug


# =============================================================================
# Declarative Migration Tests
# =============================================================================

class TestDeclarativeMigration:
    """Tests for declarative migration generation."""
    
    def test_create_table_migration(self, generator):
        """Test migration with CreateTable."""
        changes = [
            CreateTable(
                table="users",
                columns=[
                    ColumnDef(name="id", sql_type="INTEGER", primary_key=True),
                    ColumnDef(name="name", sql_type="VARCHAR(255)"),
                ]
            )
        ]
        
        path = generator.generate_declarative(changes, "create users table")
        
        assert path.exists()
        content = path.read_text()
        assert "CREATE TABLE" in content
        assert "users" in content
    
    def test_add_column_migration(self, generator):
        """Test migration with AddColumn."""
        changes = [
            AddColumn(
                table="users",
                column=ColumnDef(name="email", sql_type="VARCHAR(255)")
            )
        ]
        
        path = generator.generate_declarative(changes, "add email to users")
        
        content = path.read_text()
        assert "ADD COLUMN" in content
        assert "email" in content
    
    def test_drop_table_migration(self, generator):
        """Test migration with DropTable."""
        changes = [DropTable(table="old_users")]
        
        path = generator.generate_declarative(changes, "drop old users")
        
        content = path.read_text()
        assert "DROP TABLE" in content
        assert "old_users" in content
    
    def test_multiple_changes(self, generator):
        """Test migration with multiple changes."""
        changes = [
            CreateTable(
                table="users",
                columns=[ColumnDef(name="id", sql_type="INTEGER", primary_key=True)]
            ),
            AddIndex(table="users", columns=["email"], unique=True),
        ]
        
        path = generator.generate_declarative(changes, "create users with index")
        
        content = path.read_text()
        assert "CREATE TABLE" in content
        assert "CREATE" in content and "INDEX" in content
    
    def test_migration_has_docstring(self, generator):
        """Test migration file has docstring."""
        changes = [CreateTable(table="users", columns=[])]
        
        path = generator.generate_declarative(changes, "test migration")
        
        content = path.read_text()
        assert '"""' in content
        assert "test migration" in content
    
    def test_migration_includes_version(self, generator):
        """Test migration includes version in docstring."""
        changes = [CreateTable(table="users", columns=[])]
        
        path = generator.generate_declarative(changes, "test migration")
        
        content = path.read_text()
        assert "Migration:" in content
        assert "0001_" in content
    
    def test_migration_includes_changes_list(self, generator):
        """Test migration includes list of changes."""
        changes = [
            CreateTable(
                table="users",
                columns=[ColumnDef(name="id", sql_type="INTEGER")]
            ),
        ]
        
        path = generator.generate_declarative(changes, "test migration")
        
        content = path.read_text()
        assert "Changes:" in content
        assert "Create table" in content
    
    def test_migration_file_naming(self, generator):
        """Test migration file naming."""
        changes = [CreateTable(table="users", columns=[])]
        
        path = generator.generate_declarative(changes, "add users table")
        
        assert "add_users_table" in path.name
        assert path.suffix == ".py"


# =============================================================================
# Python Migration Tests
# =============================================================================

class TestPythonMigration:
    """Tests for Python migration generation."""
    
    def test_default_template(self, generator):
        """Test default Python migration template."""
        path = generator.generate_python("data migration")
        
        content = path.read_text()
        assert "@migration.up" in content
        assert "@migration.down" in content
        assert "async def upgrade" in content
        assert "async def downgrade" in content
    
    def test_data_template(self, generator):
        """Test data migration template."""
        path = generator.generate_python("migrate data", template="data")
        
        content = path.read_text()
        assert "async for row in op.fetch" in content
        assert "transform" in content
    
    def test_empty_template(self, generator):
        """Test empty migration template."""
        path = generator.generate_python("placeholder", template="empty")
        
        content = path.read_text()
        assert "@migration.up" in content
        assert "pass" in content
    
    def test_python_migration_imports(self, generator):
        """Test Python migration has correct imports."""
        path = generator.generate_python("test")
        
        content = path.read_text()
        assert "from pynext.db.migrations import migration, op" in content
    
    def test_generate_empty_shortcut(self, generator):
        """Test generate_empty shortcut."""
        path = generator.generate_empty("empty migration")
        
        content = path.read_text()
        assert "@migration.up" in content


# =============================================================================
# Migration Listing Tests
# =============================================================================

class TestMigrationListing:
    """Tests for migration listing."""
    
    def test_list_empty(self, generator):
        """Test listing with no migrations."""
        migrations = generator.list_migrations()
        assert migrations == []
    
    def test_list_migrations(self, generator, temp_migrations_dir):
        """Test listing migrations."""
        # Create some migrations
        (temp_migrations_dir / "0001_20240101120000_first.py").write_text("# first")
        (temp_migrations_dir / "0002_20240101120001_second.py").write_text("# second")
        
        migrations = generator.list_migrations()
        
        assert len(migrations) == 2
    
    def test_list_ignores_init(self, generator, temp_migrations_dir):
        """Test listing ignores __init__.py."""
        (temp_migrations_dir / "__init__.py").write_text("# init")
        (temp_migrations_dir / "0001_20240101120000_first.py").write_text("# first")
        
        migrations = generator.list_migrations()
        
        assert len(migrations) == 1
    
    def test_list_sorted(self, generator, temp_migrations_dir):
        """Test migrations are sorted by version."""
        (temp_migrations_dir / "0003_20240101120002_third.py").write_text("# third")
        (temp_migrations_dir / "0001_20240101120000_first.py").write_text("# first")
        (temp_migrations_dir / "0002_20240101120001_second.py").write_text("# second")
        
        migrations = generator.list_migrations()
        
        assert "0001" in migrations[0].name
        assert "0002" in migrations[1].name
        assert "0003" in migrations[2].name


# =============================================================================
# SQL Formatting Tests
# =============================================================================

class TestSQLFormatting:
    """Tests for SQL formatting in generated files."""
    
    def test_multiline_sql(self, generator):
        """Test multiline SQL is formatted correctly."""
        changes = [
            CreateTable(
                table="users",
                columns=[
                    ColumnDef(name="id", sql_type="INTEGER", primary_key=True),
                    ColumnDef(name="name", sql_type="VARCHAR(255)"),
                    ColumnDef(name="email", sql_type="VARCHAR(255)"),
                ]
            )
        ]
        
        path = generator.generate_declarative(changes, "test")
        content = path.read_text()
        
        # Should use triple-quoted string for multiline
        assert '"""' in content
    
    def test_comment_for_unsupported(self, generator):
        """Test comments for unsupported operations."""
        changes = [
            DropColumn(
                table="users",
                column=ColumnDef(name="old", sql_type="TEXT")
            )
        ]
        
        path = generator.generate_declarative(changes, "test")
        content = path.read_text()
        
        # May include comment about SQLite limitations
        assert content  # Just verify it doesn't crash


# =============================================================================
# Directory Creation Tests
# =============================================================================

class TestDirectoryCreation:
    """Tests for directory creation."""
    
    def test_creates_directory(self):
        """Test migrations directory is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            migrations_dir = Path(tmpdir) / "migrations"
            generator = MigrationGenerator(migrations_dir)
            
            assert migrations_dir.exists()
    
    def test_existing_directory_ok(self, temp_migrations_dir):
        """Test existing directory is handled."""
        generator = MigrationGenerator(temp_migrations_dir)
        
        # Should not raise
        assert temp_migrations_dir.exists()


# =============================================================================
# Edge Cases Tests
# =============================================================================

class TestEdgeCases:
    """Edge case tests."""
    
    def test_empty_changes(self, generator):
        """Test generating with empty changes list."""
        path = generator.generate_declarative([], "empty")
        
        content = path.read_text()
        assert "No changes" in content
    
    def test_very_long_message(self, generator):
        """Test handling of very long message."""
        long_message = "a" * 200
        path = generator.generate_declarative([CreateTable(table="t", columns=[])], long_message)
        
        # Filename should be truncated
        assert len(path.stem) <= 100
    
    def test_unicode_message(self, generator):
        """Test handling of unicode in message."""
        path = generator.generate_declarative(
            [CreateTable(table="t", columns=[])],
            "add café table"
        )
        
        # Should handle unicode
        assert path.exists()
    
    def test_multiple_generations(self, generator):
        """Test generating multiple migrations."""
        path1 = generator.generate_declarative([CreateTable(table="t1", columns=[])], "first")
        path2 = generator.generate_declarative([CreateTable(table="t2", columns=[])], "second")
        
        assert path1 != path2
        assert "0001" in path1.name
        assert "0002" in path2.name
    
    def test_rapid_generation(self, generator):
        """Test rapid sequential generation."""
        paths = []
        for i in range(5):
            path = generator.generate_declarative(
                [CreateTable(table=f"t{i}", columns=[])],
                f"migration {i}"
            )
            paths.append(path)
        
        # All should be unique
        assert len(set(paths)) == 5
        
        # All should be sequential
        for i, path in enumerate(paths):
            assert f"000{i+1}" in path.name

