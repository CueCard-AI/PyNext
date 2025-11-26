# Toggle

A button that can be pressed on or off.

## When to Use

Toggles are for:
- **Formatting tools** - Bold, italic, underline
- **View options** - Grid/list, show/hide
- **Editor actions** - Preview mode, fullscreen
- **Feature toggles** - Enable specific features

## Installation

```bash
pynext ui add toggle
```

Or use directly:

```python
from pynext.shadcn import Toggle, ToggleGroup
```

## Basic Usage

```python
Toggle()["B"]  # Bold toggle
```

With pressed state:

```python
Toggle(pressed=True)["B"]
```

## Variants

```python
Toggle(variant="default")["Default"]
Toggle(variant="outline")["Outline"]
```

## Examples

### Text Formatting

```python
div(class_="flex gap-1")[
    Toggle(aria_label="Bold")["𝐁"],
    Toggle(aria_label="Italic")["𝐼"],
    Toggle(aria_label="Underline")["U̲"],
]
```

### With Icons

```python
Toggle(aria_label="Toggle grid view")[
    "⊞"  # Grid icon
]
```

### Toggle Group (Single Selection)

```python
ToggleGroup(type="single", default_value="left")[
    Toggle(value="left", aria_label="Left align")["⬅"],
    Toggle(value="center", aria_label="Center align")["⬛"],
    Toggle(value="right", aria_label="Right align")["➡"],
]
```

### Toggle Group (Multiple Selection)

```python
ToggleGroup(type="multiple", default_value=["bold"])[
    Toggle(value="bold", aria_label="Bold")["B"],
    Toggle(value="italic", aria_label="Italic")["I"],
    Toggle(value="underline", aria_label="Underline")["U"],
]
```

### With Signal State

```python
from pynext import Signal

is_bold = Signal(False)

Toggle(
    pressed=is_bold.value,
    on_pressed_change=is_bold.set
)["B"]
```

### Disabled

```python
Toggle(disabled=True)["Disabled"]
```

## Props Reference

### Toggle

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `pressed` | bool | `None` | Controlled pressed state |
| `default_pressed` | bool | `False` | Initial state |
| `on_pressed_change` | callable | `None` | Called on toggle |
| `variant` | str | `"default"` | Visual style |
| `size` | str | `"default"` | Button size |
| `disabled` | bool | `False` | Disable toggle |
| `aria_label` | str | `None` | Accessibility label |

### ToggleGroup

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `type` | str | `"single"` | "single" or "multiple" |
| `value` | str/list | `None` | Controlled value(s) |
| `default_value` | str/list | `None` | Initial value(s) |
| `on_value_change` | callable | `None` | Called on change |

## Accessibility

- Uses `aria-pressed` attribute
- Keyboard focusable
- Space/Enter toggles state
- Always provide `aria_label` for icon-only toggles

## Related Components

- [Button](./button.md) - For one-time actions
- [Switch](./switch.md) - For on/off settings
- [Tabs](./tabs.md) - For content switching

