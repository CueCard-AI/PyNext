"""
Combobox Component (Autocomplete)

A searchable dropdown for selecting from a list of options.
Supports async search, multi-select, and creating new items.

Usage:
    from pynext.shadcn import (
        Combobox, ComboboxTrigger, ComboboxInput, 
        ComboboxContent, ComboboxItem, ComboboxEmpty
    )
    
    # Basic usage
    Combobox(value=selected, on_value_change=set_selected)[
        ComboboxTrigger()[
            Button(variant="outline", class_="w-[200px] justify-between")[
                selected or "Select framework...",
                ChevronsUpDown(class_="ml-2 h-4 w-4 shrink-0 opacity-50"),
            ]
        ],
        ComboboxContent()[
            ComboboxInput(placeholder="Search framework..."),
            ComboboxEmpty()["No framework found."],
            [
                ComboboxItem(value=fw["value"], key=fw["value"])[
                    fw["label"]
                ]
                for fw in frameworks
            ]
        ]
    ]
    
    # With async search
    Combobox(on_search=search_users)[
        ComboboxTrigger()[...],
        ComboboxContent()[
            ComboboxInput(placeholder="Search users..."),
            ComboboxEmpty()["No users found."],
            # Items populated by search results
        ]
    ]
"""

from typing import Any, Optional, List, Union, Callable
from pynext.tw import cn
import hashlib


# Combobox trigger styles (matches Button outline variant)
COMBOBOX_TRIGGER_BASE = (
    "flex h-10 w-full items-center justify-between rounded-md border "
    "border-input bg-background px-3 py-2 text-sm ring-offset-background "
    "placeholder:text-muted-foreground focus:outline-none focus:ring-2 "
    "focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed "
    "disabled:opacity-50"
)

# Combobox content (dropdown) styles
COMBOBOX_CONTENT_BASE = (
    "z-50 min-w-[8rem] overflow-hidden rounded-md border bg-popover p-1 "
    "text-popover-foreground shadow-md data-[state=open]:animate-in "
    "data-[state=closed]:animate-out data-[state=closed]:fade-out-0 "
    "data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 "
    "data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2"
)

# Combobox input styles
COMBOBOX_INPUT_BASE = (
    "flex h-9 w-full rounded-md bg-transparent px-3 py-1 text-sm "
    "outline-none placeholder:text-muted-foreground disabled:cursor-not-allowed "
    "disabled:opacity-50"
)

# Combobox item styles
COMBOBOX_ITEM_BASE = (
    "relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 "
    "text-sm outline-none data-[disabled]:pointer-events-none "
    "data-[disabled]:opacity-50 data-[highlighted]:bg-accent "
    "data-[highlighted]:text-accent-foreground"
)

# Empty state styles
COMBOBOX_EMPTY_BASE = "py-6 text-center text-sm text-muted-foreground"

# Group styles
COMBOBOX_GROUP_BASE = "overflow-hidden p-1"
COMBOBOX_GROUP_HEADING_BASE = (
    "px-2 py-1.5 text-xs font-medium text-muted-foreground"
)

# Separator styles
COMBOBOX_SEPARATOR_BASE = "-mx-1 my-1 h-px bg-border"


