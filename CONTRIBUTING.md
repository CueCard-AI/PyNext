# Contributing to PyNext

Thank you for your interest in contributing to PyNext! This guide will help you understand our principles, code standards, and contribution process.

---

## Our Principles

Every contribution to PyNext should align with these core principles:

| Principle | Why It Matters | How to Follow |
|-----------|----------------|---------------|
| **Readable & Simple** | Python devs shouldn't need web expertise to contribute | Plain English in comments, no jargon, obvious variable names |
| **AI-Friendly** | LLMs should understand and extend code easily | Clear docstrings, explicit types, self-documenting patterns |
| **Comprehensive Tests** | 4,886 tests and counting—we don't ship bugs | Every feature needs tests, edge cases covered |
| **Extensive Documentation** | Docs are how developers and LLMs learn PyNext | Follow our doc templates, explain first principles, real examples |
| **SolidJS Ethos** | Fine-grained reactivity, minimal overhead | No virtual DOM patterns, surgical updates only |
| **Faster Than Next.js** | Performance is a feature, not an afterthought | Benchmark before merging, no unnecessary abstractions |
| **Python-First** | For developers not super familiar with webdev | Pure Python APIs, no JavaScript concepts leaking through |

---

## Code Style Requirements

### 1. Type Hints on All Public APIs

Every public function, method, and class must have complete type hints.

```python
# ✅ Good
async def insert(self, **values: Any) -> "Table":
    """Insert a new record and return it."""
    ...

# ❌ Bad
async def insert(self, **values):
    ...
```

### 2. Docstrings with Examples (AI-Friendly)

All public APIs need docstrings that an LLM could use to understand and generate code.

```python
# ✅ Good - Clear, with example
async def select(cls) -> "Query":
    """
    Start a query to select records from this table.
    
    Returns a Query object that can be chained with where(), order_by(), etc.
    
    Example:
        users = await User.select().where(age__gt=18).order_by("name")
        
        # With limit
        top_10 = await User.select().limit(10)
    """
    ...

# ❌ Bad - No example, vague description
async def select(cls) -> "Query":
    """Select records."""
    ...
```

### 3. No Magic—Explicit Over Implicit

Don't use metaclass tricks, descriptor magic, or import-time side effects unless absolutely necessary.

```python
# ✅ Good - Explicit registration
class User(Table):
    name: str
    email: str

db.register(User)  # Clear what's happening

# ❌ Bad - Hidden magic
class User(Table):  # Secretly registers itself via metaclass
    name: str
```

### 4. Follow Existing Patterns

Look at similar code in the codebase before writing new code. Match the style.

```python
# If other adapters do this:
async def connect(self) -> None:
    """Establish connection to the database."""
    ...

# Your adapter should do the same, not:
async def open_connection(self):  # Different name, no type hint
    ...
```

---

## Test Requirements

### Every New Feature Needs Tests

We maintain 4,886+ tests. Your contribution should add to this, not skip testing.

| Contribution Type | Minimum Test Requirement |
|-------------------|--------------------------|
| New feature | Full unit tests + integration test |
| Bug fix | Regression test that would have caught the bug |
| Refactor | Existing tests must still pass |
| Performance | Benchmark test proving improvement |

### Use pytest with Async Fixtures

```python
import pytest
from pynext.db import Table, MemoryAdapter

@pytest.fixture
async def db():
    """Provide a clean in-memory database for each test."""
    adapter = MemoryAdapter()
    await adapter.connect()
    yield adapter
    await adapter.disconnect()

@pytest.fixture
def User(db):
    """Create a User table for testing."""
    class User(Table):
        name: str
        email: str
    
    User._set_adapter(db)
    return User

@pytest.mark.asyncio
async def test_insert_creates_record(User):
    """Inserting a user should create a record with an auto-generated ID."""
    user = await User.insert(name="Alice", email="alice@example.com")
    
    assert user.id is not None
    assert user.name == "Alice"
    assert user.email == "alice@example.com"
```

### Real Integration Tests

For database features, use testcontainers to spin up real PostgreSQL:

```python
import pytest
from testcontainers.postgres import PostgresContainer

@pytest.fixture(scope="module")
def postgres():
    """Spin up a real PostgreSQL container for integration tests."""
    with PostgresContainer("postgres:15") as postgres:
        yield postgres.get_connection_url()

@pytest.mark.asyncio
async def test_postgres_connection(postgres):
    """Test that we can connect to real PostgreSQL."""
    adapter = PostgresAdapter(postgres)
    await adapter.connect()
    
    assert adapter.is_connected
    await adapter.disconnect()
```

