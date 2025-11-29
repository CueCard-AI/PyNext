# PWA: App Icons & Manifest

> Make your web app installable - just drop files, PyNext does the rest.

## The Problem

To make a web app installable (PWA), you need:

```
✗ Multiple icon sizes (192x192, 512x512)
✗ Correct icon formats
✗ manifest.json with proper structure
✗ Link tags in HTML head
✗ Meta tags for Apple devices
✗ Theme color configuration
```

**Next.js approach**: Create files manually, no auto-detection.

**PyNext approach**: Drop files in `public/`, everything is auto-detected.

---

## First Principles

### What is a PWA?

A Progressive Web App can be installed on devices like a native app:

```
┌────────────────────────────────────────────────────┐
│                  Browser Tab                        │
│  ┌──────────────────────────────────────────────┐  │
│  │  🌐 https://myapp.com      ☆ ⋮  [Install ↓]  │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│   User clicks "Install"                             │
│         ↓                                           │
│   Browser needs:                                    │
│   ├── manifest.json (app metadata)                  │
│   ├── Icon 192x192 (home screen)                    │
│   └── Icon 512x512 (splash screen)                  │
│                                                     │
└────────────────────────────────────────────────────┘
                    ↓
┌────────────────────────────────────────────────────┐
│                  Home Screen                        │
│                                                     │
│   📱  📧  📷  🛒  [Your App Icon]  ...              │
│                                                     │
│   App launches in standalone mode (no browser UI)   │
│                                                     │
└────────────────────────────────────────────────────┘
```

### What Icons Do You Need?

```
Icon Type           Size        Purpose
───────────────────────────────────────────────────
favicon.ico         16x16       Browser tab
icon-192.png        192x192     Home screen (required)
icon-512.png        512x512     Splash screen (required)
apple-icon.png      180x180     iOS home screen
og-image.png        1200x630    Social media sharing
```

---

## Quick Start

### Zero Config (Just Drop Files)

Create icons and drop them in `public/`:

```
public/
├── favicon.ico
├── icon-192.png
├── icon-512.png
└── apple-icon.png
```

That's it! PyNext auto-detects and generates all HTML tags.

### Generate Manifest

```bash
pynext manifest generate
```

Creates `public/manifest.json` automatically.

### Validate PWA

```bash
pynext pwa validate

[PyNext] PWA Validation:

  ✓ Manifest: Found
  ✓ Favicon: favicon.ico
  ✓ Icon 192x192: Found
  ✓ Icon 512x512: Found

  ✓ PWA requirements met!
```

---

## Icon Detection

### Automatic Detection

PyNext scans `public/` for these patterns:

| Pattern | Detected As |
|---------|-------------|
| `favicon.ico`, `favicon.png`, `favicon.svg` | Favicon |
| `icon.png`, `icon-192.png`, `icon-512.png` | App icons |
| `apple-icon.png`, `apple-touch-icon.png` | Apple icon |
| `og-image.png`, `og.png` | Open Graph |

Size is auto-detected from filename: `icon-192.png` → 192x192

### Check Detection

```bash
pynext icons detect

[PyNext] Detected Icons:

  ✓ Favicon: favicon.ico
  ✓ App Icons: 2
      - icon-192.png (192x192)
      - icon-512.png (512x512)
  ✓ Apple Icon: apple-icon.png
  ✓ OG Image: og-image.png
```

### Explicit Configuration

Override auto-detection with explicit config:

```python
# pynext.config.py
from pynext import AppIcons, Icon

icons = AppIcons(
    favicon="custom-favicon.ico",
    icons=[
        Icon("icons/app-192.png", size=192),
        Icon("icons/app-512.png", size=512, purpose="maskable"),
    ],
    apple_icon="icons/apple.png",
    og_image="images/social-preview.png",
)
```

---

## Icon Dataclass

### The `Icon` Class

```python
from pynext import Icon

icon = Icon(
    path="icon-192.png",     # File path (relative to public/)
    size=192,                # Size in pixels (auto-detected if None)
    type="image/png",        # MIME type (auto-detected)
    purpose="any",           # any | maskable | monochrome
)
```

### Size Auto-Detection

```python
# Size extracted from filename
Icon("icon-192.png")        # size = 192
Icon("icon-512.png")        # size = 512
Icon("apple-icon-180.png")  # size = 180
Icon("icon.png")            # size = None
```

### Icon Purposes

| Purpose | Description |
|---------|-------------|
| `"any"` | Standard icon (default) |
| `"maskable"` | Can be cropped to shape (recommended for Android) |
| `"monochrome"` | Single color, for theming |

```python
# Maskable icon for Android adaptive icons
Icon("icon-512.png", size=512, purpose="maskable")
```

---

## PWA Manifest

### Basic Manifest

