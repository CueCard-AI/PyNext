# Theme Management Guide

> **Complete guide to dark mode and theming in PyNext**

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Understanding Dark Mode](#understanding-dark-mode)
3. [The Flash Problem](#the-flash-problem)
4. [Setup Step-by-Step](#setup-step-by-step)
5. [Theme Components](#theme-components)
6. [Programmatic Control](#programmatic-control)
7. [CSS Variables](#css-variables)
8. [Brand Themes](#brand-themes)
9. [Troubleshooting](#troubleshooting)

---

## Quick Start

```python
from pynext.theme import ThemeScript, ThemeProvider, ThemeToggle

@layout
def root_layout(children):
    return html()[
        head()[
            ThemeScript(),  # Prevents flash
            link(rel="stylesheet", href="/styles.css"),
        ],
        body()[
            ThemeProvider()[
                ThemeToggle(),  # Toggle button
                children,
            ],
        ],
    ]
```

That's it! Dark mode works with no JavaScript.

---

## Understanding Dark Mode

### First Principles: How Dark Mode Works

Dark mode is just CSS that activates when a class is present:

```css
/* Light mode (default) */
body {
  background: white;
  color: black;
}

/* Dark mode (when .dark class is on <html>) */
.dark body {
  background: black;
  color: white;
}
```

The challenge: **When should `.dark` be added?**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Dark Mode Sources (Priority Order)                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. User's Explicit Choice                                                  │
│     ───────────────────────                                                 │
│     User clicked "Dark Mode" → stored in localStorage                       │
│     Priority: HIGHEST (user explicitly chose)                               │
│                                                                             │
│  2. System Preference                                                       │
│     ─────────────────────                                                   │
│     User's OS is set to dark mode                                           │
│     Detected via: prefers-color-scheme: dark                                │
│     Priority: Use if no explicit choice                                     │
│                                                                             │
│  3. Default                                                                 │
│     ─────────                                                               │
│     If nothing else, use light mode                                         │
│                                                                             │
│                                                                             │
│  Decision Flow:                                                             │
│  ──────────────                                                             │
│                                                                             │
│    localStorage has theme?                                                  │
│         │                                                                   │
│    ┌────┴────┐                                                              │
│    │         │                                                              │
│   YES       NO                                                              │
│    │         │                                                              │
│    ▼         ▼                                                              │
│  Use it   Check system preference                                           │
│             │                                                               │
│        ┌────┴────┐                                                          │
│        │         │                                                          │
│      Dark      Light                                                        │
│        │         │                                                          │
│        ▼         ▼                                                          │
│    Use dark   Use light                                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## The Flash Problem

### What Is the Flash?

When a user with dark mode preference loads your page:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Timeline WITHOUT Flash Prevention                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  0ms          50ms         100ms        150ms        200ms                  │
│   │            │            │            │            │                     │
│   ▼            ▼            ▼            ▼            ▼                     │
│                                                                             │
│  ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐                      │
│  │      │   │      │   │      │   │▓▓▓▓▓▓│   │▓▓▓▓▓▓│                      │
│  │ HTML │   │ CSS  │   │ CSS  │   │ DARK │   │ DARK │                      │
│  │loads │   │loads │   │paints│   │ MODE │   │ MODE │                      │
│  │      │   │      │   │WHITE │   │      │   │      │                      │
│  └──────┘   └──────┘   └──────┘   └──────┘   └──────┘                      │
│                            │            │                                   │
│                            │            └── JavaScript finally runs,        │
│                            │                reads localStorage,             │
│                            │                adds .dark class                │
│                            │                                                │
│                            └── USER SEES WHITE FLASH! 😫                    │
│                                                                             │
│  The Problem:                                                               │
│  JavaScript runs AFTER CSS paints the page.                                 │
│  By the time JS adds .dark, user already saw white.                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### The Solution: Inline Script in `<head>`

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Timeline WITH Flash Prevention                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  0ms          50ms         100ms        150ms        200ms                  │
│   │            │            │            │            │                     │
│   ▼            ▼            ▼            ▼            ▼                     │
│                                                                             │
│  ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐                      │
│  │      │   │INLINE│   │ CSS  │   │▓▓▓▓▓▓│   │▓▓▓▓▓▓│                      │
│  │ HTML │   │SCRIPT│   │loads │   │ DARK │   │ DARK │                      │
│  │loads │   │ runs │   │sees  │   │ MODE │   │ MODE │                      │
│  │      │   │      │   │.dark │   │      │   │      │                      │
│  └──────┘   └──────┘   └──────┘   └──────┘   └──────┘                      │
│                │            │                                               │
│                │            └── CSS sees .dark already there,               │
│                │                paints dark immediately!                    │
│                │                                                            │
│                └── Inline script runs BEFORE CSS,                           │
│                    adds .dark class to <html>                               │
│                                                                             │
│  NO FLASH! 🎉                                                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

This is exactly what `ThemeScript()` does!

---

## Setup Step-by-Step

### Step 1: Add ThemeScript to Head

```python
from pynext.theme import ThemeScript

@layout
def root_layout(children):
    return html()[
        head()[
            # MUST be first thing in head!
            ThemeScript(),
            
            # Then your other stuff
            title()["My App"],
            link(rel="stylesheet", href="/styles.css"),
        ],
        body()[
            children
        ],
    ]
```

**Why first?** The script must run before ANY CSS loads.

### What ThemeScript Generates

```html
<script>
(function() {
  try {
    var mode = localStorage.getItem('theme');
    var prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    var isDark = mode === 'dark' || (mode === 'system' && prefersDark) || (!mode && prefersDark);
    if (isDark) {
      document.documentElement.classList.add('dark');
      document.documentElement.style.colorScheme = 'dark';
    }
  } catch (e) {}
})();
</script>
```

This is an **inline, synchronous, blocking** script. It runs immediately!

### Step 2: Wrap App in ThemeProvider

```python
from pynext.theme import ThemeProvider

@layout
def root_layout(children):
    return html()[
        head()[
            ThemeScript(),
            # ...
        ],
        body()[
            # Wrap your entire app
            ThemeProvider()[
                children
            ],
        ],
    ]
```

**What ThemeProvider does:**
- Creates the theme signal
- Hydrates the theme.js runtime
- Listens for system preference changes

### Step 3: Add Theme Toggle

```python
from pynext.theme import ThemeToggle

def Header():
    return header()[
        Logo(),
        nav()[...],
        ThemeToggle(),  # Adds a toggle button
    ]
```

### Step 4: Configure CSS

Make sure your CSS has dark mode styles:

```css
/* tailwind.config.js should have: */
module.exports = {
  darkMode: 'class',  /* Use .dark class, not media query */
}
```

```css
/* Your CSS variables */
:root {
  --background: 0 0% 100%;
  --foreground: 0 0% 0%;
}

.dark {
  --background: 0 0% 10%;
  --foreground: 0 0% 100%;
}
```

---

## Theme Components

### ThemeScript

```python
from pynext.theme import ThemeScript

# Default (uses "theme" key)
ThemeScript()

# Custom storage key
ThemeScript(storage_key="color-mode")
```

### ThemeProvider

```python
from pynext.theme import ThemeProvider

# Default settings
ThemeProvider()[
    children
]

# Custom settings
ThemeProvider(
    default="system",     # "light", "dark", or "system"
    storage_key="theme",  # localStorage key
)[
    children
]
```

### ThemeToggle

Simple button that cycles through themes:

```python
from pynext.theme import ThemeToggle

# Default (icon only)
ThemeToggle()

# With label
ThemeToggle(show_label=True)

# Custom class
ThemeToggle(class_="my-custom-class")
```

**What it renders:**
```html
<button onclick="__pynext__.theme.cycle()">
  <span class="dark:hidden">🌙</span>  <!-- Shows in light mode -->
  <span class="hidden dark:inline">☀️</span>  <!-- Shows in dark mode -->
</button>
```

### ThemeSwitcher

Dropdown with all three options:

```python
from pynext.theme import ThemeSwitcher

ThemeSwitcher()
```

**What it renders:**
- A dropdown button
- Three options: Light, Dark, System
- Clicking sets the theme

---

## Programmatic Control

### Using use_theme()

```python
from pynext.theme import use_theme

# Get the theme signal
theme = use_theme()

# Read current mode
current = theme()  # "light", "dark", or "system"

# Set mode
theme.set("dark")
theme.set("light")
theme.set("system")
```

### Common Patterns

```python
# Toggle between light and dark
def toggle():
    current = theme()
    theme.set("dark" if current == "light" else "light")

# Cycle through all modes
def cycle():
    modes = ["light", "dark", "system"]
    current = theme()
    idx = modes.index(current)
    next_idx = (idx + 1) % len(modes)
    theme.set(modes[next_idx])

# Check effective theme (resolves "system")
def get_effective():
    mode = theme()
    if mode == "system":
        # Would need to check system preference
        # theme.js handles this automatically
        pass
    return mode
```

### Keyboard Shortcut for Theme

```python
from pynext.keyboard import on_key_sequence
from pynext.theme import use_theme

@on_key_sequence("t d")
def toggle_dark():
    """Toggle dark mode with T then D."""
    theme = use_theme()
    current = theme()
    theme.set("dark" if current == "light" else "light")
```

---

## CSS Variables

### How CSS Variables Work

```css
/* Define variables */
:root {
  --background: 0 0% 100%;  /* HSL values without hsl() */
  --foreground: 222.2 84% 4.9%;
}

/* Use variables */
body {
  background-color: hsl(var(--background));
  color: hsl(var(--foreground));
}
```

### ShadCN-Compatible Variables

```css
@layer base {
  :root {
    /* Background colors */
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    
    /* Card colors */
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    
    /* Primary colors */
    --primary: 222.2 47.4% 11.2%;
    --primary-foreground: 210 40% 98%;
    
    /* Secondary colors */
    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;
    
    /* Muted colors */
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    
    /* Accent colors */
    --accent: 210 40% 96.1%;
    --accent-foreground: 222.2 47.4% 11.2%;
    
    /* Destructive colors */
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    
    /* Border and input */
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 222.2 84% 4.9%;
    
    /* Radius */
    --radius: 0.5rem;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
    
    --primary: 210 40% 98%;
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
    --ring: 212.7 26.8% 83.9%;
  }
}
```

### Tailwind Configuration

```javascript
// tailwind.config.js
module.exports = {
  darkMode: ['class'],
  theme: {
    extend: {
      colors: {
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
      },
    },
  },
}
```

---

## Brand Themes

### Beyond Light/Dark

You can have multiple brand themes:

```css
/* Default theme */
:root {
  --primary: 222.2 47.4% 11.2%;  /* Dark blue */
}

/* Ocean theme */
.theme-ocean {
  --primary: 199 89% 48%;  /* Cyan */
}

/* Forest theme */
.theme-forest {
  --primary: 142 76% 36%;  /* Green */
}

/* Sunset theme */
.theme-sunset {
  --primary: 25 95% 53%;  /* Orange */
}
```

### Theme Selector Component

```python
from pynext.core.client import use_storage
from pynext import div, button
from pynext.tw import cn

# Persist brand theme
brand_theme = use_storage("brand-theme", default="default")

THEMES = [
    {"id": "default", "name": "Default", "color": "#1e293b"},
    {"id": "ocean", "name": "Ocean", "color": "#0ea5e9"},
    {"id": "forest", "name": "Forest", "color": "#22c55e"},
    {"id": "sunset", "name": "Sunset", "color": "#f97316"},
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
                onclick=lambda t=t: brand_theme.set(t["id"]),
                aria_label=f"Select {t['name']} theme",
            )
            for t in THEMES
        ]
    ]
```

---

## Troubleshooting

### Flash Still Happening?

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Debugging Flash Issues                                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. Is ThemeScript FIRST in <head>?                                         │
│     ─────────────────────────────────                                       │
│     head()[                                                                 │
│       ThemeScript(),  # ← MUST be first!                                    │
│       title()["..."],                                                       │
│       link(...)                                                             │
│     ]                                                                       │
│                                                                             │
│  2. Is CSS using darkMode: 'class'?                                         │
│     ────────────────────────────────                                        │
│     // tailwind.config.js                                                   │
│     darkMode: ['class']  // NOT 'media'                                     │
│                                                                             │
│  3. Is .dark class targeting correct element?                               │
│     ──────────────────────────────────────────                              │
│     .dark body { ... }  // ✓ .dark on <html>                                │
│     body.dark { ... }   // ✗ .dark on <body>                                │
│                                                                             │
│  4. Any CSS transitions causing flash?                                      │
│     ─────────────────────────────────────                                   │
│     * { transition: all 0.3s; }  // ← Remove this!                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Theme Not Persisting?

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Debugging Persistence Issues                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. Check localStorage in DevTools:                                         │
│     ─────────────────────────────────                                       │
│     localStorage.getItem('theme')                                           │
│     // Should be "light", "dark", or "system"                               │
│                                                                             │
│  2. Is ThemeProvider wrapping your app?                                     │
│     ─────────────────────────────────────                                   │
│     body()[                                                                 │
│       ThemeProvider()[  # ← Need this!                                      │
│         children                                                            │
│       ]                                                                     │
│     ]                                                                       │
│                                                                             │
│  3. Storage key mismatch?                                                   │
│     ───────────────────────                                                 │
│     ThemeScript(storage_key="theme")                                        │
│     ThemeProvider(storage_key="theme")  // ← Must match!                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### System Preference Not Detected?

```python
# Make sure you're using "system" mode, not "light"
theme.set("system")  # This respects OS preference

# Check in browser console:
# window.matchMedia('(prefers-color-scheme: dark)').matches
```

---

## Summary

| Component | Purpose |
|-----------|---------|
| `ThemeScript()` | Prevents flash (put in `<head>`) |
| `ThemeProvider` | Wraps app, manages state |
| `ThemeToggle` | Button to toggle theme |
| `ThemeSwitcher` | Dropdown with all options |
| `use_theme()` | Programmatic control |

**Setup Order:**
1. `ThemeScript()` first in `<head>`
2. `ThemeProvider` wrapping `<body>` content
3. `ThemeToggle` wherever you want the button
4. CSS variables in your stylesheet

**Remember:**
- Always put `ThemeScript` FIRST in head
- Use Tailwind's `darkMode: 'class'`
- CSS variables should be in `:root` and `.dark`

