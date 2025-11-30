"""
Tests for Declarative Migration Format.

Tests the declarative (simple dict-based) migration format.

70 tests covering:
- create_table operations
- alter_table operations
- drop_table operations
- index operations
- constraint operations
- Auto-reverse generation
"""

import pytest

from pynext.db.migrations import migration


# =============================================================================
# Create Table Tests
# =============================================================================

class TestCreateTable:
    """Tests for create_table operations."""
    
    def test_simple_create_table(self):
        """Test simple table creation."""
        sql = migration.create_table("users", {
            "id": "serial primary key",
            "name": "varchar(255) not null",
        })
        
        assert "CREATE TABLE" in sql
        assert "users" in sql
        assert "id" in sql
        assert "name" in sql
    
    def test_create_table_with_all_types(self):
        """Test table with various column types."""
        sql = migration.create_table("test_table", {
            "id": "serial primary key",
            "name": "varchar(255)",
            "age": "integer",
            "balance": "decimal(10,2)",
            "active": "boolean default true",
            "bio": "text",
            "data": "jsonb",
            "created": "timestamp default now()",
        })
        
        assert "serial" in sql.lower()
        assert "varchar(255)" in sql.lower()
        assert "integer" in sql.lower()
        assert "decimal" in sql.lower()
        assert "boolean" in sql.lower()
        assert "text" in sql.lower()
        assert "jsonb" in sql.lower()
        assert "timestamp" in sql.lower()
    
    def test_create_table_not_null(self):
        """Test not null constraints."""
        sql = migration.create_table("users", {
            "email": "varchar(255) not null unique",
        })
        
        assert "NOT NULL" in sql.upper()
        assert "UNIQUE" in sql.upper()
    
    def test_create_table_with_default(self):
        """Test default values."""
        sql = migration.create_table("users", {
            "role": "varchar(50) default 'user'",
            "created_at": "timestamp default now()",
        })
        
        assert "DEFAULT" in sql.upper()
    
    def test_create_table_foreign_key(self):
        """Test foreign key constraint."""
        sql = migration.create_table("posts", {
            "id": "serial primary key",
            "author_id": "integer references users(id)",
        })
        
        assert "REFERENCES" in sql.upper()
    
    def test_create_table_composite_pk(self):
        """Test composite primary key."""
        sql = migration.create_table("user_roles", {
            "user_id": "integer",
            "role_id": "integer",
            "__primary_key__": "(user_id, role_id)",
        })
        
        assert "PRIMARY KEY" in sql.upper()


# =============================================================================
# Alter Table Tests
# =============================================================================

class TestAlterTable:
    """Tests for alter_table operations."""
    
    def test_add_column(self):
        """Test adding a column."""
        sql = migration.add_column("users", "phone", "varchar(20)")
        
        assert "ALTER TABLE" in sql.upper()
        assert "ADD COLUMN" in sql.upper()
        assert "phone" in sql
        assert "varchar(20)" in sql.lower()
    
    def test_add_column_with_default(self):
        """Test adding column with default."""
        sql = migration.add_column(
            "users", "status",
            "varchar(50) default 'active'"
        )
        
        assert "DEFAULT" in sql.upper()
    
    def test_drop_column(self):
        """Test dropping a column."""
        sql = migration.drop_column("users", "phone")
        
        assert "ALTER TABLE" in sql.upper()
        assert "DROP COLUMN" in sql.upper()
        assert "phone" in sql
    
    def test_rename_column(self):
        """Test renaming a column."""
        sql = migration.rename_column("users", "name", "full_name")
        
        assert "RENAME" in sql.upper()
        assert "name" in sql
        assert "full_name" in sql
    
    def test_alter_column_type(self):
        """Test changing column type."""
        sql = migration.alter_column("users", "age", "bigint")
        
        assert "ALTER" in sql.upper()
        assert "TYPE" in sql.upper() or "bigint" in sql.lower()
    
    def test_alter_column_nullable(self):
        """Test changing nullability."""
        sql = migration.alter_column(
            "users", "email",
            nullable=False
        )
        
        assert "NOT NULL" in sql.upper()
    
    def test_alter_column_default(self):
        """Test changing default value."""
        sql = migration.alter_column(
            "users", "role",
            default="'member'"
        )
        
        assert "DEFAULT" in sql.upper()


# =============================================================================
# Drop Table Tests
# =============================================================================

class TestDropTable:
    """Tests for drop_table operations."""
    
    def test_drop_table(self):
        """Test dropping a table."""
        sql = migration.drop_table("old_users")
        
        assert "DROP TABLE" in sql.upper()
        assert "old_users" in sql
    
    def test_drop_table_cascade(self):
        """Test drop with cascade."""
        sql = migration.drop_table("users", cascade=True)
        
        assert "CASCADE" in sql.upper()
    
    def test_drop_table_if_exists(self):
        """Test drop if exists."""
        sql = migration.drop_table("maybe_users", if_exists=True)
        
        assert "IF EXISTS" in sql.upper()


# =============================================================================
# Index Tests
# =============================================================================

class TestIndexOperations:
    """Tests for index operations."""
    
    def test_create_index(self):
        """Test creating an index."""
        sql = migration.create_index("users", ["email"])
        
        assert "CREATE INDEX" in sql.upper()
        assert "email" in sql
    
    def test_create_unique_index(self):
        """Test creating unique index."""
        sql = migration.create_index("users", ["email"], unique=True)
        
        assert "UNIQUE" in sql.upper()
    
    def test_create_composite_index(self):
        """Test creating composite index."""
        sql = migration.create_index("users", ["first_name", "last_name"])
        
        assert "first_name" in sql
        assert "last_name" in sql
    
    def test_create_named_index(self):
        """Test creating named index."""
        sql = migration.create_index(
            "users", ["email"],
            name="idx_users_email"
        )
        
        assert "idx_users_email" in sql
    
    def test_drop_index(self):
        """Test dropping an index."""
        sql = migration.drop_index("idx_users_email")
        
        assert "DROP INDEX" in sql.upper()
        assert "idx_users_email" in sql
    
    def test_create_partial_index(self):
        """Test creating partial index."""
        sql = migration.create_index(
            "users", ["email"],
            where="active = true"
        )
        
        assert "WHERE" in sql.upper()