```python
# pynext.config.py
from pynext import PWAManifest

manifest = PWAManifest(
    name="My Awesome App",
    theme_color="#3b82f6",
)
```

Generated `manifest.json`:

```json
{
  "name": "My Awesome App",
  "short_name": "My Awesome A",
  "start_url": "/",
  "display": "standalone",
  "theme_color": "#3b82f6",
  "background_color": "#ffffff",
  "icons": [
    {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"},
    {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"}
  ]
}
```

### Full Configuration

```python
from pynext import PWAManifest, ManifestIcon, Shortcut

manifest = PWAManifest(
    # Required
    name="Task Manager Pro",
    
    # Display
    short_name="Tasks",              # Max 12 chars (auto-generated)
    description="Manage your tasks efficiently",
    
    # Behavior
    start_url="/",                   # URL when app launches
    scope="/",                       # Navigation scope
    display="standalone",            # fullscreen/standalone/minimal-ui/browser
    orientation="any",               # any/portrait/landscape
    
    # Colors
    theme_color="#10b981",           # Browser chrome color
    background_color="#f3f4f6",      # Splash screen background
    
    # Icons (auto-detected if not provided)
    icons=[
        ManifestIcon("icon-192.png", sizes="192x192"),
        ManifestIcon("icon-512.png", sizes="512x512", purpose="maskable"),
    ],
    
    # Shortcuts (context menu actions)
    shortcuts=[
        Shortcut("New Task", "/tasks/new", description="Create a new task"),
        Shortcut("Today", "/today", description="View today's tasks"),
    ],
    
    # Categories
    categories=["productivity", "utilities"],
    
    # Language
    lang="en",
    dir="ltr",                       # ltr/rtl
)
```

### Display Modes

| Mode | Description |
|------|-------------|
| `"fullscreen"` | No browser UI, fills screen |
| `"standalone"` | App window, no URL bar (recommended) |
| `"minimal-ui"` | Minimal browser controls |
| `"browser"` | Regular browser tab |

### Shortcuts

Shortcuts appear in the app's context menu:

```python
from pynext import Shortcut

shortcuts = [
    Shortcut("New Task", "/tasks/new"),
    Shortcut("Search", "/search", icon="icon-search.png"),
    Shortcut("Settings", "/settings", description="App settings"),
]
```

---

## Convenience Functions

### `pwa_minimal`

Create a minimal manifest with sensible defaults:

```python
from pynext import pwa_minimal

# Just provide a name
manifest = pwa_minimal("My App")

# With theme color
manifest = pwa_minimal("My App", theme_color="#3b82f6")
```

### `pwa_full`

Create a full-featured manifest:

```python
from pynext import pwa_full, Shortcut

manifest = pwa_full(
    name="Task Manager",
    short_name="Tasks",
    theme_color="#10b981",
    shortcuts=[
        Shortcut("New", "/new"),
    ],
    categories=["productivity"],
)
```

### `create_icons`

Create icons with common configuration:

```python
from pynext.pwa.icons import create_icons

icons = create_icons(
    favicon="favicon.ico",
    icon_192="icon-192.png",
    icon_512="icon-512.png",
    apple_icon="apple-icon.png",
    maskable_512=True,  # Make 512 icon maskable
)
```

---

## CLI Commands

### Icon Commands

```bash
# Detect icons from public/
pynext icons detect

# Validate PWA icon requirements
pynext icons validate
```

### Manifest Commands

```bash
# Generate manifest.json
pynext manifest generate

# Generate to specific path
pynext manifest generate --output dist/manifest.json

# Preview without generating
pynext manifest preview
```

### PWA Validation

```bash
# Validate all PWA requirements
pynext pwa validate
```

---

## Generated HTML Tags

PyNext automatically injects these tags into your HTML:

```html
<!-- Favicon -->
<link rel="icon" href="/favicon.ico">

<!-- App Icons -->
<link rel="icon" type="image/png" sizes="192x192" href="/icon-192.png">
<link rel="icon" type="image/png" sizes="512x512" href="/icon-512.png">

<!-- Apple -->
<link rel="apple-touch-icon" href="/apple-icon.png">

<!-- PWA Manifest -->
<link rel="manifest" href="/manifest.json">

<!-- Theme -->
<meta name="theme-color" content="#3b82f6">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="My App">

<!-- Open Graph -->
<meta property="og:image" content="https://example.com/og-image.png">
```

---

## Real-World Examples

### E-commerce App

```python
# pynext.config.py
from pynext import pwa_full, Shortcut

manifest = pwa_full(
    name="ShopNow - Online Shopping",
    short_name="ShopNow",
    description="Shop the best deals online",
    theme_color="#f59e0b",
    background_color="#ffffff",
    shortcuts=[
        Shortcut("Search", "/search", icon="icon-search.png"),
        Shortcut("Cart", "/cart", icon="icon-cart.png"),
        Shortcut("Orders", "/orders", icon="icon-orders.png"),
    ],
    categories=["shopping", "lifestyle"],
)
```

