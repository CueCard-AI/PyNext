# PyNext Reactive Cheatsheet

> Internal reference for PyNext's reactive system. Written for Python developers who aren't frontend experts.

---

## The Mental Model

Think of PyNext reactivity like a **spreadsheet**:

- **Signals** are cells with values (like cell `A1 = 5`)
- **Memos** are computed cells (like `B1 = A1 * 2` - automatically updates when A1 changes)
- **Effects** are side-effects that run when cells change (like "send email when B1 > 100")

The magic: **you change a signal once, and everything that depends on it updates automatically** - in the browser, without a page refresh.

---

## Core Primitives (Python Side)

### Signal - A reactive value

```python
from pynext.reactive import Signal

count = Signal(0)           # Create with initial value
count()                     # Read: returns 0
count.set(5)                # Write: now it's 5
count.set(count() + 1)      # Increment: now it's 6
```

**What happens:** The value lives on both server AND client. When you change it client-side, the DOM updates automatically.

### Memo - A computed value

```python
from pynext.reactive import Memo

items = Signal([1, 2, 3])
total = Memo(lambda: sum(items()))   # Computed from items

total()  # Returns 6
items.set([1, 2, 3, 4])              # Change source
total()  # Automatically returns 10
```

**What happens:** PyNext transpiles the lambda to JavaScript. When `items` changes, `total` recomputes automatically.

### Effect - Side effects on change

```python
from pynext.reactive import effect

@effect
def log_count():
    print(f"Count is now: {count()}")
```

**What happens:** Runs once immediately, then re-runs whenever any signal it reads changes.

---

## Reactive Data Attributes (HTML Side)

These are special `data_pynext_*` attributes you put on HTML elements. PyNext's JavaScript runtime reads them and wires up the reactivity.

### 1. Text Binding: `data_pynext_text`

**Purpose:** Automatically update element's text when a signal/memo changes.

```python
span(data_pynext_text="total_count")[total_count()]
```

**Plain English:** "This span's text should always match the `total_count` signal."

**Result:** When `total_count` changes from 5 to 6, the span updates from "5" to "6" automatically.

---

### 2. Toggle Bindings: `data_pynext_toggle_*`

**Purpose:** Change an element's styles based on a signal's value. Used for tabs, buttons, show/hide, etc.

| Attribute | What it does |
|-----------|--------------|
| `data_pynext_toggle_signal` | Which signal to watch |
| `data_pynext_toggle_value` | Value to compare against (for equality checks) |
| `data_pynext_toggle_op` | How to compare (see operations below) |
| `data_pynext_toggle_active` | CSS to apply when condition is TRUE |
| `data_pynext_toggle_inactive` | CSS to apply when condition is FALSE |

#### Toggle Operations (`data_pynext_toggle_op`)

| Operation | Meaning | Example use case |
|-----------|---------|------------------|
| `eq` (default) | Signal equals value | Tab is selected |
| `neq` | Signal doesn't equal value | Tab is NOT selected |
| `truthy` | Signal is truthy (not 0, "", null, false) | Checkbox is checked |
| `falsy` | Signal is falsy | Checkbox is unchecked |
| `gt`, `gte`, `lt`, `lte` | Greater/less than | Progress bar thresholds |
| `includes` | String contains value | Search filtering |
| `startsWith`, `endsWith` | String matching | Autocomplete |

#### Example: Filter Button (Active/Inactive Styling)

```python
button(
    onclick=lambda: filter_status.set("todo"),
    data_pynext_toggle_signal="filter_status",
    data_pynext_toggle_value="todo",
    data_pynext_toggle_active="border-color: #5046e5; background: #eef2ff;",
    data_pynext_toggle_inactive="border-color: #d1d5db; background: white;",
)["Todo"]
```

**Plain English:** "Watch the `filter_status` signal. When it equals `'todo'`, apply the active styles. Otherwise, apply the inactive styles."

#### Example: Expand/Collapse (Show/Hide)

```python
div(
    data_pynext_toggle_signal="issue_1_expanded",
    data_pynext_toggle_op="truthy",
    data_pynext_toggle_active="display: block;",
    data_pynext_toggle_inactive="display: none;",
)[...]
```

**Plain English:** "Watch `issue_1_expanded`. If it's truthy (True, 1, etc.), show this div. Otherwise, hide it."

#### Example: Rotate Arrow on Expand

```python
button(
    onclick=lambda: expanded.set(not expanded()),
    data_pynext_toggle_signal="issue_1_expanded",
    data_pynext_toggle_op="truthy",
    data_pynext_toggle_active="transform: rotate(90deg);",
    data_pynext_toggle_inactive="transform: rotate(0deg);",
)["▶"]
```

**Plain English:** "When expanded, rotate the arrow 90° (pointing down). When collapsed, point right."

---

### 3. Field Bindings: `data_pynext_field_*`

**Purpose:** Bind element content to a field in a data item. Used inside `For` loops.

| Attribute | What it does |
|-----------|--------------|
| `data_pynext_field` | Field name to display as text content |
| `data_pynext_field_map` | Transform values (JSON: `{"raw":"Display"}`) |
| `data_pynext_style_map` | Apply styles based on value (JSON) |

#### Example: Display Issue Title

```python
span(data_pynext_field="title")[issue["title"]]
```

**Plain English:** "Show the `title` field. When the item updates, update this text."

#### Example: Priority Emoji Mapping

```python
span(
    data_pynext_field="priority",
    data_pynext_field_map='{"low":"🟢","medium":"🟡","high":"🟠","urgent":"🔴"}',
)[priority_emoji]
```

**Plain English:** "Show the `priority` field, but transform `'low'` → `'🟢'`, `'medium'` → `'🟡'`, etc."

#### Example: Status Badge with Dynamic Color

