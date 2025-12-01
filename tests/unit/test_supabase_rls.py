"""
Comprehensive tests for PyNext Supabase Row Level Security.

Tests cover:
- Policy model and dataclass
- PolicyDiff model
- Policy decorators (@policy, @select_policy, etc.)
- Migration generation
- Policy patterns (own_data, public_read, etc.)
- RLS management (sync, diff, apply)

Total: 120 tests
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch, AsyncMock

from pynext.db.supabase.rls import (
    SupabaseRLS,
    Policy,
    PolicyDiff,
    RLSConfig,
    PolicyOperation,
    PolicyCommand,
    PolicyRegistry,
    policy,
    select_policy,
    insert_policy,
    update_policy,
    delete_policy,
    generate_rls_migration,
    generate_rls_down_migration,
    own_data_policy,
    public_read_policy,
    authenticated_only_policy,
    role_based_policy,
    _global_registry,
)
from pynext.db.supabase.exceptions import (
    RLSError,
    PolicySyntaxError,
    PolicyConflictError,
    SyncError,
    ServiceRoleRequiredError,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_supabase():
    """Create mock Supabase adapter."""
    supabase = Mock()
    supabase._initialized = True
    supabase._ensure_initialized = Mock()
    supabase.admin_client = None
    supabase.client = Mock()
    return supabase


@pytest.fixture
def rls(mock_supabase):
    """Create SupabaseRLS instance."""
    return SupabaseRLS(mock_supabase)


@pytest.fixture
def registry():
    """Create fresh PolicyRegistry."""
    return PolicyRegistry()


@pytest.fixture(autouse=True)
def clear_global_registry():
    """Clear global registry before each test."""
    _global_registry.clear()
    yield
    _global_registry.clear()


# =============================================================================
# POLICY OPERATION TESTS (10 tests)
# =============================================================================

class TestPolicyOperation:
    """Tests for PolicyOperation enum."""
    
    def test_operation_select(self):
        """PolicyOperation has SELECT."""
        assert PolicyOperation.SELECT.value == "SELECT"
    
    def test_operation_insert(self):
        """PolicyOperation has INSERT."""
        assert PolicyOperation.INSERT.value == "INSERT"
    
    def test_operation_update(self):
        """PolicyOperation has UPDATE."""
        assert PolicyOperation.UPDATE.value == "UPDATE"
    
    def test_operation_delete(self):
        """PolicyOperation has DELETE."""
        assert PolicyOperation.DELETE.value == "DELETE"
    
    def test_operation_all(self):
        """PolicyOperation has ALL."""
        assert PolicyOperation.ALL.value == "ALL"
    
    def test_policy_command_permissive(self):
        """PolicyCommand has PERMISSIVE."""
        assert PolicyCommand.PERMISSIVE.value == "PERMISSIVE"
    
    def test_policy_command_restrictive(self):
        """PolicyCommand has RESTRICTIVE."""
        assert PolicyCommand.RESTRICTIVE.value == "RESTRICTIVE"
    
    def test_operation_from_string(self):
        """PolicyOperation can be created from string."""
        assert PolicyOperation("SELECT") == PolicyOperation.SELECT
    
    def test_operation_case_insensitive(self):
        """PolicyOperation requires uppercase."""
        with pytest.raises(ValueError):
            PolicyOperation("select")
    
    def test_command_from_string(self):
        """PolicyCommand can be created from string."""
        assert PolicyCommand("PERMISSIVE") == PolicyCommand.PERMISSIVE


# =============================================================================
# POLICY MODEL TESTS (25 tests)
# =============================================================================

class TestPolicyModel:
    """Tests for Policy dataclass."""
    
    def test_policy_creation(self):
        """Policy can be created."""
        p = Policy(table="users", operation="SELECT", using="true")
        assert p.table == "users"
        assert p.operation == PolicyOperation.SELECT
    
    def test_policy_operation_normalization(self):
        """Policy normalizes operation to enum."""
        p = Policy(table="users", operation="SELECT")
        assert isinstance(p.operation, PolicyOperation)
    
    def test_policy_auto_name(self):
        """Policy auto-generates name."""
        p = Policy(table="users", operation="SELECT")
        assert p.name == "users_select_policy"
    
    def test_policy_custom_name(self):
        """Policy uses custom name."""
        p = Policy(table="users", operation="SELECT", name="custom_name")
        assert p.name == "custom_name"
    
    def test_policy_default_roles(self):
        """Policy has public role by default."""
        p = Policy(table="users", operation="SELECT")
        assert p.roles == ["public"]
    
    def test_policy_custom_roles(self):
        """Policy accepts custom roles."""
        p = Policy(table="users", operation="SELECT", roles=["admin", "editor"])
        assert p.roles == ["admin", "editor"]
    
    def test_policy_default_command(self):
        """Policy is PERMISSIVE by default."""
        p = Policy(table="users", operation="SELECT")
        assert p.command == PolicyCommand.PERMISSIVE
    
    def test_policy_restrictive(self):
        """Policy can be RESTRICTIVE."""
        p = Policy(table="users", operation="SELECT", command=PolicyCommand.RESTRICTIVE)
        assert p.command == PolicyCommand.RESTRICTIVE
    
    def test_policy_default_schema(self):
        """Policy uses public schema by default."""
        p = Policy(table="users", operation="SELECT")
        assert p.schema == "public"
    
    def test_policy_custom_schema(self):
        """Policy accepts custom schema."""
        p = Policy(table="users", operation="SELECT", schema="private")
        assert p.schema == "private"
    
    def test_policy_using_clause(self):
        """Policy stores USING clause."""
        p = Policy(table="users", operation="SELECT", using="auth.uid() = id")
        assert p.using == "auth.uid() = id"
    
    def test_policy_check_clause(self):
        """Policy stores CHECK clause."""
        p = Policy(table="users", operation="INSERT", check="auth.uid() = user_id")
        assert p.check == "auth.uid() = user_id"
    
    def test_policy_with_check_alias(self):
        """Policy accepts with_check as alias for check."""
        p = Policy(table="users", operation="INSERT", with_check="auth.uid() = user_id")
        assert p.check == "auth.uid() = user_id"
    
    def test_policy_description(self):
        """Policy stores description."""
        p = Policy(table="users", operation="SELECT", description="Users see own data")
        assert p.description == "Users see own data"
    
    def test_policy_qualified_table(self):
        """Policy.qualified_table returns schema.table."""
        p = Policy(table="users", operation="SELECT", schema="public")
        assert p.qualified_table == "public.users"
    
    def test_policy_to_sql_basic(self):
        """Policy.to_sql generates valid SQL."""
        p = Policy(table="users", operation="SELECT", using="true")
        sql = p.to_sql()
        assert "CREATE POLICY" in sql
        assert '"users"' in sql
        assert "FOR SELECT" in sql
        assert "USING" in sql
    
    def test_policy_to_sql_with_check(self):
        """Policy.to_sql includes WITH CHECK."""
        p = Policy(table="users", operation="INSERT", check="auth.uid() = user_id")
        sql = p.to_sql()
        assert "WITH CHECK" in sql
    
    def test_policy_to_sql_schema(self):
        """Policy.to_sql includes schema."""
        p = Policy(table="users", operation="SELECT", schema="private", using="true")
        sql = p.to_sql()
        assert '"private"."users"' in sql
    
    def test_policy_to_sql_roles(self):
        """Policy.to_sql includes roles."""
        p = Policy(table="users", operation="SELECT", roles=["admin"], using="true")
        sql = p.to_sql()
        assert "TO admin" in sql
    
    def test_policy_to_sql_command(self):
        """Policy.to_sql includes command type."""
        p = Policy(table="users", operation="SELECT", using="true")
        sql = p.to_sql()
        assert "AS PERMISSIVE" in sql
    
    def test_policy_to_drop_sql(self):
        """Policy.to_drop_sql generates DROP statement."""
        p = Policy(table="users", operation="SELECT", name="my_policy")
        sql = p.to_drop_sql()
        assert "DROP POLICY" in sql
        assert '"my_policy"' in sql
        assert "IF EXISTS" in sql
    
    def test_policy_to_dict(self):
        """Policy.to_dict serializes to dictionary."""
        p = Policy(table="users", operation="SELECT", using="true")
        d = p.to_dict()
        assert d["table"] == "users"
        assert d["operation"] == "SELECT"
    
    def test_policy_from_dict(self):
        """Policy.from_dict deserializes from dictionary."""
        d = {
            "table": "orders",
            "operation": "INSERT",
            "name": "order_policy",
            "using": "true",
            "check": "auth.uid() = user_id"
        }
        p = Policy.from_dict(d)
        assert p.table == "orders"
        assert p.name == "order_policy"
    
    def test_policy_sql_parentheses(self):
        """Policy.to_sql adds parentheses to expressions."""
        p = Policy(table="users", operation="SELECT", using="auth.uid() = id")
        sql = p.to_sql()
        assert "(auth.uid() = id)" in sql
    
    def test_policy_sql_existing_parentheses(self):
        """Policy.to_sql doesn't double parentheses."""
        p = Policy(table="users", operation="SELECT", using="(auth.uid() = id)")
        sql = p.to_sql()
        assert "((auth.uid() = id))" not in sql


