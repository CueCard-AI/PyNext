# PyNext Configuration System

Configure the AI App Builder with `pynext.toml` for preferences, standards, patterns, and conditional prompts.

## Overview

The PyNext configuration system provides:

- **Hierarchical config**: Global → Project → Feature level
- **Variables**: Static and computed values usable anywhere
- **Modes**: Named bundles (prototype, production, strict)
- **Conditional prompts**: Python and LLM-evaluated conditions
- **Patterns**: Reusable code templates
- **Rules**: Validation and naming conventions

## Quick Start

```bash
# Create a config file
pynext config init

# Show current configuration
pynext config show

# Validate config
pynext config validate
```

## Config Locations

Configs are loaded in this order (later overrides earlier):

1. `~/.config/pynext/config.toml` - Global defaults
2. `./pynext.toml` - Project config
3. `./.pynext/config.toml` - Hidden project config
4. Environment variables - Env overrides
5. CLI arguments - Command overrides

## Config File Reference

### AI Settings (`[ai]`)

```toml
[ai]
model = "claude-sonnet-4-20250514"  # AI model to use
mode = "plan"                       # plan, agent, ask
complexity = "auto"                 # auto, minimal, small, medium, large, enterprise
max_thoughts = 5                    # Max thought cycles
verbose = false                     # Show AI thinking
temperature = 0.7                   # Response randomness
```

**Environment overrides:**
- `ANTHROPIC_MODEL` → `ai.model`
- `PYNEXT_MODE` → Active mode

### Code Style (`[style]`)

```toml
[style]
naming_convention = "snake_case"  # snake_case, camelCase
class_naming = "PascalCase"       # Class naming style
max_line_length = 88              # Max characters per line
quote_style = "double"            # double, single
trailing_comma = true             # Include trailing commas
docstring_style = "google"        # google, numpy, sphinx
indent_size = 4                   # Spaces per indent
```

### Validation Rules (`[validation]`)

```toml
[validation]
require_docstrings = true         # Require docstrings
require_type_hints = true         # Require type hints
require_tests = false             # Require test files
max_function_lines = 50           # Max lines per function
max_file_lines = 500              # Max lines per file
forbidden_imports = ["os.system", "eval", "exec"]
required_imports = []
forbidden_patterns = []
```

### Team Standards (`[team]`)

```toml
[team]
component_prefix = "Acme"         # Prefix for components
file_header = """
# Copyright 2025 Acme Corp
# SPDX-License-Identifier: MIT
"""
required_patterns = []
forbidden_patterns = []
```

### Prompts (`[prompts]`)

```toml
[prompts]
# System prompt prepended to ALL generations
system = """
You are an expert PyNext developer.
Follow our coding standards strictly.
"""

# Appended after every generation
suffix = "Always include accessibility attributes."

# Project/domain context
context = "This is a B2B SaaS for inventory management."

# Per-file-type prompts
[prompts.api]
prefix = "All API routes require authentication."
suffix = "Return consistent error format."

[prompts.island]
prefix = "Islands must be lightweight (<50KB)."
```

**Available file types:**
- `page`, `island`, `component`, `api`, `action`, `model`, `layout`, `middleware`, `util`

### Variables (`[vars]`)

```toml
[vars]
company = "Acme Corp"
year = 2025
db_host = "${DATABASE_HOST | localhost}"  # Env fallback

# Computed variables (Python expressions)
[vars.computed]
copyright = "f'Copyright {year} {company}'"
```

**Using variables:**
- Reference anywhere with `${var_name}`
- Environment fallback: `${ENV_VAR | default_value}`

### Modes (`[mode.*]`)

```toml
[mode.prototype]
description = "Fast iteration, minimal ceremony"
[mode.prototype.validation]
require_docstrings = false
require_type_hints = false
[mode.prototype.prompts]
suffix = "Keep it simple. Skip edge cases."

[mode.production]
description = "Production-ready code"
[mode.production.validation]
require_docstrings = true
require_tests = true

[mode.strict]
extends = "production"  # Inherit from production
[mode.strict.validation]
forbidden_imports = ["os.system", "eval", "exec"]
```

**Built-in modes:**
- `prototype` - Fast iteration
- `development` - Standard settings
- `production` - Full validation
- `strict` - Maximum safety

**Switching modes:**
```bash
pynext app new "blog" --mode strict
```

### Conditional Prompts (`[[conditional]]`)

```toml
[[conditional]]
priority = 80                     # Higher = applied first (0-100)
when = "file_type == 'api'"       # Python condition
prompt = "All APIs must validate input."

[[conditional]]
priority = 90
when_llm = "the user is building payment functionality"
prompt = """
PAYMENT HANDLING:
- Use Decimal for money
- Implement audit trails
"""

[[conditional]]
priority = 70
when = "project.has_auth"
prompt = "Use existing auth at ${auth_module}"
pattern = "auth_api"
```

