"""
Build-Time Script Optimizer for PyNext.

Handles script optimization at build time:
- Dependency analysis and ordering
- Preload hint generation
- Script bundling (optional)
- SRI hash calculation
- Dead code elimination hints

Zero runtime overhead - all work done at build.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, List, Set, Any, Tuple
import hashlib
import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

from pynext.core.script import (
    ScriptConfig,
    ScriptRegistry,
    ScriptStrategy,
    ScriptType,
    get_script_registry,
)


@dataclass
class ScriptAnalysis:
    """Analysis result for a script."""
    src: str
    hash: str
    size: int
    dependencies: List[str]  # URLs this script imports
    exports: List[str]       # Exported symbols
    is_module: bool
    is_async_safe: bool      # Can be loaded async without issues
    sri_hash: Optional[str]  # Subresource integrity hash
    load_time_estimate: float  # Estimated load time in ms


@dataclass
class ScriptOptimizerConfig:
    """Configuration for script optimization."""
    output_dir: Path = Path("static/_scripts")
    cache_dir: Path = Path(".pynext/script-cache")
    calculate_sri: bool = True
    analyze_dependencies: bool = True
    bundle_scripts: bool = False  # Bundle multiple scripts into one
    minify: bool = True
    generate_source_maps: bool = True
    parallel_analysis: int = 4


class ScriptOptimizer:
    """
    Build-time script optimizer.
    
    Analyzes and optimizes scripts:
    1. Calculates SRI hashes
    2. Analyzes dependencies for optimal ordering
    3. Detects module vs classic scripts
    4. Generates preload hints
    5. Optional bundling via esbuild
    """
    
    def __init__(self, config: Optional[ScriptOptimizerConfig] = None):
        self.config = config or ScriptOptimizerConfig()
        self._analysis_cache: Dict[str, ScriptAnalysis] = {}
    
    def optimize_scripts(
        self,
        registry: Optional[ScriptRegistry] = None,
        project_root: Optional[Path] = None,
    ) -> Dict[str, ScriptAnalysis]:
        """
        Optimize all scripts in the registry.
        
        Returns dict of script analyses.
        """
        registry = registry or get_script_registry()
        project_root = project_root or Path.cwd()
        
        # Ensure directories exist
        output_dir = project_root / self.config.output_dir
        cache_dir = project_root / self.config.cache_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        results: Dict[str, ScriptAnalysis] = {}
        
        # Collect all scripts to analyze
        scripts_to_analyze = []
        for strategy in ScriptStrategy:
            for config in registry.get_by_strategy(strategy):
                if config.src and not config.src.startswith(('http://', 'https://')):
                    scripts_to_analyze.append(config)
        
        if not scripts_to_analyze:
            return results
        
        # Analyze scripts in parallel
        with ThreadPoolExecutor(max_workers=self.config.parallel_analysis) as executor:
            futures = {
                executor.submit(
                    self._analyze_script,
                    config,
                    project_root,
                    cache_dir,
                ): config
                for config in scripts_to_analyze
            }
            
            for future in as_completed(futures):
                config = futures[future]
                try:
                    analysis = future.result()
                    if analysis:
                        results[config.src] = analysis
                except Exception as e:
                    print(f"Error analyzing script {config.src}: {e}")
        
        return results
    
    def _analyze_script(
        self,
        config: ScriptConfig,
        project_root: Path,
        cache_dir: Path,
    ) -> Optional[ScriptAnalysis]:
        """Analyze a single script."""
        src = config.src
        if not src:
            return None
        
        # Resolve path
        if src.startswith('/'):
            script_path = project_root / "static" / src.lstrip('/')
        else:
            script_path = project_root / src
        
        if not script_path.exists():
            return None
        
        # Check cache
        content = script_path.read_text()
        content_hash = hashlib.md5(content.encode()).hexdigest()
        
        cache_file = cache_dir / f"{content_hash}.json"
        if cache_file.exists():
            cached = self._load_cached_analysis(cache_file)
            if cached:
                return cached
        
        # Analyze
        size = len(content.encode('utf-8'))
        is_module = config.type == ScriptType.MODULE or 'import ' in content or 'export ' in content
        
        # Find dependencies (import statements)
        dependencies = self._find_dependencies(content)
        
        # Find exports
        exports = self._find_exports(content)
        
        # Check if async-safe (no document.write, no immediate DOM access)
        is_async_safe = self._check_async_safe(content)
        
        # Calculate SRI hash
        sri_hash = None
        if self.config.calculate_sri:
            sri_hash = self._calculate_sri(content)
        
        # Estimate load time (rough: 50KB/s on slow 3G)
        load_time_estimate = (size / 50000) * 1000  # ms
        
        analysis = ScriptAnalysis(
            src=src,
            hash=content_hash,
            size=size,
            dependencies=dependencies,
            exports=exports,
            is_module=is_module,
            is_async_safe=is_async_safe,
            sri_hash=sri_hash,
            load_time_estimate=load_time_estimate,
        )
        
        # Cache result
        self._save_cached_analysis(cache_file, analysis)
        
        return analysis
    
    def _find_dependencies(self, content: str) -> List[str]:
        """Find import dependencies in script content."""
        dependencies = []
        
        # ES module imports
        import_pattern = r'import\s+(?:(?:\{[^}]*\}|[\w*]+)\s+from\s+)?[\'"]([^\'"]+)[\'"]'
        for match in re.finditer(import_pattern, content):
            dependencies.append(match.group(1))
        
        # Dynamic imports
        dynamic_pattern = r'import\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)'
        for match in re.finditer(dynamic_pattern, content):
            dependencies.append(match.group(1))
        
        # require() calls
        require_pattern = r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)'
        for match in re.finditer(require_pattern, content):
            dependencies.append(match.group(1))
        
        return list(set(dependencies))
    
    def _find_exports(self, content: str) -> List[str]:
        """Find exported symbols in script content."""
        exports = []
        
        # Named exports
        export_pattern = r'export\s+(?:const|let|var|function|class|async function)\s+(\w+)'
        for match in re.finditer(export_pattern, content):
            exports.append(match.group(1))
        
        # Export { ... }
        export_list_pattern = r'export\s*\{([^}]+)\}'
        for match in re.finditer(export_list_pattern, content):
            names = match.group(1)
            for name in re.findall(r'(\w+)(?:\s+as\s+\w+)?', names):
                exports.append(name)
        
        # Default export
        if 'export default' in content:
            exports.append('default')
        
        return list(set(exports))
    
    def _check_async_safe(self, content: str) -> bool:
        """Check if script can be safely loaded async."""
        # Patterns that indicate script needs synchronous loading
        unsafe_patterns = [
            r'document\.write',
            r'document\.writeln',
            r'document\.getElementById\s*\([^)]+\)',  # Immediate DOM access
            r'window\.onload\s*=',  # Legacy event handlers
        ]
        
        for pattern in unsafe_patterns:
            if re.search(pattern, content):
                return False
        
        return True
    
    def _calculate_sri(self, content: str) -> str:
        """Calculate Subresource Integrity hash."""
        import base64
        
        # Use SHA-384 (recommended for SRI)
        digest = hashlib.sha384(content.encode('utf-8')).digest()
        base64_hash = base64.b64encode(digest).decode('ascii')
        
        return f"sha384-{base64_hash}"
    
    def _load_cached_analysis(self, cache_file: Path) -> Optional[ScriptAnalysis]:
        """Load cached analysis."""
        try:
            with open(cache_file) as f:
                data = json.load(f)
            
            return ScriptAnalysis(
                src=data["src"],
                hash=data["hash"],
                size=data["size"],
                dependencies=data["dependencies"],
                exports=data["exports"],
                is_module=data["isModule"],
                is_async_safe=data["isAsyncSafe"],
                sri_hash=data.get("sriHash"),
                load_time_estimate=data["loadTimeEstimate"],
            )
        except Exception:
            return None
    
    def _save_cached_analysis(self, cache_file: Path, analysis: ScriptAnalysis) -> None:
        """Save analysis to cache."""
        try:
            data = {
                "src": analysis.src,
                "hash": analysis.hash,
                "size": analysis.size,
                "dependencies": analysis.dependencies,
                "exports": analysis.exports,
                "isModule": analysis.is_module,
                "isAsyncSafe": analysis.is_async_safe,
                "sriHash": analysis.sri_hash,
                "loadTimeEstimate": analysis.load_time_estimate,
            }
            
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Failed to cache script analysis: {e}")
    
    def get_optimal_load_order(
        self,
        analyses: Dict[str, ScriptAnalysis],
    ) -> List[str]:
        """
        Get optimal script loading order based on dependencies.
        
        Uses topological sort to ensure dependencies load first.
        """
        # Build dependency graph
        graph: Dict[str, Set[str]] = {}
        for src, analysis in analyses.items():
            graph[src] = set()
            for dep in analysis.dependencies:
                if dep in analyses:
                    graph[src].add(dep)
        
        # Topological sort
        result = []
        visited = set()
        temp_visited = set()
        
        def visit(node: str):
            if node in temp_visited:
                # Circular dependency - break it
                return
            if node in visited:
                return
            
            temp_visited.add(node)
            
            for dep in graph.get(node, []):
                visit(dep)
            
            temp_visited.remove(node)
            visited.add(node)
            result.append(node)
        
        for node in graph:
            if node not in visited:
                visit(node)
        
        return result
    
    def generate_preload_hints(
        self,
        analyses: Dict[str, ScriptAnalysis],
        priority_threshold: float = 500.0,  # ms
    ) -> List[str]:
        """
        Generate preload hints for critical scripts.
        
        Scripts above priority threshold get preload links.
        """
        hints = []
        
        for src, analysis in analyses.items():
            # Large scripts or critical dependencies get preloaded
            if analysis.load_time_estimate > priority_threshold:
                continue
            
            rel = "modulepreload" if analysis.is_module else "preload"
            attrs = [f'rel="{rel}"', f'href="{src}"']
            
            if rel == "preload":
                attrs.append('as="script"')
            
            if analysis.sri_hash:
                attrs.append(f'integrity="{analysis.sri_hash}"')
                attrs.append('crossorigin="anonymous"')
            
            hints.append(f'<link {" ".join(attrs)} />')
        
        return hints
    
    def bundle_scripts(
        self,
        scripts: List[str],
        output_path: Path,
        minify: bool = True,
    ) -> Optional[Path]:
        """
        Bundle multiple scripts into one using esbuild.
        
        Returns path to bundled file.
        """
        try:
            # Check if esbuild is available
            result = subprocess.run(
                ["esbuild", "--version"],
                capture_output=True,
                check=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("esbuild not found, skipping bundling")
            return None
        
        # Create entry point that imports all scripts
        entry_content = "\n".join([f'import "{s}";' for s in scripts])
        entry_path = output_path.parent / "_bundle_entry.js"
        entry_path.write_text(entry_content)
        
        try:
            cmd = [
                "esbuild",
                str(entry_path),
                "--bundle",
                f"--outfile={output_path}",
            ]
            
            if minify:
                cmd.append("--minify")
            
            if self.config.generate_source_maps:
                cmd.append("--sourcemap")
            
            subprocess.run(cmd, check=True, capture_output=True)
            
            return output_path
            
        except subprocess.CalledProcessError as e:
            print(f"Failed to bundle scripts: {e}")
            return None
        finally:
            # Clean up entry point
            if entry_path.exists():
                entry_path.unlink()


def optimize_scripts_for_build(
    project_root: Optional[Path] = None,
    config: Optional[ScriptOptimizerConfig] = None,
) -> Dict[str, ScriptAnalysis]:
    """
    Optimize all registered scripts for production build.
    
    Called by CLI build command.
    """
    optimizer = ScriptOptimizer(config)
    return optimizer.optimize_scripts(project_root=project_root)


def generate_script_manifest(
    analyses: Dict[str, ScriptAnalysis],
    output_path: Path,
) -> None:
    """
    Generate a manifest of all scripts with their metadata.
    
    Useful for debugging and build introspection.
    """
    manifest = {
        "scripts": {
            src: {
                "hash": a.hash,
                "size": a.size,
                "dependencies": a.dependencies,
                "exports": a.exports,
                "isModule": a.is_module,
                "isAsyncSafe": a.is_async_safe,
                "sriHash": a.sri_hash,
                "loadTimeEstimate": a.load_time_estimate,
            }
            for src, a in analyses.items()
        },
        "totalSize": sum(a.size for a in analyses.values()),
        "totalScripts": len(analyses),
    }
    
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)

