"""
Migration File Generator.

Generates migration files from detected changes.
Supports both declarative and Python formats.

Design: Simple output, always reversible, human-readable.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from textwrap import dedent, indent
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from pynext.db.migrations.changes import Change


class MigrationGenerator:
    """
    Generates migration files.
    
    Supports two formats:
    1. Declarative: Simple create/alter/drop operations
    2. Python: Full async functions for complex migrations
    
    Usage:
        generator = MigrationGenerator(Path("migrations"))
        
        # Generate declarative migration
        path = generator.generate_declarative(
            changes=[CreateTable("users", [...])],
            message="create users table",
        )
        
        # Generate Python migration
        path = generator.generate_python(
            message="migrate user data",
        )
    """
    
    def __init__(
        self,
        migrations_dir: Path,
        dialect: str = "sqlite",
    ):
        """
        Args:
            migrations_dir: Directory to write migrations to
            dialect: SQL dialect for SQL generation
        """
        self.migrations_dir = migrations_dir
        self.dialect = dialect
        
        # Ensure migrations directory exists
        self.migrations_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_declarative(
        self,
        changes: List["Change"],
        message: str,
    ) -> Path:
        """
        Generate a declarative migration file.
        
        Best for simple schema changes.
        
        Args:
            changes: List of detected changes
            message: Migration message/description
            
        Returns:
            Path to generated migration file
        """
        version = self._generate_version()
        slug = self._slugify(message)
        filename = f"{version}_{slug}.py"
        filepath = self.migrations_dir / filename
        
        # Build content
        content = self._build_declarative_content(changes, message, version)
        
        filepath.write_text(content)
        return filepath
    
    def generate_python(
        self,
        message: str,
        template: str = "default",
    ) -> Path:
        """
        Generate a Python migration file.
        
        For complex data migrations.
        
        Args:
            message: Migration message/description
            template: Template to use ("default", "data", "empty")
            
        Returns:
            Path to generated migration file
        """
        version = self._generate_version()
        slug = self._slugify(message)
        filename = f"{version}_{slug}.py"
        filepath = self.migrations_dir / filename
        
        # Build content
        content = self._build_python_content(message, version, template)
        
        filepath.write_text(content)
        return filepath
    
    def generate_empty(self, message: str) -> Path:
        """
        Generate an empty migration file.
        
        For manual editing.
        
        Args:
            message: Migration message/description
            
        Returns:
            Path to generated migration file
        """
        return self.generate_python(message, template="empty")
    
    def _build_declarative_content(
        self,
        changes: List["Change"],
        message: str,
        version: str,
    ) -> str:
        """Build declarative migration file content."""
        # Collect SQL statements
        up_statements = []
        down_statements = []
        
        for change in changes:
            up_statements.extend(change.up_sql(self.dialect))
            down_statements.extend(change.down_sql(self.dialect))
        
        # Reverse down statements
        down_statements = list(reversed(down_statements))
        
        # Format SQL
        up_sql = self._format_sql_list(up_statements)
        down_sql = self._format_sql_list(down_statements)
        
        # Build descriptions
        descriptions = [f"  - {c.description()}" for c in changes]
        desc_block = "\n".join(descriptions)
        
        return dedent(f'''
            """
            {message}
            
            Migration: {version}
            
            Changes:
            {desc_block}
            """
            
            from pynext.db.migrations import migration
            
            
            # =========================================================================
            # Upgrade (apply changes)
            # =========================================================================
            
            {up_sql}
            
            
            # =========================================================================
            # Downgrade (reverse changes)
            # =========================================================================
            
            {down_sql}
        ''').strip() + "\n"
    
    def _build_python_content(
        self,
        message: str,
        version: str,
        template: str,
    ) -> str:
        """Build Python migration file content."""
        if template == "empty":
            return dedent(f'''
                """
                {message}
                
                Migration: {version}
                """
                
                from pynext.db.migrations import migration, op
                
                
                @migration.up
                async def upgrade():
                    """Apply the migration."""
                    pass
                
                
                @migration.down
                async def downgrade():
                    """Reverse the migration."""
                    pass
            ''').strip() + "\n"
        
        elif template == "data":
            return dedent(f'''
                """
                {message}
                
                Migration: {version}
                
                This is a data migration template.
                Use op.fetch() and op.execute() for data transformations.
                """
                
                from pynext.db.migrations import migration, op
                
                
                @migration.up
                async def upgrade():
                    """Apply the migration."""
                    # Example: Migrate data from old format to new format
                    async for row in op.fetch("SELECT id, old_column FROM my_table"):
                        new_value = transform(row["old_column"])
                        await op.execute(
                            "UPDATE my_table SET new_column = $1 WHERE id = $2",
                            new_value, row["id"]
                        )
                
                
                @migration.down
                async def downgrade():
                    """Reverse the migration."""
                    # Reverse the data transformation
                    async for row in op.fetch("SELECT id, new_column FROM my_table"):
                        old_value = reverse_transform(row["new_column"])
                        await op.execute(
                            "UPDATE my_table SET old_column = $1 WHERE id = $2",
                            old_value, row["id"]
                        )
                
                
                def transform(value):
                    """Transform old value to new format."""
                    # TODO: Implement transformation
                    return value
                
                
                def reverse_transform(value):
                    """Reverse transformation."""
                    # TODO: Implement reverse transformation
                    return value
            ''').strip() + "\n"
        
        else:  # default
            return dedent(f'''
                """
                {message}
                
                Migration: {version}
                """
                
                from pynext.db.migrations import migration, op
                
                
                @migration.up
                async def upgrade():
                    """Apply the migration."""
                    # Schema changes
                    # await op.add_column("table", "column", "varchar(255)")
                    
                    # Data migration (optional)
                    # async for row in op.fetch("SELECT * FROM table"):
                    #     await op.execute("UPDATE table SET ... WHERE id = $1", row["id"])
                    pass
                
                
                @migration.down
                async def downgrade():
                    """Reverse the migration."""
                    # Reverse the changes made in upgrade()
                    # await op.drop_column("table", "column")
                    pass
            ''').strip() + "\n"
    
    def _format_sql_list(self, statements: List[str]) -> str:
        """Format a list of SQL statements as migration code."""
        if not statements:
            return "# No changes"
        
        lines = []
        for stmt in statements:
            if stmt.startswith("--"):
                lines.append(f"# {stmt[3:]}")
            else:
                # Multi-line SQL
                if "\n" in stmt:
                    lines.append(f'migration.sql("""')
                    lines.append(stmt)
                    lines.append('""")')
                else:
                    lines.append(f'migration.sql("{stmt}")')
        
        return "\n".join(lines)
    
    def _generate_version(self) -> str:
        """Generate a unique version string."""
        # Format: NNNN_YYYYMMDDHHMMSS
        # NNNN is a sequential number
        existing = list(self.migrations_dir.glob("*.py"))
        
        # Extract numbers from existing files
        numbers = []
        for f in existing:
            match = re.match(r"^(\d{4})_", f.name)
            if match:
                numbers.append(int(match.group(1)))
        
        next_num = max(numbers, default=0) + 1
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        return f"{next_num:04d}_{timestamp}"
    
    def _slugify(self, text: str) -> str:
        """Convert text to a valid filename slug."""
        # Lowercase
        slug = text.lower()
        
        # Replace spaces and special chars with underscores
        slug = re.sub(r"[^a-z0-9]+", "_", slug)
        
        # Remove leading/trailing underscores
        slug = slug.strip("_")
        
        # Limit length
        if len(slug) > 50:
            slug = slug[:50].rsplit("_", 1)[0]
        
        return slug or "migration"
    
    def get_next_version(self) -> str:
        """Get the next migration version number."""
        return self._generate_version()
    
    def list_migrations(self) -> List[Path]:
        """List all migration files in order."""
        files = list(self.migrations_dir.glob("*.py"))
        
        # Filter out __init__.py
        files = [f for f in files if not f.name.startswith("_")]
        
        # Sort by version number
        def sort_key(f: Path) -> tuple:
            match = re.match(r"^(\d{4})_(\d{14})", f.name)
            if match:
                return (int(match.group(1)), match.group(2))
            return (0, "")
        
        return sorted(files, key=sort_key)


__all__ = [
    "MigrationGenerator",
]

