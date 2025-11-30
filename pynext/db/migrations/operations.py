"""
Migration Operations (op.* functions).

Provides the op.* API for Python migrations.
Used in @migration.up and @migration.down decorated functions.

Design: Stupid simple - just use op.add_column(), op.drop_table(), etc.
"""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from pynext.db.adapters.base import Adapter


class Operations:
    """
    Migration operations API.
    
    Provides methods for schema changes and data migration.
    
    Usage in Python migrations:
        from pynext.db.migrations import op
        
        @migration.up
        async def upgrade():
            # Schema changes
            await op.create_table("users", {
                "id": "serial primary key",
                "name": "varchar(255)",
            })
            await op.add_column("users", "email", "varchar(255)")
            
            # Data migration
            async for row in op.fetch("SELECT * FROM users"):
                await op.execute(
                    "UPDATE users SET email = $1 WHERE id = $2",
                    f"{row['name']}@example.com", row['id']
                )
    """
    
    def __init__(self, adapter: Optional["Adapter"] = None, dialect: str = "sqlite"):
        """
        Args:
            adapter: Database adapter (set during migration execution)
            dialect: SQL dialect ("sqlite", "postgresql")
        """
        self._adapter: Optional["Adapter"] = adapter
        self._dialect = dialect
        self._dry_run = False
        self._collected_sql: List[str] = []
    
    def configure(
        self,
        adapter: "Adapter",
        dialect: str = "sqlite",
        dry_run: bool = False,
    ) -> None:
        """
        Configure the operations for execution.
        
        Called by the migration executor before running migrations.
        """
        self._adapter = adapter
        self._dialect = dialect
        self._dry_run = dry_run
        self._collected_sql = []
    
    @property
    def sql_statements(self) -> List[str]:
        """Get collected SQL statements (for dry run mode)."""
        return self._collected_sql
    
    # =========================================================================
    # Table Operations
    # =========================================================================
    
    async def create_table(
        self,
        name: str,
        columns: Dict[str, str],
        if_not_exists: bool = True,
    ) -> None:
        """
        Create a new table.
        
        Args:
            name: Table name
            columns: Dict of column_name -> column_definition
            if_not_exists: Add IF NOT EXISTS clause
            
        Example:
            await op.create_table("users", {
                "id": "serial primary key",
                "name": "varchar(255) not null",
                "email": "varchar(255) unique",
                "created_at": "timestamp default now()",
            })
        """
        col_defs = ",\n  ".join(f"{col} {definition}" for col, definition in columns.items())
        exists = "IF NOT EXISTS " if if_not_exists else ""
        sql = f"CREATE TABLE {exists}{name} (\n  {col_defs}\n)"
        
        await self._execute(sql)
    
    async def drop_table(
        self,
        name: str,
        if_exists: bool = True,
        cascade: bool = False,
    ) -> None:
        """
        Drop a table.
        
        Args:
            name: Table name
            if_exists: Add IF EXISTS clause
            cascade: Cascade to dependent objects (PostgreSQL)
        """
        exists = "IF EXISTS " if if_exists else ""
        casc = " CASCADE" if cascade and self._dialect == "postgresql" else ""
        sql = f"DROP TABLE {exists}{name}{casc}"
        
        await self._execute(sql)
    
    async def rename_table(self, old_name: str, new_name: str) -> None:
        """
        Rename a table.
        
        Args:
            old_name: Current table name
            new_name: New table name
        """
        sql = f"ALTER TABLE {old_name} RENAME TO {new_name}"
        await self._execute(sql)
    
    # =========================================================================
    # Column Operations
    # =========================================================================
    
    async def add_column(
        self,
        table: str,
        column: str,
        type_def: str,
        nullable: bool = True,
        default: Optional[Any] = None,
    ) -> None:
        """
        Add a column to a table.
        
        Args:
            table: Table name
            column: Column name
            type_def: SQL type definition (e.g., "varchar(255)")
            nullable: Allow NULL values
            default: Default value
            
        Example:
            await op.add_column("users", "email", "varchar(255)", nullable=False)
            await op.add_column("users", "role", "varchar(50)", default="user")
        """
        parts = [f"ALTER TABLE {table} ADD COLUMN {column} {type_def}"]
        
        if not nullable:
            parts.append("NOT NULL")
        
        if default is not None:
            if isinstance(default, str):
                parts.append(f"DEFAULT '{default}'")
            elif isinstance(default, bool):
                parts.append(f"DEFAULT {1 if default else 0}")
            else:
                parts.append(f"DEFAULT {default}")
        
        sql = " ".join(parts)
        await self._execute(sql)
    
    async def drop_column(self, table: str, column: str) -> None:
        """
        Drop a column from a table.
        
        Args:
            table: Table name
            column: Column name
            
        Note: SQLite doesn't support DROP COLUMN directly.
              For SQLite, the table will need to be recreated.
        """
        if self._dialect == "sqlite":
            # SQLite requires table recreation
            # For now, just record the SQL
            sql = f"-- SQLite: DROP COLUMN requires table recreation\n"
            sql += f"-- ALTER TABLE {table} DROP COLUMN {column}"
        else:
            sql = f"ALTER TABLE {table} DROP COLUMN {column}"
        
        await self._execute(sql)
    
    async def rename_column(self, table: str, old_name: str, new_name: str) -> None:
        """
        Rename a column.
        
        Args:
            table: Table name
            old_name: Current column name
            new_name: New column name
        """
        sql = f"ALTER TABLE {table} RENAME COLUMN {old_name} TO {new_name}"
        await self._execute(sql)
    
    async def alter_column(
        self,
        table: str,
        column: str,
        type_def: Optional[str] = None,
        nullable: Optional[bool] = None,
        default: Optional[Any] = None,
        drop_default: bool = False,
    ) -> None:
        """
        Alter a column's type or constraints.
        
        Args:
            table: Table name
            column: Column name
            type_def: New SQL type (optional)
            nullable: New nullable setting (optional)
            default: New default value (optional)
            drop_default: Remove default value
            
        Example:
            await op.alter_column("users", "email", nullable=False)
            await op.alter_column("users", "bio", type_def="text")
        """
        if self._dialect != "postgresql":
            sql = f"-- SQLite: ALTER COLUMN requires table recreation for {table}.{column}"
            await self._execute(sql)
            return
        
        if type_def:
            sql = f"ALTER TABLE {table} ALTER COLUMN {column} TYPE {type_def}"
            await self._execute(sql)
        
        if nullable is not None:
            if nullable:
                sql = f"ALTER TABLE {table} ALTER COLUMN {column} DROP NOT NULL"
            else:
                sql = f"ALTER TABLE {table} ALTER COLUMN {column} SET NOT NULL"
            await self._execute(sql)
        
        if drop_default:
            sql = f"ALTER TABLE {table} ALTER COLUMN {column} DROP DEFAULT"
            await self._execute(sql)
        elif default is not None:
            if isinstance(default, str):
                sql = f"ALTER TABLE {table} ALTER COLUMN {column} SET DEFAULT '{default}'"
            else:
                sql = f"ALTER TABLE {table} ALTER COLUMN {column} SET DEFAULT {default}"
            await self._execute(sql)
    
    # =========================================================================
    # Index Operations
    # =========================================================================
    
    async def create_index(
        self,
        name: str,
        table: str,
        columns: List[str],
        unique: bool = False,
        if_not_exists: bool = True,
    ) -> None:
        """
        Create an index.
        
        Args:
            name: Index name
            table: Table name
            columns: List of column names
            unique: Create unique index
            if_not_exists: Skip if index exists
            
        Example:
            await op.create_index("ix_users_email", "users", ["email"], unique=True)
        """
        unique_str = "UNIQUE " if unique else ""
        exists = "IF NOT EXISTS " if if_not_exists else ""
        cols = ", ".join(columns)
        sql = f"CREATE {unique_str}INDEX {exists}{name} ON {table} ({cols})"
        
        await self._execute(sql)
    
    async def drop_index(self, name: str, if_exists: bool = True) -> None:
        """
        Drop an index.
        
        Args:
            name: Index name
            if_exists: Skip if index doesn't exist
        """
        exists = "IF EXISTS " if if_exists else ""
        sql = f"DROP INDEX {exists}{name}"
        
        await self._execute(sql)
    
    # =========================================================================
    # Constraint Operations
    # =========================================================================
    
    async def add_foreign_key(
        self,
        name: str,
        table: str,
        column: str,
        ref_table: str,
        ref_column: str = "id",
        on_delete: str = "CASCADE",
    ) -> None:
        """
        Add a foreign key constraint.
        
        Args:
            name: Constraint name
            table: Source table
            column: Source column
            ref_table: Referenced table
            ref_column: Referenced column (default: "id")
            on_delete: ON DELETE action
        """
        if self._dialect == "sqlite":
            sql = f"-- SQLite: Foreign keys require table recreation for {table}"
        else:
            sql = (
                f"ALTER TABLE {table} ADD CONSTRAINT {name} "
                f"FOREIGN KEY ({column}) REFERENCES {ref_table}({ref_column}) "
                f"ON DELETE {on_delete}"
            )
        
        await self._execute(sql)
    
    async def drop_constraint(self, table: str, name: str) -> None:
        """
        Drop a constraint.
        
        Args:
            table: Table name
            name: Constraint name
        """
        if self._dialect == "sqlite":
            sql = f"-- SQLite: Constraint removal requires table recreation for {table}"
        else:
            sql = f"ALTER TABLE {table} DROP CONSTRAINT {name}"
        
        await self._execute(sql)
    
    # =========================================================================
    # Data Operations
    # =========================================================================
    
    async def execute(self, sql: str, *args: Any) -> Any:
        """
        Execute raw SQL.
        
        Args:
            sql: SQL statement (use $1, $2 for parameters)
            *args: Parameter values
            
        Example:
            await op.execute("UPDATE users SET role = $1 WHERE id = $2", "admin", 1)
        """
        if self._dry_run:
            formatted = self._format_sql(sql, args)
            self._collected_sql.append(formatted)
            return None
        
        if not self._adapter:
            raise RuntimeError("No adapter configured. Call op.configure() first.")
        
        return await self._adapter.execute(sql, args if args else None)
    
    async def fetch(
        self,
        sql: str,
        *args: Any,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Fetch rows from a query.
        
        Args:
            sql: SELECT statement
            *args: Parameter values
            
        Yields:
            Row dicts
            
        Example:
            async for row in op.fetch("SELECT * FROM users WHERE role = $1", "admin"):
                print(row["name"])
        """
        if self._dry_run:
            formatted = self._format_sql(sql, args)
            self._collected_sql.append(f"-- FETCH: {formatted}")
            return
        
        if not self._adapter:
            raise RuntimeError("No adapter configured. Call op.configure() first.")
        
        rows = await self._adapter.fetch_all(sql, args if args else None)
        for row in rows:
            yield row
    
    async def fetch_one(
        self,
        sql: str,
        *args: Any,
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch a single row.
        
        Args:
            sql: SELECT statement
            *args: Parameter values
            
        Returns:
            Row dict or None
        """
        if self._dry_run:
            formatted = self._format_sql(sql, args)
            self._collected_sql.append(f"-- FETCH ONE: {formatted}")
            return None
        
        if not self._adapter:
            raise RuntimeError("No adapter configured. Call op.configure() first.")
        
        return await self._adapter.fetch_one(sql, args if args else None)
    
    async def fetch_val(self, sql: str, *args: Any) -> Any:
        """
        Fetch a single value.
        
        Args:
            sql: SELECT statement returning single value
            *args: Parameter values
            
        Returns:
            The scalar value
        """
        row = await self.fetch_one(sql, *args)
        if row:
            return list(row.values())[0]
        return None
    
    async def bulk_insert(
        self,
        table: str,
        rows: List[Dict[str, Any]],
    ) -> int:
        """
        Insert multiple rows efficiently.
        
        Args:
            table: Table name
            rows: List of row dicts
            
        Returns:
            Number of rows inserted
        """
        if not rows:
            return 0
        
        columns = list(rows[0].keys())
        placeholders = ", ".join(f"${i+1}" for i in range(len(columns)))
        cols_str = ", ".join(columns)
        sql = f"INSERT INTO {table} ({cols_str}) VALUES ({placeholders})"
        
        count = 0
        for row in rows:
            values = [row.get(col) for col in columns]
            await self.execute(sql, *values)
            count += 1
        
        return count
    
    # =========================================================================
    # Internal
    # =========================================================================
    
    async def _execute(self, sql: str) -> None:
        """Execute a DDL statement."""
        if self._dry_run:
            self._collected_sql.append(sql)
            return
        
        if not self._adapter:
            raise RuntimeError("No adapter configured. Call op.configure() first.")
        
        await self._adapter.execute(sql, None)
    
    def _format_sql(self, sql: str, args: Tuple[Any, ...]) -> str:
        """Format SQL with parameters for display."""
        result = sql
        for i, arg in enumerate(args):
            placeholder = f"${i+1}"
            if isinstance(arg, str):
                result = result.replace(placeholder, f"'{arg}'", 1)
            else:
                result = result.replace(placeholder, str(arg), 1)
        return result


# Global operations instance
op = Operations()


__all__ = [
    "Operations",
    "op",
]

