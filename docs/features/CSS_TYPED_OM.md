# CSS Typed Object Model (Phase 34.3)

CSS Typed OM provides type-safe CSS value manipulation with proper IDE autocompletion and arithmetic operations. Instead of parsing CSS strings, you work with typed values that can be manipulated programmatically.

## Overview

### What It Is

CSS Typed OM is a modern browser API (part of CSS Houdini) that represents CSS values as typed JavaScript objects rather than strings. PyNext provides full Python bindings with zero-runtime transpilation.

### Why Use It

| String-based CSS | CSS Typed OM |
|------------------|--------------|
| `el.style.width = "100px"` | `el.attributeStyleMap.set("width", CSS.px(100))` |
| No type checking | Full type hints and IDE autocompletion |
| Can't do arithmetic | `width.mul(2)` doubles the value |
| Parse errors at runtime | Type errors at transpile time |
| Browser parses every string | Pre-parsed, better performance |

### When to Use

- **Use Typed OM**: Dynamic styling, animations, theme systems, computed layouts
- **Use String CSS**: Simple static styles, fallback for older browsers

### Browser Support

| Browser | Support |
|---------|---------|
| Chrome/Edge | Full (since Chrome 66) |
| Safari | Partial (since Safari 16.4) |
| Firefox | Limited |

For production, consider feature detection or fallback to string-based CSS.

---

## Core API

### CSS Factory Namespace

The `CSS` namespace provides factory methods for creating typed CSS values:

```python
from pynext.client import CSS

# Length units
width = CSS.px(100)           # 100px
height = CSS.percent(50)      # 50%
margin = CSS.rem(2)           # 2rem
padding = CSS.em(1.5)         # 1.5em

# Viewport units
full_width = CSS.vw(100)      # 100vw
full_height = CSS.vh(100)     # 100vh

# Dynamic viewport units (mobile-safe)
safe_height = CSS.svh(100)    # Small viewport height
dynamic = CSS.dvh(100)        # Dynamic viewport height

# Container query units
card_width = CSS.cqw(50)      # 50% of container width
card_height = CSS.cqh(50)     # 50% of container height

# Typography units
line_spacing = CSS.lh(1)      # One line height
cap_size = CSS.cap(1)         # Capital letter height

# Angle units
rotation = CSS.deg(45)        # 45deg
radians = CSS.rad(3.14159)    # ~180deg

# Time units
duration = CSS.ms(300)        # 300ms

# Grid fractions
col = CSS.fr(1)               # 1fr

# Keywords
display = CSS.keyword("flex")
margin = CSS.keyword("auto")
```

### CSSUnitValue

The most common type - a numeric value with a unit:

```python
from pynext.client import CSS

width = CSS.px(100)

# Access components
value = width.value    # 100
unit = width.unit      # "px"

# String conversion
css_str = width.toString()  # "100px"

# Arithmetic
doubled = width.mul(2)      # 200px
half = width.div(2)         # 50px
added = width.add(CSS.px(50))  # 150px
subtracted = width.sub(CSS.px(30))  # 70px

# Comparison
is_equal = width.equals(CSS.px(100))  # True

# Unit conversion (same type only)
deg_val = CSS.deg(180)
rad_val = deg_val.to("rad")  # ~3.14159rad
```

### Math Functions

For responsive values using CSS functions:

```python
from pynext.client import CSS

# calc()
width = CSS.calc("100% - 20px")
height = CSS.calc("50vh + 2rem")

# min() - smallest of values
min_width = CSS.min(CSS.px(300), CSS.percent(100))

# max() - largest of values  
max_width = CSS.max(CSS.px(100), CSS.percent(50))

# clamp() - value between min and max
font_size = CSS.clamp(CSS.px(12), CSS.vw(2), CSS.px(24))
```

### StylePropertyMap

Type-safe inline style manipulation via `element.attributeStyleMap`:

```python
from pynext.client import document, CSS

el = document.getElementById("box")
style_map = el.attributeStyleMap

# Set styles with typed values
style_map.set("width", CSS.px(200))
style_map.set("height", CSS.percent(100))
style_map.set("margin", CSS.rem(2))
style_map.set("display", CSS.keyword("flex"))

# Get styles (returns CSSStyleValue)
width = style_map.get("width")
if width:
    print(width.value, width.unit)  # 200 "px"

# Check existence
if style_map.has("width"):
    # ... width is set

# Delete
style_map.delete("margin")

# Clear all
style_map.clear()

# Size
count = style_map.size

# Iteration
for prop in style_map.keys():
    value = style_map.get(prop)
    print(prop, value)
```

### Computed Styles

Read-only access to resolved computed styles:

```python
from pynext.client import document

el = document.getElementById("box")
computed = el.computedStyleMap()

# Get resolved values (% → px, etc.)
width = computed.get("width")  # Returns px, not original %
print(width.value, width.unit)  # e.g., 500 "px"

# Check if property has value
if computed.has("transform"):
    transform = computed.get("transform")

# Iterate all computed properties
for prop in computed.keys():
    value = computed.get(prop)
```

---

## Transforms

### Individual Transforms

