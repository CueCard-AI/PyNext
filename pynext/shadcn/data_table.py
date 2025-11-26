"""
DataTable Component

A powerful data table with sorting, filtering, pagination, and row selection.
Designed to work with server actions for efficient data loading.

Usage:
    from pynext.shadcn import (
        DataTable, DataTableColumn, DataTablePagination,
        DataTableToolbar, DataTableFacetedFilter
    )
    
    # Define columns
    columns = [
        DataTableColumn(
            accessor="name",
            header="Name",
            sortable=True,
        ),
        DataTableColumn(
            accessor="email",
            header="Email",
            cell=lambda row: a(href=f"mailto:{row['email']}")[row['email']]
        ),
        DataTableColumn(
            accessor="status",
            header="Status",
            filterable=True,
            filter_options=["Active", "Inactive", "Pending"]
        ),
    ]
    
    # Render table
    DataTable(
        data=users,
        columns=columns,
        pagination=True,
        row_selection=True,
        on_row_select=handle_selection,
    )
"""

from typing import Any, Optional, List, Union, Callable, Dict, Literal
from pynext.tw import cn
import hashlib


# Table container styles
TABLE_CONTAINER_BASE = "w-full overflow-auto"
TABLE_BASE = "w-full caption-bottom text-sm"

# Table parts
TABLE_HEADER_BASE = "[&_tr]:border-b"
TABLE_BODY_BASE = "[&_tr:last-child]:border-0"
TABLE_FOOTER_BASE = "border-t bg-muted/50 font-medium [&>tr]:last:border-b-0"
TABLE_ROW_BASE = (
    "border-b transition-colors hover:bg-muted/50 "
    "data-[state=selected]:bg-muted"
)
TABLE_HEAD_BASE = (
    "h-12 px-4 text-left align-middle font-medium text-muted-foreground "
    "[&:has([role=checkbox])]:pr-0"
)
TABLE_CELL_BASE = "p-4 align-middle [&:has([role=checkbox])]:pr-0"
TABLE_CAPTION_BASE = "mt-4 text-sm text-muted-foreground"

# Pagination styles
PAGINATION_BASE = "flex items-center justify-between px-2 py-4"
PAGINATION_INFO_BASE = "text-sm text-muted-foreground"
PAGINATION_BUTTONS_BASE = "flex items-center space-x-2"
PAGINATION_BUTTON_BASE = (
    "inline-flex items-center justify-center rounded-md text-sm font-medium "
    "ring-offset-background transition-colors focus-visible:outline-none "
    "focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 "
    "disabled:pointer-events-none disabled:opacity-50 "
    "border border-input bg-background hover:bg-accent hover:text-accent-foreground "
    "h-8 w-8"
)

# Toolbar styles
TOOLBAR_BASE = "flex items-center justify-between py-4"
TOOLBAR_FILTERS_BASE = "flex flex-1 items-center space-x-2"

# Sort indicator
SORT_INDICATOR_ASC = "↑"
SORT_INDICATOR_DESC = "↓"


class DataTableColumn:
    """
    Column definition for DataTable.
    
    Attributes:
        accessor: Key to access data from row object
        header: Column header text or render function
        cell: Optional cell render function
        footer: Optional footer render function
        sortable: Whether column is sortable
        filterable: Whether column is filterable
        filter_options: Options for faceted filter
        hidden: Whether column is hidden by default
        resizable: Whether column can be resized by dragging
        min_width: Minimum width when resizing (e.g., "100px")
        max_width: Maximum width when resizing (e.g., "400px")
        class_: Additional CSS classes for cells
    
    Example:
        DataTableColumn(
            accessor="email",
            header="Email",
            cell=lambda row: a(href=f"mailto:{row['email']}")[row['email']],
            sortable=True,
            resizable=True,
            min_width="150px",
        )
    """
    
    def __init__(
        self,
        accessor: str,
        header: Union[str, Callable] = "",
        cell: Optional[Callable[[dict], Any]] = None,
        footer: Optional[Callable[[], Any]] = None,
        sortable: bool = False,
        filterable: bool = False,
        filter_options: Optional[List[str]] = None,
        hidden: bool = False,
        resizable: bool = False,
        min_width: Optional[str] = None,
        max_width: Optional[str] = None,
        class_: Optional[str] = None,
        width: Optional[str] = None,
    ):
        self.accessor = accessor
        self.header = header
        self.cell = cell
        self.footer = footer
        self.sortable = sortable
        self.filterable = filterable
        self.filter_options = filter_options
        self.hidden = hidden
        self.resizable = resizable
        self.min_width = min_width
        self.max_width = max_width
        self.extra_class = class_
        self.width = width


