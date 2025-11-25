# PyNext Static Site Generation (SSG)

> Selective Hydration with Zero JavaScript for Static Pages

## Overview

PyNext SSG applies SolidJS principles to static generation:

| Feature | Next.js | PyNext |
|---------|---------|--------|
| **Hydration** | Full React tree | **Islands only** |
| **Static Detection** | Manual | **Automatic** |
| **Zero JS Pages** | Impossible | **Default for static** |
| **Rebuild** | Full page | **Incremental** |

## Quick Start

```python
from pynext import static_page, static_props, static_paths

@static_page()
def about():
    """This page ships ZERO JavaScript."""
    return div(
        h1("About Us"),
        p("We build awesome things."),
    )
```

## Core Concepts

### 1. Static Page Detection

PyNext automatically detects if a page is fully static:

```python
# ✅ Fully Static (Zero JS)
@static_page()
def about():
    return div(h1("About"), p("Static content"))

# ⚠️ Hybrid (Islands JS only)
@static_page()
def products():
    count = Signal(0)  # ← Interactive!
    return div(
        h1("Products"),
        island(AddToCart(count)),  # Only this ships JS
    )
```

### 2. Static Props (Build-Time Data)

Fetch data at build time:

```python
@static_page()
def blog_post(title: str, content: str, author: str):
    return article(
        h1(title),
        p(f"By {author}"),
        div(content),
    )

@static_props
async def get_blog_props(params: dict) -> dict:
    """Runs at build time, not runtime."""
    post = await fetch_post(params["slug"])
    return {
        "title": post.title,
        "content": post.content,
        "author": post.author.name,
    }
```

### 3. Static Paths (Dynamic Routes)

Generate paths for dynamic routes:

```python
@static_paths
async def get_blog_paths() -> list:
    """Generate all blog post URLs at build time."""
    posts = await fetch_all_posts()
    return [
        {"params": {"slug": post.slug}}
        for post in posts
    ]
```

## Configuration

```python
from pynext import StaticPageConfig, GenerationMode

@static_page(config=StaticPageConfig(
    mode=GenerationMode.STATIC,  # or SSR, ISR, HYBRID
    revalidate=None,              # Seconds for ISR
    fallback=False,               # Generate missing at runtime
    hydrate_islands_only=True,    # Only hydrate @island components
    ship_zero_js=True,            # Ship no JS if fully static
))
def my_page():
    ...
```

## Generation Modes

### STATIC (Default)
```python
@static_page()  # mode=GenerationMode.STATIC
def about():
    return div(h1("About"))
```
- Built once at build time
- No runtime rendering
- Perfect for marketing pages, docs

### HYBRID
```python
@static_page(mode=GenerationMode.HYBRID)
def products():
    cart = Signal([])
    return div(
        h1("Products"),
        island(CartWidget(cart)),  # This gets hydrated
        ProductList(),              # This stays static HTML
    )
```
- Static shell + interactive islands
- Minimal JavaScript
- Best of both worlds

### ISR (See ISR docs)
```python
@static_page(mode=GenerationMode.ISR, revalidate=60)
def pricing():
    return PricingTable()
```
- Static with background revalidation
- Fresh content without full rebuilds

## Zero JS Detection

PyNext analyzes your components to detect interactivity:

```
Component Analysis:
├── Has Signals? → Needs JS
├── Has Event handlers? → Needs JS
├── Has Effects? → Needs JS
├── Has Resources? → Needs JS
├── Has @island? → Needs JS (for that island)
└── None of above? → Zero JS! ✨
```

```python
from pynext import analyze_page

# Check if page needs JavaScript
analysis = analyze_page(my_page_content)

print(analysis)
# {
#   "is_fully_static": True,
#   "needs_js": False,
#   "island_count": 0,
#   "recommended_mode": GenerationMode.STATIC,
# }
```

## Build Output

### CLI Build Command

The `pynext build` command automatically generates static pages:

```bash
pynext build --pages ./pages --static ./public --output ./dist
```

