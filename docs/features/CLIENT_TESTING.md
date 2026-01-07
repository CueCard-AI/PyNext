# PyNext Client Testing Guide

## Overview

PyNext provides a comprehensive testing infrastructure for client-side components that mirrors React Testing Library's API, making it familiar for developers coming from React while optimized for PyNext's signal-based reactivity.

## Who Should Use This

- **Developers writing tests** for PyNext client components
- **Teams migrating from React** who want familiar testing patterns
- **Anyone building client-side applications** with PyNext

## What It Provides

### 1. React Testing Library-Style API

The `pynext.testing.client` module provides an RTL-compatible API:

```python
from pynext.testing.client import render, screen, fireEvent, waitFor

def test_button_click():
    render(Button, label="Click me")
    button = screen.getByRole("button")
    fireEvent.click(button)
    assert screen.getByText("Clicked!")
```

### 2. Query Methods

Three variants of each query method:

- **`getBy*`** - Throws if element not found (assertive)
- **`queryBy*`** - Returns None if not found (non-assertive)
- **`findBy*`** - Async, waits for element to appear

All queries support regex patterns:

```python
screen.getByText(/submit/i)  # Case-insensitive regex
screen.getByText("Submit", exact=False)  # Substring match
```

### 3. Event Firing

Comprehensive event simulation:

```python
fireEvent.click(button)
fireEvent.change(input, {"target": {"value": "new text"}})
fireEvent.keyDown(input, {"key": "Enter"})
```

### 4. Mocking Utilities

Mock browser APIs:

```python
from pynext.testing.mocks import mock_fetch, mock_navigator

with mock_fetch({
    "https://api.example.com": {"status": 200, "data": {...}}
}):
    response = await fetch("https://api.example.com")
```

## When to Use

- **Component Testing**: Test individual components in isolation
- **Integration Testing**: Test component interactions
- **User Interaction Testing**: Verify click handlers, form submissions, etc.
- **Async Testing**: Test components that fetch data or have async updates

## How It Works

### Architecture

```
Python Component → render() → HTML → HTMLNode Tree → Query API
                                              ↓
                                         Event Handlers
```

1. Components render to HTML strings
2. HTML is parsed into an `HTMLNode` tree
3. Query methods search the tree
4. Events are simulated on nodes
5. Signals update components reactively

### Example: Complete Test

```python
import pytest
from pynext.testing.client import render, screen, fireEvent, cleanup
from pynext.reactive import Signal

@pytest.fixture(autouse=True)
def auto_cleanup():
    yield
    cleanup()

def test_counter():
    count = Signal(0)
    
    def Counter():
        return f"""
        <div>
            <span data-testid="count">{count()}</span>
            <button onclick="count.set(count() + 1)">Increment</button>
        </div>
        """
    
    result = render(Counter)
    
    # Initial state
    assert result.getByTestId("count").text == "0"
    
    # Simulate click
    button = screen.getByRole("button")
    fireEvent.click(button)
    
    # Verify update (signals update synchronously)
    assert count() == 1
```

## Where to Find More

- `pynext/testing/client.py` - Main RTL-style API
- `pynext/testing/queries.py` - Query method implementations
- `pynext/testing/client_events.py` - Event firing
- `pynext/testing/mocks.py` - Mocking utilities
- `tests/unit/testing/` - Comprehensive test suite (225+ tests)

