# Dark Mode

> **Add dark mode support to your PyNext application**

PyNext ShadCN components support dark mode out of the box using Tailwind's class-based dark mode strategy.

---

## How Dark Mode Works

```
┌─────────────────────────────────────────────────────────────────┐
│  User toggles dark mode                                          │
│                    │                                              │
│                    ▼                                              │
│  <html class="dark">  ← Class added to root element              │
│                    │                                              │
│                    ▼                                              │
│  CSS Variables Switch                                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ :root        { --background: 0 0% 100%;    /* white */ }  │  │
│  │ .dark        { --background: 222 84% 4.9%; /* dark */  }  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                    │                                              │
│                    ▼                                              │
│  All components automatically use dark colors!                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Setup

### 1. Configure Tailwind

```javascript
// tailwind.config.js
module.exports = {
  darkMode: ["class"],  // Enable class-based dark mode
  // ... rest of config
}
```

### 2. Add Dark Theme Variables

```css
/* globals.css */
@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --primary: 222.2 47.4% 11.2%;
    --primary-foreground: 210 40% 98%;
    /* ... other light mode vars ... */
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
    --primary: 210 40% 98%;
    --primary-foreground: 222.2 47.4% 11.2%;
    /* ... other dark mode vars ... */
  }
}
```

### 3. Create Theme Toggle

```python
from pynext import Signal, div, button
from pynext.shadcn import Button

# Theme state
is_dark = Signal(False)

def ThemeToggle():
    def toggle():
        is_dark.update(lambda x: not x)
    
    return Button(
        variant="ghost",
        size="icon",
        on_click=toggle,
    )[
        # Sun icon for light mode
        span(class_="dark:hidden")["☀️"],
        # Moon icon for dark mode  
        span(class_="hidden dark:block")["🌙"],
    ]
```

### 4. Apply to HTML Root

```python
from pynext import layout, html, body

@layout
def root_layout(children):
    theme_class = "dark" if is_dark.value else ""
    
    return html(class_=theme_class)[
        body(class_="bg-background text-foreground")[
            children
        ]
    ]
```

---

## Persisting Theme Choice

### Using localStorage

```python
from pynext import Signal, Effect

# Initialize from localStorage
is_dark = Signal(False)

# Client-side effect to sync with localStorage
@Effect
def sync_theme():
    # This runs on the client
    if is_dark.value:
        document.documentElement.classList.add("dark")
        localStorage.setItem("theme", "dark")
    else:
        document.documentElement.classList.remove("dark")
        localStorage.setItem("theme", "light")
```

Add this script to your layout for initial load:

```python
@layout
def root_layout(children):
    init_script = """
    (function() {
        const theme = localStorage.getItem('theme');
        if (theme === 'dark' || (!theme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
            document.documentElement.classList.add('dark');
        }
    })();
    """
    
    return html()[
        head()[
            script()[init_script],  # Run before render to prevent flash
        ],
        body()[children]
    ]
```

---

## System Preference Detection

Respect the user's OS preference:

```python
def ThemeToggle():
    """Theme toggle with system preference support."""
    
    # Three states: light, dark, system
    theme = Signal("system")  
    
    def set_theme(value):
        theme.set(value)
        # Apply immediately
        if value == "dark":
            document.documentElement.classList.add("dark")
        elif value == "light":
            document.documentElement.classList.remove("dark")
        else:  # system
            if window.matchMedia("(prefers-color-scheme: dark)").matches:
                document.documentElement.classList.add("dark")
            else:
                document.documentElement.classList.remove("dark")
    
    return div(class_="flex gap-1")[
        Button(
            variant="ghost" if theme.value != "light" else "default",
            size="sm",
            on_click=lambda: set_theme("light"),
        )["☀️"],
        Button(
            variant="ghost" if theme.value != "dark" else "default",
            size="sm",
            on_click=lambda: set_theme("dark"),
        )["🌙"],
        Button(
            variant="ghost" if theme.value != "system" else "default",
            size="sm",
            on_click=lambda: set_theme("system"),
        )["💻"],
    ]
