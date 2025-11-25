"""
PyNext Static Site Generator - Build-Time HTML Generation.

Generates static HTML files during build with:
- Incremental builds (only rebuild changed pages)
- Zero JS output for fully static pages
- Islands-only JS for interactive pages
- Layout chain pre-computation
- Asset manifest with content hashes

SolidJS Principles Applied:
- Compile-time optimization
- Minimal runtime overhead
- Fine-grained updates (islands only)
"""

import asyncio
import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import importlib.util

from pynext.core.static import (
    StaticPageMeta,
    StaticPageConfig,
    StaticBuildResult,
    StaticPath,
    GenerationMode,
    get_static_pages,
    get_build_paths,
    get_page_props,
    compute_page_hash,
    get_static_analyzer,
)
from pynext.core.island import collect_islands, generate_island_script
from pynext.router.trie import LayoutCache


@dataclass
class BuildManifest:
    """Manifest of built static pages."""
    pages: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    assets: Dict[str, str] = field(default_factory=dict)  # path -> hash
    build_time: float = 0
    version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "buildTime": self.build_time,
            "pages": self.pages,
            "assets": self.assets,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BuildManifest":
        return cls(
            version=data.get("version", "1.0"),
            build_time=data.get("buildTime", 0),
            pages=data.get("pages", {}),
            assets=data.get("assets", {}),
        )


