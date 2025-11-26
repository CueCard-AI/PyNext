# Theming

> **Customize colors, fonts, and styles to match your brand**

PyNext ShadCN components use CSS variables for theming, making it easy to customize the entire look with a few changes.

---

## How Theming Works

```
┌─────────────────────────────────────────────────────────────────┐
│                     CSS Variables (globals.css)                  │
│                                                                   │
│  :root {                                                          │
│    --primary: 222.2 47.4% 11.2%;     ← Your brand color          │
│    --background: 0 0% 100%;           ← Page background          │
│    --radius: 0.5rem;                  ← Border radius            │
│  }                                                                │
│                                                                   │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Tailwind Config                              │
│                                                                   │
│  colors: {                                                        │
│    primary: "hsl(var(--primary))",    ← Maps to CSS var          │
│  }                                                                │
│                                                                   │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Components                                   │
│                                                                   │
│  Button(class_="bg-primary text-primary-foreground")             │
│                    ↑                                              │
│           Uses your custom colors!                                │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Theme Change

To change your primary color, edit ONE variable:

```css
/* globals.css */
:root {
  /* Change from default blue to purple */
  --primary: 270 50% 40%;          /* Purple hue */
  --primary-foreground: 0 0% 100%; /* White text on purple */
}
```

**That's it!** All buttons, links, and accents update automatically.

---

## Color System

### Semantic Colors

| Variable | Purpose | Example Usage |
|----------|---------|---------------|
| `--primary` | Main brand color | Buttons, links |
| `--secondary` | Supporting color | Secondary buttons |
| `--destructive` | Danger/error | Delete buttons, errors |
| `--muted` | Subtle backgrounds | Disabled states |
| `--accent` | Highlights | Hover states |

### Surface Colors

| Variable | Purpose |
|----------|---------|
| `--background` | Page background |
| `--foreground` | Default text |
| `--card` | Card backgrounds |
| `--popover` | Dropdown/modal backgrounds |

### Form Colors

| Variable | Purpose |
|----------|---------|
| `--input` | Input field borders |
| `--border` | General borders |
| `--ring` | Focus ring color |

---

## Pre-Made Themes

### Default (Zinc)

```css
:root {
  --background: 0 0% 100%;
  --foreground: 240 10% 3.9%;
  --primary: 240 5.9% 10%;
  --primary-foreground: 0 0% 98%;
  --secondary: 240 4.8% 95.9%;
  --secondary-foreground: 240 5.9% 10%;
  --muted: 240 4.8% 95.9%;
  --muted-foreground: 240 3.8% 46.1%;
  --accent: 240 4.8% 95.9%;
  --accent-foreground: 240 5.9% 10%;
  --destructive: 0 84.2% 60.2%;
  --destructive-foreground: 0 0% 98%;
  --border: 240 5.9% 90%;
  --input: 240 5.9% 90%;
  --ring: 240 5.9% 10%;
  --radius: 0.5rem;
}
```

### Blue

```css
:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  --primary: 221.2 83.2% 53.3%;
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
  --ring: 221.2 83.2% 53.3%;
}
```

### Green

```css
:root {
  --background: 0 0% 100%;
  --foreground: 240 10% 3.9%;
  --primary: 142.1 76.2% 36.3%;
  --primary-foreground: 355.7 100% 97.3%;
  --secondary: 240 4.8% 95.9%;
  --secondary-foreground: 240 5.9% 10%;
  --muted: 240 4.8% 95.9%;
  --muted-foreground: 240 3.8% 46.1%;
  --accent: 240 4.8% 95.9%;
  --accent-foreground: 240 5.9% 10%;
  --destructive: 0 84.2% 60.2%;
  --destructive-foreground: 0 0% 98%;
  --border: 240 5.9% 90%;
  --input: 240 5.9% 90%;
  --ring: 142.1 76.2% 36.3%;
}
```

### Orange

```css
:root {
  --background: 0 0% 100%;
  --foreground: 20 14.3% 4.1%;
  --primary: 24.6 95% 53.1%;
  --primary-foreground: 60 9.1% 97.8%;
  --secondary: 60 4.8% 95.9%;
  --secondary-foreground: 24 9.8% 10%;
  --muted: 60 4.8% 95.9%;
  --muted-foreground: 25 5.3% 44.7%;
  --accent: 60 4.8% 95.9%;
  --accent-foreground: 24 9.8% 10%;
  --destructive: 0 84.2% 60.2%;
  --destructive-foreground: 60 9.1% 97.8%;
  --border: 20 5.9% 90%;
  --input: 20 5.9% 90%;
  --ring: 24.6 95% 53.1%;
}
```

---

## Custom Fonts

### 1. Add Font Files

Place font files in `public/fonts/` or use a CDN.

### 2. Load in CSS

```css
/* globals.css */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
  --font-sans: 'Inter', system-ui, sans-serif;
}

