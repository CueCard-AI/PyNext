# Combobox

A searchable dropdown for selecting from a list of options. Supports filtering, multi-select, async search, and creating new items.

## Installation

```python
from pynext.shadcn import (
    Combobox, ComboboxTrigger, ComboboxContent,
    ComboboxInput, ComboboxItem, ComboboxEmpty,
    ComboboxGroup, ComboboxSeparator, ComboboxCreate
)
```

## Basic Usage

```python
frameworks = [
    {"value": "react", "label": "React"},
    {"value": "vue", "label": "Vue"},
    {"value": "svelte", "label": "Svelte"},
]

Combobox(value=selected, on_value_change=set_selected)[
    ComboboxTrigger()[
        Button(variant="outline", class_="w-[200px] justify-between")[
            selected or "Select framework...",
            "▼"
        ]
    ],
    ComboboxContent()[
        ComboboxInput(placeholder="Search framework..."),
        ComboboxEmpty()["No framework found."],
        [
            ComboboxItem(value=fw["value"])[fw["label"]]
            for fw in frameworks
        ]
    ]
]
```

## Examples

### Grouped Items

```python
Combobox()[
    ComboboxTrigger()[...],
    ComboboxContent()[
        ComboboxInput(placeholder="Search..."),
        ComboboxEmpty()["No results."],
        
        ComboboxGroup(heading="Frontend")[
            ComboboxItem(value="react")["React"],
            ComboboxItem(value="vue")["Vue"],
        ],
        ComboboxSeparator(),
        ComboboxGroup(heading="Backend")[
            ComboboxItem(value="node")["Node.js"],
            ComboboxItem(value="python")["Python"],
        ],
    ]
]
```

### With Icons

```python
ComboboxItem(value="settings")[
    span(class_="flex items-center gap-2")[
        "⚙️",
        "Settings"
    ]
]
```

### Multi-Select

```python
Combobox(multiple=True, value=selected_list)[
    ComboboxTrigger()[
        Button()[f"{len(selected_list)} selected"]
    ],
    ComboboxContent()[
        # Items toggle selection instead of replacing
    ]
]
```

### Disabled Items

```python
ComboboxItem(value="premium", disabled=True)[
    "Premium Feature (upgrade required)"
]
```

### Create New Item

Allow users to create new items when no matches are found:

```python
@server_action
async def create_tag(query: str):
    """Create a new tag in the database."""
    tag = await db.tags.create(name=query)
    return tag

Combobox(
    value=selected,
    on_value_change=set_selected,
    allow_create=True,
    on_create=create_tag
)[
    ComboboxTrigger()[
        Button(variant="outline")["Select or create tag..."]
    ],
    ComboboxContent()[
        ComboboxInput(placeholder="Search or type to create..."),
        ComboboxEmpty()["No tags found."],
        ComboboxCreate()["Create tag"],  # Shows: "Create tag "newvalue""
        [
            ComboboxItem(value=tag["id"])[tag["name"]]
            for tag in tags
        ]
    ]
]
```

How it works:

```
┌──────────────────────────────────────┐
│ Search or type to create...          │
├──────────────────────────────────────┤
│ (no matches for "newvalue")          │
├──────────────────────────────────────┤
│ ➕ Create tag "newvalue"             │  ← Click or Enter
└──────────────────────────────────────┘
          │
          ▼
    Dispatches 'pynext:combobox:create' event
    with { query: "newvalue" }
```

The `ComboboxCreate` component:
- Only appears when `allow_create=True` is set on the root `Combobox`
- Only shows when there are no matching items AND the search input has text
- Displays the current query so users know what will be created
- Triggers on click or Enter key

## API Reference

### Combobox

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `value` | `str` | `None` | Selected value |
| `on_value_change` | `Callable` | `None` | Selection callback |
| `on_search` | `Callable` | `None` | Async search callback |
| `on_create` | `Callable` | `None` | Create new item callback |
| `multiple` | `bool` | `False` | Allow multiple selection |
| `allow_create` | `bool` | `False` | Show create option when no matches |
| `open` | `bool` | `None` | Controlled open state |
| `on_open_change` | `Callable` | `None` | Callback when open state changes |

### ComboboxContent

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `side` | `string` | `"bottom"` | Dropdown position |
| `align` | `string` | `"start"` | Alignment |

### ComboboxInput

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `placeholder` | `str` | `"Search..."` | Placeholder text |

### ComboboxItem

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `value` | `str` | required | Item value |
| `disabled` | `bool` | `False` | Disable selection |

### ComboboxCreate

Shows a "create new" option when no items match the search query.

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `class_` | `str` | `None` | Additional CSS classes |

### ComboboxEmpty

Shown when no items match the search.

### ComboboxGroup

Groups items with an optional heading.

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `heading` | `str` | `None` | Group heading text |

### ComboboxSeparator

Visual separator between groups or items.

## Keyboard Navigation

- `↓/↑` - Navigate items
- `Enter` - Select highlighted item (or create new if `allow_create` and no matches)
- `Escape` - Close dropdown
- Type to filter items

## Async Search

```python
@server_action
async def search_users(query: str):
    return await db.search_users(query)

Combobox(on_search=search_users)[
    ComboboxTrigger()[...],
    ComboboxContent()[
        ComboboxInput(placeholder="Search users..."),
        ComboboxEmpty()["No users found."],
        # Items populated from search results
    ]
]
```

