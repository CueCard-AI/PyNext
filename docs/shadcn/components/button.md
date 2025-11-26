# Button

Displays a button or a component that looks like a button.

## When to Use

Buttons are the primary way users take action in your app. Use them for:

- **Form submissions** — "Submit", "Save", "Create"
- **Confirmations** — "Confirm", "Accept", "Agree"
- **Navigation actions** — "Next", "Continue", "Go Back"
- **Destructive actions** — "Delete", "Remove", "Cancel"

**Don't use buttons for navigation links.** Use `<a>` tags or the Link component instead. Buttons are for actions, links are for navigation.

---

## Installation

To add the Button component to your project (so you can customize it):

```bash
pynext ui add button
```

This copies the button code into `components/ui/button.py`. You can then edit the styles, add variants, or modify the behavior to match your design system.

**Or use it directly** without copying (if you don't need to customize):

```python
from pynext.shadcn import Button
```

---

## Basic Usage

The simplest button just wraps your text:

```python
from pynext.shadcn import Button

Button()["Click me"]
```

**How it works:** The `[]` syntax passes children to the component — in this case, the text "Click me" becomes the button's label.

---

## Variants

Variants change the visual style of the button to communicate different intents to users.

### Default

The primary action button. Use for the main action on a page.

```python
Button(variant="default")["Save Changes"]
```

### Destructive

For dangerous or irreversible actions. The red color signals caution.

```python
Button(variant="destructive")["Delete Account"]
```

**When to use:** Delete, remove, cancel subscription, revoke access — any action that can't be easily undone.

### Outline

A lighter visual weight. Good for secondary actions that shouldn't compete with the primary button.

```python
Button(variant="outline")["Cancel"]
```

**When to use:** Cancel buttons, "Learn more" links, secondary options.

### Secondary

Similar to outline but with a subtle background. Use when you need something between primary and outline.

```python
Button(variant="secondary")["Save Draft"]
```

### Ghost

Nearly invisible until hovered. Perfect for icon buttons or actions in tight spaces.

```python
Button(variant="ghost")["Edit"]
```

**When to use:** Toolbars, table row actions, icon-only buttons.

### Link

Looks like a text link but behaves like a button. Use sparingly — if it navigates somewhere, use an actual link instead.

```python
Button(variant="link")["Learn more"]
```

---

## Sizes

Size affects both the padding and font size. Choose based on context:

| Size | When to use |
|------|-------------|
| `sm` | Tight spaces, tables, inline actions |
| `default` | Most cases — forms, cards, modals |
| `lg` | Hero sections, prominent CTAs |
| `icon` | Square button for icons only |

```python
Button(size="sm")["Small"]
Button(size="default")["Default"]
Button(size="lg")["Large"]
Button(size="icon")[SearchIcon()]
```

---

## Handling Clicks

Use `on_click` to respond when the user clicks the button:

```python
def handle_save():
    print("Saving...")

Button(on_click=handle_save)["Save"]
```

### With Server Actions

Call Python functions on your server:

```python
from pynext import server_action

@server_action
async def save_to_database(data):
    # This runs on the server!
    await db.save(data)
    return {"success": True}

Button(on_click=lambda: save_to_database(form_data))["Save to Database"]
```

**What's happening here?**

1. User clicks the button
2. PyNext sends a request to your server
3. `save_to_database` runs with full Python access (database, files, etc.)
4. Result is sent back to the browser

---

## Disabled State

Disable buttons to prevent interaction when an action isn't available:

```python
Button(disabled=True)["Submit"]
```

The button will be visually muted and won't respond to clicks.

**Important:** Always explain WHY a button is disabled. Add a tooltip or helper text so users know what they need to do to enable it.

```python
div()[
    Button(disabled=not form_valid)["Submit"],
    not form_valid and span(class_="text-sm text-muted")["Please fill all required fields"]
]
```

---

## As a Link (Polymorphism)

Sometimes you want a button that's actually a link. Use `as_child`:

```python
Button(as_child=True)[
    a(href="/dashboard")["Go to Dashboard"]
]
```

This renders an `<a>` tag with button styling instead of a `<button>`. Useful for:

- Navigation that should look like a button
- External links with button styling
- Download buttons

---

## Props Reference

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `variant` | str | `"default"` | Visual style: `"default"`, `"destructive"`, `"outline"`, `"secondary"`, `"ghost"`, `"link"` |
| `size` | str | `"default"` | Size: `"default"`, `"sm"`, `"lg"`, `"icon"` |
| `disabled` | bool | `False` | Whether the button is disabled |
| `on_click` | callable | `None` | Function to call when clicked |
| `type` | str | `"button"` | HTML button type: `"button"`, `"submit"`, `"reset"` |
| `class_` | str | `None` | Additional CSS classes (merged with defaults) |
| `as_child` | bool | `False` | Merge props onto child element instead of wrapping |

---

## Accessibility

The Button component follows accessibility best practices:

- **Keyboard navigation** — Focusable with Tab, activated with Enter/Space
- **Focus indicator** — Visible focus ring for keyboard users
- **Disabled state** — Properly announced to screen readers
- **Native element** — Uses `<button>` for built-in accessibility

### Tips for Accessible Buttons

1. **Use descriptive labels** — "Save changes" not just "Save"
2. **Don't disable without explanation** — Tell users why
3. **Ensure color contrast** — Especially for destructive variant
4. **Keep text concise** — But meaningful

---

## Related Components

- [Toggle](./toggle.md) — For on/off states
- [Link](./link.md) — For navigation (not actions)

