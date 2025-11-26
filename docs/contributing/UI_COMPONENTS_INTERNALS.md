# UI Components Internals

> **How PyNext's interactive components work under the hood — from Python to browser interactivity**

This document explains the architecture of PyNext's UI component system, including how Python components become interactive in the browser.

---

## Overview

### What Problem Does This Solve?

PyNext UI components need to:
1. Render as HTML on the server (for SEO and fast first paint)
2. Become interactive in the browser (for user interaction)
3. Work without writing JavaScript

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      THE COMPONENT LIFECYCLE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. PYTHON (Server)                                                          │
│     Dialog()[...]                                                            │
│          ↓                                                                   │
│  2. HTML RENDER                                                              │
│     <div data-pynext-dialog data-pynext-dialog-open="false">...</div>        │
│          ↓                                                                   │
│  3. BROWSER RECEIVES                                                         │
│     Static HTML displayed immediately                                        │
│          ↓                                                                   │
│  4. JAVASCRIPT HYDRATION                                                     │
│     PyNext.initDialog(element)                                               │
│     - Adds click handlers                                                    │
│     - Sets up focus trap                                                     │
│     - Manages open/close state                                               │
│          ↓                                                                   │
│  5. INTERACTIVE                                                              │
│     User clicks trigger → Dialog opens!                                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## The `data-pynext-*` Attribute System

### How It Works

Every interactive component renders with special attributes that tell JavaScript what to do:

```html
<!-- Dialog component rendered HTML -->
<div 
  data-pynext-dialog           <!-- "I am a dialog" -->
  data-pynext-dialog-open="false"  <!-- "I am currently closed" -->
>
  <button data-pynext-dialog-trigger>  <!-- "Click me to open" -->
    Open
  </button>
  <div data-pynext-dialog-content>     <!-- "This is the dialog content" -->
    <h2 data-pynext-dialog-title>Title</h2>
    <p data-pynext-dialog-description>Description</p>
  </div>
</div>
```

### Attribute Types

| Pattern | Purpose | Example |
|---------|---------|---------|
| `data-pynext-[component]` | Marks component root | `data-pynext-dialog` |
| `data-pynext-[component]-[role]` | Marks child elements | `data-pynext-dialog-trigger` |
| `data-pynext-[component]-[state]` | Tracks state | `data-pynext-dialog-open="true"` |

---

## Component Initialization

### The Initialization Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      COMPONENT INITIALIZATION                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. PAGE LOADS                                                               │
│     DOMContentLoaded event fires                                             │
│          ↓                                                                   │
│  2. SCAN FOR COMPONENTS                                                      │
│     document.querySelectorAll('[data-pynext-dialog]')                        │
│     document.querySelectorAll('[data-pynext-dropdown]')                      │
│     document.querySelectorAll('[data-pynext-tabs]')                          │
│     ... etc for all component types                                          │
│          ↓                                                                   │
│  3. INITIALIZE EACH                                                          │
│     For each found element:                                                  │
│       - Check if already initialized (skip if so)                            │
│       - Call component-specific init function                                │
│       - Mark as initialized                                                  │
│          ↓                                                                   │
│  4. OBSERVE FOR DYNAMIC CONTENT                                              │
│     MutationObserver watches for new components                              │
│     Added via signals, server actions, etc.                                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### JavaScript Implementation

```javascript
// ui/loader.js

const COMPONENTS = {
  dialog: () => import('./dialog.js'),
  dropdown: () => import('./dropdown.js'),
  tabs: () => import('./tabs.js'),
  accordion: () => import('./accordion.js'),
  // ... etc
};

async function initializeComponents(root = document) {
  for (const [name, loader] of Object.entries(COMPONENTS)) {
    const elements = root.querySelectorAll(`[data-pynext-${name}]`);
    
    if (elements.length > 0) {
      // Lazy load the component module
      const module = await loader();
      
      for (const el of elements) {
        if (!el._pynextInitialized) {
          module.init(el);
          el._pynextInitialized = true;
        }
      }
    }
  }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  initializeComponents();
});

// Watch for dynamically added components
const observer = new MutationObserver((mutations) => {
  for (const mutation of mutations) {
    for (const node of mutation.addedNodes) {
      if (node.nodeType === Node.ELEMENT_NODE) {
        initializeComponents(node);
      }
    }
  }
});

observer.observe(document.body, { childList: true, subtree: true });
```