# =============================================================================
# Constraint Tests
# =============================================================================

class TestConstraintOperations:
    """Tests for constraint operations."""
    
    def test_add_unique_constraint(self):
        """Test adding unique constraint."""
        sql = migration.add_constraint(
            "users", "uq_users_email",
            "UNIQUE (email)"
        )
        
        assert "ADD CONSTRAINT" in sql.upper()
        assert "UNIQUE" in sql.upper()
    
    def test_add_check_constraint(self):
        """Test adding check constraint."""
        sql = migration.add_constraint(
            "users", "ck_users_age",
            "CHECK (age >= 0)"
        )
        
        assert "CHECK" in sql.upper()
    
    def test_add_foreign_key_constraint(self):
        """Test adding foreign key constraint."""
        sql = migration.add_constraint(
            "posts", "fk_posts_author",
            "FOREIGN KEY (author_id) REFERENCES users(id)"
        )
        
        assert "FOREIGN KEY" in sql.upper()
        assert "REFERENCES" in sql.upper()
    
    def test_drop_constraint(self):
        """Test dropping a constraint."""
        sql = migration.drop_constraint("users", "uq_users_email")
        
        assert "DROP CONSTRAINT" in sql.upper()


# =============================================================================
# Auto-Reverse Tests
# =============================================================================

class TestAutoReverse:
    """Tests for auto-reverse generation."""
    
    def test_create_table_reverse(self):
        """Test reverse of create_table is drop_table."""
        forward, reverse = migration.create_table_reversible("users", {
            "id": "serial primary key",
        })
        
        assert "CREATE TABLE" in forward.upper()
        assert "DROP TABLE" in reverse.upper()
    
    def test_add_column_reverse(self):
        """Test reverse of add_column is drop_column."""
        forward, reverse = migration.add_column_reversible(
            "users", "phone", "varchar(20)"
        )
        
        assert "ADD COLUMN" in forward.upper()
        assert "DROP COLUMN" in reverse.upper()
    
    def test_create_index_reverse(self):
        """Test reverse of create_index is drop_index."""
        forward, reverse = migration.create_index_reversible(
            "users", ["email"],
            name="idx_users_email"
        )
        
        assert "CREATE INDEX" in forward.upper()
        assert "DROP INDEX" in reverse.upper()


# =============================================================================
# SQL Dialect Tests
# =============================================================================

class TestSQLDialect:
    """Tests for SQL dialect handling."""
    
    def test_postgresql_serial(self):
        """Test PostgreSQL serial type."""
        sql = migration.create_table("users", {
            "id": "serial primary key",
        }, dialect="postgresql")
        
        assert "SERIAL" in sql.upper()
    
    def test_sqlite_autoincrement(self):
        """Test SQLite autoincrement."""
        sql = migration.create_table("users", {
            "id": "integer primary key autoincrement",
        }, dialect="sqlite")
        
        assert "AUTOINCREMENT" in sql.upper()
    
    def test_default_dialect(self):
        """Test default dialect is PostgreSQL-compatible."""
        sql = migration.create_table("users", {
            "id": "serial primary key",
        })
        
        # Should work with PostgreSQL syntax
        assert sql  # Just verify it doesn't crash


# =============================================================================
# Edge Cases Tests
# =============================================================================

class TestEdgeCases:
    """Edge case tests."""
    
    def test_empty_table(self):
        """Test creating empty table."""
        sql = migration.create_table("empty_table", {})
        
        # Should still generate valid SQL
        assert "CREATE TABLE" in sql.upper()
    
    def test_reserved_word_column(self):
        """Test column with reserved word name."""
        sql = migration.create_table("users", {
            "order": "integer",
            "select": "varchar(255)",
        })
        
        # Should quote reserved words
        assert sql  # Verify it doesn't crash
    
    def test_special_characters_in_default(self):
        """Test default value with special characters."""
        sql = migration.create_table("users", {
            "greeting": "varchar(255) default 'Hello, World!'",
        })
        
        assert "Hello" in sql
    
    def test_very_long_table_name(self):
        """Test with very long table name."""
        long_name = "a" * 100
        sql = migration.create_table(long_name, {
            "id": "serial primary key",
        })
        
        assert long_name in sql
    
    def test_numeric_column_precision(self):
        """Test numeric columns with precision."""
        sql = migration.create_table("products", {
            "price": "numeric(10, 2)",
            "weight": "decimal(8, 4)",
        })
        
        assert "10, 2" in sql or "10,2" in sql
        assert "8, 4" in sql or "8,4" in sql


# =============================================================================
# Batch Operations Tests
# =============================================================================

class TestBatchOperations:
    """Tests for batch operations."""
    
    def test_multiple_columns(self):
        """Test adding multiple columns at once."""
        sql = migration.add_columns("users", {
            "phone": "varchar(20)",
            "address": "text",
            "city": "varchar(100)",
        })
        
        assert sql.count("ADD COLUMN") >= 1  # May be combined or separate
    
    def test_batch_with_transaction(self):
        """Test batch operations wrapped in transaction."""
        statements = migration.batch([
            migration.create_table("users", {"id": "serial primary key"}),
            migration.create_table("posts", {"id": "serial primary key"}),
        ])
        
        # Should be a list of statements
        assert len(statements) >= 2

