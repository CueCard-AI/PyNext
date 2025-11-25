"""
Build-Time Font Processor for PyNext.

Handles font optimization at build time:
- Font subsetting (only include used characters)
- Format conversion (WOFF2 generation)
- Metrics extraction for size-adjust
- Google Fonts download and caching
- CSS generation with precomputed values

Zero runtime overhead - all work done at build.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, List, Set, Any
import hashlib
import json
import re
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

from pynext.core.font import (
    FontConfig,
    FontRegistry,
    OptimizedFont,
    FontVariant,
    FontMetrics,
    FontStyle,
    FontWeight,
    get_font_registry,
    generate_font_css,
    generate_preload_link,
    SYSTEM_FONT_METRICS,
)


@dataclass
class FontProcessorConfig:
    """Configuration for font processing."""
    output_dir: Path = Path("static/_fonts")
    cache_dir: Path = Path(".pynext/font-cache")
    download_google_fonts: bool = True  # Download Google Fonts locally
    generate_woff2: bool = True  # Convert to WOFF2
    subset_fonts: bool = True  # Subset to used characters
    extract_metrics: bool = True  # Extract metrics for size-adjust
    inline_critical: bool = True  # Inline critical fonts as base64
    critical_threshold: int = 10000  # Max size (bytes) for inline
    parallel_downloads: int = 4


class FontProcessor:
    """
    Build-time font processor.
    
    Optimizes fonts for production:
    1. Downloads Google Fonts locally (avoids external request)
    2. Subsets fonts to only used characters
    3. Converts to WOFF2 for best compression
    4. Extracts metrics for size-adjust calculation
    5. Generates optimized CSS
    """
    
    def __init__(self, config: Optional[FontProcessorConfig] = None):
        self.config = config or FontProcessorConfig()
        self._metrics_cache: Dict[str, FontMetrics] = {}
        self._download_cache: Dict[str, Path] = {}
    
    def process_fonts(
        self,
        registry: Optional[FontRegistry] = None,
        project_root: Optional[Path] = None,
    ) -> Dict[str, OptimizedFont]:
        """
        Process all pending fonts in the registry.
        
        Returns dict of optimized fonts.
        """
        registry = registry or get_font_registry()
        project_root = project_root or Path.cwd()
        
        # Ensure directories exist
        output_dir = project_root / self.config.output_dir
        cache_dir = project_root / self.config.cache_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        pending = registry.get_pending()
        if not pending:
            return {}
        
        results: Dict[str, OptimizedFont] = {}
        
        # Process fonts in parallel
        with ThreadPoolExecutor(max_workers=self.config.parallel_downloads) as executor:
            futures = {
                executor.submit(
                    self._process_font, 
                    config, 
                    registry.get_chars_for_family(config.family),
                    output_dir,
                    cache_dir,
                ): config
                for config in pending
            }
            
            for future in as_completed(futures):
                config = futures[future]
                try:
                    optimized = future.result()
                    if optimized:
                        registry.set(config, optimized)
                        results[config.family] = optimized
                except Exception as e:
                    print(f"Error processing font {config.family}: {e}")
        
        registry.clear_pending()
        return results
    
    def _process_font(
        self,
        config: FontConfig,
        used_chars: Set[str],
        output_dir: Path,
        cache_dir: Path,
    ) -> Optional[OptimizedFont]:
        """Process a single font configuration."""
        
        # Generate hash for caching
        hash_input = f"{config.family}-{config.weight}-{config.style.value}"
        if config.subset_text:
            hash_input += f"-{config.subset_text}"
        font_hash = hashlib.md5(hash_input.encode()).hexdigest()[:12]
        
        # Check cache
        cache_file = cache_dir / f"{font_hash}.json"
        if cache_file.exists():
            cached = self._load_cached_font(cache_file)
            if cached:
                return cached
        
        # Determine source type
        src = config.src
        if isinstance(src, str):
            if src.startswith("http"):
                # Google Font or external URL
                local_paths = self._download_font(src, config, cache_dir)
            elif Path(src).exists():
                local_paths = [src]
            else:
                # Assume it's a Google Font family name
                google_url = self._get_google_font_url(config)
                local_paths = self._download_font(google_url, config, cache_dir)
        else:
            local_paths = [s for s in src if Path(s).exists()]
        
        if not local_paths:
            # Generate CSS without local files (will use CDN)
            return self._generate_remote_font(config, font_hash)
        
        # Extract metrics if we have fonttools
        metrics = None
        if self.config.extract_metrics:
            metrics = self._extract_metrics(local_paths[0])
        
        # Subset font if enabled
        if self.config.subset_fonts and used_chars:
            local_paths = self._subset_fonts(local_paths, used_chars, output_dir)
        
        # Convert to WOFF2 if needed
        if self.config.generate_woff2:
            local_paths = self._convert_to_woff2(local_paths, output_dir)
        
        # Copy to output directory
        final_paths = self._copy_to_output(local_paths, output_dir, font_hash)
        
        # Generate variants
        variants = self._generate_variants(config, final_paths)
        
        # Calculate size-adjust for fallback
        fallback_css = ""
        if config.adjust_fallback and metrics and config.fallback:
            fallback_css = self._generate_fallback_css(config, metrics)
        
        # Generate CSS
        css = generate_font_css(config)
        
        # Generate preload links
        preload_links = []
        if config.preload:
            for path in final_paths:
                preload_links.append(generate_preload_link(f"/_fonts/{Path(path).name}"))
        
        optimized = OptimizedFont(
            family=config.family,
            hash=font_hash,
            variants=variants,
            css=css,
            fallback_css=fallback_css,
            preload_links=preload_links,
            metrics=metrics,
        )
        
        # Cache result
        self._save_cached_font(cache_file, optimized)
        
        return optimized
    
    def _download_font(
        self,
        url: str,
        config: FontConfig,
        cache_dir: Path,
    ) -> List[str]:
        """Download font from URL and return local paths."""
        # For Google Fonts CSS, parse and download actual font files
        if "fonts.googleapis.com" in url:
            return self._download_google_font(url, config, cache_dir)
        
        # Direct font file download
        filename = Path(url).name
        if not filename.endswith(('.woff2', '.woff', '.ttf', '.otf')):
            filename = f"{config.family.lower().replace(' ', '-')}.woff2"
        
        local_path = cache_dir / filename
        
        if local_path.exists():
            return [str(local_path)]
        
        try:
            urllib.request.urlretrieve(url, local_path)
            return [str(local_path)]
        except urllib.error.URLError as e:
            print(f"Failed to download font from {url}: {e}")
            return []
    
    def _download_google_font(
        self,
        css_url: str,
        config: FontConfig,
        cache_dir: Path,
    ) -> List[str]:
        """Download Google Font and return local paths."""
        try:
            # Add user agent to get WOFF2
            request = urllib.request.Request(
                css_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )
            
            with urllib.request.urlopen(request) as response:
                css = response.read().decode('utf-8')
            
            # Parse font URLs from CSS
            font_urls = re.findall(r'url\((https://fonts\.gstatic\.com[^)]+)\)', css)
            
            local_paths = []
            for font_url in font_urls:
                # Generate filename from URL hash
                url_hash = hashlib.md5(font_url.encode()).hexdigest()[:8]
                ext = Path(font_url).suffix or ".woff2"
                filename = f"{config.family.lower().replace(' ', '-')}-{url_hash}{ext}"
                local_path = cache_dir / filename
                
                if not local_path.exists():
                    try:
                        urllib.request.urlretrieve(font_url, local_path)
                    except Exception as e:
                        print(f"Failed to download {font_url}: {e}")
                        continue
                
                local_paths.append(str(local_path))
            
            return local_paths
            
        except Exception as e:
            print(f"Failed to download Google Font: {e}")
            return []
    
    def _get_google_font_url(self, config: FontConfig) -> str:
        """Generate Google Fonts CSS URL from config."""
        family = config.family.replace(" ", "+")
        
        weights: List[int] = []
        if isinstance(config.weight, int):
            weights = [config.weight]
        elif isinstance(config.weight, str):
            weights = [FontWeight.from_value(config.weight)]
        elif isinstance(config.weight, range):
            weights = list(config.weight)
        elif isinstance(config.weight, list):
            weights = [FontWeight.from_value(w) for w in config.weight]
        
        weight_str = ";".join(str(w) for w in sorted(weights))
        
        url = f"https://fonts.googleapis.com/css2?family={family}:wght@{weight_str}&display=swap"
        return url
    
    def _extract_metrics(self, font_path: str) -> Optional[FontMetrics]:
        """Extract font metrics from a font file."""
        try:
            from fontTools.ttLib import TTFont
            
            font = TTFont(font_path)
            
            # Get OS/2 table for metrics
            os2 = font.get('OS/2')
            head = font.get('head')
            hhea = font.get('hhea')
            
            if not os2 or not head:
                return None
            
            metrics = FontMetrics(
                units_per_em=head.unitsPerEm,
                ascender=hhea.ascent if hhea else os2.sTypoAscender,
                descender=hhea.descent if hhea else os2.sTypoDescender,
                line_gap=hhea.lineGap if hhea else os2.sTypoLineGap,
                x_height=os2.sxHeight if hasattr(os2, 'sxHeight') else None,
                cap_height=os2.sCapHeight if hasattr(os2, 'sCapHeight') else None,
            )
            
            font.close()
            return metrics
            
        except ImportError:
            # fonttools not available
            return None
        except Exception as e:
            print(f"Failed to extract metrics from {font_path}: {e}")
            return None
    
    def _subset_fonts(
        self,
        font_paths: List[str],
        chars: Set[str],
        output_dir: Path,
    ) -> List[str]:
        """Subset fonts to only include used characters."""
        try:
            from fontTools import subset
            
            result_paths = []
            
            for font_path in font_paths:
                # Create subset options
                options = subset.Options()
                options.layout_features = ['*']  # Keep all features
                options.name_IDs = ['*']  # Keep name table
                options.notdef_outline = True
                
                # Load font
                font = subset.load_font(font_path, options)
                
                # Create subsetter
                subsetter = subset.Subsetter(options)
                subsetter.populate(text="".join(chars))
                subsetter.subset(font)
                
                # Save subset
                base_name = Path(font_path).stem
                subset_path = output_dir / f"{base_name}-subset.woff2"
                subset.save_font(font, str(subset_path), options)
                
                result_paths.append(str(subset_path))
            
            return result_paths
            
        except ImportError:
            # fonttools not available, return original
            return font_paths
        except Exception as e:
            print(f"Failed to subset fonts: {e}")
            return font_paths
    
    def _convert_to_woff2(
        self,
        font_paths: List[str],
        output_dir: Path,
    ) -> List[str]:
        """Convert fonts to WOFF2 format."""
        try:
            from fontTools.ttLib import TTFont
            
            result_paths = []
            
            for font_path in font_paths:
                if font_path.endswith('.woff2'):
                    result_paths.append(font_path)
                    continue
                
                # Convert to WOFF2
                font = TTFont(font_path)
                base_name = Path(font_path).stem
                woff2_path = output_dir / f"{base_name}.woff2"
                font.flavor = 'woff2'
                font.save(str(woff2_path))
                font.close()
                
                result_paths.append(str(woff2_path))
            
            return result_paths
            
        except ImportError:
            return font_paths
        except Exception as e:
            print(f"Failed to convert to WOFF2: {e}")
            return font_paths
    
    def _copy_to_output(
        self,
        font_paths: List[str],
        output_dir: Path,
        font_hash: str,
    ) -> List[str]:
        """Copy fonts to output directory with hashed names."""
        import shutil
        
        result_paths = []
        
        for font_path in font_paths:
            src = Path(font_path)
            dest = output_dir / f"{src.stem}-{font_hash}{src.suffix}"
            
            if not dest.exists():
                shutil.copy2(src, dest)
            
            result_paths.append(str(dest))
        
        return result_paths
    
    def _generate_variants(
        self,
        config: FontConfig,
        paths: List[str],
    ) -> List[FontVariant]:
        """Generate font variants from config and paths."""
        variants = []
        
        weights: List[int] = []
        if isinstance(config.weight, int):
            weights = [config.weight]
        elif isinstance(config.weight, str):
            weights = [FontWeight.from_value(config.weight)]
        elif isinstance(config.weight, range):
            weights = list(config.weight)
        elif isinstance(config.weight, list):
            weights = [FontWeight.from_value(w) for w in config.weight]
        
        # Match paths to weights (simplified - assumes one path per weight)
        for i, weight in enumerate(weights):
            path = paths[i] if i < len(paths) else paths[0]
            variants.append(FontVariant(
                weight=weight,
                style=config.style,
                src=path,
            ))
        
        return variants
    
    def _generate_fallback_css(
        self,
        config: FontConfig,
        metrics: FontMetrics,
    ) -> str:
        """Generate fallback font CSS with size-adjust."""
        primary_fallback = config.fallback[0] if config.fallback else "Arial"
        
        # Get fallback metrics
        fallback_metrics = SYSTEM_FONT_METRICS.get(primary_fallback)
        if not fallback_metrics:
            fallback_metrics = SYSTEM_FONT_METRICS.get("Arial", FontMetrics())
        
        # Calculate size-adjust
        size_adjust = metrics.calculate_size_adjust(fallback_metrics)
        
        # Calculate override values
        ascent_override = (metrics.ascender / metrics.units_per_em) * 100
        descent_override = abs(metrics.descender / metrics.units_per_em) * 100
        line_gap_override = (metrics.line_gap / metrics.units_per_em) * 100
        
        return f"""@font-face {{
  font-family: "{config.family} Fallback";
  src: local("{primary_fallback}");
  size-adjust: {size_adjust:.2f}%;
  ascent-override: {ascent_override:.2f}%;
  descent-override: {descent_override:.2f}%;
  line-gap-override: {line_gap_override:.2f}%;
}}"""
    
    def _generate_remote_font(
        self,
        config: FontConfig,
        font_hash: str,
    ) -> OptimizedFont:
        """Generate font config for remote/CDN fonts."""
        css = generate_font_css(config)
        
        return OptimizedFont(
            family=config.family,
            hash=font_hash,
            variants=[],
            css=css,
            fallback_css="",
            preload_links=[],
        )
    
    def _load_cached_font(self, cache_file: Path) -> Optional[OptimizedFont]:
        """Load cached font data."""
        try:
            with open(cache_file) as f:
                data = json.load(f)
            
            return OptimizedFont(
                family=data["family"],
                hash=data["hash"],
                variants=[
                    FontVariant(
                        weight=v["weight"],
                        style=FontStyle(v["style"]),
                        src=v.get("src"),
                        unicode_range=v.get("unicodeRange"),
                    )
                    for v in data.get("variants", [])
                ],
                css=data["css"],
                fallback_css=data.get("fallbackCss", ""),
                preload_links=data.get("preloadLinks", []),
            )
        except Exception:
            return None
    
    def _save_cached_font(self, cache_file: Path, font: OptimizedFont) -> None:
        """Save font data to cache."""
        try:
            data = {
                "family": font.family,
                "hash": font.hash,
                "variants": [
                    {
                        "weight": v.weight,
                        "style": v.style.value,
                        "src": v.src,
                        "unicodeRange": v.unicode_range,
                    }
                    for v in font.variants
                ],
                "css": font.css,
                "fallbackCss": font.fallback_css,
                "preloadLinks": font.preload_links,
            }
            
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Failed to cache font: {e}")


def process_fonts_for_build(
    project_root: Optional[Path] = None,
    config: Optional[FontProcessorConfig] = None,
) -> Dict[str, OptimizedFont]:
    """
    Process all registered fonts for production build.
    
    Called by CLI build command.
    """
    processor = FontProcessor(config)
    return processor.process_fonts(project_root=project_root)

