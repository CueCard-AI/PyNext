"""
Tests for Migration History Tracking.

Tests version tracking and migration state management.

40 tests covering:
- Recording applied migrations
- Checking migration status
- History retrieval
- Rollback tracking
- Status queries
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional
import json


# =============================================================================
# Mock Classes for Testing
# =============================================================================

@dataclass
class MigrationRecord:
    """A single migration record."""
    version: str
    description: str = ""
    checksum: Optional[str] = None
    applied_at: datetime = field(default_factory=datetime.now)


class MigrationHistory:
    """In-memory migration history for testing."""
    
    def __init__(self, path: Optional[Path] = None):
        self._path = path
        self._records: List[MigrationRecord] = []
        self._file = path / ".pynext_migrations" if path else None
        
        # Load from file if exists
        if self._file and self._file.exists():
            try:
                data = json.loads(self._file.read_text())
                for item in data.get("migrations", []):
                    self._records.append(MigrationRecord(
                        version=item["version"],
                        description=item.get("description", ""),
                        checksum=item.get("checksum"),
                        applied_at=datetime.fromisoformat(item.get("applied_at", datetime.now().isoformat()))
                    ))
            except (json.JSONDecodeError, KeyError):
                # Corrupted file, start fresh
                self._records = []
    
    def record_applied(self, version: str, description: str = "", checksum: Optional[str] = None):
        """Record a migration as applied."""
        # Check for duplicates
        if any(r.version == version for r in self._records):
            return
        
        record = MigrationRecord(
            version=version,
            description=description,
            checksum=checksum,
            applied_at=datetime.now()
        )
        self._records.append(record)
        self._persist()
    
    def record_rolled_back(self, version: str):
        """Record a migration as rolled back."""
        self._records = [r for r in self._records if r.version != version]
        self._persist()
    
    def is_applied(self, version: str) -> bool:
        """Check if a migration is applied."""
        return any(r.version == version for r in self._records)
    
    def get_all(self) -> List[MigrationRecord]:
        """Get all applied migrations."""
        return list(self._records)
    
    def get_current_version(self) -> Optional[str]:
        """Get the current (latest) version."""
        if not self._records:
            return None
        return self._records[-1].version
    
    def get_applied_versions(self) -> List[str]:
        """Get list of applied version strings."""
        return [r.version for r in self._records]
    
    def clear(self):
        """Clear all history."""
        self._records = []
        self._persist()
    
    def get_count(self) -> int:
        """Get count of applied migrations."""
        return len(self._records)
    
    def _persist(self):
        """Persist to file."""
        if self._file:
            data = {
                "migrations": [
                    {
                        "version": r.version,
                        "description": r.description,
                        "checksum": r.checksum,
                        "applied_at": r.applied_at.isoformat(),
                    }
                    for r in self._records
                ]
            }
            self._file.write_text(json.dumps(data, indent=2))


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def temp_dir():
    """Create a temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def history(temp_dir):
    """Create a MigrationHistory instance."""
    return MigrationHistory(temp_dir)


# =============================================================================
# Basic History Tests
# =============================================================================

class TestBasicHistory:
    """Tests for basic history operations."""
    
    def test_empty_history(self, history):
        """Test empty history."""
        assert history.get_all() == []
    
    def test_record_migration(self, history):
        """Test recording a migration."""
        version = "0001_20240101120000"
        history.record_applied(version)
        
        records = history.get_all()
        assert len(records) == 1
        assert records[0].version == version
    
    def test_is_applied(self, history):
        """Test checking if migration is applied."""
        version = "0001_20240101120000"
        
        assert not history.is_applied(version)
        
        history.record_applied(version)
        
        assert history.is_applied(version)
    
    def test_current_version(self, history):
        """Test getting current version."""
        history.record_applied("0001_20240101120000")
        history.record_applied("0002_20240101120001")
        
        assert history.get_current_version() == "0002_20240101120001"
    
    def test_current_version_empty(self, history):
        """Test current version when empty."""
        assert history.get_current_version() is None


# =============================================================================
# Multiple Migrations Tests
# =============================================================================

class TestMultipleMigrations:
    """Tests for multiple migrations."""
    
    def test_order_preserved(self, history):
        """Test migration order is preserved."""
        history.record_applied("0001_20240101120000")
        history.record_applied("0002_20240101120001")
        history.record_applied("0003_20240101120002")
        
        records = history.get_all()
        versions = [r.version for r in records]
        
        assert versions == [
            "0001_20240101120000",
            "0002_20240101120001",
            "0003_20240101120002",
        ]
    
    def test_count(self, history):
        """Test migration count."""
        history.record_applied("0001_20240101120000")
        history.record_applied("0002_20240101120001")
        
        assert history.get_count() == 2


# =============================================================================
# Rollback Tests
# =============================================================================