**Output:**
```
[PyNext] Building for production...
[PyNext] Bundled 3 npm packages
[PyNext] Processing images...
[PyNext] Processed 12/12 images
[PyNext] Found 8 routes
[PyNext] Generating static pages...
[PyNext] Generated 5 static pages:
[PyNext]   → Zero JS pages: 3
[PyNext]   → Hybrid pages (islands): 2
[PyNext] Build complete: dist
```

### Build Pipeline

```
pynext build
    │
    ├─▶ Bundle npm packages
    │
    ├─▶ Process images (AVIF/WebP)
    │
    ├─▶ Scan routes
    │
    └─▶ Generate Static Pages
         │
         ├─▶ For each @static_page:
         │    ├─▶ Call @static_paths (if dynamic)
         │    ├─▶ Call @static_props (if defined)
         │    ├─▶ Render page component
         │    ├─▶ Analyze for interactivity
         │    ├─▶ Generate HTML file
         │    └─▶ Generate JS bundle (only if islands)
         │
         └─▶ Write build manifest
```

### Generated Files

```
dist/
├── index.html                    # Homepage (zero JS)
├── about/
│   └── index.html                # About page (zero JS)
├── blog/
│   ├── hello-world/
│   │   └── index.html            # Blog post (zero JS)
│   └── getting-started/
│       └── index.html            # Blog post (zero JS)
├── products/
│   └── index.html                # Products (2.1 KB JS - 1 island)
├── dashboard/
│   └── index.html                # Dashboard (4.3 KB JS - 3 islands)
├── _next/
│   ├── static/
│   │   ├── abc123.js             # Island bundle for products
│   │   └── def456.js             # Island bundle for dashboard
│   ├── image/
│   │   └── ...                   # Optimized images
│   └── build-manifest.json       # Build metadata
└── static/
    └── ...                       # Copied static files
```

### Build Manifest

The `build-manifest.json` tracks all generated pages:

```json
{
  "version": "1.0",
  "buildTime": 1700000000.0,
  "pages": {
    "/": {
      "hash": "abc123def456",
      "hasJs": false,
      "islandCount": 0,
      "generatedAt": 1700000000.0
    },
    "/products": {
      "hash": "789xyz012abc",
      "hasJs": true,
      "islandCount": 1,
      "generatedAt": 1700000000.0
    }
  },
  "assets": {
    "/_next/static/abc123.js": "abc123"
  }
}
```

## Incremental Builds

PyNext only rebuilds changed pages:

```python
# pynext/bundler/static.py computes content hash
hash = compute_page_hash(html, props)

# Skip rebuild if hash matches
if existing_hash == hash:
    print(f"Skipping {path} (unchanged)")
```

```bash
pynext build --incremental

Building static pages...
✓ Cached: /about (unchanged)
✓ Cached: /blog/hello-world (unchanged)
✓ Rebuilt: /blog/new-post (new file)

1 page rebuilt, 2 cached
```

## Layout Pre-Computation

Layouts are resolved once at build time:

```
pages/
├── layout.py          # Root layout
├── about/
│   └── page.py        # Uses root layout
└── blog/
    ├── layout.py      # Blog layout
    └── [slug]/
        └── page.py    # Uses blog + root layouts
```

At build time:
```python
# Layout chains are pre-computed
layout_chains = {
    "/about": [RootLayout],
    "/blog/hello": [RootLayout, BlogLayout],
}
```

## Performance Comparison

| Metric | Next.js SSG | PyNext SSG |
|--------|-------------|------------|
| Hydration JS | Full React | **0 KB** (static) |
| Rebuild Speed | Full tree | **Incremental** |
| Layout Resolution | Runtime | **Build-time** |
| Island Detection | Manual | **Automatic** |

## Best Practices

1. **Default to static** - Let PyNext detect interactivity
2. **Use @island sparingly** - Only wrap truly interactive parts
3. **Fetch data in static_props** - Not in components
4. **Use fallback for dynamic paths** - Don't generate everything

## Architecture

### File Structure

