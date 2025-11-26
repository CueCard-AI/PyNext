"""
Command-line interface for PyNext.

Provides commands for development, building, and project initialization.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def cmd_dev(args: argparse.Namespace) -> int:
    """Run the development server."""
    from pynext.server.dev import run_dev_server
    from pynext.deps import DependencyManager
    
    # Check dependencies on startup (unless --skip-deps)
    if not args.skip_deps:
        deps = DependencyManager(".")
        if deps.has_dependencies():
            missing = deps.check_all()
            if missing["python"] or missing["npm"]:
                print("[PyNext] Checking dependencies...")
                deps.print_status()
                if not args.no_install:
                    print("[PyNext] Installing missing dependencies...")
                    deps.install_all()
    
    run_dev_server(
        pages_dir=args.pages,
        static_dir=args.static,
        host=args.host,
        port=args.port,
    )
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    """Build for production."""
    import asyncio
    from pynext.bundler.npm import get_bundler
    from pynext.router.file_router import FileRouter
    
    print("[PyNext] Building for production...")
    
    # Bundle npm packages
    bundler = get_bundler()
    bundler.project_dir = Path(args.dir).resolve()
    bundler.output_dir = Path(args.output).resolve() / "bundles"
    bundles = bundler.bundle_all()
    
    if bundles:
        print(f"[PyNext] Bundled {len(bundles)} npm packages")
    
    # Process images (build-time optimization)
    try:
        from pynext.bundler.images import process_images_for_build
        
        static_path = Path(args.static).resolve()
        image_output = Path(args.output).resolve() / "_next" / "image"
        
        print("[PyNext] Processing images...")
        result = asyncio.run(process_images_for_build(
            source_dir=static_path,
            output_dir=image_output,
        ))
        
        if result["total"] > 0:
            print(f"[PyNext] Processed {result['successful']}/{result['total']} images")
            if result["zero_js_pages"] if "zero_js_pages" in result else 0:
                print(f"[PyNext]   → Zero JS images: {result.get('zero_js_pages', 'all')}")
            if result["errors"]:
                for err in result["errors"]:
                    print(f"[PyNext]   ⚠ {err['src']}: {err['error']}")
    except ImportError:
        print("[PyNext] Image processing skipped (Pillow not installed)")
    except Exception as e:
        print(f"[PyNext] Image processing error: {e}")
    
    # Scan routes
    router = FileRouter(args.pages)
    router.scan()
    print(f"[PyNext] Found {len(router.routes)} routes")
    
    # Copy static files
    static_dir = Path(args.static)
    output_static = Path(args.output) / "static"
    if static_dir.exists():
        import shutil
        if output_static.exists():
            shutil.rmtree(output_static)
        shutil.copytree(static_dir, output_static)
        print(f"[PyNext] Copied static files")
    
    # Static Site Generation (SSG)
    try:
        from pynext.bundler.static import build_static_site
        
        print("[PyNext] Generating static pages...")
        ssg_result = asyncio.run(build_static_site(
            pages_dir=Path(args.pages).resolve(),
            output_dir=Path(args.output).resolve(),
            static_dir=Path(args.static).resolve(),
        ))
        
        if ssg_result.total_pages > 0:
            print(f"[PyNext] Generated {ssg_result.total_pages} static pages:")
            print(f"[PyNext]   → Zero JS pages: {ssg_result.zero_js_pages}")
            print(f"[PyNext]   → Hybrid pages (islands): {ssg_result.hybrid_pages}")
            if ssg_result.errors:
                for err in ssg_result.errors:
                    print(f"[PyNext]   ⚠ {err['route']}: {err['error']}")
    except ImportError as e:
        print(f"[PyNext] SSG skipped: {e}")
    except Exception as e:
        print(f"[PyNext] SSG error: {e}")
    
    # Partial Prerendering (PPR) Analysis
    try:
        from pynext.bundler.ppr import analyze_ppr_for_build, PPRBuildConfig
        
        print("[PyNext] Analyzing PPR boundaries...")
        ppr_config = PPRBuildConfig(
            output_dir=Path(args.output).resolve() / ".pynext" / "ppr-cache",
        )
        ppr_results = analyze_ppr_for_build(
            pages_dir=Path(args.pages).resolve(),
            project_root=Path(args.dir).resolve(),
            config=ppr_config,
        )
        
        if ppr_results:
            fully_static = sum(1 for p in ppr_results.values() if p.is_fully_static)
            hybrid = sum(1 for p in ppr_results.values() if p.has_dynamic_parts)
            print(f"[PyNext] Analyzed {len(ppr_results)} pages for PPR:")
            print(f"[PyNext]   → Fully static (zero hydration): {fully_static}")
            print(f"[PyNext]   → Hybrid (static shell + dynamic holes): {hybrid}")
            print(f"[PyNext]   → Component-level granularity enabled")
    except ImportError as e:
        print(f"[PyNext] PPR analysis skipped: {e}")
    except Exception as e:
        print(f"[PyNext] PPR analysis error: {e}")
    
    # Font Optimization (build-time processing)
    try:
        from pynext.bundler.fonts import process_fonts_for_build, FontProcessorConfig
        
        print("[PyNext] Processing fonts...")
        font_config = FontProcessorConfig(
            output_dir=Path(args.output).resolve() / "_next" / "fonts",
            cache_dir=Path(args.dir).resolve() / ".pynext" / "font-cache",
        )
        fonts = process_fonts_for_build(
            project_root=Path(args.dir).resolve(),
            config=font_config,
        )
        
        if fonts:
            print(f"[PyNext] Processed {len(fonts)} fonts:")
            print(f"[PyNext]   → Zero JS overhead (pure CSS)")
            print(f"[PyNext]   → Precomputed size-adjust for no layout shift")
    except ImportError as e:
        print(f"[PyNext] Font processing skipped: {e}")
    except Exception as e:
        print(f"[PyNext] Font processing error: {e}")
    
    # Script Optimization (build-time analysis)
    try:
        from pynext.bundler.scripts import optimize_scripts_for_build, ScriptOptimizerConfig
        
        print("[PyNext] Analyzing scripts...")
        script_config = ScriptOptimizerConfig(
            output_dir=Path(args.output).resolve() / "_next" / "scripts",
            cache_dir=Path(args.dir).resolve() / ".pynext" / "script-cache",
        )
        script_analyses = optimize_scripts_for_build(
            project_root=Path(args.dir).resolve(),
            config=script_config,
        )
        
        if script_analyses:
            print(f"[PyNext] Analyzed {len(script_analyses)} scripts:")
            print(f"[PyNext]   → Zero wrapper overhead")
            print(f"[PyNext]   → Native loading strategies")
    except ImportError as e:
        print(f"[PyNext] Script analysis skipped: {e}")
    except Exception as e:
        print(f"[PyNext] Script analysis error: {e}")
    
    # Parallel Routes Compilation (build-time slot resolution)
    try:
        from pynext.bundler.parallel import build_parallel_routes_map
        
        print("[PyNext] Compiling parallel routes...")
        parallel_result = build_parallel_routes_map(
            pages_dir=Path(args.pages).resolve(),
            output_dir=Path(args.output).resolve(),
        )
        
        if parallel_result["total_slots"] > 0:
            print(f"[PyNext] Compiled {parallel_result['total_slots']} parallel slots:")
            print(f"[PyNext]   → Static slots: {parallel_result['static_slots']}")
            print(f"[PyNext]   → Interactive slots: {parallel_result['interactive_slots']}")
            print(f"[PyNext]   → Slot-level caching enabled")
    except ImportError as e:
        print(f"[PyNext] Parallel routes skipped: {e}")
    except Exception as e:
        print(f"[PyNext] Parallel routes error: {e}")
    
    # Intercepting Routes Compilation (modal pattern)
    try:
        from pynext.bundler.intercept import build_interception_map
        
        print("[PyNext] Compiling intercepting routes...")
        intercept_result = build_interception_map(
            pages_dir=Path(args.pages).resolve(),
            output_dir=Path(args.output).resolve(),
        )
        
        if intercept_result["total_rules"] > 0:
            print(f"[PyNext] Compiled {intercept_result['total_rules']} interception rules:")
            print(f"[PyNext]   → Static modals: {intercept_result['static_modals']}")
            print(f"[PyNext]   → Interactive modals: {intercept_result['interactive_modals']}")
            print(f"[PyNext]   → Background preserved as static")
    except ImportError as e:
        print(f"[PyNext] Interception routes skipped: {e}")
    except Exception as e:
        print(f"[PyNext] Interception routes error: {e}")
    
    # Generate route manifest
    manifest = {
        "routes": router.get_routes_info(),
        "bundles": {name: str(path) for name, path in bundles.items()},
    }
    
    manifest_path = Path(args.output) / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    
    import json
    manifest_path.write_text(json.dumps(manifest, indent=2))
    
    print(f"[PyNext] Build complete: {args.output}")
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    """Initialize a new PyNext project."""
    project_dir = Path(args.name).resolve()
    
    if project_dir.exists() and any(project_dir.iterdir()):
        print(f"Error: Directory {args.name} already exists and is not empty")
        return 1
    
    project_dir.mkdir(parents=True, exist_ok=True)
    
    # Create directory structure
    (project_dir / "pages").mkdir()
    (project_dir / "public").mkdir()
    (project_dir / "components").mkdir()
    
    # Create index page
    index_page = '''"""
