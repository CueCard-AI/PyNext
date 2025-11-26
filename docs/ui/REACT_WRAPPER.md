# React Wrapper

> **Use existing React components in PyNext when you need them**

PyNext provides a `use_react()` wrapper for integrating React components as islands. This is your escape hatch for complex UI libraries that haven't been ported to PyNext yet.

---

## When to Use This

**Use `use_react()` when:**
- You need a complex React component (data grid, rich text editor, charts)
- A library only exists for React (e.g., `react-beautiful-dnd`)
- You're migrating from React and want to reuse components

**Don't use it when:**
- A PyNext native component exists (prefer `pynext.shadcn`)
- The component is simple enough to build in Python
- You want to avoid JavaScript entirely

---

## Quick Start

```python
from pynext.react import use_react

# 1. Create a wrapper for the React component
DatePicker = use_react("react-datepicker", "DatePicker")

# 2. Use it like any PyNext component
def MyPage():
    return div()[
        h1()["Select a Date"],
        DatePicker(
            selected=date.today(),
            on_change=handle_date_change,
        ),
    ]
```

---

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                        Your Python Code                          │
│                                                                   │
│   DatePicker = use_react("react-datepicker", "DatePicker")       │
│   DatePicker(selected=today, on_change=handler)                  │
│                                                                   │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Server Renders                               │
│                                                                   │
│   <div data-pynext-react-island                                  │
│        data-component="DatePicker"                               │
│        data-package="react-datepicker"                           │
│        data-props='{"selected": "2024-01-15", ...}'>             │
│     <!-- Placeholder or loading state -->                        │
│   </div>                                                          │
│                                                                   │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Client Hydrates                              │
│                                                                   │
│   // PyNext runtime finds the island                             │
│   import { DatePicker } from 'react-datepicker';                 │
│   const props = JSON.parse(el.dataset.props);                    │
│   ReactDOM.render(<DatePicker {...props} />, el);                │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## API Reference

### `use_react(package, component, default_export=False)`

Creates a Python wrapper for a React component.

| Parameter | Type | Description |
|-----------|------|-------------|
| `package` | `str` | NPM package name (e.g., `"react-datepicker"`) |
| `component` | `str` | Component name to import |
| `default_export` | `bool` | If `True`, use default export instead of named |

**Returns:** A callable that creates ReactIsland instances

```python
# Named export: import { Calendar } from 'react-big-calendar'
Calendar = use_react("react-big-calendar", "Calendar")

# Default export: import Editor from '@monaco-editor/react'
MonacoEditor = use_react("@monaco-editor/react", "Editor", default_export=True)
```

### Using the Wrapped Component

The returned wrapper accepts any props:

```python
Calendar(
    events=my_events,           # Passed as-is
    on_select_event=handler,    # Callbacks need special handling
    style={"height": 500},      # Dicts become JS objects
)
```

---

## Complete Examples

### 1. Date Picker

```python
from pynext.react import use_react
from pynext import Signal, div, label

# Wrap the component
DatePicker = use_react("react-datepicker", "DatePicker", default_export=True)

def DatePickerDemo():
    selected_date = Signal(None)
    
    return div(class_="space-y-4")[
        label()["Select your birthday:"],
        DatePicker(
            selected=selected_date.value,
            on_change=lambda d: selected_date.set(d),
            date_format="MMMM d, yyyy",
            show_year_dropdown=True,
            placeholder_text="Click to select",
        ),
    ]
```

**Add to `pynext.npm.txt`:**
```
react-datepicker
```

### 2. Rich Text Editor

```python
from pynext.react import use_react

# Wrap Quill editor
ReactQuill = use_react("react-quill", "default", default_export=True)

def RichTextEditor(initial_value: str = ""):
    content = Signal(initial_value)
    
    return div()[
        ReactQuill(
            value=content.value,
            on_change=content.set,
            modules={
                "toolbar": [
                    ["bold", "italic", "underline"],
                    [{"list": "ordered"}, {"list": "bullet"}],
                    ["link", "image"],
                    ["clean"],
                ],
            },
            placeholder="Start writing...",
        ),
    ]
```

### 3. Data Visualization

```python
from pynext.react import use_react

# Wrap Recharts components
LineChart = use_react("recharts", "LineChart")
Line = use_react("recharts", "Line")
XAxis = use_react("recharts", "XAxis")
YAxis = use_react("recharts", "YAxis")
Tooltip = use_react("recharts", "Tooltip")

def SalesChart(data: list):
    return div(class_="w-full h-96")[
        LineChart(
            width=800,
            height=400,
            data=data,
            margin={"top": 5, "right": 30, "left": 20, "bottom": 5},
        )[
            XAxis(data_key="month"),
            YAxis(),
            Tooltip(),
            Line(
                type="monotone",
                data_key="sales",
                stroke="#8884d8",
                stroke_width=2,
            ),
        ]
    ]
```

