# Component Patterns

> **Build reusable, composable, and extendable components**

Learn advanced patterns for creating components that are flexible, maintainable, and consistent.

---

## What You'll Learn

- Composition patterns
- Variant systems
- Extending ShadCN components
- Compound components
- Render props and slots
- Polymorphic components

---

## 1. Composition Over Props

Instead of adding many props, compose smaller components:

```python
# ❌ Too many props
def Card(
    title=None,
    description=None,
    footer=None,
    header_action=None,
    variant="default",
    size="md",
    ...
):
    # Complex conditional rendering
    pass

# ✅ Composable components
def Card(children, class_=""):
    return div(class_=cn("rounded-lg border bg-card", class_))[children]

def CardHeader(children, class_=""):
    return div(class_=cn("flex flex-col space-y-1.5 p-6", class_))[children]

def CardTitle(children, class_=""):
    return h3(class_=cn("font-semibold leading-none", class_))[children]

def CardContent(children, class_=""):
    return div(class_=cn("p-6 pt-0", class_))[children]

# Usage - compose as needed
Card()[
    CardHeader()[
        CardTitle()["My Card"],
        Button(size="sm")["Action"],  # Add whatever you need
    ],
    CardContent()[
        "Content here"
    ],
]
```

---

## 2. Variant System

Create consistent variant patterns with `cn()`:

```python
from pynext.tw import cn

def button_variants(variant="default", size="default"):
    """Generate button class names based on variants."""
    
    base = "inline-flex items-center justify-center rounded-md font-medium transition-colors"
    
    variants = {
        "default": "bg-primary text-primary-foreground hover:bg-primary/90",
        "destructive": "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        "outline": "border border-input bg-background hover:bg-accent",
        "secondary": "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        "ghost": "hover:bg-accent hover:text-accent-foreground",
        "link": "text-primary underline-offset-4 hover:underline",
    }
    
    sizes = {
        "default": "h-10 px-4 py-2",
        "sm": "h-9 px-3 text-sm",
        "lg": "h-11 px-8 text-lg",
        "icon": "h-10 w-10",
    }
    
    return cn(base, variants.get(variant, ""), sizes.get(size, ""))


def Button(
    children,
    variant="default",
    size="default",
    class_="",
    **props,
):
    return button(
        class_=cn(button_variants(variant, size), class_),
        **props,
    )[children]
```

### Factory Function Pattern

```python
def create_variant_component(base_styles: str, variants: dict, default_variant: str):
    """Factory for creating variant-based components."""
    
    def component(children, variant=default_variant, class_="", **props):
        return div(
            class_=cn(base_styles, variants.get(variant, ""), class_),
            **props,
        )[children]
    
    return component


# Create Badge component
Badge = create_variant_component(
    base_styles="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold",
    variants={
        "default": "bg-primary text-primary-foreground",
        "secondary": "bg-secondary text-secondary-foreground",
        "destructive": "bg-destructive text-destructive-foreground",
        "outline": "border text-foreground",
    },
    default_variant="default",
)

# Usage
Badge(variant="destructive")["Error"]
```

---

## 3. Extending ShadCN Components

Build on existing components:

```python
from pynext.shadcn import Button as BaseButton, Input as BaseInput

# Extended button with loading state
def Button(
    children,
    loading=False,
    disabled=False,
    **props,
):
    return BaseButton(
        disabled=disabled or loading,
        **props,
    )[
        loading and span(class_="mr-2 animate-spin")["⏳"],
        children,
    ]


# Input with icon
def IconInput(
    icon,
    icon_position="left",
    class_="",
    **props,
):
    return div(class_="relative")[
        div(class_=cn(
            "absolute top-1/2 -translate-y-1/2 text-muted-foreground",
            "left-3" if icon_position == "left" else "right-3",
        ))[icon],
        BaseInput(
            class_=cn(
                "pl-10" if icon_position == "left" else "pr-10",
                class_,
            ),
            **props,
        ),
    ]


# Usage
IconInput(icon="🔍", placeholder="Search...")
```

---

## 4. Compound Components

Components that work together sharing state:

```python
from pynext import Signal

class TabsContext:
    """Shared state for Tabs components."""
    active = Signal("tab1")

def Tabs(default_value, children, class_=""):
    """Container for tabbed content."""
    TabsContext.active.set(default_value)
    return div(class_=class_)[children]

def TabsList(children, class_=""):
    """List of tab triggers."""
    return div(class_=cn(
        "inline-flex h-10 items-center justify-center rounded-md bg-muted p-1",
        class_,
    ))[children]

def TabsTrigger(value, children, class_=""):
    """Individual tab button."""
    is_active = TabsContext.active.value == value
    
    return button(
        class_=cn(
            "inline-flex items-center justify-center px-3 py-1.5 text-sm rounded-sm",
            is_active and "bg-background shadow-sm",
            not is_active and "text-muted-foreground",
            class_,
        ),
        onclick=lambda: TabsContext.active.set(value),
    )[children]

def TabsContent(value, children, class_=""):
    """Content for a specific tab."""
    if TabsContext.active.value != value:
        return None
    
    return div(class_=class_)[children]


# Usage
Tabs(default_value="account")[
    TabsList()[
        TabsTrigger(value="account")["Account"],
        TabsTrigger(value="password")["Password"],
    ],
    TabsContent(value="account")[
        "Account settings..."
    ],
    TabsContent(value="password")[
        "Password settings..."
    ],
]
```

---

## 5. Slot Pattern

Allow custom content in specific places:

```python
def Card(
    children,
    header=None,
    footer=None,
    class_="",
):
    """Card with optional header and footer slots."""
    return div(class_=cn("rounded-lg border bg-card", class_))[
        header and div(class_="border-b p-4")[header],
        div(class_="p-4")[children],
        footer and div(class_="border-t p-4")[footer],
    ]


# Usage
Card(
    header=div(class_="flex justify-between")[
        h3()["Title"],
        Button(size="sm")["Edit"],
    ],
    footer=Button(class_="w-full")["Save"],
)[
    "Main content here"
]
```

---

## 6. Polymorphic Components

Components that can render as different elements:

```python
def Text(
    as_: str = "p",
    size: str = "base",
    children=None,
    class_: str = "",
    **props,
):
    """Text component that can render as any element."""
    sizes = {
        "xs": "text-xs",
        "sm": "text-sm",
        "base": "text-base",
        "lg": "text-lg",
        "xl": "text-xl",
        "2xl": "text-2xl",
    }
    
    # Create the element dynamically
    element_map = {
        "p": p,
        "span": span,
        "h1": h1,
        "h2": h2,
        "h3": h3,
        "label": label,
    }
    
    Element = element_map.get(as_, p)
    
    return Element(
        class_=cn(sizes.get(size, ""), class_),
        **props,
    )[children]


# Usage
Text(as_="h1", size="2xl")["Heading"]
Text(as_="span", size="sm", class_="text-muted-foreground")["Caption"]
```

---

## 7. Render Props Pattern

Pass render functions for custom rendering:

```python
def List(
    items: list,
    render_item,
    empty_state=None,
    class_="",
):
    """Generic list with custom item rendering."""
    if not items:
        return empty_state or div(class_="text-muted-foreground")["No items"]
    
    return ul(class_=class_)[
        [
            li(key=str(i))[render_item(item, i)]
            for i, item in enumerate(items)
        ]
    ]


# Usage
List(
    items=users,
    render_item=lambda user, i: div(class_="flex items-center gap-2")[
        Avatar()[user.initials],
        span()[user.name],
    ],
    empty_state=div()["No users found"],
)
```

---

## 8. Higher-Order Components

Wrap components to add functionality:

```python
def with_loading(Component):
    """Add loading state to any component."""
    def Wrapped(loading=False, *args, **kwargs):
        if loading:
            return div(class_="animate-pulse bg-muted rounded")[
                Component(*args, **kwargs)
            ]
        return Component(*args, **kwargs)
    return Wrapped


def with_tooltip(Component):
    """Add tooltip to any component."""
    def Wrapped(tooltip=None, *args, **kwargs):
        inner = Component(*args, **kwargs)
        if not tooltip:
            return inner
        return Tooltip()[
            TooltipTrigger()[inner],
            TooltipContent()[tooltip],
        ]
    return Wrapped


# Usage
LoadingButton = with_loading(Button)
TooltipButton = with_tooltip(Button)

LoadingButton(loading=True)["Submit"]
TooltipButton(tooltip="Click to save")["Save"]
```

---

## 9. Form Field Pattern

Consistent form field wrapper:

```python
def FormField(
    name: str,
    label: str = None,
    description: str = None,
    error: str = None,
    required: bool = False,
    children=None,
):
    """Wrapper for form fields with label, description, and error."""
    return div(class_="space-y-2")[
        label and Label(html_for=name)[
            label,
            required and span(class_="text-destructive ml-1")["*"],
        ],
        children,  # The actual input/select/textarea
        description and not error and p(
            class_="text-sm text-muted-foreground"
        )[description],
        error and p(
            class_="text-sm text-destructive"
        )[error],
    ]


# Usage
FormField(
    name="email",
    label="Email",
    description="We'll never share your email",
    error=errors.get("email"),
    required=True,
)[
    Input(id="email", name="email", type="email")
]
```

