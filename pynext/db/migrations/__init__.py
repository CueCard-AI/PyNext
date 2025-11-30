"""
PyNext Database Migrations.

A migration system that wraps Alembic with a radically simplified API.
One-liners for common operations, full power when needed.

Quick Start:
    # Initialize migrations
    pynext db init
    
    # Generate migration from model changes
    pynext db migrate -m "add user roles"
    
    # Apply all pending migrations
    pynext db upgrade
    
    # Rollback last migration
    pynext db downgrade

Python API:
    from pynext.db.migrations import MigrationEngine, migration, op
    
    # Create engine
    engine = MigrationEngine(models, adapter)
    
    # Detect changes
    result = await engine.detect()
    
    # Generate migration
    path = await engine.generate("add user roles")
    
    # Apply migrations
    result = await engine.upgrade()

Migration File Formats:

    1. Declarative (simple operations):
    
        from pynext.db.migrations import migration
        
        migration.create_table("users", {
            "id": "serial primary key",
            "email": "varchar(255) unique not null",
        })
        
        migration.create_index("users", ["email"], unique=True)
    
    2. Python (complex operations):
    
        from pynext.db.migrations import migration, op
        
        @migration.up
        async def upgrade():
            await op.add_column("users", "full_name", "varchar(255)")
            
            async for row in op.fetch("SELECT id, first, last FROM users"):
                await op.execute(
                    "UPDATE users SET full_name = $1 WHERE id = $2",
                    f"{row['first']} {row['last']}", row["id"]
                )
        
        @migration.down
        async def downgrade():
            await op.drop_column("users", "full_name")
"""

# Core engine
from pynext.db.migrations.engine import (
    MigrationEngine,
    MigrationEngineConfig,
    create_engine,
)

# Executor and migration DSL
from pynext.db.migrations.executor import (
    Migration,
    MigrationExecutor,
    MigrationInfo,
    MigrationResult,
    migration,
)

# Operations for Python migrations
from pynext.db.migrations.operations import (
    Operations,
    op,
)

# Change detection
from pynext.db.migrations.detector import (
    AmbiguousChange,
    DetectionResult,
    ModelDiffer,
    TableSchema,
    field_to_column_def,
)

# Change types
from pynext.db.migrations.changes import (
    AddColumn,
    AddConstraint,
    AddIndex,
    AlterColumn,
    Change,
    ChangeType,
    ColumnDef,
    CreateTable,
    DropColumn,
    DropConstraint,
    DropIndex,
    DropTable,
    RawSQL,
    RenameColumn,
    RenameTable,
)

# History tracking
from pynext.db.migrations.history import (
    MigrationHistory,
    MigrationRecord,
    compute_checksum,
    parse_version,
    version_sort_key,
)

# Migration generation
from pynext.db.migrations.generator import MigrationGenerator

# Formatting
from pynext.db.migrations.formatter import (
    MigrationFormatter,
    PlainFormatter,
)

# Interactive prompts
from pynext.db.migrations.prompt import (
    InteractivePrompt,
    NonInteractivePrompt,
    PromptResult,
    TestPrompt,
)

__all__ = [
    # Core engine
    "MigrationEngine",
    "MigrationEngineConfig",
    "create_engine",
    
    # Executor
    "Migration",
    "MigrationExecutor",
    "MigrationInfo",
    "MigrationResult",
    "migration",
    
    # Operations
    "Operations",
    "op",
    
    # Detection
    "AmbiguousChange",
    "DetectionResult",
    "ModelDiffer",
    "TableSchema",
    "field_to_column_def",
    
    # Changes
    "AddColumn",
    "AddConstraint",
    "AddIndex",
    "AlterColumn",
    "Change",
    "ChangeType",
    "ColumnDef",
    "CreateTable",
    "DropColumn",
    "DropConstraint",
    "DropIndex",
    "DropTable",
    "RawSQL",
    "RenameColumn",
    "RenameTable",
    
    # History
    "MigrationHistory",
    "MigrationRecord",
    "compute_checksum",
    "parse_version",
    "version_sort_key",
    
    # Generator
    "MigrationGenerator",
    
    # Formatter
    "MigrationFormatter",
    "PlainFormatter",
    
    # Prompts
    "InteractivePrompt",
    "NonInteractivePrompt",
    "PromptResult",
    "TestPrompt",
]

