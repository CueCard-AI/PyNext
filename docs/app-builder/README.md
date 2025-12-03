# AI App Builder

Build entire PyNext applications from natural language descriptions using the AI App Builder.

## Overview

The PyNext App Builder is a Cursor-like AI application builder that can:

1. **Create entire applications** from natural language descriptions
2. **Show plans and get approval** before generating (like Cursor)
3. **Support multiple modes**: plan, agent, ask
4. **Add features** to existing projects
5. **Scale from small to large** applications (3 to 50+ files)

## Quick Start

```bash
# Create a new application
pynext app new "task manager with user auth and real-time updates"

# Add a feature to existing project
pynext app add "dark mode toggle"

# Interactive chat session
pynext app chat
```

## CLI Commands

### `pynext app new`

Create a new application from a description.

```bash
pynext app new "your app description" [options]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--output, -o` | Output directory (default: derived from description) |
| `--mode, -m` | Generation mode: `plan`, `agent`, `ask` (default: plan) |
| `--complexity, -c` | App complexity: `auto`, `minimal`, `small`, `medium`, `large`, `enterprise` |
| `--model` | AI model to use |
| `--dry-run` | Show plan without executing |
| `--no-confirm` | Skip confirmation prompts |

**Examples:**

```bash
# Create a blog with auto-detected complexity
pynext app new "blog with posts, categories, and comments"

# Create a medium-complexity e-commerce site
pynext app new "e-commerce site with products and cart" --complexity medium

# Autonomous mode (no prompts)
pynext app new "portfolio website" --mode agent

# Show plan only
pynext app new "SaaS dashboard" --dry-run
```

### `pynext app add`

Add a feature to an existing project.

```bash
pynext app add "feature description" [options]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--dir` | Project directory (default: current directory) |
| `--mode, -m` | Generation mode: `plan`, `agent`, `ask` |
| `--model` | AI model to use |

**Examples:**

```bash
# Add dark mode to current project
pynext app add "dark mode toggle"

# Add feature with step-by-step approval
pynext app add "admin dashboard" --mode ask

# Add to specific project
pynext app add "authentication" --dir ./my-project
```

### `pynext app chat`

Start an interactive chat session for building applications.

```bash
pynext app chat [--dir project_path]
```

In the chat session, you can:

- Describe what you want to build
- Add features incrementally
- View and modify plans
- Execute plans when ready

