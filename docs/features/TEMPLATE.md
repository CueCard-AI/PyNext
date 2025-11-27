# Templates

Layouts that remount on every navigation - perfect for page transitions and state resets.

---

## The Problem (Why This Exists)

Layouts persist across navigation. When you go from `/about` to `/contact`, the layout stays mounted - great for performance, but sometimes you need:

- **Page transition animations** - fade, slide, or scale between pages
- **Reset component state** - clear forms, scroll position, or ephemeral data
- **Analytics tracking** - fire events on every route change
- **Enter/exit effects** - mount animations on each page load

### Layouts vs Templates

```
┌─────────────────────────────────────────────────────────┐
│                    LAYOUT                               │
│                                                         │
│   ┌─────────┐    ┌─────────┐    ┌─────────┐           │
│   │ Header  │    │ Header  │    │ Header  │ (same)    │
│   ├─────────┤ →  ├─────────┤ →  ├─────────┤           │
│   │ Page A  │    │ Page B  │    │ Page C  │ (swaps)   │
│   ├─────────┤    ├─────────┤    ├─────────┤           │
│   │ Footer  │    │ Footer  │    │ Footer  │ (same)    │
│   └─────────┘    └─────────┘    └─────────┘           │
│                                                         │
│   Layout STAYS - only page content changes              │
├─────────────────────────────────────────────────────────┤
│                    TEMPLATE                             │
│                                                         │
│   ┌─────────┐    ┌─────────┐    ┌─────────┐           │
│   │ ~~~~~~  │    │ ~~~~~~  │    │ ~~~~~~  │           │
│   │  Fade   │ →  │  Fade   │ →  │  Fade   │           │
│   │  Out    │    │  In     │    │  Out    │           │
│   └─────────┘    └─────────┘    └─────────┘           │
│                                                         │
│   Template REMOUNTS - entire wrapper recreated          │
└─────────────────────────────────────────────────────────┘
```

### Real-World Analogy

Think of a **slideshow presentation**:
- The **projector** (layout) stays on the whole time
- Each **slide** (template) fades out and the next fades in
- The transition effect happens between every slide

---

## First Principles: How Templates Work

### The Core Concept

Templates are wrappers that:
1. **Contain** page content like layouts do
2. **Remount** on every navigation (layouts persist)
3. **Animate** between old and new content with CSS transitions
4. **Reset** scroll position and component state

### Mental Model

```
┌─────────────────────────────────────────────────────────┐
│                  NAVIGATION FLOW                        │
│                                                         │
│   Step 1: Exit Animation                               │
│   ┌─────────────┐                                      │
│   │  Old Page   │ ──→ opacity: 0                       │
│   │  (fading)   │     transform: ...                   │
│   └─────────────┘                                      │
│          │                                              │
│          ▼                                              │
│   Step 2: Content Swap                                 │
│   ┌─────────────┐                                      │
│   │  New Page   │ ──→ innerHTML replaced               │
│   │  (hidden)   │     opacity: 0                       │
│   └─────────────┘                                      │
│          │                                              │
│          ▼                                              │
│   Step 3: Enter Animation                              │
│   ┌─────────────┐                                      │
│   │  New Page   │ ──→ opacity: 1                       │
│   │  (visible)  │     transform: none                  │
│   └─────────────┘                                      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Step-by-Step: What Happens During Navigation

1. **User clicks link** - Navigation intercepted by PyNext

2. **Exit animation starts**:
   ```css
   .template-exit {
       opacity: 0;
       transition: opacity 100ms ease-out;
   }
   ```

3. **Content replaced** - New page HTML swapped in via `innerHTML`

4. **Enter animation plays**:
   ```css
   .template-enter-active {
       opacity: 1;
       transition: opacity 100ms ease-out;
   }
   ```

5. **Scroll reset** (optional) - Window scrolls to top

6. **Hydration** - New page's interactivity initialized

---

## Quick Start (Copy-Paste Ready)

### Basic Template

```python
# pages/(app)/template.py

from pynext import template, div

@template
def app_template(children):
    return div(class_="page-wrapper")[
        children
    ]
```

**What this does:**
- Line 4: `@template` marks this as a template (remounts on navigation)
- Line 5: `children` contains the page content
- Line 6: Wraps content in a div for the animation
- **Result**: Every page in `(app)` fades in/out on navigation

### Template with Custom Animation

```python
# pages/(marketing)/template.py

from pynext import template, div

