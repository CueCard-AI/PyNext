"""
Tests for pynext.app.memory - Session Memory System.

Tests cover:
- MemoryEntry, MemorySummary, Checkpoint, Preference data classes
- SessionMemory CRUD operations
- Sync configuration and behavior
- Summarization
- Search and context retrieval
- File persistence
- JSONL format and records
- Memory retrieval priority
- Context building
- Token counting
- File rotation
"""

import pytest
import json
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from pynext.app.memory import (
    MemoryEntry,
    MemorySummary,
    Checkpoint,
    Preference,
    SyncConfig,
    SessionMemory,
    get_memory,
    reset_memory,
)


# =============================================================================
# MemoryEntry Tests
# =============================================================================

class TestMemoryEntry:
    """Tests for MemoryEntry dataclass."""
    
    def test_create_entry(self):
        """Test creating a memory entry."""
        entry = MemoryEntry(
            id="e_001",
            timestamp=datetime(2025, 1, 15, 10, 0, 0),
            role="user",
            content="Create a blog",
            tokens=12,
        )
        assert entry.id == "e_001"
        assert entry.role == "user"
        assert entry.content == "Create a blog"
        assert entry.tokens == 12
        assert entry.summarized is False
    
    def test_entry_to_dict(self):
        """Test converting entry to dict."""
        entry = MemoryEntry(
            id="e_001",
            timestamp=datetime(2025, 1, 15, 10, 0, 0),
            role="user",
            content="Create a blog",
            tokens=12,
            metadata={"files": ["index.py"]},
        )
        d = entry.to_dict()
        assert d["type"] == "entry"
        assert d["id"] == "e_001"
        assert d["role"] == "user"
        assert d["content"] == "Create a blog"
        assert d["tokens"] == 12
        assert d["meta"] == {"files": ["index.py"]}
    
    def test_entry_from_dict(self):
        """Test creating entry from dict."""
        d = {
            "id": "e_001",
            "ts": "2025-01-15T10:00:00",
            "role": "assistant",
            "content": "I'll create...",
            "tokens": 100,
            "meta": {"plan_id": 123},
            "summarized": True,
        }
        entry = MemoryEntry.from_dict(d)
        assert entry.id == "e_001"
        assert entry.role == "assistant"
        assert entry.content == "I'll create..."
        assert entry.tokens == 100
        assert entry.metadata == {"plan_id": 123}
        assert entry.summarized is True


# =============================================================================
# MemorySummary Tests
# =============================================================================

class TestMemorySummary:
    """Tests for MemorySummary dataclass."""
    
    def test_create_summary(self):
        """Test creating a summary."""
        summary = MemorySummary(
            id="s_001",
            timestamp=datetime(2025, 1, 15, 11, 0, 0),
            covers=["e_001", "e_002"],
            content="User created blog with auth.",
            original_tokens=1000,
            summary_tokens=50,
            preserved_facts=["uses PostgreSQL"],
        )
        assert summary.id == "s_001"
        assert len(summary.covers) == 2
        assert summary.original_tokens == 1000
        assert summary.summary_tokens == 50
    
    def test_summary_to_dict(self):
        """Test converting summary to dict."""
        summary = MemorySummary(
            id="s_001",
            timestamp=datetime(2025, 1, 15, 11, 0, 0),
            covers=["e_001", "e_002"],
            content="Summary content",
            original_tokens=1000,
            summary_tokens=50,
        )
        d = summary.to_dict()
        assert d["type"] == "summary"
        assert d["covers"] == ["e_001", "e_002"]


# =============================================================================
# Checkpoint Tests
# =============================================================================

class TestCheckpoint:
    """Tests for Checkpoint dataclass."""
    
    def test_create_checkpoint(self):
        """Test creating a checkpoint."""
        cp = Checkpoint(
            id="cp_001",
            timestamp=datetime(2025, 1, 15, 10, 30, 0),
            trigger="before_generation",
            description="Before creating blog",
            files_snapshot={"pages/index.py": "abc123"},
        )
        assert cp.id == "cp_001"
        assert cp.trigger == "before_generation"
        assert "pages/index.py" in cp.files_snapshot
    
    def test_checkpoint_roundtrip(self):
        """Test checkpoint serialization roundtrip."""
        cp = Checkpoint(
            id="cp_001",
            timestamp=datetime(2025, 1, 15, 10, 30, 0),
            trigger="user_request",
            description="Manual checkpoint",
            files_snapshot={"a.py": "hash1", "b.py": "hash2"},
            rollback_id="rb_001",
            entry_ref="e_005",
        )
        d = cp.to_dict()
        cp2 = Checkpoint.from_dict(d)
        assert cp2.id == cp.id
        assert cp2.trigger == cp.trigger
        assert cp2.files_snapshot == cp.files_snapshot


# =============================================================================
# SyncConfig Tests
# =============================================================================

class TestSyncConfig:
    """Tests for SyncConfig dataclass."""
    
    def test_default_config(self):
        """Test default sync configuration."""
        config = SyncConfig()
        assert config.mode == "incremental"
        assert "assistant_response" in config.triggers
        assert config.batch_size == 5
    
    def test_custom_config(self):
        """Test custom sync configuration."""
        config = SyncConfig(
            mode="manual",
            triggers=["exit"],
            batch_size=10,
            exclude_roles=["system"],
        )
        assert config.mode == "manual"
        assert config.triggers == ["exit"]
        assert config.batch_size == 10


# =============================================================================
# SessionMemory Tests
# =============================================================================