```python
span(
    data_pynext_field="status",
    data_pynext_field_map='{"todo":"Todo","in_progress":"In Progress","done":"Done"}',
    data_pynext_style_map='{"todo":{"background":"#3b82f6"},"in_progress":{"background":"#f59e0b"},"done":{"background":"#10b981"}}',
)[status_label]
```

**Plain English:** "Show status as a label, AND change the background color based on the value."

---

### 4. Action Bindings: `data_pynext_action_*`

**Purpose:** Declarative mutations on arrays (delete, update). Click-to-delete without writing handlers.

| Attribute | What it does |
|-----------|--------------|
| `data_pynext_action` | Action type: `"delete"`, `"update"` |
| `data_pynext_action_signal` | Signal containing the array |
| `data_pynext_action_key` | Field to match on (usually `"id"`) |
| `data_pynext_action_value` | Value to match |

#### Example: Delete Button

```python
button(
    data_pynext_action="delete",
    data_pynext_action_signal="all_issues",
    data_pynext_action_key="id",
    data_pynext_action_value=str(issue_id),
)["🗑️"]
```

**Plain English:** "When clicked, remove the item from `all_issues` where `id` equals this value."

**No onclick needed!** The runtime wires it up automatically.

---

### 5. Event Bindings: `data_pynext_on_*`

**Purpose:** Attach event handlers that survive DOM updates.

| Attribute | What it does |
|-----------|--------------|
| `data_pynext_on_click` | JavaScript to run on click |
| `data_pynext_on_change` | JavaScript to run on change |
| `data_pynext_on_submit` | JavaScript to run on form submit |
| `data_pynext_mods_*` | Event modifiers (prevent, stop, etc.) |

#### Example: Toggle Signal on Click

```python
button(
    data_pynext_on_click='return __pynext__.getSignal("expanded").set(!__pynext__.getSignal("expanded").read());'
)["Toggle"]
```

**Why use this instead of `onclick`?** When items are added/removed in a `For` loop, the DOM nodes get cloned/reused. Regular `onclick` handlers get lost. `data_pynext_on_click` survives because it's re-attached from the attribute.

---

### 6. Attribute/Style Bindings: `data_pynext_attr_*` / `data_pynext_style_*`

**Purpose:** Bind any attribute or style property to a data field.

```python
# Bind href to item's url field
a(data_pynext_attr_href="url")["Link"]

# Bind background-color to item's color field
div(data_pynext_style_background="color")[...]
```

---

## How It All Flows

```
┌─────────────────────────────────────────────────────────────┐
│  PYTHON (Server)                                            │
│                                                             │
│  1. You define Signals, Memos, Effects                      │
│  2. PyNext renders HTML with data_pynext_* attributes       │
│  3. Signal values are serialized as JSON in the HTML        │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTML sent to browser
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  JAVASCRIPT (Browser)                                       │
│                                                             │
│  1. signals.js hydrates: recreates signals from JSON        │
│  2. Finds all data_pynext_* elements                        │
│  3. Wires up subscriptions (effects)                        │
│  4. When signal changes → DOM updates automatically         │
└─────────────────────────────────────────────────────────────┘
```

---

## Common Patterns

### Pattern 1: Counter with Live Display

```python
count = Signal(0)

div()[
    button(onclick=lambda: count.set(count() + 1))["+"],
    span(data_pynext_text="count")[count()],
    button(onclick=lambda: count.set(count() - 1))["-"],
]
```

### Pattern 2: Filtered List

```python
filter_status = Signal("all")
all_issues = Signal([...])

# Filter button
button(
    onclick=lambda: filter_status.set("todo"),
    data_pynext_toggle_signal="filter_status",
    data_pynext_toggle_value="todo",
    data_pynext_toggle_active="background: blue;",
    data_pynext_toggle_inactive="background: gray;",
)["Todo"]

# List that filters based on signal
For(
    items=all_issues,
    filter_fn=lambda i: filter_status() == "all" or i["status"] == filter_status()
)[...]
```

### Pattern 3: Expandable Section

```python
expanded = Signal(False, name=f"section_{id}_expanded")

div()[
    button(
        onclick=lambda: expanded.set(not expanded()),
        data_pynext_toggle_signal=f"section_{id}_expanded",
        data_pynext_toggle_op="truthy",
        data_pynext_toggle_active="transform: rotate(90deg);",
        data_pynext_toggle_inactive="transform: rotate(0deg);",
    )["▶"],
    div(
        data_pynext_toggle_signal=f"section_{id}_expanded",
        data_pynext_toggle_op="truthy",
        data_pynext_toggle_active="display: block;",
        data_pynext_toggle_inactive="display: none;",
    )["Hidden content here"]
]
```

---

## Debugging Tips

1. **Check browser console** for `[PyNext]` prefixed logs
2. **Inspect elements** and look for `data-pynext-*` attributes
3. **Test signals manually** in console: `__pynext__.getSignal("name").read()` and `.set(value)`
4. **Look for `data-pynext-toggle-initialized="true"`** to confirm binding was set up

---

## Quick Reference Table

| Want to... | Use this |
|------------|----------|
| Display a signal's value | `data_pynext_text="signal_name"` |
| Style based on signal value | `data_pynext_toggle_*` attributes |
| Show/hide based on boolean | `toggle_op="truthy"` + `display: block/none` |
| Highlight active tab/button | `toggle_value="tab_name"` + active/inactive styles |
| Display item field in For loop | `data_pynext_field="field_name"` |
| Transform field values | `data_pynext_field_map='{"raw":"display"}'` |
| Delete from array on click | `data_pynext_action="delete"` |
| Attach handler that survives DOM updates | `data_pynext_on_click="..."` |

---

*Last updated: December 2024*
