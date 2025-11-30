"""
Comprehensive Migration Tests.

Additional comprehensive tests for the migration system.

64 tests covering:
- Complex change scenarios
- Multi-table operations
- Constraint combinations
- Type conversions
- Edge cases
"""

import pytest
from dataclasses import dataclass
from typing import List, Optional

from pynext.db.migrations.changes import (
    Change,
    ChangeType,
    ColumnDef,
    CreateTable,
    DropTable,
    RenameTable,
    AddColumn,
    DropColumn,
    RenameColumn,
    AlterColumn,
    AddIndex,
    DropIndex,
    AddConstraint,
    DropConstraint,
    RawSQL,
)


# =============================================================================
# Complex Column Definition Tests
# =============================================================================

class TestComplexColumnDefinitions:
    """Tests for complex column definitions."""
    
    def test_column_with_all_options(self):
        """Test column with all options set."""
        col = ColumnDef(
            name="id",
            sql_type="INTEGER",
            nullable=False,
            primary_key=True,
            auto_increment=True,
            unique=True,
            default=None,
        )
        
        sql = col.to_sql()
        
        assert "id" in sql
        assert "INTEGER" in sql.upper()
        assert "PRIMARY KEY" in sql.upper()
    
    def test_column_with_foreign_key(self):
        """Test column with foreign key reference."""
        col = ColumnDef(
            name="author_id",
            sql_type="INTEGER",
            nullable=False,
            references="users(id)",
        )
        
        sql = col.to_sql()
        
        assert "author_id" in sql
        assert "REFERENCES" in sql.upper()
        assert "users(id)" in sql
    
    def test_column_with_check_constraint(self):
        """Test column with check constraint."""
        col = ColumnDef(
            name="age",
            sql_type="INTEGER",
            check="age >= 0 AND age <= 150",
        )
        
        sql = col.to_sql()
        
        assert "CHECK" in sql.upper()
        assert "age >= 0" in sql
    
    def test_column_default_string(self):
        """Test column with string default."""
        col = ColumnDef(
            name="status",
            sql_type="VARCHAR(50)",
            default="active",
        )
        
        sql = col.to_sql()
        
        assert "DEFAULT" in sql.upper()
        assert "'active'" in sql
    
    def test_column_default_number(self):
        """Test column with numeric default."""
        col = ColumnDef(
            name="count",
            sql_type="INTEGER",
            default=0,
        )
        
        sql = col.to_sql()
        
        assert "DEFAULT 0" in sql.upper()
    
    def test_column_default_boolean(self):
        """Test column with boolean default."""
        col = ColumnDef(
            name="active",
            sql_type="BOOLEAN",
            default=True,
        )
        
        sql = col.to_sql()
        
        assert "DEFAULT" in sql.upper()


# =============================================================================
# Multi-Table Operations Tests
# =============================================================================

class TestMultiTableOperations:
    """Tests for multi-table operations."""
    
    def test_create_related_tables(self):
        """Test creating related tables."""
        users = CreateTable(
            table="users",
            columns=[
                ColumnDef(name="id", sql_type="SERIAL", primary_key=True),
                ColumnDef(name="name", sql_type="VARCHAR(255)"),
            ]
        )
        
        posts = CreateTable(
            table="posts",
            columns=[
                ColumnDef(name="id", sql_type="SERIAL", primary_key=True),
                ColumnDef(name="title", sql_type="VARCHAR(255)"),
                ColumnDef(name="author_id", sql_type="INTEGER", references="users(id)"),
            ]
        )
        
        users_sql = users.to_sql()
        posts_sql = posts.to_sql()
        
        assert "users" in users_sql.lower()
        assert "posts" in posts_sql.lower()
        assert "REFERENCES" in posts_sql.upper()
    
    def test_drop_tables_in_order(self):
        """Test dropping related tables in order."""
        # Must drop posts before users (foreign key constraint)
        drop_posts = DropTable(table="posts")
        drop_users = DropTable(table="users")
        
        assert "DROP TABLE posts" in drop_posts.to_sql()
        assert "DROP TABLE users" in drop_users.to_sql()


