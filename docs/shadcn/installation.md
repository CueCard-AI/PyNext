# Installation

> **Get started with PyNext ShadCN components in minutes**

---

## Quick Start

PyNext ShadCN components are built-in — no installation needed for basic usage:

```python
from pynext.shadcn import Button, Card, Input

def MyPage():
    return Card()[
        Input(placeholder="Enter your name"),
        Button()["Submit"]
    ]
```

That's it! Components work out of the box.

---

## Two Ways to Use Components

### Option 1: Direct Import (Recommended for most cases)

Import directly from `pynext.shadcn`:

```python
from pynext.shadcn import (
    Button,
    Card, CardHeader, CardTitle, CardContent,
    Input, Label,
    Dialog, DialogTrigger, DialogContent,
)
```

**Pros:**
- Zero setup
- Always up to date with PyNext
- Smaller project size

**Cons:**
- Can't customize component internals
- Styles are fixed

### Option 2: Copy for Customization

Copy components to your project using the CLI:

```bash
# Copy specific components
pynext ui add button card input

# Copy all components
pynext ui add --all
```

This creates editable files in `components/ui/`:

```
my-project/
└── components/
    └── ui/
        ├── __init__.py
        ├── button.py      # Fully editable
        ├── card.py
        └── input.py
```

Then import from your local copy:

```python
from components.ui import Button, Card, Input
```

**Pros:**
- Full control over styles and behavior
- Customize variants
- Add your own props

**Cons:**
- Won't get PyNext updates automatically
- More files to maintain

---

## Adding Tailwind CSS

ShadCN components use Tailwind CSS classes. Set up Tailwind for the full experience:

### 1. Add Dependencies

In `pynext.npm.txt`:

```
tailwindcss
autoprefixer
postcss
```

### 2. Create Config

Create `tailwind.config.js`:

```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.py",
    "./components/**/*.py",
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
}
```

### 3. Add CSS Variables

Create `public/globals.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 222.2 84% 4.9%;
    --primary: 222.2 47.4% 11.2%;
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
    --ring: 222.2 84% 4.9%;
    --radius: 0.5rem;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
    --popover: 222.2 84% 4.9%;
    --popover-foreground: 210 40% 98%;
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

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}
```

### 4. Include in Layout

In your `pages/layout.py`:

```python
from pynext import layout, head, link

@layout
def root_layout(children):
    return html()[
        head()[
            link(rel="stylesheet", href="/globals.css"),
        ],
        body()[
            children
        ]
    ]
```

---

## Available Components

After setup, you have access to:

### Basic
- `Button` - Click actions
- `Input`, `Label`, `Textarea` - Form inputs
- `Badge` - Status indicators
- `Avatar`, `AvatarImage`, `AvatarFallback` - User pictures
- `Separator` - Visual dividers

### Cards
- `Card`, `CardHeader`, `CardTitle`, `CardDescription`, `CardContent`, `CardFooter`

### Feedback
- `Alert`, `AlertTitle`, `AlertDescription`
- `AlertDialog` and sub-components

### Interactive
- `Dialog` and sub-components
- `DropdownMenu` and sub-components
- `Tabs`, `TabsList`, `TabsTrigger`, `TabsContent`
- `Accordion`, `AccordionItem`, `AccordionTrigger`, `AccordionContent`

### Form
- `Toggle`, `ToggleGroup`
- `Switch`
- `Checkbox`
- `RadioGroup`, `RadioGroupItem`

---

## Verifying Installation

Create a test page:

```python
# pages/ui-test.py
from pynext import page
from pynext.shadcn import Button, Card, CardHeader, CardTitle, CardContent

@page(title="UI Test")
def ui_test():
    return Card(class_="max-w-md mx-auto mt-8")[
        CardHeader()[
            CardTitle()["Installation Test"]
        ],
        CardContent()[
            Button()["If you see this styled, it works!"]
        ]
    ]
```

Run `pynext dev` and visit `/ui-test`.

---

## Next Steps

- [Theming](./theming.md) - Customize colors and fonts
- [Dark Mode](./dark-mode.md) - Add dark mode support
- [Components](./components/) - Individual component docs

