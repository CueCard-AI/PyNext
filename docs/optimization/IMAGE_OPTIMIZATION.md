# PyNext Image Optimization

> Build-Time Image Processing with Zero JavaScript for Static Images

## Overview

PyNext's image optimization is fundamentally different from Next.js:

| Feature | Next.js | PyNext |
|---------|---------|--------|
| **Processing** | Runtime (on-demand) | **Build-time** |
| **Client JS** | ~15KB image loader | **0 KB** (static images) |
| **Formats** | WebP, AVIF | **AVIF-first**, WebP, JPEG fallback |
| **Lazy Loading** | JavaScript-based | **Native** `loading="lazy"` |
| **Placeholders** | Runtime blur | **Build-time** BlurHash |

### SolidJS Principles Applied

- **Zero JS for static content** - Static images ship pure HTML
- **Fine-grained reactivity only when needed** - JS only for Signal-based images
- **Build-time optimization over runtime processing** - All heavy work at compile time
- **Native browser features over JS polyfills** - Uses `loading="lazy"`, `srcset`, `<picture>`

## Quick Start

### Installation

```bash
# Core dependencies (from GitHub until PyPI release)
pip install git+https://github.com/CueCard-AI/PyNext.git

# Optional: For full image processing (recommended)
pip install Pillow blurhash-python
```

### Basic Usage

```python
from pynext import Image

# Basic usage - zero JavaScript!
Image(
    src="/images/hero.jpg",
    alt="Hero image",
    width=1920,
    height=1080,
)
```

## Features

### 1. Build-Time Processing

All images are processed during `pynext build`:
- Generate AVIF, WebP, and JPEG variants
- Create multiple sizes for responsive `srcset`
- Compute BlurHash placeholders
- Extract dominant colors

```bash
pynext build

# Output:
# [PyNext] Building for production...
# [PyNext] Bundled 3 npm packages
# [PyNext] Processing images...
# [PyNext] Processed 42/42 images
# [PyNext] Found 12 routes
# [PyNext] Build complete: dist
```

#### CLI Build Command

The `pynext build` command automatically:

1. **Scans for registered images** - Finds all `Image()` component usages
2. **Processes in parallel** - Uses multi-threading for speed
3. **Generates variants** - Creates AVIF, WebP, JPEG at multiple sizes
4. **Computes placeholders** - BlurHash + tiny base64 data URLs
5. **Creates manifest** - `_next/image/image-manifest.json` for caching
6. **Skips unchanged images** - Incremental builds via content hashing

```bash
# Full build command
pynext build --pages ./pages --static ./public --output ./dist

# The image output goes to:
# ./dist/_next/image/
#   ├── abc123_640w.avif
#   ├── abc123_640w.webp
#   ├── abc123_640w.jpg
#   ├── abc123_1080w.avif
#   ├── ... (more variants)
#   └── image-manifest.json
```

### 2. Zero JavaScript for Static Images

Static images ship **zero client-side JavaScript**:

```python
# This renders as pure HTML - no JS!
Image(src="/photo.jpg", alt="Photo")
```

Output:
```html
<picture>
  <source type="image/avif" srcset="/_next/image/abc123_640w.avif 640w, ..." />
  <source type="image/webp" srcset="/_next/image/abc123_640w.webp 640w, ..." />
  <img src="/_next/image/abc123_1080w.jpg" alt="Photo" loading="lazy" />
</picture>
```

### 3. Format Fallback Chain

PyNext uses AVIF-first with intelligent fallbacks:

```
Browser Check:
├── AVIF supported? → Use AVIF (50% smaller than WebP)
├── WebP supported? → Use WebP (30% smaller than JPEG)
└── Fallback → Use JPEG (universal support)
```

### 4. Native Lazy Loading

Uses browser-native lazy loading instead of JavaScript:

```python
# Default: lazy loading
Image(src="/photo.jpg", alt="Photo")
# Renders: <img loading="lazy" ... />

# Eager loading for above-the-fold
Image(src="/hero.jpg", alt="Hero", loading=ImageLoading.EAGER)
# Renders: <img loading="eager" ... />
```