---

## Focus Management

### Why Focus Management Matters

Accessibility requires proper focus handling:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FOCUS MANAGEMENT                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  When Dialog opens:                                                          │
│  1. Save current focused element                                             │
│  2. Move focus into dialog                                                   │
│  3. Trap focus (Tab cycles within dialog)                                    │
│  4. Block focus on elements outside                                          │
│                                                                              │
│  When Dialog closes:                                                         │
│  1. Release focus trap                                                       │
│  2. Restore focus to saved element                                           │
│                                                                              │
│  ┌─────────────────────────────────────────┐                                │
│  │                PAGE                      │                                │
│  │  [Button]  [Input]  [Link]              │                                │
│  │                                          │                                │
│  │  ┌────────────────────────────────┐     │                                │
│  │  │         DIALOG                 │     │                                │
│  │  │  ┌─────┐ ┌─────┐ ┌───────┐    │     │                                │
│  │  │  │Close│ │Input│ │Confirm│    │     │                                │
│  │  │  └─────┘ └─────┘ └───────┘    │     │                                │
│  │  │    ↑       ↓        ↓    ↑    │     │                                │
│  │  │    └───────┴────────┴────┘    │     │                                │
│  │  │         Tab cycles here       │     │                                │
│  │  └────────────────────────────────┘     │                                │
│  └─────────────────────────────────────────┘                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Implementation

```javascript
// ui/core.js

/**
 * Get all focusable elements within a container
 */
function getFocusableElements(container) {
  const selector = [
    'a[href]',
    'button:not([disabled])',
    'input:not([disabled])',
    'select:not([disabled])',
    'textarea:not([disabled])',
    '[tabindex]:not([tabindex="-1"])',
  ].join(', ');
  
  return [...container.querySelectorAll(selector)];
}

/**
 * Trap focus within a container
 */
function trapFocus(container) {
  const focusable = getFocusableElements(container);
  const firstFocusable = focusable[0];
  const lastFocusable = focusable[focusable.length - 1];
  
  container.addEventListener('keydown', (e) => {
    if (e.key !== 'Tab') return;
    
    if (e.shiftKey) {
      // Shift+Tab: if on first, go to last
      if (document.activeElement === firstFocusable) {
        e.preventDefault();
        lastFocusable.focus();
      }
    } else {
      // Tab: if on last, go to first
      if (document.activeElement === lastFocusable) {
        e.preventDefault();
        firstFocusable.focus();
      }
    }
  });
}
```

---

## Example: Dialog Component

### Python Component

```python
# pynext/shadcn/dialog.py

def Dialog(*children, open=False, on_open_change=None, **props):
    """Dialog component that becomes interactive in browser."""
    
    return div(
        data_pynext_dialog="",
        data_pynext_dialog_open=str(open).lower(),
        **props
    )[children]

def DialogTrigger(*children, **props):
    return button(
        data_pynext_dialog_trigger="",
        type="button",
        **props
    )[children]

def DialogContent(*children, **props):
    return div(
        data_pynext_dialog_content="",
        role="dialog",
        aria_modal="true",
        **props
    )[children]
```

### Rendered HTML

```html
<div data-pynext-dialog data-pynext-dialog-open="false">
  <button data-pynext-dialog-trigger type="button">
    Open Dialog
  </button>
  <div data-pynext-dialog-content role="dialog" aria-modal="true" 
       style="display: none;">
    <h2>Dialog Title</h2>
    <p>Dialog content here</p>
    <button>Close</button>
  </div>
</div>
```

### JavaScript Runtime

```javascript
// ui/dialog.js

import { getFocusableElements, trapFocus } from './core.js';

export function init(root) {
  const trigger = root.querySelector('[data-pynext-dialog-trigger]');
  const content = root.querySelector('[data-pynext-dialog-content]');
  const overlay = root.querySelector('[data-pynext-dialog-overlay]');
  
  let previouslyFocused = null;
  
  function open() {
    previouslyFocused = document.activeElement;
    
    root.setAttribute('data-pynext-dialog-open', 'true');
    content.style.display = '';
    if (overlay) overlay.style.display = '';
    
    // Focus first focusable element
    const focusable = getFocusableElements(content);
    if (focusable.length) focusable[0].focus();
    
    // Trap focus
    trapFocus(content);
    
    // Prevent body scroll
    document.body.style.overflow = 'hidden';
  }
  
  function close() {
    root.setAttribute('data-pynext-dialog-open', 'false');
    content.style.display = 'none';
    if (overlay) overlay.style.display = 'none';
    
    // Restore focus
    if (previouslyFocused) previouslyFocused.focus();
    
    // Restore body scroll
    document.body.style.overflow = '';
  }
  
  // Trigger click → open
  trigger?.addEventListener('click', open);
  
  // Close button click → close
  content.querySelectorAll('[data-pynext-dialog-close]').forEach(btn => {
    btn.addEventListener('click', close);
  });
  
  // Overlay click → close
  overlay?.addEventListener('click', close);
  
  // Escape key → close
  content.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') close();
  });
}
```

