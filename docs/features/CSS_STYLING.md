# CSS Runtime & Styling (Phase 34.2)

Complete guide to CSS styling in PyNext - from inline styles to animations.

## Overview

PyNext provides comprehensive CSS styling support with:
- **Zero-runtime passthrough** - Direct access to `element.style.*` 
- **Pythonic helpers** - Dictionary-style access, theme management
- **Web Animations API** - Smooth, GPU-accelerated animations

All APIs are fully typed for IDE autocompletion and transpile to efficient JavaScript.

---

## Table of Contents

1. [Inline Styles](#inline-styles)
2. [Dictionary-Style Access](#dictionary-style-access)
3. [CSS Variables](#css-variables)
4. [Computed Styles](#computed-styles)
5. [Class Management](#class-management)
6. [Animations](#animations)
7. [API Reference](#api-reference)

---

## Inline Styles

### Direct Property Access

Access CSS properties directly using camelCase:

```python
from pynext.client import document

el = document.getElementById("box")

# Set properties
el.style.display = "flex"
el.style.backgroundColor = "blue"
el.style.borderRadius = "8px"
el.style.transform = "rotate(45deg)"

# Read properties
current_display = el.style.display
```

### setProperty / getPropertyValue

For kebab-case properties or CSS variables:

```python
# Set with kebab-case
el.style.setProperty("background-color", "red")
el.style.setProperty("--primary-color", "#3b82f6")
el.style.setProperty("display", "none", "important")

# Get values
bg = el.style.getPropertyValue("background-color")
primary = el.style.getPropertyValue("--primary-color")

# Remove
el.style.removeProperty("background-color")
```

---

## Dictionary-Style Access

### StylesProxy

A Pythonic wrapper for more natural style access:

```python
from pynext.client import document
from pynext.client.styles import StylesProxy

el = document.getElementById("card")
styles = StylesProxy(el)

# Set with kebab-case (more Pythonic!)
styles["background-color"] = "red"
styles["border-radius"] = "8px"
styles["--primary"] = "#3b82f6"

# Check and delete
if "display" in styles:
    del styles["display"]

# Bulk update
styles.update({
    "display": "flex",
    "gap": "8px",
    "padding": "16px",
})

# Clear all inline styles
styles.clear()
```

### Iteration

```python
# Iterate over all style properties
for prop in styles:
    print(f"{prop}: {styles[prop]}")

# Get as dictionary
style_dict = styles.to_dict()
```

---

## CSS Variables

### Basic Operations

```python
from pynext.client.css_vars import set_css_var, get_css_var, remove_css_var

# Set on :root (global)
set_css_var("primary-color", "#3b82f6")
set_css_var("spacing", "16px")

# Get computed value
color = get_css_var("primary-color")

# Remove
remove_css_var("temp-color")
```

### Scoped Variables

```python
from pynext.client import document
from pynext.client.css_vars import set_css_var

# Set on specific element
card = document.getElementById("card")
set_css_var("bg-color", "#ffffff", element=card)
```

### Theme Management

```python
from pynext.client.css_vars import set_theme, toggle_theme

# Define themes
light_theme = {
    "bg": "#ffffff",
    "fg": "#1a1a1a",
    "primary": "#3b82f6",
    "secondary": "#64748b",
}

dark_theme = {
    "bg": "#0f172a",
    "fg": "#f1f5f9",
    "primary": "#60a5fa",
    "secondary": "#94a3b8",
}

# Apply a theme
set_theme(light_theme)

# Toggle based on system preference
is_dark = toggle_theme(light_theme, dark_theme)

# Force dark mode
toggle_theme(light_theme, dark_theme, prefer_dark=True)
```

---

## Computed Styles

### window.getComputedStyle

Get the final rendered CSS values:

```python
from pynext.client import window, document

el = document.getElementById("box")
computed = window.getComputedStyle(el)

# Read computed values (includes inheritance, stylesheets)
actual_width = computed.width          # "200px"
actual_bg = computed.backgroundColor   # "rgb(255, 0, 0)"

# Read CSS variable value
primary = computed.getPropertyValue("--primary-color")
```

### Pseudo-Element Styles

```python
from pynext.client import window

# Get ::before styles
before = window.getComputedStyle(el, "::before")
content = before.content

# Get ::after styles  
after = window.getComputedStyle(el, "::after")
```

### Media Queries

```python
from pynext.client import window

# Check responsive breakpoints
is_mobile = window.matchMedia("(max-width: 768px)").matches

# System preferences
prefers_dark = window.matchMedia("(prefers-color-scheme: dark)").matches
prefers_reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches

# Listen for changes
mql = window.matchMedia("(max-width: 768px)")

def on_change(event):
    if event.matches:
        print("Now mobile")
        
mql.addEventListener("change", on_change)
```

---

## Class Management

### classList API

```python
from pynext.client import document

el = document.getElementById("card")

# Add classes
el.classList.add("active")
el.classList.add("shadow", "rounded", "hover:scale-105")

# Remove classes
el.classList.remove("hidden")
el.classList.remove("old", "unused")

# Toggle
el.classList.toggle("visible")
el.classList.toggle("active", is_selected)  # Force based on condition

# Check
if el.classList.contains("active"):
    print("Element is active")

# Replace
el.classList.replace("loading", "loaded")
```

### classes() Helper

Conditional class builder (like clsx/classnames):

```python
from pynext.client.style_utils import classes

# Basic usage
cls = classes("btn", "primary")  # "btn primary"

# Conditional with tuple
cls = classes("btn", ("active", is_active))

# Dictionary style
cls = classes("btn", {"error": has_error, "success": is_success})

# Mixed (common pattern)
el.className = classes(
    "card",
    "shadow-lg",
    "rounded-xl",
    ("ring-2 ring-blue-500", is_focused),
    ("opacity-50 pointer-events-none", is_disabled),
    {
        "bg-white": theme == "light",
        "bg-slate-800": theme == "dark",
    },
)
```

### Helper Functions

```python
from pynext.client.style_utils import (
    toggle_class, add_classes, remove_classes, 
    has_class, replace_class
)

# Toggle based on condition
toggle_class(el, "active", is_selected)

# Add/remove multiple
add_classes(el, "card", "shadow", "rounded")
remove_classes(el, "hidden", "disabled")

# Check
if has_class(el, "active"):
    pass

# Replace
replace_class(el, "loading", "loaded")
```

---

## Animations

### element.animate() - Web Animations API

```python
from pynext.client import document

el = document.getElementById("box")

# Basic animation
anim = el.animate([
    {"opacity": "0"},
    {"opacity": "1"},
], duration=300)

await anim.finished  # Wait for completion

# Full options
anim = el.animate([
    {"transform": "scale(0.9)", "opacity": "0"},
    {"transform": "scale(1)", "opacity": "1"},
], 
    duration=300,
    easing="ease-out",
    fill="forwards",  # Keep end state
    delay=100,
    iterations=1,
)
```

### Animation Control

```python
anim = el.animate([...], duration=1000)

# Playback control
anim.pause()
anim.play()
anim.reverse()
anim.cancel()
anim.finish()  # Jump to end

# Speed control
anim.playbackRate = 2.0  # 2x speed
anim.playbackRate = 0.5  # Half speed
anim.playbackRate = -1   # Reverse

# Seek
anim.currentTime = 500  # Jump to 500ms

# State
print(anim.playState)  # "running", "paused", "finished"
```

### Animation Helpers

Convenience functions for common patterns:

```python
from pynext.client.animation import (
    fade_in, fade_out,
    slide_in, slide_out,
    scale_in, scale_out,
    shake, pulse,
)

# Fade
await fade_in(el)
await fade_out(el, duration=500)

# Slide
await slide_in(modal, direction="bottom")
await slide_out(drawer, direction="left")

# Scale (pop effect)
await scale_in(tooltip)
await scale_out(dialog)

# Feedback
await shake(input_field)  # Error indication
await pulse(button)       # Click feedback
```

---

## API Reference

### pynext.client.styles

| Function/Class | Description |
|----------------|-------------|
| `StylesProxy(element)` | Dictionary-style style access |
| `create_styles(element)` | Factory for StylesProxy |

### pynext.client.css_vars

| Function | Description |
|----------|-------------|
| `set_css_var(name, value, element=None)` | Set CSS variable |
| `get_css_var(name, element=None)` | Get CSS variable value |
| `remove_css_var(name, element=None)` | Remove CSS variable |
| `set_theme(variables, element=None)` | Set multiple variables |
| `get_theme(names, element=None)` | Get multiple variables |
| `toggle_theme(light, dark, prefer_dark=None)` | Switch themes |

### pynext.client.style_utils

| Function | Description |
|----------|-------------|
| `classes(*args)` | Conditional class builder |
| `set_styles(element, styles)` | Bulk style update |
| `toggle_class(element, class_name, condition)` | Conditional toggle |
| `add_classes(element, *classes)` | Add multiple classes |
| `remove_classes(element, *classes)` | Remove multiple classes |
| `has_class(element, class_name)` | Check class presence |
| `replace_class(element, old, new)` | Replace class |
| `clear_styles(element)` | Clear all inline styles |

### pynext.client.animation

| Function/Class | Description |
|----------------|-------------|
| `Animation` | Web Animations API object |
| `fade_in(el, duration=300)` | Fade in animation |
| `fade_out(el, duration=300)` | Fade out animation |
| `slide_in(el, direction="bottom")` | Slide in animation |
| `slide_out(el, direction="bottom")` | Slide out animation |
| `scale_in(el, from_scale=0.9)` | Scale in animation |
| `scale_out(el, to_scale=0.9)` | Scale out animation |
| `shake(el, intensity="10px")` | Shake animation |
| `pulse(el, scale=1.05)` | Pulse animation |

### pynext.client.window

| Property/Method | Description |
|-----------------|-------------|
| `window.getComputedStyle(el, pseudo=None)` | Get computed styles |
| `window.matchMedia(query)` | Check media query |
| `window.innerWidth` | Viewport width |
| `window.innerHeight` | Viewport height |

---

## Best Practices

1. **Use CSS variables for theming** - Easier to maintain and switch
2. **Prefer classList over className** - More efficient for single class changes
3. **Use getComputedStyle sparingly** - Can be expensive, cache results
4. **Await animations** - Ensure proper sequencing with `await anim.finished`
5. **Check prefers-reduced-motion** - Respect user accessibility preferences

```python
# Good: Check for reduced motion preference
if window.matchMedia("(prefers-reduced-motion: reduce)").matches:
    el.style.opacity = "1"  # Instant change
else:
    await fade_in(el)  # Animated
```

