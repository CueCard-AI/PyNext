# Transitions & Navigation

PyNext provides smooth page transitions using the **View Transitions API** and SPA-style client-side navigation.

## Table of Contents

- [Overview](#overview)
- [Link Component](#link-component)
- [Transition Types](#transition-types)
- [Programmatic Navigation](#programmatic-navigation)
- [View Transitions API](#view-transitions-api)
- [Prefetching](#prefetching)
- [Custom Transitions](#custom-transitions)
- [History Management](#history-management)
- [Performance](#performance)
- [API Reference](#api-reference)

---

## Overview

### How It Works

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    NAVIGATION FLOW                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. USER CLICKS LINK                                                    │
│  ───────────────────                                                    │
│                                                                         │
│  User clicks → Link intercepted → Navigation starts                     │
│                                                                         │
│  2. FETCH NEW PAGE                                                      │
│  ─────────────────                                                      │
│                                                                         │
│  Check cache → Fetch if needed → Store in cache                         │
│                                                                         │
│  3. VIEW TRANSITION                                                     │
│  ──────────────────                                                     │
│                                                                         │
│  ┌─────────────┐         ┌─────────────┐                               │
│  │  Old Page   │ ──────▶ │  New Page   │                               │
│  │  (fade out) │  300ms  │  (fade in)  │                               │
│  └─────────────┘         └─────────────┘                               │
│                                                                         │
│  4. UPDATE & REINITIALIZE                                               │
│  ────────────────────────                                               │
│                                                                         │
│  Update DOM → Push history → Reinitialize components                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Link Component

The `Link` component provides declarative navigation with transitions.

### Basic Usage

```python
from pynext import Link

# Simple link
Link(href="/about")["About Us"]

# With transition
Link(href="/dashboard", transition="slide-left")["Dashboard"]

# Without prefetch
Link(href="/admin", prefetch=False)["Admin Panel"]
```

### Link Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `href` | `str` | required | Destination URL |
| `transition` | `TransitionType \| str` | `"fade"` | Transition animation |
| `prefetch` | `bool` | `True` | Prefetch on hover |
| `replace` | `bool` | `False` | Replace history entry |

### Rendered HTML

```html
<a href="/dashboard" 
   data-pynext-link="true" 
   data-transition="slide-left"
   data-prefetch="hover">
  Dashboard
</a>
```

---

## Transition Types

PyNext includes 8 built-in transition types:

| Type | Description | Use Case |
|------|-------------|----------|
| `none` | No animation | Instant navigation |
| `fade` | Crossfade (default) | General navigation |
| `slide-left` | Slide from right | Forward navigation |
| `slide-right` | Slide from left | Back navigation |
| `slide-up` | Slide from bottom | Modal/overlay open |
| `slide-down` | Slide from top | Modal/overlay close |
| `scale` | Scale in/out | Focus change |
| `morph` | Morph between states | Shared elements |

### Using Transition Types

```python
from pynext import Link, TransitionType

# Using enum
Link(href="/next", transition=TransitionType.SLIDE_LEFT)["Next"]

# Using string
Link(href="/prev", transition="slide-right")["Previous"]
```

---

## Programmatic Navigation

Navigate from JavaScript or event handlers:

### Navigate Script

```python
from pynext import navigate_script, button

# Generate navigation JavaScript
script = navigate_script("/dashboard", transition="slide-left")

# Use in event handler
button(onclick=navigate_script("/settings"))["Settings"]
```

### Back & Forward

```python
from pynext import back_script, forward_script

# Back button with transition
button(onclick=back_script(transition="slide-right"))["← Back"]

# Forward button
button(onclick=forward_script())["Forward →"]
```

### From Client-Side JavaScript

```javascript
// Navigate to URL
await __pynext__.navigate("/dashboard", {
    transition: "slide-left",
    replace: false
});

// Go back with transition
__pynext__.back({ transition: "slide-right" });

// Go forward
__pynext__.forward({ transition: "slide-left" });
```

---

## View Transitions API

PyNext uses the native **View Transitions API** for smooth animations.

### Browser Support

The View Transitions API is supported in:
- Chrome 111+
- Edge 111+
- Opera 97+
- Safari 18+ (partial)

PyNext provides a fallback for unsupported browsers.

### How View Transitions Work

```javascript
// PyNext automatically wraps updates in startViewTransition
document.startViewTransition(() => {
    // Update the DOM
    updatePage(newHTML);
});
```

### Element-Level Transitions

Use the `@transition` decorator for shared element transitions:

```python
from pynext import transition, div, img

@transition("product-image")
def ProductImage(product):
    return img(
        src=product.image,
        alt=product.name
    )

# Both pages have the same transition name
# The browser animates between them
```

### CSS View Transition Names

```python
from pynext import div

# Direct style attribute
div(style="view-transition-name: hero-section")[
    "This element will animate"
]
```

---

## Prefetching

### Hover Prefetching (Default)

Links prefetch their destination when hovered:

```python
# Prefetch enabled by default
Link(href="/products")["Products"]

# 50ms delay to prevent accidental prefetch
# Then fetches /products HTML in background
```

### Visibility Prefetching

Prefetch when link becomes visible:

```python
# In HTML
a(href="/important", data_prefetch="visible")["Important"]
```

### Idle Prefetching

Prefetch when browser is idle:

```python
a(href="/background", data_prefetch="idle")["Background"]
```

### Disable Prefetching

```python
Link(href="/admin", prefetch=False)["Admin"]
```

### Manual Prefetch

```javascript
// Prefetch a specific URL
__pynext__.prefetch("/dashboard");
```

---

## Custom Transitions

### Register Custom Transition

```python
from pynext import TransitionConfig, TransitionType, get_transition_manager

manager = get_transition_manager()

# Register custom transition
manager.register_transition(
    "zoom-rotate",
    TransitionConfig(
        type="zoom-rotate",
        duration=400,
        easing="cubic-bezier(0.4, 0, 0.2, 1)",
        custom_css="""
            @keyframes pynext-zoom-rotate-in {
                from { transform: scale(0) rotate(-180deg); opacity: 0; }
                to { transform: scale(1) rotate(0deg); opacity: 1; }
            }
        """
    )
)

# Use in Link
Link(href="/special", transition="zoom-rotate")["Special Page"]
```

### Transition CSS

Include the built-in transition CSS:

```python
from pynext import get_transition_style_tag

# In your layout
def Layout(children):
    return html()[
        head()[
            get_transition_style_tag(),  # Include transition CSS
        ],
        body()[children]
    ]
```

---

## History Management

### Push vs Replace

```python
# Push new entry (default)
Link(href="/page2")["Go to Page 2"]

# Replace current entry
Link(href="/step2", replace=True)["Next Step"]
```

### History State

The navigation stores state in history:

```javascript
// State stored with each navigation
{
    url: "/dashboard",
    transition: "slide-left"
}

// Access in popstate
window.addEventListener('popstate', (e) => {
    console.log(e.state.url);
    console.log(e.state.transition);
});
```

### Navigation Events

Listen for navigation events:

```javascript
// Navigation starting
document.addEventListener('pynext:navigation:start', (e) => {
    console.log('Navigating from', e.detail.fromUrl, 'to', e.detail.toUrl);
});

// Navigation complete
document.addEventListener('pynext:navigation:complete', (e) => {
    console.log('Navigated to', e.detail.toUrl);
});

// Navigation error
document.addEventListener('pynext:navigation:error', (e) => {
    console.error('Navigation failed:', e.detail.error);
});
```

---

## Performance

### Benchmarks

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    NAVIGATION PERFORMANCE                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  LINK RENDERING:                                                        │
│  Simple link:           3.5μs                                           │
│  With transition:       3.6μs                                           │
│  With content:          4.3μs                                           │
│                                                                         │
│  CSS GENERATION:                                                        │
│  Transition CSS:        40ns (24.8M ops/sec)                            │
│  Style tag:             147ns                                           │
│                                                                         │
│  SCRIPT GENERATION:                                                     │
│  Navigate script:       320ns                                           │
│  Back/Forward:          176ns                                           │
│                                                                         │
│  NAVIGATION DATA:                                                       │
│  50 routes:             4.4μs                                           │
│  100 routes:            ~8μs                                            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Page Cache

PyNext caches fetched pages for instant back/forward:

```javascript
// Cache configuration
const config = {
    cacheMaxSize: 20,  // Max cached pages
    showLoadingAfter: 150,  // Show loading after 150ms
};

// Clear cache manually
__pynext__.clearNavigationCache();

// Check stats
console.log(__pynext__.getNavigationStats());
// { currentUrl: "/dashboard", cachedPages: 5, prefetching: 0 }
```

---

## API Reference

### Link Component

```python
def Link(
    href: str,
    transition: Union[TransitionType, str] = TransitionType.FADE,
    prefetch: bool = True,
    replace: bool = False,
    **attrs
) -> Element
```

### TransitionType Enum

```python
class TransitionType(Enum):
    NONE = "none"
    FADE = "fade"
    SLIDE_LEFT = "slide-left"
    SLIDE_RIGHT = "slide-right"
    SLIDE_UP = "slide-up"
    SLIDE_DOWN = "slide-down"
    SCALE = "scale"
    MORPH = "morph"
```

### TransitionConfig

```python
@dataclass
class TransitionConfig:
    type: Union[TransitionType, str] = TransitionType.FADE
    duration: int = 300
    easing: str = "ease-in-out"
    delay: int = 0
    use_view_transitions: bool = True
    fallback: Optional[str] = None
    custom_css: Optional[str] = None
```

### Navigation Functions

```python
def navigate_script(
    to: str,
    transition: Union[TransitionType, str] = TransitionType.FADE,
    replace: bool = False,
) -> str

def back_script(
    transition: Union[TransitionType, str] = TransitionType.SLIDE_RIGHT
) -> str

def forward_script(
    transition: Union[TransitionType, str] = TransitionType.SLIDE_LEFT
) -> str
```

### JavaScript API

```javascript
// Navigation
__pynext__.navigate(url, options)  // Promise<void>
__pynext__.back(options)           // void
__pynext__.forward(options)        // void

// Prefetching
__pynext__.prefetch(url)           // Promise<void>

// Cache
__pynext__.clearNavigationCache()  // void
__pynext__.getNavigationStats()    // Object
```

---

## Related Documentation

- [Code Splitting](./CODE_SPLITTING.md) - Lazy loading and route chunks
- [Routing](./ROUTING.md) - File-based routing
- [Streaming & Suspense](./STREAMING_SUSPENSE.md) - Progressive rendering

