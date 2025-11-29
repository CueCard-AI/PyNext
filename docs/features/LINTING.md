# PyNext Linting

Zero-config linting with PyNext-specific rules. Just run `pynext lint` and you're done.

## Table of Contents

- [The Problem](#the-problem)
- [The Solution](#the-solution)
- [Quick Start](#quick-start)
- [PyNext Rules](#pynext-rules)
- [Configuration](#configuration)
- [IDE Integration](#ide-integration)
- [CLI Reference](#cli-reference)
- [Troubleshooting](#troubleshooting)

---

## The Problem

Standard Python linters don't understand PyNext:
- They don't know about Signals
- They can't detect island serialization issues
- They miss route file conventions
- They don't check ARIA attributes

You need PyNext-specific linting.

---

## The Solution

PyNext linting combines:
1. **Ruff** (Rust-powered, 100x faster than ESLint)
2. **10 PyNext-specific rules** (PNX001-010)
3. **Zero config to start**
4. **Full IDE integration**

```
┌─────────────────────────────────────────────────────────┐
│                   Linting Flow                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   Source Code        Ruff         PyNext Rules          │
│   ┌──────────┐      ───────►    ┌────────────┐         │
│   │ page.py  │       Fast        │ PNX001-010 │         │
│   │ island.py│      Python       │ Signals    │         │
│   │ etc.     │      linting      │ Islands    │         │
│   └──────────┘                   │ Routes     │         │
│                                  └────────────┘         │
│                                       │                 │
│                                       ▼                 │
│                              ┌──────────────┐           │
│                              │   Combined   │           │
│                              │   Results    │           │
│                              └──────────────┘           │
│                                    │                    │
│                    ┌───────────────┼───────────────┐    │
│                    ▼               ▼               ▼    │
│               Terminal          IDE            JSON     │
│               Output           Squiggles       Output   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Performance:**

| Action | ESLint | PyNext Lint |
|--------|--------|-------------|
| Lint 1000 files | ~5s | <1s |
| Single file | ~200ms | <10ms |
| Auto-fix | ~500ms | <50ms |

---

## Quick Start

### Run Linting

```bash
# Lint entire project
pynext lint

# Lint specific directory
pynext lint pages/

# Lint with auto-fix
pynext lint --fix

# Include unsafe fixes
pynext lint --fix --unsafe
```

### Example Output

```
pages/counter.py
----------------
⚠️ PNX001: Signal 'unused' is created but never read (line 5)
  💡 Remove the unused signal

pages/dashboard/page.py
-----------------------
❌ PNX007: page.py is missing the page() function (line 1)
  💡 Add a page() function

Found: 1 error(s), 1 warning(s)
```

---

## PyNext Rules

### PNX001: Unused Signal

A signal is created but never read.

```python
# ❌ Bad
def Counter():
    count = Signal(0)
    unused = Signal(10)  # Never read!
    return div()[count()]

# ✅ Good
def Counter():
    count = Signal(0)
    return div()[count()]
```

**Auto-fix:** Yes (removes unused signal)

---

### PNX002: Signal in Loop

Signal created inside a loop.

```python
# ❌ Bad - creates new signal each iteration!
def ItemList(items):
    for item in items:
        selected = Signal(False)

# ✅ Good - one signal for all items
def ItemList(items):
    selected = Signal(set())
    for item in items:
        # Use the single signal
        ...
```

**Auto-fix:** No (requires manual refactoring)

---

### PNX003: Missing Component Return

Component function doesn't return an element.

```python
# ❌ Bad
@component
def MyComponent():
    name = "Hello"
    # Forgot to return!

# ✅ Good
@component
def MyComponent():
    name = "Hello"
    return div()[name]
```

**Auto-fix:** Yes (adds return statement template)

---

### PNX004: Invalid Prop Type for Island

Island prop isn't JSON-serializable.

```python
# ❌ Bad - sets can't be serialized
@island
def TagList(tags: set = {1, 2, 3}):
    return ul()[...]

# ✅ Good - use list instead
@island
def TagList(tags: list = [1, 2, 3]):
    return ul()[...]
```

**Serializable types:**
- ✅ `str`, `int`, `float`, `bool`, `None`
- ✅ `list`, `dict`
- ❌ `set`, `frozenset`
- ❌ `bytes`, `functions`, `classes`

**Auto-fix:** No (requires type change)

---

### PNX005: Server Import in Island

Island imports server-only code.

```python
# ❌ Bad - os doesn't work in browser!
import os

@island
def FileWidget():
    files = os.listdir(".")  # Will fail!

# ✅ Good - use server action instead
@island
def FileWidget(files: list):
    # files passed from server
    return ul()[For(files, lambda f: li()[f])]
```

**Server-only modules:**
- `os`, `subprocess`, `socket`
- `sqlite3`, `psycopg2`, `sqlalchemy`
- `pathlib`, `shutil`, `tempfile`

**Auto-fix:** No (requires architecture change)

---

### PNX006: Invalid Route Name

Route file doesn't follow convention.

```python
# ❌ Bad
pages/home_page.py     # Should be page.py in root
pages/AboutPage.py     # PascalCase not allowed
pages/blog.route.py    # Should be blog/page.py

# ✅ Good
pages/page.py          # Home page
pages/about/page.py    # About page
pages/blog/page.py     # Blog index
```

**Auto-fix:** Yes (suggests rename)

---

### PNX007: Missing Page Export

page.py doesn't have a page() function.

```python
# ❌ Bad
def AboutPage():  # Wrong name!
    return div()["About"]

# ✅ Good
def page():  # Correct!
    return div()["About"]

# ✅ Also good
@page
def my_about():
    return div()["About"]
```

**Auto-fix:** Yes (adds template)

---

### PNX008: Untracked Effect

Effect doesn't read any signals.

```python
# ❌ Bad - runs once and never again
count = Signal(0)
Effect(lambda: print("Effect ran"))

# ✅ Good - re-runs when count changes
count = Signal(0)
Effect(lambda: print(f"Count: {count()}"))
```

**Auto-fix:** No (requires code understanding)

---

### PNX009: Direct Signal Mutation

Signal mutated directly instead of using .set().

```python
# ❌ Bad - bypasses reactivity!
count = Signal(0)
count.value = 5

# ✅ Good - triggers reactivity
count = Signal(0)
count.set(5)
```

**Auto-fix:** Yes (replaces `.value =` with `.set()`)

---

### PNX010: Missing Metadata

Page doesn't have metadata for SEO.

```python
# ❌ Bad
def page():
    return div()["Hello"]

# ✅ Good
metadata = Metadata(
    title="My Page",
    description="Page description",
)

def page():
    return div()["Hello"]
```

**Auto-fix:** Yes (adds metadata template)

---

## Configuration

### Zero Config (Default)

PyNext lint works out of the box with sensible defaults:
- All PNX rules enabled
- Excludes `__pycache__`, `node_modules`, `.venv`
- Targets `pages/`, `components/`, `app/`, `src/`

### Create Config File

```bash
# Create .ruff.toml
pynext lint init --ruff

# Add to pyproject.toml
pynext lint init
```

### pyproject.toml

```toml
[tool.pynext.lint]
# Rules to enable
enabled_rules = [
    "PNX001",
    "PNX002",
    "PNX003",
]

# Rules to disable
disabled_rules = ["PNX010"]

# Directories to lint
target_dirs = ["pages", "components", "app"]

# Files/patterns to exclude
exclude = ["migrations/*", "*.generated.py"]

# Output format: "text", "json", "github"
output_format = "text"
```

### .ruff.toml

```toml
# Ruff settings (PyNext extends these)
line-length = 88
target-version = "py310"

[lint]
select = ["E", "F", "I", "B"]
ignore = ["E501"]

[lint.per-file-ignores]
"__init__.py" = ["F401"]
"tests/*" = ["B011"]
```

---

## IDE Integration

### VS Code

```bash
# Auto-configure VS Code
pynext lint vscode
```

This creates:
- `.vscode/settings.json` - Ruff integration
- `.vscode/extensions.json` - Recommended extensions

**Manual setup:**

1. Install [Ruff extension](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff)
2. Add to settings.json:

```json
{
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "[python]": {
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll.ruff": "explicit"
    }
  }
}
```

### Neovim (nvim-lspconfig)

```lua
require('lspconfig').pynext_lsp.setup{
  cmd = { "pynext", "lint", "lsp" },
  filetypes = { "python" },
  root_dir = require('lspconfig').util.root_pattern(
    "pyproject.toml", "pynext.config.py"
  ),
}
```

### LSP Server

For any editor with LSP support:

```bash
# Start LSP server
pynext lint lsp
```

The LSP server provides:
- Real-time diagnostics
- Quick fixes
- Hover information
- Code actions

---

## CLI Reference

### Basic Commands

```bash
# Lint everything
pynext lint

# Lint specific path
pynext lint pages/

# Auto-fix issues
pynext lint --fix

# Include unsafe fixes
pynext lint --fix --unsafe

# JSON output (for CI)
pynext lint --format json

# GitHub Actions output
pynext lint --format github
```

### Configuration Commands

```bash
# Create config file
pynext lint init

# Create .ruff.toml
pynext lint init --ruff

# Configure VS Code
pynext lint vscode
```

### Information Commands

```bash
# List all rules
pynext lint rules

# Explain a rule
pynext lint explain PNX001
```

### LSP Command

```bash
# Start LSP server
pynext lint lsp
```

---

## Troubleshooting

### "ruff: command not found"

Install ruff:

```bash
pip install ruff
```

Or run without ruff (PyNext rules only):

```bash
# PyNext rules still work without ruff
pynext lint
```

### Rule Not Catching Issue

Check if the rule is enabled:

```bash
# See which rules are active
pynext lint rules
```

Enable it in config:

```toml
[tool.pynext.lint]
enabled_rules = ["PNX001", "PNX002", ...]
```

### False Positives

Disable rule for a file:

```python
# noqa: PNX001
unused = Signal(0)  # Intentionally unused
```

Or disable globally:

```toml
[tool.pynext.lint]
disabled_rules = ["PNX001"]
```

### VS Code Not Showing Errors

1. Check Ruff extension is installed
2. Run `pynext lint vscode` to configure
3. Reload VS Code

### Performance Issues

Exclude slow directories:

```toml
[tool.pynext.lint]
exclude = [
    "data/*",
    "*.generated.py",
    "large_module/*",
]
```

---

## Summary

| Feature | Description |
|---------|-------------|
| Zero Config | Works out of the box |
| 10 Rules | PyNext-specific checks |
| Auto-fix | Most issues fixable |
| IDE | VS Code, Neovim, any LSP |
| Speed | 100x faster than ESLint |
| Formats | Text, JSON, GitHub Actions |

Start linting today:

```bash
pynext lint
```

