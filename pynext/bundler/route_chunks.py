"""
Route-based Code Splitting for PyNext.

Generates optimized JavaScript bundles per route:
- Analyze route dependencies
- Generate minimal per-route bundles
- Shared chunk for common code
- Prefetch hints for navigation

Usage:
    from pynext.bundler.route_chunks import RouteChunkGenerator
    
    generator = RouteChunkGenerator(router, output_dir=".pynext/chunks")
    generator.analyze_all_routes()
    generator.generate_chunks()
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from pynext.router.file_router import FileRouter

from pynext.bundler.npm import NPMBundler


@dataclass
class ChunkDependency:
    """A JavaScript dependency for a chunk."""
    
    # Module path
    module: str
    
    # Specific exports used
    exports: Set[str] = field(default_factory=set)
    
    # Whether it's a npm package
    is_npm: bool = False
    
    # Size in bytes (estimated)
    size: int = 0


@dataclass
class RouteChunkInfo:
    """Information about a route's JavaScript chunk."""
    
    # Route pattern
    route: str
    
    # Chunk file name (without extension)
    chunk_name: str
    
    # Full path to chunk file
    chunk_path: Optional[Path] = None
    
    # Dependencies (modules needed)
    dependencies: Dict[str, ChunkDependency] = field(default_factory=dict)
    
    # Islands in this route
    islands: List[str] = field(default_factory=list)
    
    # Lazy components in this route  
    lazy_components: List[str] = field(default_factory=list)
    
    # Other routes to prefetch
    prefetch_routes: List[str] = field(default_factory=list)
    
    # File size (after generation)
    size: int = 0
    
    # Content hash for cache busting
    hash: Optional[str] = None
    
    # Whether this route needs signals runtime
    needs_signals: bool = False
    
    # Whether this route needs resource runtime
    needs_resource: bool = False
    
    # Whether this route needs suspense runtime
    needs_suspense: bool = False