### Performance Benchmarks for Critical Paths

If your change affects performance-critical code, include benchmarks:

```python
import pytest

@pytest.mark.benchmark
async def test_bulk_insert_performance(db, benchmark):
    """Bulk insert should handle 10,000 records in under 1 second."""
    class Item(Table):
        name: str
    
    records = [{"name": f"item_{i}"} for i in range(10_000)]
    
    result = await benchmark(Item.insert_many, records)
    
    assert benchmark.stats["mean"] < 1.0  # Under 1 second
```

---

## Documentation Requirements

**Documentation is not optional.** Every new feature MUST include extensive documentation following our established patterns. Poor documentation = rejected PR.

### Why We Care So Much About Docs

1. **AI-Friendly** — LLMs use our docs to help developers build with PyNext
2. **Python-First** — Developers unfamiliar with web dev need clear explanations
3. **Self-Serve** — Good docs reduce support burden and GitHub issues
4. **Longevity** — Code without docs becomes unmaintainable

### Study Existing Documentation First

Before writing docs, read these examples to understand our style:

| Doc | Why It's a Good Example |
|-----|-------------------------|
| [docs/features/DATABASE.md](docs/features/DATABASE.md) | Complete API reference, first-principles explanations, many examples |
| [docs/features/POSTGRES.md](docs/features/POSTGRES.md) | Configuration tables, performance tips, troubleshooting section |
| [docs/features/MIGRATIONS.md](docs/features/MIGRATIONS.md) | Step-by-step workflows, CLI commands, error handling |
| [docs/core-concepts/STATE_MANAGEMENT.md](docs/core-concepts/STATE_MANAGEMENT.md) | Concept explanations, when to use what, comparison tables |

### Documentation Structure Template

Every feature doc should include these sections:

```markdown
# Feature Name

One-paragraph summary: what it does, why you'd use it.

---

## Quick Start

3-5 lines of code showing the most common use case.
Get the reader productive in 30 seconds.

---

## How It Works (First Principles)

Explain the underlying concepts. Assume the reader is smart but unfamiliar.
Use diagrams (ASCII art) where helpful.

---

## API Reference

### `function_name(arg1, arg2)`

**Purpose:** One sentence.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| arg1 | str | required | What it does |
| arg2 | int | 10 | What it does |

**Returns:** What and when.

**Example:**
```python
# Show real usage, not toy examples
result = function_name("real_value", arg2=20)
```

**Common Mistakes:**
```python
# ❌ Wrong - explain why
bad_usage()

# ✅ Correct - explain why
good_usage()
```

---

## Complete Examples

### Example 1: Real-World Use Case

Full, runnable code showing a realistic scenario.

### Example 2: Another Common Pattern

Different use case, different features highlighted.

---

## Configuration Options

Table of all config options with defaults and descriptions.

---

## Performance Considerations

What's fast, what's slow, how to optimize.

---

## Troubleshooting

### "Error message X"

**Cause:** Why this happens.
**Solution:** How to fix it.

---

## See Also

- Links to related docs
- External resources if relevant
```

### Documentation Checklist

Your docs must include:

- [ ] **Quick Start** — Working code in <10 lines
- [ ] **First Principles** — Explain the "why", not just the "how"
- [ ] **Every Public API** — All functions, classes, parameters documented
- [ ] **Real Examples** — Not `foo`/`bar`, use realistic names and scenarios
- [ ] **Common Mistakes** — Show wrong way AND right way with explanations
- [ ] **Error Messages** — Document what errors mean and how to fix them
- [ ] **Configuration** — All options with types, defaults, descriptions
- [ ] **Performance Notes** — What's O(1) vs O(n), what to avoid in loops
- [ ] **ASCII Diagrams** — Visualize architectures and data flows
- [ ] **Links** — Cross-reference related docs

### Writing Style

| Do | Don't |
|----|-------|
| "Signal notifies subscribers when value changes" | "Signal is a reactive primitive" (jargon) |
| "Returns the user or None if not found" | "Returns the user" (incomplete) |
| Show full import statements | Assume imports are obvious |
| Use realistic variable names (`user`, `post`) | Use `x`, `foo`, `bar` |
| Explain edge cases inline | Leave edge cases undocumented |
| Include error handling in examples | Show only happy path |

