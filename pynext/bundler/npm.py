"""
NPM package bundler for PyNext.

Provides integration with npm packages via esbuild.
Supports React components via Preact aliasing for optimal bundle size.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Optional


class NPMBundler:
    """
    Bundles npm packages for use in PyNext applications.
    
    Uses esbuild for fast, efficient bundling with tree-shaking.
    Supports React → Preact aliasing for efficient React component usage.
    """
    
    def __init__(
        self,
        project_dir: str = ".",
        output_dir: str = ".pynext/bundles",
        react_compat: bool = False,
    ):
        self.project_dir = Path(project_dir).resolve()
        self.output_dir = Path(output_dir).resolve()
        self.config_file = self.project_dir / "pynext.config.py"
        self._packages: dict[str, str] = {}  # name -> version
        self._bundled: dict[str, Path] = {}  # name -> bundle path
        self._react_compat = react_compat
        self._react_packages: set[str] = set()  # Packages that need React
    
    def _ensure_esbuild(self) -> bool:
        """Ensure esbuild is available."""
        # Check if esbuild is in PATH
        if shutil.which("esbuild"):
            return True
        
        # Check if npx is available
        if shutil.which("npx"):
            return True
        
        return False
    
    def _get_esbuild_aliases(self) -> list[str]:
        """Get esbuild alias arguments for React → Preact."""
        if not self._react_compat:
            return []
        
        return [
            "--alias:react=preact/compat",
            "--alias:react-dom=preact/compat",
            "--alias:react-dom/client=preact/compat",
            "--alias:react/jsx-runtime=preact/jsx-runtime",
            "--alias:react/jsx-dev-runtime=preact/jsx-runtime",
        ]
    
    def _run_esbuild(self, entry: str, output: str, **options) -> bool:
        """Run esbuild with given options."""
        cmd = ["esbuild", entry, f"--outfile={output}"]
        
        # Add options
        if options.get("bundle", True):
            cmd.append("--bundle")
        if options.get("minify", True):
            cmd.append("--minify")
        if options.get("sourcemap"):
            cmd.append("--sourcemap")
        if options.get("format", "esm"):
            cmd.append(f"--format={options.get('format', 'esm')}")
        if options.get("target"):
            cmd.append(f"--target={options.get('target')}")
        if options.get("external"):
            for ext in options["external"]:
                cmd.append(f"--external:{ext}")
        
        # Add JSX handling for React components
        if options.get("jsx", False) or self._react_compat:
            cmd.append("--jsx=automatic")
            if self._react_compat:
                cmd.append("--jsx-import-source=preact")
        
        # Add React → Preact aliases
        if options.get("react_aliases", True):
            cmd.extend(self._get_esbuild_aliases())
        
        # Add loader for JSX files
        cmd.append("--loader:.js=jsx")
        cmd.append("--loader:.jsx=jsx")
        cmd.append("--loader:.ts=tsx")
        cmd.append("--loader:.tsx=tsx")
        
        # Try direct esbuild first, then npx
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True,
                cwd=str(self.project_dir)
            )
            if result.returncode == 0:
                return True
            
            # Try npx
            cmd_npx = ["npx", "esbuild"] + cmd[1:]
            result = subprocess.run(
                cmd_npx, 
                capture_output=True, 
                text=True,
                cwd=str(self.project_dir)
            )
            if result.returncode != 0:
                print(f"[PyNext] esbuild error: {result.stderr}")
            return result.returncode == 0
        except Exception as e:
            print(f"[PyNext] Error running esbuild: {e}")
            return False
    
    def add_package(self, name: str, version: str = "latest", needs_react: bool = False) -> None:
        """Add an npm package to be bundled."""
        self._packages[name] = version
        if needs_react:
            self._react_packages.add(name)
            self._react_compat = True
    
    def load_config(self) -> None:
        """
        Load npm package configuration.
        
        Reads from pynext.npm.txt (preferred) or pynext.config.py (legacy).
        """
        # Try new format first: pynext.npm.txt
        npm_txt_path = self.project_dir / "pynext.npm.txt"
        if npm_txt_path.exists():
            self._load_from_npm_txt(npm_txt_path)
        
        # Also check legacy format in pynext.config.py
        if self.config_file.exists():
            self._load_from_config_py()
    
    def _load_from_npm_txt(self, path: Path) -> None:
        """Load packages from pynext.npm.txt file."""
        try:
            from pynext.deps import DependencyManager
            
            deps_manager = DependencyManager(str(self.project_dir))
            packages = deps_manager.load_npm_packages()
            
            for pkg in packages:
                self._packages[pkg.name] = pkg.version
                if self._is_react_package(pkg.name):
                    self._react_packages.add(pkg.name)
                    self._react_compat = True
        except ImportError:
            # Fallback: parse manually if deps module not available
            for line in path.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                
                # Parse package@version or @scope/package@version
                if line.startswith("@"):
                    # Scoped package
                    at_positions = [i for i, c in enumerate(line) if c == "@"]
                    if len(at_positions) >= 2:
                        last_at = at_positions[-1]
                        name = line[:last_at]
                        version = line[last_at + 1:]
                    else:
                        name = line
                        version = "latest"
                else:
                    if "@" in line:
                        name, version = line.rsplit("@", 1)
                    else:
                        name = line
                        version = "latest"
                
                self._packages[name] = version
                if self._is_react_package(name):
                    self._react_packages.add(name)
                    self._react_compat = True
    
    def _load_from_config_py(self) -> None:
        """Load packages from pynext.config.py (legacy format)."""
        config_globals: dict[str, Any] = {}
        exec(self.config_file.read_text(), config_globals)
        
        # Check for react_compat setting
        if config_globals.get("react_compat", False):
            self._react_compat = True
        
        if "npm_packages" in config_globals:
            packages = config_globals["npm_packages"]
            if isinstance(packages, list):
                for pkg in packages:
                    if isinstance(pkg, str):
                        self._packages[pkg] = "latest"
                        # Auto-detect React packages
                        if self._is_react_package(pkg):
                            self._react_packages.add(pkg)
                            self._react_compat = True
                    elif isinstance(pkg, dict):
                        for name, version in pkg.items():
                            self._packages[name] = version
                            if self._is_react_package(name):
                                self._react_packages.add(name)
                                self._react_compat = True
            elif isinstance(packages, dict):
                self._packages.update(packages)
                for name in packages:
                    if self._is_react_package(name):
                        self._react_packages.add(name)
                        self._react_compat = True
    
    def _is_react_package(self, name: str) -> bool:
        """Check if a package is likely a React package."""
        react_indicators = [
            "react-",
            "@react",
            "react/",
            "@mui/",
            "@chakra-ui/",
            "@headlessui/react",
            "@radix-ui/",
            "@emotion/react",
            "styled-components",
            "framer-motion",
        ]
        return any(name.startswith(ind) or ind in name for ind in react_indicators)
    
    def install_packages(self) -> bool:
        """Install npm packages using npm."""
        packages_to_install = dict(self._packages)
        
        # Add Preact if react_compat is enabled
        if self._react_compat:
            if "preact" not in packages_to_install:
                packages_to_install["preact"] = "latest"
            print("[PyNext] React compatibility enabled - using Preact (~4KB) as React runtime")
        
        if not packages_to_install:
            return True
        
        # Ensure node_modules directory exists
        node_modules = self.project_dir / "node_modules"
        
        # Create package.json if it doesn't exist
        package_json = self.project_dir / "package.json"
        if not package_json.exists():
            package_json.write_text(json.dumps({
                "name": "pynext-app",
                "private": True,
                "type": "module",
                "dependencies": {}
            }, indent=2))
        
        # Install packages
        install_list = [
            f"{name}@{version}" if version != "latest" else name
            for name, version in packages_to_install.items()
        ]
        
        cmd = ["npm", "install", "--save"] + install_list
        
        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.project_dir),
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                print(f"[PyNext] npm install error: {result.stderr}")
            return result.returncode == 0
        except Exception as e:
            print(f"[PyNext] Error installing packages: {e}")
            return False
    
    def bundle_preact_runtime(self) -> Optional[Path]:
        """Bundle the Preact runtime for React compatibility."""
        if not self._react_compat:
            return None
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create entry file that exports Preact as React
        entry_content = '''
// Preact runtime with React compatibility
export * from "preact/compat";
export { render, hydrate } from "preact";
import { createElement, Fragment } from "preact/compat";
export { createElement, Fragment };
export { createElement as h };

// Re-export hooks
export {
    useState,
    useEffect,
    useRef,
    useMemo,
    useCallback,
    useContext,
    useReducer,
    useLayoutEffect,
    useImperativeHandle,
    useDebugValue,
} from "preact/hooks";
'''
        
        entry_file = self.output_dir / "_entry_preact_runtime.js"
        entry_file.write_text(entry_content)
        
        output_file = self.output_dir / "preact-runtime.bundle.js"
        
        success = self._run_esbuild(
            str(entry_file),
            str(output_file),
            bundle=True,
            minify=True,
            format="esm",
            target="es2020",
            react_aliases=False,  # Don't alias for the runtime itself
        )
        
        entry_file.unlink()
        
        if success:
            self._bundled["__preact_runtime__"] = output_file
            return output_file
        return None
    
    def bundle_package(self, name: str, exports: Optional[list[str]] = None) -> Optional[Path]:
        """
        Bundle a single npm package.
        
        Args:
            name: Package name
            exports: Optional list of exports to include (tree-shaking)
        
        Returns:
            Path to the bundled file, or None on error
        """
        if not self._ensure_esbuild():
            print("[PyNext] esbuild not found. Install with: npm install -g esbuild")
            return None
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create entry file
        if exports:
            entry_content = f'export {{ {", ".join(exports)} }} from "{name}";'
        else:
            entry_content = f'export * from "{name}";'
        
        safe_name = name.replace("/", "_").replace("@", "").replace("-", "_")
        entry_file = self.output_dir / f"_entry_{safe_name}.js"
        entry_file.write_text(entry_content)
        
        # Output bundle
        output_file = self.output_dir / f"{safe_name}.bundle.js"
        
        # Run esbuild with React aliasing if this is a React package
        is_react_pkg = name in self._react_packages or self._is_react_package(name)
        
        success = self._run_esbuild(
            str(entry_file),
            str(output_file),
            bundle=True,
            minify=True,
            format="esm",
            target="es2020",
            jsx=is_react_pkg,
            react_aliases=is_react_pkg and self._react_compat,
        )
        
        # Cleanup entry file
        if entry_file.exists():
            entry_file.unlink()
        
        if success:
            self._bundled[name] = output_file
            return output_file
        return None
    
    def bundle_all(self) -> dict[str, Path]:
        """Bundle all registered packages."""
        self.load_config()
        
        if not self._packages and not self._react_compat:
            return {}
        
        # Install packages first
        if not self.install_packages():
            print("[PyNext] Failed to install npm packages")
            return {}
        
        # Bundle Preact runtime first if needed
        if self._react_compat:
            self.bundle_preact_runtime()
        
        # Bundle each package
        for name in self._packages:
            self.bundle_package(name)
        
        return dict(self._bundled)
    
    def bundle_for_route(
        self, 
        route: str, 
        packages: dict[str, list[str]]
    ) -> Optional[Path]:
        """
        Bundle npm packages for a specific route with tree-shaking.
        
        Args:
            route: Route pattern (e.g., "/dashboard")
            packages: Dict of package name -> list of exports used
                     e.g., {"lodash": ["debounce", "throttle"]}
        
        Returns:
            Path to the route-specific bundle
        
        Example:
            bundler.bundle_for_route("/dashboard", {
                "chart.js": ["Chart", "LineController"],
                "lodash": ["debounce"],
            })
        """
        if not packages:
            return None
        
        if not self._ensure_esbuild():
            return None
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create entry file with only the used exports
        entry_parts = []
        for pkg_name, exports in packages.items():
            if exports:
                # Import only specific exports (tree-shaking)
                exports_str = ", ".join(exports)
                safe_name = pkg_name.replace("/", "_").replace("@", "").replace("-", "_")
                entry_parts.append(
                    f'export {{ {exports_str} }} from "{pkg_name}";'
                )
            else:
                # Import all (esbuild will still tree-shake unused)
                entry_parts.append(f'export * from "{pkg_name}";')
        
        entry_content = "\n".join(entry_parts)
        
        # Generate route-specific file name
        safe_route = route.strip('/').replace('/', '-') or 'index'
        entry_file = self.output_dir / f"_entry_route_{safe_route}.js"
        entry_file.write_text(entry_content)
        
        output_file = self.output_dir / f"route-{safe_route}.bundle.js"
        
        success = self._run_esbuild(
            str(entry_file),
            str(output_file),
            bundle=True,
            minify=True,
            format="esm",
            target="es2020",
        )
        
        # Cleanup
        if entry_file.exists():
            entry_file.unlink()
        
        if success:
            self._bundled[f"route:{route}"] = output_file
            return output_file
        return None
    
    def analyze_package_usage(self, source_code: str, package_name: str) -> list[str]:
        """
        Analyze source code to find which exports are used from a package.
        
        This enables tree-shaking by only bundling used exports.
        
        Args:
            source_code: Python/JS source code to analyze
            package_name: npm package name
        
        Returns:
            List of export names used
        """
        import re
        
        exports_used = set()
        safe_name = package_name.replace("/", "_").replace("@", "").replace("-", "_")
        
        # Pattern: import { X, Y } from "package"
        pattern1 = rf'import\s*\{{\s*([^}}]+)\s*\}}\s*from\s*["\']' + re.escape(package_name) + r'["\']'
        for match in re.finditer(pattern1, source_code):
            exports = [e.strip() for e in match.group(1).split(',')]
            exports_used.update(exports)
        
        # Pattern: from package import X, Y (Python-style in strings)
        pattern2 = rf'from\s+{re.escape(package_name)}\s+import\s+([^\n;]+)'
        for match in re.finditer(pattern2, source_code):
            exports = [e.strip() for e in match.group(1).split(',')]
            exports_used.update(exports)
        
        # Pattern: usage like lodash.debounce or package_name.export
        pattern3 = rf'(?:{re.escape(safe_name)}|{re.escape(package_name)})\.(\w+)'
        for match in re.finditer(pattern3, source_code):
            exports_used.add(match.group(1))
        
        return list(exports_used)
    
    def get_bundle_path(self, name: str) -> Optional[Path]:
        """Get the path to a bundled package."""
        return self._bundled.get(name)
    
    def get_script_tag(self, name: str) -> str:
        """Get an HTML script tag for importing a bundled package."""
        bundle_path = self.get_bundle_path(name)
        if bundle_path:
            relative_path = bundle_path.relative_to(self.project_dir)
            return f'<script type="module" src="/{relative_path}"></script>'
        return ""
    
    def get_import_map(self) -> dict[str, str]:
        """Get an import map for all bundled packages."""
        import_map = {}
        for name in self._bundled:
            safe_name = name.replace("/", "_").replace("@", "").replace("-", "_")
            import_map[name] = f"/_pynext/npm/{safe_name}.bundle.js"
        
        # Add React aliases to import map if react_compat is enabled
        if self._react_compat:
            import_map["react"] = "/_pynext/npm/preact-runtime.bundle.js"
            import_map["react-dom"] = "/_pynext/npm/preact-runtime.bundle.js"
        
        return import_map
    
    def get_import_map_json(self) -> str:
        """Get import map as JSON for HTML script tag."""
        return json.dumps({"imports": self.get_import_map()}, indent=2)
    
    @property
    def react_compat_enabled(self) -> bool:
        """Check if React compatibility is enabled."""
        return self._react_compat


# Global bundler instance
_bundler: Optional[NPMBundler] = None


def get_bundler() -> NPMBundler:
    """Get the global npm bundler instance."""
    global _bundler
    if _bundler is None:
        _bundler = NPMBundler()
    return _bundler


def npm_import(package_name: str, exports: Optional[list[str]] = None) -> str:
    """
    Import an npm package and return the bundle URL.
    
    Usage:
        chart_url = npm_import("chart.js", ["Chart"])
        
        # In component:
        script(src=chart_url, type="module")
    """
    bundler = get_bundler()
    
    # Check if already bundled
    bundle_path = bundler.get_bundle_path(package_name)
    if not bundle_path:
        bundler.add_package(package_name)
        bundle_path = bundler.bundle_package(package_name, exports)
    
    if bundle_path:
        safe_name = package_name.replace("/", "_").replace("@", "").replace("-", "_")
        return f"/_pynext/npm/{safe_name}.bundle.js"
    return ""


class NPMPackage:
    """
    Lazy-loading wrapper for npm packages.
    
    Usage:
        chart = NPMPackage("chart.js")
        
        @component
        def ChartComponent():
            return div()[
                script(type="module")[f'''
                    import {{ Chart }} from "{chart.url}";
                    // Use Chart...
                ''']
            ]
    """
    
    def __init__(self, name: str, exports: Optional[list[str]] = None):
        self.name = name
        self.exports = exports
        self._url: Optional[str] = None
    
    @property
    def url(self) -> str:
        """Get the URL to the bundled package."""
        if self._url is None:
            self._url = npm_import(self.name, self.exports)
        return self._url
    
    def script_tag(self, **attrs) -> str:
        """Generate a script tag for this package."""
        attr_str = " ".join(f'{k}="{v}"' for k, v in attrs.items())
        return f'<script type="module" src="{self.url}" {attr_str}></script>'