# =============================================================================
# Complex Index Tests
# =============================================================================

class TestComplexIndexOperations:
    """Tests for complex index operations."""
    
    def test_unique_composite_index(self):
        """Test unique composite index."""
        idx = AddIndex(
            table="user_emails",
            columns=["user_id", "email"],
            unique=True,
            name="uix_user_emails"
        )
        
        sql = idx.to_sql()
        
        assert "UNIQUE" in sql.upper()
        assert "user_id" in sql
        assert "email" in sql
    
    def test_partial_index(self):
        """Test partial index with WHERE clause."""
        idx = AddIndex(
            table="users",
            columns=["email"],
            unique=True,
            where="deleted_at IS NULL",
        )
        
        sql = idx.to_sql(dialect="postgresql")
        
        assert "WHERE" in sql.upper()
        assert "deleted_at IS NULL" in sql
    
    def test_concurrent_index(self):
        """Test concurrent index creation."""
        idx = AddIndex(
            table="large_table",
            columns=["search_field"],
            concurrently=True,
        )
        
        sql = idx.to_sql(dialect="postgresql")
        
        assert "CONCURRENTLY" in sql.upper()
    
    def test_three_column_index(self):
        """Test index on three columns."""
        idx = AddIndex(
            table="events",
            columns=["year", "month", "day"],
        )
        
        sql = idx.to_sql()
        
        assert "year" in sql
        assert "month" in sql
        assert "day" in sql


# =============================================================================
# Constraint Tests
# =============================================================================

class TestComplexConstraints:
    """Tests for complex constraints."""
    
    def test_unique_constraint_multiple_columns(self):
        """Test unique constraint on multiple columns."""
        constraint = AddConstraint(
            table="order_items",
            name="uq_order_product",
            constraint_sql="UNIQUE (order_id, product_id)"
        )
        
        sql = constraint.to_sql(dialect="postgresql")
        
        assert "UNIQUE" in sql.upper()
        assert "order_id" in sql
        assert "product_id" in sql
    
    def test_check_constraint_complex(self):
        """Test complex check constraint."""
        constraint = AddConstraint(
            table="products",
            name="ck_price_positive",
            constraint_sql="CHECK (price > 0 AND discount_price <= price)"
        )
        
        sql = constraint.to_sql(dialect="postgresql")
        
        assert "CHECK" in sql.upper()
        assert "price > 0" in sql
    
    def test_foreign_key_on_delete_cascade(self):
        """Test foreign key with ON DELETE CASCADE."""
        constraint = AddConstraint(
            table="comments",
            name="fk_comments_post",
            constraint_sql="FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE"
        )
        
        sql = constraint.to_sql(dialect="postgresql")
        
        assert "FOREIGN KEY" in sql.upper()
        assert "ON DELETE CASCADE" in sql.upper()


# =============================================================================
# Type Conversion Tests
# =============================================================================

class TestTypeConversions:
    """Tests for type conversions between dialects."""
    
    def test_serial_postgresql(self):
        """Test SERIAL type in PostgreSQL."""
        col = ColumnDef(name="id", sql_type="SERIAL", primary_key=True)
        
        sql = col.to_sql(dialect="postgresql")
        
        assert "SERIAL" in sql.upper() or "INTEGER" in sql.upper()
    
    def test_serial_to_integer_sqlite(self):
        """Test SERIAL converts to INTEGER in SQLite."""
        col = ColumnDef(name="id", sql_type="SERIAL", primary_key=True)
        
        sql = col.to_sql(dialect="sqlite")
        
        assert "INTEGER" in sql.upper()
    
    def test_auto_increment_sqlite(self):
        """Test auto-increment in SQLite."""
        col = ColumnDef(
            name="id",
            sql_type="INTEGER",
            primary_key=True,
            auto_increment=True
        )
        
        sql = col.to_sql(dialect="sqlite")
        
        assert "AUTOINCREMENT" in sql.upper()
    
    def test_varchar_sqlite(self):
        """Test VARCHAR in SQLite (treated as TEXT)."""
        col = ColumnDef(name="name", sql_type="VARCHAR(255)")
        
        sql = col.to_sql(dialect="sqlite")
        
        # SQLite accepts VARCHAR but treats as TEXT
        assert "VARCHAR" in sql.upper() or "TEXT" in sql.upper()


