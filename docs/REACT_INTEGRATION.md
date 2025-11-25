# React Component Integration in PyNext

PyNext provides seamless integration with React npm packages while maintaining optimal performance through **Preact aliasing**. This allows you to use the entire React ecosystem (~99% compatibility) at a fraction of the bundle size.

## Table of Contents

- [Overview](#overview)
- [Performance Comparison](#performance-comparison)
- [How It Works](#how-it-works)
- [Getting Started](#getting-started)
- [Usage Patterns](#usage-patterns)
- [Signal Integration](#signal-integration)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

---

## Overview

PyNext's React integration bridges two reactive systems:

| System | Reactivity Model | Bundle Size | DOM Updates |
|--------|------------------|-------------|-------------|
| **PyNext Native** | SolidJS-style signals | ~5KB | Direct, surgical |
| **React (via Preact)** | Virtual DOM | ~4KB | Reconciliation |

When you use a React component in PyNext, it runs on **Preact** (~4KB) instead of React (~40KB), while maintaining near-complete API compatibility.

```
┌─────────────────────────────────────────────────────────────────┐
│                        PyNext Application                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐         ┌─────────────────────────────┐    │
│  │  Native PyNext  │         │     React Components        │    │
│  │  Components     │◄───────►│     (via Preact ~4KB)       │    │
│  │                 │ Shared  │                             │    │
│  │  • Direct DOM   │ Signals │  • MUI, Chakra, Radix, etc. │    │
│  │  • ~5KB runtime │         │  • Full React API           │    │
│  │  • Instant      │         │  • Virtual DOM              │    │
│  └─────────────────┘         └─────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Performance Comparison

### Bundle Size

| Approach | Runtime Size | Notes |
|----------|-------------|-------|
| PyNext Native Only | ~5KB | Signals runtime |
| PyNext + React (Preact) | ~9KB | 5KB + 4KB Preact |
| Traditional React | ~45KB | React + ReactDOM |
| Next.js | ~70KB+ | React + framework |

### Update Performance

```
Signal Update: count.set(5)
─────────────────────────────────────────────────────

PyNext Native:
  Signal → DOM Element (direct binding)
  Time: ~0.1ms
  
React Component:
  Signal → Preact State → Virtual DOM Diff → DOM
  Time: ~1-2ms
```

**Best Practice**: Use native PyNext components for frequently-updating UI (counters, progress bars, real-time data). Use React components for complex UI libraries (MUI, Chakra).

---

## How It Works

### 1. Build Time: Preact Aliasing

When you install React packages, PyNext's bundler (esbuild) automatically aliases React to Preact:

```javascript
// What you install
import { Button } from '@mui/material';

// What esbuild transforms it to
import { Button } from '@mui/material'; // But React → Preact internally
```

The esbuild configuration:
```
--alias:react=preact/compat
--alias:react-dom=preact/compat
--alias:react/jsx-runtime=preact/jsx-runtime
```

### 2. Server Side: Render Placeholder

When Python renders a `ReactComponent`, it outputs a placeholder `<div>`:

```python
ReactComponent(
    package="@mui/material",
    component="Button",
    props={"variant": "contained"},
    children="Click Me"
)
```

Renders to:
```html
<div 
    id="react_abc123" 
    data-react-component="Button"
    data-react-package="@mui/material"
    data-react-props='{"variant": "contained"}'
    class="pynext-react-root"
>Click Me</div>
```

### 3. Client Side: Hydration

The React bridge (`react-bridge.js`) hydrates these placeholders:

```javascript
// 1. Find all React component placeholders
const components = document.querySelectorAll('[data-react-component]');

// 2. Dynamically import the bundled package
const module = await import('/_pynext/npm/mui_material.bundle.js');

// 3. Get the component
const Button = module.Button;

// 4. Render with Preact
preact.render(createElement(Button, props, children), container);
```

### 4. Signal Integration

When a PyNext Signal is passed as a prop, the bridge creates a subscription:

```javascript
// Signal passed as prop
props: { "value": count_signal }

// Bridge creates subscription
const signal = __pynext__.getSignal('sig_abc123');
signal.subscribe(() => {
    // Re-render React component when signal changes
    forceUpdate();
});
```

---

## Getting Started

### 1. Install React Packages

```bash
cd your-pynext-project
npm install @mui/material @emotion/react @emotion/styled
```

### 2. Enable React Compatibility

```python
# pynext.config.py
react_compat = True

npm_packages = [
    "@mui/material",
    "@emotion/react",
    "@emotion/styled",
]
```

### 3. Use React Components

```python
from pynext import page, div, h1, ReactComponent

@page(title="Dashboard")
def dashboard():
    return div()[
        h1()["My Dashboard"],
        
        ReactComponent(
            package="@mui/material",
            component="Button",
            props={"variant": "contained", "color": "primary"},
            children="Click Me"
        )
    ]
```

### 4. Run the Bundler

```bash
pynext build  # Bundles npm packages with Preact aliasing
pynext dev    # Or start dev server (bundles on demand)
```

---

## Usage Patterns

### Pattern 1: Simple React Component

```python
from pynext import page, div
from pynext.react import ReactComponent

@page
def simple_example():
    return div()[
        ReactComponent(
            package="@mui/material",
            component="Button",
            props={
                "variant": "contained",
                "color": "primary",
                "size": "large",
            },
            children="MUI Button"
        )
    ]
```

### Pattern 2: React Component with PyNext Signal

```python
from pynext import page, Signal, div, span
from pynext.react import ReactComponent

@page
def reactive_example():
    value = Signal(50)
    
    return div()[
        # Native PyNext display - updates instantly
        span()["Current Value: ", value],
        
        # React slider - updates signal on change
        ReactComponent(
            package="@mui/material",
            component="Slider",
            props={
                "value": value,           # Signal → React prop
                "onChange": value.set,     # React event → Signal update
                "min": 0,
                "max": 100,
            }
        )
    ]
```

### Pattern 3: Nested React Components

```python
from pynext import page, div
from pynext.react import ReactComponent

@page
def nested_example():
    return div()[
        ReactComponent(
            package="@mui/material",
            component="Card",
            props={"sx": {"padding": 2}},
            children=[
                ReactComponent(
                    package="@mui/material",
                    component="CardContent",
                    children=[
                        ReactComponent(
                            package="@mui/material",
                            component="Typography",
                            props={"variant": "h5"},
                            children="Card Title"
                        ),
                    ]
                )
            ]
        )
    ]
```

### Pattern 4: Mixed Native + React

```python
from pynext import page, component, Signal, div, h1, p, button, span
from pynext.react import ReactComponent

@component
def HybridCounter():
    count = Signal(0)
    
    return div(class_="counter")[
        # Native PyNext header
        h1()["Hybrid Counter"],
        
        # Native PyNext display (instant updates)
        p()[
            "Count: ",
            span(class_="value")[count]
        ],
        
        # Native PyNext buttons
        div(class_="native-buttons")[
            button(onclick=lambda: count.update(lambda x: x + 1))["+1"],
            button(onclick=lambda: count.update(lambda x: x - 1))["-1"],
        ],
        
        # React MUI buttons (same signal)
        div(class_="react-buttons")[
            ReactComponent(
                package="@mui/material",
                component="Button",
                props={
                    "variant": "contained",
                    "onClick": lambda: count.update(lambda x: x + 10),
                },
                children="+10 (MUI)"
            ),
            ReactComponent(
                package="@mui/material",
                component="Button",
                props={
                    "variant": "outlined",
                    "onClick": lambda: count.set(0),
                },
                children="Reset (MUI)"
            ),
        ],
        
        # React slider controlling the same signal
        ReactComponent(
            package="@mui/material",
            component="Slider",
            props={
                "value": count,
                "onChange": count.set,
                "min": 0,
                "max": 100,
            }
        ),
    ]

@page(title="Hybrid Demo")
def hybrid_demo():
    return div()[
        HybridCounter()
    ]
```

---

## Signal Integration

### How Signals Connect to React

When you pass a PyNext Signal to a React component, the integration layer:

1. **Extracts current value** for server-side rendering
2. **Records binding** for client-side hydration
3. **Creates subscription** when component mounts
4. **Forces re-render** when signal changes

```
┌─────────────────────────────────────────────────────────────────┐
│                     PyNext Signal                                │
│                     value = Signal(50)                           │
└─────────────────────────────────────────────────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            │                 │                 │
            ▼                 ▼                 ▼
    ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
    │ Native span   │ │ React Slider  │ │ React Input   │
    │ span()[value] │ │ value={value} │ │ value={value} │
    └───────────────┘ └───────────────┘ └───────────────┘
            │                 │                 │
            │    Signal.set(75) ◄───────────────┘
            │                 │                 (onChange)
            ▼                 ▼
    ┌───────────────┐ ┌───────────────┐
    │ DOM updates   │ │ React         │
    │ directly      │ │ re-renders    │
    │ (instant)     │ │ (batched)     │
    └───────────────┘ └───────────────┘
```

### Signal as Prop Value

```python
count = Signal(10)

ReactComponent(
    package="@mui/material",
    component="Badge",
    props={
        "badgeContent": count,  # Reactive - updates when count changes
        "color": "primary",      # Static prop
    },
    children="Notifications"
)
```

### Signal Setter as Callback

```python
value = Signal(50)

ReactComponent(
    package="@mui/material",
    component="Slider",
    props={
        "value": value,           # Read from signal
        "onChange": value.set,     # Write to signal
    }
)
```

### Multiple Signals

```python
name = Signal("John")
age = Signal(25)
active = Signal(True)

ReactComponent(
    package="@mui/material",
    component="Card",
    props={
        "title": name,      # All three signals
        "subtitle": age,    # are tracked
        "raised": active,   # independently
    }
)
```

---

## Configuration

### pynext.config.py

```python
# Enable React → Preact aliasing
react_compat = True

# NPM packages to bundle
npm_packages = [
    # React component libraries
    "@mui/material",
    "@emotion/react",
    "@emotion/styled",
    
    # Other React packages
    "@headlessui/react",
    "framer-motion",
    
    # Non-React packages work too
    "chart.js",
    "lodash",
]

# Build options
build = {
    "output": ".pynext/build",
    "minify": True,
    "sourcemap": False,  # Set True for debugging
}
```

### Auto-Detection

PyNext automatically detects React packages by name patterns:

```python
# These are auto-detected as React packages:
"@mui/*"
"@chakra-ui/*"
"@headlessui/react"
"@radix-ui/*"
"@emotion/react"
"styled-components"
"framer-motion"
"react-*"
```

### Manual Configuration

Force a package to use React aliasing:

```python
from pynext.bundler import get_bundler

bundler = get_bundler()
bundler.add_package("my-custom-react-lib", needs_react=True)
```

---

## API Reference

### ReactComponent

```python
class ReactComponent:
    def __init__(
        self,
        package: str,           # NPM package name
        component: str,         # Component to import
        props: dict = None,     # Props (can include Signals)
        children: Any = None,   # Children (string, Element, or list)
    ):
        ...
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `package` | `str` | NPM package name (e.g., `"@mui/material"`) |
| `component` | `str` | Component name to import (e.g., `"Button"`) |
| `props` | `dict` | Props to pass. Signals are auto-bound. |
| `children` | `Any` | String, PyNext Element, or list of children |

**Example:**

```python
ReactComponent(
    package="@mui/material",
    component="Button",
    props={
        "variant": "contained",
        "color": "primary",
        "disabled": is_loading,  # Signal
        "onClick": handle_click,  # Callback
    },
    children="Submit"
)
```

### ReactIsland

For complex React component trees that need to share React context:

```python
class ReactIsland:
    def __init__(
        self,
        children: list = None,      # List of ReactComponents
        shared_context: dict = None, # Shared context data
    ):
        ...
```

**Example:**

```python
from pynext.react import ReactIsland, ReactComponent

ReactIsland(
    children=[
        ReactComponent(
            package="@mui/material",
            component="ThemeProvider",
            props={"theme": my_theme},
            children=[
                ReactComponent("@mui/material", "CssBaseline"),
                ReactComponent("@mui/material", "Container", children=[
                    ReactComponent("@mui/material", "Button", children="Themed Button"),
                ]),
            ]
        )
    ]
)
```

---

## Examples

### Example 1: Form with MUI Components

```python
from pynext import page, Signal, div, h1
from pynext.react import ReactComponent

@page(title="Contact Form")
def contact_form():
    name = Signal("")
    email = Signal("")
    message = Signal("")
    
    return div(class_="form-container")[
        h1()["Contact Us"],
        
        ReactComponent(
            package="@mui/material",
            component="TextField",
            props={
                "label": "Name",
                "value": name,
                "onChange": name.set,
                "fullWidth": True,
                "margin": "normal",
            }
        ),
        
        ReactComponent(
            package="@mui/material",
            component="TextField",
            props={
                "label": "Email",
                "type": "email",
                "value": email,
                "onChange": email.set,
                "fullWidth": True,
                "margin": "normal",
            }
        ),
        
        ReactComponent(
            package="@mui/material",
            component="TextField",
            props={
                "label": "Message",
                "value": message,
                "onChange": message.set,
                "fullWidth": True,
                "multiline": True,
                "rows": 4,
                "margin": "normal",
            }
        ),
        
        ReactComponent(
            package="@mui/material",
            component="Button",
            props={
                "variant": "contained",
                "type": "submit",
                "sx": {"marginTop": 2},
            },
            children="Send Message"
        ),
    ]
```

### Example 2: Data Table with Tanstack Table

```python
from pynext import page, Signal, div
from pynext.react import ReactComponent

@page(title="Data Table")
def data_table():
    data = Signal([
        {"id": 1, "name": "Alice", "role": "Developer"},
        {"id": 2, "name": "Bob", "role": "Designer"},
        {"id": 3, "name": "Charlie", "role": "Manager"},
    ])
    
    return div()[
        ReactComponent(
            package="@mui/x-data-grid",
            component="DataGrid",
            props={
                "rows": data,
                "columns": [
                    {"field": "id", "headerName": "ID", "width": 90},
                    {"field": "name", "headerName": "Name", "width": 150},
                    {"field": "role", "headerName": "Role", "width": 150},
                ],
                "pageSize": 5,
                "checkboxSelection": True,
            }
        )
    ]
```

### Example 3: Charts with Recharts

```python
from pynext import page, Signal, div, h1
from pynext.react import ReactComponent

@page(title="Analytics")
def analytics():
    chart_data = Signal([
        {"name": "Jan", "value": 400},
        {"name": "Feb", "value": 300},
        {"name": "Mar", "value": 600},
        {"name": "Apr", "value": 800},
    ])
    
    return div()[
        h1()["Sales Analytics"],
        
        ReactComponent(
            package="recharts",
            component="ResponsiveContainer",
            props={"width": "100%", "height": 300},
            children=[
                ReactComponent(
                    package="recharts",
                    component="LineChart",
                    props={"data": chart_data},
                    children=[
                        ReactComponent("recharts", "XAxis", props={"dataKey": "name"}),
                        ReactComponent("recharts", "YAxis"),
                        ReactComponent("recharts", "Line", props={
                            "type": "monotone",
                            "dataKey": "value",
                            "stroke": "#6366f1",
                        }),
                    ]
                )
            ]
        )
    ]
```

---

## Troubleshooting

### Component Not Rendering

**Symptom:** Placeholder div appears but component doesn't render.

**Solutions:**
1. Check browser console for errors
2. Verify package is installed: `npm list @mui/material`
3. Check bundle exists: `ls .pynext/bundles/`
4. Rebuild bundles: `pynext build`

### Signal Not Updating React Component

**Symptom:** Native PyNext elements update but React component doesn't.

**Solutions:**
1. Ensure signal is passed directly (not called): `"value": count` not `"value": count()`
2. Check React bridge loaded: Look for `[PyNext] React bridge initialized` in console
3. Verify hydration data includes signal bindings

### Import Errors

**Symptom:** `Component not found: XYZ in package`

**Solutions:**
1. Check component name matches export: Some packages use default exports
2. Try different import: `"component": "default"` or `"component": "Button"`
3. Check package documentation for export names

### Styles Not Applied

**Symptom:** MUI/Chakra components render but look unstyled.

**Solutions:**
1. Install emotion packages: `npm install @emotion/react @emotion/styled`
2. Add CSS baseline at app root
3. Check for CSS-in-JS hydration issues

### Bundle Size Too Large

**Symptom:** Slow page loads.

**Solutions:**
1. Use tree-shaking: Import specific components
2. Check for duplicate React in bundle
3. Enable minification in config
4. Lazy load heavy components

---

## Compatibility

### Supported React Features

| Feature | Support | Notes |
|---------|---------|-------|
| Functional Components | ✅ Full | |
| Class Components | ✅ Full | |
| Hooks | ✅ Full | useState, useEffect, etc. |
| Context | ✅ Full | |
| Portals | ✅ Full | |
| Refs | ✅ Full | |
| Error Boundaries | ✅ Full | |
| Suspense | ⚠️ Partial | Basic support |
| Concurrent Mode | ❌ No | Use React 17 patterns |
| Server Components | ❌ No | Not applicable |

### Tested Libraries

| Library | Status | Notes |
|---------|--------|-------|
| @mui/material | ✅ Works | Full support |
| @chakra-ui/react | ✅ Works | Full support |
| @headlessui/react | ✅ Works | Full support |
| @radix-ui/* | ✅ Works | Full support |
| framer-motion | ✅ Works | Full support |
| react-hook-form | ✅ Works | Full support |
| react-query | ✅ Works | Full support |
| recharts | ✅ Works | Full support |
| react-table | ✅ Works | Full support |
| styled-components | ✅ Works | Full support |

---

## Architecture Deep Dive

### File Structure

```
pynext/
├── react/
│   └── __init__.py          # ReactComponent, ReactIsland classes
├── runtime/
│   ├── signals.js           # Core PyNext runtime
│   └── react-bridge.js      # React mounting & signal integration
├── bundler/
│   └── npm.py               # esbuild with Preact aliasing
```

### Data Flow

```
1. Python (Server)
   ────────────────
   ReactComponent(package="@mui/material", component="Slider", props={"value": signal})
         │
         ▼
2. HTML Output
   ────────────────
   <div id="react_123" data-react-component="Slider" data-react-package="@mui/material" ...>
         │
         ▼
3. Hydration Data
   ────────────────
   window.__PYNEXT_HYDRATION__ = {
     signals: { "sig_456": { value: 50 } },
     reactComponents: [{ id: "react_123", signalBindings: { "value": "sig_456" } }]
   }
         │
         ▼
4. Client Hydration
   ────────────────
   signals.js: Creates PyNext signals
   react-bridge.js: Mounts React components, subscribes to signals
         │
         ▼
5. Runtime
   ────────────────
   Signal update → Notifies both:
     • PyNext DOM bindings (instant)
     • React component subscriptions (triggers re-render)
```

---

## Contributing

To add support for new React libraries or improve the integration:

1. Test the library with Preact compatibility
2. Add to auto-detection patterns in `npm.py` if needed
3. Document any special configuration required
4. Add example to `example/pages/`

---

## License

MIT License - See main project LICENSE file.

