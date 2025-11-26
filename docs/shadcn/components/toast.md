# Toast

Non-blocking notifications that appear temporarily. Built in a Sonner-style API.

## Installation

```python
from pynext.shadcn import Toaster, toast
```

## Setup

Add the Toaster component once to your layout:

```python
@layout
def root_layout(children):
    return html()[
        body()[
            children,
            Toaster(),  # Add at the end of body
        ]
    ]
```

## Basic Usage

```python
# Simple toast
toast("Event has been created")

# With description
toast("File uploaded", description="Your file has been saved.")

# Variants
toast.success("Profile saved successfully")
toast.error("Something went wrong")
toast.warning("Please check your input")
toast.info("New update available")
```

## Examples

### With Custom Duration

```python
# 5 seconds
toast("Custom duration", duration=5000)

# Persistent (0 = no auto-dismiss)
toast("Sticky toast", duration=0)
```

### With Action

```python
toast(
    "File deleted",
    action=("Undo", undo_handler)
)
```

### Promise Toast

```python
# Shows loading → success/error based on promise result
toast.promise(
    save_data(),
    loading="Saving...",
    success="Saved successfully!",
    error="Failed to save"
)
```

### Positioning

```python
# Available positions
Toaster(position="bottom-right")  # default
Toaster(position="bottom-left")
Toaster(position="bottom-center")
Toaster(position="top-right")
Toaster(position="top-left")
Toaster(position="top-center")
```

### Styling Options

```python
Toaster(
    rich_colors=True,      # Colored backgrounds for variants
    expand=True,           # Expand on hover
    max_visible=3,         # Max toasts shown
    close_button=True,     # Show close button
)
```

## API Reference

### Toaster

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `position` | `string` | `"bottom-right"` | Where toasts appear |
| `max_visible` | `int` | `3` | Max toasts shown at once |
| `duration` | `int` | `4000` | Default auto-dismiss (ms) |
| `close_button` | `bool` | `True` | Show close button |
| `rich_colors` | `bool` | `True` | Use colored backgrounds |
| `expand` | `bool` | `True` | Expand on hover |

### toast()

```python
toast(
    message: str,
    description: str = None,
    duration: int = 4000,
    action: tuple[str, Callable] = None,
)
```

### toast.success/error/warning/info()

```python
toast.success(message, description=None, duration=4000)
toast.error(message, description=None, duration=4000)
toast.warning(message, description=None, duration=4000)
toast.info(message, description=None, duration=4000)
```

### toast.promise()

```python
toast.promise(
    promise,
    loading="Loading...",
    success="Success",
    error="Error",
)
```

### toast.dismiss()

```python
# Dismiss specific toast
toast.dismiss(toast_id)

# Dismiss all toasts
toast.dismiss()
```

## Integration with Server Actions

Toasts work seamlessly with server actions:

```python
@server_action
async def create_item(form_data):
    try:
        result = await db.create(form_data)
        return {"success": True, "toast": toast.success("Item created")}
    except Exception as e:
        return {"success": False, "toast": toast.error(str(e))}
```