@dataclass
class BuildResult:
    """Result of the full build process."""
    success: bool
    total_pages: int
    static_pages: int
    hybrid_pages: int
    failed_pages: int
    zero_js_pages: int
    total_time_ms: float
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class StaticGenerator:
    """
    Generates static HTML files during build.
    
    Features:
    - Incremental builds based on content hash
    - Parallel page generation
    - Zero JS detection and output
    - Layout chain caching
    - Island-only JS bundles
    """
    
    def __init__(
        self,
        pages_dir: Path,
        output_dir: Path,
        static_dir: Path,
        max_workers: int = 4
    ):
        self.pages_dir = Path(pages_dir)
        self.output_dir = Path(output_dir)
        self.static_dir = Path(static_dir)
        self.max_workers = max_workers
        
        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "_next" / "static").mkdir(parents=True, exist_ok=True)
        
        # Manifest
        self.manifest_path = self.output_dir / "_next" / "build-manifest.json"
        self._manifest = self._load_manifest()
        
        # Layout cache
        self._layout_cache = LayoutCache()
        
        # Build state
        self._built_pages: Dict[str, StaticBuildResult] = {}
        self._errors: List[Dict[str, Any]] = []
    
    def _load_manifest(self) -> BuildManifest:
        """Load existing manifest for incremental builds."""
        if self.manifest_path.exists():
            try:
                data = json.loads(self.manifest_path.read_text())
                return BuildManifest.from_dict(data)
            except (json.JSONDecodeError, KeyError):
                pass
        return BuildManifest()
    
    async def build_all(self) -> BuildResult:
        """
        Build all static pages.
        
        Returns build result with statistics.
        """
        start_time = time.time()
        
        # Get all registered static pages
        static_pages = get_static_pages()
        
        if not static_pages:
            return BuildResult(
                success=True,
                total_pages=0,
                static_pages=0,
                hybrid_pages=0,
                failed_pages=0,
                zero_js_pages=0,
                total_time_ms=0,
            )
        
        # Collect all paths to build
        all_paths: List[Tuple[str, StaticPageMeta, StaticPath]] = []
        
        for route, meta in static_pages.items():
            try:
                paths = await get_build_paths(route)
                for path in paths:
                    all_paths.append((route, meta, path))
            except Exception as e:
                self._errors.append({
                    "route": route,
                    "error": f"Failed to get paths: {e}",
                })
        
        # Build pages in parallel
        results = await self._build_pages_parallel(all_paths)
        
        # Update manifest
        self._manifest.build_time = time.time()
        for result in results:
            if result:
                self._manifest.pages[result.path] = {
                    "hash": result.hash,
                    "hasJs": result.needs_js(),
                    "islandCount": result.island_count,
                    "generatedAt": result.generated_at,
                }
        
        # Save manifest
        self._save_manifest()
        
        # Compute statistics
        successful = [r for r in results if r is not None]
        zero_js = [r for r in successful if not r.needs_js()]
        hybrid = [r for r in successful if r.needs_js()]
        
        total_time = (time.time() - start_time) * 1000
        
        return BuildResult(
            success=len(self._errors) == 0,
            total_pages=len(all_paths),
            static_pages=len(zero_js),
            hybrid_pages=len(hybrid),
            failed_pages=len(self._errors),
            zero_js_pages=len(zero_js),
            total_time_ms=total_time,
            errors=self._errors,
        )
    
    async def _build_pages_parallel(
        self,
        paths: List[Tuple[str, StaticPageMeta, StaticPath]]
    ) -> List[Optional[StaticBuildResult]]:
        """Build multiple pages in parallel."""
        loop = asyncio.get_event_loop()
        
        # Use thread pool for parallel builds
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [
                loop.run_in_executor(
                    executor,
                    self._build_page_sync,
                    route, meta, path
                )
                for route, meta, path in paths
            ]
            results = await asyncio.gather(*futures, return_exceptions=True)
        
        # Handle exceptions
        processed = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                route, _, path = paths[i]
                self._errors.append({
                    "route": route,
                    "path": path.get_path(route),
                    "error": str(result),
                })
                processed.append(None)
            else:
                processed.append(result)
        
        return processed
    
    def _build_page_sync(
        self,
        route: str,
        meta: StaticPageMeta,
        path: StaticPath
    ) -> StaticBuildResult:
        """Build a single page (synchronous for thread pool)."""
        # Run async code in new event loop
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(
                self._build_page(route, meta, path)
            )
        finally:
            loop.close()
    
    async def _build_page(
        self,
        route: str,
        meta: StaticPageMeta,
        path: StaticPath
    ) -> StaticBuildResult:
        """Build a single static page."""
        url_path = path.get_path(route)
        
        # Get props
        props = await get_page_props(route, path.params)
        
        # Render page
        page_func = meta.page_func
        if asyncio.iscoroutinefunction(page_func):
            html_content = await page_func(**props)
        else:
            html_content = page_func(**props)
        
        # Convert to string if needed
        if hasattr(html_content, "render"):
            html_content = html_content.render()
        elif not isinstance(html_content, str):
            html_content = str(html_content)
        
        # Analyze for islands
        analyzer = get_static_analyzer()
        islands = collect_islands(html_content) if hasattr(html_content, "__iter__") else []
        is_static = len(islands) == 0
        
        # Generate JS bundle if needed
        js_bundle = None
        if not is_static:
            js_bundle = self._generate_page_js(islands)
        
        # Compute hash for caching
        content_hash = compute_page_hash(html_content, props)
        
        # Check if rebuild needed (incremental build)
        existing = self._manifest.pages.get(url_path)
        if existing and existing.get("hash") == content_hash:
            # No changes, skip rebuild
            return StaticBuildResult(
                path=url_path,
                html=html_content,
                js_bundle=js_bundle,
                hash=content_hash,
                has_islands=not is_static,
                island_count=len(islands),
                generated_at=existing.get("generatedAt", time.time()),
            )
        
        # Wrap in document shell
        full_html = self._generate_document(
            html_content,
            js_bundle,
            meta.config,
            props.get("metadata", {})
        )
        
        # Write HTML file
        output_path = self._get_output_path(url_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(full_html)
        
        # Write JS bundle if needed
        if js_bundle:
            js_path = self.output_dir / "_next" / "static" / f"{content_hash}.js"
            js_path.write_text(js_bundle)
        
        return StaticBuildResult(
            path=url_path,
            html=full_html,
            js_bundle=js_bundle,
            hash=content_hash,
            has_islands=not is_static,
            island_count=len(islands),
            generated_at=time.time(),
        )
    
    def _generate_document(
        self,
        content: str,
        js_bundle: Optional[str],
        config: StaticPageConfig,
        metadata: Dict[str, Any]
    ) -> str:
        """Generate full HTML document."""
        title = metadata.get("title", "PyNext App")
        description = metadata.get("description", "")
        
        # Generate meta tags
        meta_tags = [
            '<meta charset="UTF-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        ]
        if description:
            meta_tags.append(f'<meta name="description" content="{description}">')
        
        # Only include JS if needed
        scripts = ""
        if js_bundle and not config.ship_zero_js:
            scripts = f'<script type="module">{js_bundle}</script>'
        elif js_bundle:
            # Defer loading for islands
            scripts = f'''
<script type="module">
    // Lazy load island hydration
    if ('requestIdleCallback' in window) {{
        requestIdleCallback(() => {{
            {js_bundle}
        }});
    }} else {{
        setTimeout(() => {{
            {js_bundle}
        }}, 1);
    }}
</script>
'''
        
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    {chr(10).join(meta_tags)}
    <title>{title}</title>
</head>
<body>
    {content}
    {scripts}
</body>
</html>'''
    
    def _generate_page_js(self, islands: List[Any]) -> str:
        """Generate minimal JavaScript for page islands."""
        if not islands:
            return ""
        
        island_scripts = []
        for island in islands:
            script = generate_island_script(island)
            if script:
                island_scripts.append(script)
        
        if not island_scripts:
            return ""
        
        return "\n".join(island_scripts)
    
    def _get_output_path(self, url_path: str) -> Path:
        """Get file system path for a URL path."""
        # Handle root
        if url_path == "/":
            return self.output_dir / "index.html"
        
        # Remove leading slash
        path = url_path.lstrip("/")
        
        # Add index.html for directories
        if not path.endswith(".html"):
            path = f"{path}/index.html"
        
        return self.output_dir / path
    
    def _save_manifest(self) -> None:
        """Save build manifest."""
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self.manifest_path.write_text(
            json.dumps(self._manifest.to_dict(), indent=2)
        )
    
    def get_page_cache_headers(self, path: str) -> Dict[str, str]:
        """Get cache headers for a static page."""
        page_info = self._manifest.pages.get(path, {})
        
        if page_info:
            return {
                "Cache-Control": "public, max-age=31536000, immutable",
                "ETag": f'"{page_info.get("hash", "")}"',
            }
        
        return {
            "Cache-Control": "public, max-age=3600",
        }


async def build_static_site(
    pages_dir: Path,
    output_dir: Path,
    static_dir: Path,
    config: Optional[Dict[str, Any]] = None
) -> BuildResult:
    """
    Main entry point for static site generation.
    
    Called by `pynext build` command.
    """
    generator = StaticGenerator(pages_dir, output_dir, static_dir)
    return await generator.build_all()


def get_build_manifest(output_dir: Path) -> Optional[BuildManifest]:
    """Load build manifest from output directory."""
    manifest_path = output_dir / "_next" / "build-manifest.json"
    if manifest_path.exists():
        try:
            data = json.loads(manifest_path.read_text())
            return BuildManifest.from_dict(data)
        except (json.JSONDecodeError, KeyError):
            pass
    return None

