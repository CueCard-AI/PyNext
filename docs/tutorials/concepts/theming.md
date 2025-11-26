# Theming

> **Create custom themes and implement dark mode**

Learn how to build a themeable design system with CSS variables, dark mode, and brand customization using PyNext's built-in theme module.

---

## What You'll Learn

- CSS variable-based theming
- Dark mode with PyNext's theme module
- Brand color customization
- Theme persistence
- Dynamic theme switching

---

## The PyNext Approach

PyNext provides a `pynext.theme` module that handles dark mode without writing JavaScript:

```python
from pynext.theme import (
    ThemeProvider,    # Wraps app with theme context
    ThemeScript,      # Prevents flash on page load  
    ThemeToggle,      # Ready-to-use toggle button
    ThemeSwitcher,    # Dropdown with options
    use_theme,        # Hook to access theme state
)
```

---

## CSS Variable Foundation

ShadCN components use CSS variables for theming:

```css
/* public/styles.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    /* Light theme */
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    
    --primary: 199 89% 48%;
    --primary-foreground: 210 40% 98%;
    
    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;
    
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    
    --accent: 210 40% 96.1%;
    --accent-foreground: 222.2 47.4% 11.2%;
    
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 199 89% 48%;
    
    --radius: 0.5rem;
  }

  .dark {
    /* Dark theme */
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
    
    --primary: 199 89% 48%;
    --primary-foreground: 222.2 47.4% 11.2%;
    
    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;
    
    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;
    
    --accent: 217.2 32.6% 17.5%;
    --accent-foreground: 210 40% 98%;
    
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;
    
    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 199 89% 48%;
  }
}
```

---

## Tailwind Configuration

Reference CSS variables in Tailwind:

```javascript
// tailwind.config.js
module.exports = {
  darkMode: ["class"],  // Use .dark class
  theme: {
    extend: {
      colors: {
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
};
```

---

## Setting Up Dark Mode

### 1. Add ThemeScript to Head

Prevent the flash of wrong theme by adding the script to `<head>`:

```python
from pynext.theme import ThemeScript

@layout
def root_layout(children):
    return html()[
        head()[
            # This MUST be first to prevent flash
            ThemeScript(),
            
            title()["My App"],
            link(rel="stylesheet", href="/styles.css"),
        ],
        body()[
            # Wrap with ThemeProvider
            ThemeProvider()[
                children
            ],
        ],
    ]
```

### 2. Add Theme Toggle

Use the built-in toggle button:

```python
from pynext.theme import ThemeToggle

def Navbar():
    return nav(class_="flex items-center justify-between p-4")[
        Logo(),
        
        # Simple toggle
        ThemeToggle(),
    ]
```

Or use the dropdown with system option:

```python
from pynext.theme import ThemeSwitcher

def Navbar():
    return nav(class_="flex items-center justify-between p-4")[
        Logo(),
        
        # Dropdown with Light/Dark/System options
        ThemeSwitcher(),
    ]
```

### 3. Access Theme State

For custom logic, use the `use_theme` hook:

```python
from pynext.theme import use_theme

# Get the theme signal
theme = use_theme()

# Read current mode
current_mode = theme()  # "light", "dark", or "system"

# Set mode
theme.set("dark")

# Toggle
def toggle_theme():
    current = theme()
    theme.set("dark" if current == "light" else "light")

# Cycle through all modes
def cycle_theme():
    modes = ["light", "dark", "system"]
    current = theme()
    idx = modes.index(current)
    theme.set(modes[(idx + 1) % len(modes)])
```

---

## How PyNext Theme Works

PyNext's theme module automatically handles:

1. **Flash Prevention**: Inline script runs before any content
2. **System Preference**: Respects `prefers-color-scheme`
3. **Persistence**: Stores in localStorage automatically
4. **Cross-Tab Sync**: Changes reflect in all tabs
5. **Zero JavaScript**: You write Python only

```
                                                 
   ┌─────────────────────────────────────────┐   
   │              Browser                     │   
   ├─────────────────────────────────────────┤   
   │                                          │   
   │  1. HTML starts loading                  │   
   │     ↓                                    │   
   │  2. ThemeScript runs (inline, blocking)  │   
   │     - Reads localStorage                 │   
   │     - Checks system preference           │   
   │     - Adds .dark class if needed         │   
   │     ↓                                    │   
   │  3. CSS loads (sees .dark class)         │   
   │     - Applies correct variables          │   
   │     ↓                                    │   
   │  4. Content renders (no flash!)          │   
   │     ↓                                    │   
   │  5. Hydration connects theme runtime     │   
   │     - Toggle buttons work                │   
   │     - System preference listening        │   
   │                                          │   
   └─────────────────────────────────────────┘   
```

---

## Brand Themes

Create custom brand themes beyond dark/light:

```css
/* Brand: Ocean */
.theme-ocean {
  --primary: 199 89% 48%;        /* Cyan */
  --primary-foreground: 210 40% 98%;
  --ring: 199 89% 48%;
}

/* Brand: Forest */
.theme-forest {
  --primary: 142 76% 36%;        /* Green */
  --primary-foreground: 210 40% 98%;
  --ring: 142 76% 36%;
}

/* Brand: Sunset */
.theme-sunset {
  --primary: 25 95% 53%;         /* Orange */
  --primary-foreground: 210 40% 98%;
  --ring: 25 95% 53%;
}

/* Brand: Royal */
.theme-royal {
  --primary: 262 83% 58%;        /* Purple */
  --primary-foreground: 210 40% 98%;
  --ring: 262 83% 58%;
}
```

