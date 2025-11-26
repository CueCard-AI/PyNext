# Sheet

A slide-out panel that appears from the edge of the screen. Also known as a drawer.

## Installation

```python
from pynext.shadcn import (
    Sheet, SheetTrigger, SheetContent,
    SheetHeader, SheetTitle, SheetDescription,
    SheetFooter, SheetClose
)
```

## Basic Usage

```python
Sheet()[
    SheetTrigger()[
        Button()["Open Settings"]
    ],
    SheetContent()[
        SheetHeader()[
            SheetTitle()["Settings"],
            SheetDescription()["Configure your preferences"]
        ],
        div(class_="py-4")[
            # Form content here
        ],
        SheetFooter()[
            Button()["Save changes"]
        ]
    ]
]
```

## Examples

### Side Navigation

```python
Sheet()[
    SheetTrigger()[
        Button(variant="ghost", size="icon")["☰"]
    ],
    SheetContent(side="left")[
        nav(class_="flex flex-col space-y-2")[
            a(href="/")["Home"],
            a(href="/products")["Products"],
            a(href="/about")["About"],
            a(href="/contact")["Contact"],
        ]
    ]
]
```

### Different Sides

```python
# Right (default)
SheetContent(side="right")[...]

# Left
SheetContent(side="left")[...]

# Top
SheetContent(side="top")[...]

# Bottom
SheetContent(side="bottom")[...]
```

### Without Close Button

```python
SheetContent(show_close=False)[
    # No X button in corner
    SheetClose()[
        Button()["Close manually"]
    ]
]
```

### Cart Drawer

```python
Sheet()[
    SheetTrigger()[
        Button(variant="outline")["🛒 Cart (3)"]
    ],
    SheetContent()[
        SheetHeader()[
            SheetTitle()["Shopping Cart"],
            SheetDescription()["3 items in your cart"]
        ],
        div(class_="flex-1 overflow-y-auto py-4")[
            # Cart items
            [CartItem(item=item) for item in cart_items]
        ],
        SheetFooter(class_="border-t pt-4")[
            div(class_="w-full space-y-4")[
                div(class_="flex justify-between")[
                    span()["Total"],
                    span(class_="font-bold")["$299.00"]
                ],
                Button(class_="w-full")["Checkout"]
            ]
        ]
    ]
]
```

## API Reference

### Sheet

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `open` | `bool` | `None` | Controlled open state |
| `on_open_change` | `Callable` | `None` | Callback when state changes |

### SheetContent

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `side` | `"top" \| "bottom" \| "left" \| "right"` | `"right"` | Which edge to slide from |
| `show_close` | `bool` | `True` | Show close button |

### SheetHeader, SheetFooter

Container components for semantic structure.

### SheetTitle, SheetDescription

Text components with appropriate styling.

### SheetClose

Closes the sheet when clicked.

## Styling

Default widths by side:

- **left/right**: `w-3/4 sm:max-w-sm`
- **top/bottom**: Full width with auto height

Customize with `class_`:

```python
SheetContent(side="left", class_="w-96")[...]
```

## Mobile Swipe to Close

On touch devices, users can swipe to dismiss the sheet in the direction of the edge it appeared from:

```
┌─────────────────────────────────────────────┐
│                                             │
│                                     ┌──────┐│
│                                     │      ││
│    Swipe right ──────────────►      │Sheet ││
│    to close                         │      ││
│                                     │      ││
│                                     └──────┘│
│                                             │
└─────────────────────────────────────────────┘
```

- **Right sheet**: Swipe right to close
- **Left sheet**: Swipe left to close
- **Top sheet**: Swipe up to close
- **Bottom sheet**: Swipe down to close

The swipe gesture includes:
- **Visual feedback**: Sheet follows your finger during drag
- **Velocity detection**: Fast swipes close even with small distance
- **Threshold**: Minimum 100px drag or high velocity required

## Accessibility

- Focus is trapped inside when open
- Closes on Escape key
- Closes on overlay click
- **Swipe to close on mobile** (touch devices)
- Uses `role="dialog"` and `aria-modal="true"`
- Body scroll is locked when open

