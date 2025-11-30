"""
Migration Formatter.

Formats changes into human-readable output.
Used for previews, diffs, and logging.

Design: Clear, consistent, colorful (when supported).
"""

from __future__ import annotations

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from pynext.db.migrations.changes import Change
    from pynext.db.migrations.detector import DetectionResult


class MigrationFormatter:
    """
    Formats migration changes for display.
    
    Usage:
        formatter = MigrationFormatter()
        
        # Format detection result
        output = formatter.format_detection(result)
        print(output)
        
        # Format SQL preview
        sql = formatter.format_sql(changes, dialect="postgresql")
        print(sql)
    """
    
    # ANSI colors
    RESET = "\033[0m"
    GREEN = "\033[32m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    
    def __init__(self, use_color: bool = True):
        """
        Args:
            use_color: Whether to use ANSI colors
        """
        self.use_color = use_color
    
    def format_detection(self, result: "DetectionResult") -> str:
        """
        Format a detection result for display.
        
        Args:
            result: Detection result from ModelDiffer
            
        Returns:
            Formatted string
        """
        lines = []
        
        if not result.has_changes:
            lines.append(self._color("No changes detected.", self.DIM))
            return "\n".join(lines)
        
        # Header
        total = len(result.changes) + len(result.ambiguous)
        lines.append(self._color(f"Detected {total} change(s):", self.BOLD))
        lines.append("")
        
        # Changes
        for change in result.changes:
            icon = self._get_icon(change)
            color = self._get_color(change)
            desc = change.description()
            
            lines.append(f"  {icon} {self._color(desc, color)}")
        
        # Ambiguous (need confirmation)
        if result.ambiguous:
            lines.append("")
            lines.append(self._color("Requires confirmation:", self.YELLOW + self.BOLD))
            
            for ambig in result.ambiguous:
                lines.append(f"  ? {self._color(ambig.description, self.YELLOW)}")
        
        # Warnings
        if result.warnings:
            lines.append("")
            lines.append(self._color("Warnings:", self.YELLOW + self.BOLD))
            
            for warning in result.warnings:
                lines.append(f"  ⚠ {self._color(warning, self.YELLOW)}")
        
        # Destructive warning
        if result.has_destructive:
            lines.append("")
            lines.append(self._color(
                "⚠ Some changes may cause data loss. Review carefully.",
                self.RED + self.BOLD,
            ))
        
        return "\n".join(lines)
    
    def format_changes(self, changes: List["Change"]) -> str:
        """
        Format a list of changes.
        
        Args:
            changes: List of changes
            
        Returns:
            Formatted string
        """
        if not changes:
            return self._color("No changes.", self.DIM)
        
        lines = []
        for change in changes:
            icon = self._get_icon(change)
            color = self._get_color(change)
            desc = change.description()
            
            lines.append(f"  {icon} {self._color(desc, color)}")
        
        return "\n".join(lines)
    
    def format_sql(
        self,
        changes: List["Change"],
        dialect: str = "sqlite",
        direction: str = "up",
    ) -> str:
        """
        Format SQL statements for changes.
        
        Args:
            changes: List of changes
            dialect: SQL dialect
            direction: "up" or "down"
            
        Returns:
            Formatted SQL
        """
        lines = []
        
        header = "UPGRADE" if direction == "up" else "DOWNGRADE"
        lines.append(self._color(f"-- {header} SQL ({dialect})", self.DIM))
        lines.append("")
        
        for change in changes:
            # Description comment
            lines.append(self._color(f"-- {change.description()}", self.DIM))
            
            # SQL
            if direction == "up":
                statements = change.up_sql(dialect)
            else:
                statements = change.down_sql(dialect)
            
            for stmt in statements:
                if stmt.startswith("--"):
                    lines.append(self._color(stmt, self.YELLOW))
                else:
                    lines.append(self._color(stmt + ";", self.CYAN))
            
            lines.append("")
        
        return "\n".join(lines)
    
    def format_migration_file(self, path: "Path", content: str) -> str:
        """
        Format a migration file for display.
        
        Args:
            path: Path to the file
            content: File content
            
        Returns:
            Formatted display
        """
        lines = []
        
        lines.append(self._color(f"Created: {path.name}", self.GREEN + self.BOLD))
        lines.append("")
        lines.append(self._color("─" * 60, self.DIM))
        
        # Show first 30 lines
        content_lines = content.split("\n")
        for i, line in enumerate(content_lines[:30]):
            line_num = self._color(f"{i+1:3d} │ ", self.DIM)
            lines.append(line_num + line)
        
        if len(content_lines) > 30:
            lines.append(self._color(f"    │ ... ({len(content_lines) - 30} more lines)", self.DIM))
        
        lines.append(self._color("─" * 60, self.DIM))
        
        return "\n".join(lines)
    
    def format_history(
        self,
        migrations: List[dict],
        current: str = None,
    ) -> str:
        """
        Format migration history.
        
        Args:
            migrations: List of migration info dicts
            current: Current migration version
            
        Returns:
            Formatted history
        """
        lines = []
        
        if not migrations:
            return self._color("No migrations found.", self.DIM)
        
        lines.append(self._color("Migration History:", self.BOLD))
        lines.append("")
        
        for mig in migrations:
            version = mig.get("version", "???")
            name = mig.get("name", "unknown")
            applied = mig.get("applied_at")
            
            if version == current:
                icon = self._color("→", self.GREEN + self.BOLD)
            elif applied:
                icon = self._color("✓", self.GREEN)
            else:
                icon = self._color("○", self.DIM)
            
            if applied:
                status = self._color(f"(applied {applied})", self.DIM)
            else:
                status = self._color("(pending)", self.YELLOW)
            
            lines.append(f"  {icon} {version} - {name} {status}")
        
        return "\n".join(lines)
    
    def format_status(
        self,
        applied: int,
        pending: int,
        current: str = None,
    ) -> str:
        """
        Format migration status summary.
        
        Args:
            applied: Number of applied migrations
            pending: Number of pending migrations
            current: Current migration version
            
        Returns:
            Status string
        """
        lines = []
        
        lines.append(self._color("Migration Status:", self.BOLD))
        lines.append("")
        
        lines.append(f"  Applied: {self._color(str(applied), self.GREEN)}")
        
        if pending > 0:
            lines.append(f"  Pending: {self._color(str(pending), self.YELLOW)}")
        else:
            lines.append(f"  Pending: {self._color('0', self.GREEN)}")
        
        if current:
            lines.append(f"  Current: {self._color(current, self.BLUE)}")
        
        return "\n".join(lines)
    
    def _color(self, text: str, color: str) -> str:
        """Apply color if enabled."""
        if self.use_color:
            return f"{color}{text}{self.RESET}"
        return text
    
    def _get_icon(self, change: "Change") -> str:
        """Get icon for a change type."""
        from pynext.db.migrations.changes import ChangeType
        
        icons = {
            ChangeType.CREATE_TABLE: "✚",
            ChangeType.DROP_TABLE: "✖",
            ChangeType.RENAME_TABLE: "↹",
            ChangeType.ADD_COLUMN: "+",
            ChangeType.DROP_COLUMN: "-",
            ChangeType.RENAME_COLUMN: "~",
            ChangeType.ALTER_COLUMN: "≈",
            ChangeType.ADD_INDEX: "⊕",
            ChangeType.DROP_INDEX: "⊖",
            ChangeType.ADD_CONSTRAINT: "⊕",
            ChangeType.DROP_CONSTRAINT: "⊖",
            ChangeType.RAW_SQL: "◇",
        }
        
        icon = icons.get(change.change_type, "•")
        
        if change.is_destructive():
            return self._color(icon, self.RED)
        else:
            return self._color(icon, self.GREEN)
    
    def _get_color(self, change: "Change") -> str:
        """Get color for a change type."""
        if change.is_destructive():
            return self.RED
        
        from pynext.db.migrations.changes import ChangeType
        
        colors = {
            ChangeType.CREATE_TABLE: self.GREEN,
            ChangeType.DROP_TABLE: self.RED,
            ChangeType.ADD_COLUMN: self.GREEN,
            ChangeType.DROP_COLUMN: self.RED,
            ChangeType.RENAME_COLUMN: self.YELLOW,
            ChangeType.RENAME_TABLE: self.YELLOW,
            ChangeType.ALTER_COLUMN: self.YELLOW,
        }
        
        return colors.get(change.change_type, "")


class PlainFormatter(MigrationFormatter):
    """Formatter without colors (for logs, CI)."""
    
    def __init__(self):
        super().__init__(use_color=False)


__all__ = [
    "MigrationFormatter",
    "PlainFormatter",
]

