# PyNext Session Memory

Persistent conversation memory with automatic summarization for the AI App Builder.

## Overview

The PyNext memory system provides:

- **Persistent history** - Conversation saved across sessions
- **Automatic summarization** - Compress old context when it gets large
- **Checkpoints** - Snapshots for rollback
- **Preferences** - Learned user preferences
- **Configurable sync** - Control when/how memory is saved

## Quick Start

```bash
# View recent memory
pynext memory show

# Show statistics
pynext memory stats

# Create a checkpoint
pynext memory checkpoint --create "before refactor"

# Clear memory
pynext memory clear
```

## Memory File

Memory is stored in `.pynext/session.mem` as JSON Lines (JSONL):

```
project/
├── .pynext/
│   └── session.mem    # Project memory
└── ...

~/.pynext/
└── global.mem         # Global memory (cross-project)
```

### Record Types

```jsonl
{"type":"meta","v":1,"created":"2025-01-15T10:00:00Z","project":"my-app"}
{"type":"entry","id":"e_001","ts":"...","role":"user","content":"Create a blog","tokens":12}
{"type":"entry","id":"e_002","ts":"...","role":"assistant","content":"I'll create...","tokens":450,"meta":{"files":["pages/index.py"]}}
{"type":"summary","id":"s_001","ts":"...","covers":["e_001","e_002"],"content":"Created blog with 12 files.","preserved_facts":["uses PostgreSQL"]}
{"type":"checkpoint","id":"cp_001","ts":"...","trigger":"before_generation","description":"Before blog","files_snapshot":{...}}
{"type":"preference","id":"pref_001","ts":"...","key":"mode","value":"strict","confidence":0.8}
```

| Type | Purpose |
|------|---------|
| `meta` | File metadata (version, created date) |
| `entry` | Conversation turn (user/assistant) |
| `summary` | Compressed old entries |
| `checkpoint` | Project state snapshot |
| `preference` | Learned user preference |

## CLI Commands

### View Memory

```bash
# Show recent entries
pynext memory show

# Show all entries including summaries
pynext memory show --all

# Search memory
pynext memory show --search "authentication"

# Limit results
pynext memory show --limit 20
```

### Statistics

```bash
pynext memory stats
```

Output:
```
📊 Memory Statistics:
  Entries: 45
  Summaries: 3
  Checkpoints: 5
  Preferences: 2
  Total tokens: 15000
  Active tokens: 5000
  Pending sync: 0
  Last sync: 2025-01-15T10:30:00
```

### Sync & Persistence

```bash
# Force sync to disk
pynext memory flush

# Flush and summarize old entries
pynext memory flush --summarize

# Compact (remove summarized entries)
pynext memory compact

# Sync status
pynext memory sync --status

# Pause/resume auto-sync
pynext memory sync --pause
pynext memory sync --resume

# Full sync (compact + flush)
pynext memory sync --full
```

### Export

```bash
# Export as markdown
pynext memory export > history.md

# Export as JSON
pynext memory export --format json > history.json
```

### Clear Memory

```bash
# With confirmation
pynext memory clear

# Without confirmation
pynext memory clear --force
```

### Checkpoints

```bash
# List checkpoints
pynext memory checkpoint --list

# Create checkpoint
pynext memory checkpoint --create "before major refactor"

# Show diff between checkpoints
pynext memory checkpoint --diff cp_abc123 cp_def456
```

## Session Commands

In `pynext app chat`, use `/memory` commands:

```
/memory show              Show recent entries
/memory show --all        Show everything
/memory show --search X   Search memory
/memory clear             Clear memory
/memory flush             Save to disk
/memory stats             Show statistics
/memory sync --status     Sync status
```

## Sync Configuration

Configure sync behavior in `pynext.toml`:

```toml
[memory]
# Sync strategy
sync_mode = "incremental"  # incremental, full, manual

# When to auto-sync
sync_on = ["assistant_response", "checkpoint", "exit"]

# Batch size before writing
sync_batch_size = 5

# What to sync
sync_entries = true
sync_summaries = true
sync_checkpoints = true
sync_preferences = true

# Filtering
exclude_roles = []
min_content_length = 0
max_entries_in_memory = 1000

# File management
max_file_size_mb = 50
rotate_files = true
max_rotated_files = 5
```

### Sync Modes

| Mode | Behavior |
|------|----------|
| `incremental` | Append new entries (fast, default) |
| `full` | Rewrite entire file (after compact) |
| `manual` | Only sync on explicit `flush` |