class DataTable:
    """
    A feature-rich data table component.
    
    Attributes:
        data: List of row objects
        columns: List of DataTableColumn definitions
        pagination: Enable pagination
        page_size: Number of rows per page (default 10)
        page: Current page (1-indexed)
        total_pages: Total number of pages (for server-side)
        row_selection: Enable row selection
        selected_rows: Currently selected row indices
        on_row_select: Callback when selection changes
        sort_column: Currently sorted column accessor
        sort_direction: "asc" or "desc"
        on_sort: Callback when sort changes
        column_visibility: Dict mapping accessor to visibility (True/False)
        resizable: Enable column resizing for all columns
        loading: Whether data is loading
        empty_message: Message when no data
        caption: Optional table caption
        class_: Additional CSS classes
    
    Example:
        DataTable(
            data=users,
            columns=columns,
            pagination=True,
            page_size=20,
            row_selection=True,
            column_visibility={"email": False},  # Hide email column
            resizable=True,  # Enable column resizing
        )
    """
    
    def __init__(
        self,
        data: List[dict],
        columns: List[DataTableColumn],
        pagination: bool = False,
        page_size: int = 10,
        page: int = 1,
        total_pages: Optional[int] = None,
        total_rows: Optional[int] = None,
        row_selection: bool = False,
        selected_rows: Optional[List[int]] = None,
        on_row_select: Optional[Callable[[List[int]], None]] = None,
        sort_column: Optional[str] = None,
        sort_direction: Literal["asc", "desc"] = "asc",
        on_sort: Optional[Callable[[str, str], None]] = None,
        column_visibility: Optional[Dict[str, bool]] = None,
        resizable: bool = False,
        loading: bool = False,
        empty_message: str = "No results.",
        caption: Optional[str] = None,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.data = data or []
        self.columns = columns
        self.pagination = pagination
        self.page_size = page_size
        self.page = page
        self.total_pages = total_pages
        self.total_rows = total_rows or len(self.data)
        self.row_selection = row_selection
        self.selected_rows = selected_rows or []
        self.on_row_select = on_row_select
        self.sort_column = sort_column
        self.sort_direction = sort_direction
        self.on_sort = on_sort
        self.column_visibility = column_visibility or {}
        self.resizable = resizable
        self.loading = loading
        self.empty_message = empty_message
        self.caption = caption
        self.extra_class = class_
        self.attrs = attrs
    
    def render(self) -> str:
        table_id = hashlib.md5(str(id(self)).encode()).hexdigest()[:8]
        
        # Filter visible columns (check both hidden property and column_visibility dict)
        visible_columns = [
            c for c in self.columns 
            if not c.hidden and self.column_visibility.get(c.accessor, True)
        ]
        
        # Build parts
        header = self._render_header(visible_columns)
        body = self._render_body(visible_columns)
        footer = self._render_footer(visible_columns) if any(c.footer for c in visible_columns) else ""
        caption_html = f'<caption class="{cn(TABLE_CAPTION_BASE)}">{self.caption}</caption>' if self.caption else ""
        pagination_html = self._render_pagination() if self.pagination else ""
        
        container_class = cn(TABLE_CONTAINER_BASE, self.extra_class)
        table_class = cn(TABLE_BASE)
        
        # Loading overlay
        loading_overlay = ""
        if self.loading:
            loading_overlay = '''
<div class="absolute inset-0 bg-background/50 flex items-center justify-center">
    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
</div>
'''
        
        resizable_attr = 'data-resizable="true"' if self.resizable else ""
        
        return f'''
<div data-pynext-datatable="{table_id}"
     data-page="{self.page}"
     data-page-size="{self.page_size}"
     data-sort-column="{self.sort_column or ''}"
     data-sort-direction="{self.sort_direction}"
     {resizable_attr}
     class="relative">
    {loading_overlay}
    <div class="{container_class}">
        <table class="{table_class}">
            {caption_html}
            {header}
            {body}
            {footer}
        </table>
    </div>
    {pagination_html}
</div>
'''
    
    def _render_header(self, columns: List[DataTableColumn]) -> str:
        cells = []
        
        # Row selection checkbox column
        if self.row_selection:
            all_selected = len(self.selected_rows) == len(self.data) and len(self.data) > 0
            cells.append(f'''
<th class="{cn(TABLE_HEAD_BASE, 'w-[40px]')}">
    <input type="checkbox" 
           data-pynext-datatable-select-all
           {"checked" if all_selected else ""}
           class="h-4 w-4 rounded border-gray-300" />
</th>
''')
        
        # Data columns
        for col in columns:
            header_content = col.header if isinstance(col.header, str) else col.header()
            
            # Sort indicator
            sort_indicator = ""
            if col.sortable:
                if col.accessor == self.sort_column:
                    indicator = SORT_INDICATOR_ASC if self.sort_direction == "asc" else SORT_INDICATOR_DESC
                    sort_indicator = f'<span class="ml-2">{indicator}</span>'
                
                header_content = f'''
<button class="flex items-center hover:text-foreground" 
        data-pynext-datatable-sort="{col.accessor}">
    {header_content}
    {sort_indicator}
</button>
'''
            
            # Width and resize attributes
            width_style = f' style="width:{col.width}"' if col.width else ""
            is_resizable = self.resizable or col.resizable
            resize_attrs = ""
            if is_resizable:
                min_w = col.min_width or "50px"
                max_w = col.max_width or "500px"
                resize_attrs = f' data-resizable-col="{col.accessor}" data-min-width="{min_w}" data-max-width="{max_w}"'
            
            # Resize handle
            resize_handle = ""
            if is_resizable:
                resize_handle = '''
<div data-pynext-resize-handle
     class="absolute right-0 top-0 h-full w-1 cursor-col-resize 
            hover:bg-primary/50 active:bg-primary"
     style="touch-action: none;">
</div>
'''
            
            th_class = cn(TABLE_HEAD_BASE, col.extra_class)
            position_style = " position:relative;" if is_resizable else ""
            cells.append(f'<th class="{th_class}"{width_style}{resize_attrs} style="{position_style}">{header_content}{resize_handle}</th>')
        
        return f'''
<thead class="{cn(TABLE_HEADER_BASE)}">
    <tr class="{cn(TABLE_ROW_BASE)}">
        {"".join(cells)}
    </tr>
</thead>
'''
    
    def _render_body(self, columns: List[DataTableColumn]) -> str:
        if not self.data:
            col_count = len(columns) + (1 if self.row_selection else 0)
            return f'''
<tbody class="{cn(TABLE_BODY_BASE)}">
    <tr>
        <td colspan="{col_count}" class="h-24 text-center text-muted-foreground">
            {self.empty_message}
        </td>
    </tr>
</tbody>
'''
        
        rows = []
        for idx, row in enumerate(self.data):
            is_selected = idx in self.selected_rows
            selected_attr = 'data-state="selected"' if is_selected else ""
            
            cells = []
            
            # Row selection checkbox
            if self.row_selection:
                cells.append(f'''
<td class="{cn(TABLE_CELL_BASE, 'w-[40px]')}">
    <input type="checkbox"
           data-pynext-datatable-select-row="{idx}"
           {"checked" if is_selected else ""}
           class="h-4 w-4 rounded border-gray-300" />
</td>
''')
            
            # Data cells
            for col in columns:
                if col.cell:
                    cell_content = col.cell(row)
                    if hasattr(cell_content, 'render'):
                        cell_content = cell_content.render()
                else:
                    cell_content = row.get(col.accessor, "")
                
                cells.append(f'<td class="{cn(TABLE_CELL_BASE, col.extra_class)}">{cell_content}</td>')
            
            rows.append(f'''
<tr class="{cn(TABLE_ROW_BASE)}" {selected_attr} data-row-index="{idx}">
    {"".join(cells)}
</tr>
''')
        
        return f'''
<tbody class="{cn(TABLE_BODY_BASE)}">
    {"".join(rows)}
</tbody>
'''
    
    def _render_footer(self, columns: List[DataTableColumn]) -> str:
        cells = []
        
        if self.row_selection:
            cells.append(f'<td class="{cn(TABLE_CELL_BASE)}"></td>')
        
        for col in columns:
            footer_content = col.footer() if col.footer else ""
            if hasattr(footer_content, 'render'):
                footer_content = footer_content.render()
            cells.append(f'<td class="{cn(TABLE_CELL_BASE)}">{footer_content}</td>')
        
        return f'''
<tfoot class="{cn(TABLE_FOOTER_BASE)}">
    <tr>
        {"".join(cells)}
    </tr>
</tfoot>
'''
    
    def _render_pagination(self) -> str:
        total_pages = self.total_pages or max(1, (self.total_rows + self.page_size - 1) // self.page_size)
        start_row = (self.page - 1) * self.page_size + 1
        end_row = min(self.page * self.page_size, self.total_rows)
        
        # Selection info
        selection_info = ""
        if self.row_selection:
            selection_info = f'''
<div class="{cn(PAGINATION_INFO_BASE)}">
    {len(self.selected_rows)} of {self.total_rows} row(s) selected.
</div>
'''
        else:
            selection_info = f'''
<div class="{cn(PAGINATION_INFO_BASE)}">
    Showing {start_row} to {end_row} of {self.total_rows} rows.
</div>
'''
        
        # Navigation buttons
        is_first = self.page <= 1
        is_last = self.page >= total_pages
        
        return f'''
<div class="{cn(PAGINATION_BASE)}" data-pynext-datatable-pagination>
    {selection_info}
    <div class="{cn(PAGINATION_BUTTONS_BASE)}">
        <button class="{cn(PAGINATION_BUTTON_BASE)}"
                data-pynext-datatable-first
                {"disabled" if is_first else ""}
                aria-label="First page">
            <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7"/>
            </svg>
        </button>
        <button class="{cn(PAGINATION_BUTTON_BASE)}"
                data-pynext-datatable-prev
                {"disabled" if is_first else ""}
                aria-label="Previous page">
            <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
            </svg>
        </button>
        <span class="text-sm">
            Page {self.page} of {total_pages}
        </span>
        <button class="{cn(PAGINATION_BUTTON_BASE)}"
                data-pynext-datatable-next
                {"disabled" if is_last else ""}
                aria-label="Next page">
            <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
            </svg>
        </button>
        <button class="{cn(PAGINATION_BUTTON_BASE)}"
                data-pynext-datatable-last
                {"disabled" if is_last else ""}
                aria-label="Last page">
            <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7-7 7M5 5l7 7-7 7"/>
            </svg>
        </button>
    </div>
</div>
'''
    
    def __str__(self) -> str:
        return self.render()


class DataTableToolbar:
    """
    Toolbar with search and filters for DataTable.
    
    Example:
        DataTableToolbar()[
            Input(placeholder="Filter emails..."),
            DataTableFacetedFilter(column="status", options=["Active", "Inactive"]),
        ]
    """
    
    def __init__(self, class_: Optional[str] = None, **attrs: Any):
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "DataTableToolbar":
        if isinstance(children, tuple):
            self._children = list(children)
        else:
            self._children = [children]
        return self
    
    def render(self) -> str:
        children_html = "".join(
            child.render() if hasattr(child, 'render') else str(child)
            for child in self._children
        )
        
        class_str = cn(TOOLBAR_BASE, self.extra_class)
        
        return f'''
<div data-pynext-datatable-toolbar class="{class_str}">
    <div class="{cn(TOOLBAR_FILTERS_BASE)}">
        {children_html}
    </div>
</div>
'''
    
    def __str__(self) -> str:
        return self.render()


class DataTableFacetedFilter:
    """
    A faceted filter dropdown for DataTable columns.
    
    Attributes:
        column: Column accessor to filter
        title: Filter button title
        options: List of filter options
        selected: Currently selected options
        on_change: Callback when selection changes
    
    Example:
        DataTableFacetedFilter(
            column="status",
            title="Status",
            options=["Active", "Inactive", "Pending"]
        )
    """
    
    def __init__(
        self,
        column: str,
        title: str,
        options: List[str],
        selected: Optional[List[str]] = None,
        on_change: Optional[Callable[[List[str]], None]] = None,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.column = column
        self.title = title
        self.options = options
        self.selected = selected or []
        self.on_change = on_change
        self.extra_class = class_
        self.attrs = attrs
    
    def render(self) -> str:
        filter_id = hashlib.md5(f"{self.column}_{self.title}".encode()).hexdigest()[:8]
        
        selected_count = len(self.selected)
        badge = f'<span class="ml-2 rounded-full bg-primary px-2 py-0.5 text-xs text-primary-foreground">{selected_count}</span>' if selected_count else ""
        
        option_items = []
        for opt in self.options:
            is_selected = opt in self.selected
            option_items.append(f'''
<label class="flex items-center space-x-2 px-2 py-1.5 hover:bg-accent rounded cursor-pointer">
    <input type="checkbox"
           data-pynext-filter-option="{opt}"
           {"checked" if is_selected else ""}
           class="h-4 w-4 rounded border-gray-300" />
    <span class="text-sm">{opt}</span>
</label>
''')
        
        return f'''
<div data-pynext-faceted-filter="{filter_id}"
     data-column="{self.column}"
     class="relative {self.extra_class or ''}">
    <button type="button"
            data-pynext-filter-trigger
            class="inline-flex items-center justify-center rounded-md border border-dashed border-input px-3 py-2 text-sm hover:bg-accent">
        <svg class="mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
        </svg>
        {self.title}
        {badge}
    </button>
    <div data-pynext-filter-content
         class="absolute top-full left-0 mt-2 w-[200px] rounded-md border bg-popover p-2 shadow-md z-50"
         style="display:none">
        <div class="space-y-1">
            {"".join(option_items)}
        </div>
        <div class="mt-2 border-t pt-2 flex justify-end">
            <button type="button"
                    data-pynext-filter-clear
                    class="text-xs text-muted-foreground hover:text-foreground">
                Clear filters
            </button>
        </div>
    </div>
</div>
'''
    
    def __str__(self) -> str:
        return self.render()


class DataTablePagination:
    """
    Standalone pagination component for DataTable.
    
    Use when you need pagination outside the table component.
    """
    
    def __init__(
        self,
        page: int = 1,
        page_size: int = 10,
        total_rows: int = 0,
        on_page_change: Optional[Callable[[int], None]] = None,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.page = page
        self.page_size = page_size
        self.total_rows = total_rows
        self.on_page_change = on_page_change
        self.extra_class = class_
        self.attrs = attrs
    
    def render(self) -> str:
        total_pages = max(1, (self.total_rows + self.page_size - 1) // self.page_size)
        is_first = self.page <= 1
        is_last = self.page >= total_pages
        
        return f'''
<div class="{cn(PAGINATION_BASE, self.extra_class)}" data-pynext-pagination>
    <div class="{cn(PAGINATION_INFO_BASE)}">
        Page {self.page} of {total_pages}
    </div>
    <div class="{cn(PAGINATION_BUTTONS_BASE)}">
        <button class="{cn(PAGINATION_BUTTON_BASE)}"
                data-page="1"
                {"disabled" if is_first else ""}
                aria-label="First page">«</button>
        <button class="{cn(PAGINATION_BUTTON_BASE)}"
                data-page="{self.page - 1}"
                {"disabled" if is_first else ""}
                aria-label="Previous page">‹</button>
        <button class="{cn(PAGINATION_BUTTON_BASE)}"
                data-page="{self.page + 1}"
                {"disabled" if is_last else ""}
                aria-label="Next page">›</button>
        <button class="{cn(PAGINATION_BUTTON_BASE)}"
                data-page="{total_pages}"
                {"disabled" if is_last else ""}
                aria-label="Last page">»</button>
    </div>
</div>
'''
    
    def __str__(self) -> str:
        return self.render()


# Column toggle button styles
COLUMN_TOGGLE_BASE = (
    "inline-flex items-center justify-center rounded-md text-sm font-medium "
    "ring-offset-background transition-colors focus-visible:outline-none "
    "focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 "
    "disabled:pointer-events-none disabled:opacity-50 "
    "border border-input bg-background hover:bg-accent hover:text-accent-foreground "
    "h-8 px-3"
)

COLUMN_TOGGLE_CONTENT_BASE = (
    "z-50 min-w-[150px] overflow-hidden rounded-md border bg-popover p-1 "
    "text-popover-foreground shadow-md"
)

COLUMN_TOGGLE_ITEM_BASE = (
    "relative flex cursor-pointer select-none items-center rounded-sm px-2 py-1.5 "
    "text-sm outline-none hover:bg-accent hover:text-accent-foreground"
)


class DataTableColumnToggle:
    """
    A dropdown menu to toggle column visibility.
    
    Place this in a DataTableToolbar to let users show/hide columns.
    
    Attributes:
        columns: List of DataTableColumn definitions
        visibility: Current visibility state (accessor -> bool)
        on_visibility_change: Callback when visibility changes
    
    Example:
        DataTableToolbar()[
            Input(placeholder="Search..."),
            DataTableColumnToggle(
                columns=columns,
                visibility=column_visibility,
                on_visibility_change=set_visibility,
            ),
        ]
    """
    
    def __init__(
        self,
        columns: List[DataTableColumn],
        visibility: Optional[Dict[str, bool]] = None,
        on_visibility_change: Optional[Callable[[Dict[str, bool]], None]] = None,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.columns = columns
        self.visibility = visibility or {}
        self.on_visibility_change = on_visibility_change
        self.extra_class = class_
        self.attrs = attrs
    
    def render(self) -> str:
        toggle_id = hashlib.md5(str(id(self)).encode()).hexdigest()[:8]
        
        # Build column items
        items = []
        for col in self.columns:
            is_visible = self.visibility.get(col.accessor, True)
            header_text = col.header if isinstance(col.header, str) else col.accessor
            
            check_icon = '''
<svg class="mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
</svg>
''' if is_visible else '<span class="mr-2 h-4 w-4"></span>'
            
            items.append(f'''
<div data-pynext-column-toggle-item="{col.accessor}"
     data-visible="{str(is_visible).lower()}"
     class="{cn(COLUMN_TOGGLE_ITEM_BASE)}"
     role="menuitemcheckbox"
     aria-checked="{str(is_visible).lower()}">
    {check_icon}
    {header_text}
</div>
''')
        
        return f'''
<div data-pynext-column-toggle="{toggle_id}" class="relative inline-block">
    <button data-pynext-column-toggle-trigger
            class="{cn(COLUMN_TOGGLE_BASE, self.extra_class)}"
            aria-haspopup="true"
            aria-expanded="false">
        <svg class="mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                  d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7"/>
        </svg>
        Columns
    </button>
    <div data-pynext-column-toggle-content
         class="{cn(COLUMN_TOGGLE_CONTENT_BASE)}"
         style="display:none; position:absolute; right:0; top:100%; margin-top:0.25rem;"
         role="menu">
        {"".join(items)}
    </div>
</div>
'''
    
    def __str__(self) -> str:
        return self.render()

