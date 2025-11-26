# DataTable

A powerful data table with sorting, filtering, pagination, row selection, column visibility, and column resize.

## Installation

```python
from pynext.shadcn import (
    DataTable, DataTableColumn, DataTableToolbar,
    DataTableFacetedFilter, DataTablePagination, DataTableColumnToggle
)
```

## Basic Usage

```python
# Define columns
columns = [
    DataTableColumn(accessor="name", header="Name", sortable=True),
    DataTableColumn(accessor="email", header="Email"),
    DataTableColumn(accessor="status", header="Status"),
]

# Render table
DataTable(
    data=users,
    columns=columns
)
```

## Examples

### With Custom Cell Rendering

```python
columns = [
    DataTableColumn(
        accessor="avatar",
        header="",
        cell=lambda row: Avatar()[
            AvatarImage(src=row["avatar"]),
            AvatarFallback()[row["name"][0]]
        ],
        width="50px"
    ),
    DataTableColumn(
        accessor="name",
        header="Name",
        cell=lambda row: div()[
            p(class_="font-medium")[row["name"]],
            p(class_="text-sm text-muted-foreground")[row["email"]]
        ]
    ),
    DataTableColumn(
        accessor="status",
        header="Status",
        cell=lambda row: Badge(
            variant="success" if row["status"] == "active" else "secondary"
        )[row["status"]]
    ),
]
```

### With Sorting

```python
columns = [
    DataTableColumn(accessor="name", header="Name", sortable=True),
    DataTableColumn(accessor="date", header="Date", sortable=True),
    DataTableColumn(accessor="amount", header="Amount", sortable=True),
]

DataTable(
    data=data,
    columns=columns,
    sort_column="date",
    sort_direction="desc",
    on_sort=handle_sort
)
```

### With Pagination

```python
DataTable(
    data=page_data,
    columns=columns,
    pagination=True,
    page=current_page,
    page_size=20,
    total_rows=total_count
)
```

### With Row Selection

```python
DataTable(
    data=data,
    columns=columns,
    row_selection=True,
    selected_rows=selected,
    on_row_select=handle_selection
)
```

### With Toolbar and Filters

```python
div()[
    DataTableToolbar()[
        Input(placeholder="Filter by name..."),
        DataTableFacetedFilter(
            column="status",
            title="Status",
            options=["Active", "Inactive", "Pending"]
        ),
    ],
    DataTable(
        data=filtered_data,
        columns=columns
    )
]
```

### Server-Side Data Loading

```python
@server_action
async def load_users(page: int, sort: str, direction: str, filters: dict):
    return await db.query_users(
        offset=(page - 1) * 20,
        limit=20,
        order_by=sort,
        order_dir=direction,
        **filters
    )

# In component
DataTable(
    data=users,
    columns=columns,
    pagination=True,
    page=page,
    total_pages=total_pages,
    sort_column=sort_col,
    sort_direction=sort_dir,
    on_sort=lambda col, dir: load_users(page, col, dir, filters),
    on_page_change=lambda p: load_users(p, sort_col, sort_dir, filters)
)
```

### Column Visibility Toggle

Let users show/hide columns with the `DataTableColumnToggle` component:

```python
# Track visibility state
column_visibility = {"email": True, "phone": False, "address": True}

div()[
    DataTableToolbar()[
        Input(placeholder="Search..."),
        DataTableColumnToggle(
            columns=columns,
            visibility=column_visibility,
            on_visibility_change=set_visibility,
        ),
    ],
    DataTable(
        data=users,
        columns=columns,
        column_visibility=column_visibility,  # Pass visibility state
    )
]
```

The toggle renders a dropdown showing all columns with checkboxes:

```
┌─────────────────────┐
│ ☐ Columns           │
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│ ✓ Name              │
│ ✓ Email             │
│   Phone (hidden)    │
│ ✓ Status            │
└─────────────────────┘
```

### Column Resizing

Enable column resizing by dragging column borders:

```python
# Enable for all columns
DataTable(
    data=users,
    columns=columns,
    resizable=True,  # Enable resize for all columns
)

# Or enable per-column with min/max constraints
columns = [
    DataTableColumn(
        accessor="name",
        header="Name",
        resizable=True,
        min_width="100px",
        max_width="300px",
    ),
    DataTableColumn(
        accessor="description",
        header="Description",
        resizable=True,
        min_width="150px",
        max_width="500px",
    ),
]
```

**How it works:**

```
┌─────────┬───────────────────┬──────────┐
│ Name  │▎│ Description      │▎│ Status │
├─────────┼───────────────────┼──────────┤
       ↑
  Drag here to resize
```

- Drag the resize handle between columns
- Respects `min_width` and `max_width` constraints
- Works on both desktop (mouse) and mobile (touch)
- Dispatches `pynext:column-resize` event with new width

## API Reference

### DataTableColumn

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `accessor` | `str` | required | Data key |
| `header` | `str \| Callable` | `""` | Header content |
| `cell` | `Callable` | `None` | Cell render function |
| `footer` | `Callable` | `None` | Footer render function |
| `sortable` | `bool` | `False` | Enable sorting |
| `filterable` | `bool` | `False` | Enable filtering |
| `filter_options` | `list[str]` | `None` | Options for faceted filter |
| `hidden` | `bool` | `False` | Hide column by default |
| `resizable` | `bool` | `False` | Enable column resizing |
| `min_width` | `str` | `"50px"` | Minimum width when resizing |
| `max_width` | `str` | `"500px"` | Maximum width when resizing |
| `width` | `str` | `None` | Initial column width |

### DataTable

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `data` | `list[dict]` | required | Row data |
| `columns` | `list[Column]` | required | Column definitions |
| `pagination` | `bool` | `False` | Enable pagination |
| `page_size` | `int` | `10` | Rows per page |
| `page` | `int` | `1` | Current page |
| `row_selection` | `bool` | `False` | Enable selection |
| `sort_column` | `str` | `None` | Sorted column |
| `sort_direction` | `str` | `"asc"` | Sort direction |
| `column_visibility` | `dict[str, bool]` | `{}` | Accessor -> visible mapping |
| `resizable` | `bool` | `False` | Enable resize for all columns |
| `loading` | `bool` | `False` | Show loading state |
| `empty_message` | `str` | `"No results."` | Empty state text |

### DataTableColumnToggle

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `columns` | `list[Column]` | required | Column definitions |
| `visibility` | `dict[str, bool]` | `{}` | Current visibility state |
| `on_visibility_change` | `Callable` | `None` | Callback when visibility changes |

### DataTableFacetedFilter

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `column` | `str` | required | Column to filter |
| `title` | `str` | required | Filter title |
| `options` | `list[str]` | required | Filter options |
| `selected` | `list[str]` | `[]` | Selected filters |

## Events

```python
# Sort change
on_sort=lambda column, direction: ...

# Page change
on_page_change=lambda page: ...

# Row selection
on_row_select=lambda selected_rows: ...

# Column visibility change (from DataTableColumnToggle)
on_visibility_change=lambda visibility_dict: ...

# Column resize (JavaScript event)
# table.addEventListener('pynext:column-resize', (e) => {
#     accessor = e.detail.accessor  # Column accessor
#     width = e.detail.width        # New width (e.g., "250px")
# })
```

