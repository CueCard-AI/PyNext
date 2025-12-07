"""
Test Phase 7.4.1: Database-Level Cascade - FK Migrations.

These tests verify that:
1. add_fk_constraint generates correct SQL
2. alter_fk_on_delete correctly modifies constraints
3. drop_fk_constraint removes constraints
4. Migration operations work with cascade options
"""

import pytest
from typing import List, Dict, Any, Optional


# =============================================================================
# Mock Adapter for Migration Tests
# =============================================================================

class MockMigrationAdapter:
    """Mock adapter for testing FK migrations."""
    
    def __init__(self):
        self.executed_sql: List[str] = []
        self.constraints: Dict[str, Dict[str, Any]] = {}
    
    async def _execute(self, sql: str, *args) -> str:
        self.executed_sql.append(sql.strip())
        return "OK"
    
    async def get_foreign_keys(self, table: str) -> List[Dict[str, Any]]:
        """Get FKs for a table from internal storage."""
        return [
            v for k, v in self.constraints.items()
            if k.startswith(f"{table}_")
        ]
    
    async def add_fk_constraint(
        self,
        table: str,
        column: str,
        ref_table: str,
        ref_column: str = "id",
        on_delete: str = "NO ACTION",
        constraint_name: Optional[str] = None,
    ) -> None:
        """Add FK constraint."""
        if constraint_name is None:
            constraint_name = f"{table}_{column}_fkey"
        
        sql = f'''ALTER TABLE "{table}"
ADD CONSTRAINT "{constraint_name}"
FOREIGN KEY ("{column}")
REFERENCES "{ref_table}"("{ref_column}")
ON DELETE {on_delete}'''
        
        await self._execute(sql)
        
        # Track internally
        self.constraints[constraint_name] = {
            "table": table,
            "constraint_name": constraint_name,
            "column_name": column,
            "foreign_table": ref_table,
            "foreign_column": ref_column,
            "on_delete": on_delete,
        }
    
    async def alter_fk_on_delete(
        self,
        table: str,
        column: str,
        on_delete: str,
        constraint_name: Optional[str] = None,
    ) -> None:
        """Alter FK on_delete action."""
        if constraint_name is None:
            constraint_name = f"{table}_{column}_fkey"
        
        # Get current FK info
        fk_info = self.constraints.get(constraint_name)
        if not fk_info:
            raise ValueError(f"Constraint {constraint_name} not found")
        
        # Drop existing
        await self._execute(f'ALTER TABLE "{table}" DROP CONSTRAINT "{constraint_name}"')
        
        # Recreate with new on_delete
        await self.add_fk_constraint(
            table, column,
            fk_info["foreign_table"],
            fk_info["foreign_column"],
            on_delete,
            constraint_name,
        )
    
    async def drop_fk_constraint(self, table: str, constraint_name: str) -> None:
        """Drop FK constraint."""
        await self._execute(f'ALTER TABLE "{table}" DROP CONSTRAINT "{constraint_name}"')
        self.constraints.pop(constraint_name, None)


# =============================================================================
# Test add_fk_constraint
# =============================================================================

