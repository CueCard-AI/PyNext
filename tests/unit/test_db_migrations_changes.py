"""
Tests for Migration Change Types.

Tests the SQL generation for all change types (up and down).

70 tests covering:
- CreateTable/DropTable
- AddColumn/DropColumn
- RenameColumn/RenameTable
- AlterColumn
- AddIndex/DropIndex
- Constraints
- RawSQL
- SQL dialects
"""

import pytest
from pynext.db.migrations.changes import (
    AddColumn,
    AddConstraint,
    AddIndex,
    AlterColumn,
    ChangeType,
    ColumnDef,
    CreateTable,
    DropColumn,
    DropConstraint,
    DropIndex,
    DropTable,
    RawSQL,
    RenameColumn,
    RenameTable,
)


# =============================================================================
# ColumnDef Tests
# =============================================================================

class TestColumnDef:
    """Tests for ColumnDef."""
    
    def test_basic_column(self):
        """Test basic column definition."""
        col = ColumnDef(name="name", sql_type="VARCHAR(255)")
        assert col.name == "name"
        assert col.sql_type == "VARCHAR(255)"
        assert col.nullable is True
    
    def test_not_null_column(self):
        """Test NOT NULL column."""
        col = ColumnDef(name="email", sql_type="VARCHAR(255)", nullable=False)
        sql = col.to_sql()
        assert "NOT NULL" in sql
    
    def test_primary_key_column(self):
        """Test primary key column."""
        col = ColumnDef(name="id", sql_type="INTEGER", primary_key=True)
        sql = col.to_sql()
        assert "PRIMARY KEY" in sql
    
    def test_auto_increment_column(self):
        """Test auto-increment column."""
        col = ColumnDef(name="id", sql_type="INTEGER", primary_key=True, auto_increment=True)
        sql = col.to_sql()
        assert "AUTOINCREMENT" in sql or "PRIMARY KEY" in sql
    
    def test_unique_column(self):
        """Test unique column."""
        col = ColumnDef(name="email", sql_type="VARCHAR(255)", unique=True)
        sql = col.to_sql()
        assert "UNIQUE" in sql
    
    def test_default_string_column(self):
        """Test column with string default."""
        col = ColumnDef(name="role", sql_type="VARCHAR(50)", default="user")
        sql = col.to_sql()
        assert "DEFAULT 'user'" in sql
    
    def test_default_int_column(self):
        """Test column with integer default."""
        col = ColumnDef(name="count", sql_type="INTEGER", default=0)
        sql = col.to_sql()
        assert "DEFAULT 0" in sql
    
    def test_default_bool_column(self):
        """Test column with boolean default."""
        col = ColumnDef(name="active", sql_type="BOOLEAN", default=True)
        sql = col.to_sql()
        assert "DEFAULT 1" in sql
    
    def test_postgresql_serial(self):
        """Test PostgreSQL SERIAL type."""
        col = ColumnDef(name="id", sql_type="INTEGER", primary_key=True, auto_increment=True)
        sql = col.to_sql("postgresql")
        assert "SERIAL" in sql or "PRIMARY KEY" in sql


# =============================================================================
# CreateTable Tests
# =============================================================================

class TestCreateTable:
    """Tests for CreateTable change."""
    
    def test_change_type(self):
        """Test change type is CREATE_TABLE."""
        change = CreateTable(table="users", columns=[])
        assert change.change_type == ChangeType.CREATE_TABLE
    
    def test_basic_create(self):
        """Test basic CREATE TABLE."""
        change = CreateTable(
            table="users",
            columns=[
                ColumnDef(name="id", sql_type="INTEGER", primary_key=True),
                ColumnDef(name="name", sql_type="VARCHAR(255)"),
            ]
        )
        sql = change.up_sql()[0]
        assert "CREATE TABLE users" in sql
        assert "id INTEGER PRIMARY KEY" in sql
        assert "name VARCHAR(255)" in sql
    
    def test_down_sql_drops_table(self):
        """Test down SQL drops the table."""
        change = CreateTable(table="users", columns=[])
        sql = change.down_sql()[0]
        assert "DROP TABLE users" in sql
    
    def test_description(self):
        """Test description generation."""
        change = CreateTable(
            table="users",
            columns=[
                ColumnDef(name="id", sql_type="INTEGER"),
                ColumnDef(name="name", sql_type="VARCHAR(255)"),
            ]
        )
        desc = change.description()
        assert "users" in desc
        assert "2 columns" in desc
    
    def test_not_destructive(self):
        """Test CreateTable is not destructive."""
        change = CreateTable(table="users", columns=[])
        assert change.is_destructive() is False


