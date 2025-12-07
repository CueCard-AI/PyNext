"""
Test Phase 7.4.1: Database-Level Cascade - FK Introspection.

These tests verify that:
1. get_foreign_keys returns correct FK information
2. has_constraint correctly checks for constraints
3. FK introspection works with various constraint types
"""

import pytest
from typing import List, Dict, Any, Optional


# =============================================================================
# Mock Adapter for Introspection Tests
# =============================================================================

class MockIntrospectionAdapter:
    """Mock adapter for testing FK introspection."""
    
    def __init__(self, fk_data: List[Dict[str, Any]] = None):
        self.fk_data = fk_data or []
    
    async def get_foreign_keys(self, table: str) -> List[Dict[str, Any]]:
        """Get FKs for a table."""
        return [fk for fk in self.fk_data if fk.get("_table") == table]
    
    async def has_constraint(self, table: str, constraint_name: str) -> bool:
        """Check if constraint exists."""
        for fk in self.fk_data:
            if fk.get("_table") == table and fk.get("constraint_name") == constraint_name:
                return True
        return False


# =============================================================================
# Test get_foreign_keys
# =============================================================================

class TestGetForeignKeys:
    """Test get_foreign_keys method."""
    
    @pytest.fixture
    def adapter_with_fks(self):
        """Adapter with sample FK data."""
        return MockIntrospectionAdapter([
            {
                "_table": "posts",
                "constraint_name": "posts_author_id_fkey",
                "column_name": "author_id",
                "foreign_table": "users",
                "foreign_column": "id",
                "on_delete": "CASCADE",
            },
            {
                "_table": "posts",
                "constraint_name": "posts_category_id_fkey",
                "column_name": "category_id",
                "foreign_table": "categories",
                "foreign_column": "id",
                "on_delete": "SET NULL",
            },
            {
                "_table": "comments",
                "constraint_name": "comments_post_id_fkey",
                "column_name": "post_id",
                "foreign_table": "posts",
                "foreign_column": "id",
                "on_delete": "CASCADE",
            },
            {
                "_table": "orders",
                "constraint_name": "orders_user_id_fkey",
                "column_name": "user_id",
                "foreign_table": "users",
                "foreign_column": "id",
                "on_delete": "RESTRICT",
            },
        ])
    
    @pytest.mark.asyncio
    async def test_returns_list(self, adapter_with_fks):
        """get_foreign_keys should return a list."""
        result = await adapter_with_fks.get_foreign_keys("posts")
        assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_returns_correct_count(self, adapter_with_fks):
        """Should return correct number of FKs."""
        result = await adapter_with_fks.get_foreign_keys("posts")
        assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_returns_empty_for_no_fks(self, adapter_with_fks):
        """Should return empty list for table with no FKs."""
        result = await adapter_with_fks.get_foreign_keys("users")
        assert result == []
    
    @pytest.mark.asyncio
    async def test_includes_constraint_name(self, adapter_with_fks):
        """Result should include constraint_name."""
        result = await adapter_with_fks.get_foreign_keys("posts")
        assert all("constraint_name" in fk for fk in result)
        assert result[0]["constraint_name"] == "posts_author_id_fkey"
    
    @pytest.mark.asyncio
    async def test_includes_column_name(self, adapter_with_fks):
        """Result should include column_name."""
        result = await adapter_with_fks.get_foreign_keys("posts")
        assert all("column_name" in fk for fk in result)
        assert result[0]["column_name"] == "author_id"
    
    @pytest.mark.asyncio
    async def test_includes_foreign_table(self, adapter_with_fks):
        """Result should include foreign_table."""
        result = await adapter_with_fks.get_foreign_keys("posts")
        assert all("foreign_table" in fk for fk in result)
        assert result[0]["foreign_table"] == "users"
    
    @pytest.mark.asyncio
    async def test_includes_foreign_column(self, adapter_with_fks):
        """Result should include foreign_column."""
        result = await adapter_with_fks.get_foreign_keys("posts")
        assert all("foreign_column" in fk for fk in result)
        assert result[0]["foreign_column"] == "id"
    
    @pytest.mark.asyncio
    async def test_includes_on_delete(self, adapter_with_fks):
        """Result should include on_delete action."""
        result = await adapter_with_fks.get_foreign_keys("posts")
        assert all("on_delete" in fk for fk in result)
        assert result[0]["on_delete"] == "CASCADE"
    
    @pytest.mark.asyncio
    async def test_different_on_delete_actions(self, adapter_with_fks):
        """Should correctly report different on_delete actions."""
        posts = await adapter_with_fks.get_foreign_keys("posts")
        orders = await adapter_with_fks.get_foreign_keys("orders")
        
        # posts has CASCADE and SET NULL
        actions = [fk["on_delete"] for fk in posts]
        assert "CASCADE" in actions
        assert "SET NULL" in actions
        
        # orders has RESTRICT
        assert orders[0]["on_delete"] == "RESTRICT"
    
    @pytest.mark.asyncio
    async def test_single_fk_table(self, adapter_with_fks):
        """Table with single FK."""
        result = await adapter_with_fks.get_foreign_keys("comments")
        assert len(result) == 1
        assert result[0]["constraint_name"] == "comments_post_id_fkey"


# =============================================================================
# Test has_constraint
# =============================================================================