# =============================================================================
# POLICY DIFF TESTS (15 tests)
# =============================================================================

class TestPolicyDiff:
    """Tests for PolicyDiff model."""
    
    def test_diff_empty(self):
        """PolicyDiff can be empty."""
        diff = PolicyDiff()
        assert diff.to_create == []
        assert diff.to_drop == []
        assert diff.to_update == []
    
    def test_diff_has_changes_false(self):
        """has_changes returns False when empty."""
        diff = PolicyDiff()
        assert diff.has_changes is False
    
    def test_diff_has_changes_create(self):
        """has_changes returns True with to_create."""
        diff = PolicyDiff(to_create=[Policy(table="users", operation="SELECT")])
        assert diff.has_changes is True
    
    def test_diff_has_changes_drop(self):
        """has_changes returns True with to_drop."""
        diff = PolicyDiff(to_drop=[Policy(table="users", operation="SELECT")])
        assert diff.has_changes is True
    
    def test_diff_has_changes_update(self):
        """has_changes returns True with to_update."""
        p = Policy(table="users", operation="SELECT")
        diff = PolicyDiff(to_update=[(p, p)])
        assert diff.has_changes is True
    
    def test_diff_summary_no_changes(self):
        """summary returns 'No changes' when empty."""
        diff = PolicyDiff()
        assert "No changes" in diff.summary()
    
    def test_diff_summary_create(self):
        """summary shows policies to create."""
        p = Policy(table="users", operation="SELECT", name="users_select")
        diff = PolicyDiff(to_create=[p])
        summary = diff.summary()
        assert "Create" in summary
        assert "users_select" in summary
    
    def test_diff_summary_drop(self):
        """summary shows policies to drop."""
        p = Policy(table="users", operation="SELECT", name="old_policy")
        diff = PolicyDiff(to_drop=[p])
        summary = diff.summary()
        assert "Drop" in summary
        assert "old_policy" in summary
    
    def test_diff_summary_update(self):
        """summary shows policies to update."""
        p = Policy(table="users", operation="SELECT", name="changing")
        diff = PolicyDiff(to_update=[(p, p)])
        summary = diff.summary()
        assert "Update" in summary
        assert "changing" in summary
    
    def test_diff_to_sql_create(self):
        """to_sql generates CREATE for new policies."""
        p = Policy(table="users", operation="SELECT", using="true")
        diff = PolicyDiff(to_create=[p])
        sql = diff.to_sql()
        assert "CREATE POLICY" in sql
    
    def test_diff_to_sql_drop(self):
        """to_sql generates DROP for old policies."""
        p = Policy(table="users", operation="SELECT", name="old")
        diff = PolicyDiff(to_drop=[p])
        sql = diff.to_sql()
        assert "DROP POLICY" in sql
    
    def test_diff_to_sql_update(self):
        """to_sql generates DROP then CREATE for updates."""
        p = Policy(table="users", operation="SELECT", name="updating", using="true")
        diff = PolicyDiff(to_update=[(p, p)])
        sql = diff.to_sql()
        assert "DROP POLICY" in sql
        assert "CREATE POLICY" in sql
    
    def test_diff_to_sql_order(self):
        """to_sql orders: drop, then create."""
        old = Policy(table="t1", operation="SELECT", name="old")
        new = Policy(table="t2", operation="SELECT", name="new", using="true")
        diff = PolicyDiff(to_drop=[old], to_create=[new])
        sql = diff.to_sql()
        drop_pos = sql.find("DROP")
        create_pos = sql.find("CREATE")
        assert drop_pos < create_pos
    
    def test_diff_unchanged(self):
        """PolicyDiff tracks unchanged policies."""
        p = Policy(table="users", operation="SELECT")
        diff = PolicyDiff(unchanged=[p])
        assert len(diff.unchanged) == 1
    
    def test_diff_empty_to_sql(self):
        """to_sql returns empty for no changes."""
        diff = PolicyDiff()
        assert diff.to_sql() == ""


