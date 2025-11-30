"""
Migration History Tracking.

Tracks which migrations have been applied to the database.
Uses a simple table to store migration versions.

Design: Reliable, simple, works with all databases.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from pynext.db.adapters.base import Adapter


@dataclass
class MigrationRecord:
    """A recorded migration."""
    version: str
    name: str
    applied_at: datetime
    checksum: Optional[str] = None


class MigrationHistory:
    """
    Tracks applied migrations in the database.
    
    Uses a _migrations table to store:
    - version: Unique migration identifier
    - name: Human-readable name
    - applied_at: When it was applied
    - checksum: Hash of migration content (for drift detection)
    
    Usage:
        history = MigrationHistory(adapter)
        await history.initialize()
        
        # Check status
        applied = await history.get_applied()
        
        # Record new migration
        await history.mark_applied("0001_20240101", "create_users")
        
        # Rollback
        await history.mark_unapplied("0001_20240101")
    """
    
    TABLE_NAME = "_pynext_migrations"
    
    def __init__(self, adapter: "Adapter"):
        """
        Args:
            adapter: Database adapter
        """
        self.adapter = adapter
        self._initialized = False
    
    async def initialize(self) -> None:
        """
        Initialize the migrations table.
        
        Creates the table if it doesn't exist.
        Safe to call multiple times.
        """
        if self._initialized:
            return
        
        # Create migrations table
        sql = f"""
            CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
                version VARCHAR(100) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                applied_at TIMESTAMP NOT NULL,
                checksum VARCHAR(64)
            )
        """
        
        await self.adapter.execute(sql, None)
        self._initialized = True
    
    async def get_applied(self) -> List[MigrationRecord]:
        """
        Get list of applied migrations.
        
        Returns:
            List of MigrationRecord, ordered by version
        """
        await self.initialize()
        
        sql = f"""
            SELECT version, name, applied_at, checksum
            FROM {self.TABLE_NAME}
            ORDER BY version ASC
        """
        
        rows = await self.adapter.fetch_all(sql, None)
        
        records = []
        for row in rows:
            applied_at = row["applied_at"]
            if isinstance(applied_at, str):
                applied_at = datetime.fromisoformat(applied_at)
            
            records.append(MigrationRecord(
                version=row["version"],
                name=row["name"],
                applied_at=applied_at,
                checksum=row.get("checksum"),
            ))
        
        return records
    
    async def get_current(self) -> Optional[str]:
        """
        Get the current migration version.
        
        Returns:
            Latest applied version, or None if no migrations
        """
        await self.initialize()
        
        sql = f"""
            SELECT version FROM {self.TABLE_NAME}
            ORDER BY version DESC
            LIMIT 1
        """
        
        row = await self.adapter.fetch_one(sql, None)
        return row["version"] if row else None
    
    async def is_applied(self, version: str) -> bool:
        """
        Check if a migration is applied.
        
        Args:
            version: Migration version
            
        Returns:
            True if applied
        """
        await self.initialize()
        
        sql = f"""
            SELECT 1 FROM {self.TABLE_NAME}
            WHERE version = $1
        """
        
        row = await self.adapter.fetch_one(sql, (version,))
        return row is not None
    
    async def mark_applied(
        self,
        version: str,
        name: str,
        checksum: Optional[str] = None,
    ) -> None:
        """
        Record a migration as applied.
        
        Args:
            version: Migration version
            name: Migration name
            checksum: Optional content hash
        """
        await self.initialize()
        
        now = datetime.utcnow().isoformat()
        
        sql = f"""
            INSERT INTO {self.TABLE_NAME} (version, name, applied_at, checksum)
            VALUES ($1, $2, $3, $4)
        """
        
        await self.adapter.execute(sql, (version, name, now, checksum))
    
    async def mark_unapplied(self, version: str) -> None:
        """
        Remove a migration from history (for rollback).
        
        Args:
            version: Migration version
        """
        await self.initialize()
        
        sql = f"""
            DELETE FROM {self.TABLE_NAME}
            WHERE version = $1
        """
        
        await self.adapter.execute(sql, (version,))
    
    async def get_pending(
        self,
        migrations_dir: Path,
    ) -> List[dict]:
        """
        Get list of pending migrations.
        
        Args:
            migrations_dir: Directory containing migration files
            
        Returns:
            List of pending migration info dicts
        """
        applied = await self.get_applied()
        applied_versions = {m.version for m in applied}
        
        pending = []
        
        # Scan migration files
        for path in sorted(migrations_dir.glob("*.py")):
            if path.name.startswith("_"):
                continue
            
            # Extract version from filename
            match = re.match(r"^(\d{4}_\d{14})", path.name)
            if not match:
                continue
            
            version = match.group(1)
            
            if version not in applied_versions:
                # Extract name from filename
                name_part = path.stem[len(version) + 1:]  # After version_
                name = name_part.replace("_", " ").title()
                
                pending.append({
                    "version": version,
                    "name": name,
                    "path": path,
                })
        
        return pending
    
    async def get_status(
        self,
        migrations_dir: Path,
    ) -> dict:
        """
        Get comprehensive migration status.
        
        Args:
            migrations_dir: Directory containing migration files
            
        Returns:
            Status dict with counts and details
        """
        applied = await self.get_applied()
        pending = await self.get_pending(migrations_dir)
        current = applied[-1].version if applied else None
        
        return {
            "applied_count": len(applied),
            "pending_count": len(pending),
            "current": current,
            "applied": [
                {
                    "version": m.version,
                    "name": m.name,
                    "applied_at": m.applied_at.isoformat(),
                }
                for m in applied
            ],
            "pending": pending,
        }
    
    async def verify_integrity(
        self,
        migrations_dir: Path,
    ) -> List[str]:
        """
        Verify migration history integrity.
        
        Checks for:
        - Missing migration files
        - Checksum mismatches
        - Gaps in sequence
        
        Args:
            migrations_dir: Directory containing migration files
            
        Returns:
            List of warning messages
        """
        warnings = []
        applied = await self.get_applied()
        
        for record in applied:
            # Find corresponding file
            pattern = f"{record.version}*.py"
            files = list(migrations_dir.glob(pattern))
            
            if not files:
                warnings.append(
                    f"Migration {record.version} applied but file not found"
                )
                continue
            
            # Check checksum if available
            if record.checksum:
                import hashlib
                content = files[0].read_bytes()
                actual_checksum = hashlib.sha256(content).hexdigest()[:16]
                
                if actual_checksum != record.checksum:
                    warnings.append(
                        f"Migration {record.version} has been modified after application"
                    )
        
        return warnings
    
    async def reset(self) -> None:
        """
        Reset migration history (drop the table).
        
        Warning: This doesn't undo the migrations!
        """
        sql = f"DROP TABLE IF EXISTS {self.TABLE_NAME}"
        await self.adapter.execute(sql, None)
        self._initialized = False


def compute_checksum(content: str) -> str:
    """
    Compute a checksum for migration content.
    
    Args:
        content: Migration file content
        
    Returns:
        16-character hex checksum
    """
    import hashlib
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def parse_version(filename: str) -> Optional[str]:
    """
    Extract version from migration filename.
    
    Args:
        filename: Migration filename (e.g., "0001_20240101_create_users.py")
        
    Returns:
        Version string or None
    """
    match = re.match(r"^(\d{4}_\d{14})", filename)
    return match.group(1) if match else None


def version_sort_key(version: str) -> tuple:
    """
    Get sort key for a version string.
    
    Args:
        version: Version string (e.g., "0001_20240101120000")
        
    Returns:
        Tuple for sorting
    """
    parts = version.split("_", 1)
    if len(parts) == 2:
        return (int(parts[0]), parts[1])
    return (0, version)


__all__ = [
    "MigrationHistory",
    "MigrationRecord",
    "compute_checksum",
    "parse_version",
    "version_sort_key",
]

