"""
Migration Executor.

Runs migrations (up/down) with transaction support.
Wraps Alembic under the hood but provides a simpler API.

Design: Safe by default, clear errors, easy to debug.
"""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Union, TYPE_CHECKING

from pynext.db.migrations.history import (
    MigrationHistory,
    compute_checksum,
    parse_version,
)
from pynext.db.migrations.operations import op

if TYPE_CHECKING:
    from pynext.db.adapters.base import Adapter


@dataclass
class MigrationResult:
    """Result of running migrations."""
    success: bool
    applied: List[str]  # List of applied versions
    errors: List[str]
    elapsed_ms: float


@dataclass
class MigrationInfo:
    """Information about a migration file."""
    version: str
    name: str
    path: Path
    has_up: bool
    has_down: bool
    is_declarative: bool


class MigrationExecutor:
    """
    Executes migration files.
    
    Handles:
    - Loading migration modules
    - Running up/down functions
    - Transaction management
    - History tracking
    
    Usage:
        executor = MigrationExecutor(adapter, Path("migrations"))
        
        # Apply all pending
        result = await executor.upgrade()
        
        # Apply to specific version
        result = await executor.upgrade(target="0001_20240101")
        
        # Rollback one
        result = await executor.downgrade()
        
        # Preview SQL
        sql = await executor.preview_sql("up")
    """
    
    def __init__(
        self,
        adapter: "Adapter",
        migrations_dir: Path,
        dialect: str = "sqlite",
    ):
        """
        Args:
            adapter: Database adapter
            migrations_dir: Directory containing migration files
            dialect: SQL dialect ("sqlite", "postgresql")
        """
        self.adapter = adapter
        self.migrations_dir = migrations_dir
        self.dialect = dialect
        self.history = MigrationHistory(adapter)
    
    async def upgrade(
        self,
        target: Optional[str] = None,
        dry_run: bool = False,
    ) -> MigrationResult:
        """
        Apply pending migrations.
        
        Args:
            target: Target version (None = apply all)
            dry_run: If True, show SQL without applying
            
        Returns:
            MigrationResult
        """
        start_time = datetime.now()
        applied = []
        errors = []
        
        # Get pending migrations
        pending = await self.history.get_pending(self.migrations_dir)
        
        if not pending:
            return MigrationResult(
                success=True,
                applied=[],
                errors=[],
                elapsed_ms=0,
            )
        
        # Filter to target if specified
        if target:
            filtered = []
            for mig in pending:
                filtered.append(mig)
                if mig["version"] == target:
                    break
            pending = filtered
        
        # Configure operations
        op.configure(self.adapter, self.dialect, dry_run=dry_run)
        
        # Apply each migration
        for mig in pending:
            version = mig["version"]
            path = mig["path"]
            
            try:
                await self._run_migration(path, "up")
                
                if not dry_run:
                    # Record in history
                    content = path.read_text()
                    checksum = compute_checksum(content)
                    await self.history.mark_applied(
                        version=version,
                        name=mig["name"],
                        checksum=checksum,
                    )
                
                applied.append(version)
                
            except Exception as e:
                errors.append(f"{version}: {str(e)}")
                break  # Stop on first error
        
        elapsed = (datetime.now() - start_time).total_seconds() * 1000
        
        return MigrationResult(
            success=len(errors) == 0,
            applied=applied,
            errors=errors,
            elapsed_ms=elapsed,
        )
    
    async def downgrade(
        self,
        target: Optional[str] = None,
        steps: int = 1,
        dry_run: bool = False,
    ) -> MigrationResult:
        """
        Rollback migrations.
        
        Args:
            target: Target version to rollback to (exclusive)
            steps: Number of migrations to rollback (ignored if target set)
            dry_run: If True, show SQL without applying
            
        Returns:
            MigrationResult
        """
        start_time = datetime.now()
        applied = []
        errors = []
        
        # Get applied migrations (in reverse order for rollback)
        history = await self.history.get_applied()
        
        if not history:
            return MigrationResult(
                success=True,
                applied=[],
                errors=["No migrations to rollback"],
                elapsed_ms=0,
            )
        
        # Determine which to rollback
        to_rollback = []
        
        if target:
            # Rollback until we reach target
            for record in reversed(history):
                if record.version == target:
                    break
                to_rollback.append(record)
        else:
            # Rollback N steps
            to_rollback = list(reversed(history))[:steps]
        
        if not to_rollback:
            return MigrationResult(
                success=True,
                applied=[],
                errors=[],
                elapsed_ms=0,
            )
        
        # Configure operations
        op.configure(self.adapter, self.dialect, dry_run=dry_run)
        
        # Rollback each migration
        for record in to_rollback:
            version = record.version
            
            # Find migration file
            pattern = f"{version}*.py"
            files = list(self.migrations_dir.glob(pattern))
            
            if not files:
                errors.append(f"{version}: Migration file not found")
                break
            
            path = files[0]
            
            try:
                await self._run_migration(path, "down")
                
                if not dry_run:
                    await self.history.mark_unapplied(version)
                
                applied.append(version)
                
            except Exception as e:
                errors.append(f"{version}: {str(e)}")
                break
        
        elapsed = (datetime.now() - start_time).total_seconds() * 1000
        
        return MigrationResult(
            success=len(errors) == 0,
            applied=applied,
            errors=errors,
            elapsed_ms=elapsed,
        )
    
    async def preview_sql(
        self,
        direction: str = "up",
        target: Optional[str] = None,
    ) -> List[str]:
        """
        Preview SQL that would be executed.
        
        Args:
            direction: "up" or "down"
            target: Target version
            
        Returns:
            List of SQL statements
        """
        # Configure for dry run
        op.configure(self.adapter, self.dialect, dry_run=True)
        
        if direction == "up":
            pending = await self.history.get_pending(self.migrations_dir)
            
            if target:
                pending = [m for m in pending if m["version"] <= target]
            
            for mig in pending:
                await self._run_migration(mig["path"], "up")
        else:
            history = await self.history.get_applied()
            to_rollback = list(reversed(history))[:1]  # Just last one
            
            for record in to_rollback:
                pattern = f"{record.version}*.py"
                files = list(self.migrations_dir.glob(pattern))
                if files:
                    await self._run_migration(files[0], "down")
        
        return op.sql_statements
    
    async def _run_migration(self, path: Path, direction: str) -> None:
        """
        Run a single migration file.
        
        Args:
            path: Path to migration file
            direction: "up" or "down"
        """
        # Load module
        module = self._load_module(path)
        
        # Check for declarative or Python style
        if hasattr(module, "migration"):
            # Declarative style
            migration_obj = module.migration
            
            if direction == "up":
                await self._run_declarative_up(migration_obj)
            else:
                await self._run_declarative_down(migration_obj)
        else:
            # Look for decorated functions
            up_fn = None
            down_fn = None
            
            for name in dir(module):
                obj = getattr(module, name)
                if hasattr(obj, "_migration_up"):
                    up_fn = obj
                elif hasattr(obj, "_migration_down"):
                    down_fn = obj
            
            if direction == "up":
                if up_fn:
                    await up_fn()
                else:
                    raise ValueError(f"No upgrade function found in {path.name}")
            else:
                if down_fn:
                    await down_fn()
                else:
                    raise ValueError(f"No downgrade function found in {path.name}")
    
    async def _run_declarative_up(self, migration) -> None:
        """Run declarative migration (upgrade)."""
        # Execute SQL statements from migration.sql() calls
        if hasattr(migration, "_up_statements"):
            for sql in migration._up_statements:
                await op.execute(sql)
    
    async def _run_declarative_down(self, migration) -> None:
        """Run declarative migration (downgrade)."""
        if hasattr(migration, "_down_statements"):
            for sql in reversed(migration._down_statements):
                await op.execute(sql)
    
    def _load_module(self, path: Path):
        """Load a Python module from path."""
        module_name = f"pynext_migration_{path.stem}"
        
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load migration: {path}")
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        return module
    
    def get_migration_info(self, path: Path) -> MigrationInfo:
        """
        Get information about a migration file.
        
        Args:
            path: Path to migration file
            
        Returns:
            MigrationInfo
        """
        version = parse_version(path.name)
        name_part = path.stem[len(version) + 1:] if version else path.stem
        name = name_part.replace("_", " ").title()
        
        # Check content for up/down functions
        content = path.read_text()
        has_up = "@migration.up" in content or "def upgrade" in content
        has_down = "@migration.down" in content or "def downgrade" in content
        is_declarative = "migration.sql(" in content or "migration.create_table(" in content
        
        return MigrationInfo(
            version=version or "unknown",
            name=name,
            path=path,
            has_up=has_up,
            has_down=has_down,
            is_declarative=is_declarative,
        )
    
    def list_migrations(self) -> List[MigrationInfo]:
        """List all migration files."""
        migrations = []
        
        for path in sorted(self.migrations_dir.glob("*.py")):
            if path.name.startswith("_"):
                continue
            
            migrations.append(self.get_migration_info(path))
        
        return migrations


