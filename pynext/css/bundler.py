"""
CSS Bundler - Combine and Optimize CSS

Collects all scoped CSS from the application and bundles
it into optimized output files for production.

Features:
- Combines all component CSS into single file
- Removes duplicate rules
- Minifies output
- Generates source maps
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from .extractor import ExtractedCSS, CSSExtractor
from .scoper import get_global_scoper


@dataclass
class BundleStats:
    """
    Statistics about the CSS bundle.
    
    Attributes:
        total_size: Total bytes in bundle
        minified_size: Size after minification
        component_count: Number of components
        class_count: Total number of classes
        rule_count: Number of CSS rules
    """
    total_size: int
    minified_size: int
    component_count: int
    class_count: int
    rule_count: int
    
    @property
    def compression_ratio(self) -> float:
        """Ratio of minified to original size."""
        if self.total_size == 0:
            return 1.0
        return self.minified_size / self.total_size


@dataclass
class CSSBundle:
    """
    A bundled CSS output.
    
    Attributes:
        css: The bundled CSS string
        minified: Minified version
        source_map: Optional source map
        stats: Bundle statistics
        components: List of included components
    """
    css: str
    minified: str
    source_map: Optional[str]
    stats: BundleStats
    components: List[str]
    
    def write(self, path: Path, minify: bool = True):
        """
        Write bundle to file.
        
        Args:
            path: Output path
            minify: Whether to write minified version
        """
        content = self.minified if minify else self.css
        path.write_text(content, encoding="utf-8")
        
        # Write source map if available
        if self.source_map:
            map_path = path.with_suffix(path.suffix + ".map")
            map_path.write_text(self.source_map, encoding="utf-8")


class CSSBundler:
    """
    Bundles CSS from multiple sources into optimized output.
    
    The bundler:
    1. Collects CSS from all components
    2. Deduplicates identical rules
    3. Sorts for optimal compression
    4. Minifies output
    
    Example:
        >>> bundler = CSSBundler()
        >>> bundler.add_css("Button", ".button { padding: 8px; }")
        >>> bundler.add_css("Card", ".card { border: 1px solid; }")
        >>> bundle = bundler.bundle()
        >>> print(bundle.stats)
    """
    
    def __init__(self):
        self._css_parts: Dict[str, str] = {}
        self._order: List[str] = []
    
    def add_css(self, component: str, css: str):
        """
        Add CSS from a component.
        
        Args:
            component: Component name
            css: Scoped CSS string
        """
        if component not in self._css_parts:
            self._order.append(component)
        self._css_parts[component] = css
    
    def add_extracted(self, extracted: ExtractedCSS):
        """
        Add extracted CSS.
        
        Args:
            extracted: ExtractedCSS object
        """
        self.add_css(extracted.component, extracted.scoped_css)
    
    def add_from_directory(
        self,
        directory: Path,
        recursive: bool = True,
    ):
        """
        Add all CSS from a directory.
        
        Args:
            directory: Directory to scan
            recursive: Whether to scan subdirectories
        """
        extractor = CSSExtractor()
        for extracted in extractor.extract_directory(directory, recursive):
            self.add_extracted(extracted)
    
    def add_from_global_scoper(self):
        """Add all CSS registered with the global scoper."""
        global_scoper = get_global_scoper()
        all_css = global_scoper.get_all_css()
        if all_css:
            self._css_parts["__global__"] = all_css
            if "__global__" not in self._order:
                self._order.insert(0, "__global__")
    
    def bundle(
        self,
        minify: bool = True,
        source_map: bool = False,
    ) -> CSSBundle:
        """
        Generate the CSS bundle.
        
        Args:
            minify: Whether to minify output
            source_map: Whether to generate source map
            
        Returns:
            CSSBundle with bundled CSS
        """
        # Combine CSS in order
        parts = []
        for component in self._order:
            css = self._css_parts[component]
            if component != "__global__":
                parts.append(f"/* {component} */")
            parts.append(css)
        
        combined = "\n\n".join(parts)
        
        # Deduplicate rules
        deduped = self._deduplicate(combined)
        
        # Minify
        minified = self._minify(deduped) if minify else deduped
        
        # Generate source map
        sm = self._generate_source_map(deduped) if source_map else None
        
        # Calculate stats
        stats = BundleStats(
            total_size=len(deduped.encode("utf-8")),
            minified_size=len(minified.encode("utf-8")),
            component_count=len(self._css_parts),
            class_count=self._count_classes(deduped),
            rule_count=self._count_rules(deduped),
        )
        
        return CSSBundle(
            css=deduped,
            minified=minified,
            source_map=sm,
            stats=stats,
            components=list(self._order),
        )
    
    def _deduplicate(self, css: str) -> str:
        """Remove duplicate CSS rules."""
        # Parse rules
        rule_pattern = re.compile(r"([^{]+)\{([^}]*)\}", re.MULTILINE)
        seen_rules: Dict[str, str] = {}
        
        def process_rule(match: re.Match) -> str:
            selector = match.group(1).strip()
            properties = match.group(2).strip()
            
            key = f"{selector}:{properties}"
            if key in seen_rules:
                return ""  # Remove duplicate
            
            seen_rules[key] = match.group(0)
            return match.group(0)
        
        result = rule_pattern.sub(process_rule, css)
        
        # Clean up extra whitespace
        result = re.sub(r"\n{3,}", "\n\n", result)
        return result.strip()
    
    def _minify(self, css: str) -> str:
        """
        Minify CSS.
        
        Performs:
        - Remove comments
        - Remove whitespace
        - Shorten color codes
        """
        # Remove comments
        css = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
        
        # Remove newlines and extra whitespace
        css = re.sub(r"\s+", " ", css)
        
        # Remove whitespace around special characters
        css = re.sub(r"\s*([{};:,>+~])\s*", r"\1", css)
        
        # Remove trailing semicolons before closing braces
        css = re.sub(r";}", "}", css)
        
        # Shorten color codes (#ffffff -> #fff)
        def shorten_hex(match: re.Match) -> str:
            color = match.group(1)
            if len(color) == 6:
                if color[0] == color[1] and color[2] == color[3] and color[4] == color[5]:
                    return f"#{color[0]}{color[2]}{color[4]}"
            return match.group(0)
        
        css = re.sub(r"#([0-9a-fA-F]{6})\b", shorten_hex, css)
        
        return css.strip()
    
    def _generate_source_map(self, css: str) -> str:
        """Generate a basic source map."""
        # Simplified source map - just tracks components
        mappings = []
        for i, component in enumerate(self._order):
            mappings.append(f"{component}:{i}")
        
        return f"/* SourceMap: {', '.join(mappings)} */"
    
    def _count_classes(self, css: str) -> int:
        """Count unique class selectors."""
        matches = re.findall(r"\.([a-zA-Z_][a-zA-Z0-9_-]*)", css)
        return len(set(matches))
    
    def _count_rules(self, css: str) -> int:
        """Count CSS rules."""
        return len(re.findall(r"\{[^}]*\}", css))
    
    def clear(self):
        """Clear all added CSS."""
        self._css_parts.clear()
        self._order.clear()


def bundle_css(
    directories: List[Path],
    output: Path,
    minify: bool = True,
) -> CSSBundle:
    """
    Bundle CSS from multiple directories.
    
    Convenience function for common bundling workflow.
    
    Args:
        directories: List of directories to scan
        output: Output file path
        minify: Whether to minify
        
    Returns:
        CSSBundle written to output path
        
    Example:
        >>> bundle = bundle_css(
        ...     directories=[Path("components"), Path("pages")],
        ...     output=Path("dist/styles.css"),
        ...     minify=True,
        ... )
        >>> print(f"Bundled {bundle.stats.component_count} components")
    """
    bundler = CSSBundler()
    
    # Add from global scoper first
    bundler.add_from_global_scoper()
    
    # Add from directories
    for directory in directories:
        if directory.exists():
            bundler.add_from_directory(directory)
    
    # Generate bundle
    bundle = bundler.bundle(minify=minify)
    
    # Write output
    output.parent.mkdir(parents=True, exist_ok=True)
    bundle.write(output, minify=minify)
    
    return bundle

