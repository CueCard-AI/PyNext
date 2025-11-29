# PyNext Testing

Stupid simple testing for PyNext components. ONE LINE to render, ONE LINE to assert.

## Table of Contents

- [The Problem](#the-problem)
- [The Solution](#the-solution)
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [API Reference](#api-reference)
- [Real-World Patterns](#real-world-patterns)
- [Troubleshooting](#troubleshooting)
- [Comparison with Jest](#comparison-with-jest)

---

## The Problem

Testing React components typically requires:
- Setting up JSDOM or a real browser
- Complex mounting/unmounting lifecycle
- Waiting for async renders
- Virtual DOM diffing
- 100+ lines of boilerplate

This makes testing slow, fragile, and frustrating.

---

## The Solution

PyNext components are just Python functions that return HTML. We can test them instantly without any DOM setup:

```
┌─────────────────────────────────────────────────────────┐
│                   Testing Flow                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   Component      render()      RenderResult             │
│   ┌──────┐      ────────►    ┌────────────┐            │
│   │ def  │                   │ - html     │            │
│   │Button│                   │ - root     │            │
│   │ ...  │                   │ - signals  │            │
│   └──────┘                   └────────────┘            │
│                                    │                   │
│                                    ▼                   │
│                          ┌─────────────────┐           │
│                          │  Assertions     │           │
│                          │  - assert_text  │           │
│                          │  - assert_class │           │
│                          │  - assert_a11y  │           │
│                          └─────────────────┘           │
│                                    │                   │
│                                    ▼                   │
│                               Pass/Fail                │
│                                                        │
└────────────────────────────────────────────────────────┘
```

**Performance Comparison:**

| Operation | Jest + JSDOM | PyNext Testing |
|-----------|--------------|----------------|
| Render component | ~100ms | <5ms |
| DOM query | ~5ms | <1ms |
| Full test suite (100 tests) | ~30s | <2s |

---

## Quick Start

### Installation

PyNext testing is built-in. No extra installation needed.

### Your First Test

```python
# tests/test_button.py
from pynext.testing import render, assert_text, assert_has_class

def test_button():
    # Render the component
    result = render(Button, label="Click me")
    
    # Assert text content
    assert_text(result, "Click me")
    
    # Assert CSS class
    assert_has_class(result, "btn-primary")
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Update snapshots
PYNEXT_UPDATE_SNAPSHOTS=1 pytest tests/
```

---

## Core Concepts

### 1. Rendering (`render()`)

The `render()` function is the heart of PyNext testing:

```python
from pynext.testing import render

# Render a class component
result = render(Button, label="Click")

# Render a function component
result = render(my_component, data=items)

# Render an already-instantiated component
btn = Button(label="Test")
result = render(btn)
```

**What you get back:**

```python
result.html        # Raw HTML string
result.root        # Parsed DOM tree (HTMLNode)
result.signals     # Dict of signals for reactivity testing
result.render_time_ms  # How long render took
result.text        # All text content
```

### 2. Assertions (AI-Friendly Names)

Every assertion clearly describes what it checks:

```python
# Text assertions
assert_text(result, "Hello")           # Contains text
assert_no_text(result, "Error")        # Doesn't contain text
assert_text_matches(result, r"\d+")    # Matches regex

# Class assertions
assert_has_class(result, "btn")        # Has CSS class
assert_no_class(result, "disabled")    # Doesn't have class
assert_classes(result, ["a", "b"])     # Has all classes

# Attribute assertions
assert_has_attribute(result, "disabled")
assert_has_attribute(result, "type", "button")

# Element assertions
assert_exists(result, ".modal")        # Element exists
assert_not_exists(result, ".error")    # Element doesn't exist
assert_count(result, "li", 5)          # Exactly N elements
assert_tag(result, "button")           # Correct tag
```

### 3. CSS Selectors

Query elements like you would in JavaScript:

```python
# By tag
button = result.query_selector("button")

# By class
modal = result.query_selector(".modal")

# By ID
header = result.query_selector("#main-header")

# Combined
submit = result.query_selector("button.primary")

# Find all matching
items = result.query_selector_all("li")
```

### 4. Signal Testing (SolidJS Principles)

Test reactivity directly without simulating events:

```python
from pynext.testing import render, update_signal, assert_text

def test_counter():
    result = render(Counter, initial=0)
    assert_text(result, "Count: 0")
    
    # Directly manipulate the signal
    update_signal(result, "count", 5)
    
    # Re-render to see changes
    result = result.update()
    assert_text(result, "Count: 5")
```

**Why this is better:**
- No simulated clicks
- No waiting for events
- Instant feedback
- Test the signal, not the UI

### 5. Accessibility Testing

One function checks everything:

```python
from pynext.testing import render, assert_accessible

def test_form_accessibility():
    result = render(ContactForm)
    
    # Checks WCAG 2.1 AA compliance:
    # - Button names
    # - Image alt text
    # - Form labels
    # - Heading order
    # - ARIA attributes
    # - Keyboard access
    assert_accessible(result)
```

Ignore specific rules:

```python
assert_accessible(result, ignore_rules={"heading-order"})
```

### 6. Snapshot Testing

Automatic HTML comparison:

```python
from pynext.testing import render, assert_snapshot

def test_card():
    result = render(Card, title="Hello")
    
    # First run: Creates __snapshots__/card_basic.html
    # Next runs: Compares to saved snapshot
    assert_snapshot(result, "card_basic")
```

Update snapshots:

```bash
PYNEXT_UPDATE_SNAPSHOTS=1 pytest tests/
```

### 7. Visual Regression

Screenshot-based comparison:

```python
from pynext.testing import render, assert_visual_match

def test_button_visual():
    result = render(Button, variant="primary")
    
    # Compares rendered image to baseline
    assert_visual_match(result, "button_primary")
```

Test responsive variants:

```python
assert_no_visual_regression(result, "card", {
    "desktop": {"width": 1200},
    "tablet": {"width": 768},
    "mobile": {"width": 375},
})
```

### 8. Async Testing

Clean async component testing:

```python
from pynext.testing import render, wait_for, assert_text

async def test_data_loader():
    result = render(DataLoader, endpoint="/api/users")
    
    # Wait for content to load
    await wait_for(result, timeout=2.0)
    
    # Now assert
    assert_text(result, "John Doe")
```

Wait for specific conditions:

```python
await wait_for_element(result, ".loaded")
await wait_for_text(result, "Success")
await wait_for_removal(result, ".loading")
```

### 9. Performance Testing

Benchmark your components:

```python
from pynext.testing import benchmark, assert_render_time

@benchmark(iterations=100)
def test_list_performance():
    result = render(ProductList, items=range(1000))
    assert_render_time(result, max_ms=50)
```

Timing utilities:

```python
from pynext.testing import Timer, time_function

with Timer() as t:
    result = render(HeavyComponent)
print(f"Took {t.ms}ms")

result, ms = time_function(render, BigList, items=data)
```

---

## API Reference

### Render Functions

| Function | Description |
|----------|-------------|
| `render(component, *args, **kwargs)` | Render component, return RenderResult |
| `render_to_string(component, ...)` | Render and return just HTML string |
| `update_signal(result, name, value)` | Update a signal in rendered component |
| `get_signal_value(result, name)` | Get current signal value |

### Text Assertions

| Function | Description |
|----------|-------------|
| `assert_text(result, text)` | Contains text |
| `assert_no_text(result, text)` | Doesn't contain text |
| `assert_text_matches(result, pattern)` | Matches regex |

### Class Assertions

| Function | Description |
|----------|-------------|
| `assert_has_class(result, class_)` | Has CSS class |
| `assert_no_class(result, class_)` | Doesn't have class |
| `assert_classes(result, [classes])` | Has all classes |

### Attribute Assertions

| Function | Description |
|----------|-------------|
| `assert_has_attribute(result, name, value?)` | Has attribute |
| `assert_no_attribute(result, name)` | No attribute |

### Element Assertions

| Function | Description |
|----------|-------------|
| `assert_exists(result, selector)` | Element exists |
| `assert_not_exists(result, selector)` | No element |
| `assert_count(result, selector, n)` | Exactly N elements |
| `assert_tag(result, tag)` | Correct tag |

### Accessibility Assertions

| Function | Description |
|----------|-------------|
| `assert_accessible(result)` | WCAG 2.1 AA check |
| `check_accessibility(result)` | Get detailed A11yResult |
| `assert_role(result, role)` | Has ARIA role |
| `assert_aria_label(result, label)` | Has aria-label |
| `assert_focusable(result, selector)` | Is focusable |

### Async Utilities

| Function | Description |
|----------|-------------|
| `wait_for(result, condition, timeout)` | Wait for condition |
| `wait_for_element(result, selector)` | Wait for element |
| `wait_for_text(result, text)` | Wait for text |
| `wait_for_removal(result, selector)` | Wait for removal |
| `act(func)` | Run and wait for updates |

### Benchmark Utilities

| Function | Description |
|----------|-------------|
| `@benchmark(iterations=100)` | Benchmark decorator |
| `measure_render_time(component)` | Measure render time |
| `Timer()` | Timing context manager |
| `assert_performance(result, max_ms=N)` | Assert timing |

---

## Real-World Patterns

### Testing a Form Component

```python
def test_contact_form():
    result = render(ContactForm)
    
    # Structure
    assert_exists(result, "form")
    assert_count(result, "input", 3)
    assert_exists(result, "button[type=submit]")
    
    # Accessibility
    assert_accessible(result)
    
    # Labels
    assert_text(result, "Name")
    assert_text(result, "Email")
    assert_text(result, "Message")
```

### Testing a Data Table

```python
def test_data_table():
    data = [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
    ]
    
    result = render(DataTable, data=data)
    
    # Headers
    assert_text(result, "ID")
    assert_text(result, "Name")
    
    # Rows
    assert_count(result, "tr", 3)  # header + 2 data rows
    assert_text(result, "Alice")
    assert_text(result, "Bob")
    
    # Performance
    assert_render_time(result, max_ms=100)
```

### Testing Signals

```python
def test_todo_list():
    result = render(TodoList)
    
    # Initial state
    assert_signal_value(result, "todos", [])
    assert_text(result, "No items")
    
    # Add item
    update_signal(result, "todos", [{"text": "Buy milk"}])
    result = result.update()
    
    assert_count(result, ".todo-item", 1)
    assert_text(result, "Buy milk")
```

### Testing Async Components

```python
async def test_user_profile():
    result = render(UserProfile, user_id=1)
    
    # Loading state
    assert_exists(result, ".loading")
    
    # Wait for data
    await wait_for(result, lambda r: ".loading" not in r.html)
    
    # Loaded state
    assert_text(result, "John Doe")
    assert_text(result, "john@example.com")
```

---

## Troubleshooting

### "Element not found" Error

```python
# Problem: Selector doesn't match
assert_exists(result, ".btn")  # Error!

# Solution: Check your selector
print(result.html)  # See actual HTML
assert_exists(result, "button")  # Fixed
```

### Snapshot Mismatch

```bash
# Update all snapshots
PYNEXT_UPDATE_SNAPSHOTS=1 pytest tests/

# Update specific test
PYNEXT_UPDATE_SNAPSHOTS=1 pytest tests/test_card.py::test_card_basic
```

### Slow Tests

```python
# Problem: Tests are slow
def test_heavy():
    result = render(HeavyComponent)  # 500ms

# Solution: Use benchmarks to find bottlenecks
@benchmark(iterations=10)
def test_heavy():
    result = render(HeavyComponent)
    # Now you'll see timing stats
```

### Signal Not Found

```python
# Problem: Signal doesn't exist
update_signal(result, "count", 5)  # KeyError!

# Solution: Check available signals
print(result.signals.keys())  # ['total', 'items']
update_signal(result, "total", 5)  # Fixed
```

---

## Comparison with Jest

| Feature | Jest + RTL | PyNext Testing |
|---------|------------|----------------|
| Render | `render(<Button />)` | `render(Button)` |
| Query | `screen.getByText()` | `result.query_selector()` |
| Assert | `expect(el).toBeInTheDocument()` | `assert_exists(result, sel)` |
| Async | `await waitFor(() => ...)` | `await wait_for(result, ...)` |
| Snapshot | `expect().toMatchSnapshot()` | `assert_snapshot(result, name)` |
| Speed | ~30s for 100 tests | ~2s for 100 tests |

**Key Differences:**
1. No DOM emulation needed
2. Direct signal manipulation (no event simulation)
3. Python-native assertions
4. 15x faster execution
5. Built-in accessibility testing

---

## Summary

PyNext testing is designed for:
- **Simplicity**: One line to render, one line to assert
- **Speed**: 15x faster than Jest + JSDOM
- **Clarity**: AI-friendly assertion names
- **Completeness**: Accessibility, snapshots, visuals, benchmarks

Start testing your components in seconds, not hours.