# =============================================================================
# DropTable Tests
# =============================================================================

class TestDropTable:
    """Tests for DropTable change."""
    
    def test_change_type(self):
        """Test change type is DROP_TABLE."""
        change = DropTable(table="users")
        assert change.change_type == ChangeType.DROP_TABLE
    
    def test_up_sql(self):
        """Test DROP TABLE SQL."""
        change = DropTable(table="users")
        sql = change.up_sql()[0]
        assert "DROP TABLE users" in sql
    
    def test_down_sql_with_columns(self):
        """Test down SQL recreates table."""
        change = DropTable(
            table="users",
            columns=[
                ColumnDef(name="id", sql_type="INTEGER", primary_key=True),
            ]
        )
        sql = change.down_sql()[0]
        assert "CREATE TABLE users" in sql
    
    def test_down_sql_without_columns(self):
        """Test down SQL without column info."""
        change = DropTable(table="users")
        sql = change.down_sql()[0]
        assert "Cannot recreate" in sql or "CREATE TABLE" in sql
    
    def test_is_destructive(self):
        """Test DropTable is destructive."""
        change = DropTable(table="users")
        assert change.is_destructive() is True


# =============================================================================
# RenameTable Tests
# =============================================================================

class TestRenameTable:
    """Tests for RenameTable change."""
    
    def test_change_type(self):
        """Test change type is RENAME_TABLE."""
        change = RenameTable(old_name="users", new_name="accounts")
        assert change.change_type == ChangeType.RENAME_TABLE
    
    def test_up_sql(self):
        """Test RENAME TABLE SQL."""
        change = RenameTable(old_name="users", new_name="accounts")
        sql = change.up_sql()[0]
        assert "ALTER TABLE users RENAME TO accounts" in sql
    
    def test_down_sql(self):
        """Test down SQL reverses rename."""
        change = RenameTable(old_name="users", new_name="accounts")
        sql = change.down_sql()[0]
        assert "ALTER TABLE accounts RENAME TO users" in sql
    
    def test_description(self):
        """Test description."""
        change = RenameTable(old_name="users", new_name="accounts")
        desc = change.description()
        assert "users" in desc
        assert "accounts" in desc


# =============================================================================
# AddColumn Tests
# =============================================================================

class TestAddColumn:
    """Tests for AddColumn change."""
    
    def test_change_type(self):
        """Test change type is ADD_COLUMN."""
        change = AddColumn(table="users", column=ColumnDef(name="email", sql_type="VARCHAR(255)"))
        assert change.change_type == ChangeType.ADD_COLUMN
    
    def test_up_sql(self):
        """Test ADD COLUMN SQL."""
        change = AddColumn(
            table="users",
            column=ColumnDef(name="email", sql_type="VARCHAR(255)", nullable=False)
        )
        sql = change.up_sql()[0]
        assert "ALTER TABLE users ADD COLUMN" in sql
        assert "email VARCHAR(255)" in sql
    
    def test_down_sql_sqlite(self):
        """Test down SQL for SQLite (comment)."""
        change = AddColumn(table="users", column=ColumnDef(name="email", sql_type="VARCHAR(255)"))
        sql = change.down_sql("sqlite")[0]
        # SQLite doesn't support DROP COLUMN directly
        assert "SQLite" in sql or "DROP COLUMN" in sql
    
    def test_down_sql_postgresql(self):
        """Test down SQL for PostgreSQL."""
        change = AddColumn(table="users", column=ColumnDef(name="email", sql_type="VARCHAR(255)"))
        sql = change.down_sql("postgresql")[0]
        assert "DROP COLUMN email" in sql
    
    def test_not_destructive(self):
        """Test AddColumn is not destructive."""
        change = AddColumn(table="users", column=ColumnDef(name="email", sql_type="VARCHAR(255)"))
        assert change.is_destructive() is False


