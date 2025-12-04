# PyNext Session Memory System

> **Complete Reference Guide** for persistent conversation memory with automatic summarization, checkpoints, and context retrieval.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Memory File Format](#memory-file-format)
- [Record Types](#record-types)
- [CLI Commands](#cli-commands)
- [Session Commands](#session-commands)
- [Sync Configuration](#sync-configuration)
- [Summarization](#summarization)
- [Checkpoints](#checkpoints)
- [Context Building](#context-building)
- [Python API Reference](#python-api-reference)
- [Token Budget Strategy](#token-budget-strategy)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## Overview

The PyNext Session Memory system provides **persistent, intelligent memory** for AI conversations:

| Feature | Description |
|---------|-------------|
| **Persistent History** | Conversation saved to `.mem` file across sessions |
| **Automatic Summarization** | Compress old context when approaching token limits |
| **Checkpoints** | Project state snapshots for rollback capability |
| **Preferences** | Learn and remember user preferences over time |
| **Semantic Search** | Find relevant history by meaning, not just keywords |
| **Configurable Sync** | Full control over when and how memory is persisted |
| **Context Building** | Intelligent retrieval for optimal AI context |

### Why Session Memory?

Without memory, every conversation starts fresh. Session memory enables:

```
Session 1: "Create a blog with authentication"
  → AI creates blog with JWT auth, PostgreSQL, 12 files

Session 2: "Add dark mode"
  → AI remembers: uses JWT auth, PostgreSQL, existing file structure
  → Makes intelligent decisions based on context
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    SESSION MEMORY ARCHITECTURE                   │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────┐     ┌──────────────────────┐
│     In-Memory        │     │      Disk File       │
│    ┌──────────┐      │     │   .pynext/session.mem│
│    │ Entries  │◄─────┼─────┤   (JSONL format)     │
│    ├──────────┤      │     └──────────────────────┘
│    │Summaries │      │              │
│    ├──────────┤      │     ┌────────▼───────────┐
│    │Checkpoints│     │     │  Sync Manager      │
│    ├──────────┤      │     │  - Incremental     │
│    │Preferences│     │     │  - Full rewrite    │
│    └──────────┘      │     │  - Manual          │
└──────────────────────┘     └────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────────┐
│                      CONTEXT BUILDER                              │
│                                                                   │
│  Query: "add user authentication"                                 │
│                                                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐   │
│  │ Recent Entries  │  │ Preserved Facts │  │ Relevant Search │   │
│  │ (last 5)        │  │ (from summaries)│  │ (semantic)      │   │
│  │ Priority: 1     │  │ Priority: 2     │  │ Priority: 3     │   │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘   │
│                              │                                    │
│                              ▼                                    │
│                    ┌─────────────────┐                            │
│                    │ Final Context   │                            │
│                    │ (max_tokens)    │                            │
│                    └─────────────────┘                            │
└──────────────────────────────────────────────────────────────────┘
```

### File Locations

```
project/
├── .pynext/
│   ├── session.mem      # Project memory (primary)
│   └── checkpoints/     # Checkpoint files (managed by RollbackManager)
└── ...

~/.pynext/
└── global.mem           # Global memory (cross-project learnings)
```

---

## Memory File Format

Memory is stored as **JSON Lines (JSONL)** - one JSON object per line. This format enables:

- **Append-only writes** - Fast incremental saves
- **Streaming reads** - Process large files efficiently
- **Human readable** - Easy to inspect and debug
- **Partial recovery** - Corrupt lines don't break entire file

### JSONL Structure

```jsonl
{"type":"meta","v":1,"created":"2025-01-15T10:00:00Z","project":"my-app"}
{"type":"entry","id":"e_001","ts":"2025-01-15T10:01:00Z","role":"user","content":"Create a blog","tokens":12,"meta":{}}
{"type":"entry","id":"e_002","ts":"2025-01-15T10:01:30Z","role":"assistant","content":"I'll create...","tokens":450,"meta":{"files":["pages/index.py"]}}
{"type":"summary","id":"s_001","ts":"2025-01-15T11:00:00Z","covers":["e_001","e_002"],"content":"Created blog app.","original_tokens":462,"summary_tokens":25}
{"type":"checkpoint","id":"cp_001","ts":"2025-01-15T11:00:00Z","trigger":"before_generation","files_snapshot":{"pages/index.py":"sha256:abc"}}
{"type":"preference","id":"pref_001","ts":"2025-01-15T11:30:00Z","key":"mode","value":"strict","confidence":0.8}
```

---

## Record Types

### Meta Record (First Line)

```json
{
  "type": "meta",
  "v": 1,                           // File format version
  "created": "2025-01-15T10:00:00Z", // When file was created
  "project": "my-app"               // Project name
}
```

### Entry Record (Conversation Turns)

```json
{
  "type": "entry",
  "id": "e_001",                    // Unique ID (e_ prefix)
  "ts": "2025-01-15T10:01:00Z",     // Timestamp
  "role": "user",                   // user, assistant, system
  "content": "Create a blog",       // Message content
  "tokens": 12,                     // Estimated token count
  "meta": {                         // Optional metadata
    "files": ["pages/index.py"],    // Files created/modified
    "plan_id": "p_123",             // Associated plan
    "error_type": "ValidationError" // If error occurred
  },
  "summarized": false               // Whether included in a summary
}
```

### Summary Record (Compressed History)

```json
{
  "type": "summary",
  "id": "s_001",                    // Unique ID (s_ prefix)
  "ts": "2025-01-15T11:00:00Z",
  "covers": ["e_001", "e_002", "e_003"], // Entry IDs summarized
  "content": "User created a blog application with JWT authentication...",
  "original_tokens": 2500,          // Tokens before compression
  "summary_tokens": 150,            // Tokens after compression
  "preserved_facts": [              // Key facts extracted
    "uses PostgreSQL database",
    "has JWT authentication",
    "12 files created",
    "dark mode enabled"
  ],
  "checkpoint_refs": ["cp_001"]     // Related checkpoints
}
```

### Checkpoint Record (Project State Snapshot)

```json
{
  "type": "checkpoint",
  "id": "cp_001",                   // Unique ID (cp_ prefix)
  "ts": "2025-01-15T11:00:00Z",
  "trigger": "before_generation",   // What triggered checkpoint
  "description": "Before creating blog", // Human description
  "files_snapshot": {               // File hashes at this point
    "pages/index.py": "sha256:abc123...",
    "models/user.py": "sha256:def456..."
  },
  "rollback_id": "rb_456",          // ID for rollback operation
  "entry_ref": "e_002"              // Related conversation entry
}
```

**Checkpoint Triggers:**

| Trigger | Description |
|---------|-------------|
| `before_generation` | Auto before any file generation |
| `after_generation` | Auto after successful generation |
| `user_request` | User explicitly requested |
| `mode_change` | When switching modes |
| `rollback` | After a rollback operation |
| `cli` | Created via CLI command |

### Preference Record (Learned Preferences)

```json
{
  "type": "preference",
  "id": "pref_001",                 // Unique ID (pref_ prefix)
  "ts": "2025-01-15T11:30:00Z",
  "key": "database",                // Preference category
  "value": "PostgreSQL",            // Preferred value
  "confidence": 0.85                // Confidence score (0.0-1.0)
}
```

---

## CLI Commands

### View Memory

```bash
# Show recent entries
pynext memory show

# Show all entries including summaries
pynext memory show --all

# Search memory for specific content
pynext memory show --search "authentication"

# Limit number of results
pynext memory show --limit 20

# Show entries by role
pynext memory show --role user
```

### Statistics

```bash
pynext memory stats
```

**Example output:**
```
📊 Memory Statistics:
  ─────────────────────────────
  Entries:        45
  Summaries:      3
  Checkpoints:    5
  Preferences:    2
  ─────────────────────────────
  Total tokens:   15,000
  Active tokens:  5,000 (not summarized)
  ─────────────────────────────
  Pending sync:   0
  Last sync:      2025-01-15T10:30:00
  File size:      128 KB
```

### Sync & Persistence

```bash
# Force sync pending entries to disk
pynext memory flush

# Flush and summarize old entries
pynext memory flush --summarize

# Compact (remove summarized raw entries)
pynext memory compact

# Show sync status
pynext memory sync --status

# Pause automatic syncing
pynext memory sync --pause

# Resume automatic syncing
pynext memory sync --resume

# Full sync (compact + flush)
pynext memory sync --full
```

### Export Memory

```bash
# Export as markdown
pynext memory export > history.md

# Export as JSON
pynext memory export --format json > history.json
```

**Markdown export format:**
```markdown
# Session Memory Export
Project: my-app
Exported: 2025-01-15T12:00:00Z

## Conversation

### User (2025-01-15T10:01:00)
Create a blog with authentication

### Assistant (2025-01-15T10:01:30)
I'll create a blog with JWT auth...
Files: pages/index.py, api/auth.py

## Summaries

### Summary s_001 (covers e_001-e_005)
User created blog application...

## Preferences
- database: PostgreSQL (confidence: 0.9)
- mode: strict (confidence: 0.8)
```

### Clear Memory

```bash
# With confirmation (shows file status)
pynext memory clear

# Example interaction:
# > Clear all memory (file exists: True)? This cannot be undone. [y/N] y
# > ✅ Memory cleared (in-memory + disk)
# >    File: /path/to/project/.pynext/session.mem

# Without confirmation
pynext memory clear --force

# Only delete the .mem file (keep in-memory state for testing)
pynext memory clear --disk-only

# Example output:
# > ✅ Deleted memory file: /path/to/project/.pynext/session.mem
```

The clear command:
- Shows whether the `.mem` file exists before prompting
- Displays the full path to the deleted file
- With `--disk-only`: only deletes the file, preserves in-memory state

### Checkpoints

```bash
# List all checkpoints
pynext memory checkpoint --list

# Create a manual checkpoint
pynext memory checkpoint --create "before major refactor"

# Show diff between two checkpoints
pynext memory checkpoint --diff cp_abc123 cp_def456

# Rollback to a checkpoint
pynext memory rollback cp_abc123
```

---

## Session Commands

In `pynext app chat`, use `/memory` commands:

```
/memory show              Show recent entries
/memory show --all        Show everything including summaries
/memory show --search X   Search memory for X
/memory clear             Clear all memory (with confirmation)
/memory flush             Force save to disk
/memory stats             Show statistics
/memory sync --status     Show sync status
/memory sync --pause      Pause automatic sync
/memory sync --resume     Resume automatic sync
/memory checkpoint        Create checkpoint
```

### Example Session

```
You: Create a blog with authentication

AI: I'll create a blog with JWT authentication...
[Creates 12 files]

You: /memory stats
📊 Memory Statistics:
  Entries: 2
  Total tokens: 1,500
  Pending sync: 0

You: /memory checkpoint
✓ Checkpoint created: cp_abc123

You: Add dark mode toggle

AI: Adding dark mode using signals...
[Modifies 3 files]

You: /memory show --search "auth"
Found 2 results:
  e_001 [user]: Create a blog with authentication
  e_002 [assistant]: ...JWT authentication...
```

---

## Sync Configuration

Configure memory sync behavior in `pynext.toml`:

```toml
[memory]
# ========================================
# SYNC STRATEGY
# ========================================

# Mode: how to write to file
sync_mode = "incremental"  # incremental | full | manual

# When to auto-sync (list of triggers)
sync_on = [
  "assistant_response",  # After each AI response
  "checkpoint",          # When checkpoint created
  "exit",               # On session end
]

# Time-based sync (seconds, 0 = disabled)
sync_interval = 0

# Batch size before writing (0 = immediate)
sync_batch_size = 5

# ========================================
# WHAT TO SYNC
# ========================================

sync_entries = true
sync_summaries = true
sync_checkpoints = true
sync_preferences = true

# ========================================
# FILTERING
# ========================================

# Skip certain roles
exclude_roles = []  # e.g., ["system"]

# Skip short messages
min_content_length = 0

# Maximum entries before forcing flush
max_entries_in_memory = 1000

# ========================================
# FILE MANAGEMENT
# ========================================

# Rotate when file exceeds size
max_file_size_mb = 50
rotate_files = true
max_rotated_files = 5

# Compression
compress_on_sync = false
compress_threshold_mb = 10
```

### Sync Modes Explained

| Mode | Behavior | Use Case |
|------|----------|----------|
| `incremental` | Append new entries to file | **Default**. Fast, preserves history |
| `full` | Rewrite entire file on sync | After compaction, ensures consistency |
| `manual` | Only sync on explicit `flush` | Scripts, testing, full control |

### Sync Triggers

| Trigger | When Fired |
|---------|------------|
| `assistant_response` | After each AI response completes |
| `user_input` | After each user message |
| `checkpoint` | When a checkpoint is created |
| `exit` | On clean session termination |
| `error` | On errors (preserves context for debugging) |
| `summarize` | After summarization completes |
| `interval` | Every `sync_interval` seconds (if > 0) |

### Programmatic Sync Control

```python
from pynext.app.memory import SessionMemory

memory = SessionMemory(project_path=Path("."))

# Configure sync
memory.configure_sync(
    mode="incremental",
    triggers=["assistant_response", "exit"],
    batch_size=5,
)

# Pause/resume
memory.pause_sync()
# ... do operations without auto-sync ...
memory.resume_sync()

# Manual flush
count = memory.flush(force=True)
print(f"Synced {count} entries")

# Check status
print(f"Pending: {memory.pending_count}")
print(f"Last sync: {memory.last_sync}")
print(f"Paused: {memory.sync_paused}")
```

---

## Summarization

When conversation history grows large, the system automatically summarizes old entries to save tokens.

### When Summarization Triggers

```python
MAX_CONTEXT_TOKENS = 100_000
SUMMARY_THRESHOLD = 0.8  # 80%

# Summarize when:
if total_tokens > MAX_CONTEXT_TOKENS * SUMMARY_THRESHOLD:
    # total_tokens > 80,000
    summarize_old_entries()
```

### Summarization Process

```
┌──────────────────────────────────────────────────────────────┐
│                 SUMMARIZATION PROCESS                         │
└──────────────────────────────────────────────────────────────┘

1. SELECT ENTRIES TO SUMMARIZE
   ├── Keep last 10 entries intact (recent context)
   └── Select oldest N entries for summarization

2. EXTRACT KEY INFORMATION
   ├── Files created/modified
   ├── Technical decisions (DB, auth, etc.)
   ├── User preferences detected
   └── Errors and resolutions

3. GENERATE SUMMARY VIA LLM
   Prompt: "Summarize this conversation. Preserve:
            - All file names
            - User preferences
            - Technical choices
            - Errors and solutions"

4. CREATE SUMMARY RECORD
   ├── Link to original entry IDs (covers)
   ├── Store preserved_facts for quick lookup
   └── Track compression ratio

5. MARK ORIGINALS AS SUMMARIZED
   └── Flag entries, don't delete (for potential expansion)

6. LINK TO CHECKPOINTS
   └── Associate with checkpoints created during that period
```

### Summary Structure

```json
{
  "type": "summary",
  "id": "s_001",
  "covers": ["e_001", "e_002", "e_003", "e_004", "e_005"],
  "original_tokens": 2500,
  "summary_tokens": 150,
  "compression_ratio": 16.67,
  "content": "Session started. User created a blog application with JWT authentication (12 files: 3 pages, 2 models, 4 API routes, 2 islands, 1 layout). Database: PostgreSQL. Added dark mode toggle feature.",
  "preserved_facts": [
    "uses PostgreSQL database",
    "has JWT authentication",
    "12 files total",
    "dark mode enabled",
    "uses Tailwind CSS"
  ],
  "checkpoint_refs": ["cp_001", "cp_002"]
}
```

### Preserved Facts

Facts are extracted from summaries for **quick context lookup** without loading full summaries:

```python
# Get all preserved facts
facts = memory.get_preserved_facts()
# ["uses PostgreSQL", "has JWT auth", "12 files", ...]

# Facts are included in context building automatically
```

---

## Checkpoints

Checkpoints capture **project state at key moments** for rollback capability.

### Creating Checkpoints

```python
# Programmatic
cp_id = memory.add_checkpoint(
    trigger="user_request",
    description="Before adding authentication",
    files={
        "pages/index.py": "sha256:abc123...",
        "models/user.py": "sha256:def456...",
    },
    entry_ref="e_005",  # Link to conversation
)

# CLI
pynext memory checkpoint --create "Before major refactor"
```

### Checkpoint Triggers

| Trigger | When | Auto/Manual |
|---------|------|-------------|
| `before_generation` | Before file generation starts | Auto |
| `after_generation` | After successful generation | Auto |
| `user_request` | User explicitly requests | Manual |
| `mode_change` | When switching modes | Auto |
| `rollback` | After rollback operation | Auto |
| `cli` | Created via CLI | Manual |

### Listing and Comparing

```bash
# List checkpoints
pynext memory checkpoint --list

# Output:
# ID           Trigger            Description              Time
# cp_abc123    before_generation  Before blog creation     10:01:00
# cp_def456    after_generation   After blog creation      10:05:00
# cp_ghi789    user_request       Before auth changes      10:30:00

# Compare two checkpoints
pynext memory checkpoint --diff cp_abc123 cp_def456

# Output:
# Files added:
#   + pages/blog.py
#   + models/post.py
# Files modified:
#   ~ pages/index.py (hash changed)
# Files removed:
#   (none)
```

### Rollback

```bash
# Rollback to checkpoint
pynext memory rollback cp_abc123

# This will:
# 1. Show what will change
# 2. Ask for confirmation
# 3. Restore files to checkpoint state
# 4. Create a new checkpoint of current state (for undo)
```

---

## Context Building

The memory system builds **optimized context** for AI generation based on the current query.

### Priority Order

```
CONTEXT BUILDING PRIORITY
─────────────────────────

1. RECENT ENTRIES (always included)
   └── Last 3-5 conversation turns
   └── Most relevant for current task

2. PRESERVED FACTS (always included)
   └── Key facts from all summaries
   └── Compact, high-value information

3. USER PREFERENCES (always included)
   └── Learned preferences (database, style, etc.)
   └── Ensures consistency

4. RELEVANT SUMMARIES (semantic search)
   └── Summaries matching current query
   └── Provides historical context

5. RELEVANT OLD ENTRIES (if space remains)
   └── Specific entries matching query
   └── Deep context when needed
```

### Token Budget Strategy

```
TOTAL CONTEXT BUDGET: 8000 tokens (configurable)
─────────────────────────────────────────────────

┌─────────────────────────────────┬──────────────┐
│ Component                       │ Token Budget │
├─────────────────────────────────┼──────────────┤
│ Config/Standards                │ 500 (fixed)  │
│ Recent History (last 5)         │ 2000         │
│ Preserved Facts                 │ 200          │
│ Relevant Summaries              │ 500          │
│ Relevant Old Entries            │ 800          │
│ RAG Context (docs, patterns)    │ 3000         │
│ Current Request                 │ 1000         │
└─────────────────────────────────┴──────────────┘
```

### Context Building Code

```python
def get_relevant_context(self, query: str, max_tokens: int = 4000) -> str:
    """
    Build context from memory for current query.
    """
    context_parts = []
    remaining_tokens = max_tokens
    
    # 1. Recent entries (most important)
    recent = self.get_entries(limit=5)
    recent_text = self._format_entries(recent)
    context_parts.append(f"## Recent Conversation\n{recent_text}")
    remaining_tokens -= self._count_tokens(recent_text)
    
    # 2. Preserved facts (compact, always fit)
    facts = self.get_preserved_facts()
    if facts:
        facts_text = "## Key Facts\n" + "\n".join(f"- {f}" for f in facts)
        context_parts.append(facts_text)
        remaining_tokens -= self._count_tokens(facts_text)
    
    # 3. User preferences
    prefs = self.get_preferences()
    if prefs:
        prefs_text = "## User Preferences\n" + "\n".join(
            f"- {k}: {v}" for k, v in prefs.items()
        )
        context_parts.append(prefs_text)
        remaining_tokens -= self._count_tokens(prefs_text)
    
    # 4. Relevant summaries (semantic search)
    if remaining_tokens > 500:
        relevant_summaries = self._search_summaries(query, k=3)
        for summary in relevant_summaries:
            if remaining_tokens < 200:
                break
            context_parts.append(f"## Earlier: {summary.content}")
            remaining_tokens -= summary.summary_tokens
    
    # 5. Relevant old entries (if space)
    if remaining_tokens > 300:
        relevant_entries = self.search(query, k=5)
        for entry in relevant_entries:
            if remaining_tokens < 100:
                break
            if not entry.summarized:  # Don't duplicate
                context_parts.append(self._format_entry(entry))
                remaining_tokens -= entry.tokens
    
    return "\n\n".join(context_parts)
```

---

## Python API Reference

### SessionMemory Class

```python
from pynext.app.memory import SessionMemory, SyncConfig

class SessionMemory:
    """Persistent memory with automatic summarization."""
    
    def __init__(
        self,
        project_path: Path,
        sync_config: Optional[SyncConfig] = None,
    ):
        """
        Initialize session memory.
        
        Args:
            project_path: Project root directory
            sync_config: Sync configuration (uses defaults if None)
        """
```

### Core Methods

```python
# ========================================
# LOADING & SAVING
# ========================================

def load(self) -> bool:
    """Load memory from .mem file. Returns True if loaded."""
    
def flush(self, force: bool = False) -> int:
    """
    Flush pending entries to disk.
    
    Args:
        force: If True, flush even if paused
        
    Returns:
        Number of records written
    """

def clear(self, disk_only: bool = False) -> Optional[Path]:
    """
    Clear all memory.
    
    Args:
        disk_only: If True, only delete file, keep in-memory state
        
    Returns:
        Path to deleted file if it existed
    """

def compact(self) -> None:
    """Remove summarized entries from file."""

# ========================================
# ADDING RECORDS
# ========================================

def add(
    self,
    role: str,              # "user", "assistant", "system"
    content: str,           # Message content
    metadata: Dict[str, Any], # Optional metadata
) -> str:
    """
    Add a conversation entry.
    
    Returns:
        Entry ID (e_xxx)
    """

def add_checkpoint(
    self,
    trigger: str,           # What triggered this
    description: str,       # Human description
    files: Dict[str, str],  # path -> hash mapping
    entry_ref: Optional[str] = None,  # Related entry
) -> str:
    """
    Create a project checkpoint.
    
    Returns:
        Checkpoint ID (cp_xxx)
    """

def add_preference(
    self,
    key: str,               # Preference category
    value: str,             # Preferred value
    confidence: float,      # Confidence score (0.0-1.0)
) -> str:
    """
    Record a user preference.
    
    Returns:
        Preference ID (pref_xxx)
    """

# ========================================
# RETRIEVAL
# ========================================

def get_entries(self, limit: Optional[int] = None) -> List[MemoryEntry]:
    """Get entries, most recent first."""

def get_checkpoints(self, limit: int = 10) -> List[Checkpoint]:
    """Get checkpoints, most recent first."""

def get_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
    """Get specific checkpoint by ID."""

def get_preferences(self) -> Dict[str, str]:
    """Get all preferences as key->value dict."""

def get_preserved_facts(self) -> List[str]:
    """Get all preserved facts from summaries."""

# ========================================
# SEARCH
# ========================================

def search(self, query: str, k: int = 5) -> List[MemoryEntry]:
    """
    Search entries by content.
    
    Args:
        query: Search query
        k: Maximum results
        
    Returns:
        Matching entries, sorted by relevance
    """

def get_relevant_context(
    self,
    query: str,
    max_tokens: int = 4000,
) -> str:
    """
    Build context string for AI generation.
    
    Args:
        query: Current user query
        max_tokens: Maximum tokens in context
        
    Returns:
        Formatted context string
    """

# ========================================
# SUMMARIZATION
# ========================================

async def summarize_old(
    self,
    keep_recent: int = 10,
) -> Optional[str]:
    """
    Summarize old entries to compress context.
    
    Args:
        keep_recent: Number of recent entries to keep
        
    Returns:
        Summary ID if created, None otherwise
    """

# ========================================
# SYNC CONTROL
# ========================================

def configure_sync(
    self,
    mode: Optional[str] = None,
    triggers: Optional[List[str]] = None,
    batch_size: Optional[int] = None,
    **kwargs,
) -> None:
    """Configure sync behavior."""

def pause_sync(self) -> None:
    """Pause automatic syncing."""

def resume_sync(self) -> None:
    """Resume automatic syncing."""

@property
def pending_count(self) -> int:
    """Number of entries waiting to be synced."""

@property
def sync_paused(self) -> bool:
    """Whether sync is currently paused."""

# ========================================
# EXPORT
# ========================================

def export(self, format: str = "markdown") -> str:
    """
    Export memory to string.
    
    Args:
        format: "markdown" or "json"
        
    Returns:
        Exported content
    """

def stats(self) -> Dict[str, Any]:
    """
    Get memory statistics.
    
    Returns:
        Dict with entries, summaries, checkpoints,
        preferences, total_tokens, etc.
    """
```

### SyncConfig Dataclass

```python
from dataclasses import dataclass

@dataclass
class SyncConfig:
    """Configuration for memory sync behavior."""
    
    mode: str = "incremental"     # incremental, full, manual
    triggers: List[str] = field(default_factory=lambda: [
        "assistant_response",
        "checkpoint", 
        "exit"
    ])
    batch_size: int = 5           # Entries before auto-flush
    interval: int = 0             # Seconds (0 = disabled)
    
    # What to sync
    sync_entries: bool = True
    sync_summaries: bool = True
    sync_checkpoints: bool = True
    sync_preferences: bool = True
    
    # Filtering
    exclude_roles: List[str] = field(default_factory=list)
    min_content_length: int = 0
    max_entries_in_memory: int = 1000
```

### Data Classes

```python
@dataclass
class MemoryEntry:
    id: str
    timestamp: datetime
    role: str
    content: str
    tokens: int
    metadata: Dict[str, Any]
    summarized: bool = False

@dataclass
class MemorySummary:
    id: str
    timestamp: datetime
    covers: List[str]       # Entry IDs
    content: str
    original_tokens: int
    summary_tokens: int
    preserved_facts: List[str]
    checkpoint_refs: List[str] = field(default_factory=list)

@dataclass
class Checkpoint:
    id: str
    timestamp: datetime
    trigger: str
    description: str
    files_snapshot: Dict[str, str]  # path -> hash
    rollback_id: Optional[str] = None
    entry_ref: Optional[str] = None

@dataclass
class Preference:
    id: str
    timestamp: datetime
    key: str
    value: str
    confidence: float
```

### Global Functions

```python
from pynext.app.memory import get_memory, reset_memory

# Get singleton instance
memory = get_memory(project_path=Path("."))

# Reset (for testing)
reset_memory()
```

---

## Token Budget Strategy

### Default Budget Allocation

```
┌─────────────────────────────────────────────────────────────────┐
│              TOTAL CONTEXT: 8,000 tokens                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────┐                       │
│  │ Config & Standards (500)             │ Fixed overhead        │
│  └──────────────────────────────────────┘                       │
│                                                                 │
│  ┌──────────────────────────────────────┐                       │
│  │ Recent History (2000)                │ Last 3-5 exchanges    │
│  │ - Most important for continuity      │                       │
│  └──────────────────────────────────────┘                       │
│                                                                 │
│  ┌──────────────────────────────────────┐                       │
│  │ Preserved Facts + Prefs (200)        │ Compact summaries     │
│  └──────────────────────────────────────┘                       │
│                                                                 │
│  ┌──────────────────────────────────────┐                       │
│  │ Relevant Summaries (500)             │ Historical context    │
│  └──────────────────────────────────────┘                       │
│                                                                 │
│  ┌──────────────────────────────────────┐                       │
│  │ RAG Context (3000)                   │ Docs, patterns        │
│  └──────────────────────────────────────┘                       │
│                                                                 │
│  ┌──────────────────────────────────────┐                       │
│  │ Current Request (1000)               │ User's prompt         │
│  └──────────────────────────────────────┘                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Adjusting Budget

```python
# Smaller budget (faster, less context)
context = memory.get_relevant_context(query, max_tokens=2000)

# Larger budget (more context, slower)
context = memory.get_relevant_context(query, max_tokens=8000)
```

---

## Best Practices

### 1. Let Auto-Save Work

Default settings are optimized for most use cases:

```toml
[memory]
sync_mode = "incremental"
sync_on = ["assistant_response", "checkpoint", "exit"]
sync_batch_size = 5
```

### 2. Create Checkpoints Before Big Changes

```bash
# Before refactoring
pynext memory checkpoint --create "before auth refactor"

# Before trying experimental approach
pynext memory checkpoint --create "stable state before experiment"
```

### 3. Use Search to Find Context

```bash
# Find related history
pynext memory show --search "authentication"
pynext memory show --search "error"
```

### 4. Compact Periodically

```bash
# After many summarizations
pynext memory compact

# Removes raw entries that are already summarized
# Keeps file size manageable
```

### 5. Export for Sharing

```bash
# Share context with team member
pynext memory export > session-context.md

# They can review and understand the project history
```

### 6. Clear Between Unrelated Projects

```bash
# Starting fresh project in same directory
pynext memory clear --force
```

---

## Troubleshooting

### Memory Not Loading

```bash
# Check file exists
ls -la .pynext/session.mem

# Check file is valid JSONL
head -5 .pynext/session.mem

# Show stats (will report if load failed)
pynext memory stats
```

### Sync Issues

```bash
# Check sync status
pynext memory sync --status

# Output shows:
# - Pending count
# - Last sync time
# - Sync paused status

# Force sync
pynext memory flush --force

# Check for write permissions
ls -la .pynext/
```

### File Too Large

```bash
# Check current size
ls -lh .pynext/session.mem

# Compact (removes summarized raw entries)
pynext memory compact

# Check size after
ls -lh .pynext/session.mem
```

### Lost Entries

```bash
# Check if entries are in summaries
pynext memory show --all

# Export to review everything
pynext memory export > review.md

# Search for specific content
pynext memory show --search "lost content"
```

### Context Too Short

```python
# Increase token budget
context = memory.get_relevant_context(
    query="add auth",
    max_tokens=8000  # Increase from default 4000
)
```

### Malformed File

```bash
# Backup current file
cp .pynext/session.mem .pynext/session.mem.bak

# Try loading (malformed lines are skipped)
pynext memory stats

# If many lines corrupted, may need manual fix:
# 1. Open file
# 2. Remove malformed lines
# 3. Ensure first line is meta record
```

---

## Integration Examples

### With App Generator

```python
from pynext.app.generator import AppGenerator
from pynext.app.memory import SessionMemory

memory = SessionMemory(project_path=Path("."))
memory.load()

generator = AppGenerator(
    project_path=Path("."),
    memory=memory,  # Pass memory for context
)

# Memory is used automatically for context
await generator.generate_file(
    file_type="api",
    name="users",
    description="User management API",
)
```

### With Configuration

```python
from pynext.app.config import PyNextConfig
from pynext.app.memory import SessionMemory

config = PyNextConfig.load(Path("."))
memory = SessionMemory(
    project_path=Path("."),
    sync_config=config.memory,  # Use config's memory settings
)
```

### In Custom Script

```python
from pathlib import Path
from pynext.app.memory import SessionMemory

# Initialize
memory = SessionMemory(project_path=Path("."))
memory.load()

# Record conversation
memory.add("user", "Create a REST API for users", {})
memory.add("assistant", "I'll create a users API...", {
    "files": ["api/users.py", "models/user.py"]
})

# Create checkpoint
memory.add_checkpoint(
    trigger="user_request",
    description="After user API",
    files={"api/users.py": "sha256:..."}
)

# Get context for next operation
context = memory.get_relevant_context("add authentication")

# Save
memory.flush()
```