```python
from pynext.client import CSS

# Translate
move = CSS.translate(CSS.px(100), CSS.px(50))
move_x = CSS.translateX(CSS.px(100))
move_y = CSS.translateY(CSS.px(50))
move_z = CSS.translateZ(CSS.px(25))
move_3d = CSS.translate3d(CSS.px(100), CSS.px(50), CSS.px(25))

# Rotate
spin = CSS.rotate(CSS.deg(45))
spin_x = CSS.rotateX(CSS.deg(90))
spin_y = CSS.rotateY(CSS.deg(90))
spin_z = CSS.rotateZ(CSS.deg(45))

# Scale
grow = CSS.scale(2)           # uniform
stretch = CSS.scale(2, 1.5)   # x, y
squash = CSS.scaleX(0.5)
tall = CSS.scaleY(1.5)

# Skew
slant = CSS.skew(CSS.deg(10), CSS.deg(5))
slant_x = CSS.skewX(CSS.deg(10))
slant_y = CSS.skewY(CSS.deg(5))

# Perspective
depth = CSS.perspective(CSS.px(500))
```

### Combined Transforms

```python
from pynext.client import CSS, CSSTransformValue, document

# Combine multiple transforms
transform = CSSTransformValue([
    CSS.translate(CSS.px(100), CSS.px(50)),
    CSS.rotate(CSS.deg(45)),
    CSS.scale(1.5),
])

# Apply to element
el = document.getElementById("animated")
el.attributeStyleMap.set("transform", transform)

# Access components
count = transform.length  # 3
first = transform[0]      # CSSTranslate
is_2d = transform.is2D    # True

# Convert to matrix
matrix = transform.toMatrix()
```

---

## Colors

### Creating Colors

```python
from pynext.client import CSS

# RGB
red = CSS.rgb(255, 0, 0)
semi_red = CSS.rgb(255, 0, 0, 0.5)  # with alpha

# HSL
blue = CSS.hsl(240, 100, 50)
muted = CSS.hsl(240, 50, 50, 0.8)

# Modern color spaces (Chrome 111+, Safari 15.4+)
oklch = CSS.oklch(0.7, 0.15, 250)
oklab = CSS.oklab(0.7, 0.1, 0.1)

# Named colors
coral = CSS.color("coral")

# Hex
purple = CSS.hex("#800080")
```

### Color Manipulation

```python
from pynext.client import CSS

base = CSS.rgb(100, 150, 200)

# Lightness
lighter = base.lighten(20)   # 20% lighter
darker = base.darken(20)     # 20% darker

# Saturation
vivid = base.saturate(20)    # more vivid
muted = base.desaturate(20)  # more muted

# Hue rotation
complement = base.rotate(180)  # opposite color

# Alpha
transparent = base.setAlpha(0.5)
more_visible = base.fadeIn(0.2)
less_visible = base.fadeOut(0.2)

# Mix colors
red = CSS.rgb(255, 0, 0)
blue = CSS.rgb(0, 0, 255)
purple = red.mix(blue, 0.5)  # 50% each
mostly_red = red.mix(blue, 0.25)  # 75% red

# Contrast selection
bg = CSS.rgb(200, 200, 200)
white = CSS.rgb(255, 255, 255)
black = CSS.rgb(0, 0, 0)
text = bg.contrast(white, black)  # auto-select
```

### Color Conversion

```python
from pynext.client import CSS

color = CSS.rgb(255, 128, 0)

# Convert between spaces
hsl = color.toHSL()
oklch = color.toOKLCH()
hex_str = color.toHex()

# Introspection
lum = color.luminance()
is_light = color.isLight()
is_dark = color.isDark()
```

---

## Real-World Examples

### Dynamic Theme System

```python
from pynext.client import document, CSS

def apply_theme(dark_mode: bool):
    root = document.documentElement.attributeStyleMap
    
    if dark_mode:
        root.set("--bg", CSS.rgb(15, 23, 42))
        root.set("--fg", CSS.rgb(241, 245, 249))
        root.set("--primary", CSS.oklch(0.7, 0.15, 250))
    else:
        root.set("--bg", CSS.rgb(255, 255, 255))
        root.set("--fg", CSS.rgb(26, 26, 26))
        root.set("--primary", CSS.oklch(0.6, 0.2, 250))

# Toggle on button click
def toggle_theme(e):
    is_dark = document.body.classList.contains("dark")
    apply_theme(not is_dark)
    document.body.classList.toggle("dark")

btn = document.getElementById("theme-toggle")
btn.addEventListener("click", toggle_theme)
```

### Responsive Component Sizing

```python
from pynext.client import document, CSS

def style_card(card, size: str):
    style_map = card.attributeStyleMap
    
    sizes = {
        "sm": {"padding": CSS.rem(1), "radius": CSS.px(4)},
        "md": {"padding": CSS.rem(1.5), "radius": CSS.px(8)},
        "lg": {"padding": CSS.rem(2), "radius": CSS.px(12)},
    }
    
    config = sizes.get(size, sizes["md"])
    style_map.set("padding", config["padding"])
    style_map.set("border-radius", config["radius"])

card = document.getElementById("my-card")
style_card(card, "lg")
```

