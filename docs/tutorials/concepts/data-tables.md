# Data Tables

> **Build sortable, filterable, paginated tables**

Learn how to create data tables that handle large datasets with sorting, filtering, and pagination.

---

## What You'll Learn

- Creating table components
- Implementing sorting
- Adding filters
- Pagination patterns
- Server-side vs client-side operations

---

## Basic Table Structure

```python
from pynext import div, table, thead, tbody, tr, th, td
from pynext.tw import tw, cn

def DataTable(data: list, columns: list):
    """
    Basic data table.
    
    Args:
        data: List of row dictionaries
        columns: List of {"key": "field", "label": "Header"}
    """
    return div(class_="rounded-md border")[
        table(class_="w-full")[
            thead(class_="bg-muted/50")[
                tr()[
                    [
                        th(class_="px-4 py-3 text-left text-sm font-medium")[
                            col["label"]
                        ]
                        for col in columns
                    ]
                ]
            ],
            tbody()[
                [
                    tr(class_="border-t hover:bg-muted/50")[
                        [
                            td(class_="px-4 py-3 text-sm")[
                                str(row.get(col["key"], ""))
                            ]
                            for col in columns
                        ]
                    ]
                    for row in data
                ]
            ],
        ],
    ]


# Usage
users = [
    {"id": 1, "name": "Jane", "email": "jane@example.com", "role": "Admin"},
    {"id": 2, "name": "John", "email": "john@example.com", "role": "User"},
]

columns = [
    {"key": "name", "label": "Name"},
    {"key": "email", "label": "Email"},
    {"key": "role", "label": "Role"},
]

DataTable(data=users, columns=columns)
```

---

## Adding Sorting

```python
from pynext import Signal

sort_key = Signal("name")
sort_dir = Signal("asc")  # "asc" or "desc"

def SortableHeader(column: dict):
    """Column header that toggles sorting."""
    is_active = sort_key.value == column["key"]
    
    def toggle_sort():
        if is_active:
            # Toggle direction
            sort_dir.set("desc" if sort_dir.value == "asc" else "asc")
        else:
            # New column, default to ascending
            sort_key.set(column["key"])
            sort_dir.set("asc")
    
    return th(
        class_="px-4 py-3 text-left text-sm font-medium cursor-pointer hover:bg-muted",
        onclick=toggle_sort,
    )[
        div(class_="flex items-center gap-2")[
            column["label"],
            is_active and span(class_="text-xs")[
                "↑" if sort_dir.value == "asc" else "↓"
            ],
        ],
    ]


def SortableTable(data: list, columns: list):
    """Table with sortable columns."""
    # Sort data
    key = sort_key.value
    reverse = sort_dir.value == "desc"
    sorted_data = sorted(data, key=lambda x: x.get(key, ""), reverse=reverse)
    
    return div(class_="rounded-md border")[
        table(class_="w-full")[
            thead(class_="bg-muted/50")[
                tr()[
                    [SortableHeader(col) for col in columns]
                ]
            ],
            tbody()[
                [
                    tr(class_="border-t hover:bg-muted/50")[
                        [
                            td(class_="px-4 py-3 text-sm")[
                                str(row.get(col["key"], ""))
                            ]
                            for col in columns
                        ]
                    ]
                    for row in sorted_data
                ]
            ],
        ],
    ]
```

---

## Adding Filters