---

## Accessibility Considerations

### ARIA Attributes

Each component must include proper ARIA attributes:

| Component | Required ARIA |
|-----------|---------------|
| Dialog | `role="dialog"`, `aria-modal="true"`, `aria-labelledby` |
| Dropdown | `role="menu"`, `role="menuitem"`, `aria-expanded` |
| Tabs | `role="tablist"`, `role="tab"`, `aria-selected` |
| Accordion | `aria-expanded`, `aria-controls` |
| Tooltip | `role="tooltip"`, `aria-describedby` |

### Keyboard Support

| Component | Keys |
|-----------|------|
| Dialog | Escape to close, Tab to navigate |
| Dropdown | Arrow keys, Enter, Escape |
| Tabs | Arrow keys to switch, Enter to select |
| Accordion | Enter/Space to toggle |
| Combobox | Arrow keys, Enter, Escape, typing |

---

## Adding New Components

### Step 1: Python Component

```python
# pynext/shadcn/my_component.py

def MyComponent(*children, **props):
    return div(
        data_pynext_my_component="",
        **props
    )[children]

def MyComponentTrigger(*children, **props):
    return button(
        data_pynext_my_component_trigger="",
        **props
    )[children]
```

### Step 2: JavaScript Runtime

```javascript
// runtime/ui/my_component.js

export function init(root) {
  const trigger = root.querySelector('[data-pynext-my-component-trigger]');
  
  trigger?.addEventListener('click', () => {
    // Handle click
  });
  
  // Add keyboard support
  root.addEventListener('keydown', (e) => {
    // Handle keys
  });
}
```

### Step 3: Register in Loader

```javascript
// runtime/ui/loader.js

const COMPONENTS = {
  // ... existing
  'my-component': () => import('./my_component.js'),
};
```

### Step 4: Add Tests

```python
# tests/unit/test_my_component.py

def test_my_component_renders():
    html = render(MyComponent()["Content"])
    assert 'data-pynext-my-component' in html
```

---

## Common Patterns

### State via Data Attributes

```javascript
// Reading state
const isOpen = root.getAttribute('data-pynext-dialog-open') === 'true';

// Writing state
root.setAttribute('data-pynext-dialog-open', 'true');

// CSS can react to state
// [data-pynext-dialog-open="true"] .content { display: block; }
```

### Event Delegation

```javascript
// Instead of adding listeners to each item...
root.addEventListener('click', (e) => {
  const item = e.target.closest('[data-pynext-dropdown-item]');
  if (item) {
    handleItemClick(item);
  }
});
```

### Cleanup on Disconnect

```javascript
// For components that might be removed
const cleanup = [];

cleanup.push(
  addEventListener(document, 'click', handleOutsideClick)
);

// Later, when component is removed
cleanup.forEach(fn => fn());
```

---

## Debugging Tips

### Browser DevTools

```javascript
// Find all PyNext components
document.querySelectorAll('[data-pynext-dialog]')

// Check component state
element.getAttribute('data-pynext-dialog-open')

// Manually trigger
element._pynextOpen?.()
```

### Debug Mode

```javascript
// Enable verbose logging
__pynext__.debug = true;

// Console output:
// [PyNext Dialog] Opening dialog #1
// [PyNext Dialog] Focus trapped
// [PyNext Dialog] Escape pressed, closing
```

---

## Key Files

| File | Purpose |
|------|---------|
| `pynext/shadcn/*.py` | Python component definitions |
| `pynext/runtime/ui/*.js` | JavaScript runtime for each component |
| `pynext/runtime/ui/core.js` | Shared utilities |
| `pynext/runtime/ui/loader.js` | Component discovery and initialization |