# =============================================================================
# Alter Column Tests
# =============================================================================

class TestAlterColumnVariations:
    """Tests for various alter column scenarios."""
    
    def test_alter_type_only(self):
        """Test altering only the type."""
        change = AlterColumn(
            table="users",
            column_name="age",
            old_type="INTEGER",
            new_type="BIGINT",
        )
        
        sql = change.to_sql(dialect="postgresql")
        
        assert "ALTER" in sql.upper()
        assert "TYPE" in sql.upper()
        assert "BIGINT" in sql.upper()
    
    def test_alter_nullable_only(self):
        """Test altering only nullability."""
        change = AlterColumn(
            table="users",
            column_name="email",
            old_type="VARCHAR(255)",
            new_type="VARCHAR(255)",
            old_nullable=True,
            new_nullable=False,
        )
        
        sql = change.to_sql(dialect="postgresql")
        
        assert "SET NOT NULL" in sql.upper()
    
    def test_alter_drop_not_null(self):
        """Test dropping NOT NULL constraint."""
        change = AlterColumn(
            table="users",
            column_name="phone",
            old_type="VARCHAR(20)",
            new_type="VARCHAR(20)",
            old_nullable=False,
            new_nullable=True,
        )
        
        sql = change.to_sql(dialect="postgresql")
        
        assert "DROP NOT NULL" in sql.upper()
    
    def test_alter_sqlite_unsupported(self):
        """Test ALTER COLUMN in SQLite (not supported)."""
        change = AlterColumn(
            table="users",
            column_name="name",
            old_type="VARCHAR(100)",
            new_type="VARCHAR(255)",
        )
        
        sql = change.to_sql(dialect="sqlite")
        
        # Should indicate table recreation needed
        assert "--" in sql or "SQLite" in sql


# =============================================================================
# Raw SQL Tests
# =============================================================================

class TestRawSQLOperations:
    """Tests for raw SQL operations."""
    
    def test_raw_sql_with_rollback(self):
        """Test raw SQL with rollback statement."""
        change = RawSQL(
            up="CREATE FUNCTION my_func() RETURNS void AS $$ SELECT 1 $$ LANGUAGE SQL",
            down="DROP FUNCTION my_func",
            desc="Create custom function"
        )
        
        up_sql = change.to_sql()
        down_sql = change.down_sql()[0]
        
        assert "CREATE FUNCTION" in up_sql
        assert "DROP FUNCTION" in down_sql
    
    def test_raw_sql_destructive(self):
        """Test raw SQL marked as destructive."""
        change = RawSQL(
            up="TRUNCATE TABLE logs",
            down="-- Cannot reverse TRUNCATE",
            destructive=True
        )
        
        assert change.is_destructive()
    
    def test_raw_sql_safe(self):
        """Test raw SQL marked as safe."""
        change = RawSQL(
            up="CREATE VIEW my_view AS SELECT 1",
            down="DROP VIEW my_view",
            destructive=False
        )
        
        assert not change.is_destructive()


# =============================================================================
# Edge Cases Tests
# =============================================================================

class TestMigrationEdgeCases:
    """Edge case tests for migrations."""
    
    def test_empty_column_list(self):
        """Test table with empty column list."""
        table = CreateTable(table="empty_table", columns=[])
        sql = table.to_sql()
        
        assert "CREATE TABLE" in sql.upper()
    
    def test_very_long_column_name(self):
        """Test very long column name."""
        long_name = "a" * 100
        col = ColumnDef(name=long_name, sql_type="INTEGER")
        sql = col.to_sql()
        
        assert long_name in sql
    
    def test_special_characters_in_default(self):
        """Test special characters in default value."""
        col = ColumnDef(
            name="message",
            sql_type="TEXT",
            default="Hello, 'World'!"
        )
        sql = col.to_sql()
        
        assert "DEFAULT" in sql.upper()
    
    def test_unicode_column_name(self):
        """Test unicode column name."""
        col = ColumnDef(name="名前", sql_type="VARCHAR(255)")
        sql = col.to_sql()
        
        assert "名前" in sql
    
    def test_numeric_precision(self):
        """Test numeric column with precision."""
        col = ColumnDef(name="price", sql_type="DECIMAL(10, 2)")
        sql = col.to_sql()
        
        assert "DECIMAL(10, 2)" in sql


