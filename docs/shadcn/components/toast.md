# Toast

> **Like a notification that pops up briefly — "Hey, that worked!" and disappears**

A non-blocking notification that appears temporarily to provide feedback.

---

## First Principles: What IS a Toast?

### The Core Concept

A toast is a **brief, non-intrusive message** that appears and auto-dismisses:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         THE TOAST CONCEPT                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  User clicks "Save"                                                          │
│       ↓                                                                      │
│  Action happens (save to database)                                           │
│       ↓                                                                      │
│  Toast appears:                                                              │
│                                                                              │
│  ┌─────────────────────────────────────────────────────┐                    │
│  │                                      ┌────────────┐ │                    │
│  │  Your page                           │ ✓ Saved!   │ │ ← Toast           │
│  │  content                             └────────────┘ │                    │
│  │  here                                               │                    │
│  │                                                     │                    │
│  └─────────────────────────────────────────────────────┘                    │
│       ↓                                                                      │
│  After 3 seconds, toast fades away                                           │
│       ↓                                                                      │
│  User continues working (never interrupted!)                                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Toast vs Other Feedback

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         WHEN TO USE WHAT                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  TOAST:                            ALERT/DIALOG:                             │
│  ──────                            ────────────                              │
│  • Success confirmations           • Errors requiring action                 │
│  • Background task updates         • Confirmations ("Delete?")               │
│  • Non-critical info               • Critical information                    │
│  • Auto-dismisses                  • Requires user response                  │
│                                                                              │
│  Examples:                         Examples:                                 │
│  "Email sent ✓"                    "Are you sure you want to delete?"       │
│  "Settings saved"                  "Session expired. Please log in."        │
│  "Item added to cart"              "Payment failed. Please retry."          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## How It Works

### Toast Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TOAST LIFECYCLE                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. TRIGGER                                                                  │
│     toast.success("Saved!")                                                  │
│                                                                              │
│  2. APPEAR                                                                   │
│     Toast slides in from corner                                              │
│     Animation: opacity 0→1, translate                                        │
│                                                                              │
│  3. DISPLAY                                                                  │
│     Toast is visible for duration (default: 3-5s)                            │
│     User can hover to pause timer                                            │
│     User can click to dismiss early                                          │
│                                                                              │
│  4. DISAPPEAR                                                                │
│     Toast slides out                                                         │
│     Animation: opacity 1→0, translate                                        │
│                                                                              │
│  5. QUEUE NEXT                                                               │
│     If more toasts waiting, show next                                        │
│     Or container becomes empty                                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Installation

```bash
pynext ui add toast
```

Or import directly:

```python
from pynext.shadcn import Toaster, toast
```

---

## Step-by-Step Usage

### Step 1: Add Toaster to Layout

Add the Toaster component to your root layout (once per app):

```python
# layouts/root.py
def RootLayout(children):
    return html()[
        head()[...],
        body()[
            children,
            Toaster()  # Add this at the end
        ]
    ]
```

### Step 2: Trigger Toasts

```python
from pynext.shadcn import toast

# Success toast
Button(on_click=lambda: toast.success("Saved successfully!"))[
    "Save"
]

# Error toast
Button(on_click=lambda: toast.error("Something went wrong"))[
    "Error Demo"
]

# Info toast
Button(on_click=lambda: toast.info("New update available"))[
    "Info Demo"
]

# Warning toast
Button(on_click=lambda: toast.warning("Your session will expire soon"))[
    "Warning Demo"
]
```

### Step 3: With Server Actions

```python
from pynext import server_action
from pynext.shadcn import toast

@server_action
async def save_data(data: dict):
    try:
        await db.save(data)
        toast.success("Data saved!")
        return {"success": True}
    except Exception as e:
        toast.error(f"Error: {str(e)}")
        return {"success": False}

Button(on_click=lambda: save_data(form_data))["Save"]
```

---

## Toast Types

### Success

```python
toast.success("Successfully saved!")

# With title
toast.success("Changes saved", description="Your profile has been updated.")
```

### Error