### Animation with Typed Transforms

```python
from pynext.client import document, CSS, CSSTransformValue

def animate_entrance(el):
    style_map = el.attributeStyleMap
    
    # Start state: off-screen and small
    initial = CSSTransformValue([
        CSS.translateY(CSS.px(20)),
        CSS.scale(0.95),
    ])
    style_map.set("transform", initial)
    style_map.set("opacity", CSS.number(0))
    
    # Animate using Web Animations API
    el.animate([
        {"transform": "translateY(20px) scale(0.95)", "opacity": "0"},
        {"transform": "translateY(0) scale(1)", "opacity": "1"},
    ], duration=300, easing="ease-out", fill="forwards")

modal = document.getElementById("modal")
animate_entrance(modal)
```

### Progress Bar

```python
from pynext.client import document, CSS

def update_progress(bar, percent: float):
    style_map = bar.attributeStyleMap
    
    # Clamp between 0 and 100
    clamped = max(0, min(100, percent))
    style_map.set("width", CSS.percent(clamped))
    
    # Color changes based on progress
    if percent < 30:
        color = CSS.rgb(239, 68, 68)   # red
    elif percent < 70:
        color = CSS.rgb(234, 179, 8)   # yellow
    else:
        color = CSS.rgb(34, 197, 94)   # green
    
    style_map.set("background-color", color)

progress = document.getElementById("progress-fill")
update_progress(progress, 75)
```

---

## Transpilation

All CSS Typed OM code transpiles 1:1 to JavaScript:

```python
# Python
width = CSS.px(100)
el.attributeStyleMap.set("width", width)
```

```javascript
// JavaScript (identical)
const width = CSS.px(100);
el.attributeStyleMap.set("width", width);
```

See [TRANSPILATION_TYPED_OM.md](../internals/TRANSPILATION_TYPED_OM.md) for details on how transpilation works.

---

## Fallback Patterns

For browsers without full CSS Typed OM support:

```python
from pynext.client import document, CSS

def set_width(el, value):
    # Try typed OM first
    if hasattr(el, "attributeStyleMap"):
        el.attributeStyleMap.set("width", CSS.px(value))
    else:
        # Fallback to string
        el.style.width = f"{value}px"
```

Or use feature detection:

```python
from pynext.client import CSS, window

has_typed_om = hasattr(window, "CSS") and hasattr(CSS, "px")
```

---

## Modern CSS Units (Phase 34.3.1)

CSS Level 4 introduces powerful new units for responsive design.

### Dynamic Viewport Units

Account for mobile browser UI (address bar, toolbar):

```python
from pynext.client import CSS

# Small viewport (UI fully visible)
# Safest for mobile - won't be covered by browser UI
height = CSS.svh(100)
width = CSS.svw(100)

# Large viewport (UI hidden)
# Maximum size when user scrolls and browser UI hides
height = CSS.lvh(100)
width = CSS.lvw(100)

# Dynamic viewport (adapts in real-time)
# Smoothly transitions as browser UI appears/disappears
height = CSS.dvh(100)
width = CSS.dvw(100)
```

**When to use which:**
- `svh/svw`: Safe layouts that must never be covered by mobile UI
- `lvh/lvw`: Full-screen experiences when browser UI is hidden
- `dvh/dvw`: Smooth transitions, hero sections that adapt

### Container Query Units

Size relative to a query container, not the viewport:

```python
from pynext.client import CSS

# Width/height relative to container
card_width = CSS.cqw(50)   # 50% of container width
card_height = CSS.cqh(25)  # 25% of container height

# Writing-mode aware (for internationalization)
inline_size = CSS.cqi(100)  # Container inline size
block_size = CSS.cqb(100)   # Container block size

# Min/max of container dimensions
square_size = CSS.cqmin(50)  # Based on smaller dimension
fill_size = CSS.cqmax(100)   # Based on larger dimension
```

**Use case**: Components that adapt to their container size rather than viewport:

```python
# Card that works anywhere - sidebar, main content, modal
el.attributeStyleMap.set("width", CSS.cqw(100))
el.attributeStyleMap.set("font-size", CSS.cqi(4))  # Scales with container
```

### Typography Units

Precise font-relative sizing:

```python
from pynext.client import CSS

# Cap height - height of capital letters
icon_height = CSS.cap(1)  # Icon matches capital letter height

# Ideographic character - uniform CJK character width
column_width = CSS.ic(20)  # Width for 20 CJK characters

# Line height - relative to element's line-height
spacing = CSS.lh(1)   # One line of text

# Root line height - relative to html element's line-height
gap = CSS.rlh(2)      # Two root line-heights (like rem but for line-height)
```

### Browser Support

| Feature | Chrome | Safari | Firefox |
|---------|--------|--------|---------|
| Dynamic viewport (svh/lvh/dvh) | 108+ | 15.4+ | 101+ |
| Container queries (cqw/cqh) | 105+ | 16+ | 110+ |
| Typography (cap/ic/lh/rlh) | 77+ | 13+ | 96+ |

All modern browsers support these units. For older browsers, use traditional `vh`/`vw` as fallback.
