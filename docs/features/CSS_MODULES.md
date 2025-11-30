# CSS Modules

Build-time scoped CSS with zero JavaScript runtime.

## The Problem

CSS conflicts happen when two components use the same class name. Traditional solutions require JavaScript runtime overhead (CSS-in-JS) or complex build tools.

**Next.js**: Requires webpack, adds ~5KB CSS-in-JS runtime, styles applied at runtime.

**PyNext**: Build-time class name scoping, zero runtime JS, single CSS file output.

## Quick Start

```python
from pynext import css, component

# Define scoped styles
styles = css("""
.button {
    padding: 8px 16px;
    background: blue;
    color: white;
}

.button:hover {
    background: darkblue;
}

.primary {
    background: green;
}
""")

@component
def Button(variant="default", children=None):
    # Access scoped class names as attributes
    variant_class = styles.get(variant, "")
    return button(class_=f"{styles.button} {variant_class}")[
        children
    ]
```

**Output CSS:**
```css
.Button_button_x7f3d { padding: 8px 16px; background: blue; color: white; }
.Button_button_x7f3d:hover { background: darkblue; }
.Button_primary_a2b1c { background: green; }
```

## How It Works

### First Principles

1. **Parse CSS**: Extract all class selectors (`.button`, `.primary`)
2. **Generate Hash**: Create unique hash from content + component name
3. **Scope Names**: Prefix classes with `ComponentName_className_hash`
4. **Replace References**: Update all class references in the CSS

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  .button    │ → │   Hash      │ → │ Button_     │
│  { ... }    │   │  "x7f3d"    │   │ button_x7f3d│
└─────────────┘    └─────────────┘    └─────────────┘
```

### Why Build-Time?

- **Zero JS runtime**: No CSS-in-JS library shipped to browser
- **Deterministic**: Same input always produces same output
- **Cache-friendly**: Hash based on content, not random
- **Single request**: All CSS bundled into one file

## API Reference

### css()

Create inline CSS module with automatic scoping.

```python
from pynext import css

styles = css("""
.container {
    max-width: 1200px;
    margin: 0 auto;
}

.header {
    padding: 20px;
    border-bottom: 1px solid #eee;
}
""")

# Access classes
styles.container  # "Component_container_abc12"
styles.header     # "Component_header_abc12"
styles["container"]  # Same as above
```

**Parameters:**
- `content` (str): CSS string
- `component` (str, optional): Component name override

### css_module()

Load CSS from external file.

```python
from pynext import css_module

# Load from Card.module.css in same directory
styles = css_module("./Card.module.css")

# Access classes same way
styles.card
styles.header
```

**Parameters:**
- `path` (str): Path to CSS file (relative or absolute)
- `component` (str, optional): Component name override

### CSSModule Methods

```python
styles = css(".btn { } .primary { } .disabled { }")

# Attribute access
styles.btn              # "Component_btn_hash"

# Dictionary access
styles["btn"]           # "Component_btn_hash"

# Check existence
"btn" in styles         # True

# Get with default
styles.get("missing", "fallback")  # "fallback"

# Combine classes
styles.classes("btn", "primary")   # "Component_btn_hash Component_primary_hash"

# Conditional classes
styles.conditional(
    btn=True,
    primary=is_primary,
    disabled=is_disabled,
)

# Get all mappings
styles.all_classes      # {"btn": "...", "primary": "...", ...}

# Get raw CSS
styles.css              # Scoped CSS string
```

## Patterns

### Component Variants

```python
styles = css("""
.button { padding: 8px 16px; background: gray; }
.primary { background: blue; }
.secondary { background: white; border: 1px solid gray; }
.danger { background: red; }
""")

@component
def Button(variant="default", children=None):
    return button(
        class_=styles.classes("button", variant)
    )[children]

# Usage
Button(variant="primary")["Save"]
Button(variant="danger")["Delete"]
```

### Composition

```python
base_styles = css("""
.card { border-radius: 8px; padding: 16px; }
""", component="Base")

card_styles = css("""
.card { border: 1px solid #eee; }
.elevated { box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
""", component="Card")

@component
def Card(elevated=False, children=None):
    return div(
        class_=f"{base_styles.card} {card_styles.card}" + 
               (f" {card_styles.elevated}" if elevated else "")
    )[children]
```

### With Tailwind

CSS Modules work alongside Tailwind:

```python
styles = css("""
.custom-animation {
    animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}
""")

@component
def FadeIn(children):
    # Combine Tailwind utilities with custom CSS
    return div(class_=f"p-4 bg-white {styles.custom_animation}")[
        children
    ]
```

## Build Integration

### CSS Extraction

Extract CSS from Python files:

```python
from pynext.css import CSSExtractor, extract_all_css
from pathlib import Path

# Extract from single file
extractor = CSSExtractor()
results = extractor.extract_file(Path("components/Button.py"))

for css_info in results:
    print(f"{css_info.component}: {len(css_info.classes)} classes")

# Extract from directory
all_css = extract_all_css(Path("components"), recursive=True)
```

### CSS Bundling

Bundle all CSS into single file:

```python
from pynext.css import CSSBundler, bundle_css
from pathlib import Path

# Manual bundling
bundler = CSSBundler()
bundler.add_css("Button", scoped_button_css)
bundler.add_css("Card", scoped_card_css)

bundle = bundler.bundle(minify=True)
print(f"Size: {bundle.stats.minified_size} bytes")

# Convenience function
bundle = bundle_css(
    directories=[Path("components"), Path("pages")],
    output=Path("dist/styles.css"),
    minify=True,
)
```

### Build Output

```
dist/
├── styles.css       # All CSS combined and minified
└── styles.css.map   # Optional source map
```

## Performance

| Metric | Next.js CSS Modules | PyNext CSS Modules |
|--------|--------------------|--------------------|
| Runtime JS | ~5KB | 0KB |
| Parse time | Runtime | Build-time |
| HTTP requests | 1+ per page | 1 total |
| Cache invalidation | Per file | Content-based hash |

## Migration from Next.js

### Before (Next.js)

```jsx
// Button.module.css
.button { padding: 8px; }
.primary { background: blue; }

// Button.tsx
import styles from './Button.module.css';

export function Button({ variant }) {
  return (
    <button className={`${styles.button} ${styles[variant]}`}>
      Click
    </button>
  );
}
```

### After (PyNext)

```python
from pynext import css, component

styles = css("""
.button { padding: 8px; }
.primary { background: blue; }
""")

@component
def Button(variant="default", children=None):
    return button(class_=styles.classes("button", variant))[
        children
    ]
```

## Troubleshooting

### Class Not Found

```python
# Error: AttributeError: CSS class 'buttom' not defined
styles.buttom  # Typo!

# Fix: Check spelling
styles.button  # Correct
```

### Conflicting Hashes

If two components have the same hash (rare), override the component name:

```python
styles = css(".btn { }", component="UniqueButton")
```

### External CSS Not Loading

```python
# Error: FileNotFoundError
styles = css_module("./missing.css")

# Fix: Check path is relative to caller file
styles = css_module("../styles/Button.module.css")
```