### Minimum Documentation Size

| Feature Type | Minimum Doc Size |
|--------------|------------------|
| New component | 200+ lines |
| New module | 300+ lines |
| New API method | 50+ lines (in existing doc) |
| Database feature | 400+ lines |
| CLI command | 100+ lines |

These aren't arbitrary—they reflect the depth needed for developers and LLMs to actually use the feature.

---

## Contribution Examples

### Example 1: Adding a New UI Component

Let's say you want to add a `Tooltip` component.

**1. Create the component file:**

```python
# pynext/components/tooltip.py
"""
Tooltip component for displaying contextual information on hover.

This component follows the SolidJS pattern of fine-grained reactivity:
only the tooltip visibility updates, not the entire component tree.
"""

from pynext import component, Signal, div, span

@component
def Tooltip(
    content: str,
    position: str = "top",
    delay_ms: int = 200
):
    """
    Display a tooltip on hover.
    
    Args:
        content: The text to display in the tooltip
        position: Where to show the tooltip ("top", "bottom", "left", "right")
        delay_ms: Delay before showing tooltip (milliseconds)
    
    Example:
        from pynext.components import Tooltip
        
        Tooltip(content="Click to submit")[
            button()["Submit"]
        ]
    """
    visible = Signal(False)
    
    return div(
        class_=f"tooltip-container tooltip-{position}",
        onmouseenter=lambda: visible.set(True),
        onmouseleave=lambda: visible.set(False)
    )[
        # Children go here (the trigger element)
        slot(),
        
        # Tooltip only renders when visible
        Show(when=visible)[
            span(class_="tooltip-content")[content]
        ]
    ]
```

**2. Add comprehensive tests:**

```python
# tests/unit/test_tooltip.py
import pytest
from pynext.components import Tooltip
from pynext.testing import render, assert_has_text, assert_hidden

class TestTooltip:
    """Tests for the Tooltip component."""
    
    def test_renders_children(self):
        """Tooltip should render its children."""
        result = render(Tooltip(content="Help text")[
            button()["Click me"]
        ])
        
        assert_has_text(result, "Click me")
    
    def test_tooltip_hidden_by_default(self):
        """Tooltip content should be hidden initially."""
        result = render(Tooltip(content="Help text")[
            button()["Click me"]
        ])
        
        assert_hidden(result, ".tooltip-content")
    
    def test_tooltip_shows_on_hover(self):
        """Tooltip should appear when hovering over trigger."""
        result = render(Tooltip(content="Help text")[
            button()["Click me"]
        ])
        
        result.hover(".tooltip-container")
        
        assert_has_text(result, "Help text")
    
    def test_position_classes(self):
        """Tooltip should apply position-specific CSS classes."""
        for position in ["top", "bottom", "left", "right"]:
            result = render(Tooltip(content="Text", position=position)[
                button()["Click"]
            ])
            
            assert result.has_class(f"tooltip-{position}")
    
    # ... at least 20 more tests covering edge cases
```

**3. Add extensive documentation:**

Create `docs/components/TOOLTIP.md` following our template:

```markdown
# Tooltip

Display contextual information when users hover over elements.
Tooltips are essential for providing hints without cluttering the UI.

---

## Quick Start

```python
from pynext.components import Tooltip

Tooltip(content="Click to save your changes")[
    button()["Save"]
]
```

---

## How It Works

Tooltips use PyNext's fine-grained reactivity. Only the tooltip visibility 
updates—the trigger element and surrounding UI don't re-render.

```
┌─────────────────────────────────────────────┐
│  User hovers          Signal(visible)       │
│       │                    │                │
│       ▼                    ▼                │
│  onmouseenter ──────► visible.set(True)     │
│                            │                │
│                            ▼                │
│                    Show(when=visible)       │
│                    renders tooltip          │
│                                             │
│  Only the tooltip DOM updates, not parent   │
└─────────────────────────────────────────────┘
```

---

## API Reference

### `Tooltip(content, position, delay_ms)`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| content | str | required | Text displayed in the tooltip |
| position | str | "top" | Where tooltip appears: "top", "bottom", "left", "right" |
| delay_ms | int | 200 | Milliseconds before tooltip shows |

**Example:**
```python
# Bottom tooltip with longer delay
Tooltip(content="Delete permanently", position="bottom", delay_ms=500)[
    button(class_="danger")["Delete"]
]
```

---

## Accessibility

Tooltips automatically include:
- `role="tooltip"` for screen readers
- `aria-describedby` linking trigger to content
- Keyboard focus support (shows on focus, hides on blur)

---

## Common Mistakes

```python
# ❌ Wrong - Empty content
Tooltip(content="")[button()["Save"]]  # Nothing to show!