PyNext - Home Page
"""

from pynext import page, Signal, div, h1, p, button, span


@page(title="Welcome to PyNext")
def index():
    count = Signal(0)
    
    return div(class_="container")[
        h1()["Welcome to PyNext! 🚀"],
        p()["A Python framework with SolidJS-inspired reactivity"],
        
        div(class_="counter")[
            p()[
                "Count: ",
                span()[count]
            ],
            button(onclick=lambda: count.update(lambda x: x + 1))[
                "Increment"
            ]
        ]
    ]
'''
    (project_dir / "pages" / "index.py").write_text(index_page)
    
    # Create about page
    about_page = '''"""
PyNext - About Page
"""

from pynext import page, div, h1, p, a


@page(title="About PyNext")
def about():
    return div(class_="container")[
        h1()["About PyNext"],
        p()[
            "PyNext is a Python web framework that combines the best of Next.js "
            "and SolidJS, providing file-based routing, fine-grained reactivity, "
            "and seamless Python integration."
        ],
        p()[
            a(href="/")["← Back to Home"]
        ]
    ]
'''
    (project_dir / "pages" / "about.py").write_text(about_page)
    
    # Create dynamic route example
    user_page = '''"""
PyNext - Dynamic Route Example
"""

from pynext import page, div, h1, p, a, get_params


@page(title="User Profile")
def user_profile(id: str = ""):
    params = get_params()
    user_id = params.get("id", id)
    
    return div(class_="container")[
        h1()[f"User Profile: {user_id}"],
        p()["This is a dynamic route example."],
        p()[
            a(href="/")["← Back to Home"]
        ]
    ]
'''
    (project_dir / "pages" / "users").mkdir()
    (project_dir / "pages" / "users" / "[id].py").write_text(user_page)
    
    # Create server action example
    action_page = '''"""
