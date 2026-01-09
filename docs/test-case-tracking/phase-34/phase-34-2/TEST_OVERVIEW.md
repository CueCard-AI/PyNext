# Phase 34.2: CSS Runtime & Styling - Test Overview

## Summary

| Metric | Value |
|--------|-------|
| Total Tests | 188 |
| Test Files | 7 |
| Coverage Areas | 6 |

## Test Files

| File | Tests | Coverage |
|------|-------|----------|
| `test_342_style_properties.py` | 35 | Direct style property access |
| `test_342_styles_dict.py` | 25 | Dictionary-style `el.styles` access |
| `test_342_css_variables.py` | 25 | CSS custom properties helpers |
| `test_342_computed_styles.py` | 25 | getComputedStyle & matchMedia |
| `test_342_classList.py` | 20 | classList operations & helpers |
| `test_342_animation.py` | 20 | Web Animations API |
| `test_342_css_parity.py` | 38 | Integration mini-apps |

---

## Test Categories

### 1. Style Properties (35 tests)

Tests for direct `element.style.*` property access:

- **Display & Visibility** (5): display, visibility, opacity, pointerEvents, zIndex
- **Positioning** (5): position, top, left, inset, float
- **Box Model** (5): width, height, margin, padding, border, boxSizing
- **Background & Color** (5): backgroundColor, color, backgroundImage, filter
- **Flexbox** (5): flexDirection, justifyContent, alignItems, gap, flex
- **Transform & Animation** (5): transform, transition, animation, willChange
- **Vendor Prefixes** (3): webkitTransform, WebkitBackdropFilter, mozTransform
- **cssText & Length** (2): cssText, style.length

### 2. Dictionary-Style Access (25 tests)

Tests for `StylesProxy` Pythonic interface:

- **Basic Get/Set** (5): getitem, setitem, CSS vars, delitem, contains
- **Bulk Operations** (5): update, update with CSS vars, clear, len, iter
- **Kebab-Case** (5): background-color, border-radius, flex-direction, etc.
- **Get Method** (3): get, get with default, to_dict
- **Keys/Values/Items** (4): keys, values, items, create_styles
- **setProperty** (3): setProperty, with priority, removeProperty

### 3. CSS Variables (25 tests)

Tests for CSS custom property helpers:

- **set_css_var** (5): basic, with dashes, on element, complex value, number
- **get_css_var** (5): basic, with dashes, on element, assignment, expression
- **remove_css_var** (3): basic, with dashes, on element
- **set_theme** (5): basic, full, dark, on element, empty
- **get_theme** (3): basic, single, on element
- **toggle_theme** (4): basic, force dark, force light, result

### 4. Computed Styles (25 tests)

Tests for `window.getComputedStyle` and `matchMedia`:

- **Basic getComputedStyle** (8): basic, property, chained, multiple, font, transform
- **Pseudo-Elements** (5): ::before, ::after, content, background
- **getPropertyValue** (5): basic, CSS var, kebab-case, root var, chained
- **matchMedia** (7): basic, matches, dark mode, reduced motion, media property

### 5. classList Operations (20 tests)

Tests for classList and class helpers:

- **classList Basic** (8): add, add multiple, remove, toggle, toggle force, contains, replace
- **classes() Helper** (6): strings, tuple conditional, dict conditional, mixed, list, None
- **Style Utils Helpers** (6): toggle_class, add_classes, remove_classes, has_class, replace_class, set_styles

### 6. Web Animations API (20 tests)

Tests for `element.animate()` and helpers:

- **element.animate()** (8): basic, options, await finished, multiple keyframes, delay, iterations, infinite, getAnimations
- **Animation Control** (6): pause, play, cancel, reverse, playbackRate, currentTime
- **Animation Helpers** (6): fade_in, fade_out, slide_in, scale_in, shake, pulse

### 7. Integration Mini-Apps (15 tests)

End-to-end styling scenarios:

- **Theme System** (5): complete setup, toggle button, scoped theme, read/apply, system detection
- **Responsive Styling** (3): layout switch, class toggle, responsive sidebar
- **Animations** (4): modal open, notification, form validation, button feedback
- **Dynamic Styling** (3): style calculator, conditional classes, style composition

---

## Implementation Files

| File | Type | Lines | Purpose |
|------|------|-------|---------|
| `pynext/client/window.py` | New | ~300 | Window interface & getComputedStyle |
| `pynext/client/styles.py` | New | ~280 | StylesProxy dict-like access |
| `pynext/client/css_vars.py` | New | ~270 | CSS variable helpers |
| `pynext/client/style_utils.py` | New | ~250 | Class & style utilities |
| `pynext/client/animation.py` | New | ~450 | Animation types & helpers |
| `pynext/client/dom.py` | Extended | +150 | CSSStyleDeclaration + animate() |
| `pynext/transpiler/dom.py` | Extended | +20 | Window & animation methods |
| `pynext/transpiler/emitter.py` | Extended | +10 | window.* passthrough |

---

## Running Tests

```bash
# Run all Phase 34.2 tests
pytest tests/unit/client/test_342_*.py -v

# Run specific test file
pytest tests/unit/client/test_342_style_properties.py -v

# Run with coverage
pytest tests/unit/client/test_342_*.py --cov=pynext.client --cov-report=term-missing
```

---

## Key Assertions

All tests verify:

1. **Passthrough**: DOM APIs pass through unchanged
2. **No Runtime**: No `__py.` prefix in output
3. **Correct Syntax**: Valid JavaScript generated
4. **Keyword Args**: Python kwargs → JS options object
5. **CSS Properties**: All properties accessible

Example test pattern:

```python
def test_style_display(self):
    """el.style.display should pass through unchanged."""
    code = 'el.style.display = "flex"'
    result = transpile(code)
    assert 'el.style.display = "flex"' in result
    assert "__py." not in result
```