body {
  font-family: var(--font-sans);
}
```

### 3. Configure Tailwind

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      fontFamily: {
        sans: ['var(--font-sans)'],
      },
    },
  },
}
```

---

## Border Radius

Control the roundness of all components:

```css
:root {
  --radius: 0.5rem;   /* Default: slightly rounded */
}

/* Options */
--radius: 0;         /* Sharp corners */
--radius: 0.25rem;   /* Subtle rounding */
--radius: 0.5rem;    /* Moderate (default) */
--radius: 0.75rem;   /* More rounded */
--radius: 1rem;      /* Very rounded */
```

Components use calculated values:
- `border-radius-lg`: `var(--radius)`
- `border-radius-md`: `calc(var(--radius) - 2px)`
- `border-radius-sm`: `calc(var(--radius) - 4px)`

---

## Creating Your Own Theme

### Step 1: Pick Your Colors

Start with your brand's primary color. Use an HSL color picker.

### Step 2: Generate Palette

For each color, you need:
- The main color (e.g., `--primary`)
- A contrasting foreground (e.g., `--primary-foreground`)

**Rule of thumb:** If the main color is dark, foreground should be light (and vice versa).

### Step 3: Apply Consistently

```css
:root {
  /* Your brand blue */
  --primary: 210 100% 50%;
  --primary-foreground: 0 0% 100%;
  
  /* Make ring match primary */
  --ring: 210 100% 50%;
  
  /* Secondary should complement */
  --secondary: 210 20% 95%;
  --secondary-foreground: 210 100% 20%;
}
```

### Step 4: Test All Components

Check your theme on:
- Buttons (all variants)
- Form inputs
- Cards
- Dialogs
- Error states

---

## Theme Switching (Multiple Themes)

### Define Themes

```css
/* globals.css */
:root, .theme-light {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  /* ... light theme ... */
}

.theme-dark {
  --background: 222.2 84% 4.9%;
  --foreground: 210 40% 98%;
  /* ... dark theme ... */
}

.theme-blue {
  --primary: 221.2 83.2% 53.3%;
  /* ... blue accents ... */
}

.theme-green {
  --primary: 142.1 76.2% 36.3%;
  /* ... green accents ... */
}
```

### Switch in Python

```python
from pynext import Signal

theme = Signal("theme-light")

def ThemeSwitcher():
    return div(class_=theme.value)[
        # Your app content
        select(onchange=lambda e: theme.set(e.target.value))[
            option(value="theme-light")["Light"],
            option(value="theme-dark")["Dark"],
            option(value="theme-blue")["Blue"],
            option(value="theme-green")["Green"],
        ]
    ]
```

---

## Related

- [Dark Mode](./dark-mode.md) - Specific dark mode setup
- [Installation](./installation.md) - Initial setup
- [Tailwind Integration](../ui/TAILWIND.md) - Using Tailwind utilities