class RouteChunkGenerator:
    """
    Generates JavaScript chunks for each route.
    
    Analyzes component trees to determine minimal JavaScript needed,
    then generates optimized bundles using esbuild.
    """
    
    def __init__(
        self,
        router: "FileRouter",
        output_dir: str | Path = ".pynext/chunks",
        project_dir: str | Path = ".",
    ):
        self.router = router
        self.output_dir = Path(output_dir).resolve()
        self.project_dir = Path(project_dir).resolve()
        
        # Route info cache
        self.routes: Dict[str, RouteChunkInfo] = {}
        
        # Shared chunk info
        self.shared_chunk: Optional[RouteChunkInfo] = None
        
        # Runtime modules included in shared
        self.runtime_modules: Set[str] = set()
    
    def analyze_all_routes(self) -> Dict[str, RouteChunkInfo]:
        """
        Analyze all routes to determine dependencies.
        
        Returns dict of route -> RouteChunkInfo.
        """
        for route in self.router.get_all_routes():
            chunk_info = self.analyze_route(route.pattern)
            self.routes[route.pattern] = chunk_info
        
        # Determine shared dependencies
        self._compute_shared_chunk()
        
        return self.routes
    
    def analyze_route(self, route_pattern: str) -> RouteChunkInfo:
        """
        Analyze a single route's dependencies.
        """
        chunk_name = self._route_to_chunk_name(route_pattern)
        chunk_info = RouteChunkInfo(
            route=route_pattern,
            chunk_name=chunk_name,
        )
        
        # Get the route
        route_match = self.router.match(route_pattern)
        if not route_match:
            return chunk_info
        
        route = route_match[0]
        
        # Analyze page module for dependencies
        if route.module:
            self._analyze_module(route.module, chunk_info)
        
        # Check layouts for dependencies
        if hasattr(route, 'layouts') and route.layouts:
            for layout in route.layouts:
                if hasattr(layout, '__module__'):
                    self._analyze_module(layout.__module__, chunk_info)
        
        return chunk_info
    
    def _analyze_module(self, module_name: str, chunk_info: RouteChunkInfo) -> None:
        """Analyze a module for JavaScript dependencies."""
        import importlib
        import inspect
        
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            return
        
        source_code = ""
        try:
            source_code = inspect.getsource(module)
        except (OSError, TypeError):
            pass
        
        # Check for signal usage
        if "Signal(" in source_code or "Signal[" in source_code:
            chunk_info.needs_signals = True
        
        # Check for resource usage
        if "Resource(" in source_code:
            chunk_info.needs_resource = True
        
        # Check for suspense usage
        if "Suspense(" in source_code or "Suspense[" in source_code:
            chunk_info.needs_suspense = True
        
        # Check for island usage
        if "@island" in source_code:
            chunk_info.islands.append(module_name)
        
        # Check for lazy imports
        if "lazy(" in source_code or "@lazy_route" in source_code:
            chunk_info.lazy_components.append(module_name)
        
        # Check for npm imports
        if "npm_import(" in source_code or "NPMPackage(" in source_code:
            # Parse npm package names
            import re
            npm_matches = re.findall(r'(?:npm_import|NPMPackage)\s*\(\s*["\']([^"\']+)["\']', source_code)
            for pkg in npm_matches:
                chunk_info.dependencies[pkg] = ChunkDependency(
                    module=pkg,
                    is_npm=True,
                )
    
    def _compute_shared_chunk(self) -> None:
        """
        Compute shared chunk for common dependencies.
        
        Modules used by more than one route go into shared chunk.
        """
        module_usage: Dict[str, int] = {}
        
        for chunk_info in self.routes.values():
            for dep in chunk_info.dependencies:
                module_usage[dep] = module_usage.get(dep, 0) + 1
            
            # Count runtime needs
            if chunk_info.needs_signals:
                module_usage["__signals__"] = module_usage.get("__signals__", 0) + 1
            if chunk_info.needs_resource:
                module_usage["__resource__"] = module_usage.get("__resource__", 0) + 1
            if chunk_info.needs_suspense:
                module_usage["__suspense__"] = module_usage.get("__suspense__", 0) + 1
        
        # Shared modules are used by 2+ routes
        shared_modules = {mod for mod, count in module_usage.items() if count >= 2}
        
        if shared_modules:
            self.shared_chunk = RouteChunkInfo(
                route="__shared__",
                chunk_name="shared",
            )
            for mod in shared_modules:
                if mod.startswith("__"):
                    self.runtime_modules.add(mod)
                else:
                    self.shared_chunk.dependencies[mod] = ChunkDependency(
                        module=mod,
                        is_npm=True,
                    )
    
    def generate_chunks(self) -> Dict[str, Path]:
        """
        Generate JavaScript chunk files for all routes.
        
        Returns dict of route -> chunk path.
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        result = {}
        
        # Generate shared chunk first
        if self.shared_chunk:
            shared_path = self._generate_chunk(self.shared_chunk)
            if shared_path:
                result["__shared__"] = shared_path
        
        # Generate route chunks
        for route, chunk_info in self.routes.items():
            chunk_path = self._generate_chunk(chunk_info)
            if chunk_path:
                result[route] = chunk_path
        
        return result
    
    def _generate_chunk(self, chunk_info: RouteChunkInfo) -> Optional[Path]:
        """Generate a single chunk file using esbuild for real bundling."""
        chunk_path = self.output_dir / f"{chunk_info.chunk_name}.js"
        
        # Build entry file content
        entry_parts = []
        
        # Add runtime imports
        if chunk_info.needs_signals or "__signals__" in self.runtime_modules:
            entry_parts.append('import "/__pynext__/runtime.js";')
        
        if chunk_info.needs_resource:
            entry_parts.append('import "/__pynext__/runtime/resource.js";')
        
        if chunk_info.needs_suspense:
            entry_parts.append('import "/__pynext__/runtime/suspense.js";')
        
        # Add npm dependencies with tree-shaking hints
        npm_exports = []
        for dep_name, dep in chunk_info.dependencies.items():
            if dep.is_npm:
                safe_name = dep_name.replace("/", "_").replace("@", "").replace("-", "_")
                # If we know specific exports, import only those (tree-shaking)
                if dep.exports:
                    exports_str = ", ".join(dep.exports)
                    entry_parts.append(f'import {{ {exports_str} }} from "{dep_name}";')
                    npm_exports.extend(dep.exports)
                else:
                    # Import all and let esbuild tree-shake
                    entry_parts.append(f'import * as {safe_name} from "{dep_name}";')
                    npm_exports.append(safe_name)
        
        # Add island hydration
        if chunk_info.islands:
            entry_parts.append('''
// Island hydration
if (typeof window !== 'undefined' && window.__pynext__) {
    window.__pynext__.hydrateAllIslands?.();
}
''')
        
        # Add lazy loading initialization
        if chunk_info.lazy_components:
            entry_parts.append('''
// Lazy loading initialization
if (typeof window !== 'undefined' && window.__pynext__) {
    window.__pynext__.initLazyLoading?.();
}
''')
        
        # Add route-specific initialization
        entry_parts.append(f'''
// Route: {chunk_info.route}
if (typeof window !== 'undefined') {{
    console.log('[PyNext] Loaded chunk: {chunk_info.chunk_name}');
}}
''')
        
        entry_content = "\n".join(entry_parts)
        
        # Try to use esbuild for real bundling if npm deps exist
        if chunk_info.dependencies and self._esbuild_available():
            bundled_content = self._bundle_with_esbuild(
                entry_content, 
                chunk_info,
                chunk_path
            )
            if bundled_content:
                chunk_path.write_text(bundled_content)
                chunk_info.hash = hashlib.md5(bundled_content.encode()).hexdigest()[:8]
                chunk_info.size = len(bundled_content.encode())
                chunk_info.chunk_path = chunk_path
                return chunk_path
        
        # Fallback: write entry content directly (no npm bundling)
        chunk_path.write_text(entry_content)
        chunk_info.hash = hashlib.md5(entry_content.encode()).hexdigest()[:8]
        chunk_info.size = len(entry_content.encode())
        chunk_info.chunk_path = chunk_path
        
        return chunk_path
    
    def _esbuild_available(self) -> bool:
        """Check if esbuild is available."""
        return shutil.which("esbuild") is not None or shutil.which("npx") is not None
    
    def _bundle_with_esbuild(
        self, 
        entry_content: str, 
        chunk_info: RouteChunkInfo,
        output_path: Path
    ) -> Optional[str]:
        """
        Bundle the entry content using esbuild.
        
        This enables:
        - Tree-shaking of unused npm exports
        - Minification
        - Code splitting for shared dependencies
        """
        try:
            # Create temporary entry file
            with tempfile.NamedTemporaryFile(
                mode='w', 
                suffix='.js', 
                dir=self.project_dir,
                delete=False
            ) as f:
                f.write(entry_content)
                entry_file = Path(f.name)
            
            # Build esbuild command
            cmd = [
                "esbuild",
                str(entry_file),
                f"--outfile={output_path}",
                "--bundle",
                "--format=esm",
                "--target=es2020",
                "--minify",
                "--tree-shaking=true",  # Explicit tree-shaking
            ]
            
            # Add external for runtime (served separately)
            cmd.extend([
                "--external:/__pynext__/*",
            ])
            
            # Try esbuild directly
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_dir)
            )
            
            if result.returncode != 0:
                # Try with npx
                cmd_npx = ["npx"] + cmd
                result = subprocess.run(
                    cmd_npx,
                    capture_output=True,
                    text=True,
                    cwd=str(self.project_dir)
                )
            
            # Clean up temp file
            entry_file.unlink()
            
            if result.returncode == 0 and output_path.exists():
                return output_path.read_text()
            
            return None
            
        except Exception as e:
            print(f"[PyNext] esbuild bundling failed: {e}")
            return None
    
    def _route_to_chunk_name(self, route: str) -> str:
        """Convert a route pattern to a chunk file name."""
        # / -> index
        # /dashboard -> dashboard
        # /users/[id] -> users-id
        # /users/[...slug] -> users-slug
        
        name = route.strip('/')
        if not name:
            return "index"
        
        # Remove dynamic markers
        name = name.replace('[...', '').replace('[', '').replace(']', '')
        name = name.replace('/', '-')
        
        return name
    
    def get_chunk_url(self, route: str) -> Optional[str]:
        """Get the URL for a route's chunk."""
        chunk_info = self.routes.get(route)
        if not chunk_info:
            return None
        
        hash_suffix = f"?v={chunk_info.hash}" if chunk_info.hash else ""
        return f"/__pynext__/chunks/{chunk_info.chunk_name}.js{hash_suffix}"
    
    def get_preload_tags(self, route: str) -> List[str]:
        """Get preload link tags for a route and its prefetch routes."""
        tags = []
        
        chunk_info = self.routes.get(route)
        if not chunk_info:
            return tags
        
        # Main chunk
        if chunk_info.chunk_path:
            tags.append(f'<link rel="modulepreload" href="{self.get_chunk_url(route)}">')
        
        # Shared chunk
        if self.shared_chunk and self.shared_chunk.chunk_path:
            tags.append(f'<link rel="modulepreload" href="/__pynext__/chunks/shared.js">')
        
        # Prefetch routes
        for prefetch_route in chunk_info.prefetch_routes:
            prefetch_url = self.get_chunk_url(prefetch_route)
            if prefetch_url:
                tags.append(f'<link rel="prefetch" href="{prefetch_url}">')
        
        return tags
    
    def get_script_tags(self, route: str) -> List[str]:
        """Get script tags for a route."""
        tags = []
        
        # Shared chunk first
        if self.shared_chunk and self.shared_chunk.chunk_path:
            tags.append('<script type="module" src="/__pynext__/chunks/shared.js"></script>')
        
        # Route chunk
        chunk_url = self.get_chunk_url(route)
        if chunk_url:
            tags.append(f'<script type="module" src="{chunk_url}"></script>')
        
        return tags
    
    def get_manifest(self) -> Dict[str, Any]:
        """Get a manifest of all chunks for client-side routing."""
        manifest = {
            "chunks": {},
            "shared": None,
            "runtimeModules": list(self.runtime_modules),
        }
        
        for route, chunk_info in self.routes.items():
            manifest["chunks"][route] = {
                "name": chunk_info.chunk_name,
                "url": self.get_chunk_url(route),
                "size": chunk_info.size,
                "hash": chunk_info.hash,
                "prefetch": chunk_info.prefetch_routes,
                "needsSignals": chunk_info.needs_signals,
                "needsResource": chunk_info.needs_resource,
                "needsSuspense": chunk_info.needs_suspense,
            }
        
        if self.shared_chunk:
            manifest["shared"] = {
                "name": "shared",
                "url": "/__pynext__/chunks/shared.js",
                "size": self.shared_chunk.size,
                "hash": self.shared_chunk.hash,
            }
        
        return manifest
    
    def write_manifest(self) -> Path:
        """Write chunk manifest to file."""
        manifest_path = self.output_dir / "manifest.json"
        manifest_path.write_text(json.dumps(self.get_manifest(), indent=2))
        return manifest_path
    
    def get_total_size(self) -> int:
        """Get total size of all chunks."""
        total = sum(c.size for c in self.routes.values())
        if self.shared_chunk:
            total += self.shared_chunk.size
        return total
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about generated chunks."""
        return {
            "totalRoutes": len(self.routes),
            "totalChunks": len(self.routes) + (1 if self.shared_chunk else 0),
            "totalSize": self.get_total_size(),
            "sharedSize": self.shared_chunk.size if self.shared_chunk else 0,
            "avgRouteSize": self.get_total_size() // max(len(self.routes), 1),
            "routesWithSignals": sum(1 for c in self.routes.values() if c.needs_signals),
            "routesWithResource": sum(1 for c in self.routes.values() if c.needs_resource),
            "routesWithSuspense": sum(1 for c in self.routes.values() if c.needs_suspense),
            "routesWithIslands": sum(1 for c in self.routes.values() if c.islands),
            "routesWithLazy": sum(1 for c in self.routes.values() if c.lazy_components),
        }


def create_route_chunks(router: "FileRouter", output_dir: str = ".pynext/chunks") -> Dict[str, Path]:
    """
    Convenience function to generate all route chunks.
    
    Args:
        router: The file router with scanned routes
        output_dir: Directory to write chunks to
    
    Returns:
        Dict mapping routes to chunk paths
    """
    generator = RouteChunkGenerator(router, output_dir)
    generator.analyze_all_routes()
    return generator.generate_chunks()