# =============================================================================
# POLICY REGISTRY TESTS (10 tests)
# =============================================================================

class TestPolicyRegistry:
    """Tests for PolicyRegistry."""
    
    def test_register_policy(self, registry):
        """Registry can register policy."""
        p = Policy(table="users", operation="SELECT")
        registry.register(p)
        assert len(registry.get_all()) == 1
    
    def test_register_multiple_policies(self, registry):
        """Registry can register multiple policies."""
        p1 = Policy(table="users", operation="SELECT")
        p2 = Policy(table="orders", operation="INSERT")
        registry.register(p1)
        registry.register(p2)
        assert len(registry.get_all()) == 2
    
    def test_get_for_table(self, registry):
        """get_for_table returns table policies."""
        p1 = Policy(table="users", operation="SELECT")
        p2 = Policy(table="orders", operation="SELECT")
        registry.register(p1)
        registry.register(p2)
        
        users_policies = registry.get_for_table("users")
        
        assert len(users_policies) == 1
        assert users_policies[0].table == "users"
    
    def test_get_by_name(self, registry):
        """get_by_name returns specific policy."""
        p = Policy(table="users", operation="SELECT", name="users_select")
        registry.register(p)
        
        found = registry.get_by_name("users_select")
        
        assert found is not None
        assert found.name == "users_select"
    
    def test_get_by_name_not_found(self, registry):
        """get_by_name returns None for missing."""
        assert registry.get_by_name("nonexistent") is None
    
    def test_get_for_table_with_schema(self, registry):
        """get_for_table filters by schema."""
        p1 = Policy(table="users", operation="SELECT", schema="public")
        p2 = Policy(table="users", operation="SELECT", schema="private")
        registry.register(p1)
        registry.register(p2)
        
        private = registry.get_for_table("users", schema="private")
        
        assert len(private) == 1
        assert private[0].schema == "private"
    
    def test_clear_registry(self, registry):
        """clear empties registry."""
        registry.register(Policy(table="users", operation="SELECT"))
        registry.clear()
        assert registry.get_all() == []
    
    def test_get_all_returns_list(self, registry):
        """get_all returns list."""
        assert isinstance(registry.get_all(), list)
    
    def test_register_same_policy_twice(self, registry):
        """Registering same policy twice updates it."""
        p = Policy(table="users", operation="SELECT", name="unique_name")
        registry.register(p)
        registry.register(p)
        assert len(registry.get_all()) == 1
    
    def test_get_for_table_empty(self, registry):
        """get_for_table returns empty for unknown table."""
        assert registry.get_for_table("unknown") == []