### Theme Selector

```python
from pynext import Signal
from pynext.core.client import use_storage

# Persist brand theme
brand_theme = use_storage("brand-theme", default="ocean")

THEMES = [
    {"id": "ocean", "name": "Ocean", "color": "#0ea5e9"},
    {"id": "forest", "name": "Forest", "color": "#22c55e"},
    {"id": "sunset", "name": "Sunset", "color": "#f97316"},
    {"id": "royal", "name": "Royal", "color": "#8b5cf6"},
]

def ThemeSelector():
    return div(class_="flex gap-2")[
        [
            button(
                class_=cn(
                    "w-8 h-8 rounded-full border-2 transition-transform",
                    "ring-2 ring-offset-2 scale-110" if brand_theme() == t["id"] else "hover:scale-105",
                ),
                style=f"background-color: {t['color']}",
                onclick=lambda t=t: select_brand_theme(t["id"]),
                aria_label=f"Select {t['name']} theme",
            )
            for t in THEMES
        ]
    ]

def select_brand_theme(theme_id: str):
    """
    Change brand theme.
    
    This uses use_storage so the theme persists across sessions.
    """
    brand_theme.set(theme_id)
```

---

## Color System Tips

### Semantic Color Names

Use semantic names, not literal colors:

```css
/* ✗ Don't do this */
--blue-500: 199 89% 48%;
--text-black: 0 0% 0%;

/* ✓ Do this */
--primary: 199 89% 48%;
--foreground: 222.2 84% 4.9%;
```

### Foreground Colors

Every background color needs a foreground:

```css
--primary: 199 89% 48%;
--primary-foreground: 210 40% 98%;  /* Readable on primary */

--muted: 210 40% 96.1%;
--muted-foreground: 215.4 16.3% 46.9%;  /* Readable on muted */
```

### Testing Contrast

Use the Tailwind classes to test:

```python
div(class_="bg-primary text-primary-foreground")["Should be readable"]
div(class_="bg-muted text-muted-foreground")["Should also be readable"]
div(class_="bg-destructive text-destructive-foreground")["And this too"]
```

---

## Complete Example

```python
"""
Full theme setup example
"""

from pynext import html, head, body, div, nav, main
from pynext.theme import (
    ThemeProvider,
    ThemeScript,
    ThemeToggle,
    use_theme,
)
from pynext.shadcn import Button

@layout
def root_layout(children):
    return html(class_="h-full")[
        head()[
            # 1. Flash prevention FIRST
            ThemeScript(),
            
            title()["TaskFlow"],
            meta(charset="utf-8"),
            meta(name="viewport", content="width=device-width, initial-scale=1"),
            link(rel="stylesheet", href="/styles.css"),
        ],
        body(class_="h-full bg-background text-foreground")[
            # 2. Wrap with ThemeProvider
            ThemeProvider()[
                nav(class_="border-b px-4 py-3 flex items-center justify-between")[
                    Logo(),
                    div(class_="flex items-center gap-2")[
                        # 3. Add toggle
                        ThemeToggle(),
                    ],
                ],
                main(class_="p-6")[
                    children
                ],
            ],
        ],
    ]


def Logo():
    return div(class_="font-bold text-xl")["TaskFlow"]


# In a settings page, you might have more control
def ThemeSettings():
    """Settings page theme section."""
    theme = use_theme()
    
    return div(class_="space-y-4")[
        h2(class_="text-lg font-semibold")["Appearance"],
        
        div(class_="grid grid-cols-3 gap-4")[
            ThemeCard("light", "☀️", "Light", theme),
            ThemeCard("dark", "🌙", "Dark", theme),
            ThemeCard("system", "💻", "System", theme),
        ],
    ]


def ThemeCard(mode: str, icon: str, label: str, theme):
    is_active = theme() == mode
    
    return button(
        class_=cn(
            "p-4 rounded-lg border-2 text-center transition-all",
            "border-primary bg-primary/5" if is_active else "border-transparent hover:border-muted",
        ),
        onclick=lambda: theme.set(mode),
    )[
        div(class_="text-3xl mb-2")[icon],
        div(class_="font-medium")[label],
    ]
```

---

## Summary

| Feature | Module |
|---------|--------|
| Flash prevention | `ThemeScript` in `<head>` |
| Theme context | `ThemeProvider` wrapper |
| Simple toggle | `ThemeToggle` button |
| Full control | `ThemeSwitcher` dropdown |
| Programmatic | `use_theme()` hook |
| Persistence | Automatic (localStorage) |
| System sync | Automatic |

**Key Points:**
- Put `ThemeScript` first in `<head>`
- Wrap app in `ThemeProvider`
- Use CSS variables for all colors
- Test both light and dark modes
- Consider system preference users

---

## Next Steps

- [Keyboard Shortcuts](./keyboard-shortcuts.md) - Add power-user navigation
- [Component Patterns](./component-patterns.md) - Build reusable components
- [State Management](./state-management.md) - Handle complex state
