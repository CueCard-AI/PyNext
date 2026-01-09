# DOM API Reference

PyNext provides complete DOM API bindings for manipulating web pages from Python code. All DOM APIs transpile directly to JavaScript with zero runtime overhead.

## Overview

| Feature | Description |
|---------|-------------|
| **90+ APIs** | Complete Document and Element interfaces |
| **Zero Overhead** | Passthrough transpilation - no runtime helpers |
| **Full Type Hints** | IDE autocompletion for all APIs |
| **Pythonic Syntax** | Same API, Python-friendly |

## Quick Start

```python
from pynext.client import document

# Query elements
app = document.getElementById("app")
buttons = document.querySelectorAll("button")

# Create elements
div = document.createElement("div")
div.id = "container"
div.className = "wrapper"
div.innerHTML = "<h1>Hello, World!</h1>"

# Append to DOM
document.body.appendChild(div)

# Work with classes
div.classList.add("active", "visible")
div.classList.toggle("hidden")

# Work with data attributes
div.dataset.userId = "123"
print(div.dataset.userId)
```

## Transpilation

DOM APIs are **passthrough** - they transpile to identical JavaScript:

| Python | JavaScript |
|--------|------------|
| `document.getElementById("app")` | `document.getElementById("app")` |
| `el.classList.add("active")` | `el.classList.add("active")` |
| `el.dataset.userId = "123"` | `el.dataset.userId = "123"` |
| `el.remove()` | `el.remove()` |

**No runtime wrappers. No overhead. Clean JavaScript.**

---

## Document API

### Query Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `getElementById(id)` | `Element | None` | Get element by ID |
| `querySelector(selector)` | `Element | None` | First element matching CSS selector |
| `querySelectorAll(selector)` | `NodeList` | All elements matching CSS selector |
| `getElementsByClassName(name)` | `HTMLCollection` | Elements by class name |
| `getElementsByTagName(name)` | `HTMLCollection` | Elements by tag name |
| `getElementsByName(name)` | `NodeList` | Elements by name attribute |

```python
# Examples
app = document.getElementById("app")
btn = document.querySelector("button.primary")
items = document.querySelectorAll(".item")
divs = document.getElementsByTagName("div")
```

### Creation Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `createElement(tagName)` | `Element` | Create HTML element |
| `createElementNS(ns, tagName)` | `Element` | Create namespaced element (SVG, MathML) |
| `createTextNode(text)` | `Text` | Create text node |
| `createComment(text)` | `Comment` | Create comment node |
| `createDocumentFragment()` | `DocumentFragment` | Create fragment for batch operations |

```python
# Create and configure elements
div = document.createElement("div")
div.id = "container"
div.className = "wrapper"

# Create SVG elements
svg_ns = "http://www.w3.org/2000/svg"
svg = document.createElementNS(svg_ns, "svg")
circle = document.createElementNS(svg_ns, "circle")
circle.setAttribute("r", "50")

# Efficient batch operations
fragment = document.createDocumentFragment()
for item in items:
    li = document.createElement("li")
    li.textContent = item
    fragment.appendChild(li)
ul.appendChild(fragment)  # Single DOM update
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `body` | `Element` | Document body |
| `head` | `Element` | Document head |
| `documentElement` | `Element` | Root `<html>` element |
| `title` | `str` | Document title (read/write) |
| `activeElement` | `Element | None` | Currently focused element |
| `readyState` | `str` | "loading", "interactive", "complete" |
| `hidden` | `bool` | Is tab hidden |
| `visibilityState` | `str` | "visible" or "hidden" |
| `cookie` | `str` | Document cookies |

```python
# Examples
document.title = "My App - Dashboard"
if document.hidden:
    pause_video()
```

---

## Element API

### Attributes

| Method/Property | Returns | Description |
|-----------------|---------|-------------|
| `getAttribute(name)` | `str | None` | Get attribute value |
| `setAttribute(name, value)` | `None` | Set attribute value |
| `removeAttribute(name)` | `None` | Remove attribute |
| `hasAttribute(name)` | `bool` | Check if attribute exists |
| `toggleAttribute(name, force?)` | `bool` | Toggle boolean attribute |
| `getAttributeNames()` | `list[str]` | All attribute names |
| `id` | `str` | Element ID (read/write) |

```python
el.setAttribute("data-active", "true")
if el.hasAttribute("disabled"):
    el.removeAttribute("disabled")
