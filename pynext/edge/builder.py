"""
Edge Builder - Build for Edge Deployment

Compiles PyNext applications for edge deployment,
generating platform-specific output.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from .detector import EdgePlatform
from .adapters import get_adapter
from .decorator import EdgeConfig, get_edge_config, is_edge_function


@dataclass
class BuildResult:
    """
    Result of edge build.
    
    Attributes:
        platform: Target platform
        output_dir: Output directory path
        files: List of generated files
        entry_point: Main entry point file
        config_file: Platform config file
        success: Whether build succeeded
        errors: Any error messages
    """
    platform: EdgePlatform
    output_dir: Path
    files: List[Path] = field(default_factory=list)
    entry_point: Optional[Path] = None
    config_file: Optional[Path] = None
    success: bool = True
    errors: List[str] = field(default_factory=list)


class EdgeBuilder:
    """
    Builds PyNext app for edge deployment.
    
    Example:
        builder = EdgeBuilder(
            app_dir=Path("app"),
            output_dir=Path("dist"),
            platform=EdgePlatform.CLOUDFLARE,
        )
        result = builder.build()
    """
    
    def __init__(
        self,
        app_dir: Path,
        output_dir: Path,
        platform: EdgePlatform,
        config: Optional[Dict[str, Any]] = None,
    ):
        self.app_dir = app_dir
        self.output_dir = output_dir
        self.platform = platform
        self.config = config or {}
        self.adapter = get_adapter(platform)
        
        self._edge_functions: List[tuple[str, Callable, EdgeConfig]] = []
    
    def build(self) -> BuildResult:
        """
        Build the application for edge deployment.
        
        Returns:
            BuildResult with build status and files
        """
        result = BuildResult(
            platform=self.platform,
            output_dir=self.output_dir,
        )
        
        try:
            # Create output directory
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # Discover edge functions
            self._discover_edge_functions()
            
            # Generate runtime
            runtime_path = self._generate_runtime()
            result.files.append(runtime_path)
            
            # Generate entry point
            entry_path = self._generate_entry_point()
            result.files.append(entry_path)
            result.entry_point = entry_path
            
            # Generate platform config
            config_path = self._generate_platform_config()
            if config_path:
                result.files.append(config_path)
                result.config_file = config_path
            
            # Copy static assets
            static_files = self._copy_static_assets()
            result.files.extend(static_files)
            
        except Exception as e:
            result.success = False
            result.errors.append(str(e))
        
        return result
    
    def _discover_edge_functions(self):
        """Discover all @edge decorated functions."""
        import importlib.util
        import sys
        
        for py_file in self.app_dir.rglob("*.py"):
            # Skip __pycache__ and tests
            if "__pycache__" in str(py_file) or "test" in py_file.name:
                continue
            
            # Import the module
            module_name = py_file.stem
            spec = importlib.util.spec_from_file_location(module_name, py_file)
            if not spec or not spec.loader:
                continue
            
            module = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(module)
            except Exception:
                continue
            
            # Find edge functions
            for name in dir(module):
                obj = getattr(module, name)
                if callable(obj) and is_edge_function(obj):
                    config = get_edge_config(obj)
                    route = self._derive_route(py_file)
                    self._edge_functions.append((route, obj, config))
    
    def _derive_route(self, file_path: Path) -> str:
        """Derive API route from file path."""
        relative = file_path.relative_to(self.app_dir)
        route = "/" + str(relative.with_suffix("")).replace("\\", "/")
        
        # Handle index files
        if route.endswith("/index"):
            route = route[:-6] or "/"
        
        # Handle api routes
        if "api" in route:
            return route
        
        return f"/api{route}"
    
    def _generate_runtime(self) -> Path:
        """Generate the PyNext edge runtime."""
        runtime_code = '''
// PyNext Edge Runtime
export class PyNextHandler {
    constructor(env) {
        this.env = env;
        this.routes = new Map();
    }
    
    async handle(request) {
        const url = new URL(request.url);
        const path = url.pathname;
        
        // Route matching
        for (const [pattern, handler] of this.routes) {
            if (this.matchRoute(path, pattern)) {
                return await handler(request, this.env);
            }
        }
        
        return new Response('Not Found', { status: 404 });
    }
    
    matchRoute(path, pattern) {
        if (pattern === path) return true;
        
        // Simple wildcard matching
        if (pattern.endsWith('/*')) {
            const prefix = pattern.slice(0, -2);
            return path.startsWith(prefix);
        }
        
        return false;
    }
    
    addRoute(pattern, handler) {
        this.routes.set(pattern, handler);
    }
}

// Response helpers
export function json(data, init = {}) {
    return new Response(JSON.stringify(data), {
        headers: { 'Content-Type': 'application/json', ...init.headers },
        status: init.status || 200,
    });
}

export function text(str, init = {}) {
    return new Response(str, {
        headers: { 'Content-Type': 'text/plain', ...init.headers },
        status: init.status || 200,
    });
}

export function html(str, init = {}) {
    return new Response(str, {
        headers: { 'Content-Type': 'text/html', ...init.headers },
        status: init.status || 200,
    });
}

export function redirect(url, status = 302) {
    return new Response(null, {
        status,
        headers: { Location: url },
    });
}
'''
        
        runtime_path = self.output_dir / "pynext-runtime.js"
        runtime_path.write_text(runtime_code)
        return runtime_path
    
    def _generate_entry_point(self) -> Path:
        """Generate the main entry point."""
        # Get entry point from adapter
        entry_code = self.adapter.generate_entry_point(
            handler=None,  # Will be populated with discovered functions
            config=self.config,
        )
        
        # Add route registrations
        route_code = []
        for route, func, config in self._edge_functions:
            route_code.append(f'  handler.addRoute("{route}", async (req, env) => {{')
            route_code.append(f'    // Handler: {func.__name__}')
            route_code.append(f'    return json({{ "route": "{route}", "method": req.method }});')
            route_code.append(f'  }});')
        
        if route_code:
            # Insert route registrations after handler creation
            entry_code = entry_code.replace(
                'return await handler.handle(request);',
                '\n'.join(route_code) + '\n    return await handler.handle(request);'
            )
        
        entry_path = self.output_dir / "_worker.js"
        entry_path.write_text(entry_code)
        return entry_path
    
    def _generate_platform_config(self) -> Optional[Path]:
        """Generate platform-specific config file."""
        config_content = self.adapter.generate_config(self.config)
        if not config_content:
            return None
        
        # Determine config filename
        if self.platform == EdgePlatform.CLOUDFLARE:
            config_path = self.output_dir / "wrangler.toml"
        elif self.platform == EdgePlatform.VERCEL:
            config_path = self.output_dir / "vercel.json"
        elif self.platform == EdgePlatform.DENO:
            config_path = self.output_dir / "deno.json"
        elif self.platform == EdgePlatform.BUN:
            config_path = self.output_dir / "bunfig.toml"
        else:
            return None
        
        config_path.write_text(config_content)
        return config_path
    
    def _copy_static_assets(self) -> List[Path]:
        """Copy static assets to output."""
        static_dir = self.app_dir / "static"
        if not static_dir.exists():
            static_dir = self.app_dir.parent / "public"
        
        if not static_dir.exists():
            return []
        
        output_static = self.output_dir / "static"
        output_static.mkdir(exist_ok=True)
        
        copied = []
        for asset in static_dir.rglob("*"):
            if asset.is_file():
                relative = asset.relative_to(static_dir)
                dest = output_static / relative
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(asset, dest)
                copied.append(dest)
        
        return copied


def build_for_edge(
    app_dir: Path,
    output_dir: Path,
    platform: str,
    config: Optional[Dict[str, Any]] = None,
) -> BuildResult:
    """
    Build application for edge deployment.
    
    Convenience function for CLI usage.
    
    Args:
        app_dir: Application directory
        output_dir: Output directory
        platform: Platform name (cloudflare, vercel, deno, bun)
        config: Optional configuration
        
    Returns:
        BuildResult
        
    Example:
        result = build_for_edge(
            app_dir=Path("app"),
            output_dir=Path("dist"),
            platform="cloudflare",
        )
        
        if result.success:
            print(f"Built to {result.output_dir}")
    """
    edge_platform = EdgePlatform(platform)
    
    builder = EdgeBuilder(
        app_dir=app_dir,
        output_dir=output_dir,
        platform=edge_platform,
        config=config or {},
    )
    
    return builder.build()

