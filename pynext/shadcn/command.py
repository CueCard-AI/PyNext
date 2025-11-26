"""
Command Component (cmdk-style Command Palette)

A fast, composable command menu with fuzzy search.
Perfect for keyboard-driven navigation and actions.

Usage:
    from pynext.shadcn import (
        Command, CommandDialog, CommandInput, CommandList,
        CommandEmpty, CommandGroup, CommandItem, CommandSeparator,
        CommandShortcut
    )
    
    # Basic command menu
    Command()[
        CommandInput(placeholder="Type a command or search..."),
        CommandList()[
            CommandEmpty()["No results found."],
            CommandGroup(heading="Suggestions")[
                CommandItem(value="calendar")["Calendar"],
                CommandItem(value="search")["Search"],
                CommandItem(value="settings")["Settings"],
            ],
        ]
    ]
    
    # As a dialog (⌘K)
    CommandDialog(open=open_state, on_open_change=set_open)[
        CommandInput(placeholder="Search..."),
        CommandList()[
            CommandGroup(heading="Actions")[
                CommandItem(value="new", on_select=create_new)[
                    "Create New",
                    CommandShortcut()["⌘N"]
                ],
            ]
        ]
    ]
"""

from typing import Any, Optional, List, Union, Callable
from pynext.tw import cn
import hashlib


# Command container styles
COMMAND_BASE = (
    "flex h-full w-full flex-col overflow-hidden rounded-md "
    "bg-popover text-popover-foreground"
)

# Command dialog styles (when used as modal)
COMMAND_DIALOG_BASE = (
    "fixed left-[50%] top-[50%] z-50 w-full max-w-lg translate-x-[-50%] "
    "translate-y-[-50%] rounded-lg border bg-popover shadow-lg "
    "data-[state=open]:animate-in data-[state=closed]:animate-out "
    "data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 "
    "data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95"
)

COMMAND_DIALOG_OVERLAY_BASE = (
    "fixed inset-0 z-50 bg-black/50 data-[state=open]:animate-in "
    "data-[state=closed]:animate-out data-[state=closed]:fade-out-0 "
    "data-[state=open]:fade-in-0"
)

# Command input styles
COMMAND_INPUT_BASE = (
    "flex h-11 w-full rounded-md bg-transparent py-3 text-sm "
    "outline-none placeholder:text-muted-foreground "
    "disabled:cursor-not-allowed disabled:opacity-50"
)

# Command list styles
COMMAND_LIST_BASE = (
    "max-h-[300px] overflow-y-auto overflow-x-hidden"
)

# Command empty state
COMMAND_EMPTY_BASE = "py-6 text-center text-sm"

# Command group styles
COMMAND_GROUP_BASE = "overflow-hidden p-1"
COMMAND_GROUP_HEADING_BASE = (
    "px-2 py-1.5 text-xs font-medium text-muted-foreground"
)

# Command item styles
COMMAND_ITEM_BASE = (
    "relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 "
    "text-sm outline-none data-[disabled=true]:pointer-events-none "
    "data-[selected=true]:bg-accent data-[selected=true]:text-accent-foreground "
    "data-[disabled=true]:opacity-50"
)

# Command separator
COMMAND_SEPARATOR_BASE = "-mx-1 h-px bg-border"

# Command shortcut
COMMAND_SHORTCUT_BASE = (
    "ml-auto text-xs tracking-widest text-muted-foreground"
)