@template(
    animate=True,      # Enable transitions
    duration=300,      # 300ms animation
    transition="slide-left",  # Slide effect
    reset_scroll=True, # Scroll to top
)
def marketing_template(children):
    return div(class_="marketing-content")[
        children
    ]
```

**What this does:**
- `animate=True`: Enables CSS transitions
- `duration=300`: Animation takes 300ms
- `transition="slide-left"`: New page slides in from right
- `reset_scroll=True`: Scrolls to top after navigation
- **Result**: Pages slide in from the right with 300ms animation

---

## Complete API Reference

### `@template` Decorator

**What it does**: Creates a template that remounts on every navigation.

**When to use**: When you need page transitions or state reset between routes.

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `animate` | `bool` | `True` | Enable CSS transitions |
| `duration` | `int` | `200` | Animation duration in milliseconds |
| `reset_scroll` | `bool` | `True` | Scroll to top after navigation |
| `transition` | `str` or `TransitionType` | `"fade"` | Transition effect type |
| `easing` | `str` | `"ease-out"` | CSS easing function |

**Transition Types**:

| Type | Value | Description |
|------|-------|-------------|
| Fade | `"fade"` | Opacity fade in/out |
| Slide Left | `"slide-left"` | Slides in from right, out to left |
| Slide Right | `"slide-right"` | Slides in from left, out to right |
| Slide Up | `"slide-up"` | Slides in from bottom, out to top |
| Slide Down | `"slide-down"` | Slides in from top, out to bottom |
| Scale | `"scale"` | Scales up on enter, down on exit |
| None | `"none"` | No animation (instant swap) |

**Example**:

```python
from pynext import template

# Basic - defaults
@template
def simple(children):
    return children

# Custom animation
@template(transition="slide-up", duration=500)
def slide_up(children):
    return children

# Instant swap (no animation)
@template(animate=False)
def instant(children):
    return children
```

---

### `Template.render(children)`

**What it does**: Renders the template with page content.

**Returns**: HTML string with data attributes for client-side handling.

**Example output**:

```html
<div 
    data-pynext-template="marketing_template"
    data-animate="true"
    data-duration="200"
    data-reset-scroll="true"
    data-transition="fade"
    data-easing="ease-out"
>
    <!-- Page content here -->
</div>
```

---

### `Template.get_css()`

**What it does**: Generates CSS for the template's transitions.

**Returns**: CSS string to include in page head.

**Example**:

```python
@template(transition="fade", duration=300)
def my_template(children):
    return children

css = my_template.get_css()
# Returns CSS with .template-exit, .template-enter, etc.
```

---

### Convenience Decorators

**`@fade_template(duration=200)`**:

```python
from pynext import fade_template

@fade_template(duration=400)
def my_fade(children):
    return children
```

**`@slide_template(direction="left", duration=300)`**:

```python
from pynext import slide_template

@slide_template(direction="right")
def my_slide(children):
    return children
```

**`@scale_template(duration=200)`**:

```python
from pynext import scale_template

@scale_template()
def my_scale(children):
    return children
```

**`@static_template()`** - No animation:

```python
from pynext import static_template

@static_template()
def instant_swap(children):
    return children
```

---

## Real-World Patterns

### Pattern 1: App-Wide Page Transitions

**Scenario**: All app pages should fade in/out smoothly.

```python
# pages/(app)/template.py

from pynext import template, div

@template(duration=200, transition="fade")
def app_transitions(children):
    return div(class_="app-page")[
        children
    ]
```

**Combined with layout**:

```
pages/
├── (app)/
│   ├── layout.py      # Persistent sidebar (never remounts)
│   ├── template.py    # Page transitions (remounts every nav)
│   ├── dashboard/page.py
│   └── settings/page.py
```

**Result**:
- Sidebar stays mounted (from layout)
- Main content fades between pages (from template)

---

### Pattern 2: Wizard/Multi-Step Form

**Scenario**: Multi-step form where each step slides in.

```python
# pages/(wizard)/template.py

from pynext import template, div

@template(
    transition="slide-left",
    duration=300,
    reset_scroll=False,  # Keep scroll position
)
def wizard_step(children):
    return div(class_="wizard-container")[
        children
    ]