```python
toast.error("Failed to save")

# With action
toast.error(
    "Could not save",
    description="Please try again.",
    action=Button(on_click=retry)["Retry"]
)
```

### Warning

```python
toast.warning("Unsaved changes")
```

### Info

```python
toast.info("New feature available!")
```

### Loading

```python
# Show loading, then update
t = toast.loading("Saving...")

# After operation completes
toast.success("Saved!", id=t)  # Replace loading toast
```

### Promise

```python
# Automatically shows loading → success/error
toast.promise(
    save_async(),
    loading="Saving...",
    success="Saved!",
    error="Failed to save"
)
```

---

## Common Patterns

### Pattern 1: Undo Action

```python
def delete_item(id):
    # Remove from UI immediately
    items.set([i for i in items.value if i.id != id])
    
    # Show toast with undo
    toast.success(
        "Item deleted",
        action=Button(variant="outline", on_click=lambda: undo_delete(id))[
            "Undo"
        ],
        duration=10000  # Longer duration for undo
    )
```

### Pattern 2: Form Validation Errors

```python
@server_action
async def submit_form(data: dict):
    errors = validate(data)
    
    if errors:
        for error in errors:
            toast.error(error)
        return {"success": False}
    
    await save(data)
    toast.success("Form submitted!")
    return {"success": True}
```

### Pattern 3: Upload Progress

```python
async def upload_file(file):
    t = toast.loading(f"Uploading {file.name}...")
    
    try:
        await api.upload(file)
        toast.success(f"{file.name} uploaded!", id=t)
    except Exception as e:
        toast.error(f"Failed to upload {file.name}", id=t)
```

### Pattern 4: Multiple Toasts

```python
def process_items(items):
    for item in items:
        try:
            process(item)
            toast.success(f"Processed {item.name}")
        except:
            toast.error(f"Failed: {item.name}")
```

---

## Configuration

### Toaster Props

```python
Toaster(
    position="bottom-right",  # Position on screen
    duration=5000,            # Default duration (ms)
    expand=True,              # Expand toasts on hover
    rich_colors=True,         # Use semantic colors
    close_button=True,        # Show close button
)
```

### Positions

```python
# Corners
Toaster(position="top-left")
Toaster(position="top-right")
Toaster(position="bottom-left")
Toaster(position="bottom-right")  # Default

# Centered
Toaster(position="top-center")
Toaster(position="bottom-center")
```

---

## API Reference

### toast()

| Method | Description |
|--------|-------------|
| `toast(message)` | Default toast |
| `toast.success(message)` | Success toast (green) |
| `toast.error(message)` | Error toast (red) |
| `toast.warning(message)` | Warning toast (yellow) |
| `toast.info(message)` | Info toast (blue) |
| `toast.loading(message)` | Loading toast (spinner) |
| `toast.promise(promise, ...)` | Promise-based toast |
| `toast.dismiss(id)` | Dismiss specific toast |
| `toast.dismiss()` | Dismiss all toasts |

### Toast Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `description` | str | `None` | Additional detail text |
| `duration` | int | `5000` | Time to display (ms) |
| `action` | Component | `None` | Action button |
| `id` | str | `None` | Unique ID (for updating) |
| `dismissible` | bool | `True` | Can be dismissed |

---

## Accessibility

| Feature | Implementation |
|---------|----------------|
| **ARIA Role** | `role="alert"` for errors, `role="status"` for others |
| **Live Region** | `aria-live="polite"` or `"assertive"` |
| **Keyboard** | Escape to dismiss, Tab to action |
| **Reduced Motion** | Respects `prefers-reduced-motion` |

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Toast not showing | Missing Toaster | Add `<Toaster/>` to layout |
| Multiple toasts stacking | Expected behavior | Use `toast.dismiss()` if needed |
| Toast not dismissing | `dismissible=False` | Set `dismissible=True` |
| Action not working | Missing handler | Add `on_click` to action button |

---

## Related Components

- **[Alert](./alert.md)** — Persistent in-page alerts
- **[Dialog](./dialog.md)** — For confirmations requiring response