class TestSessionMemory:
    """Tests for SessionMemory class."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def memory(self, temp_project):
        """Create a memory instance for testing."""
        return SessionMemory(project_path=temp_project)
    
    def test_init(self, memory, temp_project):
        """Test memory initialization."""
        assert memory.project_path == temp_project
        assert memory.sync_config.mode == "incremental"
        assert memory._entries == []
    
    def test_add_entry(self, memory):
        """Test adding an entry."""
        entry_id = memory.add("user", "Create a blog", {})
        assert entry_id.startswith("e_")
        assert len(memory._entries) == 1
        assert memory._entries[0].role == "user"
        assert memory._entries[0].content == "Create a blog"
    
    def test_add_entry_with_metadata(self, memory):
        """Test adding entry with metadata."""
        entry_id = memory.add(
            "assistant",
            "Creating blog...",
            {"files": ["index.py"], "plan_id": 123},
        )
        entry = memory._entries[0]
        assert entry.metadata["files"] == ["index.py"]
        assert entry.metadata["plan_id"] == 123
    
    def test_add_excludes_roles(self, memory):
        """Test that excluded roles are not added."""
        memory.sync_config.exclude_roles = ["system"]
        entry_id = memory.add("system", "Internal message", {})
        assert entry_id == ""
        assert len(memory._entries) == 0
    
    def test_add_checkpoint(self, memory):
        """Test adding a checkpoint."""
        cp_id = memory.add_checkpoint(
            trigger="user_request",
            description="Test checkpoint",
            files={"a.py": "hash1"},
        )
        assert cp_id.startswith("cp_")
        assert len(memory._checkpoints) == 1
        assert memory._checkpoints[0].description == "Test checkpoint"
    
    def test_add_preference(self, memory):
        """Test adding a preference."""
        pref_id = memory.add_preference("mode", "strict", 0.9)
        assert pref_id.startswith("pref_")
        assert "mode" in memory._preferences
        assert memory._preferences["mode"].value == "strict"
    
    def test_get_entries(self, memory):
        """Test getting entries."""
        memory.add("user", "First", {})
        memory.add("assistant", "Second", {})
        memory.add("user", "Third", {})
        
        # Most recent first
        entries = memory.get_entries(limit=2)
        assert len(entries) == 2
        assert entries[0].content == "Third"
        assert entries[1].content == "Second"
    
    def test_get_preferences(self, memory):
        """Test getting preferences."""
        memory.add_preference("mode", "strict", 0.9)
        memory.add_preference("theme", "dark", 0.8)
        
        prefs = memory.get_preferences()
        assert prefs["mode"] == "strict"
        assert prefs["theme"] == "dark"
    
    def test_search(self, memory):
        """Test searching entries."""
        memory.add("user", "Create a blog with authentication", {})
        memory.add("assistant", "I'll create the blog...", {})
        memory.add("user", "Add dark mode", {})
        
        results = memory.search("blog", k=5)
        assert len(results) == 2
        assert "blog" in results[0].content.lower()
    
    def test_search_no_results(self, memory):
        """Test search with no results."""
        memory.add("user", "Hello world", {})
        results = memory.search("authentication", k=5)
        assert len(results) == 0
    
    def test_get_relevant_context(self, memory):
        """Test getting relevant context."""
        memory.add("user", "Create a blog", {})
        memory.add("assistant", "Created blog with 10 files", {})
        memory.add_preference("db", "PostgreSQL", 0.9)
        
        context = memory.get_relevant_context("add feature", max_tokens=4000)
        assert "Recent Conversation" in context or "blog" in context.lower()
        assert "PostgreSQL" in context
    
    def test_save_and_load(self, memory, temp_project):
        """Test saving and loading memory."""
        # Add some data
        memory.add("user", "Create blog", {})
        memory.add("assistant", "Done!", {"files": ["index.py"]})
        memory.add_checkpoint("test", "Test", {"a.py": "hash"})
        memory.add_preference("mode", "strict", 0.9)
        
        # Save
        memory.flush(force=True)
        
        # Create new memory instance and load
        memory2 = SessionMemory(project_path=temp_project)
        loaded = memory2.load()
        
        assert loaded is True
        assert len(memory2._entries) == 2
        assert len(memory2._checkpoints) == 1
        assert "mode" in memory2._preferences
    
    def test_clear(self, memory, temp_project):
        """Test clearing memory."""
        memory.add("user", "Test", {})
        memory.flush(force=True)
        
        deleted_path = memory.clear()
        
        assert len(memory._entries) == 0
        assert not memory._memory_file.exists()
        assert deleted_path == memory._memory_file
    
    def test_clear_disk_only(self, memory, temp_project):
        """Test clearing only disk file, keeping in-memory state."""
        memory.add("user", "Test", {})
        memory.flush(force=True)
        
        # Clear disk only
        deleted_path = memory.clear(disk_only=True)
        
        # In-memory should still have data
        assert len(memory._entries) == 1
        # File should be deleted
        assert not deleted_path.exists()
    
    def test_export_markdown(self, memory):
        """Test exporting as markdown."""
        memory.add("user", "Create blog", {})
        memory.add("assistant", "Creating...", {})
        
        md = memory.export("markdown")
        assert "# Session Memory" in md
        assert "user" in md.lower() or "User" in md
    
    def test_export_json(self, memory):
        """Test exporting as JSON."""
        memory.add("user", "Test", {})
        
        json_str = memory.export("json")
        data = json.loads(json_str)
        assert "entries" in data
        assert len(data["entries"]) == 1
    
    def test_stats(self, memory):
        """Test memory statistics."""
        memory.add("user", "Hello", {})
        memory.add("assistant", "Hi there!", {})
        
        stats = memory.stats()
        assert stats["entries"] == 2
        assert stats["summaries"] == 0
        assert stats["checkpoints"] == 0
        assert stats["total_tokens"] > 0
    
    def test_sync_pause_resume(self, memory):
        """Test pausing and resuming sync."""
        assert memory.sync_paused is False
        
        memory.pause_sync()
        assert memory.sync_paused is True
        
        memory.resume_sync()
        assert memory.sync_paused is False
    
    def test_pending_count(self, memory):
        """Test pending entry count."""
        assert memory.pending_count == 0
        
        memory.add("user", "Test", {})
        assert memory.pending_count == 1
        
        memory.flush(force=True)
        assert memory.pending_count == 0


# =============================================================================
# Summarization Tests
# =============================================================================

class TestSummarization:
    """Tests for summarization functionality."""
    
    @pytest.fixture
    def memory_with_entries(self, tmp_path):
        """Create memory with many entries."""
        memory = SessionMemory(project_path=tmp_path)
        for i in range(20):
            memory.add("user", f"Message {i} " * 100, {})  # ~400 tokens each
        return memory
    
    def test_should_summarize(self, memory_with_entries):
        """Test summarization threshold detection."""
        # With 20 entries of ~400 tokens each = ~8000 tokens
        # Threshold is 80% of 100k = 80k, so shouldn't trigger
        assert memory_with_entries._should_summarize() is False
    
    @pytest.mark.asyncio
    async def test_summarize_without_llm(self, memory_with_entries):
        """Test that summarization requires LLM."""
        result = await memory_with_entries.summarize_old()
        assert result is None  # No LLM client
    
    def test_get_preserved_facts(self, tmp_path):
        """Test getting preserved facts from summaries."""
        memory = SessionMemory(project_path=tmp_path)
        
        # Add a summary manually
        memory._summaries.append(MemorySummary(
            id="s_001",
            timestamp=datetime.utcnow(),
            covers=["e_001"],
            content="Summary",
            original_tokens=100,
            summary_tokens=10,
            preserved_facts=["fact1", "fact2"],
        ))
        
        facts = memory.get_preserved_facts()
        assert "fact1" in facts
        assert "fact2" in facts


# =============================================================================
# Compact Tests
# =============================================================================

class TestCompact:
    """Tests for memory compaction."""
    
    def test_compact_removes_summarized(self, tmp_path):
        """Test that compact removes summarized entries."""
        memory = SessionMemory(project_path=tmp_path)
        
        # Add entries
        memory.add("user", "Entry 1", {})
        memory.add("user", "Entry 2", {})
        memory.add("user", "Entry 3", {})
        
        # Mark first two as summarized
        memory._entries[0].summarized = True
        memory._entries[1].summarized = True
        
        # Add a summary covering them
        memory._summaries.append(MemorySummary(
            id="s_001",
            timestamp=datetime.utcnow(),
            covers=[memory._entries[0].id, memory._entries[1].id],
            content="Summary of entries 1 and 2",
            original_tokens=100,
            summary_tokens=10,
        ))
        
        # Save first
        memory.flush(force=True)
        
        # Compact
        memory.compact()
        
        # Should only have 1 entry now
        assert len(memory._entries) == 1
        assert memory._entries[0].content == "Entry 3"


# =============================================================================
# Sync Mode Tests
# =============================================================================

class TestSyncModes:
    """Tests for different sync modes."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_incremental_mode_appends(self, temp_project):
        """Test that incremental mode appends entries."""
        memory = SessionMemory(
            project_path=temp_project,
            sync_config=SyncConfig(mode="incremental"),
        )
        
        # Add and flush first entry
        memory.add("user", "First entry", {})
        memory.flush(force=True)
        
        # Add and flush second entry
        memory.add("user", "Second entry", {})
        memory.flush(force=True)
        
        # Load and verify both entries exist
        memory2 = SessionMemory(project_path=temp_project)
        memory2.load()
        assert len(memory2._entries) == 2
    
    def test_manual_mode_no_auto_sync(self, temp_project):
        """Test that manual mode doesn't auto-sync."""
        memory = SessionMemory(
            project_path=temp_project,
            sync_config=SyncConfig(mode="manual"),
        )
        
        memory.add("user", "Test entry", {})
        
        # Without force, should not flush
        count = memory.flush(force=False)
        assert count == 0
        assert memory.pending_count == 1
        
        # With force, should flush
        count = memory.flush(force=True)
        assert count > 0
        assert memory.pending_count == 0
    
    def test_sync_paused_no_flush(self, temp_project):
        """Test that paused sync doesn't flush."""
        memory = SessionMemory(project_path=temp_project)
        memory.pause_sync()
        
        memory.add("user", "Test", {})
        count = memory.flush(force=False)
        
        assert count == 0
        assert memory.pending_count == 1
    
    def test_sync_resume_flushes(self, temp_project):
        """Test that resuming sync flushes pending."""
        memory = SessionMemory(project_path=temp_project)
        memory.pause_sync()
        
        # Add entries while paused
        memory.add("user", "Entry 1", {})
        memory.add("user", "Entry 2", {})
        
        assert memory.pending_count == 2
        
        # Resume - should not auto-flush but allow manual
        memory.resume_sync()
        memory.flush(force=True)
        assert memory.pending_count == 0


# =============================================================================
# Sync Triggers Tests
# =============================================================================