```

---

## Component-Level Dark Mode

Components automatically adapt, but you can add custom dark styles:

```python
from pynext.tw import cn

def CustomCard(children):
    return div(class_=cn(
        # Light mode
        "bg-white border-gray-200 shadow-sm",
        # Dark mode
        "dark:bg-gray-800 dark:border-gray-700 dark:shadow-gray-900/20",
        # Shared
        "rounded-lg border p-4",
    ))[children]
```

### Using `tw` Builder

```python
from pynext.tw import tw

card_styles = tw.bg_white.dark.bg_gray_800.rounded_lg.border.p_4
# → "bg-white dark:bg-gray-800 rounded-lg border p-4"
```

---

## Complete Dark Theme

Here's a complete dark theme CSS:

```css
.dark {
  /* Backgrounds */
  --background: 222.2 84% 4.9%;
  --foreground: 210 40% 98%;
  
  /* Cards & Popovers */
  --card: 222.2 84% 4.9%;
  --card-foreground: 210 40% 98%;
  --popover: 222.2 84% 4.9%;
  --popover-foreground: 210 40% 98%;
  
  /* Primary (inverted for dark) */
  --primary: 210 40% 98%;
  --primary-foreground: 222.2 47.4% 11.2%;
  
  /* Secondary */
  --secondary: 217.2 32.6% 17.5%;
  --secondary-foreground: 210 40% 98%;
  
  /* Muted */
  --muted: 217.2 32.6% 17.5%;
  --muted-foreground: 215 20.2% 65.1%;
  
  /* Accent */
  --accent: 217.2 32.6% 17.5%;
  --accent-foreground: 210 40% 98%;
  
  /* Destructive */
  --destructive: 0 62.8% 30.6%;
  --destructive-foreground: 210 40% 98%;
  
  /* Borders & Inputs */
  --border: 217.2 32.6% 17.5%;
  --input: 217.2 32.6% 17.5%;
  --ring: 212.7 26.8% 83.9%;
}
```

---

## Preventing Flash

To prevent a flash of wrong theme on page load:

### Option 1: Blocking Script

```html
<script>
  // Run synchronously before anything renders
  (function() {
    const theme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    if (theme === 'dark' || (!theme && prefersDark)) {
      document.documentElement.classList.add('dark');
    }
  })();
</script>
```

### Option 2: Cookie-Based

Set a cookie on the server and read it during SSR:

```python
from pynext import get_cookies

@layout
def root_layout(children):
    cookies = get_cookies()
    theme = cookies.get("theme", "light")
    
    return html(class_="dark" if theme == "dark" else "")[
        body()[children]
    ]
```

---

## Images for Dark Mode

Swap images based on theme:

```python
def Logo():
    return div()[
        # Light mode logo
        img(
            src="/logo-dark.svg",  # Dark logo on light bg
            class_="block dark:hidden",
        ),
        # Dark mode logo
        img(
            src="/logo-light.svg",  # Light logo on dark bg
            class_="hidden dark:block",
        ),
    ]
```

Or use CSS to invert:

```python
img(
    src="/logo.svg",
    class_="dark:invert dark:brightness-150",
)
```

---

## Testing Dark Mode

### In Development

Add a toggle to quickly switch:

```python
def DevThemeToggle():
    """Quick toggle for development."""
    return div(class_="fixed bottom-4 right-4 z-50")[
        Button(
            on_click="document.documentElement.classList.toggle('dark')",
            variant="outline",
        )["Toggle Dark"]
    ]
```

### In Tests

```python
def test_dark_mode_button():
    """Button should have correct dark mode styles."""
    from pynext.shadcn import Button
    
    btn = Button()["Click"]
    html = btn.render()
    
    # Check dark mode classes are present
    assert "dark:bg-" in html or "dark:" in html
```

---

## Related

- [Theming](./theming.md) - Custom color schemes
- [Installation](./installation.md) - Initial setup
- [Tailwind Integration](../ui/TAILWIND.md) - Using dark: prefix