### 4. Drag and Drop

```python
from pynext.react import use_react

DragDropContext = use_react("react-beautiful-dnd", "DragDropContext")
Droppable = use_react("react-beautiful-dnd", "Droppable")
Draggable = use_react("react-beautiful-dnd", "Draggable")

def DraggableList(items: list):
    def on_drag_end(result):
        # Handle reordering
        pass
    
    return DragDropContext(on_drag_end=on_drag_end)[
        Droppable(droppable_id="list")[
            [
                Draggable(key=item["id"], draggable_id=item["id"], index=i)[
                    div(class_="p-4 bg-white rounded shadow")[
                        item["text"]
                    ]
                ]
                for i, item in enumerate(items)
            ]
        ]
    ]
```

---

## Handling Callbacks

React callbacks need special handling since they can't be directly serialized.

### Option 1: Server Actions (Recommended)

```python
from pynext import server_action
from pynext.react import use_react

@server_action
async def save_content(content: str):
    await db.save(content)
    return {"status": "saved"}

Editor = use_react("@monaco-editor/react", "Editor", default_export=True)

def CodeEditor():
    return Editor(
        default_value="// Start coding",
        on_save=save_content,  # Calls server action
    )
```

### Option 2: Client-Side Handlers

For purely client-side callbacks, define them in JavaScript:

```python
Editor(
    on_change="window.handleEditorChange",  # JS function name
)
```

Then in your JS:
```javascript
window.handleEditorChange = (value) => {
    console.log('Content:', value);
};
```

---

## Props Serialization

PyNext automatically serializes props for React:

| Python | JavaScript |
|--------|------------|
| `str` | `string` |
| `int`, `float` | `number` |
| `bool` | `boolean` |
| `None` | `null` |
| `dict` | `object` |
| `list` | `array` |
| `date`, `datetime` | ISO string |
| `Signal` | Current value |
| Callable | Server action reference |

### Example

```python
DatePicker(
    selected=datetime(2024, 1, 15),  # → "2024-01-15T00:00:00"
    min_date=date(2020, 1, 1),       # → "2020-01-01"
    show_time=True,                   # → true
    excluded_dates=None,              # → null
    custom_input={                    # → {className: "..."}
        "class_name": "custom-input"
    },
)
```

---

## Setup Requirements

### 1. Add React to Your Project

In `pynext.npm.txt`:
```
react
react-dom
```

### 2. Add Your Component's Package

```
react-datepicker
@monaco-editor/react
recharts
```

### 3. Configure Build (if needed)

Some packages need special bundling. In `pynext.config.py`:

```python
npm_packages = {
    "react-datepicker": {
        "css": True,  # Include package CSS
    },
    "@monaco-editor/react": {
        "externals": ["monaco-editor"],  # Don't bundle monaco
    },
}
```

---

## Performance Considerations

### Islands Are Lazy

React islands only hydrate when visible (using Intersection Observer by default):

```python
# This won't load React until user scrolls to it
HeavyChart = use_react("recharts", "LineChart")

def Page():
    return div()[
        # ... lots of static content ...
        HeavyChart(data=data),  # Hydrates on visibility
    ]
```

### Force Immediate Hydration

For above-the-fold components:

```python
DatePicker(
    selected=today,
    _hydrate="load",  # Hydrate immediately on page load
)
```

### Hydration Strategies

| Strategy | When to Use |
|----------|-------------|
| `"visible"` (default) | Most components, lazy load |
| `"load"` | Above the fold, critical UI |
| `"idle"` | Low priority, hydrate when browser is idle |
| `"never"` | SSR only, no client interactivity |

---

## Debugging

### Check if Component Loaded

```javascript
// In browser console
document.querySelectorAll('[data-pynext-react-island]')
```

### Common Issues

**Component not rendering:**
- Check NPM package is in `pynext.npm.txt`
- Run `pynext deps install`
- Check browser console for import errors

**Props not updating:**
- React islands don't automatically react to Signal changes
- Use server actions to update server state
- Consider using native PyNext components instead

**Styles missing:**
- Some packages need CSS imports
- Add to your main CSS or configure in build

---

## When to Port to Native

Consider porting to native PyNext when:

1. You're using the same React component everywhere
2. It's simple enough (buttons, inputs, cards)
3. You want Signal reactivity
4. You want to reduce JavaScript bundle size

```python
# Instead of wrapping react-select...
Select = use_react("react-select", "Select", default_export=True)

# Consider using the native version
from pynext.shadcn import Select, SelectTrigger, SelectContent, SelectItem
```

---

## Related

- [ShadCN Components](../shadcn/README.md) - Native components (no React needed)
- [Islands Architecture](../rendering/ISLANDS.md) - How islands work
- [NPM Integration](../advanced/NPM_PACKAGES.md) - Managing npm packages