# =============================================================================
# DECORATOR TESTS (20 tests)
# =============================================================================

class TestDecorators:
    """Tests for policy decorators."""
    
    def test_policy_decorator_registers(self):
        """@policy registers policy."""
        @policy("users", "select")
        def users_select():
            return "auth.uid() = id"
        
        policies = _global_registry.get_all()
        assert len(policies) >= 1
    
    def test_policy_decorator_uses_function_name(self):
        """@policy uses function name as policy name."""
        @policy("users", "select")
        def my_custom_policy():
            return "true"
        
        p = _global_registry.get_by_name("my_custom_policy")
        assert p is not None
    
    def test_policy_decorator_custom_name(self):
        """@policy accepts custom name."""
        @policy("users", "select", name="custom_policy_name")
        def ignored_name():
            return "true"
        
        p = _global_registry.get_by_name("custom_policy_name")
        assert p is not None
    
    def test_policy_decorator_docstring(self):
        """@policy captures docstring."""
        @policy("users", "select")
        def documented_policy():
            """This is the description."""
            return "true"
        
        policies = _global_registry.get_all()
        assert any(p.description == "This is the description." for p in policies)
    
    def test_policy_decorator_select(self):
        """@policy with select creates USING clause."""
        @policy("users", "select")
        def select_policy():
            return "auth.uid() = id"
        
        p = _global_registry.get_by_name("select_policy")
        assert p.using == "auth.uid() = id"
        assert p.check is None
    
    def test_policy_decorator_insert(self):
        """@policy with insert creates CHECK clause."""
        @policy("users", "insert")
        def insert_policy():
            return "auth.uid() = user_id"
        
        p = _global_registry.get_by_name("insert_policy")
        assert p.check == "auth.uid() = user_id"
    
    def test_policy_decorator_update(self):
        """@policy with update creates both clauses."""
        @policy("users", "update")
        def update_policy():
            return "auth.uid() = id"
        
        p = _global_registry.get_by_name("update_policy")
        assert p.using == "auth.uid() = id"
        assert p.check == "auth.uid() = id"
    
    def test_policy_decorator_delete(self):
        """@policy with delete creates USING clause."""
        @policy("users", "delete")
        def delete_policy():
            return "auth.uid() = id"
        
        p = _global_registry.get_by_name("delete_policy")
        assert p.using == "auth.uid() = id"
    
    def test_policy_decorator_all(self):
        """@policy with all creates both clauses."""
        @policy("users", "all")
        def all_policy():
            return "auth.uid() = id"
        
        p = _global_registry.get_by_name("all_policy")
        assert p.using == "auth.uid() = id"
        assert p.check == "auth.uid() = id"
    
    def test_policy_decorator_roles(self):
        """@policy accepts roles."""
        @policy("users", "select", roles=["admin"])
        def admin_policy():
            return "true"
        
        p = _global_registry.get_by_name("admin_policy")
        assert p.roles == ["admin"]
    
    def test_policy_decorator_command(self):
        """@policy accepts command."""
        @policy("users", "select", command=PolicyCommand.RESTRICTIVE)
        def restrictive_policy():
            return "true"
        
        p = _global_registry.get_by_name("restrictive_policy")
        assert p.command == PolicyCommand.RESTRICTIVE
    
    def test_policy_decorator_schema(self):
        """@policy accepts schema."""
        @policy("users", "select", schema="private")
        def private_policy():
            return "true"
        
        p = _global_registry.get_by_name("private_policy")
        assert p.schema == "private"
    
    def test_select_policy_shortcut(self):
        """@select_policy is shortcut for select."""
        @select_policy("users")
        def users_read():
            return "true"
        
        p = _global_registry.get_by_name("users_read")
        assert p.operation == PolicyOperation.SELECT
    
    def test_insert_policy_shortcut(self):
        """@insert_policy is shortcut for insert."""
        @insert_policy("users")
        def users_create():
            return "true"
        
        p = _global_registry.get_by_name("users_create")
        assert p.operation == PolicyOperation.INSERT
    
    def test_update_policy_shortcut(self):
        """@update_policy is shortcut for update."""
        @update_policy("users")
        def users_modify():
            return "true"
        
        p = _global_registry.get_by_name("users_modify")
        assert p.operation == PolicyOperation.UPDATE
    
    def test_delete_policy_shortcut(self):
        """@delete_policy is shortcut for delete."""
        @delete_policy("users")
        def users_remove():
            return "true"
        
        p = _global_registry.get_by_name("users_remove")
        assert p.operation == PolicyOperation.DELETE
    
    def test_decorator_attaches_policy(self):
        """Decorator attaches policy to function."""
        @policy("users", "select")
        def func_with_policy():
            return "true"
        
        assert hasattr(func_with_policy, "_policy")
        assert func_with_policy._policy.table == "users"
    
    def test_decorator_preserves_function(self):
        """Decorator preserves function."""
        @policy("users", "select")
        def my_function():
            return "my_expression"
        
        assert my_function() == "my_expression"
    
    def test_decorator_preserves_name(self):
        """Decorator preserves function name."""
        @policy("users", "select")
        def named_function():
            return "true"
        
        assert named_function.__name__ == "named_function"
    
    def test_multiple_decorators_different_tables(self):
        """Multiple decorators on different tables."""
        @policy("users", "select")
        def users_policy():
            return "true"
        
        @policy("orders", "select")
        def orders_policy():
            return "true"
        
        policies = _global_registry.get_all()
        tables = [p.table for p in policies]
        assert "users" in tables
        assert "orders" in tables


