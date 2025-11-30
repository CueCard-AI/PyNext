"""
Migration Change Types.

Represents all possible schema changes detected between models and database.
Each change type knows how to generate its own SQL (up and down).

Design: Stupid simple - each change is self-contained with its SQL generation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class ChangeType(Enum):
    """Types of schema changes."""
    CREATE_TABLE = "create_table"
    DROP_TABLE = "drop_table"
    RENAME_TABLE = "rename_table"
    ADD_COLUMN = "add_column"
    DROP_COLUMN = "drop_column"
    RENAME_COLUMN = "rename_column"
    ALTER_COLUMN = "alter_column"
    ADD_INDEX = "add_index"
    DROP_INDEX = "drop_index"
    ADD_CONSTRAINT = "add_constraint"
    DROP_CONSTRAINT = "drop_constraint"
    RAW_SQL = "raw_sql"


@dataclass
class ColumnDef:
    """Column definition."""
    name: str
    sql_type: str
    nullable: bool = True
    default: Optional[Any] = None
    primary_key: bool = False
    auto_increment: bool = False
    unique: bool = False
    foreign_key: Optional[str] = None  # Target table
    references: Optional[str] = None  # E.g., "users(id)"
    check: Optional[str] = None  # E.g., "age >= 0"
    
    def to_sql(self, dialect: str = "sqlite") -> str:
        """Generate SQL column definition."""
        sql_type = self.sql_type
        
        # Handle type conversions between dialects
        if dialect == "sqlite":
            # SQLite: SERIAL -> INTEGER
            if sql_type.upper() == "SERIAL":
                sql_type = "INTEGER"
        elif dialect == "postgresql":
            # PostgreSQL: auto-increment uses SERIAL
            if self.auto_increment and sql_type.upper() in ("INTEGER", "INT"):
                sql_type = "SERIAL"
        
        parts = [self.name, sql_type]
        
        if self.primary_key:
            parts.append("PRIMARY KEY")
            if self.auto_increment and dialect == "sqlite":
                parts.append("AUTOINCREMENT")
        
        if not self.nullable and not self.primary_key:
            parts.append("NOT NULL")
        
        if self.unique and not self.primary_key:
            parts.append("UNIQUE")
        
        if self.default is not None:
            if isinstance(self.default, str):
                parts.append(f"DEFAULT '{self.default}'")
            elif isinstance(self.default, bool):
                parts.append(f"DEFAULT {1 if self.default else 0}")
            else:
                parts.append(f"DEFAULT {self.default}")
        
        if self.references:
            parts.append(f"REFERENCES {self.references}")
        
        if self.check:
            parts.append(f"CHECK ({self.check})")
        
        return " ".join(parts)


@dataclass
class Change(ABC):
    """Base class for all schema changes."""
    
    @property
    @abstractmethod
    def change_type(self) -> ChangeType:
        """The type of change."""
        pass
    
    @abstractmethod
    def up_sql(self, dialect: str = "sqlite") -> List[str]:
        """SQL statements to apply this change."""
        pass
    
    @abstractmethod
    def down_sql(self, dialect: str = "sqlite") -> List[str]:
        """SQL statements to reverse this change."""
        pass
    
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of the change."""
        pass
    
    def is_destructive(self) -> bool:
        """Whether this change could lose data."""
        return False
    
    def to_sql(self, dialect: str = "sqlite") -> str:
        """Get the primary SQL statement (convenience method)."""
        stmts = self.up_sql(dialect)
        return "\n".join(stmts) if stmts else ""


@dataclass
class CreateTable(Change):
    """Create a new table."""
    table: str
    columns: List[ColumnDef]
    
    @property
    def change_type(self) -> ChangeType:
        return ChangeType.CREATE_TABLE
    
    def up_sql(self, dialect: str = "sqlite") -> List[str]:
        col_defs = ",\n  ".join(c.to_sql(dialect) for c in self.columns)
        return [f"CREATE TABLE {self.table} (\n  {col_defs}\n)"]
    
    def down_sql(self, dialect: str = "sqlite") -> List[str]:
        return [f"DROP TABLE {self.table}"]
    
    def description(self) -> str:
        return f"Create table '{self.table}' with {len(self.columns)} columns"