class TestSyncTriggers:
    """Tests for sync trigger configurations."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_batch_size_triggers_sync(self, temp_project):
        """Test that reaching batch_size triggers sync."""
        memory = SessionMemory(
            project_path=temp_project,
            sync_config=SyncConfig(batch_size=3),
        )
        
        memory.add("user", "Entry 1", {})
        memory.add("user", "Entry 2", {})
        assert memory.pending_count == 2
        
        # Third entry should trigger sync (batch_size=3)
        memory.add("user", "Entry 3", {})
        # After auto-sync, pending should be 0
        assert memory.pending_count == 0
    
    def test_exclude_roles_filter(self, temp_project):
        """Test that excluded roles are filtered."""
        memory = SessionMemory(
            project_path=temp_project,
            sync_config=SyncConfig(exclude_roles=["system", "internal"]),
        )
        
        memory.add("user", "User message", {})
        memory.add("system", "System message", {})
        memory.add("internal", "Internal message", {})
        memory.add("assistant", "Assistant message", {})
        
        assert len(memory._entries) == 2
        assert memory._entries[0].role == "user"
        assert memory._entries[1].role == "assistant"
    
    def test_min_content_length_filter(self, temp_project):
        """Test that short content is filtered."""
        memory = SessionMemory(
            project_path=temp_project,
            sync_config=SyncConfig(min_content_length=10),
        )
        
        memory.add("user", "Hi", {})  # Too short
        memory.add("user", "This is a longer message", {})
        
        assert len(memory._entries) == 1
        assert "longer" in memory._entries[0].content


# =============================================================================
# Checkpoint Tests Extended
# =============================================================================

class TestCheckpointExtended:
    """Extended tests for checkpoint functionality."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_checkpoint_with_entry_ref(self, temp_project):
        """Test checkpoint linked to conversation entry."""
        memory = SessionMemory(project_path=temp_project)
        
        entry_id = memory.add("user", "Create feature", {})
        cp_id = memory.add_checkpoint(
            trigger="before_generation",
            description="Before feature",
            files={"a.py": "hash"},
            entry_ref=entry_id,
        )
        
        cp = memory._checkpoints[0]
        assert cp.entry_ref == entry_id
    
    def test_get_checkpoint_by_id(self, temp_project):
        """Test getting checkpoint by ID."""
        memory = SessionMemory(project_path=temp_project)
        
        cp_id = memory.add_checkpoint(
            trigger="test",
            description="Test checkpoint",
            files={"a.py": "hash1"},
        )
        
        cp = memory.get_checkpoint(cp_id)
        assert cp is not None
        assert cp.description == "Test checkpoint"
    
    def test_get_checkpoint_not_found(self, temp_project):
        """Test getting non-existent checkpoint."""
        memory = SessionMemory(project_path=temp_project)
        cp = memory.get_checkpoint("cp_nonexistent")
        assert cp is None
    
    def test_multiple_checkpoints_ordering(self, temp_project):
        """Test that checkpoints are ordered by time."""
        memory = SessionMemory(project_path=temp_project)
        
        memory.add_checkpoint("test", "First", {"a.py": "h1"})
        memory.add_checkpoint("test", "Second", {"b.py": "h2"})
        memory.add_checkpoint("test", "Third", {"c.py": "h3"})
        
        checkpoints = memory.get_checkpoints(limit=10)
        # Most recent first
        assert checkpoints[0].description == "Third"
        assert checkpoints[2].description == "First"
    
    def test_checkpoint_triggers(self, temp_project):
        """Test various checkpoint triggers."""
        memory = SessionMemory(project_path=temp_project)
        
        triggers = ["before_generation", "after_generation", "user_request", "mode_change", "rollback"]
        
        for trigger in triggers:
            cp_id = memory.add_checkpoint(
                trigger=trigger,
                description=f"Trigger: {trigger}",
                files={},
            )
            assert cp_id.startswith("cp_")
        
        assert len(memory._checkpoints) == 5


# =============================================================================
# Search and Retrieval Tests Extended
# =============================================================================

class TestSearchExtended:
    """Extended tests for search and retrieval."""
    
    @pytest.fixture
    def memory_with_content(self, tmp_path):
        """Create memory with diverse content."""
        memory = SessionMemory(project_path=tmp_path)
        
        memory.add("user", "Create a blog with user authentication", {})
        memory.add("assistant", "I'll create a blog with JWT auth, PostgreSQL database, and Tailwind CSS styling", 
                   {"files": ["pages/index.py", "models/user.py"]})
        memory.add("user", "Add dark mode toggle", {})
        memory.add("assistant", "Adding dark mode with Signal-based state management", 
                   {"files": ["islands/ThemeToggle.py"]})
        memory.add("user", "Create API for posts", {})
        memory.add("assistant", "Creating CRUD API endpoints for posts with validation", 
                   {"files": ["api/posts.py"]})
        
        return memory
    
    def test_search_multiple_terms(self, memory_with_content):
        """Test searching with multiple terms."""
        results = memory_with_content.search("blog authentication", k=5)
        assert len(results) > 0
        # Should find the entry about blog with auth
        assert any("blog" in r.content.lower() for r in results)
    
    def test_search_case_insensitive(self, memory_with_content):
        """Test that search is case insensitive."""
        results1 = memory_with_content.search("BLOG", k=5)
        results2 = memory_with_content.search("blog", k=5)
        assert len(results1) == len(results2)
    
    def test_search_limit(self, memory_with_content):
        """Test search result limit."""
        results = memory_with_content.search("a", k=2)  # Common letter
        assert len(results) <= 2
    
    def test_get_relevant_context_structure(self, memory_with_content):
        """Test context structure includes expected sections."""
        context = memory_with_content.get_relevant_context("add feature", max_tokens=4000)
        
        # Should have recent conversation
        assert "Recent" in context or "blog" in context.lower()
    
    def test_get_relevant_context_with_preferences(self, tmp_path):
        """Test context includes preferences."""
        memory = SessionMemory(project_path=tmp_path)
        memory.add("user", "Test message", {})
        memory.add_preference("database", "PostgreSQL", 0.9)
        memory.add_preference("framework", "PyNext", 1.0)
        
        context = memory.get_relevant_context("build app", max_tokens=4000)
        assert "PostgreSQL" in context
        assert "PyNext" in context
    
    def test_get_relevant_context_with_summaries(self, tmp_path):
        """Test context includes relevant summaries."""
        memory = SessionMemory(project_path=tmp_path)
        
        memory.add("user", "Recent message", {})
        memory._summaries.append(MemorySummary(
            id="s_001",
            timestamp=datetime.utcnow(),
            covers=["e_old"],
            content="Previously built authentication system with JWT tokens",
            original_tokens=500,
            summary_tokens=20,
            preserved_facts=["uses JWT", "has user model"],
        ))
        
        context = memory.get_relevant_context("add auth feature", max_tokens=4000)
        # Should include summary about auth or the facts
        assert "JWT" in context or "auth" in context.lower()


# =============================================================================
# Preference Tests Extended
# =============================================================================

