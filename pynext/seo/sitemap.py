"""
Sitemap Generation for PyNext.

Generate XML sitemaps with auto-discovery from router.

Example:
    from pynext import page, sitemap
    
    @sitemap(priority=0.8, changefreq="daily")
    @page
    def ProductPage(id: str):
        return Product(id)
    
    def get_sitemap_params():
        return [{"id": p.id} for p in Product.all()]

Why This Matters:
    Sitemaps tell search engines which pages to crawl.
    Without one, crawlers may miss important pages.
    With PyNext, sitemaps are generated automatically from your routes.

SolidJS Principles:
    - Fine-grained: Per-route config via decorator
    - Compile-time: URLs discovered at build
    - Minimal runtime: Static XML files preferred
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from xml.sax.saxutils import escape
import asyncio
import os


# ============================================
# Enums for Type Safety
# ============================================

class ChangeFreq(str, Enum):
    """
    How frequently the page is likely to change.
    
    Hints for search engines on how often to re-crawl.
    """
    ALWAYS = "always"      # Changes every time accessed
    HOURLY = "hourly"      # Changes every hour
    DAILY = "daily"        # Changes every day
    WEEKLY = "weekly"      # Changes every week
    MONTHLY = "monthly"    # Changes every month
    YEARLY = "yearly"      # Changes every year
    NEVER = "never"        # Archived content


# ============================================
# Data Classes
# ============================================

@dataclass
class SitemapEntry:
    """
    A single URL entry in the sitemap.
    
    Attributes:
        loc: Full URL (required)
        lastmod: Last modification date (ISO 8601)
        changefreq: How often the page changes
        priority: Relative priority 0.0-1.0
    
    Example:
        entry = SitemapEntry(
            loc="https://example.com/products/123",
            lastmod="2024-01-15",
            changefreq="daily",
            priority=0.8,
        )
    """
    loc: str
    lastmod: Optional[str] = None
    changefreq: Optional[str] = None
    priority: Optional[float] = None
    
    def __post_init__(self):
        """Validate entry fields."""
        if not self.loc:
            raise ValueError("SitemapEntry.loc is required")
        
        if not self.loc.startswith(("http://", "https://")):
            raise ValueError(f"SitemapEntry.loc must be absolute URL, got: {self.loc}")
        
        if self.priority is not None:
            if not 0.0 <= self.priority <= 1.0:
                raise ValueError(f"priority must be 0.0-1.0, got: {self.priority}")
        
        if self.changefreq is not None:
            valid = ["always", "hourly", "daily", "weekly", "monthly", "yearly", "never"]
            if self.changefreq not in valid:
                raise ValueError(f"changefreq must be one of {valid}, got: {self.changefreq}")
    
    def to_xml(self) -> str:
        """
        Convert to XML <url> element.
        
        Returns:
            XML string for this URL entry
        """
        lines = ["  <url>"]
        lines.append(f"    <loc>{escape(self.loc)}</loc>")
        
        if self.lastmod:
            lines.append(f"    <lastmod>{escape(self.lastmod)}</lastmod>")
        
        if self.changefreq:
            lines.append(f"    <changefreq>{escape(self.changefreq)}</changefreq>")
        
        if self.priority is not None:
            lines.append(f"    <priority>{self.priority:.1f}</priority>")
        
        lines.append("  </url>")
        return "\n".join(lines)


@dataclass
class SitemapConfig:
    """
    Configuration for a page's sitemap entry.
    
    Attached to pages via the @sitemap decorator.
    
    Attributes:
        priority: Page priority 0.0-1.0 (default 0.5)
        changefreq: How often content changes
        lastmod: Last modified date ("auto" uses file mtime)
        include: Whether to include in sitemap
    
    Example:
        config = SitemapConfig(
            priority=0.8,
            changefreq="daily",
            lastmod="auto",
        )
    """
    priority: float = 0.5
    changefreq: str = "weekly"
    lastmod: str = "auto"
    include: bool = True
    
    # Internal tracking
    _source_file: Optional[str] = field(default=None, repr=False)
    _function_name: Optional[str] = field(default=None, repr=False)
    
    def __post_init__(self):
        """Validate config fields."""
        if not 0.0 <= self.priority <= 1.0:
            raise ValueError(f"priority must be 0.0-1.0, got: {self.priority}")
        
        valid_freq = ["always", "hourly", "daily", "weekly", "monthly", "yearly", "never"]
        if self.changefreq not in valid_freq:
            raise ValueError(f"changefreq must be one of {valid_freq}, got: {self.changefreq}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "priority": self.priority,
            "changefreq": self.changefreq,
            "lastmod": self.lastmod,
            "include": self.include,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SitemapConfig":
        """Create from dictionary."""
        return cls(
            priority=data.get("priority", 0.5),
            changefreq=data.get("changefreq", "weekly"),
            lastmod=data.get("lastmod", "auto"),
            include=data.get("include", True),
        )


# ============================================
# Global Registry
# ============================================

# Registry mapping function IDs to configs
_sitemap_configs: Dict[str, SitemapConfig] = {}


def _get_function_id(fn: Callable) -> str:
    """Get unique identifier for a function."""
    module = getattr(fn, "__module__", "__main__")
    name = getattr(fn, "__name__", str(fn))
    return f"{module}.{name}"


def clear_sitemap_configs() -> None:
    """Clear all registered configs (for testing)."""
    _sitemap_configs.clear()


# ============================================
# Decorator
# ============================================

def sitemap(
    priority: float = 0.5,
    changefreq: str = "weekly",
    lastmod: str = "auto",
    include: bool = True,
) -> Callable[[Callable], Callable]:
    """
    Configure sitemap entry for a page.
    
    Decorate your page function to include it in the sitemap
    with the specified settings.
    
    Args:
        priority: Page importance 0.0-1.0 (default 0.5)
            - 1.0: Most important (homepage)
            - 0.8: Very important (main sections)
            - 0.5: Normal (default)
            - 0.3: Less important
        
        changefreq: How often content changes
            - "always": Every access
            - "hourly": Every hour
            - "daily": Every day
            - "weekly": Every week (default)
            - "monthly": Every month
            - "yearly": Every year
            - "never": Never changes (archived)
        
        lastmod: Last modification date
            - "auto": Use file modification time (default)
            - "2024-01-15": Specific date (ISO format)
            - None: Don't include lastmod
        
        include: Whether to include in sitemap (default True)
            Set to False to explicitly exclude a page.
    
    Returns:
        Decorated function with __sitemap_config__ attribute
    
    Example:
        # Include with high priority
        @sitemap(priority=0.9, changefreq="daily")
        @page
        def HomePage():
            return Home()
        
        # Exclude from sitemap
        @sitemap(include=False)
        @page
        def AdminPage():
            return Admin()
        
        # Dynamic route with params
        @sitemap(priority=0.7)
        @page
        def ProductPage(id: str):
            return Product(id)
        
        # PyNext calls this to get all URLs
        def get_sitemap_params():
            return [{"id": p.id} for p in Product.all()]
    """
    config = SitemapConfig(
        priority=priority,
        changefreq=changefreq,
        lastmod=lastmod,
        include=include,
    )
    
    def decorator(fn: Callable) -> Callable:
        # Store source info
        config._source_file = getattr(fn, "__module__", None)
        config._function_name = getattr(fn, "__name__", None)
        
        # Attach config to function
        fn.__sitemap_config__ = config
        
        # Register globally
        fn_id = _get_function_id(fn)
        _sitemap_configs[fn_id] = config
        
        @wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)
        
        wrapper.__sitemap_config__ = config
        return wrapper
    
    return decorator


def get_sitemap_config(fn: Callable) -> Optional[SitemapConfig]:
    """
    Get SitemapConfig attached to a function.
    
    Args:
        fn: Function to check
    
    Returns:
        SitemapConfig if decorated, None otherwise
    """
    return getattr(fn, "__sitemap_config__", None)


def has_sitemap_config(fn: Callable) -> bool:
    """
    Check if function has SitemapConfig attached.
    
    Args:
        fn: Function to check
    
    Returns:
        True if decorated with @sitemap
    """
    return hasattr(fn, "__sitemap_config__")


# ============================================
# Sitemap Generator
# ============================================

class SitemapGenerator:
    """
    Generates XML sitemaps from router.
    
    Auto-discovers URLs from registered routes and generates
    properly formatted sitemap XML.
    
    Example:
        from pynext.seo import SitemapGenerator
        
        generator = SitemapGenerator(router, "https://example.com")
        xml = generator.generate()
        print(xml)
    
    Features:
        - Auto-discovery from router
        - Dynamic route support via get_sitemap_params()
        - Automatic sitemap index for > 50k URLs
        - Streaming generation for large sitemaps
    """
    
    # Maximum URLs per sitemap (Google's limit is 50,000)
    MAX_URLS_PER_SITEMAP = 50000
    
    # Maximum sitemap file size (50MB uncompressed)
    MAX_SITEMAP_SIZE = 50 * 1024 * 1024
    
    def __init__(self, router: Any, base_url: str):
        """
        Initialize generator.
        
        Args:
            router: FileRouter instance with routes
            base_url: Base URL for all entries (e.g., "https://example.com")
        """
        self.router = router
        self.base_url = base_url.rstrip("/")
        self._entries: List[SitemapEntry] = []
    
    def discover_urls(self) -> List[SitemapEntry]:
        """
        Auto-discover URLs from router.
        
        Iterates through all registered routes and creates
        sitemap entries based on their @sitemap configuration.
        
        For dynamic routes (with parameters), calls the module's
        get_sitemap_params() function to get all parameter combinations.
        
        Returns:
            List of SitemapEntry objects
        """
        entries = []
        
        for route in getattr(self.router, "routes", []):
            # Get config from handler
            config = self._get_route_config(route)
            
            # Skip if not configured or excluded
            if not config or not config.include:
                continue
            
            # Check if route has dynamic parameters
            has_params = self._route_has_params(route)
            
            if not has_params:
                # Static route - single URL
                entry = self._create_entry(route, config, {})
                if entry:
                    entries.append(entry)
            else:
                # Dynamic route - get all param combinations
                params_list = self._get_dynamic_params(route)
                for params in params_list:
                    entry = self._create_entry(route, config, params)
                    if entry:
                        entries.append(entry)
        
        self._entries = entries
        return entries
    
    def _get_route_config(self, route: Any) -> Optional[SitemapConfig]:
        """Get sitemap config from a route's handler."""
        handler = getattr(route, "handler", None)
        if handler:
            # Check handler directly
            config = get_sitemap_config(handler)
            if config:
                return config
            
            # Check wrapped function
            if hasattr(handler, "fn"):
                config = get_sitemap_config(handler.fn)
                if config:
                    return config
        
        return None
    
    def _route_has_params(self, route: Any) -> bool:
        """Check if route has dynamic parameters."""
        pattern = getattr(route, "pattern", None)
        if pattern:
            # Check for [param] or [...slug] patterns
            pattern_str = getattr(pattern, "pattern", "")
            return "[" in pattern_str
        return False
    
    def _get_dynamic_params(self, route: Any) -> List[Dict[str, Any]]:
        """
        Get parameter combinations for dynamic route.
        
        Looks for get_sitemap_params() in the route's module.
        """
        module_path = getattr(route, "module_path", None)
        if not module_path:
            return []
        
        try:
            # Load module and look for get_sitemap_params
            import importlib.util
            spec = importlib.util.spec_from_file_location("_sitemap_module", module_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if hasattr(module, "get_sitemap_params"):
                    params_func = module.get_sitemap_params
                    result = params_func()
                    
                    # Support async functions
                    if asyncio.iscoroutine(result):
                        result = asyncio.get_event_loop().run_until_complete(result)
                    
                    return result if result else []
        except Exception as e:
            print(f"[PyNext] Warning: Failed to get sitemap params for {module_path}: {e}")
        
        return []
    
    def _create_entry(
        self,
        route: Any,
        config: SitemapConfig,
        params: Dict[str, Any],
    ) -> Optional[SitemapEntry]:
        """Create a SitemapEntry from route, config, and params."""
        # Build URL from route pattern and params
        pattern = getattr(route, "pattern", None)
        if not pattern:
            return None
        
        pattern_str = getattr(pattern, "pattern", "")
        url_path = pattern_str
        
        # Replace parameters in pattern
        for key, value in params.items():
            # Handle [param] style
            url_path = url_path.replace(f"[{key}]", str(value))
            # Handle [...param] style (catch-all)
            url_path = url_path.replace(f"[...{key}]", str(value))
        
        # Skip if still has unreplaced params
        if "[" in url_path:
            return None
        
        # Build full URL
        full_url = f"{self.base_url}{url_path}"
        
        # Get lastmod
        lastmod = None
        if config.lastmod == "auto":
            module_path = getattr(route, "module_path", None)
            if module_path and Path(module_path).exists():
                mtime = Path(module_path).stat().st_mtime
                lastmod = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
        elif config.lastmod and config.lastmod != "auto":
            lastmod = config.lastmod
        
        # Check for lastmod in params (for dynamic routes)
        if "lastmod" in params:
            lastmod = params["lastmod"]
            if isinstance(lastmod, datetime):
                lastmod = lastmod.strftime("%Y-%m-%d")
        
        return SitemapEntry(
            loc=full_url,
            lastmod=lastmod,
            changefreq=config.changefreq,
            priority=config.priority,
        )
    
    def generate(self) -> str:
        """
        Generate sitemap XML.
        
        Discovers URLs if not already done, then generates
        the complete sitemap XML string.
        
        Returns:
            Complete sitemap XML string
        """
        if not self._entries:
            self.discover_urls()
        
        return self.generate_xml(self._entries)
    
    def generate_xml(self, entries: Optional[List[SitemapEntry]] = None) -> str:
        """
        Generate sitemap XML from entries.
        
        Args:
            entries: List of SitemapEntry (uses discovered if None)
        
        Returns:
            Complete sitemap XML string
        """
        if entries is None:
            entries = self._entries
        
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        ]
        
        for entry in entries:
            lines.append(entry.to_xml())
        
        lines.append("</urlset>")
        
        return "\n".join(lines)
    
    def generate_index(
        self,
        entries: Optional[List[SitemapEntry]] = None,
    ) -> Tuple[str, List[Tuple[str, str]]]:
        """
        Generate sitemap index with multiple sitemaps.
        
        Automatically splits into multiple sitemaps if > 50k URLs.
        
        Args:
            entries: List of SitemapEntry (uses discovered if None)
        
        Returns:
            Tuple of (index_xml, [(filename, sitemap_xml), ...])
        """
        if entries is None:
            entries = self._entries if self._entries else self.discover_urls()
        
        # If under limit, return single sitemap
        if len(entries) <= self.MAX_URLS_PER_SITEMAP:
            return "", [("sitemap.xml", self.generate_xml(entries))]
        
        # Split into chunks
        sitemaps: List[Tuple[str, str]] = []
        chunks = [
            entries[i:i + self.MAX_URLS_PER_SITEMAP]
            for i in range(0, len(entries), self.MAX_URLS_PER_SITEMAP)
        ]
        
        for i, chunk in enumerate(chunks, 1):
            filename = f"sitemap-{i}.xml"
            xml = self.generate_xml(chunk)
            sitemaps.append((filename, xml))
        
        # Generate index
        index_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        ]
        
        for filename, _ in sitemaps:
            index_lines.append("  <sitemap>")
            index_lines.append(f"    <loc>{self.base_url}/{filename}</loc>")
            index_lines.append(f"    <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>")
            index_lines.append("  </sitemap>")
        
        index_lines.append("</sitemapindex>")
        index_xml = "\n".join(index_lines)
        
        return index_xml, sitemaps
    
    def needs_index(self, entries: Optional[List[SitemapEntry]] = None) -> bool:
        """
        Check if sitemap index is needed.
        
        Args:
            entries: List of entries to check
        
        Returns:
            True if more than 50k URLs
        """
        if entries is None:
            entries = self._entries if self._entries else self.discover_urls()
        
        return len(entries) > self.MAX_URLS_PER_SITEMAP
    
    def write_to_directory(
        self,
        output_dir: Path,
        entries: Optional[List[SitemapEntry]] = None,
    ) -> List[Path]:
        """
        Write sitemap(s) to directory.
        
        Handles both single sitemap and sitemap index cases.
        
        Args:
            output_dir: Directory to write files
            entries: Entries to use (discovers if None)
        
        Returns:
            List of written file paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        written_files: List[Path] = []
        
        if entries is None:
            entries = self._entries if self._entries else self.discover_urls()
        
        if self.needs_index(entries):
            # Write sitemap index
            index_xml, sitemaps = self.generate_index(entries)
            
            index_path = output_dir / "sitemap.xml"
            index_path.write_text(index_xml, encoding="utf-8")
            written_files.append(index_path)
            
            for filename, xml in sitemaps:
                sitemap_path = output_dir / filename
                sitemap_path.write_text(xml, encoding="utf-8")
                written_files.append(sitemap_path)
        else:
            # Write single sitemap
            sitemap_path = output_dir / "sitemap.xml"
            sitemap_path.write_text(self.generate_xml(entries), encoding="utf-8")
            written_files.append(sitemap_path)
        
        return written_files
    
    @property
    def url_count(self) -> int:
        """Get number of discovered URLs."""
        return len(self._entries)


# ============================================
# Convenience Functions
# ============================================

def add_static_urls(generator: SitemapGenerator, urls: List[str]) -> None:
    """
    Add static URLs to generator.
    
    Useful for pages not in the router (e.g., external pages).
    
    Args:
        generator: SitemapGenerator instance
        urls: List of full URLs to add
    
    Example:
        generator = SitemapGenerator(router, base_url)
        add_static_urls(generator, [
            "https://example.com/about",
            "https://example.com/contact",
        ])
    """
    for url in urls:
        entry = SitemapEntry(loc=url)
        generator._entries.append(entry)


def merge_sitemaps(sitemaps: List[str]) -> str:
    """
    Merge multiple sitemap XML strings.
    
    Useful for combining auto-generated and manual sitemaps.
    
    Args:
        sitemaps: List of sitemap XML strings
    
    Returns:
        Merged sitemap XML
    """
    entries = []
    
    for sitemap_xml in sitemaps:
        # Extract <url> elements
        import re
        url_pattern = r"<url>.*?</url>"
        matches = re.findall(url_pattern, sitemap_xml, re.DOTALL)
        entries.extend(matches)
    
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    lines.extend(entries)
    lines.append("</urlset>")
    
    return "\n".join(lines)