### 5. Priority Images with Preload

Mark critical images for preloading:

```python
from pynext import PriorityImage

# Preloads in <head> for faster LCP
PriorityImage(
    src="/hero.jpg",
    alt="Hero",
    width=1920,
    height=1080,
)
```

Output includes preload link:
```html
<link rel="preload" as="image" type="image/avif" imagesrcset="..." />
<picture>...</picture>
```

### 6. BlurHash Placeholders

Tiny, beautiful placeholders computed at build time:

```python
Image(
    src="/photo.jpg",
    alt="Photo",
    placeholder="blur",  # Default
)
```

The placeholder is a ~40-byte base64 data URL embedded inline.

### 7. Layout Modes

```python
from pynext import Image, ImageLayout

# Intrinsic: Original aspect ratio, max at natural size
Image(src="/img.jpg", alt="...", layout=ImageLayout.INTRINSIC)

# Fixed: Exact dimensions
Image(src="/img.jpg", alt="...", width=300, height=200, layout=ImageLayout.FIXED)

# Responsive: Scales with container width
Image(src="/img.jpg", alt="...", layout=ImageLayout.RESPONSIVE)

# Fill: Fills parent container
Image(src="/img.jpg", alt="...", layout=ImageLayout.FILL)
```

## Configuration

```python
from pynext import ImageConfig, ImageFormat, configure_images

configure_images(ImageConfig(
    # Output formats in priority order
    formats=[
        ImageFormat.AVIF,
        ImageFormat.WEBP,
        ImageFormat.JPEG,
    ],
    
    # Quality per format
    quality={
        ImageFormat.AVIF: 75,
        ImageFormat.WEBP: 80,
        ImageFormat.JPEG: 85,
    },
    
    # Responsive sizes for srcset
    sizes=[
        ImageSize(640, suffix="_sm"),   # Mobile
        ImageSize(1080, suffix="_lg"),  # Desktop
        ImageSize(1920, suffix="_2xl"), # Large displays
    ],
    
    # BlurHash placeholder size
    blur_hash_size=4,  # 4x4 grid
))
```

## Convenience Components

```python
from pynext import ResponsiveImage, FillImage, PriorityImage, Avatar

# Responsive (full-width, auto-height)
ResponsiveImage(src="/banner.jpg", alt="Banner")

# Fill (absolute positioning, covers parent)
FillImage(src="/background.jpg", alt="Background")

# Priority (preloaded, eager)
PriorityImage(src="/hero.jpg", alt="Hero")

# Avatar (circular, fixed size)
Avatar(src="/user.jpg", alt="User", size=48)
```

## Reactive Images (With JavaScript)

If you need reactive image sources, JavaScript is included:

```python
from pynext import Signal, Image

# Only reactive images ship JS
current_image = Signal("/images/photo1.jpg")

Image(
    src=current_image,  # Signal source
    alt="Dynamic photo",
)
```

## Image Processing Pipeline

During build:

```
Source Image (/images/hero.jpg)
        │
        ├──▶ Read & Validate
        │
        ├──▶ Generate Sizes
        │    ├── 640w (mobile)
        │    ├── 750w (tablet)
        │    ├── 1080w (desktop)
        │    ├── 1200w (large)
        │    ├── 1920w (2K)
        │    └── 3840w (4K)
        │
        ├──▶ Convert Formats
        │    ├── AVIF (quality: 75)
        │    ├── WebP (quality: 80)
        │    └── JPEG (quality: 85)
        │
        ├──▶ Generate Placeholders
        │    ├── BlurHash (4x4)
        │    └── Dominant color
        │
        └──▶ Write to /_next/image/
             └── Update manifest
```

## Performance Comparison

| Metric | Next.js | PyNext |
|--------|---------|--------|
| Client JS | ~15KB | **0 KB** |
| Initial Load | Image loader init | **Instant** |
| LCP Impact | JS execution first | **Immediate render** |
| Build Time | N/A | ~50ms/image |
| Cache Strategy | Runtime cache | **CDN-friendly** |