# =============================================================================
# MIGRATION GENERATION TESTS (15 tests)
# =============================================================================

class TestMigrationGeneration:
    """Tests for migration generation."""
    
    def test_generate_migration_empty(self):
        """generate_rls_migration handles empty registry."""
        sql = generate_rls_migration()
        assert "No policies" in sql
    
    def test_generate_migration_with_policy(self):
        """generate_rls_migration includes policies."""
        @policy("users", "select")
        def users_policy():
            return "true"
        
        sql = generate_rls_migration()
        assert "CREATE POLICY" in sql
    
    def test_generate_migration_includes_enable(self):
        """generate_rls_migration includes ENABLE RLS."""
        @policy("users", "select")
        def users_policy():
            return "true"
        
        sql = generate_rls_migration()
        assert "ENABLE ROW LEVEL SECURITY" in sql
    
    def test_generate_migration_skip_enable(self):
        """generate_rls_migration can skip ENABLE."""
        @policy("users", "select")
        def users_policy():
            return "true"
        
        sql = generate_rls_migration(include_enable=False)
        assert "ENABLE ROW LEVEL SECURITY" not in sql
    
    def test_generate_migration_header(self):
        """generate_rls_migration includes header."""
        @policy("users", "select")
        def users_policy():
            return "true"
        
        sql = generate_rls_migration()
        assert "RLS Policies Migration" in sql
    
    def test_generate_migration_timestamp(self):
        """generate_rls_migration includes timestamp."""
        @policy("users", "select")
        def users_policy():
            return "true"
        
        sql = generate_rls_migration()
        assert "Generated at:" in sql
    
    def test_generate_migration_groups_by_table(self):
        """generate_rls_migration groups policies by table."""
        @policy("users", "select")
        def users_select():
            return "true"
        
        @policy("users", "insert")
        def users_insert():
            return "true"
        
        sql = generate_rls_migration()
        # Should have one ENABLE per table
        assert sql.count("ENABLE ROW LEVEL SECURITY") == 1
    
    def test_generate_migration_includes_description(self):
        """generate_rls_migration includes policy descriptions."""
        @policy("users", "select")
        def documented():
            """My description."""
            return "true"
        
        sql = generate_rls_migration()
        assert "My description" in sql
    
    def test_generate_down_migration_empty(self):
        """generate_rls_down_migration handles empty registry."""
        sql = generate_rls_down_migration()
        assert "No policies" in sql
    
    def test_generate_down_migration(self):
        """generate_rls_down_migration creates DROP statements."""
        @policy("users", "select")
        def users_policy():
            return "true"
        
        sql = generate_rls_down_migration()
        assert "DROP POLICY" in sql
    
    def test_generate_down_migration_header(self):
        """generate_rls_down_migration includes header."""
        @policy("users", "select")
        def users_policy():
            return "true"
        
        sql = generate_rls_down_migration()
        assert "Rollback" in sql
    
    def test_generate_migration_multiple_tables(self):
        """generate_rls_migration handles multiple tables."""
        @policy("users", "select")
        def users_policy():
            return "true"
        
        @policy("orders", "select")
        def orders_policy():
            return "true"
        
        sql = generate_rls_migration()
        assert sql.count("ENABLE ROW LEVEL SECURITY") == 2
    
    def test_generate_migration_complex_expression(self):
        """generate_rls_migration handles complex expressions."""
        @policy("posts", "select")
        def complex_policy():
            return """
            CASE 
                WHEN is_public = true THEN true
                ELSE auth.uid() = author_id
            END
            """
        
        sql = generate_rls_migration()
        assert "CASE" in sql
    
    def test_generate_migration_private_schema(self):
        """generate_rls_migration handles private schema."""
        @policy("users", "select", schema="private")
        def private_policy():
            return "true"
        
        sql = generate_rls_migration()
        assert '"private"."users"' in sql
    
    def test_generate_migration_restrictive(self):
        """generate_rls_migration handles RESTRICTIVE."""
        @policy("users", "select", command=PolicyCommand.RESTRICTIVE)
        def restrictive():
            return "true"
        
        sql = generate_rls_migration()
        assert "AS RESTRICTIVE" in sql