### Sync Triggers

| Trigger | When |
|---------|------|
| `assistant_response` | After each AI response |
| `user_input` | After each user message |
| `checkpoint` | When checkpoint created |
| `exit` | On session end |
| `error` | On errors |
| `summarize` | After summarization |

## Summarization

When conversation gets too long, old entries are summarized:

```
When: total_tokens > 80,000 (80% of max)

1. Select oldest entries (keep last 10)
2. Extract key information:
   - Files created/modified
   - Decisions made
   - Preferences learned
3. Generate summary via LLM
4. Mark original entries as summarized
5. Keep preserved facts for quick lookup
```

### Summary Structure

```jsonl
{
  "type": "summary",
  "id": "s_001",
  "covers": ["e_001", "e_002", "e_003"],
  "content": "User created a blog with auth (12 files)...",
  "original_tokens": 2500,
  "summary_tokens": 150,
  "preserved_facts": [
    "uses PostgreSQL",
    "has JWT auth",
    "dark mode enabled"
  ],
  "checkpoint_refs": ["cp_001"]
}
```

## Context Building

Memory provides context for AI generation:

```python
# Get relevant context for current query
context = memory.get_relevant_context(
    query="add dark mode",
    max_tokens=4000
)
```

**Priority order:**
1. Recent entries (last 5) - always included
2. Preserved facts - always included
3. Relevant summaries - semantic search
4. Relevant old entries - keyword search

## Python API

```python
from pynext.app.memory import SessionMemory, SyncConfig

# Initialize
memory = SessionMemory(
    project_path=Path("."),
    sync_config=SyncConfig(mode="incremental"),
)

# Load from file
memory.load()

# Add entries
entry_id = memory.add("user", "Create a blog", {})
memory.add("assistant", "I'll create...", {"files": ["pages/index.py"]})

# Add checkpoint
cp_id = memory.add_checkpoint(
    trigger="user_request",
    description="Before refactor",
    files={"pages/index.py": "sha256:abc123"},
)

# Add preference
memory.add_preference("mode", "strict", confidence=0.9)

# Search
results = memory.search("authentication", k=5)

# Get context for AI
context = memory.get_relevant_context("add user auth", max_tokens=4000)

# Save to disk
memory.flush()

# Summarize old entries
await memory.summarize_old(keep_recent=10)

# Export
markdown = memory.export("markdown")

# Clear
memory.clear()
```

### SyncConfig Options

```python
SyncConfig(
    mode="incremental",           # incremental, full, manual
    triggers=["assistant_response", "exit"],
    batch_size=5,
    interval=0,                   # 0 = disabled
    sync_entries=True,
    sync_summaries=True,
    sync_checkpoints=True,
    sync_preferences=True,
    exclude_roles=[],
    min_content_length=0,
    max_entries_in_memory=1000,
)
```

## Checkpoints

Checkpoints capture project state for rollback:

```python
# Create checkpoint
cp_id = memory.add_checkpoint(
    trigger="before_generation",
    description="Before adding auth",
    files={"pages/index.py": "sha256:abc123"},
    entry_ref="e_005",  # Link to conversation
)

# Get checkpoint
cp = memory.get_checkpoint("cp_abc123")

# List checkpoints
checkpoints = memory.get_checkpoints(limit=10)
```

### Checkpoint Triggers

| Trigger | When |
|---------|------|
| `before_generation` | Auto before file generation |
| `after_generation` | Auto after successful generation |
| `user_request` | User explicitly requested |
| `mode_change` | When switching modes |
| `rollback` | After a rollback operation |
| `cli` | Created via CLI |

## Best Practices

1. **Let it auto-save** - Default settings work well
2. **Create checkpoints** - Before big changes
3. **Use search** - Find relevant history
4. **Compact periodically** - Keep file size manageable
5. **Export for sharing** - Share context with team

## Troubleshooting

### Memory not loading

```bash
# Check file exists
ls -la .pynext/session.mem

# Show stats
pynext memory stats
```

### Sync issues

```bash
# Check sync status
pynext memory sync --status

# Force sync
pynext memory flush
```

### File too large

```bash
# Compact to remove summarized entries
pynext memory compact

# Check size after
ls -lh .pynext/session.mem
```

### Lost entries

```bash
# Check if entries are in summaries
pynext memory show --all

# Export to review
pynext memory export > review.md
```

