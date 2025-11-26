# Combobox

> **Like a searchable dropdown — type to filter, click to select**

A searchable dropdown that combines text input with a list of options.

---

## First Principles: What IS a Combobox?

### The Core Concept

A combobox is a **dropdown you can type into**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         THE COMBOBOX CONCEPT                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Regular Dropdown:                 Combobox:                                 │
│  ─────────────────                 ─────────                                 │
│                                                                              │
│  ┌──────────────┐                  ┌──────────────┐                         │
│  │ Select... ▼  │                  │ Type to search│                        │
│  └──────────────┘                  └──────────────┘                         │
│  ┌──────────────┐                  ┌──────────────┐                         │
│  │ Apple        │                  │ 🔍 ap        │  ← User types "ap"     │
│  │ Banana       │                  └──────────────┘                         │
│  │ Cherry       │                  ┌──────────────┐                         │
│  │ Dragonfruit  │                  │ ✓ Apple      │  ← Filtered!            │
│  │ Elderberry   │                  └──────────────┘                         │
│  │ ... scroll   │                                                            │
│  └──────────────┘                  Much faster to find!                      │
│                                                                              │
│  Must scroll through all          Type → Filter → Select                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### When to Use Combobox vs Dropdown

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CHOOSING THE RIGHT COMPONENT                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  USE DROPDOWN WHEN:                USE COMBOBOX WHEN:                        │
│  ──────────────────                ─────────────────                         │
│                                                                              │
│  • Few options (< 7)               • Many options (> 7)                      │
│  • Options are familiar            • Options need searching                  │
│  • No typing needed                • User might know partial name            │
│  • Simple selection                • Dynamic/API data                        │
│                                    • User can create new options             │
│                                                                              │
│  Examples:                         Examples:                                 │
│  • Status (Active/Inactive)        • Country selector (195 countries)        │
│  • Priority (Low/Medium/High)      • User search                             │
│  • Theme (Light/Dark)              • Tags/labels                             │
│                                    • Framework selector                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## How It Works

### Component Hierarchy

```
Combobox                           ← Root: manages state
├── ComboboxTrigger                ← Button showing selection
│   └── "Select framework..."
└── ComboboxContent                ← Dropdown panel
    ├── ComboboxInput              ← Search input
    ├── ComboboxEmpty              ← "No results" message
    ├── ComboboxGroup              ← Optional grouping
    │   ├── ComboboxLabel          ← Group heading
    │   └── ComboboxItem           ← Selectable option
    └── ComboboxCreate             ← "Create new" option
```

### The Interaction Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         COMBOBOX INTERACTION                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. CLICK TRIGGER                                                            │
│     └── Dropdown opens                                                       │
│     └── Input is focused                                                     │
│                                                                              │
│  2. TYPE QUERY                                                               │
│     └── Items filtered in real-time                                          │
│     └── Matching text highlighted                                            │
│     └── No matches → Show ComboboxEmpty                                      │
│                                                                              │
│  3. SELECT ITEM                                                              │
│     └── Click or press Enter                                                 │
│     └── Trigger updates to show selection                                    │
│     └── Dropdown closes                                                      │
│                                                                              │
│  4. CREATE NEW (if allowed)                                                  │
│     └── No matches + allowCreate                                             │
│     └── Show "Create [query]" option                                         │
│     └── Click creates new item                                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Installation

```bash
pynext ui add combobox
```

Or import directly:

```python
from pynext.shadcn import (
    Combobox, ComboboxTrigger, ComboboxContent,
    ComboboxInput, ComboboxEmpty, ComboboxGroup,
    ComboboxItem, ComboboxCreate
)
```

---

## Step-by-Step Usage

### Step 1: Basic Combobox

```python
frameworks = [
    {"value": "next", "label": "Next.js"},
    {"value": "svelte", "label": "SvelteKit"},
    {"value": "nuxt", "label": "Nuxt.js"},
    {"value": "remix", "label": "Remix"},
    {"value": "astro", "label": "Astro"},
]

Combobox()[
    ComboboxTrigger(class_="w-[200px]")[
        "Select framework..."
    ],
    ComboboxContent()[
        ComboboxInput(placeholder="Search framework..."),
        ComboboxEmpty()["No framework found."],
        [
            ComboboxItem(value=f["value"])[f["label"]]
            for f in frameworks
        ]
    ]
]
```

### Step 2: Controlled with Signal

```python
from pynext import Signal

selected = Signal("")

Combobox(
    value=selected.value,
    on_value_change=selected.set
)[
    ComboboxTrigger(class_="w-[200px]")[
        selected.value and next(
            f["label"] for f in frameworks if f["value"] == selected.value
        ) or "Select framework..."
    ],
    ComboboxContent()[
        ComboboxInput(placeholder="Search..."),
        ComboboxEmpty()["No results."],
        [ComboboxItem(value=f["value"])[f["label"]] for f in frameworks]
    ]
]
```