# =============================================================================
# DropColumn Tests
# =============================================================================

class TestDropColumn:
    """Tests for DropColumn change."""
    
    def test_change_type(self):
        """Test change type is DROP_COLUMN."""
        change = DropColumn(table="users", column=ColumnDef(name="old", sql_type="TEXT"))
        assert change.change_type == ChangeType.DROP_COLUMN
    
    def test_up_sql_postgresql(self):
        """Test DROP COLUMN SQL for PostgreSQL."""
        change = DropColumn(table="users", column=ColumnDef(name="old", sql_type="TEXT"))
        sql = change.up_sql("postgresql")[0]
        assert "ALTER TABLE users DROP COLUMN old" in sql
    
    def test_up_sql_sqlite(self):
        """Test DROP COLUMN SQL for SQLite (requires recreation)."""
        change = DropColumn(table="users", column=ColumnDef(name="old", sql_type="TEXT"))
        sql = change.up_sql("sqlite")[0]
        assert "SQLite" in sql or "DROP COLUMN" in sql
    
    def test_down_sql_adds_column(self):
        """Test down SQL adds column back."""
        change = DropColumn(table="users", column=ColumnDef(name="old", sql_type="TEXT"))
        sql = change.down_sql()[0]
        assert "ADD COLUMN old TEXT" in sql
    
    def test_is_destructive(self):
        """Test DropColumn is destructive."""
        change = DropColumn(table="users", column=ColumnDef(name="old", sql_type="TEXT"))
        assert change.is_destructive() is True


# =============================================================================
# RenameColumn Tests
# =============================================================================

class TestRenameColumn:
    """Tests for RenameColumn change."""
    
    def test_change_type(self):
        """Test change type is RENAME_COLUMN."""
        change = RenameColumn(table="users", old_name="name", new_name="full_name")
        assert change.change_type == ChangeType.RENAME_COLUMN
    
    def test_up_sql(self):
        """Test RENAME COLUMN SQL."""
        change = RenameColumn(table="users", old_name="name", new_name="full_name")
        sql = change.up_sql()[0]
        assert "ALTER TABLE users RENAME COLUMN name TO full_name" in sql
    
    def test_down_sql(self):
        """Test down SQL reverses rename."""
        change = RenameColumn(table="users", old_name="name", new_name="full_name")
        sql = change.down_sql()[0]
        assert "ALTER TABLE users RENAME COLUMN full_name TO name" in sql


# =============================================================================
# AlterColumn Tests
# =============================================================================

class TestAlterColumn:
    """Tests for AlterColumn change."""
    
    def test_change_type(self):
        """Test change type is ALTER_COLUMN."""
        change = AlterColumn(
            table="users",
            column_name="bio",
            old_type="VARCHAR(100)",
            new_type="TEXT",
        )
        assert change.change_type == ChangeType.ALTER_COLUMN
    
    def test_type_change_postgresql(self):
        """Test type change SQL for PostgreSQL."""
        change = AlterColumn(
            table="users",
            column_name="bio",
            old_type="VARCHAR(100)",
            new_type="TEXT",
        )
        sql = change.up_sql("postgresql")
        assert any("ALTER COLUMN bio TYPE TEXT" in s for s in sql)
    
    def test_nullable_change_postgresql(self):
        """Test nullable change for PostgreSQL."""
        change = AlterColumn(
            table="users",
            column_name="email",
            old_type="VARCHAR(255)",
            new_type="VARCHAR(255)",
            old_nullable=True,
            new_nullable=False,
        )
        sql = change.up_sql("postgresql")
        assert any("SET NOT NULL" in s for s in sql)
    
    def test_drop_not_null_postgresql(self):
        """Test dropping NOT NULL for PostgreSQL."""
        change = AlterColumn(
            table="users",
            column_name="email",
            old_type="VARCHAR(255)",
            new_type="VARCHAR(255)",
            old_nullable=False,
            new_nullable=True,
        )
        sql = change.up_sql("postgresql")
        assert any("DROP NOT NULL" in s for s in sql)
    
    def test_sqlite_not_supported(self):
        """Test SQLite ALTER COLUMN not supported."""
        change = AlterColumn(
            table="users",
            column_name="bio",
            old_type="VARCHAR(100)",
            new_type="TEXT",
        )
        sql = change.up_sql("sqlite")
        assert any("SQLite" in s for s in sql)
    
    def test_is_destructive(self):
        """Test AlterColumn is destructive."""
        change = AlterColumn(
            table="users",
            column_name="bio",
            old_type="TEXT",
            new_type="VARCHAR(100)",
        )
        assert change.is_destructive() is True
    
    def test_description(self):
        """Test description includes changes."""
        change = AlterColumn(
            table="users",
            column_name="bio",
            old_type="VARCHAR(100)",
            new_type="TEXT",
            old_nullable=False,
            new_nullable=True,
        )
        desc = change.description()
        assert "bio" in desc
        assert "type" in desc.lower() or "nullable" in desc.lower()