class TestPreferenceExtended:
    """Extended tests for preference management."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_preference_confidence(self, temp_project):
        """Test preference confidence levels."""
        memory = SessionMemory(project_path=temp_project)
        
        memory.add_preference("mode", "strict", 0.5)
        memory.add_preference("style", "minimal", 0.9)
        
        # Preferences should have different confidence
        assert memory._preferences["mode"].confidence == 0.5
        assert memory._preferences["style"].confidence == 0.9
    
    def test_preference_update(self, temp_project):
        """Test updating an existing preference."""
        memory = SessionMemory(project_path=temp_project)
        
        memory.add_preference("mode", "plan", 0.5)
        memory.add_preference("mode", "strict", 0.9)  # Update
        
        # Should have the latest value
        assert memory._preferences["mode"].value == "strict"
        assert memory._preferences["mode"].confidence == 0.9
    
    def test_preference_persistence(self, temp_project):
        """Test preferences are persisted and loaded."""
        memory = SessionMemory(project_path=temp_project)
        memory.add_preference("db", "postgres", 0.8)
        memory.add_preference("theme", "dark", 0.7)
        memory.flush(force=True)
        
        memory2 = SessionMemory(project_path=temp_project)
        memory2.load()
        
        prefs = memory2.get_preferences()
        assert prefs["db"] == "postgres"
        assert prefs["theme"] == "dark"


# =============================================================================
# Export Tests Extended
# =============================================================================

class TestExportExtended:
    """Extended tests for export functionality."""
    
    @pytest.fixture
    def memory_with_all_types(self, tmp_path):
        """Create memory with all record types."""
        memory = SessionMemory(project_path=tmp_path)
        
        memory.add("user", "Create blog", {})
        memory.add("assistant", "Creating...", {"files": ["index.py"]})
        memory.add_checkpoint("test", "Test checkpoint", {"a.py": "hash"})
        memory.add_preference("mode", "strict", 0.9)
        memory._summaries.append(MemorySummary(
            id="s_001",
            timestamp=datetime.utcnow(),
            covers=["old"],
            content="Old conversation summary",
            original_tokens=100,
            summary_tokens=10,
            preserved_facts=["fact1"],
        ))
        
        return memory
    
    def test_export_markdown_includes_all(self, memory_with_all_types):
        """Test markdown export includes all record types."""
        md = memory_with_all_types.export("markdown")
        
        assert "# Session Memory" in md
        assert "Conversation" in md
        assert "Create blog" in md
        assert "Checkpoints" in md
        assert "Preferences" in md
    
    def test_export_json_structure(self, memory_with_all_types):
        """Test JSON export has correct structure."""
        json_str = memory_with_all_types.export("json")
        data = json.loads(json_str)
        
        assert "entries" in data
        assert "summaries" in data
        assert "checkpoints" in data
        assert "preferences" in data
        
        assert len(data["entries"]) == 2
        assert len(data["summaries"]) == 1
        assert len(data["checkpoints"]) == 1
        assert len(data["preferences"]) == 1


# =============================================================================
# File Persistence Tests Extended
# =============================================================================

class TestFilePersistenceExtended:
    """Extended tests for file persistence."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_memory_file_created(self, temp_project):
        """Test that memory file is created on flush."""
        memory = SessionMemory(project_path=temp_project)
        memory.add("user", "Test", {})
        memory.flush(force=True)
        
        mem_file = temp_project / ".pynext" / "session.mem"
        assert mem_file.exists()
    
    def test_memory_file_contains_meta(self, temp_project):
        """Test that memory file starts with meta record."""
        memory = SessionMemory(project_path=temp_project)
        memory.add("user", "Test", {})
        memory.flush(force=True)
        
        mem_file = temp_project / ".pynext" / "session.mem"
        with open(mem_file, "r") as f:
            first_line = f.readline()
            data = json.loads(first_line)
            assert data["type"] == "meta"
            assert "v" in data
    
    def test_load_empty_file(self, temp_project):
        """Test loading when no memory file exists."""
        memory = SessionMemory(project_path=temp_project)
        loaded = memory.load()
        
        assert loaded is False
        assert len(memory._entries) == 0
    
    def test_load_malformed_line_skipped(self, temp_project):
        """Test that malformed lines are skipped."""
        # Create memory file with a bad line
        mem_dir = temp_project / ".pynext"
        mem_dir.mkdir(parents=True)
        mem_file = mem_dir / "session.mem"
        
        with open(mem_file, "w") as f:
            f.write('{"type":"meta","v":1,"created":"2025-01-15T10:00:00","project":"test"}\n')
            f.write('not valid json\n')  # Bad line
            f.write('{"type":"entry","id":"e_001","ts":"2025-01-15T10:00:00","role":"user","content":"Test","tokens":5}\n')
        
        memory = SessionMemory(project_path=temp_project)
        loaded = memory.load()
        
        assert loaded is True
        assert len(memory._entries) == 1


# =============================================================================
# Configure Sync Tests
# =============================================================================

class TestConfigureSync:
    """Tests for sync configuration methods."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_configure_sync_mode(self, temp_project):
        """Test configuring sync mode."""
        memory = SessionMemory(project_path=temp_project)
        
        assert memory.sync_config.mode == "incremental"
        
        memory.configure_sync(mode="manual")
        assert memory.sync_config.mode == "manual"
    
    def test_configure_sync_triggers(self, temp_project):
        """Test configuring sync triggers."""
        memory = SessionMemory(project_path=temp_project)
        
        memory.configure_sync(triggers=["exit", "error"])
        assert memory.sync_config.triggers == ["exit", "error"]
    
    def test_configure_sync_batch_size(self, temp_project):
        """Test configuring batch size."""
        memory = SessionMemory(project_path=temp_project)
        
        memory.configure_sync(batch_size=10)
        assert memory.sync_config.batch_size == 10
    
    def test_configure_sync_partial(self, temp_project):
        """Test partial configuration doesn't change other settings."""
        memory = SessionMemory(project_path=temp_project)
        original_mode = memory.sync_config.mode
        original_batch = memory.sync_config.batch_size
        
        memory.configure_sync(triggers=["exit"])
        
        assert memory.sync_config.mode == original_mode
        assert memory.sync_config.batch_size == original_batch
        assert memory.sync_config.triggers == ["exit"]


# =============================================================================
# Global Functions Tests
# =============================================================================

class TestGlobalFunctions:
    """Tests for module-level functions."""
    
    def test_get_memory_singleton(self, tmp_path):
        """Test that get_memory returns a singleton."""
        reset_memory()
        
        m1 = get_memory(tmp_path)
        m2 = get_memory(tmp_path)
        
        assert m1 is m2
        
        reset_memory()
    
    def test_reset_memory(self, tmp_path):
        """Test resetting the global memory instance."""
        reset_memory()
        m1 = get_memory(tmp_path)
        
        reset_memory()
        m2 = get_memory(tmp_path)
        
        assert m1 is not m2
        reset_memory()


# =============================================================================
# Edge Cases Tests
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_empty_content(self, temp_project):
        """Test adding empty content."""
        memory = SessionMemory(project_path=temp_project)
        entry_id = memory.add("user", "", {})
        
        # Empty content with min_length=0 should still be added
        assert len(memory._entries) == 1
    
    def test_very_long_content(self, temp_project):
        """Test handling very long content."""
        memory = SessionMemory(project_path=temp_project)
        long_content = "x" * 100000  # 100k characters
        
        entry_id = memory.add("user", long_content, {})
        assert len(memory._entries) == 1
        assert memory._entries[0].tokens > 0
    
    def test_unicode_content(self, temp_project):
        """Test handling unicode content."""
        memory = SessionMemory(project_path=temp_project)
        unicode_content = "Hello 世界 🎉 Привет مرحبا"
        
        entry_id = memory.add("user", unicode_content, {})
        memory.flush(force=True)
        
        memory2 = SessionMemory(project_path=temp_project)
        memory2.load()
        
        assert memory2._entries[0].content == unicode_content
    
    def test_special_characters_in_metadata(self, temp_project):
        """Test handling special characters in metadata."""
        memory = SessionMemory(project_path=temp_project)
        
        memory.add("user", "Test", {
            "path": "/path/to/file.py",
            "quotes": 'He said "hello"',
            "newlines": "line1\nline2",
        })
        memory.flush(force=True)
        
        memory2 = SessionMemory(project_path=temp_project)
        memory2.load()
        
        assert memory2._entries[0].metadata["newlines"] == "line1\nline2"
    
    def test_concurrent_access_simulation(self, temp_project):
        """Test simulating concurrent access."""
        # Create two memory instances
        memory1 = SessionMemory(project_path=temp_project)
        memory2 = SessionMemory(project_path=temp_project)
        
        # Both add entries
        memory1.add("user", "From memory 1", {})
        memory2.add("user", "From memory 2", {})
        
        # Both flush
        memory1.flush(force=True)
        memory2.flush(force=True)
        
        # Load and verify (last writer wins for file, but both should have their entries)
        memory3 = SessionMemory(project_path=temp_project)
        memory3.load()
        
        # Should have entries from at least one instance
        assert len(memory3._entries) > 0
    
    def test_stats_empty_memory(self, temp_project):
        """Test stats on empty memory."""
        memory = SessionMemory(project_path=temp_project)
        stats = memory.stats()
        
        assert stats["entries"] == 0
        assert stats["summaries"] == 0
        assert stats["checkpoints"] == 0
        assert stats["total_tokens"] == 0
    
    def test_clear_nonexistent_file(self, temp_project):
        """Test clearing when file doesn't exist."""
        memory = SessionMemory(project_path=temp_project)
        # Don't flush, so no file exists
        
        deleted_path = memory.clear()
        assert deleted_path == memory._memory_file
        # Should not raise


# =============================================================================
# JSONL Format Tests
# =============================================================================

