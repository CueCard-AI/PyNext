# Sitemap & Robots.txt

> SEO-critical files generated from your routes - simpler than Next.js, auto-discovery included.

## The Problem

Search engines need to find your pages. Without a sitemap:

```
❌ Crawler visits homepage
❌ Follows only visible links
❌ Misses dynamically generated pages
❌ Doesn't know update frequency
❌ Wastes crawl budget
```

With a sitemap:

```
✓ Crawler reads sitemap.xml
✓ Knows ALL your pages instantly
✓ Understands update frequency
✓ Prioritizes important pages
✓ Efficient crawling
```

---

## First Principles

### What is a Sitemap?

Think of it as a **table of contents for search engines**:

```
┌──────────────────────────────────────────────────────────┐
│                    Your Website                           │
│                                                           │
│   /                    (homepage)                         │
│   /about               (static page)                      │
│   /products/123        (product page)                     │
│   /products/456        (product page)                     │
│   /blog/hello-world    (blog post)                        │
│   ...                                                     │
│                                                           │
└──────────────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│                   sitemap.xml                             │
│                                                           │
│   <?xml version="1.0"?>                                   │
│   <urlset>                                                │
│     <url>                                                 │
│       <loc>https://example.com/</loc>                     │
│       <priority>1.0</priority>                            │
│     </url>                                                │
│     <url>                                                 │
│       <loc>https://example.com/products/123</loc>         │
│       <changefreq>daily</changefreq>                      │
│     </url>                                                │
│     ...                                                   │
│   </urlset>                                               │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### What is Robots.txt?

Think of it as **access control for crawlers**:

```
User-agent: *          ← "For all crawlers..."
Allow: /               ← "...you can access everything..."
Disallow: /admin       ← "...except admin pages"

Sitemap: https://example.com/sitemap.xml
```

---

## Quick Start

### 3 Lines to Add a Page to Sitemap

```python
# pages/products/[id]/page.py
from pynext import page, sitemap

@sitemap()  # That's it!
@page
def ProductPage(id: str):
    return Product(id)
```

Your page is now in the sitemap.

### Generate Sitemap

```bash
pynext sitemap generate --base-url https://example.com
```

Output: `public/sitemap.xml`

### Generate Robots.txt

```bash
pynext robots generate --base-url https://example.com
```

Output: `public/robots.txt`

---

## Sitemap API Reference

### The `@sitemap` Decorator

```python
from pynext import sitemap

@sitemap(
    priority=0.5,        # 0.0-1.0, page importance
    changefreq="weekly", # How often content changes
    lastmod="auto",      # Last modification date
    include=True,        # Include in sitemap?
)
```

### Parameters

#### `priority` - Page Importance

| Value | Meaning | Use For |
|-------|---------|---------|
| `1.0` | Most important | Homepage |
| `0.8` | Very important | Main sections, key products |
| `0.5` | Normal (default) | Standard pages |
| `0.3` | Less important | Archive, tags |
| `0.0` | Least important | Utility pages |

```python
# Homepage - highest priority
@sitemap(priority=1.0)
@page
def HomePage():
    return Home()

# Product page - high priority
@sitemap(priority=0.8)
@page
def ProductPage(id: str):
    return Product(id)
```

#### `changefreq` - Update Frequency

| Value | Meaning | Use For |
|-------|---------|---------|
| `"always"` | Changes every access | Live feeds |
| `"hourly"` | Changes every hour | News sites |
| `"daily"` | Changes daily | E-commerce, blogs |
| `"weekly"` | Changes weekly (default) | Standard pages |
| `"monthly"` | Changes monthly | Archives |
| `"yearly"` | Changes yearly | About pages |
| `"never"` | Never changes | Legal, archived |

```python
# Blog post - changes rarely
@sitemap(changefreq="yearly")
@page
def BlogPost(slug: str):
    return Post(slug)

# Product page - changes often
@sitemap(changefreq="daily")
@page
def ProductPage(id: str):
    return Product(id)
