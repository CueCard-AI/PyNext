# Dynamic OG Images

> Generate beautiful social media preview images with one decorator.

## The Problem

When you share a link on Twitter, LinkedIn, or Slack, it shows a preview:

```
┌─────────────────────────────────────────┐
│  Twitter/LinkedIn/Slack Preview         │
│  ┌───────────────────────────────────┐  │
│  │                                   │  │
│  │     [Your OG Image Here]          │  │
│  │     1200 x 630 pixels             │  │
│  │                                   │  │
│  └───────────────────────────────────┘  │
│  My Blog Post Title                     │
│  Description of the post...             │
│  example.com                            │
└─────────────────────────────────────────┘
```

Without an OG image, your links look boring and get fewer clicks.

**Next.js**: Complex ImageResponse API with JSX-like syntax
**PyNext**: Simple decorator, automatic caching

---

## First Principles

### What is an OG Image?

OG = Open Graph. It's a protocol for sharing links with previews.

When a platform sees your URL, it fetches:
1. Your page HTML
2. Looks for `<meta property="og:image">` tag
3. Fetches that image URL
4. Shows it in the preview

### The Standard Size

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│                    1200 x 630 pixels                         │
│                                                              │
│         This is the standard OG image size.                  │
│         All major platforms support this ratio.              │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### One Decorator

```python
# pages/blog/[slug].py
from pynext import og_image

@og_image()  # That's it!
def BlogPost(slug: str):
    post = get_post(slug)
    return Article(title=post.title, content=post.content)
```

PyNext will:
1. Serve OG image at `/og/blog/[slug].png`
2. Auto-inject `<meta property="og:image">` tag
3. Cache the image for 1 hour (ISR)

### With a Template

```python
from pynext import og_image
from pynext.og import templates

@og_image(template=templates.blog_post)
def BlogPost(slug: str):
    ...
```

### Preview Your OG Image

```bash
pynext og preview /blog/my-post --output preview.png
```

---

## Templates

### Pre-built Templates

PyNext includes ready-to-use templates:

| Template | Use Case | Variables |
|----------|----------|-----------|
| `blog_post` | Blog articles | `title`, `date`, `category` |
| `product` | E-commerce | `name`, `price` |
| `profile` | User profiles | `name`, `bio` |
| `minimal` | Simple pages | `title` |
| `docs` | Documentation | `title`, `section` |
| `event` | Events | `title`, `date`, `location` |
| `video` | Videos | `title`, `duration`, `channel` |

### Using Templates

```python
from pynext import og_image
from pynext.og import templates

# Blog post
@og_image(template=templates.blog_post)
def BlogPost(slug: str):
    ...

# Product page
@og_image(template=templates.product)
def ProductPage(id: str):
    ...

# Profile
@og_image(template=templates.profile)
def UserProfile(username: str):
    ...
```

### Custom Template

```python
from pynext import og_image, OGTemplate

template = OGTemplate(
    title="{{title}}",
    subtitle="{{price}} · Free shipping",
    background="gradient:green",
    title_size=56,
)

@og_image(template=template)
def ProductPage(id: str):
    ...
```

### Template Variables

Templates use `{{variable}}` placeholders:

```python
template = OGTemplate(
    title="{{title}}",
    subtitle="{{date}} · {{read_time}} min read",
)

# Variables come from page metadata or context
```

---

## OGCanvas

For full control, use `OGCanvas` with a custom handler:

### Basic Canvas

```python
from pynext import og_image, OGCanvas

@og_image()
def BlogPost(slug: str):
    ...

@BlogPost.og
def generate_og(slug: str) -> OGCanvas:
    post = get_post(slug)
    
    return OGCanvas(
        background="gradient:slate"
    ).add_text(
        post.title,
        x=60, y=200,
        font_size=64,
        font_weight="bold",
        color="white",
    )
```

### Chainable API

```python
canvas = (
    OGCanvas(background="gradient:blue")
    .add_text("Title", x=60, y=180, font_size=64, font_weight="bold", color="white")
    .add_text("Subtitle", x=60, y=280, font_size=32, color="#94a3b8")
    .add_rect(x=0, y=500, width=1200, height=130, color="#000000", opacity=0.5)
    .add_image("avatar.png", x=60, y=520, width=60, height=60, border_radius=30)
    .add_text("Author Name", x=140, y=535, font_size=24, color="white")
)
```

### Canvas Methods

| Method | Description |
|--------|-------------|
| `add_text(text, x, y, ...)` | Add text element |
| `add_image(src, x, y, w, h, ...)` | Add image element |
| `add_rect(x, y, w, h, ...)` | Add rectangle element |
| `clear()` | Remove all elements |
| `clone()` | Create a copy |