PyNext - Server Actions Example
"""

from pynext import page, server_action, div, h1, p, button, pre
import json
import os


@server_action
async def get_system_info() -> dict:
    """Server action that returns system information."""
    return {
        "python_version": os.sys.version,
        "platform": os.sys.platform,
        "cwd": os.getcwd(),
    }


@page(title="Server Actions")
def actions():
    return div(class_="container")[
        h1()["Server Actions"],
        p()["Click the button to call a server action:"],
        button(onclick=get_system_info)["Get System Info"],
        pre(id="result")["Results will appear here..."]
    ]
'''
    (project_dir / "pages" / "actions.py").write_text(action_page)
    
    # Create config file
    config = '''"""
PyNext Configuration
"""

# Build options
build = {
    "output": ".pynext/build",
    "minify": True,
}

# Development options
dev = {
    "port": 3000,
    "host": "127.0.0.1",
}
'''
    (project_dir / "pynext.config.py").write_text(config)
    
    # Create dependency files
    from pynext.deps import create_dependency_templates
    create_dependency_templates(str(project_dir))
    
    # Create base CSS
    base_css = '''/* PyNext Base Styles */

.container {
    max-width: 800px;
    margin: 0 auto;
    padding: 40px 20px;
}

h1 {
    color: #1a1a2e;
    margin-bottom: 20px;
}

p {
    color: #4a4a6a;
    margin-bottom: 16px;
}

button {
    background: #6366f1;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 16px;
    transition: background 0.2s;
}

button:hover {
    background: #4f46e5;
}

.counter {
    background: #f8f9fa;
    padding: 24px;
    border-radius: 12px;
    margin-top: 20px;
}

a {
    color: #6366f1;
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}

pre {
    background: #1a1a2e;
    color: #e2e8f0;
    padding: 16px;
    border-radius: 8px;
    overflow-x: auto;
    margin-top: 16px;
}
'''
    (project_dir / "public" / "styles.css").write_text(base_css)
    
    # Create .gitignore
    gitignore = '''# PyNext
.pynext/
__pycache__/
*.pyc
.env

# Node
node_modules/
package-lock.json

# IDE
.vscode/
.idea/
'''
    (project_dir / ".gitignore").write_text(gitignore)
    
    print(f"""
  ✨ Created PyNext project: {args.name}

  Next steps:
  
    cd {args.name}
    pip install pynext
    pynext dev

  Project structure:
  
    {args.name}/
    ├── pages/
    │   ├── index.py              # Home page
    │   ├── about.py              # About page
    │   ├── actions.py            # Server actions example
    │   └── users/
    │       └── [id].py           # Dynamic route
    ├── public/
    │   └── styles.css            # Base styles
    ├── components/               # Reusable components
    ├── pynext.config.py          # Configuration
    ├── pynext.requirements.txt   # Python dependencies
    └── pynext.npm.txt            # NPM dependencies
