"""
Build-Time PPR Analyzer for PyNext.

Analyzes pages at build time to identify:
- Static shells (pre-renderable content)
- Dynamic holes (must render at request time)
- Optimal splitting points

This enables:
- Pre-rendering static content at build
- Minimal streaming payload at runtime
- Zero JS for fully static parts
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, List, Set, Any, Callable
import hashlib
import json
import ast
import inspect
from concurrent.futures import ThreadPoolExecutor, as_completed

from pynext.core.ppr import (
    PPRAnalysis,
    ComponentType,
    PPRAnalyzer,
    get_ppr_analyzer,
)


@dataclass
class PagePPRInfo:
    """PPR information for a page."""
    path: str
    page_hash: str
    is_fully_static: bool
    has_dynamic_parts: bool
    static_shell_html: Optional[str]
    dynamic_boundary_ids: List[str]
    estimated_static_size: int
    estimated_dynamic_size: int
    components: List[PPRAnalysis]


@dataclass
class PPRBuildConfig:
    """Configuration for PPR build."""
    output_dir: Path = Path(".pynext/ppr-cache")
    analyze_depth: int = 10  # Max depth to analyze component tree
    cache_static_shells: bool = True
    generate_manifest: bool = True


class PPRBuildAnalyzer:
    """
    Build-time analyzer for PPR.
    
    Scans pages and components to:
    1. Identify static vs dynamic parts
    2. Pre-render static shells
    3. Generate boundary mappings
    4. Create optimal streaming points
    """
    
    def __init__(self, config: Optional[PPRBuildConfig] = None):
        self.config = config or PPRBuildConfig()
        self._analyzer = get_ppr_analyzer()
        self._page_cache: Dict[str, PagePPRInfo] = {}
    
    def analyze_pages(
        self,
        pages_dir: Path,
        project_root: Optional[Path] = None,
    ) -> Dict[str, PagePPRInfo]:
        """
        Analyze all pages in a directory for PPR.
        
        Returns mapping of page paths to PPR info.
        """
        project_root = project_root or Path.cwd()
        cache_dir = project_root / self.config.output_dir
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        results: Dict[str, PagePPRInfo] = {}
        
        if not pages_dir.exists():
            return results
        
        # Find all page files
        page_files = list(pages_dir.rglob("*.py"))
        page_files = [
            f for f in page_files
            if "__pycache__" not in str(f)
            and not f.name.startswith("_")
            and f.name not in ("layout.py", "loading.py", "error.py", "not-found.py")
        ]
        
        # Analyze pages in parallel
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(
                    self._analyze_page,
                    page_file,
                    pages_dir,
                    cache_dir,
                ): page_file
                for page_file in page_files
            }
            
            for future in as_completed(futures):
                page_file = futures[future]
                try:
                    info = future.result()
                    if info:
                        results[info.path] = info
                except Exception as e:
                    print(f"Error analyzing {page_file}: {e}")
        
        # Generate manifest
        if self.config.generate_manifest:
            self._generate_manifest(results, cache_dir)
        
        return results
    
    def _analyze_page(
        self,
        page_file: Path,
        pages_dir: Path,
        cache_dir: Path,
    ) -> Optional[PagePPRInfo]:
        """Analyze a single page file."""
        # Calculate page path
        rel_path = page_file.relative_to(pages_dir)
        page_path = "/" + str(rel_path.with_suffix("")).replace("\\", "/")
        if page_path.endswith("/index"):
            page_path = page_path[:-5] or "/"
        
        # Read and hash source
        source = page_file.read_text()
        page_hash = hashlib.md5(source.encode()).hexdigest()[:12]
        
        # Check cache
        cache_file = cache_dir / f"{page_hash}.json"
        if cache_file.exists():
            cached = self._load_cached_info(cache_file)
            if cached:
                return cached
        
        # Parse AST
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return None
        
        # Find page component
        page_fn = self._find_page_function(tree, source)
        if not page_fn:
            return None
        
        # Analyze component tree
        components = self._analyze_component_tree(tree, source)
        
        # Determine page characteristics
        is_fully_static = all(
            c.component_type == ComponentType.STATIC
            for c in components
        )
        
        has_dynamic_parts = any(
            c.component_type in (ComponentType.DYNAMIC, ComponentType.STREAMING)
            for c in components
        )
        
        # Estimate sizes
        static_components = [c for c in components if c.component_type == ComponentType.STATIC]
        dynamic_components = [c for c in components if c.component_type != ComponentType.STATIC]
        
        estimated_static_size = len(source) // 2  # Rough estimate
        estimated_dynamic_size = sum(c.estimated_render_time * 100 for c in dynamic_components)
        
        # Pre-render static shell if fully static
        static_shell_html = None
        if is_fully_static and self.config.cache_static_shells:
            static_shell_html = self._pre_render_shell(page_file)
        
        info = PagePPRInfo(
            path=page_path,
            page_hash=page_hash,
            is_fully_static=is_fully_static,
            has_dynamic_parts=has_dynamic_parts,
            static_shell_html=static_shell_html,
            dynamic_boundary_ids=[],  # Populated at runtime
            estimated_static_size=int(estimated_static_size),
            estimated_dynamic_size=int(estimated_dynamic_size),
            components=components,
        )
        
        # Cache result
        self._save_cached_info(cache_file, info)
        
        return info
    
    def _find_page_function(self, tree: ast.AST, source: str) -> Optional[ast.FunctionDef]:
        """Find the main page function in the AST."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if decorated with @page or has PPR decorator
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name) and decorator.id in ("page", "partial_prerender"):
                        return node
                    if isinstance(decorator, ast.Call):
                        if isinstance(decorator.func, ast.Name):
                            if decorator.func.id in ("page", "partial_prerender"):
                                return node
        
        # Fallback: look for 'default' function
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "default":
                return node
        
        return None
    
    def _analyze_component_tree(
        self,
        tree: ast.AST,
        source: str,
    ) -> List[PPRAnalysis]:
        """Analyze all components in the AST."""
        components = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                analysis = self._analyze_function(node, source)
                components.append(analysis)
        
        return components
    
    def _analyze_function(self, node: ast.FunctionDef, source: str) -> PPRAnalysis:
        """Analyze a function for PPR characteristics."""
        # Get function source
        func_source = ast.get_source_segment(source, node) or ""
        
        # Check for signals
        has_signals = any(
            pattern in func_source
            for pattern in ["Signal(", "signal(", "Effect(", "Store(", "Resource(", "create_resource("]
        )
        
        # Check for async
        has_async = isinstance(node, ast.AsyncFunctionDef) or "await " in func_source
        
        # Check for request data
        has_request_data = any(
            pattern in func_source
            for pattern in ["get_params(", "get_query(", "request.", "cookies."]
        )
        
        # Analyze parameters
        static_props = set()
        dynamic_props = set()
        
        for arg in node.args.args:
            if arg.arg == "self":
                continue
            if any(
                isinstance(default, (ast.Constant, ast.Num, ast.Str))
                for default in node.args.defaults
            ):
                static_props.add(arg.arg)
            else:
                dynamic_props.add(arg.arg)
        
        # Determine type
        if has_signals or has_async or has_request_data:
            component_type = ComponentType.DYNAMIC
        elif dynamic_props:
            component_type = ComponentType.STATIC_SHELL
        else:
            component_type = ComponentType.STATIC
        
        # Check decorators
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                if decorator.id == "static_part":
                    component_type = ComponentType.STATIC
                elif decorator.id == "dynamic_part":
                    component_type = ComponentType.DYNAMIC
            elif isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name):
                    if decorator.func.id == "static_part":
                        component_type = ComponentType.STATIC
                    elif decorator.func.id == "dynamic_part":
                        component_type = ComponentType.DYNAMIC
        
        return PPRAnalysis(
            component_type=component_type,
            has_signals=has_signals,
            has_async=has_async,
            has_request_data=has_request_data,
            static_props=static_props,
            dynamic_props=dynamic_props,
            estimated_render_time=0.1 + (len(func_source) * 0.001),
        )
    
    def _pre_render_shell(self, page_file: Path) -> Optional[str]:
        """Pre-render the static shell of a page."""
        # This would import and render the page in static mode
        # For now, return None (actual implementation needs runtime)
        return None
    
    def _load_cached_info(self, cache_file: Path) -> Optional[PagePPRInfo]:
        """Load cached PPR info."""
        try:
            with open(cache_file) as f:
                data = json.load(f)
            
            return PagePPRInfo(
                path=data["path"],
                page_hash=data["pageHash"],
                is_fully_static=data["isFullyStatic"],
                has_dynamic_parts=data["hasDynamicParts"],
                static_shell_html=data.get("staticShellHtml"),
                dynamic_boundary_ids=data.get("dynamicBoundaryIds", []),
                estimated_static_size=data["estimatedStaticSize"],
                estimated_dynamic_size=data["estimatedDynamicSize"],
                components=[],  # Don't cache component analysis
            )
        except Exception:
            return None
    
    def _save_cached_info(self, cache_file: Path, info: PagePPRInfo) -> None:
        """Save PPR info to cache."""
        try:
            data = {
                "path": info.path,
                "pageHash": info.page_hash,
                "isFullyStatic": info.is_fully_static,
                "hasDynamicParts": info.has_dynamic_parts,
                "staticShellHtml": info.static_shell_html,
                "dynamicBoundaryIds": info.dynamic_boundary_ids,
                "estimatedStaticSize": info.estimated_static_size,
                "estimatedDynamicSize": info.estimated_dynamic_size,
            }
            
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Failed to cache PPR info: {e}")
    
    def _generate_manifest(
        self,
        results: Dict[str, PagePPRInfo],
        cache_dir: Path,
    ) -> None:
        """Generate PPR manifest."""
        manifest = {
            "pages": {
                path: {
                    "hash": info.page_hash,
                    "isFullyStatic": info.is_fully_static,
                    "hasDynamicParts": info.has_dynamic_parts,
                    "staticSize": info.estimated_static_size,
                    "dynamicSize": info.estimated_dynamic_size,
                }
                for path, info in results.items()
            },
            "summary": {
                "totalPages": len(results),
                "fullyStatic": sum(1 for i in results.values() if i.is_fully_static),
                "hybrid": sum(1 for i in results.values() if i.has_dynamic_parts),
            }
        }
        
        manifest_file = cache_dir / "ppr-manifest.json"
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)


def analyze_ppr_for_build(
    pages_dir: Path,
    project_root: Optional[Path] = None,
    config: Optional[PPRBuildConfig] = None,
) -> Dict[str, PagePPRInfo]:
    """
    Analyze all pages for PPR during build.
    
    Called by CLI build command.
    """
    analyzer = PPRBuildAnalyzer(config)
    return analyzer.analyze_pages(pages_dir, project_root)