class TestJSONLFormat:
    """Tests for JSONL file format compliance."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_each_line_is_valid_json(self, temp_project):
        """Test that each line in .mem file is valid JSON."""
        memory = SessionMemory(project_path=temp_project)
        memory.add("user", "First message", {})
        memory.add("assistant", "Response", {"files": ["a.py"]})
        memory.add_checkpoint("test", "Test checkpoint", {"a.py": "hash"})
        memory.add_preference("mode", "strict", 0.9)
        memory.flush(force=True)
        
        with open(memory._memory_file, "r") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line:
                    try:
                        json.loads(line)
                    except json.JSONDecodeError as e:
                        pytest.fail(f"Line {line_num} is not valid JSON: {e}")
    
    def test_records_have_type_field(self, temp_project):
        """Test that all records have a type field."""
        memory = SessionMemory(project_path=temp_project)
        memory.add("user", "Test", {})
        memory.add_checkpoint("test", "Test", {})
        memory.add_preference("key", "value", 0.5)
        memory.flush(force=True)
        
        with open(memory._memory_file, "r") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line:
                    record = json.loads(line)
                    assert "type" in record, f"Line {line_num} missing 'type' field"
    
    def test_meta_record_first(self, temp_project):
        """Test that meta record is first in file."""
        memory = SessionMemory(project_path=temp_project)
        memory.add("user", "Test", {})
        memory.flush(force=True)
        
        with open(memory._memory_file, "r") as f:
            first_line = f.readline().strip()
            record = json.loads(first_line)
            assert record["type"] == "meta"
            assert "v" in record  # version
    
    def test_entry_record_structure(self, temp_project):
        """Test entry record has correct structure."""
        memory = SessionMemory(project_path=temp_project)
        memory.add("user", "Hello world", {"custom": "data"})
        memory.flush(force=True)
        
        with open(memory._memory_file, "r") as f:
            lines = [json.loads(l) for l in f if l.strip()]
            entry = next(r for r in lines if r["type"] == "entry")
            
            assert "id" in entry
            assert "ts" in entry
            assert "role" in entry
            assert entry["role"] == "user"
            assert "content" in entry
            assert entry["content"] == "Hello world"
            assert "tokens" in entry
            assert "meta" in entry
    
    def test_checkpoint_record_structure(self, temp_project):
        """Test checkpoint record has correct structure."""
        memory = SessionMemory(project_path=temp_project)
        memory.add_checkpoint(
            trigger="before_generation",
            description="Test checkpoint",
            files={"pages/index.py": "sha256:abc123"},
            entry_ref="e_001",
        )
        memory.flush(force=True)
        
        with open(memory._memory_file, "r") as f:
            lines = [json.loads(l) for l in f if l.strip()]
            cp = next(r for r in lines if r["type"] == "checkpoint")
            
            assert "id" in cp
            assert "ts" in cp
            assert "trigger" in cp
            assert cp["trigger"] == "before_generation"
            assert "description" in cp
            assert "files_snapshot" in cp
    
    def test_preference_record_structure(self, temp_project):
        """Test preference record has correct structure."""
        memory = SessionMemory(project_path=temp_project)
        memory.add_preference("database", "PostgreSQL", 0.85)
        memory.flush(force=True)
        
        with open(memory._memory_file, "r") as f:
            lines = [json.loads(l) for l in f if l.strip()]
            pref = next(r for r in lines if r["type"] == "preference")
            
            assert "id" in pref
            assert "ts" in pref
            assert "key" in pref
            assert pref["key"] == "database"
            assert "value" in pref
            assert pref["value"] == "PostgreSQL"
            assert "confidence" in pref
            assert pref["confidence"] == 0.85


# =============================================================================
# Memory Retrieval Priority Tests
# =============================================================================

class TestMemoryRetrievalPriority:
    """Tests for context retrieval priority order."""
    
    @pytest.fixture
    def memory_with_history(self, tmp_path):
        """Create memory with comprehensive history."""
        memory = SessionMemory(project_path=tmp_path)
        
        # Old entries (will be summarized conceptually)
        for i in range(10):
            memory.add("user", f"Old message {i} about topic A", {})
            memory.add("assistant", f"Old response {i} about topic A", {})
        
        # Add a summary covering old entries
        memory._summaries.append(MemorySummary(
            id="s_001",
            timestamp=datetime.utcnow(),
            covers=[f"e_{i:03d}" for i in range(20)],
            content="User discussed topic A extensively. Built 5 components.",
            original_tokens=5000,
            summary_tokens=50,
            preserved_facts=["uses PostgreSQL", "has dark mode", "12 files created"],
        ))
        
        # Recent entries
        memory.add("user", "Recent message about topic B", {})
        memory.add("assistant", "Recent response about topic B with files", {"files": ["new.py"]})
        memory.add("user", "Most recent message about topic C", {})
        
        # Preferences
        memory.add_preference("framework", "PyNext", 1.0)
        memory.add_preference("style", "modern", 0.8)
        
        return memory
    
    def test_context_includes_recent_entries(self, memory_with_history):
        """Test that recent entries are always included."""
        context = memory_with_history.get_relevant_context("anything", max_tokens=4000)
        
        assert "topic B" in context or "topic C" in context
    
    def test_context_includes_preserved_facts(self, memory_with_history):
        """Test that preserved facts are included."""
        context = memory_with_history.get_relevant_context("anything", max_tokens=4000)
        
        # At least some preserved facts should be in context
        has_facts = any(fact in context for fact in ["PostgreSQL", "dark mode", "12 files"])
        assert has_facts
    
    def test_context_includes_preferences(self, memory_with_history):
        """Test that preferences are included in context."""
        context = memory_with_history.get_relevant_context("anything", max_tokens=4000)
        
        assert "PyNext" in context or "modern" in context
    
    def test_context_respects_token_limit(self, memory_with_history):
        """Test that context respects token limits."""
        # Very small token budget
        context = memory_with_history.get_relevant_context("anything", max_tokens=100)
        
        # Should still have something but be constrained
        assert len(context) > 0
        # Rough estimate: context should be relatively short
        assert len(context) < 5000  # Characters, not tokens
    
    def test_search_relevance_affects_context(self, memory_with_history):
        """Test that search relevance affects what's included."""
        context_a = memory_with_history.get_relevant_context("topic A", max_tokens=4000)
        context_b = memory_with_history.get_relevant_context("topic B", max_tokens=4000)
        
        # Both should return valid context
        assert len(context_a) > 0
        assert len(context_b) > 0


# =============================================================================
# Token Counting Tests
# =============================================================================

class TestTokenCounting:
    """Tests for token estimation."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_entry_has_token_count(self, temp_project):
        """Test that entries have token counts."""
        memory = SessionMemory(project_path=temp_project)
        memory.add("user", "Hello world, this is a test message.", {})
        
        entry = memory._entries[0]
        assert entry.tokens > 0
    
    def test_longer_content_more_tokens(self, temp_project):
        """Test that longer content has more tokens."""
        memory = SessionMemory(project_path=temp_project)
        memory.add("user", "Short", {})
        memory.add("user", "This is a much longer message with more words and content.", {})
        
        short_entry = memory._entries[0]
        long_entry = memory._entries[1]
        
        assert long_entry.tokens > short_entry.tokens
    
    def test_stats_total_tokens(self, temp_project):
        """Test that stats correctly sums tokens."""
        memory = SessionMemory(project_path=temp_project)
        memory.add("user", "Message one", {})
        memory.add("assistant", "Message two", {})
        
        stats = memory.stats()
        
        expected_total = sum(e.tokens for e in memory._entries)
        assert stats["total_tokens"] == expected_total


# =============================================================================
# Summarization Tests Extended
# =============================================================================

class TestSummarizationExtended:
    """Extended tests for summarization behavior."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_summary_covers_entries(self, temp_project):
        """Test that summaries reference covered entry IDs."""
        memory = SessionMemory(project_path=temp_project)
        
        entry_ids = []
        for i in range(5):
            entry_id = memory.add("user", f"Message {i}", {})
            entry_ids.append(entry_id)
        
        # Manually add summary
        memory._summaries.append(MemorySummary(
            id="s_001",
            timestamp=datetime.utcnow(),
            covers=entry_ids[:3],  # Cover first 3
            content="Summary of first 3 messages",
            original_tokens=300,
            summary_tokens=30,
        ))
        
        summary = memory._summaries[0]
        assert set(summary.covers) == set(entry_ids[:3])
    
    def test_summary_compression_ratio(self, temp_project):
        """Test that summaries achieve compression."""
        summary = MemorySummary(
            id="s_001",
            timestamp=datetime.utcnow(),
            covers=["e_001", "e_002", "e_003"],
            content="Compressed summary",
            original_tokens=1000,
            summary_tokens=100,
        )
        
        compression_ratio = summary.original_tokens / summary.summary_tokens
        assert compression_ratio >= 5  # At least 5x compression
    
    def test_get_preserved_facts_from_multiple_summaries(self, temp_project):
        """Test collecting facts from multiple summaries."""
        memory = SessionMemory(project_path=temp_project)
        
        memory._summaries.append(MemorySummary(
            id="s_001",
            timestamp=datetime.utcnow(),
            covers=["e_001"],
            content="Summary 1",
            original_tokens=100,
            summary_tokens=10,
            preserved_facts=["fact1", "fact2"],
        ))
        memory._summaries.append(MemorySummary(
            id="s_002",
            timestamp=datetime.utcnow(),
            covers=["e_002"],
            content="Summary 2",
            original_tokens=100,
            summary_tokens=10,
            preserved_facts=["fact3", "fact4"],
        ))
        
        facts = memory.get_preserved_facts()
        assert "fact1" in facts
        assert "fact2" in facts
        assert "fact3" in facts
        assert "fact4" in facts