# =============================================================================
# POLICY PATTERNS TESTS (10 tests)
# =============================================================================

class TestPolicyPatterns:
    """Tests for built-in policy patterns."""
    
    def test_own_data_policy(self):
        """own_data_policy creates correct policy."""
        p = own_data_policy("orders")
        assert p.table == "orders"
        assert p.operation == PolicyOperation.ALL
        assert "user_id" in p.using
    
    def test_own_data_policy_custom_column(self):
        """own_data_policy accepts custom column."""
        p = own_data_policy("orders", user_column="customer_id")
        assert "customer_id" in p.using
    
    def test_own_data_policy_name(self):
        """own_data_policy has descriptive name."""
        p = own_data_policy("orders")
        assert "orders" in p.name
        assert "own_data" in p.name
    
    def test_public_read_policy(self):
        """public_read_policy creates SELECT policy."""
        p = public_read_policy("posts")
        assert p.table == "posts"
        assert p.operation == PolicyOperation.SELECT
        assert p.using == "true"
    
    def test_public_read_policy_name(self):
        """public_read_policy has descriptive name."""
        p = public_read_policy("posts")
        assert "posts" in p.name
        assert "public_read" in p.name
    
    def test_authenticated_only_policy(self):
        """authenticated_only_policy requires auth."""
        p = authenticated_only_policy("secure", PolicyOperation.SELECT)
        assert "authenticated" in p.using
    
    def test_authenticated_only_insert(self):
        """authenticated_only_policy with INSERT has check."""
        p = authenticated_only_policy("secure", PolicyOperation.INSERT)
        assert p.check is not None
        assert "authenticated" in p.check
    
    def test_role_based_policy(self):
        """role_based_policy checks role."""
        p = role_based_policy("admin_data", PolicyOperation.SELECT, "admin")
        assert "admin" in p.using
    
    def test_role_based_policy_name(self):
        """role_based_policy has descriptive name."""
        p = role_based_policy("data", PolicyOperation.SELECT, "admin")
        assert "admin" in p.name
    
    def test_pattern_returns_policy(self):
        """All patterns return Policy objects."""
        assert isinstance(own_data_policy("t"), Policy)
        assert isinstance(public_read_policy("t"), Policy)
        assert isinstance(authenticated_only_policy("t", PolicyOperation.SELECT), Policy)
        assert isinstance(role_based_policy("t", PolicyOperation.SELECT, "r"), Policy)