### Step 3: With Groups

```python
Combobox()[
    ComboboxTrigger()["Select a fruit..."],
    ComboboxContent()[
        ComboboxInput(placeholder="Search fruits..."),
        ComboboxEmpty()["No fruit found."],
        
        ComboboxGroup()[
            ComboboxLabel()["Citrus"],
            ComboboxItem(value="orange")["Orange"],
            ComboboxItem(value="lemon")["Lemon"],
            ComboboxItem(value="lime")["Lime"],
        ],
        
        ComboboxGroup()[
            ComboboxLabel()["Berries"],
            ComboboxItem(value="strawberry")["Strawberry"],
            ComboboxItem(value="blueberry")["Blueberry"],
        ],
    ]
]
```

### Step 4: Allow Creating New Items

```python
from pynext import Signal, server_action

tags = Signal(["bug", "feature", "docs"])

@server_action
async def create_tag(name: str):
    # Save to database
    return {"id": ..., "name": name}

Combobox(
    allow_create=True,
    on_create=lambda text: create_tag(text)
)[
    ComboboxTrigger()["Add tag..."],
    ComboboxContent()[
        ComboboxInput(placeholder="Search or create..."),
        ComboboxEmpty()["No tags found."],
        [ComboboxItem(value=tag)[tag] for tag in tags.value],
        ComboboxCreate()  # Shows "Create [query]" when no matches
    ]
]
```

---

## Common Patterns

### Pattern 1: Country Selector

```python
Combobox()[
    ComboboxTrigger(class_="w-[280px]")[
        span(class_="flex items-center gap-2")[
            selected_country.flag,
            selected_country.name or "Select country..."
        ]
    ],
    ComboboxContent()[
        ComboboxInput(placeholder="Search countries..."),
        ComboboxEmpty()["No country found."],
        [
            ComboboxItem(value=c["code"])[
                span(class_="flex items-center gap-2")[
                    c["flag"],
                    c["name"]
                ]
            ]
            for c in countries
        ]
    ]
]
```

### Pattern 2: User Selector with Avatars

```python
Combobox()[
    ComboboxTrigger()[
        Avatar(class_="h-6 w-6 mr-2")[...],
        "Select user..."
    ],
    ComboboxContent()[
        ComboboxInput(placeholder="Search by name or email..."),
        [
            ComboboxItem(value=user["id"])[
                div(class_="flex items-center gap-2")[
                    Avatar()[AvatarImage(src=user["avatar"])],
                    div()[
                        div(class_="font-medium")[user["name"]],
                        div(class_="text-xs text-muted-foreground")[user["email"]]
                    ]
                ]
            ]
            for user in users
        ]
    ]
]
```

### Pattern 3: Multi-Select Tags

```python
from pynext import Signal

selected_tags = Signal([])

div(class_="flex flex-wrap gap-2")[
    [
        Badge(key=tag)[
            tag,
            Button(
                variant="ghost",
                size="icon",
                class_="h-4 w-4 ml-1",
                on_click=lambda t=tag: selected_tags.set([
                    s for s in selected_tags.value if s != t
                ])
            )["×"]
        ]
        for tag in selected_tags.value
    ],
    Combobox(
        on_value_change=lambda v: selected_tags.set([*selected_tags.value, v])
    )[
        ComboboxTrigger(class_="h-8")["+ Add tag"],
        ComboboxContent()[
            ComboboxInput(placeholder="Search tags..."),
            [
                ComboboxItem(value=tag)[tag]
                for tag in available_tags
                if tag not in selected_tags.value
            ]
        ]
    ]
]
```

---

## API Reference

### Combobox

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `value` | str | `""` | Selected value |
| `on_value_change` | callable | `None` | Called when selection changes |
| `allow_create` | bool | `False` | Allow creating new items |
| `on_create` | callable | `None` | Called when creating new item |

### ComboboxItem

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `value` | str | Required | Item's value |
| `disabled` | bool | `False` | Disable this item |

### ComboboxInput

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `placeholder` | str | `""` | Placeholder text |

---

## Accessibility

| Feature | Implementation |
|---------|----------------|
| **ARIA Roles** | `role="combobox"`, `role="listbox"`, `role="option"` |
| **Arrow Keys** | Up/Down to navigate options |
| **Enter** | Select focused option |
| **Escape** | Close dropdown |
| **Type-ahead** | Typing filters results |

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Search not filtering | Missing ComboboxInput | Add ComboboxInput to content |
| Items not showing | Empty data array | Check data source |
| Selection not persisting | Missing controlled state | Use Signal for value |
| Create not working | Missing allow_create | Add `allow_create=True` |

---

## Related Components

- **[Command](./command.md)** — Full command palette
- **[DropdownMenu](./dropdown-menu.md)** — Simple selection without search
- **[Input](./input.md)** — For free-form text input