```

#### `lastmod` - Last Modified Date

| Value | Meaning |
|-------|---------|
| `"auto"` | Use file modification time (default) |
| `"2024-01-15"` | Specific date (ISO format) |
| `None` | Don't include lastmod |

```python
# Auto-detect from file
@sitemap(lastmod="auto")
@page
def Page():
    ...

# Specific date
@sitemap(lastmod="2024-01-15")
@page
def LegacyPage():
    ...
```

#### `include` - Include/Exclude

```python
# Include in sitemap (default)
@sitemap(include=True)
@page
def PublicPage():
    ...

# Exclude from sitemap
@sitemap(include=False)
@page
def AdminPage():
    ...
```

---

## Dynamic Routes

For routes like `/products/[id]`, PyNext needs to know all possible values.

### Provide Parameter Values

```python
# pages/products/[id]/page.py
from pynext import page, sitemap

@sitemap(priority=0.8)
@page
def ProductPage(id: str):
    return Product(id)

# PyNext calls this at build time
def get_sitemap_params():
    """Return all product IDs for sitemap."""
    products = Product.all()
    return [{"id": p.id} for p in products]
```

### Multiple Parameters

```python
# pages/blog/[year]/[slug]/page.py
@sitemap(priority=0.7)
@page
def BlogPost(year: str, slug: str):
    return Post(year, slug)

def get_sitemap_params():
    """Return all year/slug combinations."""
    posts = Post.all()
    return [
        {"year": p.year, "slug": p.slug}
        for p in posts
    ]
```

### With Dynamic `lastmod`

```python
def get_sitemap_params():
    """Include lastmod in params."""
    posts = Post.all()
    return [
        {
            "year": p.year,
            "slug": p.slug,
            "lastmod": p.updated_at.isoformat(),  # Dynamic lastmod
        }
        for p in posts
    ]
```

---

## Sitemap Index (Large Sites)

For sites with >50,000 URLs, PyNext automatically creates a sitemap index.

### Automatic Splitting

```
pynext sitemap generate --base-url https://example.com

[PyNext] ✓ Generated sitemap with 75,000 URLs
  → public/sitemap.xml        (index)
  → public/sitemap-1.xml      (URLs 1-50,000)
  → public/sitemap-2.xml      (URLs 50,001-75,000)
  ℹ Split into sitemap index (>50,000 URLs)
```

### Generated Index

```xml
<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap>
    <loc>https://example.com/sitemap-1.xml</loc>
    <lastmod>2024-01-15</lastmod>
  </sitemap>
  <sitemap>
    <loc>https://example.com/sitemap-2.xml</loc>
    <lastmod>2024-01-15</lastmod>
  </sitemap>
</sitemapindex>
```

---

## Robots.txt Configuration

### In `pynext.config.py`

```python
from pynext import RobotsConfig, RobotsRule

robots = RobotsConfig(
    rules=[
        RobotsRule(
            user_agent="*",
            allow=["/"],
            disallow=["/admin", "/api", "/internal"],
        ),
        RobotsRule(
            user_agent="Googlebot",
            crawl_delay=1,  # 1 second between requests
        ),
    ],
    sitemap=True,  # Include sitemap URL
)
```

### One-Line Shortcuts

```python
from pynext import robots_allow_all, robots_disallow_all

# Allow everything
robots = robots_allow_all()

# Allow everything except /admin
robots = robots_allow_all(except_paths=["/admin", "/api"])

# Block all crawlers (staging site)
robots = robots_disallow_all()
```

### Generated Output

```
User-agent: *
Allow: /
Disallow: /admin
Disallow: /api
Disallow: /internal

User-agent: Googlebot
Crawl-delay: 1

Sitemap: https://example.com/sitemap.xml
```

---

## CLI Commands

### Sitemap Commands

```bash
# Generate sitemap
pynext sitemap generate --base-url https://example.com

# Generate to specific directory
pynext sitemap generate --output dist/ --base-url https://example.com

# Preview URLs without generating
pynext sitemap preview --base-url https://example.com

# Validate existing sitemap
pynext sitemap validate
```

### Robots Commands

```bash
# Generate robots.txt
pynext robots generate --base-url https://example.com

# Preview without generating
pynext robots preview