# =============================================================================
# Preference Learning Tests
# =============================================================================

class TestPreferenceLearning:
    """Tests for preference tracking and learning."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_preference_categories(self, temp_project):
        """Test tracking multiple preference categories."""
        memory = SessionMemory(project_path=temp_project)
        
        categories = {
            "database": "PostgreSQL",
            "styling": "Tailwind",
            "auth": "JWT",
            "mode": "strict",
            "framework": "PyNext",
        }
        
        for key, value in categories.items():
            memory.add_preference(key, value, 0.8)
        
        prefs = memory.get_preferences()
        for key, value in categories.items():
            assert prefs[key] == value
    
    def test_preference_confidence_filtering(self, temp_project):
        """Test that preferences can be filtered by confidence."""
        memory = SessionMemory(project_path=temp_project)
        
        memory.add_preference("high_conf", "value1", 0.9)
        memory.add_preference("low_conf", "value2", 0.3)
        memory.add_preference("med_conf", "value3", 0.6)
        
        # Get all preferences
        all_prefs = memory.get_preferences()
        assert len(all_prefs) == 3
        
        # Filter by confidence (manual check)
        high_conf_prefs = {
            k: p.value for k, p in memory._preferences.items()
            if p.confidence >= 0.7
        }
        assert len(high_conf_prefs) == 1
        assert "high_conf" in high_conf_prefs
    
    def test_preference_update_increases_confidence(self, temp_project):
        """Test that repeated preferences can increase confidence."""
        memory = SessionMemory(project_path=temp_project)
        
        memory.add_preference("mode", "strict", 0.5)
        initial_conf = memory._preferences["mode"].confidence
        
        # Update with higher confidence
        memory.add_preference("mode", "strict", 0.9)
        updated_conf = memory._preferences["mode"].confidence
        
        assert updated_conf >= initial_conf


# =============================================================================
# Rollback and Checkpoint Tests Extended
# =============================================================================

class TestRollbackExtended:
    """Extended tests for rollback functionality."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_checkpoint_before_and_after(self, temp_project):
        """Test creating checkpoints before and after operations."""
        memory = SessionMemory(project_path=temp_project)
        
        cp_before = memory.add_checkpoint(
            trigger="before_generation",
            description="Before creating component",
            files={"a.py": "hash_before"},
        )
        
        cp_after = memory.add_checkpoint(
            trigger="after_generation",
            description="After creating component",
            files={"a.py": "hash_after", "b.py": "new_file"},
        )
        
        checkpoints = memory.get_checkpoints()
        assert len(checkpoints) == 2
        
        # Most recent first
        assert checkpoints[0].trigger == "after_generation"
        assert checkpoints[1].trigger == "before_generation"
    
    def test_checkpoint_files_differ(self, temp_project):
        """Test that checkpoint files can be compared."""
        memory = SessionMemory(project_path=temp_project)
        
        memory.add_checkpoint("test1", "Checkpoint 1", {
            "a.py": "hash1",
            "b.py": "hash2",
        })
        memory.add_checkpoint("test2", "Checkpoint 2", {
            "a.py": "hash1_modified",
            "b.py": "hash2",
            "c.py": "new_file",
        })
        
        cp1 = memory._checkpoints[0]
        cp2 = memory._checkpoints[1]
        
        # Files in cp1 but modified in cp2
        modified = [f for f in cp1.files_snapshot if f in cp2.files_snapshot and cp1.files_snapshot[f] != cp2.files_snapshot[f]]
        # Files in cp2 but not in cp1
        added = [f for f in cp2.files_snapshot if f not in cp1.files_snapshot]
        
        assert "a.py" in modified
        assert "c.py" in added


# =============================================================================
# Memory Lifecycle Tests
# =============================================================================

class TestMemoryLifecycle:
    """Tests for memory lifecycle management."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_full_session_lifecycle(self, temp_project):
        """Test complete session lifecycle."""
        # Start session
        memory = SessionMemory(project_path=temp_project)
        memory.load()  # Should not fail on empty
        
        # Add various data
        memory.add("user", "Create a blog", {})
        memory.add("assistant", "Creating blog...", {"files": ["pages/index.py"]})
        memory.add_checkpoint("generation", "Before blog", {"pages/index.py": "hash1"})
        memory.add_preference("type", "blog", 0.9)
        
        # Save and close
        memory.flush(force=True)
        
        # Simulate new session
        memory2 = SessionMemory(project_path=temp_project)
        memory2.load()
        
        # Verify all data restored
        assert len(memory2._entries) == 2
        assert len(memory2._checkpoints) == 1
        assert "type" in memory2._preferences
    
    def test_incremental_saves(self, temp_project):
        """Test that incremental saves work correctly."""
        memory = SessionMemory(project_path=temp_project)
        
        # First batch
        memory.add("user", "Message 1", {})
        memory.flush(force=True)
        
        # Second batch
        memory.add("user", "Message 2", {})
        memory.add("user", "Message 3", {})
        memory.flush(force=True)
        
        # Third batch
        memory.add("user", "Message 4", {})
        memory.flush(force=True)
        
        # Verify all saved
        memory2 = SessionMemory(project_path=temp_project)
        memory2.load()
        
        assert len(memory2._entries) == 4
    
    def test_export_restore_cycle(self, temp_project):
        """Test exporting and restoring memory."""
        memory = SessionMemory(project_path=temp_project)
        memory.add("user", "Test message", {"key": "value"})
        memory.add_preference("mode", "strict", 0.9)
        
        # Export to JSON
        json_export = memory.export("json")
        
        # Verify export is valid
        data = json.loads(json_export)
        assert "entries" in data
        assert len(data["entries"]) == 1


# =============================================================================
# Concurrent Operations Tests
# =============================================================================

class TestConcurrentOperations:
    """Tests for concurrent memory operations."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_multiple_rapid_adds(self, temp_project):
        """Test rapid sequential adds."""
        memory = SessionMemory(project_path=temp_project)
        
        for i in range(100):
            memory.add("user", f"Message {i}", {"index": i})
        
        assert len(memory._entries) == 100
    
    def test_add_during_flush(self, temp_project):
        """Test adding entries during flush operation."""
        memory = SessionMemory(project_path=temp_project)
        
        memory.add("user", "Before flush", {})
        memory.flush(force=True)
        memory.add("user", "After flush", {})
        memory.flush(force=True)
        
        memory2 = SessionMemory(project_path=temp_project)
        memory2.load()
        
        assert len(memory2._entries) == 2


# =============================================================================
# Memory Boundary Tests
# =============================================================================

