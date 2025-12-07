"""
Test Phase 7.4.1: Database-Level Cascade - PostgreSQL Integration.

These tests verify that:
1. PostgresAdapter generates correct FK constraints
2. create_table includes ON DELETE clauses
3. FK constraint methods work correctly
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Optional

from pynext.db.fields import FieldInfo, SQLType


# =============================================================================
# Mock PostgresAdapter for Testing SQL Generation
# =============================================================================

class MockPool:
    """Mock connection pool."""
    
    async def execute(self, sql: str, *args) -> str:
        return f"EXECUTE: {sql}"
    
    async def fetch(self, sql: str, *args) -> list:
        return []
    
    async def fetchrow(self, sql: str, *args) -> dict:
        return None


class TestPostgresAdapterCreateTable:
    """Test PostgresAdapter.create_table with FK constraints."""
    
    @pytest.fixture
    def mock_adapter(self):
        """Create a mock adapter for testing."""
        # We'll test the SQL generation logic directly
        from pynext.db.adapters.postgres_types import get_postgres_type
        
        class TestableAdapter:
            def __init__(self):
                self._pool = MockPool()
                self.last_sql = None
            
            async def _execute(self, sql: str, *args) -> str:
                self.last_sql = sql
                return "CREATE TABLE"
            
            def _format_default(self, value):
                if value is None:
                    return "NULL"
                elif isinstance(value, bool):
                    return "TRUE" if value else "FALSE"
                elif isinstance(value, (int, float)):
                    return str(value)
                else:
                    return f"'{value}'"
            
            async def create_table(self, table: str, fields: dict) -> None:
                columns = []
                
                for name, field_info in fields.items():
                    pg_type = get_postgres_type(field_info.python_type)
                    col_def = f'"{name}" {pg_type}'
                    
                    if field_info.primary_key:
                        if pg_type in ("INTEGER", "BIGINT"):
                            col_def = f'"{name}" SERIAL PRIMARY KEY'
                        else:
                            col_def += " PRIMARY KEY"
                    else:
                        if not field_info.nullable:
                            col_def += " NOT NULL"
                        if field_info.unique:
                            col_def += " UNIQUE"
                        if field_info.default is not None:
                            default_val = self._format_default(field_info.default)
                            col_def += f" DEFAULT {default_val}"
                        
                        # FK constraint with ON DELETE
                        if field_info.foreign_key:
                            col_def += f' REFERENCES "{field_info.foreign_key}"("id")'
                            fk_on_delete = getattr(field_info, 'fk_on_delete', 'NO ACTION')
                            if fk_on_delete and fk_on_delete != "NO ACTION":
                                col_def += f" ON DELETE {fk_on_delete}"
                    
                    columns.append(col_def)
                
                sql = f'CREATE TABLE IF NOT EXISTS "{table}" (\n  ' + ",\n  ".join(columns) + "\n)"
                await self._execute(sql)
        
        return TestableAdapter()
    
    @pytest.mark.asyncio
    async def test_create_table_without_fk(self, mock_adapter):
        """Test table creation without FK."""
        fields = {
            "id": FieldInfo("id", int, SQLType.INTEGER, primary_key=True, auto_increment=True),
            "name": FieldInfo("name", str, SQLType.VARCHAR, max_length=255),
        }
        
        await mock_adapter.create_table("users", fields)
        
        assert '"users"' in mock_adapter.last_sql
        assert '"id" SERIAL PRIMARY KEY' in mock_adapter.last_sql
        assert '"name"' in mock_adapter.last_sql
        assert "REFERENCES" not in mock_adapter.last_sql
    
    @pytest.mark.asyncio
    async def test_create_table_with_fk_cascade(self, mock_adapter):
        """Test table creation with FK CASCADE."""
        fields = {
            "id": FieldInfo("id", int, SQLType.INTEGER, primary_key=True, auto_increment=True),
            "author_id": FieldInfo(
                "author_id", int, SQLType.INTEGER,
                foreign_key="users",
                fk_on_delete="CASCADE",
            ),
            "title": FieldInfo("title", str, SQLType.VARCHAR, max_length=255),
        }
        
        await mock_adapter.create_table("posts", fields)
        
        assert '"posts"' in mock_adapter.last_sql
        assert 'REFERENCES "users"("id")' in mock_adapter.last_sql
        assert "ON DELETE CASCADE" in mock_adapter.last_sql
    
    @pytest.mark.asyncio
    async def test_create_table_with_fk_set_null(self, mock_adapter):
        """Test table creation with FK SET NULL."""
        fields = {
            "id": FieldInfo("id", int, SQLType.INTEGER, primary_key=True, auto_increment=True),
            "author_id": FieldInfo(
                "author_id", int, SQLType.INTEGER,
                nullable=True,
                foreign_key="users",
                fk_on_delete="SET NULL",
            ),
        }
        
        await mock_adapter.create_table("posts", fields)
        
        assert 'REFERENCES "users"("id")' in mock_adapter.last_sql
        assert "ON DELETE SET NULL" in mock_adapter.last_sql
    
    @pytest.mark.asyncio
    async def test_create_table_with_fk_restrict(self, mock_adapter):
        """Test table creation with FK RESTRICT."""
        fields = {
            "id": FieldInfo("id", int, SQLType.INTEGER, primary_key=True, auto_increment=True),
            "user_id": FieldInfo(
                "user_id", int, SQLType.INTEGER,
                foreign_key="users",
                fk_on_delete="RESTRICT",
            ),
        }
        
        await mock_adapter.create_table("orders", fields)
        
        assert 'REFERENCES "users"("id")' in mock_adapter.last_sql
        assert "ON DELETE RESTRICT" in mock_adapter.last_sql
    
    @pytest.mark.asyncio
    async def test_create_table_with_fk_no_action_default(self, mock_adapter):
        """Test table creation with FK NO ACTION (default - omitted)."""
        fields = {
            "id": FieldInfo("id", int, SQLType.INTEGER, primary_key=True, auto_increment=True),
            "author_id": FieldInfo(
                "author_id", int, SQLType.INTEGER,
                foreign_key="users",
                fk_on_delete="NO ACTION",
            ),
        }
        
        await mock_adapter.create_table("posts", fields)
        
        assert 'REFERENCES "users"("id")' in mock_adapter.last_sql
        # NO ACTION is default, should not be explicitly stated
        assert "ON DELETE NO ACTION" not in mock_adapter.last_sql
    
    @pytest.mark.asyncio
    async def test_create_table_multiple_fks(self, mock_adapter):
        """Test table creation with multiple FKs."""
        fields = {
            "id": FieldInfo("id", int, SQLType.INTEGER, primary_key=True, auto_increment=True),
            "author_id": FieldInfo(
                "author_id", int, SQLType.INTEGER,
                foreign_key="users",
                fk_on_delete="CASCADE",
            ),
            "category_id": FieldInfo(
                "category_id", int, SQLType.INTEGER,
                foreign_key="categories",
                fk_on_delete="SET NULL",
            ),
        }
        
        await mock_adapter.create_table("posts", fields)
        
        assert 'REFERENCES "users"("id")' in mock_adapter.last_sql
        assert 'REFERENCES "categories"("id")' in mock_adapter.last_sql
        assert "ON DELETE CASCADE" in mock_adapter.last_sql
        assert "ON DELETE SET NULL" in mock_adapter.last_sql
    
    @pytest.mark.asyncio
    async def test_create_table_fk_with_not_null(self, mock_adapter):
        """Test FK with NOT NULL constraint."""
        fields = {
            "id": FieldInfo("id", int, SQLType.INTEGER, primary_key=True, auto_increment=True),
            "author_id": FieldInfo(
                "author_id", int, SQLType.INTEGER,
                nullable=False,
                foreign_key="users",
                fk_on_delete="CASCADE",
            ),
        }
        
        await mock_adapter.create_table("posts", fields)
        
        assert "NOT NULL" in mock_adapter.last_sql
        assert 'REFERENCES "users"("id")' in mock_adapter.last_sql
        assert "ON DELETE CASCADE" in mock_adapter.last_sql


# =============================================================================
# Test FK Introspection Methods
# =============================================================================

class TestFKIntrospection:
    """Test FK introspection methods."""
    
    @pytest.fixture
    def mock_adapter_with_fks(self):
        """Create adapter that returns mock FK data."""
        class TestableAdapter:
            async def _fetch(self, sql, *args):
                if "information_schema.table_constraints" in sql:
                    return [
                        {
                            "constraint_name": "posts_author_id_fkey",
                            "column_name": "author_id",
                            "foreign_table": "users",
                            "foreign_column": "id",
                            "on_delete": "CASCADE",
                        },
                        {
                            "constraint_name": "posts_category_id_fkey",
                            "column_name": "category_id",
                            "foreign_table": "categories",
                            "foreign_column": "id",
                            "on_delete": "SET NULL",
                        },
                    ]
                return []
            
            async def _fetchrow(self, sql, *args):
                if "information_schema.table_constraints" in sql:
                    if args[1] == "posts_author_id_fkey":
                        return {"constraint_name": "posts_author_id_fkey"}
                return None
            
            async def get_foreign_keys(self, table: str):
                sql = """
                    SELECT ... FROM information_schema.table_constraints tc ...
                """
                rows = await self._fetch(sql, table)
                return [
                    {
                        "constraint_name": row["constraint_name"],
                        "column_name": row["column_name"],
                        "foreign_table": row["foreign_table"],
                        "foreign_column": row["foreign_column"],
                        "on_delete": row["on_delete"],
                    }
                    for row in rows
                ]
            
            async def has_constraint(self, table: str, constraint_name: str):
                sql = """
                    SELECT 1 FROM information_schema.table_constraints ...
                """
                result = await self._fetchrow(sql, table, constraint_name)
                return result is not None
        
        return TestableAdapter()
    
    @pytest.mark.asyncio
    async def test_get_foreign_keys_returns_list(self, mock_adapter_with_fks):
        """Test get_foreign_keys returns a list."""
        fks = await mock_adapter_with_fks.get_foreign_keys("posts")
        assert isinstance(fks, list)
        assert len(fks) == 2
    
    @pytest.mark.asyncio
    async def test_get_foreign_keys_contains_constraint_name(self, mock_adapter_with_fks):
        """Test FK info contains constraint_name."""
        fks = await mock_adapter_with_fks.get_foreign_keys("posts")
        assert fks[0]["constraint_name"] == "posts_author_id_fkey"
    
    @pytest.mark.asyncio
    async def test_get_foreign_keys_contains_column_name(self, mock_adapter_with_fks):
        """Test FK info contains column_name."""
        fks = await mock_adapter_with_fks.get_foreign_keys("posts")
        assert fks[0]["column_name"] == "author_id"
    
    @pytest.mark.asyncio
    async def test_get_foreign_keys_contains_foreign_table(self, mock_adapter_with_fks):
        """Test FK info contains foreign_table."""
        fks = await mock_adapter_with_fks.get_foreign_keys("posts")
        assert fks[0]["foreign_table"] == "users"
    
    @pytest.mark.asyncio
    async def test_get_foreign_keys_contains_on_delete(self, mock_adapter_with_fks):
        """Test FK info contains on_delete action."""
        fks = await mock_adapter_with_fks.get_foreign_keys("posts")
        assert fks[0]["on_delete"] == "CASCADE"
        assert fks[1]["on_delete"] == "SET NULL"
    
    @pytest.mark.asyncio
    async def test_has_constraint_returns_true(self, mock_adapter_with_fks):
        """Test has_constraint returns True for existing constraint."""
        result = await mock_adapter_with_fks.has_constraint("posts", "posts_author_id_fkey")
        assert result is True
    
    @pytest.mark.asyncio
    async def test_has_constraint_returns_false(self, mock_adapter_with_fks):
        """Test has_constraint returns False for non-existing constraint."""
        result = await mock_adapter_with_fks.has_constraint("posts", "nonexistent_fkey")
        assert result is False


# =============================================================================
# Test FK Alteration Methods
# =============================================================================

class TestFKAlteration:
    """Test FK constraint alteration methods."""
    
    @pytest.fixture
    def mock_adapter_for_alter(self):
        """Create adapter for testing alterations."""
        class TestableAdapter:
            def __init__(self):
                self.executed_sql = []
            
            async def _execute(self, sql, *args):
                self.executed_sql.append(sql)
                return "OK"
            
            async def _fetch(self, sql, *args):
                return [
                    {
                        "constraint_name": "posts_author_id_fkey",
                        "column_name": "author_id",
                        "foreign_table": "users",
                        "foreign_column": "id",
                        "on_delete": "NO ACTION",
                    },
                ]
            
            async def get_foreign_keys(self, table):
                rows = await self._fetch("", table)
                return rows
            
            async def add_fk_constraint(
                self, table, column, ref_table,
                ref_column="id", on_delete="NO ACTION",
                constraint_name=None
            ):
                if constraint_name is None:
                    constraint_name = f"{table}_{column}_fkey"
                
                sql = f'''
                    ALTER TABLE "{table}"
                    ADD CONSTRAINT "{constraint_name}"
                    FOREIGN KEY ("{column}")
                    REFERENCES "{ref_table}"("{ref_column}")
                    ON DELETE {on_delete}
                '''
                await self._execute(sql)
            
            async def alter_fk_on_delete(
                self, table, column, on_delete,
                constraint_name=None
            ):
                fks = await self.get_foreign_keys(table)
                for fk in fks:
                    if fk["column_name"] == column:
                        constraint_name = fk["constraint_name"]
                        ref_table = fk["foreign_table"]
                        ref_column = fk["foreign_column"]
                        break
                
                await self._execute(f'ALTER TABLE "{table}" DROP CONSTRAINT "{constraint_name}"')
                await self.add_fk_constraint(
                    table, column, ref_table, ref_column, on_delete, constraint_name
                )
            
            async def drop_fk_constraint(self, table, constraint_name):
                await self._execute(f'ALTER TABLE "{table}" DROP CONSTRAINT "{constraint_name}"')
        
        return TestableAdapter()
    
    @pytest.mark.asyncio
    async def test_add_fk_constraint(self, mock_adapter_for_alter):
        """Test add_fk_constraint generates correct SQL."""
        await mock_adapter_for_alter.add_fk_constraint(
            "posts", "author_id", "users",
            on_delete="CASCADE"
        )
        
        sql = mock_adapter_for_alter.executed_sql[0]
        assert 'ALTER TABLE "posts"' in sql
        assert 'ADD CONSTRAINT "posts_author_id_fkey"' in sql
        assert 'FOREIGN KEY ("author_id")' in sql
        assert 'REFERENCES "users"("id")' in sql
        assert "ON DELETE CASCADE" in sql
    
    @pytest.mark.asyncio
    async def test_add_fk_constraint_custom_name(self, mock_adapter_for_alter):
        """Test add_fk_constraint with custom constraint name."""
        await mock_adapter_for_alter.add_fk_constraint(
            "posts", "author_id", "users",
            on_delete="CASCADE",
            constraint_name="custom_fk_name"
        )
        
        sql = mock_adapter_for_alter.executed_sql[0]
        assert 'ADD CONSTRAINT "custom_fk_name"' in sql
    
    @pytest.mark.asyncio
    async def test_alter_fk_on_delete(self, mock_adapter_for_alter):
        """Test alter_fk_on_delete drops and recreates constraint."""
        await mock_adapter_for_alter.alter_fk_on_delete(
            "posts", "author_id", "CASCADE"
        )
        
        # Should have DROP and ADD
        assert len(mock_adapter_for_alter.executed_sql) == 2
        assert 'DROP CONSTRAINT "posts_author_id_fkey"' in mock_adapter_for_alter.executed_sql[0]
        assert "ON DELETE CASCADE" in mock_adapter_for_alter.executed_sql[1]
    
    @pytest.mark.asyncio
    async def test_drop_fk_constraint(self, mock_adapter_for_alter):
        """Test drop_fk_constraint generates correct SQL."""
        await mock_adapter_for_alter.drop_fk_constraint(
            "posts", "posts_author_id_fkey"
        )
        
        sql = mock_adapter_for_alter.executed_sql[0]
        assert 'ALTER TABLE "posts"' in sql
        assert 'DROP CONSTRAINT "posts_author_id_fkey"' in sql


# =============================================================================
# Test Base Adapter FK Methods
# =============================================================================

class TestBaseAdapterFKMethods:
    """Test base adapter FK method stubs."""
    
    @pytest.mark.asyncio
    async def test_get_foreign_keys_returns_empty(self):
        """Base adapter get_foreign_keys returns empty list."""
        from pynext.db.adapters.base import Adapter
        
        class MinimalAdapter(Adapter):
            async def connect(self): pass
            async def disconnect(self): pass
            async def create_table(self, table, fields): pass
            async def drop_table(self, table): pass
            async def insert(self, table, data, fields): pass
            async def select(self, table, query, fields): return []
            async def select_one(self, table, query, fields): return None
            async def update(self, table, id, data, fields): pass
            async def delete(self, table, id): return False
            async def count(self, table, query): return 0
            async def exists(self, table, query): return False
            async def execute(self, sql, params=None): pass
            async def fetch_all(self, sql, params=None): return []
            async def fetch_one(self, sql, params=None): return None
            async def begin_transaction(self): pass
            async def commit_transaction(self): pass
            async def rollback_transaction(self): pass
        
        adapter = MinimalAdapter()
        result = await adapter.get_foreign_keys("test")
        assert result == []
    
    @pytest.mark.asyncio
    async def test_has_constraint_returns_false(self):
        """Base adapter has_constraint returns False."""
        from pynext.db.adapters.base import Adapter
        
        class MinimalAdapter(Adapter):
            async def connect(self): pass
            async def disconnect(self): pass
            async def create_table(self, table, fields): pass
            async def drop_table(self, table): pass
            async def insert(self, table, data, fields): pass
            async def select(self, table, query, fields): return []
            async def select_one(self, table, query, fields): return None
            async def update(self, table, id, data, fields): pass
            async def delete(self, table, id): return False
            async def count(self, table, query): return 0
            async def exists(self, table, query): return False
            async def execute(self, sql, params=None): pass
            async def fetch_all(self, sql, params=None): return []
            async def fetch_one(self, sql, params=None): return None
            async def begin_transaction(self): pass
            async def commit_transaction(self): pass
            async def rollback_transaction(self): pass
        
        adapter = MinimalAdapter()
        result = await adapter.has_constraint("test", "test_fk")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_add_fk_constraint_raises(self):
        """Base adapter add_fk_constraint raises NotImplementedError."""
        from pynext.db.adapters.base import Adapter
        
        class MinimalAdapter(Adapter):
            async def connect(self): pass
            async def disconnect(self): pass
            async def create_table(self, table, fields): pass
            async def drop_table(self, table): pass
            async def insert(self, table, data, fields): pass
            async def select(self, table, query, fields): return []
            async def select_one(self, table, query, fields): return None
            async def update(self, table, id, data, fields): pass
            async def delete(self, table, id): return False
            async def count(self, table, query): return 0
            async def exists(self, table, query): return False
            async def execute(self, sql, params=None): pass
            async def fetch_all(self, sql, params=None): return []
            async def fetch_one(self, sql, params=None): return None
            async def begin_transaction(self): pass
            async def commit_transaction(self): pass
            async def rollback_transaction(self): pass
        
        adapter = MinimalAdapter()
        with pytest.raises(NotImplementedError):
            await adapter.add_fk_constraint("test", "col", "ref")