class Combobox:
    """
    Root component for a combobox.
    
    Attributes:
        value: Currently selected value
        on_value_change: Callback when selection changes
        on_search: Async search callback
        on_create: Callback to create new item from search query
        multiple: Allow multiple selection
        allow_create: Show "create new" option when no matches
        open: Controlled open state
        on_open_change: Callback when open state changes
    
    Example:
        Combobox(value=selected, on_value_change=set_selected)[
            ComboboxTrigger()[...],
            ComboboxContent()[...]
        ]
        
        # With create new
        Combobox(
            value=selected,
            on_value_change=set_selected,
            allow_create=True,
            on_create=lambda query: create_item(query)
        )[
            ComboboxTrigger()[...],
            ComboboxContent()[
                ComboboxInput(placeholder="Search or create..."),
                ComboboxEmpty()["No results found."],
                ComboboxCreate()["Create"],  # Shows when no matches
            ]
        ]
    """
    
    def __init__(
        self,
        value: Optional[str] = None,
        on_value_change: Optional[Callable[[str], None]] = None,
        on_search: Optional[Callable[[str], None]] = None,
        on_create: Optional[Callable[[str], None]] = None,
        multiple: bool = False,
        allow_create: bool = False,
        open: Optional[bool] = None,
        on_open_change: Optional[Callable[[bool], None]] = None,
        **attrs: Any
    ):
        self.value = value
        self.on_value_change = on_value_change
        self.on_search = on_search
        self.on_create = on_create
        self.multiple = multiple
        self.allow_create = allow_create
        self.open = open
        self.on_open_change = on_open_change
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "Combobox":
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
        
        combobox_id = hashlib.md5(str(id(self)).encode()).hexdigest()[:8]
        
        state = "closed"
        if self.open is True:
            state = "open"
        
        value_attr = f'data-value="{self.value}"' if self.value else ""
        multiple_attr = 'data-multiple="true"' if self.multiple else ""
        allow_create_attr = 'data-allow-create="true"' if self.allow_create else ""
        
        return f'''
<div data-pynext-combobox="{combobox_id}" 
     data-state="{state}"
     {value_attr}
     {multiple_attr}
     {allow_create_attr}
     style="position:relative;display:inline-block">
    {children_html}
</div>
'''
    
    def __str__(self) -> str:
        return self.render()


class ComboboxTrigger:
    """The button that opens the combobox dropdown."""
    
    def __init__(self, as_child: bool = True, **attrs: Any):
        self.as_child = as_child
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "ComboboxTrigger":
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
        
        return f'''
<div data-pynext-combobox-trigger 
     role="combobox"
     aria-expanded="false"
     aria-haspopup="listbox"
     style="display:contents">
    {children_html}
</div>
'''
    
    def __str__(self) -> str:
        return self.render()


class ComboboxContent:
    """
    The dropdown content container.
    
    Attributes:
        class_: Additional CSS classes
        side: Preferred side for positioning
        align: Alignment within the side
    """
    
    def __init__(
        self,
        class_: Optional[str] = None,
        side: str = "bottom",
        align: str = "start",
        **attrs: Any
    ):
        self.extra_class = class_
        self.side = side
        self.align = align
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "ComboboxContent":
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
        
        class_str = cn(COMBOBOX_CONTENT_BASE, self.extra_class)
        
        return f'''
<div data-pynext-combobox-content
     data-side="{self.side}"
     data-align="{self.align}"
     data-state="closed"
     role="listbox"
     class="{class_str}"
     style="display:none;position:absolute;top:100%;left:0;margin-top:4px;min-width:100%">
    {children_html}
</div>
'''
    
    def __str__(self) -> str:
        return self.render()