**Condition types:**
- `when` - Python expression (fast)
- `when_llm` - Natural language (AI evaluates)
- Both can be combined (both must be true)

**Available context variables:**

| Variable | Type | Description |
|----------|------|-------------|
| `file_type` | str | page, island, api, etc. |
| `intent` | str | new_app, add_feature |
| `description` | str | User's description |
| `mode` | str | Active mode name |
| `complexity` | str | App complexity |
| `project.has_auth` | bool | Has auth system |
| `project.models` | list | Existing models |
| `project.pages` | list | Existing pages |
| `len(...)` | int | Count items |

### Patterns (`[patterns.*]`)

```toml
[patterns.auth_api]
description = "API endpoint with authentication"
tags = ["api", "auth"]
when = "file_type == 'api'"       # Only suggest when condition met
deps = ["pynext.api", "utils.auth"]
code = '''
from pynext.api import api, Request, Response
from ${auth_module} import require_auth

@api
@require_auth
async def ${method}(request: Request):
    """${description}"""
    user = await get_current_user(request)
    ${body}
'''
```

**Pattern variables:**
- Use `${var_name}` for placeholders
- Variables from `[vars]` are auto-substituted

### Rules (`[rules]`)

```toml
[rules]
custom = "1. Use Tailwind CSS\n2. Include aria labels"

[rules.always]
custom = "Always handle loading/error states."

[rules.naming]
pages = "{name}.py"
components = "{Name}.py"

[rules.structure]
required_dirs = ["pages", "components"]
required_files = ["pages/layout.py"]

[[rules.conditional]]
when = "mode == 'strict'"
custom = "All functions must have try/except"
```

### Examples (`[examples]`)

```toml
[examples]
good_island = '''
@island
def Counter():
    """Accessible counter component."""
    count = Signal(0)
    return button(aria_label="Increment")(f"{count()}")
'''

bad_island = '''
def counter():  # BAD: Missing @island, no docs
    return div(style="color:red")  # BAD: inline styles
'''
```

### Memory Settings (`[memory]`)

```toml
[memory]
sync_mode = "incremental"         # incremental, full, manual
sync_on = ["assistant_response", "checkpoint", "exit"]
sync_batch_size = 5
max_entries_in_memory = 1000
```

## CLI Commands

```bash
# Create config
pynext config init                # Create pynext.toml
pynext config init --force        # Overwrite existing

# View config
pynext config show                # Show config
pynext config show --json         # As JSON
pynext config show --resolved     # With conditionals applied
pynext config get ai.model        # Get specific value

# Validate
pynext config validate            # Check syntax
```

## Python API

```python
from pynext.app.config import PyNextConfig, ConfigResolver, ConfigContext

# Load config
config = PyNextConfig.load(project_path=Path("."))

# Access settings
print(config.ai.model)
print(config.style.naming_convention)

# Get patterns
pattern = config.get_pattern("auth_api")
code = pattern.render(method="GET", description="List users")

# Resolve for context
resolver = ConfigResolver(config)
resolved = await resolver.resolve(ConfigContext(
    file_type="api",
    intent="add_feature",
    description="user authentication",
))

# Get full prompt
prompt = resolved.get_full_prompt()
```

## Config Loading Pipeline

```
1. LOAD CONFIGS (merge in order)
   ~/.config/pynext/config.toml  →  Base
   ./pynext.toml                 →  Project
   Environment variables         →  Env
   CLI arguments                 →  Command

2. RESOLVE VARIABLES
   ${var} → lookup in [vars]
   ${VAR | default} → env or default
   [vars.computed] → evaluate

3. APPLY MODE
   --mode or active_mode → load [mode.X]
   extends → inherit parent first

4. EVALUATE CONDITIONALS
   when (Python) → bool
   when_llm (AI) → bool
   Merge by priority

5. OUTPUT: ResolvedConfig
   - System prompt
   - Suffix
   - Rules
   - Patterns
```

## Best Practices

1. **Start with defaults** - Only override what you need
2. **Use modes** - Bundle settings for different contexts
3. **Leverage conditionals** - Context-aware prompts
4. **Create patterns** - Reusable code templates
5. **Validate config** - Run `pynext config validate`

## Troubleshooting

### Config not loading

```bash
# Check if file exists
ls -la pynext.toml

# Validate syntax
pynext config validate

# Show what's loaded
pynext config show
```

### Conditional not matching

```bash
# Show resolved config with context
pynext config show --resolved
```

### Pattern not found

Check that:
1. Pattern is defined in `[patterns.name]`
2. `when` condition matches
3. Tags match if using `get_patterns_by_tags`