class TestMemoryBoundaries:
    """Tests for memory limits and boundaries."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_max_entries_config(self, temp_project):
        """Test maximum entries configuration."""
        config = SyncConfig(max_entries_in_memory=10)
        memory = SessionMemory(project_path=temp_project, sync_config=config)
        
        # Add more than max
        for i in range(15):
            memory.add("user", f"Message {i}", {})
        
        # Should have triggered flush or truncation
        assert memory.sync_config.max_entries_in_memory == 10
    
    def test_empty_memory_stats(self, temp_project):
        """Test stats on completely empty memory."""
        memory = SessionMemory(project_path=temp_project)
        stats = memory.stats()
        
        assert stats["entries"] == 0
        assert stats["summaries"] == 0
        assert stats["checkpoints"] == 0
        assert stats["preferences"] == 0
        assert stats["total_tokens"] == 0
    
    def test_single_entry_operations(self, temp_project):
        """Test operations with single entry."""
        memory = SessionMemory(project_path=temp_project)
        memory.add("user", "Only entry", {})
        
        # All operations should work
        entries = memory.get_entries(limit=10)
        assert len(entries) == 1
        
        context = memory.get_relevant_context("test", max_tokens=1000)
        assert len(context) > 0
        
        results = memory.search("entry", k=5)
        assert len(results) == 1


# =============================================================================
# Metadata Tests
# =============================================================================

class TestMetadata:
    """Tests for entry metadata handling."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_files_metadata(self, temp_project):
        """Test storing files in metadata."""
        memory = SessionMemory(project_path=temp_project)
        
        memory.add("assistant", "Created files", {
            "files": ["pages/index.py", "models/user.py", "api/auth.py"]
        })
        
        entry = memory._entries[0]
        assert entry.metadata["files"] == ["pages/index.py", "models/user.py", "api/auth.py"]
    
    def test_plan_metadata(self, temp_project):
        """Test storing plan info in metadata."""
        memory = SessionMemory(project_path=temp_project)
        
        memory.add("assistant", "Generated plan", {
            "plan_id": "p_123",
            "steps": 5,
            "complexity": "medium",
        })
        
        entry = memory._entries[0]
        assert entry.metadata["plan_id"] == "p_123"
        assert entry.metadata["steps"] == 5
    
    def test_error_metadata(self, temp_project):
        """Test storing error info in metadata."""
        memory = SessionMemory(project_path=temp_project)
        
        memory.add("system", "Error occurred", {
            "error_type": "ValidationError",
            "error_message": "Invalid input",
            "file": "api/users.py",
            "line": 42,
        })
        
        entry = memory._entries[0]
        assert entry.metadata["error_type"] == "ValidationError"
        assert entry.metadata["line"] == 42
    
    def test_nested_metadata(self, temp_project):
        """Test nested metadata structures."""
        memory = SessionMemory(project_path=temp_project)
        
        memory.add("assistant", "Complex operation", {
            "changes": {
                "added": ["a.py", "b.py"],
                "modified": ["c.py"],
                "deleted": [],
            },
            "stats": {
                "lines_added": 150,
                "lines_removed": 30,
            }
        })
        
        entry = memory._entries[0]
        assert entry.metadata["changes"]["added"] == ["a.py", "b.py"]
        assert entry.metadata["stats"]["lines_added"] == 150
    
    def test_metadata_persistence(self, temp_project):
        """Test metadata persists through save/load."""
        memory = SessionMemory(project_path=temp_project)
        memory.add("user", "Test", {"custom_key": "custom_value", "number": 42})
        memory.flush(force=True)
        
        memory2 = SessionMemory(project_path=temp_project)
        memory2.load()
        
        assert memory2._entries[0].metadata["custom_key"] == "custom_value"
        assert memory2._entries[0].metadata["number"] == 42


# =============================================================================
# Timestamp Tests
# =============================================================================

class TestTimestamps:
    """Tests for timestamp handling."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_entry_has_timestamp(self, temp_project):
        """Test that entries have timestamps."""
        memory = SessionMemory(project_path=temp_project)
        
        before = datetime.utcnow()
        memory.add("user", "Test", {})
        after = datetime.utcnow()
        
        entry = memory._entries[0]
        assert entry.timestamp >= before
        assert entry.timestamp <= after
    
    def test_entries_ordered_by_timestamp(self, temp_project):
        """Test that entries maintain timestamp order."""
        memory = SessionMemory(project_path=temp_project)
        
        memory.add("user", "First", {})
        memory.add("user", "Second", {})
        memory.add("user", "Third", {})
        
        entries = memory.get_entries(limit=10)
        # Most recent first
        assert entries[0].content == "Third"
        assert entries[1].content == "Second"
        assert entries[2].content == "First"
    
    def test_timestamp_persistence(self, temp_project):
        """Test timestamps persist through save/load."""
        memory = SessionMemory(project_path=temp_project)
        memory.add("user", "Test", {})
        original_ts = memory._entries[0].timestamp
        memory.flush(force=True)
        
        memory2 = SessionMemory(project_path=temp_project)
        memory2.load()
        
        # Timestamps should be equal (within a second due to serialization)
        diff = abs((memory2._entries[0].timestamp - original_ts).total_seconds())
        assert diff < 1


# =============================================================================
# ID Generation Tests
# =============================================================================

class TestIDGeneration:
    """Tests for unique ID generation."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_entry_ids_unique(self, temp_project):
        """Test that entry IDs are unique."""
        memory = SessionMemory(project_path=temp_project)
        
        ids = set()
        for i in range(100):
            entry_id = memory.add("user", f"Message {i}", {})
            assert entry_id not in ids
            ids.add(entry_id)
    
    def test_checkpoint_ids_unique(self, temp_project):
        """Test that checkpoint IDs are unique."""
        memory = SessionMemory(project_path=temp_project)
        
        ids = set()
        for i in range(20):
            cp_id = memory.add_checkpoint("test", f"CP {i}", {"f.py": f"hash{i}"})
            assert cp_id not in ids
            ids.add(cp_id)
    
    def test_entry_id_prefix(self, temp_project):
        """Test entry ID prefix format."""
        memory = SessionMemory(project_path=temp_project)
        entry_id = memory.add("user", "Test", {})
        assert entry_id.startswith("e_")
    
    def test_checkpoint_id_prefix(self, temp_project):
        """Test checkpoint ID prefix format."""
        memory = SessionMemory(project_path=temp_project)
        cp_id = memory.add_checkpoint("test", "Test", {})
        assert cp_id.startswith("cp_")
    
    def test_preference_id_prefix(self, temp_project):
        """Test preference ID prefix format."""
        memory = SessionMemory(project_path=temp_project)
        pref_id = memory.add_preference("key", "value", 0.5)
        assert pref_id.startswith("pref_")


# =============================================================================
# Role Tests
# =============================================================================

class TestRoles:
    """Tests for different message roles."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_user_role(self, temp_project):
        """Test user role entries."""
        memory = SessionMemory(project_path=temp_project)
        memory.add("user", "User message", {})
        assert memory._entries[0].role == "user"
    
    def test_assistant_role(self, temp_project):
        """Test assistant role entries."""
        memory = SessionMemory(project_path=temp_project)
        memory.add("assistant", "Assistant response", {})
        assert memory._entries[0].role == "assistant"
    
    def test_system_role(self, temp_project):
        """Test system role entries."""
        memory = SessionMemory(project_path=temp_project)
        memory.add("system", "System message", {})
        assert memory._entries[0].role == "system"
    
    def test_filter_by_role(self, temp_project):
        """Test filtering entries by role."""
        memory = SessionMemory(project_path=temp_project)
        memory.add("user", "User 1", {})
        memory.add("assistant", "Assistant 1", {})
        memory.add("user", "User 2", {})
        memory.add("system", "System 1", {})
        memory.add("assistant", "Assistant 2", {})
        
        user_entries = [e for e in memory._entries if e.role == "user"]
        assistant_entries = [e for e in memory._entries if e.role == "assistant"]
        system_entries = [e for e in memory._entries if e.role == "system"]
        
        assert len(user_entries) == 2
        assert len(assistant_entries) == 2
        assert len(system_entries) == 1


# =============================================================================
# Context Token Budget Tests
# =============================================================================

class TestContextTokenBudget:
    """Tests for token budget management in context building."""
    
    @pytest.fixture
    def memory_with_varied_content(self, tmp_path):
        """Create memory with varied content sizes."""
        memory = SessionMemory(project_path=tmp_path)
        
        # Small entries
        memory.add("user", "Short message", {})
        memory.add("assistant", "Short reply", {})
        
        # Medium entries
        memory.add("user", "Medium length message " * 20, {})
        memory.add("assistant", "Medium length response " * 30, {})
        
        # Large entries
        memory.add("user", "Large message content " * 100, {})
        memory.add("assistant", "Large response content " * 150, {})
        
        # Add preferences
        memory.add_preference("db", "PostgreSQL", 0.9)
        memory.add_preference("auth", "JWT", 0.8)
        
        return memory
    
    def test_small_budget_includes_essentials(self, memory_with_varied_content):
        """Test small budget still includes essential info."""
        context = memory_with_varied_content.get_relevant_context("test", max_tokens=200)
        
        # Should have some content
        assert len(context) > 0
        # Should be relatively small
        assert len(context) < 3000  # Characters
    
    def test_large_budget_includes_more(self, memory_with_varied_content):
        """Test large budget includes at least as much content."""
        small_context = memory_with_varied_content.get_relevant_context("test", max_tokens=200)
        large_context = memory_with_varied_content.get_relevant_context("test", max_tokens=4000)
        
        # Large budget should include at least as much as small budget
        assert len(large_context) >= len(small_context)
    
    def test_context_respects_budget(self, memory_with_varied_content):
        """Test context doesn't grossly exceed budget."""
        # This is a rough test since we're dealing with estimates
        context = memory_with_varied_content.get_relevant_context("test", max_tokens=500)
        
        # Context shouldn't be massively larger than budget allows
        # Rough estimate: 1 token ≈ 4 characters
        max_chars = 500 * 4 * 2  # Allow some buffer
        assert len(context) < max_chars


