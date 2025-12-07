"""
Test Phase 7.4.1: Database-Level Cascade - Basic ON DELETE SQL Generation.

These tests verify that:
1. FK constraints are generated with correct ON DELETE clauses
2. The fk_on_delete attribute is set correctly on FieldInfo
3. Relationship on_delete values map correctly to PostgreSQL actions
"""

import pytest
from typing import List, Optional

from pynext.db.fields import FieldInfo, SQLType, parse_type_hint
from pynext.db.table import _map_on_delete_to_postgres


# =============================================================================
# Test _map_on_delete_to_postgres
# =============================================================================

class TestOnDeleteMapping:
    """Test mapping of PyNext on_delete values to PostgreSQL actions."""
    
    def test_cascade_maps_to_cascade(self):
        """'cascade' should map to 'CASCADE'."""
        assert _map_on_delete_to_postgres("cascade") == "CASCADE"
    
    def test_nullify_maps_to_set_null(self):
        """'nullify' should map to 'SET NULL'."""
        assert _map_on_delete_to_postgres("nullify") == "SET NULL"
    
    def test_protect_maps_to_restrict(self):
        """'protect' should map to 'RESTRICT'."""
        assert _map_on_delete_to_postgres("protect") == "RESTRICT"
    
    def test_none_maps_to_no_action(self):
        """'none' should map to 'NO ACTION'."""
        assert _map_on_delete_to_postgres("none") == "NO ACTION"
    
    def test_uppercase_cascade(self):
        """'CASCADE' should also work (case insensitive)."""
        assert _map_on_delete_to_postgres("CASCADE") == "CASCADE"
    
    def test_mixed_case_nullify(self):
        """'Nullify' should also work (case insensitive)."""
        assert _map_on_delete_to_postgres("Nullify") == "SET NULL"
    
    def test_unknown_defaults_to_no_action(self):
        """Unknown values should default to 'NO ACTION'."""
        assert _map_on_delete_to_postgres("unknown") == "NO ACTION"
        assert _map_on_delete_to_postgres("delete") == "NO ACTION"
        assert _map_on_delete_to_postgres("") == "NO ACTION"


# =============================================================================
# Test FieldInfo.fk_on_delete
# =============================================================================

class TestFieldInfoFkOnDelete:
    """Test fk_on_delete attribute on FieldInfo."""
    
    def test_default_is_no_action(self):
        """Default fk_on_delete should be 'NO ACTION'."""
        field = FieldInfo(
            name="author_id",
            python_type=int,
            sql_type=SQLType.INTEGER,
        )
        assert field.fk_on_delete == "NO ACTION"
    
    def test_can_set_cascade(self):
        """Can set fk_on_delete to 'CASCADE'."""
        field = FieldInfo(
            name="author_id",
            python_type=int,
            sql_type=SQLType.INTEGER,
            fk_on_delete="CASCADE",
        )
        assert field.fk_on_delete == "CASCADE"
    
    def test_can_set_set_null(self):
        """Can set fk_on_delete to 'SET NULL'."""
        field = FieldInfo(
            name="author_id",
            python_type=int,
            sql_type=SQLType.INTEGER,
            fk_on_delete="SET NULL",
        )
        assert field.fk_on_delete == "SET NULL"
    
    def test_can_set_restrict(self):
        """Can set fk_on_delete to 'RESTRICT'."""
        field = FieldInfo(
            name="author_id",
            python_type=int,
            sql_type=SQLType.INTEGER,
            fk_on_delete="RESTRICT",
        )
        assert field.fk_on_delete == "RESTRICT"
    
    def test_fk_with_on_delete(self):
        """FK field with on_delete configured."""
        field = FieldInfo(
            name="author_id",
            python_type=int,
            sql_type=SQLType.INTEGER,
            foreign_key="users",
            fk_on_delete="CASCADE",
        )
        assert field.foreign_key == "users"
        assert field.fk_on_delete == "CASCADE"
    
    def test_auto_detect_fk_with_on_delete(self):
        """Auto-detected FK should support fk_on_delete."""
        field = FieldInfo(
            name="author_id",
            python_type=int,
            sql_type=SQLType.INTEGER,
        )
        # Auto-detection sets foreign_key to "authors"
        assert field.foreign_key == "authors"
        # Can update fk_on_delete
        field.fk_on_delete = "CASCADE"
        assert field.fk_on_delete == "CASCADE"