### Task Manager

```python
from pynext import PWAManifest, ManifestIcon, Shortcut

manifest = PWAManifest(
    name="TaskFlow",
    short_name="Tasks",
    description="Elegant task management",
    theme_color="#10b981",
    background_color="#1f2937",
    display="standalone",
    icons=[
        ManifestIcon("icon-192.png", sizes="192x192"),
        ManifestIcon("icon-512.png", sizes="512x512", purpose="maskable"),
    ],
    shortcuts=[
        Shortcut("Add Task", "/new", description="Create a new task"),
        Shortcut("Today", "/today", description="Today's tasks"),
        Shortcut("Inbox", "/inbox", description="Unorganized tasks"),
    ],
    categories=["productivity"],
)
```

### Social App

```python
from pynext import pwa_full, Shortcut

manifest = pwa_full(
    name="Connect - Social Network",
    short_name="Connect",
    theme_color="#8b5cf6",
    shortcuts=[
        Shortcut("New Post", "/compose"),
        Shortcut("Messages", "/messages"),
        Shortcut("Notifications", "/notifications"),
    ],
    categories=["social"],
)
```

---

## Under the Hood

### Detection Flow

```
1. Startup
   ─────────
   IconDetector scans public/ directory
   
2. Pattern Matching
   ─────────────────
   Matches files against known patterns:
   - favicon.* → Favicon
   - icon-*.png → App icons (size from name)
   - apple-*.png → Apple icon
   - og-*.png → OG image
   
3. Size Detection
   ───────────────
   icon-192.png → size=192
   icon-512.png → size=512
   
4. Tag Generation
   ───────────────
   Generate <link> and <meta> tags
   Inject into HTML <head>
```

### Manifest Generation

```
1. Load Config
   ───────────
   Read PWAManifest from pynext.config.py
   
2. Merge Icons
   ────────────
   Config icons OR detected icons
   
3. Generate JSON
   ──────────────
   Build manifest.json structure
   
4. Serve/Write
   ────────────
   Serve at /manifest.json OR write to file
```

---

## Comparison with Next.js

| Feature | Next.js | PyNext |
|---------|---------|--------|
| Icon detection | None | Auto from public/ |
| Manifest | Static file only | Config + auto-generate |
| Size from filename | No | Yes |
| Shortcuts | Manual | Shortcut class |
| Validation | None | CLI command |
| Meta tags | Manual | Auto-generated |

---

## Troubleshooting

### PWA Not Installable

**Symptom**: No install prompt in browser.

**Check**:
1. Run `pynext pwa validate`
2. Ensure icon-192.png and icon-512.png exist
3. Ensure manifest.json is served

```bash
# Validate
pynext pwa validate

# Generate manifest if missing
pynext manifest generate
```

### Icons Not Detected

**Symptom**: `pynext icons detect` shows missing icons.

**Check**:
1. Files are in `public/` directory
2. Names match patterns: `icon-192.png`, `icon-512.png`
3. Files are not empty

### Manifest Not Loading

**Symptom**: Manifest 404 error.

**Fix**: Generate static manifest:

```bash
pynext manifest generate --output public/manifest.json
```

### Wrong Theme Color

**Symptom**: Browser chrome has wrong color.

**Fix**: Set in config:

```python
manifest = PWAManifest(
    name="App",
    theme_color="#3b82f6",  # Your color
)
```

---

## Best Practices

### 1. Always Include Both Required Icons

```
public/
├── icon-192.png    # Required for home screen
└── icon-512.png    # Required for splash screen
```

### 2. Use Maskable Icons

```python
Icon("icon-512.png", size=512, purpose="maskable")
```

Safe zone for maskable icons:

```
┌────────────────────────────┐
│                            │
│    ┌────────────────┐      │
│    │                │      │
│    │   Safe Zone    │      │  
│    │   (80% area)   │      │
│    │                │      │
│    └────────────────┘      │
│                            │
└────────────────────────────┘
```

### 3. Include Apple Icon

```
public/apple-icon.png  # 180x180 recommended
```

### 4. Add OG Image for Social

```
public/og-image.png  # 1200x630 recommended
```

### 5. Generate at Build Time

```bash
# Add to build script
pynext manifest generate
```

---

## Summary

| Task | How |
|------|-----|
| Auto-detect icons | Drop files in `public/` |
| Check detection | `pynext icons detect` |
| Create manifest | `PWAManifest(name="App")` |
| Generate manifest | `pynext manifest generate` |
| Validate PWA | `pynext pwa validate` |
| Add shortcuts | `shortcuts=[Shortcut("New", "/new")]` |
| Maskable icons | `Icon(..., purpose="maskable")` |

**Drop files. Generate manifest. Install your app.**

That's PWA in PyNext.

