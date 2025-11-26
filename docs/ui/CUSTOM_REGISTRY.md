# Custom Component Registries

> **Create and share your own PyNext component libraries**

PyNext supports three tiers of components. This guide covers **Tier 3: Custom Registries** — how to create, publish, and consume custom component libraries.

---

## The Three Tiers

```
┌─────────────────────────────────────────────────────────────────┐
│                   PyNext Component Sources                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  TIER 1: Native Libraries (built-in, no install needed)         │
│  ─────────────────────────────────────────────────────          │
│  from pynext.tw import tw, cn                                    │
│  from pynext.shadcn import Button, Card, Dialog                  │
│                                                                   │
│  TIER 2: Official Registries (pynext ui add)                     │
│  ─────────────────────────────────────────────────────          │
│  pynext ui add button              # Copy to components/ui/      │
│  pynext ui add --all               # All ShadCN components       │
│                                                                   │
│  TIER 3: Custom Registries (pynext registry)    ← This guide    │
│  ─────────────────────────────────────────────────────          │
│  pynext registry add acme-ui --url=https://ui.acme.com          │
│  pynext registry install acme-ui:data-table                      │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Using Custom Registries

### Add a Registry

```bash
# From a URL
pynext registry add acme-ui --url=https://ui.acme.com

# From GitHub
pynext registry add startup-kit --url=github:awesome/startup-kit
```

### Install Components

```bash
# Install a specific component
pynext registry install acme-ui:data-table

# This creates:
# components/acme-ui/data_table.py
```

### List Registries

```bash
pynext registry list
```

### Remove a Registry

```bash
pynext registry remove acme-ui
```

---

## Creating a Registry

### 1. Create the Registry Definition

Create `pynext-registry.json` in your repository root:

```json
{
  "name": "acme-ui",
  "version": "1.0.0",
  "description": "Acme Corp Design System",
  "author": "Acme Design Team",
  "base_styles": "styles/acme-theme.css",
  "components": {
    "data-table": {
      "name": "DataTable",
      "description": "Sortable, filterable data table",
      "files": ["data_table.py", "column_header.py"],
      "styles": "data_table.css",
      "dependencies": {
        "pynext": ["pynext.shadcn.table", "pynext.tw"],
        "npm": ["@tanstack/table-core"]
      }
    },
    "metric-card": {
      "name": "MetricCard",
      "description": "Dashboard metric display",
      "files": ["metric_card.py"],
      "dependencies": {
        "pynext": ["pynext.shadcn.card"]
      }
    }
  }
}
```

### 2. Create Component Files

```python
# data_table.py
"""
DataTable Component

Part of: acme-ui
Dependencies: pynext.shadcn.table, @tanstack/table-core
"""

from pynext.tw import tw, cn
from pynext.shadcn import Table, TableHeader, TableBody, TableRow, TableCell

def DataTable(
    data: list,
    columns: list,
    sortable: bool = True,
    filterable: bool = True,
    class_: str = "",
):
    """
    A feature-rich data table with sorting and filtering.
    
    Args:
        data: List of row dictionaries
        columns: Column definitions
        sortable: Enable column sorting
        filterable: Enable column filtering
        class_: Additional CSS classes
    """
    # Implementation...
    return Table(class_=cn("w-full", class_))[
        TableHeader()[
            TableRow()[
                [TableCell()[col["header"]] for col in columns]
            ]
        ],
        TableBody()[
            [
                TableRow()[
                    [TableCell()[row.get(col["key"], "")] for col in columns]
                ]
                for row in data
            ]
        ]
    ]
```

### 3. Organize Your Repository

```
my-component-library/
├── pynext-registry.json          # Registry definition
├── README.md                      # Documentation
├── components/
│   ├── data_table.py             # Component files
│   ├── column_header.py
│   └── metric_card.py
├── styles/
│   ├── acme-theme.css            # Base styles
│   └── data_table.css            # Component styles
└── examples/
    └── demo.py                    # Usage examples
```

### 4. Publish

**Option A: GitHub**
Push to GitHub, users add via:
```bash
pynext registry add my-lib --url=github:username/my-component-library
```

**Option B: Self-Hosted**
Host `pynext-registry.json` at a URL:
```bash
pynext registry add my-lib --url=https://components.mycompany.com
```

---

## Registry Schema Reference

### Root Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✓ | Registry identifier |
| `version` | string | ✓ | Semver version |
| `description` | string | | Human-readable description |
| `author` | string | | Author name/organization |
| `base_styles` | string | | Path to base CSS file |
| `components` | object | ✓ | Component definitions |

### Component Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✓ | Export name (PascalCase) |
| `description` | string | | What the component does |
| `files` | string[] | ✓ | Python files to install |
| `styles` | string | | CSS file for this component |
| `dependencies.pynext` | string[] | | Required PyNext imports |
| `dependencies.npm` | string[] | | Required NPM packages |

---

## Best Practices

### 1. Clear Dependencies

Always declare what your components need:

```json
{
  "dependencies": {
    "pynext": ["pynext.shadcn.button", "pynext.tw"],
    "npm": ["@tanstack/table-core@^8.0.0"]
  }
}
```

### 2. Document Everything

Each component file should include:

```python
"""
ComponentName - Brief description

Part of: registry-name
Dependencies: list, of, deps

Usage:
    from components.registry_name import ComponentName
    
    ComponentName(prop="value")[children]

Props:
    prop (type): Description. Default: value
"""
```

### 3. Follow PyNext Conventions

```python
# ✓ Use class_ not className
def MyComponent(class_: str = ""):