## Best Practices

1. **Use descriptive alt text** for accessibility
2. **Set width/height** to prevent layout shift
3. **Use priority for LCP images** (hero, above-fold)
4. **Use responsive layout** for content images
5. **Use fill layout** for backgrounds/cards

## Architecture

### File Structure

```
pynext/
├── core/
│   └── image.py          # Image component, ImageConfig, ImageRegistry
├── bundler/
│   └── images.py         # ImageProcessor, build-time optimization
├── runtime/
│   └── image.js          # Client-side runtime (only for reactive images)
└── cli.py                # Build command integration
```

### Key Classes

#### `ImageConfig`

Configuration for image optimization:

```python
@dataclass
class ImageConfig:
    # Output formats in priority order
    formats: List[ImageFormat] = [AVIF, WEBP, JPEG]
    
    # Predefined sizes for srcset
    sizes: List[ImageSize] = [
        ImageSize(640, suffix="_sm"),    # Mobile
        ImageSize(750, suffix="_md"),    # Tablet  
        ImageSize(1080, suffix="_lg"),   # Desktop
        ImageSize(1200, suffix="_xl"),   # Large desktop
        ImageSize(1920, suffix="_2xl"),  # 2K displays
        ImageSize(3840, suffix="_4k"),   # 4K displays
    ]
    
    # Quality per format
    quality: Dict[ImageFormat, int] = {
        AVIF: 75,
        WEBP: 80,
        JPEG: 85,
        PNG: 100,
    }
    
    # BlurHash settings
    blur_hash_size: int = 4       # 4x4 grid
    blur_placeholder_width: int = 40
    
    # Device pixel ratios
    device_sizes: List[int] = [1, 2, 3]
    
    # Output directory
    output_dir: str = "_next/image"
```

#### `ImageRegistry`

Tracks images for build-time processing:

```python
registry = get_image_registry()

# Register an image for processing
registry.register("/images/hero.jpg")

# Get optimized data (after build)
optimized = registry.get("/images/hero.jpg")
print(optimized.variants)  # {"avif": {"640w": "...", ...}, ...}
print(optimized.blur_hash)  # "LEHV6nWB2yk8pyo0adR*.7kCMdnj"

# Export/load manifest for incremental builds
manifest = registry.to_manifest()
registry.load_manifest(manifest)
```

#### `ImageProcessor`

Build-time image processing:

```python
from pynext.bundler.images import ImageProcessor

processor = ImageProcessor(
    source_dir=Path("./public"),
    output_dir=Path("./dist/_next/image"),
    config=ImageConfig(),
    max_workers=4,  # Parallel processing
)

# Process all registered images
results = await processor.process_all()

# Results include:
# - success: bool
# - src: original path
# - optimized: OptimizedImage with all variants
# - processing_time_ms: float
# - error: Optional[str]
```

### Build Integration

The CLI `build` command automatically processes images:

```python
# In pynext/cli.py

def cmd_build(args):
    # ... bundle npm packages ...
    
    # Process images (build-time optimization)
    from pynext.bundler.images import process_images_for_build
    
    result = asyncio.run(process_images_for_build(
        source_dir=Path(args.static),
        output_dir=Path(args.output) / "_next" / "image",
    ))
    
    print(f"[PyNext] Processed {result['successful']}/{result['total']} images")
    
    # ... scan routes, generate manifest ...
```

### Incremental Builds

Images are only reprocessed if their content changes:

```
Build 1: Process 100 images → 30 seconds
Build 2: 2 images changed → 0.6 seconds (98 cached)
```

The manifest tracks content hashes:

```json
{
  "/images/hero.jpg:abc123def456": {
    "original": "/images/hero.jpg",
    "hash": "abc123def456",
    "width": 1920,
    "height": 1080,
    "variants": {
      "avif": { "640w": "/_next/image/abc123_640w.avif", ... },
      "webp": { "640w": "/_next/image/abc123_640w.webp", ... },
      "jpeg": { "640w": "/_next/image/abc123_640w.jpg", ... }
    },
    "blurHash": "LEHV6nWB2yk8pyo0adR*.7kCMdnj",
    "blurDataUrl": "data:image/webp;base64,UklGR...",
    "dominantColor": "#4a7c8f"
  }
}
```

