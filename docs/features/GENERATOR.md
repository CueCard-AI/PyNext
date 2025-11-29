# Component Generator CLI

Generate pages, components, APIs, and more with intelligent defaults, interactive prompts, and optional AI assistance.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [All Generators](#all-generators)
3. [Interactive Mode](#interactive-mode)
4. [AI Mode](#ai-mode)
5. [Templates](#templates)
6. [Configuration](#configuration)
7. [API Reference](#api-reference)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start

Generate your first page in 10 seconds:

```bash
# Create a page
pynext g page blog

# Create a component
pynext g component Button

# Create an API route
pynext g api users
```

That's it! Files are created with sensible defaults and full boilerplate.

### What Just Happened?

```
my-project/
├── pages/
│   ├── blog.py           ← Created: Full page with metadata, get_data, component
│   └── api/
│       └── users.py      ← Created: REST endpoint with GET/POST handlers
├── components/
│   └── Button.py         ← Created: Reusable component with variants
```

---

## All Generators

The CLI supports 11 generator types:

| Command | Creates | Location | Description |
|---------|---------|----------|-------------|
| `pynext g page <name>` | Page | `pages/<name>.py` | Route component with metadata |
| `pynext g component <name>` | Component | `components/<name>.py` | Reusable UI component |
| `pynext g island <name>` | Island | `components/<name>.py` | Interactive client component |
| `pynext g api <name>` | API Route | `pages/api/<name>.py` | REST endpoint |
| `pynext g layout <path>` | Layout | `pages/<path>/layout.py` | Shared wrapper (persists) |
| `pynext g template <path>` | Template | `pages/<path>/template.py` | Shared wrapper (remounts) |
| `pynext g loading <path>` | Loading | `pages/<path>/loading.py` | Loading skeleton |
| `pynext g error <path>` | Error | `pages/<path>/error.py` | Error boundary |
| `pynext g middleware` | Middleware | `middleware.py` | Request interception |
| `pynext g action <name>` | Server Action | `actions/<name>.py` | Form mutation handler |
| `pynext g hook <name>` | Custom Hook | `hooks/<name>.py` | Reusable logic |

### Nested Paths

Create files in nested directories:

```bash
# Creates pages/blog/posts.py
pynext g page blog/posts

# Creates pages/dashboard/settings/layout.py
pynext g layout dashboard/settings
```

### Dynamic Routes

Use brackets for dynamic segments:

```bash
# Creates pages/products/[id].py
pynext g page "products/[id]"

# Creates pages/docs/[...slug].py (catch-all)
pynext g page "docs/[...slug]"
```

---

## Interactive Mode

By default, the CLI asks helpful questions:

```bash
$ pynext g page products

📄 Creating page: products

  Is this a dynamic route? (e.g., [id]) [y/N]: n
  Fetch data on server? (async get_data) [Y/n]: y
  Include SEO metadata? [Y/n]: y

✅ Created: pages/products.py

   → View at: http://localhost:3000/products
```

### Skip Prompts

Use `--yes` or `-y` to skip all prompts:

```bash
pynext g page products --yes
```

---

## AI Mode

Let AI generate custom code based on your requirements:

```bash
pynext g page products --ai
```

### How It Works

1. **Leading Questions**: AI asks relevant questions about your component
2. **Completeness Check**: AI evaluates if it has enough information
3. **Follow-up Questions**: AI asks clarifying questions if needed
4. **Code Generation**: AI generates production-ready code

### Example Session

```bash
$ pynext g page products --ai

🤖 AI Assistant: Let me ask a few questions about your page...

  What is this page for? (e.g., blog listing, user profile, dashboard)
  → E-commerce product catalog with filtering

  What data will this page display? (e.g., list of posts, user info)
  → Product cards with image, title, price, rating

  What can users do on this page? (e.g., click items, filter, search)
  → Filter by category, sort by price, search by name

  Any specific design style? (e.g., minimal, card-based, table)
  → Modern grid layout with hover effects

🤖 I have a few more questions to make sure I understand...

  Should the search filter results in real-time or on button click?
  → Real-time as user types

  How many products should display per page?
  → 12 with pagination

  Anything else I should know? (press Enter to skip)
  → Include an "Add to Cart" button on each card

🤖 Generating your component...

✅ Created: pages/products.py
```

### Quick Generation

Skip the interview with a direct prompt:

```bash
pynext g page products --ai --prompt "E-commerce product grid with filtering, search, and pagination"
```

### Setup

Set your Anthropic API key:

```bash
# Environment variable (recommended)
export ANTHROPIC_API_KEY="sk-ant-..."

# Or pass directly
pynext g page products --ai --api-key "sk-ant-..."
```

Install the anthropic package:

```bash
pip install anthropic
# Or add to pynext.requirements.txt
```

---

## Templates

Each generator has two template styles:

### Minimal Template

Just the essentials, no boilerplate:

```bash
pynext g page blog --minimal
```

```python
"""Page: Blog"""
from pynext import div, h1

def blog():
    return div(
        h1("Blog")
    )
```

### Full Template (Default)

Complete with imports, docstrings, examples:

```bash
pynext g page blog --full
# or just
pynext g page blog
```

```python
"""
Blog Page

Route: /blog
"""

from pynext import (
    div, h1, p, section,
    Metadata, Link,
)

# SEO metadata
metadata = Metadata(
    title="Blog",
    description="Blog page",
)

async def get_data():
    """Fetch data for this page."""
    return {"message": "Hello from Blog!"}

def blog(data: dict):
    """Blog Page"""
    return div(class_="container mx-auto px-4 py-8")(
        section(class_="mb-8")(
            h1(class_="text-3xl font-bold text-gray-900")("Blog"),
            p(class_="mt-2 text-gray-600")(data.get("message", "Welcome!")),
        ),
        section(class_="space-y-4")(
            p("Edit this page at pages/blog.py"),
            Link(href="/")("← Back to Home"),
        ),
    )
```

---

## Configuration

### src/ Folder Support

The generator auto-detects `src/` folder structure:

```
my-project/
├── src/
│   ├── pages/          ← Detected automatically
│   └── components/
```

When detected, files are created in `src/pages/` instead of `pages/`.

### Force Overwrite

Use `--force` or `-f` to overwrite existing files:

```bash
pynext g page blog --force
```

---

## API Reference

### Generator Class

```python
from pynext.generator import Generator

gen = Generator(Path("."))

# Create a page
path = gen.create("page", "blog")

# Create with options
path = gen.create(
    "component", 
    "Button",
    template_style="full",
    props={"has_variants": True},
    force=True,
)

# Create from AI-generated content
path = gen.create_from_content(
    "page",
    "products",
    ai_generated_code,
)

# List existing files
pages = gen.list_existing("page")
```

### Validators

```python
from pynext.generator.validators import (
    validate_name,
    validate_path,
    to_pascal_case,
    to_snake_case,
)

# Validate and normalize name
name = validate_name("user-profile", "component")  # "UserProfile"

# Validate path
path = validate_path("blog/posts", "page")  # Path("blog/posts")

# Case conversions
to_pascal_case("user_profile")  # "UserProfile"
to_snake_case("UserProfile")    # "user_profile"
```

### Templates

```python
from pynext.generator.templates import (
    get_template,
    render_template,
    list_generator_types,
)

# Get template
template = get_template("page", "full")

# Render with variables
content = render_template(
    template,
    name="blog",
    title="Blog",
    route="blog",
)

# List all types
types = list_generator_types()  # ["page", "component", ...]
```

### AI Generation

```python
from pynext.generator.ai import (
    ai_interview,
    generate_with_ai,
    evaluate_completeness,
)

# Run interactive interview
answers = ai_interview("page", "products")

# Generate code from answers
code = generate_with_ai("page", "products", answers)

# Check if more info needed
follow_ups = evaluate_completeness(
    "page", "products", answers, api_key="..."
)
```

---

## Troubleshooting

### Common Issues

#### "Name is reserved"

Some names are reserved by Python or PyNext:

```bash
# Bad - reserved names
pynext g page class
pynext g page layout

# Good - use different names
pynext g page my_class
pynext g page page_layout
```

#### "File already exists"

Use `--force` to overwrite:

```bash
pynext g page blog --force
```

#### "API key required"

For AI mode, set your Anthropic API key:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

#### "anthropic module not found"

Install the package:

```bash
pip install anthropic
```

### Getting Help

```bash
# General help
pynext g --help

# Specific command help
pynext g page --help
```

---

## Performance

The generator is designed for speed:

| Action | Time |
|--------|------|
| Generate page (non-interactive) | <50ms |
| Generate component | <50ms |
| AI generation | ~2-3s (API call) |

---

## Testing

The Generator CLI has **106 comprehensive tests**:

### Test Categories

| Category | Tests | Coverage |
|----------|-------|----------|
| Validators | 15 | Name/path validation, case conversion |
| Templates | 22 | All 11 types × 2 styles (minimal/full) |
| Core Logic | 25 | Generator class, path detection, file creation |
| Prompts | 12 | Interactive mode for each type |
| CLI Integration | 13 | Command parsing, flags, aliases |
| **AI Integration** | **19** | **Real API tests with Anthropic Claude** |

### AI Integration Tests

These tests **actually call the Anthropic API** to verify AI generation works:

```bash
# Run all generator tests (requires ANTHROPIC_API_KEY for AI tests)
ANTHROPIC_API_KEY="your-key" python -m pytest tests/unit/test_generator.py -v
```

| Test | What It Verifies |
|------|------------------|
| `test_evaluate_completeness_real_api_sufficient` | AI recognizes complete requirements |
| `test_evaluate_completeness_real_api_needs_more` | AI asks follow-ups for vague input |
| `test_generate_with_ai_page` | Generates valid Python page code |
| `test_generate_with_ai_component` | Generates valid component code |
| `test_generate_with_ai_island` | Generates islands with signals/state |
| `test_generate_with_ai_api_endpoint` | Generates API routes with methods |
| `test_generate_with_ai_server_action` | Generates server actions |
| `test_generate_with_ai_hook` | Generates custom hooks |
| `test_generate_with_ai_complex_component` | Generates complex DataTable |
| `test_generate_code_uses_tailwind` | Verifies Tailwind CSS usage |
| `test_generate_code_has_docstrings` | Verifies proper docstrings |

All generated code is validated with Python's `compile()` to ensure syntax correctness.

---

## Next Steps

After generating a component:

1. **Pages**: Run `pynext dev` and visit the URL shown
2. **Components**: Import in your pages: `from components.Button import Button`
3. **Islands**: Same as components, but with client-side interactivity
4. **APIs**: Test with curl or fetch: `curl http://localhost:3000/api/users`

