"""
PyNext Supabase Row Level Security (RLS).

Provides Python decorators and utilities for managing RLS policies.

What is RLS?
    Row Level Security lets you control which rows a user can access.
    Instead of filtering in application code, PostgreSQL enforces rules
    at the database level - impossible to bypass.

Why Decorators?
    SQL policy definitions are hard to manage:
    - Scattered across migration files
    - Easy to forget when adding new tables
    - Hard to review in code review
    
    With decorators:
    - Policies live next to your models
    - Easy to read and understand
    - Can be version controlled
    - Auto-generate migrations

Usage (Stupid Easy):
    from pynext.db.supabase import policy
    
    @policy("users", "select")
    def users_can_view_own():
        '''Users can only see their own data'''
        return "auth.uid() = id"
    
    @policy("posts", "select")
    def posts_public_or_own():
        '''Public posts visible to all, private only to owner'''
        return "is_public = true OR auth.uid() = author_id"
    
    # Generate migration
    migration = generate_rls_migration()
    
    # Or sync directly
    await db.rls.sync()
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union, TYPE_CHECKING
import functools
import textwrap

from .exceptions import (
    RLSError,
    PolicySyntaxError,
    PolicyConflictError,
    SyncError,
    ServiceRoleRequiredError,
)

if TYPE_CHECKING:
    from .adapter import Supabase


# =============================================================================
# ENUMS AND TYPES
# =============================================================================

class PolicyOperation(str, Enum):
    """Database operations that can have policies."""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    ALL = "ALL"


class PolicyCommand(str, Enum):
    """SQL commands for policies."""
    PERMISSIVE = "PERMISSIVE"
    RESTRICTIVE = "RESTRICTIVE"


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class Policy:
    """
    Definition of an RLS policy.
    
    Attributes:
        table: Table the policy applies to
        operation: Operation (SELECT, INSERT, UPDATE, DELETE)
        name: Policy name (auto-generated if not provided)
        using: USING clause - which rows can be seen
        check: WITH CHECK clause - which rows can be written
        roles: Roles the policy applies to (default: public)
        command: PERMISSIVE (default) or RESTRICTIVE
        schema: Database schema (default: public)
        description: Human-readable description
    
    Example:
        Policy(
            table="orders",
            operation="select",
            name="users_see_own_orders",
            using="auth.uid() = user_id",
        )
    """
    table: str
    operation: Union[str, PolicyOperation]
    name: Optional[str] = None
    using: Optional[str] = None
    check: Optional[str] = None
    with_check: Optional[str] = None  # Alias for check
    roles: List[str] = field(default_factory=lambda: ["public"])
    command: PolicyCommand = PolicyCommand.PERMISSIVE
    schema: str = "public"
    description: Optional[str] = None
    
    def __post_init__(self):
        # Normalize operation
        if isinstance(self.operation, str):
            self.operation = PolicyOperation(self.operation.upper())
        
        # Auto-generate name if not provided
        if not self.name:
            self.name = f"{self.table}_{self.operation.value.lower()}_policy"
        
        # Handle with_check alias
        if self.with_check and not self.check:
            self.check = self.with_check
    
    @property
    def qualified_table(self) -> str:
        """Get schema-qualified table name."""
        return f"{self.schema}.{self.table}"
    
    def to_sql(self) -> str:
        """Generate SQL CREATE POLICY statement."""
        parts = [f'CREATE POLICY "{self.name}"']
        parts.append(f'ON "{self.schema}"."{self.table}"')
        parts.append(f"AS {self.command.value}")
        parts.append(f"FOR {self.operation.value}")
        parts.append(f"TO {', '.join(self.roles)}")
        
        if self.using:
            using_clean = self.using.strip()
            if not using_clean.startswith("("):
                using_clean = f"({using_clean})"
            parts.append(f"USING {using_clean}")
        
        if self.check:
            check_clean = self.check.strip()
            if not check_clean.startswith("("):
                check_clean = f"({check_clean})"
            parts.append(f"WITH CHECK {check_clean}")
        
        return "\n".join(parts) + ";"
    
    def to_drop_sql(self) -> str:
        """Generate SQL DROP POLICY statement."""
        return f'DROP POLICY IF EXISTS "{self.name}" ON "{self.schema}"."{self.table}";'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "table": self.table,
            "operation": self.operation.value,
            "name": self.name,
            "using": self.using,
            "check": self.check,
            "roles": self.roles,
            "command": self.command.value,
            "schema": self.schema,
            "description": self.description,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Policy":
        """Create from dictionary."""
        return cls(
            table=data["table"],
            operation=data["operation"],
            name=data.get("name"),
            using=data.get("using"),
            check=data.get("check"),
            roles=data.get("roles", ["public"]),
            command=PolicyCommand(data.get("command", "PERMISSIVE")),
            schema=data.get("schema", "public"),
            description=data.get("description"),
        )


@dataclass
class PolicyDiff:
    """
    Difference between local and remote policies.
    
    Attributes:
        to_create: Policies that exist locally but not remotely
        to_drop: Policies that exist remotely but not locally
        to_update: Policies that differ between local and remote
        unchanged: Policies that are the same
    """
    to_create: List[Policy] = field(default_factory=list)
    to_drop: List[Policy] = field(default_factory=list)
    to_update: List[tuple] = field(default_factory=list)  # (local, remote) pairs
    unchanged: List[Policy] = field(default_factory=list)
    
    @property
    def has_changes(self) -> bool:
        """Check if there are any changes."""
        return bool(self.to_create or self.to_drop or self.to_update)
    
    def summary(self) -> str:
        """Get human-readable summary of changes."""
        lines = []
        if self.to_create:
            lines.append(f"Create {len(self.to_create)} policies:")
            for p in self.to_create:
                lines.append(f"  + {p.name} on {p.table}")
        if self.to_drop:
            lines.append(f"Drop {len(self.to_drop)} policies:")
            for p in self.to_drop:
                lines.append(f"  - {p.name} on {p.table}")
        if self.to_update:
            lines.append(f"Update {len(self.to_update)} policies:")
            for local, _ in self.to_update:
                lines.append(f"  ~ {local.name} on {local.table}")
        if not lines:
            lines.append("No changes")
        return "\n".join(lines)
    
    def to_sql(self) -> str:
        """Generate SQL for all changes."""
        statements = []
        
        # Drop old policies first
        for policy in self.to_drop:
            statements.append(policy.to_drop_sql())
        
        # Drop policies to update
        for local, _ in self.to_update:
            statements.append(local.to_drop_sql())
        
        # Create new policies
        for policy in self.to_create:
            statements.append(policy.to_sql())
        
        # Create updated policies
        for local, _ in self.to_update:
            statements.append(local.to_sql())
        
        return "\n\n".join(statements)


@dataclass
class RLSConfig:
    """
    Configuration for RLS management.
    
    Attributes:
        auto_enable: Auto-enable RLS on tables with policies
        sync_on_start: Sync policies when adapter starts
        migration_dir: Directory for migration files
    """
    auto_enable: bool = True
    sync_on_start: bool = False
    migration_dir: str = "migrations"


# =============================================================================
# POLICY REGISTRY
# =============================================================================

class PolicyRegistry:
    """
    Stores all registered RLS policies.
    
    Policies are registered via the @policy decorator.
    """
    
    def __init__(self):
        self._policies: Dict[str, Policy] = {}
    
    def register(self, policy: Policy):
        """Register a policy."""
        key = f"{policy.schema}.{policy.table}.{policy.operation.value}.{policy.name}"
        self._policies[key] = policy
    
    def get_all(self) -> List[Policy]:
        """Get all registered policies."""
        return list(self._policies.values())
    
    def get_for_table(self, table: str, schema: str = "public") -> List[Policy]:
        """Get policies for a specific table."""
        return [
            p for p in self._policies.values()
            if p.table == table and p.schema == schema
        ]
    
    def get_by_name(self, name: str) -> Optional[Policy]:
        """Get a policy by name."""
        for p in self._policies.values():
            if p.name == name:
                return p
        return None
    
    def clear(self):
        """Clear all registered policies."""
        self._policies.clear()


# Global registry
_global_registry = PolicyRegistry()


# =============================================================================
# DECORATORS
# =============================================================================

def policy(
    table: str,
    operation: Union[str, PolicyOperation],
    *,
    name: Optional[str] = None,
    roles: Optional[List[str]] = None,
    command: PolicyCommand = PolicyCommand.PERMISSIVE,
    schema: str = "public",
):
    """
    Decorator to define an RLS policy.
    
    The decorated function should return the SQL expression for the policy.
    The function's docstring becomes the policy description.
    
    Args:
        table: Table the policy applies to
        operation: SELECT, INSERT, UPDATE, DELETE, or ALL
        name: Policy name (auto-generated from function name if not provided)
        roles: Roles the policy applies to (default: ["public"])
        command: PERMISSIVE (default) or RESTRICTIVE
        schema: Database schema (default: "public")
    
    Example:
        @policy("users", "select")
        def users_can_view_own():
            '''Users can only see their own row'''
            return "auth.uid() = id"
        
        @policy("posts", "select", name="posts_public_visible")
        def posts_select():
            '''Anyone can see public posts'''
            return "is_public = true"
        
        @policy("orders", "insert", command=PolicyCommand.RESTRICTIVE)
        def orders_insert():
            '''Users can only create orders for themselves'''
            return "auth.uid() = user_id"
    """
    def decorator(func: Callable) -> Callable:
        # Get expression from function
        expression = func()
        
        # Determine if it's USING or CHECK based on operation
        op = PolicyOperation(operation.upper()) if isinstance(operation, str) else operation
        
        using = None
        check = None
        
        if op in (PolicyOperation.SELECT, PolicyOperation.DELETE):
            using = expression
        elif op == PolicyOperation.INSERT:
            check = expression
        elif op == PolicyOperation.UPDATE:
            # UPDATE uses both USING and CHECK
            using = expression
            check = expression
        elif op == PolicyOperation.ALL:
            using = expression
            check = expression
        
        # Create policy
        policy_obj = Policy(
            table=table,
            operation=op,
            name=name or func.__name__,
            using=using,
            check=check,
            roles=roles or ["public"],
            command=command,
            schema=schema,
            description=func.__doc__,
        )
        
        # Register
        _global_registry.register(policy_obj)
        
        @functools.wraps(func)
        def wrapper():
            return expression
        
        # Attach policy to function for inspection
        wrapper._policy = policy_obj
        
        return wrapper
    
    return decorator


def select_policy(table: str, **kwargs):
    """Shortcut for @policy(table, "select")."""
    return policy(table, PolicyOperation.SELECT, **kwargs)


def insert_policy(table: str, **kwargs):
    """Shortcut for @policy(table, "insert")."""
    return policy(table, PolicyOperation.INSERT, **kwargs)


def update_policy(table: str, **kwargs):
    """Shortcut for @policy(table, "update")."""
    return policy(table, PolicyOperation.UPDATE, **kwargs)


def delete_policy(table: str, **kwargs):
    """Shortcut for @policy(table, "delete")."""
    return policy(table, PolicyOperation.DELETE, **kwargs)


# =============================================================================
# MIGRATION GENERATION
# =============================================================================

def generate_rls_migration(
    name: Optional[str] = None,
    include_enable: bool = True,
) -> str:
    """
    Generate a SQL migration file from registered policies.
    
    Args:
        name: Optional name for the migration
        include_enable: Include ALTER TABLE ... ENABLE ROW LEVEL SECURITY
    
    Returns:
        SQL migration as a string
    
    Example:
        migration = generate_rls_migration()
        
        # Save to file
        with open("migrations/001_rls_policies.sql", "w") as f:
            f.write(migration)
    """
    policies = _global_registry.get_all()
    
    if not policies:
        return "-- No policies registered\n"
    
    lines = []
    lines.append(f"-- RLS Policies Migration")
    lines.append(f"-- Generated at: {datetime.now().isoformat()}")
    lines.append("")
    
    # Group by table
    tables: Dict[str, List[Policy]] = {}
    for p in policies:
        key = f"{p.schema}.{p.table}"
        if key not in tables:
            tables[key] = []
        tables[key].append(p)
    
    for table_key, table_policies in tables.items():
        schema, table = table_key.split(".")
        
        lines.append(f"-- Policies for {table_key}")
        lines.append("")
        
        # Enable RLS
        if include_enable:
            lines.append(f'ALTER TABLE "{schema}"."{table}" ENABLE ROW LEVEL SECURITY;')
            lines.append("")
        
        # Create policies
        for p in table_policies:
            if p.description:
                lines.append(f"-- {p.description}")
            lines.append(p.to_sql())
            lines.append("")
    
    return "\n".join(lines)


def generate_rls_down_migration() -> str:
    """
    Generate a SQL migration to remove all registered policies.
    
    Returns:
        SQL migration as a string
    """
    policies = _global_registry.get_all()
    
    if not policies:
        return "-- No policies to remove\n"
    
    lines = []
    lines.append("-- RLS Policies Rollback")
    lines.append(f"-- Generated at: {datetime.now().isoformat()}")
    lines.append("")
    
    for p in policies:
        lines.append(p.to_drop_sql())
    
    return "\n".join(lines)


# =============================================================================
# MAIN RLS CLASS
# =============================================================================

class SupabaseRLS:
    """
    Supabase Row Level Security management.
    
    Provides:
    - Access to registered policies
    - Diff between local and remote policies
    - Sync policies to Supabase
    - Get current policies from database
    
    Usage:
        # After registering policies with @policy
        
        # Check differences
        diff = await db.rls.diff()
        print(diff.summary())
        
        # Preview changes
        await db.rls.sync(dry_run=True)
        
        # Apply changes
        await db.rls.sync()
    """
    
    def __init__(
        self,
        supabase: "Supabase",
        config: Optional[RLSConfig] = None,
    ):
        self._supabase = supabase
        self._config = config or RLSConfig()
        self._registry = _global_registry
    
    # =========================================================================
    # READ OPERATIONS
    # =========================================================================
    
    def get_local_policies(self) -> List[Policy]:
        """Get all locally registered policies."""
        return self._registry.get_all()
    
    def get_local_policies_for_table(
        self,
        table: str,
        schema: str = "public",
    ) -> List[Policy]:
        """Get locally registered policies for a table."""
        return self._registry.get_for_table(table, schema)
    
    async def get_remote_policies(
        self,
        table: Optional[str] = None,
        schema: str = "public",
    ) -> List[Policy]:
        """
        Get policies from the Supabase database.
        
        Requires service_role_key.
        
        Args:
            table: Specific table (None for all tables)
            schema: Database schema
        
        Returns:
            List of Policy objects
        """
        admin_client = self._supabase.admin_client
        if not admin_client:
            raise ServiceRoleRequiredError(operation="get_remote_policies")
        
        try:
            # Query pg_policies system view
            query = admin_client.table("pg_policies").select("*")
            
            if table:
                query = query.eq("tablename", table)
            if schema:
                query = query.eq("schemaname", schema)
            
            result = query.execute()
            
            return [
                Policy(
                    table=row["tablename"],
                    operation=row["cmd"],
                    name=row["policyname"],
                    using=row.get("qual"),
                    check=row.get("with_check"),
                    roles=row.get("roles", ["public"]),
                    command=PolicyCommand(row.get("permissive", "PERMISSIVE")),
                    schema=row["schemaname"],
                )
                for row in result.data or []
            ]
            
        except Exception as e:
            # Fall back to raw SQL query
            try:
                sql = """
                SELECT 
                    schemaname,
                    tablename,
                    policyname,
                    permissive,
                    roles,
                    cmd,
                    qual,
                    with_check
                FROM pg_policies
                WHERE schemaname = $1
                """
                params = [schema]
                
                if table:
                    sql += " AND tablename = $2"
                    params.append(table)
                
                result = await self._supabase.client.postgrest.rpc(
                    "exec_sql",
                    {"sql": sql, "params": params}
                ).execute()
                
                return [
                    Policy(
                        table=row["tablename"],
                        operation=row["cmd"],
                        name=row["policyname"],
                        using=row.get("qual"),
                        check=row.get("with_check"),
                        schema=row["schemaname"],
                    )
                    for row in result.data or []
                ]
                
            except Exception:
                raise RLSError(
                    message=f"Failed to get remote policies: {e}",
                    details={"table": table, "schema": schema}
                )
    
    # =========================================================================
    # DIFF AND SYNC
    # =========================================================================
    
    async def diff(
        self,
        table: Optional[str] = None,
        schema: str = "public",
    ) -> PolicyDiff:
        """
        Compare local policies with remote policies.
        
        Args:
            table: Specific table (None for all)
            schema: Database schema
        
        Returns:
            PolicyDiff showing what needs to change
        """
        local = self.get_local_policies()
        remote = await self.get_remote_policies(table, schema)
        
        if table:
            local = [p for p in local if p.table == table and p.schema == schema]
        
        # Build lookup maps
        local_by_key = {
            (p.schema, p.table, p.name): p
            for p in local
        }
        remote_by_key = {
            (p.schema, p.table, p.name): p
            for p in remote
        }
        
        diff = PolicyDiff()
        
        # Find policies to create (in local, not in remote)
        for key, p in local_by_key.items():
            if key not in remote_by_key:
                diff.to_create.append(p)
            else:
                # Check if different
                remote_p = remote_by_key[key]
                if self._policies_differ(p, remote_p):
                    diff.to_update.append((p, remote_p))
                else:
                    diff.unchanged.append(p)
        
        # Find policies to drop (in remote, not in local)
        for key, p in remote_by_key.items():
            if key not in local_by_key:
                diff.to_drop.append(p)
        
        return diff
    
    def _policies_differ(self, local: Policy, remote: Policy) -> bool:
        """Check if two policies are different."""
        # Normalize expressions for comparison
        def normalize(expr: Optional[str]) -> str:
            if not expr:
                return ""
            return " ".join(expr.strip().split())
        
        if normalize(local.using) != normalize(remote.using):
            return True
        if normalize(local.check) != normalize(remote.check):
            return True
        if local.operation != remote.operation:
            return True
        
        return False
    
    async def sync(
        self,
        dry_run: bool = False,
        table: Optional[str] = None,
        schema: str = "public",
    ) -> PolicyDiff:
        """
        Sync local policies to Supabase.
        
        Requires service_role_key.
        
        Args:
            dry_run: If True, only show what would be done
            table: Specific table (None for all)
            schema: Database schema
        
        Returns:
            PolicyDiff showing what was/would be changed
        """
        admin_client = self._supabase.admin_client
        if not admin_client:
            raise ServiceRoleRequiredError(operation="sync")
        
        diff = await self.diff(table, schema)
        
        if not diff.has_changes:
            return diff
        
        if dry_run:
            print("Dry run - would execute:")
            print(diff.to_sql())
            return diff
        
        # Execute changes
        try:
            sql = diff.to_sql()
            
            # Execute via RPC or raw SQL
            await self._execute_sql(sql)
            
        except Exception as e:
            raise SyncError(reason=str(e))
        
        return diff
    
    async def _execute_sql(self, sql: str):
        """Execute raw SQL (requires service role)."""
        admin_client = self._supabase.admin_client
        if not admin_client:
            raise ServiceRoleRequiredError(operation="_execute_sql")
        
        # Try RPC first
        try:
            await admin_client.rpc("exec_sql", {"sql": sql}).execute()
            return
        except Exception:
            pass
        
        # Fall back to direct execution if available
        try:
            # This depends on how the underlying client handles raw SQL
            await admin_client.postgrest.rpc("", {"query": sql}).execute()
        except Exception as e:
            raise RLSError(message=f"Failed to execute SQL: {e}")
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    async def enable_rls(self, table: str, schema: str = "public"):
        """
        Enable RLS on a table.
        
        Args:
            table: Table name
            schema: Database schema
        """
        sql = f'ALTER TABLE "{schema}"."{table}" ENABLE ROW LEVEL SECURITY;'
        await self._execute_sql(sql)
    
    async def disable_rls(self, table: str, schema: str = "public"):
        """
        Disable RLS on a table.
        
        Warning: This removes all row-level access control!
        
        Args:
            table: Table name
            schema: Database schema
        """
        sql = f'ALTER TABLE "{schema}"."{table}" DISABLE ROW LEVEL SECURITY;'
        await self._execute_sql(sql)
    
    async def apply(self, policies: List[Policy]):
        """
        Apply a list of policies.
        
        Args:
            policies: Policies to apply
        """
        for p in policies:
            sql = p.to_sql()
            await self._execute_sql(sql)
    
    async def drop(self, policy: Policy):
        """
        Drop a specific policy.
        
        Args:
            policy: Policy to drop
        """
        sql = policy.to_drop_sql()
        await self._execute_sql(sql)
    
    def generate_migration(self, name: Optional[str] = None) -> str:
        """
        Generate a migration from registered policies.
        
        Returns:
            SQL migration string
        """
        return generate_rls_migration(name)
    
    def generate_rollback(self) -> str:
        """
        Generate a rollback migration.
        
        Returns:
            SQL rollback string
        """
        return generate_rls_down_migration()


# =============================================================================
# COMMON POLICY PATTERNS
# =============================================================================

def own_data_policy(table: str, user_column: str = "user_id") -> Policy:
    """
    Create a policy where users can only access their own data.
    
    Args:
        table: Table name
        user_column: Column containing user ID
    
    Returns:
        Policy for own data access
    
    Example:
        policy = own_data_policy("orders", "customer_id")
    """
    return Policy(
        table=table,
        operation=PolicyOperation.ALL,
        name=f"{table}_own_data",
        using=f"auth.uid() = {user_column}",
        check=f"auth.uid() = {user_column}",
        description=f"Users can only access their own {table}",
    )


def public_read_policy(table: str) -> Policy:
    """
    Create a policy for public read access.
    
    Args:
        table: Table name
    
    Returns:
        Policy for public read access
    """
    return Policy(
        table=table,
        operation=PolicyOperation.SELECT,
        name=f"{table}_public_read",
        using="true",
        description=f"Anyone can read {table}",
    )


def authenticated_only_policy(table: str, operation: PolicyOperation) -> Policy:
    """
    Create a policy that only allows authenticated users.
    
    Args:
        table: Table name
        operation: Which operation to restrict
    
    Returns:
        Policy for authenticated users only
    """
    return Policy(
        table=table,
        operation=operation,
        name=f"{table}_authenticated_{operation.value.lower()}",
        using="auth.role() = 'authenticated'",
        check="auth.role() = 'authenticated'" if operation != PolicyOperation.SELECT else None,
        description=f"Only authenticated users can {operation.value.lower()} {table}",
    )


def role_based_policy(
    table: str,
    operation: PolicyOperation,
    role: str,
    role_column: str = "role",
) -> Policy:
    """
    Create a policy based on user role in user_metadata.
    
    Args:
        table: Table name
        operation: Which operation to restrict
        role: Required role (e.g., "admin")
        role_column: Column in user_metadata containing role
    
    Returns:
        Role-based policy
    """
    return Policy(
        table=table,
        operation=operation,
        name=f"{table}_{role}_{operation.value.lower()}",
        using=f"auth.jwt() ->> 'role' = '{role}'",
        description=f"Only {role}s can {operation.value.lower()} {table}",
    )