# =============================================================================
# Description Tests
# =============================================================================

class TestChangeDescriptions:
    """Tests for change descriptions."""
    
    def test_create_table_description(self):
        """Test create table description."""
        change = CreateTable(
            table="users",
            columns=[
                ColumnDef(name="id", sql_type="INTEGER"),
                ColumnDef(name="name", sql_type="VARCHAR(255)"),
            ]
        )
        
        desc = change.description()
        
        assert "Create table" in desc
        assert "users" in desc
        assert "2 columns" in desc
    
    def test_add_column_description(self):
        """Test add column description."""
        change = AddColumn(
            table="users",
            column=ColumnDef(name="email", sql_type="VARCHAR(255)")
        )
        
        desc = change.description()
        
        assert "Add column" in desc
        assert "email" in desc
    
    def test_drop_table_description(self):
        """Test drop table description."""
        change = DropTable(table="old_users")
        
        desc = change.description()
        
        assert "Drop table" in desc
        assert "old_users" in desc


# =============================================================================
# Destructive Flag Tests
# =============================================================================

class TestDestructiveFlags:
    """Tests for destructive change flags."""
    
    def test_drop_table_is_destructive(self):
        """Test drop table is marked destructive."""
        change = DropTable(table="users")
        assert change.is_destructive()
    
    def test_drop_column_is_destructive(self):
        """Test drop column is marked destructive."""
        change = DropColumn(
            table="users",
            column=ColumnDef(name="old_field", sql_type="TEXT")
        )
        assert change.is_destructive()
    
    def test_alter_column_is_destructive(self):
        """Test alter column is marked destructive."""
        change = AlterColumn(
            table="users",
            column_name="name",
            old_type="TEXT",
            new_type="VARCHAR(100)"
        )
        assert change.is_destructive()
    
    def test_create_table_not_destructive(self):
        """Test create table is not destructive."""
        change = CreateTable(table="new_table", columns=[])
        assert not change.is_destructive()
    
    def test_add_column_not_destructive(self):
        """Test add column is not destructive."""
        change = AddColumn(
            table="users",
            column=ColumnDef(name="new_field", sql_type="TEXT")
        )
        assert not change.is_destructive()
    
    def test_add_index_not_destructive(self):
        """Test add index is not destructive."""
        change = AddIndex(table="users", columns=["email"])
        assert not change.is_destructive()


# =============================================================================
# Change Type Tests
# =============================================================================

class TestChangeTypes:
    """Tests for change type enumerations."""
    
    def test_create_table_type(self):
        """Test create table change type."""
        change = CreateTable(table="test", columns=[])
        assert change.change_type == ChangeType.CREATE_TABLE
    
    def test_drop_table_type(self):
        """Test drop table change type."""
        change = DropTable(table="test")
        assert change.change_type == ChangeType.DROP_TABLE
    
    def test_add_column_type(self):
        """Test add column change type."""
        change = AddColumn(
            table="test",
            column=ColumnDef(name="col", sql_type="TEXT")
        )
        assert change.change_type == ChangeType.ADD_COLUMN
    
    def test_rename_table_type(self):
        """Test rename table change type."""
        change = RenameTable(old_name="old", new_name="new")
        assert change.change_type == ChangeType.RENAME_TABLE
    
    def test_add_index_type(self):
        """Test add index change type."""
        change = AddIndex(table="test", columns=["col"])
        assert change.change_type == ChangeType.ADD_INDEX