---

## 10. Component Documentation Pattern

Document your components inline:

```python
def Button(
    children,
    variant: str = "default",
    size: str = "default",
    disabled: bool = False,
    loading: bool = False,
    class_: str = "",
    **props,
):
    """
    Primary button component.
    
    Variants:
        - default: Primary action button
        - secondary: Less prominent action
        - destructive: Dangerous actions (delete, etc.)
        - outline: Bordered, transparent background
        - ghost: Minimal, no background until hover
        - link: Looks like a text link
    
    Sizes:
        - default: Standard size (h-10)
        - sm: Smaller (h-9)
        - lg: Larger (h-11)
        - icon: Square for icon buttons (h-10 w-10)
    
    Examples:
        Button()["Click me"]
        Button(variant="destructive")["Delete"]
        Button(loading=True)["Saving..."]
    """
    # Implementation...
```

---

## Complete Example: DataTable Component

```python
from dataclasses import dataclass
from typing import List, Callable, Optional

@dataclass
class Column:
    key: str
    label: str
    sortable: bool = False
    render: Optional[Callable] = None

def DataTable(
    data: List[dict],
    columns: List[Column],
    selectable: bool = False,
    on_select: Callable = None,
    empty_state=None,
    class_: str = "",
):
    """
    Full-featured data table component.
    
    Features:
    - Sortable columns
    - Row selection
    - Custom cell rendering
    - Empty state
    """
    selected = Signal(set())
    sort_key = Signal(None)
    sort_dir = Signal("asc")
    
    def toggle_select(id):
        current = selected.value.copy()
        if id in current:
            current.discard(id)
        else:
            current.add(id)
        selected.set(current)
        on_select and on_select(current)
    
    def toggle_sort(key):
        if sort_key.value == key:
            sort_dir.set("desc" if sort_dir.value == "asc" else "asc")
        else:
            sort_key.set(key)
            sort_dir.set("asc")
    
    # Sort data
    sorted_data = data
    if sort_key.value:
        sorted_data = sorted(
            data,
            key=lambda x: x.get(sort_key.value, ""),
            reverse=sort_dir.value == "desc",
        )
    
    if not data:
        return empty_state or EmptyState()
    
    return div(class_=cn("rounded-md border", class_))[
        table(class_="w-full")[
            thead(class_="bg-muted/50")[
                tr()[
                    selectable and th(class_="w-10 px-4")[
                        Checkbox(
                            checked=len(selected.value) == len(data),
                            onchange=lambda: selected.set(
                                set() if selected.value else {row["id"] for row in data}
                            ),
                        )
                    ],
                    [
                        th(
                            class_=cn(
                                "px-4 py-3 text-left text-sm font-medium",
                                col.sortable and "cursor-pointer hover:bg-muted",
                            ),
                            onclick=lambda c=col: c.sortable and toggle_sort(c.key),
                        )[
                            div(class_="flex items-center gap-2")[
                                col.label,
                                col.sortable and sort_key.value == col.key and span()[
                                    "↑" if sort_dir.value == "asc" else "↓"
                                ],
                            ]
                        ]
                        for col in columns
                    ],
                ]
            ],
            tbody()[
                [
                    tr(class_=cn(
                        "border-t hover:bg-muted/50",
                        row["id"] in selected.value and "bg-primary/10",
                    ))[
                        selectable and td(class_="px-4")[
                            Checkbox(
                                checked=row["id"] in selected.value,
                                onchange=lambda r=row: toggle_select(r["id"]),
                            )
                        ],
                        [
                            td(class_="px-4 py-3 text-sm")[
                                col.render(row) if col.render else str(row.get(col.key, ""))
                            ]
                            for col in columns
                        ],
                    ]
                    for row in sorted_data
                ]
            ],
        ],
    ]
```

---

## Key Takeaways

1. **Compose, don't configure** — Small pieces over mega-props
2. **Variants for consistency** — Use `cn()` and variant maps
3. **Extend, don't duplicate** — Build on existing components
4. **Share state carefully** — Context for compound components
5. **Document inline** — Help future you (and others)

---

## Related Tutorials

- [Theming](./theming.md) - Styling components
- [State Management](./state-management.md) - Component state patterns