@dataclass
class DropTable(Change):
    """Drop an existing table."""
    table: str
    columns: List[ColumnDef] = field(default_factory=list)  # For down migration
    
    @property
    def change_type(self) -> ChangeType:
        return ChangeType.DROP_TABLE
    
    def up_sql(self, dialect: str = "sqlite") -> List[str]:
        return [f"DROP TABLE {self.table}"]
    
    def down_sql(self, dialect: str = "sqlite") -> List[str]:
        if not self.columns:
            return [f"-- Cannot recreate table '{self.table}' (no column info)"]
        col_defs = ",\n  ".join(c.to_sql(dialect) for c in self.columns)
        return [f"CREATE TABLE {self.table} (\n  {col_defs}\n)"]
    
    def description(self) -> str:
        return f"Drop table '{self.table}'"
    
    def is_destructive(self) -> bool:
        return True


@dataclass
class RenameTable(Change):
    """Rename a table."""
    old_name: str
    new_name: str
    
    @property
    def change_type(self) -> ChangeType:
        return ChangeType.RENAME_TABLE
    
    def up_sql(self, dialect: str = "sqlite") -> List[str]:
        return [f"ALTER TABLE {self.old_name} RENAME TO {self.new_name}"]
    
    def down_sql(self, dialect: str = "sqlite") -> List[str]:
        return [f"ALTER TABLE {self.new_name} RENAME TO {self.old_name}"]
    
    def description(self) -> str:
        return f"Rename table '{self.old_name}' to '{self.new_name}'"


@dataclass
class AddColumn(Change):
    """Add a column to a table."""
    table: str
    column: ColumnDef
    if_not_exists: bool = False
    
    @property
    def change_type(self) -> ChangeType:
        return ChangeType.ADD_COLUMN
    
    def up_sql(self, dialect: str = "sqlite") -> List[str]:
        if_clause = "IF NOT EXISTS " if self.if_not_exists and dialect == "postgresql" else ""
        return [f"ALTER TABLE {self.table} ADD COLUMN {if_clause}{self.column.to_sql(dialect)}"]
    
    def down_sql(self, dialect: str = "sqlite") -> List[str]:
        if dialect == "sqlite":
            # SQLite doesn't support DROP COLUMN directly
            return [f"-- SQLite: DROP COLUMN requires table recreation for '{self.table}.{self.column.name}'"]
        return [f"ALTER TABLE {self.table} DROP COLUMN {self.column.name}"]
    
    def description(self) -> str:
        return f"Add column '{self.column.name}' to '{self.table}'"


@dataclass
class DropColumn(Change):
    """Drop a column from a table."""
    table: str
    column: ColumnDef  # Full column info for down migration
    
    @property
    def change_type(self) -> ChangeType:
        return ChangeType.DROP_COLUMN
    
    def up_sql(self, dialect: str = "sqlite") -> List[str]:
        if dialect == "sqlite":
            return [f"-- SQLite: DROP COLUMN requires table recreation for '{self.table}.{self.column.name}'"]
        return [f"ALTER TABLE {self.table} DROP COLUMN {self.column.name}"]
    
    def down_sql(self, dialect: str = "sqlite") -> List[str]:
        return [f"ALTER TABLE {self.table} ADD COLUMN {self.column.to_sql(dialect)}"]
    
    def description(self) -> str:
        return f"Drop column '{self.column.name}' from '{self.table}'"
    
    def is_destructive(self) -> bool:
        return True


@dataclass
class RenameColumn(Change):
    """Rename a column."""
    table: str
    old_name: str
    new_name: str
    
    @property
    def change_type(self) -> ChangeType:
        return ChangeType.RENAME_COLUMN
    
    def up_sql(self, dialect: str = "sqlite") -> List[str]:
        if dialect == "postgresql":
            return [f"ALTER TABLE {self.table} RENAME COLUMN {self.old_name} TO {self.new_name}"]
        else:
            return [f"ALTER TABLE {self.table} RENAME COLUMN {self.old_name} TO {self.new_name}"]
    
    def down_sql(self, dialect: str = "sqlite") -> List[str]:
        if dialect == "postgresql":
            return [f"ALTER TABLE {self.table} RENAME COLUMN {self.new_name} TO {self.old_name}"]
        else:
            return [f"ALTER TABLE {self.table} RENAME COLUMN {self.new_name} TO {self.old_name}"]
    
    def description(self) -> str:
        return f"Rename column '{self.old_name}' to '{self.new_name}' in '{self.table}'"


