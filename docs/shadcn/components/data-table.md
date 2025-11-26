# DataTable

> **Like a supercharged spreadsheet — sortable, filterable, paginated**

A feature-rich data table for displaying and managing large datasets with sorting, filtering, pagination, row selection, column visibility, and column resizing.

---

## First Principles: What IS a DataTable?

### The Core Concept

A DataTable transforms **raw data** into **actionable information**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        THE DATA → TABLE TRANSFORMATION                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Raw Data (Unmanageable):              DataTable (Organized):                │
│  ─────────────────────────             ───────────────────────               │
│                                                                              │
│  [                                     ┌────────┬──────────┬───────┐        │
│    {"id":1,"name":"Alice",             │ Name   │ Email    │ Role  │        │
│     "email":"alice@..."},              ├────────┼──────────┼───────┤        │
│    {"id":2,"name":"Bob",       ──▶     │ Alice  │ alice@.. │ Admin │        │
│     "email":"bob@..."},                │ Bob    │ bob@..   │ User  │        │
│    {"id":3,"name":"Carol",             │ Carol  │ carol@.. │ User  │        │
│     "email":"carol@..."},              └────────┴──────────┴───────┘        │
│    ... 1000 more                              Page 1 of 100                  │
│  ]                                            Sort: Name A→Z                │
│                                               Filter: Active only            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Why DataTables Are Complex

A DataTable must handle **many concerns simultaneously**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DATATABLE RESPONSIBILITIES                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  DATA DISPLAY                    INTERACTIVITY                               │
│  ────────────                    ─────────────                               │
│  • Columns and rows              • Click header to sort                      │
│  • Cell formatting               • Type to filter                            │
│  • Responsive layout             • Check to select                           │
│  • Empty states                  • Drag to resize columns                    │
│                                                                              │
│  STATE MANAGEMENT                ACCESSIBILITY                               │
│  ────────────────                ─────────────                               │
│  • Current sort column           • Keyboard navigation                       │
│  • Sort direction                • Screen reader announcements               │
│  • Current page                  • Focus management                          │
│  • Selected rows                 • ARIA attributes                           │
│  • Column visibility                                                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Installation

```bash
pynext ui add data-table
```

Or import directly:

```python
from pynext.shadcn import (
    DataTable, DataTableColumn, DataTablePagination,
    DataTableColumnToggle
)
```

---

## Step-by-Step Usage

### Step 1: Basic Table

Define columns and pass data:

```python
from pynext.shadcn import DataTable, DataTableColumn

# Your data
users = [
    {"id": 1, "name": "Alice", "email": "alice@example.com"},
    {"id": 2, "name": "Bob", "email": "bob@example.com"},
    {"id": 3, "name": "Carol", "email": "carol@example.com"},
]

# Define columns
columns = [
    DataTableColumn(key="name", header="Name"),
    DataTableColumn(key="email", header="Email"),
]

# Render table
DataTable(data=users, columns=columns)
```

**What happens:**
- `DataTable` creates a `<table>` with proper structure
- Each column becomes a `<th>` header and maps to `<td>` cells
- Data is rendered row by row

### Step 2: Add Sorting

Make columns clickable to sort:

```python
columns = [
    DataTableColumn(
        key="name", 
        header="Name", 
        sortable=True  # ← Click header to sort
    ),
    DataTableColumn(
        key="created_at", 
        header="Created", 
        sortable=True,
        sort_fn=lambda a, b: a.timestamp() - b.timestamp()  # Custom sort
    ),
]

DataTable(
    data=users, 
    columns=columns,
    default_sort="name",      # Initial sort column
    default_sort_dir="asc",   # Initial direction
)
```

### Step 3: Add Filtering

Enable global search:

```python
DataTable(
    data=users,
    columns=columns,
    filterable=True,           # Show filter input
    filter_placeholder="Search users...",
)
```

Or column-specific filters:

```python
columns = [
    DataTableColumn(
        key="status",
        header="Status",
        filter_type="select",  # Dropdown filter
        filter_options=["Active", "Inactive", "Pending"]
    ),
]
```

### Step 4: Add Pagination

For large datasets:

```python
DataTable(
    data=all_users,            # Can be 10,000 items
    columns=columns,
    page_size=10,              # Show 10 per page
    page_sizes=[10, 25, 50],   # Allow user to change
)
```

### Step 5: Add Row Selection

Select rows for bulk actions:

```python
from pynext import Signal

selected_rows = Signal([])

DataTable(
    data=users,
    columns=columns,
    selectable=True,
    selected=selected_rows.value,
    on_select=selected_rows.set,
)

# Bulk action button
Button(
    disabled=len(selected_rows.value) == 0,
    on_click=lambda: delete_users(selected_rows.value)
)[
    f"Delete {len(selected_rows.value)} users"
]
```