class TestAddFKConstraint:
    """Test add_fk_constraint method."""
    
    @pytest.fixture
    def adapter(self):
        return MockMigrationAdapter()
    
    @pytest.mark.asyncio
    async def test_generates_alter_table(self, adapter):
        """Should generate ALTER TABLE SQL."""
        await adapter.add_fk_constraint("posts", "author_id", "users")
        
        sql = adapter.executed_sql[0]
        assert 'ALTER TABLE "posts"' in sql
    
    @pytest.mark.asyncio
    async def test_generates_add_constraint(self, adapter):
        """Should generate ADD CONSTRAINT clause."""
        await adapter.add_fk_constraint("posts", "author_id", "users")
        
        sql = adapter.executed_sql[0]
        assert 'ADD CONSTRAINT "posts_author_id_fkey"' in sql
    
    @pytest.mark.asyncio
    async def test_generates_foreign_key(self, adapter):
        """Should generate FOREIGN KEY clause."""
        await adapter.add_fk_constraint("posts", "author_id", "users")
        
        sql = adapter.executed_sql[0]
        assert 'FOREIGN KEY ("author_id")' in sql
    
    @pytest.mark.asyncio
    async def test_generates_references(self, adapter):
        """Should generate REFERENCES clause."""
        await adapter.add_fk_constraint("posts", "author_id", "users")
        
        sql = adapter.executed_sql[0]
        assert 'REFERENCES "users"("id")' in sql
    
    @pytest.mark.asyncio
    async def test_generates_on_delete(self, adapter):
        """Should generate ON DELETE clause."""
        await adapter.add_fk_constraint("posts", "author_id", "users", on_delete="CASCADE")
        
        sql = adapter.executed_sql[0]
        assert "ON DELETE CASCADE" in sql
    
    @pytest.mark.asyncio
    async def test_default_on_delete_no_action(self, adapter):
        """Default on_delete should be NO ACTION."""
        await adapter.add_fk_constraint("posts", "author_id", "users")
        
        sql = adapter.executed_sql[0]
        assert "ON DELETE NO ACTION" in sql
    
    @pytest.mark.asyncio
    async def test_custom_constraint_name(self, adapter):
        """Should support custom constraint name."""
        await adapter.add_fk_constraint(
            "posts", "author_id", "users",
            constraint_name="custom_author_fk"
        )
        
        sql = adapter.executed_sql[0]
        assert 'ADD CONSTRAINT "custom_author_fk"' in sql
    
    @pytest.mark.asyncio
    async def test_custom_ref_column(self, adapter):
        """Should support custom reference column."""
        await adapter.add_fk_constraint(
            "posts", "author_email", "users",
            ref_column="email"
        )
        
        sql = adapter.executed_sql[0]
        assert 'REFERENCES "users"("email")' in sql
    
    @pytest.mark.asyncio
    async def test_on_delete_set_null(self, adapter):
        """Should support SET NULL on_delete."""
        await adapter.add_fk_constraint("posts", "author_id", "users", on_delete="SET NULL")
        
        sql = adapter.executed_sql[0]
        assert "ON DELETE SET NULL" in sql
    
    @pytest.mark.asyncio
    async def test_on_delete_restrict(self, adapter):
        """Should support RESTRICT on_delete."""
        await adapter.add_fk_constraint("posts", "author_id", "users", on_delete="RESTRICT")
        
        sql = adapter.executed_sql[0]
        assert "ON DELETE RESTRICT" in sql


# =============================================================================
# Test alter_fk_on_delete
# =============================================================================

class TestAlterFKOnDelete:
    """Test alter_fk_on_delete method."""
    
    @pytest.fixture
    async def adapter_with_fk(self):
        """Adapter with pre-existing FK."""
        adapter = MockMigrationAdapter()
        await adapter.add_fk_constraint("posts", "author_id", "users", on_delete="NO ACTION")
        adapter.executed_sql.clear()  # Clear initial SQL
        return adapter
    
    @pytest.mark.asyncio
    async def test_drops_existing_constraint(self, adapter_with_fk):
        """Should drop existing constraint."""
        await adapter_with_fk.alter_fk_on_delete("posts", "author_id", "CASCADE")
        
        assert any("DROP CONSTRAINT" in sql for sql in adapter_with_fk.executed_sql)
    
    @pytest.mark.asyncio
    async def test_recreates_constraint(self, adapter_with_fk):
        """Should recreate constraint with new on_delete."""
        await adapter_with_fk.alter_fk_on_delete("posts", "author_id", "CASCADE")
        
        assert any("ADD CONSTRAINT" in sql for sql in adapter_with_fk.executed_sql)
        assert any("ON DELETE CASCADE" in sql for sql in adapter_with_fk.executed_sql)
    
    @pytest.mark.asyncio
    async def test_preserves_constraint_name(self, adapter_with_fk):
        """Should preserve original constraint name."""
        await adapter_with_fk.alter_fk_on_delete("posts", "author_id", "CASCADE")
        
        # Both DROP and ADD should use same name
        assert any('"posts_author_id_fkey"' in sql for sql in adapter_with_fk.executed_sql)
    
    @pytest.mark.asyncio
    async def test_raises_for_nonexistent(self):
        """Should raise for non-existent constraint."""
        adapter = MockMigrationAdapter()
        
        with pytest.raises(ValueError) as exc_info:
            await adapter.alter_fk_on_delete("posts", "author_id", "CASCADE")
        
        assert "not found" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_change_to_set_null(self, adapter_with_fk):
        """Should change to SET NULL."""
        await adapter_with_fk.alter_fk_on_delete("posts", "author_id", "SET NULL")
        
        assert any("ON DELETE SET NULL" in sql for sql in adapter_with_fk.executed_sql)
    
    @pytest.mark.asyncio
    async def test_change_to_restrict(self, adapter_with_fk):
        """Should change to RESTRICT."""
        await adapter_with_fk.alter_fk_on_delete("posts", "author_id", "RESTRICT")
        
        assert any("ON DELETE RESTRICT" in sql for sql in adapter_with_fk.executed_sql)


