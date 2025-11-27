# Project Structure

Auto-detect `src/` folder structure with zero configuration.

---

## The Problem (Why This Exists)

Different teams prefer different project layouts:

**Standard Layout** (common in smaller projects):
```
my-app/
├── pages/
├── components/
├── lib/
└── public/
```

**src/ Layout** (common in larger projects):
```
my-app/
├── src/
│   ├── pages/
│   ├── components/
│   └── lib/
└── public/
```

Without auto-detection, you'd need to configure paths manually. PyNext just works with either.

### Real-World Analogy

Think of it like a **GPS that adapts to your driving style**:
- Some people prefer highways → GPS uses highways
- Some people prefer backroads → GPS uses backroads
- You don't have to tell it which you prefer → it figures it out

PyNext figures out your project structure automatically.

---

## First Principles: How It Works

### The Core Concept

PyNext auto-detects project structure at startup:

1. **Check** if `src/pages/` exists
2. **If yes** → Use `src/` structure
3. **If no** → Use standard structure
4. **No config needed** → Just create your folders

### Mental Model

```
┌─────────────────────────────────────────────────────────┐
│                  STARTUP DETECTION                      │
│                                                         │
│   Does src/pages/ exist?                               │
│           │                                             │
│     ┌─────┴─────┐                                      │
│     │           │                                      │
│    Yes          No                                     │
│     │           │                                      │
│     ▼           ▼                                      │
│   ┌───────┐  ┌───────┐                                │
│   │ src/  │  │ root  │                                │
│   │layout │  │layout │                                │
│   └───────┘  └───────┘                                │
│                                                         │
│   pages = src/pages    pages = pages                   │
│   components = src/... components = components         │
│   public = public      public = public                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Step-by-Step: What Happens at Startup

1. **App initializes** without explicit paths:
   ```python
   app = PyNextApp()  # No pages_dir specified
   ```

2. **Path resolution runs**:
   ```python
   # Internal logic
   if (project_root / "src" / "pages").exists():
       pages_dir = "src/pages"  # Use src/ layout
   else:
       pages_dir = "pages"      # Use standard layout
   ```

3. **All paths resolved**:
   ```python
   ProjectPaths(
       pages = /project/src/pages,      # or /project/pages
       components = /project/src/components,
       lib = /project/src/lib,
       public = /project/public,        # Always at root
       root = /project,
   )
   ```

4. **Router scans** the resolved paths

---

## Quick Start (Copy-Paste Ready)

### Option 1: Standard Structure (Default)

```bash
pynext init my-app
cd my-app
```

Creates:
```
my-app/
├── pages/
│   └── index.py
├── components/
├── lib/
├── public/
└── pynext.config.py
```

### Option 2: src/ Structure

```bash
pynext init my-app --src
cd my-app
```

Creates:
```
my-app/
├── src/
│   ├── pages/
│   │   └── index.py
│   ├── components/
│   └── lib/
├── public/
└── pynext.config.py
```

### Option 3: Convert Existing Project

Already have a project? Just move files:

```bash
# From standard to src/
mkdir -p src
mv pages src/
mv components src/
mv lib src/

# Restart server - PyNext auto-detects
pynext dev
```

No config changes needed!

---

## Complete API Reference

### `resolve_paths(root: Path = None) -> ProjectPaths`

**What it does**: Auto-detects and returns all project paths.

**When to use**: When you need to know where project files are.

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `root` | `Path` | `cwd()` | Project root directory |

**Returns**: `ProjectPaths` dataclass with all paths

**Example**:

```python
from pynext import resolve_paths

paths = resolve_paths()