### Step 6: Column Visibility & Resize

Let users customize the view:

```python
DataTable(
    data=users,
    columns=columns,
    column_visibility=True,  # Toggle button to show/hide columns
    resizable=True,          # Drag column borders to resize
)
```

---

## Complete Example

```python
from pynext.shadcn import (
    DataTable, DataTableColumn, Button, Input,
    DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem
)
from pynext import Signal, server_action

# State
selected = Signal([])
search = Signal("")

# Columns
columns = [
    DataTableColumn(
        key="name",
        header="Name",
        sortable=True,
    ),
    DataTableColumn(
        key="email",
        header="Email",
        sortable=True,
    ),
    DataTableColumn(
        key="role",
        header="Role",
        filter_type="select",
        filter_options=["Admin", "Editor", "Viewer"],
    ),
    DataTableColumn(
        key="actions",
        header="",
        cell=lambda row: DropdownMenu()[
            DropdownMenuTrigger()[Button(variant="ghost")["⋯"]],
            DropdownMenuContent()[
                DropdownMenuItem(on_click=lambda: edit(row["id"]))["Edit"],
                DropdownMenuItem(on_click=lambda: delete(row["id"]))["Delete"],
            ]
        ]
    ),
]

# Table
div(class_="space-y-4")[
    # Toolbar
    div(class_="flex items-center justify-between")[
        Input(
            placeholder="Search...",
            value=search.value,
            on_change=lambda e: search.set(e.target.value),
            class_="max-w-sm"
        ),
        div(class_="flex gap-2")[
            DataTableColumnToggle(columns=columns),
            Button()["Export"],
        ]
    ],
    
    # Table
    DataTable(
        data=users,
        columns=columns,
        selectable=True,
        selected=selected.value,
        on_select=selected.set,
        page_size=10,
        resizable=True,
    ),
    
    # Bulk actions
    div(class_="flex items-center gap-2")[
        span()[f"{len(selected.value)} selected"],
        Button(
            variant="destructive",
            disabled=len(selected.value) == 0
        )["Delete Selected"],
    ]
]
```

---

## Column Configuration

### DataTableColumn Props

| Prop | Type | Description |
|------|------|-------------|
| `key` | str | Data field key |
| `header` | str | Column header text |
| `sortable` | bool | Enable sorting |
| `sort_fn` | callable | Custom sort function |
| `filter_type` | str | `"text"`, `"select"`, `"date"` |
| `filter_options` | list | Options for select filter |
| `cell` | callable | Custom cell renderer |
| `min_width` | int | Minimum column width (px) |
| `max_width` | int | Maximum column width (px) |
| `hidden` | bool | Initially hidden |

### Custom Cell Rendering

```python
DataTableColumn(
    key="status",
    header="Status",
    cell=lambda row: Badge(
        variant="success" if row["status"] == "Active" else "secondary"
    )[row["status"]]
)
```

### Formatted Values

```python
DataTableColumn(
    key="created_at",
    header="Created",
    cell=lambda row: row["created_at"].strftime("%b %d, %Y")
)

DataTableColumn(
    key="amount",
    header="Amount",
    cell=lambda row: f"${row['amount']:,.2f}"
)
```

---

## API Reference

### DataTable

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `data` | list | `[]` | Array of row objects |
| `columns` | list | `[]` | Column configurations |
| `selectable` | bool | `False` | Enable row selection |
| `selected` | list | `[]` | Selected row IDs |
| `on_select` | callable | `None` | Selection change handler |
| `filterable` | bool | `False` | Show global filter |
| `page_size` | int | `10` | Rows per page |
| `page_sizes` | list | `[10, 25, 50]` | Available page sizes |
| `default_sort` | str | `None` | Initial sort column |
| `default_sort_dir` | str | `"asc"` | Initial sort direction |
| `column_visibility` | bool | `False` | Enable column toggle |
| `resizable` | bool | `False` | Enable column resize |

---

## Accessibility

| Feature | Implementation |
|---------|----------------|
| **Sortable headers** | `aria-sort="ascending/descending"` |
| **Selectable rows** | Checkbox with `aria-label` |
| **Pagination** | Announced via `aria-live` |
| **Column resize** | Keyboard-accessible handles |
| **Focus management** | Tab through headers and cells |

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Sort not working | `sortable=False` | Add `sortable=True` to column |
| No pagination | Small dataset | Add more data or lower `page_size` |
| Selection lost | Component re-render | Use Signal for `selected` |
| Columns not resizing | `resizable=False` | Add `resizable=True` to DataTable |

---

## Related Components

- **[Button](./button.md)** — For table actions
- **[Badge](./badge.md)** — For status cells
- **[DropdownMenu](./dropdown-menu.md)** — For row actions
- **[Input](./input.md)** — For filter input
