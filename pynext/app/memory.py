"""
Session Memory - Persistent conversation history with automatic summarization.

Stores conversation history, checkpoints, summaries, and preferences in a
.mem file for retrieval across sessions.

Example:
    memory = SessionMemory(project_path=Path("."))
    memory.load()
    
    memory.add("user", "Create a blog with auth", {})
    memory.add("assistant", "I'll create...", {"files": ["pages/index.py"]})
    
    # Get context for AI
    context = memory.get_relevant_context("add dark mode", max_tokens=4000)
    
    memory.flush()  # Save to disk
"""

import asyncio
import hashlib
import json
import logging
import os
import re
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class MemoryEntry:
    """A single conversation entry."""
    id: str
    timestamp: datetime
    role: str  # user, assistant, system
    content: str
    tokens: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    summarized: bool = False  # Has this been included in a summary?
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return {
            "type": "entry",
            "id": self.id,
            "ts": self.timestamp.isoformat(),
            "role": self.role,
            "content": self.content,
            "tokens": self.tokens,
            "meta": self.metadata,
            "summarized": self.summarized,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryEntry":
        """Create from dict."""
        return cls(
            id=data["id"],
            timestamp=datetime.fromisoformat(data["ts"]),
            role=data["role"],
            content=data["content"],
            tokens=data.get("tokens", 0),
            metadata=data.get("meta", {}),
            summarized=data.get("summarized", False),
        )


@dataclass
class MemorySummary:
    """A summary of multiple conversation entries."""
    id: str
    timestamp: datetime
    covers: List[str]  # Entry IDs that were summarized
    content: str
    original_tokens: int
    summary_tokens: int
    preserved_facts: List[str] = field(default_factory=list)
    checkpoint_refs: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return {
            "type": "summary",
            "id": self.id,
            "ts": self.timestamp.isoformat(),
            "covers": self.covers,
            "content": self.content,
            "original_tokens": self.original_tokens,
            "summary_tokens": self.summary_tokens,
            "preserved_facts": self.preserved_facts,
            "checkpoint_refs": self.checkpoint_refs,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemorySummary":
        """Create from dict."""
        return cls(
            id=data["id"],
            timestamp=datetime.fromisoformat(data["ts"]),
            covers=data["covers"],
            content=data["content"],
            original_tokens=data.get("original_tokens", 0),
            summary_tokens=data.get("summary_tokens", 0),
            preserved_facts=data.get("preserved_facts", []),
            checkpoint_refs=data.get("checkpoint_refs", []),
        )


@dataclass
class Checkpoint:
    """A snapshot of project state at a point in time."""
    id: str
    timestamp: datetime
    trigger: str  # before_generation, after_generation, user_request, etc.
    description: str
    files_snapshot: Dict[str, str]  # path -> content hash
    rollback_id: Optional[str] = None
    entry_ref: Optional[str] = None  # Link to conversation entry
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return {
            "type": "checkpoint",
            "id": self.id,
            "ts": self.timestamp.isoformat(),
            "trigger": self.trigger,
            "description": self.description,
            "files_snapshot": self.files_snapshot,
            "rollback_id": self.rollback_id,
            "entry_ref": self.entry_ref,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Checkpoint":
        """Create from dict."""
        return cls(
            id=data["id"],
            timestamp=datetime.fromisoformat(data["ts"]),
            trigger=data["trigger"],
            description=data["description"],
            files_snapshot=data["files_snapshot"],
            rollback_id=data.get("rollback_id"),
            entry_ref=data.get("entry_ref"),
        )


@dataclass
class Preference:
    """A learned user preference."""
    id: str
    timestamp: datetime
    key: str
    value: str
    confidence: float = 0.5  # 0.0 to 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return {
            "type": "preference",
            "id": self.id,
            "ts": self.timestamp.isoformat(),
            "key": self.key,
            "value": self.value,
            "confidence": self.confidence,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Preference":
        """Create from dict."""
        return cls(
            id=data["id"],
            timestamp=datetime.fromisoformat(data["ts"]),
            key=data["key"],
            value=data["value"],
            confidence=data.get("confidence", 0.5),
        )


@dataclass
class SyncConfig:
    """Configuration for memory sync behavior."""
    mode: str = "incremental"  # incremental, full, manual
    triggers: List[str] = field(default_factory=lambda: ["assistant_response", "checkpoint", "exit"])
    batch_size: int = 5  # Buffer this many entries before writing
    interval: int = 0  # Seconds between syncs (0 = disabled)
    
    # What to sync
    sync_entries: bool = True
    sync_summaries: bool = True
    sync_checkpoints: bool = True
    sync_preferences: bool = True
    
    # Filtering
    exclude_roles: List[str] = field(default_factory=list)
    min_content_length: int = 0
    max_entries_in_memory: int = 1000
    
    # File management
    max_file_size_mb: int = 50
    rotate_files: bool = True
    max_rotated_files: int = 5
    
    # Compression
    compress_on_sync: bool = False
    compress_threshold_mb: int = 10


# =============================================================================
# Session Memory
# =============================================================================

class SessionMemory:
    """
    Persistent memory with automatic summarization.
    
    Stores conversation history, checkpoints, summaries, and preferences
    in a .mem file (JSON Lines format) for retrieval across sessions.
    """
    
    MEMORY_FILE = ".pynext/session.mem"
    GLOBAL_MEMORY = Path.home() / ".pynext" / "global.mem"
    MAX_CONTEXT_TOKENS = 100_000
    SUMMARY_THRESHOLD = 0.8  # Summarize at 80% capacity
    
    def __init__(
        self,
        project_path: Optional[Path] = None,
        sync_config: Optional[SyncConfig] = None,
        llm_client: Optional[Any] = None,
    ):
        """
        Initialize session memory.
        
        Args:
            project_path: Path to project directory
            sync_config: Configuration for sync behavior
            llm_client: LLM client for summarization
        """
        self.project_path = project_path or Path.cwd()
        self.sync_config = sync_config or SyncConfig()
        self.llm_client = llm_client
        
        # In-memory storage
        self._entries: List[MemoryEntry] = []
        self._summaries: List[MemorySummary] = []
        self._checkpoints: List[Checkpoint] = []
        self._preferences: Dict[str, Preference] = {}
        
        # Sync state
        self._pending_entries: List[MemoryEntry] = []
        self._pending_summaries: List[MemorySummary] = []
        self._pending_checkpoints: List[Checkpoint] = []
        self._pending_preferences: List[Preference] = []
        self._last_sync: Optional[datetime] = None
        self._sync_paused: bool = False
        
        # File metadata
        self._file_version: int = 1
        self._project_name: str = self.project_path.name
        self._created: Optional[datetime] = None
        
        # Ensure directory exists
        self._memory_file.parent.mkdir(parents=True, exist_ok=True)
    
    @property
    def _memory_file(self) -> Path:
        """Get the memory file path."""
        return self.project_path / self.MEMORY_FILE
    
    # =========================================================================
    # Writing
    # =========================================================================
    
    def add(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Add a conversation entry.
        
        Args:
            role: user, assistant, or system
            content: The message content
            metadata: Optional metadata (files created, plan info, etc.)
            
        Returns:
            Entry ID
        """
        # Check exclusions
        if role in self.sync_config.exclude_roles:
            return ""
        if len(content) < self.sync_config.min_content_length:
            return ""
        
        entry_id = f"e_{uuid.uuid4().hex[:8]}"
        entry = MemoryEntry(
            id=entry_id,
            timestamp=datetime.utcnow(),
            role=role,
            content=content,
            tokens=self._count_tokens(content),
            metadata=metadata or {},
        )
        
        self._entries.append(entry)
        self._pending_entries.append(entry)
        
        # Check if we should auto-sync
        if self._should_auto_sync("entry"):
            self._maybe_sync()
        
        # Check if we need to summarize
        if self._should_summarize():
            asyncio.create_task(self.summarize_old())
        
        logger.debug(f"Added entry {entry_id}: {role}")
        return entry_id
    
    def add_checkpoint(
        self,
        trigger: str,
        description: str,
        files: Dict[str, str],
        entry_ref: Optional[str] = None,
    ) -> str:
        """
        Create a checkpoint.
        
        Args:
            trigger: What triggered this checkpoint
            description: Human-readable description
            files: Dict of path -> content hash
            entry_ref: Optional link to conversation entry
            
        Returns:
            Checkpoint ID
        """
        checkpoint_id = f"cp_{uuid.uuid4().hex[:8]}"
        checkpoint = Checkpoint(
            id=checkpoint_id,
            timestamp=datetime.utcnow(),
            trigger=trigger,
            description=description,
            files_snapshot=files,
            rollback_id=f"rb_{uuid.uuid4().hex[:8]}",
            entry_ref=entry_ref,
        )
        
        self._checkpoints.append(checkpoint)
        self._pending_checkpoints.append(checkpoint)
        
        if self._should_auto_sync("checkpoint"):
            self._maybe_sync()
        
        logger.debug(f"Created checkpoint {checkpoint_id}: {trigger}")
        return checkpoint_id
    
    def add_preference(
        self,
        key: str,
        value: str,
        confidence: float = 0.5,
    ) -> str:
        """
        Add or update a user preference.
        
        Args:
            key: Preference key
            value: Preference value
            confidence: Confidence level (0.0 to 1.0)
            
        Returns:
            Preference ID
        """
        pref_id = f"pref_{uuid.uuid4().hex[:8]}"
        preference = Preference(
            id=pref_id,
            timestamp=datetime.utcnow(),
            key=key,
            value=value,
            confidence=confidence,
        )
        
        self._preferences[key] = preference
        self._pending_preferences.append(preference)
        
        logger.debug(f"Set preference {key}={value}")
        return pref_id
    
    # =========================================================================
    # Reading
    # =========================================================================
    
    def get_entries(self, limit: Optional[int] = None) -> List[MemoryEntry]:
        """Get conversation entries, most recent first."""
        entries = list(reversed(self._entries))
        if limit:
            entries = entries[:limit]
        return entries
    
    def get_summaries(self) -> List[MemorySummary]:
        """Get all summaries."""
        return list(self._summaries)
    
    def get_checkpoints(self, limit: int = 10) -> List[Checkpoint]:
        """Get checkpoints, most recent first."""
        return list(reversed(self._checkpoints))[:limit]
    
    def get_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """Get a specific checkpoint by ID."""
        for cp in self._checkpoints:
            if cp.id == checkpoint_id:
                return cp
        return None
    
    def get_preferences(self) -> Dict[str, str]:
        """Get all preferences as key-value pairs."""
        return {k: v.value for k, v in self._preferences.items()}
    
    def get_preserved_facts(self) -> List[str]:
        """Get all preserved facts from summaries."""
        facts = []
        for summary in self._summaries:
            facts.extend(summary.preserved_facts)
        return facts
    
    # =========================================================================
    # Search / Retrieval
    # =========================================================================
    
    def search(self, query: str, k: int = 5) -> List[MemoryEntry]:
        """
        Search entries by keyword matching.
        
        Args:
            query: Search query
            k: Maximum results
            
        Returns:
            List of matching entries
        """
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        scored_entries = []
        for entry in self._entries:
            content_lower = entry.content.lower()
            # Simple keyword matching score
            score = sum(1 for word in query_words if word in content_lower)
            if score > 0:
                scored_entries.append((score, entry))
        
        scored_entries.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in scored_entries[:k]]
    
    def get_relevant_context(self, query: str, max_tokens: int = 4000) -> str:
        """
        Build context from memory for current query.
        
        Priority order:
        1. Recent entries (last 3-5) - always included
        2. Preserved facts - always included (compact)
        3. Relevant summaries - semantic search
        4. Relevant old entries - keyword search (if space)
        
        Args:
            query: Current user query
            max_tokens: Maximum tokens for context
            
        Returns:
            Formatted context string
        """
        context_parts = []
        remaining_tokens = max_tokens
        
        # 1. Recent entries (most important)
        recent = self.get_entries(limit=5)
        if recent:
            recent_text = self._format_entries(recent)
            context_parts.append(f"## Recent Conversation\n{recent_text}")
            remaining_tokens -= self._count_tokens(recent_text)
        
        # 2. Preserved facts (compact, always fit)
        facts = self.get_preserved_facts()
        if facts:
            facts_text = "## Key Facts\n" + "\n".join(f"- {f}" for f in facts[:20])
            context_parts.append(facts_text)
            remaining_tokens -= self._count_tokens(facts_text)
        
        # 3. Preferences
        prefs = self.get_preferences()
        if prefs:
            prefs_text = "## User Preferences\n" + "\n".join(
                f"- {k}: {v}" for k, v in prefs.items()
            )
            context_parts.append(prefs_text)
            remaining_tokens -= self._count_tokens(prefs_text)
        
        # 4. Relevant summaries
        if remaining_tokens > 500 and self._summaries:
            relevant_summaries = self._search_summaries(query, k=3)
            for summary in relevant_summaries:
                if remaining_tokens < 200:
                    break
                context_parts.append(f"## Earlier Session\n{summary.content}")
                remaining_tokens -= summary.summary_tokens
        
        # 5. Relevant old entries (if space)
        if remaining_tokens > 500:
            relevant_entries = self.search(query, k=5)
            # Filter out entries already in recent
            recent_ids = {e.id for e in recent}
            relevant_entries = [e for e in relevant_entries if e.id not in recent_ids]
            
            if relevant_entries:
                relevant_text = self._format_entries(relevant_entries)
                context_parts.append(f"## Related History\n{relevant_text}")
        
        return "\n\n".join(context_parts)
    
    def _search_summaries(self, query: str, k: int = 3) -> List[MemorySummary]:
        """Search summaries by keyword matching."""
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        scored = []
        for summary in self._summaries:
            content_lower = summary.content.lower()
            score = sum(1 for word in query_words if word in content_lower)
            # Boost for facts
            for fact in summary.preserved_facts:
                if any(word in fact.lower() for word in query_words):
                    score += 0.5
            if score > 0:
                scored.append((score, summary))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in scored[:k]]
    
    def _format_entries(self, entries: List[MemoryEntry]) -> str:
        """Format entries for context."""
        lines = []
        for entry in entries:
            role_prefix = {"user": "User", "assistant": "Assistant", "system": "System"}.get(
                entry.role, entry.role.title()
            )
            lines.append(f"**{role_prefix}**: {entry.content[:500]}")
            if entry.metadata.get("files"):
                lines.append(f"  Files: {', '.join(entry.metadata['files'])}")
        return "\n".join(lines)
    
    # =========================================================================
    # Persistence
    # =========================================================================
    
    def load(self) -> bool:
        """
        Load memory from .mem file.
        
        Returns:
            True if loaded successfully
        """
        if not self._memory_file.exists():
            logger.info(f"No memory file found at {self._memory_file}")
            return False
        
        try:
            with open(self._memory_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        data = json.loads(line)
                        record_type = data.get("type")
                        
                        if record_type == "meta":
                            self._file_version = data.get("v", 1)
                            self._created = datetime.fromisoformat(data["created"])
                            self._project_name = data.get("project", "")
                        elif record_type == "entry":
                            self._entries.append(MemoryEntry.from_dict(data))
                        elif record_type == "summary":
                            self._summaries.append(MemorySummary.from_dict(data))
                        elif record_type == "checkpoint":
                            self._checkpoints.append(Checkpoint.from_dict(data))
                        elif record_type == "preference":
                            pref = Preference.from_dict(data)
                            self._preferences[pref.key] = pref
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(f"Skipping malformed line: {e}")
            
            logger.info(
                f"Loaded memory: {len(self._entries)} entries, "
                f"{len(self._summaries)} summaries, "
                f"{len(self._checkpoints)} checkpoints"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to load memory: {e}")
            return False
    
    def save(self) -> None:
        """Alias for flush() - saves pending changes to disk."""
        self.flush()
    
    def flush(self, force: bool = False) -> int:
        """
        Flush pending entries to .mem file.
        
        Args:
            force: Force sync even if paused
            
        Returns:
            Number of records written
        """
        if self._sync_paused and not force:
            return 0
        
        if self.sync_config.mode == "manual" and not force:
            return 0
        
        count = 0
        
        try:
            # Ensure directory exists
            self._memory_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if we need to write meta header
            write_meta = not self._memory_file.exists()
            
            with open(self._memory_file, "a", encoding="utf-8") as f:
                # Write meta if new file
                if write_meta:
                    meta = {
                        "v": self._file_version,
                        "type": "meta",
                        "created": datetime.utcnow().isoformat(),
                        "project": self._project_name,
                    }
                    f.write(json.dumps(meta) + "\n")
                    count += 1
                
                # Write pending entries
                if self.sync_config.sync_entries:
                    for entry in self._pending_entries:
                        f.write(json.dumps(entry.to_dict()) + "\n")
                        count += 1
                
                # Write pending summaries
                if self.sync_config.sync_summaries:
                    for summary in self._pending_summaries:
                        f.write(json.dumps(summary.to_dict()) + "\n")
                        count += 1
                
                # Write pending checkpoints
                if self.sync_config.sync_checkpoints:
                    for checkpoint in self._pending_checkpoints:
                        f.write(json.dumps(checkpoint.to_dict()) + "\n")
                        count += 1
                
                # Write pending preferences
                if self.sync_config.sync_preferences:
                    for pref in self._pending_preferences:
                        f.write(json.dumps(pref.to_dict()) + "\n")
                        count += 1
            
            # Clear pending
            self._pending_entries.clear()
            self._pending_summaries.clear()
            self._pending_checkpoints.clear()
            self._pending_preferences.clear()
            self._last_sync = datetime.utcnow()
            
            logger.debug(f"Flushed {count} records to {self._memory_file}")
            
        except Exception as e:
            logger.error(f"Failed to flush memory: {e}")
        
        return count
    
    def compact(self) -> None:
        """
        Rewrite file, removing entries that have been summarized.
        
        This reduces file size by keeping only:
        - Meta header
        - Unsummarized entries
        - All summaries
        - All checkpoints
        - All preferences
        """
        # Get IDs of summarized entries
        summarized_ids: Set[str] = set()
        for summary in self._summaries:
            summarized_ids.update(summary.covers)
        
        # Filter entries
        kept_entries = [e for e in self._entries if e.id not in summarized_ids]
        
        # Rewrite file
        try:
            with open(self._memory_file, "w", encoding="utf-8") as f:
                # Meta
                meta = {
                    "v": self._file_version,
                    "type": "meta",
                    "created": (self._created or datetime.utcnow()).isoformat(),
                    "project": self._project_name,
                }
                f.write(json.dumps(meta) + "\n")
                
                # Entries
                for entry in kept_entries:
                    f.write(json.dumps(entry.to_dict()) + "\n")
                
                # Summaries
                for summary in self._summaries:
                    f.write(json.dumps(summary.to_dict()) + "\n")
                
                # Checkpoints
                for checkpoint in self._checkpoints:
                    f.write(json.dumps(checkpoint.to_dict()) + "\n")
                
                # Preferences
                for pref in self._preferences.values():
                    f.write(json.dumps(pref.to_dict()) + "\n")
            
            # Update in-memory entries
            self._entries = kept_entries
            
            logger.info(
                f"Compacted memory: removed {len(summarized_ids)} summarized entries"
            )
            
        except Exception as e:
            logger.error(f"Failed to compact memory: {e}")
    
    def clear(self) -> None:
        """Clear all memory (both in-memory and on disk)."""
        self._entries.clear()
        self._summaries.clear()
        self._checkpoints.clear()
        self._preferences.clear()
        self._pending_entries.clear()
        self._pending_summaries.clear()
        self._pending_checkpoints.clear()
        self._pending_preferences.clear()
        
        if self._memory_file.exists():
            self._memory_file.unlink()
        
        logger.info("Cleared all memory")
    
    def export(self, format: str = "markdown") -> str:
        """
        Export memory to a readable format.
        
        Args:
            format: "markdown" or "json"
            
        Returns:
            Formatted string
        """
        if format == "json":
            data = {
                "entries": [e.to_dict() for e in self._entries],
                "summaries": [s.to_dict() for s in self._summaries],
                "checkpoints": [c.to_dict() for c in self._checkpoints],
                "preferences": [p.to_dict() for p in self._preferences.values()],
            }
            return json.dumps(data, indent=2)
        
        # Markdown format
        lines = ["# Session Memory\n"]
        
        if self._summaries:
            lines.append("## Summaries\n")
            for summary in self._summaries:
                lines.append(f"### {summary.timestamp.strftime('%Y-%m-%d %H:%M')}")
                lines.append(summary.content)
                if summary.preserved_facts:
                    lines.append("\n**Key Facts:**")
                    for fact in summary.preserved_facts:
                        lines.append(f"- {fact}")
                lines.append("")
        
        if self._entries:
            lines.append("## Conversation\n")
            for entry in self._entries:
                role = entry.role.title()
                time = entry.timestamp.strftime("%H:%M")
                lines.append(f"**[{time}] {role}:** {entry.content}")
                if entry.metadata.get("files"):
                    lines.append(f"  *Files: {', '.join(entry.metadata['files'])}*")
                lines.append("")
        
        if self._checkpoints:
            lines.append("## Checkpoints\n")
            for cp in self._checkpoints:
                lines.append(f"- **{cp.id}** ({cp.trigger}): {cp.description}")
        
        if self._preferences:
            lines.append("\n## Preferences\n")
            for key, pref in self._preferences.items():
                lines.append(f"- {key}: {pref.value} (confidence: {pref.confidence})")
        
        return "\n".join(lines)
    
    # =========================================================================
    # Sync Control
    # =========================================================================
    
    def configure_sync(
        self,
        mode: Optional[str] = None,
        triggers: Optional[List[str]] = None,
        batch_size: Optional[int] = None,
        interval: Optional[int] = None,
    ) -> None:
        """Configure sync behavior."""
        if mode is not None:
            self.sync_config.mode = mode
        if triggers is not None:
            self.sync_config.triggers = triggers
        if batch_size is not None:
            self.sync_config.batch_size = batch_size
        if interval is not None:
            self.sync_config.interval = interval
    
    def pause_sync(self) -> None:
        """Pause automatic syncing."""
        self._sync_paused = True
        logger.info("Sync paused")
    
    def resume_sync(self) -> None:
        """Resume automatic syncing."""
        self._sync_paused = False
        logger.info("Sync resumed")
        self._maybe_sync()
    
    @property
    def pending_count(self) -> int:
        """Number of entries waiting to be synced."""
        return (
            len(self._pending_entries) +
            len(self._pending_summaries) +
            len(self._pending_checkpoints) +
            len(self._pending_preferences)
        )
    
    @property
    def last_sync(self) -> Optional[datetime]:
        """When was last successful sync."""
        return self._last_sync
    
    @property
    def sync_paused(self) -> bool:
        """Is syncing currently paused."""
        return self._sync_paused
    
    def _should_auto_sync(self, trigger: str) -> bool:
        """Check if we should auto-sync based on trigger."""
        if self._sync_paused:
            return False
        if self.sync_config.mode == "manual":
            return False
        
        # Check trigger
        trigger_map = {
            "entry": "user_input" if trigger == "user" else "assistant_response",
            "checkpoint": "checkpoint",
        }
        mapped_trigger = trigger_map.get(trigger, trigger)
        return mapped_trigger in self.sync_config.triggers
    
    def _maybe_sync(self) -> None:
        """Check if we should sync based on batch size."""
        if self.pending_count >= self.sync_config.batch_size:
            self.flush()
    
    # =========================================================================
    # Summarization
    # =========================================================================
    
    def _should_summarize(self) -> bool:
        """Check if we should summarize old entries."""
        total_tokens = sum(e.tokens for e in self._entries if not e.summarized)
        threshold = self.MAX_CONTEXT_TOKENS * self.SUMMARY_THRESHOLD
        return total_tokens > threshold
    
    async def summarize_old(self, keep_recent: int = 10) -> Optional[str]:
        """
        Summarize old entries to save tokens.
        
        Args:
            keep_recent: Number of recent entries to keep unsummarized
            
        Returns:
            Summary ID if created, None otherwise
        """
        if not self.llm_client:
            logger.warning("No LLM client configured for summarization")
            return None
        
        # Get entries to summarize (oldest, not already summarized)
        unsummarized = [e for e in self._entries if not e.summarized]
        if len(unsummarized) <= keep_recent:
            return None
        
        to_summarize = unsummarized[:-keep_recent]
        if not to_summarize:
            return None
        
        # Build content for summarization
        content_parts = []
        for entry in to_summarize:
            role = entry.role.title()
            content_parts.append(f"{role}: {entry.content}")
            if entry.metadata.get("files"):
                content_parts.append(f"  Files: {', '.join(entry.metadata['files'])}")
        
        conversation_text = "\n".join(content_parts)
        original_tokens = sum(e.tokens for e in to_summarize)
        
        # Get checkpoints in this range
        entry_ids = {e.id for e in to_summarize}
        checkpoint_refs = [
            cp.id for cp in self._checkpoints
            if cp.entry_ref in entry_ids
        ]
        
        # Call LLM for summarization
        try:
            prompt = f"""Summarize this conversation history. Preserve:
- All file names created/modified
- User preferences and decisions
- Technical choices (DB, auth, styling)
- Any errors encountered and how they were resolved

Format your response as:
SUMMARY: <concise paragraph>
FACTS:
- <fact 1>
- <fact 2>
...

CONVERSATION:
{conversation_text}"""

            response = await self.llm_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            )
            
            response_text = response.content[0].text
            
            # Parse response
            summary_content = ""
            facts = []
            
            if "SUMMARY:" in response_text:
                parts = response_text.split("FACTS:")
                summary_content = parts[0].replace("SUMMARY:", "").strip()
                if len(parts) > 1:
                    facts_text = parts[1].strip()
                    facts = [
                        line.strip().lstrip("- ")
                        for line in facts_text.split("\n")
                        if line.strip().startswith("-")
                    ]
            else:
                summary_content = response_text.strip()
            
            # Create summary
            summary_id = f"s_{uuid.uuid4().hex[:8]}"
            summary = MemorySummary(
                id=summary_id,
                timestamp=datetime.utcnow(),
                covers=[e.id for e in to_summarize],
                content=summary_content,
                original_tokens=original_tokens,
                summary_tokens=self._count_tokens(summary_content),
                preserved_facts=facts,
                checkpoint_refs=checkpoint_refs,
            )
            
            self._summaries.append(summary)
            self._pending_summaries.append(summary)
            
            # Mark entries as summarized
            for entry in to_summarize:
                entry.summarized = True
            
            logger.info(
                f"Created summary {summary_id}: "
                f"compressed {original_tokens} -> {summary.summary_tokens} tokens"
            )
            
            if self._should_auto_sync("summarize"):
                self.flush()
            
            return summary_id
            
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return None
    
    def expand_summary(self, summary_id: str) -> List[MemoryEntry]:
        """Get original entries for a summary."""
        for summary in self._summaries:
            if summary.id == summary_id:
                return [
                    e for e in self._entries
                    if e.id in summary.covers
                ]
        return []
    
    # =========================================================================
    # Utilities
    # =========================================================================
    
    def _count_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        # Simple approximation: ~4 chars per token
        return len(text) // 4
    
    def stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        total_tokens = sum(e.tokens for e in self._entries)
        summarized_tokens = sum(e.tokens for e in self._entries if e.summarized)
        
        return {
            "entries": len(self._entries),
            "summaries": len(self._summaries),
            "checkpoints": len(self._checkpoints),
            "preferences": len(self._preferences),
            "total_tokens": total_tokens,
            "summarized_tokens": summarized_tokens,
            "active_tokens": total_tokens - summarized_tokens,
            "pending_sync": self.pending_count,
            "last_sync": self._last_sync.isoformat() if self._last_sync else None,
            "sync_paused": self._sync_paused,
        }


# =============================================================================
# Convenience Functions
# =============================================================================

_memory_instance: Optional[SessionMemory] = None


def get_memory(project_path: Optional[Path] = None) -> SessionMemory:
    """Get or create the memory instance."""
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = SessionMemory(project_path=project_path)
    return _memory_instance


def reset_memory() -> None:
    """Reset the global memory instance."""
    global _memory_instance
    _memory_instance = None