class Migration:
    """
    Migration DSL for declarative migrations.
    
    Usage in migration files:
        from pynext.db.migrations import migration
        
        migration.create_table("users", {...})
        migration.add_column("users", "email", "varchar(255)")
        migration.sql("CREATE INDEX ...")
    """
    
    def __init__(self):
        self._up_statements: List[str] = []
        self._down_statements: List[str] = []
        self._up_fn = None
        self._down_fn = None
    
    # Decorators for Python-style migrations
    
    def up(self, fn):
        """Decorator for upgrade function."""
        fn._migration_up = True
        self._up_fn = fn
        return fn
    
    def down(self, fn):
        """Decorator for downgrade function."""
        fn._migration_down = True
        self._down_fn = fn
        return fn
    
    # Declarative methods
    
    def sql(self, statement: str) -> str:
        """Add a raw SQL statement."""
        self._up_statements.append(statement)
        return statement
    
    def create_table(
        self,
        name: str,
        columns: dict,
        dialect: str = "postgresql",
    ) -> str:
        """Create a table."""
        if not columns:
            sql = f"CREATE TABLE IF NOT EXISTS {name} ()"
        else:
            col_defs = ",\n  ".join(f"{col} {definition}" for col, definition in columns.items() if not col.startswith("__"))
            sql = f"CREATE TABLE IF NOT EXISTS {name} (\n  {col_defs}\n)"
            
            # Handle special directives
            if "__primary_key__" in columns:
                pk_cols = columns["__primary_key__"]
                sql = sql.rstrip(")")
                sql += f",\n  PRIMARY KEY {pk_cols}\n)"
        
        self._up_statements.append(sql)
        self._down_statements.append(f"DROP TABLE IF EXISTS {name}")
        return sql
    
    def drop_table(
        self,
        name: str,
        cascade: bool = False,
        if_exists: bool = False,
    ) -> str:
        """Drop a table."""
        parts = ["DROP TABLE"]
        if if_exists:
            parts.append("IF EXISTS")
        parts.append(name)
        if cascade:
            parts.append("CASCADE")
        sql = " ".join(parts)
        self._up_statements.append(sql)
        return sql
    
    def add_column(
        self,
        table: str,
        column: str,
        type_def: str,
        nullable: bool = True,
        default: Optional[str] = None,
    ) -> str:
        """Add a column."""
        parts = [f"ALTER TABLE {table} ADD COLUMN {column} {type_def}"]
        if not nullable:
            parts.append("NOT NULL")
        if default is not None:
            parts.append(f"DEFAULT {default}")
        
        sql = " ".join(parts)
        self._up_statements.append(sql)
        self._down_statements.append(f"ALTER TABLE {table} DROP COLUMN {column}")
        return sql
    
    def add_columns(self, table: str, columns: dict) -> str:
        """Add multiple columns at once."""
        statements = []
        for column, type_def in columns.items():
            stmt = f"ALTER TABLE {table} ADD COLUMN {column} {type_def}"
            statements.append(stmt)
            self._up_statements.append(stmt)
            self._down_statements.append(f"ALTER TABLE {table} DROP COLUMN {column}")
        return "\n".join(statements)
    
    def drop_column(self, table: str, column: str) -> str:
        """Drop a column."""
        sql = f"ALTER TABLE {table} DROP COLUMN {column}"
        self._up_statements.append(sql)
        return sql
    
    def rename_column(self, table: str, old_name: str, new_name: str) -> str:
        """Rename a column."""
        sql = f"ALTER TABLE {table} RENAME COLUMN {old_name} TO {new_name}"
        self._up_statements.append(sql)
        self._down_statements.append(
            f"ALTER TABLE {table} RENAME COLUMN {new_name} TO {old_name}"
        )
        return sql
    
    def alter_column(
        self,
        table: str,
        column: str,
        type_def: Optional[str] = None,
        nullable: Optional[bool] = None,
        default: Optional[str] = None,
    ) -> str:
        """Alter a column type or constraints."""
        parts = [f"ALTER TABLE {table} ALTER COLUMN {column}"]
        
        if type_def:
            parts.append(f"TYPE {type_def}")
        if nullable is False:
            parts.append("SET NOT NULL")
        elif nullable is True:
            parts.append("DROP NOT NULL")
        if default is not None:
            parts.append(f"SET DEFAULT {default}")
        
        sql = " ".join(parts)
        self._up_statements.append(sql)
        return sql
    
    def create_index(
        self,
        table: str,
        columns: List[str],
        unique: bool = False,
        name: Optional[str] = None,
        where: Optional[str] = None,
    ) -> str:
        """Create an index."""
        if name is None:
            prefix = "uix" if unique else "ix"
            name = f"{prefix}_{table}_{'_'.join(columns)}"
        
        unique_str = "UNIQUE " if unique else ""
        cols = ", ".join(columns)
        
        sql = f"CREATE {unique_str}INDEX {name} ON {table} ({cols})"
        if where:
            sql += f" WHERE {where}"
        
        self._up_statements.append(sql)
        self._down_statements.append(f"DROP INDEX {name}")
        return sql
    
    def drop_index(self, name: str) -> str:
        """Drop an index."""
        sql = f"DROP INDEX {name}"
        self._up_statements.append(sql)
        return sql
    
    def add_constraint(
        self,
        table: str,
        name: str,
        definition: str,
    ) -> str:
        """Add a constraint."""
        sql = f"ALTER TABLE {table} ADD CONSTRAINT {name} {definition}"
        self._up_statements.append(sql)
        self._down_statements.append(f"ALTER TABLE {table} DROP CONSTRAINT {name}")
        return sql
    
    def drop_constraint(self, table: str, name: str) -> str:
        """Drop a constraint."""
        sql = f"ALTER TABLE {table} DROP CONSTRAINT {name}"
        self._up_statements.append(sql)
        return sql
    
    # Reversible methods (return tuple of forward, reverse SQL)
    
    def create_table_reversible(self, name: str, columns: dict) -> Tuple[str, str]:
        """Create a table (reversible)."""
        forward = self.create_table(name, columns)
        reverse = f"DROP TABLE IF EXISTS {name}"
        return forward, reverse
    
    def add_column_reversible(
        self,
        table: str,
        column: str,
        type_def: str,
    ) -> Tuple[str, str]:
        """Add a column (reversible)."""
        forward = self.add_column(table, column, type_def)
        reverse = f"ALTER TABLE {table} DROP COLUMN {column}"
        return forward, reverse
    
    def create_index_reversible(
        self,
        table: str,
        columns: List[str],
        unique: bool = False,
        name: Optional[str] = None,
    ) -> Tuple[str, str]:
        """Create an index (reversible)."""
        forward = self.create_index(table, columns, unique=unique, name=name)
        
        if name is None:
            prefix = "uix" if unique else "ix"
            name = f"{prefix}_{table}_{'_'.join(columns)}"
        
        reverse = f"DROP INDEX {name}"
        return forward, reverse
    
    def batch(self, statements: List[str]) -> List[str]:
        """Batch multiple statements."""
        for stmt in statements:
            self._up_statements.append(stmt)
        return statements


# Global migration instance for declarative style
migration = Migration()


__all__ = [
    "MigrationExecutor",
    "MigrationResult",
    "MigrationInfo",
    "Migration",
    "migration",
]