```python
filter_text = Signal("")
filter_role = Signal("")

def TableFilters(roles: list):
    """Filter controls for the table."""
    return div(class_="flex gap-4 mb-4")[
        # Text search
        div(class_="flex-1")[
            Input(
                type="search",
                placeholder="Search by name or email...",
                value=filter_text.value,
                oninput=lambda e: filter_text.set(e.target.value),
            ),
        ],
        
        # Role filter
        select(
            class_="rounded-md border px-3 py-2",
            onchange=lambda e: filter_role.set(e.target.value),
        )[
            option(value="")["All Roles"],
            [option(value=role)[role] for role in roles],
        ],
    ]


def FilterableTable(data: list, columns: list):
    """Table with search and filter."""
    # Apply filters
    filtered = data
    
    # Text filter
    if filter_text.value:
        query = filter_text.value.lower()
        filtered = [
            row for row in filtered
            if query in row.get("name", "").lower()
            or query in row.get("email", "").lower()
        ]
    
    # Role filter
    if filter_role.value:
        filtered = [
            row for row in filtered
            if row.get("role") == filter_role.value
        ]
    
    roles = list(set(row.get("role") for row in data))
    
    return div()[
        TableFilters(roles),
        SortableTable(filtered, columns),
        div(class_="text-sm text-muted-foreground mt-2")[
            f"Showing {len(filtered)} of {len(data)} rows"
        ],
    ]
```

---

## Pagination

```python
page_size = 10
current_page = Signal(1)

def Pagination(total_items: int):
    """Pagination controls."""
    total_pages = (total_items + page_size - 1) // page_size
    page = current_page.value
    
    return div(class_="flex items-center justify-between mt-4")[
        # Info
        div(class_="text-sm text-muted-foreground")[
            f"Page {page} of {total_pages}"
        ],
        
        # Controls
        div(class_="flex gap-2")[
            Button(
                variant="outline",
                size="sm",
                disabled=page <= 1,
                onclick=lambda: current_page.set(1),
            )["«"],
            Button(
                variant="outline",
                size="sm",
                disabled=page <= 1,
                onclick=lambda: current_page.update(lambda p: p - 1),
            )["‹"],
            
            # Page numbers
            [
                Button(
                    variant="default" if p == page else "outline",
                    size="sm",
                    onclick=lambda p=p: current_page.set(p),
                )[str(p)]
                for p in range(
                    max(1, page - 2),
                    min(total_pages + 1, page + 3)
                )
            ],
            
            Button(
                variant="outline",
                size="sm",
                disabled=page >= total_pages,
                onclick=lambda: current_page.update(lambda p: p + 1),
            )["›"],
            Button(
                variant="outline",
                size="sm",
                disabled=page >= total_pages,
                onclick=lambda: current_page.set(total_pages),
            )["»"],
        ],
    ]


def PaginatedTable(data: list, columns: list):
    """Table with pagination."""
    # Calculate slice
    start = (current_page.value - 1) * page_size
    end = start + page_size
    page_data = data[start:end]
    
    return div()[
        DataTable(page_data, columns),
        Pagination(len(data)),
    ]
```

---

## Server-Side Operations

For large datasets, handle sorting/filtering/pagination on the server:

```python
from pynext import server_action

@server_action
async def fetch_users(
    page: int = 1,
    page_size: int = 10,
    sort_by: str = "name",
    sort_dir: str = "asc",
    search: str = "",
    role: str = "",
):
    """Fetch users with server-side operations."""
    # Build query
    query = "SELECT * FROM users WHERE 1=1"
    params = []
    
    if search:
        query += " AND (name LIKE ? OR email LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    
    if role:
        query += " AND role = ?"
        params.append(role)
    
    # Get total count
    count_query = query.replace("SELECT *", "SELECT COUNT(*)")
    total = db.execute(count_query, params).fetchone()[0]
    
    # Add sorting and pagination
    query += f" ORDER BY {sort_by} {sort_dir.upper()}"
    query += f" LIMIT {page_size} OFFSET {(page - 1) * page_size}"
    
    rows = db.execute(query, params).fetchall()
    
    return {
        "data": [dict(row) for row in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# Component that uses server-side data
def ServerTable():
    result = fetch_users(
        page=current_page.value,
        sort_by=sort_key.value,
        sort_dir=sort_dir.value,
        search=filter_text.value,
        role=filter_role.value,
    )
    
    return div()[
        TableFilters(),
        DataTable(result["data"], columns),
        Pagination(result["total"]),
    ]
```

---

## Row Selection