# =============================================================================
# Test SQL Generation with ON DELETE
# =============================================================================

class TestSQLGenerationOnDelete:
    """Test SQL generation includes ON DELETE clauses."""
    
    def test_to_sql_column_basic(self):
        """Basic column without FK."""
        field = FieldInfo(
            name="title",
            python_type=str,
            sql_type=SQLType.VARCHAR,
            max_length=255,
        )
        sql = field.to_sql_column()
        assert "title" in sql
        assert "VARCHAR" in sql
        assert "ON DELETE" not in sql
    
    def test_field_with_fk_has_foreign_key(self):
        """FK field should have foreign_key attribute."""
        field = FieldInfo(
            name="author_id",
            python_type=int,
            sql_type=SQLType.INTEGER,
            foreign_key="users",
        )
        assert field.foreign_key == "users"
    
    def test_parsed_field_with_fk_pattern(self):
        """Parsed field with _id pattern should auto-detect FK."""
        field = parse_type_hint("author_id", int)
        assert field.foreign_key == "authors"
        assert field.fk_on_delete == "NO ACTION"


# =============================================================================
# Test Complete SQL Generation (Mocked Adapter)
# =============================================================================

class MockPostgresAdapter:
    """Mock adapter to test SQL generation."""
    
    def build_column_def(self, name: str, field: FieldInfo) -> str:
        """Build column definition like PostgresAdapter."""
        # Simulate PostgresAdapter logic
        pg_type = self._get_postgres_type(field.python_type)
        col_def = f'"{name}" {pg_type}'
        
        if field.primary_key:
            if pg_type in ("INTEGER", "BIGINT"):
                col_def = f'"{name}" SERIAL PRIMARY KEY'
            else:
                col_def += " PRIMARY KEY"
        else:
            if not field.nullable:
                col_def += " NOT NULL"
            if field.unique:
                col_def += " UNIQUE"
            
            # FK constraint with ON DELETE
            if field.foreign_key:
                col_def += f' REFERENCES "{field.foreign_key}"("id")'
                fk_on_delete = getattr(field, 'fk_on_delete', 'NO ACTION')
                if fk_on_delete and fk_on_delete != "NO ACTION":
                    col_def += f" ON DELETE {fk_on_delete}"
        
        return col_def
    
    def _get_postgres_type(self, python_type):
        """Get PostgreSQL type."""
        type_map = {
            int: "INTEGER",
            str: "VARCHAR(255)",
            float: "DOUBLE PRECISION",
            bool: "BOOLEAN",
        }
        return type_map.get(python_type, "TEXT")


