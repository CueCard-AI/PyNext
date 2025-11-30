"""
Core Migration Engine.

The main entry point for all migration operations.
Coordinates between detector, generator, executor, and history.

Design: One-liner for common operations, full control when needed.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Type, TYPE_CHECKING

from pynext.db.migrations.changes import Change
from pynext.db.migrations.detector import (
    AmbiguousChange,
    DetectionResult,
    ModelDiffer,
)
from pynext.db.migrations.executor import (
    Migration,
    MigrationExecutor,
    MigrationInfo,
    MigrationResult,
    migration,
)
from pynext.db.migrations.formatter import MigrationFormatter
from pynext.db.migrations.generator import MigrationGenerator
from pynext.db.migrations.history import MigrationHistory, MigrationRecord
from pynext.db.migrations.operations import op
from pynext.db.migrations.prompt import (
    InteractivePrompt,
    NonInteractivePrompt,
    PromptResult,
)

if TYPE_CHECKING:
    from pynext.db.adapters.base import Adapter
    from pynext.db.table import Table


@dataclass
class MigrationEngineConfig:
    """Configuration for the migration engine."""
    migrations_dir: Path = Path("migrations")
    dialect: str = "sqlite"
    interactive: bool = True
    use_colors: bool = True
    auto_create_dir: bool = True


class MigrationEngine:
    """
    Main migration engine - coordinates all migration operations.
    
    This is the primary API for working with migrations:
    
    ```python
    from pynext.db import _model_registry, get_adapter
    from pynext.db.migrations import MigrationEngine
    
    # Create engine
    engine = MigrationEngine(
        models=_model_registry,
        adapter=get_adapter(),
    )
    
    # Detect changes
    result = await engine.detect()
    print(result.changes)
    
    # Generate migration
    path = await engine.generate(message="add user roles")
    
    # Apply migrations
    result = await engine.upgrade()
    
    # Rollback
    result = await engine.downgrade()
    
    # Get status
    status = await engine.status()
    ```
    """
    
    def __init__(
        self,
        models: Dict[str, Type["Table"]],
        adapter: "Adapter",
        config: Optional[MigrationEngineConfig] = None,
    ):
        """
        Args:
            models: Registry of model classes
            adapter: Database adapter
            config: Engine configuration
        """
        self.models = models
        self.adapter = adapter
        self.config = config or MigrationEngineConfig()
        
        # Ensure migrations directory exists
        if self.config.auto_create_dir:
            self.config.migrations_dir.mkdir(parents=True, exist_ok=True)
        
        # Create sub-components
        self.differ = ModelDiffer(models, adapter)
        self.generator = MigrationGenerator(
            self.config.migrations_dir,
            self.config.dialect,
        )
        self.executor = MigrationExecutor(
            adapter,
            self.config.migrations_dir,
            self.config.dialect,
        )
        self.history = MigrationHistory(adapter)
        self.formatter = MigrationFormatter(use_color=self.config.use_colors)
        
        if self.config.interactive:
            self.prompt = InteractivePrompt()
        else:
            self.prompt = NonInteractivePrompt()
    
    # =========================================================================
    # High-Level Operations
    # =========================================================================
    
    async def detect(self) -> DetectionResult:
        """
        Detect schema changes between models and database.
        
        Returns:
            DetectionResult with changes and ambiguous cases
        """
        return await self.differ.detect()
    
    async def generate(
        self,
        message: str,
        resolve_ambiguous: bool = True,
        empty_ok: bool = False,
    ) -> Optional[Path]:
        """
        Generate a migration from detected changes.
        
        Args:
            message: Migration description
            resolve_ambiguous: Prompt for ambiguous changes
            empty_ok: Allow creating empty migrations
            
        Returns:
            Path to generated migration, or None if no changes
        """
        # Detect changes
        result = await self.detect()
        
        # Resolve ambiguous changes
        all_changes = list(result.changes)
        
        if resolve_ambiguous and result.ambiguous:
            prompt_result = self.prompt.resolve_all(result.ambiguous)
            all_changes.extend(prompt_result.resolved_changes)
        
        # Check if we have changes
        if not all_changes:
            if empty_ok:
                return self.generator.generate_empty(message)
            return None
        
        # Generate migration file
        return self.generator.generate_declarative(all_changes, message)
    
    async def generate_python(self, message: str) -> Path:
        """
        Generate an empty Python migration for manual editing.
        
        Args:
            message: Migration description
            
        Returns:
            Path to generated migration
        """
        return self.generator.generate_python(message, template="default")
    
    async def generate_data_migration(self, message: str) -> Path:
        """
        Generate a data migration template.
        
        Args:
            message: Migration description
            
        Returns:
            Path to generated migration
        """
        return self.generator.generate_python(message, template="data")
    
    async def upgrade(
        self,
        target: Optional[str] = None,
        dry_run: bool = False,
    ) -> MigrationResult:
        """
        Apply pending migrations.
        
        Args:
            target: Stop at this version (None = all pending)
            dry_run: Show SQL without applying
            
        Returns:
            MigrationResult
        """
        return await self.executor.upgrade(target=target, dry_run=dry_run)
    
    async def downgrade(
        self,
        target: Optional[str] = None,
        steps: int = 1,
        dry_run: bool = False,
    ) -> MigrationResult:
        """
        Rollback migrations.
        
        Args:
            target: Rollback to this version (exclusive)
            steps: Number of migrations to rollback (if no target)
            dry_run: Show SQL without applying
            
        Returns:
            MigrationResult
        """
        return await self.executor.downgrade(
            target=target,
            steps=steps,
            dry_run=dry_run,
        )
    
    async def reset(self, confirm: bool = False) -> MigrationResult:
        """
        Reset database (rollback all, then apply all).
        
        Args:
            confirm: Must be True to proceed
            
        Returns:
            Combined MigrationResult
        """
        if not confirm:
            raise ValueError("Pass confirm=True to reset the database")
        
        # Rollback all
        down_result = await self.downgrade(steps=9999)
        
        if not down_result.success:
            return down_result
        
        # Apply all
        up_result = await self.upgrade()
        
        # Combine results
        return MigrationResult(
            success=up_result.success,
            applied=up_result.applied,
            errors=down_result.errors + up_result.errors,
            elapsed_ms=down_result.elapsed_ms + up_result.elapsed_ms,
        )
    
    # =========================================================================
    # Status and History
    # =========================================================================
    
    async def status(self) -> dict:
        """
        Get comprehensive migration status.
        
        Returns:
            Status dict with applied/pending counts
        """
        return await self.history.get_status(self.config.migrations_dir)
    
    async def current(self) -> Optional[str]:
        """
        Get the current migration version.
        
        Returns:
            Current version or None
        """
        return await self.history.get_current()
    
    async def history(self) -> List[MigrationRecord]:
        """
        Get migration history.
        
        Returns:
            List of applied migrations
        """
        return await self.history.get_applied()
    
    async def pending(self) -> List[dict]:
        """
        Get pending migrations.
        
        Returns:
            List of pending migration info
        """
        return await self.history.get_pending(self.config.migrations_dir)
    
    # =========================================================================
    # Preview and Formatting
    # =========================================================================
    
    async def preview(self, direction: str = "up") -> str:
        """
        Preview SQL that would be executed.
        
        Args:
            direction: "up" or "down"
            
        Returns:
            Formatted SQL preview
        """
        sql = await self.executor.preview_sql(direction)
        return "\n".join(sql)
    
    def format_result(self, result: MigrationResult) -> str:
        """Format a migration result for display."""
        lines = []
        
        if result.success:
            lines.append(self.formatter._color("✓ Migration successful", self.formatter.GREEN))
        else:
            lines.append(self.formatter._color("✗ Migration failed", self.formatter.RED))
        
        if result.applied:
            lines.append(f"\nApplied {len(result.applied)} migration(s):")
            for version in result.applied:
                lines.append(f"  • {version}")
        
        if result.errors:
            lines.append("\nErrors:")
            for error in result.errors:
                lines.append(f"  • {self.formatter._color(error, self.formatter.RED)}")
        
        lines.append(f"\nElapsed: {result.elapsed_ms:.1f}ms")
        
        return "\n".join(lines)
    
    def format_status(self, status: dict) -> str:
        """Format status for display."""
        return self.formatter.format_status(
            applied=status["applied_count"],
            pending=status["pending_count"],
            current=status["current"],
        )
    
    def format_detection(self, result: DetectionResult) -> str:
        """Format detection result for display."""
        return self.formatter.format_detection(result)
    
    # =========================================================================
    # Initialization
    # =========================================================================
    
    async def init(self) -> Path:
        """
        Initialize migrations directory.
        
        Creates the migrations folder and __init__.py.
        
        Returns:
            Path to migrations directory
        """
        migrations_dir = self.config.migrations_dir
        migrations_dir.mkdir(parents=True, exist_ok=True)
        
        # Create __init__.py
        init_file = migrations_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text('"""PyNext migrations."""\n')
        
        # Initialize history table
        await self.history.initialize()
        
        return migrations_dir
    
    def list_migrations(self) -> List[MigrationInfo]:
        """List all migration files."""
        return self.executor.list_migrations()
    
    async def verify(self) -> List[str]:
        """
        Verify migration integrity.
        
        Returns:
            List of warnings
        """
        return await self.history.verify_integrity(self.config.migrations_dir)


# Factory function for easy creation
def create_engine(
    migrations_dir: str = "migrations",
    dialect: str = "sqlite",
    interactive: bool = True,
) -> MigrationEngine:
    """
    Create a migration engine with default configuration.
    
    Args:
        migrations_dir: Path to migrations directory
        dialect: SQL dialect
        interactive: Enable interactive prompts
        
    Returns:
        Configured MigrationEngine
    """
    from pynext.db import _model_registry, get_adapter
    
    config = MigrationEngineConfig(
        migrations_dir=Path(migrations_dir),
        dialect=dialect,
        interactive=interactive,
    )
    
    return MigrationEngine(
        models=_model_registry,
        adapter=get_adapter(),
        config=config,
    )


__all__ = [
    "MigrationEngine",
    "MigrationEngineConfig",
    "create_engine",
]