# =============================================================================
# Test drop_fk_constraint
# =============================================================================

class TestDropFKConstraint:
    """Test drop_fk_constraint method."""
    
    @pytest.fixture
    async def adapter_with_fk(self):
        """Adapter with pre-existing FK."""
        adapter = MockMigrationAdapter()
        await adapter.add_fk_constraint("posts", "author_id", "users")
        adapter.executed_sql.clear()
        return adapter
    
    @pytest.mark.asyncio
    async def test_generates_drop_constraint(self, adapter_with_fk):
        """Should generate DROP CONSTRAINT SQL."""
        await adapter_with_fk.drop_fk_constraint("posts", "posts_author_id_fkey")
        
        sql = adapter_with_fk.executed_sql[0]
        assert 'ALTER TABLE "posts"' in sql
        assert 'DROP CONSTRAINT "posts_author_id_fkey"' in sql
    
    @pytest.mark.asyncio
    async def test_removes_from_internal_tracking(self, adapter_with_fk):
        """Should remove constraint from internal tracking."""
        await adapter_with_fk.drop_fk_constraint("posts", "posts_author_id_fkey")
        
        assert "posts_author_id_fkey" not in adapter_with_fk.constraints


# =============================================================================
# Test Migration Sequences
# =============================================================================

class TestMigrationSequences:
    """Test complete migration sequences."""
    
    @pytest.mark.asyncio
    async def test_add_multiple_fks(self):
        """Should add multiple FKs."""
        adapter = MockMigrationAdapter()
        
        await adapter.add_fk_constraint("posts", "author_id", "users", on_delete="CASCADE")
        await adapter.add_fk_constraint("posts", "category_id", "categories", on_delete="SET NULL")
        
        assert len(adapter.executed_sql) == 2
        assert "author_id" in adapter.executed_sql[0]
        assert "category_id" in adapter.executed_sql[1]
    
    @pytest.mark.asyncio
    async def test_add_then_alter(self):
        """Should add then alter FK."""
        adapter = MockMigrationAdapter()
        
        # Add
        await adapter.add_fk_constraint("posts", "author_id", "users", on_delete="NO ACTION")
        
        # Alter
        await adapter.alter_fk_on_delete("posts", "author_id", "CASCADE")
        
        # Should have: ADD, DROP, ADD
        assert len(adapter.executed_sql) == 3
        assert "ON DELETE CASCADE" in adapter.executed_sql[2]
    
    @pytest.mark.asyncio
    async def test_add_alter_drop(self):
        """Should add, alter, then drop FK."""
        adapter = MockMigrationAdapter()
        
        # Add
        await adapter.add_fk_constraint("posts", "author_id", "users")
        
        # Alter
        await adapter.alter_fk_on_delete("posts", "author_id", "CASCADE")
        
        # Drop
        await adapter.drop_fk_constraint("posts", "posts_author_id_fkey")
        
        # Should have: ADD, DROP, ADD, DROP
        assert len(adapter.executed_sql) == 4
        assert "DROP CONSTRAINT" in adapter.executed_sql[3]


# =============================================================================
# Test Rollback Scenario
# =============================================================================

class TestRollbackScenario:
    """Test migration rollback scenarios."""
    
    @pytest.mark.asyncio
    async def test_rollback_add_fk(self):
        """Should be able to rollback FK addition."""
        adapter = MockMigrationAdapter()
        
        # Forward: Add FK
        await adapter.add_fk_constraint("posts", "author_id", "users", on_delete="CASCADE")
        
        # Rollback: Drop FK
        await adapter.drop_fk_constraint("posts", "posts_author_id_fkey")
        
        assert "posts_author_id_fkey" not in adapter.constraints
    
    @pytest.mark.asyncio
    async def test_rollback_alter_fk(self):
        """Should be able to rollback FK alteration."""
        adapter = MockMigrationAdapter()
        
        # Initial: Add FK with NO ACTION
        await adapter.add_fk_constraint("posts", "author_id", "users", on_delete="NO ACTION")
        
        # Forward: Change to CASCADE
        await adapter.alter_fk_on_delete("posts", "author_id", "CASCADE")
        
        # Rollback: Change back to NO ACTION
        await adapter.alter_fk_on_delete("posts", "author_id", "NO ACTION")
        
        # Final FK should have NO ACTION
        fk = adapter.constraints["posts_author_id_fkey"]
        assert fk["on_delete"] == "NO ACTION"