# Validate existing file
pynext robots validate
```

### Build Integration

```bash
# Generate both during build
pynext build --sitemap
```

---

## Real-World Examples

### E-commerce Site

```python
# pages/page.py (homepage)
@sitemap(priority=1.0, changefreq="daily")
@page
def HomePage():
    return Home()

# pages/products/[id]/page.py
@sitemap(priority=0.8, changefreq="daily")
@page
def ProductPage(id: str):
    return Product(id)

def get_sitemap_params():
    return [{"id": p.id} for p in Product.all()]

# pages/categories/[slug]/page.py
@sitemap(priority=0.6, changefreq="weekly")
@page
def CategoryPage(slug: str):
    return Category(slug)

def get_sitemap_params():
    return [{"slug": c.slug} for c in Category.all()]

# pages/admin/page.py
@sitemap(include=False)  # Don't index admin
@page
def AdminPage():
    return Admin()
```

**pynext.config.py:**

```python
robots = robots_allow_all(
    except_paths=["/admin", "/api", "/checkout", "/cart"]
)
```

### Blog Site

```python
# pages/blog/[slug]/page.py
@sitemap(priority=0.7, changefreq="monthly")
@page
def BlogPost(slug: str):
    return Article(slug)

def get_sitemap_params():
    posts = Post.published()
    return [
        {
            "slug": p.slug,
            "lastmod": p.updated_at.strftime("%Y-%m-%d"),
        }
        for p in posts
    ]

# pages/blog/page.py (blog index)
@sitemap(priority=0.8, changefreq="daily")
@page
def BlogIndex():
    return BlogList()
```

### SaaS Application

```python
# Public pages in sitemap
@sitemap(priority=1.0)
@page
def LandingPage():
    return Landing()

@sitemap(priority=0.9)
@page
def PricingPage():
    return Pricing()

@sitemap(priority=0.8)
@page
def FeaturesPage():
    return Features()

# Private pages excluded
@sitemap(include=False)
@page
def DashboardPage():
    return Dashboard()

@sitemap(include=False)
@page
def SettingsPage():
    return Settings()
```

**pynext.config.py:**

```python
robots = RobotsConfig(
    rules=[
        RobotsRule(
            user_agent="*",
            allow=["/", "/pricing", "/features", "/blog"],
            disallow=["/app", "/api", "/dashboard", "/settings"],
        ),
    ],
    sitemap=True,
)
```

---

## Build-Time vs Runtime

### Build-Time (Default)

Best for static sites or SSG. Generated once at build.

```bash
pynext build --sitemap
# Creates public/sitemap.xml
```

Served as static file. Zero runtime cost.

### Runtime (Dynamic)

For sites where URLs change frequently.

**pynext.config.py:**

```python
config = {
    "dynamic_sitemap": True,
    "base_url": "https://example.com",
}
```

Server generates sitemap on each request:

```python
GET /sitemap.xml  →  Generated dynamically
```

Cached for 1 hour by default.

---

## Under the Hood

### Generation Flow

```
1. Scan Routes
   ─────────────
   FileRouter scans pages/ directory
   Finds all routes with @sitemap decorator
   
2. Discover URLs
   ─────────────
   For each @sitemap route:
   - Static route → Single URL
   - Dynamic route → Call get_sitemap_params()
   
3. Create Entries
   ─────────────
   Build SitemapEntry for each URL:
   - loc: Full URL
   - lastmod: From file mtime or params
   - changefreq: From @sitemap config
   - priority: From @sitemap config
   
4. Generate XML
   ─────────────
   If ≤50k URLs → Single sitemap.xml
   If >50k URLs → sitemap index + split files
   
5. Write Files
   ─────────────
   Output to public/ directory
```

### Performance

| Operation | Next.js | PyNext |
|-----------|---------|--------|
| URL discovery | Manual function | Auto from router |
| Build (1k URLs) | ~500ms | ~50ms |
| Build (50k URLs) | ~5s | ~500ms |
| Dynamic generation | Always | Optional |

---

## Comparison with Next.js

### Next.js Approach

```javascript
// app/sitemap.js
export default function sitemap() {
  return [
    { url: 'https://example.com', lastModified: new Date() },
    { url: 'https://example.com/about', lastModified: new Date() },
    // ...manually list every URL
  ]
}