**Session Commands:**

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/plan` | Show current plan |
| `/execute` | Execute current plan |
| `/mode <mode>` | Change mode (plan/agent/ask) |
| `/files` | List project files |
| `/status` | Show session status |
| `/quit` | Exit session |

## Generation Modes

### Plan Mode (Default)

1. Creates a plan with all files to generate
2. Displays the plan for review
3. Waits for approval
4. Generates all files in order
5. Shows progress

Best for: Most use cases, learning, important projects

### Agent Mode

1. Creates a plan
2. Immediately generates all files
3. Reports results

Best for: Quick scaffolding, scripting, experienced users

### Ask Mode

1. Creates a plan
2. For each file:
   - Shows a preview
   - Asks for approval
   - Generates if approved
3. Can skip individual files

Best for: Learning, critical projects, partial generation

## Complexity Levels

| Level | Files | Example |
|-------|-------|---------|
| `minimal` | 3-5 | Landing page with contact form |
| `small` | 5-10 | Blog with auth |
| `medium` | 10-30 | Full-stack CRUD app |
| `large` | 30-50 | E-commerce with dashboard |
| `enterprise` | 50+ | Full SaaS application |

The `auto` complexity (default) analyzes your description to determine the appropriate level.

## PyNext Knowledge Base (RAG)

Since **no AI model is natively trained on PyNext**, the App Builder includes a sophisticated RAG (Retrieval-Augmented Generation) system. This is critical because:

- PyNext is a new framework not in LLM training data
- Unique syntax patterns (`class_=`, `input_`, Signal patterns)
- Without RAG, AI would guess wrong imports and syntax

### RAG Architecture

```
User Request: "task manager with drag-drop boards"
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│                     1. INDEXING (One-time)                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   KnowledgeIndexer scans:                                   │
│   ├── docs/*.md → Split by ## headers, extract code blocks │
│   ├── pynext/*.py → Extract docstrings, signatures         │
│   └── Creates IndexedChunks with topics (routing, state...)│
│                                                              │
│   Each chunk gets:                                          │
│   - Unique ID (hash)                                        │
│   - Content                                                 │
│   - Source file                                             │
│   - Type: docs, code, example, api                         │
│   - Topics: [routing, state, database, auth, ...]          │
│   - Embedding vector (optional)                            │
└─────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│                     2. RETRIEVAL                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   SemanticRetriever.search("drag drop interactive")         │
│                                                              │
│   Scoring = Keyword Match (30%) + Semantic Similarity (70%) │
│                                                              │
│   Returns ranked results:                                    │
│   ├── Score 0.89: islands.md "Interactive Components"       │
│   ├── Score 0.82: @island decorator API                     │
│   ├── Score 0.76: Signal state management docs              │
│   └── Score 0.71: example DragDrop component                │
└─────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│                  3. PATTERN MATCHING                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   PatternLibrary.get_patterns_for("drag drop boards")       │
│                                                              │
│   Matches keywords to patterns:                              │
│   ├── "interactive" → island_component                      │
│   ├── "state" → signal_state                                │
│   ├── "database" → database_model                           │
│   └── "page" → basic_page, page_with_data                   │
│                                                              │
│   Each pattern has:                                          │
│   - Code template with placeholders                          │
│   - Required imports                                         │
│   - Related patterns                                         │
└─────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│                 4. CONTEXT BUILDING                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ContextBuilder.build_context(task, max_tokens=8000)       │
│                                                              │
│   Assembles optimal prompt:                                  │
│   ┌────────────────────────────────────────┐                │
│   │ ## PyNext Overview (always included)   │ Priority: 100  │
│   │ - HTML elements, Signals, Islands      │                │
│   │ - Server Actions, API routes           │                │
│   └────────────────────────────────────────┘                │
│   ┌────────────────────────────────────────┐                │
│   │ ## Relevant Patterns                   │ Priority: 90   │
│   │ - island_component template            │                │
│   │ - signal_state template                │                │
│   └────────────────────────────────────────┘                │
│   ┌────────────────────────────────────────┐                │
│   │ ## Existing Files (for imports)        │ Priority: 85   │
│   │ - pages/layout.py signatures           │                │
│   └────────────────────────────────────────┘                │
│   ┌────────────────────────────────────────┐                │
│   │ ## Retrieved Documentation             │ Priority: 80   │
│   │ - Islands.md excerpts                  │                │
│   └────────────────────────────────────────┘                │
│                                                              │
│   Sections sorted by priority, fit within token budget      │
└─────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│                 5. AI GENERATION                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   FileGenerator sends to Claude:                             │
│                                                              │
│   SYSTEM: [PyNext context from ContextBuilder]               │
│                                                              │
│   USER: Generate a PyNext island file.                       │
│         File: islands/DragDrop.py                           │
│         Description: Drag-drop board component              │
│         Requirements: {...}                                  │
│                                                              │
│   Claude generates valid PyNext code because it has:         │
│   ✓ Correct import statements                                │
│   ✓ Proper @island decorator usage                          │
│   ✓ Signal patterns for state                               │
│   ✓ PyNext HTML element syntax                              │
└─────────────────────────────────────────────────────────────┘
```

### Why RAG is Critical

**Problem**: Without context, AI generates broken code:

```python
# ❌ Without RAG (AI guesses wrong)
from pynext import div

def Component():
    return div(class="container")  # WRONG: should be class_=
```

**Solution**: With RAG, AI knows PyNext syntax:

```python
# ✅ With RAG (AI knows correct patterns)
from pynext import div, Signal
from pynext.islands import island

@island
def Counter():
    count = Signal(0)
    return div(class_="container")(  # CORRECT: class_= syntax
        button(on_click=lambda: count.set(count() + 1))(
            f"Count: {count()}"
        )
    )
```

### RAG Components

#### 1. KnowledgeIndexer (`pynext/app/knowledge/indexer.py`)

Indexes all PyNext documentation and source code:

```python
indexer = KnowledgeIndexer(project_root)
await indexer.index_all()

# Creates chunks like:
IndexedChunk(
    id="abc123",
    content="@island decorator makes components interactive...",
    source_path="docs/islands.md",
    metadata={"type": "documentation"},
    topics=["islands", "interactive", "reactivity"],
)
```

#### 2. SemanticRetriever (`pynext/app/knowledge/retriever.py`)

Performs semantic + keyword hybrid search:

```python
retriever = SemanticRetriever(indexer, embedding_provider)

# Search for relevant content
results = retriever.search(
    "drag and drop component",
    top_k=10,
    filters={"type": "docs"}
)

# Returns ranked SearchResult objects
# SearchResult(chunk=..., relevance_score=0.89, keyword_score=0.6, total_score=0.8)
```

#### 3. PatternLibrary (`pynext/app/knowledge/patterns.py`)

16 curated PyNext patterns with code templates:

```python
Pattern(
    name="island_component",
    description="Interactive component with client-side state",
    code='''
@island
def ${component_name}(${props}):
    ${state_name} = Signal(${initial_state})
    
    def ${handler_name}():
        ${handler_body}
    
    return div(class_="${container_class}")(
        ${content}
    )
''',
    required_imports=[
        "from pynext import div, button",
        "from pynext import Signal",
        "from pynext.islands import island",
    ],
    tags=["island", "reactivity", "signal", "component"],
)
```

#### 4. EmbeddingProvider (`pynext/app/knowledge/embeddings.py`)

Generates vector embeddings for semantic search:

```python
# Local embeddings (no API needed)
provider = EmbeddingProvider()  # Uses sentence-transformers

# Generate embedding
embedding = await provider.get_embedding("drag drop component")
# Returns: [0.23, -0.45, 0.12, ...] (384-dim vector)
```

#### 5. ContextBuilder (`pynext/app/knowledge/context_builder.py`)

Assembles optimal context within token budget:

```python
builder = ContextBuilder(retriever, pattern_library)

context = builder.build_context(
    user_query="Create a drag-drop kanban board",
    current_files={"pages/layout.py": "..."},
    relevant_chunks=retriever.search(...),
)

# Returns formatted string with:
# - PyNext framework overview
# - Relevant patterns
# - Documentation excerpts
# - Existing file signatures
```

### How It Works Together

```python
# Inside FileGenerator.generate_file()

# 1. Search knowledge base
relevant_chunks = self.knowledge.search(
    f"PyNext {file_type} {description}",
    top_k=5
)

# 2. Get relevant patterns
patterns = self.knowledge.pattern_library.get_patterns_for(file_type)

# 3. Build context with token budget
context = self.knowledge.build_context(
    user_query=description,
    current_files=previously_generated_files,
    relevant_chunks=relevant_chunks,
)

# 4. Generate with Claude
response = await self.client.messages.create(
    model=self.config.model,
    system=context,  # Full PyNext knowledge injected here
    messages=[{"role": "user", "content": generation_prompt}],
)
```

### Pattern Library (16 Patterns)

The App Builder includes 16 curated patterns for common PyNext code:

| Category | Pattern | Description |
|----------|---------|-------------|
| **Pages** | `basic_page` | Simple static page with SEO |
| | `page_with_data` | Page with async data fetching |
| | `dynamic_route_page` | Dynamic routes (`[id].py`) |
| **Components** | `static_component` | Reusable UI component |
| | `component_with_props` | Component accepting props |
| | `island_component` | Interactive island with state |
| **State** | `signal_state` | Reactive state with Signal |
| | `computed_value` | Derived values with Computed |
| | `effect_side_effect` | Side effects with Effect |
| **Data** | `database_model` | Table model definition |
| | `api_crud` | Full CRUD API endpoints |
| | `server_action` | Form handling action |
| **Auth** | `auth_middleware` | Route protection middleware |
| | `protected_page` | Page requiring authentication |
| | `login_form` | Login page and form |
| **Real-time** | `websocket_connection` | WebSocket integration |
| | `live_query` | Live database queries with `Model.live()` |

**Example Pattern Usage:**

```python
from pynext.app.knowledge import PatternLibrary

patterns = PatternLibrary()

# Get a specific pattern
island_pattern = patterns.get_pattern("island_component")

# Render with variables
code = island_pattern.render(
    component_name="Counter",
    state_name="count",
    initial_state="0",
    handler_name="increment",
    handler_body="count.set(count() + 1)",
)
```

## App Templates

Pre-defined structures for common app types:

### Blog

```bash
pynext app new "blog"
```

Creates:
- Home page with post list
- Post detail page
- Admin dashboard
- Post, Category, Comment models
- CRUD APIs
- Comment form island

### SaaS

```bash
pynext app new "SaaS application"
```

Creates:
- Landing page
- Login/Signup pages
- Dashboard with sidebar
- User settings
- Team management
- Auth middleware
- User/Organization models

### E-commerce

```bash
pynext app new "e-commerce store"
```

Creates:
- Product catalog
- Product detail pages
- Shopping cart
- Checkout flow
- Order history
- Product, Cart, Order models
- Interactive cart components

### Dashboard

```bash
pynext app new "admin dashboard"
```

Creates:
- Overview with stats
- User management
- Analytics charts
- Settings page
- Real-time statistics
- Activity logging

## Example Session

### Creating a New App (Plan Mode)

```
$ pynext app new "task manager with user auth, drag-drop boards, and real-time sync"

🤖 Creating new application...
   Description: task manager with user auth, drag-drop boards, and real-time sync
   Mode: plan
   Complexity: auto

🔍 Analyzing requirements...

# App Plan: task-manager

**Description:** task manager with user auth, drag-drop boards, and real-time sync
**Complexity:** medium (18 files)
**Estimated Time:** 2-3 minutes

## Files to Create

1. ✨ `pages/layout.py` - Application layout
2. ✨ `pages/index.py` - Landing page
3. ✨ `pages/login.py` - Auth login
4. ✨ `pages/signup.py` - Auth signup
5. ✨ `pages/dashboard.py` - Main dashboard
6. ✨ `pages/board/[id].py` - Board detail view
7. ✨ `components/TaskCard.py` - Draggable task card
8. ✨ `components/Board.py` - Kanban board
9. ✨ `islands/DragDrop.py` - Drag-drop interactivity
10. ✨ `models/user.py` - User model
11. ✨ `models/board.py` - Board model
12. ✨ `models/task.py` - Task model
13. ✨ `api/boards.py` - Board CRUD API
14. ✨ `api/tasks.py` - Task CRUD API
15. ✨ `api/ws/sync.py` - WebSocket sync
16. ✨ `actions/auth.py` - Auth actions
17. ✨ `middleware/auth.py` - Auth middleware
18. ✨ `styles/globals.css` - Global styles

## Required Packages

- pynext[db] (PostgreSQL)
- pynext[auth] (Authentication)
- pynext[realtime] (WebSocket)

Proceed? [Y/n/edit] y

🚀 Generating...

  [1/18] Creating pages/layout.py... ✓
  [2/18] Creating pages/index.py... ✓
  ...
  [18/18] Creating styles/globals.css... ✓

──────────────────────────────────────────────────────
✅ Generation complete!

  Files created: 18
  Total time:    45.2s

Next steps:
  cd task-manager
  pynext db init
  pynext dev
```

### Adding a Feature (Ask Mode)

```
$ pynext app add "dark mode toggle" --mode ask

🔧 Adding feature to /Users/you/task-manager...
   Feature: dark mode toggle
   Mode: ask

🔍 Analyzing project...

# Feature Plan: Dark Mode Toggle

## Files to Create/Modify

1. 📝 `components/ThemeToggle.py` (create)
2. 📝 `islands/ThemeProvider.py` (create)
3. 📝 `pages/layout.py` (modify)
4. 📝 `styles/globals.css` (modify)

[1/4] Create components/ThemeToggle.py?

Preview:
```python
from pynext import button, span
from pynext.islands import island

@island
def ThemeToggle():
    ...
```

Create this file? [Y/n/edit] y

✓ Created

[2/4] Create islands/ThemeProvider.py?
...

✅ Feature added successfully!
   Created 4 file(s)
```

## Python API

Use the App Builder programmatically:

```python
from pathlib import Path
from pynext.app import AppGenerator, AppPlanner, create_app, add_feature

# Quick functions
result = await create_app(
    "blog with auth",
    output_dir="./my-blog",
    mode="agent",
)

result = await add_feature(
    "dark mode",
    project_path="./my-blog",
)

# Full control
generator = AppGenerator()

# Create new app
result = await generator.new_app(
    description="task manager with real-time updates",
    output_dir=Path("./task-app"),
    mode="plan",
    complexity="medium",
)

# Add feature
result = await generator.add_feature(
    feature="admin dashboard",
    project_path=Path("./task-app"),
    mode="ask",
)

# Access results
print(f"Success: {result.success}")
print(f"Files: {list(result.generated_files.keys())}")
print(f"Duration: {result.duration}s")
```

## Knowledge Base API

Access the PyNext knowledge base directly for custom integrations:

### Initialization

```python
from pathlib import Path
from pynext.app.knowledge import PyNextKnowledge

# Initialize knowledge base
kb = PyNextKnowledge(project_root=Path.cwd())

# Index all PyNext docs and source (one-time, cached)
await kb.initialize()
```

### Semantic Search

```python
# Search for relevant content
results = kb.search("drag and drop component", top_k=10)

for result in results:
    print(f"Score: {result.total_score:.2f}")
    print(f"Source: {result.chunk.source_path}")
    print(f"Content: {result.chunk.content[:100]}...")
    print()
```

### Pattern Library

```python
# Get a specific pattern
pattern = kb.get_pattern("island_component")
print(pattern.description)
print(pattern.code)

# Get all patterns matching tags
island_patterns = kb.pattern_library.get_patterns_by_tags(["island", "reactivity"])

# Render a pattern with variables
code = pattern.render(
    component_name="DragDrop",
    state_name="items",
    initial_state="[]",
)
```

### Context Building

```python
# Build optimized context for AI generation
context = kb.build_context(
    user_query="Create a real-time chat component",
    current_files={"pages/chat.py": "..."},  # Existing files
    relevant_chunks=kb.search("chat component websocket"),
)

# Context is formatted and prioritized to fit within token limits
print(f"Context length: {len(context)} chars")
```

### Embeddings

```python
from pynext.app.knowledge import EmbeddingProvider

# Local embeddings (sentence-transformers, no API)
provider = EmbeddingProvider()

# Generate embedding for a query
embedding = await provider.get_embedding("PyNext Signal state management")

# Batch embeddings
embeddings = await provider.get_batch_embeddings([
    "page routing",
    "island component",
    "database model",
])
```

### Indexing Custom Content

```python
from pynext.app.knowledge import KnowledgeIndexer, IndexedChunk

indexer = kb.indexer

# Get all indexed chunks
chunks = indexer.get_chunks()
print(f"Total chunks: {len(chunks)}")

# Filter by type
doc_chunks = indexer.get_chunks(filters={"type": "documentation"})
code_chunks = indexer.get_chunks(filters={"type": "source_code"})

# Filter by topics
signal_chunks = indexer.get_chunks(filters={"topics": ["signal", "reactivity"]})
```

## Extending the Knowledge Base

### Adding Custom Patterns

Create new patterns for your team's coding standards:

```python
from pynext.app.knowledge.patterns import PyNextPattern, PatternLibrary

# Define a custom pattern
my_pattern = PyNextPattern(
    name="team_component",
    description="Team-standard component with logging",
    code='''
from pynext import div, Signal
from pynext.islands import island
import logging

logger = logging.getLogger(__name__)

@island
def ${component_name}():
    """${description}"""
    logger.info("${component_name} mounted")
    
    ${state_declarations}
    
    return div(class_="${container_class}")(
        ${content}
    )
''',
    tags=["team", "component", "logging"],
    dependencies=["pynext.islands"],
    template_vars={
        "component_name": "str",
        "description": "str",
        "state_declarations": "str",
        "container_class": "str",
        "content": "str",
    },
)

# Add to library
patterns = PatternLibrary()
patterns.add_pattern(my_pattern)
```

### Custom Index Sources

Index additional documentation or code:

```python
from pynext.app.knowledge import KnowledgeIndexer

indexer = KnowledgeIndexer(project_root)

# Index a custom directory
await indexer._index_file(
    Path("team_docs/conventions.md"),
    doc_type="documentation"
)

# Index external examples
await indexer._index_file(
    Path("examples/advanced_island.py"),
    doc_type="example"
)
```

### Custom Retrieval Strategies

Implement custom scoring for your use case:

```python
from pynext.app.knowledge import SemanticRetriever, SearchResult

class CustomRetriever(SemanticRetriever):
    def _rerank_results(self, results: list[SearchResult]) -> list[SearchResult]:
        # Custom reranking: boost patterns and examples
        for result in results:
            chunk_type = result.chunk.metadata.get("type")
            if chunk_type == "pattern":
                result.total_score *= 1.5  # Boost patterns
            elif chunk_type == "example":
                result.total_score *= 1.3  # Boost examples
        
        results.sort(key=lambda x: x.total_score, reverse=True)
        return results
```

## Troubleshooting

### "No ANTHROPIC_API_KEY found"

Set your API key:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

Or pass it directly:

```bash
ANTHROPIC_API_KEY=sk-ant-... pynext app new "my app"
```

### Generation is slow

- Use `--complexity minimal` for faster generation
- Use `--mode agent` to skip confirmations
- The first run builds the knowledge index (cached after)

### Files have errors

- Use `--mode ask` to review each file
- Run `pynext lint --fix` after generation
- Report issues at github.com/cuegrowthos/pynext/issues

### Want to customize generated code

1. Generate with `--mode ask`
2. Edit the preview when shown
3. Or generate and then modify manually

## Best Practices

1. **Start with a clear description**: The more detail, the better the result
2. **Use appropriate complexity**: Don't over-engineer simple apps
3. **Review the plan**: Use plan mode for important projects
4. **Iterate**: Add features incrementally rather than all at once
5. **Customize**: Generated code is a starting point - customize as needed