### Text Options

```python
canvas.add_text(
    text="Hello World",
    x=60,                    # X position (from left)
    y=200,                   # Y position (from top)
    font_size=64,            # Font size in pixels
    font_weight="bold",      # "normal" or "bold"
    font_family="Inter",     # Font family
    color="#ffffff",         # Text color
    max_width=1080,          # Max width before wrapping
    line_height=1.4,         # Line height multiplier
    align="left",            # "left", "center", "right"
)
```

### Image Options

```python
canvas.add_image(
    src="avatar.png",        # File path or URL
    x=60,                    # X position
    y=400,                   # Y position
    width=80,                # Width in pixels
    height=80,               # Height in pixels
    border_radius=40,        # Corner radius (circular = width/2)
    object_fit="cover",      # "cover", "contain", "fill"
)
```

### Rectangle Options

```python
canvas.add_rect(
    x=0,                     # X position
    y=500,                   # Y position
    width=1200,              # Width in pixels
    height=130,              # Height in pixels
    color="#000000",         # Fill color
    border_radius=0,         # Corner radius
    opacity=0.5,             # Opacity (0.0 - 1.0)
)
```

---

## Gradients

PyNext includes 25+ pre-defined gradients:

### Using Gradients

```python
# In templates
OGTemplate(background="gradient:blue")

# In canvas
OGCanvas(background="gradient:purple")
```

### Available Gradients

| Name | Colors |
|------|--------|
| `slate` | Dark gray gradient |
| `blue` | Blue gradient |
| `purple` | Purple gradient |
| `green` | Green gradient |
| `orange` | Orange gradient |
| `pink` | Pink gradient |
| `red` | Red gradient |
| `sunset` | Orange to pink |
| `ocean` | Cyan to blue |
| `aurora` | Purple to cyan |

### List All Gradients

```python
from pynext.og.templates import list_gradients, get_gradient

# Get all gradient names
names = list_gradients()  # ["slate", "blue", ...]

# Get gradient CSS
css = get_gradient("blue")  # "linear-gradient(135deg, #3b82f6, #1d4ed8)"
```

---

## Caching

OG images are cached with ISR (Incremental Static Regeneration).

### Default Caching (1 hour)

```python
@og_image()  # Cached for 3600 seconds (1 hour)
def Page(): ...
```

### Custom Cache Duration

```python
@og_image(cache=86400)  # 24 hours
def Page(): ...

@og_image(cache=False)  # No caching
def Page(): ...
```

### Cache Headers

Response includes:
```
Cache-Control: public, max-age=3600
```

---

## Output Formats

### PNG (Default)

```python
@og_image()  # Default: PNG
def Page(): ...
```

### JPEG

```python
@og_image(format="jpeg", quality=85)
def Page(): ...
```

### WebP

```python
@og_image(format="webp", quality=90)
def Page(): ...
```

---

## CLI Commands

### Preview

```bash
# Preview OG image for a route
pynext og preview /blog/my-post

# Save to file
pynext og preview /blog/my-post --output preview.png
```

### Generate All

```bash
# Generate all OG images at build time
pynext og generate

# Custom output directory
pynext og generate --output-dir public/og
```

### Validate

```bash
# Check which pages have @og_image
pynext og validate
```

---

## Auto Meta Tags

PyNext automatically injects these meta tags:

```html
<meta property="og:image" content="https://example.com/og/blog/my-post.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://example.com/og/blog/my-post.png">
```

---

## Real-World Examples

### Blog Post with Author

```python
from pynext import og_image, OGCanvas

@og_image()
def BlogPost(slug: str):
    post = get_post(slug)
    return Article(title=post.title, content=post.content)

@BlogPost.og
def generate_og(slug: str) -> OGCanvas:
    post = get_post(slug)
    
    return (
        OGCanvas(background="gradient:slate")
        # Category label
        .add_text(
            post.category.upper(),
            x=60, y=120,
            font_size=20,
            color="#94a3b8",
        )
        # Title
        .add_text(
            post.title,
            x=60, y=180,
            font_size=56,
            font_weight="bold",
            color="white",
            max_width=1080,
        )
        # Author avatar
        .add_image(
            post.author.avatar,
            x=60, y=480,
            width=64, height=64,
            border_radius=32,
        )
        # Author name
        .add_text(
            post.author.name,
            x=140, y=495,
            font_size=24,
            color="white",
        )
        # Date and read time
        .add_text(
            f"{post.date} · {post.read_time} min read",
            x=140, y=525,
            font_size=18,
            color="#94a3b8",
        )
    )
```

