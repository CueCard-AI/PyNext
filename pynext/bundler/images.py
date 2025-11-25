"""
PyNext Image Processor - Build-Time Optimization.

Processes images at build time to generate:
- Multiple format variants (AVIF, WebP, JPEG)
- Multiple size variants for srcset
- BlurHash placeholders
- Dominant color extraction
- Image manifest for caching

This runs during `pynext build`, not at runtime, ensuring
zero processing overhead for production serving.
"""

import asyncio
import hashlib
import json
import struct
import zlib
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import base64
import io
import math

# Image processing imports (optional dependencies)
try:
    from PIL import Image as PILImage
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

try:
    import blurhash
    HAS_BLURHASH = True
except ImportError:
    HAS_BLURHASH = False


from pynext.core.image import (
    ImageConfig,
    ImageFormat,
    ImageSize,
    OptimizedImage,
    get_image_config,
    get_image_registry,
)


@dataclass
class ProcessingResult:
    """Result of processing a single image."""
    success: bool
    src: str
    optimized: Optional[OptimizedImage] = None
    error: Optional[str] = None
    processing_time_ms: float = 0


class ImageProcessor:
    """
    Build-time image processor for PyNext.
    
    Optimizes all registered images during the build phase:
    1. Generates format variants (AVIF, WebP, JPEG)
    2. Generates size variants for responsive srcset
    3. Computes BlurHash for placeholders
    4. Extracts dominant color
    5. Creates manifest for caching
    
    Uses parallel processing for speed.
    """
    
    def __init__(
        self,
        source_dir: Path,
        output_dir: Path,
        config: Optional[ImageConfig] = None,
        max_workers: int = 4
    ):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.config = config or get_image_config()
        self.max_workers = max_workers
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Manifest path
        self.manifest_path = self.output_dir / "image-manifest.json"
        
        # Load existing manifest for incremental builds
        self._manifest: Dict[str, Any] = {}
        if self.manifest_path.exists():
            try:
                self._manifest = json.loads(self.manifest_path.read_text())
            except json.JSONDecodeError:
                pass
    
    async def process_all(self) -> List[ProcessingResult]:
        """
        Process all pending images in the registry.
        
        Returns list of processing results for reporting.
        """
        if not HAS_PILLOW:
            return [ProcessingResult(
                success=False,
                src="",
                error="Pillow not installed. Run: pip install Pillow"
            )]
        
        registry = get_image_registry()
        pending = registry.get_pending()
        
        if not pending:
            return []
        
        results = []
        
        # Process in parallel using thread pool
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [
                loop.run_in_executor(executor, self._process_single, src)
                for src in pending
            ]
            results = await asyncio.gather(*futures)
        
        # Update manifest
        self._save_manifest()
        
        # Clear pending
        registry.clear_pending()
        
        return results
    
    def process_single_sync(self, src: str) -> ProcessingResult:
        """Synchronous wrapper for processing a single image."""
        return self._process_single(src)
    
    def _process_single(self, src: str) -> ProcessingResult:
        """Process a single image file."""
        import time
        start_time = time.time()
        
        try:
            # Resolve source path
            if src.startswith("/"):
                source_path = self.source_dir / src[1:]
            else:
                source_path = self.source_dir / src
            
            if not source_path.exists():
                return ProcessingResult(
                    success=False,
                    src=src,
                    error=f"Image not found: {source_path}"
                )
            
            # Check if already processed (incremental build)
            file_hash = self._get_file_hash(source_path)
            cache_key = f"{src}:{file_hash}"
            
            if cache_key in self._manifest:
                cached = self._manifest[cache_key]
                optimized = OptimizedImage(
                    original_src=src,
                    hash=file_hash[:12],
                    width=cached["width"],
                    height=cached["height"],
                    variants=cached.get("variants", {}),
                    blur_hash=cached.get("blurHash"),
                    blur_data_url=cached.get("blurDataUrl"),
                    dominant_color=cached.get("dominantColor"),
                )
                get_image_registry().set(src, optimized)
                return ProcessingResult(
                    success=True,
                    src=src,
                    optimized=optimized,
                    processing_time_ms=(time.time() - start_time) * 1000
                )
            
            # Open and process image
            with PILImage.open(source_path) as img:
                # Get original dimensions
                orig_width, orig_height = img.size
                
                # Convert to RGB if necessary (for JPEG/WebP)
                if img.mode in ("RGBA", "P"):
                    rgb_img = img.convert("RGB")
                else:
                    rgb_img = img
                
                # Generate variants
                variants = self._generate_variants(img, rgb_img, src, file_hash)
                
                # Generate BlurHash
                blur_hash, blur_data_url = self._generate_blur_placeholder(img)
                
                # Extract dominant color
                dominant_color = self._extract_dominant_color(img)
                
                # Create optimized image object
                optimized = OptimizedImage(
                    original_src=src,
                    hash=file_hash[:12],
                    width=orig_width,
                    height=orig_height,
                    variants=variants,
                    blur_hash=blur_hash,
                    blur_data_url=blur_data_url,
                    dominant_color=dominant_color,
                )
                
                # Update registry
                get_image_registry().set(src, optimized)
                
                # Update manifest
                self._manifest[cache_key] = optimized.to_dict()
                
                processing_time = (time.time() - start_time) * 1000
                
                return ProcessingResult(
                    success=True,
                    src=src,
                    optimized=optimized,
                    processing_time_ms=processing_time
                )
                
        except Exception as e:
            return ProcessingResult(
                success=False,
                src=src,
                error=str(e),
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    def _generate_variants(
        self,
        img: "PILImage.Image",
        rgb_img: "PILImage.Image",
        src: str,
        file_hash: str
    ) -> Dict[str, Dict[str, str]]:
        """Generate format and size variants."""
        variants: Dict[str, Dict[str, str]] = {}
        
        orig_width, orig_height = img.size
        aspect_ratio = orig_height / orig_width if orig_width > 0 else 1
        
        for fmt in self.config.formats:
            if fmt == ImageFormat.SVG:
                continue  # Skip SVG (no processing needed)
            
            variants[fmt.value] = {}
            quality = self.config.quality.get(fmt, 80)
            
            for size in self.config.sizes:
                # Skip sizes larger than original
                if size.width > orig_width:
                    continue
                
                # Calculate height maintaining aspect ratio
                new_width = size.width
                new_height = size.height or int(new_width * aspect_ratio)
                
                # Resize image
                resized = img.resize(
                    (new_width, new_height),
                    PILImage.Resampling.LANCZOS
                )
                
                # Convert if needed (JPEG/WebP don't support alpha)
                if fmt in (ImageFormat.JPEG, ImageFormat.WEBP) and resized.mode == "RGBA":
                    resized = resized.convert("RGB")
                
                # Generate output path
                ext = fmt.value if fmt != ImageFormat.JPEG else "jpg"
                output_name = f"{file_hash[:12]}_{size.name}.{ext}"
                output_path = self.output_dir / output_name
                
                # Save with appropriate settings
                save_kwargs = {"quality": quality}
                if fmt == ImageFormat.AVIF:
                    save_kwargs["codec"] = "av1"
                elif fmt == ImageFormat.WEBP:
                    save_kwargs["method"] = 6  # Best compression
                
                try:
                    resized.save(output_path, **save_kwargs)
                    
                    # Store relative URL path
                    url_path = f"/{self.config.output_dir}/{output_name}"
                    variants[fmt.value][size.name] = url_path
                except Exception:
                    # Format not supported, skip
                    pass
        
        return variants
    
    def _generate_blur_placeholder(
        self,
        img: "PILImage.Image"
    ) -> Tuple[Optional[str], Optional[str]]:
        """Generate BlurHash and tiny blur data URL."""
        blur_hash = None
        blur_data_url = None
        
        # Generate tiny thumbnail for blur
        thumb_size = (self.config.blur_placeholder_width, 
                     int(self.config.blur_placeholder_width * img.height / img.width))
        thumb = img.resize(thumb_size, PILImage.Resampling.BOX)
        
        # Convert to RGB for consistency
        if thumb.mode != "RGB":
            thumb = thumb.convert("RGB")
        
        # Generate BlurHash if available
        if HAS_BLURHASH:
            try:
                blur_hash = blurhash.encode(
                    thumb,
                    x_components=self.config.blur_hash_size,
                    y_components=self.config.blur_hash_size
                )
            except Exception:
                pass
        
        # Generate tiny base64 data URL (always works)
        try:
            buffer = io.BytesIO()
            thumb.save(buffer, format="WEBP", quality=20)
            b64 = base64.b64encode(buffer.getvalue()).decode()
            blur_data_url = f"data:image/webp;base64,{b64}"
        except Exception:
            # Fallback to JPEG
            buffer = io.BytesIO()
            thumb.save(buffer, format="JPEG", quality=20)
            b64 = base64.b64encode(buffer.getvalue()).decode()
            blur_data_url = f"data:image/jpeg;base64,{b64}"
        
        return blur_hash, blur_data_url
    
    def _extract_dominant_color(self, img: "PILImage.Image") -> str:
        """Extract dominant color as hex string."""
        # Resize to tiny size for speed
        tiny = img.resize((10, 10), PILImage.Resampling.BOX)
        if tiny.mode != "RGB":
            tiny = tiny.convert("RGB")
        
        # Get all pixels
        pixels = list(tiny.getdata())
        
        # Simple average (good enough for placeholder)
        r = sum(p[0] for p in pixels) // len(pixels)
        g = sum(p[1] for p in pixels) // len(pixels)
        b = sum(p[2] for p in pixels) // len(pixels)
        
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def _get_file_hash(self, path: Path) -> str:
        """Get hash of file for cache invalidation."""
        hasher = hashlib.md5()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def _save_manifest(self) -> None:
        """Save manifest to disk."""
        self.manifest_path.write_text(
            json.dumps(self._manifest, indent=2)
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return {
            "total_images": len(self._manifest),
            "output_dir": str(self.output_dir),
            "formats": [f.value for f in self.config.formats],
            "sizes": [s.name for s in self.config.sizes],
        }


def create_placeholder_svg(width: int, height: int, color: str = "#e5e7eb") -> str:
    """Create a simple SVG placeholder for images before processing."""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect fill="{color}" width="100%" height="100%"/>
</svg>'''


def encode_svg_data_url(svg: str) -> str:
    """Encode SVG as data URL."""
    encoded = base64.b64encode(svg.encode()).decode()
    return f"data:image/svg+xml;base64,{encoded}"


async def process_images_for_build(
    source_dir: Path,
    output_dir: Path,
    config: Optional[ImageConfig] = None
) -> Dict[str, Any]:
    """
    Main entry point for build-time image processing.
    
    Called by `pynext build` command.
    
    Returns processing report.
    """
    processor = ImageProcessor(source_dir, output_dir, config)
    results = await processor.process_all()
    
    # Generate report
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]
    
    total_time = sum(r.processing_time_ms for r in results)
    
    return {
        "success": len(failed) == 0,
        "total": len(results),
        "successful": len(successful),
        "failed": len(failed),
        "total_time_ms": total_time,
        "errors": [{"src": r.src, "error": r.error} for r in failed],
        "stats": processor.get_stats(),
    }