```
pynext/
├── core/
│   └── static.py          # SSG decorators, StaticAnalyzer
├── bundler/
│   └── static.py          # StaticGenerator, build_static_site
├── router/
│   └── trie.py            # LayoutCache for layout chain
└── cli.py                 # Build command integration
```

### Key Classes

#### `StaticPageConfig`

Configuration for static page generation:

```python
@dataclass
class StaticPageConfig:
    mode: GenerationMode = GenerationMode.STATIC
    revalidate: Optional[int] = None     # Seconds for ISR
    fallback: bool = False               # Generate missing at runtime
    hydrate_islands_only: bool = True    # Only hydrate @island components
    ship_zero_js: bool = True            # Attempt zero JS output
    cache_control: str = "public, max-age=31536000, immutable"
    parallel: bool = True                # Build paths in parallel
```

#### `StaticGenerator`

Core build-time generator:

```python
generator = StaticGenerator(
    pages_dir=Path("./pages"),
    output_dir=Path("./dist"),
    static_dir=Path("./public"),
    max_workers=4,  # Parallel builds
)

result = await generator.build_all()
print(f"Generated {result.zero_js_pages} zero-JS pages")
```

#### `StaticAnalyzer`

Analyzes components for interactivity:

```python
analyzer = get_static_analyzer()

# Check if component needs any JavaScript
is_static = analyzer.is_fully_static(my_component)

# Get minimal JS needed (or None for static)
js_bundle = analyzer.get_required_js(my_component)
```

### CLI Integration

The `pynext build` command calls `build_static_site()`:

```python
# In pynext/cli.py

from pynext.bundler.static import build_static_site

result = asyncio.run(build_static_site(
    pages_dir=Path(args.pages).resolve(),
    output_dir=Path(args.output).resolve(),
    static_dir=Path(args.static).resolve(),
))

print(f"[PyNext] Generated {result.total_pages} static pages:")
print(f"[PyNext]   → Zero JS pages: {result.zero_js_pages}")
print(f"[PyNext]   → Hybrid pages (islands): {result.hybrid_pages}")
```

## API Reference

### @static_page

```python
@static_page(config: Optional[StaticPageConfig] = None)
def my_page(...):
    """Mark a page for static generation."""
```

### @static_props

```python
@static_props(revalidate: Optional[int] = None)
async def get_props(params: dict) -> dict:
    """Fetch data at build time."""
```

### @static_paths

```python
@static_paths(fallback: bool = False)
async def get_paths() -> List[Dict]:
    """Generate dynamic route paths."""
```

### analyze_page

```python
def analyze_page(component) -> Dict:
    """Analyze page for static/interactive detection."""
```

### StaticBuildResult

```python
@dataclass
class StaticBuildResult:
    path: str                          # URL path
    html: str                          # Generated HTML
    js_bundle: Optional[str]           # JS code (None = zero JS)
    hash: str                          # Content hash for caching
    has_islands: bool                  # Has interactive islands
    island_count: int                  # Number of islands

    def needs_js(self) -> bool:
        """Check if this page needs JavaScript."""
```

### BuildResult

```python
@dataclass
class BuildResult:
    success: bool
    total_pages: int
    static_pages: int       # Zero-JS pages
    hybrid_pages: int       # Pages with islands
    failed_pages: int
    zero_js_pages: int
    total_time_ms: float
    errors: List[Dict]
    warnings: List[str]
```

## Troubleshooting

### Pages not being generated

Ensure pages are decorated with `@static_page`:

```python
@static_page()  # ← Required!
def my_page():
    return div("Content")
```

### Dynamic routes missing pages

Define `@static_paths` for routes with `[params]`:

```python
@static_paths
async def get_paths():
    return [{"params": {"slug": "post-1"}}, ...]
```

### Unexpected JavaScript in output

Check for hidden interactivity:
- Signals in component
- Event handlers (onclick, etc.)
- Effects or Resources
- Nested `@island` components

```python
analysis = analyze_page(my_page_content)
print(analysis["islands"])  # Shows what requires JS
```