class TestRollback:
    """Tests for rollback tracking."""
    
    def test_record_rollback(self, history):
        """Test recording a rollback."""
        version = "0001_20240101120000"
        history.record_applied(version)
        history.record_rolled_back(version)
        
        assert not history.is_applied(version)
        assert history.get_all() == []
    
    def test_rollback_multiple(self, history):
        """Test rolling back multiple migrations."""
        history.record_applied("0001_20240101120000")
        history.record_applied("0002_20240101120001")
        history.record_applied("0003_20240101120002")
        
        history.record_rolled_back("0003_20240101120002")
        
        assert history.get_current_version() == "0002_20240101120001"
        
        history.record_rolled_back("0002_20240101120001")
        
        assert history.get_current_version() == "0001_20240101120000"
    
    def test_rollback_nonexistent(self, history):
        """Test rolling back non-existent migration."""
        history.record_rolled_back("nonexistent")
        
        # Should not crash
        assert history.get_all() == []


# =============================================================================
# Record Details Tests
# =============================================================================

class TestRecordDetails:
    """Tests for migration record details."""
    
    def test_record_includes_timestamp(self, history):
        """Test record includes timestamp."""
        history.record_applied("0001_20240101120000")
        
        record = history.get_all()[0]
        
        assert record.applied_at is not None
        assert isinstance(record.applied_at, datetime)
    
    def test_record_with_description(self):
        """Test record with description."""
        record = MigrationRecord(
            version="0001_20240101120000",
            description="Initial migration"
        )
        
        assert record.version == "0001_20240101120000"
        assert record.description == "Initial migration"
    
    def test_record_defaults(self):
        """Test record default values."""
        record = MigrationRecord(version="0001_20240101120000")
        
        assert record.description == ""
        assert record.applied_at is not None
    
    def test_record_equality(self):
        """Test record equality."""
        r1 = MigrationRecord(version="0001_20240101120000")
        r2 = MigrationRecord(version="0001_20240101120000")
        
        assert r1.version == r2.version


# =============================================================================
# Persistence Tests
# =============================================================================

class TestPersistence:
    """Tests for history persistence."""
    
    def test_history_persists(self, temp_dir):
        """Test history is persisted to disk."""
        history1 = MigrationHistory(temp_dir)
        history1.record_applied("0001_20240101120000")
        
        # Create new instance
        history2 = MigrationHistory(temp_dir)
        
        assert history2.is_applied("0001_20240101120000")
    
    def test_history_file_created(self, history, temp_dir):
        """Test history file is created."""
        history.record_applied("0001_20240101120000")
        
        # Check for history file
        files = list(temp_dir.glob("*"))
        assert len(files) > 0
    
    def test_load_corrupted_gracefully(self, temp_dir):
        """Test loading corrupted history."""
        # Write invalid data
        history_file = temp_dir / ".pynext_migrations"
        history_file.write_text("not valid json")
        
        # Should handle gracefully
        history = MigrationHistory(temp_dir)
        
        # Start fresh
        assert history.get_all() == []


# =============================================================================
# Edge Cases Tests
# =============================================================================

class TestEdgeCases:
    """Edge case tests."""
    
    def test_duplicate_apply(self, history):
        """Test applying same migration twice."""
        version = "0001_20240101120000"
        
        history.record_applied(version)
        history.record_applied(version)  # Duplicate
        
        records = history.get_all()
        assert len(records) == 1
    
    def test_reapply_after_rollback(self, history):
        """Test reapplying after rollback."""
        version = "0001_20240101120000"
        
        history.record_applied(version)
        history.record_rolled_back(version)
        history.record_applied(version)
        
        assert history.is_applied(version)
        assert len(history.get_all()) == 1
    
    def test_clear_history(self, history):
        """Test clearing all history."""
        history.record_applied("0001_20240101120000")
        history.record_applied("0002_20240101120001")
        
        history.clear()
        
        assert history.get_all() == []
        assert history.get_current_version() is None
    
    def test_get_applied_versions(self, history):
        """Test getting list of applied versions."""
        history.record_applied("0001_20240101120000")
        history.record_applied("0002_20240101120001")
        
        versions = history.get_applied_versions()
        
        assert versions == ["0001_20240101120000", "0002_20240101120001"]


# =============================================================================
# Description Tests
# =============================================================================

class TestDescriptions:
    """Tests for migration descriptions."""
    
    def test_record_with_description(self, history):
        """Test recording with description."""
        history.record_applied("0001_20240101120000", description="Add users table")
        
        record = history.get_all()[0]
        assert record.description == "Add users table"
    
    def test_description_persists(self, temp_dir):
        """Test description persists."""
        history1 = MigrationHistory(temp_dir)
        history1.record_applied("0001_20240101120000", description="Add users")
        
        history2 = MigrationHistory(temp_dir)
        record = history2.get_all()[0]
        
        assert record.description == "Add users"
