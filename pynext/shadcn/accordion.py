"""
Accordion Components

A vertically stacked set of collapsible sections.

Usage:
    from pynext.shadcn import Accordion, AccordionItem, AccordionTrigger, AccordionContent
    
    Accordion(type="single", collapsible=True)[
        AccordionItem(value="item-1")[
            AccordionTrigger()["Is it accessible?"],
            AccordionContent()["Yes. It follows WAI-ARIA design patterns."]
        ],
        AccordionItem(value="item-2")[
            AccordionTrigger()["Is it styled?"],
            AccordionContent()["Yes. It comes with default styling."]
        ]
    ]
"""

from typing import Any, Optional, List, Union, Callable, Literal
from pynext.tw import cn


# Accordion styles
ACCORDION_ITEM_BASE = "border-b"

ACCORDION_TRIGGER_BASE = (
    "flex flex-1 items-center justify-between py-4 font-medium transition-all "
    "hover:underline [&[data-state=open]>svg]:rotate-180"
)

ACCORDION_CONTENT_BASE = (
    "overflow-hidden text-sm transition-all "
    "data-[state=closed]:animate-accordion-up data-[state=open]:animate-accordion-down"
)

ACCORDION_CONTENT_INNER_BASE = "pb-4 pt-0"


AccordionType = Literal["single", "multiple"]


class Accordion:
    """
    Root component for an accordion.
    
    Attributes:
        type: "single" (one panel at a time) or "multiple" (multiple panels)
        collapsible: If True and type="single", allows closing all panels
        default_value: Initially open panel(s)
    
    Example:
        Accordion(type="single", collapsible=True)[
            AccordionItem(value="item-1")[...],
            AccordionItem(value="item-2")[...]
        ]
    """
    
    def __init__(
        self,
        type: AccordionType = "single",
        collapsible: bool = False,
        default_value: Optional[Union[str, List[str]]] = None,
        value: Optional[Union[str, List[str]]] = None,
        on_value_change: Optional[Callable] = None,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.type = type
        self.collapsible = collapsible
        self.default_value = default_value
        self.value = value
        self.on_value_change = on_value_change
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "Accordion":
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
        
        import hashlib
        accordion_id = hashlib.md5(str(id(self)).encode()).hexdigest()[:8]
        
        attrs_str = f'data-pynext-accordion="{accordion_id}"'
        attrs_str += f' data-type="{self.type}"'
        
        if self.collapsible:
            attrs_str += ' data-collapsible'
        
        if self.extra_class:
            attrs_str += f' class="{self.extra_class}"'
        
        return f'<div {attrs_str}>{children_html}</div>'
    
    def __str__(self) -> str:
        return self.render()


class AccordionItem:
    """A single accordion section."""
    
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
    
    def __getitem__(self, children: Union[Any, tuple]) -> "AccordionItem":
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
        
        class_str = cn(ACCORDION_ITEM_BASE, self.extra_class)
        
        attrs_str = f'class="{class_str}"'
        attrs_str += f' data-pynext-accordion-item'
        attrs_str += f' data-value="{self.value}"'
        
        if self.disabled:
            attrs_str += ' data-disabled'
        
        return f'<div {attrs_str}>{children_html}</div>'
    
    def __str__(self) -> str:
        return self.render()


class AccordionTrigger:
    """The clickable header that expands/collapses the content."""
    
    def __init__(self, class_: Optional[str] = None, **attrs: Any):
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "AccordionTrigger":
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
        
        class_str = cn(ACCORDION_TRIGGER_BASE, self.extra_class)
        
        # Chevron icon
        chevron = '''
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-4 w-4 shrink-0 transition-transform duration-200">
    <path d="m6 9 6 6 6-6"></path>
</svg>
'''
        
        return f'''
<h3 class="flex">
    <button class="{class_str}" data-pynext-accordion-trigger>
        {children_html}
        {chevron}
    </button>
</h3>
'''
    
    def __str__(self) -> str:
        return self.render()


class AccordionContent:
    """The collapsible content of an accordion item."""
    
    def __init__(self, class_: Optional[str] = None, **attrs: Any):
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "AccordionContent":
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
        
        outer_class = cn(ACCORDION_CONTENT_BASE, self.extra_class)
        inner_class = ACCORDION_CONTENT_INNER_BASE
        
        return f'''
<div class="{outer_class}" data-pynext-accordion-content>
    <div class="{inner_class}">{children_html}</div>
</div>
'''
    
    def __str__(self) -> str:
        return self.render()