# ✓ Use [children] syntax
Button()["Click me"]

# ✓ Use pynext.tw for classes
from pynext.tw import tw, cn

# ✓ Allow class overrides
return div(class_=cn(base_classes, class_))[...]
```

### 4. Provide Examples

Include an `examples/` directory with working demos:

```python
# examples/data_table_demo.py
from components.acme_ui import DataTable

def Demo():
    data = [
        {"name": "Alice", "role": "Engineer"},
        {"name": "Bob", "role": "Designer"},
    ]
    
    columns = [
        {"key": "name", "header": "Name"},
        {"key": "role", "header": "Role"},
    ]
    
    return DataTable(data=data, columns=columns)
```

### 5. Version Your Components

Use semantic versioning and maintain a CHANGELOG:

```
## [1.2.0] - 2024-01-15
### Added
- DataTable: New `exportable` prop for CSV export
- MetricCard: Sparkline support

### Fixed
- DataTable: Sort icons alignment on mobile
```

---

## Integration with Official Components

Your components can extend PyNext's official ShadCN components:

```python
from pynext.shadcn import (
    Card, CardHeader, CardTitle, CardContent,
    Badge
)
from pynext.tw import tw, cn

def MetricCard(
    title: str,
    value: str | int,
    change: float = None,
    trend: str = None,  # "up" | "down" | "neutral"
):
    """A dashboard metric card with optional trend indicator."""
    
    trend_colors = {
        "up": "text-green-500",
        "down": "text-red-500", 
        "neutral": "text-gray-500",
    }
    
    return Card()[
        CardHeader(class_=tw.pb_2)[
            CardTitle(class_=tw.text_sm.font_medium.text_muted_foreground)[
                title
            ]
        ],
        CardContent()[
            div(class_=tw.flex.items_baseline.gap_2)[
                span(class_=tw.text_2xl.font_bold)[value],
                change is not None and Badge(
                    variant="outline",
                    class_=trend_colors.get(trend, ""),
                )[
                    f"{'+' if change > 0 else ''}{change}%"
                ],
            ]
        ]
    ]
```

---

## CLI Reference

### `pynext registry add`

```bash
pynext registry add <name> --url=<url>
```

| Argument | Description |
|----------|-------------|
| `name` | Local name for the registry |
| `--url` | Registry URL or `github:owner/repo` |

### `pynext registry remove`

```bash
pynext registry remove <name>
```

### `pynext registry list`

```bash
pynext registry list
```

Shows all registered sources with their URLs and available components.

### `pynext registry install`

```bash
pynext registry install <registry>:<component>
```

Installs component files to `components/<registry>/`.

### `pynext registry init`

```bash
pynext registry init
```

Creates a template `pynext-registry.json` for starting your own library.

---

## File Structure After Install

When you install components, they're placed in your project:

```
my-app/
├── components/
│   ├── ui/                    # Official PyNext components
│   │   ├── button.py
│   │   └── card.py
│   ├── acme-ui/               # Custom registry
│   │   ├── data_table.py
│   │   └── metric_card.py
│   └── startup-kit/           # Another registry
│       └── pricing_card.py
├── pages/
└── pynext.config.py
```

Import like:

```python
from components.acme_ui import DataTable
from components.startup_kit import PricingCard
```

---

## Troubleshooting

### Registry Not Found

```bash
pynext registry install acme-ui:table
# Error: Registry not found: acme-ui
```

**Solution:** Add the registry first:
```bash
pynext registry add acme-ui --url=https://...
```

### Component Not Found

```bash
pynext registry install acme-ui:nonexistent
# Error: Component not found: nonexistent in acme-ui
```

**Solution:** Check available components:
```bash
pynext registry list
```

### Missing Dependencies

After install, if imports fail:
```bash
pynext deps install
```

---

## Related

- [Official Components](./GETTING_STARTED.md) - Tier 1 & 2 components
- [Tailwind Integration](./TAILWIND.md) - Styling your components
- [ShadCN Components](../shadcn/README.md) - Base components to extend