print(f"Pages: {paths.pages}")           # /project/src/pages or /project/pages
print(f"Components: {paths.components}") # /project/src/components or /project/components
print(f"Public: {paths.public}")         # /project/public (always at root)
print(f"Uses src/: {paths.uses_src}")    # True or False
```

---

### `ProjectPaths` Dataclass

**Properties**:

| Property | Type | Description |
|----------|------|-------------|
| `pages` | `Path` | Pages directory |
| `components` | `Path` | Components directory |
| `lib` | `Path` | Library/utils directory |
| `public` | `Path` | Static files directory |
| `root` | `Path` | Project root |
| `uses_src` | `bool` | True if using src/ structure |
| `styles` | `Path` | Styles directory |
| `api` | `Path` | API routes directory (pages/api) |

**Methods**:

```python
paths = resolve_paths()

# Get relative path from root
rel = paths.relative(Path("/project/src/pages/about/page.py"))
# Returns: Path("src/pages/about/page.py")

# Convert to dictionary
data = paths.to_dict()
# Returns: {"pages": "...", "components": "...", ...}
```

---

### `detect_structure(root: Path = None) -> str`

**What it does**: Returns the structure type without resolving all paths.

**Returns**: `"src"` or `"standard"`

**Example**:

```python
from pynext import detect_structure

structure = detect_structure()
print(f"Using {structure} structure")
# "Using src structure" or "Using standard structure"
```

---

### `ensure_structure(root: Path = None, use_src: bool = False) -> ProjectPaths`

**What it does**: Creates project directory structure.

**When to use**: When initializing a new project.

**Example**:

```python
from pynext import ensure_structure
from pathlib import Path

# Create standard structure
paths = ensure_structure(Path("/my-project"), use_src=False)

# Create src/ structure
paths = ensure_structure(Path("/my-project"), use_src=True)
```

---

### `find_project_root(start: Path = None) -> Optional[Path]`

**What it does**: Searches upward to find project root.

**When to use**: When running commands from subdirectories.

**Example**:

```python
from pynext import find_project_root
from pathlib import Path

# From deep in the project
root = find_project_root(Path("/project/src/pages/admin/users"))
# Returns: Path("/project")
```

**How it finds the root**:
1. Looks for `pynext.config.py`
2. Looks for `pages/` with `page.py` files
3. Looks for `src/pages/`
4. Checks `pyproject.toml` for `[tool.pynext]`

---

### `validate_structure(root: Path = None) -> Tuple[bool, List[str]]`

**What it does**: Checks if project structure is valid.

**Returns**: `(is_valid, list_of_issues)`

**Example**:

```python
from pynext import validate_structure

valid, issues = validate_structure()

if valid:
    print("Project structure is valid!")
else:
    print("Issues found:")
    for issue in issues:
        print(f"  - {issue}")
```

---

### `get_watch_dirs(root: Path = None) -> List[Path]`

**What it does**: Returns directories to watch for hot reload.

**When to use**: Setting up file watchers.

**Example**:

```python
from pynext import get_watch_dirs

dirs = get_watch_dirs()
# Returns: [pages, components, lib, public] (only existing ones)
```

---

## Real-World Patterns

### Pattern 1: Monorepo with Multiple Apps

**Structure**:

```
monorepo/
├── apps/
│   ├── marketing/
│   │   └── src/pages/      # Marketing site
│   └── dashboard/
│       └── src/pages/      # Dashboard app
├── packages/
│   └── ui/                 # Shared components
└── package.json
```

**Running each app**:

```bash
# Marketing site
cd apps/marketing
pynext dev

# Dashboard
cd apps/dashboard
pynext dev
```

Each app auto-detects its own structure.

---

### Pattern 2: Migrating from Next.js

**Next.js structure**:

```
next-app/
├── src/
│   ├── app/           # Next.js app router
│   ├── components/
│   └── lib/
└── public/
```

**PyNext structure** (similar!):

```
pynext-app/
├── src/
│   ├── pages/         # PyNext pages
│   ├── components/
│   └── lib/
└── public/
```

**Migration steps**:
1. Rename `src/app/` to `src/pages/`
2. Convert React components to PyNext
3. Run `pynext dev` - it auto-detects `src/` structure

---

### Pattern 3: Shared Components Library

**Structure**:

```
project/
├── src/
│   ├── pages/
│   ├── components/    # Project-specific components
│   └── lib/
├── packages/
│   └── ui/            # Shared UI library
└── public/
```

**Using shared components**:

```python
# src/pages/index.py