```

### Content

| Property | Type | Description |
|----------|------|-------------|
| `innerHTML` | `str` | HTML content (read/write) |
| `outerHTML` | `str` | Element + content (read/write) |
| `innerText` | `str` | Visible text (read/write) |
| `textContent` | `str` | All text content (read/write) |
| `value` | `str` | Form element value |

```python
el.innerHTML = "<span>Hello</span>"
el.textContent = "Plain text"
input_el.value = "New value"
```

### Classes (classList)

| Method | Returns | Description |
|--------|---------|-------------|
| `classList.add(*names)` | `None` | Add classes |
| `classList.remove(*names)` | `None` | Remove classes |
| `classList.toggle(name, force?)` | `bool` | Toggle class |
| `classList.contains(name)` | `bool` | Has class |
| `classList.replace(old, new)` | `bool` | Replace class |

```python
el.classList.add("active", "visible")
el.classList.remove("hidden")
el.classList.toggle("expanded")
if el.classList.contains("active"):
    print("Active!")
```

### Data Attributes (dataset)

Access `data-*` attributes with camelCase conversion:

```python
# HTML: <div data-user-id="123" data-user-name="Alice">

el.dataset.userId      # "123"
el.dataset.userName    # "Alice"

el.dataset.role = "admin"  # Sets data-role="admin"
```

### Traversal

| Property | Returns | Description |
|----------|---------|-------------|
| `parentElement` | `Element | None` | Parent element |
| `children` | `HTMLCollection` | Child elements |
| `firstElementChild` | `Element | None` | First child element |
| `lastElementChild` | `Element | None` | Last child element |
| `nextElementSibling` | `Element | None` | Next sibling element |
| `previousElementSibling` | `Element | None` | Previous sibling element |
| `childElementCount` | `int` | Number of child elements |

| Method | Returns | Description |
|--------|---------|-------------|
| `closest(selector)` | `Element | None` | Find ancestor by selector |
| `matches(selector)` | `bool` | Check if matches selector |

```python
parent = el.parentElement
for child in el.children:
    print(child.tagName)

container = el.closest(".container")
if el.matches(".active"):
    print("Active!")
```

### Manipulation

| Method | Returns | Description |
|--------|---------|-------------|
| `appendChild(child)` | `Node` | Append child |
| `insertBefore(new, ref)` | `Node` | Insert before reference |
| `removeChild(child)` | `Node` | Remove child |
| `replaceChild(new, old)` | `Node` | Replace child |
| `remove()` | `None` | Remove self |
| `cloneNode(deep?)` | `Node` | Clone element |
| `append(*nodes)` | `None` | Append multiple nodes/strings |
| `prepend(*nodes)` | `None` | Prepend multiple nodes/strings |
| `after(*nodes)` | `None` | Insert after self |
| `before(*nodes)` | `None` | Insert before self |

```python
parent.appendChild(child)
el.remove()
clone = el.cloneNode(True)  # Deep clone
el.append(node1, "text", node2)
```

### Focus

| Method | Description |
|--------|-------------|
| `focus()` | Focus element |
| `blur()` | Remove focus |
| `click()` | Simulate click |

```python
input_el.focus()
button.click()
```

---

## Collections

### NodeList

Returned by `querySelectorAll()` and `childNodes`.

```python
items = document.querySelectorAll(".item")
print(items.length)  # Number of items

# Iterate
for item in items:
    item.classList.add("processed")

# Access by index
first = items.item(0)
```

### HTMLCollection

Live collection returned by `getElementsBy*()` methods.

```python
divs = document.getElementsByTagName("div")
print(divs.length)

# Access by name/id
special = divs.namedItem("special-id")
```

---

## Style

Access inline styles via `element.style`:

```python
el.style.display = "flex"
el.style.backgroundColor = "blue"
el.style.setProperty("--custom-color", "red")

# Remove property
el.style.removeProperty("display")
```

---

## Best Practices

### 1. Use DocumentFragment for Batch Operations

```python
fragment = document.createDocumentFragment()
for i in range(100):
    li = document.createElement("li")
    li.textContent = f"Item {i}"
    fragment.appendChild(li)
ul.appendChild(fragment)  # Single DOM update
```

### 2. Query Once, Manipulate Many

```python
# Good
el = document.getElementById("app")
el.classList.add("active")
el.dataset.loaded = "true"
el.innerHTML = content

# Avoid querying repeatedly
```

### 3. Use classList Instead of className

```python
# Good
el.classList.add("active")
el.classList.remove("hidden")

# Avoid - can accidentally remove other classes
el.className = "active"
```

### 4. Use dataset for Custom Data

```python
# Good
el.dataset.userId = "123"

# Avoid
el.setAttribute("data-user-id", "123")
```

---

## Type Hints

All DOM APIs are fully typed for IDE support:

```python
from pynext.client import document, Element, NodeList

def process_items(container: Element) -> None:
    items: NodeList = container.querySelectorAll(".item")
    for item in items:
        item.classList.add("processed")

app: Element = document.getElementById("app")
if app:
    process_items(app)
```

---

## See Also

- [Transpilation Internals](../internals/TRANSPILATION_DOM.md) - How DOM passthrough works
- [Phase 34.1 Test Overview](../test-case-tracking/phase-34/phase-34-1/TEST_OVERVIEW.md) - Test coverage

