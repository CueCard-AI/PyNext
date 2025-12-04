# PyNext Configuration System

> **Complete Reference Guide** for configuring the AI App Builder with preferences, standards, patterns, and intelligent conditional prompts.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Config Locations](#config-locations)
- [Complete Config Reference](#complete-config-reference)
  - [AI Settings](#1-ai-settings-ai)
  - [Code Style](#2-code-style-style)
  - [Validation Rules](#3-validation-rules-validation)
  - [Team Standards](#4-team-standards-team)
  - [Prompts](#5-prompts-prompts)
  - [Variables](#6-variables-vars)
  - [Modes](#7-modes-mode)
  - [Patterns](#8-patterns-patterns)
  - [Conditionals](#9-conditional-prompts-conditional)
  - [Rules](#10-rules-rules)
  - [Examples](#11-examples-examples)
  - [Memory Settings](#12-memory-settings-memory)
- [Config Loading Pipeline](#config-loading-pipeline)
- [Priority System](#priority-system)
- [Condition Evaluation](#condition-evaluation)
- [CLI Commands](#cli-commands)
- [Python API Reference](#python-api-reference)
- [Best Practices](#best-practices)
- [Complete Example Config](#complete-example-config)
- [Troubleshooting](#troubleshooting)

---

## Overview

The PyNext Configuration System provides **intelligent, context-aware configuration** for the AI App Builder:

| Feature | Description |
|---------|-------------|
| **Hierarchical Config** | Global → Project → Feature level inheritance |
| **Variables** | Static and computed values usable anywhere |
| **Modes** | Named bundles (prototype, production, strict) |
| **Conditional Prompts** | Python and LLM-evaluated conditions |
| **Patterns** | Reusable code templates with variables |
| **Rules** | Validation, naming, and structure rules |
| **Type-Specific Prompts** | Different guidance per file type |

### Why Configuration?

Without configuration, AI generates generic code. With configuration:

```
Without Config:
  "Create an API" → Generic REST endpoint

With Config:
  [prompts.api] prefix = "All APIs require authentication"
  [[conditional]] when_llm = "handles user data" → security rules
  
  "Create an API" → Authenticated, secure, following team standards
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   CONFIG LOADING PIPELINE                        │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│   Global Config  │   │  Project Config  │   │  Hidden Config   │
│ ~/.config/pynext │ → │   ./pynext.toml  │ → │ ./.pynext/config │
│   config.toml    │   │                  │   │      .toml       │
└────────┬─────────┘   └────────┬─────────┘   └────────┬─────────┘
         │                      │                      │
         └──────────────────────┼──────────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │    MERGE CONFIGS      │
                    │   (later overrides)   │
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │  RESOLVE VARIABLES    │
                    │  ${var} → value       │
                    │  ${ENV | default}     │
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │    APPLY MODE         │
                    │  [mode.X] settings    │
                    │  extends → inherit    │
                    └───────────┬───────────┘
                                │
         ┌──────────────────────┼──────────────────────┐
         │                      │                      │
┌────────▼────────┐   ┌────────▼────────┐   ┌────────▼────────┐
│ EVAL CONDITIONS │   │  MERGE PROMPTS  │   │ SELECT PATTERNS │
│ when = "expr"   │   │  by priority    │   │  by tags/when   │
│ when_llm = "..."│   │                 │   │                 │
└────────┬────────┘   └────────┬────────┘   └────────┬────────┘
         │                      │                      │
         └──────────────────────┼──────────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │   RESOLVED CONFIG     │
                    │  Ready for AI prompt  │
                    └───────────────────────┘
```

---

## Config Locations

Configs are loaded and merged in this order (later overrides earlier):

| Priority | Location | Purpose |
|----------|----------|---------|
| 1 (lowest) | `~/.config/pynext/config.toml` | Global defaults |
| 2 | `./pynext.toml` | Project config (visible) |
| 3 | `./.pynext/config.toml` | Project config (hidden) |
| 4 | Environment variables | Runtime overrides |
| 5 (highest) | CLI arguments | Command-line overrides |

### File Structure

```
~/.config/pynext/
└── config.toml          # Global config

project/
├── pynext.toml          # Main project config (visible)
├── .pynext/
│   └── config.toml      # Hidden project config (optional)
└── ...
```

---

## Complete Config Reference

### 1. AI Settings (`[ai]`)

Control AI model and generation behavior.

```toml
[ai]
# Model selection
model = "claude-sonnet-4-20250514"  # AI model to use

# Generation mode
mode = "plan"                       # plan, agent, ask
# - plan: Generate plan first, then execute
# - agent: Direct generation with thought loops
# - ask: Interactive, asks clarifying questions

# Complexity setting
complexity = "auto"                 # auto, minimal, small, medium, large, enterprise
# Affects: file count, detail level, feature scope

# Thought configuration
max_thoughts = 5                    # Max thought cycles for agent mode
thought_depth = "medium"            # shallow, medium, deep

# Output control
verbose = false                     # Show AI thinking process
temperature = 0.7                   # Response randomness (0.0-1.0)
```

**Environment Variable Overrides:**

| Env Variable | Config Key | Example |
|--------------|------------|---------|
| `ANTHROPIC_MODEL` | `ai.model` | `claude-opus-4` |
| `PYNEXT_MODE` | Active mode | `strict` |
| `PYNEXT_AI_VERBOSE` | `ai.verbose` | `true` |

---

### 2. Code Style (`[style]`)

Define coding style preferences.

```toml
[style]
# Naming conventions
naming_convention = "snake_case"    # snake_case, camelCase
class_naming = "PascalCase"         # Class naming style

# Formatting
max_line_length = 88                # Max characters per line
quote_style = "double"              # double, single
trailing_comma = true               # Include trailing commas in collections
indent_size = 4                     # Spaces per indentation level

# Documentation
docstring_style = "google"          # google, numpy, sphinx
```

**Style Examples:**

```python
# snake_case (default)
def get_user_by_id(user_id: int) -> User:
    """Get user by ID."""
    pass

# camelCase
def getUserById(userId: int) -> User:
    """Get user by ID."""
    pass
```

---

### 3. Validation Rules (`[validation]`)

Define code quality requirements.

```toml
[validation]
# Documentation requirements
require_docstrings = true           # Functions must have docstrings
require_type_hints = true           # Parameters must have type hints

# Testing requirements
require_tests = false               # Must generate test files

# Size limits
max_function_lines = 50             # Max lines per function
max_file_lines = 500                # Max lines per file

# Import rules
forbidden_imports = [               # Blocked imports
    "os.system",
    "eval",
    "exec",
    "subprocess.shell"
]
required_imports = []               # Must include these

# Pattern rules
forbidden_patterns = [              # Blocked code patterns
    "import *",
    "exec(",
]
```

---

### 4. Team Standards (`[team]`)

Define organization-specific standards.

```toml
[team]
# Component naming
component_prefix = "Acme"           # Prefix for components
# Results in: AcmeButton, AcmeHeader, etc.

# File headers
file_header = """
# Copyright 2025 Acme Corp
# SPDX-License-Identifier: MIT
"""

# Pattern requirements
required_patterns = ["error_handling", "logging"]
forbidden_patterns = []
```

---

### 5. Prompts (`[prompts]`)

Define AI prompts for different contexts.

```toml
[prompts]
# System prompt - prepended to ALL generations
system = """
You are an expert PyNext developer at Acme Corp.
Follow our coding standards strictly.
Always prioritize security and performance.
"""

# Suffix prompt - appended to ALL generations
suffix = """
Remember:
- All components must be accessible (WCAG 2.1 AA)
- Include error boundaries for islands
- Log all user actions for analytics
"""

# Context prompt - project/domain context
context = """
This is a B2B SaaS application for inventory management.
Users are warehouse managers and logistics coordinators.
The UI should be functional and data-dense, not flashy.
"""

# ========================================
# PER-FILE-TYPE PROMPTS
# ========================================

[prompts.page]
prefix = "Pages should include SEO metadata and loading states."
suffix = "Include breadcrumb navigation."

[prompts.island]
prefix = "Islands must be lightweight (<50KB hydrated)."
suffix = "Include loading and error states."

[prompts.api]
prefix = "All API routes require authentication."
suffix = "Return consistent error format: {error: string, code: number}."

[prompts.model]
prefix = "Models should include created_at and updated_at fields."
suffix = "Add indexes for frequently queried fields."

[prompts.action]
prefix = "Actions must validate all inputs."
suffix = "Log action execution for audit trail."

[prompts.component]
prefix = "Components must be reusable and well-documented."
suffix = "Include prop validation."

[prompts.layout]
prefix = "Layouts define page structure."
suffix = "Include error boundaries."

[prompts.middleware]
prefix = "Middleware runs on every request."
suffix = "Be performance-conscious."

[prompts.util]
prefix = "Utilities should be pure functions."
suffix = "Include comprehensive tests."
```

**Available File Types:**
- `page`, `island`, `component`, `api`, `action`, `model`, `layout`, `middleware`, `util`

---

### 6. Variables (`[vars]`)

Define reusable variables for substitution.

```toml
[vars]
# Static variables
company = "Acme Corp"
year = 2025
auth_module = "utils.auth"
api_version = "v1"

# Environment variable with fallback
db_host = "${DATABASE_HOST | localhost}"
db_port = "${DATABASE_PORT | 5432}"

# ========================================
# COMPUTED VARIABLES (Python expressions)
# ========================================

[vars.computed]
# Expressions evaluated at load time
copyright = "'Copyright ' + str(year) + ' ' + company"
api_base = "'/api/' + api_version"
full_db_url = "f'postgresql://{db_host}:{db_port}/app'"
```

**Using Variables:**

```toml
# Reference in any string with ${var_name}
[prompts]
system = "You work for ${company}. ${copyright}"

[patterns.api]
code = '''
from ${auth_module} import require_auth
# API version: ${api_version}
'''
```

**Variable Syntax:**

| Syntax | Description | Example |
|--------|-------------|---------|
| `${var}` | Simple substitution | `${company}` → `Acme Corp` |
| `${VAR \| default}` | Env var with fallback | `${PORT \| 3000}` |
| `[vars.computed]` | Python expression | `year + 1` |

---

### 7. Modes (`[mode.*]`)

Define named configuration bundles.

```toml
# ========================================
# PROTOTYPE MODE - Fast iteration
# ========================================
[mode.prototype]
description = "Fast iteration, minimal ceremony"

[mode.prototype.validation]
require_docstrings = false
require_type_hints = false
require_tests = false
max_function_lines = 100

[mode.prototype.prompts]
suffix = "Keep it simple and working. Skip edge cases for now."

# ========================================
# DEVELOPMENT MODE - Balanced
# ========================================
[mode.development]
description = "Standard development settings"

[mode.development.validation]
require_docstrings = true
require_type_hints = true
require_tests = false

# ========================================
# PRODUCTION MODE - Full validation
# ========================================
[mode.production]
description = "Production-ready code"

[mode.production.validation]
require_docstrings = true
require_type_hints = true
require_tests = true
max_function_lines = 30

[mode.production.prompts]
suffix = """
This is production code. Include:
- Comprehensive error handling
- Input validation
- Logging
- Performance considerations
"""

# ========================================
# STRICT MODE - Maximum safety (inherits from production)
# ========================================
[mode.strict]
description = "Maximum safety and compliance"
extends = "production"  # Inherit all production settings

[mode.strict.validation]
require_tests = true
forbidden_imports = ["os.system", "eval", "exec", "subprocess.shell"]
forbidden_patterns = ["import *", "exec("]

[mode.strict.prompts]
system = """
STRICT MODE: Security is paramount.
- Never trust user input
- Always sanitize and validate
- Use parameterized queries only
- Log all sensitive operations
"""
```

**Mode Inheritance:**

```toml
[mode.base]
# Base settings

[mode.child]
extends = "base"  # Inherits all settings from base
# Can override specific settings
```

**Switching Modes:**

```bash
# CLI
pynext app new "blog" --mode strict

# In chat session
> /mode strict
Switched to strict mode.

# Environment variable
PYNEXT_MODE=strict pynext app new "blog"
```

**Built-in Modes:**

| Mode | Description |
|------|-------------|
| `prototype` | Fast iteration, no tests, minimal validation |
| `development` | Standard development settings |
| `production` | Full validation, tests required |
| `strict` | Maximum safety, security focus |

---

### 8. Patterns (`[patterns.*]`)

Define reusable code templates.

```toml
[patterns.team_button]
description = "Standard team button with logging"
tags = ["component", "team", "ui"]
when = "file_type == 'island'"     # Only suggest for islands
deps = ["pynext.islands", "logging"]
code = '''
from pynext.islands import island
from pynext import button
import logging

logger = logging.getLogger(__name__)

@island
def ${name}Button(label: str = "${label}", variant: str = "${variant}"):
    """${description}
    
    Args:
        label: Button text
        variant: Visual variant (primary, secondary, danger)
    """
    def handle_click():
        logger.info(f"Button clicked: {label}")
    
    return button(
        class_=f"btn btn--{variant}",
        on_click=handle_click
    )(label)
'''

[patterns.api_crud]
description = "Full CRUD API with auth and validation"
tags = ["api", "crud", "auth"]
when = "file_type == 'api'"
deps = ["pynext.api", "${auth_module}"]
code = '''
from pynext.api import api, Request, Response
from pynext.db import ${Model}
from ${auth_module} import require_auth, get_current_user

@api
@require_auth
async def GET(request: Request):
    """List all ${model}s for current user."""
    user = await get_current_user(request)
    items = await ${Model}.filter(owner_id=user.id).all()
    return Response.json([item.to_dict() for item in items])

@api
@require_auth
async def POST(request: Request):
    """Create a new ${model}."""
    user = await get_current_user(request)
    data = await request.json()
    item = await ${Model}.create(**data, owner_id=user.id)
    return Response.json(item.to_dict(), status=201)
'''

[patterns.data_table]
description = "Sortable, filterable data table island"
tags = ["island", "table", "data"]
when_llm = "the user needs to display tabular data"
code = '''
from pynext import Signal, Computed
from pynext.islands import island

@island
def ${name}Table(initial_data: list = None):
    """Data table with sort, filter, pagination."""
    data = Signal(initial_data or [])
    sort_key = Signal("id")
    sort_dir = Signal("asc")
    filter_text = Signal("")
    
    sorted_data = Computed(lambda: sorted(
        [d for d in data() if filter_text().lower() in str(d).lower()],
        key=lambda x: x.get(sort_key(), ""),
        reverse=sort_dir() == "desc"
    ))
    
    # ... implementation
'''
```

**Pattern Fields:**

| Field | Required | Description |
|-------|----------|-------------|
| `description` | No | What the pattern does |
| `tags` | No | For searching/filtering |
| `code` | Yes | Template code |
| `when` | No | Python condition for when to suggest |
| `when_llm` | No | LLM-evaluated condition |
| `deps` | No | Required imports |

**Using Patterns:**

```python
# Get pattern by name
pattern = config.get_pattern("api_crud")

# Render with variables
code = pattern.render(
    Model="User",
    model="user",
)

# Get patterns by tags
api_patterns = config.get_patterns_by_tags(["api", "auth"])
```

---

### 9. Conditional Prompts (`[[conditional]]`)

Define context-aware prompts that activate based on conditions.

```toml
# ========================================
# PYTHON CONDITIONS (evaluated by Python)
# ========================================

[[conditional]]
priority = 80                       # Higher = applied first (0-100)
when = "file_type == 'api'"         # Python expression
prompt = "All API endpoints must return JSON with consistent error format."

[[conditional]]
priority = 85
when = "file_type == 'api' and 'auth' in description.lower()"
prompt = "Use JWT tokens. Include refresh token logic."
pattern = "api_auth"                # Suggest this pattern

[[conditional]]
priority = 75
when = "intent == 'new_app'"
prompt = "This is a new application. Set up proper project structure."

[[conditional]]
priority = 75
when = "intent == 'add_feature'"
prompt = "Integrate with existing patterns. Check imports from existing files."

[[conditional]]
priority = 70
when = "len(project.models) > 0"
prompt = "Existing models: ${project.models}. Reuse these where appropriate."

[[conditional]]
priority = 70
when = "project.has_auth"
prompt = "Auth system exists at ${auth_module}. Use require_auth decorator."

# ========================================
# LLM CONDITIONS (evaluated by AI)
# ========================================

[[conditional]]
priority = 90
when_llm = "the user is building something that handles payments or financial data"
prompt = """
FINANCIAL DATA HANDLING:
- Never log sensitive financial information
- Use decimal types for money, never float
- Implement audit trails for all transactions
- Consider PCI compliance requirements
"""

[[conditional]]
priority = 85
when_llm = "this feature involves user-generated content"
prompt = """
UGC SAFETY:
- Sanitize all user input for XSS
- Implement content moderation hooks
- Rate limit submissions
- Store original + sanitized versions
"""

[[conditional]]
priority = 80
when_llm = "the component will be used by many other components"
prompt = "This is a shared component. Make it highly reusable and well-documented."

# ========================================
# COMBINED CONDITIONS
# ========================================

[[conditional]]
priority = 88
when = "file_type == 'api'"         # Must be API file
when_llm = "and it handles sensitive user data"  # AND handles sensitive data
prompt = "Use encryption for data at rest. Implement rate limiting."
```

**Condition Types:**

| Type | Syntax | Evaluation | Speed |
|------|--------|------------|-------|
| Python | `when = "expr"` | Python eval | Fast |
| LLM | `when_llm = "..."` | AI evaluation | Slow |
| Combined | Both fields | Both must be true | Medium |

**Available Context Variables for `when`:**

| Variable | Type | Description |
|----------|------|-------------|
| `file_type` | str | `page`, `island`, `api`, `model`, etc. |
| `intent` | str | `new_app`, `add_feature`, `refactor` |
| `description` | str | User's description |
| `mode` | str | Active mode name |
| `complexity` | str | `minimal`, `small`, `medium`, `large` |
| `project.has_auth` | bool | Project has auth system |
| `project.models` | list | Existing model names |
| `project.pages` | list | Existing page names |
| `project.islands` | list | Existing island names |
| `project.all_files` | list | All project files |
| `has_auth` | bool | Shorthand for project.has_auth |
| `len(...)` | int | Count of items |
| `'x' in y` | bool | String containment |

---

### 10. Rules (`[rules]`)

Define validation and structure rules.

```toml
[rules]
# Freeform rules (always included)
custom = """
1. Never use inline styles - always use Tailwind classes
2. All forms must have CSRF protection
3. Database queries must use parameterized statements
4. File uploads limited to images under 5MB
5. All dates stored in UTC, displayed in user timezone
"""

# ========================================
# ALWAYS RULES (applied to everything)
# ========================================
[rules.always]
custom = """
1. Use Tailwind CSS for styling
2. Include aria labels for accessibility
3. Handle loading and error states
"""

# ========================================
# NAMING RULES
# ========================================
[rules.naming]
pages = "{name}.py"              # pages/dashboard.py
components = "{Name}.py"         # components/UserCard.py
islands = "{Name}.py"            # islands/Counter.py
models = "{name}.py"             # models/user.py
api = "{name}.py"                # api/users.py

# ========================================
# STRUCTURE RULES
# ========================================
[rules.structure]
required_dirs = ["pages", "components", "models", "api", "utils"]
required_files = ["pages/layout.py", "utils/auth.py"]

# ========================================
# CONDITIONAL RULES
# ========================================
[[rules.conditional]]
when = "mode == 'strict'"
custom = """
STRICT MODE RULES:
- All functions must have try/except
- Log all exceptions with full context
- Never expose internal errors to users
"""

[[rules.conditional]]
when_llm = "working with external APIs or third-party services"
custom = """
EXTERNAL SERVICE RULES:
- Implement circuit breakers
- Add retry logic with exponential backoff
- Cache responses where appropriate
- Have fallback behavior
"""
```

---

### 11. Examples (`[examples]`)

Provide few-shot examples for the AI.

```toml
[examples]
# Good examples (what to do)
good_island = '''
# GOOD: Clean, accessible, follows standards
@island
def SearchBox():
    """Search input with debounced API calls."""
    query = Signal("")
    results = Signal([])
    loading = Signal(False)
    
    async def search():
        if len(query()) < 2:
            return
        loading.set(True)
        try:
            results.set(await api.search(query()))
        finally:
            loading.set(False)
    
    Effect(lambda: debounce(search, 300)())
    
    return div(class_="search-container", role="search")(
        input_(
            type="search",
            value=query,
            on_input=lambda e: query.set(e.target.value),
            placeholder="Search...",
            aria_label="Search",
        ),
        Show(when=loading)(Spinner()),
        ul(class_="results", role="listbox")(
            For(each=results)(lambda item: 
                li(role="option")(item.name)
            )
        )
    )
'''

good_api = '''
# GOOD: Authenticated, validated, proper error handling
@api
@require_auth
async def POST(request: Request):
    """Create a new resource.
    
    Args:
        request: The incoming request
        
    Returns:
        JSON response with created resource
        
    Raises:
        ValidationError: If input is invalid
    """
    try:
        data = await request.json()
        validated = validate_input(data)
        result = await Resource.create(**validated)
        return Response.json(result.to_dict(), status=201)
    except ValidationError as e:
        return Response.json({"error": str(e)}, status=400)
'''

# Bad examples (what NOT to do)
bad_island = '''
# BAD: Avoid these patterns
def bad():
    # No @island decorator
    # No type hints
    # Inline styles
    # No accessibility
    return div(style="color:red")(
        input()  # No label, no aria
    )
'''

bad_api = '''
# BAD: Avoid these patterns
def get():  # No @api decorator, no type hints
    data = request.json()  # No await, no validation
    return data  # No proper response format
'''
```

---

### 12. Memory Settings (`[memory]`)

Configure session memory sync behavior.

```toml
[memory]
# Sync strategy
sync_mode = "incremental"           # incremental, full, manual

# When to auto-sync
sync_on = ["assistant_response", "checkpoint", "exit"]

# Batching
sync_batch_size = 5                 # Buffer before write
sync_interval = 0                   # Seconds (0 = disabled)

# Limits
max_entries_in_memory = 1000        # Flush when exceeded
max_file_size_mb = 50               # Rotate when exceeded

# Filtering
exclude_roles = []                  # Skip these roles
min_content_length = 0              # Skip short messages
```

See [MEMORY.md](./MEMORY.md) for complete memory documentation.

---

## Config Loading Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONFIG LOADING PIPELINE                       │
└─────────────────────────────────────────────────────────────────┘

STEP 1: LOAD CONFIGS
├── ~/.config/pynext/config.toml    →  Global defaults
├── ./pynext.toml                   →  Project overrides
├── ./.pynext/config.toml           →  Hidden project config
├── Environment variables           →  Env overrides
└── CLI arguments                   →  Command overrides

STEP 2: MERGE (later overrides earlier)
├── Start with global
├── Merge project on top
├── Apply env vars
└── Apply CLI args

STEP 3: RESOLVE VARIABLES
├── ${var}         → lookup in [vars]
├── ${VAR|default} → env var or default
└── [vars.computed] → evaluate expressions

STEP 4: APPLY MODE
├── Get active_mode or --mode
├── Load [mode.X] settings
├── If extends, inherit parent first
└── Merge mode settings

STEP 5: BUILD CONTEXT
├── file_type (what's being generated)
├── intent (new_app, add_feature)
├── description (user's request)
├── project.* (existing project state)
└── mode (active mode)

STEP 6: EVALUATE CONDITIONALS
├── For each [[conditional]]:
│   ├── Eval `when` (Python) → bool
│   ├── Eval `when_llm` (AI) → bool  
│   └── If both true: add to candidates
└── Sort by priority (high to low)

STEP 7: MERGE BY PRIORITY
├── Collect all matching prompts
├── Collect all matching rules
├── Collect all matching patterns
└── Apply variable substitution

STEP 8: OUTPUT ResolvedConfig
├── system_prompt (merged)
├── suffix_prompt (merged)
├── prompts[] (all matching)
├── rules[] (all matching)
├── patterns[] (suggested)
├── validation (final settings)
└── style (final settings)
```

---

## Priority System

### Trigger Priority (highest to lowest)

| Priority | Source | When Applied |
|----------|--------|--------------|
| 100 | Explicit command | User says "use strict mode" |
| 90 | Feature-level | Inline in generation request |
| 80 | Intent-based | Detected from user request |
| 70 | File-type | Based on what's being generated |
| 60 | Project-state | Based on existing codebase |
| 50 | Mode defaults | Active mode settings |
| 40 | Project config | `pynext.toml` |
| 30 | Global config | `~/.config/pynext/config.toml` |

### Conditional Priority

Conditionals are sorted by `priority` field (0-100):

```toml
[[conditional]]
priority = 90  # High priority - applied first
when = "..."
prompt = "..."

[[conditional]]
priority = 50  # Lower priority - applied after
when = "..."
prompt = "..."
```

Higher priority conditionals are processed first and their prompts appear earlier in the context.

---

## Condition Evaluation

### Python Conditions (`when`)

Evaluated using Python's `eval()` with a restricted namespace:

```toml
# Simple comparisons
when = "file_type == 'api'"
when = "mode == 'strict'"

# Compound conditions
when = "file_type == 'api' and project.has_auth"
when = "file_type in ['page', 'layout']"

# String operations
when = "'auth' in description.lower()"

# List operations
when = "len(project.models) > 0"
when = "'User' in project.models"

# Complex expressions
when = "file_type == 'api' and (project.has_auth or 'auth' in description)"
```

### LLM Conditions (`when_llm`)

Natural language conditions evaluated by the AI:

```toml
# Semantic understanding
when_llm = "the user is building payment functionality"
when_llm = "this feature involves user-generated content"
when_llm = "the component will be shared across many files"

# Domain-specific
when_llm = "this appears to be a security-sensitive feature"
when_llm = "the user wants real-time updates"
```

**LLM Evaluation Process:**

```
Prompt to LLM:
"Evaluate if this condition is TRUE or FALSE.
Respond with only 'TRUE' or 'FALSE'.

CONDITION: the user is building payment functionality

CONTEXT:
- File type: api
- Intent: add_feature
- Description: Create a checkout flow with Stripe
- Project has auth: true

Answer:"
```

### Combined Conditions

When both `when` and `when_llm` are specified, **both must be true**:

```toml
[[conditional]]
priority = 88
when = "file_type == 'api'"            # Must be API file
when_llm = "handles sensitive data"     # AND handles sensitive data
prompt = "Implement encryption and rate limiting."
```

---

## CLI Commands

### Initialize Config

```bash
# Create pynext.toml with defaults
pynext config init

# Overwrite existing
pynext config init --force
```

### View Config

```bash
# Show merged config
pynext config show

# Show as JSON
pynext config show --json

# Show resolved config (with conditionals applied)
pynext config show --resolved

# Get specific value
pynext config get ai.model
pynext config get style.max_line_length
```

### Validate Config

```bash
# Check syntax and references
pynext config validate

# Output:
# ✓ Config syntax valid
# ✓ All mode extends references valid
# ✓ All pattern conditions valid
# ✓ No circular mode inheritance
```

### Reload Config (in session)

```bash
# In pynext app chat
> /config reload
Config reloaded from pynext.toml

> /config show
[Shows current config]
```

---

## Python API Reference

### PyNextConfig Class

```python
from pynext.app.config import PyNextConfig

class PyNextConfig:
    """Main configuration class."""
    
    # Settings
    ai: AIPreferences
    style: CodeStyle
    validation: ValidationRules
    team: TeamStandards
    prompts: PromptConfig
    vars: Dict[str, str]
    modes: Dict[str, ModeConfig]
    patterns: Dict[str, Pattern]
    conditionals: List[Conditional]
    rules: RulesConfig
    examples: ExamplesConfig
    memory: MemoryConfig
    
    @classmethod
    def load(cls, project_path: Path = None) -> "PyNextConfig":
        """Load merged config from global + project + env."""
    
    def get_mode(self, name: str) -> Optional[ModeConfig]:
        """Get a specific mode by name."""
    
    def get_pattern(self, name: str) -> Optional[Pattern]:
        """Get a pattern by name."""
    
    def get_patterns_by_tags(self, tags: List[str]) -> List[Pattern]:
        """Get patterns matching any of the given tags."""
    
    def substitute_vars(self, text: str) -> str:
        """Replace ${var} with resolved values."""
    
    def to_prompt(self) -> str:
        """Format config as context for LLM prompts."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
```

### ConfigResolver Class

```python
from pynext.app.config import ConfigResolver, ConfigContext

class ConfigResolver:
    """Resolves config based on context."""
    
    def __init__(self, config: PyNextConfig):
        """Initialize with base config."""
    
    def resolve_sync(self, ctx: ConfigContext) -> ResolvedConfig:
        """Resolve config synchronously (Python conditions only)."""
    
    async def resolve(self, ctx: ConfigContext) -> ResolvedConfig:
        """Resolve config with LLM conditions."""
```

### ConfigContext Class

```python
from dataclasses import dataclass

@dataclass
class ConfigContext:
    """Context for condition evaluation."""
    
    file_type: str = ""           # page, island, api, etc.
    intent: str = ""              # new_app, add_feature
    description: str = ""         # User's description
    mode: str = "development"     # Active mode
    project: Optional[Any] = None # Project context
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for eval context."""
```

### ResolvedConfig Class

```python
@dataclass
class ResolvedConfig:
    """Fully resolved configuration."""
    
    system_prompt: str = ""
    suffix_prompt: str = ""
    prompts: List[str] = field(default_factory=list)
    rules: List[str] = field(default_factory=list)
    patterns: List[Pattern] = field(default_factory=list)
    validation: ValidationRules = field(default_factory=ValidationRules)
    style: CodeStyle = field(default_factory=CodeStyle)
    
    def get_system_prompt(self) -> str:
        """Get full system prompt with all additions."""
    
    def get_full_prompt(self) -> str:
        """Get complete prompt for AI."""
```

### Usage Example

```python
from pathlib import Path
from pynext.app.config import (
    PyNextConfig,
    ConfigResolver,
    ConfigContext,
)

# Load config
config = PyNextConfig.load(project_path=Path("."))

# Access settings
print(config.ai.model)
print(config.style.naming_convention)

# Get patterns
pattern = config.get_pattern("api_crud")
if pattern:
    code = pattern.render(Model="User", model="user")

# Resolve for context
resolver = ConfigResolver(config)
ctx = ConfigContext(
    file_type="api",
    intent="add_feature",
    description="user authentication API",
    mode="strict",
)
resolved = resolver.resolve_sync(ctx)

# Use resolved config
prompt = resolved.get_full_prompt()
```

### Global Functions

```python
from pynext.app.config import get_config, reset_config, validate_config

# Get singleton instance
config = get_config(project_path=Path("."))

# Reset (for testing)
reset_config()

# Validate config file
errors = validate_config(Path("pynext.toml"))
if errors:
    for error in errors:
        print(f"Error: {error}")
```

---

## Best Practices

### 1. Start with Defaults

Only override what you need:

```toml
# Good: Override only what's different
[ai]
model = "claude-opus-4"

# Bad: Copy entire default config
```

### 2. Use Modes for Context Switching

```toml
# Define modes once
[mode.prototype]
# Fast iteration settings

[mode.production]
# Full validation settings

# Switch as needed
pynext app new "feature" --mode prototype  # Quick iteration
pynext app new "feature" --mode production # Final version
```

### 3. Leverage Conditionals

```toml
# Instead of manual prompts, use conditionals
[[conditional]]
priority = 80
when = "file_type == 'api'"
prompt = "APIs need auth"

# AI automatically gets right context
```

### 4. Create Reusable Patterns

```toml
# Define patterns for common code
[patterns.form_island]
description = "Form with validation"
tags = ["island", "form"]
code = '...'

# Patterns are suggested automatically
```

### 5. Validate Your Config

```bash
# Before committing changes
pynext config validate

# Fix any errors before use
```

### 6. Document Team Standards

```toml
[team]
component_prefix = "Acme"
file_header = "# Copyright..."

[rules]
custom = """
Team-specific rules:
1. All PRs need review
2. Use feature branches
"""
```

---

## Complete Example Config

```toml
# pynext.toml - Complete Example Configuration
# ============================================

# ============================================
# VARIABLES
# ============================================
[vars]
company = "Acme Corp"
year = 2025
auth_module = "utils.auth"
api_version = "v1"
db_host = "${DATABASE_HOST | localhost}"

[vars.computed]
copyright = "'Copyright ' + str(year) + ' ' + company"

# ============================================
# AI SETTINGS
# ============================================
[ai]
model = "claude-sonnet-4-20250514"
mode = "plan"
complexity = "auto"
max_thoughts = 5
verbose = false

# ============================================
# CODE STYLE
# ============================================
[style]
naming_convention = "snake_case"
class_naming = "PascalCase"
max_line_length = 88
quote_style = "double"
docstring_style = "google"

# ============================================
# VALIDATION
# ============================================
[validation]
require_docstrings = true
require_type_hints = true
require_tests = false
max_function_lines = 50
forbidden_imports = ["os.system", "eval", "exec"]

# ============================================
# TEAM STANDARDS
# ============================================
[team]
component_prefix = "Acme"
file_header = """
# ${copyright}
# SPDX-License-Identifier: MIT
"""

# ============================================
# PROMPTS
# ============================================
[prompts]
system = """
You are an expert PyNext developer at ${company}.
Follow our coding standards strictly.
"""
suffix = "Include accessibility attributes."
context = "B2B SaaS for inventory management."

[prompts.api]
prefix = "All APIs require authentication."
suffix = "Return consistent error format."

[prompts.island]
prefix = "Islands must be <50KB hydrated."

# ============================================
# MODES
# ============================================
[mode.prototype]
description = "Fast iteration"
[mode.prototype.validation]
require_docstrings = false
require_type_hints = false

[mode.strict]
description = "Maximum safety"
extends = "production"
[mode.strict.validation]
require_tests = true
forbidden_imports = ["os.system", "eval", "exec", "subprocess"]

# ============================================
# CONDITIONALS
# ============================================
[[conditional]]
priority = 80
when = "file_type == 'api'"
prompt = "Validate all inputs."

[[conditional]]
priority = 90
when_llm = "handles payments or financial data"
prompt = "Use Decimal for money. Implement audit trails."

# ============================================
# PATTERNS
# ============================================
[patterns.auth_api]
description = "Authenticated API endpoint"
tags = ["api", "auth"]
when = "file_type == 'api'"
code = '''
@api
@require_auth
async def ${method}(request: Request):
    """${description}"""
    user = await get_current_user(request)
    ${body}
'''

# ============================================
# RULES
# ============================================
[rules]
custom = "Use Tailwind CSS. Include aria labels."

[rules.naming]
pages = "{name}.py"
islands = "{Name}.py"

[rules.structure]
required_dirs = ["pages", "components", "models"]

# ============================================
# EXAMPLES
# ============================================
[examples]
good_island = '''
@island
def Counter():
    """Accessible counter."""
    count = Signal(0)
    return button(aria_label="Increment")(f"{count()}")
'''

# ============================================
# MEMORY
# ============================================
[memory]
sync_mode = "incremental"
sync_on = ["assistant_response", "checkpoint", "exit"]
sync_batch_size = 5
```

---

## Troubleshooting

### Config Not Loading

```bash
# Check file exists
ls -la pynext.toml

# Validate syntax
pynext config validate

# Show what's loaded
pynext config show
```

### Conditional Not Matching

```bash
# Show resolved config with context
pynext config show --resolved

# Check if condition is valid Python
python -c "file_type = 'api'; print(file_type == 'api')"
```

### Variable Not Substituting

```bash
# Check vars are defined
pynext config get vars

# Test substitution
pynext config show | grep '\${'  # Should show no unresolved vars
```

### Pattern Not Found

Check that:
1. Pattern is defined in `[patterns.name]`
2. `when` condition matches current context
3. Tags match if using `get_patterns_by_tags`

```bash
# List all patterns
pynext config show | grep '\[patterns\.'
```

### Mode Not Applying

```bash
# Check mode exists
pynext config get mode.strict

# Verify extends chain
pynext config show --resolved --mode strict
```

### TOML Syntax Errors

Common issues:
- Missing quotes around strings
- Incorrect multiline string syntax (use `'''...'''`)
- Duplicate section names
- Invalid table syntax

```bash
# Validate syntax
pynext config validate

# Use a TOML linter
pip install toml
python -c "import toml; toml.load('pynext.toml')"
```