class ComboboxInput:
    """
    The search input field within the combobox.
    
    Attributes:
        placeholder: Placeholder text
        class_: Additional CSS classes
    """
    
    def __init__(
        self,
        placeholder: str = "Search...",
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.placeholder = placeholder
        self.extra_class = class_
        self.attrs = attrs
    
    def render(self) -> str:
        class_str = cn(COMBOBOX_INPUT_BASE, self.extra_class)
        
        return f'''
<div class="flex items-center border-b px-3">
    <svg class="mr-2 h-4 w-4 shrink-0 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
    </svg>
    <input data-pynext-combobox-input
           type="text"
           class="{class_str}"
           placeholder="{self.placeholder}"
           autocomplete="off"
           autocorrect="off"
           spellcheck="false" />
</div>
'''
    
    def __str__(self) -> str:
        return self.render()


class ComboboxItem:
    """
    An individual item in the combobox list.
    
    Attributes:
        value: The value when selected
        disabled: Whether the item is disabled
        class_: Additional CSS classes
    
    Example:
        ComboboxItem(value="react")["React"]
    """
    
    def __init__(
        self,
        value: str,
        disabled: bool = False,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.value = value
        self.disabled = disabled
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "ComboboxItem":
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
        
        class_str = cn(COMBOBOX_ITEM_BASE, self.extra_class)
        disabled_attr = 'data-disabled="true"' if self.disabled else ""
        
        # Check icon (shown when selected)
        check_icon = '''
<svg class="mr-2 h-4 w-4 opacity-0 data-[selected=true]:opacity-100" 
     data-pynext-combobox-check
     fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
</svg>
'''
        
        return f'''
<div data-pynext-combobox-item
     data-value="{self.value}"
     {disabled_attr}
     role="option"
     class="{class_str}">
    {check_icon}
    {children_html}
</div>
'''
    
    def __str__(self) -> str:
        return self.render()


class ComboboxEmpty:
    """
    Displayed when no items match the search.
    
    Example:
        ComboboxEmpty()["No results found."]
    """
    
    def __init__(self, class_: Optional[str] = None, **attrs: Any):
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "ComboboxEmpty":
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
        
        class_str = cn(COMBOBOX_EMPTY_BASE, self.extra_class)
        
        return f'''
<div data-pynext-combobox-empty
     class="{class_str}"
     style="display:none">
    {children_html}
</div>
'''
    
    def __str__(self) -> str:
        return self.render()


class ComboboxGroup:
    """
    A group of items with an optional heading.
    
    Example:
        ComboboxGroup(heading="Fruits")[
            ComboboxItem(value="apple")["Apple"],
            ComboboxItem(value="banana")["Banana"],
        ]
    """
    
    def __init__(
        self,
        heading: Optional[str] = None,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.heading = heading
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "ComboboxGroup":
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
        
        class_str = cn(COMBOBOX_GROUP_BASE, self.extra_class)
        heading_class = cn(COMBOBOX_GROUP_HEADING_BASE)
        
        heading_html = ""
        if self.heading:
            heading_html = f'<div class="{heading_class}">{self.heading}</div>'
        
        return f'''
<div data-pynext-combobox-group class="{class_str}" role="group">
    {heading_html}
    {children_html}
</div>
'''
    
    def __str__(self) -> str:
        return self.render()


class ComboboxSeparator:
    """A visual separator between groups."""
    
    def __init__(self, class_: Optional[str] = None, **attrs: Any):
        self.extra_class = class_
        self.attrs = attrs
    
    def render(self) -> str:
        class_str = cn(COMBOBOX_SEPARATOR_BASE, self.extra_class)
        return f'<div class="{class_str}" role="separator"></div>'
    
    def __str__(self) -> str:
        return self.render()


# Create new item styles
COMBOBOX_CREATE_BASE = (
    "relative flex cursor-pointer select-none items-center rounded-sm px-2 py-1.5 "
    "text-sm outline-none hover:bg-accent hover:text-accent-foreground "
    "border-t mt-1 pt-2"
)


class ComboboxCreate:
    """
    A "create new" option that appears when no items match the search.
    
    Displays the current search query and allows creating a new item.
    Hidden when there are matching results, shown when `ComboboxEmpty` would show.
    
    Attributes:
        class_: Additional CSS classes
    
    Example:
        ComboboxContent()[
            ComboboxInput(placeholder="Search or create..."),
            ComboboxEmpty()["No results found."],
            ComboboxCreate()["Create"],  # "Create: {query}" is shown
        ]
    """
    
    def __init__(self, class_: Optional[str] = None, **attrs: Any):
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "ComboboxCreate":
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
        
        class_str = cn(COMBOBOX_CREATE_BASE, self.extra_class)
        
        # Plus icon
        plus_icon = '''
<svg class="mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
</svg>
'''
        
        return f'''
<div data-pynext-combobox-create
     class="{class_str}"
     style="display:none"
     role="option">
    {plus_icon}
    <span>{children_html}</span>
    <span data-pynext-combobox-create-query class="ml-1 font-medium"></span>
</div>
'''
    
    def __str__(self) -> str:
        return self.render()