""")
    
    return 0


def cmd_routes(args: argparse.Namespace) -> int:
    """List all registered routes."""
    from pynext.router.file_router import FileRouter
    
    router = FileRouter(args.pages)
    router.scan()
    
    if not router.routes:
        print("No routes found.")
        return 0
    
    print("\nRegistered Routes:\n")
    for route in router.routes:
        print(f"  {route.pattern.url_pattern:<30} → {route.module_path}")
    print()
    
    return 0


def cmd_ui(args: argparse.Namespace) -> int:
    """Manage UI components (Tier 2: Official components)."""
    from pynext.registry import (
        list_available_components,
        copy_component_to_project,
        AVAILABLE_COMPONENTS,
    )
    from pynext.registry.components import copy_all_components
    
    project_dir = Path(args.dir).resolve()
    
    if args.ui_command == "add":
        components = args.components
        
        # Handle --all flag
        if args.all:
            print("[PyNext] Copying all UI components...")
            copied = copy_all_components(project_dir)
            print(f"[PyNext] Copied {len(copied)} components to components/ui/")
            for path in copied:
                print(f"  ✓ {path.name}")
            return 0
        
        if not components:
            print("Error: Specify component names or use --all")
            print("Example: pynext ui add button card dialog")
            return 1
        
        # Copy specified components
        copied = []
        failed = []
        for name in components:
            if name not in AVAILABLE_COMPONENTS:
                failed.append(name)
                continue
            
            result = copy_component_to_project(name, project_dir)
            if result:
                copied.append(result)
                print(f"  ✓ {name} → {result.relative_to(project_dir)}")
            else:
                failed.append(name)
        
        if copied:
            print(f"\n[PyNext] Copied {len(copied)} component(s)")
        
        if failed:
            print(f"\n[PyNext] Failed to copy: {', '.join(failed)}")
            print("  Available components: " + ", ".join(AVAILABLE_COMPONENTS.keys()))
            return 1
        
        return 0
    
    elif args.ui_command == "list":
        print("\n[PyNext] Available UI Components\n")
        
        # Group by category
        categories = {}
        for comp in list_available_components():
            if comp.category not in categories:
                categories[comp.category] = []
            categories[comp.category].append(comp)
        
        for category, components in sorted(categories.items()):
            print(f"  {category.upper()}")
            for comp in components:
                exports = ", ".join(comp.exports[:3])
                if len(comp.exports) > 3:
                    exports += f" (+{len(comp.exports) - 3} more)"
                print(f"    {comp.name:<20} {exports}")
            print()
        
        print(f"  Total: {len(AVAILABLE_COMPONENTS)} components")
        print("\n  Usage: pynext ui add <component> [component...]")
        print("         pynext ui add --all")
        return 0
    
    else:
        # No subcommand, show help
        print("\n[PyNext] UI Component Management")
        print("\n  Commands:")
        print("    pynext ui list              List available components")
        print("    pynext ui add <names...>    Copy components for customization")
        print("    pynext ui add --all         Copy all components")
        print("\n  Components are copied to components/ui/ for editing")
        print("  Or import directly: from pynext.shadcn import Button")
        return 0


def cmd_registry(args: argparse.Namespace) -> int:
    """Manage custom component registries (Tier 3)."""
    from pynext.registry import RegistryManager
    
    manager = RegistryManager(args.dir)
    
    if args.registry_command == "add":
        if not args.url:
            print("Error: --url is required")
            print("Example: pynext registry add acme-ui --url=https://ui.acme.com")
            print("         pynext registry add my-lib --url=github:user/repo")
            return 1
        
        print(f"[PyNext] Adding registry: {args.name}")
        registry = manager.add_registry(args.name, args.url)
        print(f"  ✓ Added {registry.name}")
        print(f"  URL: {registry.url}")
        
        if registry.components:
            print(f"  Components: {len(registry.components)}")
        else:
            print("  Note: Registry metadata will be fetched on first install")
        
        return 0
    
    elif args.registry_command == "remove":
        if manager.remove_registry(args.name):
            print(f"[PyNext] Removed registry: {args.name}")
            return 0
        else:
            print(f"Error: Registry not found: {args.name}")
            return 1
    
    elif args.registry_command == "list":
        registries = manager.list_registries()
        
        if not registries:
            print("\n[PyNext] No custom registries configured")
            print("\n  Add one with: pynext registry add <name> --url=<url>")
            return 0
        
        print("\n[PyNext] Custom Registries\n")
        for reg in registries:
            print(f"  {reg.name}")
            print(f"    URL: {reg.url}")
            print(f"    Version: {reg.version}")
            if reg.components:
                print(f"    Components: {', '.join(reg.components.keys())}")
            print()
        
        return 0
    
    elif args.registry_command == "install":
        # Parse registry:component format
        if ":" not in args.component:
            print("Error: Use format registry:component")
            print("Example: pynext registry install acme-ui:data-table")
            return 1
        
        registry_name, component_name = args.component.split(":", 1)
        
        try:
            print(f"[PyNext] Installing {component_name} from {registry_name}...")
            installed = manager.install_component(registry_name, component_name)
            print(f"  ✓ Installed {len(installed)} file(s)")
            for path in installed:
                print(f"    {path.relative_to(manager.project_dir)}")
            return 0
        except ValueError as e:
            print(f"Error: {e}")
            return 1
    
    elif args.registry_command == "init":
        from pynext.registry.manager import create_registry_template
        
        output_path = Path(args.dir) / "pynext-registry.json"
        create_registry_template(output_path)
        print(f"[PyNext] Created {output_path}")
        print("  Edit this file to define your component library")
        return 0
    
    else:
        # No subcommand, show help
        print("\n[PyNext] Custom Registry Management")
        print("\n  Commands:")
        print("    pynext registry list                      List registered sources")
        print("    pynext registry add <name> --url=<url>    Add a custom registry")
        print("    pynext registry remove <name>             Remove a registry")
        print("    pynext registry install <reg>:<comp>      Install from registry")
        print("    pynext registry init                      Create registry template")
        print("\n  URL formats:")
        print("    https://ui.example.com                    HTTP URL")
        print("    github:owner/repo                         GitHub repository")
        return 0


def cmd_deps(args: argparse.Namespace) -> int:
    """Manage project dependencies."""
    from pynext.deps import DependencyManager
    
    deps = DependencyManager(args.dir)
    
    if args.deps_command == "install":
        print("[PyNext] Installing dependencies...")
        
        if args.python_only:
            success = deps.install_python_deps()
            if success:
                print("[PyNext] Python dependencies installed ✓")
            else:
                print("[PyNext] Failed to install Python dependencies")
                return 1
        elif args.npm_only:
            success = deps.install_npm_deps()
            if success:
                print("[PyNext] NPM dependencies installed ✓")
            else:
                print("[PyNext] Failed to install NPM dependencies")
                return 1
        else:
            python_ok = deps.install_python_deps()
            npm_ok = deps.install_npm_deps()
            
            if python_ok:
                print("[PyNext] Python dependencies installed ✓")
            if npm_ok:
                print("[PyNext] NPM dependencies installed ✓")
            
            if not python_ok or not npm_ok:
                return 1
        
        return 0
    
    elif args.deps_command == "check":
        print("[PyNext] Checking dependencies...")
        
        missing = deps.check_all()
        
        if not missing["python"] and not missing["npm"]:
            print("[PyNext] All dependencies installed ✓")
            return 0
        
        if missing["python"]:
            print(f"\n[PyNext] Missing Python packages ({len(missing['python'])}):")
            for pkg in missing["python"]:
                print(f"  - {pkg}")
        
        if missing["npm"]:
            print(f"\n[PyNext] Missing NPM packages ({len(missing['npm'])}):")
            for pkg in missing["npm"]:
                print(f"  - {pkg}")
        
        print("\n[PyNext] Run 'pynext deps install' to install missing dependencies")
        return 1
    
    elif args.deps_command == "init":
        from pynext.deps import create_dependency_templates
        
        python_path, npm_path = create_dependency_templates(args.dir)
        print(f"[PyNext] Created {python_path.name}")
        print(f"[PyNext] Created {npm_path.name}")
        return 0
    
    else:
        # No subcommand, show status
        deps.print_status()
        return 0


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="pynext",
        description="PyNext - A Python web framework with SolidJS-inspired reactivity",
    )
    parser.add_argument(
        "--version", "-v",
        action="store_true",
        help="Show version",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # dev command
    dev_parser = subparsers.add_parser("dev", help="Start development server")
    dev_parser.add_argument("--pages", default="pages", help="Pages directory")
    dev_parser.add_argument("--static", default="public", help="Static files directory")
    dev_parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    dev_parser.add_argument("--port", "-p", type=int, default=3000, help="Port to listen on")
    dev_parser.add_argument("--skip-deps", action="store_true", help="Skip dependency check")
    dev_parser.add_argument("--no-install", action="store_true", help="Don't auto-install missing deps")
    
    # build command
    build_parser = subparsers.add_parser("build", help="Build for production")
    build_parser.add_argument("--dir", default=".", help="Project directory")
    build_parser.add_argument("--pages", default="pages", help="Pages directory")
    build_parser.add_argument("--static", default="public", help="Static files directory")
    build_parser.add_argument("--output", "-o", default=".pynext/build", help="Output directory")
    
    # init command
    init_parser = subparsers.add_parser("init", help="Initialize new project")
    init_parser.add_argument("name", help="Project name/directory")
    
    # routes command
    routes_parser = subparsers.add_parser("routes", help="List all routes")
    routes_parser.add_argument("--pages", default="pages", help="Pages directory")
    
    # deps command
    deps_parser = subparsers.add_parser("deps", help="Manage dependencies")
    deps_parser.add_argument("--dir", default=".", help="Project directory")
    deps_subparsers = deps_parser.add_subparsers(dest="deps_command", help="Dependency commands")
    
    # deps install
    deps_install = deps_subparsers.add_parser("install", help="Install dependencies")
    deps_install.add_argument("--python", dest="python_only", action="store_true", help="Install only Python deps")
    deps_install.add_argument("--npm", dest="npm_only", action="store_true", help="Install only NPM deps")
    
    # deps check
    deps_subparsers.add_parser("check", help="Check for missing dependencies")
    
    # deps init
    deps_subparsers.add_parser("init", help="Create dependency files")
    
    # ui command (Tier 2: Official components)
    ui_parser = subparsers.add_parser("ui", help="Manage UI components")
    ui_parser.add_argument("--dir", default=".", help="Project directory")
    ui_subparsers = ui_parser.add_subparsers(dest="ui_command", help="UI commands")
    
    # ui add
    ui_add = ui_subparsers.add_parser("add", help="Add UI components to project")
    ui_add.add_argument("components", nargs="*", help="Component names to add")
    ui_add.add_argument("--all", action="store_true", help="Add all components")
    
    # ui list
    ui_subparsers.add_parser("list", help="List available components")
    
    # registry command (Tier 3: Custom registries)
    reg_parser = subparsers.add_parser("registry", help="Manage custom component registries")
    reg_parser.add_argument("--dir", default=".", help="Project directory")
    reg_subparsers = reg_parser.add_subparsers(dest="registry_command", help="Registry commands")
    
    # registry add
    reg_add = reg_subparsers.add_parser("add", help="Add a custom registry")
    reg_add.add_argument("name", help="Registry name")
    reg_add.add_argument("--url", help="Registry URL (https:// or github:owner/repo)")
    
    # registry remove
    reg_remove = reg_subparsers.add_parser("remove", help="Remove a registry")
    reg_remove.add_argument("name", help="Registry name to remove")
    
    # registry list
    reg_subparsers.add_parser("list", help="List registered sources")
    
    # registry install
    reg_install = reg_subparsers.add_parser("install", help="Install from registry")
    reg_install.add_argument("component", help="Component to install (registry:component)")
    
    # registry init
    reg_subparsers.add_parser("init", help="Create registry template for publishing")
    
    args = parser.parse_args()
    
    if args.version:
        from pynext import __version__
        print(f"pynext {__version__}")
        return 0
    
    if args.command == "dev":
        return cmd_dev(args)
    elif args.command == "build":
        return cmd_build(args)
    elif args.command == "init":
        return cmd_init(args)
    elif args.command == "routes":
        return cmd_routes(args)
    elif args.command == "deps":
        return cmd_deps(args)
    elif args.command == "ui":
        return cmd_ui(args)
    elif args.command == "registry":
        return cmd_registry(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())