### E-commerce Product

```python
from pynext import og_image, OGCanvas

@og_image()
def ProductPage(id: str):
    product = get_product(id)
    return ProductDetail(product=product)

@ProductPage.og
def generate_og(id: str) -> OGCanvas:
    product = get_product(id)
    
    return (
        OGCanvas(background="#ffffff")
        # Product image
        .add_image(
            product.image,
            x=60, y=65,
            width=500, height=500,
            border_radius=16,
        )
        # Product name
        .add_text(
            product.name,
            x=620, y=150,
            font_size=48,
            font_weight="bold",
            color="#1f2937",
            max_width=520,
        )
        # Price
        .add_text(
            f"${product.price}",
            x=620, y=260,
            font_size=40,
            color="#10b981",
        )
        # Description
        .add_text(
            product.description[:100] + "...",
            x=620, y=330,
            font_size=24,
            color="#6b7280",
            max_width=520,
        )
    )
```

### Documentation Page

```python
from pynext import og_image
from pynext.og import templates

template = templates.docs.with_logo("public/logo.svg")

@og_image(template=template)
def DocsPage(path: str):
    ...
```

---

## Under the Hood

### How It Works

```
1. Request comes to /og/blog/my-post.png
   ─────────────────────────────────────
   
2. PyNext finds the route handler for /blog/my-post
   ─────────────────────────────────────────────────
   
3. Checks if handler has @og_image decorator
   ────────────────────────────────────────────
   
4. Checks ISR cache for existing image
   ─────────────────────────────────────
   
5. If not cached:
   ───────────────
   a. Run custom @handler.og() if exists
   b. OR render template with context
   c. Use Pillow to generate image
   d. Cache result
   
6. Return image bytes
   ───────────────────
```

### Performance

| Metric | PyNext | Next.js |
|--------|--------|---------|
| First generation | ~200ms | ~500ms |
| Cached response | ~5ms | ~50ms |
| Memory per image | ~10MB | ~50MB |
| Dependencies | Pillow | Satori + Sharp |

---

## Troubleshooting

### Image Not Generating

**Symptom**: 404 at `/og/path.png`

**Check**:
1. Page has `@og_image()` decorator
2. Route exists and matches

```bash
pynext og validate
```

### Pillow Not Installed

**Symptom**: 500 error "Pillow required"

**Fix**:
```bash
pip install Pillow
```

### Gradient Not Rendering

**Symptom**: White background instead of gradient

**Check**: Use correct gradient name:
```python
# Correct
OGCanvas(background="gradient:blue")

# Incorrect
OGCanvas(background="gradient:lightblue")
```

### Text Overflowing

**Symptom**: Text runs off edge

**Fix**: Use `max_width`:
```python
canvas.add_text(
    long_text,
    x=60, y=200,
    max_width=1080,  # Will wrap
)
```

---

## Best Practices

### 1. Use Templates for Consistency

```python
# Create a shared template
my_template = OGTemplate(
    title="{{title}}",
    subtitle="{{site_name}}",
    background="gradient:blue",
    logo="public/logo.png",
)

# Reuse across pages
@og_image(template=my_template)
def Page1(): ...

@og_image(template=my_template)
def Page2(): ...
```

### 2. Cache Appropriately

```python
# Static content: long cache
@og_image(cache=86400)  # 24 hours
def AboutPage(): ...

# Dynamic content: short cache
@og_image(cache=3600)  # 1 hour
def BlogPost(slug: str): ...

# Real-time data: no cache
@og_image(cache=False)
def StockPrice(symbol: str): ...
```

### 3. Keep Text Readable

- Title: 48-64px
- Subtitle: 24-32px
- Minimum: 18px (for accessibility)

### 4. Use High Contrast

```python
# Good: white on dark
OGCanvas(background="gradient:slate").add_text(
    "Title", color="white"
)

# Bad: light gray on light background
OGCanvas(background="#f0f0f0").add_text(
    "Title", color="#cccccc"  # Hard to read
)
```

---

## Summary

| Task | How |
|------|-----|
| Add OG image | `@og_image()` |
| Use template | `@og_image(template=templates.blog_post)` |
| Custom canvas | `@page.og` decorator |
| Add text | `canvas.add_text(...)` |
| Add image | `canvas.add_image(...)` |
| Use gradient | `background="gradient:blue"` |
| Cache 24h | `@og_image(cache=86400)` |
| Preview | `pynext og preview /path` |

**One decorator. Beautiful previews. More clicks.**

That's OG Images in PyNext.