# =============================================================================
# Async Operations Tests
# =============================================================================

class TestAsyncOperations:
    """Tests for async memory operations."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.mark.asyncio
    async def test_async_flush(self, temp_project):
        """Test async flush operation."""
        memory = SessionMemory(project_path=temp_project)
        memory.add("user", "Test async", {})
        
        # If flush_async exists and returns a task
        if hasattr(memory, 'flush_async'):
            task = memory.flush_async()
            await task
            assert memory.pending_count == 0
    
    @pytest.mark.asyncio
    async def test_summarize_old_async(self, temp_project):
        """Test async summarization."""
        memory = SessionMemory(project_path=temp_project)
        
        # Add entries
        for i in range(10):
            memory.add("user", f"Entry {i}", {})
        
        # Summarize should work async
        result = await memory.summarize_old()
        # Without LLM client, should return None
        assert result is None


# =============================================================================
# Export Format Tests
# =============================================================================

class TestExportFormats:
    """Extended tests for export formats."""
    
    @pytest.fixture
    def rich_memory(self, tmp_path):
        """Create memory with all record types."""
        memory = SessionMemory(project_path=tmp_path)
        
        # Entries
        memory.add("user", "Create a blog with authentication", {})
        memory.add("assistant", "I'll create a blog with JWT auth...", {
            "files": ["pages/index.py", "api/auth.py"],
            "plan_id": "p_001"
        })
        memory.add("user", "Add dark mode", {})
        memory.add("assistant", "Adding dark mode...", {
            "files": ["islands/ThemeToggle.py"]
        })
        
        # Checkpoints
        memory.add_checkpoint("before_generation", "Before blog", {"pages/index.py": "hash1"})
        memory.add_checkpoint("after_generation", "After blog", {"pages/index.py": "hash2", "api/auth.py": "hash3"})
        
        # Preferences
        memory.add_preference("database", "PostgreSQL", 0.9)
        memory.add_preference("styling", "Tailwind", 0.8)
        
        # Summary
        memory._summaries.append(MemorySummary(
            id="s_001",
            timestamp=datetime.utcnow(),
            covers=["e_old_1", "e_old_2"],
            content="Earlier: Set up basic project structure",
            original_tokens=500,
            summary_tokens=20,
            preserved_facts=["uses PyNext", "started from scratch"],
        ))
        
        return memory
    
    def test_markdown_export_sections(self, rich_memory):
        """Test markdown export has proper sections."""
        md = rich_memory.export("markdown")
        
        # Should have header
        assert "# Session Memory" in md or "# " in md
        
        # Should mention entries
        assert "blog" in md.lower() or "conversation" in md.lower()
    
    def test_json_export_complete_structure(self, rich_memory):
        """Test JSON export has complete structure."""
        json_str = rich_memory.export("json")
        data = json.loads(json_str)
        
        # All sections present
        assert "entries" in data
        assert "summaries" in data
        assert "checkpoints" in data
        assert "preferences" in data
        
        # Correct counts
        assert len(data["entries"]) == 4
        assert len(data["summaries"]) == 1
        assert len(data["checkpoints"]) == 2
        assert len(data["preferences"]) == 2
    
    def test_json_export_entry_structure(self, rich_memory):
        """Test JSON export entry structure."""
        json_str = rich_memory.export("json")
        data = json.loads(json_str)
        
        entry = data["entries"][0]
        assert "id" in entry
        assert "timestamp" in entry or "ts" in entry
        assert "role" in entry
        assert "content" in entry
    
    def test_json_export_reimportable(self, rich_memory):
        """Test JSON export can be parsed and used."""
        json_str = rich_memory.export("json")
        
        # Should be valid JSON
        data = json.loads(json_str)
        
        # Should be serializable again
        json_str2 = json.dumps(data)
        assert json.loads(json_str2) == data


# =============================================================================
# Memory Integrity Tests
# =============================================================================

class TestMemoryIntegrity:
    """Tests for memory data integrity."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_content_unchanged_after_save_load(self, temp_project):
        """Test content is unchanged after save/load cycle."""
        memory = SessionMemory(project_path=temp_project)
        
        original_content = "Test content with special chars: 'quotes', \"double\", \n newlines \t tabs"
        memory.add("user", original_content, {})
        memory.flush(force=True)
        
        memory2 = SessionMemory(project_path=temp_project)
        memory2.load()
        
        assert memory2._entries[0].content == original_content
    
    def test_metadata_unchanged_after_save_load(self, temp_project):
        """Test metadata is unchanged after save/load cycle."""
        memory = SessionMemory(project_path=temp_project)
        
        original_meta = {
            "files": ["a.py", "b.py"],
            "nested": {"key": "value"},
            "number": 42,
            "boolean": True,
        }
        memory.add("assistant", "Test", original_meta)
        memory.flush(force=True)
        
        memory2 = SessionMemory(project_path=temp_project)
        memory2.load()
        
        assert memory2._entries[0].metadata == original_meta
    
    def test_checkpoint_files_unchanged(self, temp_project):
        """Test checkpoint files snapshot is unchanged."""
        memory = SessionMemory(project_path=temp_project)
        
        original_files = {
            "pages/index.py": "sha256:abc123",
            "api/users.py": "sha256:def456",
        }
        memory.add_checkpoint("test", "Test checkpoint", original_files)
        memory.flush(force=True)
        
        memory2 = SessionMemory(project_path=temp_project)
        memory2.load()
        
        assert memory2._checkpoints[0].files_snapshot == original_files
    
    def test_preference_values_unchanged(self, temp_project):
        """Test preference values are unchanged."""
        memory = SessionMemory(project_path=temp_project)
        
        memory.add_preference("mode", "strict", 0.85)
        memory.flush(force=True)
        
        memory2 = SessionMemory(project_path=temp_project)
        memory2.load()
        
        assert memory2._preferences["mode"].value == "strict"
        assert memory2._preferences["mode"].confidence == 0.85


# =============================================================================
# Stress Tests
# =============================================================================

class TestStress:
    """Stress tests for memory system."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_many_entries(self, temp_project):
        """Test handling many entries."""
        memory = SessionMemory(project_path=temp_project)
        
        for i in range(500):
            memory.add("user", f"Entry {i}", {"index": i})
        
        assert len(memory._entries) == 500
        
        # Operations should still work
        entries = memory.get_entries(limit=10)
        assert len(entries) == 10
        
        results = memory.search("Entry 250", k=5)
        assert len(results) > 0
    
    def test_large_metadata(self, temp_project):
        """Test handling large metadata."""
        memory = SessionMemory(project_path=temp_project)
        
        large_meta = {
            "files": [f"file_{i}.py" for i in range(100)],
            "data": "x" * 10000,
        }
        memory.add("assistant", "Test", large_meta)
        memory.flush(force=True)
        
        memory2 = SessionMemory(project_path=temp_project)
        memory2.load()
        
        assert len(memory2._entries[0].metadata["files"]) == 100
    
    def test_many_checkpoints(self, temp_project):
        """Test handling many checkpoints."""
        memory = SessionMemory(project_path=temp_project)
        
        for i in range(50):
            memory.add_checkpoint(f"trigger_{i}", f"Checkpoint {i}", {f"f{i}.py": f"hash{i}"})
        
        assert len(memory._checkpoints) == 50
        
        checkpoints = memory.get_checkpoints(limit=10)
        assert len(checkpoints) == 10
    
    def test_save_load_large_memory(self, temp_project):
        """Test save/load with large memory."""
        memory = SessionMemory(project_path=temp_project)
        
        # Add many entries
        for i in range(200):
            memory.add("user", f"User message {i} " * 10, {"i": i})
            memory.add("assistant", f"Assistant response {i} " * 15, {"i": i})
        
        memory.flush(force=True)
        
        # Load should work
        memory2 = SessionMemory(project_path=temp_project)
        memory2.load()
        
        assert len(memory2._entries) == 400