@dataclass
class AlterColumn(Change):
    """Alter a column's type or constraints."""
    table: str
    column_name: str
    old_type: str
    new_type: str
    old_nullable: bool = True
    new_nullable: bool = True
    old_default: Optional[Any] = None
    new_default: Optional[Any] = None
    
    @property
    def change_type(self) -> ChangeType:
        return ChangeType.ALTER_COLUMN
    
    def up_sql(self, dialect: str = "sqlite") -> List[str]:
        stmts = []
        
        if dialect == "postgresql":
            if self.old_type != self.new_type:
                stmts.append(
                    f"ALTER TABLE {self.table} "
                    f"ALTER COLUMN {self.column_name} TYPE {self.new_type}"
                )
            
            if self.old_nullable != self.new_nullable:
                if self.new_nullable:
                    stmts.append(
                        f"ALTER TABLE {self.table} "
                        f"ALTER COLUMN {self.column_name} DROP NOT NULL"
                    )
                else:
                    stmts.append(
                        f"ALTER TABLE {self.table} "
                        f"ALTER COLUMN {self.column_name} SET NOT NULL"
                    )
            
            if self.old_default != self.new_default:
                if self.new_default is not None:
                    stmts.append(
                        f"ALTER TABLE {self.table} "
                        f"ALTER COLUMN {self.column_name} SET DEFAULT {self.new_default!r}"
                    )
                else:
                    stmts.append(
                        f"ALTER TABLE {self.table} "
                        f"ALTER COLUMN {self.column_name} DROP DEFAULT"
                    )
        else:
            # SQLite doesn't support ALTER COLUMN
            stmts.append(
                f"-- SQLite: ALTER COLUMN requires table recreation for "
                f"'{self.table}.{self.column_name}'"
            )
        
        return stmts if stmts else ["-- No changes needed"]
    
    def down_sql(self, dialect: str = "sqlite") -> List[str]:
        # Reverse: new -> old
        stmts = []
        
        if dialect == "postgresql":
            if self.old_type != self.new_type:
                stmts.append(
                    f"ALTER TABLE {self.table} "
                    f"ALTER COLUMN {self.column_name} TYPE {self.old_type}"
                )
            
            if self.old_nullable != self.new_nullable:
                if self.old_nullable:
                    stmts.append(
                        f"ALTER TABLE {self.table} "
                        f"ALTER COLUMN {self.column_name} DROP NOT NULL"
                    )
                else:
                    stmts.append(
                        f"ALTER TABLE {self.table} "
                        f"ALTER COLUMN {self.column_name} SET NOT NULL"
                    )
            
            if self.old_default != self.new_default:
                if self.old_default is not None:
                    stmts.append(
                        f"ALTER TABLE {self.table} "
                        f"ALTER COLUMN {self.column_name} SET DEFAULT {self.old_default!r}"
                    )
                else:
                    stmts.append(
                        f"ALTER TABLE {self.table} "
                        f"ALTER COLUMN {self.column_name} DROP DEFAULT"
                    )
        else:
            stmts.append(
                f"-- SQLite: ALTER COLUMN requires table recreation for "
                f"'{self.table}.{self.column_name}'"
            )
        
        return stmts if stmts else ["-- No changes needed"]
    
    def description(self) -> str:
        changes = []
        if self.old_type != self.new_type:
            changes.append(f"type {self.old_type} → {self.new_type}")
        if self.old_nullable != self.new_nullable:
            changes.append(f"nullable {self.old_nullable} → {self.new_nullable}")
        if self.old_default != self.new_default:
            changes.append(f"default {self.old_default} → {self.new_default}")
        
        return f"Alter '{self.table}.{self.column_name}': {', '.join(changes)}"
    
    def is_destructive(self) -> bool:
        # Narrowing a type could lose data
        return True


@dataclass
class AddIndex(Change):
    """Add an index."""
    table: str
    columns: List[str]
    unique: bool = False
    name: Optional[str] = None
    concurrently: bool = False
    where: Optional[str] = None
    if_not_exists: bool = False
    
    @property
    def change_type(self) -> ChangeType:
        return ChangeType.ADD_INDEX
    
    @property
    def index_name(self) -> str:
        if self.name:
            return self.name
        prefix = "uix" if self.unique else "ix"
        return f"{prefix}_{self.table}_{'_'.join(self.columns)}"
    
    def up_sql(self, dialect: str = "sqlite") -> List[str]:
        unique = "UNIQUE " if self.unique else ""
        concurrent = "CONCURRENTLY " if self.concurrently and dialect == "postgresql" else ""
        cols = ", ".join(self.columns)
        
        sql = f"CREATE {unique}{concurrent}INDEX {self.index_name} ON {self.table} ({cols})"
        
        if self.where and dialect == "postgresql":
            sql += f" WHERE {self.where}"
        
        return [sql]
    
    def down_sql(self, dialect: str = "sqlite") -> List[str]:
        return [f"DROP INDEX {self.index_name}"]
    
    def description(self) -> str:
        unique = "unique " if self.unique else ""
        return f"Create {unique}index '{self.index_name}' on '{self.table}'"