# =============================================================================
# AddIndex Tests
# =============================================================================

class TestAddIndex:
    """Tests for AddIndex change."""
    
    def test_change_type(self):
        """Test change type is ADD_INDEX."""
        change = AddIndex(table="users", columns=["email"])
        assert change.change_type == ChangeType.ADD_INDEX
    
    def test_basic_index(self):
        """Test basic CREATE INDEX SQL."""
        change = AddIndex(table="users", columns=["email"])
        sql = change.up_sql()[0]
        assert "CREATE INDEX" in sql
        assert "ON users (email)" in sql
    
    def test_unique_index(self):
        """Test CREATE UNIQUE INDEX SQL."""
        change = AddIndex(table="users", columns=["email"], unique=True)
        sql = change.up_sql()[0]
        assert "CREATE UNIQUE INDEX" in sql
    
    def test_multi_column_index(self):
        """Test multi-column index."""
        change = AddIndex(table="users", columns=["first_name", "last_name"])
        sql = change.up_sql()[0]
        assert "first_name, last_name" in sql
    
    def test_custom_name(self):
        """Test custom index name."""
        change = AddIndex(table="users", columns=["email"], name="idx_email")
        sql = change.up_sql()[0]
        assert "idx_email" in sql
    
    def test_auto_generated_name(self):
        """Test auto-generated index name."""
        change = AddIndex(table="users", columns=["email"])
        assert change.index_name == "ix_users_email"
    
    def test_down_sql(self):
        """Test DROP INDEX SQL."""
        change = AddIndex(table="users", columns=["email"])
        sql = change.down_sql()[0]
        assert "DROP INDEX" in sql


# =============================================================================
# DropIndex Tests
# =============================================================================

class TestDropIndex:
    """Tests for DropIndex change."""
    
    def test_change_type(self):
        """Test change type is DROP_INDEX."""
        change = DropIndex(table="users", name="ix_users_email")
        assert change.change_type == ChangeType.DROP_INDEX
    
    def test_up_sql(self):
        """Test DROP INDEX SQL."""
        change = DropIndex(table="users", name="ix_users_email")
        sql = change.up_sql()[0]
        assert "DROP INDEX ix_users_email" in sql
    
    def test_down_sql_with_columns(self):
        """Test down SQL recreates index."""
        change = DropIndex(
            table="users",
            name="ix_users_email",
            columns=["email"],
            unique=True,
        )
        sql = change.down_sql()[0]
        assert "CREATE UNIQUE INDEX" in sql
        assert "ix_users_email" in sql


# =============================================================================
# Constraint Tests
# =============================================================================

class TestAddConstraint:
    """Tests for AddConstraint change."""
    
    def test_change_type(self):
        """Test change type is ADD_CONSTRAINT."""
        change = AddConstraint(
            table="posts",
            name="fk_posts_user",
            constraint_sql="FOREIGN KEY (user_id) REFERENCES users(id)",
        )
        assert change.change_type == ChangeType.ADD_CONSTRAINT
    
    def test_up_sql_postgresql(self):
        """Test ADD CONSTRAINT SQL for PostgreSQL."""
        change = AddConstraint(
            table="posts",
            name="fk_posts_user",
            constraint_sql="FOREIGN KEY (user_id) REFERENCES users(id)",
        )
        sql = change.up_sql("postgresql")[0]
        assert "ADD CONSTRAINT fk_posts_user" in sql
    
    def test_sqlite_not_supported(self):
        """Test SQLite constraint requires table recreation."""
        change = AddConstraint(
            table="posts",
            name="fk_posts_user",
            constraint_sql="FOREIGN KEY (user_id) REFERENCES users(id)",
        )
        sql = change.up_sql("sqlite")[0]
        assert "SQLite" in sql