```

```
pages/
├── (wizard)/
│   ├── layout.py          # Progress bar
│   ├── template.py        # Slide transition
│   ├── step-1/page.py     # → /step-1
│   ├── step-2/page.py     # → /step-2
│   └── step-3/page.py     # → /step-3
```

**What happens**:
- Progress bar persists (layout)
- Each step slides in from right
- Scroll position preserved between steps

---

### Pattern 3: Analytics Tracking

**Scenario**: Fire analytics event on every page view.

```python
# pages/(tracked)/template.py

from pynext import template, div, script

@template
def tracked_template(children):
    return div()[
        children,
        # This script runs on every mount
        script()[
            """
            // Fires on every page navigation
            if (typeof gtag !== 'undefined') {
                gtag('event', 'page_view', {
                    page_path: window.location.pathname
                });
            }
            """
        ],
    ]
```

**Why template, not layout**:
- Layout script runs once at initial load
- Template script runs on every navigation

---

### Pattern 4: Reset Form State

**Scenario**: Clear form state when navigating away and back.

```python
# pages/(forms)/template.py

from pynext import template, div

@template(reset_scroll=True)  # Also scroll to top
def form_template(children):
    # Template remounts = all form state resets
    return div(class_="form-page")[
        children
    ]
```

**Without template** (using layout):
- Navigate away and back → form shows old values
- State persists in mounted components

**With template**:
- Navigate away and back → form is fresh
- Components remount → state resets

---

## How It Works Under the Hood

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                SERVER-SIDE                              │
│                                                         │
│   Template.render() outputs:                           │
│   <div data-pynext-template="name"                     │
│        data-animate="true"                             │
│        data-duration="200"                             │
│        ...>                                            │
│       {page content}                                   │
│   </div>                                               │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                CLIENT-SIDE (template.js)                │
│                                                         │
│   1. Navigation intercepted                            │
│   2. Fetch new page HTML                               │
│   3. Find template element                             │
│   4. Run exit animation (CSS transitions)              │
│   5. Swap innerHTML                                    │
│   6. Run enter animation                               │
│   7. Reset scroll (if enabled)                         │
│   8. Hydrate new content                               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### CSS Generation

Templates generate CSS like:

```css
[data-pynext-template="my_template"] {
    transition: opacity 200ms ease-out, 
                transform 200ms ease-out;
}

[data-pynext-template="my_template"].template-exit {
    opacity: 0;
}

[data-pynext-template="my_template"].template-enter {
    opacity: 0;
}

[data-pynext-template="my_template"].template-enter-active {
    opacity: 1;
}
```

### Why This is Better Than React/Next.js

| Aspect | React/Next.js | PyNext |
|--------|---------------|--------|
| Page transitions | Requires framer-motion (~30KB) | CSS-only (~1KB) |
| State reset | useEffect cleanup (complex) | Remount (simple) |
| Implementation | React reconciliation | Single innerHTML swap |
| Bundle size | Large animation library | Zero additional JS |

---

## Troubleshooting

### "Animation isn't playing"

**Check 1**: Is `animate=True`?

```python
# Wrong - animation disabled
@template(animate=False)

# Right
@template(animate=True)  # or just @template
```

**Check 2**: Is the CSS being applied?

```html
<!-- Should see data attributes -->
<div data-pynext-template="my_template" data-animate="true" ...>
```

**Check 3**: Is the JavaScript loaded?

```python
# In your layout, ensure runtime is included
script(src="/_pynext/runtime.js")
```

---

### "Page flashes during transition"

**Cause**: Enter animation starting before exit finishes.

**Fix**: Increase duration or use proper timing:

```python
@template(duration=300)  # Give enough time
```

---

### "Scroll jumps during navigation"

**Cause**: `reset_scroll=True` (default) scrolls to top.

**Fix**: Disable if you want to preserve scroll:

```python
@template(reset_scroll=False)
```

---

## Summary

**Key Takeaways**:

1. **Templates remount on navigation**, layouts persist
2. **Use templates for transitions** - fade, slide, scale effects
3. **State resets automatically** when template remounts
4. **CSS-only animations** - no JavaScript animation library needed

**When to Use Templates**:

| Need | Use Layout | Use Template |
|------|------------|--------------|
| Persistent navigation | ✓ | |
| Page transitions | | ✓ |
| Analytics on every page view | | ✓ |
| Reset form state on navigate | | ✓ |
| Shared header/footer | ✓ | |

**Next Steps**:

- [Error Pages](./ERROR_PAGES.md) - Custom 401/403/404 pages
- [Route Groups](./ROUTE_GROUPS.md) - Organize routes by section