## Dependencies

### Required

- **Python 3.8+** - Core framework

### Optional (Recommended)

- **Pillow** - Image resizing, format conversion
  ```bash
  pip install Pillow
  ```

- **blurhash-python** - BlurHash placeholder generation
  ```bash
  pip install blurhash-python
  ```

Without these, images are served as-is without optimization.

### Supported Formats

| Format | Read | Write | Notes |
|--------|------|-------|-------|
| JPEG | ✅ | ✅ | Universal fallback |
| PNG | ✅ | ✅ | Lossless |
| WebP | ✅ | ✅ | Wide browser support |
| AVIF | ✅ | ✅* | Requires Pillow 9.1+ |
| GIF | ✅ | ✅ | Animated support |
| SVG | ✅ | - | Pass-through (no processing) |

*AVIF encoding requires `pillow-avif-plugin` or Pillow 10+

## API Reference

### Image Component

```python
def Image(
    src: Union[str, Signal],    # Image source
    alt: str,                    # Alt text (required)
    width: Optional[int],        # Width in pixels
    height: Optional[int],       # Height in pixels
    layout: ImageLayout,         # INTRINSIC, FIXED, RESPONSIVE, FILL
    loading: ImageLoading,       # LAZY, EAGER, PRIORITY
    priority: bool,              # Preload in head
    placeholder: str,            # "blur", "color", "empty"
    quality: Optional[int],      # Override quality (1-100)
    sizes: Optional[str],        # CSS sizes attribute
    className: str,              # CSS class
    style: Dict[str, str],       # Inline styles
    on_load: Callable,           # Load callback (requires JS)
    on_error: Callable,          # Error callback (requires JS)
) -> str
```

### Enums

```python
class ImageFormat(Enum):
    AVIF = "avif"    # Best compression, modern browsers
    WEBP = "webp"    # Good compression, wide support
    PNG = "png"      # Lossless fallback
    JPEG = "jpeg"    # Universal fallback
    GIF = "gif"      # Animated images
    SVG = "svg"      # Vector (no processing)

class ImageLayout(Enum):
    INTRINSIC = "intrinsic"    # Original aspect ratio
    FIXED = "fixed"            # Exact dimensions
    RESPONSIVE = "responsive"  # Scales with container
    FILL = "fill"              # Fills parent

class ImageLoading(Enum):
    LAZY = "lazy"        # Native lazy loading
    EAGER = "eager"      # Load immediately  
    PRIORITY = "priority"  # Preload in <head>
```

### Helper Functions

```python
from pynext import (
    get_image_registry,     # Get global registry
    get_image_config,       # Get global config
    configure_images,       # Set global config
)

from pynext.bundler.images import (
    ImageProcessor,           # Build-time processor
    process_images_for_build, # Helper for CLI
)
```

## Troubleshooting

### "Image processing skipped (Pillow not installed)"

Install the required dependency:
```bash
pip install Pillow
```

### AVIF encoding fails

AVIF requires Pillow 10+ or the `pillow-avif-plugin`:
```bash
pip install pillow-avif-plugin
# or upgrade Pillow
pip install --upgrade Pillow
```

### Images not optimized in development

Image optimization runs during `pynext build`. In development mode (`pynext dev`), images are served as-is for faster iteration.

### Large build times

- Reduce the number of sizes in `ImageConfig.sizes`
- Increase `max_workers` for more parallelism
- Use incremental builds (don't delete the manifest)

## Performance Targets

| Metric | Next.js | PyNext |
|--------|---------|--------|
| Client JS | ~15KB | **0 KB** (static) |
| Initial Load | Image loader init | **Instant** |
| LCP Impact | JS execution first | **Immediate render** |
| Build Time | N/A | ~50ms/image |
| Cache Strategy | Runtime cache | **CDN-friendly** |
| Locale Switch | Re-render images | **No change** |