```python
selected_rows = Signal(set())

def SelectableRow(row: dict, columns: list):
    """Row with checkbox selection."""
    row_id = row["id"]
    is_selected = row_id in selected_rows.value
    
    def toggle():
        current = selected_rows.value.copy()
        if is_selected:
            current.discard(row_id)
        else:
            current.add(row_id)
        selected_rows.set(current)
    
    return tr(class_=cn(
        "border-t hover:bg-muted/50",
        is_selected and "bg-primary/10",
    ))[
        td(class_="px-4 py-3")[
            Checkbox(checked=is_selected, onchange=toggle),
        ],
        [
            td(class_="px-4 py-3 text-sm")[
                str(row.get(col["key"], ""))
            ]
            for col in columns
        ],
    ]


def SelectableTable(data: list, columns: list):
    """Table with row selection."""
    all_selected = len(selected_rows.value) == len(data)
    
    def toggle_all():
        if all_selected:
            selected_rows.set(set())
        else:
            selected_rows.set({row["id"] for row in data})
    
    return div()[
        # Bulk actions (shown when rows selected)
        selected_rows.value and div(class_="mb-4 p-2 bg-muted rounded flex items-center gap-4")[
            span()[f"{len(selected_rows.value)} selected"],
            Button(variant="outline", size="sm")["Delete Selected"],
            Button(variant="ghost", size="sm", onclick=lambda: selected_rows.set(set()))[
                "Clear"
            ],
        ],
        
        table(class_="w-full border rounded-md")[
            thead(class_="bg-muted/50")[
                tr()[
                    th(class_="px-4 py-3 w-10")[
                        Checkbox(checked=all_selected, onchange=toggle_all),
                    ],
                    [th(class_="px-4 py-3 text-left text-sm font-medium")[col["label"]] 
                     for col in columns],
                ],
            ],
            tbody()[
                [SelectableRow(row, columns) for row in data]
            ],
        ],
    ]
```

---

## Complete Example

```python
from pynext import page, Signal
from pynext.shadcn import Button, Input, Card

# State
sort_key = Signal("name")
sort_dir = Signal("asc")
filter_text = Signal("")
current_page = Signal(1)
page_size = 5

# Sample data
users = [
    {"id": i, "name": f"User {i}", "email": f"user{i}@example.com", "role": "User" if i % 3 else "Admin"}
    for i in range(1, 51)
]

columns = [
    {"key": "name", "label": "Name", "sortable": True},
    {"key": "email", "label": "Email", "sortable": True},
    {"key": "role", "label": "Role", "sortable": True},
]


@page(title="Users")
def users_page():
    # Filter
    filtered = users
    if filter_text.value:
        q = filter_text.value.lower()
        filtered = [u for u in filtered if q in u["name"].lower() or q in u["email"].lower()]
    
    # Sort
    filtered = sorted(
        filtered,
        key=lambda x: x.get(sort_key.value, ""),
        reverse=sort_dir.value == "desc"
    )
    
    # Paginate
    total = len(filtered)
    start = (current_page.value - 1) * page_size
    page_data = filtered[start:start + page_size]
    
    return div(class_="p-8 max-w-4xl mx-auto")[
        h1(class_="text-2xl font-bold mb-6")["Users"],
        
        Card()[
            div(class_="p-4 border-b")[
                Input(
                    type="search",
                    placeholder="Search users...",
                    value=filter_text.value,
                    oninput=lambda e: filter_text.set(e.target.value),
                    class_="max-w-sm",
                ),
            ],
            
            # Table
            DataTable(page_data, columns),
            
            # Pagination
            div(class_="p-4 border-t")[
                Pagination(total),
            ],
        ],
    ]
```

---

## Key Takeaways

1. **Start simple** — Basic table, then add features
2. **Use Signals** — For reactive sorting/filtering/pagination
3. **Server-side for large data** — Don't load 10,000 rows client-side
4. **Accessible tables** — Use proper `th`, `scope`, `role` attributes
5. **Loading states** — Show skeleton while fetching

---

## Related Tutorials

- [State Management](./state-management.md) - Reactive table state
- [Forms & Validation](./forms-and-validation.md) - Inline editing