from pynext import page, div

# Import from project components
from src.components.header import Header

# Import from shared package
from packages.ui.button import Button

@page(title="Home")
def home():
    return div()[
        Header(),
        Button()["Click me"],
    ]
```

---

## How It Works Under the Hood

### Path Resolution Logic

```python
def resolve_paths(root: Path = None) -> ProjectPaths:
    root = Path(root or Path.cwd()).resolve()
    
    # Priority check: src/pages/ takes precedence
    src_pages = root / "src" / "pages"
    if src_pages.exists():
        return ProjectPaths(
            pages=src_pages,
            components=root / "src" / "components",
            lib=root / "src" / "lib",
            public=root / "public",  # Always at root!
            root=root,
        )
    
    # Fallback: standard structure
    return ProjectPaths(
        pages=root / "pages",
        components=root / "components",
        lib=root / "lib",
        public=root / "public",
        root=root,
    )
```

### Server Integration

```python
class PyNextApp:
    def __init__(
        self,
        pages_dir: Optional[str] = None,  # Can be None!
        static_dir: Optional[str] = None,
    ):
        # Auto-detect if not specified
        if pages_dir is None or static_dir is None:
            paths = resolve_paths()
            
            if pages_dir is None:
                self.pages_dir = paths.pages
                print(f"[PyNext] Detected: {paths.pages}")
            
            if static_dir is None:
                self.static_dir = paths.public
```

### CLI Integration

```python
def cmd_init(args):
    # Ask about structure
    use_src = args.src  # --src flag
    
    if not args.yes and not use_src:
        response = input("Use src/ directory? [y/N]: ")
        use_src = response.lower() in ("y", "yes")
    
    # Create structure
    paths = ensure_structure(project_dir, use_src=use_src)
    print(f"Created {'src/' if use_src else 'standard'} structure")
```

---

## Troubleshooting

### "PyNext isn't finding my pages"

**Check 1**: Is your structure correct?

```
# Standard - pages at root
my-app/
├── pages/
│   └── page.py    # ← Must have at least one page

# src/ - pages in src/
my-app/
├── src/
│   └── pages/
│       └── page.py
```

**Check 2**: Are you running from project root?

```bash
# Wrong - running from pages directory
cd my-app/pages
pynext dev  # Can't find project!

# Right - running from project root
cd my-app
pynext dev
```

---

### "Getting 'pages directory not found'"

**Check**: Run validation

```python
from pynext import validate_structure

valid, issues = validate_structure()
for issue in issues:
    print(issue)
```

---

### "Public files not being served"

**Remember**: `public/` is always at project root, even with `src/` structure:

```
my-app/
├── src/
│   └── pages/
├── public/        # ← Always here, NOT in src/
│   ├── images/
│   └── favicon.ico
```

---

## Summary

**Key Takeaways**:

1. **Zero configuration** - PyNext auto-detects your structure
2. **src/ or standard** - Both work, choose your preference
3. **public/ always at root** - Static files stay outside src/
4. **Use `resolve_paths()`** to get project paths programmatically

**Structure Quick Reference**:

| Structure | Pages | Components | Public |
|-----------|-------|------------|--------|
| Standard | `/pages` | `/components` | `/public` |
| src/ | `/src/pages` | `/src/components` | `/public` |

**CLI Commands**:

```bash
# Standard structure (default)
pynext init my-app

# src/ structure
pynext init my-app --src

# Skip prompts
pynext init my-app --src --yes
```

**Next Steps**:

- [Route Groups](./ROUTE_GROUPS.md) - Organize routes
- [Templates](./TEMPLATE.md) - Page transitions
- [Error Pages](./ERROR_PAGES.md) - Custom error handling