class TestHasConstraint:
    """Test has_constraint method."""
    
    @pytest.fixture
    def adapter_with_constraints(self):
        """Adapter with sample constraint data."""
        return MockIntrospectionAdapter([
            {
                "_table": "posts",
                "constraint_name": "posts_author_id_fkey",
                "column_name": "author_id",
                "foreign_table": "users",
                "foreign_column": "id",
                "on_delete": "CASCADE",
            },
            {
                "_table": "posts",
                "constraint_name": "posts_pkey",
                "column_name": "id",
                "foreign_table": None,
                "foreign_column": None,
                "on_delete": None,
            },
        ])
    
    @pytest.mark.asyncio
    async def test_returns_true_for_existing(self, adapter_with_constraints):
        """Should return True for existing constraint."""
        result = await adapter_with_constraints.has_constraint("posts", "posts_author_id_fkey")
        assert result is True
    
    @pytest.mark.asyncio
    async def test_returns_false_for_nonexistent(self, adapter_with_constraints):
        """Should return False for non-existent constraint."""
        result = await adapter_with_constraints.has_constraint("posts", "nonexistent_fkey")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_returns_false_for_wrong_table(self, adapter_with_constraints):
        """Should return False for constraint on different table."""
        result = await adapter_with_constraints.has_constraint("users", "posts_author_id_fkey")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_checks_exact_name(self, adapter_with_constraints):
        """Should check exact constraint name."""
        result = await adapter_with_constraints.has_constraint("posts", "posts_author")
        assert result is False  # Partial match should not work


# =============================================================================
# Test FK Introspection with Various ON DELETE Actions
# =============================================================================

class TestOnDeleteIntrospection:
    """Test introspection of various ON DELETE actions."""
    
    @pytest.fixture
    def adapter_with_all_actions(self):
        """Adapter with all ON DELETE action types."""
        return MockIntrospectionAdapter([
            {"_table": "t1", "constraint_name": "cascade_fk", "on_delete": "CASCADE"},
            {"_table": "t2", "constraint_name": "set_null_fk", "on_delete": "SET NULL"},
            {"_table": "t3", "constraint_name": "set_default_fk", "on_delete": "SET DEFAULT"},
            {"_table": "t4", "constraint_name": "restrict_fk", "on_delete": "RESTRICT"},
            {"_table": "t5", "constraint_name": "no_action_fk", "on_delete": "NO ACTION"},
        ])
    
    @pytest.mark.asyncio
    async def test_cascade_introspection(self, adapter_with_all_actions):
        """Should correctly introspect CASCADE."""
        result = await adapter_with_all_actions.get_foreign_keys("t1")
        assert result[0]["on_delete"] == "CASCADE"
    
    @pytest.mark.asyncio
    async def test_set_null_introspection(self, adapter_with_all_actions):
        """Should correctly introspect SET NULL."""
        result = await adapter_with_all_actions.get_foreign_keys("t2")
        assert result[0]["on_delete"] == "SET NULL"
    
    @pytest.mark.asyncio
    async def test_set_default_introspection(self, adapter_with_all_actions):
        """Should correctly introspect SET DEFAULT."""
        result = await adapter_with_all_actions.get_foreign_keys("t3")
        assert result[0]["on_delete"] == "SET DEFAULT"
    
    @pytest.mark.asyncio
    async def test_restrict_introspection(self, adapter_with_all_actions):
        """Should correctly introspect RESTRICT."""
        result = await adapter_with_all_actions.get_foreign_keys("t4")
        assert result[0]["on_delete"] == "RESTRICT"
    
    @pytest.mark.asyncio
    async def test_no_action_introspection(self, adapter_with_all_actions):
        """Should correctly introspect NO ACTION."""
        result = await adapter_with_all_actions.get_foreign_keys("t5")
        assert result[0]["on_delete"] == "NO ACTION"


# =============================================================================
# Test Complex FK Scenarios
# =============================================================================

class TestComplexFKScenarios:
    """Test introspection with complex FK relationships."""
    
    @pytest.fixture
    def adapter_complex(self):
        """Adapter with complex FK scenarios."""
        return MockIntrospectionAdapter([
            # Self-referencing FK
            {
                "_table": "categories",
                "constraint_name": "categories_parent_id_fkey",
                "column_name": "parent_id",
                "foreign_table": "categories",
                "foreign_column": "id",
                "on_delete": "CASCADE",
            },
            # Multiple FKs to same table
            {
                "_table": "posts",
                "constraint_name": "posts_author_id_fkey",
                "column_name": "author_id",
                "foreign_table": "users",
                "foreign_column": "id",
                "on_delete": "CASCADE",
            },
            {
                "_table": "posts",
                "constraint_name": "posts_editor_id_fkey",
                "column_name": "editor_id",
                "foreign_table": "users",
                "foreign_column": "id",
                "on_delete": "SET NULL",
            },
        ])
    
    @pytest.mark.asyncio
    async def test_self_referencing_fk(self, adapter_complex):
        """Should correctly introspect self-referencing FK."""
        result = await adapter_complex.get_foreign_keys("categories")
        assert len(result) == 1
        assert result[0]["foreign_table"] == "categories"
        assert result[0]["column_name"] == "parent_id"
    
    @pytest.mark.asyncio
    async def test_multiple_fks_to_same_table(self, adapter_complex):
        """Should correctly introspect multiple FKs to same table."""
        result = await adapter_complex.get_foreign_keys("posts")
        
        # Should have 2 FKs, both referencing users
        assert len(result) == 2
        
        foreign_tables = [fk["foreign_table"] for fk in result]
        assert all(t == "users" for t in foreign_tables)
        
        columns = [fk["column_name"] for fk in result]
        assert "author_id" in columns
        assert "editor_id" in columns
    
    @pytest.mark.asyncio
    async def test_different_on_delete_same_ref_table(self, adapter_complex):
        """Multiple FKs to same table can have different on_delete."""
        result = await adapter_complex.get_foreign_keys("posts")
        
        on_delete_by_column = {fk["column_name"]: fk["on_delete"] for fk in result}
        
        assert on_delete_by_column["author_id"] == "CASCADE"
        assert on_delete_by_column["editor_id"] == "SET NULL"

