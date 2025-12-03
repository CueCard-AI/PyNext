"""
Tests for pynext.app.memory - Session Memory System.

Tests cover:
- MemoryEntry, MemorySummary, Checkpoint, Preference data classes
- SessionMemory CRUD operations
- Sync configuration and behavior
- Summarization
- Search and context retrieval
- File persistence
"""

import pytest
import json
import tempfile
from datetime import datetime
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
        
        memory.clear()
        
        assert len(memory._entries) == 0
        assert not memory._memory_file.exists()
    
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