// For dynamic routes, you must:
// 1. Create sitemap.js in each route
// 2. Fetch all IDs manually
// 3. Build URLs manually
```

### PyNext Approach

```python
# Just decorate your pages!
@sitemap()
@page
def HomePage():
    ...

@sitemap()
@page
def ProductPage(id: str):
    ...

def get_sitemap_params():
    return [{"id": p.id} for p in Product.all()]

# URLs auto-discovered from router!
```

| Aspect | Next.js | PyNext |
|--------|---------|--------|
| Discovery | Manual | Automatic |
| Per-page config | No | Yes (decorator) |
| Dynamic routes | Manual fetch | get_sitemap_params() |
| Sitemap index | Manual | Automatic |
| Build integration | Manual | pynext build --sitemap |

---

## Troubleshooting

### No URLs in Sitemap

**Symptom**: Sitemap is empty or has very few URLs.

**Check**:
1. Add `@sitemap()` decorator to pages
2. Ensure decorator is above `@page`
3. For dynamic routes, implement `get_sitemap_params()`

```python
# ✅ Correct order
@sitemap()
@page
def MyPage():
    ...

# ❌ Wrong order - won't be discovered
@page
@sitemap()
def MyPage():
    ...
```

### Dynamic Routes Not Appearing

**Symptom**: `/products/123` not in sitemap, only `/products/[id]`.

**Fix**: Add `get_sitemap_params()` function:

```python
# pages/products/[id]/page.py
@sitemap()
@page
def ProductPage(id: str):
    ...

# This function is required for dynamic routes!
def get_sitemap_params():
    return [{"id": p.id} for p in Product.all()]
```

### Wrong Base URL

**Symptom**: URLs use `https://example.com` placeholder.

**Fix**: Specify `--base-url`:

```bash
pynext sitemap generate --base-url https://yoursite.com
```

Or set in config:

```python
# pynext.config.py
config = {
    "base_url": "https://yoursite.com",
}
```

### Robots.txt Blocking Too Much

**Symptom**: Search engines can't access public pages.

**Check** your `pynext.config.py`:

```python
# ❌ Too restrictive
robots = RobotsConfig(
    rules=[RobotsRule(disallow=["/"]) ],  # Blocks everything!
)

# ✅ Allow public, block private
robots = robots_allow_all(except_paths=["/admin", "/api"])
```

---

## Best Practices

### 1. Always Add `@sitemap()` to Public Pages

```python
@sitemap()  # Don't forget!
@page
def PublicPage():
    ...
```

### 2. Use Appropriate Priorities

```python
# Homepage: highest
@sitemap(priority=1.0)

# Key pages: high
@sitemap(priority=0.8)

# Standard pages: default
@sitemap()  # 0.5

# Archive/tags: low
@sitemap(priority=0.3)
```

### 3. Set Realistic `changefreq`

Don't set everything to "daily" - be honest about how often content changes.

### 4. Exclude Private Pages

```python
@sitemap(include=False)
@page
def AdminPage():
    ...
```

### 5. Generate at Build Time

```bash
# Add to your build script
pynext build --sitemap
```

### 6. Submit to Search Console

After deploying, submit your sitemap to Google Search Console:

```
https://search.google.com/search-console
→ Sitemaps → Add sitemap → https://yoursite.com/sitemap.xml
```

---

## Summary

| Task | How |
|------|-----|
| Include page in sitemap | `@sitemap()` decorator |
| Set priority | `@sitemap(priority=0.8)` |
| Set update frequency | `@sitemap(changefreq="daily")` |
| Exclude page | `@sitemap(include=False)` |
| Dynamic route params | `def get_sitemap_params()` |
| Generate sitemap | `pynext sitemap generate` |
| Configure robots.txt | `robots = RobotsConfig(...)` |
| Generate robots.txt | `pynext robots generate` |
| Build with sitemap | `pynext build --sitemap` |

**One decorator. Auto-discovery. Zero hassle.**

That's SEO in PyNext.