class Command:
    """
    Root component for a command menu.
    
    Attributes:
        value: Currently selected value
        on_value_change: Callback when selection changes
        filter: Custom filter function
        loop: Whether keyboard navigation loops
        class_: Additional CSS classes
    
    Example:
        Command()[
            CommandInput(placeholder="Search..."),
            CommandList()[
                CommandGroup(heading="Actions")[
                    CommandItem(value="copy")["Copy"],
                    CommandItem(value="paste")["Paste"],
                ]
            ]
        ]
    """
    
    def __init__(
        self,
        value: Optional[str] = None,
        on_value_change: Optional[Callable[[str], None]] = None,
        filter: Optional[Callable[[str, str], bool]] = None,
        loop: bool = False,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.value = value
        self.on_value_change = on_value_change
        self.filter = filter
        self.loop = loop
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "Command":
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
        
        command_id = hashlib.md5(str(id(self)).encode()).hexdigest()[:8]
        class_str = cn(COMMAND_BASE, self.extra_class)
        
        loop_attr = 'data-loop="true"' if self.loop else ""
        value_attr = f'data-value="{self.value}"' if self.value else ""
        
        return f'''
<div data-pynext-command="{command_id}"
     {value_attr}
     {loop_attr}
     class="{class_str}"
     role="listbox">
    {children_html}
</div>
'''
    
    def __str__(self) -> str:
        return self.render()


class CommandDialog:
    """
    Command menu displayed as a modal dialog.
    
    Typically opened with ⌘K.
    
    Attributes:
        open: Controlled open state
        on_open_change: Callback when open state changes
        class_: Additional CSS classes
    
    Example:
        CommandDialog(open=is_open, on_open_change=set_open)[
            CommandInput(placeholder="Search..."),
            CommandList()[...]
        ]
    """
    
    def __init__(
        self,
        open: Optional[bool] = None,
        on_open_change: Optional[Callable[[bool], None]] = None,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.open = open
        self.on_open_change = on_open_change
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "CommandDialog":
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
        
        dialog_id = hashlib.md5(str(id(self)).encode()).hexdigest()[:8]
        state = "open" if self.open else "closed"
        
        dialog_class = cn(COMMAND_DIALOG_BASE, self.extra_class)
        overlay_class = cn(COMMAND_DIALOG_OVERLAY_BASE)
        command_class = cn(COMMAND_BASE, "[&_[data-pynext-command-input-wrapper]]:border-b")
        
        display = "" if self.open else "display:none;"
        
        return f'''
<div data-pynext-command-dialog="{dialog_id}" data-state="{state}">
    <div class="{overlay_class}" data-pynext-command-dialog-overlay data-state="{state}" style="{display}"></div>
    <div class="{dialog_class}" data-state="{state}" style="{display}">
        <div class="{command_class}" data-pynext-command role="listbox">
            {children_html}
        </div>
    </div>
</div>
'''
    
    def __str__(self) -> str:
        return self.render()


class CommandInput:
    """
    The search input for the command menu.
    
    Attributes:
        placeholder: Placeholder text
        class_: Additional CSS classes
    
    Example:
        CommandInput(placeholder="Type a command or search...")
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
        class_str = cn(COMMAND_INPUT_BASE, self.extra_class)
        
        return f'''
<div class="flex items-center border-b px-3" data-pynext-command-input-wrapper>
    <svg class="mr-2 h-4 w-4 shrink-0 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
    </svg>
    <input data-pynext-command-input
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


class CommandList:
    """
    Container for command items and groups.
    
    Example:
        CommandList()[
            CommandGroup(heading="Actions")[...]
        ]
    """
    
    def __init__(self, class_: Optional[str] = None, **attrs: Any):
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "CommandList":
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
        
        class_str = cn(COMMAND_LIST_BASE, self.extra_class)
        
        return f'''
<div data-pynext-command-list class="{class_str}" role="listbox">
    {children_html}
</div>
'''
    
    def __str__(self) -> str:
        return self.render()


class CommandEmpty:
    """
    Displayed when no results match the search.
    
    Example:
        CommandEmpty()["No results found."]
    """
    
    def __init__(self, class_: Optional[str] = None, **attrs: Any):
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "CommandEmpty":
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
        
        class_str = cn(COMMAND_EMPTY_BASE, self.extra_class)
        
        return f'''
<div data-pynext-command-empty class="{class_str}" style="display:none">
    {children_html}
</div>
'''
    
    def __str__(self) -> str:
        return self.render()


class CommandGroup:
    """
    A group of related command items.
    
    Attributes:
        heading: Optional group heading
        class_: Additional CSS classes
    
    Example:
        CommandGroup(heading="Suggestions")[
            CommandItem(value="calendar")["Calendar"],
            CommandItem(value="settings")["Settings"],
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
    
    def __getitem__(self, children: Union[Any, tuple]) -> "CommandGroup":
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
        
        class_str = cn(COMMAND_GROUP_BASE, self.extra_class)
        heading_class = cn(COMMAND_GROUP_HEADING_BASE)
        
        heading_html = ""
        if self.heading:
            heading_html = f'<div data-pynext-command-group-heading class="{heading_class}">{self.heading}</div>'
        
        return f'''
<div data-pynext-command-group class="{class_str}" role="group">
    {heading_html}
    {children_html}
</div>
'''
    
    def __str__(self) -> str:
        return self.render()


class CommandItem:
    """
    An individual command item.
    
    Attributes:
        value: The value when selected (also used for search matching)
        on_select: Callback when item is selected
        disabled: Whether the item is disabled
        class_: Additional CSS classes
    
    Example:
        CommandItem(value="copy", on_select=copy_handler)[
            "Copy to clipboard",
            CommandShortcut()["⌘C"]
        ]
    """
    
    def __init__(
        self,
        value: str,
        on_select: Optional[Callable[[], None]] = None,
        disabled: bool = False,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.value = value
        self.on_select = on_select
        self.disabled = disabled
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "CommandItem":
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
        
        class_str = cn(COMMAND_ITEM_BASE, self.extra_class)
        disabled_attr = 'data-disabled="true"' if self.disabled else ""
        
        return f'''
<div data-pynext-command-item
     data-value="{self.value}"
     {disabled_attr}
     role="option"
     class="{class_str}">
    {children_html}
</div>
'''
    
    def __str__(self) -> str:
        return self.render()


class CommandSeparator:
    """A visual separator between groups."""
    
    def __init__(self, class_: Optional[str] = None, **attrs: Any):
        self.extra_class = class_
        self.attrs = attrs
    
    def render(self) -> str:
        class_str = cn(COMMAND_SEPARATOR_BASE, self.extra_class)
        return f'<div class="{class_str}" role="separator"></div>'
    
    def __str__(self) -> str:
        return self.render()


class CommandShortcut:
    """
    Display a keyboard shortcut hint.
    
    Example:
        CommandItem(value="save")[
            "Save",
            CommandShortcut()["⌘S"]
        ]
    """
    
    def __init__(self, class_: Optional[str] = None, **attrs: Any):
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "CommandShortcut":
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
        
        class_str = cn(COMMAND_SHORTCUT_BASE, self.extra_class)
        
        return f'<span data-pynext-command-shortcut class="{class_str}">{children_html}</span>'
    
    def __str__(self) -> str:
        return self.render()