# =============================================================================
# RLS MANAGER TESTS (15 tests)
# =============================================================================

class TestRLSManager:
    """Tests for SupabaseRLS class."""
    
    def test_get_local_policies(self, rls):
        """get_local_policies returns registered policies."""
        @policy("users", "select")
        def users_policy():
            return "true"
        
        policies = rls.get_local_policies()
        assert len(policies) >= 1
    
    def test_get_local_policies_for_table(self, rls):
        """get_local_policies_for_table filters by table."""
        @policy("users", "select")
        def users_policy():
            return "true"
        
        @policy("orders", "select")
        def orders_policy():
            return "true"
        
        policies = rls.get_local_policies_for_table("users")
        assert all(p.table == "users" for p in policies)
    
    @pytest.mark.asyncio
    async def test_get_remote_policies_requires_admin(self, rls):
        """get_remote_policies requires service_role_key."""
        with pytest.raises(ServiceRoleRequiredError):
            await rls.get_remote_policies()
    
    @pytest.mark.asyncio
    async def test_sync_requires_admin(self, rls):
        """sync requires service_role_key."""
        with pytest.raises(ServiceRoleRequiredError):
            await rls.sync()
    
    def test_generate_migration(self, rls):
        """generate_migration returns SQL."""
        @policy("users", "select")
        def users_policy():
            return "true"
        
        sql = rls.generate_migration()
        assert "CREATE POLICY" in sql
    
    def test_generate_rollback(self, rls):
        """generate_rollback returns SQL."""
        @policy("users", "select")
        def users_policy():
            return "true"
        
        sql = rls.generate_rollback()
        assert "DROP POLICY" in sql
    
    @pytest.mark.asyncio
    async def test_enable_rls_requires_admin(self, rls):
        """enable_rls requires service_role_key."""
        with pytest.raises(ServiceRoleRequiredError):
            await rls.enable_rls("users")
    
    @pytest.mark.asyncio
    async def test_disable_rls_requires_admin(self, rls):
        """disable_rls requires service_role_key."""
        with pytest.raises(ServiceRoleRequiredError):
            await rls.disable_rls("users")
    
    @pytest.mark.asyncio
    async def test_apply_requires_admin(self, rls):
        """apply requires service_role_key."""
        policies = [Policy(table="users", operation="SELECT", using="true")]
        with pytest.raises(ServiceRoleRequiredError):
            await rls.apply(policies)
    
    @pytest.mark.asyncio
    async def test_drop_requires_admin(self, rls):
        """drop requires service_role_key."""
        p = Policy(table="users", operation="SELECT")
        with pytest.raises(ServiceRoleRequiredError):
            await rls.drop(p)
    
    def test_rls_config_defaults(self):
        """RLSConfig has sensible defaults."""
        config = RLSConfig()
        assert config.auto_enable is True
        assert config.sync_on_start is False
    
    def test_rls_config_custom(self):
        """RLSConfig accepts custom values."""
        config = RLSConfig(auto_enable=False, migration_dir="db/migrations")
        assert config.auto_enable is False
        assert config.migration_dir == "db/migrations"
    
    def test_rls_with_config(self, mock_supabase):
        """SupabaseRLS accepts config."""
        config = RLSConfig(auto_enable=False)
        rls = SupabaseRLS(mock_supabase, config)
        assert rls._config.auto_enable is False
    
    def test_rls_registry_reference(self, rls):
        """SupabaseRLS uses global registry."""
        @policy("test", "select")
        def test_policy():
            return "true"
        
        # RLS should see policies registered globally
        assert len(rls.get_local_policies()) >= 1
    
    def test_get_local_policies_empty(self, rls):
        """get_local_policies returns empty when none registered."""
        policies = rls.get_local_policies()
        assert policies == []