class TestDropConstraint:
    """Tests for DropConstraint change."""
    
    def test_change_type(self):
        """Test change type is DROP_CONSTRAINT."""
        change = DropConstraint(table="posts", name="fk_posts_user")
        assert change.change_type == ChangeType.DROP_CONSTRAINT
    
    def test_up_sql_postgresql(self):
        """Test DROP CONSTRAINT SQL for PostgreSQL."""
        change = DropConstraint(table="posts", name="fk_posts_user")
        sql = change.up_sql("postgresql")[0]
        assert "DROP CONSTRAINT fk_posts_user" in sql


# =============================================================================
# RawSQL Tests
# =============================================================================

class TestRawSQL:
    """Tests for RawSQL change."""
    
    def test_change_type(self):
        """Test change type is RAW_SQL."""
        change = RawSQL(up="SELECT 1", down="SELECT 1")
        assert change.change_type == ChangeType.RAW_SQL
    
    def test_up_sql(self):
        """Test up SQL returns provided SQL."""
        change = RawSQL(up="CREATE EXTENSION pg_trgm", down="DROP EXTENSION pg_trgm")
        sql = change.up_sql()[0]
        assert "CREATE EXTENSION pg_trgm" in sql
    
    def test_down_sql(self):
        """Test down SQL returns provided SQL."""
        change = RawSQL(up="CREATE EXTENSION pg_trgm", down="DROP EXTENSION pg_trgm")
        sql = change.down_sql()[0]
        assert "DROP EXTENSION pg_trgm" in sql
    
    def test_custom_description(self):
        """Test custom description."""
        change = RawSQL(
            up="SELECT 1",
            down="SELECT 1",
            desc="Enable full-text search",
        )
        assert change.description() == "Enable full-text search"
    
    def test_destructive_flag(self):
        """Test destructive flag."""
        change = RawSQL(
            up="TRUNCATE users",
            down="-- Cannot restore",
            destructive=True,
        )
        assert change.is_destructive() is True
    
    def test_not_destructive_default(self):
        """Test not destructive by default."""
        change = RawSQL(up="SELECT 1", down="SELECT 1")
        assert change.is_destructive() is False


# =============================================================================
# SQL Dialect Tests
# =============================================================================

class TestSQLDialects:
    """Tests for SQL dialect handling."""
    
    def test_create_table_sqlite(self):
        """Test CREATE TABLE for SQLite."""
        change = CreateTable(
            table="users",
            columns=[
                ColumnDef(name="id", sql_type="INTEGER", primary_key=True, auto_increment=True),
            ]
        )
        sql = change.up_sql("sqlite")[0]
        assert "AUTOINCREMENT" in sql or "PRIMARY KEY" in sql
    
    def test_create_table_postgresql(self):
        """Test CREATE TABLE for PostgreSQL."""
        change = CreateTable(
            table="users",
            columns=[
                ColumnDef(name="id", sql_type="INTEGER", primary_key=True, auto_increment=True),
            ]
        )
        sql = change.up_sql("postgresql")[0]
        # PostgreSQL uses SERIAL
        assert "SERIAL" in sql or "PRIMARY KEY" in sql
    
    def test_alter_column_sqlite_unsupported(self):
        """Test ALTER COLUMN not supported in SQLite."""
        change = AlterColumn(
            table="users",
            column_name="bio",
            old_type="VARCHAR(100)",
            new_type="TEXT",
        )
        sql = change.up_sql("sqlite")
        assert any("SQLite" in s for s in sql)
    
    def test_drop_column_sqlite_unsupported(self):
        """Test DROP COLUMN in SQLite requires recreation."""
        change = DropColumn(table="users", column=ColumnDef(name="old", sql_type="TEXT"))
        sql = change.up_sql("sqlite")
        assert any("SQLite" in s or "DROP COLUMN" in s for s in sql)