# ✅ Correct - Meaningful content
Tooltip(content="Save changes to database")[button()["Save"]]
```

```python
# ❌ Wrong - Too much text
Tooltip(content="This is a very long explanation that...")[...]

# ✅ Correct - Keep it brief, link to docs for details
Tooltip(content="Ctrl+S to save")[...]
```

---

## See Also

- [Popover](./POPOVER.md) — For richer interactive content
- [Dialog](./DIALOG.md) — For modal confirmations
```

This is the level of documentation we expect. See `docs/features/DATABASE.md` for a full example.

---

### Example 2: Adding a Database Feature

Let's say you want to add `LIKE` queries to the ORM.

**1. Add to the query builder:**

```python
# pynext/db/query.py

class Query:
    # ... existing code ...
    
    def like(self, field: str, pattern: str) -> "Query":
        """
        Add a LIKE condition to the query.
        
        Args:
            field: The column to search
            pattern: SQL LIKE pattern (use % for wildcards)
        
        Example:
            # Find users whose name starts with "A"
            users = await User.select().like("name", "A%")
            
            # Find emails containing "gmail"
            gmail_users = await User.select().like("email", "%gmail%")
        
        Returns:
            Query: Self for chaining
        """
        self._conditions.append(LikeCondition(field, pattern))
        return self
```

**2. Add comprehensive tests:**

```python
# tests/unit/test_db_query_like.py

class TestQueryLike:
    """Tests for LIKE query functionality."""
    
    @pytest.mark.asyncio
    async def test_like_prefix_match(self, User):
        """LIKE should match prefixes with % wildcard."""
        await User.insert(name="Alice")
        await User.insert(name="Bob")
        await User.insert(name="Amy")
        
        results = await User.select().like("name", "A%")
        
        assert len(results) == 2
        assert all(u.name.startswith("A") for u in results)
    
    @pytest.mark.asyncio
    async def test_like_suffix_match(self, User):
        """LIKE should match suffixes with % wildcard."""
        await User.insert(name="Alice")
        await User.insert(name="Grace")
        
        results = await User.select().like("name", "%ce")
        
        assert len(results) == 2
    
    @pytest.mark.asyncio
    async def test_like_contains_match(self, User):
        """LIKE should match substrings with %...% pattern."""
        await User.insert(email="alice@gmail.com")
        await User.insert(email="bob@yahoo.com")
        
        results = await User.select().like("email", "%gmail%")
        
        assert len(results) == 1
    
    @pytest.mark.asyncio
    async def test_like_case_sensitive(self, User):
        """LIKE should be case-sensitive by default."""
        await User.insert(name="Alice")
        await User.insert(name="ALICE")
        
        results = await User.select().like("name", "A%")
        
        assert len(results) == 2  # Both match "A%"
    
    @pytest.mark.asyncio
    async def test_like_chaining(self, User):
        """LIKE should chain with other query methods."""
        await User.insert(name="Alice", age=25)
        await User.insert(name="Amy", age=30)
        await User.insert(name="Bob", age=25)
        
        results = await User.select().like("name", "A%").where(age=25)
        
        assert len(results) == 1
        assert results[0].name == "Alice"
    
    @pytest.mark.asyncio
    async def test_like_sql_injection_prevention(self, User):
        """LIKE should prevent SQL injection."""
        await User.insert(name="Alice")
        
        # This should NOT execute the injection
        results = await User.select().like("name", "'; DROP TABLE users; --")
        
        assert len(results) == 0
        # Table should still exist
        all_users = await User.select()
        assert len(all_users) == 1
    
    # ... 20+ more tests
```

---

### Example 3: Adding Tests for Existing Code

Found untested code? Great! Here's how to add tests.

**1. Identify the untested functionality:**