@dataclass
class DropIndex(Change):
    """Drop an index."""
    name: str
    table: Optional[str] = None  # Optional - some DBs don't need it
    columns: List[str] = field(default_factory=list)  # For down migration
    unique: bool = False
    
    @property
    def change_type(self) -> ChangeType:
        return ChangeType.DROP_INDEX
    
    def up_sql(self, dialect: str = "sqlite") -> List[str]:
        return [f"DROP INDEX {self.name}"]
    
    def down_sql(self, dialect: str = "sqlite") -> List[str]:
        if not self.columns or not self.table:
            return [f"-- Cannot recreate index '{self.name}' (no column info)"]
        unique = "UNIQUE " if self.unique else ""
        cols = ", ".join(self.columns)
        return [f"CREATE {unique}INDEX {self.name} ON {self.table} ({cols})"]
    
    def description(self) -> str:
        if self.table:
            return f"Drop index '{self.name}' from '{self.table}'"
        return f"Drop index '{self.name}'"


@dataclass
class AddConstraint(Change):
    """Add a constraint (foreign key, check, etc.)."""
    table: str
    name: str
    constraint_sql: str
    
    @property
    def change_type(self) -> ChangeType:
        return ChangeType.ADD_CONSTRAINT
    
    def up_sql(self, dialect: str = "sqlite") -> List[str]:
        if dialect == "sqlite":
            return [f"-- SQLite: Constraints require table recreation for '{self.table}'"]
        return [f"ALTER TABLE {self.table} ADD CONSTRAINT {self.name} {self.constraint_sql}"]
    
    def down_sql(self, dialect: str = "sqlite") -> List[str]:
        if dialect == "sqlite":
            return [f"-- SQLite: Constraints require table recreation for '{self.table}'"]
        return [f"ALTER TABLE {self.table} DROP CONSTRAINT {self.name}"]
    
    def description(self) -> str:
        return f"Add constraint '{self.name}' to '{self.table}'"


@dataclass
class DropConstraint(Change):
    """Drop a constraint."""
    table: str
    name: str
    constraint_sql: str = ""  # For down migration
    
    @property
    def change_type(self) -> ChangeType:
        return ChangeType.DROP_CONSTRAINT
    
    def up_sql(self, dialect: str = "sqlite") -> List[str]:
        if dialect == "sqlite":
            return [f"-- SQLite: Constraints require table recreation for '{self.table}'"]
        return [f"ALTER TABLE {self.table} DROP CONSTRAINT {self.name}"]
    
    def down_sql(self, dialect: str = "sqlite") -> List[str]:
        if not self.constraint_sql:
            return [f"-- Cannot recreate constraint '{self.name}' (no constraint info)"]
        if dialect == "sqlite":
            return [f"-- SQLite: Constraints require table recreation for '{self.table}'"]
        return [f"ALTER TABLE {self.table} ADD CONSTRAINT {self.name} {self.constraint_sql}"]
    
    def description(self) -> str:
        return f"Drop constraint '{self.name}' from '{self.table}'"


@dataclass
class RawSQL(Change):
    """Execute raw SQL."""
    up: str
    down: str
    desc: str = "Execute raw SQL"
    destructive: bool = False
    
    @property
    def change_type(self) -> ChangeType:
        return ChangeType.RAW_SQL
    
    def up_sql(self, dialect: str = "sqlite") -> List[str]:
        return [self.up]
    
    def down_sql(self, dialect: str = "sqlite") -> List[str]:
        return [self.down]
    
    def description(self) -> str:
        return self.desc
    
    def is_destructive(self) -> bool:
        return self.destructive


# Export all change types
__all__ = [
    "ChangeType",
    "ColumnDef",
    "Change",
    "CreateTable",
    "DropTable",
    "RenameTable",
    "AddColumn",
    "DropColumn",
    "RenameColumn",
    "AlterColumn",
    "AddIndex",
    "DropIndex",
    "AddConstraint",
    "DropConstraint",
    "RawSQL",
]