class TestMockedSQLGeneration:
    """Test SQL generation using mocked adapter."""
    
    def setup_method(self):
        """Create mock adapter."""
        self.adapter = MockPostgresAdapter()
    
    def test_fk_with_cascade(self):
        """FK with CASCADE generates correct SQL."""
        field = FieldInfo(
            name="author_id",
            python_type=int,
            sql_type=SQLType.INTEGER,
            foreign_key="users",
            fk_on_delete="CASCADE",
        )
        sql = self.adapter.build_column_def("author_id", field)
        assert 'REFERENCES "users"("id")' in sql
        assert "ON DELETE CASCADE" in sql
    
    def test_fk_with_set_null(self):
        """FK with SET NULL generates correct SQL."""
        field = FieldInfo(
            name="author_id",
            python_type=int,
            sql_type=SQLType.INTEGER,
            nullable=True,
            foreign_key="users",
            fk_on_delete="SET NULL",
        )
        sql = self.adapter.build_column_def("author_id", field)
        assert 'REFERENCES "users"("id")' in sql
        assert "ON DELETE SET NULL" in sql
    
    def test_fk_with_restrict(self):
        """FK with RESTRICT generates correct SQL."""
        field = FieldInfo(
            name="author_id",
            python_type=int,
            sql_type=SQLType.INTEGER,
            foreign_key="users",
            fk_on_delete="RESTRICT",
        )
        sql = self.adapter.build_column_def("author_id", field)
        assert 'REFERENCES "users"("id")' in sql
        assert "ON DELETE RESTRICT" in sql
    
    def test_fk_with_no_action(self):
        """FK with NO ACTION doesn't add explicit clause."""
        field = FieldInfo(
            name="author_id",
            python_type=int,
            sql_type=SQLType.INTEGER,
            foreign_key="users",
            fk_on_delete="NO ACTION",
        )
        sql = self.adapter.build_column_def("author_id", field)
        assert 'REFERENCES "users"("id")' in sql
        assert "ON DELETE" not in sql  # NO ACTION is default, not needed
    
    def test_fk_without_on_delete(self):
        """FK without on_delete uses default (NO ACTION)."""
        field = FieldInfo(
            name="author_id",
            python_type=int,
            sql_type=SQLType.INTEGER,
            foreign_key="users",
        )
        sql = self.adapter.build_column_def("author_id", field)
        assert 'REFERENCES "users"("id")' in sql
        assert "ON DELETE" not in sql  # Default, not needed
    
    def test_non_fk_column(self):
        """Non-FK column should not have REFERENCES."""
        field = FieldInfo(
            name="title",
            python_type=str,
            sql_type=SQLType.VARCHAR,
            max_length=255,
        )
        sql = self.adapter.build_column_def("title", field)
        assert "REFERENCES" not in sql
        assert "ON DELETE" not in sql
    
    def test_primary_key_column(self):
        """Primary key column should not have REFERENCES."""
        field = FieldInfo(
            name="id",
            python_type=int,
            sql_type=SQLType.INTEGER,
            primary_key=True,
            auto_increment=True,
        )
        sql = self.adapter.build_column_def("id", field)
        assert "SERIAL PRIMARY KEY" in sql
        assert "REFERENCES" not in sql


# =============================================================================
# Test ON DELETE Action Enum (from cascade.py)
# =============================================================================

class TestOnDeleteAction:
    """Test OnDeleteAction enum."""
    
    def test_cascade_value(self):
        """Test CASCADE value."""
        from pynext.db.relationships.cascade import OnDeleteAction
        assert OnDeleteAction.CASCADE.value == "cascade"
    
    def test_nullify_value(self):
        """Test NULLIFY value."""
        from pynext.db.relationships.cascade import OnDeleteAction
        assert OnDeleteAction.NULLIFY.value == "nullify"
    
    def test_protect_value(self):
        """Test PROTECT value."""
        from pynext.db.relationships.cascade import OnDeleteAction
        assert OnDeleteAction.PROTECT.value == "protect"
    
    def test_none_value(self):
        """Test NONE value."""
        from pynext.db.relationships.cascade import OnDeleteAction
        assert OnDeleteAction.NONE.value == "none"
    
    def test_from_string_cascade(self):
        """Test from_string with 'cascade'."""
        from pynext.db.relationships.cascade import OnDeleteAction
        assert OnDeleteAction.from_string("cascade") == OnDeleteAction.CASCADE
    
    def test_from_string_nullify(self):
        """Test from_string with 'nullify'."""
        from pynext.db.relationships.cascade import OnDeleteAction
        assert OnDeleteAction.from_string("nullify") == OnDeleteAction.NULLIFY
    
    def test_from_string_protect(self):
        """Test from_string with 'protect'."""
        from pynext.db.relationships.cascade import OnDeleteAction
        assert OnDeleteAction.from_string("protect") == OnDeleteAction.PROTECT
    
    def test_from_string_uppercase(self):
        """Test from_string with uppercase."""
        from pynext.db.relationships.cascade import OnDeleteAction
        assert OnDeleteAction.from_string("CASCADE") == OnDeleteAction.CASCADE
    
    def test_from_string_invalid(self):
        """Test from_string with invalid value."""
        from pynext.db.relationships.cascade import OnDeleteAction
        with pytest.raises(ValueError) as exc_info:
            OnDeleteAction.from_string("invalid")
        assert "Invalid on_delete value" in str(exc_info.value)