```bash
# Run coverage report
pytest --cov=pynext --cov-report=html tests/unit/

# Open htmlcov/index.html and find uncovered lines
```

**2. Write tests that cover the gaps:**

```python
# tests/unit/test_signal_edge_cases.py

class TestSignalEdgeCases:
    """Tests for edge cases in Signal implementation."""
    
    def test_signal_with_none_initial_value(self):
        """Signal should accept None as initial value."""
        sig = Signal(None)
        
        assert sig() is None
    
    def test_signal_update_with_none_return(self):
        """Signal.update should handle functions returning None."""
        sig = Signal(5)
        sig.update(lambda x: None)
        
        assert sig() is None
    
    def test_signal_set_same_value(self):
        """Setting same value should not trigger unnecessary updates."""
        updates = []
        sig = Signal(5)
        
        @Effect
        def track():
            updates.append(sig())
        
        sig.set(5)  # Same value
        sig.set(5)  # Same value again
        
        assert len(updates) == 1  # Only initial subscription
    
    def test_signal_with_complex_objects(self):
        """Signal should work with complex nested objects."""
        data = {"users": [{"name": "Alice"}, {"name": "Bob"}]}
        sig = Signal(data)
        
        assert sig()["users"][0]["name"] == "Alice"
```

---

## Step-by-Step Contribution Process

### 1. Fork and Clone

```bash
# Fork the repo on GitHub, then:
git clone https://github.com/YOUR_USERNAME/PyNext.git
cd PyNext
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Verify tests pass
pytest tests/unit/ -x -q
```

### 3. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number-description
```

### 4. Write Tests First (TDD Encouraged)

Write your tests before implementing the feature. This ensures:
- You understand what you're building
- The API is usable before you write it
- You don't skip tests

### 5. Implement Your Feature

- Follow the code style requirements above
- Add docstrings with examples
- Keep changes focused (one feature per PR)

### 6. Run the Full Test Suite

```bash
# Run all tests
pytest tests/unit/ -v

# Check that all 4,886+ tests pass
pytest tests/unit/ --tb=short

# Run with coverage
pytest tests/unit/ --cov=pynext --cov-report=term-missing
```

### 7. Write Extensive Documentation

**This step is not optional.** Documentation is as important as the code itself.

For new features:
1. Create a new doc file in `docs/features/` or `docs/components/`
2. Follow the template in "Documentation Requirements" section above
3. Include: Quick Start, How It Works, full API Reference, Examples, Troubleshooting
4. Minimum 200-400 lines depending on feature complexity
5. Add cross-references to related docs

For changes to existing features:
1. Update the relevant doc file
2. Add new API methods to the reference section
3. Add examples showing new functionality
4. Update any outdated information

Always:
- Add examples to docstrings in the code
- Update README.md if it's a major feature
- Cross-link from related documentation pages

### 8. Submit a Pull Request

```bash
git add .
git commit -m "feat: Add LIKE query support to ORM

- Add Query.like() method for pattern matching
- Support all LIKE patterns (%, _)
- Add SQL injection prevention
- Add 25 comprehensive tests"

git push origin feature/your-feature-name
```

Then open a PR on GitHub with:
- Clear description of what changed
- Link to any related issues
- Screenshots if UI-related

---

## PR Checklist

Before submitting, verify:

- [ ] **Tests pass** — All 4,886+ tests still pass
- [ ] **New tests added** — Your feature has comprehensive tests (20+ for new features)
- [ ] **Type hints** — All public APIs have type annotations
- [ ] **Docstrings** — With clear examples that an LLM could use
- [ ] **Documentation created/updated** — See "Documentation Requirements" section above
  - [ ] Quick Start section with working code
  - [ ] First-principles explanation of concepts
  - [ ] All APIs documented with parameters, returns, examples
  - [ ] Common mistakes shown with corrections
  - [ ] Minimum line counts met (200+ for components, 300+ for modules)
- [ ] **No performance regression** — Benchmarked if relevant
- [ ] **Follows existing patterns** — Matches codebase style

---

## Getting Help

- **Questions?** Open a GitHub Discussion
- **Found a bug?** Open an Issue with reproduction steps
- **Not sure where to start?** Look for `good first issue` labels

---

## Recognition

All contributors are recognized in our release notes. Significant contributions may be highlighted in the README.

Thank you for helping make PyNext better!

